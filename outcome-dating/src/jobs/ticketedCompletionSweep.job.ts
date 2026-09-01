/**
 * §15.4 Ticketed Completion Window Sweep job. Thin wrapper around
 * `dateProposal.service#sweepTicketedCompletionWindows`, every `ticketed`
 * proposal whose no-scan confirmation window has closed is moved to
 * `no_show` (zero confirmations) or `disputed` (exactly one), automatically
 * and idempotently (see that function's own doc). No domain logic here.
 */
import type { Ctx } from '../lib/ctx.js';
import { sweepTicketedCompletionWindows } from '../services/dateProposal.service.js';
import type { SweepTicketedCompletionWindowsResult } from '../services/dateProposal.service.js';
import type { JobDefinition } from './types.js';

export async function runTicketedCompletionSweepJob(ctx: Ctx): Promise<SweepTicketedCompletionWindowsResult> {
  return sweepTicketedCompletionWindows(ctx);
}

export const ticketedCompletionSweepJob: JobDefinition = {
  name: 'ticketed_completion_sweep',
  description: 'Resolve ticketed date proposals whose no-scan confirmation window closed, to no_show or disputed (§15.4).',
  intervalMs: 15 * 60 * 1000,
  run: runTicketedCompletionSweepJob,
};
