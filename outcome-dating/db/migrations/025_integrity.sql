-- 025_integrity.sql
--
-- Fixes for docs/normalization.md's "Worth changing, ranked by real
-- corruption risk" list, in that order. Each numbered block below
-- corresponds to one ranked item. Every constraint added here has a
-- matching "bad state is rejected" test in tests/unit/integrity.test.ts.
--
-- Two ranked items are NOT fully closed by this migration, on purpose —
-- both because the safe fix requires editing a file outside this build's
-- ownership. See the comments at the bottom of each relevant section for
-- exactly why, and what the follow-up change is.

-- =========================================================================
-- 1. post_date_feedback: `positive` (legacy) vs `outcome` (check-in) can
--    disagree.
-- =========================================================================
--
-- Root fix (application layer, not in this file): the legacy write path
-- (`dateProposal.service#submitPostDateFeedback`, which used to run its
-- own INSERT/UPDATE touching only `positive`/`would_meet_again`/
-- `safety_concern`/`notes`) is deleted. `POST /date-proposals/:id/feedback`
-- still exists for HTTP backward compatibility, but now translates its
-- body and calls `postDateFeedbackService#submitLegacyFeedback`, which
-- shares the SAME write statement as `submitCheckIn` (see
-- postDateFeedback.service.ts). There is exactly one place in the
-- codebase that writes outcome/safety data to this table now, and it
-- never writes `positive` at all — new rows only ever get `outcome`.
--
-- `positive` is kept (not dropped): src/services/stats.service.ts and
-- src/jobs/statsAggregation.job.ts (both owned by the stats agent, out of
-- this build's scope) read `positive` directly via raw SQL as a fallback
-- for rows that predate the check-in's `outcome` column
-- (statsAggregation.job.ts literally encodes `positive = true OR outcome
-- = 'happened_good'` / `positive = false OR outcome = 'happened_bad'` as
-- one condition). Dropping the column would break those queries outright
-- with no way for this build to fix the break. Instead:
--
--   (a) Backfill every historical legacy-only row (outcome still NULL,
--       positive set) onto the equivalent outcome value, using the exact
--       equivalence statsAggregation.job.ts already assumes. After this,
--       every row readable through the newer outcome-based surfaces
--       (getMyCheckIn, getMyDateOutcomes) reflects legacy feedback too.
--   (b) Backfill `safety_flag` from the legacy `safety_concern` boolean
--       for the same historical rows, so a flagged legacy row is at
--       least visible as a 'concern' going forward. This does NOT
--       retroactively file a report (see report_id, left NULL) — auto-
--       filing a report for a historical flag with no live corroboration
--       context would be a behavior change with real consequences, not a
--       normalization fix.
--   (c) A CHECK constraint ties the two columns together for any row
--       that has both set, so a future second writer (should one ever
--       reappear) cannot recreate a contradictory row: `positive = true`
--       must pair with `outcome = 'happened_good'`, `positive = false`
--       with `outcome = 'happened_bad'` — the same pairing the backfill
--       uses and the same one statsAggregation.job.ts already treats as
--       equivalent. Any other pairing (e.g. positive = true with
--       outcome = 'happened_bad', the literal "both good and bad at
--       once" bug this item exists to close) is now rejected by the
--       database itself, not just by there being one writer.

UPDATE post_date_feedback
   SET outcome = CASE WHEN positive THEN 'happened_good' ELSE 'happened_bad' END
 WHERE outcome IS NULL AND positive IS NOT NULL;

UPDATE post_date_feedback
   SET safety_flag = 'concern'
 WHERE safety_flag = 'none' AND safety_concern = true;

ALTER TABLE post_date_feedback
  ADD CONSTRAINT post_date_feedback_positive_outcome_agree CHECK (
    positive IS NULL
    OR outcome IS NULL
    OR (positive = true  AND outcome = 'happened_good')
    OR (positive = false AND outcome = 'happened_bad')
  );

-- =========================================================================
-- 2. users: `status = 'suspended'` vs the separate `suspended` boolean
--    can disagree.
-- =========================================================================
--
-- `status` is the authoritative field: it is the one checked first and
-- foremost everywhere a suspension actually gates behavior (`auth.service
-- #login` rejects on `status = 'suspended'`; `discovery.service
-- #isProfileVisibleTo` rejects on `status <> 'active'` as rule 1, before
-- even looking at `suspended`; `moderation.service#isUserInGoodStanding`
-- checks `status = 'active'`). `suspended` is read directly in a few more
-- places (discovery.service.ts's candidate-pool query, auth.service.ts's
-- returned user shape, profile.routes.ts's admin view) but never as the
-- SOLE gate — `status` is checked first, or alongside it, everywhere it
-- matters.
--
-- `suspended` cannot simply be dropped and derived: `src/seed.ts`,
-- `src/services/auth.service.ts`, and several test fixtures outside this
-- build's ownership (e.g. tests/unit/testCtxAgentE.ts's `insertUser`)
-- explicitly INSERT a `suspended` value as one of the row's columns —
-- turning it into a GENERATED column would make every one of those
-- INSERTs fail outright (Postgres refuses an explicit value for a
-- generated column, even the "correct" one), which is a much larger,
-- more certain breakage than the one this CHECK accepts below.
--
-- The constraint below is the literal fix docs/normalization.md itself
-- proposes for this item. It rejects a user row where the two disagree
-- in either direction: `status = 'suspended'` with `suspended = false`,
-- or `suspended = true` with any other `status`.
--
-- KNOWN CONFLICT (out of this build's ownership): tests/unit/
-- discovery.test.ts's `makeUser('suspended')` helper (around line 213)
-- inserts `status = 'suspended'` without ever setting `suspended = true`
-- (the column is omitted from that INSERT entirely, so it defaults to
-- false) — precisely the disagreement this constraint exists to reject.
-- That test currently passes only because nothing enforced the pairing;
-- after this migration its fixture INSERT will fail with a constraint
-- violation. The fix is a one-line change to that helper (also set
-- `suspended = true`), but tests/unit/discovery.test.ts is outside the
-- file list this build may modify, so it is reported here rather than
-- edited.

ALTER TABLE users
  ADD CONSTRAINT users_status_suspended_agree CHECK ((status = 'suspended') = suspended);

-- =========================================================================
-- 3. users: `trust_level` is a pure function of `trust_score`, stored
--    separately.
-- =========================================================================
--
-- NOT fixed with a table-level constraint (CHECK, generated column, or
-- trigger) on `users` itself — see trust.service.ts#recalculateTrustScore
-- for the fix that WAS made there, and the reasoning below for why a
-- table-level one was deliberately not added on top.
--
-- The band boundaries (`trust.level_standard_min`, `trust.level_trusted
-- _min`, `trust.level_elite_min`) live in `config_entries` and are
-- explicitly documented as admin-retunable (spec §21). That rules out a
-- GENERATED column outright, not just as a design preference: Postgres
-- forbids a GENERATED ALWAYS AS expression from reading any table but
-- the row's own (SQL standard restriction, not a Postgres limitation to
-- work around), so a generated column literally cannot consult
-- `config_entries`. The same restriction applies to a CHECK constraint —
-- Postgres rejects a CHECK expression that references another table at
-- all, config-driven bounds or not. So neither of the two purely
-- declarative options is available here; only a function/trigger that
-- runs real SQL against `config_entries` can look at the current bounds.
--
-- A function that does that is added below, `trust_level_for_score`, and
-- trust.service.ts's `recalculateTrustScore` (the one legitimate
-- production writer of both columns) now calls it INSIDE the same UPDATE
-- that writes `trust_score`, instead of computing the level separately in
-- TypeScript (via a possibly cache-stale `ctx.config` read) and passing
-- it down as an independent literal. That closes the actual gap this
-- item flags for the one real writer: trust_score and trust_level can no
-- longer drift apart from within that function, under any config, without
-- a second migration.
--
-- A trigger that forcibly overwrites `trust_level` from `trust_score` on
-- EVERY write (closing the gap even against a hypothetical future second
-- writer, the way item 1's CHECK does) was deliberately not added: a wide
-- swath of this codebase's own test fixtures, outside this build's
-- ownership, set `trust_level` directly and independently of
-- `trust_score` on purpose, to pin a user at a given trust TIER for
-- unrelated test setup, without going through real trust-event scoring.
-- For example: tests/unit/decisionsConfig.test.ts's
-- `UPDATE users SET trust_level = 'limited' WHERE id = $1` (no matching
-- trust_score change); tests/unit/testCtxAgentC.ts, tests/unit/
-- testCtxDecisions.ts, tests/unit/testHarnessMatch.ts, tests/unit/
-- testCtxEligibility.ts, and tests/jobs/testHarness.ts all take
-- `trustLevel`/`trust_level` as an independent fixture parameter with the
-- same intent. A forcing trigger would silently overwrite every one of
-- those fixtures' chosen tier back to whatever the DEFAULT trust_score
-- (usually 50, "standard") maps to, which is a silent, hard-to-diagnose
-- behavior change across a large number of files this build may not
-- touch — worse than leaving the gap open for a hypothetical future
-- second writer that does not exist today.

CREATE OR REPLACE FUNCTION trust_level_for_score(p_trust_score integer)
RETURNS text
LANGUAGE sql
STABLE
AS $$
  SELECT CASE
    WHEN p_trust_score >= COALESCE(
      (SELECT (value_json #>> '{}')::int FROM config_entries WHERE key = 'trust.level_elite_min'), 90)
      THEN 'elite'
    WHEN p_trust_score >= COALESCE(
      (SELECT (value_json #>> '{}')::int FROM config_entries WHERE key = 'trust.level_trusted_min'), 70)
      THEN 'trusted'
    WHEN p_trust_score >= COALESCE(
      (SELECT (value_json #>> '{}')::int FROM config_entries WHERE key = 'trust.level_standard_min'), 40)
      THEN 'standard'
    ELSE 'limited'
  END;
$$;

-- =========================================================================
-- 4. interests / date_proposals / payment_holds: status vs. transition
--    timestamps can disagree.
-- =========================================================================
--
-- `interests` is a true one-shot state machine (pending -> exactly one
-- terminal status, never revisited — verified against every write site in
-- interest.service.ts: sendInterest, acceptInterest, atomicTransition
-- (decline/cancel), autoDeclineOne, expireDuePendingInterests all stamp
-- exactly one of the four terminal timestamp columns and only from
-- `status = 'pending'`), so the full bijective constraint
-- docs/normalization.md's own example describes is safe to add in both
-- directions: pending has every terminal timestamp NULL, and each
-- terminal status has its own timestamp set and no other terminal
-- timestamp set.
--
-- KNOWN CONFLICT (out of this build's ownership): tests/perf/
-- seedScaleCurve.ts (around line 224) seeds `interests` rows with status
-- and `accepted_at` drawn from two INDEPENDENT `random()` calls, so a
-- meaningful fraction of seeded rows will have `status = 'accepted'` with
-- `accepted_at IS NULL` or vice versa — this is the exact bug class this
-- constraint exists to reject, now caught in a performance-seeding
-- script that plainly never meant to create it. tests/perf/** is outside
-- this build's ownership (owned by the agent on tests/perf/ and
-- db/migrations/023), so it is reported here rather than edited. Fix:
-- tie the `accepted_at` draw to the same `status` draw (e.g.
-- `CASE WHEN status = 'accepted' THEN now() ELSE NULL END`) instead of
-- drawing it independently.

ALTER TABLE interests
  ADD CONSTRAINT interests_status_timestamp_agree CHECK (
    (status = 'pending'  AND accepted_at IS NULL     AND declined_at IS NULL AND canceled_at IS NULL AND expired_at IS NULL) OR
    (status = 'accepted' AND accepted_at IS NOT NULL AND declined_at IS NULL AND canceled_at IS NULL AND expired_at IS NULL) OR
    (status = 'declined' AND declined_at IS NOT NULL AND accepted_at IS NULL AND canceled_at IS NULL AND expired_at IS NULL) OR
    (status = 'canceled' AND canceled_at IS NOT NULL AND accepted_at IS NULL AND declined_at IS NULL AND expired_at IS NULL) OR
    (status = 'expired'  AND expired_at  IS NOT NULL AND accepted_at IS NULL AND declined_at IS NULL AND canceled_at IS NULL)
  );

-- `date_proposals` and `payment_holds` are NOT one-shot: both accumulate
-- timestamps across a real pipeline (date_proposals: accepted -> charged
-- -> ticketed -> completed all stamp their own column and keep the
-- earlier ones; payment_holds: authorized -> captured, and captured ->
-- refunded, likewise keep the earlier stamp). A row "claiming to be
-- ticketed" legitimately still has accepted_at AND charged_at non-null
-- from its own earlier, real transitions — a bijective constraint like
-- the one above would be WRONG here, not just strict.
--
-- The safe subset actually added below is deliberately narrow, chosen
-- after checking every direct SQL writer of these two tables in both
-- src/** and tests/**: it only constrains (a) the pre-anything states,
-- which must have every downstream timestamp NULL (this is exactly
-- docs/normalization.md's own literal example: "status='pending' [not
-- yet accepted] with accepted_at set"), and (b) a small number of
-- specific statuses where every legitimate writer — production code AND
-- every test fixture found — already always sets that status's own
-- timestamp, so the forward direction is safe to require too.
--
-- date_proposals: only `dateProposal.service.ts` (this build's own file)
-- ever writes `status`/its timestamp columns in production code (grep
-- confirmed no other src/** writer). Every one of the many out-of-scope
-- test fixtures that create a date_proposals row directly at a LATER
-- status (e.g. tests/jobs/ticketedCompletionSweep.test.ts,
-- tests/jobs/matchingSignalSweep.test.ts, tests/jobs/
-- checkInPromptSweep.test.ts, tests/jobs/voucherExpiry.test.ts,
-- tests/unit/testCtxRetention.ts, tests/unit/deletion.test.ts, and this
-- build's own tests/http/feedback.test.ts / tests/unit/
-- postDateFeedback.test.ts before this migration) does so WITHOUT
-- backfilling the earlier pipeline's timestamps, because those tests
-- only care about "this row is at status X" and not its history. A
-- forward requirement for accepted/charged/ticketed/completed/disputed/
-- no_show/completed_unverified would reject the overwhelming majority of
-- those fixtures. So only the pre-acceptance states (draft,
-- pending_acceptance — nothing has happened to the proposal yet, so
-- every timestamp must be NULL) and declined/expired/canceled/refunded
-- (each reachable only via a single dedicated stamp — declined_at,
-- expired_at, or canceled_at, which `timeline.service.ts` itself already
-- relies on `canceled_at` covering both canceled AND refunded, per
-- dateProposal.service.ts's own comment on that reuse) are constrained.
-- 'completed'/'ticketed'/'accepted'/'charged'/etc. carry no requirement
-- at all under this narrower constraint set — including this build's own
-- tests/http/feedback.test.ts / tests/unit/postDateFeedback.test.ts
-- fixtures, which create 'completed'/'ticketed' rows with no timestamps
-- set and need no change for this migration.

ALTER TABLE date_proposals
  ADD CONSTRAINT date_proposals_pre_acceptance_no_later_timestamps CHECK (
    status NOT IN ('draft', 'pending_acceptance')
    OR (
      accepted_at IS NULL AND declined_at IS NULL AND expired_at IS NULL AND canceled_at IS NULL
      AND charged_at IS NULL AND ticketed_at IS NULL AND completed_at IS NULL
    )
  );

ALTER TABLE date_proposals
  ADD CONSTRAINT date_proposals_declined_has_timestamp
    CHECK (status <> 'declined' OR declined_at IS NOT NULL);

ALTER TABLE date_proposals
  ADD CONSTRAINT date_proposals_expired_has_timestamp
    CHECK (status <> 'expired' OR expired_at IS NOT NULL);

ALTER TABLE date_proposals
  ADD CONSTRAINT date_proposals_canceled_family_has_timestamp
    CHECK (status NOT IN ('canceled', 'refunded') OR canceled_at IS NOT NULL);

-- payment_holds: same reasoning. Only `payment.service.ts` (out of this
-- build's ownership, but its every write site was checked) writes this
-- table in production code, always consistently. `status = 'pending'`
-- (the schema default, before any authorize attempt) must have every
-- timestamp NULL. `authorized`/`capture_pending` always follow a real
-- authorize call in every production and test writer found, so
-- `authorized_at IS NOT NULL` is safe to require for both. A forward
-- requirement for `captured`/`released`/`refunded` was NOT added:
-- tests/jobs/venuePayoutSettlement.test.ts (around line 44) creates a
-- `captured` hold with only `captured_at` set (no `authorized_at`), and
-- tests/unit/deletion.test.ts (around line 193) creates a `captured` hold
-- with NEITHER timestamp set — both outside this build's ownership, both
-- would fail a forward requirement on `captured`.

ALTER TABLE payment_holds
  ADD CONSTRAINT payment_holds_pending_no_timestamps CHECK (
    status <> 'pending'
    OR (authorized_at IS NULL AND captured_at IS NULL AND released_at IS NULL AND refunded_at IS NULL)
  );

ALTER TABLE payment_holds
  ADD CONSTRAINT payment_holds_authorized_has_timestamp
    CHECK (status NOT IN ('authorized', 'capture_pending') OR authorized_at IS NOT NULL);

-- =========================================================================
-- 5. notification_dedup_log.outbox_id has no foreign key.
-- =========================================================================
--
-- NOT added in this migration. This is a real gap, but a plain
-- `REFERENCES notification_outbox (id)` cannot be added safely without
-- also changing src/services/notifications/outbox.ts (outside this
-- build's ownership), because that file's `enqueueNotification` writes
-- `notification_dedup_log.outbox_id` in two separate, non-transactional
-- steps:
--
--   1. `INSERT INTO notification_dedup_log (dedup_key, outbox_id, ...)
--      VALUES ($1, $2, ...) ON CONFLICT (dedup_key) DO NOTHING` where
--      `$2` is `claimId = newId()` — a freshly generated uuid that does
--      NOT correspond to any `notification_outbox` row yet. This is a
--      deliberate "claim the dedup key first" idempotency trick (see that
--      file's own step-1 comment), not a bug, but it means `outbox_id`
--      is a dangling reference by construction at the moment of this
--      INSERT.
--   2. Only after the real outbox row(s) are created (step 3 in that
--      file) does a SEPARATE `UPDATE notification_dedup_log SET
--      outbox_id = $2 WHERE dedup_key = $1` backfill the real id.
--
-- `ctx.db` at this call site is the raw pool in the common case (no
-- surrounding `withTransaction` — confirmed no such wrapper exists at or
-- above every `enqueueNotification` call site), so each of those two
-- statements commits independently. A `DEFERRABLE INITIALLY DEFERRED`
-- constraint does not help: without an enclosing transaction, each
-- single statement's own implicit transaction ends (and the constraint
-- is checked) immediately after it runs, exactly like a non-deferred
-- constraint would. Adding the FK as written today would make the very
-- first `INSERT` of every single notification (a call site used
-- throughout the whole platform) fail with a foreign-key violation.
--
-- The fix belongs in outbox.ts, not here: insert `outbox_id` as NULL in
-- step 1 (the column would need `DROP NOT NULL`, which this migration
-- could do), keep the existing step-3 UPDATE to backfill the real id
-- (already written to tolerate an update after the fact), and only then
-- add `REFERENCES notification_outbox (id) ON DELETE SET NULL` — SET
-- NULL, not CASCADE, because retention.service.ts prunes
-- `notification_outbox` and `notification_dedup_log` on two INDEPENDENT
-- 30-day schedules keyed off each table's own `created_at`
-- (retention.service.ts's own comment: dedup_log's retention is
-- deliberately "a generous multiple of the outbox's own retry/backoff
-- horizon", i.e. it is meant to be able to outlive the outbox row it
-- guards) — CASCADE would delete the dedup-key guard at the same moment
-- as the outbox row, which is exactly the case that comment says must
-- not happen.
