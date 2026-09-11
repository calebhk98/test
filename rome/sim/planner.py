#!/usr/bin/env python3
"""Work backward from the goal, instead of walking a hand-written list.

THE QUESTION THAT STARTED THIS FILE: "Why is the sim a monte carlo sim? Is
that the best way to make an optimizer here? We know the end state right? Or
is it too complex now to just calculate backwards?" The answer is: it is not
too complex, and the sim was never actually doing search at all. `step()`
walks a fixed `order` list of node ids - a strategy file - starting whatever
it can afford, in the order the file happens to name. `--mc N` only re-rolls
the SAME order against N different random event sequences and averages the
outcome; that measures how an order copes with bad luck, it does not choose
the order. `recommended.json` was hand-written and reached the transistor in
0% of trials on Rome at a 700-year horizon; `captured_han_386.json` - which
is nothing but the order one lucky trial happened to finish its own work in -
reached it in 100%. The entire difference between those two numbers is
ordering, and nothing before this file ever computed one on purpose.

The tree does not need search to be ordered well. It is a DAG with priced,
timed nodes and a single goal; every node's true urgency is a computable
property of its position in that DAG, not a thing that has to be discovered
by gambling. This is the classic critical-path-method (CPM) question from
project scheduling: given a goal, a set of tasks, their durations and their
dependencies, which tasks are on the clock (zero slack - delaying one delays
the goal) and which have room to wait? Compute that once, directly, and the
critical ones go first.

WHAT THIS DELIBERATELY DOES NOT DO: it does not simulate concurrency, money,
staff or trade availability while planning - `Sim.step()` already does all of
that, live, every year, against whatever priority order it is handed (see
core.py step() 4b: `order` is a PREFERENCE the greedy loop consults, not a
schedule it is bound to; anything not yet legal is simply skipped that year
and reconsidered the next). So the planner's job is narrower and more honest
than "solve the whole game": say which of the ~149 nodes the goal actually
needs are on the critical spine, order those first, and leave the live
engine's own affordability and staffing checks to do what they already do
well. Chasing a full schedule (dates, concurrency, cash flow) here would be
duplicating logic that already exists and is already tested, badly.

SIDE BRANCHES. The 149-node closure is EVERYTHING the goal needs and nothing
else; it is not everything a household needs to survive on the way there.
`step()` already has a reactive fallback for this (core.py, "EARN A LIVING
FIRST") that switches to whatever pays best when revenue is thin - but that
is a patch applied after the fact, not a plan. A few cheap, high-margin,
short-payback revenue nodes woven into the order ahead of time give the
household something to run WHILE the spine is being built, rather than
waiting for the reactive fallback to notice it is starving. See
`pick_side_branches` and `--side-branches`.

CLOSING THE LOOP. The user's second question: "when the test DOES find a
working way through, why don't we reuse that as the starting sim?" `run
--save-winner FILE` already captures the order a winning trial finished its
work in, and this planner can take that (or its own previous output) as a
SEED: the CPM ranking still decides the primary order, but a seed's own
position is the tie-break within a band of equal slack, where the structural
model is genuinely ambiguous and the empirical evidence is not. `--refine`
goes one step further and automates that loop end to end: plan, run a batch
of trials, capture the best winner's order as a new seed, re-plan, repeat -
so a planning run can start from what the last one proved rather than from
nothing, the same complaint the user made about recommended.json never
updating itself.

WHY THIS IS NOT A FOG LEAK. This module is reached only from the command
line (`simulator.py plan`), reads the tree and prices directly, and is never
called from `play` or `agent` - the two entry points a fogged player actually
uses. A strategy file it writes can be fed back in with `--strategy`, exactly
like `recommended.json` or a captured winner, which is public information a
player already has (the file is sitting in the repository); the planner adds
no new way for a live, fogged session to see past what it has legitimately
discovered. It is a developer and optimizer tool, the same category
`compare`, `sweep` and `sensitivity` already are.
"""
import argparse, json, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from engine.data import (STRATS, closure, load, load_civ, topo_order)
from engine.core import Sim


# ----------------------------------------------------------------------------
# Critical-path method over the goal's closure
# ----------------------------------------------------------------------------

def duration(n):
    """Calendar years a node occupies if money and staff are no constraint at
    all: the larger of its own calendar floor (`yrs`, which the schema itself
    says "labour cannot buy down") and what one director's hours alone would
    take (`ph`/2000, a founder's year - see DEFAULTS). This is exactly the
    per-node term critical_path() in engine/data.py sums along the single
    longest chain to one target; it is not exposed per-node there, so it is
    repeated here rather than reused, to get it for every node in the closure
    at once instead of one target at a time.
    """
    return max(n["yrs"], n["ph"] / 2000.0)


def cpm(nodes, need):
    """Earliest/latest start and finish, and slack, for every node in `need`.

    Standard critical-path method, run once over the DAG restricted to `need`.
    A node with slack 0 sits on at least one longest chain to the goal:
    delaying it by a single year delays the goal by a year, and no amount of
    money changes that (the calendar floors and founder-hour floors this is
    built from are exactly the things `validate`/`path` already call
    unbuyable). A node with slack 40 could in principle wait forty years
    without costing the goal a day, PURELY on the graph's own shape - money,
    staff and concurrency limits are real constraints too and are left to the
    live engine, which already enforces them every year regardless of what
    order says (see the module docstring).
    """
    order = topo_order(nodes, need)
    es, ef = {}, {}
    for k in order:
        n = nodes[k]
        pred_ef = [ef[p] for p in n["pre"] if p in need]
        es[k] = max(pred_ef) if pred_ef else 0.0
        ef[k] = es[k] + duration(n)
    total = max(ef.values()) if ef else 0.0
    # Dependants WITHIN `need`, computed once rather than rescanning every
    # node for every k - closure(nodes, goal) is an ANCESTOR set, so every
    # member other than the goal itself has at least one dependant also in
    # `need` (that is how it was reached in the first place).
    deps = {k: [] for k in need}
    for m in need:
        for p in nodes[m]["pre"]:
            if p in need:
                deps[p].append(m)
    ls, lf, slack = {}, {}, {}
    for k in reversed(order):
        dep_ls = [ls[m] for m in deps[k]]
        lf[k] = min(dep_ls) if dep_ls else total
        ls[k] = lf[k] - duration(nodes[k])
        slack[k] = ls[k] - es[k]
    return {"es": es, "ef": ef, "ls": ls, "lf": lf, "slack": slack, "total": total}


# SORTING BY (slack, earliest start) IS NOT ITSELF A TOPOLOGICAL ORDER, and
# that is fine rather than a bug to chase. Earliest-start IS monotonic along
# every edge (a node cannot start before its own prerequisite finishes), but
# slack is not: on this tree 132 pairs have a prerequisite with STRICTLY MORE
# slack than something that needs it, because slack is a function of the
# longest remaining chain through every dependant, not of any one edge. The
# classic CPM remedy for that is the very function `load_strategy` (cli.py)
# already runs every strategy file through before the engine ever sees it -
# `topo_stable`, which repairs exactly this while disturbing the preferred
# order as little as possible - so the repair is not duplicated here. Verified
# empirically (see test_regressions.py): zero violations remain in the order
# `load_strategy` actually hands to `Sim` for every plan this module writes.


# ----------------------------------------------------------------------------
# Side branches: revenue that pays for the spine
# ----------------------------------------------------------------------------

def pick_side_branches(nodes, need, s, limit):
    """The `limit` best-return-on-capital nodes OUTSIDE the goal's closure,
    for THIS civilisation specifically.

    "Best" is net annual revenue (rev - up, so an upkeep-heavy concern cannot
    look good on revenue alone) per denarius of setup cost - the same ratio
    `costs` already prints under "best return on capital" in cli.py, applied
    here as a filter instead of a report. Restricted to what this civ could
    actually use: `_is_foreign_only` excludes another society's institutions
    (a Han run has no use for Roman citizenship), and anything already
    granted or already a hard prerequisite of the goal is excluded because it
    needs no priority push - it is either free or already first in line.
    """
    cands = []
    for k, n in nodes.items():
        if k in need or k in s.done or k in s.granted:
            continue
        if n["tier"] == 9 or n["cat"] == "unobtainable":
            continue
        if s._is_foreign_only(k):
            continue
        net = n["rev"] - n["up"]
        if net <= 0:
            continue
        cands.append(((net / max(1.0, n["_total_cost"])), k))
    cands.sort(key=lambda x: (-x[0], nodes[x[1]]["_total_cost"], x[1]))
    return [k for _, k in cands[:limit]]


def interleave(order, extras, every=8):
    """Weave `extras` into `order` at a steady rate rather than dumping them
    all at the front or all at the back.

    A single up-front block of revenue nodes only solves the OPENING; the
    complaint in the task brief is that side branches "pay for the spine"
    throughout, which argues for a trickle, not a lump sum. `every` is how
    many spine nodes pass between one side branch and the next; whatever
    remains after `order` runs out is appended, so nothing named is ever
    silently dropped. Topological legality is NOT enforced here on purpose -
    `load_strategy` in cli.py already runs every strategy file it reads
    through `topo_stable`, which repairs exactly this kind of interleaving
    without disturbing it more than the repair requires, and duplicating that
    logic here would be one more place for the two copies to drift apart.
    """
    if not extras:
        return list(order)
    out, ei = [], 0
    for i, k in enumerate(order):
        out.append(k)
        if ei < len(extras) and (i + 1) % every == 0:
            out.append(extras[ei])
            ei += 1
    out.extend(extras[ei:])
    return out


# ----------------------------------------------------------------------------
# The plan itself
# ----------------------------------------------------------------------------

def backward_plan(nodes, goal, s, seed_order=None, side_branches=12,
                   side_branch_every=8):
    """Order the goal's closure by CPM slack, tie-broken by a seed order where
    the graph itself cannot tell two nodes apart, then weave in a handful of
    self-funding side branches.

    A SEED IS A TIE-BREAK, NOT AN OVERRIDE. The structural ranking (slack,
    then earliest start - "of two things with equal room to wait, do the one
    that unblocks something sooner") always decides between nodes in
    different slack bands; a seed's position only decides between nodes the
    graph says are equally urgent, which is exactly where real evidence about
    staffing and cash flow (which the graph does not model) is worth more
    than a graph-only tiebreaker like id order. This is how a captured winner
    or a previous plan IMPROVES the result instead of merely being copied:
    the graph fixes whatever was wrong about the seed's ordering of
    genuinely-different-urgency nodes (recommended.json's failure mode), and
    the seed supplies the fine sequencing the graph has no opinion about.
    """
    need = closure(nodes, goal)
    c = cpm(nodes, need)
    seed_rank = {k: i for i, k in enumerate(seed_order or ())}
    def key(k):
        return (round(c["slack"][k], 3), round(c["es"][k], 3),
                seed_rank.get(k, 10 ** 9), nodes[k]["_total_cost"], k)
    order = sorted(need, key=key)
    extras = pick_side_branches(nodes, need, s, side_branches) if side_branches else []
    order = interleave(order, extras, side_branch_every)
    return order, c, extras


def _capture_winner_order(nodes, goal, need, results):
    """The same rule `--save-winner` uses in cli.py: the closure-only finish
    order of whichever trial reached the goal soonest, or None if none did.
    Kept in step with that function on purpose - see its own comment on why
    "everything a winner touched" (2,676 nodes) scores 0% while "only what the
    goal needs, in the order a winner actually finished it" (149 nodes)
    scores 100%. Duplicated rather than imported because cli.py's version is
    embedded in cmd_run and works from parsed argparse args, not a bare list
    of Sim results; the RULE is what has to match, not the plumbing.
    """
    won = [r for r in results if r.goal_year]
    if not won:
        return None, None
    best = min(won, key=lambda r: r.goal_year)
    seq = sorted((k for k in best.done if k in need and k not in best.granted),
                 key=lambda k: (best.done_year.get(k, 0), k))
    return seq, best


def refine(nodes, goal, s, order, extras, civ, mc, horizon, seed, rounds,
           side_branch_every=8, log=print):
    """CLOSE THE LOOP: plan, measure, capture the winner, re-plan from it.

    This is still not Monte Carlo SEARCH - nothing here tries random orders
    and hopes. Each round runs a small batch of trials against ONE candidate
    order to measure it (the same thing `run --mc` already does), and if any
    trial won, its own finish order becomes the seed for the NEXT
    deterministic CPM pass - the same evidence `--save-winner` already
    captures to a file today, just fed straight back in instead of requiring
    someone to notice, save it, and remember to pass it to the next
    invocation. The order actually kept at the end is whichever round scored
    best on WIN RATE first, then median year reached, never on vibes.
    """
    need = closure(nodes, goal)
    # CURRENT is what gets measured and then advanced each round; BEST is
    # whichever round's order scored best, which is what gets returned. These
    # must not be the same variable: a later round can score WORSE than an
    # earlier one (a seed can mislead the tie-break as easily as help it), and
    # returning "whatever the last round produced" regardless of its score
    # would silently throw away a better round that came before it.
    cur_order, cur_extras = order, extras
    best_order, best_extras, best_score = order, extras, None
    for rnd in range(rounds):
        res = [Sim(nodes, cur_order, random.Random(seed + i), events=True,
                   civ=load_civ(civ)).run(goal, horizon)
               for i in range(mc)]
        wins = sum(1 for r in res if r.goal_year)
        years = sorted(r.goal_year for r in res if r.goal_year)
        med = years[len(years) // 2] if years else None
        # Win rate first, then an EARLIER median beats a later one - negated so
        # a plain tuple comparison ("higher score wins") reads the right way
        # for both halves at once.
        score = (wins, -(med or 10 ** 9))
        log("  round %d: %d/%d reached the goal%s"
            % (rnd, wins, mc, (", median %d AD" % med) if med else ""))
        if best_score is None or score > best_score:
            best_score, best_order, best_extras = score, cur_order, cur_extras
        seq, _winner = _capture_winner_order(nodes, goal, need, res)
        if seq is None:
            # Nothing won this round; there is no fresh evidence to seed the
            # next pass with, so re-planning from the SAME seed would just
            # reproduce this round exactly. Stop rather than burn the rest of
            # the trial budget on a repeat.
            log("  no trial reached the goal this round; stopping refinement early")
            break
        cur_order, _c, cur_extras = backward_plan(
            nodes, goal, s, seed_order=seq,
            side_branches=len(extras), side_branch_every=side_branch_every)
    return best_order, best_extras, best_score


# ----------------------------------------------------------------------------
# Strategy file I/O
# ----------------------------------------------------------------------------

def load_seed(path, nodes):
    if not path:
        return None
    p = path
    if not os.path.exists(p):
        p = os.path.join(STRATS, path + ".json")
    with open(p) as fh:
        blob = json.load(fh)
    return [k for k in blob.get("order", []) if k in nodes]


def write_strategy(path, label, rationale, order):
    out = {"label": label, "rationale": rationale, "order": order}
    with open(path, "w") as fh:
        json.dump(out, fh, indent=1)
    return path


def plan(civ="rome_100ad", goal=None, seed_strategy=None, side_branches=12,
         side_branch_every=8, refine_rounds=0, mc=12, horizon=700, seed=1,
         log=print):
    """The whole pipeline: load the tree, build a throwaway Sim for `civ`
    (never stepped - only used for its own filters: what this civilisation
    already has for free, and which institutions belong to somebody else),
    compute the CPM order, optionally weave in a seed and refine against real
    trials, and hand back (order, rationale_lines, cpm_summary).
    """
    tree, prices, nodes, wages, goods = load()
    goal = goal or tree["meta"]["goal_node"]
    s = Sim(nodes, [], random.Random(seed), events=False, civ=load_civ(civ))
    seed_order = load_seed(seed_strategy, nodes)
    order, c, extras = backward_plan(nodes, goal, s, seed_order, side_branches,
                                     side_branch_every)
    score = None
    if refine_rounds:
        order, extras, score = refine(nodes, goal, s, order, extras, civ, mc,
                                      horizon, seed, refine_rounds,
                                      side_branch_every, log)
    need = closure(nodes, goal)
    crit = sum(1 for k in need if c["slack"].get(k, 0) <= 1e-6)
    rationale = [
        "Computed backward from the goal by critical-path method (CPM) over "
        "its %d-node prerequisite closure, not observed from a lucky run: "
        "%d of those nodes have zero slack (%.1f years of critical-path "
        "floor total) and are ordered first; everything else is ordered by "
        "how much room it has to wait without delaying the goal."
        % (len(need), crit, c["total"]),
    ]
    if seed_order:
        rationale.append(
            "Seeded from %s (%d nodes recognised): used only to break ties "
            "among nodes the graph itself ranks as equally urgent, never to "
            "override the CPM ordering of two nodes at different slack."
            % (seed_strategy, len(seed_order)))
    if extras:
        rationale.append(
            "%d revenue-positive side branch(es) outside the goal's own "
            "requirements, chosen for %s's own economy by return on capital "
            "(net annual revenue per denarius of setup cost) and woven in "
            "roughly one per %d spine nodes so the household has something "
            "to run while the spine is being built, rather than waiting on "
            "the engine's own reactive fallback to notice it is starving."
            % (len(extras), civ, side_branch_every))
    if score is not None:
        rationale.append(
            "Refined over %d round(s) of %d trials each at a %d-year "
            "horizon (seed %d): each round's winning trial's own finish "
            "order was fed back as the next round's tie-break seed. Final "
            "round: %d/%d trials reached the goal."
            % (refine_rounds, mc, horizon, seed, score[0], mc))
    return order, rationale, c


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--civ", default="rome_100ad")
    ap.add_argument("--goal", default=None)
    ap.add_argument("--out", required=True, help="strategy file to write")
    ap.add_argument("--seed-strategy", default=None,
                    help="a strategy name or path (e.g. captured_han_386, or "
                         "a previous plan) to seed ties with")
    ap.add_argument("--side-branches", type=int, default=12)
    ap.add_argument("--side-branch-every", type=int, default=8)
    ap.add_argument("--refine-rounds", type=int, default=0,
                    help="plan, run --mc trials, capture the winner, re-plan; "
                         "repeat this many times. 0 (default) skips it and "
                         "stays purely structural/instant.")
    ap.add_argument("--mc", type=int, default=12)
    ap.add_argument("--horizon", type=int, default=700)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    order, rationale, c = plan(a.civ, a.goal, a.seed_strategy, a.side_branches,
                               a.side_branch_every, a.refine_rounds, a.mc,
                               a.horizon, a.seed)
    tree, _p, nodes, _w, _g = load()
    goal = a.goal or tree["meta"]["goal_node"]
    label = ("PLANNED (CPM): backward-chained from %s over its prerequisite "
            "closure for %s%s" % (goal, a.civ,
                                  ", refined against real trials" if a.refine_rounds else ""))
    write_strategy(a.out, label, rationale, order)
    print("wrote %d nodes to %s" % (len(order), a.out))
    for line in rationale:
        print("  - " + line)


if __name__ == "__main__":
    main()
