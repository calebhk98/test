/**
 * src/domain/i18n/statusLabels.ts — the "status must never be conveyed by
 * colour alone" backend guarantee (task brief accessibility rule 2).
 *
 * Every status-shaped enum already returned by this API (trust level,
 * date-proposal state, payment-hold state, ...) is already a plain
 * machine-readable string — that half of the rule was true before this
 * build. What was missing is the other half: a locale-aware, HUMAN-
 * readable label a client can show next to (or instead of) a colour, so a
 * colour-blind user or a screen reader never has to infer meaning from
 * hue alone. `describeStatus` is that: given a domain + the raw enum
 * value already on the row, it returns the value back (unchanged — for a
 * client that already switches on it) plus a `tone` (a small closed set,
 * NOT a colour name — see below) plus a localized `label`.
 *
 * `tone` is deliberately an abstract word, not "green"/"red"/"amber": a
 * client is free to map `'critical'` to a red badge, a bold icon, or a
 * screen-reader-only "(critical)" suffix — the API commits to the
 * SEMANTIC classification, never to a colour choice, which is exactly
 * the separation of concerns spec §1's "no generative text" also aims
 * for (backend picks stable machine facts; the client picks presentation).
 *
 * INTEGRATION: this module is standalone — it does not (and, per this
 * build's file ownership, cannot) edit any serializer. See
 * docs/accessibility.md for the exact one-line change each serializer
 * that already emits one of these enums would add: spread
 * `describeStatus(domain, row.status, locale)` alongside the existing raw
 * field.
 */
import { DEFAULT_LOCALE, fallbackChain } from './locales.js';

export type StatusTone = 'neutral' | 'positive' | 'caution' | 'critical';

export interface StatusDescriptor {
  /** The raw enum value, unchanged — a client that already switches on this keeps working exactly as before. */
  status: string;
  /** Abstract semantic classification — see module doc. Never a colour name. */
  tone: StatusTone;
  /** Localized, human-readable label. Never abbreviated (task brief: "avoid abbreviations that a screen reader mangles" — e.g. "Payment failed", not "Pmt failed"). */
  label: string;
}

interface StatusDef {
  tone: StatusTone;
  labels: Record<string, string>; // locale -> label; every entry MUST have "en"
}

/** One domain's full set of status values. Keying by (domain, value) rather than reusing `src/domain/i18n/catalog.ts`'s single flat key namespace keeps this table's shape self-documenting and lets `tests/unit/altText.test.ts` mechanically assert "every domain's every declared value has a tone and an `en` label" without needing to know catalog key naming conventions. */
type StatusRegistry = Record<string, Record<string, StatusDef>>;

function def(tone: StatusTone, en: string, es: string): StatusDef {
  return { tone, labels: { en, es } };
}

/**
 * Every status-shaped domain this backend's schema currently defines (see
 * src/domain/types.ts) that a client could plausibly colour-code. Deal-
 * breaker-only or purely categorical enums (report category, venue
 * category, message-flag type, ...) are NOT included — those are
 * classifications, not a state a user watches change over time, so the
 * "colour alone" risk this rule targets doesn't apply to them the same
 * way. New status values must be added here in the same change that adds
 * them to `src/domain/types.ts` — `tests/unit/altText.test.ts` walks this
 * table for shape, but cannot detect a value the enum gained and this
 * table didn't (no import of the (deliberately untouched) owning
 * service's file crosses that boundary — see docs/accessibility.md).
 */
export const STATUS_REGISTRY: StatusRegistry = {
  userStatus: {
    active: def('positive', 'Active', 'Activa'),
    suspended: def('critical', 'Suspended', 'Suspendida'),
    deleted: def('neutral', 'Deleted', 'Eliminada'),
  },
  trustLevel: {
    limited: def('caution', 'Limited trust', 'Confianza limitada'),
    standard: def('neutral', 'Standard trust', 'Confianza estándar'),
    trusted: def('positive', 'Trusted', 'De confianza'),
    elite: def('positive', 'Elite trust', 'Confianza élite'),
  },
  photoModerationStatus: {
    pending: def('neutral', 'Under review', 'En revisión'),
    approved: def('positive', 'Approved', 'Aprobada'),
    rejected: def('critical', 'Rejected', 'Rechazada'),
    flagged: def('caution', 'Flagged for review', 'Marcada para revisión'),
  },
  interestStatus: {
    pending: def('neutral', 'Pending', 'Pendiente'),
    accepted: def('positive', 'Accepted', 'Aceptada'),
    declined: def('neutral', 'Declined', 'Rechazada'),
    expired: def('neutral', 'Expired', 'Vencida'),
    canceled: def('neutral', 'Canceled', 'Cancelada'),
  },
  conversationStatus: {
    active: def('positive', 'Active', 'Activa'),
    cooling: def('caution', 'Going quiet', 'Perdiendo actividad'),
    archived: def('neutral', 'Archived', 'Archivada'),
    established: def('positive', 'Established', 'Consolidada'),
  },
  notificationStatus: {
    pending: def('neutral', 'Pending', 'Pendiente'),
    sent: def('neutral', 'Sent', 'Enviada'),
    failed: def('critical', 'Failed to send', 'No se pudo enviar'),
    read: def('neutral', 'Read', 'Leída'),
  },
  dateProposalStatus: {
    draft: def('neutral', 'Draft', 'Borrador'),
    pending_acceptance: def('neutral', 'Awaiting response', 'Esperando respuesta'),
    accepted: def('positive', 'Accepted', 'Aceptada'),
    declined: def('neutral', 'Declined', 'Rechazada'),
    expired: def('neutral', 'Expired', 'Vencida'),
    canceled: def('neutral', 'Canceled', 'Cancelada'),
    payment_failed: def('critical', 'Payment failed', 'El pago falló'),
    charged: def('neutral', 'Payment charged', 'Pago cobrado'),
    ticketed: def('positive', 'Ticket issued', 'Boleto emitido'),
    completed: def('positive', 'Completed', 'Completada'),
    completed_unverified: def('caution', 'Completed, unverified', 'Completada, sin verificar'),
    no_show: def('critical', 'No-show reported', 'Inasistencia reportada'),
    refunded: def('neutral', 'Refunded', 'Reembolsada'),
    disputed: def('critical', 'Under dispute', 'En disputa'),
  },
  paymentHoldStatus: {
    pending: def('neutral', 'Pending', 'Pendiente'),
    authorized: def('neutral', 'Authorized', 'Autorizado'),
    capture_pending: def('neutral', 'Charge pending', 'Cobro pendiente'),
    captured: def('positive', 'Charged', 'Cobrado'),
    released: def('neutral', 'Released, not charged', 'Liberado, sin cobrar'),
    failed: def('critical', 'Failed', 'Fallido'),
    refunded: def('neutral', 'Refunded', 'Reembolsado'),
  },
  voucherStatus: {
    issued: def('neutral', 'Issued', 'Emitido'),
    redeemed: def('positive', 'Redeemed', 'Canjeado'),
    expired: def('neutral', 'Expired', 'Vencido'),
    canceled: def('neutral', 'Canceled', 'Cancelado'),
  },
  moderationActionType: {
    none: def('positive', 'No action taken', 'Sin medidas tomadas'),
    warning: def('caution', 'Warning issued', 'Advertencia emitida'),
    restriction: def('caution', 'Account restricted', 'Cuenta restringida'),
    shadowban: def('critical', 'Visibility limited', 'Visibilidad limitada'),
    suspension: def('critical', 'Account suspended', 'Cuenta suspendida'),
  },
  appealStatus: {
    pending: def('neutral', 'Under review', 'En revisión'),
    approved: def('positive', 'Approved', 'Aprobada'),
    rejected: def('critical', 'Rejected', 'Rechazada'),
  },
};

export type StatusDomain = keyof typeof STATUS_REGISTRY;

/**
 * Resolves the tone + localized label for one (domain, status) pair,
 * walking the same locale fallback chain `translate()` uses (locales.ts
 * `fallbackChain`) — a locale with no Spanish-equivalent label yet (every
 * locale but `es` today) degrades to the `en` label, never a raw key or a
 * thrown error, same contract as `translate()`.
 *
 * Throws only for a genuinely unknown (domain, value) pair — i.e. a
 * caller passing a status this registry hasn't been told about, which
 * (same reasoning as `translate()`'s missing-KEY case) is a code bug,
 * not a runtime/user condition: showing a colour-coded status with no
 * label at all would be exactly the accessibility gap this module exists
 * to close.
 */
export function describeStatus(domain: StatusDomain, status: string, locale: string): StatusDescriptor {
  const domainDefs = STATUS_REGISTRY[domain];
  const statusDef = domainDefs?.[status];
  if (!statusDef) {
    throw new Error(`i18n: unknown status "${status}" for domain "${domain}" — add it to STATUS_REGISTRY`);
  }
  for (const loc of fallbackChain(locale)) {
    const label = statusDef.labels[loc];
    if (label) return { status, tone: statusDef.tone, label };
  }
  // Every entry is required to carry an "en" label (enforced by
  // tests/unit/altText.test.ts), and DEFAULT_LOCALE is always the last
  // link of fallbackChain, so this is unreachable in practice — kept as
  // an explicit, typed failure rather than a non-null assertion.
  throw new Error(`i18n: status "${domain}.${status}" has no "${DEFAULT_LOCALE}" label`);
}
