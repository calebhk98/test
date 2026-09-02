/**
 * Weight formatting: canonical storage is grams (`weightG`), matching
 * the backend's integer-gram discipline; imperial display is whole
 * pounds.
 */
import type { UnitPreference } from '../api/types';

const G_PER_LB = 453.59237;

export function formatWeight(g: number | null, pref: UnitPreference): string | null {
  if (g === null) return null;
  if (pref === 'imperial') {
    return `${Math.round(g / G_PER_LB)} lb`;
  }
  return `${(g / 1000).toFixed(1)} kg`;
}
