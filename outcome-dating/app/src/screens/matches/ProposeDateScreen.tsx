import React, { useState } from 'react';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { Pressable, StyleSheet, View } from 'react-native';
import { Screen } from '../../components/Screen';
import { Title, Body, Caption } from '../../components/Typography';
import { Button } from '../../components/Button';
import { FormField } from '../../components/FormField';
import { LoadingState, ErrorState } from '../../components/AsyncState';
import { colors, radii, spacing } from '../../theme/tokens';
import { useAsync } from '../../hooks/useAsync';
import { api } from '../../api/client';
import { messageForError } from '../../api/errors';
import { formatDateTime } from '../../units/datetime';
import { projectUpcomingSlots, type ConcreteSlot } from '../../domain/venueSlots';
import type { Venue } from '../../api/types';
import type { MatchesStackParamList } from '../../navigation/types';

type Props = NativeStackScreenProps<MatchesStackParamList, 'ProposeDate'>;

type Step = 'venue' | 'slot' | 'confirm';

export function ProposeDateScreen({ route, navigation }: Props): React.ReactElement {
  const { conversationId, recipientDisplayName } = route.params;
  const venuesState = useAsync(() => api.listVenues(), []);

  const [step, setStep] = useState<Step>('venue');
  const [venue, setVenue] = useState<Venue | null>(null);
  const [slot, setSlot] = useState<ConcreteSlot | null>(null);
  const [note, setNote] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  async function handleConfirm(): Promise<void> {
    if (!venue || !slot) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      const proposal = await api.proposeDate(conversationId, {
        venueId: venue.id,
        scheduledStart: slot.start.toISOString(),
        scheduledEnd: slot.end.toISOString(),
        optionalNote: note.trim() || undefined,
      });
      navigation.replace('DateProposalDetail', { dateProposalId: proposal.id });
    } catch (error) {
      setSubmitError(messageForError(error));
    } finally {
      setSubmitting(false);
    }
  }

  if (step === 'venue') {
    if (venuesState.status === 'loading') {
      return (
        <Screen>
          <LoadingState label="Loading venues" />
        </Screen>
      );
    }
    if (venuesState.status === 'error') {
      return (
        <Screen>
          <ErrorState error={venuesState.error} onRetry={venuesState.reload} />
        </Screen>
      );
    }
    return (
      <Screen>
        <Title style={styles.title}>Where to?</Title>
        <Body style={styles.subtitle}>Pick a venue for your date with {recipientDisplayName}.</Body>
        {venuesState.data.map((v) => (
          <Pressable
            key={v.id}
            onPress={() => {
              setVenue(v);
              setStep('slot');
            }}
            style={styles.venueRow}
            accessibilityRole="button"
            accessibilityLabel={`${v.name}, ${v.address}`}
          >
            <Body style={styles.venueName}>{v.name}</Body>
            <Caption>{v.address}</Caption>
          </Pressable>
        ))}
      </Screen>
    );
  }

  if (step === 'slot' && venue) {
    const slots = projectUpcomingSlots(venue.timeSlots, new Date(), 14);
    return (
      <Screen>
        <Title style={styles.title}>When?</Title>
        <Body style={styles.subtitle}>Available times at {venue.name}.</Body>
        {slots.length === 0 ? (
          <Body style={styles.subtitle}>No upcoming times found for this venue. Try another one.</Body>
        ) : (
          slots.map((s) => (
            <Pressable
              key={s.start.toISOString()}
              onPress={() => {
                setSlot(s);
                setStep('confirm');
              }}
              style={styles.venueRow}
              accessibilityRole="button"
              accessibilityLabel={formatDateTime(s.start.toISOString())}
            >
              <Body>{formatDateTime(s.start.toISOString())}</Body>
            </Pressable>
          ))
        )}
        <Button label="Choose a different venue" onPress={() => setStep('venue')} variant="ghost" />
      </Screen>
    );
  }

  if (step === 'confirm' && venue && slot) {
    return (
      <Screen>
        <Title style={styles.title}>Review your invite</Title>
        <View style={styles.summaryBox}>
          <Body style={styles.venueName}>{venue.name}</Body>
          <Caption>{venue.address}</Caption>
          <Body style={styles.when}>{formatDateTime(slot.start.toISOString())}</Body>
        </View>

        <FormField
          label="Add a note (optional)"
          value={note}
          onChangeText={setNote}
          placeholder={`Looking forward to it, ${recipientDisplayName}!`}
          multiline
        />

        <View style={styles.moneyBox} accessible accessibilityLabel="About the payment hold">
          <Body style={styles.moneyTitle}>About the hold on your card</Body>
          <Body style={styles.moneyText}>
            Sending this invite places a hold on your card, like a hotel deposit, it is not a charge. Nothing is taken
            from your card unless {recipientDisplayName} accepts. We'll show you the exact amount on the next screen,
            the moment the hold is placed.
          </Body>
          <Body style={styles.moneyText}>
            If they decline, don't respond in time, or you cancel far enough ahead, the hold is released automatically
            and you're never charged.
          </Body>
        </View>

        {submitError ? (
          <Body style={styles.error} accessibilityRole="alert">
            {submitError}
          </Body>
        ) : null}

        <Button label="Send date invite" onPress={handleConfirm} loading={submitting} testID="confirm-propose-date" />
        <Button label="Back" onPress={() => setStep('slot')} variant="ghost" disabled={submitting} />
      </Screen>
    );
  }

  return (
    <Screen>
      <ErrorState error={new Error('missing_selection')} onRetry={() => setStep('venue')} />
    </Screen>
  );
}

const styles = StyleSheet.create({
  title: { marginBottom: spacing.xs },
  subtitle: { color: colors.textSecondary, marginBottom: spacing.md },
  venueRow: { borderWidth: 1, borderColor: colors.border, borderRadius: radii.md, padding: spacing.md, marginBottom: spacing.sm, minHeight: 48 },
  venueName: { fontWeight: '700' },
  summaryBox: { backgroundColor: colors.surface, borderRadius: radii.md, padding: spacing.md, marginBottom: spacing.md },
  when: { marginTop: spacing.sm, fontWeight: '700' },
  moneyBox: { backgroundColor: colors.accentMuted, borderRadius: radii.md, padding: spacing.md, marginVertical: spacing.md, gap: spacing.sm },
  moneyTitle: { fontWeight: '700', color: colors.accent },
  moneyText: { color: colors.textPrimary },
  error: { color: colors.critical, fontWeight: '600', marginBottom: spacing.md },
});
