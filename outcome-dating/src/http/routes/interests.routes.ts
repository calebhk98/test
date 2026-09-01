/** §24.6 Interests routes. */
import type { FastifyInstance } from 'fastify';
import { z } from 'zod';
import * as interestService from '../../services/interest.service.js';
import { serializeInterestListPage } from '../serializers/interests.js';
import type { AppDeps } from '../deps.js';
import { authenticate, requireRole } from '../auth.js';
import { paginationQuerySchema, parseOrThrow, requireUuidParam } from '../validation.js';

// §11.3 "no free text before match", this schema structurally has no
// message/body field, so a client cannot smuggle one through even by
// accident (interest.service.ts's own signature enforces the same thing
// one layer down).
const SendInterestBodySchema = z.object({ recipientId: z.string() });

export function registerInterestRoutes(app: FastifyInstance, deps: AppDeps): void {
  const auth = { preHandler: [authenticate(deps), requireRole('user')] };

  app.post('/interests', auth, async (req, reply) => {
    const body = parseOrThrow(SendInterestBodySchema, req.body);
    reply.status(201).send(await interestService.sendInterest(req.ctx!, body.recipientId));
  });

  // Enriched with the counterpart's displayName/primaryPhotoUrl/age/
  // approximateDistanceKm (docs/ux-api-review.md §6, the "who liked me"
  // screen was otherwise a bare-id list plus one profile call per row).
  app.get('/interests/outgoing', auth, async (req, reply) => {
    const query = parseOrThrow(paginationQuerySchema, req.query);
    reply.send(serializeInterestListPage(await interestService.listOutgoingEnriched(req.ctx!, query)));
  });

  app.get('/interests/incoming', auth, async (req, reply) => {
    const query = parseOrThrow(paginationQuerySchema, req.query);
    reply.send(serializeInterestListPage(await interestService.listIncomingEnriched(req.ctx!, query)));
  });

  app.post('/interests/:interestId/accept', auth, async (req, reply) => {
    const interestId = requireUuidParam(req.params, 'interestId');
    reply.send(await interestService.acceptInterest(req.ctx!, interestId));
  });

  app.post('/interests/:interestId/decline', auth, async (req, reply) => {
    const interestId = requireUuidParam(req.params, 'interestId');
    reply.send(await interestService.declineInterest(req.ctx!, interestId));
  });

  app.post('/interests/:interestId/cancel', auth, async (req, reply) => {
    const interestId = requireUuidParam(req.params, 'interestId');
    reply.send(await interestService.cancelInterest(req.ctx!, interestId));
  });
}
