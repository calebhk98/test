/**
 * Unit tests for src/services/statsVenn.ts.
 *
 * Pure logic, no database (the module itself has zero I/O), so this file
 * needs no `odate_stats2_<suite>` database of its own -- listed here only
 * because the task brief names it as an expected new test file for this
 * build.
 *
 * Coverage:
 *  - the five-region shape (set sizes, intersection, "outside each") is
 *    computed correctly from the three reality-dashboard counts
 *  - small-cohort suppression is applied to EVERY derived quantity
 *    independently, not just the three inputs
 *  - the SVG carries the same numbers as the data, plus a text
 *    alternative (title/desc) a screen reader can read, and never leaks a
 *    suppressed number through either channel
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { computePoolVenn, renderPoolVennSvg, type SuppressibleCount } from '../../src/services/statsVenn.js';

const MIN_SUPPRESSIBLE_COHORT = 5;

function suppress(n: number): SuppressibleCount {
  if (n < MIN_SUPPRESSIBLE_COHORT) return { value: null, suppressed: true };
  return { value: n, suppressed: false };
}

test('computePoolVenn: derives set sizes, intersection, and outside-each counts from the three reality-dashboard numbers', () => {
  const data = computePoolVenn({ matchesMyFilters: 42, whoseFiltersIMatch: 30, mutualMatchPool: 20 }, suppress);

  assert.equal(data.setA.count.value, 42);
  assert.equal(data.setB.count.value, 30);
  assert.equal(data.intersection.count.value, 20);
  assert.equal(data.onlyA.count.value, 22); // 42 - 20
  assert.equal(data.onlyB.count.value, 10); // 30 - 20
  for (const region of [data.setA, data.setB, data.intersection, data.onlyA, data.onlyB]) {
    assert.equal(region.count.suppressed, false);
    assert.ok(region.label.length > 0);
  }
});

test('computePoolVenn: never produces a negative "outside" count even if inputs are inconsistent', () => {
  // mutualMatchPool larger than one of the set sizes should not happen in
  // practice (Z is always <= min(X, Y) by construction upstream), but this
  // function must still degrade safely rather than surface a negative
  // count if it ever did. Uses an identity "suppress" (never withholds)
  // so the raw derived value is directly observable here, distinct from
  // the suppression behaviour the other tests in this file cover.
  const identity = (n: number): SuppressibleCount => ({ value: n, suppressed: false });
  const data = computePoolVenn({ matchesMyFilters: 5, whoseFiltersIMatch: 5, mutualMatchPool: 9 }, identity);
  assert.equal(data.onlyA.count.value, 0);
  assert.equal(data.onlyB.count.value, 0);
});

test('computePoolVenn: suppresses every derived quantity independently, not just the raw inputs', () => {
  // setA and the intersection both clear the threshold (9 and 5), but the
  // DIFFERENCE (onlyA = 9 - 5 = 4) does not -- onlyA must be suppressed
  // even though setA and intersection are not.
  const data = computePoolVenn({ matchesMyFilters: 9, whoseFiltersIMatch: 6, mutualMatchPool: 5 }, suppress);

  assert.equal(data.setA.count.suppressed, false);
  assert.equal(data.setA.count.value, 9);
  assert.equal(data.intersection.count.suppressed, false);
  assert.equal(data.intersection.count.value, 5);
  assert.equal(data.onlyA.count.suppressed, true, 'onlyA (9 - 5 = 4) is below the suppression threshold');
  assert.equal(data.onlyA.count.value, null);
});

test('computePoolVenn: an all-suppressed pool suppresses every region', () => {
  const data = computePoolVenn({ matchesMyFilters: 2, whoseFiltersIMatch: 1, mutualMatchPool: 1 }, suppress);
  for (const region of [data.setA, data.setB, data.intersection, data.onlyA, data.onlyB]) {
    assert.equal(region.count.suppressed, true);
    assert.equal(region.count.value, null);
  }
});

test('renderPoolVennSvg: every visible number also appears in the JSON data (the SVG is not the only source of truth)', () => {
  const data = computePoolVenn({ matchesMyFilters: 42, whoseFiltersIMatch: 30, mutualMatchPool: 20 }, suppress);
  const svg = renderPoolVennSvg(data);

  assert.ok(svg.startsWith('<svg'));
  assert.ok(svg.includes('</svg>'));
  // Region-exclusive numbers rendered as pixels...
  assert.ok(svg.includes('>22<'), 'onlyA (22) should be legible in the image');
  assert.ok(svg.includes('>20<'), 'intersection (20) should be legible in the image');
  assert.ok(svg.includes('>10<'), 'onlyB (10) should be legible in the image');
  // ...and the SAME numbers must independently be present in `data`
  // (already asserted by the earlier test), so a consumer never has to
  // parse the image to get them.
  assert.equal(data.onlyA.count.value, 22);
  assert.equal(data.intersection.count.value, 20);
  assert.equal(data.onlyB.count.value, 10);
});

test('renderPoolVennSvg: has a title and description a screen reader can read, referencing every region by name', () => {
  const data = computePoolVenn({ matchesMyFilters: 42, whoseFiltersIMatch: 30, mutualMatchPool: 20 }, suppress);
  const svg = renderPoolVennSvg(data);

  assert.match(svg, /role="img"/);
  assert.match(svg, /aria-labelledby="venn-title venn-desc"/);
  assert.match(svg, /<title id="venn-title">[^<]+<\/title>/);
  assert.match(svg, /<desc id="venn-desc">[^<]+<\/desc>/);

  const descMatch = svg.match(/<desc id="venn-desc">([^<]+)<\/desc>/);
  assert.ok(descMatch);
  const desc = descMatch![1]!;
  assert.ok(desc.includes('42'));
  assert.ok(desc.includes('30'));
  assert.ok(desc.includes('20'));
  assert.ok(desc.includes('22'));
  assert.ok(desc.includes('10'));
  assert.ok(desc.length > 40, 'the description should be a real sentence, not a placeholder');
});

test('renderPoolVennSvg: a suppressed region never leaks its number through pixels OR the text alternative', () => {
  const data = computePoolVenn({ matchesMyFilters: 6, whoseFiltersIMatch: 4, mutualMatchPool: 4 }, suppress);
  assert.equal(data.onlyA.count.suppressed, true);

  const svg = renderPoolVennSvg(data);
  assert.ok(!svg.includes('>2<'), 'the suppressed onlyA value (2) must never appear as a visible number');
  assert.ok(svg.toLowerCase().includes('too few nearby people'), 'the suppressed region should say why, not show a number');

  const descMatch = svg.match(/<desc id="venn-desc">([^<]+)<\/desc>/);
  assert.ok(descMatch);
  assert.ok(!descMatch![1]!.includes(' 2.'), 'the raw suppressed count must not appear in the description either');
});

test('renderPoolVennSvg: respects custom width/height and stays a well-formed, self-contained document', () => {
  const data = computePoolVenn({ matchesMyFilters: 42, whoseFiltersIMatch: 30, mutualMatchPool: 20 }, suppress);
  const svg = renderPoolVennSvg(data, { width: 600, height: 360 });

  assert.ok(svg.includes('width="600"'));
  assert.ok(svg.includes('height="360"'));
  assert.ok(svg.includes('viewBox="0 0 600 360"'));
  assert.equal((svg.match(/<circle/g) ?? []).length, 2, 'a two-set Venn has exactly two circles');
  // No external asset references of any kind -- fully self-contained
  // (the xmlns declaration's URI is not a network fetch, so it is exempt).
  assert.ok(!svg.includes('<image'));
  assert.ok(!svg.includes('xlink:href'));
  assert.ok(!/\ssrc=/.test(svg));
});
