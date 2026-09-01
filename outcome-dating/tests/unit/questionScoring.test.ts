/**
 * Pure-function unit tests for src/domain/questions/**.
 *
 * No database, everything under test here is pure (scoring.ts,
 * importance.ts, typeHandlers.ts, ladder.ts, selector.ts, dealBreakers.ts,
 * tags.ts). DB-backed tests for the service-layer wrappers live in
 * tests/unit/question.service.test.ts.
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  IMPORTANCE_LEVELS,
  IMPORTANCE_MULTIPLIER,
  importanceMultiplier,
  scoreQuestionContribution,
  aggregateQuestionScores,
  getTypeHandler,
  selectNextQuestions,
  DEFAULT_SKIP_COOLDOWN_DAYS,
  deriveDealBreakerFilterRows,
  deriveDealBreakerFilterRowsForQuestion,
  evaluateDealBreakers,
  scoreTagIntensityMatch,
  passesAvoidTagFilter,
  isLadderEligible,
  presentationFor,
  ladderLabels,
  ladderPositionToPreference,
  preferenceToLadderPosition,
  LADDER_POSITIONS,
  answeredState,
  skippedState,
  unansweredState,
  preferNotToSayState,
} from '../../src/domain/questions/index.js';
import type {
  QuestionDefinition,
  ScaleDefinition,
  SingleChoiceDefinition,
  MultiChoiceDefinition,
  FrequencyDefinition,
  QuestionAnswerState,
  LadderPosition,
} from '../../src/domain/questions/index.js';

// =====================================================================
// Fixtures
// =====================================================================

let idCounter = 0;
function nextId(): string {
  idCounter += 1;
  return `q-${idCounter}`;
}

function scaleQuestion(overrides?: Partial<QuestionDefinition> & { typeDef?: Partial<ScaleDefinition> }): QuestionDefinition {
  const typeDef: ScaleDefinition = {
    type: 'scale',
    min: 1,
    max: 5,
    minLabel: 'Not at all important',
    maxLabel: 'Extremely important',
    midLabel: 'Somewhat important',
    ...overrides?.typeDef,
  };
  return {
    id: nextId(),
    slug: 'test-scale',
    version: 1,
    category: 'lifestyle',
    subcategory: null,
    tags: [],
    questionText: 'How important is X to you?',
    typeDef,
    presentation: presentationFor(typeDef),
    baseWeight: 1,
    sensitive: false,
    active: true,
    answerRateHint: 0.5,
    ...overrides,
  };
}

const KIDS_OPTIONS = [
  { key: 'no_kids_no_want', label: 'No children, and do not want any' },
  { key: 'no_kids_want', label: 'No children, but want them' },
  { key: 'has_kids_want_more', label: 'Have children and want more' },
  { key: 'has_kids_no_more', label: 'Have children and do not want more' },
  { key: 'still_deciding', label: 'Still deciding' },
];

function singleChoiceQuestion(overrides?: Partial<QuestionDefinition> & { typeDef?: Partial<SingleChoiceDefinition> }): QuestionDefinition {
  const typeDef: SingleChoiceDefinition = {
    type: 'single_choice',
    options: KIDS_OPTIONS,
    ...overrides?.typeDef,
  };
  return {
    id: nextId(),
    slug: 'test-single-choice',
    version: 1,
    category: 'family',
    subcategory: null,
    tags: [],
    questionText: 'Children',
    typeDef,
    presentation: presentationFor(typeDef),
    baseWeight: 2,
    sensitive: false,
    active: true,
    answerRateHint: 0.5,
    ...overrides,
  };
}

const BINARY_OPTIONS = [
  { key: 'no', label: 'I do not smoke' },
  { key: 'yes', label: 'I smoke' },
];

function binaryQuestion(overrides?: Partial<QuestionDefinition>): QuestionDefinition {
  const typeDef: SingleChoiceDefinition = { type: 'single_choice', options: BINARY_OPTIONS };
  return {
    id: nextId(),
    slug: 'test-binary',
    version: 1,
    category: 'lifestyle',
    subcategory: null,
    tags: [],
    questionText: 'Smoking',
    typeDef,
    presentation: presentationFor(typeDef),
    baseWeight: 1,
    sensitive: false,
    active: true,
    answerRateHint: 0.5,
    ...overrides,
  };
}

function multiChoiceQuestion(overrides?: Partial<QuestionDefinition> & { typeDef?: Partial<MultiChoiceDefinition> }): QuestionDefinition {
  const typeDef: MultiChoiceDefinition = {
    type: 'multi_choice',
    options: [
      { key: 'spanish', label: 'Spanish' },
      { key: 'french', label: 'French' },
      { key: 'mandarin', label: 'Mandarin' },
    ],
    ...overrides?.typeDef,
  };
  return {
    id: nextId(),
    slug: 'test-multi',
    version: 1,
    category: 'interests',
    subcategory: null,
    tags: [],
    questionText: 'Languages spoken',
    typeDef,
    presentation: presentationFor(typeDef),
    baseWeight: 1,
    sensitive: false,
    active: true,
    answerRateHint: 0.5,
    ...overrides,
  };
}

function frequencyQuestion(overrides?: Partial<QuestionDefinition> & { typeDef?: Partial<FrequencyDefinition> }): QuestionDefinition {
  const typeDef: FrequencyDefinition = {
    type: 'frequency',
    anchors: [
      { key: 'never', label: 'Never' },
      { key: 'yearly', label: 'A few times a year' },
      { key: 'monthly', label: 'Monthly' },
      { key: 'weekly', label: 'Weekly' },
      { key: 'daily', label: 'Daily' },
    ],
    ...overrides?.typeDef,
  };
  return {
    id: nextId(),
    slug: 'test-frequency',
    version: 1,
    category: 'health',
    subcategory: null,
    tags: [],
    questionText: 'How often do you exercise?',
    typeDef,
    presentation: presentationFor(typeDef),
    baseWeight: 1,
    sensitive: false,
    active: true,
    answerRateHint: 0.5,
    ...overrides,
  };
}

// =====================================================================
// Importance multipliers
// =====================================================================

test('importance: documented multiplier ordering irrelevant < slight < important < critical', () => {
  assert.equal(IMPORTANCE_MULTIPLIER.irrelevant, 0);
  assert.equal(IMPORTANCE_MULTIPLIER.slight, 0.5);
  assert.equal(IMPORTANCE_MULTIPLIER.important, 1.0);
  assert.equal(IMPORTANCE_MULTIPLIER.critical, 2.0);
  assert.ok(IMPORTANCE_MULTIPLIER.irrelevant < IMPORTANCE_MULTIPLIER.slight);
  assert.ok(IMPORTANCE_MULTIPLIER.slight < IMPORTANCE_MULTIPLIER.important);
  assert.ok(IMPORTANCE_MULTIPLIER.important < IMPORTANCE_MULTIPLIER.critical);
  // deal_breaker is deliberately NOT "higher than critical", it is off
  // the scoring axis entirely (see importance.ts doc).
  assert.equal(IMPORTANCE_MULTIPLIER.deal_breaker, 0);
});

test('importance: every level has a documented multiplier', () => {
  for (const level of IMPORTANCE_LEVELS) {
    assert.equal(typeof importanceMultiplier(level), 'number');
  }
});

// =====================================================================
// scoreQuestionContribution, importance semantics
// =====================================================================

test('scoreQuestionContribution: irrelevant on either side excludes the question entirely (zero weight, no satisfaction)', () => {
  const q = scaleQuestion();
  const a = answeredState(5, 5, 'irrelevant');
  const b = answeredState(1, 1, 'important');

  const result = scoreQuestionContribution(q, a, b);
  assert.equal(result.excluded, true);
  assert.equal(result.reason, 'irrelevant');
  assert.equal(result.weight, 0);
  assert.equal(result.satisfaction, null);
});

test('scoreQuestionContribution: deal_breaker excludes from weighted scoring (not a very-large weight)', () => {
  const q = scaleQuestion({ baseWeight: 10 });
  const a = answeredState(5, 5, 'deal_breaker');
  const b = answeredState(1, 1, 'important');

  const result = scoreQuestionContribution(q, a, b);
  assert.equal(result.excluded, true);
  assert.equal(result.reason, 'deal_breaker');
  assert.equal(result.weight, 0, 'a deal breaker must contribute ZERO weight to the weighted average, not a large one');
  assert.equal(result.satisfaction, null);
});

test('scoreQuestionContribution: weight ordering across importance levels (slight < important < critical), all else equal', () => {
  const q = scaleQuestion({ baseWeight: 1 });
  const self = 3;
  const pref = 3;

  function weightFor(importance: 'slight' | 'important' | 'critical'): number {
    const a = answeredState(self, pref, importance);
    const b = answeredState(self, pref, importance);
    return scoreQuestionContribution(q, a, b).weight;
  }

  const slight = weightFor('slight');
  const important = weightFor('important');
  const critical = weightFor('critical');

  assert.ok(slight < important, `slight (${slight}) must weigh less than important (${important})`);
  assert.ok(important < critical, `important (${important}) must weigh less than critical (${critical})`);
  assert.ok(Math.abs(slight - 0.5) < 1e-9);
  assert.ok(Math.abs(important - 1) < 1e-9);
  assert.ok(Math.abs(critical - 2) < 1e-9);
});

test('scoreQuestionContribution: symmetric under swapping argument order', () => {
  const q = scaleQuestion();
  const a = answeredState(2, 5, 'critical');
  const b = answeredState(4, 3, 'slight');

  const forward = scoreQuestionContribution(q, a, b);
  const backward = scoreQuestionContribution(q, b, a);

  assert.ok(Math.abs(forward.satisfaction! - backward.satisfaction!) < 1e-9);
  assert.ok(Math.abs(forward.weight - backward.weight) < 1e-9);
});

// ---- three non-answer states, all excluded ----

test('scoreQuestionContribution: unanswered excludes', () => {
  const q = scaleQuestion();
  const result = scoreQuestionContribution(q, unansweredState(), answeredState(3, 3, 'important'));
  assert.equal(result.excluded, true);
  assert.equal(result.reason, 'unanswered');
  assert.equal(result.weight, 0);
});

test('scoreQuestionContribution: skipped excludes', () => {
  const q = scaleQuestion();
  const result = scoreQuestionContribution(q, skippedState(), answeredState(3, 3, 'important'));
  assert.equal(result.excluded, true);
  assert.equal(result.reason, 'skipped');
  assert.equal(result.weight, 0);
});

test('scoreQuestionContribution: prefer_not_to_say excludes and is treated as neutral (not a match, not a mismatch)', () => {
  const q = scaleQuestion();
  const result = scoreQuestionContribution(q, preferNotToSayState(), answeredState(3, 3, 'important'));
  assert.equal(result.excluded, true);
  assert.equal(result.reason, 'prefer_not_to_say');
  assert.equal(result.weight, 0);
  assert.equal(result.satisfaction, null);
});

test('scoreQuestionContribution: inactive question never contributes', () => {
  const q = scaleQuestion({ active: false });
  const result = scoreQuestionContribution(q, answeredState(5, 5, 'critical'), answeredState(5, 5, 'critical'));
  assert.equal(result.excluded, true);
  assert.equal(result.reason, 'not_active');
});

// =====================================================================
// Per-type scoring correctness
// =====================================================================

test('scale: satisfaction is 1 minus normalized distance', () => {
  const q = scaleQuestion(); // min 1, max 5 -> range 4
  const a = answeredState(5, 5, 'important'); // A is 5, wants a 5
  const b = answeredState(1, 5, 'important'); // B is 1, wants a 5
  const result = scoreQuestionContribution(q, a, b);
  // satisfactionAtoB = handler(A.self=5, B.pref=5) = 1
  // satisfactionBtoA = handler(B.self=1, A.pref=5) = 1 - |1-5|/4 = 0
  // pair = (1+0)/2 = 0.5
  assert.ok(Math.abs(result.satisfaction! - 0.5) < 1e-9);
});

test('single_choice: satisfaction is binary, in the acceptable set or not, no midpoint fuzziness', () => {
  const q = singleChoiceQuestion();
  // A has_kids_want_more, wants a partner who also has_kids_want_more or has_kids_no_more.
  const a = answeredState('has_kids_want_more', ['has_kids_want_more', 'has_kids_no_more'], 'critical');
  // B has_kids_no_more, wants a partner in {has_kids_want_more}.
  const bAcceptable = answeredState('has_kids_no_more', ['has_kids_want_more'], 'critical');
  const resultAcceptable = scoreQuestionContribution(q, a, bAcceptable);
  // A satisfies B's want (A is has_kids_want_more, in B's set) -> 1
  // B satisfies A's want (B is has_kids_no_more, in A's set) -> 1
  assert.ok(Math.abs(resultAcceptable.satisfaction! - 1) < 1e-9);

  const bUnacceptable = answeredState('still_deciding', ['has_kids_want_more'], 'critical');
  const resultUnacceptable = scoreQuestionContribution(q, a, bUnacceptable);
  // A satisfies B's want (A is has_kids_want_more, in B's set) -> 1
  // B does NOT satisfy A's want (B is still_deciding, not in A's {has_kids_want_more, has_kids_no_more}) -> 0
  assert.ok(Math.abs(resultUnacceptable.satisfaction! - 0.5) < 1e-9);
});

test('multi_choice: satisfaction is set overlap (Jaccard), not mere co-presence', () => {
  const q = multiChoiceQuestion();
  const a = answeredState(['spanish', 'french'], ['spanish'], 'important');
  const b = answeredState(['spanish'], ['spanish', 'french'], 'important');
  const result = scoreQuestionContribution(q, a, b);
  // A satisfies B's want: self={spanish,french}, pref={spanish,french} -> overlap=2,union=2 -> 1
  // B satisfies A's want: self={spanish}, pref={spanish} -> overlap=1,union=1 -> 1
  assert.ok(Math.abs(result.satisfaction! - 1) < 1e-9);

  const handler = getTypeHandler('multi_choice');
  const partial = handler.satisfaction(q.typeDef, ['spanish'], ['spanish', 'french', 'mandarin']);
  assert.ok(Math.abs(partial - 1 / 3) < 1e-9, `expected 1/3 overlap, got ${partial}`);
});

test('frequency: ordinal distance, concrete anchors, not a bare number', () => {
  const q = frequencyQuestion();
  const handler = getTypeHandler('frequency');
  assert.ok(Math.abs(handler.satisfaction(q.typeDef, 'never', 'daily') - 0) < 1e-9);
  assert.ok(Math.abs(handler.satisfaction(q.typeDef, 'weekly', 'daily') - 0.75) < 1e-9);
  assert.ok(Math.abs(handler.satisfaction(q.typeDef, 'monthly', 'monthly') - 1) < 1e-9);
});

// =====================================================================
// aggregateQuestionScores, end-to-end accumulation with sparse overlap
// =====================================================================

test('aggregateQuestionScores: two users overlapping on only a handful of (600-question-bank-sized) questions', () => {
  const questions: QuestionDefinition[] = [];
  for (let i = 0; i < 50; i++) questions.push(scaleQuestion({ id: `bulk-${i}`, slug: `bulk-${i}` }));

  const answersA = new Map<string, QuestionAnswerState>();
  const answersB = new Map<string, QuestionAnswerState>();
  // Only 3 of the 50 are shared/answered by both.
  answersA.set(questions[0]!.id, answeredState(5, 5, 'important'));
  answersB.set(questions[0]!.id, answeredState(5, 5, 'important'));
  answersA.set(questions[1]!.id, answeredState(1, 1, 'critical'));
  answersB.set(questions[1]!.id, answeredState(5, 5, 'critical'));
  answersA.set(questions[2]!.id, answeredState(3, 3, 'important'));
  answersB.set(questions[2]!.id, answeredState(3, 3, 'important'));
  // A answered a 4th question B never touched -> excluded (unanswered on B's side).
  answersA.set(questions[3]!.id, answeredState(5, 5, 'important'));

  const result = aggregateQuestionScores(questions, answersA, answersB);
  assert.equal(result.scoredQuestionCount, 3);
  assert.ok(result.score > 0 && result.score < 1);
});

test('aggregateQuestionScores: no overlap at all defaults to noDataDefaultScore', () => {
  const questions = [scaleQuestion()];
  const result = aggregateQuestionScores(questions, new Map(), new Map(), 0.42);
  assert.equal(result.score, 0.42);
  assert.equal(result.scoredQuestionCount, 0);
});

// =====================================================================
// Ladder presentation
// =====================================================================

test('ladder: eligible only for exactly-two-option single_choice; presentationFor is explicit and server-computed', () => {
  const binary = binaryQuestion();
  assert.equal(isLadderEligible(binary.typeDef), true);
  assert.equal(binary.presentation, 'ladder');

  const kids = singleChoiceQuestion(); // 5 options
  assert.equal(isLadderEligible(kids.typeDef), false);
  assert.equal(kids.presentation, 'value_importance');

  const scale = scaleQuestion();
  assert.equal(scale.presentation, 'value_importance');

  const multi = multiChoiceQuestion();
  assert.equal(multi.presentation, 'value_importance');

  const freq = frequencyQuestion();
  assert.equal(freq.presentation, 'value_importance');
});

test('ladder: labels are plain language, built from the question\'s own option labels, no bare numbers, no section marks', () => {
  const binary = binaryQuestion();
  const labels = ladderLabels(binary.typeDef as SingleChoiceDefinition);
  assert.equal(labels.length, 5);
  assert.equal(labels[0], 'Deal breaker: I do not smoke');
  assert.equal(labels[2], "Don't care");
  assert.equal(labels[4], 'Deal breaker: I smoke');
  for (const label of labels) {
    assert.ok(!/§/.test(label));
    assert.ok(!/^\d+$/.test(label));
  }
});

test('ladder: position <-> (value, importance) round-trips over every position', () => {
  const def = binaryQuestion().typeDef as SingleChoiceDefinition;
  for (const position of LADDER_POSITIONS) {
    const pref = ladderPositionToPreference(def, position);
    const roundTripped = preferenceToLadderPosition(def, pref.preferenceValue, pref.importance);
    assert.equal(roundTripped, position, `position ${position} did not round-trip (got ${roundTripped})`);
  }
});

test('ladder: don\'t care maps to irrelevant; both deal-breaker ends map to deal_breaker with the value determining which side', () => {
  const def = binaryQuestion().typeDef as SingleChoiceDefinition;

  const dontCare = ladderPositionToPreference(def, 2);
  assert.equal(dontCare.importance, 'irrelevant');

  const dbNo = ladderPositionToPreference(def, 0);
  assert.equal(dbNo.importance, 'deal_breaker');
  assert.deepEqual(dbNo.preferenceValue, ['no']);

  const dbYes = ladderPositionToPreference(def, 4);
  assert.equal(dbYes.importance, 'deal_breaker');
  assert.deepEqual(dbYes.preferenceValue, ['yes']);

  const preferNo = ladderPositionToPreference(def, 1);
  const preferYes = ladderPositionToPreference(def, 3);
  // "the middle two map to the intermediate importance levels", not irrelevant, not deal_breaker.
  assert.notEqual(preferNo.importance, 'irrelevant');
  assert.notEqual(preferNo.importance, 'deal_breaker');
  assert.notEqual(preferYes.importance, 'irrelevant');
  assert.notEqual(preferYes.importance, 'deal_breaker');
  assert.deepEqual(preferNo.preferenceValue, ['no']);
  assert.deepEqual(preferYes.preferenceValue, ['yes']);
});

test('ladder vs. two-control presentations score identically for the equivalent underlying (value, importance) pair', () => {
  const def = binaryQuestion().typeDef as SingleChoiceDefinition;
  const q = binaryQuestion({ typeDef: def as unknown as SingleChoiceDefinition });

  // Two users: A picks ladder position 4 ("Deal breaker: I smoke" side ==
  // wants a smoker, no tolerance). B fills the equivalent two-control form
  // directly with the same underlying pair.
  const ladderPref = ladderPositionToPreference(def, 4);
  const aViaLadder = answeredState('yes', ladderPref.preferenceValue, ladderPref.importance);
  const aViaControls = answeredState('yes', ['yes'], 'deal_breaker');

  const partner = answeredState('yes', ['yes', 'no'], 'irrelevant');

  const viaLadder = scoreQuestionContribution(q, aViaLadder, partner);
  const viaControls = scoreQuestionContribution(q, aViaControls, partner);

  assert.deepEqual(viaLadder, viaControls, 'presentation must not change the maths');
});

// =====================================================================
// Selector
// =====================================================================

function makeBank(count: number, categories: string[]): QuestionDefinition[] {
  const bank: QuestionDefinition[] = [];
  for (let i = 0; i < count; i++) {
    const category = categories[i % categories.length]!;
    bank.push(
      scaleQuestion({
        id: `bank-${i}`,
        slug: `bank-${i}`,
        category,
        baseWeight: 0.5 + (i % 5) * 0.5,
        answerRateHint: 0.2 + (i % 5) * 0.15,
      }),
    );
  }
  return bank;
}

test('selector: excludes answered, prefer_not_to_say, and recently-skipped questions', () => {
  const bank = makeBank(20, ['lifestyle', 'values']);
  const now = new Date('2026-06-01T00:00:00Z');
  const history = new Map([
    ['bank-0', { status: 'answered' as const, at: now }],
    ['bank-1', { status: 'prefer_not_to_say' as const, at: now }],
    ['bank-2', { status: 'skipped' as const, at: now }], // just skipped, inside cooldown
  ]);

  const selected = selectNextQuestions({ questions: bank, history, now, count: 20 });
  const slugs = new Set(selected.map((s) => s.question.slug));
  assert.ok(!slugs.has('bank-0'));
  assert.ok(!slugs.has('bank-1'));
  assert.ok(!slugs.has('bank-2'));
});

test('selector: a skip older than the cooldown becomes eligible again', () => {
  const bank = makeBank(5, ['lifestyle']);
  const now = new Date('2026-06-01T00:00:00Z');
  const oldSkip = new Date(now.getTime() - (DEFAULT_SKIP_COOLDOWN_DAYS + 1) * 24 * 60 * 60 * 1000);
  const history = new Map([['bank-0', { status: 'skipped' as const, at: oldSkip }]]);

  const selected = selectNextQuestions({ questions: bank, history, now, count: 5 });
  assert.ok(selected.some((s) => s.question.slug === 'bank-0'));
});

test('selector: category-balances, under-represented categories are prioritized', () => {
  const bank = makeBank(20, ['lifestyle', 'values']);
  const now = new Date('2026-06-01T00:00:00Z');
  // User has answered 5 lifestyle questions and 0 values questions.
  const history = new Map<string, { status: 'answered' | 'skipped' | 'prefer_not_to_say'; at: Date }>();
  for (let i = 0; i < 20; i += 2) history.set(`bank-${i}`, { status: 'answered', at: now }); // all lifestyle (even indices)

  const selected = selectNextQuestions({ questions: bank, history, now, count: 3 });
  const categories = selected.map((s) => s.question.category);
  assert.ok(categories.every((c) => c === 'values'), `expected values-category questions prioritized, got ${categories.join(',')}`);
});

test('selector: 600+ question bank stays fast and returns a sensible batch', () => {
  const bank = makeBank(650, ['lifestyle', 'values', 'family', 'social', 'health', 'interests', 'communication', 'logistics']);
  const now = new Date('2026-06-01T00:00:00Z');
  const history = new Map<string, { status: 'answered' | 'skipped' | 'prefer_not_to_say'; at: Date }>();
  for (let i = 0; i < 40; i++) history.set(`bank-${i}`, { status: 'answered', at: now });

  const start = performance.now();
  const selected = selectNextQuestions({ questions: bank, history, now, count: 10 });
  const elapsedMs = performance.now() - start;

  assert.equal(selected.length, 10);
  assert.ok(elapsedMs < 50, `selectNextQuestions over 650 questions took ${elapsedMs}ms, expected < 50ms`);
});

test('selector: performance does not degrade badly as the bank grows (600 -> 6000)', () => {
  const categories = ['lifestyle', 'values', 'family', 'social', 'health', 'interests', 'communication', 'logistics'];
  const smallBank = makeBank(600, categories);
  const bigBank = makeBank(6000, categories);
  const now = new Date('2026-06-01T00:00:00Z');
  const history = new Map<string, { status: 'answered' | 'skipped' | 'prefer_not_to_say'; at: Date }>();
  for (let i = 0; i < 40; i++) history.set(`bank-${i}`, { status: 'answered', at: now });

  const t0 = performance.now();
  selectNextQuestions({ questions: smallBank, history, now, count: 10 });
  const smallMs = performance.now() - t0;

  const t1 = performance.now();
  selectNextQuestions({ questions: bigBank, history, now, count: 10 });
  const bigMs = performance.now() - t1;

  // 10x the questions should not cost anywhere near 10x quadratic blowup
  // (O(n log n) predicts roughly ~11-12x, not e.g. 100x for O(n^2)).
  assert.ok(bigMs < smallMs * 40 + 20, `bank 10x larger took ${bigMs}ms vs ${smallMs}ms for the smaller bank, looks superlinear`);
});

// =====================================================================
// Deal breakers, derivation + evaluation
// =====================================================================

test('deriveDealBreakerFilterRowsForQuestion: no filter for a non-deal-breaker answer', () => {
  const q = singleChoiceQuestion();
  const rows = deriveDealBreakerFilterRowsForQuestion(q, answeredState('has_kids_want_more', ['has_kids_want_more'], 'critical'));
  assert.deepEqual(rows, []);
});

test('deriveDealBreakerFilterRowsForQuestion: single_choice deal breaker derives an "in" filter over the acceptable set, prefixed qb:', () => {
  const q = singleChoiceQuestion();
  const rows = deriveDealBreakerFilterRowsForQuestion(q, answeredState('has_kids_want_more', ['has_kids_want_more', 'still_deciding'], 'deal_breaker'));
  assert.equal(rows.length, 1);
  assert.equal(rows[0]!.filterKey, 'qb:test-single-choice');
  assert.equal(rows[0]!.operator, 'in');
  assert.deepEqual(rows[0]!.value, ['has_kids_want_more', 'still_deciding']);
  assert.equal(rows[0]!.enabled, true);
  assert.equal(rows[0]!.excludeIfUnset, true);
});

test('deriveDealBreakerFilterRowsForQuestion: scale/frequency deal breaker derives an exact "eq" filter (zero tolerance)', () => {
  const q = scaleQuestion();
  const rows = deriveDealBreakerFilterRowsForQuestion(q, answeredState(5, 5, 'deal_breaker'));
  assert.equal(rows.length, 1);
  assert.equal(rows[0]!.operator, 'eq');
  assert.equal(rows[0]!.value, 5);
});

test('deriveDealBreakerFilterRows: aggregates only deal-breaker answers across the full set', () => {
  const q1 = scaleQuestion({ slug: 'q1' });
  const q2 = singleChoiceQuestion({ slug: 'q2' });
  const answers = new Map<string, QuestionAnswerState>([
    ['q1', answeredState(3, 3, 'slight')], // not a deal breaker
    ['q2', answeredState('has_kids_want_more', ['has_kids_want_more'], 'deal_breaker')],
  ]);
  const rows = deriveDealBreakerFilterRows([q1, q2], answers);
  assert.equal(rows.length, 1);
  assert.equal(rows[0]!.filterKey, 'qb:q2');
});

test('evaluateDealBreakers: candidate satisfying the deal breaker passes', () => {
  const q = singleChoiceQuestion({ slug: 'kids' });
  const viewer = new Map<string, QuestionAnswerState>([['kids', answeredState(null, ['has_kids_want_more'], 'deal_breaker')]]);
  const candidate = new Map<string, QuestionAnswerState>([['kids', answeredState('has_kids_want_more', null, 'important')]]);
  const result = evaluateDealBreakers([q], viewer, candidate);
  assert.equal(result.passes, true);
  assert.deepEqual(result.failedSlugs, []);
});

test('evaluateDealBreakers: candidate failing the deal breaker fails, and is named in failedSlugs', () => {
  const q = singleChoiceQuestion({ slug: 'kids' });
  const viewer = new Map<string, QuestionAnswerState>([['kids', answeredState(null, ['has_kids_want_more'], 'deal_breaker')]]);
  const candidate = new Map<string, QuestionAnswerState>([['kids', answeredState('still_deciding', null, 'important')]]);
  const result = evaluateDealBreakers([q], viewer, candidate);
  assert.equal(result.passes, false);
  assert.deepEqual(result.failedSlugs, ['kids']);
});

test('evaluateDealBreakers: prefer_not_to_say on the candidate side still fails the viewer\'s deal breaker, filters win', () => {
  const q = singleChoiceQuestion({ slug: 'kids' });
  const viewer = new Map<string, QuestionAnswerState>([['kids', answeredState(null, ['has_kids_want_more'], 'deal_breaker')]]);
  const candidate = new Map<string, QuestionAnswerState>([['kids', preferNotToSayState()]]);
  const result = evaluateDealBreakers([q], viewer, candidate);
  assert.equal(result.passes, false, 'a candidate who prefers not to say must still fail the deal breaker, not be treated as neutral');
  assert.deepEqual(result.failedSlugs, ['kids']);
});

test('evaluateDealBreakers: candidate who never answered the question fails closed too', () => {
  const q = singleChoiceQuestion({ slug: 'kids' });
  const viewer = new Map<string, QuestionAnswerState>([['kids', answeredState(null, ['has_kids_want_more'], 'deal_breaker')]]);
  const candidate = new Map<string, QuestionAnswerState>(); // no row at all
  const result = evaluateDealBreakers([q], viewer, candidate);
  assert.equal(result.passes, false);
});

test('evaluateDealBreakers: a viewer with no deal breakers always passes', () => {
  const q = singleChoiceQuestion({ slug: 'kids' });
  const viewer = new Map<string, QuestionAnswerState>([['kids', answeredState(null, ['has_kids_want_more'], 'slight')]]);
  const candidate = new Map<string, QuestionAnswerState>([['kids', preferNotToSayState()]]);
  const result = evaluateDealBreakers([q], viewer, candidate);
  assert.equal(result.passes, true);
});

// =====================================================================
// Tag intensity + avoidance
// =====================================================================

test('scoreTagIntensityMatch: identical intensities score 1, opposite ends score 0, closer scores higher', () => {
  assert.equal(scoreTagIntensityMatch('daily', 'daily'), 1);
  assert.equal(scoreTagIntensityMatch('rarely', 'daily'), 0);
  const close = scoreTagIntensityMatch('regularly', 'frequently');
  const far = scoreTagIntensityMatch('rarely', 'frequently');
  assert.ok(close > far);
});

test('passesAvoidTagFilter: excludes when the viewer avoids a tag the candidate holds', () => {
  const result = passesAvoidTagFilter(new Set(['t1']), new Set(['astrology']), new Set(['astrology', 't2']), new Set());
  assert.equal(result.passes, false);
  assert.deepEqual(result.violatingTagIds, ['astrology']);
});

test('passesAvoidTagFilter: excludes when the candidate avoids a tag the viewer holds (bidirectional)', () => {
  const result = passesAvoidTagFilter(new Set(['crossfit']), new Set(), new Set(['t2']), new Set(['crossfit']));
  assert.equal(result.passes, false);
  assert.deepEqual(result.violatingTagIds, ['crossfit']);
});

test('passesAvoidTagFilter: passes when neither avoids anything the other holds', () => {
  const result = passesAvoidTagFilter(new Set(['hiking']), new Set(['astrology']), new Set(['reading']), new Set(['crossfit']));
  assert.equal(result.passes, true);
  assert.deepEqual(result.violatingTagIds, []);
});
