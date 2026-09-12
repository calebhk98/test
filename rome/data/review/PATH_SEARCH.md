# Solving the dice-free problem first, then seeing what survives the dice

Goal node, read from the tree at measurement time (`tree["meta"]["goal_node"]`,
the same line `planner.py` and `path_search.py` both read it from, never
hand-typed): **`junction_transistor`**. Its prerequisite closure, also read
from the tree (`engine/data.py:closure()`, which follows `pre` and every
single-option `req_any` group): **168 nodes** (`simulator.py validate`
confirms this independently: "required for goal: 168" - measured twice,
before and after the merge below, both times 168, not 158 or 185, both of
which were briefly written down elsewhere today and are wrong).

Measured against `f764e5e`. Partway through this work the shared branch
picked up a large, unrelated performance pass (a 300-year single-seed run
went from 12.8s to 7.8s; a 700-year single seed that previously would not
finish inside a ten-minute timeout now takes about three and a half
minutes) plus real balance changes to `core.py`/`economy.py`/`society.py`/
`protocol.py` from four other agents. Merged cleanly (no conflicts outside
`cli.py`, which `git` resolved on its own). Determinism through the merge
was checked directly, not assumed: the dice-free Rome trial's state at
year 1000 - capital `29,520,851.012074385`, `employees` down to the
fraction (`chemist: 10.45, engineer: 10.45, machinist: 2.0, optician: 2.0,
electrician: 4.0`) - is byte-for-byte identical before and after the merge.
The speed is not, and it is the reason section 1's answer below is
**correct** rather than merely faster: every horizon this report quotes
past year 1000 was too expensive to reach before the merge, and the
pre-merge version of this same investigation (reaching only as far as year
1000, because that was already tens of minutes of compute) concluded "no"
to the question section 1 actually answers "yes" to. That draft conclusion
never left this file's own working history - it is recorded here, once,
as the clearest illustration this report has of why "solve the
deterministic problem first" has to mean "run it to an horizon long enough
to find out," not "run it as long as seemed affordable an hour ago."

## Method

"Solve the deterministic problem first," per the brief: turn off events
(`--no-events` already exists) AND turn off the one other source of
randomness that is not gated by `events` - a project's own risk of failing
outright, which is a bare `self.rng.random() < n["risk"]` in
`projects.py:_complete` that fires whether or not `events=True`. A seeded
rng whose `random()` always returns 1.0 is never below any probability
threshold anywhere in the engine - not that roll, not the 3.5% yearly
attrition check, not the 25% manumission check, not the fractional-headcount
stochastic rounding - so it reproduces a single trial with money, staff,
calendar and the tree's own dependency structure as the only constraints.
This lives in the new module `rome/sim/path_search.py` as `DetRNG`, built
and run with an `immortal=True` founder and `events=False`, never by
editing `core.py`/`projects.py`/`labour.py`/`society.py`/`economy.py`.

A footnote worth recording rather than burying: CPython hashes strings
differently by default in every process (`hash("machinist")` differs run to
run), and a few places in this engine walk a bare, unsorted `set` of node or
trade ids - `core.py`'s own comment on `rng.sample(losable, ...)` names this
exact risk for one such set and sorts it there specifically because an
earlier version did not. Every repeated trial here (same order, same
`DetRNG`, separate `python3` processes, before AND after the performance
merge) came back bit-identical regardless - so nothing here was silently
corrupted by it - but `path_search.py` pins `PYTHONHASHSEED` before any
`Sim` runs anyway (`ensure_fixed_hash_seed`, a one-time self-re-exec),
because removing the question costs nothing and is cheaper than
re-auditing every set-iteration site in files that are not this module's to
edit and that keep changing under other agents' hands.

## 1. The deterministic answer

**Yes.** With the dice removed entirely, the current critical-path plan -
`backward_plan()`'s own output, byte-identical to what `simulator.py plan`
produces with no flags, which is in turn byte-identical to the committed
`strategies/planned_rome.json` and `planned_han.json` - reaches
`junction_transistor` on BOTH civilisations, given a long enough horizon.
Money and the generic scholar/artisan pools are never the reason it takes
as long as it does (both end up far beyond abundant on every trial below);
a slow-to-resolve cash-flow/named-trade bottleneck is, and it resolves on
its own, eventually, without any help from ordering.

**Han China** (`han_china_100ad`): reaches the goal at **year 555 AD - 455
years after arrival**, against a 142.2-year critical-path floor.

| year | closure nodes done | capital (den) | named-trade employees |
|---|---:|---:|---|
| 250 | 43/168 | -2,388 | (none taught yet) |
| 300 | 82/168 | +640,039 | all five at 4.0 |
| 350-400 | 85/168 | +3.5m to +5.1m | all five still at 4.0 (plateaued) |
| 450 | 109/168 | +3,867,285 | all five at ~4.29 |
| 500 | 145/168 | +225,269,370 | all five at 10.45 |
| **555** | **168/168 - GOAL REACHED** | **+1,210,824,657** | all five at 10.45 |

**Rome** (`rome_100ad`): reaches the goal at **year 1121 AD - 1,021 years
after arrival**, nearly twice Han's span.

| year | closure nodes done | capital (den) | named-trade employees |
|---|---:|---:|---|
| 250-700 | 30/168 | -4,100 to -5,839 | (none taught yet) |
| 750-950 | 36-41/168 | -6,583 to -17,198 | 0 to 2 each, as they get taught and occasionally lost |
| 1000 | 109/168 | +29,520,851 | chemist/engineer 10.45, machinist/optician 2.0, electrician 4.0 |
| 1050 | 140/168 | +753,790,341 | all five at 10.45 |
| 1100 | 162/168 | +1,516,565,621 | all five at 10.45 |
| **1121** | **168/168 - GOAL REACHED** | **+1,818,924,430** | all five at 10.45 |

Both tables show the same shape, at different scales: a long plateau (Han
~250 years, Rome ~950 years) in which capital sits flat or mildly negative
and none of the five `TRADES_ABSENT` trades (chemist, electrician,
engineer, machinist, optician) have any headcount at all, followed by a
single expensive cascade year in which staffing, revenue and the closure
count all jump together (Han: 85→109→145 in 100 years; Rome: 41→109→140 in
150 years), after which every trade converges to the same 10.45 headcount
and the rest of the closure clears in well under a century.

**What the plateau actually is.** `data/review/ROME_SOLVENCY.md` traced
this independently, under real seeded trials, to `staff_capacity()`'s
affordability term: it needs an annual operating surplus on the order of
$20,000-25,000 before it grants a single whole hire, and neither
civilisation's own trading margin clears that on its own for a long time -
Han because it takes roughly 150-200 years to compound its technological
head start into that much surplus, Rome because it starts with none of
that head start and needs closer to 900. Nothing about strategy ORDER
shortens this: it is a property of household income relative to a fixed
affordability formula, exactly the kind of live money/staff modelling
`planner.py`'s own docstring declines to duplicate and leaves to the
engine. Once the surplus clears the threshold, the five named trades -
which grow ONLY through `step()`'s once-a-year, two-people-at-a-time
auto-teach, normally frozen almost the instant any of them gets nonzero
headcount (the sole re-trigger is `market_supply(t) <= 0.0`, never true
again short of a trade dying out completely) - get pushed through several
cycles of being staffed, lost (to unpaid wages in a tight year, not to
attrition, which `DetRNG` disables), and re-taught in quick succession
once the household can actually afford to keep rehiring them, which is
what the post-cascade convergence to 10.45 each actually is. None of this
needed search to find - it is what simply running the unmodified plan out
far enough shows.

## 2. The search

`rome/sim/path_search.py` automates "repeatedly relax the binding
constraint" - one of the two methods the brief names - rather than a blind
metaheuristic over the space of 168! orderings, because at any one moment
the constraint here is not diffuse: it is measurably one or a few named
trades, read directly off a live `Sim`'s own `active`/`employees`/
`hours_you_can_call_on` state, not modelled a second time. Each round:

1. Runs a dice-free trial of the current order.
2. `diagnose_scarce_trades`: flags a `TRADES_ABSENT` trade as the binding
   constraint if two or more still-outstanding nodes want it AND their
   combined outstanding hours are worth more than `--backlog-ratio` (6, by
   default) years of what the household can draw on in a single year.
3. Two moves, applied only to nodes that touch a flagged trade:
   - **Pull every side branch that draws on it out of the interleaved
     order, to the very end** - a side branch exists only to fund the
     spine, so one competing with the spine for the one thing actually
     blocking the spine is a net cost. (Measured aside: 7 of Rome's 12
     CPM-picked side branches - locomotives, TNT, dynamite, a double-acting
     engine - draw on these exact five trades, spread through the order
     specifically so they compete with the spine for them the whole run.)
   - **Within a tied CPM slack band, move nodes that draw on it to the
     front, smallest total hours of it first** - shortest-processing-time-
     first, the standard remedy for many jobs queued on one non-shareable
     resource, applied only where `planner.py` already treats the graph as
     unable to tell two nodes apart.
4. Re-simulates, keeps whichever round scored best (see `fitness` - reaching
   the goal beats not reaching it, earlier beats later, more of the closure
   done beats less), and stops itself once a round makes no further change,
   reaches the goal, or flags nothing scarce.

**Honestly measured, across three different diagnosis points, the search
never improves on the plain CPM order - it also never makes it worse, and
for Han it correctly recognises success and stops immediately:**

- Diagnosing at horizon 500 on Rome (cheap, but before the plateau has
  broken): flags four trades as "scarce" (nothing taught yet, so any
  backlog clears the ratio trivially), pulls one side branch
  (`tr_articulated_locomotive`), converges after one round. Final order is
  NOT the plain CPM order (one side branch moved) but scores identically
  at every horizon tested, including the goal itself: **year 1121, both
  ways.**
- Diagnosing at year 1000 on Rome directly, against the real bottleneck
  (`machinist`: 101,559 hours of backlog across 25 still-outstanding
  nodes, against a realised supply of 6,360 hours/year - sixteen years of
  uncontested work just to clear that one year's backlog): correctly and
  precisely identifies the true constraint, pulls the same one side
  branch, and still reaches the goal at **year 1121, both ways** -
  identical capital to the cent (`1,818,924,430`).
- Diagnosing at horizon 900 on Han: the dice-free trial has already
  reached the goal (555 < 900) by the time the first round finishes, so
  the search sees nothing outstanding, flags no scarce trade, and stops
  itself on round 0 rather than hunting for a problem that no longer
  exists. Goal year: **555, both ways.**

**Why the relaxation never matters, even when it correctly identifies the
right trade:** `interchangeable_parts` alone, on its own, already demands
more machinist-hours in a single year than the entire named-trade pool can
supply - so pulling ONE competing side branch off that trade never changes
how fast `interchangeable_parts` itself clears, because it was never
sharing the bottleneck with anything else in the order that mattered within
the years that count. This is not a disappointing footnote to explain away:
**the named-trade freeze, while real and precisely measurable, turns out to
be a multi-century DELAY, not a permanent wall, and the delay's length is
set by the affordability/auto-teach cycle described in section 1, which no
reordering of a strategy file touches.** A search that tries to relax it
anyway, measures three separate times that it cannot, and reports that
honestly is doing its job correctly - the same discipline `planner.py`'s
own comments already apply to the staffing-institution question
("measured, putting them in this order made the run worse, not better"),
extended to a constraint the graph-only CPM pass has no way to see in the
first place. A genuinely different search - one that tries moves this
module does not (loosening `--side-branches` itself, or a different
concurrency cap on how many closure nodes may be simultaneously active) -
might still find something these two moves do not; that is future work, not
a claim made here.

`--search-rounds` is wired into `simulator.py plan` (see `engine/cli.py`
`cmd_plan`) precisely so this is re-runnable rather than a one-off claim:
`plan --search-rounds N --search-horizon H --out FILE` diagnoses and
relaxes for real, on demand, against whatever the tree says today.

## 3. Against real seeds

Since the search never improves on the plain CPM order, "the best
deterministic path" for this measurement IS that order -
`planned_rome.json`/`planned_han.json`, unmodified, exactly as
`simulator.py plan` (no `--search-rounds`) already produces them.
`python3 rome/sim/simulator.py run --civ <civ> --strategy <file> --mc 3 --horizon 700 --seed 1`
(real events on, real project-failure risk, a mortal founder by default -
nothing dice-free about either run; each took a few minutes on this
machine after the performance merge, tens of minutes before it):

**Rome: 0 of 3.**

```
runs                : 3
reached transistor  : 0  (0%)
years spent short of a raw material (median run):
   iron         15 run-years
   coal         11 run-years
   copper       5 run-years
   saltpetre    3 run-years
coppice woodland owned: median 384 hectares
final reputation    : median 99/100
failure modes       :
   ran out of horizon                                           3 (100%)
first blocked node  :
   point_contact_transistor                                     1
   atomic_theory                                                1
   cap_heat_3000                                                1
```

**Han China: 2 of 3 (67%).**

```
runs                : 3
reached transistor  : 2  (67%)
year reached        : best 663 | p25 663 | median 703 | p75 703 | worst 703
elapsed from 100 AD  : median 603 years
years spent short of a raw material (median run):
   saltpetre    217 run-years
   iron         45 run-years
   copper       21 run-years
   coal         18 run-years
   gold         3 run-years
coppice woodland owned: median 1182 hectares
final reputation    : median 100/100
failure modes       :
   ran out of horizon                                           1 (33%)
first blocked node  :
   point_contact_transistor                                     1
```

**How much of the deterministic answer survives the dice, stated plainly:
for Han, most of it; for Rome, none of it - and section 1 already explains
exactly why, with no need to guess.** `--horizon 700` with `start_year 100`
means the test actually cuts off at year 800 AD, not 700. Han's dice-free
trial reaches the goal at year 555, with 245 years of slack against that
800 AD cutoff; two of three real-seeded trials land inside that slack (663
and 703) and the third runs out of the full 800 years without reaching it
at all - real shocks and a mortal founder cost that one trial more than
245 years of margin, which is a real, visible cost of the dice, just not
an unsurvivable one here. Rome's dice-free trial does not reach the goal
until year 1121 - **321 years past the 800 AD cutoff this measurement
actually uses** - so 0 of 3 real-seeded trials reaching it is not evidence
that ordering or luck failed Rome; a perfectly luck-free trial of the
identical order already needed 1,021 years from arrival, and no amount of
good fortune inside an 800-year window was ever going to make up a
321-year gap. The honest conclusion is not "Rome's plan doesn't work" -
section 1 shows that it does - but "Rome's plan needs a longer horizon
than this project has been testing it at," which is a claim about the
TEST, not about the tree, the civilisation, or the planner's ordering.

## A warning, taken seriously: is `planned_rome.json` even current?

The brief's own warning - every saved strategy in this repository was stale
for weeks, targeting a retired goal node, without anyone noticing - has a
concrete, checkable instance in this project's own history. Commit
`758744b` recorded `planned_rome.json` reaching the goal **10 of 10**
trials at a 700-year horizon with events on. That commit predates
`fa31ff1` ("data: both transistors, with the 1951 one as the target"), the
commit that retired the 1947 point-contact device as the goal and made
`junction_transistor` (1951) the target - i.e. that 10/10 almost certainly
measured the OLD goal, not the one this report (and the current tree) is
actually asking about. It is not reused here for that reason, however
tempting a ready-made "10/10" would be. Every number in this report was
measured fresh, this session, against `tree["meta"]["goal_node"]` read
live off the current tree - not against anything remembered from an
earlier session, a stale strategy file, or an old commit's own report. The
nearer-miss version of the same lesson is this report's own section 1: a
number that was true of "as far as this session could afford to compute
an hour ago" stopped being the right answer the moment a performance fix
made computing further affordable, and the fix was to re-run, not to
footnote the old number and move on.
