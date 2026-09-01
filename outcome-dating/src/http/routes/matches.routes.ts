/**
 * `/matches` routes (product-owner finding #1 — see `matches.service.ts`
 * for the ownership/design notes). Not a §24-listed route; an addition,
 * same pattern `routeTable.ts` already uses for e.g.
 * `/discovery/reality`/`/conversations/:conversationId/read`.
 *
 * ROLE BOUNDARY: `requireRole('user')` only, same as every
 * `/conversations/*` route — a match IS a conversation, so the identical
 * "venue staff/admin never sees this" gate applies (spec §4.2, C-4.2.4).
 */
import type { FastifyInstance } from 'fastify';
import * as matchesService from '../../services/matches.service.js';
import type { AppDeps } from '../deps.js';
import { authenticate, requireRole } from '../auth.js';
import { paginationQuerySchema, parseOrThrow, requireUuidParam } from '../validation.js';
import { serializeMatch, serializeMatchPage } from '../serializers/matches.js';

export function registerMatchRoutes(app: FastifyInstance, deps: AppDeps): void {
  const auth = { preHandler: [authenticate(deps), requireRole('user')] };

  app.get('/matches', auth, async (req, reply) => {
    const query = parseOrThrow(paginationQuerySchema, req.query);
    reply.send(serializeMatchPage(await matchesService.listMyMatches(req.ctx!, query)));
  });

  app.get('/matches/:conversationId', auth, async (req, reply) => {
    const conversationId = requireUuidParam(req.params, 'conversationId');
    reply.send(serializeMatch(await matchesService.getMyMatch(req.ctx!, conversationId)));
  });
}
