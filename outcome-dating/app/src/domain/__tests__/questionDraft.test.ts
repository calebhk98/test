import { buildAnsweredPayload, buildPreferNotToSayPayload, buildSkipPayload, emptyDraftFor, isDraftComplete } from '../questionDraft';
import type { FrequencyDefinition, MultiChoiceDefinition, QuestionCardView, ScaleDefinition, SingleChoiceDefinition } from '../../api/types';

function question(overrides: Partial<QuestionCardView>): QuestionCardView {
  return {
    id: 'q1',
    slug: 'test-question',
    version: 1,
    category: 'lifestyle',
    subcategory: null,
    tags: [],
    questionText: 'Test question?',
    sensitive: false,
    typeDef: { type: 'scale', min: 1, max: 5, minLabel: 'Never', maxLabel: 'Always', midLabel: 'Sometimes' },
    presentation: 'value_importance',
    ...overrides,
  };
}

describe('a scale question (value_importance presentation)', () => {
  const scaleDef: ScaleDefinition = { type: 'scale', min: 1, max: 5, minLabel: 'Never', maxLabel: 'Always', midLabel: 'Sometimes' };
  const q = question({ typeDef: scaleDef, presentation: 'value_importance' });

  it('starts incomplete', () => {
    expect(isDraftComplete(emptyDraftFor(q))).toBe(false);
    expect(buildAnsweredPayload(q, emptyDraftFor(q))).toBeNull();
  });

  it('requires selfValue, preferenceValue, AND importance before it is complete', () => {
    let draft = emptyDraftFor(q);
    if (draft.kind !== 'scale') throw new Error('expected scale draft');
    draft = { ...draft, selfValue: 3 };
    expect(isDraftComplete(draft)).toBe(false);
    draft = { ...draft, preferenceValue: 4 };
    expect(isDraftComplete(draft)).toBe(false);
    draft = { ...draft, importance: 'important' };
    expect(isDraftComplete(draft)).toBe(true);
  });

  it('produces the exact wire payload once complete, never a ladderPosition', () => {
    const draft = { kind: 'scale' as const, selfValue: 3, preferenceValue: 4, importance: 'important' as const };
    const payload = buildAnsweredPayload(q, draft);
    expect(payload).toEqual({
      slug: 'test-question',
      status: 'answered',
      selfValue: 3,
      preferenceValue: 4,
      importance: 'important',
    });
  });
});

describe('a two-option single_choice question uses the ladder presentation', () => {
  const ladderDef: SingleChoiceDefinition = {
    type: 'single_choice',
    options: [
      { key: 'yes', label: 'Wants kids' },
      { key: 'no', label: 'Does not want kids' },
    ],
  };
  const q = question({ typeDef: ladderDef, presentation: 'ladder' });

  it('builds a ladder-shaped empty draft, never value_importance, honouring the server-sent presentation field', () => {
    const draft = emptyDraftFor(q);
    expect(draft.kind).toBe('ladder');
  });

  it('requires a self value AND a ladder position', () => {
    let draft = emptyDraftFor(q);
    if (draft.kind !== 'ladder') throw new Error('expected ladder draft');
    expect(isDraftComplete(draft)).toBe(false);
    draft = { ...draft, selfValue: 'yes' };
    expect(isDraftComplete(draft)).toBe(false);
    draft = { ...draft, position: 4 };
    expect(isDraftComplete(draft)).toBe(true);
  });

  it('sends ladderPosition on the wire, never a client-derived preferenceValue/importance pair', () => {
    const draft = { kind: 'ladder' as const, selfValue: 'yes', position: 0 as const };
    const payload = buildAnsweredPayload(q, draft);
    expect(payload).toEqual({ slug: 'test-question', status: 'answered', selfValue: 'yes', ladderPosition: 0 });
    // The payload must never carry preferenceValue/importance alongside ladderPosition,
    // the server rejects that combination (see question.service.ts putMyQuestionAnswer).
    expect(payload && 'preferenceValue' in payload).toBe(false);
    expect(payload && 'importance' in payload).toBe(false);
  });
});

describe('a three-option single_choice question never gets the ladder, regardless of option count elsewhere', () => {
  const def: SingleChoiceDefinition = {
    type: 'single_choice',
    options: [
      { key: 'a', label: 'A' },
      { key: 'b', label: 'B' },
      { key: 'c', label: 'C' },
    ],
  };
  // The server would never actually send presentation: 'ladder' for a
  // 3-option question, this test only exercises emptyDraftFor's own
  // switch, which must key off the `presentation` field exactly as sent.
  const q = question({ typeDef: def, presentation: 'value_importance' });

  it('collects a single self value and a SET of acceptable preference values', () => {
    let draft = emptyDraftFor(q);
    if (draft.kind !== 'single_choice') throw new Error('expected single_choice draft');
    expect(isDraftComplete(draft)).toBe(false);
    draft = { ...draft, selfValue: 'a', preferenceValue: ['a', 'b'], importance: 'critical' };
    expect(isDraftComplete(draft)).toBe(true);
    const payload = buildAnsweredPayload(q, draft);
    expect(payload).toEqual({
      slug: 'test-question',
      status: 'answered',
      selfValue: 'a',
      preferenceValue: ['a', 'b'],
      importance: 'critical',
    });
  });
});

describe('a multi_choice question collects a set for both self and preference', () => {
  const def: MultiChoiceDefinition = {
    type: 'multi_choice',
    options: [
      { key: 'hiking', label: 'Hiking' },
      { key: 'cooking', label: 'Cooking' },
    ],
  };
  const q = question({ typeDef: def, presentation: 'value_importance' });

  it('is incomplete until both sets are non-empty and importance is set', () => {
    let draft = emptyDraftFor(q);
    if (draft.kind !== 'multi_choice') throw new Error('expected multi_choice draft');
    expect(isDraftComplete(draft)).toBe(false);
    draft = { ...draft, selfValue: ['hiking'] };
    expect(isDraftComplete(draft)).toBe(false);
    draft = { ...draft, preferenceValue: ['cooking'], importance: 'slight' };
    expect(isDraftComplete(draft)).toBe(true);
  });
});

describe('a frequency question uses ordered anchors for both self and preference', () => {
  const def: FrequencyDefinition = {
    type: 'frequency',
    anchors: [
      { key: 'never', label: 'Never' },
      { key: 'monthly', label: 'Monthly' },
      { key: 'daily', label: 'Daily' },
    ],
  };
  const q = question({ typeDef: def, presentation: 'value_importance' });

  it('requires one anchor each for self and preference, plus importance', () => {
    let draft = emptyDraftFor(q);
    if (draft.kind !== 'frequency') throw new Error('expected frequency draft');
    draft = { ...draft, selfValue: 'monthly' };
    expect(isDraftComplete(draft)).toBe(false);
    draft = { ...draft, preferenceValue: 'daily', importance: 'deal_breaker' };
    expect(isDraftComplete(draft)).toBe(true);
  });
});

describe('skip and prefer-not-to-say', () => {
  const q = question({});

  it('are always available and never carry a value, regardless of question type', () => {
    expect(buildSkipPayload(q)).toEqual({ slug: 'test-question', status: 'skipped' });
    expect(buildPreferNotToSayPayload(q)).toEqual({ slug: 'test-question', status: 'prefer_not_to_say' });
  });
});
