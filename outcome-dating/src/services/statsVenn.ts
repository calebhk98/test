/**
 * src/services/statsVenn.ts: turns the reality dashboard's three counts
 * (matches this user's filters, whose filters this user matches, the
 * mutual pool) into a proper two-set Venn: set sizes, the intersection,
 * and what sits outside each set. Also renders a small, self-contained,
 * accessible SVG of that Venn, since this project has no client to draw
 * one itself.
 *
 * Deliberately has ZERO dependency on stats.service.ts (no import of it,
 * no import of its SuppressibleCount type) even though the two describe
 * the same shape. This keeps the module a pure, independently-testable
 * unit (see tests/unit/statsVenn.test.ts) and avoids a circular import,
 * since stats.service.ts is the one that imports THIS file, not the other
 * way around. `computePoolVenn` takes suppression as an injected function
 * rather than importing stats.service.ts#suppressSmallCohort directly, so
 * the one small-cohort rule still has exactly one implementation, just
 * not one this file needs to know the name of.
 *
 * PRIVACY: every number here is a count of a population (or a population
 * minus a subset), never a list, never an id. `computePoolVenn` runs the
 * SAME suppression rule over every one of the five derived quantities
 * (both set totals, the intersection, and both "outside" counts) rather
 * than deriving some of them from an already-suppressed value: a
 * suppressed set total does not silently make a derived count look like
 * an honest zero, it stays its own explicit "too few people to show"
 * result.
 */

export interface SuppressibleCount {
  value: number | null;
  suppressed: boolean;
}

export interface PoolVennCounts {
  /** X: other people who pass this user's own filters. */
  matchesMyFilters: number;
  /** Y: other people this user would pass THEIR filters. */
  whoseFiltersIMatch: number;
  /** Z: the mutual pool (both directions, plus capacity/moderation gates, see discovery.service.ts#getRealityDashboard). Always <= min(X, Y). */
  mutualMatchPool: number;
}

export interface PoolVennRegion {
  label: string;
  count: SuppressibleCount;
}

export interface PoolVennData {
  setA: PoolVennRegion; // matchesMyFilters (X)
  setB: PoolVennRegion; // whoseFiltersIMatch (Y)
  intersection: PoolVennRegion; // mutualMatchPool (Z)
  onlyA: PoolVennRegion; // X - Z: pass my filters, but not the full mutual pool
  onlyB: PoolVennRegion; // Y - Z: I pass their filters, but not the full mutual pool
}

const SET_A_LABEL = 'People who match your filters';
const SET_B_LABEL = 'People whose filters you match';
const INTERSECTION_LABEL = 'Mutual match pool';
const ONLY_A_LABEL = 'Match your filters only';
const ONLY_B_LABEL = 'You match their filters only';

/** Pure: builds the full Venn shape from the three reality-dashboard counts, applying `suppress` (normally stats.service.ts#suppressSmallCohort) to every one of the five derived quantities independently. */
export function computePoolVenn(counts: PoolVennCounts, suppress: (n: number) => SuppressibleCount): PoolVennData {
  const onlyA = Math.max(0, counts.matchesMyFilters - counts.mutualMatchPool);
  const onlyB = Math.max(0, counts.whoseFiltersIMatch - counts.mutualMatchPool);
  return {
    setA: { label: SET_A_LABEL, count: suppress(counts.matchesMyFilters) },
    setB: { label: SET_B_LABEL, count: suppress(counts.whoseFiltersIMatch) },
    intersection: { label: INTERSECTION_LABEL, count: suppress(counts.mutualMatchPool) },
    onlyA: { label: ONLY_A_LABEL, count: suppress(onlyA) },
    onlyB: { label: ONLY_B_LABEL, count: suppress(onlyB) },
  };
}

const SUPPRESSED_TEXT = 'too few nearby people to show';

function regionText(region: PoolVennRegion): string {
  return region.count.suppressed ? SUPPRESSED_TEXT : String(region.count.value);
}

function regionSentence(region: PoolVennRegion): string {
  return region.count.suppressed
    ? `${region.label}: too few nearby people to show without risking identifying someone.`
    : `${region.label}: ${region.count.value}.`;
}

/** Escapes the handful of characters that matter inside SVG text content or attribute values. Every string this function ever receives is this module's own fixed label text, never third-party input, but escaping unconditionally costs nothing and removes the need to ever re-audit that assumption later. */
function escapeXml(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

export interface VennSvgOptions {
  width?: number;
  height?: number;
}

const DEFAULT_WIDTH = 480;
const DEFAULT_HEIGHT = 300;

/**
 * A small, self-contained, dependency-free SVG rendering `data` as a
 * two-circle Venn diagram: sized sensibly (default 480x300, legible at
 * that size without scaling), with every number that appears as pixels
 * ALSO present as a `<title>`/`<desc>` text alternative in the same
 * document (see docs/accessibility.md's "no text embedded in generated
 * imagery without the same values as data" principle: the caller
 * additionally gets `PoolVennData` as plain JSON alongside this image,
 * so the numbers are never trapped inside pixels; this SVG's own
 * `<desc>` is the screen-reader path to the same numbers, not the only
 * one). No charting library, just five circles and text elements, hand-laid-out.
 */
export function renderPoolVennSvg(data: PoolVennData, opts?: VennSvgOptions): string {
  const width = opts?.width ?? DEFAULT_WIDTH;
  const height = opts?.height ?? DEFAULT_HEIGHT;

  const cy = Math.round(height * 0.56);
  const r = Math.round(Math.min(width * 0.24, height * 0.4));
  const cxA = Math.round(width * 0.38);
  const cxB = Math.round(width * 0.62);
  const labelY = Math.round(cy - r - 14);
  const onlyAX = Math.round(cxA - r * 0.42);
  const onlyBX = Math.round(cxB + r * 0.42);
  const midX = Math.round((cxA + cxB) / 2);

  const title = 'Your discovery pool, as a Venn diagram';
  const desc = [
    regionSentence(data.setA),
    regionSentence(data.setB),
    regionSentence(data.onlyA),
    regionSentence(data.onlyB),
    regionSentence(data.intersection),
  ].join(' ');

  return [
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}" role="img" aria-labelledby="venn-title venn-desc">`,
    `<title id="venn-title">${escapeXml(title)}</title>`,
    `<desc id="venn-desc">${escapeXml(desc)}</desc>`,
    `<rect x="0" y="0" width="${width}" height="${height}" fill="none" />`,
    `<circle cx="${cxA}" cy="${cy}" r="${r}" fill="#6f8bd6" fill-opacity="0.45" stroke="#3a52a0" stroke-width="2" />`,
    `<circle cx="${cxB}" cy="${cy}" r="${r}" fill="#d68f6f" fill-opacity="0.45" stroke="#a0523a" stroke-width="2" />`,
    `<text x="${cxA}" y="${labelY}" text-anchor="middle" font-size="14" font-family="sans-serif" fill="currentColor">${escapeXml(data.setA.label)}</text>`,
    `<text x="${cxB}" y="${labelY}" text-anchor="middle" font-size="14" font-family="sans-serif" fill="currentColor">${escapeXml(data.setB.label)}</text>`,
    `<text x="${onlyAX}" y="${cy}" text-anchor="middle" font-size="20" font-weight="bold" font-family="sans-serif" fill="#1a1a1a">${escapeXml(regionText(data.onlyA))}</text>`,
    `<text x="${midX}" y="${cy}" text-anchor="middle" font-size="20" font-weight="bold" font-family="sans-serif" fill="#1a1a1a">${escapeXml(regionText(data.intersection))}</text>`,
    `<text x="${onlyBX}" y="${cy}" text-anchor="middle" font-size="20" font-weight="bold" font-family="sans-serif" fill="#1a1a1a">${escapeXml(regionText(data.onlyB))}</text>`,
    `<text x="${midX}" y="${cy + r + 26}" text-anchor="middle" font-size="13" font-family="sans-serif" fill="currentColor">${escapeXml(data.intersection.label)}</text>`,
    `</svg>`,
  ].join('');
}
