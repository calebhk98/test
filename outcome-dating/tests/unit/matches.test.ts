/**
 * matches.service.ts unit tests. Product-owner finding #1: "You cannot see
 * your matches", a match list, click-through data, ordering, and cursor
 * pagination including a never-messaged match.
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import * as interestService from '../../src/services/interest.service.js';
import * as messageService from '../../src/services/message.service.js';
import * as discoveryService from '../../src/services/discovery.service.js';
import * as matchesService from '../../src/services/matches.service.js';
import { ForbiddenError, NotFoundError } from '../../src/lib/errors.js';
import {
  setupTestDb,
  teardownTestDb,
  makeCtx,
  userActor,
  createUserWithProfile,
  addApprovedPhoto,
  type TestDb,
} from './testHarnessMatch.js';

let db: TestDb;

before(async () => {
  db = await setupTestDb('matches');
});

after(async () => {
  await teardownTestDb(db);
});

/** Sends an interest A -> B and has B accept it, returning the conversationId. */
async function makeMatch(userAId: string, userBId: string): Promise<string> {
  const interest = await interestService.sendInterest(makeCtx(db, userActor(userAId)), userBId);
  const { conversation } = await interestService.acceptInterest(makeCtx(db, userActor(userBId)), interest.id);
  return conversation.id;
}

// =====================================================================
// Appears immediately on accept; click-through data; no coordinate leak.
// =====================================================================

test('a match appears in the list as soon as an interest is accepted', async () => {
  const a = await createUserWithProfile(db, { displayName: 'Alice', gender: 'woman', seeking: 'men' });
  const b = await createUserWithProfile(db, { displayName: 'Bob', gender: 'man', seeking: 'women', lat: 39.9, lon: -89.5 });
  await addApprovedPhoto(db, b, 'https://example.test/bob-primary.jpg', { primary: true });

  const conversationId = await makeMatch(a, b);

  const page = await matchesService.listMyMatches(makeCtx(db, userActor(a)));
  assert.equal(page.items.length, 1);
  const item = page.items[0]!;
  assert.equal(item.conversationId, conversationId);
  assert.equal(item.matchedUserId, b);
  assert.equal(item.displayName, 'Bob');
  assert.equal(item.primaryPhotoUrl, 'https://example.test/bob-primary.jpg');
  assert.equal(item.conversationStatus, 'active');
  assert.equal(item.lastMessagePreview, null);
  assert.equal(item.lastMessageAt, null);
  assert.equal(item.unreadCount, 0);
  assert.ok(item.matchedAt);
  assert.ok(item.lastActivityAt);

  // Click-through: no raw coordinate anywhere on the row, only the
  // already-bucketed distance, same guarantee `profile.service` makes.
  assert.equal(typeof item.approximateDistanceKm, 'number');
  assert.ok(!('latitude' in item));
  assert.ok(!('longitude' in item));

  // Click-through target: matches.getMyMatch reuses the identical row shape.
  const detail = await matchesService.getMyMatch(makeCtx(db, userActor(a)), conversationId);
  assert.deepEqual(detail, item);
});

test('last message preview/time and unread count update as messages are sent and read', async () => {
  const a = await createUserWithProfile(db, { displayName: 'Carol' });
  const b = await createUserWithProfile(db, { displayName: 'Dave' });
  const conversationId = await makeMatch(a, b);

  const longBody = 'x'.repeat(200);
  await messageService.sendMessage(makeCtx(db, userActor(b)), conversationId, longBody);

  let page = await matchesService.listMyMatches(makeCtx(db, userActor(a)));
  let item = page.items.find((m) => m.conversationId === conversationId)!;
  assert.equal(item.lastMessagePreview!.length, 141); // 140 chars + ellipsis
  assert.ok(item.lastMessagePreview!.endsWith('…'));
  assert.ok(item.lastMessageAt);
  assert.equal(item.unreadCount, 1); // A hasn't read B's message yet

  // B's own view: not unread from B's perspective (B sent it).
  const bPage = await matchesService.listMyMatches(makeCtx(db, userActor(b)));
  const bItem = bPage.items.find((m) => m.conversationId === conversationId)!;
  assert.equal(bItem.unreadCount, 0);

  const messages = await messageService.listMessages(makeCtx(db, userActor(a)), conversationId, {});
  await messageService.markRead(makeCtx(db, userActor(a)), conversationId, messages.items[0]!.id);

  page = await matchesService.listMyMatches(makeCtx(db, userActor(a)));
  item = page.items.find((m) => m.conversationId === conversationId)!;
  assert.equal(item.unreadCount, 0);
});

// =====================================================================
// Ordering: most recent activity first; a never-messaged match is not
// buried under an older, quieter, messaged conversation.
// =====================================================================

test('ordering: most recent activity first, and a brand-new never-messaged match is not buried', async () => {
  const me = await createUserWithProfile(db, { displayName: 'Order Tester' });
  const older = await createUserWithProfile(db, { displayName: 'Older Match' });
  const newest = await createUserWithProfile(db, { displayName: 'Newest No-Message Match' });

  // Older match, with a message sent a while ago.
  const olderConvo = await makeMatch(me, older);
  await messageService.sendMessage(makeCtx(db, userActor(me)), olderConvo, 'hello from a while back');

  db.clock.advanceDays(3);

  // Brand-new match made just now, with zero messages.
  const newestConvo = await makeMatch(me, newest);

  const page = await matchesService.listMyMatches(makeCtx(db, userActor(me)));
  const ids = page.items.map((m) => m.conversationId);
  // The never-messaged brand-new match sorts ABOVE the older, message-having one.
  assert.deepEqual(ids, [newestConvo, olderConvo]);
});

// =====================================================================
// Cursor pagination.
// =====================================================================

test('cursor pagination walks every match exactly once, in stable order', async () => {
  const me = await createUserWithProfile(db, { displayName: 'Pager' });
  const others: string[] = [];
  for (let i = 0; i < 5; i++) {
    const other = await createUserWithProfile(db, { displayName: `Pager Match ${i}` });
    others.push(await makeMatch(me, other));
    db.clock.advanceMs(1000); // distinct matchedAt per row for a deterministic order
  }

  const seen: string[] = [];
  let cursor: string | null | undefined;
  do {
    const page = await matchesService.listMyMatches(makeCtx(db, userActor(me)), { cursor: cursor ?? undefined, limit: 2 });
    seen.push(...page.items.map((m) => m.conversationId));
    cursor = page.nextCursor;
  } while (cursor);

  assert.equal(seen.length, others.length);
  assert.deepEqual(new Set(seen), new Set(others));
  // No duplicates across pages.
  assert.equal(new Set(seen).size, seen.length);
  // Most-recent-first: reverse of insertion order.
  assert.deepEqual(seen, [...others].reverse());
});

// =====================================================================
// Never-matched users are unreachable through this path.
// =====================================================================

test('a user with no conversation is never reachable via getMyMatch', async () => {
  const me = await createUserWithProfile(db, { displayName: 'Alone' });
  const stranger = await createUserWithProfile(db, { displayName: 'Stranger' });
  void stranger;

  await assert.rejects(() => matchesService.getMyMatch(makeCtx(db, userActor(me)), '00000000-0000-0000-0000-000000000000'), NotFoundError);
});

test('a non-participant cannot read someone else\'s match via getMyMatch (404, existence not leaked)', async () => {
  const a = await createUserWithProfile(db, { displayName: 'Eve' });
  const b = await createUserWithProfile(db, { displayName: 'Frank' });
  const outsider = await createUserWithProfile(db, { displayName: 'Outsider' });
  const conversationId = await makeMatch(a, b);

  await assert.rejects(() => matchesService.getMyMatch(makeCtx(db, userActor(outsider)), conversationId), NotFoundError);
});

test('a blocked match is dropped from the list rather than erroring the whole page', async () => {
  const a = await createUserWithProfile(db, { displayName: 'Grace' });
  const b = await createUserWithProfile(db, { displayName: 'Henry' });
  const conversationId = await makeMatch(a, b);

  await discoveryService.blockUser(makeCtx(db, userActor(a)), b);

  const page = await matchesService.listMyMatches(makeCtx(db, userActor(a)));
  assert.ok(!page.items.some((m) => m.conversationId === conversationId));

  await assert.rejects(() => matchesService.getMyMatch(makeCtx(db, userActor(a)), conversationId), ForbiddenError);
});
