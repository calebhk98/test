/**
 * Admin stats page routes (product owner addition). Admin-only, and EVERY
 * request here — reads included, not just mutations — writes an
 * `admin_audit_log` row via `writeAdminAudit`: this page aggregates the
 * platform's full operational and financial history, and the task brief
 * calls for every access to be logged, a deliberately stronger bar than
 * the read-routes-are-not-audited convention `admin.routes.ts` otherwise
 * uses for ordinary admin GETs.
 */
import type { FastifyInstance } from 'fastify';
import { z } from 'zod';
import * as adminStatsService from '../../services/adminStats.service.js';
import { serializeAdminStatsOverview, serializeAdminRetention } from '../serializers/stats.js';
import type { AppDeps } from '../deps.js';
import { authenticate, requireRole } from '../auth.js';
import { writeAdminAudit } from '../audit.js';
import { parseOrThrow } from '../validation.js';

const OverviewQuerySchema = z.object({
  window: z.union([z.coerce.number().int().min(1).max(adminStatsService.MAX_WINDOW_DAYS), z.literal('all')]).optional(),
});

export function registerAdminStatsRoutes(app: FastifyInstance, deps: AppDeps): void {
  const auth = { preHandler: [authenticate(deps), requireRole('admin')] };

  app.get('/admin/stats/overview', auth, async (req, reply) => {
    const query = parseOrThrow(OverviewQuerySchema, req.query);
    const overview = await adminStatsService.getOverview(req.ctx!, { windowDays: query.window ?? adminStatsService.DEFAULT_WINDOW_DAYS });
    await writeAdminAudit(req.ctx!, {
      action: 'stats.view_overview',
      targetType: 'stats_platform_daily',
      after: { windowDays: query.window ?? adminStatsService.DEFAULT_WINDOW_DAYS },
    });
    reply.send(serializeAdminStatsOverview(overview));
  });

  app.get('/admin/stats/retention', auth, async (req, reply) => {
    const retention = await adminStatsService.getRetention(req.ctx!);
    await writeAdminAudit(req.ctx!, { action: 'stats.view_retention', targetType: 'stats_cohort_retention' });
    reply.send(serializeAdminRetention(retention));
  });
}
