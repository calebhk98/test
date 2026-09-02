import React, { useState } from 'react';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { StyleSheet, View } from 'react-native';
import { Screen } from '../../components/Screen';
import { Title, Body, Caption } from '../../components/Typography';
import { Button } from '../../components/Button';
import { StatusBadge } from '../../components/StatusBadge';
import { LoadingState, ErrorState } from '../../components/AsyncState';
import { colors, radii, spacing } from '../../theme/tokens';
import { useAsync } from '../../hooks/useAsync';
import { api } from '../../api/client';
import { messageForError } from '../../api/errors';
import { useAuth } from '../../state/AuthContext';
import { formatDateTime } from '../../units/datetime';
import { describeDateProposalStatus } from '../../domain/dateProposalCopy';
import {
  acceptExpiryDetail,
  declineOutcomeDetail,
  holdDetail,
  holdHeadline,
  noShowDetail,
  refundCutoffDetail,
} from '../../domain/moneyMomentCopy';
import type { MatchesStackParamList } from '../../navigation/types';

type Props = NativeStackScreenProps<MatchesStackParamList, 'DateProposalDetail'>;

export function DateProposalDetailScreen({ route, navigation }: Props): React.ReactElement {
  const { dateProposalId } = route.params;
  const { me } = useAuth();
  const { status, data: proposal, error, reload } = useAsync(() => api.getDateProposal(dateProposalId), [dateProposalId]);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  if (status === 'loading') {
    return (
      <Screen>
        <LoadingState label="Loading date" />
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

  const viewerIsProposer = proposal.proposerId === me?.id;
  // The date-proposal response carries only ids, not display names (see
  // api/types.ts DateProposal); the conversation/match list is where a
  // name is available. "them" keeps this screen correct without
  // fetching a second profile just to fill in a word.
  const otherPartyLabel = 'them';
  const statusCopy = describeDateProposalStatus(proposal.status, viewerIsProposer);

  async function runAction(name: string, action: () => Promise<unknown>): Promise<void> {
    setActionLoading(name);
    setActionError(null);
    try {
      await action();
      reload();
    } catch (err) {
      setActionError(messageForError(err));
    } finally {
      setActionLoading(null);
    }
  }

  const canAccept = !viewerIsProposer && proposal.status === 'pending_acceptance';
  const canDecline = !viewerIsProposer && proposal.status === 'pending_acceptance';
  const canCancel = proposal.status === 'pending_acceptance' || proposal.status === 'accepted';
  const canConfirmAttendance = proposal.status === 'ticketed' || proposal.status === 'accepted' || proposal.status === 'charged';

  return (
    <Screen>
      <View style={styles.headerRow}>
        <Title>{formatDateTime(proposal.scheduledStart)}</Title>
        <StatusBadge label={statusCopy.label} tone={statusCopy.tone} />
      </View>
      <Body style={styles.statusDetail}>{statusCopy.detail}</Body>

      {proposal.optionalNote ? (
        <View style={styles.noteBox}>
          <Caption>Note</Caption>
          <Body>{proposal.optionalNote}</Body>
        </View>
      ) : null}

      <View style={styles.moneyBox} accessible accessibilityLabel="About the payment hold on this date">
        <Body style={styles.moneyTitle}>About the money</Body>
        <Body style={styles.moneyText}>{holdHeadline(proposal.escrowAmountCents, 'usd', otherPartyLabel)}</Body>
        <Body style={styles.moneyText}>{holdDetail(proposal.escrowAmountCents, 'usd')}</Body>
        {proposal.status === 'pending_acceptance' ? (
          <Body style={styles.moneyText}>{acceptExpiryDetail(proposal.policySnapshot['date.accept_expiry_hours'])}</Body>
        ) : null}
        <Body style={styles.moneyText}>{refundCutoffDetail(proposal.policySnapshot)}</Body>
        <Body style={styles.moneyText}>{noShowDetail(proposal.policySnapshot)}</Body>
        {viewerIsProposer && proposal.status === 'pending_acceptance' ? (
          <Body style={styles.moneyText}>{declineOutcomeDetail(otherPartyLabel)}</Body>
        ) : null}
      </View>

      {actionError ? (
        <Body style={styles.error} accessibilityRole="alert">
          {actionError}
        </Body>
      ) : null}

      <View style={styles.actions}>
        {canAccept ? (
          <Button
            label="Accept date"
            onPress={() => runAction('accept', () => api.acceptDateProposal(dateProposalId))}
            loading={actionLoading === 'accept'}
            testID="accept-date"
          />
        ) : null}
        {canDecline ? (
          <Button
            label="Decline"
            onPress={() => runAction('decline', () => api.declineDateProposal(dateProposalId))}
            loading={actionLoading === 'decline'}
            variant="secondary"
            testID="decline-date"
          />
        ) : null}
        {canConfirmAttendance ? (
          <Button
            label="Confirm we both showed up"
            onPress={() => runAction('confirm', () => api.confirmAttendance(dateProposalId))}
            loading={actionLoading === 'confirm'}
            variant="secondary"
          />
        ) : null}
        {canConfirmAttendance ? (
          <Button label="Check in after the date" onPress={() => navigation.navigate('CheckIn', { dateProposalId })} variant="ghost" />
        ) : null}
        {canCancel ? (
          <Button
            label="Cancel this date"
            onPress={() => runAction('cancel', () => api.cancelDateProposal(dateProposalId))}
            loading={actionLoading === 'cancel'}
            variant="destructive"
            testID="cancel-date"
          />
        ) : null}
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  headerRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: spacing.sm },
  statusDetail: { color: colors.textSecondary, marginTop: spacing.xs, marginBottom: spacing.md },
  noteBox: { backgroundColor: colors.surface, borderRadius: radii.md, padding: spacing.md, marginBottom: spacing.md },
  moneyBox: { backgroundColor: colors.accentMuted, borderRadius: radii.md, padding: spacing.md, gap: spacing.sm, marginBottom: spacing.lg },
  moneyTitle: { fontWeight: '700', color: colors.accent },
  moneyText: { color: colors.textPrimary },
  error: { color: colors.critical, fontWeight: '600', marginBottom: spacing.md },
  actions: { gap: spacing.sm },
});
