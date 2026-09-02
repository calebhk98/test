/** §24.11 Trust routes. */
import type { FastifyInstance } from 'fastify';
import { z } from 'zod';
import * as trustService from '../../services/trust.service.js';
import * as appealService from '../../services/appeal.service.js';
import { serializeTrustSummary, getMyCapabilities } from '../serializers/trust.js';
import type { AppDeps } from '../deps.js';
import { authenticate, requireRole } from '../auth.js';
import { paginationQuerySchema, parseOrThrow } from '../validation.js';
import { withIdempotencyKey, idempotencyKeyHeader } from '../middleware/idempotency.js';

const AppealBodySchema = z.object({
  moderationActionId: z.string().optional(),
  method: z.enum(['liveness_check', 'payment_verification', 'cooldown', 'existing_signals']),
  evidence: z.record(z.unknown()).optional(),
});

export function registerTrustRoutes(app: FastifyInstance, deps: AppDeps): void {
  const auth = { preHandler: [authenticate(deps), requireRole('user')] };

  app.get('/me/trust', auth, async (req, reply) => {
    const summary = await trustService.getMyTrustSummary(req.ctx!);
    reply.send(await serializeTrustSummary(req.ctx!, summary));
  });

  app.get('/me/trust/events', auth, async (req, reply) => {
    const query = parseOrThrow(paginationQuerySchema, req.query);
    reply.send(await trustService.listMyTrustEvents(req.ctx!, query));
  });

  // `trust.service#can()` was built and tested but had no route, a
  // client had no way to know an action was disabled without attempting
  // it and parsing a 403 (docs/ux-api-review.md §11).
  app.get('/me/capabilities', auth, async (req, reply) => {
    reply.send(await getMyCapabilities(req.ctx!));
  });

  // Mobile readiness (wiring item 6): a retried submit must not file two
  // appeals, see middleware/idempotency.ts.
  app.post('/me/trust/appeal', auth, async (req, reply) => {
    const body = parseOrThrow(AppealBodySchema, req.body);
    const result = await withIdempotencyKey(
      req.ctx!,
      { scope: 'POST /me/trust/appeal', key: idempotencyKeyHeader(req), requestBody: body },
      async () => ({ status: 201, body: await appealService.submitAppeal(req.ctx!, body) }),
    );
    reply.status(result.status).send(result.body);
  });
}
