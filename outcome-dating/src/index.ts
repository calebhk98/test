#!/usr/bin/env node
/**
 * src/index.ts — the process entrypoint/CLI.
 *
 * Usage:
 *   node dist/index.js serve          # HTTP API + background job scheduler
 *   node dist/index.js migrate        # apply pending db/migrations/*.sql
 *   node dist/index.js seed           # deterministic dev/test seed data
 *   node dist/index.js jobs:run NAME  # run one §25 job once, print its result, exit
 *   node dist/index.js jobs:start     # run the job scheduler only (no HTTP server)
 *
 * Every command builds its own `AppDeps` (real Postgres pool, `SystemClock`,
 * the configured `PaymentProcessor`/`ImageModerationPort` — see
 * `src/http/deps.ts`) rather than sharing process-wide singletons across
 * commands, since only one command ever runs per process invocation.
 */
import { getEnv } from './config/env.js';
import { runMigrations } from './db/migrate.js';
import { closePool } from './db/pool.js';
import { seed } from './seed.js';
import { buildDeps } from './http/deps.js';
import { buildServer } from './http/server.js';
import { JobScheduler } from './jobs/scheduler.js';
import { ALL_JOBS, findJob } from './jobs/registry.js';

async function cmdServe(): Promise<void> {
  const deps = buildDeps();
  const env = getEnv();
  const app = buildServer(deps);

  const scheduler = new JobScheduler(deps);
  scheduler.start();

  await app.listen({ port: env.HTTP_PORT, host: env.HTTP_HOST });
  deps.logger.info('server.listening', { port: env.HTTP_PORT, host: env.HTTP_HOST, jobs: ALL_JOBS.map((j) => j.name) });

  const shutdown = async (signal: string): Promise<void> => {
    deps.logger.info('server.shutting_down', { signal });
    scheduler.stop();
    await app.close();
    await closePool();
    process.exit(0);
  };
  process.on('SIGINT', () => void shutdown('SIGINT'));
  process.on('SIGTERM', () => void shutdown('SIGTERM'));
}

async function cmdMigrate(): Promise<void> {
  const { applied } = await runMigrations();
  if (applied.length === 0) {
    console.log('No pending migrations.');
  } else {
    console.log(`Applied ${applied.length} migration(s):`);
    for (const f of applied) console.log(`  - ${f}`);
  }
  await closePool();
}

async function cmdSeed(): Promise<void> {
  await seed();
  await closePool();
}

async function cmdJobsRun(name: string | undefined): Promise<void> {
  if (!name) {
    console.error(`Usage: jobs:run <name>\nKnown jobs: ${ALL_JOBS.map((j) => j.name).join(', ')}`);
    process.exitCode = 1;
    await closePool();
    return;
  }
  if (!findJob(name)) {
    console.error(`Unknown job "${name}". Known jobs: ${ALL_JOBS.map((j) => j.name).join(', ')}`);
    process.exitCode = 1;
    await closePool();
    return;
  }

  const deps = buildDeps();
  const scheduler = new JobScheduler(deps);
  const result = await scheduler.runJob(name);
  console.log(JSON.stringify(result, null, 2));
  if (!result.ok) process.exitCode = 1;
  await closePool();
}

async function cmdJobsStart(): Promise<void> {
  const deps = buildDeps();
  const scheduler = new JobScheduler(deps);
  scheduler.start();
  deps.logger.info('jobs.scheduler_started', { jobs: ALL_JOBS.map((j) => j.name) });

  // The scheduler's own timers are unref'd (see JobScheduler#start's doc —
  // that's correct when embedded inside `serve`, whose HTTP listener keeps
  // the process alive on its own). A standalone jobs-only process needs its
  // own keep-alive, and a clean way to exit on Ctrl-C / SIGTERM.
  const heartbeat = setInterval(() => {}, 1 << 30);
  const shutdown = async (signal: string): Promise<void> => {
    deps.logger.info('jobs.shutting_down', { signal });
    clearInterval(heartbeat);
    scheduler.stop();
    await closePool();
    process.exit(0);
  };
  process.on('SIGINT', () => void shutdown('SIGINT'));
  process.on('SIGTERM', () => void shutdown('SIGTERM'));
}

async function main(): Promise<void> {
  const [, , command, ...rest] = process.argv;

  switch (command) {
    case 'serve':
      await cmdServe();
      return;
    case 'migrate':
      await cmdMigrate();
      return;
    case 'seed':
      await cmdSeed();
      return;
    case 'jobs:run':
      await cmdJobsRun(rest[0]);
      return;
    case 'jobs:start':
      await cmdJobsStart();
      return;
    default:
      console.error(
        `Unknown command "${command ?? ''}".\n\nUsage:\n  serve\n  migrate\n  seed\n  jobs:run <name>\n  jobs:start\n\nKnown jobs: ${ALL_JOBS.map((j) => j.name).join(', ')}`,
      );
      process.exitCode = 1;
  }
}

const isMain = process.argv[1] !== undefined && import.meta.url === `file://${process.argv[1]}`;
if (isMain) {
  main().catch((err) => {
    console.error(err);
    process.exitCode = 1;
  });
}

export { main };
