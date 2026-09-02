/**
 * Copy for the date-proposal money moment: the highest-stakes screen in
 * the product (task brief). Every sentence here either quotes or
 * closely follows docs/ux-product-review.md's "payment-hold moment"
 * finding almost verbatim (the exact suggested line: "Sending this
 * date invite places a $20 hold on your card, like a hotel deposit.
 * Nothing is charged unless [Name] accepts."), or extends that same
 * plain, blame-neutral register to the adjacent facts (decline,
 * cancel, refund cutoff) the review calls out as needing the same
 * care. No backend enum value (`payment_failed`, `disputed`,
 * `refunded`, `date.late_cancel_refund_percent`) is ever shown to a
 * user verbatim, this module is the one place that turns those into
 * sentences (see also domain/dateProposalCopy.ts for status labels).
 *
 * Pure and I/O-free on purpose: this is exactly the logic the task
 * brief asks to be covered by a component test.
 */
import { formatCents } from '../units/money';
import type { DateProposalPolicySnapshot } from '../api/types';

export function holdHeadline(amountCents: number, currency: string, recipientName: string): string {
  const amount = formatCents(amountCents, currency);
  return `Sending this date invite places a ${amount} hold on your card, like a hotel deposit. Nothing is charged unless ${recipientName} accepts.`;
}

export function holdDetail(amountCents: number, currency: string): string {
  const amount = formatCents(amountCents, currency);
  return `A hold reserves ${amount} on your card but does not move any money. If they accept, both of you are charged; if they decline, don't respond in time, or you cancel first, the hold is released and you're never charged.`;
}

export function acceptExpiryDetail(hours: number): string {
  const days = hours % 24 === 0 ? hours / 24 : null;
  const span = days ? `${days} day${days === 1 ? '' : 's'}` : `${hours} hours`;
  return `This invite stays open for ${span}. If it isn't answered in that time, it expires on its own and your hold is released.`;
}

export function refundCutoffDetail(policy: DateProposalPolicySnapshot): string {
  const cutoffHours = policy['date.full_refund_cutoff_hours'];
  const lateCancelPercent = policy['date.late_cancel_refund_percent'];
  const cutoffSpan = cutoffHours % 24 === 0 ? `${cutoffHours / 24} day${cutoffHours / 24 === 1 ? '' : 's'}` : `${cutoffHours} hours`;
  if (lateCancelPercent >= 100) {
    return `You can cancel any time before the date for a full refund. Canceling within ${cutoffSpan} of the date still refunds you in full.`;
  }
  if (lateCancelPercent <= 0) {
    return `Canceling more than ${cutoffSpan} before the date gets a full refund. Canceling closer to the date than that is not refunded, the venue has already reserved your spot.`;
  }
  return `Canceling more than ${cutoffSpan} before the date gets a full refund. Canceling closer to the date than that refunds ${lateCancelPercent}% of the hold.`;
}

export function noShowDetail(policy: DateProposalPolicySnapshot): string {
  const percent = policy['date.no_show_refund_percent'];
  if (percent >= 100) return "If a date doesn't happen and you weren't the reason, you're refunded in full.";
  if (percent <= 0) return "If you don't show up to a confirmed date, your hold is charged in full.";
  return `If you don't check in for a confirmed date, ${percent}% of the hold is charged.`;
}

export function declineOutcomeDetail(recipientName: string): string {
  return `If ${recipientName} declines, your hold is released automatically. You won't be charged, and there's nothing further to do.`;
}
