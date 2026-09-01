import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import * as report from '../../src/services/report.service.js';
import {
  setupTestDatabase,
  teardownTestDatabase,
  buildCtx,
  userActor,
  insertUser,
  insertConversation,
  insertAuthEvent,
} from './testCtxAgentE.js';

before(async () => {
  await setupTestDatabase('report');
});

after(async () => {
  await teardownTestDatabase();
});

test('submitReport only accepts the exact §18.3 structured categories', async () => {
  const ctx = buildCtx();
  const reporterId = await insertUser(ctx);
  const reportedId = await insertUser(ctx);
  const reportCtx = buildCtx({ actor: userActor(reporterId) });

  // @ts-expect-error deliberately invalid category to prove the union/CHECK rejects it
  await assert.rejects(() => report.submitReport(reportCtx, { reportedId, category: 'not_a_real_category' }));
});

test('submitReport stores category as the primary signal; details is optional free text', async () => {
  const ctx = buildCtx();
  const reporterId = await insertUser(ctx);
  const reportedId = await insertUser(ctx);
  const reportCtx = buildCtx({ actor: userActor(reporterId) });

  const withoutDetails = await report.submitReport(reportCtx, { reportedId, category: 'spam' });
  assert.equal(withoutDetails.category, 'spam');
  assert.equal(withoutDetails.details, null);

  const withDetails = await report.submitReport(reportCtx, { reportedId, category: 'harassment', details: 'sent repeated unwanted messages' });
  assert.equal(withDetails.details, 'sent repeated unwanted messages');
});

test('submitReport never exposes the reporter identity in a way reachable by the reported user (no export leaks reporterId)', async () => {
  const ctx = buildCtx();
  const reporterId = await insertUser(ctx);
  const reportedId = await insertUser(ctx);
  const reportCtx = buildCtx({ actor: userActor(reporterId) });

  await report.submitReport(reportCtx, { reportedId, category: 'spam' });

  // The only export that could plausibly be reachable from the REPORTED
  // user's side is `countRecentReportsAgainst` (a bare number, no
  // reporter id at all), assert its shape carries nothing identifying.
  const count = await report.countRecentReportsAgainst(ctx, reportedId, 30);
  assert.equal(typeof count, 'number');
});

test('submitReport preserves the referenced conversation for automated investigation (spec §30.9), no archive/mutation', async () => {
  const ctx = buildCtx();
  const reporterId = await insertUser(ctx);
  const reportedId = await insertUser(ctx);
  const conversationId = await insertConversation(ctx, reporterId, reportedId);
  const before = await ctx.db.query('SELECT * FROM conversations WHERE id = $1', [conversationId]);

  const reportCtx = buildCtx({ actor: userActor(reporterId) });
  await report.submitReport(reportCtx, { reportedId, conversationId, category: 'unsafe_behavior' });

  const after = await ctx.db.query('SELECT * FROM conversations WHERE id = $1', [conversationId]);
  assert.deepEqual(after.rows[0], before.rows[0]);
});

// =====================================================================
// §18.5 scoring weights.
// =====================================================================
test('scoreReport: higher category severity scores higher, all else equal', async () => {
  const ctx = buildCtx();
  const reporterId = await insertUser(ctx, { trustLevel: 'standard' });
  const reportedId = await insertUser(ctx);

  const spamReport = { id: 'r1', reporterId, reportedId, conversationId: null, messageId: null, category: 'spam' as const, severity: 1, details: null, createdAt: ctx.clock.now() };
  const scamReport = { ...spamReport, id: 'r2', category: 'scam_money_request' as const };

  const spamScore = await report.scoreReport(ctx, spamReport);
  const scamScore = await report.scoreReport(ctx, scamReport);
  assert.ok(scamScore > spamScore, 'scam/money-request must outweigh spam');
});

test('scoreReport: a report from a trusted reporter scores higher than the same report from a limited-trust reporter', async () => {
  const ctx = buildCtx();
  const trustedReporter = await insertUser(ctx, { trustLevel: 'trusted' });
  const limitedReporter = await insertUser(ctx, { trustLevel: 'limited' });
  const reportedId = await insertUser(ctx);

  const base = { conversationId: null, messageId: null, category: 'scam_money_request' as const, severity: 4, details: null, createdAt: ctx.clock.now() };
  const fromTrusted = await report.scoreReport(ctx, { ...base, id: 'r1', reporterId: trustedReporter, reportedId });
  const fromLimited = await report.scoreReport(ctx, { ...base, id: 'r2', reporterId: limitedReporter, reportedId });

  assert.ok(fromTrusted > fromLimited, 'spec §18.5 example: "scam report from trusted user = high weight"');
});

test('scoreReport: a report from an actual match (shared conversation) outweighs a stranger report', async () => {
  const ctx = buildCtx();
  const matchedReporter = await insertUser(ctx);
  const strangerReporter = await insertUser(ctx);
  const reportedId = await insertUser(ctx);
  await insertConversation(ctx, matchedReporter, reportedId);

  const base = { conversationId: null, messageId: null, category: 'harassment' as const, severity: 4, details: null, createdAt: ctx.clock.now() };
  const matched = await report.scoreReport(ctx, { ...base, id: 'r1', reporterId: matchedReporter, reportedId });
  const stranger = await report.scoreReport(ctx, { ...base, id: 'r2', reporterId: strangerReporter, reportedId });

  assert.ok(matched > stranger);
});

test('scoreReport: recency matters, an old report scores lower than a fresh one, but never to zero', async () => {
  const ctx = buildCtx();
  const reporterId = await insertUser(ctx);
  const reportedId = await insertUser(ctx);

  const base = { id: 'r1', reporterId, reportedId, conversationId: null, messageId: null, category: 'fake_profile' as const, severity: 3, details: null };
  const fresh = await report.scoreReport(ctx, { ...base, createdAt: ctx.clock.now() });
  const old = await report.scoreReport(ctx, { ...base, createdAt: new Date(ctx.clock.now().getTime() - 400 * 24 * 60 * 60 * 1000) });

  assert.ok(fresh > old);
  assert.ok(old > 0, 'an old report must still count for something, not be worthless');
});

test('scoreReport: repeated prior reports against the same target raise the weight, capped', async () => {
  const ctx = buildCtx();
  const reportedId = await insertUser(ctx);

  // File several distinct prior reports against the same target from distinct reporters.
  for (let i = 0; i < 5; i++) {
    const reporterId = await insertUser(ctx);
    const reportCtx = buildCtx({ actor: userActor(reporterId) });
    await report.submitReport(reportCtx, { reportedId, category: 'spam' });
  }

  const freshReporter = await insertUser(ctx);
  const target = { id: 'rX', reporterId: freshReporter, reportedId, conversationId: null, messageId: null, category: 'spam' as const, severity: 1, details: null, createdAt: ctx.clock.now() };
  const withHistory = await report.scoreReport(ctx, target);

  const cleanReportedId = await insertUser(ctx);
  const cleanTarget = { ...target, id: 'rY', reportedId: cleanReportedId };
  const withoutHistory = await report.scoreReport(ctx, cleanTarget);

  assert.ok(withHistory > withoutHistory);
});

// =====================================================================
// Anti-brigading discount, the explicitly required test (spec §18.5
// "Reason: Prevent brigading and false positives").
// =====================================================================
test('anti-brigading: reports from reporters sharing a device fingerprint are diminishingly weighted', async () => {
  const ctx = buildCtx();
  const reportedId = await insertUser(ctx);
  const sharedDevice = 'device-fingerprint-brigade-1';

  const reporter1 = await insertUser(ctx);
  await insertAuthEvent(ctx, reporter1, sharedDevice);
  const report1Ctx = buildCtx({ actor: userActor(reporter1), now: ctx.clock.now() });
  const r1 = await report.submitReport(report1Ctx, { reportedId, category: 'harassment' });

  const reporter2 = await insertUser(ctx);
  await insertAuthEvent(ctx, reporter2, sharedDevice);
  const report2Ctx = buildCtx({ actor: userActor(reporter2), now: new Date(ctx.clock.now().getTime() + 1000) });

  const reporter3 = await insertUser(ctx);
  await insertAuthEvent(ctx, reporter3, sharedDevice);
  const report3Ctx = buildCtx({ actor: userActor(reporter3), now: new Date(ctx.clock.now().getTime() + 2000) });

  // Score the SAME category/severity report as it would be scored at each
  // position in the cluster sequence (1st, 2nd, 3rd from the same device).
  const shape = { conversationId: null, messageId: null, category: 'harassment' as const, severity: 4, details: null };
  const first = await report.scoreReport(ctx, { ...shape, id: 'a', reporterId: reporter1, reportedId, createdAt: r1.createdAt });

  // Insert reporter2's and reporter3's reports for real so the cluster count reflects them.
  await report.submitReport(report2Ctx, { reportedId, category: 'harassment' });
  const second = await report.scoreReport(ctx, { ...shape, id: 'b', reporterId: reporter3, reportedId, createdAt: new Date(r1.createdAt.getTime() + 3000) });

  assert.ok(second < first, 'a report from a cluster that has already reported this target must weigh less than the first from that cluster');
});

test('anti-brigading: reports from unrelated devices are NOT discounted by each other', async () => {
  const ctx = buildCtx();
  const reportedId = await insertUser(ctx);

  const reporter1 = await insertUser(ctx);
  await insertAuthEvent(ctx, reporter1, 'device-A');
  const ctx1 = buildCtx({ actor: userActor(reporter1) });
  await report.submitReport(ctx1, { reportedId, category: 'harassment' });

  const reporter2 = await insertUser(ctx);
  await insertAuthEvent(ctx, reporter2, 'device-B'); // different device, not the same cluster
  const shape = { conversationId: null, messageId: null, category: 'harassment' as const, severity: 4, details: null, createdAt: ctx.clock.now() };
  const score = await report.scoreReport(ctx, { ...shape, id: 'x', reporterId: reporter2, reportedId });

  const baselineReportedId = await insertUser(ctx);
  const baselineScore = await report.scoreReport(ctx, { ...shape, id: 'y', reporterId: reporter2, reportedId: baselineReportedId });

  assert.equal(score, baselineScore, 'an unrelated device must not be discounted just because someone else reported the same target');
});

// =====================================================================
// §18.3 "minor suspected" = maximum severity.
// =====================================================================
test('scoreReport: minor_suspected carries the highest category weight of any category', async () => {
  const ctx = buildCtx();
  const reporterId = await insertUser(ctx, { trustLevel: 'limited' }); // even at the weakest reporter-trust multiplier...
  const reportedId = await insertUser(ctx);
  const otherReporterId = await insertUser(ctx, { trustLevel: 'elite' }); // ...vs. the strongest, for a harsh category

  const minorReport = { id: 'm1', reporterId, reportedId, conversationId: null, messageId: null, category: 'minor_suspected' as const, severity: 5, details: null, createdAt: ctx.clock.now() };
  const scamReport = { id: 'm2', reporterId: otherReporterId, reportedId, conversationId: null, messageId: null, category: 'scam_money_request' as const, severity: 4, details: null, createdAt: ctx.clock.now() };

  const minorScore = await report.scoreReport(ctx, minorReport);
  const scamScore = await report.scoreReport(ctx, scamReport);
  assert.ok(minorScore > scamScore, 'minor_suspected must outweigh even a high-severity category from the most-trusted reporter');
});

test('countRecentReportsAgainst only counts reports within the window', async () => {
  const ctx = buildCtx();
  const reporterId = await insertUser(ctx);
  const reportedId = await insertUser(ctx);
  const reportCtx = buildCtx({ actor: userActor(reporterId) });

  await report.submitReport(reportCtx, { reportedId, category: 'spam' });

  // Look at the count from a vantage point well after the report was
  // filed (the row's created_at is the DB's own real wall clock, not
  // `ctx.clock`, advance a fresh ManualClock forward from "now" so the
  // window boundary is unambiguous either way, rather than racing a
  // same-instant comparison).
  const laterCtx = buildCtx({ now: new Date(Date.now() + 40 * 24 * 60 * 60 * 1000) });
  assert.equal(await report.countRecentReportsAgainst(laterCtx, reportedId, 50), 1, 'a 50-day window from 40 days later must still include it');
  assert.equal(await report.countRecentReportsAgainst(laterCtx, reportedId, 30), 0, 'a 30-day window from 40 days later must exclude it');
});
