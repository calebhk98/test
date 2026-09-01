import type { ChoiceOption, ImportanceLevel, QuestionPresentation, QuestionTypeDefinition, SingleChoiceDefinition } from './types.js';

/**
 * Presentation collapse for binary preferences.
 *
 * Product refinement on top of the base value+importance model: a user
 * must never be shown two abstract sliders for a plain yes/no-shaped
 * preference. For a `single_choice` question with exactly two options,
 * the value axis (which option) and the importance axis (how much it
 * matters) collapse into ONE ordered five-position control:
 *
 *   0: Deal breaker: <option A>
 *   1: Prefer <option A>
 *   2: Don't care
 *   3: Prefer <option B>
 *   4: Deal breaker: <option B>
 *
 * `scale`, `frequency`, and `multi_choice` questions (and `single_choice`
 * questions with more than two options) are NOT ladder-eligible, their
 * value dimension has more than two directions, so there is no single
 * "which side, how far" axis to collapse onto. Those keep the separate
 * value + importance controls (`QuestionPresentation = 'value_importance'`).
 *
 * The ladder is purely a PRESENTATION convenience: `ladderPositionToPreference`
 * / `preferenceToLadderPosition` are lossless, round-tripping bijections
 * onto the exact same (preferenceValue, importance) pair the two-control
 * form would produce, scoring.ts never knows or cares which presentation
 * produced its inputs (see questionScoring.test.ts "ladder vs. two-control
 * presentations score identically").
 */

export type LadderPosition = 0 | 1 | 2 | 3 | 4;

export const LADDER_POSITIONS: readonly LadderPosition[] = [0, 1, 2, 3, 4];

/** A `single_choice` question is ladder-eligible iff it has exactly two options. */
export function isLadderEligible(typeDef: QuestionTypeDefinition): typeDef is SingleChoiceDefinition {
  return typeDef.type === 'single_choice' && typeDef.options.length === 2;
}

/** The single server-computed source of truth for `QuestionDefinition.presentation`, never inferred client-side (see types.ts `QuestionPresentation`). */
export function presentationFor(typeDef: QuestionTypeDefinition): QuestionPresentation {
  return isLadderEligible(typeDef) ? 'ladder' : 'value_importance';
}

function requireLadderEligible(def: SingleChoiceDefinition): [ChoiceOption, ChoiceOption] {
  if (def.options.length !== 2) {
    throw new Error(`Ladder presentation requires exactly two options, got ${def.options.length}`);
  }
  return [def.options[0]!, def.options[1]!];
}

/**
 * User-facing ladder copy, built from the question's own option labels,
 * plain language, no bare numbers, no section references. Index matches
 * `LadderPosition` (0-4).
 */
export function ladderLabels(def: SingleChoiceDefinition): [string, string, string, string, string] {
  const [a, b] = requireLadderEligible(def);
  return [
    `Deal breaker: ${a.label}`,
    `Prefer ${a.label}`,
    `Don't care`,
    `Prefer ${b.label}`,
    `Deal breaker: ${b.label}`,
  ];
}

export interface LadderPreference {
  preferenceValue: string[]; // acceptable option-key set, same shape single_choice preferences always use
  importance: ImportanceLevel;
}

/**
 * Ladder position -> (value, importance) pair. Total over `LadderPosition`
 * (every position produces a result).
 *
 *   - Both deal-breaker ends (0, 4) map to importance `deal_breaker`, with
 *     the value narrowed to whichever side was picked, the position
 *     determines WHICH option is required, not just that one is.
 *   - `Don't care` (2) maps to importance `irrelevant`; both options are
 *     recorded as acceptable (matches "irrelevant contributes nothing",
 *     the value is moot once importance is irrelevant, but a concrete,
 *     total value is still stored rather than a null so the shape stays
 *     uniform with every other single_choice preference).
 *   - The two "Prefer" positions (1, 3) map to importance `important`,
 *     a real, moderate preference; not a mild "slight" nudge and not a
 *     hard exclusion.
 */
export function ladderPositionToPreference(def: SingleChoiceDefinition, position: LadderPosition): LadderPreference {
  const [a, b] = requireLadderEligible(def);
  switch (position) {
    case 0:
      return { preferenceValue: [a.key], importance: 'deal_breaker' };
    case 1:
      return { preferenceValue: [a.key], importance: 'important' };
    case 2:
      return { preferenceValue: [a.key, b.key], importance: 'irrelevant' };
    case 3:
      return { preferenceValue: [b.key], importance: 'important' };
    case 4:
      return { preferenceValue: [b.key], importance: 'deal_breaker' };
  }
}

/**
 * (value, importance) -> ladder position. The inverse of
 * `ladderPositionToPreference`; returns `null` for a pair that has no
 * ladder representation (e.g. importance `slight`/`critical`, which the
 * ladder never produces and the two-control form must be used for
 * instead, this is expected and not an error, just "not
 * ladder-representable").
 */
export function preferenceToLadderPosition(
  def: SingleChoiceDefinition,
  preferenceValue: string[],
  importance: ImportanceLevel,
): LadderPosition | null {
  const [a, b] = requireLadderEligible(def);
  const set = new Set(preferenceValue);

  if (importance === 'irrelevant') return 2;

  if (importance === 'deal_breaker') {
    if (set.size === 1 && set.has(a.key)) return 0;
    if (set.size === 1 && set.has(b.key)) return 4;
    return null;
  }

  if (importance === 'important') {
    if (set.size === 1 && set.has(a.key)) return 1;
    if (set.size === 1 && set.has(b.key)) return 3;
    return null;
  }

  return null; // 'slight' / 'critical', not producible by the ladder
}
