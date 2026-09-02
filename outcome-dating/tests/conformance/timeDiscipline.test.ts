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
 * this exact bug class (`report.service.ts`'s `reports.created_at`); this
 * file adds dedicated regression coverage for two more, found while
 * building this suite's CC-9 test (see privacy.test.ts's inline note).
 *
 * FINDING (report this, do not weaken these tests): both
 * `moderation.service.ts#applyThresholds`'s `INSERT INTO moderation_actions`
 * and `appeal.service.ts#submitAppeal`'s `INSERT INTO appeals` omit
 * `created_at`/`submitted_at` from their column list, so both fall back to
 * the schema's own `DEFAULT now()` (`db/migrations/001_init.sql`), the
 * database's real wall clock, not the `Ctx.clock` these two service files
 * otherwise honor everywhere else (both explicitly pass `ctx.clock.now()`
 * for their OTHER timestamp columns, e.g. `resolveAppeal`'s
 * `resolved_at`). Concretely, this makes `appeal.service#checkCooldownElapsed`
 * (which correctly reads `ctx.clock.now()`) compare a `ManualClock`
 * pinned to a test's fixed epoch against a REAL timestamp, so a test
 * built the way this whole suite is supposed to be built (a fixed
 * historical `ManualClock`, per docs/test-strategy.md) sees "0 hours (or
 * a deeply negative number of hours) have elapsed" no matter how far the
 * manual clock is advanced, unless it is advanced PAST real wall-clock
 * time, which defeats the entire point of a controllable clock. Both
 * tests below fail today for exactly this reason and must not be
 * "fixed" by relaxing the assertion, waiting on real time, or asserting
 * against `new Date()`; the fix belongs in `moderation.service.ts` /
 * `appeal.service.ts`, passing `ctx.clock.now()` into both INSERTs like
 * every sibling function in the same files already does.
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
