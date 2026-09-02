/**
 * Pure state + builder for one in-progress question answer. Kept free
 * of React and the API client so the "does this control produce the
 * right wire payload for this type/presentation" logic is unit
 * testable without mounting a screen.
 */
import type { ImportanceLevel, PutQuestionAnswerInput, QuestionCardView } from '../api/types';
import { ladderPositionToPreference, type LadderPosition } from './ladder';

export type QuestionDraft =
  | { kind: 'ladder'; selfValue: string | null; position: LadderPosition | null }
  | { kind: 'scale'; selfValue: number | null; preferenceValue: number | null; importance: ImportanceLevel | null }
  | { kind: 'single_choice'; selfValue: string | null; preferenceValue: string[]; importance: ImportanceLevel | null }
  | { kind: 'multi_choice'; selfValue: string[]; preferenceValue: string[]; importance: ImportanceLevel | null }
  | { kind: 'frequency'; selfValue: string | null; preferenceValue: string | null; importance: ImportanceLevel | null };

/** Builds the empty draft for a question, honouring `presentation` exactly as the server sent it, never inferring ladder-vs-two-control from `type`/option count client-side. */
export function emptyDraftFor(question: QuestionCardView): QuestionDraft {
  if (question.presentation === 'ladder') {
    return { kind: 'ladder', selfValue: null, position: null };
  }
  switch (question.typeDef.type) {
    case 'scale':
      return { kind: 'scale', selfValue: null, preferenceValue: null, importance: null };
    case 'single_choice':
      return { kind: 'single_choice', selfValue: null, preferenceValue: [], importance: null };
    case 'multi_choice':
      return { kind: 'multi_choice', selfValue: [], preferenceValue: [], importance: null };
    case 'frequency':
      return { kind: 'frequency', selfValue: null, preferenceValue: null, importance: null };
  }
}

/** Whether the draft has everything required to submit as `answered`. Skip / prefer-not-to-say never need this, they are always available regardless of draft completeness. */
export function isDraftComplete(draft: QuestionDraft): boolean {
  switch (draft.kind) {
    case 'ladder':
      return draft.selfValue !== null && draft.position !== null;
    case 'scale':
      return draft.selfValue !== null && draft.preferenceValue !== null && draft.importance !== null;
    case 'single_choice':
      return draft.selfValue !== null && draft.preferenceValue.length > 0 && draft.importance !== null;
    case 'multi_choice':
      return draft.selfValue.length > 0 && draft.preferenceValue.length > 0 && draft.importance !== null;
    case 'frequency':
      return draft.selfValue !== null && draft.preferenceValue !== null && draft.importance !== null;
  }
}

/** Builds the exact `PUT /me/answers` payload for a complete draft. Returns `null` if the draft is not yet complete, callers should gate the submit action on `isDraftComplete` first rather than relying on this. */
export function buildAnsweredPayload(question: QuestionCardView, draft: QuestionDraft): PutQuestionAnswerInput | null {
  if (!isDraftComplete(draft)) return null;

  if (draft.kind === 'ladder') {
    if (question.typeDef.type !== 'single_choice') return null;
    const position = draft.position as LadderPosition;
    // Client never re-derives (preferenceValue, importance) to send over the wire, ladderPosition IS the payload;
    // this call only exists so the draft stays internally consistent for display before submit.
    ladderPositionToPreference(question.typeDef, position);
    return { slug: question.slug, status: 'answered', selfValue: draft.selfValue, ladderPosition: position };
  }

  if (draft.kind === 'scale' && draft.selfValue !== null && draft.preferenceValue !== null && draft.importance) {
    return {
      slug: question.slug,
      status: 'answered',
      selfValue: draft.selfValue,
      preferenceValue: draft.preferenceValue,
      importance: draft.importance,
    };
  }

  if (draft.kind === 'single_choice' && draft.selfValue !== null && draft.importance) {
    return {
      slug: question.slug,
      status: 'answered',
      selfValue: draft.selfValue,
      preferenceValue: draft.preferenceValue,
      importance: draft.importance,
    };
  }

  if (draft.kind === 'multi_choice' && draft.importance) {
    return {
      slug: question.slug,
      status: 'answered',
      selfValue: draft.selfValue,
      preferenceValue: draft.preferenceValue,
      importance: draft.importance,
    };
  }

  if (draft.kind === 'frequency' && draft.selfValue !== null && draft.preferenceValue !== null && draft.importance) {
    return {
      slug: question.slug,
      status: 'answered',
      selfValue: draft.selfValue,
      preferenceValue: draft.preferenceValue,
      importance: draft.importance,
    };
  }

  return null;
}

export function buildSkipPayload(question: QuestionCardView): PutQuestionAnswerInput {
  return { slug: question.slug, status: 'skipped' };
}

export function buildPreferNotToSayPayload(question: QuestionCardView): PutQuestionAnswerInput {
  return { slug: question.slug, status: 'prefer_not_to_say' };
}
