/**
 * src/config/adapters.ts, explicit, exhaustive environment-driven adapter
 * selection, plus the production fail-fast guard built on top of it.
 *
 * PROBLEM THIS FILE CLOSES (see docs/scale-and-sources.md Part 2, and the
 * build brief this file was written against): every external-integration
 * port in this codebase was previously selected with a pattern shaped like
 *
 *   env.PAYMENT_PROCESSOR === 'stripe' ? new StripeProcessor(...) : new FakeProcessor()
 *
 * which silently resolves to the fake/in-memory adapter for ANY value of
 * the env var, unset, misspelled, or simply forgotten in a deployment
 * manifest, including in production. `StubMediaModerationAdapter` was
 * worse: it was wired with no env switch at all. Nothing refused to start;
 * a misconfigured production deployment looked, and ran, exactly like a
 * healthy one.
 *
 * FIX, two parts:
 *
 * 1. Selection here is a function of `env.NODE_ENV`, not of the
 *    provider-name env var alone. Every `selectX`/`describeX` pair below
 *    switches on `env.NODE_ENV` with all three branches written out and a
 *    compile-time-enforced `assertNever` default, adding a fourth
 *    `NODE_ENV` value (or a new capability, by copying this shape) forces
 *    every switch to be revisited; there is no default arm a new case can
 *    silently fall into. Outside production, the fake/in-memory/stub
 *    adapter is *always* selected, no configuration required, per the
 *    build brief's "fakes must remain the effortless default outside
 *    production" rule. Inside production, the provider-name env var is
 *    read, but an unset/fake/unimplemented value is a hard error, never a
 *    silent fallback.
 * 2. `runProductionGuard` collects every problem across every capability
 *    (not just the first one hit) and throws one aggregated,
 *    secret-free error naming each one, so an operator fixes every
 *    misconfiguration in a single pass instead of a restart-per-error
 *    loop. It is called explicitly at process startup (`src/index.ts`)
 *    and is also enforced independently, per capability, by `buildDeps`
 *    (`src/http/deps.ts`) via the `selectX` functions themselves, so
 *    even a future caller that forgets to invoke the guard still cannot
 *    end up with a production `AppDeps` wired to a fake adapter.
 *
 * MEDIA MODERATION SPECIAL CASE: no real `ImageModerationPort`
 * implementation exists anywhere in this codebase yet (only
 * `StubMediaModerationAdapter` does, see docs/scale-and-sources.md
 * §2.3/§2.6). `MEDIA_MODERATION_PROVIDER` is the configuration seam this
 * file adds so a real provider CAN be selected once one exists, but
 * today, selecting anything (stub or otherwise) fails in production,
 * which is the correct, honest behavior: per the doc's own conclusion,
 * "treat photo moderation as off in any environment reachable by real
 * users" until a real adapter is implemented and registered in
 * `selectMediaModerationAdapter` below.
 *
 * NO SECRET VALUE IS EVER PLACED IN A `ReadinessEntry`, A THROWN ERROR
 * MESSAGE, OR A LOG LINE, every check below reports only booleans,
 * lengths, and provider names. See `tests/unit/productionGuard.test.ts`'s
 * "never leaks a secret value" tests.
 */
import type { Env } from './env.js';
import type { PaymentProcessor } from '../services/payments/processor.port.js';
import { FakeProcessor } from '../services/payments/fake.processor.js';
import { StripeProcessor } from '../services/payments/stripe.processor.js';
import type { ImageModerationPort } from '../services/media/moderation.port.js';
import { StubMediaModerationAdapter } from '../services/media/stub.adapter.js';
import type { PushSender } from '../services/notifications/ports/push.port.js';
import { FakePushSender } from '../services/notifications/adapters/fake.push.js';
import { FcmPushSender } from '../services/notifications/adapters/fcm.push.js';
import { ApnsPushSender } from '../services/notifications/adapters/apns.push.js';
import type { EmailSender } from '../services/notifications/ports/email.port.js';
import { FakeEmailSender } from '../services/notifications/adapters/fake.email.js';
import { SesEmailSender } from '../services/notifications/adapters/ses.email.js';
import type { SmsSender } from '../services/notifications/ports/sms.port.js';
import { FakeSmsSender } from '../services/notifications/adapters/fake.sms.js';
import { TwilioSmsSender } from '../services/notifications/adapters/twilio.sms.js';

/** Exhaustiveness helper: a call site that reaches this has an un-handled case, TypeScript rejects the call unless `x` is provably `never`, i.e. every declared case has already been handled above it. */
function assertNever(x: never): never {
  throw new Error(`adapters.ts: unreachable case reached (${JSON.stringify(x)}), a value was added without a corresponding branch.`);
}

// The literal insecure/local defaults this guard refuses to run on in
// production. Mirrors the `.default(...)` values in `env.ts`, kept as
// named constants here (rather than re-imported) because `env.ts`
// intentionally has no dependency on this file.
const DEV_DEFAULT_AUTH_SECRET = 'dev-insecure-secret-change-me';
const DEV_DEFAULT_DATABASE_URL = 'postgres://outcome_dating@127.0.0.1:55433/outcome_dating';

/** Minimum acceptable length for a production HMAC-SHA256 signing secret (`src/lib/signing.ts`), 32 chars is a conservative floor for 256-bit-class key material, not a hard cryptographic requirement for the string encoding used. */
const MIN_SECRET_LENGTH = 32;

export interface ReadinessEntry {
  /** Stable machine-readable capability id, e.g. "payments", "mediaModeration". */
  capability: string;
  /** The adapter's own `.name` (or a short status token for non-adapter checks), never a secret value. */
  selected: string;
  /** True when the active/attempted choice is a fake, stub, or in-memory implementation. */
  isFake: boolean;
  /** True when this capability is fit to run as currently configured. */
  ok: boolean;
  /** Human-readable, secret-free explanation of `selected`/`ok`. */
  detail: string;
}

export interface ReadinessReport {
  environment: Env['NODE_ENV'];
  generatedAt: string;
  /** True only when every entry is `ok`. */
  ok: boolean;
  entries: ReadinessEntry[];
}

/** Thrown by `runProductionGuard` when `NODE_ENV==='production'` and one or more capabilities are not production-ready. Aggregates every problem found, not just the first. */
export class ProductionConfigError extends Error {
  readonly problems: string[];

  constructor(problems: string[]) {
    super(
      `Refusing to start in production: ${problems.length} configuration problem(s) found:\n` +
        problems.map((p, i) => `  ${i + 1}. ${p}`).join('\n'),
    );
    this.name = 'ProductionConfigError';
    this.problems = problems;
  }
}

// ---------------------------------------------------------------------
// Payments
// ---------------------------------------------------------------------

function describePayments(env: Env): ReadinessEntry {
  const capability = 'payments';
  switch (env.NODE_ENV) {
    case 'development':
    case 'test':
      return { capability, selected: 'fake', isFake: true, ok: true, detail: `${env.NODE_ENV}: FakeProcessor (no configuration required).` };
    case 'production': {
      if (env.PAYMENT_PROCESSOR !== 'stripe') {
        return {
          capability,
          selected: env.PAYMENT_PROCESSOR,
          isFake: env.PAYMENT_PROCESSOR === 'fake',
          ok: false,
          detail: `PAYMENT_PROCESSOR="${env.PAYMENT_PROCESSOR}", production requires PAYMENT_PROCESSOR=stripe. Running "fake" in production means date proposals get "authorized," tickets get issued, and venues get recorded as paid while no money ever moves.`,
        };
      }
      const missing = [!env.STRIPE_SECRET_KEY && 'STRIPE_SECRET_KEY', !env.STRIPE_WEBHOOK_SECRET && 'STRIPE_WEBHOOK_SECRET'].filter(
        (x): x is string => Boolean(x),
      );
      if (missing.length > 0) {
        return { capability, selected: 'stripe', isFake: false, ok: false, detail: `PAYMENT_PROCESSOR=stripe but missing required secret(s): ${missing.join(', ')}.` };
      }
      return { capability, selected: 'stripe', isFake: false, ok: true, detail: 'StripeProcessor configured (STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET are set).' };
    }
    default:
      return assertNever(env.NODE_ENV);
  }
}

/** Selects the `PaymentProcessor` for `env.NODE_ENV`. Throws in production rather than ever returning `FakeProcessor`. */
export function selectPaymentProcessor(env: Env): PaymentProcessor {
  switch (env.NODE_ENV) {
    case 'development':
    case 'test':
      return new FakeProcessor();
    case 'production': {
      const entry = describePayments(env);
      if (!entry.ok) throw new Error(`[payments] ${entry.detail}`);
      return new StripeProcessor(env.STRIPE_SECRET_KEY);
    }
    default:
      return assertNever(env.NODE_ENV);
  }
}

// ---------------------------------------------------------------------
// Media moderation
//
// No real `ImageModerationPort` implementation exists anywhere in this
// codebase yet (only `StubMediaModerationAdapter` does). Rather than hard-
// code a single hypothetical provider name, the seam is a small registry:
// a future agent implements a real adapter and calls
// `registerMediaModerationProvider('vision_api', (env) => new
// VisionApiAdapter(...))` (e.g. from that adapter's own module, imported
// once from `src/http/deps.ts`), nothing about the selection/guard logic
// below needs to change. The registry starts empty, which is exactly why
// production can never select a real media-moderation adapter today: none
// has been registered, matching docs/scale-and-sources.md §2.3/§2.6's
// conclusion to "treat photo moderation as off in any environment
// reachable by real users" until one exists.
// ---------------------------------------------------------------------

export type MediaModerationProviderFactory = (env: Env) => ImageModerationPort;

const mediaModerationProviders = new Map<string, MediaModerationProviderFactory>();

/** Registers a real `ImageModerationPort` factory under `providerName`, making it selectable via `MEDIA_MODERATION_PROVIDER=<providerName>` in production. Call once, at module load, from the adapter's own file. */
export function registerMediaModerationProvider(providerName: string, factory: MediaModerationProviderFactory): void {
  if (providerName === 'stub') {
    throw new Error('registerMediaModerationProvider: "stub" is reserved for StubMediaModerationAdapter and can never be registered as a real provider.');
  }
  mediaModerationProviders.set(providerName, factory);
}

/** Test-only: clears every provider registered via `registerMediaModerationProvider`, restoring the "no real provider exists" baseline. */
export function _clearMediaModerationProvidersForTests(): void {
  mediaModerationProviders.clear();
}

function describeMedia(env: Env): ReadinessEntry {
  const capability = 'mediaModeration';
  switch (env.NODE_ENV) {
    case 'development':
    case 'test':
      return { capability, selected: 'stub', isFake: true, ok: true, detail: `${env.NODE_ENV}: StubMediaModerationAdapter (no configuration required).` };
    case 'production': {
      const provider = env.MEDIA_MODERATION_PROVIDER;
      if (!provider || provider === 'stub') {
        return {
          capability,
          selected: provider ?? 'stub',
          isFake: true,
          ok: false,
          detail:
            'MEDIA_MODERATION_PROVIDER is unset (or "stub"), the stub adapter approves virtually any photo by URL heuristic alone and MUST NOT run in production: it would approve real nudity, weapons, and illegal-content photos the product is required to block. Implement a real ImageModerationPort adapter, register it with registerMediaModerationProvider(...) in src/config/adapters.ts, then set MEDIA_MODERATION_PROVIDER to select it.',
        };
      }
      if (!mediaModerationProviders.has(provider)) {
        return {
          capability,
          selected: provider,
          isFake: false,
          ok: false,
          detail: `MEDIA_MODERATION_PROVIDER="${provider}" has no ImageModerationPort implementation registered. Implement one in src/services/media, then call registerMediaModerationProvider("${provider}", ...) before production can start with it.`,
        };
      }
      return { capability, selected: provider, isFake: false, ok: true, detail: `Real ImageModerationPort provider "${provider}" is registered and selected.` };
    }
    default:
      return assertNever(env.NODE_ENV);
  }
}

/** Selects the `ImageModerationPort` for `env.NODE_ENV`. Throws in production unless a real provider has been registered via `registerMediaModerationProvider`, see the module doc above. */
export function selectMediaModerationAdapter(env: Env): ImageModerationPort {
  switch (env.NODE_ENV) {
    case 'development':
    case 'test':
      return new StubMediaModerationAdapter();
    case 'production': {
      const entry = describeMedia(env);
      if (!entry.ok) throw new Error(`[mediaModeration] ${entry.detail}`);
      // entry.ok is only true once env.MEDIA_MODERATION_PROVIDER names a
      // provider present in the registry (checked above), so the lookup
      // below cannot miss.
      const factory = mediaModerationProviders.get(env.MEDIA_MODERATION_PROVIDER as string) as MediaModerationProviderFactory;
      return factory(env);
    }
    default:
      return assertNever(env.NODE_ENV);
  }
}

// ---------------------------------------------------------------------
// Push
// ---------------------------------------------------------------------

function describePush(env: Env): ReadinessEntry {
  const capability = 'pushNotifications';
  switch (env.NODE_ENV) {
    case 'development':
    case 'test':
      return { capability, selected: 'fake', isFake: true, ok: true, detail: `${env.NODE_ENV}: FakePushSender (no configuration required).` };
    case 'production':
      switch (env.PUSH_PROVIDER) {
        case 'fake':
          return {
            capability,
            selected: 'fake',
            isFake: true,
            ok: false,
            detail: 'PUSH_PROVIDER=fake (or unset), refusing to run the fake push sender in production. Set PUSH_PROVIDER=fcm or PUSH_PROVIDER=apns.',
          };
        case 'fcm':
          if (!env.FCM_SERVICE_ACCOUNT_JSON) {
            return { capability, selected: 'fcm', isFake: false, ok: false, detail: 'PUSH_PROVIDER=fcm but FCM_SERVICE_ACCOUNT_JSON is not set.' };
          }
          return { capability, selected: 'fcm', isFake: false, ok: true, detail: 'FcmPushSender configured.' };
        case 'apns': {
          const missing = [
            !env.APNS_KEY_ID && 'APNS_KEY_ID',
            !env.APNS_TEAM_ID && 'APNS_TEAM_ID',
            !env.APNS_SIGNING_KEY && 'APNS_SIGNING_KEY',
            !env.APNS_BUNDLE_ID && 'APNS_BUNDLE_ID',
          ].filter((x): x is string => Boolean(x));
          if (missing.length > 0) {
            return { capability, selected: 'apns', isFake: false, ok: false, detail: `PUSH_PROVIDER=apns but missing required secret(s): ${missing.join(', ')}.` };
          }
          return { capability, selected: 'apns', isFake: false, ok: true, detail: 'ApnsPushSender configured.' };
        }
        default:
          return assertNever(env.PUSH_PROVIDER);
      }
    default:
      return assertNever(env.NODE_ENV);
  }
}

/** Selects the `PushSender` for `env.NODE_ENV`. Throws in production rather than ever returning `FakePushSender`. */
export function selectPushSender(env: Env): PushSender {
  switch (env.NODE_ENV) {
    case 'development':
    case 'test':
      return new FakePushSender();
    case 'production': {
      const entry = describePush(env);
      if (!entry.ok) throw new Error(`[pushNotifications] ${entry.detail}`);
      switch (env.PUSH_PROVIDER) {
        case 'fcm':
          return new FcmPushSender(env.FCM_SERVICE_ACCOUNT_JSON);
        case 'apns':
          return new ApnsPushSender({
            keyId: env.APNS_KEY_ID as string,
            teamId: env.APNS_TEAM_ID as string,
            signingKey: env.APNS_SIGNING_KEY as string,
            bundleId: env.APNS_BUNDLE_ID as string,
          });
        case 'fake':
          throw new Error('[pushNotifications] unreachable: entry.ok was true for PUSH_PROVIDER=fake.');
        default:
          return assertNever(env.PUSH_PROVIDER);
      }
    }
    default:
      return assertNever(env.NODE_ENV);
  }
}

// ---------------------------------------------------------------------
// Email
// ---------------------------------------------------------------------

function describeEmail(env: Env): ReadinessEntry {
  const capability = 'emailNotifications';
  switch (env.NODE_ENV) {
    case 'development':
    case 'test':
      return { capability, selected: 'fake', isFake: true, ok: true, detail: `${env.NODE_ENV}: FakeEmailSender (no configuration required).` };
    case 'production':
      switch (env.EMAIL_PROVIDER) {
        case 'fake':
          return {
            capability,
            selected: 'fake',
            isFake: true,
            ok: false,
            detail: 'EMAIL_PROVIDER=fake (or unset), refusing to run the fake email sender in production. Set EMAIL_PROVIDER=ses.',
          };
        case 'ses': {
          const missing = [!env.SES_REGION && 'SES_REGION', !env.SES_FROM_ADDRESS && 'SES_FROM_ADDRESS'].filter((x): x is string => Boolean(x));
          if (missing.length > 0) {
            return { capability, selected: 'ses', isFake: false, ok: false, detail: `EMAIL_PROVIDER=ses but missing required setting(s): ${missing.join(', ')}.` };
          }
          return { capability, selected: 'ses', isFake: false, ok: true, detail: 'SesEmailSender configured.' };
        }
        default:
          return assertNever(env.EMAIL_PROVIDER);
      }
    default:
      return assertNever(env.NODE_ENV);
  }
}

/** Selects the `EmailSender` for `env.NODE_ENV`. Throws in production rather than ever returning `FakeEmailSender`. */
export function selectEmailSender(env: Env): EmailSender {
  switch (env.NODE_ENV) {
    case 'development':
    case 'test':
      return new FakeEmailSender();
    case 'production': {
      const entry = describeEmail(env);
      if (!entry.ok) throw new Error(`[emailNotifications] ${entry.detail}`);
      switch (env.EMAIL_PROVIDER) {
        case 'ses':
          return new SesEmailSender({ region: env.SES_REGION as string, fromAddress: env.SES_FROM_ADDRESS as string });
        case 'fake':
          throw new Error('[emailNotifications] unreachable: entry.ok was true for EMAIL_PROVIDER=fake.');
        default:
          return assertNever(env.EMAIL_PROVIDER);
      }
    }
    default:
      return assertNever(env.NODE_ENV);
  }
}

// ---------------------------------------------------------------------
// SMS
// ---------------------------------------------------------------------

function describeSms(env: Env): ReadinessEntry {
  const capability = 'smsNotifications';
  switch (env.NODE_ENV) {
    case 'development':
    case 'test':
      return { capability, selected: 'fake', isFake: true, ok: true, detail: `${env.NODE_ENV}: FakeSmsSender (no configuration required).` };
    case 'production':
      switch (env.SMS_PROVIDER) {
        case 'fake':
          return {
            capability,
            selected: 'fake',
            isFake: true,
            ok: false,
            detail: 'SMS_PROVIDER=fake (or unset), refusing to run the fake SMS sender in production. Set SMS_PROVIDER=twilio.',
          };
        case 'twilio': {
          const missing = [!env.TWILIO_ACCOUNT_SID && 'TWILIO_ACCOUNT_SID', !env.TWILIO_AUTH_TOKEN && 'TWILIO_AUTH_TOKEN', !env.TWILIO_FROM_NUMBER && 'TWILIO_FROM_NUMBER'].filter(
            (x): x is string => Boolean(x),
          );
          if (missing.length > 0) {
            return { capability, selected: 'twilio', isFake: false, ok: false, detail: `SMS_PROVIDER=twilio but missing required secret(s): ${missing.join(', ')}.` };
          }
          return { capability, selected: 'twilio', isFake: false, ok: true, detail: 'TwilioSmsSender configured.' };
        }
        default:
          return assertNever(env.SMS_PROVIDER);
      }
    default:
      return assertNever(env.NODE_ENV);
  }
}

/** Selects the `SmsSender` for `env.NODE_ENV`. Throws in production rather than ever returning `FakeSmsSender`. */
export function selectSmsSender(env: Env): SmsSender {
  switch (env.NODE_ENV) {
    case 'development':
    case 'test':
      return new FakeSmsSender();
    case 'production': {
      const entry = describeSms(env);
      if (!entry.ok) throw new Error(`[smsNotifications] ${entry.detail}`);
      switch (env.SMS_PROVIDER) {
        case 'twilio':
          return new TwilioSmsSender({
            accountSid: env.TWILIO_ACCOUNT_SID as string,
            authToken: env.TWILIO_AUTH_TOKEN as string,
            fromNumber: env.TWILIO_FROM_NUMBER as string,
          });
        case 'fake':
          throw new Error('[smsNotifications] unreachable: entry.ok was true for SMS_PROVIDER=fake.');
        default:
          return assertNever(env.SMS_PROVIDER);
      }
    }
    default:
      return assertNever(env.NODE_ENV);
  }
}

// ---------------------------------------------------------------------
// Secrets and the database connection (not adapter selections, but the
// same "silent insecure default in production" failure pattern,
// docs/scale-and-sources.md §2.4).
// ---------------------------------------------------------------------

function describeAuthSecret(env: Env): ReadinessEntry {
  const capability = 'authTokenSecret';
  if (env.NODE_ENV !== 'production') {
    return { capability, selected: 'dev-default-permitted', isFake: false, ok: true, detail: `${env.NODE_ENV}: the insecure default is permitted.` };
  }
  if (env.AUTH_TOKEN_SECRET === DEV_DEFAULT_AUTH_SECRET) {
    return {
      capability,
      selected: 'dev-default',
      isFake: true,
      ok: false,
      detail: 'AUTH_TOKEN_SECRET is still the insecure development default ("dev-insecure-secret-change-me"). Set it to a unique, random, high-entropy value in production.',
    };
  }
  if (env.AUTH_TOKEN_SECRET.length < MIN_SECRET_LENGTH) {
    return {
      capability,
      selected: 'too-short',
      isFake: false,
      ok: false,
      detail: `AUTH_TOKEN_SECRET is only ${env.AUTH_TOKEN_SECRET.length} character(s) long; production requires at least ${MIN_SECRET_LENGTH}.`,
    };
  }
  return { capability, selected: 'configured', isFake: false, ok: true, detail: 'AUTH_TOKEN_SECRET is set to a non-default value of adequate length.' };
}

function describeVoucherSecret(env: Env): ReadinessEntry {
  const capability = 'voucherSecret';
  if (env.NODE_ENV !== 'production') {
    return {
      capability,
      selected: env.VOUCHER_QR_SECRET ? 'configured' : 'falls-back-to-auth-secret',
      isFake: false,
      ok: true,
      detail: `${env.NODE_ENV}: falling back to AUTH_TOKEN_SECRET when unset is documented, intended behavior outside production.`,
    };
  }
  if (!env.VOUCHER_QR_SECRET) {
    return {
      capability,
      selected: 'unset',
      isFake: false,
      ok: false,
      detail:
        'VOUCHER_QR_SECRET is not set. In production it must be a dedicated secret, separate from AUTH_TOKEN_SECRET, a leaked venue-facing QR secret must never be usable to mint auth tokens, so it must not silently fall back to AUTH_TOKEN_SECRET the way it does outside production.',
    };
  }
  if (env.VOUCHER_QR_SECRET.length < MIN_SECRET_LENGTH) {
    return {
      capability,
      selected: 'too-short',
      isFake: false,
      ok: false,
      detail: `VOUCHER_QR_SECRET is only ${env.VOUCHER_QR_SECRET.length} character(s) long; production requires at least ${MIN_SECRET_LENGTH}.`,
    };
  }
  if (env.VOUCHER_QR_SECRET === env.AUTH_TOKEN_SECRET) {
    return {
      capability,
      selected: 'same-as-auth-secret',
      isFake: false,
      ok: false,
      detail: 'VOUCHER_QR_SECRET is identical to AUTH_TOKEN_SECRET. These must be distinct keys (see src/config/env.ts for why key separation matters here).',
    };
  }
  return { capability, selected: 'configured', isFake: false, ok: true, detail: 'VOUCHER_QR_SECRET is set, distinct from AUTH_TOKEN_SECRET, and of adequate length.' };
}

function describeDatabase(env: Env): ReadinessEntry {
  const capability = 'database';
  if (env.NODE_ENV !== 'production') {
    return { capability, selected: 'configured', isFake: false, ok: true, detail: `${env.NODE_ENV}: the local development connection is permitted.` };
  }
  if (env.DATABASE_URL === DEV_DEFAULT_DATABASE_URL) {
    return {
      capability,
      selected: 'dev-default',
      isFake: true,
      ok: false,
      detail: 'DATABASE_URL is still the local development default (127.0.0.1:55433/outcome_dating). Set DATABASE_URL to the production database.',
    };
  }
  let parsed: URL;
  try {
    parsed = new URL(env.DATABASE_URL);
  } catch {
    return { capability, selected: 'invalid', isFake: false, ok: false, detail: 'DATABASE_URL is not a valid URL.' };
  }
  if (parsed.protocol !== 'postgres:' && parsed.protocol !== 'postgresql:') {
    return { capability, selected: 'invalid', isFake: false, ok: false, detail: `DATABASE_URL has scheme "${parsed.protocol}", expected postgres:// or postgresql://.` };
  }
  return { capability, selected: 'configured', isFake: false, ok: true, detail: 'DATABASE_URL is set to a non-default value.' };
}

// ---------------------------------------------------------------------
// Aggregate report + guard
// ---------------------------------------------------------------------

/** Builds the full per-capability readiness report for `env`. Never throws, and never includes a secret value, safe to log or serve over HTTP as-is. */
export function buildReadinessReport(env: Env): ReadinessReport {
  const entries: ReadinessEntry[] = [
    describePayments(env),
    describeMedia(env),
    describePush(env),
    describeEmail(env),
    describeSms(env),
    describeAuthSecret(env),
    describeVoucherSecret(env),
    describeDatabase(env),
  ];
  return {
    environment: env.NODE_ENV,
    generatedAt: new Date().toISOString(),
    ok: entries.every((e) => e.ok),
    entries,
  };
}

/**
 * The startup fail-fast guard. Builds the readiness report and, only when
 * `env.NODE_ENV==='production'` and one or more capabilities are not
 * ready, throws a single `ProductionConfigError` naming every problem at
 * once. Outside production this never throws, it only returns the report
 * (still useful to log, so an operator can see which fakes are active in
 * dev/test too).
 */
export function runProductionGuard(env: Env): ReadinessReport {
  const report = buildReadinessReport(env);
  if (env.NODE_ENV === 'production' && !report.ok) {
    const problems = report.entries.filter((e) => !e.ok).map((e) => `${e.capability}: ${e.detail}`);
    throw new ProductionConfigError(problems);
  }
  return report;
}
