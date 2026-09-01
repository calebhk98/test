import type { Ctx } from '../lib/ctx.js';
import { NotImplementedError } from '../lib/errors.js';
import type { Voucher, VoucherQrPayload } from '../domain/types.js';

/**
 * voucher.service — the ticket/voucher lifecycle.
 * Spec: §15.1, §15.2, §23.20, §24.9, §25.8 (expiry job).
 *
 * Owning agent: D.
 *
 * INVARIANT (spec §14.4, restated as the ticket-specific rule):
 * `issueVoucher` may only be called by `dateProposal.service.ts` after
 * BOTH `payment_holds` rows for the proposal are `captured` — this module
 * does not itself verify that (it trusts its caller), but the caller MUST,
 * and the two calls belong in the same transaction: a `date_proposals` row
 * must never reach `status = 'ticketed'` without a corresponding
 * `vouchers` row existing, and vice versa.
 *
 * QR payload: `sign<VoucherQrPayload>(payload, secret)` from
 * `src/lib/signing.ts` (spec §15.2's "signed JWT or similar signed
 * token" — see that module's header for why it's not literally a JWT).
 * The payload never includes payment card data (spec §15.2) — only ids
 * and an expiry.
 */

export async function issueVoucher(ctx: Ctx, dateProposalId: string): Promise<Voucher> {
  throw new NotImplementedError('voucher.issueVoucher');
}

export async function getVoucher(ctx: Ctx, voucherId: string): Promise<Voucher> {
  throw new NotImplementedError('voucher.getVoucher');
}

/** `GET /tickets` — every voucher for a proposal the caller participated in. */
export async function listMyVouchers(ctx: Ctx): Promise<Voucher[]> {
  throw new NotImplementedError('voucher.listMyVouchers');
}

/** Verifies the HMAC signature and decodes the payload (spec §15.2). Throws if the signature is invalid/tampered — does NOT check `status`/expiry itself (that's `redemption.service.ts`'s job, since a validly-signed-but-expired/already-redeemed voucher is a different failure mode than a forged one). */
export function verifyQrPayload(ctx: Ctx, compactToken: string): VoucherQrPayload {
  throw new NotImplementedError('voucher.verifyQrPayload');
}

/** §25.8 job: expire `issued` vouchers past `voucher.expiry_hours_after_date_end` from their proposal's `scheduled_end`. */
export async function expireDueVouchers(ctx: Ctx): Promise<{ expired: number }> {
  throw new NotImplementedError('voucher.expireDueVouchers');
}

/** Cancels an issued (not yet redeemed) voucher — called by `dateProposal.service.ts` on a post-ticketing cancellation/refund (spec §14.7, §15). Throws ConflictError if already redeemed. */
export async function cancelVoucher(ctx: Ctx, voucherId: string): Promise<Voucher> {
  throw new NotImplementedError('voucher.cancelVoucher');
}

/** Transitions `status: 'issued' -> 'redeemed'` and stamps `redeemed_at`. Only `redemption.service.ts` should call this, immediately after inserting the `venue_redemptions` row, in the same transaction. Throws ConflictError if not currently 'issued' (already redeemed/expired/canceled). */
export async function markRedeemed(ctx: Ctx, voucherId: string): Promise<Voucher> {
  throw new NotImplementedError('voucher.markRedeemed');
}
