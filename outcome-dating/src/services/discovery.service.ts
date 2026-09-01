import type { Ctx } from '../lib/ctx.js';
import { NotImplementedError } from '../lib/errors.js';
import type { Block, DiscoveryCandidate, Page, RealityDashboard } from '../domain/types.js';

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
 */

export interface DiscoveryGridParams {
  limit?: number;
  cursor?: string;
}

export async function getDiscoveryGrid(ctx: Ctx, params: DiscoveryGridParams): Promise<Page<DiscoveryCandidate>> {
  throw new NotImplementedError('discovery.getDiscoveryGrid');
}

/** §9.3 "Reality Dashboard": X = filter.countUsersMatchingMyFilters, Y = filter.countUsersWhoseFiltersIMatch, Z = mutual pool size (both directions, further reduced by capacity/moderation gates). */
export async function getRealityDashboard(ctx: Ctx): Promise<RealityDashboard> {
  throw new NotImplementedError('discovery.getRealityDashboard');
}

/** Records a `discovery_events` row and forwards to `photoExperiment.service#recordImpression` when the shown card used an experiment photo (spec §7.3 rule 3, §23.11). */
export async function recordDiscoveryImpression(ctx: Ctx, candidateUserId: string, primaryPhotoId: string | null): Promise<void> {
  throw new NotImplementedError('discovery.recordDiscoveryImpression');
}

/** The full §10.2 nine-point visibility check for one candidate as seen by one viewer. `getDiscoveryGrid` is expected to use a batch-friendly equivalent internally, not call this per-row, but this is the spec-traceable unit both should agree with. */
export async function isProfileVisibleTo(ctx: Ctx, viewerUserId: string, candidateUserId: string): Promise<boolean> {
  throw new NotImplementedError('discovery.isProfileVisibleTo');
}

// ---- Blocking (§24.5 POST /profiles/{userId}/block) ----

export async function blockUser(ctx: Ctx, targetUserId: string): Promise<Block> {
  throw new NotImplementedError('discovery.blockUser');
}

export async function unblockUser(ctx: Ctx, targetUserId: string): Promise<void> {
  throw new NotImplementedError('discovery.unblockUser');
}

export async function listBlockedUsers(ctx: Ctx): Promise<Block[]> {
  throw new NotImplementedError('discovery.listBlockedUsers');
}

/** True if either user has blocked the other (spec §10.2 rule 9 is symmetric even though the row is directional). */
export async function isEitherBlocked(ctx: Ctx, userId: string, otherUserId: string): Promise<boolean> {
  throw new NotImplementedError('discovery.isEitherBlocked');
}
