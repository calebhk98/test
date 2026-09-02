import React, { useState } from 'react';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { StyleSheet, View } from 'react-native';
import { Screen } from '../../components/Screen';
import { Headline, Body } from '../../components/Typography';
import { Button } from '../../components/Button';
import { ScaffoldNotice } from '../../components/ScaffoldNotice';
import { colors, spacing } from '../../theme/tokens';
import { api } from '../../api/client';
import { messageForError } from '../../api/errors';
import type { CheckInOutcome } from '../../api/types';
import type { MatchesStackParamList } from '../../navigation/types';

type Props = NativeStackScreenProps<MatchesStackParamList, 'CheckIn'>;

const OUTCOMES: { key: CheckInOutcome; label: string }[] = [
  { key: 'went_well', label: 'It went well' },
  { key: 'went_okay', label: 'It was okay' },
  { key: 'did_not_go_well', label: "It didn't go well" },
  { key: 'did_not_happen', label: "It didn't happen" },
];

/**
 * Scaffolded: wires the real endpoint with the four-outcome model the
 * product review calls out as worth protecting ("the four-outcome
 * post-date check-in instead of a single star rating"), but has none
 * of a finished screen's safety-flag detail form, confirmation state,
 * or tests.
 */
export function CheckInScreen({ route, navigation }: Props): React.ReactElement {
  const { dateProposalId } = route.params;
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  async function submit(outcome: CheckInOutcome): Promise<void> {
    setSubmitting(true);
    setError(null);
    try {
      await api.submitCheckIn(dateProposalId, { outcome });
      setDone(true);
    } catch (err) {
      setError(messageForError(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Screen>
      <Headline style={styles.title}>How did it go?</Headline>
      <ScaffoldNotice remaining="Safety-flag details, 'would meet again', and free-text notes are not built, only the four-outcome choice. Not tested." />
      {done ? (
        <View>
          <Body>Thanks, that's saved.</Body>
          <Button label="Back" onPress={() => navigation.goBack()} variant="secondary" />
        </View>
      ) : (
        <View style={styles.list}>
          {OUTCOMES.map((o) => (
            <Button key={o.key} label={o.label} onPress={() => submit(o.key)} loading={submitting} variant="secondary" />
          ))}
        </View>
      )}
      {error ? (
        <Body style={styles.error} accessibilityRole="alert">
          {error}
        </Body>
      ) : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  title: { marginBottom: spacing.sm },
  list: { gap: spacing.sm },
  error: { color: colors.critical, fontWeight: '600', marginTop: spacing.md },
});
