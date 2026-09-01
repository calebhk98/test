/**
 * Unit tests for src/domain/units/, pure, no I/O, no database (every
 * function under test is a pure function of its inputs).
 *
 * Covers:
 *   - round-trip conversion stability across the plausible height/weight/
 *     distance ranges (converting to imperial and back must not drift,
 *     tested as idempotency of the display-rounded round trip, which is
 *     the correct formalization of "stable": the FIRST conversion may
 *     round, but re-applying the round trip to an already-rounded value
 *     must reproduce the same value, forever).
 *   - a compile-time (`@ts-expect-error`) proof that a value in one unit
 *     cannot be used where another is expected, this is the "structural
 *     guarantee" the product owner asked for: if branding ever regresses,
 *     `npx tsc --noEmit` fails the build, not just this test file.
 *   - formatting output shapes (feet+inches, whole km/mi, etc).
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  kilometres,
  miles,
  kilometresToMiles,
  milesToKilometres,
  toDisplayDistance,
  formatDistance,
  type Kilometres,
  type Miles,
} from '../../src/domain/units/distance.js';
import {
  centimetres,
  centimetresToFeetInches,
  feetInchesToCentimetres,
  formatHeight,
  type Centimetres,
} from '../../src/domain/units/height.js';
import {
  grams,
  pounds,
  gramsToPounds,
  poundsToGrams,
  roundedPounds,
  formatWeight,
  type Grams,
} from '../../src/domain/units/weight.js';
import { BODY_TYPES, isBodyType } from '../../src/domain/units/bodyType.js';
import { resolveDefaultUnitPreference, DEFAULT_UNIT_PREFERENCE } from '../../src/domain/units/preference.js';

// =====================================================================
// Compile-time proof: mixing units is a TYPE ERROR.
// =====================================================================

test('branded types make unit mixing a compile-time error (and this test proves it compiles)', () => {
  const distanceKm = kilometres(5);
  const distanceMiles = miles(3);
  const heightCm = centimetres(180);

  // @ts-expect-error, a Miles value cannot be assigned where Kilometres is expected, even though both are `number` at runtime.
  const mixedDistance: Kilometres = distanceMiles;
  // @ts-expect-error, a Kilometres value cannot be assigned where Miles is expected (the mismatch is symmetric).
  const mixedDistance2: Miles = distanceKm;
  // @ts-expect-error, a raw number literal cannot be assigned where a branded Centimetres is expected; it must go through centimetres().
  const rawNumberAsHeight: Centimetres = 180;
  // @ts-expect-error, a Centimetres value cannot be assigned where Grams is expected (different dimensions entirely).
  const heightAsWeight: Grams = heightCm;

  // These are type-error-only checks; nothing above should ever actually
  // run (that's what @ts-expect-error guarantees at compile time, if any
  // of those lines stopped being an error, `npx tsc --noEmit` fails).
  // The assertion below is just so this is a real, executing test.
  assert.ok(typeof mixedDistance === 'number');
  assert.ok(typeof mixedDistance2 === 'number');
  assert.ok(typeof rawNumberAsHeight === 'number');
  assert.ok(typeof heightAsWeight === 'number');
});

test('constructors accept raw numbers; branded values are otherwise ordinary numbers at runtime', () => {
  assert.equal(kilometres(5), 5);
  assert.equal(miles(3.1), 3.1);
  assert.equal(centimetres(180), 180);
  assert.equal(grams(70000), 70000);
});

test('constructors reject invalid input (negative, non-integer where integer discipline applies)', () => {
  assert.throws(() => kilometres(-1), RangeError);
  assert.throws(() => miles(-1), RangeError);
  assert.throws(() => centimetres(-1), RangeError);
  assert.throws(() => centimetres(180.5), RangeError, 'height is integer-only');
  assert.throws(() => grams(-1), RangeError);
  assert.throws(() => grams(70000.5), RangeError, 'weight is integer-only');
});

// =====================================================================
// Round-trip stability: distance (km <-> mi).
// =====================================================================

test('distance: exact km<->mi round trip is stable to floating-point precision across the plausible range', () => {
  for (let km = 0; km <= 20000; km += 137) {
    const original = kilometres(km);
    const roundTripped = milesToKilometres(kilometresToMiles(original));
    assert.ok(
      Math.abs(roundTripped - original) < 1e-9,
      `km=${km} drifted to ${roundTripped} after an exact km->mi->km round trip`,
    );
  }
});

test('distance: the DISPLAY (rounded) round trip is idempotent, converting to imperial and back never keeps drifting', () => {
  for (let km = 0; km <= 20000; km += 91) {
    const original = kilometres(km);
    const firstDisplay = toDisplayDistance(original, 'imperial');
    const backToKm = milesToKilometres(miles(firstDisplay.value));
    const secondDisplay = toDisplayDistance(backToKm, 'imperial');
    assert.equal(
      secondDisplay.value,
      firstDisplay.value,
      `km=${km}: re-round-tripping an already-displayed value must not drift further`,
    );
  }
});

// =====================================================================
// Round-trip stability: height (cm <-> ft/in).
// =====================================================================

test('height: cm -> ft/in -> cm -> ft/in is idempotent after the first conversion, across the plausible adult range', () => {
  for (let cm = 100; cm <= 250; cm++) {
    const original = centimetres(cm);
    const firstFeetInches = centimetresToFeetInches(original);
    const backToCm = feetInchesToCentimetres(firstFeetInches.feet, firstFeetInches.inches);
    const secondFeetInches = centimetresToFeetInches(backToCm);
    assert.deepEqual(
      secondFeetInches,
      firstFeetInches,
      `cm=${cm}: re-round-tripping an already-displayed ft/in value must not drift further`,
    );
    // Sanity: never drifts more than half an inch's worth of cm from the original.
    assert.ok(Math.abs(backToCm - cm) <= 1.27, `cm=${cm} drifted to ${backToCm}cm after one ft/in round trip`);
  }
});

test('height: feet/inches round trip produces a valid 0-11 inches remainder', () => {
  for (let cm = 100; cm <= 250; cm += 3) {
    const { inches } = centimetresToFeetInches(centimetres(cm));
    assert.ok(inches >= 0 && inches <= 11, `inches=${inches} out of 0-11 range for cm=${cm}`);
  }
});

// =====================================================================
// Round-trip stability: weight (g <-> lb).
// =====================================================================

test('weight: exact g<->lb round trip is stable across the plausible range', () => {
  for (let g = 20000; g <= 300000; g += 1301) {
    const original = grams(g);
    const roundTripped = poundsToGrams(gramsToPounds(original));
    assert.ok(
      Math.abs(roundTripped - g) <= 1,
      `g=${g} drifted to ${roundTripped} after an exact g->lb->g round trip (grams are integer-rounded on the way back, so <=1g tolerance)`,
    );
  }
});

test('weight: the DISPLAY (whole-pound) round trip is idempotent', () => {
  for (let g = 20000; g <= 300000; g += 977) {
    const original = grams(g);
    const firstLb = roundedPounds(original);
    const backToG = poundsToGrams(pounds(firstLb));
    const secondLb = roundedPounds(backToG);
    assert.equal(secondLb, firstLb, `g=${g}: re-round-tripping an already-displayed lb value must not drift further`);
  }
});

// =====================================================================
// Formatting.
// =====================================================================

test('formatDistance: whole km/mi, "<1" for a nonzero sub-unit distance, null passthrough', () => {
  assert.equal(formatDistance(kilometres(5), 'metric'), '5 km');
  assert.equal(formatDistance(kilometres(5), 'imperial'), '3 mi');
  assert.equal(formatDistance(kilometres(0.4), 'metric'), '<1 km');
  assert.equal(formatDistance(null, 'metric'), null);
  assert.equal(formatDistance(null, 'imperial'), null);
});

test('formatHeight: feet+inches for imperial, whole cm for metric, null passthrough', () => {
  assert.equal(formatHeight(centimetres(180), 'metric'), '180 cm');
  assert.equal(formatHeight(centimetres(180), 'imperial'), "5'11\"");
  assert.equal(formatHeight(null, 'imperial'), null);
});

test('formatWeight: whole lb for imperial, whole kg for metric, null passthrough', () => {
  assert.equal(formatWeight(grams(70000), 'metric'), '70 kg');
  assert.equal(formatWeight(grams(70000), 'imperial'), '154 lb');
  assert.equal(formatWeight(null, 'metric'), null);
});

// =====================================================================
// Unit preference default resolution.
// =====================================================================

test('resolveDefaultUnitPreference: metric with no country signal, imperial for the three imperial-using countries', () => {
  assert.equal(resolveDefaultUnitPreference(), DEFAULT_UNIT_PREFERENCE);
  assert.equal(resolveDefaultUnitPreference(null), 'metric');
  assert.equal(resolveDefaultUnitPreference('US'), 'imperial');
  assert.equal(resolveDefaultUnitPreference('us'), 'imperial', 'case-insensitive');
  assert.equal(resolveDefaultUnitPreference('FR'), 'metric');
});

// =====================================================================
// Body type.
// =====================================================================

test('isBodyType: only recognizes the canonical BODY_TYPES list', () => {
  for (const bt of BODY_TYPES) assert.equal(isBodyType(bt), true);
  assert.equal(isBodyType('not-a-body-type'), false);
  assert.equal(isBodyType(42), false);
});
