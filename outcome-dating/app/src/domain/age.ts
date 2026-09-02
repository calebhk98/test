/** Pure age arithmetic, shared by the sign-up form's live validation and its component tests. Mirrors the eighteen-and-over rule the server enforces; this is a client-side early check for a better form experience, never the actual gate (the server is always the authority). */

export const MINIMUM_AGE = 18;

export function calculateAge(birthdateIso: string, today: Date = new Date()): number | null {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(birthdateIso);
  if (!match) return null;
  const [, yearStr, monthStr, dayStr] = match;
  const year = Number(yearStr);
  const month = Number(monthStr);
  const day = Number(dayStr);
  if (month < 1 || month > 12 || day < 1 || day > 31) return null;

  const birth = new Date(Date.UTC(year, month - 1, day));
  if (birth.getUTCFullYear() !== year || birth.getUTCMonth() !== month - 1 || birth.getUTCDate() !== day) return null;
  if (birth.getTime() > today.getTime()) return null;

  let age = today.getUTCFullYear() - year;
  const hadBirthdayThisYear =
    today.getUTCMonth() > month - 1 || (today.getUTCMonth() === month - 1 && today.getUTCDate() >= day);
  if (!hadBirthdayThisYear) age -= 1;
  return age;
}

export function isAtLeastMinimumAge(birthdateIso: string, today: Date = new Date()): boolean {
  const age = calculateAge(birthdateIso, today);
  return age !== null && age >= MINIMUM_AGE;
}
