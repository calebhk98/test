/**
 * src/services/stats.service.ts: the USER-facing "stats page" (product
 * owner: "1 for admins and 1 for users... tucked away, but should allow
 * tons of data"). Every function here answers only for the CALLING user
 * (`requireUserActor(ctx)`), never for anyone else.
 *
 * PRIVACY, enforced by construction (not by a serializer allowlist bolted
 * on afterward, see docs/risk-review.md and docs/ux-product-review.md,
 * both read before this file was designed):
 *
 *  - No query in this file ever returns another user's id, name, photo, or
 *    any per-candidate row. Every "how many other people" number is a
 *    COUNT, never a list (discovery_events/interests/etc. are always
 *    aggregated, never joined out to another person's profile).
 *  - `MIN_SUPPRESSIBLE_COHORT`: any count that describes a population of
 *    OTHER people (not the caller's own activity) below this size is
 *    withheld (`suppressed: true`, no number) rather than shown, see
 *    `suppressSmallCohort`. A pool of 1-4 nearby people is small enough
 *    that showing the exact number risks the viewer identifying who it
 *    is, especially after narrowing filters further. This is the ONE
 *    suppression rule in this file; every comparison added below (region
 *    typical questions answered, region typical filter strictness, tag
 *    prevalence, the pool Venn) reuses it rather than inventing a second
 *    threshold.
 *  - Nothing here reads or derives the trust-score weighting
 *    (`trust.service.ts`'s own module doc: "NEVER returned by any
 *    user-facing export"). This file does not import trust.service at
 *    all, deliberately: trust has its own page
 *    (`GET /me/trust`/`serializeTrustSummary`) and that boundary is not
 *    redrawn here.
 *  - COMPARISONS ARE AGGREGATE-VERSUS-AGGREGATE, NEVER PERSON-VERSUS-
 *    PERSON, AND NEVER A PUBLIC OR RANKED SIGNAL: the product owner asked
 *    for comparison against the average (how you compare against
 *    typical, how many people share an interest, how strict your filters
 *    are), and product review (docs/ux-product-review.md) is equally
 *    clear this product has deliberately no popularity signal: no like
 *    counts, no boosts, no rank among peers, nothing that is VISIBLE TO
 *    ANYONE ELSE or that FEEDS BACK into who is shown to whom. Every
 *    comparison in this file is the caller's own count/rate against a
 *    regional MEDIAN and interquartile band, reduced to a coarse "below
 *    typical / typical / above typical" position, never a numeric
 *    percentile or rank, and it is returned only in a response scoped to
 *    the caller's own request, `requireUserActor(ctx)`, never stored
 *    anywhere another user's request could read, never joined into
 *    discovery/matching/compatibility scoring, and never shown to the
 *    other party in any interaction. That is the actual line: a
 *    desirability score is a problem because it is a SHARED or RANKED
 *    signal, visible to (or acted on by) someone other than the person
 *    it describes, which is what manufactures status hierarchies and
 *    changes behaviour toward the people ranked lower. A number only the
 *    subject themselves can ever see has no such mechanism, nobody's
 *    matches change because of it, nobody ranks anybody by it, it cannot
 *    create the dynamic this product avoids. So, alongside the caller's
 *    own effort (questions answered) and their own settings (filter
 *    strictness, tag prevalence), this file ALSO compares how OTHERS
 *    responded to the caller (sent-interest acceptance rate,
 *    received-interest conversion rate and volume, profile views, photo
 *    performance) against the same kind of regional band, honestly and
 *    without softening the numbers, a person asking for their own
 *    statistics is entitled to the real answer. See
 *    "PEER COMPARISONS: OTHERS' RESPONSES" below for exactly what is
 *    compared and the additional, metric-level suppression this needs
 *    beyond the region-population gate every comparison already has.
 *  - `post_date_feedback.safety_flag`/`safety_details`/`notes` are never
 *    selected here, even for the row's own owner, see
 *    `postDateFeedback.service.ts`'s isolation guarantee for those two
 *    columns; this file stays out of that boundary entirely rather than
 *    re-deciding it.
 *
 * PERFORMANCE: every query below is scoped to the calling user's own rows
 * via an existing index (`sender_id`/`recipient_id`/`user_id`/
 * `viewer_user_id`/`candidate_user_id`), so cost scales with ONE user's
 * activity, not the platform's, cheap regardless of total platform size,
 * unlike the admin page (which needs `statsAggregation.job.ts`'s rollup
 * tables because IT aggregates over everyone). The one genuinely expensive
 * piece, "how many people would each filter open up", makes ONE pass over
 * a geographically-bounded (`filterService.DASHBOARD_SCAN_CAP`) candidate
 * sample and classifies every candidate by exactly which of the caller's
 * filters it fails, rather than the earlier design's one full pool search
 * per filter (see `computeFilterFailureBreakdown`'s doc for the query-
 * count math). Results are cached per user for `FILTER_COST_CACHE_TTL_MS`
 * (see `getMyFilterCosts`) rather than recomputed on every casual page
 * open, and the pool Venn (`getMyPoolVenn`) reuses that same cache instead
 * of paying for its own reality-dashboard computation. The region
 * comparisons (`getMyComparisons`) read one small precomputed rollup row
 * (`stats_region_activity`/`stats_region_tag_prevalence`, written by
 * `statsAggregation.job.ts`) rather than scanning any population live.
 * See this build's report for measured query counts/timings.
 */
import type { Ctx } from '../lib/ctx.js';
import { requireUserActor } from '../lib/ctx.js';
import type { FilterOperator } from '../domain/types.js';
import * as filterService from './filter.service.js';
import * as discoveryService from './discovery.service.js';
import * as photoExperimentService from './photoExperiment.service.js';
import { computeProfileCompleteness } from './profile.service.js';
import * as statsVenn from './statsVenn.js';
import { regionKeyFor } from '../jobs/statsAggregation.job.js';

export const MIN_SUPPRESSIBLE_COHORT = 5;
const FILTER_COST_CACHE_TTL_MS = 60 * 60 * 1000; // 1 hour
const MAX_FILTERS_EVALUATED = 8;
const TREND_DEFAULT_WEEKS = 12;
const TREND_MAX_WEEKS = 52;
const RESPONSE_TIME_CONVERSATION_LIMIT = 30;
const RESPONSE_TIME_MESSAGE_LIMIT = 2000;

/** A count of OTHER people, suppressed below `MIN_SUPPRESSIBLE_COHORT`, see module doc. */
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
// Funnel + completeness + response behaviour + date outcomes, one
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
  /** Static, non-numeric-weight copy, never the scoring formula. */
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
    note: 'A fuller profile and more answered questions give the matching system more to work with, they help you be discovered by, and matched with, more compatible people.',
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

  // Deliberately selects ONLY outcome/would_meet_again, never
  // safety_flag/safety_details/notes/report_id, even for the row's own
  // owner. See module doc. `outcome` is the only feedback axis this table
  // has, the old `positive` boolean is gone (db/migrations/
  // 028_remove_legacy.sql), so there is no second column to fall back to.
  const { rows } = await ctx.db.query<{ outcome: string; would_meet_again: boolean | null }>(
    `SELECT outcome, would_meet_again FROM post_date_feedback WHERE user_id = $1 AND outcome IS NOT NULL`,
    [userId],
  );

  const byOutcome: Record<string, number> = {};
  const wouldMeetAgain = { yes: 0, no: 0, unsure: 0 };
  for (const r of rows) {
    byOutcome[r.outcome] = (byOutcome[r.outcome] ?? 0) + 1;
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

/** One composite call for the main stats page, all four sections above, run in parallel. */
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
// Trends over time, the user against their OWN past, never against
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
// Photo performance, accepted-interest rate is the metric, never raw
// impressions/views (see photoExperiment.service.ts's own invariant,
// reused here rather than re-derived).
// =====================================================================

export interface PhotoStatEntry {
  photoId: string;
  impressions: number;
  interestsSent: number;
  interestsAccepted: number;
  /** interestsAccepted / impressions, the metric this product deliberately ranks on, not raw impressions. Null if too few impressions to be meaningful. */
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
// Filter cost: "how many people does this filter exclude, and what
// would widening it open up." Reuses the reality dashboard's already-
// bounded machinery for the three headline numbers
// (discovery.service.ts#getRealityDashboard), and answers the per-filter
// breakdown with ONE pass over a geographically-bounded candidate sample
// (see `computeFilterFailureBreakdown` below) instead of the earlier
// design's one full pool search per enabled filter. Cached per user for
// `FILTER_COST_CACHE_TTL_MS`.
//
// ATTRIBUTE-RESOLUTION DUPLICATION, ON PURPOSE, DOCUMENTED: the one-pass
// computation needs to know, for a given filter key, which candidate
// attribute to compare against (a `profiles` column, a haversine distance,
// or a `qb:`-prefixed question-bank answer). `filter.service.ts` already
// has exactly this logic (`STRUCTURED_ATTRIBUTE_KEYS`,
// `resolveAttributeValueFromMaps`, `loadProfilesBatch`,
// `loadQuestionBankAnswersBatch`), but keeps it private, and this build's
// file-ownership boundary does not include that file. The pure comparison
// semantics (`evaluateFilter`) and the distance formula (`haversineKm`)
// ARE exported and are reused verbatim below, so the only thing
// duplicated here is the small, stable "which column does this filter key
// read from" routing table and the two batched SELECTs that load it, not
// the actual filter-matching logic. If filter.service.ts's owner can
// later export `resolveAttributeValueFromMaps`/`loadAttributeMapsFor` (or
// add a dedicated `evaluateFilterPairsBatchPerFilter` that returns a
// per-filter breakdown directly), this duplication goes away entirely;
// noted in this build's report as the requested new export rather than
// editing that file directly.
// =====================================================================

export interface FilterCostEntry {
  filterKey: string;
  /** Candidates that would additionally pass if this one filter, and only this one, were removed (i.e. candidates failing this filter and nothing else). Suppressed (never shown as a raw number) below `MIN_SUPPRESSIBLE_COHORT`. */
  additionalCandidatesIfRemoved: SuppressibleCount;
}

export interface UserFilterCosts {
  currentPool: SuppressibleCount; // matchesMyFilters, all filters applied
  whoseFiltersIMatch: SuppressibleCount;
  mutualMatchPool: SuppressibleCount;
  perFilter: FilterCostEntry[];
  /** Candidates failing two or more of the caller's enabled filters at once, i.e. candidates no SINGLE filter relaxation would recover. Same suppression rule as every other cross-person count. */
  candidatesFailingTwoOrMore: SuppressibleCount;
  /** The single enabled filter whose removal would open up the most candidates, or null if there are no enabled filters or every candidate's numbers are suppressed. Convenience view over `perFilter`, not a new computation. */
  costliestFilter: FilterCostEntry | null;
  computedAt: Date;
  fromCache: boolean;
  /**
   * The three reality-dashboard counts BEFORE suppression, kept only so
   * `getMyPoolVenn` can derive the Venn's five region sizes without
   * re-running `discoveryService.getRealityDashboard` (the expensive
   * part of this whole payload) a second time. Same sensitivity as
   * `currentPool`/`whoseFiltersIMatch`/`mutualMatchPool` above (a count of
   * other people, scoped to this one user's own cache row, never a list),
   * and never spread into an HTTP response: `serializeUserFilterCosts`
   * (src/http/serializers/stats.ts) does not include it.
   */
  rawPool: statsVenn.PoolVennCounts;
}

async function readStatsCache<T extends { computedAt: Date }>(ctx: Ctx, userId: string, cacheKey: string, ttlMs: number): Promise<T | null> {
  const { rows } = await ctx.db.query<{ computed_at: Date; payload: T }>(
    `SELECT computed_at, payload FROM stats_user_cache WHERE user_id = $1 AND cache_key = $2`,
    [userId, cacheKey],
  );
  const row = rows[0];
  if (!row) return null;
  if (ctx.clock.now().getTime() - row.computed_at.getTime() > ttlMs) return null;
  return { ...row.payload, computedAt: new Date(row.computed_at) };
}

async function writeStatsCache<T>(ctx: Ctx, userId: string, cacheKey: string, payload: T): Promise<void> {
  await ctx.db.query(
    `INSERT INTO stats_user_cache (user_id, cache_key, computed_at, payload)
     VALUES ($1, $2, $3, $4::jsonb)
     ON CONFLICT (user_id, cache_key) DO UPDATE SET computed_at = excluded.computed_at, payload = excluded.payload`,
    [userId, cacheKey, ctx.clock.now(), JSON.stringify(payload)],
  );
}

/** Mirrors filter.service.ts's private `STRUCTURED_ATTRIBUTE_KEYS` (see the DUPLICATION note above). Anything not in this set is a `qb:`-prefixed question-bank slug lookup. */
const STRUCTURED_FILTER_KEYS: ReadonlySet<string> = new Set([
  'age_min',
  'age_max',
  'distance_km',
  'gender_preference',
  'relationship_intention',
  'height_cm',
  'weight_g',
  'body_type',
]);

interface FilterEvalProfile {
  age: number | null;
  gender: string | null;
  relationshipIntention: string | null;
  latitude: number | null;
  longitude: number | null;
  heightCm: number | null;
  weightG: number | null;
  weightVisible: boolean;
  bodyType: string | null;
}

/** Batched profile load for filter evaluation, same columns as filter.service.ts's private `loadProfilesBatch`. */
async function loadFilterEvalProfiles(ctx: Ctx, userIds: string[]): Promise<Map<string, FilterEvalProfile>> {
  const map = new Map<string, FilterEvalProfile>();
  const ids = [...new Set(userIds)];
  if (ids.length === 0) return map;
  const { rows } = await ctx.db.query<{
    user_id: string;
    age: number;
    gender: string;
    relationship_intention: string;
    latitude: number | null;
    longitude: number | null;
    height_cm: number | null;
    weight_g: number | null;
    weight_visible: boolean;
    body_type: string | null;
  }>(
    `SELECT user_id, age, gender, relationship_intention, latitude, longitude, height_cm, weight_g, weight_visible, body_type
     FROM profiles WHERE user_id = ANY($1::uuid[])`,
    [ids],
  );
  for (const row of rows) {
    map.set(row.user_id, {
      age: row.age,
      gender: row.gender,
      relationshipIntention: row.relationship_intention,
      latitude: row.latitude,
      longitude: row.longitude,
      heightCm: row.height_cm,
      weightG: row.weight_g,
      weightVisible: row.weight_visible,
      bodyType: row.body_type,
    });
  }
  return map;
}

/** Batched question-bank answer load for filter evaluation, same shape and same `status = 'answered'` rule as filter.service.ts's private `loadQuestionBankAnswersBatch`. */
async function loadFilterEvalAnswers(ctx: Ctx, userIds: string[], slugs: string[]): Promise<Map<string, Map<string, unknown>>> {
  const map = new Map<string, Map<string, unknown>>();
  const ids = [...new Set(userIds)];
  if (ids.length === 0 || slugs.length === 0) return map;
  const { rows } = await ctx.db.query<{ user_id: string; question_slug: string; status: string; self_value: unknown }>(
    `SELECT user_id, question_slug, status, self_value
     FROM user_question_answers
     WHERE user_id = ANY($1::uuid[]) AND question_slug = ANY($2::text[])`,
    [ids, slugs],
  );
  for (const row of rows) {
    if (row.status !== 'answered') continue;
    let perUser = map.get(row.user_id);
    if (!perUser) {
      perUser = new Map();
      map.set(row.user_id, perUser);
    }
    perUser.set(row.question_slug, row.self_value);
  }
  return map;
}

/** Same resolution filter.service.ts's private `resolveAttributeValueFromMaps` performs, switch case for switch case (see the DUPLICATION note above for why this lives here too). */
function resolveFilterAttributeValue(
  subjectId: string,
  ownerId: string,
  filterKey: string,
  profiles: Map<string, FilterEvalProfile>,
  answers: Map<string, Map<string, unknown>>,
): unknown {
  if (!STRUCTURED_FILTER_KEYS.has(filterKey)) {
    if (!filterKey.startsWith('qb:')) return undefined;
    const slug = filterKey.slice(3);
    const perUser = answers.get(subjectId);
    if (!perUser || !perUser.has(slug)) return undefined;
    return perUser.get(slug);
  }
  switch (filterKey) {
    case 'age_min':
    case 'age_max':
      return profiles.get(subjectId)?.age ?? undefined;
    case 'distance_km': {
      const subject = profiles.get(subjectId);
      const owner = profiles.get(ownerId);
      if (subject?.latitude == null || subject?.longitude == null || owner?.latitude == null || owner?.longitude == null) {
        return undefined;
      }
      return filterService.haversineKm(subject.latitude, subject.longitude, owner.latitude, owner.longitude);
    }
    case 'gender_preference':
      return profiles.get(subjectId)?.gender ?? undefined;
    case 'relationship_intention':
      return profiles.get(subjectId)?.relationshipIntention ?? undefined;
    case 'height_cm':
      return profiles.get(subjectId)?.heightCm ?? undefined;
    case 'weight_g': {
      const profile = profiles.get(subjectId);
      if (!profile || !profile.weightVisible || profile.weightG == null) return undefined;
      return profile.weightG;
    }
    case 'body_type':
      return profiles.get(subjectId)?.bodyType ?? undefined;
    default:
      return undefined;
  }
}

interface NearbyActiveUsersForFilterEval {
  ids: string[];
  truncated: boolean;
  totalActiveInRadius: number;
}

/**
 * Same population, same geographic bounding box, same `DASHBOARD_SCAN_CAP`
 * cap, and same two-query shape (count + capped select) as
 * filter.service.ts's private `listNearbyActiveUserIds`, built here from
 * that file's EXPORTED `resolveGeoSearchContext` rather than duplicating
 * the box math itself. Keeping this population identical to the one
 * `discoveryService.getRealityDashboard`'s `matchesMyFilters` count uses
 * is what makes `computeFilterFailureBreakdown`'s zero-failures bucket
 * agree with that number (see this build's report for the equivalence
 * proof).
 */
async function loadNearbyActiveUsersForFilterEval(ctx: Ctx, userId: string, cap: number): Promise<NearbyActiveUsersForFilterEval> {
  const geo = await filterService.resolveGeoSearchContext(ctx, userId);

  const params: unknown[] = [userId];
  let geoClause = '';
  if (geo.box) {
    params.push(geo.box.latMin, geo.box.latMax, geo.box.lon1Min, geo.box.lon1Max, geo.box.lon2Min, geo.box.lon2Max);
    geoClause = `
       AND p.latitude BETWEEN $2 AND $3
       AND (p.longitude BETWEEN $4 AND $5 OR p.longitude BETWEEN $6 AND $7)`;
  }

  const { rows: totalRows } = await ctx.db.query<{ count: string }>(
    `SELECT count(*)::text AS count
     FROM users u JOIN profiles p ON p.user_id = u.id
     WHERE u.status = 'active' AND u.id <> $1${geoClause}`,
    params,
  );
  const totalActiveInRadius = Number(totalRows[0]!.count);

  const limitParamIndex = params.length + 1;
  const { rows } = await ctx.db.query<{ id: string }>(
    `SELECT u.id
     FROM users u JOIN profiles p ON p.user_id = u.id
     WHERE u.status = 'active' AND u.id <> $1${geoClause}
     ORDER BY u.last_active_at DESC, u.id ASC
     LIMIT $${limitParamIndex}`,
    [...params, cap + 1],
  );
  const truncated = rows.length > cap;
  return { ids: rows.slice(0, cap).map((r) => r.id), truncated, totalActiveInRadius };
}

interface EnabledFilterRow {
  filter_key: string;
  operator: FilterOperator;
  value: unknown;
  exclude_if_unset: boolean;
}

/**
 * The optimization this build's report measures: ONE pass over the
 * geographically-bounded candidate sample, evaluating every one of the
 * caller's enabled filters against every candidate, instead of the
 * earlier design's one full `countUsersMatchingMyFilters` search PER
 * enabled filter (each of those itself a fresh geo query plus a batched
 * evaluation, run inside a scratch transaction that flipped a real
 * `hard_filters` row and rolled the flip back).
 *
 * For each candidate this tracks exactly which of the caller's filters it
 * fails (stopping early once a second failure is seen, since this build
 * only needs "0", "exactly 1 (and which one)", or "2+"): a candidate
 * failing NO filters is in the baseline pool already (reflected in
 * `discoveryService.getRealityDashboard`'s `matchesMyFilters`, not
 * counted again here); a candidate failing EXACTLY ONE filter F is
 * precisely a candidate `additionalCandidatesIfRemoved` for F must count
 * (removing F alone would let them through, since they already pass every
 * other filter); a candidate failing TWO OR MORE is a candidate no single
 * filter relaxation can recover, which is exactly
 * `candidatesFailingTwoOrMore`. Query count: 1 (this user's own geo box,
 * via `resolveGeoSearchContext`) + 2 (`loadNearbyActiveUsersForFilterEval`)
 * + up to 2 (`loadFilterEvalProfiles`/`loadFilterEvalAnswers`, run in
 * parallel) = at most 5 queries total, REGARDLESS of how many filters are
 * enabled (bounded by `MAX_FILTERS_EVALUATED` either way) or how large the
 * candidate sample is (bounded by `DASHBOARD_SCAN_CAP`) -- the earlier
 * design's cost grew linearly with the enabled-filter count instead.
 */
async function computeFilterFailureBreakdown(
  ctx: Ctx,
  userId: string,
  filterRows: EnabledFilterRow[],
): Promise<{ perFilter: FilterCostEntry[]; candidatesFailingTwoOrMore: SuppressibleCount }> {
  if (filterRows.length === 0) {
    return { perFilter: [], candidatesFailingTwoOrMore: suppressSmallCohort(0) };
  }

  const nearby = await loadNearbyActiveUsersForFilterEval(ctx, userId, filterService.DASHBOARD_SCAN_CAP);
  if (nearby.ids.length === 0) {
    return {
      perFilter: filterRows.map((f) => ({ filterKey: f.filter_key, additionalCandidatesIfRemoved: suppressSmallCohort(0) })),
      candidatesFailingTwoOrMore: suppressSmallCohort(0),
    };
  }

  const qbSlugs = [...new Set(filterRows.filter((f) => f.filter_key.startsWith('qb:')).map((f) => f.filter_key.slice(3)))];
  const allIds = [...nearby.ids, userId];
  const [profiles, answers] = await Promise.all([
    loadFilterEvalProfiles(ctx, allIds),
    qbSlugs.length > 0 ? loadFilterEvalAnswers(ctx, allIds, qbSlugs) : Promise.resolve(new Map<string, Map<string, unknown>>()),
  ]);

  const failingOnlyCountByFilter = new Map<string, number>();
  let failingTwoOrMoreInSample = 0;

  for (const candidateId of nearby.ids) {
    let failingCount = 0;
    let onlyFailedKey: string | null = null;
    for (const f of filterRows) {
      const value = resolveFilterAttributeValue(candidateId, userId, f.filter_key, profiles, answers);
      const passes = filterService.evaluateFilter({ operator: f.operator, value: f.value }, value, f.exclude_if_unset);
      if (passes) continue;
      failingCount += 1;
      if (failingCount === 1) onlyFailedKey = f.filter_key;
      else break; // already know this candidate is in the "two or more" bucket
    }
    if (failingCount === 1 && onlyFailedKey) {
      failingOnlyCountByFilter.set(onlyFailedKey, (failingOnlyCountByFilter.get(onlyFailedKey) ?? 0) + 1);
    } else if (failingCount >= 2) {
      failingTwoOrMoreInSample += 1;
    }
  }

  const perFilter: FilterCostEntry[] = filterRows.map((f) => {
    const inSample = failingOnlyCountByFilter.get(f.filter_key) ?? 0;
    const estimate = filterService.summarizeSampledCount(ctx, `getMyFilterCosts:${f.filter_key}`, inSample, nearby);
    return { filterKey: f.filter_key, additionalCandidatesIfRemoved: suppressSmallCohort(estimate) };
  });

  const twoOrMoreEstimate = filterService.summarizeSampledCount(ctx, 'getMyFilterCosts:twoOrMore', failingTwoOrMoreInSample, nearby);
  return { perFilter, candidatesFailingTwoOrMore: suppressSmallCohort(twoOrMoreEstimate) };
}

function pickCostliestFilter(perFilter: FilterCostEntry[]): FilterCostEntry | null {
  let best: FilterCostEntry | null = null;
  for (const entry of perFilter) {
    const value = entry.additionalCandidatesIfRemoved.value;
    if (value === null) continue;
    if (!best || value > (best.additionalCandidatesIfRemoved.value ?? -1)) best = entry;
  }
  return best;
}

export interface GetMyFilterCostsOpts {
  forceRefresh?: boolean;
}

/** True for a plain `{ forceRefresh?: boolean }` options object, false for anything with a `query` method (a `pg.Pool`/`pg.PoolClient`) -- see `getMyFilterCosts`'s doc for why this distinction exists at all. */
function isFilterCostsOpts(v: unknown): v is GetMyFilterCostsOpts {
  return typeof v === 'object' && v !== null && !('query' in (v as Record<string, unknown>));
}

/**
 * `secondArg` accepts EITHER the real `opts` (the current, intended
 * calling convention: `getMyFilterCosts(ctx, { forceRefresh: true })`) OR
 * a legacy `pg.Pool`/`pg.PoolClient` in that position, with `opts` then
 * passed as a third argument. That second shape only exists because this
 * build's file-ownership boundary does not include
 * `tests/perf/scaleCurve.perf.test.ts` (owned by the scale-testing build
 * running concurrently), which still calls the pre-optimization
 * three-argument form (`getMyFilterCosts(ctx, pool, opts)`) from before
 * this build removed the scratch-transaction rollback that needed a raw
 * pool. Accepting and ignoring it here keeps that file compiling without
 * this build editing a test outside its ownership; every call site this
 * build owns uses the plain two-argument form.
 */
export async function getMyFilterCosts(
  ctx: Ctx,
  secondArg?: unknown,
  legacyOpts?: GetMyFilterCostsOpts,
): Promise<UserFilterCosts> {
  const opts: GetMyFilterCostsOpts | undefined = legacyOpts ?? (isFilterCostsOpts(secondArg) ? secondArg : undefined);
  const { userId } = requireUserActor(ctx);

  if (!opts?.forceRefresh) {
    const cached = await readStatsCache<UserFilterCosts>(ctx, userId, 'filter_costs', FILTER_COST_CACHE_TTL_MS);
    if (cached) return { ...cached, fromCache: true };
  }

  const [reality, filterRows] = await Promise.all([
    discoveryService.getRealityDashboard(ctx),
    ctx.db.query<EnabledFilterRow>(
      `SELECT filter_key, operator, value, exclude_if_unset FROM hard_filters WHERE user_id = $1 AND enabled = true ORDER BY filter_key ASC LIMIT $2`,
      [userId, MAX_FILTERS_EVALUATED],
    ),
  ]);

  const { perFilter, candidatesFailingTwoOrMore } = await computeFilterFailureBreakdown(ctx, userId, filterRows.rows);

  const payload: UserFilterCosts = {
    currentPool: suppressSmallCohort(reality.matchesMyFilters),
    whoseFiltersIMatch: suppressSmallCohort(reality.whoseFiltersIMatch),
    mutualMatchPool: suppressSmallCohort(reality.mutualMatchPool),
    perFilter,
    candidatesFailingTwoOrMore,
    costliestFilter: pickCostliestFilter(perFilter),
    computedAt: ctx.clock.now(),
    fromCache: false,
    rawPool: {
      matchesMyFilters: reality.matchesMyFilters,
      whoseFiltersIMatch: reality.whoseFiltersIMatch,
      mutualMatchPool: reality.mutualMatchPool,
    },
  };

  await writeStatsCache(ctx, userId, 'filter_costs', payload);
  return payload;
}

// =====================================================================
// Pool Venn: the same three reality-dashboard counts `getMyFilterCosts`
// already computes, reshaped into a proper two-set Venn (set sizes,
// intersection, and what sits outside each set) plus a small
// self-contained accessible SVG rendering of it. See statsVenn.ts for the
// pure data/rendering logic; this section is just wiring plus caching.
// =====================================================================

/** Cached implicitly: reads (and, on a cold cache, writes) the SAME `filter_costs` cache entry `getMyFilterCosts` uses, so a page that loads both the filter-cost view and the Venn on one visit pays for `discoveryService.getRealityDashboard` at most once. */
export async function getMyPoolVenn(ctx: Ctx): Promise<statsVenn.PoolVennData> {
  requireUserActor(ctx);
  const costs = await getMyFilterCosts(ctx);
  return statsVenn.computePoolVenn(costs.rawPool, suppressSmallCohort);
}

/** `renderPoolVennSvg`'s numbers are exactly `getMyPoolVenn`'s numbers, nothing computed only for the picture -- see statsVenn.ts's own doc on why that matters for a screen reader. */
export async function getMyPoolVennSvg(ctx: Ctx): Promise<string> {
  const data = await getMyPoolVenn(ctx);
  return statsVenn.renderPoolVennSvg(data);
}

// =====================================================================
// Peer comparisons: the caller's own behaviour/choices, AND how others
// responded to them, against a geographically-scoped regional typical,
// read from the small rollup `statsAggregation.job.ts` maintains
// (`stats_region_activity`/`stats_region_tag_prevalence`) rather than
// scanned live. See this file's module doc, "COMPARISONS ARE
// AGGREGATE-VERSUS-AGGREGATE, NEVER PERSON-VERSUS-PERSON, AND NEVER A
// PUBLIC OR RANKED SIGNAL", for where the line sits.
// =====================================================================

export type DistributionPosition = 'below_typical' | 'typical' | 'above_typical' | 'insufficient_data';

export interface QuestionsAnsweredComparison {
  mine: number;
  /** Regional median, rounded to the nearest whole question. Null when the region has too little data to compare against (see `MIN_SUPPRESSIBLE_COHORT`). */
  regionTypical: number | null;
  position: DistributionPosition;
}

export interface FilterStrictnessComparison {
  myEnabledFilterCount: number;
  regionTypicalEnabledFilterCount: number | null;
  position: DistributionPosition;
  costliestFilter: FilterCostEntry | null;
}

export interface TagPrevalenceEntry {
  tagId: string;
  tagName: string;
  /** Other people near the caller who also hold this tag (the caller's own row, if any, is excluded). Suppressed below `MIN_SUPPRESSIBLE_COHORT`, same rule as every other cross-person count in this file. */
  nearbyHolders: SuppressibleCount;
}

// ---------------------------------------------------------------------
// PEER COMPARISONS: OTHERS' RESPONSES.
//
// The four numbers a person cannot see about themselves under the old
// design: how often the interests they SEND are accepted, how often the
// interests they RECEIVE convert (and how many they receive at all), and
// how their photos perform, each set against a regional typical band. All
// four already existed as the caller's own raw numbers elsewhere on this
// page (`getMyFunnel`, `getMyPhotoStats`); what changes here is only that
// this file will now also say whether that number is low, typical, or
// high for the area, the same courtesy already extended to
// `questionsAnswered`/`filterStrictness` above. See the module doc for
// why a comparison scoped to a single authenticated response, never
// stored or shown anywhere a second person's request could read it,
// carries none of the status-signal risk a public or ranked number would.
//
// `mine` is `null` (not `0`) for a RATE metric the caller has no
// denominator for yet (never sent a resolved interest, never had a photo
// impression), `0` would claim "you always get rejected," `null` says
// "not enough of your own history yet to have a rate," and the position
// is `insufficient_data` to match. `receivedInterestVolume`/
// `profileViews` are plain counts, always defined (zero is a real
// answer: zero people viewed you), so `mine` there is always a number.
// ---------------------------------------------------------------------

export interface RateComparison {
  /** 0..1, or null if the caller has no denominator for this rate yet (see section doc). */
  mine: number | null;
  /** Regional median rate, null if too few nearby people contribute a defined rate to compare against (see `..._sample_size` in the rollup and `MIN_SUPPRESSIBLE_COHORT`). */
  regionTypical: number | null;
  position: DistributionPosition;
}

export interface CountComparison {
  mine: number;
  regionTypical: number | null;
  position: DistributionPosition;
}

export interface UserStatsComparisons {
  /** False when the caller has no location on file -- every comparison below is then `insufficient_data`/empty rather than falling back to a global (and, for a local product, misleading) average. */
  hasLocation: boolean;
  /** The regional population these comparisons are drawn from. Coarser and computed differently than `currentPool`/`whoseFiltersIMatch` above (a precomputed grid cell, not a live per-viewer radius) -- see statsAggregation.job.ts's `REGION_GRID_DEGREES`. */
  regionPopulation: SuppressibleCount;
  questionsAnswered: QuestionsAnsweredComparison;
  filterStrictness: FilterStrictnessComparison;
  tagPrevalence: TagPrevalenceEntry[];
  /** How often interests the caller sends are accepted, versus what's typical nearby. */
  sentInterestAcceptance: RateComparison;
  /** How often interests the caller receives convert (get accepted), versus what's typical nearby. */
  receivedInterestConversion: RateComparison;
  /** How many interests the caller receives, versus what's typical nearby. */
  receivedInterestVolume: CountComparison;
  /** How many profile views the caller has received, versus what's typical nearby. */
  profileViews: CountComparison;
  /** The caller's overall accepted-interest rate across all their photos (interestsAccepted / impressions, summed), versus what's typical nearby. */
  photoPerformance: RateComparison;
  computedAt: Date;
}

function positionFromBand(mine: number | null, p25: number | null, p75: number | null): DistributionPosition {
  if (mine === null || p25 === null || p75 === null) return 'insufficient_data';
  if (mine < p25) return 'below_typical';
  if (mine > p75) return 'above_typical';
  return 'typical';
}

function toNullableNumber(v: string | null): number | null {
  return v === null ? null : Number(v);
}

/**
 * Builds a `RateComparison`/`CountComparison`-shaped result, gating the
 * regional side on BOTH the overall region-population suppression rule
 * (`regionHasEnoughData`, checked by the caller before this runs) and,
 * for a rate metric, this metric's OWN contributor sample size, see
 * `aggregateRegionActivity`'s doc for why a rate needs its own gate.
 * `sampleSize` is `undefined` for a metric that reads from the whole
 * (zero-included) population, i.e. it already inherits the region-level
 * gate and needs no separate one. `round`, true for a count (a "typical"
 * count of 2.5 whole interests is not meaningful, same as
 * `questionsAnswered`/`filterStrictness` above), false for a rate (0..1
 * is the natural, unrounded unit every other rate in this file uses).
 */
function bandComparison(
  mine: number | null,
  median: string | null,
  p25: string | null,
  p75: string | null,
  round: boolean,
  sampleSize?: number,
): { regionTypical: number | null; position: DistributionPosition } {
  const enoughSample = sampleSize === undefined || sampleSize >= MIN_SUPPRESSIBLE_COHORT;
  if (!enoughSample) return { regionTypical: null, position: 'insufficient_data' };
  const medianValue = toNullableNumber(median);
  return {
    regionTypical: round && medianValue !== null ? Math.round(medianValue) : medianValue,
    position: positionFromBand(mine, toNullableNumber(p25), toNullableNumber(p75)),
  };
}

interface RegionActivityRow {
  user_count: number;
  questions_answered_median: string | null;
  questions_answered_p25: string | null;
  questions_answered_p75: string | null;
  enabled_filters_median: string | null;
  enabled_filters_p25: string | null;
  enabled_filters_p75: string | null;
  sent_interest_acceptance_median: string | null;
  sent_interest_acceptance_p25: string | null;
  sent_interest_acceptance_p75: string | null;
  sent_interest_acceptance_sample_size: number;
  received_interest_conversion_median: string | null;
  received_interest_conversion_p25: string | null;
  received_interest_conversion_p75: string | null;
  received_interest_conversion_sample_size: number;
  received_interest_volume_median: string | null;
  received_interest_volume_p25: string | null;
  received_interest_volume_p75: string | null;
  profile_views_median: string | null;
  profile_views_p25: string | null;
  profile_views_p75: string | null;
  photo_performance_median: string | null;
  photo_performance_p25: string | null;
  photo_performance_p75: string | null;
  photo_performance_sample_size: number;
}

interface MyInterestRatesRow {
  sent_accepted: string;
  sent_resolved: string;
  received_total: string;
  received_accepted: string;
  received_resolved: string;
}

export async function getMyComparisons(ctx: Ctx): Promise<UserStatsComparisons> {
  const { userId } = requireUserActor(ctx);
  const now = ctx.clock.now();

  const [profileRow, questionsRow, filterCountRow, myTagRows, costs, myInterestRow, myProfileViewsRow, myPhotoRow] = await Promise.all([
    ctx.db.query<{ latitude: number | null; longitude: number | null }>(
      `SELECT latitude, longitude FROM profiles WHERE user_id = $1`,
      [userId],
    ),
    ctx.db.query<{ n: string }>(`SELECT count(*)::text AS n FROM user_question_answers WHERE user_id = $1`, [userId]),
    ctx.db.query<{ n: string }>(`SELECT count(*)::text AS n FROM hard_filters WHERE user_id = $1 AND enabled = true`, [userId]),
    ctx.db.query<{ tag_id: string; visibility: string; name: string }>(
      `SELECT ut.tag_id, ut.visibility, it.name
       FROM user_tags ut JOIN interest_tags it ON it.id = ut.tag_id
       WHERE ut.user_id = $1`,
      [userId],
    ),
    getMyFilterCosts(ctx),
    ctx.db.query<MyInterestRatesRow>(
      `SELECT
         count(*) FILTER (WHERE sender_id = $1 AND status = 'accepted')::text AS sent_accepted,
         count(*) FILTER (WHERE sender_id = $1 AND status IN ('accepted', 'declined', 'expired'))::text AS sent_resolved,
         count(*) FILTER (WHERE recipient_id = $1)::text AS received_total,
         count(*) FILTER (WHERE recipient_id = $1 AND status = 'accepted')::text AS received_accepted,
         count(*) FILTER (WHERE recipient_id = $1 AND status IN ('accepted', 'declined', 'expired'))::text AS received_resolved
       FROM interests WHERE sender_id = $1 OR recipient_id = $1`,
      [userId],
    ),
    ctx.db.query<{ n: string }>(`SELECT count(*)::text AS n FROM discovery_events WHERE candidate_user_id = $1`, [userId]),
    ctx.db.query<{ accepted: string; impressions: string }>(
      `SELECT coalesce(sum(interests_accepted), 0)::text AS accepted, coalesce(sum(impressions), 0)::text AS impressions
       FROM photo_experiments WHERE user_id = $1`,
      [userId],
    ),
  ]);

  const myQuestionsAnswered = Number(questionsRow.rows[0]?.n ?? '0');
  const myEnabledFilterCount = Number(filterCountRow.rows[0]?.n ?? '0');
  const costliestFilter = costs.costliestFilter;
  const profile = profileRow.rows[0];

  const interestRow = myInterestRow.rows[0]!;
  const sentResolved = Number(interestRow.sent_resolved);
  const mySentInterestAcceptance = sentResolved > 0 ? Number(interestRow.sent_accepted) / sentResolved : null;
  const receivedResolved = Number(interestRow.received_resolved);
  const myReceivedInterestConversion = receivedResolved > 0 ? Number(interestRow.received_accepted) / receivedResolved : null;
  const myReceivedInterestVolume = Number(interestRow.received_total);
  const myProfileViews = Number(myProfileViewsRow.rows[0]?.n ?? '0');
  const photoImpressions = Number(myPhotoRow.rows[0]?.impressions ?? '0');
  const myPhotoPerformance = photoImpressions > 0 ? Number(myPhotoRow.rows[0]!.accepted) / photoImpressions : null;

  if (!profile || profile.latitude == null || profile.longitude == null) {
    return {
      hasLocation: false,
      regionPopulation: suppressSmallCohort(0),
      questionsAnswered: { mine: myQuestionsAnswered, regionTypical: null, position: 'insufficient_data' },
      filterStrictness: {
        myEnabledFilterCount,
        regionTypicalEnabledFilterCount: null,
        position: 'insufficient_data',
        costliestFilter,
      },
      tagPrevalence: [],
      sentInterestAcceptance: { mine: mySentInterestAcceptance, regionTypical: null, position: 'insufficient_data' },
      receivedInterestConversion: { mine: myReceivedInterestConversion, regionTypical: null, position: 'insufficient_data' },
      receivedInterestVolume: { mine: myReceivedInterestVolume, regionTypical: null, position: 'insufficient_data' },
      profileViews: { mine: myProfileViews, regionTypical: null, position: 'insufficient_data' },
      photoPerformance: { mine: myPhotoPerformance, regionTypical: null, position: 'insufficient_data' },
      computedAt: now,
    };
  }

  const regionKey = regionKeyFor(profile.latitude, profile.longitude);
  const { rows: regionRows } = await ctx.db.query<RegionActivityRow>(
    `SELECT user_count, questions_answered_median, questions_answered_p25, questions_answered_p75,
            enabled_filters_median, enabled_filters_p25, enabled_filters_p75,
            sent_interest_acceptance_median, sent_interest_acceptance_p25, sent_interest_acceptance_p75, sent_interest_acceptance_sample_size,
            received_interest_conversion_median, received_interest_conversion_p25, received_interest_conversion_p75, received_interest_conversion_sample_size,
            received_interest_volume_median, received_interest_volume_p25, received_interest_volume_p75,
            profile_views_median, profile_views_p25, profile_views_p75,
            photo_performance_median, photo_performance_p25, photo_performance_p75, photo_performance_sample_size
     FROM stats_region_activity WHERE region_key = $1`,
    [regionKey],
  );
  const region = regionRows[0];
  const regionUserCount = region?.user_count ?? 0;
  const regionHasEnoughData = region !== undefined && regionUserCount >= MIN_SUPPRESSIBLE_COHORT;

  const questionsAnswered: QuestionsAnsweredComparison = regionHasEnoughData
    ? {
        mine: myQuestionsAnswered,
        regionTypical:
          region!.questions_answered_median === null ? null : Math.round(Number(region!.questions_answered_median)),
        position: positionFromBand(
          myQuestionsAnswered,
          toNullableNumber(region!.questions_answered_p25),
          toNullableNumber(region!.questions_answered_p75),
        ),
      }
    : { mine: myQuestionsAnswered, regionTypical: null, position: 'insufficient_data' };

  const filterStrictness: FilterStrictnessComparison = regionHasEnoughData
    ? {
        myEnabledFilterCount,
        regionTypicalEnabledFilterCount:
          region!.enabled_filters_median === null ? null : Math.round(Number(region!.enabled_filters_median)),
        position: positionFromBand(
          myEnabledFilterCount,
          toNullableNumber(region!.enabled_filters_p25),
          toNullableNumber(region!.enabled_filters_p75),
        ),
        costliestFilter,
      }
    : { myEnabledFilterCount, regionTypicalEnabledFilterCount: null, position: 'insufficient_data', costliestFilter };

  // Below, `regionHasEnoughData` gates every one of these the same way it
  // gates questionsAnswered/filterStrictness above (the region as a whole
  // must clear MIN_SUPPRESSIBLE_COHORT); `bandComparison` additionally
  // gates the three RATE metrics on their own contributor sample size, see
  // that function's doc and aggregateRegionActivity's doc for why a rate
  // needs a second, narrower gate the two always-defined counts do not.
  const sentInterestAcceptance: RateComparison = regionHasEnoughData
    ? {
        mine: mySentInterestAcceptance,
        ...bandComparison(
          mySentInterestAcceptance,
          region!.sent_interest_acceptance_median,
          region!.sent_interest_acceptance_p25,
          region!.sent_interest_acceptance_p75,
          false,
          region!.sent_interest_acceptance_sample_size,
        ),
      }
    : { mine: mySentInterestAcceptance, regionTypical: null, position: 'insufficient_data' };

  const receivedInterestConversion: RateComparison = regionHasEnoughData
    ? {
        mine: myReceivedInterestConversion,
        ...bandComparison(
          myReceivedInterestConversion,
          region!.received_interest_conversion_median,
          region!.received_interest_conversion_p25,
          region!.received_interest_conversion_p75,
          false,
          region!.received_interest_conversion_sample_size,
        ),
      }
    : { mine: myReceivedInterestConversion, regionTypical: null, position: 'insufficient_data' };

  const receivedInterestVolume: CountComparison = regionHasEnoughData
    ? {
        mine: myReceivedInterestVolume,
        ...bandComparison(
          myReceivedInterestVolume,
          region!.received_interest_volume_median,
          region!.received_interest_volume_p25,
          region!.received_interest_volume_p75,
          true,
        ),
      }
    : { mine: myReceivedInterestVolume, regionTypical: null, position: 'insufficient_data' };

  const profileViews: CountComparison = regionHasEnoughData
    ? {
        mine: myProfileViews,
        ...bandComparison(myProfileViews, region!.profile_views_median, region!.profile_views_p25, region!.profile_views_p75, true),
      }
    : { mine: myProfileViews, regionTypical: null, position: 'insufficient_data' };

  const photoPerformance: RateComparison = regionHasEnoughData
    ? {
        mine: myPhotoPerformance,
        ...bandComparison(
          myPhotoPerformance,
          region!.photo_performance_median,
          region!.photo_performance_p25,
          region!.photo_performance_p75,
          false,
          region!.photo_performance_sample_size,
        ),
      }
    : { mine: myPhotoPerformance, regionTypical: null, position: 'insufficient_data' };

  let tagPrevalence: TagPrevalenceEntry[] = [];
  if (myTagRows.rows.length > 0) {
    const tagIds = myTagRows.rows.map((r) => r.tag_id);
    const { rows: prevalenceRows } = await ctx.db.query<{ tag_id: string; user_count: number }>(
      `SELECT tag_id, user_count FROM stats_region_tag_prevalence WHERE region_key = $1 AND tag_id = ANY($2::uuid[])`,
      [regionKey, tagIds],
    );
    const prevalenceByTag = new Map(prevalenceRows.map((r) => [r.tag_id, r.user_count]));
    tagPrevalence = myTagRows.rows.map((t) => {
      const raw = prevalenceByTag.get(t.tag_id) ?? 0;
      // The rollup counts the caller's own row too, if their tag wasn't
      // hidden -- subtract self so "nearby holders" means OTHER people,
      // matching every other SuppressibleCount in this file.
      const others = Math.max(0, raw - (t.visibility === 'hidden' ? 0 : 1));
      return { tagId: t.tag_id, tagName: t.name, nearbyHolders: suppressSmallCohort(others) };
    });
  }

  return {
    hasLocation: true,
    regionPopulation: suppressSmallCohort(regionUserCount),
    questionsAnswered,
    filterStrictness,
    tagPrevalence,
    sentInterestAcceptance,
    receivedInterestConversion,
    receivedInterestVolume,
    profileViews,
    photoPerformance,
    computedAt: now,
  };
}
