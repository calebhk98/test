import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import * as trust from '../../src/services/trust.service.js';
import * as message from '../../src/services/message.service.js';
import { setupTestDatabase, teardownTestDatabase, buildCtx, userActor, insertUser, insertProfile, insertPaymentMethod } from './testCtxAgentE.js';

before(async () => {
  await setupTestDatabase('trust');
});

after(async () => {
  await teardownTestDatabase();
});

// =====================================================================
// §6.1 level boundaries, every edge named in the task brief.
// =====================================================================
test('levelForScore: every §6.1 boundary is exactly right', async () => {
  const ctx = buildCtx();
  assert.equal(await trust.levelForScore(ctx, 0), 'limited');
  assert.equal(await trust.levelForScore(ctx, 39), 'limited');
  assert.equal(await trust.levelForScore(ctx, 40), 'standard');
  assert.equal(await trust.levelForScore(ctx, 69), 'standard');
  assert.equal(await trust.levelForScore(ctx, 70), 'trusted');
  assert.equal(await trust.levelForScore(ctx, 89), 'trusted');
  assert.equal(await trust.levelForScore(ctx, 90), 'elite');
  assert.equal(await trust.levelForScore(ctx, 100), 'elite');
});

test('levelForScore: clamps beyond [0,100]', async () => {
  const ctx = buildCtx();
  assert.equal(await trust.levelForScore(ctx, -50), 'limited');
  assert.equal(await trust.levelForScore(ctx, -1), 'limited');
  assert.equal(await trust.levelForScore(ctx, 101), 'elite');
  assert.equal(await trust.levelForScore(ctx, 1000), 'elite');
});

test('levelForScore: boundaries follow config, not a hardcoded table', async () => {
  const ctx = buildCtx({ actor: { type: 'admin', adminId: 'admin-1' } });
  await ctx.config.set('trust.level_standard_min', 60, 'test-admin');
  assert.equal(await trust.levelForScore(ctx, 55), 'limited');
  assert.equal(await trust.levelForScore(ctx, 60), 'standard');
});

// =====================================================================
// recalculateTrustScore: clamping and event-log reconstruction.
// =====================================================================
test('recalculateTrustScore clamps the persisted score to [0,100]', async () => {
  const ctx = buildCtx();
  const userId = await insertUser(ctx, { trustScore: 50 });

  // Push the score far below 0 with negative events.
  for (let i = 0; i < 10; i++) {
    await trust.recordTrustEvent(ctx, { userId, eventType: 'moderation_action_suspension', delta: -30 });
  }
  const low = await trust.recalculateTrustScore(ctx, userId);
  assert.equal(low.trustScore, 0);
  assert.equal(low.trustLevel, 'limited');

  // And far above 100.
  for (let i = 0; i < 20; i++) {
    await trust.recordTrustEvent(ctx, { userId, eventType: 'date_completed', delta: 20 });
  }
  const high = await trust.recalculateTrustScore(ctx, userId);
  assert.equal(high.trustScore, 100);
  assert.equal(high.trustLevel, 'elite');
});

test('recalculateTrustScore is reconstructable from the trust_events log', async () => {
  const ctx = buildCtx();
  const userId = await insertUser(ctx, { trustScore: 50, createdAt: new Date(Date.now() - 1000) });

  // Base 50 + no state factors (unverified, no profile, brand new) + events.
  await trust.recordTrustEvent(ctx, { userId, eventType: 'date_completed', delta: 12 });
  await trust.recordTrustEvent(ctx, { userId, eventType: 'no_show', delta: -7 });

  const result = await trust.recalculateTrustScore(ctx, userId);
  // 50 + 12 - 7 = 55, with no state-factor contribution for a bare-minimum account.
  assert.equal(result.trustScore, 55);

  const events = await trust.listMyTrustEvents(buildCtx({ actor: userActor(userId) }));
  assert.equal(events.items.length, 2);
  const deltaSum = events.items.reduce((sum, e) => sum + e.delta, 0);
  assert.equal(50 + deltaSum, result.trustScore, 'score must equal base plus the sum of every recorded event delta');
});

test('recalculateTrustScore: state factors (verified email/payment/profile) contribute on top of the event log', async () => {
  const ctx = buildCtx();
  const userId = await insertUser(ctx, { trustScore: 50, emailVerified: true, createdAt: new Date() });
  await insertProfile(ctx, userId, { completeness: 100 });
  await insertPaymentMethod(ctx, userId, { verified: true });

  const withState = await trust.recalculateTrustScore(ctx, userId);
  assert.ok(withState.trustScore > 50, 'verified email/payment/profile should raise the score above the neutral base');
});

// =====================================================================
// §6.3 user-facing explanation, must never leak weights.
// =====================================================================
test('getMyTrustSummary shows actionable items and recent negative events, never raw weights', async () => {
  const ctx = buildCtx();
  const userId = await insertUser(ctx, { trustScore: 50, createdAt: new Date() });
  await insertProfile(ctx, userId, { completeness: 10 });

  await trust.recordTrustEvent(ctx, { userId, eventType: 'no_show', delta: -10 });
  await trust.recalculateTrustScore(ctx, userId);

  const summary = await trust.getMyTrustSummary(buildCtx({ actor: userActor(userId) }));

  // Structural proof weights cannot leak: TrustSummary's own shape has no
  // numeric factor/weight fields at all, only these four keys exist.
  assert.deepEqual(Object.keys(summary).sort(), ['actionableImprovements', 'recentNegativeEvents', 'trustLevel', 'trustScore'].sort());

  assert.ok(summary.actionableImprovements.length > 0);
  for (const item of summary.actionableImprovements) {
    assert.equal(typeof item, 'string');
    // Static template strings only, no interpolated numbers (a weight
    // leaking in would show up as a digit in the copy).
    assert.doesNotMatch(item, /\d/);
  }
  assert.ok(summary.recentNegativeEvents.some((e) => e.includes('missed date')));
  assert.ok(summary.recentNegativeEvents.every((e) => typeof e === 'string'));
});

test('getMyTrustSummary: Elite users get no actionable improvements', async () => {
  const ctx = buildCtx();
  const userId = await insertUser(ctx, { trustScore: 95, trustLevel: 'elite', emailVerified: true, createdAt: new Date(Date.now() - 400 * 24 * 60 * 60 * 1000) });
  await insertProfile(ctx, userId, { completeness: 100 });
  await insertPaymentMethod(ctx, userId, { verified: true });
  await trust.recordTrustEvent(ctx, { userId, eventType: 'date_completed', delta: 10 });
  await trust.recalculateTrustScore(ctx, userId);

  const summary = await trust.getMyTrustSummary(buildCtx({ actor: userActor(userId) }));
  assert.equal(summary.trustLevel, 'elite');
  assert.deepEqual(summary.actionableImprovements, []);
});

// =====================================================================
// InternalTrustBreakdown is a genuinely separate, non-exposed type.
// =====================================================================
test('the internal breakdown type is structurally distinct from TrustSummary (weights never reachable from the public export)', async () => {
  const ctx = buildCtx();
  const userId = await insertUser(ctx, { trustScore: 50, createdAt: new Date() });
  const summary = await trust.getMyTrustSummary(buildCtx({ actor: userActor(userId) }));
  // TrustSummary has no 'stateFactors'/'base'/'rawScore' keys, those only
  // exist on InternalTrustBreakdown, which getMyTrustSummary never returns.
  assert.equal('stateFactors' in summary, false);
  assert.equal('base' in summary, false);
  assert.equal('rawScore' in summary, false);
});

// =====================================================================
// §6.4 capability matrix (`can`) and the §6.4 vs §12.3 precedence.
// =====================================================================
test('can(): browse and chat are always allowed at every level', async () => {
  const ctx = buildCtx();
  for (const level of ['limited', 'standard', 'trusted', 'elite'] as const) {
    assert.equal((await trust.can(ctx, 'browse', { trustLevel: level })).allowed, true);
    assert.equal((await trust.can(ctx, 'chat', { trustLevel: level })).allowed, true);
  }
});

test('can(): send_interest is allowed for everyone, flagged "limited" at Limited trust', async () => {
  const ctx = buildCtx();
  const limited = await trust.can(ctx, 'send_interest', { trustLevel: 'limited' });
  assert.equal(limited.allowed, true);
  assert.equal(limited.limited, true);

  const standard = await trust.can(ctx, 'send_interest', { trustLevel: 'standard' });
  assert.equal(standard.allowed, true);
  assert.equal(standard.limited, undefined);
});

test('can(): propose_date requires a verified payment method only at Limited trust', async () => {
  const ctx = buildCtx();
  const limitedNoPayment = await trust.can(ctx, 'propose_date', { trustLevel: 'limited' });
  assert.equal(limitedNoPayment.allowed, false);
  assert.equal(limitedNoPayment.reasonCode, 'payment_method_required');

  const limitedWithPayment = await trust.can(ctx, 'propose_date', { trustLevel: 'limited', hasVerifiedPaymentMethod: true });
  assert.equal(limitedWithPayment.allowed, true);

  const standard = await trust.can(ctx, 'propose_date', { trustLevel: 'standard' });
  assert.equal(standard.allowed, true);
});

test('can(): send_links follows the §6.4 no/warning/yes/yes table by default', async () => {
  const ctx = buildCtx();
  assert.equal((await trust.can(ctx, 'send_links', { trustLevel: 'limited' })).linkMode, 'blocked');
  assert.equal((await trust.can(ctx, 'send_links', { trustLevel: 'standard' })).linkMode, 'warn');
  assert.equal((await trust.can(ctx, 'send_links', { trustLevel: 'trusted' })).linkMode, 'clickable');
  assert.equal((await trust.can(ctx, 'send_links', { trustLevel: 'elite' })).linkMode, 'clickable');
});

test('canSendClickableLinks matches can()\'s send_links gate for a real user row', async () => {
  const ctx = buildCtx();
  const limitedUser = await insertUser(ctx, { trustLevel: 'limited' });
  const trustedUser = await insertUser(ctx, { trustLevel: 'trusted' });
  assert.equal(await trust.canSendClickableLinks(ctx, limitedUser), false);
  assert.equal(await trust.canSendClickableLinks(ctx, trustedUser), true);
});

test('§6.4 vs §12.3 precedence: linksPerHourLimitFor tracks the same trust.link_min_level boundary as send_links clickability', async () => {
  const ctx = buildCtx({ actor: { type: 'admin', adminId: 'admin-1' } });

  // Default boundary ('standard'): Limited is below it, Standard+ meets it.
  assert.equal(await trust.linksPerHourLimitFor(ctx, 'limited'), 0);
  assert.equal(await trust.linksPerHourLimitFor(ctx, 'standard'), 5);
  assert.equal((await trust.can(ctx, 'send_links', { trustLevel: 'limited' })).linkMode, 'blocked');
  assert.equal((await trust.can(ctx, 'send_links', { trustLevel: 'standard' })).linkMode, 'warn');

  // Retune the boundary to 'trusted', both the numeric per-hour bucket
  // AND the clickability gate must move together, proving they share one
  // source of truth rather than two independently-hardcoded comparisons.
  await ctx.config.set('trust.link_min_level', 'trusted', 'test-admin');
  assert.equal(await trust.linksPerHourLimitFor(ctx, 'standard'), 0, 'standard should now fall in the low-trust bucket');
  assert.equal((await trust.can(ctx, 'send_links', { trustLevel: 'standard' })).linkMode, 'blocked');
  assert.equal(await trust.linksPerHourLimitFor(ctx, 'trusted'), 5);
  assert.equal((await trust.can(ctx, 'send_links', { trustLevel: 'trusted' })).linkMode, 'warn');

  await ctx.config.set('trust.link_min_level', 'standard', 'test-admin'); // restore default for later tests in this file
});

// =====================================================================
// docs/duplication.md finding 2: message.service#linkLimitForCaller used
// to re-derive its own hardcoded 'limited' boundary instead of calling
// trust.service#linksPerHourLimitFor, so retuning trust.link_min_level
// moved link *clickability* but silently left the per-hour *send* cap
// pinned to the old boundary. Proves the fix: one config key now moves
// BOTH the numeric per-hour cap (message.service, this test) and the
// clickability gate (trust.service, tested above) together.
// =====================================================================
test('finding 2 fix: message.linkLimitForCaller equals trust.linksPerHourLimitFor for every level, at the default trust.link_min_level', async () => {
  const ctx = buildCtx({ actor: { type: 'admin', adminId: 'admin-1' } });
  for (const level of ['limited', 'standard', 'trusted', 'elite'] as const) {
    const levelCtx = buildCtx({ actor: userActor('22222222-2222-2222-2222-222222222222', level) });
    assert.equal(await message.linkLimitForCaller(levelCtx), await trust.linksPerHourLimitFor(ctx, level));
  }
});

test('finding 2 fix: retuning trust.link_min_level moves message.linkLimitForCaller in lockstep with clickability, not just the render-time gate', async () => {
  const adminCtx = buildCtx({ actor: { type: 'admin', adminId: 'admin-1' } });

  // Default boundary ('standard'): a Standard-trust user gets the
  // standard_trust cap and clickable-with-warning links. Each assertion
  // below builds a FRESH Ctx (a fresh, uncached ConfigService instance)
  // so it always reads the live config row rather than an instance-local
  // cache from before the retune, this project's ConfigService caches
  // per-instance, not globally (see config.service.ts#get).
  const standardBefore = buildCtx({ actor: userActor('33333333-3333-3333-3333-333333333333', 'standard') });
  assert.equal(await message.linkLimitForCaller(standardBefore), 5);
  assert.equal((await trust.can(adminCtx, 'send_links', { trustLevel: 'standard' })).linkMode, 'warn');

  // Retune the ONE config key. Before the fix (finding 2), this moved
  // clickability but left linkLimitForCaller's hardcoded `=== 'limited'`
  // comparison untouched, so a demoted 'standard' user could still send
  // several links per hour even though they no longer render clickable.
  await adminCtx.config.set('trust.link_min_level', 'trusted', 'test-admin');

  const standardAfter = buildCtx({ actor: userActor('33333333-3333-3333-3333-333333333333', 'standard') });
  assert.equal(
    await message.linkLimitForCaller(standardAfter),
    0,
    'a Standard-trust user demoted below the retuned trust.link_min_level must fall into the low-trust send cap too',
  );
  assert.equal((await trust.can(adminCtx, 'send_links', { trustLevel: 'standard' })).linkMode, 'blocked');

  // A 'trusted' user still meets the new, higher bar.
  const trustedAfter = buildCtx({ actor: userActor('44444444-4444-4444-4444-444444444444', 'trusted') });
  assert.equal(await message.linkLimitForCaller(trustedAfter), 5);
  assert.equal((await trust.can(adminCtx, 'send_links', { trustLevel: 'trusted' })).linkMode, 'warn');

  await adminCtx.config.set('trust.link_min_level', 'standard', 'test-admin'); // restore default
});
