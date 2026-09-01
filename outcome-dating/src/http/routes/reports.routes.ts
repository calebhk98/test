/** §24.12 Reports route (generic `POST /reports`, distinct from `POST /profiles/{userId}/report` in discovery.routes.ts — both call the same service). */
import type { FastifyInstance } from 'fastify';
import { z } from 'zod';
import * as reportService from '../../services/report.service.js';
import type { AppDeps } from '../deps.js';
import { authenticate, requireRole } from '../auth.js';
import { parseOrThrow } from '../validation.js';

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

  app.post('/reports', auth, async (req, reply) => {
    const body = parseOrThrow(ReportBodySchema, req.body);
    reply.status(201).send(await reportService.submitReport(req.ctx!, body));
  });
}
