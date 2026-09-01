import type { Ctx } from '../lib/ctx.js';
import { NotImplementedError } from '../lib/errors.js';
import type { Report, ReportCategory } from '../domain/types.js';

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
 *    callers (HTTP layer) must not either.
 *  - `submitReport` preserves the associated conversation for automated
 *    investigation (spec §30.9) — it must NOT archive or otherwise mutate
 *    the referenced `conversation_id`/`message_id`.
 *  - `submitReport` forwards to `moderation.service#recordAutomatedFlag`
 *    (or the caller does, immediately after) so scoring/thresholds react
 *    promptly — see `moderation.service.ts` for the aggregation step this
 *    module does NOT itself perform.
 */

export interface SubmitReportInput {
  reportedId: string;
  conversationId?: string;
  messageId?: string;
  category: ReportCategory;
  details?: string;
}

export async function submitReport(ctx: Ctx, input: SubmitReportInput): Promise<Report> {
  throw new NotImplementedError('report.submitReport');
}

/** Admin/moderation internal use — every report ever filed against `userId`. */
export async function listReportsAgainst(ctx: Ctx, userId: string): Promise<Report[]> {
  throw new NotImplementedError('report.listReportsAgainst');
}

export async function countRecentReportsAgainst(ctx: Ctx, userId: string, sinceDays: number): Promise<number> {
  throw new NotImplementedError('report.countRecentReportsAgainst');
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
  throw new NotImplementedError('report.scoreReport');
}
