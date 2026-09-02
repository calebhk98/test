/**
 * tests/support/trustFixtures.ts
 *
 * Shared abstraction for putting a test user at a specific `trust_level`,
 * used by every harness/test file this build migrated off a raw
 * `INSERT`/`UPDATE` that set `users.trust_level` directly and
 * independently of `users.trust_score`.
 *
 * WHY THIS EXISTS (see db/migrations/029_trust_invariant.sql): a prior
 * build wanted `trust_level` to be structurally impossible to disagree
 * with `trust_score` (a trigger enforcing `trust_level =
 * trust_level_for_score(trust_score)` on every write), and declined,
 * because a large number of test fixtures across the suite deliberately
 * set `trust_level` independent of `trust_score` to pin a user at a tier
 * for unrelated test setup, and the trigger would reject every one of
 * them. That decision treated the coupling as an obstacle. It is the
 * actual defect: tests should not be able to reach into `users`' internal
 * representation at all, they should ask a real API for the state they
 * need.
 *
 * `pinTrustLevel` is that real API, built entirely out of
 * `trust.service.ts`'s own OWN exported functions
 * (`recordTrustEvent`/`recalculateTrustScore`), never a raw write to
 * `trust_score`/`trust_level`. It works by:
 *
 *   1. Calling `recalculateTrustScore` once with NO fixture adjustment,
 *      to read the score `trust.service.ts` itself would derive for this
 *      user right now (base + whatever state factors the fixture already
 *      set up: verified email, profile completeness, account age, a
 *      clean-record bonus, see trust.service.ts's module doc). This
 *      makes the helper correct regardless of what else a test's fixture
 *      inserted first, it never assumes a bare score of 50.
 *   2. Computing a target score inside `level`'s CURRENT config band
 *      (read live via `ctx.config`, the same bounds
 *      `trust.service#levelForScore` itself reads, so a test that retunes
 *      `trust.level_*_min` before pinning gets the retuned band, not a
 *      hardcoded one).
 *   3. Recording exactly ONE `trust_events` row for the difference (via
 *      `recordTrustEvent`, the same function every production caller
 *      uses to move a score) and recalculating. This is slower than a
 *      raw `UPDATE`, and it is correct: the resulting row is
 *      indistinguishable, to any other code in the codebase, from a user
 *      who reached that tier through real events, and the DB's own
 *      `trust_level_for_score` (enforced by the trigger) guarantees the
 *      pair could never have disagreed in the first place.
 *
 * `insertBaseUser` is the one narrow, explicitly-named exception this
 * module keeps: no service in this codebase creates a bare `users` row
 * quickly enough for unit-test fixtures without also driving a real
 * email-verification/OTP flow (see this module's own report for the
 * `auth.service#register` alternative and why it was not adopted
 * wholesale here). It deliberately does NOT accept a `trustScore`/
 * `trustLevel` column override, callers that need a specific tier call
 * `pinTrustLevel`/`createUserAtTrustLevel` instead, which is the entire
 * point: the raw insert only ever produces the schema's own agreeing
 * default pair (`trust_score = 50`, `trust_level = 'standard'`).
 */
import { randomUUID } from 'node:crypto';
import type { Ctx } from '../../src/lib/ctx.js';
import type { TrustLevel } from '../../src/domain/types.js';
import * as trust from '../../src/services/trust.service.js';

/**
 * Event type used ONLY by this fixture helper, deliberately distinct from
 * every real `trust.TRUST_EVENT_TYPES` value (see trust.service.ts) so a
 * `trust_events` row created by a test fixture is always identifiable as
 * such in an audit trail, never mistaken for a real production signal.
 */
export const TEST_FIXTURE_TRUST_EVENT_TYPE = 'test_fixture_trust_adjustment';

interface LevelBounds {
  eliteMin: number;
  trustedMin: number;
  standardMin: number;
}

async function readLevelBounds(ctx: Ctx): Promise<LevelBounds> {
  const bounds = await ctx.config.getMany([
    'trust.level_elite_min',
    'trust.level_trusted_min',
    'trust.level_standard_min',
  ] as const);
  return {
    eliteMin: bounds['trust.level_elite_min'],
    trustedMin: bounds['trust.level_trusted_min'],
    standardMin: bounds['trust.level_standard_min'],
  };
}

/** A score safely inside `level`'s current band (not just at its edge), so a caller's later, small adjustments to state factors don't accidentally tip it into a neighboring tier. */
function targetScoreForLevel(level: TrustLevel, bounds: LevelBounds): number {
  const { eliteMin, trustedMin, standardMin } = bounds;
  switch (level) {
    case 'elite':
      return Math.min(100, eliteMin + Math.min(5, 100 - eliteMin));
    case 'trusted':
      return Math.min(Math.max(trustedMin, eliteMin - 1), trustedMin + 2);
    case 'standard':
      return Math.min(Math.max(standardMin, trustedMin - 1), standardMin + 2);
    case 'limited':
      return Math.max(0, standardMin - 5);
  }
}

/**
 * Moves `userId` to `level` by recording a `trust_events` row and letting
 * `trust.service#recalculateTrustScore` derive `trust_score`/`trust_level`
 * from it, the same production path every real trust-score change goes
 * through. Never writes `users.trust_score`/`trust_level` directly.
 *
 * Always drives the score to the SAME representative point inside
 * `level`'s band (see `targetScoreForLevel`), regardless of where the
 * user's state-factor-only baseline already sits, so the result is
 * deterministic and reproducible across runs. If that baseline already
 * happens to land exactly there, no event is recorded at all.
 */
export async function pinTrustLevel(ctx: Ctx, userId: string, level: TrustLevel): Promise<{ trustScore: number; trustLevel: TrustLevel }> {
  const baseline = await trust.recalculateTrustScore(ctx, userId);
  const bounds = await readLevelBounds(ctx);
  const target = targetScoreForLevel(level, bounds);
  const delta = target - baseline.trustScore;

  if (delta !== 0) {
    await trust.recordTrustEvent(ctx, {
      userId,
      eventType: TEST_FIXTURE_TRUST_EVENT_TYPE,
      delta,
      metadata: { reason: 'test fixture: pin trust level', targetLevel: level },
    });
  }

  const result = await trust.recalculateTrustScore(ctx, userId);
  if (result.trustLevel !== level) {
    // Only reachable if a test retuned the config bands to something that
    // makes `level` unreachable (e.g. standardMin > trustedMin). Fail
    // loudly rather than silently handing back the wrong tier.
    throw new Error(
      `pinTrustLevel: could not reach "${level}" for user ${userId}, landed at "${result.trustLevel}" ` +
        `(score ${result.trustScore}). Check the configured trust.level_*_min bounds.`,
    );
  }
  return result;
}

export interface InsertBaseUserOpts {
  id?: string;
  email?: string;
  birthdate?: string;
  status?: 'active' | 'suspended' | 'deleted';
  suspended?: boolean;
  shadowbanned?: boolean;
  emailVerified?: boolean;
  createdAt?: Date;
}

let userSeq = 0;
function uniqueEmail(prefix = 'fixture'): string {
  userSeq += 1;
  return `${prefix}-${userSeq}-${Date.now()}-${randomUUID().slice(0, 8)}@example.test`;
}

/**
 * Inserts a minimal `users` row through raw SQL (see module doc: no
 * service in this codebase creates one fast enough for unit fixtures
 * without a full auth/verification flow). Deliberately does NOT accept a
 * trust column override, the row always gets the schema's own agreeing
 * defaults (`trust_score = 50`, `trust_level = 'standard'`); call
 * `pinTrustLevel`/`createUserAtTrustLevel` for anything else.
 */
export async function insertBaseUser(ctx: Ctx, opts: InsertBaseUserOpts = {}): Promise<string> {
  const id = opts.id ?? randomUUID();
  const createdAt = opts.createdAt ?? new Date();
  await ctx.db.query(
    `INSERT INTO users (id, email, password_hash, birthdate, status, suspended, shadowbanned, email_verified_at, created_at, last_active_at)
     VALUES ($1, $2, 'x', $3, $4, $5, $6, $7, $8, $8)`,
    [
      id,
      opts.email ?? uniqueEmail(),
      opts.birthdate ?? '1990-01-01',
      opts.status ?? 'active',
      opts.suspended ?? false,
      opts.shadowbanned ?? false,
      opts.emailVerified ? createdAt : null,
      createdAt,
    ],
  );
  return id;
}

/** `insertBaseUser` + `pinTrustLevel` in one call, the common case: "give me a user at trust level X". Omit `level` (or pass `undefined`) for a plain user with whatever tier the schema's own default (`trust_score = 50` / `'standard'`) and this fixture's other state-factor opts naturally produce, no fixture-adjustment event recorded. */
export async function createUserAtTrustLevel(ctx: Ctx, level: TrustLevel | undefined, opts: InsertBaseUserOpts = {}): Promise<string> {
  const id = await insertBaseUser(ctx, opts);
  if (level) {
    await pinTrustLevel(ctx, id, level);
  }
  return id;
}
