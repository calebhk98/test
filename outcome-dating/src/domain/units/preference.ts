/**
 * src/domain/units/preference.ts — per-user display unit preference.
 *
 * The single knob that drives which unit a value is CONVERTED TO at the
 * presentation boundary (see the module doc in `index.ts`). It never
 * affects what is stored — `profile.service.ts`'s `unit_preference` column
 * only changes which conversion function a caller applies when rendering
 * a value that is, underneath, always canonical (see `distance.ts`,
 * `height.ts`, `weight.ts`).
 */
import { z } from 'zod';

export type UnitPreference = 'metric' | 'imperial';

export const UNIT_PREFERENCES: readonly UnitPreference[] = ['metric', 'imperial'];

export const unitPreferenceSchema = z.enum(['metric', 'imperial']);

/**
 * Documented default: metric.
 *
 * "Infer from country/locale if you have one" — `profiles` (see
 * `profile.service.ts`'s `ProfileRow`) has no country/locale column, only
 * a free-text `city`, which is not a reliable signal to parse a country
 * out of. So today every call resolves to the static default below.
 *
 * `resolveDefaultUnitPreference` still takes an optional ISO-3166 alpha-2
 * country code so that the moment such a column exists, the default
 * becomes locale-aware by passing it in — no call site needs to change
 * shape, only what it passes.
 */
export const DEFAULT_UNIT_PREFERENCE: UnitPreference = 'metric';

/** ISO-3166 alpha-2 codes of the countries that primarily use imperial/US customary units (miles, feet+inches, pounds) for everyday personal measurements. */
const IMPERIAL_COUNTRY_CODES: ReadonlySet<string> = new Set(['US', 'LR', 'MM']);

export function resolveDefaultUnitPreference(countryCode?: string | null): UnitPreference {
  if (countryCode && IMPERIAL_COUNTRY_CODES.has(countryCode.trim().toUpperCase())) {
    return 'imperial';
  }
  return DEFAULT_UNIT_PREFERENCE;
}
