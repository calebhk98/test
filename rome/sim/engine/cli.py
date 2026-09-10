"""The command line: validate, costs, path, run, compare, play, agent."""
import collections, json, math, os, random
from collections import defaultdict

from .data import *          # the shared tables and loaders
from .data import (WAGES, ANNUAL_WAGE, TRADE_NOTES, TRADES_ABSENT,
                   TRADE_FAMILY, TECH_EFFECTS, DEFAULTS, SHOCKS,
                   STARTING_KITS, trade_family, closure, critical_path,
                   topo_order, load, load_civ, haversine_km,
                   load_geography, load_resources)


import argparse, sys

from .core import Sim
from .protocol import (
    _agent_available, _agent_dispatch, _agent_end_reason, _agent_help,
    _agent_state, _node_explain, load_state, render_pretty, save_state)


def load_strategy(name, nodes, goal):
    path = os.path.join(STRATS, name + ".json")
    if os.path.exists(path):
        s = json.load(open(path))
        order = [k for k in s["order"] if k in nodes]
        # Everything the strategy did not name gets a sensible default ordering:
        # things the goal needs first, then by tier, then cheapest first. Falling
        # back to alphabetical order made the simulation spend a century acquiring
        # ox carts before it touched a furnace.
        need = closure(nodes, "point_contact_transistor")
        rest = [k for k in nodes if k not in order]
        rest.sort(key=lambda k: (k not in need, nodes[k]["tier"],
                                 nodes[k]["_total_cost"], k))
        rest = topo_stable(nodes, rest)
        return s.get("label", name), order + rest, set(s.get("bounties", []))
    if name == "topo":
        need = closure(nodes, goal)
        order = topo_order(nodes, need)
        return ("bare topological order to the goal",
                order + [k for k in topo_order(nodes) if k not in need], set())
    if name == "cheapest":
        order = sorted(nodes, key=lambda k: nodes[k]["_total_cost"])
        return "cheapest first", topo_stable(nodes, order), set()
    raise SystemExit("unknown strategy: %s" % name)


def topo_stable(nodes, preference):
    """Reorder `preference` so no node precedes its prerequisites."""
    out, placed = [], set()
    pref = list(preference)
    guard = 0
    while pref and guard < 100000:
        guard += 1
        for k in list(pref):
            if all(p in placed for p in nodes[k]["pre"]):
                out.append(k); placed.add(k); pref.remove(k); break
        else:
            out.extend(pref); break
    return out


# ----------------------------------------------------------------------------
# Commands
# ----------------------------------------------------------------------------

def cmd_validate(a):
    tree, prices, nodes, wages, goods = load()
    errs, warns = [], []
    for k, n in nodes.items():
        for p in n["pre"]:
            if p not in nodes: errs.append("%s: unknown prereq %s" % (k, p))
        for m in n["mat"]:
            if m not in goods: errs.append("%s: unpriced material %s" % (k, m))
        for t in n["lab"]:
            if t not in wages: errs.append("%s: unknown trade %s" % (k, t))
        if not 0 <= n["risk"] <= 1: errs.append("%s: risk out of range" % k)
        if n["conf"] not in "ABC": warns.append("%s: odd confidence %s" % (k, n["conf"]))
        # A `why` on seven hand-written nodes killed the process with KeyError
        # 'sus' because I added them without the v1 scalars the explain path
        # still reads. Catch a missing field here, where it is a warning, rather
        # than in a player's session, where it is the end of their game.
        for f in ("sus", "gov", "tier", "cat", "pre", "ph", "cap", "up", "risk"):
            if f not in n:
                errs.append("%s: missing required field '%s'" % (k, f))
    try:
        topo_order(nodes)
    except RuntimeError as e:
        errs.append(str(e))
    goal = tree["meta"]["goal_node"]
    need = closure(nodes, goal)
    print("nodes            : %d" % len(nodes))
    print("edges            : %d" % sum(len(n["pre"]) for n in nodes.values()))
    print("required for goal: %d  (%d are optional: revenue, survival, side branches)"
          % (len(need), len(nodes) - len(need)))
    yrs, chain = critical_path(nodes, goal)
    print("critical path    : %.1f years of irreducible serial time, %d nodes deep" % (yrs, len(chain)))
    print("total capital     : %s den across all %d nodes" % (f"{sum(n['_total_cost'] for n in nodes.values()):,.0f}", len(nodes)))
    print("total founder hrs : %s" % f"{sum(n['ph'] for n in nodes.values()):,}")
    print()
    if errs:
        print("ERRORS:"); [print("  " + e) for e in errs]
    if warns:
        print("WARNINGS:"); [print("  " + w) for w in warns]
    if not errs:
        print("OK: tree is a valid DAG, fully priced, goal reachable.")
    return 1 if errs else 0


def cmd_path(a):
    tree, prices, nodes, wages, goods = load()
    goal = a.goal or tree["meta"]["goal_node"]
    need = closure(nodes, goal)
    order = topo_order(nodes, need)
    cum_cost = cum_ph = 0.0
    print("%-4s %-34s %-5s %8s %9s %6s %5s %5s" %
          ("#", "node", "tier", "yourhrs", "cost(den)", "years", "risk", "conf"))
    print("-" * 88)
    for i, k in enumerate(order, 1):
        n = nodes[k]
        cum_cost += n["_total_cost"]; cum_ph += n["ph"]
        print("%-4d %-34s %-5d %8d %9s %6.1f %5.2f %5s" %
              (i, k[:34], n["tier"], n["ph"], f"{n['_total_cost']:,.0f}", n["yrs"], n["risk"], n["conf"]))
    print("-" * 88)
    print("TOTAL  %d nodes   %s founder-hours   %s denarii" %
          (len(order), f"{cum_ph:,.0f}", f"{cum_cost:,.0f}"))
    yrs, chain = critical_path(nodes, goal)
    print("\nLongest serial chain (%.1f yr floor, cannot be bought down with money):" % yrs)
    for k in chain:
        print("   -> %s  (%.1f yr floor, %d your-hrs)" % (k, nodes[k]["yrs"], nodes[k]["ph"]))
    print("\nFounder-hours available in one lifetime at 2400/yr for 30 yrs: 72,000")
    print("Founder-hours demanded by this path                          : %s" % f"{cum_ph:,.0f}")
    print("=> %s" % ("feasible alone in principle, but not with the calendar floors"
                     if cum_ph < 72000 else
                     "IMPOSSIBLE for one person. You must convert your hours into other people's hours."))


def cmd_costs(a):
    tree, prices, nodes, wages, goods = load()
    rows = sorted(nodes.values(), key=lambda n: -n["_total_cost"])[:a.top]
    print("%-34s %10s %10s %10s %8s %6s" % ("node", "labour", "materials", "capital", "TOTAL", "rev/yr"))
    print("-" * 84)
    for n in rows:
        print("%-34s %10s %10s %10s %8s %6s" % (
            n["id"][:34], f"{n['_labour_cost']:,.0f}", f"{n['_material_cost']:,.0f}",
            f"{n['cap']:,.0f}", f"{n['_total_cost']:,.0f}", f"{n['rev']:,}"))
    print()
    prof = sorted([n for n in nodes.values() if n["rev"]], key=lambda n: -(n["rev"] / max(n["_total_cost"], 1)))
    print("Best return on capital (revenue per denarius of setup cost):")
    for n in prof[:12]:
        print("  %-32s %6.2f  (rev %s / cost %s)" %
              (n["id"][:32], n["rev"] / max(n["_total_cost"], 1), f"{n['rev']:,}", f"{n['_total_cost']:,.0f}"))


def _summarise(results, label):
    ok = [r for r in results if r.goal_year]
    print("\n=== %s ===" % label)
    print("runs                : %d" % len(results))
    print("reached transistor  : %d  (%.0f%%)" % (len(ok), 100.0 * len(ok) / len(results)))
    if ok:
        ys = sorted(r.goal_year for r in ok)
        q = lambda p: ys[min(len(ys) - 1, int(p * len(ys)))]
        print("year reached        : best %d | p25 %d | median %d | p75 %d | worst %d"
              % (ys[0], q(.25), q(.5), q(.75), ys[-1]))
        start = results[0].cfg["start_year"]
        print("elapsed from %d AD  : median %d years" % (start, q(.5) - start))
    sh = collections.Counter()
    for r in results:
        sh.update(r.shortages)
    if sh:
        print("years spent short of a raw material (median run):")
        for k, v in sh.most_common(5):
            print("   %-12s %d run-years" % (k, v))
    fh = sorted(r.forest_ha for r in results)
    print("coppice woodland owned: median %.0f hectares" % fh[len(fh) // 2])
    rep = sorted(r.reputation for r in results)
    print("final reputation    : median %.0f/100" % rep[len(rep) // 2])
    b = [r.bounties_paid for r in results]
    if any(b):
        print("bounties posted     : mean %.1f per run" % (sum(b) / len(b)))
    causes = defaultdict(int)
    for r in results:
        if r.dead_reason: causes[r.dead_reason.split(":")[0]] += 1
        elif not r.goal_year: causes["ran out of horizon"] += 1
    if causes:
        print("failure modes       :")
        for k, v in sorted(causes.items(), key=lambda x: -x[1]):
            print("   %-58s %3d (%.0f%%)" % (k, v, 100.0 * v / len(results)))
    # where do runs get stuck
    stuck = defaultdict(int)
    for r in results:
        if not r.goal_year:
            need = closure(r.nodes, "point_contact_transistor")
            miss = [k for k in topo_order(r.nodes, need) if k not in r.done]
            if miss: stuck[miss[0]] += 1
    if stuck:
        print("first blocked node  :")
        for k, v in sorted(stuck.items(), key=lambda x: -x[1])[:6]:
            print("   %-58s %3d" % (k, v))


def cmd_run(a):
    tree, prices, nodes, wages, goods = load()
    goal = tree["meta"]["goal_node"]
    label, order, bounties = load_strategy(a.strategy, nodes, goal)
    res = []
    for i in range(a.mc):
        rng = random.Random(a.seed + i)
        s = Sim(nodes, order, rng, events=not a.no_events,
                cfg={"immortal": not a.mortal,
                     "start_capital": STARTING_KITS[a.kit]["den"]},
                civ=load_civ(a.civ),
                bounty_set=(set() if a.no_bounties else bounties)).run(goal, a.horizon)
        res.append(s)
    _summarise(res, "%s%s" % (label, "  [events disabled]" if a.no_events else ""))
    if a.trace:
        s = res[0]
        print("\n--- trace of run 0 ---")
        for y, m in s.log:
            print("  %4d  %s" % (y, m))


def cmd_compare(a):
    tree, prices, nodes, wages, goods = load()
    goal = tree["meta"]["goal_node"]
    for name in ["rush", "topo", "recommended"]:
        try:
            label, order, bounties = load_strategy(name, nodes, goal)
        except SystemExit:
            continue
        # At 3000 nodes a full comparison takes tens of minutes. Without this
        # line, and without the flushes below, the command looks hung: stdout
        # is block-buffered when redirected, so nothing at all appeared until
        # the very end.
        sys.stderr.write("  running %s: %d trials...\n" % (name, a.mc))
        sys.stderr.flush()
        res = [Sim(nodes, order, random.Random(a.seed + i), events=True,
                   cfg={"immortal": not getattr(a, "mortal", False),
                        "start_capital": STARTING_KITS.get(getattr(a,"kit","poor_scholar"),
                                                           STARTING_KITS["poor_scholar"])["den"]},
                   civ=load_civ(getattr(a, "civ", "rome_100ad")),
                   bounty_set=bounties).run(goal, a.horizon)
               for i in range(a.mc)]
        _summarise(res, label)
        sys.stdout.flush()


def cmd_play(a):
    """Interactive human REPL. Two modes:

    Default (no --manual): unchanged from before. Typing a node id only
    reprioritises `order`; the optimizer in step() 4b still starts whatever
    else it wants that year. This mode exists to WATCH the optimizer, and it
    is honestly labelled below as advisory, not a real choice.

    --manual: the optimizer's 4b loop is switched off (see Sim.manual). Typing
    a node id now calls start_project(), which is the ONLY thing that starts
    it. Nothing else will ever become active on its own. This is a real game:
    what you do not start, does not happen. See the `agent` command for the
    same guarantee driven by a script instead of a keyboard.
    """
    tree, prices, nodes, wages, goods = load()
    goal = tree["meta"]["goal_node"]
    label, order, bounties = load_strategy(a.strategy, nodes, goal)
    # `play` used to always be Rome, with no way to say otherwise, while `run`
    # and `agent` both took --civ. A human at the keyboard could not reach four
    # of the five civilisations at all.
    cfg = {"immortal": not getattr(a, "mortal", False)}
    kit = getattr(a, "kit", None)
    if kit:
        cfg["start_capital"] = STARTING_KITS[kit]["den"]
    s = Sim(nodes, order, random.Random(a.seed), events=True, bounty_set=bounties,
            manual=a.manual, civ=load_civ(getattr(a, "civ", None) or "rome_100ad"),
            cfg=cfg)
    s.goal = goal; s.done_year = {}
    s.fog = bool(getattr(a, "fog", False))
    if a.manual:
        print("You arrive in %d AD with %d denarii in unminted gold. MANUAL MODE:\n"
              "nothing starts unless you start it. Type a node id to start it,\n"
              "'x <id>' to abandon it, 'a' for what is available,\n"
              "'s' for status, 'n' to advance a year, 'q' to quit.\n" % (s.year, s.capital))
    else:
        print("You arrive in %d AD with %d denarii in unminted gold.\n"
              "Type a node id to PRIORITISE it (the optimizer still runs the rest;\n"
              "pass --manual for real free choice), 'a' for what is available,\n"
              "'s' for status, 'n' to advance a year, 'q' to quit.\n" % (s.year, s.capital))
    # NOT 100 + horizon. That constant was Rome's start year, harmless while
    # `play` could only ever be Rome, and fatal the moment it accepted --civ:
    # a Norse game begins in 900, and 900 is not less than 600, so the loop
    # ended before the player typed anything. The civilisation says when it
    # starts; the horizon is measured from there.
    end_year = getattr(s, "end_year", None) or (s.cfg["start_year"] + (a.horizon or 400))
    while s.year < end_year and not s.dead_reason and not s.goal_year:
        cmd = input("[%d AD | %d den | you:%d hr | sch %.0f art %.0f | rep %.0f | susp %.0f] > "
                    % (s.year, s.capital, s.director_pool(), s.scholars, s.artisans,
                       s.reputation, s.suspicion)).strip()
        if cmd == "q": break
        if cmd == "n":
            before = set(s.done); s.step()
            for k in sorted(s.done - before):    # sorted: see protocol.py
                print("   completed:", nodes[k]["name"])
            for y, m in s.log[-3:]: print("   %d %s" % (y, m))
            continue
        if cmd == "a":
            av = [k for k in s.order if s.can_start(k)][:20]
            for k in av:
                n = nodes[k]
                print("   %-32s cost %8s  your-hrs %5d  %s"
                      % (k, f"{n['_total_cost']:,.0f}", n["ph"], n["note"][:60]))
            continue
        if cmd == "s":
            print("   done: %d  active: %s" % (len(s.done), ", ".join(s.active) or "nothing"))
            continue
        if cmd.startswith("x ") and a.manual:
            target = cmd[2:].strip()
            ok, why = s.stop_project(target)
            print("   stopped." if ok else "   can't: %s" % why)
            continue
        if cmd in nodes:
            if a.manual:
                ok, why = s.start_project(cmd)
                print("   started." if ok else "   blocked: %s" % why)
            elif s.can_start(cmd):
                s.order.remove(cmd); s.order.insert(0, cmd); print("   prioritised.")
            else:
                miss = [p for p in nodes[cmd]["pre"] if p not in s.done]
                print("   blocked. missing:", ", ".join(miss) or
                      "staff (needs %d scholars, %d artisans)" % (nodes[cmd]["sch"], nodes[cmd]["art"]))
        else:
            print("   unknown command")
    print("\nEnded %d AD. %s" % (s.year, s.dead_reason or ("GOAL REACHED" if s.goal_year else "horizon")))


# ----------------------------------------------------------------------------
# Machine-playable interface: `agent`
#
# See the module docstring for the protocol table. In short: every line in,
# every line out, is one JSON object. `state` reports; `start`/`stop`/`bounty`/
# `buy` act; `step` advances the calendar. It is built on the same Sim.manual
# and start_project()/stop_project() this file's step()/can_start() comments
# already explain, so an agent driving this gets EXACTLY the consequences of
# its own choices, nothing the optimizer would have chosen for it.
# ----------------------------------------------------------------------------


def cmd_agent(a):
    """Machine-playable driver: JSON in, JSON out. See the module docstring for
    the protocol. Runs in Sim.manual mode ALWAYS, regardless of any other flag:
    the entire point of this command is that a script chooses the research
    path, so the optimizer's own auto-start (step() 4b) is never in play here.
    That is different from `play --manual`, which is the same guarantee for a
    human at a keyboard; `agent` is that guarantee for a script or an LLM.
    """
    tree, prices, nodes, wages, goods = load()
    goal = tree["meta"]["goal_node"]
    label, order, bounties = load_strategy(a.strategy, nodes, goal)
    # `run`/`compare`/`play` all take --mortal; `agent` silently did not, so
    # the founder was immortal in every scripted or JSON-driven game no
    # matter what was asked for - and the menu (below) was printing a
    # "--mortal" flag on its suggested agent command line that argparse would
    # have rejected outright, because the flag did not exist here at all.
    cfg = {"start_capital": STARTING_KITS[a.kit]["den"], "horizon_years": a.horizon,
           "immortal": not getattr(a, "mortal", False)}
    s = Sim(nodes, order, random.Random(a.seed), events=not a.no_events,
            cfg=cfg, civ=load_civ(a.civ), bounty_set=set(), manual=True)
    s.goal = goal
    s.done_year = {}
    s.end_year = s.cfg["start_year"] + a.horizon
    s.fog = bool(getattr(a, "fog", False))
    s.revealed = set()
    pretty = bool(getattr(a, "pretty", False))

    session = getattr(a, "session", None)
    if session and os.path.exists(session):
        try:
            load_state(s, session)
        except Exception as e:
            sys.stdout.write(json.dumps(
                {"ok": False, "error": "could not read the save file %r: %s" % (session, e)}
            ) + "\n")
            return 1

    def emit(obj, op=None):
        # THE JSON LINE IS UNCHANGED, ALWAYS, REGARDLESS OF --pretty. It is
        # written first, exactly as before pretty rendering existed, so a
        # script reading only stdout sees byte-identical output whether or
        # not a human also asked for a readable view. The readable view - if
        # asked for - is a SEPARATE line on stderr, alongside the JSON, never
        # instead of it, so nothing that parses stdout has to change either.
        sys.stdout.write(json.dumps(obj) + "\n")
        sys.stdout.flush()
        if pretty:
            sys.stderr.write(render_pretty(op, obj) + "\n\n")
            sys.stderr.flush()

    # A player who has been told nothing but the path to this file must still be
    # able to start. On a new game the first line out is the whole briefing,
    # unasked, because there is nowhere else for them to learn it.
    # To STDERR, deliberately. stdout is the protocol and must stay exactly one
    # reply per command: an unsolicited line there shifts every index and breaks
    # anything parsing positionally, which it promptly did to my own tests.
    if not (session and os.path.exists(session)):
        sys.stderr.write(json.dumps(
            {"welcome": _agent_help(s),
             "read this first": "This is the only instruction you get. Everything "
                                "else is here or in {\"cmd\":\"help\"}."},
            indent=1) + "\n")
        sys.stderr.flush()

    if a.script:
        try:
            cmds = json.load(open(a.script))
        except (OSError, ValueError) as e:
            emit({"ok": False, "error": "could not read script %r: %s" % (a.script, e)})
            return 1
        if not isinstance(cmds, list):
            emit({"ok": False, "error": "--script file must contain a JSON list of command objects"})
            return 1
        for c in cmds:
            emit(_agent_dispatch(s, nodes, c), c.get("cmd") if isinstance(c, dict) else None)
            if session:
                save_state(s, session)
        return 0

    # REPL over stdin/stdout: one JSON command per line in, one JSON object
    # per line out. This is the primary form; --script above is a thin
    # wrapper that replays a fixed list through the same dispatcher.
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            cmd = json.loads(line)
        except ValueError as e:
            emit({"ok": False, "error": "invalid JSON: %s" % e})
            continue
        # The dispatcher guards non-object input and replies politely, and then
        # THIS line used to kill the process: cmd.get on a bare null, number,
        # string or list is an AttributeError. A playtester reopened the
        # "malformed input ends your game" class through the quit check, one
        # line after the guard that was supposed to prevent exactly that.
        try:
            resp = _agent_dispatch(s, nodes, cmd)
        except Exception as e:                      # never lose a session to a bug
            resp = {"ok": False,
                    "error": "internal error handling that command: %s: %s. "
                             "The game is intact; try something else."
                             % (type(e).__name__, e)}
        emit(resp, cmd.get("cmd") if isinstance(cmd, dict) else None)
        if session:
            save_state(s, session)
        if isinstance(cmd, dict) and cmd.get("cmd") == "quit":
            break
    return 0


def cmd_sensitivity(a):
    """Ablation study: how much is each defensive or institutional node worth?

    Removes one node from the strategy (so it is never built) and re-runs. Nodes
    that are prerequisites of the goal cannot be ablated and are reported as such.
    """
    tree, prices, nodes, wages, goods = load()
    goal = tree["meta"]["goal_node"]
    label, order, bounties = load_strategy(a.strategy, nodes, goal)
    need = closure(nodes, goal)

    def trial(drop=None):
        o = [k for k in order if k != drop]
        res = [Sim(nodes, o, random.Random(a.seed + i), events=True,
                   bounty_set=bounties).run(goal, a.horizon)
               for i in range(a.mc)]
        ok = sorted(r.goal_year for r in res if r.goal_year)
        return (100.0 * len(ok) / len(res), ok[len(ok) // 2] if ok else None)

    base_rate, base_med = trial()
    print("baseline (%s): %.0f%% reach the goal, median %s AD" %
          (a.strategy, base_rate, base_med))
    print("A node's value shows up in the CALENDAR at least as much as in the")
    print("success rate, so both are scored. 'delay' is how many years later the")
    print("median run reaches the transistor when this node is never built.\n")
    print("%-24s %8s %8s %8s   %s" % ("node removed", "success", "median", "delay", "verdict"))
    print("-" * 78)
    cands = ["plague_preparedness", "corpus_written", "corpus_dispersed", "printing_press",
             "rag_paper", "school_founded", "academy_network", "endowment_land",
             "freedman_staff", "collegium_licensed", "patron_senatorial", "patron_imperial",
             "semaphore_telegraph", "citizenship", "mirror_amalgam", "lens_grinding",
             "crop_rotation", "world_map", "sanitation_antisepsis", "telegraph_electric"]
    rows = []
    for k in cands:
        if k not in nodes:
            continue
        if k in need:
            print("%-26s %10s %10s   hard prerequisite of the goal, cannot be skipped" % (k, "-", "-"))
            continue
        r, m = trial(k)
        rows.append((base_rate - r, k, r, m))
    scored = []
    for d, k, r, m in rows:
        delay = (m - base_med) if (m and base_med) else 999
        # one point of success rate is worth roughly two years of delay
        score = d + delay / 2.0
        scored.append((score, k, r, m, d, delay))
    for score, k, r, m, d, delay in sorted(scored, reverse=True):
        verdict = ("CRITICAL, do not skip" if score > 20 else
                   "clearly worth it" if score > 8 else
                   "worth it" if score > 3 else
                   "marginal in this model" if score > -3 else
                   "the model says this costs more than it returns")
        print("%-24s %7.0f%% %8s %+8s   %s" %
              (k, r, m or "never", ("%d yr" % delay) if m else "n/a", verdict))


def cmd_why(a):
    """Explain one node: what it needs, what needs it, and what it costs."""
    tree, prices, nodes, wages, goods = load()
    k = a.node
    if k not in nodes:
        near = [x for x in nodes if a.node.lower() in x.lower()]
        raise SystemExit("unknown node. did you mean: %s" % (", ".join(near[:8]) or "no idea"))
    n = nodes[k]
    print("%s  [tier %d, %s, confidence %s]" % (n["name"], n["tier"], n["cat"], n["conf"]))
    print("=" * 78)
    print(n["note"])
    print()
    print("Recipe          : rome/knowledge/%s" % n["kb"])
    print("Your hours      : %s   (%.1f%% of a 72,000-hour life)" % (f"{n['ph']:,}", 100.0 * n["ph"] / 72000))
    print("Hired labour    : %s" % (", ".join("%s %s h" % (t, f"{h:,}") for t, h in n["lab"].items()) or "none"))
    print("Materials       : %s" % (", ".join("%s %s" % (m, f"{q:,}") for m, q in n["mat"].items()) or "none"))
    print("Cost            : %s den labour + %s materials + %s capital = %s TOTAL"
          % (f"{n['_labour_cost']:,.0f}", f"{n['_material_cost']:,.0f}",
             f"{n['cap']:,}", f"{n['_total_cost']:,.0f}"))
    print("Upkeep          : %s den/yr        Revenue: %s den/yr" % (f"{n['up']:,}", f"{n['rev']:,}"))
    print("Calendar floor  : %.1f years (money cannot buy this down)" % n["yrs"])
    print("Failure risk    : %.0f%% per attempt" % (100 * n["risk"]))
    print("Staff needed    : %d trained scholars, %d trained artisans" % (n["sch"], n["art"]))
    print("Suspicion       : %+d       State interest: %+d%s" % (n.get("sus", 0), n.get("gov", 0),
          ("  <- OPPOSED. Costs %d%% more, +%d extra suspicion, needs %s"
           % (25 * -n.get("gov", 0), 3 * -n.get("gov", 0),
              "senatorial patronage" if n.get("gov", 0) <= -2 else "a patron"))
          if n.get("gov", 0) < 0 else ""))
    eligible = (n["tier"] <= 2 and n["cat"] in ("glass_optics", "metallurgy", "precision",
                "power", "agriculture", "information", "instruments"))
    print("Bounty          : %s" % ("YES, can be bought as a public prize for about %s den"
                                    % f"{n['_total_cost'] * 2.5:,.0f}" if eligible else
                                    "no, a local craftsman could not recognise success"))
    print()
    print("DIRECT PREREQUISITES")
    for p_ in n["pre"] or ["(none, you can start this on arrival)"]:
        print("   %s" % (("%-30s %s" % (p_, nodes[p_]["name"])) if p_ in nodes else p_))
    need = closure(nodes, k) - {k}
    print("\nFULL CHAIN BEHIND IT: %d nodes, %s of your hours, %s denarii, %.0f-year serial floor"
          % (len(need), f"{sum(nodes[x]['ph'] for x in need):,}",
             f"{sum(nodes[x]['_total_cost'] for x in need):,.0f}", critical_path(nodes, k)[0]))
    print("   " + ", ".join(topo_order(nodes, need)))
    unlocks = [m for m in nodes if k in nodes[m]["pre"]]
    print("\nDIRECTLY UNLOCKS")
    for u in unlocks or ["(nothing, this is a leaf)"]:
        print("   %s" % (("%-30s %s" % (u, nodes[u]["name"])) if u in nodes else u))
    blocks = {m for m in nodes if k in closure(nodes, m)} - {k}
    print("\nTOTAL DOWNSTREAM: %d nodes depend on this, directly or indirectly." % len(blocks))
    if "point_contact_transistor" in blocks:
        print("   INCLUDING THE GOAL. This node is on the critical path.")


def cmd_sweep(a):
    """Sweep a starting condition and show how the outcome and the FAILURE MODE move.

    The failure mode moving is the interesting part. More starting capital does
    not simply help: past a point it switches you from dying poor and untaught to
    being denounced as a magician, because money buys speed, speed buys
    visibility, and visibility in Trajanic Rome is dangerous.
    """
    tree, prices, nodes, wages, goods = load()
    goal = tree["meta"]["goal_node"]
    label, order, bounties = load_strategy(a.strategy, nodes, goal)
    sweeps = {
        "capital":  ("start_capital", [2000, 5000, 10320, 25000, 50000, 200000, 1000000]),
        "lifespan": ("founder_life",  [10, 15, 20, 28, 35, 45, 60]),
        "hours":    ("founder_hours_per_year", [1200, 1800, 2400, 3000, 3600]),
        "mortality":("founder_life_mean", [10, 15, 20, 28, 40, 60]),
    }
    key, values = sweeps[a.axis]
    print("sweeping %s under strategy '%s', %d runs per point\n" % (a.axis, a.strategy, a.mc))
    print("%-12s %8s %8s %8s   %s" % (a.axis, "success", "median", "p25", "dominant failure"))
    print("-" * 78)
    for v in values:
        cfg, life = {}, None
        if key == "founder_life_mean":
            cfg = {"immortal": False, "founder_life_mean": v, "founder_life_sd": 4.0}
        elif key == "founder_life":
            life = v
        else:
            cfg[key] = v
        res = []
        for i in range(a.mc):
            sim = Sim(nodes, order, random.Random(a.seed + i), events=True, cfg=cfg,
                      bounty_set=bounties)
            if life is not None:
                sim.life_left = float(life)
            res.append(sim.run(goal, a.horizon))
        ok = sorted(r.goal_year for r in res if r.goal_year)
        c = defaultdict(int)
        for r in res:
            if not r.goal_year:
                c[(r.dead_reason or "ran out of horizon").split(":")[0]] += 1
        worst = max(c.items(), key=lambda x: x[1]) if c else ("none", 0)
        print("%-12s %7.0f%% %8s %8s   %s" %
              (f"{v:,}", 100.0 * len(ok) / len(res),
               ok[len(ok) // 2] if ok else "never",
               ok[len(ok) // 4] if ok else "-",
               "%s (%d)" % (worst[0][:44], worst[1]) if worst[1] else "-"))
    print("\nWatch the failure column, not the success column. When it changes, the")
    print("binding constraint has changed and so should your strategy.")


def cmd_civs(a):
    """List the civilizations you can play, and what makes each one different.

    home_regions and base_reach used to be printed here and read NOWHERE
    ELSE: that was the entire bug this session fixed. They now actually
    drive Sim.region_reach() and Sim.material_reach() (see simulator.py),
    which is a much better reason to show them, so this now also names the
    home ground itself rather than just the region ids.
    """
    geo = load_geography()
    region_names = {rid: r.get("name", rid)
                    for rid, r in (geo.get("regions") or {}).items()
                    if not rid.startswith("_")}
    for f in sorted(os.listdir(CIVDIR)):
        # Files starting with "_" are schema/reference data, not a playable
        # civilization (e.g. _TECH_EFFECTS.json), same convention this file
        # already uses everywhere else for "_"-prefixed keys and entries.
        if not f.endswith(".json") or f.startswith("_"):
            continue
        c = json.load(open(os.path.join(CIVDIR, f)))
        v = c["values"]
        print("%-16s %s, %s" % (c["id"], c["name"], c["year"]))
        print("   %s" % c.get("blurb", ""))
        homes = [region_names.get(r, r) for r in c.get("home_regions") or []]
        print("   home ground: %s" % (", ".join(homes) if homes else "(none set)"))
        print("   population %s   state capacity %.2f   base_reach %d (how far it already "
              "routinely travels)   starts with %d technologies"
              % (f"{c.get('population',0):,}", c.get("state_capacity", 0),
                 c.get("base_reach", 0), len(c.get("starting_techs", []))))
        print("   fears the inexplicable %.2f | fears heterodoxy %.2f | resents machines %+.2f "
              "| bribable %.2f | habituates %.2f"
              % (v["w_magic_fear"], v["w_religious_rigidity"], v["w_labour_saving"],
                 v["bribability"], v["adaptation_rate"]))
        print("   eminence is dangerous %.2f  (how much prominence ITSELF endangers you)"
              % v.get("w_eminence_danger", 0.5))
        mults = c.get("cost_multipliers") or {}
        if mults:
            easy = sorted((x for x in mults.items() if x[1] < 1.0), key=lambda x: x[1])[:4]
            hard = sorted((x for x in mults.items() if x[1] > 1.0), key=lambda x: -x[1])[:4]
            if easy:
                print("   good at : " + ", ".join("%s x%.2f" % kv for kv in easy))
            if hard:
                print("   bad at  : " + ", ".join("%s x%.2f" % kv for kv in hard))
        print()
    print("starting kits (--kit):")
    for k, d in STARTING_KITS.items():
        print("   %-14s %9s den   %s" % (k, f"{d['den']:,}", d["desc"]))
    return 0


def _wrap(text, width=76, indent="   "):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width:
            lines.append(indent + cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(indent + cur)
    return "\n".join(lines)


def _pick_session_filename(civ_id):
    """A save name for a game the menu is about to start, picked so it never
    silently overwrites an existing one.

    A relative filename in the current directory, which is exactly what
    `save` will accept (see _unsafe_path in protocol.py) and exactly where it
    will actually be written.
    """
    candidate = "%s.json" % civ_id
    i = 2
    while os.path.exists(candidate):
        candidate = "%s_%d.json" % (civ_id, i)
        i += 1
    return candidate


def _ask(prompt, options, default=None):
    """Ask until the answer is one of options. Empty input takes the default."""
    while True:
        try:
            raw = input(prompt).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return None
        if not raw and default is not None:
            return default
        if raw in ("q", "quit", "exit"):
            return None
        for o in options:
            if raw == o or (len(raw) == 1 and o.startswith(raw)):
                return o
        print("   -- I did not understand that. Options: %s" % ", ".join(options))


def cmd_menu(a):
    """The front door for a person, rather than for a script.

    Everything here can be done with command-line flags, and the flags are
    what a script should use. This exists because "what do I type" was the
    first thing every human tester had to be told out of band, and because a
    game about arriving somewhere should be able to tell you where you have
    arrived before it asks you to make decisions about it.
    """
    civs = []
    for fn in sorted(os.listdir(CIVDIR)):
        if not fn.endswith(".json") or fn.startswith("_"):
            continue
        civs.append(json.load(open(os.path.join(CIVDIR, fn))))
    civs.sort(key=lambda c: c.get("year", 0))

    print()
    print("=" * 78)
    print("   ONE PERSON, AND EVERYTHING THEY KNOW".center(78))
    print("=" * 78)
    print()
    print(_wrap(
        "You are one person, dropped into a pre-industrial society, carrying "
        "the knowledge of how modern technology works and none of the industry "
        "that makes it. Knowing how a thing works is free. Building it is not: "
        "it costs your own hours, other people's hours, money, materials, and "
        "years you do not get back."))
    print()
    print(_wrap(
        "You arrive alone. No employees, no slaves, nobody who owes you "
        "anything, and about enough money to eat for a few months."))
    print()
    print("-" * 78)
    print("   WHERE, AND WHEN")
    print("-" * 78)
    for i, c in enumerate(civs, 1):
        print()
        print("   %d) %s, %d" % (i, c.get("name", c["id"]), c.get("year", 0)))
        print(_wrap(c.get("blurb", ""), indent="      "))
        print("      %s people   state capacity %.2f   prices %.2fx Rome"
              % (f"{c.get('population', 0):,}", c.get("state_capacity", 0),
                 c.get("price_index", 1.0)))
    print()
    while True:
        try:
            raw = input("   Which one? [1-%d, or q to leave] " % len(civs)).strip()
        except (EOFError, KeyboardInterrupt):
            print(); return
        if raw.lower() in ("q", "quit", "exit"):
            return
        if raw.isdigit() and 1 <= int(raw) <= len(civs):
            civ = civs[int(raw) - 1]
            break
        print("   -- a number from 1 to %d." % len(civs))

    op = civ.get("opening") or {}
    print()
    print("=" * 78)
    print(("   %s, %d" % (civ.get("name", civ["id"]), civ.get("year", 0))).upper())
    print("=" * 78)
    for key, heading in (("arrival", None),
                         ("what_you_can_see", "What you can see"),
                         ("what_is_missing", "What is missing"),
                         ("what_is_coming", "What is coming, and only you know it")):
        if not op.get(key):
            continue
        print()
        if heading:
            print("   %s" % heading.upper())
        print(_wrap(op[key]))
    if not op:
        print()
        print(_wrap(civ.get("blurb", "")))
    print()

    print("-" * 78)
    print(_wrap("FOG OF WAR. With it on you see what you have built, what you "
                "could begin today as a one-line summary, and things you have "
                "heard of but cannot yet start. You cannot see where anything "
                "leads. With it off you can see the whole tree and plan a "
                "route through it.", indent="   "))
    fog = _ask("\n   Fog of war? [Y/n] ", ["y", "n"], "y")
    if fog is None:
        return
    print()
    print("-" * 78)
    print("   WHAT YOU ARRIVED WITH")
    for name, kit in STARTING_KITS.items():
        print("      %-14s %9s den" % (name, f"{kit['den']:,}"))
        if kit.get("desc"):
            print(_wrap(kit["desc"], indent="         "))
    kit = _ask("\n   Which? [%s] " % "/".join(STARTING_KITS), list(STARTING_KITS),
               "poor_scholar")
    if kit is None:
        return
    print()
    print("-" * 78)
    print(_wrap("MORTALITY. By default the founder does not age, which measures "
                "the tree rather than a lifespan lottery. Turned on, you get one "
                "human life and everything you have not made permanent dies with "
                "you. The premise of the whole game is that one is the honest "
                "number.", indent="   "))
    mortal = _ask("\n   Let the founder age and die? [y/N] ", ["y", "n"], "n")
    if mortal is None:
        return

    # THIS USED TO STOP HERE: print the command for the JSON protocol and ASK
    # whether to play. A tester put it plainly - "it should be the save
    # starting. It should have you pick, then you immediately jump in" - and
    # they were right: everything above this point is a choice about WHAT
    # game to start, not whether to start one, and a menu that ends by
    # handing you a command line to go run yourself is not a front door, it
    # is a man page. So: pick where the save goes, say so once, and go.
    #
    # This drops into `agent`, not `play`, even though `agent` speaks JSON
    # rather than plain typed commands. Two reasons. First, only `agent` has
    # a session file at all, and "then you immediately jump in" is worthless
    # if the game vanishes the moment this process exits - the whole point of
    # asking for a save name is that you can come back. Second, `play`
    # WITHOUT --manual is explicitly not a real choice (see its docstring:
    # the optimizer keeps starting things on its own regardless of what you
    # type), and wiring --manual through the menu just to reach the same
    # guarantee `agent` already provides by default would be reinventing it
    # worse. --pretty is what actually answers the testers who found raw
    # JSON hard to read, without giving up the one JSON object per line that
    # makes the save/resume story work at all.
    session = _pick_session_filename(civ["id"])
    print()
    print("=" * 78)
    print(_wrap(
        "Starting now. Progress is written to this file after every command, "
        "so you can stop any time - close the terminal, anything - and come "
        "back to exactly where you left off with:"))
    print()
    print("      python3 rome/sim/simulator.py agent --session %s --pretty" % session)
    print()
    print(_wrap(
        "Type one JSON command per line, for example {\"cmd\":\"available\"} or "
        "{\"cmd\":\"step\",\"years\":5}. Each reply prints as JSON, followed by a "
        "plain-English reading of the same reply. {\"cmd\":\"help\"} explains "
        "everything else, and nothing you type here can be typed wrong badly "
        "enough to lose the game.", indent=""))
    print()

    class Args:
        pass
    args = Args()
    args.strategy = "recommended"
    args.seed = 1
    args.horizon = 500
    args.civ = civ["id"]
    args.kit = kit
    args.mortal = (mortal == "y")
    args.fog = (fog == "y")
    args.no_events = False
    args.session = session
    args.script = None
    args.pretty = True
    return cmd_agent(args)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    # NOT required: typing the bare command should open the menu rather than
    # print a usage error at somebody who has just arrived.
    sub = p.add_subparsers(dest="cmd", required=False)
    sub.add_parser("validate")
    sub.add_parser("civs")
    q = sub.add_parser("path"); q.add_argument("goal", nargs="?")
    q = sub.add_parser("costs"); q.add_argument("--top", type=int, default=20)
    q = sub.add_parser("why"); q.add_argument("node")
    q = sub.add_parser("sweep")
    q.add_argument("axis", choices=["capital", "lifespan", "hours", "mortality"])
    q.add_argument("--strategy", default="recommended")
    q.add_argument("--mc", type=int, default=200)
    q.add_argument("--seed", type=int, default=1)
    q.add_argument("--horizon", type=int, default=500)
    for name in ("run", "compare"):
        q = sub.add_parser(name)
        q.add_argument("--strategy", default="recommended")
        q.add_argument("--mc", type=int, default=200)
        q.add_argument("--seed", type=int, default=1)
        q.add_argument("--horizon", type=int, default=500)
        q.add_argument("--no-events", action="store_true")
        q.add_argument("--no-bounties", action="store_true")
        q.add_argument("--civ", default="rome_100ad",
                       help="which civilization to play. See data/civilizations/")
        q.add_argument("--kit", default="poor_scholar",
                       help="starting wealth: " + ", ".join(STARTING_KITS))
        q.add_argument("--mortal", action="store_true",
                       help="turn the founder's mortality back on (default: immortal, "
                            "so the run measures the TREE and not a lifespan lottery)")
        q.add_argument("--trace", action="store_true")
    q = sub.add_parser("sensitivity")
    q.add_argument("--strategy", default="recommended")
    q.add_argument("--mc", type=int, default=200)
    q.add_argument("--seed", type=int, default=1)
    q.add_argument("--horizon", type=int, default=500)
    sub.add_parser("menu", help="pick a civilisation, read where you have landed, "
                                "and start. This is what a bare invocation does.")
    q = sub.add_parser("play")
    q.add_argument("--strategy", default="recommended")
    q.add_argument("--seed", type=int, default=1)
    q.add_argument("--horizon", type=int, default=500)
    q.add_argument("--civ", default="rome_100ad")
    q.add_argument("--kit", default="poor_scholar",
                   help="starting wealth: " + ", ".join(STARTING_KITS))
    q.add_argument("--fog", action="store_true")
    q.add_argument("--mortal", action="store_true")
    q.add_argument("--manual", action="store_true",
                   help="nothing starts on its own; only nodes you type actually begin. "
                        "Without this flag, typing a node id only reprioritises the "
                        "optimizer, which keeps starting things on its own.")
    q = sub.add_parser("agent", help="JSON protocol so a script or an AI agent can play "
                                     "and choose its own research path. See the module "
                                     "docstring for the command table.")
    q.add_argument("--strategy", default="recommended",
                   help="only used to seed the display order in 'available'; nothing "
                        "is auto-started, this command always runs manual")
    q.add_argument("--seed", type=int, default=1)
    q.add_argument("--horizon", type=int, default=500)
    q.add_argument("--civ", default="rome_100ad")
    q.add_argument("--kit", default="poor_scholar",
                   help="starting wealth: " + ", ".join(STARTING_KITS))
    q.add_argument("--no-events", action="store_true",
                   help="turn off random hazards, for a deterministic scripted playthrough")
    q.add_argument("--fog", action="store_true",
                   help="fog of war: you see what you have built and what you could "
                        "begin next, and nothing about where any of it leads")
    q.add_argument("--mortal", action="store_true",
                   help="turn the founder's mortality back on (default: immortal, "
                        "same meaning as on 'run'/'compare'/'play')")
    q.add_argument("--session", default=None,
                   help="a save file. Loaded if it exists, written after every "
                        "command, so you can play across separate invocations "
                        "without holding a process open")
    q.add_argument("--script", default=None,
                   help="path to a JSON file holding a list of command objects, "
                        "played in order instead of reading stdin")
    q.add_argument("--pretty", action="store_true",
                   help="alongside the ordinary JSON line on stdout - unchanged, "
                        "still exactly one object per line - print a human-readable "
                        "rendering of each reply to stderr. Never changes stdout; "
                        "a script reading only stdout sees no difference at all.")
    a = p.parse_args()
    if not a.cmd:
        a.cmd = "menu"
    return {"validate": cmd_validate, "path": cmd_path, "costs": cmd_costs,
            "why": cmd_why, "sweep": cmd_sweep, "civs": cmd_civs, "menu": cmd_menu,
            "run": cmd_run, "compare": cmd_compare, "play": cmd_play, "agent": cmd_agent,
            "sensitivity": cmd_sensitivity}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main() or 0)
