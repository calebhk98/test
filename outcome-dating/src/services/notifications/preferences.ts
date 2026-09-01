import { z } from 'zod';
import type { Ctx } from '../../lib/ctx.js';
import { requireUserActor } from '../../lib/ctx.js';
import { ForbiddenError, ValidationError } from '../../lib/errors.js';
import { getVerifiedPhoneForUser } from '../auth.service.js';
import type { CategoryPrefs, NotificationCategory } from './types.js';

/**
 * Per-user, per-category, per-channel notification preferences (build
 * brief: "A preference per event category and per channel (push, email,
 * in-app), defaulting to sensible values"). No row for (user, category)
 * means "use the default below" — the same convention
 * `config.service.ts`'s `config_entries` uses, chosen for the same
 * reason: a brand-new user needs no seeding pass for this to behave
 * correctly.
 *
 * Defaults (spec §20, §29, build brief):
 *  - match / message / date_request: push ON (the three the product
 *    owner explicitly named as push-primary), email OFF (push is the
 *    primary channel for an app-first product), in-app ON.
 *  - account_activity (chat lifecycle, payments, tickets, reminders,
 *    trust level — everything else in §20.1's event list): push and
 *    in-app ON, email ON too — these are the closest thing to a receipt
 *    (payment hold, ticket issued) and are worth a durable email copy.
 *  - marketing: everything OFF (spec §29 "marketing opt-out" — this is
 *    the opt-out already applied by default, not something a user has to
 *    find a switch for).
 *
 * `sms` is OFF by default for every single category, including
 * account_activity (build correction: optional phone -> optional, opt-in
 * SMS). Two independent reasons stack here, either alone would be enough:
 * (1) most users have no verified phone on file at all, so it couldn't
 * deliver regardless, and (2) SMS costs real money per message — nothing
 * should ever cost the product money without the user explicitly asking
 * for it, unlike push/email which are free to default on.
 */
export const DEFAULT_PREFERENCES: Record<NotificationCategory, CategoryPrefs> = {
  match: { push: true, email: false, inApp: true, sms: false },
  message: { push: true, email: false, inApp: true, sms: false },
  date_request: { push: true, email: false, inApp: true, sms: false },
  account_activity: { push: true, email: true, inApp: true, sms: false },
  marketing: { push: false, email: false, inApp: false, sms: false },
};

const CATEGORIES = ['match', 'message', 'date_request', 'account_activity', 'marketing'] as const satisfies readonly NotificationCategory[];

interface PrefRow {
  category: NotificationCategory;
  push: boolean;
  email: boolean;
  in_app: boolean;
  sms: boolean;
}

function mapRow(row: PrefRow): CategoryPrefs {
  return { push: row.push, email: row.email, inApp: row.in_app, sms: row.sms };
}

export async function getMyNotificationPreferences(ctx: Ctx): Promise<Record<NotificationCategory, CategoryPrefs>> {
  const { userId } = requireUserActor(ctx);
  return getPreferencesForUser(ctx, userId);
}

/**
 * Internal (system) read of every category's resolved preference for
 * `userId` — used by `delivery.ts`'s gate. Not actor-gated to "self"
 * (system actor calling on behalf of an arbitrary recipient), matching
 * `devices.listActiveDeviceTokensForUser`'s trust boundary.
 */
export async function getPreferencesForUser(ctx: Ctx, userId: string): Promise<Record<NotificationCategory, CategoryPrefs>> {
  if (ctx.actor.type === 'user' && ctx.actor.userId !== userId) {
    throw new ForbiddenError('Cannot read another user\'s notification preferences.');
  }
  const { rows } = await ctx.db.query<PrefRow>(
    `SELECT category, push, email, in_app, sms FROM notification_preferences WHERE user_id = $1`,
    [userId],
  );
  const byCategory = new Map(rows.map((r) => [r.category, mapRow(r)]));
  const result = {} as Record<NotificationCategory, CategoryPrefs>;
  for (const category of CATEGORIES) {
    result[category] = byCategory.get(category) ?? DEFAULT_PREFERENCES[category];
  }
  return result;
}

/** Resolves just one category's preference for `userId` — the single row `delivery.ts` actually needs per outbox item. */
export async function getCategoryPreferenceForUser(ctx: Ctx, userId: string, category: NotificationCategory): Promise<CategoryPrefs> {
  const { rows } = await ctx.db.query<PrefRow>(
    `SELECT category, push, email, in_app, sms FROM notification_preferences WHERE user_id = $1 AND category = $2`,
    [userId, category],
  );
  return rows[0] ? mapRow(rows[0]) : DEFAULT_PREFERENCES[category];
}

const UpdatePreferenceSchema = z.object({
  push: z.boolean().optional(),
  email: z.boolean().optional(),
  inApp: z.boolean().optional(),
  sms: z.boolean().optional(),
});

/**
 * Updates the calling user's preference for one category. Partial —
 * omitted fields keep their current (or default) value. This is the ONLY
 * place a caller can change what gets delivered; there is deliberately no
 * "send anyway" flag anywhere in `outbox.ts`/`delivery.ts` (build brief:
 * "Preferences must never be bypassable by a caller passing a flag").
 *
 * Turning `sms` ON is rejected up front unless the caller already has a
 * VERIFIED phone number — a friendlier, earlier error than silently
 * persisting a preference that can never actually fire. This is a UX
 * convenience only, never the enforcement point: `delivery.ts` re-checks
 * for a verified phone live on every send, because a phone can be removed
 * (immediately disabling SMS, per the build brief) at any time after this
 * preference was saved.
 */
export async function updateMyNotificationPreference(
  ctx: Ctx,
  category: NotificationCategory,
  patch: { push?: boolean; email?: boolean; inApp?: boolean; sms?: boolean },
): Promise<CategoryPrefs> {
  const { userId } = requireUserActor(ctx);
  const parsed = UpdatePreferenceSchema.parse(patch);

  if (parsed.sms === true) {
    const phone = await getVerifiedPhoneForUser(ctx, userId);
    if (!phone) {
      throw new ValidationError('Add and verify a phone number before turning on SMS notifications.', {
        field: 'sms',
      });
    }
  }

  const current = await getCategoryPreferenceForUser(ctx, userId, category);
  const next: CategoryPrefs = {
    push: parsed.push ?? current.push,
    email: parsed.email ?? current.email,
    inApp: parsed.inApp ?? current.inApp,
    sms: parsed.sms ?? current.sms,
  };
  const now = ctx.clock.now();
  await ctx.db.query(
    `INSERT INTO notification_preferences (user_id, category, push, email, in_app, sms, updated_at)
     VALUES ($1, $2, $3, $4, $5, $6, $7)
     ON CONFLICT (user_id, category) DO UPDATE SET
       push = EXCLUDED.push, email = EXCLUDED.email, in_app = EXCLUDED.in_app, sms = EXCLUDED.sms, updated_at = EXCLUDED.updated_at`,
    [userId, category, next.push, next.email, next.inApp, next.sms, now],
  );
  return next;
}

// =========================================================================
// Content preview opt-in (lock-screen preview text — default OFF)
// =========================================================================

export async function getMyContentPreviewSetting(ctx: Ctx): Promise<boolean> {
  const { userId } = requireUserActor(ctx);
  return getContentPreviewForUser(ctx, userId);
}

/** Internal (system) read — default false (opt-IN, build brief: "a lock-screen preview is visible to anyone holding the phone"). */
export async function getContentPreviewForUser(ctx: Ctx, userId: string): Promise<boolean> {
  const { rows } = await ctx.db.query<{ enabled: boolean }>(
    `SELECT enabled FROM notification_content_preview WHERE user_id = $1`,
    [userId],
  );
  return rows[0]?.enabled ?? false;
}

export async function updateMyContentPreviewSetting(ctx: Ctx, enabled: boolean): Promise<void> {
  const { userId } = requireUserActor(ctx);
  const now = ctx.clock.now();
  await ctx.db.query(
    `INSERT INTO notification_content_preview (user_id, enabled, updated_at)
     VALUES ($1, $2, $3)
     ON CONFLICT (user_id) DO UPDATE SET enabled = EXCLUDED.enabled, updated_at = EXCLUDED.updated_at`,
    [userId, enabled, now],
  );
}
