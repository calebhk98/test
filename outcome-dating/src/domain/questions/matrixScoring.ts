/**
 * matrixScoring.ts, a second implementation of pairwise compatibility
 * scoring, built to test one specific idea: can casting per-question
 * satisfaction as a small dense kernel lookup (the "one-hot times a fixed
 * kernel" trick) and batching it over many users at once beat the existing
 * per-pair, per-question scalar path (scoring.ts#aggregateQuestionScores)?
 *
 * ADOPTED, for the one call shape that actually batches: `compatibility
 * .service.ts#refreshAllScores` (the nightly bulk materialization) calls
 * `computeCompatibilityBlock` below, grouping many users' candidate rows
 * against a shared column set instead of scoring one pair at a time, see
 * that function's file-level BLOCK REFRESH doc. It is a second,
 * independently tested code path that MUST produce results identical to
 * scoring.ts#scoreQuestionContribution / aggregateQuestionScores for every
 * input, or it has no value (see tests/unit/matrixScoring.test.ts), and it
 * still does not replace `computePairScore` itself: every OTHER caller in
 * this codebase (`getScore`, `getScoresForCandidates`,
 * `refreshScoresForUser`, the cold path) keeps scoring one user against a
 * candidate list, the shape this technique does NOT clearly win at, and
 * stays on the unchanged scalar path. See docs/matrix-scoring.md for the
 * measured verdict, both the original one-vs-many measurements that led to
 * "reject, as originally shaped" and the block-refresh measurements that
 * led to adopting it for the nightly job specifically.
 *
 * THE IDEA: for a question whose answers live in a small, fixed, ordered
 * domain (scale: 1..5; frequency: an ordered list of anchors), satisfaction
 * between two answers only depends on their indices in that domain. Build a
 * kernel K where K[a][b] is the satisfaction of index a against index b,
 * once per domain size, and look values up in it instead of recomputing
 * `1 - |a - b| / range` (and, for frequency, an anchors.findIndex scan) on
 * every pair. single_choice fits the same shape without even needing a
 * kernel: a preference is already a 0/1 acceptability vector over the
 * option set, so satisfaction is a direct index into it.
 *
 * WHAT THIS DELIBERATELY DOES NOT DO: it does not materialize literal
 * one-hot row vectors and multiply them through K with a generic N x C
 * times C x C times C x M dense matmul. For a one-hot input, `onehot(a) @ K`
 * is just row `a` of K; multiplying that by a one-hot `onehot(b)^T` is just
 * that row's `b`-th entry. Doing the literal matrix multiplication would
 * spend O(C) work per pair to recover a value that is already sitting at a
 * fixed offset, for a domain size C of 5 or so, that is pure waste with no
 * compensating benefit anywhere in this code path. What is implemented
 * below is the computationally-optimal form of the same idea: the O(N) (or
 * O(M)) work of resolving each user's answer to an index happens once, up
 * front, per question, typed-array to typed-array (no Map, no per-pair
 * branch, no handler dispatch); the O(N x M) pairwise sweep is then a flat
 * array gather. This is still "the kernel trick", it is just not a
 * performative BLAS call for its own sake. Where an answer's stored value
 * cannot be resolved into the CURRENT question version's domain at all (a
 * version-drift edge case, see `collectOrdinalInfo`/`collectChoiceInfo`
 * below), that single question falls back to the exact, unmodified
 * `scoreQuestionContribution` scalar path rather than guessing.
 *
 * TYPE COVERAGE: `scale` and `frequency` (kernel gather), `single_choice`
 * (direct indicator gather, no kernel needed at all). `multi_choice`'s
 * satisfaction is a Jaccard ratio (overlap / union) over two option sets of
 * per-question, varying size, not a fixed small domain, and does not
 * reduce to a fixed-size dense lookup the way the other three do. It is
 * scored via the exact same fallback path used for version-drift, i.e. the
 * unmodified `scoreQuestionContribution`, per pair, per question. See
 * docs/matrix-scoring.md for what fraction of a realistic bank that leaves
 * on the fast path versus the fallback path, and whether the fast path is
 * actually faster in practice.
 */
import { importanceMultiplier, isScoringExcludedImportance } from './importance.js';
import { scoreQuestionContribution } from './scoring.js';
import { unansweredState } from './types.js';
import type {
  FrequencyDefinition,
  QuestionAnswerState,
  QuestionDefinition,
  ScaleDefinition,
  SingleChoiceDefinition,
} from './types.js';

const UNANSWERED: QuestionAnswerState = unansweredState();

/**
 * The result of scoring one block of (rowUserIds x colUserIds) pairs.
 * `scores`/`sharedCounts` are row-major, length rowUserIds.length *
 * colUserIds.length: `scores[i * colUserIds.length + j]` is the score for
 * `(rowUserIds[i], colUserIds[j])`, matching what
 * `computePairScore(questions, answersFor(rowUserIds[i]), answersFor(colUserIds[j]), ...)`
 * would have returned.
 */
export interface MatrixScoreResult {
  scores: Float64Array;
  sharedCounts: Int32Array;
}

// =====================================================================
// The ordinal kernel: K[a][b] = 1 - |a - b| / (n - 1), n x n, row-major.
// Cached by n alone, since the value only depends on index distance, not
// on which question or which labels/anchors produced that many buckets
// (a 1-5 scale question and a 5-anchor frequency question share the exact
// same 5x5 kernel).
// =====================================================================

const ordinalKernelCache = new Map<number, Float64Array>();

function ordinalKernel(n: number): Float64Array {
  const cached = ordinalKernelCache.get(n);
  if (cached) return cached;
  const k = new Float64Array(n * n);
  const range = n - 1;
  for (let a = 0; a < n; a++) {
    for (let b = 0; b < n; b++) {
      k[a * n + b] = range <= 0 ? 1 : 1 - Math.abs(a - b) / range;
    }
  }
  ordinalKernelCache.set(n, k);
  return k;
}

// =====================================================================
// Per-question, per-user-list precompute for the ordinal (scale/frequency)
// path.
// =====================================================================

interface OrdinalInfo {
  eligible: Uint8Array;
  selfIdx: Int32Array;
  prefIdx: Int32Array;
  mult: Float64Array;
  /** True if any user's stored value could not be resolved to an index inside [0, n): the whole question falls back to the scalar path for this block rather than risk a wrong answer. */
  outOfDomain: boolean;
}

function collectOrdinalInfo(
  questionId: string,
  indexOf: (value: unknown) => number,
  n: number,
  answersByUser: ReadonlyMap<string, ReadonlyMap<string, QuestionAnswerState>>,
  userIds: readonly string[],
): OrdinalInfo {
  const len = userIds.length;
  const eligible = new Uint8Array(len);
  const selfIdx = new Int32Array(len);
  const prefIdx = new Int32Array(len);
  const mult = new Float64Array(len);
  let outOfDomain = false;

  for (let i = 0; i < len; i++) {
    const state = answersByUser.get(userIds[i]!)?.get(questionId) ?? UNANSWERED;
    if (state.status !== 'answered') continue;
    const importance = state.importance!;
    if (isScoringExcludedImportance(importance)) continue;

    const si = indexOf(state.selfValue);
    const pi = indexOf(state.preferenceValue);
    if (!Number.isInteger(si) || si < 0 || si >= n || !Number.isInteger(pi) || pi < 0 || pi >= n) {
      outOfDomain = true;
      continue;
    }

    eligible[i] = 1;
    selfIdx[i] = si;
    prefIdx[i] = pi;
    mult[i] = importanceMultiplier(importance);
  }

  return { eligible, selfIdx, prefIdx, mult, outOfDomain };
}

function scaleIndexer(def: ScaleDefinition): (value: unknown) => number {
  return (value) => (typeof value === 'number' ? value - def.min : NaN);
}

function frequencyIndexer(def: FrequencyDefinition): (value: unknown) => number {
  const byKey = new Map(def.anchors.map((a, i) => [a.key, i]));
  return (value) => (typeof value === 'string' ? (byKey.get(value) ?? -1) : -1);
}

function contributeOrdinal(
  question: QuestionDefinition,
  answersByUser: ReadonlyMap<string, ReadonlyMap<string, QuestionAnswerState>>,
  rowUserIds: readonly string[],
  colUserIds: readonly string[],
  weightedSum: Float64Array,
  weightTotal: Float64Array,
  sharedCounts: Int32Array,
): void {
  const def = question.typeDef;
  let n: number;
  let indexOf: (value: unknown) => number;
  if (def.type === 'scale') {
    n = Math.max(1, def.max - def.min + 1);
    indexOf = scaleIndexer(def);
  } else if (def.type === 'frequency') {
    n = Math.max(1, def.anchors.length);
    indexOf = frequencyIndexer(def);
  } else {
    throw new Error(`contributeOrdinal called with non-ordinal type "${def.type}"`);
  }

  const rowInfo = collectOrdinalInfo(question.id, indexOf, n, answersByUser, rowUserIds);
  const colInfo = collectOrdinalInfo(question.id, indexOf, n, answersByUser, colUserIds);
  if (rowInfo.outOfDomain || colInfo.outOfDomain) {
    contributeFallback(question, answersByUser, rowUserIds, colUserIds, weightedSum, weightTotal, sharedCounts);
    return;
  }

  const K = ordinalKernel(n);
  const R = rowUserIds.length;
  const C = colUserIds.length;
  for (let i = 0; i < R; i++) {
    if (!rowInfo.eligible[i]) continue;
    const selfI = rowInfo.selfIdx[i]!;
    const prefI = rowInfo.prefIdx[i]!;
    const multI = rowInfo.mult[i]!;
    const rowBase = i * C;
    for (let j = 0; j < C; j++) {
      if (!colInfo.eligible[j]) continue;
      const selfJ = colInfo.selfIdx[j]!;
      const prefJ = colInfo.prefIdx[j]!;
      const satAtoB = K[selfI * n + prefJ]!; // A's self satisfies B's preference
      const satBtoA = K[selfJ * n + prefI]!; // B's self satisfies A's preference
      const satisfaction = (satAtoB + satBtoA) / 2;
      const weight = question.baseWeight * ((multI + colInfo.mult[j]!) / 2);
      const idx = rowBase + j;
      weightedSum[idx]! += satisfaction * weight;
      weightTotal[idx]! += weight;
      sharedCounts[idx]! += 1;
    }
  }
}

// =====================================================================
// single_choice: no kernel needed. A preference is already a 0/1
// acceptability vector over the option set; satisfaction is a direct
// lookup of "is the other side's self-choice in my acceptable set".
// =====================================================================

interface ChoiceInfo {
  eligible: Uint8Array;
  selfIdx: Int32Array;
  /** len * n, row i holds a 0/1 acceptability vector for user i. */
  prefIndicator: Uint8Array;
  mult: Float64Array;
  outOfDomain: boolean;
}

function collectChoiceInfo(
  questionId: string,
  keyIndex: ReadonlyMap<string, number>,
  n: number,
  answersByUser: ReadonlyMap<string, ReadonlyMap<string, QuestionAnswerState>>,
  userIds: readonly string[],
): ChoiceInfo {
  const len = userIds.length;
  const eligible = new Uint8Array(len);
  const selfIdx = new Int32Array(len);
  const prefIndicator = new Uint8Array(len * n);
  const mult = new Float64Array(len);
  let outOfDomain = false;

  for (let i = 0; i < len; i++) {
    const state = answersByUser.get(userIds[i]!)?.get(questionId) ?? UNANSWERED;
    if (state.status !== 'answered') continue;
    const importance = state.importance!;
    if (isScoringExcludedImportance(importance)) continue;

    const si = keyIndex.get(state.selfValue as string);
    const prefKeys = state.preferenceValue as unknown;
    if (si === undefined || !Array.isArray(prefKeys) || prefKeys.length === 0) {
      outOfDomain = true;
      continue;
    }
    let allKnown = true;
    const base = i * n;
    for (const key of prefKeys) {
      const pi = keyIndex.get(key as string);
      if (pi === undefined) {
        allKnown = false;
        break;
      }
      prefIndicator[base + pi] = 1;
    }
    if (!allKnown) {
      outOfDomain = true;
      continue;
    }

    eligible[i] = 1;
    selfIdx[i] = si;
    mult[i] = importanceMultiplier(importance);
  }

  return { eligible, selfIdx, prefIndicator, mult, outOfDomain };
}

function contributeSingleChoice(
  question: QuestionDefinition,
  answersByUser: ReadonlyMap<string, ReadonlyMap<string, QuestionAnswerState>>,
  rowUserIds: readonly string[],
  colUserIds: readonly string[],
  weightedSum: Float64Array,
  weightTotal: Float64Array,
  sharedCounts: Int32Array,
): void {
  const def = question.typeDef as SingleChoiceDefinition;
  const n = Math.max(1, def.options.length);
  const keyIndex = new Map(def.options.map((o, i) => [o.key, i]));

  const rowInfo = collectChoiceInfo(question.id, keyIndex, n, answersByUser, rowUserIds);
  const colInfo = collectChoiceInfo(question.id, keyIndex, n, answersByUser, colUserIds);
  if (rowInfo.outOfDomain || colInfo.outOfDomain) {
    contributeFallback(question, answersByUser, rowUserIds, colUserIds, weightedSum, weightTotal, sharedCounts);
    return;
  }

  const R = rowUserIds.length;
  const C = colUserIds.length;
  for (let i = 0; i < R; i++) {
    if (!rowInfo.eligible[i]) continue;
    const selfI = rowInfo.selfIdx[i]!;
    const multI = rowInfo.mult[i]!;
    const rowBase = i * C;
    const rowPrefBase = i * n;
    for (let j = 0; j < C; j++) {
      if (!colInfo.eligible[j]) continue;
      const selfJ = colInfo.selfIdx[j]!;
      const satAtoB = colInfo.prefIndicator[j * n + selfI]!; // A self in B's acceptable set?
      const satBtoA = rowInfo.prefIndicator[rowPrefBase + selfJ]!; // B self in A's acceptable set?
      const satisfaction = (satAtoB + satBtoA) / 2;
      const weight = question.baseWeight * ((multI + colInfo.mult[j]!) / 2);
      const idx = rowBase + j;
      weightedSum[idx]! += satisfaction * weight;
      weightTotal[idx]! += weight;
      sharedCounts[idx]! += 1;
    }
  }
}

// =====================================================================
// Fallback: the exact, unmodified scoring.ts#scoreQuestionContribution,
// called per pair. Used for multi_choice always (its Jaccard satisfaction
// is not a fixed-size dense lookup) and for any question that hit a
// version-drift domain mismatch above. Not vectorized, not faster than
// today's path; correctness, not speed, is the point of this branch.
// =====================================================================

function contributeFallback(
  question: QuestionDefinition,
  answersByUser: ReadonlyMap<string, ReadonlyMap<string, QuestionAnswerState>>,
  rowUserIds: readonly string[],
  colUserIds: readonly string[],
  weightedSum: Float64Array,
  weightTotal: Float64Array,
  sharedCounts: Int32Array,
): void {
  const R = rowUserIds.length;
  const C = colUserIds.length;
  const rowStates = rowUserIds.map((u) => answersByUser.get(u)?.get(question.id) ?? UNANSWERED);
  const colStates = colUserIds.map((u) => answersByUser.get(u)?.get(question.id) ?? UNANSWERED);

  for (let i = 0; i < R; i++) {
    const a = rowStates[i]!;
    const rowBase = i * C;
    for (let j = 0; j < C; j++) {
      const b = colStates[j]!;
      const contribution = scoreQuestionContribution(question, a, b);
      if (contribution.excluded) continue;
      const idx = rowBase + j;
      weightedSum[idx]! += contribution.satisfaction! * contribution.weight;
      weightTotal[idx]! += contribution.weight;
      sharedCounts[idx]! += 1;
    }
  }
}

// =====================================================================
// Public entry points
// =====================================================================

/**
 * Scores every (rowUserIds[i], colUserIds[j]) pair against `questions`,
 * batched: each question is visited once and contributes to every pair in
 * the block in one pass, rather than every pair visiting every question
 * once (today's `aggregateQuestionScores` shape, called once per pair).
 * `rowUserIds` and `colUserIds` need not be disjoint; each cell is scored
 * independently and identically to
 * `computePairScore(questions, answersFor(row), answersFor(col), ...)`
 * regardless of overlap, INCLUDING the `row === col` (self-pair) case,
 * which callers should filter out themselves if they don't want it, same
 * as they would have to with `computePairScore`.
 */
export function computeCompatibilityBlock(
  questions: readonly QuestionDefinition[],
  answersByUser: ReadonlyMap<string, ReadonlyMap<string, QuestionAnswerState>>,
  rowUserIds: readonly string[],
  colUserIds: readonly string[],
  minSharedQuestions: number,
  noDataDefaultScore = 0,
): MatrixScoreResult {
  const R = rowUserIds.length;
  const C = colUserIds.length;
  const weightedSum = new Float64Array(R * C);
  const weightTotal = new Float64Array(R * C);
  const sharedCounts = new Int32Array(R * C);

  for (const question of questions) {
    if (!question.active) continue;
    switch (question.typeDef.type) {
      case 'scale':
      case 'frequency':
        contributeOrdinal(question, answersByUser, rowUserIds, colUserIds, weightedSum, weightTotal, sharedCounts);
        break;
      case 'single_choice':
        contributeSingleChoice(question, answersByUser, rowUserIds, colUserIds, weightedSum, weightTotal, sharedCounts);
        break;
      case 'multi_choice':
        contributeFallback(question, answersByUser, rowUserIds, colUserIds, weightedSum, weightTotal, sharedCounts);
        break;
    }
  }

  const scores = new Float64Array(R * C);
  for (let idx = 0; idx < R * C; idx++) {
    const shared = sharedCounts[idx]!;
    const total = weightTotal[idx]!;
    scores[idx] = shared < minSharedQuestions ? noDataDefaultScore : total > 0 ? weightedSum[idx]! / total : noDataDefaultScore;
  }

  return { scores, sharedCounts };
}

/**
 * Single-pair convenience wrapper, matching
 * `compatibility.service.ts#computePairScore`'s signature and return shape
 * closely enough for a direct, side-by-side equivalence test. Not how a
 * real caller should use this module (a 1x1 block pays all the setup cost
 * of the batched path for none of its benefit); see
 * `computeScoresForCandidatesMatrix` below for the batched shape a real
 * caller wants.
 */
export function computePairScoreMatrix(
  questions: readonly QuestionDefinition[],
  answersA: ReadonlyMap<string, QuestionAnswerState>,
  answersB: ReadonlyMap<string, QuestionAnswerState>,
  minSharedQuestions: number,
  noDataDefaultScore = 0,
): { score: number; sharedAnsweredQuestionCount: number } {
  const answersByUser = new Map<string, ReadonlyMap<string, QuestionAnswerState>>([
    ['__a__', answersA],
    ['__b__', answersB],
  ]);
  const result = computeCompatibilityBlock(questions, answersByUser, ['__a__'], ['__b__'], minSharedQuestions, noDataDefaultScore);
  return { score: result.scores[0]!, sharedAnsweredQuestionCount: result.sharedCounts[0]! };
}

/**
 * Batched one-vs-many shape matching
 * `compatibility.service.ts#getScoresForCandidates`: one user against a
 * list of candidates, in a single pass over the question bank instead of
 * one pass per candidate. This is the realistic integration seam for the
 * discovery-candidate-scoring call site, if adopted (see
 * docs/matrix-scoring.md).
 */
export function computeScoresForCandidatesMatrix(
  questions: readonly QuestionDefinition[],
  answersByUser: ReadonlyMap<string, ReadonlyMap<string, QuestionAnswerState>>,
  userId: string,
  candidateIds: readonly string[],
  minSharedQuestions: number,
  noDataDefaultScore = 0,
): Map<string, number> {
  const result = computeCompatibilityBlock(questions, answersByUser, [userId], candidateIds, minSharedQuestions, noDataDefaultScore);
  const out = new Map<string, number>();
  for (let j = 0; j < candidateIds.length; j++) {
    out.set(candidateIds[j]!, result.scores[j]!);
  }
  return out;
}
