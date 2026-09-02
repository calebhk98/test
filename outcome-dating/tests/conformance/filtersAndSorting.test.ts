/**
 * CC-1: "no candidate who fails either party's hard filters is EVER
 * returned by discovery, regardless of compatibility score." Per the task
 * brief this is one of the most important, least-covered cross-module
 * invariants: `filter.service.ts` decides eligibility, `compatibility.service.ts`
 * decides order, and `discovery.service.ts` is the only module positioned
 * to get their composition wrong. A per-module test can prove each piece
 * works in isolation without ever proving the WIRING keeps them in the
 * right order; this file proves the composition, using a candidate this
 * suite drives to genuine 1.0 compatibility (not just a stubbed number) so
 * "regardless of compatibility score" is the case actually exercised, per
 * the checklist's own oracle for C-9.1.2 ("candidate with compatibilityScore
 * = 1.0 ... is absent from discovery output").
 *
 * filter.service.ts, compatibility.service.ts, and discovery.service.ts are
 * all on the task's list of files other agents are concurrently changing;
 * if a case here regresses, check recent history on those three files
 * before assuming a new defect (see task instructions).
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { setupConformanceDb, teardownConformanceDb, makeCtx, userActor, adminActor, createUser, type TestDb } from './support.js';
import * as filterService from '../../src/services/filter.service.js';
import * as compatibilityService from '../../src/services/compatibility.service.js';
import * as discoveryService from '../../src/services/discovery.service.js';
import * as questionService from '../../src/services/question.service.js';
import { sortDiscoveryCandidates, type DiscoveryRankingInput } from '../../src/services/discovery.service.js';
import type { DiscoveryCandidate } from '../../src/domain/types.js';

let db: TestDb;

before(async () => {
  db = await setupConformanceDb('filters');
});

after(async () => {
  await teardownConformanceDb(db);
});

// =====================================================================
// C-9.2.1: table-driven property over `evaluateFilter`'s operators. Pure,
// no I/O, so this is a real exhaustive check of every operator semantics
// the built-in filter keys rely on, not just a happy-path example.
// =====================================================================

test('C-9.2.1: evaluateFilter operator table, a candidate on the wrong side is excluded, one on the right side is not', () => {
  const cases: Array<{ name: string; operator: 'eq' | 'neq' | 'gte' | 'lte' | 'gt' | 'lt' | 'in'; value: unknown; passingValue: unknown; failingValue: unknown }> = [
    { name: 'age_min (gte)', operator: 'gte', value: 25, passingValue: 25, failingValue: 24 },
    { name: 'age_max (lte)', operator: 'lte', value: 40, passingValue: 40, failingValue: 41 },
    { name: 'max_distance (lt)', operator: 'lt', value: 50, passingValue: 49, failingValue: 50 },
    { name: 'min_score (gt)', operator: 'gt', value: 3, passingValue: 4, failingValue: 3 },
    { name: 'gender_preference (in)', operator: 'in', value: ['woman', 'nonbinary'], passingValue: 'woman', failingValue: 'man' },
    { name: 'relationship_intention (eq)', operator: 'eq', value: 'long_term', passingValue: 'long_term', failingValue: 'short_term' },
    { name: 'excluded_religion (neq)', operator: 'neq', value: 'none', passingValue: 'buddhist', failingValue: 'none' },
  ];

  for (const c of cases) {
    assert.equal(
      filterService.evaluateFilter({ operator: c.operator, value: c.value }, c.passingValue),
      true,
      `${c.name}: a candidate on the RIGHT side of the filter must pass`,
    );
    assert.equal(
      filterService.evaluateFilter({ operator: c.operator, value: c.value }, c.failingValue),
      false,
      `${c.name}: a candidate on the WRONG side of the filter must be excluded`,
    );
  }
});

// =====================================================================
// Full-stack fixture: viewer + two candidates, all three genuinely tied
// on a perfect (1.0) compatibility score via real answered questions, one
// candidate fails the viewer's hard filter, the other doesn't.
// =====================================================================

async function createFullUser(opts: { age: number; gender?: string; relationshipIntention?: string }): Promise<string> {
  const userId = await createUser(db);
  await db.pool.query(
    `INSERT INTO profiles (user_id, display_name, city, latitude, longitude, location_fuzzed, age, gender, seeking, relationship_intention, profile_completeness)
     VALUES ($1, $2, 'Testville', 39.78, -89.65, true, $3, $4, 'any', $5, 80)`,
    [userId, `User-${userId.slice(0, 8)}`, opts.age, opts.gender ?? 'woman', opts.relationshipIntention ?? 'long_term'],
  );
  await db.pool.query(
    `INSERT INTO user_photos (user_id, image_url, position, is_primary, moderation_status) VALUES ($1, 'https://example.test/p.jpg', 0, true, 'approved')`,
    [userId],
  );
  return userId;
}

/** Creates `count` fresh scale questions (min=1,max=5) and answers them IDENTICALLY (self=3, preference=3, importance='important') for both users, which drives every shared question's per-question satisfaction to exactly 1.0 (self matches the counterpart's stated preference on both sides), and therefore the aggregate `computePairScore` to exactly 1.0 regardless of weighting, comfortably above `compatibility.min_shared_questions`'s default of 3. */
async function givePerfectCompatibility(userA: string, userB: string, count = 3): Promise<void> {
  const adminCtx = makeCtx(db, adminActor());
  for (let i = 0; i < count; i++) {
    const slug = `conf_filters_perfect_${Date.now()}_${i}_${Math.random().toString(36).slice(2, 8)}`;
    await questionService.adminCreateQuestionBankEntry(adminCtx, {
      slug,
      category: 'conformance',
      questionText: `Conformance fixture question ${i}`,
      typeDef: { type: 'scale', min: 1, max: 5, minLabel: 'low', maxLabel: 'high', midLabel: 'mid' },
      baseWeight: 1,
    });
    for (const userId of [userA, userB]) {
      const ctx = makeCtx(db, userActor(userId));
      await questionService.putMyQuestionAnswer(ctx, { slug, status: 'answered', selfValue: 3, preferenceValue: 3, importance: 'important' });
    }
  }
}

test('CC-1 / C-9.1.2 / C-16.1.1 / C-1.3 / C-1.17: a candidate at compatibilityScore 1.0 who fails a hard filter is absent from discovery, while an equally-perfect filter-passing candidate is shown', async () => {
  const viewerId = await createFullUser({ age: 30 });
  const passingCandidateId = await createFullUser({ age: 30 }); // clears age_min: 25
  const failingCandidateId = await createFullUser({ age: 18 }); // fails age_min: 25

  await givePerfectCompatibility(viewerId, passingCandidateId);
  await givePerfectCompatibility(viewerId, failingCandidateId);

  const viewerCtx = makeCtx(db, userActor(viewerId));
  await filterService.updateMyFilters(viewerCtx, [{ filterKey: 'age_min', operator: 'gte', value: 25, enabled: true }]);

  // Prove the "1.0" premise first, independently of discovery: this really
  // is a perfect-compatibility pair on both sides, not a fixture that
  // merely claims to be.
  const scorePassing = await compatibilityService.getScore(viewerCtx, viewerId, passingCandidateId);
  const scoreFailing = await compatibilityService.getScore(viewerCtx, viewerId, failingCandidateId);
  assert.equal(scorePassing, 1, 'sanity: the filter-passing fixture candidate really is a perfect compatibility match');
  assert.equal(scoreFailing, 1, 'sanity: the filter-FAILING fixture candidate is ALSO a perfect compatibility match, this is the whole point of CC-1');

  // The direct, pure gate: passesMutualFilters must say no for the failing
  // candidate regardless of the score computed above.
  assert.equal(await filterService.passesMutualFilters(viewerCtx, viewerId, failingCandidateId), false);
  assert.equal(await filterService.passesMutualFilters(viewerCtx, viewerId, passingCandidateId), true);

  // The end-to-end gate: discovery must reflect the same thing.
  const grid = await discoveryService.getDiscoveryGrid(viewerCtx, {});
  const ids = grid.items.map((c) => c.userId);
  assert.ok(ids.includes(passingCandidateId), 'the filter-passing, perfect-compatibility candidate must appear');
  assert.equal(
    ids.includes(failingCandidateId),
    false,
    'CC-1: a perfect-compatibility candidate who fails a hard filter must NEVER be returned by discovery, no matter the score',
  );
});

test('C-10.3.3: a filter-passing candidate with a TERRIBLE compatibility score is still shown (no compatibility floor hides them)', async () => {
  const viewerId = await createFullUser({ age: 30 });
  const badMatchId = await createFullUser({ age: 30 });

  // Answer identically-shaped questions with maximally OPPOSED self/preference
  // values (self=1 vs preference=5 both ways), driving satisfaction toward 0
  // rather than 1, without touching any hard filter.
  const adminCtx = makeCtx(db, adminActor());
  for (let i = 0; i < 3; i++) {
    const slug = `conf_filters_bad_${Date.now()}_${i}_${Math.random().toString(36).slice(2, 8)}`;
    await questionService.adminCreateQuestionBankEntry(adminCtx, {
      slug,
      category: 'conformance',
      questionText: `Conformance opposed fixture ${i}`,
      typeDef: { type: 'scale', min: 1, max: 5, minLabel: 'low', maxLabel: 'high', midLabel: 'mid' },
      baseWeight: 1,
    });
    await questionService.putMyQuestionAnswer(makeCtx(db, userActor(viewerId)), { slug, status: 'answered', selfValue: 1, preferenceValue: 5, importance: 'important' });
    await questionService.putMyQuestionAnswer(makeCtx(db, userActor(badMatchId)), { slug, status: 'answered', selfValue: 1, preferenceValue: 5, importance: 'important' });
  }

  const viewerCtx = makeCtx(db, userActor(viewerId));
  const score = await compatibilityService.getScore(viewerCtx, viewerId, badMatchId);
  assert.ok(score < 0.5, `sanity: this fixture must be a genuinely bad match, got ${score}`);

  const grid = await discoveryService.getDiscoveryGrid(viewerCtx, {});
  assert.ok(
    grid.items.map((c) => c.userId).includes(badMatchId),
    'a filter-passing candidate must never be hidden purely for having a low compatibility score (spec §10.3, no threshold hiding)',
  );
});

// =====================================================================
// C-10.3.4: sorting is the ONLY effect of compatibility score on
// visibility. Shuffling scores across an otherwise-fixed candidate set
// must change ORDER but never the SET. Pure, so no DB fixture needed,
// exercises `sortDiscoveryCandidates` directly per its own doc contract.
// =====================================================================

function candidate(overrides: Partial<DiscoveryCandidate> & { userId: string }): DiscoveryCandidate {
  return {
    displayName: overrides.userId,
    age: 30,
    approximateDistanceKm: 5,
    primaryPhotoUrl: null,
    sharedInterestTag: null,
    compatibilityScore: 0.5,
    trustLevel: 'standard',
    profileCompleteness: 80,
    ...overrides,
  };
}
function ranked(c: DiscoveryCandidate): DiscoveryRankingInput {
  return { candidate: c, trustScore: 60, lastActiveAt: new Date('2026-01-01T00:00:00Z'), responseRate: 0.5 };
}

test('C-10.3.4: shuffling compatibilityScore across a fixed, filter-passing candidate set changes order but never the returned set', () => {
  const ids = ['a', 'b', 'c', 'd', 'e'];
  const scoreAssignments = [
    [0.9, 0.1, 0.5, 0.3, 0.7],
    [0.1, 0.9, 0.3, 0.7, 0.5],
    [0.5, 0.5, 0.5, 0.5, 0.5],
  ];
  for (const scores of scoreAssignments) {
    const inputs = ids.map((id, i) => ranked(candidate({ userId: id, compatibilityScore: scores[i]! })));
    const sorted = sortDiscoveryCandidates(inputs);
    assert.deepEqual(new Set(sorted.map((c) => c.userId)), new Set(ids), 'the SET of returned candidates must be identical regardless of score assignment');
  }
});
