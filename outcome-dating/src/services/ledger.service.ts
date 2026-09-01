import type { Ctx } from '../lib/ctx.js';
import { NotImplementedError } from '../lib/errors.js';
import type { LedgerEntry, LedgerEntryType, Page } from '../domain/types.js';

/**
 * ledger.service — the immutable payment ledger.
 * Spec: §14.8, §27 (admin payment ledger viewer), §25.9 (reconciliation).
 *
 * Owning agent: D.
 *
 * HARD INVARIANT: `payment_ledger` rows are INSERT-only. This module
 * exposes no update/delete function on purpose — correcting a mistaken
 * entry means inserting a new offsetting entry (e.g. a `refund` row),
 * never mutating history. `payment.service.ts` is the only caller that
 * should invoke `recordEntry`, always from inside the same transaction as
 * the `payment_holds` status change it documents (see
 * `payment.service.ts` invariants) — a ledger entry must never exist for
 * a state the corresponding hold didn't actually reach.
 */

export interface RecordEntryInput {
  userId: string;
  dateProposalId: string;
  paymentHoldId: string | null;
  type: LedgerEntryType;
  amountCents: number;
  currency: string;
  processorReference: string | null;
  metadata?: Record<string, unknown>;
}

export async function recordEntry(ctx: Ctx, input: RecordEntryInput): Promise<LedgerEntry> {
  throw new NotImplementedError('ledger.recordEntry');
}

export async function listEntriesForDateProposal(ctx: Ctx, dateProposalId: string): Promise<LedgerEntry[]> {
  throw new NotImplementedError('ledger.listEntriesForDateProposal');
}

/** Admin payment ledger viewer (spec §27 item 8). */
export async function listEntriesForUser(ctx: Ctx, userId: string, params?: { cursor?: string; limit?: number }): Promise<Page<LedgerEntry>> {
  throw new NotImplementedError('ledger.listEntriesForUser');
}

export interface LedgerMismatch {
  dateProposalId: string;
  paymentHoldId: string | null;
  reason: string;
  ledgerAmountCents: number | null;
  processorAmountCents: number | null;
}

/** §25.9 job: compare processor-reported state (via `ctx.payments`, where the adapter supports a lookup) against local ledger/holds and flag mismatches for admin review — never auto-corrects financial state. */
export async function reconcileWithProcessor(ctx: Ctx, params?: { since?: Date }): Promise<{ checked: number; mismatches: LedgerMismatch[] }> {
  throw new NotImplementedError('ledger.reconcileWithProcessor');
}
