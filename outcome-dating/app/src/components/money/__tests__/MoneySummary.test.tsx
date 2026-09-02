import React from 'react';
import { render } from '@testing-library/react-native';
import { MoneySummary } from '../MoneySummary';
import type { DateProposalPolicySnapshot } from '../../../api/types';

const policy: DateProposalPolicySnapshot = {
  'date.escrow_amount_cents': 2000,
  'date.accept_expiry_hours': 48,
  'date.full_refund_cutoff_hours': 24,
  'date.late_cancel_refund_percent': 50,
  'date.no_show_refund_percent': 0,
  'date.no_scan_confirmation_hours': 6,
};

describe('MoneySummary, the money moment', () => {
  it('states the hold amount and that nothing is charged unless the other person accepts', () => {
    const { getByText } = render(
      <MoneySummary
        escrowAmountCents={2000}
        currency="usd"
        policySnapshot={policy}
        status="pending_acceptance"
        viewerIsProposer
        otherPartyLabel="Jordan"
      />,
    );
    expect(getByText(/Sending this date invite places a \$20\.00 hold on your card/)).toBeTruthy();
    expect(getByText(/Nothing is charged unless Jordan accepts/)).toBeTruthy();
  });

  it('shows the expiry-window fact only while the invite is still pending', () => {
    const pending = render(
      <MoneySummary
        escrowAmountCents={2000}
        currency="usd"
        policySnapshot={policy}
        status="pending_acceptance"
        viewerIsProposer
        otherPartyLabel="Jordan"
      />,
    );
    expect(pending.getByText(/stays open for/)).toBeTruthy();

    const accepted = render(
      <MoneySummary
        escrowAmountCents={2000}
        currency="usd"
        policySnapshot={policy}
        status="accepted"
        viewerIsProposer
        otherPartyLabel="Jordan"
      />,
    );
    expect(accepted.queryByText(/stays open for/)).toBeNull();
  });

  it('only tells the proposer about the decline outcome while pending, never the recipient', () => {
    const asProposer = render(
      <MoneySummary
        escrowAmountCents={2000}
        currency="usd"
        policySnapshot={policy}
        status="pending_acceptance"
        viewerIsProposer
        otherPartyLabel="Jordan"
      />,
    );
    expect(asProposer.getByText(/If Jordan declines, your hold is released automatically/)).toBeTruthy();

    const asRecipient = render(
      <MoneySummary
        escrowAmountCents={2000}
        currency="usd"
        policySnapshot={policy}
        status="pending_acceptance"
        viewerIsProposer={false}
        otherPartyLabel="Jordan"
      />,
    );
    expect(asRecipient.queryByText(/your hold is released automatically/)).toBeNull();
  });

  it('always shows the refund cutoff and no-show policy, regardless of status', () => {
    const { getByText } = render(
      <MoneySummary
        escrowAmountCents={2000}
        currency="usd"
        policySnapshot={policy}
        status="completed"
        viewerIsProposer={false}
        otherPartyLabel="Jordan"
      />,
    );
    expect(getByText(/full refund/)).toBeTruthy();
    expect(getByText(/charged in full/)).toBeTruthy();
  });
});
