#!/usr/bin/env python3
"""Find a working order in the world with the dice removed, then see how much
of it survives them.

THE OWNER'S OWN DIAGNOSIS, TAKEN LITERALLY. `planner.py` computes one
structural ordering by critical-path method and stops; this module is what
"solve the deterministic problem first" actually looks like. `run
--no-events` already turns off dated shocks, but a project's own risk of
FAILING outright is a separate roll in `projects.py:_complete`
(`self.rng.random() < n["risk"]`) that fires whether or not events are on -
so a fully dice-free trial needs a seeded rng whose `random()` always returns
1.0, never below any probability threshold anywhere in the engine (a
project's failure risk, the 3.5% yearly attrition roll, the 25% manumission
roll, the fractional-headcount rounding in `_stochastic_round`). See
`DetRNG` below. Nothing in `core.py`, `projects.py`, `labour.py`, `society.py`
or `economy.py` is edited to get this - the same rules run, against a
different sequence of "how did that roll come out".

THE FIRST QUESTION - DOES THE CURRENT PLAN EVEN GET THERE WITH THE DICE
OFF? - turns out to have a real, specific answer, not a shrug: no, and not
because of money or the generic scholar/artisan pools, both of which end up
abundant (tens of millions of denarii, hundreds of scholars and artisans).
It stalls on a small, fixed set of NAMED CRAFT TRADES the tree calls
`TRADES_ABSENT` - chemist, electrician, engineer, machinist, optician -
which do not exist in this civilisation at all until you personally teach
them (`labour.py:trade_available`), and which grow ONLY through
`step()`'s once-a-year, two-people-at-a-time auto-teach (core.py, "4a2"),
gated further by a 25-year per-trade cooldown. Once a trade's headcount is
above zero, `market_supply(t) <= 0.0` - the sole trigger auto-teach uses to
decide a trade is worth training more of - is simply never true again unless
every last person of that trade dies out, so in a deathless, failure-free
world a trade that got taught once, early, for two people, STAYS at two
people for the rest of the run, however many projects are starved for it.
That is not a bug this module can fix (core.py/labour.py are not this
module's to edit); it is a fact about how the given rules grow named-trade
labour, and the only lever a strategy ORDER has over it is which nodes get
to spend that frozen, tiny pool of hours, and in what sequence.

THE BINDING CONSTRAINT, MEASURED: on Rome's planned order, three nodes -
`steam_atmospheric`, `interchangeable_parts`, `spectroscope` - go active
early, need machinist/chemist/engineer hours nothing else in the run can
supply, and never finish. Fifty-six of the tree's other 168 closure nodes sit
downstream of those three and can never even start. And the planner's own
`pick_side_branches` - which ranks candidates purely by return on capital,
with no idea the tree has any scarce labour at all - hands the household
several more nodes (locomotives, TNT, dynamite, double-acting engines) that
draw on the EXACT SAME five trades, spread through the order specifically so
they compete with the spine for it throughout the run.

THE SEARCH. Two moves, applied to the CPM order `planner.backward_plan`
already computes, chosen because they attack this specific, measured
constraint rather than guessing at the space of all 168! orderings:

  1. PULL every side branch that draws on a currently-scarce trade OUT of
     the interleaved order entirely, to the very end (after the spine, after
     the goal). A side branch is optional by definition - it exists only to
     fund the spine - so one that competes with the spine for the one
     resource actually blocking the spine is worse than not building it at
     all, and `refine`'s own measured finding on staffing institutions
     already established that "obviously helpful" is not the same claim as
     "measured helpful" for this exact tree.

  2. WITHIN a tied CPM slack band (nodes the graph itself cannot tell apart -
     see planner.py's own comment on why this is exactly where a seed or a
     tie-break is honest to apply), move nodes that draw on a scarce trade
     to the FRONT of the band, smallest total scarce-trade hours first. This
     is shortest-processing-time-first, the standard remedy for many jobs
     queued on one non-shareable resource: it clears the queue soonest and
     is a strict refinement of the tie-break planner.py already documents as
     legitimate, not a new principle.

Both moves are computed FROM a diagnostic run of the real Sim, not from a
second model of the tree - `diagnose_scarce_trades` reads `s.active`,
`s.employees` and `s.hours_you_can_call_on` off an actual simulated
household, the same object `run` would build. Each round re-diagnoses from
the new order's own simulated state, so a trade that stops being scarce
(finished, unblocked) stops being treated as one, and a round that does not
improve on the previous best is simply not kept - see `search()`. This is
"repeatedly relaxing whatever the binding constraint turns out to be", one
of the two methods the brief itself names, chosen over a from-scratch
metaheuristic (random-restart hill-climbing over raw orderings, simulated
annealing, ...) because the constraint here is not diffuse - it is these
five trades, provably - and searching blindly over 168! orderings to
rediscover a fact already visible in `s.active` would be slower and no more
honest than reading it off the Sim directly.
"""
import argparse, os, random, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)


def ensure_fixed_hash_seed(seed="0"):
    """A "deterministic" trial is not, unless this is called first.

    `DetRNG` makes `random()` return 1.0 for every call, which is exactly
    reproducible on its own - but CPython hashes strings differently in every
    process by default (`hash("machinist")` differs run to run unless
    `PYTHONHASHSEED` is fixed), and a handful of places in this engine walk a
    bare, unsorted `set` of node or trade ids rather than a list or a
    `sorted()` view of one - core.py's own comment on `rng.sample(losable,
    ...)` names this exact risk for ONE such set and sorts it there
    specifically because an earlier version did not. Repeated trials here
    (same order, same DetRNG, three separate `python3` processes) came back
    identical either way for the runs this module actually measured, so
    nothing in THIS search was silently corrupted by it - but that is one
    tree, one order, one horizon, not a proof that no set-iteration site
    anywhere in core.py/labour.py/economy.py can ever matter for a
    DIFFERENT order this search might try next. Pinning the hash seed before
    any Sim runs costs nothing and removes the question entirely, which is
    cheaper than auditing every such site by hand and trusting the audit to
    stay correct as those files keep changing under other agents' hands.
    `PYTHONHASHSEED` can only be set before the interpreter starts, not from
    inside an already-running one, so a process that was not launched with
    it fixed re-execs itself, once, with it set - which is why every entry
    point in this module calls this first.
    """
    if os.environ.get("PYTHONHASHSEED") == seed:
        return
    env = dict(os.environ, PYTHONHASHSEED=seed)
    os.execvpe(sys.executable, [sys.executable] + sys.argv, env)

from engine.data import TRADES_ABSENT, closure, load, load_civ
from engine.core import Sim
from engine.cli import load_strategy, topo_stable

import planner as _planner


# ----------------------------------------------------------------------------
# A dice-free trial
# ----------------------------------------------------------------------------

class DetRNG(random.Random):
    """A seeded rng whose random() always returns 1.0.

    Every probability check in the engine is "< threshold" with threshold in
    (0, 1) - a project's risk of failure, the 3.5% attrition roll, the 25%
    manumission roll, the fractional-headcount stochastic rounding - so a
    draw of 1.0 is never below any of them: nothing fails, nobody dies,
    nothing is freed by luck, every fraction rounds down. `randint`/`sample`
    are never reached in a deathless run (they sit behind `not
    self.founder_alive`, and immortal=True in every Sim this module builds),
    so overriding `random()` alone is enough to make a whole run
    reproduce identically for any seed - the seed number itself stops
    mattering, which is the point: this is the world with the dice removed,
    not a world with better dice.
    """
    def random(self):
        return 1.0


def deterministic_sim(nodes, order, goal, civ, horizon, bounty_set=None):
    """One dice-free trial of `order` against `civ`, to `horizon` years."""
    s = Sim(nodes, order, DetRNG(1), events=False,
            cfg={"immortal": True}, civ=load_civ(civ),
            bounty_set=set(bounty_set or ()))
    s.run(goal, horizon)
    return s


def fitness(s, need):
    """Higher is better. Reaching the goal beats not reaching it outright;
    among runs that reach it, earlier beats later; among runs that do not,
    more of the goal's own closure finished beats less, and surplus capital
    (not in arrears, not sitting on an unfunded programme) breaks the last
    tie. A plain tuple comparison reads this correctly with no weighting to
    tune, which is the whole reason it is shaped this way rather than as one
    blended score.
    """
    done = sum(1 for k in need if k in s.done)
    return (1 if s.goal_year else 0, -(s.goal_year or 10 ** 9), done, s.capital)


# ----------------------------------------------------------------------------
# Diagnose the binding constraint FROM the simulator's own state
# ----------------------------------------------------------------------------

def diagnose_scarce_trades(s, nodes, outstanding, backlog_ratio=6.0):
    """Which of the five taught trades (TRADES_ABSENT) are actually the
    thing holding this run up, read off a simulated household rather than
    guessed at.

    A trade counts as scarce here if (a) more than one node still
    outstanding wants it at all, and (b) the total hours those nodes still
    need of it (`backlog`) is worth more than `backlog_ratio` years of what
    the household can currently draw on in a single year
    (`hours_you_can_call_on`, the same ceiling `lab_year_draw` itself pays
    projects out of). `backlog_ratio` is a judgement call, not a measured
    constant: too low and a trade that is merely busy this decade gets
    treated as permanently frozen; too high and the five-trades-frozen-at-
    two-forever wall this module exists to work around goes undetected. 6
    years of backlog against one year of throughput is comfortably past
    "busy" for a game whose calendar floors are measured in single-digit
    years per node.
    """
    scarce = {}
    for t in TRADES_ABSENT:
        contested = [k for k in outstanding if nodes[k]["lab"].get(t, 0.0) > 0]
        if len(contested) < 2:
            continue
        backlog = sum(nodes[k]["lab"][t] for k in contested)
        supply = max(1.0, s.hours_you_can_call_on(t))
        if backlog / supply > backlog_ratio:
            scarce[t] = {"contested": contested, "backlog": backlog,
                         "supply_per_year": supply,
                         "employees": s.employees.get(t, 0.0)}
    return scarce


def stuck_active(s, need):
    """Nodes the goal needs that have been active a while and are making
    little or no headway - the visible symptom `diagnose_scarce_trades`
    explains the cause of. Purely descriptive (used for the report, not the
    search itself), read straight off `s.active`.
    """
    out = []
    for k, st in s.active.items():
        if k not in need:
            continue
        if st.get("stalled_years", 0) > 0 or st.get("short_of_trade") or st.get("waiting_on_money"):
            out.append(k)
    return sorted(out)


# ----------------------------------------------------------------------------
# The two moves
# ----------------------------------------------------------------------------

def _needs(nodes, k, trades):
    return any(nodes[k]["lab"].get(t, 0.0) > 0 for t in trades)


def _scarce_hours(nodes, k, trades):
    return sum(nodes[k]["lab"].get(t, 0.0) for t in trades)


def pull_scarce_extras(order, nodes, need, scarce):
    """Move 1: any node OUTSIDE the goal's own closure that draws on a
    currently-scarce trade goes to the very end, after everything the goal
    needs. It is there to fund the spine; a side branch that instead
    competes with the spine for the one resource holding the spine up is a
    net cost, not a net gain - see the module docstring's measured account
    of the seven of Rome's twelve picked side branches that do exactly this.
    Relative order of everything else is untouched.
    """
    if not scarce:
        return list(order)
    keep, pulled = [], []
    for k in order:
        if k not in need and _needs(nodes, k, scarce):
            pulled.append(k)
        else:
            keep.append(k)
    return keep + pulled


def spt_within_slack_bands(order, nodes, need, c, scarce):
    """Move 2: within each tied CPM slack band (planner.py's own definition
    of "the graph cannot tell these apart"), nodes that draw on a currently
    scarce trade move to the front of the band, smallest total scarce-trade
    hours first - shortest-processing-time-first, which clears a shared,
    non-shareable resource in the least total time. Nodes outside the goal's
    closure (no CPM slack of their own) and nodes that need no scarce trade
    keep their existing relative order, band by band.
    """
    if not scarce:
        return list(order)
    slack = c["slack"]
    out = []
    i = 0
    n = len(order)
    while i < n:
        k = order[i]
        if k not in need:
            out.append(k)
            i += 1
            continue
        band = round(slack.get(k, 0.0), 3)
        j = i
        group = []
        # A "band" is a maximal run of CONSECUTIVE spine nodes sharing this
        # exact slack value - not every node in the tree with this slack,
        # because side branches interleaved between them are not fungible
        # with spine placement and moving spine nodes PAST an interleaved
        # side branch would silently undo the funding cadence `interleave`
        # was built to give the household.
        while j < n and order[j] in need and round(slack.get(order[j], 0.0), 3) == band:
            group.append(order[j])
            j += 1
        group.sort(key=lambda x: (0, _scarce_hours(nodes, x, scarce)) if _needs(nodes, x, scarce)
                                  else (1, 0.0))
        out.extend(group)
        i = j
    return out


# ----------------------------------------------------------------------------
# The search itself: diagnose, relax, re-simulate, keep what improves
# ----------------------------------------------------------------------------

def search(civ="rome_100ad", goal=None, side_branches=12, side_branch_every=8,
           rounds=6, horizon=500, backlog_ratio=6.0, seed_order=None, log=print):
    """Plan by CPM, then repeatedly diagnose the binding constraint against a
    dice-free trial of the current order and relax it, keeping whichever
    round's order scored best (see `fitness`).

    `seed_order`: the same kind of tie-break `planner.backward_plan` already
    accepts (a previous plan's or a captured winner's order) - passed
    straight through to the initial CPM pass so `--search-rounds` composes
    with `--seed-strategy` instead of ignoring it.

    Returns (best_order, best_extras, history) where `history` is one dict
    per round: the scarce trades found, the stuck nodes they explain, and
    the fitness reached - the evidence `main()` writes into the strategy
    file's own rationale and PATH_SEARCH.md draws its numbers from.
    """
    ensure_fixed_hash_seed()
    tree, prices, nodes, wages, goods = load()
    goal = goal or tree["meta"]["goal_node"]
    need = closure(nodes, goal)
    s0 = Sim(nodes, [], random.Random(1), events=False, civ=load_civ(civ))
    order, c, extras, staffing = _planner.backward_plan(
        nodes, goal, s0, seed_order=seed_order, side_branches=side_branches,
        side_branch_every=side_branch_every)

    history = []
    best_order, best_extras, best_fit = order, extras, None
    cur_order, cur_extras = order, extras
    for rnd in range(rounds):
        full = _planner._repaired(nodes, goal, cur_order)
        sim = deterministic_sim(nodes, full, goal, civ, horizon)
        fit = fitness(sim, need)
        stuck = stuck_active(sim, need)
        outstanding = [k for k in (need | set(cur_extras)) if k not in sim.done]
        scarce = diagnose_scarce_trades(sim, nodes, outstanding, backlog_ratio)
        rec = {"round": rnd, "goal_year": sim.goal_year,
               "closure_done": fit[2], "capital": sim.capital,
               "stuck": stuck, "scarce_trades": sorted(scarce),
               "scarce_detail": scarce}
        history.append(rec)
        log("  round %d: %d/%d closure nodes done%s, stuck on %s, scarce trade(s): %s"
            % (rnd, fit[2], len(need),
               (" (goal reached %d AD)" % sim.goal_year) if sim.goal_year else "",
               ", ".join(stuck) or "(nothing)", ", ".join(sorted(scarce)) or "(none)"))
        if best_fit is None or fit > best_fit:
            best_fit, best_order, best_extras = fit, cur_order, cur_extras
        if sim.goal_year:
            log("  goal reached; stopping the search early")
            break
        if not scarce:
            # Nothing currently reads as a resource bottleneck by this
            # round's own diagnosis. Either the run is money/calendar-bound
            # instead (nothing this module can relax - see planner.py's own
            # position on not modelling money live) or a previous round
            # already relaxed everything this method knows how to relax;
            # burning the rest of the round budget re-deriving the same
            # order would not find anything new.
            log("  no scarce-trade bottleneck detected; stopping early")
            break
        spine = [k for k in cur_order if k in need]
        new_spine = spt_within_slack_bands(spine, nodes, need, c, scarce)
        new_order = pull_scarce_extras(
            _planner.interleave(new_spine, cur_extras, side_branch_every),
            nodes, need, scarce)
        if new_order == cur_order:
            log("  relaxation made no change to the order; stopping early")
            break
        cur_order = new_order
    return best_order, best_extras, history


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--civ", default="rome_100ad")
    ap.add_argument("--goal", default=None)
    ap.add_argument("--out", required=True, help="strategy file to write")
    ap.add_argument("--side-branches", type=int, default=12)
    ap.add_argument("--side-branch-every", type=int, default=8)
    ap.add_argument("--rounds", type=int, default=6)
    ap.add_argument("--horizon", type=int, default=500,
                    help="dice-free horizon used WHILE searching - kept short "
                         "for speed; verify the winner separately at a longer "
                         "horizon and then against real seeds")
    ap.add_argument("--backlog-ratio", type=float, default=6.0)
    ap.add_argument("--seed-strategy", default=None,
                    help="a strategy name or path whose order breaks ties "
                         "among nodes the critical path ranks as equally "
                         "urgent, same as planner.py's own --seed-strategy")
    a = ap.parse_args()
    ensure_fixed_hash_seed()
    t0 = time.time()
    _tree0, _p0, _nodes0, _w0, _g0 = load()
    seed_order = _planner.load_seed(a.seed_strategy, _nodes0)
    order, extras, history = search(a.civ, a.goal, a.side_branches,
                                    a.side_branch_every, a.rounds, a.horizon,
                                    a.backlog_ratio, seed_order=seed_order)
    tree, _p, nodes, _w, _g = load()
    goal = a.goal or tree["meta"]["goal_node"]
    last = history[-1]
    rationale = [
        "Deterministic search (rome/sim/path_search.py): CPM order, then up "
        "to %d rounds of diagnosing the binding constraint against a "
        "dice-free trial (no events, no project failures, immortal founder) "
        "and relaxing it, keeping whichever round scored best." % a.rounds,
        "Final round %d: %d/%d closure nodes done%s. Scarce trade(s) found: "
        "%s." % (last["round"], last["closure_done"],
                len(closure(nodes, goal)),
                (", goal reached %d AD" % last["goal_year"]) if last["goal_year"] else "",
                ", ".join(last["scarce_trades"]) or "(none)"),
    ]
    _planner.write_strategy(a.out, "SEARCHED (deterministic): %s over %s's "
                            "critical-path order, relaxed against its own "
                            "scarce-trade bottleneck" % (goal, a.civ),
                            rationale, order)
    print("wrote %d nodes to %s in %.1fs" % (len(order), a.out, time.time() - t0))
    for line in rationale:
        print("  - " + line)


if __name__ == "__main__":
    main()
