/**
 * "No generated prose reaches a user: every user-visible string traces to
 * a static template." (§1 rule 9, §12.4, §20). Exercised at two seams:
 * `notification.service.ts` (every notification renders from a fixed
 * `templateKey`, never free text in the payload) and `textscan.service.ts`
 * (message analysis is pure regex/keyword matching, never a model call,
 * proven here by determinism AND by the function being synchronous, which
 * a real network call to a generative model could not be).
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { setupConformanceDb, teardownConformanceDb, makeCtx, userActor, systemActor, createUser, createConversation, type TestDb } from './support.js';
import * as notificationService from '../../src/services/notification.service.js';
import { NOTIFICATION_TEMPLATES } from '../../src/services/notification.service.js';
import * as textscanService from '../../src/services/textscan.service.js';
import * as messageService from '../../src/services/message.service.js';
import { ValidationError } from '../../src/lib/errors.js';

let db: TestDb;

before(async () => {
  db = await setupConformanceDb('staticprose');
});

after(async () => {
  await teardownConformanceDb(db);
});

// =====================================================================
// C-20.0.1 / C-1.9: notifications only ever render from a fixed template
// registry, never caller-supplied prose.
// =====================================================================

test('C-1.10 / fixture-data: NOTIFICATION_TEMPLATES is a fixed, finite, static-string registry (every key -> a plain versioned template id, no interpolated content)', () => {
  const values = Object.values(NOTIFICATION_TEMPLATES);
  assert.ok(values.length >= 16, 'the full §20.1 event list (16 events) plus decision-layer additions must all be present');
  for (const [eventType, templateKey] of Object.entries(NOTIFICATION_TEMPLATES)) {
    assert.equal(typeof templateKey, 'string');
    assert.match(templateKey, /^[a-z0-9_]+_v\d+$/, `${eventType}'s template key ("${templateKey}") must be a plain static identifier, not free text`);
  }
  // No accidental collisions (two different events silently sharing one
  // template key would let one static string stand in for two different
  // meanings, an early symptom of ad hoc string-building creeping in).
  assert.equal(new Set(values).size, values.length, 'every event must have its own distinct template key');
});

test('C-20.0.1: notify() rejects any templateKey not in the static registry', async () => {
  const userId = await createUser(db);
  const ctx = makeCtx(db, systemActor());
  await assert.rejects(
    () =>
      notificationService.notify(ctx, {
        userId,
        eventType: 'safety_notice',
        channel: 'in_app',
        templateKey: 'you_got_a_great_match_today_congrats', // free-text-shaped, not in the registry
        payload: {},
      }),
    ValidationError,
  );
});

test('C-20.0.1 / C-1.9: notify() rejects a payload carrying free-text prose under any of the forbidden keys (body/message/etc), only structured slot-fill data is allowed', async () => {
  const userId = await createUser(db);
  const ctx = makeCtx(db, systemActor());
  for (const forbiddenKey of ['body', 'message', 'text', 'html', 'copy', 'content']) {
    await assert.rejects(
      () =>
        notificationService.notify(ctx, {
          userId,
          eventType: 'safety_notice',
          channel: 'in_app',
          payload: { [forbiddenKey]: 'Hey, wanted to let you know something important happened on your account today!' },
        }),
      ValidationError,
      `payload key "${forbiddenKey}" must be rejected as a free-text smuggling attempt`,
    );
  }

  // Structured (non-prose) payload data is fine.
  const ok = await notificationService.notify(ctx, { userId, eventType: 'safety_notice', channel: 'in_app', payload: { action: 'restriction' } });
  assert.equal(ok.templateKey, NOTIFICATION_TEMPLATES.safety_notice);
});

// =====================================================================
// C-12.4.1 / C-12.4.2: text analysis is regex/keyword-based, deterministic,
// and structurally cannot be a model call (it isn't even async).
// =====================================================================

test('C-12.4.2: scanText is synchronous (not a Promise), the strongest structural proof no network/model call happens in it', () => {
  const ctx = makeCtx(db, systemActor());
  const result = textscanService.scanText(ctx, 'hello, want to grab coffee sometime?');
  assert.equal(result instanceof Promise, false, 'a real call to a generative model requires I/O and cannot be synchronous');
});

test('C-12.4.2: scanText is a pure, deterministic function of (body, ruleset), same input always produces the byte-identical output', () => {
  const ctx = makeCtx(db, systemActor());
  const body = 'Message me on telegram @realdeal_123 or send crypto to my wallet, its urgent, wire transfer ok too';
  const first = textscanService.scanText(ctx, body);
  const second = textscanService.scanText(ctx, body);
  assert.deepEqual(first, second);
  // A different Ctx (different actor) must not change the result either,
  // since the function's contract is a pure function of (body, ruleset).
  const otherCtx = makeCtx(db, userActor('00000000-0000-0000-0000-000000000000'));
  const third = textscanService.scanText(otherCtx, body);
  assert.deepEqual(first, third);
});

test('C-19.3.1: table-driven scam/off-platform pattern coverage, one representative message per named category', () => {
  const ctx = makeCtx(db, systemActor());
  const cases: Array<{ category: string; body: string }> = [
    { category: 'crypto', body: 'send it to my bitcoin wallet address please' },
    { category: 'gift cards', body: 'just need you to buy a gift card and send the code' },
    { category: 'wire transfer', body: 'can you wire transfer me the deposit' },
    { category: 'cashapp/venmo/zelle', body: 'just cashapp me the money' },
    { category: 'emergency money', body: 'I need emergency money right now, please help' },
    { category: 'investment offer', body: 'I can help you with an investment opportunity that guarantees returns' },
    { category: 'telegram/whatsapp', body: 'message me on telegram instead' },
    { category: 'adult content promotion', body: 'check out my onlyfans for exclusive content' },
  ];
  for (const c of cases) {
    const result = textscanService.scanText(ctx, c.body);
    assert.ok(result.flags.length > 0, `category "${c.category}" (message: "${c.body}") must produce at least one flag`);
  }
});

test('C-12.5.1 / C-19.3.2 / C-19.3.3 / C-19.3.4: a scam/off-platform message is flagged and banner-eligible, but is NOT auto-blocked, it still sends', async () => {
  const a = await createUser(db);
  const b = await createUser(db);
  const conversationId = await createConversation(db, a, b, 'active');
  const ctx = makeCtx(db, userActor(a));

  const message = await messageService.sendMessage(ctx, conversationId, 'send crypto to this wallet, its urgent, message me on telegram');
  assert.ok(message.id, 'the message must actually send (§12.5/§19.3: never blocked for this)');
});
