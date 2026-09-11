"""The simulation itself: what one year does, and the loop over years."""
import collections, json, math, os, random
from collections import defaultdict

from .data import *          # the shared tables and loaders
from .data import (WAGES, ANNUAL_WAGE, TRADE_NOTES, TRADES_ABSENT,
                   TRADE_FAMILY, TECH_EFFECTS, DEFAULTS, SHOCKS,
                   STARTING_KITS, trade_family, closure, critical_path,
                   topo_order, load, load_civ, haversine_km,
                   load_geography, load_resources)


from .economy import EconomyMixin
from .fog import FogMixin
from .geography import GeographyMixin
from .labour import LabourMixin
from .projects import ProjectsMixin
from .society import SocietyMixin


class Sim(EconomyMixin, FogMixin, GeographyMixin, LabourMixin,
          ProjectsMixin, SocietyMixin):
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
        self._wage_index_base = self.wage_index
        self.state_capacity = float(self.civ.get("state_capacity", 0.7))
        self.pop_scale = max(0.05, float(self.civ.get("population", 65e6)) / 65e6)
        # A PLAGUE IS A HIT TO THE WHOLE LABOUR MARKET, NOT ONLY TO YOU. A
        # playtester watched the Black Death take a third of their own staff
        # and nothing else happen to the world around them, and asked why a
        # mortality event this size left everybody ELSE's wages untouched.
        # self._pop_scale_base is this civilization's steady-state size;
        # self.pop_deficit is how far below it the whole society currently
        # sits, and self.pop_scale (read everywhere else in the engine) is
        # always base * (1 - deficit). _demographic_recovery() below is the
        # only place that moves deficit, wage_index or pop_scale_base after
        # today; _shocks() in society.py only ever adds to the deficit.
        self._pop_scale_base = self.pop_scale
        self.pop_deficit = 0.0
        self._pop_recovery_years = 0.0
        # Population-raising technologies (sanitation, antisepsis, crop
        # rotation, canning...) queue their effect here instead of applying
        # it the year they complete - see apply_tech_effects in society.py.
        # Each entry is [fraction-of-baseline added per year, years left to
        # add it]: a lower death rate shows up in a headcount a generation
        # later, not the day a latrine opens.
        self._pop_tech_pending = []
        self.year = self.cfg["start_year"]
        c = self.cfg
        # AT THIS SOCIETY'S PRICES, like everything else you will spend it on.
        # The kits are quoted in Rome 100 AD denarii, and once revenue and
        # living costs started converting (see economy.living_cost) leaving the
        # purse flat meant "four hundred denarii" bought a third more months of
        # bread in Luoyang than in Scandinavia, silently, for no modelled
        # reason. A kit is "a few months' subsistence", and a few months'
        # subsistence costs what it costs where you are.
        self.capital = float(c["start_capital"]) * self.price_index
        self.done = set()
        self._done_seq = None
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
        self.forgotten = {}              # {node: year} destroyed by a sacking
        self.opened_year = {}            # {node: year} the doors first opened
        self.paid_towards = {}           # {node: denarii} sunk before it stopped
        self.last_taught = {}            # {trade: year} auto_train last taught it
        self.wages_prepaid = 0.0         # first-year wages `hire` already took
        # WHAT YOU ACTUALLY RUN, as opposed to what you know how to do. Revenue
        # and upkeep follow this set and nothing else does. See is_venture and
        # open_venture in projects.py: completing the research used to start
        # paying you whether or not you ever opened the doors.
        self.operating = set()
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
            # OFF FOR A PLAYER, like every other automation, and on for the
            # optimizer, which the long civilisation runs are calibrated
            # against. This is the most consequential thing the game does
            # without being asked: it discards technologies you built, which
            # under fog are the only score there is. A break tester found it on
            # by default and quietly deleting their work. Nothing stops a
            # player shedding a loss-maker by hand - `mothball` does exactly
            # that, and gets it back with `restore`.
            "auto_shed":     not manual,
            # Open every concern that plainly pays for itself. On for the
            # optimizer, whose long runs are calibrated against a household
            # that does run what it builds, and off for a player, for whom
            # deciding what to actually operate is the point.
            "auto_open":     not manual,
            # Buy a job from an outside shop when a few pairs of hands are the
            # only thing standing between you and something you need.
            "auto_commission": not manual,
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
                self._done_changed()
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
        # AGAIN, NOW THAT starting_techs ARE IN. grant_ambient walks the tree
        # crediting free tier-0 work whose prerequisites are already done, and
        # it ran BEFORE this loop - so anything a civ's named starting
        # technology unlocks was still ungranted when turn one began, and
        # arrived on the player's first `step` as "COMPLETED 100: Amphitheatre
        # with tiered seating". A play tester reported those, correctly, as
        # completions for things they had never started. Rome's amphitheatre
        # and barrel vault are not the founder's work and are not news.
        self.grant_ambient()

    def _demographic_recovery(self, yr):
        """Mortality shocks fade and population-raising technologies build in.

        Two unrelated inputs move the same two numbers, self.pop_scale and
        self.wage_index, and they are handled together because both ARE the
        same underlying thing: how many people this society has to work with
        this year. A staff_loss hazard in _shocks() (society.py) adds to
        self.pop_deficit, the fraction the whole society currently sits
        below its baseline size. A population-raising technology adds to
        self._pop_scale_base through self._pop_tech_pending, queued by
        apply_tech_effects() (society.py).

        The deficit decays EXPONENTIALLY rather than healing on a fixed
        clock, so a run always reads "a little better than last year" rather
        than sitting frozen until some cliff-edge recovery date:
        deficit *= exp(-1/tau), with tau set so that after
        self._pop_recovery_years the deficit is down to about 5% of where
        the shock left it (e**-3 ~= 0.05, the standard "three time
        constants" rule of thumb). England's population took roughly 150
        years to regain its pre-Black-Death level (Broadberry et al.,
        British Economic Growth, 2015), and england_1300.json's Black Death
        entry is staff_loss 0.45, so 150 years is calibrated to THAT hazard
        specifically; every other hazard's recovery horizon scales off it in
        proportion to how much of the population it actually took, so the
        Antonine plague (0.28) gets a shorter, gentler recovery than the
        Black Death, not the same 150 years regardless of size.
        """
        if self.pop_deficit > 1e-6:
            tau = max(10.0, self._pop_recovery_years) / 3.0
            self.pop_deficit *= math.exp(-1.0 / tau)
        else:
            self.pop_deficit = 0.0
        if self._pop_tech_pending:
            still = []
            for per_year, years_left in self._pop_tech_pending:
                self._pop_scale_base += per_year
                if years_left > 1:
                    still.append((per_year, years_left - 1))
            self._pop_tech_pending = still
        self.pop_scale = max(0.05, self._pop_scale_base * (1.0 - self.pop_deficit))
        # LABOUR SCARCER, SO DEARER. Elasticity 0.9 means a population still a
        # third below trend (deficit 0.33) carries about a 30% wage premium;
        # run for a century, as the Black Death's deficit roughly does before
        # it has decayed away, and that compounds into the rough doubling
        # Phelps Brown and Hopkins' English real-wage index shows across the
        # century after 1348, without the elasticity itself needing to be
        # implausibly large. wage_index is what ANNUAL_WAGE, WAGES and every
        # hiring, teaching and payroll cost in the engine are already
        # multiplied by, so this one number is the whole of "higher wages
        # raise the cost of everything built with labour" - nothing else
        # downstream needs to change.
        self.wage_index = self._wage_index_base * (1.0 + 0.9 * self.pop_deficit)
        # SAY WHY THE WAGE BILL MOVED. A plague that quietly doubles every
        # hiring and teaching cost for decades and never says so reads as the
        # economy drifting for no reason - exactly the complaint this whole
        # mechanism exists to answer. Throttled the same way the debasement
        # and output_factor messages are (see _shocks): once when it is worth
        # mentioning, then a reminder at most every 15 years, not every year
        # of a shortfall that can run for a century.
        premium = (self.wage_index / self._wage_index_base - 1.0) * 100
        if premium > 0.5 and yr - getattr(self, "_said_wage_cascade", -999) >= 15:
            self._said_wage_cascade = yr
            self.log.append((yr, "population still %d%% below trend: wages "
                                 "(and anything billed in them) are running "
                                 "%d%% above normal for here, and will ease "
                                 "as the population does"
                             % (round(self.pop_deficit * 100), round(premium))))

    # -- helpers ------------------------------------------------------------

    # Years between one automatic teaching of a trade and the next. Long
    # enough that restoring a lost trade is an event rather than a habit.
    RETEACH_EVERY = 25

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

    def step(self):
        c = self.cfg
        yr = self.year
        # WHERE SCANDAL STOOD WHEN THE PLAYER LAST LOOKED. `state` prints the
        # chance of being denounced from the CURRENT scandal, and scandal moves
        # DURING the step - so a break tester read "scandal 21.9 ... 0% chance
        # of being denounced this year", pressed step once, and the same batch
        # printed the first warning and "RUN ENDS: denounced: as a sorcerer".
        # The figure was never wrong; it was answering about a year that had
        # already gone. A player needs the direction as well as the level, and
        # this is the only place that knows both.
        self.scandal_last_year = self.scandal

        # 0. PEOPLE WHOSE APPRENTICESHIP ENDED. This block used to sit at the
        #    very BOTTOM of step(), after the year's work had already been
        #    handed out - so machinists promised "ready in 102" were not usable
        #    on anything until 103, and a break tester timed both the message
        #    and the ready_year and found each a year late. A man who finishes
        #    his training at the turn of the year works that year.
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
                        # They are trained now, so _resync_pools counts them
                        # from the people you actually hold - see the note
                        # there about why adding to self.artisans directly was
                        # thrown away at the next call.
                        self.log.append((self.year,
                                         "%g of the people you bought finish "
                                         "learning the work" % round(cap / 0.55, 1)))
                else:
                    still.append(row)
            # BEFORE the resync, not after: _resync_pools counts who is still
            # learning off this very list, so recomputing while the matured row
            # was still on it cost a whole extra year of everybody's time.
            self.training = still
            self._resync_pools()


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
        # TWO THINGS WERE WRONG WITH HOW THIS USED TO DECIDE, and a break tester
        # found both at once: they hired six smiths with two thirds of their
        # credit line still unused, stepped one year, and every one of the six
        # was gone, with nothing whatever in the log to say so.
        #
        # 1. The trigger was `capital < 0`, which is being overdrawn, not being
        #    unable to pay. A household with credit left borrows and makes
        #    payroll; that is what credit is for, and enforce_credit_limit
        #    already models the point where it runs out. Letting your staff go
        #    the first year you dip a denarius below zero, with the lender still
        #    willing, is not what an enterprise does.
        # 2. The gap it tried to close was measured with living_cost(), which
        #    INCLUDES the wage bill, so the deficit being closed was the payroll
        #    PLUS the founder's own food, rent and appearances. Firing people
        #    cannot buy your own dinner. Whenever base living exceeded revenue -
        #    which it does in every early game - the loop ran off the end of the
        #    staff list and emptied it. And the log line sat inside `if net >=
        #    0`, so the one case that always happened was the one case that said
        #    nothing at all.
        #
        # The honest rule is that your people are paid out of what is left after
        # everything else, INCLUDING what somebody will still lend you, and you
        # shed only the part of the payroll that will not cover.
        payroll = self.wage_bill()
        other = (self.upkeep() + (self.living_cost() - payroll)
                 + self.mine_operating_cost())
        # capital is negative in arrears; credit_limit() is how far into arrears
        # anyone will let you go, so this is what you can actually still spend.
        headroom = max(0.0, self.capital + self.credit_limit())
        can_pay = self.revenue() - other + headroom
        # NOT GATED BY A POLICY, and this is the one automatic thing that is not.
        # A policy switch is for something the game decides FOR you - who to
        # hire, what to mothball - and every one of those is yours to turn off.
        # People leaving a household that has no money and no credit to pay them
        # is not a decision the game is making on your behalf, it is the world
        # answering one you already made, the same as the arrears bleed below.
        # The `policy` reply says so in as many words now, because the tester
        # read its promise as covering this and was entitled to.
        if payroll > can_pay and self.employees:
            short = payroll - can_pay
            gone = 0.0
            # shed, dearest first, until the wages you are left with fit
            for t in sorted(self.employees, key=lambda t: -ANNUAL_WAGE.get(t, 375.0)):
                if short <= 0:
                    break
                wage = ANNUAL_WAGE.get(t, 375.0) * self.wage_index * self.price_index
                if wage <= 0:
                    continue
                cut = min(self.employees[t], short / wage)
                self.employees[t] -= cut
                short -= cut * wage
                gone += cut
                if self.employees[t] < 0.05:
                    self.employees.pop(t)
            self._resync_pools()
            # ALWAYS, not only when it worked. Losing the staff you paid to hire
            # is more consequential than any of the flavour events that do get
            # logged, and a player who is not told has to notice their own wage
            # bill hit zero to find out.
            if gone > 0.005:
                self.log.append((yr, "you cannot pay everyone: %.1f of your staff "
                                     "leave for work that pays" % gone))
        # NOT `capital > 0`. This is the same catch-22 auto_open_ventures was
        # already caught by and had fixed: a household in arrears could never
        # take on the people whose work is the only way out of arrears. And a
        # run that keeps a project going keeps a balance in the red almost
        # permanently, so the gate was not "you are ruined", it was "you are
        # building something". A Rome run traced for this comment sat at about
        # -5,000 against a credit line of 8,000 for five hundred years with a
        # clear surplus of 650 a year and hired NOBODY: zero scholars and zero
        # craftsmen in 600 AD, 387 technologies, no goal. Deep in arrears is
        # deep in arrears; the affordability arithmetic below - which already
        # subtracts living cost, upkeep and the wages you are carrying - is
        # what decides how many, and it correctly says nobody when there is
        # nothing spare.
        _hire_room = (self.capital >= 0
                      or -self.capital <= self.credit_limit() * 0.75)
        if (self.policy.get("auto_hire", not self.manual) and _hire_room):
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
            # SPECIALISTS MUST NOT EAT THE GENERALISTS. The generic bucket was
            # the remainder after every taught trade had taken its share, so
            # once the top-up kept five specialist trades at two apiece the
            # artisans were squeezed to nothing - a play tester watched theirs
            # go 6.0 to 0.03 while scholars filled every place, and since
            # artisans are what supervise a concern, twenty-two concerns closed
            # and their net went from +8,010 a year to -3,027. A household of
            # nothing but specialists cannot keep its own doors open.
            self.employees["artisan"] = max(craft * 0.25, craft - specials)
            if self.scholars > 0:
                self.employees["scholar"] = self.scholars
            # REPLACE THE PEOPLE YOU LOSE, trade by trade. Attrition was eating
            # the taught trades (the engineers went from 1.9 to 0.3 over sixty
            # years) and nothing ever replaced them, because the top-up only knew
            # about the two generic buckets. A programme that trains the first
            # machinists in the world and then lets them die out has not trained
            # anybody.
            # FROM THE TRADES YOU TAUGHT, not from the keys that happen to be
            # left. A trade falls out of `employees` entirely once the last of
            # them drops below 0.05, and this loop only ever looked at the
            # keys - so the moment a taught trade went to nothing it stopped
            # being replaced, permanently. That is the leak behind a Rome run
            # that built 829 technologies and could not begin
            # precision_three_plate: not that machinists were never taught, but
            # that the last one died and the top-up had already forgotten they
            # existed.
            for t in sorted(set(self.employees) | set(self.trades_created)):
                if t in ("artisan", "scholar"):
                    continue
                have = self.employees.get(t, 0.0)
                want = max(have, 2.0 if t in self.trades_created else 0.0)
                short = want - have
                if short > 0.02 and self.capital > ANNUAL_WAGE.get(t, 375.0) * 6:
                    self.employees[t] = have + short
                    self.capital -= short * ANNUAL_WAGE.get(t, 375.0) * self.price_index
            self._resync_pools()
        # BUY A JOB WHEN A HANDFUL OF HANDS IS THE ONLY THING IN THE WAY.
        # Letting contracted craftsmen count toward a project's staff
        # requirement fixed the Norse deadlock for a person at a keyboard and
        # not at all for the optimizer, because nothing in the engine had ever
        # called commission(). A run that can see the wall, has the money, and
        # has no way to spend it on the wall is the same dead end wearing a
        # different hat.
        if self.policy.get("auto_commission", not self.manual):
            self.auto_commission_for_blocked()
        self.directors_extra += (di_cap - self.directors_extra) * 0.12 - self.directors_extra * ATTRITION
        self.artisans = max(0.0, self.artisans)
        self.scholars = max(0.0, self.scholars)
        self.directors_extra = max(0.0, self.directors_extra)
        # SAY IT WHEN IT CROSSES A WHOLE PERSON. A play tester noticed "10,175
        # founder-hours free this year (2,000 of your own, plus 4.5 deputies at
        # 1,800 hours each)" by accident, after playing for a century on the
        # assumption that their year was two thousand hours and would stay
        # that way. The single largest change to the resource the whole game
        # is built on had never announced itself.
        _whole = int(self.directors_extra)
        if _whole > int(getattr(self, "_said_deputies", 0)):
            self._said_deputies = _whole
            self.log.append((yr, "you now have %d deput%s directing work in "
                                 "your name: your year is %s hours instead of "
                                 "%s. They came with the institutions you built"
                             % (_whole, "y" if _whole == 1 else "ies",
                                "{:,.0f}".format(self.director_pool()),
                                "{:,.0f}".format(self.cfg["founder_hours_per_year"]))))

        # 2. money
        self.economy = self.economy_index()
        lc = self.living_cost()
        # THE YEAR YOU PAID FOR IN ADVANCE IS NOT BILLED AGAIN. `hire` takes a
        # finder's fee and the first year's wages up front, and living_cost()
        # carries the whole payroll, so a smith at 281 a year cost 566 in his
        # first year: the advance, then the identical year again at the next
        # step. A break tester found hire-then-fire in one turn burned the
        # advance for no work at all.
        prepaid = min(lc, getattr(self, "wages_prepaid", 0.0))
        lc -= prepaid
        self.wages_prepaid = 0.0
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
        # A CONCERN NEEDS SOMEBODY WATCHING IT EVERY YEAR, not only on the day
        # you open it. `open` refused without supervisors and then nothing ever
        # looked again, so a break tester hired five craftsmen, opened eleven
        # concerns in one turn, fired all six people, and watched net income
        # RISE - "EMPLOY: 0 people" with seventeen concerns running, and the
        # same loom still paying 435 a year in 1800 with nobody employed,
        # straight through the Black Death.
        self.close_unstaffed_ventures(yr)
        # Open what plainly pays for itself, before the books are struck: a
        # concern you opened this year is a concern that earns this year.
        if self.policy.get("auto_open", not self.manual):
            self.auto_open_ventures()
        self.charge_interest(yr)
        if self.policy.get("auto_shed", True):
            self.shed_loss_makers(yr)
        self.warn_near_the_limit(yr)
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
            # BEING IN DEBT IS NOT THE SAME AS BEING INSOLVENT. This counted a
            # year of arrears for every year capital was below zero, whatever
            # the household was earning - so a Rome run with revenue of 1,006
            # against 470 of living costs, paying its debt down at 522 a year,
            # was still "in arrears 183 years" and still refused permission to
            # start anything, which is what kept it from ever climbing out. A
            # household running a surplus is paying its creditors, and nobody
            # calls that insolvency; what the counter is for is the household
            # whose income does not cover its costs.
            _net = (self.revenue() - self.upkeep() - self.living_cost()
                    - self.mine_operating_cost())
            if _net > 0:
                self.insolvent_years = 0
            else:
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
                        # CLOSE IT, DO NOT UNLEARN IT - and above all do not do
                        # both. Discarding from `done` while adding to
                        # `mothballed` produced a state no verb could clear: a
                        # play tester lost precision_three_plate to a sack, and
                        # `start` sent them to `restore`, `restore` said they no
                        # longer knew how, `open` said they had not built it and
                        # `mothball` said there was nothing to shut. That node
                        # gates the whole precision branch, so `available` read
                        # "0 startable now" for a hundred and eighty years while
                        # they sat on a quarter of a billion denarii. The same
                        # pair of lines was fixed in enforce_credit_limit and in
                        # shed_loss_makers and survived here.
                        self.operating.discard(k)
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
            if self.capital > 6000 and self.artisans < 12 and self.running("workshop_first"):
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
        # Population and the wage premium it drives recover/build in on their
        # own clock too, and must run before this year's shocks get a chance
        # to add a fresh deficit - see _demographic_recovery for why.
        self._demographic_recovery(yr)

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
        # ONLY THE NODES THAT COULD EVER BE GRANTED THIS WAY, not the whole
        # tree. tier, ph, _total_cost and foreign-institution status are all
        # fixed tree/civ data that cannot change after construction (see
        # _is_foreign_institution), so the set of nodes this loop will ever
        # look twice at is fixed too - computed once and reused, in the same
        # relative order as `self.order`, which is what makes this provably
        # identical to walking the full list every year: every node this
        # skips was going to fail the same tier/ph/cost/foreign test again
        # anyway. A Rome run walked all 2,831 nodes here every year for 500+
        # years to find the same 130 candidates; most of those had also
        # already been granted and were only ever going to hit `k not in
        # self.done` and nothing else.
        cand = getattr(self, "_auto_grant_candidates", None)
        if cand is None:
            cand = self._auto_grant_candidates = [
                k for k in self.order
                if not self._is_foreign_institution(k)
                and self.nodes[k]["tier"] == 0 and self.nodes[k]["ph"] == 0
                and self.nodes[k]["_total_cost"] <= 1]
        for k in cand:
            if k in self.done or k in self.active:
                continue
            n = self.nodes[k]
            if all(p in self.done for p in n["pre"]):
                self.done.add(k)
                self._done_changed()
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
            # LOCAL, PER-YEAR MEMO for market_supply()/trade_available().
            # Both are pure functions of staff and trades_created, which this
            # whole block only READS - train(), below, adds to trades_created,
            # but that happens once, at the very end, after every use of these
            # memos - so the same handful of distinct trade names (maybe
            # thirty) get recomputed from scratch once per NODE that lists
            # them in `lab`, and hundreds of nodes across the tree share the
            # same absent trade (machinist, engineer, ...). This dict is a
            # plain local, created fresh every call and discarded when the
            # block ends, so it needs no invalidation logic at all: nothing
            # outside this block ever reads it, so it cannot go stale.
            _ms_memo, _ta_memo = {}, {}
            def _market_supply(t):
                v = _ms_memo.get(t)
                if v is None:
                    v = _ms_memo[t] = self.market_supply(t)
                return v
            def _trade_avail(t):
                v = _ta_memo.get(t)
                if v is None:
                    v = _ta_memo[t] = self.trade_available(t)
                return v
            # Anything already in hand that has lost its trade comes FIRST: those
            # projects are burning a slot and will be halted if nobody turns up.
            for k in self.active:
                for t in self.nodes[k]["lab"]:
                    if _market_supply(t) <= 0.0:
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
            # EXISTING IS NOT THE SAME AS ANYBODY BEING LEFT. A trade you
            # taught stays "available" for ever, so once the last machinist
            # had died of old age this loop skipped every node that needed
            # one and nobody was ever taught again. A Rome run built 829
            # technologies, sat on 31.9M denarii, and could not begin
            # precision_three_plate - which gates master_screw, the screw
            # lathe and the entire precision branch, ninety-nine of the
            # hundred and forty-six nodes on the road to the goal. This is
            # the same distinction start_reason learned an hour earlier.
            # Hoisted out of the loop below: it closes only over `self` and
            # the memos above, never over the loop variable `k`, so defining
            # it fresh on every one of ~2,800 iterations bought nothing.
            def _gone(t):
                return (not _trade_avail(t)
                        or (_market_supply(t) <= 0.0
                            and self._trade_headcount_pending(t) <= 0.0))
            for k in self.order:
                if k in self.done or k in self.active:
                    continue
                n = self.nodes[k]
                if not any(_gone(t) for t in n["lab"]):
                    continue
                if not self.start_reason(k, ignore_trade=True)[0]:
                    continue
                for t in n["lab"]:
                    if _gone(t):
                        want[t] = want.get(t, 0) + 1
            # NOT EVERY YEAR. Teaching two of a trade costs about nine hundred
            # of the founder's two thousand hours plus their keep, and once
            # re-teaching a lost trade was possible at all the loop did it
            # continuously: three Rome seeds fell from 829, 858 and 1,257
            # technologies to 229, 56 and 188, the whole difference going into
            # a teaching treadmill. A trade is worth restoring; it is not worth
            # half of every year for ever.
            _taught = getattr(self, "last_taught", None)
            if _taught is None:
                _taught = self.last_taught = {}
            want = {t: v for t, v in want.items()
                    if yr - _taught.get(t, -999) >= self.RETEACH_EVERY}
            # AND ONLY IF YOU CAN PAY THEM. train() checked hours, literacy and
            # household room and never once looked at money - so a Rome
            # household earning 1,232 a year taught itself two engineers at
            # 625 each, and every year after that its whole income went on
            # their wages. That is the poverty trap three separate testers
            # described from three directions: "auto_train bought me chemists,
            # engineers, machinists and opticians I had no work for", "-6,900
            # denarii in three steps", and a run that sat at 144 technologies
            # from 125 AD to 300. A trade you cannot pay for is not a trade you
            # have; it is a wage bill that stops you building anything.
            #
            # Two standards, because the two cases are not alike. A trade a
            # project ALREADY IN HAND is waiting on (scored 500 above) is worth
            # borrowing against: that work is paid for and stops without it.
            # A trade for something you might start one day has to come out of
            # what you are actually clearing.
            _spare_tr = self.revenue() - self.upkeep() - self.living_cost()
            for t, _score in sorted(want.items(), key=lambda kv: (-kv[1], kv[0]))[:1]:
                _wages = 2.0 * ANNUAL_WAGE.get(t, 375.0) * self.price_index * self.wage_index
                _budget = (max(0.0, _spare_tr) + max(0.0, self.capital) * 0.10
                           if _score >= 500 else max(0.0, _spare_tr) * 0.5)
                if _wages > _budget:
                    continue
                _first = t not in self.trades_created
                ok, _msg = self.train(t, 2)
                # THE COOLDOWN IS ON TEACHING, NOT ON TRYING. Recording the
                # attempt meant a refusal - no room in the household, no hours
                # left, nobody to teach from - burned the trade's whole
                # twenty-five years, so the run went on needing machinists and
                # never asked again.
                if ok:
                    _taught[t] = yr
                    self.log.append((yr, "you begin teaching the first %ss this "
                                         "world has ever had" % t if _first else
                                     "the last %ss are gone; you begin teaching "
                                     "more" % t))

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
            max_active = int(2 + self.director_pool() / 2000.0
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
                # INTEREST IS A FIXED COST, and leaving it out is how a
                # household in arrears decides it has a surplus. A Rome run
                # paying 552 a year of interest computed its five years of
                # headroom as though that money did not exist, committed
                # against it, and went from -369 to -7,827 in twenty-five
                # years - then bled for four centuries. Every other net in this
                # program was taught to count arrears; this one was missed
                # because it is not a net, it is a budget.
                fixed = (self.upkeep() + self.living_cost()
                         + self.mine_operating_cost()
                         + max(0.0, -self.capital) * self.debt_interest_rate())
                room = (max(0.0, self.capital) + self.credit_limit() * 0.5
                        + max(0.0, self.revenue() - fixed) * 5.0
                        - sum(st.get("cost_left") or 0.0 for st in self.active.values()))
                if self.project_cost(k) > room:
                    continue
                if k in self.bounty_set and self.bounty_eligible(k) and self.post_bounty(k):
                    continue
                # lab_left starts full here too, for the same reason
                # start_project (projects.py) sets it at creation rather than
                # leaving lab_year_draw to guess it from ph_left the first
                # time it runs - see the comment there.
                self.active[k] = dict(ph_left=float(n["ph"]), yrs=0.0, spent=0.0,
                                      cost_left=self.project_cost(k),
                                      lab_left=dict(n["lab"]))

        # 4c. materials. Buy the woodland and dig the beds BEFORE the shortage
        #     bites, which is what a competent manager does and what the old
        #     model never had to think about at all.
        self.commission_mines()
        thr = self.resource_throttle()
        # THE GATE WAS THE DEADLOCK. `capital > 3000` was meant to stop this
        # spending a poor household's last coin, and instead it made charcoal
        # a wall nobody in arrears could ever climb: no woodland, so the
        # furnaces run at a fraction, so nothing is built, so no money, so
        # still no woodland. An England run measured 521 charcoal-short years
        # out of 700, ended on 31 technologies with 71 hectares of coppice and
        # -6,332 in hand, and settled its debts twenty-eight times.
        #
        # Coppice is the cheapest thing in the tree and the one that decides
        # whether a furnace runs at all, so what it is really gated on is
        # whether you can raise the price of some, which is what
        # spending_power says. Below that the branch does nothing anyway,
        # because buy_forest refuses what you cannot pay for.
        _can_raise = self.spending_power("buy")
        if (thr < 0.9 and _can_raise > self.FOREST_COST_PER_HA * self.price_index
                and (self.policy.get("auto_mine", not self.manual)
                     or self.policy.get("auto_forest", not self.manual))):
            # Charcoal is GROWN, so the answer is woodland. Everything else in
            # this list is DUG, so the answer is a mine, and the old model had
            # no answer at all for coal: the binding constraint fell through
            # both branches and the run simply sat throttled. That is why coal
            # showed 1,669 shortage-years in a 395 year run.
            if self.binding == "charcoal":
                if self.policy.get("auto_forest", not self.manual):
                    # SIZED FROM THE SHORTFALL, like the mine branch below,
                    # rather than from a flat share of cash. A tenth of a
                    # denarius of capital bought a ten-thousandth of a hectare
                    # while the demand was measured in hundreds of tonnes.
                    _need_t = (self.annual_material_demand().get("charcoal_kg", 0.0)
                               / 1000.0) - self.forest_ha * self.CHARCOAL_PER_HA
                    _want_ha = max(0.0, _need_t) / max(self.CHARCOAL_PER_HA, 1e-9)
                    _afford_ha = (_can_raise * 0.35
                                  / (self.FOREST_COST_PER_HA * self.price_index))
                    self.buy_forest(min(400.0, _want_ha, _afford_ha))
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
            elif (self.binding == "saltpetre"
                    and self.policy.get("auto_mine", not self.manual)):
                # GATED, like every other automatic purchase. This branch sat
                # outside the policy check and took five per cent of a manual
                # player's capital every year they were short of nitre,
                # without a line in the log and without anything they typed.
                spend = min(self.capital * 0.05, 2000)
                self.capital -= spend
                self.nitre_bed_m2 += spend / self.NITRE_COST_PER_M2
                self.log.append((yr, "laid down %d square metres of nitre bed "
                                     "for %d denarii (auto_mine)"
                                 % (spend / self.NITRE_COST_PER_M2, spend)))
        if thr < 0.6 and self.binding:
            # SAY WHAT TO DO ABOUT IT. A play tester read "SHORT OF SALTPETRE:
            # work at 5% of plan" for thirty years and could not find out what
            # saltpetre was for, who wanted it, or what would fix it. A number
            # that low with no remedy attached reads as the game being stuck.
            self.log.append((yr, "SHORT OF %s: work running at %d%% of plan. %s"
                             % (self.binding.upper(), thr * 100,
                                self.shortage_remedy(self.binding))))

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
                    st["blocked_on_trades"] = blocked
                    if st["stalled_years"] >= 4:
                        self.log.append((yr, "HALTED %s: there is nobody here who can "
                                             "do this work (%s). What you spent is lost"
                                         % (k, ", ".join(blocked[:2]))))
                        self.active.pop(k, None)
                        self.bountied.discard(k)
                    else:
                        # WARN BEFORE THE MONEY GOES. Six projects were wiped in
                        # one year for a play tester who had no way to list what
                        # was at risk: the countdown ran silently for three years
                        # and then took everything spent. Say it each year, with
                        # the number of years left and what would fix it.
                        _left = 4 - st["stalled_years"]
                        self.log.append((yr, "%s cannot go on: no %s here. It has "
                                             "%d year%s before it is abandoned and "
                                             "what you spent on it is lost. Teach "
                                             "the trade, or 'stop %s' now and keep "
                                             "your hours"
                                         % (k, " or ".join(blocked[:2]), _left,
                                            "" if _left == 1 else "s", k)))
                        # Nothing happened here this year - say so, rather than
                        # leaving last year's hours_offered/effective sitting on
                        # the entry looking like they still applied.
                        st["hours_offered_this_year"] = 0.0
                        st["hours_effective_this_year"] = 0.0
                    continue
                st["stalled_years"] = 0
                per = min(remaining, max(st["ph_left"], n["ph"] / max(n["yrs"], 1.0))) * self.throttle
                remaining -= per
                # WHAT WAS ACTUALLY TAKEN OFF, which is not the same as what was
                # offered: `per` is allowed to exceed ph_left (the max() above
                # offers a full year's worth even to a project with an hour to
                # run), and the subtraction clamps at zero. The refunds below
                # were computed from `per` regardless, so a project with 10
                # hours left could be offered 500, have its 10 taken, and be
                # handed 200 back - ending the year with twenty times the hours
                # it began with. A playtester found the far end of that: a
                # progress bar reading "-67% of your hours spent", with
                # founder_hours_left larger than founder_hours_total. You cannot
                # be refunded work you never did.
                spent_hours = min(per, st["ph_left"])
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
                # LABOUR BY TRADE. The old model pooled every trade into one
                # bucket of hired hours, so 450 hours of engineer and 450 hours
                # of labourer were the same resource. They are not, and the wage
                # table has said so all along. What binds now is the scarcest
                # trade this project actually needs.
                #
                # HOURS ARE A TOTAL AND A CEILING NOW, NOT A FIXED ANNUAL TOLL.
                # See ProjectsMixin.lab_year_draw (projects.py) for the finding
                # that forced this and the reasoning behind the new shape; this
                # call site only has to act on what it returns.
                hh, worst, frac, _abandon = self.lab_year_draw(k, st, frac, hired_left)
                if _abandon:
                    self.log.append((yr, "ABANDONED %s: %s" % (k, _abandon)))
                    self.active.pop(k, None)
                    self.bountied.discard(k)
                    continue
                if worst < 1.0:
                    # NEVER ALL OF IT. The refund says "hours offered but not
                    # usable, because the trade was booked" - and with no floor
                    # under it, it could hand back every hour that had actually
                    # gone in. A break tester watched a project's founder-hours
                    # sit unchanged for ever because its scarcest trade was
                    # short, the bill fully paid, the calendar long past, making
                    # no progress at all while holding an entire trade's pool
                    # and freezing other projects behind it.
                    #
                    # If a fraction `worst` of the work could be done, then a
                    # fraction `worst` of it WAS done, and that much can never
                    # be given back. Progress is now strictly positive whenever
                    # anybody at all can be found.
                    give_back = min(spent_hours - refunded,
                                    per * 0.4 * (1.0 - worst),
                                    spent_hours * (1.0 - worst))
                    st["ph_left"] += max(0.0, give_back)
                    refunded += max(0.0, give_back)
                    # Remember it. A tester sat on 696,350 denarii watching three
                    # projects report waiting_on "money" with 2.3, 84 and 158
                    # denarii left to pay, and reasonably concluded the spend cap
                    # was broken. It was not: the trades those projects needed
                    # were fully booked, so almost nothing could be paid FOR. The
                    # mechanic was right and the label was a lie. (short_of_trade
                    # itself is now set inside lab_year_draw, against the same
                    # pace this comment describes.)
                if hh > hired_left:
                    frac *= hired_left / max(hh, 1e-9)
                    hh = hired_left
                # THE INSTALMENT IS WHAT A CONSTRAINED YEAR CAN DO; THE BILL IS
                # WHAT IS LEFT. This used to work the payment out first and then
                # multiply it by each shortage in turn, so once the remaining
                # balance was smaller than a year's instalment you paid a
                # FRACTION OF WHAT WAS LEFT every year, for ever: a geometric
                # decay that approaches zero and never reaches it, while
                # completion needs the bill down to half a denarius. A
                # playtester watched one project sit at "71% done" for
                # twenty-five years with cash in hand and no idea why. Working
                # it out from the already-scaled `frac` means a shortage sets
                # how FAST you can pay and never stops the last payment landing.
                money = min(st["cost_left"], self.project_cost(k) * frac)
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
                    # Capped at what was actually taken off, and at what has not
                    # already been handed back by the trade-shortage refund
                    # above. See spent_hours: you cannot be refunded work you
                    # never did, and you cannot be refunded the same hour twice.
                    give_back = min(spent_hours - refunded, per * (1.0 - funded_frac))
                    st["ph_left"] += max(0.0, give_back)
                    refunded += max(0.0, give_back)
                    st["underfunded_this_year"] = True
                    # WHY, not just that. A playtester ran deep into debt and
                    # watched every project report hours "offered" and none
                    # "effective", with nothing in help, why, money or risk
                    # explaining it. Arrears are the reason: the purse a project
                    # may draw on is what you hold plus part of your credit,
                    # less what your fixed costs need, and in arrears that is
                    # nothing at all.
                    st["why_underfunded"] = (
                        "in arrears: after fixed costs there is nothing left to "
                        "draw on, so the hours offered this year did almost "
                        "nothing" if self.capital < 0 else
                        "this year's instalment is more than the purse will bear")
                else:
                    st.pop("underfunded_this_year", None)
                    st.pop("why_underfunded", None)
                self.capital -= money
                self.total_spend += money
                st["spent"] += money
                st["cost_left"] = max(0.0, st["cost_left"] - money)
                # spent_hours, NOT per. `per` is what was OFFERED, and it is
                # allowed to exceed the hours the project actually had left; the
                # refunds above are capped at spent_hours for exactly that
                # reason, and this line was left uncapped. A sweep of the
                # playtest notes found a project reporting 387.2 effective hours
                # a year for four consecutive years while founder_hours_left sat
                # unchanged at 112.8 - work reported that provably did not
                # happen, about the one resource the whole game is built on.
                st["hours_effective_this_year"] = round(max(0.0, spent_hours - refunded), 1)
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
                # HALF AN HOUR IS NOTHING LEFT TO DO. The give-back hands back a
                # fraction of what was offered, so on a throttled project
                # ph_left decays geometrically towards zero and never reaches
                # it: a break tester's `logarithms` sat at 1.29e-25 founder-hours
                # with the bill paid and thirty years elapsed, complete in every
                # sense except the comparison. The bill already had this exact
                # fix and this exact reason (see `money` just above, and
                # cost_left <= 0.5 on the same line); hours never got it.
                if st["ph_left"] < 0.5:
                    st["ph_left"] = 0.0
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
            # ONLY IF IT PAYS BETTER THAN THE PRACTICE IT DISPLACES. Wage hours
            # now cost you the share of your practice they were sold out of
            # (see practice_attention), and without this check the optimizer
            # went on taking a scribe's wage at the price of a physician's fee
            # and lost Rome a sixth of its runs. A man with a practice does not
            # go and copy documents for less than the practice earns; that is
            # the whole reason `work` is the thing you do BEFORE you have one.
            # NOT `pool`. That name already held the year's project budget,
            # computed at 4b, and reusing it here overwrote it - so
            # hours_this_year then reported "offered_to_projects" against the
            # WHOLE year instead of against the project budget. The year's
            # hours added up to 2,900 out of 2,000, which is exactly the sort
            # of arithmetic a player cannot argue with and cannot trust.
            year_hours = max(1.0, self.director_pool())
            practice_lost = self.revenue() * (hours / year_hours) * (
                1.0 if self.practice_attention() > 0 else 0.0)
            rate = (ANNUAL_WAGE.get(trade, 375.0) / self.HOURS_PER_PERSON_YEAR
                    * self.price_index * self.wage_index
                    * (1.0 + min(0.5, self.reputation / 200.0)))
            if hours * rate > practice_lost:
                _, err = self.work_for_wages(trade, hours)
                # Kept in step with `remaining` so hours_this_year (below) does
                # not count hours sold for wages here as still unused.
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
        # WARN BEFORE IT KILLS YOU. A play tester built 952 technologies, was
        # three nodes from the goal, and the run ended on a 2% roll against an
        # eminence of 28.2 - with no escalation of any kind beforehand, and
        # nothing in the log ever mentioning it. Their words: "no escalation on
        # the stat that ends the run". It is the one hazard that cannot be
        # bribed away and the one the player was never told was closing in.
        _danger = self.cfg["eminence_danger"]
        if self.eminence > _danger * 0.75:
            _said = getattr(self, "_said_eminence", -999)
            _band = int(self.eminence / max(1.0, _danger * 0.15))
            if _band > _said:
                self._said_eminence = _band
                self.log.append((yr, "YOU ARE BECOMING CONSPICUOUS: eminence %.0f "
                                     "against a danger line of %.0f. This is the "
                                     "one thing no patron and no bribe protects "
                                     "you from, and it grows with reputation and "
                                     "visible wealth. A wide, dispersed "
                                     "institution is what survives you"
                                 % (self.eminence, _danger)))
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
        # WARN, THE WAY EMINENCE DOES. Denunciation ends the run outright and
        # said nothing at all first: a break tester read "RUN ENDS: denounced:
        # as a sorcerer" after eleven quiet years, with `state` showing
        # "scandal 33.55" and no threshold, no probability and no note - on the
        # same screen where eminence carefully explains that it is "dangerous
        # above 26 ... 0% chance the run ENDS this year". Two hazards of the
        # same shape, one of them legible.
        _sd = c["suspicion_danger"]
        if self.scandal > _sd * 0.75:
            _band = int(self.scandal / max(1.0, _sd * 0.15))
            if _band > int(getattr(self, "_said_scandal", 0)):
                self._said_scandal = _band
                self.log.append((yr, "YOU ARE BEING TALKED ABOUT: scandal %.0f "
                                     "against a line of %.0f. Past it you may be "
                                     "denounced, and that ends the run - about "
                                     "%.0f%% a year at this level. 'bribe' buys "
                                     "advocacy and piety; it falls a tenth a "
                                     "year on its own"
                                 % (self.scandal, _sd,
                                    100.0 * max(0.0, (self.scandal - _sd) / 60.0))))
        elif self.scandal < _sd * 0.5:
            self._said_scandal = 0
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
                            self._done_changed()
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
            if self.running("sanitation_antisepsis"):
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
                        self.operating.discard(k)
                        self.done.discard(k)
                        self._done_changed()
            if self.stalled >= 12:
                self._catastrophe("the founder died without training successors; "
                                  "the school dispersed and the work was forgotten")
        else:
            self.stalled = 0

        # 8. random events
        if self.events and not self.dead_reason:
            self._random_events(yr)

        self.year += 1

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
