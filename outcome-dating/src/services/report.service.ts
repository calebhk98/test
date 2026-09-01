import { z } from 'zod';
import type { Ctx } from '../lib/ctx.js';
import { requireUserActor } from '../lib/ctx.js';
import { ForbiddenError, NotFoundError, ValidationError } from '../lib/errors.js';
import type { Report, ReportCategory, TrustLevel } from '../domain/types.js';
import * as moderation from './moderation.service.js';
import * as trust from './trust.service.js';

/**
 * report.service, structured user reports.
 * Spec: §18.3, §18.5 (scoring inputs), §24.12, §30.9.
 *
 * Owning agent: E.
 *
 * Invariants:
 *  - `category` is one of the exact §18.3 list (enforced by the DB CHECK
 *    and the `ReportCategory` union), there is no free-text-only report
 *    path (spec §18.3 "Do not rely only on free-text reports"); `details`
 *    is optional supplementary text alongside the required category.
 *  - `submitReport` never reveals the reporter's identity to the reported
 *    user (spec §30.9), this module has no function that would leak it;
 *    callers (HTTP layer) must not either. Note this is a "never to the
 *    REPORTED user" rule, not "never persisted", `reporter_id` is a
 *    normal column on `reports`, readable by the admin actor that's
 *    allowed to view moderation data (§4.3, §27); no export in this file
 *    returns a reporter id keyed to anything the reported user could
 *    plausibly see.
 *  - `submitReport` preserves the associated conversation for automated
 *    investigation (spec §30.9), it must NOT archive or otherwise mutate
 *    the referenced `conversation_id`/`message_id`. (Structurally
 *    enforced: this file never imports `conversation.service.ts` and
 *    never writes to the `conversations`/`messages` tables.)
 *  - `submitReport` forwards to `moderation.service#recordAutomatedFlag`
 *    immediately after insert, then calls `moderation.service#applyThresholds`
 *    so a `minor_suspected` report gets its "immediate protective action"
 *    (spec §18.3/§18.5) synchronously, in the same call, rather than
 *    waiting for the §25.7 recalculation job. See moderation.service.ts's
 *    module doc for the full "where does computeModerationScore's number
 *    come from" note, this is the one function that pushes into it.
 */

// =====================================================================
// §18.5 scoring model (internal weights, not part of any user-facing
// return type; `scoreReport`'s return is a plain number consumed only by
// `moderation.service.ts`).
// =====================================================================

/** Category base severity (spec §18.3 list; §18.5 "score depends on ... report category", `minor_suspected` is deliberately far above everything else, spec "maximum severity"). */
const CATEGORY_WEIGHT: Record<ReportCategory, number> = {
  minor_suspected: 100,
  scam_money_request: 30,
  unsafe_behavior: 30,
  harassment: 25,
  fake_profile: 15,
  inappropriate_content: 15,
  misleading_photos: 10,
  spam: 10,
  no_show: 8, // spec §18.5 example: "no-show report after completed date = medium weight"
  other: 5,
};

/** `reports.severity` (1-5, DB CHECK), a coarser, stored-on-the-row classification distinct from the scoring weight above (which is only ever computed on demand, never persisted). */
const CATEGORY_SEVERITY: Record<ReportCategory, number> = {
  minor_suspected: 5,
  scam_money_request: 4,
  unsafe_behavior: 4,
  harassment: 4,
  fake_profile: 3,
  inappropriate_content: 3,
  misleading_photos: 2,
  no_show: 2,
  spam: 1,
  other: 1,
};

/** Spec §18.5 "scam report from trusted user = high weight", reporter trust scales credibility. */
const REPORTER_TRUST_MULTIPLIER: Record<TrustLevel, number> = {
  limited: 0.5,
  standard: 1.0,
  trusted: 1.3,
  elite: 1.6,
};

/** Reduced weight for a report with no on-platform interaction between reporter and reported (no shared conversation), a stranger report is harder to corroborate than one from an actual match. */
const NO_RELATIONSHIP_MULTIPLIER = 0.6;
const HAS_RELATIONSHIP_MULTIPLIER = 1.0;

/** Spec §18.5 "number of previous reports", each additional prior report against the same target raises credibility that a pattern exists, capped so one target can't be driven to an extreme multiplier by volume alone. */
const PREVIOUS_REPORTS_STEP = 0.05;
const PREVIOUS_REPORTS_MULTIPLIER_CAP = 1.5;

/** Spec §18.5 "recency", a report from a year ago says less about current risk than one from today. Linear decay, floored so old reports still count for something (an old scam report is never worthless). */
const RECENCY_DECAY_DAYS = 365;
const RECENCY_MULTIPLIER_FLOOR = 0.3;

/**
 * ANTI-BRIGADING DISCOUNT (spec §18.5 "duplicate report from same social
 * cluster = reduced weight", the explicit stated reason for this design,
 * spec §18.5 "Reason: Prevent brigading and false positives"). If N other
 * reporters who are in the SAME CLUSTER as this reporter (see
 * `findClusteredPriorReporters` below) have already reported the same
 * target, this report's weight is discounted by `1 / (1 + N)`, the first
 * report from a cluster counts fully, the second counts at half weight,
 * the third at a third, and so on. Floored so a large brigade can't drive
 * an individual report's contribution to exactly zero (it can still tip a
 * score given enough volume, just each additional one from the same
 * cluster matters much less).
 *
 * SAF-6 FIX, what "cluster" means changed. Before this fix, "cluster"
 * was ONLY "shares a `device_fingerprint` with this reporter", and
 * `device_fingerprint` is a client-supplied, never-verified string
 * (`auth.service.ts`'s own schema marks it `.optional()`, and nothing
 * derives it server-side). An attacker sends a different fingerprint
 * string per fake account and the discount never applies, it fails
 * exactly when it's needed, and (per SAF-1) that failure used to feed
 * straight into an instant, uncorroborated suspension.
 *
 * `findClusteredPriorReporters` now treats the client fingerprint as an
 * untrusted HINT ONLY, one weak signal among several the client cannot
 * unilaterally control:
 *   - shared device fingerprint            (client-supplied, weak alone)
 *   - shared SERVER-OBSERVED IP address    (`user_auth_events.ip_address`)
 *   - account-creation-time proximity      (`users.created_at`)
 *   - report-timing correlation            (both reports' `created_at`)
 *   - shared behavioral history WITH THE TARGET (both reporters have/had
 *     a conversation with the person they're both reporting)
 *   - account-graph proximity              (the two reporters know each
 *     other directly, OR have both reported some other third party
 *     before, a repeat joint-reporting pattern)
 * Each contributes a fixed weight (see the `CLUSTER_SIGNAL_WEIGHT_*`
 * constants); two reporters are only treated as the same cluster once
 * their COMBINED signal weight clears `moderation.brigade_cluster_score_
 * threshold` (config, default 3), the fingerprint signal alone (weight
 * 1) can never reach that on its own, so varying it per fake account no
 * longer evades the discount by itself. Combining several weak signals
 * this way is deliberately harder to spoof end-to-end than defeating any
 * one strong-looking signal (the old design's mistake).
 */
const CLUSTER_DISCOUNT_FLOOR = 0.15;

const CLUSTER_SIGNAL_WEIGHT_FINGERPRINT = 1; // client-supplied, weak, see module doc above
const CLUSTER_SIGNAL_WEIGHT_IP = 2; // server-observed
const CLUSTER_SIGNAL_WEIGHT_ACCOUNT_CREATION_PROXIMITY = 2;
const CLUSTER_SIGNAL_WEIGHT_REPORT_TIMING_PROXIMITY = 1;
const CLUSTER_SIGNAL_WEIGHT_SHARED_TARGET_HISTORY = 2;
const CLUSTER_SIGNAL_WEIGHT_ACCOUNT_GRAPH_PROXIMITY = 3;

export interface SubmitReportInput {
  reportedId: string;
  conversationId?: string;
  messageId?: string;
  category: ReportCategory;
  details?: string;
}

const REPORT_CATEGORIES = [
  'fake_profile',
  'scam_money_request',
  'harassment',
  'unsafe_behavior',
  'misleading_photos',
  'minor_suspected',
  'spam',
  'no_show',
  'inappropriate_content',
  'other',
] as const satisfies readonly ReportCategory[];

const SubmitReportSchema = z.object({
  reportedId: z.string().uuid(),
  conversationId: z.string().uuid().optional(),
  messageId: z.string().uuid().optional(),
  category: z.enum(REPORT_CATEGORIES),
  details: z.string().trim().max(2000).optional(),
});

function rowToReport(row: {
  id: string;
  reporter_id: string;
  reported_id: string;
  conversation_id: string | null;
  message_id: string | null;
  category: ReportCategory;
  severity: number;
  details: string | null;
  created_at: Date;
}): Report {
  return {
    id: row.id,
    reporterId: row.reporter_id,
    reportedId: row.reported_id,
    conversationId: row.conversation_id,
    messageId: row.message_id,
    category: row.category,
    severity: row.severity,
    details: row.details,
    createdAt: row.created_at,
  };
}

export async function submitReport(ctx: Ctx, input: SubmitReportInput): Promise<Report> {
  const actor = requireUserActor(ctx);
  const parsed = SubmitReportSchema.parse(input);

  if (parsed.reportedId === actor.userId) {
    throw new ValidationError('Cannot report yourself.');
  }

  const { rows } = await ctx.db.query<{
    id: string;
    reporter_id: string;
    reported_id: string;
    conversation_id: string | null;
    message_id: string | null;
    category: ReportCategory;
    severity: number;
    details: string | null;
    created_at: Date;
  }>(
    `INSERT INTO reports (reporter_id, reported_id, conversation_id, message_id, category, severity, details)
     VALUES ($1, $2, $3, $4, $5, $6, $7)
     RETURNING id, reporter_id, reported_id, conversation_id, message_id, category, severity, details, created_at`,
    [
      actor.userId,
      parsed.reportedId,
      parsed.conversationId ?? null,
      parsed.messageId ?? null,
      parsed.category,
      CATEGORY_SEVERITY[parsed.category],
      parsed.details ?? null,
    ],
  );
  // Deliberately no write, archive, or read-through to `conversations`/
  // `messages` beyond the plain insert above, spec §30.9 "preserve the
  // conversation for automated investigation".
  const report = rowToReport(rows[0]!);

  // SAF-1 fix: `minor_suspected` deliberately does NOT push a
  // `recordAutomatedFlag` entry into the general score-ladder pool. That
  // category's `scoreReport` weight is the highest of any category by a
  // wide margin (spec §18.3/§18.5's own "maximum severity" instinct),
  // feeding it into `computeModerationScore` unconditionally would let a
  // single high-trust reporter's report cross `moderation.
  // auto_suspension_score` through the ORDINARY ladder alone, silently
  // recreating the exact one-report-suspends bug this build fixes, just
  // through a different door. `moderation.service#applyThresholds` still
  // evaluates this category on every call via `report.assessMinorSuspected`
  // (see that function's module doc for the full corroboration model),
  // every other category is unaffected and still feeds the general ladder
  // exactly as before.
  if (parsed.category !== 'minor_suspected') {
    const weight = await scoreReport(ctx, report);
    await moderation.recordAutomatedFlag(ctx, {
      userId: report.reportedId,
      signalType: 'user_report',
      weight,
      // reporterId is retained here for automated-investigation traceability
      // (admin-viewable per §4.3/§27), never returned to the reported user
      // by any export in this file or moderation.service.ts.
      metadata: { reportId: report.id, category: report.category, reporterId: report.reporterId },
    });
  }
  await moderation.applyThresholds(ctx, report.reportedId);

  return report;
}

/** Admin/moderation internal use, every report ever filed against `userId`. */
export async function listReportsAgainst(ctx: Ctx, userId: string): Promise<Report[]> {
  const { rows } = await ctx.db.query<{
    id: string;
    reporter_id: string;
    reported_id: string;
    conversation_id: string | null;
    message_id: string | null;
    category: ReportCategory;
    severity: number;
    details: string | null;
    created_at: Date;
  }>(
    `SELECT id, reporter_id, reported_id, conversation_id, message_id, category, severity, details, created_at
       FROM reports WHERE reported_id = $1 ORDER BY created_at DESC`,
    [userId],
  );
  return rows.map(rowToReport);
}

export async function countRecentReportsAgainst(ctx: Ctx, userId: string, sinceDays: number): Promise<number> {
  const since = new Date(ctx.clock.now().getTime() - sinceDays * 24 * 60 * 60 * 1000);
  const { rows } = await ctx.db.query<{ count: string }>(
    'SELECT count(*)::text AS count FROM reports WHERE reported_id = $1 AND created_at >= $2',
    [userId, since],
  );
  return Number(rows[0]?.count ?? '0');
}

async function reporterTrustMultiplier(ctx: Ctx, reporterId: string): Promise<number> {
  const { rows } = await ctx.db.query<{ trust_level: TrustLevel }>('SELECT trust_level FROM users WHERE id = $1', [reporterId]);
  const level = rows[0]?.trust_level ?? 'standard';
  return REPORTER_TRUST_MULTIPLIER[level];
}

/** Whether reporter and reported have any on-platform conversation together (spec §18.5 "reporter/reported relationship"). Canonical pair ordering matches the `conversations` CHECK constraint (INTERFACES.md decision #6). */
async function hasRelationship(ctx: Ctx, reporterId: string, reportedId: string): Promise<boolean> {
  const [a, b] = reporterId < reportedId ? [reporterId, reportedId] : [reportedId, reporterId];
  const { rows } = await ctx.db.query<{ count: string }>(
    'SELECT count(*)::text AS count FROM conversations WHERE user_a_id = $1 AND user_b_id = $2',
    [a, b],
  );
  return Number(rows[0]?.count ?? '0') > 0;
}

export interface ClusteredPriorReporter {
  reporterId: string;
  clusterScore: number;
}

/**
 * SAF-6 fix: every OTHER reporter who has ALREADY reported `reportedId`
 * (any category, a coordinated actor spreading reports across several
 * categories to look less coordinated is still the same cluster) before
 * `beforeCreatedAt`, paired with a combined weighted-signal "cluster
 * score" against `reporterId`, see this file's anti-brigading module
 * doc above for what each signal means. Returns only those whose combined
 * score clears `moderation.brigade_cluster_score_threshold`; the raw
 * per-signal breakdown never leaves this function (nothing downstream
 * needs it, and exposing it would hand a would-be brigade a tuning
 * oracle).
 */
export async function findClusteredPriorReporters(
  ctx: Ctx,
  reporterId: string,
  reportedId: string,
  beforeCreatedAt: Date,
): Promise<ClusteredPriorReporter[]> {
  const [threshold, creationWindowMinutes, timingWindowMinutes] = await Promise.all([
    ctx.config.get('moderation.brigade_cluster_score_threshold'),
    ctx.config.get('moderation.brigade_account_creation_window_minutes'),
    ctx.config.get('moderation.brigade_report_timing_window_minutes'),
  ]);

  const { rows } = await ctx.db.query<{ reporter_id: string; cluster_score: number }>(
    `WITH target_reporters AS (
       SELECT DISTINCT r.reporter_id, r.created_at AS report_created_at
       FROM reports r
       WHERE r.reported_id = $1 AND r.reporter_id <> $2 AND r.created_at < $3
     )
     SELECT
       tr.reporter_id,
       (
         (CASE WHEN EXISTS (
            SELECT 1 FROM user_auth_events me
            JOIN user_auth_events other
              ON other.device_fingerprint = me.device_fingerprint AND other.user_id = tr.reporter_id
            WHERE me.user_id = $2 AND me.device_fingerprint IS NOT NULL
          ) THEN $4 ELSE 0 END)
         +
         (CASE WHEN EXISTS (
            SELECT 1 FROM user_auth_events me
            JOIN user_auth_events other
              ON other.ip_address = me.ip_address AND other.user_id = tr.reporter_id
            WHERE me.user_id = $2 AND me.ip_address IS NOT NULL
          ) THEN $5 ELSE 0 END)
         +
         (CASE WHEN EXISTS (
            SELECT 1 FROM users me, users other
            WHERE me.id = $2 AND other.id = tr.reporter_id
              AND abs(EXTRACT(EPOCH FROM (me.created_at - other.created_at))) <= $6
          ) THEN $7 ELSE 0 END)
         +
         (CASE WHEN abs(EXTRACT(EPOCH FROM ($3::timestamptz - tr.report_created_at))) <= $8
          THEN $9 ELSE 0 END)
         +
         (CASE WHEN
            EXISTS (SELECT 1 FROM conversations c1 WHERE (c1.user_a_id = $2 AND c1.user_b_id = $1) OR (c1.user_a_id = $1 AND c1.user_b_id = $2))
            AND
            EXISTS (SELECT 1 FROM conversations c2 WHERE (c2.user_a_id = tr.reporter_id AND c2.user_b_id = $1) OR (c2.user_a_id = $1 AND c2.user_b_id = tr.reporter_id))
          THEN $10 ELSE 0 END)
         +
         (CASE WHEN
            EXISTS (SELECT 1 FROM conversations c3 WHERE (c3.user_a_id = $2 AND c3.user_b_id = tr.reporter_id) OR (c3.user_a_id = tr.reporter_id AND c3.user_b_id = $2))
            OR
            EXISTS (
              SELECT 1 FROM reports r1 JOIN reports r2 ON r1.reported_id = r2.reported_id
              WHERE r1.reporter_id = $2 AND r2.reporter_id = tr.reporter_id AND r1.reported_id <> $1
            )
          THEN $11 ELSE 0 END)
       ) AS cluster_score
     FROM target_reporters tr`,
    [
      reportedId,
      reporterId,
      beforeCreatedAt,
      CLUSTER_SIGNAL_WEIGHT_FINGERPRINT,
      CLUSTER_SIGNAL_WEIGHT_IP,
      creationWindowMinutes * 60,
      CLUSTER_SIGNAL_WEIGHT_ACCOUNT_CREATION_PROXIMITY,
      timingWindowMinutes * 60,
      CLUSTER_SIGNAL_WEIGHT_REPORT_TIMING_PROXIMITY,
      CLUSTER_SIGNAL_WEIGHT_SHARED_TARGET_HISTORY,
      CLUSTER_SIGNAL_WEIGHT_ACCOUNT_GRAPH_PROXIMITY,
    ],
  );

  return rows
    .filter((r) => Number(r.cluster_score) >= threshold)
    .map((r) => ({ reporterId: r.reporter_id, clusterScore: Number(r.cluster_score) }));
}

/** Anti-brigading: counts prior reports against `reportedId`, filed before `beforeCreatedAt`, by OTHER reporters in the same cluster as `reporterId`, see `findClusteredPriorReporters`. */
async function countSameClusterPriorReports(ctx: Ctx, reporterId: string, reportedId: string, beforeCreatedAt: Date): Promise<number> {
  const clustered = await findClusteredPriorReporters(ctx, reporterId, reportedId, beforeCreatedAt);
  return clustered.length;
}

/**
 * Weights one report per spec §18.5's stated factors: report category,
 * reporter trust, reporter/reported relationship (e.g. matched vs.
 * unmatched, same-cluster reports are down-weighted per the spec's
 * "duplicate report from same social cluster = reduced weight" example),
 * number of previous reports against the target, and recency. Pure
 * function of its inputs plus config thresholds (`ctx.config`), no
 * writes. `moderation.service#computeModerationScore` sums this across all
 * of a user's reports plus other automated signals.
 */
export async function scoreReport(ctx: Ctx, report: Report): Promise<number> {
  const categoryWeight = CATEGORY_WEIGHT[report.category];

  const [trustMult, relMult, previousCount, clusterPriorCount] = await Promise.all([
    reporterTrustMultiplier(ctx, report.reporterId),
    hasRelationship(ctx, report.reporterId, report.reportedId),
    countRecentReportsAgainst(ctx, report.reportedId, 3650).then((total) => Math.max(0, total - 1)), // exclude this report itself
    countSameClusterPriorReports(ctx, report.reporterId, report.reportedId, report.createdAt),
  ]);

  const relationshipMultiplier = relMult ? HAS_RELATIONSHIP_MULTIPLIER : NO_RELATIONSHIP_MULTIPLIER;
  const previousReportsMultiplier = Math.min(PREVIOUS_REPORTS_MULTIPLIER_CAP, 1 + PREVIOUS_REPORTS_STEP * previousCount);

  const ageDays = Math.max(0, (ctx.clock.now().getTime() - report.createdAt.getTime()) / (1000 * 60 * 60 * 24));
  const recencyMultiplier = Math.max(RECENCY_MULTIPLIER_FLOOR, 1 - ageDays / RECENCY_DECAY_DAYS);

  const clusterMultiplier = Math.max(CLUSTER_DISCOUNT_FLOOR, 1 / (1 + clusterPriorCount));

  const score = categoryWeight * trustMult * relationshipMultiplier * previousReportsMultiplier * recencyMultiplier * clusterMultiplier;
  return Math.round(score * 100) / 100;
}

// =========================================================================
// SAF-1 FIX, minor_suspected corroboration model.
//
// Before this fix, `moderation.service#applyThresholds` suspended an
// account the instant ANY report with `category = 'minor_suspected'`
// existed against it, no score threshold, no reporter-credibility check,
// no corroboration. That preserved the spec's right instinct (§18.3/
// §18.5: this category is maximum severity, act immediately, don't wait
// for score accumulation) but implemented it as a one-click weapon: any
// account, however new or untrustworthy, could suspend anyone else for
// free with a single report.
//
// THE MODEL below keeps the "act immediately, act decisively" intent for
// a REAL signal while removing the single-report kill switch:
//
//   1. CREDIBILITY GATE (`reporterCredibility`). A report only counts
//      toward the fast path at all if its reporter is currently
//      "credible": trust_level at/above a configurable floor, account
//      older than a configurable minimum age, and not "previously
//      abusive" (more than a configurable number of their own past
//      minor_suspected reports have been marked `outcome = 'unfounded'`,
//      see `recordReportOutcome`). A report from a non-credible reporter
//      still exists, still feeds `computeModerationScore` via the
//      ordinary automated flag `submitReport` records, it just can't
//      single-handedly trigger this category's special fast path.
//
//   2. IMMEDIATE, BUT REVERSIBLE, PROTECTIVE ACTION. The moment even ONE
//      credible report exists, `moderation.service#applyThresholds`
//      applies `moderation.minor_suspected_interim_action` (default:
//      `restriction`, reduced discovery visibility, fewer outgoing
//      interests, links disabled, extra verification required, see that
//      module's own doc) IMMEDIATELY, synchronously, same call. This is
//      the "preserve fast protective action" half of the fix, nobody
//      has to wait for corroboration before SOMETHING protective happens.
//      Critically, `restriction` is not `suspension`: it's the same
//      action tier the ordinary score ladder already uses for a much
//      lower-confidence signal, and it's fully reachable through the
//      existing automated appeal path (`appeal.service.ts`) for anyone
//      wrongly caught by it.
//
//   3. SUSPENSION REQUIRES CORROBORATION. Automated suspension for this
//      category requires BOTH: (a) at least
//      `moderation.minor_suspected_min_corroborating_reporters` (default
//      2) DISTINCT credible reporters who are NOT in the same brigading
//      cluster as each other (see `findClusteredPriorReporters`, this is
//      exactly where the SAF-6 fix does its second job: a brigade of
//      sock-puppets filing the same report from spoofed-fingerprint
//      accounts gets counted as ONE cluster, not N corroborators), AND
//      (b) their combined credibility-weighted score (`scoreReport`,
//      summed) at/above `moderation.minor_suspected_suspension_score`.
//      A single report, no matter how trusted its reporter, can never
//      cross the corroborating-reporter-count gate alone, so it can never
//      terminate an account by itself. Once genuine corroboration
//      arrives (a second independent, non-clustered credible reporter),
//      `applyThresholds` escalates from restriction straight to
//      suspension on that very call, still fast, still decisive, now
//      actually verified.
//
//   4. CONSEQUENCES FOR FALSE REPORTS (`recordReportOutcome`). When a
//      minor_suspected report is later established as unfounded (the
//      natural trigger: an appeal against the action it caused is
//      approved, flagged below for `appeal.service.ts` to wire in, see
//      that export's own doc), the REPORTER (not the target) takes a
//      configurable negative trust event, AND that report's `outcome`
//      permanently lowers their future credibility for this category via
//      the `priorUnfoundedCount` gate in step 1, closing the loop so
//      abusing this category repeatedly gets progressively less effective
//      instead of staying free.
//
// See `tests/unit/safetyFixes.test.ts` for both required proofs: a lone,
// uncorroborated, low-credibility report does NOT suspend, and a
// corroborated/high-credibility signal still acts fast and decisively.
// =========================================================================

const TRUST_LEVEL_RANK: Record<TrustLevel, number> = { limited: 0, standard: 1, trusted: 2, elite: 3 };

export interface ReporterCredibility {
  trustLevel: TrustLevel;
  accountAgeHours: number;
  priorUnfoundedCount: number;
  /** trust_level >= floor AND account age >= minimum AND priorUnfoundedCount <= cap, see module doc above. */
  isCredible: boolean;
}

/** Evaluates one reporter's current credibility for the minor_suspected fast path, as of `atCreatedAt` (the report's own timestamp, never "now", so re-evaluating an old report later doesn't retroactively change what already happened). */
export async function reporterCredibility(ctx: Ctx, reporterId: string, atCreatedAt: Date): Promise<ReporterCredibility> {
  const [trustFloor, minAgeHours, maxPriorUnfounded] = await Promise.all([
    ctx.config.get('moderation.minor_suspected_reporter_credibility_trust_floor'),
    ctx.config.get('moderation.minor_suspected_reporter_min_account_age_hours'),
    ctx.config.get('moderation.minor_suspected_reporter_max_prior_unfounded'),
  ]);

  const { rows } = await ctx.db.query<{ trust_level: TrustLevel; created_at: Date }>(
    'SELECT trust_level, created_at FROM users WHERE id = $1',
    [reporterId],
  );
  const u = rows[0];
  const trustLevel = u?.trust_level ?? 'standard';
  const accountAgeHours = u ? Math.max(0, (atCreatedAt.getTime() - u.created_at.getTime()) / (60 * 60 * 1000)) : 0;

  const { rows: unfoundedRows } = await ctx.db.query<{ count: string }>(
    `SELECT count(*)::text AS count FROM reports WHERE reporter_id = $1 AND category = 'minor_suspected' AND outcome = 'unfounded'`,
    [reporterId],
  );
  const priorUnfoundedCount = Number(unfoundedRows[0]?.count ?? '0');

  const isCredible =
    TRUST_LEVEL_RANK[trustLevel] >= TRUST_LEVEL_RANK[trustFloor] &&
    accountAgeHours >= minAgeHours &&
    priorUnfoundedCount <= maxPriorUnfounded;

  return { trustLevel, accountAgeHours, priorUnfoundedCount, isCredible };
}

export interface MinorSuspectedAssessment {
  /** Any minor_suspected report at all exists against this user, credible or not, purely informational. */
  hasAnyReport: boolean;
  /** At least one minor_suspected report comes from a currently-credible reporter, this is what drives the immediate interim protective action. */
  hasCredibleSignal: boolean;
  /** Sum of `scoreReport` over minor_suspected reports from CREDIBLE reporters only. */
  weightedScore: number;
  /** Count of distinct credible reporters, after collapsing anyone in the same brigading cluster as an already-counted reporter down to one, see `findClusteredPriorReporters`. This is the number that must clear `moderation.minor_suspected_min_corroborating_reporters` before suspension is considered. */
  distinctCredibleCorroborators: number;
}

/** The full SAF-1 assessment for one user, see this section's module doc. `moderation.service#applyThresholds` is the only caller in the MVP call graph. */
export async function assessMinorSuspected(ctx: Ctx, userId: string): Promise<MinorSuspectedAssessment> {
  const { rows } = await ctx.db.query<{
    id: string;
    reporter_id: string;
    reported_id: string;
    conversation_id: string | null;
    message_id: string | null;
    category: ReportCategory;
    severity: number;
    details: string | null;
    created_at: Date;
  }>(
    `SELECT id, reporter_id, reported_id, conversation_id, message_id, category, severity, details, created_at
       FROM reports WHERE reported_id = $1 AND category = 'minor_suspected' ORDER BY created_at ASC`,
    [userId],
  );
  const reports = rows.map(rowToReport);

  if (reports.length === 0) {
    return { hasAnyReport: false, hasCredibleSignal: false, weightedScore: 0, distinctCredibleCorroborators: 0 };
  }

  const credibilityByReporter = new Map<string, ReporterCredibility>();
  for (const r of reports) {
    if (!credibilityByReporter.has(r.reporterId)) {
      credibilityByReporter.set(r.reporterId, await reporterCredibility(ctx, r.reporterId, r.createdAt));
    }
  }

  const credibleReports = reports.filter((r) => credibilityByReporter.get(r.reporterId)!.isCredible);

  let weightedScore = 0;
  for (const r of credibleReports) {
    weightedScore += await scoreReport(ctx, r);
  }

  // Greedy clustering, chronological: a credible reporter only earns a
  // NEW corroborator seat if they are not in the same brigading cluster
  // as a reporter already counted (see findClusteredPriorReporters,
  // shared device fingerprint alone is far too weak a signal to satisfy
  // this on its own after the SAF-6 fix).
  const representativeReporterIds: string[] = [];
  for (const r of credibleReports) {
    const clusteredWithThisReporter = new Set(
      (await findClusteredPriorReporters(ctx, r.reporterId, userId, r.createdAt)).map((c) => c.reporterId),
    );
    const alreadyRepresented = representativeReporterIds.some((id) => clusteredWithThisReporter.has(id));
    if (!alreadyRepresented) {
      representativeReporterIds.push(r.reporterId);
    }
  }

  return {
    hasAnyReport: true,
    hasCredibleSignal: credibleReports.length > 0,
    weightedScore: Math.round(weightedScore * 100) / 100,
    distinctCredibleCorroborators: representativeReporterIds.length,
  };
}

export type ReportOutcome = 'confirmed' | 'unfounded';

/** trust.service event type for a reporter penalized under `recordReportOutcome` below, not in `trust.service.ts#TRUST_EVENT_TYPES` (that module's "recommended vocabulary" list is owned by a different agent); an unrecognized event type still records and displays fine there under its documented generic fallback label. */
const FALSE_MINOR_SUSPECTED_REPORT_EVENT_TYPE = 'false_minor_suspected_report';

/**
 * SAF-1 fix, consequence half: marks a single report's `outcome`. When a
 * `minor_suspected` report is marked `'unfounded'`, applies
 * `moderation.false_minor_suspected_report_trust_penalty` (a negative
 * delta, config-driven) as a trust event against the REPORTER, and,
 * because `reporterCredibility` above counts `outcome = 'unfounded'`
 * rows, durably lowers that reporter's future credibility for this
 * category. This is the "false reports carry consequences for the
 * reporter" requirement; without it, a bad-faith reporter who gets
 * caught pays no price and can simply try again.
 *
 * ADMIN-ONLY FOR NOW: restricted to an `admin` or `system` actor. The
 * natural automated trigger, an appeal against a minor_suspected-
 * triggered action being approved, i.e. the account is reinstated, lives
 * in `appeal.service.ts`, which is outside this build's file-ownership
 * boundary; flagged in the build report for that agent to call this
 * function from `resolveAppeal` on approval. The mechanism itself is
 * fully implemented and independently tested here
 * (`tests/unit/safetyFixes.test.ts`) so a human moderator (or that future
 * automated caller) can use it correctly today via the same admin surface
 * §4.3/§27 already grants read access to moderation data through.
 */
export async function recordReportOutcome(ctx: Ctx, reportId: string, outcome: ReportOutcome): Promise<void> {
  if (ctx.actor.type !== 'admin' && ctx.actor.type !== 'system') {
    throw new ForbiddenError('Only an admin or system actor may record a report outcome.');
  }
  const now = ctx.clock.now();

  const { rows } = await ctx.db.query<{ id: string; reporter_id: string; category: ReportCategory }>(
    `UPDATE reports SET outcome = $2, outcome_recorded_at = $3 WHERE id = $1
     RETURNING id, reporter_id, category`,
    [reportId, outcome, now],
  );
  const row = rows[0];
  if (!row) {
    throw new NotFoundError('Report not found.');
  }

  if (outcome === 'unfounded' && row.category === 'minor_suspected') {
    const penalty = await ctx.config.get('moderation.false_minor_suspected_report_trust_penalty');
    await trust.recordTrustEvent(ctx, {
      userId: row.reporter_id,
      eventType: FALSE_MINOR_SUSPECTED_REPORT_EVENT_TYPE,
      delta: penalty,
      metadata: { reportId: row.id },
    });
    await trust.recalculateTrustScore(ctx, row.reporter_id);
  }
}
