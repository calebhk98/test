import { describeDateProposalStatus } from '../dateProposalCopy';
import type { DateProposalStatus } from '../../api/types';

const ALL_STATUSES: DateProposalStatus[] = [
  'draft',
  'pending_acceptance',
  'accepted',
  'declined',
  'expired',
  'canceled',
  'payment_failed',
  'charged',
  'ticketed',
  'completed',
  'completed_unverified',
  'no_show',
  'refunded',
  'disputed',
];

describe('describeDateProposalStatus', () => {
  it('produces a label, tone, and detail sentence for every status the backend can return', () => {
    for (const status of ALL_STATUSES) {
      const copy = describeDateProposalStatus(status, true);
      expect(copy.label.length).toBeGreaterThan(0);
      expect(copy.detail.length).toBeGreaterThan(0);
      expect(['neutral', 'positive', 'caution', 'critical']).toContain(copy.tone);
    }
  });

  it('never shows the literal word "disputed" to a user, per the product review', () => {
    const copy = describeDateProposalStatus('disputed', true);
    expect(copy.label.toLowerCase()).not.toContain('disputed');
    expect(copy.detail.toLowerCase()).not.toContain('disputed');
    expect(copy.detail).toBe("We're waiting on your date to also confirm you both showed up.");
  });

  it('gives payment_failed blame-neutral copy that states nothing was charged', () => {
    const copy = describeDateProposalStatus('payment_failed', true);
    expect(copy.detail).toMatch(/nothing was charged/i);
  });

  it('keeps the generic decline template vague, on purpose (protects the other person\'s privacy)', () => {
    const copy = describeDateProposalStatus('declined', false);
    expect(copy.detail).toBe('They passed on this date.');
  });
});
