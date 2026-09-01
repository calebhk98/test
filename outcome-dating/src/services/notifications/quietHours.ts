import { z } from 'zod';
import type { Ctx } from '../../lib/ctx.js';
import { requireUserActor } from '../../lib/ctx.js';
import { ValidationError } from '../../lib/errors.js';
import type { QuietHours } from './types.js';

/**
 * Per-user quiet hours, evaluated in the USER's own local time (build
 * brief), never server time. No row for a user means quiet hours are OFF
 * (24/7 delivery allowed).
 *
 * Policy for a notification raised DURING quiet hours: HOLD it and
 * deliver right after quiet hours end (see config.ts
 * `NOTIFICATION_CONFIG.quietHours.policy` for the justification) — except
 * for the small bypass list in `config.ts` `quietHoursBypassEvents`
 * (today: `safety_notice` only), which is delivered immediately
 * regardless of the recipient's local time.
 */

const DEFAULT_QUIET_HOURS: QuietHours = { enabled: false, startMinute: 1320, endMinute: 480, timezone: 'UTC' };

interface QuietHoursRow {
  enabled: boolean;
  start_minute: number;
  end_minute: number;
  timezone: string;
}

function mapRow(row: QuietHoursRow): QuietHours {
  return { enabled: row.enabled, startMinute: row.start_minute, endMinute: row.end_minute, timezone: row.timezone };
}

export async function getMyQuietHours(ctx: Ctx): Promise<QuietHours> {
  const { userId } = requireUserActor(ctx);
  return getQuietHoursForUser(ctx, userId);
}

/** Internal (system) read — used by `delivery.ts`'s gate for an arbitrary recipient. */
export async function getQuietHoursForUser(ctx: Ctx, userId: string): Promise<QuietHours> {
  const { rows } = await ctx.db.query<QuietHoursRow>(
    `SELECT enabled, start_minute, end_minute, timezone FROM notification_quiet_hours WHERE user_id = $1`,
    [userId],
  );
  return rows[0] ? mapRow(rows[0]) : DEFAULT_QUIET_HOURS;
}

const UpdateQuietHoursSchema = z.object({
  enabled: z.boolean(),
  startMinute: z.number().int().min(0).max(1439),
  endMinute: z.number().int().min(0).max(1439),
  timezone: z.string().min(1).max(100),
});

export async function updateMyQuietHours(ctx: Ctx, input: QuietHours): Promise<QuietHours> {
  const { userId } = requireUserActor(ctx);
  const parsed = UpdateQuietHoursSchema.parse(input);
  assertValidTimeZone(parsed.timezone);
  const now = ctx.clock.now();
  await ctx.db.query(
    `INSERT INTO notification_quiet_hours (user_id, enabled, start_minute, end_minute, timezone, updated_at)
     VALUES ($1, $2, $3, $4, $5, $6)
     ON CONFLICT (user_id) DO UPDATE SET
       enabled = EXCLUDED.enabled, start_minute = EXCLUDED.start_minute,
       end_minute = EXCLUDED.end_minute, timezone = EXCLUDED.timezone, updated_at = EXCLUDED.updated_at`,
    [userId, parsed.enabled, parsed.startMinute, parsed.endMinute, parsed.timezone, now],
  );
  return parsed;
}

function assertValidTimeZone(timezone: string): void {
  try {
    Intl.DateTimeFormat('en-US', { timeZone: timezone });
  } catch {
    throw new ValidationError(`"${timezone}" is not a recognized IANA time zone name.`);
  }
}

/** Minutes since local midnight (0-1439) for `date` as observed in `timezone`. */
function localMinuteOfDay(date: Date, timezone: string): number {
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone: timezone,
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
  }).formatToParts(date);
  const hour = Number(parts.find((p) => p.type === 'hour')!.value) % 24;
  const minute = Number(parts.find((p) => p.type === 'minute')!.value);
  return hour * 60 + minute;
}

/**
 * True iff `now` falls inside `qh`'s configured window, in the user's own
 * local time. Handles an overnight window (`startMinute > endMinute`,
 * e.g. 22:00 -> 08:00) via wraparound. A disabled window, or a
 * zero-length window (`startMinute === endMinute`), is always "not
 * quiet" — a zero-length window is indistinguishable from "no window" and
 * treated the same rather than as "quiet all day", so a user can never
 * accidentally silence themselves permanently via a data-entry slip.
 */
export function isWithinQuietHours(qh: QuietHours, now: Date): boolean {
  if (!qh.enabled || qh.startMinute === qh.endMinute) return false;
  const m = localMinuteOfDay(now, qh.timezone);
  if (qh.startMinute < qh.endMinute) {
    return m >= qh.startMinute && m < qh.endMinute;
  }
  return m >= qh.startMinute || m < qh.endMinute;
}

/**
 * The next instant (>= `now`) at which `qh`'s window will have ended,
 * used as the held outbox row's `next_attempt_at`. Computed as "minutes
 * from now until local time == endMinute", which assumes the UTC offset
 * for `qh.timezone` does not change between `now` and that instant — true
 * the overwhelming majority of the time (a quiet-hours window is at most
 * ~24h long) but can be off by up to an hour on the specific night a DST
 * transition falls inside the window. Documented, accepted limitation for
 * this build; a fully DST-exact version would need to re-resolve the
 * offset iteratively rather than doing one minutes-based arithmetic pass.
 */
export function nextQuietHoursEnd(qh: QuietHours, now: Date): Date {
  const m = localMinuteOfDay(now, qh.timezone);
  let deltaMinutes = qh.endMinute - m;
  if (deltaMinutes <= 0) deltaMinutes += 24 * 60;
  return new Date(now.getTime() + deltaMinutes * 60_000);
}
