import { ladderLabels, ladderPositionToPreference } from '../ladder';
import type { SingleChoiceDefinition } from '../../api/types';

const def: SingleChoiceDefinition = {
  type: 'single_choice',
  options: [
    { key: 'wants_kids', label: 'Wants kids' },
    { key: 'no_kids', label: "Doesn't want kids" },
  ],
};

describe('ladderLabels', () => {
  it('builds five labels from the question option labels, deal breakers at both ends and "don\'t care" in the middle', () => {
    const labels = ladderLabels(def);
    expect(labels).toEqual([
      'Deal breaker: Wants kids',
      'Prefer Wants kids',
      "Don't care",
      "Prefer Doesn't want kids",
      "Deal breaker: Doesn't want kids",
    ]);
  });
});

describe('ladderPositionToPreference', () => {
  it('maps both deal-breaker ends to importance deal_breaker, narrowed to the picked side', () => {
    expect(ladderPositionToPreference(def, 0)).toEqual({ preferenceValue: ['wants_kids'], importance: 'deal_breaker' });
    expect(ladderPositionToPreference(def, 4)).toEqual({ preferenceValue: ['no_kids'], importance: 'deal_breaker' });
  });

  it('maps the middle position to importance irrelevant with both options accepted', () => {
    expect(ladderPositionToPreference(def, 2)).toEqual({ preferenceValue: ['wants_kids', 'no_kids'], importance: 'irrelevant' });
  });

  it('maps the two "prefer" positions to importance important', () => {
    expect(ladderPositionToPreference(def, 1)).toEqual({ preferenceValue: ['wants_kids'], importance: 'important' });
    expect(ladderPositionToPreference(def, 3)).toEqual({ preferenceValue: ['no_kids'], importance: 'important' });
  });

  it('throws for a question with anything other than exactly two options', () => {
    const threeOptionDef: SingleChoiceDefinition = { type: 'single_choice', options: [...def.options, { key: 'unsure', label: 'Unsure' }] };
    expect(() => ladderPositionToPreference(threeOptionDef, 0)).toThrow();
  });
});
