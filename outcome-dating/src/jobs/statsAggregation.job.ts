/**
 * src/jobs/statsAggregation.job.ts, the rollup job both stats pages read
 * from, so neither page ever scans raw event history at request time.
 *
 * STRATEGY ("bounded time window, pre-aggregation, documented freshness",
 * see this build's report for the measured cost):
 *
 *  1. `stats_platform_daily` (one row per UTC calendar day, admin page):
 *     every run RE-AGGREGATES a bounded trailing window
 *     (`TRAILING_WINDOW_DAYS`, default 35 days including today) and
 *     overwrites those days' rows outright. Days older than the window are
 *     never touched again. This assumes every source row's terminal state
 *     settles well within the window, true here: interests expire/get
 *     answered in days, date proposals resolve in days-to-a-couple-weeks
 *     (see `dateProposalExpiry.job.ts`/`ticketedCompletionSweep.job.ts`).
 *     Each metric is computed with exactly ONE grouped, indexed,
 *     day-range query across the whole window (`date-range WHERE` +
 *     `GROUP BY day`), never a per-day loop of queries, so the read side
 *     is O(number of metrics) round trips, not O(window days) or O(all
 *     history). The write side is a bounded per-day UPSERT loop (at most
 *     `TRAILING_WINDOW_DAYS + 1` single-row writes).
 *
 *     A cold start (the table is empty, first deploy) additionally
 *     backfills every day of platform history ONCE, in the same
 *     one-query-per-metric shape (just a wider window). This is a
 *     one-time cost paid once at rollout, not a recurring per-request or
 *     even a recurring per-run cost, documented explicitly so it is
 *     never confused with the steady-state trailing-window behavior above.
 *
 *  2. `stats_cohort_retention` (one row per registration-day cohort, admin
 *     page): same shape, bounded to `RETENTION_WINDOW_DAYS` (default 60)
 *     trailing cohorts, one grouped query. Retention is measured against
 *     `users.last_active_at` (a single snapshot column, not a full
 *     activity log, see the migration file's comment on that table for
 *     why) as "was this user still active at least N days into their
 *     tenure", an honest, clearly-labeled proxy, not a precise
 *     daily-active reconstruction.
 *
 *  3. `stats_platform_gauges` (running metrics that are not naturally
 *     day-bucketed sums, currently just the repeat-date rate, which needs
 *     a per-user distinct count across a window rather than a per-day
 *     count): one grouped query bounded to `GAUGE_LOOKBACK_DAYS` (default
 *     ~2 years) of `date_proposals.scheduled_end`.
 *
 *  4. `stats_region_activity` / `stats_region_tag_prevalence` (024_stats_
 *     comparisons.sql, user page's peer-comparison section): unlike 1-3,
 *     these are not time-windowed. A comparison needs a snapshot of the
 *     WHOLE current active population's distribution, not a trailing
 *     window, so every run TRUNCATEs both tables and repopulates them with
 *     one grouped `INSERT ... SELECT` each (never a per-region write
 *     loop), bucketing every active user with a location into a coarse
 *     geographic cell (see `REGION_GRID_DEGREES`/`regionKeyFor`) and
 *     computing per-region medians/quartiles and tag counts in that one
 *     pass. See `db/migrations/024_stats_comparisons.sql`'s own header for
 *     the privacy rules this pair of tables follows.
 *
 * FRESHNESS: every run appends one `stats_aggregation_runs` row. Both
 * stats services surface the most recent run's `run_at` so a viewer always
 * sees an honest "as of" time rather than an implied-live number. Default
 * scheduler interval (`registry.ts`) is 15 minutes, so data is stale by at
 * most that long, acceptable for a page product describes as "opened
 * casually," never wired to anything that needs real-time truth (money
 * reconciliation reads `payment_ledger` directly in a test to prove the
 * rollup matches it exactly, not to prove it's instantaneous).
 *
 * The per-user stats page mostly does NOT read from these tables: a
 * user's own activity is already a small, indexed slice (their own rows,
 * via the existing `sender_id`/`recipient_id`/`user_id` indexes), so
 * querying it live is cheap regardless of platform size. The one
 * exception is the peer-comparison section above (point 4): "how does my
 * activity compare to typical" is inherently a question about everyone
 * else, so it is the one part of the user page that reads a rollup rather
 * than computing live, see `stats.service.ts`'s own module doc.
 */
import type { Ctx } from '../lib/ctx.js';
import type { JobDefinition } from './types.js';

export const TRAILING_WINDOW_DAYS = 35;
export const RETENTION_WINDOW_DAYS = 60;
export const RETENTION_HORIZON_DAYS = 30; // longest retention threshold measured (d30)
export const GAUGE_LOOKBACK_DAYS = 730;

function utcDayKey(d: Date): string {
  return d.toISOString().slice(0, 10);
}

function startOfUtcDay(d: Date): Date {
  return new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()));
}

function addUtcDays(d: Date, n: number): Date {
  return new Date(d.getTime() + n * 24 * 60 * 60 * 1000);
}

function dayRange(startInclusive: Date, endExclusive: Date): string[] {
  const days: string[] = [];
  for (let d = startInclusive; d < endExclusive; d = addUtcDays(d, 1)) {
    days.push(utcDayKey(d));
  }
  return days;
}

export const DAILY_COLUMNS = [
  'registrations',
  'verified_emails',
  'profiles_completed',
  'discovery_impressions',
  'interests_sent',
  'interests_accepted',
  'interests_declined',
  'interests_expired',
  'conversations_opened',
  'date_proposals_sent',
  'date_proposals_accepted',
  'dates_completed',
  'dates_no_show',
  'dates_disputed',
  'voucher_redemptions',
  'reports',
  'blocks',
  'shadowban_actions',
  'positive_feedback',
  'negative_feedback',
  'messages_sent',
  'authorizations_cents',
  'captures_cents',
  'refunds_cents',
  'refunds_count',
  'releases_cents',
] as const;

export type DailyColumn = (typeof DAILY_COLUMNS)[number];
export type DailyRow = Record<DailyColumn, number>;

function zeroRow(): DailyRow {
  const row = {} as DailyRow;
  for (const c of DAILY_COLUMNS) row[c] = 0;
  return row;
}

interface SimpleMetric {
  column: DailyColumn;
  /** Full SQL; must select `day text` (already UTC-bucketed via to_char(... AT TIME ZONE 'UTC', 'YYYY-MM-DD')) and `n bigint`, and accept ($1 = window start inclusive, $2 = window end exclusive) as timestamptz bounds. */
  sql: string;
}

/**
 * One grouped, indexed, day-range query per metric, see module doc.
 * `tsColumn` is the event's own transition timestamp (never a mutable
 * "last updated" column for anything that can transition more than once),
 * so a row is bucketed into exactly the day it actually happened, and
 * never re-bucketed on a later, unrelated update.
 */
function simpleMetrics(): SimpleMetric[] {
  const bucketed = (tsColumn: string, table: string, extraWhere = ''): string => `
    SELECT to_char(${tsColumn} AT TIME ZONE 'UTC', 'YYYY-MM-DD') AS day, count(*)::bigint AS n
    FROM ${table}
    WHERE ${tsColumn} >= $1 AND ${tsColumn} < $2 ${extraWhere}
    GROUP BY 1`;

  return [
    { column: 'registrations', sql: bucketed('created_at', 'users') },
    { column: 'verified_emails', sql: bucketed('email_verified_at', 'users') },
    { column: 'profiles_completed', sql: bucketed('updated_at', 'profiles', 'AND profile_completeness >= 100') },
    { column: 'discovery_impressions', sql: bucketed('created_at', 'discovery_events') },
    { column: 'interests_sent', sql: bucketed('created_at', 'interests') },
    { column: 'interests_accepted', sql: bucketed('accepted_at', 'interests') },
    { column: 'interests_declined', sql: bucketed('declined_at', 'interests') },
    { column: 'interests_expired', sql: bucketed('expired_at', 'interests') },
    { column: 'conversations_opened', sql: bucketed('created_at', 'conversations') },
    { column: 'date_proposals_sent', sql: bucketed('created_at', 'date_proposals') },
    { column: 'date_proposals_accepted', sql: bucketed('accepted_at', 'date_proposals') },
    {
      column: 'dates_completed',
      sql: bucketed('completed_at', 'date_proposals', `AND status IN ('completed', 'completed_unverified')`),
    },
    { column: 'dates_no_show', sql: bucketed('scheduled_end', 'date_proposals', `AND status = 'no_show'`) },
    { column: 'dates_disputed', sql: bucketed('scheduled_end', 'date_proposals', `AND status = 'disputed'`) },
    { column: 'voucher_redemptions', sql: bucketed('created_at', 'venue_redemptions') },
    { column: 'reports', sql: bucketed('created_at', 'reports') },
    { column: 'blocks', sql: bucketed('created_at', 'blocks') },
    { column: 'shadowban_actions', sql: bucketed('created_at', 'moderation_actions', `AND action = 'shadowban'`) },
    { column: 'messages_sent', sql: bucketed('created_at', 'messages') },
  ];
}

/** post_date_feedback covers both the legacy boolean and the newer 4-way outcome in one pass (see the file this reads, both are mutually exclusive per row, never both non-null). */
const FEEDBACK_SQL = `
  SELECT to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD') AS day,
    count(*) FILTER (WHERE positive = true OR outcome = 'happened_good')::bigint AS pos,
    count(*) FILTER (WHERE positive = false OR outcome = 'happened_bad')::bigint AS neg
  FROM post_date_feedback
  WHERE created_at >= $1 AND created_at < $2
  GROUP BY 1`;

/** payment_ledger: one grouped query covering every type this rollup tracks, bucketed by day+type. */
const LEDGER_SQL = `
  SELECT to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD') AS day, type,
    sum(amount_cents)::bigint AS cents, count(*)::bigint AS n
  FROM payment_ledger
  WHERE created_at >= $1 AND created_at < $2
    AND type IN ('authorization', 'capture', 'refund', 'release')
  GROUP BY 1, 2`;

export interface StatsAggregationResult {
  windowStartDay: string;
  windowEndDay: string;
  daysUpserted: number;
  cohortsUpserted: number;
  regionsUpserted: number;
  tagRowsUpserted: number;
  durationMs: number;
  backfilled: boolean;
}

async function isFirstRun(ctx: Ctx): Promise<boolean> {
  const { rows } = await ctx.db.query<{ n: string }>('SELECT count(*)::text AS n FROM stats_platform_daily');
  return Number(rows[0]?.n ?? '0') === 0;
}

async function earliestRegistrationDay(ctx: Ctx): Promise<Date | null> {
  const { rows } = await ctx.db.query<{ min: Date | null }>('SELECT min(created_at) AS min FROM users');
  return rows[0]?.min ?? null;
}

async function aggregateDailyWindow(ctx: Ctx, windowStart: Date, windowEndExclusive: Date): Promise<number> {
  const days = dayRange(windowStart, windowEndExclusive);
  const rowsByDay = new Map<string, DailyRow>();
  for (const d of days) rowsByDay.set(d, zeroRow());

  const metrics = simpleMetrics();
  const [metricResults, feedbackResult, ledgerResult] = await Promise.all([
    Promise.all(
      metrics.map((m) => ctx.db.query<{ day: string; n: string }>(m.sql, [windowStart, windowEndExclusive])),
    ),
    ctx.db.query<{ day: string; pos: string; neg: string }>(FEEDBACK_SQL, [windowStart, windowEndExclusive]),
    ctx.db.query<{ day: string; type: string; cents: string; n: string }>(LEDGER_SQL, [windowStart, windowEndExclusive]),
  ]);

  metrics.forEach((m, i) => {
    for (const r of metricResults[i]!.rows) {
      const row = rowsByDay.get(r.day);
      if (row) row[m.column] = Number(r.n);
    }
  });

  for (const r of feedbackResult.rows) {
    const row = rowsByDay.get(r.day);
    if (row) {
      row.positive_feedback = Number(r.pos);
      row.negative_feedback = Number(r.neg);
    }
  }

  for (const r of ledgerResult.rows) {
    const row = rowsByDay.get(r.day);
    if (!row) continue;
    const cents = Number(r.cents);
    const n = Number(r.n);
    if (r.type === 'authorization') row.authorizations_cents = cents;
    else if (r.type === 'capture') row.captures_cents = cents;
    else if (r.type === 'release') row.releases_cents = cents;
    else if (r.type === 'refund') {
      row.refunds_cents = cents;
      row.refunds_count = n;
    }
  }

  const columnList = DAILY_COLUMNS.join(', ');
  const placeholders = DAILY_COLUMNS.map((_, i) => `$${i + 2}`).join(', ');
  const updateList = DAILY_COLUMNS.map((c) => `${c} = $${DAILY_COLUMNS.indexOf(c) + 2}`).join(', ');
  const upsertSql = `
    INSERT INTO stats_platform_daily (day, ${columnList}, updated_at)
    VALUES ($1, ${placeholders}, now())
    ON CONFLICT (day) DO UPDATE SET ${updateList}, updated_at = now()`;

  for (const [day, row] of rowsByDay) {
    const values = DAILY_COLUMNS.map((c) => row[c]);
    await ctx.db.query(upsertSql, [day, ...values]);
  }

  return rowsByDay.size;
}

const RETENTION_SQL = `
  SELECT (created_at AT TIME ZONE 'UTC')::date::text AS cohort_date,
    count(*)::int AS cohort_size,
    count(*) FILTER (WHERE last_active_at >= created_at + interval '1 day')::int AS d1,
    count(*) FILTER (WHERE last_active_at >= created_at + interval '7 day')::int AS d7,
    count(*) FILTER (WHERE last_active_at >= created_at + interval '30 day')::int AS d30
  FROM users
  WHERE created_at >= $1 AND created_at < $2
  GROUP BY 1`;

async function aggregateRetention(ctx: Ctx, windowStart: Date, windowEndExclusive: Date): Promise<number> {
  const { rows } = await ctx.db.query<{ cohort_date: string; cohort_size: number; d1: number; d7: number; d30: number }>(
    RETENTION_SQL,
    [windowStart, windowEndExclusive],
  );
  for (const r of rows) {
    await ctx.db.query(
      `INSERT INTO stats_cohort_retention (cohort_date, cohort_size, active_d1, active_d7, active_d30, computed_at)
       VALUES ($1, $2, $3, $4, $5, now())
       ON CONFLICT (cohort_date) DO UPDATE SET
         cohort_size = excluded.cohort_size, active_d1 = excluded.active_d1,
         active_d7 = excluded.active_d7, active_d30 = excluded.active_d30, computed_at = now()`,
      [r.cohort_date, r.cohort_size, r.d1, r.d7, r.d30],
    );
  }
  return rows.length;
}

/**
 * Repeat-date rate gauge: of users with >=1 completed date (in the
 * lookback window), what fraction have >=2? One grouped query, bounded by
 * `GAUGE_LOOKBACK_DAYS` of `scheduled_end` (indexed), cost scales with
 * completed-date volume in that window, not total user count.
 */
const REPEAT_DATE_SQL = `
  WITH participants AS (
    SELECT proposer_id AS user_id FROM date_proposals
    WHERE status IN ('completed', 'completed_unverified') AND scheduled_end >= $1
    UNION ALL
    SELECT recipient_id AS user_id FROM date_proposals
    WHERE status IN ('completed', 'completed_unverified') AND scheduled_end >= $1
  ),
  per_user AS (
    SELECT user_id, count(*) AS n FROM participants GROUP BY user_id
  )
  SELECT count(*)::bigint AS daters, count(*) FILTER (WHERE n >= 2)::bigint AS repeaters FROM per_user`;

async function aggregateGauges(ctx: Ctx, now: Date): Promise<void> {
  const lookback = addUtcDays(startOfUtcDay(now), -GAUGE_LOOKBACK_DAYS);
  const { rows } = await ctx.db.query<{ daters: string; repeaters: string }>(REPEAT_DATE_SQL, [lookback]);
  const daters = Number(rows[0]?.daters ?? '0');
  const repeaters = Number(rows[0]?.repeaters ?? '0');
  const rate = daters > 0 ? repeaters / daters : 0;
  await ctx.db.query(
    `INSERT INTO stats_platform_gauges (key, value_numeric, computed_at)
     VALUES ('repeat_date_rate', $1, now())
     ON CONFLICT (key) DO UPDATE SET value_numeric = excluded.value_numeric, computed_at = now()`,
    [rate],
  );
}

// =====================================================================
// Region comparisons (024_stats_comparisons.sql, user page's peer-
// comparison section). See that migration's header and this file's
// module doc, point 4, for the full write-up.
// =====================================================================

/** Side of a coarse geographic grid cell, in degrees. ~220km at the equator, coarser toward the poles as longitude compresses -- deliberately rougher than filter.service.ts's per-viewer radius box, because this groups EVERY user in one pass rather than answering one viewer's query at a time. Never returned to a client -- an internal join key only. */
export const REGION_GRID_DEGREES = 2;

/** Must stay behaviorally identical to `regionKeySqlExpr` below -- both compute the same coarse grid cell from a latitude/longitude pair, one in SQL (for the rollup writer) and one in JS (for the read path resolving a single viewer's own cell against the rollup). */
export function regionKeyFor(latitude: number, longitude: number): string {
  return `${Math.floor(latitude / REGION_GRID_DEGREES)}:${Math.floor(longitude / REGION_GRID_DEGREES)}`;
}

/** SQL form of `regionKeyFor`, evaluated against `latitude`/`longitude` columns on table alias `alias`. */
function regionKeySqlExpr(alias: string): string {
  return `(floor(${alias}.latitude / ${REGION_GRID_DEGREES})::int::text || ':' || floor(${alias}.longitude / ${REGION_GRID_DEGREES})::int::text)`;
}

/** Active users with a known location -- the population every region aggregate below is grouped over. `questionsAnswered` here intentionally counts every `user_question_answers` row regardless of status, matching `stats.service.ts#getMyCompleteness`'s own definition of "questions answered" (skipped/prefer_not_to_say rows count as attempted), so a viewer's own number and the regional typical number mean the same thing. */
function regionPopulationCte(): string {
  return `
    pop AS (
      SELECT u.id AS user_id, ${regionKeySqlExpr('p')} AS region_key
      FROM users u JOIN profiles p ON p.user_id = u.id
      WHERE u.status = 'active' AND p.latitude IS NOT NULL AND p.longitude IS NOT NULL
    )`;
}

/** One TRUNCATE + one grouped INSERT..SELECT -- the write side never loops per region, so its round-trip count stays fixed regardless of how many distinct regions exist. */
async function aggregateRegionActivity(ctx: Ctx): Promise<number> {
  await ctx.db.query('TRUNCATE stats_region_activity');
  const result = await ctx.db.query(`
    INSERT INTO stats_region_activity (
      region_key, user_count,
      questions_answered_median, questions_answered_p25, questions_answered_p75,
      enabled_filters_median, enabled_filters_p25, enabled_filters_p75, computed_at
    )
    WITH ${regionPopulationCte()},
    qa AS (SELECT user_id, count(*) AS n FROM user_question_answers GROUP BY user_id),
    ef AS (SELECT user_id, count(*) AS n FROM hard_filters WHERE enabled GROUP BY user_id)
    SELECT
      pop.region_key,
      count(*)::int AS user_count,
      percentile_cont(0.5) WITHIN GROUP (ORDER BY coalesce(qa.n, 0)) AS questions_answered_median,
      percentile_cont(0.25) WITHIN GROUP (ORDER BY coalesce(qa.n, 0)) AS questions_answered_p25,
      percentile_cont(0.75) WITHIN GROUP (ORDER BY coalesce(qa.n, 0)) AS questions_answered_p75,
      percentile_cont(0.5) WITHIN GROUP (ORDER BY coalesce(ef.n, 0)) AS enabled_filters_median,
      percentile_cont(0.25) WITHIN GROUP (ORDER BY coalesce(ef.n, 0)) AS enabled_filters_p25,
      percentile_cont(0.75) WITHIN GROUP (ORDER BY coalesce(ef.n, 0)) AS enabled_filters_p75,
      now()
    FROM pop
    LEFT JOIN qa ON qa.user_id = pop.user_id
    LEFT JOIN ef ON ef.user_id = pop.user_id
    GROUP BY pop.region_key`);
  return result.rowCount ?? 0;
}

/** Same one-truncate-plus-one-insert shape as `aggregateRegionActivity`. Only tags a user chose to make visible beyond just themselves ('public' or 'private_reciprocal') count toward the region's prevalence numbers -- see 024_stats_comparisons.sql's PRIVACY note for why a 'hidden' tag is excluded even though only a count, never an identity, would ever be exposed. */
async function aggregateRegionTagPrevalence(ctx: Ctx): Promise<number> {
  await ctx.db.query('TRUNCATE stats_region_tag_prevalence');
  const result = await ctx.db.query(`
    INSERT INTO stats_region_tag_prevalence (region_key, tag_id, user_count, computed_at)
    WITH ${regionPopulationCte()}
    SELECT pop.region_key, ut.tag_id, count(*)::int AS user_count, now()
    FROM user_tags ut
    JOIN pop ON pop.user_id = ut.user_id
    WHERE ut.visibility <> 'hidden'
    GROUP BY pop.region_key, ut.tag_id`);
  return result.rowCount ?? 0;
}

async function aggregateRegionComparisons(ctx: Ctx): Promise<{ regionsUpserted: number; tagRowsUpserted: number }> {
  const [regionsUpserted, tagRowsUpserted] = await Promise.all([
    aggregateRegionActivity(ctx),
    aggregateRegionTagPrevalence(ctx),
  ]);
  return { regionsUpserted, tagRowsUpserted };
}

export async function runStatsAggregationJob(ctx: Ctx): Promise<StatsAggregationResult> {
  const start = Date.now();
  const now = ctx.clock.now();
  const todayStart = startOfUtcDay(now);
  const windowEndExclusive = addUtcDays(todayStart, 1); // include all of "today" so far

  const backfilled = await isFirstRun(ctx);
  let windowStart: Date;
  if (backfilled) {
    const earliest = await earliestRegistrationDay(ctx);
    windowStart = earliest ? startOfUtcDay(earliest) : addUtcDays(todayStart, -TRAILING_WINDOW_DAYS);
  } else {
    windowStart = addUtcDays(todayStart, -(TRAILING_WINDOW_DAYS - 1));
  }

  const retentionWindowStart = addUtcDays(todayStart, -(RETENTION_WINDOW_DAYS - 1));
  const retentionStart = backfilled && windowStart < retentionWindowStart ? windowStart : retentionWindowStart;

  const [daysUpserted, cohortsUpserted, regionComparisons] = await Promise.all([
    aggregateDailyWindow(ctx, windowStart, windowEndExclusive),
    aggregateRetention(ctx, retentionStart, windowEndExclusive),
    aggregateRegionComparisons(ctx),
  ]);
  await aggregateGauges(ctx, now);

  const durationMs = Date.now() - start;
  await ctx.db.query(
    `INSERT INTO stats_aggregation_runs (run_at, window_start_day, window_end_day, days_upserted, duration_ms)
     VALUES ($1, $2, $3, $4, $5)`,
    [now, utcDayKey(windowStart), utcDayKey(addUtcDays(windowEndExclusive, -1)), daysUpserted, durationMs],
  );

  return {
    windowStartDay: utcDayKey(windowStart),
    windowEndDay: utcDayKey(addUtcDays(windowEndExclusive, -1)),
    daysUpserted,
    cohortsUpserted,
    regionsUpserted: regionComparisons.regionsUpserted,
    tagRowsUpserted: regionComparisons.tagRowsUpserted,
    durationMs,
    backfilled,
  };
}

export const statsAggregationJob: JobDefinition = {
  name: 'stats_aggregation',
  description: 'Re-aggregates a bounded trailing window of platform activity into stats_platform_daily / stats_cohort_retention / stats_platform_gauges / stats_region_activity / stats_region_tag_prevalence for the admin and user stats pages.',
  intervalMs: 15 * 60 * 1000, // 15 minutes
  run: runStatsAggregationJob,
};
