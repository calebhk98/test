/**
 * src/domain/units/ — measurement units module.
 *
 * Built in response to a real incident: distance was hardcoded in
 * kilometres throughout the codebase with no per-user unit preference and
 * nothing in the type system stopping a value in one unit from being
 * rendered, stored, or compared as another. This module is the
 * structural fix, not a one-off patch:
 *
 *   1. CANONICAL STORAGE. Exactly one unit per dimension is ever stored:
 *      - distance:  kilometres (`distance.ts` — see its file doc for why
 *        km and not metres; distance is computed, never stored, on a row)
 *      - height:    whole centimetres, integer (`height.ts`)
 *      - weight:    whole grams, integer (`weight.ts`)
 *      Height and weight are STORED profile fields, so their canonical
 *      unit is also integer-disciplined: no rounding drift across reads
 *      can ever change what a `gte`/`lte` filter comparison returns.
 *      `profile.service.ts` never stores a display unit.
 *
 *   2. CONVERSION ONLY AT THE BOUNDARY. Every function in `distance.ts`/
 *      `height.ts`/`weight.ts` that produces a display value
 *      (`toDisplayDistance`, `formatDistance`, `centimetresToFeetInches`,
 *      `formatHeight`, `roundedPounds`, `formatWeight`) takes the
 *      canonical value plus a `UnitPreference` and returns a NEW display
 *      value — it never mutates or re-stores anything. Nothing in
 *      `profile.service.ts` or `filter.service.ts` ever writes a
 *      converted value back to a row.
 *
 *   3. MIXING UNITS IS A TYPE ERROR. `Kilometres`/`Miles`,
 *      `Centimetres`, and `Grams`/`Pounds` are nominal ("branded") types
 *      (see `brand.ts`) — a raw `number` cannot be passed where one of
 *      these is expected, and a `Miles` value cannot be assigned where a
 *      `Kilometres` is expected, even though both are `number` at
 *      runtime. This is enforced by `tsc`, not by convention, and is
 *      covered by a `@ts-expect-error` compile-time proof in
 *      `tests/unit/units.test.ts` — if that mixing ever stops being a
 *      type error, `npx tsc --noEmit` fails the build.
 *
 *   4. PER-USER PREFERENCE, PRESENTATION ONLY. `preference.ts`'s
 *      `UnitPreference` (`'metric' | 'imperial'`) is the one thing that
 *      picks which conversion a boundary applies. Changing it never
 *      touches a stored `height_cm`/`weight_g` value — see
 *      `profile.service.ts`'s `unitPreference` field and
 *      `tests/unit/profileAttributes.test.ts`'s
 *      "changing unitPreference does not alter stored values" test.
 *
 * Consumers:
 *   - `profile.service.ts` (this build) stores `heightCm`/`weightG` as
 *     plain canonical numbers on the `profiles` row (branded at
 *     construction, widened back to `number` for DB/JSON boundaries —
 *     branding is compile-time only, see `brand.ts`).
 *   - `filter.service.ts` (this build) compares height/weight/distance
 *     filters against canonical values only — never a display unit.
 *   - `discovery.service.ts` (owned by another agent, NOT modified by
 *     this build) is the intended caller of `formatDistance` for card
 *     rendering — see this build's report for the exact call shape to
 *     wire in.
 */
export * from './brand.js';
export * from './preference.js';
export * from './distance.js';
export * from './height.js';
export * from './weight.js';
export * from './bodyType.js';
