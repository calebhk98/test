import type { Ctx } from '../lib/ctx.js';
import { requireUserActor } from '../lib/ctx.js';
import { ValidationError } from '../lib/errors.js';
import type { Block, DiscoveryCandidate, Page, RealityDashboard, TrustLevel } from '../domain/types.js';
import { passesMutualFilters, countUsersMatchingMyFilters, countUsersWhoseFiltersIMatch, haversineKm } from './filter.service.js';
import { getScoresForCandidates } from './compatibility.service.js';
import { isVisibleInDiscovery } from './moderation.service.js';
import { resolveVisibleTagsFor } from './question.service.js';
import * as photoExperiment from './photoExperiment.service.js';

/**
 * discovery.service — the discovery grid, visibility rules, the §9.3
 * reality dashboard, and block/report entry points (both live under
 * `/profiles/{userId}/...` in §24.5, alongside discovery).
 * Spec: §10, §9.3, §24.5.
 *
 * Owning agent: B.
 *
 * `getDiscoveryGrid` composes four other modules and MUST call them in
 * this order/role (see INTERFACES.md invariants table):
 *   1. `filter.service#passesMutualFilters` — hard gate, spec §9.1/§16.1.
 *   2. `moderation.service#isVisibleInDiscovery` (shadowban/suspension) and
 *      the capacity rules (§10.2 rules 5-6: incoming interest/active
 *      conversation caps) — also hard gates, not sorting.
 *   3. `compatibility.service#getScoresForCandidates` — sort key only
 *      (§10.3); MUST NOT remove anyone (§10.3 "No compatibility threshold
 *      hides users").
 *   4. Tie-break by trust score, profile completeness, recent activity,
 *      response rate (§10.3), in that order.
 *
 * Blocking is bidirectional for visibility purposes (spec §10.2 rule 9)
 * even though `blocks` rows are directional — `isEitherBlocked` checks
 * both directions.
 *
 * CROSS-DOMAIN TABLE READS: this module reads `profiles`/`user_photos`/
 * `interests`/`conversations` directly via SQL rather than through a
 * service call. INTERFACES.md's "may call" column for `discovery.service`
 * is `filter, compatibility, trust, moderation, photoExperiment` — it does
 * NOT list `interest`/`conversation`/`profile`, yet §10.2 rules 3-6 need
 * exactly that data (profile completeness, photo approval, pending-interest
 * count, active-conversation count) and no sanctioned service call exposes
 * it in bulk. Direct reads of another domain's tables (not calling that
 * domain's *service functions*, which would be the actual boundary
 * violation) match the pattern already established elsewhere in this
 * codebase (e.g. `compatibility.service` reading `answers`/`questions`
 * directly). "trust score" for the §10.3 tie-break is likewise read
 * directly from `users.trust_score` — `trust.service.ts` has no bulk/
 * other-user read function to call instead (its exports are all
 * caller's-own-data: `getMyTrustSummary`, `recordTrustEvent`, ...).
 *
 * SIGNATURE ADDITION (flagged): this file calls
 * `question.service#resolveVisibleTagsFor` to populate
 * `DiscoveryCandidate.sharedInterestTag` (§10.1 "maybe one shared
 * interest") — see the "SIGNATURE ADDITION" note at the top of
 * `question.service.ts` for why that function exists and why this edge
 * isn't in INTERFACES.md's authoritative call-graph diagram either.
 */

// =====================================================================
// Pure ranking (exported for direct unit testing without a DB — see
// tests/unit/discovery.test.ts).
// =====================================================================

/** Everything `sortDiscoveryCandidates` needs beyond the public `DiscoveryCandidate` shape. `trustScore` is the raw 0-100 number (§10.3 "trust score"); `DiscoveryCandidate` itself only carries the coarser `trustLevel` (§6.1's "don't expose the exact number" is a *user-facing display* rule, not a constraint on this internal sort key). */
export interface DiscoveryRankingInput {
  candidate: DiscoveryCandidate;
  trustScore: number;
  lastActiveAt: Date;
  responseRate: number; // 0-1
}

/**
 * §10.3 sort: compatibility DESC, then trust score, profile completeness,
 * recent activity, response rate, all DESC, as tie-breakers in that order.
 * Pure and total — never removes an entry (§10.3/§16.1 "no compatibility
 * threshold hides users": filtering happens upstream, in
 * `computeRankedCandidatePool`, before this function ever sees a
 * candidate). A candidate with `compatibilityScore === 0` sorts strictly
 * after every candidate with a higher score, but is never dropped.
 */
export function sortDiscoveryCandidates(inputs: DiscoveryRankingInput[]): DiscoveryCandidate[] {
  return [...inputs]
    .sort((a, b) => {
      if (b.candidate.compatibilityScore !== a.candidate.compatibilityScore) {
        return b.candidate.compatibilityScore - a.candidate.compatibilityScore;
      }
      if (b.trustScore !== a.trustScore) return b.trustScore - a.trustScore;
      if (b.candidate.profileCompleteness !== a.candidate.profileCompleteness) {
        return b.candidate.profileCompleteness - a.candidate.profileCompleteness;
      }
      const activityDiff = b.lastActiveAt.getTime() - a.lastActiveAt.getTime();
      if (activityDiff !== 0) return activityDiff;
      return b.responseRate - a.responseRate;
    })
    .map((i) => i.candidate);
}

// =====================================================================
// §10.2 rule 3 "profile is complete enough" threshold, 0-100.
//
// DECISION-LAYER UPDATE: this used to be a local constant (`src/config/
// config.service.ts` was outside this agent's file-ownership boundary
// during the parallel build). It is now backed by the real
// `discovery.min_profile_completeness` config key (default still `50`,
// unchanged) — `loadCandidatePool`/`isProfileVisibleTo` read it from
// `ctx.config`. This constant is kept, still equal to the config default,
// only as a fallback for any call site that can't await `ctx.config`.
// =====================================================================
export const MIN_PROFILE_COMPLETENESS_FOR_DISCOVERY = 50;

const DEFAULT_PAGE_LIMIT = 20;
const MAX_PAGE_LIMIT = 100;

function clampLimit(limit: number | undefined): number {
  if (limit === undefined || !Number.isFinite(limit) || limit <= 0) return DEFAULT_PAGE_LIMIT;
  return Math.min(Math.floor(limit), MAX_PAGE_LIMIT);
}

function parseCursorOffset(cursor: string | undefined): number {
  if (!cursor) return 0;
  const n = Number.parseInt(cursor, 10);
  return Number.isFinite(n) && n >= 0 ? n : 0;
}

// =====================================================================
// Candidate pool + ranking assembly
// =====================================================================

interface CandidatePoolRow {
  id: string;
  trust_score: number;
  trust_level: TrustLevel;
  last_active_at: Date;
  display_name: string;
  age: number;
  latitude: number | null;
  longitude: number | null;
  profile_completeness: number;
  primary_photo_id: string | null;
  primary_photo_url: string | null;
}

async function loadCandidatePool(ctx: Ctx, viewerId: string): Promise<CandidatePoolRow[]> {
  const minProfileCompleteness = await ctx.config.get('discovery.min_profile_completeness');
  const { rows } = await ctx.db.query<CandidatePoolRow>(
    `SELECT
       u.id,
       u.trust_score,
       u.trust_level,
       u.last_active_at,
       p.display_name,
       p.age,
       p.latitude,
       p.longitude,
       p.profile_completeness,
       ph.id AS primary_photo_id,
       ph.image_url AS primary_photo_url
     FROM users u
     JOIN profiles p ON p.user_id = u.id
     LEFT JOIN user_photos ph
       ON ph.user_id = u.id AND ph.is_primary AND ph.moderation_status = 'approved'
     WHERE u.id <> $1
       AND u.status = 'active'
       AND p.profile_completeness >= $2
       AND EXISTS (SELECT 1 FROM user_photos ap WHERE ap.user_id = u.id AND ap.moderation_status = 'approved')
       AND NOT EXISTS (
         SELECT 1 FROM blocks b
         WHERE (b.blocker_id = $1 AND b.blocked_id = u.id) OR (b.blocker_id = u.id AND b.blocked_id = $1)
       )`,
    [viewerId, minProfileCompleteness],
  );
  return rows;
}

async function loadPendingIncomingCounts(ctx: Ctx, candidateIds: string[]): Promise<Map<string, number>> {
  if (candidateIds.length === 0) return new Map();
  const { rows } = await ctx.db.query<{ recipient_id: string; count: string }>(
    `SELECT recipient_id, count(*)::text AS count
     FROM interests
     WHERE recipient_id = ANY($1::uuid[]) AND status = 'pending'
     GROUP BY recipient_id`,
    [candidateIds],
  );
  return new Map(rows.map((r) => [r.recipient_id, Number(r.count)]));
}

async function loadActiveConversationCounts(ctx: Ctx, candidateIds: string[]): Promise<Map<string, number>> {
  if (candidateIds.length === 0) return new Map();
  const { rows } = await ctx.db.query<{ candidate_id: string; count: string }>(
    `SELECT candidate_id, count(*)::text AS count FROM (
       SELECT user_a_id AS candidate_id FROM conversations WHERE status = 'active' AND user_a_id = ANY($1::uuid[])
       UNION ALL
       SELECT user_b_id AS candidate_id FROM conversations WHERE status = 'active' AND user_b_id = ANY($1::uuid[])
     ) t
     GROUP BY candidate_id`,
    [candidateIds],
  );
  return new Map(rows.map((r) => [r.candidate_id, Number(r.count)]));
}

/**
 * §10.3 "response rate" tie-break, per candidate as an interest *recipient*:
 * (accepted + declined) / (accepted + declined + expired). `canceled` (the
 * sender withdrew) is excluded from the denominator — the recipient never
 * had an opportunity to respond, so it shouldn't count against them.
 * Candidates with no resolved history default to 0 (last-resort tie-break;
 * documented as the simplest defensible default rather than an
 * artificially inflated "neutral" score).
 */
async function loadResponseRates(ctx: Ctx, candidateIds: string[]): Promise<Map<string, number>> {
  if (candidateIds.length === 0) return new Map();
  const { rows } = await ctx.db.query<{ recipient_id: string; responded: string; opportunities: string }>(
    `SELECT
       recipient_id,
       count(*) FILTER (WHERE status IN ('accepted', 'declined'))::text AS responded,
       count(*) FILTER (WHERE status IN ('accepted', 'declined', 'expired'))::text AS opportunities
     FROM interests
     WHERE recipient_id = ANY($1::uuid[])
     GROUP BY recipient_id`,
    [candidateIds],
  );
  const result = new Map<string, number>();
  for (const r of rows) {
    const opportunities = Number(r.opportunities);
    result.set(r.recipient_id, opportunities > 0 ? Number(r.responded) / opportunities : 0);
  }
  return result;
}

async function loadViewerProfile(ctx: Ctx, viewerId: string): Promise<{ latitude: number | null; longitude: number | null }> {
  const { rows } = await ctx.db.query<{ latitude: number | null; longitude: number | null }>(
    'SELECT latitude, longitude FROM profiles WHERE user_id = $1',
    [viewerId],
  );
  return rows[0] ?? { latitude: null, longitude: null };
}

async function loadViewerOwnTagIds(ctx: Ctx, viewerId: string): Promise<Set<string>> {
  const { rows } = await ctx.db.query<{ tag_id: string }>('SELECT tag_id FROM user_tags WHERE user_id = $1', [
    viewerId,
  ]);
  return new Set(rows.map((r) => r.tag_id));
}

/** Rounds a distance in km to the nearest whole km — an approximate value only (spec §7.1/§28.5: never expose exact coordinates or a precise distance). */
function toApproximateDistanceKm(km: number): number {
  return Math.round(km);
}

/**
 * The full §10.2 gate + §16.3 scoring + ranking-field assembly for every
 * candidate eligible to appear in `viewerId`'s discovery grid, unsorted.
 * Both `getDiscoveryGrid` (paginates the sorted result) and
 * `getRealityDashboard` (`Z` = `.length`) build on this shared pipeline so
 * they can never disagree about who is in the pool.
 */
async function computeRankedCandidatePool(ctx: Ctx, viewerId: string): Promise<DiscoveryRankingInput[]> {
  const pool = await loadCandidatePool(ctx, viewerId);
  if (pool.length === 0) return [];

  const candidateIds = pool.map((r) => r.id);
  const [pendingCounts, activeConvCounts, responseRates, viewerProfile, viewerTagIds] = await Promise.all([
    loadPendingIncomingCounts(ctx, candidateIds),
    loadActiveConversationCounts(ctx, candidateIds),
    loadResponseRates(ctx, candidateIds),
    loadViewerProfile(ctx, viewerId),
    loadViewerOwnTagIds(ctx, viewerId),
  ]);

  const incomingLimit = await ctx.config.get('interest.incoming_pending_limit');
  const activeConvLimit = await ctx.config.get('chat.active_limit');

  const survivors: CandidatePoolRow[] = [];
  const sharedTagByCandidate = new Map<string, string | null>();

  for (const row of pool) {
    // §10.2 rule 5: incoming pending interests < cap.
    if ((pendingCounts.get(row.id) ?? 0) >= incomingLimit) continue;
    // §10.2 rule 6: active conversations < cap.
    if ((activeConvCounts.get(row.id) ?? 0) >= activeConvLimit) continue;
    // §10.2 rules 1-2: active/not shadowbanned/not suspended.
    if (!(await isVisibleInDiscovery(ctx, row.id))) continue;
    // §10.2 rules 7-8: mutual hard filters (spec §9.1 — the invariant this whole module exists to protect).
    if (!(await passesMutualFilters(ctx, viewerId, row.id))) continue;

    survivors.push(row);

    // §10.1 "maybe one shared interest" — §8.4-respecting: only tags this
    // viewer is actually allowed to see, intersected with the viewer's own.
    const visibleTags = await resolveVisibleTagsFor(ctx, viewerId, row.id);
    const shared = visibleTags.find((t) => viewerTagIds.has(t.tagId));
    sharedTagByCandidate.set(row.id, shared?.name ?? null);
  }

  if (survivors.length === 0) return [];

  const scores = await getScoresForCandidates(ctx, viewerId, survivors.map((r) => r.id));

  return survivors.map((row) => {
    const approximateDistanceKm =
      row.latitude != null && row.longitude != null && viewerProfile.latitude != null && viewerProfile.longitude != null
        ? toApproximateDistanceKm(haversineKm(viewerProfile.latitude, viewerProfile.longitude, row.latitude, row.longitude))
        : null;

    const candidate: DiscoveryCandidate = {
      userId: row.id,
      displayName: row.display_name,
      age: row.age,
      approximateDistanceKm,
      primaryPhotoUrl: row.primary_photo_url,
      sharedInterestTag: sharedTagByCandidate.get(row.id) ?? null,
      compatibilityScore: scores.get(row.id) ?? 0,
      trustLevel: row.trust_level,
      profileCompleteness: row.profile_completeness,
    };

    return {
      candidate,
      trustScore: row.trust_score,
      lastActiveAt: row.last_active_at,
      responseRate: responseRates.get(row.id) ?? 0,
    };
  });
}

export interface DiscoveryGridParams {
  limit?: number;
  cursor?: string;
}

/**
 * §30.1 "no candidates" and §30.3 "recipient inbox full" are both
 * satisfied structurally, not as special cases: an empty `items` array
 * (with the reality dashboard counts available separately via
 * `getRealityDashboard` for the caller to render alongside the §30.1 static
 * copy) is exactly what a fully-filtered pool produces, and an inbox-full
 * candidate is excluded by the §10.2 rule-5 capacity check inside
 * `computeRankedCandidatePool` before it ever reaches sorting.
 *
 * Does NOT itself call `recordDiscoveryImpression` — call that once per
 * card actually rendered to the viewer (e.g. scrolled into view), not for
 * every row a page happens to return, so impression counts reflect what
 * was actually seen (feeds Agent A's photo A/B stats, §7.3).
 */
export async function getDiscoveryGrid(ctx: Ctx, params: DiscoveryGridParams): Promise<Page<DiscoveryCandidate>> {
  const { userId } = requireUserActor(ctx);
  const limit = clampLimit(params.limit);
  const offset = parseCursorOffset(params.cursor);

  const ranked = await computeRankedCandidatePool(ctx, userId);
  const sorted = sortDiscoveryCandidates(ranked);

  const items = sorted.slice(offset, offset + limit);
  const nextCursor = offset + limit < sorted.length ? String(offset + limit) : null;

  return { items, nextCursor };
}

/** §9.3 "Reality Dashboard": X = filter.countUsersMatchingMyFilters, Y = filter.countUsersWhoseFiltersIMatch, Z = mutual pool size (both directions, further reduced by capacity/moderation gates). */
export async function getRealityDashboard(ctx: Ctx): Promise<RealityDashboard> {
  const { userId } = requireUserActor(ctx);
  const [matchesMyFilters, whoseFiltersIMatch, ranked] = await Promise.all([
    countUsersMatchingMyFilters(ctx, userId),
    countUsersWhoseFiltersIMatch(ctx, userId),
    computeRankedCandidatePool(ctx, userId),
  ]);
  return { matchesMyFilters, whoseFiltersIMatch, mutualMatchPool: ranked.length };
}

/** Records a `discovery_events` row and forwards to `photoExperiment.service#recordImpression` when the shown card used an experiment photo (spec §7.3 rule 3, §23.11). */
export async function recordDiscoveryImpression(ctx: Ctx, candidateUserId: string, primaryPhotoId: string | null): Promise<void> {
  const { userId } = requireUserActor(ctx);
  await ctx.db.query(
    `INSERT INTO discovery_events (viewer_user_id, candidate_user_id, primary_photo_id, source, created_at)
     VALUES ($1, $2, $3, 'discovery_grid', $4)`,
    [userId, candidateUserId, primaryPhotoId, ctx.clock.now()],
  );
  if (primaryPhotoId) {
    // `photoExperiment.recordImpression` itself decides whether this photo
    // is part of an active experiment (>=3 photos, flag on, §7.3 rule 1) —
    // this call site doesn't duplicate that judgment, it just always
    // forwards when a primary photo was actually shown.
    await photoExperiment.recordImpression(ctx, { candidateUserId, photoId: primaryPhotoId });
  }
}

/** The full §10.2 nine-point visibility check for one candidate as seen by one viewer. `getDiscoveryGrid` is expected to use a batch-friendly equivalent internally, not call this per-row, but this is the spec-traceable unit both should agree with. */
export async function isProfileVisibleTo(ctx: Ctx, viewerUserId: string, candidateUserId: string): Promise<boolean> {
  if (viewerUserId === candidateUserId) return false;

  const { rows: userRows } = await ctx.db.query<{ status: string }>('SELECT status FROM users WHERE id = $1', [
    candidateUserId,
  ]);
  const candidateUser = userRows[0];
  if (!candidateUser || candidateUser.status !== 'active') return false; // rule 1

  if (!(await isVisibleInDiscovery(ctx, candidateUserId))) return false; // rule 2 (shadowban/suspension)

  const { rows: profileRows } = await ctx.db.query<{ profile_completeness: number }>(
    'SELECT profile_completeness FROM profiles WHERE user_id = $1',
    [candidateUserId],
  );
  const profile = profileRows[0];
  const minProfileCompleteness = await ctx.config.get('discovery.min_profile_completeness');
  if (!profile || profile.profile_completeness < minProfileCompleteness) return false; // rule 3

  const { rows: photoRows } = await ctx.db.query<{ has_approved: boolean }>(
    `SELECT EXISTS(SELECT 1 FROM user_photos WHERE user_id = $1 AND moderation_status = 'approved') AS has_approved`,
    [candidateUserId],
  );
  if (!photoRows[0]?.has_approved) return false; // rule 4

  const incomingLimit = await ctx.config.get('interest.incoming_pending_limit');
  const { rows: incomingRows } = await ctx.db.query<{ count: string }>(
    `SELECT count(*)::text AS count FROM interests WHERE recipient_id = $1 AND status = 'pending'`,
    [candidateUserId],
  );
  if (Number(incomingRows[0]!.count) >= incomingLimit) return false; // rule 5

  const activeConvLimit = await ctx.config.get('chat.active_limit');
  const { rows: convRows } = await ctx.db.query<{ count: string }>(
    `SELECT count(*)::text AS count FROM conversations WHERE (user_a_id = $1 OR user_b_id = $1) AND status = 'active'`,
    [candidateUserId],
  );
  if (Number(convRows[0]!.count) >= activeConvLimit) return false; // rule 6

  if (!(await passesMutualFilters(ctx, viewerUserId, candidateUserId))) return false; // rules 7-8

  if (await isEitherBlocked(ctx, viewerUserId, candidateUserId)) return false; // rule 9

  return true;
}

// ---- Blocking (§24.5 POST /profiles/{userId}/block) ----

interface BlockRow {
  id: string;
  blocker_id: string;
  blocked_id: string;
  created_at: Date;
}

function blockFromRow(row: BlockRow): Block {
  return { id: row.id, blockerId: row.blocker_id, blockedId: row.blocked_id, createdAt: row.created_at };
}

export async function blockUser(ctx: Ctx, targetUserId: string): Promise<Block> {
  const { userId } = requireUserActor(ctx);
  if (userId === targetUserId) {
    throw new ValidationError('Cannot block yourself', { targetUserId });
  }
  const { rows } = await ctx.db.query<BlockRow>(
    `INSERT INTO blocks (blocker_id, blocked_id, created_at)
     VALUES ($1, $2, $3)
     ON CONFLICT (blocker_id, blocked_id) DO UPDATE SET created_at = blocks.created_at
     RETURNING *`,
    [userId, targetUserId, ctx.clock.now()],
  );
  return blockFromRow(rows[0]!);
}

export async function unblockUser(ctx: Ctx, targetUserId: string): Promise<void> {
  const { userId } = requireUserActor(ctx);
  await ctx.db.query('DELETE FROM blocks WHERE blocker_id = $1 AND blocked_id = $2', [userId, targetUserId]);
}

export async function listBlockedUsers(ctx: Ctx): Promise<Block[]> {
  const { userId } = requireUserActor(ctx);
  const { rows } = await ctx.db.query<BlockRow>('SELECT * FROM blocks WHERE blocker_id = $1 ORDER BY created_at DESC', [
    userId,
  ]);
  return rows.map(blockFromRow);
}

/** True if either user has blocked the other (spec §10.2 rule 9 is symmetric even though the row is directional). */
export async function isEitherBlocked(ctx: Ctx, userId: string, otherUserId: string): Promise<boolean> {
  const { rows } = await ctx.db.query<{ count: string }>(
    `SELECT count(*)::text AS count FROM blocks
     WHERE (blocker_id = $1 AND blocked_id = $2) OR (blocker_id = $2 AND blocked_id = $1)`,
    [userId, otherUserId],
  );
  return Number(rows[0]!.count) > 0;
}
