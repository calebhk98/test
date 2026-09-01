/**
 * src/http/deps.ts, process-wide dependency bundle for the HTTP layer and
 * background jobs.
 *
 * This is the API/JOBS agent's equivalent of `src/index.ts`'s inline
 * `buildSystemCtx()` (the placeholder entrypoint this build replaces), but
 * factored out so both `src/http/server.ts` (real HTTP requests) and
 * `src/jobs/*` (scheduled/CLI-invoked jobs) share exactly one construction
 * path for the five shared singletons (`pool`, `clock`, `config`, `flags`,
 * `logger`) plus the two external-integration ports (`payments`, `media`),
 * see INTERFACES.md decision #1: "nobody should import a concrete adapter
 * directly, always go through ctx."
 *
 * `AppDeps` deliberately excludes `actor`, that's per-request/per-job-run,
 * built by `ctxWithActor`/`systemCtx` below, never baked into the shared
 * bundle.
 */
import type pg from 'pg';
import { getPool } from '../db/pool.js';
import { getEnv } from '../config/env.js';
import { ConfigService } from '../config/config.service.js';
import { FlagsService } from '../config/flags.service.js';
import { SystemClock } from '../lib/time.js';
import type { Clock } from '../lib/time.js';
import { createLogger } from '../lib/logger.js';
import type { Logger } from '../lib/logger.js';
import { selectPaymentProcessor, selectMediaModerationAdapter } from '../config/adapters.js';
import type { PaymentProcessor } from '../services/payments/processor.port.js';
import type { ImageModerationPort } from '../services/media/moderation.port.js';
import type { Actor, Ctx } from '../lib/ctx.js';
import type { DbClient } from '../db/pool.js';

export interface AppDeps {
  pool: pg.Pool;
  clock: Clock;
  config: ConfigService;
  flags: FlagsService;
  logger: Logger;
  payments: PaymentProcessor;
  media: ImageModerationPort;
}

/**
 * Builds the shared dependency bundle. Every field is independently
 * overridable so tests can inject a `ManualClock`, a `FakeProcessor`
 * pre-seeded for a specific scenario, or a `pg.Pool` bound to a per-test
 * database, see `tests/http/testServer.ts` / `tests/jobs/testHarness.ts`.
 */
export function buildDeps(overrides?: Partial<AppDeps>): AppDeps {
  const env = getEnv();
  const pool = overrides?.pool ?? getPool();
  const clock = overrides?.clock ?? new SystemClock();
  const logger = overrides?.logger ?? createLogger({ service: 'outcome-dating' });
  const config = overrides?.config ?? new ConfigService(pool, clock, logger);
  const flags = overrides?.flags ?? new FlagsService(pool, logger);
  // Selection is explicit and total over `env.NODE_ENV` (see
  // src/config/adapters.ts), it can never silently resolve to a fake/stub
  // adapter in production the way a bare `?? new FakeX()` default could.
  // This is defense-in-depth: `src/index.ts` also runs the full
  // `runProductionGuard` before calling this, but a fake/stub adapter is
  // unconstructable here in production regardless of whether that ran.
  const media = overrides?.media ?? selectMediaModerationAdapter(env);
  const payments = overrides?.payments ?? selectPaymentProcessor(env);
  return { pool, clock, config, flags, logger, payments, media };
}

/** Builds a `Ctx` bound to `deps` for the given `actor`, optionally against a specific `db` handle (e.g. a transaction client). */
export function ctxWithActor(deps: AppDeps, actor: Actor, db: DbClient = deps.pool): Ctx {
  return {
    db,
    clock: deps.clock,
    config: deps.config,
    flags: deps.flags,
    logger: deps.logger,
    actor,
    payments: deps.payments,
    media: deps.media,
  };
}

/** A `system`-actor Ctx, used for background jobs, and as the throwaway Ctx `verifyAccessToken` needs before we know who the caller is. */
export function systemCtx(deps: AppDeps, job = 'http'): Ctx {
  return ctxWithActor(deps, { type: 'system', job });
}
