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
        self.state_capacity = float(self.civ.get("state_capacity", 0.7))
        self.pop_scale = max(0.05, float(self.civ.get("population", 65e6)) / 65e6)
        self.year = self.cfg["start_year"]
        c = self.cfg
        self.capital = float(c["start_capital"])
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
        # Open what plainly pays for itself, before the books are struck: a
        # concern you opened this year is a concern that earns this year.
        if self.policy.get("auto_open", not self.manual):
            self.auto_open_ventures()
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
                        self.operating.discard(k)
                        self.done.discard(k)
                        self._done_changed()
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
                    else:
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
                    hh *= worst
                    give_back = min(spent_hours - refunded, per * 0.4 * (1.0 - worst))
                    st["ph_left"] += max(0.0, give_back)
                    refunded += max(0.0, give_back)
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
