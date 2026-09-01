import { z } from 'zod';
import type { Ctx } from '../lib/ctx.js';
import { requireUserActor } from '../lib/ctx.js';
import { ValidationError } from '../lib/errors.js';
import type { Report, ReportCategory, TrustLevel } from '../domain/types.js';
import * as moderation from './moderation.service.js';

/**
 * report.service — structured user reports.
 * Spec: §18.3, §18.5 (scoring inputs), §24.12, §30.9.
 *
 * Owning agent: E.
 *
 * Invariants:
 *  - `category` is one of the exact §18.3 list (enforced by the DB CHECK
 *    and the `ReportCategory` union) — there is no free-text-only report
 *    path (spec §18.3 "Do not rely only on free-text reports"); `details`
 *    is optional supplementary text alongside the required category.
 *  - `submitReport` never reveals the reporter's identity to the reported
 *    user (spec §30.9) — this module has no function that would leak it;
 *    callers (HTTP layer) must not either. Note this is a "never to the
 *    REPORTED user" rule, not "never persisted" — `reporter_id` is a
 *    normal column on `reports`, readable by the admin actor that's
 *    allowed to view moderation data (§4.3, §27); no export in this file
 *    returns a reporter id keyed to anything the reported user could
 *    plausibly see.
 *  - `submitReport` preserves the associated conversation for automated
 *    investigation (spec §30.9) — it must NOT archive or otherwise mutate
 *    the referenced `conversation_id`/`message_id`. (Structurally
 *    enforced: this file never imports `conversation.service.ts` and
 *    never writes to the `conversations`/`messages` tables.)
 *  - `submitReport` forwards to `moderation.service#recordAutomatedFlag`
 *    immediately after insert, then calls `moderation.service#applyThresholds`
 *    so a `minor_suspected` report gets its "immediate protective action"
 *    (spec §18.3/§18.5) synchronously, in the same call, rather than
 *    waiting for the §25.7 recalculation job. See moderation.service.ts's
 *    module doc for the full "where does computeModerationScore's number
 *    come from" note — this is the one function that pushes into it.
 */

// =====================================================================
// §18.5 scoring model (internal weights — not part of any user-facing
// return type; `scoreReport`'s return is a plain number consumed only by
// `moderation.service.ts`).
// =====================================================================

/** Category base severity (spec §18.3 list; §18.5 "score depends on ... report category" — `minor_suspected` is deliberately far above everything else, spec "maximum severity"). */
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

/** `reports.severity` (1-5, DB CHECK) — a coarser, stored-on-the-row classification distinct from the scoring weight above (which is only ever computed on demand, never persisted). */
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

/** Spec §18.5 "scam report from trusted user = high weight" — reporter trust scales credibility. */
const REPORTER_TRUST_MULTIPLIER: Record<TrustLevel, number> = {
  limited: 0.5,
  standard: 1.0,
  trusted: 1.3,
  elite: 1.6,
};

/** Reduced weight for a report with no on-platform interaction between reporter and reported (no shared conversation) — a stranger report is harder to corroborate than one from an actual match. */
const NO_RELATIONSHIP_MULTIPLIER = 0.6;
const HAS_RELATIONSHIP_MULTIPLIER = 1.0;

/** Spec §18.5 "number of previous reports" — each additional prior report against the same target raises credibility that a pattern exists, capped so one target can't be driven to an extreme multiplier by volume alone. */
const PREVIOUS_REPORTS_STEP = 0.05;
const PREVIOUS_REPORTS_MULTIPLIER_CAP = 1.5;

/** Spec §18.5 "recency" — a report from a year ago says less about current risk than one from today. Linear decay, floored so old reports still count for something (an old scam report is never worthless). */
const RECENCY_DECAY_DAYS = 365;
const RECENCY_MULTIPLIER_FLOOR = 0.3;

/**
 * ANTI-BRIGADING DISCOUNT (spec §18.5 "duplicate report from same social
 * cluster = reduced weight" — the explicit stated reason for this design,
 * spec §18.5 "Reason: Prevent brigading and false positives"). "Cluster"
 * is approximated via shared device fingerprint: if N other reporters who
 * share a device fingerprint with THIS reporter have already reported the
 * same target, this report's weight is discounted by `1 / (1 + N)` — the
 * first report from a cluster counts fully, the second counts at half
 * weight, the third at a third, and so on. Floored so a large brigade
 * can't drive an individual report's contribution to exactly zero (it can
 * still tip a score given enough volume, just each additional one from
 * the same cluster matters much less).
 */
const CLUSTER_DISCOUNT_FLOOR = 0.15;

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
  // `messages` beyond the plain insert above — spec §30.9 "preserve the
  // conversation for automated investigation".
  const report = rowToReport(rows[0]!);

  const weight = await scoreReport(ctx, report);
  await moderation.recordAutomatedFlag(ctx, {
    userId: report.reportedId,
    signalType: 'user_report',
    weight,
    // reporterId is retained here for automated-investigation traceability
    // (admin-viewable per §4.3/§27) — never returned to the reported user
    // by any export in this file or moderation.service.ts.
    metadata: { reportId: report.id, category: report.category, reporterId: report.reporterId },
  });
  await moderation.applyThresholds(ctx, report.reportedId);

  return report;
}

/** Admin/moderation internal use — every report ever filed against `userId`. */
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

/** Anti-brigading: counts prior reports against `reportedId`, filed before `beforeCreatedAt`, by OTHER reporters who share a device fingerprint with `reporterId` (via `user_auth_events`, spec §19.2/§23.2). */
async function countSameClusterPriorReports(ctx: Ctx, reporterId: string, reportedId: string, beforeCreatedAt: Date): Promise<number> {
  const { rows } = await ctx.db.query<{ count: string }>(
    `SELECT count(DISTINCT r.reporter_id)::text AS count
       FROM reports r
       JOIN user_auth_events uae ON uae.user_id = r.reporter_id AND uae.device_fingerprint IS NOT NULL
      WHERE r.reported_id = $1
        AND r.reporter_id <> $2
        AND r.created_at < $3
        AND uae.device_fingerprint IN (
          SELECT device_fingerprint FROM user_auth_events
           WHERE user_id = $2 AND device_fingerprint IS NOT NULL
        )`,
    [reportedId, reporterId, beforeCreatedAt],
  );
  return Number(rows[0]?.count ?? '0');
}

/**
 * Weights one report per spec §18.5's stated factors: report category,
 * reporter trust, reporter/reported relationship (e.g. matched vs.
 * unmatched — same-cluster reports are down-weighted per the spec's
 * "duplicate report from same social cluster = reduced weight" example),
 * number of previous reports against the target, and recency. Pure
 * function of its inputs plus config thresholds (`ctx.config`) — no
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
