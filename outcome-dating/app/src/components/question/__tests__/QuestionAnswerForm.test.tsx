import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import { QuestionAnswerForm } from '../QuestionAnswerForm';
import type { PutQuestionAnswerInput, QuestionCardView } from '../../../api/types';

const ladderQuestion: QuestionCardView = {
  id: 'q-ladder',
  slug: 'wants-kids',
  version: 1,
  category: 'lifestyle',
  subcategory: null,
  tags: [],
  questionText: 'Kids?',
  sensitive: false,
  typeDef: {
    type: 'single_choice',
    options: [
      { key: 'yes', label: 'Wants kids' },
      { key: 'no', label: "Doesn't want kids" },
    ],
  },
  presentation: 'ladder',
};

const scaleQuestion: QuestionCardView = {
  id: 'q-scale',
  slug: 'tidiness',
  version: 1,
  category: 'lifestyle',
  subcategory: null,
  tags: [],
  questionText: 'How tidy are you?',
  sensitive: false,
  typeDef: { type: 'scale', min: 1, max: 5, minLabel: 'Messy', maxLabel: 'Spotless', midLabel: 'Average' },
  presentation: 'value_importance',
};

describe('QuestionAnswerForm - ladder presentation', () => {
  it('renders the ladder control, never the two-slider form, for a ladder-presentation question', () => {
    const { getByTestId, queryByText } = render(
      <QuestionAnswerForm question={ladderQuestion} onSubmit={jest.fn()} onSkip={jest.fn()} onPreferNotToSay={jest.fn()} />,
    );
    expect(getByTestId('ladder-control')).toBeTruthy();
    expect(queryByText('How much does this matter to you?')).toBeNull();
  });

  it('keeps Save answer disabled until both a self value and a ladder position are chosen', () => {
    const { getByTestId } = render(
      <QuestionAnswerForm question={ladderQuestion} onSubmit={jest.fn()} onSkip={jest.fn()} onPreferNotToSay={jest.fn()} />,
    );
    const saveButton = getByTestId('save-answer');
    expect(saveButton.props.accessibilityState.disabled).toBe(true);

    fireEvent.press(getByTestId('ladder-position-0'));
    expect(saveButton.props.accessibilityState.disabled).toBe(true); // still missing self value

    fireEvent.press(getByTestId('ladder-position-4'));
    expect(saveButton.props.accessibilityState.disabled).toBe(true); // still missing self value
  });

  it('submits ladderPosition (not a derived preferenceValue/importance pair) once both are chosen', () => {
    let submitted: PutQuestionAnswerInput | null = null;
    const { getByTestId, getByLabelText } = render(
      <QuestionAnswerForm
        question={ladderQuestion}
        onSubmit={(input) => {
          submitted = input;
        }}
        onSkip={jest.fn()}
        onPreferNotToSay={jest.fn()}
      />,
    );
    fireEvent.press(getByLabelText('Wants kids'));
    fireEvent.press(getByTestId('ladder-position-1'));
    fireEvent.press(getByTestId('save-answer'));

    expect(submitted).toEqual({ slug: 'wants-kids', status: 'answered', selfValue: 'yes', ladderPosition: 1 });
  });
});

describe('QuestionAnswerForm - value_importance presentation', () => {
  it('renders separate self and preference scale controls plus an importance control', () => {
    const { getByText } = render(
      <QuestionAnswerForm question={scaleQuestion} onSubmit={jest.fn()} onSkip={jest.fn()} onPreferNotToSay={jest.fn()} />,
    );
    expect(getByText('About you')).toBeTruthy();
    expect(getByText('What you want in a partner')).toBeTruthy();
    expect(getByText('How much does this matter to you?')).toBeTruthy();
  });

  it('requires self value, preference value, AND importance before Save answer enables', () => {
    const { getByTestId, getAllByLabelText, getByLabelText } = render(
      <QuestionAnswerForm question={scaleQuestion} onSubmit={jest.fn()} onSkip={jest.fn()} onPreferNotToSay={jest.fn()} />,
    );
    const saveButton = getByTestId('save-answer');
    expect(saveButton.props.accessibilityState.disabled).toBe(true);

    // Two "Average" radios exist (self scale + preference scale); press both.
    const midpoints = getAllByLabelText('Average');
    expect(midpoints).toHaveLength(2);
    fireEvent.press(midpoints[0]!);
    expect(saveButton.props.accessibilityState.disabled).toBe(true);
    fireEvent.press(midpoints[1]!);
    expect(saveButton.props.accessibilityState.disabled).toBe(true); // importance still missing

    fireEvent.press(getByLabelText('Important'));
    expect(saveButton.props.accessibilityState.disabled).toBe(false);
  });
});

describe('QuestionAnswerForm - skip and prefer-not-to-say are always reachable', () => {
  it('calls onSkip immediately, with no value required, regardless of question type or draft completeness', () => {
    const onSkip = jest.fn();
    const { getByTestId } = render(
      <QuestionAnswerForm question={scaleQuestion} onSubmit={jest.fn()} onSkip={onSkip} onPreferNotToSay={jest.fn()} />,
    );
    fireEvent.press(getByTestId('skip-question'));
    expect(onSkip).toHaveBeenCalledTimes(1);
  });

  it('calls onPreferNotToSay immediately, with no value required', () => {
    const onPreferNotToSay = jest.fn();
    const { getByTestId } = render(
      <QuestionAnswerForm question={ladderQuestion} onSubmit={jest.fn()} onSkip={jest.fn()} onPreferNotToSay={onPreferNotToSay} />,
    );
    fireEvent.press(getByTestId('prefer-not-to-say'));
    expect(onPreferNotToSay).toHaveBeenCalledTimes(1);
  });

  it('never disables skip/prefer-not-to-say based on draft completeness', () => {
    const { getByTestId } = render(
      <QuestionAnswerForm question={scaleQuestion} onSubmit={jest.fn()} onSkip={jest.fn()} onPreferNotToSay={jest.fn()} />,
    );
    expect(getByTestId('skip-question').props.accessibilityState.disabled).toBeFalsy();
    expect(getByTestId('prefer-not-to-say').props.accessibilityState.disabled).toBeFalsy();
  });
});
