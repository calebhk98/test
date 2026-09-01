/**
 * src/http/serializers/payment.ts — payment method / ledger views.
 *
 * Spec §28.4 "do not store card numbers"; `PaymentMethodSummary` (domain
 * type) already structurally carries only `brand`/`last4`/processor
 * metadata, never a raw token or PAN — this is the explicit-allowlist
 * last line of defence on top of that, and the one place a venue-staff
 * response is guaranteed to never reach (no route wires this serializer
 * for a venue-staff-authenticated request — see `src/http/auth.ts`'s role
 * guards and C-4.2.6).
 */
import type { LedgerEntry, PaymentMethodSummary } from '../../domain/types.js';

export interface PaymentMethodView {
  id: string;
  processor: string;
  brand: string | null;
  last4: string | null;
  isDefault: boolean;
  verifiedAt: string | null;
  createdAt: string;
}

export function serializePaymentMethod(m: PaymentMethodSummary): PaymentMethodView {
  return {
    id: m.id,
    processor: m.processor,
    brand: m.brand,
    last4: m.last4,
    isDefault: m.isDefault,
    verifiedAt: m.verifiedAt ? m.verifiedAt.toISOString() : null,
    createdAt: m.createdAt.toISOString(),
  };
}

export interface LedgerEntryView {
  id: string;
  dateProposalId: string;
  type: LedgerEntry['type'];
  amountCents: number;
  currency: string;
  createdAt: string;
}

export function serializeLedgerEntry(e: LedgerEntry): LedgerEntryView {
  return {
    id: e.id,
    dateProposalId: e.dateProposalId,
    type: e.type,
    amountCents: e.amountCents,
    currency: e.currency,
    createdAt: e.createdAt.toISOString(),
  };
}
