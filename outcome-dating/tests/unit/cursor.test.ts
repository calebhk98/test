/**
 * tests/unit/cursor.test.ts, src/lib/cursor.ts, the shared
 * `(timestamp, id)` cursor codec extracted per docs/duplication.md finding
 * 3 (three of six pagination endpoints validated a malformed cursor's date
 * and three silently let an `Invalid Date` reach a SQL query, turning
 * ordinary bad client input into an HTTP 500 instead of a 400).
 *
 * Two halves:
 *  1. Pure unit tests of `decodeTimestampIdCursor`/`encodeTimestampIdCursor`
 *     directly, against every malformed-input shape the task calls out:
 *     malformed, truncated, tampered, wrong-type, and null-date cursors.
 *  2. A DB-backed proof that an ADOPTING endpoint (`message.service#listMessages`,
 *     switched onto this helper as part of the same fix) turns a malformed
 *     cursor into a typed `ValidationError` (status 400) rather than a raw
 *     DB error (which the shared HTTP error handler, src/http/errors.ts,
 *     would otherwise turn into an unintended 500), the exact bug this
 *     helper closes.
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { decodeTimestampIdCursor, encodeTimestampIdCursor } from '../../src/lib/cursor.js';
import { ValidationError } from '../../src/lib/errors.js';
import * as message from '../../src/services/message.service.js';
import {
  setupTestDatabase,
  teardownTestDatabase,
  buildCtx,
  userActor,
  insertUser,
  insertConversation,
} from './testCtxAgentE.js';

// =====================================================================
// 1. Pure codec tests
// =====================================================================

test('encode/decode round-trips a (timestamp, id) pair exactly', () => {
  const ts = new Date('2026-03-14T09:26:53.589Z');
  const id = '11111111-1111-1111-1111-111111111111';
  const cursor = encodeTimestampIdCursor(ts, id);
  const decoded = decodeTimestampIdCursor(cursor);
  assert.equal(decoded.ts.getTime(), ts.getTime());
  assert.equal(decoded.id, id);
});

test('decodeTimestampIdCursor: null-date cursor throws ValidationError, not a usable Date', () => {
  // The exact shape finding 3 describes: a structurally well-formed cursor
  // whose timestamp component does not parse to a real date.
  const cursor = Buffer.from('not-a-date|11111111-1111-1111-1111-111111111111', 'utf8').toString('base64url');
  assert.throws(() => decodeTimestampIdCursor(cursor), ValidationError);
});

test('decodeTimestampIdCursor: literal "null"/"undefined" timestamp text throws', () => {
  for (const bad of ['null', 'undefined', 'NaN', '']) {
    const cursor = Buffer.from(`${bad}|11111111-1111-1111-1111-111111111111`, 'utf8').toString('base64url');
    assert.throws(() => decodeTimestampIdCursor(cursor), ValidationError, `expected "${bad}" to be rejected`);
  }
});

test('decodeTimestampIdCursor: malformed cursor (no separator at all) throws', () => {
  const cursor = Buffer.from('2026-03-14T09:26:53.589Znoseparatorhere', 'utf8').toString('base64url');
  assert.throws(() => decodeTimestampIdCursor(cursor), ValidationError);
});

test('decodeTimestampIdCursor: garbage / non-base64url junk throws rather than returning nonsense', () => {
  assert.throws(() => decodeTimestampIdCursor('!!!not valid base64url at all!!!'), ValidationError);
  assert.throws(() => decodeTimestampIdCursor('....'), ValidationError);
});

test('decodeTimestampIdCursor: truncated cursor (valid cursor cut short) throws', () => {
  const full = encodeTimestampIdCursor(new Date('2026-01-01T00:00:00.000Z'), '11111111-1111-1111-1111-111111111111');
  const truncated = full.slice(0, Math.floor(full.length / 3));
  assert.throws(() => decodeTimestampIdCursor(truncated), ValidationError);
});

test('decodeTimestampIdCursor: tampered cursor (flipped interior character) is rejected or safely re-parsed, never silently wrong in a way that skips validation', () => {
  const full = encodeTimestampIdCursor(new Date('2026-01-01T00:00:00.000Z'), '11111111-1111-1111-1111-111111111111');
  const chars = full.split('');
  // Flip a character in the middle of the encoded payload.
  const mid = Math.floor(chars.length / 2);
  chars[mid] = chars[mid] === 'A' ? 'B' : 'A';
  const tampered = chars.join('');
  // Tampering either corrupts the structure/date (-> throws) or happens to
  // still decode to *some* valid (ts, id) pair (base64url has no checksum,
  // so this is possible), either way it must never throw anything other
  // than a typed ValidationError, and it must never produce an Invalid Date.
  try {
    const decoded = decodeTimestampIdCursor(tampered);
    assert.equal(Number.isNaN(decoded.ts.getTime()), false, 'a value that decodes at all must carry a valid Date');
  } catch (err) {
    assert.ok(err instanceof ValidationError, 'a tampered cursor that fails to decode must fail as ValidationError');
  }
});

test('decodeTimestampIdCursor: wrong-type input throws ValidationError, not a crash', () => {
  for (const bad of [123, null, undefined, {}, [], true, ''] as unknown[]) {
    assert.throws(() => decodeTimestampIdCursor(bad), ValidationError, `expected ${JSON.stringify(bad)} to be rejected`);
  }
});

test('decodeTimestampIdCursor: empty id half throws', () => {
  const cursor = Buffer.from('2026-01-01T00:00:00.000Z|', 'utf8').toString('base64url');
  assert.throws(() => decodeTimestampIdCursor(cursor), ValidationError);
});

// =====================================================================
// 2. Adopting-endpoint proof: message.service#listMessages
// =====================================================================

before(async () => {
  await setupTestDatabase('cursor');
});

after(async () => {
  await teardownTestDatabase();
});

test('adopting endpoint (message.listMessages): a malformed cursor is a typed ValidationError (HTTP 400), never an unhandled 500', async () => {
  const setupCtx = buildCtx();
  const userAId = await insertUser(setupCtx);
  const userBId = await insertUser(setupCtx);
  const conversationId = await insertConversation(setupCtx, userAId, userBId);
  const ctx = buildCtx({ actor: userActor(userAId) });

  // Exactly finding 3's concrete divergent input: parseable base64url,
  // corrupted date. Before this fix, message.service's local decodeCursor
  // threaded the resulting Invalid Date straight into the SQL query.
  const badCursor = Buffer.from('not-a-date|11111111-1111-1111-1111-111111111111', 'utf8').toString('base64url');

  await assert.rejects(
    () => message.listMessages(ctx, conversationId, { cursor: badCursor }),
    (err: unknown) => {
      // Must be the typed AppError whose `.status` (src/http/errors.ts's
      // fastifyErrorHandler forwards this verbatim) is 400, never a raw
      // RangeError/other untyped error, which the same handler maps to 500.
      assert.ok(err instanceof ValidationError, `expected ValidationError, got ${(err as Error)?.constructor?.name}`);
      assert.equal((err as ValidationError).status, 400);
      return true;
    },
  );
});

test('adopting endpoint (message.listMessages): a well-formed cursor still paginates correctly', async () => {
  const setupCtx = buildCtx();
  const userAId = await insertUser(setupCtx);
  const userBId = await insertUser(setupCtx);
  const conversationId = await insertConversation(setupCtx, userAId, userBId);
  const ctx = buildCtx({ actor: userActor(userAId) });

  for (let i = 0; i < 3; i++) {
    await message.sendMessage(ctx, conversationId, `message number ${i}`);
  }

  const page1 = await message.listMessages(ctx, conversationId, { limit: 2 });
  assert.equal(page1.items.length, 2);
  assert.ok(page1.nextCursor);

  const page2 = await message.listMessages(ctx, conversationId, { cursor: page1.nextCursor!, limit: 2 });
  assert.equal(page2.items.length, 1);
  assert.equal(page2.nextCursor, null);

  const seenIds = new Set([...page1.items, ...page2.items].map((m) => m.id));
  assert.equal(seenIds.size, 3, 'paginating with the shared cursor helper must see every message exactly once');
});
