/**
 * User stats page routes (product owner addition, see stats.service.ts's
 * module doc for the privacy rules enforced upstream of every one of
 * these). Every route requires an authenticated regular user and only
 * ever answers for that user's own id, none of these take a `userId`
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
  serializeUserPoolVenn,
  serializeUserStatsComparisons,
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
  // (a single bounded pass over the candidate pool, see
  // stats.service.ts#getMyFilterCosts). `?refresh=true` bypasses the
  // 1-hour cache explicitly rather than the page silently recomputing it
  // on every casual open.
  app.get('/me/stats/filters', auth, async (req, reply) => {
    const query = parseOrThrow(FilterCostsQuerySchema, req.query);
    const costs = await statsService.getMyFilterCosts(req.ctx!, { forceRefresh: query.refresh });
    reply.send(serializeUserFilterCosts(costs));
  });

  // Two views of the same numbers: this route for a client that wants the
  // plain data (set sizes, intersection, what's outside each set), and
  // /me/stats/venn.svg below for a client that just wants a picture. Both
  // are backed by the SAME cache as /me/stats/filters (see
  // stats.service.ts#getMyPoolVenn), so loading this after (or before)
  // /me/stats/filters on the same page view does not pay for the
  // reality-dashboard computation twice.
  app.get('/me/stats/venn', auth, async (req, reply) => {
    const data = await statsService.getMyPoolVenn(req.ctx!);
    reply.send(serializeUserPoolVenn(data));
  });

  // A small, self-contained, accessible SVG rendering of the same data
  // /me/stats/venn returns as JSON, see statsVenn.ts's own doc for the
  // accessibility guarantees (title/desc text alternative, every number
  // that appears as pixels also available as data from the JSON route
  // above). There is no client in this project to draw the diagram
  // itself, so the API returns a ready-to-display image directly.
  app.get('/me/stats/venn.svg', auth, async (req, reply) => {
    const svg = await statsService.getMyPoolVennSvg(req.ctx!);
    reply.type('image/svg+xml').send(svg);
  });

  // Peer comparisons, see stats.service.ts's module doc,
  // "COMPARISONS ARE AGGREGATE-VERSUS-AGGREGATE", for what is and is not
  // compared here and why.
  app.get('/me/stats/comparisons', auth, async (req, reply) => {
    const comparisons = await statsService.getMyComparisons(req.ctx!);
    reply.send(serializeUserStatsComparisons(comparisons));
  });
}
