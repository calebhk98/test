/**
 * tests/unit/i18n.test.ts — locale negotiation, the copy catalog's
 * fallback chain, pluralisation, currency formatting for a non-dollar
 * currency, "missing translation degrades rather than shows a key", and
 * the question-bank localization attachment
 * (src/domain/i18n/questionLocalization.ts).
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { randomUUID } from 'node:crypto';
import {
  DEFAULT_LOCALE,
  LOCALE_REGISTRY,
  fallbackChain,
  getLocaleDirection,
  normalizeLocaleTag,
  parseAcceptLanguage,
  resolveLocale,
} from '../../src/domain/i18n/locales.js';
import { formatMoney, minorUnitDigits, pluralCategory, formatNumber } from '../../src/domain/i18n/format.js';
import { translate, isKnownCatalogKey } from '../../src/domain/i18n/translate.js';
import { CATALOG_KEYS, CATALOGS } from '../../src/domain/i18n/catalog.js';
import {
  getQuestionTranslation,
  getQuestionTranslations,
  localizeQuestionDefinition,
  upsertQuestionTranslation,
} from '../../src/domain/i18n/questionLocalization.js';
import type { QuestionDefinition, ScaleDefinition, SingleChoiceDefinition } from '../../src/domain/questions/types.js';
import { setupTestDatabase, teardownTestDatabase, buildCtx, systemActor } from './testCtxRetention.js';
import type pg from 'pg';

let pool: pg.Pool;

before(async () => {
  pool = await setupTestDatabase('i18n');
});

after(async () => {
  await teardownTestDatabase();
});

// -------------------------------------------------------------------------
// Locale negotiation
// -------------------------------------------------------------------------

test('resolveLocale: a stored preference always wins over the Accept-Language header', () => {
  const result = resolveLocale({ storedPreference: 'es', acceptLanguageHeader: 'fr-FR,fr;q=0.9,en;q=0.8' });
  assert.equal(result.locale, 'es');
  assert.equal(result.source, 'stored_preference');
});

test('resolveLocale: falls back to the Accept-Language header when nothing is stored', () => {
  const result = resolveLocale({ storedPreference: null, acceptLanguageHeader: 'fr-FR,fr;q=0.9,en;q=0.8' });
  assert.equal(result.locale, 'fr-FR');
  assert.equal(result.source, 'accept_language_header');
});

test('resolveLocale: falls back to DEFAULT_LOCALE when neither a preference nor a header is present', () => {
  const result = resolveLocale({ storedPreference: null, acceptLanguageHeader: null });
  assert.equal(result.locale, DEFAULT_LOCALE);
  assert.equal(result.source, 'default');
});

test('parseAcceptLanguage: orders by descending q, ignores a bare wildcard, never throws on garbage input', () => {
  assert.deepEqual(parseAcceptLanguage('fr;q=0.5,en;q=0.9,es'), ['es', 'en', 'fr']);
  assert.deepEqual(parseAcceptLanguage('*'), []);
  assert.deepEqual(parseAcceptLanguage(undefined), []);
  assert.deepEqual(parseAcceptLanguage(''), []);
  assert.doesNotThrow(() => parseAcceptLanguage(',,,garbage;;q=notanumber'));
});

test('fallbackChain: a region variant falls back through its base language to the default locale', () => {
  assert.deepEqual(fallbackChain('es-MX'), ['es-MX', 'es', 'en']);
  assert.deepEqual(fallbackChain('en'), ['en']);
});

test('getLocaleDirection: RTL for Arabic/Hebrew even when not explicitly asked via LOCALE_REGISTRY casing, LTR otherwise', () => {
  assert.equal(getLocaleDirection('ar'), 'rtl');
  assert.equal(getLocaleDirection('he-IL'), 'rtl');
  assert.equal(getLocaleDirection('es'), 'ltr');
  assert.equal(getLocaleDirection('fa'), 'rtl', 'a locale not in LOCALE_REGISTRY at all still gets correct direction from its language subtag');
});

test('LOCALE_REGISTRY: exactly en and es are shipped; every other registered locale is explicitly marked as needing translation', () => {
  const shipped = LOCALE_REGISTRY.filter((l) => l.status === 'shipped').map((l) => l.code);
  assert.deepEqual(shipped.sort(), ['en', 'es']);
  assert.ok(LOCALE_REGISTRY.some((l) => l.status === 'needs_translation'));
});

test('normalizeLocaleTag: canonicalizes casing without validating the tag is real', () => {
  assert.equal(normalizeLocaleTag('ES-mx'), 'es-MX');
  assert.equal(normalizeLocaleTag('EN'), 'en');
});

// -------------------------------------------------------------------------
// Catalog + fallback chain (translate)
// -------------------------------------------------------------------------

test('translate: renders real text for the base locale', () => {
  const result = translate('en', 'discovery.emptyState.title');
  assert.equal(result.text, 'No candidates currently match your filters.');
  assert.equal(result.resolvedLocale, 'en');
  assert.equal(result.usedFallback, false);
});

test('translate: renders real, different text for the worked second locale (es)', () => {
  const result = translate('es', 'discovery.emptyState.title');
  assert.equal(result.text, 'Ningún candidato coincide actualmente con tus filtros.');
  assert.equal(result.usedFallback, false);
});

test('translate: a missing translation (unshipped locale) degrades to the English fallback — never a thrown error, never the raw key', () => {
  const result = translate('de', 'discovery.emptyState.title'); // 'de' is registered but has zero catalog entries
  assert.equal(result.text, 'No candidates currently match your filters.');
  assert.equal(result.resolvedLocale, 'en');
  assert.equal(result.usedFallback, true);
  assert.notEqual(result.text, 'discovery.emptyState.title', 'must never show the raw key to a user');
});

test('translate: a region variant with no exact catalog falls back through its base language before English', () => {
  const result = translate('es-MX', 'discovery.emptyState.title');
  assert.equal(result.resolvedLocale, 'es', 'falls back to the base "es" catalog, not straight to "en"');
  assert.equal(result.usedFallback, true, 'still counts as a fallback — the requested tag was "es-MX", not "es"');
});

test('translate: an unknown catalog key throws — an authoring bug, not a runtime condition to hide', () => {
  assert.throws(() => translate('en', 'this.key.does.not.exist'));
});

test('isKnownCatalogKey / CATALOG_KEYS agree, and es never defines a key en does not (no orphan translations)', () => {
  for (const key of CATALOG_KEYS) {
    assert.ok(isKnownCatalogKey(key));
  }
  const enKeys = new Set(Object.keys(CATALOGS.en!));
  for (const key of Object.keys(CATALOGS.es!)) {
    assert.ok(enKeys.has(key), `es defines "${key}" which does not exist in the base "en" catalog`);
  }
});

// -------------------------------------------------------------------------
// Pluralisation
// -------------------------------------------------------------------------

test('translate: plural entry picks the right English form for one vs. many', () => {
  const one = translate('en', 'notifications.newMessages', { count: 1, name: 'Alex' });
  assert.equal(one.text, 'You have a new message from Alex.');

  const many = translate('en', 'notifications.newMessages', { count: 3, name: 'Alex' });
  assert.equal(many.text, 'You have 3 new messages from Alex.');
});

test('translate: plural entry picks the right Spanish form too', () => {
  const one = translate('es', 'notifications.newMessages', { count: 1, name: 'Marta' });
  assert.equal(one.text, 'Tienes un mensaje nuevo de Marta.');

  const many = translate('es', 'notifications.newMessages', { count: 5, name: 'Marta' });
  assert.equal(many.text, 'Tienes 5 mensajes nuevos de Marta.');
});

test('pluralCategory: the underlying mechanism handles a language with more than two plural categories (Arabic), proving this is not a hardcoded English one/other rule', () => {
  assert.equal(pluralCategory(0, 'ar'), 'zero');
  assert.equal(pluralCategory(1, 'ar'), 'one');
  assert.equal(pluralCategory(2, 'ar'), 'two');
  assert.equal(pluralCategory(11, 'ar'), 'many');
  // English only ever distinguishes 'one' from 'other' — contrast case.
  assert.equal(pluralCategory(1, 'en'), 'one');
  assert.equal(pluralCategory(11, 'en'), 'other');
});

// -------------------------------------------------------------------------
// Currency — a non-dollar currency, correctly formatted
// -------------------------------------------------------------------------

test('formatMoney: a non-dollar currency (EUR) formats with locale-correct symbol placement and grouping', () => {
  const es = formatMoney(1234560, 'EUR', 'es'); // 12,345.60
  assert.match(es, /€/);
  assert.match(es, /12\.345,60/, 'Spanish grouping uses "." and decimal comma');

  const en = formatMoney(1234560, 'USD', 'en');
  assert.match(en, /\$/);
  assert.match(en, /12,345\.60/);
});

test('formatMoney: zero-decimal currencies (e.g. JPY) never divide by 100', () => {
  assert.equal(minorUnitDigits('JPY'), 0);
  const yen = formatMoney(1500, 'JPY', 'en'); // 1500 minor units == 1500 yen, not 15.00
  assert.match(yen, /1,500/);
  assert.doesNotMatch(yen, /15\.00|15,00/);
});

test('translate: interpolates a formatted, non-dollar currency amount into a catalog sentence', () => {
  const result = translate('es', 'payments.escrowRefunded', { amount: { amountMinorUnits: 1500000, currency: 'EUR' } });
  assert.match(result.text, /€/);
  assert.match(result.text, /15\.000,00/);
});

test('formatNumber: locale-correct grouping for a plain interpolated number', () => {
  assert.equal(formatNumber(12345, 'en'), '12,345');
  assert.equal(formatNumber(12345, 'es'), '12.345');
});

// -------------------------------------------------------------------------
// Question-bank localization (attaches without touching question_bank.ts)
// -------------------------------------------------------------------------

async function insertQuestionBankRow(): Promise<{ id: string; def: QuestionDefinition }> {
  const scaleTypeDef: ScaleDefinition = { type: 'scale', min: 1, max: 5, minLabel: 'Not important', maxLabel: 'Very important', midLabel: 'Neutral' };
  const { rows } = await pool.query<{ id: string; created_at: Date; updated_at: Date }>(
    `INSERT INTO question_bank (slug, version, is_current, category, question_type, question_text, type_definition, base_weight)
     VALUES ($1, 1, true, 'lifestyle', 'scale', 'How important is regular exercise to you?', $2::jsonb, 1.0)
     RETURNING id, created_at, updated_at`,
    [`i18n-test-${randomUUID()}`, JSON.stringify(scaleTypeDef)],
  );
  const row = rows[0]!;
  const def: QuestionDefinition = {
    id: row.id,
    slug: 'i18n-test',
    version: 1,
    category: 'lifestyle',
    subcategory: null,
    tags: [],
    questionText: 'How important is regular exercise to you?',
    typeDef: scaleTypeDef,
    presentation: 'value_importance',
    baseWeight: 1.0,
    sensitive: false,
    active: true,
    answerRateHint: 0.5,
  };
  return { id: row.id, def };
}

test('getQuestionTranslation: no row yet -> null, and localizeQuestionDefinition(def, null) leaves the definition untouched', async () => {
  const { id, def } = await insertQuestionBankRow();
  const ctx = buildCtx({ actor: systemActor() });

  const translation = await getQuestionTranslation(ctx, id, 'es');
  assert.equal(translation, null);
  assert.deepEqual(localizeQuestionDefinition(def, translation), def);
});

test('getQuestionTranslation: requesting the base locale ("en") never queries a translation row at all — the base row IS the English text', async () => {
  const { id } = await insertQuestionBankRow();
  const ctx = buildCtx({ actor: systemActor() });
  const translation = await getQuestionTranslation(ctx, id, 'en');
  assert.equal(translation, null);
});

test('upsertQuestionTranslation + localizeQuestionDefinition: question text and scale labels localize field-by-field, partial translations degrade gracefully', async () => {
  const { id, def } = await insertQuestionBankRow();
  const ctx = buildCtx({ actor: systemActor() });

  // First: only the option labels are translated, not the question text yet.
  await upsertQuestionTranslation(ctx, id, 'es', {
    labels: { minLabel: 'Nada importante', maxLabel: 'Muy importante' }, // midLabel deliberately left untranslated
  });

  const partial = await getQuestionTranslation(ctx, id, 'es');
  const partialLocalized = localizeQuestionDefinition(def, partial);
  const partialScale = partialLocalized.typeDef as ScaleDefinition;
  assert.equal(partialLocalized.questionText, def.questionText, 'question text not yet translated — falls back to English');
  assert.equal(partialScale.minLabel, 'Nada importante');
  assert.equal(partialScale.maxLabel, 'Muy importante');
  assert.equal(partialScale.midLabel, 'Neutral', 'midLabel not yet translated — falls back to the original English label');

  // Then: the question text arrives too, merged with the existing label translations (not overwritten).
  await upsertQuestionTranslation(ctx, id, 'es', { questionText: '¿Qué tan importante es el ejercicio regular para ti?' });
  const full = await getQuestionTranslation(ctx, id, 'es');
  const fullLocalized = localizeQuestionDefinition(def, full);
  assert.equal(fullLocalized.questionText, '¿Qué tan importante es el ejercicio regular para ti?');
  assert.equal((fullLocalized.typeDef as ScaleDefinition).minLabel, 'Nada importante', 'earlier label translations survive a later text-only upsert (merge, not overwrite)');
});

test('localizeQuestionDefinition: single_choice option labels localize by the STABLE option key, not by position or English label', async () => {
  const choiceTypeDef: SingleChoiceDefinition = {
    type: 'single_choice',
    options: [
      { key: 'yes', label: 'Yes' },
      { key: 'no', label: 'No' },
    ],
  };
  const def: QuestionDefinition = {
    id: randomUUID(),
    slug: 'choice-test',
    version: 1,
    category: 'lifestyle',
    subcategory: null,
    tags: [],
    questionText: 'Do you want children?',
    typeDef: choiceTypeDef,
    presentation: 'ladder',
    baseWeight: 1,
    sensitive: false,
    active: true,
    answerRateHint: 0.5,
  };

  const localized = localizeQuestionDefinition(def, {
    questionBankId: def.id,
    locale: 'es',
    questionText: '¿Quieres tener hijos?',
    labels: { yes: 'Sí', no: 'No' },
    updatedAt: new Date(),
  });

  const options = (localized.typeDef as SingleChoiceDefinition).options;
  assert.deepEqual(
    options.map((o) => o.label),
    ['Sí', 'No'],
  );
  assert.deepEqual(
    options.map((o) => o.key),
    ['yes', 'no'],
    'option keys never change — only labels do',
  );
});

test('getQuestionTranslations: batch form resolves each id independently in one round trip', async () => {
  const q1 = await insertQuestionBankRow();
  const q2 = await insertQuestionBankRow();
  const ctx = buildCtx({ actor: systemActor() });

  await upsertQuestionTranslation(ctx, q1.id, 'es', { questionText: 'Pregunta uno traducida.' });
  // q2 deliberately left untranslated.

  const map = await getQuestionTranslations(ctx, [q1.id, q2.id], 'es');
  assert.equal(map.get(q1.id)?.questionText, 'Pregunta uno traducida.');
  assert.equal(map.has(q2.id), false, 'no translation row exists for q2 — absent from the map, not a null entry');
});
