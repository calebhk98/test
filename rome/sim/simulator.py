#!/usr/bin/env python3
"""
ROME 100 AD -> TRANSISTOR : tech-tree simulator, planner and game.

Three things at once, as requested:
  * a RECORD    : `validate`, `costs`, `path` dump the tree and its economics
  * a TOOL      : `run` Monte-Carlos a strategy and tells you where it breaks
  * a GAME      : `play` steps you through it year by year

No third-party dependencies. Python 3.8+.

    python3 rome/sim/simulator.py validate
    python3 rome/sim/simulator.py path point_contact_transistor
    python3 rome/sim/simulator.py costs --top 25
    python3 rome/sim/simulator.py run --strategy recommended --mc 400
    python3 rome/sim/simulator.py run --strategy recommended --no-events   # pure engineering timeline
    python3 rome/sim/simulator.py compare --mc 400
    python3 rome/sim/simulator.py play --strategy recommended
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

def load_resources():
    return json.load(open(RESFILE))

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
    "absurd":      {"den": 1000000,"desc": "four senatorial fortunes in unminted gold. Included to show that it makes things WORSE, not better."},
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
                 bounty_set=None, civ=None):
        self.nodes = nodes
        self.order = list(order)
        self.rng = rng
        self.events = events
        self.cfg = dict(DEFAULTS, **(cfg or {}))
        self.verbose = verbose
        self.bounty_set = set(bounty_set or ())
        self.civ = civ or load_civ()
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
        self.forest_ha = 0.0        # coppice you own, in hectares
        self.nitre_bed_m2 = 0.0
        self.shortages = collections.Counter()
        self.throttle = 1.0
        self.binding = None
        # whatever this civilization already has is free and already done
        for k in self.civ.get("starting_techs", []):
            if k in self.nodes:
                self.done.add(k)

    # -- helpers ------------------------------------------------------------
    def has(self, k):
        return k in self.done

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
            n = self.nodes[k]
            if n["rev"]:
                age = self.year - self.done_year.get(k, self.year)
                ramp = min(1.0, (age + 1) / self.cfg["revenue_ramp_years"])
                r += n["rev"] * ramp
        return (r * (self.economy ** 0.75) + self.state_funding()) * self.output_factor

    def upkeep(self):
        return sum(self.nodes[k]["up"] for k in self.done)

    # ---- raw material supply ------------------------------------------------
    CHARCOAL_PER_HA = 0.75          # tonnes per hectare per year, sustainable
    # How much of the empire's annual output you can actually BUY. This is not
    # one number: charcoal is bulky, crumbles when carted, and is therefore a
    # LOCAL commodity no matter how much of it the empire makes in total, while
    # coal is barely used by anyone so you can have almost all of it.
    MARKET_SHARE = {"charcoal": 0.002, "iron": 0.03, "copper": 0.03, "lead": 0.03,
                    "tin": 0.05, "silver": 0.01, "coal": 0.50, "saltpetre": 0.0}

    def annual_material_demand(self):
        """Tonnes per year of the materials that actually bind, from work in hand."""
        d = collections.Counter()
        for k in self.active:
            n = self.nodes[k]
            span = max(1.0, float(n.get("build_yrs") or n.get("yrs") or 1.0))
            for m, q in n["mat"].items():
                d[m] += float(q) / span / 1000.0     # kg -> tonnes per year
        # A furnace does not eat charcoal only while it is being built. It eats
        # charcoal every year it runs, forever. Omitting that was why forest
        # ownership never mattered in the model and always mattered in reality.
        for k in self.done:
            n = self.nodes[k]
            if n["up"] <= 0 or not n["mat"]:
                continue
            span = max(1.0, float(n.get("build_yrs") or n.get("yrs") or 1.0))
            for m, q in n["mat"].items():
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
            "iron_bar_kg": ("iron", 0.0), "iron_ore_kg": ("iron", 0.0),
            "coal_kg": ("coal", 0.0), "copper_kg": ("copper", 0.0),
            "lead_kg": ("lead", 0.0), "tin_kg": ("tin", 0.0),
            "silver_kg": ("silver", 0.0), "nitre_kg": ("saltpetre", self.nitre_bed_m2 * 0.0008),
        }
        for mat, (emp_key, own) in checks.items():
            need = demand.get(mat, 0.0)
            if need <= 0:
                continue
            share = self.MARKET_SHARE.get(emp_key, 0.03)
            market = emp.get(emp_key, {}).get("t_per_yr", 0) * share * self.pop_scale
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

    def buy_slaves(self, n_people):
        """The option the model refuses to hide, and refuses to make costless.

        Roman labour is cheap because much of it is coerced, and any honest model
        of a Roman enterprise has to let you do this. It is available, it works,
        it is counted separately, and manumission is modelled as strictly better
        on the numbers as well as on every other ground: a freedman is paid, is
        literate, stays, and transmits what he knows.
        """
        price = 300.0 * n_people
        if price > self.capital:
            return 0
        self.capital -= price
        self.slaves += n_people
        self.artisans += n_people * 0.55        # unfree labour is less productive
        return n_people

    def manumit(self, n_people):
        n_people = min(n_people, self.slaves)
        if not n_people:
            return 0
        self.slaves -= n_people
        self.freedmen += n_people
        self.manumitted_total += n_people
        self.artisans += n_people * 0.55        # same person, now working properly
        self.reputation += 0.4 * n_people       # manumission was publicly admired
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
        price = n["_total_cost"] * 2.5
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

    def can_start(self, k):
        n = self.nodes[k]
        if k in self.done or k in self.active:
            return False
        # Tier 9 is UNOBTAINABLE by construction: rubber, quinine, New World crops.
        # An earlier version cheerfully queued "potato" and let it occupy a project
        # slot for four centuries, which quietly strangled the whole run.
        if n["tier"] == 9 or n["cat"] == "unobtainable":
            return False
        if not all(p in self.done for p in n["pre"]):
            return False
        if not self.substitution_quality(k)[1]:
            return False
        if n["sch"] > self.scholars or n["art"] > self.artisans:
            return False
        # SOCIAL APPROVAL GATE. Some things the State does not want built, and no
        # amount of money substitutes for someone powerful being willing to be
        # associated with it. See 03_SOCIAL_POLITICS.md section 4.
        # SOCIAL APPROVAL. Computed from this civilization's values and this
        # technology's traits, not from a number baked into the technology.
        # Never let the gate ask for a thing in order to get that same thing:
        # the patronage and institution nodes are how you BUY permission, so they
        # cannot themselves require permission.
        if n["cat"] in ("social", "institution", "foundation", "capability", "material"):
            return True
        si = self.state_interest(n)
        if si < -0.4 and not self.has("patron_local"):
            return False
        if si < -1.2 and not (self.has("patron_senatorial") or self.protection > 0.45):
            return False
        return True

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
        self.capital += self.revenue() - self.upkeep() - lc
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

        # 4a. Anything Rome ALREADY HAS costs nothing and takes nobody's attention.
        #     Grant it the moment its prerequisites are met instead of making it
        #     queue behind real work.
        for k in self.order:
            n = self.nodes[k]
            if (n["tier"] == 0 and n["ph"] == 0 and n["_total_cost"] <= 1
                    and k not in self.done and k not in self.active
                    and all(p in self.done for p in n["pre"])):
                self.done.add(k)
                self.done_year[k] = self.year

        # 4b. start new projects
        pool = self.director_pool()
        hired_left = self.hired_cap()
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
            # do not start something we cannot plausibly fund this decade
            if n["_total_cost"] * self.money_real > self.capital * 3 + self.revenue() * 6:
                continue
            if k in self.bounty_set and self.bounty_eligible(k) and self.post_bounty(k):
                continue
            self.active[k] = dict(ph_left=float(n["ph"]), yrs=0.0, spent=0.0)

        # 4c. materials. Buy the woodland and dig the beds BEFORE the shortage
        #     bites, which is what a competent manager does and what the old
        #     model never had to think about at all.
        thr = self.resource_throttle()
        if thr < 0.9 and self.capital > 3000:
            if self.binding in ("charcoal", "iron", "copper", "lead"):
                self.buy_forest(min(400.0, self.capital / 900.0))
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
                money = n["_total_cost"] * frac * self.money_real * opposition
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
        self.update_protection()
        self.scandal *= 0.90
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
                losable = [k for k in self.done if self.nodes[k]["tier"] >= 2]
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
                    for k in list(self.active):
                        self.active[k]["ph_left"] = self.nodes[k]["ph"]
                        self.active[k]["yrs"] = 0.0
                    self.log.append((yr, "%s: a site is sacked" % h.get("name","crisis")))
                    if self.has("corpus_dispersed"):   pl, frac = 0.12, 0.08
                    elif self.has("corpus_written"):   pl, frac = 0.45, 0.22
                    else:                              pl, frac = 0.80, 0.40
                    if r.random() < pl:
                        losable = [k for k in self.done if self.nodes[k]["tier"] >= 2]
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
        res = [Sim(nodes, order, random.Random(a.seed + i), events=True,
                   cfg={"immortal": not getattr(a, "mortal", False),
                        "start_capital": STARTING_KITS.get(getattr(a,"kit","poor_scholar"),
                                                           STARTING_KITS["poor_scholar"])["den"]},
                   civ=load_civ(getattr(a, "civ", "rome_100ad")),
                   bounty_set=bounties).run(goal, a.horizon)
               for i in range(a.mc)]
        _summarise(res, label)


def cmd_play(a):
    tree, prices, nodes, wages, goods = load()
    goal = tree["meta"]["goal_node"]
    label, order, bounties = load_strategy(a.strategy, nodes, goal)
    s = Sim(nodes, order, random.Random(a.seed), events=True, bounty_set=bounties)
    s.goal = goal; s.done_year = {}
    print("You arrive in %d AD with %d denarii in unminted gold.\n"
          "Type a node id to begin work on it, 'a' for what is available,\n"
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
        if cmd in nodes:
            if s.can_start(cmd):
                s.order.remove(cmd); s.order.insert(0, cmd); print("   prioritised.")
            else:
                miss = [p for p in nodes[cmd]["pre"] if p not in s.done]
                print("   blocked. missing:", ", ".join(miss) or
                      "staff (needs %d scholars, %d artisans)" % (nodes[cmd]["sch"], nodes[cmd]["art"]))
        else:
            print("   unknown command")
    print("\nEnded %d AD. %s" % (s.year, s.dead_reason or ("GOAL REACHED" if s.goal_year else "horizon")))


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
    print("Suspicion       : %+d       State interest: %+d%s" % (n["sus"], n["gov"],
          ("  <- OPPOSED. Costs %d%% more, +%d extra suspicion, needs %s"
           % (25 * -n["gov"], 3 * -n["gov"],
              "senatorial patronage" if n["gov"] <= -2 else "a patron"))
          if n["gov"] < 0 else ""))
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
    """List the civilizations you can play, and what makes each one different."""
    for f in sorted(os.listdir(CIVDIR)):
        if not f.endswith(".json"):
            continue
        c = json.load(open(os.path.join(CIVDIR, f)))
        v = c["values"]
        print("%-16s %s, %s" % (c["id"], c["name"], c["year"]))
        print("   %s" % c.get("blurb", ""))
        print("   population %s   state capacity %.2f   reach %d   starts with %d technologies"
              % (f"{c.get('population',0):,}", c.get("state_capacity", 0),
                 c.get("base_reach", 0), len(c.get("starting_techs", []))))
        print("   fears the inexplicable %.2f | fears heterodoxy %.2f | resents machines %+.2f "
              "| bribable %.2f | habituates %.2f"
              % (v["w_magic_fear"], v["w_religious_rigidity"], v["w_labour_saving"],
                 v["bribability"], v["adaptation_rate"]))
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
    a = p.parse_args()
    return {"validate": cmd_validate, "path": cmd_path, "costs": cmd_costs, "why": cmd_why, "sweep": cmd_sweep, "civs": cmd_civs,
            "run": cmd_run, "compare": cmd_compare, "play": cmd_play,
            "sensitivity": cmd_sensitivity}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main() or 0)
