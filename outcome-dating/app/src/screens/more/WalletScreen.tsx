import React from 'react';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { Pressable, StyleSheet, View } from 'react-native';
import { Screen } from '../../components/Screen';
import { Headline, Body, Caption } from '../../components/Typography';
import { StatusBadge } from '../../components/StatusBadge';
import { LoadingState, ErrorState, EmptyState } from '../../components/AsyncState';
import { ScaffoldNotice } from '../../components/ScaffoldNotice';
import { colors, radii, spacing } from '../../theme/tokens';
import { useAsync } from '../../hooks/useAsync';
import { api } from '../../api/client';
import { formatDateTime } from '../../units/datetime';
import type { MoreStackParamList } from '../../navigation/types';

type Props = NativeStackScreenProps<MoreStackParamList, 'Wallet'>;

const TICKET_TONE: Record<string, 'positive' | 'neutral' | 'critical'> = {
  issued: 'positive',
  redeemed: 'neutral',
  expired: 'neutral',
  canceled: 'critical',
};

export function WalletScreen({ navigation }: Props): React.ReactElement {
  const result = useAsync(() => api.listMyTickets(), []);

  return (
    <Screen>
      <Headline style={styles.title}>Wallet</Headline>
      <ScaffoldNotice remaining="Redemption QR code display, ticket cancellation, and expired-ticket cleanup are not built. This reads real tickets from the API." />
      {result.status === 'loading' ? <LoadingState label="Loading tickets" /> : null}
      {result.status === 'error' ? <ErrorState error={result.error} onRetry={result.reload} /> : null}
      {result.status === 'ready' && result.data.length === 0 ? <EmptyState title="No tickets yet" message="Confirmed dates show a ticket here." /> : null}
      {result.status === 'ready'
        ? result.data.map((ticket) => (
            <Pressable
              key={ticket.id}
              style={styles.row}
              onPress={() => navigation.navigate('TicketDetail', { ticketId: ticket.id })}
              accessibilityRole="button"
              accessibilityLabel={`${ticket.venueName}, ${formatDateTime(ticket.scheduledStart)}, ${ticket.status}`}
            >
              <Body style={styles.venueName}>{ticket.venueName}</Body>
              <Caption>{formatDateTime(ticket.scheduledStart)}</Caption>
              <View style={styles.badgeRow}>
                <StatusBadge label={ticket.status} tone={TICKET_TONE[ticket.status] ?? 'neutral'} />
              </View>
            </Pressable>
          ))
        : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  title: { marginBottom: spacing.sm },
  row: { borderWidth: 1, borderColor: colors.border, borderRadius: radii.md, padding: spacing.md, marginBottom: spacing.sm },
  venueName: { fontWeight: '700' },
  badgeRow: { marginTop: spacing.sm },
});
