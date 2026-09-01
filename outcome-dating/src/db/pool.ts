import pg from 'pg';
import { getEnv } from '../config/env.js';

const { Pool } = pg;

let sharedPool: pg.Pool | undefined;

/** Lazily-created singleton connection pool, configured from DATABASE_URL. */
export function getPool(): pg.Pool {
  if (!sharedPool) {
    const env = getEnv();
    sharedPool = new Pool({
      connectionString: env.DATABASE_URL,
      max: 10,
      idleTimeoutMillis: 30_000,
    });
  }
  return sharedPool;
}

/** Closes the shared pool. Call in test teardown / process shutdown. */
export async function closePool(): Promise<void> {
  if (sharedPool) {
    await sharedPool.end();
    sharedPool = undefined;
  }
}

/**
 * A query-capable handle. Both `pg.Pool` and `pg.PoolClient` satisfy this,
 * so code that receives a `DbClient` works whether it's running outside a
 * transaction (pool) or inside one (checked-out client), see
 * `withTransaction` in src/db/tx.ts and `Ctx.db` in src/lib/ctx.ts.
 */
export type DbClient = Pick<pg.Pool | pg.PoolClient, 'query'>;
