/**
 * Timestamp formatting. Every timestamp on the wire is an ISO-8601
 * instant; the server deliberately never sends a pre-formatted or
 * relative string (see the task brief), so all formatting, including
 * "in 6 hours"-style copy, happens here, at render time, in the
 * device's own locale and timezone. `Intl.DateTimeFormat` with no
 * explicit `timeZone` already uses the device's local zone.
 */

export function formatDateTime(iso: string, locale?: string): string {
  return new Intl.DateTimeFormat(locale, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(iso));
}

export function formatDate(iso: string, locale?: string): string {
  return new Intl.DateTimeFormat(locale, { dateStyle: 'medium' }).format(new Date(iso));
}

export function formatTime(iso: string, locale?: string): string {
  return new Intl.DateTimeFormat(locale, { timeStyle: 'short' }).format(new Date(iso));
}

/**
 * A fact, not a countdown. The product review flags countdown-style
 * copy ("2h 14m left!") as reading like pressure; a plain "Open until
 * <date>" reads as a fact instead (docs/ux-product-review.md, "the
 * 48-hour interest/proposal clock"). This helper exists only for the
 * rare place a duration is genuinely useful (e.g. "about 2 days"), not
 * for headline copy.
 */
export function roughDurationFromNow(iso: string, now: Date = new Date()): string {
  const ms = new Date(iso).getTime() - now.getTime();
  const hours = Math.round(Math.abs(ms) / (1000 * 60 * 60));
  if (hours < 1) return 'less than an hour';
  if (hours < 48) return `about ${hours} hour${hours === 1 ? '' : 's'}`;
  const days = Math.round(hours / 24);
  return `about ${days} day${days === 1 ? '' : 's'}`;
}

export function isPast(iso: string, now: Date = new Date()): boolean {
  return new Date(iso).getTime() < now.getTime();
}
