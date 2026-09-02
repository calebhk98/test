import { z } from 'zod';
import type { Ctx } from '../lib/ctx.js';
import { requireUserActor } from '../lib/ctx.js';
import { NotFoundError, RateLimitError } from '../lib/errors.js';
import type { Appeal, AppealMethod, AppealStatus, ModerationActionType } from '../domain/types.js';
import * as moderation from './moderation.service.js';
import * as trust from './trust.service.js';
import * as notification from './notification.service.js';

/**
 * appeal.service, automated appeals against a moderation restriction.
 * Spec: §18.6, §24.11 (`POST /me/trust/appeal`).
 *
 * Owning agent: E.
 *
 * HARD INVARIANT (spec §18.1/§18.6, "no human moderation means appeals
 * must be automated"): `resolveAppeal`'s decision must come from a
 * verifiable automated signal per `method`, liveness check result,
 * payment-method verification status, cooldown elapsed, or existing
 * account signals (spec §18.6 steps 1-4), never a manual review queue.
 * `submitAppeal` calls `resolveAppeal` SYNCHRONOUSLY before returning, so
 * the DB's transient `status = 'pending'` row (the schema's default,
 * needed because `appeals` has no "instant" status) never escapes this
 * module as a value a caller could observe mid-flight, every `Appeal`
 * this module hands back is already `'approved'` or `'rejected'`.
 *
 * `submitAppeal` enforces `moderation.appeal_cooldown_hours` (config) has
 * elapsed since the triggering `moderation_actions` row before a new
 * appeal is accepted for the same restriction, via
 * `checkCooldownElapsed`. `checkCooldownElapsed` also considers the most
 * recent PRIOR appeal's resolution time (not just the original
 * moderation action), so a user who submits and fails an appeal must
 * wait out the cooldown again before trying once more, this is the
 * "repeated failed appeals must not be spammable" rate limit.
 *
 * On approval, `resolveAppeal` restores the account (clears
 * `shadowbanned`/`suspended` as appropriate) and records a positive
 * `trust.service.ts` event; on rejection, the restriction is left in
 * place and a negative event is NOT added (a rejected appeal isn't itself
 * a new violation).
 */

const AUTOMATED_APPEAL_TRUST_BONUS = 15;
const EXISTING_SIGNALS_MIN_ACCOUNT_AGE_DAYS = 30;

export interface SubmitAppealInput {
  /** The moderation_actions row being appealed. Omit to appeal the user's current overall restriction if there's exactly one active one. */
  moderationActionId?: string;
  method: AppealMethod;
  /** Evidence payload shape depends on `method`, e.g. a liveness-check session id, a payment_method id just verified. */
  evidence?: Record<string, unknown>;
}

const APPEAL_METHODS = ['liveness_check', 'payment_verification', 'cooldown', 'existing_signals'] as const satisfies readonly AppealMethod[];

const SubmitAppealSchema = z.object({
  moderationActionId: z.string().uuid().optional(),
  method: z.enum(APPEAL_METHODS),
  evidence: z.record(z.unknown()).optional(),
});

interface AppealRow {
  id: string;
  user_id: string;
  moderation_action_id: string | null;
  method: AppealMethod;
  status: AppealStatus;
  submitted_at: Date;
  resolved_at: Date | null;
  metadata: Record<string, unknown>;
}

function rowToAppeal(row: AppealRow): Appeal {
  return {
    id: row.id,
    userId: row.user_id,
    moderationActionId: row.moderation_action_id,
    method: row.method,
    status: row.status,
    submittedAt: row.submitted_at,
    resolvedAt: row.resolved_at,
    metadata: row.metadata ?? {},
  };
}

async function findLatestActiveModerationActionId(ctx: Ctx, userId: string): Promise<{ id: string; action: ModerationActionType } | null> {
  const page = await moderation.listModerationActions(ctx, userId, { limit: 1 });
  const latest = page.items[0];
  if (!latest || latest.action === 'none') return null;
  return { id: latest.id, action: latest.action };
}

export async function submitAppeal(ctx: Ctx, input: SubmitAppealInput): Promise<Appeal> {
  const actor = requireUserActor(ctx);
  const parsed = SubmitAppealSchema.parse(input);

  let moderationActionId = parsed.moderationActionId ?? null;
  if (!moderationActionId) {
    const latest = await findLatestActiveModerationActionId(ctx, actor.userId);
    if (!latest) {
      throw new NotFoundError('No active moderation action to appeal.');
    }
    moderationActionId = latest.id;
  }

  const cooldownElapsed = await checkCooldownElapsed(ctx, actor.userId);
  if (!cooldownElapsed) {
    throw new RateLimitError('Appeal cooldown has not elapsed yet.');
  }

  // CC-12 fix (tests/conformance/timeDiscipline.test.ts FINDING): pass
  // ctx.clock.now() explicitly for submitted_at rather than leaving it to
  // the schema's own `DEFAULT now()`, resolveAppeal's resolved_at (below)
  // already does this, the INSERT below just hadn't. A DB-default real
  // wall-clock value here made checkCooldownElapsed (which correctly
  // compares against ctx.clock.now()) impossible to test deterministically
  // with a ManualClock pinned away from real wall-clock time.
  const { rows } = await ctx.db.query<AppealRow>(
    `INSERT INTO appeals (user_id, moderation_action_id, method, status, metadata, submitted_at)
     VALUES ($1, $2, $3, 'pending', $4::jsonb, $5)
     RETURNING id, user_id, moderation_action_id, method, status, submitted_at, resolved_at, metadata`,
    [actor.userId, moderationActionId, parsed.method, JSON.stringify(parsed.evidence ?? {}), ctx.clock.now()],
  );
  const appeal = rows[0]!;

  // Resolve synchronously, see module doc: no path returns a caller a
  // 'pending' appeal that is actually waiting on a human.
  return resolveAppeal(ctx, appeal.id);
}

async function evaluateAutomatedSignal(ctx: Ctx, appeal: AppealRow): Promise<boolean> {
  const evidence = appeal.metadata ?? {};
  switch (appeal.method) {
    case 'liveness_check':
      return typeof evidence.livenessSessionId === 'string' && evidence.livenessSessionId.length > 0 && evidence.passed === true;

    case 'payment_verification': {
      if (typeof evidence.paymentMethodId !== 'string') return false;
      const { rows } = await ctx.db.query<{ count: string }>(
        `SELECT count(*)::text AS count FROM payment_methods
          WHERE id = $1 AND user_id = $2 AND deleted_at IS NULL AND verified_at IS NOT NULL`,
        [evidence.paymentMethodId, appeal.user_id],
      );
      return Number(rows[0]?.count ?? '0') > 0;
    }

    case 'cooldown':
      // Submission already required the cooldown to have elapsed; this is
      // a re-verification (the automated "signal" for this method IS time
      // having passed), not a rubber stamp.
      return checkCooldownElapsed(ctx, appeal.user_id);

    case 'existing_signals': {
      const { rows } = await ctx.db.query<{ email_verified_at: Date | null; created_at: Date }>(
        'SELECT email_verified_at, created_at FROM users WHERE id = $1',
        [appeal.user_id],
      );
      const user = rows[0];
      if (!user || !user.email_verified_at) return false;
      const ageDays = (ctx.clock.now().getTime() - user.created_at.getTime()) / (1000 * 60 * 60 * 24);
      if (ageDays < EXISTING_SIGNALS_MIN_ACCOUNT_AGE_DAYS) return false;

      // Safety carve-out: never auto-restore via generic account signals
      // if a minor-suspicion report is on file (spec §18.3 "maximum
      // severity"), that category requires a stronger signal than
      // "account looks fine", if it's ever to be lifted automatically at
      // all.
      const { rows: minorRows } = await ctx.db.query<{ count: string }>(
        `SELECT count(*)::text AS count FROM reports WHERE reported_id = $1 AND category = 'minor_suspected'`,
        [appeal.user_id],
      );
      return Number(minorRows[0]?.count ?? '0') === 0;
    }

    default:
      return false;
  }
}

/** Evaluates the submitted evidence against `method`'s automated verification and updates the appeal's status accordingly (spec §18.6 "If appeal passes, restore account. If appeal fails, maintain restriction."). */
export async function resolveAppeal(ctx: Ctx, appealId: string): Promise<Appeal> {
  const { rows } = await ctx.db.query<AppealRow>(
    `SELECT id, user_id, moderation_action_id, method, status, submitted_at, resolved_at, metadata FROM appeals WHERE id = $1`,
    [appealId],
  );
  const existing = rows[0];
  if (!existing) throw new NotFoundError(`Appeal ${appealId} not found.`);
  if (existing.status !== 'pending') {
    // Already resolved, resolving twice is a no-op, not a re-decision.
    return rowToAppeal(existing);
  }

  const passed = await evaluateAutomatedSignal(ctx, existing);
  const status: AppealStatus = passed ? 'approved' : 'rejected';

  const { rows: updatedRows } = await ctx.db.query<AppealRow>(
    `UPDATE appeals SET status = $2, resolved_at = $3 WHERE id = $1
     RETURNING id, user_id, moderation_action_id, method, status, submitted_at, resolved_at, metadata`,
    [appealId, status, ctx.clock.now()],
  );
  const updated = updatedRows[0]!;

  if (passed) {
    let triggeringAction: ModerationActionType | null = null;
    if (updated.moderation_action_id) {
      const { rows: actionRows } = await ctx.db.query<{ action: ModerationActionType }>(
        'SELECT action FROM moderation_actions WHERE id = $1',
        [updated.moderation_action_id],
      );
      triggeringAction = actionRows[0]?.action ?? null;
    }

    if (triggeringAction === 'shadowban') {
      await ctx.db.query('UPDATE users SET shadowbanned = false WHERE id = $1', [updated.user_id]);
    } else if (triggeringAction === 'suspension') {
      await ctx.db.query(`UPDATE users SET suspended = false, shadowbanned = false, status = 'active' WHERE id = $1`, [updated.user_id]);
    }
    // 'restriction'/'warning' have no dedicated boolean to clear, restored
    // purely via the positive trust event + recalculation below, which is
    // also what lifts the §6.4 Limited-tier restrictions for shadowban/
    // suspension cases once the level itself recovers.

    await trust.recordTrustEvent(ctx, {
      userId: updated.user_id,
      eventType: trust.TRUST_EVENT_TYPES.APPEAL_APPROVED,
      delta: AUTOMATED_APPEAL_TRUST_BONUS,
      metadata: { appealId: updated.id, moderationActionId: updated.moderation_action_id },
    });
    await trust.recalculateTrustScore(ctx, updated.user_id);
  }
  // Rejected: deliberately no trust_event write, a failed appeal is not
  // itself a new violation (see module doc).

  try {
    await notification.notify(ctx, {
      userId: updated.user_id,
      eventType: 'safety_notice',
      channel: 'in_app',
      payload: { appealId: updated.id, outcome: status },
    });
  } catch (err) {
    ctx.logger.warn('appeal.resolveAppeal: notify failed', { userId: updated.user_id, err: (err as Error).message });
  }

  return rowToAppeal(updated);
}

export async function getMyLatestAppeal(ctx: Ctx): Promise<Appeal | null> {
  const actor = requireUserActor(ctx);
  const { rows } = await ctx.db.query<AppealRow>(
    `SELECT id, user_id, moderation_action_id, method, status, submitted_at, resolved_at, metadata
       FROM appeals WHERE user_id = $1 ORDER BY submitted_at DESC LIMIT 1`,
    [actor.userId],
  );
  const row = rows[0];
  return row ? rowToAppeal(row) : null;
}

/** Whether `moderation.appeal_cooldown_hours` has elapsed since `userId`'s triggering moderation action, per spec §18.6 step 3. Also anchors on the most recent appeal's resolution (or submission, if still resolving) so repeated appeal attempts are themselves rate-limited. */
export async function checkCooldownElapsed(ctx: Ctx, userId: string): Promise<boolean> {
  const cooldownHours = await ctx.config.get('moderation.appeal_cooldown_hours');

  const { rows: actionRows } = await ctx.db.query<{ created_at: Date }>(
    'SELECT created_at FROM moderation_actions WHERE user_id = $1 ORDER BY created_at DESC LIMIT 1',
    [userId],
  );
  const { rows: appealRows } = await ctx.db.query<{ submitted_at: Date; resolved_at: Date | null }>(
    'SELECT submitted_at, resolved_at FROM appeals WHERE user_id = $1 ORDER BY submitted_at DESC LIMIT 1',
    [userId],
  );

  const candidates: Date[] = [];
  if (actionRows[0]) candidates.push(actionRows[0].created_at);
  if (appealRows[0]) candidates.push(appealRows[0].resolved_at ?? appealRows[0].submitted_at);

  if (candidates.length === 0) return true; // nothing to cool down from

  const referenceTime = candidates.reduce((latest, d) => (d.getTime() > latest.getTime() ? d : latest));
  const elapsedHours = (ctx.clock.now().getTime() - referenceTime.getTime()) / (1000 * 60 * 60);
  return elapsedHours >= cooldownHours;
}
