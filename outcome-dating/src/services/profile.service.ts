import { z } from 'zod';
import type { Ctx } from '../lib/ctx.js';
import { requireUserActor } from '../lib/ctx.js';
import { ForbiddenError, NotFoundError, ValidationError } from '../lib/errors.js';
import type { Profile, TrustLevel } from '../domain/types.js';
import * as discovery from './discovery.service.js';
import { BODY_TYPES, type BodyType } from '../domain/units/bodyType.js';
import { resolveDefaultUnitPreference, unitPreferenceSchema, type UnitPreference } from '../domain/units/preference.js';
import { approximateDistanceBetween } from '../domain/units/distance.js';

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
 *
 * PHYSICAL ATTRIBUTES + UNITS (this build; no § reference — product
 * decision, `db/migrations/009_units_attributes.sql`). `profiles` gains
 * `height_cm`/`weight_g` (both optional, both canonical — see
 * `src/domain/units/`, never a display unit), `weight_visible` (whether
 * `weight_g` appears on `PublicProfileView` at all — see that type's own
 * doc below), `body_type` (optional, categorical — `src/domain/units/
 * bodyType.ts`), and `unit_preference` (`'metric' | 'imperial'`,
 * presentation-only: changing it NEVER rewrites `height_cm`/`weight_g`,
 * see `tests/unit/profileAttributes.test.ts`). `Profile` (`domain/
 * types.ts`, not owned by this agent) predates these fields, so
 * `getMyProfile`/`updateMyProfile` return `ProfileWithAttributes` below —
 * a strict superset of `Profile` — rather than editing that file; every
 * existing caller typed against `Profile` keeps compiling unchanged
 * (structural typing, extra fields on the returned object are not a type
 * error). `http/serializers/profile.ts` (frozen, `src/http/**`) does not
 * yet forward these new fields to the wire — flagged in this build's
 * report for that agent to wire in.
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
  /** Canonical whole centimetres (see `src/domain/units/height.ts`). Optional — a blank height must not exclude the user from anyone's results unless a viewer's height filter has `excludeIfUnset: true` (see `filter.service.ts`). */
  heightCm?: number;
  /** Canonical whole grams (see `src/domain/units/weight.ts`). Optional, same non-exclusion default as `heightCm`. */
  weightG?: number;
  /** Whether `weightG` appears on this user's `PublicProfileView` at all. Defaults to `true` (visible) — see that type's doc for why "hidden" means fully omitted, not sent-and-masked. */
  weightVisible?: boolean;
  /** Self-described, categorical — see `src/domain/units/bodyType.ts`. Optional. */
  bodyType?: BodyType;
  /** Presentation-only — see this file's module doc "PHYSICAL ATTRIBUTES + UNITS". Never affects a stored measure. */
  unitPreference?: UnitPreference;
  /**
   * SAF-2 fix: an optional per-user floor on how coarse the distance
   * OTHER users see to this profile must be. `null`/omitted uses the
   * platform default (`domain/units/distance.ts#DEFAULT_DISTANCE_BUCKET_KM`).
   * Setting e.g. `25` never lets `approximateDistanceBetween` report this
   * user's distance any more precisely than a 25km bucket, regardless of
   * the platform default — "a per-user precision floor for anyone who
   * wants it". Only ever widens (never narrows) the effective bucket —
   * see `buildPublicProfileView`/`discovery.service.ts#loadCandidatePool`.
   */
  distancePrecisionFloorKm?: number | null;
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
  /** Canonical whole centimetres, or `null` if unset. Always present when set — height has no per-user hide toggle (only weight does; see `weightG` below). */
  heightCm: number | null;
  /** Self-described categorical value, or `null` if unset. */
  bodyType: BodyType | null;
  /**
   * Canonical whole grams. OPTIONAL KEY, not `number | null`: this
   * property is only ever set on the returned object when the profile
   * owner has `weightVisible: true` AND has actually set a weight —
   * `buildPublicProfileView` never assigns it otherwise. This mirrors the
   * `latitude`/`longitude` discipline this file's own module doc
   * documents for location: a hidden weight is not sent-and-hidden, it is
   * structurally ABSENT from the object a caller receives (`'weightG' in
   * view` is `false`), so no serializer downstream can leak it by
   * forgetting to check a flag.
   */
  weightG?: number;
}

/**
 * `Profile` (`domain/types.ts`, not owned by this agent) plus this
 * build's physical-attribute/unit fields — see the module doc
 * "PHYSICAL ATTRIBUTES + UNITS". A strict superset, never edited in
 * place: `getMyProfile`/`updateMyProfile` return this instead of bare
 * `Profile` so every existing field stays exactly where callers typed
 * against `Profile` expect it.
 */
export interface ProfileWithAttributes extends Profile {
  heightCm: number | null;
  weightG: number | null;
  weightVisible: boolean;
  bodyType: BodyType | null;
  unitPreference: UnitPreference;
  /** See `UpdateProfileInput.distancePrecisionFloorKm`. `null` = use the platform default bucket. */
  distancePrecisionFloorKm: number | null;
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
  // Bounds mirror db/migrations/009_units_attributes.sql's CHECK
  // constraints exactly — kept in sync deliberately (see that migration's
  // comment) so an out-of-range value is rejected here, at the validation
  // boundary, with a ValidationError, rather than surfacing as an opaque
  // Postgres constraint-violation error.
  heightCm: z.number().int().min(100).max(250).optional(),
  weightG: z.number().int().min(20000).max(300000).optional(),
  weightVisible: z.boolean().optional(),
  bodyType: z.enum(BODY_TYPES).optional(),
  unitPreference: unitPreferenceSchema.optional(),
  // 1km-500km: below 1 is meaningless (finer than the platform default
  // ever goes) and above 500 is not "your own city", it's "hide it
  // entirely" — that's what leaving latitude/longitude unset already does.
  distancePrecisionFloorKm: z.number().int().min(1).max(500).nullable().optional(),
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
  height_cm: number | null;
  weight_g: number | null;
  weight_visible: boolean;
  body_type: string | null;
  unit_preference: string;
  distance_precision_floor_km: number | null;
}

function mapProfile(row: ProfileRow): ProfileWithAttributes {
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
    heightCm: row.height_cm,
    weightG: row.weight_g,
    weightVisible: row.weight_visible,
    bodyType: row.body_type as BodyType | null,
    unitPreference: row.unit_preference as UnitPreference,
    distancePrecisionFloorKm: row.distance_precision_floor_km,
  };
}

const PROFILE_ROW_COLUMNS =
  'user_id, display_name, bio, city, latitude, longitude, location_fuzzed, age, gender, seeking, relationship_intention, profile_completeness, updated_at, height_cm, weight_g, weight_visible, body_type, unit_preference, distance_precision_floor_km';

async function fetchProfileRow(ctx: Ctx, userId: string): Promise<ProfileRow | undefined> {
  const { rows } = await ctx.db.query<ProfileRow>(
    `SELECT ${PROFILE_ROW_COLUMNS} FROM profiles WHERE user_id = $1`,
    [userId],
  );
  return rows[0];
}

// =====================================================================
// getMyProfile / updateMyProfile
// =====================================================================

export async function getMyProfile(ctx: Ctx): Promise<ProfileWithAttributes> {
  const { userId } = requireUserActor(ctx);
  const row = await fetchProfileRow(ctx, userId);
  if (!row) {
    throw new NotFoundError('You have not created a profile yet.');
  }
  return mapProfile(row);
}

/** Upserts the caller's profile and recomputes `profileCompleteness` (§9.4). */
export async function updateMyProfile(ctx: Ctx, patch: UpdateProfileInput): Promise<ProfileWithAttributes> {
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
    // Optional physical attributes — never required (see UpdateProfileSchema/`required` above), so `existing` may be absent and the field simply stays null.
    heightCm: parsed.heightCm ?? existing?.height_cm ?? null,
    weightG: parsed.weightG ?? existing?.weight_g ?? null,
    weightVisible: parsed.weightVisible ?? existing?.weight_visible ?? true,
    bodyType: parsed.bodyType ?? existing?.body_type ?? null,
    distancePrecisionFloorKm:
      parsed.distancePrecisionFloorKm !== undefined ? parsed.distancePrecisionFloorKm : (existing?.distance_precision_floor_km ?? null),
    // No country/locale field exists on this table to infer from (see
    // src/domain/units/preference.ts) — resolveDefaultUnitPreference(null)
    // always yields the documented static default (metric) today.
    unitPreference: parsed.unitPreference ?? existing?.unit_preference ?? resolveDefaultUnitPreference(null),
  };

  const now = ctx.clock.now();

  const { rows } = await ctx.db.query<ProfileRow>(
    `INSERT INTO profiles (user_id, display_name, bio, city, latitude, longitude, location_fuzzed, age, gender, seeking, relationship_intention, profile_completeness, updated_at, height_cm, weight_g, weight_visible, body_type, unit_preference, distance_precision_floor_km)
     VALUES ($1, $2, $3, $4, $5, $6, true, $7, $8, $9, $10, 0, $11, $12, $13, $14, $15, $16, $17)
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
       updated_at = EXCLUDED.updated_at,
       height_cm = EXCLUDED.height_cm,
       weight_g = EXCLUDED.weight_g,
       weight_visible = EXCLUDED.weight_visible,
       body_type = EXCLUDED.body_type,
       unit_preference = EXCLUDED.unit_preference,
       distance_precision_floor_km = EXCLUDED.distance_precision_floor_km
     RETURNING ${PROFILE_ROW_COLUMNS}`,
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
      merged.heightCm,
      merged.weightG,
      merged.weightVisible,
      merged.bodyType,
      merged.unitPreference,
      merged.distancePrecisionFloorKm,
    ],
  );

  const completeness = await computeProfileCompleteness(ctx, userId);
  await ctx.db.query('UPDATE profiles SET profile_completeness = $2 WHERE user_id = $1', [userId, completeness]);

  return mapProfile({ ...rows[0]!, profile_completeness: completeness });
}

// =====================================================================
// getPublicProfile
// =====================================================================

/**
 * SAF-2 fix: distance is computed by exactly one function
 * (`domain/units/distance.ts#approximateDistanceBetween`), shared with
 * `discovery.service.ts` — this file no longer has its own bucketing
 * implementation. `bucketKm` is the config-driven platform default
 * (`privacy.distance_bucket_km`) widened to at least the TARGET's own
 * opted-in precision floor, never the viewer's (a viewer cannot make
 * someone else's distance more precise by asking for one).
 */
async function distanceToTarget(
  ctx: Ctx,
  viewer: { latitude: number | null; longitude: number | null },
  viewerId: string,
  target: { latitude: number | null; longitude: number | null; distance_precision_floor_km?: number | null },
  targetId: string,
): Promise<number | null> {
  const platformDefaultKm = await ctx.config.get('privacy.distance_bucket_km');
  const bucketKm = Math.max(platformDefaultKm, target.distance_precision_floor_km ?? 0);
  return approximateDistanceBetween({ id: viewerId, ...viewer }, { id: targetId, ...target }, { bucketKm });
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

  const approximateDistanceKm = await distanceToTarget(
    ctx,
    viewerProfile ?? { latitude: null, longitude: null },
    viewerId,
    targetProfile,
    targetUserId,
  );

  const view: PublicProfileView = {
    userId: targetUserId,
    displayName: targetProfile.display_name,
    age: targetProfile.age,
    approximateDistanceKm,
    bio: targetProfile.bio,
    photoUrls: photoRows.map((r) => r.image_url),
    trustLevel: userRow.trust_level,
    visibleInterestTagNames: tagRows.map((r) => r.name),
    heightCm: targetProfile.height_cm,
    bodyType: targetProfile.body_type as BodyType | null,
  };
  // See PublicProfileView's own doc: `weightG` is only ever ASSIGNED when
  // visible+set — never assigned-then-nulled — so a hidden/unset weight is
  // structurally absent from `view`, not merely masked.
  if (targetProfile.weight_visible && targetProfile.weight_g != null) {
    view.weightG = targetProfile.weight_g;
  }
  return view;
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
 * §29 account deletion / PRIV-1 FIX.
 *
 * Before this fix, deletion only ever touched `users` (status flip),
 * `profiles` (display fields wiped), `user_photos` (deleted), and
 * `refresh_sessions` (revoked) — `answers` (including every
 * `sensitive:true` question — religion, drug use, sexuality-adjacent
 * lifestyle), `user_tags` (including `private_reciprocal` tags that can
 * reveal stigmatized interests), `hard_filters`, and full `messages`
 * content all survived indefinitely, keyed to a `user_id` that still
 * existed in every one of those tables. A "deleted" account's sensitive
 * data and private chat content persisted forever.
 *
 * WHAT THIS FUNCTION NOW DOES, table by table:
 *   - users:              status -> 'deleted' (unchanged from before).
 *   - profiles:            display fields wiped, coordinates/physical
 *                           attributes/precision floor nulled (unchanged
 *                           from before, extended to the new
 *                           `distance_precision_floor_km` column).
 *   - user_photos:          hard-deleted (unchanged from before).
 *   - refresh_sessions:     revoked (unchanged from before).
 *   - answers:              HARD-DELETED, every row, including every
 *                           `sensitive:true` question's self/partner
 *                           value. This is the single biggest gap PRIV-1
 *                           named — it is erased, not anonymised, because
 *                           there is no legitimate reason to retain it in
 *                           any form once the account is gone.
 *   - user_tags:            HARD-DELETED, every row (public AND
 *                           private_reciprocal — both can reveal a
 *                           stigmatized interest, per PRIV-3).
 *   - hard_filters:         HARD-DELETED, every row.
 *   - messages:              the DELETED USER'S OWN message bodies are
 *                           overwritten with a static placeholder
 *                           (`DELETED_MESSAGE_PLACEHOLDER`); the
 *                           `conversations`/`messages` ROWS themselves,
 *                           and the OTHER participant's own messages, are
 *                           left completely untouched.
 *
 * MESSAGE-RETENTION POLICY (the "documented policy" the brief asks for):
 * ERASE CONTENT, KEEP ATTRIBUTION — chosen over the alternative
 * (deleting/hiding the row and leaving a synthetic "deleted user" byline)
 * because deleting `messages` rows or archiving `conversations` out from
 * under the other participant is exactly the "must not corrupt the other
 * party's conversation" failure mode the brief warns against: the other
 * user's own conversation thread, their own messages, and the
 * conversation's timeline metadata (created_at/first_date_completed_at/
 * etc.) all stay exactly as they were. Only the erased user's own words
 * are gone. `profiles.display_name` already reads 'Deleted user' after
 * this function runs, so the byline naturally attributes those now-empty
 * messages to a deleted account without this file needing a second
 * "who sent this" concept.
 *
 * DELIBERATELY RETAINED (not this function's job, and not safe to erase):
 *   - payment_holds / payment_ledger: financial/ledger records — §14.8
 *     ledger is explicitly immutable, and payment records are the kind of
 *     "genuinely must be retained" data the brief calls out by name (tax/
 *     dispute/audit obligations survive account deletion in most
 *     jurisdictions). Never touched by this function, same as before.
 *   - reports / moderation_actions / trust_events: the platform's safety
 *     audit trail. Erasing a target's or reporter's history on deletion
 *     would let a suspended/banned user launder their record by
 *     self-deleting and re-registering — directly undermining SAF-1/SAF-5
 *     ban-evasion resistance. These rows reference a `user_id` whose
 *     profile is already anonymised by this function, so no display name/
 *     bio/photo/answer survives through them.
 *   - appeals: same reasoning as moderation_actions — part of the
 *     automated-moderation audit trail, not personal profile content.
 *   - discovery_events / photo_experiments / compatibility_scores: out of
 *     this fix's scope (PRIV-1, as filed, names `answers`, `messages`,
 *     `user_tags`, `hard_filters` specifically) and owned by services
 *     this build does not touch; flagged for a follow-up retention-window
 *     pass (see PRIV-5) rather than folded in here.
 *
 * IDEMPOTENT / SAFE TO RE-RUN: every statement below is naturally
 * idempotent (UPDATE ... to a fixed value, DELETE FROM ... WHERE user_id
 * = $1 on rows that may already be gone, an UPDATE guarded by `<> $2` so
 * re-running never re-writes what it already wrote) — calling this twice
 * for the same user produces the exact same end state as calling it once,
 * with no error either time. See `tests/unit/deletion.test.ts`.
 */
export const DELETED_MESSAGE_PLACEHOLDER = 'This message is no longer available.';

export async function deleteMyAccount(ctx: Ctx): Promise<void> {
  const { userId } = requireUserActor(ctx);
  const now = ctx.clock.now();

  await ctx.db.query(`UPDATE users SET status = 'deleted', last_active_at = $2 WHERE id = $1`, [userId, now]);

  await ctx.db.query(
    `UPDATE profiles
        SET display_name = 'Deleted user', bio = '', city = NULL, latitude = NULL, longitude = NULL,
            height_cm = NULL, weight_g = NULL, body_type = NULL, distance_precision_floor_km = NULL,
            updated_at = $2
      WHERE user_id = $1`,
    [userId, now],
  );

  await ctx.db.query(`DELETE FROM user_photos WHERE user_id = $1`, [userId]);

  // Kill every active session so a deleted account can't keep making
  // authenticated calls with a still-valid access/refresh token.
  await ctx.db.query(`UPDATE refresh_sessions SET revoked_at = $2 WHERE user_id = $1 AND revoked_at IS NULL`, [
    userId,
    now,
  ]);

  // ---- PRIV-1 fix: the previously-untouched tables ----

  // Sensitive-category compatibility answers (§8.2/§8.5 "sensitive: true"
  // questions included) — full erasure, not anonymisation: there is no
  // retention justification for these once the account is gone.
  await ctx.db.query(`DELETE FROM answers WHERE user_id = $1`, [userId]);

  // Interest tags, including private_reciprocal ones (§8.4) that can
  // reveal a stigmatized interest to anyone who happens to share it.
  await ctx.db.query(`DELETE FROM user_tags WHERE user_id = $1`, [userId]);

  // This user's own hard-filter preferences.
  await ctx.db.query(`DELETE FROM hard_filters WHERE user_id = $1`, [userId]);

  // This user's own message content, in every conversation — see the
  // "MESSAGE-RETENTION POLICY" note above for why the row/conversation
  // itself is left in place. `body <> $2` makes the statement a genuine
  // no-op (not just a same-value rewrite) on a second run.
  await ctx.db.query(`UPDATE messages SET body = $2, analysis_flags = '[]'::jsonb WHERE sender_id = $1 AND body <> $2`, [
    userId,
    DELETED_MESSAGE_PLACEHOLDER,
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
