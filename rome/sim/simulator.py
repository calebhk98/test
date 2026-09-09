#!/usr/bin/env python3
"""
ROME 100 AD -> TRANSISTOR : tech-tree simulator, planner and game.

Three things at once, as requested:
  * a RECORD    : `validate`, `costs`, `path` dump the tree and its economics
  * a TOOL      : `run` Monte-Carlos a strategy and tells you where it breaks
  * a GAME      : `play` steps you through it year by year, and `agent` lets a
                  script or an AI play it instead of a person at a keyboard

No third-party dependencies. Python 3.8+.

    python3 rome/sim/simulator.py validate
    python3 rome/sim/simulator.py path point_contact_transistor
    python3 rome/sim/simulator.py costs --top 25
    python3 rome/sim/simulator.py run --strategy recommended --mc 400
    python3 rome/sim/simulator.py run --strategy recommended --no-events   # pure engineering timeline
    python3 rome/sim/simulator.py compare --mc 400
    python3 rome/sim/simulator.py play --strategy recommended
    python3 rome/sim/simulator.py play --manual                            # real free choice, no autopilot
    python3 rome/sim/simulator.py agent                                    # JSON protocol, see below

MACHINE-PLAYABLE INTERFACE (`agent`, and `play --manual`)
-----------------------------------------------------------------------------
`play` used to be a demonstration, not a game: typing a node id only moved it
to the front of the OPTIMIZER's own ordering, and the optimizer (step() 4b)
went on starting whatever else it wanted that year regardless. There was no
way to make a choice and live with only that choice's consequences, and
nothing but a human typing into input() could drive it at all.

Two fixes, usable separately or together:

  --manual (on `play`, and always-on inside `agent`)
      Switches off step() 4b, the optimizer's auto-start loop, entirely.
      Nothing becomes active except what start_project() was explicitly told
      to start. Money, materials, staff, hazards and the calendar all still
      proceed on their own; only the research CHOICE stops being automatic.
      A player who starts nothing makes no progress. That is correct.

  `agent`  a line-oriented JSON protocol, for a script or an LLM
      Reads one JSON command per line from stdin and writes one JSON object
      per line to stdout (or, with --script FILE, reads a JSON list of the
      same command objects from a file and plays them in order). Every
      response is exactly one line of valid JSON; a failed command comes back
      as {"ok": false, "error": "..."} explaining what to do instead, never a
      stack trace or a bare False.

      {"cmd":"state"}                              current situation, in full
      {"cmd":"available"}                          every node that can legally start now,
                                                    with cost, founder hours, calendar
                                                    floor, prerequisites and its note
      {"cmd":"why","id":"zinc_metal"}              the full explanation for one node:
                                                    cost, staff, risk, chain, what it
                                                    unlocks, why it is or isn't startable
      {"cmd":"path","id":"zinc_metal"}             everything still undone on the way
                                                    to this node, in dependency order
      {"cmd":"start","id":"zinc_metal"}            begin a project (error explains
                                                    exactly what is missing if you can't)
      {"cmd":"stop","id":"zinc_metal"}             abandon a project; sunk cost is sunk
      {"cmd":"bounty","id":"zinc_metal"}           post a public prize instead of
                                                    building it yourself (tier <=2 crafts
                                                    only; converts denarii into hours)
      {"cmd":"buy","what":"forest","n":100}        buy 100 ha of coppice woodland
      {"cmd":"buy","what":"mine","material":"iron","n":500}   sink a mine
      {"cmd":"buy","what":"slaves","n":4}          the economic actions the optimizer
      {"cmd":"buy","what":"manumit","n":4}         could take, exposed to the player
      {"cmd":"step","years":5}                     advance the calendar; returns what
                                                    completed and what happened
      {"cmd":"quit"}                               end the session

      The `state` object (also embedded in every `step` reply) reports: year,
      capital, revenue, founder hours available, founder_alive, scholars,
      artisans, reputation, suspicion, scandal, eminence, protection,
      done_count, active (each project's progress), resource_throttle and
      throttle_binding (what is limiting work, if anything), and ended /
      end_reason once the run is over (goal reached, died, or ran out of
      horizon). `available` and `why` never consult the optimizer's own
      ordering for a decision, only for a stable listing order; every
      decision an agent needs is reachable through start/stop/bounty/buy/step
      alone, all the way to the transistor.
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
        # You are one scholar. Rome already has excellent craftsmen for hire;
        # `art` requirements mean staff who understand YOUR methods, so you start
        # with a small pool of hired Roman artisans you can direct.
        self.scholars = 1.0
        self.artisans = 3.0
        self.directors_extra = 0.0
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
            h += self.cfg["founder_hours_per_year"]
        h += self.directors_extra * self.cfg["director_hours_per_year"]
        return h

    def staff_capacity(self):
        """How many trained people the institution can support.

        Ceilings, not rates. You cannot teach faster than you can feed, house and
        supervise, and you cannot supervise more than your directors can reach.
        Funding matters: an institute whose income has collapsed sheds people.
        """
        # Rome already has excellent craftsmen for hire. This floor is them, and it
        # is not conditional on your finances: you can always find a smith.
        base_sc, base_ar = 1.0, 4.0
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
        income = (self.revenue() + max(0.0, self.capital) * 0.12) * self.rep_factor()
        afford = income / (900.0 * self.price_index)        # c. 900 den/yr all-in for one trained person
        scale = max(0.10, min(1.0, afford / max(1.0, sc + ar)))
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

    STAFF_SOURCES = {
        "scholars": [("school_founded", "the school is the only thing that produces scholars in "
                                        "quantity, and it grants more every year it runs"),
                     ("academy_network", "three academies produce more than one school"),
                     ("collegium_licensed", "required before the school is legal")],
        "artisans": [("freedman_staff", "buy, teach and free a technical staff"),
                     ("workshop_first", "you need somewhere for them to work"),
                     ("BUY", "{\"cmd\":\"buy\",\"what\":\"slaves\",\"n\":N} then "
                             "manumit, though they are untrained for three years")],
    }

    def _staff_advice(self, kind):
        """Name the remedy, not just the shortfall."""
        bits = []
        for node, why in self.STAFF_SOURCES.get(kind, []):
            if node == "BUY":
                bits.append(why)
            elif node not in self.done:
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

    def is_visible(self, k):
        """Can the player see this node at all?"""
        if not getattr(self, "fog", False):
            return True
        if k in self.done or k in self.active:
            return True
        if k in getattr(self, "revealed", set()):
            return True
        # anything you could start right now is visible by definition: you can
        # see the work in front of you even if you cannot see past it
        return self.start_reason(k)[0]

    def fog_summary(self, k):
        """One sentence. Deliberately not the whole note, and never the unlocks."""
        note = (self.nodes[k].get("note") or "").strip()
        if not note:
            return self.nodes[k]["name"]
        for sep in (". ", "? ", "! "):
            if sep in note:
                return note.split(sep)[0].strip() + "."
        return (note[:160] + ("..." if len(note) > 160 else ""))

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
            upcoming.append({"name": h.get("name", "hazard"),
                             "years": [y0, y1],
                             "in_progress": y0 <= self.year <= y1,
                             "sacks_a_site": bool(h.get("sack_chance")),
                             "sack_chance_per_year": h.get("sack_chance"),
                             "staff_loss": h.get("staff_loss"),
                             "note": h.get("note")})
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
            "hedged_by": hedge,
            "better_hedge_available": None if hedge == "corpus_dispersed" else "corpus_dispersed",
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
    NEVER_ABANDON = {"social", "institution", "foundation", "law", "organisation",
                     "mathematics", "physics", "information", "method",
                     "notation", "algebra", "geometry", "probability", "analysis"}

    FOREIGN_MARKERS = ("_roman", "_rome", "annona", "insula", "societas",
                       "collegium", "argentarii", "latifundi")

    def _is_foreign_institution(self, k):
        if self.civ.get("id") == "rome_100ad":
            return False
        hay = (k + " " + self.nodes[k].get("name", "")).lower()
        return any(m in hay for m in self.FOREIGN_MARKERS)

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

    def revenue(self):
        r = 0.0
        for k in self.done:
            if k in self.granted and not self._practisable(k):
                continue          # the society's, not yours
            n = self.nodes[k]
            if n["rev"]:
                age = self.year - self.done_year.get(k, self.year)
                ramp = min(1.0, (age + 1) / self.cfg["revenue_ramp_years"])
                r += n["rev"] * ramp
        return (r * (self.economy ** 0.75) + self.state_funding()) * self.output_factor

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
        return sum(self.nodes[k]["up"] for k in self.done
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
        for k in self.active:
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
        for k in self.done:
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
    MINE_CAPEX_PER_T_YR = {"coal": 9.0, "iron": 60.0, "copper": 240.0,
                           "lead": 80.0, "tin": 420.0, "silver": 9000.0}
    MINE_OPEX_PER_T     = {"coal": 1.5, "iron": 12.0, "copper": 55.0,
                           "lead": 18.0, "tin": 95.0, "silver": 2200.0}
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
        return base + household + tax + status

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
        pending = sum(1 for _ in self.training)
        untrained = min(n_people, int(sum(c for c, _ in self.training) / 0.55 + 0.5))
        trained_freed = max(0, n_people - untrained)
        self.artisans += trained_freed * 0.45
        if untrained:
            share = untrained / max(1.0, sum(c for c, _ in self.training) / 0.55)
            for row in self.training:
                row[0] *= 1.0 + 0.45 / 0.55 * min(1.0, share)
        # Manumission was publicly admired, and admiration saturates. The first
        # freedmen you make are a statement; the four hundredth is a payroll.
        # Uncapped, this was a reputation pump that beat taking a patron.
        gain = 0.4 * n_people / (1.0 + self.manumitted_total / 25.0)
        self.reputation += min(gain, 6.0)
        return n_people

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
                 * self.material_cost_factor(k) * self.money_real)
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

    def start_reason(self, k):
        """Same legality test as `can_start`, but explains a refusal instead of
        just returning False. `can_start` is a thin wrapper around this now;
        the wrapper exists because the optimizer's inner loop calls it a huge
        number of times and does not want to build a string it will discard.
        The reason text is what a PLAYER needs (human or agent): not just "no",
        but "no, because you need a local patron first"."""
        if k not in self.nodes:
            return False, "no such node"
        n = self.nodes[k]
        if k in self.done:
            return False, "already done"
        if k in self.active:
            return False, "already active"
        # Tier 9 once meant UNOBTAINABLE: rubber, quinine, New World crops. That
        # concept was abolished, because nothing is unobtainable, only elsewhere,
        # and the tree now routes those through exp_* expedition nodes instead.
        # The guard stays only to stop a stray tier 9 from a new branch file
        # silently making a technology permanently unbuildable; treetool now
        # retiers them on merge, so this should never fire.
        if n["tier"] == 9 or n["cat"] == "unobtainable":
            return False, "retired category: unobtainable in this tree"
        missing = [p for p in n["pre"] if p not in self.done]
        if missing:
            return False, "missing prerequisites: " + ", ".join(missing)
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
        cheap_enough = (n["_total_cost"] * self.money_real * self.civ_cost_factor(k)
                        <= max(800.0, self.revenue()))
        if (getattr(self, "insolvent_years", 0) >= 3
                and not cheap_enough
                and self.capital < -max(4000.0, self.revenue() * 2.0)):
            return False, ("you have been in arrears %d years and are %.0f denarii down; "
                           "nobody will fund a new undertaking of this size. Something "
                           "you can pay for out of this year's income is still allowed, "
                           "so is finishing or stopping what is running."
                           % (getattr(self, "insolvent_years", 0), -self.capital))
        if n["sch"] > self.scholars:
            return False, ("needs %d trained scholars, you have %.1f. %s"
                           % (n["sch"], self.scholars, self._staff_advice("scholars")))
        if n["art"] > self.artisans:
            return False, ("needs %d trained artisans, you have %.1f. %s"
                           % (n["art"], self.artisans, self._staff_advice("artisans")))
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

    def can_start(self, k):
        return self.start_reason(k)[0]

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
        self.active[k] = dict(ph_left=float(n["ph"]), yrs=0.0, spent=0.0)
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

        # 1. staff: bounded by what you can actually house, teach and PAY,
        #    and constantly eroded by death, poaching and old age.
        sc_cap, ar_cap, di_cap = self.staff_capacity()
        ATTRITION = 0.035           # Roman adult mortality plus normal turnover
        self.scholars += (sc_cap - self.scholars) * 0.18 - self.scholars * ATTRITION
        self.artisans += (ar_cap - self.artisans) * 0.22 - self.artisans * ATTRITION
        self.directors_extra += (di_cap - self.directors_extra) * 0.12 - self.directors_extra * ATTRITION
        # while you live you are always at least one natural philosopher
        self.scholars = max(1.0 if self.founder_alive else 0.0, self.scholars)
        self.artisans = max(1.0, self.artisans)
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
        if self.capital < 0 and self.mine_capacity:
            self.mothball_mines()

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
                if net < 0:
                    burden = sorted((k for k in self.done
                                     if self.nodes[k]["up"] > 0
                                     and k not in self.granted
                                     and self.nodes[k]["cat"] not in self.NEVER_ABANDON),
                                    key=lambda k: (self.nodes[k]["rev"] - self.nodes[k]["up"]))
                    shed = []
                    for k in burden:
                        if net >= 0:
                            break
                        n = self.nodes[k]
                        net += n["up"] - n["rev"]
                        self.done.discard(k)
                        shed.append(k)
                    if shed:
                        self.log.append((yr, "ABANDONED %d works you could no longer "
                                             "maintain; they have fallen into disrepair"
                                             % len(shed)))
        else:
            self.insolvent_years = 0
        # a standing workforce policy: buy when short of hands and flush, and
        # free them steadily, which is both the decent and the efficient choice
        if self.capital > 6000 and self.artisans < 12 and self.has("workshop_first"):
            self.buy_slaves(min(6, int(self.capital // 1500)))
        if self.slaves and self.rng.random() < 0.25:
            self.manumit(max(1, self.slaves // 4))
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

        # 4b. start new projects
        pool = self.director_pool()
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
        if not self.manual:
            # More directors means more things in hand at once, and a big trained staff
            # lets routine work proceed without the founder watching it.
            max_active = int(2 + self.director_pool() / 2400.0
                             + self.scholars / 12.0 + self.artisans / 25.0)
            for k in self.order:
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
                if (n["_total_cost"] * self.money_real * self.civ_cost_factor(k)
                        * self.material_cost_factor(k)) > self.capital * 3 + self.revenue() * 6:
                    continue
                if k in self.bounty_set and self.bounty_eligible(k) and self.post_bounty(k):
                    continue
                self.active[k] = dict(ph_left=float(n["ph"]), yrs=0.0, spent=0.0)

        # 4c. materials. Buy the woodland and dig the beds BEFORE the shortage
        #     bites, which is what a competent manager does and what the old
        #     model never had to think about at all.
        self.commission_mines()
        thr = self.resource_throttle()
        if thr < 0.9 and self.capital > 3000:
            # Charcoal is GROWN, so the answer is woodland. Everything else in
            # this list is DUG, so the answer is a mine, and the old model had
            # no answer at all for coal: the binding constraint fell through
            # both branches and the run simply sat throttled. That is why coal
            # showed 1,669 shortage-years in a 395 year run.
            if self.binding == "charcoal":
                self.buy_forest(min(400.0, self.capital / 900.0))
            elif self.binding in self.MINE_CAPEX_PER_T_YR:
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
        for k in active_sorted:
                st = self.active[k]
                n = self.nodes[k]
                per = min(remaining, max(st["ph_left"], n["ph"] / max(n["yrs"], 1.0))) * self.throttle
                remaining -= per
                st["ph_left"] -= per
                self.director_hours_spent_founder += per if self.founder_alive else 0
                st["yrs"] += 1
                frac = min(1.0, 1.0 / max(1.0, n["yrs"]))
                # opposed work costs more: bribes, delay, a provincial site, a front man
                opposition = 1.0 + 0.25 * max(0.0, -self.state_interest(n))
                # material_cost_factor: how far THIS civilization is from
                # wherever geography.json says this thing actually comes
                # from. 1.0 for every node that is not a located material.
                money = (n["_total_cost"] * frac * self.money_real * opposition
                         * self.civ_cost_factor(k) * self.material_cost_factor(k))
                self._spend_this_year = getattr(self, "_spend_this_year", 0.0) + money
                hh = n["_hired_hours"] * frac
                if hh > hired_left:
                    frac *= hired_left / max(hh, 1e-9)
                    money *= hired_left / max(hh, 1e-9)
                    hh = hired_left
                hired_left -= hh
                if money > self.capital:
                    money = max(0.0, self.capital)
                    st["ph_left"] += per * 0.5     # underfunded work stalls
                self.capital -= money
                self.total_spend += money
                st["spent"] += money
                floor = n["yrs"]
                if n["yrs"] >= 5:   # diffusion-limited nodes, not physical curing
                    floor = max(2.0, n["yrs"] / (1.0 + self.reputation / 90.0))
                if st["ph_left"] <= 0 and st["yrs"] >= floor:
                    self._complete(k)

        # 6. reputation, familiarity, protection, scandal
        self.reputation *= 0.97
        # ADAPTATION. Every year the world has known you, and every visible thing
        # you have already done, makes the next one less astonishing.
        pub = sum(1 for k in self.done
                  if set(self.nodes[k].get("traits", [])) & {"spectacle", "inexplicable"})
        self.familiarity = min(0.9, 1.0 - math.exp(-self.w["adaptation_rate"] *
                                                   (0.5 * pub + 0.25 * (self.year - 100))))
        self.spend_last_year = getattr(self, "_spend_this_year", 0.0)
        self._spend_this_year = 0.0
        # Sellers restock, so the pressure your buying put on the market fades.
        self.market_pressure = max(0.0, getattr(self, "market_pressure", 0.0) * 0.55 - 2.0)
        # People bought this year are not artisans this year.
        if self.training:
            still = []
            for cap, ready in self.training:
                if self.year >= ready:
                    self.artisans += cap
                else:
                    still.append([cap, ready])
            self.training = still
        self.update_protection()
        self.scandal *= 0.90
        # Eminence accumulates in a SEPARATE pool, because bribery does not
        # touch it. You can buy a magistrate, an accuser and a jury. You cannot
        # buy an emperor's judgement that you have grown too large, and the
        # attempt is itself evidence against you.
        self.eminence = self.eminence * 0.93 + self.prominence_hazard()
        # you can buy your way out of trouble, and a sane player does
        if self.scandal > 8 and self.capital > 2000:
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
            self.capital -= n["_total_cost"] * 0.4 * self.money_real
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
                loss = h["staff_loss"] * (0.25 if prep else 1.0)
                self.scholars *= (1 - loss); self.artisans *= (1 - loss)
                self.directors_extra *= (1 - loss); self.capital *= (1 - loss * 0.6)
                self.log.append((yr, "%s: staff -%d%%%s" % (h.get("name","hazard"),
                                 loss * 100, " (mitigated)" if prep else "")))
            if "sack_chance" in h:
                p = h["sack_chance"]
                if self.has("academy_network"): p *= 0.40
                if self.has("endowment_land"):  p *= 0.85
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
                self.output_factor = min(self.output_factor, h["output_factor"])
            if "real_erosion" in h:
                self.money_real *= (1 - h["real_erosion"])
                self.capital *= (1 - h["real_erosion"] * 0.85 *
                                 (0.35 if self.has("endowment_land") else 1.0))

    def _random_events(self, yr):
        r = self.rng
        # A patron dies ONCE and then you have courted his heir. The old model
        # rolled 4% every year forever, so a long run logged the same line six
        # times, which is not how having a patron works.
        if (r.random() < 0.05 and self.has("patron_local")
                and yr - getattr(self, "_last_patron_death", -99) > 25):
            self._last_patron_death = yr
            self.scandal += 4
            self.protection *= 0.6
            self.capital -= 800
            self.log.append((yr, "your patron dies; his heir must be courted afresh"))
        if r.random() < 0.03:
            self.capital *= 0.82
            self.log.append((yr, "fire in the insula district"))
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
        return "ran out of horizon (%d AD) without reaching the goal" % end_year
    return None


def _agent_state(s, nodes):
    active = {}
    for k, st in s.active.items():
        n = nodes[k]
        active[k] = {"name": n["name"], "founder_hours_left": round(st["ph_left"], 1),
                     "founder_hours_total": n["ph"], "years_in_progress": st["yrs"],
                     "spent": round(st["spent"], 1), "bountied": k in s.bountied}
    end_reason = _agent_end_reason(s)
    return {
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
        "project_spend_last_year": round(getattr(s, "spend_last_year", 0.0), 1),
        "net_after_project_spend": round(s.revenue() - s.upkeep() - s.living_cost()
                                         - s.mine_operating_cost()
                                         - getattr(s, "spend_last_year", 0.0), 1),
        "net_per_year": round(s.revenue() - s.upkeep() - s.living_cost()
                              - s.mine_operating_cost(), 1),
        "training_pending": [{"artisan_capacity": round(c, 2), "ready_year": y}
                             for c, y in getattr(s, "training", [])],
        "founder_hours_available": round(s.director_pool(), 1),
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
        "knowledge_risk": s.knowledge_risk(),
        "resource_throttle": round(s.throttle, 3), "throttle_binding": s.binding,
        "forest_ha": round(s.forest_ha, 1),
        "mine_capacity": {m: round(v, 1) for m, v in s.mine_capacity.items()},
        "slaves": s.slaves, "freedmen": s.freedmen,
        "goal": None if getattr(s, "fog", False) else s.goal,
        "goal_reached": s.goal_year is not None, "goal_year": s.goal_year,
        "fog_of_war": getattr(s, "fog", False),
        "manual": s.manual, "ended": end_reason is not None, "end_reason": end_reason,
    }


def _agent_help(s):
    """Everything a player needs, from inside the game.

    A tester should not have to be told the commands out of band, and neither
    should a player. If the only way to learn this game is for someone to hand
    you a protocol document, the game is not finished.
    """
    fog = getattr(s, "fog", False)
    return {
        "what this is": (
            "You are one person, dropped into a pre-industrial society, carrying "
            "the knowledge of how modern technology works but none of the "
            "industry that makes it. You are playing %s, beginning in %d. "
            "Knowing how a thing works is free. Building it is not: it takes your "
            "own hours, other people's hours, money, materials, and years."
            % (s.civ.get("name", "a society"), s.cfg["start_year"])),
        "how a turn works": (
            "Nothing happens until you make it happen. You begin projects, then "
            "advance time. Projects consume money and hours while they run. You "
            "are charged for food, rent and appearances every year whether or not "
            "you are building anything."),
        "what you are trying to do": (
            "Advance as far as you can before the horizon at %d. There is no "
            "score but the state of what you have built." % s.end_year
            if fog else
            "Reach %s, and see the rest of what you can build on the way."
            % s.goal),
        "commands": {
            "state": "everything about your position right now",
            "available": "what you could begin today" + (
                ", one line each" if fog else ", in full"),
            "why <id>": "everything known about one thing",
            "start <id>": "begin work on something",
            "stop <id>": "abandon it, losing what you have spent",
            "step <years>": "let time pass",
            "buy": "forest, mine, slaves, or manumit; see 'economy' below",
            "bounty <id>": "pay someone else to solve it instead of building it",
            "path <id>": ("not available under fog of war"
                          if fog else "what something still needs"),
            "save <file>": "write the game to a file",
            "load <file>": "read a game back",
            "help": "this",
            "quit": "stop",
        },
        "how to send a command": (
            'One JSON object per line on standard input, for example '
            '{"cmd":"available"} or {"cmd":"step","years":5} or '
            '{"cmd":"start","id":"some_id"}. Each reply is one JSON object.'),
        "playing across several sittings": (
            "Pass --session FILE on the command line. The game is written to that "
            "file after every command and read back when you start again, so you "
            "do not need to hold a process open or write a script."),
        "economy": {
            "buy forest": '{"cmd":"buy","what":"forest","n":100} hectares of coppice, '
                          'which is where charcoal comes from',
            "buy mine": '{"cmd":"buy","what":"mine","material":"coal","n":500} tonnes '
                        'a year of your own workings; it takes years to sink',
            "buy slaves": '{"cmd":"buy","what":"slaves","n":5}. This is available '
                          'because it was the ordinary condition of production in '
                          'most of these societies, and a model that hides it lies '
                          'about the cost of everything.',
            "manumit": '{"cmd":"buy","what":"manumit","n":5} frees people you hold. '
                       'They then work better, and it is the decent thing.',
        },
        "fog of war": (
            "ON. You can see what you have built, what you could begin today as a "
            "one line summary, and things you have heard of but cannot yet begin. "
            "You cannot see where anything leads, and there is no way to view the "
            "whole tree." if fog else "OFF. You can see the whole tree."),
    }


def _agent_available(s, nodes):
    out = []
    for k in s.order:
        if not s.can_start(k):
            continue
        n = nodes[k]
        if getattr(s, "fog", False):
            # One sentence, the price, and how long. No prerequisites, because
            # you already have them, and above all no hint of what it leads to.
            out.append({"id": k, "name": n["name"],
                        "summary": s.fog_summary(k),
                        "cost": round(n["_total_cost"] * s.civ_cost_factor(k)
                                      * s.material_cost_factor(k) * s.money_real, 1),
                        "your_hours": n["ph"],
                        "least_years": n["yrs"],
                        "chance_of_failure": n["risk"]})
        else:
            out.append({"id": k, "name": n["name"], "tier": n["tier"], "cat": n["cat"],
                        "cost": round(n["_total_cost"], 1), "founder_hours": n["ph"],
                        "calendar_floor_years": n["yrs"], "risk": n["risk"],
                        "prerequisites": n["pre"], "note": n["note"]})
    if getattr(s, "fog", False):
        heard = sorted(k for k in getattr(s, "revealed", set())
                       if k not in s.done and k not in s.active
                       and not s.start_reason(k)[0])
        return {"count": len(out), "available": out,
                "heard_of_but_cannot_begin": [
                    {"id": k, "name": nodes[k]["name"],
                     "why_not": s.start_reason(k)[1]} for k in heard[:40]],
                "note": "Under fog you see only what you could begin now, and things "
                        "you have heard of. There is no way to see the whole tree."}
    return {"count": len(out), "available": out}


def _node_explain(s, nodes, k):
    n = nodes[k]
    need = closure(nodes, k) - {k}
    unlocks = [] if getattr(s, "fog", False) else [m for m in nodes if k in nodes[m]["pre"]]
    blocks = {m for m in nodes if k in closure(nodes, m)} - {k}
    bounty_by_type = (n["tier"] <= 2 and n["cat"] in ("glass_optics", "metallurgy", "precision",
                      "power", "agriculture", "information", "instruments"))
    started = k in s.done or k in s.active
    return {
        "id": k, "name": n["name"], "tier": n["tier"], "cat": n["cat"], "confidence": n["conf"],
        "note": n["note"], "kb": n["kb"],
        "founder_hours": n["ph"], "hired_labour": n["lab"], "materials": n["mat"],
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
                 "price_index": round(s.money_real, 3),
                 "total": round(n["_total_cost"] * s.civ_cost_factor(k)
                                * s.material_cost_factor(k) * s.money_real, 1)},
        "upkeep": n["up"], "revenue": n["rev"],
        "calendar_floor_years": n["yrs"], "risk": n["risk"],
        "staff_needed": {"scholars": n["sch"], "artisans": n["art"]},
        "suspicion": n.get("sus", 0), "state_interest_trait_score": n.get("gov", 0),
        "bounty_eligible_by_type": bounty_by_type,
        "direct_prerequisites": n["pre"],
        "missing_prerequisites": [p for p in n["pre"] if p not in s.done],
        "chain_size": len(need), "chain_founder_hours": sum(nodes[x]["ph"] for x in need),
        "chain_cost": round(sum(nodes[x]["_total_cost"] for x in need), 1),
        "critical_path_years": critical_path(nodes, k)[0],
        "unlocks": unlocks, "downstream_count": len(blocks),
        "on_goal_path": k == s.goal or s.goal in blocks,
        "done": k in s.done, "active": k in s.active,
        "can_start_now": (not started) and s.can_start(k),
        "start_blocked_reason": None if started else s.start_reason(k)[1],
    }


def _agent_dispatch(s, nodes, cmd):
    if not isinstance(cmd, dict) or "cmd" not in cmd:
        return {"ok": False, "error": "each line must be a JSON object with a 'cmd' field, "
                                      "e.g. {\"cmd\":\"state\"}"}
    op = cmd.get("cmd")
    ended = _agent_end_reason(s)

    if op in ("help", "?", "commands"):
        return {"ok": True, "help": _agent_help(s)}

    # One central guard rather than five. A playtester sent {"id": {"a": 1}} and
    # the process died on `k not in nodes` with an unhashable-type TypeError,
    # losing the whole session. A malformed command must cost you the command,
    # never the game.
    if "id" in cmd and not isinstance(cmd["id"], str):
        return {"ok": False,
                "error": "id must be a string, got %s. Nothing was changed."
                         % type(cmd["id"]).__name__}

    if op == "state":
        return dict(ok=True, **_agent_state(s, nodes))

    if op == "available":
        return dict(ok=True, **_agent_available(s, nodes))

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
        return {"ok": True, "started": k, "name": n["name"], "founder_hours_needed": n["ph"],
                "calendar_floor_years": n["yrs"]}

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
                 * s.material_cost_factor(k) * s.money_real)
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
            return {"ok": True, "commissioned_t_per_yr": round(got, 2),
                    "ready_year": s.mine_ready.get(mat), "capital": round(s.capital, 1)}
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
    "stalled", "life_left", "founder_alive", "revealed",
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
