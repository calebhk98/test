import { z } from 'zod';

/**
 * Typed process-env loading. This is distinct from `config.service.ts`
 * (spec §21): env vars are deployment/infrastructure settings (DB URL,
 * ports, secrets) fixed at process start, while the config service manages
 * *business* variables that change at runtime without a deploy.
 */
const EnvSchema = z.object({
  NODE_ENV: z.enum(['development', 'test', 'production']).default('development'),

  DATABASE_URL: z
    .string()
    .default('postgres://outcome_dating@127.0.0.1:55433/outcome_dating'),

  HTTP_PORT: z.coerce.number().int().positive().default(3000),
  HTTP_HOST: z.string().default('0.0.0.0'),

  AUTH_TOKEN_SECRET: z.string().min(1).default('dev-insecure-secret-change-me'),
  ACCESS_TOKEN_TTL_MINUTES: z.coerce.number().int().positive().default(15),
  REFRESH_TOKEN_TTL_DAYS: z.coerce.number().int().positive().default(30),

  /**
   * Decision-layer addition: a dedicated signing secret for voucher QR
   * payloads, separate from `AUTH_TOKEN_SECRET` (spec §15.2). Key
   * separation matters here — a leaked QR secret (exposed to venue
   * hardware/apps, printed on receipts, scanned in public) must not be
   * usable to mint auth tokens. Optional so dev/test keep working without
   * setting it: `voucher.service.ts#voucherSecret()` falls back to
   * `AUTH_TOKEN_SECRET` when unset, logging that it did so is unnecessary
   * noise for local/test — the fallback is the documented, intended
   * behavior there, not a silent footgun.
   */
  VOUCHER_QR_SECRET: z.string().min(1).optional(),

  PAYMENT_PROCESSOR: z.enum(['fake', 'stripe']).default('fake'),
  STRIPE_SECRET_KEY: z.string().optional(),
  STRIPE_WEBHOOK_SECRET: z.string().optional(),

  /**
   * Which `ImageModerationPort` adapter to use (see
   * `src/services/media/moderation.port.ts`). Deliberately a free-form
   * identifier, not a closed enum: unlike payments/push/email/sms, no real
   * adapter exists in this codebase yet (only `StubMediaModerationAdapter`
   * does) — see `src/config/adapters.ts#selectMediaModerationAdapter` and
   * docs/scale-and-sources.md Part 2.3. Defaults to `'stub'`, which is the
   * only value that ever constructs successfully, and only outside
   * production — the production guard (`src/config/adapters.ts`) refuses
   * to start with `'stub'` (or with any other value, since nothing else is
   * implemented yet) when `NODE_ENV==='production'`.
   */
  MEDIA_MODERATION_PROVIDER: z.string().min(1).optional(),

  /** Which `PushSender` adapter to use (`src/services/notifications/ports/push.port.ts`). */
  PUSH_PROVIDER: z.enum(['fake', 'fcm', 'apns']).default('fake'),
  FCM_SERVICE_ACCOUNT_JSON: z.string().optional(),
  APNS_KEY_ID: z.string().optional(),
  APNS_TEAM_ID: z.string().optional(),
  APNS_SIGNING_KEY: z.string().optional(),
  APNS_BUNDLE_ID: z.string().optional(),

  /** Which `EmailSender` adapter to use (`src/services/notifications/ports/email.port.ts`). */
  EMAIL_PROVIDER: z.enum(['fake', 'ses']).default('fake'),
  SES_REGION: z.string().optional(),
  SES_FROM_ADDRESS: z.string().optional(),

  /** Which `SmsSender` adapter to use (`src/services/notifications/ports/sms.port.ts`). */
  SMS_PROVIDER: z.enum(['fake', 'twilio']).default('fake'),
  TWILIO_ACCOUNT_SID: z.string().optional(),
  TWILIO_AUTH_TOKEN: z.string().optional(),
  TWILIO_FROM_NUMBER: z.string().optional(),
});

export type Env = z.infer<typeof EnvSchema>;

let cached: Env | undefined;

/** Parses and validates process.env once, caching the result. Throws on the first call if invalid. */
export function getEnv(): Env {
  if (!cached) {
    const parsed = EnvSchema.safeParse(process.env);
    if (!parsed.success) {
      throw new Error(`Invalid environment configuration:\n${parsed.error.toString()}`);
    }
    cached = parsed.data;
  }
  return cached;
}

/** Test-only: reset the cached env so a test can mutate process.env and reload. */
export function _resetEnvCacheForTests(): void {
  cached = undefined;
}
