import { z } from 'zod';
import { getPool } from '../db/pool.js';
import { withTransaction } from '../db/tx.js';
import type { Ctx } from '../lib/ctx.js';
import { requireUserActor, withDb } from '../lib/ctx.js';
import { ConflictError, ForbiddenError, NotFoundError, ValidationError } from '../lib/errors.js';
import type { DateProposal, RedemptionMethod, VenueRedemption, Voucher } from '../domain/types.js';
import * as voucherService from './voucher.service.js';
import { InvalidSignatureError } from '../lib/signing.js';
import * as dateProposalService from './dateProposal.service.js';
import * as conversationService from './conversation.service.js';
import * as trustService from './trust.service.js';

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
 *   5. `conversation.service#establishConversation`.
 *   6. `trust.service#recordTrustEvent` for both participants.
 *
 * INVARIANT (actor scoping, spec §4.2): `redeemByStaff` requires
 * `ctx.actor.type === 'venue_staff'` and that actor's `venueId` must match
 * the voucher's `venue_id` — venue staff cannot redeem another venue's
 * tickets. `RedeemResult` (`Voucher`/`VenueRedemption`/`DateProposal`) has
 * no field for chats, emails, or payment card details by construction —
 * this module never queries `messages`, `users.email`, `payment_holds`, or
 * `payment_methods` at all, so there is nothing to accidentally leak.
 *
 * Venue settlement (§13.2 "margin percentage") is intentionally NOT
 * touched here — nothing in this module calls `ctx.payments` or
 * `payment.service.ts`. The user-facing escrow was already fully captured
 * back in `dateProposal.acceptDateProposal` (§14.2 Step 3); a real venue
 * payout pipeline (paying the venue its margin-adjusted share) would be a
 * separate downstream process reading `venue_redemptions`, out of this
 * module's frozen scope. This separation is also what makes §15.4's
 * "does not automatically settle venue payment" true almost for free: the
 * no-scan `confirmAttendance` path (owned by `dateProposal.service.ts`)
 * never writes a `venue_redemptions` row at all, so whatever downstream
 * process eventually pays venues from that table simply never sees an
 * unverified date — no separate "don't pay" flag is needed.
 */

export interface RedeemInput {
  code?: string;
  qrPayload?: string;
}

export interface RedeemResult {
  voucher: Voucher;
  redemption: VenueRedemption;
  dateProposal: DateProposal;
}

interface VoucherRowForRedemption {
  id: string;
  date_proposal_id: string;
  venue_id: string;
  status: string;
  expires_at: Date;
}

interface VenueRedemptionRow {
  id: string;
  voucher_id: string;
  venue_id: string;
  venue_staff_id: string | null;
  method: RedemptionMethod;
  created_at: Date;
}

function mapRedemption(row: VenueRedemptionRow): VenueRedemption {
  return {
    id: row.id,
    voucherId: row.voucher_id,
    venueId: row.venue_id,
    venueStaffId: row.venue_staff_id,
    method: row.method,
    createdAt: row.created_at,
  };
}

function resolveVoucherId(ctx: Ctx, input: RedeemInput): { voucherId: string | null; code: string | null; method: RedemptionMethod } {
  const hasCode = typeof input.code === 'string' && input.code.length > 0;
  const hasQr = typeof input.qrPayload === 'string' && input.qrPayload.length > 0;
  if (hasCode === hasQr) {
    throw new ValidationError('Exactly one of code or qrPayload must be provided');
  }
  if (hasQr) {
    let payload;
    try {
      payload = voucherService.verifyQrPayload(ctx, input.qrPayload!);
    } catch (err) {
      if (err instanceof InvalidSignatureError) throw new ValidationError('Invalid or tampered voucher code');
      throw err;
    }
    return { voucherId: payload.voucher_id, code: null, method: 'qr_scan' };
  }
  return { voucherId: null, code: input.code!, method: 'manual_code' };
}

async function runRedemption(ctx: Ctx, resolved: { voucherId: string | null; code: string | null; method: RedemptionMethod }, venueStaffId: string | null): Promise<RedeemResult> {
  return withTransaction(async (db) => {
    const txCtx = withDb(ctx, db);

    const { rows } = resolved.voucherId
      ? await db.query<VoucherRowForRedemption>(`SELECT id, date_proposal_id, venue_id, status, expires_at FROM vouchers WHERE id = $1 FOR UPDATE`, [resolved.voucherId])
      : await db.query<VoucherRowForRedemption>(`SELECT id, date_proposal_id, venue_id, status, expires_at FROM vouchers WHERE code = $1 FOR UPDATE`, [resolved.code]);
    const voucherRow = rows[0];
    if (!voucherRow) throw new NotFoundError('Voucher not found');

    if (ctx.actor.type === 'venue_staff' && voucherRow.venue_id !== ctx.actor.venueId) {
      throw new ForbiddenError('This voucher belongs to a different venue');
    }
    if (voucherRow.status !== 'issued') {
      throw new ConflictError(`Cannot redeem a voucher in status '${voucherRow.status}'`);
    }
    if (voucherRow.expires_at.getTime() < ctx.clock.now().getTime()) {
      throw new ConflictError('Voucher has expired');
    }

    const { rows: redemptionRows } = await db.query<VenueRedemptionRow>(
      `INSERT INTO venue_redemptions (voucher_id, venue_id, venue_staff_id, method)
       VALUES ($1, $2, $3, $4)
       RETURNING *`,
      [voucherRow.id, voucherRow.venue_id, venueStaffId, resolved.method],
    );
    const redemption = redemptionRows[0]!;

    const voucher = await voucherService.markRedeemed(txCtx, voucherRow.id);
    const dateProposal = await dateProposalService.markCompletedByRedemption(txCtx, voucherRow.date_proposal_id);
    await conversationService.establishConversation(txCtx, dateProposal.conversationId);
    await trustService.recordTrustEvent(txCtx, {
      userId: dateProposal.proposerId,
      eventType: 'completed_date',
      delta: 5,
      metadata: { dateProposalId: dateProposal.id, verified: true },
    });
    await trustService.recordTrustEvent(txCtx, {
      userId: dateProposal.recipientId,
      eventType: 'completed_date',
      delta: 5,
      metadata: { dateProposalId: dateProposal.id, verified: true },
    });

    return { voucher, redemption: mapRedemption(redemption), dateProposal };
  }, getPool());
}

/** Venue-staff-initiated redemption (`POST /venue/redeem`). Requires `ctx.actor.type === 'venue_staff'`. */
export async function redeemByStaff(ctx: Ctx, input: RedeemInput): Promise<RedeemResult> {
  if (ctx.actor.type !== 'venue_staff') throw new ForbiddenError('Only venue staff can redeem via this endpoint');
  const resolved = resolveVoucherId(ctx, input);
  return runRedemption(ctx, resolved, ctx.actor.venueStaffId);
}

/**
 * User-initiated variant (`POST /tickets/{ticketId}/redeem`, spec §24.9).
 * The resulting state transition is identical to `redeemByStaff` minus the
 * venue-staff actor check — `venue_staff_id` on the resulting
 * `venue_redemptions` row is null for this path. `ticketId` is a voucher
 * id; the caller must be a participant in that voucher's date proposal.
 */
export async function redeemBySelf(ctx: Ctx, ticketId: string, input: RedeemInput): Promise<RedeemResult> {
  const { userId } = requireUserActor(ctx);
  if (!z.string().uuid().safeParse(ticketId).success) throw new ValidationError('ticketId must be a uuid');

  const { rows } = await ctx.db.query<{ proposer_id: string; recipient_id: string }>(
    `SELECT dp.proposer_id, dp.recipient_id
     FROM vouchers v JOIN date_proposals dp ON dp.id = v.date_proposal_id
     WHERE v.id = $1`,
    [ticketId],
  );
  const proposal = rows[0];
  if (!proposal) throw new NotFoundError('Voucher not found');
  if (proposal.proposer_id !== userId && proposal.recipient_id !== userId) {
    throw new ForbiddenError('Not authorized to redeem this ticket');
  }

  const resolved = resolveVoucherId(ctx, input);
  if (resolved.voucherId && resolved.voucherId !== ticketId) {
    throw new ValidationError('qrPayload does not match this ticket');
  }
  // Force resolution to this ticket id regardless of code/QR ambiguity —
  // the route param is authoritative for which voucher is being redeemed.
  return runRedemption(ctx, { voucherId: ticketId, code: null, method: resolved.method }, null);
}

/** Venue staff's own redemption history (admin/venue dashboard use). Requires `ctx.actor.type === 'venue_staff'`, scoped to that actor's `venueId`. */
export async function getRedemptionHistory(ctx: Ctx, venueId: string): Promise<VenueRedemption[]> {
  if (ctx.actor.type !== 'venue_staff') throw new ForbiddenError('Only venue staff can view redemption history');
  if (ctx.actor.venueId !== venueId) throw new ForbiddenError('Cannot view another venue\'s redemption history');

  const { rows } = await ctx.db.query<VenueRedemptionRow>(
    `SELECT * FROM venue_redemptions WHERE venue_id = $1 ORDER BY created_at DESC`,
    [venueId],
  );
  return rows.map(mapRedemption);
}
