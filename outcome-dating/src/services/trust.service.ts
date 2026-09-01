import { z } from 'zod';
import type { Ctx } from '../lib/ctx.js';
import { requireUserActor } from '../lib/ctx.js';
import type { Page, TrustEvent, TrustLevel, TrustSummary } from '../domain/types.js';
import * as notification from './notification.service.js';

export type { TrustLevel };

/**
 * trust.service — the §6 trust score/level and its visibility into
 * "why is my level limited".
 * Spec: §6, §24.11, §25.6 (recalculation job).
 *
 * Owning agent: E.
 *
 * ---------------------------------------------------------------------
 * SCORING MODEL (internal — see report to orchestrator for the numbers;
 * NEVER returned by any user-facing export in this file)
 * ---------------------------------------------------------------------
 * `recalculateTrustScore` composes two additive layers on top of a fixed
 * base, then clamps to [0,100]:
 *
 *  1. STATE factors (`computeStateFactors`) — read live from `users`,
 *     `profiles`, `payment_methods`, `user_photos` at recalculation time.
 *     These are current-status facts (verified email, verified payment
 *     method, profile completeness, account age, and a "clean record"
 *     bonus for zero negative trust_events in the last 90 days) rather
 *     than one-off events, and no other service is wired (per
 *     INTERFACES.md's call graph) to push them as `trust_events` — only
 *     `trust.service.ts` itself can observe "is my email verified right
 *     now", so re-deriving them fresh every recalculation (rather than
 *     trying to keep an event log in sync with them) is what makes this
 *     recomputation idempotent and safe to re-run any time (spec §25.6).
 *
 *  2. EVENT factors — `sum(trust_events.delta)` for the user, all time.
 *     This is the append-only log spec §6 describes ("recomputed rather
 *     than mutated in place, so the why is always reconstructable") and
 *     is how the REST of §6.2's factors reach the score: completed dates,
 *     positive/negative post-date feedback, no-shows, payment failures/
 *     chargebacks, and moderation actions/appeal outcomes all arrive here
 *     as `trust_events` rows pushed by the module that is actually
 *     wired (per the "may call" graph) to observe them —
 *     `dateProposal.service` (dateProposal ─▶ trust), `redemption.service`
 *     (redemption ─▶ trust), `moderation.service` (moderation ─▶ trust),
 *     and `appeal.service` (appeal ─▶ trust). `trust.service.ts` does not
 *     — and structurally cannot, per the call graph — read `messages`,
 *     `date_proposals`, or `reports` itself to derive these; it only
 *     knows what's been recorded via `recordTrustEvent`.
 *
 * `TRUST_EVENT_TYPES` below is the recommended vocabulary other agents'
 * `recordTrustEvent` calls should use — the *delta value* is always
 * caller-supplied (frozen signature: `RecordTrustEventInput.delta` is
 * required, not derived from `eventType` here), but using these exact
 * strings lets `getMyTrustSummary`'s "recent negative events" rendering
 * produce a friendly label instead of falling back to a generic one.
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
 *
 * ---------------------------------------------------------------------
 * NEW EXPORTS beyond the frozen INTERFACES.md list (flagged loudly for
 * cross-agent coordination — nothing frozen was removed or changed):
 * ---------------------------------------------------------------------
 *  - `can(ctx, action, subject)` — the single total capability check the
 *    task brief asks trust.service to expose for §6.4. Agent C
 *    (interest/message services) and the API/HTTP layer are the intended
 *    callers.
 *  - `linksPerHourLimitFor(ctx, trustLevel)` — ties §6.4's clickability
 *    tier to §12.3's per-hour numeric link cap so the two can't drift out
 *    of sync when an admin retunes `trust.link_min_level`. See the
 *    "§6.4 vs §12.3 precedence" comment on `can()` below.
 */

// =====================================================================
// Recognized trust_events vocabulary (recommendation, not enforcement —
// event_type is a free-text column; unrecognized values still count
// toward the score via their delta, they just render generically in
// `recentNegativeEvents`).
// =====================================================================
export const TRUST_EVENT_TYPES = {
  DATE_COMPLETED: 'date_completed',
  POSITIVE_POST_DATE_FEEDBACK: 'positive_post_date_feedback',
  NEGATIVE_POST_DATE_FEEDBACK: 'negative_post_date_feedback',
  NO_SHOW: 'no_show',
  PAYMENT_FAILED: 'payment_failed',
  PAYMENT_CHARGEBACK: 'payment_chargeback',
  MODERATION_WARNING: 'moderation_action_warning',
  MODERATION_RESTRICTION: 'moderation_action_restriction',
  MODERATION_SHADOWBAN: 'moderation_action_shadowban',
  MODERATION_SUSPENSION: 'moderation_action_suspension',
  APPEAL_APPROVED: 'appeal_approved',
} as const;

/** Static, non-generated label for a recognized negative event_type (spec §1/§20 "no generated prose"). Unrecognized types fall back to a generic label — never crashes on an unexpected string from another service. */
const NEGATIVE_EVENT_LABELS: Record<string, string> = {
  [TRUST_EVENT_TYPES.NO_SHOW]: 'missed date',
  [TRUST_EVENT_TYPES.NEGATIVE_POST_DATE_FEEDBACK]: 'negative post-date feedback',
  [TRUST_EVENT_TYPES.PAYMENT_FAILED]: 'payment failure',
  [TRUST_EVENT_TYPES.PAYMENT_CHARGEBACK]: 'payment chargeback',
  [TRUST_EVENT_TYPES.MODERATION_WARNING]: 'warning',
  [TRUST_EVENT_TYPES.MODERATION_RESTRICTION]: 'account restriction',
  [TRUST_EVENT_TYPES.MODERATION_SHADOWBAN]: 'reduced visibility action',
  [TRUST_EVENT_TYPES.MODERATION_SUSPENSION]: 'account suspension',
};
const GENERIC_NEGATIVE_LABEL = 'report or automated safety flag';

const LEVEL_RANK: Record<TrustLevel, number> = { limited: 0, standard: 1, trusted: 2, elite: 3 };
const TRUST_SCORE_BASE = 50; // matches users.trust_score DEFAULT in 001_init.sql — a new account starts neutral.

// ---- internal, never-exposed state-factor weights (see module doc above) ----
const WEIGHT_VERIFIED_EMAIL = 8;
const WEIGHT_VERIFIED_PAYMENT_METHOD = 8;
const WEIGHT_COMPLETED_PROFILE_MAX = 6; // scaled by profiles.profile_completeness / 100
const WEIGHT_ACCOUNT_AGE_PER_MONTH = 1;
const WEIGHT_ACCOUNT_AGE_MAX = 10;
const WEIGHT_CLEAN_RECORD_BONUS = 3;
const CLEAN_RECORD_LOOKBACK_DAYS = 90;
const CLEAN_RECORD_MIN_ACCOUNT_AGE_DAYS = 14;

/**
 * INTERNAL ONLY. Carries every named factor and its applied weight.
 * Deliberately NOT exported alongside a public API surface, and
 * deliberately a *different shape* from `TrustSummary` (domain/types.ts)
 * so there is no accidental code path that could serialize this straight
 * into an HTTP response — spec §6.3 "Do not expose the exact formula."
 * Useful for admin tooling / tests that need to assert *why* a score is
 * what it is.
 */
export interface InternalTrustBreakdown {
  userId: string;
  base: number;
  stateFactors: Array<{ name: string; weight: number }>;
  stateSum: number;
  eventSum: number;
  eventCount: number;
  rawScore: number; // base + stateSum + eventSum, before clamping
  clampedScore: number;
  level: TrustLevel;
}

function daysBetween(a: Date, b: Date): number {
  return (b.getTime() - a.getTime()) / (1000 * 60 * 60 * 24);
}

async function computeStateFactors(
  ctx: Ctx,
  userId: string,
): Promise<{ factors: Array<{ name: string; weight: number }>; sum: number; emailVerified: boolean; paymentVerified: boolean; profileCompleteness: number; hasFacePhoto: boolean; accountAgeDays: number }> {
  const { rows: userRows } = await ctx.db.query<{ email_verified_at: Date | null; created_at: Date }>(
    'SELECT email_verified_at, created_at FROM users WHERE id = $1',
    [userId],
  );
  const user = userRows[0];
  const emailVerified = !!user?.email_verified_at;
  const accountAgeDays = user ? Math.max(0, daysBetween(user.created_at, ctx.clock.now())) : 0;

  const { rows: pmRows } = await ctx.db.query<{ count: string }>(
    `SELECT count(*)::text AS count FROM payment_methods WHERE user_id = $1 AND deleted_at IS NULL AND verified_at IS NOT NULL`,
    [userId],
  );
  const paymentVerified = Number(pmRows[0]?.count ?? '0') > 0;

  const { rows: profileRows } = await ctx.db.query<{ profile_completeness: number }>(
    'SELECT profile_completeness FROM profiles WHERE user_id = $1',
    [userId],
  );
  const profileCompleteness = profileRows[0]?.profile_completeness ?? 0;

  const { rows: photoRows } = await ctx.db.query<{ count: string }>(
    `SELECT count(*)::text AS count FROM user_photos WHERE user_id = $1 AND is_primary AND face_detected IS TRUE`,
    [userId],
  );
  const hasFacePhoto = Number(photoRows[0]?.count ?? '0') > 0;

  const factors: Array<{ name: string; weight: number }> = [];
  if (emailVerified) factors.push({ name: 'verified_email', weight: WEIGHT_VERIFIED_EMAIL });
  if (paymentVerified) factors.push({ name: 'verified_payment_method', weight: WEIGHT_VERIFIED_PAYMENT_METHOD });

  const profileWeight = Math.round((profileCompleteness / 100) * WEIGHT_COMPLETED_PROFILE_MAX);
  if (profileWeight > 0) factors.push({ name: 'profile_completeness', weight: profileWeight });

  const ageWeight = Math.min(WEIGHT_ACCOUNT_AGE_MAX, Math.floor(accountAgeDays / 30) * WEIGHT_ACCOUNT_AGE_PER_MONTH);
  if (ageWeight > 0) factors.push({ name: 'account_age', weight: ageWeight });

  if (accountAgeDays >= CLEAN_RECORD_MIN_ACCOUNT_AGE_DAYS) {
    const { rows: negRows } = await ctx.db.query<{ count: string }>(
      `SELECT count(*)::text AS count FROM trust_events WHERE user_id = $1 AND delta < 0 AND created_at >= $2`,
      [userId, new Date(ctx.clock.now().getTime() - CLEAN_RECORD_LOOKBACK_DAYS * 24 * 60 * 60 * 1000)],
    );
    if (Number(negRows[0]?.count ?? '0') === 0) {
      factors.push({ name: 'clean_record', weight: WEIGHT_CLEAN_RECORD_BONUS });
    }
  }

  const sum = factors.reduce((acc, f) => acc + f.weight, 0);
  return { factors, sum, emailVerified, paymentVerified, profileCompleteness, hasFacePhoto, accountAgeDays };
}

async function sumTrustEvents(ctx: Ctx, userId: string): Promise<{ sum: number; count: number }> {
  const { rows } = await ctx.db.query<{ sum: string | null; count: string }>(
    'SELECT COALESCE(sum(delta), 0)::text AS sum, count(*)::text AS count FROM trust_events WHERE user_id = $1',
    [userId],
  );
  return { sum: Number(rows[0]?.sum ?? '0'), count: Number(rows[0]?.count ?? '0') };
}

/** Builds the full internal breakdown for `userId` without writing anything. Shared by `recalculateTrustScore` and `getMyTrustSummary`. */
async function computeBreakdown(ctx: Ctx, userId: string): Promise<InternalTrustBreakdown & { emailVerified: boolean; paymentVerified: boolean; profileCompleteness: number; hasFacePhoto: boolean; accountAgeDays: number }> {
  const state = await computeStateFactors(ctx, userId);
  const events = await sumTrustEvents(ctx, userId);
  const rawScore = TRUST_SCORE_BASE + state.sum + events.sum;
  const clampedScore = Math.max(0, Math.min(100, Math.round(rawScore)));
  const level = await levelForScore(ctx, clampedScore);
  return {
    userId,
    base: TRUST_SCORE_BASE,
    stateFactors: state.factors,
    stateSum: state.sum,
    eventSum: events.sum,
    eventCount: events.count,
    rawScore,
    clampedScore,
    level,
    emailVerified: state.emailVerified,
    paymentVerified: state.paymentVerified,
    profileCompleteness: state.profileCompleteness,
    hasFacePhoto: state.hasFacePhoto,
    accountAgeDays: state.accountAgeDays,
  };
}

export async function getMyTrustSummary(ctx: Ctx): Promise<TrustSummary> {
  const actor = requireUserActor(ctx);
  const breakdown = await computeBreakdown(ctx, actor.userId);

  const actionableImprovements: string[] = [];
  if (breakdown.level !== 'elite') {
    if (!breakdown.emailVerified) actionableImprovements.push('Verify your email address');
    if (!breakdown.hasFacePhoto) actionableImprovements.push('Add a clear face photo');
    if (!breakdown.paymentVerified) actionableImprovements.push('Verify a payment method');
    if (breakdown.profileCompleteness < 80) actionableImprovements.push('Complete more of your profile questions');
    const { rows: dateRows } = await ctx.db.query<{ count: string }>(
      `SELECT count(*)::text AS count FROM trust_events WHERE user_id = $1 AND event_type = $2`,
      [actor.userId, TRUST_EVENT_TYPES.DATE_COMPLETED],
    );
    if (Number(dateRows[0]?.count ?? '0') === 0) actionableImprovements.push('Complete a date');
  }

  const { rows: negativeRows } = await ctx.db.query<{ event_type: string; count: string }>(
    `SELECT event_type, count(*)::text AS count
       FROM trust_events
      WHERE user_id = $1 AND delta < 0 AND created_at >= $2
      GROUP BY event_type
      ORDER BY max(created_at) DESC
      LIMIT 5`,
    [actor.userId, new Date(ctx.clock.now().getTime() - CLEAN_RECORD_LOOKBACK_DAYS * 24 * 60 * 60 * 1000)],
  );
  const recentNegativeEvents = negativeRows.map((r) => {
    const label = NEGATIVE_EVENT_LABELS[r.event_type] ?? GENERIC_NEGATIVE_LABEL;
    const count = Number(r.count);
    return `${count} ${label}${count > 1 ? 's' : ''}`;
  });

  return {
    trustLevel: breakdown.level,
    trustScore: breakdown.clampedScore,
    actionableImprovements,
    recentNegativeEvents,
  };
}

export async function listMyTrustEvents(ctx: Ctx, params?: { cursor?: string; limit?: number }): Promise<Page<TrustEvent>> {
  const actor = requireUserActor(ctx);
  const limit = Math.min(100, Math.max(1, params?.limit ?? 20));
  const offset = params?.cursor ? Number(params.cursor) : 0;

  const { rows } = await ctx.db.query<{
    id: string;
    user_id: string;
    event_type: string;
    delta: number;
    metadata: Record<string, unknown>;
    created_at: Date;
  }>(
    `SELECT id, user_id, event_type, delta, metadata, created_at
       FROM trust_events
      WHERE user_id = $1
      ORDER BY created_at DESC, id DESC
      LIMIT $2 OFFSET $3`,
    [actor.userId, limit + 1, offset],
  );

  const hasMore = rows.length > limit;
  const page = hasMore ? rows.slice(0, limit) : rows;
  return {
    items: page.map(rowToTrustEvent),
    nextCursor: hasMore ? String(offset + limit) : null,
  };
}

function rowToTrustEvent(row: { id: string; user_id: string; event_type: string; delta: number; metadata: Record<string, unknown>; created_at: Date }): TrustEvent {
  return {
    id: row.id,
    userId: row.user_id,
    eventType: row.event_type,
    delta: Number(row.delta),
    metadata: row.metadata ?? {},
    createdAt: row.created_at,
  };
}

export interface RecordTrustEventInput {
  userId: string;
  eventType: string;
  delta: number;
  metadata?: Record<string, unknown>;
}

const RecordTrustEventSchema = z.object({
  userId: z.string().uuid(),
  eventType: z.string().trim().min(1).max(100),
  delta: z.number().finite().min(-100).max(100),
  metadata: z.record(z.unknown()).optional(),
});

/** Appends one `trust_events` row. Does NOT recompute `trust_score` itself — callers that need the recomputation to happen synchronously should call `recalculateTrustScore` afterward (spec §25.6 lists exactly which events trigger it: report, date completed, payment failure, profile change, verification change). */
export async function recordTrustEvent(ctx: Ctx, input: RecordTrustEventInput): Promise<TrustEvent> {
  const parsed = RecordTrustEventSchema.parse(input);

  const { rows } = await ctx.db.query<{
    id: string;
    user_id: string;
    event_type: string;
    delta: number;
    metadata: Record<string, unknown>;
    created_at: Date;
  }>(
    `INSERT INTO trust_events (user_id, event_type, delta, metadata)
     VALUES ($1, $2, $3, $4::jsonb)
     RETURNING id, user_id, event_type, delta, metadata, created_at`,
    [parsed.userId, parsed.eventType, parsed.delta, JSON.stringify(parsed.metadata ?? {})],
  );
  return rowToTrustEvent(rows[0]!);
}

/** §25.6: recompute `trust_score`/`trust_level` for one user from their event history, persist, and notify on a level change. */
export async function recalculateTrustScore(ctx: Ctx, userId: string): Promise<{ trustScore: number; trustLevel: TrustLevel }> {
  const before = await ctx.db.query<{ trust_level: TrustLevel }>('SELECT trust_level FROM users WHERE id = $1', [userId]);
  const previousLevel = before.rows[0]?.trust_level;

  const breakdown = await computeBreakdown(ctx, userId);

  await ctx.db.query('UPDATE users SET trust_score = $1, trust_level = $2 WHERE id = $3', [
    breakdown.clampedScore,
    breakdown.level,
    userId,
  ]);

  if (previousLevel && previousLevel !== breakdown.level) {
    // Best-effort: a notification-delivery hiccup must never roll back an
    // already-persisted trust score change (notification.service.ts is a
    // leaf owned by a sibling agent and may not be implemented yet during
    // parallel development — see module doc above).
    try {
      await notification.notify(ctx, {
        userId,
        eventType: 'trust_level_changed',
        channel: 'in_app',
        payload: { previousLevel, newLevel: breakdown.level },
      });
    } catch (err) {
      ctx.logger.warn('trust.recalculateTrustScore: notify failed', { userId, err: (err as Error).message });
    }
  }

  return { trustScore: breakdown.clampedScore, trustLevel: breakdown.level };
}

/**
 * Decision-layer addition (Open Question OQ-7, see docs/conformance.md):
 * whether the numeric `trustScore` may be shown to the user at all, as
 * opposed to `trustLevel` alone (spec §6.1 "not shown as an exact number
 * unless product explicitly decides otherwise"). `getMyTrustSummary`
 * itself deliberately keeps its frozen contract — it always returns both
 * fields (see this file's own module doc, and `TrustSummary.trustScore`'s
 * doc comment in domain/types.ts: "service always returns it") — so tests
 * and other server-side consumers of the full breakdown are unaffected.
 * This is the single source of truth for the *display* gate: the HTTP
 * layer should call this before deciding whether to serialize `trustScore`
 * into a response, rather than re-deriving the config check itself.
 */
export async function shouldExposeRawTrustScore(ctx: Ctx): Promise<boolean> {
  return ctx.config.get('trust.expose_raw_score');
}

/** Maps a 0-100 score to a level using the configured boundaries (spec §6.1, tunable via §21 config). Pure given the config values, but reads them via `ctx.config`, so it's `async`. */
export async function levelForScore(ctx: Ctx, score: number): Promise<TrustLevel> {
  const clamped = Math.max(0, Math.min(100, score));
  const bounds = await ctx.config.getMany(['trust.level_elite_min', 'trust.level_trusted_min', 'trust.level_standard_min'] as const);
  if (clamped >= bounds['trust.level_elite_min']) return 'elite';
  if (clamped >= bounds['trust.level_trusted_min']) return 'trusted';
  if (clamped >= bounds['trust.level_standard_min']) return 'standard';
  return 'limited';
}

/** Spec §6.4 "Send links" row: whether `userId`'s trust level meets `trust.link_min_level`. */
export async function canSendClickableLinks(ctx: Ctx, userId: string): Promise<boolean> {
  const { rows } = await ctx.db.query<{ trust_level: TrustLevel }>('SELECT trust_level FROM users WHERE id = $1', [userId]);
  const level = rows[0]?.trust_level ?? 'limited';
  return await levelMeetsLinkMinimum(ctx, level);
}

async function levelMeetsLinkMinimum(ctx: Ctx, level: TrustLevel): Promise<boolean> {
  const minLevel = await ctx.config.get('trust.link_min_level');
  return LEVEL_RANK[level] >= LEVEL_RANK[minLevel];
}

// =====================================================================
// `can()` — §6.4 capability matrix. NEW export (not in the frozen
// INTERFACES.md list) — see module doc header for why, and flag this to
// Agent C (interest.service, message.service) and the API/HTTP layer as a
// new call surface to wire up.
// =====================================================================

export type TrustGatedAction = 'browse' | 'send_interest' | 'chat' | 'send_links' | 'propose_date';

export interface CapabilitySubject {
  trustLevel: TrustLevel;
  /** Only consulted for `propose_date` — §6.4 "Date proposals: requires payment method at Limited". */
  hasVerifiedPaymentMethod?: boolean;
}

export interface CapabilityDecision {
  allowed: boolean;
  /** Present (and true) when `allowed` but under a reduced quota — §6.4 "Send interests: limited" for Limited trust. Callers apply their own reduced numeric cap (e.g. `interest.service.ts`'s own config-driven limit); this flag only signals *that* a reduction applies. */
  limited?: boolean;
  /** Only meaningful for `send_links`. */
  linkMode?: 'blocked' | 'warn' | 'clickable';
  /** Static, stable reason code — safe to show to the user, carries no weights. */
  reasonCode?: 'payment_method_required' | 'reduced_quota_low_trust' | 'links_disabled_low_trust' | 'links_warning_standard_trust';
}

/**
 * Single total capability check for the §6.4 restriction table. Every
 * branch is exhaustive and returns a decision — there is no action this
 * function can be asked about that it doesn't have an answer for.
 *
 * ---------------------------------------------------------------------
 * §6.4 vs §12.3 PRECEDENCE (documented per the task brief's "note the
 * tension"):
 * ---------------------------------------------------------------------
 * §6.4's "Send links" row and §12.3's per-hour link-count limits
 * (`chat.max_links_per_hour_low_trust` / `..._standard_trust`) answer two
 * DIFFERENT questions and are evaluated at different times, in this
 * order:
 *
 *   1. SEND-TIME (§12.3, `message.service.ts`, not this file): "may this
 *      message containing N links be sent at all right now?" — a rate
 *      limit keyed on a volume of links per rolling hour. This gate runs
 *      FIRST, before the message is persisted.
 *   2. RENDER-TIME (§6.4/§19.4, `canSendClickableLinks`/`can()` here):
 *      "once a link has been sent, should it render as clickable, as
 *      plain text, or clickable-with-warning?" This is a display
 *      concern, independent of how many links were sent.
 *
 *   A link that fails gate 1 is never sent, so gate 2 never runs for it.
 *   A link that passes gate 1 always still goes through gate 2 — passing
 *   the rate limit does not make a Limited-trust user's links clickable.
 *
 *   The actual "tension": §12.3's config keys hardcode a binary
 *   "low_trust" vs "standard_trust" split, while §6.4/`trust.link_min_level`
 *   is a single configurable rank boundary. If an admin retunes
 *   `trust.link_min_level` (e.g. from 'standard' to 'trusted'), §6.4's
 *   clickability boundary moves, but §12.3's *bucket assignment* would
 *   silently stay pinned to the literal 'limited' level unless it is
 *   ALSO derived from `trust.link_min_level`. Precedence: this module's
 *   level-vs-`trust.link_min_level` comparison is authoritative for
 *   BOTH concerns' bucket boundary — `linksPerHourLimitFor` below is the
 *   function `message.service.ts` should call (instead of re-deriving
 *   its own "is this user low-trust" comparison) so retuning
 *   `trust.link_min_level` moves both the clickability rule and the
 *   per-hour cap bucket together. The two *numeric* limits themselves
 *   (0 vs 5 per hour) remain §12.3's own separately configurable values.
 */
export async function can(ctx: Ctx, action: TrustGatedAction, subject: CapabilitySubject): Promise<CapabilityDecision> {
  switch (action) {
    case 'browse':
      return { allowed: true };

    case 'chat':
      return { allowed: true };

    case 'send_interest':
      if (subject.trustLevel === 'limited') {
        return { allowed: true, limited: true, reasonCode: 'reduced_quota_low_trust' };
      }
      return { allowed: true };

    case 'propose_date': {
      if (subject.trustLevel === 'limited' && !subject.hasVerifiedPaymentMethod) {
        return { allowed: false, reasonCode: 'payment_method_required' };
      }
      return { allowed: true };
    }

    case 'send_links': {
      const minLevel = await ctx.config.get('trust.link_min_level');
      const rank = LEVEL_RANK[subject.trustLevel];
      const minRank = LEVEL_RANK[minLevel];
      if (rank < minRank) {
        return { allowed: true, linkMode: 'blocked', reasonCode: 'links_disabled_low_trust' };
      }
      if (rank === minRank) {
        return { allowed: true, linkMode: 'warn', reasonCode: 'links_warning_standard_trust' };
      }
      return { allowed: true, linkMode: 'clickable' };
    }
  }
}

/**
 * §12.3's per-hour link cap for `trustLevel`, bucketed via the SAME
 * level-vs-`trust.link_min_level` comparison `can()`/`canSendClickableLinks`
 * use (see the precedence note on `can()` above) rather than a hardcoded
 * `=== 'limited'` check, so the two mechanisms can't drift apart when an
 * admin retunes `trust.link_min_level`. `message.service.ts` should call
 * this instead of re-deriving its own trust-tier comparison.
 */
export async function linksPerHourLimitFor(ctx: Ctx, trustLevel: TrustLevel): Promise<number> {
  const meetsMinimum = await levelMeetsLinkMinimum(ctx, trustLevel);
  return meetsMinimum
    ? ctx.config.get('chat.max_links_per_hour_standard_trust')
    : ctx.config.get('chat.max_links_per_hour_low_trust');
}

/**
 * Decision-layer addition (Open Question OQ-4, see docs/conformance.md):
 * §6.4's "Send interests: limited" restriction-table cell for Limited
 * trust never had a concrete number — only the shared, all-tiers
 * `interest.outgoing_pending_limit` (5) existed. `interest.service.ts`
 * should call this instead of reading `interest.outgoing_pending_limit`
 * unconditionally, so a Limited-trust user's effective cap is the
 * (smaller) `interest.outgoing_pending_limit_limited_tier` — mirrors
 * `linksPerHourLimitFor`'s same trust-tier-bucketing pattern above.
 */
export async function outgoingInterestPendingLimitFor(ctx: Ctx, trustLevel: TrustLevel): Promise<number> {
  return trustLevel === 'limited'
    ? ctx.config.get('interest.outgoing_pending_limit_limited_tier')
    : ctx.config.get('interest.outgoing_pending_limit');
}

