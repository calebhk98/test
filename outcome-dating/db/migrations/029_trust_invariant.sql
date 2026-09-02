-- 029_trust_invariant.sql
--
-- Closes item 3 from db/migrations/025_integrity.sql the rest of the way:
-- `users.trust_level` is now structurally unable to disagree with
-- `users.trust_score`, on every INSERT or UPDATE, not just from the one
-- disciplined production writer (trust.service#recalculateTrustScore).
--
-- 025_integrity.sql deliberately stopped short of a trigger here, on the
-- grounds that "a wide swath of this codebase's own test fixtures...set
-- `trust_level` directly and independently of `trust_score` on purpose,
-- to pin a user at a given trust TIER for unrelated test setup" and a
-- forcing trigger would silently corrupt every one of them.
--
-- That is true, and it is not a reason to leave the invariant unenforced,
-- it is a description of the actual defect: those fixtures reach past
-- every service in this codebase straight into `users`' internal
-- representation. The fix landed in tests/support/trustFixtures.ts
-- (`pinTrustLevel`/`createUserAtTrustLevel`), which puts a user at a
-- given trust level by RECORDING TRUST EVENTS through
-- `trust.service#recordTrustEvent` and letting
-- `trust.service#recalculateTrustScore` derive the pair, the same path
-- every real trust-score change in production goes through. Every
-- fixture this build owns (tests/unit/testCtxAgentE.ts,
-- tests/unit/testCtxAgentC.ts, tests/unit/testCtxDecisions.ts,
-- tests/unit/safetyFixes.test.ts, and the individual test files that
-- called them with an independent `trustLevel`) was migrated onto it
-- before this migration was added, see the build's report for the exact
-- list and counts.
--
-- Enforcement: a BEFORE INSERT OR UPDATE trigger, not a CHECK constraint.
-- 025_integrity.sql's own comment already establishes why a CHECK (or a
-- GENERATED column) cannot express this: the band boundaries
-- (trust.level_standard_min/trusted_min/elite_min) live in
-- `config_entries` and are admin-retunable (spec Sec21), and Postgres
-- forbids both a GENERATED expression and a CHECK expression from
-- consulting another table. Only a trigger, calling the existing
-- `trust_level_for_score` SQL function (025_integrity.sql), can read the
-- live config bounds. The trigger raises SQLSTATE 23514
-- (check_violation), the same code every other constraint in this schema
-- raises, so a caller checking "was this write rejected by an integrity
-- rule" (see tests/unit/integrity.test.ts's `assertCheckViolation`, and
-- this migration's own tests/unit/trustInvariant.test.ts) does not need
-- to special-case a trigger-raised error differently from a real CHECK.
--
-- No WHEN clause narrows this to "only when trust_score/trust_level
-- actually changed": every other integrity constraint in this schema
-- (025_integrity.sql's CHECKs) already runs on every INSERT/UPDATE
-- unconditionally, and `trust_level_for_score` is a cheap STABLE lookup
-- against a handful of `config_entries` rows, consistent with that
-- existing cost profile rather than a new one.
--
-- =========================================================================
-- KNOWN CONFLICT, out of this build's ownership, NOT fixed here:
-- =========================================================================
-- `src/seed.ts` (around line 1023) inserts each seeded user's
-- `trust_score` and `trust_level` from two INDEPENDENT random draws:
--   trust_score:  randInt(45, 95)
--   trust_level:  pick(['standard', 'standard', 'trusted', 'limited', 'elite'])
-- exactly the bug class this migration exists to close, now caught in
-- the platform's own dev/demo data seeder. `tests/foundation.test.ts`'s
-- "seed runs end-to-end and produces expected data" test calls `seed()`
-- directly and will fail with a 23514 the first time a seeded user's two
-- independent draws disagree (near-certain given the draw ranges: e.g.
-- trust_score=50 with trust_level='trusted' is a same-probability outcome
-- as any other combination). src/seed.ts is outside this build's file
-- ownership (only trust.service.ts/moderation.service.ts/
-- appeal.service.ts/tests under this build's list), so it is reported
-- here rather than edited, per this repo's own established convention
-- for exactly this situation (see 025_integrity.sql's own "KNOWN
-- CONFLICT" sections for tests/unit/discovery.test.ts and
-- tests/perf/seedScaleCurve.ts, the same pattern, same reasoning).
--
-- The fix is one line, mirroring trust.service#recalculateTrustScore's
-- own fix for this exact problem: replace the independent `pick(...)`
-- trust_level draw with a SQL-side derivation from the SAME trust_score
-- value in the one INSERT statement, e.g.
--   trust_level_for_score($4)
-- in place of the current `$5` positional placeholder (dropping the
-- separate `pick([...])` call entirely), so the two columns can never
-- diverge because they are no longer two draws, they are one.

CREATE OR REPLACE FUNCTION enforce_trust_level_agrees_with_score()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF NEW.trust_level IS DISTINCT FROM trust_level_for_score(NEW.trust_score) THEN
    RAISE EXCEPTION 'users.trust_level (%) disagrees with trust_level_for_score(trust_score=%) = %, for user %',
      NEW.trust_level, NEW.trust_score, trust_level_for_score(NEW.trust_score), NEW.id
      USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trust_level_agrees_with_score ON users;

CREATE TRIGGER trust_level_agrees_with_score
  BEFORE INSERT OR UPDATE ON users
  FOR EACH ROW
  EXECUTE FUNCTION enforce_trust_level_agrees_with_score();
