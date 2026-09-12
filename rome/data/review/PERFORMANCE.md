# PERFORMANCE.md - where a simulated year actually goes

The reported symptom: `python3 rome/sim/simulator.py run --civ rome_100ad
--strategy rome/sim/strategies/planned_rome.json --mc 3 --horizon 700` takes
between thirty minutes and two hours - 2,100 simulated years, roughly one to
three seconds of wall clock per year, for a model whose state is a few
thousand booleans and a few dozen floats. This is measured before any code
was touched, what it turned out to be, and what four small, independent
fixes bought, each verified deterministic and against the regression suite.

**Do not trust guesses about this codebase, including previous ones.** The
instructions that produced this document note that several confident wrong
diagnoses had already been offered today. What is below is a profile, not a
theory: `cProfile` over `Sim.run()`, single seed, single trial, 300
simulated years (100 AD -> 400 AD), `rome_100ad` on the `planned_rome`
strategy. That is the same shape of work the slow command does, at a
tenth of the length, and it is fast enough to iterate on directly - the
whole point of the ground rule against running `--mc` sweeps as a
measuring stick.

## The baseline profile (before any change)

```
71,471,967 function calls in 34.435 seconds   (300 simulated years, one seed)
```

By self time (`tottime` - time inside the function itself, not in what it calls):

| ncalls | self time | function |
|---:|---:|---|
| 1,546,809 | 7.142s | `economy.py:_goods_category_state` |
| 34,117,767 | 2.933s | `dict.get` |
| 28,423 | 2.399s | `economy.py:revenue` |
| 604,367 | 1.789s | `sorted` (builtin) |
| 25,819 | 1.330s | `economy.py:capability_factor` |
| 1,546,809 | 1.215s | `economy.py:_goods_category_ratios` |
| 300 | 1.151s | `core.py:step` |
| 1,420,076 | 1.103s | `economy.py:venture_ramp` |
| 21 | 0.830s | `core.py:1102` (`[k for k in self.order if k not in set(earners)]`) |

By cumulative time (`cumtime` - this function plus everything it calls):

| ncalls | cumtime | function |
|---:|---:|---|
| 28,423 | 21.861s | `revenue()` |
| 9,314 | 15.883s | `living_cost()` |
| 1,420,076 | 15.635s | `goods_market_factor(k)` |
| 4,615 | 11.745s | `credit_limit()` |
| 1,546,809 | 13.710s | `_goods_category_ratios(cat)` |
| 1,546,809 | 11.040s | `_goods_category_state(cat)` |

**The per-call counts are the number to read, not the cumulative times** -
a previous pass on this code found `revenue()` calling one helper 61
million times in a run, and the pattern here is the same shape: a handful
of top-level "what is my financial state" queries (`revenue`,
`living_cost`, `credit_limit`), each one fanning out into a million-plus
calls to a function that recomputes something from scratch that had
already been computed a moment earlier, or that cannot have changed since
the year began.

## What was actually being recomputed

### 1. `revenue()` called twice by its own caller, for no reason

`living_cost()` (economy.py) called `self.revenue()` once to compute
`tax`, and again eighteen lines later to compute `room` - with nothing in
between that mutates any state `revenue()` reads. `self.wage_bill()` had
the identical pattern. `revenue()` is not cheap (see below), so
`living_cost()` alone was responsible for roughly two of every three calls
to it (9,314 calls to `living_cost()` x 2 = 18,628 of `revenue()`'s 28,423
total calls). Every other caller of `living_cost()` - `net = (self.revenue()
- self.upkeep() - self.living_cost() - ...)`, all over core.py, labour.py,
projects.py, society.py - was therefore paying for revenue() three times
to get one number.

### 2. `_goods_category_state()`: `sorted(self.operating)`, scanned and
   filtered, on every single call

`goods_market_factor(k)` - called once per operating venture inside
`revenue()`'s main loop - asks `_goods_category_ratios(cat)` for its
node's category, which calls `_goods_category_state(cat)`. That function
did:

```python
for m in sorted(self.operating):
    if self.nodes[m].get("cat") != cat:
        continue
    ...
```

`self.operating` is the set of every concern the player currently runs, and
this sorted the whole thing and threw away every member that did not match
`cat`, on every call. Worse: for every venture in a *non-essential*
category, `goods_market_factor` also calls `income_factor()` ->
`essential_price_ratio()` -> the *same* `_goods_category_state()`, again,
for the essential category (`processing`). So the call volume is roughly
(operating ventures) x (operating ventures x categories touched) - the
quadratic-in-portfolio-size shape that made later, more-built-up years of
a run cost far more than early ones, and that a 700-year run (far more
built up by the end than a 300-year one) would hit far harder than this
profile shows. `cat` is fixed on a node at tree-load time and never
changes at runtime; nothing here needed re-deriving every call, let alone
every call for every operating venture.

### 3. `set(earners)` rebuilt from scratch, once per node, in `self.order`

In `step()`'s auto-start-work branch (core.py, ~line 1097), when money is
tight relative to fixed costs:

```python
candidates = earners + [k for k in self.order if k not in set(earners)]
```

`self.order` carries the strategy's full working order - 2,833 nodes for
`planned_rome`. Because `set(earners)` is written inline inside the
comprehension's condition, Python rebuilds it from scratch on every one of
those 2,833 iterations: an O(|order| x |earners|) rebuild of a set whose
contents never change during the walk, where one set built once would
cover the whole thing in O(|order|). This branch is rare early in a run
(21 calls in this 300-year profile) and far more common whenever revenue
stays tight for a long stretch - exactly the condition a 700-year run
spends more of its time in.

### 4. `material_price_factor()`: the whole tick's demand dict, scanned
   per material, per node

```python
for (ek, tag), need in sorted(self._cached_demand_by_tag().items()):
    if ek != emp_key or need <= 0:
        continue
    ...
```

`_cached_demand_by_tag()` is already a proper per-tick cache (see its own
comment in economy.py, and `resource_throttle()`'s). But
`material_price_factor(emp_key)` re-sorted and re-scanned that whole dict
and threw away everything not matching `emp_key`, on every call -
`project_cost()` calls it once per material a candidate node buys, once
per candidate node, every year.

### What did *not* need fixing

`_done_seq` (economy.py's existing `_done_changed()` convention) and the
per-tick material-demand caches (`_material_demand_cache`,
`_demand_by_tag_cache`) were already doing the right thing before this
pass, and the fixes below reuse those exact conventions rather than
inventing a second caching scheme. `labour.py`'s `auto_commission_for_blocked`
memoizes `market_supply`/`trade_available` per call with a local dict
already (`_ms_memo`, `_ta_memo`), correctly hoisted outside the
2,800-iteration loop - also not touched.

## The fixes, in the order they were made, and what each measured

All four fixes are in economy.py or core.py, each its own commit, each
re-profiled, re-run against the regression suite
(`rome/sim/test_regressions.py`, 860 checks), and checked for determinism
(same seed, separate processes, and under different `PYTHONHASHSEED`
values, output diffed byte-for-byte) before being called done.

| # | Fix | ncalls before -> after (300yr profile) | Cumulative profiled time (300yr) |
|---|---|---|---|
| 1 | `living_cost()`: call `revenue()`/`wage_bill()` once, reuse | `revenue()` 28,423 -> 19,109 | 34.4s -> ~27s |
| 2 | `_goods_category_state()`: static per-category node index instead of `sorted(operating)` per call | `_goods_category_state` 1,546,809 -> 1,039,683 calls, self time 7.142s -> 1.587s | ~27s -> 21.5s |
| 3 | `core.py`: hoist `set(earners)` out of the per-node comprehension | the 0.811s/21-call line no longer appears in the top 35 by self time | 21.5s -> 21.2s (this branch is rare at horizon 300; see below) |
| 4 | `material_price_factor()`: group per-tick demand by `emp_key` once, cached the same way `_cached_demand_by_tag()` already is | `material_price_factor` no longer re-sorts the full demand dict per call | 21.2s -> ~20.0s |

Total for the 300-year single-seed profile: **34.4s -> ~20.0s under the
profiler**, function calls **71.5M -> 39.1M**. The profiler itself adds
substantial overhead (instrumenting every call), so the un-profiled wall
clock moved by more in relative terms:

```
python3 rome/sim/simulator.py run --civ rome_100ad \
  --strategy rome/sim/strategies/planned_rome.json --mc 1 --horizon 300 --seed 1

before:  12.134s
after:    6.563s     (1.85x)
output: byte-for-byte identical
```

**The clearest evidence is on the actual reported shape of the problem**
- single seed, `--horizon 700`, no `--mc` (per the ground rule against
running MC sweeps as a measuring stick):

```
before (baseline, un-optimized): did not finish inside a 600s (10 minute)
                                  timeout - killed, still running
after (all four commits applied): 3m26s (206s), completed, reached
                                  point_contact_transistor as first blocked node
```

That the baseline did not even finish a *single* 700-year seed within ten
minutes, while the reported symptom is 3 seeds in thirty minutes to two
hours, is consistent with fix #2 and #4's quadratic-shaped costs: a
700-year run has a far larger `operating` set and far more material
pressure late in its life than a 300-year one, so the per-call cost those
two fixes removed was growing with it, not staying flat. This is also why
fix #3's measured effect looks small at horizon 300 (21 calls) - the
branch it fixes fires when revenue is tight relative to fixed costs, which
is rare early in a short run and the norm in a long, materially-constrained
one.

## Determinism

Per fix, and cumulatively: the same seed, run in separate processes, and
under `PYTHONHASHSEED=1`, `999`, `555`, `777` (arbitrary distinct values),
produced byte-for-byte identical stdout, both against each other and
against the un-optimized baseline's own output for the same seed. No cache
added here changes the iteration order of anything that feeds a float sum:
`_goods_category_state`'s new per-category index and `material_price_
factor`'s new per-key grouping are both consumed only by `max()` (order-
independent), and the `_goods_by_cat`/`_demand_by_emp_key` caches are
built from `self.nodes.items()` / an already-existing dict, both of which
iterate in insertion order regardless of `PYTHONHASHSEED`.

## What is left on the table, and why it was not done here

The dominant remaining cost by self time is still inside `revenue()`'s own
loop (`goods_market_factor`, `venture_ramp`, `_goods_category_ratios`) and
`capability_factor()`, both of which walk `done_in_order()` - every
completed node - on every call, filtering for what is or is not currently
`operating`/`granted`. `capability_factor()` in particular sums over the
full done list every one of its ~17,000 calls in this profile, and its
result changes only when `self.done` or `self.operating` changes, not
every call. Making that properly incremental (an accumulator maintained
alongside `self.done`/`self.operating`, rather than a full walk) would
plausibly be the next-largest win, but `self.operating` is mutated directly
(`.add`/`.discard`) from nine call sites across core.py, projects.py,
economy.py and society.py - four files, all being edited by other agents
concurrently right now. Wiring in a correct invalidation signal that
does not go stale means touching all nine, and getting that wrong
silently changes results rather than just slows them down. That is an
architectural change - a real accumulator with a real invalidation
contract, not a one-line cache - and it is recommended, but not attempted
in this pass, in favour of leaving four small, independent, easily-rebased
commits behind instead of one large one that conflicts with everybody.
