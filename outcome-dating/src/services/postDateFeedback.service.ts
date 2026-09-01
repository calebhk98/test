import { z } from 'zod';
import type { Ctx } from '../lib/ctx.js';
import { requireUserActor } from '../lib/ctx.js';
import { ConflictError, ForbiddenError, NotFoundError } from '../lib/errors.js';
import { hoursBetween } from '../lib/time.js';
import { KNOWN_FLAGS } from '../config/flags.service.js';
import type { TrustLevel } from '../domain/types.js';
import { getTypeHandler } from '../domain/questions/typeHandlers.js';
import type { QuestionType, QuestionTypeDefinition } from '../domain/questions/types.js';
import * as reportService from './report.service.js';
import * as trustService from './trust.service.js';
import * as notificationService from './notification.service.js';

/**
 * postDateFeedback.service — the post-date check-in.
 *
 * Product framing (not a spec section — a direct product-owner ask):
 * "There 100% needs to be a post-date check-in. We need to know how it
 * went, not just for safety, but also for potential future matches." This
 * module is the one place all three purposes meet, and its entire design
 * is about keeping them from corrupting each other:
 *
 *   1. SAFETY  — `safetyFlag`/`safetyDetails`. Routed into the existing
 *      `report.service#submitReport` machinery (never reimplemented —
 *      see "SAFETY ROUTING" below) and NEVER returned by any export here
 *      to anyone but the row's own submitter. See "SAFETY ISOLATION".
 *   2. OUTCOME TRUTH  — `outcome`, one of exactly four values
 *      (`did_not_happen` / `happened_bad` / `happened_fine` /
 *      `happened_good`), never collapsed into a single satisfaction
 *      score. Each has its own, deliberately different, platform effect
 *      — see "OUTCOME EFFECTS".
 *   3. FUTURE MATCHING SIGNAL  — `runMatchingSignalSweep`, which never
 *      writes a `user_question_answers` row directly and only ever creates a *pending*
 *      `behavioral_prompt_suggestions` row (the existing §17 mechanism —
 *      see behavioralPrompt.service.ts) for the user to explicitly answer
 *      or skip.
 *
 * Extends the existing `post_date_feedback` table (see
 * db/migrations/016_post_date_feedback.sql for the full column-by-column
 * rationale) rather than duplicating it. `dateProposal.service
 * #submitPostDateFeedback` (frozen per INTERFACES.md) is left completely
 * untouched and keeps writing the same four legacy columns to the same
 * table — the two paths share one row per (date_proposal_id, user_id) via
 * the table's existing UNIQUE constraint, they just each own a disjoint
 * set of columns, so neither can clobber the other's data. (That legacy
 * endpoint has no outcome/safety-routing/trust/matching-signal behavior
 * at all — it just stores a boolean and never reaches moderation or
 * trust.service.ts. This module is the intended real implementation of
 * the product ask; whichever agent owns dateProposal.service.ts's route
 * wiring may want to deprecate `POST /date-proposals/:id/feedback` in
 * favor of `POST /date-proposals/:id/check-in` below, but that file is
 * outside this module's edit scope beyond the two completion hooks noted
 * below, so it is left in place and flagged in the build report instead.)
 *
 * `submitCheckIn` reads `date_proposals` directly (existence/participant/
 * status/timing) rather than calling `dateProposal.service#getDateProposal`
 * — `dateProposal.service.ts` itself calls INTO this module (the two
 * completion hooks below), so this module deliberately never imports
 * back from it, avoiding a module-cycle. Reading `date_proposals` (and
 * `users`, `user_question_answers`, `question_bank`) directly is the same
 * "narrow read of a sibling's table" pattern report.service.ts/
 * trust.service.ts already use throughout (e.g.
 * `report.service#reporterCredibility` reading `users.trust_level`
 * directly rather than importing trust.service.ts).
 *
 * ---------------------------------------------------------------------
 * ONE-SIDED BY DEFAULT
 * ---------------------------------------------------------------------
 * Nothing here ever waits for, or requires, both participants to submit.
 * Every effect (trust delta, safety report, prompt bookkeeping, matching
 * signal) is computed from a SINGLE row the moment it exists. Most dates
 * will only ever get one side's check-in — that is the expected case, not
 * a degraded one.
 *
 * ---------------------------------------------------------------------
 * OUTCOME EFFECTS (§ "must lead to very different platform actions")
 * ---------------------------------------------------------------------
 *   did_not_happen  — no trust effect on either party. A single-sided
 *     "it didn't happen" claim is exactly the kind of thing a retaliating
 *     or embarrassed user could file about a real date, so on its own it
 *     changes nothing about the other party's trust score. (It IS still
 *     stored — it's the product's own "did dates actually happen" truth
 *     signal — just not auto-scored against anyone. Corroboration/
 *     dispute handling for a contested "did it happen" already exists
 *     as its own thing, `disputeResolution.service.ts` — this module
 *     deliberately does not build a second one.)
 *   happened_bad    — a small NEGATIVE trust event for the other party,
 *     weighted down for retaliation risk — see "RETALIATION RESISTANCE".
 *     Never, by itself, routes to moderation/report — a subjectively bad
 *     date is not a safety problem (that's `safetyFlag`'s job, entirely
 *     independent of `outcome`).
 *   happened_fine   — a small POSITIVE trust event for the other party.
 *   happened_good   — a larger POSITIVE trust event for the other party,
 *     and the input the matching-signal sweep looks for patterns in.
 *
 * ---------------------------------------------------------------------
 * RETALIATION RESISTANCE (rejected person rating out of spite)
 * ---------------------------------------------------------------------
 * Chosen mitigations, deliberately layered rather than relying on one:
 *   1. ASYMMETRY — only `happened_bad` can ever cost the other party
 *      anything, and it is capped small (see `BASE_NEGATIVE_DELTA`);
 *      `happened_bad` NEVER reaches moderation/report on its own, unlike
 *      a safety flag, which always does. A spiteful "bad date" rating can
 *      cost trust points, never an account restriction.
 *   2. WEIGHT BY THE RATER'S OWN TRUST — `NEGATIVE_WEIGHT_BY_TRUST`,
 *      mirroring (independently, since report.service's own multiplier
 *      table is private to that file) the same "trusted reporters count
 *      more" idea `report.service#REPORTER_TRUST_MULTIPLIER` already
 *      uses for reports.
 *   3. SERIAL-NEGATIVE DAMPING — a rater whose recent outcome history is
 *      overwhelmingly `happened_bad` (>`HIGH_NEGATIVE_RATE_THRESHOLD` of
 *      their last `NEGATIVE_HISTORY_WINDOW` rated dates) has their
 *      negative weight further multiplied down by `SERIAL_NEGATIVE_
 *      DAMPING` — someone rating every date badly reads as a
 *      venting/retaliation pattern, not a string of genuinely bad dates,
 *      and is discounted accordingly (mirrors report.service's own
 *      anti-brigading instinct, applied to a single serial rater instead
 *      of a cluster).
 *   4. LOCKED AT FIRST SUBMISSION — the trust effect for `outcome` fires
 *      exactly once per (date_proposal_id, user_id), on the row's true
 *      first INSERT (detected via the `xmax = 0` Postgres idiom — see
 *      `submitCheckIn`), never again on a later edit to the same row. A
 *      user can still edit their own notes/safety fields afterward, but
 *      cannot toggle `outcome` back and forth to apply repeated trust
 *      damage.
 *   5. SAFETY-FLAG CORROORATION FOR THE MILD TIER — see "SAFETY ROUTING".
 *
 * ---------------------------------------------------------------------
 * SAFETY ROUTING (must route into moderation, must carry more weight than
 * an ordinary report, must not require a separate manual report)
 * ---------------------------------------------------------------------
 * `safetyFlag: 'incident'` (an immediate, credible, serious concern)
 * routes into `report.service#submitReport` (category `unsafe_behavior`
 * — the highest-severity category legitimately applicable here; the
 * other very-high category, `minor_suspected`, has a specific,
 * unrelated, corroboration-gated fast path in report.service.ts that this
 * module must not misuse) THE MOMENT it is first submitted — no
 * corroboration required, mirroring the spec's own "act immediately on a
 * credible severe signal" instinct. This module NEVER reimplements
 * `scoreReport` — it only ever calls `submitReport`, which already scores
 * category + reporter trust + the relationship multiplier (a completed
 * date guarantees `hasRelationship` is true, i.e. the FULL multiplier, not
 * the discounted stranger-report one) + prior-report history + recency.
 * Because it is auto-filed at the correct high-severity category with the
 * full relationship multiplier and zero manual-filing friction, it
 * already scores at or above an "ordinary" (often lower-category,
 * often no-relationship) manually-filed report, with no need to (and no
 * way to, without touching report.service.ts) hand-tune its weight
 * further.
 *
 * `safetyFlag: 'concern'` (milder — "something felt off") does NOT file a
 * report on its own. A single spiteful "concern" flag from a rejected
 * date must not be able to trigger a report by itself. Instead it is
 * recorded, and `countDistinctSafetyFlaggersAgainst` checks whether the
 * SAME reported user has now accumulated `CONCERN_CORROBORATION_
 * THRESHOLD` (2) or more DISTINCT flaggers (across different dates) —
 * once corroborated by a second independent person, the report files
 * automatically on that corroborating submission. This is the same
 * "one report alone can't hurt someone; independent corroboration can"
 * shape as report.service.ts's own minor_suspected fast path, reused
 * here for the mild safety tier instead of rebuilt from scratch.
 *
 * Either way, the reporter is always the check-in submitter (`ctx.actor`)
 * and `reportedId` is always the other date participant — the user never
 * has to separately open a report form.
 *
 * ---------------------------------------------------------------------
 * SAFETY ISOLATION (never visible to the other party, ever, in any
 * aggregate, not inferable from timing or observable behavior)
 * ---------------------------------------------------------------------
 *   - `safetyFlag`/`safetyDetails` are returned ONLY by `getMyCheckIn`/
 *     `submitCheckIn`, both scoped to `WHERE user_id = <the caller>` —
 *     structurally impossible for the other participant to read, since
 *     no export here ever accepts "give me the other side's row".
 *   - The trust events this module records directly (`recordTrustEvent`
 *     for `outcome`) NEVER carry `dateProposalId`, `safetyFlag`, or any
 *     other correlatable identifier in `metadata` — `{}` every time (see
 *     `applyOutcomeTrustEffectBestEffort`). A user reading their OWN
 *     `GET /me/trust/events` (a route this module does not own) can see a
 *     generic "negative post-date feedback" line, per spec §6.3's own
 *     transparency example, but can never pin it to a specific date or
 *     partner.
 *   - A safety flag reaches the reported party, if at all, exactly the
 *     way ANY other user-filed `unsafe_behavior` report would — through
 *     `report.service.ts`'s own guarantee that reporter identity is never
 *     exposed to the reported user (see that file's module doc). Nothing
 *     in this module adds a distinguishing "this came from a post-date
 *     check-in" marker anywhere user-visible, so a report that originated
 *     here is indistinguishable, from the reported party's side, from one
 *     any stranger could have filed manually. That indistinguishability
 *     — not a separate access-control rule — is what makes a safety
 *     answer unobservable: there is no code path, anywhere, that renders
 *     "post-date check-in" as a string reachable by the reported user.
 *   - Submitting a check-in — of ANY kind, safety or not — never
 *     notifies the other party. There is no `notify(otherUserId, ...)`
 *     call anywhere in this file. This removes the timing side-channel
 *     the brief calls out explicitly: nothing observable happens to the
 *     other party's notifications, API responses, or date-proposal state
 *     at the moment a check-in (safety or otherwise) is submitted.
 *   - `submitCheckIn` never writes to `date_proposals.status` or any
 *     other field the other participant's own `GET /date-proposals/:id`
 *     response would surface — a safety flag cannot be inferred from a
 *     status change either.
 *
 * ---------------------------------------------------------------------
 * MATCHING SIGNAL (§17 behavioral-prompt mechanism — never silently
 * changes stated answers/sorting, only ever an explicit skippable
 * question)
 * ---------------------------------------------------------------------
 * `runMatchingSignalSweep` looks, per user, for a compatibility question
 * (in the ONE typed question bank, `question_bank`/`user_question_answers`
 * — db/migrations/008_questions.sql) where the AVERAGE divergence between
 * what that user says they want (`user_question_answers.preference_value`)
 * and what their `happened_good`-rated dates' partners actually reported
 * about themselves on that same question
 * (`user_question_answers.self_value`) is large — i.e. "the dates you rate
 * as GOOD tend not to match what you said you want, on this specific
 * axis". Divergence is `1 - satisfaction`, using EXACTLY the same
 * `src/domain/questions/typeHandlers.ts#satisfaction` function
 * `compatibility.service.ts` scores matches with (0 = perfectly satisfies,
 * 1 = fully diverges) — this is what lets the sweep work uniformly across
 * every question TYPE (`scale`, `single_choice`, `multi_choice`,
 * `frequency`), unlike the OLD bank's flat 1-5 numeric diff, which was
 * only ever meaningful for a plain numeric scale. When the average
 * crosses `MATCHING_SIGNAL_DIVERGENCE_THRESHOLD` across at least
 * `MIN_GOOD_DATES_FOR_MATCHING_SIGNAL` good-outcome dates, it inserts
 * exactly one `pending` row into the EXISTING `behavioral_prompt_
 * suggestions` table (same table, same conflict target, same `status`
 * lifecycle as behavioralPrompt.service.ts's own tag-based trigger — this
 * is "feed the existing mechanism", not a parallel one). It NEVER calls
 * `question.service#putMyQuestionAnswer` and NEVER writes to
 * `user_question_answers` — turning a suggestion into a real answer, or
 * skipping it, is entirely `behavioralPrompt.service#respondToSuggestion`'s
 * job, driven by the user's own explicit response, exactly as §17
 * requires.
 *
 * ---------------------------------------------------------------------
 * TIMING (prompt after scheduled end, with a window, and a reminder — do
 * not prompt endlessly; ctx.clock throughout)
 * ---------------------------------------------------------------------
 * See `runCheckInPromptSweep`/`ensureCheckInPromptSent`. Local constants
 * (`INITIAL_PROMPT_DELAY_HOURS` etc.), not `ctx.config`, for the same
 * file-ownership-boundary reason `behavioralPrompt.service.ts` already
 * documents on `MIN_PATTERN_ACCEPT_COUNT`: `config.service.ts`'s key
 * registry is a hardcoded typed list this module may not edit.
 */

// =====================================================================
// Shared vocabulary
// =====================================================================

export const CHECK_IN_OUTCOMES = ['did_not_happen', 'happened_bad', 'happened_fine', 'happened_good'] as const;
export type CheckInOutcome = (typeof CHECK_IN_OUTCOMES)[number];

export const SAFETY_FLAG_LEVELS = ['none', 'concern', 'incident'] as const;
export type SafetyFlagLevel = (typeof SAFETY_FLAG_LEVELS)[number];

export const WOULD_MEET_AGAIN_VALUES = ['yes', 'no', 'unsure'] as const;
export type WouldMeetAgain = (typeof WOULD_MEET_AGAIN_VALUES)[number];

export interface PostDateCheckIn {
  id: string;
  dateProposalId: string;
  outcome: CheckInOutcome;
  wouldMeetAgain: WouldMeetAgain | null;
  safetyFlag: SafetyFlagLevel;
  safetyDetails: string | null;
  notes: string | null;
  /** Whether this check-in's safety flag has (so far) resulted in a report.service.ts report. Never reveals the report's id/category/reportedId beyond what the submitter already knows. */
  reportFiled: boolean;
  createdAt: Date;
}

function boolToTriState(v: boolean | null): WouldMeetAgain | null {
  if (v === true) return 'yes';
  if (v === false) return 'no';
  return null; // covers both "unsure" and "not applicable" (did_not_happen) — deliberately indistinguishable, same as §8.5's "prefer not to say" null.
}

function triStateToBool(v: WouldMeetAgain | undefined): boolean | null {
  if (v === 'yes') return true;
  if (v === 'no') return false;
  return null;
}

function describeError(err: unknown): string {
  return err instanceof Error ? err.message : String(err);
}

// =====================================================================
// submitCheckIn / getMyCheckIn
//
// Deliberately NEVER gated behind KNOWN_FLAGS.POST_DATE_FEEDBACK (unlike
// the prompt sweep and the matching-signal sweep below) — a feature flag
// must never be able to silently swallow a safety report. Only the
// PROACTIVE nudging and the discretionary matching-signal derivation are
// flag-gated; the endpoint that actually accepts a check-in always works.
// =====================================================================

const ELIGIBLE_CHECK_IN_STATUSES = new Set(['ticketed', 'completed', 'completed_unverified', 'disputed', 'no_show']);

const SubmitCheckInSchema = z.object({
  outcome: z.enum(CHECK_IN_OUTCOMES),
  wouldMeetAgain: z.enum(WOULD_MEET_AGAIN_VALUES).optional(),
  safetyFlag: z.enum(SAFETY_FLAG_LEVELS).optional().default('none'),
  safetyDetails: z.string().trim().min(1).max(1000).optional(),
  notes: z.string().trim().min(1).max(1000).optional(),
});

export type SubmitCheckInInput = z.input<typeof SubmitCheckInSchema>;

interface CheckInRow {
  id: string;
  date_proposal_id: string;
  user_id: string;
  outcome: CheckInOutcome | null;
  would_meet_again: boolean | null;
  safety_flag: SafetyFlagLevel;
  safety_details: string | null;
  notes: string | null;
  report_id: string | null;
  created_at: Date;
}

function toCheckInView(row: CheckInRow): PostDateCheckIn {
  return {
    id: row.id,
    dateProposalId: row.date_proposal_id,
    outcome: row.outcome as CheckInOutcome,
    wouldMeetAgain: boolToTriState(row.would_meet_again),
    safetyFlag: row.safety_flag,
    safetyDetails: row.safety_details,
    notes: row.notes,
    reportFiled: row.report_id !== null,
    createdAt: row.created_at,
  };
}

/**
 * Submit (or update) the caller's own post-date check-in for one date
 * proposal. Usable the instant the date is ticketed/resolved, by either
 * participant, independently — see module doc "ONE-SIDED BY DEFAULT".
 */
interface CheckInProposalRow {
  id: string;
  conversation_id: string;
  proposer_id: string;
  recipient_id: string;
  status: string;
  scheduled_start: Date;
}

/** Existence/participant check on `date_proposals`, read directly rather than via `dateProposal.service#getDateProposal` — see module doc for why (avoiding a module cycle). Mirrors that function's own NotFoundError/ForbiddenError contract exactly. */
async function loadCheckInProposal(ctx: Ctx, dateProposalId: string, userId: string): Promise<CheckInProposalRow> {
  const { rows } = await ctx.db.query<CheckInProposalRow>(
    `SELECT id, conversation_id, proposer_id, recipient_id, status, scheduled_start FROM date_proposals WHERE id = $1`,
    [dateProposalId],
  );
  const row = rows[0];
  if (!row) throw new NotFoundError('Date proposal not found.', { dateProposalId });
  if (row.proposer_id !== userId && row.recipient_id !== userId) {
    throw new ForbiddenError('You are not a participant in this date proposal.');
  }
  return row;
}

export async function submitCheckIn(ctx: Ctx, dateProposalId: string, input: unknown): Promise<PostDateCheckIn> {
  const { userId } = requireUserActor(ctx);
  const parsed = SubmitCheckInSchema.parse(input);

  const proposal = await loadCheckInProposal(ctx, dateProposalId, userId);
  if (!ELIGIBLE_CHECK_IN_STATUSES.has(proposal.status)) {
    throw new ConflictError('A check-in can’t be submitted for this date right now.', { status: proposal.status });
  }
  if (ctx.clock.now().getTime() < proposal.scheduled_start.getTime()) {
    throw new ConflictError('Cannot submit a check-in before the date has started.');
  }

  const otherUserId = userId === proposal.proposer_id ? proposal.recipient_id : proposal.proposer_id;
  const wouldMeetAgainBool = parsed.outcome === 'did_not_happen' ? null : triStateToBool(parsed.wouldMeetAgain);
  const safetyDetails = parsed.safetyFlag === 'none' ? null : (parsed.safetyDetails ?? null);

  const { rows } = await ctx.db.query<CheckInRow & { inserted: boolean }>(
    `INSERT INTO post_date_feedback (date_proposal_id, user_id, outcome, would_meet_again, safety_flag, safety_details, notes)
     VALUES ($1, $2, $3, $4, $5, $6, $7)
     ON CONFLICT (date_proposal_id, user_id) DO UPDATE SET
       outcome = EXCLUDED.outcome,
       would_meet_again = EXCLUDED.would_meet_again,
       safety_flag = EXCLUDED.safety_flag,
       safety_details = EXCLUDED.safety_details,
       notes = EXCLUDED.notes
     RETURNING id, date_proposal_id, user_id, outcome, would_meet_again, safety_flag, safety_details, notes, report_id, created_at,
               (xmax = 0) AS inserted`,
    [dateProposalId, userId, parsed.outcome, wouldMeetAgainBool, parsed.safetyFlag, safetyDetails, parsed.notes ?? null],
  );
  let row = rows[0]!;

  // Retaliation resistance #4 ("locked at first submission"): the outcome
  // trust effect fires only on the row's true first INSERT, never again
  // on a later edit to the same (date_proposal_id, user_id) row.
  if (row.inserted) {
    await applyOutcomeTrustEffectBestEffort(ctx, { raterId: userId, targetUserId: otherUserId, outcome: parsed.outcome });
  }

  // Safety routing can still fire on a later edit (escalating from 'none'
  // to a flag, or from 'concern' to 'incident') — see module doc "SAFETY
  // ROUTING". Guarded by `report_id IS NULL` so a declared incident is
  // only ever routed once.
  if (parsed.safetyFlag !== 'none' && row.report_id === null) {
    const filedReportId = await routeSafetyFlagBestEffort(ctx, {
      dateProposalId,
      conversationId: proposal.conversation_id,
      submitterId: userId,
      reportedId: otherUserId,
      safetyFlag: parsed.safetyFlag,
      safetyDetails,
    });
    if (filedReportId) {
      const { rows: updatedRows } = await ctx.db.query<CheckInRow>(
        `UPDATE post_date_feedback SET report_id = $1 WHERE date_proposal_id = $2 AND user_id = $3
         RETURNING id, date_proposal_id, user_id, outcome, would_meet_again, safety_flag, safety_details, notes, report_id, created_at`,
        [filedReportId, dateProposalId, userId],
      );
      row = { ...updatedRows[0]!, inserted: row.inserted };
    }
  }

  return toCheckInView(row);
}

/** The caller's own check-in for one date proposal, if they've submitted one via `submitCheckIn`. Never the other participant's — see module doc "SAFETY ISOLATION" (the scoping here is what makes that structural, not a permission check someone could get wrong). */
export async function getMyCheckIn(ctx: Ctx, dateProposalId: string): Promise<PostDateCheckIn> {
  const { userId } = requireUserActor(ctx);
  const { rows } = await ctx.db.query<CheckInRow>(
    `SELECT id, date_proposal_id, user_id, outcome, would_meet_again, safety_flag, safety_details, notes, report_id, created_at
       FROM post_date_feedback
      WHERE date_proposal_id = $1 AND user_id = $2 AND outcome IS NOT NULL`,
    [dateProposalId, userId],
  );
  const row = rows[0];
  if (!row) throw new NotFoundError('No check-in found for this date.', { dateProposalId });
  return toCheckInView(row);
}

// =====================================================================
// Outcome -> trust effect
// =====================================================================

const POSITIVE_FINE_DELTA = 2;
const POSITIVE_GOOD_DELTA = 5;
const BASE_NEGATIVE_DELTA = -4;

const NEGATIVE_WEIGHT_BY_TRUST: Record<TrustLevel, number> = { limited: 0.4, standard: 0.7, trusted: 1.0, elite: 1.2 };
const NEGATIVE_HISTORY_WINDOW = 10;
const MIN_HISTORY_FOR_DAMPENING = 4;
const HIGH_NEGATIVE_RATE_THRESHOLD = 0.6;
const SERIAL_NEGATIVE_DAMPING = 0.3;

/** See module doc "RETALIATION RESISTANCE" #2/#3. Queries `users`/`post_date_feedback` directly rather than importing anything private from trust.service.ts/report.service.ts, mirroring report.service#reporterCredibility's own "read users.trust_level directly" pattern. */
async function negativeFeedbackRetaliationWeight(ctx: Ctx, raterId: string): Promise<number> {
  const { rows: userRows } = await ctx.db.query<{ trust_level: TrustLevel }>('SELECT trust_level FROM users WHERE id = $1', [raterId]);
  let weight = NEGATIVE_WEIGHT_BY_TRUST[userRows[0]?.trust_level ?? 'standard'];

  const { rows: histRows } = await ctx.db.query<{ outcome: CheckInOutcome }>(
    `SELECT outcome FROM post_date_feedback
      WHERE user_id = $1 AND outcome IN ('happened_bad', 'happened_fine', 'happened_good')
      ORDER BY created_at DESC LIMIT $2`,
    [raterId, NEGATIVE_HISTORY_WINDOW],
  );
  if (histRows.length >= MIN_HISTORY_FOR_DAMPENING) {
    const negativeRate = histRows.filter((r) => r.outcome === 'happened_bad').length / histRows.length;
    if (negativeRate > HIGH_NEGATIVE_RATE_THRESHOLD) weight *= SERIAL_NEGATIVE_DAMPING;
  }
  return weight;
}

async function applyOutcomeTrustEffectBestEffort(
  ctx: Ctx,
  input: { raterId: string; targetUserId: string; outcome: CheckInOutcome },
): Promise<void> {
  try {
    if (input.outcome === 'did_not_happen') return; // see module doc "OUTCOME EFFECTS"
    if (input.outcome === 'happened_fine') {
      await trustService.recordTrustEvent(ctx, {
        userId: input.targetUserId,
        eventType: trustService.TRUST_EVENT_TYPES.POSITIVE_POST_DATE_FEEDBACK,
        delta: POSITIVE_FINE_DELTA,
        metadata: {}, // deliberately no dateProposalId/identifying info — see module doc "SAFETY ISOLATION"
      });
      return;
    }
    if (input.outcome === 'happened_good') {
      await trustService.recordTrustEvent(ctx, {
        userId: input.targetUserId,
        eventType: trustService.TRUST_EVENT_TYPES.POSITIVE_POST_DATE_FEEDBACK,
        delta: POSITIVE_GOOD_DELTA,
        metadata: {},
      });
      return;
    }
    // happened_bad
    const weight = await negativeFeedbackRetaliationWeight(ctx, input.raterId);
    const delta = Math.round(BASE_NEGATIVE_DELTA * weight);
    if (delta === 0) return; // fully dampened (e.g. a low-trust serial negative rater) — no-op rather than a zero-delta audit row
    await trustService.recordTrustEvent(ctx, {
      userId: input.targetUserId,
      eventType: trustService.TRUST_EVENT_TYPES.NEGATIVE_POST_DATE_FEEDBACK,
      delta,
      metadata: {},
    });
  } catch (err) {
    ctx.logger.warn('postDateFeedback.trust_event_failed', { targetUserId: input.targetUserId, outcome: input.outcome, err: describeError(err) });
  }
}

// =====================================================================
// Safety flag -> report.service routing
// =====================================================================

const CONCERN_CORROBORATION_THRESHOLD = 2;

const SAFETY_REPORT_DETAILS_PREFIX: Record<'incident' | 'concern_corroborated', string> = {
  incident: 'Post-date check-in: safety incident flagged.',
  concern_corroborated: 'Post-date check-in: corroborated safety concern (independent flags from more than one date).',
};

function buildSafetyReportDetails(kind: 'incident' | 'concern_corroborated', userDetails: string | null): string {
  const prefix = SAFETY_REPORT_DETAILS_PREFIX[kind];
  return userDetails ? `${prefix} ${userDetails}` : prefix;
}

/** Distinct submitters who have flagged ANY non-'none' safety concern against `reportedId`, across all of their own dates with that person — the corroboration count for the mild ('concern') tier. See module doc "SAFETY ROUTING". */
async function countDistinctSafetyFlaggersAgainst(ctx: Ctx, reportedId: string, excludeUserId: string): Promise<number> {
  const { rows } = await ctx.db.query<{ count: string }>(
    `SELECT count(DISTINCT pdf.user_id)::text AS count
       FROM post_date_feedback pdf
       JOIN date_proposals dp ON dp.id = pdf.date_proposal_id
      WHERE pdf.safety_flag <> 'none'
        AND pdf.user_id <> $2
        AND ((dp.proposer_id = $1 AND pdf.user_id = dp.recipient_id) OR (dp.recipient_id = $1 AND pdf.user_id = dp.proposer_id))`,
    [reportedId, excludeUserId],
  );
  return Number(rows[0]?.count ?? '0');
}

/** Returns the filed report's id, or null if nothing was (yet) filed (a non-corroborated 'concern'). Never reimplements report.service#scoreReport — only ever calls submitReport. */
async function routeSafetyFlag(
  ctx: Ctx,
  input: {
    conversationId: string;
    submitterId: string;
    reportedId: string;
    safetyFlag: Exclude<SafetyFlagLevel, 'none'>;
    safetyDetails: string | null;
  },
): Promise<string | null> {
  if (input.safetyFlag === 'incident') {
    const report = await reportService.submitReport(ctx, {
      reportedId: input.reportedId,
      conversationId: input.conversationId,
      category: 'unsafe_behavior',
      details: buildSafetyReportDetails('incident', input.safetyDetails),
    });
    return report.id;
  }

  // 'concern' — corroboration-gated, see module doc "SAFETY ROUTING".
  const priorDistinctFlaggers = await countDistinctSafetyFlaggersAgainst(ctx, input.reportedId, input.submitterId);
  if (priorDistinctFlaggers + 1 < CONCERN_CORROBORATION_THRESHOLD) return null;

  const report = await reportService.submitReport(ctx, {
    reportedId: input.reportedId,
    conversationId: input.conversationId,
    category: 'unsafe_behavior',
    details: buildSafetyReportDetails('concern_corroborated', input.safetyDetails),
  });
  return report.id;
}

async function routeSafetyFlagBestEffort(
  ctx: Ctx,
  input: {
    dateProposalId: string;
    conversationId: string;
    submitterId: string;
    reportedId: string;
    safetyFlag: Exclude<SafetyFlagLevel, 'none'>;
    safetyDetails: string | null;
  },
): Promise<string | null> {
  try {
    return await routeSafetyFlag(ctx, input);
  } catch (err) {
    // Logged at error, not warn — unlike an ordinary best-effort side
    // effect (a notification, say), a safety flag that fails to route
    // is the one failure mode in this file worth being loud about.
    ctx.logger.error('postDateFeedback.safety_routing_failed', {
      dateProposalId: input.dateProposalId,
      safetyFlag: input.safetyFlag,
      err: describeError(err),
    });
    return null;
  }
}

// =====================================================================
// Timing — prompt after scheduled end, with a window, and a reminder.
// Do not prompt endlessly. ctx.clock throughout, never Date.now()/new
// Date() directly.
// =====================================================================

const PROMPT_ELIGIBLE_STATUSES = ['ticketed', 'completed', 'completed_unverified', 'disputed', 'no_show'] as const;
const INITIAL_PROMPT_DELAY_HOURS = 3; // wait this long after scheduled_end before the first nudge
const REMINDER_DELAY_HOURS = 48; // wait this long after the first nudge before the (single) reminder
const MAX_PROMPT_WINDOW_DAYS = 14; // never prompt at all once this many days past scheduled_end have elapsed
const MAX_PROMPTS_PER_USER = 2; // initial + exactly one reminder, then stop for good

interface PromptableProposalRow {
  id: string;
  proposer_id: string;
  recipient_id: string;
  scheduled_end: Date;
  status: string;
}

async function notifyBestEffort(ctx: Ctx, input: notificationService.NotifyInput): Promise<void> {
  try {
    await notificationService.notify(ctx, input);
  } catch (err) {
    ctx.logger.warn('postDateFeedback.notify_failed', { eventType: input.eventType, userId: input.userId, err: describeError(err) });
  }
}

/** One participant's prompt/reminder decision for one date proposal. Idempotent and safe to call repeatedly with any clock — see module doc "TIMING". */
async function maybePromptParticipant(ctx: Ctx, row: PromptableProposalRow, userId: string, now: Date): Promise<'prompted' | 'reminded' | 'skipped'> {
  const enabled = await ctx.flags.isEnabled(KNOWN_FLAGS.POST_DATE_FEEDBACK, { userId });
  if (!enabled) return 'skipped';

  const { rows: existingFeedback } = await ctx.db.query(
    `SELECT 1 FROM post_date_feedback WHERE date_proposal_id = $1 AND user_id = $2 AND outcome IS NOT NULL`,
    [row.id, userId],
  );
  if (existingFeedback.length > 0) return 'skipped'; // already checked in — nothing to prompt for

  if (hoursBetween(row.scheduled_end, now) > MAX_PROMPT_WINDOW_DAYS * 24) return 'skipped'; // "do not prompt endlessly"

  const { rows: promptRows } = await ctx.db.query<{ prompt_count: number; last_prompted_at: Date | null }>(
    `SELECT prompt_count, last_prompted_at FROM post_date_feedback_prompts WHERE date_proposal_id = $1 AND user_id = $2`,
    [row.id, userId],
  );
  const existing = promptRows[0];

  if (!existing) {
    if (hoursBetween(row.scheduled_end, now) < INITIAL_PROMPT_DELAY_HOURS) return 'skipped'; // too soon
    await notifyBestEffort(ctx, { userId, eventType: 'post_date_feedback_request', channel: 'in_app', payload: { dateProposalId: row.id } });
    await ctx.db.query(
      `INSERT INTO post_date_feedback_prompts (date_proposal_id, user_id, prompt_count, first_prompted_at, last_prompted_at)
       VALUES ($1, $2, 1, $3, $3)
       ON CONFLICT (date_proposal_id, user_id) DO NOTHING`,
      [row.id, userId, now],
    );
    return 'prompted';
  }

  if (existing.prompt_count >= MAX_PROMPTS_PER_USER) return 'skipped'; // already sent the one reminder — stop for good
  if (!existing.last_prompted_at || hoursBetween(existing.last_prompted_at, now) < REMINDER_DELAY_HOURS) return 'skipped'; // not due yet

  await notifyBestEffort(ctx, { userId, eventType: 'post_date_feedback_request', channel: 'in_app', payload: { dateProposalId: row.id } });
  await ctx.db.query(
    `UPDATE post_date_feedback_prompts SET prompt_count = prompt_count + 1, last_prompted_at = $3 WHERE date_proposal_id = $1 AND user_id = $2`,
    [row.id, userId, now],
  );
  return 'reminded';
}

/**
 * Eagerly evaluates the prompt decision for both participants of one date
 * proposal, right now, per `ctx.clock`. Called (best-effort, additively)
 * from the two `dateProposal.service.ts` sites where a proposal actually
 * reaches `completed`/`completed_unverified` — see that file's two
 * one-line hooks. Purely a responsiveness nicety: `runCheckInPromptSweep`
 * below applies the exact same gating/timing independently and will catch
 * anything this misses (including tickets that never got confirmed at
 * all — the "did the date even happen" case this module cares about most
 * — which never call this function).
 */
export async function ensureCheckInPromptSent(ctx: Ctx, dateProposalId: string): Promise<void> {
  const { rows } = await ctx.db.query<PromptableProposalRow>(
    `SELECT id, proposer_id, recipient_id, scheduled_end, status FROM date_proposals WHERE id = $1`,
    [dateProposalId],
  );
  const row = rows[0];
  if (!row || !(PROMPT_ELIGIBLE_STATUSES as readonly string[]).includes(row.status)) return;

  const now = ctx.clock.now();
  await maybePromptParticipant(ctx, row, row.proposer_id, now);
  await maybePromptParticipant(ctx, row, row.recipient_id, now);
}

export interface CheckInPromptSweepResult {
  promptsSent: number;
  remindersSent: number;
}

/**
 * The general sweep — meant to be wired into `src/jobs/*` by whichever
 * agent owns that directory (outside this module's edit scope; see build
 * report). Scans every `date_proposals` row that ever reached `ticketed`
 * and whose `scheduled_end` falls within the prompt window, for BOTH
 * participants independently — including proposals that never got
 * confirmed/completed at all, which is exactly the "the date might not
 * have happened" case a completion-only hook would miss entirely.
 */
export async function runCheckInPromptSweep(ctx: Ctx): Promise<CheckInPromptSweepResult> {
  const now = ctx.clock.now();
  const cutoff = new Date(now.getTime() - MAX_PROMPT_WINDOW_DAYS * 24 * 60 * 60 * 1000);

  const { rows } = await ctx.db.query<PromptableProposalRow>(
    `SELECT id, proposer_id, recipient_id, scheduled_end, status FROM date_proposals
      WHERE status = ANY($1) AND scheduled_end <= $2 AND scheduled_end >= $3`,
    [PROMPT_ELIGIBLE_STATUSES as unknown as string[], now, cutoff],
  );

  let promptsSent = 0;
  let remindersSent = 0;
  for (const row of rows) {
    for (const userId of [row.proposer_id, row.recipient_id]) {
      const outcome = await maybePromptParticipant(ctx, row, userId, now);
      if (outcome === 'prompted') promptsSent++;
      else if (outcome === 'reminded') remindersSent++;
    }
  }
  return { promptsSent, remindersSent };
}

// =====================================================================
// Matching signal — feeds the EXISTING §17 behavioral_prompt_suggestions
// mechanism (behavioralPrompt.service.ts). See module doc "MATCHING
// SIGNAL". Gated behind BOTH KNOWN_FLAGS.POST_DATE_FEEDBACK (this data
// comes from post-date feedback) and KNOWN_FLAGS.BEHAVIORAL_QUESTION_
// PROMPTS (it surfaces through that mechanism) per-user, mirroring
// behavioralPrompt.service#detectPatternsForUser's own gating.
// =====================================================================

export const MIN_GOOD_DATES_FOR_MATCHING_SIGNAL = 3;
// Normalized 0..1 (see module doc "MATCHING SIGNAL": divergence is
// `1 - satisfaction`, and `satisfaction` is always 0..1 regardless of
// question type). 0.5 is the direct normalization of the OLD bank's
// threshold (an absolute diff of 2, out of that bank's fixed 0-4 range on
// a 1-5 scale question -> 2/4 = 0.5) — same real-world strictness, just
// expressed on the new bank's type-agnostic scale.
const MATCHING_SIGNAL_DIVERGENCE_THRESHOLD = 0.5;

interface DivergenceRow {
  question_slug: string;
  question_bank_id: string;
  question_type: QuestionType;
  type_definition: QuestionTypeDefinition;
  preference_value: unknown;
  other_self_value: unknown;
}

/** One candidate user's pass: finds the single question with the largest average good-date divergence and inserts one pending suggestion for it, if any clears the threshold. At most one new suggestion per user per sweep run, to keep prompting bounded. */
async function createMatchingSignalSuggestion(ctx: Ctx, userId: string): Promise<boolean> {
  const { rows } = await ctx.db.query<DivergenceRow>(
    `SELECT a_mine.question_slug AS question_slug,
            qb.id AS question_bank_id,
            qb.question_type AS question_type,
            qb.type_definition AS type_definition,
            a_mine.preference_value AS preference_value,
            a_other.self_value AS other_self_value
       FROM post_date_feedback pdf
       JOIN date_proposals dp ON dp.id = pdf.date_proposal_id
       JOIN user_question_answers a_mine ON a_mine.user_id = pdf.user_id AND a_mine.status = 'answered'
       JOIN user_question_answers a_other
         ON a_other.question_slug = a_mine.question_slug
        AND a_other.status = 'answered'
        AND a_other.user_id = CASE WHEN dp.proposer_id = pdf.user_id THEN dp.recipient_id ELSE dp.proposer_id END
       JOIN question_bank qb ON qb.slug = a_mine.question_slug AND qb.is_current = true AND qb.active = true
      WHERE pdf.user_id = $1
        AND pdf.outcome = 'happened_good'
        AND pdf.matching_signal_processed_at IS NULL`,
    [userId],
  );

  const byQuestion = new Map<string, { questionBankId: string; diffs: number[] }>();
  for (const r of rows) {
    const handler = getTypeHandler(r.question_type);
    const satisfaction = handler.satisfaction(r.type_definition, r.other_self_value, r.preference_value);
    const divergence = 1 - satisfaction;
    const bucket = byQuestion.get(r.question_slug) ?? { questionBankId: r.question_bank_id, diffs: [] };
    bucket.diffs.push(divergence);
    byQuestion.set(r.question_slug, bucket);
  }

  let best: { questionBankId: string; slug: string; avgDivergence: number } | undefined;
  for (const [slug, { questionBankId, diffs }] of byQuestion) {
    if (diffs.length < MIN_GOOD_DATES_FOR_MATCHING_SIGNAL) continue;
    const avgDivergence = diffs.reduce((a, b) => a + b, 0) / diffs.length;
    if (avgDivergence < MATCHING_SIGNAL_DIVERGENCE_THRESHOLD) continue;
    if (!best || avgDivergence > best.avgDivergence) best = { questionBankId, slug, avgDivergence };
  }
  if (!best) return false;

  // Same table, same conflict target as behavioralPrompt.service#detectPatternsForUser
  // — this IS the existing mechanism, not a parallel one. Never writes to
  // `user_question_answers`; the suggestion is presented and can be
  // skipped, exactly like the tag-triggered kind
  // (behavioralPrompt.service#respondToSuggestion). `question_id` here is
  // a `question_bank` id (current version at detection time) — see
  // `db/migrations/022_drop_old_question_bank.sql` for the FK repoint.
  const { rows: inserted } = await ctx.db.query<{ id: string }>(
    `INSERT INTO behavioral_prompt_suggestions (user_id, question_id, trigger_kind, trigger_label, status, created_at)
     VALUES ($1, $2, 'post_date_outcome', $3, 'pending', $4)
     ON CONFLICT (user_id, question_id) WHERE status = 'pending' DO NOTHING
     RETURNING id`,
    [userId, best.questionBankId, best.slug, ctx.clock.now()],
  );
  return inserted.length > 0;
}

export interface MatchingSignalSweepResult {
  usersConsidered: number;
  suggestionsCreated: number;
}

/** Meant to be wired into `src/jobs/*` alongside `runCheckInPromptSweep` — outside this module's edit scope. See build report. */
export async function runMatchingSignalSweep(ctx: Ctx): Promise<MatchingSignalSweepResult> {
  const { rows: candidateRows } = await ctx.db.query<{ user_id: string }>(
    `SELECT user_id FROM post_date_feedback
      WHERE outcome = 'happened_good' AND matching_signal_processed_at IS NULL
      GROUP BY user_id
     HAVING count(*) >= $1`,
    [MIN_GOOD_DATES_FOR_MATCHING_SIGNAL],
  );

  let suggestionsCreated = 0;
  let usersConsidered = 0;
  for (const { user_id: userId } of candidateRows) {
    const [feedbackEnabled, promptsEnabled] = await Promise.all([
      ctx.flags.isEnabled(KNOWN_FLAGS.POST_DATE_FEEDBACK, { userId }),
      ctx.flags.isEnabled(KNOWN_FLAGS.BEHAVIORAL_QUESTION_PROMPTS, { userId }),
    ]);
    if (!feedbackEnabled || !promptsEnabled) continue;

    usersConsidered++;
    if (await createMatchingSignalSuggestion(ctx, userId)) suggestionsCreated++;

    // Mark considered rows processed regardless of whether a suggestion
    // was created this round, so the sweep does bounded work — see
    // module doc "MATCHING SIGNAL".
    await ctx.db.query(
      `UPDATE post_date_feedback SET matching_signal_processed_at = $2
        WHERE user_id = $1 AND outcome IN ('happened_good', 'happened_bad') AND matching_signal_processed_at IS NULL`,
      [userId, ctx.clock.now()],
    );
  }

  return { suggestionsCreated, usersConsidered };
}
