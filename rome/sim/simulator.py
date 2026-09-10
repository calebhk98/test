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

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TREE = os.path.join(ROOT, "data", "tech_tree.json")
PRICES = os.path.join(ROOT, "data", "prices.json")
STRATS = os.path.join(HERE, "strategies")

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


def load_civ(name="rome_100ad"):
    """A civilization is DATA, not code. Swapping Rome for Han China, Viking
    Norway, Mexica Tenochtitlan or somewhere invented is a different file, not a
    different simulator. See data/civilizations/_SCHEMA.md."""
    f = os.path.join(CIVDIR, name + ".json")
    if not os.path.exists(f):
        have = sorted(x[:-5] for x in os.listdir(CIVDIR) if x.endswith(".json"))
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
        own = max(n["yrs"], n["ph"] / 2400.0)
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
    "absurd":      {"den": 1000000,"desc": "four senatorial fortunes in unminted gold. It used to make things worse and no longer does: once money can be converted into protection and into sunk mines, wealth helps. What it does NOT do is make you a magician, and across the whole kit range the medians sit inside the noise band anyway."},
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
    founder_hours_per_year=2400,
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


class Sim:
    def __init__(self, nodes, order, rng, events=True, cfg=None, verbose=False,
                 bounty_set=None, civ=None, manual=False):
        self.nodes = nodes
        self.order = list(order)
        self.rng = rng
        self.events = events
        self.cfg = dict(DEFAULTS, **(cfg or {}))
        self.verbose = verbose
        self.bounty_set = set(bounty_set or ())
        self.civ = civ or load_civ()
        # MANUAL MODE: the optimizer in step() 4b never starts anything on its
        # own. The only projects that ever become active are ones something
        # called start_project() on, i.e. a human or an agent choosing them.
        # See the comment on step() 4b and on start_project() for why this
        # exists: without it, "choosing" a node in `play` was cosmetic.
        self.manual = bool(manual)
        self.w = self.civ["values"]
        # A civilization brings its own date, its own price level and its own
        # capacity to fund things. Norse Scandinavia does not start in 100 AD.
        self.cfg["start_year"] = int(self.civ.get("year", self.cfg["start_year"]))
        self.price_index = float(self.civ.get("price_index", 1.0))
        self.wage_index = float(self.civ.get("wage_index", 1.0))
        self.state_capacity = float(self.civ.get("state_capacity", 0.7))
        self.pop_scale = max(0.05, float(self.civ.get("population", 65e6)) / 65e6)
        self.year = self.cfg["start_year"]
        c = self.cfg
        self.capital = float(c["start_capital"])
        self.done = set()
        self.training = []        # [[artisan_capacity, year_it_matures], ...]
        self.granted = set()      # held because the SOCIETY has it, not because you built it
        self.active = {}          # id -> dict(ph_left, years_elapsed, spent)
        self.failed_attempts = defaultdict(int)
        # YOU ARRIVE ALONE. No employees, no slaves, no household: you stepped
        # out of the future into a street in a city where nobody knows you, and
        # the three artisans the model used to hand you on arrival were never
        # hired by anybody. You are your own only scholar (see
        # effective_scholars) and everyone else has to be found, paid, taught or
        # bought, by you, on purpose.
        self.scholars = 0.0
        self.artisans = 0.0
        self.directors_extra = 0.0
        # Standing staff BY TRADE, which is what makes a smith not a scribe.
        self.employees = {}
        # Trades this society does not have and you have taught into existence.
        self.trades_created = set()
        self.contract_projects = set()   # projects staffed by the job, not by employees
        self.wages_paid = 0.0
        self.contract_hours = {}         # trade -> hours bought this year, by the job
        self.commissioned = {}           # trade -> hours bought this year, cumulative log
        self.teaching_hours_this_year = 0.0
        self.trade_hours_used = {}       # trade -> hours consumed by projects this year
        self.mothballed = set()          # completed works you shut down on purpose
        self.bondage_years_left = 0.0    # years of service still owed for a debt
        self.bondage_debt = 0.0
        self.credit_frozen_until = 0     # year until which nobody will fund new work
        # EVERY AUTOMATIC BEHAVIOUR, IN ONE PLACE, SWITCHABLE.
        #
        # A tester's objection, and the right one: "everything that is automatic
        # should be controllable by players, allowing them to enable/disable
        # that, as well as manually doing it". Each of these was a thing the
        # engine did on its own with no way to stop it and, in several cases, no
        # log line saying it had happened. Defaults differ between the optimizer
        # and a human: the optimizer has to run unattended, so it manages its own
        # household; a player is handed nothing they did not ask for.
        self.policy = {
            "auto_hire":     not manual,   # grow the staff toward what you can support
            # ON for the optimizer, OFF for a player, and that distinction is the
            # whole of what the tester actually objected to. Their complaint was
            # not that the model has slavery, it was that it bought people on
            # THEIR behalf, in a game they were playing by hand, with no prompt
            # and no line in the log. An unattended run of a slave economy that
            # says "bought 6 people for the workshop" in its log is modelling the
            # thing; a player who never typed the command and finds twenty people
            # in their household is being lied to.
            "auto_buy_people": not manual,
            "auto_manumit":  not manual,
            "auto_train":    not manual,   # teach trades this society does not have
            "auto_mine":     not manual,   # sink shafts when a material binds
            "auto_forest":   not manual,   # buy coppice when charcoal binds
            "auto_mothball": True,         # stop working what you cannot pay for
            "auto_shed":     True,         # let go of works that cost more than they return
            "auto_bribe":    not manual,   # pay your way out of a scandal
        }
        self.founder_alive = True
        self.suspicion = 0.0
        self.suspicion_mult = 1.0
        self.gov = 0.0
        self.log = []
        self.dead_reason = None
        self.goal_year = None
        self.money_real = 1.0     # purchasing power of a denarius, 1.0 at 100 AD

        self.economy = 1.0        # size of the imperial economy relative to 100 AD
        self.output_factor = 1.0  # real output, crushed by war and plague, not by debasement
        self.director_hours_spent_founder = 0.0
        self.stalled = 0
        self.last_settlement = -999
        self.bounties_paid = 0
        self.bountied = set()
        self.total_spend = 0.0
        # founder remaining lifespan, elite male already aged 35
        self.life_left = (1e9 if self.cfg["immortal"]
                          else max(5, rng.gauss(self.cfg["founder_life_mean"],
                                                self.cfg["founder_life_sd"])))
        # REPUTATION: your ability to be believed and followed. Distinct from money
        # and from political protection. A man with a great reputation gets his
        # ideas adopted; a man without one gets them ignored however right he is.
        self.reputation = 5.0
        # SCANDAL replaces the old scalar "suspicion". Doing something a society
        # cannot explain is alarming; doing a lot of ordinary things over decades
        # is not. The old model conflated speed with sorcery, which is wrong: the
        # iPhone was astonishing in 2007 and boring by 2012.
        self.scandal = 0.0
        self.eminence = 0.0
        self.familiarity = 0.0      # how used to you the world has become
        self.protection = 0.0       # patrons, office, citizenship, priesthood
        self.bribes_ytd = 0.0
        self.slaves = 0
        self.freedmen = 0
        self.manumitted_total = 0
        self.living_cost_paid = 0.0
        self.atrocity = 0           # counted, never scored as a benefit
        # --- RAW MATERIAL QUANTITIES -------------------------------------
        # Until this existed the model assumed that if a material existed
        # anywhere you had unlimited quantities of it. That was the largest
        # remaining falsehood in the simulation.
        self.res = load_resources()
        # --- GEOGRAPHY: where things are, FOR THE CIVILIZATION IN PLAY -----
        # geography.json used to give every region one Rome-centric `reach`
        # and nothing in this file ever read it. See load_geography() and
        # region_reach()/material_reach() below for the fix: real coordinates,
        # a reach computed from THIS civ's own home ground, and a material
        # cost that follows from it. All of the below depends only on the
        # civ file and the (static) geography file, so it is computed once.
        self.geo = load_geography()
        self._regions = {k: v for k, v in (self.geo.get("regions") or {}).items()
                          if not k.startswith("_")}
        self._home_centroid = self._compute_home_centroid()
        # node id -> located_materials key. Lets material_cost_factor() find
        # the geography entry for a location-gated tech node (mat_gutta_percha,
        # mat_natural_rubber, ...) without the tech tree needing to know
        # anything about geography itself.
        self._mat_unlock = {}
        for mk, md in (self.geo.get("located_materials") or {}).items():
            if mk.startswith("_"):
                continue
            for nid in (md.get("unlocks") or []):
                self._mat_unlock[nid] = mk
        # Mineral market access used to be `self.pop_scale`, i.e. "how much
        # coal can you buy" scaled by HOW MANY PEOPLE YOU HAVE. That is wrong
        # in both directions: Norse Scandinavia got 2.3% of Rome's coal
        # because it has 2.3% of the people, and England in 1300 got 7%,
        # when England is precisely where the coal actually IS. Geology is
        # not demography. See _compute_mineral_scale() for the replacement.
        # It depends only on home_regions and reach, neither of which change
        # during a run, so it is computed once here rather than every year.
        self._mineral_scale = {m: self._compute_mineral_scale(m)
                                for m in ("iron", "coal", "copper", "lead",
                                          "tin", "silver", "saltpetre")}
        self.forest_ha = 0.0        # coppice you own, in hectares
        self.nitre_bed_m2 = 0.0
        self.market_pressure = 0.0  # how hard you have recently leaned on the slave market
        self.mine_capacity = {}     # material -> tonnes/yr of your OWN workings
        self.mine_pending = {}      # sunk but not yet producing
        self.mine_ready = {}        # material -> year it comes on stream
        self.mine_cost_paid = 0.0
        self.shortages = collections.Counter()
        self.throttle = 1.0
        self.binding = None
        # Whatever this civilization already has is free and already done, and it
        # is GRANTED, not earned. A playtester pointed out that these were being
        # counted in done_earned as though the founder had built them, which both
        # flatters the player and, worse, exposed a society's own ancestral
        # crafts to being "forgotten" in a sacking. Han China does not forget how
        # to cast iron because your workshop burned down.
        self.grant_ambient()          # see below: before turn one, not after it
        missing = []
        for k in self.civ.get("starting_techs", []):
            if k in self.nodes:
                self.done.add(k)
                self.granted.add(k)
            else:
                missing.append(k)
        if missing:
            # Loudly. Eight of these were silently dropped across three
            # civilizations, including four of the Mexica's five, so their
            # entire stated identity was fiction that nothing ever reported.
            sys.stderr.write("WARNING: %s lists starting technologies that do not "
                             "exist in the tree and have been ignored: %s\n"
                             % (self.civ.get("id", "?"), ", ".join(missing)))

    # -- helpers ------------------------------------------------------------
    def has(self, k):
        return k in self.done

    # ---- GEOGRAPHY: reach and material cost, FOR THE CIVILIZATION IN PLAY --
    # geography.json used to hard-code one `reach` per region, measured from
    # Italy, and nothing in this file ever read it as a cost: `civs` printed
    # `base_reach` and that was the entire effect either number had. Play Han
    # China and the model still treated Chinese silk as three reach-steps
    # away and Malaya, which Chinese and Malay traders already sail to
    # routinely, as an exotic frontier, while Italy -- a place that
    # civilization has never seen -- was reach 0. That is backwards for
    # every civilization except Rome. Everything below computes reach from
    # the ACTUAL civilization's own home ground instead.

    def _compute_home_centroid(self):
        """Average lat/lon of this civilization's own home_regions.

        A crude centroid, not a capital city, but that matches the rest of
        this model: regions are already coarse political/geographic blocks,
        not points, so a coarse average of them is the right level of detail.
        """
        homes = [r for r in (self.civ.get("home_regions") or []) if r in self._regions]
        if not homes:
            # A civ file with no valid home_regions would otherwise crash
            # region_reach for everyone; falling back to Italy or to
            # whatever region exists keeps this from being a hard wall.
            homes = ["italia"] if "italia" in self._regions else list(self._regions)[:1]
        lat = sum(self._regions[r]["lat"] for r in homes) / len(homes)
        lon = sum(self._regions[r]["lon"] for r in homes) / len(homes)
        return lat, lon

    # Straight-line kilometres (after geography.json's route_difficulty and
    # this civilization's own travel speed, below, have been applied) banded
    # onto the same 0-6 scale reach_levels already uses. Chosen so that
    # ROME, at its own base_reach of 2, lands close to its own OLD
    # hand-authored reach_from_italia numbers across the whole region list
    # (checked by hand while building this): this is a generalisation of the
    # old table, not an unrelated replacement for it.
    RAW_DISTANCE_BANDS = ((1200.0, 1), (2500.0, 2), (4500.0, 3), (7000.0, 4), (11000.0, 5))

    # How much base_reach shortens the EFFECTIVE distance, not the band.
    # An earlier version of this subtracted base_reach straight off the
    # band number, which looked right for Rome but broke on the Norse: with
    # only 6 bands total, subtracting 4 (their base_reach) collapsed nearly
    # every coastal region in the world, China included, to band 1 -- "as
    # easy as sailing to Gaul", which overstates even Norse mobility. Dividing
    # the DISTANCE by a speed factor instead degrades gracefully: closer
    # places still get much easier, but a civilization does not get to treat
    # the far side of the planet as next door no matter how good its ships.
    REACH_SPEED_COEF = 0.22

    def region_reach(self, region_id):
        """How hard `region_id` is to reach, FOR THIS CIVILIZATION, 0-6.

        Three things determine it, none of which the old model had:
          1. HOME IS HOME. If the region is one of this civ's own
             home_regions the reach is 0, full stop, regardless of geometry.
          2. RAW DISTANCE. Great-circle distance from this civ's own home
             centroid to the region's centroid, scaled by route_difficulty
             (ice, open ocean and mountain relay routes are harder than the
             straight line suggests; a scheduled wind system like the
             monsoon is easier).
          3. WHAT YOU ALREADY DO. base_reach is how far this society already
             routinely travels -- the Norse (base_reach 4) really do sail to
             Greenland and the Black Sea, Rome (base_reach 2) really does
             run the India trade every year -- and it SHRINKS that distance
             before banding (see REACH_SPEED_COEF above for why division,
             not subtraction). A society with no ocean-going tradition at
             all still gets base_reach >= 1 in every civ file in this
             directory, so nobody's effective distance is ever left
             un-shrunk.
          Sea vs land matters too: the shrink applies in full to a COASTAL
          destination (this is mostly what "routinely travels" means for
          these five civilizations) and at reduced strength (square root)
          to a landlocked one, because a fleet does not help you cross a
          desert.

        The result is never below 1 for a non-home region: reach 0 is
        reserved for "this is actually your own ground", not for "the
        arithmetic rounded down to nothing."
        """
        if region_id not in self._regions:
            return 6           # unknown region: treat as maximally far, not a crash
        if region_id in (self.civ.get("home_regions") or []):
            return 0
        reg = self._regions[region_id]
        hlat, hlon = self._home_centroid
        dist = haversine_km(hlat, hlon, reg["lat"], reg["lon"]) * float(reg.get("route_difficulty", 1.0))
        base_reach = float(self.civ.get("base_reach", 2))
        speed = 1.0 + self.REACH_SPEED_COEF * base_reach
        coastal = bool(reg.get("coastal", True))
        effective = dist / speed if coastal else dist / (speed ** 0.5)
        band = 6
        for edge, b in self.RAW_DISTANCE_BANDS:
            if effective <= edge:
                band = b
                break
        return max(1, min(6, band))

    # How much of a region's output reaches your market by ordinary trade
    # when you do NOT hold the region yourself, fading with reach rather
    # than cutting off: nothing in this model is a wall, only a price.
    TRADE_ACCESS_BY_REACH = {0: 1.0, 1: 0.5, 2: 0.3, 3: 0.15, 4: 0.08, 5: 0.04, 6: 0.02}

    def material_reach(self, material_key):
        """Reach and cost multiplier for `material_key`, FOR THIS CIVILIZATION.

        Looks the material up in geography.json's located_materials, picks
        whichever of its regions is EASIEST for this civ to reach (a rational
        buyer sources from the nearest deposit, not always the "primary"
        one), and turns that region's reach into a cost multiplier.

        The published cost_multiplier in geography.json was written for
        Rome: it is calibrated against that region's reach_from_italia, the
        old Roman-only reach number. So: at civ_reach 0 (you live there) the
        multiplier is 1, at civ_reach == reach_from_italia it reproduces the
        published number exactly (which is why Rome's own numbers barely
        move), and at civ_reach below reach_from_italia -- Han China and
        Malayan gutta percha is the case this bug report was written about
        -- it comes out CHEAPER than Rome pays, because the material
        genuinely is closer for that civilization. Above reach_from_italia
        it costs MORE than Rome's figure, for the same reason in reverse.
        Power, not a straight line, so it is smooth at both ends and never
        goes negative or hits exactly zero.
        """
        materials = self.geo.get("located_materials") or {}
        md = materials.get(material_key)
        if not md:
            return 0, 1.0
        base_mult = float(md.get("cost_multiplier", 1.0))
        best = None
        for rid in (md.get("regions") or []):
            reg = self._regions.get(rid)
            if not reg:
                continue
            civ_r = self.region_reach(rid)
            if best is None or civ_r < best[0]:
                italia_r = max(1, int(reg.get("reach_from_italia", civ_r) or 1))
                best = (civ_r, italia_r)
        if best is None:
            return 0, base_mult
        civ_r, italia_r = best
        if civ_r <= 0:
            return 0, 1.0      # it is, in effect, home ground for this civilization
        raw = base_mult ** (civ_r / italia_r)
        # Cap it. The exponent could reach x235 for gutta percha and x468 for
        # rubber, and a several-hundred-fold cost is not an expense, it is the
        # abolished "unobtainable" category wearing a price tag. The ceiling is
        # argued from the Roman evidence rather than chosen for feel: pepper
        # carried roughly a tenfold to twentyfold markup and silk about a
        # hundredfold, both RETAIL across a chain of middlemen. This node buys
        # your OWN supply, which should cost less per unit than retail, not
        # more. 60 is therefore generous rather than punitive, which is the
        # right way to be wrong here.
        # Compress rather than clamp. A hard ceiling flattened the very
        # distinction this function exists to draw: Rome's 235 and Han China's
        # 60 both hit a cap of 60 and came out identical, so the geography fix
        # stopped doing anything. Raising to a fractional power keeps the
        # ORDERING intact while pulling the magnitudes back to something
        # defensible, and the ceiling stays only as a backstop.
        return civ_r, min(raw ** 0.6, 45.0)

    def material_cost_factor(self, k):
        """Cost multiplier a located-material tech node picks up from
        geography, for the civilization in play.

        Only applies to nodes geography.json actually names (via
        located_materials.*.unlocks, e.g. mat_gutta_percha, mat_natural_rubber):
        everything else returns 1.0 and is untouched. This is the wiring the
        bug report asked for: before this existed, geography.json's
        cost_multiplier field was read by nobody, so gutta percha cost
        exactly the same (nothing extra) whether you were playing Rome or
        Han China, and the entire India-and-east trade advantage a
        China-based civilization actually has was invisible to the model.
        """
        mk = self._mat_unlock.get(k)
        if not mk:
            return 1.0
        _, mult = self.material_reach(mk)
        return mult

    def _compute_mineral_scale(self, material):
        """Fraction of a mined mineral's reference output this civilization
        can draw on: geology and reach, not population.

        resource_throttle() used to multiply by self.pop_scale here, i.e.
        "how much coal can you buy" scaled by HOW MANY PEOPLE YOU HAVE. That
        is backwards twice over: Norse Scandinavia got 2.3% of Rome's coal
        because it has 2.3% of the people, and England in 1300 got 7%, when
        England is precisely where the coal actually is. A coalfield does
        not care how many people live near it.

        geography.json's per-region `minerals` gives each region's rough
        share of a material's total output, normalised so ROME'S OWN home
        regions sum to about 1.0 -- which is what reproduces
        resources.json's Roman totals exactly for a Rome-based civ and
        changes nothing about the Rome baseline. For any other civilization:
        regions it actually HOLDS (home_regions) count in full, and every
        other region contributes a SHRINKING but never-zero share as it
        fades with reach (TRADE_ACCESS_BY_REACH), because a civilization
        with no local ore can still buy imported metal, just less of it.
        Floored well above zero so this is a price, never a wall.
        """
        home = set(self.civ.get("home_regions") or [])
        total = 0.0
        for rid, reg in self._regions.items():
            ab = float((reg.get("minerals") or {}).get(material, 0.0))
            if ab <= 0:
                continue
            if rid in home:
                total += ab
            else:
                total += ab * self.TRADE_ACCESS_BY_REACH.get(self.region_reach(rid), 0.02)
        return max(0.05, total)

    def mineral_scale(self, material):
        """Cached result of _compute_mineral_scale(). Geology and reach do
        not change during a run, so this is computed once in __init__
        rather than recomputed every simulated year."""
        return self._mineral_scale.get(material, self.pop_scale)

    def director_pool(self):
        h = 0.0
        if self.founder_alive:
            own = self.cfg["founder_hours_per_year"]
            # In bondage most of your hours are owed to somebody else. Not all
            # of them: nobody worked every waking hour, and the evenings are
            # where the work gets done. This is the cost, and it is temporary.
            if self.bondage_years_left > 0:
                own *= 0.25
            h += own
        h += self.directors_extra * self.cfg["director_hours_per_year"]
        return h

    def staff_capacity(self):
        """How many trained people the institution can support.

        Ceilings, not rates. You cannot teach faster than you can feed, house and
        supervise, and you cannot supervise more than your directors can reach.
        Funding matters: an institute whose income has collapsed sheds people.
        """
        # There is no floor here any more. Rome does have excellent craftsmen for
        # hire and they are reachable through market_supply() and `hire`, which
        # is a thing you do rather than a staff of four you are handed on
        # arrival and never asked for.
        base_sc, base_ar = 0.0, 0.0
        sc = ar = di = 0.0
        if self.has("workshop_first"):     ar += 6
        if self.has("freedman_staff"):     ar += 10
        if self.has("school_founded"):     sc += 12; ar += 12; di += 2.0
        if self.has("collegium_licensed"): sc += 3
        if self.has("patron_senatorial"):  sc += 4;  ar += 6
        if self.has("patron_imperial"):    sc += 14; ar += 50; di += 2.0
        if self.has("endowment_land"):     sc += 6;  ar += 8;  di += 1.0
        if self.has("academy_network"):    sc += 40; ar += 50; di += 6.0
        if self.has("corpus_dispersed"):   sc += 8;  di += 1.0   # people teach themselves from your books
        # Industrialisation compounds: each heavy node trains the workforce that
        # makes the next one possible. This is the engine of the late game.
        if self.has("interchangeable_parts"): ar += 40; sc += 4
        if self.has("crucible_steel"):     ar += 12
        if self.has("blast_furnace"):      ar += 15
        if self.has("telegraph_electric"): ar += 25; sc += 6
        if self.has("steam_high_pressure"):ar += 45
        if self.has("bessemer_openhearth"):ar += 65; sc += 6
        if self.has("railway"):            ar += 95; sc += 8
        if self.has("power_grid"):         sc += 45; ar += 130; di += 6.0
        # you cannot keep staff you cannot pay
        # a famous school attracts students and patrons it did not have to pay for
        # WAGES ARE A REAL CHARGE NOW (see wage_bill), so this ceiling is no
        # longer "what you could pay for": it is what you can pay for WITHOUT
        # eating the surplus you need in order to build anything. The first
        # version of the explicit wage bill hired to the old affordability
        # ceiling and the household then consumed the entire surplus: revenue
        # 32,000, upkeep 17,000, wages 12,000, and exactly nothing left to spend
        # on the work, for two centuries. A programme whose payroll is its whole
        # income is not a programme.
        #
        # SPARE USED TO BE revenue() MINUS UPKEEP() ALONE, which is the upkeep of
        # BUILT WORKS and says nothing about living_cost - rent, appearances, tax
        # and (via wage_bill) the staff you ALREADY carry. On turn one, with 400
        # denarii, 232/yr of income and a 230/yr household, that left "spare"
        # reading a healthy 267 while the true surplus was 3.5. auto_hire spent
        # against the healthy number, not the true one. Subtracting living_cost
        # here is what "what you can pay for" has to mean if it is to mean
        # anything: money already going to rent and to people you already
        # employ is not there to hire more people with.
        spare = max(0.0, (self.revenue() - self.upkeep() - self.living_cost())
                    * self.rep_factor() + max(0.0, self.capital) * 0.06)
        budget = spare * 0.40
        afford = budget / (420.0 * self.price_index * self.wage_index)
        # EXTRA is supervision_room(), the headroom auto_hire adds on top of
        # this institutional ceiling (see step(), section 1). It used to be
        # added with no affordability check of its own at all - this ceiling's
        # `scale` only ever throttled sc/ar, which are BOTH ZERO before you
        # have built a workshop or a school, so the extra six-person headroom
        # went through at full strength regardless of income. A tester's turn
        # one hired 1.32 artisans and 0.38 scholars on 400 denarii and a net
        # income of 3.5/yr, taking living cost to 699.9 and capital to -688.
        # Folding extra into the SAME denominator this ceiling is scaled
        # against is what makes "grow the staff toward what you can house and
        # pay" true of the headroom hiring and not just the institutional kind.
        extra = self.supervision_room()
        scale = max(0.10, min(1.0, afford / max(1.0, sc + ar + extra * 1.35)))
        self._staff_scale = scale     # step() applies this to `extra` too
        # A civilization of 1.5 million simply cannot field the trained people a
        # civilization of 65 million can, however rich you are. This is the single
        # biggest structural difference between playing Rome and playing Norway.
        # Softened after a first pass made every small civilization fail outright.
        # A 4.5 million person society CAN eventually staff a semiconductor
        # programme, it just has to grow into it. Making that impossible was a
        # modelling error, not a finding.
        pop = 0.45 + 0.55 * min(1.0, self.pop_scale ** 0.35)
        return (base_sc + sc * scale * pop, base_ar + ar * scale * pop,
                di * min(1.0, scale * 1.3) * pop)

    def supervision_room(self):
        """People you can direct and pay BEYOND what your institutions train.

        staff_capacity is a ceiling on what a school, a workshop and a patron
        produce and support. It is not a ceiling on how many men you can hire
        off the street, which is limited by money and by the market. Conflating
        the two put a hard wall across the Norse run: it needed thirty craftsmen
        for interchangeable parts against an institutional ceiling of 27.6, and
        a society of a million and a half could never cross the gap however rich
        it got. The old model cleared it by handing every founder four artisans
        on arrival, which is the thing a tester objected to and which I removed;
        this is the honest version of the same headroom. You hire them, you pay
        them every year, and you can only supervise so many.
        """
        room = 6.0 + 14.0 * self.directors_extra
        if self.has("workshop_first"):  room += 6.0
        if self.has("school_founded"):  room += 10.0
        if self.has("academy_network"): room += 30.0
        return room

    def hired_cap(self):
        # a civilization of 1.5 million cannot staff what one of 65 million can
        cap = self.cfg["hired_hours_cap_base"] * (0.25 + 0.75 * min(1.0, self.pop_scale))
        if self.has("school_founded"):    cap *= 2.0
        if self.has("freedman_staff"):    cap *= 1.5
        if self.has("patron_imperial"):   cap *= 3.0
        if self.has("academy_network"):   cap *= 2.5
        if self.has("interchangeable_parts"): cap *= 1.5
        return cap

    # ---- how a SOCIETY reacts to a TECHNOLOGY -------------------------------
    STATE_WEIGHTS = {"infrastructure":0.5, "food":0.7, "medical":0.5,
                     "luxury":0.1, "spectacle":0.1, "inexplicable":0.0,
                     "status_threatening":-0.6, "weapon_democratising":-0.5}

    def state_interest(self, n):
        w = self.w
        m = dict(self.STATE_WEIGHTS)
        m.update({"military": w["w_military"], "labour_saving": w["w_labour_saving"],
                  "information": w["w_information"], "commerce": w["w_commerce"],
                  "religious_adjacent": -0.9 * w["w_religious_rigidity"]})
        return sum(m.get(t, 0.0) for t in n.get("traits", []))

    def alarm_of(self, n):
        """How alarming this technology is TO THIS CIVILIZATION, before defences.

        Note what is NOT in here: speed, and money. Building fast does not make
        you a sorcerer. Producing an effect a society has no category for does.
        """
        w = self.w
        a = 0.0
        for t in n.get("traits", []):
            if   t == "inexplicable":        a += 10.0 * w["w_magic_fear"]
            elif t == "spectacle":           a += 4.0  * w["w_magic_fear"]
            elif t == "religious_adjacent":  a += 9.0  * w["w_religious_rigidity"]
            elif t == "status_threatening":  a += 5.0
            elif t == "weapon_democratising":a += 6.0
            elif t == "labour_saving":       a += 4.0  * max(0.0, -w["w_labour_saving"])
        a *= (1.0 + max(0.0, -w["w_novelty"]))
        a *= max(0.12, 1.0 - self.familiarity)      # people habituate, fast
        a *= max(0.15, 1.0 - self.protection)       # patrons, office, money
        return a

    def update_protection(self):
        """Standing, office and MONEY all protect. The old model had money only
        endangering you, which is backwards: wealth buys advocates, priesthoods,
        magistracies and, in a society with a bribability of 0.55, verdicts."""
        p = 0.0
        w = self.w
        if self.has("patron_local"):        p += 0.18 * w["patronage_weight"]
        if self.has("patron_senatorial"):   p += 0.26 * w["patronage_weight"]
        if self.has("patron_imperial"):     p += 0.32 * w["patronage_weight"]
        if self.has("citizenship"):         p += 0.10
        if self.has("collegium_licensed"):  p += 0.10
        if self.has("endowment_land"):      p += 0.08   # conspicuous benefaction
        if self.has("fin_university") or self.has("school_founded"): p += 0.06
        p += min(0.30, self.reputation / 260.0)
        # BRIBERY, ADVOCACY AND PIETY: an explicit, spendable defence.
        income = max(1.0, self.revenue())
        p += min(0.30, (self.bribes_ytd / (income * 0.6)) * w["bribability"])
        self.protection = min(0.92, p)

    def prominence_hazard(self):
        """Eminence is its own hazard, and protection does NOT reduce it.

        The model had a defect that only showed once the tree got big: every
        defence saturates. Protection caps at 0.92, familiarity decays alarm to
        a tenth, reputation sits at 97 out of 100 by the second century, and the
        result was 200 successful runs out of 200. Nothing could touch you.

        What was missing is that in an autocracy prominence is not only a shield,
        it is a target, and the people who protect you are the people who destroy
        you when you outgrow them. Sejanus was the most protected man in Rome
        until the morning he was not. Seneca was the emperor's own tutor. Thrasea
        Paetus was merely admired. None of them was brought down by a mob or by a
        magic charge; they were brought down by being too eminent in a system
        with one man at the top.

        So this rises with reputation and with visible wealth, it is multiplied
        by having got close to the throne, and no amount of patronage reduces it.
        It feeds scandal rather than killing you outright, because the usual
        outcome is a bad year, a confiscation or a lost patron, not a death.
        """
        w = self.w
        rep = max(0.0, self.reputation) / 100.0
        wealth = min(1.0, max(0.0, self.capital) / 250000.0)
        h = 2.2 * w.get("w_eminence_danger", 0.5) * (0.70 * rep * rep + 0.30 * wealth)
        if self.has("patron_imperial"):
            h *= 1.5          # nearest the throne, most exposed to its turnover
        # A wide, dispersed institution is harder to destroy than one great man.
        if self.has("academy_network"):
            h *= 0.65
        return h

    # The FIRST answer to "I have no staff" is now the obvious one, which the
    # model did not have until this round: hire somebody. A tester spent five
    # hundred years with one scholar, built five separate institution nodes
    # hoping one of them would help, and wrote "if there's a way to grow
    # scholars, I never found it" - because there was not one, short of an
    # institution costing thousands.
    STAFF_SOURCES = {
        "scholars": [("HIRE", "{\"cmd\":\"hire\",\"trade\":\"scholar\",\"n\":2} "
                              "hires literate men by the year; see {\"cmd\":\"labour\"}"),
                     ("school_founded", "the school produces scholars in quantity, and "
                                        "grants more every year it runs"),
                     ("academy_network", "three academies produce more than one school"),
                     ("collegium_licensed", "required before the school is legal")],
        "artisans": [("HIRE", "{\"cmd\":\"hire\",\"trade\":\"smith\",\"n\":3} or any "
                              "trade in {\"cmd\":\"labour\"}; or "
                              "{\"cmd\":\"commission\",\"trade\":\"smith\",\"hours\":400} "
                              "to buy one job instead of employing anybody"),
                     ("freedman_staff", "buy, teach and free a technical staff"),
                     ("workshop_first", "you need somewhere for them to work"),
                     ("BUY", "{\"cmd\":\"buy\",\"what\":\"slaves\",\"n\":N} then "
                             "manumit, though they are untrained for three years")],
    }

    def _staff_advice(self, kind):
        """Name the remedy, not just the shortfall - and only remedies you could
        actually have heard of.

        This advice told a tester to "build workshop_first" for ten years while
        `why workshop_first` replied "you have never heard of that", from the
        same program in the same second. They called it the single most confusing
        thing in the game and they were right. Hiring is always sayable, because
        the labour market is in front of you; a named institution is not, until
        it is.
        """
        bits = []
        for node, why in self.STAFF_SOURCES.get(kind, []):
            if node in ("BUY", "HIRE"):
                bits.append(why)
            elif node not in self.done and self.is_visible(node):
                bits.append("build %s (%s)" % (node, why))
        if not bits:
            return "wait: your existing institutions add %s each year." % kind
        return "To get more %s: %s." % (kind, "; ".join(bits[:3]))

    def apply_tech_effects(self, k):
        """Building something changes what this society is like.

        _TECH_EFFECTS.json was written, committed with a description of what it
        would do, and never referenced by any code. Printing raised nobody's
        literacy; the scientific method reduced nobody's fear of the
        inexplicable. The whole argument for teaching and printing early is that
        they change people, and the model quietly did not implement it.
        """
        eff = TECH_EFFECTS.get(k)
        if not eff:
            return
        changed = []
        for field, delta in eff.items():
            if field.startswith("_") or not isinstance(delta, (int, float)):
                continue
            if field in self.w:
                before = self.w[field]
                self.w[field] = max(-1.0, min(1.5, before + delta))
                changed.append(field)
            elif field in ("literacy_general", "literacy_elite", "state_capacity"):
                before = float(self.civ.get(field, 0.0))
                self.civ[field] = max(0.0, min(1.0, before + delta))
                if field == "state_capacity":
                    self.state_capacity = self.civ[field]
                changed.append(field)
        if changed:
            self.log.append((self.year, "%s changes the society: %s"
                             % (self.nodes[k]["name"], ", ".join(sorted(changed)))))

    # FOG OF WAR. Without it the player sees the entire tree from the first
    # minute, including exactly what a transistor needs, which is both a spoiler
    # and a lie about what knowing something feels like. With fog on you see
    # what you have built in full, what you could start next as a one line
    # summary, and nothing at all about where any of it leads.
    def reveal_from(self, k):
        """Completing something teaches you what it leads towards, vaguely."""
        if not getattr(self, "fog", False):
            return
        self.revealed = set(getattr(self, "revealed", set()))
        self.revealed.add(k)
        for other, n in self.nodes.items():
            if k in n.get("pre", []):
                self.revealed.add(other)
            for g in n.get("req_any", []):
                if k in (g.get("options") or {}):
                    self.revealed.add(other)

    def is_visible(self, k, _memo=None):
        """Can the player see this node at all?

        _memo: an optional dict shared across one recursive descent. is_visible
        calls start_reason, and start_reason calls is_visible on every missing
        prerequisite of a node with missing prerequisites - which, on a node
        deep in the tree, is every one of ITS missing prerequisites too. Without
        sharing one memo down that whole call tree, checking visibility of a
        single deep node re-derived the visibility of common ancestors once per
        path to them, which is exponential in the depth of the tree. A profiler
        on `can_start('dynamo')` on norse_900ad under fog counted 12,465 nested
        calls to start_reason from three top-level ones, at 0.45s each; a plain
        `available` call, which checks all ~2,800 nodes this way, did not return
        in 60 seconds. The memo makes one recursive descent O(nodes touched)
        instead of O(paths to them); a fresh dict per outward-facing call (the
        default) keeps it exact - nothing here is cached ACROSS commands, so a
        node built or revealed between one call and the next is seen correctly
        next time.
        """
        if not getattr(self, "fog", False):
            return True
        if k in self.done or k in self.active:
            return True
        if k in getattr(self, "revealed", set()):
            return True
        memo = {} if _memo is None else _memo
        if k in memo:
            return memo[k]
        memo[k] = False        # provisional: the tree is a DAG so this should
                                # never actually be read back, but a cycle must
                                # not recurse forever if one ever sneaks in.
        # anything you could start right now is visible by definition: you can
        # see the work in front of you even if you cannot see past it
        result = self.start_reason(k, _memo=memo)[0]
        memo[k] = result
        return result

    def fog_scrub(self, text):
        """Strip node ids the player has not discovered out of a message."""
        if not text or not getattr(self, "fog", False):
            return text
        out = text
        for k in self.nodes:
            if k in out and not self.is_visible(k):
                out = out.replace(k, "something you have not heard of")
        return out

    def fog_summary(self, k):
        """One sentence. Deliberately not the whole note, and never the unlocks."""
        note = (self.nodes[k].get("note") or "").strip()
        if not note:
            return self.nodes[k]["name"]
        for sep in (". ", "? ", "! "):
            if sep in note:
                note = note.split(sep)[0].strip() + "."
                break
        # Hard cap. A "one sentence" summary that runs to 160 characters, times
        # thirty entries in a list, is most of the reply.
        return note if len(note) <= 110 else note[:107].rstrip(" ,;") + "..."

    def knowledge_risk(self):
        """How exposed your finished work is to being forgotten, and to what.

        A playtester read the guide's warning about the Third Century Crisis,
        then reasonably decided to skip the academies because `path` told them,
        correctly, that no academy is a technical prerequisite of a transistor.
        They then lost 25 technologies in one year, 24 more nine years later,
        and 16 more after that, and rebuilt them while the goal stood still.

        Their complaint is the sharp one: this project's whole thesis is that
        the technical dependency graph is not the real dependency graph, and
        the protocol was exposing only the technical graph. The risk existed
        solely as prose, in a knowledge file, attached to the MITIGATION rather
        than to anything the player could see while deciding. A tool that shows
        you one graph while the guide insists a second one governs you is a tool
        that misleads by omission.

        So the numbers behind the dice are now readable while there is still
        time to act on them.
        """
        if self.has("corpus_dispersed"):   chance, frac, hedge = 0.12, 0.08, "corpus_dispersed"
        elif self.has("corpus_written"):   chance, frac, hedge = 0.45, 0.22, "corpus_written"
        else:                              chance, frac, hedge = 0.80, 0.40, None
        at_risk = sum(1 for k in self.done if self.nodes[k]["tier"] >= 2)
        upcoming = []
        for h in (self.civ.get("hazards") or []):
            yrs = h.get("years") or []
            if not yrs:
                continue
            y0 = yrs[0]
            y1 = yrs[1] if len(yrs) > 1 else yrs[0]
            if self.year > y1:
                continue                      # already survived, or missed
            row = {"name": h.get("name", "hazard"),
                   "years": [y0, y1],
                   "in_progress": y0 <= self.year <= y1,
                   "sacks_a_site": bool(h.get("sack_chance")),
                   "sack_chance_per_year": h.get("sack_chance"),
                   "staff_loss": h.get("staff_loss"),
                   "note": h.get("note")}
            # WHAT YOU CAN DO ABOUT IT. Every hazard here is fightable, and
            # until now nothing said so: testers watched the plague arrive on
            # the year they were told it would and treated it as weather.
            row["what_you_can_do"] = {}
            for kind in ("staff_loss", "sack_chance", "output_factor", "real_erosion"):
                if kind in h or (kind == "sack_chance" and h.get("sack_chance")):
                    row["what_you_can_do"][kind] = self.hazard_advice(kind)
            if "sack_chance" in h:
                row["sack_chance_after_what_you_have_built"] = round(
                    h["sack_chance"] * self.hazard_relief("sack_chance")[0], 4)
            if "staff_loss" in h:
                row["staff_loss_after_what_you_have_built"] = round(
                    h["staff_loss"] * self.hazard_relief("staff_loss")[0], 4)
            upcoming.append(row)
        # Norse hazards do not sack anything, and a playtester watched this
        # advertise a loss risk and recommend a hedge for a full 500 year run in
        # which no sacking could ever occur. Risk you cannot face is not risk.
        can_be_sacked = any(h.get("sacks_a_site") for h in upcoming)
        if not can_be_sacked:
            return {
                "technologies_at_risk": at_risk,
                "loss_chance_if_a_site_is_sacked": round(chance, 2),
                "fraction_lost_when_it_happens": round(frac, 2),
                "expected_technologies_lost_per_sacking": 0.0,
                "hedged_by": hedge,
                "better_hedge_available": None,
                "note": "no remaining hazard for this civilization sacks a site, "
                        "so nothing here is currently at risk of being forgotten",
                "known_hazards_ahead": upcoming,
            }
        return {
            "technologies_at_risk": at_risk,
            "loss_chance_if_a_site_is_sacked": round(chance, 2),
            "fraction_lost_when_it_happens": round(frac, 2),
            "expected_technologies_lost_per_sacking": round(at_risk * chance * frac, 1),
            # Under fog, do not name a node the player has not discovered. A
            # tester was told in `state` that corpus_dispersed would hedge them,
            # asked `why` about it, and was told they had never heard of it.
            # Both replies came from the same program in the same second.
            "hedged_by": hedge if (not getattr(self, "fog", False)
                                   or self.is_visible(hedge or "")) else "nothing yet",
            "better_hedge_available": (
                None if hedge == "corpus_dispersed" else
                ("corpus_dispersed" if not getattr(self, "fog", False)
                 else "there is said to be a way to guard against this; "
                      "you have not found it yet")),
            "known_hazards_ahead": upcoming,
        }

    # Institutions that belong to one named society. Granting them to everyone
    # was the bug; refusing to let anyone else BUILD them would be a worse one,
    # because a founder can perfectly well introduce an aqueduct to Tenochtitlan.
    # This only blocks the free gift.
    # Standing, knowledge and persona are not plant. They carry upkeep because
    # they cost you to maintain, and they cannot be let go to save money the way
    # a mill or a mine can. A playtester went bankrupt and the abandonment
    # mechanic shed `identity_cover`, which is a persona AND a real prerequisite
    # of the goal, and they sat softlocked for 470 years unable to rebuild it.
    # Knowledge cannot be repossessed. Everything else can lapse.
    #
    # This started as a broad category list, added to stop bankruptcy shedding
    # `identity_cover` and softlocking the run. It then caused the opposite
    # problem: it protected patron_local, collegium_licensed, freedman_staff and
    # workshop_first, which between them carried 3,380 denarii of upkeep against
    # 1,501 of revenue, so a ruined run could never stop bleeding and recovery
    # took centuries. Both of those are real. A patronage can lapse and a
    # workshop can close; what you cannot lose is who you are and what you know.
    #
    # A tester watched creditors make the founder forget Newton's laws
    # (sc2_physics_newtons_laws, cat "physics", up 40) - already covered above
    # - and separately watched abstract science and medicine outside pure
    # mathematics go the same way: cell theory, DNA, the phase diagram of
    # iron, none of them a building, all of them carrying real upkeep (40 to
    # 400 denarii, from "keeping up scholarly correspondence" rather than rent)
    # and so all of them ELIGIBLE under the up-exceeds-revenue test that gates
    # both shed_loss_makers and enforce_credit_limit's seizure. "theory" and
    # "knowledge" are what the tree itself calls these categories, which is
    # the same evidence "physics" and "mathematics" were added on: you cannot
    # be made to un-know a thing to balance a ledger, whatever it is filed
    # under. NARROW ON PURPOSE, same lesson as FOREIGN_MARKERS below: most
    # knowledge (tex_drop_spindle, "basic textile technique", among it) costs
    # nothing to keep and was never at risk, needing no protection here at
    # all - see the note on that in never_abandon's caller. This list is only
    # for the knowledge that DOES carry upkeep and would otherwise be shed for
    # it.
    NEVER_ABANDON = {"mathematics", "physics", "method", "notation",
                     "algebra", "geometry", "probability", "analysis",
                     "theory", "knowledge"}

    def never_abandon(self, k):
        """Protected: knowledge, and anything the goal actually needs.

        Keying the softlock guard on the GOAL CLOSURE rather than on a list of
        category names is what makes both halves work. You can let a patron go
        and rebuild him later; you cannot have the game quietly delete a step
        you need and then refuse to fund rebuilding it.
        """
        if self.nodes[k]["cat"] in self.NEVER_ABANDON:
            return True
        if not hasattr(self, "_goal_closure"):
            try:
                self._goal_closure = closure(self.nodes, self.goal)
            except Exception:
                self._goal_closure = set()
        return k in self._goal_closure

    FOREIGN_MARKERS = ("_roman", "_rome", "annona", "insula", "societas",
                       "collegium", "argentarii", "latifundi")

    # A Roman masonry arch is a way of laying stone and anyone can learn it. The
    # annona is the Roman state's grain dole and Roman citizenship is a status
    # only Rome can confer, and neither is a thing you can BUILD in Luoyang.
    # A tester played five hundred years of Han China with `citizenship`
    # ("the difference between a governor executing you and Rome hearing you")
    # sitting in their available list the whole time, and called it what it was:
    # unfinished civilization gating rather than a deliberate choice.
    # NARROW, and I made this too wide first time and broke Han China with it.
    # Blocking anything with "collegium" in the name cut the licensed
    # association out of the tree, and with it school_founded, endowment_land,
    # academy_network and both patronage tiers, which is the entire
    # institutional ladder: Han finished 156 of the 168 nodes the transistor
    # needs and then failed for want of eighteen craftsmen it had 320 million
    # denarii to hire. Every society has partnerships, money-lenders and
    # licensed associations under its own names, and the Han even had a grain
    # stabilisation office. What no other society has is Roman citizenship,
    # because only Rome can confer it. That is the whole list.
    # And in the end the list is empty, which is the right answer. My first
    # version blocked six markers and cut Han China off from the whole
    # institutional ladder. Narrowing it to Roman citizenship alone moved the
    # wall one node back, because the licensed association requires legal
    # standing, and a model in which only Romans can have legal standing is
    # worse than the flavour-text problem it was fixing. `citizenship` is now
    # what it always modelled - a status the courts will hear - and every
    # society has one under its own name. What remains civ-specific is which
    # institutions you are GRANTED for free, which FOREIGN_MARKERS still
    # handles: the Han are not handed the annona.
    FOREIGN_INSTITUTIONS = ()

    def _is_foreign_institution(self, k):
        if self.civ.get("id") == "rome_100ad":
            return False
        hay = (k + " " + self.nodes[k].get("name", "")).lower()
        return any(m in hay for m in self.FOREIGN_MARKERS)

    def _is_foreign_only(self, k):
        """A legal or civic institution of a society that is not this one."""
        if self.civ.get("id") == "rome_100ad":
            return False
        hay = (k + " " + self.nodes[k].get("name", "")).lower()
        return any(m in hay for m in self.FOREIGN_INSTITUTIONS)

    def civ_cost_factor(self, k):
        """What this society is unusually good or bad at building.

        Until now every civilization built every node at the same real cost and
        differed only in population, prices, values and reach. That misses the
        most important thing about them. The Mexica are not a small Rome: there
        is no domesticable draught animal anywhere in Mesoamerica, so every load
        moves on a human back, and that is a permanent fact about the continent
        rather than something the founder can teach away. The Norse build the
        best ships in Europe and cannot organise a public works programme. Han
        China already has cast iron, paper and the blast furnace.

        A factor above 1 means this society finds that domain harder than Rome
        does; below 1, easier. It is deliberately a small table in the civ file
        rather than logic in here, so a new civilization is data.
        """
        mults = self.civ.get("cost_multipliers") or {}
        if not mults:
            return 1.0
        # A remedy lifts a handicap once you have built the thing that answers
        # it. This was written into every civilization file and then never wired
        # into the code at all: a playtester built collegium_licensed, watched
        # the public-works multiplier sit unchanged at 1.53, and went and read
        # the source to find that `handicap_remedies` is referenced nowhere.
        # They were right. The feature existed only as data and as a claim in a
        # commit message.
        rem = self.civ.get("handicap_remedies") or {}
        n = self.nodes[k]
        f = 1.0
        for key in (n.get("cat"), ) + tuple(n.get("traits") or ()):
            if key not in mults:
                continue
            m = float(mults[key])
            r = rem.get(key)
            if isinstance(r, dict) and r.get("node") in self.done:
                m = float(r.get("residual", 1.0))
            f *= m
        return f

    def standing_floor(self):
        """The reputation you keep for what you have built, whatever else happens.

        Novelty fades. A corpus in three libraries, a school with students and a
        senator who will receive you do not.
        """
        earned = len(self.done) - len(self.granted)
        f = 0.5 + 0.55 * math.sqrt(max(0, earned))
        if self.has("corpus_written"):     f += 3.0
        if self.has("corpus_dispersed"):   f += 6.0
        if self.has("school_founded"):     f += 4.0
        if self.has("academy_network"):    f += 10.0
        if self.has("patron_senatorial"):  f += 3.0
        if self.has("patron_imperial"):    f += 8.0
        if self.has("identity_cover"):     f += 1.0
        # Scandal is the one thing that eats into standing rather than sitting
        # alongside it: being notorious is not the same as being unknown.
        return max(0.0, f - 0.5 * self.scandal)

    def rep_factor(self):
        """How much easier reputation makes everything. 1.0 at zero reputation."""
        return 1.0 + self.reputation / 120.0

    def economy_index(self):
        """Diffused technology enriches the whole Empire, not only your workshop.

        Britain's industrialisation paid for itself. So does yours: each heavy
        technology that spreads raises output everywhere, which raises what the
        State and the market can pay you. Without this term the model says an
        industrial revolution is unaffordable, which is false, and the reason it
        is false is that the revolution funds itself.
        """
        diffused = sum(1 for k in self.done if self.nodes[k]["tier"] >= 2)
        e = 1.0 + 0.055 * diffused
        if not self.has("corpus_dispersed"):
            e = 1.0 + 0.030 * diffused      # knowledge locked in one workshop spreads slowly
        return e

    def state_funding(self):
        if not self.has("patron_imperial"):
            return 0.0
        return (2500.0 * self.economy * self.state_capacity * self.pop_scale ** 0.4
                * (1.0 + max(0.0, self.gov) / 25.0) * self.rep_factor())

    def grant_ambient(self):
        """Credit this society's existing technology immediately.

        It used to happen on the first `step`, which meant turn-one `available`
        listed a hundred and thirty things the player was about to be handed for
        nothing, and `done_count` then jumped from 12 to 140 for free. Every
        naive tester remarked on it, one called it "a 128-technology free dump",
        and the reviewer's instruction is the obviously right one: these are
        COMPLETED before the game starts, not available to research.
        """
        changed = True
        while changed:
            changed = False
            for k in self.order:
                n = self.nodes[k]
                if k in self.done or k in self.active:
                    continue
                if self._is_foreign_institution(k):
                    continue
                if (n["tier"] == 0 and n["ph"] == 0 and n["_total_cost"] <= 1
                        and all(p in self.done for p in n["pre"])):
                    self.done.add(k)
                    self.granted.add(k)
                    # done_year is set by the callers after construction, so do
                    # not assume it exists yet at grant time.
                    if not hasattr(self, "done_year"):
                        self.done_year = {}
                    self.done_year[k] = self.cfg["start_year"]
                    changed = True

    def credit_limit(self):
        """How far into arrears anyone will actually let you go.

        Unbounded debt is an accounting fiction, and it produced the single worst
        outcome in the playtests: testers sat at minus 200,000 denarii for two
        and three CENTURIES, making no progress, with the clock running. That is
        not a hard game, it is a game that has stopped and not said so.

        In reality credit stops long before that, and the moment it stops you are
        merely poor. Poor is recoverable: you climbed out of it the first time
        starting from 400 denarii and a physician's practice, and nothing has
        taken that practice away from you.

        What you can borrow depends on who will stand behind you, which is the
        same currency as everything else in this model.
        """
        # What a STRANGER can borrow is almost nothing, which is the reviewer's
        # question and the right answer. You have walked into a town with no
        # name, no land and no one to vouch for you. The old floor of 2,000
        # denarii handed a newcomer roughly two years of living expenses on
        # nothing but arrival. Credit here is what someone will advance against
        # your income and the people who will stand behind you.
        base = self.revenue() * 0.5
        if self.has("identity_cover"):     base += 400.0
        if self.has("patron_local"):       base += 3000.0
        if self.has("patron_senatorial"):  base += 15000.0
        if self.has("patron_imperial"):    base += 60000.0
        if self.has("collegium_licensed"): base += 4000.0
        if self.has("endowment_land"):     base += 30000.0      # real collateral
        base += max(0.0, self.reputation) * 250.0
        base += self.forest_ha * 120.0                           # also collateral
        # A FLOOR of one year's running costs, because everyone everywhere has
        # always been able to run a tab. The baker, the landlord and the smith
        # all carry you for a season; what they will not do is advance you cash.
        # Without this floor a household whose rent exceeded its credit line by
        # a few denarii was declared insolvent, settled, and then declared
        # insolvent again the next year, for ever.
        floor = self.living_cost() + self.upkeep() * 0.5
        return max(base, floor) * self.price_index

    def shed_loss_makers(self, yr):
        """In arrears, stop maintaining anything that costs more than it returns.

        This is what finally answers the reviewer's objection, which was the right
        one: if you can build an enterprise starting from 400 denarii and a
        physician's practice, you must be able to rebuild after ruin, and an
        immortal founder should never spend two centuries making no progress.

        The earlier fixes bounded the DEBT but not the BLEEDING. A ruined run
        still held works whose upkeep exceeded their revenue, so net income sat
        near zero for ever and the recovery took centuries. Nobody does that. You
        let the loss-makers go the same year you notice, and then your income is
        your practice again, which is what you started with and is enough.
        """
        if self.capital >= 0:
            return
        shed = []
        while True:
            net = (self.revenue() - self.upkeep() - self.living_cost()
                   - self.mine_operating_cost())
            if net >= 0:
                break
            worst = None
            for k in sorted(self.done):
                n = self.nodes[k]
                if (n["up"] <= n["rev"] or k in self.granted
                        or self.never_abandon(k)):
                    continue
                if worst is None or (n["rev"] - n["up"]) < (self.nodes[worst]["rev"]
                                                           - self.nodes[worst]["up"]):
                    worst = k
            if worst is None:
                break
            self.done.discard(worst)
            # MOTHBALLED, not merely discarded: this is the plant falling into
            # disrepair, exactly like a deliberate `mothball`, and it must show
            # up the same way - in `state.mothballed`, and NOT back in
            # `available` looking like research you have never done. Before
            # this it was a bare discard, so a repossessed work reappeared
            # indistinguishable from something you had never built, and
            # `restore` (a fraction of the cost) was never offered.
            self.mothballed.add(worst)
            shed.append(worst)
        if shed:
            # NAME THEM. "stopped maintaining 1 works" told a player nothing:
            # not which one, not how to get it back. A tester asked the fair
            # question - how do you understand what you lost, or why an option
            # reappeared, if you were never told its name?
            self.log.append((yr, "stopped maintaining %d works that cost more than "
                                 "they returned: %s" % (len(shed), ", ".join(shed))))

    def work_for_wages(self, trade, hours):
        """Do a job. For money. Like everybody else.

        The reviewer asked for this and it is a fair gap: you could hire a smith,
        a glassblower or a farmer all day long and had no way to BE one. A
        founder with no capital and a useful pair of hands should be able to earn
        a wage, and at the start it is one of the few things he can do.

        It is paid at the ordinary rate for that trade, which is the same table
        the game charges you when you hire someone, so there is no arbitrage in
        either direction. The cost is your own hours, which are the one resource
        nothing else can buy, so this is always a trade of time for money and
        usually a bad one once you have anything better to do. That is the
        honest shape of wage labour.
        """
        w = WAGES.get(trade)
        if w is None:
            return 0.0, ("no such trade. you could work as: "
                         + ", ".join(sorted(WAGES)))
        hours = float(hours)
        if hours <= 0:
            return 0.0, "hours must be greater than zero"
        left = self.director_pool() - getattr(self, "wage_hours_this_year", 0.0)
        if hours > left:
            return 0.0, ("you have %.0f of your own hours left this year, not %.0f"
                         % (max(0.0, left), hours))
        # Your own labour is worth the trade rate: the SAME rate the game charges
        # you to employ somebody in that trade, which is the point. It used to be
        # billed from the hourly column while hiring was billed from the annual
        # one, and those two columns disagree by about half, so a founder could
        # work as a scholar for 1,416 a year and hire one for 625. The docstring
        # claimed "there is no arbitrage in either direction" while the arithmetic
        # ran a 2.3x spread.
        rate = ANNUAL_WAGE.get(trade, 375.0) / self.HOURS_PER_PERSON_YEAR
        pay = (hours * rate * self.price_index * self.wage_index
               * (1.0 + min(0.5, self.reputation / 200.0)))
        self.capital += pay
        self.wage_hours_this_year = getattr(self, "wage_hours_this_year", 0.0) + hours
        self.wages_earned = getattr(self, "wages_earned", 0.0) + pay
        return pay, None

    def debt_interest_rate(self):
        """What arrears cost you a year.

        Roman lending was expensive and the legal ceiling of twelve per cent was
        a ceiling on the RESPECTABLE end of it; maritime loans ran far higher
        because the risk was real. A man with no standing borrows from whoever
        will have him and pays for it. Standing is what makes money cheap, which
        is the same rule as everything else in this model: patronage is the
        currency underneath the currency.
        """
        r = 0.12
        if self.has("patron_local"):        r -= 0.015
        if self.has("patron_senatorial"):   r -= 0.03
        if self.has("patron_imperial"):     r -= 0.03
        if self.has("endowment_land"):      r -= 0.02          # secured, not personal
        if self.has("fin_argentarii"):      r -= 0.01          # a banker you know
        r -= min(0.03, max(0.0, self.reputation) / 3000.0)
        return max(0.0, r)

    def charge_interest(self, yr):
        """Arrears accrue. They did not before, which made debt free money."""
        if self.capital >= 0:
            return 0.0
        rate = self.debt_interest_rate()
        owed = -self.capital * rate
        self.capital -= owed
        self.interest_paid = getattr(self, "interest_paid", 0.0) + owed
        if owed > 0 and (getattr(self, "insolvent_years", 0) in (1, 5, 15)):
            self.log.append((yr, "interest on %0.f denarii of arrears at %.1f%% a year"
                                 % (-self.capital, rate * 100)))
        return owed

    def enforce_credit_limit(self, yr):
        """Nobody lends past the limit, so past the limit you simply stop.

        The order matters and is the realistic one: first you stop paying for new
        work, then you let go of what you cannot maintain, and only then, if it is
        still hopeless, your creditors write the rest off and take everything
        that was not nailed down. You are left poor rather than impossibly
        indebted, which is a position you can work out of.
        """
        limit = self.credit_limit()
        if self.capital >= -limit:
            return
        # stop everything in progress: you cannot fund it
        if self.active:
            dropped = sorted(self.active)
            for k in dropped:
                self.active.pop(k, None)
                self.bountied.discard(k)
            self.credit_frozen_until = yr + 5
            self.log.append((yr, "CREDIT EXHAUSTED: %d projects halted, unfinished. "
                                 "Nobody will fund new work here for some years"
                                 % len(dropped)))
        # let go of what you cannot maintain
        if self.capital < -limit:
            self.mothball_mines()
        if self.capital < -limit:
            burden = sorted((k for k in self.done
                             if self.nodes[k]["up"] > self.nodes[k]["rev"]
                             and k not in self.granted
                             and not self.never_abandon(k)),
                            key=lambda k: (self.nodes[k]["rev"] - self.nodes[k]["up"]))
            taken = []
            for k in burden:
                if self.capital >= -limit:
                    break
                self.done.discard(k)
                self.capital += self.nodes[k]["up"] * 2.0
                # MOTHBALLED, not merely discarded - see the identical comment
                # in shed_loss_makers. Without this a work creditors took stood
                # indistinguishable from research never begun, and `restore`
                # (a fraction of the cost) was never offered for it.
                self.mothballed.add(k)
                taken.append(k)
            # Only say it if it happened. This line used to fire every year
            # whether or not there was anything left to take, so a run with
            # nothing to lose logged creditors seizing it over and over.
            # NAME THEM, for the same reason shed_loss_makers now does: a
            # player cannot understand what they lost, or why it reappeared
            # mothballed rather than gone, from a bare count.
            if taken:
                self.log.append((yr, "creditors took what they could: %d works let go: %s"
                                     % (len(taken), ", ".join(taken))))
        # And the household goes. This was the missing piece: a tester's run sat
        # pinned at the credit floor making no progress for a century because the
        # upkeep of a household they could no longer feed consumed every denarius
        # of income forever. Nobody keeps four hundred dependants they cannot
        # feed. People are sold or freed and they leave, and the point of modelling
        # it is that shedding them is how you become solvent again.
        if self.capital < -limit and (self.slaves or self.freedmen):
            freed = self.slaves + self.freedmen
            self.manumit(self.slaves)          # you do not sell them on
            self.freedmen = 0
            self.artisans = max(3.0, self.artisans * 0.4)
            self.log.append((yr, "the household disperses: %d people leave, because "
                                 "you can no longer feed them" % freed))

        # DEBT BONDAGE, where the society had it, and worked off, because that is
        # what it mostly was. A tester asked me to reconsider having refused it:
        # "I know a lot of slave debt was also something you worked off, so it
        # wouldn't necessarily be a dead end." That is right, and the general
        # case matters more than the Roman one: Han debt servitude, the Norse
        # debt-thrall and Mexica tlacotin were all terms of service that ended,
        # were redeemable, and in the Mexica case were not heritable. Rome is the
        # exception, not the rule, because nexum was abolished in 326 BC, so Rome
        # carries debt_bondage false and goes straight to the write-off below.
        #
        # In bondage your hours are not your own. That is the whole penalty, and
        # it is a heavy one in a game whose scarcest resource is your hours; but
        # it ends, and it ends sooner if the work is worth something.
        if (self.capital < -limit and self.civ.get("debt_bondage")
                and not self.bondage_years_left):
            term = float(self.civ.get("bondage_years", 10))
            self.bondage_years_left = term
            self.bondage_debt = -self.capital
            self.capital = 0.0
            self.log.append((yr, "BONDAGE: you cannot pay, and you enter service for "
                                 "your debt. For about %d years most of your hours "
                                 "belong to someone else. It is not the end: it is "
                                 "worked off, and then you are free again" % term))
            return

        # and the rest is written off. You keep your standing, your knowledge and
        # your practice, which is exactly what you started with.
        #
        # ONCE A DECADE AT MOST. The first version settled whenever the balance
        # sat a denarius past the line, so a household whose rent slightly
        # exceeded its credit was "settled" every single year, logging the same
        # dramatic event five hundred times. A write-off is a once-in-a-life
        # humiliation, not an annual accounting entry, and between them you are
        # simply in arrears, which already has consequences of its own.
        if self.capital < -limit and yr - getattr(self, "last_settlement", -999) >= 10:
            self.last_settlement = yr
            self.capital = -limit * 0.35
            self.reputation = max(0.0, self.reputation - 12)
            self.log.append((yr, "INSOLVENCY SETTLED: the debt is written off, you "
                                 "keep your name and your knowledge, and you begin "
                                 "again poor"))

    def cost_money_factor(self):
        """What a denarius of QUOTED cost means, for spending purposes.

        This exists because money_real was being multiplied into every price,
        and money_real FALLS as the currency is debased. So the worse the money
        got, the cheaper everything became: a naive tester found a pawnshop
        quoted at 5 denarii in 278 AD that had cost 1,025 when they built one in
        160, and correctly said debasement should push nominal prices UP, not
        collapse them by two orders of magnitude. They guessed the cause exactly:
        a multiplier tending to zero being multiplied in rather than divided.

        The model is in REAL terms. Debasement destroys the value of CASH, which
        is already handled by taking a haircut off capital when it fires. Real
        prices do not fall, so nothing here tracks money_real; it survives only
        as something to report. Applying both would have been a double count in
        opposite directions.
        """
        return float(self.price_index)

    def opposition_factor(self, k):
        """Opposed work costs more: bribes, delay, a provincial site, a front man."""
        return 1.0 + 0.25 * max(0.0, -self.state_interest(self.nodes[k]))

    def project_cost(self, k):
        """What this project will actually cost in money, all factors applied.

        This is the number `why` quotes and the number the project must have
        actually PAID before it can complete. It used not to exist, and that was
        the single worst bug in the economy: step() charged what you could afford
        each year, clamped at your balance, and then completed the project on
        hours and calendar alone. A tester started a 4,361 denarius balloon with
        400 denarii, finished it in four years having paid about 984, and the
        remainder was simply forgiven. Money was decorative; only hours were real.
        """
        n = self.nodes[k]
        return (n["_total_cost"] * self.cost_money_factor() * self.opposition_factor(k)
                * self.civ_cost_factor(k) * self.material_cost_factor(k))

    def done_in_order(self):
        """Everything you have finished, in a FIXED order.

        `self.done` is a set of strings, and a set of strings iterates in an
        order that depends on PYTHONHASHSEED, which Python randomises per
        process. Three places summed floats over it - revenue, upkeep and
        material demand - and floating point addition is not associative, so
        the totals differed in their last bits between one process and the
        next. Over five hundred years those last bits decide which side of a
        threshold you land on, and the same --seed gave two different answers
        on alternate invocations. Three other sites were fixed for this before
        by sorting; these were missed because nothing here touches the RNG, and
        the arithmetic looked innocent.

        `self.order` is a list, and a list is a list.
        """
        return [k for k in self.order if k in self.done]

    def revenue(self):
        r = 0.0
        for k in self.done_in_order():
            if k in self.granted and not self._practisable(k):
                continue          # the society's, not yours
            n = self.nodes[k]
            if n["rev"]:
                age = self.year - self.done_year.get(k, self.year)
                ramp = min(1.0, (age + 1) / self.cfg["revenue_ramp_years"])
                r += n["rev"] * ramp
        # THERE IS ONLY SO MUCH MARKET. Uncapped, this compounds: every venture
        # pays back inside two years, so its income buys the next one, and a run
        # ended holding three billion denarii against an empire whose entire
        # annual product was perhaps five billion. Testers saw the near end of
        # it and said so plainly: "I have far more capital than I have good
        # places to put it". You cannot sell more inns than the town wants, and
        # a saturating curve says that without ever making a venture worthless.
        # WHAT YOUR OWN WORKSHOP SELLS. Charging wages explicitly without
        # crediting the work was half an accounting change: in the old model a
        # trained staff was free and its output was folded invisibly into node
        # revenue, so adding a payroll of 12,000 a year and no corresponding
        # output made every civilization except Rome unable to finish. Thirty
        # craftsmen in a workshop do not sit there costing money. They make
        # things, and the things are sold.
        #
        # It is deliberately less than a 2x markup on wages and it needs somewhere
        # to work: a staff with no workshop is an expense, which is exactly why
        # workshop_first matters and why it is cheap.
        r += self.workshop_output()
        gross = r * (self.economy ** 0.75)
        ceiling = 900000.0 * self.pop_scale * (self.economy ** 0.75) * self.price_index
        gross = gross / (1.0 + gross / max(1.0, ceiling))
        return (gross + self.state_funding()) * self.output_factor

    def workshop_output(self):
        """What your standing staff produces and sells, over and above projects."""
        if not (self.has("workshop_first") or self.has("school_founded")):
            return 0.0
        craft = sum(n for t, n in self.employees.items() if trade_family(t) == "craft")
        craft += self.freedmen + self.slaves * 0.7
        wage = 0.0
        for t, n in self.employees.items():
            if trade_family(t) == "craft":
                wage += n * ANNUAL_WAGE.get(t, 375.0)
        wage += (self.freedmen + self.slaves * 0.7) * ANNUAL_WAGE.get("artisan", 250.0)
        mark = 1.55
        if self.has("interchangeable_parts"):  mark += 0.35
        if self.has("power_grid"):             mark += 0.45
        return wage * mark * self.wage_index * self.price_index

    def revenue_sources(self):
        """Where the money actually comes from, itemised.

        Testers asked this three separate times and could not answer it: "there
        is no visible in-fiction source for it", "a player who never issues a
        single start still gets richer every year". Both were looking at the
        income from practising medicine, which is the cover identity the game
        tells you to adopt, and neither had any way to find that out.
        """
        rows = {}
        for k in self.done_in_order():
            if k in self.granted and not self._practisable(k):
                continue
            n = self.nodes[k]
            if not n["rev"]:
                continue
            age = self.year - self.done_year.get(k, self.year)
            ramp = min(1.0, (age + 1) / self.cfg["revenue_ramp_years"])
            amt = n["rev"] * ramp * (self.economy ** 0.75) * self.output_factor
            if amt > 0.5:
                rows[k] = round(amt, 1)
        out = dict(sorted(rows.items(), key=lambda kv: -kv[1])[:15])
        if self.state_funding() > 0.5:
            out["_state_funding"] = round(self.state_funding() * self.output_factor, 1)
        return out

    # Of the auto-granted nodes that carry revenue, seven are medicine and two
    # are shipping, and the difference decides who gets paid. Cataract couching
    # is a skill a single trained person practises with their own hands, and
    # practising it is exactly the cover the guide tells you to adopt. A fleet
    # of large merchant ships is owned by other people and you are not entitled
    # to its freight. Removing the revenue from BOTH, which is what I did first,
    # was too blunt: it left every civilization with no way to earn a living at
    # all, and the Norse, who are poorer and pay a 1.4 price index, could then
    # never accumulate the 1,580 denarii for identity_cover. They failed 100% of
    # runs, blocked on the first node in the game.
    PRACTISABLE_CATS = {"surgery", "obstetrics", "pharmacology", "medicine",
                        "diagnosis", "dentistry"}

    def _practisable(self, k):
        """Is this granted node a skill YOU can practise for a fee?"""
        return self.nodes[k].get("cat") in self.PRACTISABLE_CATS

    def upkeep(self):
        # Symmetrically, you do not pay to maintain what you do not own, but you
        # do bear the small standing cost of the practice you actually run.
        return sum(self.nodes[k]["up"] for k in self.done_in_order()
                   if k not in self.granted or self._practisable(k))

    # ---- raw material supply ------------------------------------------------
    CHARCOAL_PER_HA = 0.75          # tonnes per hectare per year, sustainable
    # How much of the empire's annual output you can actually BUY. This is not
    # one number: charcoal is bulky, crumbles when carted, and is therefore a
    # LOCAL commodity no matter how much of it the empire makes in total, while
    # coal is barely used by anyone so you can have almost all of it.
    MARKET_SHARE = {"charcoal": 0.002, "iron": 0.03, "copper": 0.03, "lead": 0.03,
                    "tin": 0.05, "silver": 0.01, "coal": 0.50, "saltpetre": 0.0}

    # Coke and charcoal are not interchangeable at one kg for one kg. A charcoal
    # blast furnace burns about 3 kg of charcoal per kg of iron; a coke furnace
    # burns about 1.6 kg of coke, and coke is about 1.6 kg of coal, so 2.56 kg
    # of coal. Switching fuel therefore MOVES the demand to a different material
    # at 0.85 of the mass, and that is the whole reason coke mattered: not that
    # it is better fuel, but that coal is dug and charcoal has to be grown.
    COKE_PER_CHARCOAL = 0.85

    def chosen_fuel(self, k):
        """Which fuel this node would actually burn, given what you have.

        The tree had a fuel OR-group on the blast furnace and a hard-coded
        4,500 tonnes of charcoal in its material list. The group was decorative:
        picking coke changed the quality factor and left the charcoal demand
        exactly where it was, so the model could never show the one substitution
        that actually decided industrial history.
        """
        for g in (self.nodes[k].get("req_any") or []):
            if "fuel" not in str(g.get("group", "")).lower():
                continue
            best, pick = 0.0, None
            for opt, qual in (g.get("options") or {}).items():
                have = opt in self.done or opt not in self.nodes
                if have and float(qual) > best:
                    best, pick = float(qual), opt
            if pick and ("coke" in pick or "coal" in pick):
                return "coke"
        return "charcoal"

    def annual_material_demand(self):
        """Tonnes per year of the materials that actually bind, from work in hand."""
        d = collections.Counter()
        for k in sorted(self.active):
            n = self.nodes[k]
            span = max(1.0, float(n.get("build_yrs") or n.get("yrs") or 1.0))
            coke = self.chosen_fuel(k) == "coke"
            for m, q in n["mat"].items():
                if coke and m in ("charcoal_kg", "firewood_kg"):
                    d["coal_kg"] += float(q) * self.COKE_PER_CHARCOAL / span / 1000.0
                    continue
                d[m] += float(q) / span / 1000.0     # kg -> tonnes per year
        # A furnace does not eat charcoal only while it is being built. It eats
        # charcoal every year it runs, forever. Omitting that was why forest
        # ownership never mattered in the model and always mattered in reality.
        for k in self.done_in_order():
            n = self.nodes[k]
            if n["up"] <= 0 or not n["mat"]:
                continue
            span = max(1.0, float(n.get("build_yrs") or n.get("yrs") or 1.0))
            coke = self.chosen_fuel(k) == "coke"
            for m, q in n["mat"].items():
                if coke and m in ("charcoal_kg", "firewood_kg"):
                    d["coal_kg"] += 0.5 * float(q) * self.COKE_PER_CHARCOAL / span / 1000.0
                    continue
                d[m] += 0.5 * float(q) / span / 1000.0
        return d

    def resource_throttle(self):
        """How much of this year's planned work the materials will actually support.

        Charcoal is the one that bites, because it is not mined, it is GROWN.
        A hectare of coppice yields about 0.75 tonnes of charcoal a year, and a
        single blast furnace making 300 tonnes of iron eats 900 tonnes of it. If
        you have not bought the woodland, the furnace idles.
        """
        emp = self.res["empire_output_100ad"]
        demand = self.annual_material_demand()
        worst, who = 1.0, None
        checks = {
            "charcoal_kg": ("charcoal", self.forest_ha * self.CHARCOAL_PER_HA),
            "firewood_kg": ("charcoal", self.forest_ha * self.CHARCOAL_PER_HA * 4),
            "iron_bar_kg": ("iron", self.mine_capacity.get("iron", 0.0)),
            "iron_ore_kg": ("iron", self.mine_capacity.get("iron", 0.0)),
            "coal_kg": ("coal", self.mine_capacity.get("coal", 0.0)),
            "copper_kg": ("copper", self.mine_capacity.get("copper", 0.0)),
            "lead_kg": ("lead", self.mine_capacity.get("lead", 0.0)),
            "tin_kg": ("tin", self.mine_capacity.get("tin", 0.0)),
            "silver_kg": ("silver", self.mine_capacity.get("silver", 0.0)),
            "nitre_kg": ("saltpetre", self.nitre_bed_m2 * 0.0008),
        }
        for mat, (emp_key, own) in checks.items():
            need = demand.get(mat, 0.0)
            if need <= 0:
                continue
            share = self.MARKET_SHARE.get(emp_key, 0.03)
            # How much of a market you can command is a function of STANDING, not
            # just of money. A stranger buys at the margin; a man with senatorial
            # backing buys through their agents; a holder of imperial patronage
            # has the fiscus itself as a supplier, and the metalla were largely
            # imperial property. Charcoal is exempt because no amount of standing
            # makes a bulky crumbling fuel travel further than it can travel.
            if emp_key != "charcoal":
                if self.has("patron_imperial"):     share *= 6.0
                elif self.has("patron_senatorial"): share *= 2.5
                elif self.has("citizenship"):       share *= 1.4
                share = min(share, 0.60)
            # GEOLOGY, NOT DEMOGRAPHY. This used to be `* self.pop_scale`:
            # mineral availability scaled by population, so Norse Scandinavia
            # got 2.3% of Rome's coal because it has 2.3% of the people, and
            # England in 1300 got 7%, when England is precisely where the
            # coal actually is. A coalfield does not care how many people
            # live near it. mineral_scale() derives this instead from the
            # regions this civilization actually holds and can trade with
            # (see _compute_mineral_scale). Charcoal stays on pop_scale: it
            # is not mined, it is a local wood market, and THAT genuinely
            # does track how much local economic activity there is to buy
            # firewood from.
            scale = self.pop_scale if emp_key == "charcoal" else self.mineral_scale(emp_key)
            market = emp.get(emp_key, {}).get("t_per_yr", 0) * share * scale
            # Bengal saltpetre: an existing annual sea route, not a nitre bed.
            # This is the single most useful thing in the geography file.
            if emp_key == "saltpetre" and self.has("exp_trade_route_extend"):
                market += 60.0
            supply = own + market
            if supply < need:
                f = max(0.05, supply / need)
                if f < worst:
                    worst, who = f, emp_key
        self.throttle, self.binding = worst, who
        if who:
            self.shortages[who] += 1
        return worst

    # Capital to create one tonne per year of standing extraction capacity, and
    # the recurring cost of actually getting that tonne out. DERIVED, not
    # measured: a Roman coal hewer working a shallow drift wins on the order of
    # a tonne a day, so 250 t/yr a man, and the miner wage of 0.09 den/hr over
    # 2000 hours is 180 den a year, giving roughly 0.7 den per tonne in wages
    # before haulage. Doubling it for haulage, timbering and overseers gives the
    # figures below. Metal ores cost far more per tonne of METAL because of the
    # ore grade and the smelting, and the capital rises with depth and drainage.
    # Gold is here because a tester asked the obvious question about debasement:
    # "what if you build a mine that can mine gold?" If the money is being ruined
    # by having less silver in it, a man who digs his own metal is not ruined with
    # it. Roman gold (Dacia, Las Medulas) was mined at enormous cost and that is
    # what the capex says.
    MINE_CAPEX_PER_T_YR = {"coal": 9.0, "iron": 60.0, "copper": 240.0,
                           "lead": 80.0, "tin": 420.0, "silver": 9000.0,
                           "gold": 160000.0}
    MINE_OPEX_PER_T     = {"coal": 1.5, "iron": 12.0, "copper": 55.0,
                           "lead": 18.0, "tin": 95.0, "silver": 2200.0,
                           "gold": 42000.0}
    MINE_LEAD_YEARS = 3.0        # sinking, drainage, roads, and hiring

    def open_mine(self, mat, t_per_yr):
        """Open your own workings.

        The model used to treat the Empire's ATTESTED output as a hard ceiling,
        so a founder who needed twenty thousand tonnes of coal a year simply
        never got it and sat throttled for centuries. That is the unobtainable
        fallacy wearing different clothes. Rome mined almost no coal because
        almost nobody wanted coal, not because the coal was not there: Britain,
        Gaul and Spain are sitting on it, and Roman engineers already sink
        shafts, drive adits and drain them with wheels at Rio Tinto and Las
        Medulas. If you know what coke is for, you open a mine.

        What it is NOT is free or instant. You pay to sink it, you wait for it,
        and you pay every year to work it.
        """
        if t_per_yr <= 0:
            return 0.0
        cap = self.MINE_CAPEX_PER_T_YR.get(mat)
        if cap is None:
            return 0.0
        # Scale beyond a local lease needs a concession, which in practice means
        # the fiscus. Metalla were largely imperial property.
        # The ceiling is about STANDING and STATE CAPACITY, not about one
        # Rome-specific node id. Keying it on patron_imperial permanently capped
        # every civilization that has no emperor, which is not a finding about
        # the Norse, it is a bug about the model. A society with little state
        # capacity genuinely cannot organise a very large mine, but a chieftain
        # who can raise a crew can certainly do better than a foreigner with a
        # local lease.
        sc = float(self.civ.get("state_capacity", 0.5))
        if self.has("patron_imperial"):     ceiling = 20000.0 + 60000.0 * sc
        elif self.has("patron_senatorial"): ceiling = 9000.0 + 20000.0 * sc
        elif self.has("citizenship"):       ceiling = 6000.0 + 8000.0 * sc
        else:                               ceiling = 3000.0 + 4000.0 * sc
        # And scale is buyable. What actually limits a mine is crews, timber,
        # drainage and someone to run it, all of which a large enterprise can
        # organise whether or not it holds a title. Without this the Norse run
        # ended with 259 million denarii unspent and no iron mine, capped at
        # 3,600 tonnes a year by institutions that civilization does not have.
        ceiling *= 1.0 + min(5.0, max(0.0, self.revenue()) / 60000.0)
        t_per_yr = min(t_per_yr, max(0.0, ceiling - self.mine_capacity.get(mat, 0.0)
                                          - self.mine_pending.get(mat, 0.0)))
        if t_per_yr <= 0:
            return 0.0
        cost = t_per_yr * cap * self.price_index
        if cost > self.capital:
            t_per_yr = self.capital / (cap * self.price_index)
            cost = self.capital
        if t_per_yr <= 0:
            return 0.0
        self.capital -= cost
        # Each investment is its own working with its own sinking time. Pooling
        # them and taking the LATEST ready date meant a player who invested
        # spare cash every year, which is exactly what a poor civilization must
        # do, pushed the finish line back annually and never got any capacity at
        # all: a playtester funded sixty consecutive years and ended with an
        # empty mine_capacity.
        self.mine_tranches = getattr(self, "mine_tranches", [])
        self.mine_tranches.append([mat, t_per_yr, self.year + self.MINE_LEAD_YEARS])
        self.mine_pending[mat] = self.mine_pending.get(mat, 0.0) + t_per_yr
        return t_per_yr

    def commission_mines(self):
        """Move finished workings from pending into capacity, tranche by tranche."""
        still = []
        for mat, amount, ready in getattr(self, "mine_tranches", []):
            if self.year >= ready:
                self.mine_capacity[mat] = self.mine_capacity.get(mat, 0.0) + amount
                self.mine_pending[mat] = max(0.0, self.mine_pending.get(mat, 0.0) - amount)
                if self.mine_pending.get(mat, 0.0) <= 0:
                    self.mine_pending.pop(mat, None)
            else:
                still.append([mat, amount, ready])
        self.mine_tranches = still

    def mothball_mines(self):
        """Stop working what you cannot pay for, worst value first.

        Mothballing is not free to reverse: the shaft floods, the timbering
        rots and the crew disperses, so bringing capacity back means paying to
        sink it again through open_mine. That is the honest cost of having
        overbuilt."""
        order = sorted(self.mine_capacity,
                       key=lambda m: -self.MINE_OPEX_PER_T.get(m, 0.0))
        for m in order:
            if self.capital >= 0:
                break
            cut = self.mine_capacity[m] * 0.5
            self.mine_capacity[m] -= cut
            self.capital += cut * self.MINE_OPEX_PER_T.get(m, 0.0) * self.price_index
            self.log.append((self.year, "MOTHBALLED half the %s workings; you could "
                                        "not pay to keep them running" % m))
            if self.mine_capacity[m] < 1.0:
                self.mine_capacity.pop(m)
        # This used to clamp capital to minus one year's revenue every time any
        # mine was held, which forgave debt the mothballing had not actually
        # paid off. A playtester proved it to the cent: capital landed on
        # exactly -revenue() on two separate steps with different amounts
        # mothballed in between, so the floor, not the arithmetic, set the
        # number. Debt is now whatever the arithmetic says it is.

    def mine_operating_cost(self):
        """Charged every year the workings stand, whether or not you use them."""
        return sum(self.mine_capacity.get(m, 0.0) * self.MINE_OPEX_PER_T.get(m, 0.0)
                   for m in self.mine_capacity) * self.price_index

    def buy_forest(self, ha):
        """Coppice woodland, bought outright. The cheapest thing in the tree that
        nobody thinks to buy, and the one that decides whether a furnace runs."""
        cost = ha * 250.0 * self.price_index      # ~1 iugerum of woodland per 0.25 ha
        if cost > self.capital:
            return 0.0
        self.capital -= cost
        self.forest_ha += ha
        return ha

    def living_cost(self):
        """You have to eat, sleep somewhere, pay tax, and look the part.

        The last one is not a joke. In a patronage society a man who is visibly
        richer than he dresses is suspected, and a man seeking status must spend
        on it: clothes, a household, hospitality, and public benefaction. That
        expense RISES with your wealth and with your standing, which is why so
        many Roman fortunes went sideways into games and buildings.
        """
        base = 120.0                                  # bare subsistence, one person
        household = 90.0 * (1 + self.freedmen * 0.5 + self.slaves * 0.35)
        tax = max(0.0, self.revenue()) * 0.06         # portoria, vicesima, local dues
        status = 0.0
        if self.has("citizenship"):        status += 200
        if self.has("patron_senatorial"):  status += 900
        if self.has("patron_imperial"):    status += 2500
        status += max(0.0, self.capital) * 0.015      # you cannot look poor and rich
        return base + household + tax + status + self.wage_bill()

    HOURS_PER_PERSON_YEAR = 2000.0   # prices.json: a 10-hour day, 250 days, less feasts

    def wage_bill(self):
        """What your standing staff costs you every year, by trade.

        A machinist is not paid a labourer's wage and cannot be had at one. This
        is the other half of differentiating the trades: the expensive trades are
        expensive to keep, so a large staff of the people you actually need is a
        real commitment rather than a number that drifts upward on its own.
        """
        total = 0.0
        for t, n in self.employees.items():
            total += n * ANNUAL_WAGE.get(t, 375.0) * self.wage_index
        return total * self.price_index

    def effective_scholars(self):
        """You are your own natural philosopher; everyone else is hired."""
        return self.scholars + (1.0 if self.founder_alive else 0.0)

    def trade_available(self, t):
        """Can this trade be had here at all, at any price?

        Rome has masons and plumbers in abundance and no machinists whatever.
        An absent trade is not expensive, it is absent, and the only way to have
        one is to teach somebody the trade yourself.
        """
        if t not in TRADES_ABSENT:
            return True
        return t in self.trades_created

    def market_supply(self, t):
        """Hours a year of this trade the local labour market can actually supply."""
        if not self.trade_available(t):
            return 0.0
        base = self.cfg["hired_hours_cap_base"] * (0.25 + 0.75 * min(1.0, self.pop_scale))
        if t in TRADES_ABSENT:
            # Only the people you taught, plus the ones they have taught since.
            return self.employees.get(t, 0.0) * self.HOURS_PER_PERSON_YEAR * 1.5
        # How much of the town's labour market is this trade. These are shares of
        # the SAME base the old single pool used, and the aggregate pool is still
        # applied on top, so total hired labour is bounded exactly as before; what
        # changes is that the trades are no longer one interchangeable bucket.
        note = TRADE_NOTES.get(t, "").lower()
        if "abundance" in note or "abundant" in note or "numerous" in note:
            share = 1.0
        elif "scarcest" in note:
            share = 0.08
        elif trade_family(t) == "scholar":
            share = 0.35          # literate men are a small fraction of anywhere
        elif t in ("labourer", "artisan", "carpenter", "mason", "potter", "smith",
                   "sailor", "miner", "furnaceman"):
            share = 0.9
        else:
            share = 0.25          # glassblowers, engravers, opticians' forebears
        cap = base * share
        if self.has("school_founded"):        cap *= 2.0
        if self.has("patron_imperial"):       cap *= 3.0
        if self.has("academy_network"):       cap *= 2.5
        if self.has("interchangeable_parts"): cap *= 1.5
        return cap + self.employees.get(t, 0.0) * self.HOURS_PER_PERSON_YEAR

    def hire(self, trade, n):
        """Take someone onto the staff permanently. They are paid every year."""
        trade = str(trade or "").strip().lower()
        if trade not in WAGES:
            return False, ("no such trade: %s. Trades: %s"
                           % (trade, ", ".join(sorted(WAGES))))
        if n <= 0:
            return False, "n must be greater than zero. Nothing was changed."
        if not self.trade_available(trade):
            return False, ("there are no %ss to hire in this society at any price: %s "
                           'Teach one: {"cmd":"train","trade":"%s","n":1}'
                           % (trade, TRADE_NOTES.get(trade, ""), trade))
        # A finder's fee and the first year in advance, which is what a household
        # actually pays to take a skilled man off someone else's bench.
        fee = n * ANNUAL_WAGE.get(trade, 375.0) * self.wage_index * self.price_index
        if fee > self.capital + self.credit_limit() * 0.5:
            return False, ("hiring %g %ss costs %.0f denarii in advance and you have %.0f"
                           % (n, trade, fee, self.capital))
        room = (self.staff_capacity()[1] + self.supervision_room()
                - self.headcount())
        if n > room:
            return False, ("you can supervise, house and teach %.1f more people, not %g. %s"
                           % (max(0.0, room), n, self._staff_advice("artisans")))
        self.capital -= fee
        self.employees[trade] = self.employees.get(trade, 0.0) + float(n)
        self._resync_pools()
        return True, None

    def fire(self, trade, n):
        """Let staff go. Their wages stop; so does what they were doing."""
        trade = str(trade or "").strip().lower()
        have = self.employees.get(trade, 0.0)
        if have <= 0:
            return False, "you employ no %ss" % trade
        n = min(float(n), have)
        self.employees[trade] = have - n
        if self.employees[trade] <= 1e-9:
            self.employees.pop(trade)
        self._resync_pools()
        return True, None

    def train(self, trade, n, frm=None):
        """Teach a trade that does not exist here into existence.

        This is the answer to "there are no machinists in 100 AD". There are
        smiths, and a smith who spends two years with you becomes the first
        machinist in the world. It costs your own hours, which is the scarcest
        thing you have, and it is per-trade: the machinists you made are no use
        at all when you need a chemist.
        """
        trade = str(trade or "").strip().lower()
        if trade not in WAGES:
            return False, "no such trade: %s" % trade
        if n <= 0:
            return False, "n must be greater than zero. Nothing was changed."
        frm = (frm or ("smith" if trade in ("machinist", "engineer")
                       else "glassblower" if trade == "optician"
                       else "scribe" if trade == "chemist"
                       else "smith")).strip().lower()
        if frm in TRADES_ABSENT and frm not in self.trades_created:
            return False, "you cannot teach from %ss; there are none" % frm
        hours = 450.0 * n            # your hours, teaching, per person
        pool = self.director_pool() - self.director_hours_committed()
        if hours > pool:
            return False, ("teaching %g %ss takes %.0f of your own hours and you have "
                           "%.0f uncommitted this year" % (n, trade, hours, max(0.0, pool)))
        fee = n * ANNUAL_WAGE.get(frm, 375.0) * 1.2 * self.wage_index * self.price_index
        if fee > self.capital + self.credit_limit() * 0.5:
            return False, ("you must keep them fed while they learn: %.0f denarii, "
                           "and you have %.0f" % (fee, self.capital))
        self.capital -= fee
        self.teaching_hours_this_year = getattr(self, "teaching_hours_this_year", 0.0) + hours
        self.trades_created.add(trade)
        self.training.append([0.0, self.year + 2.0, trade, float(n)])
        return True, ("%g %s%s will be ready in 2 years" % (n, trade, "s" if n != 1 else ""))

    def commission(self, trade, hours):
        """Pay for a job, not for a person.

        A tester's objection, and a fair one: "maybe you don't want employees,
        you just want some copper wire, and you don't need a full time smith".
        This buys a specific piece of work from somebody else's shop at a
        premium over their wage, with no standing obligation either way.
        """
        trade = str(trade or "").strip().lower()
        if trade not in WAGES:
            return False, "no such trade: %s" % trade
        if hours <= 0:
            return False, "hours must be greater than zero. Nothing was changed."
        if not self.trade_available(trade):
            return False, ("no %s will take the work; the trade does not exist here: %s"
                           % (trade, TRADE_NOTES.get(trade, "")))
        spare = self.market_supply(trade) - self.contract_hours.get(trade, 0.0)
        if hours > spare:
            return False, ("the %ss here can spare %.0f more hours this year, not %.0f"
                           % (trade, max(0.0, spare), hours))
        # A shop charges more for a one-off than it pays its own man for a year.
        fee = hours * WAGES[trade] * 1.6 * self.wage_index * self.price_index
        if fee > self.capital + self.credit_limit() * 0.5:
            return False, ("%.0f hours of a %s costs %.0f denarii and you have %.0f"
                           % (hours, trade, fee, self.capital))
        self.capital -= fee
        self.contract_hours[trade] = self.contract_hours.get(trade, 0.0) + hours
        self.commissioned[trade] = self.commissioned.get(trade, 0.0) + hours
        return True, ("%.0f hours of a %s bought for %.0f denarii" % (hours, trade, fee))

    def headcount(self):
        return sum(self.employees.values()) + self.slaves + self.freedmen

    def director_hours_committed(self):
        """Hours of your own year already spoken for before any project sees them.

        WAGE HOURS BELONG HERE, and their absence was the worst thing two naive
        testers found. `work` kept its own separate tally, so a founder could
        report "your_hours_left_this_year: 0.0" after a full 2,400 hours of paid
        labour and then complete eight projects worth 2,044 founder-hours in the
        same year. One of them called it "a free second year inside every year"
        and correctly identified it as the dominant strategy in the game. There
        is one year, and one pair of hands.
        """
        return (getattr(self, "teaching_hours_this_year", 0.0)
                + getattr(self, "wage_hours_this_year", 0.0))

    def _resync_pools(self):
        """Recompute the two aggregate pools the tech tree asks for from the
        actual people on the books. `art` and `sch` in the tree mean "trained
        people who understand your methods", so they are the sum of the trades,
        not a number that floats free of them."""
        craft = sum(n for t, n in self.employees.items() if trade_family(t) == "craft")
        schol = sum(n for t, n in self.employees.items() if trade_family(t) == "scholar")
        # People you own or have freed work in the shop; they are not scholars.
        self.artisans = craft + self.freedmen * 1.0 + self.slaves * 0.7
        self.scholars = schol

    TRAINING_YEARS = 3.0      # nobody is a useful artisan the week you buy them

    def slave_quote(self, n_people):
        """What buying this many people actually costs, here, today.

        A town's slave market has a depth; buying beyond it bids the price up.
        Flat pricing let a playtester take 3,333 people in one instant at list
        price, which no market of any period would absorb.
        """
        if n_people <= 0:
            return 0.0
        # The surcharge has to remember. My first version priced each CALL by
        # its own size and kept no memory, so a playtester bought 1,000 people
        # in a hundred calls of ten and paid 297 a head instead of 3,868, a
        # thirteenfold discount, with no cap. A market that resets between two
        # purchases made in the same instant is not a market.
        #
        # market_pressure accumulates with every purchase and decays each year
        # as sellers restock, so buying in slices is now priced as one large
        # purchase unless you actually wait between them.
        depth = max(8.0, 40.0 * self.pop_scale ** 0.5)
        # Integrate the rising price ACROSS the purchase instead of applying one
        # surcharge to the whole block. Applying the end-price to every head
        # overcharged a single large call relative to the same number bought in
        # slices, which is why slicing still saved about a fifth. Now the nth
        # head costs what the nth head costs however you group them.
        already = getattr(self, "market_pressure", 0.0)
        n = float(n_people)
        e = 1.85                       # 1 + 0.85
        integral = (((already + n) ** e) - (already ** e)) / (e * (depth ** 0.85))
        return 300.0 * (n + integral) * self.price_index

    def buy_slaves(self, n_people):
        """The option the model refuses to hide, and refuses to make costless.

        Roman labour is cheap because much of it is coerced, and any honest model
        of a Roman enterprise has to let you do this. It is available, it works,
        it is counted separately, and manumission is modelled as strictly better
        on the numbers as well as on every other ground: a freedman is paid, is
        literate, stays, and transmits what he knows.

        A playtester found three separate holes here and they compounded.

        First, buy_slaves added 0.55 artisans per person and manumit then added
        ANOTHER 0.55 for the SAME PERSON, so one human being yielded 1.1 workers.
        Manumission does not clone anybody. It makes the same person work
        properly, which is a rise from 0.55 to 1.0, so it adds 0.45.

        Second, the price was flat at 300 denarii however many you bought, so
        3,333 people could be had in a single instant at list price. No market
        of any period absorbs that. The price now rises with the size of the
        purchase against the local market's depth.

        Third, it was INSTANT. Buy and free ten people and you had eleven
        trained artisans in the same tick, for money alone, with no founder
        hours and no calendar time. That strictly dominated freedman_staff, the
        node that models the same thing honestly at 900 founder hours and two
        years, so the narrated route was always the worse deal. People now
        arrive untrained and become useful over a training lag.
        """
        if n_people <= 0:
            return 0
        # A town's slave market has a depth. Buying beyond it bids the price up.
        price = self.slave_quote(n_people)
        if price > self.capital:
            return 0
        self.capital -= price
        self.slaves += n_people
        self.market_pressure = getattr(self, "market_pressure", 0.0) + n_people
        # Untrained on arrival. They become productive through self.training.
        self.training.append([n_people * 0.55, self.year + self.TRAINING_YEARS])
        return n_people

    def manumit(self, n_people):
        n_people = min(n_people, self.slaves)
        if not n_people:
            return 0
        self.slaves -= n_people
        self.freedmen += n_people
        self.manumitted_total += n_people
        # The SAME person, working properly: 0.55 to 1.0, not another whole
        # worker. This was the double count.
        #
        # But only for people who are actually TRAINED. A playtester noticed
        # that freeing someone bought this morning still handed over the 0.45
        # uplift immediately while their 0.55 sat in the training queue, so
        # buy-and-free bought 82 per cent of a trained artisan with no calendar
        # time at all, which is most of the way back to the exploit the training
        # lag was added to close. Freeing an untrained person upgrades what they
        # will be worth WHEN they mature; it does not skip the maturing.
        # The training queue also carries taught-trade rows now (which have a
        # trade name in them and no artisan capacity), so read column 0 by index
        # rather than unpacking a row whose width is no longer fixed.
        in_training = sum(row[0] for row in self.training)
        untrained = min(n_people, int(in_training / 0.55 + 0.5))
        trained_freed = max(0, n_people - untrained)
        self.artisans += trained_freed * 0.45
        if untrained:
            share = untrained / max(1.0, in_training / 0.55)
            for row in self.training:
                row[0] *= 1.0 + 0.45 / 0.55 * min(1.0, share)
        # Manumission was publicly admired, and admiration saturates. The first
        # freedmen you make are a statement; the four hundredth is a payroll.
        # Uncapped, this was a reputation pump that beat taking a patron.
        gain = 0.4 * n_people / (1.0 + self.manumitted_total / 25.0)
        self.reputation += min(gain, 6.0)
        return n_people

    def mothball_work(self, k):
        """Shut a completed work down to stop paying its upkeep.

        Three testers hit the same wall and described it the same way: deep in
        debt, the only lever the game offered was to start MORE things, because
        `stop` cancels work in progress and there was nothing at all that shut
        down a finished institution. One wrote "once you've over-built, the
        recurring cost is permanent"; another "your agency basically
        disappears". This is the missing lever. It is not free: you lose what
        the work gave you, and restoring it costs a fraction of building it.
        """
        if k not in self.nodes:
            return False, "no such node"
        if k not in self.done:
            return False, "you have not built that"
        if k in self.granted:
            return False, ("that is something the society has, not something you "
                           "maintain; there is no upkeep of yours to stop")
        if self.nodes[k]["up"] <= 0:
            return False, "that costs nothing to keep; there is nothing to save"
        # A DELIBERATE SHUTDOWN IS NOT AN ABANDONMENT. never_abandon exists to
        # stop the ENGINE quietly deleting a step you need and then refusing to
        # fund rebuilding it. A player choosing to close something down is the
        # opposite: they chose it, restore brings it back, and refusing them was
        # the exact trap a tester hit - the upkeep bankrupting them was the one
        # thing they were not allowed to stop paying for, which is how a bad
        # year became "an unrecoverable softlock". Knowledge still cannot be
        # unlearned; a building can always be shut.
        warn = None
        if self.never_abandon(k):
            if self.nodes[k]["cat"] in self.NEVER_ABANDON:
                return False, ("that is knowledge, or it is who you are here. "
                               "You cannot un-know a thing to save its upkeep")
            warn = ("this is a step on the way to what you are trying to reach; "
                    "you will have to restore or rebuild it before you can go on")
        self.done.discard(k)
        self.mothballed.add(k)
        msg = ("%s shut down; you stop paying %.0f a year for it, and you stop "
               "getting what it gave you" % (k, self.nodes[k]["up"]))
        return True, (msg + (". Note: " + warn if warn else ""))

    def restore_work(self, k):
        """Bring a mothballed work back. The plant rotted while it stood idle."""
        if k not in getattr(self, "mothballed", set()):
            return False, "you have not shut that down"
        n = self.nodes[k]
        fee = self.project_cost(k) * 0.3
        if fee > self.capital + self.credit_limit() * 0.5:
            return False, ("bringing it back costs %.0f denarii and you have %.0f"
                           % (fee, self.capital))
        if any(p not in self.done for p in n["pre"]):
            return False, ("you no longer have what it stands on: "
                           + ", ".join(p for p in n["pre"] if p not in self.done))
        self.capital -= fee
        self.done.add(k)
        self.mothballed.discard(k)
        return True, ("%s back in service for %.0f denarii" % (k, fee))

    def bribe(self, amount):
        """Pay your way out of trouble, deliberately, for a stated sum."""
        amount = float(amount)
        if amount <= 0:
            return False, "amount must be greater than zero. Nothing was changed."
        if amount > self.capital:
            return False, "you have %.0f denarii" % self.capital
        before = self.scandal
        self.capital -= amount
        self.bribes_ytd = 0.7 * self.bribes_ytd + amount
        self.scandal = max(0.0, self.scandal - amount / 300.0 * self.w["bribability"])
        return True, ("scandal %.2f -> %.2f for %.0f denarii" % (before, self.scandal, amount))

    def bounty_eligible(self, k):
        """Can this be bought as a prize instead of built with your own hands?

        A public prize ("ten thousand sesterces to the first glassworker who
        brings me a clear sphere of glass the size of a millet seed") converts
        DENARII into someone else's HOURS, which is the trade you most want to
        make. It only works where the craft already exists in the Empire and the
        artisan can recognise success without understanding the theory. You
        cannot post a bounty for zone refining; nobody would know what to aim at.
        """
        n = self.nodes[k]
        if n["tier"] > 2:
            return False
        if n["cat"] not in ("glass_optics", "metallurgy", "precision", "power",
                            "agriculture", "information", "instruments"):
            return False
        return all(p in self.done for p in n["pre"])

    def post_bounty(self, k):
        """Pay well over the odds, save 65% of your own hours, gain visibility."""
        n = self.nodes[k]
        # 2.5x the cost THIS society would actually incur, not 2.5x an
        # abstract base. A playtester found `why` quoting 188 denarii to build a
        # node while `bounty` demanded 588 for the same thing, because the
        # bounty ignored the civilization and price factors the build applies.
        price = (n["_total_cost"] * 2.5 * self.civ_cost_factor(k)
                 * self.material_cost_factor(k) * self.cost_money_factor())
        if price > self.capital:
            return False
        self.capital -= price
        self.total_spend += price
        self.bounties_paid += 1
        self.active[k] = dict(ph_left=n["ph"] * 0.35, yrs=0.0, spent=price)
        self.bountied.add(k)
        self.suspicion += 2 * self.suspicion_mult   # a public prize makes you conspicuous
        self.log.append((self.year, "posted a public bounty for %s (%s den)"
                         % (n["name"], f"{price:,.0f}")))
        return True

    def substitution_quality(self, k):
        """Resolve `req_any` groups: for each, the best option you actually have.

        A steam engine does not REQUIRE coal and steel. It requires a fuel and a
        pressure vessel. Wood in a bronze boiler works. It is just bad, and the
        quality factor is how bad: it multiplies output and divides efficiency.
        """
        n = self.nodes[k]
        groups = n.get("req_any") or []
        if not groups:
            return 1.0, True
        q = 1.0
        for g in groups:
            best = 0.0
            for opt, qual in (g.get("options") or {}).items():
                if opt in self.done or opt in self.nodes.get(k, {}).get("mat", {}):
                    best = max(best, float(qual))
                elif opt not in self.nodes:
                    best = max(best, float(qual) * 0.9)   # a purchasable commodity
            if best <= 0:
                return 0.0, False        # no option in this group is available
            q *= best
        return q, True

    def start_reason(self, k, ignore_trade=False, _memo=None):
        """Same legality test as `can_start`, but explains a refusal instead of
        just returning False. `can_start` is a thin wrapper around this now;
        the wrapper exists because the optimizer's inner loop calls it a huge
        number of times and does not want to build a string it will discard.
        The reason text is what a PLAYER needs (human or agent): not just "no",
        but "no, because you need a local patron first".

        ignore_trade skips only the "does the trade exist" check below, so
        auto_train can ask a narrower question than "what would help
        eventually": "is THIS the one thing standing between me and starting
        this, right now?" See its use in step(), 4a2.

        _memo is is_visible()'s shared per-descent cache, passed straight
        through to the is_visible() calls below for a missing node's own
        visibility. Not this function's concern otherwise; see is_visible's
        docstring for why it exists."""
        if k not in self.nodes:
            return False, "no such node"
        n = self.nodes[k]
        if k in self.done:
            return False, "already done"
        if k in self.active:
            return False, "already active"
        # A MOTHBALLED WORK IS NOT FRESH RESEARCH. You already know how; what
        # is gone is the plant, at a fraction of the cost to put back up. A
        # `start` here used to charge the FULL cost again and hand back the
        # full founder_hours as if this were the first time, which is exactly
        # what a tester objected to: a repossessed work "reappears in
        # available looking like fresh research rather than something you
        # already knew and must rebuild". `restore` is the honest version.
        if k in getattr(self, "mothballed", set()):
            return False, ("you built this once and let it go; you already "
                           'know how, so restoring it is cheaper than starting '
                           'over: {"cmd":"restore","id":"%s"} for about %.0f '
                           "denarii" % (k, self.project_cost(k) * 0.3))
        # Tier 9 once meant UNOBTAINABLE: rubber, quinine, New World crops. That
        # concept was abolished, because nothing is unobtainable, only elsewhere,
        # and the tree now routes those through exp_* expedition nodes instead.
        # The guard stays only to stop a stray tier 9 from a new branch file
        # silently making a technology permanently unbuildable; treetool now
        # retiers them on merge, so this should never fire.
        if n["tier"] == 9 or n["cat"] == "unobtainable":
            return False, "retired category: unobtainable in this tree"
        if self._is_foreign_only(k):
            return False, ("that is an institution of a different society. %s has "
                           "no such thing, and it is not something you can build "
                           "here" % self.civ.get("name", "this society"))
        missing = [p for p in n["pre"] if p not in self.done]
        if missing:
            # NAME ONLY WHAT YOU HAVE HEARD OF. A tester wrote a twenty-line
            # crawler that did nothing but read this message, and mapped 163
            # nodes - the entire ancestor closure of the transistor - in eight
            # rounds, while `why` and `path` dutifully refused every one of them.
            # Fog that one error message undoes is not fog.
            known = [p for p in missing if self.is_visible(p, _memo=_memo)]
            hidden = len(missing) - len(known)
            if not getattr(self, "fog", False) or not hidden:
                return False, "missing prerequisites: " + ", ".join(missing)
            bits = []
            if known:
                bits.append("missing prerequisites: " + ", ".join(known))
            bits.append("%d other thing%s you have not heard of yet"
                        % (hidden, "" if hidden == 1 else "s"))
            return False, "; and ".join(bits) if known else \
                ("this needs %s, and you do not yet know what %s"
                 % (bits[-1], "they are" if hidden > 1 else "it is"))
        if not self.substitution_quality(k)[1]:
            return False, "no viable option in a required substitution group (fuel, vessel, etc.)"
        # A playtester hit a scholar wall that stopped ALL progress and reported
        # that nothing in the protocol told them how to get more scholars. The
        # refusal named the shortfall and not the remedy, which is the least
        # useful half. Staff is not a technical prerequisite so it never appears
        # in `path`, and the player had no way to discover the answer except by
        # reading prose they had no reason to think was relevant.
        # Arrears blocks NEW commitments, with two escape hatches, because
        # without them this is a trap rather than a setback. A playtester went
        # bankrupt, had a prerequisite abandoned out from under them, and then
        # could not rebuild it: they sat softlocked for 470 years until the
        # horizon. First hatch: creditors care about PERSISTENT insolvency, not
        # one bad year. Second: anything you can fund from this year's income
        # needs nobody's permission.
        # "Cheap enough to need nobody's permission" means payable out of what
        # is actually LEFT, not out of turnover. Measured against gross revenue
        # it let a bankrupt household with 11,637 of income and 6,020 of upkeep
        # start 11,000-denarius projects every year for two centuries, each one
        # halted by the creditors a year later: 18 technologies in 200 years and
        # a log that was nothing but CREDIT EXHAUSTED.
        surplus = (self.revenue() - self.upkeep() - self.living_cost()
                   - self.mine_operating_cost())
        cheap_enough = (self.project_cost(k) <= max(600.0, surplus * 2.0))
        if (getattr(self, "insolvent_years", 0) >= 3
                and not cheap_enough
                and self.capital < -max(4000.0, self.revenue() * 2.0)):
            return False, ("you have been in arrears %d years and are %.0f denarii down; "
                           "nobody will fund a new undertaking of this size. Something "
                           "you can pay for out of this year's income is still allowed, "
                           "so is finishing or stopping what is running."
                           % (getattr(self, "insolvent_years", 0), -self.capital))
        if n["sch"] > self.effective_scholars():
            return False, ("needs %d trained scholars, you have %.1f (you are one of them). %s"
                           % (n["sch"], self.effective_scholars(), self._staff_advice("scholars")))
        if n["art"] > self.artisans:
            return False, ("needs %d trained craftsmen on your own staff, you have %.1f. %s"
                           % (n["art"], self.artisans, self._staff_advice("artisans")))
        # THE TRADE HAS TO EXIST. A node wanting 450 hours of an engineer cannot
        # be built by smiths, and in 100 AD there is no such person as a private
        # engineer: the wage table says so itself. You make one by teaching one.
        absent = [] if ignore_trade else sorted(t for t in n["lab"]
                                                if not self.trade_available(t))
        if absent:
            return False, ("this needs %s and there are none in this society. "
                           'Teach one: {"cmd":"train","trade":"%s","n":2} '
                           "(about 450 of your own hours each, two years)"
                           % (", ".join(a + "s" for a in absent), absent[0]))
        # SOCIAL APPROVAL GATE. Some things the State does not want built, and no
        # amount of money substitutes for someone powerful being willing to be
        # associated with it. See 03_SOCIAL_POLITICS.md section 4.
        # SOCIAL APPROVAL. Computed from this civilization's values and this
        # technology's traits, not from a number baked into the technology.
        # Never let the gate ask for a thing in order to get that same thing:
        # the patronage and institution nodes are how you BUY permission, so they
        # cannot themselves require permission.
        if n["cat"] in ("social", "institution", "foundation", "capability", "material"):
            return True, None
        si = self.state_interest(n)
        if si < -0.4 and not self.has("patron_local"):
            return False, ("the state is wary of this (state interest %.1f); "
                           "get at least a local patron first" % si)
        if si < -1.2 and not (self.has("patron_senatorial") or self.protection > 0.45):
            return False, ("the state actively opposes this (state interest %.1f); "
                           "you need senatorial patronage, or protection above 0.45 "
                           "(you have %.2f)" % (si, self.protection))
        return True, None

    def can_start(self, k, _memo=None):
        return self.start_reason(k, _memo=_memo)[0]

    def start_project(self, k):
        """PLAYER-CHOSEN start. This is the whole reason `--manual` and the
        `agent` JSON protocol exist: the old `play` command let you type a
        node id, but all that did was move it to the front of `order`, the
        list the OPTIMIZER in step() still walked on its own; the optimizer
        went on starting whatever ELSE it wanted that year regardless of what
        you typed. You never actually chose anything, you only nudged a
        priority queue you did not otherwise control. This method is the real
        thing: it applies the same legality check as the optimizer
        (`start_reason`), and if it passes, THIS is the only place besides the
        optimizer's own loop that ever adds to `self.active`. In `--manual`
        mode the optimizer's loop is switched off entirely (see step(), 4b),
        so this becomes the only way anything ever starts.
        """
        ok, why = self.start_reason(k)
        if not ok:
            return False, why
        n = self.nodes[k]
        self.active[k] = dict(ph_left=float(n["ph"]), yrs=0.0, spent=0.0,
                              cost_left=self.project_cost(k))
        # Director hours in step() 5 are handed out by priority in `order`.
        # A thing you just chose to work on should get first call on your own
        # hours, exactly as the old (cosmetic) reprioritisation implied it did.
        if k in self.order:
            self.order.remove(k)
        self.order.insert(0, k)
        return True, None

    def stop_project(self, k):
        """Abandon a project the player started. Money and hours already spent
        on it are gone, same as they would be for a real abandoned enterprise;
        there is no refund."""
        if k not in self.active:
            return False, "not active"
        del self.active[k]
        self.bountied.discard(k)
        return True, None

    # -- main loop ----------------------------------------------------------
    def step(self):
        c = self.cfg
        yr = self.year

        # 1. staff. ATTRITION IS UNCONDITIONAL: people die, are poached and grow
        #    old whatever your policy is. GROWTH IS NOT. It used to be, and that
        #    was the same fault as buying people without being asked: a player
        #    who never issued a single command watched the staff climb on its own.
        #
        #    With auto_hire on (the default for the optimizer, off for a player)
        #    the old smoothing toward capacity runs as before, which is what the
        #    long civilization runs are calibrated against. With it off, the only
        #    things that change the staff are hire, fire, train, buy and manumit.
        sc_cap, ar_cap, di_cap = self.staff_capacity()
        ATTRITION = 0.035           # Roman adult mortality plus normal turnover
        for t in list(self.employees):
            self.employees[t] *= (1.0 - ATTRITION)
            if self.employees[t] < 0.05:
                self.employees.pop(t)
        self._resync_pools()
        # A HOUSEHOLD THAT CANNOT PAY ITS PEOPLE LETS THEM GO. This is the whole
        # answer to "you built it from nothing, so you must be able to rebuild
        # it": the thing that kept a ruined run frozen for two centuries was a
        # payroll it could not carry and never reduced. A run that fired its
        # staff, lived cheaply and started again earned 300 technologies; the
        # same run holding on to eleven people it could not pay earned 18.
        net = (self.revenue() - self.upkeep() - self.living_cost()
               - self.mine_operating_cost())
        # Only when you are ACTUALLY in the red, not merely having an expensive
        # year. Taking someone on is an investment that costs more than it
        # returns at first; shedding on a single negative year undid every hire
        # the moment it was made and a clean run never got a staff at all.
        if net < 0 and self.capital < 0 and self.employees:
            # shed, dearest first, until the books balance
            for t in sorted(self.employees, key=lambda t: -ANNUAL_WAGE.get(t, 375.0)):
                if net >= 0:
                    break
                wage = ANNUAL_WAGE.get(t, 375.0) * self.wage_index * self.price_index
                if wage <= 0:
                    continue
                cut = min(self.employees[t], (-net) / wage)
                self.employees[t] -= cut
                net += cut * wage
                if self.employees[t] < 0.05:
                    self.employees.pop(t)
            self._resync_pools()
            if net >= 0:
                self.log.append((yr, "you cannot pay everyone, so some of them go"))
        if (self.policy.get("auto_hire", not self.manual) and self.capital > 0):
            # Scaled by the SAME affordability figure staff_capacity() just
            # used for sc_cap/ar_cap (see the comment there): supervision-room
            # headroom is not a free six people, it is six people you still
            # have to pay for.
            extra = self.supervision_room() * getattr(self, "_staff_scale", 1.0)
            self.scholars += (sc_cap + extra * 0.35 - self.scholars) * 0.18
            self.artisans += (ar_cap + extra - self.artisans) * 0.22
            # Keep the per-trade books honest about the aggregate: staff taken on
            # for you are generic craftsmen and scribes, and that is all they are.
            craft = max(0.0, self.artisans - self.freedmen - self.slaves * 0.7)
            generic = self.employees.get("artisan", 0.0)
            specials = sum(v for t, v in self.employees.items()
                           if t not in ("artisan", "scholar") and trade_family(t) == "craft")
            self.employees["artisan"] = max(0.0, craft - specials)
            if self.scholars > 0:
                self.employees["scholar"] = self.scholars
            # REPLACE THE PEOPLE YOU LOSE, trade by trade. Attrition was eating
            # the taught trades (the engineers went from 1.9 to 0.3 over sixty
            # years) and nothing ever replaced them, because the top-up only knew
            # about the two generic buckets. A programme that trains the first
            # machinists in the world and then lets them die out has not trained
            # anybody.
            for t in list(self.employees):
                if t in ("artisan", "scholar"):
                    continue
                want = max(self.employees[t], 2.0 if t in self.trades_created else 0.0)
                short = want - self.employees[t]
                if short > 0.02 and self.capital > ANNUAL_WAGE.get(t, 375.0) * 6:
                    self.employees[t] += short
                    self.capital -= short * ANNUAL_WAGE.get(t, 375.0) * self.price_index
            self._resync_pools()
        self.directors_extra += (di_cap - self.directors_extra) * 0.12 - self.directors_extra * ATTRITION
        self.artisans = max(0.0, self.artisans)
        self.scholars = max(0.0, self.scholars)
        self.directors_extra = max(0.0, self.directors_extra)

        # 2. money
        self.economy = self.economy_index()
        lc = self.living_cost()
        self.living_cost_paid += lc
        mo = self.mine_operating_cost()
        self.mine_cost_paid += mo
        self.capital += self.revenue() - self.upkeep() - lc - mo
        # A mine you cannot pay for is a mine you stop working. Without this the
        # opex accrued for ever against a bankrupt enterprise: the England run
        # sank a large mine, lost its revenue and then ran three centuries at
        # minus four million denarii, unable to afford anything at all, which
        # the log reported as being "blocked" on a treadle lathe.
        if self.capital < 0 and self.mine_capacity and self.policy.get("auto_mothball", True):
            self.mothball_mines()
        self.charge_interest(yr)
        if self.policy.get("auto_shed", True):
            self.shed_loss_makers(yr)
        self.enforce_credit_limit(yr)

        # INSOLVENCY. A playtester ran to minus 4.12 million denarii over eighty
        # years and nothing whatever happened: no event, no block, no attrition.
        # That is not a hard game made easy, it is an accounting fiction, and it
        # quietly made every cost in the model optional.
        #
        # The consequence is deliberately the realistic one rather than a
        # dramatic one. Nobody arrests you for debt. What happens is that people
        # you cannot pay stop turning up, and nobody will extend you credit for
        # something new while you are in arrears.
        if self.capital < 0:
            self.insolvent_years = getattr(self, "insolvent_years", 0) + 1
            floor = -max(4000.0, self.revenue() * 2.0)
            if self.capital < floor and self.insolvent_years >= 3:
                # wages unpaid: freedmen leave first, they are free to
                # A FLOOR, because the first version was a doom loop. Staff bled
                # without limit, so fewer people earned less, which deepened the
                # arrears, which bled more people. One Norse run sat insolvent
                # for 495 years with 2.9 artisans left, unable to recover and
                # unable to end. Insolvency should cost you your expansion, not
                # trap you in a state you can never leave: a household that has
                # shed everything also stops paying for it, and can climb back.
                bleed = min(0.15, 0.04 * self.insolvent_years)
                self.artisans = max(3.0, self.artisans * (1.0 - bleed))
                self.scholars = max(1.0, self.scholars * (1.0 - bleed * 0.6))
                if self.insolvent_years in (3, 6, 12, 25):
                    self.log.append((yr, "IN ARREARS for %d years: staff are leaving "
                                         "because you cannot pay them" % self.insolvent_years))
                # ABANDONMENT, and this is what makes insolvency survivable.
                # The failed Norse run carried 3,920 denarii of upkeep against
                # 3,134 of revenue: permanently underwater, floored at three
                # artisans, simulating 495 years of nothing and reporting it as
                # "ran out of horizon". An enterprise that cannot maintain its
                # works does not pay for them for five centuries. It lets them
                # go, and the buildings fall down. You lose what they gave you
                # and can rebuild later, which is a real cost and a real way out.
                net = (self.revenue() - self.upkeep() - self.living_cost()
                       - self.mine_operating_cost())
                # ONLY WORKS THAT COST MORE THAN THEY RETURN, and only if you let
                # it happen at all. Both halves were wrong and a tester called the
                # result "an unrecoverable softlock", correctly: the loop ran
                # until the books balanced rather than until shedding stopped
                # helping, so once the genuine loss-makers were gone it went on
                # to destroy eleven works earning 2,700 a year against 330 of
                # upkeep, each one making the deficit worse, for ever. And it did
                # it whether or not auto_shed was switched off, in a game whose
                # own help says "every one of them is a switch you control".
                if net < 0 and self.policy.get("auto_shed", True):
                    burden = sorted((k for k in self.done
                                     if self.nodes[k]["up"] > self.nodes[k]["rev"]
                                     and k not in self.granted
                                     and not self.never_abandon(k)),
                                    key=lambda k: (self.nodes[k]["rev"] - self.nodes[k]["up"]))
                    shed = []
                    for k in burden:
                        if net >= 0:
                            break
                        n = self.nodes[k]
                        net += n["up"] - n["rev"]
                        self.done.discard(k)
                        self.mothballed.add(k)   # you can buy it back
                        shed.append(k)
                    if shed:
                        # NAME THEM, for the same reason as shed_loss_makers and
                        # the creditors' seizure below: a bare count does not
                        # tell a player what they lost or why it later
                        # reappeared mothballed rather than gone for good.
                        self.log.append((yr, "ABANDONED %d works you could no longer "
                                             "maintain; they have fallen into disrepair: %s"
                                             % (len(shed), ", ".join(shed))))
        else:
            self.insolvent_years = 0
        # A standing workforce policy, and ONLY when the optimizer is playing.
        #
        # This used to run in manual mode too, so a player who never issued a
        # buy command watched `slaves` climb on its own with no prompt and no log
        # line. A tester caught it and put the objection better than I can: the
        # game's own justification for modelling slavery at all is that "a model
        # that hides it lies about the cost of everything", and then it was
        # hiding the acquisition. Buying people on someone's behalf without
        # telling them is the worst version of that.
        if self.policy.get("auto_buy_people", False):
            if self.capital > 6000 and self.artisans < 12 and self.has("workshop_first"):
                got = self.buy_slaves(min(6, int(self.capital // 1500)))
                if got:
                    self.log.append((yr, "bought %d people for the workshop" % got))
        if self.policy.get("auto_manumit", not self.manual) and self.slaves:
            if self.rng.random() < 0.25:
                freed = self.manumit(max(1, self.slaves // 4))
                if freed:
                    self.log.append((yr, "freed %d people" % freed))
        # currency debasement and war damage now come from the civilization's
        # own hazard list, not from Rome's dates baked into the engine
        if self.output_factor < 1.0:
            self.output_factor = min(1.0, self.output_factor + 0.006)

        # 3. dated shocks
        if self.events:
            self._shocks(yr)
            if self.dead_reason:
                return

        # 4a. Anything THIS SOCIETY already has costs nothing and takes nobody's
        #     attention. Grant it the moment its prerequisites are met instead of
        #     making it queue behind real work.
        #
        #     It used to say "anything ROME already has", and meant it: a Han
        #     playtester was handed civ_aqueduct_roman, civ_sewer_roman,
        #     civ_insula, fin_annona and fin_societas for free in year one. The
        #     annona is the Roman grain dole. Han China does not have one, and a
        #     model that gives every society Rome's institutions is not modelling
        #     societies at all.
        for k in self.order:
            n = self.nodes[k]
            if self._is_foreign_institution(k):
                continue
            if (n["tier"] == 0 and n["ph"] == 0 and n["_total_cost"] <= 1
                    and k not in self.done and k not in self.active
                    and all(p in self.done for p in n["pre"])):
                self.done.add(k)
                self.done_year[k] = self.year
                # This node is granted because THE SOCIETY already has it, not
                # because you built it. Rome having large merchant ships means
                # the ships exist, not that you own the fleet, so you do not
                # collect their revenue. Left unmarked, the 148 auto-granted
                # nodes paid the founder 11,650 den a year for existing, 8,000
                # of it from a merchant fleet belonging to other people.
                self.granted.add(k)

        # 4a2. TEACH THE TRADES THIS SOCIETY DOES NOT HAVE. The optimizer has to
        #      do this for itself or half the tree is unreachable; a player does
        #      it with `train`, or turns this on.
        if self.policy.get("auto_train", not self.manual):
            want = {}
            # Anything already in hand that has lost its trade comes FIRST: those
            # projects are burning a slot and will be halted if nobody turns up.
            for k in self.active:
                for t in self.nodes[k]["lab"]:
                    if self.market_supply(t) <= 0.0:
                        want[t] = want.get(t, 0) + 500
            # WORK THE PLAYER COULD START TODAY, not the whole tree. The old
            # test was "direct prerequisites satisfied", which is not "wanted":
            # it looked past cost, staff, state approval and every OTHER trade
            # a node needs, so it walked deep into the order training engineers,
            # then chemists, machinists and opticians, with no active project
            # asking for any of them. Its own description promises "when a
            # project needs them", and a project three tiers away with money
            # you do not have is not a project you need anything for yet.
            # ignore_trade asks the one question that answers that: if this
            # trade existed, would everything ELSE already let it start?
            for k in self.order:
                if k in self.done or k in self.active:
                    continue
                n = self.nodes[k]
                if not any(not self.trade_available(t) for t in n["lab"]):
                    continue
                if not self.start_reason(k, ignore_trade=True)[0]:
                    continue
                for t in n["lab"]:
                    if not self.trade_available(t):
                        want[t] = want.get(t, 0) + 1
            for t, _ in sorted(want.items(), key=lambda kv: -kv[1])[:1]:
                ok, _msg = self.train(t, 2)
                if ok:
                    self.log.append((yr, "you begin teaching the first %ss this world "
                                         "has ever had" % t))

        # 4b. start new projects
        pool = max(0.0, self.director_pool() - self.director_hours_committed())
        hired_left = self.hired_cap()
        # MANUAL MODE STOPS HERE. This loop is "the optimizer": it walks
        # `order` and starts whatever it judges best, which is exactly the
        # behaviour a free-choice player must NOT get. The old `play` command
        # let you type a node id, but that only did `order.remove/insert(0)`
        # a few lines above this loop's own input; the loop then ran anyway
        # and started other things you never asked for. `self.manual` cuts
        # that off at the root: nothing is ever added to `self.active` here,
        # so the only way anything starts is start_project(), called by a
        # human or a script. Everything below this block (materials, staff,
        # money, hazards, the calendar) is untouched by `manual` and keeps
        # running exactly as before.
        if not self.manual and yr >= getattr(self, "credit_frozen_until", 0):
            # More directors means more things in hand at once, and a big trained staff
            # lets routine work proceed without the founder watching it.
            # How many things can be in hand at once. I tried doubling this on
            # the theory that money is now the real constraint and attention need
            # not stand in for a budget. It made every civilization worse,
            # including Rome, from 33% of runs reaching the transistor to none:
            # more projects in hand divide the same purse into smaller annual
            # payments, so everything crawls and nothing finishes. Spreading a
            # fixed budget across more work is not more work. Left as it was.
            max_active = int(2 + self.director_pool() / 2400.0
                             + self.scholars / 12.0 + self.artisans / 25.0)
            # EARN A LIVING FIRST. Now that a project must actually be paid for,
            # a founder who arrives with 400 denarii and walks the goal-ordered
            # list starves: every human tester worked this out for themselves
            # within a few turns and went hunting for the cheap revenue nodes,
            # and the optimizer had no such instinct. When the surplus is thin,
            # prefer whatever pays best for what it costs; the goal order resumes
            # the moment there is money to pursue it with.
            fixed0 = self.upkeep() + self.living_cost() + self.mine_operating_cost()
            candidates = self.order
            if self.revenue() - fixed0 < max(400.0, fixed0 * 0.25):
                earners = [k for k in self.order
                           if self.nodes[k]["rev"] - self.nodes[k]["up"] > 0]
                earners.sort(key=lambda k: self.project_cost(k)
                             / max(1.0, self.nodes[k]["rev"] - self.nodes[k]["up"]))
                candidates = earners + [k for k in self.order if k not in set(earners)]
            for k in candidates:
                if len(self.active) - len(self.bountied & set(self.active)) >= max_active:
                    break
                if not self.can_start(k):
                    continue
                n = self.nodes[k]
                # do not start something we cannot plausibly fund this decade.
                # material_cost_factor is geography.json's contribution: a
                # located material (mat_gutta_percha and the like) costs more
                # or less to reach depending on how far THIS civ actually is
                # from it, not on Rome's distance to it.
                # Do not begin what you cannot pay for. This used to allow three
                # times your capital plus six years of GROSS revenue, which was
                # harmless while the money was notional and the bill was quietly
                # forgiven at completion. Now that the bill has to be paid, the
                # same heuristic commits the household to more than it can ever
                # fund, the creditors halt everything, and the spend is lost.
                fixed = self.upkeep() + self.living_cost() + self.mine_operating_cost()
                room = (max(0.0, self.capital) + self.credit_limit() * 0.5
                        + max(0.0, self.revenue() - fixed) * 5.0
                        - sum(st.get("cost_left") or 0.0 for st in self.active.values()))
                if self.project_cost(k) > room:
                    continue
                if k in self.bounty_set and self.bounty_eligible(k) and self.post_bounty(k):
                    continue
                self.active[k] = dict(ph_left=float(n["ph"]), yrs=0.0, spent=0.0,
                                      cost_left=self.project_cost(k))

        # 4c. materials. Buy the woodland and dig the beds BEFORE the shortage
        #     bites, which is what a competent manager does and what the old
        #     model never had to think about at all.
        self.commission_mines()
        thr = self.resource_throttle()
        if (thr < 0.9 and self.capital > 3000
                and (self.policy.get("auto_mine", not self.manual)
                     or self.policy.get("auto_forest", not self.manual))):
            # Charcoal is GROWN, so the answer is woodland. Everything else in
            # this list is DUG, so the answer is a mine, and the old model had
            # no answer at all for coal: the binding constraint fell through
            # both branches and the run simply sat throttled. That is why coal
            # showed 1,669 shortage-years in a 395 year run.
            if self.binding == "charcoal":
                if self.policy.get("auto_forest", not self.manual):
                    self.buy_forest(min(400.0, self.capital / 900.0))
            elif (self.binding in self.MINE_CAPEX_PER_T_YR
                    and self.policy.get("auto_mine", not self.manual)):
                # Size the mine from ALL the material keys that feed this
                # bucket, not one of them. The throttle counted iron ore AND
                # iron bar against "iron"; the investment response looked only
                # at iron bar. A run needing 10,330 tonnes of ore a year sank a
                # mine sized for the 13 tonnes of bar, stayed throttled for
                # centuries, and ended with its capital untouched.
                dem = self.annual_material_demand()
                keys = {"coal": ("coal_kg",),
                        "iron": ("iron_bar_kg", "iron_ore_kg"),
                        "copper": ("copper_kg",), "lead": ("lead_kg",),
                        "tin": ("tin_kg",), "silver": ("silver_kg",)}[self.binding]
                short = sum(dem.get(kk, 0.0) for kk in keys)
                want = max(0.0, short - self.mine_capacity.get(self.binding, 0.0))
                self.open_mine(self.binding, min(want, self.capital * 0.25
                                                 / max(1.0, self.MINE_CAPEX_PER_T_YR[self.binding])))
                # Iron and the base metals are smelted with charcoal, so the
                # ore is only half the answer.
                if self.binding in ("iron", "copper", "lead"):
                    self.buy_forest(min(200.0, self.capital / 1800.0))
            elif self.binding == "saltpetre":
                spend = min(self.capital * 0.05, 2000)
                self.capital -= spend
                self.nitre_bed_m2 += spend / 2.0
        if thr < 0.6 and self.binding:
            self.log.append((yr, "SHORT OF %s: work running at %d%% of plan"
                             % (self.binding.upper(), thr * 100)))

        # 5. progress. Director hours go to the HIGHEST-PRIORITY active projects
        #    first, not spread evenly: a director who gives every project equal
        #    attention finishes nothing, which is a real failure mode but not the
        #    one we are trying to model here.
        rank = {k: i for i, k in enumerate(self.order)}
        active_sorted = sorted(self.active, key=lambda k: rank.get(k, 9999))
        remaining = pool
        self.trade_hours_used = {}
        # Summed as the loop runs, not re-read from self.active afterwards,
        # because a project that completes THIS year is popped from
        # self.active before we would get to it. See the hours_this_year
        # summary this feeds, below the loop.
        hours_effective_total = 0.0
        for k in active_sorted:
                st = self.active[k]
                n = self.nodes[k]
                # IS THERE ANYBODY TO DO THE WORK? If a trade this project needs
                # has vanished since it started (the machinists you taught died
                # out, say), nothing can be done on it this year, and your own
                # hours should go somewhere they are useful rather than into a
                # project that cannot absorb them.
                #
                # This matters more than it sounds. Without it a project whose
                # trade had disappeared sat in `active` for ever: hours went in,
                # no money was spent because no work was done, so the bill was
                # never paid, so it could never complete, so it never released
                # the slot. Four of those deadlocked a run at 98 technologies for
                # two hundred and fifty years.
                blocked = [t for t, want in n["lab"].items()
                           if want > 0 and self.market_supply(t) <= 0.0]
                if blocked:
                    st["stalled_years"] = st.get("stalled_years", 0) + 1
                    if st["stalled_years"] >= 4:
                        self.log.append((yr, "HALTED %s: there is nobody here who can "
                                             "do this work (%s). What you spent is lost"
                                         % (k, ", ".join(blocked[:2]))))
                        self.active.pop(k, None)
                        self.bountied.discard(k)
                    continue
                st["stalled_years"] = 0
                per = min(remaining, max(st["ph_left"], n["ph"] / max(n["yrs"], 1.0))) * self.throttle
                remaining -= per
                st["ph_left"] = max(0.0, st["ph_left"] - per)
                self.director_hours_spent_founder += per if self.founder_alive else 0
                # Hours OFFERED this year vs hours that actually did anything.
                # `refunded` tracks the difference: hours credited back to
                # ph_left below because a trade or the money to pay for it
                # fell short. Four projects each showed EXACTLY HALF their
                # founder hours left after one year and a tester called it
                # "confusing and feels artificial" - it was: nothing told them
                # `per` had been offered in full and half of it handed straight
                # back. See hours_this_year in `state`.
                st["hours_offered_this_year"] = round(per, 1)
                refunded = 0.0
                st["yrs"] += 1
                frac = min(1.0, 1.0 / max(1.0, n["yrs"]))
                # A project started before this field existed (an old save) has
                # no bill to pay; give it one now rather than crash on it.
                if st.get("cost_left") is None:
                    st["cost_left"] = max(0.0, self.project_cost(k) - st["spent"])
                # material_cost_factor: how far THIS civilization is from
                # wherever geography.json says this thing actually comes
                # from. 1.0 for every node that is not a located material.
                money = min(st["cost_left"], self.project_cost(k) * frac)
                # LABOUR BY TRADE. The old model pooled every trade into one
                # bucket of hired hours, so 450 hours of engineer and 450 hours
                # of labourer were the same resource. They are not, and the wage
                # table has said so all along. What binds now is the scarcest
                # trade this project actually needs.
                hh = n["_hired_hours"] * frac
                worst = 1.0
                for t, want in n["lab"].items():
                    need = want * frac
                    if need <= 0:
                        continue
                    have = (self.market_supply(t) + self.contract_hours.get(t, 0.0)
                            - self.trade_hours_used.get(t, 0.0))
                    if need > have:
                        worst = min(worst, max(0.0, have) / need)
                if worst < 1.0:
                    frac *= worst
                    money *= worst
                    hh *= worst
                    give_back = per * 0.4 * (1.0 - worst)
                    st["ph_left"] += give_back
                    refunded += give_back
                    # Remember it. A tester sat on 696,350 denarii watching three
                    # projects report waiting_on "money" with 2.3, 84 and 158
                    # denarii left to pay, and reasonably concluded the spend cap
                    # was broken. It was not: the trades those projects needed
                    # were fully booked, so almost nothing could be paid FOR. The
                    # mechanic was right and the label was a lie.
                    st["short_of_trade"] = sorted(
                        t for t, wnt in n["lab"].items()
                        if wnt > 0 and (self.market_supply(t)
                                        + self.contract_hours.get(t, 0.0)
                                        - self.trade_hours_used.get(t, 0.0)) < wnt * frac)[:3]
                else:
                    st.pop("short_of_trade", None)
                for t, want in n["lab"].items():
                    self.trade_hours_used[t] = (self.trade_hours_used.get(t, 0.0)
                                                + want * frac)
                if hh > hired_left:
                    frac *= hired_left / max(hh, 1e-9)
                    money *= hired_left / max(hh, 1e-9)
                    hh = hired_left
                hired_left -= hh
                # You may spend into debt, up to what someone will lend you, and
                # no further. Beyond that the work simply does not get paid for
                # this year, and a year nobody was paid for is a year of little
                # progress. What must NOT happen is the bill being forgiven.
                #
                # The margin is deliberate. Spending to the last denarius of your
                # credit means next year's rent breaches the limit and the
                # creditors halt every project you have, which turns "I was
                # ambitious" into "everything I had in hand was destroyed". A
                # lender who will advance you a thousand will not let you draw
                # the last two hundred of it against a half-built balloon.
                # Reserve next year's fixed costs AND most of the credit line.
                # Drawing the line to its last denarius is how one ambitious
                # project destroyed everything else a tester had in hand: the
                # limit itself falls as reputation and revenue fall, so a balance
                # exactly at the limit this year is over it next year, and over
                # the line every project in progress is halted at once.
                # Reserve only the SHORTFALL, not the whole running cost. This
                # year's rent and wages have already been taken out of capital at
                # the top of step(); reserving them again left a household with
                # 6,670 in hand and 31,000 of costs covered by 31,600 of income
                # unable to spend a single denarius on its own projects, so four
                # of them sat unpayable and unfinished for two hundred years.
                fixed = self.living_cost() + self.upkeep() + self.mine_operating_cost()
                reserve = max(0.0, fixed - self.revenue())
                purse = self.capital + self.credit_limit() * 0.6 - reserve
                if money > purse:
                    # PROPORTIONAL, not a flat half. This used to refund
                    # exactly per*0.5 whenever the purse fell short AT ALL,
                    # whether by one denarius or by the whole bill, which is
                    # what produced the "exactly half" a tester flagged as
                    # arbitrary-looking: four unrelated projects each showing
                    # precisely half their founder hours left after one year
                    # is not a coincidence, it is this constant. A project
                    # funded to 95% of what it needed lost the same fixed
                    # half of its hour's progress as one funded to 5%; the
                    # trade-shortage case two blocks up already scales its
                    # refund by how much of the need went unmet (worst), and
                    # this should too.
                    funded_frac = 0.0 if money <= 0 else max(0.0, min(1.0, purse / money))
                    money = max(0.0, purse)
                    give_back = per * (1.0 - funded_frac)
                    st["ph_left"] += give_back
                    refunded += give_back
                    st["underfunded_this_year"] = True
                else:
                    st.pop("underfunded_this_year", None)
                self.capital -= money
                self.total_spend += money
                st["spent"] += money
                st["cost_left"] = max(0.0, st["cost_left"] - money)
                st["hours_effective_this_year"] = round(max(0.0, per - refunded), 1)
                hours_effective_total += st["hours_effective_this_year"]
                # Count it HERE, after the hired-hours scaling and the
                # affordability clamp, not before them. Accumulating the
                # notional figure made project_spend_last_year disagree with
                # the actual capital movement by a factor of 89, which a tester
                # caught by comparing three numbers in a single `state` reply.
                self._spend_this_year = getattr(self, "_spend_this_year", 0.0) + money
                floor = n["yrs"]
                if n["yrs"] >= 5:   # diffusion-limited nodes, not physical curing
                    floor = max(2.0, n["yrs"] / (1.0 + self.reputation / 90.0))
                # THE BILL HAS TO BE PAID. Hours done and years elapsed are not
                # enough; if the money never arrived, the thing was never built.
                if st["ph_left"] <= 0 and st["yrs"] >= floor and st["cost_left"] <= 0.5:
                    self._complete(k)
                elif st["ph_left"] <= 0 and st["yrs"] >= floor and st["cost_left"] > 0.5:
                    st["waiting_on_money"] = True

        # Snapshot BEFORE 5b spends more of `remaining` on wage work: otherwise
        # offered_to_projects below double-counts wage hours as though they had
        # been offered to projects too, since 5b draws from the same pool.
        remaining_after_projects = remaining

        # 5b. IF THERE IS NO WORK AND NO MONEY, TAKE A JOB. A man who arrives
        #     with four hundred denarii and a lens does not sit watching his
        #     savings run out; he teaches, or writes, or sets bones for money. It
        #     is in the protocol as `work` for a player and the optimizer had no
        #     equivalent, so a single bad year in the opening decade could end a
        #     run: one Rome seed earned four technologies in five hundred years
        #     because a fire in 103 took a fifth of everything it had.
        if (not self.manual and remaining > 100.0
                and (self.capital < self.living_cost() * 2 or not self.active)):
            trade = ("scholar" if self.effective_scholars() >= 1 else "scribe")
            hours = min(remaining, 1200.0)
            _, err = self.work_for_wages(trade, hours)
            # Kept in step with `remaining` so hours_this_year (below) does not
            # count hours sold for wages here as still unused.
            if err is None:
                remaining -= hours

        # 6. reputation, familiarity, protection, scandal
        #
        # Reputation DECAYS TOWARD WHAT YOU ARE ACTUALLY KNOWN FOR, not toward
        # zero. Three testers independently reported the same thing: reputation
        # slid from 10 to 0.2 over a century and a half with no event ever
        # explaining it, and one called it "less like a lever I could manage and
        # more like a clock running out in the background". They were right, and
        # decaying to zero was also wrong on its own terms. A physician with a
        # practice, a school and a written corpus does not become a man nobody
        # has heard of because thirty quiet years passed. What fades is novelty;
        # what remains is the work.
        floor = self.standing_floor()
        self.reputation = floor + (self.reputation - floor) * 0.97
        # ADAPTATION. Every year the world has known you, and every visible thing
        # you have already done, makes the next one less astonishing.
        pub = sum(1 for k in self.done
                  if set(self.nodes[k].get("traits", [])) & {"spectacle", "inexplicable"})
        self.familiarity = min(0.9, 1.0 - math.exp(-self.w["adaptation_rate"] *
                                                   (0.5 * pub + 0.25 * (self.year - 100))))
        # WHERE THE YEAR'S HOURS WENT. Four projects each showed exactly half
        # their founder hours left after one year, with 2,400 available and
        # only about 200 apparently spent, and a tester had no way to see why:
        # nothing in `state` accounted for a year's hours at all. Captured
        # here, before the tallies below reset for the next year, the same way
        # spend_last_year already captures the year's spending. See it as
        # `hours_this_year` in `state`.
        self.hours_this_year = {
            "available": round(self.director_pool(), 1),
            "wage_work": round(getattr(self, "wage_hours_this_year", 0.0), 1),
            "teaching": round(getattr(self, "teaching_hours_this_year", 0.0), 1),
            "offered_to_projects": round(max(0.0, pool - remaining_after_projects), 1),
            # OFFERED is what projects were given a shot at; EFFECTIVE is what
            # actually reduced their founder_hours_left. The gap between the
            # two is hours that went in and came straight back out again
            # because a trade or the money to pay for it fell short that year
            # - see hours_offered_this_year / hours_effective_this_year on
            # each project in `active`, and underfunded_this_year.
            "effective_on_projects": round(hours_effective_total, 1),
            "unused": round(max(0.0, remaining), 1),
        }
        # Reset AFTER the progress pass above, which is where the hours you sold
        # are subtracted from the hours you have left to direct.
        self.wage_hours_this_year = 0.0
        # Contracted work is bought for a year and expires with it: hours you
        # paid a shop for in 142 are not still sitting there in 143.
        self.contract_hours = {}
        self.teaching_hours_this_year = 0.0
        self.spend_last_year = getattr(self, "_spend_this_year", 0.0)
        self._spend_this_year = 0.0
        # Sellers restock, so the pressure your buying put on the market fades.
        self.market_pressure = max(0.0, getattr(self, "market_pressure", 0.0) * 0.55 - 2.0)
        # People bought this year are not artisans this year.
        if self.training:
            still = []
            for row in self.training:
                cap, ready = row[0], row[1]
                trade = row[2] if len(row) > 2 else None
                count = row[3] if len(row) > 3 else 0.0
                if self.year >= ready:
                    if trade:
                        # A trade you taught. They are now yours to pay, and
                        # they are that trade and no other.
                        self.employees[trade] = self.employees.get(trade, 0.0) + count
                        self.log.append((self.year, "%g %s%s finish their training"
                                         % (count, trade, "s" if count != 1 else "")))
                        self._resync_pools()
                    else:
                        self.artisans += cap
                else:
                    still.append(row)
            self.training = still
        self.update_protection()
        self.scandal *= 0.90
        # Eminence accumulates in a SEPARATE pool, because bribery does not
        # touch it. You can buy a magistrate, an accuser and a jury. You cannot
        # buy an emperor's judgement that you have grown too large, and the
        # attempt is itself evidence against you.
        self.eminence = self.eminence * 0.93 + self.prominence_hazard()
        # you can buy your way out of trouble, and a sane player does
        if self.scandal > 8 and self.capital > 2000 and self.policy.get("auto_bribe", not self.manual):
            spend = min(self.capital * 0.12, self.scandal * 260)
            self.capital -= spend
            self.bribes_ytd = 0.7 * self.bribes_ytd + spend
            self.scandal -= spend / 300.0 * self.w["bribability"]
        else:
            self.bribes_ytd *= 0.7
        self.scandal = max(0.0, self.scandal)
        if self.events and self.scandal > c["suspicion_danger"]:
            p = (self.scandal - c["suspicion_danger"]) / 60.0
            if self.rng.random() < p:
                self._catastrophe("denounced: %s" % ("as a sorcerer" if self.w["w_magic_fear"] > 0.5
                                                     else "as a subversive"))
        # The eminence hazard is separate and unbribable. Its usual outcome is a
        # bad year rather than a death: a confiscation, a patron destroyed in
        # someone else's quarrel, a forced withdrawal from public life.
        if self.events and self.eminence > c["eminence_danger"]:
            p = (self.eminence - c["eminence_danger"]) / 90.0
            if self.rng.random() < p:
                roll = self.rng.random()
                if roll < 0.45:
                    take = self.capital * 0.55
                    self.capital -= take
                    self.reputation = max(0.0, self.reputation - 18)
                    self.eminence *= 0.45
                    self.log.append((yr, "PROMINENCE: property confiscated, %d den lost, "
                                         "and you withdraw from public life for a while" % take))
                elif roll < 0.80:
                    for pat in ("patron_imperial", "patron_senatorial"):
                        if pat in self.done:
                            self.done.discard(pat)
                            self.log.append((yr, "PROMINENCE: your patron is destroyed in "
                                                 "someone else's quarrel and you lose %s" % pat))
                            break
                    self.eminence *= 0.5
                    self.reputation = max(0.0, self.reputation - 10)
                else:
                    self._catastrophe("too eminent: brought down not for what you built "
                                      "but for how large you had become")

        # 6b. serving out a debt. The hours you owe go to the creditor and the
        #     debt falls; when it is done you are free, and you keep everything
        #     you know.
        if self.bondage_years_left > 0:
            self.bondage_years_left -= 1
            paid = self.cfg["founder_hours_per_year"] * 0.75 * \
                (WAGES.get("labourer", 0.075) * 1.2) * self.wage_index * self.price_index
            self.bondage_debt = max(0.0, self.bondage_debt - paid)
            if self.bondage_debt <= 0 and self.bondage_years_left > 0:
                self.bondage_years_left = 0     # paid early
            if self.bondage_years_left <= 0:
                self.bondage_years_left = 0.0
                self.bondage_debt = 0.0
                self.log.append((yr, "your term is served and the debt is discharged; "
                                     "you are your own man again"))

        # 7. founder mortality
        if self.founder_alive:
            self.life_left -= 1
            if self.has("sanitation_antisepsis"):
                self.life_left += 0.12      # you at least do not die of a septic cut
            if self.life_left <= 0:
                self.founder_alive = False
                self.log.append((yr, "the founder dies, aged about %d"
                                 % (self.cfg["founder_arrival_age"] + yr - self.cfg["start_year"])))
        # a programme with no director is not paused, it is dissolving
        if not self.founder_alive and self.directors_extra < 0.5:
            self.stalled += 1
            if self.stalled >= 3:
                losable = sorted(k for k in self.done if self.nodes[k]["tier"] >= 2)
                # sorted() matters: self.done is a SET, and a set iterates in an
                # order that depends on PYTHONHASHSEED, so feeding it unsorted to
                # rng.sample made the same --seed give a different answer on every
                # invocation. Every figure this project has reported was, strictly,
                # unreproducible.
                if losable:
                    for k in self.rng.sample(losable, max(1, len(losable) // 6)):
                        self.done.discard(k)
            if self.stalled >= 12:
                self._catastrophe("the founder died without training successors; "
                                  "the school dispersed and the work was forgotten")
        else:
            self.stalled = 0

        # 8. random events
        if self.events and not self.dead_reason:
            self._random_events(yr)

        self.year += 1

    def _complete(self, k):
        n = self.nodes[k]
        if self.rng.random() < n["risk"]:
            self.failed_attempts[k] += 1
            self.active[k]["ph_left"] = n["ph"] * 0.4
            self.active[k]["yrs"] = 0.0
            self.capital -= n["_total_cost"] * 0.4 * self.cost_money_factor()
            return
        del self.active[k]
        self.bountied.discard(k)
        self.done.add(k)
        self.done_year[k] = self.year
        # A technology changes the society that built it. Only for work YOU
        # completed: a society is not altered by owning something it always had.
        self.apply_tech_effects(k)
        self.reveal_from(k)
        # Visible, useful, State-approved work builds standing. Obscure laboratory
        # work does not, however important it is, which is a real and annoying fact
        # about how credibility actually accrues.
        gain = (0.6 + 0.5 * max(0.0, self.state_interest(n))
                + (1.2 if n["rev"] > 0 else 0.0) + 0.25 * n["tier"])
        self.reputation = min(100.0, self.reputation + gain)
        self.scandal += self.alarm_of(n)
        self.gov += self.state_interest(n)
        if k == "freedman_staff":     self.artisans += 8
        if k == "school_founded":     self.scholars += 4
        if k == "academy_network":    self.scholars += 10; self.artisans += 10
        if k == "mining_concession":  pass
        self.log.append((self.year, "completed: " + n["name"]))
        if k == self.goal and self.goal_year is None:
            self.goal_year = self.year

    # -- shocks -------------------------------------------------------------
    # WHAT YOU CAN DO ABOUT HISTORY.
    #
    # A tester's question, and it is the right one to ask of a game that tells
    # you on turn one exactly which disasters are coming: "some techs might
    # counter that, like what if you build a mine that can mine gold for Rome,
    # or guns for a rebellion, or medicine for disease?" Until now the answer
    # was almost no: four hardcoded checks, none of them findable, and the
    # hazards were weather. They are not weather. They are the thing the whole
    # programme is for.
    #
    # Each entry is (node id, how much of the harm it removes, what it is).
    # They compound, and none of them takes a hazard to zero on its own: no
    # amount of sanitation stops a plague, it decides how many of your people
    # are still alive at the end of it.
    HAZARD_COUNTERS = {
        "staff_loss": [
            ("sanitation_antisepsis", 0.30, "boiled water, handwashing, clean wounds"),
            ("med_quarantine_sanitation", 0.30, "quarantine, clean water, sewage"),
            ("germ_theory", 0.25, "knowing what is actually killing them"),
            ("md2_isolation_hospital", 0.20, "the sick kept apart from the well"),
            ("med_vaccination_progression", 0.45, "variolation and then vaccination"),
            ("md2_vaccine_smallpox", 0.40, "smallpox vaccine"),
            ("md2_vaccine_plague", 0.35, "plague vaccine"),
            ("md2_vaccine_typhoid", 0.20, "typhoid vaccine"),
            ("md2_sand_filtration", 0.15, "filtered water"),
            ("soap_hard", 0.10, "hard soap, in quantity"),
            ("med_nursing_profession", 0.12, "people trained to nurse the sick"),
            ("plague_preparedness", 0.35, "a plan made before the plague"),
            ("crop_rotation", 0.15, "fields that do not fail together"),
            ("ag2_silage_silo", 0.10, "fodder that keeps through a bad winter"),
            ("fud_canning_appert_method", 0.10, "food that keeps"),
        ],
        "sack_chance": [
            ("mil_trace_italienne", 0.45, "angled bastion walls no ram or ladder answers"),
            ("mil_bastion", 0.30, "a bastioned enclosure"),
            ("mil_concrete_fortification", 0.30, "concrete fortification"),
            ("mil_matchlock", 0.25, "firearms in the hands of your own people"),
            ("mil_flintlock", 0.35, "reliable firearms"),
            ("mil_artillery_piece", 0.30, "guns on the walls"),
            ("gunpowder", 0.15, "corned powder"),
            ("patron_imperial", 0.30, "a patron with soldiers"),
            ("academy_network", 0.40, "the work is in too many places to burn"),
            ("endowment_land", 0.15, "land nobody can carry away"),
        ],
        "output_factor": [
            ("endowment_land", 0.30, "land that yields whoever is emperor this year"),
            ("crop_rotation", 0.20, "you feed yourself"),
            ("water_power_scale", 0.20, "power that does not come by ship"),
            ("civ_road_paved", 0.10, "your own roads"),
            ("fin_marine_insurance", 0.15, "losses spread rather than borne"),
        ],
        "real_erosion": [
            ("_own_gold", 0.55, "your own gold, dug not minted"),
            ("_own_silver", 0.35, "your own silver"),
            ("endowment_land", 0.40, "wealth held as land, not as coin"),
            ("fin_bimetallism", 0.25, "a standard the coin can be held to"),
            ("fin_assay_office", 0.20, "you can prove what metal is in a coin"),
            ("met_fire_assay", 0.15, "you can assay ore and coin yourself"),
        ],
    }

    def hazard_relief(self, kind):
        """How much of one kind of harm the things you have built take off.

        Returns (multiplier, [what did it]). Diminishing: each counter removes a
        share of what is LEFT, so five partial answers are strong and none of
        them is a switch that turns history off.
        """
        mult, why = 1.0, []
        for node, share, label in self.HAZARD_COUNTERS.get(kind, ()):
            if node == "_own_gold":
                got = self.mine_capacity.get("gold", 0.0) > 0.0005
            elif node == "_own_silver":
                got = self.mine_capacity.get("silver", 0.0) > 0.01
            else:
                got = self.has(node)
            if got:
                mult *= (1.0 - share)
                why.append(label)
        return mult, why

    def hazard_advice(self, kind):
        """What KIND of thing would help, without naming what you cannot see.

        Under fog this must not turn into a list of node ids to go and build:
        that is the tech tree by the back door. It names the kind of answer, in
        the same words a person in the year 100 would use.
        """
        words = {"staff_loss": "clean water, quarantine, and eventually inoculation",
                 "sack_chance": "walls, firearms, powerful friends, and copies of "
                                "your work kept somewhere else",
                 "output_factor": "land and power of your own, and not depending on "
                                  "trade that a war can cut",
                 "real_erosion": "metal you dug yourself, land, and a way to prove "
                                 "what a coin contains"}
        mult, why = self.hazard_relief(kind)
        out = {"you_currently_take": round(mult, 3), "because_of": why}
        if mult > 0.75:
            out["what_would_help"] = words.get(kind, "")
        return out

    def _shocks(self, yr):
        """Dated catastrophes, read from the CIVILIZATION file.

        Rome gets the Antonine plague and the third century crisis. England 1300
        gets the Great Famine and the Black Death. The Mexica get the contact
        epidemics, which are the most severe hazard in the whole directory and
        are not a fair fight. None of it is hardcoded here any more.
        """
        r = self.rng
        prep = self.has("plague_preparedness")
        for h in self.civ.get("hazards", []):
            a, b = h.get("years", [0, 0])
            if not (a <= yr <= b):
                continue
            if "staff_loss" in h and r.random() < 0.32:
                relief, why = self.hazard_relief("staff_loss")
                loss = h["staff_loss"] * relief
                self.scholars *= (1 - loss); self.artisans *= (1 - loss)
                for t in list(self.employees):
                    self.employees[t] *= (1 - loss)
                self.directors_extra *= (1 - loss); self.capital *= (1 - loss * 0.6)
                self.log.append((yr, "%s: staff -%d%%%s" % (h.get("name","hazard"),
                                 loss * 100,
                                 " (would have been -%d%%: %s)"
                                 % (h["staff_loss"] * 100, "; ".join(why)) if why else "")))
            if "sack_chance" in h:
                relief, why = self.hazard_relief("sack_chance")
                p = h["sack_chance"] * relief
                if why and r.random() < h["sack_chance"] - p:
                    self.log.append((yr, "%s: an attack comes to nothing (%s)"
                                     % (h.get("name", "crisis"), "; ".join(why[:3]))))
                if r.random() < p:
                    self.capital *= 0.40
                    self.artisans *= 0.55; self.scholars *= 0.55
                    self.directors_extra *= 0.65
                    for k in sorted(self.active):
                        self.active[k]["ph_left"] = self.nodes[k]["ph"]
                        self.active[k]["yrs"] = 0.0
                    self.log.append((yr, "%s: a site is sacked" % h.get("name","crisis")))
                    if self.has("corpus_dispersed"):   pl, frac = 0.12, 0.08
                    elif self.has("corpus_written"):   pl, frac = 0.45, 0.22
                    else:                              pl, frac = 0.80, 0.40
                    if r.random() < pl:
                        # sorted() matters: self.done is a SET and iterates in an
                        # order that depends on PYTHONHASHSEED, so feeding it
                        # unsorted to rng.sample made the same --seed give a
                        # different answer every invocation.
                        # Never the society's own inheritance: you can lose what
                        # YOU built, not what the civilization has always known.
                        losable = sorted(k for k in self.done
                                         if self.nodes[k]["tier"] >= 2
                                         and k not in self.granted)
                        if losable:
                            drop = r.sample(losable, max(1, int(len(losable) * frac)))
                            for k in drop: self.done.discard(k)
                            self.log.append((yr, "KNOWLEDGE LOST: %d technologies forgotten%s"
                                % (len(drop), "" if self.has("corpus_dispersed")
                                   else " (the corpus was never printed and dispersed)")))
            if "output_factor" in h:
                relief, _why = self.hazard_relief("output_factor")
                # relief moves the floor back toward 1.0 rather than scaling the
                # damage: self-sufficiency means less of your income was ever
                # coming through the thing the war cut.
                floor = 1.0 - (1.0 - h["output_factor"]) * relief
                before = self.output_factor
                self.output_factor = min(self.output_factor, floor)
                if before > self.output_factor:
                    self.log.append((yr, "%s: trade and output fall to %d%% of normal"
                                     % (h.get("name", "crisis"), self.output_factor * 100)))
            if "real_erosion" in h:
                relief, why = self.hazard_relief("real_erosion")
                self.money_real *= (1 - h["real_erosion"])
                bite = h["real_erosion"] * 0.85 * relief
                self.capital *= (1 - bite)
                if not getattr(self, "_said_debasement", 0) or yr - self._said_debasement >= 15:
                    self._said_debasement = yr
                    self.log.append((yr, "%s: the coin is worth %d%% less than it was%s"
                                     % (h.get("name", "debasement"),
                                        (1 - self.money_real) * 100,
                                        "; you feel less of it (%s)" % "; ".join(why)
                                        if why else "")))

    def _random_events(self, yr):
        r = self.rng
        # A patron dies ONCE and then you have courted his heir. The old model
        # rolled 4% every year forever, so a long run logged the same line six
        # times, which is not how having a patron works.
        if (r.random() < 0.05 and self.has("patron_local")
                and yr - getattr(self, "_last_patron_death", -99) > 25):
            self.last_patron_death = yr
            self.scandal += 4
            self.protection *= 0.6
            self.capital -= 800
            self.log.append((yr, "your patron dies; his heir must be courted afresh"))
        if r.random() < 0.03:
            self.capital *= 0.82
            # An insula is a Roman tenement block, and a tester playing Han China
            # counted nine fires in the insula district of Luoyang in a hundred
            # years. Every civilization file names its own quarter.
            self.log.append((yr, "fire in the %s"
                             % self.civ.get("fire_quarter", "crowded quarter")))
        if r.random() < 0.02:
            self.capital *= 0.9
            self.log.append((yr, "banditry or a frontier war disrupts supply"))

    def _catastrophe(self, why):
        self.dead_reason = why
        self.log.append((self.year, "RUN ENDS: " + why))

    # -- driver -------------------------------------------------------------
    def run(self, goal, horizon=None):
        self.goal = goal
        self.done_year = {}
        horizon = horizon or self.cfg["horizon_years"]
        end = self.cfg["start_year"] + horizon
        while self.year < end and not self.dead_reason and self.goal_year is None:
            self.step()
        return self


# ----------------------------------------------------------------------------
# Strategies
# ----------------------------------------------------------------------------

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
    s = Sim(nodes, order, random.Random(a.seed), events=True, bounty_set=bounties,
            manual=a.manual)
    s.goal = goal; s.done_year = {}
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
    while s.year < 100 + (a.horizon or 400) and not s.dead_reason and not s.goal_year:
        cmd = input("[%d AD | %d den | you:%d hr | sch %.0f art %.0f | rep %.0f | susp %.0f] > "
                    % (s.year, s.capital, s.director_pool(), s.scholars, s.artisans,
                       s.reputation, s.suspicion)).strip()
        if cmd == "q": break
        if cmd == "n":
            before = set(s.done); s.step()
            for k in s.done - before: print("   completed:", nodes[k]["name"])
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

def _agent_end_reason(s):
    """None while the run is live; otherwise why it stopped, for state() and
    to refuse further start/stop/bounty/buy commands once it has."""
    end_year = getattr(s, "end_year", s.cfg["start_year"] + s.cfg["horizon_years"])
    if s.dead_reason:
        return s.dead_reason
    if s.goal_year:
        return "goal reached: %s completed in %d AD" % (s.goal, s.goal_year)
    if s.year >= end_year:
        # Under fog there IS no stated goal, so saying the player failed to reach
        # one is incoherent. A tester finished a 500 year run and was told they
        # had missed a goal they were never shown and had no way to set.
        if getattr(s, "fog", False):
            return ("the horizon at %d AD is reached. You built %d things of your "
                    "own. There was no target to hit; how far you got is the whole "
                    "of the result." % (end_year, len(s.done - s.granted)))
        return "ran out of horizon (%d AD) without reaching the goal" % end_year
    return None


def _agent_state(s, nodes, cmd=None):
    active = {}
    for k, st in s.active.items():
        n = nodes[k]
        bill = st.get("cost_left")
        if bill is None:
            bill = max(0.0, s.project_cost(k) - st["spent"])
        active[k] = {"name": n["name"], "founder_hours_left": round(st["ph_left"], 1),
                     "founder_hours_total": n["ph"], "years_in_progress": st["yrs"],
                     "spent": round(st["spent"], 1), "still_to_pay": round(bill, 1),
                     # A tester poured 1,200 hours into a project that was
                     # calendar-locked and could not use them, and only noticed by
                     # reading state closely. Say which of the three things it is
                     # actually waiting for.
                     "waiting_on": (
                         ("nobody to do the work: " + ", ".join(st["short_of_trade"]))
                         if st.get("short_of_trade")
                         else "money" if st["ph_left"] <= 0 and bill > 0.5
                         else "the calendar" if st["ph_left"] <= 0
                         else "your hours"),
                     # WHERE THIS YEAR'S HOURS WENT, for this project specifically.
                     # offered is what step() gave it a shot at; effective is
                     # how much of that actually came off founder_hours_left.
                     # The two differ when a trade or the money for it fell
                     # short - see hours_this_year for the whole year's picture.
                     "hours_offered_this_year": st.get("hours_offered_this_year", 0.0),
                     "hours_effective_this_year": st.get("hours_effective_this_year", 0.0),
                     "underfunded_this_year": st.get("underfunded_this_year", False),
                     "bountied": k in s.bountied}
    end_reason = _agent_end_reason(s)
    full = bool((cmd or {}).get("full"))
    out = {
        "year": s.year, "capital": round(s.capital, 1), "revenue": round(s.revenue(), 1),
        "upkeep": round(s.upkeep(), 1),
        # A playtester watched capital fall 400 to 184 on the first step with
        # nothing active and both revenue and upkeep reported as zero, and no
        # field in the protocol explained where the money went. It went on food,
        # rent, tax and keeping up appearances, which the model has always
        # charged and never showed. Anything that moves your money should be
        # visible in the state that claims to describe your money.
        "living_cost": round(s.living_cost(), 1),
        "mine_operating_cost": round(s.mine_operating_cost(), 1),
        # net_per_year counts the STANDING flows only. It never counted what
        # projects consume, which is usually the largest outflow by far, so a
        # playtester watched it report a healthy positive number for eight
        # consecutive years while capital sat at exactly 0.0, every denarius
        # going into the work in progress. A field that says you are making
        # money while you are visibly making none is worse than no field.
        # Named for what it is. The roll happens after the spending loop, so this
        # is the year just simulated, not the one before it.
        "project_spend_this_year": round(getattr(s, "spend_last_year", 0.0), 1),
        "net_after_project_spend": round(s.revenue() - s.upkeep() - s.living_cost()
                                         - s.mine_operating_cost()
                                         - getattr(s, "spend_last_year", 0.0), 1),
        "net_per_year": round(s.revenue() - s.upkeep() - s.living_cost()
                              - s.mine_operating_cost(), 1),
        # Rows are [capacity, ready_year] for people bought and trained, and
        # [0, ready_year, trade, count] for a trade being taught, so read by
        # index. Unpacking two names off a four-wide row killed `state` outright
        # the moment anybody used `train`.
        "training_pending": [
            {"artisan_capacity": round(row[0], 2), "ready_year": row[1],
             "trade": (row[2] if len(row) > 2 else None),
             "people": (row[3] if len(row) > 3 else None)}
            for row in getattr(s, "training", [])],
        "founder_hours_available": round(s.director_pool(), 1),
        # LAST YEAR'S HOURS, ACCOUNTED FOR. Set in step(); see the comment
        # there. available is this year's fresh figure, not last year's -
        # read it alongside, not in place of, hours_this_year.
        "hours_this_year": getattr(s, "hours_this_year", None),
        "founder_alive": s.founder_alive,
        "scholars": round(s.scholars, 2), "artisans": round(s.artisans, 2),
        "directors_extra": round(s.directors_extra, 2),
        "reputation": round(s.reputation, 1), "suspicion": round(s.suspicion, 2),
        "scandal": round(s.scandal, 2), "eminence": round(s.eminence, 2),
        "protection": round(s.protection, 3), "familiarity": round(s.familiarity, 3),
        # A playtester could not tell the difference between technologies the
        # society already had and ones they had earned: about 140 nodes complete
        # in year one and appeared in done_count as if the player had built
        # them. Separate the two, because "you have 140 technologies" and "you
        # have built 3 technologies" are very different situations.
        "done_count": len(s.done),
        "done_granted": len(s.granted & s.done),
        "done_earned": len(s.done - s.granted),
        "active": active,
        # A tester spent 284 years with scholars frozen at 1.0 and artisans
        # plateaued, and wrote that they never found any way to grow either. The
        # remedy was only ever mentioned in a refusal message, so a player who
        # never happened to try a staff-gated project never saw it at all. Staff
        # is not a technical prerequisite, so it appears in no dependency list
        # either. Tell them unprompted.
        "how_to_grow_staff": {
            "scholars": s._staff_advice("scholars"),
            "artisans": s._staff_advice("artisans"),
        },
        "where_the_money_comes_from": s.revenue_sources(),
        "employees": {t: round(v, 2) for t, v in sorted(s.employees.items()) if v > 0.005},
        "employees_total": round(sum(s.employees.values()), 2),
        "annual_wage_bill": round(s.wage_bill(), 1),
        # FRACTIONS ARE REAL, NOT A DISPLAY GLITCH. A tester reported "1.32
        # artisans" and "0.07 engineers" as if something had gone wrong. It
        # had not: staff grow and decay gradually (hiring phases in, training
        # takes years, attrition is a yearly 3.5%), so at any given moment a
        # trade you have IS a partial year's worth of one more or one fewer
        # person, the same way a company's headcount can be "40.5 FTE". Said
        # only when it would actually be confusing - a whole-number staff
        # needs no footnote.
        "staff_are_fractional_because": (
            None if (abs(s.scholars - round(s.scholars)) < 0.02
                     and abs(s.artisans - round(s.artisans)) < 0.02
                     and all(abs(v - round(v)) < 0.02 for v in s.employees.values()))
            else ("these are continuous full-time-equivalents, not a count of "
                  "whole people: hiring phases in, training takes years, and "
                  "attrition (about 3.5%/yr) trims everyone a little rather "
                  "than dismissing one person at a time. 1.32 artisans is the "
                  "wage and output of one artisan plus a third of another's.")),
        "trades_you_created": sorted(s.trades_created),
        "mothballed": sorted(getattr(s, "mothballed", set())),
        "policy": dict(s.policy),
        "in_bondage_for_debt": round(getattr(s, "bondage_years_left", 0.0), 1),
        "debt_still_to_work_off": round(getattr(s, "bondage_debt", 0.0), 1),
        "credit_limit": round(s.credit_limit(), 1),
        "debt_interest_rate": round(s.debt_interest_rate(), 4),
        "interest_paid_total": round(getattr(s, "interest_paid", 0.0), 1),
        "knowledge_risk": s.knowledge_risk(),
        "resource_throttle": round(s.throttle, 3), "throttle_binding": s.binding,
        "forest_ha": round(s.forest_ha, 1),
        "mine_capacity": {m: round(v, 1) for m, v in s.mine_capacity.items()},
        "slaves": s.slaves, "freedmen": s.freedmen,
        "scholars_including_you": round(s.effective_scholars(), 2),
        "founder_ages": not s.cfg.get("immortal", True),
        "goal": None if getattr(s, "fog", False) else s.goal,
        "goal_reached": s.goal_year is not None, "goal_year": s.goal_year,
        "fog_of_war": getattr(s, "fog", False),
        "manual": s.manual, "ended": end_reason is not None, "end_reason": end_reason,
    }
    # A SHORT REPLY BY DEFAULT. `state` had grown to 55 fields and four
    # kilobytes, two of them a hazard briefing repeated verbatim on every single
    # call, and a tester said reading it back "made me double-check arithmetic
    # more than once". The three heaviest blocks now have commands of their own,
    # so you read them when you want them instead of every turn.
    if not full:
        moved = {"knowledge_risk": "risk", "how_to_grow_staff": "labour",
                 "policy": "policy", "where_the_money_comes_from": "money",
                 "training_pending": "labour"}
        elided = []
        for field, where in moved.items():
            if field in out:
                if field == "knowledge_risk":
                    kr = out[field]
                    haz = [h["name"] for h in kr.get("known_hazards_ahead", [])
                           if h.get("in_progress")]
                    out["at_risk"] = {
                        "technologies_you_could_lose": kr.get("technologies_at_risk"),
                        "hedged_by": kr.get("hedged_by"),
                        "happening_now": haz or None,
                        "hazards_still_ahead": len(kr.get("known_hazards_ahead", [])),
                        "in_full": '{"cmd":"risk"}'}
                elif field == "training_pending" and out[field]:
                    out["in_training"] = len(out[field])
                del out[field]
                elided.append('%s -> {"cmd":"%s"}' % (field, where))
        out["also_available"] = elided
        out["everything_at_once"] = '{"cmd":"state","full":true}'
    return out


HELP_TOPICS = ("commands", "labour", "economy", "money", "automatic",
               "sittings", "fog")


def _agent_help(s, topic=None):
    """Everything a player needs, from inside the game, a topic at a time.

    A tester should not have to be told the commands out of band, and neither
    should a player. But the whole of it at once was four and a half kilobytes
    of JSON before a single move had been made, and testers were spending a
    command just to re-read it. If it is too much for a machine it is far too
    much for a person. So: a short front page, and topics on request.
    """
    fog = getattr(s, "fog", False)
    topic = (topic or "").strip().lower()

    if not topic:
        return {
            "what this is": (
                "You are one person, dropped into a pre-industrial society, "
                "carrying the knowledge of how modern technology works but none "
                "of the industry that makes it. You are playing %s, beginning in "
                "%d. Knowing how a thing works is free. Building it is not: it "
                "takes your own hours, other people's hours, money, materials, "
                "and years."
                % (s.civ.get("name", "a society"), s.cfg["start_year"])),
            "how a turn works": (
                "You begin projects, then advance time. Nothing happens unless "
                "you make it. You are charged for food, rent and appearances "
                "every year whether or not you are building anything."),
            "what you are trying to do": (
                "Advance as far as you can before the horizon at %d. There is no "
                "score but the state of what you have built." % s.end_year
                if fog else
                "Reach %s, and see the rest of what you can build on the way."
                % s.goal),
            "you arrive alone": (
                "No employees, no slaves, nobody who owes you anything. Anyone "
                'who works for you is hired, taught, commissioned or bought. See '
                '{"cmd":"help","topic":"labour"}.'),
            "the four you need first": {
                "state": "where you stand",
                "available": "what you could begin today",
                "why <id>": "everything known about one thing",
                "step <years>": "let time pass",
            },
            "how to send a command": (
                'One JSON object per line on standard input, for example '
                '{"cmd":"available"} or {"cmd":"step","years":5}. Each reply is '
                'one JSON object.'),
            "more": {t: '{"cmd":"help","topic":"%s"}' % t for t in HELP_TOPICS},
        }

    if topic in ("commands", "command", "all"):
        return {"commands": {
            "state": "where you stand; add full:true for every field",
            "available": "what you could begin today, summarised by subject; "
                         'add subject, find, afford, limit/offset, or all:true',
            "why <id>": "everything known about one thing",
            "start <id>": "begin work on something",
            "stop <id>": "abandon it, losing what you have spent",
            "step <years>": "let time pass",
            "money": "the whole ledger: what comes in, what goes out",
            "risk": "what history is about to do to you, and what blunts it",
            "labour": "who you employ and what trades exist here",
            "hire / fire / train / commission": "see the labour topic",
            "buy": "forest, mine, slaves, or manumit; see the economy topic",
            "work <trade> <hours>": "do an ordinary job for ordinary pay",
            "bounty <id>": "pay someone else to solve it instead",
            "mothball <id> / restore <id>": "shut a finished work down, or reopen it",
            "bribe <amount>": "spend money to reduce a scandal",
            "policy": "every automatic behaviour, and a switch for each",
            "path <id>": ("not available under fog of war" if fog
                          else "what something still needs"),
            "save <file> / load <file>": "write or read a game",
            "help": "this; add a topic",
            "quit": "stop",
        }}

    if topic == "labour":
        return {"labour": (
            "You arrive alone. Everything anyone else does for you is hired by "
            "the year, bought as a single job, taught by you from nothing if "
            "this society has no such trade, or bought outright as a person. "
            "Trades are NOT interchangeable: a smith is not a scribe, and a "
            "project asking for an engineer cannot be built by smiths however "
            "many you have."),
            "commands": {
                "labour": 'who exists here and what they cost; add "trade" for one',
                "hire": '{"cmd":"hire","trade":"smith","n":3} - paid every year, '
                        "whether you have work for them or not",
                "fire": '{"cmd":"fire","trade":"smith","n":1}',
                "train": '{"cmd":"train","trade":"machinist","n":2} - teaches a '
                         "trade that does not exist here, out of your own hours",
                "commission": '{"cmd":"commission","trade":"smith","hours":400} - '
                              "buy a job rather than a person",
            }}

    if topic in ("economy", "money", "buy"):
        return {"the ledger": '{"cmd":"money"} itemises what comes in and what '
                              "goes out, including where the income comes from",
                "buy forest": '{"cmd":"buy","what":"forest","n":100} hectares of '
                              "coppice, which is where charcoal comes from",
                "buy mine": '{"cmd":"buy","what":"mine","material":"coal","n":500} '
                            "tonnes a year of your own workings; it takes years "
                            "to sink. Materials: " + ", ".join(Sim.MINE_CAPEX_PER_T_YR),
                "buy slaves": '{"cmd":"buy","what":"slaves","n":5}. This is '
                              "available because it was the ordinary condition of "
                              "production in most of these societies, and a model "
                              "that hides it lies about the cost of everything.",
                "manumit": '{"cmd":"buy","what":"manumit","n":5} frees people you '
                           "hold. They then work better, and it is the decent thing.",
                "debt": "You may spend past what you have, as far as somebody will "
                        "lend you and no further. Arrears cost interest."}

    if topic in ("automatic", "policy"):
        return {"what happens on its own": (
            "Some things the engine will do for you if you let it: grow the "
            "staff, teach trades, sink mines, buy woodland, shut down what you "
            "cannot pay for, pay off a scandal. Every one is a switch you "
            "control, and every one can be done by hand instead."),
            "see them": '{"cmd":"policy"}',
            "change one": '{"cmd":"policy","set":{"auto_hire":true}}'}

    if topic in ("sittings", "save", "load"):
        return {"playing across several sittings": (
            "Pass --session FILE on the command line. The game is written to "
            "that file after every command and read back when you start again, "
            "so you do not need to hold a process open or write a script.")}

    if topic == "fog":
        return {"fog of war": (
            "ON. You can see what you have built, what you could begin today as "
            "a one line summary, and things you have heard of but cannot yet "
            "begin. You cannot see where anything leads, and there is no way to "
            "view the whole tree." if fog else "OFF. You can see the whole tree.")}

    return {"no such topic": topic, "topics": list(HELP_TOPICS)}


SUBJECTS = {
    "00": "the briefing", "01": "the world as it is", "03": "society and politics",
    "10": "metallurgy", "20": "chemistry", "30": "glass and optics",
    "40": "power and precision", "50": "electricity", "55": "semiconductors",
    "60": "mathematics and method", "70": "medicine and biology",
    "75": "agriculture and food", "76": "farming, in depth",
    "80": "printing and information", "85": "roads, bridges and canals",
    "86": "transport, in depth", "87": "construction", "88": "signals and media",
    "89": "the remaining arts", "90": "textiles", "91": "the household",
    "95": "expeditions", "96": "finance", "97": "military",
    "98": "power stations",
}


def _subject_of(n):
    """A readable heading for a node, from its knowledge module.

    There are 241 distinct `cat` values and 26 knowledge modules. The modules
    are the ones a person would recognise as subjects.
    """
    kb = (n.get("kb") or "").split("#")[0]
    return SUBJECTS.get(kb[:2], "everything else")


def _brief(s, nodes, k, fog):
    n = nodes[k]
    if fog:
        return {"id": k, "name": n["name"],
                "cost": round(s.project_cost(k), 1),
                "your_hours": n["ph"],
                "least_years": n["yrs"],
                "chance_of_failure": n["risk"]}
    return {"id": k, "name": n["name"], "tier": n["tier"], "cat": n["cat"],
            "cost": round(s.project_cost(k), 1), "founder_hours": n["ph"],
            "calendar_floor_years": n["yrs"], "risk": n["risk"]}


def _full_entry(s, nodes, k, fog):
    e = _brief(s, nodes, k, fog)
    n = nodes[k]
    if fog:
        e["summary"] = s.fog_summary(k)
        if n["lab"]:
            e["trades_needed"] = sorted(n["lab"])
    else:
        e["prerequisites"] = n["pre"]
        e["note"] = n["note"]
    return e


def _agent_available(s, nodes, cmd=None):
    """What you could begin today.

    THIS USED TO RETURN EVERYTHING. At year 250 that was 559 entries and 165
    kilobytes in a single reply, and even at the start it was 78 entries and 21
    kilobytes: a wall nobody reads, which testers dealt with by grepping their
    own scrollback. If it is too much for a machine it is far too much for a
    person. So the default is now a digest by subject, and you ask for the part
    you want.
    """
    cmd = cmd or {}
    fog = getattr(s, "fog", False)
    # ONE memo for the whole sweep, not one per node. Under fog, checking
    # whether a deep node can start asks whether each of its missing
    # prerequisites is even visible, which asks the same question about
    # THEIR missing prerequisites, and neighbouring nodes in `order` share
    # most of that ancestry. Recomputing it fresh per node, 2,800 times, is
    # what made a single `available` call under fog on norse_900ad take
    # upward of a minute; sharing the memo across the sweep makes it once
    # per node actually touched. See is_visible()'s docstring.
    _memo = {}
    ok = [k for k in s.order if s.can_start(k, _memo=_memo)]
    # Anything the society is about to be handed for nothing is not a decision.
    ok = [k for k in ok
          if not (nodes[k]["tier"] == 0 and nodes[k]["ph"] == 0
                  and nodes[k]["_total_cost"] <= 1
                  and not s._is_foreign_institution(k))]

    want_subject = (cmd.get("subject") or cmd.get("group") or "").strip().lower()
    find = (cmd.get("find") or cmd.get("search") or "").strip().lower()
    show_all = bool(cmd.get("all"))
    try:
        limit = int(cmd.get("limit", 0))
    except (TypeError, ValueError):
        limit = 0
    try:
        offset = max(0, int(cmd.get("offset", 0)))
    except (TypeError, ValueError):
        offset = 0
    afford = float(cmd.get("afford")) if str(cmd.get("afford", "")).strip() not in ("", "None") else None

    sel, why_these = ok, None
    if find:
        sel = [k for k in ok if find in k.lower() or find in nodes[k]["name"].lower()]
        why_these = "matching %r" % find
    elif want_subject:
        sel = [k for k in ok if want_subject in _subject_of(nodes[k]).lower()]
        why_these = "in %r" % want_subject
    if afford is not None:
        sel = [k for k in sel if s.project_cost(k) <= afford]

    heard = []
    if fog:
        heard = sorted(k for k in getattr(s, "revealed", set())
                       if k not in s.done and k not in s.active
                       and not s.start_reason(k)[0])[:25]
    heard_block = [{"id": k, "name": nodes[k]["name"],
                    "why_not": s.start_reason(k)[1]} for k in heard]

    # A LIST was asked for: a subject, a search, an explicit page, or everything.
    if find or want_subject or limit or offset or show_all or afford is not None:
        page = sel if show_all else sel[offset:offset + (limit or 30)]
        out = {"ok": True, "count": len(sel), "of_everything_startable": len(ok),
               "showing": "%d-%d%s" % (offset + 1, offset + len(page),
                                       (" " + why_these) if why_these else ""),
               "available": [_full_entry(s, nodes, k, fog) for k in page]}
        if not show_all and offset + len(page) < len(sel):
            out["more"] = ('%d more; ask again with "offset": %d'
                           % (len(sel) - offset - len(page), offset + len(page)))
        if fog and heard_block and offset == 0:
            out["heard_of_but_cannot_begin"] = heard_block
        return out

    # DEFAULT: the digest.
    groups = {}
    for k in ok:
        g = groups.setdefault(_subject_of(nodes[k]), [])
        g.append(k)
    purse = s.capital + s.credit_limit() * 0.5
    rows = []
    for name, ks in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        costs = sorted(s.project_cost(k) for k in ks)
        rows.append({"subject": name, "things": len(ks),
                     "cheapest": round(costs[0], 1),
                     "dearest": round(costs[-1], 1),
                     "you_could_pay_for": sum(1 for c in costs if c <= purse)})
    cheap = sorted(ok, key=lambda k: s.project_cost(k))[:6]
    out = {"ok": True, "count": len(ok),
           "showing": "a summary by subject, because the full list is %d things"
                      % len(ok),
           "subjects": rows,
           "cheapest_six": [_full_entry(s, nodes, k, fog) for k in cheap],
           "to_see_more": {
               "one subject": '{"cmd":"available","subject":"metallurgy"}',
               "by name": '{"cmd":"available","find":"furnace"}',
               "what you can pay for": '{"cmd":"available","afford":%d}' % int(max(0, purse)),
               "a page of everything": '{"cmd":"available","limit":30,"offset":0}',
               "all of it at once": '{"cmd":"available","all":true} (large)'}}
    if fog and heard_block:
        out["heard_of_but_cannot_begin"] = heard_block
    if fog:
        out["note"] = ("Under fog you see only what you could begin now, and things "
                       "you have heard of. There is no way to see the whole tree.")
    return out


def _node_explain(s, nodes, k):
    n = nodes[k]
    need = closure(nodes, k) - {k}
    unlocks = [] if getattr(s, "fog", False) else [m for m in nodes if k in nodes[m]["pre"]]
    blocks = {m for m in nodes if k in closure(nodes, m)} - {k}
    bounty_by_type = (n["tier"] <= 2 and n["cat"] in ("glass_optics", "metallurgy", "precision",
                      "power", "agriculture", "information", "instruments"))
    started = k in s.done or k in s.active
    out = {
        "id": k, "name": n["name"], "tier": n["tier"], "cat": n["cat"], "confidence": n["conf"],
        "note": n["note"], "kb": n["kb"],
        "founder_hours": n["ph"],
        # Two different kinds of people, and a tester reasonably read the two
        # fields as contradicting each other ("hired_labour names an engineer,
        # staff_needed asks for artisans; the two labour fields don't agree on
        # who is actually doing the work"). They are not the same question.
        # hired_labour is HOURS OF A JOB, bought from whoever does that trade
        # here, for this project only. staff_needed is PEOPLE ON YOUR OWN BOOKS
        # who understand your methods and stay afterwards.
        "hired_labour": n["lab"],
        "materials": n["mat"],
        # `why` used to quote the BASE cost, identical for every civilization,
        # while step() charged that base multiplied by this society's domain
        # factor and by how far it sits from the material's source. A Han
        # playtester compared `why` across two civs, saw byte-identical numbers,
        # and reasonably concluded the whole civilization model was inert
        # flavour text. It is not: the CHARGE has always applied both factors.
        # The QUOTE was lying, which is the more embarrassing half, because a
        # player plans against the quote.
        "cost": {"labour": round(n["_labour_cost"], 1),
                 "materials": round(n["_material_cost"], 1),
                 "capital": n["cap"],
                 "base_total": round(n["_total_cost"], 1),
                 "civ_domain_factor": round(s.civ_cost_factor(k), 3),
                 "material_distance_factor": round(s.material_cost_factor(k), 3),
                 "opposition_factor": round(s.opposition_factor(k), 3),
                 "price_index": round(s.money_real, 3),
                 # The same figure the project will be billed, and must actually
                 # have paid in full before it can complete.
                 "total": round(s.project_cost(k), 1)},
        "upkeep": n["up"], "revenue": n["rev"],
        "calendar_floor_years": n["yrs"], "risk": n["risk"],
        "staff_needed": {"scholars": n["sch"], "artisans": n["art"]},
        "you_have": {"scholars": round(s.effective_scholars(), 1),
                     "artisans": round(s.artisans, 1)},
        "suspicion": n.get("sus", 0), "state_interest_trait_score": n.get("gov", 0),
        "bounty_eligible_by_type": bounty_by_type,
        "direct_prerequisites": n["pre"],
        "missing_prerequisites": [p for p in n["pre"] if p not in s.done],
        # Same reasoning: the size and cost of everything BEHIND a node is a
        # measurement of a tree you cannot see. You do know how many of its own
        # prerequisites you are still missing, because those have names you have
        # either heard or not.
        "chain_size": (len(need) if not getattr(s, "fog", False) else None),
        "chain_founder_hours": (sum(nodes[x]["ph"] for x in need)
                                if not getattr(s, "fog", False) else None),
        "chain_cost": (round(sum(nodes[x]["_total_cost"] for x in need), 1)
                       if not getattr(s, "fog", False) else None),
        "critical_path_years": (critical_path(nodes, k)[0]
                                if not getattr(s, "fog", False) else None),
        # DOWNSTREAM COUNT IS A SPOILER UNDER FOG, and a tester said so
        # unprompted: "downstream_count 1276 seems slightly cheaty". They were
        # right, and worse than cheaty, it was the whole game. Two testers
        # independently found the same three hub nodes by calling `why` on
        # guesses and reading the number, and one wrote that after that "the
        # early strategy is pretty obvious". An exact count of everything a
        # thing leads to is a map of the tree you were told you could not see.
        #
        # What survives fog is the thing a person in the year 100 could actually
        # judge: whether this is a foundation others will build on, or an end in
        # itself. You can tell that much by looking at it.
        "unlocks": unlocks,
        "downstream_count": (len(blocks) if not getattr(s, "fog", False) else None),
        "how_much_rests_on_this": (
            None if not getattr(s, "fog", False) else
            "almost everything" if len(blocks) > 1200 else
            "a great deal" if len(blocks) > 300 else
            "a fair amount" if len(blocks) > 40 else
            "a few things" if len(blocks) > 3 else
            "nothing else; this is worth having for itself"),
        # Under fog there is no goal, so a boolean saying whether this is "on the
        # goal path" is either meaningless or a leak. A tester read it as
        # true/false for five hundred years while `state.goal` was null and
        # reasonably asked what path it could possibly mean.
        "on_goal_path": (None if getattr(s, "fog", False)
                         else (k == s.goal or s.goal in blocks)),
        "done": k in s.done, "active": k in s.active,
        "can_start_now": (not started) and s.can_start(k),
        # Under fog this used to name locked prerequisites in full, so a tester
        # learned the name and description of the printing press from an
        # unrelated node's explanation while `why` on the press itself said they
        # had never heard of it. If you cannot see a thing, you cannot see its
        # name in someone else's sentence either.
        "start_blocked_reason": None if started else s.fog_scrub(s.start_reason(k)[1]),
    }
    # Say what the two labour fields mean ONLY when this node makes it matter.
    # A tester read them as contradicting each other, so the explanation earns
    # its place; carrying it on every reply whether or not the node hires anyone
    # is 400 bytes of boilerplate per call.
    absent = sorted(t for t in n["lab"] if not s.trade_available(t))
    if absent:
        out["trades_that_do_not_exist_here"] = absent
        out["hired_labour_means"] = ("hours of a trade bought in for this job only. "
                                     "These trades do not exist here yet and must "
                                     "be taught; see the labour command.")
    if n["art"] > s.artisans or n["sch"] > s.effective_scholars():
        out["staff_needed_means"] = ("people kept on your own staff, who understand "
                                     "your methods and stay when this is finished. "
                                     "Different from hired_labour, which is hours of "
                                     "a job.")
    return out


def _num(v, default=0.0):
    """Read a number from a command without ever raising at the player.

    NaN AND INFINITY ARE NOT NUMBERS FOR THIS PURPOSE. Python's json accepts
    bare NaN and Infinity as an extension, float() accepts the strings, and
    every comparison against NaN is False - so `NaN` walked through every "must
    be greater than zero" guard in the game, set capital to NaN permanently,
    made everything free, and then got written into the save file as bare NaN,
    which is not legal JSON and cannot be read back by anything else. A tester
    bought 999,999 hectares of woodland with 400 denarii this way.
    """
    try:
        f = float(v)
    except (TypeError, ValueError):
        return float(default)
    if f != f or f in (float("inf"), float("-inf")):
        return float(default)
    return f


def _clean(v):
    """True if this is a real, finite number (or something that is not a number
    at all and will be rejected elsewhere). False only for NaN and infinity."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return True
    return v == v and v not in (float("inf"), float("-inf"))


def _flag(v, default=False):
    """Read a switch. "false", "no", "0" and "" are all off.

    A tester set a policy to the STRING "false" and it came back true, because
    bool("false") is true. Every other language on earth has this bug too and it
    is still a bug.
    """
    if isinstance(v, str):
        return v.strip().lower() not in ("", "false", "no", "off", "0", "none")
    return bool(default if v is None else v)


def _agent_dispatch(s, nodes, cmd):
    if not isinstance(cmd, dict) or "cmd" not in cmd:
        return {"ok": False, "error": "each line must be a JSON object with a 'cmd' field, "
                                      "e.g. {\"cmd\":\"state\"}"}
    op = cmd.get("cmd")
    ended = _agent_end_reason(s)

    if op in ("help", "?", "commands"):
        return {"ok": True, "help": _agent_help(s, cmd.get("topic"))}

    # One central guard rather than five. A playtester sent {"id": {"a": 1}} and
    # the process died on `k not in nodes` with an unhashable-type TypeError,
    # losing the whole session. A malformed command must cost you the command,
    # never the game.
    if "id" in cmd and not isinstance(cmd["id"], str):
        return {"ok": False,
                "error": "id must be a string, got %s. Nothing was changed."
                         % type(cmd["id"]).__name__}

    # NaN and Infinity, anywhere in the command, before anything is touched.
    bad = sorted(k for k, v in cmd.items() if not _clean(v))
    if bad:
        return {"ok": False,
                "error": "%s must be a real number; NaN and Infinity are not "
                         "quantities. Nothing was changed." % ", ".join(bad)}

    if op == "state":
        return dict(ok=True, **_agent_state(s, nodes, cmd))

    if op == "available":
        return _agent_available(s, nodes, cmd)

    if op == "why":
        k = cmd.get("id")
        if isinstance(k, str) and k in nodes and not s.is_visible(k):
            return {"ok": False,
                    "error": "you have never heard of that. You know what you have "
                             "built and what you could begin now; use 'available'."}
        if not isinstance(k, str):
            return {"ok": False, "error": "id must be a string, got %s" % type(k).__name__}
        if k not in nodes:
            near = [x for x in nodes if str(k).lower() in x.lower()]
            return {"ok": False, "error": "unknown node %r. did you mean: %s"
                    % (k, ", ".join(near[:8]) or "no idea")}
        return dict(ok=True, **_node_explain(s, nodes, k))

    if op == "path":
        if getattr(s, "fog", False):
            return {"ok": False,
                    "error": "you cannot plan a route to something you have not "
                             "discovered. Nobody can tell you what a thing requires "
                             "until you know the thing exists. Use 'available' to see "
                             "what you could begin now."}
        k = cmd.get("id")
        if k not in nodes:
            return {"ok": False, "error": "unknown node id %r" % k}
        need = closure(nodes, k)
        order = topo_order(nodes, need)
        remaining = [x for x in order if x not in s.done]
        return {"ok": True, "id": k, "done": k in s.done,
                "remaining_count": len(remaining), "remaining": remaining}

    if op == "start":
        if ended:
            return {"ok": False, "error": "the run has ended (%s); nothing more can be started" % ended}
        k = cmd.get("id")
        if k not in nodes:
            return {"ok": False, "error": "unknown node id %r. use {\"cmd\":\"available\"} "
                                          "or {\"cmd\":\"why\",\"id\":...} to find valid ids" % k}
        ok, why = s.start_project(k)
        if not ok:
            return {"ok": False, "error": why}
        n = nodes[k]
        out = {"ok": True, "started": k, "name": n["name"], "founder_hours_needed": n["ph"],
               "calendar_floor_years": n["yrs"]}
        # WARN, DO NOT SILENTLY ACCEPT. start_reason() already refuses a trade
        # that does not exist AT ALL (see "THE TRADE HAS TO EXIST" there), but
        # trade_available() goes true the moment you call `train`, two years
        # before anyone graduates - market_supply() is the stricter, honest
        # figure step() actually checks. A tester's `start` came back ok:true
        # for a project needing an engineer while nobody could yet DO engineer
        # work, and years later it was HALTED with everything spent on it
        # lost, with no warning at the point they could still have done
        # something about it. Name it here instead.
        short = sorted(t for t in n["lab"] if s.market_supply(t) <= 0.0)
        if short:
            out["warning"] = (
                "no one can do this work YET: %s. The trade exists here or is "
                "being taught, but nobody is trained and ready, and this "
                "project cannot progress at all until someone is. If that is "
                "still true after four years with no progress, it is halted "
                "and everything spent on it is lost. Check {\"cmd\":\"labour\"}, "
                "and see {\"cmd\":\"train\"} if nobody is being taught yet."
                % ", ".join(short))
        return out

    if op == "stop":
        k = cmd.get("id")
        ok, why = s.stop_project(k)
        if not ok:
            return {"ok": False, "error": why}
        return {"ok": True, "stopped": k}

    if op == "bounty":
        if ended:
            return {"ok": False, "error": "the run has ended (%s); nothing more can be bought" % ended}
        k = cmd.get("id")
        if k not in nodes:
            return {"ok": False, "error": "unknown node id %r" % k}
        if k in s.done:
            return {"ok": False, "error": "%s is already done" % k}
        if k in s.active:
            return {"ok": False, "error": "%s is already active; stop it first if you want "
                                          "to switch to a bounty instead" % k}
        if not s.bounty_eligible(k):
            n = nodes[k]
            missing = [p for p in n["pre"] if p not in s.done]
            if missing:
                return {"ok": False, "error": "missing prerequisites: " + ", ".join(missing)}
            return {"ok": False, "error": "not bounty-eligible (tier %d, category %s): a Roman "
                                          "artisan could not recognise success at this" % (n["tier"], n["cat"])}
        price = (nodes[k]["_total_cost"] * 2.5 * s.civ_cost_factor(k)
                 * s.material_cost_factor(k) * s.cost_money_factor())
        if not s.post_bounty(k):
            return {"ok": False, "error": "cannot afford the bounty: needs about %.0f denarii, "
                                          "you have %.0f. Earn or wait, then try again" % (price, s.capital)}
        return {"ok": True, "posted": k, "price": round(price, 1), "capital": round(s.capital, 1)}

    if op == "buy":
        if ended:
            return {"ok": False, "error": "the run has ended (%s); nothing more can be bought" % ended}
        what = cmd.get("what")
        try:
            n = float(cmd.get("n", 0))
        except (TypeError, ValueError):
            return {"ok": False, "error": "n must be a number"}
        # A playtester passed n:-5 and got money from nothing. buy_forest(-5)
        # computed a NEGATIVE cost, passed the affordability test because
        # -1250 > 400 is false, then credited the capital and set forest_ha to
        # -5, while the reply said ok:false. The refusal was reported AFTER the
        # mutation had already happened. Validate before touching anything.
        if not (n > 0):
            return {"ok": False,
                    "error": "n must be greater than zero, got %g. Nothing was changed." % n}
        if what == "forest":
            got = s.buy_forest(n)
            if got <= 0:
                return {"ok": False, "error": "cannot afford %.0f ha of coppice woodland "
                                              "(you have %.0f denarii)" % (n, s.capital)}
            return {"ok": True, "bought_ha": got, "forest_ha": round(s.forest_ha, 1),
                    "capital": round(s.capital, 1)}
        if what == "mine":
            mat = cmd.get("material")
            if mat not in s.MINE_CAPEX_PER_T_YR:
                return {"ok": False, "error": "material must be one of: "
                                              + ", ".join(s.MINE_CAPEX_PER_T_YR)}
            got = s.open_mine(mat, n)
            if got <= 0:
                return {"ok": False, "error": "could not commission any %s capacity right now "
                                              "(capital too low, ceiling reached, or standing "
                                              "too low for a concession that size)" % mat}
            # Say what was actually commissioned and WHEN it arrives. A tester
            # asked for 999,999,999 tonnes a year, silently got 59, and found
            # ready_year was always null so there was no way to know whether the
            # workings would appear in four years or ninety-five. Both of those
            # are the model being coy about its own arithmetic.
            tranche = [t for t in getattr(s, "mine_tranches", []) if t[0] == mat]
            ready = min((t[2] for t in tranche), default=None)
            asked = float(n)
            reply = {"ok": True, "material": mat,
                     "you_asked_for_t_per_yr": asked,
                     "commissioned_t_per_yr": round(got, 2),
                     "ready_year": ready,
                     "years_until_producing": (None if ready is None
                                               else round(ready - s.year, 1)),
                     "already_producing_t_per_yr": round(s.mine_capacity.get(mat, 0.0), 2),
                     "capital": round(s.capital, 1)}
            if got < asked * 0.999:
                reply["note"] = ("less than you asked for: limited by capital, by the "
                                 "ceiling your standing supports, or both. Nothing was "
                                 "wasted, you paid only for what was sunk.")
            return reply
        if what == "slaves":
            got = s.buy_slaves(int(n))
            if got <= 0:
                # Quote the price actually asked. It is no longer 300 flat: a
                # large purchase bids the local market up, and saying "300 each"
                # while charging far more is the model lying to the player.
                q = s.slave_quote(int(n))
                return {"ok": False,
                        "error": "cannot afford %d slaves: %.0f denarii "
                                 "(%.0f each after the market moves against a purchase "
                                 "this size) and you have %.0f"
                                 % (int(n), q, q / max(1, int(n)), s.capital)}
            return {"ok": True, "bought": got, "slaves": s.slaves, "capital": round(s.capital, 1)}
        if what == "manumit":
            got = s.manumit(int(n))
            if got <= 0:
                return {"ok": False, "error": "you have no slaves to free"}
            return {"ok": True, "manumitted": got, "freedmen": s.freedmen, "slaves": s.slaves}
        return {"ok": False, "error": "what must be one of: forest, mine, slaves, manumit"}

    if op == "work":
        if ended:
            return {"ok": False, "error": "the run has ended (%s)" % ended}
        pay, err = s.work_for_wages(cmd.get("trade"), cmd.get("hours", 0))
        if err:
            return {"ok": False, "error": err}
        return {"ok": True, "trade": cmd.get("trade"), "hours": cmd.get("hours"),
                "earned": round(pay, 1), "capital": round(s.capital, 1),
                "your_hours_left_this_year": round(
                    max(0.0, s.director_pool() - s.wage_hours_this_year), 1)}

    if op in ("risk", "hazards"):
        kr = s.knowledge_risk()
        return {"ok": True, "knowledge_risk": kr,
                "note": "What history is about to do to you, and what you have "
                        "built that blunts it. Every hazard here is fightable."}

    if op in ("money", "ledger", "accounts"):
        fixed = s.upkeep() + s.living_cost() + s.mine_operating_cost()
        return {"ok": True,
                "capital": round(s.capital, 1),
                "revenue": round(s.revenue(), 1),
                "where_the_money_comes_from": s.revenue_sources(),
                "what_it_costs_you": {
                    "upkeep_of_what_you_built": round(s.upkeep(), 1),
                    "living_and_appearances": round(s.living_cost() - s.wage_bill(), 1),
                    "wages": round(s.wage_bill(), 1),
                    "mines_standing": round(s.mine_operating_cost(), 1)},
                "net_per_year": round(s.revenue() - fixed, 1),
                "spent_on_projects_last_year": round(getattr(s, "spend_last_year", 0.0), 1),
                "credit_limit": round(s.credit_limit(), 1),
                "interest_rate_on_arrears": round(s.debt_interest_rate(), 4),
                "interest_paid_in_total": round(getattr(s, "interest_paid", 0.0), 1),
                "still_owed_on_work_in_hand": round(
                    sum(st.get("cost_left") or 0.0 for st in s.active.values()), 1)}

    if op == "labour":
        one = (cmd.get("trade") or "").strip().lower()
        if one and one not in WAGES:
            return {"ok": False, "error": "no such trade: %s. They are: %s"
                    % (one, ", ".join(sorted(WAGES)))}
        def row(t, long=False):
            r = {"trade": t,
                 "a_year_of_one": round(ANNUAL_WAGE.get(t, 375.0) * s.wage_index
                                        * s.price_index, 0),
                 "you_employ": round(s.employees.get(t, 0.0), 2)}
            if long:
                r.update({"kind": trade_family(t),
                          "wage_per_hour": round(WAGES[t] * s.wage_index
                                                 * s.price_index, 3),
                          "hours_the_market_can_supply": round(s.market_supply(t), 0),
                          "note": TRADE_NOTES.get(t, "")})
            return r
        if one:
            r = row(one, long=True)
            r["exists_here"] = s.trade_available(one)
            return {"ok": True, "trade": r}
        have = sorted(t for t in WAGES if s.employees.get(t, 0.0) > 0.005)
        hirable = sorted(t for t in WAGES
                         if s.trade_available(t) and t not in have)
        absent = sorted(t for t in WAGES if not s.trade_available(t))
        return {"ok": True,
                "on_your_staff": [row(t) for t in have] or "nobody",
                "you_could_hire_here": hirable,
                "do_not_exist_here": absent,
                "you_employ_in_total": round(sum(s.employees.values()), 2),
                "slaves": s.slaves, "freedmen": s.freedmen,
                "annual_wage_bill": round(s.wage_bill(), 1),
                "craftsmen_on_your_staff": round(s.artisans, 2),
                "scholars_including_you": round(s.effective_scholars(), 2),
                "in_training": [
                    {"trade": (r_[2] if len(r_) > 2 else None),
                     "people": (r_[3] if len(r_) > 3 else round(r_[0], 2)),
                     "ready_year": r_[1]}
                    for r_ in getattr(s, "training", [])],
                "one_trade_in_full": '{"cmd":"labour","trade":"smith"}',
                "how_to_grow_staff": {"scholars": s._staff_advice("scholars"),
                                      "artisans": s._staff_advice("artisans")},
                "note": "A trade that does not exist here cannot be hired at any "
                        "price; teach one with train. Trades are not "
                        "interchangeable. Buying a job instead of a person is "
                        "commission."}

    if op == "hire":
        if ended:
            return {"ok": False, "error": "the run has ended (%s)" % ended}
        ok, err = s.hire(cmd.get("trade"), _num(cmd.get("n"), 1))
        if not ok:
            return {"ok": False, "error": err}
        return {"ok": True, "hired": cmd.get("trade"), "n": cmd.get("n"),
                "you_now_employ": round(s.employees.get(str(cmd.get("trade")).lower(), 0.0), 2),
                "annual_wage_bill": round(s.wage_bill(), 1),
                "capital": round(s.capital, 1)}

    if op in ("fire", "dismiss"):
        ok, err = s.fire(cmd.get("trade"), _num(cmd.get("n"), 1))
        if not ok:
            return {"ok": False, "error": err}
        return {"ok": True, "let_go": cmd.get("trade"),
                "annual_wage_bill": round(s.wage_bill(), 1)}

    if op == "train":
        if ended:
            return {"ok": False, "error": "the run has ended (%s)" % ended}
        ok, msg = s.train(cmd.get("trade"), _num(cmd.get("n"), 1), cmd.get("from"))
        if not ok:
            return {"ok": False, "error": msg}
        return {"ok": True, "training": msg, "capital": round(s.capital, 1),
                "your_hours_left_this_year": round(
                    max(0.0, s.director_pool() - s.director_hours_committed()), 1)}

    if op in ("commission", "job"):
        if ended:
            return {"ok": False, "error": "the run has ended (%s)" % ended}
        ok, msg = s.commission(cmd.get("trade"), _num(cmd.get("hours"), 0))
        if not ok:
            return {"ok": False, "error": msg}
        return {"ok": True, "commissioned": msg, "capital": round(s.capital, 1),
                "note": "These hours are available to your projects this year only."}

    if op == "mothball":
        ok, msg = s.mothball_work(cmd.get("id"))
        if not ok:
            return {"ok": False, "error": msg}
        return {"ok": True, "mothballed": msg, "upkeep": round(s.upkeep(), 1)}

    if op == "restore":
        ok, msg = s.restore_work(cmd.get("id"))
        if not ok:
            return {"ok": False, "error": msg}
        return {"ok": True, "restored": msg, "capital": round(s.capital, 1)}

    if op == "bribe":
        ok, msg = s.bribe(_num(cmd.get("amount"), 0))
        if not ok:
            return {"ok": False, "error": msg}
        return {"ok": True, "bribed": msg, "capital": round(s.capital, 1)}

    if op == "policy":
        want = cmd.get("set")
        changed = {}
        if want is not None:
            if not isinstance(want, dict):
                return {"ok": False,
                        "error": 'set must be an object, e.g. '
                                 '{"cmd":"policy","set":{"auto_hire":true}}'}
            for key, val in want.items():
                if key not in s.policy:
                    return {"ok": False, "error": "no such policy: %s. They are: %s"
                            % (key, ", ".join(sorted(s.policy)))}
                s.policy[key] = _flag(val)
                changed[key] = s.policy[key]
        return {"ok": True, "policy": dict(s.policy), "changed": changed,
                "what_each_does": {
                    "auto_hire": "grow the staff toward what you can house and pay",
                    "auto_buy_people": "buy slaves when the workshop is short-handed",
                    "auto_manumit": "free people you hold, over time",
                    "auto_train": "teach trades this society does not have when a "
                                  "project needs them",
                    "auto_mine": "sink a mine when a mineral is holding work up",
                    "auto_forest": "buy coppice when charcoal is holding work up",
                    "auto_mothball": "stop working mines you cannot pay for",
                    "auto_shed": "let go of works that cost more than they return",
                    "auto_bribe": "pay your way out of a scandal before it kills you",
                },
                "note": "Anything switched off here you can still do by hand: hire, "
                        "train, buy, commission, mothball, restore, bribe."}

    if op in ("save", "load"):
        path = cmd.get("file") or cmd.get("path")
        if not isinstance(path, str) or not path:
            return {"ok": False, "error": 'give a filename, e.g. {"cmd":"save","file":"mygame.json"}'}
        try:
            if op == "save":
                save_state(s, path)
                return {"ok": True, "saved": path, "year": s.year}
            load_state(s, path)
            return {"ok": True, "loaded": path, "year": s.year}
        except Exception as e:
            return {"ok": False, "error": "could not %s %r: %s" % (op, path, e)}

    if op == "step":
        # It used to advance the clock silently after the run was over, which
        # looks identical to a working game that has simply stopped progressing.
        if ended:
            return {"ok": False, "error": "the run has ended (%s); time cannot advance. "
                                          "Use {\"cmd\":\"state\"} to see the final position."
                                          % ended}
        try:
            years = int(cmd.get("years", 1))
        except (TypeError, ValueError):
            return {"ok": False, "error": "years must be an integer"}
        if years < 1:
            return {"ok": False, "error": "years must be >= 1"}
        completed, events = [], []
        end_year = s.end_year
        for _ in range(years):
            if s.dead_reason or s.goal_year or s.year >= end_year:
                break
            before_done, before_log = set(s.done), len(s.log)
            s.step()
            for k in s.done - before_done:
                completed.append({"id": k, "name": nodes[k]["name"], "year": s.done_year.get(k)})
            for y, m in s.log[before_log:]:
                events.append({"year": y, "message": m})
        out = dict(ok=True, completed=completed, events=events)
        out.update(_agent_state(s, nodes))
        return out

    if op == "quit":
        return {"ok": True, "bye": True}

    return {"ok": False, "error": "unknown cmd %r. use one of: state, available, why, path, "
                                  "start, stop, bounty, buy, step, quit" % op}


SAVE_FIELDS = (
    "year", "capital", "done", "granted", "active", "done_year", "training",
    "scholars", "artisans", "directors_extra", "reputation", "suspicion",
    "scandal", "eminence", "protection", "familiarity", "forest_ha",
    "nitre_bed_m2", "mine_capacity", "mine_pending", "mine_ready",
    "mine_tranches", "market_pressure", "slaves", "freedmen",
    "manumitted_total", "goal_year", "dead_reason", "insolvent_years",
    "bribes_ytd", "living_cost_paid", "mine_cost_paid", "spend_last_year",
    "output_factor", "economy", "throttle", "binding", "bountied",
    "stalled", "life_left", "founder_alive", "revealed", "last_settlement",
    "employees", "trades_created", "policy", "mothballed", "contract_hours",
    "commissioned", "teaching_hours_this_year", "wages_paid",
    "bondage_years_left", "bondage_debt", "money_real", "credit_frozen_until",
    # Counters and within-year tallies that were being silently reset on every
    # single command, because with --session every command is a save and a load.
    # wage_hours_this_year is the dangerous one: it is the tally that stops you
    # selling the same year's hours twice, so dropping it handed the exploit
    # straight back to anyone playing the ordinary way, across sittings.
    "interest_paid", "wage_hours_this_year", "teaching_hours_this_year",
    "trade_hours_used", "total_spend", "director_hours_spent_founder",
    "bounties_paid", "atrocity", "suspicion_mult", "gov", "wages_earned",
    "last_patron_death", "_said_debasement",
    # hours_this_year: last year's founder-hours accounting (see step(), just
    # before the within-year tallies above reset). Without it, `state` right
    # after a `--session` reload would report nothing for a figure the player
    # just saw.
    "hours_this_year",
)


def save_state(s, path):
    """Write the whole game to a file.

    There was no save, which is why every playtester ended up writing a driver
    script to hold one long session across many calls. That is a thing a tester
    can do and a player should never have to, so the fix is not a better script,
    it is a save file.
    """
    blob = {}
    for f in SAVE_FIELDS:
        v = getattr(s, f, None)
        if isinstance(v, set):
            v = {"__set__": sorted(v)}
        blob[f] = v
    blob["_civ"] = s.civ.get("id")
    blob["_civ_live"] = {k: s.civ.get(k) for k in
                         ("literacy_general", "literacy_elite", "state_capacity")}
    blob["_weights"] = dict(s.w)
    blob["_fog"] = getattr(s, "fog", False)
    blob["_version"] = 1
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(blob, fh, indent=1, sort_keys=True, default=str)
    os.replace(tmp, path)          # atomic: a crash mid-save cannot eat the game
    return path


def load_state(s, path):
    blob = json.load(open(path))
    for f in SAVE_FIELDS:
        if f not in blob:
            continue
        v = blob[f]
        # NEVER restore a null over a live default. A field that had not been
        # initialised yet when the game was saved, spend_last_year and
        # insolvent_years among them, was written as null and then loaded back
        # OVER the number the constructor had just set, so the next `state`
        # died on round(None). A naive tester hit this on the very first
        # save-and-restart, which is the exact workflow the welcome text tells
        # players is safe, and went back to holding a process open through a
        # FIFO instead. My own round-trip tests missed it because I happened to
        # step the clock first, which initialises those fields.
        if v is None:
            continue
        if isinstance(v, dict) and "__set__" in v:
            v = set(v["__set__"])
        setattr(s, f, v)
    for k, v in (blob.get("_civ_live") or {}).items():
        if v is not None:
            s.civ[k] = v
    s.w.update(blob.get("_weights") or {})
    s.state_capacity = float(s.civ.get("state_capacity", s.state_capacity))
    s.fog = bool(blob.get("_fog", False))
    return s


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
    s = Sim(nodes, order, random.Random(a.seed), events=not a.no_events,
            cfg={"start_capital": STARTING_KITS[a.kit]["den"], "horizon_years": a.horizon},
            civ=load_civ(a.civ), bounty_set=set(), manual=True)
    s.goal = goal
    s.done_year = {}
    s.end_year = s.cfg["start_year"] + a.horizon
    s.fog = bool(getattr(a, "fog", False))
    s.revealed = set()

    session = getattr(a, "session", None)
    if session and os.path.exists(session):
        try:
            load_state(s, session)
        except Exception as e:
            sys.stdout.write(json.dumps(
                {"ok": False, "error": "could not read the save file %r: %s" % (session, e)}
            ) + "\n")
            return 1

    def emit(obj):
        sys.stdout.write(json.dumps(obj) + "\n")
        sys.stdout.flush()

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
            emit(_agent_dispatch(s, nodes, c))
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
        emit(resp)
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
                                    "no, a Roman artisan could not recognise success"))
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


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
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
    q = sub.add_parser("play")
    q.add_argument("--strategy", default="recommended")
    q.add_argument("--seed", type=int, default=1)
    q.add_argument("--horizon", type=int, default=500)
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
    q.add_argument("--session", default=None,
                   help="a save file. Loaded if it exists, written after every "
                        "command, so you can play across separate invocations "
                        "without holding a process open")
    q.add_argument("--script", default=None,
                   help="path to a JSON file holding a list of command objects, "
                        "played in order instead of reading stdin")
    a = p.parse_args()
    return {"validate": cmd_validate, "path": cmd_path, "costs": cmd_costs, "why": cmd_why, "sweep": cmd_sweep, "civs": cmd_civs,
            "run": cmd_run, "compare": cmd_compare, "play": cmd_play, "agent": cmd_agent,
            "sensitivity": cmd_sensitivity}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main() or 0)
