/**
 * src/services/stats.service.ts — the USER-facing "stats page" (product
 * owner: "1 for admins and 1 for users... tucked away, but should allow
 * tons of data"). Every function here answers only for the CALLING user
 * (`requireUserActor(ctx)`), never for anyone else.
 *
 * PRIVACY, enforced by construction (not by a serializer allowlist bolted
 * on afterward — see docs/risk-review.md and docs/ux-product-review.md,
 * both read before this file was designed):
 *
 *  - No query in this file ever returns another user's id, name, photo, or
 *    any per-candidate row. Every "how many other people" number is a
 *    COUNT, never a list — `discovery_events`/`interests`/etc. are always
 *    aggregated, never joined out to another person's profile.
 *  - `MIN_SUPPRESSIBLE_COHORT`: any count that describes a population of
 *    OTHER people (not the caller's own activity) below this size is
 *    withheld (`suppressed: true`, no number) rather than shown — see
 *    `suppressSmallCohort`. A pool of 1-4 nearby people is small enough
 *    that showing the exact number risks the viewer identifying who it
 *    is, especially after narrowing filters further.
 *  - Nothing here reads or derives the trust-score weighting
 *    (`trust.service.ts`'s own module doc: "NEVER returned by any
 *    user-facing export"). This file does not import trust.service at
 *    all, deliberately — trust has its own page
 *    (`GET /me/trust`/`serializeTrustSummary`) and that boundary is not
 *    redrawn here.
 *  - No ranking/percentile/"top X%" anywhere — every comparison in this
 *    file is the caller against their OWN past (a trend over time), never
 *    against other users. There is no query anywhere below that computes
 *    a percentile or rank.
 *  - `post_date_feedback.safety_flag`/`safety_details`/`notes` are never
 *    selected here, even for the row's own owner — see
 *    `postDateFeedback.service.ts`'s isolation guarantee for those two
 *    columns; this file stays out of that boundary entirely rather than
 *    re-deciding it.
 *
 * PERFORMANCE: every query below is scoped to the calling user's own rows
 * via an existing index (`sender_id`/`recipient_id`/`user_id`/
 * `viewer_user_id`/`candidate_user_id`), so cost scales with ONE user's
 * activity, not the platform's — cheap regardless of total platform size,
 * unlike the admin page (which needs `statsAggregation.job.ts`'s rollup
 * tables because IT aggregates over everyone). The one genuinely expensive
 * piece — "how many people would each filter open up" — reuses
 * `filter.service.ts`'s already-bounded (`DASHBOARD_SCAN_CAP`) reality-
 * dashboard machinery and is cached per user for
 * `FILTER_COST_CACHE_TTL_MS` (see `getMyFilterCosts`) rather than
 * recomputed on every casual page open. See this build's report for
 * measured query counts/timings.
 */
import type pg from 'pg';
import type { Ctx } from '../lib/ctx.js';
import { requireUserActor, withDb } from '../lib/ctx.js';
import * as filterService from './filter.service.js';
import * as discoveryService from './discovery.service.js';
import * as photoExperimentService from './photoExperiment.service.js';
import { computeProfileCompleteness } from './profile.service.js';

export const MIN_SUPPRESSIBLE_COHORT = 5;
const FILTER_COST_CACHE_TTL_MS = 60 * 60 * 1000; // 1 hour
const MAX_FILTERS_EVALUATED = 8;
const TREND_DEFAULT_WEEKS = 12;
const TREND_MAX_WEEKS = 52;
const RESPONSE_TIME_CONVERSATION_LIMIT = 30;
const RESPONSE_TIME_MESSAGE_LIMIT = 2000;

/** A count of OTHER people, suppressed below `MIN_SUPPRESSIBLE_COHORT` — see module doc. */
export interface SuppressibleCount {
  value: number | null;
  suppressed: boolean;
}

export function suppressSmallCohort(n: number): SuppressibleCount {
  if (n < MIN_SUPPRESSIBLE_COHORT) return { value: null, suppressed: true };
  return { value: n, suppressed: false };
}

function rate(numerator: number, denominator: number): number | null {
  if (denominator <= 0) return null;
  return numerator / denominator;
}

// =====================================================================
// Funnel + completeness + response behaviour + date outcomes — one
// composite call, all bounded per-user queries.
// =====================================================================

export interface InterestFunnelSide {
  total: number;
  pending: number;
  accepted: number;
  declined: number;
  expired: number;
  acceptanceRate: number | null;
}

export interface DateProposalFunnelSide {
  total: number;
  accepted: number;
  acceptanceRate: number | null;
}

export interface UserFunnel {
  profileViewsReceived: number;
  interestsReceived: InterestFunnelSide;
  interestsSent: InterestFunnelSide;
  conversationsOpened: number;
  dateProposalsSent: DateProposalFunnelSide;
  dateProposalsReceived: DateProposalFunnelSide;
  datesCompleted: number;
  datesNoShowAsMe: number;
  dateCompletionRate: number | null;
}

async function loadInterestFunnelSide(ctx: Ctx, userId: string, side: 'sender_id' | 'recipient_id'): Promise<InterestFunnelSide> {
  const { rows } = await ctx.db.query<{ status: string; n: string }>(
    `SELECT status, count(*)::text AS n FROM interests WHERE ${side} = $1 GROUP BY status`,
    [userId],
  );
  const byStatus = new Map(rows.map((r) => [r.status, Number(r.n)]));
  const pending = byStatus.get('pending') ?? 0;
  const accepted = byStatus.get('accepted') ?? 0;
  const declined = byStatus.get('declined') ?? 0;
  const expired = byStatus.get('expired') ?? 0;
  const canceled = byStatus.get('canceled') ?? 0;
  const total = pending + accepted + declined + expired + canceled;
  const resolved = accepted + declined + expired;
  return { total, pending, accepted, declined, expired, acceptanceRate: rate(accepted, resolved) };
}

async function loadDateProposalFunnelSide(ctx: Ctx, userId: string, side: 'proposer_id' | 'recipient_id'): Promise<DateProposalFunnelSide> {
  const { rows } = await ctx.db.query<{ n: string; accepted: string }>(
    `SELECT count(*)::text AS n,
       count(*) FILTER (WHERE status NOT IN ('draft', 'pending_acceptance', 'payment_failed'))::text AS accepted
     FROM date_proposals WHERE ${side} = $1`,
    [userId],
  );
  const total = Number(rows[0]?.n ?? '0');
  const accepted = Number(rows[0]?.accepted ?? '0');
  return { total, accepted, acceptanceRate: rate(accepted, total) };
}

export async function getMyFunnel(ctx: Ctx): Promise<UserFunnel> {
  const { userId } = requireUserActor(ctx);

  const [profileViewsRow, interestsReceived, interestsSent, conversationsRow, dateProposalsSent, dateProposalsReceived, dateOutcomeRow] =
    await Promise.all([
      ctx.db.query<{ n: string }>(`SELECT count(*)::text AS n FROM discovery_events WHERE candidate_user_id = $1`, [userId]),
      loadInterestFunnelSide(ctx, userId, 'recipient_id'),
      loadInterestFunnelSide(ctx, userId, 'sender_id'),
      ctx.db.query<{ n: string }>(
        `SELECT count(*)::text AS n FROM conversations WHERE user_a_id = $1 OR user_b_id = $1`,
        [userId],
      ),
      loadDateProposalFunnelSide(ctx, userId, 'proposer_id'),
      loadDateProposalFunnelSide(ctx, userId, 'recipient_id'),
      ctx.db.query<{ completed: string; no_show: string; disputed: string }>(
        `SELECT
           count(*) FILTER (WHERE status IN ('completed', 'completed_unverified'))::text AS completed,
           count(*) FILTER (WHERE status = 'no_show')::text AS no_show,
           count(*) FILTER (WHERE status = 'disputed')::text AS disputed
         FROM date_proposals WHERE proposer_id = $1 OR recipient_id = $1`,
        [userId],
      ),
    ]);

  const completed = Number(dateOutcomeRow.rows[0]?.completed ?? '0');
  const noShow = Number(dateOutcomeRow.rows[0]?.no_show ?? '0');
  const disputed = Number(dateOutcomeRow.rows[0]?.disputed ?? '0');
  const resolvedDates = completed + noShow + disputed;

  return {
    profileViewsReceived: Number(profileViewsRow.rows[0]?.n ?? '0'),
    interestsReceived,
    interestsSent,
    conversationsOpened: Number(conversationsRow.rows[0]?.n ?? '0'),
    dateProposalsSent,
    dateProposalsReceived,
    datesCompleted: completed,
    datesNoShowAsMe: noShow,
    dateCompletionRate: rate(completed, resolvedDates),
  };
}

export interface UserCompleteness {
  profileCompleteness: number;
  questionsAnswered: number;
  questionsAvailable: number;
  /** Static, non-numeric-weight copy — never the scoring formula. */
  note: string;
}

export async function getMyCompleteness(ctx: Ctx): Promise<UserCompleteness> {
  const { userId } = requireUserActor(ctx);
  const [profileCompleteness, answeredRow, availableRow] = await Promise.all([
    computeProfileCompleteness(ctx, userId),
    ctx.db.query<{ n: string }>(`SELECT count(*)::text AS n FROM user_question_answers WHERE user_id = $1`, [userId]),
    ctx.db.query<{ n: string }>(`SELECT count(*)::text AS n FROM question_bank WHERE active AND is_current`),
  ]);
  return {
    profileCompleteness,
    questionsAnswered: Number(answeredRow.rows[0]?.n ?? '0'),
    questionsAvailable: Number(availableRow.rows[0]?.n ?? '0'),
    note: 'A fuller profile and more answered questions give the matching system more to work with — they help you be discovered by, and matched with, more compatible people.',
  };
}

export interface ResponseBehaviour {
  /** Minutes; null if there is not yet enough reply data in the recent window to estimate. */
  medianResponseMinutes: number | null;
  sampledReplies: number;
  incomingInterestExpiryRate: number | null;
  incomingInterestsResolved: number;
}

function median(values: number[]): number | null {
  if (values.length === 0) return null;
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 === 0 ? (sorted[mid - 1]! + sorted[mid]!) / 2 : sorted[mid]!;
}

export async function getMyResponseBehaviour(ctx: Ctx): Promise<ResponseBehaviour> {
  const { userId } = requireUserActor(ctx);

  const { rows: convoRows } = await ctx.db.query<{ id: string }>(
    `SELECT id FROM conversations WHERE (user_a_id = $1 OR user_b_id = $1) AND last_message_at IS NOT NULL
     ORDER BY last_message_at DESC LIMIT $2`,
    [userId, RESPONSE_TIME_CONVERSATION_LIMIT],
  );
  const conversationIds = convoRows.map((r) => r.id);

  let medianResponseMinutes: number | null = null;
  let sampledReplies = 0;
  if (conversationIds.length > 0) {
    const { rows: msgRows } = await ctx.db.query<{ conversation_id: string; sender_id: string; created_at: Date }>(
      `SELECT conversation_id, sender_id, created_at FROM messages
       WHERE conversation_id = ANY($1::uuid[])
       ORDER BY conversation_id ASC, created_at ASC LIMIT $2`,
      [conversationIds, RESPONSE_TIME_MESSAGE_LIMIT],
    );
    const gapsMinutes: number[] = [];
    let prevConversation: string | null = null;
    let prevSenderId: string | null = null;
    let prevCreatedAt: Date | null = null;
    for (const m of msgRows) {
      if (m.conversation_id !== prevConversation) {
        prevConversation = m.conversation_id;
        prevSenderId = m.sender_id;
        prevCreatedAt = m.created_at;
        continue;
      }
      if (m.sender_id === userId && prevSenderId !== null && prevSenderId !== userId && prevCreatedAt) {
        gapsMinutes.push((m.created_at.getTime() - prevCreatedAt.getTime()) / 60000);
      }
      prevSenderId = m.sender_id;
      prevCreatedAt = m.created_at;
    }
    sampledReplies = gapsMinutes.length;
    medianResponseMinutes = median(gapsMinutes);
  }

  const { rows: interestRows } = await ctx.db.query<{ expired: string; resolved: string }>(
    `SELECT
       count(*) FILTER (WHERE status = 'expired')::text AS expired,
       count(*) FILTER (WHERE status IN ('accepted', 'declined', 'expired'))::text AS resolved
     FROM interests WHERE recipient_id = $1`,
    [userId],
  );
  const expired = Number(interestRows[0]?.expired ?? '0');
  const resolved = Number(interestRows[0]?.resolved ?? '0');

  return {
    medianResponseMinutes,
    sampledReplies,
    incomingInterestExpiryRate: rate(expired, resolved),
    incomingInterestsResolved: resolved,
  };
}

export interface DateOutcomeSummary {
  totalCheckIns: number;
  byOutcome: Record<string, number>;
  wouldMeetAgain: { yes: number; no: number; unsure: number };
}

export async function getMyDateOutcomes(ctx: Ctx): Promise<DateOutcomeSummary> {
  const { userId } = requireUserActor(ctx);

  // Deliberately selects ONLY outcome/positive/would_meet_again — never
  // safety_flag/safety_details/notes/report_id, even for the row's own
  // owner. See module doc.
  const { rows } = await ctx.db.query<{ outcome: string | null; positive: boolean | null; would_meet_again: boolean | null }>(
    `SELECT outcome, positive, would_meet_again FROM post_date_feedback WHERE user_id = $1`,
    [userId],
  );

  const byOutcome: Record<string, number> = {};
  const wouldMeetAgain = { yes: 0, no: 0, unsure: 0 };
  for (const r of rows) {
    const key = r.outcome ?? (r.positive === true ? 'happened_good' : r.positive === false ? 'happened_bad' : 'unspecified');
    byOutcome[key] = (byOutcome[key] ?? 0) + 1;
    if (r.would_meet_again === true) wouldMeetAgain.yes += 1;
    else if (r.would_meet_again === false) wouldMeetAgain.no += 1;
    else wouldMeetAgain.unsure += 1;
  }

  return { totalCheckIns: rows.length, byOutcome, wouldMeetAgain };
}

export interface UserStatsOverview {
  funnel: UserFunnel;
  completeness: UserCompleteness;
  responseBehaviour: ResponseBehaviour;
  dateOutcomes: DateOutcomeSummary;
  generatedAt: Date;
}

/** One composite call for the main stats page — all four sections above, run in parallel. */
export async function getMyStatsOverview(ctx: Ctx): Promise<UserStatsOverview> {
  requireUserActor(ctx); // fail fast/uniformly before issuing any query
  const [funnel, completeness, responseBehaviour, dateOutcomes] = await Promise.all([
    getMyFunnel(ctx),
    getMyCompleteness(ctx),
    getMyResponseBehaviour(ctx),
    getMyDateOutcomes(ctx),
  ]);
  return { funnel, completeness, responseBehaviour, dateOutcomes, generatedAt: ctx.clock.now() };
}

// =====================================================================
// Trends over time — the user against their OWN past, never against
// anyone else.
// =====================================================================

export interface TrendPoint {
  weekStart: string; // ISO date (UTC Monday) of the bucket start
  interestsSent: number;
  interestsAccepted: number;
  interestsReceived: number;
  datesCompleted: number;
}

export interface UserStatsTrends {
  weeks: number;
  points: TrendPoint[];
}

function weekBucketSql(tsColumn: string, table: string, side: string, userId: string): { text: string; params: unknown[] } {
  return {
    text: `SELECT to_char(date_trunc('week', ${tsColumn} AT TIME ZONE 'UTC'), 'YYYY-MM-DD') AS week, count(*)::text AS n
           FROM ${table} WHERE ${side} = $1 AND ${tsColumn} >= $2 GROUP BY 1`,
    params: [userId],
  };
}

export async function getMyStatsTrends(ctx: Ctx, opts?: { weeks?: number }): Promise<UserStatsTrends> {
  const { userId } = requireUserActor(ctx);
  const weeks = Math.min(TREND_MAX_WEEKS, Math.max(1, opts?.weeks ?? TREND_DEFAULT_WEEKS));
  const windowStart = new Date(ctx.clock.now().getTime() - weeks * 7 * 24 * 60 * 60 * 1000);

  const sentQ = weekBucketSql('created_at', 'interests', 'sender_id', userId);
  const acceptedQ = weekBucketSql('accepted_at', 'interests', 'sender_id', userId);
  const receivedQ = weekBucketSql('created_at', 'interests', 'recipient_id', userId);
  const completedQ = `SELECT to_char(date_trunc('week', completed_at AT TIME ZONE 'UTC'), 'YYYY-MM-DD') AS week, count(*)::text AS n
    FROM date_proposals WHERE (proposer_id = $1 OR recipient_id = $1)
      AND status IN ('completed', 'completed_unverified') AND completed_at >= $2 GROUP BY 1`;

  const [sent, accepted, received, completed] = await Promise.all([
    ctx.db.query<{ week: string; n: string }>(sentQ.text, [userId, windowStart]),
    ctx.db.query<{ week: string; n: string }>(acceptedQ.text, [userId, windowStart]),
    ctx.db.query<{ week: string; n: string }>(receivedQ.text, [userId, windowStart]),
    ctx.db.query<{ week: string; n: string }>(completedQ, [userId, windowStart]),
  ]);

  const sentMap = new Map(sent.rows.map((r) => [r.week, Number(r.n)]));
  const acceptedMap = new Map(accepted.rows.map((r) => [r.week, Number(r.n)]));
  const receivedMap = new Map(received.rows.map((r) => [r.week, Number(r.n)]));
  const completedMap = new Map(completed.rows.map((r) => [r.week, Number(r.n)]));

  const allWeeks = new Set<string>([...sentMap.keys(), ...acceptedMap.keys(), ...receivedMap.keys(), ...completedMap.keys()]);
  const points: TrendPoint[] = [...allWeeks]
    .sort()
    .map((weekStart) => ({
      weekStart,
      interestsSent: sentMap.get(weekStart) ?? 0,
      interestsAccepted: acceptedMap.get(weekStart) ?? 0,
      interestsReceived: receivedMap.get(weekStart) ?? 0,
      datesCompleted: completedMap.get(weekStart) ?? 0,
    }));

  return { weeks, points };
}

// =====================================================================
// Photo performance — accepted-interest rate is the metric, never raw
// impressions/views (see photoExperiment.service.ts's own invariant,
// reused here rather than re-derived).
// =====================================================================

export interface PhotoStatEntry {
  photoId: string;
  impressions: number;
  interestsSent: number;
  interestsAccepted: number;
  /** interestsAccepted / impressions — the metric this product deliberately ranks on, not raw impressions. Null if too few impressions to be meaningful. */
  acceptedInterestRate: number | null;
  recommended: boolean;
}

export interface UserPhotoStats {
  photos: PhotoStatEntry[];
  hasEnoughDataForRecommendation: boolean;
}

export async function getMyPhotoStats(ctx: Ctx): Promise<UserPhotoStats> {
  const { userId } = requireUserActor(ctx);
  const [stats, recommendations] = await Promise.all([
    photoExperimentService.listStatsForUser(ctx, userId),
    photoExperimentService.getMyPhotoTestResults(ctx),
  ]);
  const recommendedIds = new Set(recommendations.map((r) => r.photoId));

  const photos: PhotoStatEntry[] = stats.map((s) => ({
    photoId: s.photoId,
    impressions: s.impressions,
    interestsSent: s.interestsSent,
    interestsAccepted: s.interestsAccepted,
    acceptedInterestRate: s.impressions > 0 ? s.interestsAccepted / s.impressions : null,
    recommended: recommendedIds.has(s.photoId),
  }));

  return { photos, hasEnoughDataForRecommendation: stats.length >= 3 };
}

// =====================================================================
// Filter cost — "how many people does this filter exclude, and what
// would widening it open up." Reuses the reality dashboard's already-
// bounded machinery (filter.service.ts#countUsersMatchingMyFilters,
// discovery.service.ts#getRealityDashboard); the per-filter breakdown
// asks the SAME bounded question once per enabled filter with that one
// filter temporarily (and non-destructively) disabled inside a
// transaction that is always rolled back, never committed — see
// `withScratchRollback` below. Cached per user for `FILTER_COST_CACHE_TTL_MS`.
// =====================================================================

export interface FilterCostEntry {
  filterKey: string;
  /** Candidates that would additionally pass if this one filter were removed, all else unchanged. Suppressed (never shown as a raw number) below `MIN_SUPPRESSIBLE_COHORT`. */
  additionalCandidatesIfRemoved: SuppressibleCount;
}

export interface UserFilterCosts {
  currentPool: SuppressibleCount; // matchesMyFilters, all filters applied
  whoseFiltersIMatch: SuppressibleCount;
  mutualMatchPool: SuppressibleCount;
  perFilter: FilterCostEntry[];
  computedAt: Date;
  fromCache: boolean;
}

async function withScratchRollback<T>(pool: pg.Pool, fn: (client: pg.PoolClient) => Promise<T>): Promise<T> {
  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    return await fn(client);
  } finally {
    await client.query('ROLLBACK').catch(() => {});
    client.release();
  }
}

async function readFilterCostCache(ctx: Ctx, userId: string): Promise<UserFilterCosts | null> {
  const { rows } = await ctx.db.query<{ computed_at: Date; payload: UserFilterCosts }>(
    `SELECT computed_at, payload FROM stats_user_cache WHERE user_id = $1 AND cache_key = 'filter_costs'`,
    [userId],
  );
  const row = rows[0];
  if (!row) return null;
  if (ctx.clock.now().getTime() - row.computed_at.getTime() > FILTER_COST_CACHE_TTL_MS) return null;
  return { ...row.payload, computedAt: new Date(row.computed_at), fromCache: true };
}

async function writeFilterCostCache(ctx: Ctx, userId: string, payload: UserFilterCosts): Promise<void> {
  await ctx.db.query(
    `INSERT INTO stats_user_cache (user_id, cache_key, computed_at, payload)
     VALUES ($1, 'filter_costs', $2, $3::jsonb)
     ON CONFLICT (user_id, cache_key) DO UPDATE SET computed_at = excluded.computed_at, payload = excluded.payload`,
    [userId, ctx.clock.now(), JSON.stringify(payload)],
  );
}

export async function getMyFilterCosts(ctx: Ctx, pool: pg.Pool, opts?: { forceRefresh?: boolean }): Promise<UserFilterCosts> {
  const { userId } = requireUserActor(ctx);

  if (!opts?.forceRefresh) {
    const cached = await readFilterCostCache(ctx, userId);
    if (cached) return cached;
  }

  const [reality, filterRows] = await Promise.all([
    discoveryService.getRealityDashboard(ctx),
    ctx.db.query<{ filter_key: string }>(
      `SELECT filter_key FROM hard_filters WHERE user_id = $1 AND enabled = true ORDER BY filter_key ASC LIMIT $2`,
      [userId, MAX_FILTERS_EVALUATED],
    ),
  ]);

  const baseline = reality.matchesMyFilters;
  const perFilter: FilterCostEntry[] = [];
  for (const { filter_key: filterKey } of filterRows.rows) {
    const withoutCount = await withScratchRollback(pool, async (client) => {
      await client.query(`UPDATE hard_filters SET enabled = false WHERE user_id = $1 AND filter_key = $2`, [
        userId,
        filterKey,
      ]);
      return filterService.countUsersMatchingMyFilters(withDb(ctx, client), userId);
    });
    const additional = Math.max(0, withoutCount - baseline);
    perFilter.push({ filterKey, additionalCandidatesIfRemoved: suppressSmallCohort(additional) });
  }

  const payload: UserFilterCosts = {
    currentPool: suppressSmallCohort(reality.matchesMyFilters),
    whoseFiltersIMatch: suppressSmallCohort(reality.whoseFiltersIMatch),
    mutualMatchPool: suppressSmallCohort(reality.mutualMatchPool),
    perFilter,
    computedAt: ctx.clock.now(),
    fromCache: false,
  };

  await writeFilterCostCache(ctx, userId, payload);
  return payload;
}
