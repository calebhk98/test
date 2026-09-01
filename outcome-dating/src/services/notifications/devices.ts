import { z } from 'zod';
import type { Ctx } from '../../lib/ctx.js';
import { requireUserActor } from '../../lib/ctx.js';
import { ForbiddenError } from '../../lib/errors.js';
import type { DevicePlatform, DeviceTokenRow } from './types.js';

/**
 * Device token registration (build brief: "device tokens per user with
 * platform, a stable device identifier, created/last-seen timestamps, and
 * an enabled flag").
 *
 * Two invariants this file is entirely responsible for:
 *
 *  1. Re-registering the SAME (platform, pushToken) never duplicates a
 *     row, `registerDeviceToken`'s `ON CONFLICT (platform, push_token)`
 *     upsert (011_notifications.sql) guarantees this at the DB level, not
 *     just in application logic.
 *  2. A token moving to a NEW user (shared/resold device) cuts the
 *     previous owner off immediately, because it's the same physical row
 *     being reassigned (not a new row alongside an old one), the previous
 *     owner's `listActiveDeviceTokensForUser` simply stops returning it
 *     the instant the new registration commits. There is no separate
 *     "revoke" step to remember, and no window where both users appear to
 *     own the token.
 */

const PLATFORMS = ['ios', 'android', 'web'] as const satisfies readonly DevicePlatform[];

const RegisterDeviceSchema = z.object({
  platform: z.enum(PLATFORMS),
  deviceId: z.string().min(1).max(200),
  pushToken: z.string().min(1).max(4096),
});

export interface RegisterDeviceInput {
  platform: DevicePlatform;
  deviceId: string;
  pushToken: string;
}

interface DeviceRow {
  id: string;
  user_id: string;
  platform: DevicePlatform;
  device_id: string;
  push_token: string;
  enabled: boolean;
  created_at: Date;
  last_seen_at: Date;
}

function mapRow(row: DeviceRow): DeviceTokenRow {
  return {
    id: row.id,
    userId: row.user_id,
    platform: row.platform,
    deviceId: row.device_id,
    pushToken: row.push_token,
    enabled: row.enabled,
    createdAt: row.created_at,
    lastSeenAt: row.last_seen_at,
  };
}

/**
 * Registers (or re-registers, or reassigns) one device token for the
 * calling user. Idempotent-safe to call on every app launch, exactly the
 * way a real client would.
 */
export async function registerDeviceToken(ctx: Ctx, input: RegisterDeviceInput): Promise<DeviceTokenRow> {
  const { userId } = requireUserActor(ctx);
  const parsed = RegisterDeviceSchema.parse(input);
  const now = ctx.clock.now();

  const { rows } = await ctx.db.query<DeviceRow>(
    `INSERT INTO device_tokens (user_id, platform, device_id, push_token, enabled, created_at, last_seen_at)
     VALUES ($1, $2, $3, $4, true, $5, $5)
     ON CONFLICT (platform, push_token) DO UPDATE SET
       user_id = EXCLUDED.user_id,
       device_id = EXCLUDED.device_id,
       enabled = true,
       last_seen_at = EXCLUDED.last_seen_at
     RETURNING *`,
    [userId, parsed.platform, parsed.deviceId, parsed.pushToken, now],
  );
  return mapRow(rows[0]!);
}

/** Disables (but does not delete) a device token, e.g. explicit logout on that device. Only the owning user may do this. */
export async function unregisterDeviceToken(ctx: Ctx, pushToken: string): Promise<void> {
  const { userId } = requireUserActor(ctx);
  await ctx.db.query(`UPDATE device_tokens SET enabled = false WHERE push_token = $1 AND user_id = $2`, [
    pushToken,
    userId,
  ]);
}

export async function listMyDeviceTokens(ctx: Ctx): Promise<DeviceTokenRow[]> {
  const { userId } = requireUserActor(ctx);
  return listActiveDeviceTokensForUser(ctx, userId, { includeDisabled: true });
}

/**
 * Internal (system/delivery-worker) read: every enabled device token for
 * `userId`. Not actor-gated to "self", `delivery.ts` calls this for
 * arbitrary recipients as `system`, same trust boundary as
 * `notification.service.ts#deliverPending`.
 */
export async function listActiveDeviceTokensForUser(
  ctx: Ctx,
  userId: string,
  opts: { includeDisabled?: boolean } = {},
): Promise<DeviceTokenRow[]> {
  if (ctx.actor.type === 'user' && ctx.actor.userId !== userId) {
    throw new ForbiddenError('Cannot list another user\'s device tokens.');
  }
  const clause = opts.includeDisabled ? '' : 'AND enabled';
  const { rows } = await ctx.db.query<DeviceRow>(
    `SELECT * FROM device_tokens WHERE user_id = $1 ${clause} ORDER BY last_seen_at DESC`,
    [userId],
  );
  return rows.map(mapRow);
}

/**
 * Prunes a token the sender reported as invalid/unregistered (build
 * brief: "invalid or unregistered tokens reported back by the sender must
 * be pruned automatically"). Deletes outright rather than merely
 * disabling, an invalid token is permanently dead at the provider, so
 * there is nothing worth keeping around. System-only; called by
 * `delivery.ts` right after a `PushSender.send` returns
 * `status: 'invalid_token'`.
 */
export async function pruneInvalidToken(ctx: Ctx, platform: DevicePlatform, pushToken: string): Promise<void> {
  await ctx.db.query(`DELETE FROM device_tokens WHERE platform = $1 AND push_token = $2`, [platform, pushToken]);
}
