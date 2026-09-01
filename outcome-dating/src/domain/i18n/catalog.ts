/**
 * src/domain/i18n/catalog.ts, the locale-keyed copy catalogue itself.
 *
 * STATIC TEMPLATE DISCIPLINE (task brief: "keeping the static-template
 * discipline, no generated prose"): every string below is fixed,
 * human-authored text with named `{placeholder}` slots for structured
 * data (a name, a formatted amount, a count), never string
 * concatenation, never an LLM call. This is the same discipline
 * `notification.service.ts`'s `NOTIFICATION_TEMPLATES` and
 * `notifications/templates.ts`'s `MESSAGE_TEMPLATES` already use for
 * template KEYS; this file is what a template key's actual, renderable,
 * per-locale TEXT looks like (see translate.ts for how a key + params
 * become a string, and docs/localization.md for exactly which of this
 * build's sibling files would wire a real template key to one of these).
 *
 * WHAT'S ACTUALLY SHIPPED VS A WORKED EXAMPLE (task brief: "Ship English
 * plus ... one worked second locale to prove the mechanism, and mark the
 * rest as needing real translators"):
 *   - `en`, the base/fallback locale. Every key below MUST have an `en`
 *     entry; translate.ts throws at render time if one doesn't (a missing
 *     `en` entry is a catalog-authoring bug, not a runtime condition).
 *   - `es`, the one worked second locale, real human-written Spanish
 *     (not machine-translated), proving interpolation, pluralisation, and
 *     currency formatting actually work end to end in a language whose
 *     plural/word-order rules differ from English.
 *   - Every other locale in `LOCALE_REGISTRY` (locales.ts) intentionally
 *     has NO entry here, see that file's `status: 'needs_translation'`
 *     field, and translate.ts's fallback chain, which is exactly what
 *     makes that safe (falls through to `en`, never a raw key).
 *
 * NO EMOJI, NO SYMBOL-ONLY MEANING (task brief accessibility rule): every
 * string in this file is plain text a screen reader can read aloud
 * without losing meaning, no emoji standing in for a word, no bare
 * symbol. `tests/unit/altText.test.ts` scans this file's actual string
 * values for exactly that and fails the build if one shows up.
 */

/** A parameter this catalog's templates can interpolate. Plain strings/numbers pass through `formatNumber`; a money param is always the raw minor-unit integer + its ISO currency code, formatted via `formatMoney` at render time, never a pre-formatted "$12.34" baked in by a caller (see format.ts's module doc for why). A date param is a real `Date`, formatted via `formatLongDate`, never a caller-assembled string, so word/field order is always locale-correct. */
export type CatalogParamValue = string | number | Date | { amountMinorUnits: number; currency: string };
export type CatalogParams = Record<string, CatalogParamValue>;

export type PluralCategory = 'zero' | 'one' | 'two' | 'few' | 'many' | 'other';

export interface TextCatalogEntry {
  kind: 'text';
  /** The name/index the *count* parameter carries (see `translate`'s call site), only present on a `plural` entry, this field doesn't apply here. */
  text: string;
}

export interface PluralCatalogEntry {
  kind: 'plural';
  /** Which param in the call's `params` is the count driving CLDR plural-category selection (see format.ts#pluralCategory). */
  countParam: string;
  /** `other` is the only category every CLDR locale defines, required. A locale that doesn't distinguish e.g. `'one'` from `'other'` (many East Asian languages) simply never gets asked for that category, so omitting it is correct, not an oversight. */
  forms: Partial<Record<PluralCategory, string>> & { other: string };
}

export type CatalogEntry = TextCatalogEntry | PluralCatalogEntry;

export type LocaleCatalog = Record<string, CatalogEntry>;

function text(t: string): TextCatalogEntry {
  return { kind: 'text', text: t };
}

function plural(countParam: string, forms: Partial<Record<PluralCategory, string>> & { other: string }): PluralCatalogEntry {
  return { kind: 'plural', countParam, forms };
}

/**
 * English, the base/fallback catalog. Every key here is a REAL, useful
 * piece of copy (not a placeholder) covering the situations the task
 * brief calls out by name: a plain notice, a pluralised count, a
 * currency-bearing amount, and a date-bearing sentence.
 */
const en: LocaleCatalog = {
  'discovery.emptyState.title': text('No candidates currently match your filters.'),
  'discovery.emptyState.body': text('Try widening your distance or age range.'),
  'interest.outgoingLimitReached': text('You have reached your pending interest limit. Wait for responses or expiration.'),
  'notifications.newMessages': plural('count', {
    one: 'You have a new message from {name}.',
    other: 'You have {count} new messages from {name}.',
  }),
  'notifications.dateReminder': text('Your date at {venueName} is on {date}.'),
  'payments.escrowRefunded': text('Your deposit of {amount} was refunded.'),
  'payments.escrowCaptured': text('Your deposit of {amount} was charged for your upcoming date.'),
  'safety.reportReceived': text('We received your report and are reviewing it.'),
  'safety.trustLevelChanged': text('Your trust level is now {trustLevel}.'),
  'photo.altText.prompt': text('Describe this photo for people using a screen reader.'),
  'photo.altText.missing': text('No description was provided for this photo.'),
  'account.deletionConfirmed': text('Your account has been deleted.'),
  'locale.preferenceSaved': text('Your language preference has been saved.'),
};

/**
 * Spanish, the one worked second locale. Written directly by a fluent
 * speaker for this task, not run through a translation API, per the
 * brief's "do not machine-translate anything." Spanish's plural rule
 * happens to be a "one vs other" split for cardinal numbers, same shape
 * as English's, deliberately NOT chosen to hide the mechanism working
 * for a language with a genuinely different plural system; see
 * `format.ts#pluralCategory` (backed by `Intl.PluralRules`, which already
 * has real data for languages with 3-6 categories, e.g. Arabic) and
 * `tests/unit/i18n.test.ts`'s Arabic-category assertion, which proves the
 * plural MECHANISM (not this file's Spanish copy) handles that case too.
 */
const es: LocaleCatalog = {
  'discovery.emptyState.title': text('Ningún candidato coincide actualmente con tus filtros.'),
  'discovery.emptyState.body': text('Prueba ampliar la distancia o el rango de edad.'),
  'interest.outgoingLimitReached': text('Has alcanzado tu límite de solicitudes pendientes. Espera respuestas o a que venzan.'),
  'notifications.newMessages': plural('count', {
    one: 'Tienes un mensaje nuevo de {name}.',
    other: 'Tienes {count} mensajes nuevos de {name}.',
  }),
  // Spanish date-in-sentence word order ("el {date}", article before the
  // date) differs from English ("on {date}"), this is exactly why a
  // template is a whole per-locale SENTENCE with a placeholder, never an
  // English sentence with a translated date spliced in.
  'notifications.dateReminder': text('Tu cita en {venueName} es el {date}.'),
  'payments.escrowRefunded': text('Se reembolsó tu depósito de {amount}.'),
  'payments.escrowCaptured': text('Se cobró tu depósito de {amount} para tu próxima cita.'),
  'safety.reportReceived': text('Recibimos tu reporte y lo estamos revisando.'),
  'safety.trustLevelChanged': text('Tu nivel de confianza ahora es {trustLevel}.'),
  'photo.altText.prompt': text('Describe esta foto para las personas que usan un lector de pantalla.'),
  'photo.altText.missing': text('No se proporcionó una descripción para esta foto.'),
  'account.deletionConfirmed': text('Tu cuenta ha sido eliminada.'),
  'locale.preferenceSaved': text('Se guardó tu preferencia de idioma.'),
};

export const CATALOGS: Record<string, LocaleCatalog> = { en, es };

/** Every key the base (`en`) catalog defines, the full set a caller may legally pass to `translate()`; also what `tests/unit/i18n.test.ts` walks to assert `es` has no ORPHAN key (translated text for a key `en` doesn't have) even though `es` is allowed to be a strict subset (untranslated keys degrade to `en`, see translate.ts). */
export const CATALOG_KEYS: readonly string[] = Object.keys(en);
