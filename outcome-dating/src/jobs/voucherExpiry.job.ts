/**
 * §25.8 Voucher Expiry job. "Expire vouchers after configurable period.",
 * exactly `voucher.service#expireDueVouchers`
 * (`UPDATE vouchers SET status='expired' WHERE status='issued' AND
 * expires_at < now`, itself already baking in
 * `voucher.expiry_hours_after_date_end` at issuance time per that module's
 * §21.3 snapshot-semantics note).
 */
import type { Ctx } from '../lib/ctx.js';
import { expireDueVouchers } from '../services/voucher.service.js';
import type { JobDefinition } from './types.js';

export async function runVoucherExpiryJob(ctx: Ctx): Promise<{ expired: number }> {
  return expireDueVouchers(ctx);
}

export const voucherExpiryJob: JobDefinition = {
  name: 'voucher_expiry',
  description: 'Expire issued vouchers past their expires_at (§25.8, §15 state machine L2).',
  intervalMs: 15 * 60 * 1000,
  run: runVoucherExpiryJob,
};
