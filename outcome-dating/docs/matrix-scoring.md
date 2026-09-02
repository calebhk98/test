# Matrix scoring: verdict

**Update (block-refresh adoption): ADOPTED for `refreshAllScores`, the
nightly bulk materialization job, and ONLY there.** The section "Where it
would actually win" below, written when this file first rejected the
technique, predicted exactly this: restructure `refreshAllScores` to batch
each geographic cluster into one `computeCompatibilityBlock` call instead
of scoring pairs one at a time, and the all-pairs numbers already measured
would apply. That restructure has now been done (see
`compatibility.service.ts`'s BLOCK REFRESH doc for exactly how pairs are
grouped into blocks, and why grouping cannot drop a candidate at a group
boundary) and measured directly, see "Block-refresh adoption: measured
before/after" below for the numbers. Candidate SELECTION (the geo-bounded
LATERAL query, the activity window, the per-user neighbor cap, the
no-location fallback) is completely unchanged; only how the already-selected
pairs get scored changed.

**Original recommendation, still true for every OTHER call shape in this
codebase: reject.** `getScore`, `getScoresForCandidates`, and
`refreshScoresForUser` all still score one user against a candidate list,
never a block, and stay on the unchanged scalar path
(`computePairScore`/`aggregateQuestionScores`). The idea is sound and the
alternative implementation is correct and fast in the shape it wants, but
these call sites present the shape it does *not* want, and in that shape
the measured win is modest at best and negative at the largest bank size
tested (see "The numbers" below, unchanged from the original measurement).
See `src/domain/questions/matrixScoring.ts` for the implementation; it now
has exactly one production caller (`refreshAllScores`, via
`computeCompatibilityBlock`), reached only through the batched shape.

## The numbers

Two call shapes were benchmarked (`tests/perf/matrixScoring.perf.test.ts`,
median of 15 runs after warmup for one-vs-many, single measurement for
all-pairs, realistic type mix matching `src/seed.ts`: 40% scale, 12%
frequency, 40% single_choice, 8% multi_choice):

**One-vs-many** (the real shape: `getScoresForCandidates` and
`refreshScoresForUser` both score one user against a candidate list, never
a block):

| shape | bank | density | candidates | naive | matrix | speedup |
|---|---|---|---|---|---|---|
| materialized refresh (K=50) | 65 | dense | 50 | 0.73ms | 0.67ms | 1.08x |
| materialized refresh (K=50) | 65 | sparse | 50 | 0.47ms | 0.32ms | 1.48x |
| materialized refresh (K=50) | 600 | dense | 50 | 6.6ms | 5.7ms | 1.17x |
| max discovery pool (K=500) | 65 | dense | 500 | 7.2ms | 5.0ms | 1.43x |
| max discovery pool (K=500) | 65 | sparse | 500 | 5.6ms | 3.0ms | 1.85x |
| max discovery pool (K=500) | 600 | dense | 500 | 74.5ms | 102.1ms | **0.73x (matrix loses)** |
| max discovery pool (K=500) | 600 | sparse | 500 | 52.3ms | 31.3ms | 1.67x |

**All-pairs block** (250 x 250 = 62,500 cells at once; not how anything in
this codebase actually calls scoring today, see below):

| bank | density | naive | matrix | speedup |
|---|---|---|---|---|
| 65 | dense | 814ms | 105ms | 7.7x |
| 65 | sparse | 575ms | 14ms | 41.1x |
| 600 | dense | 8678ms | 452ms | 19.2x |
| 600 | sparse | 6231ms | 93ms | 67.1x |

The crossover is about batch shape, not density: the technique wins
convincingly only when *both* sides of the block are large enough to
amortize its per-question setup cost. Every real call site keeps one side
at exactly 1.

## Why the real shape doesn't benefit much

The matrix path's per-question cost has two parts: an O(rows + cols) setup
pass (resolve each user's answer to an index, once) and an O(rows x cols)
gather. With rows=1, the O(rows x cols) part is only ever cols-sized, the
same order as the naive path, so there's no batching win to amortize the
setup against, just a constant-factor win from replacing `Map` lookups,
status branches and handler dispatch with flat typed-array reads. That win
is real (1.1x-1.9x across most one-vs-many scenarios) but modest, and at
bank=600 with 500 candidates it goes negative: 600 questions x roughly 8
typed-array allocations each for the setup pass outweighs the savings when
the column side is the only side doing real work. The all-pairs numbers
show what the same code does when given the shape it's actually built for.

## Where it would actually win (now done, see below)

`refreshAllScores` computes many pairs, but used to do so geo-bounded
neighbor-by-neighbor per user (per its own file-level SCALE FIX doc), not
as a shared block. Restructuring it to batch each geographic cluster into
one `computeCompatibilityBlock` call instead of scoring pairs one at a
time was flagged here as the change that would make the all-pairs numbers
above real; that restructure has since been done, see the next section for
the measured result.

## Block-refresh adoption: the clustering scheme and how it handles edges

**Candidate selection is completely unchanged.** `loadGeoBoundedPairs` (the
geo-bounded LATERAL query), the platform-wide no-location fallback query,
the activity window, and the per-user neighbor cap are byte-for-byte the
same SQL and the same logic as before this adoption. WHICH pairs get
materialized was already correct and already tested; this build did not
touch it, and does not re-derive it in JS.

**What changed is purely how the resulting pairs get grouped for scoring.**
`refreshAllScores` now buckets rows into a plain lat/lon grid (cell size =
the fixed refresh box's own width/height, `2 * latDeltaDeg` by
`2 * lonDeltaDeg`, a size already computed for the run, not a new magic
number) keyed by each row user's OWN coordinates, then scores every row in
a bucket against the UNION of those rows' own already-selected candidates
in one `computeCompatibilityBlock` call (row-chunked, bounded by
`BLOCK_MAX_CELLS`, if a bucket's row-count times its column-count would
otherwise allocate an unreasonable amount of memory in one call, e.g. one
very dense metro's entire located population landing in a single bucket).
Unlocated users need no bucketing at all: they all share the exact same
fixed fallback candidate list already, so they are naturally one single,
maximally batchable group.

**Why a bucket boundary cannot drop a candidate.** A bucket is a
scheduling decision, "which rows to score in the same call," never a
membership test for candidacy. A row's column set for its block call is
always built from `directedCandidates.get(rowId)`, i.e. exactly the
candidates the UNCHANGED SQL already selected for that specific user, not
from "whoever else happens to land in the same bucket." Concretely: user A
is bucketed by A's own coordinates into bucket X; A's candidate B (found by
the SQL, and possibly bucketed into a completely different bucket Y, or
geographically far enough from A's bucket center to look unrelated in grid
terms) is still always in A's column list, because that list was built
directly from A's own directed candidates, never from bucket membership.
There is therefore no grid edge, anywhere in this code, for a real
candidate to fall on the wrong side of. Two tests in
`tests/unit/compatibility.test.ts` exercise this directly:
- **"a candidate pair whose two users land in different scoring buckets
  (grid-cell boundary) is still materialized"**: two users placed a few
  kilometres apart, deliberately straddling a computed grid line (verified
  by asserting their bucket indices actually differ before the real
  assertions run), both directions still materialized, score bit-identical
  to `computePairScore` run directly.
- **"the materialized geo-bounded pair set matches an independent
  brute-force reference exactly"**: a larger, multi-cluster fixture
  (several clusters, a straggler near one cluster's edge, a genuine
  outlier, unlocated users), compared cell-by-cell against a from-scratch,
  O(n^2), no-SQL, no-grid brute-force re-implementation of "the `cap`
  nearest others within the fixed box" using only the pure, exported
  `boundingBoxForRadius`. Exact set equality, in both directions (nothing
  missing, nothing extra), for the geo-bounded portion; the unlocated
  portion is checked for "no omissions" against the real platform-wide
  fallback query rather than exact equality, since that query legitimately
  draws from every active user in this file's shared, accumulating test
  database, not just this one fixture (documented at the test itself).

## Block-refresh adoption: equivalence proof

Materialized rows must still be bit-for-bit identical to
`scoreQuestionContribution`/`computePairScore` computed directly, for every
question type, every importance level, and every non-answer state, exactly
the bar the original (unadopted) matrix path was already held to. Nothing
about that proof changed: `computeCompatibilityBlock` itself is untouched
by this adoption (see "Equivalence and floating point" below, still
"every comparison bit-for-bit identical, max difference exactly zero"), and
`refreshAllScores`'s own "semantics-preservation" DB test
(`tests/unit/compatibility.test.ts`) asserts every materialized row for a
worked, hand-checked fixture matches `computePairScore` invoked directly
on the same inputs, unchanged in substance by this build (still passing,
now backed by the block-scoring path instead of a per-pair loop). The two
new tests described in the clustering section above add the same
bit-for-bit standard specifically at grid boundaries, where a batching bug
would most plausibly hide.

## Block-refresh adoption: pair-set comparison (old shape vs new shape)

Compared directly, on the same fixture, in
`tests/unit/compatibility.test.ts`'s "the materialized geo-bounded pair set
matches an independent brute-force reference exactly" test: the set of
pairs the current, block-scoring `refreshAllScores` materializes for a
multi-cluster fixture, against a from-scratch brute-force computation of
what the geo-bounded selection SHOULD produce. **Exact set equality, both
directions asserted separately (nothing the reference expects is missing;
nothing extra was materialized that the reference does not expect).**
Separately, `tests/perf/compatRefresh.perf.test.ts`'s before/after test
(see the next section) asserts the OLD (pre-adoption, scalar, one
`computePairScore` call per pair) and NEW (block-matrix) shapes, run back
to back against the identical seeded 20,000-user population with identical
candidate-selection SQL, produce the exact same row COUNT, both as
`result.updated` and as the final `compatibility_scores` table size, this
is the same claim at full production scale rather than a small hand-built
fixture. No pair was found present in one shape and absent from the other
in either check; there is no discrepancy to justify.

## Block-refresh adoption: measured before/after

Measured with `tests/perf/compatRefresh.perf.test.ts`, reusing the
existing `seedDiscoveryPerfData` perf-seed helper (unchanged), the same
20,000-user, six-city seed `discovery.perf.test.ts` and the original
bounded-refresh build already used, New York seeded as roughly half the
population (`pickCity`'s documented weighting) specifically so a genuinely
dense cluster is exercised, not just six evenly sized cities.

## Bank coverage

Counted directly from `src/seed.ts`'s 65 real questions: scale 26,
frequency 8, single_choice 26, multi_choice 5. `scale` and `frequency` use
a shared kernel (`K[a][b] = 1 - |a-b|/(n-1)`, exactly `typeHandlers.ts`'s
formula); `single_choice` needs no kernel at all, a preference is already a
0/1 acceptability vector, so satisfaction is a direct index into it. That's
**60/65 (92%)** of the real bank on the fast path. `multi_choice`'s
Jaccard satisfaction depends on set union, not a fixed-size lookup, and
falls back to the exact, unmodified `scoreQuestionContribution` per pair,
same as any version-drift case (a stale anchor/option key from an edited
question) that the fast path detects and refuses to guess on.

## Equivalence and floating point

`tests/unit/matrixScoring.test.ts`: hand-checked cases for every type,
every importance level (including `irrelevant`/`deal_breaker` exclusion),
all three non-answer states, the too-few-shared-questions default, both
version-drift fallbacks, and a randomized sweep (4000 pair comparisons over
a 40-question mixed bank, 30 users, varying `minSharedQuestions` and
`noDataDefaultScore`), plus a separate batched-block sweep checked cell by
cell against the scalar path.

**Every comparison, across all of it, was bit-for-bit identical: max
`|scalar - matrix| = 0`.** This isn't luck: the kernel/indicator gather
performs the exact same floating point operations (same subtraction, same
division, same operand order) that `typeHandlers.ts` does, just precomputed
once instead of recomputed per pair, and the accumulation loop visits
questions in the same order doing the same `+=` sequence either way. No
epsilon tolerance was needed anywhere.
