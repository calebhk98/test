/**
 * tests/unit/productionGuard.test.ts — the production fail-fast guard
 * (`runProductionGuard`, `src/config/adapters.ts`), invoked at startup
 * from `src/index.ts`.
 *
 * Every misconfiguration this build brief calls out gets its own test
 * (never one blanket test): starting from `VALID_PRODUCTION_ENV` (a
 * completely correctly-configured production deployment), each test
 * changes exactly one variable to the broken value and asserts
 * `runProductionGuard` throws, naming that specific problem. The inverse
 * is tested too: the untouched baseline passes, and development/test
 * environments are never affected by any of this, no matter how broken
 * their config looks.
 *
 * No database is needed — `runProductionGuard` is a pure function of
 * `Env`.
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { getEnv, _resetEnvCacheForTests } from '../../src/config/env.js';
import {
  runProductionGuard,
  buildReadinessReport,
  ProductionConfigError,
  registerMediaModerationProvider,
  _clearMediaModerationProvidersForTests,
} from '../../src/config/adapters.js';
import type { ImageModerationPort } from '../../src/services/media/moderation.port.js';

// ---------------------------------------------------------------------
// Env-mutation helper (save / apply / reset cache / run / restore),
// matching the pattern already used in tests/unit/decisionsConfig.test.ts.
// ---------------------------------------------------------------------

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

function withEnv<T>(overrides: Record<string, string | undefined>, fn: () => T): T {
  const saved: Record<string, string | undefined> = {};
  for (const key of ALL_MANAGED_KEYS) saved[key] = process.env[key];
  try {
    for (const key of ALL_MANAGED_KEYS) delete process.env[key]; // start from a clean slate every time
    for (const [key, value] of Object.entries(overrides)) {
      if (value !== undefined) process.env[key] = value;
    }
    _resetEnvCacheForTests();
    return fn();
  } finally {
    for (const [key, value] of Object.entries(saved)) {
      if (value === undefined) delete process.env[key];
      else process.env[key] = value;
    }
    _resetEnvCacheForTests();
  }
}

// A distinctive, greppable marker baked into every secret value below so
// the "never leaks a secret" tests can assert its absence with certainty
// rather than guessing at what a "real-looking" secret is.
const SECRET_MARKER = 'ZZZ_MUST_NOT_LEAK';

const AUTH_SECRET = `${SECRET_MARKER}_AUTH_${'x'.repeat(32)}`;
const VOUCHER_SECRET = `${SECRET_MARKER}_VOUCHER_${'y'.repeat(32)}`;
const STRIPE_SECRET_KEY = `${SECRET_MARKER}_sk_live_${'z'.repeat(20)}`;
const STRIPE_WEBHOOK_SECRET = `${SECRET_MARKER}_whsec_${'w'.repeat(20)}`;
const FCM_JSON = `{"marker":"${SECRET_MARKER}_fcm"}`;
const TWILIO_AUTH_TOKEN = `${SECRET_MARKER}_twilio_auth`;

const REAL_MEDIA_PROVIDER_NAME = 'test_real_provider';

/** A fully, correctly configured production deployment — the baseline every single-failure test starts from and un-does exactly one field of. */
const VALID_PRODUCTION_ENV: Record<string, string> = {
  NODE_ENV: 'production',
  DATABASE_URL: 'postgres://prod_user:prod_pass@prod-db.internal:5432/outcome_dating_prod',
  AUTH_TOKEN_SECRET: AUTH_SECRET,
  VOUCHER_QR_SECRET: VOUCHER_SECRET,
  PAYMENT_PROCESSOR: 'stripe',
  STRIPE_SECRET_KEY: STRIPE_SECRET_KEY,
  STRIPE_WEBHOOK_SECRET: STRIPE_WEBHOOK_SECRET,
  MEDIA_MODERATION_PROVIDER: REAL_MEDIA_PROVIDER_NAME,
  PUSH_PROVIDER: 'fcm',
  FCM_SERVICE_ACCOUNT_JSON: FCM_JSON,
  EMAIL_PROVIDER: 'ses',
  SES_REGION: 'us-east-1',
  SES_FROM_ADDRESS: 'noreply@example.com',
  SMS_PROVIDER: 'twilio',
  TWILIO_ACCOUNT_SID: 'AC_marker_sid',
  TWILIO_AUTH_TOKEN: TWILIO_AUTH_TOKEN,
  TWILIO_FROM_NUMBER: '+15550000000',
};

// The whole suite registers a stand-in "real" media moderation provider
// under REAL_MEDIA_PROVIDER_NAME so VALID_PRODUCTION_ENV can be genuinely
// fully valid (see adapters.ts's registry design) — without this, media
// moderation would fail every test in this file, since no real provider
// ships in this codebase yet.
const STAND_IN_MEDIA_ADAPTER: ImageModerationPort = {
  name: REAL_MEDIA_PROVIDER_NAME,
  async analyzePhoto() {
    throw new Error('not called by any test in this file');
  },
};

before(() => {
  registerMediaModerationProvider(REAL_MEDIA_PROVIDER_NAME, () => STAND_IN_MEDIA_ADAPTER);
});

after(() => {
  _clearMediaModerationProvidersForTests();
});

function expectBlocked(overrides: Record<string, string | undefined>, pattern: RegExp): void {
  withEnv({ ...VALID_PRODUCTION_ENV, ...overrides }, () => {
    assert.throws(
      () => runProductionGuard(getEnv()),
      (err: unknown) => {
        assert.ok(err instanceof ProductionConfigError, `expected ProductionConfigError, got ${String(err)}`);
        assert.match(err.message, pattern);
        return true;
      },
    );
  });
}

// =====================================================================
// Inverse: a correctly configured production environment passes.
// =====================================================================

test('inverse: a fully correctly configured production environment does not throw', () => {
  withEnv(VALID_PRODUCTION_ENV, () => {
    const report = runProductionGuard(getEnv());
    assert.equal(report.ok, true);
    assert.equal(report.environment, 'production');
    for (const entry of report.entries) {
      assert.equal(entry.ok, true, `${entry.capability} unexpectedly not ok: ${entry.detail}`);
      assert.equal(entry.isFake, false, `${entry.capability} unexpectedly reported as fake`);
    }
  });
});

// =====================================================================
// Inverse: development/test are never affected, however bad the config.
// =====================================================================

test('inverse: development is unaffected even with every insecure default left in place', () => {
  withEnv(
    {
      NODE_ENV: 'development',
      // Deliberately every field either unset or at its worst value —
      // none of this should matter outside production.
      AUTH_TOKEN_SECRET: undefined,
      VOUCHER_QR_SECRET: undefined,
      PAYMENT_PROCESSOR: undefined,
      DATABASE_URL: undefined,
      MEDIA_MODERATION_PROVIDER: undefined,
      PUSH_PROVIDER: undefined,
      EMAIL_PROVIDER: undefined,
      SMS_PROVIDER: undefined,
    },
    () => {
      const report = runProductionGuard(getEnv());
      assert.equal(report.environment, 'development');
      // Every fake is active — that's fine and expected outside production.
      assert.ok(report.entries.some((e) => e.capability === 'payments' && e.isFake));
    },
  );
});

test('inverse: test environment is unaffected even with every insecure default left in place', () => {
  withEnv({ NODE_ENV: 'test' }, () => {
    assert.doesNotThrow(() => runProductionGuard(getEnv()));
  });
});

// =====================================================================
// One test per production failure mode.
// =====================================================================

test('payments: PAYMENT_PROCESSOR unset in production is blocked, naming payments', () => {
  expectBlocked({ PAYMENT_PROCESSOR: undefined }, /payments:.*PAYMENT_PROCESSOR/is);
});

test('payments: PAYMENT_PROCESSOR=fake explicitly in production is blocked, naming payments', () => {
  expectBlocked({ PAYMENT_PROCESSOR: 'fake' }, /payments:.*PAYMENT_PROCESSOR="fake"/is);
});

test('payments: PAYMENT_PROCESSOR=stripe missing STRIPE_SECRET_KEY is blocked, naming STRIPE_SECRET_KEY', () => {
  expectBlocked({ STRIPE_SECRET_KEY: undefined }, /payments:.*STRIPE_SECRET_KEY/is);
});

test('payments: PAYMENT_PROCESSOR=stripe missing STRIPE_WEBHOOK_SECRET is blocked, naming STRIPE_WEBHOOK_SECRET', () => {
  expectBlocked({ STRIPE_WEBHOOK_SECRET: undefined }, /payments:.*STRIPE_WEBHOOK_SECRET/is);
});

test('mediaModeration: MEDIA_MODERATION_PROVIDER unset (stub) in production is blocked, naming mediaModeration', () => {
  expectBlocked({ MEDIA_MODERATION_PROVIDER: undefined }, /mediaModeration:.*stub/is);
});

test('mediaModeration: an unregistered provider name in production is blocked, naming the provider', () => {
  expectBlocked({ MEDIA_MODERATION_PROVIDER: 'some_unregistered_vision_api' }, /mediaModeration:.*some_unregistered_vision_api.*no ImageModerationPort implementation registered/is);
});

test('pushNotifications: PUSH_PROVIDER unset (fake) in production is blocked, naming pushNotifications', () => {
  expectBlocked({ PUSH_PROVIDER: undefined }, /pushNotifications:.*fake/is);
});

test('pushNotifications: PUSH_PROVIDER=fcm missing FCM_SERVICE_ACCOUNT_JSON is blocked, naming it', () => {
  expectBlocked({ FCM_SERVICE_ACCOUNT_JSON: undefined }, /pushNotifications:.*FCM_SERVICE_ACCOUNT_JSON/is);
});

test('pushNotifications: PUSH_PROVIDER=apns missing APNS credentials is blocked, naming the missing ones', () => {
  expectBlocked(
    { PUSH_PROVIDER: 'apns', FCM_SERVICE_ACCOUNT_JSON: undefined, APNS_KEY_ID: undefined, APNS_TEAM_ID: 'team', APNS_SIGNING_KEY: undefined, APNS_BUNDLE_ID: 'bundle' },
    /pushNotifications:.*APNS_KEY_ID.*APNS_SIGNING_KEY/is,
  );
});

test('emailNotifications: EMAIL_PROVIDER unset (fake) in production is blocked, naming emailNotifications', () => {
  expectBlocked({ EMAIL_PROVIDER: undefined }, /emailNotifications:.*fake/is);
});

test('emailNotifications: EMAIL_PROVIDER=ses missing SES settings is blocked, naming them', () => {
  expectBlocked({ SES_REGION: undefined, SES_FROM_ADDRESS: undefined }, /emailNotifications:.*SES_REGION.*SES_FROM_ADDRESS/is);
});

test('smsNotifications: SMS_PROVIDER unset (fake) in production is blocked, naming smsNotifications', () => {
  expectBlocked({ SMS_PROVIDER: undefined }, /smsNotifications:.*fake/is);
});

test('smsNotifications: SMS_PROVIDER=twilio missing credentials is blocked, naming them', () => {
  expectBlocked({ TWILIO_ACCOUNT_SID: undefined, TWILIO_AUTH_TOKEN: undefined }, /smsNotifications:.*TWILIO_ACCOUNT_SID.*TWILIO_AUTH_TOKEN/is);
});

test('authTokenSecret: the dev-insecure default in production is blocked, naming AUTH_TOKEN_SECRET', () => {
  expectBlocked({ AUTH_TOKEN_SECRET: 'dev-insecure-secret-change-me' }, /authTokenSecret:.*AUTH_TOKEN_SECRET.*insecure development default/is);
});

test('authTokenSecret: a too-short value in production is blocked, naming the length problem', () => {
  expectBlocked({ AUTH_TOKEN_SECRET: 'short-secret' }, /authTokenSecret:.*AUTH_TOKEN_SECRET is only \d+ character/is);
});

test('voucherSecret: unset in production is blocked, naming VOUCHER_QR_SECRET (must not fall back to AUTH_TOKEN_SECRET)', () => {
  expectBlocked({ VOUCHER_QR_SECRET: undefined }, /voucherSecret:.*VOUCHER_QR_SECRET is not set/is);
});

test('voucherSecret: a too-short value in production is blocked, naming the length problem', () => {
  expectBlocked({ VOUCHER_QR_SECRET: 'short' }, /voucherSecret:.*VOUCHER_QR_SECRET is only \d+ character/is);
});

test('voucherSecret: identical to AUTH_TOKEN_SECRET in production is blocked (key-separation violation)', () => {
  expectBlocked({ VOUCHER_QR_SECRET: AUTH_SECRET }, /voucherSecret:.*identical to AUTH_TOKEN_SECRET/is);
});

test('database: the local development DATABASE_URL default in production is blocked, naming DATABASE_URL', () => {
  expectBlocked({ DATABASE_URL: 'postgres://outcome_dating@127.0.0.1:55433/outcome_dating' }, /database:.*DATABASE_URL.*local development default/is);
});

test('database: an invalid DATABASE_URL scheme in production is blocked', () => {
  expectBlocked({ DATABASE_URL: 'mysql://prod-db.internal:3306/outcome_dating' }, /database:.*DATABASE_URL has scheme/is);
});

test('database: a malformed DATABASE_URL in production is blocked', () => {
  expectBlocked({ DATABASE_URL: 'not a url at all' }, /database:.*DATABASE_URL is not a valid URL/is);
});

// =====================================================================
// Aggregation: every problem is reported at once, not just the first.
// =====================================================================

test('aggregation: multiple simultaneous misconfigurations are all named in one thrown error', () => {
  withEnv({ ...VALID_PRODUCTION_ENV, PAYMENT_PROCESSOR: 'fake', AUTH_TOKEN_SECRET: 'dev-insecure-secret-change-me', SMS_PROVIDER: undefined }, () => {
    try {
      runProductionGuard(getEnv());
      assert.fail('expected runProductionGuard to throw');
    } catch (err) {
      assert.ok(err instanceof ProductionConfigError);
      assert.equal(err.problems.length, 3, `expected exactly 3 problems, got: ${JSON.stringify(err.problems)}`);
      const joined = err.problems.join('\n');
      assert.match(joined, /payments/);
      assert.match(joined, /authTokenSecret/);
      assert.match(joined, /smsNotifications/);
    }
  });
});

// =====================================================================
// No secret value ever appears in a thrown message or the report.
// =====================================================================

test('never leaks a secret value: the aggregated error from a broken production env contains no configured secret', () => {
  withEnv(
    { ...VALID_PRODUCTION_ENV, PAYMENT_PROCESSOR: 'fake', VOUCHER_QR_SECRET: undefined, FCM_SERVICE_ACCOUNT_JSON: undefined, PUSH_PROVIDER: 'fcm' },
    () => {
      try {
        runProductionGuard(getEnv());
        assert.fail('expected runProductionGuard to throw');
      } catch (err) {
        assert.ok(err instanceof ProductionConfigError);
        assert.doesNotMatch(err.message, new RegExp(SECRET_MARKER));
        assert.doesNotMatch(err.message, new RegExp(STRIPE_SECRET_KEY.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));
        assert.doesNotMatch(err.message, new RegExp(STRIPE_WEBHOOK_SECRET.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));
      }
    },
  );
});

test('never leaks a secret value: buildReadinessReport (what the /admin/system-readiness endpoint returns) contains no configured secret, passing or failing', () => {
  // Passing case.
  withEnv(VALID_PRODUCTION_ENV, () => {
    const report = runProductionGuard(getEnv());
    const json = JSON.stringify(report);
    assert.doesNotMatch(json, new RegExp(SECRET_MARKER));
    assert.doesNotMatch(json, new RegExp(TWILIO_AUTH_TOKEN.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));
  });
  // Failing case — the secrets that ARE set (e.g. STRIPE_SECRET_KEY, still
  // present while STRIPE_WEBHOOK_SECRET is the thing that's missing) must
  // still never appear in the report.
  withEnv({ ...VALID_PRODUCTION_ENV, STRIPE_WEBHOOK_SECRET: undefined }, () => {
    try {
      runProductionGuard(getEnv());
      assert.fail('expected runProductionGuard to throw');
    } catch (err) {
      assert.ok(err instanceof ProductionConfigError);
    }
    // buildReadinessReport itself never throws — use it directly too, the
    // same way the /admin/system-readiness route does.
    const report = buildReadinessReport(getEnv());
    const json = JSON.stringify(report);
    assert.doesNotMatch(json, new RegExp(SECRET_MARKER));
    assert.doesNotMatch(json, new RegExp(STRIPE_SECRET_KEY.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));
  });
});
