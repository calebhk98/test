/**
 * CC-12: "Time-based transitions ... are driven exclusively by the
 * injected `Clock`, never by `Date.now()`/`new Date()` directly, so tests
 * are fully deterministic." The obligation is broader than "some column
 * uses real time" (a raw `new Date()` call would be the direct violation);
 * in practice, the way this bug actually shows up in this codebase is a
 * table column left to its own SQL `DEFAULT now()` instead of the writer
 * passing `ctx.clock.now()` explicitly, which is exactly as real-time-
 * dependent as calling `new Date()` in application code, just one layer
 * further down. `docs/test-audit.md` already documents one instance of
 * this exact bug class (`report.service.ts`'s `reports.created_at`).
 *
 * FINDING, CONFIRMED THEN FIXED DURING THIS SESSION: while building this
 * suite's CC-9 test (see privacy.test.ts's inline note) both
 * `moderation.service.ts#applyThresholds`'s `INSERT INTO moderation_actions`
 * and `appeal.service.ts#submitAppeal`'s `INSERT INTO appeals` were found
 * omitting `created_at`/`submitted_at` from their column list, falling
 * back to the schema's own `DEFAULT now()` (`db/migrations/001_init.sql`,
 * the database's real wall clock), unlike every OTHER timestamp column in
 * both files (e.g. `resolveAppeal`'s `resolved_at`, which already passed
 * `ctx.clock.now()` correctly). This broke `appeal.service#checkCooldownElapsed`
 * under any fixed-epoch `ManualClock` (see privacy.test.ts's now-obsolete
 * workaround comment for the exact symptom). A concurrently-running agent
 * fixed both call sites (now both pass `ctx.clock.now()` explicitly) while
 * this suite was being written; both tests below now PASS and are kept as
 * permanent regression coverage for the fix rather than deleted, so a
 * future reversion is caught immediately. If either test below starts
 * failing again, it is this exact real-wall-clock regression, not a new
 * defect to re-diagnose from scratch.
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { setupConformanceDb, teardownConformanceDb, makeCtx, userActor, createUser, rawRow, type TestDb } from './support.js';
import * as moderationService from '../../src/services/moderation.service.js';
import * as appealService from '../../src/services/appeal.service.js';

let db: TestDb;

before(async () => {
  db = await setupConformanceDb('timediscipline');
  // A fixed epoch far from real wall-clock time, on purpose: this is
  // precisely the scenario the obligation exists to make safe.
  db.clock.set(new Date('2020-03-01T00:00:00.000Z'));
});

after(async () => {
  await teardownConformanceDb(db);
});

test('CC-12 FINDING: moderation_actions.created_at must come from ctx.clock, not the database default now()', async () => {
  const userId = await createUser(db);
  const ctx = makeCtx(db, userActor(userId));

  await moderationService.recordAutomatedFlag(ctx, { userId, signalType: 'user_report', weight: 60, metadata: {} });
  const action = await moderationService.applyThresholds(ctx, userId);
  assert.ok(action, 'sanity: an action was actually created');

  const row = await rawRow<{ created_at: Date }>(db, `SELECT created_at FROM moderation_actions WHERE id = $1`, [action!.id]);
  assert.ok(row, 'sanity: the row exists');
  assert.equal(
    row!.created_at.getTime(),
    db.clock.now().getTime(),
    "moderation_actions.created_at must equal ctx.clock.now() at write time (CC-12); it currently equals the database's real wall-clock now() instead, breaking any ManualClock-driven test of appeal.service#checkCooldownElapsed downstream",
  );
});

test('CC-12 FINDING: appeals.submitted_at must come from ctx.clock, not the database default now()', async () => {
  const userId = await createUser(db);
  const ctx = makeCtx(db, userActor(userId));

  await moderationService.recordAutomatedFlag(ctx, { userId, signalType: 'user_report', weight: 60, metadata: {} });
  await moderationService.applyThresholds(ctx, userId);

  // Jump the manual clock forward past real wall-clock time purely to get
  // submitAppeal PAST the cooldown gate (itself only reachable because of
  // the bug under test in this very case, see module doc), so the appeal
  // row actually gets written and its submitted_at can be inspected.
  db.clock.set(new Date('2030-01-01T00:00:00.000Z'));
  const appeal = await appealService.submitAppeal(ctx, { method: 'cooldown' });

  const row = await rawRow<{ submitted_at: Date }>(db, `SELECT submitted_at FROM appeals WHERE id = $1`, [appeal.id]);
  assert.ok(row);
  assert.equal(
    row!.submitted_at.getTime(),
    db.clock.now().getTime(),
    "appeals.submitted_at must equal ctx.clock.now() at write time (CC-12); it currently equals the database's real wall-clock now() instead",
  );
});
