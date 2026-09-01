/**
 * Decision-layer config/gap-closing unit tests: the 8 new config keys
 * (see docs/conformance.md and the final report), their wiring into the
 * services that used to carry local fallback constants, and the
 * VOUCHER_QR_SECRET key-separation addition.
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { ConfigKeyRegistry, CONFIG_DEFAULTS, DATE_PROPOSAL_POLICY_KEYS } from '../../src/config/config.service.js';
import { getEnv, _resetEnvCacheForTests } from '../../src/config/env.js';
import { sign, verify, InvalidSignatureError } from '../../src/lib/signing.js';
import * as compatibilityService from '../../src/services/compatibility.service.js';
import * as discoveryService from '../../src/services/discovery.service.js';
import * as trustService from '../../src/services/trust.service.js';
import * as interestService from '../../src/services/interest.service.js';
import * as conversationService from '../../src/services/conversation.service.js';
import { RateLimitError } from '../../src/lib/errors.js';
import {
  setupTestDb,
  teardownTestDb,
  makeCtx,
  userActor,
  createUser,
  type TestDb,
} from './testCtxDecisions.js';

// =====================================================================
// Registry shape (no DB needed).
// =====================================================================

test('ConfigKeyRegistry: the 8 decision-layer keys exist with the specified defaults', () => {
  assert.equal(CONFIG_DEFAULTS['chat.cooling_days'], 14);
  assert.equal(CONFIG_DEFAULTS['compatibility.min_shared_questions'], 3);
  assert.equal(CONFIG_DEFAULTS['compatibility.no_data_default_score'], 0);
  assert.equal(CONFIG_DEFAULTS['discovery.min_profile_completeness'], 50);
  assert.equal(CONFIG_DEFAULTS['interest.outgoing_pending_limit_limited_tier'], 2);
  assert.equal(CONFIG_DEFAULTS['trust.expose_raw_score'], false);
  assert.equal(CONFIG_DEFAULTS['date.no_scan_confirmation_hours'], 72);
  assert.equal(CONFIG_DEFAULTS['date.dispute_auto_resolve_hours'], 72);
});

test('ConfigKeyRegistry: date.dispute_auto_resolve_hours is a snapshot-scope key included in DATE_PROPOSAL_POLICY_KEYS', () => {
  assert.equal(ConfigKeyRegistry['date.dispute_auto_resolve_hours'].scope, 'snapshot');
  assert.ok(DATE_PROPOSAL_POLICY_KEYS.includes('date.dispute_auto_resolve_hours'));
});

// =====================================================================
// VOUCHER_QR_SECRET — key separation from AUTH_TOKEN_SECRET.
// =====================================================================

test('VOUCHER_QR_SECRET: when set, it is a genuinely different secret from AUTH_TOKEN_SECRET — a token signed with one does not verify against the other', () => {
  const savedAuth = process.env.AUTH_TOKEN_SECRET;
  const savedVoucher = process.env.VOUCHER_QR_SECRET;
  try {
    process.env.AUTH_TOKEN_SECRET = 'decision-test-auth-secret';
    process.env.VOUCHER_QR_SECRET = 'decision-test-voucher-secret';
    _resetEnvCacheForTests();
    const env = getEnv();
    assert.equal(env.AUTH_TOKEN_SECRET, 'decision-test-auth-secret');
    assert.equal(env.VOUCHER_QR_SECRET, 'decision-test-voucher-secret');

    const signedWithAuth = sign({ hello: 'world' }, env.AUTH_TOKEN_SECRET);
    assert.throws(() => verify(signedWithAuth.compact, env.VOUCHER_QR_SECRET!), InvalidSignatureError);

    const signedWithVoucher = sign({ hello: 'world' }, env.VOUCHER_QR_SECRET!);
    assert.deepEqual(verify(signedWithVoucher.compact, env.VOUCHER_QR_SECRET!), { hello: 'world' });
    assert.throws(() => verify(signedWithVoucher.compact, env.AUTH_TOKEN_SECRET), InvalidSignatureError);
  } finally {
    if (savedAuth === undefined) delete process.env.AUTH_TOKEN_SECRET;
    else process.env.AUTH_TOKEN_SECRET = savedAuth;
    if (savedVoucher === undefined) delete process.env.VOUCHER_QR_SECRET;
    else process.env.VOUCHER_QR_SECRET = savedVoucher;
    _resetEnvCacheForTests();
  }
});

test('VOUCHER_QR_SECRET: unset by default, so dev/test keeps working without it', () => {
  const savedVoucher = process.env.VOUCHER_QR_SECRET;
  try {
    delete process.env.VOUCHER_QR_SECRET;
    _resetEnvCacheForTests();
    assert.equal(getEnv().VOUCHER_QR_SECRET, undefined);
  } finally {
    if (savedVoucher === undefined) delete process.env.VOUCHER_QR_SECRET;
    else process.env.VOUCHER_QR_SECRET = savedVoucher;
    _resetEnvCacheForTests();
  }
});

// =====================================================================
// DB-backed wiring checks.
// =====================================================================

let db: TestDb;

before(async () => {
  db = await setupTestDb('config');
});

after(async () => {
  await teardownTestDb(db);
});

test('trust.expose_raw_score: shouldExposeRawTrustScore reflects the config value, default false', async () => {
  const ctx = makeCtx(db, userActor(await createUser(db)));
  assert.equal(await trustService.shouldExposeRawTrustScore(ctx), false);
  await db.config.set('trust.expose_raw_score', true, 'test-admin');
  assert.equal(await trustService.shouldExposeRawTrustScore(ctx), true);
  await db.config.set('trust.expose_raw_score', false, 'test-admin');
});

test('discovery.min_profile_completeness: raising the config threshold excludes a previously-visible profile', async () => {
  const viewerId = await createUser(db);
  const candidateId = await createUser(db);
  await db.pool.query(
    `INSERT INTO profiles (user_id, display_name, bio, age, gender, seeking, relationship_intention, profile_completeness)
     VALUES ($1, 'Candidate', 'bio', 25, 'nonbinary', 'everyone', 'long_term', 60)`,
    [candidateId],
  );
  await db.pool.query(
    `INSERT INTO user_photos (user_id, image_url, is_primary, moderation_status, face_detected)
     VALUES ($1, 'https://example.test/photo.jpg', true, 'approved', true)`,
    [candidateId],
  );

  const ctx = makeCtx(db, userActor(viewerId));
  assert.equal(await discoveryService.isProfileVisibleTo(ctx, viewerId, candidateId), true, 'default threshold (50) — a 60-complete profile is visible');

  await db.config.set('discovery.min_profile_completeness', 70, 'test-admin');
  assert.equal(await discoveryService.isProfileVisibleTo(ctx, viewerId, candidateId), false, 'raised threshold (70) — the same profile is now excluded');

  await db.config.set('discovery.min_profile_completeness', 50, 'test-admin'); // restore default
});

test('compatibility.no_data_default_score: config controls the score assigned when too few shared questions exist', async () => {
  const userAId = await createUser(db);
  const userBId = await createUser(db);
  // No answers at all -> definitely below compatibility.min_shared_questions (default 3).

  const defaultScore = await compatibilityService.getScore(makeCtx(db, userActor(userAId)), userAId, userBId);
  assert.equal(defaultScore, 0, 'default compatibility.no_data_default_score is 0');

  await db.config.set('compatibility.no_data_default_score', 0.5, 'test-admin');
  const configuredScore = await compatibilityService.getScore(makeCtx(db, userActor(userAId)), userAId, userBId);
  assert.equal(configuredScore, 0.5, 'getScore now reads the configured no-data default');

  await db.config.set('compatibility.no_data_default_score', 0, 'test-admin'); // restore default
});

test('chat.cooling_days: config controls when an aging, date-proposal-free conversation moves to cooling', async () => {
  const userAId = await createUser(db);
  const userBId = await createUser(db);
  const [a, b] = userAId < userBId ? [userAId, userBId] : [userBId, userAId];
  const { rows } = await db.pool.query<{ id: string }>(
    `INSERT INTO conversations (user_a_id, user_b_id, status, created_at) VALUES ($1, $2, 'active', $3) RETURNING id`,
    [a, b, db.clock.now()],
  );
  const conversationId = rows[0]!.id;
  await db.pool.query(`INSERT INTO messages (conversation_id, sender_id, body, created_at) VALUES ($1, $2, 'hi', $3)`, [
    conversationId,
    a,
    db.clock.now(),
  ]);

  await db.config.set('chat.cooling_days', 1, 'test-admin');
  db.clock.advanceHours(25); // just past 1 day
  const ctx = makeCtx(db, userActor(a));
  const result = await conversationService.runChatDecayJob(ctx);
  assert.ok(result.cooled >= 1);

  const { rows: convRows } = await db.pool.query<{ status: string }>('SELECT status FROM conversations WHERE id = $1', [conversationId]);
  assert.equal(convRows[0]!.status, 'cooling');

  await db.config.set('chat.cooling_days', 14, 'test-admin'); // restore default
});

test('interest.outgoing_pending_limit_limited_tier: a Limited-trust sender hits a lower outgoing cap than a Standard-trust sender', async () => {
  const limitedSenderId = await createUser(db);
  await db.pool.query(`UPDATE users SET trust_level = 'limited' WHERE id = $1`, [limitedSenderId]);
  const standardSenderId = await createUser(db);

  const limitedCtx = makeCtx(db, userActor(limitedSenderId, 'limited'));
  const standardCtx = makeCtx(db, userActor(standardSenderId, 'standard'));

  // Send 2 (the Limited-tier default cap) — both should succeed.
  for (let i = 0; i < 2; i++) {
    await interestService.sendInterest(limitedCtx, await createUser(db));
    await interestService.sendInterest(standardCtx, await createUser(db));
  }
  // 3rd for the Limited sender is rejected; the Standard sender still has headroom (cap 5).
  const anotherRecipientId = await createUser(db);
  await assert.rejects(() => interestService.sendInterest(limitedCtx, anotherRecipientId), RateLimitError);
  await interestService.sendInterest(standardCtx, await createUser(db)); // 3rd — fine for Standard
});
