"""What a society believes, fears, and does to you for being large.

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


class SocietyMixin:
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
        # A recognised scholar doing something strange is a scholar; a stranger
        # doing the same thing is a sorcerer. This is the persona working, and
        # it is what the node has always said it does.
        if self.running("identity_cover"):
            a *= 0.75
        return a

    def military_leverage(self):
        """How much of the military branch this founder can put in a patron's
        hands: the count that "if I woke up in Rome and made cannon" is
        actually asking about.

        Measured against a founder with none of the 111+ military, weapon and
        fortification nodes, the ONLY effect any of them had anywhere in the
        engine was `weapon_democratising` raising suspicion (see alarm_of) -
        arming a state you already live in was a pure liability. This is the
        other half: a founder who hands a patron the flintlock or the bastion
        fort is worth more to him, which is what update_protection() and
        hazard_relief("output_factor") below both spend it on.

        Sqrt-scaled and capped at 1.0, the same shape standing_floor() uses
        for earned work: the FIRST working gun matters enormously to a patron
        shopping for an edge over his rivals, the fortieth barely adds
        anything he does not already have. Counts DONE, not merely operating
        - see `has` vs `running` in projects.py - because a fortification
        design or a powder formula is something a patron's arsenal keeps
        knowing whether or not you personally still run a workshop on it.
        Reaches 1.0 at 25 nodes, a little over a fifth of the tree's military
        branch, so this cannot be maxed by a token gesture, and cannot be
        maxed by "build everything military" either - both would make the
        branch a strategy unto itself, which the other ~2,700 nodes on the
        way to a transistor should not have to compete with.
        """
        n = sum(1 for k in self.done if "military" in self.nodes[k].get("traits", ()))
        if n <= 0:
            return 0.0
        return min(1.0, math.sqrt(n / 25.0))

    def update_protection(self):
        """Standing, office and MONEY all protect. The old model had money only
        endangering you, which is backwards: wealth buys advocates, priesthoods,
        magistracies and, in a society with a bribability of 0.55, verdicts."""
        p = 0.0
        w = self.w
        if self.running("patron_local"):        p += 0.18 * w["patronage_weight"]
        if self.running("patron_senatorial"):   p += 0.26 * w["patronage_weight"]
        if self.running("patron_imperial"):     p += 0.32 * w["patronage_weight"]
        # AN ARMOURER IS PROTECTED DIFFERENTLY FROM A PHILOSOPHER, AND ONLY
        # WHEN SOMEBODY WANTS WHAT HE MAKES. Sejanus's people were safe until
        # they no longer had anything Tiberius needed, and the same logic
        # runs the other way: a patron who can call on your powder mill or
        # your bastion design has a reason to keep you out of court that
        # identity_cover and citizenship do not supply on their own. Gated on
        # having a patron at all - knowing how to cast a cannon with nobody
        # to sell it to is not leverage, it is just a dangerous thing to be
        # caught doing, which is exactly what alarm_of's weapon_democratising
        # term already charges you for and this does NOT cancel.
        if (self.running("patron_local") or self.running("patron_senatorial")
                or self.running("patron_imperial")):
            p += 0.09 * w["patronage_weight"] * self.military_leverage()
        # IT SAYS "REDUCES ALL FUTURE SUSPICION" AND IT DID NOTHING OF THE KIND.
        # identity_cover's entire implementation was +1.0 to the reputation
        # floor and +400 to the credit limit, and the suspicion it promised to
        # reduce was a field that no longer exists. Its real value was that it
        # gated a quarter of the tree - which is why every tester concluded
        # they had to have it and assumed it was about illegal activity. It is
        # a persona: books, a house, clothes, a secretary and a reputation for
        # piety. What that buys is that an inexplicable effect coming out of
        # YOUR workshop is read as learning rather than as sorcery.
        if self.running("identity_cover"):      p += 0.12
        if self.has("citizenship"):         p += 0.10
        if self.running("collegium_licensed"):  p += 0.10
        if self.running("endowment_land"):      p += 0.08   # conspicuous benefaction
        if self.running("fin_university") or self.running("school_founded"): p += 0.06
        p += min(0.30, self.reputation / 260.0)
        # BRIBERY, ADVOCACY AND PIETY: an explicit, spendable defence.
        income = max(1.0, self.revenue())
        p += min(0.30, (self.bribes_ytd / (income * 0.6)) * w["bribability"])
        self.protection = min(0.92, p)

    WITHDRAW_EVERY = 12          # years; being seen to retire twice is not retiring

    def withdraw_from_public_life(self):
        """Deliberately become a smaller man. The one lever against prominence.

        Both play testers of round eight died to eminence and both said the
        same thing about it: `help eminence` says "nothing lowers it directly,
        which is the point", the two counters named are ten-year builds behind
        long chains, and the steady state the game prints is above the danger
        line - so playing well is a death sentence and no command reads as
        "get smaller". That is a mechanic with no decision in it.

        This is the decision. It is what the men this hazard is modelled on
        actually did, and what the game's own confiscation event already
        describes ("you withdraw from public life for a while"): stop
        appearing, stop publishing under your own name, let somebody else take
        the credit. The price is reputation, which in this model is not
        cosmetic - it sets your credit limit, your protection, what wages you
        must pay, how fast the market supplies you and the calendar floor on
        every project. You cannot get small and stay grand.

        What you BUILT you keep: the floor under reputation is exactly the work
        that stands, so this takes away the novelty and leaves the corpus.
        """
        if not self.founder_alive:
            return False, "there is nobody left to withdraw"
        last = getattr(self, "last_withdrawal", -999)
        if self.year - last < self.WITHDRAW_EVERY:
            return False, ("you stepped back in %d; doing it again so soon is "
                           "not retirement, it is a performance, and nobody "
                           "would believe it. You could again in %d"
                           % (last, last + self.WITHDRAW_EVERY))
        floor = self.standing_floor()
        # DO NOT LET THEM PAY FOR NOTHING. Same rule as `bribe`: work out
        # whether it would buy anything before taking anything. At an eminence
        # nobody has noticed, retiring is not modesty, it is throwing away the
        # standing that gets your work funded and staffed.
        danger = self.cfg["eminence_danger"]
        if self.eminence < danger * 0.5:
            return False, ("nobody is watching you closely enough for this to "
                           "buy anything: prominence is %.1f against a danger "
                           "line of %.0f. Withdrawing now would only cost you "
                           "the standing that gets your work funded. Nothing "
                           "was changed." % (self.eminence, danger))
        if self.reputation <= floor + 0.5:
            return False, ("you are already as obscure as a man who has built "
                           "what you have built can be. What is left of your "
                           "standing is the work itself, and that does not go "
                           "away. Nothing was changed.")
        self.last_withdrawal = self.year
        rep_before, em_before = self.reputation, self.eminence
        # Halfway to the floor, not to zero: the work stands.
        self.reputation = floor + (self.reputation - floor) * 0.5
        self.eminence *= 0.5
        self.update_protection()
        msg = ("you withdraw from public life: reputation %.1f -> %.1f, "
               "eminence %.1f -> %.1f. What you built still stands, and that "
               "is the floor under your standing (%.1f). It costs you credit, "
               "protection and cheap labour until it grows back."
               % (rep_before, self.reputation, em_before, self.eminence, floor))
        self.log.append((self.year, msg))
        return True, msg

    def eminence_report(self):
        """Where you stand against the one danger no patron can protect you from."""
        c = self.cfg
        danger = c["eminence_danger"]
        yearly = self.prominence_hazard()
        # eminence decays 0.93 a year and gains `yearly`, so this is where it
        # settles if nothing changes.
        settles = yearly / 0.07
        p = max(0.0, (self.eminence - danger) / 90.0)
        helps = []
        if not self.running("academy_network"):
            helps.append("a wide, dispersed institution is harder to destroy than "
                         "one great man")
        if self.running("patron_imperial"):
            helps.append("you are as close to the throne as it is possible to "
                         "stand, which is the most exposed place there is")
        if self.capital > 250000:
            helps.append("visible wealth is half of what makes you a target")
        # THE LEVER, NAMED. Two play testers read this screen, found no command
        # in it that meant "get smaller", and died. It is `withdraw`.
        _last = getattr(self, "last_withdrawal", None)
        if _last is not None and self.year - _last < self.WITHDRAW_EVERY:
            _w = ("you stepped back in %d; again no sooner than %d"
                  % (_last, _last + self.WITHDRAW_EVERY))
        else:
            _w = ("'withdraw' halves this now and gives up half the reputation "
                  "you hold above what your work alone is worth (%.1f). That is "
                  "a real price - reputation is your credit, your protection, "
                  "your wages and the pace of your projects - and it is the only "
                  "thing that lowers prominence the year you do it."
                  % self.standing_floor())
        return {"now": round(self.eminence, 2),
                "dangerous_above": danger,
                "settles_at_if_nothing_changes": round(settles, 1),
                "chance_of_ruin_this_year": round(p, 4),
                # WHICH OUTCOME. A play tester survived two confiscations and
                # was then ended by a third roll, with "7% chance of ruin this
                # year" shown before all three, and had no way to know the rolls
                # differed. They do: 45% a confiscation, 35% a patron lost, 20%
                # the end. Reading "chance of ruin" as "chance of death" was the
                # game's fault, not theirs.
                "if_it_lands_it_is": {
                    "property confiscated and a forced retirement": 0.45,
                    "your patron destroyed in someone else's quarrel": 0.35,
                    "the end of the run": 0.20},
                "chance_the_run_ENDS_this_year": round(p * 0.20, 4),
                "the_one_lever": _w,
                "what_would_change_it": helps,
                "note": "This is prominence, not scandal. It cannot be bribed "
                        "away, and every defence that makes you safer from "
                        "accusation makes you larger and so raises this."}

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
        if self.running("patron_imperial"):
            h *= 1.5          # nearest the throne, most exposed to its turnover
        # A wide, dispersed institution is harder to destroy than one great man.
        if self.running("academy_network"):
            h *= 0.65
        # AND A CITY GETS USED TO YOU. familiarity is the model's own measure of
        # how unsurprising you have become - it already decays the alarm your
        # work causes - and it was the one defence prominence ignored. Two play
        # testers read "EMINENCE is dangerous above 26 (settles near 39.2)" and
        # correctly described it as the game announcing that a successful run is
        # scheduled to die. A man who has been the great man of the city for
        # ninety years is a fixture, not a novelty; he is still exposed, and he
        # is not what he was in his first decade.
        #
        # A SIXTH OFF, NOT A THIRD. The first attempt at this took a third, and
        # a break tester then measured three thousand run-years in which the
        # sum of every reported chance of ruin was exactly 0.00 - a mechanic
        # that cannot reach you is not a hazard, it is scenery, and the
        # correction had gone as far past the line as the original sat the
        # other side of it. At a sixth, a man who has been the city's fixture
        # for ninety years settles just under the danger line and a man who has
        # also got himself next to the throne settles well over it, which is
        # the shape the whole mechanic is about.
        h *= (1.0 - 0.15 * self.familiarity)
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

    # A lower death rate shows up in the census a generation later, not the
    # year the node completes, so a "population" tech effect is spread over
    # this many years rather than dumped on the first one. Forty years is
    # two adult generations, which is about how long it takes a mortality
    # improvement to finish working its way through age structure into a
    # visibly larger population, and it is short enough that a civilization
    # which never stops building these nodes still cannot make the ramp
    # itself the fast part of the cascade.
    POP_TECH_RAMP_YEARS = 40

    def apply_tech_effects(self, k):
        """Building something changes what this society is like.

        This is what applies _TECH_EFFECTS.json, and it is called from
        _complete(). Printing raises literacy; the scientific method reduces the
        fear of the inexplicable. The whole argument for teaching and printing
        early is that they change people, and this is where that happens.

        It was once true that the effects table was written, committed with a
        description of what it would do, and never referenced by any code. That
        was fixed, and this comment then described the fix in the past tense
        badly enough that an agent reading the file reported the dead mechanic
        as a live finding. A comment that states a bug without stating plainly
        that it is fixed will be read as current, because that is the only
        sensible way to read it.
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
            elif field == "population":
                # SANITATION, ANTISEPSIS, BETTER FOOD AND THE LIKE RAISE THE
                # POPULATION, AND THAT FEEDS BACK: more people is a bigger
                # labour market and a bigger ceiling on trade (see pop_scale
                # in economy.py, labour.py and geography.py). Unlike every
                # other field above, this does NOT land in one year - a
                # lower death rate shows up in the headcount a generation
                # later, not the day a latrine opens - so it is queued here
                # and spread over RAMP_YEARS by _demographic_recovery() in
                # core.py, the same file that drives the mortality side of
                # this same cascade. `delta` is this technology's total,
                # eventual addition to this civilization's baseline
                # population, as a fraction of it.
                self._pop_tech_pending.append(
                    (delta / self.POP_TECH_RAMP_YEARS, self.POP_TECH_RAMP_YEARS))
                changed.append(field)
        if changed:
            self.log.append((self.year, "%s changes the society: %s"
                             % (self.nodes[k]["name"], ", ".join(sorted(changed)))))

    # ---- EDUCATING A WHOLE SOCIETY, NOT JUST A HOUSEHOLD -------------------
    # "Can we make the whole country's literacy rates improve? What if we
    # make 5,000 schools and tractors and food production... can I create a
    # 90%+ literate population?" Before this, literacy_general/literacy_elite
    # moved only through the fixed, one-off deltas in _TECH_EFFECTS.json,
    # applied once, the year a technology like printing_press or
    # school_founded first completes (see apply_tech_effects above). Founding
    # a hundred schools did nothing that founding one did not: nothing else
    # in the engine ever read institution_units("school_founded") against
    # literacy. This section is the missing half - a school or an academy
    # that is actually OPEN teaches the society a little more every year it
    # stays open, not only on the day its doors first unlocked - bounded by
    # the user's own, historically correct caveat: a farming family that
    # cannot spare a child from the harvest will not send that child to a
    # classroom however many classrooms you build, so the CEILING literacy
    # can approach is itself a function of how much of the countryside's
    # labour has been freed by mechanised agriculture, and only the RATE of
    # approach to that ceiling is a function of how much schooling is
    # running.
    AGRI_MECHANISATION_CATS = frozenset(
        {"agriculture", "field_machinery", "crops", "soil"})

    def _is_agri_mechanisation(self, k):
        """Is `k` one of the technologies that lets a farm feed the same
        number of mouths with fewer hands - the thing that frees a child
        for a classroom instead of the harvest?

        Reads the tree's own `cat` and `traits`, the same fixed, structural
        tree data civ_cost_factor already keys off, rather than a second,
        hand-maintained list that could drift out of step with which nodes
        the tree actually has. THE TREE ALREADY NAMES THIS: `labour_saving`
        is a trait, and the first version of this function matched on `food`
        alone, which is also carried by tea, coffee and sugar imports, jam
        and cheese making and a dozen other nodes that make farming more
        PROFITABLE without freeing a single pair of hands from it - 136
        nodes matched, most of them tier 0-1, so a household could reach
        full mechanisation before touching anything resembling a reaper.
        Requiring `labour_saving` as well narrows this to the 40 nodes that
        are actually about doing the same farm work with fewer people: the
        chaff cutter and the harrow at the cheap end, the reaper, the
        threshing machine and tile drainage in the middle, the steam
        tractor and the combine harvester at the top. tl_tractor is
        checked by id on its own because the tree files it under the
        generic `vehicle_types` category with every other wheeled thing
        rather than with the rest of agriculture, and a tractor is exactly
        what the user asked for by name.
        """
        n = self.nodes.get(k)
        if not n:
            return False
        if k == "tl_tractor":
            return True
        if "labour_saving" not in (n.get("traits") or ()):
            return False
        return n.get("cat") in self.AGRI_MECHANISATION_CATS or "food" in n["traits"]

    # Reaches full effect at 18 of the 40 matching nodes done (see
    # _is_agri_mechanisation): a little under half, "substantially
    # mechanised farming", not "literally every one of them".
    AGRI_MECHANISATION_SATURATES_AT = 18.0

    def agrarian_slack(self):
        """0..1: how much of the countryside's labour mechanised farming has
        freed, which is the hard limit on how many children a family can
        spare for a school instead of the fields.

        This is the user's own instinct, already half-stated in
        institution_unit_ceiling's own comment (projects.py) before this
        function existed: "a lot of rural people without good farming don't
        really want their kids to go to school, they want them working for
        food or money." Nothing in this engine keeps a literal tonne of
        grain, so this counts what the tree actually offers instead - the
        reaper, the threshing machine, the seed drill, the tractor, better
        rotations and fertiliser - the same shape military_leverage() already
        uses for "how much of one branch of the tree have you actually
        built": a plain count of matching DONE nodes (order cannot change a
        sum of ones, so this needs no sorted() the way a weighted sum would,
        see military_leverage's own unsorted count for the same reasoning),
        square-rooted so the fifth mechanised technique matters far more than
        the fifteenth, and capped at 1.0 so this can never be a lever on its
        own - only a MULTIPLIER on what schooling is allowed to do, below.

        CALLED EVERY YEAR SCHOOLING IS RUNNING, not once at completion like
        apply_tech_effects - _advance_literacy reads the CEILING every year,
        which reads this. Scanning self.done (up to 2,833 entries, and only
        ever growing over the course of a long run) for a 40-node match every
        single year of a 700-year run is the wrong direction: only 40 ids can
        ever match at all (see _is_agri_mechanisation), fixed the moment the
        tree loads, so this walks THAT list once, cached forever the same way
        _is_foreign_institution caches (below) - nothing that changes after
        construction - and does one `in self.done` set lookup per id, however
        large self.done has grown.
        """
        ids = self.__dict__.get("_agri_mechanisation_ids")
        if ids is None:
            ids = self._agri_mechanisation_ids = tuple(
                sorted(k for k in self.nodes if self._is_agri_mechanisation(k)))
        n = sum(1 for k in ids if k in self.done)
        if n <= 0:
            return 0.0
        return min(1.0, math.sqrt(n / self.AGRI_MECHANISATION_SATURATES_AT))

    # What a pre-industrial society can reach on schooling and urban/clerical
    # literacy alone, with farming still entirely by hand: a merchant class,
    # a priesthood, a bureaucracy and their households, well above Rome's
    # bare 12% general literacy and well short of a modern figure. Kept
    # deliberately conservative rather than citing a campaign like Sweden's
    # that reached near-universal reading through the church rather than
    # freed farm labour, because this model has no lever for that route and
    # a number this file cannot actually justify with a mechanism is not one
    # it should claim.
    LITERACY_ROOM_WITHOUT_MECHANISATION = 0.35

    def literacy_ceiling_general(self):
        """The most of the general population schooling could ever make
        literate here, RIGHT NOW - not a fixed number, because
        agrarian_slack() moves it as the countryside mechanises.

        This is the answer to "can I create a 90%+ literate population": at
        the limit, full mechanisation (agrarian_slack() == 1.0) puts the
        ceiling at 0.35 + 0.55 == 0.90, and it costs exactly what the user's
        own caveat says it costs - schools AND the agricultural machinery
        that frees the children who would otherwise be working the harvest.
        Never above 0.90: a hard 10% of any pre-transistor-era population -
        the very young, the infirm, the itinerant - is not a schooling
        question at all.
        """
        room = self.LITERACY_ROOM_WITHOUT_MECHANISATION
        return min(0.90, room + 0.55 * self.agrarian_slack())

    # The propertied and lettered class literacy_elite measures was never
    # the class tied to the fields, so its ceiling does not read
    # agrarian_slack() at all: an academy can teach every noble and priest's
    # child a society has whether or not a single field has been mechanised.
    # Left short of 1.0 for the same reason literacy_ceiling_general is: some
    # fraction of any class is never going to be readers.
    LITERACY_CEILING_ELITE = 0.97

    def literacy_ceiling_elite(self):
        return self.LITERACY_CEILING_ELITE

    def _schooling_flow(self):
        """0 if no school is open here at all; otherwise a small positive
        number that grows, with diminishing returns, in how much school and
        academy capacity is actually running.

        Square-rooted in institution_units for the same reason every other
        institution-driven pool in this engine is (see staff_capacity and
        hired_cap, labour.py, and institution_unit_ceiling, projects.py): a
        second school teaches nearly as many more people as the first one
        did; a ninth does not teach nine times as many. This is 0.0, and
        every function below that reads it does nothing, for the run that
        never builds a school at all - which is deliberate: literacy in this
        model is something a society is TAUGHT into, not something that
        drifts upward for free while nobody is teaching anybody.
        """
        if not self.running("school_founded"):
            return 0.0
        flow = self.institution_units("school_founded") ** 0.5
        if self.running("academy_network"):
            flow += 1.5 * self.institution_units("academy_network") ** 0.5
        return flow

    # HOW FAST LITERACY CLOSES THE GAP TO ITS CEILING, per unit of
    # _schooling_flow, per year. At flow 1.0 (a single ordinary school and
    # nothing more) the general-literacy gap closes with a time constant of
    # about 1/(0.006*1) ~= 167 years - a run has to want this for the long
    # haul, across several generations, exactly the caution the brief asked
    # for. At flow ~7 (several schools and academies both expanded - the
    # "8.85 units" scale labour.py's own comments record a break tester
    # actually reaching) the time constant falls to about 24 years, so heavy,
    # deliberate investment can visibly transform a society within one or two
    # long lifetimes, which is the other half of what the user asked for:
    # yes, 90%+ is reachable, and it costs generations of sustained schooling
    # and mechanisation, not five turns of building schools.
    LITERACY_GROWTH_RATE_GENERAL = 0.006
    # Faster than the general rate: the propertied class an academy draws on
    # is a far smaller pool to reach than "the whole countryside", so the
    # same institutional effort closes its gap faster. Chosen so Rome's own
    # 0.90 starting elite literacy, already close to its 0.97 ceiling, moves
    # only slightly over a run even under heavy investment - this lever is
    # for the civilisations that start far below it, Norse and Mexica among
    # them, not a way to squeeze Rome's last few points out faster.
    LITERACY_GROWTH_RATE_ELITE = 0.010

    def _advance_literacy(self, yr):
        """Once a year: let running schools and academies close part of the
        gap between this society's literacy and what it could now reach.

        Logistic-shaped on purpose (the increment shrinks as the gap does,
        the same shape prominence_hazard's `settles_at` and staff_capacity's
        `scale` already use for "approaches a limit, never overshoots it"):
        a society does not leap to its ceiling, and it does not overshoot it
        and have to fall back either.
        """
        flow = self._schooling_flow()
        if flow <= 0.0:
            return
        changed = {}
        gen = float(self.civ.get("literacy_general", 0.0))
        gen_ceil = self.literacy_ceiling_general()
        if gen < gen_ceil - 1e-6:
            gen_new = min(gen_ceil, gen + self.LITERACY_GROWTH_RATE_GENERAL
                          * flow * (gen_ceil - gen))
            if gen_new - gen > 1e-6:
                self.civ["literacy_general"] = gen_new
                changed["literacy_general"] = gen_new
        eli = float(self.civ.get("literacy_elite", 0.0))
        eli_ceil = self.literacy_ceiling_elite()
        if eli < eli_ceil - 1e-6:
            eli_new = min(eli_ceil, eli + self.LITERACY_GROWTH_RATE_ELITE
                          * flow * (eli_ceil - eli))
            if eli_new - eli > 1e-6:
                self.civ["literacy_elite"] = eli_new
                changed["literacy_elite"] = eli_new
        if not changed:
            return
        # ONCE A GENERATION, NOT ONCE A YEAR. A gain of a few thousandths a
        # year is real and worth recording, and logging it every single year
        # for a five-hundred-year run would be the same fault the debasement
        # and output_factor hazards were already fixed for elsewhere in this
        # file: a message repeated until it is noise has stopped being a
        # message. Thrown on a fixed 25-year clock (a generation) rather than
        # on a rounded-value change, so it fires on the same schedule whether
        # a run is barely investing or investing heavily.
        last = getattr(self, "_literacy_said", -999)
        if yr - last >= 25:
            self._literacy_said = yr
            bits = []
            if "literacy_general" in changed:
                bits.append("general reading is now %d%% of the population"
                            % round(changed["literacy_general"] * 100))
            if "literacy_elite" in changed:
                bits.append("the lettered and propertied class is now %d%% "
                            "literate" % round(changed["literacy_elite"] * 100))
            self.log.append((yr, "a generation of schooling shows in the "
                             "census: %s" % "; ".join(bits)))

    # ---- A TRADE THE FOUNDER INTRODUCED BECOMES A TRADE THE SOCIETY HAS ----
    # "If I invent electricity, you can't say that after 100 years I still
    # can't find anyone who can make or research generators." TRADES_ABSENT
    # (data.py) names five trades - chemist, electrician, engineer,
    # machinist, optician - that do not exist here until the founder
    # personally teaches the first one (train(), labour.py); trade_available()
    # then reads them as permanently available because self.trades_created
    # never shrinks. What never followed from that is the society producing
    # MORE of them on its own: literate_capacity() bounds how many the
    # founder can hire or teach, and until now nothing but the founder's own
    # director-hours and money ever moved a trade's headcount toward that
    # bound. This is the missing mechanism - once a taught trade has been
    # established long enough, WITH schools actually running, the society
    # naturalises it: it starts producing its own people in that trade, on
    # its own, the same way it always produced its own smiths, bounded by
    # the exact same literate_capacity() wall a founder training them by hand
    # would have been bounded by.
    #
    # No schooling running at all means this never fires, by design: the
    # user's framing is "an EDUCATED society eventually produces its own
    # electricians", not "any society, given centuries, does" - a founder who
    # never builds a school keeps a trade as their own personal secret for
    # as long as the run lasts, which is the honest answer to "after 100
    # years I'm still the only one" when nothing was ever done to change it.
    TRADE_ABSORPTION_BASE_YEARS = 110.0
    # Never faster than one working lifetime, however much is invested: a
    # trade the founder taught last year cannot be "something this society
    # has always had" by definition, whatever the schooling budget is.
    TRADE_ABSORPTION_MIN_YEARS = 35.0

    def _trade_absorption_years(self, flow):
        return max(self.TRADE_ABSORPTION_MIN_YEARS,
                   self.TRADE_ABSORPTION_BASE_YEARS / (1.0 + flow) ** 0.5)

    # Once endemic, the fraction of the remaining gap to literate_capacity()
    # closed each year. A time constant of 1/0.05 == 20 years on top of the
    # 35-110 years it already took to BECOME endemic - so the total span from
    # "the founder teaches the first one" to "the society is producing them
    # near its own natural ceiling" is on the order of a century, generations
    # either way you slice it, which is the pace the brief asked this whole
    # mechanism to run at.
    TRADE_DIFFUSION_APPROACH_RATE = 0.05

    def _advance_trade_absorption(self, yr):
        for t in sorted(TRADES_ABSENT):
            if t not in self.trades_created:
                continue          # never taught here; nothing to naturalise
            intro = self.trade_introduced_year.get(t)
            if intro is None:
                # First year this function has ever seen the trade in
                # trades_created. Recorded now rather than back-dated,
                # because train() (labour.py) does not itself timestamp the
                # set it adds to, and "the year this file first noticed" is
                # at worst one step later than the true year, which cannot
                # matter against a minimum absorption time measured in
                # decades.
                self.trade_introduced_year[t] = yr
                continue
            if t in self.trades_endemic:
                self._grow_endemic_trade(t)
                continue
            flow = self._schooling_flow()
            if flow <= 0.0:
                continue
            if yr - intro >= self._trade_absorption_years(flow):
                self.trades_endemic.add(t)
                # IN-WORLD, NOT A CHANGE-LOG. This narrates a census fact -
                # the trade is no longer one household's secret - the same
                # way every other log line in this file narrates an event
                # the founder would actually observe, never a note about the
                # code that produced it.
                self.log.append((yr, "%s is no longer only your trade: "
                                 "enough schooling has passed through enough "
                                 "hands that this society simply has its own "
                                 "%ss now, the way it always had smiths"
                                 % (t, t)))

    def _grow_endemic_trade(self, t):
        """Let a naturalised trade's own headcount drift toward the same
        ceiling literate_capacity() already enforces on a founder hiring or
        teaching it by hand - so this never hands out a person the rest of
        the engine would have refused the player.

        Continuous, not whole-person rounded: `state`'s own
        "staff_are_fractional_because" text already explains to the player
        that headcount here is a full-time-equivalent that phases in
        smoothly rather than a literal integer count of named people (see
        protocol.py), so this is consistent with a number the player already
        sees fluctuate this way from hiring, training and attrition alike.
        """
        ceiling = self.literate_capacity(t)
        if not (ceiling < float("inf")):
            return
        have = self.employees.get(t, 0.0)
        room = ceiling - have
        if room <= 1e-6:
            return
        self.employees[t] = have + room * self.TRADE_DIFFUSION_APPROACH_RATE
        self._resync_pools()

    def advance_society(self, yr):
        """Once a year: everything in this file that moves on the society's
        own slow clock rather than on a project's. Called from step() right
        alongside _demographic_recovery(), which is the same kind of thing -
        a population figure that ramps in over generations - for population
        instead of literacy and trades.
        """
        self._advance_literacy(yr)
        self._advance_trade_absorption(yr)

    # ---- WHAT YOU BUILT DOES NOT STAY YOURS ---------------------------------
    # "To make it even more interesting, you could make it so others try to
    # figure your stuff out, to sell it themselves... over a generation or
    # two." economy_index() (economy.py) already spends the idea that
    # diffused technology enriches the whole empire - it raises the WHOLE
    # economy the instant a tier-2+ node is DONE, with no delay and no
    # distinction between a technique you have never opened for business and
    # one you have been visibly selling from for a century. That is the
    # empire-wide half of the story, and it is not this file's to touch
    # (economy.py is another agent's). What is missing, and IS this file's
    # job, is the other half: a NUMBER, per venture, for how much of the one
    # thing YOU personally run has leaked to imitators - not a price, which
    # is the competing agent's own territory (see goods_market_factor,
    # economy.py, already doing exactly that job, by AGE, for four goods
    # categories) - a fraction of the original edge that is gone, that a
    # price formula can spend however it spends a competitive market. This
    # is deliberately NOT wired into revenue() here: that function belongs to
    # the agent making the goods market competitive at the same time this was
    # written, and two agents independently pricing the same venture is
    # exactly the tangle the brief asked this to avoid. See diffusion_share's
    # own docstring for exactly how a price formula should read it.
    #
    # Years for HALF of a visibly-run venture's original edge to have leaked
    # to competitors who watched you run it, absent any effect of publishing
    # or literacy. Pitched at the low end of "a generation or two" (a
    # generation is conventionally 25-30 years) because the ventures this
    # applies to are ones you are OPERATING for revenue in public, which is
    # the most visible thing a person in this model can be doing - the
    # opposite case, a technique you worked out and never opened for
    # business, is exactly what `k not in self.operating` below returns zero
    # for, because nobody has anything to watch.
    VENTURE_DIFFUSION_HALF_LIFE_YEARS = 40.0
    # HOWEVER LONG YOU HAVE BEEN VISIBLE, some of a first-mover's edge never
    # leaves: your own customers, your own reputation for the thing, your own
    # head start on the next improvement. Capped, the same way protection,
    # familiarity and every other saturating share in this file are capped,
    # so this can never be read as "and eventually it reaches 1.0", a claim
    # this model has no basis for making.
    VENTURE_DIFFUSION_CAP = 0.65

    def diffusion_share(self, k):
        """0..VENTURE_DIFFUSION_CAP: how much of what running venture `k`
        earns has already leaked to competitors who watched you run it and
        went into the same business themselves.

        Zero for anything not currently operating (running()/is_venture,
        projects.py) - a technique sitting in `done` with the doors shut is
        not a thing anybody has watched you run - and zero for anything with
        no revenue, since there is no market in it to compete for. Two
        things move it FASTER than the bare passage of time: a corpus that is
        written down and dispersed is knowledge a rival can read rather than
        having to reverse-engineer from watching your workshop (reusing
        corpus_written/corpus_dispersed - the model's own existing idea of
        how published knowledge spreads, rather than inventing a second one
        - see the brief's own pointer to it); and a more literate society has
        more people able to read it and go into business against you, the
        same literacy_general this file already reads everywhere else a
        society's own capacity is the question.

        FOR THE MARKET AGENT: a revenue formula that wants to spend this
        number honestly should reduce what THIS venture earns by up to this
        share while economy_index() (or its successor) is credited with the
        matching gain to the wider economy - `diffused` there already grows
        with self.done regardless of this function, so the two are additive,
        not double-counting the same escape.
        """
        if k not in self.operating:
            return 0.0
        n = self.nodes.get(k)
        if not n or n.get("rev", 0) <= 0:
            return 0.0
        started = self.opened_year.get(k, self.done_year.get(k, self.year))
        age = max(0.0, self.year - started)
        pace = 1.0
        if self.running("corpus_dispersed"):
            pace = 1.7
        elif self.running("corpus_written"):
            pace = 1.3
        gen_lit = float(self.civ.get("literacy_general", 0.12))
        pace *= 0.7 + 0.3 * min(2.0, gen_lit / max(0.02, self.LITERACY_REFERENCE_GENERAL))
        half_life = self.VENTURE_DIFFUSION_HALF_LIFE_YEARS / max(0.4, pace)
        share = 1.0 - 0.5 ** (age / half_life)
        return min(self.VENTURE_DIFFUSION_CAP, max(0.0, share))

    def diffusion_index(self):
        """One number for the whole household: the revenue-weighted average
        of diffusion_share() across everything currently operated for a
        living. 0.0 if nothing is operating, or everything operating is
        brand new. Revenue-weighted rather than a plain average because a
        household running one huge ironworks and one brand-new stall should
        read as "mostly caught up with", not as "half caught up with" -
        exactly the same reasoning revenue() itself already weights by each
        node's own `rev` figure.
        """
        ops = sorted(k for k in self.operating
                     if self.nodes.get(k, {}).get("rev", 0) > 0)
        if not ops:
            return 0.0
        tot_w = tot = 0.0
        for k in ops:
            w = self.nodes[k]["rev"]
            tot_w += w
            tot += w * self.diffusion_share(k)
        return tot / tot_w if tot_w > 0 else 0.0

    # FOG OF WAR. Without it the player sees the entire tree from the first
    # minute, including exactly what a transistor needs, which is both a spoiler
    # and a lie about what knowing something feels like. With fog on you see
    # what you have built in full, what you could start next as a one line
    # summary, and nothing at all about where any of it leads.

    def _is_foreign_institution(self, k):
        # CACHED FOREVER, not per-year, and ONLY for civs that actually pay
        # for the string search below. Rome's own answer is unconditionally
        # False without looking at k at all - that branch was already as
        # cheap as a Python method call can be, and touching a cache dict for
        # it would only add overhead. Everyone else's answer depends only on
        # this civilization's id (fixed at construction) and this node's own
        # key and name (fixed tree data) - nothing that changes over a run.
        # The 4a auto-grant loop in step() called this for every node in
        # `order` (2,831 of them) every single year, most of them already
        # done or never going to be granted this way at all, so a 500-year
        # Han run paid for the same string search on the same node hundreds
        # of times over. See `_done_changed` for the convention this
        # deliberately does NOT need: there is no invalidation here because
        # nothing it reads can change after the Sim is built.
        if self.civ.get("id") == "rome_100ad":
            return False
        cache = self.__dict__.setdefault("_foreign_institution_cache", {})
        v = cache.get(k)
        if v is None:
            hay = (k + " " + self.nodes[k].get("name", "")).lower()
            v = any(m in hay for m in self.FOREIGN_MARKERS)
            cache[k] = v
        return v

    def _is_foreign_only(self, k):
        """A legal or civic institution of a society that is not this one."""
        # CACHED FOREVER, for the same reason as _is_foreign_institution just
        # above, and with the same Rome fast path kept outside the cache.
        # start_reason() calls this on every not-yet-done node it is asked
        # about, every year, for as long as that node stays unbuilt.
        if self.civ.get("id") == "rome_100ad":
            return False
        cache = self.__dict__.setdefault("_foreign_only_cache", {})
        v = cache.get(k)
        if v is None:
            hay = (k + " " + self.nodes[k].get("name", "")).lower()
            v = any(m in hay for m in self.FOREIGN_INSTITUTIONS)
            cache[k] = v
        return v

    def needs_first(self, k):
        """(node, why) this society must have before it can begin `k` at all.

        cost_multipliers say a domain is DEARER here. Some things are not dear,
        they are impossible: a break tester started horse_collar in the Valley
        of Mexico in 1500, on the same screen as a menu describing a society
        with "no draught animals, no iron, no wheel in practical use", and
        `why` there still described it as a collar for a draught horse.

        Data, like everything else about a civilisation, and always liftable -
        every entry names the node that opens it. See _SCHEMA.md.
        """
        spec = self.civ.get("needs_first") or {}
        for key, ent in spec.items():
            if key.startswith("_") or not isinstance(ent, dict):
                continue
            if k in (ent.get("ids") or ()):
                node = ent.get("node")
                if node and node not in self.done:
                    return node, (ent.get("because") or
                                  "this society has no %s" % key)
        return None, None

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

        def mult(key):
            m = float(mults[key])
            r = rem.get(key)
            if isinstance(r, dict) and r.get("node") in self.done:
                m = float(r.get("residual", 1.0))
            return m

        # THE CATEGORY IS THE CRAFT; THE TRAITS ARE WHAT IT IS FOR, and treating
        # them as equals inverted the whole system. Every matching key used to be
        # multiplied together, so a longship - category `ships`, which the Norse
        # file scores 0.60, the best in Europe - also carried its `infrastructure`
        # trait at 1.80 and `commerce` at 1.10, and came out at 1.19. Measured
        # across the tree before this fix: all 20 ship nodes, 48 of 50 marine
        # nodes and all 19 navigation nodes cost the Norse MORE than they cost
        # Rome. The one thing that civilisation is famous for was its worst
        # domain, and the file said the opposite.
        #
        # What a thing takes to build is its craft. What it is used for should
        # colour that, not overwhelm it, so traits apply at a damped exponent
        # when the craft is known and at full weight when it is not.
        cat = n.get("cat")
        traits = [t for t in (n.get("traits") or ()) if t in mults]
        if cat in mults:
            f = mult(cat)
            for t in traits:
                f *= mult(t) ** 0.25
            return f
        f = 1.0
        for t in traits:
            f *= mult(t)
        return f

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
                # AND NOTHING THIS SOCIETY CANNOT HAVE. needs_first already
                # says a Mexica household cannot start a horse collar in the
                # Valley of Mexico, and this loop was handing the same
                # household square sails, a spritsail, a mortise-and-tenon
                # Mediterranean hull, large merchant sailing ships and the
                # monsoon route to India, free, before turn one - because
                # each is tier 0 and costs nothing, which is the test this
                # loop was applying. Free and weightless is not the same as
                # universally available.
                if self.needs_first(k)[0]:
                    continue
                if (n["tier"] == 0 and n["ph"] == 0 and n["_total_cost"] <= 1
                        and all(p in self.done for p in n["pre"])):
                    self.done.add(k)
                    self._done_changed()
                    self.granted.add(k)
                    # done_year is set by the callers after construction, so do
                    # not assume it exists yet at grant time.
                    if not hasattr(self, "done_year"):
                        self.done_year = {}
                    self.done_year[k] = self.cfg["start_year"]
                    changed = True

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
        if kind == "output_factor":
            m, reason = self._military_war_relief()
            if reason:
                mult *= m
                why.append(reason)
        return mult, why

    def _military_war_relief(self):
        """A state that can fight loses less of its economy when it has to.

        Every output_factor hazard in every civilization file - Rome's third
        century crisis and Gothic settlement, Han's rebellions and
        fragmentations, England's civil wars, the Mexica wars of
        independence and revolution - IS a war, a rebellion, or the
        administrative aftermath of one; none of them is a plague or a
        famine, which hit staff_loss and real_erosion instead (see the
        `years` these hazards share with `sack_chance` and `values` in the
        civilization files). So this is not gated per-hazard the way
        HAZARD_COUNTERS entries are: it is one diminishing term, on the same
        military_leverage() count update_protection() reads, applied
        wherever `output_factor` is. Deliberately NOT applied to staff_loss:
        a founder with cannon should not cure the Antonine plague, and most
        staff_loss hazards in the civilization files are exactly that -
        disease and famine - with no sack_chance or output_factor alongside
        them to say otherwise.

        Capped at 0.30, matching endowment_land's own share in
        HAZARD_COUNTERS["output_factor"] rather than exceeding it: land of
        your own and an army of your own are comparable hedges, and neither
        should dwarf the other.
        """
        lev = self.military_leverage()
        if lev <= 0.0:
            return 1.0, None
        share = 0.30 * lev
        return (1.0 - share), ("an army and treasury the state can call on "
                               "(military strength %d%%)" % round(lev * 100))

    def _calendar_floor_remaining(self, goal):
        """Minimum calendar years before `goal` is finished, even if every
        prerequisite still open were started TODAY - critical_path()'s own
        floor (see data.py), minus whatever of that chain is already done.

        THE NUMBER THE WARNING WAS MISSING. A Han playtester was told from
        turn one that the hedge against being sacked was "copies of your
        work kept somewhere else" and, having acted on that the moment it
        was said, still lost the corpus to the Yellow Turban rebellion -
        twice, some of it rebuilt and lost again. The advice was right and
        the words never changed; what was missing was that the strongest
        hedge in HAZARD_COUNTERS["sack_chance"] (academy_network, sharing
        0.40 of the risk, the biggest single number in that list) sits at
        the end of scientific_method -> corpus_written -> corpus_dispersed
        -> academy_network, a chain whose OWN yrs fields (data already
        carried, already shown per-node as `calendar_floor_years` by
        protocol.py, and already the basis of the `path` command's own
        "Longest serial chain" line) sum to a 30-year floor - not something
        five years' warning is enough for, and nothing before this said the
        chain had a length at all, only that it existed.

        Reuses critical_path(), the SAME function `path` already calls for
        exactly this question about a goal node - not a second notion of
        "how long something takes" invented for hazards - and only sums the
        portion of the winning chain not already in self.done, so a player
        partway through the chain sees what is actually left, not the whole
        chain's floor from scratch every time.
        """
        if goal not in self.nodes:
            return None
        _total, chain = critical_path(self.nodes, goal)
        remaining = sum(max(self.nodes[k]["yrs"], self.nodes[k]["ph"] / 2000.0)
                        for k in chain if k not in self.done)
        return round(remaining, 1)

    def hazard_advice(self, kind):
        """What KIND of thing would help, without naming what you cannot see.

        Under fog this must not turn into a list of node ids to go and build:
        that is the tech tree by the back door. It names the kind of answer, in
        the same words a person in the year 100 would use.
        """
        words = {"staff_loss": "clean water, quarantine, and eventually inoculation",
                 "sack_chance": "walls, firearms, powerful friends, and copies of "
                                "your work kept somewhere else",
                 "output_factor": "land and power of your own, not depending on trade "
                                  "a war can cut, and a state that can fight back",
                 "real_erosion": "metal you dug yourself, land, and a way to prove "
                                 "what a coin contains"}
        mult, why = self.hazard_relief(kind)
        out = {"you_currently_take": round(mult, 3), "because_of": why}
        if mult > 0.75:
            out["what_would_help"] = words.get(kind, "")
            # AND SOMETHING YOU CAN ACT ON. A playtester was told the answer to
            # the Spanish was "walls, firearms, powerful friends, and copies of
            # your work kept somewhere else", played 154 years, saw 269
            # startable things, and reported finding no hedge of any kind. The
            # hedges were there and shallow - a sand filter needs no
            # prerequisite at all, only one artisan you do not have yet - but
            # advice you cannot act on reads as advice about nothing.
            #
            # This does NOT name the hedge or open the tree. It names things you
            # could begin TODAY, which you can already see, and says only that
            # they lead that way. That is what a person who knows how the
            # technology works would know and what fog has no business hiding:
            # fog is about the society, not about your own education.
            step = self.hedge_first_steps(kind)
            if step:
                out["you_could_begin_now_toward_it"] = step
            # AND HOW LONG BEFORE ANY OF IT HELPS. Numbers only, never a node
            # id, so this tells nothing fog would hide: two playtesters (Han,
            # Rome) each acted on `what_would_help` the moment they read it and
            # were sacked anyway, because the strongest real hedge among these
            # words is not a purchase, it is a multi-decade diffusion chain -
            # see _calendar_floor_remaining's own comment. Given as a range
            # because these words bundle several genuinely different hedges
            # (a patron is bought in a few years; three dispersed academies are
            # not), and the range is the honest shape of the answer: some of
            # this is fast, and the slowest part is not.
            floors = sorted(
                f for node, _share, _label in self.HAZARD_COUNTERS.get(kind, ())
                if not node.startswith("_") and node in self.nodes
                and not self.has(node)
                for f in [self._calendar_floor_remaining(node)]
                if f is not None)
            if floors:
                out["even_started_today_the_real_hedges_here_take_years"] = (
                    {"quickest": floors[0], "slowest": floors[-1]}
                    if floors[0] != floors[-1] else floors[0])
        return out

    def hedge_first_steps(self, kind, limit=4):
        """The hedges against `kind` that you can actually see, and what each
        one is waiting for.

        Deliberately NARROW: the counters themselves and their direct
        prerequisites, and only those fog would let you see anyway. An earlier
        version walked the whole ancestry and ranked by strategy order, which
        duly advised beginning a "respectable cover identity" as a hedge
        against smallpox - true, in that most of the tree is downstream of it,
        and useless to a reader. If nothing near is visible, the words on their
        own are the honest answer and this says nothing.
        """
        want = []
        leads_to = {}
        counters = set()
        for node, _share, label in self.HAZARD_COUNTERS.get(kind, ()):
            if node not in self.nodes or node in self.done:
                continue
            want.append((0, node))
            counters.add(node)
            leads_to.setdefault(node, label)
            for pre in self.nodes[node]["pre"]:
                if pre in self.nodes and pre not in self.done:
                    want.append((1, pre))
                    # SAY WHAT IT LEADS TO. A break tester was offered
                    # `horse_collar` as the thing to build against the Antonine
                    # plague, directly under prose saying the remedy is "clean
                    # water, quarantine, and eventually inoculation". It is a
                    # prerequisite of crop rotation, which is a real hedge
                    # against a famine year - but nothing said so, and an
                    # unexplained horse collar under a plague warning reads as
                    # the game being broken.
                    leads_to.setdefault(pre, "a step toward %s" % label)
        memo = {}
        seen, out = set(), []
        for d, k in sorted(want):
            if k in seen:
                continue
            seen.add(k)
            if getattr(self, "fog", False) and not self.is_visible(k, _memo=memo):
                continue
            ok, why = self.start_reason(k)
            entry = {"id": k, "name": self.nodes[k]["name"],
                     "cost": round(self.project_cost(k), 1),
                     "because_it_gives_you": leads_to.get(k),
                     "can_begin_now": bool(ok),
                     "waiting_on": None if ok else why}
            # THE WHOLE ROAD, not just this one node's own calendar floor. A
            # step that "can begin now" and costs little reads as quick; for
            # a HAZARD_COUNTERS entry itself (not one of its prerequisites)
            # this is often the LAST of several such steps, each looking
            # equally beginnable, with a total the size of a human generation
            # behind it. See _calendar_floor_remaining.
            if k in counters:
                floor = self._calendar_floor_remaining(k)
                if floor is not None:
                    entry["years_even_if_you_start_today"] = floor
            out.append(entry)
            if len(out) >= limit:
                break
        # What you can start comes first: it is the part you can act on today.
        out.sort(key=lambda e: not e["can_begin_now"])
        return out

    # ---- A TIMELINE, NOT A WALL OF TEXT THAT NEVER CHANGES -----------------
    # `risk` already had dates, yearly odds, cumulative danger and what prior
    # choices buy against each - a winning player called that combination one
    # of the strongest systems in the game. What it did not have was ONE
    # compact, chronological answer to "what is coming, how soon, and am I
    # covered" - that reply is scattered across a single flat `hedged_by`
    # (one word for the whole civilisation, not per hazard) and a list of
    # hazard rows each carrying its own sack/staff-loss percentages several
    # keys deep. And `hedged_by` itself never changed its wording as a date
    # got closer: a Rome player watched it read "nothing yet" for a hundred
    # and fifty years, across a hazard that eventually arrived anyway, and
    # lost 22 technologies, 1.38 million denarii and 47 staff in the single
    # turn it landed - a third of their critical-path progress. The words had
    # been true every one of those years and had stopped being a WARNING long
    # before that, because a sentence that reads identically five years out
    # and a hundred and fifty years out carries no information about which of
    # those it is.
    #
    # THE FIX IS NOT A COUNTDOWN. A bare "N years left" still reads the same
    # at every distance greater than zero - what actually has to escalate is
    # the relationship between the calendar and the hedge itself. The real
    # hedges in HAZARD_COUNTERS have lead times of their own (see
    # _calendar_floor_remaining - up to thirty years for academy_network's
    # own dispersal chain) and a hazard that is fifty years off with a five-
    # year hedge is not urgent, while the SAME fifty years against a thirty-
    # year hedge is already something to be starting now, not later - it is
    # the gap between the two clocks that should set the tone, not either
    # clock alone.
    #
    # Three clean levels come out of comparing "years until it arrives" to
    # "years the live hedges still need". Two such lead times are kept, not
    # one, because they escalate at DIFFERENT moments: the QUICKEST counter
    # among HAZARD_COUNTERS (some relief, soonest) and the SLOWEST (the
    # strongest one among the same counters - the thirty-year
    # academy_network dispersal chain, for sack_chance). A player still has
    # time to begin the quick, partial answer well after it is already too
    # late for the one actually carrying the largest share of the relief, so
    # the bands below are four, nearest first (HORIZON_MULT gives the margin
    # on the furthest boundary - calm vs "begin now" - because a player who
    # starts exactly on the strong hedge's own floor has no slack left for
    # anything going wrong with it):
    #   - past the strong hedge's own floor by a comfortable margin: plenty
    #     of time, said once and then left alone.
    #   - inside that margin, strong hedge not yet begun: begin it now -
    #     there is still time, but not much of it.
    #   - past the strong hedge's own floor, but still within the quick
    #     hedge's: a partial answer can still finish; the real one cannot.
    #   - past even the quick hedge's own floor: too late to finish anything
    #     from a cold start; the event is coming regardless of what begins
    #     today.
    # A hazard already well hedged, or already in progress, or with no known
    # hedge at all, reports that plainly instead of forcing it into one of
    # these four bands.
    HAZARD_TIMELINE_BEGIN_NOW_MULT = 1.5
    # Which urgency tags keep their full sentence once a row is past the
    # nearest one - see the note where this is applied, in hazard_timeline
    # itself, for why position in the list is the wrong thing to key this on.
    HAZARD_TIMELINE_WARN_TAGS = frozenset(
        {"happening now", "too late to hedge", "stopgap only", "begin hedge now"})

    @staticmethod
    def _yr_words(n):
        n = round(n)
        return "%d year" % n if n == 1 else "%d years" % n

    def hazard_timeline(self, limit=4):
        """What is coming, how many years off, and whether what stands
        between now and then is enough - one line per hazard, nearest first.

        This is `risk`'s missing compact view: every number in it (years
        until, current relief, the fastest hedge's own lead time) is already
        computed elsewhere in this file (hazard_relief, hazard_advice,
        _calendar_floor_remaining) - this only arranges them chronologically
        and picks the words that should change as the gap between "when it
        lands" and "how long the hedge takes" closes. See the section
        comment above for why that gap, not the bare year count, is what
        actually has to escalate.
        """
        rows = []
        for h in (self.civ.get("hazards") or []):
            yrs = h.get("years") or []
            if not yrs:
                continue
            y0 = yrs[0]
            y1 = yrs[1] if len(yrs) > 1 else yrs[0]
            if self.year > y1:
                continue                      # already survived, or missed
            in_progress = y0 <= self.year <= y1
            years_until = 0 if in_progress else (y0 - self.year)
            name = h.get("name", "hazard")
            kinds = [kd for kd in
                     ("staff_loss", "sack_chance", "output_factor", "real_erosion")
                     if kd in h]
            if not kinds:
                continue
            # THE LEAST-DEFENDED SIDE OF IT, not an average, and its OWN
            # hedge's own lead time - not the quickest lead time among ALL
            # the kinds this hazard happens to carry. A hazard that is both
            # a sacking risk (hedged, for real, only by a thirty-year
            # academy_network dispersal chain) and an output shock (hedged
            # by things as quick as two years) is exactly as urgent as the
            # sacking half if that is the half nothing has been built
            # against - taking the faster OTHER kind's lead time here would
            # have said "two years will cover you" about a risk a two-year
            # hedge does nothing for, which is the averaging mistake the
            # section comment above warns against, just one kind's own floor
            # away from where it would actually bite.
            # QUICKEST (some relief, started cold, soonest) and SLOWEST (the
            # strongest real hedge among the same counters - up to the
            # thirty-year academy_network chain for sack_chance) are both
            # kept, because they escalate at DIFFERENT times: a player still
            # has time for a partial answer after it is already too late for
            # the one that actually carries the largest share of the relief.
            worst_mult, quick_hedge, strong_hedge = 0.0, None, None
            for kd in kinds:
                mult, _why = self.hazard_relief(kd)
                if mult <= worst_mult:
                    continue
                worst_mult = mult
                quick_hedge = strong_hedge = None
                if mult > 0.75:
                    advice = self.hazard_advice(kd)
                    fl = advice.get("even_started_today_the_real_hedges_here_take_years")
                    if isinstance(fl, dict):
                        quick_hedge, strong_hedge = fl.get("quickest"), fl.get("slowest")
                    elif isinstance(fl, (int, float)):
                        quick_hedge = strong_hedge = fl
            hedged = worst_mult <= 0.75
            _yu = self._yr_words(years_until)
            if in_progress:
                urgency = "happening now"
                headline = ("%s: under way now%s"
                            % (name, "" if hedged else
                               ", and built defences do not cover most of it"))
            elif hedged:
                urgency = "hedged"
                headline = "%s: %s off, already well hedged" % (name, _yu)
            elif quick_hedge is None:
                urgency = "no hedge found"
                headline = ("%s: %s off, unhedged, no hedge visible yet"
                            % (name, _yu))
            elif years_until <= quick_hedge:
                urgency = "too late to hedge"
                headline = ("%s: only %s left; even the fastest hedge needs "
                            "about %s - it is coming regardless"
                            % (name, _yu, self._yr_words(quick_hedge)))
            elif strong_hedge and strong_hedge > quick_hedge and years_until <= strong_hedge:
                urgency = "stopgap only"
                headline = ("%s: %s off - a quick hedge (%s) could still "
                            "finish, the strong one (%s) could not"
                            % (name, _yu, self._yr_words(quick_hedge),
                               self._yr_words(strong_hedge)))
            elif years_until <= (strong_hedge or quick_hedge) * self.HAZARD_TIMELINE_BEGIN_NOW_MULT:
                urgency = "begin hedge now"
                headline = ("%s: %s off; the real hedge needs %s - time is "
                            "short" % (name, _yu,
                                      self._yr_words(strong_hedge or quick_hedge)))
            else:
                urgency = "on the horizon"
                headline = ("%s: %s off, unhedged, plenty of time to build "
                            "one (%s)" % (name, _yu,
                                          self._yr_words(strong_hedge or quick_hedge)))
            rows.append({"name": name, "years_until": years_until,
                         "in_progress": in_progress, "urgency": urgency,
                         "headline": headline})
        rows.sort(key=lambda r: (0 if r["in_progress"] else 1, r["years_until"]))
        rows = rows[:limit]
        # COMPACT EXCEPT WHERE IT IS ACTUALLY A WARNING, same reasoning
        # knowledge_risk's own known_hazards_ahead already applies to its
        # "note"/"what_you_can_do" fields, but keyed on URGENCY rather than
        # bare position in the list: a hazard that is calm stays calm
        # whether it is first or sixth on the list, and a hazard that is not
        # - "too late to hedge", "stopgap only", "begin hedge now",
        # "happening now" - is exactly the one case this whole method exists
        # to NOT bury in a compact name-and-number line. The single nearest
        # entry keeps its sentence regardless, so the reply always orients
        # on at least one real sentence even in a run where everything left
        # is calm.
        for i, r in enumerate(rows):
            if i == 0 or r["urgency"] in self.HAZARD_TIMELINE_WARN_TAGS:
                continue
            r.pop("headline", None)
            r.pop("in_progress", None)
        return rows

    def lose_capital(self, fraction, floor_at_zero=True):
        """Destroy a fraction of what you HAVE. Never a fraction of what you owe.

        Every capital loss in this file used to be written `self.capital *= x`,
        which is sign-blind: at minus a thousand denarii a sacking multiplied
        the DEBT by 0.4 and handed the player six hundred denarii. A sweep of
        the playtest notes caught it live twice - a Mexica sack took -251 to
        -100.5, an England thatch fire took -629.2 to -569.4 - which made the
        deepest hole in the game the safest place to stand, and made every
        catastrophe a reason to stay in arrears.

        A fire destroys goods. If you own nothing, the fire takes nothing; it
        does not pay off your creditors.
        """
        if self.capital <= 0:
            return 0.0
        lost = self.capital * max(0.0, min(1.0, fraction))
        self.capital -= lost
        return lost

    def _resolve_hazard_condition(self, h, yr, a):
        """History on rails, but the household is allowed to have changed
        the ground it runs on.

        A dated hazard's `years` window used to be the whole story: the
        Third-Century Crisis or the African grain fleet failing in 439 fired
        on schedule no matter what the player had built, which is the exact
        complaint a player who had spent three centuries industrialising
        made - technology changed how much a hazard hurt, never whether it
        happened. This is the fix, and it is deliberately narrow: only a
        hazard whose CIVILIZATION FILE gives it a `condition` is touched at
        all, so a hazard with none - which is most of them - fires exactly
        as before. See the civilization files themselves for which hazards
        got one and why: in every case the note names a MATERIAL cause (a
        supply line, a building material, a drainage engine) that a rich
        household's own building can plausibly remove, never a succession, a
        religious policy or an administrative reform - one household in 300
        AD did not choose the emperor, and none of those hazards carry a
        `condition` at all.

        `condition` names exactly one numeric field on the hazard
        (`field`), a list of tech ids the player must have ALL of
        (`requires_all`), and what happens when they do (`outcome`:
        "avert" drops the field for this hazard entirely, "alter" scales
        it via `alter_scale`, which is how much of the ORIGINAL shortfall
        - 1 minus the field, for output_factor; the field itself for the
        rest - survives). Returns `h` unchanged, or a SHALLOW COPY with
        that one field adjusted; every other field on the hazard (a sack
        risk, a values shift) is untouched, because a household that fed
        itself did not thereby also arm itself or convert the Church.

        Told, not silent, in all three cases - fires as written, fires
        altered, or is averted - the once, the year the hazard's window
        opens (`yr == a`), keyed on the hazard's own name so a multi-year
        window does not repeat itself every year it stays open.
        """
        cond = h.get("condition")
        if not cond:
            return h
        field = cond.get("field")
        need = cond.get("requires_all") or []
        met = all(self.has(n) for n in need)
        if yr == a:
            said = getattr(self, "_said_condition", None)
            if said is None:
                said = self._said_condition = set()
            key = h.get("name", "hazard")
            if key not in said:
                said.add(key)
                msg = cond.get("met_message" if met else "unmet_message")
                if msg:
                    self.log.append((yr, msg))
        if not met or field not in h:
            return h
        h2 = dict(h)
        outcome = cond.get("outcome")
        scale = cond.get("alter_scale", 1.0)
        if outcome == "avert":
            del h2[field]
        elif outcome == "alter":
            if field == "output_factor":
                h2[field] = 1.0 - (1.0 - h[field]) * scale
            else:
                h2[field] = h[field] * scale
        return h2

    def _shocks(self, yr):
        """Dated catastrophes, read from the CIVILIZATION file.

        Rome gets the Antonine plague and the third century crisis. England 1300
        gets the Great Famine and the Black Death. The Mexica get the contact
        epidemics, which are the most severe hazard in the whole directory and
        are not a fair fight. None of it is hardcoded here any more.
        """
        r = self.rng
        prep = self.running("plague_preparedness")
        for h in self.civ.get("hazards", []):
            a, b = h.get("years", [0, 0])
            if not (a <= yr <= b):
                continue
            h = self._resolve_hazard_condition(h, yr, a)
            if "staff_loss" in h and r.random() < 0.32:
                relief, why = self.hazard_relief("staff_loss")
                loss = h["staff_loss"] * relief
                _people_before = (self.scholars + self.artisans
                                  + sum(self.employees.values()))
                self.scholars *= (1 - loss); self.artisans *= (1 - loss)
                for t in list(self.employees):
                    self.employees[t] *= (1 - loss)
                self.directors_extra *= (1 - loss)
                # THE MONEY GOES TOO, and the log never said so. A weird-play
                # tester watched the Black Death take 12,676 denarii down to
                # 9,111 against a stated net of -195 a year, with the only
                # message reading "staff -45%", and reasonably concluded the
                # accounts were broken. A plague empties the market as well as
                # the workshop; that is real, and it has to be said.
                cash = self.lose_capital(loss * 0.6)
                # SAY WHAT ACTUALLY HAPPENED TO YOU. A weird-play tester with no
                # staff and no money read "staff -45%, and 0 pence gone" three
                # years running and reasonably concluded the event was firing
                # against nobody. It was: they had nothing to lose. An event
                # should report the harm it did, not the harm it would have
                # done to somebody else.
                # THE WHOLE SOCIETY LOST PEOPLE TOO, not only your household,
                # and your own hedges do not change that: the quarantine you
                # built protects your people, not everyone else's labour
                # market. A playtester found a plague that hit them and
                # nobody else, and asked why their wage bill never moved
                # afterward the way the real Black Death moved England's.
                # This uses the hazard's RAW rate, never `loss` above, which
                # is personal and already reduced by your own hedges; and it
                # compounds onto any deficit still open from an earlier,
                # unfinished recovery rather than overwriting it, because two
                # plagues in one lifetime are worse than either alone.
                # _demographic_recovery() in core.py is what reads this back
                # out into pop_scale and wage_index, and lets it decay.
                raw = h["staff_loss"]
                self.pop_deficit = 1.0 - (1.0 - self.pop_deficit) * (1.0 - raw)
                self._pop_recovery_years = max(self._pop_recovery_years,
                                                150.0 * (raw / 0.45))
                # SEVERITY HONESTY: the words have to match `loss`, the
                # number the mechanic just applied above, not `raw`, the
                # historical hazard's own unmitigated figure - a tester
                # whose sanitation and quarantine cut a 28% plague down to
                # 0.4% still read "staff -0%... (would have been -28%: ...)"
                # in the same breath, and came away certain they had just
                # lived through a 28% plague, because the sentence restated
                # 28% twice and the near-zero number once. `relief` (mult)
                # is the SAME diminishing fraction hazard_relief and
                # hazard_advice already compute, and hazard_timeline's own
                # "hedged" cutoff is this same 0.75 - reused, not a second
                # estimate of what your hedges did.
                _hit = []
                if _people_before > 0.05:
                    if why and relief <= 0.25:
                        _hit.append("staff -%d%%, held off almost entirely "
                                    "by what you built (%s)"
                                    % (loss * 100, "; ".join(why)))
                    elif why and relief <= 0.75:
                        _hit.append("staff -%d%% (softened by %s)"
                                    % (loss * 100, "; ".join(why)))
                    else:
                        _hit.append("staff -%d%%" % (loss * 100))
                if cash > 0.5:
                    _hit.append("%s gone with the trade that stopped"
                                % "{:,.0f}".format(cash))
                if not _hit:
                    _hit.append("you had nothing it could take")
                msg = "%s: %s" % (h.get("name", "hazard"), ", ".join(_hit))
                # THE WHOLE SOCIETY LOST PEOPLE TOO, not only your household,
                # and your own hedges do not change that: the quarantine you
                # built protects your people, not everyone else's labour
                # market (see the comment on `raw` above). Kept as a
                # SEPARATE sentence, explicitly "either way", so a household
                # that came through nearly untouched does not read this
                # empire-wide toll as its own.
                if raw > 0.01:
                    msg += (". Empire-wide, population -%d%% - wages (and "
                            "everything paid in them) stay dear for roughly "
                            "the next %d years either way"
                            % (raw * 100, round(self._pop_recovery_years)))
                self.log.append((yr, msg))
            if "sack_chance" in h:
                relief, why = self.hazard_relief("sack_chance")
                p = h["sack_chance"] * relief
                if why and r.random() < h["sack_chance"] - p:
                    self.log.append((yr, "%s: an attack comes to nothing (%s)"
                                     % (h.get("name", "crisis"), "; ".join(why[:3]))))
                if r.random() < p:
                    # SAY WHAT IT TOOK FROM YOU. This printed "a site is
                    # sacked" and nothing else while removing 62% of a
                    # weird-play tester's money, restarting every project they
                    # had and cutting their people nearly in half - and they
                    # owned no sites at all. The plague family was taught to
                    # report the harm it actually did; this one was not, and a
                    # bare event line against an unexplained fall in capital is
                    # how a player stops trusting the ledger.
                    _cap0 = max(0.0, self.capital)
                    _people0 = self.artisans + self.scholars
                    _act0 = len(self.active)
                    self.lose_capital(0.60)
                    self.artisans *= 0.55; self.scholars *= 0.55
                    self.directors_extra *= 0.65
                    for k in sorted(self.active):
                        self.active[k]["ph_left"] = self.nodes[k]["ph"]
                        self.active[k]["yrs"] = 0.0
                    _took = []
                    if _cap0 - max(0.0, self.capital) > 0.5:
                        _took.append("%s taken"
                                     % "{:,.0f}".format(_cap0 - max(0.0, self.capital)))
                    if _people0 - (self.artisans + self.scholars) > 0.05:
                        _took.append("%.1f of your people gone"
                                     % (_people0 - (self.artisans + self.scholars)))
                    if _act0:
                        _took.append("%d project%s back to the beginning"
                                     % (_act0, "" if _act0 == 1 else "s"))
                    self.log.append((yr, "%s: a site is sacked - %s"
                                     % (h.get("name", "crisis"),
                                        ", ".join(_took)
                                        or "you had nothing it could take")))
                    # Sim.corpus_hedge (core.py) is the one place this is
                    # decided, and `risk` calls the same method - see its
                    # own comment for why this used to quote `running()`
                    # and tell a player, in `risk`, that they had a hedge
                    # `running()` said had already lapsed.
                    pl, frac, _hedge_before = self.corpus_hedge()
                    if r.random() < pl:
                        # sorted() matters: self.done is a SET and iterates in an
                        # order that depends on PYTHONHASHSEED, so feeding it
                        # unsorted to rng.sample made the same --seed give a
                        # different answer every invocation.
                        # Never the society's own inheritance: you can lose what
                        # YOU built, not what the civilization has always known.
                        # Nor corpus_dispersed: its whole definition is that
                        # copies exist in other people's hands, beyond this
                        # one site - a sack here cannot reach a copy sitting
                        # in a library three provinces away. corpus_written,
                        # one set of books in one place, stays losable; only
                        # dispersal is out of a single raid's reach. This is
                        # about a SACK specifically - mothballing or
                        # abandoning the corpus yourself is a different
                        # mechanism and still applies.
                        losable = sorted(k for k in self.done
                                         if self.nodes[k]["tier"] >= 2
                                         and k not in self.granted
                                         and k != "corpus_dispersed")
                        if losable:
                            drop = r.sample(losable, max(1, int(len(losable) * frac)))
                            _lost = getattr(self, "forgotten", None)
                            if _lost is None:
                                _lost = self.forgotten = {}
                            for k in drop:
                                self.operating.discard(k)
                                self.done.discard(k)
                                self.mothballed.discard(k)
                                # KEPT, so `risk` can list what you have to
                                # build again. Otherwise the only record is a
                                # log line a century back.
                                _lost[k] = yr
                            self._done_changed()
                            # NAME THEM. A play tester discovered a loss decades
                            # later, when `start X` said "missing prerequisites:
                            # <thing you built two hundred years ago>", and then
                            # rebuilt the chain one refusal at a time. A bare
                            # count is not a report of what happened to you.
                            _named = sorted(drop)
                            _corpus = [c for c in ("corpus_written",
                                                   "corpus_dispersed")
                                       if c in drop]
                            # AND WHAT IT DOES TO THE ROAD YOU ARE ACTUALLY ON.
                            # Naming the lost ids was the first fix; a Rome
                            # player with a real goal set still found out the
                            # road had gotten longer only by re-running `path`
                            # afterwards and comparing it by hand to what they
                            # remembered - a sack that silently undid a third
                            # of their critical-path progress in one turn.
                            # Said here, once, in the same breath as the loss
                            # itself, using the same goal-closure `never_
                            # abandon` already computes and caches.
                            _on_road = 0
                            _goal = getattr(self, "goal", None)
                            if _goal and _goal in self.nodes:
                                try:
                                    _gc = getattr(self, "_goal_closure", None)
                                    if _gc is None:
                                        _gc = self._goal_closure = closure(
                                            self.nodes, _goal)
                                    _on_road = sum(1 for x in drop if x in _gc)
                                except Exception:
                                    _on_road = 0
                            self.log.append((yr, "KNOWLEDGE LOST: %d technolog%s "
                                                 "forgotten - %s%s%s%s"
                                % (len(drop), "y" if len(drop) == 1 else "ies",
                                   ", ".join(_named[:8])
                                   + (" and %d more" % (len(_named) - 8)
                                      if len(_named) > 8 else ""),
                                   # BEFORE the loss, not after: `drop` has
                                   # already come out of `self.done` by this
                                   # point, so re-asking `self.done` here
                                   # could tell a player the corpus was
                                   # "never printed and dispersed" in the
                                   # same sentence that says the corpus
                                   # itself just went - both about the same
                                   # sacking. _hedge_before was read when
                                   # the sack started, before anything was
                                   # taken.
                                   "" if _hedge_before == "corpus_dispersed"
                                   else " (the corpus was never printed and "
                                        "dispersed)",
                                   ". THE CORPUS ITSELF WENT (%s): your hedge "
                                   "against this is gone and 'risk' will say so "
                                   "- build it again first" % ", ".join(_corpus)
                                   if _corpus else "",
                                   (". %d of these stood on the road to your "
                                    "goal: the route is longer than it was a "
                                    "moment ago - 'path' will show the rebuilt "
                                    "shape of it" % _on_road)
                                   if _on_road else "")))
            if "output_factor" in h:
                relief, why = self.hazard_relief("output_factor")
                # relief moves the floor back toward 1.0 rather than scaling the
                # damage: self-sufficiency means less of your income was ever
                # coming through the thing the war cut.
                floor = 1.0 - (1.0 - h["output_factor"]) * relief
                before = self.output_factor
                self.output_factor = min(self.output_factor, floor)
                # ONCE, AND THEN A REMINDER, not every year of a hundred-year
                # war. output_factor recovers a little each step, so this line
                # re-fired the moment the war pulled it back down - which is
                # every single year. A weird-play tester read the same sentence
                # about the Hundred Years War roughly eighty times and stopped
                # reading the log, which is the real cost: a message repeated
                # until it is noise has stopped being a message.
                said = getattr(self, "_said_output", {})
                key = h.get("name", "crisis")
                if before > self.output_factor and yr - said.get(key, -99) >= 20:
                    said[key] = yr
                    self._said_output = said
                    # SAY WHAT HELD. A founder who armed the state before the
                    # war arrived measured protection 0.019 to 0.019 against
                    # one who never touched the military branch, and every
                    # other hazard message in this file already names its
                    # hedges - staff_loss says "would have been"; sack_chance
                    # says "comes to nothing (%s)". This one said nothing,
                    # which is indistinguishable from doing nothing.
                    self.log.append((yr, "%s: trade and output fall to %d%% of "
                                         "normal%s"
                                     % (key, self.output_factor * 100,
                                        " (your own strength holds off worse: %s)"
                                        % "; ".join(why[:3]) if why else "")))
            if "real_erosion" in h:
                relief, why = self.hazard_relief("real_erosion")
                self.money_real *= (1 - h["real_erosion"])
                bite = h["real_erosion"] * 0.85 * relief
                had = max(0.0, self.capital)
                self.lose_capital(bite)
                lost = had - max(0.0, self.capital)
                if not getattr(self, "_said_debasement", 0) or yr - self._said_debasement >= 15:
                    self._said_debasement = yr
                    # SAY WHAT IT DID TO YOU, and say what it did NOT do. A
                    # break tester read "the coin is worth 99% less", checked
                    # `why horse_collar` in 107, 207 and 307 AD, found the
                    # quote identical to the denarius, and filed it as the
                    # debasement doing nothing. It is doing something: every
                    # price in this game is what a thing really costs in
                    # labour and materials, which debasement does not change.
                    # What it destroys is the money you are HOLDING. Quoting
                    # the bite in coin makes that the visible half.
                    self.log.append((yr, "%s: the coin is worth %d%% less than it "
                                         "was%s. Quoted costs are what a thing "
                                         "really takes to make, so they do not "
                                         "move; what debases is the money in "
                                         "your chest, and this year it took %s%s"
                                     % (h.get("name", "debasement"),
                                        (1 - self.money_real) * 100,
                                        "; you feel less of it (%s)" % "; ".join(why)
                                        if why else "",
                                        "{:,.0f}".format(lost)
                                        if lost > 0.5 else "nothing, because you "
                                        "were holding none",
                                        " denarii" if lost > 0.5 else "")))
            if "values" in h:
                # A hazard can kill your people, burn a site, or make you
                # poorer, and that used to be the whole vocabulary. Norse
                # Christianisation is none of those: its real effect is on
                # what the society BELIEVES, which is exactly what
                # alarm_of() and update_protection() read out of self.w. This
                # is apply_tech_effects' mechanism (see there), aimed at a
                # hazard instead of a technology, with one difference: a
                # technology is a single event and logs once, but a hazard
                # like this runs for over a century, so the shift is spread
                # evenly across every year of `years` rather than dumped on
                # the first one. Applying 1/Nth of the total delta every
                # year, for N years, is what "gradual" means here; a single
                # jump on the first year would be exactly the fake
                # instantaneous conversion this mechanism exists to avoid.
                span = max(1, int(b) - int(a) + 1)
                changed = {}
                for field, total_delta in h["values"].items():
                    if field.startswith("_") or not isinstance(total_delta, (int, float)):
                        continue
                    if field not in self.w:
                        continue
                    before = self.w[field]
                    self.w[field] = max(-1.0, min(1.5, before + total_delta / span))
                    if abs(self.w[field] - before) > 1e-9:
                        changed[field] = self.w[field]
                # VISIBLE WHILE IT HAPPENS, not only in hindsight: a tester
                # should be able to watch the society turning against them
                # year by year, not discover it as a lump sum in the future.
                # A hundred-odd years of this hazard would be a hundred-odd
                # near-identical log lines if this fired every year, so it
                # is throttled to the first year, the last, and every tenth
                # in between -- the same spirit as the debasement throttle
                # just above, which exists for the same reason.
                if changed and (yr == a or yr == b or (yr - a) % 10 == 0):
                    self.log.append((yr, "%s: the society's values are shifting (%s)"
                                     % (h.get("name", "hazard"),
                                        ", ".join("%s now %.2f" % (f, v)
                                                  for f, v in sorted(changed.items())))))

    def _random_events(self, yr):
        r = self.rng
        # A patron dies ONCE and then you have courted his heir. The old model
        # rolled 4% every year forever, so a long run logged the same line six
        # times, which is not how having a patron works.
        # ONE ATTRIBUTE, NOT TWO. The guard read `_last_patron_death` and the
        # body set `last_patron_death`, so the twenty-five year cooling-off
        # this comment describes never applied to anything: the roll came up
        # five per cent a year for ever, which is precisely the behaviour the
        # fix was written to stop. (The save list carried the unread name too.)
        if (r.random() < 0.05 and self.running("patron_local")
                and yr - getattr(self, "last_patron_death", -99) > 25):
            self.last_patron_death = yr
            self.scandal += 4
            was = self.protection
            self.protection *= 0.6
            gift = 800.0 * self.price_index
            self.capital -= gift
            # SAY WHAT IT COST. A play tester read "your patron dies; his heir
            # must be courted afresh", found nothing in `state` that had
            # changed by an amount they could point at, and asked whether the
            # line was decorative. It was not: it takes money, standing and
            # most of your cover, and it should say so, because the answer to
            # it - court somebody, spend on standing - is a decision.
            self.log.append((yr, "your patron dies; his heir must be courted "
                                 "afresh. The courting cost %s denarii, your "
                                 "protection falls from %d%% to %d%%, and you "
                                 "are talked about (scandal +4)"
                             % ("{:,.0f}".format(gift), was * 100,
                                self.protection * 100)))
        if r.random() < 0.03:
            had = max(0.0, self.capital)
            self.lose_capital(0.18)
            # An insula is a Roman tenement block, and a tester playing Han China
            # counted nine fires in the insula district of Luoyang in a hundred
            # years. Every civilization file names its own quarter.
            self.log.append((yr, "fire in the %s: it destroyed %s"
                             % (self.civ.get("fire_quarter", "crowded quarter"),
                                self._loss_words(had))))
        if r.random() < 0.02:
            had = max(0.0, self.capital)
            self.lose_capital(0.10)
            self.log.append((yr, "banditry or a frontier war disrupts supply: "
                                 "it cost you %s" % self._loss_words(had)))

    def _loss_words(self, had_before):
        """"1,240 denarii" or "nothing, you were holding none".

        Every one of these lines used to name the event and stop. A break
        tester's standing complaint across two rounds was that the game
        announces catastrophes and leaves you to diff your own `state` to find
        out whether anything happened.
        """
        lost = had_before - max(0.0, self.capital)
        if lost <= 0.5:
            return "nothing, because you were holding none"
        return "{:,.0f} denarii".format(lost)

    def _catastrophe(self, why):
        self.dead_reason = why
        self.log.append((self.year, "RUN ENDS: " + why))

    # -- driver -------------------------------------------------------------
