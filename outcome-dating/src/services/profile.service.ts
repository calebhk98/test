import { z } from 'zod';
import type { Ctx } from '../lib/ctx.js';
import { requireUserActor } from '../lib/ctx.js';
import { ForbiddenError, NotFoundError, ValidationError } from '../lib/errors.js';
import type { Profile, TrustLevel } from '../domain/types.js';
import * as discovery from './discovery.service.js';

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
 * coordinates may be returned. This is enforced structurally, not just by
 * convention: `PublicProfileView` (below) has no coordinate fields at all,
 * and `getPublicProfile` is the only function in this file that returns
 * that type — there is no code path that can accidentally leak a
 * candidate's raw lat/long, because the type it hands back cannot carry one.
 *
 * Beyond the frozen export list (`getMyProfile`, `updateMyProfile`,
 * `getPublicProfile`, `computeProfileCompleteness`), this file adds
 * `deleteMyAccount` and `exportMyData` (§29 privacy requirements — account
 * deletion + data export). INTERFACES.md's module table doesn't enumerate
 * these for `profile.service`, but nothing in the "may call" graph lists
 * another service importing from `profile.service` (only the reverse:
 * `profile -> discovery`), so adding exports here cannot break a sibling's
 * compile. Flagged in the build report for the API agent to route.
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
  /**
   * Required to be `true` when the patch touches a "critical" field
   * (currently: gender, seeking, relationshipIntention, age — the fields
   * that most directly change who the user matches with) on an *existing*
   * profile (spec §30.8 "Show confirmation before saving critical fields").
   * Omitted/false on a critical-field patch throws a `ValidationError`
   * carrying `details.requiresConfirmation` and the static warning copy —
   * never generated text.
   */
  confirmCriticalChange?: boolean;
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

/** §30.8 static warning copy — never generated text. Mirrors the spec's own example ("This answer may significantly change your matches.") for the profile-field-change case. */
export const CRITICAL_FIELD_CHANGE_WARNING =
  'This change may significantly change your matches.';

/** Profile fields whose change requires explicit confirmation (§30.8) — they most directly drive matching/filtering. */
const CRITICAL_FIELDS = ['gender', 'seeking', 'relationshipIntention', 'age'] as const;
type CriticalField = (typeof CRITICAL_FIELDS)[number];

const UpdateProfileSchema = z.object({
  displayName: z.string().trim().min(1).max(80).optional(),
  bio: z.string().trim().max(2000).optional(),
  city: z.string().trim().min(1).max(200).optional(),
  latitude: z.number().min(-90).max(90).optional(),
  longitude: z.number().min(-180).max(180).optional(),
  age: z.number().int().min(18).max(120).optional(),
  gender: z.string().trim().min(1).max(50).optional(),
  seeking: z.string().trim().min(1).max(50).optional(),
  relationshipIntention: z.string().trim().min(1).max(50).optional(),
  confirmCriticalChange: z.boolean().optional(),
});

// =====================================================================
// Row mapping
// =====================================================================

interface ProfileRow {
  user_id: string;
  display_name: string;
  bio: string;
  city: string | null;
  latitude: number | null;
  longitude: number | null;
  location_fuzzed: boolean;
  age: number;
  gender: string;
  seeking: string;
  relationship_intention: string;
  profile_completeness: number;
  updated_at: Date;
}

function mapProfile(row: ProfileRow): Profile {
  return {
    userId: row.user_id,
    displayName: row.display_name,
    bio: row.bio,
    city: row.city,
    latitude: row.latitude,
    longitude: row.longitude,
    locationFuzzed: row.location_fuzzed,
    age: row.age,
    gender: row.gender,
    seeking: row.seeking,
    relationshipIntention: row.relationship_intention,
    profileCompleteness: row.profile_completeness,
    updatedAt: row.updated_at,
  };
}

async function fetchProfileRow(ctx: Ctx, userId: string): Promise<ProfileRow | undefined> {
  const { rows } = await ctx.db.query<ProfileRow>(
    `SELECT user_id, display_name, bio, city, latitude, longitude, location_fuzzed, age, gender, seeking, relationship_intention, profile_completeness, updated_at
     FROM profiles WHERE user_id = $1`,
    [userId],
  );
  return rows[0];
}

// =====================================================================
// getMyProfile / updateMyProfile
// =====================================================================

export async function getMyProfile(ctx: Ctx): Promise<Profile> {
  const { userId } = requireUserActor(ctx);
  const row = await fetchProfileRow(ctx, userId);
  if (!row) {
    throw new NotFoundError('You have not created a profile yet.');
  }
  return mapProfile(row);
}

/** Upserts the caller's profile and recomputes `profileCompleteness` (§9.4). */
export async function updateMyProfile(ctx: Ctx, patch: UpdateProfileInput): Promise<Profile> {
  const { userId } = requireUserActor(ctx);
  const parsed = UpdateProfileSchema.parse(patch);

  const existing = await fetchProfileRow(ctx, userId);

  if (existing) {
    const currentByField: Record<CriticalField, unknown> = {
      gender: existing.gender,
      seeking: existing.seeking,
      relationshipIntention: existing.relationship_intention,
      age: existing.age,
    };
    const touchedCritical = CRITICAL_FIELDS.filter((field: CriticalField) => {
      if (parsed[field] === undefined) return false;
      return parsed[field] !== currentByField[field];
    });
    if (touchedCritical.length > 0 && !parsed.confirmCriticalChange) {
      throw new ValidationError(CRITICAL_FIELD_CHANGE_WARNING, {
        requiresConfirmation: true,
        criticalFields: touchedCritical,
        warning: CRITICAL_FIELD_CHANGE_WARNING,
      });
    }
  } else {
    // First-time profile creation requires the full required field set —
    // there is no "prior value" to change, so no confirmation applies, but
    // every NOT NULL column needs a value.
    const required: Array<keyof typeof parsed> = ['displayName', 'age', 'gender', 'seeking', 'relationshipIntention'];
    const missing = required.filter((f) => parsed[f] === undefined);
    if (missing.length > 0) {
      throw new ValidationError('Missing required profile field(s) for initial profile creation.', { missing });
    }
  }

  const merged = {
    displayName: parsed.displayName ?? existing?.display_name,
    bio: parsed.bio ?? existing?.bio ?? '',
    city: parsed.city ?? existing?.city ?? null,
    latitude: parsed.latitude ?? existing?.latitude ?? null,
    longitude: parsed.longitude ?? existing?.longitude ?? null,
    age: parsed.age ?? existing?.age,
    gender: parsed.gender ?? existing?.gender,
    seeking: parsed.seeking ?? existing?.seeking,
    relationshipIntention: parsed.relationshipIntention ?? existing?.relationship_intention,
  };

  const now = ctx.clock.now();

  const { rows } = await ctx.db.query<ProfileRow>(
    `INSERT INTO profiles (user_id, display_name, bio, city, latitude, longitude, location_fuzzed, age, gender, seeking, relationship_intention, profile_completeness, updated_at)
     VALUES ($1, $2, $3, $4, $5, $6, true, $7, $8, $9, $10, 0, $11)
     ON CONFLICT (user_id) DO UPDATE SET
       display_name = EXCLUDED.display_name,
       bio = EXCLUDED.bio,
       city = EXCLUDED.city,
       latitude = EXCLUDED.latitude,
       longitude = EXCLUDED.longitude,
       age = EXCLUDED.age,
       gender = EXCLUDED.gender,
       seeking = EXCLUDED.seeking,
       relationship_intention = EXCLUDED.relationship_intention,
       updated_at = EXCLUDED.updated_at
     RETURNING user_id, display_name, bio, city, latitude, longitude, location_fuzzed, age, gender, seeking, relationship_intention, profile_completeness, updated_at`,
    [
      userId,
      merged.displayName,
      merged.bio,
      merged.city,
      merged.latitude,
      merged.longitude,
      merged.age,
      merged.gender,
      merged.seeking,
      merged.relationshipIntention,
      now,
    ],
  );

  const completeness = await computeProfileCompleteness(ctx, userId);
  await ctx.db.query('UPDATE profiles SET profile_completeness = $2 WHERE user_id = $1', [userId, completeness]);

  return mapProfile({ ...rows[0]!, profile_completeness: completeness });
}

// =====================================================================
// getPublicProfile
// =====================================================================

const EARTH_RADIUS_KM = 6371;
/** Round to the nearest 5km bucket — an "approximate distance", never exact (§7.1, §28.5). */
const DISTANCE_BUCKET_KM = 5;

function haversineKm(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const toRad = (deg: number) => (deg * Math.PI) / 180;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) ** 2 + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return EARTH_RADIUS_KM * c;
}

function approximateDistanceKm(
  a: { latitude: number | null; longitude: number | null },
  b: { latitude: number | null; longitude: number | null },
): number | null {
  if (a.latitude == null || a.longitude == null || b.latitude == null || b.longitude == null) return null;
  const exact = haversineKm(a.latitude, a.longitude, b.latitude, b.longitude);
  return Math.round(exact / DISTANCE_BUCKET_KM) * DISTANCE_BUCKET_KM;
}

/**
 * Fetch another user's profile as the caller would see it. Throws
 * `NotFoundError` if the target doesn't exist; throws `ForbiddenError` if
 * the caller has blocked or is blocked by the target (mirrors the
 * discovery visibility rule, spec §10.2 rule 9) — viewing a full profile
 * page should not be a backdoor around a block.
 *
 * Split into a thin wrapper (`getPublicProfile`, does the block check via
 * `discovery.service` — the sole cross-module call this file makes) and
 * `buildPublicProfileView` (everything else: lookups, distance bucketing,
 * tag visibility). The split is deliberate, not just style: it lets this
 * module's own tests exercise every bit of *this* file's logic against a
 * real DB without depending on `discovery.service` (owned by, and built in
 * parallel by, a different agent) being implemented yet.
 */
export async function getPublicProfile(ctx: Ctx, targetUserId: string): Promise<PublicProfileView> {
  const { userId: viewerId } = requireUserActor(ctx);

  if (targetUserId === viewerId) {
    // Viewing your own "public" profile is nonsensical for this endpoint;
    // route callers to getMyProfile instead.
    throw new ValidationError('Use getMyProfile to view your own profile.');
  }

  if (await discovery.isEitherBlocked(ctx, viewerId, targetUserId)) {
    throw new ForbiddenError('This profile is not available.');
  }

  return buildPublicProfileView(ctx, viewerId, targetUserId);
}

/** See `getPublicProfile`'s doc comment for why this is a separate export. Performs no block check of its own — callers other than `getPublicProfile` are responsible for that. */
export async function buildPublicProfileView(ctx: Ctx, viewerId: string, targetUserId: string): Promise<PublicProfileView> {
  const { rows: userRows } = await ctx.db.query<{ status: string; trust_level: TrustLevel }>(
    `SELECT status, trust_level FROM users WHERE id = $1`,
    [targetUserId],
  );
  const userRow = userRows[0];
  if (!userRow || userRow.status === 'deleted') {
    throw new NotFoundError('Profile not found.');
  }

  const targetProfile = await fetchProfileRow(ctx, targetUserId);
  if (!targetProfile) {
    throw new NotFoundError('Profile not found.');
  }
  const viewerProfile = await fetchProfileRow(ctx, viewerId);

  const { rows: photoRows } = await ctx.db.query<{ image_url: string }>(
    `SELECT image_url FROM user_photos WHERE user_id = $1 AND moderation_status = 'approved' ORDER BY is_primary DESC, position ASC`,
    [targetUserId],
  );

  const { rows: tagRows } = await ctx.db.query<{ name: string }>(
    `SELECT it.name AS name
     FROM user_tags ut
     JOIN interest_tags it ON it.id = ut.tag_id
     WHERE ut.user_id = $1
       AND (
         ut.visibility = 'public'
         OR (ut.visibility = 'private_reciprocal' AND EXISTS (
           SELECT 1 FROM user_tags viewer_ut WHERE viewer_ut.user_id = $2 AND viewer_ut.tag_id = ut.tag_id
         ))
       )
     ORDER BY it.name`,
    [targetUserId, viewerId],
  );

  return {
    userId: targetUserId,
    displayName: targetProfile.display_name,
    age: targetProfile.age,
    approximateDistanceKm: approximateDistanceKm(viewerProfile ?? { latitude: null, longitude: null }, targetProfile),
    bio: targetProfile.bio,
    photoUrls: photoRows.map((r) => r.image_url),
    trustLevel: userRow.trust_level,
    visibleInterestTagNames: tagRows.map((r) => r.name),
  };
}

// =====================================================================
// computeProfileCompleteness
// =====================================================================

/**
 * Pure-ish scoring of how complete a profile is (0-100), per §7.1/§9.4.
 * Exposed separately from `updateMyProfile` so `discovery.service.ts`'s
 * visibility rule ("profile is complete enough", §10.2 rule 3) and the
 * §25 nightly jobs can recompute without going through the update path.
 *
 * Deterministic weighted formula (documented here as the single source of
 * truth — no hidden magic elsewhere):
 *
 *   - display name set (non-empty)                          15
 *   - bio is at least 20 characters                          15
 *   - city set                                                10
 *   - core required fields present (age/gender/seeking/       10
 *     relationshipIntention — always true once a profile row
 *     exists, since those columns are NOT NULL; kept as an
 *     explicit weight for forward-compatibility if that ever
 *     changes to a staged/partial profile flow)
 *   - at least 1 approved photo (§10.2 rule 4 gate)            20
 *   - at least 3 approved photos (also unlocks §7.3 A/B test)  10
 *   - at least 5 answered compatibility questions              15
 *   - at least 1 visible interest tag                           5
 *                                                       total 100
 */
export async function computeProfileCompleteness(ctx: Ctx, userId: string): Promise<number> {
  const profile = await fetchProfileRow(ctx, userId);
  if (!profile) return 0;

  let score = 0;

  if (profile.display_name && profile.display_name.trim().length > 0) score += 15;
  if (profile.bio && profile.bio.trim().length >= 20) score += 15;
  if (profile.city && profile.city.trim().length > 0) score += 10;
  if (profile.age && profile.gender && profile.seeking && profile.relationship_intention) score += 10;

  const { rows: photoCountRows } = await ctx.db.query<{ count: string }>(
    `SELECT count(*)::text AS count FROM user_photos WHERE user_id = $1 AND moderation_status = 'approved'`,
    [userId],
  );
  const approvedPhotos = Number(photoCountRows[0]?.count ?? 0);
  if (approvedPhotos >= 1) score += 20;
  if (approvedPhotos >= 3) score += 10;

  const { rows: answerCountRows } = await ctx.db.query<{ count: string }>(
    `SELECT count(*)::text AS count FROM answers WHERE user_id = $1`,
    [userId],
  );
  if (Number(answerCountRows[0]?.count ?? 0) >= 5) score += 15;

  const { rows: tagCountRows } = await ctx.db.query<{ count: string }>(
    `SELECT count(*)::text AS count FROM user_tags WHERE user_id = $1`,
    [userId],
  );
  if (Number(tagCountRows[0]?.count ?? 0) >= 1) score += 5;

  return Math.min(100, Math.max(0, score));
}

// =====================================================================
// Account deletion + data export (§29) — additions beyond the frozen list.
// =====================================================================

/**
 * §29 account deletion: removes the profile from discovery (status flips
 * to 'deleted', which every visibility check in this codebase gates on),
 * blocks new messages (same status flip — `message.service`/
 * `conversation.service` are expected to check `users.status`, flagged in
 * the build report), retains financial rows (this function never touches
 * `payment_holds`/`payment_ledger` — not this module's tables, and nothing
 * here deletes them), and anonymizes the analytics surface this module
 * owns (profile display fields wiped, photos removed so no image survives
 * in discovery caches).
 */
export async function deleteMyAccount(ctx: Ctx): Promise<void> {
  const { userId } = requireUserActor(ctx);
  const now = ctx.clock.now();

  await ctx.db.query(`UPDATE users SET status = 'deleted', last_active_at = $2 WHERE id = $1`, [userId, now]);

  await ctx.db.query(
    `UPDATE profiles SET display_name = 'Deleted user', bio = '', city = NULL, latitude = NULL, longitude = NULL, updated_at = $2 WHERE user_id = $1`,
    [userId, now],
  );

  await ctx.db.query(`DELETE FROM user_photos WHERE user_id = $1`, [userId]);

  // Kill every active session so a deleted account can't keep making
  // authenticated calls with a still-valid access/refresh token.
  await ctx.db.query(`UPDATE refresh_sessions SET revoked_at = $2 WHERE user_id = $1 AND revoked_at IS NULL`, [
    userId,
    now,
  ]);
}

/** §29 data export: everything this module's tables (users/profiles/photos/photo experiment stats) hold about the caller, excluding the password hash. */
export async function exportMyData(ctx: Ctx): Promise<Record<string, unknown>> {
  const { userId } = requireUserActor(ctx);

  const { rows: userRows } = await ctx.db.query(
    `SELECT id, email, birthdate::text, status, trust_score, trust_level, email_verified_at, created_at, last_active_at
     FROM users WHERE id = $1`,
    [userId],
  );
  const profile = await fetchProfileRow(ctx, userId);
  const { rows: photos } = await ctx.db.query(
    `SELECT id, image_url, position, is_primary, moderation_status, created_at FROM user_photos WHERE user_id = $1 ORDER BY position`,
    [userId],
  );
  const { rows: photoStats } = await ctx.db.query(
    `SELECT photo_id, impressions, interests_sent, interests_accepted FROM photo_experiments WHERE user_id = $1`,
    [userId],
  );

  return {
    account: userRows[0] ?? null,
    profile: profile ? mapProfile(profile) : null,
    photos,
    photoExperimentStats: photoStats,
  };
}
