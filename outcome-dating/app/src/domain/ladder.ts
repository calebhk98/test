/**
 * Client copy of the backend's ladder presentation math
 * (domain/questions/ladder.ts). The server tells us a question's
 * `presentation` is `'ladder'`, it never guesses that itself (see
 * QuestionCardView doc), but it does not send label strings for the
 * five positions, those are built from the question's own two option
 * labels, so this mirrors the server's `ladderPositionToPreference` /
 * `ladderLabels` exactly (same position -> (value, importance) mapping)
 * to stay presentation-only, never a second source of truth for
 * WHETHER a question is ladder-eligible.
 */
import type { ChoiceOption, ImportanceLevel, SingleChoiceDefinition } from '../api/types';

export type LadderPosition = 0 | 1 | 2 | 3 | 4;
export const LADDER_POSITIONS: readonly LadderPosition[] = [0, 1, 2, 3, 4];

export interface LadderPreference {
  preferenceValue: string[];
  importance: ImportanceLevel;
}

function requireTwoOptions(def: SingleChoiceDefinition): [ChoiceOption, ChoiceOption] {
  const [a, b] = def.options;
  if (!a || !b || def.options.length !== 2) {
    throw new Error(`Ladder control requires exactly two options, got ${def.options.length}`);
  }
  return [a, b];
}

export function ladderLabels(def: SingleChoiceDefinition): [string, string, string, string, string] {
  const [a, b] = requireTwoOptions(def);
  return [`Deal breaker: ${a.label}`, `Prefer ${a.label}`, "Don't care", `Prefer ${b.label}`, `Deal breaker: ${b.label}`];
}

export function ladderPositionToPreference(def: SingleChoiceDefinition, position: LadderPosition): LadderPreference {
  const [a, b] = requireTwoOptions(def);
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
