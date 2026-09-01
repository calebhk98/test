# Accessibility, what the backend guarantees, what the client owes

A backend cannot make a client accessible by itself, but it can make
accessibility *impossible* by shipping the wrong shape of data (no alt
text field, colour-only status, a pre-rendered "2h ago" string a screen
reader mangles). This document draws that line explicitly: what this API
guarantees below, and what remains entirely the client's job.

## 1. Photo alt text

**Backend guarantees:** a user can attach a free-text description to any
of their own photos (`src/services/photoAltText.service.ts`), stored as
`user_photos.alt_text`, on the photo's own row, not a side table, so it
is structurally impossible to fetch a photo without its description
sitting in the same row. `getAltTextForPhotos(ctx, photoIds)` is a batch
lookup any serializer emitting a page of photos can call once, keyed by
photo id.

**What's NOT wired in yet, and why:** this build owns
`photoAltText.service.ts` and the migration that adds the column, but not
any serializer. Today, exactly one place in the API surface returns
photos at all, `profile.service.ts`'s `fetchProfileRow`, which returns
`photoUrls: string[]` (bare URLs, no photo id, no alt text, see that
file). That is itself a pre-existing structural gap this build cannot fix
directly: an alt-text string cannot be paired with a bare URL string once
it's already been flattened away from its id. **What profile.service.ts's
owner needs to adopt**: change `photoUrls: string[]` to an array of `{
id, url, altText }` objects (id and url are already one query away, see
`fetchProfileRow`'s existing `SELECT image_url FROM user_photos ...`,
which just needs `id, alt_text` added to the column list), or at minimum
call `getAltTextForPhotos` once per request and return a parallel
`photoAltText` map/array alongside the existing `photoUrls`. Either way,
the fix is additive to that file, not a rewrite.

**Client responsibility:** render `altText` as the image's accessible
name (e.g. an `<img alt>` or platform-equivalent) with a sensible
fallback (e.g. `photo.altText.missing`'s catalog text, "No description
was provided for this photo.") when it's `null`, never render the raw
absence as a blank/silent image.

## 2. Status must never be conveyed by colour alone

**Backend guarantees:** `src/domain/i18n/statusLabels.ts` is a registry
covering every status-shaped enum this schema defines (trust level, date-
proposal status, payment-hold status, voucher status, interest status,
conversation status, notification status, photo-moderation status,
moderation-action type, appeal status, user status), 11 domains, every
value from `src/domain/types.ts`. `describeStatus(domain, status, locale)`
returns the raw status back unchanged (a client already switching on it
keeps working) plus:

- `tone`, one of `'neutral' | 'positive' | 'caution' | 'critical'`. An
  abstract semantic classification, deliberately **not** a colour name,
  the API commits to the fact ("this is a critical state"), the client
  chooses the presentation (a red badge, a bold icon, a `(critical)`
  screen-reader-only suffix). That separation is what makes this a real
  accessibility guarantee rather than just moving the colour choice
  server-side.
- `label`, a localized, unabbreviated human-readable string (task
  brief: "avoid abbreviations that a screen reader mangles", "Payment
  failed", never "Pmt failed").

**What's NOT wired in yet, and why:** every status field already exists
as a plain string enum in every serializer (that half of the rule was
already true), what's missing is calling `describeStatus` from each of
them, and none of those serializer files are in this build's file list
(`discovery`, `matches`, `payment`, `tickets`, `trust` serializers are
owned by other agents' in-flight work). **What each serializer's owner
needs to adopt**: one import, one spread, per status field it already
returns, e.g. a date-proposal serializer returning `status:
row.status` today would add `statusDetail:
describeStatus('dateProposalStatus', row.status, locale)` alongside it
(never *replacing* the raw field, clients that already switch on the
bare string must keep working). `locale` is whatever
`resolveLocale(...)` (`src/domain/i18n/locales.ts`) resolved for the
request; a serializer with no locale context yet can pass `'en'` and get
correct (English) behavior with zero risk, then adopt real negotiation
later.

**Client responsibility:** never hard-code a colour-to-status mapping
that ignores `tone`/`label`, always render at least one of them
alongside (or instead of) any colour, so removing colour from the
picture (colour-blindness, a screen reader, high-contrast mode, print)
never removes meaning.

## 3. No text embedded in generated imagery; no meaning conveyed only by an emoji or symbol

**Backend guarantees:** this codebase generates no imagery at all today
(spec §1 rule 9/10: no generative LLM text, static UI copy only, the
same principle extends to images; there is no image-generation pipeline
anywhere in `src/`), so "no text embedded in generated imagery" is
trivially, structurally true right now, not just true by convention.
Should an image-generation feature ever be added, this rule would need a
real enforcement point at that time; noted here so it isn't assumed to be
handled by default.

For "no meaning conveyed only by an emoji or symbol in copy": every
string this build's own locale catalog
(`src/domain/i18n/catalog.ts`) defines is plain, screen-reader-safe text
 `tests/unit/altText.test.ts` runs a static scan (same technique as the
existing `tests/unit/copyGuard.test.ts` spec-leak scanner) over that
file's actual string values and fails the build if an emoji-range
character appears anywhere. This is an enforced guarantee for this
build's own catalog, and a documented discipline (not yet a repo-wide
lint) for every other file that owns user-visible copy.

## 4. Structured, not pre-formatted, values

**Verified, not changed:** every timestamp this API returns is a
Postgres `timestamptz` value coming back through `pg`/Fastify's default
JSON serialization, which calls `Date.prototype.toJSON()` →
`toISOString()`, i.e. ISO-8601 UTC, automatically; there is no code
path in this codebase that pre-renders a relative string ("2h ago",
"yesterday") server-side. `tests/unit/altText.test.ts` includes a static
scan (same shape as `copyGuard.test.ts`) over every string literal under
`src/http/serializers/**` for the words a relative-time formatter would
use ("ago", "just now", "yesterday", "minutes ago", ...) and fails the
build the moment one appears, a regression guard, not a new capability,
since the property already held before this build.

Money already follows the same discipline: `amount_cents` (an integer)
and `currency` (an ISO 4217 code) are always separate JSON fields (see
`payment_holds`/`payment_ledger`/`date_proposals.escrow_amount_cents`,
`db/migrations/001_init.sql`), never a pre-formatted `"$12.34"` string.
`src/domain/i18n/format.ts#formatMoney` exists for the one place *static
copy* legitimately needs to interpolate a formatted amount into a
translated sentence (see docs/localization.md), it is never used to
replace the raw structured fields the API returns.

**Client responsibility:** format every ISO timestamp and every
`amount_cents`+`currency` pair in the viewer's own locale, time zone, and
preferred text size, this is unavoidably a client-side decision (the
same instant reads as "3:00 PM" or "15:00" depending on the viewer, and
no server-side default is correct for everyone).

## 5. Abbreviations a screen reader mangles

**Backend guarantees:** every string in `src/domain/i18n/catalog.ts` and
`src/domain/i18n/statusLabels.ts` is written in full words, "Payment
failed" not "Pmt failed", "Under review" not "Pending rvw", reviewed by
hand as part of writing this build's copy, not mechanically enforced
(unlike the emoji/relative-time scans above, there's no reliable
automated test for "is this an abbreviation a screen reader would
mangle").

**Client responsibility:** apply the same discipline to any client-only
copy this backend doesn't own (button labels, local validation messages,
etc.), this guarantee only covers strings that actually come from this
API.
