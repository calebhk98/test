/**
 * §25.4 Compatibility Score Refresh job — nightly full recompute of
 * `compatibility_scores`, run through the actual job function.
 *
 * CUTOVER NOTE (question-system-cutover build, reported — this file is
 * outside that build's file-ownership boundary and `src/jobs/**` is
 * explicitly off limits to edit): `compatibility.service.ts#refreshAllScores`
 * (called by `runCompatibilityRefreshJob` below, itself unmodified — a
 * one-line wrapper) now scores exclusively from the ONE typed question
 * bank (`question_bank`/`user_question_answers` —
 * db/migrations/008_questions.sql), not the old `questions`/`answers`
 * pair. This file's fixtures were repointed at the new bank so its
 * assertions (a perfect shared answer set scores 1.0; changing an answer
 * changes the materialized score on the next nightly run) still hold —
 * see src/services/question.service.ts's file-level CUTOVER doc for the
 * full accounting of what moved and why.
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

/** Inserts a typed-bank `scale` (min=1,max=5) question and returns (id, slug). */
async function insertQuestion(slug: string): Promise<{ id: string; slug: string }> {
  const { rows } = await db.pool.query<{ id: string }>(
    `INSERT INTO question_bank (slug, version, is_current, category, subcategory, tags, question_type, question_text, type_definition, base_weight, sensitive, active, answer_rate_hint)
     VALUES ($1, 1, true, 'test', NULL, '{}', 'scale', $1, $2::jsonb, 1, false, true, 0.5)
     RETURNING id`,
    [slug, JSON.stringify({ type: 'scale', min: 1, max: 5, minLabel: 'low', maxLabel: 'high', midLabel: 'mid' })],
  );
  return { id: rows[0]!.id, slug };
}

async function answer(userId: string, q: { id: string; slug: string }, selfValue: number, preferenceValue: number): Promise<void> {
  await db.pool.query(
    `INSERT INTO user_question_answers (user_id, question_slug, question_bank_id, status, self_value, preference_value, importance, answered_at, updated_at)
     VALUES ($1, $2, $3, 'answered', $4::jsonb, $5::jsonb, 'important', now(), now())
     ON CONFLICT (user_id, question_slug) DO UPDATE SET
       self_value = EXCLUDED.self_value, preference_value = EXCLUDED.preference_value, updated_at = EXCLUDED.updated_at`,
    [userId, q.slug, q.id, JSON.stringify(selfValue), JSON.stringify(preferenceValue)],
  );
}

test('nightly refresh populates compatibility_scores for both directions of an active-user pair', async () => {
  const ctx = makeCtx(db);
  const a = await createUser(db);
  const b = await createUser(db);

  // >= DEFAULT_MIN_SHARED_QUESTIONS (3) fully-answered shared questions so the score is non-trivial.
  for (let i = 0; i < 3; i++) {
    const q = await insertQuestion(`q${i}-${a}`);
    await answer(a, q, 3, 3);
    await answer(b, q, 3, 3);
  }

  const result = await runCompatibilityRefreshJob(ctx);
  assert.equal(result.updated, 2, 'one row per direction for the single pair');

  const { rows } = await db.pool.query<{ score: string }>(
    `SELECT score FROM compatibility_scores WHERE user_id = $1 AND candidate_id = $2`,
    [a, b],
  );
  assert.equal(Number(rows[0]!.score), 1, 'identical self/preference answers on every shared question -> perfect satisfaction');
});

test('a nightly re-run after an answer change updates the materialized score (§25.4)', async () => {
  const ctx = makeCtx(db);
  const a = await createUser(db);
  const b = await createUser(db);
  const questions: Array<{ id: string; slug: string }> = [];
  for (let i = 0; i < 3; i++) {
    const q = await insertQuestion(`change-q${i}-${a}`);
    questions.push(q);
    await answer(a, q, 3, 3);
    await answer(b, q, 3, 3);
  }
  await runCompatibilityRefreshJob(ctx);
  const before = await db.pool.query<{ score: string; computed_at: Date }>(
    `SELECT score, computed_at FROM compatibility_scores WHERE user_id = $1 AND candidate_id = $2`,
    [a, b],
  );

  // A changes their stated preference to be maximally unsatisfied by B's self-answer on every question.
  for (const q of questions) {
    await answer(a, q, 3, 1);
  }
  await runCompatibilityRefreshJob(ctx);
  const after = await db.pool.query<{ score: string; computed_at: Date }>(
    `SELECT score, computed_at FROM compatibility_scores WHERE user_id = $1 AND candidate_id = $2`,
    [a, b],
  );

  assert.notEqual(Number(after.rows[0]!.score), Number(before.rows[0]!.score));
});
