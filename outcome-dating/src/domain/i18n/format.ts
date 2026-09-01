/**
 * src/domain/i18n/format.ts — locale-aware formatting for the two things
 * that break hardest when a backend assumes "everyone reads English
 * numbers and everyone pays in dollars": money and plain numbers.
 *
 * IMPORTANT boundary (see docs/accessibility.md): the API itself keeps
 * returning STRUCTURED values — `amount_cents` (bigint) + `currency`
 * (ISO 4217 code) as separate JSON fields, timestamps as ISO-8601 UTC —
 * never a pre-formatted display string. These functions exist for the
 * one place static copy legitimately needs to INTERPOLATE a formatted
 * number into a translated sentence (see translate.ts) — e.g. "Your
 * deposit of {amount} was refunded" — not to replace the raw API fields.
 * A client is always free to format the raw fields itself in the
 * viewer's own locale/text size/number system; this module is what the
 * i18n catalog's own template rendering uses internally.
 */

/**
 * ISO 4217 currencies with a minor-unit exponent other than the default
 * 2 — the exact fact the task brief's "escrow amount is not always
 * dollars" note is pointing at: a naive `amountMinorUnits / 100` is wrong
 * for a zero-decimal currency (divides a whole-yen amount by 100) and for
 * a three-decimal one (loses a digit of precision). Not exhaustive of
 * every ISO 4217 currency — just the common zero/three-decimal ones a
 * payment processor is realistically configured for — deliberately a
 * short, auditable list rather than silently defaulting everything
 * unlisted to 2 without anyone having decided that's correct for it.
 */
const ZERO_DECIMAL_CURRENCIES: ReadonlySet<string> = new Set([
  'BIF', 'CLP', 'DJF', 'GNF', 'ISK', 'JPY', 'KMF', 'KRW', 'PYG', 'RWF', 'UGX', 'VND', 'VUV', 'XAF', 'XOF', 'XPF',
]);
const THREE_DECIMAL_CURRENCIES: ReadonlySet<string> = new Set(['BHD', 'IQD', 'JOD', 'KWD', 'LYD', 'OMR', 'TND']);

/** Minor-unit exponent for `currency` — how many digits of `amountMinorUnits` are the fractional part. Defaults to 2 (USD, EUR, GBP, ... the overwhelming majority of currencies) for anything not explicitly listed above. */
export function minorUnitDigits(currency: string): number {
  const code = currency.trim().toUpperCase();
  if (ZERO_DECIMAL_CURRENCIES.has(code)) return 0;
  if (THREE_DECIMAL_CURRENCIES.has(code)) return 3;
  return 2;
}

/**
 * Formats a minor-unit integer amount (the same shape `payment_holds`/
 * `payment_ledger`/`date_proposals.escrow_amount_cents` already store —
 * see db/migrations/001_init.sql's "all money is bigint minor-unit cents"
 * convention) as a locale-correct, currency-symbol-and-grouping-correct
 * string, e.g. `formatMoney(150000, 'EUR', 'es')` -> `"1.500,00 €"`,
 * `formatMoney(150000, 'USD', 'en')` -> `"$1,500.00"`.
 *
 * Deliberately takes `currency` as an explicit parameter rather than
 * assuming USD — `payment_holds.currency`/`payment_ledger.currency`
 * already carry a real ISO code per row (db/migrations/001_init.sql), so
 * nothing about the schema forces USD; only two call sites in
 * `dateProposal.service.ts` (a file this build does not own or touch)
 * currently hardcode the literal `'usd'` at escrow-hold creation — see
 * docs/localization.md for the exact follow-up that file's owner would
 * need to make to let a non-USD escrow amount actually reach this
 * function with a real currency instead of a hardcoded one.
 */
export function formatMoney(amountMinorUnits: number, currency: string, locale: string): string {
  const digits = minorUnitDigits(currency);
  const major = amountMinorUnits / 10 ** digits;
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: currency.trim().toUpperCase(),
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(major);
}

/** Locale-correct grouping/decimal-separator formatting for a plain number interpolated into copy (e.g. a coalesced notification count). Never used for money — see `formatMoney`. */
export function formatNumber(value: number, locale: string): string {
  return new Intl.NumberFormat(locale).format(value);
}

/**
 * Locale-correct long-form date, for the rare case static copy needs to
 * say a date in a sentence (e.g. "Your date at {venueName} is on
 * {date}."). Takes a real `Date` — never a pre-formatted string — and
 * formats it fresh per request locale; the API's own JSON fields keep
 * returning ISO-8601 UTC regardless (see module doc above). Word/field
 * ORDER (which the task brief calls out — "day month year" vs "month day
 * year") is exactly what `Intl.DateTimeFormat`'s locale data already
 * gets right; this function deliberately never hand-assembles
 * `${month}/${day}/${year}`.
 */
export function formatLongDate(date: Date, locale: string): string {
  return new Intl.DateTimeFormat(locale, { dateStyle: 'long' }).format(date);
}

/** The CLDR plural category (RFC-ish: Unicode Plural Rules) `count` falls into for `locale` — e.g. `pluralCategory(1, 'en')` -> `'one'`, `pluralCategory(2, 'en')` -> `'other'`, while Arabic has distinct `'zero'|'one'|'two'|'few'|'many'|'other'` categories for the exact same range. Never hardcode an "n === 1 ? singular : plural" check in copy — see translate.ts's plural entries, which call this instead. */
export function pluralCategory(count: number, locale: string): Intl.LDMLPluralRule {
  return new Intl.PluralRules(locale).select(count);
}
