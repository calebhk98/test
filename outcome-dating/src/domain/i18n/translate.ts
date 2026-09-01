/**
 * src/domain/i18n/translate.ts — turns (locale, catalog key, params) into
 * a rendered string, walking the fallback chain and never leaking a raw
 * key or throwing over a MISSING TRANSLATION (only over a missing KEY,
 * which is an authoring bug — see `translate`'s doc below for the
 * distinction).
 */
import { CATALOGS } from './catalog.js';
import type { CatalogEntry, CatalogParamValue, CatalogParams } from './catalog.js';
import { DEFAULT_LOCALE, fallbackChain, normalizeLocaleTag } from './locales.js';
import { formatLongDate, formatMoney, formatNumber, pluralCategory } from './format.js';

export interface TranslateResult {
  /** The rendered, ready-to-display string. */
  text: string;
  /** Which locale in the fallback chain actually supplied the text. */
  resolvedLocale: string;
  /** True when `resolvedLocale` is not the caller's requested locale — i.e. this render degraded to a fallback (e.g. a not-yet-translated locale, or a not-yet-translated key within an otherwise-shipped locale) rather than throwing or showing the raw key. */
  usedFallback: boolean;
}

function formatParam(value: CatalogParamValue, locale: string): string {
  if (typeof value === 'string') return value;
  if (typeof value === 'number') return formatNumber(value, locale);
  if (value instanceof Date) return formatLongDate(value, locale);
  return formatMoney(value.amountMinorUnits, value.currency, locale);
}

/** Replaces every `{name}` placeholder in `template` with its formatted param. Throws if a placeholder has no matching param — a mismatched template/params pair is a caller (code) bug, not a user-facing or locale-data condition, so this deliberately does NOT fail soft into showing the literal `{name}` to a user. */
function interpolate(template: string, params: CatalogParams, locale: string): string {
  return template.replace(/\{(\w+)\}/g, (whole, name: string) => {
    if (!(name in params)) {
      throw new Error(`i18n: template "${template}" references param "{${name}}" which was not supplied`);
    }
    return formatParam(params[name]!, locale);
  });
}

function renderEntry(entry: CatalogEntry, params: CatalogParams, locale: string): string {
  if (entry.kind === 'text') {
    return interpolate(entry.text, params, locale);
  }
  const rawCount = params[entry.countParam];
  if (typeof rawCount !== 'number') {
    throw new Error(`i18n: plural entry needs a numeric "${entry.countParam}" param`);
  }
  const category = pluralCategory(rawCount, locale);
  const form = entry.forms[category] ?? entry.forms.other;
  return interpolate(form, params, locale);
}

/**
 * Renders `key` for `requestedLocale`, walking the fallback chain
 * (`fallbackChain` — requested -> base language -> `DEFAULT_LOCALE`) and
 * returning the FIRST locale in that chain whose catalog actually defines
 * `key`.
 *
 * Two very different failure shapes, handled deliberately differently
 * (task brief: "a missing translation degrading to the fallback rather
 * than showing a key"):
 *   - MISSING TRANSLATION (key exists in `en`, not in the requested
 *     locale's catalog, or the requested locale isn't shipped at all) —
 *     never an error. Falls through to the next locale in the chain;
 *     since `en` is guaranteed to define every real key, this always
 *     succeeds and the caller gets real text, just not in the language
 *     they asked for. `usedFallback: true` on the result is how a caller
 *     (or a test) can tell this happened without it being a thrown error.
 *   - MISSING KEY (not defined even in `en`) — a genuine authoring bug
 *     (a caller typo'd the key, or a key was removed but a call site
 *     wasn't updated), and DOES throw — the alternative would be
 *     rendering the raw key string (e.g. `"notifications.newMessages"`)
 *     to a real user, which is worse than crashing loudly in dev/test.
 */
export function translate(requestedLocale: string, key: string, params: CatalogParams = {}): TranslateResult {
  const requestedNormalized = normalizeLocaleTag(requestedLocale);
  const chain = fallbackChain(requestedLocale);

  for (const locale of chain) {
    const entry = CATALOGS[locale]?.[key];
    if (!entry) continue;
    return {
      text: renderEntry(entry, params, locale),
      resolvedLocale: locale,
      usedFallback: locale !== requestedNormalized,
    };
  }

  throw new Error(`i18n: unknown catalog key "${key}" (missing even from the base locale "${DEFAULT_LOCALE}")`);
}

/** True iff `key` exists in the base (`en`) catalog — i.e. is a legal key to call `translate` with at all. Used by tests and by callers that want to validate a key before it's wired to a template registry elsewhere. */
export function isKnownCatalogKey(key: string): boolean {
  return key in CATALOGS[DEFAULT_LOCALE]!;
}
