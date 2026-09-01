/**
 * Equivalence tests for matrixScoring.ts against the existing, unmodified
 * scoring path (scoring.ts#aggregateQuestionScores via
 * compatibility.service.ts#computePairScore). Pure, no DB.
 *
 * The bar here is not "close enough": a fast wrong answer is worthless
 * (see docs/matrix-scoring.md). Every comparison below asserts the two
 * paths produce the SAME score, and the randomized suite tracks the
 * largest observed floating-point difference across thousands of trials
 * so that number, not a hand-wave, is what goes in the report.
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { answeredState } from '../../src/domain/questions/index.js';
import type { ImportanceLevel, QuestionAnswerState, QuestionDefinition, QuestionTypeDefinition } from '../../src/domain/questions/index.js';
import { computePairScore } from '../../src/services/compatibility.service.js';
import { computeCompatibilityBlock, computePairScoreMatrix, computeScoresForCandidatesMatrix } from '../../src/domain/questions/matrixScoring.js';

// =====================================================================
// Fixtures
// =====================================================================

let nextId = 0;
function freshId(prefix: string): string {
  nextId += 1;
  return `${prefix}_${nextId}`;
}

function question(typeDef: QuestionTypeDefinition, overrides: Partial<QuestionDefinition> = {}): QuestionDefinition {
  const id = overrides.id ?? freshId('q');
  return {
    id,
    slug: id,
    version: 1,
    category: 'test',
    subcategory: null,
    tags: [],
    questionText: 'test question',
    typeDef,
    presentation: 'value_importance',
    baseWeight: 1,
    sensitive: false,
    active: true,
    answerRateHint: 0.5,
    ...overrides,
  };
}

const SCALE_1_5: QuestionTypeDefinition = { type: 'scale', min: 1, max: 5, minLabel: 'low', maxLabel: 'high', midLabel: 'mid' };
const FREQ_5 = (): QuestionTypeDefinition => ({
  type: 'frequency',
  anchors: [
    { key: 'never', label: 'Never' },
    { key: 'yearly', label: 'Yearly' },
    { key: 'monthly', label: 'Monthly' },
    { key: 'weekly', label: 'Weekly' },
    { key: 'daily', label: 'Daily' },
  ],
});
const SINGLE_3 = (): QuestionTypeDefinition => ({
  type: 'single_choice',
  options: [
    { key: 'a', label: 'A' },
    { key: 'b', label: 'B' },
    { key: 'c', label: 'C' },
  ],
});
const MULTI_4 = (): QuestionTypeDefinition => ({
  type: 'multi_choice',
  options: [
    { key: 'w', label: 'W' },
    { key: 'x', label: 'X' },
    { key: 'y', label: 'Y' },
    { key: 'z', label: 'Z' },
  ],
});

// =====================================================================
// Small, hand-checkable equivalence tests, one per dimension the task
// brief calls out explicitly: every type, every importance level, the
// three non-answer states, and the too-few-shared-questions case.
// =====================================================================

test('matrix path matches scalar path: a mixed-type worked example', () => {
  const questions = [
    question(SCALE_1_5, { id: 'scale1', baseWeight: 1 }),
    question(FREQ_5(), { id: 'freq1', baseWeight: 2 }),
    question(SINGLE_3(), { id: 'choice1', baseWeight: 1.5 }),
    question(MULTI_4(), { id: 'multi1', baseWeight: 3 }),
  ];
  const a = new Map<string, QuestionAnswerState>([
    ['scale1', answeredState(5, 3, 'important')],
    ['freq1', answeredState('daily', 'weekly', 'critical')],
    ['choice1', answeredState('a', ['a', 'b'], 'important')],
    ['multi1', answeredState(['w', 'x'], ['x', 'y'], 'slight')],
  ]);
  const b = new Map<string, QuestionAnswerState>([
    ['scale1', answeredState(2, 4, 'important')],
    ['freq1', answeredState('monthly', 'never', 'critical')],
    ['choice1', answeredState('b', ['a'], 'important')],
    ['multi1', answeredState(['x', 'y', 'z'], ['w'], 'slight')],
  ]);

  const scalar = computePairScore(questions, a, b, 1);
  const matrix = computePairScoreMatrix(questions, a, b, 1);

  assert.equal(matrix.sharedAnsweredQuestionCount, scalar.sharedAnsweredQuestionCount);
  assert.equal(matrix.score, scalar.score);
});

test('matrix path matches scalar path: every importance level, including irrelevant and deal_breaker exclusion', () => {
  const levels: ImportanceLevel[] = ['irrelevant', 'slight', 'important', 'critical', 'deal_breaker'];
  const questions = levels.map((level) => question(SCALE_1_5, { id: `q_${level}`, baseWeight: 1 }));
  const a = new Map<string, QuestionAnswerState>();
  const b = new Map<string, QuestionAnswerState>();
  for (const level of levels) {
    a.set(`q_${level}`, answeredState(4, 2, level));
    b.set(`q_${level}`, answeredState(3, 5, level));
  }

  const scalar = computePairScore(questions, a, b, 1);
  const matrix = computePairScoreMatrix(questions, a, b, 1);
  assert.equal(matrix.sharedAnsweredQuestionCount, scalar.sharedAnsweredQuestionCount);
  assert.equal(matrix.score, scalar.score);
  // irrelevant/deal_breaker must both have been excluded from both paths identically.
  assert.equal(scalar.sharedAnsweredQuestionCount, 3);
});

test('matrix path matches scalar path: the three non-answer states, each type', () => {
  const statuses: QuestionAnswerState[] = [
    { status: 'unanswered', selfValue: null, preferenceValue: null, importance: null },
    { status: 'skipped', selfValue: null, preferenceValue: null, importance: null },
    { status: 'prefer_not_to_say', selfValue: null, preferenceValue: null, importance: null },
  ];
  const typeDefs: QuestionTypeDefinition[] = [SCALE_1_5, FREQ_5(), SINGLE_3(), MULTI_4()];

  for (const typeDef of typeDefs) {
    for (const state of statuses) {
      const q = question(typeDef, { id: freshId('q'), baseWeight: 1 });
      const a = new Map<string, QuestionAnswerState>([[q.id, state]]);
      const b = new Map<string, QuestionAnswerState>([[q.id, answeredState(1, 1, 'important')]]);
      // b's self/pref values are type-inappropriate for freq/single/multi,
      // but that's fine: the question is excluded by A's non-answer status
      // before either side's value is ever read.
      const scalar = computePairScore([q], a, b, 0);
      const matrix = computePairScoreMatrix([q], a, b, 0);
      assert.equal(matrix.sharedAnsweredQuestionCount, 0, `${typeDef.type}/${state.status}`);
      assert.equal(scalar.sharedAnsweredQuestionCount, 0, `${typeDef.type}/${state.status}`);
      assert.equal(matrix.score, scalar.score, `${typeDef.type}/${state.status}`);
    }
  }
});

test('matrix path matches scalar path: too few shared questions falls back to the configured default', () => {
  const questions = [question(SCALE_1_5, { id: 'q1' }), question(SCALE_1_5, { id: 'q2' }), question(SCALE_1_5, { id: 'q3' })];
  const a = new Map<string, QuestionAnswerState>([
    ['q1', answeredState(5, 5, 'important')],
    ['q2', answeredState(5, 5, 'important')],
  ]);
  const b = new Map<string, QuestionAnswerState>([['q1', answeredState(5, 5, 'important')]]);

  for (const noDataDefault of [0, 0.25, 0.5]) {
    const scalar = computePairScore(questions, a, b, 3, noDataDefault);
    const matrix = computePairScoreMatrix(questions, a, b, 3, noDataDefault);
    assert.equal(matrix.sharedAnsweredQuestionCount, 1);
    assert.equal(matrix.score, noDataDefault);
    assert.equal(matrix.score, scalar.score);
  }
});

test('matrix path matches scalar path: frequency version drift (stale anchor key) falls back correctly, not silently wrong', () => {
  const q = question(FREQ_5(), { id: 'freq_drift' });
  const a = new Map<string, QuestionAnswerState>([['freq_drift', answeredState('fortnightly', 'weekly', 'important')]]); // 'fortnightly' not in current anchors
  const b = new Map<string, QuestionAnswerState>([['freq_drift', answeredState('daily', 'monthly', 'important')]]);

  const scalar = computePairScore([q], a, b, 1);
  const matrix = computePairScoreMatrix([q], a, b, 1);
  assert.equal(matrix.sharedAnsweredQuestionCount, scalar.sharedAnsweredQuestionCount);
  assert.equal(matrix.score, scalar.score);
  // frequencyHandler.satisfaction returns 0 (not excluded) for an unresolvable anchor.
  assert.equal(scalar.sharedAnsweredQuestionCount, 1);
});

test('matrix path matches scalar path: single_choice version drift (stale option key in preference set)', () => {
  const q = question(SINGLE_3(), { id: 'choice_drift' });
  const a = new Map<string, QuestionAnswerState>([['choice_drift', answeredState('a', ['a', 'retired_option'], 'important')]]);
  const b = new Map<string, QuestionAnswerState>([['choice_drift', answeredState('b', ['b'], 'important')]]);

  const scalar = computePairScore([q], a, b, 1);
  const matrix = computePairScoreMatrix([q], a, b, 1);
  assert.equal(matrix.sharedAnsweredQuestionCount, scalar.sharedAnsweredQuestionCount);
  assert.equal(matrix.score, scalar.score);
});

test('matrix path matches scalar path: an inactive question contributes nothing on either path', () => {
  const active = question(SCALE_1_5, { id: 'active', active: true });
  const inactive = question(SCALE_1_5, { id: 'inactive', active: false });
  const a = new Map<string, QuestionAnswerState>([
    ['active', answeredState(5, 5, 'important')],
    ['inactive', answeredState(5, 5, 'important')],
  ]);
  const b = new Map<string, QuestionAnswerState>([
    ['active', answeredState(3, 3, 'important')],
    ['inactive', answeredState(3, 3, 'important')],
  ]);
  const scalar = computePairScore([active, inactive], a, b, 1);
  const matrix = computePairScoreMatrix([active, inactive], a, b, 1);
  assert.equal(matrix.sharedAnsweredQuestionCount, 1);
  assert.equal(matrix.score, scalar.score);
});

// =====================================================================
// Batched block equivalence: multiple row users x multiple col users,
// including overlapping row/col sets (self-pairs included, as documented).
// =====================================================================

test('computeCompatibilityBlock matches computePairScore for every cell of an R x C block', () => {
  const questions = [
    question(SCALE_1_5, { id: 'scale1' }),
    question(FREQ_5(), { id: 'freq1', baseWeight: 2 }),
    question(SINGLE_3(), { id: 'choice1' }),
    question(MULTI_4(), { id: 'multi1', baseWeight: 0.5 }),
  ];
  const users = ['u1', 'u2', 'u3', 'u4'];
  const answersByUser = new Map<string, Map<string, QuestionAnswerState>>([
    ['u1', new Map([
      ['scale1', answeredState(5, 1, 'important')],
      ['freq1', answeredState('daily', 'never', 'critical')],
      ['choice1', answeredState('a', ['a', 'c'], 'important')],
      ['multi1', answeredState(['w'], ['w', 'x'], 'slight')],
    ])],
    ['u2', new Map([
      ['scale1', answeredState(1, 5, 'important')],
      ['freq1', answeredState('never', 'daily', 'critical')],
      ['choice1', answeredState('c', ['a'], 'important')],
      ['multi1', answeredState(['x', 'y'], ['w'], 'slight')],
    ])],
    ['u3', new Map([
      ['scale1', answeredState(3, 3, 'slight')],
      ['choice1', answeredState('b', ['b', 'c'], 'critical')],
      // freq1 and multi1 unanswered by u3.
    ])],
    // u4 has no answers at all.
  ]);

  const rowIds = ['u1', 'u2', 'u3', 'u4'];
  const colIds = ['u1', 'u2', 'u3', 'u4'];
  const block = computeCompatibilityBlock(questions, answersByUser, rowIds, colIds, 1, 0);

  for (let i = 0; i < rowIds.length; i++) {
    for (let j = 0; j < colIds.length; j++) {
      const a = answersByUser.get(rowIds[i]!) ?? new Map();
      const b = answersByUser.get(colIds[j]!) ?? new Map();
      const scalar = computePairScore(questions, a, b, 1, 0);
      const idx = i * colIds.length + j;
      assert.equal(block.sharedCounts[idx], scalar.sharedAnsweredQuestionCount, `sharedCount mismatch at (${rowIds[i]},${colIds[j]})`);
      assert.equal(block.scores[idx], scalar.score, `score mismatch at (${rowIds[i]},${colIds[j]})`);
    }
  }
  void users;
});

test('computeScoresForCandidatesMatrix matches computePairScore for a one-vs-many candidate list', () => {
  const questions = [question(SCALE_1_5, { id: 'scale1' }), question(SINGLE_3(), { id: 'choice1' })];
  const answersByUser = new Map<string, Map<string, QuestionAnswerState>>([
    ['self', new Map([
      ['scale1', answeredState(4, 2, 'important')],
      ['choice1', answeredState('a', ['a', 'b'], 'critical')],
    ])],
    ['cand1', new Map([
      ['scale1', answeredState(2, 4, 'important')],
      ['choice1', answeredState('b', ['a'], 'important')],
    ])],
    ['cand2', new Map([['scale1', answeredState(1, 1, 'important')]])], // choice1 unanswered
    ['cand3', new Map()], // nothing at all
  ]);
  const candidateIds = ['cand1', 'cand2', 'cand3'];
  const result = computeScoresForCandidatesMatrix(questions, answersByUser, 'self', candidateIds, 1, 0);

  for (const cid of candidateIds) {
    const scalar = computePairScore(questions, answersByUser.get('self')!, answersByUser.get(cid) ?? new Map(), 1, 0);
    assert.equal(result.get(cid), scalar.score, `mismatch for ${cid}`);
  }
});

// =====================================================================
// Randomized equivalence sweep. Deterministic seeded PRNG so failures are
// reproducible. Every question type, every importance level, the three
// non-answer states, and version-drift are all exercised with real
// probability across the trial count below.
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

const IMPORTANCE_LEVELS: ImportanceLevel[] = ['irrelevant', 'slight', 'important', 'critical', 'deal_breaker'];

function buildRandomBank(rng: () => number, size: number): QuestionDefinition[] {
  const bank: QuestionDefinition[] = [];
  for (let i = 0; i < size; i++) {
    const roll = rng();
    let typeDef: QuestionTypeDefinition;
    if (roll < 0.4) typeDef = SCALE_1_5;
    else if (roll < 0.55) typeDef = FREQ_5();
    else if (roll < 0.85) typeDef = SINGLE_3();
    else typeDef = MULTI_4();
    bank.push(
      question(typeDef, {
        id: `bank_q${i}`,
        baseWeight: 0.5 + rng() * 2.5,
        active: rng() > 0.05, // occasionally inactive
      }),
    );
  }
  return bank;
}

function randomAnswerState(rng: () => number, typeDef: QuestionTypeDefinition): QuestionAnswerState {
  const statusRoll = rng();
  if (statusRoll < 0.15) return { status: 'unanswered', selfValue: null, preferenceValue: null, importance: null };
  if (statusRoll < 0.25) return { status: 'skipped', selfValue: null, preferenceValue: null, importance: null };
  if (statusRoll < 0.32) return { status: 'prefer_not_to_say', selfValue: null, preferenceValue: null, importance: null };

  const importance = IMPORTANCE_LEVELS[Math.floor(rng() * IMPORTANCE_LEVELS.length)]!;
  if (typeDef.type === 'scale') {
    const self = typeDef.min + Math.floor(rng() * (typeDef.max - typeDef.min + 1));
    const pref = typeDef.min + Math.floor(rng() * (typeDef.max - typeDef.min + 1));
    return answeredState(self, pref, importance);
  }
  if (typeDef.type === 'frequency') {
    // 5% of answered frequency states use a stale anchor not in the current def, to exercise the version-drift fallback.
    if (rng() < 0.05) return answeredState('__stale_anchor__', typeDef.anchors[0]!.key, importance);
    const self = typeDef.anchors[Math.floor(rng() * typeDef.anchors.length)]!.key;
    const pref = typeDef.anchors[Math.floor(rng() * typeDef.anchors.length)]!.key;
    return answeredState(self, pref, importance);
  }
  if (typeDef.type === 'single_choice') {
    if (rng() < 0.05) return answeredState('__stale_option__', [typeDef.options[0]!.key], importance);
    const self = typeDef.options[Math.floor(rng() * typeDef.options.length)]!.key;
    const prefCount = 1 + Math.floor(rng() * typeDef.options.length);
    const pref = [...new Set(Array.from({ length: prefCount }, () => typeDef.options[Math.floor(rng() * typeDef.options.length)]!.key))];
    return answeredState(self, pref, importance);
  }
  // multi_choice
  const pick = (max: number) => {
    const n = Math.floor(rng() * (max + 1));
    return [...new Set(Array.from({ length: n }, () => typeDef.options[Math.floor(rng() * typeDef.options.length)]!.key))];
  };
  return answeredState(pick(typeDef.options.length), pick(typeDef.options.length), importance);
}

test('randomized equivalence sweep: matrix path bit-matches scalar path across thousands of pairs', () => {
  const rng = mulberry32(1234567);
  const bank = buildRandomBank(rng, 40);
  const userCount = 30;
  const answersByUser = new Map<string, Map<string, QuestionAnswerState>>();
  for (let u = 0; u < userCount; u++) {
    const m = new Map<string, QuestionAnswerState>();
    for (const q of bank) {
      // Some users skip whole questions entirely (absent from the map), matching real sparse data.
      if (rng() < 0.9) m.set(q.id, randomAnswerState(rng, q.typeDef));
    }
    answersByUser.set(`u${u}`, m);
  }

  let maxAbsDiff = 0;
  let comparisons = 0;
  const thresholds = [0, 1, 3, 5, 10];
  const defaults = [0, 0.5];

  for (let ti = 0; ti < 4000; ti++) {
    const i = Math.floor(rng() * userCount);
    const j = Math.floor(rng() * userCount);
    const a = answersByUser.get(`u${i}`)!;
    const b = answersByUser.get(`u${j}`)!;
    const minShared = thresholds[Math.floor(rng() * thresholds.length)]!;
    const noDataDefault = defaults[Math.floor(rng() * defaults.length)]!;

    const scalar = computePairScore(bank, a, b, minShared, noDataDefault);
    const matrix = computePairScoreMatrix(bank, a, b, minShared, noDataDefault);

    assert.equal(matrix.sharedAnsweredQuestionCount, scalar.sharedAnsweredQuestionCount, `shared count mismatch at trial ${ti} (u${i},u${j})`);
    const diff = Math.abs(matrix.score - scalar.score);
    if (diff > maxAbsDiff) maxAbsDiff = diff;
    comparisons += 1;
    assert.ok(diff < 1e-9, `score mismatch at trial ${ti} (u${i},u${j}): scalar=${scalar.score} matrix=${matrix.score} diff=${diff}`);
  }

  // eslint-disable-next-line no-console
  console.log(`[matrixScoring] randomized sweep: ${comparisons} pair comparisons, max |scalar - matrix| = ${maxAbsDiff}`);
  assert.equal(maxAbsDiff, 0, 'expected bit-for-bit identical scores (same arithmetic, same operand order), not merely close');
});

test('randomized equivalence sweep: batched block matches scalar path one cell at a time', () => {
  const rng = mulberry32(99);
  const bank = buildRandomBank(rng, 25);
  const userCount = 12;
  const answersByUser = new Map<string, Map<string, QuestionAnswerState>>();
  for (let u = 0; u < userCount; u++) {
    const m = new Map<string, QuestionAnswerState>();
    for (const q of bank) {
      if (rng() < 0.85) m.set(q.id, randomAnswerState(rng, q.typeDef));
    }
    answersByUser.set(`u${u}`, m);
  }
  const rowIds = Array.from({ length: userCount }, (_, i) => `u${i}`);
  const colIds = rowIds;
  const block = computeCompatibilityBlock(bank, answersByUser, rowIds, colIds, 2, 0);

  for (let i = 0; i < rowIds.length; i++) {
    for (let j = 0; j < colIds.length; j++) {
      const scalar = computePairScore(bank, answersByUser.get(rowIds[i]!)!, answersByUser.get(colIds[j]!)!, 2, 0);
      const idx = i * colIds.length + j;
      assert.equal(block.sharedCounts[idx], scalar.sharedAnsweredQuestionCount, `(${rowIds[i]},${colIds[j]})`);
      assert.equal(block.scores[idx], scalar.score, `(${rowIds[i]},${colIds[j]})`);
    }
  }
});
