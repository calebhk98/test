/**
 * postDateFeedback.service.ts unit tests.
 *
 * Self-contained: this file owns its own tiny test harness (rather than
 * importing a shared `testHarness*.ts` owned by a sibling agent) since
 * this build's file list grants edit rights only to this file and
 * `tests/http/feedback.test.ts`. Uses its own dedicated Postgres database
 * (`odate_feedback_unit`, never `outcome_dating`/other agents' `odate_*`
 * databases) per the task brief.
 *
 * Every service exercised here (dateProposal-adjacent tables via raw SQL
 * setup, report.service.ts, trust.service.ts, moderation.service.ts,
 * notification.service.ts, behavioral_prompt_suggestions) is the real,
 * fully-implemented sibling code, nothing is mocked. Date proposals are
 * inserted directly via SQL rather than driven through
 * `dateProposal.service#proposeDate/acceptDateProposal` (that state
 * machine has its own dedicated test file, `dateProposal.test.ts`), this
 * file only needs a `date_proposals` row in a given status, not to
 * re-prove the payment/escrow flow that gets it there.
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import pg from 'pg';
import { runMigrations } from '../../src/db/migrate.js';
import { getPool, closePool } from '../../src/db/pool.js';
import { ConfigService } from '../../src/config/config.service.js';
import { FlagsService, KNOWN_FLAGS } from '../../src/config/flags.service.js';
import { ManualClock } from '../../src/lib/time.js';
import { createSilentLogger } from '../../src/lib/logger.js';
import { FakeProcessor } from '../../src/services/payments/fake.processor.js';
import { StubMediaModerationAdapter } from '../../src/services/media/stub.adapter.js';
import type { Actor, Ctx } from '../../src/lib/ctx.js';
import type { TrustLevel } from '../../src/domain/types.js';
import * as postDateFeedback from '../../src/services/postDateFeedback.service.js';
import { TRUST_EVENT_TYPES } from '../../src/services/trust.service.js';
import { ConflictError, ForbiddenError, NotFoundError } from '../../src/lib/errors.js';
import { createUserAtTrustLevel } from '../support/trustFixtures.js';

// ---------------------------------------------------------------------
// Self-contained harness
// ---------------------------------------------------------------------

const BASE_URL = process.env.DATABASE_URL ?? 'postgres://outcome_dating@127.0.0.1:55433/outcome_dating';
const DB_NAME = 'odate_feedback_unit';

function withDbName(url: string, dbName: string): string {
  const u = new URL(url);
  u.pathname = `/${dbName}`;
  return u.toString();
}

let adminPool: pg.Pool;
let pool: pg.Pool;
let clock: ManualClock;
let config: ConfigService;
let flags: FlagsService;

before(async () => {
  adminPool = new pg.Pool({ connectionString: BASE_URL });
  await adminPool.query(`SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = $1 AND pid <> pg_backend_pid()`, [DB_NAME]);
  await adminPool.query(`DROP DATABASE IF EXISTS ${DB_NAME}`);
  await adminPool.query(`CREATE DATABASE ${DB_NAME}`);

  process.env.DATABASE_URL = withDbName(BASE_URL, DB_NAME);
  await runMigrations();

  pool = getPool();
  clock = new ManualClock(new Date('2026-01-05T12:00:00.000Z'));
  const logger = createSilentLogger();
  config = new ConfigService(pool, clock, logger);
  flags = new FlagsService(pool, logger);
  await config.seedDefaults('system:test');
  await flags.seedKnownFlags();
});

after(async () => {
  await closePool();
  await adminPool.query(`DROP DATABASE IF EXISTS ${DB_NAME}`);
  await adminPool.end();
});

function ctxFor(actor: Actor): Ctx {
  return {
    db: pool,
    clock,
    config,
    flags,
    logger: createSilentLogger(),
    actor,
    payments: new FakeProcessor(),
    media: new StubMediaModerationAdapter(),
  };
}

function userActor(userId: string, trustLevel: TrustLevel = 'standard'): Actor {
  return { type: 'user', userId, trustLevel };
}

let userCounter = 0;
/**
 * `trust_level` is now structurally unable to disagree with `trust_score`
 * (db/migrations/029_trust_invariant.sql, a trigger a concurrently-worked
 * migration added on top of this build's own 025_integrity.sql item 3).
 * A raw `INSERT` naming a `trustLevel` independent of a hardcoded
 * `trust_score` (this helper's previous shape) violates that trigger for
 * anything but the schema's own agreeing default. `createUserAtTrustLevel`
 * (tests/support/trustFixtures.ts, the sanctioned fixture the rest of the
 * suite already migrated onto, see that migration's own doc) reaches the
 * requested level the same way production code ever could, recording a
 * real `trust_events` row through `trust.service.ts` and letting the
 * database derive the pair, so the row this returns can never be the
 * disagreeing shape the trigger exists to reject.
 */
async function insertUser(trustLevel: TrustLevel = 'standard'): Promise<string> {
  userCounter += 1;
  // 'standard' (the default every call site but the retaliation-weighting
  // tests uses) needs no pinning at all: the schema's own default
  // (trust_score 50 / trust_level 'standard') already agrees, and passing
  // `level` unconditionally would record an extra `trust_events` "pin"
  // row that most of this file's `trustEventsFor(...)` assertions (an
  // unfiltered count) never expected, see `createUserAtTrustLevel`'s own
  // doc for exactly this distinction.
  return createUserAtTrustLevel(ctxFor({ type: 'system', job: 'test' }), trustLevel === 'standard' ? undefined : trustLevel, {
    email: `pdf-user-${userCounter}-${Date.now()}@example.test`,
    birthdate: '1995-01-01',
    emailVerified: true,
  });
}

/** Find-or-create, some tests insert more than one date proposal for the same pair, and `conversations` has a UNIQUE(user_a_id, user_b_id) constraint. */
async function insertConversation(userAId: string, userBId: string): Promise<string> {
  const [a, b] = userAId < userBId ? [userAId, userBId] : [userBId, userAId];
  const { rows } = await pool.query<{ id: string }>(
    `INSERT INTO conversations (user_a_id, user_b_id, status) VALUES ($1, $2, 'active')
     ON CONFLICT (user_a_id, user_b_id) DO UPDATE SET status = conversations.status
     RETURNING id`,
    [a, b],
  );
  return rows[0]!.id;
}

let venueId: string | undefined;
async function insertVenue(): Promise<string> {
  if (venueId) return venueId;
  const { rows } = await pool.query<{ id: string }>(
    `INSERT INTO venues (name, address, latitude, longitude, category, active, margin_percent, time_slot_config, redemption_method)
     VALUES ('Test Cafe', '1 Test St', 39.0, -89.0, 'coffee', true, 15, '{"slots":[]}'::jsonb, 'qr_scan')
     RETURNING id`,
  );
  venueId = rows[0]!.id;
  return venueId;
}

interface InsertProposalOpts {
  status?: string;
  scheduledStart?: Date;
  scheduledEnd?: Date;
}

/** Inserts a `date_proposals` row directly at whatever status/timing a test needs, see module doc for why this bypasses `dateProposal.service`'s own state machine. */
async function insertDateProposal(proposerId: string, recipientId: string, opts: InsertProposalOpts = {}): Promise<{ id: string; conversationId: string }> {
  const conversationId = await insertConversation(proposerId, recipientId);
  const venue = await insertVenue();
  const scheduledStart = opts.scheduledStart ?? new Date(clock.now().getTime() - 6 * 60 * 60 * 1000);
  const scheduledEnd = opts.scheduledEnd ?? new Date(scheduledStart.getTime() + 60 * 60 * 1000);
  const { rows } = await pool.query<{ id: string }>(
    `INSERT INTO date_proposals (conversation_id, proposer_id, recipient_id, venue_id, scheduled_start, scheduled_end, status, policy_snapshot, escrow_amount_cents)
     VALUES ($1, $2, $3, $4, $5, $6, $7, '{}'::jsonb, 2000)
     RETURNING id`,
    [conversationId, proposerId, recipientId, venue, scheduledStart, scheduledEnd, opts.status ?? 'completed'],
  );
  return { id: rows[0]!.id, conversationId };
}

async function trustEventsFor(userId: string): Promise<Array<{ event_type: string; delta: number; metadata: Record<string, unknown> }>> {
  const { rows } = await pool.query('SELECT event_type, delta, metadata FROM trust_events WHERE user_id = $1 ORDER BY created_at', [userId]);
  return rows;
}

interface TestQuestion {
  id: string;
  slug: string;
}

/** Inserts a `scale`-type row into the ONE typed question bank (question_bank/user_question_answers, db/migrations/008_questions.sql), replaces the OLD `questions` table this used to target. */
async function insertQuestion(slug: string): Promise<TestQuestion> {
  const typeDefinition = { type: 'scale', min: 1, max: 5, minLabel: 'low', maxLabel: 'high', midLabel: 'mid' };
  const { rows } = await pool.query<{ id: string }>(
    `INSERT INTO question_bank (slug, version, is_current, category, question_type, question_text, type_definition, active)
     VALUES ($1, 1, true, 'lifestyle', 'scale', 'Test question', $2::jsonb, true)
     RETURNING id`,
    [slug, JSON.stringify(typeDefinition)],
  );
  return { id: rows[0]!.id, slug };
}

/** `selfValue`/`preferenceValue` are the new bank's self/preference axis on a `scale` question (1-5), direct replacement for the OLD `answers.self_value`/`answers.partner_value` this used to write. */
async function upsertAnswer(userId: string, question: TestQuestion, selfValue: number, preferenceValue: number): Promise<void> {
  await pool.query(
    `INSERT INTO user_question_answers (user_id, question_slug, question_bank_id, status, self_value, preference_value, importance, answered_at, updated_at)
     VALUES ($1, $2, $3, 'answered', $4::jsonb, $5::jsonb, 'slight', now(), now())
     ON CONFLICT (user_id, question_slug) DO UPDATE SET
       self_value = EXCLUDED.self_value, preference_value = EXCLUDED.preference_value, updated_at = now()`,
    [userId, question.slug, question.id, JSON.stringify(selfValue), JSON.stringify(preferenceValue)],
  );
}

// =====================================================================
// One-sided feedback is still useful
// =====================================================================

test('a single participant submitting a check-in is fully effective without the other side ever responding', async () => {
  const a = await insertUser();
  const b = await insertUser();
  const { id: dateProposalId } = await insertDateProposal(a, b);

  const view = await postDateFeedback.submitCheckIn(ctxFor(userActor(a)), dateProposalId, { outcome: 'happened_good' });
  assert.equal(view.outcome, 'happened_good');
  assert.equal(view.reportFiled, false);

  // B never submits anything, the effect on B (the OTHER party) must
  // already be fully in place from A's single submission.
  const bEvents = await trustEventsFor(b);
  const positive = bEvents.filter((e) => e.event_type === TRUST_EVENT_TYPES.POSITIVE_POST_DATE_FEEDBACK);
  assert.equal(positive.length, 1);
  assert.equal(positive[0]!.delta, 5);

  // A can read their own submission back...
  const mine = await postDateFeedback.getMyCheckIn(ctxFor(userActor(a)), dateProposalId);
  assert.equal(mine.id, view.id);

  // ...but B, who never submitted, has nothing to read.
  await assert.rejects(() => postDateFeedback.getMyCheckIn(ctxFor(userActor(b)), dateProposalId), NotFoundError);
});

// =====================================================================
// Four outcome categories -> four different platform effects
// =====================================================================

test('did_not_happen produces no trust effect on the other party (retaliation-resistant by construction)', async () => {
  const a = await insertUser();
  const b = await insertUser();
  const { id: dateProposalId } = await insertDateProposal(a, b);

  await postDateFeedback.submitCheckIn(ctxFor(userActor(a)), dateProposalId, { outcome: 'did_not_happen' });

  const bEvents = await trustEventsFor(b);
  assert.equal(bEvents.length, 0, 'a single-sided "did not happen" claim must not dock the other party trust');
});

test('happened_bad produces a negative trust event for the other party, weighted (not scored to zero for a standard-trust rater)', async () => {
  const a = await insertUser('standard');
  const b = await insertUser();
  const { id: dateProposalId } = await insertDateProposal(a, b);

  await postDateFeedback.submitCheckIn(ctxFor(userActor(a)), dateProposalId, { outcome: 'happened_bad' });

  const bEvents = await trustEventsFor(b);
  const negative = bEvents.filter((e) => e.event_type === TRUST_EVENT_TYPES.NEGATIVE_POST_DATE_FEEDBACK);
  assert.equal(negative.length, 1);
  assert.ok(negative[0]!.delta < 0, 'happened_bad must cost the other party some trust');
  assert.ok(negative[0]!.delta > -4, 'a standard-trust rater is weighted down from the unweighted base delta');
  // Safety isolation extends to ordinary outcome trust events too, no
  // correlatable dateProposalId in metadata.
  assert.deepEqual(negative[0]!.metadata, {});
});

test('happened_fine produces a small positive trust event, distinct in size from happened_good', async () => {
  const a = await insertUser();
  const fineB = await insertUser();
  const goodB = await insertUser();
  const fineProposal = await insertDateProposal(a, fineB);
  const goodProposal = await insertDateProposal(a, goodB);

  await postDateFeedback.submitCheckIn(ctxFor(userActor(a)), fineProposal.id, { outcome: 'happened_fine' });
  await postDateFeedback.submitCheckIn(ctxFor(userActor(a)), goodProposal.id, { outcome: 'happened_good' });

  const fineEvents = await trustEventsFor(fineB);
  const goodEvents = await trustEventsFor(goodB);
  assert.equal(fineEvents[0]!.delta, 2);
  assert.equal(goodEvents[0]!.delta, 5);
  assert.ok(goodEvents[0]!.delta > fineEvents[0]!.delta, 'happened_good must count for more than happened_fine, not collapsed into one score');
});

test('outcome effects fire once at first submission and do not re-fire on a later edit (bounds repeated-toggle abuse)', async () => {
  const a = await insertUser();
  const b = await insertUser();
  const { id: dateProposalId } = await insertDateProposal(a, b);

  await postDateFeedback.submitCheckIn(ctxFor(userActor(a)), dateProposalId, { outcome: 'happened_good' });
  await postDateFeedback.submitCheckIn(ctxFor(userActor(a)), dateProposalId, { outcome: 'happened_bad' });
  await postDateFeedback.submitCheckIn(ctxFor(userActor(a)), dateProposalId, { outcome: 'happened_good' });

  const bEvents = await trustEventsFor(b);
  assert.equal(bEvents.length, 1, 'editing outcome after first submission must not fire additional trust events');
  assert.equal(bEvents[0]!.delta, 5, 'the FIRST submission is what counted');

  const latest = await postDateFeedback.getMyCheckIn(ctxFor(userActor(a)), dateProposalId);
  assert.equal(latest.outcome, 'happened_good', 'the row itself still reflects the latest edit');
});

test('submitCheckIn rejects a status the date proposal never reached (e.g. still pending_acceptance) and rejects before the date has started', async () => {
  const a = await insertUser();
  const b = await insertUser();
  const notTicketed = await insertDateProposal(a, b, { status: 'pending_acceptance' });
  await assert.rejects(() => postDateFeedback.submitCheckIn(ctxFor(userActor(a)), notTicketed.id, { outcome: 'happened_good' }), ConflictError);

  const future = await insertDateProposal(a, b, { status: 'ticketed', scheduledStart: new Date(clock.now().getTime() + 60 * 60 * 1000), scheduledEnd: new Date(clock.now().getTime() + 2 * 60 * 60 * 1000) });
  await assert.rejects(() => postDateFeedback.submitCheckIn(ctxFor(userActor(a)), future.id, { outcome: 'happened_good' }), ConflictError);
});

test('submitCheckIn rejects a non-participant', async () => {
  const a = await insertUser();
  const b = await insertUser();
  const stranger = await insertUser();
  const { id: dateProposalId } = await insertDateProposal(a, b);
  await assert.rejects(() => postDateFeedback.submitCheckIn(ctxFor(userActor(stranger)), dateProposalId, { outcome: 'happened_good' }), ForbiddenError);
});

// =====================================================================
// Safety: reaches moderation without a separate manual report
// =====================================================================

test('safetyFlag "incident" routes into report.service/moderation immediately, with no separate report required', async () => {
  const a = await insertUser();
  const b = await insertUser();
  const { id: dateProposalId } = await insertDateProposal(a, b);

  const view = await postDateFeedback.submitCheckIn(ctxFor(userActor(a)), dateProposalId, {
    outcome: 'happened_bad',
    safetyFlag: 'incident',
    safetyDetails: 'they followed me after I said goodnight',
  });
  assert.equal(view.reportFiled, true);

  const { rows: reportRows } = await pool.query<{ reporter_id: string; reported_id: string; category: string }>(
    'SELECT reporter_id, reported_id, category FROM reports WHERE reported_id = $1',
    [b],
  );
  assert.equal(reportRows.length, 1, 'exactly one report.service report must exist, the user never had to also file one manually');
  assert.equal(reportRows[0]!.reporter_id, a);
  assert.equal(reportRows[0]!.category, 'unsafe_behavior');

  // Proof it reached the ACTUAL moderation machinery (not just a `reports`
  // row), report.service#submitReport's own call to
  // moderation.recordAutomatedFlag, never reimplemented here.
  const { rows: flagRows } = await pool.query('SELECT signal_type, weight FROM automated_moderation_flags WHERE user_id = $1', [b]);
  assert.equal(flagRows.length, 1);
  assert.equal(flagRows[0]!.signal_type, 'user_report');
  assert.ok(Number(flagRows[0]!.weight) > 0);
});

test('an "incident" safety flag scores at least as high as an ordinary manually-filed report of the same category (never reimplements scoring, relies on report.service\'s own relationship/category weighting)', async () => {
  const a = await insertUser();
  const b = await insertUser();
  const stranger = await insertUser();
  const { id: dateProposalId } = await insertDateProposal(a, b);

  await postDateFeedback.submitCheckIn(ctxFor(userActor(a)), dateProposalId, {
    outcome: 'happened_bad',
    safetyFlag: 'incident',
  });

  // An "ordinary" manual report: same category, but from a stranger with
  // no shared conversation (relationshipMultiplier discount applies).
  const reportService = await import('../../src/services/report.service.js');
  await reportService.submitReport(ctxFor(userActor(stranger)), { reportedId: b, category: 'unsafe_behavior' });

  const { rows } = await pool.query<{ reporter_id: string; created_at: Date; category: string; severity: number }>(
    'SELECT reporter_id, created_at, category, severity FROM reports WHERE reported_id = $1 ORDER BY created_at',
    [b],
  );
  const checkInReport = { id: rows[0]!.reporter_id, created_at: rows[0]!.created_at, category: rows[0]!.category, severity: rows[0]!.severity };
  const strangerReport = rows[1]!;
  const checkInWeight = await reportService.scoreReport(ctxFor(userActor(a)), {
    id: 'x',
    reporterId: a,
    reportedId: b,
    conversationId: null,
    messageId: null,
    category: 'unsafe_behavior',
    severity: checkInReport.severity,
    details: null,
    createdAt: checkInReport.created_at,
  });
  const strangerWeight = await reportService.scoreReport(ctxFor(userActor(a)), {
    id: 'y',
    reporterId: stranger,
    reportedId: b,
    conversationId: null,
    messageId: null,
    category: 'unsafe_behavior',
    severity: strangerReport.severity,
    details: null,
    createdAt: strangerReport.created_at,
  });
  assert.ok(checkInWeight >= strangerWeight, `check-in-originated report (${checkInWeight}) should score >= an ordinary stranger report (${strangerWeight})`);
});

test('safetyFlag "concern" alone does NOT file a report, only corroboration by a second, independent flagger does', async () => {
  const a = await insertUser();
  const b = await insertUser();
  const c = await insertUser();
  const target = await insertUser(); // the person both a and c will flag concern about, across two DIFFERENT dates

  const dateAC = await insertDateProposal(a, target);
  const view1 = await postDateFeedback.submitCheckIn(ctxFor(userActor(a)), dateAC.id, { outcome: 'happened_fine', safetyFlag: 'concern', safetyDetails: 'felt a little off' });
  assert.equal(view1.reportFiled, false, 'a single concern flag must not file a report by itself');

  let { rows } = await pool.query('SELECT 1 FROM reports WHERE reported_id = $1', [target]);
  assert.equal(rows.length, 0);

  const dateCTarget = await insertDateProposal(c, target);
  const view2 = await postDateFeedback.submitCheckIn(ctxFor(userActor(c)), dateCTarget.id, { outcome: 'happened_fine', safetyFlag: 'concern', safetyDetails: 'also felt off' });
  assert.equal(view2.reportFiled, true, 'a second independent flagger must corroborate and trigger filing');

  ({ rows } = await pool.query('SELECT reporter_id FROM reports WHERE reported_id = $1', [target]));
  assert.equal(rows.length, 1);
  assert.equal((rows[0] as { reporter_id: string }).reporter_id, c, 'the corroborating (second) submitter is the one who files it');
});

test('re-submitting the same check-in never files a second report for the same declared safety flag', async () => {
  const a = await insertUser();
  const b = await insertUser();
  const { id: dateProposalId } = await insertDateProposal(a, b);

  await postDateFeedback.submitCheckIn(ctxFor(userActor(a)), dateProposalId, { outcome: 'happened_bad', safetyFlag: 'incident', safetyDetails: 'first telling' });
  await postDateFeedback.submitCheckIn(ctxFor(userActor(a)), dateProposalId, { outcome: 'happened_bad', safetyFlag: 'incident', safetyDetails: 'first telling, edited' });

  const { rows } = await pool.query('SELECT 1 FROM reports WHERE reported_id = $1', [b]);
  assert.equal(rows.length, 1);
});

// =====================================================================
// Safety isolation: the other party cannot observe a safety response
// =====================================================================

test('the reported party cannot read the safety flag/details through any export in this module', async () => {
  const a = await insertUser();
  const b = await insertUser();
  const { id: dateProposalId } = await insertDateProposal(a, b);

  await postDateFeedback.submitCheckIn(ctxFor(userActor(a)), dateProposalId, {
    outcome: 'happened_bad',
    safetyFlag: 'incident',
    safetyDetails: 'a specific safety detail only A wrote',
  });

  // B has no check-in of their own, getMyCheckIn is hard-scoped to the
  // CALLER's own row, so it structurally cannot return A's.
  await assert.rejects(() => postDateFeedback.getMyCheckIn(ctxFor(userActor(b)), dateProposalId), NotFoundError);

  // Nothing anywhere in trust_events for B (the reported party) carries
  // the safety text, "safety", or A's identity.
  const bEvents = await trustEventsFor(b);
  const serialized = JSON.stringify(bEvents);
  assert.ok(!serialized.includes('specific safety detail'), 'safety details text must never reach the reported party\'s own trust events');
  assert.ok(!serialized.toLowerCase().includes('safety'), 'no event type/metadata visible to B may even be labeled as safety-specific');

  // A safety flag CAN legitimately end up producing the same generic
  // `safety_notice` moderation notification an ordinary manually-filed
  // unsafe_behavior report would also produce (report.service.ts's own,
  // pre-existing behavior, not reimplemented or amplified here). The
  // isolation guarantee is INDISTINGUISHABILITY, not literal silence:
  // assert whatever B received carries nothing naming "check-in"/
  // "post-date", and none of the submitter's free text.
  const { rows: bNotifications } = await pool.query<{ event_type: string; payload: Record<string, unknown> }>(
    'SELECT event_type, payload FROM notifications WHERE user_id = $1',
    [b],
  );
  for (const n of bNotifications) {
    assert.notEqual(n.event_type, 'post_date_feedback_request', 'the reported party must never receive the CHECK-IN PROMPT event about someone else\'s submission');
    const payloadText = JSON.stringify(n.payload).toLowerCase();
    assert.ok(!payloadText.includes('check-in') && !payloadText.includes('check_in'), 'no notification payload may name the check-in mechanism');
    assert.ok(!payloadText.includes('specific safety detail'), 'no notification may carry the submitter\'s free-text safety details');
  }
});

test('a NON-safety check-in never notifies the other party at all (no timing side-channel for ordinary outcome ratings)', async () => {
  const a = await insertUser();
  const b = await insertUser();
  const { id: dateProposalId } = await insertDateProposal(a, b);

  await postDateFeedback.submitCheckIn(ctxFor(userActor(a)), dateProposalId, { outcome: 'happened_bad' });

  const { rows: bNotifications } = await pool.query('SELECT event_type FROM notifications WHERE user_id = $1', [b]);
  assert.equal(bNotifications.length, 0, 'an ordinary (non-safety) check-in must never notify the other party, nothing observable happens to them at all');
});

test('a safety flag never changes the date proposal state the other party can read', async () => {
  const a = await insertUser();
  const b = await insertUser();
  const { id: dateProposalId } = await insertDateProposal(a, b);

  const before = await pool.query('SELECT status FROM date_proposals WHERE id = $1', [dateProposalId]);
  await postDateFeedback.submitCheckIn(ctxFor(userActor(a)), dateProposalId, { outcome: 'happened_bad', safetyFlag: 'incident', safetyDetails: 'x' });
  const after = await pool.query('SELECT status FROM date_proposals WHERE id = $1', [dateProposalId]);

  assert.equal(after.rows[0].status, before.rows[0].status, 'a safety flag must not alter date_proposals.status (which the reported party CAN read via GET /date-proposals/:id)');
});

// =====================================================================
// Retaliation weighting
// =====================================================================

test('a rater whose recent history is overwhelmingly negative is damped down (serial-negative pattern), vs a clean-history rater at full weight', async () => {
  const serialRater = await insertUser('trusted'); // high base weight, so the dampening effect is unambiguous
  const cleanRater = await insertUser('trusted');

  // Build up a mostly-negative history for serialRater across several
  // different dates (independent partners, so this isn't about any one
  // relationship).
  for (let i = 0; i < 5; i++) {
    const partner = await insertUser();
    const { id } = await insertDateProposal(serialRater, partner);
    await postDateFeedback.submitCheckIn(ctxFor(userActor(serialRater)), id, { outcome: 'happened_bad' });
  }

  const cleanTarget = await insertUser();
  const serialTarget = await insertUser();
  const cleanProposal = await insertDateProposal(cleanRater, cleanTarget);
  const serialProposal = await insertDateProposal(serialRater, serialTarget);

  await postDateFeedback.submitCheckIn(ctxFor(userActor(cleanRater)), cleanProposal.id, { outcome: 'happened_bad' });
  await postDateFeedback.submitCheckIn(ctxFor(userActor(serialRater)), serialProposal.id, { outcome: 'happened_bad' });

  const cleanEvents = (await trustEventsFor(cleanTarget)).filter((e) => e.event_type === TRUST_EVENT_TYPES.NEGATIVE_POST_DATE_FEEDBACK);
  const serialEvents = (await trustEventsFor(serialTarget)).filter((e) => e.event_type === TRUST_EVENT_TYPES.NEGATIVE_POST_DATE_FEEDBACK);

  assert.equal(cleanEvents.length, 1);
  const serialMagnitude = serialEvents.length === 0 ? 0 : Math.abs(serialEvents[0]!.delta);
  assert.ok(serialMagnitude < Math.abs(cleanEvents[0]!.delta), `a serial-negative rater's delta magnitude (${serialMagnitude}) must be damped below a clean-history rater's (${Math.abs(cleanEvents[0]!.delta)})`);
});

test('a low-trust rater\'s negative rating counts for less than a high-trust rater\'s', async () => {
  const limitedRater = await insertUser('limited');
  const eliteRater = await insertUser('elite');
  const targetOfLimited = await insertUser();
  const targetOfElite = await insertUser();

  const p1 = await insertDateProposal(limitedRater, targetOfLimited);
  const p2 = await insertDateProposal(eliteRater, targetOfElite);
  await postDateFeedback.submitCheckIn(ctxFor(userActor(limitedRater)), p1.id, { outcome: 'happened_bad' });
  await postDateFeedback.submitCheckIn(ctxFor(userActor(eliteRater)), p2.id, { outcome: 'happened_bad' });

  const limitedEffect = (await trustEventsFor(targetOfLimited))[0]!.delta;
  const eliteEffect = (await trustEventsFor(targetOfElite))[0]!.delta;
  assert.ok(Math.abs(limitedEffect) < Math.abs(eliteEffect), `limited-trust rater's effect (${limitedEffect}) should be smaller in magnitude than an elite-trust rater's (${eliteEffect})`);
});

// =====================================================================
// Timing: prompt after scheduled end, with a window, and a reminder,
// never endlessly.
// =====================================================================

/**
 * These prompt-sweep tests deliberately assert against the specific
 * `post_date_feedback_prompts` rows for THIS test's own date proposal/
 * users, rather than `runCheckInPromptSweep`'s aggregate return counters
 * the sweep scans the whole `date_proposals` table, and this file's
 * earlier tests share the same database and the same advancing
 * `ManualClock`, so by the time later tests run, plenty of unrelated
 * `completed` proposals from earlier tests are ALSO legitimately
 * sweep-eligible. That is real, correct sweep behavior, not a bug, the
 * per-row assertions below are what actually isolates this test's claim.
 */
async function promptRowFor(dateProposalId: string, userId: string): Promise<{ prompt_count: number } | undefined> {
  const { rows } = await pool.query<{ prompt_count: number }>(
    'SELECT prompt_count FROM post_date_feedback_prompts WHERE date_proposal_id = $1 AND user_id = $2',
    [dateProposalId, userId],
  );
  return rows[0];
}

test('check-in prompt fires only after the delay window, sends exactly one reminder, then stops for good', async () => {
  await flags.setFlag(KNOWN_FLAGS.POST_DATE_FEEDBACK, { enabled: true, rolloutPercent: 100 });

  const a = await insertUser();
  const b = await insertUser();
  const scheduledEnd = new Date(clock.now().getTime());
  const { id: dateProposalId } = await insertDateProposal(a, b, { status: 'ticketed', scheduledStart: new Date(scheduledEnd.getTime() - 60 * 60 * 1000), scheduledEnd });

  const sysCtx = ctxFor({ type: 'system', job: 'test' });

  // Too soon, the initial delay hasn't elapsed yet.
  await postDateFeedback.runCheckInPromptSweep(sysCtx);
  assert.equal(await promptRowFor(dateProposalId, a), undefined, 'no prompt row yet, too soon after scheduled_end');

  clock.advanceHours(4); // past the initial delay
  await postDateFeedback.runCheckInPromptSweep(sysCtx);
  assert.equal((await promptRowFor(dateProposalId, a))?.prompt_count, 1, 'A should get the initial prompt');
  assert.equal((await promptRowFor(dateProposalId, b))?.prompt_count, 1, 'B should get the initial prompt');

  // Immediately again, no reminder due yet, no duplicate initial prompt.
  await postDateFeedback.runCheckInPromptSweep(sysCtx);
  assert.equal((await promptRowFor(dateProposalId, a))?.prompt_count, 1);

  clock.advanceHours(49); // past the reminder delay
  await postDateFeedback.runCheckInPromptSweep(sysCtx);
  assert.equal((await promptRowFor(dateProposalId, a))?.prompt_count, 2, 'exactly one reminder');
  assert.equal((await promptRowFor(dateProposalId, b))?.prompt_count, 2);

  // Advance well past the reminder delay again, must NOT prompt a third
  // time ("do not prompt endlessly").
  clock.advanceHours(200);
  await postDateFeedback.runCheckInPromptSweep(sysCtx);
  assert.equal((await promptRowFor(dateProposalId, a))?.prompt_count, 2, 'stays at 2 forever, no third prompt');
  assert.equal((await promptRowFor(dateProposalId, b))?.prompt_count, 2);
});

test('a check-in prompt stops once the user has actually submitted, and never fires once the max window has elapsed', async () => {
  await flags.setFlag(KNOWN_FLAGS.POST_DATE_FEEDBACK, { enabled: true, rolloutPercent: 100 });

  const a = await insertUser();
  const b = await insertUser();
  const scheduledEnd = new Date(clock.now().getTime());
  const { id: dateProposalId } = await insertDateProposal(a, b, { status: 'ticketed', scheduledStart: new Date(scheduledEnd.getTime() - 60 * 60 * 1000), scheduledEnd });

  await postDateFeedback.submitCheckIn(ctxFor(userActor(a)), dateProposalId, { outcome: 'happened_good' });

  clock.advanceHours(4);
  const sysCtx = ctxFor({ type: 'system', job: 'test' });
  await postDateFeedback.runCheckInPromptSweep(sysCtx);
  assert.equal(await promptRowFor(dateProposalId, a), undefined, 'A already checked in, never even gets a prompt row');
  assert.equal((await promptRowFor(dateProposalId, b))?.prompt_count, 1, 'B, who has not checked in, gets prompted');

  // A stale proposal whose window has already fully elapsed must never be prompted at all.
  const staleEnd = new Date(clock.now().getTime() - 20 * 24 * 60 * 60 * 1000);
  const c = await insertUser();
  const d = await insertUser();
  const stale = await insertDateProposal(c, d, { status: 'ticketed', scheduledStart: new Date(staleEnd.getTime() - 60 * 60 * 1000), scheduledEnd: staleEnd });
  await postDateFeedback.runCheckInPromptSweep(sysCtx);
  assert.equal(await promptRowFor(stale.id, c), undefined, 'a proposal past the max prompt window must never be prompted');
  assert.equal(await promptRowFor(stale.id, d), undefined);
});

test('the prompt sweep sends nothing while the feature flag is disabled', async () => {
  await flags.setFlag(KNOWN_FLAGS.POST_DATE_FEEDBACK, { enabled: false });

  const a = await insertUser();
  const b = await insertUser();
  const scheduledEnd = new Date(clock.now().getTime());
  await insertDateProposal(a, b, { status: 'ticketed', scheduledStart: new Date(scheduledEnd.getTime() - 60 * 60 * 1000), scheduledEnd });

  clock.advanceHours(4);
  const result = await postDateFeedback.runCheckInPromptSweep(ctxFor({ type: 'system', job: 'test' }));
  assert.equal(result.promptsSent, 0);
});

// =====================================================================
// Matching signal: produces a question, never a silent change
// =====================================================================

test('the matching-signal sweep creates a pending behavioral_prompt_suggestions row and never touches user_question_answers directly', async () => {
  await flags.setFlag(KNOWN_FLAGS.POST_DATE_FEEDBACK, { enabled: true, rolloutPercent: 100 });
  await flags.setFlag(KNOWN_FLAGS.BEHAVIORAL_QUESTION_PROMPTS, { enabled: true, rolloutPercent: 100 });

  const user = await insertUser();
  const question = await insertQuestion(`matching-signal-${Date.now()}`);
  // User states they want a partner who scores LOW (1) on this axis...
  await upsertAnswer(user, question, 3, 1);

  // ...but every one of their GOOD dates was with a partner who scores
  // HIGH (5), a real divergence between stated preference and what
  // actually correlates with a good outcome.
  for (let i = 0; i < postDateFeedback.MIN_GOOD_DATES_FOR_MATCHING_SIGNAL; i++) {
    const partner = await insertUser();
    await upsertAnswer(partner, question, 5, 3);
    const { id } = await insertDateProposal(user, partner);
    await postDateFeedback.submitCheckIn(ctxFor(userActor(user)), id, { outcome: 'happened_good' });
  }

  const beforeAnswer = await pool.query(
    'SELECT self_value, preference_value FROM user_question_answers WHERE user_id = $1 AND question_slug = $2',
    [user, question.slug],
  );

  const result = await postDateFeedback.runMatchingSignalSweep(ctxFor({ type: 'system', job: 'test' }));
  assert.ok(result.suggestionsCreated >= 1);

  const { rows } = await pool.query(
    `SELECT status, trigger_kind, question_id FROM behavioral_prompt_suggestions WHERE user_id = $1`,
    [user],
  );
  assert.equal(rows.length, 1);
  assert.equal((rows[0] as { status: string }).status, 'pending', 'must be a pending QUESTION, never an auto-applied answer');
  assert.equal((rows[0] as { trigger_kind: string }).trigger_kind, 'post_date_outcome');
  assert.equal((rows[0] as { question_id: string }).question_id, question.id);

  // The user's stated answer must be byte-for-byte unchanged, this
  // module never silently rewrites `user_question_answers` or sorting.
  const afterAnswer = await pool.query(
    'SELECT self_value, preference_value FROM user_question_answers WHERE user_id = $1 AND question_slug = $2',
    [user, question.slug],
  );
  assert.deepEqual(afterAnswer.rows[0], beforeAnswer.rows[0]);
});

test('the matching-signal sweep creates nothing for a user with too few good-outcome dates, or when divergence is small', async () => {
  await flags.setFlag(KNOWN_FLAGS.POST_DATE_FEEDBACK, { enabled: true, rolloutPercent: 100 });
  await flags.setFlag(KNOWN_FLAGS.BEHAVIORAL_QUESTION_PROMPTS, { enabled: true, rolloutPercent: 100 });

  const user = await insertUser();
  const question = await insertQuestion(`matching-signal-small-${Date.now()}`);
  await upsertAnswer(user, question, 3, 3);

  // Only ONE good date, below MIN_GOOD_DATES_FOR_MATCHING_SIGNAL.
  const partner = await insertUser();
  await upsertAnswer(partner, question, 3, 3); // and no divergence anyway
  const { id } = await insertDateProposal(user, partner);
  await postDateFeedback.submitCheckIn(ctxFor(userActor(user)), id, { outcome: 'happened_good' });

  await postDateFeedback.runMatchingSignalSweep(ctxFor({ type: 'system', job: 'test' }));
  const { rows } = await pool.query('SELECT 1 FROM behavioral_prompt_suggestions WHERE user_id = $1', [user]);
  assert.equal(rows.length, 0);
});
