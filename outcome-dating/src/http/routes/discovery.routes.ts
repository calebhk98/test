/** §24.5 Discovery routes (grid, reality dashboard, profile view, block, report). */
import type { FastifyInstance } from 'fastify';
import { z } from 'zod';
import * as discoveryService from '../../services/discovery.service.js';
import * as profileService from '../../services/profile.service.js';
import * as reportService from '../../services/report.service.js';
import { serializeDiscoveryPage } from '../serializers/discovery.js';
import { serializePublicProfile } from '../serializers/profile.js';
import type { AppDeps } from '../deps.js';
import { authenticate, requireRole } from '../auth.js';
import { paginationQuerySchema, parseOrThrow, requireUuidParam } from '../validation.js';

/** §30.1 exact static copy for an empty discovery grid — never generated, always this string. */
export const NO_CANDIDATES_MESSAGE = 'No candidates currently match your filters. Try widening distance or age range.';

const ReportCategorySchema = z.enum([
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
]);
const ReportBodySchema = z.object({
  category: ReportCategorySchema,
  details: z.string().optional(),
  conversationId: z.string().optional(),
  messageId: z.string().optional(),
});

export function registerDiscoveryRoutes(app: FastifyInstance, deps: AppDeps): void {
  const auth = { preHandler: [authenticate(deps), requireRole('user')] };

  app.get('/discovery', auth, async (req, reply) => {
    const query = parseOrThrow(paginationQuerySchema, req.query);
    const page = await discoveryService.getDiscoveryGrid(req.ctx!, query);
    const body = serializeDiscoveryPage(page);
    reply.send(page.items.length === 0 ? { ...body, message: NO_CANDIDATES_MESSAGE } : body);
  });

  app.get('/discovery/reality', auth, async (req, reply) => {
    reply.send(await discoveryService.getRealityDashboard(req.ctx!));
  });

  app.get('/profiles/:userId', auth, async (req, reply) => {
    const userId = requireUuidParam(req.params, 'userId');
    const view = await profileService.getPublicProfile(req.ctx!, userId);
    reply.send(serializePublicProfile(view));
  });

  app.post('/profiles/:userId/block', auth, async (req, reply) => {
    const userId = requireUuidParam(req.params, 'userId');
    reply.status(201).send(await discoveryService.blockUser(req.ctx!, userId));
  });

  app.delete('/profiles/:userId/block', auth, async (req, reply) => {
    const userId = requireUuidParam(req.params, 'userId');
    await discoveryService.unblockUser(req.ctx!, userId);
    reply.status(204).send();
  });

  app.post('/profiles/:userId/report', auth, async (req, reply) => {
    const userId = requireUuidParam(req.params, 'userId');
    const body = parseOrThrow(ReportBodySchema, req.body);
    const report = await reportService.submitReport(req.ctx!, { reportedId: userId, ...body });
    // §30.9: the reporter's own confirmation of THEIR OWN report obviously
    // includes their own id (they already know it) — but never anything
    // about how it will read to the reported user, and no other route ever
    // echoes `reporterId` back to anyone else. See reports.routes.ts.
    reply.status(201).send(report);
  });
}
