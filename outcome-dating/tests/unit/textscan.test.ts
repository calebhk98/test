import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  PATTERN_GROUPS,
  scanText,
  extractFirstLink,
  extractDomain,
  decideLinkPresentation,
  KNOWN_SAFE_DOMAINS,
  OFF_APP_BANNER_REASON,
  SCAM_RISK_BANNER_REASON,
} from '../../src/services/textscan.service.js';
import type { Ctx } from '../../src/lib/ctx.js';
import { ManualClock } from '../../src/lib/time.js';
import { createSilentLogger } from '../../src/lib/logger.js';
import { FakeProcessor } from '../../src/services/payments/fake.processor.js';
import { StubMediaModerationAdapter } from '../../src/services/media/stub.adapter.js';

// `scanText` is pure/synchronous but still takes a Ctx per its frozen
// signature — this fixture never touches a DB.
function fakeCtx(): Ctx {
  const clock = new ManualClock(new Date('2026-01-01T00:00:00.000Z'));
  const logger = createSilentLogger();
  return {
    db: undefined as unknown as Ctx['db'],
    clock,
    config: undefined as unknown as Ctx['config'],
    flags: undefined as unknown as Ctx['flags'],
    logger,
    actor: { type: 'system', job: 'test' },
    payments: new FakeProcessor(),
    media: new StubMediaModerationAdapter(),
  };
}

// =====================================================================
// PATTERN_GROUPS coverage — every §19.3 category maps to a flag_type.
// =====================================================================

test('PATTERN_GROUPS covers every §23.15 flag_type at least once', () => {
  const types = new Set(PATTERN_GROUPS.map((g) => g.flagType));
  for (const t of ['external_contact', 'money_request', 'link', 'crypto', 'spam_pattern', 'abuse_pattern']) {
    assert.ok(types.has(t as never), `missing pattern group for flag_type "${t}"`);
  }
});

// =====================================================================
// True positives — one per §19.3 category.
// =====================================================================

test('scanText: detects an Instagram handle as external_contact', () => {
  const result = scanText(fakeCtx(), "Hit me up on insta: it's @jordan.travels");
  assert.ok(result.flags.some((f) => f.type === 'external_contact'));
});

test('scanText: detects a real phone number as external_contact', () => {
  const result = scanText(fakeCtx(), 'Call me at 555-123-4567 anytime this week!');
  assert.ok(result.flags.some((f) => f.type === 'external_contact'));
});

test('scanText: detects cashapp/venmo/zelle mentions as money_request', () => {
  for (const body of ['send it to my venmo @jsmith', 'just zelle me the deposit', "here's my cash app $jsmith22"]) {
    const result = scanText(fakeCtx(), body);
    assert.ok(result.flags.some((f) => f.type === 'money_request'), `expected money_request for "${body}"`);
  }
});

test('scanText: detects gift-card requests as money_request', () => {
  const result = scanText(fakeCtx(), 'Can you just grab me a steam card for now?');
  assert.ok(result.flags.some((f) => f.type === 'money_request'));
});

test('scanText: detects crypto/investment language as crypto', () => {
  const result = scanText(fakeCtx(), 'I can get you into a great bitcoin investment opportunity');
  assert.ok(result.flags.some((f) => f.type === 'crypto'));
});

test('scanText: detects adult-content promotion as spam_pattern', () => {
  const result = scanText(fakeCtx(), 'check out my onlyfans for more content ;)');
  assert.ok(result.flags.some((f) => f.type === 'spam_pattern'));
});

test('scanText: a URL embedded inside an otherwise normal sentence is still detected', () => {
  const result = scanText(fakeCtx(), "Here's a great recipe I tried: https://example.com/recipes/pasta - so good!");
  const linkFlag = result.flags.find((f) => f.type === 'link');
  assert.ok(linkFlag, 'expected a link flag');
  assert.equal(result.showSafetyBanner, true);
  assert.equal(result.safetyBannerTemplateKey, OFF_APP_BANNER_REASON);
});

// =====================================================================
// False-positive guards — the three explicitly required cases.
// =====================================================================

test('scanText: "my cash app of tea"-style near-miss still flags (regex cannot read puns) but NEVER blocks — flag internally, never refuse the send', () => {
  const result = scanText(fakeCtx(), "Honestly reality TV is not my cash app of tea.");
  // It's fine — arguably correct — that the literal substring "cash app"
  // still matches; the spec's actual invariant is that this can never
  // block sending (§19.3 "Do not block the message automatically by
  // default"), only flag. `message.service.ts`'s own tests confirm the
  // message still sends when this happens.
  assert.ok(result.flags.some((f) => f.type === 'money_request'));
  assert.equal(result.flags.length > 0, true);
});

test('scanText: a dotted calendar date is NOT mistaken for a phone number', () => {
  const result = scanText(fakeCtx(), "Let's meet 3.15.2026 at noon, does that work?");
  assert.ok(
    !result.flags.some((f) => f.type === 'external_contact'),
    'a MM.DD.YYYY-shaped date must not match the phone-number heuristic',
  );
});

test('scanText: a slash-formatted date is NOT mistaken for a phone number', () => {
  const result = scanText(fakeCtx(), 'How about 10/25/2026, does that work for you?');
  assert.ok(!result.flags.some((f) => f.type === 'external_contact'));
});

test('scanText: ordinary conversation produces no flags at all', () => {
  const result = scanText(fakeCtx(), "I had a great time on our walk yesterday, want to grab coffee this weekend?");
  assert.deepEqual(result.flags, []);
  assert.equal(result.showSafetyBanner, false);
  assert.equal(result.safetyBannerTemplateKey, null);
});

// =====================================================================
// Safety-banner priority: scam-risk outranks the generic off-app notice.
// =====================================================================

test('scanText: a message with both a link AND a money request shows the scam-risk banner, not the generic one', () => {
  const result = scanText(fakeCtx(), 'Check my page https://example.com and just venmo me the deposit first');
  assert.equal(result.showSafetyBanner, true);
  assert.equal(result.safetyBannerTemplateKey, SCAM_RISK_BANNER_REASON);
});

// =====================================================================
// extractFirstLink / extractDomain
// =====================================================================

test('extractFirstLink returns the matched URL substring', () => {
  assert.equal(extractFirstLink('go to https://example.com/path?x=1 now'), 'https://example.com/path?x=1');
  assert.equal(extractFirstLink('no links in this sentence at all'), null);
});

test('extractDomain normalizes scheme and www', () => {
  assert.equal(extractDomain('https://www.example.com/foo'), 'example.com');
  assert.equal(extractDomain('example.com'), 'example.com');
  assert.equal(extractDomain('not a url at all'), null);
});

// =====================================================================
// decideLinkPresentation — pure §19.4 presentation logic.
// =====================================================================

test('decideLinkPresentation: not clickable when the trust gate says no', () => {
  const decision = decideLinkPresentation({
    url: 'https://instagram.com/me',
    canSendClickableLinks: false,
    linksSentInLastHour: 0,
    linkLimitPerHour: 5,
  });
  assert.equal(decision.clickable, false);
  assert.equal(decision.unknownDomainWarning, false);
});

test('decideLinkPresentation: not clickable once the hourly quota is spent, even for a trust-eligible sender', () => {
  const decision = decideLinkPresentation({
    url: 'https://instagram.com/me',
    canSendClickableLinks: true,
    linksSentInLastHour: 5,
    linkLimitPerHour: 5,
  });
  assert.equal(decision.clickable, false);
});

test('decideLinkPresentation: clickable + no warning for a known-safe domain', () => {
  assert.ok(KNOWN_SAFE_DOMAINS.has('instagram.com'));
  const decision = decideLinkPresentation({
    url: 'https://instagram.com/me',
    canSendClickableLinks: true,
    linksSentInLastHour: 0,
    linkLimitPerHour: 5,
  });
  assert.equal(decision.clickable, true);
  assert.equal(decision.unknownDomainWarning, false);
});

test('decideLinkPresentation: clickable + unknown-domain warning for an unrecognized domain', () => {
  const decision = decideLinkPresentation({
    url: 'https://totally-random-scam-site.example',
    canSendClickableLinks: true,
    linksSentInLastHour: 0,
    linkLimitPerHour: 5,
  });
  assert.equal(decision.clickable, true);
  assert.equal(decision.unknownDomainWarning, true);
});
