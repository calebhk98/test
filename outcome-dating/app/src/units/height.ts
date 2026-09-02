/**
 * Height formatting: canonical storage is centimetres (`heightCm`);
 * imperial display is feet+inches, not decimal feet, since that is how
 * height is actually read aloud.
 */
import type { UnitPreference } from '../api/types';

const CM_PER_INCH = 2.54;

export function formatHeight(cm: number | null, pref: UnitPreference): string | null {
  if (cm === null) return null;
  if (pref === 'imperial') {
    const totalInches = Math.round(cm / CM_PER_INCH);
    const feet = Math.floor(totalInches / 12);
    const inches = totalInches % 12;
    return `${feet}'${inches}"`;
  }
  return `${Math.round(cm)} cm`;
}
