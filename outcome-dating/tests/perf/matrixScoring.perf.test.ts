/**
 * tests/perf/matrixScoring.perf.test.ts
 *
 * The measured half of "is matrix multiplication worth it for compatibility
 * scoring": benchmarks matrixScoring.ts's batched kernel/indicator path
 * against the existing, unmodified scalar path
 * (compatibility.service.ts#computePairScore, unchanged), at several
 * realistic shapes. Pure, in-memory, no DB (both implementations under
 * test are pure functions of questions + answers).
 *
 * Two call shapes are benchmarked because the codebase actually only ever
 * presents one of them:
 *
 *   ONE-VS-MANY: one user scored against a candidate list. This is the
 *   REAL shape of every call site in compatibility.service.ts today:
 *   `getScoresForCandidates` (self vs. a page of candidates, up to
 *   `MAX_CANDIDATE_POOL_SIZE`=500) and `refreshScoresForUser` (self vs.
 *   up to `MATERIALIZED_NEIGHBORS_PER_USER`=50 geo-bounded neighbors).
 *   Both are exercised below (K=50 and K=500).
 *
 *   ALL-PAIRS BLOCK: many users against many users at once (an N x N
 *   block). This is NOT how `refreshAllScores` is actually shaped today
 *   (it computes each user's neighbor set independently, effectively many
 *   separate one-vs-K calls, per its own file-level SCALE FIX doc in
 *   compatibility.service.ts): it is included to show what the technique
 *   is capable of when both sides of the block are large, i.e. the shape
 *   dense linear algebra actually wants, since that is the shape the task
 *   brief's plausibility argument is built on.
 *
 * See docs/matrix-scoring.md for the numbers this file produces and the
 * resulting recommendation.
 */
import { test } from 'node:test';
import { performance } from 'node:perf_hooks';
import { answeredState } from '../../src/domain/questions/index.js';
import type { ImportanceLevel, QuestionAnswerState, QuestionDefinition, QuestionTypeDefinition } from '../../src/domain/questions/index.js';
import { computePairScore } from '../../src/services/compatibility.service.js';
import { computeCompatibilityBlock, computeScoresForCandidatesMatrix } from '../../src/domain/questions/matrixScoring.js';

// =====================================================================
// Fixtures: a seeded RNG and a bank generator whose type mix matches the
// REAL seeded bank (src/seed.ts): ~40% scale, ~12% frequency, ~40%
// single_choice, ~8% multi_choice (26/8/26/5 out of 65 questions,
// counted directly from src/seed.ts for this build's report).
// =====================================================================

function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const SCALE_1_5: QuestionTypeDefinition = { type: 'scale', min: 1, max: 5, minLabel: 'low', maxLabel: 'high', midLabel: 'mid' };
const FREQ_5 = (): QuestionTypeDefinition => ({
  type: 'frequency',
  anchors: ['never', 'yearly', 'monthly', 'weekly', 'daily'].map((k) => ({ key: k, label: k })),
});
const SINGLE_3 = (): QuestionTypeDefinition => ({
  type: 'single_choice',
  options: ['a', 'b', 'c'].map((k) => ({ key: k, label: k })),
});
const MULTI_4 = (): QuestionTypeDefinition => ({
  type: 'multi_choice',
  options: ['w', 'x', 'y', 'z'].map((k) => ({ key: k, label: k })),
});

function makeQuestion(id: string, typeDef: QuestionTypeDefinition): QuestionDefinition {
  return {
    id,
    slug: id,
    version: 1,
    category: 'perf',
    subcategory: null,
    tags: [],
    questionText: 'perf question',
    typeDef,
    presentation: 'value_importance',
    baseWeight: 1,
    sensitive: false,
    active: true,
    answerRateHint: 0.5,
  };
}

/** Type mix matching the real seeded bank: 40% scale, 12.3% frequency, 40% single_choice, 7.7% multi_choice. */
function realisticBank(rng: () => number, size: number): QuestionDefinition[] {
  const out: QuestionDefinition[] = [];
  for (let i = 0; i < size; i++) {
    const roll = rng();
    let typeDef: QuestionTypeDefinition;
    if (roll < 0.4) typeDef = SCALE_1_5;
    else if (roll < 0.523) typeDef = FREQ_5();
    else if (roll < 0.923) typeDef = SINGLE_3();
    else typeDef = MULTI_4();
    out.push(makeQuestion(`q${i}`, typeDef));
  }
  return out;
}

function uniformBank(size: number, typeDef: () => QuestionTypeDefinition): QuestionDefinition[] {
  const out: QuestionDefinition[] = [];
  for (let i = 0; i < size; i++) out.push(makeQuestion(`q${i}`, typeDef()));
  return out;
}

const IMPORTANCE_LEVELS: ImportanceLevel[] = ['irrelevant', 'slight', 'important', 'critical', 'deal_breaker'];

function randomAnswerState(rng: () => number, typeDef: QuestionTypeDefinition): QuestionAnswerState {
  const importance = IMPORTANCE_LEVELS[Math.floor(rng() * IMPORTANCE_LEVELS.length)]!;
  if (typeDef.type === 'scale') {
    return answeredState(
      typeDef.min + Math.floor(rng() * (typeDef.max - typeDef.min + 1)),
      typeDef.min + Math.floor(rng() * (typeDef.max - typeDef.min + 1)),
      importance,
    );
  }
  if (typeDef.type === 'frequency') {
    return answeredState(
      typeDef.anchors[Math.floor(rng() * typeDef.anchors.length)]!.key,
      typeDef.anchors[Math.floor(rng() * typeDef.anchors.length)]!.key,
      importance,
    );
  }
  if (typeDef.type === 'single_choice') {
    return answeredState(typeDef.options[Math.floor(rng() * typeDef.options.length)]!.key, [typeDef.options[Math.floor(rng() * typeDef.options.length)]!.key], importance);
  }
  return answeredState([typeDef.options[0]!.key], [typeDef.options[typeDef.options.length - 1]!.key], importance);
}

/** `density` = probability any given user answered any given question ("dense" ~ engaged user against a realistic bank; "sparse" ~ a small subset of a large bank, per the task brief's stated skepticism). */
function buildUsers(rng: () => number, bank: QuestionDefinition[], count: number, density: number): Map<string, Map<string, QuestionAnswerState>> {
  const users = new Map<string, Map<string, QuestionAnswerState>>();
  for (let u = 0; u < count; u++) {
    const m = new Map<string, QuestionAnswerState>();
    for (const q of bank) {
      if (rng() < density) m.set(q.id, randomAnswerState(rng, q.typeDef));
    }
    users.set(`u${u}`, m);
  }
  return users;
}

function median(values: number[]): number {
  const sorted = [...values].sort((a, b) => a - b);
  return sorted[Math.floor(sorted.length / 2)]!;
}

function log(line: string): void {
  // eslint-disable-next-line no-console
  console.log(`[matrixScoring.perf] ${line}`);
}

// =====================================================================
// ONE-VS-MANY: the real call shape. Median of REPS timed runs, after a
// few warmup iterations so JIT warmup doesn't distort the comparison.
// =====================================================================

function benchOneVsMany(bank: QuestionDefinition[], density: number, candidateCount: number, label: string, reps = 15): { naiveMs: number; matrixMs: number } {
  const rng = mulberry32(42);
  const users = buildUsers(rng, bank, candidateCount + 1, density);
  const ids = [...users.keys()];
  const selfId = ids[0]!;
  const candidateIds = ids.slice(1);
  const selfAnswers = users.get(selfId)!;

  for (let w = 0; w < 5; w++) {
    for (const c of candidateIds) computePairScore(bank, selfAnswers, users.get(c)!, 3, 0);
    computeScoresForCandidatesMatrix(bank, users, selfId, candidateIds, 3, 0);
  }

  const naiveTimes: number[] = [];
  const matrixTimes: number[] = [];
  for (let r = 0; r < reps; r++) {
    let t0 = performance.now();
    for (const c of candidateIds) computePairScore(bank, selfAnswers, users.get(c)!, 3, 0);
    naiveTimes.push(performance.now() - t0);

    t0 = performance.now();
    computeScoresForCandidatesMatrix(bank, users, selfId, candidateIds, 3, 0);
    matrixTimes.push(performance.now() - t0);
  }

  const naiveMs = median(naiveTimes);
  const matrixMs = median(matrixTimes);
  log(`ONE-VS-MANY ${label}: bank=${bank.length} density=${density} candidates=${candidateCount} | naive=${naiveMs.toFixed(3)}ms matrix=${matrixMs.toFixed(3)}ms speedup=${(naiveMs / matrixMs).toFixed(2)}x`);
  return { naiveMs, matrixMs };
}

test('perf: one-vs-many, materialized-refresh shape (K=50)', () => {
  benchOneVsMany(realisticBank(mulberry32(1), 65), 0.85, 50, 'dense/realistic-bank/K50');
  benchOneVsMany(realisticBank(mulberry32(1), 65), 0.15, 50, 'sparse/realistic-bank/K50');
  benchOneVsMany(realisticBank(mulberry32(1), 600), 0.85, 50, 'dense/large-bank/K50');
  benchOneVsMany(realisticBank(mulberry32(1), 600), 0.15, 50, 'sparse/large-bank/K50');
});

test('perf: one-vs-many, max discovery pool shape (K=500)', () => {
  benchOneVsMany(realisticBank(mulberry32(1), 65), 0.85, 500, 'dense/realistic-bank/K500');
  benchOneVsMany(realisticBank(mulberry32(1), 65), 0.15, 500, 'sparse/realistic-bank/K500');
  benchOneVsMany(realisticBank(mulberry32(1), 600), 0.85, 500, 'dense/large-bank/K500');
  benchOneVsMany(realisticBank(mulberry32(1), 600), 0.15, 500, 'sparse/large-bank/K500');
});

test('perf: one-vs-many, ceiling and floor cases by bank composition', () => {
  benchOneVsMany(uniformBank(65, () => (Math.random() < 0.5 ? SCALE_1_5 : FREQ_5())), 0.85, 500, 'CEILING all-ordinal(scale+frequency)/K500');
  benchOneVsMany(uniformBank(65, SINGLE_3), 0.85, 500, 'all-single_choice/K500');
  benchOneVsMany(uniformBank(65, MULTI_4), 0.85, 500, 'FLOOR all-multi_choice(pure fallback)/K500');
});

// =====================================================================
// ALL-PAIRS BLOCK: the shape the technique actually wants. Single
// measurement per scenario (not medianed over reps) since the naive side
// alone is multiple seconds at the larger bank size; a light warmup pass
// at a much smaller N primes the JIT for both paths first.
// =====================================================================

function benchAllPairs(bank: QuestionDefinition[], density: number, n: number, label: string): { naiveMs: number; matrixMs: number } {
  const warmupUsers = buildUsers(mulberry32(999), bank, 20, density);
  const warmupIds = [...warmupUsers.keys()];
  for (let i = 0; i < warmupIds.length; i++) {
    for (let j = 0; j < warmupIds.length; j++) computePairScore(bank, warmupUsers.get(warmupIds[i]!)!, warmupUsers.get(warmupIds[j]!)!, 3, 0);
  }
  computeCompatibilityBlock(bank, warmupUsers, warmupIds, warmupIds, 3, 0);

  const users = buildUsers(mulberry32(7), bank, n, density);
  const ids = [...users.keys()];

  let t0 = performance.now();
  for (let i = 0; i < ids.length; i++) {
    for (let j = 0; j < ids.length; j++) computePairScore(bank, users.get(ids[i]!)!, users.get(ids[j]!)!, 3, 0);
  }
  const naiveMs = performance.now() - t0;

  t0 = performance.now();
  computeCompatibilityBlock(bank, users, ids, ids, 3, 0);
  const matrixMs = performance.now() - t0;

  log(`ALL-PAIRS ${label}: bank=${bank.length} density=${density} n=${n} (${ids.length * ids.length} cells) | naive=${naiveMs.toFixed(1)}ms matrix=${matrixMs.toFixed(1)}ms speedup=${(naiveMs / matrixMs).toFixed(2)}x`);
  return { naiveMs, matrixMs };
}

test('perf: all-pairs block, dense linear algebra\'s natural shape', () => {
  const n = 250;
  benchAllPairs(realisticBank(mulberry32(2), 65), 0.85, n, 'dense/realistic-bank');
  benchAllPairs(realisticBank(mulberry32(2), 65), 0.15, n, 'sparse/realistic-bank');
  benchAllPairs(realisticBank(mulberry32(2), 600), 0.85, n, 'dense/large-bank');
  benchAllPairs(realisticBank(mulberry32(2), 600), 0.15, n, 'sparse/large-bank');
});
