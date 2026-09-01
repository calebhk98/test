/**
 * §25.9 Payment Reconciliation job. "Compare processor webhooks with local
 * ledger. Flag mismatches.", exactly `ledger.service#reconcileWithProcessor`,
 * which NEVER auto-corrects financial state (see that function's own doc,
 * the immutable-ledger invariant), only reports mismatches. This wrapper's
 * only added behavior is logging each flagged mismatch at `warn` level so
 * it's visible in process logs/observability even before an admin views
 * `GET /admin/users/:userId/ledger`.
 */
import type { Ctx } from '../lib/ctx.js';
import { reconcileWithProcessor } from '../services/ledger.service.js';
import type { LedgerMismatch } from '../services/ledger.service.js';
import type { JobDefinition } from './types.js';

export async function runPaymentReconciliationJob(ctx: Ctx): Promise<{ checked: number; mismatches: LedgerMismatch[] }> {
  const result = await reconcileWithProcessor(ctx);
  for (const mismatch of result.mismatches) {
    ctx.logger.warn('payment_reconciliation.mismatch', { ...mismatch });
  }
  return result;
}

export const paymentReconciliationJob: JobDefinition = {
  name: 'payment_reconciliation',
  description: 'Compare local payment_holds/payment_ledger state against the processor and flag (never auto-correct) mismatches (§25.9).',
  intervalMs: 30 * 60 * 1000,
  run: runPaymentReconciliationJob,
};
