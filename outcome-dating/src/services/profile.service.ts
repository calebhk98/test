import type { Ctx } from '../lib/ctx.js';
import { NotImplementedError } from '../lib/errors.js';
import type { Profile, TrustLevel } from '../domain/types.js';

/**
 * profile.service — the user-editable profile (§7.1) and the public view
 * of another user's profile.
 * Spec: §7.1, §24.2, §9.4 (completeness), §28.5/§7.1 (location privacy).
 *
 * Owning agent: A.
 *
 * Invariant: `latitude`/`longitude` on `profiles` are NEVER returned by
 * `getPublicProfile` — only `approximateDistanceKm`, computed server-side
 * and coarsened (spec §7.1 "Exact location MUST NOT be shown", §28.5).
 * `getMyProfile` (the owner viewing their own data) is the one place true
 * coordinates may be returned.
 */

export interface UpdateProfileInput {
  displayName?: string;
  bio?: string;
  city?: string;
  latitude?: number;
  longitude?: number;
  age?: number;
  gender?: string;
  seeking?: string;
  relationshipIntention?: string;
}

/** Richer than a discovery.DiscoveryCandidate card: full bio, prompts, tags, photos — but still location-fuzzed (§7.1). */
export interface PublicProfileView {
  userId: string;
  displayName: string;
  age: number;
  approximateDistanceKm: number | null;
  bio: string;
  photoUrls: string[];
  trustLevel: TrustLevel;
  /** Public + reciprocally-visible tags only (§8.4) — never a tag the viewer doesn't share when it's `private_reciprocal`. */
  visibleInterestTagNames: string[];
}

export async function getMyProfile(ctx: Ctx): Promise<Profile> {
  throw new NotImplementedError('profile.getMyProfile');
}

/** Upserts the caller's profile and recomputes `profileCompleteness` (§9.4). */
export async function updateMyProfile(ctx: Ctx, patch: UpdateProfileInput): Promise<Profile> {
  throw new NotImplementedError('profile.updateMyProfile');
}

/**
 * Fetch another user's profile as the caller would see it. Throws
 * `NotFoundError` if the target doesn't exist; throws `ForbiddenError` if
 * the caller has blocked or is blocked by the target (mirrors the
 * discovery visibility rule, spec §10.2 rule 9) — viewing a full profile
 * page should not be a backdoor around a block.
 */
export async function getPublicProfile(ctx: Ctx, targetUserId: string): Promise<PublicProfileView> {
  throw new NotImplementedError('profile.getPublicProfile');
}

/**
 * Pure-ish scoring of how complete a profile is (0-100), per §7.1/§9.4.
 * Exposed separately from `updateMyProfile` so `discovery.service.ts`'s
 * visibility rule ("profile is complete enough", §10.2 rule 3) and the
 * §25 nightly jobs can recompute without going through the update path.
 */
export async function computeProfileCompleteness(ctx: Ctx, userId: string): Promise<number> {
  throw new NotImplementedError('profile.computeProfileCompleteness');
}
