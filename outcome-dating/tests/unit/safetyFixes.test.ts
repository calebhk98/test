/**
 * tests/unit/safetyFixes.test.ts, SAF-1 (minor_suspected corroboration)
 * and SAF-6 (multi-signal anti-brigading) proofs, per docs/risk-review.md.
 *
 * Self-contained: this file owns its OWN dedicated Postgres database
 * (`odate_safety_safetyfixes`, per the build brief's "use your own
 * Postgres databases odate_safety_<suite>" instruction) rather than
 * sharing `tests/unit/testCtxAgentE.ts`'s `odate_agent_e_*` databases, so
 * it never races another suite for a DROP/CREATE DATABASE lock.
 *
 * Required proof, both directions (see moderation.service.ts's and
 * report.service.ts's "SAF-1 FIX" / anti-brigading module docs for the
 * full model these tests exercise):
 *   - a lone, uncorroborated, low-credibility report must NOT suspend;
 *   - a corroborated / high-credibility signal must still act fast.
 * Plus the SAF-6 requirement: varying only the client-supplied device
 * fingerprint per report must not evade the anti-brigading discount.
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
import type { Actor, Ctx } from '../../src/lib/ctx.js';
import type { TrustLevel } from '../../src/domain/types.js';
import * as report from '../../src/services/report.service.js';
import * as moderation from '../../src/services/moderation.service.js';
import { ForbiddenError } from '../../src/lib/errors.js';
import { pinTrustLevel } from '../support/trustFixtures.js';

// ---------------------------------------------------------------------
// Self-contained DB/ctx setup (see module doc, deliberately NOT shared
// with any other agent's test helper file).
// ---------------------------------------------------------------------

const BASE_URL = process.env.DATABASE_URL ?? 'postgres://outcome_dating@127.0.0.1:55433/outcome_dating';
const DB_NAME = 'odate_safety_safetyfixes';

function withDbName(url: string, dbName: string): string {
  const u = new URL(url);
  u.pathname = `/${dbName}`;
  return u.toString();
}

let adminPool: pg.Pool | undefined;
let testPool: pg.Pool | undefined;

before(async () => {
  adminPool = new pg.Pool({ connectionString: BASE_URL });
  await adminPool.query(`SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = $1 AND pid <> pg_backend_pid()`, [DB_NAME]);
  await adminPool.query(`DROP DATABASE IF EXISTS ${DB_NAME}`);
  await adminPool.query(`CREATE DATABASE ${DB_NAME}`);
  process.env.DATABASE_URL = withDbName(BASE_URL, DB_NAME);
  await runMigrations();
  testPool = getPool();
});

after(async () => {
  await closePool();
  if (adminPool) {
    await adminPool.query(`DROP DATABASE IF EXISTS ${DB_NAME}`);
    await adminPool.end();
  }
});

function getTestPool(): pg.Pool {
  if (!testPool) throw new Error('DB not set up yet');
  return testPool;
}

function buildCtx(opts: { actor?: Actor; now?: Date } = {}): Ctx {
  const pool = getTestPool();
  const clock = new ManualClock(opts.now ?? new Date());
  const logger = createSilentLogger();
  return {
    db: pool,
    clock,
    config: new ConfigService(pool, clock, logger),
    flags: new FlagsService(pool, logger),
    logger,
    actor: opts.actor ?? { type: 'system', job: 'test' },
    payments: new FakeProcessor(),
    media: new StubMediaModerationAdapter(),
  };
}

function userActor(userId: string, trustLevel: TrustLevel = 'standard'): Actor {
  return { type: 'user', userId, trustLevel };
}

let emailCounter = 0;
function uniqueEmail(): string {
  emailCounter += 1;
  return `safety${emailCounter}.${Date.now()}@example.test`;
}

/**
 * `trustLevel`, if given, is NOT written to the row directly (see
 * db/migrations/029_trust_invariant.sql, which rejects a `trust_level`
 * that disagrees with `trust_level_for_score(trust_score)`). Instead it's
 * reached via `tests/support/trustFixtures.ts#pinTrustLevel`, recording a
 * real `trust_events` row and recalculating through `trust.service.ts`'s
 * own production path.
 */
async function insertUser(
  ctx: Ctx,
  opts: { trustLevel?: TrustLevel; createdAt?: Date } = {},
): Promise<string> {
  const id = randomUUID();
  await ctx.db.query(
    `INSERT INTO users (id, email, password_hash, birthdate, status, created_at, last_active_at)
     VALUES ($1, $2, 'x', '1990-01-01', 'active', $3, $3)`,
    [id, uniqueEmail(), opts.createdAt ?? new Date()],
  );
  if (opts.trustLevel) {
    await pinTrustLevel(ctx, id, opts.trustLevel);
  }
  return id;
}

async function insertAuthEvent(ctx: Ctx, userId: string, deviceFingerprint: string, ipAddress?: string): Promise<void> {
  await ctx.db.query(
    `INSERT INTO user_auth_events (user_id, device_fingerprint, ip_address, success) VALUES ($1, $2, $3, true)`,
    [userId, deviceFingerprint, ipAddress ?? null],
  );
}

/** Old-enough, trusted-enough reporter to pass the default credibility gates on its own. */
async function insertCredibleReporter(ctx: Ctx, trustLevel: TrustLevel = 'trusted', daysOld = 90): Promise<string> {
  return insertUser(ctx, { trustLevel, createdAt: new Date(Date.now() - daysOld * 24 * 60 * 60 * 1000) });
}

// =========================================================================
// SAF-1, minor_suspected corroboration model.
// =========================================================================

test('SAF-1: a single report from a brand-new, low-trust reporter never suspends, and never even applies the interim action', async () => {
  const ctx = buildCtx();
  const reportedId = await insertUser(ctx);
  // Brand new (createdAt ~ now) AND limited trust, fails BOTH credibility gates.
  const reporterId = await insertUser(ctx, { trustLevel: 'limited', createdAt: new Date() });
  const reporterCtx = buildCtx({ actor: userActor(reporterId, 'limited') });

  await report.submitReport(reporterCtx, { reportedId, category: 'minor_suspected' });

  const page = await moderation.listModerationActions(ctx, reportedId);
  // Strongest possible outcome: no credible signal at all means the
  // minor_suspected fast path never fires, and (per the SAF-1 fix) this
  // category is excluded from the general score ladder entirely, so NO
  // moderation action is taken at all, not even a warning.
  assert.equal(page.items.length, 0, 'must never take any action, let alone suspend, on one uncredible report');
  assert.equal(await moderation.isVisibleInDiscovery(ctx, reportedId), true);
});

test('SAF-1: a single report, even from the most credible possible reporter, applies only the fast interim action, never suspension', async () => {
  const ctx = buildCtx();
  const reportedId = await insertUser(ctx);
  const reporterId = await insertCredibleReporter(ctx, 'elite', 365);
  const reporterCtx = buildCtx({ actor: userActor(reporterId, 'elite') });

  await report.submitReport(reporterCtx, { reportedId, category: 'minor_suspected' });

  const page = await moderation.listModerationActions(ctx, reportedId);
  assert.equal(page.items[0]?.action, 'restriction');
  assert.equal(page.items[0]?.reason, 'minor_suspected_report_interim_protective_action');
});

test('SAF-1: two independent, non-clustered, credible reporters escalate to suspension fast (same call as the 2nd report)', async () => {
  const ctx = buildCtx();
  const reportedId = await insertUser(ctx);

  const reporter1 = await insertCredibleReporter(ctx, 'trusted', 200);
  await report.submitReport(buildCtx({ actor: userActor(reporter1, 'trusted') }), { reportedId, category: 'minor_suspected' });
  assert.equal((await moderation.listModerationActions(ctx, reportedId)).items[0]?.action, 'restriction');

  const reporter2 = await insertCredibleReporter(ctx, 'trusted', 100);
  await report.submitReport(buildCtx({ actor: userActor(reporter2, 'trusted') }), { reportedId, category: 'minor_suspected' });

  const page = await moderation.listModerationActions(ctx, reportedId);
  assert.equal(page.items[0]?.action, 'suspension', 'corroborated genuine signal must act decisively and fast');
  assert.equal(page.items[0]?.reason, 'minor_suspected_report_immediate_protective_action');
  assert.equal(await moderation.isVisibleInDiscovery(ctx, reportedId), false);
});

test('SAF-1: a brigade of sock-puppets sharing IP + creation-time proximity (but each a DIFFERENT device fingerprint) is collapsed to ONE corroborator, not N, stays at restriction', async () => {
  const ctx = buildCtx();
  const reportedId = await insertUser(ctx);
  const sharedIp = '203.0.113.7';
  const burstCreatedAt = new Date(Date.now() - 2 * 24 * 60 * 60 * 1000); // all "created" within the same short window

  for (let i = 0; i < 4; i++) {
    const reporterId = await insertUser(ctx, { trustLevel: 'trusted', createdAt: burstCreatedAt });
    // A DIFFERENT fingerprint every time, the exact SAF-6 evasion attempt,
    // but the SAME server-observed IP and the same account-creation burst.
    await insertAuthEvent(ctx, reporterId, `spoofed-fingerprint-${i}`, sharedIp);
    await report.submitReport(buildCtx({ actor: userActor(reporterId, 'trusted') }), { reportedId, category: 'minor_suspected' });
  }

  const page = await moderation.listModerationActions(ctx, reportedId);
  assert.notEqual(page.items[0]?.action, 'suspension', 'a brigade must not be able to buy suspension by varying the fingerprint alone');
  assert.equal(page.items[0]?.action, 'restriction');
});

test('SAF-1: reports from genuinely unrelated credible reporters (no shared IP/fingerprint/creation-burst/relationship) DO count as distinct corroborators', async () => {
  const ctx = buildCtx();
  const reportedId = await insertUser(ctx);

  const reporter1 = await insertCredibleReporter(ctx, 'trusted', 400);
  await insertAuthEvent(ctx, reporter1, 'fp-unrelated-1', '198.51.100.1');
  await report.submitReport(buildCtx({ actor: userActor(reporter1, 'trusted') }), { reportedId, category: 'minor_suspected' });

  const reporter2 = await insertCredibleReporter(ctx, 'trusted', 40); // far apart in account age
  await insertAuthEvent(ctx, reporter2, 'fp-unrelated-2', '198.51.100.250'); // different IP
  await report.submitReport(buildCtx({ actor: userActor(reporter2, 'trusted') }), { reportedId, category: 'minor_suspected' });

  const page = await moderation.listModerationActions(ctx, reportedId);
  assert.equal(page.items[0]?.action, 'suspension');
});

test('SAF-1: false-report consequence, marking a minor_suspected report unfounded penalizes the reporter and durably lowers their future credibility', async () => {
  const ctx = buildCtx();
  const reportedId = await insertUser(ctx);
  const reporterId = await insertCredibleReporter(ctx, 'trusted', 365);
  const reporterCtx = buildCtx({ actor: userActor(reporterId, 'trusted') });

  const filed = await report.submitReport(reporterCtx, { reportedId, category: 'minor_suspected' });

  const before = await report.reporterCredibility(ctx, reporterId, new Date());
  assert.equal(before.isCredible, true);

  const adminCtx = buildCtx({ actor: { type: 'admin', adminId: 'admin-1' } });
  await report.recordReportOutcome(adminCtx, filed.id, 'unfounded');

  const after = await report.reporterCredibility(ctx, reporterId, new Date());
  assert.equal(after.priorUnfoundedCount, 1);
  assert.equal(after.isCredible, false, 'a reporter with an unfounded minor_suspected report on file must lose default credibility');

  // A second minor_suspected report from this now-"previously abusive"
  // reporter must not, by itself, even get the fast interim action.
  const reportedId2 = await insertUser(ctx);
  await report.submitReport(reporterCtx, { reportedId: reportedId2, category: 'minor_suspected' });
  const page2 = await moderation.listModerationActions(ctx, reportedId2);
  assert.notEqual(page2.items[0]?.action, 'suspension');
  assert.notEqual(page2.items[0]?.reason, 'minor_suspected_report_interim_protective_action');
});

test('SAF-1: recordReportOutcome is admin/system-only', async () => {
  const ctx = buildCtx();
  const reportedId = await insertUser(ctx);
  const reporterId = await insertUser(ctx);
  const reporterCtx = buildCtx({ actor: userActor(reporterId) });
  const filed = await report.submitReport(reporterCtx, { reportedId, category: 'spam' });

  await assert.rejects(() => report.recordReportOutcome(reporterCtx, filed.id, 'unfounded'), ForbiddenError);
});

// =========================================================================
// SAF-6, multi-signal anti-brigading (general, not minor_suspected-specific).
// =========================================================================

test('SAF-6: varying the device fingerprint alone no longer evades the anti-brigading discount when other signals still correlate', async () => {
  const ctx = buildCtx();
  const reportedId = await insertUser(ctx);
  const sharedIp = '203.0.113.99';
  const burst = new Date(Date.now() - 5 * 24 * 60 * 60 * 1000);

  const r1 = await insertUser(ctx, { createdAt: burst });
  await insertAuthEvent(ctx, r1, 'fingerprint-A', sharedIp);
  const filed1 = await report.submitReport(buildCtx({ actor: userActor(r1) }), { reportedId, category: 'harassment' });

  const r2 = await insertUser(ctx, { createdAt: burst });
  await insertAuthEvent(ctx, r2, 'fingerprint-B', sharedIp); // different fingerprint, same IP + creation burst
  await report.submitReport(buildCtx({ actor: userActor(r2) }), { reportedId, category: 'harassment' });

  const r3 = await insertUser(ctx, { createdAt: burst });
  await insertAuthEvent(ctx, r3, 'fingerprint-C', sharedIp);
  const shape = { conversationId: null, messageId: null, category: 'harassment' as const, severity: 4, details: null };
  const clusteredScore = await report.scoreReport(ctx, {
    ...shape,
    id: 'clustered',
    reporterId: r3,
    reportedId,
    createdAt: new Date(filed1.createdAt.getTime() + 5000),
  });

  // Compare against a report from a truly unrelated reporter scored at the same position.
  const unrelatedTarget = await insertUser(ctx);
  const rU = await insertUser(ctx, { createdAt: new Date(Date.now() - 500 * 24 * 60 * 60 * 1000) });
  const unrelatedScore = await report.scoreReport(ctx, {
    ...shape,
    id: 'unrelated',
    reporterId: rU,
    reportedId: unrelatedTarget,
    createdAt: new Date(filed1.createdAt.getTime() + 5000),
  });

  assert.ok(clusteredScore < unrelatedScore, 'three fingerprint-varied but IP/timing-correlated reporters must still be discounted relative to a genuinely unrelated reporter');
});

test('SAF-6: findClusteredPriorReporters requires MULTIPLE weak signals, a shared fingerprint alone (no other correlation) does not cross the cluster threshold', async () => {
  const ctx = buildCtx();
  const reportedId = await insertUser(ctx);

  const r1 = await insertUser(ctx, { createdAt: new Date(Date.now() - 300 * 24 * 60 * 60 * 1000) });
  await insertAuthEvent(ctx, r1, 'shared-fp-only'); // no IP set
  const filed1 = await report.submitReport(buildCtx({ actor: userActor(r1) }), { reportedId, category: 'spam' });

  const r2 = await insertUser(ctx, { createdAt: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000) }); // far apart in account age
  await insertAuthEvent(ctx, r2, 'shared-fp-only'); // same fingerprint, nothing else shared

  const clustered = await report.findClusteredPriorReporters(ctx, r2, reportedId, new Date(filed1.createdAt.getTime() + 60 * 60 * 1000));
  assert.equal(clustered.length, 0, 'fingerprint alone (weight 1) must stay below the default cluster threshold (3)');
});
