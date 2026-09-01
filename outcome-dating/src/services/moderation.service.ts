import type { Ctx } from '../lib/ctx.js';
import { NotImplementedError } from '../lib/errors.js';
import type { ModerationAction, ModerationActionType, Page } from '../domain/types.js';

/**
 * moderation.service — automated moderation scoring and actions.
 * Spec: §18 (except §18.6 appeals, in `appeal.service.ts`), §24.13,
 * §25.7 (recalculation job).
 *
 * Owning agent: E.
 *
 * HARD INVARIANT (spec §18.1, restated as Definition of Done #17): the
 * system assumes ZERO human moderators. Every function here must resolve
 * to an outcome (none/warning/restriction/shadowban/suspension) purely
 * from automated signals — there is no "escalate to a human queue" return
 * value anywhere in this module's contract.
 *
 * `applyThresholds` reads its cutoffs from config
 * (`moderation.auto_restriction_score`, `moderation.auto_shadowban_score`,
 * `moderation.auto_suspension_score` — all 'live' scope per §21.4, so a
 * threshold change applies to the next run, not retroactively to past
 * actions) and compares against `computeModerationScore`, which sums
 * `report.service#scoreReport` across a user's reports plus other
 * automated signals (message velocity, device reputation, no-shows,
 * negative post-date feedback — spec §18.2). `applyThresholds` is this
 * module's only writer of `moderation_actions` and of
 * `users.shadowbanned`/`users.suspended`.
 *
 * `isVisibleInDiscovery` is `discovery.service.ts`'s hard gate for
 * shadowban/suspension (spec §10.2 rules 1-2) — it reads
 * `users.status`/`shadowbanned`, it does not recompute the score.
 */

export interface AutomatedFlagInput {
  userId: string;
  /** e.g. "message_velocity", "device_reputation", "no_show", "negative_feedback", "duplicate_photo" (spec §18.2). */
  signalType: string;
  weight: number;
  metadata?: Record<string, unknown>;
}

/** Ingests one automated signal (not a user report — see `report.service.ts` for those). Does not itself apply an action; `applyThresholds` (called after, by the same request path or the §25.7 job) does. */
export async function recordAutomatedFlag(ctx: Ctx, input: AutomatedFlagInput): Promise<void> {
  throw new NotImplementedError('moderation.recordAutomatedFlag');
}

/** Sums `report.service#scoreReport` across `userId`'s reports plus recorded automated flags (spec §18.5). Pure aggregation — no writes. */
export async function computeModerationScore(ctx: Ctx, userId: string): Promise<number> {
  throw new NotImplementedError('moderation.computeModerationScore');
}

/**
 * Compares `computeModerationScore` against the configured thresholds and,
 * if crossed, writes a `moderation_actions` row and updates
 * `users.shadowbanned`/`suspended` accordingly. Returns `null` if no new
 * action was warranted (score below `moderation.auto_restriction_score`,
 * or already at/above the action the score warrants). Also fires a
 * `safety_notice` notification (spec §20.1) and a `trust.service.ts`
 * negative event on any action taken.
 */
export async function applyThresholds(ctx: Ctx, userId: string): Promise<ModerationAction | null> {
  throw new NotImplementedError('moderation.applyThresholds');
}

/** Admin moderation action viewer (spec §27 item 6). Omit `userId` to list across all users. */
export async function listModerationActions(ctx: Ctx, userId?: string, params?: { cursor?: string; limit?: number }): Promise<Page<ModerationAction>> {
  throw new NotImplementedError('moderation.listModerationActions');
}

/** `discovery.service.ts`'s hard gate: false if `userId` is shadowbanned or suspended (spec §10.2 rules 1-2, §18.4). */
export async function isVisibleInDiscovery(ctx: Ctx, userId: string): Promise<boolean> {
  throw new NotImplementedError('moderation.isVisibleInDiscovery');
}

/** §25.7 job: recompute and apply thresholds for every user with a moderation-relevant event since the last run. */
export async function runModerationRecalculation(ctx: Ctx): Promise<{ usersEvaluated: number; actionsApplied: number }> {
  throw new NotImplementedError('moderation.runModerationRecalculation');
}

export type { ModerationActionType };
