import React, { useState } from 'react';
import { StyleSheet, View } from 'react-native';
import { Title, Body, Caption } from '../Typography';
import { Button } from '../Button';
import { ChoiceGroup, MultiChoiceGroup } from './ChoiceGroup';
import { ImportanceControl } from './ImportanceControl';
import { LadderControl } from './LadderControl';
import { ScaleControl } from './ScaleControl';
import { SkipRow } from './SkipRow';
import { spacing } from '../../theme/tokens';
import { buildAnsweredPayload, emptyDraftFor, isDraftComplete, type QuestionDraft } from '../../domain/questionDraft';
import type { PutQuestionAnswerInput, QuestionCardView } from '../../api/types';

interface QuestionAnswerFormProps {
  question: QuestionCardView;
  onSubmit: (input: PutQuestionAnswerInput) => void;
  onSkip: () => void;
  onPreferNotToSay: () => void;
  submitting?: boolean;
}

/**
 * Renders the control that matches this question's `type` AND
 * `presentation`, exactly as the server sent them, never guessed. This
 * is the piece that failed real user testing before the typed bank
 * existed (an unlabelled 1-5 with no skip and no "don't care"), so
 * every branch below corresponds one-to-one to a case the product
 * review calls out: an ordered scale with a labelled midpoint, a real
 * categorical choice, a multi-select, a frequency scale with concrete
 * anchors, and, when eligible, the single ladder control instead of
 * two abstract sliders.
 */
export function QuestionAnswerForm({ question, onSubmit, onSkip, onPreferNotToSay, submitting }: QuestionAnswerFormProps): React.ReactElement {
  const [draft, setDraft] = useState<QuestionDraft>(() => emptyDraftFor(question));
  const canSubmit = isDraftComplete(draft) && !submitting;

  function handleSubmit(): void {
    const payload = buildAnsweredPayload(question, draft);
    if (payload) onSubmit(payload);
  }

  return (
    <View>
      <Title style={styles.question}>{question.questionText}</Title>
      {question.sensitive ? <Caption style={styles.sensitive}>This is a sensitive topic. Answering is always optional.</Caption> : null}

      {renderControl(question, draft, setDraft)}

      <View style={styles.submitRow}>
        <Button label="Save answer" onPress={handleSubmit} disabled={!canSubmit} loading={submitting} testID="save-answer" />
      </View>

      <SkipRow onSkip={onSkip} onPreferNotToSay={onPreferNotToSay} disabled={submitting} />
    </View>
  );
}

function renderControl(question: QuestionCardView, draft: QuestionDraft, setDraft: (d: QuestionDraft) => void): React.ReactElement {
  if (draft.kind === 'ladder' && question.typeDef.type === 'single_choice') {
    const def = question.typeDef;
    return (
      <View style={styles.block}>
        <Body style={styles.sectionLabel}>Which describes you?</Body>
        <ChoiceGroup
          options={def.options}
          value={draft.selfValue}
          onChange={(selfValue) => setDraft({ ...draft, selfValue })}
          accessibilityLabel="Which describes you"
        />
        <Body style={[styles.sectionLabel, styles.spaced]}>Your preference</Body>
        <LadderControl def={def} position={draft.position} onChange={(position) => setDraft({ ...draft, position })} />
      </View>
    );
  }

  if (draft.kind === 'scale' && question.typeDef.type === 'scale') {
    const def = question.typeDef;
    return (
      <View style={styles.block}>
        <Body style={styles.sectionLabel}>About you</Body>
        <ScaleControl
          def={def}
          value={draft.selfValue}
          onChange={(selfValue) => setDraft({ ...draft, selfValue })}
          accessibilityLabel="About you"
        />
        <Body style={[styles.sectionLabel, styles.spaced]}>What you want in a partner</Body>
        <ScaleControl
          def={def}
          value={draft.preferenceValue}
          onChange={(preferenceValue) => setDraft({ ...draft, preferenceValue })}
          accessibilityLabel="What you want in a partner"
        />
        <View style={styles.spaced}>
          <ImportanceControl value={draft.importance} onChange={(importance) => setDraft({ ...draft, importance })} />
        </View>
      </View>
    );
  }

  if (draft.kind === 'single_choice' && question.typeDef.type === 'single_choice') {
    const def = question.typeDef;
    return (
      <View style={styles.block}>
        <Body style={styles.sectionLabel}>Which describes you?</Body>
        <ChoiceGroup
          options={def.options}
          value={draft.selfValue}
          onChange={(selfValue) => setDraft({ ...draft, selfValue })}
          accessibilityLabel="Which describes you"
        />
        <Body style={[styles.sectionLabel, styles.spaced]}>Which would be okay in a partner? Choose any that apply.</Body>
        <MultiChoiceGroup
          options={def.options}
          value={draft.preferenceValue}
          onChange={(preferenceValue) => setDraft({ ...draft, preferenceValue })}
          accessibilityLabel="Acceptable in a partner"
        />
        <View style={styles.spaced}>
          <ImportanceControl value={draft.importance} onChange={(importance) => setDraft({ ...draft, importance })} />
        </View>
      </View>
    );
  }

  if (draft.kind === 'multi_choice' && question.typeDef.type === 'multi_choice') {
    const def = question.typeDef;
    return (
      <View style={styles.block}>
        <Body style={styles.sectionLabel}>Which apply to you? Choose any that apply.</Body>
        <MultiChoiceGroup
          options={def.options}
          value={draft.selfValue}
          onChange={(selfValue) => setDraft({ ...draft, selfValue })}
          accessibilityLabel="Which apply to you"
        />
        <Body style={[styles.sectionLabel, styles.spaced]}>Which would you like in a partner? Choose any that apply.</Body>
        <MultiChoiceGroup
          options={def.options}
          value={draft.preferenceValue}
          onChange={(preferenceValue) => setDraft({ ...draft, preferenceValue })}
          accessibilityLabel="Which you would like in a partner"
        />
        <View style={styles.spaced}>
          <ImportanceControl value={draft.importance} onChange={(importance) => setDraft({ ...draft, importance })} />
        </View>
      </View>
    );
  }

  if (draft.kind === 'frequency' && question.typeDef.type === 'frequency') {
    const def = question.typeDef;
    return (
      <View style={styles.block}>
        <Body style={styles.sectionLabel}>How often is this true for you?</Body>
        <ChoiceGroup
          options={def.anchors}
          value={draft.selfValue}
          onChange={(selfValue) => setDraft({ ...draft, selfValue })}
          accessibilityLabel="How often is this true for you"
        />
        <Body style={[styles.sectionLabel, styles.spaced]}>How often would you want this from a partner?</Body>
        <ChoiceGroup
          options={def.anchors}
          value={draft.preferenceValue}
          onChange={(preferenceValue) => setDraft({ ...draft, preferenceValue })}
          accessibilityLabel="How often you want this from a partner"
        />
        <View style={styles.spaced}>
          <ImportanceControl value={draft.importance} onChange={(importance) => setDraft({ ...draft, importance })} />
        </View>
      </View>
    );
  }

  // Unreachable given `emptyDraftFor` always matches the question's own type/presentation, kept only so this function is total.
  return <Body>Unsupported question type.</Body>;
}

const styles = StyleSheet.create({
  question: { marginBottom: spacing.xs },
  sensitive: { marginBottom: spacing.md },
  block: { marginTop: spacing.md },
  sectionLabel: { fontWeight: '700', marginBottom: spacing.sm },
  spaced: { marginTop: spacing.lg },
  submitRow: { marginTop: spacing.lg },
});
