/**
 * Minimal Fastify bootstrap. This foundation layer's job is the typed
 * service contracts (see INTERFACES.md) — wiring the full §24 REST API
 * onto Fastify routes is deliberately left to the parallel agents once
 * their service bodies exist. This file exists so `npm run dev`/`build`
 * have something real to run, and demonstrates the intended wiring: build
 * one `Ctx` per request from the shared singletons below.
 */
import Fastify from 'fastify';
import { getEnv } from './config/env.js';
import { getPool } from './db/pool.js';
import { ConfigService } from './config/config.service.js';
import { FlagsService } from './config/flags.service.js';
import { SystemClock } from './lib/time.js';
import { createLogger } from './lib/logger.js';
import { FakeProcessor } from './services/payments/fake.processor.js';
import { StripeProcessor } from './services/payments/stripe.processor.js';
import { StubMediaModerationAdapter } from './services/media/stub.adapter.js';
import type { PaymentProcessor } from './services/payments/processor.port.js';
import type { Ctx } from './lib/ctx.js';

const env = getEnv();
const pool = getPool();
const clock = new SystemClock();
const logger = createLogger({ service: 'outcome-dating' });
const config = new ConfigService(pool, clock, logger);
const flags = new FlagsService(pool, logger);
const media = new StubMediaModerationAdapter();
const payments: PaymentProcessor =
  env.PAYMENT_PROCESSOR === 'stripe' ? new StripeProcessor(env.STRIPE_SECRET_KEY) : new FakeProcessor();

/** Builds a system-actor Ctx bound to the shared pool. Per-request handlers should instead build a `{ type: 'user' | 'venue_staff' | 'admin', ... }` actor from the verified access token. */
export function buildSystemCtx(): Ctx {
  return { db: pool, clock, config, flags, logger, actor: { type: 'system', job: 'http' }, payments, media };
}

const app = Fastify({ logger: false });

app.get('/healthz', async () => ({ status: 'ok' }));

async function main(): Promise<void> {
  await app.listen({ port: env.HTTP_PORT, host: env.HTTP_HOST });
  logger.info('server.listening', { port: env.HTTP_PORT, host: env.HTTP_HOST });
}

const isMain = process.argv[1] && import.meta.url === `file://${process.argv[1]}`;
if (isMain) {
  main().catch((err) => {
    logger.error('server.start_failed', { err: String(err) });
    process.exit(1);
  });
}

export { app };
