/**
 * Notification centre routes (docs/ux-api-review.md §13, the single
 * biggest reachability gap in the review). `notification.service.ts`'s
 * `listMyNotifications`/`markNotificationRead` were fully built and
 * tested but had no HTTP route anywhere, spec §20.2's "in-app
 * notification center" channel (conformance C-20.2.1, `MUST`) did not
 * exist as an API surface at all. Not part of §24's original route list;
 * an addition, same pattern `routeTable.ts` already uses for e.g.
 * `/matches`, `/discovery/reality`.
 */
import type { FastifyInstance } from 'fastify';
import { z } from 'zod';
import * as notificationService from '../../services/notification.service.js';
import type { AppDeps } from '../deps.js';
import { authenticate, requireRole } from '../auth.js';
import { parseOrThrow, requireUuidParam } from '../validation.js';

// Query strings arrive as plain strings, `z.coerce.boolean()` would treat
// the literal string "false" as truthy (any non-empty string coerces to
// `true`), so this maps only "true"/"1" to `true` and everything else
// (including absent, "false", "0") to `false`/undefined explicitly.
const queryBooleanSchema = z
  .string()
  .optional()
  .transform((v) => (v === 'true' || v === '1' ? true : v === undefined ? undefined : false));

const ListNotificationsQuerySchema = z.object({
  cursor: z.string().optional(),
  limit: z.coerce.number().int().min(1).max(100).optional(),
  unreadOnly: queryBooleanSchema,
});

export function registerNotificationRoutes(app: FastifyInstance, deps: AppDeps): void {
  const auth = { preHandler: [authenticate(deps), requireRole('user')] };

  app.get('/notifications', auth, async (req, reply) => {
    const query = parseOrThrow(ListNotificationsQuerySchema, req.query);
    reply.send(await notificationService.listMyNotifications(req.ctx!, query));
  });

  app.post('/notifications/:notificationId/read', auth, async (req, reply) => {
    const notificationId = requireUuidParam(req.params, 'notificationId');
    await notificationService.markNotificationRead(req.ctx!, notificationId);
    reply.status(204).send();
  });
}
