/**
 * §25.2 Date Proposal Expiry job. "Find pending date proposals past
 * acceptance expiry. Set to expired. Release proposer hold." — exactly
 * `dateProposal.service#expireDuePendingProposals`, which per-row checks
 * `policySnapshot['date.accept_expiry_hours']` (never live config, per the
 * §21.3 snapshot invariant) and calls `payment.releaseHold` only for a
 * still-`authorized` proposer hold, so a repeated run is a no-op for any
 * row it already processed.
 */
import type { Ctx } from '../lib/ctx.js';
import { expireDuePendingProposals } from '../services/dateProposal.service.js';
import type { JobDefinition } from './types.js';

export async function runDateProposalExpiryJob(ctx: Ctx): Promise<{ expired: number }> {
  return expireDuePendingProposals(ctx);
}

export const dateProposalExpiryJob: JobDefinition = {
  name: 'date_proposal_expiry',
  description: 'Expire pending_acceptance date proposals past date.accept_expiry_hours and release the proposer hold (§25.2).',
  intervalMs: 5 * 60 * 1000,
  run: runDateProposalExpiryJob,
};
