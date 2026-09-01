import type { Ctx } from '../lib/ctx.js';
import { withActor } from '../lib/ctx.js';
import type { TrustLevel } from '../domain/types.js';
import * as dateProposalService from './dateProposal.service.js';
import * as reportService from './report.service.js';
import * as trustService from './trust.service.js';
import * as notificationService from './notification.service.js';

/**
 * disputeResolution.service — automated resolution of `disputed` date
 * proposals.
 * Spec: §15.4 ("automated handling... according to policy", never named
 * further) — see docs/conformance.md's Open Question OQ-3 for the decision
 * this implements: an unresolved dispute past
 * `date.dispute_auto_resolve_hours` is treated as an implicit no-show
 * report against the non-confirming party, routed through the EXISTING
 * report/moderation scoring machinery (never reimplemented here) and
 * feeding trust recalculation. No human step anywhere (spec §18.1).
 *
 * A SEPARATE module from `dateProposal.service.ts` on purpose:
 * `dateProposal.service.ts`'s documented "may call" list (INTERFACES.md)
 * is `venue, payment, voucher, conversation, notification, trust` — it
 * does not include `report`. Resolving a dispute needs exactly that edge
 * (`report.service#submitReport`, which itself drives
 * `moderation.service#applyThresholds` — see report.service.ts's own doc),
 * so rather than widen that frozen, well-documented file's call graph for
 * one decision-layer feature, this module owns the `-> report` edge
 * instead, composing `dateProposal.service.ts`'s exported read-only
 * lookup/marker functions (`listDisputesAwaitingAutoResolution`,
 * `markDisputeResolved`) with `report.service` and `trust.service` calls
 * of its own.
 *
 * `disputed` stays a terminal `DateProposalStatus` throughout (spec
 * §13.3) — resolution never changes `date_proposals.status`; it only
 * performs the report/trust side effects exactly once per proposal
 * (idempotency via `date_proposals.dispute_resolved_at`, see
 * `db/migrations/007_decisions.sql`) and records that it did.
 *
 * IMPERSONATION NOTE: `report.service#submitReport` requires a `user`
 * actor (it records `reporter_id` and validates `reportedId !==
 * actor.userId`). This module impersonates the CONFIRMING party as the
 * reporter — they are the one participant who could legitimately file
 * this report; the non-confirming party never showed up to say otherwise.
 * This is the one place in the codebase that impersonates a specific user
 * for a fully-automated action, and it is narrowly scoped to exactly this
 * call (`withActor`, not a persisted session/token).
 */

export interface ResolveDueDisputesResult {
  resolved: number;
}

const AUTOMATED_DISPUTE_REPORT_DETAILS =
  'Automated resolution: the post-date confirmation window closed with only one party confirming attendance.';

async function trustLevelOf(ctx: Ctx, userId: string): Promise<TrustLevel> {
  const { rows } = await ctx.db.query<{ trust_level: TrustLevel }>('SELECT trust_level FROM users WHERE id = $1', [userId]);
  return rows[0]?.trust_level ?? 'standard';
}

async function resolveOneDispute(
  ctx: Ctx,
  dispute: { dateProposalId: string; conversationId: string; confirmingUserId: string; nonConfirmingUserId: string },
): Promise<void> {
  const confirmingTrustLevel = await trustLevelOf(ctx, dispute.confirmingUserId);
  const reporterCtx = withActor(ctx, { type: 'user', userId: dispute.confirmingUserId, trustLevel: confirmingTrustLevel });

  // Routed through the real report/moderation pipeline — "do not
  // reimplement scoring" (task brief). `submitReport` itself pushes an
  // automated moderation flag and runs `moderation.applyThresholds`
  // (spec §18.3/§18.5), which recalculates trust only when a score
  // threshold is actually crossed.
  await reportService.submitReport(reporterCtx, {
    reportedId: dispute.nonConfirmingUserId,
    conversationId: dispute.conversationId,
    category: 'no_show',
    details: AUTOMATED_DISPUTE_REPORT_DETAILS,
  });

  // Independent of whether the report alone crossed a moderation
  // threshold: a disputed-and-resolved date should affect the
  // non-confirming party's trust the same way a plain, confirmed no-show
  // does (`dateProposal.service#markNoShow` uses the same -8 weight) —
  // this is the "feeding trust recalculation via the trust service" half
  // of the decision.
  await trustService.recordTrustEvent(ctx, {
    userId: dispute.nonConfirmingUserId,
    eventType: 'no_show',
    delta: -8,
    metadata: { dateProposalId: dispute.dateProposalId, autoResolved: true, source: 'dispute_auto_resolution' },
  });
  await trustService.recalculateTrustScore(ctx, dispute.nonConfirmingUserId);

  await dateProposalService.markDisputeResolved(ctx, dispute.dateProposalId);

  // Best-effort, like every other notification in this decision layer —
  // a notification hiccup must never leave a dispute stuck un-resolved on
  // retry (the report/trust/marker writes above have already committed).
  try {
    await notificationService.notify(ctx, {
      userId: dispute.confirmingUserId,
      eventType: 'date_disputed',
      channel: 'in_app',
      payload: { dateProposalId: dispute.dateProposalId, resolved: true },
    });
    await notificationService.notify(ctx, {
      userId: dispute.nonConfirmingUserId,
      eventType: 'date_disputed',
      channel: 'in_app',
      payload: { dateProposalId: dispute.dateProposalId, resolved: true },
    });
  } catch (err) {
    ctx.logger.warn('disputeResolution.notify_failed', {
      dateProposalId: dispute.dateProposalId,
      err: err instanceof Error ? err.message : String(err),
    });
  }
}

/**
 * The job body (§25-style automated job — not registered in `src/jobs/**`
 * here, that directory belongs to a different, concurrently-working
 * agent; see the final report for the exact function name to schedule).
 * Idempotent/safe to re-run with any clock: only disputes with
 * `dispute_resolved_at IS NULL` past their deadline are ever candidates
 * (`dateProposal.service#listDisputesAwaitingAutoResolution`), and
 * `markDisputeResolved` is unconditionally the last step of each
 * iteration.
 */
export async function resolveDueDisputes(ctx: Ctx): Promise<ResolveDueDisputesResult> {
  const due = await dateProposalService.listDisputesAwaitingAutoResolution(ctx);

  let resolved = 0;
  for (const dispute of due) {
    await resolveOneDispute(ctx, dispute);
    resolved++;
  }
  return { resolved };
}
