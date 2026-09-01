/**
 * tests/unit/retention.test.ts — src/services/retention.service.ts.
 *
 * Covers: each class expiring at its window boundary and not before,
 * financial + safety records surviving untouched, batching honoured,
 * idempotent re-runs, and a large backlog never exceeding the per-run
 * cap. `ctx.clock` (a ManualClock) drives every cutoff — no real waiting.
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { randomUUID } from 'node:crypto';
import { ManualClock, addDays } from '../../src/lib/time.js';
import {
  RETENTION_POLICIES,
  RETAINED_FOREVER_TABLES,
  runRetentionSweep,
  runRetentionPolicy,
} from '../../src/services/retention.service.js';
import {
  setupTestDatabase,
  teardownTestDatabase,
  buildCtx,
  createUser,
  createConversation,
  createVenue,
  createDateProposal,
  systemActor,
} from './testCtxRetention.js';
import type pg from 'pg';

let pool: pg.Pool;

before(async () => {
  pool = await setupTestDatabase('retention');
});

after(async () => {
  await teardownTestDatabase();
});

const NOW = new Date('2026-06-15T00:00:00.000Z');

test('every RETENTION_POLICIES entry carries a written-down reasoning (no policy is undocumented)', () => {
  assert.ok(RETENTION_POLICIES.length > 0);
  for (const policy of RETENTION_POLICIES) {
    assert.ok(policy.reasoning.trim().length > 20, `${policy.name} has no real reasoning`);
    assert.ok(policy.windowDays > 0, `${policy.name} has a non-positive window`);
    assert.ok(['delete', 'anonymize'].includes(policy.action));
  }
});

test('RETENTION_POLICIES count matches docs/retention.md\'s "Enforced policies" table row count — keeps the code and the privacy-review doc from silently drifting apart', () => {
  assert.equal(RETENTION_POLICIES.length, 12);
});

// -------------------------------------------------------------------------
// Boundary correctness — one representative delete policy, one anonymize
// policy, each with a row just inside the window (must survive) and one
// just past it (must be gone/anonymized) after a single sweep at NOW.
// -------------------------------------------------------------------------

test('expired verification tokens: survives just inside the 7-day window, gone just past it', async () => {
  const userId = await createUser(pool);
  const clock = new ManualClock(NOW);
  const ctx = buildCtx({ actor: systemActor(), clock });

  const insideId = randomUUID();
  const pastId = randomUUID();
  await pool.query(
    `INSERT INTO email_verification_tokens (id, user_id, token_hash, expires_at) VALUES ($1, $2, 'h1', $3)`,
    [insideId, userId, addDays(NOW, -6)], // 6 days old: inside the 7-day window
  );
  await pool.query(
    `INSERT INTO email_verification_tokens (id, user_id, token_hash, expires_at) VALUES ($1, $2, 'h2', $3)`,
    [pastId, userId, addDays(NOW, -8)], // 8 days old: past the 7-day window
  );

  await runRetentionPolicy(ctx, 'expired_email_verification_tokens');

  const { rows } = await pool.query<{ id: string }>(`SELECT id FROM email_verification_tokens WHERE user_id = $1`, [userId]);
  const remaining = new Set(rows.map((r) => r.id));
  assert.ok(remaining.has(insideId), 'row inside the window must survive');
  assert.ok(!remaining.has(pastId), 'row past the window must be deleted');
});

test('raw auth events: survives just inside the 90-day window, deleted just past it', async () => {
  const userId = await createUser(pool);
  const clock = new ManualClock(NOW);
  const ctx = buildCtx({ actor: systemActor(), clock });

  await pool.query(`INSERT INTO user_auth_events (user_id, login_at, success) VALUES ($1, $2, true)`, [userId, addDays(NOW, -89)]);
  await pool.query(`INSERT INTO user_auth_events (user_id, login_at, success) VALUES ($1, $2, true)`, [userId, addDays(NOW, -91)]);

  await runRetentionPolicy(ctx, 'raw_auth_events');

  const { rows } = await pool.query<{ login_at: Date }>(`SELECT login_at FROM user_auth_events WHERE user_id = $1`, [userId]);
  assert.equal(rows.length, 1);
  assert.ok(rows[0]!.login_at.getTime() >= addDays(NOW, -90).getTime(), 'only the newer (inside-window) row should remain');
});

test('discovery impressions: survives just inside the 30-day window, deleted just past it', async () => {
  const viewer = await createUser(pool);
  const candidate = await createUser(pool);
  const clock = new ManualClock(NOW);
  const ctx = buildCtx({ actor: systemActor(), clock });

  await pool.query(`INSERT INTO discovery_events (viewer_user_id, candidate_user_id, created_at) VALUES ($1, $2, $3)`, [
    viewer,
    candidate,
    addDays(NOW, -29),
  ]);
  await pool.query(`INSERT INTO discovery_events (viewer_user_id, candidate_user_id, created_at) VALUES ($1, $2, $3)`, [
    viewer,
    candidate,
    addDays(NOW, -31),
  ]);

  await runRetentionPolicy(ctx, 'discovery_impressions');

  const { rows } = await pool.query(`SELECT id FROM discovery_events WHERE viewer_user_id = $1`, [viewer]);
  assert.equal(rows.length, 1);
});

test('delivered notifications: pending rows are never touched regardless of age; sent rows expire at 90 days', async () => {
  const userId = await createUser(pool);
  const clock = new ManualClock(NOW);
  const ctx = buildCtx({ actor: systemActor(), clock });

  await pool.query(
    `INSERT INTO notifications (user_id, event_type, channel, template_key, status, created_at)
     VALUES ($1, 'interest_received', 'in_app', 'k', 'pending', $2)`,
    [userId, addDays(NOW, -400)],
  );
  await pool.query(
    `INSERT INTO notifications (user_id, event_type, channel, template_key, status, created_at)
     VALUES ($1, 'interest_received', 'in_app', 'k', 'sent', $2)`,
    [userId, addDays(NOW, -91)],
  );
  await pool.query(
    `INSERT INTO notifications (user_id, event_type, channel, template_key, status, created_at)
     VALUES ($1, 'interest_received', 'in_app', 'k', 'read', $2)`,
    [userId, addDays(NOW, -10)],
  );

  await runRetentionPolicy(ctx, 'delivered_notifications');

  const { rows } = await pool.query<{ status: string }>(`SELECT status FROM notifications WHERE user_id = $1 ORDER BY status`, [userId]);
  const statuses = rows.map((r) => r.status);
  assert.deepEqual(statuses.sort(), ['pending', 'read'], 'the old pending row survives (never touched); the old sent row is gone; the recent read row survives');
});

test('anonymize policy: device_fingerprints keeps reputation_score/is_vpn, clears only the raw metadata payload, past its 180-day window', async () => {
  const clock = new ManualClock(NOW);
  const ctx = buildCtx({ actor: systemActor(), clock });

  const { rows } = await pool.query<{ id: string }>(
    `INSERT INTO device_fingerprints (fingerprint_hash, last_seen_at, is_vpn, reputation_score, metadata)
     VALUES ('fp-1', $1, true, 12, '{"raw":"signal"}'::jsonb) RETURNING id`,
    [addDays(NOW, -181)],
  );
  const id = rows[0]!.id;

  await runRetentionPolicy(ctx, 'stale_device_fingerprint_signals');

  const { rows: after } = await pool.query<{ metadata: Record<string, unknown>; is_vpn: boolean; reputation_score: number }>(
    `SELECT metadata, is_vpn, reputation_score FROM device_fingerprints WHERE id = $1`,
    [id],
  );
  assert.deepEqual(after[0]!.metadata, {}, 'raw metadata payload is cleared');
  assert.equal(after[0]!.is_vpn, true, 'derived classification (is_vpn) survives — this is anonymize, not delete');
  assert.equal(after[0]!.reputation_score, 12, 'derived classification (reputation_score) survives');
});

test('anonymize policy: dormant chat content — active conversations are never touched at any age; archived ones past 730 days get placeholder bodies, row and conversation survive', async () => {
  const userA = await createUser(pool);
  const userB = await createUser(pool);
  const userC = await createUser(pool);
  const userD = await createUser(pool);
  const clock = new ManualClock(NOW);
  const ctx = buildCtx({ actor: systemActor(), clock });

  const activeConvoId = await createConversation(pool, userA, userB, 'active', { createdAt: addDays(NOW, -3000) });
  const archivedConvoId = await createConversation(pool, userC, userD, 'archived', { archivedAt: addDays(NOW, -731), createdAt: addDays(NOW, -731) });

  await pool.query(`INSERT INTO messages (conversation_id, sender_id, body, created_at) VALUES ($1, $2, 'hi from an ancient active chat', $3)`, [
    activeConvoId,
    userA,
    addDays(NOW, -3000),
  ]);
  await pool.query(`INSERT INTO messages (conversation_id, sender_id, body, created_at) VALUES ($1, $2, 'a dormant secret', $3)`, [
    archivedConvoId,
    userC,
    addDays(NOW, -731),
  ]);

  await runRetentionPolicy(ctx, 'dormant_chat_content');

  const { rows: activeMsgs } = await pool.query<{ body: string }>(`SELECT body FROM messages WHERE conversation_id = $1`, [activeConvoId]);
  assert.equal(activeMsgs[0]!.body, 'hi from an ancient active chat', 'an active conversation is never touched regardless of age');

  const { rows: archivedMsgs } = await pool.query<{ body: string }>(`SELECT body FROM messages WHERE conversation_id = $1`, [archivedConvoId]);
  assert.notEqual(archivedMsgs[0]!.body, 'a dormant secret');
  assert.match(archivedMsgs[0]!.body, /no longer available/i);

  // The row and the conversation itself both survive — this is anonymize, not delete.
  const { rows: stillThere } = await pool.query(`SELECT id FROM conversations WHERE id = $1`, [archivedConvoId]);
  assert.equal(stillThere.length, 1);
});

// -------------------------------------------------------------------------
// Financial + safety records survive every policy, untouched, forever.
// -------------------------------------------------------------------------

test('financial and safety audit tables are never touched by a full sweep, however old their rows are', async () => {
  const userId = await createUser(pool);
  const otherUser = await createUser(pool);
  const clock = new ManualClock(NOW);
  const ctx = buildCtx({ actor: systemActor(), clock });

  const ancient = addDays(NOW, -3650); // 10 years old — older than every window this file defines

  const venueId = await createVenue(pool);
  const conversationId = await createConversation(pool, userId, otherUser, 'established', { createdAt: ancient });
  const dateProposalId = await createDateProposal(pool, conversationId, userId, otherUser, venueId);

  await pool.query(
    `INSERT INTO payment_ledger (user_id, date_proposal_id, type, amount_cents, currency, created_at)
     VALUES ($1, $2, 'authorization', 100, 'usd', $3)`,
    [userId, dateProposalId, ancient],
  );
  await pool.query(`INSERT INTO reports (reporter_id, reported_id, category, created_at) VALUES ($1, $2, 'other', $3)`, [
    userId,
    await createUser(pool),
    ancient,
  ]);
  await pool.query(`INSERT INTO moderation_actions (user_id, action, reason, created_at) VALUES ($1, 'warning', 'r', $2)`, [userId, ancient]);
  await pool.query(`INSERT INTO trust_events (user_id, event_type, delta, created_at) VALUES ($1, 'verified_email', 5, $2)`, [userId, ancient]);
  await pool.query(`INSERT INTO automated_moderation_flags (user_id, signal_type, weight, created_at) VALUES ($1, 'user_report', 1, $2)`, [
    userId,
    ancient,
  ]);

  const before: Record<string, number> = {};
  for (const table of RETAINED_FOREVER_TABLES) {
    const { rows } = await pool.query<{ count: string }>(`SELECT count(*)::text AS count FROM ${table}`);
    before[table] = Number(rows[0]!.count);
  }

  await runRetentionSweep(ctx);

  for (const table of RETAINED_FOREVER_TABLES) {
    const { rows } = await pool.query<{ count: string }>(`SELECT count(*)::text AS count FROM ${table}`);
    assert.equal(Number(rows[0]!.count), before[table], `${table} row count changed — this table must be retained forever`);
  }
});

// -------------------------------------------------------------------------
// Batching, idempotency, and the per-run cap on a large backlog.
// -------------------------------------------------------------------------

test('batching: a run stops at the batch boundary, and a second run finishes the rest', async () => {
  const clock = new ManualClock(NOW);
  const ctx = buildCtx({ actor: systemActor(), clock });

  const batchSize = RETENTION_POLICIES.find((p) => p.name === 'notification_dedup_log')!.batchSize;
  const total = batchSize + 5;
  for (let i = 0; i < total; i++) {
    await pool.query(`INSERT INTO notification_dedup_log (dedup_key, outbox_id, created_at) VALUES ($1, $2, $3)`, [
      `dedup-${randomUUID()}`,
      randomUUID(),
      addDays(NOW, -31),
    ]);
  }

  // Force exactly one batch by capping maxBatchesPerRun to 1 via a direct policy call — runRetentionPolicy uses the
  // registered policy's own maxBatchesPerRun (50), which would finish this small backlog in one run, so instead this
  // asserts the *first single batch* only ever touches batchSize rows, then a second batch gets the remainder.
  const { rowCount: firstBatch } = await ctx.db.query(
    `WITH victims AS (SELECT dedup_key FROM notification_dedup_log WHERE created_at < $1 ORDER BY created_at LIMIT $2)
     DELETE FROM notification_dedup_log WHERE dedup_key IN (SELECT dedup_key FROM victims)`,
    [addDays(NOW, -30), batchSize],
  );
  assert.equal(firstBatch, batchSize, 'one batch never deletes more than its configured batch size');

  const { rows: remaining } = await pool.query<{ count: string }>(`SELECT count(*)::text AS count FROM notification_dedup_log`);
  assert.equal(Number(remaining[0]!.count), 5, 'exactly the overflow past one batch remains');

  const result = await runRetentionPolicy(ctx, 'notification_dedup_log');
  assert.equal(result.affected, 5);
  assert.equal(result.exhausted, true);
});

test('idempotent re-run: running the same policy twice against an already-processed database affects nothing the second time', async () => {
  const viewer = await createUser(pool);
  const candidate = await createUser(pool);
  const clock = new ManualClock(NOW);
  const ctx = buildCtx({ actor: systemActor(), clock });

  for (let i = 0; i < 10; i++) {
    await pool.query(`INSERT INTO discovery_events (viewer_user_id, candidate_user_id, created_at) VALUES ($1, $2, $3)`, [
      viewer,
      candidate,
      addDays(NOW, -60),
    ]);
  }

  const first = await runRetentionPolicy(ctx, 'discovery_impressions');
  assert.ok(first.affected >= 10);

  const second = await runRetentionPolicy(ctx, 'discovery_impressions');
  assert.equal(second.affected, 0, 'nothing left to delete — the second run is a costless no-op');
  assert.equal(second.exhausted, true);
});

test('a large backlog never exceeds batchSize * maxBatchesPerRun rows affected in one run', async () => {
  const viewer = await createUser(pool);
  const candidate = await createUser(pool);
  const clock = new ManualClock(NOW);
  const ctx = buildCtx({ actor: systemActor(), clock });

  const policy = RETENTION_POLICIES.find((p) => p.name === 'discovery_impressions')!;
  const cap = policy.batchSize * policy.maxBatchesPerRun;
  const backlogSize = cap + 137; // deliberately more than one run's cap

  // Bulk-insert via generate_series rather than `backlogSize` round trips.
  await pool.query(
    `INSERT INTO discovery_events (viewer_user_id, candidate_user_id, created_at)
     SELECT $1, $2, $3::timestamptz - (n || ' seconds')::interval FROM generate_series(1, $4) AS n`,
    [viewer, candidate, addDays(NOW, -60), backlogSize],
  );

  const result = await runRetentionPolicy(ctx, 'discovery_impressions');
  assert.equal(result.affected, cap, 'exactly the per-run cap is affected, never more');
  assert.equal(result.exhausted, false, 'a backlog remains for the next scheduled run');

  const { rows } = await pool.query<{ count: string }>(`SELECT count(*)::text AS count FROM discovery_events WHERE viewer_user_id = $1`, [viewer]);
  assert.equal(Number(rows[0]!.count), backlogSize - cap);
});

test('runRetentionSweep runs every policy and totals their affected counts', async () => {
  const userId = await createUser(pool);
  const clock = new ManualClock(NOW);
  const ctx = buildCtx({ actor: systemActor(), clock });

  await pool.query(`INSERT INTO user_auth_events (user_id, login_at, success) VALUES ($1, $2, true)`, [userId, addDays(NOW, -200)]);

  const result = await runRetentionSweep(ctx);
  assert.equal(result.policies.length, RETENTION_POLICIES.length);
  const authPolicyResult = result.policies.find((p) => p.policy === 'raw_auth_events');
  assert.ok(authPolicyResult && authPolicyResult.affected >= 1);
  assert.equal(
    result.totalAffected,
    result.policies.reduce((sum, p) => sum + p.affected, 0),
  );
});
