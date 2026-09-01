/**
 * src/domain/units/weight.ts, weight measure.
 *
 * CANONICAL STORAGE UNIT: whole grams (integer). Same integer-discipline
 * reasoning as `height.ts`: weight is a STORED, filterable profile field,
 * so its canonical form must never be a float a `gte`/`lte` comparison
 * could see drift in across reads. Grams (not kilograms) is the canonical
 * unit specifically so the stored column stays an integer without losing
 * precision, `70.5kg` stored as kilograms would need a float or a fixed
 * decimal column; stored as `70500` grams it is an ordinary `integer`.
 */
import { brand, type Brand } from './brand.js';
import type { UnitPreference } from './preference.js';

export type Grams = Brand<number, 'Grams'>;
export type Pounds = Brand<number, 'Pounds'>;

const GRAMS_PER_POUND = 453.59237; // exact, internationally defined

/** The only way to mint a `Grams` value from a raw number. Throws on a non-integer or negative input, see the file doc for why weight is integer-only. */
export function grams(value: number): Grams {
  if (!Number.isInteger(value) || value < 0) {
    throw new RangeError(`Grams must be a non-negative integer, got ${value}`);
  }
  return brand(value);
}

/** The only way to mint a `Pounds` value from a raw number. Pounds is a DISPLAY unit only (never stored), so unlike `grams()` it is not integer-constrained. */
export function pounds(value: number): Pounds {
  if (!Number.isFinite(value) || value < 0) {
    throw new RangeError(`Pounds must be a non-negative finite number, got ${value}`);
  }
  return brand(value);
}

/** Exact (unrounded) conversion, used internally and by round-trip tests; callers that want a display string should use `formatWeight` instead. */
export function gramsToPounds(g: Grams): Pounds {
  return pounds(g / GRAMS_PER_POUND);
}

/** Inverse of `gramsToPounds`, rounded back to a whole gram (integer discipline, see file doc). */
export function poundsToGrams(lb: Pounds): Grams {
  return grams(Math.round(lb * GRAMS_PER_POUND));
}

/** Whole-pound display value, separate from the exact `gramsToPounds` so round-trip (display -> canonical -> display) idempotency can be tested precisely against what a user actually sees. */
export function roundedPounds(g: Grams): number {
  return Math.round(g / GRAMS_PER_POUND);
}

/** "154 lb" for imperial, "70 kg" for metric. `null` in, `null` out (an unset optional weight has nothing to format). */
export function formatWeight(g: Grams | null, pref: UnitPreference): string | null {
  if (g === null) return null;
  if (pref === 'imperial') return `${roundedPounds(g)} lb`;
  return `${Math.round(g / 1000)} kg`;
}
