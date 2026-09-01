/**
 * §25.1 Interest Expiry job. "Run every few minutes. Find pending interests
 * past expiry. Set to expired. Release outgoing slot."
 *
 * All three of those are already exactly what
 * `interest.service#expireDuePendingInterests` does in one idempotent
 * UPDATE (`WHERE status = 'pending' AND expires_at <= now`), this job is a
 * thin, named wrapper so the scheduler/CLI has a stable entry, per the task
 * brief's "never reimplements domain logic in the job."
 */
import type { Ctx } from '../lib/ctx.js';
import { expireDuePendingInterests } from '../services/interest.service.js';
import type { JobDefinition } from './types.js';

export async function runInterestExpiryJob(ctx: Ctx): Promise<{ expired: number }> {
  return expireDuePendingInterests(ctx);
}

export const interestExpiryJob: JobDefinition = {
  name: 'interest_expiry',
  description: 'Expire pending interests past interest.expiry_hours and free the sender outgoing slot (§25.1).',
  intervalMs: 5 * 60 * 1000, // every few minutes, per spec
  run: runInterestExpiryJob,
};
