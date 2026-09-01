/**
 * src/domain/units/height.ts — height measure.
 *
 * CANONICAL STORAGE UNIT: whole centimetres (integer). Height is a
 * STORED profile field (unlike distance, which is always recomputed), so
 * the task's integer-discipline requirement applies directly: a stored
 * `height_cm` is always a whole number, never a float that could drift a
 * `gte`/`lte` filter comparison by a fraction of a unit across reads.
 * Imperial height has no clean whole-unit equivalent (a "whole foot" is
 * far too coarse; a "whole inch" is the natural imperial granularity, and
 * 1 inch ≈ 2.54cm, finer than a whole cm) — so centimetres is also the
 * finer-grained, information-preserving choice between the two.
 */
import { brand, type Brand } from './brand.js';
import type { UnitPreference } from './preference.js';

export type Centimetres = Brand<number, 'Centimetres'>;

const CM_PER_INCH = 2.54; // exact, internationally defined
const INCHES_PER_FOOT = 12;

/** The only way to mint a `Centimetres` value from a raw number. Throws on a non-integer or negative input — see the file doc for why height is integer-only. */
export function centimetres(value: number): Centimetres {
  if (!Number.isInteger(value) || value < 0) {
    throw new RangeError(`Centimetres must be a non-negative integer, got ${value}`);
  }
  return brand(value);
}

export interface FeetInches {
  feet: number;
  inches: number; // 0-11
}

/** Rounds to the nearest whole inch, then splits into feet+inches — the conventional imperial height display ("5'11\""). */
export function centimetresToFeetInches(cm: Centimetres): FeetInches {
  const totalInches = Math.round(cm / CM_PER_INCH);
  const feet = Math.floor(totalInches / INCHES_PER_FOOT);
  const inches = totalInches - feet * INCHES_PER_FOOT;
  return { feet, inches };
}

/** Inverse of `centimetresToFeetInches`, rounded back to a whole centimetre (integer discipline — see file doc). */
export function feetInchesToCentimetres(feet: number, inches: number): Centimetres {
  const totalInches = feet * INCHES_PER_FOOT + inches;
  return centimetres(Math.round(totalInches * CM_PER_INCH));
}

/** "5'11\"" for imperial, "180 cm" for metric. `null` in, `null` out (an unset optional height has nothing to format). */
export function formatHeight(cm: Centimetres | null, pref: UnitPreference): string | null {
  if (cm === null) return null;
  if (pref === 'imperial') {
    const { feet, inches } = centimetresToFeetInches(cm);
    return `${feet}'${inches}"`;
  }
  return `${cm} cm`;
}
