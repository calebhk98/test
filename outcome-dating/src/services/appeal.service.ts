import type { Ctx } from '../lib/ctx.js';
import { NotImplementedError } from '../lib/errors.js';
import type { Appeal, AppealMethod } from '../domain/types.js';

/**
 * appeal.service — automated appeals against a moderation restriction.
 * Spec: §18.6, §24.11 (`POST /me/trust/appeal`).
 *
 * Owning agent: E.
 *
 * HARD INVARIANT (spec §18.1/§18.6, "no human moderation means appeals
 * must be automated"): `resolveAppeal`'s decision must come from a
 * verifiable automated signal per `method` — liveness check result,
 * payment-method verification status, cooldown elapsed, or existing
 * account signals (spec §18.6 steps 1-4) — never a manual review queue.
 *
 * `submitAppeal` enforces `moderation.appeal_cooldown_hours` (config) has
 * elapsed since the triggering `moderation_actions` row before a new
 * appeal is accepted for the same restriction, via
 * `checkCooldownElapsed`.
 *
 * On approval, `resolveAppeal` restores the account (clears
 * `shadowbanned`/`suspended` as appropriate) and records a positive
 * `trust.service.ts` event; on rejection, the restriction is left in
 * place and a negative event is NOT added (a rejected appeal isn't itself
 * a new violation).
 */

export interface SubmitAppealInput {
  /** The moderation_actions row being appealed. Omit to appeal the user's current overall restriction if there's exactly one active one. */
  moderationActionId?: string;
  method: AppealMethod;
  /** Evidence payload shape depends on `method` — e.g. a liveness-check session id, a payment_method id just verified. */
  evidence?: Record<string, unknown>;
}

export async function submitAppeal(ctx: Ctx, input: SubmitAppealInput): Promise<Appeal> {
  throw new NotImplementedError('appeal.submitAppeal');
}

/** Evaluates the submitted evidence against `method`'s automated verification and updates the appeal's status accordingly (spec §18.6 "If appeal passes, restore account. If appeal fails, maintain restriction."). */
export async function resolveAppeal(ctx: Ctx, appealId: string): Promise<Appeal> {
  throw new NotImplementedError('appeal.resolveAppeal');
}

export async function getMyLatestAppeal(ctx: Ctx): Promise<Appeal | null> {
  throw new NotImplementedError('appeal.getMyLatestAppeal');
}

/** Whether `moderation.appeal_cooldown_hours` has elapsed since `userId`'s triggering moderation action, per spec §18.6 step 3. */
export async function checkCooldownElapsed(ctx: Ctx, userId: string): Promise<boolean> {
  throw new NotImplementedError('appeal.checkCooldownElapsed');
}
