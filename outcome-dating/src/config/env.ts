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
