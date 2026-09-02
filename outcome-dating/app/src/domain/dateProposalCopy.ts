/**
 * Date-proposal status -> what a person actually reads. The state
 * machine's own values (see api/types.ts DateProposalStatus) are
 * internal vocabulary: `disputed`, `payment_failed`, `charged` read as
 * either alarming or meaningless out of context. Every sentence below
 * either comes straight from docs/ux-product-review.md's copy audit or
 * follows its explicit rules (blame-neutral payment language, "disputed"
 * never shown as the word "disputed", the generic decline stays vague
 * on purpose).
 */
import type { DateProposalStatus } from '../api/types';
import type { Tone } from '../components/StatusBadge';

export interface DateProposalStatusCopy {
  label: string;
  tone: Tone;
  detail: string;
}

/** `viewerIsProposer` only changes wording for the couple of statuses where the two sides genuinely see something different (who's waiting on whom); it never changes what's disclosed. */
export function describeDateProposalStatus(status: DateProposalStatus, viewerIsProposer: boolean): DateProposalStatusCopy {
  switch (status) {
    case 'draft':
      return { label: 'Starting...', tone: 'neutral', detail: 'Setting up this invite.' };
    case 'pending_acceptance':
      return viewerIsProposer
        ? { label: 'Waiting for a reply', tone: 'neutral', detail: 'This invite is open until it expires. Nothing is charged unless they accept.' }
        : { label: 'Date invite', tone: 'neutral', detail: 'Accept or decline whenever you like, before it expires.' };
    case 'accepted':
      return { label: 'Confirmed', tone: 'positive', detail: "You're both confirmed for this date." };
    case 'declined':
      return { label: 'Declined', tone: 'neutral', detail: 'They passed on this date.' };
    case 'expired':
      return { label: 'Expired', tone: 'neutral', detail: 'This invite expired without a response.' };
    case 'canceled':
      return { label: 'Canceled', tone: 'neutral', detail: 'This date was canceled.' };
    case 'payment_failed':
      return {
        label: 'Payment issue',
        tone: 'caution',
        detail: "We couldn't complete the card authorization for this date. Nothing was charged. Try a different payment method.",
      };
    case 'charged':
      return { label: 'Payment confirmed', tone: 'positive', detail: 'Both holds were completed. Your ticket is on its way.' };
    case 'ticketed':
      return { label: 'Ticket ready', tone: 'positive', detail: 'Your ticket is in your wallet.' };
    case 'completed':
      return { label: 'Completed', tone: 'positive', detail: 'This date is complete.' };
    case 'completed_unverified':
      return { label: 'Completed', tone: 'positive', detail: 'You both confirmed you showed up.' };
    case 'no_show':
      return { label: 'No-show reported', tone: 'caution', detail: 'This date was marked as a no-show.' };
    case 'refunded':
      return { label: 'Refunded', tone: 'neutral', detail: 'This hold was released back to the card, not charged.' };
    case 'disputed':
      // Product review: never surface the word "disputed" to a user.
      return {
        label: 'Waiting on confirmation',
        tone: 'caution',
        detail: "We're waiting on your date to also confirm you both showed up.",
      };
  }
}
