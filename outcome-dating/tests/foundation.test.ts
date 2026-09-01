/**
 * Foundation smoke test.
 *
 * Boots the local dev Postgres (assumes `scripts/pg-dev.sh start` has
 * already been run — see package.json `pretest`-free `test` script;
 * CI/dev should run `npm run pg:start && npm run test`), runs migrations
 * against a dedicated `outcome_dating_test` database, seeds it, and
 * asserts:
 *   1. migrations apply cleanly and are idempotent,
 *   2. the config service returns every §21.4 default,
 *   3. `snapshotPolicy` is stable — two calls with no config change in
 *      between return deep-equal objects, and a subsequent `set` does NOT
 *      retroactively change an already-captured snapshot,
 *   4. the seed module runs end-to-end and produces the expected row
 *      counts.
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import pg from 'pg';
import { randomUUID } from 'node:crypto';
import { runMigrations } from '../src/db/migrate.js';
import { closePool } from '../src/db/pool.js';
import { ConfigService, CONFIG_DEFAULTS, DATE_PROPOSAL_POLICY_KEYS, INTEREST_POLICY_KEYS } from '../src/config/config.service.js';
import { FlagsService, KNOWN_FLAGS } from '../src/config/flags.service.js';
import { SystemClock } from '../src/lib/time.js';
import { createSilentLogger } from '../src/lib/logger.js';
import { seed } from '../src/seed.js';

const BASE_URL = process.env.DATABASE_URL ?? 'postgres://outcome_dating@127.0.0.1:55433/outcome_dating';
// A bare, un-namespaced `outcome_dating_test` was the worst-exposed name
// in the whole suite for the cross-run database race (test-audit.md's
// database-race item): every harness in this repo computes its database
// name deterministically, so two overlapping `npm test` runs (this repo's
// suite is routinely run by more than one agent at once against the same
// shared dev Postgres cluster on port 55433) would DROP a database the
// other still had a live connection to. Folding a fresh per-process
// random id into the name removes the collision at its root.
const RUN_SUFFIX = randomUUID().replace(/-/g, '').slice(0, 8);
const TEST_DB_NAME = `outcome_dating_test_${RUN_SUFFIX}`;

function withDbName(url: string, dbName: string): string {
  const u = new URL(url);
  u.pathname = `/${dbName}`;
  return u.toString();
}

const TEST_DATABASE_URL = withDbName(BASE_URL, TEST_DB_NAME);

let adminPool: pg.Pool;
let pool: pg.Pool;

before(async () => {
  // Connect to the default admin DB to (re)create a clean test database.
  adminPool = new pg.Pool({ connectionString: BASE_URL });
  await adminPool.query(`DROP DATABASE IF EXISTS ${TEST_DB_NAME}`);
  await adminPool.query(`CREATE DATABASE ${TEST_DB_NAME}`);

  process.env.DATABASE_URL = TEST_DATABASE_URL;
  pool = new pg.Pool({ connectionString: TEST_DATABASE_URL });
});

after(async () => {
  await pool.end();
  // `runMigrations`/`seed` use the shared singleton pool (src/db/pool.ts),
  // which by now holds open connections to the test DB — close it too, or
  // DROP DATABASE below fails with "being accessed by other users".
  await closePool();
  await adminPool.query(`DROP DATABASE IF EXISTS ${TEST_DB_NAME}`);
  await adminPool.end();
});

test('migrations apply cleanly and are idempotent', async () => {
  const first = await runMigrations();
  assert.ok(first.applied.includes('001_init.sql'));

  const second = await runMigrations();
  assert.deepEqual(second.applied, []);

  const { rows } = await pool.query<{ count: string }>(
    `SELECT count(*)::text AS count FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE'`,
  );
  // 26 spec tables + implied tables (venue_staff, admin_users,
  // admin_audit_log, notifications, post_date_feedback, blocks, appeals,
  // device_fingerprints, compatibility_scores, date_attendance_confirmations,
  // payment_methods) + schema_migrations.
  assert.ok(Number(rows[0]!.count) >= 26 + 1, `expected at least 27 tables, got ${rows[0]!.count}`);
});

test('config service returns every §21.4 default', async () => {
  const config = new ConfigService(pool, new SystemClock(), createSilentLogger());

  assert.equal(await config.get('interest.outgoing_pending_limit'), 5);
  assert.equal(await config.get('interest.incoming_pending_limit'), 10);
  assert.equal(await config.get('interest.expiry_hours'), 48);
  assert.equal(await config.get('chat.active_limit'), 15);
  assert.equal(await config.get('chat.date_prompt_hours'), 72);
  assert.equal(await config.get('chat.pre_date_archive_days'), 21);
  assert.equal(await config.get('date.escrow_amount_cents'), 2000);
  assert.equal(await config.get('date.accept_expiry_hours'), 48);
  assert.equal(await config.get('date.full_refund_cutoff_hours'), 24);
  assert.equal(await config.get('date.late_cancel_refund_percent'), 0);
  assert.equal(await config.get('moderation.auto_restriction_score'), 50);
  assert.equal(await config.get('moderation.auto_shadowban_score'), 80);
  assert.equal(await config.get('trust.link_min_level'), 'standard');

  // No row exists yet for any key — `get` must fall back to the registry
  // default rather than throwing or returning undefined.
  for (const [key, value] of Object.entries(CONFIG_DEFAULTS)) {
    assert.equal(await config.get(key as keyof typeof CONFIG_DEFAULTS), value, `default mismatch for ${key}`);
  }
});

test('policy snapshot is stable and does not retroactively change', async () => {
  const config = new ConfigService(pool, new SystemClock(), createSilentLogger());

  const snapshotA = await config.snapshotPolicy(INTEREST_POLICY_KEYS);
  const snapshotB = await config.snapshotPolicy(INTEREST_POLICY_KEYS);
  assert.deepEqual(snapshotA, snapshotB);
  assert.deepEqual(snapshotA, {
    'interest.expiry_hours': 48,
    'interest.outgoing_pending_limit': 5,
    'interest.incoming_pending_limit': 10,
  });

  const dateSnapshotBefore = await config.snapshotPolicy(DATE_PROPOSAL_POLICY_KEYS);
  assert.equal(dateSnapshotBefore['date.escrow_amount_cents'], 2000);

  // Changing a 'snapshot'-scope key (spec §21.4 "existing proposals keep
  // original") must not alter an already-captured snapshot object.
  await config.set('date.escrow_amount_cents', 2500, 'test-admin');
  assert.equal(dateSnapshotBefore['date.escrow_amount_cents'], 2000, 'already-captured snapshot must not mutate');

  const dateSnapshotAfter = await config.snapshotPolicy(DATE_PROPOSAL_POLICY_KEYS);
  assert.equal(dateSnapshotAfter['date.escrow_amount_cents'], 2500, 'a *new* snapshot must see the updated live value');
});

test('feature flags service resolves deterministically per user', async () => {
  const flags = new FlagsService(pool, createSilentLogger());
  await flags.seedKnownFlags();

  const offByDefault = await flags.isEnabled(KNOWN_FLAGS.PHOTO_AB_TESTING, { userId: 'user-1' });
  assert.equal(offByDefault, false);

  await flags.setFlag(KNOWN_FLAGS.PHOTO_AB_TESTING, { enabled: true, rolloutPercent: 50 });

  const results = new Set<boolean>();
  for (let i = 0; i < 25; i++) {
    results.add(await flags.isEnabled(KNOWN_FLAGS.PHOTO_AB_TESTING, { userId: `user-${i}` }));
  }
  // With 25 distinct users at a 50% rollout, expect a mix of true/false
  // (not all-or-nothing) — proves bucketing is actually per-user, not a
  // single coin flip for the whole flag.
  assert.ok(results.has(true) && results.has(false), 'expected a mix of enabled/disabled across users at 50% rollout');

  // Determinism: same (flag, user) always resolves the same way.
  const firstCall = await flags.isEnabled(KNOWN_FLAGS.PHOTO_AB_TESTING, { userId: 'stable-user' });
  for (let i = 0; i < 5; i++) {
    const repeat = await flags.isEnabled(KNOWN_FLAGS.PHOTO_AB_TESTING, { userId: 'stable-user' });
    assert.equal(repeat, firstCall);
  }
});

test('seed runs end-to-end and produces expected data', async () => {
  await seed();

  const counts = await pool.query<{ users: string; questions: string; venues: string; tags: string }>(`
    SELECT
      (SELECT count(*) FROM users)::text AS users,
      (SELECT count(*) FROM questions)::text AS questions,
      (SELECT count(*) FROM venues)::text AS venues,
      (SELECT count(*) FROM interest_tags)::text AS tags
  `);
  const row = counts.rows[0]!;
  assert.equal(Number(row.users), 20);
  assert.ok(Number(row.questions) >= 25, `expected at least 25 questions, got ${row.questions}`);
  assert.equal(Number(row.venues), 8);
  assert.ok(Number(row.tags) >= 1);

  const { rows: categoryRows } = await pool.query<{ category: string }>('SELECT DISTINCT category FROM venues');
  const categories = new Set(categoryRows.map((r) => r.category));
  assert.ok(categories.size >= 5, 'seed venues should span multiple §13.2 categories');
});
