import React from 'react';
import { StyleSheet, View } from 'react-native';
import { Body } from '../Typography';
import { colors, radii, spacing } from '../../theme/tokens';
import {
  acceptExpiryDetail,
  declineOutcomeDetail,
  holdDetail,
  holdHeadline,
  noShowDetail,
  refundCutoffDetail,
} from '../../domain/moneyMomentCopy';
import type { DateProposalPolicySnapshot, DateProposalStatus } from '../../api/types';

interface MoneySummaryProps {
  escrowAmountCents: number;
  currency: string;
  policySnapshot: DateProposalPolicySnapshot;
  status: DateProposalStatus;
  viewerIsProposer: boolean;
  otherPartyLabel: string;
}

/**
 * The money moment, extracted from `DateProposalDetailScreen` so its
 * copy logic (what is held, when the expiry clock matters, the refund
 * cutoff, what a decline means) is directly component-testable without
 * mounting a whole screen or mocking the API client. Every sentence
 * comes from `domain/moneyMomentCopy.ts`; this component only decides
 * WHICH of those sentences apply for the current status/role, it never
 * writes new copy of its own.
 */
export function MoneySummary({ escrowAmountCents, currency, policySnapshot, status, viewerIsProposer, otherPartyLabel }: MoneySummaryProps): React.ReactElement {
  return (
    <View style={styles.box} accessible accessibilityLabel="About the payment hold on this date" testID="money-summary">
      <Body style={styles.title}>About the money</Body>
      <Body style={styles.text}>{holdHeadline(escrowAmountCents, currency, otherPartyLabel)}</Body>
      <Body style={styles.text}>{holdDetail(escrowAmountCents, currency)}</Body>
      {status === 'pending_acceptance' ? (
        <Body style={styles.text}>{acceptExpiryDetail(policySnapshot['date.accept_expiry_hours'])}</Body>
      ) : null}
      <Body style={styles.text}>{refundCutoffDetail(policySnapshot)}</Body>
      <Body style={styles.text}>{noShowDetail(policySnapshot)}</Body>
      {viewerIsProposer && status === 'pending_acceptance' ? (
        <Body style={styles.text}>{declineOutcomeDetail(otherPartyLabel)}</Body>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  box: { backgroundColor: colors.accentMuted, borderRadius: radii.md, padding: spacing.md, gap: spacing.sm },
  title: { fontWeight: '700', color: colors.accent },
  text: { color: colors.textPrimary },
});
