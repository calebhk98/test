/**
 * tests/unit/trustInvariant.test.ts
 *
 * Proves db/migrations/029_trust_invariant.sql actually enforces what it
 * claims: `users.trust_level` can never disagree with
 * `trust_level_for_score(users.trust_score)`, on INSERT or UPDATE, from
 * ANY writer, not just trust.service.ts's own disciplined one. And proves
 * the fixture abstraction this build built to replace the raw-SQL pins
 * the trigger now rejects (`tests/support/trustFixtures.ts`) actually
 * reaches every level through the real `trust.service.ts` path.
 *
 * Self-contained (own `odate_fixture_trustinvariant` database, per this
 * build's task brief), independent of any other agent's shared test
 * harness.
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import pg from 'pg';
import { randomUUID } from 'node:crypto';
import { runMigrations } from '../../src/db/migrate.js';
import { getPool, closePool } from '../../src/db/pool.js';
import { ConfigService } from '../../src/config/config.service.js';
import { FlagsService } from '../../src/config/flags.service.js';
import { ManualClock } from '../../src/lib/time.js';
import { createSilentLogger } from '../../src/lib/logger.js';
import { FakeProcessor } from '../../src/services/payments/fake.processor.js';
import { StubMediaModerationAdapter } from '../../src/services/media/stub.adapter.js';
import type { Ctx } from '../../src/lib/ctx.js';
import * as trust from '../../src/services/trust.service.js';
import {
  insertBaseUser,
  pinTrustLevel,
  createUserAtTrustLevel,
  TEST_FIXTURE_TRUST_EVENT_TYPE,
} from '../support/trustFixtures.js';

const BASE_URL = process.env.DATABASE_URL ?? 'postgres://outcome_dating@127.0.0.1:55433/outcome_dating';
const DB_NAME_PREFIX = 'odate_fixture_trustinvariant';
const RUN_SUFFIX = randomUUID().replace(/-/g, '').slice(0, 8);

function withDbName(url: string, dbName: string): string {
  const u = new URL(url);
  u.pathname = `/${dbName}`;
  return u.toString();
}

let adminPool: pg.Pool | undefined;
let pool: pg.Pool;
let dbName: string;
let ctx: Ctx;

before(async () => {
  dbName = `${DB_NAME_PREFIX}_${RUN_SUFFIX}`;
  adminPool = new pg.Pool({ connectionString: BASE_URL });
  await adminPool.query(`DROP DATABASE IF EXISTS ${dbName}`);
  await adminPool.query(`CREATE DATABASE ${dbName}`);
  process.env.DATABASE_URL = withDbName(BASE_URL, dbName);
  await runMigrations();
  pool = getPool();

  const clock = new ManualClock(new Date('2026-02-01T12:00:00.000Z'));
  const logger = createSilentLogger();
  ctx = {
    db: pool,
    clock,
    config: new ConfigService(pool, clock, logger),
    flags: new FlagsService(pool, logger),
    logger,
    actor: { type: 'system', job: 'test' },
    payments: new FakeProcessor(),
    media: new StubMediaModerationAdapter(),
  };
});

after(async () => {
  await closePool();
  if (adminPool) {
    await adminPool.query(`DROP DATABASE IF EXISTS ${dbName}`);
    await adminPool.end();
  }
});

/** Asserts `fn` rejects with a Postgres check_violation (SQLSTATE 23514), the same code every other integrity rule in this schema raises (see db/migrations/025_integrity.sql). */
async function assertCheckViolation(fn: () => Promise<unknown>, label: string): Promise<void> {
  await assert.rejects(
    fn,
    (err: unknown) => {
      const code = (err as { code?: string }).code;
      assert.equal(code, '23514', `${label}: expected a check_violation (23514), got ${code}, ${(err as Error).message}`);
      return true;
    },
    `${label}: expected the insert/update to be rejected, but it succeeded`,
  );
}

// =========================================================================
// The invariant itself: any direct write of a disagreeing pair is rejected.
// =========================================================================

test('a direct INSERT with a disagreeing trust_score/trust_level pair is rejected', async () => {
  const id = randomUUID();
  await assertCheckViolation(
    () =>
      pool.query(
        `INSERT INTO users (id, email, password_hash, birthdate, status, trust_score, trust_level)
         VALUES ($1, $2, 'x', '1990-01-01', 'active', 50, 'elite')`, // 50 is 'standard', not 'elite', by default bands
        [id, `invariant-${id}@example.test`],
      ),
    'INSERT with score=50/level=elite',
  );
});

test('a direct UPDATE that makes the pair disagree is rejected, even on an otherwise-unrelated column change', async () => {
  const id = await insertBaseUser(ctx); // schema defaults: score 50 / level 'standard', agree
  await assertCheckViolation(
    () => pool.query(`UPDATE users SET trust_level = 'elite' WHERE id = $1`, [id]), // trust_score still 50
    'UPDATE trust_level alone to a disagreeing value',
  );
  await assertCheckViolation(
    () => pool.query(`UPDATE users SET trust_score = 95 WHERE id = $1`, [id]), // trust_level still 'standard'
    'UPDATE trust_score alone to a disagreeing value',
  );
});

test('a direct write of an AGREEING pair is accepted (the trigger does not over-reject)', async () => {
  const id = randomUUID();
  await pool.query(
    `INSERT INTO users (id, email, password_hash, birthdate, status, trust_score, trust_level)
     VALUES ($1, $2, 'x', '1990-01-01', 'active', 95, 'elite')`, // 95 >= elite_min(90) by default
    [id, `invariant-agree-${id}@example.test`],
  );
  await pool.query(`UPDATE users SET trust_score = 40, trust_level = 'standard' WHERE id = $1`, [id]); // 40 is exactly standard_min
  const { rows } = await pool.query<{ trust_score: number; trust_level: string }>('SELECT trust_score, trust_level FROM users WHERE id = $1', [id]);
  assert.equal(rows[0]!.trust_score, 40);
  assert.equal(rows[0]!.trust_level, 'standard');
});

test('trust.service#recalculateTrustScore (the one real production writer) is unaffected by the trigger', async () => {
  const id = await insertBaseUser(ctx);
  await trust.recordTrustEvent(ctx, { userId: id, eventType: 'date_completed', delta: 45 });
  const result = await trust.recalculateTrustScore(ctx, id);
  assert.equal(result.trustScore, 95);
  assert.equal(result.trustLevel, 'elite');
});

// =========================================================================
// The abstraction: pinTrustLevel/createUserAtTrustLevel reach every level
// through trust.service.ts's real path, never a raw column write.
// =========================================================================

test('pinTrustLevel reaches every trust level, and the resulting row always satisfies the trigger', async () => {
  for (const level of ['limited', 'standard', 'trusted', 'elite'] as const) {
    const id = await insertBaseUser(ctx);
    const result = await pinTrustLevel(ctx, id, level);
    assert.equal(result.trustLevel, level);

    const { rows } = await pool.query<{ trust_score: number; trust_level: string }>('SELECT trust_score, trust_level FROM users WHERE id = $1', [id]);
    assert.equal(rows[0]!.trust_level, level);
    assert.equal(await trust.levelForScore(ctx, rows[0]!.trust_score), level, 'the persisted score must itself land in the requested level\'s band');
  }
});

test('pinTrustLevel works by recording a real trust_events row, never a raw column write', async () => {
  const id = await insertBaseUser(ctx);
  const { rows: before } = await pool.query<{ count: string }>('SELECT count(*)::text AS count FROM trust_events WHERE user_id = $1', [id]);
  assert.equal(before[0]!.count, '0');

  await pinTrustLevel(ctx, id, 'trusted');

  const { rows: after } = await pool.query<{ count: string; event_type: string }>(
    'SELECT count(*)::text AS count, max(event_type) AS event_type FROM trust_events WHERE user_id = $1',
    [id],
  );
  assert.equal(after[0]!.count, '1', 'exactly one fixture-adjustment event should have been recorded');
  assert.equal(after[0]!.event_type, TEST_FIXTURE_TRUST_EVENT_TYPE);
});

test('pinTrustLevel accounts for state factors already present, rather than assuming a bare score of 50', async () => {
  const oldEnough = new Date(ctx.clock.now().getTime() - 400 * 24 * 60 * 60 * 1000);
  const id = await insertBaseUser(ctx, { emailVerified: true, createdAt: oldEnough });
  // This user already earns real state-factor weight (verified email +
  // account age + clean record) before any pinning, pinTrustLevel must
  // still land exactly on 'limited', not overshoot because it assumed a
  // bare base score.
  const result = await pinTrustLevel(ctx, id, 'limited');
  assert.equal(result.trustLevel, 'limited');
});

test('pinTrustLevel follows the CURRENT config bands, not the defaults baked in at call time', async () => {
  const adminCtx: Ctx = { ...ctx, actor: { type: 'admin', adminId: 'admin-1' } };
  await adminCtx.config.set('trust.level_trusted_min', 85, 'test-admin');

  const id = await insertBaseUser(ctx);
  const result = await pinTrustLevel(ctx, id, 'trusted');
  assert.equal(result.trustLevel, 'trusted');
  assert.ok(result.trustScore >= 85, 'must respect the retuned (higher) trusted_min, not the original default of 70');

  await adminCtx.config.set('trust.level_trusted_min', 70, 'test-admin'); // restore default for any later test file run against this db
});

test('createUserAtTrustLevel: insertBaseUser + pinTrustLevel in one call', async () => {
  const id = await createUserAtTrustLevel(ctx, 'elite');
  const { rows } = await pool.query<{ trust_level: string }>('SELECT trust_level FROM users WHERE id = $1', [id]);
  assert.equal(rows[0]!.trust_level, 'elite');
});

test('createUserAtTrustLevel: omitting level leaves the schema\'s own agreeing default untouched, no event recorded', async () => {
  const id = await createUserAtTrustLevel(ctx, undefined);
  const { rows } = await pool.query<{ trust_score: number; trust_level: string }>('SELECT trust_score, trust_level FROM users WHERE id = $1', [id]);
  assert.equal(rows[0]!.trust_score, 50);
  assert.equal(rows[0]!.trust_level, 'standard');

  const { rows: events } = await pool.query<{ count: string }>('SELECT count(*)::text AS count FROM trust_events WHERE user_id = $1', [id]);
  assert.equal(events[0]!.count, '0');
});
