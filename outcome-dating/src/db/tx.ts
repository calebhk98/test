import type pg from 'pg';
import { getPool, type DbClient } from './pool.js';

/**
 * Runs `fn` inside a single Postgres transaction (BEGIN/COMMIT, ROLLBACK on
 * throw) and hands it a `DbClient` bound to the checked-out connection.
 * Every multi-statement write path (interest acceptance -> conversation
 * creation, date proposal capture -> ticket issuance, voucher redemption ->
 * conversation established + trust event, etc — see INTERFACES.md
 * invariants) MUST go through this rather than issuing separate pool
 * queries, or partial failure can leave the DB inconsistent.
 */
export async function withTransaction<T>(
  fn: (db: DbClient) => Promise<T>,
  pool: pg.Pool = getPool(),
): Promise<T> {
  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    const result = await fn(client);
    await client.query('COMMIT');
    return result;
  } catch (err) {
    await client.query('ROLLBACK').catch(() => {
      /* connection may already be dead; ROLLBACK failing is not the error to surface */
    });
    throw err;
  } finally {
    client.release();
  }
}

export type { DbClient };
