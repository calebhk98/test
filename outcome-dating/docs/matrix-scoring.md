# Matrix scoring: verdict

**Recommendation: reject, for the codebase as it stands today.** Keep
`compatibility.service.ts` untouched (per the task's own instruction: only
add the seam if adopting). The idea is sound and the alternative
implementation is correct and fast in the shape it wants, but every real
call site in this codebase presents the shape it does *not* want, and in
that shape the measured win is modest at best and negative at the largest
bank size tested. See `src/domain/questions/matrixScoring.ts` for the
implementation, kept as a tested, unused, alternative path in case a future
restructure changes which shape is real (see "Where it would actually win"
below).

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

## Where it would actually win

`refreshAllScores` computes many pairs, but geo-bounded neighbor-by-neighbor
per user (per its own file-level SCALE FIX doc), not as a shared block. If
it were restructured to batch each geographic cluster into one
`computeCompatibilityBlock` call instead of per-user neighbor queries, the
all-pairs numbers above say that would be a real, large win. That
restructure is a separate, larger architectural change (how pairs are
selected, not just how they're scored) and is out of scope here; it is
flagged for whoever next touches `refreshAllScores`, not undertaken.

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
