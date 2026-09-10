"""What the player can see, and what their work is at risk of losing.

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


class FogMixin:
    def reveal_from(self, k):
        """Completing something teaches you what it leads towards, vaguely."""
        if not getattr(self, "fog", False):
            return
        self.revealed = set(getattr(self, "revealed", set()))
        self.revealed.add(k)
        for other, n in self.nodes.items():
            if k in n.get("pre", []):
                self.revealed.add(other)
            for g in n.get("req_any", []):
                if k in (g.get("options") or {}):
                    self.revealed.add(other)

    def is_visible(self, k, _memo=None):
        """Can the player see this node at all?

        _memo: an optional dict shared across one recursive descent. is_visible
        calls start_reason, and start_reason calls is_visible on every missing
        prerequisite of a node with missing prerequisites - which, on a node
        deep in the tree, is every one of ITS missing prerequisites too. Without
        sharing one memo down that whole call tree, checking visibility of a
        single deep node re-derived the visibility of common ancestors once per
        path to them, which is exponential in the depth of the tree. A profiler
        on `can_start('dynamo')` on norse_900ad under fog counted 12,465 nested
        calls to start_reason from three top-level ones, at 0.45s each; a plain
        `available` call, which checks all ~2,800 nodes this way, did not return
        in 60 seconds. The memo makes one recursive descent O(nodes touched)
        instead of O(paths to them); a fresh dict per outward-facing call (the
        default) keeps it exact - nothing here is cached ACROSS commands, so a
        node built or revealed between one call and the next is seen correctly
        next time.
        """
        if not getattr(self, "fog", False):
            return True
        if k in self.done or k in self.active:
            return True
        if k in getattr(self, "revealed", set()):
            return True
        memo = {} if _memo is None else _memo
        if k in memo:
            return memo[k]
        memo[k] = False        # provisional: the tree is a DAG so this should
                                # never actually be read back, but a cycle must
                                # not recurse forever if one ever sneaks in.
        # anything you could start right now is visible by definition: you can
        # see the work in front of you even if you cannot see past it
        result = self.start_reason(k, _memo=memo)[0]
        memo[k] = result
        return result

    def fog_scrub(self, text):
        """Strip node ids the player has not discovered out of a message."""
        if not text or not getattr(self, "fog", False):
            return text
        out = text
        for k in self.nodes:
            if k in out and not self.is_visible(k):
                out = out.replace(k, "something you have not heard of")
        return out

    def fog_summary(self, k):
        """One sentence. Deliberately not the whole note, and never the unlocks."""
        note = (self.nodes[k].get("note") or "").strip()
        if not note:
            return self.nodes[k]["name"]
        for sep in (". ", "? ", "! "):
            if sep in note:
                note = note.split(sep)[0].strip() + "."
                break
        # Hard cap. A "one sentence" summary that runs to 160 characters, times
        # thirty entries in a list, is most of the reply.
        return note if len(note) <= 110 else note[:107].rstrip(" ,;") + "..."

    def knowledge_risk(self):
        """How exposed your finished work is to being forgotten, and to what.

        A playtester read the guide's warning about the Third Century Crisis,
        then reasonably decided to skip the academies because `path` told them,
        correctly, that no academy is a technical prerequisite of a transistor.
        They then lost 25 technologies in one year, 24 more nine years later,
        and 16 more after that, and rebuilt them while the goal stood still.

        Their complaint is the sharp one: this project's whole thesis is that
        the technical dependency graph is not the real dependency graph, and
        the protocol was exposing only the technical graph. The risk existed
        solely as prose, in a knowledge file, attached to the MITIGATION rather
        than to anything the player could see while deciding. A tool that shows
        you one graph while the guide insists a second one governs you is a tool
        that misleads by omission.

        So the numbers behind the dice are now readable while there is still
        time to act on them.
        """
        if self.has("corpus_dispersed"):   chance, frac, hedge = 0.12, 0.08, "corpus_dispersed"
        elif self.has("corpus_written"):   chance, frac, hedge = 0.45, 0.22, "corpus_written"
        else:                              chance, frac, hedge = 0.80, 0.40, None
        at_risk = sum(1 for k in self.done if self.nodes[k]["tier"] >= 2)
        upcoming = []
        for h in (self.civ.get("hazards") or []):
            yrs = h.get("years") or []
            if not yrs:
                continue
            y0 = yrs[0]
            y1 = yrs[1] if len(yrs) > 1 else yrs[0]
            if self.year > y1:
                continue                      # already survived, or missed
            row = {"name": h.get("name", "hazard"),
                   "years": [y0, y1],
                   "in_progress": y0 <= self.year <= y1,
                   "sacks_a_site": bool(h.get("sack_chance")),
                   "sack_chance_per_year": h.get("sack_chance"),
                   "staff_loss": h.get("staff_loss"),
                   "note": h.get("note")}
            # WHAT YOU CAN DO ABOUT IT. Every hazard here is fightable, and
            # until now nothing said so: testers watched the plague arrive on
            # the year they were told it would and treated it as weather.
            row["what_you_can_do"] = {}
            for kind in ("staff_loss", "sack_chance", "output_factor", "real_erosion"):
                if kind in h or (kind == "sack_chance" and h.get("sack_chance")):
                    row["what_you_can_do"][kind] = self.hazard_advice(kind)
            if "sack_chance" in h:
                row["sack_chance_after_what_you_have_built"] = round(
                    h["sack_chance"] * self.hazard_relief("sack_chance")[0], 4)
            if "staff_loss" in h:
                row["staff_loss_after_what_you_have_built"] = round(
                    h["staff_loss"] * self.hazard_relief("staff_loss")[0], 4)
            upcoming.append(row)
        # Norse hazards do not sack anything, and a playtester watched this
        # advertise a loss risk and recommend a hedge for a full 500 year run in
        # which no sacking could ever occur. Risk you cannot face is not risk.
        can_be_sacked = any(h.get("sacks_a_site") for h in upcoming)
        if not can_be_sacked:
            return {
                "technologies_at_risk": at_risk,
                "loss_chance_if_a_site_is_sacked": round(chance, 2),
                "fraction_lost_when_it_happens": round(frac, 2),
                "expected_technologies_lost_per_sacking": 0.0,
                "hedged_by": hedge,
                "better_hedge_available": None,
                "note": "no remaining hazard for this civilization sacks a site, "
                        "so nothing here is currently at risk of being forgotten",
                "known_hazards_ahead": upcoming,
            }
        return {
            "technologies_at_risk": at_risk,
            "loss_chance_if_a_site_is_sacked": round(chance, 2),
            "fraction_lost_when_it_happens": round(frac, 2),
            "expected_technologies_lost_per_sacking": round(at_risk * chance * frac, 1),
            # Under fog, do not name a node the player has not discovered. A
            # tester was told in `state` that corpus_dispersed would hedge them,
            # asked `why` about it, and was told they had never heard of it.
            # Both replies came from the same program in the same second.
            "hedged_by": hedge if (not getattr(self, "fog", False)
                                   or self.is_visible(hedge or "")) else "nothing yet",
            "better_hedge_available": (
                None if hedge == "corpus_dispersed" else
                ("corpus_dispersed" if not getattr(self, "fog", False)
                 else "there is said to be a way to guard against this; "
                      "you have not found it yet")),
            "known_hazards_ahead": upcoming,
        }

    # Institutions that belong to one named society. Granting them to everyone
    # was the bug; refusing to let anyone else BUILD them would be a worse one,
    # because a founder can perfectly well introduce an aqueduct to Tenochtitlan.
    # This only blocks the free gift.
    # Standing, knowledge and persona are not plant. They carry upkeep because
    # they cost you to maintain, and they cannot be let go to save money the way
    # a mill or a mine can. A playtester went bankrupt and the abandonment
    # mechanic shed `identity_cover`, which is a persona AND a real prerequisite
    # of the goal, and they sat softlocked for 470 years unable to rebuild it.
    # Knowledge cannot be repossessed. Everything else can lapse.
    #
    # This started as a broad category list, added to stop bankruptcy shedding
    # `identity_cover` and softlocking the run. It then caused the opposite
    # problem: it protected patron_local, collegium_licensed, freedman_staff and
    # workshop_first, which between them carried 3,380 denarii of upkeep against
    # 1,501 of revenue, so a ruined run could never stop bleeding and recovery
    # took centuries. Both of those are real. A patronage can lapse and a
    # workshop can close; what you cannot lose is who you are and what you know.
    #
    # A tester watched creditors make the founder forget Newton's laws
    # (sc2_physics_newtons_laws, cat "physics", up 40) - already covered above
    # - and separately watched abstract science and medicine outside pure
    # mathematics go the same way: cell theory, DNA, the phase diagram of
    # iron, none of them a building, all of them carrying real upkeep (40 to
    # 400 denarii, from "keeping up scholarly correspondence" rather than rent)
    # and so all of them ELIGIBLE under the up-exceeds-revenue test that gates
    # both shed_loss_makers and enforce_credit_limit's seizure. "theory" and
    # "knowledge" are what the tree itself calls these categories, which is
    # the same evidence "physics" and "mathematics" were added on: you cannot
    # be made to un-know a thing to balance a ledger, whatever it is filed
    # under. NARROW ON PURPOSE, same lesson as FOREIGN_MARKERS below: most
    # knowledge (tex_drop_spindle, "basic textile technique", among it) costs
    # nothing to keep and was never at risk, needing no protection here at
    # all - see the note on that in never_abandon's caller. This list is only
    # for the knowledge that DOES carry upkeep and would otherwise be shed for
    # it.
    NEVER_ABANDON = {"mathematics", "physics", "method", "notation",
                     "algebra", "geometry", "probability", "analysis",
                     "theory", "knowledge"}

    def never_abandon(self, k):
        """Protected: knowledge, and anything the goal actually needs.

        Keying the softlock guard on the GOAL CLOSURE rather than on a list of
        category names is what makes both halves work. You can let a patron go
        and rebuild him later; you cannot have the game quietly delete a step
        you need and then refuse to fund rebuilding it.
        """
        if self.nodes[k]["cat"] in self.NEVER_ABANDON:
            return True
        if not hasattr(self, "_goal_closure"):
            try:
                self._goal_closure = closure(self.nodes, self.goal)
            except Exception:
                self._goal_closure = set()
        return k in self._goal_closure

    FOREIGN_MARKERS = ("_roman", "_rome", "annona", "insula", "societas",
                       "collegium", "argentarii", "latifundi",
                       # The cursus publicus is the Roman imperial dispatch
                       # relay and the Pharos is one specific Ptolemaic
                       # building at Alexandria. Neither is a generic capability
                       # any society might have, and with no marker of their own
                       # both were being handed free to Han and to the Norse -
                       # the last two of the thirteen Roman-branded grants that
                       # testers kept finding in other people's civilisations.
                       "cursus", "pharos")

    # A Roman masonry arch is a way of laying stone and anyone can learn it. The
    # annona is the Roman state's grain dole and Roman citizenship is a status
    # only Rome can confer, and neither is a thing you can BUILD in Luoyang.
    # A tester played five hundred years of Han China with `citizenship`
    # ("the difference between a governor executing you and Rome hearing you")
    # sitting in their available list the whole time, and called it what it was:
    # unfinished civilization gating rather than a deliberate choice.
    # NARROW, and I made this too wide first time and broke Han China with it.
    # Blocking anything with "collegium" in the name cut the licensed
    # association out of the tree, and with it school_founded, endowment_land,
    # academy_network and both patronage tiers, which is the entire
    # institutional ladder: Han finished 156 of the 168 nodes the transistor
    # needs and then failed for want of eighteen craftsmen it had 320 million
    # denarii to hire. Every society has partnerships, money-lenders and
    # licensed associations under its own names, and the Han even had a grain
    # stabilisation office. What no other society has is Roman citizenship,
    # because only Rome can confer it. That is the whole list.
    # And in the end the list is empty, which is the right answer. My first
    # version blocked six markers and cut Han China off from the whole
    # institutional ladder. Narrowing it to Roman citizenship alone moved the
    # wall one node back, because the licensed association requires legal
    # standing, and a model in which only Romans can have legal standing is
    # worse than the flavour-text problem it was fixing. `citizenship` is now
    # what it always modelled - a status the courts will hear - and every
    # society has one under its own name. What remains civ-specific is which
    # institutions you are GRANTED for free, which FOREIGN_MARKERS still
    # handles: the Han are not handed the annona.
    FOREIGN_INSTITUTIONS = ()
