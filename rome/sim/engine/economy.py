"""Money, materials, and the works that consume both.

Split out of simulator.py, which had grown to 5,600 lines. These are
methods of Sim; they are a mixin only so that they can live in a file of
their own. Behaviour is unchanged and verified byte-identical.
"""
import collections, json, math, os, random
from collections import defaultdict

from .data import *          # the shared tables and loaders
from .data import (WAGES, ANNUAL_WAGE, TRADE_NOTES, TRADES_ABSENT,
                   TRADE_FAMILY, TECH_EFFECTS, DEFAULTS, SHOCKS,
                   STARTING_KITS, trade_family, closure, critical_path,
                   topo_order, load, load_civ, haversine_km,
                   load_geography, load_resources)


class EconomyMixin:
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
            self._done_changed()
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
                self._done_changed()
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

    def _done_changed(self):
        """Call after anything adds to or removes from self.done."""
        self._done_seq = None

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
        # CACHED, because this is O(nodes) and revenue() calls it. Uncached it
        # was 2.2 seconds of a 3.5 second `can_start` once something else began
        # calling revenue() thousands of times: correct, and quadratic. The
        # cache is invalidated by hand at the twelve places that add to or
        # remove from `done`, rather than by a length check, because a year that
        # abandons one work and completes another leaves the length identical
        # and the contents different.
        seq = getattr(self, "_done_seq", None)
        if seq is None:
            seq = self._done_seq = [k for k in self.order if k in self.done]
        return seq

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

    def mine_quote(self, mat, t_per_yr):
        """What a mine would cost, BEFORE you commit to it.

        A tester asked for one tonne of gold a year - the same order as the
        example in the help text - and went from 38,151 denarii to zero on a
        single command, with no price shown and no way to ask. Five years later
        the workings were mothballed for non-payment and they were in debt
        bondage. Every other purchase in this game quotes before it charges.
        """
        cap = self.MINE_CAPEX_PER_T_YR.get(mat)
        if cap is None:
            return None
        t = max(0.0, float(t_per_yr))
        sink = t * cap * self.price_index
        opex = t * self.MINE_OPEX_PER_T.get(mat, 0.0) * self.price_index
        return {"material": mat,
                "tonnes_per_year": round(t, 3),
                "to_sink_it": round(sink, 1),
                "every_year_it_stands": round(opex, 1),
                "years_before_it_produces": self.MINE_LEAD_YEARS,
                "you_have": round(self.capital, 1),
                "you_can_afford_about": round(
                    max(0.0, self.capital) / max(cap * self.price_index, 1e-9), 3),
                "note": "The yearly cost is charged whether or not you use the "
                        "output, and goes on until you close it. Mothballing is "
                        "not free to reverse: the shaft floods and the crew "
                        "disperses, so reopening means sinking it again."}

    def close_mine(self, mat):
        """Shut your own workings down, on purpose.

        The engine mothballs mines it cannot pay for and there was no way for a
        player to ask. A tester was billed 28.1 a year in perpetuity for a gold
        mine producing 0.0 tonnes and could do nothing about it.
        """
        mat = str(mat or "").strip().lower()
        have = self.mine_capacity.get(mat, 0.0)
        pend = [t for t in getattr(self, "mine_tranches", []) if t[0] == mat]
        if not have and not pend:
            return False, ("you have no %s workings, and none being sunk" % mat
                           if mat in self.MINE_CAPEX_PER_T_YR
                           else "no such material: %s. Mineable: %s"
                                % (mat, ", ".join(sorted(self.MINE_CAPEX_PER_T_YR))))
        saved = have * self.MINE_OPEX_PER_T.get(mat, 0.0) * self.price_index
        self.mine_capacity.pop(mat, None)
        self.mine_tranches = [t for t in getattr(self, "mine_tranches", [])
                              if t[0] != mat]
        self.log.append((self.year, "you close the %s workings" % mat))
        return True, ("the %s workings are closed. You stop paying %.0f a year. "
                      "What you spent sinking them is gone, and reopening means "
                      "sinking them again." % (mat, saved))

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
