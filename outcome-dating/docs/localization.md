# Localization

## Architecture

```
src/domain/i18n/
  locales.ts               locale identity, Accept-Language parsing, negotiation, fallback chain, RTL direction
  format.ts                Intl-backed money / number / date / plural-category formatting
  catalog.ts                the static copy catalogue itself (en base + es worked locale)
  translate.ts              catalog key + params -> rendered string, walking the fallback chain
  statusLabels.ts            non-colour status tone + label registry (see docs/accessibility.md rule 2)
  questionLocalization.ts   question-bank translation storage + pure localize-a-QuestionDefinition function

src/services/photoAltText.service.ts   (accessibility, not localization, but same "attach without editing" shape)
src/http/routes/i18n.routes.ts         GET /locales, GET|PUT /me/locale
db/migrations/021_retention_i18n.sql   user_locale_preferences, question_bank_translations, user_photos.alt_text
```

Static-template discipline (spec §1: no generative LLM text) is kept
throughout: every catalog entry is fixed, human-authored text with named
`{placeholder}` slots, never string concatenation and never a model call.

### Catalog + fallback chain

`translate(locale, key, params)` walks `fallbackChain(locale)` —
`["es-MX", "es", "en"]` for a request negotiated to `es-MX`, `["en"]` for
`en` — and returns the first locale in that chain whose catalog actually
defines `key`. Two distinct failure shapes, handled deliberately
differently:

- **Missing translation** (the key exists in `en`, not in the requested
  locale) — never an error. Falls through the chain; `en` is guaranteed
  to define every real key, so this always succeeds. The result carries
  `usedFallback: true` so a caller (or a test) can tell without it being
  an exception.
- **Missing key** (doesn't exist even in `en`) — throws. Rendering the
  raw key string (`"notifications.newMessages"`) to a real user would be
  worse than crashing loudly in dev/test; this is a caller/authoring bug,
  never a runtime/user condition.

This is the literal implementation of the task brief's "a missing
translation degrading to the fallback rather than showing a key."

### What ships vs. what's a worked example

- `en` — base/fallback. Every catalog key exists here.
- `es` — the one worked second locale the task brief asks for, proving
  the mechanism end to end with **real, human-written Spanish** — not
  machine-translated (the brief's explicit instruction).
- `fr`, `de`, `pt-BR`, `ja`, `ar`, `he` — registered in
  `LOCALE_REGISTRY` (correct number/date/plural/RTL-direction handling
  via `Intl` works for them today) but carry **zero** catalog entries —
  `status: 'needs_translation'` is the explicit, machine-readable marker.
  Requesting any of them degrades to English copy via the fallback chain
  above; nothing pretends otherwise.

### Pluralisation

Never a hardcoded `n === 1 ? singular : plural` check. A plural catalog
entry declares which param is the count and a `forms` map keyed by CLDR
plural category (`zero | one | two | few | many | other`);
`format.ts#pluralCategory` calls `Intl.PluralRules(locale).select(count)`
to pick the category, so a language with more than two categories (e.g.
Arabic's six) is handled correctly by the same code path the moment its
catalog exists — `tests/unit/i18n.test.ts` asserts
`pluralCategory` actually returns Arabic's `'zero'|'two'|'few'|'many'`
categories (not just `'one'|'other'`) to prove the *mechanism*, not the
Spanish copy, handles that case.

### Currency (the escrow amount is not always dollars)

`payment_holds.currency` / `payment_ledger.currency` /
`date_proposals.escrow_amount_cents` already store a real ISO 4217 code
per row (`db/migrations/001_init.sql` — "all money is bigint minor-unit
cents", currency stored alongside, not assumed) — the schema was never
the blocker. `format.ts#formatMoney(amountMinorUnits, currency, locale)`
divides by the *correct* minor-unit exponent for that currency (2 for
most, 0 for zero-decimal currencies like JPY/KRW, 3 for three-decimal
ones like BHD/KWD) and formats via `Intl.NumberFormat`'s `currency`
style — `formatMoney(150000, 'EUR', 'es')` → `"1.500,00 €"`, proving both
a non-dollar currency and locale-correct grouping/symbol placement.

**What's actually hardcoded, and where**: two call sites in
`dateProposal.service.ts` (owned by another agent, not touched by this
build) currently write `currency: 'usd'` literally when creating an
escrow hold. Nothing downstream forces that — `formatMoney` above and
the whole payments schema are currency-agnostic already. **What that
file's owner would adopt**: thread a real currency (from the venue, or a
future user/region setting) into those two call sites instead of the
literal `'usd'`; no schema change needed, since the column already
accepts any code.

### Name and date order

**Names**: not applicable at the schema level — `profiles.display_name`
is a single free-text field the user chooses themselves (see
`profile.service.ts`), not a decomposed given-name/family-name pair this
backend could get the ORDER of wrong. There is nothing to reorder.

**Dates**: the API's own JSON fields stay ISO-8601 UTC always (see
docs/accessibility.md rule 4) — never reordered, never localized, by
design. The one place static copy legitimately needs a date *inside a
sentence* (`notifications.dateReminder`: "Your date at {venueName} is on
{date}.") takes a real `Date` and formats it via
`format.ts#formatLongDate` (`Intl.DateTimeFormat(locale, {dateStyle:
'long'})`) at render time — word/field order is exactly what `Intl`'s
locale data already gets right, so this code never hand-assembles
`${month}/${day}/${year}`. Compare the `en` and `es` catalog entries for
this key directly: English says "is **on** {date}", Spanish says "es
**el** {date}" — a translated whole sentence, not an English sentence
with a translated date spliced in. That's why every catalog entry is a
full per-locale sentence rather than a language-agnostic template with
translated fragments glued around it.

### Right-to-left text

`getLocaleDirection(locale)` (`locales.ts`) returns `'rtl'` for Arabic,
Hebrew, and five other RTL language subtags — checked independently of
`LOCALE_REGISTRY`, so even a locale this backend has never explicitly
registered (e.g. a raw `fa-IR` Accept-Language value) still gets correct
direction metadata rather than silently defaulting to `'ltr'`. This is
metadata for a client to apply (e.g. setting `dir="rtl"` on a text
container) — the backend has no layout to mirror itself.

### Units are a separate, pre-existing choice — never overridden by locale

`profiles.unit_preference` (`'metric' | 'imperial'`,
`src/domain/units/preference.ts`) already exists and is completely
independent of locale — this build does not read it, write it, or let
locale negotiation influence it in any way. A Spanish-speaking user in
the US who prefers `imperial`, and an English-speaking user in Germany
who prefers `metric`, are both fully supported today and remain so;
locale governs *language*, `unit_preference` governs *units*, and mixing
the two would silently override a preference the user set explicitly.

## Locale negotiation

`resolveLocale({ storedPreference, acceptLanguageHeader })`
(`locales.ts`) — a stored preference **always** wins over the request's
`Accept-Language` header (task brief: "honouring a stored preference over
a request header"), because a header reflects the device's OS setting at
the moment of the request, which shouldn't govern an account-level choice
(borrowed device, travel, ...). Only when nothing is stored does the
header get a say (`parseAcceptLanguage` sorts by descending `q`, RFC
9110 §12.5.4); if neither yields anything, `DEFAULT_LOCALE` (`'en'`).

`GET /me/locale` / `PUT /me/locale` (`src/http/routes/i18n.routes.ts`)
expose this per user, backed by a dedicated `user_locale_preferences`
table (not a `users`/`profiles` column — avoids write contention on
either of those two heavily-shared tables, same reasoning
`notification_quiet_hours` already applied to its own per-user setting).
`GET /locales` is public and returns `LOCALE_REGISTRY` for a client's
language picker, including pre-sign-in.

## The question bank: what its owner needs to adopt

Questions are user-visible content and need localized text and option
labels — but `question.service.ts`, `src/domain/questions/**`, and the
`question_bank`/`user_question_answers` tables are all actively owned by
a concurrent build cutting the question system over to the new typed
bank right now. This build's localization attaches to that structure
without editing any of those files:

- **New table**: `question_bank_translations` (this build's own
  migration), `PRIMARY KEY (question_bank_id, locale)`, FK'd to
  `question_bank(id) ON DELETE CASCADE`. Keyed by the row's immutable
  per-**version** id — the same id an answer itself pins to (see
  `008_questions.sql`'s "answer-version pinning" doc) — specifically so a
  translation is pinned to the exact English wording it was translated
  FROM. Editing a question's English text (which creates a new
  `question_bank` row with a new id, per that table's own versioning
  design) simply means the new version starts with no translation yet
  (falls back to English) rather than silently showing stale Spanish next
  to new English.
- **Pure functions, no DB dependency of their own beyond that one new
  table**: `getQuestionTranslation(ctx, questionBankId, locale)` /
  `getQuestionTranslations(ctx, questionBankIds, locale)` (batch form,
  for a paged listing) read it; `localizeQuestionDefinition(def,
  translation)` is a **pure** function that takes the
  `QuestionDefinition` the question-bank code already builds and returns
  a copy with `questionText` and every option/scale-endpoint label
  overridden, degrading field-by-field to the original English when a
  translation (or one specific field of it) doesn't exist yet.

**The exact integration point** — one call site, additive: wherever
`question.service.ts` maps its own DB row into the `QuestionDefinition`
it returns to a client, add:

```ts
const translation = await getQuestionTranslation(ctx, def.id, resolvedLocale);
const localizedDef = localizeQuestionDefinition(def, translation);
```

(or the batch form for a listing endpoint). No schema change on that
file's side, no behavior change for a question with no translation row
yet (`localizeQuestionDefinition(def, null) === def`, effectively), and
`resolvedLocale` is whatever `resolveLocale(...)` already resolved for
the request.

## Do not machine-translate

Every string in `src/domain/i18n/catalog.ts` and
`src/domain/i18n/statusLabels.ts` was written directly for this task —
`es` proves the mechanism with a real, reviewed second language; every
other registered locale is explicitly marked `needs_translation` and
carries no catalog entries at all, rather than a machine-translated
placeholder standing in as if it were reviewed copy.
