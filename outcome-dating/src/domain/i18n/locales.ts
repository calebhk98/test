/**
 * src/domain/i18n/locales.ts — locale identity, negotiation, and the
 * fallback chain every catalog lookup (see translate.ts) walks.
 *
 * Scope note: this whole `src/domain/i18n/**` tree is new, additive
 * infrastructure. It does not change what any existing route returns —
 * see docs/localization.md for exactly what an owning file (question
 * bank, notification templates, ...) needs to adopt to actually put a
 * locale-aware string in front of a user.
 */

/** A BCP-47-ish language tag, e.g. "en", "es", "es-MX", "pt-BR". Never validated against a fixed enum here — Intl.NumberFormat/DateTimeFormat/PluralRules accept any syntactically valid tag and degrade gracefully (fall back to a "best effort" match) even for one this backend has never heard of, so locale NEGOTIATION (this file) stays permissive; only the CATALOG (translate.ts) needs an explicit fallback since static copy genuinely doesn't exist for every tag. */
export type LocaleTag = string;

export type LocaleDirection = 'ltr' | 'rtl';

export interface LocaleInfo {
  /** Canonical tag as stored/negotiated. */
  code: LocaleTag;
  englishName: string;
  nativeName: string;
  dir: LocaleDirection;
  /** 'shipped': src/domain/i18n/catalog.ts has real, human-reviewed copy for this locale. 'needs_translation': registered (shows up as a selectable locale, gets correct number/date/plural/RTL handling) but every catalog lookup degrades to the English fallback until a real translator fills it in — see docs/localization.md's "what ships vs what's a worked example" note. */
  status: 'shipped' | 'needs_translation';
}

export const DEFAULT_LOCALE: LocaleTag = 'en';

/**
 * The locale registry. `en` is the base/fallback locale (every catalog key
 * MUST exist here — translate.ts throws if one doesn't). `es` is the one
 * "worked second locale" the task brief asks for, proving the mechanism
 * end to end (plural forms, currency, interpolation) with real,
 * human-written Spanish — not machine-translated.
 *
 * Everything below `es` is deliberately registered with NO catalog
 * entries: they exist so the *mechanism* (locale negotiation, RTL
 * direction, number/date formatting via Intl) already works correctly the
 * day a real translator's strings land, without a code change — but their
 * copy is 100% English-fallback today. `status: 'needs_translation'` is
 * the explicit, machine-readable marker for that (see localeStatus below)
 * — nothing here pretends these are translated.
 */
export const LOCALE_REGISTRY: readonly LocaleInfo[] = [
  { code: 'en', englishName: 'English', nativeName: 'English', dir: 'ltr', status: 'shipped' },
  { code: 'es', englishName: 'Spanish', nativeName: 'Español', dir: 'ltr', status: 'shipped' },
  { code: 'fr', englishName: 'French', nativeName: 'Français', dir: 'ltr', status: 'needs_translation' },
  { code: 'de', englishName: 'German', nativeName: 'Deutsch', dir: 'ltr', status: 'needs_translation' },
  { code: 'pt-BR', englishName: 'Portuguese (Brazil)', nativeName: 'Português (Brasil)', dir: 'ltr', status: 'needs_translation' },
  { code: 'ja', englishName: 'Japanese', nativeName: '日本語', dir: 'ltr', status: 'needs_translation' },
  { code: 'ar', englishName: 'Arabic', nativeName: 'العربية', dir: 'rtl', status: 'needs_translation' },
  { code: 'he', englishName: 'Hebrew', nativeName: 'עברית', dir: 'rtl', status: 'needs_translation' },
];

const REGISTRY_BY_CODE: ReadonlyMap<string, LocaleInfo> = new Map(LOCALE_REGISTRY.map((l) => [l.code.toLowerCase(), l]));

/** Language subtags that read right-to-left. Consulted independently of `LOCALE_REGISTRY` so an *unregistered* locale (e.g. a raw "fa-IR" Accept-Language value we've never listed) still gets correct direction metadata rather than silently defaulting to "ltr". */
const RTL_LANGUAGE_SUBTAGS: ReadonlySet<string> = new Set(['ar', 'he', 'fa', 'ur', 'yi', 'ps', 'sd']);

function baseLanguage(locale: LocaleTag): string {
  return (locale.split('-')[0] ?? locale).toLowerCase();
}

/** Canonicalizes casing (language lowercase, region uppercase) without validating the tag is "real" — `Intl` is the source of truth for that, and calling it here on every negotiated header value would make a malformed header a 500 instead of a graceful default. */
export function normalizeLocaleTag(raw: string): LocaleTag {
  const parts = raw.trim().split('-');
  const lang = (parts[0] ?? '').toLowerCase();
  const rest = parts.slice(1).map((p) => (p.length === 2 ? p.toUpperCase() : p.toLowerCase()));
  return [lang, ...rest].filter(Boolean).join('-');
}

export function findLocaleInfo(locale: LocaleTag): LocaleInfo | undefined {
  return REGISTRY_BY_CODE.get(locale.toLowerCase()) ?? REGISTRY_BY_CODE.get(baseLanguage(locale));
}

/** Direction never silently defaults from an unrecognized tag to "wrong": known RTL language subtags are honoured even for a locale not in `LOCALE_REGISTRY`. */
export function getLocaleDirection(locale: LocaleTag): LocaleDirection {
  const info = findLocaleInfo(locale);
  if (info) return info.dir;
  return RTL_LANGUAGE_SUBTAGS.has(baseLanguage(locale)) ? 'rtl' : 'ltr';
}

/**
 * The chain a catalog lookup walks, most-specific first, always ending at
 * `DEFAULT_LOCALE`: `"es-MX"` -> `["es-MX", "es", "en"]`; `"en"` -> `["en"]`.
 * Region variants (`es-MX`) fall back to their base language (`es`) before
 * falling back to English — the base-language catalog is what
 * `LOCALE_REGISTRY` actually ships, region variants only affect
 * Intl-driven number/date/plural formatting, never the copy lookup.
 */
export function fallbackChain(locale: LocaleTag): LocaleTag[] {
  const chain: LocaleTag[] = [];
  const normalized = normalizeLocaleTag(locale);
  if (normalized) chain.push(normalized);
  const base = baseLanguage(normalized || locale);
  if (base && !chain.includes(base)) chain.push(base);
  if (!chain.includes(DEFAULT_LOCALE)) chain.push(DEFAULT_LOCALE);
  return chain;
}

/** One entry of a parsed `Accept-Language` header, in the header's own field names (RFC 4647 / RFC 9110 §12.5.4). */
interface WeightedLocale {
  tag: string;
  q: number;
}

/**
 * Parses an `Accept-Language` header into tags ordered by descending
 * quality (`q`), stable on ties (header order preserved). Never throws —
 * a malformed header (or `undefined`/empty string) just yields `[]`, which
 * `resolveLocale` treats the same as "no header sent".
 */
export function parseAcceptLanguage(header: string | null | undefined): string[] {
  if (!header) return [];
  const parsed: WeightedLocale[] = [];
  for (const part of header.split(',')) {
    const [tagRaw, ...params] = part.trim().split(';').map((s) => s.trim());
    if (!tagRaw) continue;
    if (tagRaw === '*') continue; // a wildcard names no concrete locale to negotiate to
    let q = 1;
    for (const param of params) {
      const [k, v] = param.split('=').map((s) => s.trim());
      if (k === 'q' && v !== undefined) {
        const n = Number(v);
        if (Number.isFinite(n)) q = n;
      }
    }
    parsed.push({ tag: tagRaw, q });
  }
  // Stable sort by descending q — Array#sort is stable per spec (Node/V8),
  // so header order is preserved among equal-q entries.
  return parsed
    .sort((a, b) => b.q - a.q)
    .filter((w) => w.q > 0)
    .map((w) => w.tag);
}

export type LocaleSource = 'stored_preference' | 'accept_language_header' | 'default';

export interface ResolvedLocale {
  locale: LocaleTag;
  source: LocaleSource;
}

/**
 * Per-user locale negotiation: a STORED preference always wins over the
 * request's `Accept-Language` header (task brief: "honouring a stored
 * preference over a request header") — a header reflects the device's OS
 * setting at the moment of the request, which a user may not want to
 * govern an account-level choice (e.g. borrowing a friend's phone,
 * traveling). Only when nothing is stored does the header get a say; if
 * neither yields anything, `DEFAULT_LOCALE`.
 *
 * Deliberately does NOT require the resolved locale to be one of
 * `LOCALE_REGISTRY`'s entries — see the `LocaleTag` doc above for why:
 * `translate()`'s own fallback chain is what makes an unshipped locale
 * safe to resolve to (it degrades to English copy, never a raw key or a
 * throw), and Intl formatting works for locales this backend has never
 * explicitly registered.
 */
export function resolveLocale(opts: { storedPreference?: string | null; acceptLanguageHeader?: string | null }): ResolvedLocale {
  if (opts.storedPreference) {
    return { locale: normalizeLocaleTag(opts.storedPreference), source: 'stored_preference' };
  }
  const candidates = parseAcceptLanguage(opts.acceptLanguageHeader);
  const first = candidates[0];
  if (first) {
    return { locale: normalizeLocaleTag(first), source: 'accept_language_header' };
  }
  return { locale: DEFAULT_LOCALE, source: 'default' };
}
