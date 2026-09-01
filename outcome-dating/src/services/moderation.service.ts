import { z } from 'zod';
import type { Ctx } from '../lib/ctx.js';
import type { ModerationAction, ModerationActionType, Page } from '../domain/types.js';
import * as report from './report.service.js';
import * as trust from './trust.service.js';
import * as notification from './notification.service.js';

/**
 * moderation.service, automated moderation scoring and actions.
 * Spec: §18 (except §18.6 appeals, in `appeal.service.ts`), §24.13,
 * §25.7 (recalculation job).
 *
 * Owning agent: E.
 *
 * HARD INVARIANT (spec §18.1, restated as Definition of Done #17): the
 * system assumes ZERO human moderators. Every function here must resolve
 * to an outcome (none/warning/restriction/shadowban/suspension) purely
 * from automated signals, there is no "escalate to a human queue" return
 * value anywhere in this module's contract. `ModerationActionType` itself
 * has no "pending_review"-shaped member, so this is enforced at the type
 * level, not just by convention, see `tests/unit/moderation.test.ts`
 * ("the action pipeline reaches a terminal decision with no human input")
 * for a runtime proof of the same thing.
 *
 * ---------------------------------------------------------------------
 * WHERE THE SCORE COMES FROM (coordination note, resolves an ambiguity
 * between this module's and report.service.ts's frozen doc comments):
 * ---------------------------------------------------------------------
 * `report.service#submitReport` computes that report's weight via
 * `scoreReport` and pushes it here via `recordAutomatedFlag`
 * (`signalType: 'user_report'`) at submission time, see report.service.ts.
 * `computeModerationScore` therefore does NOT re-walk `report.listReportsAgainst`
 * and re-sum `scoreReport` itself (that would double-count every report);
 * it purely sums `automated_moderation_flags.weight` for the user, which
 * already reflects every report (via the flag report.service pushed) plus
 * any other automated signal recorded directly through `recordAutomatedFlag`
 * (message velocity, device reputation, no-shows, negative post-date
 * feedback, spec §18.2, for whichever future caller ends up wired to
 * observe those; none of `message`/`dateProposal`/`redemption`.service is
 * on the "may call" graph into `moderation` yet, so in the MVP the
 * practical source is reports). This module DOES use the `moderation ─▶
 * report` graph edge, but for a narrower purpose: `applyThresholds` calls
 * `report.assessMinorSuspected` to evaluate the `minor_suspected` category
 * (spec §18.3/§18.5 "maximum severity, immediate protective action"),
 * see report.service.ts's "SAF-1 FIX" module doc for the full
 * corroboration model this now applies (a lone, uncorroborated report no
 * longer suspends anyone by itself; see SAF-1 in docs/risk-review.md).
 * This is a credibility/corroboration lookup across the reporter graph,
 * not a re-derivation of `computeModerationScore`'s own number.
 *
 * `applyThresholds` reads its cutoffs from config
 * (`moderation.auto_restriction_score`, `moderation.auto_shadowban_score`,
 * `moderation.auto_suspension_score`, all 'live' scope per §21.4, so a
 * threshold change applies to the next run, not retroactively to past
 * actions) and compares against `computeModerationScore`. `applyThresholds`
 * is this module's only writer of `moderation_actions` and of
 * `users.shadowbanned`/`users.suspended`.
 *
 * RESTRICTION EFFECTS (§18.4 "reduced discovery visibility, fewer
 * outgoing interests, links disabled, extra verification required"): a
 * `restriction` action carries no dedicated boolean column of its own,
 * `applyThresholds` realizes it by pushing a large negative
 * `trust.service` event and forcing a synchronous `recalculateTrustScore`,
 * which (per §6.4's restriction table, already enforced by
 * `trust.service#can`/`canSendClickableLinks`) is what actually reduces a
 * user's discovery visibility, interest quota, and link clickability once
 * their level drops to Limited. This module doesn't need a parallel
 * "restricted" flag propagated to `interest`/`discovery`.service,
 * trust level IS the restriction mechanism for those three effects.
 * "Extra verification required" has no consuming code path yet in the
 * MVP; it's recorded in the `moderation_actions.metadata` for
 * traceability and future wiring.
 *
 * `isVisibleInDiscovery` is `discovery.service.ts`'s hard gate for
 * shadowban/suspension (spec §10.2 rules 1-2), it reads
 * `users.status`/`shadowbanned`, it does not recompute the score. Per
 * spec §30.4, this is deliberately the ONLY thing a shadowban touches,
 * an existing conversation is untouched by anything in this file.
 */

// =====================================================================
// Internal action model (never exposed with weights, `ModerationAction`
// from domain/types.ts, the frozen return type, carries `score`/`reason`/
// `metadata` for admin auditability per spec §18.4/§23.23, which is fine:
// unlike trust's weighting formula, §18 has no "don't expose the
// mechanism" requirement, admins explicitly need this for §4.3/§27.)
// =====================================================================

const ACTION_SEVERITY: Record<ModerationActionType, number> = {
  none: 0,
  warning: 1,
  restriction: 2,
  shadowban: 3,
  suspension: 4,
};
const SEVERITY_ACTION: ModerationActionType[] = ['none', 'warning', 'restriction', 'shadowban', 'suspension'];

/** Internal-only, not derived from config (no §21.4 key exists for a "warning" cutoff, only restriction/shadowban/suspension are named there), a fixed fraction of the (configurable) restriction threshold. */
const WARNING_SCORE_RATIO = 0.5;

/** Trust-score deltas pushed on each action (spec §6.2 "reports" as a negative factor arrives at trust.service exactly here, see trust.service.ts's module doc for why raw non-actioned reports don't move trust on their own). */
const TRUST_DELTA_FOR_ACTION: Partial<Record<ModerationActionType, number>> = {
  warning: -5,
  restriction: -20,
  shadowban: -40,
  suspension: -70,
};
const TRUST_EVENT_TYPE_FOR_ACTION: Partial<Record<ModerationActionType, string>> = {
  warning: trust.TRUST_EVENT_TYPES.MODERATION_WARNING,
  restriction: trust.TRUST_EVENT_TYPES.MODERATION_RESTRICTION,
  shadowban: trust.TRUST_EVENT_TYPES.MODERATION_SHADOWBAN,
  suspension: trust.TRUST_EVENT_TYPES.MODERATION_SUSPENSION,
};

/** Static reason strings (spec §1/§20 "no generated prose" applies here in spirit too, `moderation_actions.reason` is an audit-log field, not user copy, but it's still a fixed vocabulary, never interpolated free text). */
const REASON_MINOR_SUSPECTED = 'minor_suspected_report_immediate_protective_action';
/** SAF-1 fix: the fast, reversible interim action applied on an uncorroborated (but credible-reporter) minor_suspected signal, see `report.service.ts`'s "SAF-1 FIX" module doc for the full model. Distinct reason from `REASON_MINOR_SUSPECTED` so the audit trail (and any caller reading `moderation_actions.reason`) can tell "this was the fast-but-reversible step" apart from "this was the corroborated, decisive one" at a glance. */
const REASON_MINOR_SUSPECTED_INTERIM = 'minor_suspected_report_interim_protective_action';
const REASON_SCORE_THRESHOLD = 'automated_score_threshold_crossed';

export interface AutomatedFlagInput {
  userId: string;
  /** e.g. "message_velocity", "device_reputation", "no_show", "negative_feedback", "duplicate_photo" (spec §18.2). */
  signalType: string;
  weight: number;
  metadata?: Record<string, unknown>;
}

const AutomatedFlagSchema = z.object({
  userId: z.string().uuid(),
  signalType: z.string().trim().min(1).max(100),
  weight: z.number().finite(),
  metadata: z.record(z.unknown()).optional(),
});

/** Ingests one automated signal (not a user report, see `report.service.ts` for those, though report.service is itself the primary caller of this function). Does not itself apply an action; `applyThresholds` (called after, by the same request path or the §25.7 job) does. */
export async function recordAutomatedFlag(ctx: Ctx, input: AutomatedFlagInput): Promise<void> {
  const parsed = AutomatedFlagSchema.parse(input);
  await ctx.db.query(
    `INSERT INTO automated_moderation_flags (user_id, signal_type, weight, metadata)
     VALUES ($1, $2, $3, $4::jsonb)`,
    [parsed.userId, parsed.signalType, parsed.weight, JSON.stringify(parsed.metadata ?? {})],
  );
}

/** Sums recorded automated flags for `userId` (spec §18.5), see module doc for why this does not separately re-walk `report.listReportsAgainst`. Pure aggregation, no writes. */
export async function computeModerationScore(ctx: Ctx, userId: string): Promise<number> {
  const { rows } = await ctx.db.query<{ sum: string | null }>(
    'SELECT COALESCE(sum(weight), 0)::text AS sum FROM automated_moderation_flags WHERE user_id = $1',
    [userId],
  );
  return Number(rows[0]?.sum ?? '0');
}

async function currentActionLevel(ctx: Ctx, userId: string): Promise<number> {
  const { rows } = await ctx.db.query<{ shadowbanned: boolean; suspended: boolean }>(
    'SELECT shadowbanned, suspended FROM users WHERE id = $1',
    [userId],
  );
  const u = rows[0];
  if (u?.suspended) return ACTION_SEVERITY.suspension;
  if (u?.shadowbanned) return ACTION_SEVERITY.shadowban;

  const { rows: lastActionRows } = await ctx.db.query<{ action: ModerationActionType }>(
    'SELECT action FROM moderation_actions WHERE user_id = $1 ORDER BY created_at DESC LIMIT 1',
    [userId],
  );
  const lastAction = lastActionRows[0]?.action;
  if (lastAction === 'restriction') return ACTION_SEVERITY.restriction;
  if (lastAction === 'warning') return ACTION_SEVERITY.warning;
  return ACTION_SEVERITY.none;
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
  const score = await computeModerationScore(ctx, userId);
  const [restrictionThreshold, shadowbanThreshold, suspensionThreshold] = await Promise.all([
    ctx.config.get('moderation.auto_restriction_score'),
    ctx.config.get('moderation.auto_shadowban_score'),
    ctx.config.get('moderation.auto_suspension_score'),
  ]);
  const warningThreshold = restrictionThreshold * WARNING_SCORE_RATIO;

  // ---- ordinary score-ladder action (unchanged from before this fix) ----
  let scoreBasedAction: ModerationActionType;
  if (score >= suspensionThreshold) {
    scoreBasedAction = 'suspension';
  } else if (score >= shadowbanThreshold) {
    scoreBasedAction = 'shadowban';
  } else if (score >= restrictionThreshold) {
    scoreBasedAction = 'restriction';
  } else if (score >= warningThreshold) {
    scoreBasedAction = 'warning';
  } else {
    scoreBasedAction = 'none';
  }

  // ---- SAF-1 fix: minor_suspected corroboration model (see
  // report.service.ts's "SAF-1 FIX" module doc for the full model) ----
  const minorSuspected = await report.assessMinorSuspected(ctx, userId);
  let minorSuspectedAction: ModerationActionType = 'none';
  let minorSuspectedReason: string = REASON_MINOR_SUSPECTED_INTERIM;
  if (minorSuspected.hasCredibleSignal) {
    const [minCorroborators, minorSuspensionScore, interimAction] = await Promise.all([
      ctx.config.get('moderation.minor_suspected_min_corroborating_reporters'),
      ctx.config.get('moderation.minor_suspected_suspension_score'),
      ctx.config.get('moderation.minor_suspected_interim_action'),
    ]);
    if (
      minorSuspected.distinctCredibleCorroborators >= minCorroborators &&
      minorSuspected.weightedScore >= minorSuspensionScore
    ) {
      // Corroborated by multiple independent, non-clustered credible
      // reporters AND the combined weighted score clears the bar, this
      // is the "genuine signal still acts decisively and fast" case.
      // Never reachable from a single report, regardless of its
      // reporter's trust level (see module doc: the corroborating-
      // reporter-count gate is a hard floor of 1, i.e. never satisfied by
      // exactly one report).
      minorSuspectedAction = 'suspension';
      minorSuspectedReason = REASON_MINOR_SUSPECTED;
    } else {
      // Uncorroborated (or not yet enough independent reporters/score),
      // fast, reversible protective action instead of termination.
      minorSuspectedAction = interimAction;
      minorSuspectedReason = REASON_MINOR_SUSPECTED_INTERIM;
    }
  }
  // A minor_suspected report from a non-credible (brand-new, untrusted,
  // or previously-abusive) reporter, with no credible reporter yet
  // involved at all, deliberately does NOT drive `minorSuspectedAction`
  // here. Unlike every other report category, `minor_suspected` reports
  // are deliberately excluded from `computeModerationScore`'s general
  // flag pool entirely (see `report.service#submitReport`'s own note),
  // this category's escalation is governed exclusively by this
  // corroboration model, never by the ordinary score ladder, so a single
  // report (from any reporter, however trusted) cannot reach suspension
  // through either door.

  // ---- combine: never LESS protective than either path alone ----
  let targetAction: ModerationActionType;
  let reason: string;
  if (ACTION_SEVERITY[minorSuspectedAction] >= ACTION_SEVERITY[scoreBasedAction]) {
    targetAction = minorSuspectedAction;
    reason = minorSuspectedAction === 'none' ? REASON_SCORE_THRESHOLD : minorSuspectedReason;
  } else {
    targetAction = scoreBasedAction;
    reason = REASON_SCORE_THRESHOLD;
  }

  const targetLevel = ACTION_SEVERITY[targetAction];
  const currentLevel = await currentActionLevel(ctx, userId);
  if (targetLevel === 0 || targetLevel <= currentLevel) {
    return null;
  }

  const metadata = {
    score,
    thresholds: { restrictionThreshold, shadowbanThreshold, suspensionThreshold, warningThreshold },
    minorSuspected,
  };

  const { rows } = await ctx.db.query<{
    id: string;
    user_id: string;
    action: ModerationActionType;
    reason: string;
    score: number;
    metadata: Record<string, unknown>;
    created_at: Date;
  }>(
    `INSERT INTO moderation_actions (user_id, action, reason, score, metadata)
     VALUES ($1, $2, $3, $4, $5::jsonb)
     RETURNING id, user_id, action, reason, score, metadata, created_at`,
    [userId, targetAction, reason, score, JSON.stringify(metadata)],
  );
  const row = rows[0]!;

  if (targetAction === 'shadowban' || targetAction === 'suspension') {
    await ctx.db.query('UPDATE users SET shadowbanned = true WHERE id = $1', [userId]);
  }
  if (targetAction === 'suspension') {
    await ctx.db.query(`UPDATE users SET suspended = true, status = 'suspended' WHERE id = $1`, [userId]);
  }

  const delta = TRUST_DELTA_FOR_ACTION[targetAction];
  const eventType = TRUST_EVENT_TYPE_FOR_ACTION[targetAction];
  if (delta !== undefined && eventType !== undefined) {
    await trust.recordTrustEvent(ctx, {
      userId,
      eventType,
      delta,
      metadata: { moderationActionId: row.id, score },
    });
    await trust.recalculateTrustScore(ctx, userId);
  }

  try {
    await notification.notify(ctx, {
      userId,
      eventType: 'safety_notice',
      channel: 'in_app',
      payload: { action: targetAction },
    });
  } catch (err) {
    ctx.logger.warn('moderation.applyThresholds: notify failed', { userId, err: (err as Error).message });
  }

  return rowToModerationAction(row);
}

function rowToModerationAction(row: {
  id: string;
  user_id: string;
  action: ModerationActionType;
  reason: string;
  score: number;
  metadata: Record<string, unknown>;
  created_at: Date;
}): ModerationAction {
  return {
    id: row.id,
    userId: row.user_id,
    action: row.action,
    reason: row.reason,
    score: Number(row.score),
    metadata: row.metadata ?? {},
    createdAt: row.created_at,
  };
}

/** Admin moderation action viewer (spec §27 item 6). Omit `userId` to list across all users. */
export async function listModerationActions(ctx: Ctx, userId?: string, params?: { cursor?: string; limit?: number }): Promise<Page<ModerationAction>> {
  const limit = Math.min(100, Math.max(1, params?.limit ?? 20));
  const offset = params?.cursor ? Number(params.cursor) : 0;

  const { rows } = userId
    ? await ctx.db.query<{ id: string; user_id: string; action: ModerationActionType; reason: string; score: number; metadata: Record<string, unknown>; created_at: Date }>(
        `SELECT id, user_id, action, reason, score, metadata, created_at
           FROM moderation_actions WHERE user_id = $1
          ORDER BY created_at DESC, id DESC
          LIMIT $2 OFFSET $3`,
        [userId, limit + 1, offset],
      )
    : await ctx.db.query<{ id: string; user_id: string; action: ModerationActionType; reason: string; score: number; metadata: Record<string, unknown>; created_at: Date }>(
        `SELECT id, user_id, action, reason, score, metadata, created_at
           FROM moderation_actions
          ORDER BY created_at DESC, id DESC
          LIMIT $1 OFFSET $2`,
        [limit + 1, offset],
      );

  const hasMore = rows.length > limit;
  const page = hasMore ? rows.slice(0, limit) : rows;
  return { items: page.map(rowToModerationAction), nextCursor: hasMore ? String(offset + limit) : null };
}

/** `discovery.service.ts`'s hard gate: false if `userId` is shadowbanned or suspended (spec §10.2 rules 1-2, §18.4). Reads `users` state only, deliberately does not touch `conversations`/`messages` (spec §30.4: an existing conversation must survive a shadowban). */
export async function isVisibleInDiscovery(ctx: Ctx, userId: string): Promise<boolean> {
  const { rows } = await ctx.db.query<{ status: string; shadowbanned: boolean; suspended: boolean }>(
    'SELECT status, shadowbanned, suspended FROM users WHERE id = $1',
    [userId],
  );
  const u = rows[0];
  if (!u) return false;
  return u.status === 'active' && !u.shadowbanned && !u.suspended;
}

/** §25.7 job: recompute and apply thresholds for every user with a moderation-relevant event (a report or automated flag) on record. */
export async function runModerationRecalculation(ctx: Ctx): Promise<{ usersEvaluated: number; actionsApplied: number }> {
  const { rows } = await ctx.db.query<{ user_id: string }>(
    `SELECT DISTINCT user_id FROM (
       SELECT user_id FROM automated_moderation_flags
       UNION
       SELECT reported_id AS user_id FROM reports
     ) AS candidates`,
  );

  let actionsApplied = 0;
  for (const { user_id: userId } of rows) {
    const action = await applyThresholds(ctx, userId);
    if (action) actionsApplied++;
  }
  return { usersEvaluated: rows.length, actionsApplied };
}

export type { ModerationActionType };
