/**
 * src/jobs/registry.ts — the full §25 job inventory, keyed by name for
 * `jobs:run <name>` (CLI) and `JobScheduler#start` (all of them, on their
 * own interval).
 */
import type { JobDefinition } from './types.js';
import { interestExpiryJob } from './interestExpiry.job.js';
import { dateProposalExpiryJob } from './dateProposalExpiry.job.js';
import { chatDecayJob } from './chatDecay.job.js';
import { compatibilityRefreshJob } from './compatibilityRefresh.job.js';
import { photoAbStatsJob } from './photoAbStats.job.js';
import { trustRecalculationJob } from './trustRecalculation.job.js';
import { moderationRecalculationJob } from './moderationRecalculation.job.js';
import { voucherExpiryJob } from './voucherExpiry.job.js';
import { paymentReconciliationJob } from './paymentReconciliation.job.js';

export const ALL_JOBS: JobDefinition[] = [
  interestExpiryJob,
  dateProposalExpiryJob,
  chatDecayJob,
  compatibilityRefreshJob,
  photoAbStatsJob,
  trustRecalculationJob,
  moderationRecalculationJob,
  voucherExpiryJob,
  paymentReconciliationJob,
];

export function findJob(name: string): JobDefinition | undefined {
  return ALL_JOBS.find((j) => j.name === name);
}

export {
  interestExpiryJob,
  dateProposalExpiryJob,
  chatDecayJob,
  compatibilityRefreshJob,
  photoAbStatsJob,
  trustRecalculationJob,
  moderationRecalculationJob,
  voucherExpiryJob,
  paymentReconciliationJob,
};
