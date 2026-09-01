/**
 * Push-token device registration routes (docs/ux-api-review.md §13).
 * `notifications/devices.ts#registerDeviceToken`/`unregisterDeviceToken`/
 * `listMyDeviceTokens` were fully built and tested but had no HTTP route —
 * a client could never register an APNs/FCM token, so push notifications
 * were structurally impossible in production regardless of which push
 * adapter was configured. Not part of §24's original route list; an
 * addition, same pattern `routeTable.ts` already uses elsewhere.
 */
import type { FastifyInstance } from 'fastify';
import { z } from 'zod';
import { registerDeviceToken, unregisterDeviceToken, listMyDeviceTokens } from '../../services/notifications/devices.js';
import type { AppDeps } from '../deps.js';
import { authenticate, requireRole } from '../auth.js';
import { parseOrThrow } from '../validation.js';

const RegisterDeviceBodySchema = z.object({
  platform: z.enum(['ios', 'android', 'web']),
  deviceId: z.string().min(1).max(200),
  pushToken: z.string().min(1).max(4096),
});

const UnregisterDeviceBodySchema = z.object({ pushToken: z.string().min(1).max(4096) });

export function registerDeviceRoutes(app: FastifyInstance, deps: AppDeps): void {
  const auth = { preHandler: [authenticate(deps), requireRole('user')] };

  app.get('/devices', auth, async (req, reply) => {
    reply.send(await listMyDeviceTokens(req.ctx!));
  });

  app.post('/devices', auth, async (req, reply) => {
    const body = parseOrThrow(RegisterDeviceBodySchema, req.body);
    reply.status(201).send(await registerDeviceToken(req.ctx!, body));
  });

  // Disables the caller's own token by value, not by path id — a device
  // token has no stable client-facing id of its own (the row is keyed by
  // (platform, push_token), see devices.ts), and the token is already
  // something only this device's own client holds, so accepting it back
  // in the body rather than the URL avoids putting it in server access
  // logs for no benefit.
  app.delete('/devices', auth, async (req, reply) => {
    const body = parseOrThrow(UnregisterDeviceBodySchema, req.body);
    await unregisterDeviceToken(req.ctx!, body.pushToken);
    reply.status(204).send();
  });
}
