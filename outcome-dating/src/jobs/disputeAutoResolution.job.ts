/**
 * §15.4 Dispute Auto-Resolution job. Thin wrapper around
 * `disputeResolution.service#resolveDueDisputes` — every `disputed` date
 * proposal past `date.dispute_auto_resolve_hours` gets resolved exactly
 * once (idempotent via `date_proposals.dispute_resolved_at`, see that
 * module's own doc). No domain logic lives here.
 */
import type { Ctx } from '../lib/ctx.js';
import { resolveDueDisputes } from '../services/disputeResolution.service.js';
import type { ResolveDueDisputesResult } from '../services/disputeResolution.service.js';
import type { JobDefinition } from './types.js';

export async function runDisputeAutoResolutionJob(ctx: Ctx): Promise<ResolveDueDisputesResult> {
  return resolveDueDisputes(ctx);
}

export const disputeAutoResolutionJob: JobDefinition = {
  name: 'dispute_auto_resolution',
  description: 'Automatically resolve disputed date proposals past date.dispute_auto_resolve_hours (§15.4).',
  intervalMs: 15 * 60 * 1000,
  run: runDisputeAutoResolutionJob,
};
