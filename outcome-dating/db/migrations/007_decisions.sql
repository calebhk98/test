-- 007_decisions.sql
-- Product-decision layer on top of the completed service implementation
-- (see docs/conformance.md, "Open Questions / Spec Conflicts" OQ-1, OQ-3,
-- OQ-8, OQ-10). Three open questions were resolved by the product owner:
--
--   OQ-8 (venue settlement): §15.4 implies venues are eventually paid their
--     `margin_percent` (§13.2/§23.16) but the original spec defines no
--     payout mechanism. This migration adds it: a `venue_settlements`
--     table plus a `venue_payout` payment_ledger entry type.
--   OQ-3 (no_show / disputed resolution): no schema change needed beyond a
--     `date_proposals.dispute_resolved_at` idempotency marker — `disputed`
--     stays a terminal `DateProposalStatus` (§13.3), only auto-resolved
--     "underneath" via the report/trust machinery, not a new status.
--   OQ-1 / OQ-10 (inclusive thresholds): pure application-code behavior
--     (already `>=` throughout — see the final report), no schema change.
--
-- Conventions match 001_init.sql: bigint minor-unit money, timestamptz,
-- text + CHECK for enumerated columns (not native ENUM) so this migration
-- can extend existing CHECK constraints with a plain ALTER rather than
-- ALTER TYPE ceremony.

-- =========================================================================
-- 1. payment_ledger: add the `venue_payout` entry type (OQ-8).
--
-- A venue_payout ledger row pays a VENUE, not a user — `payment_ledger`
-- had no representation for that (user_id was NOT NULL, no venue_id
-- column existed at all). Rather than force venue payouts through a
-- user_id (there is no "venue's user account" concept anywhere else in
-- this schema), user_id is relaxed to nullable and a nullable venue_id FK
-- is added, with a CHECK enforcing that exactly one of the two is set,
-- keyed off `type`. Every pre-existing entry type keeps user_id NOT
-- NULL-in-practice (enforced by the same CHECK, just no longer at the
-- column level) and venue_id NULL — no existing INSERT statement in
-- ledger.service.ts's `recordEntry` needs to change shape for the six
-- original types.
-- =========================================================================
ALTER TABLE payment_ledger ALTER COLUMN user_id DROP NOT NULL;
ALTER TABLE payment_ledger ADD COLUMN venue_id uuid REFERENCES venues (id);

ALTER TABLE payment_ledger DROP CONSTRAINT payment_ledger_type_check;
ALTER TABLE payment_ledger ADD CONSTRAINT payment_ledger_type_check
  CHECK (type IN ('authorization', 'capture', 'release', 'refund', 'dispute', 'chargeback', 'venue_payout')); -- §14.8 + OQ-8

ALTER TABLE payment_ledger ADD CONSTRAINT payment_ledger_payee_check
  CHECK (
    (type = 'venue_payout' AND venue_id IS NOT NULL AND user_id IS NULL)
    OR (type <> 'venue_payout' AND user_id IS NOT NULL AND venue_id IS NULL)
  );

CREATE INDEX idx_payment_ledger_venue ON payment_ledger (venue_id) WHERE venue_id IS NOT NULL;

-- =========================================================================
-- 2. venue_settlements — the payout mechanism itself (OQ-8).
--
-- One row per settled date_proposal, ever (UNIQUE on date_proposal_id is
-- the idempotency backstop a retried settlement run relies on — see
-- src/services/venueSettlement.service.ts). `gross_escrow_cents` is the
-- sum of both participants' captured escrow for that proposal;
-- `margin_percent_applied` is the venue's `margin_percent` AS IT STOOD AT
-- SETTLEMENT TIME (an immutable historical record, independent of any
-- later `adminUpdateVenue` change) — `venue_payout_cents +
-- platform_cents = gross_escrow_cents` always holds exactly (integer
-- floor-division money math, see the service for the worked rounding
-- rule).
-- =========================================================================
CREATE TABLE venue_settlements (
  id                       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  venue_id                 uuid NOT NULL REFERENCES venues (id),
  date_proposal_id         uuid NOT NULL UNIQUE REFERENCES date_proposals (id),
  gross_escrow_cents       bigint NOT NULL CHECK (gross_escrow_cents >= 0),
  margin_percent_applied   double precision NOT NULL CHECK (margin_percent_applied BETWEEN 0 AND 100),
  venue_payout_cents       bigint NOT NULL CHECK (venue_payout_cents >= 0),
  platform_cents           bigint NOT NULL CHECK (platform_cents >= 0),
  status                   text NOT NULL DEFAULT 'settled'
                             CHECK (status IN ('settled', 'failed')),
  settlement_period        text NOT NULL, -- e.g. "2026-01" (UTC year-month at settlement time)
  created_at               timestamptz NOT NULL DEFAULT now(),
  settled_at               timestamptz,
  processor_reference      text,

  CONSTRAINT venue_settlements_payout_sums_to_gross
    CHECK (venue_payout_cents + platform_cents = gross_escrow_cents)
);

CREATE INDEX idx_venue_settlements_venue ON venue_settlements (venue_id, created_at DESC);
CREATE INDEX idx_venue_settlements_period ON venue_settlements (settlement_period);

-- =========================================================================
-- 3. date_proposals: idempotency marker for automated dispute resolution
-- (OQ-3). `disputed` stays a terminal DateProposalStatus (§13.3) — this
-- column records that the automated "implicit no-show report against the
-- non-confirming party" step (routed through report.service/trust.service)
-- has already run for this proposal, so the sweep job can re-run safely
-- without filing a duplicate report or double-counting trust deltas.
-- =========================================================================
ALTER TABLE date_proposals ADD COLUMN dispute_resolved_at timestamptz;

CREATE INDEX idx_date_proposals_dispute_resolution
  ON date_proposals (status, scheduled_end)
  WHERE status = 'disputed' AND dispute_resolved_at IS NULL;

-- Ticketed-but-unresolved-completion sweep (OQ-3 no_show / disputed entry
-- points) scans exactly this shape: `ticketed` proposals whose no-scan
-- window may have closed.
CREATE INDEX idx_date_proposals_completion_sweep
  ON date_proposals (status, scheduled_end)
  WHERE status = 'ticketed';

-- =========================================================================
-- 4. notifications: add the five missing event types flagged by
-- dateProposal.service.ts's module doc (OQ-3's "no human step" transitions
-- need to be able to notify) — canceled/refunded/disputed/no-show/completed
-- had no NotificationEventType at all.
-- =========================================================================
ALTER TABLE notifications DROP CONSTRAINT notifications_event_type_check;
ALTER TABLE notifications ADD CONSTRAINT notifications_event_type_check
  CHECK (event_type IN (
    'interest_received', 'interest_accepted', 'interest_declined', 'interest_expiring_soon',
    'chat_opened', 'date_proposal_received', 'date_accepted', 'payment_hold_authorized',
    'payment_failed', 'ticket_issued', 'date_reminder', 'venue_redeemed',
    'post_date_feedback_request', 'chat_cooling', 'trust_level_changed', 'safety_notice',
    'date_canceled', 'date_refunded', 'date_disputed', 'date_no_show', 'date_completed'
  ));
