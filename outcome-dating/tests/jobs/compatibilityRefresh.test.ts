/**
 * §25.4 Compatibility Score Refresh job — nightly full recompute of
 * `compatibility_scores`, run through the actual job function.
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { setupTestDb, teardownTestDb, makeCtx, createUser } from './testHarness.js';
import type { TestDb } from './testHarness.js';
import { runCompatibilityRefreshJob } from '../../src/jobs/compatibilityRefresh.job.js';

let db: TestDb;

before(async () => {
  db = await setupTestDb('compatibility_refresh');
});

after(async () => {
  await teardownTestDb(db);
});

async function insertQuestion(slug: string): Promise<string> {
  const { rows } = await db.pool.query<{ id: string }>(
    `INSERT INTO questions (slug, category, question_text, self_left_label, self_right_label, partner_left_label, partner_right_label, weight, polarity, sensitive, active)
     VALUES ($1, 'test', $1, 'l', 'r', 'l', 'r', 1, 'standard', false, true) RETURNING id`,
    [slug],
  );
  return rows[0]!.id;
}

test('nightly refresh populates compatibility_scores for both directions of an active-user pair', async () => {
  const ctx = makeCtx(db);
  const a = await createUser(db);
  const b = await createUser(db);

  // >= DEFAULT_MIN_SHARED_QUESTIONS (3) fully-answered shared questions so the score is non-trivial.
  for (let i = 0; i < 3; i++) {
    const questionId = await insertQuestion(`q${i}-${a}`);
    await db.pool.query(`INSERT INTO answers (user_id, question_id, self_value, partner_value) VALUES ($1, $2, 3, 3)`, [a, questionId]);
    await db.pool.query(`INSERT INTO answers (user_id, question_id, self_value, partner_value) VALUES ($1, $2, 3, 3)`, [b, questionId]);
  }

  const result = await runCompatibilityRefreshJob(ctx);
  assert.equal(result.updated, 2, 'one row per direction for the single pair');

  const { rows } = await db.pool.query<{ score: string }>(
    `SELECT score FROM compatibility_scores WHERE user_id = $1 AND candidate_id = $2`,
    [a, b],
  );
  assert.equal(Number(rows[0]!.score), 1, 'identical self/partner answers on every shared question -> perfect satisfaction');
});

test('a nightly re-run after an answer change updates the materialized score (§25.4)', async () => {
  const ctx = makeCtx(db);
  const a = await createUser(db);
  const b = await createUser(db);
  const questions = [];
  for (let i = 0; i < 3; i++) {
    const questionId = await insertQuestion(`change-q${i}-${a}`);
    questions.push(questionId);
    await db.pool.query(`INSERT INTO answers (user_id, question_id, self_value, partner_value) VALUES ($1, $2, 3, 3)`, [a, questionId]);
    await db.pool.query(`INSERT INTO answers (user_id, question_id, self_value, partner_value) VALUES ($1, $2, 3, 3)`, [b, questionId]);
  }
  await runCompatibilityRefreshJob(ctx);
  const before = await db.pool.query<{ score: string; computed_at: Date }>(
    `SELECT score, computed_at FROM compatibility_scores WHERE user_id = $1 AND candidate_id = $2`,
    [a, b],
  );

  // A changes their partner preference to be maximally unsatisfied by B's self-answer on every question.
  for (const q of questions) {
    await db.pool.query(`UPDATE answers SET partner_value = 1 WHERE user_id = $1 AND question_id = $2`, [a, q]);
  }
  await runCompatibilityRefreshJob(ctx);
  const after = await db.pool.query<{ score: string; computed_at: Date }>(
    `SELECT score, computed_at FROM compatibility_scores WHERE user_id = $1 AND candidate_id = $2`,
    [a, b],
  );

  assert.notEqual(Number(after.rows[0]!.score), Number(before.rows[0]!.score));
});
