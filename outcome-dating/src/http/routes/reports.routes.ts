/** §24.12 Reports route (generic `POST /reports`, distinct from `POST /profiles/{userId}/report` in discovery.routes.ts, both call the same service). */
import type { FastifyInstance } from 'fastify';
import { z } from 'zod';
import * as reportService from '../../services/report.service.js';
import type { AppDeps } from '../deps.js';
import { authenticate, requireRole } from '../auth.js';
import { parseOrThrow } from '../validation.js';
import { withIdempotencyKey, idempotencyKeyHeader } from '../middleware/idempotency.js';

const ReportBodySchema = z.object({
  reportedId: z.string(),
  category: z.enum([
    'fake_profile',
    'scam_money_request',
    'harassment',
    'unsafe_behavior',
    'misleading_photos',
    'minor_suspected',
    'spam',
    'no_show',
    'inappropriate_content',
    'other',
  ]),
  details: z.string().optional(),
  conversationId: z.string().optional(),
  messageId: z.string().optional(),
});

export function registerReportRoutes(app: FastifyInstance, deps: AppDeps): void {
  const auth = { preHandler: [authenticate(deps), requireRole('user')] };

  // Mobile readiness (wiring item 6): a retried submit must not file two
  // reports for the same incident, see middleware/idempotency.ts.
  app.post('/reports', auth, async (req, reply) => {
    const body = parseOrThrow(ReportBodySchema, req.body);
    const result = await withIdempotencyKey(
      req.ctx!,
      { scope: 'POST /reports', key: idempotencyKeyHeader(req), requestBody: body },
      async () => ({ status: 201, body: await reportService.submitReport(req.ctx!, body) }),
    );
    reply.status(result.status).send(result.body);
  });
}
