/**
 * src/http/serializers/venue.ts, every response shape reachable by a
 * `venue_staff` actor.
 *
 * HARD INVARIANT (spec §4.2, C-4.2.4/5/6): venue staff MUST NOT see chats,
 * emails, or payment card/hold data. `redemption.service.ts`'s own
 * `RedeemResult` (`{voucher, redemption, dateProposal}`) is already narrow
 * by construction (its module doc: "never touches `messages`, `users.email`,
 * or `payment_methods`/`payment_holds`"), but `DateProposal` itself still
 * carries `proposerId`/`recipientId` (bare ids, not emails, harmless) and
 * `policySnapshot` (config values, not money the venue needs to see). This
 * serializer is the explicit allowlist that is the ACTUAL enforcement
 * point: every field a venue-staff response can carry is named here, so
 * "does this leak anything" is answerable by reading one small function
 * instead of auditing every domain type this module touches.
 *
 * Participant NAMES (not ids, not emails) come from `profiles.display_name`
 * via a direct, read-only query, `profile.service.ts` has no
 * "look up display names for a set of user ids" export, and this is
 * exactly the kind of narrow cross-domain read the rest of the codebase
 * already does directly (e.g. `discovery.service.ts` reading `profiles`
 * itself) rather than inventing a new service export for one call site.
 */
import type { Ctx } from '../../lib/ctx.js';
import type { DateProposal, RedemptionMethod, Venue, VenueRedemption, Voucher } from '../../domain/types.js';
import type { RedeemResult } from '../../services/redemption.service.js';

async function displayNamesFor(ctx: Ctx, userIds: string[]): Promise<Map<string, string>> {
  if (userIds.length === 0) return new Map();
  const { rows } = await ctx.db.query<{ user_id: string; display_name: string }>(
    `SELECT user_id, display_name FROM profiles WHERE user_id = ANY($1::uuid[])`,
    [userIds],
  );
  return new Map(rows.map((r) => [r.user_id, r.display_name]));
}

export interface VenueVoucherView {
  id: string;
  code: string;
  status: Voucher['status'];
  issuedAt: string;
  expiresAt: string;
}

export interface VenueDateProposalView {
  id: string;
  venueId: string;
  scheduledStart: string;
  scheduledEnd: string;
  status: DateProposal['status'];
  /** Display names only, never email, never a bare id lookup the client could correlate to PII (spec §15.1 "user names"). */
  participantNames: string[];
}

export interface VenueRedemptionView {
  id: string;
  method: RedemptionMethod;
  createdAt: string;
}

export interface VenueRedeemResponse {
  voucher: VenueVoucherView;
  dateProposal: VenueDateProposalView;
  redemption: VenueRedemptionView;
}

function serializeVenueVoucher(v: Voucher): VenueVoucherView {
  return { id: v.id, code: v.code, status: v.status, issuedAt: v.issuedAt.toISOString(), expiresAt: v.expiresAt.toISOString() };
}

function serializeVenueRedemption(r: VenueRedemption): VenueRedemptionView {
  return { id: r.id, method: r.method, createdAt: r.createdAt.toISOString() };
}

export async function serializeVenueRedeemResult(ctx: Ctx, result: RedeemResult): Promise<VenueRedeemResponse> {
  const names = await displayNamesFor(ctx, [result.dateProposal.proposerId, result.dateProposal.recipientId]);
  return {
    voucher: serializeVenueVoucher(result.voucher),
    dateProposal: {
      id: result.dateProposal.id,
      venueId: result.dateProposal.venueId,
      scheduledStart: result.dateProposal.scheduledStart.toISOString(),
      scheduledEnd: result.dateProposal.scheduledEnd.toISOString(),
      status: result.dateProposal.status,
      participantNames: [names.get(result.dateProposal.proposerId) ?? 'Unknown', names.get(result.dateProposal.recipientId) ?? 'Unknown'],
    },
    redemption: serializeVenueRedemption(result.redemption),
  };
}

export interface VenueUpcomingVoucherRow {
  voucher_id: string;
  code: string;
  status: Voucher['status'];
  scheduled_start: Date;
  scheduled_end: Date;
  date_proposal_id: string;
  proposer_id: string;
  recipient_id: string;
}

export interface VenueUpcomingVoucherView {
  voucherId: string;
  code: string;
  status: Voucher['status'];
  scheduledStart: string;
  scheduledEnd: string;
  dateProposalId: string;
  participantNames: string[];
}

/** `GET /venue/vouchers`, upcoming (not-yet-redeemed) vouchers for the caller's venue only (spec §4.2 "view upcoming vouchers for their venue"). */
export async function listUpcomingVouchersForVenue(ctx: Ctx, venueId: string): Promise<VenueUpcomingVoucherView[]> {
  const { rows } = await ctx.db.query<VenueUpcomingVoucherRow>(
    `SELECT v.id AS voucher_id, v.code, v.status, dp.scheduled_start, dp.scheduled_end, dp.id AS date_proposal_id,
            dp.proposer_id, dp.recipient_id
     FROM vouchers v
     JOIN date_proposals dp ON dp.id = v.date_proposal_id
     WHERE v.venue_id = $1 AND v.status = 'issued'
     ORDER BY dp.scheduled_start ASC`,
    [venueId],
  );
  const allUserIds = [...new Set(rows.flatMap((r) => [r.proposer_id, r.recipient_id]))];
  const names = await displayNamesFor(ctx, allUserIds);

  return rows.map((r) => ({
    voucherId: r.voucher_id,
    code: r.code,
    status: r.status,
    scheduledStart: r.scheduled_start.toISOString(),
    scheduledEnd: r.scheduled_end.toISOString(),
    dateProposalId: r.date_proposal_id,
    participantNames: [names.get(r.proposer_id) ?? 'Unknown', names.get(r.recipient_id) ?? 'Unknown'],
  }));
}

export type { Venue };
