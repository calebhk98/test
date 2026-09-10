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
        if self.has("identity_cover"):
            a *= 0.75
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
        # IT SAYS "REDUCES ALL FUTURE SUSPICION" AND IT DID NOTHING OF THE KIND.
        # identity_cover's entire implementation was +1.0 to the reputation
        # floor and +400 to the credit limit, and the suspicion it promised to
        # reduce was a field that no longer exists. Its real value was that it
        # gated a quarter of the tree - which is why every tester concluded
        # they had to have it and assumed it was about illegal activity. It is
        # a persona: books, a house, clothes, a secretary and a reputation for
        # piety. What that buys is that an inexplicable effect coming out of
        # YOUR workshop is read as learning rather than as sorcery.
        if self.has("identity_cover"):      p += 0.12
        if self.has("citizenship"):         p += 0.10
        if self.has("collegium_licensed"):  p += 0.10
        if self.has("endowment_land"):      p += 0.08   # conspicuous benefaction
        if self.has("fin_university") or self.has("school_founded"): p += 0.06
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
        if not self.has("academy_network"):
            helps.append("a wide, dispersed institution is harder to destroy than "
                         "one great man")
        if self.has("patron_imperial"):
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
        if self.has("patron_imperial"):
            h *= 1.5          # nearest the throne, most exposed to its turnover
        # A wide, dispersed institution is harder to destroy than one great man.
        if self.has("academy_network"):
            h *= 0.65
        # AND A CITY GETS USED TO YOU. familiarity is the model's own measure of
        # how unsurprising you have become - it already decays the alarm your
        # work causes - and it was the one defence prominence ignored. Two play
        # testers read "EMINENCE is dangerous above 26 (settles near 39.2)" and
        # correctly described it as the game announcing that a successful run is
        # scheduled to die. A man who has been the great man of the city for
        # ninety years is a fixture, not a novelty; he is still exposed, and he
        # is not what he was in his first decade. Capped at a third off, so this
        # softens the clock without stopping it.
        h *= (1.0 - 0.37 * self.familiarity)
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
        if changed:
            self.log.append((self.year, "%s changes the society: %s"
                             % (self.nodes[k]["name"], ", ".join(sorted(changed)))))

    # FOG OF WAR. Without it the player sees the entire tree from the first
    # minute, including exactly what a transistor needs, which is both a spoiler
    # and a lie about what knowing something feels like. With fog on you see
    # what you have built in full, what you could start next as a one line
    # summary, and nothing at all about where any of it leads.

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
        for node, _share, label in self.HAZARD_COUNTERS.get(kind, ()):
            if node not in self.nodes or node in self.done:
                continue
            want.append((0, node))
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
            out.append({"id": k, "name": self.nodes[k]["name"],
                        "cost": round(self.project_cost(k), 1),
                        "because_it_gives_you": leads_to.get(k),
                        "can_begin_now": bool(ok),
                        "waiting_on": None if ok else why})
            if len(out) >= limit:
                break
        # What you can start comes first: it is the part you can act on today.
        out.sort(key=lambda e: not e["can_begin_now"])
        return out

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
                _hit = []
                if _people_before > 0.05:
                    _hit.append("staff -%d%%" % (loss * 100))
                if cash > 0.5:
                    _hit.append("%s gone with the trade that stopped"
                                % "{:,.0f}".format(cash))
                if not _hit:
                    _hit.append("you had nothing it could take")
                self.log.append((yr, "%s: %s%s"
                                 % (h.get("name", "hazard"), ", ".join(_hit),
                                    " (would have been -%d%%: %s)"
                                    % (h["staff_loss"] * 100, "; ".join(why)) if why else "")))
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
                            for k in drop:
                                self.operating.discard(k)
                                self.done.discard(k)
                            self._done_changed()
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
                    self.log.append((yr, "%s: trade and output fall to %d%% of normal"
                                     % (key, self.output_factor * 100)))
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
        if (r.random() < 0.05 and self.has("patron_local")
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
