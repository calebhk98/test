/**
 * §24.9 Tickets routes: user-facing (`/tickets*`) plus the venue-staff
 * redemption surface (`/venue/*`).
 *
 * ROLE BOUNDARY: `/tickets*` is `requireRole('user')`; `/venue/*` is
 * `requireRole('venue_staff')` — a regular user hitting `/venue/redeem`
 * gets 403 (C-4.RBAC.2), and every `/venue/*` response is built through
 * `src/http/serializers/venue.ts`'s explicit allowlist (never a bare
 * `Voucher`/`DateProposal` spread), which is the serializer-level half of
 * the §4.2 "no chats/emails/card data" invariant.
 */
import type { FastifyInstance } from 'fastify';
import { z } from 'zod';
import * as voucherService from '../../services/voucher.service.js';
import * as redemptionService from '../../services/redemption.service.js';
import { serializeVenueRedeemResult, listUpcomingVouchersForVenue } from '../serializers/venue.js';
import { listMyTickets, getMyTicket } from '../serializers/tickets.js';
import type { AppDeps } from '../deps.js';
import { authenticate, requireRole } from '../auth.js';
import { parseOrThrow, requireUuidParam } from '../validation.js';

const RedeemBodySchema = z.object({ code: z.string().optional(), qrPayload: z.string().optional() });

export function registerTicketRoutes(app: FastifyInstance, deps: AppDeps): void {
  const userAuth = { preHandler: [authenticate(deps), requireRole('user')] };
  const venueAuth = { preHandler: [authenticate(deps), requireRole('venue_staff')] };

  // Denormalized with venue name/address + the proposal's schedule
  // (docs/ux-api-review.md §10 — the wallet screen otherwise needs a
  // per-ticket venue lookup plus a per-ticket date-proposal lookup just
  // to render "Coffee at The Daily Grind, Sat 6:00 PM").
  app.get('/tickets', userAuth, async (req, reply) => {
    reply.send(await listMyTickets(req.ctx!));
  });

  app.get('/tickets/:ticketId', userAuth, async (req, reply) => {
    const ticketId = requireUuidParam(req.params, 'ticketId');
    reply.send(await getMyTicket(req.ctx!, ticketId, voucherService.getVoucher));
  });

  app.post('/tickets/:ticketId/redeem', userAuth, async (req, reply) => {
    const ticketId = requireUuidParam(req.params, 'ticketId');
    const body = parseOrThrow(RedeemBodySchema, req.body);
    reply.send(await redemptionService.redeemBySelf(req.ctx!, ticketId, body));
  });

  // ---- Venue staff (§4.2) ----
  app.post('/venue/redeem', venueAuth, async (req, reply) => {
    const body = parseOrThrow(RedeemBodySchema, req.body);
    const result = await redemptionService.redeemByStaff(req.ctx!, body);
    reply.send(await serializeVenueRedeemResult(req.ctx!, result));
  });

  // C-4.2.1 addition: "venue staff can view upcoming vouchers for their venue".
  app.get('/venue/vouchers', venueAuth, async (req, reply) => {
    const actor = req.ctx!.actor;
    if (actor.type !== 'venue_staff') throw new Error('unreachable: guarded by requireRole');
    reply.send(await listUpcomingVouchersForVenue(req.ctx!, actor.venueId));
  });

  app.get('/venue/redemptions', venueAuth, async (req, reply) => {
    const actor = req.ctx!.actor;
    if (actor.type !== 'venue_staff') throw new Error('unreachable: guarded by requireRole');
    reply.send(await redemptionService.getRedemptionHistory(req.ctx!, actor.venueId));
  });
}
