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
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TREE = os.path.join(ROOT, "data", "tech_tree.json")
PRICES = os.path.join(ROOT, "data", "prices.json")
STRATS = os.path.join(HERE, "strategies")

# ----------------------------------------------------------------------------
# Loading and derived economics
# ----------------------------------------------------------------------------

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
    """Longest chain by minimum calendar years + director-hours-at-one-director."""
    memo = {}
    def f(k):
        if k in memo:
            return memo[k]
        n = nodes[k]
        own = max(n["yrs"], n["ph"] / 2400.0)
        best, chain = 0.0, []
        for p in n["pre"]:
            d, c = f(p)
            if d > best:
                best, chain = d, c
        memo[k] = (best + own, chain + [k])
        return memo[k]
    return f(goal)


# ----------------------------------------------------------------------------
# Simulation
# ----------------------------------------------------------------------------

DEFAULTS = dict(
    start_year=100,
    start_capital=10320,        # scholar_modest kit, 3 kg of gold at 3,440 den/kg
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
                 bounty_set=None):
        self.nodes = nodes
        self.order = list(order)
        self.rng = rng
        self.events = events
        self.cfg = dict(DEFAULTS, **(cfg or {}))
        self.verbose = verbose
        self.bounty_set = set(bounty_set or ())
        c = self.cfg
        self.year = c["start_year"]
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
        self.life_left = max(5, rng.gauss(28, 8))

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
        income = self.revenue() + max(0.0, self.capital) * 0.12
        afford = income / 900.0        # c. 900 den/yr all-in for one trained person
        scale = max(0.10, min(1.0, afford / max(1.0, sc + ar)))
        return base_sc + sc * scale, base_ar + ar * scale, di * min(1.0, scale * 1.3)

    def hired_cap(self):
        cap = self.cfg["hired_hours_cap_base"]
        if self.has("school_founded"):    cap *= 2.0
        if self.has("freedman_staff"):    cap *= 1.5
        if self.has("patron_imperial"):   cap *= 3.0
        if self.has("academy_network"):   cap *= 2.5
        if self.has("interchangeable_parts"): cap *= 1.5
        return cap

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
        return 2500.0 * self.economy * (1.0 + max(0.0, self.gov) / 25.0)

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

    def can_start(self, k):
        n = self.nodes[k]
        if k in self.done or k in self.active:
            return False
        if not all(p in self.done for p in n["pre"]):
            return False
        if n["sch"] > self.scholars or n["art"] > self.artisans:
            return False
        # SOCIAL APPROVAL GATE. Some things the State does not want built, and no
        # amount of money substitutes for someone powerful being willing to be
        # associated with it. See 03_SOCIAL_POLITICS.md section 4.
        if n["gov"] < 0 and not self.has("patron_local"):
            return False
        if n["gov"] <= -2 and not self.has("patron_senatorial"):
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
        self.capital += self.revenue() - self.upkeep()
        if yr >= SHOCKS["debasement_starts"]:
            # The denarius loses almost all its silver between 190 and 275. This
            # destroys anyone holding coin. It does NOT destroy real output, because
            # prices adjust. Hold land and tools, never a chest of denarii.
            rate = 0.02 if yr < 235 else (0.09 if yr < 275 else 0.03)
            self.money_real *= (1 - rate)
            hedge = 0.35 if self.has("endowment_land") else 1.0
            self.capital *= (1 - rate * 0.85 * hedge)
        # real output: war, plague and broken trade routes, then a partial recovery
        a, b = SHOCKS["third_century_crisis"]
        if a <= yr <= b:
            self.output_factor = 0.62
        elif yr > b:
            self.output_factor = min(0.85, 0.62 + 0.006 * (yr - b))

        # 3. dated shocks
        if self.events:
            self._shocks(yr)
            if self.dead_reason:
                return

        # 4. start new projects, cheapest-first among the strategy order
        pool = self.director_pool()
        hired_left = self.hired_cap()
        max_active = int(2 + self.director_pool() / 2400.0)
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
                per = min(remaining, max(st["ph_left"], n["ph"] / max(n["yrs"], 1.0)))
                remaining -= per
                st["ph_left"] -= per
                self.director_hours_spent_founder += per if self.founder_alive else 0
                st["yrs"] += 1
                frac = min(1.0, 1.0 / max(1.0, n["yrs"]))
                # opposed work costs more: bribes, delay, a provincial site, a front man
                opposition = 1.0 + 0.25 * max(0, -n["gov"])
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
                if st["ph_left"] <= 0 and st["yrs"] >= n["yrs"]:
                    self._complete(k)

        # 6. suspicion
        self.suspicion *= (1 - c["suspicion_decay"])
        # Protection is multiplicative and it is the whole reason to spend years
        # courting people instead of building things. An unprotected philosopher
        # doing chemistry in a rented room is a defendant waiting to be named.
        mult = 1.0
        if self.has("patron_local"):       mult *= 0.60
        if self.has("collegium_licensed"): mult *= 0.65
        if self.has("citizenship"):        mult *= 0.80
        if self.has("patron_senatorial"):  mult *= 0.70
        if self.has("patron_imperial"):    mult *= 0.55
        if self.has("sanitation_antisepsis"): mult *= 0.85   # a famous healer is forgiven much
        if self.has("endowment_land"):     mult *= 0.90      # conspicuous public benefaction
        self.suspicion_mult = mult
        self.suspicion = max(0.0, self.suspicion)
        if self.events and self.suspicion > c["suspicion_danger"]:
            p = (self.suspicion - c["suspicion_danger"]) / 120.0
            if self.rng.random() < p:
                self._catastrophe("denounced as a magician: property seized, school closed")

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
        self.suspicion += (n["sus"] + 3 * max(0, -n["gov"])) * self.suspicion_mult
        self.gov += n["gov"]
        if k == "freedman_staff":     self.artisans += 8
        if k == "school_founded":     self.scholars += 4
        if k == "academy_network":    self.scholars += 10; self.artisans += 10
        if k == "mining_concession":  pass
        self.log.append((self.year, "completed: " + n["name"]))
        if k == self.goal and self.goal_year is None:
            self.goal_year = self.year

    # -- shocks -------------------------------------------------------------
    def _shocks(self, yr):
        """The three dated catastrophes you have foreknowledge of, and cannot avoid.

        You can only mitigate them, and the mitigations are cheap defensive nodes
        with no technical payoff, which is exactly why a greedy strategy skips them
        and then loses the run 130 years later.
        """
        r = self.rng
        prep = self.has("plague_preparedness")
        for name, (a, b) in (("Antonine plague", SHOCKS["antonine_plague"]),
                             ("Plague of Cyprian", SHOCKS["cyprian_plague"])):
            if a <= yr <= b and r.random() < 0.34:
                loss = 0.08 if prep else 0.32
                self.scholars *= (1 - loss)
                self.artisans *= (1 - loss)
                self.directors_extra *= (1 - loss)
                self.capital *= (1 - loss * 0.7)
                self.log.append((yr, "%s: staff -%d%%%s"
                                 % (name, loss * 100, " (mitigated)" if prep else "")))

        a, b = SHOCKS["third_century_crisis"]
        if a <= yr <= b:
            p = 0.16
            if self.has("academy_network"): p *= 0.40   # three sites, not one
            if self.has("patron_imperial"): p *= 0.85
            if self.has("endowment_land"):  p *= 0.85   # land survives what coin does not
            if r.random() < p:
                self.capital *= 0.40
                self.artisans *= 0.55
                self.scholars *= 0.55
                self.directors_extra *= 0.65
                for k in list(self.active):
                    self.active[k]["ph_left"] = self.nodes[k]["ph"]
                    self.active[k]["yrs"] = 0.0
                self.log.append((yr, "third-century crisis: a site is sacked; work in hand is lost"))
                # THE decisive mechanic: was the knowledge printed and dispersed?
                if self.has("corpus_dispersed"):
                    pl, frac = 0.12, 0.08
                elif self.has("corpus_written"):
                    pl, frac = 0.45, 0.22     # manuscripts in one place burn with the place
                else:
                    pl, frac = 0.80, 0.40
                if r.random() < pl:
                    losable = [k for k in self.done if self.nodes[k]["tier"] >= 2]
                    if losable:
                        drop = r.sample(losable, max(1, int(len(losable) * frac)))
                        for k in drop:
                            self.done.discard(k)
                        self.log.append((yr, "KNOWLEDGE LOST: %d technologies forgotten%s"
                                         % (len(drop),
                                            "" if self.has("corpus_dispersed")
                                            else " (the corpus was never printed and dispersed)")))

    def _random_events(self, yr):
        r = self.rng
        if r.random() < 0.04 and self.has("patron_local"):
            self.suspicion += 6
            self.capital -= 800 * self.money_real
            self.log.append((yr, "a patron dies; you must court his heir"))
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
        rest = [k for k in topo_order(nodes) if k not in order]
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
        print("elapsed from 100 AD : median %d years" % (q(.5) - 100))
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
        cmd = input("[%d AD | %d den | you:%d hr | sch %.0f art %.0f | susp %.0f] > "
                    % (s.year, s.capital, s.director_pool(), s.scholars, s.artisans, s.suspicion)).strip()
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


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("validate")
    q = sub.add_parser("path"); q.add_argument("goal", nargs="?")
    q = sub.add_parser("costs"); q.add_argument("--top", type=int, default=20)
    q = sub.add_parser("why"); q.add_argument("node")
    for name in ("run", "compare"):
        q = sub.add_parser(name)
        q.add_argument("--strategy", default="recommended")
        q.add_argument("--mc", type=int, default=200)
        q.add_argument("--seed", type=int, default=1)
        q.add_argument("--horizon", type=int, default=500)
        q.add_argument("--no-events", action="store_true")
        q.add_argument("--no-bounties", action="store_true")
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
    return {"validate": cmd_validate, "path": cmd_path, "costs": cmd_costs, "why": cmd_why,
            "run": cmd_run, "compare": cmd_compare, "play": cmd_play,
            "sensitivity": cmd_sensitivity}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main() or 0)
