/** §24.11 Trust routes. */
import type { FastifyInstance } from 'fastify';
import { z } from 'zod';
import * as trustService from '../../services/trust.service.js';
import * as appealService from '../../services/appeal.service.js';
import { serializeTrustSummary } from '../serializers/trust.js';
import { requireUserActor } from '../../lib/ctx.js';
import type { AppDeps } from '../deps.js';
import { authenticate, requireRole } from '../auth.js';
import { paginationQuerySchema, parseOrThrow } from '../validation.js';

const AppealBodySchema = z.object({
  moderationActionId: z.string().optional(),
  method: z.enum(['liveness_check', 'payment_verification', 'cooldown', 'existing_signals']),
  evidence: z.record(z.unknown()).optional(),
});

export function registerTrustRoutes(app: FastifyInstance, deps: AppDeps): void {
  const auth = { preHandler: [authenticate(deps), requireRole('user')] };

  app.get('/me/trust', auth, async (req, reply) => {
    const { userId } = requireUserActor(req.ctx!);
    const summary = await trustService.getMyTrustSummary(req.ctx!);
    reply.send(await serializeTrustSummary(deps.flags, userId, summary));
  });

  app.get('/me/trust/events', auth, async (req, reply) => {
    const query = parseOrThrow(paginationQuerySchema, req.query);
    reply.send(await trustService.listMyTrustEvents(req.ctx!, query));
  });

  app.post('/me/trust/appeal', auth, async (req, reply) => {
    const body = parseOrThrow(AppealBodySchema, req.body);
    reply.status(201).send(await appealService.submitAppeal(req.ctx!, body));
  });
}
