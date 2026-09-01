/**
 * src/domain/units/distance.ts, distance measure.
 *
 * CANONICAL STORAGE UNIT: kilometres. Chosen (over metres) because every
 * existing distance surface in this codebase already speaks kilometres,
 * the `distance_km` hard-filter key (`filter.service.ts`), `haversineKm`
 * (`filter.service.ts` and, separately, `profile.service.ts`'s own copy
 * used for `approximateDistanceKm`), and `DiscoveryCandidate.
 * approximateDistanceKm` (`domain/types.ts`, not owned by this module),
 * all already use km. Introducing metres as "the" canonical unit here
 * would just move the swap-risk to a km<->m boundary instead of removing
 * it. `Kilometres` is the branded type that makes that existing
 * convention structurally explicit instead of implicit-by-naming-only.
 *
 * Distance is NEVER stored on a row as a value in this codebase, it is
 * always recomputed from two lat/long pairs at read time, so there is no
 * "stored measure" integer-discipline concern here the way there is for
 * height/weight; `Kilometres` stays a float, matching `haversineKm`'s
 * existing return type exactly (no behavior change to that function).
 */
import { brand, type Brand } from './brand.js';
import type { UnitPreference } from './preference.js';

export type Kilometres = Brand<number, 'Kilometres'>;
export type Miles = Brand<number, 'Miles'>;

const KM_PER_MILE = 1.609344; // exact, internationally defined

function assertFiniteNonNegative(value: number, label: string): void {
  if (!Number.isFinite(value) || value < 0) {
    throw new RangeError(`${label} must be a non-negative finite number, got ${value}`);
  }
}

/** The only way to mint a `Kilometres` value from a raw number. */
export function kilometres(value: number): Kilometres {
  assertFiniteNonNegative(value, 'Kilometres');
  return brand(value);
}

/** The only way to mint a `Miles` value from a raw number. */
export function miles(value: number): Miles {
  assertFiniteNonNegative(value, 'Miles');
  return brand(value);
}

/** Exact (unrounded) conversion, used internally and by round-trip tests; callers that want a display string should use `formatDistance` instead. */
export function kilometresToMiles(km: Kilometres): Miles {
  return miles(km / KM_PER_MILE);
}

/** Exact (unrounded) conversion, see `kilometresToMiles`. */
export function milesToKilometres(mi: Miles): Kilometres {
  return kilometres(mi * KM_PER_MILE);
}

export interface DisplayDistance {
  value: number; // rounded to a whole unit
  unit: 'km' | 'mi';
}

/**
 * Rounds a canonical distance to a whole display unit, per the caller's
 * preference. Whole-unit rounding matches the precision every existing
 * distance surface in this codebase already uses (`profile.service.ts`'s
 * 5km bucket, `discovery.service.ts`'s 1km rounding), sub-unit precision
 * on a distance to another user was never meaningful here, and the
 * §7.1/§28.5 "approximate distance only" requirement gives no reason to
 * add any back.
 */
export function toDisplayDistance(km: Kilometres, pref: UnitPreference): DisplayDistance {
  if (pref === 'imperial') {
    return { value: Math.round(kilometresToMiles(km)), unit: 'mi' };
  }
  return { value: Math.round(km), unit: 'km' };
}

/**
 * The seam function `discovery.service.ts` (owned by another agent) is
 * meant to call to render a card's distance, see this build's report for
 * the exact call shape. Returns `null` (never a string) when `km` is
 * `null`, so a caller can pass a nullable distance straight through.
 */
export function formatDistance(km: Kilometres | null, pref: UnitPreference): string | null {
  if (km === null) return null;
  const { value, unit } = toDisplayDistance(km, pref);
  if (value === 0 && km > 0) return `<1 ${unit}`;
  return `${value} ${unit}`;
}

// =========================================================================
// SAF-2 FIX, the one approximate-distance function every display surface
// must call.
//
// Before this fix, `discovery.service.ts#toApproximateDistanceKm` rounded
// to the nearest 1km and `profile.service.ts#approximateDistanceKm`
// independently bucketed to the nearest 5km, two different, unjittered
// functions computing "the same" concept. That combination (fine
// precision, no jitter, no query-rate limit) is the exact precondition
// that has repeatedly let researchers trilaterate real dating-app users:
// create a handful of accounts at known coordinates, record the reported
// distance from each, solve the intersecting circles for the target's
// real position.
//
// THE FIX has two independent parts, both required:
//
//   1. ONE COARSE BUCKET (`DEFAULT_DISTANCE_BUCKET_KM`, config-overridable
//      by the caller via `bucketKm`/`precisionFloorKm`, see
//      profile.service.ts's `distancePrecisionFloorKm`). Wider than either
//      of the two functions this replaces: a 1km (or even 5km) grid is
//      still fine enough for classic trilateration once you have three or
//      more vantage points; single-digit-km buckets remain useful for "is
//      this person nearby" without being useful for "where exactly do
//      they live".
//
//   2. A STABLE PER-VIEWER-PAIR OFFSET (`stablePairOffsetSteps`). Plain
//      bucketing alone is still exploitable by an attacker who controls
//      MULTIPLE viewer accounts at known coordinates (the textbook
//      pattern: 3+ fake accounts, each records the bucketed distance,
//      solve for the intersection), the bucketed number is a direct,
//      predictable function of true distance, so combining several
//      accounts' readings still converges on the target's real location
//      as the bucket narrows toward zero and/or vantage points multiply.
//      Adding a deterministic pseudorandom offset, seeded from the
//      (viewerId, targetId) PAIR only, never from either party's actual
//      coordinates, decorrelates what different viewer accounts see for
//      the same target: attacker account A's reading is displaced from
//      the truth by a fixed but unrelated amount to attacker account B's,
//      so their circles no longer intersect where the target actually is.
//      Critically, this offset does NOT depend on position, so it never
//      moves smoothly as either party moves nearby, it only ever jumps
//      when the underlying bucket itself changes, exactly like plain
//      bucketing, so it never betrays fine-grained movement either.
//
//      This does not (and cannot, from a distance-only signal) defeat a
//      SINGLE account teleporting itself to many exact known coordinates
//      and sampling the same target repeatedly, see
//      `tests/unit/distancePrivacy.test.ts` for why the bucket width
//      alone already caps that attack's useful precision to
//      +/-`bucketKm`-ish, which is the documented, accepted residual (an
//      "approximate distance" feature can never be fully immune to a
//      single-vantage adversary with an otherwise-exact oracle; widening
//      the bucket is the only lever, and this module makes it one lever,
//      applied consistently, everywhere, instead of two inconsistent
//      ones).
//
//   Per-user precision floor: a profile MAY set its own
//   `distancePrecisionFloorKm` (see `profile.service.ts`), passed in here
//   as `bucketKm` by the caller, for anyone who wants an even coarser
//   number shown to others than the platform default.
// =========================================================================

const EARTH_RADIUS_KM = 6371;

/** Default coarse bucket width, km, deliberately wider than either of the two functions this replaces (1km / 5km). See module doc above. */
export const DEFAULT_DISTANCE_BUCKET_KM = 8;

/** How many extra bucket-widths the per-pair offset may shift the displayed number, each direction (so the offset is bounded, the number shown is always "in the right neighborhood", never wildly wrong; see module doc). */
const JITTER_BUCKET_SPAN = 2;

/** Plain, exact great-circle distance, internal only. Never exported: every external caller wants `approximateDistanceBetween`, never a raw exact figure, per §7.1/§28.5 "exact location/distance MUST NOT be shown". (`filter.service.ts` keeps its own copy for hard-filter *enforcement*, e.g. "must be within 50km", a materially different concern, exact-distance comparison never displayed to a user, and out of this module's file-ownership boundary; this is not the duplication SAF-2 is about.) */
function haversineKmExact(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const toRad = (deg: number) => (deg * Math.PI) / 180;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a = Math.sin(dLat / 2) ** 2 + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return EARTH_RADIUS_KM * c;
}

/**
 * Deterministic, roughly-uniform 32-bit hash of the ordered (viewerId,
 * targetId) pair. Not a cryptographic commitment and doesn't need to be
 * one, its only job is "stable across calls, and two different pairs
 * don't obviously collide" (an FNV-1a variant comfortably clears that
 * bar). Deliberately ORDER-SENSITIVE (viewer, target) rather than sorted:
 * what viewer A sees for target B need not match what B would see for A
 * (they may not even both have locations set), and there is no
 * requirement anywhere in the spec that the figure be symmetric.
 */
function stablePairSeed(viewerId: string, targetId: string): number {
  const s = `${viewerId} ${targetId}`;
  let h = 0x811c9dc5;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return h >>> 0;
}

/** Maps the pair seed onto a small signed integer in [-JITTER_BUCKET_SPAN, +JITTER_BUCKET_SPAN], used as a whole-number multiple of `bucketKm`. */
function stablePairOffsetSteps(viewerId: string, targetId: string): number {
  const span = 2 * JITTER_BUCKET_SPAN + 1;
  return (stablePairSeed(viewerId, targetId) % span) - JITTER_BUCKET_SPAN;
}

export interface DistanceParty {
  /** Stable identity used only to seed the per-pair offset, never interpreted as a location. */
  id: string;
  latitude: number | null;
  longitude: number | null;
}

export interface ApproximateDistanceOptions {
  /** Coarse bucket width, km. Defaults to `DEFAULT_DISTANCE_BUCKET_KM`. Callers pass `Math.max(default, target's own precisionFloorKm)` when the target has opted into a coarser floor (see `profile.service.ts`). */
  bucketKm?: number;
}

/**
 * THE approximate-distance function, see module doc above. Every surface
 * that shows one user their distance to another (discovery grid, profile
 * page, and any future one) MUST call this and MUST NOT compute or round
 * a distance any other way. Returns `null` when either party's
 * coordinates are unset, a caller with no location on file gets no
 * distance figure, not a stale/zero one.
 */
export function approximateDistanceBetween(
  viewer: DistanceParty,
  target: DistanceParty,
  options: ApproximateDistanceOptions = {},
): number | null {
  if (viewer.latitude == null || viewer.longitude == null || target.latitude == null || target.longitude == null) {
    return null;
  }
  const bucketKm = Math.max(1, options.bucketKm ?? DEFAULT_DISTANCE_BUCKET_KM);

  const exactKm = haversineKmExact(viewer.latitude, viewer.longitude, target.latitude, target.longitude);
  const bucketed = Math.round(exactKm / bucketKm) * bucketKm;

  const offsetSteps = stablePairOffsetSteps(viewer.id, target.id);
  const jittered = bucketed + offsetSteps * bucketKm;

  return Math.max(0, jittered);
}

// Exported for `tests/unit/distancePrivacy.test.ts` and
// `tests/unit/units.test.ts` only, not part of the public "call this to
// show a distance" surface (`approximateDistanceBetween` is), but the
// offset mechanism's own determinism/boundedness properties need direct
// coverage independent of any particular bucket width.
export const __internal = { stablePairSeed, stablePairOffsetSteps, haversineKmExact, JITTER_BUCKET_SPAN };
