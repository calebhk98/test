import React from 'react';
import { Pressable, StyleSheet, View } from 'react-native';
import { Body, Caption } from '../../components/Typography';
import { StatusBadge } from '../../components/StatusBadge';
import { colors, radii, spacing } from '../../theme/tokens';
import { formatDateTime, formatTime } from '../../units/datetime';
import { describeDateProposalStatus } from '../../domain/dateProposalCopy';
import type { TimelineEventView } from '../../api/types';

interface TimelineEventRowProps {
  event: TimelineEventView;
  isOwnMessage: boolean;
  viewerId: string | undefined;
  onPressDateProposal: (dateProposalId: string) => void;
}

/** One row of the merged conversation timeline: a chat bubble for a message, or, in place, a card for a date-proposal lifecycle event (proposed/accepted/declined/canceled/expired). Never two separate lists stitched together in the UI. */
export function TimelineEventRow({ event, isOwnMessage, viewerId, onPressDateProposal }: TimelineEventRowProps): React.ReactElement {
  if (event.kind === 'message') {
    return (
      <View style={[styles.messageRow, isOwnMessage ? styles.messageRowOwn : styles.messageRowOther]}>
        <View style={[styles.bubble, isOwnMessage ? styles.bubbleOwn : styles.bubbleOther]}>
          <Body style={isOwnMessage ? styles.bubbleTextOwn : styles.bubbleTextOther}>{event.body}</Body>
        </View>
        <Caption style={styles.timestamp}>{formatTime(event.occurredAt)}</Caption>
      </View>
    );
  }

  const statusCopy = describeDateProposalStatus(event.status, event.proposerId === viewerId);
  return (
    <Pressable
      onPress={() => onPressDateProposal(event.dateProposalId)}
      style={styles.card}
      accessibilityRole="button"
      accessibilityLabel={`Date at ${event.venueName}, ${formatDateTime(event.scheduledStart)}, ${statusCopy.label}`}
    >
      <Caption>Date invite</Caption>
      <Body style={styles.venueName}>{event.venueName}</Body>
      <Body>{formatDateTime(event.scheduledStart)}</Body>
      <View style={styles.cardFooter}>
        <StatusBadge label={statusCopy.label} tone={statusCopy.tone} />
        {event.hasTicket ? <Caption style={styles.ticketNote}>Ticket ready</Caption> : null}
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  messageRow: { marginVertical: spacing.xs, maxWidth: '80%' },
  messageRowOwn: { alignSelf: 'flex-end', alignItems: 'flex-end' },
  messageRowOther: { alignSelf: 'flex-start', alignItems: 'flex-start' },
  bubble: { borderRadius: radii.lg, paddingHorizontal: spacing.md, paddingVertical: spacing.sm },
  bubbleOwn: { backgroundColor: colors.accent },
  bubbleOther: { backgroundColor: colors.surface },
  bubbleTextOwn: { color: colors.textOnAccent },
  bubbleTextOther: { color: colors.textPrimary },
  timestamp: { marginTop: 2 },
  card: {
    alignSelf: 'stretch',
    backgroundColor: colors.background,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radii.md,
    padding: spacing.md,
    marginVertical: spacing.sm,
  },
  venueName: { fontWeight: '700', marginTop: 2 },
  cardFooter: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, marginTop: spacing.sm },
  ticketNote: { color: colors.positive, fontWeight: '600' },
});
