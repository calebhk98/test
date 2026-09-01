/**
 * src/domain/units/distance.ts — distance measure.
 *
 * CANONICAL STORAGE UNIT: kilometres. Chosen (over metres) because every
 * existing distance surface in this codebase already speaks kilometres —
 * the `distance_km` hard-filter key (`filter.service.ts`), `haversineKm`
 * (`filter.service.ts` and, separately, `profile.service.ts`'s own copy
 * used for `approximateDistanceKm`), and `DiscoveryCandidate.
 * approximateDistanceKm` (`domain/types.ts`, not owned by this module) —
 * all already use km. Introducing metres as "the" canonical unit here
 * would just move the swap-risk to a km<->m boundary instead of removing
 * it. `Kilometres` is the branded type that makes that existing
 * convention structurally explicit instead of implicit-by-naming-only.
 *
 * Distance is NEVER stored on a row as a value in this codebase — it is
 * always recomputed from two lat/long pairs at read time — so there is no
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

/** Exact (unrounded) conversion — used internally and by round-trip tests; callers that want a display string should use `formatDistance` instead. */
export function kilometresToMiles(km: Kilometres): Miles {
  return miles(km / KM_PER_MILE);
}

/** Exact (unrounded) conversion — see `kilometresToMiles`. */
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
 * 5km bucket, `discovery.service.ts`'s 1km rounding) — sub-unit precision
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
 * meant to call to render a card's distance — see this build's report for
 * the exact call shape. Returns `null` (never a string) when `km` is
 * `null`, so a caller can pass a nullable distance straight through.
 */
export function formatDistance(km: Kilometres | null, pref: UnitPreference): string | null {
  if (km === null) return null;
  const { value, unit } = toDisplayDistance(km, pref);
  if (value === 0 && km > 0) return `<1 ${unit}`;
  return `${value} ${unit}`;
}
