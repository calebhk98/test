/**
 * Money formatting. The server sends integer cents plus an ISO-4217
 * currency code; this is the one place that turns that into a display
 * string, using the device locale so grouping/decimal marks match what
 * the reader expects.
 */
export function formatCents(amountCents: number, currency: string, locale?: string): string {
  try {
    return new Intl.NumberFormat(locale, { style: 'currency', currency: currency.toUpperCase() }).format(amountCents / 100);
  } catch {
    return `$${(amountCents / 100).toFixed(2)}`;
  }
}
