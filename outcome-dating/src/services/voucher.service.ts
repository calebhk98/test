import { z } from 'zod';
import type { Ctx } from '../lib/ctx.js';
import { requireUserActor } from '../lib/ctx.js';
import { ConflictError, ForbiddenError, NotFoundError, ValidationError } from '../lib/errors.js';
import { addHours } from '../lib/time.js';
import { newHumanCode, newId } from '../lib/ids.js';
import { sign, verify, InvalidSignatureError } from '../lib/signing.js';
import { getEnv } from '../config/env.js';
import type { Voucher, VoucherQrPayload, VoucherStatus } from '../domain/types.js';

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
 * `vouchers` row existing, and vice versa. `issueVoucher` is idempotent on
 * `date_proposal_id` (the table's own UNIQUE constraint) — a retried call
 * returns the already-issued voucher rather than erroring.
 *
 * QR payload: `sign<VoucherQrPayload>(payload, secret)` from
 * `src/lib/signing.ts` (spec §15.2's "signed JWT or similar signed
 * token"). The payload never includes payment card data, user emails, or
 * chat content (spec §15.2, §4.2) — only ids and an expiry, matching
 * `VoucherQrPayload` exactly (`voucher_id`, `venue_id`, `date_proposal_id`,
 * `expires_at`).
 *
 * SIGNING SECRET: `Ctx` carries no dedicated "signing secret" field, and
 * `src/config/env.ts` (shared infra, not owned by this agent) has no
 * `VOUCHER_QR_SECRET`. Rather than add a new env var to a file outside
 * this agent's ownership without cross-agent coordination, vouchers are
 * signed with the same `AUTH_TOKEN_SECRET` used for auth tokens (both are
 * HMAC-SHA256 compact tokens via the same `sign`/`verify` helpers) — this
 * is noted in the final report as a candidate follow-up (a dedicated
 * voucher secret would let the two token families be rotated
 * independently) rather than made silently.
 *
 * `voucher.expiry_hours_after_date_end` is a `scope: 'snapshot'` config
 * key (spec §21.3/§21.4) with nowhere to persist a JSON snapshot on the
 * `vouchers` row (§23.20 has no `policy_snapshot` column) — the snapshot
 * semantics are instead realized by computing `expires_at` once, at
 * `issueVoucher` time, from the *current* config value and baking it into
 * the concrete timestamp column. A later `config.set` changes future
 * issuances only; it can never retroactively move an already-issued
 * voucher's `expires_at`.
 */

function voucherSecret(): string {
  return getEnv().AUTH_TOKEN_SECRET;
}

interface VoucherRow {
  id: string;
  date_proposal_id: string;
  venue_id: string;
  code: string;
  qr_payload: string;
  status: VoucherStatus;
  issued_at: Date;
  expires_at: Date;
  redeemed_at: Date | null;
}

function mapVoucher(row: VoucherRow): Voucher {
  return {
    id: row.id,
    dateProposalId: row.date_proposal_id,
    venueId: row.venue_id,
    code: row.code,
    qrPayload: row.qr_payload,
    status: row.status,
    issuedAt: row.issued_at,
    expiresAt: row.expires_at,
    redeemedAt: row.redeemed_at,
  };
}

interface DateProposalForVoucher {
  scheduled_end: Date;
  proposer_id: string;
  recipient_id: string;
}

async function loadDateProposalForVoucher(ctx: Ctx, dateProposalId: string): Promise<DateProposalForVoucher> {
  const { rows } = await ctx.db.query<DateProposalForVoucher>(
    `SELECT scheduled_end, proposer_id, recipient_id FROM date_proposals WHERE id = $1`,
    [dateProposalId],
  );
  if (!rows[0]) throw new NotFoundError('Date proposal not found');
  return rows[0];
}

/** Called by `dateProposal.service.ts` only, after both holds are captured (see module header). */
export async function issueVoucher(ctx: Ctx, dateProposalId: string): Promise<Voucher> {
  if (!z.string().uuid().safeParse(dateProposalId).success) throw new ValidationError('dateProposalId must be a uuid');

  const { rows: existingRows } = await ctx.db.query<VoucherRow>(`SELECT * FROM vouchers WHERE date_proposal_id = $1`, [dateProposalId]);
  if (existingRows[0]) return mapVoucher(existingRows[0]); // idempotent — already issued

  const { rows: proposalRows } = await ctx.db.query<{ venue_id: string; scheduled_end: Date }>(
    `SELECT venue_id, scheduled_end FROM date_proposals WHERE id = $1`,
    [dateProposalId],
  );
  const proposal = proposalRows[0];
  if (!proposal) throw new NotFoundError('Date proposal not found');

  const expiryHours = await ctx.config.get('voucher.expiry_hours_after_date_end');
  const expiresAt = addHours(proposal.scheduled_end, expiryHours);

  const voucherId = newId();
  const payload: VoucherQrPayload = {
    voucher_id: voucherId,
    venue_id: proposal.venue_id,
    date_proposal_id: dateProposalId,
    expires_at: expiresAt.toISOString(),
  };
  const { compact } = sign(payload, voucherSecret());

  const { rows } = await ctx.db.query<VoucherRow>(
    `INSERT INTO vouchers (id, date_proposal_id, venue_id, code, qr_payload, status, issued_at, expires_at)
     VALUES ($1, $2, $3, $4, $5, 'issued', $6, $7)
     ON CONFLICT (date_proposal_id) DO NOTHING
     RETURNING *`,
    [voucherId, dateProposalId, proposal.venue_id, newHumanCode(), compact, ctx.clock.now(), expiresAt],
  );
  if (rows[0]) return mapVoucher(rows[0]);

  // Lost a race against a concurrent issuer for the same proposal — fetch what won.
  const { rows: winner } = await ctx.db.query<VoucherRow>(`SELECT * FROM vouchers WHERE date_proposal_id = $1`, [dateProposalId]);
  return mapVoucher(winner[0]!);
}

async function assertCanViewVoucher(ctx: Ctx, dateProposalId: string): Promise<void> {
  if (ctx.actor.type === 'admin' || ctx.actor.type === 'system') return;
  if (ctx.actor.type !== 'user') throw new ForbiddenError('Not authorized to view this voucher');
  const proposal = await loadDateProposalForVoucher(ctx, dateProposalId);
  if (proposal.proposer_id !== ctx.actor.userId && proposal.recipient_id !== ctx.actor.userId) {
    throw new ForbiddenError('Not authorized to view this voucher');
  }
}

export async function getVoucher(ctx: Ctx, voucherId: string): Promise<Voucher> {
  if (!z.string().uuid().safeParse(voucherId).success) throw new ValidationError('voucherId must be a uuid');
  const { rows } = await ctx.db.query<VoucherRow>(`SELECT * FROM vouchers WHERE id = $1`, [voucherId]);
  if (!rows[0]) throw new NotFoundError('Voucher not found');
  await assertCanViewVoucher(ctx, rows[0].date_proposal_id);
  return mapVoucher(rows[0]);
}

/** `GET /tickets` — every voucher for a proposal the caller participated in. */
export async function listMyVouchers(ctx: Ctx): Promise<Voucher[]> {
  const { userId } = requireUserActor(ctx);
  const { rows } = await ctx.db.query<VoucherRow>(
    `SELECT v.* FROM vouchers v
     JOIN date_proposals dp ON dp.id = v.date_proposal_id
     WHERE dp.proposer_id = $1 OR dp.recipient_id = $1
     ORDER BY v.issued_at DESC`,
    [userId],
  );
  return rows.map(mapVoucher);
}

/**
 * Verifies the HMAC signature and decodes the payload (spec §15.2). Throws
 * `InvalidSignatureError` (from `src/lib/signing.ts`) if the signature is
 * invalid/tampered — does NOT check `status`/expiry itself (that's
 * `redemption.service.ts`'s job, since a validly-signed-but-expired/
 * already-redeemed voucher is a different failure mode than a forged one).
 */
export function verifyQrPayload(ctx: Ctx, compactToken: string): VoucherQrPayload {
  return verify<VoucherQrPayload>(compactToken, voucherSecret());
}

/** §25.8 job: expire `issued` vouchers past `voucher.expiry_hours_after_date_end` from their proposal's `scheduled_end` — realized here simply as `expires_at < ctx.clock.now()`, since `expires_at` already bakes that policy in at issuance time. */
export async function expireDueVouchers(ctx: Ctx): Promise<{ expired: number }> {
  const { rowCount } = await ctx.db.query(`UPDATE vouchers SET status = 'expired' WHERE status = 'issued' AND expires_at < $1`, [ctx.clock.now()]);
  return { expired: rowCount ?? 0 };
}

/** Cancels an issued (not yet redeemed) voucher — called by `dateProposal.service.ts` on a post-ticketing cancellation/refund (spec §14.7, §15). Throws ConflictError if not currently 'issued'. */
export async function cancelVoucher(ctx: Ctx, voucherId: string): Promise<Voucher> {
  if (!z.string().uuid().safeParse(voucherId).success) throw new ValidationError('voucherId must be a uuid');
  const { rows } = await ctx.db.query<VoucherRow>(`SELECT * FROM vouchers WHERE id = $1`, [voucherId]);
  const voucher = rows[0];
  if (!voucher) throw new NotFoundError('Voucher not found');
  if (voucher.status === 'canceled') return mapVoucher(voucher); // idempotent
  if (voucher.status !== 'issued') throw new ConflictError(`Cannot cancel a voucher in status '${voucher.status}'`);

  const { rows: updated } = await ctx.db.query<VoucherRow>(
    `UPDATE vouchers SET status = 'canceled' WHERE id = $1 AND status = 'issued' RETURNING *`,
    [voucherId],
  );
  return mapVoucher(updated[0]!);
}

/**
 * Transitions `status: 'issued' -> 'redeemed'` and stamps `redeemed_at`.
 * Only `redemption.service.ts` should call this, immediately after
 * inserting the `venue_redemptions` row, in the same transaction — so this
 * function deliberately uses `ctx.db` as given and never opens its own
 * transaction. Throws ConflictError if not currently 'issued' (already
 * redeemed/expired/canceled) or if past `expires_at`.
 */
export async function markRedeemed(ctx: Ctx, voucherId: string): Promise<Voucher> {
  if (!z.string().uuid().safeParse(voucherId).success) throw new ValidationError('voucherId must be a uuid');
  const { rows } = await ctx.db.query<VoucherRow>(`SELECT * FROM vouchers WHERE id = $1 FOR UPDATE`, [voucherId]);
  const voucher = rows[0];
  if (!voucher) throw new NotFoundError('Voucher not found');
  if (voucher.status !== 'issued') throw new ConflictError(`Cannot redeem a voucher in status '${voucher.status}'`);
  if (voucher.expires_at.getTime() < ctx.clock.now().getTime()) throw new ConflictError('Voucher has expired');

  const { rows: updated } = await ctx.db.query<VoucherRow>(
    `UPDATE vouchers SET status = 'redeemed', redeemed_at = $2 WHERE id = $1 AND status = 'issued' RETURNING *`,
    [voucherId, ctx.clock.now()],
  );
  if (!updated[0]) throw new ConflictError('Voucher was redeemed concurrently');
  return mapVoucher(updated[0]);
}

export { InvalidSignatureError };
