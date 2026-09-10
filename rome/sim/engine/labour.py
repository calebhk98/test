"""People: hiring them, teaching them, buying them, paying them.

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


class LabourMixin:
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

    # ---- literacy bounds who you can hire ----------------------------------
    # FINDINGS_ROUND2 section Q: every civ file carries literacy_general and
    # literacy_elite, apply_tech_effects (society.py) raises them when paper,
    # printing, schools and libraries are built, and until now nothing else in
    # the engine ever read either number. A scribe cost the same to hire in a
    # society where two people in a hundred could read as in one where nine
    # could.
    #
    # `scholar` is drawn from the lettered, propertied class - literacy_elite
    # in the civ file, "fraction of the propertied class that can read". The
    # rest - `scribe`, and the trades taught into being from ordinary
    # craftsmen (`engineer`, `chemist`, `machinist`, `optician`) - draw on the
    # wider literacy_general pool of anyone who can read at all. `merchant` is
    # left out on purpose: an agent working on commission is not, in this
    # period, chiefly a reader.
    LITERATE_TRADES = frozenset({"scholar", "scribe", "engineer", "chemist",
                                 "machinist", "optician"})
    # The literacy this file's trade shares and staff ceilings were already
    # tuned against, before literacy was read anywhere: Rome's own numbers
    # (rome_100ad.json), because every other constant in this economy - price
    # index, cost multipliers - is already calibrated relative to Rome. Below
    # its own reference literacy stays 1.0 and NOTHING changes for Rome; a
    # civilization with less of either number gets a genuinely smaller pool,
    # in proportion, and a civilization with more (Han's elite literacy, 0.95
    # against Rome's 0.9) is not penalised for having read more than Rome did.
    LITERACY_REFERENCE_GENERAL = 0.12   # rome_100ad.json literacy_general
    LITERACY_REFERENCE_ELITE = 0.90     # rome_100ad.json literacy_elite

    def literacy_factor(self, trade):
        """0..1: how much of this trade's usual pool this society's literacy
        can actually fill. 1.0 for anything that is not a literate trade."""
        if trade not in self.LITERATE_TRADES:
            return 1.0
        if trade == "scholar":
            lit, ref = self.civ.get("literacy_elite", 0.0), self.LITERACY_REFERENCE_ELITE
        else:
            lit, ref = self.civ.get("literacy_general", 0.0), self.LITERACY_REFERENCE_GENERAL
        return max(0.0, min(1.0, float(lit) / ref))

    def literate_capacity(self, trade):
        """The most people this society's literacy will EVER let you have in
        this trade, hired and taught combined - a headcount ceiling, not an
        hours one.

        `hire`'s own affordability and supervision checks say nothing about
        whether anyone who can read is available at any price; this is the
        actual wall. Read as people rather than hours, it is the same
        abstracted labour-market scale market_supply() already uses for the
        share a scholar-family trade gets (25,000 hours at full population
        scale, of which a lettered trade gets 35% before literacy narrows it
        further) - not a second population model that has to be kept in step
        with the first, but that one.
        """
        if trade not in self.LITERATE_TRADES:
            return float("inf")
        base = self.cfg["hired_hours_cap_base"] * (0.25 + 0.75 * min(1.0, self.pop_scale))
        people = base * 0.35 / self.HOURS_PER_PERSON_YEAR
        # A FLOOR OF TWO, because the unfloored number said something false.
        # Norse elite literacy is a sixth of Rome's, which took this ceiling to
        # 0.2 people: not "scarce" but "there is no such person in Scandinavia,
        # at any price, ever". That is wrong about the period. Viking-age
        # Scandinavia had runic literacy, rune-carvers who cut inscriptions for
        # hire, merchants who kept reckonings, and from the tenth century
        # priests who read Latin. What it did not have was a POOL - a body of
        # lettered men large enough to staff an institution.
        #
        # So literacy bounds the SCALE of what you can build and not whether a
        # single literate person can be found.
        #
        # ADDED, not a maximum. My first attempt floored this with max(), which
        # fixed the falsehood and broke the mechanism: the floor was larger than
        # anything Norse literacy could reach, so teaching the society to read
        # changed the ceiling not at all, for the one civilisation the mechanism
        # exists to matter for. A floor that swallows the signal is worse than
        # no floor. The rune-carver and the priest are always findable; the POOL
        # on top of them is what literacy buys, and it is what teaching moves.
        return 1.5 + people * self.literacy_factor(trade)

    def _trade_headcount_pending(self, trade):
        """People already on the books in this trade, plus people already
        being taught into it who are not ready yet - what a fresh hire or a
        fresh training run would be added ON TOP OF."""
        pending = sum(row[3] for row in self.training
                      if len(row) > 2 and row[2] == trade)
        return self.employees.get(trade, 0.0) + pending

    # ---- the market responds to demand, and to supply ----------------------
    # FINDINGS_ROUND2 section R: market_pressure already does this for slaves
    # - buying in bulk bids the price up, it remembers between purchases, and
    # it decays - and nothing else in the economy had an equivalent. This is
    # the labour half: the same saturating idea, extended honestly rather than
    # copied, and self-contained (decayed on READ rather than decremented once
    # a year in step(), which lives in core.py, so nothing outside this file
    # has to know this exists). 0.6x a year, the same rate market_pressure
    # decays at (0.55, near enough) - mostly gone in three years.
    def labour_pressure(self, trade):
        rec = getattr(self, "_labour_pressure", None)
        rec = rec.get(trade) if rec else None
        if not rec:
            return 0.0
        hours, yr = rec
        age = max(0.0, self.year - yr)
        return hours * (0.6 ** age)

    def _add_labour_pressure(self, trade, hours):
        d = getattr(self, "_labour_pressure", None)
        if d is None:
            d = self._labour_pressure = {}
        d[trade] = (self.labour_pressure(trade) + max(0.0, hours), self.year)

    def labour_price_factor(self, trade):
        """What hiring, commissioning or keeping MORE of this trade costs
        beyond the wage table, from how hard you have recently leaned on its
        local supply.

        `market_supply(trade)` is the ceiling: everyone this trade could put
        to work here, including everyone you already employ. Recent pressure
        taken as a share of that ceiling is negligible at a fifth of it and
        roughly doubles the price at the whole of it - the same curve
        `material_price_factor` uses for the same reason. Because the ceiling
        itself grows when you teach the trade a bigger workforce, or when an
        institution or literacy widens it, the SAME recent pressure buys a
        smaller premium once the supply behind it is bigger: teaching fifty
        machinists is what makes hiring the fifty-first one cheap again, not
        merely possible.
        """
        supply = max(1.0, self.market_supply(trade))
        share = min(1.5, self.labour_pressure(trade) / supply)
        return 1.0 + 0.9 * share * share

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
        # LITERACY BOUNDS THE SCHOLAR CEILING. A school, an academy or an
        # imperial patron can only produce as many scholars as this society
        # has literate, propertied people to draw them from (literacy_factor
        # reads literacy_elite for "scholar"; see FINDINGS_ROUND2 section Q).
        # Below Rome's own literacy_elite (0.9, the number every one of the
        # figures above was already tuned against) this narrows the pool;
        # printing, schools and libraries raise literacy_elite
        # (apply_tech_effects, society.py) and widen it again as a run goes
        # on, which is the entire point of building them.
        sc *= self.literacy_factor("scholar")
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
            here = sorted(t for t in WAGES if self.trade_available(t))
            return 0.0, ("no such trade. you could work as: " + ", ".join(here))
        # A TRADE NOBODY HERE PRACTISES IS A TRADE NOBODY HERE WILL PAY YOU FOR.
        # A break tester earned wages as a chemist, an electrician and an
        # engineer in 1500 Tenochtitlan, in the same session where `hire` had
        # just refused all three ("there are no chemists to hire in this society
        # at any price") and `labour` listed them under do_not_exist_here. The
        # gate existed; this one command simply never applied it, and its own
        # "no such trade" whitelist named the full civilisation-agnostic roster,
        # which is what told the tester those jobs were available in the first
        # place.
        #
        # The founder really does know chemistry - that is the premise. What he
        # does not have is a customer. Wage labour is somebody else deciding
        # your work is worth money, and there is nobody here to decide that
        # until you have taught the trade, at which point trade_available()
        # turns true and this opens by itself.
        if not self.trade_available(trade):
            return 0.0, ("nobody here will pay you to be a %s: the trade does "
                         "not exist in this society, so there is no employer "
                         "for it. Teach it first with train, or work at "
                         "something they do recognise." % trade)
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

    def wage_bill(self):
        """What your standing staff costs you every year, by trade.

        A machinist is not paid a labourer's wage and cannot be had at one. This
        is the other half of differentiating the trades: the expensive trades are
        expensive to keep, so a large staff of the people you actually need is a
        real commitment rather than a number that drifts upward on its own.

        Recently having leaned hard on a trade's local supply (labour_price_factor)
        shows up here too, not only in the fee `hire` charged to bring someone
        on: a town that just watched you take on half its smiths pays every
        smith more for a few years, yours included, until the pressure decays
        or the supply of smiths genuinely grows.
        """
        total = 0.0
        for t, n in self.employees.items():
            total += n * ANNUAL_WAGE.get(t, 375.0) * self.wage_index * self.labour_price_factor(t)
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
        # A trade that needs reading cannot be bought past how many people
        # here can read (FINDINGS_ROUND2 section Q). scholar and scribe are
        # the only literate trades that reach this branch - the taught ones
        # (engineer, chemist, machinist, optician) are all in TRADES_ABSENT
        # and returned above, bounded instead by literate_capacity() in
        # train().
        if t in self.LITERATE_TRADES:
            cap *= self.literacy_factor(t)
        return cap + self.employees.get(t, 0.0) * self.HOURS_PER_PERSON_YEAR

    def hire(self, trade, n):
        """Take someone onto the staff permanently. They are paid every year."""
        trade = str(trade or "").strip().lower()
        if trade not in WAGES:
            return False, ("no such trade: %s. Trades: %s"
                           % (trade, ", ".join(sorted(WAGES))))
        if isinstance(n, str) or isinstance(n, bool):
            # `buy` and `start` both type-check and `hire` did not, so "5"
            # walked straight in where 5 was meant.
            return False, "n must be a number, not %r" % (n,)
        if n <= 0:
            return False, "n must be greater than zero. Nothing was changed."
        if not self.trade_available(trade):
            return False, ("there are no %ss to hire in this society at any price: %s "
                           'Teach one: {"cmd":"train","trade":"%s","n":1}'
                           % (trade, TRADE_NOTES.get(trade, ""), trade))
        # LITERACY IS A WALL, NOT A COST. Money buys the finder's fee below;
        # it cannot buy people who do not exist. See FINDINGS_ROUND2 section
        # Q and literate_capacity()'s docstring.
        if trade in self.LITERATE_TRADES:
            cap = self.literate_capacity(trade)
            have = self._trade_headcount_pending(trade)
            if have + n > cap + 1e-6:
                return False, ("this society's literacy will not supply more than "
                               "%.1f %ss in total, ever, at any price; you already have "
                               "%.1f (hired and still being taught). Raise "
                               "literacy_general or literacy_elite -- printing, schools "
                               "and libraries do -- to widen this pool."
                               % (cap, trade, have))
        # A finder's fee and the first year in advance, which is what a household
        # actually pays to take a skilled man off someone else's bench. Buying
        # deep into a trade's LOCAL supply bids its price up, the same
        # principle market_pressure already applies to slaves (see
        # labour_price_factor for why it is not a one-way ratchet: teaching
        # or hiring your way to a bigger supply of the trade brings the price
        # back down).
        fee = (n * ANNUAL_WAGE.get(trade, 375.0) * self.wage_index * self.price_index
              * self.labour_price_factor(trade))
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
        self._add_labour_pressure(trade, float(n) * self.HOURS_PER_PERSON_YEAR)
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
        # LITERACY BOUNDS TEACHING TOO, and this is where it bites hardest:
        # engineer, chemist, machinist and optician can ONLY be had this way
        # (trade_available refuses to hire them at all), so without this check
        # a founder with enough director-hours and money could teach an
        # unlimited technical staff into a society two per cent of whose
        # people can read. Money and hours are necessary; they were never
        # supposed to be sufficient. See FINDINGS_ROUND2 section Q.
        if trade in self.LITERATE_TRADES:
            cap = self.literate_capacity(trade)
            have = self._trade_headcount_pending(trade)
            if have + n > cap + 1e-6:
                return False, ("this society's literacy will not supply more than "
                               "%.1f %ss in total, ever, at any price; you already have "
                               "%.1f (hired and still being taught). Raise "
                               "literacy_general or literacy_elite -- printing, schools "
                               "and libraries do -- to widen this pool."
                               % (cap, trade, have))
        hours = 450.0 * n            # your hours, teaching, per person
        pool = self.director_pool() - self.director_hours_committed()
        if hours > pool:
            return False, ("teaching %g %ss takes %.0f of your own hours and you have "
                           "%.0f uncommitted this year" % (n, trade, hours, max(0.0, pool)))
        # Teaching pulls the SOURCE trade's people off their own bench for the
        # duration, which is exactly what market_pressure prices for buying
        # slaves and labour_price_factor now prices for hiring: the more of
        # `frm` you have already pulled recently, the dearer feeding the next
        # batch while they learn.
        fee = (n * ANNUAL_WAGE.get(frm, 375.0) * 1.2 * self.wage_index * self.price_index
              * self.labour_price_factor(frm))
        if fee > self.capital + self.credit_limit() * 0.5:
            return False, ("you must keep them fed while they learn: %.0f denarii, "
                           "and you have %.0f" % (fee, self.capital))
        self.capital -= fee
        self.teaching_hours_this_year = getattr(self, "teaching_hours_this_year", 0.0) + hours
        self.trades_created.add(trade)
        self.training.append([0.0, self.year + 2.0, trade, float(n)])
        self._add_labour_pressure(frm, float(n) * self.HOURS_PER_PERSON_YEAR)
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
        # A shop charges more for a one-off than it pays its own man for a
        # year, and more again if you are buying deep into what the local
        # market can spare this year (see labour_price_factor).
        fee = (hours * WAGES[trade] * 1.6 * self.wage_index * self.price_index
              * self.labour_price_factor(trade))
        if fee > self.capital + self.credit_limit() * 0.5:
            return False, ("%.0f hours of a %s costs %.0f denarii and you have %.0f"
                           % (hours, trade, fee, self.capital))
        self.capital -= fee
        self.contract_hours[trade] = self.contract_hours.get(trade, 0.0) + hours
        self.commissioned[trade] = self.commissioned.get(trade, 0.0) + hours
        self._add_labour_pressure(trade, hours)
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
