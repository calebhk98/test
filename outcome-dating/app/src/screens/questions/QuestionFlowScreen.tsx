import React, { useCallback, useState } from 'react';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { StyleSheet } from 'react-native';
import { Screen } from '../../components/Screen';
import { Body, Caption } from '../../components/Typography';
import { LoadingState, ErrorState, EmptyState } from '../../components/AsyncState';
import { QuestionAnswerForm } from '../../components/question/QuestionAnswerForm';
import { spacing } from '../../theme/tokens';
import { useAsync } from '../../hooks/useAsync';
import { api } from '../../api/client';
import { messageForError } from '../../api/errors';
import type { PutQuestionAnswerInput, QuestionCardView } from '../../api/types';
import type { QuestionsStackParamList } from '../../navigation/types';

type Props = NativeStackScreenProps<QuestionsStackParamList, 'QuestionFlow'>;

const BATCH_SIZE = 10;

export function QuestionFlowScreen(_props: Props): React.ReactElement {
  const { status, data, error, reload } = useAsync(() => api.getNextQuestions(BATCH_SIZE), []);
  const [queue, setQueue] = useState<QuestionCardView[] | null>(null);
  const [answeredCount, setAnsweredCount] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const effectiveQueue = queue ?? (status === 'ready' ? data.items : null);
  const current = effectiveQueue?.[0] ?? null;

  const advance = useCallback(async () => {
    const rest = (effectiveQueue ?? []).slice(1);
    if (rest.length > 0) {
      setQueue(rest);
      return;
    }
    // Ran out of the current batch, ask the selector for what's next.
    try {
      const next = await api.getNextQuestions(BATCH_SIZE);
      setQueue(next.items);
    } catch {
      setQueue([]);
    }
  }, [effectiveQueue]);

  async function handleAnswer(input: PutQuestionAnswerInput): Promise<void> {
    setSubmitting(true);
    setSubmitError(null);
    try {
      await api.putMyAnswer(input);
      setAnsweredCount((n) => n + 1);
      await advance();
    } catch (err) {
      setSubmitError(messageForError(err));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleSkip(): Promise<void> {
    if (!current) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      await api.putMyAnswer({ slug: current.slug, status: 'skipped' });
      await advance();
    } catch (err) {
      setSubmitError(messageForError(err));
    } finally {
      setSubmitting(false);
    }
  }

  async function handlePreferNotToSay(): Promise<void> {
    if (!current) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      await api.putMyAnswer({ slug: current.slug, status: 'prefer_not_to_say' });
      await advance();
    } catch (err) {
      setSubmitError(messageForError(err));
    } finally {
      setSubmitting(false);
    }
  }

  if (status === 'loading' && !queue) {
    return (
      <Screen>
        <LoadingState label="Finding your next question" />
      </Screen>
    );
  }

  if (status === 'error' && !queue) {
    return (
      <Screen>
        <ErrorState error={error} onRetry={reload} />
      </Screen>
    );
  }

  if (!current) {
    return (
      <Screen>
        <EmptyState
          title="You're all caught up"
          message="There's nothing new to answer right now. Check back later, or revisit questions you've already answered from Settings."
        />
      </Screen>
    );
  }

  return (
    <Screen>
      <Caption style={styles.progress}>{answeredCount} answered this session</Caption>
      <QuestionAnswerForm
        key={current.id}
        question={current}
        onSubmit={handleAnswer}
        onSkip={handleSkip}
        onPreferNotToSay={handlePreferNotToSay}
        submitting={submitting}
      />
      {submitError ? (
        <Body style={styles.error} accessibilityRole="alert">
          {submitError}
        </Body>
      ) : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  progress: { marginBottom: spacing.md },
  error: { color: '#A3231A', marginTop: spacing.md, fontWeight: '600' },
});
