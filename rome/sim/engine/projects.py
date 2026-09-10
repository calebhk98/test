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
    # ---- knowing how, and actually running it -------------------------------
    # THE DEEPEST THING ANY PLAYTESTER SAID ABOUT THIS MODEL was not a bug
    # report. It was: "you research the finance stuff and instantly make money
    # -- but shouldn't that just unlock the ABILITY to do it? You research
    # loans, now you can give out loans. What if you didn't give out any? And
    # inventing stock market maths without building a stock market, or the
    # assembly line without a factory, is a bit unlikely to pay."
    #
    # That was right, and it went to the middle of the economy. 1,337 of the
    # 2,831 nodes carry revenue and 1,256 of those also carry upkeep, so the
    # tree ALREADY described them as going concerns that cost money to run and
    # pay money back. The only thing missing was the act of choosing to run
    # one. Completing the research paid you whether or not you ever opened the
    # doors.
    #
    # So: `done` is what you KNOW. `operating` is what you RUN. Revenue and
    # upkeep follow `operating`, and nothing else does - the goal, the tree,
    # the prerequisites and the standing you earn all still follow `done`,
    # because knowing how to make a transistor is the achievement and does not
    # require you to sell any.
    def is_venture(self, k):
        """Is this something you could run as a going concern, as opposed to a
        piece of knowledge that simply changes what you can do?"""
        n = self.nodes.get(k)
        if n is None or k in self.granted:
            return False
        return n["rev"] > 0 or n["up"] > 0

    def venture_capex(self, k):
        """What it costs to open the doors, over and above having worked out
        how. Stock, premises, the first year's materials: a fraction of what
        the work itself cost, and never less than a year of its running cost,
        so that a thing which is cheap to invent and expensive to run cannot
        be opened for nothing."""
        n = self.nodes[k]
        return max(self.project_cost(k) * 0.15, n["up"] * 1.0)

    # SUPERVISION, NOT OPERATION. A node's sch/art figures are what it takes to
    # BUILD the thing, and its upkeep already pays the people who run it once
    # built - so charging the full build crew against your own staff for ever
    # would be billing you twice for the same hands, and it measurably was:
    # Rome fell from half its runs reaching the goal to a quarter when the
    # operating cost was the whole build crew. What your own trained people
    # actually owe a going concern is supervision - somebody of yours has to
    # keep an eye on it - and that is a fraction of what it took to build.
    VENTURE_SUPERVISION = 0.25
    # AND A FLOOR FROM ITS SIZE. Charging a fraction of the BUILD crew alone
    # meant that the 19% of concerns which take nobody to build - a bottling
    # shed, a butter trade, a chaff cutter - took nobody to RUN either. A break
    # tester ended a Han run with between 51 and 94 concerns going at once,
    # among them a whaling fleet, a coal seam, an inn and a gambling house,
    # on nought employees and nought in wages, and pointed out that this is
    # precisely what the opening screen promises the model will not do. A
    # going concern needs somebody of yours to keep an eye on it whether or not
    # it was hard to build, and a bigger one needs more: one pair of hands per
    # 1,500 a year of takings, which puts a 130-a-year bottling shed at a tenth
    # of a person and a 12,000-a-year fleet at eight.
    VENTURE_HANDS_PER_REVENUE = 1500.0

    def venture_hands(self, k):
        """(scholars, craftsmen) of your own that running this ties up."""
        n = self.nodes[k]
        f = self.VENTURE_SUPERVISION
        by_size = max(0.0, n["rev"]) / self.VENTURE_HANDS_PER_REVENUE
        return n["sch"] * f, max(n["art"] * f, by_size)

    def venture_staff_used(self):
        """People of your own tied up supervising what you already have open."""
        sch = art = 0.0
        for k in self.operating:
            if k not in self.nodes:
                continue
            a, b = self.venture_hands(k)
            sch += a
            art += b
        return sch, art

    # YOU ARE A PAIR OF HANDS TOO. Requiring staff for every concern, however
    # small, meant a founder with nobody could open nothing at all - not a
    # bottling shed, not an inn - and since revenue now follows what you RUN,
    # that closed the only door out of an empty household: no hands, so no
    # concern; no concern, so no income; no income, so no hands. Rome ran to
    # year 800 with 270 technologies, no craftsmen and one open concern, and
    # Norse sat solvent at 317 in hand with none. One person can keep an eye on
    # one small shop, which is exactly how every one of these fortunes started.
    FOUNDER_IS_WORTH = 1.0

    def venture_staff_free(self):
        """People you could put behind something new. You cannot run fifty
        businesses with three people, and this is the whole of why choosing
        WHICH to run is a decision rather than an accounting formality."""
        sch_used, art_used = self.venture_staff_used()
        own = self.FOUNDER_IS_WORTH if self.founder_alive else 0.0
        return (max(0.0, self.effective_scholars() - sch_used),
                max(0.0, self.artisans + own - art_used))

    def open_venture(self, k, pay=True):
        """Start actually running something you have worked out how to do."""
        if k not in self.nodes:
            return False, "no such node"
        if k not in self.done:
            return False, ("you have not worked out how to do that yet, so there "
                           "is nothing to open")
        if k in self.granted:
            if self._practisable(k):
                # A tester put this best: "my entire un-chosen livelihood is
                # drilling holes in Han skulls, and the game denies it's mine."
                # `money` itemises this as their revenue and `open` called it
                # the society's. Both are half right: the SKILL is the
                # society's, and you are already practising it - which is why
                # it pays, and why there is nothing here to open.
                return False, ("you are already doing that - it is your practice, "
                               "and it is where most of your income comes from. "
                               "It is a skill this society has, not a concern "
                               "you opened, so there is nothing to open and "
                               "nothing to close")
            return False, ("that is something the society has, not a concern of "
                           "yours to run")
        if not self.is_venture(k):
            return False, ("that is knowledge, not a going concern: there is "
                           "nothing to open and nothing it would earn. It has "
                           "already changed what you can build")
        if k in self.operating:
            return False, "you are already running that"
        n = self.nodes[k]
        sch_free, art_free = self.venture_staff_free()
        need_sch, need_art = self.venture_hands(k)
        if need_sch > sch_free + 1e-9 or need_art > art_free + 1e-9:
            return False, ("nobody free to keep an eye on it: it needs %.1f "
                           "scholars and %.1f craftsmen to supervise, and you "
                           "have %.1f and %.1f not already watching something "
                           "else. Hire, teach, or close something."
                           % (need_sch, need_art, sch_free, art_free))
        fee = self.venture_capex(k)
        # A SHOP THAT LOST ITS KEEPER IS NOT A SHOP YOU HAVE TO BUILD AGAIN.
        # Staff attrition runs at 3.5% a year, so a household sitting near the
        # supervision line loses a concern most years and pays the full stock
        # and premises to reopen it - a play tester watched four close at once,
        # every year, and wrote that it cost them hundreds a year and they
        # could never get ahead of it. The premises are still standing and the
        # stock is still on the shelves; what was missing was somebody to
        # watch it. Reopening within a few years costs the difference, not the
        # whole thing.
        _shut = getattr(self, "shut_for_staff", {})
        if k in _shut and self.year - _shut[k] <= self.STAFF_CLOSURE_GRACE:
            fee *= 0.1
        if pay:
            if fee > self.capital + self.credit_limit() * 0.5:
                return False, ("opening it costs %s denarii in stock and premises "
                               "and you have %s"
                               % ("{:,.0f}".format(fee), "{:,.0f}".format(self.capital)))
            self.capital -= fee
        self.operating.add(k)
        self.mothballed.discard(k)
        _shut.pop(k, None)
        self.shut_for_staff = _shut
        return True, ("%s open: it earns %s a year and costs %s a year to run"
                      % (k, "{:,.0f}".format(n["rev"]), "{:,.0f}".format(n["up"])))

    def close_venture(self, k):
        """Stop running it. You keep the knowledge; you stop paying for it and
        stop being paid by it."""
        if k not in self.operating:
            return False, "you are not running that"
        self.operating.discard(k)
        self.mothballed.add(k)
        n = self.nodes[k]
        return True, ("%s closed: you stop paying %s a year and stop earning %s"
                      % (k, "{:,.0f}".format(n["up"]), "{:,.0f}".format(n["rev"])))

    # Years a shop stands with its stock and its lease while you find somebody
    # to keep an eye on it. Past that it really has been given up.
    STAFF_CLOSURE_GRACE = 6

    def close_unstaffed_ventures(self, yr):
        """Shut what nobody is left to watch, dearest to supervise first.

        Not a policy and not an automation you can switch off: it is the same
        rule `open` already applies, applied on the years after the first. A
        shop whose keeper you dismissed is a shop that stops trading, and the
        alternative - which is what the game did - is a fortune of concerns
        running themselves for ever on an empty payroll.
        """
        closed = []
        while self.operating:
            sch_used, art_used = self.venture_staff_used()
            own = self.FOUNDER_IS_WORTH if self.founder_alive else 0.0
            if (sch_used <= self.effective_scholars() + 1e-6
                    and art_used <= self.artisans + own + 1e-6):
                break
            # THE LEAST WORTH KEEPING, not the largest. This picked whichever
            # concern needed the most hands, which is very nearly the same as
            # picking the most PROFITABLE one - a break tester watched it close
            # a 600-a-year hopper wagon twice and keep a concern earning
            # nothing with identical staffing. Shut the one that returns least
            # for the people it ties up.
            worst = min(self.operating,
                        key=lambda k: ((self.nodes[k]["rev"] - self.nodes[k]["up"])
                                       / max(0.01, self.venture_hands(k)[1]),
                                       -self.venture_hands(k)[1]))
            self.operating.discard(worst)
            self.mothballed.add(worst)
            _sfs = getattr(self, "shut_for_staff", {})
            _sfs[worst] = yr
            self.shut_for_staff = _sfs
            closed.append(worst)
        if closed:
            self.log.append((yr, "nobody left to keep an eye on %d concern%s, so "
                                 "%s closed. You still know how; reopen with "
                                 "'open' once you have the people. The premises "
                                 "and the stock stand for a few years yet, so "
                                 "reopening soon costs a tenth of what opening did"
                             % (len(closed), "" if len(closed) == 1 else "s",
                                ", ".join(sorted(closed)[:4])
                                + (" and others" if len(closed) > 4 else ""))))
        return closed

    def auto_open_ventures(self):
        """Open what plainly pays for itself, best margin first, within the
        staff and the money available. Default ON for the optimizer and OFF
        for a player, like every other automation in this game."""
        opened = []
        cands = sorted((k for k in self.done
                        if self.is_venture(k) and k not in self.operating
                        and self.nodes[k]["rev"] > self.nodes[k]["up"]),
                       key=lambda k: -(self.nodes[k]["rev"] - self.nodes[k]["up"]))
        blocked = None
        for k in cands:
            if self.capital <= 0:
                blocked = blocked or (cands[0], "you have no money to open it with")
                break
            ok, why = self.open_venture(k)
            if ok:
                opened.append(k)
            elif blocked is None:
                blocked = (k, why)
        # SAY WHY THE BEST ONE STAYED SHUT. A break tester watched a concern
        # earning 150 a year against 15 of upkeep sit closed for six years with
        # the policy switched on, because auto_open threw away every refusal
        # open_venture handed it. A policy that silently declines is
        # indistinguishable from a policy that is broken.
        if blocked and not opened:
            k, why = blocked
            said = getattr(self, "_said_autoopen", {})
            if self.year - said.get(k, -99) >= 10:
                said[k] = self.year
                self._said_autoopen = said
                self.log.append((self.year,
                                 "%s would earn %s a year against %s of upkeep and "
                                 "is still shut: %s"
                                 % (k, "{:,.0f}".format(self.nodes[k]["rev"]),
                                    "{:,.0f}".format(self.nodes[k]["up"]),
                                    why or "something is in the way")))
        return opened

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
        if self.never_abandon(k) and self.nodes[k]["cat"] in self.NEVER_ABANDON:
            return False, ("that is knowledge, or it is who you are here. "
                           "You cannot un-know a thing to save its upkeep")
        # SHUTTING A SHOP DOWN IS NOT FORGETTING HOW IT WORKED. This used to
        # discard the node from `done`, so closing a loss-maker cost you your
        # place in the tree and the warning had to say "you will have to
        # restore or rebuild it before you can go on". That was a real trap and
        # it only existed because there was nowhere else to put "built but not
        # running". There is now: what you know is `done`, what you run is
        # `operating`, and this touches only the second.
        was_running = k in self.operating
        self.operating.discard(k)
        self.mothballed.add(k)
        if not was_running:
            return True, ("%s was not running, so there was nothing to stop "
                          "paying for. You still know how to do it." % k)
        return True, ("%s shut down; you stop paying %s a year for it and stop "
                      "earning the %s a year it brought in. You still know how "
                      "to do it, and 'restore %s' opens it again"
                      % (k, "{:,.0f}".format(self.nodes[k]["up"]),
                         "{:,.0f}".format(self.nodes[k]["rev"]), k))

    def restore_work(self, k):
        """Bring a mothballed work back. The plant rotted while it stood idle."""
        if k not in getattr(self, "mothballed", set()):
            return False, "you have not shut that down"
        if k not in self.done:
            return False, ('you no longer know how to do that, so there is '
                           'nothing to reopen: build it again with '
                           '{"cmd":"start","id":"%s"}' % k)
        n = self.nodes[k]
        # A FLOOR FROM THE UPKEEP, not only a share of the build cost. Thirty
        # per cent of nothing is nothing, and a node that costs nothing to build
        # while costing 20 a year to keep could be shut down and brought back
        # around the annual tick for free, which made its upkeep optional. A
        # tester did exactly that and the reply read "back in service for 0
        # denarii". The engine already gets this right for mines - `quote mine`
        # says in as many words that mothballing is not free to reverse,
        # because the shaft floods and the crew disperses - so the asymmetry
        # was an oversight rather than a decision. Two years of the upkeep you
        # avoided is what it costs to find the people and the plant again.
        fee = max(self.project_cost(k) * 0.3, n["up"] * 2.0)
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
        # Back in service means back in OPERATION: restore is what a player
        # types to reopen something they shut, so it must put it back on the
        # books rather than leaving it known-but-closed.
        if self.is_venture(k):
            self.operating.add(k)
        return True, ("%s back in service for %s denarii"
                      % (k, "{:,.0f}".format(fee)))

    def bribe(self, amount):
        """Pay your way out of trouble, deliberately, for a stated sum."""
        amount = float(amount)
        if amount <= 0:
            return False, "amount must be greater than zero. Nothing was changed."
        if amount > self.capital:
            return False, "you have %.0f denarii" % self.capital
        before = self.scandal
        prot_before = self.protection
        # DO NOT CHARGE FOR NOTHING. This took the money and then said, in the
        # same breath, "you had no scandal to answer and are already as
        # protected as money can make you, so this bought nothing" - a break
        # tester lost 5,000 to a single mistyped command that way, with no cap
        # and no confirmation. Work out whether it would move anything BEFORE
        # taking the money, and refuse if it would not.
        if before <= 0.0005:
            spent = 0.7 * self.bribes_ytd + amount
            income = max(1.0, self.revenue())
            would = min(0.30, (spent / (income * 0.6)) * self.w["bribability"])
            already = min(0.30, (self.bribes_ytd / (income * 0.6)) * self.w["bribability"])
            if would - already < 0.005:
                return False, ("you have no scandal to answer and you are already "
                               "as protected as money can make you here, so this "
                               "would buy nothing. Nothing was changed.")
        # NEVER TAKE MORE THAN IT CAN SPEND. Both things a bribe buys are
        # bounded: scandal stops at zero and the protection it buys saturates
        # at 0.30. A break tester typed `bribe 1000000`, got exactly the same
        # 0% -> 32% as `bribe 100`, and was left with nothing at all - one
        # command, no cap, no warning, and the run was over. What a man cannot
        # be paid to do more of, he cannot be paid more for.
        bribability = max(1e-9, self.w["bribability"])
        for_scandal = self.scandal * 300.0 / bribability
        income = max(1.0, self.revenue())
        # spent/(income*0.6) * bribability = 0.30, solved for the carried total
        for_protection = max(0.0, (0.30 * income * 0.6) / bribability
                             - 0.7 * self.bribes_ytd)
        useful = max(for_scandal, for_protection)
        refused = 0.0
        if amount > useful + 0.5:
            refused, amount = amount - useful, useful
        self.capital -= amount
        self.bribes_ytd = 0.7 * self.bribes_ytd + amount
        self.scandal = max(0.0, self.scandal - amount / 300.0 * bribability)
        self.update_protection()
        # BOTH THINGS IT BUYS. A break tester spent 500 denarii against a
        # scandal of zero, read "scandal 0.00 -> 0.00", and wrote it down as
        # money silently burned. It was not: bribes_ytd feeds protection, which
        # is what keeps an accusation from being made in the first place. A
        # reply that names only the half that did not move is what made a real
        # effect look like a bug.
        msg = "scandal %.2f -> %.2f for %.0f denarii" % (before, self.scandal, amount)
        if refused > 0.5:
            msg += ("; %s denarii of what you offered was not taken, because "
                    "this is as far as money goes here - you kept it"
                    % "{:,.0f}".format(refused))
        if self.protection > prot_before + 0.0005:
            msg += ("; advocacy and piety bought as well: protection %.2f -> %.2f"
                    % (prot_before, self.protection))
        elif before <= 0.0005:
            msg += ("; you had no scandal to answer and are already as protected "
                    "as money can make you, so this bought nothing")
        return True, msg

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
            # A MOTHBALLED WORK IS NOT FRESH RESEARCH, and it is not "already
            # done" either: you know how, and the plant is gone. `restore` puts
            # it back at a fraction of the cost, and this branch used to sit
            # BELOW the flat "already done" that swallowed it - reachable only
            # in the one state where its advice was wrong.
            if k in getattr(self, "mothballed", set()):
                return False, ("you built this once and let it go; you already "
                               'know how, so restoring it is cheaper than '
                               'starting over: {"cmd":"restore","id":"%s"} for '
                               "about %.0f denarii"
                               % (k, self.project_cost(k) * 0.3))
            return False, "already done"
        if k in self.active:
            return False, "already active"
        # NOT DEAR HERE, IMPOSSIBLE HERE. See SocietyMixin.needs_first.
        _nf, _why_nf = self.needs_first(k)
        if _nf:
            return False, ("%s. Build %s first and this opens with it"
                           % (_why_nf, _nf))
        # A MOTHBALL ENTRY WITHOUT THE KNOWLEDGE IS A STALE ENTRY, and it falls
        # through to the ordinary checks below. Refusing here and sending the
        # player to `restore` - which answers "you no longer know how" - was a
        # deadlock no verb could clear: a play tester lost
        # precision_three_plate to a sack and watched `available` read "0
        # startable now" for a hundred and eighty years, because that node
        # gates the whole precision branch.
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
        # COMPUTED ONLY WHEN IT CAN MATTER. revenue() walks every technology you
        # have, and start_reason is called for every node in the tree, several
        # times over, by can_start and by is_visible under fog. A 45-year
        # fogged Mexica run made 335,276 calls to revenue() from here and spent
        # 38 of its 100 seconds inside them - to compute a surplus that is only
        # read when the household has been insolvent three years or more, which
        # in most runs is never.
        # A CREDIT FREEZE HAS TO APPLY TO THE PLAYER TOO. It was set when the
        # creditors halted your work and then only ever checked in the
        # optimizer's own start loop, so a person at a keyboard could default,
        # be frozen out on paper, and carry on borrowing and starting things
        # regardless. A weird-play tester found the consequence: creditors
        # seize CONCERNS, so a player who opens none can default over and over
        # for nothing but reputation, which regenerates - and building raises
        # reputation, which raises the credit limit. They financed 22
        # technologies with money that did not exist and kept all of it.
        if self.year < getattr(self, "credit_frozen_until", 0):
            return False, ("nobody here will fund new work: your creditors were "
                           "left unpaid and the word is out. They will deal with "
                           "you again in %d, and until then you may finish what "
                           "is running, and pay for something out of money you "
                           "actually hold."
                           % int(self.credit_frozen_until))
        if getattr(self, "insolvent_years", 0) >= 3:
            surplus = (self.revenue() - self.upkeep() - self.living_cost()
                       - self.mine_operating_cost())
            cheap_enough = (self.project_cost(k) <= max(600.0, surplus * 2.0))
        else:
            cheap_enough = True
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
        # CRAFTSMEN YOU HAVE UNDER CONTRACT COUNT TOO. This read self.artisans
        # alone, so work you had already paid an outside shop to do could not
        # satisfy the requirement - and the refusal's own advice was to go and
        # commission it. `commission` could not unblock the gate that
        # recommended commission.
        #
        # It is also what deadlocked an entire civilisation. A Norse run ended
        # at year 1500 with 31,068 denarii, 136 technologies and 1.6 craftsmen,
        # unable to build workshop_first because it needs 2 - while every
        # institution that would raise the staff ceiling (freedman_staff,
        # collegium_licensed, school_founded) needs workshop_first first. You
        # needed two craftsmen to build the place craftsmen work, and could
        # never get to two. The Norse reached the goal in 0% of runs.
        #
        # Buying a jobbing carpenter for a season to raise your workshop is
        # what a person in this position actually did.
        if n["art"] > self.craft_hands_available():
            return False, ("needs %d trained craftsmen, on your staff or under "
                           "contract, and you have %.1f. %s"
                           % (n["art"], self.craft_hands_available(),
                              self._staff_advice("artisans")))
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
        # YOU MAY COMMIT PAST WHAT YOU HOLD, AND NOT PAST WHAT ANYONE WILL LEND.
        # `help economy` states exactly that contract, and nothing enforced the
        # second half. A break tester started all 104 available projects in a
        # fresh England game - 43,914 denarii of work in hand against 400 in
        # cash and a displayed credit limit of 1,503 - and was at -3,672 one
        # step later. Committing to something you cannot yet afford is
        # realistic project accounting and stays; committing to thirty times
        # what anyone will advance you is not a plan, it is an accounting
        # fiction, and the limit the player read a second earlier has to mean
        # something.
        price = self.project_cost(k)
        owed = sum(st.get("cost_left") or 0.0 for st in self.active.values())
        ceiling = max(0.0, self.capital) + self.credit_limit()
        # `self.active and` used to guard this, which exempted the FIRST
        # project from the only affordability test there is. A break tester
        # took tx2_watch_case at 17,415 denarii on 400 in cash and 1,367 of
        # credit because it was their opening move, then found the identical
        # command refused - quoting the shortfall exactly - after they had
        # started a five-denarius project first. Two insolvencies, 1,306 in
        # interest and reputation from 5 to 0.2 later, nothing was built.
        if owed + price > ceiling:
            return False, ("you already owe %s denarii on work in hand; this "
                           "would take it to %s, and between cash and credit "
                           "you can raise %s. Finish or stop something first."
                           % ("{:,.0f}".format(owed), "{:,.0f}".format(owed + price),
                              "{:,.0f}".format(ceiling)))
        n = self.nodes[k]
        # A THING YOU ARE REBUILDING IS NOT A THING SITTING IDLE. If the
        # knowledge was destroyed and only the mothball entry survived, that
        # entry is stale the moment you begin again - and while it stands,
        # `available` hides the node and `restore` claims it can reopen it.
        self.mothballed.discard(k)
        self.active[k] = dict(ph_left=float(n["ph"]), yrs=0.0, spent=0.0,
                              cost_left=price)
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
            _lost = n["_total_cost"] * 0.4 * self.cost_money_factor()
            self.capital -= _lost
            # SAY SO. The roll has always worked - 40 failures in 200 at a
            # stated 20% - and it has never once announced itself: it reset the
            # project and logged nothing, so a break tester watched about 113
            # builds, expected nine failures, found no occurrence of "fail",
            # "abandon" or "lost" anywhere in the output, and concluded the
            # whole mechanic was dead. A cost you cannot see is a cost the
            # player is not paying attention to, which is the same as not
            # charging it.
            # 40, NOT 60. ph_left is set to 0.4 of the FULL hours, so what is
            # to do again is forty per cent of the work; the line said sixty
            # and a break tester who measured the hours reported the stated
            # penalty as never charged. It was charged. The sentence was wrong.
            self.log.append((self.year,
                             "FAILED at %s: it did not work. %d%% of the hours "
                             "are to do again (%s of your own) and %s is gone. "
                             "Attempt %d."
                             % (n["name"], 40, "{:,.0f}".format(n["ph"] * 0.4),
                                "{:,.0f}".format(max(0.0, _lost)),
                                self.failed_attempts[k] + 1)))
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
        # SAY THAT IT IS NOT YET RUNNING. Completing something that could be a
        # going concern no longer starts it earning, and a player who is not
        # told will reasonably conclude the money is broken rather than that
        # they have not opened the doors.
        if self.is_venture(k) and not self.policy.get("auto_open", not self.manual):
            self.log.append((self.year, "completed: %s. You know how; nothing "
                                        "is earning yet - 'open %s' to run it"
                                        % (n["name"], k)))
        else:
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
