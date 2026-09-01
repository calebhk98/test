/**
 * tests/unit/altText.test.ts — the accessibility suite:
 *
 *   1. photo alt text (src/services/photoAltText.service.ts) — travels
 *      with the photo everywhere it's fetched, ownership-checked,
 *      clearable, batch-readable.
 *   2. every status carries a non-colour label
 *      (src/domain/i18n/statusLabels.ts) — full domain coverage, tone is
 *      never a colour name, labels degrade to English rather than
 *      throwing for an untranslated locale.
 *   3. static-scan guards mirroring tests/unit/copyGuard.test.ts's own
 *      technique: no emoji/symbol-only meaning in this build's catalog,
 *      and no pre-formatted relative-time string anywhere in the
 *      serializers this repo already ships (a regression guard on an
 *      already-true property, per the task brief: "verify and keep it
 *      that way").
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { NotFoundError } from '../../src/lib/errors.js';
import { setupTestDatabase, teardownTestDatabase, buildCtx, createUser, createPhoto, userActor } from './testCtxRetention.js';
import {
  setPhotoAltText,
  clearPhotoAltText,
  getPhotoAltText,
  getAltTextForPhotos,
} from '../../src/services/photoAltText.service.js';
import { STATUS_REGISTRY, describeStatus } from '../../src/domain/i18n/statusLabels.js';
import type { StatusDomain } from '../../src/domain/i18n/statusLabels.js';
import { CATALOGS } from '../../src/domain/i18n/catalog.js';
import type pg from 'pg';

let pool: pg.Pool;

before(async () => {
  pool = await setupTestDatabase('alt_text');
});

after(async () => {
  await teardownTestDatabase();
});

// -------------------------------------------------------------------------
// 1. Photo alt text
// -------------------------------------------------------------------------

test('setPhotoAltText: an owner can describe their own photo, and the description round-trips', async () => {
  const userId = await createUser(pool);
  const photoId = await createPhoto(pool, userId);
  const ctx = buildCtx({ actor: userActor(userId) });

  const result = await setPhotoAltText(ctx, photoId, { altText: 'A person laughing on a hiking trail at sunrise.' });
  assert.equal(result.altText, 'A person laughing on a hiking trail at sunrise.');

  const fetched = await getPhotoAltText(ctx, photoId);
  assert.equal(fetched?.altText, 'A person laughing on a hiking trail at sunrise.');
});

test('setPhotoAltText: rejects someone else\'s photo with NotFoundError, not silent success', async () => {
  const owner = await createUser(pool);
  const stranger = await createUser(pool);
  const photoId = await createPhoto(pool, owner);
  const ctx = buildCtx({ actor: userActor(stranger) });

  await assert.rejects(() => setPhotoAltText(ctx, photoId, { altText: 'Someone else\'s photo.' }), NotFoundError);
});

test('setPhotoAltText: rejects empty/whitespace-only text — a photo should read as "not described", never "described with nothing"', async () => {
  const userId = await createUser(pool);
  const photoId = await createPhoto(pool, userId);
  const ctx = buildCtx({ actor: userActor(userId) });

  await assert.rejects(() => setPhotoAltText(ctx, photoId, { altText: '   ' }));
});

test('clearPhotoAltText: withdraws a description back to null, distinct from never having set one', async () => {
  const userId = await createUser(pool);
  const photoId = await createPhoto(pool, userId);
  const ctx = buildCtx({ actor: userActor(userId) });

  await setPhotoAltText(ctx, photoId, { altText: 'A description to withdraw.' });
  await clearPhotoAltText(ctx, photoId);

  const fetched = await getPhotoAltText(ctx, photoId);
  assert.equal(fetched?.altText, null);
});

test('getAltTextForPhotos: batch read returns every requested photo, described or not, in one call — the shape any serializer needs to make alt text travel with the photo', async () => {
  const userId = await createUser(pool);
  const described = await createPhoto(pool, userId, { isPrimary: true });
  const undescribed = await createPhoto(pool, userId, { isPrimary: false });
  const ctx = buildCtx({ actor: userActor(userId) });

  await setPhotoAltText(ctx, described, { altText: 'A description that must travel with this exact photo id.' });

  const map = await getAltTextForPhotos(ctx, [described, undescribed]);
  assert.equal(map.size, 2, 'every requested id is present, whether described or not');
  assert.equal(map.get(described)?.altText, 'A description that must travel with this exact photo id.');
  assert.equal(map.get(undescribed)?.altText, null);
});

test('getAltTextForPhotos: an empty request never touches the database and returns an empty map', async () => {
  const userId = await createUser(pool);
  const ctx = buildCtx({ actor: userActor(userId) });
  const map = await getAltTextForPhotos(ctx, []);
  assert.equal(map.size, 0);
});

// -------------------------------------------------------------------------
// 2. Every status carries a non-colour label
// -------------------------------------------------------------------------

const EXPECTED_DOMAIN_VALUES: Record<StatusDomain, string[]> = {
  userStatus: ['active', 'suspended', 'deleted'],
  trustLevel: ['limited', 'standard', 'trusted', 'elite'],
  photoModerationStatus: ['pending', 'approved', 'rejected', 'flagged'],
  interestStatus: ['pending', 'accepted', 'declined', 'expired', 'canceled'],
  conversationStatus: ['active', 'cooling', 'archived', 'established'],
  notificationStatus: ['pending', 'sent', 'failed', 'read'],
  dateProposalStatus: [
    'draft',
    'pending_acceptance',
    'accepted',
    'declined',
    'expired',
    'canceled',
    'payment_failed',
    'charged',
    'ticketed',
    'completed',
    'completed_unverified',
    'no_show',
    'refunded',
    'disputed',
  ],
  paymentHoldStatus: ['pending', 'authorized', 'capture_pending', 'captured', 'released', 'failed', 'refunded'],
  voucherStatus: ['issued', 'redeemed', 'expired', 'canceled'],
  moderationActionType: ['none', 'warning', 'restriction', 'shadowban', 'suspension'],
  appealStatus: ['pending', 'approved', 'rejected'],
};

test('STATUS_REGISTRY covers every real status value from src/domain/types.ts, for every domain', () => {
  for (const [domain, values] of Object.entries(EXPECTED_DOMAIN_VALUES)) {
    const registered = STATUS_REGISTRY[domain];
    assert.ok(registered, `domain "${domain}" is missing from STATUS_REGISTRY`);
    for (const value of values) {
      assert.ok(registered[value], `${domain}.${value} has no status descriptor`);
    }
  }
});

test('describeStatus: tone is always one of the four abstract categories, never a colour word', () => {
  const COLOUR_WORDS = /\b(red|green|yellow|amber|orange|blue|colou?r)\b/i;
  for (const [domain, defs] of Object.entries(STATUS_REGISTRY)) {
    for (const [value, def] of Object.entries(defs)) {
      assert.ok(['neutral', 'positive', 'caution', 'critical'].includes(def.tone), `${domain}.${value} has an invalid tone`);
      assert.ok(!COLOUR_WORDS.test(def.tone), `${domain}.${value}'s tone reads like a colour name: "${def.tone}"`);
    }
  }
});

test('describeStatus: returns the raw status unchanged, plus a real label, for a shipped locale', () => {
  const result = describeStatus('dateProposalStatus', 'payment_failed', 'en');
  assert.equal(result.status, 'payment_failed');
  assert.equal(result.tone, 'critical');
  assert.equal(result.label, 'Payment failed');

  const es = describeStatus('dateProposalStatus', 'payment_failed', 'es');
  assert.equal(es.label, 'El pago falló');
});

test('describeStatus: an unshipped locale degrades to the English label rather than throwing', () => {
  const result = describeStatus('trustLevel', 'trusted', 'fr'); // fr is registered (locales.ts) but has no STATUS_REGISTRY labels
  assert.equal(result.label, 'Trusted', 'falls back to English, not a thrown error or a raw key');
});

test('describeStatus: an unknown (domain, value) pair throws — a code bug, not a runtime condition to hide', () => {
  assert.throws(() => describeStatus('trustLevel', 'nonexistent_level', 'en'));
});

test('no abbreviation-shaped labels in STATUS_REGISTRY (a screen reader must be able to read every label aloud)', () => {
  const SUSPICIOUS_ABBREVIATIONS = /\b(pmt|acct|msg|rcvd|apprv|rej|cfg|abbr)\b\.?/i;
  for (const [domain, defs] of Object.entries(STATUS_REGISTRY)) {
    for (const [value, def] of Object.entries(defs)) {
      for (const [locale, label] of Object.entries(def.labels)) {
        assert.ok(!SUSPICIOUS_ABBREVIATIONS.test(label), `${domain}.${value} (${locale}) label looks abbreviated: "${label}"`);
      }
    }
  }
});

// -------------------------------------------------------------------------
// 3a. No emoji / symbol-only meaning in this build's own copy catalog.
// -------------------------------------------------------------------------

/** Matches any character in a Unicode emoji block — deliberately broad (better to over-flag during authoring than ship an emoji that slips through a narrower range). */
const EMOJI_PATTERN = /[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}\u{1F000}-\u{1F0FF}\u{2190}-\u{21FF}\u{2B00}-\u{2BFF}]/u;

test('the copy catalog contains no emoji or symbol standing in for meaning', () => {
  for (const [locale, catalog] of Object.entries(CATALOGS)) {
    for (const [key, entry] of Object.entries(catalog)) {
      const strings = entry.kind === 'text' ? [entry.text] : Object.values(entry.forms);
      for (const s of strings) {
        assert.ok(!EMOJI_PATTERN.test(s), `${locale}.${key} contains an emoji/symbol: ${JSON.stringify(s)}`);
      }
    }
  }
});

test('the status label registry also contains no emoji or symbol standing in for meaning', () => {
  for (const [domain, defs] of Object.entries(STATUS_REGISTRY)) {
    for (const [value, def] of Object.entries(defs)) {
      for (const [locale, label] of Object.entries(def.labels)) {
        assert.ok(!EMOJI_PATTERN.test(label), `${domain}.${value} (${locale}) contains an emoji/symbol: ${JSON.stringify(label)}`);
      }
    }
  }
});

// -------------------------------------------------------------------------
// 3b. Structured, not pre-formatted, values — regression guard.
// Same static-scan technique as tests/unit/copyGuard.test.ts: extract every
// quoted string literal from src/http/serializers/**, fail if one looks
// like a pre-rendered relative-time string a server should never emit.
// -------------------------------------------------------------------------

const SERIALIZERS_DIR = join(import.meta.dirname, '..', '..', 'src', 'http', 'serializers');
const RELATIVE_TIME_PATTERN = /\b(\d+\s*(min(ute)?s?|hrs?|hours?|days?)\s*ago|just now|yesterday|moments? ago)\b/i;

function listTsFiles(dir: string): string[] {
  const out: string[] = [];
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) out.push(...listTsFiles(full));
    else if (entry.endsWith('.ts')) out.push(full);
  }
  return out;
}

function extractStringLiterals(source: string): string[] {
  const withoutComments = source.replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/.*$/gm, '');
  const pattern = /'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*"|`(?:[^`\\]|\\.)*`/g;
  const literals: string[] = [];
  let m: RegExpExecArray | null;
  while ((m = pattern.exec(withoutComments)) !== null) literals.push(m[0].slice(1, -1));
  return literals;
}

test('no serializer emits a pre-rendered relative-time string — timestamps stay structured ISO-8601 (regression guard, property already held before this build)', () => {
  const violations: Array<{ file: string; literal: string }> = [];
  for (const file of listTsFiles(SERIALIZERS_DIR)) {
    for (const literal of extractStringLiterals(readFileSync(file, 'utf8'))) {
      if (RELATIVE_TIME_PATTERN.test(literal)) violations.push({ file, literal });
    }
  }
  assert.deepEqual(violations, [], `Found pre-formatted relative-time string(s): ${JSON.stringify(violations)}`);
});

test('the relative-time scanner actually catches a violation (not a silent no-op)', () => {
  const fixture = "const label = '5 minutes ago';";
  const literals = extractStringLiterals(fixture);
  assert.ok(literals.some((l) => RELATIVE_TIME_PATTERN.test(l)), 'the scanner must flag an obvious relative-time literal');
});
