/**
 * User stats page routes (product owner addition — see stats.service.ts's
 * module doc for the privacy rules enforced upstream of every one of
 * these). Every route requires an authenticated regular user and only
 * ever answers for that user's own id — none of these take a `userId`
 * param.
 */
import type { FastifyInstance } from 'fastify';
import { z } from 'zod';
import * as statsService from '../../services/stats.service.js';
import {
  serializeUserStatsOverview,
  serializeUserStatsTrends,
  serializeUserPhotoStats,
  serializeUserFilterCosts,
} from '../serializers/stats.js';
import type { AppDeps } from '../deps.js';
import { authenticate, requireRole } from '../auth.js';
import { parseOrThrow } from '../validation.js';

const TrendsQuerySchema = z.object({ weeks: z.coerce.number().int().min(1).max(52).optional() });
const FilterCostsQuerySchema = z.object({ refresh: z.coerce.boolean().optional() });

export function registerStatsRoutes(app: FastifyInstance, deps: AppDeps): void {
  const auth = { preHandler: [authenticate(deps), requireRole('user')] };

  app.get('/me/stats', auth, async (req, reply) => {
    const overview = await statsService.getMyStatsOverview(req.ctx!);
    reply.send(serializeUserStatsOverview(overview));
  });

  app.get('/me/stats/trends', auth, async (req, reply) => {
    const query = parseOrThrow(TrendsQuerySchema, req.query);
    const trends = await statsService.getMyStatsTrends(req.ctx!, { weeks: query.weeks });
    reply.send(serializeUserStatsTrends(trends));
  });

  app.get('/me/stats/photos', auth, async (req, reply) => {
    const stats = await statsService.getMyPhotoStats(req.ctx!);
    reply.send(serializeUserPhotoStats(stats));
  });

  // The one route on this page that can be genuinely slow on a cold cache
  // (a handful of bounded discovery-pool evaluations, one per enabled
  // filter — see stats.service.ts#getMyFilterCosts) — `?refresh=true`
  // bypasses the 1-hour cache explicitly rather than the page silently
  // recomputing it on every casual open.
  app.get('/me/stats/filters', auth, async (req, reply) => {
    const query = parseOrThrow(FilterCostsQuerySchema, req.query);
    const costs = await statsService.getMyFilterCosts(req.ctx!, deps.pool, { forceRefresh: query.refresh });
    reply.send(serializeUserFilterCosts(costs));
  });
}
