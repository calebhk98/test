import {
  acceptExpiryDetail,
  declineOutcomeDetail,
  holdDetail,
  holdHeadline,
  noShowDetail,
  refundCutoffDetail,
} from '../moneyMomentCopy';
import type { DateProposalPolicySnapshot } from '../../api/types';

const policy: DateProposalPolicySnapshot = {
  'date.escrow_amount_cents': 2000,
  'date.accept_expiry_hours': 48,
  'date.full_refund_cutoff_hours': 24,
  'date.late_cancel_refund_percent': 50,
  'date.no_show_refund_percent': 0,
  'date.no_scan_confirmation_hours': 6,
};

describe('holdHeadline, the single most important sentence in the app', () => {
  it('says "hold" and states plainly that nothing is charged unless the other person accepts', () => {
    const text = holdHeadline(2000, 'usd', 'Jordan');
    expect(text).toContain('hold');
    expect(text).toContain('Nothing is charged unless Jordan accepts');
  });

  it('renders the exact dollar amount from cents, in the given currency', () => {
    expect(holdHeadline(2000, 'usd', 'Jordan')).toContain('$20.00');
    expect(holdHeadline(1500, 'usd', 'Sam')).toContain('$15.00');
  });

  it('never leaks a raw backend enum value (snake_case internal state) into user-facing copy', () => {
    const allCopy = [
      holdHeadline(2000, 'usd', 'Jordan'),
      holdDetail(2000, 'usd'),
      acceptExpiryDetail(48),
      refundCutoffDetail(policy),
      noShowDetail(policy),
      declineOutcomeDetail('Jordan'),
    ].join(' ');
    // Backend status values are snake_case (payment_failed, no_show, ...);
    // plain English words like "refund"/"refunded" are fine, an
    // underscore-joined token is the actual leak this guards against.
    expect(allCopy).not.toMatch(/[a-z]+_[a-z]+/);
  });
});

describe('holdDetail', () => {
  it('explains a hold reserves money without moving it, and names every release path', () => {
    const text = holdDetail(2000, 'usd');
    expect(text).toMatch(/does not move any money/);
    expect(text).toMatch(/decline/);
    expect(text).toMatch(/cancel/);
    expect(text).toMatch(/released/);
  });
});

describe('acceptExpiryDetail', () => {
  it('reads as a fact ("stays open for"), never a countdown, per the product review', () => {
    const text = acceptExpiryDetail(48);
    expect(text).toContain('stays open for');
    expect(text).not.toMatch(/\d+h\s*\d*m?\s*left/i);
  });

  it('converts whole-day hour counts to a day figure', () => {
    expect(acceptExpiryDetail(48)).toContain('2 days');
    expect(acceptExpiryDetail(24)).toContain('1 day');
  });

  it('keeps an hour figure when it does not divide evenly into days', () => {
    expect(acceptExpiryDetail(36)).toContain('36 hours');
  });
});

describe('refundCutoffDetail', () => {
  it('describes a full refund before the cutoff and a partial refund after it', () => {
    const text = refundCutoffDetail(policy);
    expect(text).toMatch(/full refund/);
    expect(text).toContain('50%');
  });

  it('describes a zero late-cancel refund as no refund, not "0%"', () => {
    const text = refundCutoffDetail({ ...policy, 'date.late_cancel_refund_percent': 0 });
    expect(text).toMatch(/not refunded/);
    expect(text).not.toContain('0%');
  });

  it('describes a 100% late-cancel refund as always fully refundable', () => {
    const text = refundCutoffDetail({ ...policy, 'date.late_cancel_refund_percent': 100 });
    expect(text).toMatch(/full refund/);
    expect(text).not.toContain('100%');
  });
});

describe('noShowDetail', () => {
  it('is blame-neutral phrasing, matching the product review\'s "not a generic payment failed" rule', () => {
    const text = noShowDetail(policy);
    expect(text).not.toMatch(/no_show/);
  });

  it('describes full forfeiture plainly when the refund percent is zero', () => {
    expect(noShowDetail({ ...policy, 'date.no_show_refund_percent': 0 })).toMatch(/charged in full/);
  });

  it('describes full refund plainly when the refund percent is 100', () => {
    expect(noShowDetail({ ...policy, 'date.no_show_refund_percent': 100 })).toMatch(/refunded in full/);
  });
});

describe('declineOutcomeDetail', () => {
  it('reassures the proposer nothing further is owed and no charge happens', () => {
    const text = declineOutcomeDetail('Jordan');
    expect(text).toMatch(/released automatically/);
    expect(text).toMatch(/won't be charged/);
  });
});
