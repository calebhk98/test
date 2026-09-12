# Solving the dice-free problem first, then seeing what survives the dice

Goal node, read from the tree at measurement time (`tree["meta"]["goal_node"]`,
the same line `planner.py` and `path_search.py` both read it from, never
hand-typed): **`junction_transistor`**. Its prerequisite closure, also read
from the tree (`engine/data.py:closure()`, which follows `pre` and every
single-option `req_any` group): **168 nodes** (`simulator.py validate`
confirms this independently: "required for goal: 168").

Measured against `651e95b`. Everything below is run against the CURRENT
tree and the CURRENT `planner.py`, not against a remembered number from an
earlier session - see the closing section for a concrete case of why that
distinction matters here specifically.

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
and run with an `immortal=True` founder and `events=False`, never by editing
`core.py`/`projects.py`/`labour.py`/`society.py`/`economy.py`.

A footnote worth recording rather than burying: CPython hashes strings
differently by default in every process (`hash("machinist")` differs run to
run), and a few places in this engine walk a bare, unsorted `set` of node or
trade ids - `core.py`'s own comment on `rng.sample(losable, ...)` names this
exact risk for one such set and sorts it there specifically because an
earlier version did not. Repeated trials here (same order, same `DetRNG`,
three separate `python3` processes) came back bit-identical either way for
every run this search actually measured - so nothing here was silently
corrupted by it - but `path_search.py` pins `PYTHONHASHSEED` before any `Sim`
runs anyway (`ensure_fixed_hash_seed`, a one-time self-re-exec), because
removing the question costs nothing and is cheaper than re-auditing every
set-iteration site in files that are not this module's to edit and that keep
changing under other agents' hands.

## 1. The deterministic answer

**No - with the dice removed, the current critical-path plan does not reach
`junction_transistor`, on either civilisation, within the horizons this
search could afford to run.** That by itself is the headline, and it is a
clean answer to the brief's first question: the tree is not silently
unsolvable by money or scholars or artisans (both end up abundant on every
trial below), so the planner's job - ordering - is where to keep looking.

**Rome** (`rome_100ad`, CPM order with 12 side branches every 8 nodes - the
same parameters `planner.py plan`'s defaults use, and the committed
`strategies/planned_rome.json` is byte-identical to what a fresh,
unseeded run of that command produces today):

| year | closure nodes done | capital (den) | named-trade employees |
|---|---:|---:|---|
| 250 | 30/168 | -4,646 | (none taught yet) |
| 450-700 | 30/168 | -4,789 to -5,839 | (none taught yet) |
| 750 | 36/168 | -6,583 | (none taught yet) |
| 800-850 | 37-41/168 | -13,242 to -15,458 | (none taught yet) |
| 900 | 41/168 | -17,198 | engineer 2.0, chemist 2.0 |
| 950 | 41/168 | -10,023 | chemist 1.0 |
| **1000** | **109/168** | **+29,520,851** | chemist 10.45, engineer 10.45, machinist 2.0, optician 2.0, electrician 4.0 |

Two distinct things are visible in that table, and they are not the same
constraint:

- **Years ~150-950: a cash-flow plateau, not a knowledge or staffing
  wall.** Capital drifts in a band around -4,000 to -17,000 for the better
  part of eight centuries while the closure count barely moves (30 to 41 of
  168). This is the same mechanism `data/review/ROME_SOLVENCY.md` traced
  independently and in detail under real seeded trials: `staff_capacity()`'s
  affordability term needs an annual operating surplus on the order of
  $20,000-25,000 before it grants a single whole hire, and Rome's own
  surplus under this plan never gets there on its own - so scholars and
  artisans sit at 0 for centuries, the cheap ventures that would grow the
  surplus stay shut for want of craftsmen, and the loop closes on itself.
  Nothing about strategy ORDER breaks this loop; it is a property of the
  household's income relative to a fixed affordability formula, which is
  exactly the kind of live money/staff modelling `planner.py`'s own
  docstring declines to duplicate and leaves to the engine.
- **After year ~1000: a hard throughput ceiling on five named trades.**
  Once the plateau breaks (a single expensive cascade year, not a
  gradual climb - see below), 56 of the 59 closure nodes still missing at
  year 1000 trace back through their prerequisite chains to the other
  three, which go active early and never finish themselves:
  `steam_atmospheric`, `interchangeable_parts`, `spectroscope`. All three need hours of `chemist`, `electrician`,
  `engineer`, `machinist` or `optician` - the tree's `TRADES_ABSENT` set,
  trades this civilisation does not have at all until personally taught.
  Those five trades grow ONLY through `step()`'s once-a-year,
  two-people-at-a-time auto-teach, and in practice freeze almost
  immediately: the sole re-trigger condition is `market_supply(t) <= 0.0`,
  and once a trade has ANY headcount at all that is never true again short
  of the whole trade dying out - which a deathless, failure-free trial
  (by construction) never lets happen. Measured directly off a live `Sim`
  at year 1000: `machinist` backlog across 25 still-outstanding closure/side
  nodes is **101,559 hours** against a realised supply of **6,360
  hours/year** - 16 years of uninterrupted, uncontested work just to clear
  today's backlog, before a single one of the other 24 nodes gets a turn.
  Money is not the constraint here (capital is +$29.5 million); headcount
  in five specific trades is, and it is frozen by rules in `core.py`/
  `labour.py` this task does not get to edit.

**Han China** (`han_china_100ad`, same CPM parameters; `planned_han.json`
is likewise what a fresh unseeded plan produces): the same two-phase shape,
compressed by its historical technology head start (cast iron, paper,
water-powered bellows, etc. - see `ROME_SOLVENCY.md` section 3 for the
trace). The cash-flow plateau breaks by ~year 300 instead of ~year 1000:

| year | closure nodes done | capital (den) | named-trade employees |
|---|---:|---:|---|
| 250 | 43/168 | -2,388 | (none taught yet) |
| 300 | 82/168 | +640,039 | chemist/electrician/engineer/machinist/optician all 4.0 |
| 350-400 | 85/168 | +3.5m to +5.1m | all five still at 4.0 (plateaued again) |
| 450 | 109/168 | +3,867,285 | all five at ~4.29 |

Han reaches the exact same 109/168 ceiling Rome does, about 550 years
sooner, with a healthier (if still frozen) named-trade headcount - and
still has not reached the goal. The SAME five trades are the thing holding
both civilisations at 109/168; the tech head start changes how fast a
household gets rich enough to reach the wall, not whether the wall is
there.

## 2. The search

`rome/sim/path_search.py` automates "repeatedly relax the binding
constraint" - one of the two methods the brief names - rather than a blind
metaheuristic over the space of 168! orderings, because the constraint here
is not diffuse: it is measurably these five trades, read directly off a
live `Sim`'s own `active`/`employees`/`hours_you_can_call_on` state, not
modelled a second time. Each round:

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
     specifically to compete with the spine for them the whole run.)
   - **Within a tied CPM slack band, move nodes that draw on it to the
     front, smallest total hours of it first** - shortest-processing-time-
     first, the standard remedy for many jobs queued on one non-shareable
     resource, applied only where `planner.py` already treats the graph as
     unable to tell two nodes apart.
4. Re-simulates, keeps whichever round scored best, and stops itself once a
   round makes no further change (it always has, in one application) or
   flags nothing scarce.

**Honestly measured, the search does not change the outcome.** Two separate
experiments, both on Rome:

- Diagnosing at the search's own default horizon (500 - cheap, but before
  the cash-flow plateau has broken): flags all four trades trained so far as
  "scarce" almost trivially (nothing has been taught yet, so any backlog
  clears the ratio), pulls one side branch, and the relaxed order scores
  EXACTLY as well as the unmodified CPM order at every horizon tested up to
  year 1000 (109/168, capital $29,520,851.01 - identical to the cent, not
  merely similar).
- Diagnosing at year 1000 itself, against the REAL bottleneck
  (`machinist`, 101,559 hours of backlog, 25 contested nodes, the number
  quoted above): correctly and precisely identifies the true constraint,
  pulls the one side branch that touches it
  (`tr_articulated_locomotive`), and STILL scores identically:
  109/168, $29,520,851.01, `interchangeable_parts` still the only node
  stuck. Pulling the one competitor changed nothing because it was never
  the thing splitting `machinist`'s 6,360 hours/year in the first place -
  `interchangeable_parts` alone already exceeds that entire annual supply
  by itself, every year, whether or not anything else is also asking for
  it.

This is the honest finding, not a disappointing footnote to work around:
**the named-trade freeze is a throughput ceiling, not a scheduling
problem, and no reordering of a strategy file can relax a ceiling.** A
search that tries to relax it anyway and then reports "no change, measured
twice, for two different and independently-reasoned diagnoses" is doing
its job correctly - it is the same discipline `planner.py`'s own comments
already apply to the staffing-institution question ("measured, putting
them in this order made the run worse, not better") extended to a second
question the graph-only CPM pass has no way to see: not every wall a
household hits is a wall an ORDER can move.

`--search-rounds` is wired into `simulator.py plan` (see `engine/cli.py`
`cmd_plan`) precisely so this is re-runnable rather than a one-off claim:
`plan --search-rounds N --search-horizon H --out FILE` diagnoses and
relaxes for real, on demand, against whatever the tree says today.

## 3. Against real seeds

Since the search's own relaxation scored no better than the plain CPM order
(section 2), "the best deterministic path" for this measurement IS the
current CPM order - `planned_rome.json`/`planned_han.json`, unmodified,
exactly as `simulator.py plan` (no `--search-rounds`) already produces them.

`python3 rome/sim/simulator.py run --civ rome_100ad --strategy planned_rome --mc 3 --horizon 700 --seed 1`
(real events on, real project-failure risk, a mortal founder by default -
nothing dice-free about this run; it took about 35 minutes on this machine):

```
runs                : 3
reached transistor  : 0  (0%)
years spent short of a raw material (median run):
   saltpetre    277 run-years
   coal         21 run-years
   iron         18 run-years
   copper       5 run-years
coppice woodland owned: median 769 hectares
final reputation    : median 99/100
failure modes       :
   ran out of horizon                                           3 (100%)
first blocked node  :
   point_contact_transistor                                     1
   atomic_theory                                                1
   arc_furnace_ferroalloys                                      1
```

**0 of 3 reach the goal.** All three ran out of the 700-year horizon. None
of the three first-blocked nodes matches the deterministic trace's own
chain (`steam_atmospheric`/`interchangeable_parts`/`spectroscope`) - with
real randomness in the mix, different seeds get caught on different parts
of the same underlying wall (two of three are stopped even earlier than the
deterministic trial gets, on `point_contact_transistor` and
`atomic_theory`, both further back in the closure than anything the
dice-free trial itself struggled with) - consistent with the deterministic
finding rather than contradicting it: named-trade headcount is frozen
either way, and a mortal founder, real shocks and real risk rolls give the
household strictly less room to out-earn that freeze than the dice-free
trial had, not more.

**How much of the deterministic trial's "advantage" survives the dice: none
of it, honestly.** The dice-free trial got to 109/168 by year 1000 (beyond
this run's 700-year horizon) and still didn't reach the goal; the real-seed
trials, also given 700 years (less runway, plus every other thing that can
go wrong), also don't reach it, and score worse against the goal's own
near-term prerequisites specifically. There is no "reordering fixes it"
result to report here - only the honest one: the binding constraint is in
`core.py`/`labour.py`'s own rules for growing five named trades, a
structural pass over the tech tree (CPM, with or without this search's
relaxation) cannot buy around it, and real seeds do not get lucky enough to
route around it either, at this horizon.

`python3 rome/sim/simulator.py run --civ han_china_100ad --strategy planned_han --mc 3 --horizon 700 --seed 1`:

[FILLING IN - launched after the Rome run above; same command, same
horizon, same honesty - will be added the moment it completes rather than
estimated from the deterministic trace.]

## A warning, taken seriously: is `planned_rome.json` even current?

The brief's own warning - every saved strategy in this repository was stale
for weeks, targeting a retired goal node, without anyone noticing - has a
concrete, checkable instance in this project's own history. Commit
`758744b` (an ancestor of `651e95b`, the commit this report is measured
against) recorded `planned_rome.json` reaching the goal **10 of 10** trials
at a 700-year horizon with events on. That commit predates `fa31ff1`
("data: both transistors, with the 1951 one as the target"), the commit
that retired the 1947 point-contact device as the goal and made
`junction_transistor` (1951) the target - i.e. that 10/10 almost certainly
measured the OLD goal, not the one this report (and the current tree) is
actually asking about. It is not reused here for that reason, however
tempting a ready-made "10/10" would be. Every number in this report was
measured fresh, this session, against `tree["meta"]["goal_node"]` read live
off the current tree - not against anything remembered from an earlier
session, a stale strategy file, or an old commit's own report.
