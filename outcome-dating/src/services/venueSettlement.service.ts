import { z } from 'zod';
import { getPool } from '../db/pool.js';
import { withTransaction } from '../db/tx.js';
import type { Ctx } from '../lib/ctx.js';
import { withDb } from '../lib/ctx.js';
import { ForbiddenError, ValidationError } from '../lib/errors.js';
import type { Page, VenueSettlement, VenueSettlementStatus } from '../domain/types.js';
import * as ledger from './ledger.service.js';

/**
 * venueSettlement.service — venue payout settlement.
 * Spec: §15.4 (venue payment "does not automatically settle" for an
 * unverified date, implying it DOES settle for a verified one — see
 * docs/conformance.md Open Question OQ-8, resolved by product), §13.2/
 * §23.16 (`venues.margin_percent`).
 *
 * Decision-layer addition (not part of the original 5-agent parallel
 * build) — the spec gives every venue a `margin_percent` but never defines
 * a payout mechanism, ledger type, schema, or endpoint. This module is
 * that mechanism.
 *
 * EARNING RULE (the whole point of §15.4): a date proposal earns venue
 * settlement ONLY when BOTH of these hold —
 *   1. `date_proposals.status = 'completed'` (venue-VERIFIED completion,
 *      §15.3 — set only by `dateProposal.service#markCompletedByRedemption`,
 *      itself only called from `redemption.service.ts` after a real venue
 *      scan/manual-code redemption).
 *   2. A `venue_redemptions` row actually exists for that proposal's
 *      voucher (checked explicitly here, not merely inferred from status,
 *      as defense in depth against a future code path that might set
 *      `status = 'completed'` some other way).
 * `completed_unverified` (§15.4's no-scan fallback), `no_show`, `canceled`,
 * `refunded`, and `disputed` proposals are excluded by construction: the
 * settlement-candidate query below filters on `status = 'completed'` AND
 * the redemption join, so none of those statuses is ever even a candidate
 * row — see `tests/unit/venueSettlement.test.ts` for the negative-case
 * proof against each one (that IS the point of this design, per §15.4).
 *
 * PAYOUT MATH (integer minor units only, per INTERFACES.md's money
 * invariant): `venuePayoutCents = Math.floor(grossCents * marginPercent /
 * 100)`, `platformCents = grossCents - venuePayoutCents` — computed by
 * subtraction from the gross, not by a second `Math.floor` call, so
 * `venuePayoutCents + platformCents === grossCents` holds EXACTLY, always
 * (see `computeVenuePayout`, unit-tested directly for the rounding case
 * where `marginPercent` doesn't divide evenly into cents — the same
 * "round down, in the platform's favor" rule `payment.service.ts` uses
 * for refunds, §14.7/OQ-6).
 *
 * IDEMPOTENCY: `venue_settlements.date_proposal_id` is `UNIQUE` (see
 * `db/migrations/007_decisions.sql`) — one settlement per date proposal,
 * ever. `settleDueVenuePayouts` re-checks for an existing row inside the
 * same transaction as the insert (`ON CONFLICT (date_proposal_id) DO
 * NOTHING`) so a retried/concurrent run never double-pays; the caller-
 * facing `settled` count only reflects rows THIS call actually inserted.
 *
 * CALL GRAPH: reads `date_proposals`/`venues`/`vouchers`/`venue_redemptions`/
 * `payment_holds` directly (read-only), matching the established pattern
 * elsewhere in this codebase (e.g. `discovery.service.ts` reading
 * `profiles`/`interests` directly rather than through another module's
 * service functions) rather than adding new "may call" edges into
 * `dateProposal.service.ts`'s frozen, documented call graph. The one
 * outgoing service call is `ledger.service#recordEntry`, appending the
 * `venue_payout` ledger row (extended in `db/migrations/007_decisions.sql`
 * + `LedgerEntryType`, see domain/types.ts).
 *
 * NOT REGISTERED AS A JOB: this module exports `settleDueVenuePayouts`
 * (the job body) but does not itself schedule anything — `src/jobs/**` is
 * owned by a different, concurrently-working agent. See the final report
 * for the exact function name/signature to wire up.
 */

interface SettlementCandidateRow {
  date_proposal_id: string;
  venue_id: string;
  margin_percent: number;
}

async function loadSettlementCandidates(ctx: Ctx): Promise<SettlementCandidateRow[]> {
  const { rows } = await ctx.db.query<SettlementCandidateRow>(
    `SELECT dp.id AS date_proposal_id, dp.venue_id, v.margin_percent
       FROM date_proposals dp
       JOIN venues v ON v.id = dp.venue_id
       JOIN vouchers vo ON vo.date_proposal_id = dp.id
       JOIN venue_redemptions vr ON vr.voucher_id = vo.id
      WHERE dp.status = 'completed'
        AND NOT EXISTS (SELECT 1 FROM venue_settlements vs WHERE vs.date_proposal_id = dp.id)
      ORDER BY dp.completed_at ASC NULLS LAST, dp.id ASC`,
  );
  return rows;
}

async function grossCapturedCentsForProposal(ctx: Ctx, dateProposalId: string): Promise<number> {
  const { rows } = await ctx.db.query<{ sum: string | null }>(
    `SELECT COALESCE(sum(amount_cents), 0)::text AS sum
       FROM payment_holds
      WHERE date_proposal_id = $1 AND status = 'captured'`,
    [dateProposalId],
  );
  return Number(rows[0]?.sum ?? '0');
}

/**
 * Pure payout split for one date proposal's gross captured escrow. Exported
 * directly so the "payout + platform === gross, exactly" invariant and the
 * floor-rounding rule are unit-testable without a database — this is
 * exactly where a rounding bug would hide (spec's own "money hazard" note,
 * mirrored from `dateProposal.service#percentOfCents`'s doc).
 */
export function computeVenuePayout(grossCents: number, marginPercent: number): { venuePayoutCents: number; platformCents: number } {
  if (!Number.isInteger(grossCents) || grossCents < 0) {
    throw new ValidationError('grossCents must be a non-negative integer');
  }
  if (!Number.isFinite(marginPercent) || marginPercent < 0 || marginPercent > 100) {
    throw new ValidationError('marginPercent must be between 0 and 100');
  }
  const venuePayoutCents = Math.floor((grossCents * marginPercent) / 100);
  const platformCents = grossCents - venuePayoutCents;
  return { venuePayoutCents, platformCents };
}

interface VenueSettlementRow {
  id: string;
  venue_id: string;
  date_proposal_id: string;
  gross_escrow_cents: string;
  margin_percent_applied: number;
  venue_payout_cents: string;
  platform_cents: string;
  status: VenueSettlementStatus;
  settlement_period: string;
  created_at: Date;
  settled_at: Date | null;
  processor_reference: string | null;
}

function mapSettlement(row: VenueSettlementRow): VenueSettlement {
  return {
    id: row.id,
    venueId: row.venue_id,
    dateProposalId: row.date_proposal_id,
    grossEscrowCents: Number(row.gross_escrow_cents),
    marginPercentApplied: Number(row.margin_percent_applied),
    venuePayoutCents: Number(row.venue_payout_cents),
    platformCents: Number(row.platform_cents),
    status: row.status,
    settlementPeriod: row.settlement_period,
    createdAt: row.created_at,
    settledAt: row.settled_at,
    processorReference: row.processor_reference,
  };
}

function settlementPeriodFor(now: Date): string {
  return now.toISOString().slice(0, 7); // "YYYY-MM", UTC
}

/** Settles exactly one date proposal, idempotently. Returns `null` if it was already settled (by this call racing another, or a prior run) or has no captured escrow to settle. */
async function settleOneDateProposal(
  ctx: Ctx,
  dateProposalId: string,
  venueId: string,
  marginPercent: number,
): Promise<VenueSettlement | null> {
  return withTransaction(async (db) => {
    const txCtx = withDb(ctx, db);

    // Re-check inside the transaction — the caller's candidate list was
    // read outside any lock, so a concurrent settlement run could have
    // already inserted a row for this proposal in between.
    const { rows: existing } = await db.query<{ id: string }>(
      `SELECT id FROM venue_settlements WHERE date_proposal_id = $1`,
      [dateProposalId],
    );
    if (existing[0]) return null;

    const grossCents = await grossCapturedCentsForProposal(txCtx, dateProposalId);
    if (grossCents <= 0) return null; // nothing captured to settle — should not happen for a 'completed' proposal, but never pay out of nothing.

    const { venuePayoutCents, platformCents } = computeVenuePayout(grossCents, marginPercent);
    const now = txCtx.clock.now();
    const processorReference = `venue-settlement:${dateProposalId}`;

    const { rows: inserted } = await db.query<VenueSettlementRow>(
      `INSERT INTO venue_settlements
         (venue_id, date_proposal_id, gross_escrow_cents, margin_percent_applied, venue_payout_cents, platform_cents, status, settlement_period, created_at, settled_at, processor_reference)
       VALUES ($1, $2, $3, $4, $5, $6, 'settled', $7, $8, $8, $9)
       ON CONFLICT (date_proposal_id) DO NOTHING
       RETURNING *`,
      [venueId, dateProposalId, grossCents, marginPercent, venuePayoutCents, platformCents, settlementPeriodFor(now), now, processorReference],
    );
    const row = inserted[0];
    if (!row) return null; // lost a race against a concurrent settlement run

    await ledger.recordEntry(txCtx, {
      userId: null,
      venueId,
      dateProposalId,
      paymentHoldId: null,
      type: 'venue_payout',
      amountCents: venuePayoutCents,
      currency: 'usd',
      processorReference,
      metadata: { grossCents, marginPercent, platformCents },
    });

    return mapSettlement(row);
  }, getPool());
}

export interface SettleDueVenuePayoutsResult {
  settled: number;
  totalVenuePayoutCents: number;
  totalPlatformCents: number;
  settlements: VenueSettlement[];
}

/**
 * The job body (§25-style automated job — see this module's header for why
 * it is NOT registered in `src/jobs/**` here). Finds every `completed`,
 * venue-redeemed date proposal without an existing settlement and settles
 * each one exactly once. Safe to call repeatedly/concurrently: idempotent
 * per date proposal (see module header).
 */
export async function settleDueVenuePayouts(ctx: Ctx): Promise<SettleDueVenuePayoutsResult> {
  const candidates = await loadSettlementCandidates(ctx);

  const result: SettleDueVenuePayoutsResult = { settled: 0, totalVenuePayoutCents: 0, totalPlatformCents: 0, settlements: [] };
  for (const candidate of candidates) {
    const settlement = await settleOneDateProposal(ctx, candidate.date_proposal_id, candidate.venue_id, Number(candidate.margin_percent));
    if (!settlement) continue;
    result.settled++;
    result.totalVenuePayoutCents += settlement.venuePayoutCents;
    result.totalPlatformCents += settlement.platformCents;
    result.settlements.push(settlement);
  }
  return result;
}

/** Settles one specific, already-`completed`+redeemed date proposal on demand (e.g. an admin "settle now" action). Idempotent — a no-op (`null`) if not eligible or already settled. */
export async function settleOneDateProposalById(ctx: Ctx, dateProposalId: string): Promise<VenueSettlement | null> {
  if (!z.string().uuid().safeParse(dateProposalId).success) throw new ValidationError('That is not a valid id.');

  const { rows } = await ctx.db.query<SettlementCandidateRow>(
    `SELECT dp.id AS date_proposal_id, dp.venue_id, v.margin_percent
       FROM date_proposals dp
       JOIN venues v ON v.id = dp.venue_id
       JOIN vouchers vo ON vo.date_proposal_id = dp.id
       JOIN venue_redemptions vr ON vr.voucher_id = vo.id
      WHERE dp.status = 'completed' AND dp.id = $1`,
    [dateProposalId],
  );
  const candidate = rows[0];
  if (!candidate) return null; // not eligible: not completed, or never venue-redeemed (§15.4)

  return settleOneDateProposal(ctx, candidate.date_proposal_id, candidate.venue_id, Number(candidate.margin_percent));
}

function requireAdminOrSystemActor(ctx: Ctx): void {
  if (ctx.actor.type !== 'admin' && ctx.actor.type !== 'system') {
    throw new ForbiddenError('Admin or system actor required to view venue settlements');
  }
}

/** Admin payout view (spec §27-style admin surface — mirrors `ledger.service#listEntriesForUser`'s pagination shape). Omit `venueId` to list across all venues. */
export async function listVenueSettlements(
  ctx: Ctx,
  params?: { venueId?: string; cursor?: string; limit?: number },
): Promise<Page<VenueSettlement>> {
  requireAdminOrSystemActor(ctx);
  const limit = Math.min(Math.max(params?.limit ?? 50, 1), 200);
  const offset = params?.cursor ? Number(params.cursor) : 0;

  const values: unknown[] = [];
  let whereClause = '';
  if (params?.venueId) {
    if (!z.string().uuid().safeParse(params.venueId).success) throw new ValidationError('That is not a valid id.');
    values.push(params.venueId);
    whereClause = `WHERE venue_id = $${values.length}`;
  }
  values.push(limit + 1, offset);

  const { rows } = await ctx.db.query<VenueSettlementRow>(
    `SELECT * FROM venue_settlements ${whereClause}
      ORDER BY created_at DESC, id DESC
      LIMIT $${values.length - 1} OFFSET $${values.length}`,
    values,
  );

  const hasMore = rows.length > limit;
  const page = hasMore ? rows.slice(0, limit) : rows;
  return { items: page.map(mapSettlement), nextCursor: hasMore ? String(offset + limit) : null };
}

/** Sum of `venuePayoutCents` for `venueId` across every settlement (admin/venue-dashboard convenience — spec §13.2 margin reporting). */
export async function totalSettledPayoutForVenue(ctx: Ctx, venueId: string): Promise<number> {
  requireAdminOrSystemActor(ctx);
  if (!z.string().uuid().safeParse(venueId).success) throw new ValidationError('That is not a valid id.');
  const { rows } = await ctx.db.query<{ sum: string | null }>(
    `SELECT COALESCE(sum(venue_payout_cents), 0)::text AS sum FROM venue_settlements WHERE venue_id = $1 AND status = 'settled'`,
    [venueId],
  );
  return Number(rows[0]?.sum ?? '0');
}
