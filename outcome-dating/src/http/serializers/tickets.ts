/**
 * src/http/serializers/tickets.ts, the wallet/ticket list, denormalized.
 *
 * `voucher.service#listMyVouchers`/`getVoucher` return a bare `Voucher`
 * (`id`, `dateProposalId`, `venueId`, `code`, `qrPayload`, `status`,
 * `issuedAt`, `expiresAt`, `redeemedAt`), no venue name/address and no
 * date/time, since those live on `venues`/`date_proposals`, not
 * `vouchers`. Rendering a wallet screen ("Coffee at The Daily Grind, Sat
 * 6:00 PM") for M tickets against that shape means one
 * `GET /date-proposals/:id` per ticket for the schedule, plus a venue
 * lookup per ticket (docs/ux-api-review.md §10).
 *
 * This file closes that gap the same way `serializers/venue.ts`'s
 * `listUpcomingVouchersForVenue` already does for the venue-staff side,
 * and the same way `timeline.service.ts` denormalizes `venueName` onto a
 * date-proposal event in chat: one direct, read-only, batched join query
 * (never per-row), never a second/parallel `Venue`-shaped return from
 * `voucher.service.ts` itself, that file's frozen `may call` list has no
 * edge to `venue`, so the join lives here at the HTTP layer instead,
 * exactly like `serializers/venue.ts`'s own precedent.
 */
import type { Ctx } from '../../lib/ctx.js';
import { requireUserActor } from '../../lib/ctx.js';
import type { Page, Voucher } from '../../domain/types.js';
import { decodeTimestampIdCursor, encodeTimestampIdCursor } from '../../lib/cursor.js';

export interface MyTicketView {
  id: string;
  dateProposalId: string;
  venueId: string;
  venueName: string;
  venueAddress: string;
  code: string;
  qrPayload: string;
  status: Voucher['status'];
  scheduledStart: string;
  scheduledEnd: string;
  issuedAt: string;
  expiresAt: string;
  redeemedAt: string | null;
}

interface TicketRow {
  id: string;
  date_proposal_id: string;
  venue_id: string;
  venue_name: string;
  venue_address: string;
  code: string;
  qr_payload: string;
  status: Voucher['status'];
  scheduled_start: Date;
  scheduled_end: Date;
  issued_at: Date;
  expires_at: Date;
  redeemed_at: Date | null;
}

function serializeRow(row: TicketRow): MyTicketView {
  return {
    id: row.id,
    dateProposalId: row.date_proposal_id,
    venueId: row.venue_id,
    venueName: row.venue_name,
    venueAddress: row.venue_address,
    code: row.code,
    qrPayload: row.qr_payload,
    status: row.status,
    scheduledStart: row.scheduled_start.toISOString(),
    scheduledEnd: row.scheduled_end.toISOString(),
    issuedAt: row.issued_at.toISOString(),
    expiresAt: row.expires_at.toISOString(),
    redeemedAt: row.redeemed_at ? row.redeemed_at.toISOString() : null,
  };
}

const TICKET_SELECT = `SELECT v.id, v.date_proposal_id, v.venue_id, ven.name AS venue_name, ven.address AS venue_address,
         v.code, v.qr_payload, v.status, dp.scheduled_start, dp.scheduled_end, v.issued_at, v.expires_at, v.redeemed_at
  FROM vouchers v
  JOIN date_proposals dp ON dp.id = v.date_proposal_id
  JOIN venues ven ON ven.id = v.venue_id`;

/**
 * `GET /tickets`, every voucher for a proposal the caller participated in,
 * with venue name/address and the proposal's schedule denormalized onto
 * each row (see file doc).
 *
 * Mobile readiness (wiring item 6): a user's own ticket history grows
 * without bound over the life of an account, this previously had no
 * cursor at all (an unconditional, unlimited `SELECT`). Cursor-paginated
 * now on `(issued_at, id)`, same shared codec (src/lib/cursor.ts) every
 * other list in this codebase uses. Breaking response shape change (bare
 * array -> `{items, nextCursor}`), fine per this build's brief (nothing
 * has shipped).
 */
export async function listMyTickets(ctx: Ctx, params?: { cursor?: string; limit?: number }): Promise<Page<MyTicketView>> {
  const { userId } = requireUserActor(ctx);
  const limit = Math.min(Math.max(params?.limit ?? 50, 1), 200);

  const values: unknown[] = [userId];
  let cursorClause = '';
  if (params?.cursor) {
    const c = decodeTimestampIdCursor(params.cursor);
    values.push(c.ts, c.id);
    cursorClause = `AND (v.issued_at, v.id) < ($2, $3)`;
  }
  values.push(limit + 1);

  const { rows } = await ctx.db.query<TicketRow>(
    `${TICKET_SELECT} WHERE (dp.proposer_id = $1 OR dp.recipient_id = $1) ${cursorClause}
     ORDER BY v.issued_at DESC, v.id DESC LIMIT $${values.length}`,
    values,
  );

  const hasMore = rows.length > limit;
  const pageRows = hasMore ? rows.slice(0, limit) : rows;
  const items = pageRows.map(serializeRow);
  const lastRow = pageRows[pageRows.length - 1];
  const nextCursor = hasMore && lastRow ? encodeTimestampIdCursor(lastRow.issued_at, lastRow.id) : null;
  return { items, nextCursor };
}

/**
 * `GET /tickets/:ticketId`, enriched. Reuses `voucher.service#getVoucher`
 * purely for its authorization check (participant-or-admin-or-system,
 * see that function's `assertCanViewVoucher`) before running the enriched
 * join, so the "who may view this ticket" rule stays defined in exactly
 * one place.
 */
export async function getMyTicket(ctx: Ctx, ticketId: string, authorize: (ctx: Ctx, ticketId: string) => Promise<Voucher>): Promise<MyTicketView> {
  await authorize(ctx, ticketId);
  const { rows } = await ctx.db.query<TicketRow>(`${TICKET_SELECT} WHERE v.id = $1`, [ticketId]);
  return serializeRow(rows[0]!);
}
