"""Starting, stopping, finishing and abandoning a piece of work.

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


class ProjectsMixin:
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
        self._done_changed()
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
        self._done_changed()
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
        # THE ALLOW-LIST IS ROME'S CRAFTS, and it was applied to everybody. A
        # Norse tester was refused a bounty on `sea_skeleton_first` -
        # shipbuilding - by a civilisation whose own profile marks ships as the
        # thing it is best at in the world, and told "a Roman artisan could not
        # recognise success at this". So the list is now a floor, not the whole
        # rule: anything this society is measurably GOOD at (its own cost
        # multipliers say so) can be recognised by its own craftsmen, whatever
        # Rome's craft categories happen to be.
        if n["cat"] in ("glass_optics", "metallurgy", "precision", "power",
                        "agriculture", "information", "instruments"):
            return all(p in self.done for p in n["pre"])
        if self.civ_cost_factor(k) < 0.95:
            return all(p in self.done for p in n["pre"])
        return False

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
        self._done_changed()
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
