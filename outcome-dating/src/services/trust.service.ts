import type { Ctx } from '../lib/ctx.js';
import { NotImplementedError } from '../lib/errors.js';
import type { Page, TrustEvent, TrustLevel, TrustSummary } from '../domain/types.js';

export type { TrustLevel };

/**
 * trust.service — the §6 trust score/level and its visibility into
 * "why is my level limited".
 * Spec: §6, §24.11, §25.6 (recalculation job).
 *
 * Owning agent: E.
 *
 * Invariants:
 *  - `getMyTrustSummary` MUST show actionable items and recent negative
 *    events (spec §6.3 example) and MUST NOT expose the exact weighting
 *    formula — `actionableImprovements`/`recentNegativeEvents` are static
 *    template strings keyed off which factors are missing/present, never
 *    raw factor weights.
 *  - `levelForScore` reads the boundaries from config
 *    (`trust.level_standard_min`, `trust.level_trusted_min`,
 *    `trust.level_elite_min`) rather than hardcoding §6.1's table, so an
 *    admin can retune them (spec §21 "config-driven variables").
 *  - `recalculateTrustScore` is the only function that writes
 *    `users.trust_score`/`trust_level` — it must derive the new score from
 *    the full `trust_events` history (or an incremental delta plus prior
 *    score; implementation's choice) and record *why* via
 *    `recordTrustEvent`, never adjust the column directly elsewhere.
 *  - A trust_level change fires a `trust_level_changed` notification
 *    (spec §20.1) — that call belongs in `recalculateTrustScore`.
 *  - `canSendLinks`/link-clickability is governed by `trust.link_min_level`
 *    (spec §6.4, §19.4) — `message.service.ts` calls this rather than
 *    re-deriving the comparison.
 */

export async function getMyTrustSummary(ctx: Ctx): Promise<TrustSummary> {
  throw new NotImplementedError('trust.getMyTrustSummary');
}

export async function listMyTrustEvents(ctx: Ctx, params?: { cursor?: string; limit?: number }): Promise<Page<TrustEvent>> {
  throw new NotImplementedError('trust.listMyTrustEvents');
}

export interface RecordTrustEventInput {
  userId: string;
  eventType: string;
  delta: number;
  metadata?: Record<string, unknown>;
}

/** Appends one `trust_events` row. Does NOT recompute `trust_score` itself — callers that need the recomputation to happen synchronously should call `recalculateTrustScore` afterward (spec §25.6 lists exactly which events trigger it: report, date completed, payment failure, profile change, verification change). */
export async function recordTrustEvent(ctx: Ctx, input: RecordTrustEventInput): Promise<TrustEvent> {
  throw new NotImplementedError('trust.recordTrustEvent');
}

/** §25.6: recompute `trust_score`/`trust_level` for one user from their event history, persist, and notify on a level change. */
export async function recalculateTrustScore(ctx: Ctx, userId: string): Promise<{ trustScore: number; trustLevel: TrustLevel }> {
  throw new NotImplementedError('trust.recalculateTrustScore');
}

/** Maps a 0-100 score to a level using the configured boundaries (spec §6.1, tunable via §21 config). Pure given the config values, but reads them via `ctx.config`, so it's `async`. */
export async function levelForScore(ctx: Ctx, score: number): Promise<TrustLevel> {
  throw new NotImplementedError('trust.levelForScore');
}

/** Spec §6.4 "Send links" row: whether `userId`'s trust level meets `trust.link_min_level`. */
export async function canSendClickableLinks(ctx: Ctx, userId: string): Promise<boolean> {
  throw new NotImplementedError('trust.canSendClickableLinks');
}
