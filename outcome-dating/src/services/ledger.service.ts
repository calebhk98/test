import { z } from 'zod';
import type { Ctx } from '../lib/ctx.js';
import { ValidationError } from '../lib/errors.js';
import type { LedgerEntry, LedgerEntryType, Page } from '../domain/types.js';

/**
 * ledger.service, the immutable payment ledger.
 * Spec: §14.8, §27 (admin payment ledger viewer), §25.9 (reconciliation).
 *
 * Owning agent: D.
 *
 * HARD INVARIANT: `payment_ledger` rows are INSERT-only. This module
 * exposes no update/delete function on purpose, correcting a mistaken
 * entry means inserting a new offsetting entry (e.g. a `refund` row),
 * never mutating history. `payment.service.ts` is the only caller that
 * should invoke `recordEntry`, always from inside the same transaction as
 * the `payment_holds` status change it documents (see
 * `payment.service.ts` invariants), a ledger entry must never exist for
 * a state the corresponding hold didn't actually reach.
 *
 * `recordEntry` deliberately does NOT open its own DB transaction, it
 * issues a single INSERT against `ctx.db`, whatever that is bound to. This
 * is what lets `payment.service.ts` pair a `payment_holds` UPDATE and a
 * `payment_ledger` INSERT atomically inside its own `withTransaction`
 * block without `ledger.service.ts` fighting over the connection.
 */

const LEDGER_TYPES: readonly LedgerEntryType[] = [
  'authorization',
  'capture',
  'release',
  'refund',
  'dispute',
  'chargeback',
  'venue_payout', // decision-layer addition, see docs/conformance.md OQ-8
];

const RecordEntrySchema = z
  .object({
    // Nullable/optional: a `type: 'venue_payout'` entry pays a venue, not a
    // user (decision-layer addition, see db/migrations/007_decisions.sql's
    // `payment_ledger_payee_check`; every pre-existing entry type still
    // requires a real `userId`, enforced below rather than at the schema
    // shape level so the error message is clearer than a generic union
    // mismatch).
    userId: z.string().uuid().nullable(),
    venueId: z.string().uuid().nullable().optional(),
    dateProposalId: z.string().uuid(),
    paymentHoldId: z.string().uuid().nullable(),
    type: z.enum(LEDGER_TYPES as [LedgerEntryType, ...LedgerEntryType[]]),
    amountCents: z.number().int(),
    currency: z.string().min(1).max(8),
    processorReference: z.string().nullable(),
    metadata: z.record(z.unknown()).optional(),
  })
  .refine((v) => (v.type === 'venue_payout' ? v.venueId != null && v.userId == null : v.userId != null), {
    message: "type 'venue_payout' requires venueId (and null userId); every other type requires a non-null userId.",
  });

export interface RecordEntryInput {
  userId: string | null;
  /** Required (and only meaningful) when `type: 'venue_payout'`. */
  venueId?: string | null;
  dateProposalId: string;
  paymentHoldId: string | null;
  type: LedgerEntryType;
  amountCents: number;
  currency: string;
  processorReference: string | null;
  metadata?: Record<string, unknown>;
}

interface LedgerRow {
  id: string;
  user_id: string | null;
  venue_id: string | null;
  date_proposal_id: string;
  payment_hold_id: string | null;
  type: LedgerEntryType;
  amount_cents: string; // bigint comes back as a string from pg
  currency: string;
  processor_reference: string | null;
  metadata: Record<string, unknown>;
  created_at: Date;
}

function mapEntry(row: LedgerRow): LedgerEntry {
  return {
    id: row.id,
    userId: row.user_id,
    venueId: row.venue_id,
    dateProposalId: row.date_proposal_id,
    paymentHoldId: row.payment_hold_id,
    type: row.type,
    amountCents: Number(row.amount_cents),
    currency: row.currency,
    processorReference: row.processor_reference,
    metadata: row.metadata ?? {},
    createdAt: row.created_at,
  };
}

/** Append one immutable ledger row. Never call this outside a transaction shared with the corresponding `payment_holds` write (see module header). */
/**
 * `created_at` here is deliberately left to the column's own SQL `now()`
 * default rather than `ctx.clock.now()` (unlike every business-state
 * timestamp elsewhere in Agent D's code, see `dateProposal.service.ts`/
 * `payment.service.ts`). The ledger is a forensic, append-only audit trail
 * (§14.8) whose ordering must reflect the real order writes physically
 * happened in, not a test's simulated business clock, several money
 * operations record multiple ledger rows back-to-back with a `ManualClock`
 * that hasn't advanced between them, and `ORDER BY created_at` is how
 * `listEntriesForDateProposal`/reconciliation recover chronological order.
 */
export async function recordEntry(ctx: Ctx, input: RecordEntryInput): Promise<LedgerEntry> {
  const parsed = RecordEntrySchema.parse(input);

  const { rows } = await ctx.db.query<LedgerRow>(
    `INSERT INTO payment_ledger (user_id, venue_id, date_proposal_id, payment_hold_id, type, amount_cents, currency, processor_reference, metadata)
     VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb)
     RETURNING *`,
    [
      parsed.userId,
      parsed.venueId ?? null,
      parsed.dateProposalId,
      parsed.paymentHoldId,
      parsed.type,
      parsed.amountCents,
      parsed.currency,
      parsed.processorReference,
      JSON.stringify(parsed.metadata ?? {}),
    ],
  );
  return mapEntry(rows[0]!);
}

export async function listEntriesForDateProposal(ctx: Ctx, dateProposalId: string): Promise<LedgerEntry[]> {
  if (!z.string().uuid().safeParse(dateProposalId).success) {
    throw new ValidationError('dateProposalId must be a uuid');
  }
  const { rows } = await ctx.db.query<LedgerRow>(
    `SELECT * FROM payment_ledger WHERE date_proposal_id = $1 ORDER BY created_at ASC, id ASC`,
    [dateProposalId],
  );
  return rows.map(mapEntry);
}

/** Admin payment ledger viewer (spec §27 item 8). Simple offset-free keyset pagination on `created_at DESC, id DESC`. */
export async function listEntriesForUser(ctx: Ctx, userId: string, params?: { cursor?: string; limit?: number }): Promise<Page<LedgerEntry>> {
  if (!z.string().uuid().safeParse(userId).success) {
    throw new ValidationError('userId must be a uuid');
  }
  const limit = Math.min(Math.max(params?.limit ?? 50, 1), 200);

  let rows: LedgerRow[];
  if (params?.cursor) {
    const [cursorCreatedAt, cursorId] = decodeCursor(params.cursor);
    ({ rows } = await ctx.db.query<LedgerRow>(
      `SELECT * FROM payment_ledger
       WHERE user_id = $1 AND (created_at, id) < ($2, $3)
       ORDER BY created_at DESC, id DESC
       LIMIT $4`,
      [userId, cursorCreatedAt, cursorId, limit + 1],
    ));
  } else {
    ({ rows } = await ctx.db.query<LedgerRow>(
      `SELECT * FROM payment_ledger WHERE user_id = $1 ORDER BY created_at DESC, id DESC LIMIT $2`,
      [userId, limit + 1],
    ));
  }

  const hasMore = rows.length > limit;
  const page = hasMore ? rows.slice(0, limit) : rows;
  const last = page[page.length - 1];
  const nextCursor = hasMore && last ? encodeCursor(last.created_at, last.id) : null;

  return { items: page.map(mapEntry), nextCursor };
}

function encodeCursor(createdAt: Date, id: string): string {
  return Buffer.from(JSON.stringify([createdAt.toISOString(), id])).toString('base64url');
}
function decodeCursor(cursor: string): [string, string] {
  try {
    const [createdAt, id] = JSON.parse(Buffer.from(cursor, 'base64url').toString('utf8')) as [string, string];
    return [createdAt, id];
  } catch {
    throw new ValidationError('Invalid cursor');
  }
}

export interface LedgerMismatch {
  dateProposalId: string;
  paymentHoldId: string | null;
  reason: string;
  ledgerAmountCents: number | null;
  processorAmountCents: number | null;
}

interface HoldForReconciliation {
  id: string;
  date_proposal_id: string;
  user_id: string;
  processor_intent_id: string | null;
  amount_cents: string;
  status: string;
  captured_at: Date | null;
}

/**
 * §25.9 job: compare processor-reported state against local
 * `payment_holds`/`payment_ledger` and flag mismatches for admin review,
 * NEVER auto-corrects financial state (spec §14.8, this module's header).
 *
 * The `PaymentProcessor` port (spec's own design) does not expose a
 * generic "look up an intent by id" method, only authorize/capture/
 * cancel/refund, each of which would itself mutate processor state, which
 * a read-only reconciliation pass must never do. `FakeProcessor` exposes a
 * `_debugGetIntent` escape hatch for tests/dev; a real Stripe adapter would
 * add a dedicated read method (e.g. `retrieveIntent`) to the port when
 * reconciliation goes live in production: that is a port-signature change
 * outside this file's authority, so this function reconciles what it can
 * without one: it flags any *locally inconsistent* state (a ledger entry
 * whose implied hold status doesn't match `payment_holds.status`, or a
 * hold reported `captured`/`refunded` with no matching ledger row) as a
 * mismatch, which is exactly the class of drift a crash between "processor
 * call succeeds" and "persist state" (see payment.service.ts) would leave
 * behind.
 */
export async function reconcileWithProcessor(ctx: Ctx, params?: { since?: Date }): Promise<{ checked: number; mismatches: LedgerMismatch[] }> {
  const since = params?.since ?? new Date(0);

  const { rows: holds } = await ctx.db.query<HoldForReconciliation>(
    `SELECT id, date_proposal_id, user_id, processor_intent_id, amount_cents, status, captured_at
     FROM payment_holds
     WHERE authorized_at >= $1 OR authorized_at IS NULL`,
    [since],
  );

  const mismatches: LedgerMismatch[] = [];

  for (const hold of holds) {
    const { rows: ledgerRows } = await ctx.db.query<{ type: LedgerEntryType; amount_cents: string }>(
      `SELECT type, amount_cents FROM payment_ledger WHERE payment_hold_id = $1 ORDER BY created_at ASC`,
      [hold.id],
    );
    // A 'capture' ledger row with amount 0 is the audit trail of a
    // *declined* capture attempt (see `payment.service#captureHold`), it
    // moved no money, so it must not be treated as evidence the hold
    // should be 'captured'.
    const capturedEntries = ledgerRows.filter((r) => r.type === 'capture' && Number(r.amount_cents) > 0);
    const refundedEntries = ledgerRows.filter((r) => r.type === 'refund');

    // A hold the local DB believes is captured must have exactly one
    // 'capture' ledger row, and vice versa.
    if (hold.status === 'captured' && capturedEntries.length === 0) {
      mismatches.push({
        dateProposalId: hold.date_proposal_id,
        paymentHoldId: hold.id,
        reason: 'hold marked captured with no capture ledger entry',
        ledgerAmountCents: null,
        processorAmountCents: Number(hold.amount_cents),
      });
    }
    if (hold.status !== 'captured' && hold.status !== 'refunded' && capturedEntries.length > 0) {
      mismatches.push({
        dateProposalId: hold.date_proposal_id,
        paymentHoldId: hold.id,
        reason: `capture ledger entry exists but hold status is '${hold.status}'`,
        ledgerAmountCents: Number(capturedEntries[0]!.amount_cents),
        processorAmountCents: null,
      });
    }
    if (hold.status === 'refunded' && refundedEntries.length === 0) {
      mismatches.push({
        dateProposalId: hold.date_proposal_id,
        paymentHoldId: hold.id,
        reason: 'hold marked refunded with no refund ledger entry',
        ledgerAmountCents: null,
        processorAmountCents: null,
      });
    }

    // Cross-check against the live processor state where the port allows it
    // (FakeProcessor's debug hook; a production adapter would use its own
    // read method here instead, see function-level doc).
    const debugGetIntent = (ctx.payments as { _debugGetIntent?: (id: string) => { status: string; capturedAmountCents: number } | undefined })._debugGetIntent;
    if (debugGetIntent && hold.processor_intent_id) {
      const intent = debugGetIntent.call(ctx.payments, hold.processor_intent_id);
      if (intent && hold.status === 'captured' && intent.status === 'captured' && intent.capturedAmountCents !== Number(hold.amount_cents)) {
        mismatches.push({
          dateProposalId: hold.date_proposal_id,
          paymentHoldId: hold.id,
          reason: 'local captured amount does not match processor captured amount',
          ledgerAmountCents: Number(hold.amount_cents),
          processorAmountCents: intent.capturedAmountCents,
        });
      }
    }
  }

  return { checked: holds.length, mismatches };
}
