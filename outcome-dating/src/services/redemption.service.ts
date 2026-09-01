import type { Ctx } from '../lib/ctx.js';
import { NotImplementedError } from '../lib/errors.js';
import type { DateProposal, VenueRedemption, Voucher } from '../domain/types.js';

/**
 * redemption.service — venue-side voucher redemption.
 * Spec: §15.3, §24.9 (`POST /tickets/{ticketId}/redeem`,
 * `POST /venue/redeem`).
 *
 * Owning agent: D.
 *
 * This is the top of its own small dependency chain — it orchestrates
 * `voucher.service`, `dateProposal.service`, `conversation.service`, and
 * `trust.service` (all one-directional; none of them call back into this
 * module), all inside a single `withTransaction`:
 *
 *   1. `voucher.service#verifyQrPayload` (if redeeming by QR) or a direct
 *      `code` lookup, then load the voucher and confirm `status ===
 *      'issued'` and not expired.
 *   2. Insert the `venue_redemptions` row.
 *   3. `voucher.service#markRedeemed`.
 *   4. `dateProposal.service#markCompletedByRedemption`.
 *   5. `conversation.service#establishConversation` (spec §15.3 "conversation
 *      = established").
 *   6. `trust.service#recordTrustEvent` for both participants (spec §6.2
 *      "completed dates" positive factor).
 *
 * INVARIANT (actor scoping, spec §4.2): `redeemByStaff` requires
 * `ctx.actor.type === 'venue_staff'` and that actor's `venueId` must match
 * the voucher's `venue_id` — venue staff cannot redeem another venue's
 * tickets, cannot see chats (never touches `messages`), cannot see user
 * emails (only `Voucher`'s already-non-PII fields), and never see payment
 * card details (payment_holds/payment_methods are out of scope for this
 * module entirely).
 */

export interface RedeemInput {
  /** One of `code` or `qrPayload` must be provided. */
  code?: string;
  qrPayload?: string;
}

export interface RedeemResult {
  voucher: Voucher;
  redemption: VenueRedemption;
  dateProposal: DateProposal;
}

/** Venue-staff-initiated redemption (`POST /venue/redeem`). Requires `ctx.actor.type === 'venue_staff'`. */
export async function redeemByStaff(ctx: Ctx, input: RedeemInput): Promise<RedeemResult> {
  throw new NotImplementedError('redemption.redeemByStaff');
}

/**
 * User-initiated variant (`POST /tickets/{ticketId}/redeem`, spec §24.9).
 * Spec doesn't specify this path's exact real-world trigger (e.g. a venue
 * displaying a QR code the *customer* scans instead of staff scanning the
 * customer's), but the resulting state transition is identical to
 * `redeemByStaff` minus the venue-staff actor check — `venue_staff_id` on
 * the resulting `venue_redemptions` row is null for this path.
 */
export async function redeemBySelf(ctx: Ctx, ticketId: string, input: RedeemInput): Promise<RedeemResult> {
  throw new NotImplementedError('redemption.redeemBySelf');
}

/** Venue staff's own redemption history (admin/venue dashboard use). Requires `ctx.actor.type === 'venue_staff'`, scoped to that actor's `venueId`. */
export async function getRedemptionHistory(ctx: Ctx, venueId: string): Promise<VenueRedemption[]> {
  throw new NotImplementedError('redemption.getRedemptionHistory');
}
