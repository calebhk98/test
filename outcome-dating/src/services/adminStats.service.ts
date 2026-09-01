/**
 * src/services/adminStats.service.ts — the ADMIN-facing "stats page"
 * (product owner: "1 for admins... should allow tons of data" — the
 * operational/product-health metrics list: registrations, verified
 * emails, completed profiles, impressions, interests sent/accepted,
 * conversations, date proposals/completions, voucher redemptions,
 * refunds, no-shows, reports, blocks, shadowbans, retention by cohort,
 * plus the quality metrics — accepted-interest rate, date completion
 * rate, positive feedback rate, report rate per thousand messages,
 * no-show rate, refund rate, chat-to-date conversion, repeat date rate).
 *
 * ADMIN-ONLY, AUDITED: every exported function here requires an admin
 * actor (`requireAdminActor`) as defense in depth (the HTTP layer already
 * gates `/admin/stats/*` behind `requireRole('admin')` — see
 * `adminStats.routes.ts`), and every route that calls into this file
 * writes an `admin_audit_log` row for the READ itself, not just for
 * mutations — a deliberately stronger bar than the sibling
 * `admin.routes.ts` convention (which only audits writes), because this
 * page aggregates the platform's full operational and financial history
 * and product explicitly asked for every access to be logged.
 *
 * AGGREGATES ONLY: nothing here ever selects a message body, a report's
 * free-text `details`, post-date `notes`/`safety_details`, or any other
 * column that would let an admin read a private conversation through this
 * page. Every query below is a `count(*)`/`sum(...)` over a rollup table
 * or a `GROUP BY` count — never a row-level SELECT of message content.
 *
 * PERFORMANCE / FRESHNESS: this file reads exclusively from the small
 * rollup tables `statsAggregation.job.ts` maintains
 * (`stats_platform_daily`, `stats_cohort_retention`,
 * `stats_platform_gauges`, `stats_aggregation_runs`) — at most a few
 * thousand rows regardless of how large `users`/`messages`/`interests`
 * etc. have grown, so every query here is a bounded aggregate over a
 * small table, not a scan of platform history. The three exceptions are
 * `verifiedEmailsNow`/`profilesCompletedNow`/`shadowbannedNow`, which are
 * live, cheap, INDEX-ONLY point counts (see the partial indexes in
 * `db/migrations/020_stats.sql`) rather than rollup reads — they are
 * current-state gauges, not historical flow, and a partial index makes
 * "how many rows are currently true" cheap independent of total table
 * size. Every response carries `freshness` (the rollup job's last run) so
 * a viewer always sees an honest "as of" time. See this build's report for
 * measured query counts/timings.
 */
import type { Ctx } from '../lib/ctx.js';
import { ForbiddenError } from '../lib/errors.js';
import { DAILY_COLUMNS } from '../jobs/statsAggregation.job.js';
import type { DailyRow } from '../jobs/statsAggregation.job.js';

export const DEFAULT_WINDOW_DAYS = 30;
export const MAX_WINDOW_DAYS = 3653; // ~10 years — still just summing one row per day
const RETENTION_LIST_DAYS = 60;

function requireAdminActor(ctx: Ctx): void {
  if (ctx.actor.type !== 'admin') {
    throw new ForbiddenError('Admin stats are only available to an admin actor.');
  }
}

function utcDayKey(d: Date): string {
  return d.toISOString().slice(0, 10);
}

export interface StatsWindow {
  startDay: string;
  endDay: string;
  isAllTime: boolean;
}

/** `windowDays` is inclusive of today; `'all'` sums every rollup day ever written (still cheap — one row per day, not per event). */
export function resolveWindow(now: Date, windowDays: number | 'all'): StatsWindow {
  const endDay = utcDayKey(now);
  if (windowDays === 'all') {
    return { startDay: '1970-01-01', endDay, isAllTime: true };
  }
  const clamped = Math.min(MAX_WINDOW_DAYS, Math.max(1, Math.floor(windowDays)));
  const start = new Date(now.getTime() - (clamped - 1) * 24 * 60 * 60 * 1000);
  return { startDay: utcDayKey(start), endDay, isAllTime: false };
}

async function sumDailyWindow(ctx: Ctx, window: StatsWindow): Promise<DailyRow> {
  const selectList = DAILY_COLUMNS.map((c) => `coalesce(sum(${c}), 0)::text AS ${c}`).join(', ');
  const { rows } = await ctx.db.query<Record<string, string>>(
    `SELECT ${selectList} FROM stats_platform_daily WHERE day >= $1 AND day <= $2`,
    [window.startDay, window.endDay],
  );
  const row = rows[0] ?? {};
  const out = {} as DailyRow;
  for (const c of DAILY_COLUMNS) out[c] = Number(row[c] ?? '0');
  return out;
}

export interface AdminCoreMetrics {
  registrations: number;
  verifiedEmailsInWindow: number;
  verifiedEmailsNow: number;
  profilesCompletedInWindow: number;
  profilesCompletedNow: number;
  discoveryImpressions: number;
  interestsSent: number;
  interestsAccepted: number;
  interestsDeclined: number;
  interestsExpired: number;
  conversationsOpened: number;
  dateProposalsSent: number;
  dateProposalsAccepted: number;
  datesCompleted: number;
  datesNoShow: number;
  datesDisputed: number;
  voucherRedemptions: number;
  reports: number;
  blocks: number;
  shadowbanActionsInWindow: number;
  shadowbannedNow: number;
  messagesSent: number;
}

export interface AdminMoneyMetrics {
  authorizationsCents: number;
  capturesCents: number;
  refundsCents: number;
  refundsCount: number;
  releasesCents: number;
}

export interface AdminQualityMetrics {
  acceptedInterestRate: number | null;
  dateCompletionRate: number | null;
  positiveFeedbackRate: number | null;
  reportRatePerThousandMessages: number | null;
  noShowRate: number | null;
  refundRate: number | null;
  chatToDateConversionRate: number | null;
  repeatDateRate: number | null;
}

export interface AdminFreshness {
  lastRunAt: Date | null;
  rollupWindowStartDay: string | null;
  rollupWindowEndDay: string | null;
}

export interface AdminStatsOverview {
  window: StatsWindow;
  core: AdminCoreMetrics;
  money: AdminMoneyMetrics;
  quality: AdminQualityMetrics;
  freshness: AdminFreshness;
}

async function currentGaugeCounts(ctx: Ctx): Promise<{ verifiedEmailsNow: number; profilesCompletedNow: number; shadowbannedNow: number }> {
  const [v, p, s] = await Promise.all([
    ctx.db.query<{ n: string }>(`SELECT count(*)::text AS n FROM users WHERE email_verified_at IS NOT NULL`),
    ctx.db.query<{ n: string }>(`SELECT count(*)::text AS n FROM profiles WHERE profile_completeness >= 100`),
    ctx.db.query<{ n: string }>(`SELECT count(*)::text AS n FROM users WHERE shadowbanned = true`),
  ]);
  return {
    verifiedEmailsNow: Number(v.rows[0]?.n ?? '0'),
    profilesCompletedNow: Number(p.rows[0]?.n ?? '0'),
    shadowbannedNow: Number(s.rows[0]?.n ?? '0'),
  };
}

async function repeatDateRate(ctx: Ctx): Promise<number | null> {
  const { rows } = await ctx.db.query<{ value_numeric: number }>(
    `SELECT value_numeric FROM stats_platform_gauges WHERE key = 'repeat_date_rate'`,
  );
  return rows[0] ? rows[0].value_numeric : null;
}

async function freshness(ctx: Ctx): Promise<AdminFreshness> {
  const { rows } = await ctx.db.query<{ run_at: Date; window_start_day: Date; window_end_day: Date }>(
    `SELECT run_at, window_start_day, window_end_day FROM stats_aggregation_runs ORDER BY run_at DESC LIMIT 1`,
  );
  const row = rows[0];
  if (!row) return { lastRunAt: null, rollupWindowStartDay: null, rollupWindowEndDay: null };
  return {
    lastRunAt: row.run_at,
    rollupWindowStartDay: utcDayKey(row.window_start_day),
    rollupWindowEndDay: utcDayKey(row.window_end_day),
  };
}

function ratio(numerator: number, denominator: number): number | null {
  if (denominator <= 0) return null;
  return numerator / denominator;
}

/**
 * The full admin overview — bundles core/money/quality/freshness in one
 * call so the page loads in one round trip from the client's perspective,
 * mirroring the existing `/admin/analytics/overview` pattern this build
 * is additive to (that route stays owned by its original agent; this is a
 * separate, richer, rollup-backed surface — see this build's report).
 */
export async function getOverview(ctx: Ctx, opts?: { windowDays?: number | 'all' }): Promise<AdminStatsOverview> {
  requireAdminActor(ctx);
  const window = resolveWindow(ctx.clock.now(), opts?.windowDays ?? DEFAULT_WINDOW_DAYS);

  const [sums, gauges, repeatRate, fresh] = await Promise.all([
    sumDailyWindow(ctx, window),
    currentGaugeCounts(ctx),
    repeatDateRate(ctx),
    freshness(ctx),
  ]);

  const core: AdminCoreMetrics = {
    registrations: sums.registrations,
    verifiedEmailsInWindow: sums.verified_emails,
    verifiedEmailsNow: gauges.verifiedEmailsNow,
    profilesCompletedInWindow: sums.profiles_completed,
    profilesCompletedNow: gauges.profilesCompletedNow,
    discoveryImpressions: sums.discovery_impressions,
    interestsSent: sums.interests_sent,
    interestsAccepted: sums.interests_accepted,
    interestsDeclined: sums.interests_declined,
    interestsExpired: sums.interests_expired,
    conversationsOpened: sums.conversations_opened,
    dateProposalsSent: sums.date_proposals_sent,
    dateProposalsAccepted: sums.date_proposals_accepted,
    datesCompleted: sums.dates_completed,
    datesNoShow: sums.dates_no_show,
    datesDisputed: sums.dates_disputed,
    voucherRedemptions: sums.voucher_redemptions,
    reports: sums.reports,
    blocks: sums.blocks,
    shadowbanActionsInWindow: sums.shadowban_actions,
    shadowbannedNow: gauges.shadowbannedNow,
    messagesSent: sums.messages_sent,
  };

  const money: AdminMoneyMetrics = {
    authorizationsCents: sums.authorizations_cents,
    capturesCents: sums.captures_cents,
    refundsCents: sums.refunds_cents,
    refundsCount: sums.refunds_count,
    releasesCents: sums.releases_cents,
  };

  const dateOutcomeDenominator = core.datesCompleted + core.datesNoShow + core.datesDisputed;
  const quality: AdminQualityMetrics = {
    acceptedInterestRate: ratio(core.interestsAccepted, core.interestsSent),
    dateCompletionRate: ratio(core.datesCompleted, dateOutcomeDenominator),
    positiveFeedbackRate: ratio(sums.positive_feedback, sums.positive_feedback + sums.negative_feedback),
    reportRatePerThousandMessages: core.messagesSent > 0 ? (core.reports / core.messagesSent) * 1000 : null,
    noShowRate: ratio(core.datesNoShow, dateOutcomeDenominator),
    refundRate: ratio(money.refundsCount, core.datesCompleted + core.datesNoShow + core.datesDisputed || core.dateProposalsSent),
    chatToDateConversionRate: ratio(core.dateProposalsSent, core.conversationsOpened),
    repeatDateRate: repeatRate,
  };

  return { window, core, money, quality, freshness: fresh };
}

export interface RetentionCohortRow {
  cohortDate: string;
  cohortSize: number;
  activeD1: number;
  activeD7: number;
  activeD30: number;
  d1Rate: number | null;
  d7Rate: number | null;
  d30Rate: number | null;
}

export interface AdminRetention {
  cohorts: RetentionCohortRow[];
  freshness: AdminFreshness;
}

/** Bounded to the trailing `RETENTION_LIST_DAYS` (default 60) cohorts — the rollup job itself only maintains that many, see statsAggregation.job.ts. */
export async function getRetention(ctx: Ctx): Promise<AdminRetention> {
  requireAdminActor(ctx);
  const [{ rows }, fresh] = await Promise.all([
    ctx.db.query<{ cohort_date: Date; cohort_size: number; active_d1: number; active_d7: number; active_d30: number }>(
      `SELECT cohort_date, cohort_size, active_d1, active_d7, active_d30
       FROM stats_cohort_retention
       ORDER BY cohort_date DESC LIMIT $1`,
      [RETENTION_LIST_DAYS],
    ),
    freshness(ctx),
  ]);

  const cohorts: RetentionCohortRow[] = rows.map((r) => ({
    cohortDate: utcDayKey(r.cohort_date),
    cohortSize: r.cohort_size,
    activeD1: r.active_d1,
    activeD7: r.active_d7,
    activeD30: r.active_d30,
    d1Rate: ratio(r.active_d1, r.cohort_size),
    d7Rate: ratio(r.active_d7, r.cohort_size),
    d30Rate: ratio(r.active_d30, r.cohort_size),
  }));

  return { cohorts, freshness: fresh };
}
