"""Loading the tree, the prices, the geography and the civilisations."""
#!/usr/bin/env python3
"""
ROME 100 AD -> TRANSISTOR : tech-tree simulator, planner and game.

  a RECORD : validate, costs, path   dump the tree and its economics
  a TOOL   : run, compare, sweep     Monte-Carlo a strategy, find where it breaks
  a GAME   : play, agent             step through it yourself, or let a script play

    python3 rome/sim/simulator.py validate
    python3 rome/sim/simulator.py civs                       who you can play
    python3 rome/sim/simulator.py play --manual               free choice, no autopilot
    python3 rome/sim/simulator.py agent --civ rome_100ad --fog

`agent` speaks one JSON object per line in and one per line out. It explains
itself: it prints a welcome on first run and answers {"cmd":"help"}. There is
no protocol document to read, on purpose.

No third-party dependencies. Python 3.8+.
Design notes and the full protocol: rome/sim/PROTOCOL.md
"""

import argparse, json, math, os, random, sys
sys.setrecursionlimit(20000)
import collections
from collections import defaultdict

# This file lives in rome/sim/engine/, one level deeper than simulator.py used
# to, so the data directory is two parents up rather than one. Everything that
# reads a path reads it from here.
HERE = os.path.dirname(os.path.abspath(__file__))          # rome/sim/engine
SIMDIR = os.path.dirname(HERE)                             # rome/sim
ROOT = os.path.dirname(SIMDIR)                             # rome
TREE = os.path.join(ROOT, "data", "tech_tree.json")
PRICES = os.path.join(ROOT, "data", "prices.json")
STRATS = os.path.join(SIMDIR, "strategies")   # rome/sim/strategies, beside simulator.py

# ----------------------------------------------------------------------------
# Loading and derived economics
# ----------------------------------------------------------------------------

CIVDIR = os.path.join(ROOT, "data", "civilizations")
RESFILE = os.path.join(ROOT, "data", "world", "resources.json")
GEOFILE = os.path.join(ROOT, "data", "world", "geography.json")

def load_resources():
    return json.load(open(RESFILE))

def load_geography():
    """Where things are, not just what they cost.

    geography.json used to carry a single hard-coded `reach` per region,
    measured from Italy, and nothing in this file ever read it: the `civs`
    command printed `base_reach` from the civ file and that was the entire
    effect either number had. Play Han China and the tree still behaved as
    though Italy were reach 0 and Malaya, which Chinese and Malay traders
    already sail to routinely, were an exotic reach-3 frontier. That is
    backwards for every civilization except Rome. See Sim.region_reach and
    Sim.material_reach for the fix: this loader just hands back the raw data.
    """
    return json.load(open(GEOFILE))


def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance between two lat/lon points, in kilometres.

    Coarse on purpose: geography.json's coordinates are region centroids, not
    ports, so this is a reach ESTIMATE, the same spirit as everything else in
    this file being an order-of-magnitude model rather than a survey.
    """
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))

def _load_tech_effects():
    p = os.path.join(CIVDIR, "_TECH_EFFECTS.json")
    try:
        return {k: v for k, v in json.load(open(p)).items() if not k.startswith("_")}
    except Exception:
        return {}


TECH_EFFECTS = _load_tech_effects()


def _load_wages():
    """The wage table, skipping the _note entry that is a bare string.

    My first version did `v["rate"]` over every entry, hit the explanatory
    _note string, raised, and a bare `except` turned that into an empty dict. So
    every trade reported "no such trade" and the error helpfully listed nothing
    at all. Swallowing an exception into a silent empty default is the same
    failure as the save file writing nulls: the bug is the except, not the data.
    """
    p = json.load(open(PRICES))
    return {k: v["rate"] for k, v in p["wage_rates_denarii_per_hour"].items()
            if isinstance(v, dict) and "rate" in v}


WAGES = _load_wages()


def _load_annual_wages():
    """What a year of one person of each trade actually costs.

    Two columns in prices.json disagree with each other by about half: `rate` is
    denarii an hour, `day_hs` is sestertii a day, and rate x 10 hours is
    consistently 1.5x day_hs / 4. The day figure is the better sourced of the
    two (it is what the wage evidence is actually quoted in), so annual pay
    comes from that where it exists, and only falls back to the hourly rate
    where it does not.
    """
    p = json.load(open(PRICES))
    out = {}
    for k, v in p["wage_rates_denarii_per_hour"].items():
        if not isinstance(v, dict):
            continue
        if "day_hs" in v:
            out[k] = v["day_hs"] / 4.0 * 250.0     # 4 sestertii to the denarius
        elif "rate" in v:
            out[k] = v["rate"] * 2500.0
    return out


ANNUAL_WAGE = _load_annual_wages()


def _load_trade_notes():
    p = json.load(open(PRICES))
    return {k: (v.get("note") or "") for k, v in p["wage_rates_denarii_per_hour"].items()
            if isinstance(v, dict)}


TRADE_NOTES = _load_trade_notes()

# Trades that DO NOT EXIST in a pre-industrial society. The wage table already
# says so, in its own notes, for every one of them ("does not exist yet; you
# must create this trade"), so read it rather than keeping a second list that
# can drift out of step with the first.
TRADES_ABSENT = frozenset(t for t, note in TRADE_NOTES.items()
                          if "does not exist" in note.lower())

# What kind of person a trade is, for the two aggregate pools the tech tree asks
# for. A tester put the objection exactly: "a skilled blacksmith is not a skilled
# writer, but the game treats all as artisans". These are not interchangeable and
# from here on the model does not pretend they are.
TRADE_FAMILY = {
    "scholar": "scholar", "chemist": "scholar", "engineer": "scholar",
    "scribe": "scholar", "merchant": "scholar",
    "labourer": "labour", "miner": "labour", "sailor": "labour",
}   # everything else is a craft: smith, carpenter, mason, glassblower, ...


def trade_family(t):
    return TRADE_FAMILY.get(t, "craft")


# WHAT MONEY IS CALLED WHERE YOU ARE. Every civilisation file has carried a
# `currency` field since the schema was written and not one line of the engine
# ever read it, so an English player in 1300 counted denarii, hired against an
# equestrian census and was quoted for papyrus. The engine's arithmetic is all
# calibrated to Rome 100 AD through price_index, which is a real and defensible
# modelling choice; calling the unit a denarius in Tenochtitlan is not.
#
# The map is from the `currency` field to the form that reads correctly in a
# sentence like "you have 400 ___". A civilisation whose currency is not listed
# falls back to its own field, and then to denarii.
MONEY_WORDS = {
    "denarius": "denarii",
    "sterling penny": "pence",
    "wu zhu cash": "cash",
    "hacksilver by weight": "in hacksilver",
    "cacao bean and cotton cloth": "in cacao beans",
}


# THE SAME WORD IN BOTH FORMS, except for Rome where "den" is the established
# abbreviation and appears throughout the notes. Having a long form and a
# different short form produced sentences like "needs about 1959 pence, you
# have 612 den" - one clause localised from the payload, the next from the
# renderer - which a break tester quite reasonably filed as the currency
# drifting between three names.
MONEY_SHORT_WORDS = {
    "denarius": "den", "sterling penny": "pence", "wu zhu cash": "cash",
    "hacksilver by weight": "hacksilver", "cacao bean and cotton cloth": "beans",
}


def money_word(civ):
    cur = (civ or {}).get("currency") or "denarius"
    return MONEY_WORDS.get(cur, cur)


def money_short(civ):
    """The abbreviation used in compact lines: "400 den", "net +12 den/yr"."""
    cur = (civ or {}).get("currency") or "denarius"
    return MONEY_SHORT_WORDS.get(cur, MONEY_WORDS.get(cur, "den"))


def load_civ(name="rome_100ad"):
    """A civilization is DATA, not code. Swapping Rome for Han China, Viking
    Norway, Mexica Tenochtitlan or somewhere invented is a different file, not a
    different simulator. See data/civilizations/_SCHEMA.md."""
    f = os.path.join(CIVDIR, name + ".json")
    if not os.path.exists(f):
        # "_"-prefixed files are schema and reference data, not playable
        # civilizations - the same convention cli.py applies in both the places
        # it lists this directory, and the one place that did not, which is why
        # a play tester's typo was answered with "available: _TECH_EFFECTS,
        # england_1300, ...".
        have = sorted(x[:-5] for x in os.listdir(CIVDIR)
                      if x.endswith(".json") and not x.startswith("_"))
        raise SystemExit("unknown civilization %r. available: %s" % (name, ", ".join(have)))
    c = json.load(open(f))
    c.setdefault("starting_techs", [])
    c.setdefault("values", {})
    for k, d in (("w_military",0.5),("w_labour_saving",0.0),("w_information",0.0),
                 ("w_novelty",0.0),("w_magic_fear",0.4),("w_religious_rigidity",0.3),
                 ("w_commerce",0.3),("bribability",0.4),("patronage_weight",0.6),
                 ("adaptation_rate",0.10)):
        c["values"].setdefault(k, d)
    return c


def load():
    tree = json.load(open(TREE))
    prices = json.load(open(PRICES))
    nodes = {n["id"]: n for n in tree["nodes"]}
    wages = {k: v["rate"] for k, v in prices["wage_rates_denarii_per_hour"].items()
             if not k.startswith("_")}
    goods = {k: v["p"] for k, v in prices["purchase_prices_denarii"].items()
             if not k.startswith("_")}
    for n in nodes.values():
        n["_labour_cost"] = sum(wages[t] * h for t, h in n["lab"].items())
        n["_material_cost"] = sum(goods[m] * q for m, q in n["mat"].items())
        n["_total_cost"] = n["_labour_cost"] + n["_material_cost"] + n["cap"]
        n["_hired_hours"] = sum(n["lab"].values())
    return tree, prices, nodes, wages, goods


# How many things rest on each node, for the whole tree at once.
#
# The old answer to "what depends on this" was, per node asked about:
#     blocks = {m for m in nodes if k in closure(nodes, m)}
# - a full ancestor closure of every one of 2,831 nodes, every time. That is
# affordable once, on `why`, and completely unaffordable for a table of thirty
# rows, which is why the number a normal-play tester said was the only one that
# decided anything was the one number `available` did not show. They ended up
# scripting 460 separate `why` calls to recover it, and wrote that "competent
# play degenerates into writing a scraper".
#
# So: one reverse-topological pass, descendants held as bitmasks in Python
# integers, computed once per tree and cached. Ordinary set unions would be
# 2,831 sets of up to 2,831 ids; an int OR is the same operation with the
# machine doing the work.
_DESC_CACHE = {}


def descendants(nodes):
    """{id: bitmask of everything downstream of it}, plus the index it uses."""
    key = id(nodes)
    hit = _DESC_CACHE.get(key)
    if hit is not None and hit[0] == len(nodes):
        return hit[1], hit[2]
    index = {k: i for i, k in enumerate(sorted(nodes))}
    kids = {k: [] for k in nodes}
    for m in nodes:
        for p in nodes[m]["pre"]:
            if p in kids:
                kids[p].append(m)
    # Iterative post-order DFS rather than topo_order(): that one rescans every
    # key for every key it pops, which is 8 million comparisons on this tree and
    # three and a half seconds of stall the first time anybody typed
    # "available". A DFS visits each edge once.
    masks = {}
    for root in sorted(nodes):
        if root in masks:
            continue
        stack = [(root, False)]
        while stack:
            k, expanded = stack.pop()
            if expanded:
                m = 0
                for c in kids[k]:
                    m |= (1 << index[c]) | masks.get(c, 0)
                masks[k] = m
                continue
            if k in masks:
                continue
            stack.append((k, True))
            for c in kids[k]:
                if c not in masks:
                    stack.append((c, False))
    _DESC_CACHE[key] = (len(nodes), masks, index)
    return masks, index


def downstream_count(nodes, k):
    """How many nodes are downstream of k. Cheap after the first call."""
    masks, _index = descendants(nodes)
    return bin(masks.get(k, 0)).count("1")


def is_downstream(nodes, k, target):
    """Is `target` downstream of `k`?"""
    masks, index = descendants(nodes)
    if target not in index:
        return False
    return bool(masks.get(k, 0) >> index[target] & 1)


def topo_order(nodes, subset=None):
    """Kahn topological sort. `subset` restricts to a set of ids."""
    keys = set(subset) if subset else set(nodes)
    indeg = {k: 0 for k in keys}
    for k in keys:
        for p in nodes[k]["pre"]:
            if p in keys:
                indeg[k] += 1
    ready = sorted([k for k in keys if indeg[k] == 0])
    out = []
    while ready:
        k = ready.pop(0)
        out.append(k)
        for m in sorted(keys):
            if k in nodes[m]["pre"]:
                indeg[m] -= 1
                if indeg[m] == 0:
                    ready.append(m)
    if len(out) != len(keys):
        raise RuntimeError("cycle detected among: %s" % sorted(keys - set(out)))
    return out


def closure(nodes, goal):
    need, stack = set(), [goal]
    while stack:
        c = stack.pop()
        if c in need:
            continue
        need.add(c)
        stack.extend(nodes[c]["pre"])
    return need


def critical_path(nodes, goal):
    """Longest chain by minimum calendar years plus director-hours at one director.

    Iterative, over a topological order. The recursive version blew the stack once
    the tree passed a thousand nodes, which is a fair warning that this is no
    longer a toy graph.
    """
    need = closure(nodes, goal)
    order = topo_order(nodes, need)
    best = {}
    chain = {}
    for k in order:
        n = nodes[k]
        own = max(n["yrs"], n["ph"] / 2000.0)
        pb, pc = 0.0, []
        for p in n["pre"]:
            if p in best and best[p] > pb:
                pb, pc = best[p], chain[p]
        best[k] = pb + own
        chain[k] = pc + [k]
    return best[goal], chain[goal]


# ----------------------------------------------------------------------------
# Simulation
# ----------------------------------------------------------------------------

STARTING_KITS = {
    "destitute":   {"den": 0,     "desc": "the clothes you stand in. You must earn your first meal."},
    "poor_scholar":{"den": 400,   "desc": "DEFAULT. A few months' subsistence, a knife, a lens, a codex of notes. About what a working teacher has."},
    "artisan":     {"den": 1200,  "desc": "enough to rent a workshop and buy a first set of tools."},
    "merchant":    {"den": 4000,  "desc": "a modest trading capital. You can fund one real venture."},
    "rich_merchant":{"den": 20000,"desc": "wealthy but well under the equestrian census of 100,000."},
    "equestrian":  {"den": 100000,"desc": "the equestrian census exactly. Conspicuous."},
    # "the medians sit inside the noise band" is what this used to claim, and a
    # break tester called it false. They were right, though their measurement
    # (technologies built by year 12: 8 destitute, 51 poor_scholar, 143
    # rich_merchant) was of the OPENING rather than the finish, which is the
    # part money moves most. Measured on the finish as well - Rome, 8 runs a
    # kit, one seed - the median year the transistor is reached runs 476
    # destitute, 489 poor_scholar, 468 rich_merchant, 434 absurd. The first
    # three are inside each other's spread; a million denarii is not. So the
    # claim was true of the middle of the range and false at the top of it,
    # which is exactly the kind of statement that should not be made in one
    # sentence about "the whole kit range".
    "absurd":      {"den": 1000000,"desc": "four senatorial fortunes in unminted gold. It used to make things worse and no longer does: once money can be converted into protection and into sunk mines, wealth helps. What it does NOT do is make you a magician: a million denarii buys perhaps a tenth off the time, not a different game. What money changes most is the OPENING - the first fifty years, where a poor founder is choosing between eating and building."},
}

DEFAULTS = dict(
    # IMMORTALITY IS THE DEFAULT. The point of this simulator is to test the TREE,
    # and a mortality lottery that ends one run in five drowns the signal from the
    # technology in noise about how long one man happened to live. Turn death back
    # on with --mortal when you want to study succession instead of engineering.
    immortal=True,
    founder_life_mean=28.0,
    founder_life_sd=8.0,
    start_year=100,
    # DEFAULT IS A POOR SCHOLAR. Arriving with a noble's fortune is a strange
    # premise and the sweep shows it is also a worse one. Pick a kit with --kit.
    start_capital=400,
    founder_arrival_age=35,
    # 2,000, NOT 2,400. Everyone you HIRE is modelled at HOURS_PER_PERSON_YEAR
    # = 2,000 - "a 10-hour day, 250 days, less feasts" - and the founder was
    # given 2,400, twenty per cent more than a hired man, with no illness, no
    # travel, no administration and no bad weather. There is no story in which
    # the same person-year is worth more hours for you than for the smith you
    # pay. A modern 40-hour week over 52 weeks with no holiday at all is 2,080.
    founder_hours_per_year=2000,
    director_hours_per_year=1800,
    hired_hours_cap_base=25000,   # what a provincial town's labour market can actually supply
    revenue_ramp_years=3,
    suspicion_decay=0.045,
    suspicion_danger=25.0,
    eminence_danger=26.0,
    horizon_years=500,
)

# Known dated shocks. You have foreknowledge of all of these; the model does not
# let you dodge them for free, only mitigate them.
SHOCKS = dict(
    antonine_plague=(165, 180),
    cyprian_plague=(249, 262),
    third_century_crisis=(235, 284),
    debasement_starts=190,
)


