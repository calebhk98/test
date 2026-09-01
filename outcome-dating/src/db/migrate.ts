/**
 * Tiny migration runner. Applies db/migrations/*.sql in filename order,
 * each inside its own transaction, and records applied filenames in a
 * `schema_migrations` table so re-running is a no-op. No down-migrations,
 * no framework, this is intentionally minimal for MVP (spec §32 just
 * requires "relational database", not a specific migration tool).
 *
 * Usage: `npm run migrate` (reads DATABASE_URL via src/config/env.ts).
 */
import { readdir, readFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { getPool, closePool } from './pool.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const MIGRATIONS_DIR = join(__dirname, '..', '..', 'db', 'migrations');

async function ensureMigrationsTable(): Promise<void> {
  const pool = getPool();
  await pool.query(`
    CREATE TABLE IF NOT EXISTS schema_migrations (
      filename    text PRIMARY KEY,
      applied_at  timestamptz NOT NULL DEFAULT now()
    )
  `);
}

async function appliedMigrations(): Promise<Set<string>> {
  const pool = getPool();
  const { rows } = await pool.query<{ filename: string }>('SELECT filename FROM schema_migrations');
  return new Set(rows.map((r) => r.filename));
}

export async function runMigrations(): Promise<{ applied: string[] }> {
  await ensureMigrationsTable();
  const already = await appliedMigrations();

  const files = (await readdir(MIGRATIONS_DIR)).filter((f) => f.endsWith('.sql')).sort();

  const pool = getPool();
  const applied: string[] = [];

  for (const file of files) {
    if (already.has(file)) continue;
    const sql = await readFile(join(MIGRATIONS_DIR, file), 'utf8');
    const client = await pool.connect();
    try {
      await client.query('BEGIN');
      await client.query(sql);
      await client.query('INSERT INTO schema_migrations (filename) VALUES ($1)', [file]);
      await client.query('COMMIT');
      applied.push(file);
    } catch (err) {
      await client.query('ROLLBACK').catch(() => {});
      throw new Error(`Migration failed: ${file}\n${(err as Error).message}`, { cause: err });
    } finally {
      client.release();
    }
  }

  return { applied };
}

async function main(): Promise<void> {
  const { applied } = await runMigrations();
  if (applied.length === 0) {
    console.log('No pending migrations.');
  } else {
    console.log(`Applied ${applied.length} migration(s):`);
    for (const f of applied) console.log(`  - ${f}`);
  }
  await closePool();
}

const isMain = process.argv[1] === fileURLToPath(import.meta.url);
if (isMain) {
  main().catch((err) => {
    console.error(err);
    process.exit(1);
  });
}
