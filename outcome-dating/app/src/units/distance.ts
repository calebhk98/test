/**
 * Distance formatting. The server already returns a fuzzed, bucketed
 * `approximateDistanceKm` (see the backend's domain/units/distance.ts);
 * this module's only job is the km <-> mi presentation step, driven by
 * the user's stored `unitPreference`. Every screen that shows a
 * distance MUST go through `formatDistance`, never divide or round a
 * kilometre number inline, that's the "unit mixing is a compile error"
 * discipline the backend enforces with branded types; on the client we
 * enforce it by convention, one function, one call site pattern.
 */
import type { UnitPreference } from '../api/types';

const KM_PER_MILE = 1.609344;

export function kilometresToMiles(km: number): number {
  return km / KM_PER_MILE;
}

/**
 * Rounds to a whole display unit and returns a ready-to-render string,
 * or `null` when there is no distance to show (no location on file for
 * one side), which a screen should render as "distance unknown", never
 * as 0 or a blank space.
 */
export function formatDistance(km: number | null, pref: UnitPreference): string | null {
  if (km === null) return null;
  if (pref === 'imperial') {
    const mi = Math.round(kilometresToMiles(km));
    if (mi === 0 && km > 0) return '<1 mi';
    return `${mi} mi`;
  }
  const rounded = Math.round(km);
  if (rounded === 0 && km > 0) return '<1 km';
  return `${rounded} km`;
}
