/**
 * tests/unit/adapterSelection.test.ts, `src/config/adapters.ts`'s
 * per-environment selection functions and the readiness report they feed.
 *
 * Companion to tests/unit/productionGuard.test.ts, which covers the
 * fail-fast startup guard (one test per production misconfiguration).
 * This file covers the selection mechanism itself: that every capability
 * defaults to its fake/stub/in-memory adapter outside production with
 * zero configuration, that a correctly-configured production environment
 * actually constructs the real adapter class, and that the media-
 * moderation provider registry (the "configuration seam" the build brief
 * asked for) works both empty (today's real state) and populated (proving
 * the seam is real, not aspirational).
 *
 * No database is needed for any test in this file, every function under
 * test is a pure function of `Env`.
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { getEnv, _resetEnvCacheForTests } from '../../src/config/env.js';
import {
  selectPaymentProcessor,
  selectMediaModerationAdapter,
  selectPushSender,
  selectEmailSender,
  selectSmsSender,
  buildReadinessReport,
  registerMediaModerationProvider,
  _clearMediaModerationProvidersForTests,
} from '../../src/config/adapters.js';
import type { ImageModerationPort, PhotoAnalysisInput, PhotoAnalysisResult } from '../../src/services/media/moderation.port.js';

/** Saves the given env var keys, applies `overrides` (a value of `undefined` deletes the key), resets the cached `Env`, runs `fn`, then restores every saved key and resets the cache again, mirrors the pattern already used in tests/unit/decisionsConfig.test.ts. */
async function withEnv<T>(overrides: Record<string, string | undefined>, fn: () => T | Promise<T>): Promise<T> {
  const saved: Record<string, string | undefined> = {};
  for (const key of Object.keys(overrides)) saved[key] = process.env[key];
  try {
    for (const [key, value] of Object.entries(overrides)) {
      if (value === undefined) delete process.env[key];
      else process.env[key] = value;
    }
    _resetEnvCacheForTests();
    return await fn();
  } finally {
    for (const [key, value] of Object.entries(saved)) {
      if (value === undefined) delete process.env[key];
      else process.env[key] = value;
    }
    _resetEnvCacheForTests();
  }
}

const ALL_MANAGED_KEYS = [
  'NODE_ENV',
  'DATABASE_URL',
  'AUTH_TOKEN_SECRET',
  'VOUCHER_QR_SECRET',
  'PAYMENT_PROCESSOR',
  'STRIPE_SECRET_KEY',
  'STRIPE_WEBHOOK_SECRET',
  'MEDIA_MODERATION_PROVIDER',
  'PUSH_PROVIDER',
  'FCM_SERVICE_ACCOUNT_JSON',
  'APNS_KEY_ID',
  'APNS_TEAM_ID',
  'APNS_SIGNING_KEY',
  'APNS_BUNDLE_ID',
  'EMAIL_PROVIDER',
  'SES_REGION',
  'SES_FROM_ADDRESS',
  'SMS_PROVIDER',
  'TWILIO_ACCOUNT_SID',
  'TWILIO_AUTH_TOKEN',
  'TWILIO_FROM_NUMBER',
] as const;

/** Clears every managed key so a test starts from a clean, fully-default env (equivalent to none of these ever being set in the deployment). */
function clearAllOverrides(): Record<string, undefined> {
  return Object.fromEntries(ALL_MANAGED_KEYS.map((k) => [k, undefined]));
}

// =====================================================================
// Outside production: fakes are the effortless default, zero config.
// =====================================================================

test('selectPaymentProcessor: development with no env vars set returns FakeProcessor', async () => {
  await withEnv({ ...clearAllOverrides(), NODE_ENV: 'development' }, () => {
    const processor = selectPaymentProcessor(getEnv());
    assert.equal(processor.name, 'fake');
  });
});

test('selectPaymentProcessor: test env with no env vars set returns FakeProcessor', async () => {
  await withEnv({ ...clearAllOverrides(), NODE_ENV: 'test' }, () => {
    const processor = selectPaymentProcessor(getEnv());
    assert.equal(processor.name, 'fake');
  });
});

test('selectMediaModerationAdapter: development returns StubMediaModerationAdapter with no env vars set', async () => {
  await withEnv({ ...clearAllOverrides(), NODE_ENV: 'development' }, () => {
    const media = selectMediaModerationAdapter(getEnv());
    assert.equal(media.name, 'stub');
  });
});

test('selectPushSender / selectEmailSender / selectSmsSender: development returns the fake senders with no env vars set', async () => {
  await withEnv({ ...clearAllOverrides(), NODE_ENV: 'development' }, () => {
    assert.equal(selectPushSender(getEnv()).name, 'fake');
    assert.equal(selectEmailSender(getEnv()).name, 'fake');
    assert.equal(selectSmsSender(getEnv()).name, 'fake');
  });
});

test('buildReadinessReport: development with nothing configured reports every capability as fake but ok', async () => {
  await withEnv({ ...clearAllOverrides(), NODE_ENV: 'development' }, () => {
    const report = buildReadinessReport(getEnv());
    assert.equal(report.ok, true);
    const fakeCapabilities = report.entries.filter((e) => e.isFake).map((e) => e.capability);
    assert.deepEqual(
      new Set(fakeCapabilities),
      new Set(['payments', 'mediaModeration', 'pushNotifications', 'emailNotifications', 'smsNotifications']),
    );
    for (const entry of report.entries) assert.equal(entry.ok, true, `${entry.capability} should be ok in development`);
  });
});

// =====================================================================
// Production, correctly configured: the REAL adapter is constructed.
// =====================================================================

test('selectPaymentProcessor: production with PAYMENT_PROCESSOR=stripe and both secrets set returns StripeProcessor', async () => {
  await withEnv(
    { ...clearAllOverrides(), NODE_ENV: 'production', PAYMENT_PROCESSOR: 'stripe', STRIPE_SECRET_KEY: 'sk_test_marker', STRIPE_WEBHOOK_SECRET: 'whsec_marker' },
    () => {
      const processor = selectPaymentProcessor(getEnv());
      assert.equal(processor.name, 'stripe');
    },
  );
});

test('selectPushSender: production with PUSH_PROVIDER=fcm and credentials returns FcmPushSender', async () => {
  await withEnv({ ...clearAllOverrides(), NODE_ENV: 'production', PUSH_PROVIDER: 'fcm', FCM_SERVICE_ACCOUNT_JSON: '{"marker":true}' }, () => {
    assert.equal(selectPushSender(getEnv()).name, 'fcm');
  });
});

test('selectPushSender: production with PUSH_PROVIDER=apns and full credentials returns ApnsPushSender', async () => {
  await withEnv(
    {
      ...clearAllOverrides(),
      NODE_ENV: 'production',
      PUSH_PROVIDER: 'apns',
      APNS_KEY_ID: 'key-marker',
      APNS_TEAM_ID: 'team-marker',
      APNS_SIGNING_KEY: 'signing-marker',
      APNS_BUNDLE_ID: 'com.example.app',
    },
    () => {
      assert.equal(selectPushSender(getEnv()).name, 'apns');
    },
  );
});

test('selectEmailSender: production with EMAIL_PROVIDER=ses and settings returns SesEmailSender', async () => {
  await withEnv({ ...clearAllOverrides(), NODE_ENV: 'production', EMAIL_PROVIDER: 'ses', SES_REGION: 'us-east-1', SES_FROM_ADDRESS: 'noreply@example.com' }, () => {
    assert.equal(selectEmailSender(getEnv()).name, 'ses');
  });
});

test('selectSmsSender: production with SMS_PROVIDER=twilio and credentials returns TwilioSmsSender', async () => {
  await withEnv(
    { ...clearAllOverrides(), NODE_ENV: 'production', SMS_PROVIDER: 'twilio', TWILIO_ACCOUNT_SID: 'AC-marker', TWILIO_AUTH_TOKEN: 'auth-marker', TWILIO_FROM_NUMBER: '+15550000000' },
    () => {
      assert.equal(selectSmsSender(getEnv()).name, 'twilio');
    },
  );
});

// =====================================================================
// Media moderation provider registry, the "configuration seam".
// =====================================================================

test('media moderation registry: empty registry means selectMediaModerationAdapter always throws in production, for any provider name', async () => {
  _clearMediaModerationProvidersForTests();
  await withEnv({ ...clearAllOverrides(), NODE_ENV: 'production', MEDIA_MODERATION_PROVIDER: 'some_vision_api' }, () => {
    assert.throws(() => selectMediaModerationAdapter(getEnv()), /mediaModeration/);
  });
});

test('media moderation registry: registering a real provider makes it selectable in production', async () => {
  _clearMediaModerationProvidersForTests();
  try {
    const fakeRealAdapter: ImageModerationPort = {
      name: 'test_real_provider',
      async analyzePhoto(_input: PhotoAnalysisInput): Promise<PhotoAnalysisResult> {
        throw new Error('not called in this test');
      },
    };
    registerMediaModerationProvider('test_real_provider', () => fakeRealAdapter);

    await withEnv({ ...clearAllOverrides(), NODE_ENV: 'production', MEDIA_MODERATION_PROVIDER: 'test_real_provider' }, () => {
      const media = selectMediaModerationAdapter(getEnv());
      assert.equal(media.name, 'test_real_provider');
      assert.equal(media, fakeRealAdapter);

      const report = buildReadinessReport(getEnv());
      const entry = report.entries.find((e) => e.capability === 'mediaModeration')!;
      assert.equal(entry.ok, true);
      assert.equal(entry.isFake, false);
      assert.equal(entry.selected, 'test_real_provider');
    });
  } finally {
    _clearMediaModerationProvidersForTests();
  }
});

test('media moderation registry: "stub" can never be registered as a real provider', () => {
  _clearMediaModerationProvidersForTests();
  try {
    assert.throws(() => registerMediaModerationProvider('stub', () => {
      throw new Error('never constructed');
    }));
  } finally {
    _clearMediaModerationProvidersForTests();
  }
});

// =====================================================================
// Exhaustiveness / totality of the readiness report.
// =====================================================================

test('buildReadinessReport: always reports exactly the 8 expected capabilities, in production and outside it', async () => {
  const expected = new Set([
    'payments',
    'mediaModeration',
    'pushNotifications',
    'emailNotifications',
    'smsNotifications',
    'authTokenSecret',
    'voucherSecret',
    'database',
  ]);
  await withEnv({ ...clearAllOverrides(), NODE_ENV: 'development' }, () => {
    const report = buildReadinessReport(getEnv());
    assert.deepEqual(new Set(report.entries.map((e) => e.capability)), expected);
  });
  await withEnv({ ...clearAllOverrides(), NODE_ENV: 'production' }, () => {
    const report = buildReadinessReport(getEnv());
    assert.deepEqual(new Set(report.entries.map((e) => e.capability)), expected);
  });
});

test('buildReadinessReport: environment field always echoes NODE_ENV', async () => {
  await withEnv({ ...clearAllOverrides(), NODE_ENV: 'test' }, () => {
    assert.equal(buildReadinessReport(getEnv()).environment, 'test');
  });
});
