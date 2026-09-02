import React from 'react';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { StyleSheet, View } from 'react-native';
import { Screen } from '../../components/Screen';
import { Title, Body, Caption } from '../../components/Typography';
import { StatusBadge } from '../../components/StatusBadge';
import { LoadingState, ErrorState } from '../../components/AsyncState';
import { ScaffoldNotice } from '../../components/ScaffoldNotice';
import { colors, radii, spacing } from '../../theme/tokens';
import { useAsync } from '../../hooks/useAsync';
import { api } from '../../api/client';
import { formatDateTime } from '../../units/datetime';
import type { MoreStackParamList } from '../../navigation/types';

type Props = NativeStackScreenProps<MoreStackParamList, 'TicketDetail'>;

export function TicketDetailScreen({ route }: Props): React.ReactElement {
  const { status, data: ticket, error, reload } = useAsync(() => api.getMyTicket(route.params.ticketId), [route.params.ticketId]);

  if (status === 'loading') {
    return (
      <Screen>
        <LoadingState label="Loading ticket" />
      </Screen>
    );
  }
  if (status === 'error') {
    return (
      <Screen>
        <ErrorState error={error} onRetry={reload} />
      </Screen>
    );
  }

  return (
    <Screen>
      <ScaffoldNotice remaining="No scannable QR rendering yet, the code is shown as plain text. A venue-side scan flow is out of scope for this app." />
      <Title>{ticket.venueName}</Title>
      <Caption style={styles.address}>{ticket.venueAddress}</Caption>
      <StatusBadge label={ticket.status} tone={ticket.status === 'issued' ? 'positive' : 'neutral'} />
      <View style={styles.detailBox}>
        <Body>{formatDateTime(ticket.scheduledStart)}</Body>
        <Caption style={styles.code}>Code: {ticket.code}</Caption>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  address: { marginBottom: spacing.sm },
  detailBox: { backgroundColor: colors.surface, borderRadius: radii.md, padding: spacing.md, marginTop: spacing.md },
  code: { marginTop: spacing.sm, fontWeight: '700' },
});
