import type { Ctx } from '../lib/ctx.js';
import { NotImplementedError } from '../lib/errors.js';
import type { AttendanceConfirmation, DateProposal, PostDateFeedback } from '../domain/types.js';

/**
 * dateProposal.service — the §13-§15 date proposal orchestrator. This is
 * the module every other payment/voucher/conversation piece ultimately
 * serves; it owns the state machine in §13.3 and the payment choreography
 * in §14.2.
 * Spec: §13, §14, §15.4, §24.8, §25.2 (expiry job).
 *
 * Owning agent: D.
 *
 * State machine (spec §13.3, plus `completed_unverified` from §15.4):
 *   draft -> pending_acceptance -> accepted -> charged -> ticketed -> completed
 *                                                                   -> completed_unverified (§15.4, no venue scan)
 *   pending_acceptance -> declined | expired | canceled | payment_failed
 *   accepted -> payment_failed | canceled (late, no refund) | refunded (early cancel)
 *   ticketed/completed_unverified -> disputed (only one of two confirms, §15.4) | no_show
 *
 * INVARIANTS (see INTERFACES.md for the full table):
 *  - §14.3: nobody is charged until BOTH holds are authorized. `proposeDate`
 *    authorizes ONLY the proposer's hold; `acceptDateProposal` authorizes
 *    the recipient's, and ONLY once that succeeds does it call
 *    `payment.service#captureHold` for both sides.
 *  - §14.4/§14 orchestrator rule: `voucher.service#issueVoucher` is called
 *    only after both captures succeed, in the same transaction as the
 *    `status = 'ticketed'` write.
 *  - §14.5: any authorization/capture failure releases whichever hold(s)
 *    already succeeded and sets `status = 'payment_failed'` — never leaves
 *    one side charged while the other isn't.
 *  - §21.3: `policySnapshot` (via
 *    `ctx.config.snapshotPolicy(DATE_PROPOSAL_POLICY_KEYS)`) is captured
 *    once at `proposeDate` and used for every later expiry/refund
 *    calculation on this proposal — never re-read from live config.
 *  - Every status transition here that reaches a terminal-ish state
 *    (`ticketed`, `completed`, `completed_unverified`, `refunded`,
 *    `disputed`) fires the matching `notification.service.ts` event and,
 *    where the spec calls for it (completion), a `trust.service.ts` event
 *    — via `redemption.service.ts` for the venue-scan path, and directly
 *    here for the no-scan `confirmAttendance` path.
 */

export interface ProposeDateInput {
  conversationId: string;
  venueId: string;
  scheduledStart: Date;
  scheduledEnd: Date;
  optionalNote?: string;
}

/** Creates the proposal, snapshots policy, and authorizes the proposer's hold. Result status is 'pending_acceptance' on success or 'payment_failed' if authorization is declined (spec §14.2 Step 1). */
export async function proposeDate(ctx: Ctx, input: ProposeDateInput): Promise<DateProposal> {
  throw new NotImplementedError('dateProposal.proposeDate');
}

/**
 * Recipient accepts. Authorizes the recipient's hold; if that succeeds,
 * captures BOTH holds and issues the voucher (spec §14.2 Steps 2-4). If
 * the recipient's authorization fails, releases the proposer's hold and
 * sets `payment_failed` (spec §14.5). If a capture fails after both
 * authorizations succeeded, releases ALL holds and sets `payment_failed`
 * (spec §14.5 "Capture fails after authorization").
 */
export async function acceptDateProposal(ctx: Ctx, dateProposalId: string): Promise<DateProposal> {
  throw new NotImplementedError('dateProposal.acceptDateProposal');
}

export async function declineDateProposal(ctx: Ctx, dateProposalId: string): Promise<DateProposal> {
  throw new NotImplementedError('dateProposal.declineDateProposal');
}

/**
 * Cancellation, branching on the §14.7 policy read from the proposal's own
 * `policySnapshot` (never live config):
 *  - before acceptance: release the proposer's hold, `status = 'canceled'`.
 *  - after acceptance, more than `full_refund_cutoff_hours` before
 *    `scheduledStart`: refund both users, voucher canceled if issued,
 *    `status = 'refunded'`.
 *  - after acceptance, inside the cutoff: refund per
 *    `late_cancel_refund_percent` (0 by default), `status = 'canceled'`.
 */
export async function cancelDateProposal(ctx: Ctx, dateProposalId: string): Promise<DateProposal> {
  throw new NotImplementedError('dateProposal.cancelDateProposal');
}

/**
 * §15.4 no-scan fallback. Records the caller's confirmation. If both
 * users have confirmed within `date.no_scan_confirmation_hours` of
 * `scheduledEnd`: `status = 'completed_unverified'` and
 * `conversation.service#establishConversation` is called — this does NOT
 * settle venue payment (spec §15.4 "does not automatically settle venue
 * payment"). If the window elapses with only one confirmation:
 * `status = 'disputed'`.
 */
export async function confirmAttendance(ctx: Ctx, dateProposalId: string): Promise<{ dateProposal: DateProposal; confirmation: AttendanceConfirmation }> {
  throw new NotImplementedError('dateProposal.confirmAttendance');
}

export async function submitPostDateFeedback(ctx: Ctx, dateProposalId: string, input: { positive: boolean; wouldMeetAgain?: boolean; safetyConcern?: boolean; notes?: string }): Promise<PostDateFeedback> {
  throw new NotImplementedError('dateProposal.submitPostDateFeedback');
}

export async function getDateProposal(ctx: Ctx, dateProposalId: string): Promise<DateProposal> {
  throw new NotImplementedError('dateProposal.getDateProposal');
}

/** §25.2 job: pending_acceptance proposals past `policySnapshot['date.accept_expiry_hours']` -> 'expired', release the proposer's hold. */
export async function expireDuePendingProposals(ctx: Ctx): Promise<{ expired: number }> {
  throw new NotImplementedError('dateProposal.expireDuePendingProposals');
}

/** Admin/automated no-show marking (spec §13.3 `no_show`, feeds `trust.service.ts` negative factors, §6.2). Applies the `no_show_refund_percent` policy from the proposal's own snapshot. */
export async function markNoShow(ctx: Ctx, dateProposalId: string, noShowUserId: string): Promise<DateProposal> {
  throw new NotImplementedError('dateProposal.markNoShow');
}

/**
 * Called by `redemption.service.ts` only, immediately after a successful
 * venue scan, in the same transaction as the `venue_redemptions` insert
 * and `voucher.service#markRedeemed`. Sets `status = 'completed'` and
 * `completed_at` — NOT `completed_unverified` (that's the separate
 * no-scan path via `confirmAttendance`). Establishing the conversation and
 * firing trust events are `redemption.service.ts`'s responsibility, not
 * this function's, since they also apply to actions outside this module's
 * ownership (venue staff identity).
 */
export async function markCompletedByRedemption(ctx: Ctx, dateProposalId: string): Promise<DateProposal> {
  throw new NotImplementedError('dateProposal.markCompletedByRedemption');
}
