"""The JSON protocol a player or an agent speaks.

One object per line in, one object per line out. It explains itself: there is
no protocol document to read, on purpose.
"""
import collections, hashlib, json, math, os, random, re
from collections import defaultdict

from .data import *          # the shared tables and loaders
from .data import (WAGES, ANNUAL_WAGE, TRADE_NOTES, TRADES_ABSENT,
                   TRADE_FAMILY, TECH_EFFECTS, DEFAULTS, SHOCKS,
                   STARTING_KITS, trade_family, closure, critical_path,
                   topo_order, load, load_civ, haversine_km,
                   load_geography, load_resources, money_word,
                   downstream_count, is_downstream)
from .fog import strip_self_play_advice


from .core import Sim


def _agent_end_reason(s):
    """None while the run is live; otherwise why it stopped, for state() and
    to refuse further start/stop/bounty/buy commands once it has."""
    end_year = getattr(s, "end_year", s.cfg["start_year"] + s.cfg["horizon_years"])
    if s.dead_reason:
        return s.dead_reason
    # REACHING THE GOAL IS NOT AN ENDING ANY MORE. A player who won wrote: "I
    # wanted to keep going after the transistor. I had this enormous
    # industrial/research civilization and a giant untouched tree. Stopping
    # immediately after the victory screen would waste the most developed state
    # the player has ever created." They are right, and the tree agrees with
    # them - the goal's prerequisite closure is 168 nodes of 2,833, so a won run
    # has barely touched it. The win is recorded in s.goal_year for ever and the
    # run carries on until the founder dies or the horizon arrives.
    #
    # `run` and `compare` are unaffected: Sim.run() in core.py stops at the goal
    # on its own, which is what every measurement in this repository wants and
    # what keeps a dice-free trial cheap. This is the interactive path only.
    if s.year >= end_year:
        # Under fog there IS no stated goal, so saying the player failed to reach
        # one is incoherent. A tester finished a 500 year run and was told they
        # had missed a goal they were never shown and had no way to set.
        if getattr(s, "fog", False):
            # It said "there was no target to hit", which was false: there is
            # one, `help` names it now, and telling a player at the end that
            # they were never aiming at anything is the same lie the other way
            # round.
            #
            # AND IT NEVER CHECKED s.goal_year AT ALL. A player who reached
            # the goal under fog and kept building (exactly what the block
            # comment above this function describes as the normal case now)
            # still got "did not reach %s" here, unconditionally, because
            # this branch was written before goal completion stopped being
            # an ending and never grew the same s.goal_year check the
            # non-fog branch two lines below it already has. One rule,
            # living in two places, and only one copy got the fix. Found
            # while wiring the ending score's own end_reason field to a
            # save that had, in fact, reached the goal.
            _goal_name = (s.nodes[s.goal]["name"].lower() if s.goal in s.nodes
                         else "the goal")
            if s.goal_year:
                return ("the horizon at %d AD is reached. You reached %s in "
                        "%d AD and kept building for %d years after it."
                        % (end_year, _goal_name, s.goal_year,
                           end_year - s.goal_year))
            return ("the horizon at %d AD is reached. You built %d things of your "
                    "own and did not reach %s."
                    % (end_year, len(s.done - s.granted), _goal_name))
        if s.goal_year:
            return ("the horizon at %d AD is reached. You reached %s in %d AD "
                    "and kept building for %d years after it."
                    % (end_year,
                       s.nodes[s.goal]["name"].lower() if s.goal in s.nodes
                       else "the goal", s.goal_year, end_year - s.goal_year))
        return "ran out of horizon (%d AD) without reaching the goal" % end_year
    return None


def _risk_without_the_essays(kr):
    """knowledge_risk with the hazard prose stripped, for embedding in state."""
    if not isinstance(kr, dict):
        return kr
    out = dict(kr)
    ahead = out.get("known_hazards_ahead")
    if isinstance(ahead, list):
        out["known_hazards_ahead"] = [
            {k: v for k, v in h.items() if k not in ("note", "what_you_can_do")}
            for h in ahead if isinstance(h, dict)]
        out["the_full_account_of_each"] = '{"cmd":"risk"}'
    return out


def _waiting_on(s, nodes, k, st, bill):
    """What is ACTUALLY holding this project up, checked against today."""
    n = nodes[k]
    frac = min(1.0, 1.0 / max(1.0, n["yrs"]))
    # WHAT IS LEFT OF EACH TRADE'S TOTAL, not the flat annual figure the
    # project was once billed whether or not it was still owed. See
    # ProjectsMixin.lab_year_draw (projects.py): hired-labour hours are a
    # total drawn down over the project's life, so near the end of a trade's
    # own balance the true ask is smaller than its nominal pace, and saying
    # "short" against the bigger, already-paid-down figure would name a
    # shortfall that no longer exists.
    lab_left = st.get("lab_left") or n["lab"]
    # TWO DIFFERENT FACTS, NOT ONE. "this society can field 3.5 scribes" and
    # "the scribes here can supply 8,750 but your other work has them booked"
    # used to share one label, "nobody to do the work", and a player with
    # one chemist left after attrition could not tell, in one glance, a
    # shortage no amount of portfolio management would fix from one their
    # OWN other projects were causing by outbidding this one for the same
    # trade - which 'stop' on something else actually answers. Kept as two
    # lists so the message - and _portfolio_constraint's classification of
    # it, below - can tell them apart.
    staffing_short = []
    booked_short = []
    for t, want in (n["lab"] or {}).items():
        need = min(want / max(1.0, n["yrs"]), lab_left.get(t, want))
        if need <= 0:
            continue
        supply = s.hours_you_can_call_on(t)
        have = supply - s.trade_hours_used.get(t, 0.0)
        if have < need:
            # The society's CAPACITY is the durable fact and the one a player
            # can act on; what is left after this year's bookings is noise that
            # changes every step. Say the first, and only mention the second
            # when it is what is actually binding.
            if supply < need:
                staffing_short.append(
                    "%s (wants %.0f hours a year; this society can "
                    "field %.0f at most)" % (t, need, max(0.0, supply)))
            else:
                booked_short.append(
                    "%s (wants %.0f hours a year; the %ss here can "
                    "supply %.0f but your other work has them booked)"
                    % (t, need, t, max(0.0, supply)))
    # BOTH, WHEN BOTH ARE TRUE, NOT JUST THE FIRST ONE FOUND. This loop already
    # knows every trade this project is short on; returning the moment
    # staffing_short had anything in it silently dropped booked_short even
    # when both were populated by the SAME loop above - a project short one
    # trade absolutely and a second only to its own other work looked, from
    # here, exactly like the first shortage was the whole story. A Han
    # playtester who fired a specialist on the strength of a single named
    # blocker found a second, undisplayed one waiting behind it. _portfolio_
    # constraint still classifies this by its leading words, so the merged
    # sentence keeps "nobody to do the work" first and unchanged.
    if staffing_short and booked_short:
        return ("nobody to do the work: " + "; ".join(sorted(staffing_short)[:3])
                + ". Also short, but only because your own other work has it "
                  "booked: " + "; ".join(sorted(booked_short)[:3]))
    if staffing_short:
        return "nobody to do the work: " + "; ".join(sorted(staffing_short)[:3])
    if booked_short:
        # A DIFFERENT SENTENCE FOR A DIFFERENT REMEDY. The society CAN field
        # this trade; it is your own other active work that has it booked.
        # Teaching or hiring more does nothing here - 'portfolio' (the
        # aggregate demand-vs-supply view) or stopping something else does.
        return "trade hours already booked: " + "; ".join(sorted(booked_short)[:3])
    if st["ph_left"] <= 0 and bill > 0.5:
        # MONEY YOU HAVE IS NOT MONEY YOU ARE SHORT OF. step() pays at most one
        # year's instalment - the cost divided by the node's calendar floor -
        # so a ten-year work absorbs a tenth of its bill a year however rich
        # you are. This said "waiting on money" to a play tester holding
        # 73,234,107 denarii against 45,448 still owed, which is not a
        # diagnosis, it is a contradiction. What they were waiting on was the
        # calendar, and nothing anywhere said there was a pace at all.
        per_year = s.project_cost(k) * frac
        if per_year > 0.5 and s.capital + s.credit_limit() * 0.5 >= per_year:
            return ("the pace it can absorb money: at most %s a year goes into "
                    "this (%s still owed, about %.0f more year%s at that rate). "
                    "Money in hand cannot buy it down faster"
                    % ("{:,.0f}".format(per_year), "{:,.0f}".format(bill),
                       math.ceil(bill / per_year),
                       "" if math.ceil(bill / per_year) == 1 else "s"))
        return ("money: %s still owed and this year's instalment of %s is more "
                "than you can raise" % ("{:,.0f}".format(bill),
                                        "{:,.0f}".format(per_year)))
    if st["ph_left"] <= 0:
        return "the calendar"
    # MATERIALS. One economy-wide shortage (charcoal, iron ore, saltpetre...)
    # scales EVERY active project's offered hours down by the same factor -
    # see core.py step() 5, "per = ... * self.throttle" - so a project with
    # founder-hours still to spend and nobody short on trade or money can
    # still be making less of them than the pool alone would suggest, for a
    # reason that is neither staffing, money nor the calendar. Only said when
    # it is genuinely biting (2% is noise); resource_throttle() itself is the
    # one place that number is computed, read here rather than re-derived.
    _thr = s.resource_throttle()
    if _thr < 0.98 and s.binding:
        return ("materials: a shortage of %s has every project (this one "
                "included) running at %d%% of the pace its hours alone "
                "would allow; 'capacity' shows the shortfall"
                % (s.binding, round(_thr * 100)))
    # FOUNDER HOURS - AND WHY THIS MUCH OF THEM. Before this, a project
    # sharing the pool with ten others and one sitting alone both said the
    # identical "your hours", and a player who had already won the game
    # asked for the difference in so many words: "This project is receiving
    # 420 of your 25,000 available directed hours this year because 11
    # active projects are sharing organizational attention." The numbers
    # below are read from step()'s own bookkeeping (core.py, "pool_rank_
    # this_year" and neighbours) - never recomputed - so this sentence and
    # what actually happened cannot disagree.
    _rank = st.get("pool_rank_this_year")
    _count = st.get("pool_active_count_this_year")
    _total = st.get("pool_total_this_year")
    if _rank and _count and _count > 1:
        return ("your hours: priority #%d of %d active projects sharing "
                "this year's %s directed hours; 'portfolio' shows what "
                "each one is getting and why"
                % (_rank, _count, "{:,.0f}".format(_total or 0.0)))
    return "your hours"


# WHAT EACH TRAIT IN self.w ACTUALLY DOES, in the player's own words. Event
# text has always named these fields directly - "corpus_dispersed changes
# the society: w_novelty" (see society.apply_tech_effects) - with no command
# anywhere that would tell a player what w_novelty IS, let alone what it is
# now. Two testers asked for exactly this, in separate rounds, in close to
# the same words. Not civ-specific and not a fog spoiler: these field names
# and what they do are the same across every civilisation, only the starting
# numbers differ, so naming what the mechanic does is not a leak of
# anything the founder in the story would not already understand about their
# own society.
_VALUE_MEANINGS = {
    "adaptation_rate": "how fast this society stops being alarmed by "
                       "something it has now seen for a while",
    "bribability": "how far money moves scandal down, and how much of an "
                   "opposed project's delay a bribe buys off",
    "patronage_weight": "how much protection a patron actually gives you",
    "w_commerce": "how much the state cares about work it can tax or trade on",
    "w_eminence_danger": "how dangerous standing out is here - autocracies "
                         "run this high",
    "w_information": "how much the state cares about work that spreads ideas",
    "w_labour_saving": "negative here means a machine that displaces hands "
                       "is itself alarming, on top of anything else about it",
    "w_magic_fear": "how alarmed this society is by anything inexplicable "
                    "or showy",
    "w_military": "how much the state cares about work it could use militarily",
    "w_novelty": "negative here means novelty itself is alarming, whatever "
                "the work actually is",
    "w_religious_rigidity": "how threatening anything religion-adjacent looks",
}


def _agent_values(s):
    """What this society actually believes, as numbers you can look up.

    These move over the course of a run - printing raises literacy, the
    scientific method lowers the fear of the inexplicable - and the only
    record of a move has ever been a completion's "changes the society:
    w_novelty, w_commerce" line, naming fields with no way to see what they
    are or what they are now. This is that way.
    """
    w = dict(getattr(s, "w", {}) or {})
    rows = [{"field": f, "value": round(w[f], 3), "means": _VALUE_MEANINGS.get(f)}
            for f in sorted(w) if not f.startswith("_")]
    return {"ok": True, "values": rows,
            "note": "a completion's own 'changes the society' line says which "
                    "of these moved and when."}


def render_values(out):
    L = ["WHAT THIS SOCIETY BELIEVES"]
    for r in out.get("values") or []:
        L.append("  %-22s %7s  %s" % (r["field"], _factor(r["value"]),
                                      r.get("means") or ""))
    if out.get("note"):
        L.append("")
        L.append(_wrap(out["note"]))
    return "\n".join(L)


# ---------------------------------------------------------------------------
# THE INDUSTRIAL DASHBOARD. A player who had already won the game asked for
# one command that answers "what physical capability does my society
# currently have, not just what I know how to build" - tonnages and
# kilowatts, not tech names. Every figure below reads a function economy.py
# (or this file) already computes for some OTHER purpose: resource_throttle's
# own supply-vs-demand arithmetic, mine_yield_t, hours_you_can_call_on,
# _agent_state's own per-project accounting. Nothing here is a second copy of
# a number computed somewhere else - see _power_status's own note for the one
# place that would have needed one and does not get it: the tree narrates
# power capability in kilowatts and megawatts (node names, notes) but nothing
# in the engine ever turns that into a tracked wattage, so this reports the
# capability gate honestly instead of inventing a figure to match the prose.
# ---------------------------------------------------------------------------

def _material_capacity_rows(s):
    """Capacity, demand and surplus/shortfall for every material currently in
    demand, or in which you have sunk your own capacity even if nothing
    currently needs it - the same own-supply-plus-market arithmetic
    resource_throttle() already runs to find the ONE worst-binding material
    (see economy.py's _own_material_supply/_material_market_tonnes), laid
    out for every material instead of only the worst.
    """
    demand = s.annual_material_demand()
    by_tag = s._demand_by_supply_tag(demand)
    rows = {}
    for (emp_key, tag), need in by_tag.items():
        own = s._own_material_supply(tag)
        market = s._material_market_tonnes(emp_key)
        rows[emp_key] = {
            "material": emp_key,
            "capacity_t_per_yr": round(own + market, 1),
            "your_own_capacity_t_per_yr": round(own, 1),
            "market_capacity_t_per_yr": round(market, 1),
            "demand_t_per_yr": round(need, 1),
            "surplus_t_per_yr": round(own + market - need, 1)}
    # OWNED CAPACITY WITH NO CURRENT DEMAND. A mine you sank and no longer
    # need does not simply vanish from what you could still supply.
    for mat in s.mine_capacity:
        if mat in rows:
            continue
        own = s._own_material_supply("mine:" + mat)
        market = s._material_market_tonnes(mat)
        rows[mat] = {
            "material": mat,
            "capacity_t_per_yr": round(own + market, 1),
            "your_own_capacity_t_per_yr": round(own, 1),
            "market_capacity_t_per_yr": round(market, 1),
            "demand_t_per_yr": 0.0,
            "surplus_t_per_yr": round(own + market, 1)}
    for mat, r in rows.items():
        if mat in s.mine_capacity:
            note = s.mine_depletion_note(mat)
            if note:
                r["yield_note"] = note
    # WORST SHORTFALL FIRST - the bottleneck a player actually has to reason
    # about belongs at the top, not buried alphabetically.
    return sorted(rows.values(), key=lambda r: (r["surplus_t_per_yr"], -r["demand_t_per_yr"]))


# THE POWER LADDER, in the order the tree actually builds it. Each entry is a
# real capability node; the label is the tree's OWN description of its scale
# (node name/note), not a number this file made up - see _power_status.
_POWER_LADDER = (
    ("cap_power_muscle", "muscle and animal power"),
    ("cap_power_water", "water power, tens of kW on one shaft"),
    ("cap_power_steam", "portable steam power, hundreds of kW"),
    ("cap_power_electric", "local electric power, kW scale (workshop-scale)"),
    ("cap_power_grid", "grid electric power, MW scale (central generation)"))


def _power_status(s, nodes):
    """What this society can generate, transmit and draw, in real kilowatts,
    and - once electrification has actually begun for THIS player - which
    visible projects are waiting on workshop-scale power versus the grid.

    REAL FIGURES NOW, not only a capability gate: economy.py's
    generation_breakdown_kw()/_electricity_demand_kw() (see that file's own
    long comment on where every number in them came from, and where the
    tree's own notes were too vague to give one) turn the ladder's names -
    "kW scale", "tens of kW", "hundreds of kW", "MW scale" - into tracked
    watts, the same way resource_throttle() already tracks iron and copper.
    This screen reads those functions; it computes nothing of its own.

    FOG: a rung is named only once it is visible (built, active, or
    revealed) - the ladder itself is not spoiled by naming an unbuilt lower
    rung, since is_visible already governs which rungs qualify. The
    generation/demand FIGURES are safe to show even so: both functions sum
    only over self.done/self.active, and is_visible(k) is unconditionally
    true for anything in either set (fog.py's own definition) - a number is
    never built from a node the player has not already built or started
    themselves. The workshop-versus-grid split on projects goes further: it
    distinguishes the two scales for a project only once the player has
    themselves discovered BOTH cap_power_electric and, separately,
    cap_power_grid - naming "this needs the grid" before the player has ever
    heard of a grid would hand over the existence of the next tier exactly
    the way `bounty` once handed over power_grid's id by naming a raw
    prerequisite; here nothing is named until it is not a prerequisite the
    player would be seeing for the first time.
    """
    tiers = []
    highest = None
    for nid, label in _POWER_LADDER:
        if nid not in nodes or not s.is_visible(nid):
            continue
        built = s.has(nid)
        tiers.append({"capability": label, "id": nid, "built": built})
        if built:
            highest = label
    out = {
        "power_tiers_you_have_discovered": tiers or "none yet",
        "highest_you_have_built": highest,
    }
    if not tiers:
        out["note"] = ("nothing discovered yet: no generation, no demand.")
        return out
    gen = s.generation_breakdown_kw()
    demand_kw = s._electricity_demand_kw()
    total_kw = gen["total_kw"]
    out["generation_kw"] = {"local_workshop_scale": round(gen["local_kw"], 1),
                             "grid_scale": round(gen["grid_kw"], 1),
                             "total": round(total_kw, 1)}
    out["demand_kw"] = round(demand_kw, 1)
    out["reserve_margin"] = (None if demand_kw <= 1e-9 else
                             round((total_kw - demand_kw) / demand_kw, 3))
    out["transmission_capacity_kw"] = round(gen["transmission_kw"], 1)
    mech = gen["mechanical_kw"]
    if mech.get("water") or mech.get("steam"):
        out["mechanical_shaft_power_kw"] = {k: round(v, 1)
                                            for k, v in sorted(mech.items()) if v}
    if s.binding == "electricity":
        out["electricity_is_the_binding_constraint"] = True
        out["throttle"] = round(s.throttle, 3)
    out["note"] = ("generation and demand are both averaged continuous "
                   "kilowatts, the same annual-flow convention every other "
                   "tracked resource in this engine uses - not an "
                   "instantaneous or peak reading.")
    elec_known = s.is_visible("cap_power_electric")
    grid_known = s.is_visible("cap_power_grid")
    if elec_known:
        workshop_scale, grid_scale = [], []
        for k, n in nodes.items():
            if k in s.done or not s.is_visible(k):
                continue
            pre = n.get("pre") or []
            if grid_known and not s.has("cap_power_grid") and "cap_power_grid" in pre:
                grid_scale.append(k)
            elif not s.has("cap_power_electric") and "cap_power_electric" in pre:
                workshop_scale.append(k)
        if workshop_scale:
            out["waiting_on_workshop_scale_power"] = sorted(workshop_scale)
        if grid_scale:
            out["waiting_on_grid_scale_power"] = sorted(grid_scale)
    return out


def _agent_mines(s):
    """A list of your own mines, ONE ROW PER WORKING: the material it
    raises, its rated capacity, its actual output after ITS OWN depletion
    and current technology, what it costs to run, its utilisation, the
    year it was commissioned, and whether it is actually supplying any of
    this year's demand or merely standing there being paid for. See the
    `mines`/`workings` dispatch below and _agent_capacity, which both call
    this rather than keeping two copies of the same arithmetic.

    A player who had already won the game asked for exactly this: "a mines
    command showing each mine, resource key, rated capacity, actual
    output, operating cost, utilization, commissioning year, and whether
    it is currently supplying anything would have prevented several
    confusing decisions." Before economy.py's self.mines existed there was
    no "it" to ask any of this about - mine_capacity was one float per
    material, so a mine had no individual identity, no commissioning year,
    and no per-working depletion; a shaft opened last year read as
    depleted as one opened three centuries earlier because they were the
    same number. This does not fabricate what that model never recorded:
    a working carried over from a save written before this existed has
    "commissioned_year": None, shown as "unknown" (see load_state's own
    migration comment), never a guessed year.

    Separately, auto_mine quietly took 353,039 a year against 467,227 of
    revenue for a play tester, and there was no command anywhere that named
    what they owned or what it cost; two `close` calls took their net from
    -61,884 to +291,156. The verbs to sink one and to shut one both
    existed; nothing showed you the books.
    """
    dem = s.annual_material_demand()
    # copper_wire_kg/wire_drawn_kg and gold_kg: economy.py's MATERIAL_CHECKS
    # now tracks these against the same copper/gold supply this row is
    # about (see that table's own comment); this local key map has to
    # agree or "you actually need" would silently exclude what 36
    # electrical nodes and a central bank draw.
    _keys = {"coal": ("coal_kg",), "iron": ("iron_bar_kg", "iron_ore_kg"),
             "copper": ("copper_kg", "copper_wire_kg", "wire_drawn_kg"),
             "lead": ("lead_kg",),
             "tin": ("tin_kg",), "silver": ("silver_kg",),
             "gold": ("gold_kg",)}
    # GENERALISED (COMMODITY_DYNAMISM.md, economy.py's open_mine() is no
    # longer limited to these seven names): for a mine in a material
    # outside the curated list above, the material key IS its own demand
    # key (see economy.py's _material_tag(), same convention), so a
    # default of "look up the key by its own name" covers it rather than
    # silently reporting 0 tonnes needed for anything not in `_keys`.
    rows = []
    # PENDING WORKINGS COUNT. A shaft takes years to come into production
    # and is paid for the moment you sink it, so a player who has just
    # bought one and types `mines` must not be told they own none. Not yet
    # a working - it has no commissioning year until commission_mines()
    # actually makes it one - so these stay grouped by material, as before.
    _pending = {}
    for _t in sorted(getattr(s, "mine_tranches", [])):
        _m, _amt, _ready = _t[0], _t[1], _t[2]
        _pending.setdefault(_m, [0.0, _ready])
        _pending[_m][0] += _amt
        _pending[_m][1] = min(_pending[_m][1], _ready)
    # GROUPED BY MATERIAL, ordered by commissioning year within it, so
    # several workings of the same seam read as a chronology, not a jumble.
    # self.mines is a list (append/commission order), not a set, so the
    # groupby itself needs no sorted() to be deterministic across hash
    # seeds - only the final row order does, hence the explicit sort key.
    by_mat = {}
    for w in getattr(s, "mines", ()):
        by_mat.setdefault(w["material"], []).append(w)
    for m in sorted(by_mat):
        workings = by_mat[m]
        want = sum(dem.get(kk, 0.0) for kk in _keys.get(m, (m,)))
        total_rated = sum(w["capacity"] for w in workings)
        for w in sorted(workings, key=lambda w: (
                w.get("opened_year") if w.get("opened_year") is not None
                else -1)):
            # ACTUAL yield, not the nominal tonnage sunk: THIS working's
            # own depletion (the easy ore going, aged from its own
            # commissioning year - see economy.py's class comment above
            # _workings_of) and current mining technology both move this
            # away from rated capacity, and a player whose coal yield has
            # halved over eighty years has to be able to see that here,
            # not just infer it from a lower revenue somewhere else.
            actual = s.mine_yield_t_for(w)
            # UTILISATION: rated capacity against what is really being
            # drawn - the question the player actually asked. Demand for
            # this material is shared across its workings in proportion to
            # their own rated capacity (the model has no finer-grained way
            # to say which working feeds which furnace); what a working
            # can actually be drawn on for is capped by its OWN yield, so
            # a fully depleted working shows low utilisation even when
            # every tonne it can still raise is being used, and an unused
            # one shows 0% however healthy its seam is - exactly the
            # distinction between a real supply and an economic asset the
            # player asked to see.
            share = want * (w["capacity"] / total_rated) if total_rated > 0 else 0.0
            drawn = min(share, actual)
            util = (drawn / w["capacity"]) if w["capacity"] > 0 else 0.0
            rows.append({
                "material": m,
                "commissioned_year": w.get("opened_year") if w.get("opened_year")
                                     is not None else "unknown (from a save "
                                     "written before per-working tracking "
                                     "existed)",
                "rated_capacity_t_per_yr": round(w["capacity"], 2),
                "actual_output_t_per_yr": round(actual, 2),
                "material_demand_t_per_yr": round(want, 2),
                "costs_you_a_year": round(s.mine_operating_cost_for(w), 1),
                "utilization": ("%d%%" % round(100.0 * util))
                               if w["capacity"] > 0 else "-",
                # WHETHER IT IS ACTUALLY SUPPLYING ANYTHING, as a plain flag,
                # not only as a percentage a reader has to interpret. A
                # tester's own question was exactly this: does the game
                # count a mine as real supply, or only as an economic asset
                # sitting on the books?
                "actually_supplying_demand": bool(drawn > 1e-9),
                "yield_note": s.mine_depletion_note_for(w),
                "shut_it_with": "close %s" % m})
    for m, (amt, ready) in sorted(_pending.items()):
        rows.append({
            "material": m,
            "commissioned_year": "pending",
            "rated_capacity_t_per_yr": 0.0,
            "actual_output_t_per_yr": 0.0,
            "material_demand_t_per_yr":
                round(sum(dem.get(kk, 0.0) for kk in _keys.get(m, (m,))), 2),
            "costs_you_a_year": 0.0,
            "utilization": "sinking",
            "actually_supplying_demand": False,
            "ready_in": ready,
            "tonnes_a_year_when_it_is_ready": round(amt, 2),
            "shut_it_with": "close %s" % m})
    return {"ok": True,
            "mines_you_own": rows or "none",
            "they_cost_you_a_year_in_all": round(s.mine_operating_cost(), 1),
            "your_revenue_is": round(s.revenue(), 1),
            "still_being_sunk": {m: v[1] for m, v in sorted(_pending.items())},
            "note": "Workings are charged every year they stand, whether or "
                    "not you use what they raise. One you no longer need is "
                    "money going out for nothing: 'close <material>'. "
                    "Reopening means sinking it again. 'close' shuts every "
                    "working of that material at once - there is no way to "
                    "shut just one of several workings in the same seam."}


def _portfolio_constraint(waiting):
    """Which of the SIX things a project could be waiting on, from the
    exact sentence _waiting_on already builds for `state` - a second
    classifier reading the same words back, not a second guess at what is
    actually binding.

    Used to be five, with "nobody to do the work" covering both an absolute
    staffing shortage and a trade your OWN other active work has booked -
    two different facts with two different remedies, now two different
    buckets (see _waiting_on's own comment on the split). "materials" is new
    outright: a project can be short of nothing - staff, money, trade,
    calendar - and still be making less progress than its hours alone would
    buy, because the whole economy is throttled by one scarce input.
    """
    if not isinstance(waiting, str):
        return "unclear"
    if waiting.startswith("nobody to do the work"):
        return "staffing"
    if waiting.startswith("trade hours already booked"):
        return "trade_hours"
    if waiting.startswith("materials:"):
        return "materials"
    if waiting.startswith("money") or "pace it can absorb money" in waiting:
        return "money"
    if waiting == "the calendar":
        return "calendar"
    if waiting == "your hours" or waiting.startswith("your hours:"):
        return "founder_hours"
    return "unclear"


# ORDER A PLAYER SHOULD TRIAGE IN: the things only they can fix (staffing,
# trade hours, money) before the things that are just the calendar or their
# own queue running its course. "materials" sits with the other three
# actionable causes - buy the woodland, sink the mine - ahead of the two
# that are not really problems, only pace.
_PORTFOLIO_ORDER = {"staffing": 0, "trade_hours": 1, "materials": 2,
                    "money": 3, "founder_hours": 4, "calendar": 5,
                    "unclear": 6}


def _portfolio_rows(nodes, active_out):
    """Every project you have in hand, grouped by what is actually
    constraining it, reusing _agent_state's own per-project accounting
    (waiting_on, founder-hours, risk) rather than a second copy of it - the
    same active dict `state` already returns, resorted so several long
    clocks running at once read as one screen instead of requiring a player
    to hold each one in their head.
    """
    rows = []
    for k, a in active_out.items():
        n = nodes[k]
        constraint = _portfolio_constraint(a.get("waiting_on"))
        row = {
            "id": k, "name": a["name"], "constraint": constraint,
            "waiting_on": a.get("waiting_on"),
            "founder_hours_left": a.get("founder_hours_left"),
            "founder_hours_total": a.get("founder_hours_total"),
            # READ, NOT RECOMPUTED. These four come straight off the same
            # st dict step()'s own allocator loop wrote them to (core.py,
            # "pool_total_this_year" and neighbours) - the actual share this
            # project got this year, and why, never a second guess at it
            # that could end up disagreeing with what was actually applied.
            "hours_offered_this_year": a.get("hours_offered_this_year"),
            "hours_effective_this_year": a.get("hours_effective_this_year"),
            "pool_rank_this_year": a.get("pool_rank_this_year"),
            "pool_active_count_this_year": a.get("pool_active_count_this_year"),
            "pool_total_this_year": a.get("pool_total_this_year"),
            "years_in_progress": a.get("years_in_progress"),
            "calendar_years_left": round(
                max(0.0, float(n["yrs"]) - float(a.get("years_in_progress") or 0.0)), 1),
            "still_to_pay": a.get("still_to_pay"),
            "chance_of_failure": n.get("risk") or None,
        }
        if "will_be_abandoned_in_years" in a:
            row["will_be_abandoned_in_years"] = a["will_be_abandoned_in_years"]
            row["because_nobody_here_can"] = a.get("because_nobody_here_can")
        rows.append(row)
    rows.sort(key=lambda r: (_PORTFOLIO_ORDER.get(r["constraint"], 9),
                             -(r["founder_hours_left"] or 0.0)))
    return rows


def _spare_capacity(s, state_out):
    """Founder-hours, staff and cash flow not currently spoken for: enough
    to teach parallelism without saying what to build with it. Every figure
    here is hours_you_can_call_on(t)/trade_hours_used - the same pair
    _waiting_on already reads per project - summed by trade family instead
    of read one project at a time, plus the spending figures `money`/`state`
    already compute for their own screens.
    """
    families = {}
    for t in WAGES:
        if not s.trade_available(t):
            continue
        fam = trade_family(t)
        d = families.setdefault(fam, [0.0, 0.0])
        supply = s.hours_you_can_call_on(t)
        used = min(supply, s.trade_hours_used.get(t, 0.0))
        d[0] += supply
        d[1] += used
    rows = []
    for fam, (supply, used) in sorted(families.items()):
        spare = max(0.0, supply - used)
        if supply <= 0:
            continue
        rows.append({"trade_family": fam,
                     "spare_hours_this_year": round(spare, 0),
                     "spare_people_equivalent": round(
                         spare / s.HOURS_PER_PERSON_YEAR, 1)})
    return {
        "founder_hours_available": state_out.get("founder_hours_available"),
        "free_hours_going_unused": state_out.get("free_hours_going_unused"),
        "spare_by_trade_family": rows or "none",
        "you_could_raise_right_now": round(s.spending_power("buy"), 1),
        "credit_limit": round(s.credit_limit(), 1),
        "standing_net_per_year": state_out.get("net_per_year"),
        "note": "standing net per year is this household's own ordinary-year "
                "surplus or deficit before this year's project spend - "
                "roughly how much more annual project spend you could "
                "sustain going forward if it is positive, not cash sitting "
                "idle today. 'money' shows how it is made up.",
    }


def _trade_demand_rows(s):
    """trade_demand_vs_supply (projects.py), with the family a player
    actually hires by attached and sorted worst-first - the aggregate
    picture a player needs BEFORE committing to one more project that
    shares a trade already oversubscribed: "the game reported 10,000-25,000
    founder-hours free, while a project requiring only hundreds of hours
    advanced very slowly because of the active portfolio" was never a
    founder-hours problem at all in the run that said it; it was this.
    """
    rows = []
    for t, d in s.trade_demand_vs_supply().items():
        rows.append({
            "trade": t, "trade_family": trade_family(t),
            "demand_hours_this_year": d["demand_hours_this_year"],
            "supply_hours_this_year": d["supply_hours_this_year"],
            "oversubscribed": d["oversubscribed"],
            "projects_drawing_on_it": d["projects_drawing_on_it"],
        })
    rows.sort(key=lambda r: (not r["oversubscribed"],
                             r["supply_hours_this_year"] - r["demand_hours_this_year"]))
    return rows


def _agent_portfolio(s, nodes, cmd=None):
    """The screen a player who had already won the game asked for four
    separate times in one run: what every active project is actually
    getting this year, why, and whether the portfolio as a whole is asking
    its trades for more than they can give - all of it read back from the
    allocator's own bookkeeping (core.py step(), projects.py trade_draw_
    plan/trade_demand_vs_supply), never recomputed here.
    """
    state_out = _agent_state(s, nodes)
    active_out = state_out.get("active") or {}
    rows = _portfolio_rows(nodes, active_out)
    pool_total = state_out.get("founder_hours_available")
    count = len(active_out)
    return {
        "ok": True,
        "active_project_count": count,
        "founder_hours_available_this_year": pool_total,
        "free_hours_going_unused": state_out.get("free_hours_going_unused"),
        "projects": rows,
        "trade_hours_demand_vs_supply": _trade_demand_rows(s),
        "note": ("%d active project%s %s sharing this year's %s directed "
                "hours; each row above shows what IT got and why. "
                "'trade_hours_demand_vs_supply' is the same question for "
                "every hired trade your portfolio draws on, summed across "
                "all of them, before you commit to one more."
                % (count, "" if count == 1 else "s",
                   "is" if count == 1 else "are",
                   "{:,.0f}".format(pool_total or 0.0))) if count else
                "nothing active yet - 'available' or 'stuck' says what you "
                "could begin today.",
    }


def _agent_capacity(s, nodes, cmd=None):
    """The industrial dashboard: physical capability, not just known
    technologies. One underlying summary for resources, power, mines, the
    project portfolio and spare capacity, because a player reasoning about
    a bottleneck needs all five in the same place, not six commands to
    cross-reference by hand.
    """
    state_out = _agent_state(s, nodes)
    active_out = state_out.get("active") or {}
    return {
        "ok": True,
        "resources": _material_capacity_rows(s),
        "power": _power_status(s, nodes),
        "mines": _agent_mines(s),
        "portfolio": _portfolio_rows(nodes, active_out),
        "spare_capacity": _spare_capacity(s, state_out),
        "resource_throttle": state_out.get("resource_throttle"),
        "throttle_binding": state_out.get("throttle_binding"),
        "note": "'mines' gives the same mine rows with more room; 'labour' "
                "gives any one trade in full; 'money' gives the ledger this "
                "reads its cash figures from.",
    }


def render_capacity(out):
    L = ["THE INDUSTRIAL DASHBOARD"]
    res = out.get("resources") or []
    if res:
        L.append("")
        L.append("  RESOURCES")
        L.append("  %-14s %12s %12s %12s" % ("MATERIAL", "CAPACITY/YR",
                                             "DEMAND/YR", "SURPLUS/YR"))
        for r in res:
            L.append("  %-14s %12s %12s %12s%s"
                     % (r["material"], _fmt_num(r["capacity_t_per_yr"]),
                        _fmt_num(r["demand_t_per_yr"]),
                        _fmt_num(r["surplus_t_per_yr"]),
                        "  SHORT" if r["surplus_t_per_yr"] < 0 else ""))
            if r.get("yield_note"):
                L.append(_wrap(r["yield_note"], indent="      "))
    pw = out.get("power") or {}
    L.append("")
    L.append("  POWER")
    tiers = pw.get("power_tiers_you_have_discovered")
    if isinstance(tiers, list) and tiers:
        for t in tiers:
            L.append("    [%s] %s" % ("x" if t["built"] else " ", t["capability"]))
    else:
        L.append("    nothing discovered yet")
    gen = pw.get("generation_kw")
    if gen:
        L.append("    generation: %s kW local + %s kW grid = %s kW total"
                 % (_fmt_num(gen["local_workshop_scale"]), _fmt_num(gen["grid_scale"]),
                    _fmt_num(gen["total"])))
        L.append("    demand: %s kW" % _fmt_num(pw.get("demand_kw")))
        rm = pw.get("reserve_margin")
        L.append("    reserve margin: %s"
                 % ("no demand yet" if rm is None else _pct(rm) if rm >= 0
                    else "SHORT by " + _pct(-rm)))
        if pw.get("transmission_capacity_kw"):
            L.append("    grid transmission capacity: %s kW"
                     % _fmt_num(pw["transmission_capacity_kw"]))
        if pw.get("mechanical_shaft_power_kw"):
            L.append("    mechanical shaft power available: "
                     + ", ".join("%s %s kW" % (k, _fmt_num(v))
                                 for k, v in pw["mechanical_shaft_power_kw"].items()))
        if pw.get("electricity_is_the_binding_constraint"):
            L.append("    ELECTRICITY IS THE BINDING CONSTRAINT this year "
                     "(throttle %s)" % _pct(pw.get("throttle")))
    if pw.get("waiting_on_workshop_scale_power"):
        L.append("    waiting on workshop-scale power: "
                 + ", ".join(pw["waiting_on_workshop_scale_power"]))
    if pw.get("waiting_on_grid_scale_power"):
        L.append("    waiting on the grid: " + ", ".join(pw["waiting_on_grid_scale_power"]))
    if pw.get("note"):
        L.append(_wrap(pw["note"], indent="    "))
    mines = (out.get("mines") or {}).get("mines_you_own")
    L.append("")
    L.append("  MINES  (see 'mines' for the full table)")
    if isinstance(mines, list) and mines:
        for r in mines:
            yr = r.get("commissioned_year")
            yr_s = "%d" % yr if isinstance(yr, (int, float)) else str(yr)
            L.append("    %-10s (since %6s) raises %8s of %8s needed  "
                     "supplying: %s"
                     % (r["material"], yr_s,
                        _fmt_num(r.get("actual_output_t_per_yr")),
                        _fmt_num(r.get("material_demand_t_per_yr")),
                        "yes" if r.get("actually_supplying_demand") else "no"))
    else:
        L.append("    none")
    port = out.get("portfolio") or []
    L.append("")
    L.append("  PROJECT PORTFOLIO")
    if port:
        for r in port:
            L.append("    %-28s [%s]  %s hrs left, %s yrs left, risk %s"
                     % (r["name"], r["constraint"].replace("_", " "),
                        _fmt_num(r["founder_hours_left"]),
                        _fmt_num(r["calendar_years_left"]), _pct(r["chance_of_failure"])))
            L.append(_wrap("waiting on: " + str(r["waiting_on"]), indent="      "))
    else:
        L.append("    nothing in hand")
    sp = out.get("spare_capacity") or {}
    L.append("")
    L.append("  SPARE CAPACITY")
    L.append("    founder-hours free this year: %s"
             % _fmt_num(sp.get("founder_hours_available")))
    fam = sp.get("spare_by_trade_family")
    if isinstance(fam, list) and fam:
        L.append("    " + "; ".join("%s: %s free (%s hrs)"
                                    % (f["trade_family"], _fmt_num(f["spare_people_equivalent"]),
                                       _fmt_num(f["spare_hours_this_year"])) for f in fam))
    L.append("    you could raise %s now; %s standing net/yr"
             % (_fmt_num(sp.get("you_could_raise_right_now")),
                _fmt_num(sp.get("standing_net_per_year"))))
    if sp.get("free_hours_going_unused"):
        L.append(_wrap("  " + sp["free_hours_going_unused"]))
    return "\n".join(L)


def render_portfolio(out):
    L = ["PROJECT PORTFOLIO"]
    rows = out.get("projects") or []
    L.append("  %d active project%s, %s founder-hours available this year"
             % (out.get("active_project_count") or 0,
                "" if out.get("active_project_count") == 1 else "s",
                _fmt_num(out.get("founder_hours_available_this_year"))))
    if rows:
        for r in rows:
            _rank = r.get("pool_rank_this_year")
            _count = r.get("pool_active_count_this_year")
            L.append("")
            L.append("  %-28s [%s]" % (r["name"], r["constraint"].replace("_", " ")))
            L.append("    this year: %s offered, %s effective, of %s hrs "
                     "total to go%s"
                     % (_fmt_num(r.get("hours_offered_this_year")),
                        _fmt_num(r.get("hours_effective_this_year")),
                        _fmt_num(r.get("founder_hours_total")),
                        ("  (priority #%s of %s active)" % (_rank, _count))
                        if _rank and _count else ""))
            L.append(_wrap("waiting on: " + str(r.get("waiting_on")), indent="      "))
    else:
        L.append("  nothing in hand - 'available' or 'stuck' says what you "
                 "could begin today")
    trows = out.get("trade_hours_demand_vs_supply") or []
    L.append("")
    L.append("  TRADE-HOUR DEMAND VS SUPPLY THIS YEAR")
    if trows:
        for t in trows:
            L.append("    %-14s demand %8s   supply %8s%s"
                     % (t["trade"], _fmt_num(t["demand_hours_this_year"]),
                        _fmt_num(t["supply_hours_this_year"]),
                        ("   OVERSUBSCRIBED - queued: " +
                         ", ".join(t["projects_drawing_on_it"][:3]))
                        if t["oversubscribed"] else ""))
    else:
        L.append("    nothing active draws on a hired trade")
    if out.get("note"):
        L.append("")
        L.append(_wrap(out["note"]))
    return "\n".join(L)


def _dashboard_snapshot(s):
    """One year's worth of the numbers `changes` diffs against later - a
    timestamped copy of figures already computed elsewhere (price_index,
    literacy, mine_capacity, ...), not a new figure of its own. Called once
    per simulated year from the `step` dispatch below."""
    return {
        "year": s.year,
        "price_index": round(s.price_index, 4),
        "wage_index": round(s.wage_index, 4),
        "literacy_general": round(float(s.civ.get("literacy_general", 0.0)), 4),
        "literacy_elite": round(float(s.civ.get("literacy_elite", 0.0)), 4),
        "capital": round(s.capital, 1),
        "revenue": round(s.revenue(), 1),
        "credit_limit": round(s.credit_limit(), 1),
        "throttle": round(s.throttle, 3),
        "binding": s.binding,
        "operating_count": len(s.operating),
        "done_earned": len(s.done - s.granted),
        "employees_total": round(sum(s.employees.values()), 2),
        "scholars": round(s.scholars, 2),
        "artisans": round(s.artisans, 2),
        "mine_capacity": {m: round(v, 1) for m, v in s.mine_capacity.items()},
        "scandal": round(s.scandal, 2),
        "reputation": round(s.reputation, 1),
        "eminence": round(s.eminence, 2),
    }


def _agent_economy(s, cmd=None):
    """A short, readable economic summary, with detail behind an explicit
    ask rather than printed by default - major prices, wages, cost of
    living, literacy, market saturation and household capacity, all read
    from figures `money`/`labour`/`state` already compute for their own
    screens, plus what has moved most recently using the same yearly
    snapshots `changes` reads.
    """
    full = bool((cmd or {}).get("full"))
    hist = getattr(s, "_dashboard_history", None) or []
    moved = {}
    if hist:
        now = hist[-1]
        for n_yrs in (5, 10):
            cutoff = s.year - n_yrs
            base = None
            for rec in hist:
                if rec["year"] <= cutoff:
                    base = rec
                else:
                    break
            if base is not None:
                moved["last_%d_years" % n_yrs] = {
                    "price_index": round(now["price_index"] - base["price_index"], 4),
                    "wage_index": round(now["wage_index"] - base["wage_index"], 4),
                    "literacy_general": round(
                        now["literacy_general"] - base["literacy_general"], 4)}
    out = {
        "ok": True,
        "price_index": round(s.price_index, 4),
        "wage_index": round(s.wage_index, 4),
        "cost_of_living_a_year": round(s.living_cost() - s.wage_bill(), 1),
        "literacy": {"general": round(float(s.civ.get("literacy_general", 0.0)), 3),
                     "elite": round(float(s.civ.get("literacy_elite", 0.0)), 3)},
        "household_places_used_of_all": "%.1f of %.1f" % (
            s.headcount(), s.headcount() + max(0.0, s.household_room())),
        "where_the_money_comes_from": s.revenue_sources(),
        "market_saturation": s.goods_market_summary(),
        "materials_at_a_premium": s.material_market_summary(),
        "what_moved_most": moved or "not enough history yet - step forward "
                                    "and ask again",
        "more_detail": '{"cmd":"economy","full":true}',
    }
    if full:
        # THE SAME PER-MATERIAL FACTOR money's own material_market_summary
        # already aggregates into one worst-case note, here as the rows that
        # note is built from, for every tracked commodity rather than just
        # the worst one.
        rows, seen = [], set()
        for pair in s.MATERIAL_CHECKS.values():
            ek = pair[0]
            if ek in seen:
                continue
            seen.add(ek)
            rows.append({"material": ek,
                        "price_factor_over_book": round(s.material_price_factor(ek), 3)})
        out["tracked_material_prices"] = sorted(rows, key=lambda r: -r["price_factor_over_book"])
        # THE SAME FORMULA `labour`'s own row() uses for "a_year_of_one", not
        # a second version of a wage this file already prints elsewhere.
        out["wages_by_trade"] = [
            {"trade": t, "a_year_of_one": round(
                ANNUAL_WAGE.get(t, 375.0) * s.wage_index * s.price_index
                * s.labour_price_factor(t), 0)}
            for t in sorted(WAGES) if s.trade_available(t)]
    return out


def render_economy(out):
    L = ["THE ECONOMY"]
    L.append("  price index %s   wage index %s   cost of living %s/yr"
             % (_factor(out.get("price_index")), _factor(out.get("wage_index")),
                _fmt_num(out.get("cost_of_living_a_year"))))
    lit = out.get("literacy") or {}
    L.append("  literacy: general %s, elite %s"
             % (_pct(lit.get("general")), _pct(lit.get("elite"))))
    L.append("  household places used: %s" % out.get("household_places_used_of_all"))
    if out.get("market_saturation"):
        L.append("")
        L.append(_wrap(out["market_saturation"], indent="  "))
    if out.get("materials_at_a_premium"):
        L.append(_wrap(out["materials_at_a_premium"], indent="  "))
    moved = out.get("what_moved_most")
    if isinstance(moved, dict) and moved:
        L.append("")
        L.append("  WHAT HAS MOVED MOST")
        for span, vals in sorted(moved.items()):
            L.append("    %s: price index %+.3f, wage index %+.3f, literacy %+.3f"
                     % (span.replace("_", " "), vals["price_index"],
                        vals["wage_index"], vals["literacy_general"]))
    if out.get("tracked_material_prices"):
        L.append("")
        L.append("  MATERIALS ABOVE BOOK PRICE")
        for r in out["tracked_material_prices"]:
            if r["price_factor_over_book"] > 1.01:
                L.append("    %-10s %sx book" % (r["material"],
                                                 _factor(r["price_factor_over_book"])))
    return "\n".join(L)


def _agent_changes(s, nodes, cmd=None):
    """What materially changed over the last N years - the diff a player
    otherwise has to work out by holding two screens in their head, which is
    exactly what one of our own testers had to do to diagnose a bug. Reads
    the yearly snapshots `step` records (_dashboard_snapshot) rather than
    recomputing anything; see that function for what is actually stored.
    """
    raw = (cmd or {}).get("years", 5)
    if isinstance(raw, bool):
        return {"ok": False, "error": "years must be a number, not true or false"}
    try:
        years = int(raw)
    except (TypeError, ValueError):
        return {"ok": False, "error": "years must be an integer"}
    if float(raw) != years:
        return {"ok": False, "error": "years must be a whole number of years. "
                                      "Nothing was changed."}
    if years < 1:
        return {"ok": False, "error": "years must be >= 1"}
    hist = getattr(s, "_dashboard_history", None) or []
    if not hist:
        return {"ok": False, "error": "nothing has been recorded yet; step "
                                      "forward a year first, then ask again"}
    now = hist[-1]
    cutoff = s.year - years
    baseline = None
    for rec in hist:
        if rec["year"] <= cutoff:
            baseline = rec
        else:
            break
    if baseline is None:
        earliest = hist[0]["year"]
        return {"ok": False,
                "error": ("this run's own record only goes back to %d AD, %d "
                          "years ago; ask for %d or fewer"
                          % (earliest, s.year - earliest, s.year - earliest))}
    moved = {
        "price_index": round(now["price_index"] - baseline["price_index"], 4),
        "wage_index": round(now["wage_index"] - baseline["wage_index"], 4),
        "literacy_general": round(
            now["literacy_general"] - baseline["literacy_general"], 4),
        "literacy_elite": round(
            now["literacy_elite"] - baseline["literacy_elite"], 4),
        "capital": round(now["capital"] - baseline["capital"], 1),
        "revenue": round(now["revenue"] - baseline["revenue"], 1),
        "credit_limit": round(now["credit_limit"] - baseline["credit_limit"], 1),
        "employees_total": round(
            now["employees_total"] - baseline["employees_total"], 2),
        "scholars": round(now["scholars"] - baseline["scholars"], 2),
        "artisans": round(now["artisans"] - baseline["artisans"], 2),
        "operating_count": now["operating_count"] - baseline["operating_count"],
        "technologies_completed": now["done_earned"] - baseline["done_earned"],
        "scandal": round(now["scandal"] - baseline["scandal"], 2),
        "reputation": round(now["reputation"] - baseline["reputation"], 1),
        "eminence": round(now["eminence"] - baseline["eminence"], 2),
    }
    then_cap = baseline.get("mine_capacity") or {}
    now_cap = now.get("mine_capacity") or {}
    cap_changes = []
    for m in sorted(set(then_cap) | set(now_cap)):
        d = round(now_cap.get(m, 0.0) - then_cap.get(m, 0.0), 1)
        if abs(d) > 0.05:
            cap_changes.append({"material": m, "change_t_per_yr": d})

    def _uniq(seq):
        return list(dict.fromkeys(seq))

    completed, revealed, opened, closed = [], [], [], []
    for rec in hist:
        if rec["year"] <= cutoff:
            continue
        completed.extend(rec.get("completed") or [])
        revealed.extend(rec.get("revealed_added") or [])
        opened.extend(rec.get("concerns_opened") or [])
        closed.extend(rec.get("concerns_closed") or [])
    completed = _uniq(completed)
    revealed = _uniq([k for k in revealed if k not in completed])
    opened = _uniq(opened)
    closed = _uniq([k for k in closed if k not in opened])
    # A HANDFUL OF WORDS, NOT THE WHOLE LOG. Anything the engine already
    # logged as happening TO this player over the window, filtered to the
    # kind of thing a player would call a political event rather than
    # ordinary bookkeeping ("hired a smith"). The log itself is already
    # player-facing prose (see `log`); this only picks out a slice of it.
    _MARKERS = ("sack", "denounced", "founder dies", "plague", "crisis",
               "scandal", "credit exhausted", "insolvency", "war", "revolt",
               "famine", "fire", "died", "denunciation")
    events = [{"year": y, "message": m} for y, m in s.log
             if cutoff < y <= s.year and any(mk in m.lower() for mk in _MARKERS)]
    return {
        "ok": True,
        "from_year": baseline["year"], "to_year": now["year"],
        "moved": moved,
        "bottleneck": {"then": baseline.get("binding"), "now": now.get("binding")},
        "capacity_gained_or_lost": cap_changes or "none",
        "technologies_completed": completed or "none",
        "technologies_newly_heard_of": revealed or "none",
        "concerns_opened": opened or "none",
        "concerns_closed": closed or "none",
        "notable_events": events or "none",
    }


def render_changes(out):
    L = ["WHAT CHANGED, %s to %s AD" % (out.get("from_year"), out.get("to_year"))]
    m = out.get("moved") or {}
    L.append("  price index %+.3f   wage index %+.3f   literacy %+.3f (general)"
             % (m.get("price_index", 0.0), m.get("wage_index", 0.0),
                m.get("literacy_general", 0.0)))
    L.append("  capital %s%s   revenue %s%s/yr   %s technologies completed"
             % ("+" if m.get("capital", 0) >= 0 else "", _fmt_num(m.get("capital")),
                "+" if m.get("revenue", 0) >= 0 else "", _fmt_num(m.get("revenue")),
                _fmt_num(m.get("technologies_completed"))))
    bn = out.get("bottleneck") or {}
    if bn.get("then") != bn.get("now"):
        L.append("  bottleneck moved: %s -> %s" % (bn.get("then"), bn.get("now")))
    elif bn.get("now"):
        L.append("  bottleneck unchanged: %s" % bn.get("now"))
    cap = out.get("capacity_gained_or_lost")
    if isinstance(cap, list) and cap:
        L.append("  capacity: " + ", ".join(
            "%s %+.1f t/yr" % (r["material"], r["change_t_per_yr"]) for r in cap))
    for label, key in (("built", "technologies_completed"),
                       ("newly heard of", "technologies_newly_heard_of"),
                       ("opened", "concerns_opened"), ("closed", "concerns_closed")):
        v = out.get(key)
        if isinstance(v, list) and v:
            L.append("  %s: %s" % (label, ", ".join(v)))
    ev = out.get("notable_events")
    if isinstance(ev, list) and ev:
        L.append("")
        L.append("  NOTABLE EVENTS")
        for e in ev:
            L.append(_wrap("%d: %s" % (e["year"], e["message"]), indent="    "))
    return "\n".join(L)


def final_report(s, nodes):
    """The scoreboard, once the run is over.

    Two play testers finished long runs and got one sentence - "you built 1944
    things and did not reach point-contact transistor" - then a queue of
    identical refusals. One started a whole second game with the fog off and
    ran `path` just to learn that the goal is 142 nodes deep and which one
    they had stopped at. That is a question the game should answer when there
    is nothing left to spoil: the run is finished, so showing the road is the
    reward for finishing it, not a leak.
    """
    goal = getattr(s, "goal", None)
    earned = sorted(s.done - s.granted)
    out = {"ended_in": s.year, "why": _agent_end_reason(s),
           "you_built": len(earned),
           "this_society_already_had": len(s.granted),
           "money": round(s.capital, 1),
           "people": round(s.headcount(), 1),
           "reputation": round(s.reputation, 1),
           "concerns_you_were_running": len(getattr(s, "operating", ())),
           "failed_attempts": sum(getattr(s, "failed_attempts", {}).values())}
    if goal and goal in nodes:
        need = closure(nodes, goal)
        left = [x for x in topo_order(nodes, need) if x not in s.done]
        out["the_goal"] = goal
        out["reached_it"] = bool(s.goal_year)
        out["the_whole_road_was"] = len(need)
        out["you_had_%d_of_them" % (len(need) - len(left))] = len(need) - len(left)
        out["still_to_build_when_it_ended"] = len(left)
        # The next few steps you never took, in the order you would have taken
        # them. Under fog this is the first sight of the road; the run is over.
        out["the_next_things_would_have_been"] = left[:8]
        out["and_the_last_step"] = goal
    biggest = sorted(earned, key=lambda k: -nodes[k]["_total_cost"])[:6]
    out["the_largest_things_you_built"] = biggest
    # THE SCORE, ON THE SAME SCREEN. The run is over, so the tree's total
    # size is never withheld here (score_report's own reveal_tree_total is
    # (not fog) or ended, and by the time final_report runs it is always
    # ended) - see score_report and _score_components for what feeds it.
    out["score"] = score_report(s, nodes)
    return out


def render_final(out):
    L = ["=" * 70, "THE RUN IS OVER", "=" * 70]
    L.append(_wrap(str(out.get("why") or ""), indent="  "))
    L.append("")
    L.append("  ended in %s AD" % _fmt_num(out.get("ended_in")))
    L.append("  you built %s things; this society already had %s"
             % (_fmt_num(out.get("you_built")),
                _fmt_num(out.get("this_society_already_had"))))
    L.append("  %s in hand, %s people, reputation %s, %s concerns running"
             % (_fmt_num(out.get("money")), _fmt_num(out.get("people")),
                _fmt_num(out.get("reputation")),
                _fmt_num(out.get("concerns_you_were_running"))))
    if out.get("failed_attempts"):
        L.append("  %s attempts failed and had to be begun again"
                 % _fmt_num(out["failed_attempts"]))
    if out.get("the_goal"):
        L.append("")
        _had = next((v for k, v in out.items() if k.startswith("you_had_")), 0)
        L.append("  THE ROAD TO %s" % str(out["the_goal"]).upper())
        L.append("    %s nodes in all; you had %s of them and %s were still to build"
                 % (_fmt_num(out.get("the_whole_road_was")), _fmt_num(_had),
                    _fmt_num(out.get("still_to_build_when_it_ended"))))
        nxt = out.get("the_next_things_would_have_been") or []
        if nxt:
            L.append("    the next steps would have been: " + ", ".join(nxt))
    big = out.get("the_largest_things_you_built") or []
    if big:
        L.append("")
        L.append("  the largest things you built: " + ", ".join(big))
    if out.get("score") is not None:
        L.append("")
        L.append("  SCORE")
        L.extend(_score_lines(out["score"], indent="    "))
    L.append("=" * 70)
    return "\n".join(L)


# ---------------------------------------------------------------------------
# THE SCORE. A player who had just won asked for one number, weighted across
# seven things they named, plus a short list of achievements. Every raw
# value below is something the engine already tracks for a DIFFERENT reason
# (state, final_report, the risk and labour screens) - nothing here is a new
# ledger invented to make the formula prettier. See each component's own
# comment for exactly which field feeds it and why that is a fair reading of
# the category the player named, and see the commit/report for which of
# these are mechanically bounded (no tuning possible) versus anchored by
# judgement against the one real high-water mark available, the 599 AD save.
# ---------------------------------------------------------------------------

SCORE_WEIGHTS = {
    "technology_coverage": 0.35,
    "literacy": 0.15,
    "workforce": 0.15,
    "economy": 0.10,
    "institutions": 0.10,
    "resilience": 0.10,
    "standing": 0.05,
}


def _score_goal_floor_years(s, nodes):
    """The goal's own critical-path floor, in years - the fastest any run of
    any civilisation could reach it with unlimited money and one director
    (data.critical_path, civ-independent by construction: see its own
    docstring). Cached on the Sim the same way `final_report`'s
    `_goal_closure` already caches the goal's prerequisite set, because this
    walks the whole closure and `score` is meant to be called often.
    """
    cached = getattr(s, "_goal_critical_floor", None)
    if cached is not None:
        return cached
    goal = getattr(s, "goal", None)
    if not goal or goal not in nodes:
        return None
    try:
        yrs, _chain = critical_path(nodes, goal)
    except Exception:
        return None
    s._goal_critical_floor = yrs
    return yrs


def _score_components(s, nodes, reveal_tree_total):
    """The seven weighted components, each {"raw", "normalized", "weight",
    "weighted"} - raw in the quantity's own natural unit, normalized the
    0..1 figure the weight actually multiplies.

    `reveal_tree_total` is True off fog, or once the run has ended - the
    same two-part condition final_report's own "the TOTAL is the size of
    the tree's own spoiler surface" comment already uses for the goal's
    road, applied here to the bigger spoiler: the size of the WHOLE tree.
    done_count is visible in `state` under fog regardless, so showing
    done/total under fog mid-run would hand back the withheld total by
    division - this is the one place that has to check.
    """
    out = {}

    # TECHNOLOGY COVERAGE (35%) - done / the WHOLE tree, not done / the
    # goal's own closure. The goal's closure is 1 to 201 nodes of the tree
    # (goal_catalog, 17 goals) and reaching it no longer ends the run - see
    # _agent_end_reason's own comment: a won run has "barely touched" the
    # tree, and the default horizon (500 years) is comfortably more than
    # twice the longest goal floor (142 years), so every goal, however small
    # its own closure, leaves centuries to keep building before death or the
    # horizon actually ends the run. A goal-relative fraction would jump to
    # 1.0 the instant the goal completes and sit there for the rest of a
    # long run, which throws away 35% of the score's discriminating power
    # for exactly the "the tree is the real game, the goal is a gate" shape
    # this engine is built around. This is already a true fraction - 0 with
    # nothing built, 1 with the whole tree - so it needs no further anchor.
    if reveal_tree_total:
        total = len(nodes)
        raw = len(s.done)
        normalized = min(1.0, raw / total) if total else 0.0
        out["technology_coverage"] = {"raw": raw, "of_total": total,
                                       "normalized": normalized}
    else:
        out["technology_coverage"] = {
            "raw": len(s.done), "of_total": None, "normalized": None,
            "withheld": ("the tree's total size is the one thing fog keeps "
                         "from you; this resolves once the run ends")}

    # LITERACY (15%) - general and elite literacy against the CEILING each
    # already has in this engine (SocietyMixin.literacy_ceiling_general/
    # _elite, society.py): a hard, population- and mechanisation-driven cap
    # that is the same structural number for every civilisation, not
    # something this file tunes. 0.90 general / 0.97 elite are what the
    # mechanism itself says a pre-transistor-era society can ever reach, so
    # "literacy" here means how much of what is ACTUALLY reachable has been
    # reached, not a raw fraction a civilisation starting with worse
    # schooling could never max out. Weighted equally between the two
    # populations the engine tracks separately.
    gen = max(0.0, float(s.civ.get("literacy_general", 0.0)))
    gen_ceiling = max(1e-9, s.literacy_ceiling_general())
    eli = max(0.0, float(s.civ.get("literacy_elite", 0.0)))
    eli_ceiling = max(1e-9, s.literacy_ceiling_elite())
    lit_norm = 0.5 * min(1.0, gen / gen_ceiling) + 0.5 * min(1.0, eli / eli_ceiling)
    out["literacy"] = {"raw": round(gen, 4),
                        "raw_detail": {"general": round(gen, 4),
                                       "general_ceiling": round(gen_ceiling, 4),
                                       "elite": round(eli, 4),
                                       "elite_ceiling": round(eli_ceiling, 4)},
                        "normalized": lit_norm}

    # WORKFORCE (15%) - headcount(), the same aggregate final_report already
    # reports as "people" (employees plus slaves plus freedmen; labour.py).
    # Population has no mechanical ceiling this engine states outright the
    # way literacy does, so this is the one honest anchor available: a
    # log scale (a second thousand employees is not as meaningful as the
    # first) against a round number with headroom above the one real
    # high-water mark on record, the 599 AD calibration save's 691.7 - NOT
    # that save's own figure, so the save does not define 100% by
    # construction. 7,000 is ten times 691.7, rounded to a clean figure.
    WORKFORCE_ANCHOR = 7000.0
    headcount = max(0.0, s.headcount())
    work_norm = min(1.0, math.log1p(headcount) / math.log1p(WORKFORCE_ANCHOR))
    out["workforce"] = {"raw": round(headcount, 1), "normalized": work_norm}

    # ECONOMY (10%) - capital, but never as a bare denarius figure: each
    # civilisation's currency is a different scale (civs/*.json: "denarius",
    # "wu zhu cash", "hacksilver by weight", "cacao bean and cotton cloth",
    # each with its own wage_index/price_index multiplier on the shared wage
    # table, data.ANNUAL_WAGE) - comparing raw capital across civilisations
    # would be comparing different units with the same name. Deflating by
    # one ordinary worker-year IN THIS CIVILISATION'S OWN MONEY (an
    # artisan's annual wage, scaled by this civ's live price_index and
    # wage_index - the same two multipliers economy.py and labour.py price
    # everything else with) turns capital into a currency-free "years of an
    # ordinary worker's wage this fortune could buy", which is comparable
    # across civilisations. Log-scaled for the same reason as workforce,
    # against the same methodology: a round anchor ten times the
    # calibration save's 4.41 million worker-years, rounded to a clean
    # figure (50 million), not that save's own number.
    ECONOMY_ANCHOR_WORKER_YEARS = 50_000_000.0
    reference_wage = max(1e-6, ANNUAL_WAGE.get("artisan", 250.0)
                          * max(1e-6, float(getattr(s, "price_index", 1.0)))
                          * max(1e-6, float(getattr(s, "wage_index", 1.0))))
    worker_years = max(0.0, s.capital) / reference_wage
    econ_norm = min(1.0, math.log1p(worker_years)
                    / math.log1p(ECONOMY_ANCHOR_WORKER_YEARS))
    out["economy"] = {"raw": round(s.capital, 1),
                       "raw_detail": {"worker_years_equivalent":
                                      round(worker_years, 1)},
                       "normalized": econ_norm}

    # INSTITUTIONS (10%) - every CAPABILITY_INSTITUTIONS node (projects.py:
    # the fixed roster every running()/auto-open rule in the engine already
    # checks against), scored by institution_units()/institution_unit_ceiling()
    # for the five that scale (workshop, school, academy, collegium,
    # freedman staff - each ceiling already population- and literacy-driven,
    # the same mechanism literacy's own ceiling uses) and by a plain
    # running() boolean for the rest, which this engine models as one-off
    # achievements rather than a quantity (a patronage, a written corpus, a
    # power grid). sorted() because this sums floats over what would
    # otherwise be a frozenset, and PYTHONHASHSEED must not move the sum.
    inst_keys = sorted(s.CAPABILITY_INSTITUTIONS)
    inst_vals = []
    for k in inst_keys:
        if k in s.SCALABLE_INSTITUTIONS:
            ceiling = max(1.0, s.institution_unit_ceiling(k))
            inst_vals.append(min(1.0, s.institution_units(k) / ceiling))
        else:
            inst_vals.append(1.0 if s.running(k) else 0.0)
    inst_norm = (sum(inst_vals) / len(inst_vals)) if inst_vals else 0.0
    out["institutions"] = {"raw": sum(1 for v in inst_vals if v > 0.0),
                            "of_total": len(inst_vals),
                            "normalized": inst_norm}

    # RESILIENCE (10%) - an equally-weighted average of five fractions, each
    # a real, already-saved field read against a real threshold, none of
    # them invented for this screen:
    #   - corpus_preserved: 1 - forgotten / (done + forgotten). `forgotten`
    #     (society.py's _shocks, set nowhere else) is every technology a
    #     sacking actually destroyed; this is the share of everything ever
    #     completed that still stands.
    #   - solvent_share: 1 - insolvent_years / years elapsed. insolvent_years
    #     is a running count economy.py already keeps.
    #   - staffing_share: 1 - (distinct years close_unstaffed_ventures fired)
    #     / years elapsed. shut_for_staff (projects.py) is {node: year};
    #     distinct years, not count of concerns, because closing four
    #     concerns in one bad year is one bad year, not four.
    #   - scandal_margin: 1 - scandal / suspicion_danger, the exact ratio
    #     `state` already reports as "chance_of_being_denounced_this_year"'s
    #     own numerator and denominator.
    #   - founder_share: 1.0 if founder_alive else 0.0 - only ever
    #     discriminating in mortal play; harmless (always 1.0) under the
    #     immortal default.
    # Each is already a fraction of a real total, so none of these five
    # needs a chosen anchor the way workforce/economy do.
    run_years = max(1.0, s.year - s.cfg.get("start_year", s.year))
    forgotten_n = len(getattr(s, "forgotten", None) or {})
    ever_completed = len(s.done) + forgotten_n
    corpus_preserved = (1.0 - forgotten_n / ever_completed) if ever_completed else 1.0
    solvent_share = 1.0 - min(1.0, getattr(s, "insolvent_years", 0) / run_years)
    shut_years = len(set((getattr(s, "shut_for_staff", None) or {}).values()))
    staffing_share = 1.0 - min(1.0, shut_years / run_years)
    suspicion_danger = max(1e-9, float(s.cfg.get("suspicion_danger", 25.0)))
    scandal_margin = 1.0 - min(1.0, max(0.0, s.scandal) / suspicion_danger)
    founder_share = 1.0 if s.founder_alive else 0.0
    res_parts = [corpus_preserved, solvent_share, staffing_share,
                 scandal_margin, founder_share]
    res_norm = sum(res_parts) / len(res_parts)
    out["resilience"] = {"raw": sum(1 for v in res_parts if v >= 0.999),
                          "of_total": len(res_parts), "normalized": res_norm}

    # STANDING (5%) - reputation alone, not eminence: eminence is a danger
    # signal (how close you sit to being confiscated or denounced for being
    # too visible - see `prominence`/eminence_report), the opposite of a
    # score you want to maximise, where reputation (0..100 by construction;
    # projects.py clamps it at 100) is this engine's own plain measure of
    # standing.
    rep = max(0.0, min(100.0, s.reputation))
    out["standing"] = {"raw": round(rep, 1), "normalized": rep / 100.0}

    for name, weight in SCORE_WEIGHTS.items():
        comp = out[name]
        comp["weight"] = weight
        comp["weighted"] = (round(comp["normalized"] * weight, 4)
                            if comp["normalized"] is not None else None)
    return out


def _score_achievements(s, nodes):
    """Won-run achievements, each a plain condition on a field the engine
    already saves across sittings (SAVE_FIELDS, this file) - so each one is
    true of the WHOLE run, not just whatever is in memory right now. None of
    these reads failed_attempts: that counter is real (projects.py) but is
    NOT in SAVE_FIELDS, so it silently resets to empty every time a session
    is resumed from disk - the normal way this game is played (cli.py
    autosaves after every command). An achievement built on it would read
    "flawless" for any run that was ever closed and reopened, which is not
    an achievement, it is a bug in what gets remembered. See the report.
    """
    goal = getattr(s, "goal", None)
    won = bool(goal and s.goal_year)
    out = {}
    if not won:
        return out
    out["corpus_intact"] = {
        "won": len(getattr(s, "forgotten", None) or {}) == 0,
        "what": "the corpus was never diminished by a sacking"}
    out["never_understaffed"] = {
        "won": len(getattr(s, "shut_for_staff", None) or {}) == 0,
        "what": "no concern ever closed for want of staff"}
    out["clean_ledger"] = {
        "won": (getattr(s, "insolvent_years", 0) == 0
                and getattr(s, "interest_paid", 0.0) <= 0.0),
        "what": "never spent a year insolvent or paid a denarius of interest"}
    out["free_hands_only"] = {
        "won": (s.slaves == 0 and getattr(s, "manumitted_total", 0) == 0),
        "what": "built it without ever owning a slave"}
    floor = _score_goal_floor_years(s, nodes)
    out["outpaced_the_fastest_plan"] = {
        "won": bool(floor and (s.goal_year - s.cfg["start_year"]) <= 2.0 * floor),
        "what": ("reached the goal within twice its own fastest possible "
                 "timeline (%s years, one director, unlimited money)"
                 % _fmt_num(floor) if floor else "the goal's floor is unknown")}
    return out


def score_report(s, nodes):
    """The full score: the gate, the seven weighted components, the total,
    and the achievements - read by both the `score` command (any time) and
    the ending screen (final_report, below).
    """
    end_reason = _agent_end_reason(s)
    reveal_tree_total = (not getattr(s, "fog", False)) or (end_reason is not None)
    components = _score_components(s, nodes, reveal_tree_total)
    goal = getattr(s, "goal", None)
    goal_reached = bool(goal and s.goal_year)
    total = None
    if goal_reached and all(c["normalized"] is not None for c in components.values()):
        total = round(sum(c["weighted"] for c in components.values()), 4)
    out = {"goal_in_words": (s.nodes[goal]["name"] if goal in getattr(s, "nodes", {})
                             else None),
           "goal_reached": goal_reached, "goal_year": s.goal_year,
           "end_reason": end_reason,
           "components": components, "total": total}
    if not goal_reached:
        out["no_score"] = "the goal was not reached"
    out["achievements"] = _score_achievements(s, nodes)
    return out


_SCORE_COMPONENT_ORDER = ("technology_coverage", "literacy", "workforce",
                          "economy", "institutions", "resilience", "standing")


def _score_lines(out, indent="  "):
    """The component table, the total and the achievements, as plain text -
    shared by `score` (render_score) and the ending screen (render_final),
    so there is exactly one rendering of a score to fall out of step.
    """
    L = []
    if not out.get("goal_reached"):
        L.append(_wrap("no score: the goal was not reached%s"
                       % (" yet" if out.get("end_reason") is None else "")
                       + (". The breakdown below is provisional - what you "
                          "would be optimising if you reached %s."
                          % (out.get("goal_in_words") or "the goal")
                          if out.get("end_reason") is None else "."),
                       indent=indent))
        L.append("")
    for name in _SCORE_COMPONENT_ORDER:
        c = (out.get("components") or {}).get(name)
        if not c:
            continue
        label = name.replace("_", " ")
        if c.get("normalized") is None:
            L.append("%s%-20s withheld: %s" % (indent, label, c.get("withheld", "-")))
            continue
        L.append("%s%-20s raw %-14s normalized %-6s weight %-5s weighted %s"
                 % (indent, label, _fmt_num(c.get("raw")),
                    "%.3f" % c["normalized"], "%.0f%%" % (c["weight"] * 100),
                    "%.4f" % c["weighted"]))
    L.append("")
    if out.get("total") is not None:
        L.append("%sTOTAL: %.1f%%" % (indent, out["total"] * 100))
    else:
        L.append("%sTOTAL: -- (%s)" % (indent, out.get("no_score")
                 or "not computable until the run ends under fog"))
    ach = out.get("achievements") or {}
    if ach:
        L.append("")
        L.append("%sACHIEVEMENTS" % indent)
        for a in ach.values():
            L.append("%s  [%s] %s" % (indent, "x" if a["won"] else " ", a["what"]))
    return L


def render_score(out):
    L = ["=" * 70, "SCORE", "=" * 70, ""]
    L.extend(_score_lines(out))
    L.append("=" * 70)
    return "\n".join(L)


def _goal_progress_count(s, nodes):
    """How many of the goal's own prerequisites you already have, with
    nothing named and not even the total - see the block comment where this
    is used in _agent_state for why the total itself has to stay withheld
    until the run ends.
    """
    goal = getattr(s, "goal", None)
    if not goal or goal not in nodes:
        return None
    need = getattr(s, "_goal_closure", None)
    if need is None:
        try:
            need = s._goal_closure = closure(nodes, goal)
        except Exception:
            return None
    return sum(1 for x in need if x in s.done)


def _founder_death_info(s):
    """When and how old the founder was when they died, or None if not.

    core.py logs "the founder dies, aged about %d" the one time it happens
    and never stores the age anywhere else - a normal-play tester in mortal
    mode found their founder's death reported as one more line among sixty
    in a long `step`'s events, with no field anywhere a script would check
    first, and the age nowhere but that sentence.

    THE ATTRIBUTES, NOT ONLY THE LOG. `log` is not itself a saved field -
    see SAVE_FIELDS - so a save taken after the founder's death and resumed
    in a new process starts that process's `s.log` empty, and scanning it
    would silently un-report an age that had already been shown once. The
    step handler sets _founder_death_aged/_founder_death_year the moment it
    sees the line, and those two ARE saved fields, so this is the fast path
    and the one that survives a resume. Scanning the log is the fallback,
    for a Sim driven straight off the engine (as the test suite does) or a
    save written before this existed.
    """
    if s.founder_alive:
        return None
    aged = getattr(s, "_founder_death_aged", None)
    if aged is not None:
        return {"year": getattr(s, "_founder_death_year", None), "aged_about": aged}
    cache = getattr(s, "_founder_death_cache", None)
    if cache is not None:
        return cache
    for yr, msg in s.log:
        if "founder dies" in msg.lower():
            m = re.search(r"aged about (\d+)", msg)
            cache = {"year": yr, "aged_about": int(m.group(1)) if m else None}
            s._founder_death_cache = cache
            return cache
    return None


def _worth_knowing_early(s):
    """Said once, ever, early in a run: `help commands` is the complete
    command index (log, values, money, automation, save/load and more, not
    only the five starter verbs), and `log` is an exact, paginated history of
    everything that happens from here on. Both are true from turn one, and
    neither was ever pointed at directly - the opening briefing names `help`
    in passing and lists its topics, but a player who won the whole game
    reported using specialised commands for a long while without realising
    how complete the index was, and separately flagged `log`'s depth (815
    entries by 200 AD in their run) as something worth knowing about sooner.

    ONCE, NOT EVERY TURN: gated on a flag this sets itself the first time it
    fires (see _said_command_index in SAVE_FIELDS - it has to survive a save
    or it would fire again every time a script reloads the game) and on
    still being early in the run, so resuming a save from deep into an
    existing game never springs a first-timer's tip on somebody who has long
    since found all of this themselves.
    """
    if getattr(s, "_said_command_index", False):
        return None
    if s.year > s.cfg.get("start_year", s.year) + 3:
        return None
    s._said_command_index = True
    return ("{\"cmd\":\"help\",\"topic\":\"commands\"} lists the entire "
            "command surface, not only the five you started with - log, "
            "values, money, automation, save/load and more, one line each. "
            "{\"cmd\":\"log\"} is a paginated, exact history of everything "
            "that happens from here on: starts, completions, failures, "
            "hazards, openings, closures, staffing. Both are worth a look "
            "now, before a hundred turns go by and you wish you had been "
            "reading it all along.")


def _agent_state(s, nodes, cmd=None):
    active = {}
    for k, st in s.active.items():
        n = nodes[k]
        bill = st.get("cost_left")
        _at_risk = st.get("stalled_years", 0)
        if bill is None:
            bill = max(0.0, s.project_cost(k) - st["spent"])
        active[k] = {"name": n["name"], "founder_hours_left": round(st["ph_left"], 1),
                     "founder_hours_total": n["ph"], "years_in_progress": st["yrs"],
                     "spent": round(st["spent"], 1), "still_to_pay": round(bill, 1),
                     # THE COUNTDOWN, WHERE IT CAN BE SEEN. It ran silently for
                     # three years and then took everything spent.
                     **({"will_be_abandoned_in_years": 4 - _at_risk,
                         "because_nobody_here_can": st.get("blocked_on_trades")}
                        if _at_risk else {}),
                     # A tester poured 1,200 hours into a project that was
                     # calendar-locked and could not use them, and only noticed by
                     # reading state closely. Say which of the three things it is
                     # actually waiting for.
                     # WORKED OUT NOW, not read off what last year happened to
                     # record. short_of_trade is only written when a step
                     # actually ran the shortage branch, so a project could sit
                     # for centuries reporting "your hours" while the founder
                     # had 1,900 idle: a play tester watched `logarithms` stall
                     # from 325 AD to the horizon that way, and the real cause
                     # was 40,000 scribe-hours wanted from a society that can
                     # field three and a half scribes. Telling somebody to
                     # spend hours they cannot spend, for 275 years, is worse
                     # than saying nothing.
                     "waiting_on": _waiting_on(s, nodes, k, st, bill),
                     # WHERE THIS YEAR'S HOURS WENT, for this project specifically.
                     # offered is what step() gave it a shot at; effective is
                     # how much of that actually came off founder_hours_left.
                     # The two differ when a trade or the money for it fell
                     # short - see hours_this_year for the whole year's picture.
                     "hours_offered_this_year": st.get("hours_offered_this_year", 0.0),
                     "hours_effective_this_year": st.get("hours_effective_this_year", 0.0),
                     # WHY THIS MUCH, READ BACK FROM THE ALLOCATOR ITSELF.
                     # core.py's step() (5. progress) writes these four onto
                     # the same st dict as it decides each project's share of
                     # the pool; `portfolio` and _waiting_on's own "your
                     # hours" sentence both read them from here, so the share
                     # a player is TOLD and the share that was actually
                     # applied are the same number by construction, not by
                     # agreement between two pieces of code that happen to
                     # compute it the same way. None before the first step()
                     # a fresh project has lived through.
                     "pool_rank_this_year": st.get("pool_rank_this_year"),
                     "pool_active_count_this_year":
                         st.get("pool_active_count_this_year"),
                     "pool_total_this_year": st.get("pool_total_this_year"),
                     "pool_remaining_before_this_year":
                         st.get("pool_remaining_before_this_year"),
                     "underfunded_this_year": st.get("underfunded_this_year", False),
                     # Only present when it is underfunded, and it says why: a
                     # playtester in deep arrears saw hours offered and none
                     # effective, with nothing anywhere explaining the gap.
                     "why_underfunded": st.get("why_underfunded"),
                     "bountied": k in s.bountied}
    end_reason = _agent_end_reason(s)
    full = bool((cmd or {}).get("full"))
    end_year = getattr(s, "end_year", s.cfg["start_year"] + s.cfg["horizon_years"])
    out = {
        "year": s.year,
        # HOW MUCH TIME IS LEFT. A weird-play tester ran to the end of a
        # five-hundred-year game and wrote that "the hidden 1800 horizon is
        # announced nowhere until you overshoot it". It was in one help topic
        # and in no reply anybody reads every turn. A clock you cannot see is
        # not a constraint, it is an ambush.
        "horizon_year": end_year, "years_left": max(0, end_year - s.year),
        "capital": round(s.capital, 1), "revenue": round(s.revenue(), 1),
        "upkeep": round(s.upkeep(), 1),
        # A playtester watched capital fall 400 to 184 on the first step with
        # nothing active and both revenue and upkeep reported as zero, and no
        # field in the protocol explained where the money went. It went on food,
        # rent, tax and keeping up appearances, which the model has always
        # charged and never showed. Anything that moves your money should be
        # visible in the state that claims to describe your money.
        # SPLIT, because one number under this name was two things. A break
        # tester proved `state.living_cost` was living_and_appearances PLUS the
        # entire payroll (224.9 + 884.2 = 1109.1, to the decimal), while `money`
        # reported those as two separate lines - the same quantity labelled two
        # incompatible ways by two commands in one program, and the misleading
        # label was on `state`, which the welcome text calls one of "the four
        # you need first". A player watching only `state` after hiring would
        # read their own payroll as their cost of living spiralling.
        "living_cost": round(s.living_cost() - s.wage_bill(), 1),
        "wage_bill": round(s.wage_bill(), 1),
        "mine_operating_cost": round(s.mine_operating_cost(), 1),
        # Knowing how and running it are different, so say how many you know
        # how to run and have not opened. Without this the difference is
        # invisible until a player wonders why building things stopped paying.
        # Only present when the run has effectively stopped. See stall_diagnosis.
        # NOT AFTER IT IS OVER. At the horizon this still printed "it is
        # escapable ... work for wages: you have 2000 of your own hours left
        # this year", and every action it recommended was then refused with
        # "the run has ended". Advice you cannot take is not advice.
        "stuck": (None if _agent_end_reason(s) else s.stall_diagnosis()),
        "concerns_you_run": len(getattr(s, "operating", ())),
        "you_know_how_to_run_but_have_not_opened": sum(
            1 for k in s.done if s.is_venture(k) and k not in s.operating),
        # WHAT THAT IS COSTING YOU, in money, on the main screen. A play tester
        # built twenty concerns, left them all shut for twenty-five years and
        # watched their income sit flat: the per-completion line saying "open
        # it" was one line in a log full of them, and a count of shut shops is
        # not a reason to act. A yearly figure is.
        "shut_concerns_would_earn_a_year": round(sum(
            nodes[k]["rev"] - nodes[k]["up"] for k in s.done
            if s.is_venture(k) and k not in s.operating
            and nodes[k]["rev"] > nodes[k]["up"]), 0) or None,
        # THE SAME GAP, for the handful of capabilities whose running()-gated
        # payout is not revenue at all - protection, standing, credit, a
        # staff ceiling - and so never showed up in shut_concerns above. This
        # is `state`, the screen a player actually rereads every year, which
        # is exactly where the corpus bug's lesson said a DONE/OPERATING
        # split has to be loud: see ProjectsMixin.capability_gaps.
        "critical_capabilities_not_operating": s.capability_gaps() or None,
        # net_per_year counts the STANDING flows only. It never counted what
        # projects consume, which is usually the largest outflow by far, so a
        # playtester watched it report a healthy positive number for eight
        # consecutive years while capital sat at exactly 0.0, every denarius
        # going into the work in progress. A field that says you are making
        # money while you are visibly making none is worse than no field.
        # Named for what it is. The roll happens after the spending loop, so this
        # is the year just simulated, not the one before it.
        "project_spend_this_year": round(getattr(s, "spend_last_year", 0.0), 1),
        # INTEREST IS A COST AND BELONGS IN THE NET. A weird-play tester read
        # "+9.5 a year" for years while their capital fell 105, then 117,
        # accelerating - with the interest rate printed two lines below on the
        # same screen. Arrears compound; a net that ignores them tells a
        # household in a debt spiral that it is recovering.
        "interest_on_arrears_this_year": round(
            max(0.0, -s.capital) * s.debt_interest_rate(), 1),
        # LESS THE YEAR YOU HAVE ALREADY PAID FOR. `hire` takes a finder's fee
        # and the first year's wages in advance, and step() correctly nets that
        # advance off the living cost it charges - but this forecast did not,
        # so it billed the same year twice. A break tester hired four artisans,
        # read "Net/yr after it: -1,097", stepped once, and lost 61. Off by the
        # whole wage bill, in the one year the player is most likely to look.
        "wages_you_have_already_paid_this_year": round(
            getattr(s, "wages_prepaid", 0.0), 1) or None,
        "net_after_project_spend": round(s.revenue() - s.upkeep() - s.living_cost()
                                         + min(s.living_cost(),
                                               getattr(s, "wages_prepaid", 0.0))
                                         - s.mine_operating_cost()
                                         - max(0.0, -s.capital) * s.debt_interest_rate()
                                         - getattr(s, "spend_last_year", 0.0), 1),
        # THE STANDING FIGURE HAS TO READ THE STANDING REVENUE. This counts
        # "the STANDING flows only" per the comment on shut_concerns above -
        # the household's ordinary-year position, not this particular year's
        # - and was reading plain revenue(), which dips for a year whenever
        # `work` sells founder-hours: a player who sold hours watched this
        # swing to -193/yr and revert the moment the calendar rolled over.
        # revenue_capacity() (economy.py) exists for exactly this - it is
        # what credit_limit() already reads, with the identical reasoning in
        # its own docstring ("a lender does not cut your line because you
        # took a job this year") - and this field claimed to be the same
        # kind of number without actually being computed as one.
        "net_per_year": round(s.revenue_capacity() - s.upkeep() - s.living_cost()
                              + min(s.living_cost(),
                                    getattr(s, "wages_prepaid", 0.0))
                              - s.mine_operating_cost()
                              - max(0.0, -s.capital) * s.debt_interest_rate(), 1),
        # Rows are [capacity, ready_year] for people bought and trained, and
        # [0, ready_year, trade, count] for a trade being taught, so read by
        # index. Unpacking two names off a four-wide row killed `state` outright
        # the moment anybody used `train`.
        "training_pending": [
            {"artisan_capacity": round(row[0], 2), "ready_year": row[1],
             "trade": (row[2] if len(row) > 2 else None),
             "people": (row[3] if len(row) > 3 else None)}
            for row in getattr(s, "training", [])],
        # LESS WHAT YOU HAVE ALREADY SOLD. A break tester worked 2,300 hours as
        # a scholar, was told "hours left: 0" by the work reply, and then read
        # "2,400 founder-hours free this year" in state and on the prompt in the
        # same breath - and was refused one more hour for having none. The pool
        # is the pool; what is FREE is the pool less the hours already spent on
        # wage work.
        "founder_hours_available": round(
            max(0.0, s.director_pool() - s.director_hours_committed()), 1),
        # FREE HOURS, SHOUTED, WHEN THEY ARE GOING TO WASTE, not one quiet
        # number among fifty. A blind playthrough treated a long
        # calendar-floor project as though it were the active research,
        # even with thousands of founder-hours spent on nothing that year,
        # and only started running several projects in parallel after an
        # outside hint changed the run materially - their own account calls
        # it probably decisive. This is the central mechanic of the game
        # (see help's "how a turn works") and nothing taught it. Every
        # active project's own hours are fully spent for the year exactly
        # when it is waiting on the calendar, not on you - _waiting_on
        # returns "the calendar" for precisely that case - so that is the
        # signal, not a guess at intent.
        # WHICH CONCERN SHUTS NEXT, while there is still time to hire. The
        # staffing rule closing a concern is not a policy a player can switch
        # off - it is the world taking back something nobody is left to watch -
        # and a concern that shuts itself now reopens once restaffed. What three
        # players still asked for was the year's notice, not the cure.
        "supervision_close_to_the_edge": s.staffing_closure_warnings() or None,
        # SAID ONCE, EARLY, NOT EVERY TURN. The opening briefing already names
        # `help` and lists its topics in passing, but a player who won the
        # whole game reported using specialised commands for a long while
        # without realising `help commands` was a complete index of
        # everything the game can do - log, values, money, automation,
        # save/load - and separately flagged `log` itself, an exact paginated
        # history of starts, completions, failures, hazards, openings,
        # closures and staffing, as something they wished they had leaned on
        # from the start rather than discovering was this thorough only after
        # hundreds of entries had piled up. Both are already true from turn
        # one; neither was ever pointed at directly. Fired once, only in the
        # first few years of a run (never on a save that is already well
        # under way), so a veteran resuming an old game is not told this
        # again on a whim - see _said_command_index in SAVE_FIELDS for why it
        # only ever fires once per game, not once per session.
        # full:true IS THE "EVERYTHING AT ONCE" POWER VIEW, already the
        # reply most often bumping its own readability ceiling (see the
        # "state full stays readable" checks) - not the screen a first
        # turn's plain `state` actually returns. Asking only there, never
        # under full:true, means the one-shot chance to say this is never
        # spent paying that screen's byte budget, and it still fires on the
        # very next ordinary `state` or `step` instead.
        **({"worth_knowing_early": _worth_knowing_early(s)} if not full else {}),
        "free_hours_going_unused": (
            ("%s founder-hours this year are going into nothing: every "
             "project you have in hand is only waiting on the calendar "
             "now, not on you or your money. A calendar floor is not "
             "exclusive research time - start something else alongside "
             "it while it runs. 'available' or 'stuck' says what you "
             "could begin today."
             % "{:,.0f}".format(max(0.0, s.director_pool()
                                    - s.director_hours_committed())))
            if (active
                and all(v["founder_hours_left"] <= 0 for v in active.values())
                and max(0.0, s.director_pool()
                        - s.director_hours_committed()) > 200)
            # AND WHEN NOTHING IS RUNNING AT ALL, which the first branch cannot
            # see because it requires `active` to be non-empty. A player who
            # steps a year with an empty slate loses those hours exactly as
            # completely, and hours do not carry.
            else ("%s founder-hours this year are going into nothing at all: "
                  "you have no work in hand. Hours do not carry to next year. "
                  "'available' or 'stuck' says what you could begin today."
                  % "{:,.0f}".format(max(0.0, s.director_pool()
                                         - s.director_hours_committed()))
                  if (not active
                      and max(0.0, s.director_pool()
                              - s.director_hours_committed()) > 200)
                  else None)),
        "founder_hours_sold_for_wages_this_year": round(
            getattr(s, "wage_hours_this_year", 0.0), 1),
        # WHERE THE HOURS COME FROM. A play tester watched their year grow from
        # 2,000 hours to 6,090 over a long run with nothing anywhere saying
        # why. It is not the founder working harder: it is the deputies an
        # institution gives you, each of whom directs work in your name.
        "where_your_hours_come_from": {
            "you": round(s.cfg["founder_hours_per_year"]
                         * (0.25 if s.bondage_years_left > 0 else 1.0), 1)
                   if s.founder_alive else 0.0,
            "deputies_who_direct_work_for_you": round(s.directors_extra, 2),
            "hours_each_deputy_adds": s.cfg["director_hours_per_year"],
        },
        "founder_hours_spent_teaching_this_year": round(
            getattr(s, "teaching_hours_this_year", 0.0), 1),
        # LAST YEAR'S HOURS, ACCOUNTED FOR. Set in step(); see the comment
        # there. available is this year's fresh figure, not last year's -
        # read it alongside, not in place of, hours_this_year.
        "hours_this_year": getattr(s, "hours_this_year", None),
        "founder_alive": s.founder_alive,
        # THE AGE ITSELF, AS A FIELD, not only inside a log sentence a script
        # would have to parse. See _founder_death_info.
        "founder_died_aged": (_founder_death_info(s) or {}).get("aged_about"),
        "founder_died_in": (_founder_death_info(s) or {}).get("year"),
        "scholars": round(s.scholars, 2), "artisans": round(s.artisans, 2),
        "directors_extra": round(s.directors_extra, 2),
        # NO "suspicion" FIELD. It was replaced by `scandal` (see core.py: "doing
        # something a society cannot explain is alarming; doing a lot of
        # ordinary things over decades is not"), and the attribute has been set
        # to 0.0 at startup and never written since. Two testers watched it read
        # exactly 0.0 for five hundred years - one with 388 employees and a
        # paved road network - and concluded the social-danger system never
        # fires. What never fired was a vestige. Reporting a dead number every
        # turn is worse than not having it: it teaches the player that a live
        # mechanic is broken.
        "reputation": round(s.reputation, 1),
        "scandal": round(s.scandal, 2), "eminence": round(s.eminence, 2),
        "protection": round(s.protection, 3), "familiarity": round(s.familiarity, 3),
        # HOW EDUCATED THIS SOCIETY IS, AND HOW FAR THAT COULD GO. Answering
        # the user's own question - "can I create a 90%+ literate
        # population" - needs the ceiling shown alongside the current
        # figure, not just the figure alone: a founder watching
        # literacy_general climb with no sense of where it stops cannot tell
        # a slow success from a mechanism that has already maxed out. See
        # SocietyMixin.literacy_ceiling_general/_elite and agrarian_slack
        # (society.py).
        "literacy": {
            "general": round(float(s.civ.get("literacy_general", 0.0)), 3),
            "general_ceiling_now": round(s.literacy_ceiling_general(), 3),
            "elite": round(float(s.civ.get("literacy_elite", 0.0)), 3),
            "elite_ceiling": round(s.literacy_ceiling_elite(), 3),
            "schools_actually_teaching": s._schooling_flow() > 0.0,
            "farm_labour_freed_by_mechanisation": round(s.agrarian_slack(), 3),
        },
        # HOW MUCH OF WHAT YOU RUN HAS LEAKED TO COMPETITORS. See
        # SocietyMixin.diffusion_share/diffusion_index (society.py) for what
        # moves this; it is not yet spent anywhere in this engine's own
        # pricing, only reported, because that spending is another agent's
        # seam to wire in (see that function's own docstring).
        "diffusion_index": round(s.diffusion_index(), 3),
        # A playtester could not tell the difference between technologies the
        # society already had and ones they had earned: about 140 nodes complete
        # in year one and appeared in done_count as if the player had built
        # them. Separate the two, because "you have 140 technologies" and "you
        # have built 3 technologies" are very different situations.
        "done_count": len(s.done),
        "done_granted": len(s.granted & s.done),
        "done_earned": len(s.done - s.granted),
        "active": active,
        # A tester spent 284 years with scholars frozen at 1.0 and artisans
        # plateaued, and wrote that they never found any way to grow either. The
        # remedy was only ever mentioned in a refusal message, so a player who
        # never happened to try a staff-gated project never saw it at all. Staff
        # is not a technical prerequisite, so it appears in no dependency list
        # either. Tell them unprompted.
        "how_to_grow_staff": {
            "scholars": s._staff_advice("scholars"),
            "artisans": s._staff_advice("artisans"),
        },
        "where_the_money_comes_from": s.revenue_sources(),
        "employees": {t: round(v, 2) for t, v in sorted(s.employees.items()) if v > 0.005},
        "employees_total": round(sum(s.employees.values()), 2),
        "household_places_used_of_all": "%.1f of %.1f"
            % (s.headcount(), s.headcount() + max(0.0, s.household_room())),
        "annual_wage_bill": round(s.wage_bill(), 1),
        # WHAT THE PROMPT'S sch/art MEAN. Those two figures count yourself and
        # any hours you have bought, so the prompt can read "sch 1 art 1" on a
        # turn where you employ nobody - and a play tester who saw that beside
        # "EMPLOY: 0 people" reported it as the game losing count. Both are
        # right; they are answering different questions, and this says so.
        "what_you_can_field": (
            "counting yourself and hours you have bought: %.1f scholars and "
            "%.1f craft hands. That pair is what the prompt shows and what "
            "'why' and 'start' test a project against; the count above is "
            "people on your payroll."
            % (s.effective_scholars(), s.craft_hands_available())),
        # FRACTIONS ARE REAL, NOT A DISPLAY GLITCH. A tester reported "1.32
        # artisans" and "0.07 engineers" as if something had gone wrong. It
        # had not: staff grow and decay gradually (hiring phases in, training
        # takes years, attrition is a yearly 3.5%), so at any given moment a
        # trade you have IS a partial year's worth of one more or one fewer
        # person, the same way a company's headcount can be "40.5 FTE". Said
        # only when it would actually be confusing - a whole-number staff
        # needs no footnote.
        "staff_are_fractional_because": (
            None if (abs(s.scholars - round(s.scholars)) < 0.02
                     and abs(s.artisans - round(s.artisans)) < 0.02
                     and all(abs(v - round(v)) < 0.02 for v in s.employees.values()))
            else ("these are continuous full-time-equivalents, not a count of "
                  "whole people: hiring phases in, training takes years, and "
                  "attrition (about 3.5%/yr) trims everyone a little rather "
                  "than dismissing one person at a time. 1.32 artisans is the "
                  "wage and output of one artisan plus a third of another's.")),
        "trades_you_created": sorted(s.trades_created),
        # WHICH OF THOSE THE SOCIETY NOW SUPPLIES ON ITS OWN. See
        # SocietyMixin.advance_society (society.py): once a taught trade has
        # been established long enough, with schools actually running, it
        # stops being only the founder's secret.
        "trades_society_now_has_on_its_own": sorted(s.trades_endemic),
        "mothballed": sorted(getattr(s, "mothballed", set())),
        "policy": dict(s.policy),
        "in_bondage_for_debt": round(getattr(s, "bondage_years_left", 0.0), 1),
        "debt_still_to_work_off": round(getattr(s, "bondage_debt", 0.0), 1),
        # HOW CLOSE YOU ARE TO BEING DESTROYED FOR BEING TOO LARGE, and what
        # changes it. `eminence` was reported as a bare number with no threshold,
        # no trend and no lever, so a player sat at 24.9 against a danger line of
        # 26 with nothing telling them they were one bad year from the end. At a
        # successful late game the equilibrium lands within five per cent of the
        # threshold, which makes the outcome a coin toss decided by noise rather
        # than by anything the player chose. The mechanic is sound and the
        # levers are real - a dispersed academy network cuts it by a third, and
        # getting close to the throne raises it by half - but neither was
        # visible, and an unseen lever is not a choice.
        "prominence": s.eminence_report(),
        "credit_limit": round(s.credit_limit(), 1),
        "debt_interest_rate": round(s.debt_interest_rate(), 4),
        "interest_paid_total": round(getattr(s, "interest_paid", 0.0), 1),
        # WITHOUT THE HISTORY ESSAYS. Each dated hazard now carries a real
        # historical note, several of them a couple of hundred words, and
        # embedding the lot here took one `state full` reply to nearly twenty
        # thousand bytes - the exact wall this reply was split up to stop
        # producing. The numbers stay; the prose lives in `risk`, which is the
        # command you type when you want it.
        "knowledge_risk": _risk_without_the_essays(s.knowledge_risk()),
        # THE OTHER HAZARD THAT ENDS THE RUN, on the same screen as the one that
        # already explains itself. See step() 6.
        "scandal_danger": s.cfg["suspicion_danger"],
        "chance_of_being_denounced_this_year": round(
            max(0.0, (s.scandal - s.cfg["suspicion_danger"]) / 60.0), 4),
        # AND WHICH WAY IT IS GOING. The chance above is computed from where
        # scandal stands now, and the roll happens after a year in which it
        # moves - so the figure is honest about today and says nothing about
        # the step you are about to take. A tester crossed from 21.9 to 29 and
        # was denounced inside one step, having last read "0%".
        "scandal_now": round(s.scandal, 1),
        "scandal_rose_by_last_year": (
            round(s.scandal - s.scandal_last_year, 1)
            if getattr(s, "scandal_last_year", None) is not None else None),
        "years_until_scandal_crosses_the_line": (
            int(max(0.0, (s.cfg["suspicion_danger"] - s.scandal))
                / (s.scandal - s.scandal_last_year)) + 1
            if (getattr(s, "scandal_last_year", None) is not None
                and s.scandal - s.scandal_last_year > 0.05
                and s.scandal < s.cfg["suspicion_danger"]) else None),
        "resource_throttle": round(s.throttle, 3), "throttle_binding": s.binding,
        "forest_ha": round(s.forest_ha, 1),
        "mine_capacity": {m: round(v, 1) for m, v in s.mine_capacity.items()},
        "slaves": s.slaves, "freedmen": s.freedmen,
        "scholars_including_you": round(s.effective_scholars(), 2),
        "founder_ages": not s.cfg.get("immortal", True),
        "goal": None if getattr(s, "fog", False) else s.goal,
        # The NAME, not the id, so it survives fog without handing back the
        # prerequisite crawl the visibility guard exists to stop.
        "goal_in_words": (s.nodes[s.goal]["name"]
                          if getattr(s, "goal", None) in s.nodes else None),
        "goal_reached": s.goal_year is not None, "goal_year": s.goal_year,
        # THE FOG-SAFE VERSION OF final_report's "146 nodes in all; you had
        # 122" - a tester called that the most useful line in the game, and
        # it is withheld until the run ends on purpose: the TOTAL is the size
        # of the tree's own spoiler surface (same reasoning as
        # downstream_count being hidden for a single node, just applied to
        # the whole road at once). So during play this says only how many of
        # the road's nodes you already have, never how many there are in
        # all and never which ones remain - you get a sense of progress
        # without being handed a map.
        "on_the_road_to_the_goal_so_far": (
            _goal_progress_count(s, nodes) if getattr(s, "fog", False) else None),
        "fog_of_war": getattr(s, "fog", False),
        "manual": s.manual, "ended": end_reason is not None, "end_reason": end_reason,
    }
    # A SHORT REPLY BY DEFAULT. `state` had grown to 55 fields and four
    # kilobytes, two of them a hazard briefing repeated verbatim on every single
    # call, and a tester said reading it back "made me double-check arithmetic
    # more than once". The three heaviest blocks now have commands of their own,
    # so you read them when you want them instead of every turn.
    if not full:
        moved = {"knowledge_risk": "risk", "how_to_grow_staff": "labour",
                 "policy": "policy", "where_the_money_comes_from": "money",
                 "training_pending": "labour"}
        elided = []
        for field, where in moved.items():
            if field in out:
                if field == "knowledge_risk":
                    kr = out[field]
                    haz = [h["name"] for h in kr.get("known_hazards_ahead", [])
                           if h.get("in_progress")]
                    out["at_risk"] = {
                        "technologies_you_could_lose": kr.get("technologies_at_risk"),
                        "hedged_by": kr.get("hedged_by"),
                        "happening_now": haz or None,
                        "hazards_still_ahead": len(kr.get("known_hazards_ahead", [])),
                        "in_full": '{"cmd":"risk"}'}
                elif field == "training_pending" and out[field]:
                    out["in_training"] = len(out[field])
                del out[field]
                elided.append('%s -> {"cmd":"%s"}' % (field, where))
        # THE ONE COMMAND FOR "WHY AM I NOT GETTING ON", advertised where a
        # player will see it every turn. Three testers described the same
        # ninety- to two-hundred-and-fifty-year stalls and each found the cause
        # by typing `why` at a guess.
        elided.append('why_you_are_not_getting_on -> {"cmd":"stuck"}')
        out["also_available"] = elided
        out["everything_at_once"] = '{"cmd":"state","full":true}'
    return out


HELP_TOPICS = ("commands", "labour", "economy", "money", "automatic",
               "sittings", "fog", "eminence", "risk", "protection", "stuck",
               "log")


def _agent_help(s, topic=None):
    """Everything a player needs, from inside the game, a topic at a time.

    A tester should not have to be told the commands out of band, and neither
    should a player. But the whole of it at once was four and a half kilobytes
    of JSON before a single move had been made, and testers were spending a
    command just to re-read it. If it is too much for a machine it is far too
    much for a person. So: a short front page, and topics on request.
    """
    fog = getattr(s, "fog", False)
    topic = (topic or "").strip().lower()

    if not topic:
        return {
            "what this is": (
                "You are one person, dropped into a pre-industrial society, "
                "carrying the knowledge of how modern technology works but none "
                "of the industry that makes it. You are playing %s, beginning in "
                "%d. Knowing how a thing works is free. Building it is not: it "
                "takes your own hours, other people's hours, money, materials, "
                "and years."
                % (s.civ.get("name", "a society"), s.cfg["start_year"])),
            "how a turn works": (
                "You begin projects, then advance time. Nothing happens unless "
                "you make it. You are charged for food, rent and appearances "
                "every year whether or not you are building anything."),
            # UNDER FOG TOO. This used to say "there is no score but the state
            # of what you have built", and a normal-play tester spent five
            # hundred years optimising breadth on the strength of it, then met
            # "Getting here from 100 AD is the whole game" on the ending
            # screen. They had the money and the years to reach it. Fog hides
            # the SOCIETY's tree; it has no business hiding what a man who
            # knows how a transistor works is trying to build. The NAME, never
            # the id: naming the id would hand back the prerequisite crawl that
            # the visibility guard exists to stop.
            "what you are trying to do": (
                "Build %s, before the horizon at %d. You know what it is and "
                "what it is for; what you cannot see is the road there, only "
                "the next step of it."
                % (s.nodes[s.goal]["name"].lower() if s.goal in s.nodes else "it",
                   s.end_year)
                if fog else
                "Reach %s, and see the rest of what you can build on the way."
                % s.goal),
            "you arrive alone": (
                "No employees, no slaves, nobody who owes you anything. Anyone "
                'who works for you is hired, taught, commissioned or bought. See '
                '{"cmd":"help","topic":"labour"}.'),
            "the five you need first": {
                "state": "where you stand",
                "available": "what you could begin today",
                "why <id>": "everything known about one thing",
                "start <id>": "begin it",
                "step <years>": "let time pass",
            },
            # THE ACTUAL WALKTHROUGH, and it used to appear in exactly one
            # line of `help commands` and nowhere near the five above. An
            # England player spent about forty minutes guessing before
            # finding it, and said it "trivially reorganized the rest of
            # play" once they had. It is also the answer to the single most
            # requested thing two other players asked for in separate
            # sessions: what the goal still needs, joined to what you could
            # start on it today, instead of two separate reports you cross
            # off against each other by eye.
            **({} if fog else {
                "and the sixth, once you have a goal in mind": (
                    "{\"cmd\":\"path\",\"id\":\"<goal>\"} - everything still "
                    "standing between here and there, AND which of those "
                    "you could start TODAY. This is the walkthrough."),
            }),
            # NAMED OUTRIGHT, not left to be found inside "more" below by a
            # player who has to already suspect it exists. A player who won
            # the whole game reported using specialised commands for a long
            # while without realising `help commands` was a complete index
            # of everything the game can do, and separately flagged `log` -
            # an exact, paginated history of starts, completions, failures,
            # hazards, openings, closures and staffing - as something they
            # wished they had leaned on from the start. Both are true from
            # turn one.
            "the complete command index, and your own exact history": (
                "{\"cmd\":\"help\",\"topic\":\"commands\"} lists every "
                "command the game has, not only the five above - including "
                "'log', 'values', 'money', automation and save/load. "
                "{\"cmd\":\"log\"} is worth checking on its own: a "
                "paginated, exact record of everything that happens from "
                "here on."),
            # See cmd_play's opening screen for why this is not buried in a
            # topic: a finished concern earns nothing until its doors open, and
            # a tester left seven of them shut and went bankrupt in year three.
            "and the one rule that catches everybody": (
                "Finishing something earns you nothing. A concern earns when "
                "you 'open' it, and costs its upkeep only then too. "
                '{"cmd":"ventures"} lists what you know how to run and have '
                "not opened."),
            "when you cannot see why you are not getting on": '{"cmd":"stuck"}',
            # Which of the two front ends is reading. `play` types words and
            # `agent` sends JSON, and telling a person at a keyboard to send
            # one JSON object per line - which this did - is telling them to
            # do something the program they are using does not ask for.
            "how to send a command": (
                'One command per line, in plain words: "available", '
                '"step 5", "hire smith 2", "why fud_wheelbarrow". Pasting a '
                'JSON command works too, if you happen to have one.'
                if TYPED_HINTS else
                'One JSON object per line on standard input, for example '
                '{"cmd":"available"} or {"cmd":"step","years":5}. Each reply is '
                'one JSON object.'),
            "more": {t: '{"cmd":"help","topic":"%s"}' % t for t in HELP_TOPICS},
        }

    if topic in ("commands", "command", "all"):
        return {"commands": {
            "state": "where you stand; add full:true for every field",
            "available": "what you could begin today, summarised by subject; "
                         "add subject, find, afford, limit/offset, or all:true; "
                         "add sort (price/hours/years/earns/upkeep/risk/alpha/"
                         "fewest_missing) and reverse to change the order, and "
                         "page with offset/heard_offset all the way to the end. "
                         "fewest_missing is about the heard-of list only - it "
                         "orders by how few of a thing's OWN prerequisites are "
                         "still missing, not by distance to any goal you have "
                         "set; see 'path <goal>' for that, once fog is off",
            "why <id>": "everything known about one thing",
            "start <id>": "begin work on something",
            "stop <id>": "abandon it, losing what you have spent",
            "rush": "start everything you could begin today in one go, "
                    "highest-leverage first; add limit:N to cap it",
            "step <years>": "let time pass",
            "money": "the whole ledger: what comes in, what goes out",
            "values": "what this society actually believes, as numbers - the "
                     "same fields a completion's 'changes the society' line "
                     "names",
            "log": "your own history - what you did and what followed, most "
                   "recent first; add failures:true, find, since/before, "
                   "order, offset. Never the whole thing in one go",
            "quote <what>": "what something would cost before you commit to it; "
                            'so far {"cmd":"quote","what":"mine",'
                            '"material":"coal","n":500}',
            "close <material>": "shut your own workings down and stop paying to "
                                "keep them standing",
            "risk": "what history is about to do to you, and what blunts it",
            "labour": "who you employ and what trades exist here",
            "hire / fire / train / commission": "see the labour topic",
            "buy": "forest, nitre, mine, slaves, or manumit; see the economy topic",
            "work <trade> <hours>": "do an ordinary job for ordinary pay",
            "bounty <id>": "pay someone else to solve it instead",
            "open <id>": "start actually running something you have worked out "
                         "how to do; until you do, it earns nothing and costs "
                         "nothing",
            "ventures": "what you are running, and what you know how to run and "
                        "have not opened",
            "mothball <id> / restore <id>": "shut a finished work down, or reopen it",
            "bribe <amount>": "spend money to reduce a scandal",
            "policy": "every automatic behaviour, and a switch for each",
            "path <id>": ("not available under fog of war" if fog
                          else "the route to one thing: everything still "
                               "standing between here and there, AND which "
                               "of those you could start today - the "
                               "walkthrough, effectively; try 'path' on "
                               "your goal first"),
            "score": "what you are optimising: each ending-score component, "
                    "raw and weighted, any time - not only at the end; the "
                    "technology-coverage share stays withheld under fog "
                    "until the run is over, the same way the goal's own "
                    "road total does",
            "save <file> / load <file>": "write or read a game",
            "help": "this; add a topic",
            "quit": "stop",
        }}

    if topic == "labour":
        return {"labour": (
            "You arrive alone. Everything anyone else does for you is hired by "
            "the year, bought as a single job, taught by you from nothing if "
            "this society has no such trade, or bought outright as a person. "
            "Trades are NOT interchangeable: a smith is not a scribe, and a "
            "project asking for an engineer cannot be built by smiths however "
            "many you have."),
            "commands": {
                "labour": 'who exists here and what they cost; add "trade" for one',
                "hire": '{"cmd":"hire","trade":"smith","n":3} - paid every year, '
                        "whether you have work for them or not",
                "fire": '{"cmd":"fire","trade":"smith","n":1}',
                "train": '{"cmd":"train","trade":"machinist","n":2} - teaches a '
                         "trade that does not exist here, out of your own hours",
                "commission": '{"cmd":"commission","trade":"smith","hours":400} - '
                              "buy a job rather than a person",
            }}

    if topic == "money":
        # `help money` and `help economy` printed the same page, and both were
        # listed as separate topics, so a play tester read one and expected
        # something else from the other. Money is where it comes from and where
        # it goes; economy is what you can buy with it.
        return {"where it comes from": (
            "Your practice - the trade this society already had, which you can "
            "do from the first day - plus every concern you have OPENED, plus "
            'what your own workshop sells. {"cmd":"money"} itemises all of it '
            "and the rows sum to the revenue above them."),
            "your practice pays less than the tree quotes": (
                "About a third: one person in a rented room is not an organised "
                "concern, and that gap does not close with time. Selling your "
                "hours for wages takes another bite, because you cannot be in "
                "two places."),
            "a concern you open starts small": (
                "It reaches its full figure over about three years."),
            "where it goes": (
                "Living and appearances, wages, the upkeep of what you are "
                "RUNNING, mines standing whether or not you work them, and "
                "interest on arrears."),
            "money costs money to hold": (
                "Living and appearances is about a sixtieth of your capital a "
                "year, on top of a subsistence floor and your household, plus "
                "a fixed sum for each rank you hold. In a patronage society a "
                "man visibly richer than he lives is suspected, and a man "
                "seeking standing must spend on it. An idle million bleeds "
                "about fifteen thousand a year doing nothing, which is why "
                "money sitting still is money going backwards."),
            "what you can buy": '{"cmd":"help","topic":"economy"}',
            "debt": "You may spend past what you have, as far as somebody will "
                    "lend you and no further. Arrears cost interest."}

    if topic in ("economy", "buy"):
        return {"the ledger": '{"cmd":"money"} itemises what comes in and what '
                              "goes out, including where the income comes from",
                "buy forest": '{"cmd":"buy","what":"forest","n":100} hectares of '
                              "coppice, which is where charcoal comes from",
                "buy nitre": '{"cmd":"buy","what":"nitre","n":20000} square metres of nitre bed. Saltpetre is made, not mined, and nothing else supplies it.',
                "buy mine": '{"cmd":"buy","what":"mine","material":"coal","n":500} '
                            "tonnes a year of your own workings; it takes years "
                            "to sink, and it costs to keep standing whether or "
                            "not you use it. ASK THE PRICE FIRST with "
                            '{"cmd":"quote","what":"mine","material":"coal",'
                            '"n":500}, and close it with '
                            '{"cmd":"close","material":"coal"}. Materials: '
                            + Sim.mine_catalog_hint(Sim),
                "buy slaves": '{"cmd":"buy","what":"slaves","n":5}. This is '
                              "available because it was the ordinary condition of "
                              "production in most of these societies, and a model "
                              "that hides it lies about the cost of everything.",
                "manumit": '{"cmd":"buy","what":"manumit","n":5} frees people you '
                           "hold. They then work better, and it is the decent thing.",
                "debt": "You may spend past what you have, as far as somebody will "
                        "lend you and no further. Arrears cost interest. "
                        "Money in arrears also stalls HOUR progress on work "
                        "you already have in hand: a project still owing "
                        "money draws on what you could raise this year, and "
                        "if that is nothing, its hours mostly go to waste "
                        "rather than into the work - not just the money, the "
                        "founder-hours too. 'state' shows which active "
                        "project this is happening to and names the cause "
                        "(why_underfunded); a project already fully paid is "
                        "never affected by this, whatever else is in "
                        "arrears."}

    if topic in ("automatic", "policy"):
        return {"what happens on its own": (
            "Some things the engine will do for you if you let it: grow the "
            "staff, teach trades, sink mines, buy woodland, shut down what you "
            "cannot pay for, pay off a scandal. Every one is a switch you "
            "control, and every one can be done by hand instead."),
            "see them": '{"cmd":"policy"}',
            "change one": '{"cmd":"policy","set":{"auto_hire":true}}'}

    if topic in ("sittings", "save", "load"):
        return {"playing across several sittings": (
            "Pass --session FILE on the command line. The game is written to "
            "that file after every command and read back when you start again, "
            "so you do not need to hold a process open or write a script.")}

    if topic in ("stuck", "blocked"):
        return {"stuck": (
            "Type 'stuck' at any time. It answers, in one place, why you are "
            "not getting on: what each piece of work in hand is waiting for, "
            "whether anything is startable and affordable, whether a raw "
            "material is throttling everything, whether you have room for more "
            "people, and how deep in arrears you are."),
            "the usual answers": (
                "hours (you only have so many), money (you can raise only so "
                "much), a trade this society does not have, a material nobody "
                "is selling, or room for the people it would take."),
            "where to look next": (
                '{"cmd":"available"} for what you could begin, '
                '{"cmd":"labour"} for people, {"cmd":"money"} for the ledger.')}

    if topic in ("log", "history", "diary"):
        return {"log": (
            "Your own history, in the order it happened: what you started, "
            "what finished, what failed and why, a concern opening or "
            "closing, staff hired or let go, a hazard landing, money running "
            "out. Type 'log' alone for the twenty most recent lines."),
            "see only the bad news": "'log failures'",
            "search it": "'log find plague'",
            "a year range": "'log since 300 before 400'",
            "read forward from the start instead of back from now": "'log oldest'",
            "page through to the end": "'log offset 20'",
            "why it never dumps everything": (
                "a long run's history runs to tens of thousands of lines, "
                "more than anyone - human or script - can read in one reply, "
                "so this always pages and there is no way to ask for all of "
                "it at once."),
            "fog": ("respects it: a line cannot go on naming something you "
                    "have since forgotten or never heard of just because it "
                    "was visible the year it happened.")}

    if topic in ("protection", "standing"):
        return {"protection": (
            "How far your standing shields you when you produce an effect "
            "nobody can explain. It decides whether a strange result out of "
            "your workshop is read as learning or as sorcery, and it is the "
            "only thing money can buy here directly."),
            "what raises it": (
                "A patron, citizenship, a licensed collegium, land endowed in "
                "public, a school, and your reputation - and spending on "
                "advocacy and piety, which is what `bribe` does when you have "
                "no scandal to answer. Protection caps at 92% in total, and "
                "money is only 30 points of that however much you spend - a "
                "break tester read the 92 as the ceiling on bribery, offered a "
                "million, and stopped at the same 32% a hundred had bought. "
                "The rest has to be earned."),
            "what it does NOT protect you from": (
                "Eminence. Being too large is the one hazard no protection "
                "touches; see {\"cmd\":\"help\",\"topic\":\"eminence\"}."),
            "where to watch it": '{"cmd":"state"} shows it under STANDING'}

    if topic in ("eminence", "prominence"):
        return {"eminence": (
            "The one hazard no patron, no bribe and no reputation protects you "
            "from, because it IS reputation. It rises with how well known you "
            "are and how visibly rich, it is multiplied by standing close to "
            "the throne, and past the danger line it rolls every year for your "
            "ruin. Sejanus was the most protected man in Rome until the morning "
            "he was not."),
            "what lowers it": (
                'One command does, and its price is real: {"cmd":"withdraw"} '
                "halves your prominence now and gives up half the reputation "
                "you hold above what your work by itself is worth. Reputation "
                "here is your credit limit, your protection, the wages you must "
                "pay and the pace of your projects, so you cannot get small and "
                "stay grand - and you cannot do it twice in twelve years, "
                "because being seen to retire repeatedly is not retiring."),
            "what survives it": (
                "A wide, dispersed institution - academy_network makes the "
                "hazard itself smaller, and corpus_dispersed means what you "
                "know is in too many places to burn. Being merely rich and "
                "merely famous is the dangerous combination."),
            "and time helps": (
                "A city gets used to you. The longer you have been a fixture "
                "and the more of your work it has already seen, the less "
                "alarming the next thing is - the same familiarity that decays "
                "the alarm your work causes takes up to a third off this."),
            "if it lands": (
                "45% of the time it is a confiscation and a forced retirement, "
                "35% your patron is destroyed in somebody else's quarrel, and "
                "20% it is the end of the run. `state` shows both figures."),
            "where to watch it": '{"cmd":"state"} shows it under STANDING'}

    if topic in ("risk", "hazards"):
        return {"risk": ("What history is about to do to you, with dates, and "
                         "what you have built that blunts each one. Every "
                         "hazard is fightable and the numbers are real."),
                "see it": '{"cmd":"risk"}'}

    if topic == "fog":
        return {"fog of war": (
            "ON. You can see what you have built, what you could begin today as "
            "a one line summary, and things you have heard of but cannot yet "
            "begin. You cannot see where anything leads, and there is no way to "
            "view the whole tree." if fog else "OFF. You can see the whole tree.")}

    return {"no such topic": topic, "topics": list(HELP_TOPICS)}


SUBJECTS = {
    "00": "the briefing", "01": "the world as it is", "03": "society and politics",
    "10": "metallurgy", "20": "chemistry", "30": "glass and optics",
    "40": "power and precision", "50": "electricity", "55": "semiconductors",
    "60": "mathematics and method", "70": "medicine and biology",
    "75": "agriculture and food", "76": "farming, in depth",
    "80": "printing and information", "85": "roads, bridges and canals",
    "86": "transport, in depth", "87": "construction", "88": "signals and media",
    "89": "the remaining arts", "90": "textiles", "91": "the household",
    "95": "expeditions", "96": "finance", "97": "military",
    "98": "power stations",
}


def _subject_of(n):
    """A readable heading for a node, from its knowledge module.

    There are 241 distinct `cat` values and 26 knowledge modules. The modules
    are the ones a person would recognise as subjects.
    """
    kb = (n.get("kb") or "").split("#")[0]
    return SUBJECTS.get(kb[:2], "everything else")


def _staff_short(n):
    """"2s1a" - the standing staff a project needs, in a table cell.

    A play tester picked six projects out of `available` on cost and hours,
    started all six, and found every one of them waiting on people: the row
    carried nine numbers and not one of them was the staff, which lived only
    in `why`, one node at a time. Two characters a trade is enough to see it
    while scanning.
    """
    bits = ""
    if n["sch"]:
        bits += "%gs" % round(n["sch"], 1)
    if n["art"]:
        bits += "%ga" % round(n["art"], 1)
    return bits or "-"


def _short_of_staff(s, n):
    """True when you could NOT staff this today. Marks the row with a *.

    THE SAME MEASURE start_reason USES. This compared against self.artisans
    alone while the gate counts the founder's own hands and anything you have
    under contract, so a break tester read "* means you do not have them yet -
    the work waits" beside projects that started and built at full speed with
    nobody on the payroll at all. A marker that contradicts the gate it is
    describing is worse than no marker.
    """
    return bool(n["art"] > s.craft_hands_available() + 1e-9
                or n["sch"] > s.effective_scholars() + 1e-9)


def _staff_fields(s, n):
    """The two staff keys, present only when they SAY something.

    A row that needs nobody, or that you can already staff, carries neither.
    `available` has a size budget - it was 165 kilobytes once - and forty
    bytes of "needs_staff":"-","short_of_staff":false on every one of two
    hundred rows is eight kilobytes spent saying nothing.
    """
    out = {}
    short = _staff_short(n)
    if short != "-":
        out["needs_staff"] = short
        if _short_of_staff(s, n):
            out["short_of_staff"] = True
    return out


def _coarse_round(x):
    """Round a fogged revenue guess to a figure a person would actually say
    aloud - "three to five hundred a year", not "347.2 to 511.8 den/yr".
    Real-looking precision on a number that is, by construction, not the
    truth would read as measured rather than guessed, which defeats the
    point of guessing at all.
    """
    x = max(0.0, x)
    if x == 0:
        return 0.0
    step = 5 if x < 100 else 25 if x < 1000 else 100 if x < 10000 else 500
    return round(x / step) * step


def _revenue_known_exactly(s, k):
    """Have you actually RUN this long enough to know what it earns?

    Granted knowledge (k in s.granted) is answered True unconditionally: it
    is part of the persona you arrived with, not a prospect you are sizing
    up, so there is nothing to guess about. Anything else you have finished
    needs a few years of its own ledger behind it - "a few years" taken
    literally, three - before the figure stops being a forecast and starts
    being a fact; done_year missing (a bookkeeping gap, not a fresh
    completion) defaults to True rather than trapping a player in a fog
    the engine itself cannot explain.
    """
    if k not in s.done:
        return False
    if k in s.granted:
        return True
    started = s.done_year.get(k)
    if started is None:
        return True
    return (s.year - started) >= 3


def _fog_revenue_estimate(s, k):
    """What `available` and `why` show for EARNS/YR on a thing you have
    never run, under fog of war: a range, not the true figure.

    The user who asked for this put the question plainly: "should you
    really be able to tell how much money you would make from researching
    something? Shouldn't the payback be something you don't know until
    after research?" A break tester's own numbers say why it matters: under
    fog they built 540 technologies using EARNS/YR as, in their own words,
    "the only usable heuristic", and reached 95 of the 146 nodes on the road
    to the goal that way - not because they had worked out the tree, but
    because the exact payback figure told them which side branches paid and
    steered them straight past the spine. Real payback is a thing you learn
    by running a concern for a few years, not by reading a number off a
    prospectus before you have so much as broken ground.

    Two things this must never be:
      - RE-ROLLED. A fresh call to self.rng here would answer differently on
        two consecutive looks at the same screen, and would also consume a
        draw from the SAME generator the simulation itself steps with - so
        merely asking `why` twice would change how the game plays out.
        Read-only commands must not touch self.rng. Instead this hashes
        something stable for the LIFE of one game (this civilisation, this
        goal, this starting purse) together with the node's own id, so the
        same game asked the same question twice gets the same answer, and a
        different game is not guaranteed to.
      - A TIGHT SYMMETRIC BAND ON THE TRUTH. "400 +/- 50" tells you 400 just
        as plainly as the bare number did, because the midpoint gives it
        away. The low and high bounds below are pulled by two independently
        drawn fractions, so the middle of the printed range is not, in
        general, anywhere near the real figure, and averaging the two bounds
        does not recover it.
    It DOES widen with how well this node's own numbers are attested: `conf`
    is already in the tree data for exactly this reason (A well attested, B
    probable, C the author's estimate), so a guess about a well-documented
    Roman trade is tighter than a guess about a Han institution nobody wrote
    down the takings of, the same as a historian's own uncertainty would be.
    """
    n = s.nodes[k]
    real = n["rev"]
    if real <= 0:
        return None          # nothing to estimate; a non-earner is a non-earner under fog too
    key = "%s|%s|%.1f|%s" % (s.civ.get("id") or s.civ.get("name") or "civ",
                             getattr(s, "goal", "") or "",
                             s.cfg.get("start_capital", 0.0), k)
    h = hashlib.sha256(key.encode("utf-8")).digest()
    half = {"A": 0.30, "B": 0.55}.get(n.get("conf"), 0.85)
    lo_frac = 0.35 + (h[0] / 255.0) * 0.55
    hi_frac = 0.35 + (h[1] / 255.0) * 0.90
    lo = _coarse_round(real * (1.0 - half * lo_frac))
    hi = _coarse_round(real * (1.0 + half * hi_frac))
    if hi <= lo:
        hi = lo + (5 if lo < 100 else 25 if lo < 1000 else 100)
    return [lo, hi]


def _brief(s, nodes, k, fog):
    """One row of `available`.
    
    IT USED TO CARRY COST, HOURS, YEARS AND RISK AND NOTHING ELSE, and a
    normal-play tester who ran the game to its horizon wrote that none of those
    decide anything: what decides is what a thing EARNS, what it costs you every
    year afterwards, and how much else rests on it - all of which lived only in
    `why`, one node at a time. They found the two nodes the whole opening turns
    on by scripting a hundred `why` calls, and by the end were scripting four
    hundred and sixty. "Competent play degenerates into writing a scraper" is a
    fair description of an interface that hides its own decisive numbers.
    """
    n = nodes[k]
    # The SHORT band in a table row. `why` gets the long sentence, because it
    # is explaining one thing; a row is a row, and eleven copies of "nothing
    # else; this is worth having for itself" is half a kilobyte of a reply that
    # has a size budget to keep.
    rests = _rests_band(downstream_count(nodes, k)).split(";")[0]
    if fog:
        # A ROW HERE IS ALWAYS A THING YOU HAVE NOT BUILT - `available` lists
        # what you could BEGIN, never what you already have - so there is no
        # "have you run it long enough" case to check; see
        # _revenue_known_exactly for the one that `why` does need, because
        # `why` also answers for things you finished years ago.
        _est = _fog_revenue_estimate(s, k)
        return {"id": k, "name": n["name"],
                "cost": round(s.project_cost(k), 1),
                "your_hours": n["ph"],
                "least_years": n["yrs"],
                # effective_risk, NOT n["risk"]. Once a project has failed
                # once, retry learning means the tree's bare figure is no
                # longer what the dice use, and quoting it would understate
                # what a second attempt is worth - the opposite of the lie
                # this screen used to tell about failure costing nothing.
                "chance_of_failure": s.effective_risk(k),
                # WHAT A FAILURE COSTS, not only how likely one is. A failure
                # takes a flat 40% of the money and sets 40% of the hours to
                # do again; the rate was on the screen and the sum never was,
                # so three players in a row read a single-digit risk as a
                # small thing and were not expecting what it took off a large
                # project. Zero when the work cannot fail, so nothing invents
                # a danger that is not there.
                "failure_costs": (round(s.project_cost(k) * 0.4, 1)
                                  if n["risk"] else 0.0),
                "failure_costs_hours": round(n["ph"] * 0.4, 1) if n["risk"] else 0.0,
                "earns_per_year": _est if _est is not None else round(n["rev"], 1),
                "costs_per_year_after": round(n["up"], 1),
                "how_much_rests_on_this": rests,
                **_staff_fields(s, n)}
    return {"id": k, "name": n["name"], "tier": n["tier"], "cat": n["cat"],
            **_staff_fields(s, n),
            "cost": round(s.project_cost(k), 1), "founder_hours": n["ph"],
            "calendar_floor_years": n["yrs"], "risk": s.effective_risk(k),
            "earns_per_year": round(n["rev"], 1),
            "costs_per_year_after": round(n["up"], 1),
            # _downstream_of, NOT downstream_count. The cached bitmask index
            # in data.py follows hard prerequisites only, and it must: adding
            # req_any options to it introduces real CYCLES (junction_transistor
            # -> silicon_path -> point_contact_transistor -> junction_transistor
            # is one of four), and a bitmask DFS that assumes a DAG runs out of
            # memory on them. The tree is acyclic on `pre` and is not acyclic
            # on `pre` plus substitutions. This walk carries a visited set, so
            # it is safe on the real graph, and it is the one place the number
            # is shown to a player as "nothing depends on this".
            "downstream_count": len(_downstream_of(k, nodes))}


def _full_entry(s, nodes, k, fog):
    e = _brief(s, nodes, k, fog)
    n = nodes[k]
    if fog:
        e["summary"] = s.fog_summary(k)
        if n["lab"]:
            e["trades_needed"] = sorted(n["lab"])
    else:
        e["prerequisites"] = n["pre"]
        # See strip_self_play_advice: a node's own note is data written by a
        # designer ranking it against the rest of the tree, not something the
        # founder in the story could know, and that stays cut whether or not
        # fog is on - see the block comment in fog.py.
        e["note"] = strip_self_play_advice(n["note"])
    # THE HONEST TOTAL, not the risk and the floor left for the player to
    # multiply by hand - and only HERE, on the full per-node entry, not on
    # _brief's own compact digest rows (cheapest_six, most_rests_on_these):
    # those feed a summary a play tester already flagged as a reply budget
    # to keep inside, and this number is worth a few extra bytes on the one
    # row you asked to actually look at, not on every row of a six-wide
    # sampler. See expected_calendar_years' own docstring (projects.py): it
    # is >= the floor above, strictly more once risk is above zero, and it
    # is why a 45%-risk, 4-year-floor node is not a 4-year project.
    if n.get("risk"):
        e["expected_calendar_years_with_retries"] = round(
            s.expected_calendar_years(k), 2)
    return e


# EVERY SORT A PLAYER ASKED FOR, one table. Both the paged `available` list
# and the "heard of but cannot begin" list under it were hard-wired to one
# order each (cost, and nearest-first) with no way to ask for another, and a
# play tester paging through "632 more, nearest first" asked outright how to
# sort by what a thing earns instead of digging through cost order for it.
# One table serves both lists so a player only has to learn one vocabulary:
# {"cmd":"available","sort":"risk"} and the heard-of block below it sort the
# same way.
_SORT_KEYS = {
    "price": lambda s, n, k: s.project_cost(k),
    "cost": lambda s, n, k: s.project_cost(k),
    "hours": lambda s, n, k: n[k]["ph"],
    "years": lambda s, n, k: n[k]["yrs"],
    "earns": lambda s, n, k: n[k]["rev"],
    "revenue": lambda s, n, k: n[k]["rev"],
    "upkeep": lambda s, n, k: n[k]["up"],
    "risk": lambda s, n, k: n[k]["risk"],
    "alpha": lambda s, n, k: n[k]["name"].lower(),
    "alphabetical": lambda s, n, k: n[k]["name"].lower(),
    "name": lambda s, n, k: n[k]["name"].lower(),
    # FEWEST_MISSING: fewest of its OWN direct prerequisites still missing -
    # i.e. closest to becoming startable, never distance to whatever goal is
    # set. Every node in the STARTABLE list has zero missing by definition,
    # so this only discriminates the heard-of list; asking for it on the
    # startable list is harmless, not an error, and falls back to id order
    # there, which is exactly what misled a goal-directed player: with the
    # goal set to the junction transistor, "available sort nearest" kept
    # opening with agriculture, because id order is what "no missing
    # prerequisites to discriminate by" falls back to, and nothing about the
    # name "nearest" said it meant anything other than "nearest to your
    # goal". `path <goal>` answers that real question - "what could I start
    # today toward this" - without leaking the hidden tree; this key never
    # did and was never trying to, so it is renamed to say what it actually
    # measures. "near"/"nearest" still work, for any script already using
    # them, but no longer appear in the advertised list below.
    "fewest_missing": lambda s, n, k: sum(1 for p in n[k]["pre"] if p not in s.done),
    "near": lambda s, n, k: sum(1 for p in n[k]["pre"] if p not in s.done),
    "nearest": lambda s, n, k: sum(1 for p in n[k]["pre"] if p not in s.done),
}

_SORT_KEY_NAMES = ("price", "hours", "years", "earns", "upkeep", "risk",
                   "alpha", "fewest_missing")


def _agent_available(s, nodes, cmd=None):
    """What you could begin today.

    THIS USED TO RETURN EVERYTHING. At year 250 that was 559 entries and 165
    kilobytes in a single reply, and even at the start it was 78 entries and 21
    kilobytes: a wall nobody reads, which testers dealt with by grepping their
    own scrollback. If it is too much for a machine it is far too much for a
    person. So the default is now a digest by subject, and you ask for the part
    you want.
    """
    cmd = cmd or {}
    fog = getattr(s, "fog", False)
    # ONE memo for the whole sweep, not one per node. Under fog, checking
    # whether a deep node can start asks whether each of its missing
    # prerequisites is even visible, which asks the same question about
    # THEIR missing prerequisites, and neighbouring nodes in `order` share
    # most of that ancestry. Recomputing it fresh per node, 2,800 times, is
    # what made a single `available` call under fog on norse_900ad take
    # upward of a minute; sharing the memo across the sweep makes it once
    # per node actually touched. See is_visible()'s docstring.
    _memo = {}
    ok = [k for k in s.order if s.can_start(k, _memo=_memo)]
    # Anything the society is about to be handed for nothing is not a decision.
    ok = [k for k in ok
          if not (nodes[k]["tier"] == 0 and nodes[k]["ph"] == 0
                  and nodes[k]["_total_cost"] <= 1
                  and not s._is_foreign_institution(k))]

    # QUOTES ARE THE NATURAL INSTINCT for a subject with a space in it, and
    # `available "power and precision"` silently matched nothing while the
    # unquoted form worked. Strip them rather than failing quietly.
    want_subject = (cmd.get("subject") or cmd.get("group") or "").strip()
    want_subject = want_subject.strip('"\'').lower()
    find = (cmd.get("find") or cmd.get("search") or "").strip().strip('"\'').lower()
    show_all = bool(cmd.get("all"))
    try:
        limit = int(cmd.get("limit", 0))
    except (TypeError, ValueError):
        limit = 0
    try:
        offset = max(0, int(cmd.get("offset", 0)))
    except (TypeError, ValueError):
        offset = 0
    afford = float(cmd.get("afford")) if str(cmd.get("afford", "")).strip() not in ("", "None") else None
    sort_by = str(cmd.get("sort") or "").strip().lower()
    _sort_fn = _SORT_KEYS.get(sort_by)
    reverse = bool(cmd.get("reverse"))

    sel, why_these = ok, None
    if find:
        sel = [k for k in ok if find in k.lower() or find in nodes[k]["name"].lower()]
        why_these = "matching %r" % find
    elif want_subject:
        sel = [k for k in ok if want_subject in _subject_of(nodes[k]).lower()]
        why_these = "in %r" % want_subject
        if not sel:
            # THE SUMMARY COUNTED IT AND THE FILTER DID NOT. `available` listed
            # "society and politics 1 1,200 1,200 1" and `available society and
            # politics` answered "nothing in it", because the one item was
            # already active. Say which, rather than appearing to disagree with
            # the line above it.
            _busy = sorted(k for k in nodes
                           if want_subject in _subject_of(nodes[k]).lower()
                           and (k in s.active or k in s.done)
                           and (not fog or s.is_visible(k)))
            if _busy:
                why_these += (" - nothing left to begin; you already have or "
                              "are working on " + ", ".join(_busy[:4]))
    if afford is not None:
        sel = [k for k in sel if s.project_cost(k) <= afford]
    # PAGE IN THE ORDER YOU DISPLAY. Each page was sorted by cost as it was
    # printed, but the pages were CUT from strategy order, so a break tester
    # asking for the cheapest work found it at item 31 - and the first page was
    # a cost-sorted view of an arbitrary thirty. Sort the selection, then cut.
    # DEFAULT COST, BUT NOT THE ONLY CHOICE. A play tester paging through
    # "632 more" asked how to see it sorted by what a thing earns instead of
    # digging cost order for it; `sort` picks any column, `reverse` flips it.
    if find or want_subject or limit or offset or show_all or afford is not None:
        if _sort_fn:
            sel = sorted(sel, key=lambda k: (_sort_fn(s, nodes, k), k), reverse=reverse)
        else:
            sel = sorted(sel, key=lambda k: (s.project_cost(k), k))

    heard, heard_more, heard_from = [], 0, 0
    if fog:
        # CLOSEST FIRST, NOT ALPHABETICALLY. This sorted by id and cut at 25, so
        # the list a player reads was always the same handful of things
        # beginning with a, b and c, however many they had heard of and however
        # near the rest were. A play tester noticed it stopped around "c" and
        # had no way to page past it. Fewest missing prerequisites first is the
        # order that answers the question the list is actually asked: what is
        # nearly within reach?
        _heard_all = [k for k in getattr(s, "revealed", set())
                      if k not in s.done and k not in s.active
                      and not s.start_reason(k)[0]]
        # THE SAME SEARCH, OR NOTHING. This block used to ignore `find` and
        # `subject` entirely and print its usual nearest-first twenty-five
        # regardless of what was typed, so `available find zzz` - a search
        # that matched nothing startable - still dumped seven things the
        # player had never asked about, under a heading that gave no sign any
        # of it was unrelated to the search. A search that matches nothing is
        # supposed to look like nothing, and a search that matches something
        # heard-of-but-not-yet-startable is exactly the case this list exists
        # to answer, so the fix is to search it rather than hide it outright.
        if find:
            _heard_all = [k for k in _heard_all
                          if find in k.lower() or find in nodes[k]["name"].lower()]
        elif want_subject:
            _heard_all = [k for k in _heard_all
                          if want_subject in _subject_of(nodes[k]).lower()]
        # NEAREST-FIRST BY DEFAULT, but the same `sort`/`reverse` a player set
        # on the startable list applies here too - one vocabulary for both
        # halves of the screen, per the sort table's own docstring.
        if _sort_fn:
            _heard_all.sort(key=lambda k: (_sort_fn(s, nodes, k), k), reverse=reverse)
        else:
            _heard_all.sort(key=lambda k: (sum(1 for p_ in nodes[k]["pre"]
                                               if p_ not in s.done),
                                           nodes[k]["tier"], k))
        # PAGEABLE, and it says when it is cut. This was a silent slice at 25
        # in a game where a play tester had a thousand nodes in play: no note
        # that it was truncated and no way to see the rest. `heard_offset`
        # pages it, the same way `offset` pages the startable list.
        try:
            _hoff = max(0, int(cmd.get("heard_offset", 0)))
        except (TypeError, ValueError):
            _hoff = 0
        heard = _heard_all[_hoff:_hoff + 25]
        heard_more = max(0, len(_heard_all) - _hoff - len(heard))
        heard_from = _hoff
    heard_block = [{"id": k, "name": nodes[k]["name"],
                    "why_not": s.start_reason(k)[1]} for k in heard]

    # A LIST was asked for: a subject, a search, an explicit page, or everything.
    if find or want_subject or limit or offset or show_all or afford is not None:
        # THIRTY AT A TIME WAS A BARE NUMBER; DEFAULT_AVAILABLE_LIMIT IS THE
        # SAME NUMBER, now the one a player can raise from the Options
        # screen - see its own comment, near TYPED_HINTS - instead of typing
        # limit:N by hand on every page of a long search or subject list.
        page = sel if show_all else sel[offset:offset + (limit or DEFAULT_AVAILABLE_LIMIT)]
        out = {"ok": True, "count": len(sel), "of_everything_startable": len(ok),
               # The same figure the digest carries, so a paged list can mark
               # what you could not raise today. See _cost_marker.
               "you_could_raise_for_a_project": round(s.spending_power("start"), 1),
               "showing": ("nothing%s" % ((" " + why_these) if why_these else "")
                           if not page else
                           "%d-%d%s" % (offset + 1, offset + len(page),
                                        (" " + why_these) if why_these else "")),
               "available": [_full_entry(s, nodes, k, fog) for k in page]}
        if not page:
            # "1-0 matching 'furnace'" over an empty table is a range that
            # cannot exist, printed where an answer should be. Say the answer
            # instead - and, under fog, say only what a player is entitled to
            # know: that nothing they can begin TODAY matches. Whether the
            # thing exists at all in the tree is exactly what fog withholds.
            # SAY WHAT IT SEARCHED. A play tester read `available find cap_`
            # coming back empty as the search ignoring ids - it does not; it
            # searches both, and only among what is startable NOW, which at
            # that point in their run was the true answer.
            out["nothing_matched"] = (
                "Nothing you could begin today matches that. This looks at both "
                "ids and names, but only among what you could start now."
                + (" That does not mean there is no such thing; it means "
                   "nothing in front of you right now answers to it. Try a "
                   "shorter word, or a subject: 'available metallurgy'."
                   if fog else
                   " Try a shorter word, or a subject: 'available metallurgy'."))
        # DISCOVERABLE, not just possible. `help available` says this too, but
        # a naive player reading the table itself should not have to go
        # looking for the one line that explains how to change what they are
        # looking at.
        out["sorted_by"] = sort_by if _sort_fn else "cost"
        if reverse:
            out["sorted_by"] += ", reversed"
        out["to_sort_or_page_differently"] = (
            "add a 'sort' of %s, and 'reverse' to flip it; 'offset'/'limit' "
            "page the list you could start, 'heard_offset' pages the "
            "heard-of one below it - all the way to the end."
            % ", ".join(_SORT_KEY_NAMES))
        if not show_all and offset + len(page) < len(sel):
            out["more"] = ('%d more; ask again with "offset": %d'
                           % (len(sel) - offset - len(page), offset + len(page)))
        if fog and heard_block and offset == 0:
            out["heard_of_but_cannot_begin"] = heard_block
            if heard_more:
                out["and_more_you_have_heard_of"] = (
                    "%d more, %s; ask again with heard_offset %d"
                    % (heard_more,
                       ("sorted by %s%s" % (sort_by, " reversed" if reverse else ""))
                       if _sort_fn else "fewest missing prerequisites first, "
                                        "which is not the same as nearest to "
                                        "your goal",
                       heard_from + len(heard_block)))
        return out

    # DEFAULT: the digest.
    groups = {}
    for k in ok:
        g = groups.setdefault(_subject_of(nodes[k]), [])
        g.append(k)
    # The AFFORD column is about STARTING work, so it uses the rule `start`
    # uses. It used the purchase rule, which is why the hint under the table
    # offered "available afford 1,083" for a player `start` would have let
    # commit 1,767. See Sim.spending_power.
    purse = s.spending_power("start")
    rows = []
    for name, ks in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        costs = sorted(s.project_cost(k) for k in ks)
        rows.append({"subject": name, "things": len(ks),
                     "cheapest": round(costs[0], 1),
                     "dearest": round(costs[-1], 1),
                     "you_could_pay_for": sum(1 for c in costs if c <= purse)})
    # LEVERAGE FIRST, then price. These two lists deduplicated the wrong way
    # round: the leverage list dropped anything that was also in the cheapest
    # six, and the spine of this game is precisely the nodes that are BOTH -
    # free, zero-revenue, and holding up an age. A play tester put it exactly:
    # "zero-cost nodes gate whole ages and are invisible... twice one of them
    # was the only thing between me and a branch". Being cheap is the reason
    # they are easy to miss, not a reason to hide them from the column that
    # exists to find them.
    _lev_all = sorted(ok, key=lambda k: (-downstream_count(nodes, k),
                                         s.project_cost(k)))
    leverage = _lev_all[:5]
    cheap = [k for k in sorted(ok, key=lambda k: s.project_cost(k))
             if k not in leverage][:6]
    # AND THE SIX MOST RESTS ON. A normal-play tester found that the spine of
    # the whole game is a handful of cheap, zero-revenue, tier-0 nodes -
    # units_standards, identity_cover, patron_local, workshop_first - and that
    # the only way to find them was to script a `why` call for every startable
    # id, a hundred at first and four hundred and sixty by the end. The digest
    # sorted by price, which is the one axis on which those nodes look like
    # nothing. Leverage is a column the game already knows.
    out = {"ok": True, "count": len(ok),
           "showing": "a summary by subject, because the full list is %d things"
                      % len(ok),
           "subjects": rows,
           # _brief for a DIGEST. _full_entry carried each node's prerequisites
           # and full note - several hundred bytes apiece that the table never
           # renders and that `why` exists to give you properly. The digest's
           # job is to help you choose which `why` to run, and it has a size
           # budget precisely so that it stays a digest.
           "cheapest_six": [_brief(s, nodes, k, fog) for k in cheap],
           # _brief, not _full_entry: the table renders only the columns, and a
           # second block of fog summaries pushed the reply past the size a
           # reply is allowed to be. See the wall-of-text check.
           "most_rests_on_these": [_brief(s, nodes, k, fog) for k in leverage],
           "to_see_more": {
               "one subject": '{"cmd":"available","subject":"metallurgy"}',
               "by name": '{"cmd":"available","find":"furnace"}',
               "what you can pay for": '{"cmd":"available","afford":%d}' % int(max(0, purse)),
               "a page of everything": ('{"cmd":"available","limit":%d,"offset":0}'
                                        % DEFAULT_AVAILABLE_LIMIT),
               "all of it at once": '{"cmd":"available","all":true} (large)'},
           "you_could_raise_for_a_project": round(purse, 1)}
    if fog and heard_block:
        out["heard_of_but_cannot_begin"] = heard_block
        if heard_more:
            out["and_more_you_have_heard_of"] = (
                'ask again with {"cmd":"available","heard_offset":%d} for %d '
                "more, fewest missing prerequisites first (not nearest to "
                "your goal - see 'path <goal>' for that, once fog is off)"
                % (heard_from + len(heard_block), heard_more))
    if fog:
        out["note"] = ("Under fog you see only what you could begin now, and things "
                       "you have heard of. There is no way to see the whole tree.")
    return out


# A LOG LINE A PLAYER WOULD CALL BAD NEWS. Eleven rounds of playtesting kept
# coming back to the same complaint in different words - "failures are
# silent" - and the engine's own self.log already records every one of them,
# in the founder's own words, with no field anywhere marking which lines are
# the bad ones. Matched on the actual wording every append site already uses
# (self.log.append across core.py, projects.py, economy.py and society.py),
# not reinvented here.
_FAILURE_MARKERS = (
    "FAILED", "HALTED", "ABANDONED", "CREDIT EXHAUSTED", "CLOSE TO THE LIMIT",
    "IN ARREARS", "in arrears", "INSOLVENCY", "BONDAGE", "cannot go on",
    "cannot pay everyone", "SHORT OF", "nobody left to keep an eye",
    "disperses", "sacked", "KNOWLEDGE LOST", "destroyed", "confiscated",
    "founder dies", "RUN ENDS", "MOTHBALLED",
)


def _is_failure_line(msg):
    # CASE-INSENSITIVELY, because these markers are prose and prose gets
    # rewritten. The founder's death line was recapitalised to say what the
    # death MEANS rather than only that it happened, and silently stopped
    # being a failure line here, in `log failures`, which is the one screen a
    # player checks to find out what went wrong.
    _low = msg.lower()
    return any(marker.lower() in _low for marker in _FAILURE_MARKERS)


def _log_scrub(s, text):
    """A log line, with anything the player cannot currently see redacted.

    self.log stores what happened IN THE YEAR IT HAPPENED, in plain English,
    and can go on naming a thing for centuries after fog would refuse to
    answer `why` about it - either because a sacking took it away (see
    knowledge_risk's `forgotten`) or, for a hazard's own advice, because it
    names a hedge the player never found. `fog_scrub` already strips ids out
    of a message; most of this engine's own log lines name the thing, not the
    id - "completed: Horizontal loom", not "completed: tex_horizontal_loom" -
    so this also strips NAMES of anything not currently visible.
    """
    text = s.fog_scrub(text)
    if not getattr(s, "fog", False) or not text:
        return text
    memo = {}
    for k, n in s.nodes.items():
        nm = n.get("name")
        if nm and nm in text and not s.is_visible(k, _memo=memo):
            text = text.replace(
                nm, "something you have since forgotten"
                    if k in (getattr(s, "forgotten", None) or {}) else
                    "something you have not heard of")
    return text


def _agent_log(s, cmd=None):
    """The player's own history: what they did, and what followed from it.

    The commonest complaint across eleven rounds of playtesting was some
    version of "failures are silent" - a project stalling, a concern closing
    for want of staff, a hazard landing - none of it visible anywhere once
    the turn it happened had scrolled past. The engine has always kept every
    one of these in self.log; there was simply no command to read it back.

    NEVER THE WHOLE THING. A run of any length runs to tens of thousands of
    lines, more than an agent's whole context window, so this always pages
    and defaults to a recent window - `limit` is hard-capped, not merely
    suggested, and there is no `all:true` here the way `available` has one.
    """
    cmd = cmd or {}
    log = list(getattr(s, "log", None) or [])
    only_fail = bool(cmd.get("failures")
                     or str(cmd.get("only") or "").strip().lower() in
                        ("failures", "failure", "fails", "fail"))
    find = str(cmd.get("find") or cmd.get("search") or "").strip().strip('"\'').lower()
    try:
        since = int(cmd["since"]) if str(cmd.get("since", "")).strip() not in ("", "None") else None
    except (TypeError, ValueError):
        since = None
    try:
        before = int(cmd["before"]) if str(cmd.get("before", "")).strip() not in ("", "None") else None
    except (TypeError, ValueError):
        before = None
    order = str(cmd.get("order") or "newest").strip().lower()
    if order not in ("newest", "oldest"):
        order = "newest"
    try:
        limit = int(cmd.get("limit", 20))
    except (TypeError, ValueError):
        limit = 20
    # THE HARD CAP THAT MAKES "NEVER DUMPED IN ONE GO" TRUE REGARDLESS OF WHAT
    # IS ASKED FOR. Every other paged screen in this game trusts `limit` to
    # whatever a script asks; this one cannot, because the failure mode this
    # command exists to prevent - a reply so large it overflows a reader's
    # context - is exactly what a script asking for {"limit":100000} would
    # otherwise get.
    limit = max(1, min(limit, 100))
    try:
        offset = max(0, int(cmd.get("offset", 0)))
    except (TypeError, ValueError):
        offset = 0

    rows = list(enumerate(log))
    if since is not None:
        rows = [r for r in rows if r[1][0] >= since]
    if before is not None:
        rows = [r for r in rows if r[1][0] <= before]
    if only_fail:
        rows = [r for r in rows if _is_failure_line(r[1][1])]
    if find:
        # CHEAP FIRST, then confirmed against what fog actually lets the
        # player see. A search that only matched a name fog is about to
        # redact would otherwise report "3 lines mention X" as proof
        # something called X exists, which is the same leak the visibility
        # guard on `why` exists to close, reached from a different command.
        rows = [r for r in rows if find in r[1][1].lower()]
        if getattr(s, "fog", False):
            # THE RECHECK IS THE EXPENSIVE HALF, one node sweep per candidate
            # line, so a common word over a run's whole history could be
            # thousands of sweeps. Capped to the most recent slice, which is
            # also the one this command defaults to showing: a search that
            # matches more than this has to narrow the word, the same as a
            # search with no fog concern at all would still have to page.
            _cap = rows[-2000:] if order != "oldest" else rows[:2000]
            rows = [r for r in _cap if find in _log_scrub(s, r[1][1]).lower()]

    total = len(rows)
    ordered = list(reversed(rows)) if order == "newest" else rows
    page = ordered[offset:offset + limit]
    entries = [{"year": yr, "what": _log_scrub(s, msg)} for _idx, (yr, msg) in page]

    out = {"ok": True, "count": total,
           "showing": ("nothing" if not entries else
                      "%d-%d of %d, %s first"
                      % (offset + 1, offset + len(entries), total, order)),
           "entries": entries}
    if offset + len(page) < total:
        out["more"] = ('%d more; ask again with "offset": %d'
                       % (total - offset - len(page), offset + len(page)))
    if not log:
        out["note"] = "nothing has happened yet"
    elif not entries and (find or only_fail or since is not None or before is not None):
        out["note"] = "nothing in your history matches that."
    # DISCOVERABLE ON THE SCREEN ITSELF, not only in `help`. A naive player
    # is not going to guess that this command takes filters at all.
    out["to_filter_or_sort"] = (
        "add 'failures':true for only what went wrong, 'find' to search, "
        "'since'/'before' for a year range, 'order':'oldest' to read forward "
        "from the start instead of back from now, and 'offset' to page "
        "through to the end.")
    return out


def _rests_band(n):
    """How much rests on a node, in the words a person in the year 100 could
    actually use. The exact count is a fog spoiler; the band is not.

    "NOTHING ELSE" HAS TO MEAN ZERO. The bottom band used to cover everything
    from 0 to 3, so a node with real dependents was described as having none,
    and a naive Rome player caught the game contradicting itself inside a
    minute: `why met_ore_crushing_sorting` said "nothing else rests on this"
    while met_jigging_gravity, sitting visible in their own list, gave
    "missing prerequisites: met_ore_crushing_sorting". They found the same
    pair again with in2_tape_measure_steel and
    in2_baseline_measurement_apparatus. Banding is the right answer to the
    spoiler problem, since the exact count is a map of the tree; a band whose
    words are false is not. Vague is allowed here, wrong is not - so 1 to 3
    gets its own rung and the bottom one means what it says.
    """
    return ("almost everything" if n > 1200 else
            "a great deal" if n > 300 else
            "a fair amount" if n > 40 else
            "a few things" if n > 3 else
            "a little" if n > 0 else
            "nothing else; this is worth having for itself")


def _node_explain(s, nodes, k):
    n = nodes[k]
    # WHAT IS LEFT OF IT, not what it always was. A play tester read identical
    # figures in year 436 after building 227 technologies as in year 100 with
    # nothing built, and reasonably said the number never counts down. The
    # chain BEHIND a node is a fixed fact about the tree; what a player is
    # deciding with is what they still have to do.
    _chain_all = closure(nodes, k) - {k}
    need = _chain_all - s.done
    # req_any COUNTS AS UNLOCKING. A node can be reached two ways: as a hard
    # prerequisite in `pre`, or as one option inside a req_any substitution
    # group ("any of a steam engine, a water wheel or a horse will drive this").
    # Scanning `pre` alone reported ten nodes as dead ends that are nothing of
    # the kind, and they were not obscure ones: the Norse clinker hull and
    # bog-iron bloomery, and the Mexica's chinampa. Three civilisations were
    # being told their own signature technology led nowhere, which is exactly
    # the "flagship starting techs are dead ends" complaint a play tester filed
    # against the Norse.
    unlocks = [] if getattr(s, "fog", False) else _unlocked_by(k, nodes)
    # Was: {m for m in nodes if k in closure(nodes, m)} - a full ancestor
    # closure of all 2,831 nodes, per call. Same answers, computed once for the
    # whole tree and cached. See data.descendants.
    # THE CYCLE-SAFE WALK, not the cached bitmask. See the comment on the same
    # substitution in _node_explain's sibling below: the index follows hard
    # prerequisites only and cannot do otherwise, because req_any options make
    # the graph cyclic. This is the number a player reads as "nothing depends
    # on this", and `why sea_clinker_hull` was printing DIRECTLY UNLOCKS with a
    # node named on one line and TOTAL DOWNSTREAM: 0 on the next.
    n_blocks = len(_downstream_of(k, nodes))
    bounty_by_type = (n["tier"] <= 2 and n["cat"] in ("glass_optics", "metallurgy", "precision",
                      "power", "agriculture", "information", "instruments"))
    started = k in s.done or k in s.active
    # THE SUPERVISION FIGURE, from the SAME function open_venture() enforces
    # (see venture_hands, projects.py) - not a second estimate of it. Only
    # meaningful for something that could ever be a going concern; knowledge
    # alone (is_venture false) has nothing to keep an eye on.
    _is_venture = s.is_venture(k)
    _sup_sch, _sup_art = s.venture_hands(k) if _is_venture else (0.0, 0.0)
    _free_sch, _free_art = s.venture_staff_free() if _is_venture else (0.0, 0.0)
    out = {
        "id": k, "name": n["name"], "tier": n["tier"], "cat": n["cat"], "confidence": n["conf"],
        # See strip_self_play_advice (fog.py): drops any sentence that ranks
        # this node against the game or the tree itself - "the pivot of the
        # entire game", "THE highest expected-value node in the tree" - and
        # keeps everything else the note says. Applied here, not only under
        # fog: telling a player outright which of their own choices is
        # correct is the game answering its own question either way.
        "note": strip_self_play_advice(n["note"]),
        # FOG-SCRUBBED. The knowledge-base citation is a section anchor into
        # a shared markdown file, and the tree's own convention names most
        # anchors after the node id they document - so "kb":
        # "...#ag2_norfolk_course" on a completely unrelated, visible node
        # names a hidden node's id in plain sight, the same class of leak
        # `bounty` had with a raw prerequisite list. Found by the generic
        # fog scanner in test_regressions.py (which exists to catch exactly
        # this on the NEXT command too), not by a playtester. fog_scrub is
        # the one filter every such free-text field goes through.
        "kb": s.fog_scrub(n["kb"]),
        "founder_hours": n["ph"],
        # Two different kinds of people, and a tester reasonably read the two
        # fields as contradicting each other ("hired_labour names an engineer,
        # staff_needed asks for artisans; the two labour fields don't agree on
        # who is actually doing the work"). They are not the same question.
        # hired_labour is HOURS OF A JOB, bought from whoever does that trade
        # here, for this project only. staff_needed is PEOPLE ON YOUR OWN BOOKS
        # who understand your methods and stay afterwards.
        "hired_labour": n["lab"],
        "materials": n["mat"],
        # `why` used to quote the BASE cost, identical for every civilization,
        # while step() charged that base multiplied by this society's domain
        # factor and by how far it sits from the material's source. A Han
        # playtester compared `why` across two civs, saw byte-identical numbers,
        # and reasonably concluded the whole civilization model was inert
        # flavour text. It is not: the CHARGE has always applied both factors.
        # The QUOTE was lying, which is the more embarrassing half, because a
        # player plans against the quote.
        "cost": {"labour": round(n["_labour_cost"], 1),
                 "materials": round(n["_material_cost"], 1),
                 "capital": n["cap"],
                 "base_total": round(n["_total_cost"], 1),
                 "civ_domain_factor": round(s.civ_cost_factor(k), 3),
                 "material_distance_factor": round(s.material_cost_factor(k), 3),
                 # THE SCARCITY PREMIUM, which project_cost multiplies in and
                 # this breakdown did not list. A break tester multiplied the
                 # shown factors out for clock_pendulum, got 4,747.6 against a
                 # stated 4,834, and reported it as the one card in the game
                 # whose arithmetic does not work. It was the only missing
                 # term: what the market charges you for a material it barely
                 # sells. Same lesson as price_index below - a breakdown that
                 # omits a factor is worse than no breakdown, because it
                 # invites exactly this check and then fails it.
                 "scarce_material_premium": round(s.material_market_factor(k), 3),
                 "opposition_factor": round(s.opposition_factor(k), 3),
                 # THE FACTOR ACTUALLY MULTIPLIED IN, not a decoy. This field
                 # was filled with money_real while project_cost multiplies by
                 # cost_money_factor(), which is price_index. For Norse, whose
                 # prices are 1.4x Roman, the breakdown printed 1.0 here and
                 # hid its largest term: a tester checked seven nodes, found the
                 # total was 1.4000x the product of the parts every time, and
                 # reasonably called it an undisclosed overhead multiplier. A
                 # breakdown offered as the explanation of a total has to
                 # reconcile with it, or it is worse than no breakdown.
                 "price_index": round(s.cost_money_factor(), 3),
                 "purchasing_power_of_the_coin": round(s.money_real, 3),
                 # The same figure the project will be billed, and must actually
                 # have paid in full before it can complete.
                 "total": round(s.project_cost(k), 1),
                 # AS OF TODAY. A tester read 106,567 here, started the thing
                 # forty years later, and was billed 207,811. Both figures were
                 # correct on their own day: this total moves with prices, the
                 # coinage, what a material costs to get and what you have
                 # since built. The bill is fixed at the moment you START, and
                 # `start` says what it was fixed at.
                 "as_of_year": s.year,
                 "note": "today's price. It is fixed when you start, not when "
                         "you read it: quotes move with prices, the coinage "
                         "and what a material costs to get.",
                 # THE STICKER PRICE IS NOT WHAT `start` WOULD ACTUALLY CHARGE,
                 # once money is already sunk into this node - start_project's
                 # own _paid_now discount (see that function) subtracts
                 # paid_towards[k] before billing a single denarius, but this
                 # screen kept quoting the gross total forever, for a project
                 # a creditor or the player's own `stop` had halted partway.
                 # An England player planning from `why` was planning against
                 # a number the engine would never actually charge; the real,
                 # discounted figure showed up only inside a `start` refusal
                 # or its success line, after the fact.
                 **({"already_paid_towards_this": round(
                        min(s.project_cost(k),
                            max(0.0, getattr(s, "paid_towards", {}).get(k, 0.0))), 1),
                     "what_start_would_actually_charge": round(
                        max(0.0, s.project_cost(k)
                            - min(s.project_cost(k),
                                  max(0.0, getattr(s, "paid_towards", {}).get(k, 0.0)))), 1),
                     "why_less_than_the_total_above":
                        "this much was already paid in before the work "
                        "stopped, halted by a creditor or by your own "
                        "'stop'; it stands to your credit and comes off "
                        "the bill the moment you start this again"}
                    if k not in s.done and k not in s.active
                    and max(0.0, (getattr(s, "paid_towards", {}) or {}).get(k, 0.0)) > 0.5
                    else {})},
        # UPKEEP STAYS EXACT, EVEN UNDER FOG, AND REVENUE DOES NOT. Upkeep is
        # closer to a quoted PRICE than to a forecast - rent, wages and
        # materials are things you can ask around about before you commit,
        # the same way `cost` above is already shown exact and fixed the
        # moment you start. Revenue is different in kind: it is what the
        # market will actually pay for a thing nobody here has ever sold,
        # and that is not knowable in advance whatever you ask around, which
        # is the whole of the user's original question - "shouldn't the
        # payback be something you don't know until after research?" So
        # revenue alone is fogged; see _fog_revenue_estimate.
        "upkeep": n["up"],
        "revenue": (n["rev"] if (not getattr(s, "fog", False)
                                 or _revenue_known_exactly(s, k))
                   else (_fog_revenue_estimate(s, k) or 0.0)),
        # WHAT IT PAYS YOU, which for something in your own practice is a third
        # of the figure above. A break tester read "REVENUE: 500 den/yr" beside
        # a ledger crediting 166.7 for the same node and called it `why`
        # overstating income threefold. Both are true of different things: the
        # tree quotes the trade as an organised concern, and one person in a
        # rented room is not one.
        "but_it_pays_YOU": (
            round(n["rev"] * s.PRACTICE_SHARE * s.practice_attention(), 1)
            if k in s._practice_set() and n["rev"] else None),
        "because": ("this is your own practice, not a concern: it pays about a "
                    "third of what the tree quotes for the trade, and selling "
                    "your hours for wages takes another bite"
                    if k in s._practice_set() and n["rev"] else None),
        "calendar_floor_years": n["yrs"], "risk": s.effective_risk(k),
        # THE EXPECTED TOTAL, RETRIES INCLUDED - not the floor and the risk
        # left for the player to combine by hand. A 45%-risk, 4-year-floor
        # node is not a 4-year project: the bare geometric series 1/(1-p) is
        # 1.82 attempts, and even that understates it once retry learning
        # (RETRY_RISK_FLOOR/DECAY, RETRY_CALENDAR_CAP/DECAY - see
        # expected_calendar_years' own docstring in projects.py) starts
        # moving both the odds and the wait on every attempt after the
        # first. A player who had already won the game watched
        # point_contact_transistor fail six times running and estimated it
        # cost "roughly two dozen years" - this is the number that would
        # have told them what to expect before the dice started rolling,
        # computed through the SAME retry rule _complete actually applies,
        # not a second, looser approximation of it.
        "expected_calendar_years_with_retries": round(
            s.expected_calendar_years(k), 2),
        # WHAT THE FAILURES SO FAR HAVE BOUGHT, said out loud, because a
        # number that quietly improves is a number a player cannot plan with.
        "attempts_already_failed": int(getattr(s, "failed_attempts", {}).get(k, 0)),
        "risk_before_any_attempt": n["risk"],
        # THE SUM, NOT ONLY THE RATE. See _node_explain's own note: a failure
        # takes a flat 40% of the money and puts 40% of the hours back on the
        # slate, and a player deciding whether to risk it is holding the size
        # of the project in their head, not the percentage.
        "failure_costs": round(s.project_cost(k) * 0.4, 1) if n["risk"] else 0.0,
        "failure_costs_hours": round(n["ph"] * 0.4, 1) if n["risk"] else 0.0,
        "staff_needed": {"scholars": n["sch"], "artisans": n["art"]},
        # THE FIGURE THE GAME ACTUALLY TESTS. start_project gates artisans on
        # craft_hands_available() - staff, plus yourself, plus any hours you
        # have already bought - and this printed s.artisans, which is only the
        # first of the three. A play tester read "STAFF NEEDED: 3 artisans
        # (you have 1, 0)" beside a prompt reading "sch 0 art 0" and could not
        # tell which of the two numbers, if either, was the one that decided
        # whether they could begin. Print what decides it.
        "you_have": {"scholars": round(s.effective_scholars(), 1),
                     "artisans": round(s.craft_hands_available(), 1)},
        "you_have_counts": ("counting yourself, and hours you have bought"
                            if s.founder_alive else "counting hours you have bought"),
        # SAY WHEN THE STAFF IT WANTS IS MORE THAN THIS SOCIETY HAS. The goal
        # itself needs twenty-five scholars against a ceiling of 6.4, and a
        # play tester found that ceiling in a refusal message in year 463 of a
        # 500-year game - the single thing that decided whether their run could
        # be won, on no screen anywhere.
        # AGAINST WHAT YOU ACTUALLY HAVE, not against the hiring ceiling alone.
        # A school and an academy grant scholars outright, on top of anyone you
        # could hire, so "literacy here will never supply more than 6.4"
        # printed beside "(you have 210)" - and twice made a play tester think
        # they were hard-blocked when they were not.
        "more_scholars_than_this_society_can_supply": (
            "%s wanted; you have %.1f and literacy here will never let you HIRE "
            "more than %.1f. Printing, paper, schools and academies raise both."
            % (n["sch"], s.effective_scholars(), s.literate_capacity("scholar"))
            if (n["sch"] > s.literate_capacity("scholar")
                and n["sch"] > s.effective_scholars()) else None),
        "more_craftsmen_than_your_household_can_hold": (
            "%s wanted; you have %.1f and could hold %.1f in all. %s"
            % (n["art"], s.artisans,
               s.headcount() + max(0.0, s.household_room()), s._room_advice())
            if (n["art"] > s.headcount() + max(0.0, s.household_room())
                and n["art"] > s.artisans) else None),
        # A SECOND STAFF FIGURE, AND IT IS NOT THE SAME NUMBER. staff_needed
        # above is the BUILD crew - what start_project gates on, and what
        # goes idle again once the work is finished. A going concern is a
        # standing commitment on top of that: somebody of yours has to keep
        # an eye on it every year it runs, which is venture_hands() - a
        # quarter of the build crew, floored by how much the concern takes
        # in (see venture_hands's own comment) - and open_venture() is the
        # ONLY other place this is checked. Three players built something on
        # the strength of the number above, paid for it in full, and were
        # then refused at `open` on a bigger number neither `why` nor
        # `available` had ever shown them - one measured it exactly:
        # "2.13 craftsmen" enforced against a `why` that had said "2
        # artisans" and nothing else. Read the SAME function open_venture()
        # calls, not a second estimate of it, so the two can never drift
        # apart again.
        "staff_to_keep_it_open": (
            {"scholars": round(_sup_sch, 2), "artisans": round(_sup_art, 2)}
            if _is_venture else None),
        "staff_to_keep_it_open_means": (
            "a SEPARATE requirement from staff_needed above, and the one "
            "'open' actually enforces once this is built: people of your "
            "own who keep an eye on it every year it runs, not the crew "
            "that built it. Often smaller than staff_needed - typically a "
            "quarter of it - but a concern that takes in a great deal needs "
            "more watching than it took to build, and this can come out "
            "LARGER. Checked when you 'open' it, not when you 'start' it, "
            "so know this number before you spend money on the other one."
            if _is_venture else None),
        "more_supervision_than_you_have_free_right_now": (
            "%.2f scholars and %.2f artisans needed to keep it open; you "
            "have %.2f and %.2f free right now (not already watching "
            "something else). This is what 'open' will actually check, on "
            "the day you open it - hire, teach, or close something first."
            % (_sup_sch, _sup_art, _free_sch, _free_art)
            if _is_venture and (_sup_sch > _free_sch + 1e-9
                                or _sup_art > _free_art + 1e-9) else None),
        "suspicion": n.get("sus", 0), "state_interest_trait_score": n.get("gov", 0),
        "bounty_eligible_by_type": bounty_by_type,
        # NOT CHARGED UNTIL YOU OPEN IT. A tester read the upkeep off `why`,
        # built the thing, and found nothing on the bill - correctly, because
        # revenue and upkeep follow what you RUN. The figure is real; it just
        # is not yours yet.
        "revenue_and_upkeep_apply_only_once_opened": (
            True if (n["rev"] > 0 or n["up"] > 0) and k not in s.granted
            and k not in s.operating else None),
        # "FINISHED, STAYS FINISHED" MEANS THREE DIFFERENT THINGS, and this
        # engine said it the same way for all three. Most of what you build is
        # a plain prerequisite: done once, it counts for ever, whatever you do
        # with it afterward (see missing_prerequisites below, which reads
        # `done`, never `running`). A CAPABILITY_INSTITUTIONS node is not that:
        # a school's scholars, a workshop's household places, a patron's
        # credit, and a patron's willingness to have his name behind
        # something the state is wary of, ALL stop the moment you close the
        # doors, exactly like its revenue and upkeep above - even though the
        # knowledge of how to run one never leaves you. A Mexica player lost
        # two multi-year stretches to closing these for the capital back, and
        # a Rome player separately could not tell which of `identity_cover`,
        # `workshop_first` and `patron_local` (all sitting identically in
        # `ventures`) actually needed to stay open. This says which kind a
        # node is, in the one place a player reads before deciding.
        "this_is_a_capability_you_must_keep_open": (
            "yes - it is knowledge (that part is permanent), but scholars it "
            "supports, household places it adds, credit or standing it lends "
            "you, or a future start it clears all stop the moment you close "
            "it, the same as its revenue and upkeep. Closing it for the "
            "capital back gives up all of that, not only the money."
            if k in s.CAPABILITY_INSTITUTIONS else None),
        # ONLY WHAT YOU HAVE HEARD OF. These are read for a visible node, where
        # every prerequisite is either done or itself heard of - except on the
        # goal, which `why` answers under fog because the status line names it
        # every turn. Unfiltered, that one exception printed the goal's seven
        # hidden prerequisites by name in the JSON, which is the fog exploit
        # this file has already closed twice.
        "direct_prerequisites": ([p for p in n["pre"] if s.is_visible(p)]
                                 if getattr(s, "fog", False) else n["pre"]),
        # A GRANTED NODE IS HELD, WHATEVER ROUTE THE TREE DRAWS TO IT. `why
        # cap_heat_1300` on Han reported done:true, missing_prerequisites:
        # ["cap_heat_1100"] and can_start_now:false in one object - three
        # statements that cannot all be true. The cause is not a broken graph
        # but a mis-read one: the tree encodes ONE acquisition route, and a
        # society that already has the thing did not travel it. The clearest
        # case is the Mexica, whose maize and chinampas hang off
        # exp_americas_factory - crossing the Atlantic and founding a trading
        # post - because that is how a European acquires maize. Closing the
        # prerequisites into the grant, the obvious-looking fix, would hand
        # Tenochtitlan sextants, pendulum clocks and cementation steel for
        # nothing. What is actually wrong is the claim that a thing you have
        # is missing something.
        "missing_prerequisites": ([] if k in s.granted
                                  else [p for p in n["pre"] if p not in s.done
                                        and (not getattr(s, "fog", False)
                                             or s.is_visible(p))]),
        "prerequisites_you_have_not_heard_of": (
            sum(1 for p in n["pre"] if not s.is_visible(p))
            if getattr(s, "fog", False) else 0) or None,
        "held_without_building_it": k in s.granted,
        "prerequisites_are_how_another_society_would_get_this": (
            "this society already has it; the list above is the route somebody "
            "who did not would have to take" if k in s.granted and n["pre"]
            else None),
        # Same reasoning: the size and cost of everything BEHIND a node is a
        # measurement of a tree you cannot see. You do know how many of its own
        # prerequisites you are still missing, because those have names you have
        # either heard or not.
        "chain_size": (len(need) if not getattr(s, "fog", False) else None),
        "chain_size_counting_what_you_have_built": (
            len(_chain_all) if not getattr(s, "fog", False) else None),
        "chain_founder_hours": (sum(nodes[x]["ph"] for x in need)
                                if not getattr(s, "fog", False) else None),
        # AT THIS SOCIETY'S PRICES, like the COST line four rows above it. This
        # summed the tree's BASE cost and applied none of the multipliers the
        # same page prints - the eight prerequisites of a telescope came out at
        # 24,175 in all five civilisations, against a real bill of 18,970 in
        # Han and 35,108 for the Norse. A break tester checked it and called it
        # a 31% error in the poorest civilisation; chain_size and
        # chain_founder_hours were exact, and only the money was wrong.
        "chain_cost": (round(sum(s.project_cost(x) for x in sorted(need)), 1)
                       if not getattr(s, "fog", False) else None),
        "critical_path_years": (critical_path(nodes, k)[0]
                                if not getattr(s, "fog", False) else None),
        # DOWNSTREAM COUNT IS A SPOILER UNDER FOG, and a tester said so
        # unprompted: "downstream_count 1276 seems slightly cheaty". They were
        # right, and worse than cheaty, it was the whole game. Two testers
        # independently found the same three hub nodes by calling `why` on
        # guesses and reading the number, and one wrote that after that "the
        # early strategy is pretty obvious". An exact count of everything a
        # thing leads to is a map of the tree you were told you could not see.
        #
        # What survives fog is the thing a person in the year 100 could actually
        # judge: whether this is a foundation others will build on, or an end in
        # itself. You can tell that much by looking at it.
        "unlocks": unlocks,
        "downstream_count": (n_blocks if not getattr(s, "fog", False) else None),
        "how_much_rests_on_this": (
            None if not getattr(s, "fog", False) else _rests_band(n_blocks)),
        # Under fog there is no goal, so a boolean saying whether this is "on the
        # goal path" is either meaningless or a leak. A tester read it as
        # true/false for five hundred years while `state.goal` was null and
        # reasonably asked what path it could possibly mean.
        "on_goal_path": (None if getattr(s, "fog", False)
                         else (k == s.goal or is_downstream(nodes, k, s.goal))),
        "done": k in s.done, "active": k in s.active,
        "can_start_now": (not started) and s.can_start(k),
        # Under fog this used to name locked prerequisites in full, so a tester
        # learned the name and description of the printing press from an
        # unrelated node's explanation while `why` on the press itself said they
        # had never heard of it. If you cannot see a thing, you cannot see its
        # name in someone else's sentence either.
        "start_blocked_reason": None if started else s.fog_scrub(s.start_reason(k)[1]),
    }
    # WHAT IS ACTUALLY HOLDING AN ACTIVE PROJECT UP, on the one screen a
    # player names it by id to read. `state` already says this for every
    # RUNNING project (see _waiting_on's own comment: a project can only
    # absorb its cost divided by its calendar floor in any one year,
    # however much cash is in hand, and a Han player watched abundant
    # capital sit idle against cheap projects for years before inferring the
    # mechanism themselves). `why <id>` on that same project said nothing of
    # the kind - STATUS: ACTIVE and no more - which is exactly the screen a
    # player checking on one specific stalled project would reach for.
    if k in s.active:
        _st = s.active[k]
        _bill = _st.get("cost_left")
        if _bill is None:
            _bill = max(0.0, s.project_cost(k) - _st["spent"])
        out["waiting_on"] = _waiting_on(s, nodes, k, _st, _bill)
    # Say what the two labour fields mean ONLY when this node makes it matter.
    # A tester read them as contradicting each other, so the explanation earns
    # its place; carrying it on every reply whether or not the node hires anyone
    # is 400 bytes of boilerplate per call.
    absent = sorted(t for t in n["lab"] if not s.trade_available(t))
    if absent:
        out["trades_that_do_not_exist_here"] = absent
        out["hired_labour_means"] = ("hours of a trade bought in for this job only. "
                                     "These trades do not exist here yet and must "
                                     "be taught; see the labour command.")
    # TRAIN AND HIRE ARE TWO STEPS, and a project asking for a taught trade
    # went quiet about it the moment `train` was called - trade_available()
    # (what `absent` above checks) goes true instantly, years before anyone
    # actually graduates or is hired in. `start` catches the real shortage
    # (market_supply, not trade_available) and refuses; `why` said nothing
    # about it beforehand. A Rome player hit that refusal with no warning on
    # either this screen or train's own success message.
    _taught_but_empty = sorted(t for t in n["lab"]
                               if t not in absent and s.market_supply(t) <= 0.0)
    if _taught_but_empty:
        out["trades_taught_but_nobody_here_to_do_them_yet"] = _taught_but_empty
        out["trades_taught_but_nobody_here_means"] = (
            "the trade exists here, but nobody is trained and ready: a "
            "project draws only on people actually held in a taught trade, "
            "never a general market for it. If someone is still learning "
            "this may still let the work start and then stall at 0 progress "
            "on this trade until they finish; if nobody is even learning it "
            "yet, starting is refused outright. Check 'labour' for who is "
            "in training, or 'hire' to add people to this trade right now.")
    if n["art"] > s.artisans or n["sch"] > s.effective_scholars():
        out["staff_needed_means"] = ("people kept on your own staff, who understand "
                                     "your methods and stay when this is finished. "
                                     "Different from hired_labour, which is hours of "
                                     "a job.")
    return out


# ----------------------------------------------------------------------------
# A rendering for a person, alongside the JSON one, not instead of it.
#
# Two testers asked for this in almost the same words: the JSON is precise
# and correct and a wall to read. Everything below turns an outgoing reply
# dict - the exact same dict that gets json.dumps()'d to stdout - into text a
# person can scan. It NEVER changes what goes to stdout; see cli.py's --pretty
# handling, which prints this to stderr, alongside the unmodified JSON line,
# only when asked. The renderer reads the reply dict only, never the live Sim,
# so what a person reads and what a script reads are guaranteed to agree -
# there is only one source of truth for any number in here.
# ----------------------------------------------------------------------------


def _factor(v):
    """A multiplier, at the precision a player would need to reproduce a total.

    _fmt_num drops to one decimal above 1, which turned an opposition factor
    of 1.15 into "x1.1" and made 200 x 1.15 = 230 look like arithmetic the
    game had got wrong. A factor is not a quantity; it is a term in a product
    somebody is going to multiply out.
    """
    if not isinstance(v, (int, float)) or isinstance(v, bool):
        return _fmt_num(v)
    f = float(v)
    if abs(f - round(f)) < 5e-4:
        return "%d" % round(f)
    return ("%.3f" % f).rstrip("0")


def _fmt_num(v):
    """A number the way a person reads it: thousands separated, and no more
    precision than is useful. 12345.6 -> "12,346". 4.0 -> "4". 0.375 -> "0.38".

    Whole-feeling numbers (anything 1 and up) carry no decimal at all once
    they are the size a player actually deals in; a tester said reading raw
    JSON here "made me double-check arithmetic", which a rounded, comma'd
    figure does not invite.
    """
    if v is None:
        return "-"
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, (int, float)):
        f = float(v)
        if f != f or f in (float("inf"), float("-inf")):
            return str(v)
        if f == 0:
            return "0"
        if abs(f) >= 1000:
            return "{:,.0f}".format(f)
        if abs(f) >= 1:
            return "{:,.0f}".format(f) if float(f).is_integer() else "{:,.1f}".format(f)
        return "{:,.2f}".format(f)
    return str(v)


def _fmt_range(v):
    """earns_per_year, under fog, for a thing you have never run: [lo, hi]
    rather than a bare number - see _fog_revenue_estimate. One column had to
    read both shapes, so this reads either and falls back to _fmt_num for
    the ordinary case.
    """
    if isinstance(v, (list, tuple)) and len(v) == 2:
        return "%s-%s" % (_fmt_num(v[0]), _fmt_num(v[1]))
    return _fmt_num(v)


def _pct(v):
    """A 0..1 fraction as a percentage a person reads at a glance.

    NEVER ROUND A FATAL CHANCE TO ZERO. Two play testers were ended by
    something this had just printed as 0%: "1% chance something lands this
    year, of which 0% would end the run", and then the run ended. A number
    that means "this can kill you" and prints as "this cannot happen" is the
    one number in the game that must not be rounded down. Anything that can
    happen at all prints as at least "<1%".
    """
    if v is None:
        return "-"
    try:
        f = 100.0 * float(v)
    except (TypeError, ValueError):
        return str(v)
    if f <= 0.0:
        return "0%"
    if f < 0.5:
        return "<1%"
    return "%.0f%%" % f


def _wrap(text, width=None, indent=""):
    # WIDTH DEFAULTS TO DISPLAY_WIDTH, NOT A LITERAL NUMBER, so the one
    # player-facing preference for it (cli.py's Options screen, "display
    # width") reaches every caller that does not ask for a specific width of
    # its own - see DISPLAY_WIDTH's own comment, near TYPED_HINTS, for who
    # sets it and why `agent` never does.
    if width is None:
        width = DISPLAY_WIDTH
    if not text:
        return ""
    words, lines, cur = str(text).split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width:
            lines.append(indent + cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(indent + cur)
    return "\n".join(lines)


def render_error(resp):
    return "REFUSED: %s" % resp.get("error", "unknown error")


def render_state(out):
    """A position, not a dict: year, money, what is running and what each
    thing is waiting on, who you employ, what is about to happen to you.

    Works on both the short state() and state(full=true), and on step()'s
    reply, which is this same shape with completed/events stitched on front.
    """
    L = []
    year = out.get("year")
    L.append("=" * 60)
    # WITH THE CLOCK ON IT. The horizon was in one help topic and in no reply
    # anyone reads every turn, so a tester met it only by overshooting it.
    left = out.get("years_left")
    L.append(("YEAR %s%s" % (year, ("   (%s years to the horizon at %s)"
                                    % (_fmt_num(left), out.get("horizon_year")))
                             if left is not None else ""))
             if year is not None else "STATE")
    L.append("=" * 60)
    if out.get("ended"):
        L.append("")
        L.append("*** THE RUN HAS ENDED: %s ***" % out.get("end_reason"))

    L.append("")
    net_after = out.get("net_after_project_spend")
    net_plain = out.get("net_per_year")
    spend = out.get("project_spend_this_year")
    L.append("Money: %s den" % _fmt_num(out.get("capital")))
    # BOTH NUMBERS, ALWAYS - NOT ONE HIDING THE OTHER. This used to print
    # net_after_project_spend alone whenever it was present, which is every
    # turn: it is capital in less what you owe, less whatever went into
    # projects THIS YEAR, so starting one expensive thing made the household
    # look about to go broke on the very turn it was investing soundly. A
    # play tester read that plunge on every build and could not tell "the
    # household is failing" from "the household just paid for a workshop"
    # without a second command (`money`) the tutorial never points at. The
    # recurring figure - what standing income clears with nothing new
    # started - is the honest one to watch, and it now prints on the same
    # line `state` is read from every turn instead of one command away.
    if net_plain is not None and net_after is not None:
        L.append("  net %s%s den/yr, recurring - this is the one to watch"
                 % ("+" if net_plain >= 0 else "", _fmt_num(net_plain)))
        if abs(spend or 0) > 0.5 or round(net_after, 1) != round(net_plain, 1):
            L.append("  this year also put %s den into projects, leaving "
                     "%s%s den/yr after that (one-off, not a sign the "
                     "recurring figure above has changed)"
                     % (_fmt_num(spend or 0),
                        "+" if net_after >= 0 else "", _fmt_num(net_after)))
    elif net_after is not None:
        L.append("  net %s%s den/yr (after %s den into projects this year)"
                 % ("+" if net_after >= 0 else "", _fmt_num(net_after), _fmt_num(spend or 0)))
    elif net_plain is not None:
        L.append("  standing net %s%s den/yr (does not count project spend)"
                 % ("+" if net_plain >= 0 else "", _fmt_num(net_plain)))
    if out.get("in_bondage_for_debt"):
        L.append("IN DEBT BONDAGE: %s years left owing %s den"
                 % (_fmt_num(out["in_bondage_for_debt"]), _fmt_num(out.get("debt_still_to_work_off"))))

    # WHETHER YOU AGE IS A FACT ABOUT THE GAME YOU ARE PLAYING, and the human
    # rendering did not carry it: a mortal run and an immortal one looked
    # identical here, though the menu asks you to choose between them and one
    # of them ends with everything you have not made permanent dying with you.
    _src = out.get("where_your_hours_come_from") or {}
    _dep = _src.get("deputies_who_direct_work_for_you") or 0
    # THE AGE, ON THE LINE THAT ALREADY SAYS DEAD OR ALIVE, not only inside a
    # log sentence from however many years ago: a normal-play tester in
    # mortal mode never saw an age anywhere but that one line in `events`.
    L.append("You: %s%s, %s founder-hours free this year%s"
             % ("alive" if out.get("founder_alive") else
                ("DEAD (aged about %s at death, in %s)"
                 % (out.get("founder_died_aged"), out.get("founder_died_in"))
                 if out.get("founder_died_aged") is not None else "DEAD"),
                " and ageing" if out.get("founder_ages") else " (you do not age)",
                _fmt_num(out.get("founder_hours_available")),
                ("   (%s of your own, plus %s deputies directing work in your "
                 "name at %s hours each)"
                 % (_fmt_num(_src.get("you")), _fmt_num(_dep),
                    _fmt_num(_src.get("hours_each_deputy_adds"))))
                if _dep else ""))
    for _w in (out.get("supervision_close_to_the_edge") or []):
        # EACH ENTRY IS A DICT (id/name/within/of/headline/...), not a bare
        # string - staffing_closure_warnings() returns structured rows so a
        # JSON caller gets the trade, the room and the fix command apart from
        # the prose. This human-text renderer wants only the sentence; a
        # bare `_w` here crashed `state` outright the moment any warning
        # actually fired ("can only concatenate str (not 'dict') to str"),
        # which nothing caught because the regression suite only ever called
        # staffing_closure_warnings() directly, never through render_state.
        L.append(_wrap("  " + (_w.get("headline") if isinstance(_w, dict) else _w)))
    if out.get("worth_knowing_early"):
        L.append(_wrap("  " + out["worth_knowing_early"]))
    if out.get("free_hours_going_unused"):
        L.append(_wrap("  " + out["free_hours_going_unused"]))

    active = out.get("active") or {}
    L.append("")
    L.append("RUNNING (%d):" % len(active) if active else "RUNNING: nothing")
    for k, st in sorted(active.items(), key=lambda kv: kv[0]):
        total = st.get("founder_hours_total") or 0
        left = st.get("founder_hours_left") or 0
        pct = 100.0 * (total - left) / total if total else 100.0
        # Clamped. Refunded hours could once exceed hours spent, and a
        # playtester read the result off this very line: "-67% of your hours
        # spent". The arithmetic is fixed in core.py; the display refuses to
        # print an impossible figure either way.
        pct = max(0.0, min(100.0, pct))
        # THE ID, because that is what `stop` and `why` take. This printed the
        # display NAME, so a play tester with a project they wanted to abandon
        # had no way to name it: "no way to map a running project's display
        # name back to an id so you can stop it". The name goes on the line
        # after, where it costs nothing.
        L.append("  %-34s %3.0f%% of your hours spent, %s still owed - waiting on %s"
                 % (k, pct, _fmt_num(st.get("still_to_pay")),
                    st.get("waiting_on") or "-"))
        if st.get("name"):
            L.append("      %s" % st["name"])
        if st.get("why_underfunded"):
            L.append("      %s" % st["why_underfunded"])
        if st.get("will_be_abandoned_in_years") is not None:
            _tr = st.get("because_nobody_here_can") or ["trade"]
            L.append("      !! ABANDONED IN %s YEAR%s unless you can find %s %s: "
                     "everything spent on it goes. 'stop %s' keeps your hours."
                     % (_fmt_num(st["will_be_abandoned_in_years"]),
                        "" if st["will_be_abandoned_in_years"] == 1 else "S",
                        "an" if _tr[0][0] in "aeiou" else "a",
                        " or ".join(_tr), k))

    stuck = out.get("stuck")
    if stuck:
        L.append("")
        L.append("!! " + stuck["you_are_stuck"].upper())
        L.append(_wrap(stuck["this_is_not_the_end_of_the_run"], indent="   "))
        for w in stuck["what_would_change_it"]:
            L.append(_wrap("- " + w, indent="   "))

    idle_v = out.get("you_know_how_to_run_but_have_not_opened")
    if out.get("concerns_you_run") or idle_v:
        L.append("")
        L.append("RUNNING AS CONCERNS: %s   (you know how to run %s more and "
                 "have not opened them - 'ventures')"
                 % (_fmt_num(out.get("concerns_you_run")), _fmt_num(idle_v)))
        if out.get("shut_concerns_would_earn_a_year"):
            L.append("  those shut concerns would clear %s den/yr between them, "
                     "and earn nothing while they are shut"
                     % _fmt_num(out["shut_concerns_would_earn_a_year"]))

    employees = out.get("employees") or {}
    L.append("")
    _house = (out.get("slaves") or 0) + (out.get("freedmen") or 0)
    L.append("EMPLOY: %s people, %s den/yr in wages%s"
             % (_fmt_num(out.get("employees_total")),
                _fmt_num(out.get("annual_wage_bill")),
                ("   (and %s in your household, owned or freed)" % _fmt_num(_house))
                if _house else ""))
    if out.get("household_places_used_of_all"):
        L.append("  household places: %s used - what you can feed, house and "
                 "oversee. 'labour' says what raises it."
                 % out["household_places_used_of_all"])
    for t, v in sorted(employees.items()):
        L.append("  %-16s %s" % (t, _fmt_num(v)))
    if not employees:
        L.append("  nobody")
    if out.get("what_you_can_field"):
        L.append(_wrap(out["what_you_can_field"], indent="  "))
    if out.get("staff_are_fractional_because"):
        L.append(_wrap(out["staff_are_fractional_because"], indent="  "))

    L.append("")
    # PROTECTION BELONGS HERE. It is what bribes, patrons and standing actually
    # buy, and what decides whether a strange result out of your workshop is
    # read as learning or as sorcery - and it appeared on no screen at all. A
    # weird-play tester found it only by noticing that bribing with no scandal
    # to answer still moved SOMETHING, and reported it as a hidden stat being
    # sold to them.
    L.append("STANDING: reputation %s   protection %s   scandal %s   eminence %s"
             % (_fmt_num(out.get("reputation")), _pct(out.get("protection")),
                _fmt_num(out.get("scandal")), _fmt_num(out.get("eminence"))))
    prom = out.get("prominence") or {}
    if prom:
        # SAY WHICH NUMBER IT IS ABOUT. This line sat directly under the row
        # showing reputation, suspicion, scandal and eminence, and refers to the
        # LAST of those - so a break tester with suspicion pinned at 30 read
        # "dangerous above 26 ... 0% chance of ruin this year" as a flat
        # contradiction, and wrote the whole mechanic off as inert. It was
        # answering a question they had not asked.
        # "CHANCE OF RUIN" MEANT "CHANCE SOMETHING HAPPENS", and only a fifth
        # of those somethings end the run. A play tester survived two
        # confiscations, was ended by the third roll, and had this same line in
        # front of them before all three. Print both figures.
        if out.get("scandal_danger") is not None:
            L.append("  SCANDAL is dangerous above %s (%s chance of being "
                     "denounced this year, which ends the run; 'bribe' buys it "
                     "down and it falls a tenth a year on its own)"
                     % (_fmt_num(out["scandal_danger"]),
                        _pct(out.get("chance_of_being_denounced_this_year"))))
            # THE DIRECTION, not only the level. See _agent_state.
            if out.get("years_until_scandal_crosses_the_line") is not None:
                L.append("    and RISING: up %s last year. At that rate you "
                         "cross the line in about %s year(s), and the chance "
                         "above is only true of where you stand today"
                         % (_fmt_num(out.get("scandal_rose_by_last_year")),
                            _fmt_num(out["years_until_scandal_crosses_the_line"])))
        L.append("  EMINENCE is dangerous above %s (settles near %s if nothing "
                 "changes; %s chance something lands this year, of which %s "
                 "would end the run)"
                 % (_fmt_num(prom.get("dangerous_above")),
                    _fmt_num(prom.get("settles_at_if_nothing_changes")),
                    _pct(prom.get("chance_of_ruin_this_year")),
                    _pct(prom.get("chance_the_run_ENDS_this_year"))))
        if prom.get("the_one_lever") and (prom.get("now") or 0) > (
                prom.get("dangerous_above") or 1e9) * 0.6:
            L.append(_wrap(prom["the_one_lever"], indent="    "))
    L.append("  technologies: %s built by you, %s granted for free (%s total)"
             % (_fmt_num(out.get("done_earned")), _fmt_num(out.get("done_granted")),
                _fmt_num(out.get("done_count"))))

    at_risk = out.get("at_risk")
    kr = out.get("knowledge_risk")
    L.append("")
    if at_risk:
        L.append("AHEAD: %s technologies at risk if a hazard lands, hedged by %s"
                 % (_fmt_num(at_risk.get("technologies_you_could_lose")),
                    at_risk.get("hedged_by") or "nothing yet"))
        if at_risk.get("happening_now"):
            L.append("  HAPPENING NOW: %s" % ", ".join(at_risk["happening_now"]))
        L.append("  %s more hazard(s) known ahead - %s"
                 % (_fmt_num(at_risk.get("hazards_still_ahead")), at_risk.get("in_full") or ""))
    elif kr:
        L.append("AHEAD: %s technologies at risk; a sacking that costs you "
                 "anything (%s of them do) takes %s, hedged by %s"
                 % (_fmt_num(kr.get("technologies_at_risk")),
                    _pct(kr.get("and_the_chance_a_sacking_costs_you_anything")),
                    _fmt_num(kr.get("expected_technologies_lost_per_sacking")),
                    kr.get("hedged_by") or "nothing yet"))
        for h in kr.get("known_hazards_ahead") or []:
            yrs = h.get("years") or [0, 0]
            tag = "IN PROGRESS" if h.get("in_progress") else "%s-%s" % (yrs[0], yrs[-1])
            L.append("  [%s] %s" % (tag, h.get("name")))

    if out.get("fog_of_war"):
        L.append("")
        L.append("Fog of war is on: you see the next step, never the road. "
                 "%s of your own built so far." % _fmt_num(out.get("done_earned")))
        if out.get("goal_in_words"):
            L.append("Aiming at: %s%s" % (out["goal_in_words"],
                     ("  -- REACHED in %s AD" % out.get("goal_year"))
                     if out.get("goal_reached") else ""))
        # HOW MANY, NEVER HOW MANY OF HOW MANY. See the field's own comment
        # in _agent_state for why the total stays withheld until the run is
        # over.
        if out.get("on_the_road_to_the_goal_so_far") is not None:
            L.append("On the road there so far: %s of its nodes"
                     % _fmt_num(out["on_the_road_to_the_goal_so_far"]))
    elif out.get("goal"):
        L.append("")
        L.append("Goal: %s%s" % (out["goal"],
                 ("  -- REACHED in %s AD" % out.get("goal_year")) if out.get("goal_reached") else ""))

    completed = out.get("completed")
    events = out.get("events")
    lost = out.get("lost")
    fdts = out.get("the_founder_died_this_step")
    if completed or events or lost or fdts:
        head = []
        # THE LOUDEST LINE IN THE REPLY, not one more EVENT line among sixty.
        # See _founder_death_info and the step handler's own comment on why
        # a multi-year step stops here rather than running on past it.
        if fdts:
            head.append("  *** THE FOUNDER HAS DIED, aged about %s, in %s ***"
                        % (fdts.get("aged_about"), fdts.get("year")))
        for c in completed or []:
            head.append("  %s %s: %s"
                        % ("THIS SOCIETY NOW HAS" if c.get("granted")
                           else "COMPLETED", c.get("year"), c.get("name")))
        for c in lost or []:
            head.append("  LOST %s: %s%s"
                        % (c.get("year"), c.get("name"),
                           " (restore brings it back for a fraction of the cost)"
                           if c.get("can_be_restored") else ""))
        for e in events or []:
            # "DURING 381", NOT "EVENT 381". step() captures the year at the
            # top, logs everything that happens during that year under it, and
            # increments at the end - so an event is stamped with the year being
            # LIVED THROUGH while the prompt underneath already reads the next
            # one. A player reproducing a disaster from a save read "EVENT 381"
            # beside a prompt saying 382, concluded the event had not fired, and
            # spent a while chasing that. The year is right; "EVENT 381" implied
            # "as of 381" when it means "in the course of 381". Said the other
            # way, the two screens stop contradicting each other - and nothing
            # in any save or log changes, which a shift of the stamped year
            # itself could not have promised.
            head.append("  DURING %s: %s" % (e.get("year"), e.get("message")))
        if out.get("stopped_early"):
            head.append("  " + out["stopped_early"])
        L = head + [""] + L if head else L

    also = out.get("also_available")
    if also:
        L.append("")
        L.append("more: " + "; ".join(also))
    return "\n".join(L)


# The short forms of the bands, so the column stays a column.
_RESTS_SHORT = {"almost everything": "ALL", "a great deal": "much",
                "a fair amount": "some", "a few things": "few",
                "a little": "1-3",
                "nothing else; this is worth having for itself": "-"}


def _cost_marker(e, purse):
    """A row you cannot pay for today gets its cost marked.

    "MOST RESTS ON THESE" heads its list with items at 230 to 1,580 denarii
    against an opening purse of 400, and a break tester followed it into
    CREDIT EXHAUSTED by year 106. The advice is right - those really are the
    nodes everything rests on - and the reader needs to know which of them
    they can act on this year.
    """
    c = e.get("cost")
    if purse is None or not isinstance(c, (int, float)):
        return ""
    return "" if c <= purse else "*"


def _available_row(e, w=None, purse=None):
    # THE FLOOR SCALES WITH DISPLAY_WIDTH, NOT A BARE 34. render_available
    # already grows this per-table to fit the longest id on the page (see
    # its own comment on _w below), so a narrow default never truncated one;
    # this only gives a wide terminal the same extra breathing room _wrap
    # gets, and reproduces exactly 34 at DISPLAY_WIDTH's own old default
    # (76), so nothing here moves for a player who has changed nothing.
    if w is None:
        w = max(34, DISPLAY_WIDTH - 42)
    hours = e.get("founder_hours", e.get("your_hours"))
    years = e.get("calendar_floor_years", e.get("least_years"))
    risk = e.get("risk", e.get("chance_of_failure"))
    dc = e.get("downstream_count")
    rests = (_fmt_num(dc) if dc is not None
             else _RESTS_SHORT.get(e.get("how_much_rests_on_this"), "?"))
    # THE ID IS NOT DECORATION, IT IS THE NEXT THING YOU TYPE. Truncating it to
    # thirty characters meant the longest ids could not be copied out of the
    # table at all, and both a play tester and a break tester lost time to
    # `start` refusing an id the table had just printed - with the refusal
    # helpfully suggesting they use `available` to find valid ids. Names get
    # cut instead; nobody has to retype a name.
    staff = e.get("needs_staff") or "-"
    if e.get("short_of_staff"):
        staff += "*"
    return "%-*s %-20s %9s %7s %5s %5s %8s %7s %6s %6s" % (
        w, (e.get("id") or ""), (e.get("name") or "")[:20],
        _fmt_num(e.get("cost")) + _cost_marker(e, purse),
        _fmt_num(hours), _fmt_num(years), _pct(risk),
        _fmt_range(e.get("earns_per_year")), _fmt_num(e.get("costs_per_year_after")),
        staff, rests)


def render_available(out):
    """A scannable table: every column aligned, sorted cheapest-first so the
    same eye scan works whether you are looking for a bargain or a subject.
    """
    L = ["AVAILABLE: %s startable now" % _fmt_num(out.get("count"))]
    if out.get("showing"):
        L.append(out["showing"])
    if out.get("sorted_by"):
        L.append("sorted by: %s" % out["sorted_by"])
    L.append("")
    # Sized to the longest id ON THIS PAGE, so the table stays aligned without
    # ever cutting the one string the player has to type next.
    _purse = out.get("you_could_raise_for_a_project")
    _rows_here = (out.get("available") or []) + (out.get("cheapest_now") or [])
    _w = max([34] + [len(r.get("id") or "") for r in _rows_here
                     if isinstance(r, dict)])
    header = ("%-*s %-20s %9s %7s %5s %5s %8s %7s %6s %6s"
              % (_w, "ID", "NAME", "COST", "HOURS", "YEARS", "RISK", "EARNS/YR",
                 "UPKEEP", "STAFF", "RESTS"))

    if "subjects" in out:
        L.append("%-24s %8s %10s %10s %10s" % ("SUBJECT", "THINGS", "CHEAPEST", "DEAREST", "AFFORD"))
        for r in out["subjects"]:
            L.append("%-24s %8s %10s %10s %10s" % (
                r["subject"][:24], _fmt_num(r["things"]), _fmt_num(r["cheapest"]),
                _fmt_num(r["dearest"]), _fmt_num(r["you_could_pay_for"])))
        L.append("")
        L.append("CHEAPEST SIX RIGHT NOW, sorted by cost:")
        L.append(header)
        for e in sorted(out.get("cheapest_six") or [], key=lambda e: e.get("cost", 0)):
            L.append(_available_row(e, _w, _purse))
        if out.get("most_rests_on_these"):
            L.append("")
            L.append("MOST RESTS ON THESE, of what you could begin today:")
            L.append(header)
            for e in out["most_rests_on_these"]:
                L.append(_available_row(e, _w, _purse))
        L.append("")
        for k, v in (out.get("to_see_more") or {}).items():
            L.append("  %s: %s" % (k, v))
    elif "available" in out and not out["available"]:
        # No column headings over no rows. A play tester read "1-0 matching
        # 'furnace'" above an empty table and could not tell whether the
        # search had failed or the game had.
        L.append(out.get("nothing_matched")
                 or "Nothing you could begin today matches that.")
    elif "available" in out:
        L.append(header)
        # IN THE ORDER THE REPLY GAVE IT, not re-sorted by cost here. A player
        # who asked for {"sort":"risk"} got a JSON list in risk order and a
        # printed table back in cost order underneath it - the JSON and the
        # words describing the same reply disagreeing about what "sorted"
        # meant. _agent_available already sorts the page exactly the way it
        # was asked to; the one thing this renderer must not do is undo that.
        for e in out["available"]:
            L.append(_available_row(e, _w, _purse))
        if out.get("more"):
            L.append("")
            L.append(out["more"])

    # LEGEND, once, and only when a table was actually printed. "1a*" means
    # nothing to a reader who has not been told; the column exists to be read
    # at a glance and a glance does not include guessing.
    _shown = ((out.get("available") or []) + (out.get("cheapest_six") or [])
              + (out.get("most_rests_on_these") or []))
    if _shown:
        L.append("")
        L.append("  STAFF is the standing people it needs: 2s = two scholars, "
                 "1a = one craftsman.")
        if any(e.get("short_of_staff") for e in _shown if isinstance(e, dict)):
            L.append("  A * after STAFF means you do not have them yet - 'hire' "
                     "or 'train' first, or the work waits.")
        if _purse is not None and any(_cost_marker(e, _purse) for e in _shown
                                      if isinstance(e, dict)):
            L.append("  A * after COST means you could not raise it today: "
                     "between cash and credit you can put %s into a project."
                     % _fmt_num(_purse))

    heard = out.get("heard_of_but_cannot_begin")
    if heard:
        L.append("")
        L.append("HEARD OF, CANNOT BEGIN YET:")
        for h in heard:
            L.append("  %-34s %s" % (h["id"], h.get("why_not") or ""))
        if out.get("and_more_you_have_heard_of"):
            L.append("  " + str(out["and_more_you_have_heard_of"]))
    if out.get("to_sort_or_page_differently"):
        L.append("")
        L.append(_wrap(out["to_sort_or_page_differently"]))
    if out.get("note"):
        L.append("")
        L.append(_wrap(out["note"]))
    return "\n".join(L)


def render_why(out):
    """A page about one thing: what it needs, what it costs, what depends
    on it, and whether you could start it today.
    """
    L = []
    title = "%s  [%s]" % (out.get("name"), out.get("id"))
    L.append(title)
    L.append("=" * min(78, len(title)))
    bits = []
    if out.get("tier") is not None:
        bits.append("tier %s" % out["tier"])
    if out.get("cat"):
        bits.append(out["cat"])
    if out.get("confidence"):
        bits.append("confidence %s" % out["confidence"])
    if bits:
        L.append(", ".join(bits))
    if out.get("note"):
        L.append("")
        L.append(_wrap(out["note"]))

    L.append("")
    cost = out.get("cost") or {}
    # EVERY FACTOR THAT IS MULTIPLIED IN. opposition_factor - bribes, delay, a
    # provincial site, a front man, up to 1.3x for work this society dislikes -
    # was in the JSON and not on this line, so a break tester multiplied the
    # printed terms out for three nodes, got 240 against 258, 200 against 230
    # and 10,075 against 10,831, and reported an undisclosed overhead. Third
    # time this exact lesson has been learned on this exact line: a breakdown
    # that omits a term invites the check and then fails it.
    L.append("COST: %s den total  (%s labour + %s materials + %s capital, then "
             "x%s your civ, x%s distance, x%s scarcity, x%s opposition, "
             "x%s prices)"
             % (_fmt_num(cost.get("total")), _fmt_num(cost.get("labour")),
                _fmt_num(cost.get("materials")), _fmt_num(cost.get("capital")),
                _factor(cost.get("civ_domain_factor")),
                _factor(cost.get("material_distance_factor")),
                _factor(cost.get("scarce_material_premium")),
                _factor(cost.get("opposition_factor")),
                _factor(cost.get("price_index"))))
    if cost.get("already_paid_towards_this"):
        L.append("!! %s den already sunk into this before it stopped: "
                 "'start' would actually charge %s den, not the total "
                 "above" % (_fmt_num(cost["already_paid_towards_this"]),
                            _fmt_num(cost.get("what_start_would_actually_charge"))))
    L.append("YOUR HOURS: %s     CALENDAR FLOOR: %s years     FAILURE RISK: %s"
             % (_fmt_num(out.get("founder_hours")), _fmt_num(out.get("calendar_floor_years")),
                _pct(out.get("risk"))))
    if out.get("attempts_already_failed"):
        L.append("ATTEMPTS ALREADY FAILED: %d. The risk above is what the next "
                 "attempt actually faces; it was %s before anyone tried. What "
                 "went wrong last time is not lost on the people who will try "
                 "again."
                 % (out["attempts_already_failed"],
                    _pct(out.get("risk_before_any_attempt"))))
    if out.get("failure_costs"):
        L.append("IF IT FAILS: %s gone (40%% of the money) and %s of your "
                 "hours to do again. It can fail more than once."
                 % (_fmt_num(out.get("failure_costs")),
                    _fmt_num(out.get("failure_costs_hours"))))
    staff, have = out.get("staff_needed") or {}, out.get("you_have") or {}
    L.append("STAFF NEEDED: %s scholars, %s artisans   (you have %s, %s%s)"
             % (_fmt_num(staff.get("scholars")), _fmt_num(staff.get("artisans")),
                _fmt_num(have.get("scholars")), _fmt_num(have.get("artisans")),
                (" - " + out["you_have_counts"]) if out.get("you_have_counts") else ""))
    for _k_warn in ("more_scholars_than_this_society_can_supply",
                    "more_craftsmen_than_your_household_can_hold"):
        if out.get(_k_warn):
            L.append(_wrap("  !! " + out[_k_warn], indent="     "))
    # A SECOND, SEPARATE STAFF FIGURE. Not shown at all until `open` refused
    # somebody on it, which is the exact complaint three play testers filed.
    # See staff_to_keep_it_open_means for why this is not the line above.
    open_staff = out.get("staff_to_keep_it_open")
    if open_staff is not None:
        L.append("STAFF TO KEEP IT OPEN: %s scholars, %s artisans   "
                 "(a separate, later requirement - see below)"
                 % (_fmt_num(open_staff.get("scholars")),
                    _fmt_num(open_staff.get("artisans"))))
        if out.get("staff_to_keep_it_open_means"):
            L.append(_wrap("  " + out["staff_to_keep_it_open_means"], indent="     "))
        if out.get("more_supervision_than_you_have_free_right_now"):
            L.append(_wrap("  !! " + out["more_supervision_than_you_have_free_right_now"],
                            indent="     "))
    lab = out.get("hired_labour") or {}
    if lab:
        L.append("HIRED LABOUR: " + ", ".join("%s %sh" % (t, _fmt_num(h)) for t, h in lab.items()))
    mat = out.get("materials") or {}
    if mat:
        L.append("MATERIALS: " + ", ".join("%s %s" % (m, _fmt_num(q)) for m, q in mat.items()))
    if out.get("upkeep") or out.get("revenue"):
        # A RANGE READS AS A RANGE, NOT AS TWO NUMBERS GLUED TOGETHER. See
        # _fog_revenue_estimate: under fog, on a thing nobody here has ever
        # run, this is a guess, and saying so is the whole point of showing
        # a guess instead of the true figure.
        _rev = out.get("revenue")
        _is_est = isinstance(_rev, (list, tuple))
        L.append("UPKEEP: %s den/yr     REVENUE: %s den/yr%s"
                 % (_fmt_num(out.get("upkeep")), _fmt_range(_rev),
                    " (nobody has run this here yet - a guess, not a fact)"
                    if _is_est else ""))
    if out.get("but_it_pays_YOU") is not None:
        L.append("  BUT IT PAYS YOU %s den/yr: %s"
                 % (_fmt_num(out["but_it_pays_YOU"]), out.get("because") or ""))
    if out.get("revenue_and_upkeep_apply_only_once_opened"):
        L.append("  NOT CHARGED OR EARNED UNTIL YOU OPEN IT: finishing this "
                 "buys the knowledge; the figures above only start moving "
                 "once you 'open' it.")
    if out.get("this_is_a_capability_you_must_keep_open"):
        L.append(_wrap("  KEEP THIS OPEN: " + out["this_is_a_capability_you_must_keep_open"],
                       indent="    "))

    L.append("")
    status = ("DONE" if out.get("done") else
              "ACTIVE" if out.get("active") else
              "CAN START NOW" if out.get("can_start_now") else "BLOCKED")
    L.append("STATUS: %s" % status)
    if out.get("active") and out.get("waiting_on"):
        L.append(_wrap("  waiting on: " + out["waiting_on"], indent="    "))
    if out.get("start_blocked_reason"):
        # start_blocked_reason is already the full, human-authored sentence -
        # when it is naming missing prerequisites (the common case) it says
        # so itself, and a second "MISSING PREREQUISITES: ..." line straight
        # after it was the same list twice, once wrapped in a sentence and
        # once bare. Show the sentence; it is the more complete of the two.
        L.append(_wrap(out["start_blocked_reason"], indent="  "))
    else:
        missing = out.get("missing_prerequisites")
        direct = out.get("direct_prerequisites")
        if out.get("held_without_building_it"):
            L.append("THIS SOCIETY ALREADY HAS THIS. You did not build it and "
                     "do not maintain it.")
            if direct:
                L.append("  (%s is how somebody who did not have it would get "
                         "there)" % ", ".join(direct))
        elif missing:
            L.append("MISSING PREREQUISITES: " + ", ".join(missing))
        elif direct:
            L.append("PREREQUISITES (all met, and finished counts for ever): "
                     + ", ".join(direct))
        else:
            L.append("PREREQUISITES: none, you can start this on arrival")
    # DONE, NOT MERELY OPEN - SAID ONCE, WHICHEVER BRANCH ABOVE ACTUALLY
    # FIRED. A tester wrote "nothing states whether a prerequisite must be
    # DONE or open"; it has always meant done, but the one sentence that used
    # to say so lived only in the `elif missing:` branch just above, which
    # start_blocked_reason (the common case - see its own comment) pre-empts
    # on every refusal that actually has missing prerequisites, so a player
    # who hit this refusal in the ordinary way never saw it at all. Printed
    # here instead, off the same `missing` list, it is reachable whichever of
    # the two branches actually wrote the list out.
    if out.get("missing_prerequisites"):
        L.append("  (a prerequisite has to be FINISHED, not merely started, "
                 "and it stays finished: you need not keep it running.)")

    if out.get("chain_size") is not None:
        L.append("")
        L.append("STILL TO BUILD BEHIND IT: %s of %s nodes, %s of your hours, %s den, %s-year serial floor"
                 % (_fmt_num(out["chain_size"]),
                    _fmt_num(out.get("chain_size_counting_what_you_have_built")),
                    _fmt_num(out.get("chain_founder_hours")),
                    _fmt_num(out.get("chain_cost")), _fmt_num(out.get("critical_path_years"))))

    unlocks = out.get("unlocks")
    if unlocks:
        L.append("")
        L.append("DIRECTLY UNLOCKS: " + ", ".join(unlocks))
    dc = out.get("downstream_count")
    if dc is not None:
        L.append("TOTAL DOWNSTREAM: %s thing(s) depend on this%s"
                 % (_fmt_num(dc), " -- INCLUDING THE GOAL" if out.get("on_goal_path") else ""))
    elif out.get("how_much_rests_on_this"):
        L.append("HOW MUCH RESTS ON THIS: %s" % out["how_much_rests_on_this"])

    if out.get("bounty_eligible_by_type"):
        L.append("")
        L.append("BOUNTY: yes, could be posted as a public prize")
    if out.get("trades_that_do_not_exist_here"):
        L.append("")
        L.append(_wrap(out.get("hired_labour_means") or ""))
        L.append("TRADES NOT YET TAUGHT HERE: " + ", ".join(out["trades_that_do_not_exist_here"]))
    if out.get("trades_taught_but_nobody_here_to_do_them_yet"):
        L.append("")
        L.append("TAUGHT, BUT NOBODY HERE TO DO IT YET: "
                 + ", ".join(out["trades_taught_but_nobody_here_to_do_them_yet"]))
        L.append(_wrap(out.get("trades_taught_but_nobody_here_means") or ""))
    if out.get("staff_needed_means"):
        L.append(_wrap(out["staff_needed_means"]))
    return "\n".join(L)


def render_step(out):
    # step()'s reply is completed/events stitched onto a full state() reply;
    # render_state already knows how to read completed/events off the front.
    return render_state(out)


def render_money(out):
    L = ["LEDGER"]
    L.append("Capital: %s den     Revenue: %s den/yr" % (_fmt_num(out.get("capital")), _fmt_num(out.get("revenue"))))
    src = out.get("where_the_money_comes_from") or {}
    if src:
        L.append("  from:")
        for k, v in sorted(src.items(),
                           key=lambda kv: -(kv[1] if isinstance(kv[1], (int, float)) else 0)):
            # The engine's own rows are node ids and must stay verbatim; the
            # aggregate lines are marked with a leading underscore so they sort
            # and read as what they are rather than as technologies.
            label = k[1:].replace("_", " ") if k.startswith("_") else k
            L.append("    %-38s %s" % (label, _fmt_num(v)))
        L.append("    %-38s %s" % ("(these add up to the revenue above)", ""))
        if out.get("still_building_up_custom"):
            L.append(_wrap("STILL BUILDING UP: " + out["still_building_up_custom"],
                           indent="    "))
        if out.get("about_your_own_practice"):
            L.append(_wrap("YOUR PRACTICE: " + out["about_your_own_practice"],
                           indent="    "))
        if out.get("the_market_you_sell_into"):
            L.append(_wrap("THE MARKET: " + out["the_market_you_sell_into"],
                           indent="    "))
    costs = out.get("what_it_costs_you") or {}
    if costs:
        L.append("Costs:")
        for k, v in costs.items():
            if v is None:
                continue
            L.append("  %-30s %s"
                     % (k.lstrip("_").replace("_", " "), _fmt_num(v)))
    L.append("Net/yr before the work in hand: %s   (recurring - `state` "
             "prints this same figure)     spent on projects last step: %s"
             % (_fmt_num(out.get("net_per_year")),
                _fmt_num(out.get("spent_on_projects_last_year"))))
    if out.get("net_after_project_spend") is not None:
        L.append("Net/yr after it: %s   (one-off; `state` prints this too, "
                 "alongside the recurring figure above)"
                 % _fmt_num(out.get("net_after_project_spend")))
    L.append("Credit limit: %s (%s used)     interest on arrears: %s     paid so far: %s"
             % (_fmt_num(out.get("credit_limit")),
                out.get("of_that_limit_you_have_used") or "none",
                _pct(out.get("interest_rate_on_arrears")),
                _fmt_num(out.get("interest_paid_in_total"))))
    if out.get("still_owed_on_work_in_hand"):
        L.append("Still owed on work in hand: %s" % _fmt_num(out["still_owed_on_work_in_hand"]))
    return "\n".join(L)


def render_stuck(out):
    L = ["WHY YOU ARE NOT GETTING ON"]
    L.append("  %s things you could begin, %s of them you could pay for"
             % (_fmt_num(out.get("you_could_begin")),
                _fmt_num(out.get("and_could_pay_for"))))
    if out.get("and_the_cheapest_thing_you_could_start_now"):
        L.append("  cheapest of them: %s"
                 % out["and_the_cheapest_thing_you_could_start_now"])
    rs = out.get("what_is_holding_you_up")
    L.append("")
    if isinstance(rs, str):
        L.append("  " + rs)
    else:
        for r in rs:
            L.append("  %s:" % str(r.get("what", "")).upper())
            if r.get("why"):
                L.append(_wrap(r["why"], indent="    "))
            for k, v in sorted((r.get("each_waiting_on") or {}).items()):
                L.append(_wrap("%s - waiting on %s" % (k, v), indent="    "))
            if r.get("the_nearest_few"):
                L.append(_wrap("nearest first: " + ", ".join(r["the_nearest_few"]),
                               indent="    "))
    hole = out.get("and_you_are_in_a_hole")
    if hole:
        L.append("")
        L.append("  " + str(hole.get("you_are_stuck", "")).upper())
        for w in hole.get("what_would_change_it") or []:
            L.append(_wrap("- " + w, indent="    "))
    if out.get("this_does_not_know_your_goal"):
        L.append("")
        L.append(_wrap(out["this_does_not_know_your_goal"], indent="  "))
    return "\n".join(L)


def render_mines(out):
    L = ["YOUR OWN WORKINGS"]
    rows = out.get("mines_you_own")
    if isinstance(rows, list) and rows:
        L.append("  %-9s %8s %10s %10s %6s %6s %10s" % (
            "MATERIAL", "SINCE", "RATED", "ACTUAL", "UTIL", "SUPPLY", "COST/YR"))
        for r in rows:
            yr = r.get("commissioned_year")
            yr_s = "%d" % yr if isinstance(yr, (int, float)) else str(yr)
            L.append("  %-9s %8s %10s %10s %6s %6s %10s%s"
                     % (r["material"], yr_s,
                        _fmt_num(r.get("rated_capacity_t_per_yr")),
                        _fmt_num(r.get("actual_output_t_per_yr")),
                        r.get("utilization") or "-",
                        "yes" if r.get("actually_supplying_demand") else "no",
                        _fmt_num(r["costs_you_a_year"]),
                        "   (ready %s)" % _fmt_num(r["ready_in"])
                        if r.get("ready_in") else ""))
        L.append("")
        L.append("  they cost %s den/yr in all, against revenue of %s"
                 % (_fmt_num(out.get("they_cost_you_a_year_in_all")),
                    _fmt_num(out.get("your_revenue_is"))))
        L.append("  shut one with 'close <material>' (shuts every working of "
                 "that material at once)")
    else:
        L.append("  none")
    pend = out.get("still_being_sunk") or {}
    if pend:
        L.append("")
        L.append("  still being sunk: "
                 + ", ".join("%s (ready %s)" % (m, _fmt_num(y))
                             for m, y in pend.items()))
    if out.get("note"):
        L.append("")
        L.append(_wrap(out["note"], indent="  "))
    return "\n".join(L)


def render_labour(out):
    if isinstance(out.get("trade"), dict):
        t = out["trade"]
        L = ["TRADE: %s (%s)" % (t.get("trade"), t.get("kind"))]
        L.append("exists here: %s" % t.get("exists_here"))
        L.append("a year of one: %s den     wage: %s den/hr" % (_fmt_num(t.get("a_year_of_one")), _fmt_num(t.get("wage_per_hour"))))
        L.append("you employ: %s     the town can supply: %s hours"
                 % (_fmt_num(t.get("you_employ")),
                    _fmt_num(t.get("hours_the_market_can_supply"))))
        if t.get("hours_your_own_people_add"):
            L.append("your own %ss add %s" % (t.get("trade"),
                                              _fmt_num(t.get("hours_your_own_people_add"))))
        if t.get("hours_you_could_still_commission"):
            L.append("and an outside shop would take on %s more hours at a "
                     "premium ('commission'); you have bought %s"
                     % (_fmt_num(t.get("hours_you_could_still_commission")),
                        _fmt_num(t.get("hours_you_have_commissioned"))))
        L.append("so %s hours a year are available to you in all"
                 % _fmt_num(t.get("hours_available_to_you_in_all")))
        if t.get("most_this_society_can_ever_supply") is not None:
            L.append("HEADCOUNT CEILING: %s %ss in total, ever, at any price - "
                     "you have or are teaching %s"
                     % (_fmt_num(t["most_this_society_can_ever_supply"]),
                        t.get("trade"), _fmt_num(t.get("you_have_or_are_teaching"))))
            L.append(_wrap("what widens it: " + str(t.get("what_widens_it") or ""),
                           indent="  "))
        if t.get("note"):
            L.append(_wrap(t["note"]))
        return "\n".join(L)
    L = ["LABOUR", "ON YOUR STAFF:"]
    staff = out.get("on_your_staff")
    _shown = False
    if isinstance(staff, list) and staff:
        _shown = True
        for r in staff:
            L.append("  %-16s %8s   %s den/yr each%s"
                     % (r["trade"], _fmt_num(r["you_employ"]),
                        _fmt_num(r["a_year_of_one"]),
                        "   (%s dearer than usual)" % r["dearer_than_usual_by"]
                        if r.get("dearer_than_usual_by") else ""))
    # PEOPLE YOU OWN OR HAVE FREED ARE YOUR HOUSEHOLD TOO. They are not
    # `employees` and so were never on this list: a weird-play tester bought
    # ten people and read "ON YOUR STAFF: nobody" and "EMPLOY: 0 people" while
    # the prompt said art 7, and concluded - reasonably - that the game had
    # lost track of their household. It had not; it was only showing one third
    # of it.
    if out.get("slaves"):
        _shown = True
        L.append("  %-16s %8s   held, not paid a wage"
                 % ("people you own", _fmt_num(out.get("slaves"))))
    if out.get("freedmen"):
        _shown = True
        L.append("  %-16s %8s   freed, and worth more for it"
                 % ("freedmen", _fmt_num(out.get("freedmen"))))
    if not _shown:
        L.append("  nobody")
    if out.get("household_places_in_all") is not None:
        L.append("")
        L.append("HOUSEHOLD PLACES: %s of %s used, room for %s more"
                 % (_fmt_num(out.get("household_places_used")),
                    _fmt_num(out.get("household_places_in_all")),
                    _fmt_num(out.get("room_for_more_people"))))
        if out.get("what_raises_that_room"):
            L.append(_wrap("  to make room: " + str(out["what_raises_that_room"]),
                           indent="  "))
        # THE OTHER CEILING, which is not room and cannot be built past. A
        # tester met it only inside a `hire` refusal in year 463 of a 500-year
        # game, and called it the single thing that decided the run.
        if out.get("and_how_many_of_the_lettered_trades_this_society_supplies"):
            L.append(_wrap("  the lettered trades: "
                           + out["and_how_many_of_the_lettered_trades_this_society_supplies"],
                           indent="  "))
    L.append("")
    L.append("YOU COULD HIRE: " + (", ".join(out.get("you_could_hire_here") or []) or "nobody new"))
    if out.get("only_the_ones_you_taught"):
        L.append("EXISTS ONLY BECAUSE YOU TAUGHT IT: "
                 + ", ".join(out["only_the_ones_you_taught"])
                 + "   (no market; teach more, or they come only from your own)")
    L.append("MUST BE TAUGHT: " + (", ".join(out.get("do_not_exist_here") or []) or "none"))
    training = out.get("in_training")
    if training:
        L.append("")
        L.append("IN TRAINING:")
        for r in training:
            L.append("  %s x%s, ready %s" % (r.get("trade"), _fmt_num(r.get("people")), r.get("ready_year")))
    L.append("")
    L.append("Total employed: %s     annual wage bill: %s den"
             % (_fmt_num(out.get("you_employ_in_total")), _fmt_num(out.get("annual_wage_bill"))))
    if out.get("note"):
        L.append("")
        L.append(_wrap(out["note"]))
    return "\n".join(L)


def render_ventures(out):
    """What you run and what you could. This fell through to the generic
    key/value dump, which prints a list of dicts as raw Python - a tester
    reported "ventures dumps raw Python dicts" and they were reading exactly
    that."""
    L = ["CONCERNS"]
    free = out.get("people_free_to_run_something_new") or {}
    L.append("free to put behind something new: %s scholars, %s craftsmen%s"
             % (_fmt_num(free.get("scholars")), _fmt_num(free.get("craftsmen")),
                "   (one of each of those is you)"
                if out.get("one_of_each_of_those_is_you") else ""))
    _hi = out.get("you_have_in_all") or {}
    _hh = out.get("held_in_all") or {}
    if _hi:
        L.append("you have %s scholars and %s craftsmen in all; %s and %s of "
                 "them are watching a concern"
                 % (_fmt_num(_hi.get("scholars")), _fmt_num(_hi.get("craftsmen")),
                    _fmt_num(_hh.get("scholars")), _fmt_num(_hh.get("craftsmen"))))
    _holders = out.get("and_these_concerns_are_holding_the_rest")
    if isinstance(_holders, list) and _holders:
        L.append("")
        L.append("  %-34s %10s %10s" % ("HELD BY", "SCHOLARS", "CRAFTSMEN"))
        for r in _holders:
            L.append("  %-34s %10s %10s"
                     % (r["id"], _fmt_num(r["scholars"]), _fmt_num(r["craftsmen"])))
    if out.get("these_are_not_interchangeable"):
        L.append("")
        L.append(_wrap(out["these_are_not_interchangeable"], indent="  "))
    L.append("")
    run = out.get("running")
    L.append("RUNNING")
    if isinstance(run, list) and run:
        L.append("  %-34s %10s %10s %8s" % ("ID", "EARNS/YR", "COSTS/YR", "NEEDS"))
        for r in run:
            nd = r.get("needs") or {}
            L.append("  %-34s %10s %10s %4s sch %3s cr%s"
                     % (r.get("id"), _fmt_num(r.get("earns_a_year")),
                        _fmt_num(r.get("costs_a_year")),
                        _fmt_num(nd.get("scholars")), _fmt_num(nd.get("craftsmen")),
                        "   [CAPABILITY - see below]" if r.get("capability") else ""))
    else:
        L.append("  nothing")
    idle = out.get("you_know_how_but_have_not_opened")
    L.append("")
    L.append("YOU KNOW HOW, AND HAVE NOT OPENED  (ordinary earn/cost businesses)")
    if isinstance(idle, list) and idle:
        L.append("  %-34s %10s %10s %10s" % ("ID", "EARNS/YR", "COSTS/YR", "TO OPEN"))
        for r in idle:
            L.append("  %-34s %10s %10s %10s"
                     % (r.get("id"), _fmt_num(r.get("earns_a_year")),
                        _fmt_num(r.get("costs_a_year")), _fmt_num(r.get("to_open_it"))))
    else:
        L.append("  nothing")
    if out.get("and_more_you_could_open"):
        L.append("  ...and %s more" % _fmt_num(out["and_more_you_could_open"]))
    # CAPABILITIES ARE NOT EARN/COST DECISIONS, and a table that scored them
    # as one is exactly what put identity_cover and patron_local in the same
    # row a Rome player could not tell apart. A separate heading, with money
    # figures still shown for reference but a standing warning that money is
    # not the whole story here.
    cap_idle = out.get("capabilities_you_know_how_to_run_but_have_not_opened")
    if isinstance(cap_idle, list) and cap_idle:
        L.append("")
        L.append("YOU KNOW HOW, AND HAVE NOT OPENED  (capabilities - NOT judged "
                 "on money alone; 'why <id>' says what each one actually does)")
        L.append("  %-34s %10s %10s %10s" % ("ID", "EARNS/YR", "COSTS/YR", "TO OPEN"))
        for r in cap_idle:
            L.append("  %-34s %10s %10s %10s"
                     % (r.get("id"), _fmt_num(r.get("earns_a_year")),
                        _fmt_num(r.get("costs_a_year")), _fmt_num(r.get("to_open_it"))))
    if out.get("your_practice_is_not_a_venture"):
        L.append("")
        L.append(_wrap("YOUR PRACTICE (not a concern, and not listed above): "
                       + out["your_practice_is_not_a_venture"]))
    if out.get("note"):
        L.append("")
        L.append(_wrap(out["note"]))
    return "\n".join(L)


def render_risk(out):
    kr = out.get("knowledge_risk") or out
    year = out.get("year")
    L = ["KNOWLEDGE AT RISK"]
    L.append("technologies at risk: %s     chance lost if a site is sacked: %s     fraction lost when it happens: %s"
             % (_fmt_num(kr.get("technologies_at_risk")), _pct(kr.get("loss_chance_if_a_site_is_sacked")),
                _pct(kr.get("fraction_lost_when_it_happens"))))
    L.append("hedge: %s" % (kr.get("hedged_by") or "none yet"))
    if kr.get("you_have_already_lost"):
        L.append("")
        L.append("ALREADY LOST TO A SACKING: %s technolog%s, most recently in %s"
                 % (_fmt_num(kr["you_have_already_lost"]),
                    "y" if kr["you_have_already_lost"] == 1 else "ies",
                    _fmt_num(kr.get("the_most_recent_went_in"))))
        L.append(_wrap("you have to build these again: "
                       + ", ".join(kr.get("and_have_to_build_again") or []),
                       indent="  "))
    if kr.get("note"):
        L.append(_wrap(kr["note"]))
    L.append("")
    for h in kr.get("known_hazards_ahead") or []:
        yrs = h.get("years") or [0, 0]
        tag = "IN PROGRESS" if h.get("in_progress") else "%s-%s" % (yrs[0], yrs[-1])
        L.append("[%s] %s" % (tag, h.get("name")))
        # REPEATED ROLLS, NOT ONE. A per-year percentage over a window that
        # can run decades reads as one low-stakes check, and it is not one:
        # the engine rolls it independently EVERY year the window is open
        # (SocietyMixin._shocks runs once per simulated year, and this same
        # hazard is tested again each time). A Rome player, shown a figure
        # like this and told nothing about the window, built the hedges the
        # game suggested, was sacked twice in the same window anyway, and
        # lost about 300,000 denarii and 17 in-progress projects. Say what
        # the window actually adds up to, not only the one year's die.
        _p_year = h.get("sack_chance_per_year")
        if _p_year:
            _y0, _y1 = yrs[0], yrs[-1]
            _from = max(_y0, year) if year is not None else _y0
            _span = max(1, int(round(_y1 - _from)) + 1)
            _p_eff = h.get("sack_chance_after_what_you_have_built")
            _p_use = _p_eff if _p_eff is not None else _p_year
            _cum = 1.0 - (1.0 - max(0.0, min(1.0, _p_use))) ** _span
            L.append("  %s a year, checked EVERY year of this %d-year window "
                     "- not once: about %s chance at least one sacking lands "
                     "somewhere in it before the window closes"
                     % (_pct(_p_year), _span, _pct(_cum)))
        if h.get("note"):
            L.append(_wrap(h["note"], indent="  "))
        for kind, advice in (h.get("what_you_can_do") or {}).items():
            L.append(_advice_line(kind, advice))
        for kind in ("sack_chance", "staff_loss"):
            after = h.get("%s_after_what_you_have_built" % kind)
            if after is not None:
                L.append("  %s after what you have built: %s" % (kind.replace("_", " "), _pct(after)))
    return "\n".join(L)


def _advice_line(kind, advice, indent="  "):
    """One hazard's exposure, in a sentence rather than a bare dict repr -
    playing this through a real run, {'you_currently_take': 1.0, 'because_of':
    [], 'what_would_help': '...'} printed as literal Python was the single
    worst line in the whole rendering.
    """
    if not isinstance(advice, dict):
        return "%s%s: %s" % (indent, kind.replace("_", " "), advice)
    take = advice.get("you_currently_take")
    because = advice.get("because_of") or []
    line = "%s%s: you take %s of it" % (indent, kind.replace("_", " "), _pct(take))
    if because:
        line += " (softened by %s)" % ", ".join(because)
    help_ = advice.get("what_would_help")
    if help_:
        line += "\n%s  what would help: %s" % (indent, help_)
    # AND WHICH OF THE THINGS IN FRONT OF YOU IS ONE OF THOSE. A playtester was
    # told the answer to the Spanish was "walls, firearms, powerful friends",
    # then played 154 years with 269 startable things in view and reported
    # finding no hedge of any kind. Naming the ones they can already see costs
    # nothing and is the difference between advice and a slogan.
    steps = advice.get("you_could_begin_now_toward_it") or []
    now = [e for e in steps if e.get("can_begin_now")]
    later = [e for e in steps if not e.get("can_begin_now")]
    if now:
        line += "\n%s  you could begin now: %s" % (
            indent, ", ".join("%s (%s, %s)"
                              % (e["id"], _fmt_num(e["cost"]),
                                 e.get("because_it_gives_you") or "a hedge")
                              for e in now))
    for e in later[:2]:
        line += "\n%s  %s is one of them, waiting on: %s" % (
            indent, e["id"], (e.get("waiting_on") or "").split(". To get")[0])
    return line


def render_generic(resp, indent=""):
    """Every other reply: a plain key: value dump, numbers made readable.

    Nothing here needs a bespoke renderer to be worth reading - hire, buy,
    quote and the rest are already a handful of fields - so this is the
    fallback for all of them rather than one function apiece.
    """
    L = []
    for k, v in resp.items():
        if k == "ok":
            continue
        label = k.replace("_", " ")
        if isinstance(v, dict):
            if v:
                L.append("%s%s:" % (indent, label))
                L.append(render_generic(v, indent + "  "))
            else:
                L.append("%s%s: (none)" % (indent, label))
        elif isinstance(v, list):
            if not v:
                L.append("%s%s: (none)" % (indent, label))
            elif all(isinstance(x, (str, int, float)) and not isinstance(x, bool) for x in v):
                L.append("%s%s: %s" % (indent, label, ", ".join(_fmt_num(x) if isinstance(x, (int, float)) else str(x) for x in v)))
            else:
                L.append("%s%s:" % (indent, label))
                for item in v:
                    if isinstance(item, dict):
                        L.append(indent + "  - " + ", ".join("%s=%s" % (kk, vv) for kk, vv in item.items()))
                    else:
                        L.append("%s  - %s" % (indent, item))
        elif isinstance(v, (int, float)) and not isinstance(v, bool):
            L.append("%s%s: %s" % (indent, label, _fmt_num(v)))
        else:
            L.append("%s%s: %s" % (indent, label, v))
    return "\n".join(L)


def render_log(out):
    """Your own history, a year and a line at a time, newest first by default.

    Plain lines rather than a table: these are sentences, of wildly varying
    length - "FAILED at X" runs to three clauses, "hired 2 smiths" is four
    words - and forcing them into columns would either truncate the long ones
    or waste most of a line of blank padding on the short ones.
    """
    L = ["HISTORY: %s" % _fmt_num(out.get("count"))]
    if out.get("showing"):
        L.append(out["showing"])
    L.append("")
    if out.get("note") and not out.get("entries"):
        L.append(out["note"])
    for e in out.get("entries") or []:
        L.append("  %4s AD  %s" % (e.get("year"), e.get("what")))
    if out.get("more"):
        L.append("")
        L.append(out["more"])
    if out.get("to_filter_or_sort"):
        L.append("")
        L.append(_wrap(out["to_filter_or_sort"]))
    return "\n".join(L)


def render_policy(out):
    """The switches, under a plain statement of what they are.

    The generic renderer printed the warning below AFTER the list of eleven
    switches and their descriptions, unwrapped, as a single eighty-word line
    that a player scanning for a switch name would never read. The whole point
    of that paragraph is that it is read BEFORE somebody turns one on.
    """
    L = ["AUTOMATIC BEHAVIOUR"]
    if out.get("these_are_approximations_not_optimal_play"):
        L.append(_wrap(out["these_are_approximations_not_optimal_play"],
                       indent="  "))
        L.append("")
    # GROUPED BY WHETHER THEY ARE ACTUALLY RUNNING, not listed alphabetically
    # with the state as a word at the end of a name. An England play tester
    # read "auto_open ... opens concerns that plainly pay for themselves",
    # built a pawnshop that plainly paid for itself, watched nothing happen,
    # and wrote it up as the policy not matching its own description. The
    # screen was right - "off" was printed directly above that sentence - but
    # every description here is in the present indicative, so a reader
    # scanning descriptions reads eleven statements of what the game is doing
    # and has to carry a separate column in their head to know that ten of
    # them are hypothetical. Two headings cost nothing and remove the
    # ambiguity: what is running, and what is not.
    pol = out.get("policy") or {}
    does = out.get("what_each_does") or {}
    on = [k for k in sorted(pol) if pol[k]]
    off = [k for k in sorted(pol) if not pol[k]]
    for head, keys, empty in (
            ("RUNNING NOW:", on, "  nothing is automatic just now: every one "
                                 "of these is off, and the game does only "
                                 "what you tell it to."),
            ("NOT RUNNING - these describe what each WOULD do if you turned "
             "it on:", off, None)):
        if not keys:
            if empty:
                L.append("")
                L.append(_wrap(empty))
            continue
        L.append("")
        L.append("  " + head if len(head) < 40 else _wrap("  " + head))
        for k in keys:
            L.append("  %-18s %s" % (k, "ON" if pol[k] else "off"))
            if does.get(k):
                L.append(_wrap(does[k], width=DISPLAY_WIDTH - 8,
                               indent="        "))
    if out.get("changed"):
        L.append("")
        L.append("  changed: %s" % out["changed"])
    stopped = out.get("stopped_by") or out.get("but")
    if stopped:
        L.append("")
        L.append("  NOT ACTING JUST NOW:")
        if isinstance(stopped, dict):
            for k, v in sorted(stopped.items()):
                L.append(_wrap("%s - %s" % (k, v), indent="    "))
        else:
            L.append(_wrap(str(stopped), indent="    "))
    return "\n".join(L)


def render_rush(out):
    L = ["RUSH: %d started, %d not" % (out.get("count_started", 0),
                                       out.get("count_not_started", 0))]
    for r in out.get("started") or []:
        L.append("  STARTED %s (%s): %s" % (r.get("id"), _fmt_num(r.get("cost")),
                                            r.get("name")))
    for r in out.get("not_started") or []:
        L.append("  NOT STARTED %s: %s" % (r.get("id"), r.get("why")))
    if out.get("this_is_an_approximation_not_optimal_play"):
        L.append("")
        L.append(_wrap(out["this_is_an_approximation_not_optimal_play"]))
    if out.get("note"):
        L.append("")
        L.append(_wrap(out["note"]))
    return "\n".join(L)


def render_path(out):
    """The route to one goal, and - the join nobody had - which of the
    nodes still standing between here and there you could actually begin
    today. See the op handler's own comment: two players asked for exactly
    this, and a third built their own script outside the game to get it.
    """
    L = ["ROUTE TO %s  [%s]" % (out.get("name"), out.get("id"))]
    if out.get("done"):
        L.append("You have already built this.")
        return "\n".join(L)
    L.append("%s node(s) still stand between here and there; %s of them you "
             "could start TODAY, %s are still waiting on something else"
             % (_fmt_num(out.get("remaining_count")),
                _fmt_num(out.get("startable_today_count")),
                _fmt_num(out.get("still_waiting_on_something_else"))))
    L.append("")
    rows = out.get("startable_today_toward_this")
    L.append("STARTABLE TODAY, TOWARD THIS GOAL  (cheapest first)")
    if isinstance(rows, list) and rows:
        _w = max([34] + [len(e.get("id") or "") for e in rows])
        L.append("%-*s %-20s %9s %7s %5s %5s %8s %7s %6s %6s"
                 % (_w, "ID", "NAME", "COST", "HOURS", "YEARS", "RISK", "EARNS/YR",
                    "UPKEEP", "STAFF", "RESTS"))
        for e in rows:
            L.append(_available_row(e, _w, None))
        if out.get("and_more_startable_today"):
            L.append("...and %s more" % _fmt_num(out["and_more_startable_today"]))
    else:
        L.append("  nothing - " + (out.get("note") or
                 "everything left on this route is waiting on something else"))
    if out.get("on_this_route_but_shut_down"):
        L.append("")
        L.append("ON THIS ROUTE BUT SHUT DOWN: "
                 + ", ".join(out["on_this_route_but_shut_down"]))
        if out.get("reopen_them_with"):
            L.append(_wrap("  " + out["reopen_them_with"]))
    if out.get("this_route_pays_for_nothing"):
        L.append("")
        L.append(_wrap("!! " + out["this_route_pays_for_nothing"]))
    if out.get("these_together_cost_more_than_you_can_raise"):
        L.append(_wrap("!! " + out["these_together_cost_more_than_you_can_raise"]))
    return "\n".join(L)


_RENDERERS = {
    "policy": render_policy,
    "state": render_state, "step": render_step, "available": render_available,
    "why": render_why, "money": render_money, "ledger": render_money,
    "accounts": render_money, "labour": render_labour, "risk": render_risk,
    "hazards": render_risk, "ventures": render_ventures, "path": render_path,
    "mines": render_mines, "workings": render_mines,
    "stuck": render_stuck, "log": render_log, "history": render_log,
    "values": render_values, "rush": render_rush,
    "capacity": render_capacity, "industry": render_capacity,
    "dashboard": render_capacity, "portfolio": render_portfolio,
    "economy": render_economy, "changes": render_changes,
    "final": render_final, "score": render_score,
}


# A REPLY IS FULL OF WORKED EXAMPLES, and until now every one of them was
# JSON: 'more: knowledge_risk -> {"cmd":"risk"}'. That is exactly right when a
# script is reading, and exactly wrong in front of a person who has just been
# told to type words. The JSON payload itself must not change - it is the
# protocol - so the translation happens here, on the rendered text only, and
# only when the caller says the reader is typing.
TYPED_HINTS = False
# The short form used in the compact lines ("400 den", "net +12 den/yr"). Set
# alongside TYPED_HINTS by whichever front end is rendering; see MONEY_WORDS.
MONEY_SHORT = "den"

# HOW WIDE A LINE IS, AND HOW MANY ROWS A PAGE SHOWS, BEFORE A PLAYER ASKS
# FOR SOMETHING ELSE. Both used to be bare numbers scattered through _wrap's
# own default, _available_row's column floor, and _agent_available's page
# slice - which means the game was silently assuming one terminal size and
# one page length for everyone, and a player whose actual terminal was
# narrower lost ids off the edge of a table they meant to copy one out of.
# These are APPLICATION preferences now (cli.py's main-menu Options screen,
# "display width" and "rows per table"; see settings.py's module docstring
# for why they are application-level and not part of any one save), set
# once at the top of cli.py's human-facing entry points - the menu and
# `play` - via cli.py's _apply_display_prefs. `agent` never calls it: its
# JSON protocol (and the --pretty rendering alongside it) is a stable
# machine interface and must render exactly as it always has regardless of
# whichever human happens to be running the script, on whatever terminal.
# The values below are exactly what every caller already hardcoded, so a
# process that never touches these (every `agent` invocation, and any
# `play`/menu session before a player has ever opened Options) renders
# byte-for-byte as it did before this existed.
DISPLAY_WIDTH = 76
DEFAULT_AVAILABLE_LIMIT = 30


def _typed_form(obj):
    """One command dict written the way a person would type it."""
    op = obj.get("cmd")
    if not op:
        return None
    bits = [str(op)]
    if op == "policy" and isinstance(obj.get("set"), dict):
        for k, v in obj["set"].items():
            bits += [str(k), "on" if v else "off"]
        return " ".join(bits)
    for key in ("id", "topic", "trade", "what", "material", "subject", "group",
                "file", "path"):
        if obj.get(key) not in (None, "", False):
            bits.append(str(obj[key]))
    for key, word in (("find", "find"), ("search", "find"), ("afford", "afford"),
                      ("limit", "limit"), ("offset", "offset")):
        if obj.get(key) not in (None, "", False):
            bits += [word, _fmt_num(obj[key]) if key != "find" and key != "search"
                     else str(obj[key])]
    for key in ("years", "n", "hours", "amount"):
        if obj.get(key) not in (None, "", False):
            bits.append(_fmt_num(obj[key]))
    if obj.get("all") is True:
        bits.append("all")
    if obj.get("full") is True:
        bits.append("full")
    return " ".join(bits)


# Values may be a bare word rather than a literal: several hints are written as
# worked examples with a placeholder in them ({"cmd":"buy","what":"slaves",
# "n":N}), which is not valid JSON and so survived the first version of this
# untouched, in front of a person who had been told to type words.
_JSON_HINT = re.compile(r'\{"cmd"\s*:\s*"[a-z_]+"(?:\s*,\s*"[a-z_]+"\s*:\s*'
                        r'(?:"[^"]*"|-?[0-9.]+|true|false|[A-Za-z_][A-Za-z0-9_]*'
                        r'|\{[^{}]*\}))*\}')
_JSON_PAIR = re.compile(r'"([a-z_]+)"\s*:\s*("(?:[^"]*)"|-?[0-9.]+|true|false'
                        r'|[A-Za-z_][A-Za-z0-9_]*)')


def _typed_deep(obj):
    """to_typed_hints applied to every string a renderer is about to read.

    Keys are left alone: a field name is protocol, and only the values a
    person reads get rewritten. Same rule, and same reason, as
    _localise_money.
    """
    if isinstance(obj, str):
        return to_typed_hints(obj)
    if isinstance(obj, list):
        return [_typed_deep(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _typed_deep(v) for k, v in obj.items()}
    return obj


def to_typed_hints(text):
    """Rewrite every {"cmd":...} example in rendered text as a typed command.
    Best-effort: anything that will not parse is left exactly as it was."""
    def sub(m):
        raw = m.group(0)
        try:
            obj = json.loads(raw)
        except ValueError:
            # A worked example with a placeholder in it. Read the pairs off
            # textually and keep the placeholder as the player sees it.
            obj = {}
            for key, val in _JSON_PAIR.findall(raw):
                obj[key] = val[1:-1] if val.startswith('"') else val
            if "cmd" not in obj:
                return raw
        return _typed_form(obj) or raw
    return _JSON_HINT.sub(sub, text)


_DEN_RE = re.compile(r"\bden\b")


def render_pretty(op, resp):
    """The human rendering of one reply. Never touches stdout or the JSON
    itself - see cli.py, which prints this to stderr alongside the unchanged
    JSON line, only when --pretty is on.

    Rendering is best-effort ON PURPOSE: a bug in a formatter must cost the
    formatting, never the session. The JSON already went to stdout by the
    time this is called, so the worst this function can do is print an
    apology instead of a pretty table.
    """
    try:
        if isinstance(resp, dict) and resp.get("ok") is False:
            err = render_error(resp)
            return to_typed_hints(err) if TYPED_HINTS else err
        fn = _RENDERERS.get((op or "").strip().lower(), render_generic)
        # REWRITE THE HINTS BEFORE WRAPPING, NOT AFTER. This ran on the
        # finished page, so a paragraph wrapped at 76 columns around a long
        # {"cmd":"hire","trade":"smith","n":3} and then had it replaced by
        # `hire smith 3`, leaving a ragged half-width block wherever the game
        # explains what to type - which is most of the places it explains
        # anything. Wrapping the final words is the only way the line lengths
        # can be right.
        out = fn(_typed_deep(resp) if TYPED_HINTS else resp)
        if MONEY_SHORT != "den":
            # "Money: 400 den" in a game counted in pence was the other half of
            # the currency work, and a tester duly reported "pence vs den mixed
            # throughout".
            out = _DEN_RE.sub(MONEY_SHORT, out)
        return to_typed_hints(out) if TYPED_HINTS else out
    except Exception as e:
        return "(could not render a readable view of this reply: %s: %s)" % (type(e).__name__, e)


SAVE_SUFFIXES = (".json", ".save")


def _unsafe_path(path):
    """None if this is a reasonable place for a save file; a refusal if not.

    Deliberately conservative rather than clever: a save must be a .json or
    .save file, must not be absolute, and must not climb out of where the game
    was started. That covers writing into /etc, which a tester did, without
    pretending to be a security boundary - anyone who can send commands to this
    process can already run code as this user. It is here so the ordinary
    accident does not happen, not because a sandbox exists.
    """
    if os.path.isabs(path):
        return ("a save file must be a relative path, not an absolute one. "
                "Try {\"cmd\":\"save\",\"file\":\"mygame.json\"}")
    norm = os.path.normpath(path)
    if norm.startswith(".." + os.sep) or norm == "..":
        return "a save file cannot be written outside the directory you started in"
    if not norm.lower().endswith(SAVE_SUFFIXES):
        return "a save file should end in %s" % " or ".join(SAVE_SUFFIXES)
    return None


def _qty(cmd, key, default=None):
    """Read a quantity, or say why it is not one. Returns (value, error).

    _num() silently substitutes a default for anything it cannot read, which
    meant {"cmd":"hire","trade":"smith","n":"banana"} hired one smith and
    echoed "n": "banana" back in the reply as though that had been honoured.
    A number that cannot be read is a mistake, and the useful thing to do with
    a mistake is name it. A numeric string is still accepted, because "5" is
    unambiguous and refusing it helps nobody.
    """
    v = cmd.get(key, default)
    if v is None:
        return None, "%s is required" % key
    if isinstance(v, bool):
        return None, "%s must be a number, not true or false" % key
    if isinstance(v, (int, float)):
        f = float(v)
    elif isinstance(v, str):
        try:
            f = float(v.strip())
        except ValueError:
            return None, "%s must be a number, not %r" % (key, v)
    else:
        return None, "%s must be a number, not %s" % (key, type(v).__name__)
    if f != f or f in (float("inf"), float("-inf")):
        return None, ("%s must be a real number; NaN and Infinity are not "
                      "quantities" % key)
    # A QUANTITY, NOT A FLOAT EXPERIMENT. `hire smith 999999999999999999999`
    # was answered with "hiring 1e+21 smiths costs 281250000000000012058624
    # denarii" - a refusal, but one written in scientific notation and binary
    # rounding error, which is the game losing its composure rather than
    # keeping it. Nothing in this world comes in more than a billion.
    if abs(f) > 1e9:
        return None, ("%s must be a quantity of something real. There are not "
                      "a thousand million of anything here" % key)
    return f, None


def _num(v, default=0.0):
    """Read a number from a command without ever raising at the player.

    NaN AND INFINITY ARE NOT NUMBERS FOR THIS PURPOSE. Python's json accepts
    bare NaN and Infinity as an extension, float() accepts the strings, and
    every comparison against NaN is False - so `NaN` walked through every "must
    be greater than zero" guard in the game, set capital to NaN permanently,
    made everything free, and then got written into the save file as bare NaN,
    which is not legal JSON and cannot be read back by anything else. A tester
    bought 999,999 hectares of woodland with 400 denarii this way.
    """
    try:
        f = float(v)
    except (TypeError, ValueError):
        return float(default)
    if f != f or f in (float("inf"), float("-inf")):
        return float(default)
    return f


def _clean(v):
    """True if this is a real, finite number (or something that is not a number
    at all and will be rejected elsewhere). False only for NaN and infinity."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return True
    return v == v and v not in (float("inf"), float("-inf"))


def _flag(v, default=False):
    """Read a switch. "false", "no", "0" and "" are all off.

    A tester set a policy to the STRING "false" and it came back true, because
    bool("false") is true. Every other language on earth has this bug too and it
    is still a bug.
    """
    if isinstance(v, str):
        return v.strip().lower() not in ("", "false", "no", "off", "0", "none")
    return bool(default if v is None else v)


# Every command the dispatcher answers to, in the order a player meets them.
# Kept beside the dispatcher so that adding a command and forgetting to
# advertise it is a visible omission rather than a silent one.
KNOWN_COMMANDS = (
    "state", "available", "why", "path", "start", "stop", "rush", "step",
    "money", "risk", "values", "labour", "policy", "help", "log",
    "hire", "fire", "train", "commission", "work",
    "buy", "quote", "close", "bounty", "mothball", "restore", "bribe",
    "open", "ventures", "withdraw", "mines", "stuck",
    "capacity", "economy", "changes", "score", "portfolio",
    "save", "load", "quit",
)


# ---------------------------------------------------------------------------
# TYPED COMMANDS, for a person at a keyboard.
#
# Everything a player can do lived only in the JSON protocol above. `play` -
# the human front door - understood six things: next year, available, status,
# start, stop, quit. Money, hiring, teaching a trade, working for wages,
# policy, the ledger, saving: a human could not reach any of it without
# typing JSON at a prompt, and the menu's answer was to hand them
# {"cmd":"available"} and wish them luck.
#
# So this is a parser and NOT a second implementation. It turns a typed line
# into exactly the dict the JSON protocol takes, and hands it to the same
# _agent_dispatch below. There is one command set, one set of rules, and one
# place a new command has to be added. A typed game and a scripted game
# cannot disagree about what the game is, because underneath they are the
# same call.
# ---------------------------------------------------------------------------

# What a person types on the left, the protocol's own name on the right. The
# single letters are the ones `play` has always used, kept because the older
# notes and anyone who has played before will still type them.
TYPED_ALIASES = {
    "s": "state", "st": "state", "status": "state",
    "a": "available", "av": "available", "options": "available",
    "n": "step", "next": "step", "wait": "step", "year": "step",
    "x": "stop", "abandon": "stop", "cancel": "stop",
    "q": "quit", "exit": "quit", "bye": "quit",
    "h": "help", "?": "help", "commands": "help",
    "ledger": "money", "accounts": "money", "cash": "money",
    "hazards": "risk", "risks": "risk",
    "history": "log", "diary": "log", "logs": "log", "journal": "log",
    "people": "labour", "staff": "labour", "workers": "labour",
    "dismiss": "fire", "sack": "fire", "lay": "fire",
    "job": "commission", "hireout": "commission",
    "teach": "train", "learn": "train",
    "price": "quote", "cost": "quote",
    "shut": "close", "closemine": "close", "close_mine": "close",
    "begin": "start", "research": "start", "build": "start",
    "explain": "why", "look": "why", "inspect": "why",
    "route": "path", "plan": "path",
    "workings": "mines", "mine": "mines", "pits": "mines",
    "blocked": "stuck", "help_me": "stuck", "why_stuck": "stuck",
    "retire": "withdraw", "step_back": "withdraw", "obscurity": "withdraw",
    "beliefs": "values", "traits": "values", "society": "values",
    "startall": "rush", "start_all": "rush", "muster": "rush",
    "overview": "capacity", "industry": "capacity", "dashboard": "capacity",
    "infrastructure": "capacity", "power": "capacity",
    "prices": "economy", "econ": "economy",
    "diff": "changes", "recap": "changes", "summary": "changes",
}


def _typed_number(tok):
    """The token as a number, or None. Tolerates 1,000 and 1_000 because
    people type both, and a thousand-separator is not a syntax error."""
    try:
        return float(str(tok).replace(",", "").replace("_", ""))
    except (TypeError, ValueError):
        return None


# The real ids, and a case-folded index onto them. Built once: parse_typed has
# no Sim to ask and runs on every line a player types. One load(), not two -
# it re-reads both tree files from disk and re-derives every node's cost, and
# this file already pays that once per process for NODE_IDS; NODE_NAME_NORM
# below reuses the same dict rather than paying it again.
_NODES_ONCE = load()[2]
NODE_IDS = frozenset(_NODES_ONCE)
NODE_IDS_LOWER = {k.lower(): k for k in NODE_IDS}


def _norm_name(text):
    """Fold case and punctuation, so a typed name matches what the game
    printed however it was capitalised or punctuated.

    Every screen in this game prints the NAME ("Horizontal loom") and every
    command up to now took only the ID ("tex_horizontal_loom") - testers
    found that jarring often enough to say so in almost identical words. A
    player copying a name back exactly, in any case, with or without the
    comma a name like "Loom, treadle" carries, has to land on the same key.
    """
    return re.sub(r"[^a-z0-9]+", " ", str(text).lower()).strip()


# NAMES ARE NOT UNIQUE THE WAY IDS ARE - the tree has several nodes called
# things like "Bronze casting" at different tiers - so this maps one
# normalised name onto every id that carries it, and resolution (below)
# decides whether that is one answer or a question back to the player.
# Built once, alongside NODE_IDS_LOWER, for the same reason: no Sim exists yet
# when a typed line first has to be read.
NODE_NAME_NORM = defaultdict(list)
for _nn_k, _nn_n in _NODES_ONCE.items():
    NODE_NAME_NORM[_norm_name(_nn_n["name"])].append(_nn_k)
del _nn_k, _nn_n


def _resolve_by_name(text):
    """Every id whose name matches `text`, case and punctuation folded.

    Exact match first, so that typing a name back verbatim - which is what a
    player does after reading it off `state` or `available` - always lands on
    every node that carries exactly that name, never something merely close
    to it. Failing that, a unique prefix or a distinctive (4+ character)
    substring works too, the same generosity `_did_you_mean` already gives an
    id typo, extended to names because a player cannot be expected to know
    that names, unlike ids, are not unique.
    """
    q = _norm_name(text)
    if not q:
        return []
    exact = NODE_NAME_NORM.get(q)
    if exact:
        return list(exact)
    if len(q) < 3:
        return []            # too short to mean anything as a name fragment
    prefix = [k for nm, ids in NODE_NAME_NORM.items() if nm.startswith(q) for k in ids]
    if prefix:
        return prefix
    if len(q) >= 4:
        return [k for nm, ids in NODE_NAME_NORM.items() if q in nm for k in ids]
    return []


def _absorb_key_colons(rest, flag_keys, value_keys):
    """Normalise 'key:value' typed tokens into the plain words the rest of a
    command's own parser already reads one at a time.

    'sort:risk' becomes the two words 'sort', 'risk' - value_keys, where the
    value matters. 'all:true' becomes the one bare word 'all'; 'all:false'
    is dropped outright, the same as never typing it - flag_keys, a word
    whose own presence IS the value and which a command's follow-up loop
    turns into True on sight.

    Every one of these was the same break, found three times: a typed
    key:value pair that `help commands` itself advertises fell straight
    through a loop that only read bare words, with no error - 'available
    all:true' became a search for the literal string "all:true" and quietly
    matched nothing, then 'available ... limit:N', then 'available
    reverse:true'. Fixing the instance in front of you each time is how it
    kept coming back in a fourth command; this is the one place it is fixed
    for every caller that uses it, including the next one.
    """
    out = []
    for w in rest:
        t = str(w)
        if ":" in t:
            a, _, b = t.partition(":")
            al = a.lower()
            if al in flag_keys:
                if b.lower() in ("false", "0", "no", "off"):
                    continue          # same as never having typed it
                out.append(a)
                continue
            if al in value_keys:
                out.append(a)
                if b:
                    out.append(b)
                continue
        out.append(t)
    return out


def parse_typed(line):
    """One typed line -> (command dict, None), or (None, a refusal to show).

    Returns (None, None) for a blank line: nothing to do and nothing to say.
    """
    if line is None:
        return None, None
    text = line.strip()
    if not text:
        return None, None
    # A player who has read the JSON docs, or pasted from their own notes,
    # should not be told their own game's protocol is a syntax error.
    if text.startswith("{"):
        try:
            obj = json.loads(text)
        except ValueError as e:
            return None, "that looked like JSON but would not parse: %s" % e
        if isinstance(obj, dict) and "cmd" in obj:
            return obj, None
        return None, "a JSON command needs a 'cmd' field."

    # ONE COMMAND PER LINE. `step 1; step 1` advanced a single year and said
    # nothing about the half of the line it dropped. Silently doing part of what
    # was asked is the worst of the three options; the other two are doing all
    # of it or saying you will not.
    if ";" in text:
        first = text.split(";")[0].strip()
        return None, ("one command per line - I will not guess which half you "
                      "meant. Send %r on its own line, then the next."
                      % (first or text.strip()))
    parts = text.split()
    head = parts[0].lower()
    rest = parts[1:]
    op = TYPED_ALIASES.get(head, head)
    if op not in KNOWN_COMMANDS:
        near = [c for c in KNOWN_COMMANDS if c.startswith(head[:3])]
        return None, ("no command called %r. Type 'help' for the list%s."
                      % (head, (", or did you mean: " + ", ".join(near)) if near else ""))

    words = [w for w in rest if _typed_number(w) is None]
    nums = [_typed_number(w) for w in rest if _typed_number(w) is not None]

    if op in ("money", "values", "quit", "score"):
        return {"cmd": op}, None

    if op == "risk":
        # 'risk json' prints the raw reply - see 'portfolio json' and
        # 'state json' just below for the same fix in the same family.
        return {"cmd": "risk",
               "json": "json" in [w.lower() for w in words]}, None

    if op == "rush":
        # 'rush' alone starts everything you could begin today; 'rush 5',
        # 'rush limit:5' and 'rush limit 5' all cap it at the first five,
        # highest-leverage first.
        #
        # limit:N IS THE FORM THE HELP TEXT ADVERTISES - "add limit:N to cap
        # it" - and it was the one form this did not accept. `limit:3` is not
        # a number, so `nums` came back empty, no limit was set, and the
        # command went on to start everything startable. A player who read
        # the help, wanted three things, and typed exactly what it told them
        # to type got twenty-one projects and every denarius of their credit.
        # The safest-looking spelling of the most expensive command in the
        # game was the one that removed the safety, silently. Same key:value
        # spelling `state full:true` already takes.
        out = {"cmd": "rush"}
        _lim = None
        for w in rest:
            t = str(w)
            for pre in ("limit:", "limit=", "n:", "n="):
                if t.lower().startswith(pre):
                    v = _typed_number(t[len(pre):])
                    if v is None:
                        # AND A CAP THAT DID NOT PARSE IS A REFUSAL, not a
                        # shrug. Falling through to no limit at all means the
                        # one typo a player can make while trying to be
                        # careful is the typo that starts everything.
                        return None, ("'%s' is not a number of things to "
                                      "start. 'rush limit:3' begins the three "
                                      "highest-leverage things you could "
                                      "begin today; 'rush' alone begins every "
                                      "one of them." % t[len(pre):])
                    _lim = v
                    break
        if _lim is None and nums:
            _lim = nums[0]
        if _lim is not None:
            out["limit"] = int(_lim)
        return out, None

    if op == "state":
        # 'state full' and 'state full:true' both mean the same thing, and a
        # player who has read the JSON docs will type the second. 'state
        # json' (in any position, 'state full json' included) prints the
        # raw reply instead of the rendered screen: every player of this
        # game is an AI agent parsing text, and several have lost runs to
        # parsing prose that was never meant to be machine-readable.
        low_rest = [w.lower() for w in rest]
        want_full = bool(rest) and low_rest[0].split(":")[0] == "full"
        out = {"cmd": "state", "full": want_full}
        if "json" in low_rest:
            out["json"] = True
        return out, None

    if op == "available":
        # 'available' alone is the digest. The rest are the same narrowings the
        # digest itself suggests, spelled the way a person would say them:
        #   available metallurgy      available find furnace
        #   available afford 900      available all
        #   available limit 30 offset 30
        #   available find furnace sort risk reverse
        out = {"cmd": "available"}
        # key:value AND key value, BOTH. This loop read bare words only, so
        # `available all:true` - the spelling `help commands` itself gives -
        # fell all the way through to the subject branch at the bottom and was
        # used as a search string named "all:true", silently matching nothing.
        # A Han player reported it as a documentation bug and was right; the
        # same hole swallowed limit:30, find:furnace and every other pair, and
        # - found later, same shape exactly - `reverse:true`, which fell
        # through to the same subject branch and was read as a search for the
        # literal text "reverse:true". See _absorb_key_colons, which now does
        # this for every caller rather than once per command found missing it.
        rest = _absorb_key_colons(
            rest,
            flag_keys=("all", "reverse", "reversed", "desc", "descending"),
            value_keys=("find", "search", "named", "afford", "under", "within",
                        "limit", "offset", "heard", "heard_offset", "sort"))
        low = [w.lower() for w in rest]
        i = 0
        while i < len(low):
            w = low[i]
            nxt = low[i + 1] if i + 1 < len(low) else None
            if w == "all":
                out["all"] = True
            elif w in ("find", "search", "named") and nxt:
                out["find"] = nxt; i += 1
            elif w in ("afford", "under", "within") and nxt is not None:
                out["afford"] = _typed_number(nxt) or 0; i += 1
            elif w == "limit" and nxt is not None:
                out["limit"] = int(_typed_number(nxt) or 0); i += 1
            elif w == "offset" and nxt is not None:
                out["offset"] = int(_typed_number(nxt) or 0); i += 1
            elif w in ("heard", "heard_offset") and nxt is not None:
                out["heard_offset"] = int(_typed_number(nxt) or 0); i += 1
            # SORT AND REVERSE, spelled the way a person would type them:
            # 'available sort risk reverse'. A break tester paging through
            # "632 more, nearest first" by hand, thirty at a time, is exactly
            # the failure a typed synonym for the JSON 'sort' field exists to
            # stop.
            elif w == "sort" and nxt:
                out["sort"] = nxt; i += 1
            elif w in ("reverse", "reversed", "desc", "descending"):
                out["reverse"] = True
            elif _typed_number(w) is not None:
                out["afford"] = _typed_number(w)
            elif w in ("subject", "group", "in") and nxt:
                out["subject"] = " ".join(rest[i + 1:])
                break
            else:
                # A bare word is a subject: 'available metallurgy'. Subjects are
                # several words long ("roads, bridges and canals"), so take the
                # whole tail rather than one token.
                out["subject"] = " ".join(rest[i:])
                break
            i += 1
        return out, None

    if op == "help":
        return {"cmd": "help", "topic": (rest[0].lower() if rest else None)}, None

    if op == "step":
        # A bare 'n' is one year, which is what it has always meant - but
        # `step abc` is not a bare 'n'. That fell through to the default and
        # silently advanced a year, while `step 0` and `step -5` were properly
        # refused: a weird-play tester found the inconsistency and it is the
        # worst kind, because the accepted case does something other than what
        # was asked and says nothing.
        if rest and not nums:
            return None, ("step takes a number of years, e.g. 'step 5', or "
                          "nothing at all for one. %r is not a number."
                          % " ".join(rest))
        return {"cmd": "step", "years": (nums[0] if nums else 1)}, None

    if op == "ventures":
        return {"cmd": "ventures"}, None

    if op == "log":
        # 'log' alone is the twenty most recent lines. The same narrowings
        # 'available' takes, spelled the way a person would say them:
        #   log failures              log find plague
        #   log since 300             log before 200 oldest
        #   log limit 50 offset 50
        out = {"cmd": "log"}
        # SAME FAMILY, SAME FIX. 'log failures:true' was the same shape as
        # 'available all:true' - a key:value pair `help` never tells anyone
        # NOT to type, read by a loop that only matched bare words - except
        # here there is no subject fallback to land in, so it failed even
        # more quietly: the flag was simply dropped, with the command
        # reporting ok:true on a plain, unfiltered log instead of erroring or
        # searching. See _absorb_key_colons.
        rest = _absorb_key_colons(
            rest,
            flag_keys=("failures", "failure", "fails", "fail",
                      "oldest", "forward", "newest", "backward", "recent"),
            value_keys=("find", "search", "since", "before", "limit", "offset"))
        low = [w.lower() for w in rest]
        i = 0
        while i < len(low):
            w = low[i]
            nxt = low[i + 1] if i + 1 < len(low) else None
            if w in ("failures", "failure", "fails", "fail"):
                out["failures"] = True
            elif w in ("find", "search") and nxt:
                out["find"] = nxt; i += 1
            elif w == "since" and nxt is not None:
                out["since"] = int(_typed_number(nxt) or 0); i += 1
            elif w == "before" and nxt is not None:
                out["before"] = int(_typed_number(nxt) or 0); i += 1
            elif w == "limit" and nxt is not None:
                out["limit"] = int(_typed_number(nxt) or 0); i += 1
            elif w == "offset" and nxt is not None:
                out["offset"] = int(_typed_number(nxt) or 0); i += 1
            elif w in ("oldest", "forward"):
                out["order"] = "oldest"
            elif w in ("newest", "backward", "recent"):
                out["order"] = "newest"
            elif _typed_number(w) is not None:
                out["limit"] = int(_typed_number(w))
            i += 1
        return out, None

    if op == "open" and nums:
        # A TRAILING NUMBER IS UNITS, NOT PART OF THE NAME. 'open
        # school_founded 2' founds a second school - see
        # ProjectsMixin._expand_institution. No id is only digits, so a
        # number anywhere in the line is unambiguously this, not a stray word
        # of a multi-word name.
        want = " ".join(words)
        if want not in NODE_IDS:
            want = NODE_IDS_LOWER.get(want.lower(), want)
        return {"cmd": "open", "id": want, "units": nums[-1]}, None

    if op in ("why", "path", "start", "stop", "bounty", "mothball",
              "restore", "open"):
        if not rest:
            return None, ("%s needs the name of a technology, e.g. '%s "
                          "fud_wheelbarrow'. 'available' lists what you can "
                          "begin now." % (op, op))
        # MATCHED CASE-INSENSITIVELY, NOT LOWERCASED. `WHY AG2_MARLING` was
        # refused with "did you mean: ag2_marling", the game naming the right
        # answer and declining to act on it - but flattening the case broke
        # eleven ids that genuinely carry capitals, among them the whole
        # cap_pure_2N/4N/6N/9N purity ladder, which sits on the critical path
        # to germanium. A play tester lost the endgame to it and could only get
        # past it by falling back to the raw JSON form. So: try what was typed,
        # then try a case-insensitive match against the real ids, and keep
        # whatever the tree actually calls it.
        #
        # THE WHOLE REST OF THE LINE, NOT JUST rest[0]. Every screen in this
        # game prints a NAME - "Horizontal loom", two words - and every one of
        # these commands took only an id until now, so 'why horizontal loom'
        # silently discarded 'loom' and asked about a nonexistent 'horizontal'.
        # A single id never has a space in it, so joining the whole tail costs
        # a one-word id nothing and is what a multi-word name needs. Names are
        # not unique, so this does not resolve them here - _agent_dispatch_inner
        # does that, because resolving under fog has to filter candidates by
        # what the player has actually heard of, which needs the live Sim this
        # function does not have.
        want = " ".join(rest)
        if want not in NODE_IDS:
            want = NODE_IDS_LOWER.get(want.lower(), want)
        return {"cmd": op, "id": want}, None

    if op in ("withdraw", "retire"):
        return {"cmd": "withdraw"}, None

    if op == "mines":
        return {"cmd": "mines"}, None

    if op == "stuck":
        return {"cmd": "stuck"}, None

    if op == "capacity":
        return {"cmd": "capacity"}, None

    if op == "portfolio":
        # 'portfolio json' prints the raw reply instead of the rendered
        # table - see _absorb_key_colons's own family of fixes for why this
        # is scanned across all of `words`, not just rest[0]: a player typing
        # 'portfolio json' after reading the JSON docs should not have that
        # silently ignored the way 'state full' once would have been had it
        # come second. Every player of this game is an AI agent parsing
        # text, and prose is not a stable interface to parse.
        return {"cmd": "portfolio",
               "json": "json" in [w.lower() for w in words]}, None

    if op == "economy":
        return {"cmd": "economy", "full": "full" in [w.lower() for w in words]}, None

    if op == "changes":
        # 'changes' alone means the last 5 years; 'changes 10' means ten.
        return {"cmd": "changes", "years": (nums[0] if nums else 5)}, None

    if op == "bribe":
        if not nums:
            return None, "bribe needs an amount, e.g. 'bribe 500'."
        return {"cmd": "bribe", "amount": nums[0]}, None

    if op == "labour":
        # A PLAYER WHO TYPES THE FIELD NAME MEANS THE FIELD. The help shows
        # {"cmd":"labour","trade":"smith"}, so `labour trade smith` is the
        # obvious typed reading of it, and it was answered with "no such trade:
        # trade". Same for `available subject metallurgy`, which quietly
        # searched for a subject literally called "subject metallurgy" and
        # reported nothing startable.
        _w = [x for x in words if x.lower() != "trade"]
        return {"cmd": "labour", "trade": (_w[0].lower() if _w else None)}, None

    if op in ("hire", "fire"):
        if not words:
            return None, ("%s needs a trade, e.g. '%s smith 2'. 'labour' lists "
                          "which trades exist here." % (op, op))
        return {"cmd": op, "trade": words[0].lower(),
                "n": (nums[0] if nums else 1)}, None

    if op in ("work", "commission"):
        if not words:
            return None, ("%s needs a trade and a number of hours, e.g. "
                          "'%s smith 200'." % (op, op))
        if not nums:
            return None, "%s needs a number of hours, e.g. '%s %s 200'." % (op, op, words[0])
        return {"cmd": op, "trade": words[0].lower(), "hours": nums[0]}, None

    if op == "train":
        # 'train smith 2' and 'train smith 2 from labourer' both read naturally.
        src_trade = None
        low = [w.lower() for w in words]
        if "from" in low:
            i = low.index("from")
            if i + 1 < len(low):
                src_trade = low[i + 1]
            low = low[:i]
        if not low:
            return None, ("train needs a trade to teach, e.g. 'train smith 2' "
                          "or 'train chemist 1 from artisan'.")
        out = {"cmd": "train", "trade": low[0], "n": (nums[0] if nums else 1)}
        if src_trade:
            out["from"] = src_trade
        return out, None

    if op in ("buy", "quote"):
        if not words:
            return None, ("%s needs something to %s, e.g. '%s iron 500'."
                          % (op, op, op))
        # 'buy mine coal 500' and 'quote mine iron 200' are the forms the help
        # itself gives, and the first version of this parser took only the FIRST
        # word and threw the material away - so every documented three-word buy
        # failed with an error that listed the material the player had just
        # typed. A weird-play tester lost the whole mining subsystem to it.
        out = {"cmd": op, "what": words[0].lower()}
        if len(words) > 1:
            out["material"] = words[1].lower()
        elif out["what"] in ("mine", "mines"):
            return None, "say which mineral, e.g. '%s mine coal 500'." % op
        # 'buy coal 500' means the same thing and is what a person types; the
        # protocol wants it spelled out as a mine in a mineral.
        if out["what"] in ("nitre", "saltpetre", "nitre_bed"):
            out["what"] = "nitre"
        elif out["what"] not in ("forest", "slaves", "mine", "mines", "people",
                                 "manumit", "manumission", "free"):
            out["material"], out["what"] = out["what"], "mine"
        if out["what"] == "mines":
            out["what"] = "mine"
        if nums:
            out["n"] = nums[0]
        return out, None

    if op == "close":
        if not words:
            return None, "close needs a mine, e.g. 'close iron'."
        # 'close mine coal' and 'close coal' both mean the one thing close does.
        mat = words[1].lower() if len(words) > 1 else words[0].lower()
        return {"cmd": "close", "what": mat, "material": mat}, None

    if op == "policy":
        if not rest:
            return {"cmd": "policy"}, None
        if len(rest) < 2:
            return None, ("to change one, say which and whether, e.g. "
                          "'policy auto_hire off'. Bare 'policy' lists them.")
        val = rest[1].lower()
        if val in ("on", "true", "yes", "y", "1"):
            flag = True
        elif val in ("off", "false", "no", "n", "0"):
            flag = False
        else:
            return None, "say 'on' or 'off', e.g. 'policy auto_hire off'."
        return {"cmd": "policy", "set": {rest[0].lower(): flag}}, None

    if op in ("save", "load"):
        if not rest:
            return None, "%s needs a file name, e.g. '%s mygame.json'." % (op, op)
        return {"cmd": op, "file": rest[0]}, None

    # Any command added to KNOWN_COMMANDS that this parser has not been taught
    # about still reaches the dispatcher rather than being refused here.
    return {"cmd": op}, None


# Every command that names a technology. Under fog, NONE of them may say
# anything about one you have not heard of - including refusing it for a reason
# that describes it.
_ID_COMMANDS = ("why", "path", "start", "stop", "bounty", "mothball", "restore")

# Every command whose `id` a typed NAME should resolve onto, before anything
# else touches it. `open` is not in _ID_COMMANDS above - it is safe without
# the fog guard, because you can only open something you have already done -
# but a player still types its name, not its id, so it needs the same
# resolution the fog-guarded commands get.
_NAME_COMMANDS = _ID_COMMANDS + ("open",)


def _downstream_of(k, nodes):
    """Everything that depends on this node, however far away, following hard
    prerequisites AND substitution groups alike.

    NOT closure(), which answers a different question. closure() is what you
    MUST have, so it follows `pre` only, and it has to: a req_any group is a
    list of alternatives and treating every option as required would balloon
    the goal's own prerequisite set with things nobody needs. But "what rests
    on this" is the reverse question, and there a substitution option counts,
    because something really would be harder or impossible without it. The
    chinampa read "TOTAL DOWNSTREAM: 0" while genuinely feeding terracing.
    """
    seen, stack = set(), [k]
    while stack:
        cur = stack.pop()
        for m in _unlocked_by(cur, nodes):
            if m not in seen:
                seen.add(m)
                stack.append(m)
    seen.discard(k)
    return seen


def _unlocked_by(k, nodes):
    """Everything that needs this node, whether hard or as one option of a
    substitution group. sorted() because a set of ids iterates in an order
    that depends on PYTHONHASHSEED."""
    out = set()
    for m, v in nodes.items():
        if k in v["pre"]:
            out.add(m)
            continue
        for g in (v.get("req_any") or []):
            if k in (g.get("options") or {}):
                out.add(m)
                break
    return sorted(out)


def _did_you_mean(k, nodes, limit=8, s=None):
    """Names close to what was typed.

    This was a plain substring test, so it helped with a truncation and not at
    all with a typo: one wrong character and the answer was the literal words
    "did you mean: no idea". Substring first, because a partial name is the
    common case and an exact prefix is a better guess than anything fuzzy, then
    difflib for the rest.
    """
    q = str(k).lower()
    near = [x for x in nodes if q in x.lower()]
    if len(near) < limit:
        import difflib
        for x in difflib.get_close_matches(q, list(nodes), n=limit, cutoff=0.6):
            if x not in near:
                near.append(x)
    # A word from the middle of a name is a real attempt too: "wheelbarrow"
    # should find fud_wheelbarrow even when the fuzzy score does not.
    # A SUBSTANTIAL word from the middle of a name is a real attempt too:
    # "wheelbarrow" should find lnd_wheelbarrow. Four characters minimum,
    # because matching on "fud" or "ag2" returns every node in the branch and
    # buries the one good answer under seven bad ones.
    if len(near) < limit:
        parts = [w for w in q.split("_") if len(w) >= 4]
        for x in nodes:
            if any(w in x.lower() for w in parts) and x not in near:
                near.append(x)
            if len(near) >= limit:
                break
    # NOT THROUGH THE FOG. `help fog` says in as many words that there is no
    # way to view the whole tree, and `path` is properly disabled - and then a
    # misspelling was answered out of the complete namespace. A weird-play
    # tester typed `why transistor` and was handed junction_transistor and
    # point_contact_transistor; `why vacuum`, `why steam` and `why
    # semiconductor` each dumped eight hidden ids, and they pointed out that
    # two-letter prefixes would reconstruct the entire tree. A suggestion is
    # still a statement about what exists.
    if s is not None and getattr(s, "fog", False):
        memo = {}
        near = [x for x in near if s.is_visible(x, _memo=memo)]
    return near[:limit]


_MONEY_RE = re.compile(r"\bdenarii\b|\bdenarius\b")


def _localise_words(obj, pairs):
    """Rewrite the phrases this civilisation says differently.

    Same mechanism as _localise_money and the same reason: the tree is written
    from Rome 100 AD and stays that way, and a play tester in Han China should
    not be told they are writing their corpus "in plain quantitative Greek and
    Latin" and seeking "Senatorial patronage". Only phrases specific enough to
    occur nowhere else; a historical note ABOUT Rome is left alone, because it
    is about Rome.
    """
    if not pairs:
        return obj
    if isinstance(obj, str):
        for a, b in pairs:
            if a in obj:
                obj = obj.replace(a, b)
        return obj
    if isinstance(obj, list):
        return [_localise_words(x, pairs) for x in obj]
    if isinstance(obj, dict):
        # Keys are protocol; only the values a person reads get rewritten.
        return {k: _localise_words(v, pairs) for k, v in obj.items()}
    return obj


def _localise_money(obj, word):
    """Rewrite the unit of account in anything a player is about to read.

    Every message in the engine is written in denarii because the whole price
    model is calibrated to Rome 100 AD, which is a real modelling decision and
    stays. What does not have to stay is telling a player in 1300 England, or
    in Tenochtitlan, that they are counting Roman coins. This is the one place
    every reply passes through, so the substitution happens once here rather
    than in the twenty-odd messages that mention money.
    """
    if word in ("denarii", "denarius"):
        return obj
    if isinstance(obj, str):
        return _MONEY_RE.sub(word, obj)
    if isinstance(obj, list):
        return [_localise_money(x, word) for x in obj]
    if isinstance(obj, dict):
        # KEYS ARE NOT PROSE. A field name is part of the protocol and scripts
        # match on it; only the values a person reads get rewritten.
        return {k: _localise_money(v, word) for k, v in obj.items()}
    return obj


def _agent_dispatch(s, nodes, cmd):
    """Every reply, in the money of the place you are standing in."""
    _out = _localise_money(_agent_dispatch_inner(s, nodes, cmd), money_word(s.civ))
    return _localise_words(_out, ((s.civ.get("local_words") or {}).get("pairs")))


def _agent_dispatch_inner(s, nodes, cmd):
    if not isinstance(cmd, dict) or "cmd" not in cmd:
        return {"ok": False, "error": "each line must be a JSON object with a 'cmd' field, "
                                      "e.g. {\"cmd\":\"state\"}"}
    # A NAME RESOLVES TO AN ID, BEFORE ANYTHING ELSE READS IT. Every screen in
    # this game prints the human NAME - "Horizontal loom" - and every command
    # that acts on a technology took only the machine id - "tex_horizontal_
    # loom" - until now; testers called that jarring often enough, in close
    # to the same words, that it stopped being a style choice. This has to run
    # before the fog guard just below: that guard reads cmd["id"] straight off
    # the command, so a name that resolves to exactly one id must already BE
    # that id by the time the guard looks at it, or a perfectly good name
    # would be refused as something the player had never heard of. `id` still
    # takes a raw id unchanged - this only fires when what was given is NOT
    # already one, so scripts and the `agent` protocol lose nothing.
    if (isinstance(cmd.get("cmd"), str) and isinstance(cmd.get("id"), str)
            and cmd["cmd"].strip().lower() in _NAME_COMMANDS
            and cmd["id"] not in nodes):
        _name_cands = _resolve_by_name(cmd["id"])
        if getattr(s, "fog", False):
            # ONLY WHAT THE PLAYER HAS ACTUALLY HEARD OF. Two nodes can share
            # a name where one is built and the other is still beyond the
            # fog; handing back the hidden one as a candidate to disambiguate
            # between is exactly the leak the fog guard below exists to close,
            # so the filter runs before a player ever sees the list, not after.
            _name_memo = {}
            _goal = getattr(s, "goal", None)
            # THE GOAL'S NAME GETS THE SAME NARROW EXCEPTION ITS ID ALREADY
            # HAS, on `why` alone - see the fog guard's own comment on
            # _goal_why just below. Without this, a player who only ever
            # learned the goal's NAME (under fog its id is never shown; see
            # _agent_state's "goal" field) typed it into `why` and was told
            # "you have never heard of any such thing" about the one thing
            # they were told by name on arrival. It is gated on an EXACT match
            # of the goal's own name, not the prefix/substring tiers: a vague
            # guess like "transistor" must stay refused, the same way
            # `_did_you_mean` already refuses to suggest the goal for one.
            _exact_here = NODE_NAME_NORM.get(_norm_name(cmd["id"]), ())
            _op_lc = cmd["cmd"].strip().lower()
            _name_cands = [
                k for k in _name_cands
                if s.is_visible(k, _memo=_name_memo)
                or (k == _goal and _op_lc == "why" and k in _exact_here)]
        if len(_name_cands) == 1:
            cmd = dict(cmd, id=_name_cands[0])
        elif len(_name_cands) > 1:
            _name_cands = sorted(_name_cands, key=lambda k: (nodes[k]["name"], k))
            return {"ok": False,
                    "error": ("more than one thing is called that; say which "
                              "by id: %s%s"
                              % (", ".join("%s (%s)" % (k, nodes[k]["name"])
                                           for k in _name_cands[:10]),
                                 " and %d more" % (len(_name_cands) - 10)
                                 if len(_name_cands) > 10 else ""))}
        # Otherwise: no match by name either. Fall through with cmd["id"]
        # untouched, so the ordinary unknown-id handling further down - and
        # the fog guard immediately below it - answer it exactly as they
        # already do for a mistyped id, did-you-mean included.
    # ONE GUARD, FOR EVERY COMMAND THAT TAKES AN ID. `why` checked visibility
    # and `bounty` did not: it checked prerequisites first, so refusing a
    # bounty on the goal node printed the goal's seven missing prerequisites by
    # name. A break tester crawled that error recursively and recovered 134
    # hidden technology ids and the entire dependency graph to the transistor
    # in six rounds, with fog on the whole time. Patching bounty alone would
    # leave the next command that grows an id to make the same mistake, so the
    # check lives here, once, before any handler sees the id.
    if getattr(s, "fog", False) and isinstance(cmd.get("cmd"), str):
        _op = cmd["cmd"].strip().lower()
        _k = cmd.get("id")
        # THE SAME ANSWER WHETHER OR NOT IT EXISTS. Refusing an unheard-of node
        # with "you have never heard of that" and a nonexistent one with
        # "unknown node 'X'" makes the two distinguishable, and that difference
        # IS the tree: a break tester classified ten real technologies and five
        # invented ones from sixteen plain-English guesses, on a fogged save,
        # in one pass. `help fog` promises there is no way to view the whole
        # tree, and a question you can ask about any name at all, and get a
        # true answer to, is a way to view the whole tree.
        # THE ONE EXCEPTION IS `why` ON THE GOAL. The status line names the goal
        # every single turn - "Aiming at: Point-contact transistor" - and this
        # answered `why point_contact_transistor` with "you have never heard of
        # any such thing", then offered fin_contract_law as what the player
        # might have meant, for the first 187 years of a play tester's run.
        # Being told what you are for and then told you have never heard of it
        # is a contradiction, not fog. It is `why` alone, and not is_visible
        # itself, because making the goal visible reopened the exact exploit
        # this guard exists to close: `bounty` on the goal then printed its
        # seven missing prerequisites by name, and a break tester once crawled
        # that error recursively to recover 134 hidden ids. `why` under fog
        # already says only "this needs 7 other things you have not heard of
        # yet", which is the honest answer.
        _goal_why = (_op == "why" and _k == getattr(s, "goal", None))
        if _op in _ID_COMMANDS and isinstance(_k, str) and not _goal_why and (
                _k not in nodes or not s.is_visible(_k)):
            if _k == getattr(s, "goal", None):
                # You know its name; you were handed it on arrival. Telling you
                # that you have never heard of the thing you are aiming at, and
                # then guessing you meant fin_contract_law, is absurd on its
                # face. Saying nothing MORE than "not yet" leaks nothing.
                return {"ok": False,
                        "error": "that is what you are aiming at, and you cannot "
                                 "act on it yet: everything it rests on is still "
                                 "beyond what you have heard of. 'why %s' is all "
                                 "of it you can see from here." % _k}
            near = _did_you_mean(_k, nodes, s=s)
            # SAY WHERE THE SUGGESTIONS COME FROM. The suggestions are already
            # filtered through is_visible, so nothing hidden is ever named -
            # but this said "you have never heard of any such thing... nothing
            # tells you what lies beyond that" and then listed three ids, and a
            # break tester reasonably read that as the fog leaking and filed it
            # as their second most serious finding. It was a false alarm: the
            # three they saw were two of Rome's own granted crafts and one
            # thing standing startable in front of them. A refusal that
            # manufactures false bug reports is costing real work, so the
            # sentence now says which of the two the suggestions are.
            return {"ok": False,
                    "error": "you have never heard of any such thing. You know "
                             "what you have built and what you could begin next; "
                             "nothing tells you what lies beyond that.%s"
                             % ((" Among the things you DO know, did you mean: "
                                 + ", ".join(near)) if near else "")}
    op = cmd.get("cmd")
    ended = _agent_end_reason(s)

    if op in ("help", "?", "commands"):
        return {"ok": True, "help": _agent_help(s, cmd.get("topic"))}

    # One central guard rather than five. A playtester sent {"id": {"a": 1}} and
    # the process died on `k not in nodes` with an unhashable-type TypeError,
    # losing the whole session. A malformed command must cost you the command,
    # never the game.
    if "id" in cmd and not isinstance(cmd["id"], str):
        return {"ok": False,
                "error": "id must be a name in quotes, not %s. Nothing was changed."
                         % type(cmd["id"]).__name__}

    # NaN and Infinity, anywhere in the command, before anything is touched.
    bad = sorted(k for k, v in cmd.items() if not _clean(v))
    if bad:
        return {"ok": False,
                "error": "%s must be a real number; NaN and Infinity are not "
                         "quantities. Nothing was changed." % ", ".join(bad)}

    if op == "state":
        return dict(ok=True, **_agent_state(s, nodes, cmd))

    if op == "available":
        return _agent_available(s, nodes, cmd)

    if op == "log":
        return _agent_log(s, cmd)

    if op == "score":
        return {"ok": True, **score_report(s, nodes)}

    if op == "why":
        k = cmd.get("id")
        # The goal is the one thing you were told the name of on arrival; see
        # the _goal_why note on the fog guard above for why it is `why` alone.
        if (isinstance(k, str) and k in nodes and not s.is_visible(k)
                and k != getattr(s, "goal", None)):
            return {"ok": False,
                    "error": "you have never heard of that. You know what you have "
                             "built and what you could begin now; use 'available'."}
        if not isinstance(k, str):
            return {"ok": False,
                    "error": 'which one? give an id, for example '
                             '{"cmd":"why","id":"units_standards"}. '
                             'Use {"cmd":"available"} to see what you could begin.'
                    if k is None else
                    "id must be a name in quotes, not %s" % type(k).__name__}
        if k not in nodes:
            # Only blame the fog when there IS any. With it off a break tester
            # mistyped an id and was told the fog was limiting the suggestions,
            # in a game they had explicitly started with the whole tree visible.
            return {"ok": False, "error": "unknown node %r. did you mean: %s"
                    % (k, ", ".join(_did_you_mean(k, nodes, s=s))
                       or ("no idea, and under fog of war I can only suggest "
                           "things you have heard of"
                           if getattr(s, "fog", False)
                           else "no idea - nothing in the tree is spelled much "
                                "like that"))}
        return dict(ok=True, **_node_explain(s, nodes, k))

    if op == "path":
        if getattr(s, "fog", False):
            # THE REASON HAS TO BE THE REAL ONE. This said "you have not
            # discovered this" for every id, including ones the player had
            # already finished and could see `done: true` on in the same
            # session. A player debugging that would go looking for a corrupt
            # save. The command is switched off wholesale under fog, which is a
            # different fact and the true one.
            return {"ok": False,
                    "error": "route planning is switched off under fog of war: "
                             "nobody can lay out a road to somewhere they have "
                             "not been, whether or not you have built this "
                             "particular thing already. Use 'available' to see "
                             "what you could begin now."}
        k = cmd.get("id")
        if k not in nodes:
            return {"ok": False, "error": "unknown node id %r" % k}
        need = closure(nodes, k)
        order = topo_order(nodes, need)
        remaining = [x for x in order if x not in s.done]
        out = {"ok": True, "id": k, "name": nodes[k]["name"], "done": k in s.done,
               "remaining_count": len(remaining), "remaining": remaining}
        # THE JOIN NOBODY HAD: "what the goal still needs" and "what I could
        # start today" were two separate reports - this one, and `available`
        # - and by midgame nearly everything on `available`'s several-hundred
        # row list is irrelevant to any one goal. A Han player wrote their own
        # regex script outside the game to intersect the two; an England
        # player asked for exactly this. Do the intersection here, once,
        # cheapest first, so it never has to be done by eye or by script
        # again.
        _startable = sorted((x for x in remaining if s.can_start(x)),
                            key=lambda x: s.project_cost(x))
        out["startable_today_count"] = len(_startable)
        out["startable_today_toward_this"] = (
            [_brief(s, nodes, x, False) for x in _startable[:30]] or "nothing yet")
        if len(_startable) > 30:
            out["and_more_startable_today"] = len(_startable) - 30
        out["still_waiting_on_something_else"] = len(remaining) - len(_startable)
        if remaining and not _startable:
            out["note"] = ("nothing on the route is startable today - see "
                           "'stuck' for what the nearest of them are waiting on")
        # A ROUTE CAN BE ENTIRELY TRUE AND ENTIRELY UNABLE TO PAY THE RENT.
        # `path` was promoted into the welcome screen's own starter verbs
        # because an earlier player called it the thing that reorganised
        # their whole run - and a second player, who saw it immediately
        # because of that promotion, reported the half that promotion
        # exposed: early in any tree the critical path is almost pure
        # knowledge, zero revenue, and this screen - now the game's own
        # first suggestion - pointed firmly at it with no word that none of
        # it earns a denarius. They found a profitable concern only by
        # guessing to sort `available` by earnings, which nothing here or in
        # the welcome text mentions. Following the game's own first piece of
        # advice should not be how a new player walks into the opening debt
        # trap this engine otherwise warns about everywhere else.
        #
        # PROMOTING THIS SCREEN MADE THE PROBLEM IT REVEALS MORE DAMAGING, NOT
        # LESS. Three more players hit this once `path` became a starter verb.
        # One read the income gap correctly and recovered by abandoning `path`
        # for `available sort earns reverse`, unprompted by anything in the
        # game. A second started four DIFFERENT path items over five years -
        # each individually affordable on the day it was started - and spent
        # the next 24 years in a debt spiral with two insolvencies and a
        # reputation crash, because each one's own affordability check has no
        # memory of the others: "nothing warns that several individually
        # affordable path items can be collectively unaffordable," in their
        # own words, and they are right - `can_start` asks "could I begin
        # this, today, on its own", which is a different and smaller question
        # than "could I finish several of these together". A third reached
        # the identical trap through `rush` instead.
        #
        # So this is not gated on already being insolvent any more - that
        # caught the damage, never the cause, and by the time recurring
        # income actually goes negative the debt is often already taken.
        # Said plainly, every time the route itself cannot pay for itself,
        # whether or not today's ledger happens to look fine yet; and said
        # with the COMBINED bill of everything listed above, not each item's
        # own affordability, which is the exact number these players were
        # never shown before committing to more than one.
        if _startable and all(nodes[x]["rev"] <= 0 for x in _startable):
            _combined = sum(s.project_cost(x) for x in _startable)
            _raise = s.spending_power("start")
            out["this_route_pays_for_nothing"] = (
                "every one of the %d things above is knowledge or "
                "infrastructure - none earns a denarius by itself. This "
                "route will not cover your costs; something off it has to. "
                "{\"cmd\":\"available\",\"sort\":\"earns\",\"reverse\":true} "
                "finds what actually pays today - building one of those "
                "alongside the route is not a detour from it, it is how you "
                "afford to keep walking it." % len(_startable))
            # THE COMBINED BILL, not each item's own affordability. Several
            # individually-affordable starts are not one affordable start;
            # `can_start` has no memory of its own earlier answers, so the
            # first time a player can see the total is here, where several
            # are listed together.
            if _combined > _raise:
                out["these_together_cost_more_than_you_can_raise"] = (
                    "starting everything listed above would cost %s in "
                    "all, against %s you could actually raise today. Each "
                    "one passed its OWN affordability check when it was "
                    "priced; that is not the same question as whether you "
                    "can afford several of them at once. Pick one, or a few, "
                    "not all of them - and see what pays before spending "
                    "the rest."
                    % ("{:,.0f}".format(_combined), "{:,.0f}".format(_raise)))
        # A ROUTE THAT DOES NOT SAY "RESTORE" IS A ROUTE YOU CANNOT FOLLOW. A
        # break tester drove a run mechanically from `path` after a sack:
        # `path` listed lead_chamber as remaining, `start` answered "you built
        # this once - restore it", and anything downstream said the same node
        # was a missing prerequisite. They sat at 106 technologies and 760,403
        # denarii from 460 AD to the horizon, because `path` never mentioned
        # the one verb that would have moved them.
        # A node you know but have SHUT does not appear above: it is done, so
        # it is not remaining, and nothing downstream is blocked by it. It is
        # still the thing a player driving from `path` most needs to see after
        # a bad century, because its plant is gone and its income with it.
        _shut = sorted(x for x in need
                       if x in getattr(s, "mothballed", set()) and x in s.done)
        if _shut:
            out["on_this_route_but_shut_down"] = _shut[:10]
            out["reopen_them_with"] = ("'restore <id>' - you still know how, so "
                                       "putting the plant back costs a fraction "
                                       "of building it. Nothing downstream is "
                                       "waiting on them; their income is")
        return out

    if op == "start":
        if ended:
            return {"ok": False, "error": "the run has ended (%s); nothing more can be started. 'state' shows where you finished and how far you got" % ended}
        k = cmd.get("id")
        if k not in nodes:
            return {"ok": False, "error": "unknown node id %r. use {\"cmd\":\"available\"} "
                                          "or {\"cmd\":\"why\",\"id\":...} to find valid ids" % k}
        # SAY UP FRONT WHEN THE SOCIETY CANNOT STAFF IT. A play tester started
        # arithmetic_positional, which wants 2,500 scribe-hours a year against
        # a national ceiling of 1,321, and watched it sit at "81% spent" from
        # 1309 to about 1440 - a hundred and thirty years. Their point is the
        # right one: the engine knows this at `start` time. It is still allowed
        # (you may teach or hire your way to the hours, and the work does
        # crawl) but it must not be a silent trap.
        # THE NUMBER PRINTED HAS TO BE THE NUMBER TESTED. The commit that added
        # commissioned hours to the test above ("Make the stated labour ceiling
        # the real one") changed the comparison to hours_you_can_call_on - which
        # is market_supply PLUS whatever you have already commissioned - and left
        # this line printing market_supply alone. A player who had commissioned
        # any of the trade saw `start` quote one ceiling and `stuck` quote a
        # higher one for the identical project a moment later, which is the exact
        # thing that commit's own message promised could not happen again.
        _impossible = []
        _impossible_trades = set()
        _n0 = nodes[k]
        _frac0 = min(1.0, 1.0 / max(1.0, _n0["yrs"]))
        for _t, _want in (_n0["lab"] or {}).items():
            _need = _want * _frac0
            if _need > 0 and s.hours_you_can_call_on(_t) < _need:
                _impossible.append("%s (wants %.0f hours a year; this society can "
                                   "field %.0f at most)"
                                   % (_t, _need, max(0.0, s.hours_you_can_call_on(_t))))
                _impossible_trades.add(_t)
        # OVERSUBSCRIBED IS NOT THE SAME AS IMPOSSIBLE. The society may be
        # able to field the trade this wants and STILL not have enough of
        # it left once your own OTHER active work is already drawing on it
        # - "the first workshop/lab sat at 60% until I stopped adding new
        # work for a year", from a player who could not see this coming
        # until it had already happened. trade_demand_vs_supply (projects.py)
        # is the CURRENT portfolio's own demand, before this project is
        # added; trade_draw_plan(k, None) is this project's own full want,
        # since it has not started and so owes the whole thing. Same two
        # calls `portfolio` makes to build the aggregate table - reused
        # here, not re-derived, so `start`'s warning and `portfolio`'s own
        # figures can never tell two different stories about the same year.
        _demand_now = s.trade_demand_vs_supply()
        _oversub = []
        for _t, _p in s.trade_draw_plan(k, None).items():
            if _t in _impossible_trades:
                continue          # already said, and said more plainly
            _supply = s.hours_you_can_call_on(_t)
            if _supply <= 0:
                continue
            _existing = _demand_now.get(_t, {}).get("demand_hours_this_year", 0.0)
            _competitors = len(_demand_now.get(_t, {}).get("projects_drawing_on_it", ()))
            _new_total = _existing + _p["desired"]
            if _new_total > _supply + 1e-6:
                _oversub.append(
                    "%s: this portfolio would want %s hours a year against "
                    "%s this society can supply (%d other active project%s "
                    "already drawing on it); this one competes for what is "
                    "left, it does not get %s to itself"
                    % (_t, "{:,.0f}".format(_new_total), "{:,.0f}".format(_supply),
                       _competitors, "" if _competitors == 1 else "s",
                       "{:,.0f}".format(_p["desired"])))
        ok, why = s.start_project(k)
        if not ok:
            return {"ok": False, "error": why}
        n = nodes[k]
        # SAY SO, FOR THE PLAYER'S OWN RECORD. start_project itself only logs
        # the RESTART case (see its own self.log.append for "begun again");
        # a fresh start was silent, so a player reading `log` back saw
        # completions and failures appear out of nowhere with no record of
        # having chosen to begin them.
        if s.active.get(k, {}).get("spent", 0.0) <= 0.5:
            s.log.append((s.year, "started: %s" % n["name"]))
        # THE PRICE YOU ACTUALLY COMMITTED TO. A normal-play tester read a cost
        # of 106,567 off `why`, started the thing forty years later, and was
        # billed 207,811 - because project_cost moves with prices, the coinage,
        # material scarcity and what you have since built, and nothing told
        # them the earlier figure was a snapshot. The bill IS fixed at the
        # moment you start; what was missing was any statement of what it was
        # fixed AT.
        bill = round(s.active.get(k, {}).get("cost_left", s.project_cost(k)), 1)
        _warn_staff = ("started, but this society cannot supply the labour it "
                       "wants and it will crawl until you can: %s"
                       % "; ".join(_impossible)) if _impossible else None
        out = {"ok": True, "started": k, "name": n["name"], "founder_hours_needed": n["ph"],
               "calendar_floor_years": n["yrs"],
               # SAID AT THE MOMENT OF COMMITMENT, not only on `why` beforehand
               # or `available` in passing - this is the screen the player is
               # actually looking at when the risk becomes theirs. See
               # expected_calendar_years (projects.py): the true expected
               # total, retries included, computed through the same retry
               # rule _complete applies on every failure, not a plain
               # geometric series on the bare risk field.
               "expected_calendar_years_with_retries": round(
                   s.expected_calendar_years(k), 2),
               "the_bill_you_have_taken_on": bill,
               "note": "This is the price as of today, and it is now fixed for "
                       "this project. Quotes move with prices, the coinage and "
                       "what a material costs to get: a figure you read years "
                       "ago is not what you will pay."}
        # SAID AT THE MOMENT OF COMMITMENT, NOT DISCOVERED 60% IN. A player
        # who had already won the game found the first workshop/lab stalled
        # at 60% "until I stopped adding new work for a year", with nothing
        # at `start` time to have told them the trade they needed was
        # already spoken for by their own other projects.
        if _oversub:
            out["this_oversubscribes_a_trade"] = (
                "started - but %s. 'portfolio' shows the full demand-vs-"
                "supply table before your next start"
                % "; ".join(_oversub))
        # TAUGHT ONCE, AT THE MOMENT IT FIRST MATTERS. A blind playthrough
        # spent its whole early game treating one long calendar-floor project
        # as "the active research" and only discovered parallel play - running
        # several things at once while a multi-year project sits in the
        # background - after an outside hint, which their own write-up calls
        # probably the difference between finishing comfortably and risking
        # the horizon. This is the central mechanic of the game and the
        # welcome text never says it. Fired once, on the first project whose
        # calendar floor is long enough that it cannot be the only thing in
        # hand for a while - not every multi-year start, which would be noise
        # by the fifth one.
        if n["yrs"] >= 2 and not getattr(s, "_said_parallelism", False):
            s._said_parallelism = True
            out["a_calendar_floor_is_not_exclusive_research_time"] = (
                "%s will take at least %d year%s, whatever else you do. That "
                "time is not spent watching it: your founder-hours and staff "
                "are free the moment this year's share of the work is paid "
                "for, and nothing stops you spending them on something else "
                "in the meantime. The strongest play is usually to keep "
                "several things running at once - start preparing the next "
                "layer now rather than waiting for this one to finish."
                % (n["name"], n["yrs"], "" if n["yrs"] == 1 else "s"))
        if _warn_staff:
            out["but"] = _warn_staff
        # BUILD STAFF AND OPERATING STAFF ARE DIFFERENT NUMBERS, and a player
        # can clear the first (checked above, and by start_project itself),
        # pay the whole bill, and only discover the second - venture_hands(),
        # what 'open' actually enforces - refuses them once the work is
        # already finished. `why` has shown this for a while (same
        # computation, see staff_to_keep_it_open there); three playtesters
        # missed it anyway in a long page and found out at 'open' instead.
        # Said here too, at the one other moment it can still change
        # anything, with today's free staff - not a promise, since attrition
        # and hiring between now and completion can move either number.
        if s.is_venture(k):
            _sup_sch, _sup_art = s.venture_hands(k)
            _free_sch, _free_art = s.venture_staff_free()
            if _sup_sch > _free_sch + 1e-9 or _sup_art > _free_art + 1e-9:
                out["today_you_could_not_open_this_when_it_is_done"] = (
                    "keeping it open will want %.2f scholars and %.2f "
                    "artisans of your own watching it; you have %.2f and "
                    "%.2f free right now, with nothing else committed. That "
                    "is a different, usually smaller number than the crew "
                    "that builds it, and it is checked only when you 'open' "
                    "it - not now. Staffing can change before this "
                    "finishes, for better or worse; if it has not by then, "
                    "hire, teach, or close something first."
                    % (_sup_sch, _sup_art, _free_sch, _free_art))
        # AND SAY WHEN THIS WOULD BORROW TO FINISH. `start` financed the gap
        # between what a project costs and what the household has, silently,
        # at up to twelve per cent - three players in a row were carried into
        # debt they had not decided to take on. One went 750 denarii short of
        # affordable on turn one and spent the next twenty-five years digging
        # out while the project sat stalled and the interest compounded.
        #
        # Not a refusal. Borrowing to build is a real and often correct move,
        # and the game already lets you. It is the not-being-told that was
        # wrong, so this names the gap, the rate, and how much room is left
        # before the creditors stop being patient - and what they do then,
        # because both players who found that out found it out by losing a
        # school and a collegium they had built years earlier.
        #
        # A FORECAST, NOT A RECEIPT - the keys have to say so. `start` itself
        # borrows nothing: credit only actually draws down at step resolution,
        # if and when cash genuinely goes negative paying this year's share.
        # The first version of this block said "borrowed_now", in the past
        # tense, on the very command that had not borrowed a denarius yet - a
        # Norse player read "borrowed now: 123.8" here and "(none used)" on
        # `money` in the next breath and rightly called it a ledger
        # contradiction. Same numbers, same warning; they describe what WILL
        # happen if the project runs to completion on today's cash, not what
        # has.
        _gap = bill - max(0.0, s.capital)
        if _gap > 0:
            _lim = s.credit_limit()
            _after = -(min(0.0, s.capital) - _gap)
            out["on_credit"] = {
                "nothing_is_borrowed_yet": (
                    "this is a forecast, not a receipt: credit only actually "
                    "draws down at step resolution, if cash runs short paying "
                    "this year's share. These figures are what happens if it "
                    "does, on today's numbers."),
                "you_would_borrow": round(_gap, 1),
                "interest_per_year_on_it": round(s.debt_interest_rate() * 100, 1),
                "you_would_then_owe": round(_after, 1),
                "no_one_advances_past": round(_lim, 1),
                "what_happens_there":
                    "past that limit every project in hand halts unfinished, "
                    "nobody funds new work for some years, and your creditors "
                    "take and sell what you are running - including things you "
                    "built long ago and had no debt against.",
            }
        # WARN, DO NOT SILENTLY ACCEPT. start_reason() already refuses a trade
        # that does not exist AT ALL (see "THE TRADE HAS TO EXIST" there), but
        # trade_available() goes true the moment you call `train`, two years
        # before anyone graduates - market_supply() is the stricter, honest
        # figure step() actually checks. A tester's `start` came back ok:true
        # for a project needing an engineer while nobody could yet DO engineer
        # work, and years later it was HALTED with everything spent on it
        # lost, with no warning at the point they could still have done
        # something about it. Name it here instead.
        short = sorted(t for t in n["lab"] if s.market_supply(t) <= 0.0)
        if short:
            out["warning"] = (
                "no one can do this work YET: %s. The trade exists here or is "
                "being taught, but nobody is trained and ready, and this "
                "project cannot progress at all until someone is. If that is "
                "still true after four years with no progress, it is halted "
                "and everything spent on it is lost. Check {\"cmd\":\"labour\"}, "
                "and see {\"cmd\":\"train\"} if nobody is being taught yet."
                % ", ".join(short))
        return out

    if op == "stop":
        k = cmd.get("id")
        ok, why = s.stop_project(k)
        if not ok:
            return {"ok": False, "error": why}
        # stop_project ITSELF never touches self.log - see its own docstring,
        # which is entirely about what the hours and money do, not about
        # recording the decision. A deliberate abandonment is exactly the
        # kind of thing a player asked `log` to be able to find again.
        s.log.append((s.year, "stopped: %s (%s)" % (nodes[k]["name"], why)))
        return {"ok": True, "stopped": k, "what_happened": why}

    if op == "rush":
        # BULK START, FOG-SAFE. A break tester in the late game had thirty
        # or forty things startable at once and nothing to do but type
        # `start <id>` thirty or forty times - "the late game is pure
        # typing" - and every one of those ids was already something
        # `can_start` had already cleared, the same check `available` uses
        # to decide what to list at all, so acting on all of them at once
        # hands back nothing a player could not already see for themselves.
        if ended:
            return {"ok": False,
                    "error": "the run has ended (%s); nothing more can be "
                             "started. 'state' shows where you finished and "
                             "how far you got" % ended}
        try:
            limit = (int(cmd.get("limit")) if cmd.get("limit") is not None
                     else None)
        except (TypeError, ValueError):
            return {"ok": False, "error": "limit must be a whole number"}
        if limit is not None and limit < 1:
            return {"ok": False, "error": "limit must be at least 1"}
        _memo = {}
        _ok = [k for k in s.order if s.can_start(k, _memo=_memo)]
        # THE SAME EXCLUSION `available` USES: a node with no cost, no hours
        # and nothing else standing in its way is not a decision, it is
        # about to be handed to you for free whatever you type.
        _ok = [k for k in _ok
               if not (nodes[k]["tier"] == 0 and nodes[k]["ph"] == 0
                       and nodes[k]["_total_cost"] <= 1
                       and not s._is_foreign_institution(k))]
        # HIGHEST-LEVERAGE FIRST, INTERNALLY ONLY. This never shows a player
        # a downstream_count - that is a fog spoiler, see _node_explain's own
        # comment on it - it only uses the number to decide which of several
        # things your money cannot all cover gets it first, the same number
        # `available`'s own "most_rests_on_these" digest already uses to
        # decide what to show you. Ranking by it here leaks nothing, because
        # the ranking itself is never printed, only which ids got started.
        _ok.sort(key=lambda k: (-downstream_count(nodes, k), s.project_cost(k)))
        # AND STOP WHEN THE YEAR IS FULL. `rush limit:1000` on turn one started
        # 209 things at once - a plantation, a whaling industry, a theatre, a
        # gambling house, nitre beds and lens grinding, all in the same year -
        # owing 90,944 founder-hours against a lifetime the game itself puts at
        # about 72,000. The next step gave hours to exactly ONE of them and the
        # other 208 sat inert for ever, so "RUNNING (209)" was a fiction about
        # 208 of them. A weird-play tester called it out as the worst thing they
        # found, and they were right: the command was doing what it was asked
        # and what it was asked was incoherent.
        #
        # Committing a couple of years of everyone's attention is a decision a
        # player might reasonably make. Committing four centuries of it is not.
        _hours_room = max(0.0, s.director_pool() - s.director_hours_committed())
        _HORIZON_YEARS = 2.0
        _budget = s.director_pool() * _HORIZON_YEARS
        started, not_started = [], []
        _owed = 0.0
        for k in _ok:
            if limit is not None and len(started) >= limit:
                break
            if started and _owed + nodes[k]["ph"] > _budget:
                not_started.append({
                    "id": k, "name": nodes[k]["name"],
                    "why": "not begun: the %d things already started this turn "
                           "owe %s of your hours, and you have about %s a year. "
                           "Beginning more would not make them go faster, only "
                           "leave them all standing still"
                           % (len(started), "{:,.0f}".format(_owed),
                              "{:,.0f}".format(s.director_pool()))})
                continue
            ok2, why = s.start_project(k)
            if ok2:
                _owed += nodes[k]["ph"]
                n = nodes[k]
                # SAY SO, for the same reason the single-id `start` does: a
                # player reading `log` back should see every begun-work as a
                # choice they made, not a completion that appeared unasked.
                if s.active.get(k, {}).get("spent", 0.0) <= 0.5:
                    s.log.append((s.year, "started: %s" % n["name"]))
                started.append({"id": k, "name": n["name"],
                                "cost": round(s.active.get(k, {}).get(
                                    "cost_left", s.project_cost(k)), 1)})
            else:
                not_started.append({"id": k, "why": why})
        return {"ok": True, "started": started, "count_started": len(started),
                "not_started": not_started,
                "count_not_started": len(not_started),
                # THE SAME WARNING `policy` CARRIES, for the same reason. This
                # is an automatic behaviour and it reads as the game offering to
                # play your turn well for you. It is not: it begins things in
                # order of how much rests on them, which is a rule of thumb and
                # not a plan. A round-12 tester used it on turn one and watched
                # scandal jump to within a year of the line that ends the run,
                # with the treasury in debt.
                "this_is_an_approximation_not_optimal_play": (
                    "`rush` is a rough rule of thumb, not a plan: it begins "
                    "things in order of how much rests on them, with no idea "
                    "what you are building toward. Beginning a great deal at "
                    "once also makes you conspicuous and spends your credit, so "
                    "on an early turn it can do real damage. A careful player "
                    "beats it; it exists to save typing in a late game where "
                    "you would have begun all of these anyway."),
                "note": "tried everything you could begin today, "
                        "highest-leverage first, until your credit ran out "
                        "or the list did. 'why <id>' on anything in "
                        "not_started says exactly why it stopped there."}

    if op == "bounty":
        if ended:
            return {"ok": False, "error": "the run has ended (%s); nothing more can be bought. 'state' shows where you finished and how far you got" % ended}
        k = cmd.get("id")
        if k not in nodes:
            return {"ok": False, "error": "unknown node id %r" % k}
        if k in s.done:
            return {"ok": False, "error": "%s is already done" % k}
        # ELIGIBILITY FIRST, ALWAYS - a tester was told to stop an active
        # mat_platinum_bulk in order to switch it to a bounty, did so, and
        # then had `bounty mat_platinum_bulk` refused as not bounty-eligible:
        # advice the game itself could have checked before giving. Since an
        # active project's prerequisites are already satisfied (that is what
        # let it start), eligibility here depends only on tier/category, so
        # checking it before the "already active" branch costs nothing and
        # never sends a player to stop something that could not become a
        # bounty anyway.
        if not s.bounty_eligible(k):
            n = nodes[k]
            missing = [p for p in n["pre"] if p not in s.done]
            if missing:
                # SAME FOG FILTER `why` USES, not a second one. This used to
                # print every missing prerequisite by raw id regardless of
                # whether the player had ever heard of it - industrial zinc
                # leaked power_grid this way, the getter leaked its induction-
                # heating coupling, and the vacuum tube leaked its hidden
                # cathode prerequisite.
                return {"ok": False, "error": s.missing_prereq_message(missing)}
            return {"ok": False,
                    "error": "not bounty-eligible (tier %d, category %s): a craftsman "
                             "in %s could not recognise success at this without "
                             "understanding the theory, so there is nothing to "
                             "award the prize for. A bounty works where the craft "
                             "already exists here and success is visible."
                             % (n["tier"], n["cat"],
                                s.civ.get("name", "this society"))}
        if k in s.active:
            return {"ok": False, "error": "%s is already active; stop it first if you want "
                                          "to switch to a bounty instead" % k}
        price = (nodes[k]["_total_cost"] * 2.5 * s.civ_cost_factor(k)
                 * s.material_cost_factor(k) * s.cost_money_factor())
        if not s.post_bounty(k):
            return {"ok": False, "error": "cannot afford the bounty: needs about %.0f denarii, "
                                          "you have %.0f. Earn or wait, then try again" % (price, s.capital)}
        return {"ok": True, "posted": k, "price": round(price, 1), "capital": round(s.capital, 1)}

    if op == "buy":
        if ended:
            return {"ok": False, "error": "the run has ended (%s); nothing more can be bought. 'state' shows where you finished and how far you got" % ended}
        what = cmd.get("what")
        # THE SAME READER AS EVERY OTHER QUANTITY. This had its own float()
        # and so missed the guards _qty carries: a break tester bought
        # 1e30 hectares of coppice and read the refusal in binary rounding
        # error.
        n, _err_n = _qty(cmd, "n", 0)
        if _err_n:
            return {"ok": False, "error": _err_n + ". Nothing was changed."}
        # A playtester passed n:-5 and got money from nothing. buy_forest(-5)
        # computed a NEGATIVE cost, passed the affordability test because
        # -1250 > 400 is false, then credited the capital and set forest_ha to
        # -5, while the reply said ok:false. The refusal was reported AFTER the
        # mutation had already happened. Validate before touching anything.
        if not (n > 0):
            return {"ok": False,
                    "error": "n must be greater than zero, got %g. Nothing was changed." % n}
        if what == "forest":
            got = s.buy_forest(n)
            if got <= 0:
                return {"ok": False, "error": "cannot afford %.0f ha of coppice woodland "
                                              "(you have %.0f denarii)" % (n, s.capital)}
            return {"ok": True, "bought_ha": got, "forest_ha": round(s.forest_ha, 1),
                    "capital": round(s.capital, 1)}
        if what in ("nitre", "nitre_bed", "saltpetre", "nitre beds"):
            got = s.build_nitre(n)
            if got <= 0:
                return {"ok": False,
                        "error": "cannot afford %.0f square metres of nitre bed "
                                 "(that is %s denarii and you have %s). Nothing "
                                 "was changed."
                                 % (n, "{:,.0f}".format(n * s.NITRE_COST_PER_M2
                                                        * s.price_index),
                                    "{:,.0f}".format(s.capital))}
            return {"ok": True, "laid_m2": got,
                    "nitre_bed_m2": round(s.nitre_bed_m2, 1),
                    "saltpetre_it_yields_per_year_tonnes":
                        round(s.nitre_bed_m2 * s.NITRE_YIELD_T_PER_M2, 3),
                    "capital": round(s.capital, 1)}
        if what == "mine":
            mat = cmd.get("material")
            # GENERALISED beyond the seven hand-named metals (see
            # economy.py's mineable()/mine_catalog_hint(), and
            # COMMODITY_DYNAMISM.md for why the closed list was the actual
            # bug: "no mine, no supply lever" for anything else the tree
            # ever asks a node to buy). This is the one gate that used to
            # make that literally true at the command surface, even though
            # the seven-name dict membership check lived here, not in
            # economy.py, which is why the fix has to touch this file.
            if not s.mineable(mat):
                return {"ok": False, "error": "material must be one of: "
                                              + s.mine_catalog_hint()}
            # partial=False: a mine you asked for by name is bought in full or
            # not at all. It used to spend every denarius you had and hand back
            # a fraction, without asking.
            price = s.mine_quote(mat, n).get("to_sink_it") if hasattr(s, "mine_quote") else None
            got = s.open_mine(mat, n, partial=False)
            if got <= 0:
                if price is not None and price > s.capital:
                    return {"ok": False,
                            "error": "%.0f tonnes a year of %s costs %s denarii to "
                                     "sink and you have %s. Nothing was changed - ask "
                                     "for what you can pay for, or check the price "
                                     'first with {"cmd":"quote","what":"mine",'
                                     '"material":"%s","n":%g}.'
                                     % (float(n), mat, "{:,.0f}".format(price),
                                        "{:,.0f}".format(s.capital), mat, float(n))}
                return {"ok": False, "error": "could not commission any %s capacity right now "
                                              "(ceiling reached, or standing too low for a "
                                              "concession that size)" % mat}
            # Say what was actually commissioned and WHEN it arrives. A tester
            # asked for 999,999,999 tonnes a year, silently got 59, and found
            # ready_year was always null so there was no way to know whether the
            # workings would appear in four years or ninety-five. Both of those
            # are the model being coy about its own arithmetic.
            tranche = [t for t in getattr(s, "mine_tranches", []) if t[0] == mat]
            ready = min((t[2] for t in tranche), default=None)
            asked = float(n)
            reply = {"ok": True, "material": mat,
                     "you_asked_for_t_per_yr": asked,
                     "commissioned_t_per_yr": round(got, 2),
                     "ready_year": ready,
                     "years_until_producing": (None if ready is None
                                               else round(ready - s.year, 1)),
                     "already_producing_t_per_yr": round(s.mine_capacity.get(mat, 0.0), 2),
                     "capital": round(s.capital, 1)}
            if got < asked * 0.999:
                reply["note"] = ("less than you asked for: limited by capital, by the "
                                 "ceiling your standing supports, or both. Nothing was "
                                 "wasted, you paid only for what was sunk.")
            return reply
        if what == "slaves":
            s._last_buy_refusal = None
            got = s.buy_slaves(int(n))
            if got <= 0 and getattr(s, "_last_buy_refusal", None):
                return {"ok": False, "error": s._last_buy_refusal}
            if got <= 0:
                # Quote the price actually asked. It is no longer 300 flat: a
                # large purchase bids the local market up, and saying "300 each"
                # while charging far more is the model lying to the player.
                q = s.slave_quote(int(n))
                return {"ok": False,
                        "error": "cannot afford %d slaves: %.0f denarii "
                                 "(%.0f each after the market moves against a purchase "
                                 "this size) and you have %.0f"
                                 % (int(n), q, q / max(1, int(n)), s.capital)}
            return {"ok": True, "bought": got, "slaves": s.slaves, "capital": round(s.capital, 1)}
        if what == "manumit":
            got = s.manumit(int(n))
            if got <= 0:
                return {"ok": False, "error": "you have no slaves to free"}
            return {"ok": True, "manumitted": got, "freedmen": s.freedmen, "slaves": s.slaves}
        return {"ok": False, "error": "what must be one of: forest, mine, slaves, manumit"}

    if op == "work":
        if ended:
            return {"ok": False, "error": "the run has ended (%s). 'state' shows where you finished and how far you got" % ended}
        # WHAT THE PRACTICE WAS EARNING BEFORE YOU TOOK THE JOB. Selling your
        # hours takes them out of your own surgery, which is where most of your
        # income comes from at the start - so a play tester earned 80.1 for 500
        # hours as a scribe and lost 58.3 of practice income the same instant,
        # netting 22 for a quarter of their year. Nothing anywhere said founder
        # hours drove revenue, and they only found it by diffing the ledger.
        _rev_before = s.revenue()
        pay, err = s.work_for_wages(cmd.get("trade"), cmd.get("hours", 0))
        # A message WITH pay is a warning about a bad trade, not a refusal:
        # the work happened and the player should be told what it cost them.
        if err and pay <= 0:
            return {"ok": False, "error": err}
        _rev_after = s.revenue()
        _cost = _rev_before - _rev_after
        out = {"ok": True, "trade": cmd.get("trade"), "hours": cmd.get("hours"),
               "earned": round(pay, 1), "capital": round(s.capital, 1),
               "your_hours_left_this_year": round(
                   max(0.0, s.director_pool() - s.wage_hours_this_year), 1)}
        if _cost > 0.5:
            # Same rule: round the parts, then take the difference from the
            # rounded parts, so the three figures on the screen subtract.
            out["earned"] = round(pay, 1)
            out["it_cost_your_own_practice"] = round(_cost, 1)
            out["so_you_are_up"] = round(round(pay, 1) - round(_cost, 1), 1)
            out["why"] = ("You cannot be in two places. Hours sold for wages "
                          "come out of the practice, so what you really made "
                          "this year is the wage less what the surgery did not "
                          "take. Hours you put into your OWN projects do not "
                          "cost you this.")
        if err:
            out["but"] = err
        return out

    if op in ("risk", "hazards"):
        kr = s.knowledge_risk()
        return {"ok": True, "knowledge_risk": kr, "year": s.year,
                "note": "What history is about to do to you, and what you have "
                        "built that blunts it. Every hazard here is fightable."}

    if op == "values":
        return _agent_values(s)

    if op in ("money", "ledger", "accounts"):
        # LESS THE YEAR YOU HAVE ALREADY PAID FOR. `hire` takes a finder's fee
        # and the first year's wages up front, and step() nets that advance off
        # the living cost it charges - so counting the whole payroll here bills
        # the same year twice. A break tester hired four artisans, read
        # "Net/yr after it: -1,097" on this very screen, stepped once and lost
        # 61. From the second year on the figure was right, which is what made
        # it so hard to see.
        _prepaid = min(s.living_cost(), getattr(s, "wages_prepaid", 0.0))
        fixed = (s.upkeep() + s.living_cost() - _prepaid
                 + s.mine_operating_cost())
        _ramp, _prac = s.still_ramping(), s.practice_note()
        _mkt = s.goods_market_summary()
        # A PLAYER MUST SEE IT (rome/data/review/COMMODITY_DYNAMISM.md):
        # material_price_factor() now responds for every material a node
        # buys, not just the 9 originally tracked commodities, so what it
        # is doing to costs needs a line here too, not only inside one
        # project's own `why`. See economy.py's material_market_summary().
        _mat_mkt = s.material_market_summary()
        return {"ok": True,
                "capital": round(s.capital, 1),
                "revenue": round(s.revenue(), 1),
                "where_the_money_comes_from": s.revenue_sources(),
                **({"still_building_up_custom": _ramp} if _ramp else {}),
                **({"about_your_own_practice": _prac} if _prac else {}),
                **({"materials_costing_you_a_premium": _mat_mkt} if _mat_mkt else {}),
                **({"the_market_you_sell_into": _mkt} if _mkt else {}),
                "what_it_costs_you": {
                    "upkeep_of_what_you_built": round(s.upkeep(), 1),
                    "living_and_appearances": round(s.living_cost() - s.wage_bill(), 1),
                    # NAME THE PART THAT IS THERE BECAUSE YOU ARE RICH. A break
                    # tester started with a million, built nothing, hired
                    # nobody, and read "living and appearances ~14,990, Net/yr
                    # -14,990" with no explanation anywhere of why an idle
                    # fortune bleeds. It is not a fee: it is that a man visibly
                    # richer than he lives is suspected in a patronage society.
                    "_of_which_because_you_are_rich":
                        round(max(0.0, s.capital) * 0.015, 1) or None,
                    "wages": round(s.wage_bill(), 1),
                    "of_which_already_paid_as_hiring_advances":
                        round(_prepaid, 1) or None,
                    "mines_standing": round(s.mine_operating_cost(), 1),
                    # A COST LIKE ANY OTHER. It was printed two lines below the
                    # net that ignored it, so a tester in a debt spiral read
                    # "+9.5 a year" while capital fell 105 and then 117.
                    "interest_on_arrears": round(
                        max(0.0, -s.capital) * s.debt_interest_rate(), 1)},
                # revenue_capacity(), not revenue() - this is the STANDING
                # figure (see the comment two lines below, and state's own
                # net_per_year, protocol.py: same fix, same reason). A
                # player who sold founder-hours with `work` watched this
                # swing to -193/yr for exactly one year and back, which is
                # not what "recurring" means.
                "net_per_year": round(
                    s.revenue_capacity() - fixed
                    - max(0.0, -s.capital) * s.debt_interest_rate(), 1),
                "spent_on_projects_last_year": round(getattr(s, "spend_last_year", 0.0), 1),
                # THE SAME FIGURE `state` PRINTS. A break tester read `state`
                # "net -70.8 den/yr (after 75.5 den into projects)" against
                # `money` "Net/yr: 4.6" and called it a contradiction. Both were
                # right and only one was labelled: net_per_year is the standing
                # flows, before anything goes into the work in hand.
                "net_after_project_spend": round(
                    s.revenue() - fixed
                    - max(0.0, -s.capital) * s.debt_interest_rate()
                    - getattr(s, "spend_last_year", 0.0), 1),
                "credit_limit": round(s.credit_limit(), 1),
                "interest_rate_on_arrears": round(s.debt_interest_rate(), 4),
                "interest_paid_in_total": round(getattr(s, "interest_paid", 0.0), 1),
                # HOW CLOSE, not just how far it goes. See warn_near_the_limit.
                "of_that_limit_you_have_used": (
                    "%d%%" % (100.0 * -s.capital / max(1e-9, s.credit_limit()))
                    if s.capital < 0 and s.credit_limit() > 0 else "none"),
                "still_owed_on_work_in_hand": round(
                    sum(st.get("cost_left") or 0.0 for st in s.active.values()), 1)}

    if op in ("stuck", "why_stuck", "blocked"):
        # THE QUESTION EVERY TESTER ASKED, in different words. "There's no 'why
        # am I stuck?' view - three separate 90-250-year stalls, each caused by
        # one node blocked on one thing, each found by typing `why` at a
        # guess." The pieces were all here; nothing put them in one place, and
        # stall_diagnosis only spoke after eight years of insolvency.
        _fog = getattr(s, "fog", False)
        reasons = []
        _startable = [k for k in nodes
                      if k not in s.done and k not in s.active
                      and (not _fog or s.is_visible(k))
                      and s.start_reason(k)[0]]
        _afford = [k for k in _startable
                   if s.project_cost(k) <= s.spending_power("start")]
        if s.active:
            _waits = {}
            for k, st in sorted(s.active.items()):
                bill = st.get("cost_left")
                if bill is None:
                    bill = max(0.0, s.project_cost(k) - st["spent"])
                _waits[k] = _waiting_on(s, nodes, k, st, bill)
            reasons.append({"what": "work in hand",
                            "how_many": len(s.active),
                            "each_waiting_on": _waits})
        # THE ROAD TO THE GOAL, not the tree at large. A play tester with fifty
        # nodes left and nothing startable was told "you have work in hand,
        # money to pay for it and people to do it", because two hundred
        # unrelated things elsewhere in the tree were startable. Nobody is
        # stuck for want of a bottling shed.
        _goal = getattr(s, "goal", None)
        _goal_routing_off_under_fog = False
        if _goal in nodes and not _fog:
            _road = closure(nodes, _goal) - s.done
            _road_open = [k for k in _road if s.start_reason(k)[0]]
            if _road and not _road_open:
                _near = sorted(_road, key=lambda k: len(closure(nodes, k) - s.done))
                reasons.append({
                    "what": "the road to the goal",
                    "why": "%d of its nodes are still to build and NONE of them "
                           "is startable today. The nearest is %s: %s"
                           % (len(_road), _near[0],
                              s.start_reason(_near[0])[1]),
                    "the_nearest_few": _near[:5]})
        elif _goal in nodes and _fog:
            # SAY SO, THE WAY `rush` DOES. A blind Han run with the goal set
            # to the junction transistor hit hundreds of affordable things
            # late in the game and was told to open a profitable concern
            # instead of being pointed at the one real blocker - not because
            # this command was broken, but because the road-to-the-goal
            # branch above is switched off under fog of war for exactly the
            # reason 'path' gives for doing the same: naming what is left on
            # a route to something not fully discovered would hand over the
            # hidden tree. The silence read as "everything below is the real
            # answer" when it was really "the one analysis that could answer
            # this did not run". A player should be told that, not left to
            # infer it from an unhelpful reply.
            _goal_routing_off_under_fog = True
        # STARTING NOTHING IS THE COMMONEST WAY TO GET NOWHERE, and this
        # command - whose whole job is "why you are not getting on" - said
        # "nothing: you have work in hand, money to pay for it and people to do
        # it" to a play tester on turn one, with no project running at all. It
        # was the first thing they typed and it was false.
        if not s.active:
            _cheap = (min(_afford or _startable, key=lambda k: s.project_cost(k))
                      if (_afford or _startable) else None)
            reasons.append({"what": "you have started nothing",
                            "why": ("no project is in hand, so no year of yours "
                                    "is being spent on one. %s"
                                    % ("'start %s' would begin the cheapest "
                                       "thing you can pay for today." % _cheap
                                       if _cheap else
                                       "and nothing in front of you can be "
                                       "begun, which the rows below explain."))})
        # AND WHAT YOU HAVE BUILT AND NEVER SWITCHED ON. A break tester read
        # "NOTHING YOU COULD BEGIN" while two concerns sat finished and closed
        # that between them raised their revenue by 71%.
        _shut = sorted(k for k in s.done
                       if s.is_venture(k) and k not in s.operating
                       and nodes[k]["rev"] > nodes[k]["up"])
        if _shut:
            # DO NOT RECOMMEND A COMMAND THAT WILL FAIL. This used to pick
            # the best-margin shut concern by revenue minus upkeep alone and
            # tell the player to 'open' it, without ever checking whether
            # open_venture would actually let them. A household deep in the
            # credit-exhaustion/named-trade trap (see PATH_SEARCH.md) sits
            # with free_art at 0.00-0.03 for centuries: this command was
            # measured telling such a household "open lens_grinding", which
            # needs 2.13 craftsmen to supervise and fails outright - advice
            # that spends a turn on a refusal and reads as the game having
            # lied about what it just told you to do.
            _sch_free, _art_free = s.venture_staff_free()
            _shut_for_staff = getattr(s, "shut_for_staff", {})
            def _capex_now(_k):
                _fee = s.venture_capex(_k)
                if (_k in _shut_for_staff
                        and s.year - _shut_for_staff[_k] <= s.STAFF_CLOSURE_GRACE):
                    _fee *= 0.1
                return _fee
            def _openable(_k):
                _need_sch, _need_art = s.venture_hands(_k)
                return (_need_sch <= _sch_free + 0.01
                        and _need_art <= _art_free + 0.01
                        and _capex_now(_k) <= s.spending_power("buy"))
            _really_openable = [k for k in _shut if _openable(k)]
            if _really_openable:
                _best = max(_really_openable,
                           key=lambda k: nodes[k]["rev"] - nodes[k]["up"])
                reasons.append({"what": "things you built and never opened",
                                "why": "%d finished concern(s) are shut and "
                                       "earning nothing. The best you could "
                                       "actually open right now is %s, which "
                                       "would earn %s a year against %s of "
                                       "upkeep: 'open %s'"
                                       % (len(_shut), _best,
                                          "{:,.0f}".format(nodes[_best]["rev"]),
                                          "{:,.0f}".format(nodes[_best]["up"]),
                                          _best)})
            else:
                _best = max(_shut, key=lambda k: nodes[k]["rev"] - nodes[k]["up"])
                _need_sch, _need_art = s.venture_hands(_best)
                if _need_sch > _sch_free + 0.01 or _need_art > _art_free + 0.01:
                    _why = ("it needs %.2f scholars and %.2f craftsmen to "
                            "supervise it, and you have %.2f and %.2f not "
                            "already watching something else"
                            % (_need_sch, _need_art, _sch_free, _art_free))
                else:
                    _why = ("opening it costs %s denarii, and between cash "
                            "and what anyone will advance you can raise %s"
                            % ("{:,.0f}".format(_capex_now(_best)),
                               "{:,.0f}".format(s.spending_power("buy"))))
                reasons.append({"what": "things you built and cannot open yet",
                                "why": "%d finished concern(s) are shut and "
                                       "earning nothing, and none of them can "
                                       "be opened right now. The best is %s, "
                                       "which would earn %s a year against "
                                       "%s of upkeep, but %s. Hire, teach, or "
                                       "close something to free the hands, "
                                       "or raise the money, and try again"
                                       % (len(_shut), _best,
                                          "{:,.0f}".format(nodes[_best]["rev"]),
                                          "{:,.0f}".format(nodes[_best]["up"]),
                                          _why)})
        if not _startable:
            reasons.append({"what": "nothing you could begin",
                            "why": "everything in front of you is either built, "
                                   "already running, or waiting on something. "
                                   "'available' says which."})
        elif not _afford:
            reasons.append({"what": "money",
                            "why": "%d things are startable and the cheapest of "
                                   "them costs %s, against the %s you could "
                                   "raise"
                                   % (len(_startable),
                                      "{:,.0f}".format(min(s.project_cost(k)
                                                           for k in _startable)),
                                      "{:,.0f}".format(s.spending_power("start")))})
        if s.binding and s.resource_throttle() < 0.95:
            reasons.append({"what": "a raw material",
                            "why": "%s: work is running at %d%% of plan. %s"
                                   % (s.binding, s.resource_throttle() * 100,
                                      s.shortage_remedy(s.binding))})
        _room = s.household_room()
        if _room < 1.0:
            reasons.append({"what": "room for people",
                            "why": "you can take %.2f more people. %s"
                                   % (max(0.0, _room), s._room_advice())})
        if s.capital < 0:
            reasons.append({"what": "arrears",
                            "why": "you owe %s of the %s anyone will advance "
                                   "you, and the interest is %s a year"
                                   % ("{:,.0f}".format(-s.capital),
                                      "{:,.0f}".format(s.credit_limit()),
                                      "{:,.0f}".format(-s.capital
                                                       * s.debt_interest_rate()))})
        if s.year < getattr(s, "credit_frozen_until", 0):
            reasons.append({"what": "a credit freeze",
                            "why": "nobody will fund new work until %d"
                                   % int(s.credit_frozen_until)})
        _stall = s.stall_diagnosis()
        out = {"ok": True,
               "you_could_begin": len(_startable),
               "and_could_pay_for": len(_afford),
               "what_is_holding_you_up": reasons or (
                   "nothing: %d project(s) in hand, money to pay for them and "
                   "people to do them" % len(s.active)),
               "and_the_cheapest_thing_you_could_start_now": (
                   min(_startable, key=lambda k: s.project_cost(k))
                   if _startable else None)}
        if _stall:
            out["and_you_are_in_a_hole"] = _stall
        if _goal_routing_off_under_fog:
            out["this_does_not_know_your_goal"] = (
                "fog of war is on, so this cannot check whether anything "
                "below is actually on the route to your goal, or name the "
                "one thing blocking it - that would leak the hidden tree, "
                "the same reason 'path' refuses outright under fog. "
                "Everything above is general advice, not goal-directed; "
                "'why <id>' on anything you have heard of is still the way "
                "to reason toward the goal by hand.")
        return out

    if op in ("mines", "workings"):
        # See _agent_mines above: the one place this arithmetic is written,
        # shared with `capacity`, so the two screens cannot drift apart.
        return _agent_mines(s)

    if op in ("capacity", "industry", "dashboard"):
        return _agent_capacity(s, nodes, cmd)

    if op == "portfolio":
        return _agent_portfolio(s, nodes, cmd)

    if op == "economy":
        return _agent_economy(s, cmd)

    if op == "changes":
        return _agent_changes(s, nodes, cmd)

    if op == "labour":
        one = (cmd.get("trade") or "").strip().lower()
        if one and one not in WAGES:
            return {"ok": False, "error": "no such trade: %s. They are: %s"
                    % (one, ", ".join(sorted(WAGES)))}
        def row(t, long=False):
            # THE PRICE YOU ACTUALLY PAY, not the table price. A play tester
            # watched engineers go from 781 a year to 1,094 and budgeted wrong
            # for decades: leaning on a trade's local supply bids it up, and
            # the premium appeared in the bill and nowhere else.
            _lpf = s.labour_price_factor(t)
            r = {"trade": t,
                 "a_year_of_one": round(ANNUAL_WAGE.get(t, 375.0) * s.wage_index
                                        * s.price_index * _lpf, 0),
                 "you_employ": round(s.employees.get(t, 0.0), 2)}
            # THE CEILING, ON THE SCREEN. "This society's literacy will not
            # supply more than 6.4 scholars in total, ever" gates the goal
            # itself - which wants twenty-five - and appeared in no screen at
            # all: a play tester found it in a refusal message in year 463 of a
            # 500-year game. A wall you can only discover by walking into it is
            # not a wall, it is a trap.
            if t in s.LITERATE_TRADES:
                r["most_this_society_can_ever_supply"] = round(
                    s.literate_capacity(t), 1)
                r["you_have_or_are_teaching"] = round(
                    s._trade_headcount_pending(t), 2)
                r["what_widens_it"] = ("printing, paper, schools and academies - "
                                       "they raise how many people here can "
                                       "read, and this ceiling rises with it")
            if _lpf > 1.005:
                r["dearer_than_usual_by"] = "%d%%" % ((_lpf - 1.0) * 100)
                r["because"] = ("you have taken on a large share of the %ss "
                                "here lately. Teaching more of the trade, or "
                                "anything that widens the supply, brings it "
                                "back down" % t)
            if long:
                r.update({"kind": trade_family(t),
                          "wage_per_hour": round(WAGES[t] * s.wage_index
                                                 * s.price_index, 3),
                          # SPLIT, because the total includes your own people
                          # and calling all of it "the market" made hiring look
                          # like it created smiths out of nothing.
                          "hours_the_market_can_supply": round(s.market_supply_split(t)[0], 0),
                          "hours_your_own_people_add": round(s.market_supply_split(t)[1], 0),
                          # AND THE SECOND CHANNEL. A break tester read one
                          # ceiling in three places and then commissioned past
                          # it. There are two: who you can HIRE here, and what
                          # an outside shop will take on, at a premium.
                          "hours_you_have_commissioned": round(s.hours_reserved(t), 0),
                          "hours_you_could_still_commission": round(
                              max(0.0, s.market_supply(t) - s.hours_reserved(t)), 0),
                          "hours_available_to_you_in_all": round(
                              s.hours_you_can_call_on(t), 0),
                          # THE NOTE IS STATIC AND THE WORLD IS NOT. A break
                          # tester read "exists here: True" and "does not exist
                          # yet; you must create this trade" three lines apart,
                          # because the note is a fixed string about the
                          # society as it started and they had since taught the
                          # trade into existence. Teaching one is the whole
                          # point of `train`; the reply has to notice it
                          # happened.
                          "note": (("you taught this trade into existence here; "
                                    "the only %ss in this society are yours and "
                                    "the ones they have taught since" % t)
                                   if t in s.trades_created
                                   else TRADE_NOTES.get(t, ""))})
            return r
        if one:
            r = row(one, long=True)
            r["exists_here"] = s.trade_available(one)
            return {"ok": True, "trade": r}
        have = sorted(t for t in WAGES if s.employees.get(t, 0.0) > 0.005)
        # NOT "TRADES YOU DO NOT YET EMPLOY", and not "trades that exist"
        # either. Excluding the ones you have reads as "no more smiths
        # available" the moment you hire your first smith, which `hire smith 1`
        # then contradicts; including every available trade put machinist on
        # the list while `labour machinist` said "the town can supply: 0
        # hours", which a play tester read side by side. It is every trade
        # there is actually somebody here to hire.
        hirable = sorted(t for t in WAGES
                         if s.trade_available(t) and s.market_supply_split(t)[0] > 0)
        taught_only = sorted(t for t in WAGES
                             if s.trade_available(t) and t not in hirable)
        absent = sorted(t for t in WAGES if not s.trade_available(t))
        return {"ok": True,
                "on_your_staff": [row(t) for t in have] or "nobody",
                "you_could_hire_here": hirable,
                "only_the_ones_you_taught": taught_only,
                "do_not_exist_here": absent,
                "you_employ_in_total": round(sum(s.employees.values()), 2),
                # THE CAP, WHERE A PLAYER CAN SEE IT. This number decided a
                # play tester's entire mid-game and appeared NOWHERE: not in
                # state, not in state full, not here. The only way to learn it
                # was to try to hire and be refused, and the only way to learn
                # what RAISED it was to read the refusal, which changed as the
                # tree opened. They sat on 285,000 denarii unable to take on a
                # sixth person and had no idea why.
                "household_places_used": round(s.headcount(), 2),
                "household_places_in_all":
                    round(s.headcount() + max(0.0, s.household_room()), 2),
                "room_for_more_people": round(max(0.0, s.household_room()), 2),
                # _room_advice, NOT _staff_advice. This is `labour`, and
                # `state` sends a player here with the words "'labour' says
                # what raises it" - meaning the CEILING on people. It answered
                # with _staff_advice, which names hiring, commissioning and
                # buying, every one of which needs the room you have not got.
                # Two play testers followed it in a circle; one found the real
                # answer only by guessing the word "workshop" in a search.
                # _room_advice exists for exactly this and was written after
                # the same complaint about the hire refusal.
                "what_raises_that_room": s._room_advice(),
                # NOT "NEVER", AND NOT "HOWEVER RICH". This sentence is mine
                # and it went stale the same day I wrote it. It said the
                # ceiling could never move, which was true of the old model and
                # is now false: the ceiling grows with the institutions that
                # train scholars and carry their keep. The user caught it by
                # reading the sentence literally, which is the right way to
                # read a sentence, and noticing it implies no research you do
                # can ever help. The `hire` refusal had already been corrected
                # and this screen had not, so the game was saying both things.
                "and_how_many_of_the_lettered_trades_this_society_supplies": (
                    "%s: right now your household can hold at most %.1f of them "
                    "in total, hired and taught together. That is your reach "
                    "into the labour market, not a fact about how many people "
                    "here can read. It RISES: a school, an academy and an "
                    "imperial patron train and pay scholars on their own "
                    "budget and lift this ceiling with them, which is the large "
                    "effect; printing, paper and libraries widen literacy "
                    "itself, which is the smaller one."
                    % (", ".join(sorted(s.LITERATE_TRADES)),
                       s.literate_capacity("scholar"))),
                "slaves": s.slaves, "freedmen": s.freedmen,
                "annual_wage_bill": round(s.wage_bill(), 1),
                "craftsmen_on_your_staff": round(s.artisans, 2),
                "scholars_including_you": round(s.effective_scholars(), 2),
                # A ROW WITH NO TRADE IS PEOPLE YOU BOUGHT, and printing that
                # as the literal string "None" - "None x3.3", "None x0.55" -
                # is how two separate testers concluded the game had lost track
                # of their household. It knows exactly what they are.
                "in_training": [
                    {"trade": (r_[2] if len(r_) > 2
                               else "people you bought, learning the work"),
                     "people": (r_[3] if len(r_) > 3
                                else round(r_[0] / 0.55, 2)),
                     "ready_year": r_[1]}
                    for r_ in getattr(s, "training", [])],
                "one_trade_in_full": '{"cmd":"labour","trade":"smith"}',
                "how_to_grow_staff": {"scholars": s._staff_advice("scholars"),
                                      "artisans": s._staff_advice("artisans")},
                "note": "A trade that does not exist here cannot be hired at any "
                        "price; teach one with train. Trades are not "
                        "interchangeable. Buying a job instead of a person is "
                        "commission."}

    if op == "hire":
        if ended:
            return {"ok": False, "error": "the run has ended (%s). 'state' shows where you finished and how far you got" % ended}
        if not s.founder_alive and s.directors_extra < 0.5:
            return {"ok": False,
                    "error": "there is nobody left to take anyone on: the "
                             "founder is dead and no deputy remains to direct "
                             "the work"}
        n, err = _qty(cmd, "n", 1)
        if err:
            return {"ok": False, "error": err + ". Nothing was changed."}
        ok, err = s.hire(cmd.get("trade"), n)
        if not ok:
            return {"ok": False, "error": err}
        # HIRING AND LETTING GO ARE DECISIONS, not standing facts the way
        # payroll is - neither labour.py nor core.py logs either one, so a
        # player reading `log` back saw the wage bill change with nothing
        # saying they were the one who changed it. `hire` already composed a
        # precise sentence for this ("2 smiths taken on for 750 denarii...");
        # using it here rather than rebuilding one from cmd["n"] keeps the log
        # honest about what actually happened, not just what was asked for.
        s.log.append((s.year, err or ("hired %s %s" % (cmd.get("n"), cmd.get("trade")))))
        return {"ok": True, "hired": cmd.get("trade"), "n": cmd.get("n"),
                "you_now_employ": round(s.employees.get(str(cmd.get("trade")).lower(), 0.0), 2),
                "annual_wage_bill": round(s.wage_bill(), 1),
                "capital": round(s.capital, 1)}

    if op in ("fire", "dismiss"):
        n, err = _qty(cmd, "n", 1)
        if err:
            return {"ok": False, "error": err + ". Nothing was changed."}
        ok, err = s.fire(cmd.get("trade"), n)
        if not ok:
            return {"ok": False, "error": err}
        # Same reasoning as `hire` above: `err` here is fire()'s own success
        # message, which says exactly what happened - staff let go, an
        # apprenticeship cancelled, or both - and cmd["n"] alone would not.
        s.log.append((s.year, err or ("let go %s %s" % (cmd.get("n"), cmd.get("trade")))))
        out = {"ok": True, "let_go": cmd.get("trade"),
               "annual_wage_bill": round(s.wage_bill(), 1)}
        if err:
            out["what_happened"] = err
        return out

    if op == "train":
        if ended:
            return {"ok": False, "error": "the run has ended (%s). 'state' shows where you finished and how far you got" % ended}
        n, err = _qty(cmd, "n", 1)
        if err:
            return {"ok": False, "error": err + ". Nothing was changed."}
        ok, msg = s.train(cmd.get("trade"), n, cmd.get("from"))
        if not ok:
            return {"ok": False, "error": msg}
        out = {"ok": True, "training": msg, "capital": round(s.capital, 1),
               "your_hours_left_this_year": round(
                   max(0.0, s.director_pool() - s.director_hours_committed()), 1)}
        # TRAIN AND HIRE ARE TWO SEPARATE STEPS, and this message was the only
        # one a player saw at the moment they took the first of them. This
        # trade did not exist here before, and a project's hired_labour for it
        # draws only on people you have trained or hired INTO it - there is no
        # open market to fall back on the way there is for a smith or a
        # scribe. Nobody can do that work until the people above finish
        # learning, and 'hire' is how you add more without that wait, now that
        # the trade exists to hire into at all. A Rome player found this out
        # only when `start` refused a project outright, having read nothing on
        # this screen or on `why` that named the gap in advance.
        _trade = str(cmd.get("trade") or "").strip().lower()
        if _trade in TRADES_ABSENT:
            out["means"] = (
                "%s now exists here, but nobody can do that work yet: a "
                "project needing it draws only on people trained or hired "
                "into this exact trade, never a general market. "
                "'hire %s <n>' adds more right away, without waiting; "
                "otherwise the people above are it until they finish."
                % (_trade, _trade))
        return out

    if op in ("commission", "job"):
        if ended:
            return {"ok": False, "error": "the run has ended (%s). 'state' shows where you finished and how far you got" % ended}
        hours, err = _qty(cmd, "hours")
        if err:
            return {"ok": False, "error": err + ". Nothing was changed."}
        ok, msg = s.commission(cmd.get("trade"), hours)
        if not ok:
            return {"ok": False, "error": msg}
        return {"ok": True, "commissioned": msg, "capital": round(s.capital, 1),
                "note": "These hours are available to your projects this year only."}

    if op == "mothball":
        _mb_id = cmd.get("id")
        ok, msg = s.mothball_work(_mb_id)
        if not ok:
            return {"ok": False, "error": msg}
        # mothball_work does not log either - a deliberate shutdown reads no
        # differently from one the creditors forced on you (see economy.py's
        # own, separate log lines for THAT case) unless the player's own
        # choice gets a line of its own too.
        s.log.append((s.year, "mothballed: %s (%s)"
                     % (nodes[_mb_id]["name"] if _mb_id in nodes else _mb_id, msg)))
        out = {"ok": True, "mothballed": msg, "upkeep": round(s.upkeep(), 1)}
        # SAY WHAT ELSE CLOSES WITH IT. A Mexica player shut capability
        # institutions for the capital back and lost two multi-year
        # stretches to it silently - the upkeep saving was the only thing
        # this reply ever mentioned. `mothball` takes effect before this
        # runs, so `s.CAPABILITY_INSTITUTIONS` already tells the truth about
        # what just stopped.
        if _mb_id in s.CAPABILITY_INSTITUTIONS:
            out["but"] = (
                "this was a capability, not only an expense: scholars it "
                "supported, household places it added, credit or standing "
                "it lent you, or a future start it cleared have ALL stopped "
                "too, the same as its upkeep. 'restore %s' brings it back "
                "for a fraction of the original cost." % _mb_id)
        return out

    if op == "restore":
        _rs_id = cmd.get("id")
        ok, msg = s.restore_work(_rs_id)
        if not ok:
            return {"ok": False, "error": msg}
        s.log.append((s.year, "restored: %s (%s)"
                     % (nodes[_rs_id]["name"] if _rs_id in nodes else _rs_id, msg)))
        return {"ok": True, "restored": msg, "capital": round(s.capital, 1)}

    if op in ("quote", "price"):
        what = (cmd.get("what") or "mine").strip().lower()
        # EVERYTHING YOU CAN BUY, NOT JUST MINES. `quote` exists because a
        # tester went from 38,151 denarii to zero on one unpriced mine command.
        # A break tester then spent 27,500 - 68% of their capital - on `buy
        # forest 100`, with no price shown anywhere, no way to ask for one, and
        # no market to sell it back into. Same lesson, same command, different
        # counter.
        if what in ("forest", "coppice", "woodland"):
            n_f, err_f = _qty(cmd, "n", 100)
            if err_f:
                return {"ok": False, "error": err_f}
            per = s.FOREST_COST_PER_HA * s.price_index
            return {"ok": True, "what": "forest", "hectares": n_f,
                    "to_buy_it": round(per * n_f, 1),
                    "per_hectare": round(per, 2),
                    "you_have": round(s.capital, 1),
                    "you_could_raise": round(s.spending_power("buy"), 1),
                    "you_can_afford_about": round(s.spending_power("buy") / max(per, 1e-9), 1),
                    "afford_means": "cash plus half the credit line",
                    "it_yields_per_hectare_per_year":
                        "%.2f tonnes of charcoal, sustainably" % s.CHARCOAL_PER_HA,
                    "note": "Coppice is bought once and yields every year after. "
                            "There is no market to sell it back into."}
        if what in ("nitre", "nitre_bed", "saltpetre"):
            n_n, err_n = _qty(cmd, "n", 10000)
            if err_n:
                return {"ok": False, "error": err_n}
            per_n = s.NITRE_COST_PER_M2 * s.price_index
            return {"ok": True, "what": "nitre bed", "square_metres": n_n,
                    "to_lay_it": round(per_n * n_n, 1),
                    "per_square_metre": round(per_n, 2),
                    "you_have": round(s.capital, 1),
                    "you_could_raise": round(s.spending_power("buy"), 1),
                    "you_can_afford_about": round(s.spending_power("buy") / max(per_n, 1e-9), 0),
                    "afford_means": "cash plus half the credit line",
                    "it_yields_per_square_metre_per_year":
                        "%.4f tonnes of saltpetre" % s.NITRE_YIELD_T_PER_M2,
                    "note": "Saltpetre is made, not mined: dung, straw and ash "
                            "turned for a couple of years. Cheap by the metre "
                            "and thin by the metre, so beds are laid in "
                            "thousands of square metres, not hundreds."}
        if what in ("slaves", "people"):
            n_s, err_s = _qty(cmd, "n", 1)
            if err_s:
                return {"ok": False, "error": err_s}
            return {"ok": True, "what": "slaves", "people": n_s,
                    "to_buy_them": round(s.slave_quote(n_s), 1),
                    "you_have": round(s.capital, 1),
                    "note": "The price rises with how many you take at once, and "
                            "they are worth nothing to you for the first few "
                            "years while they learn the work. Freeing them "
                            "afterwards makes them worth more, not less."}
        if what != "mine":
            return {"ok": False,
                    "error": "you can quote a mine, a forest or people: "
                             "quote mine coal 500, quote forest 100, quote slaves 5"}
        n, err = _qty(cmd, "n", 1)
        if err:
            return {"ok": False, "error": err}
        q = s.mine_quote(cmd.get("material"), n)
        if q is None:
            return {"ok": False, "error": "no such material: %r. %s"
                    % (cmd.get("material"), s.mine_catalog_hint())}
        return dict(ok=True, **q)

    if op in ("close", "close_mine"):
        if ended:
            return {"ok": False, "error": "the run has ended (%s). 'state' shows where you finished and how far you got" % ended}
        ok, msg = s.close_mine(cmd.get("material") or cmd.get("what"))
        if not ok:
            return {"ok": False, "error": msg}
        return {"ok": True, "closed": msg,
                "mine_operating_cost": round(s.mine_operating_cost(), 1)}

    if op == "withdraw":
        if ended:
            return {"ok": False, "error": "the run has ended (%s). 'state' shows where you finished and how far you got" % ended}
        ok, msg = s.withdraw_from_public_life()
        if not ok:
            return {"ok": False, "error": msg}
        return {"ok": True, "withdrew": msg,
                "eminence": round(s.eminence, 2),
                "reputation": round(s.reputation, 1),
                "protection": round(s.protection, 3)}

    if op == "bribe":
        if ended:
            return {"ok": False, "error": "the run has ended (%s). 'state' shows where you finished and how far you got" % ended}
        amount, err = _qty(cmd, "amount")
        if err:
            return {"ok": False, "error": err + ". Nothing was changed."}
        ok, msg = s.bribe(amount)
        if not ok:
            return {"ok": False, "error": msg}
        return {"ok": True, "bribed": msg, "capital": round(s.capital, 1)}

    if op == "open":
        if ended:
            return {"ok": False, "error": "the run has ended (%s). 'state' shows where you finished and how far you got" % ended}
        k = cmd.get("id")
        if not isinstance(k, str):
            return {"ok": False, "error": 'give an id, e.g. {"cmd":"open","id":"fin_pawnshop"}'}
        if k not in nodes:
            # `why` on a mistyped id suggests; `open` answered "no such node"
            # and stopped. Same typo, same player, two different games.
            near = _did_you_mean(k, nodes, s=s)
            return {"ok": False,
                    "error": "no such thing as %r%s"
                             % (k, (". did you mean: " + ", ".join(near))
                                if near else "")}
        # UNITS: HOW A PLAYER FOUNDS A SECOND SCHOOL. See
        # ProjectsMixin.open_venture / _expand_institution (projects.py). A
        # call with no "units" field behaves exactly as it always has.
        _units = cmd.get("units")
        if _units is not None and not isinstance(_units, (int, float)):
            return {"ok": False, "error": "units must be a number"}
        ok, msg = s.open_venture(k, units=_units)
        if not ok:
            return {"ok": False, "error": msg}
        # The single rule `help` calls out as the one that catches everybody -
        # finishing something earns nothing until you open it - deserves a
        # line in the player's own history, not just in the reply to this one
        # command. open_venture itself stays silent; see its docstring.
        s.log.append((s.year, "opened: %s (%s)" % (nodes[k]["name"], msg)))
        return {"ok": True, "opened": msg, "capital": round(s.capital, 1),
                "revenue": round(s.revenue(), 1), "upkeep": round(s.upkeep(), 1)}

    if op == "ventures":
        sch_free, art_free = s.venture_staff_free()
        running = sorted(s.operating)
        idle = sorted(k for k in s.done
                      if s.is_venture(k) and k not in s.operating)

        def _vrow(k):
            n = nodes[k]
            # AT THE FIGURE THE LEDGER USES. This printed the tree's raw
            # revenue, and the ledger applies the economy, the output factor,
            # this society's prices and the ramp - so a break tester measured
            # `ventures` understating every concern by a uniform 2.234x against
            # `money` (11,000 against 24,571). And NEEDS printed the BUILD crew
            # while the engine charges supervision, which is a quarter of it
            # and never the number the refusal quotes.
            _scale = (s.economy ** 0.75) * s.output_factor * s.price_index
            _sup_s, _sup_a = s.venture_hands(k)
            # AT THE SAME MARKET PRICE `money` credits, for a goods-producing
            # concern: goods_market_factor() is 1.0 for anything not in
            # GOODS_CATEGORIES and for anything not yet open, so this changes
            # nothing for every other row. See that method's own comment.
            _mkt = s.goods_market_factor(k) if k in s.operating else 1.0
            row = {"id": k, "name": n["name"],
                    "earns_a_year": round(n["rev"] * _scale
                                          * (s.venture_ramp(k) if k in s.operating
                                             else 1.0) * _mkt, 1),
                    "costs_a_year": round(n["up"] * s.price_index, 1),
                    "needs": {"scholars": round(_sup_s, 2),
                              "craftsmen": round(_sup_a, 2)}}
            _note = s.goods_market_note(k)
            if _note:
                row["market"] = _note
            # A CAPABILITY, NOT ONLY A BUSINESS. Every other row here is a
            # straightforward earn-vs-cost decision; these are not, because
            # closing one loses scholars it supports, household places it
            # adds, credit or standing it lends, or a future start it clears
            # - none of which show up in earns/costs at all. A Rome player
            # could not tell `identity_cover` and `workshop_first` (real
            # capabilities) apart from an ordinary shuttered business by
            # looking at this exact table; a Mexica player closed some of
            # these for the capital back and lost the capability along with
            # it, twice, having no way to see the difference here either.
            if k in s.CAPABILITY_INSTITUTIONS:
                row["capability"] = ("yes - more than income; see 'why %s'" % k)
            return row

        # CAPABILITY INSTITUTIONS GET THEIR OWN LIST. Sorting them into the
        # ordinary earn/cost table invited exactly the misreading above; a
        # separate heading says outright that these are not evaluated the
        # same way.
        _idle_ordinary = [k for k in idle if k not in s.CAPABILITY_INSTITUTIONS]
        _idle_capability = [k for k in idle if k in s.CAPABILITY_INSTITUTIONS]
        out = {"ok": True,
               "running": [_vrow(k) for k in running] or "nothing",
               "you_know_how_but_have_not_opened":
                   [dict(_vrow(k), to_open_it=round(s.venture_capex(k), 1))
                    for k in _idle_ordinary[:20]] or "nothing",
               "capabilities_you_know_how_to_run_but_have_not_opened":
                   [dict(_vrow(k), to_open_it=round(s.venture_capex(k), 1))
                    for k in _idle_capability] or "nothing",
               "people_free_to_run_something_new": {
                   "scholars": round(sch_free, 2), "craftsmen": round(art_free, 2)},
               # YOU ARE IN THAT COUNT. `ventures` said "1 scholars, 1
               # craftsmen" on the same screen as `labour`'s "ON YOUR STAFF:
               # nobody" and `why`'s "(you have 1, 0)" - three screens, three
               # different counts, and a break tester listed all three side by
               # side. One person can keep an eye on one small shop, which is
               # how every one of these fortunes started; it just has to say
               # that the person is you.
               "one_of_each_of_those_is_you": bool(s.founder_alive),
               # WHERE THE REST OF THEM ARE. See venture_staff_who_is_watching_what.
               "and_these_concerns_are_holding_the_rest":
                   s.venture_staff_who_is_watching_what()[:12] or "none",
               "held_in_all": {
                   "scholars": round(s.venture_staff_used()[0], 2),
                   "craftsmen": round(s.venture_staff_used()[1], 2)},
               "you_have_in_all": {
                   "scholars": round(s.effective_scholars(), 2),
                   "craftsmen": round(s.artisans
                                      + (s.FOUNDER_IS_WORTH if s.founder_alive
                                         else 0.0), 2)},
               # SCHOLARS AND CRAFTSMEN ARE NOT INTERCHANGEABLE, and nothing
               # said so. A play tester spent thirty years poor because
               # auto_train had bought them engineers - who count as scholars
               # and cannot keep an eye on a workshop - and the turn they
               # swapped three engineers for three artisans their net went from
               # -155 a year to +4,164. `labour <trade>` shows the wage and not
               # which of the two columns the trade lands in.
               "these_are_not_interchangeable": (
                   "Most concerns want CRAFTSMEN to keep an eye on them. "
                   "Engineers, chemists and machinists are scholars here, and "
                   "a scholar cannot watch a workshop. 'labour <trade>' says "
                   "which of the two a trade is."),
               "note": "Knowing how to do a thing and running it are different. "
                       "Of the things in the TREE, only what you are RUNNING "
                       "earns anything or costs anything. 'open <id>' starts "
                       "one, 'mothball <id>' stops it, and you keep the "
                       "knowledge either way. The capability list below is "
                       "not judged on money the way the ordinary one is - see "
                       "each one's own 'why' before deciding whether to open "
                       "or close it."}
        # THE PRACTICE IS NOT A VENTURE, AND IT IS WHERE YOUR MONEY COMES FROM.
        # A break tester read "RUNNING: nothing" and "only what you are RUNNING
        # earns anything" on the same screen as a ledger paying 233.5 a year
        # from two named nodes, and filed it as the two screens flatly
        # contradicting each other. They do not, but nothing said which side
        # the practice falls on.
        _prac_note = s.practice_note()
        if _prac_note:
            out["your_practice_is_not_a_venture"] = (
                "%s You did not open it and you cannot close it; it is not "
                "listed here, and it is most of your income until you build "
                "something. See 'money'." % _prac_note)
        if len(_idle_ordinary) > 20:
            out["and_more_you_could_open"] = len(_idle_ordinary) - 20
        return out

    if op == "policy":
        want = cmd.get("set")
        changed = {}
        if want is not None:
            if not isinstance(want, dict):
                return {"ok": False,
                        "error": 'set must be an object, e.g. '
                                 '{"cmd":"policy","set":{"auto_hire":true}}'}
            for key, val in want.items():
                if key not in s.policy:
                    return {"ok": False, "error": "no such policy: %s. They are: %s"
                            % (key, ", ".join(sorted(s.policy)))}
                s.policy[key] = _flag(val)
                changed[key] = s.policy[key]
        # WHICH OF THESE CAN ACTUALLY ACT TODAY. A play tester spent about eight
        # years and 5,952 denarii working out that negative capital silently
        # disables both hiring and opening: the switches read ON, the engine
        # did nothing, and the only clue was one refusal string. A switch that
        # says ON while nothing happens is worse than one that says OFF.
        _stopped = {}
        if s.capital <= 0:
            if s.policy.get("auto_hire"):
                _stopped["auto_hire"] = ("nothing to hire with: hiring is paid "
                                         "in advance and you are in arrears")
            if s.policy.get("auto_open"):
                _stopped["auto_open"] = ("nothing to open with: opening a "
                                         "concern costs stock and premises")
        if s.year < getattr(s, "credit_frozen_until", 0):
            _stopped["credit"] = ("nobody will fund new work until %d"
                                  % int(s.credit_frozen_until))
        _pol = {"ok": True, "policy": dict(s.policy), "changed": changed,
                # WHAT THESE ARE FOR, BEFORE WHAT EACH ONE DOES. Play testers
                # keep switching them on in the belief that the engine knows
                # the best line and is offering to walk it for them, and then
                # reporting the result as a bug: "policy auto_hire true
                # destroyed my run in eight years", "auto_train quietly
                # bankrupted me", "policy auto_hire on quietly destroyed my
                # economy". They are none of them wrong about what happened.
                # They are wrong about what these are, and nothing on this
                # screen has ever told them.
                #
                # These are a rough hand on the tiller so a player who does not
                # want to manage a payroll every turn does not have to. They
                # follow simple rules on the information of a single year. They
                # do not look ahead, they do not know your plan, and they will
                # sometimes take a line you would not have taken. That is the
                # deal, and it is worth taking for the tedium it saves; it is
                # not an optimizer and playing by hand will beat it.
                "these_are_approximations_not_optimal_play": (
                    "Each of these is a rough rule of thumb applied once a "
                    "year on that year's figures. None of them looks ahead, "
                    "knows what you are building towards, or is trying to win. "
                    "They exist to save you typing, and a careful player beats "
                    "them. Turn one on when the tedium is worse than the "
                    "mistakes; turn it off the moment it does something you "
                    "would not have done. If one of them ever ruins you rather "
                    "than merely costing you a little, that is a defect worth "
                    "reporting, not the intended cost of convenience."),
                "what_each_does": {
                    # SAY WHAT MIX. "Grow the staff" was the whole
                    # description, and a play tester turned it on and watched
                    # scholars take all 22 of their household places while
                    # artisans fell to 0.03 - which shut 22 concerns, because
                    # artisans are what supervise them, and took their net from
                    # +8,010 a year to -3,027. The mix is now defended in
                    # code; a player deciding whether to switch this on should
                    # be able to read what it will do before it does it.
                    "auto_hire": "grow the staff toward what you can house and "
                                 "pay. Mostly craftsmen, because craftsmen are "
                                 "what keep concerns open; some scholars; and "
                                 "it replaces any trade you taught as its "
                                 "people die off. It spends only a share of "
                                 "your surplus, so with no surplus it hires "
                                 "nobody",
                    "auto_buy_people": "buy slaves when the workshop is short-handed",
                    "auto_manumit": "free people you hold, over time",
                    "auto_train": "teach trades this society does not have when a "
                                  "project needs them",
                    "auto_mine": "sink a mine when a mineral is holding work up",
                    "auto_forest": "buy coppice when charcoal is holding work up",
                    "auto_mothball": "stop working mines you cannot pay for",
                    # THE ONE SWITCH WITH NO DESCRIPTION AT ALL, on a screen
                    # whose entire purpose is saying what each of these does.
                    "auto_commission": "buy a job from an outside shop when a "
                                       "few pairs of hands are the only thing "
                                       "between you and something you need. "
                                       "Cheaper than employing somebody you "
                                       "will not need next year, and it leaves "
                                       "no standing obligation either way",
                    "auto_bribe": "pay your way out of a scandal before it kills you",
                    "auto_shed": "let go of WORKS that cost more than they return "
                                 "(this is about buildings and practices, not people)",
                    # SAY WHAT IT WILL NOT DO - AND SAY THE EXCEPTION, which
                    # this did not, so two players on different civilisations
                    # each watched it open a loss-making concern, checked the
                    # help, and reported the automation as broken. It is not:
                    # auto_open_ventures deliberately opens a capability
                    # institution at a loss, because a school takes 2,500 a
                    # year and hands back 800 and is where twelve of your
                    # scholars come from, and the margin test would otherwise
                    # shut it for ever. An ordinary shop that earns less than
                    # it costs is still left shut, which is the case the
                    # original sentence was written for - a play tester whose
                    # nitre beds and glassware stayed closed. Both halves are
                    # true and only one of them was written down.
                    "auto_open": "open concerns that plainly pay for themselves, "
                                 "and the institutions that train and house "
                                 "people even when those run at a loss - a "
                                 "school costs more than it takes and is where "
                                 "your scholars come from. An ordinary shop that "
                                 "earns less than it costs is left shut however "
                                 "much you need it; open those yourself with "
                                 "'open <id>'",
                },
                "note": "Anything switched off here you can still do by hand: hire, "
                        "train, buy, commission, mothball, restore, bribe.",
                # A break tester read the note above as covering everything the
                # game ever does without being asked, switched auto_shed off,
                # and lost their whole staff anyway. The note was too broad and
                # they were entitled to read it that way. A policy is something
                # the game DECIDES for you; a consequence is the world answering
                # a decision you already made, and no switch turns those off.
                "not_policies": "Some things are consequences, not automation, "
                                "and there is no switch for them: people you "
                                "cannot pay leave, mines you cannot pay for stop "
                                "being worked once your credit is gone, and "
                                "creditors take what they are owed. Those follow "
                                "from having no money, not from a setting."}
        if _stopped:
            _pol["switched_on_but_cannot_act_right_now"] = _stopped
        return _pol

    if op in ("save", "load"):
        path = cmd.get("file") or cmd.get("path")
        if not isinstance(path, str) or not path:
            return {"ok": False, "error": 'give a filename, e.g. {"cmd":"save","file":"mygame.json"}'}
        # A SAVE FILE IS A SAVE FILE, not a way to write anywhere on the disk.
        # A tester confirmed this would write into /etc/, and that a relative
        # path scattered files through the repository root. The game is played
        # by pointing agents and scripts at it; "name a path and I will write
        # there" is not a thing it should offer.
        bad = _unsafe_path(path)
        if bad:
            return {"ok": False, "error": bad}
        try:
            if op == "save":
                save_state(s, path)
                return {"ok": True, "saved": path, "year": s.year}
            load_state(s, path)
            return {"ok": True, "loaded": path, "year": s.year}
        except Exception as e:
            return {"ok": False, "error": "could not %s %r: %s" % (op, path, e)}

    if op == "step":
        # It used to advance the clock silently after the run was over, which
        # looks identical to a working game that has simply stopped progressing.
        if ended:
            return {"ok": False, "error": "the run has ended (%s); time cannot advance. "
                                          "Use {\"cmd\":\"state\"} to see the final position."
                                          % ended}
        raw_years = cmd.get("years", 1)
        # `True` is an int in Python and stepped one year silently. A player who
        # sends true meant something, and it was not that.
        if isinstance(raw_years, bool):
            return {"ok": False, "error": "years must be a number, not true or false"}
        try:
            years = int(raw_years)
        except (TypeError, ValueError):
            return {"ok": False, "error": "years must be an integer"}
        # 0.999 was rejected and 1.99 was silently floored to one year, which is
        # the worst pair of answers to give: the boundary is invisible and the
        # accepted side quietly does something other than what was asked. A
        # calendar advances in years; say so, rather than rounding on the
        # player's behalf and calling it "accepted".
        if float(raw_years) != years:
            return {"ok": False,
                    "error": "years must be a whole number of years; %r is not. "
                             "Nothing was changed." % raw_years}
        if years < 1:
            return {"ok": False, "error": "years must be >= 1"}
        # A tester sent 100000 and the run silently ended. Nothing is gained by
        # accepting a number larger than the game can contain, and a typo that
        # ends your run without saying so is the worst kind of accepted input.
        left = max(0, s.end_year - s.year)
        if years > left:
            return {"ok": False,
                    "error": "there are only %d years left before the horizon at "
                             "%d. Ask for %d or fewer, or fewer still if you want "
                             "to see what happens on the way."
                             % (left, s.end_year, left)}
        # WARN BEFORE, NOT AFTER, A MULTI-YEAR STEP WASTES HOURS. "Founder-
        # hours do not bank. A player can have long calendar-floor projects
        # running, use `step 5`, and unintentionally throw away thousands of
        # usable founder-hours if they did not fill the portfolio first" -
        # from a player who had already won the game. Checked against THIS
        # year only, before any of the requested years run: free_hours_
        # going_unused is the exact same test `state` already uses (every
        # active project already calendar-locked, or nothing active at all,
        # with a real pool still free) - read here, not recomputed, so this
        # warning and that field can never disagree about what "idle" means.
        # Non-blocking: it says so and proceeds, it does not refuse the step.
        multi_year_hours_warning = None
        if years > 1:
            _pre_state = _agent_state(s, nodes)
            _idle_note = _pre_state.get("free_hours_going_unused")
            if _idle_note:
                # A STARTABLE PROJECT HAS TO EXIST, or the warning would be
                # telling a player to do something they cannot do. Early
                # exit on the first hit - see `stuck`'s own _startable for
                # the same full-tree scan, accepted there for the same
                # reason: nothing cheaper tells you whether ANYTHING at all
                # is startable right now.
                _could_start = next(
                    (x for x in nodes if x not in s.done and x not in s.active
                     and s.can_start(x)), None)
                if _could_start:
                    # DOES IT ACTUALLY BANK? Checked against step()'s own
                    # code, not assumed: core.py's step() computes `pool`
                    # fresh every year from director_pool() minus this
                    # year's commitments, and whatever of it 5b's wage-work
                    # branch does not spend either is simply never written
                    # anywhere - no field on `self` carries a "leftover
                    # hours" balance into the next call. It does not partly
                    # bank; it does not bank at all.
                    multi_year_hours_warning = (
                        "before stepping %d years: %s founder-hours this "
                        "year are already going to waste, and '%s' is one "
                        "thing you could start today that would use some of "
                        "them. Founder-hours do not bank at all: step() "
                        "draws a fresh pool every year, and what goes "
                        "unused this year is simply gone, never carried "
                        "into the next one - so 'step %d' spends this "
                        "year's slack exactly as idle as it is right now, "
                        "%d more times over, unless you start something "
                        "first. Proceeding anyway."
                        % (years, "{:,.0f}".format(
                               _pre_state.get("founder_hours_available") or 0.0),
                           nodes[_could_start]["name"], years, years))
        # LOST, not only completed. A normal-play tester lost fourteen finished
        # works inside a single `step 12` - among them corpus_written and
        # school_founded, which they called the pivot of the entire game - and
        # wrote that "completions get EVENT lines; losses get nothing". The
        # engine does log the shedding, but nothing in the reply put a name
        # against what left, while every arrival got one. A game whose only
        # score is what you have built has to report subtraction at least as
        # loudly as addition.
        # STOP WHEN SOMETHING IT WARNED ABOUT ACTUALLY HAPPENS, rather than
        # running the rest of the years you asked for on top of it. A break
        # tester watched a `step 12` carry "CLOSE TO THE LIMIT ... while it is
        # still your choice" (see economy.warn_near_the_limit) straight
        # through to CREDIT EXHAUSTED, and then spend the REMAINING years of
        # the same call compounding arrears with nobody able to react - the
        # choice the warning promised was still theirs had already gone by
        # before the reply came back. A request for N years is not a promise
        # to hide what happens in year 1 until year N has also gone by. So
        # this breaks the loop, not only the request, the moment it fires.
        # A normal-play tester in mortal mode hit the equivalent fault for
        # the founder's own death: it landed inside a `step 60` and the call
        # ran eleven more years past it - far enough to also trip the
        # no-successor catastrophe - before the player got a turn to react.
        # MATCHED CASE-INSENSITIVELY BELOW, because this is prose and prose
        # gets rewritten: the death line was recapitalised to say what the
        # death MEANS and silently stopped matching here, which cost the step
        # its stop and the reply its death field.
        # CLOSE TO THE LIMIT BELONGS HERE TOO, and did not: the comment above
        # describes exactly this warning being cut short so the choice it
        # offers is still real, but the tuple itself never named it, so a
        # batched step ran straight past "stop a project... while it is
        # still your choice" and only broke four years later on the fatal
        # CREDIT EXHAUSTED that warning exists to prevent. The one event that
        # still leaves you options is the one this most needed to interrupt
        # for; the fatal one needs it least, since there is nothing left to
        # choose by the time it fires.
        _STEP_STOP_MARKERS = ("CREDIT EXHAUSTED", "FOUNDER DIES",
                              "CLOSE TO THE LIMIT")
        completed, lost, events = [], [], []
        founder_died_this_step = None
        stopped_early = None
        end_year = s.end_year
        ran = 0
        for _ in range(years):
            if s.dead_reason or s.year >= end_year:
                break
            before_done, before_log = set(s.done), len(s.log)
            # FOR `changes`: what a bare node-or-concern-set diff cannot tell
            # you on its own - WHEN it changed. revealed/operating only ever
            # grow or lose members silently; snapshotting the sets either
            # side of this one year's step() is the one place that year's
            # own diff can still be taken, cheaply, before it is gone.
            before_revealed = set(getattr(s, "revealed", set()))
            before_operating = set(s.operating)
            s.step()
            ran += 1
            hist = getattr(s, "_dashboard_history", None)
            if hist is None:
                hist = s._dashboard_history = []
            _snap = _dashboard_snapshot(s)
            _snap["revealed_added"] = sorted(
                set(getattr(s, "revealed", set())) - before_revealed)
            _snap["concerns_opened"] = sorted(s.operating - before_operating)
            _snap["concerns_closed"] = sorted(before_operating - s.operating)
            _snap["completed"] = sorted(s.done - before_done)
            hist.append(_snap)
            # sorted(), because this is a set difference and a set of strings
            # iterates in an order that depends on PYTHONHASHSEED. Two runs of
            # the same game with the same seed reported the same completions in
            # different orders, which is a small thing that makes the protocol's
            # own output impossible to diff. Caught by fingerprinting the
            # engine before and after being split into modules: every number
            # matched and this list did not.
            for k in sorted(s.done - before_done):
                # YOURS OR THE SOCIETY'S. Anything in `granted` is this
                # civilisation's own work, credited free; printing it in the
                # same "COMPLETED" line as a project the player paid for and
                # waited three years on had a tester reading their first turn
                # as two finished buildings they had never started.
                completed.append({"id": k, "name": nodes[k]["name"],
                                  "year": s.done_year.get(k),
                                  "granted": k in s.granted})
            for k in sorted(before_done - s.done):
                lost.append({"id": k, "name": nodes[k]["name"], "year": s.year,
                             "can_be_restored": k in getattr(s, "mothballed", set())})
            _this_year = s.log[before_log:]
            for y, m in _this_year:
                events.append({"year": y, "message": m})
                if "founder dies" in m.lower():
                    _age = re.search(r"aged about (\d+)", m)
                    _age_n = int(_age.group(1)) if _age else None
                    founder_died_this_step = {"year": y, "aged_about": _age_n}
                    # SAVED, NOT ONLY LOGGED - see _founder_death_info's own
                    # comment on why the log alone cannot be trusted to
                    # survive a save and a resume.
                    s._founder_death_aged, s._founder_death_year = _age_n, y
            # AND STOP THE YEAR YOU WIN. Reaching the goal is no longer an
            # ending, so without this a `step 50` that crosses the finish line
            # would run on for another forty-nine years and mention it in
            # passing. It is the one moment in a run most worth handing back.
            if ran < years and s.goal_year == s.year:
                stopped_early = ("stopped after %d of the %d years you asked "
                                 "for: you reached it. Step again when you "
                                 "have had a look around."
                                 % (ran, years))
                break
            if ran < years and any(mk.lower() in m.lower() for _, m in _this_year
                                   for mk in _STEP_STOP_MARKERS):
                stopped_early = ("stopped after %d of the %d years you asked "
                                 "for: something happened that you warned "
                                 "yourself about and should see before more "
                                 "time passes. Step again when you are ready."
                                 % (ran, years))
                break
        out = dict(ok=True, completed=completed, lost=lost, events=events)
        if founder_died_this_step:
            out["the_founder_died_this_step"] = founder_died_this_step
        if stopped_early:
            out["stopped_early"] = stopped_early
        if multi_year_hours_warning:
            out["multi_year_hours_warning"] = multi_year_hours_warning
        out.update(_agent_state(s, nodes))
        return out

    if op == "quit":
        return {"ok": True, "bye": True}

    # THE LIST MUST NOT GO STALE. This was ten commands hard-coded into a
    # string while the game had grown to twenty-four, so a player who mistyped
    # was handed a list that silently omitted labour, hire, train, commission,
    # money, risk, policy, quote, close, mothball, restore, work and bribe.
    # A help message that is wrong is worse than none, because it is believed.
    return {"ok": False,
            "error": "unknown cmd %r. Use one of: %s. %s"
                     % (op, ", ".join(KNOWN_COMMANDS),
                        'Or {"cmd":"help"} for what each one does.')}


SAVE_FIELDS = (
    # THE LOG, which the `log` command exists to read back and which was not
    # saved. The opening screen promises "progress is written to this file
    # after every command, so you can stop any time - close the terminal,
    # anything - and come back to exactly where you left off", and a break
    # tester did exactly that and found `log` answering "nothing has happened
    # yet" while money, reputation and technologies were all intact. A history
    # that does not survive the thing the game tells you to do is not a history.
    "log",
    "year", "capital", "done", "granted", "active", "done_year", "training",
    "scholars", "artisans", "directors_extra", "reputation", "suspicion",
    "scandal", "eminence", "protection", "familiarity", "forest_ha",
    "nitre_bed_m2", "mine_pending", "mine_ready",
    # WORKINGS, PLURAL: mine_capacity used to be the saved field, one float
    # per material; it is now a computed property (economy.py), so what
    # gets saved is the list it is computed FROM - each working with its
    # own material, capacity, commissioning year, capex and depletion
    # clock. Missing entirely, as in every save from before workings
    # existed, reads back as no workings at all - see load_state's own
    # migration of a genuinely old "mine_capacity" blob into this shape,
    # which does not happen here but right after this loop, because it has
    # to know whether "mines" was actually present in the file first.
    "mines",
    "mine_tranches", "market_pressure", "slaves", "freedmen",
    "manumitted_total", "goal_year", "dead_reason", "insolvent_years",
    "bribes_ytd", "living_cost_paid", "mine_cost_paid", "spend_last_year",
    "output_factor", "economy", "throttle", "binding", "bountied",
    "stalled", "life_left", "founder_alive", "revealed", "last_settlement",
    "employees", "trades_created", "policy", "mothballed", "operating",
    "forgotten", "opened_year", "last_taught", "paid_towards",
    "contract_hours",
    "commissioned", "teaching_hours_this_year", "wages_paid",
    "bondage_years_left", "bondage_debt", "money_real", "credit_frozen_until",
    # Counters and within-year tallies that were being silently reset on every
    # single command, because with --session every command is a save and a load.
    # wage_hours_this_year is the dangerous one: it is the tally that stops you
    # selling the same year's hours twice, so dropping it handed the exploit
    # straight back to anyone playing the ordinary way, across sittings.
    "interest_paid", "wage_hours_this_year", "teaching_hours_this_year",
    "trade_hours_used", "total_spend", "director_hours_spent_founder",
    "bounties_paid", "atrocity", "suspicion_mult", "gov", "wages_earned",
    "last_patron_death", "_said_debasement", "_said_autoopen", "_said_output",
    "_said_scandal", "_said_parallelism",
    "_said_command_index",
    "_said_deputies",
    "_said_near_limit",
    "shut_for_staff",
    # TONNES ON HAND. Own production a year did not use banks here instead of
    # evaporating, which is what lets a twenty-gram gold demand be met by
    # buying twenty grams rather than by commissioning a mine. It has to
    # survive a save: without it a resumed game silently starts at zero stock
    # and plays differently from the one that was saved, which is the same
    # class of fault as the fog that could be rewound by reloading. Counter
    # round-trips through JSON as a plain object and comes back a dict, which
    # the accessor treats alike.
    "_material_stock_ledger",
    "last_withdrawal",
    "wages_prepaid",
    # WHAT AN INSTITUTION GAVE YOU OUTRIGHT (see _grant_staff, labour.py).
    # scholars/artisans are saved as their current totals two lines up, but
    # _resync_pools() recomputes both from `employees` on every step and adds
    # this back in - so a save missing it would read correctly right up until
    # the next step, then silently lose the school's +4 scholars the same way
    # the bug this field fixes did.
    "granted_staff",
    # hours_this_year: last year's founder-hours accounting (see step(), just
    # before the within-year tallies above reset). Without it, `state` right
    # after a `--session` reload would report nothing for a figure the player
    # just saw.
    "hours_this_year",
    # THE FOUNDER'S AGE AT DEATH, so it survives a --session reload. `log`
    # is not a saved field, so without these two the one place the age had
    # ever been written would go empty on resume and `state` would silently
    # stop being able to say it - see _founder_death_info.
    "_founder_death_aged", "_founder_death_year",
    # HOW MANY UNITS OF EACH SCALABLE INSTITUTION ARE ACTUALLY FOUNDED. See
    # ProjectsMixin.institution_units (projects.py): a save missing this
    # entirely - every save from before institutions were quantities - is
    # read as every open one being exactly 1.0 unit, which is exactly what it
    # always was, so an old save resumes unchanged.
    "inst_units",
    # WHEN a taught trade was first taught, and which taught trades this
    # society has since naturalised on its own - see
    # SocietyMixin.advance_society (society.py). Missing entirely, as in
    # every save from before this existed, reads back as "no trade has been
    # taught long enough yet to naturalise", which is exactly true of a save
    # from before the mechanism could ever have fired.
    "trade_introduced_year", "trades_endemic",
    # ONE SNAPSHOT A YEAR, for `changes` and `economy`'s "what moved most" -
    # see _dashboard_snapshot. Missing entirely, as in every save from
    # before this existed, reads back as no history at all, which `changes`
    # already handles by name ("nothing has been recorded yet"); it is not
    # backfilled, because there is nothing honest to backfill it from.
    "_dashboard_history",
    # RETRY LEARNING, WHICH WAS BEING ERASED BY THE VERY ACT OF SAVING.
    # failed_attempts is what _retry_risk_multiplier and
    # _retry_calendar_retain are computed from (projects.py), so a node the
    # household has failed three times faces 0.53 of its bare risk and banks
    # 56.9% of the elapsed clock toward the next attempt. None of that was
    # in this tuple, so it all reset to "nothing has ever been tried" on
    # every resume: three failures on zone_refining went from a 23.8% next
    # attempt back to the full 45%, and `why`'s own attempts_already_failed
    # told the player 0 about a node they had failed six times. The player
    # who won this game complained that repeated 45% failures had "no
    # strategic mitigation visible" - the mitigation existed and the save
    # round-trip was deleting it. A defaultdict comes back from JSON as a
    # plain dict, which is promoted in load_state before anything adds to it.
    #
    # `shortages` is the same omission with far lower stakes: a diagnostic
    # tally of which material bound in which year, read by `run`/`compare`'s
    # cross-seed summary (cli.py) and by nothing that decides anything. It
    # is here so that a resumed game's own record of what it has been short
    # of is continuous, not because any mechanic reads it.
    "failed_attempts", "shortages",
)


def save_state(s, path):
    """Write the whole game to a file.

    There was no save, which is why every playtester ended up writing a driver
    script to hold one long session across many calls. That is a thing a tester
    can do and a player should never have to, so the fix is not a better script,
    it is a save file.
    """
    blob = {}
    for f in SAVE_FIELDS:
        v = getattr(s, f, None)
        if isinstance(v, set):
            v = {"__set__": sorted(v)}
        blob[f] = v
    blob["_civ"] = s.civ.get("id")
    # THE GOAL YOU CHOSE, same reasoning as _fog/_immortal just below: it is
    # a choice the menu asked about when this game began, not a flag that
    # should silently reset to the transistor because a resume happened to
    # omit --goal. See load_state.
    blob["_goal"] = getattr(s, "goal", None)
    blob["_civ_live"] = {k: s.civ.get(k) for k in
                         ("literacy_general", "literacy_elite", "state_capacity")}
    blob["_weights"] = dict(s.w)
    blob["_fog"] = getattr(s, "fog", False)
    # WHETHER THE FOUNDER AGES, saved for the same reason fog is: they are
    # choices the menu asks you to make about what game this is, and resuming
    # into the other one is resuming into a different game. _fog was already
    # written here and never read back, so every resumed game silently had the
    # whole tree in view; see load_state.
    blob["_immortal"] = bool(s.cfg.get("immortal", True))
    # THE DICE, TOO. Nothing saved the random state, so every resume restarted
    # it from the seed and re-rolled everything the world does. A break tester
    # found the sharp edge of that: a project sitting at its completion
    # threshold re-rolls its failure check on each resume, so
    # `start fin_bimetallism` then one `step` per process oscillated
    # 100%/60%/100%/60% for ever, burning hours and money and never finishing.
    # They reproduced it 5 times out of 5. It also meant hazards, sackings and
    # events were silently re-drawn every time a player came back to a save,
    # which is a different game from the one they left.
    try:
        st = s.rng.getstate()
        blob["_rng"] = [st[0], list(st[1]), st[2]]
    except Exception:
        blob["_rng"] = None
    blob["_version"] = 1
    tmp = path + ".tmp"
    # A save into a directory that is not there killed the process outright on
    # a FileNotFoundError, which is the one thing a save must never do.
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)
    with open(tmp, "w") as fh:
        json.dump(blob, fh, indent=1, sort_keys=True, default=str)
    os.replace(tmp, path)          # atomic: a crash mid-save cannot eat the game
    return path


# Required to even consider a file a save from this game. Not all of
# SAVE_FIELDS: most of it is optional (fields that did not exist yet when an
# older save was written are just skipped, same as always), but a file
# missing any of these is not a save, it is some other JSON document.
REQUIRED_SAVE_FIELDS = ("year", "capital", "done", "active", "_civ", "_version")

# Fields that hold a SET of node ids (see save_state's {"__set__": [...]}
# encoding). Anything named here is checked against the currently loaded
# tree, because the tree is data and does get edited: a node can be renamed
# or removed between when a save was written and when it is read back.
# NOT trades_created. That holds TRADE names - "optician", "chemist" - and it
# was in this list, so `train optician 1` wrote a perfectly valid trade into
# the save and the next load refused the whole file for referring to a
# technology called optician that the tree does not have and never did. A
# normal-play tester lost two runs to it, and it is worse than losing a save:
# the five trades that have to be taught are the ones gating chemistry,
# precision and electricity, so the one action that opens the second half of
# the game was the one action that destroyed the game.
_SET_FIELDS_OF_NODE_IDS = ("done", "granted", "mothballed", "operating",
                           "bountied",
                           "revealed")
# Checked against the wage table instead, which is what they actually are.
# trades_endemic holds trade names for the same reason trades_created does
# (see the comment just above) and needs exactly the same protection: it is
# a set of TRADE names, not node ids, so it belongs here and not in
# _SET_FIELDS_OF_NODE_IDS.
_SET_FIELDS_OF_TRADE_NAMES = ("trades_created", "trades_endemic")


def _validate_save(blob, s):
    """None if `blob` looks like a save this game could have produced and can
    be loaded into `s` as it stands right now; otherwise a short, plain
    sentence saying why not.

    `load` used to accept any JSON object at all: a typo'd filename, an
    unrelated file, a save from a different civilisation, or a save that
    refers to a node a later edit to the tech tree renamed or removed. Every
    one of those went straight into setattr() - which either corrupted the
    running game half-applied (fields earlier in SAVE_FIELDS take, the rest
    do not, because the loop does not stop for a bad value) or surfaced as a
    bare Python exception. This runs to completion BEFORE a single attribute
    of `s` is touched, so a bad file costs exactly one clear sentence and
    nothing else about the running game changes.
    """
    if not isinstance(blob, dict):
        return ("this is not a save from this game: expected a JSON object, "
                "got %s" % type(blob).__name__)
    missing = [f for f in REQUIRED_SAVE_FIELDS if f not in blob]
    if missing:
        return ("this is not a save from this game: missing %s. A save this "
                "game writes always has all of: %s"
                % (", ".join(missing), ", ".join(REQUIRED_SAVE_FIELDS)))
    if not isinstance(blob.get("_version"), int):
        return "this save is corrupt: '_version' should be a whole number"
    for f in ("year", "capital"):
        v = blob.get(f)
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            return "this save is corrupt: '%s' should be a number, got %r" % (f, v)

    civ_id = blob.get("_civ")
    have_civ = s.civ.get("id")
    if civ_id != have_civ:
        return ("this save is from a different civilisation (%r); this game "
                "is running %r. Start the agent with --civ %s to load it."
                % (civ_id, have_civ, civ_id))

    active = blob.get("active")
    if not isinstance(active, dict):
        return "this save is corrupt: 'active' should be an object of id -> progress"
    for k, v in active.items():
        if not isinstance(k, str) or not isinstance(v, dict):
            return "this save is corrupt: active[%r] is not a valid entry" % (k,)
        for f in ("ph_left", "spent"):
            if f not in v or isinstance(v[f], bool) or not isinstance(v[f], (int, float)):
                return ("this save is corrupt: active[%r] is missing a numeric "
                         "'%s'" % (k, f))

    done = blob.get("done")
    if not (isinstance(done, dict) and isinstance(done.get("__set__"), list)):
        return "this save is corrupt: 'done' should be a set of ids"

    # Every node id the save refers to must still exist in the tree we have
    # loaded right now.
    unknown = set()
    for f in _SET_FIELDS_OF_NODE_IDS:
        v = blob.get(f)
        if v is None:
            continue
        ids = v.get("__set__") if isinstance(v, dict) else None
        if ids is None or not all(isinstance(x, str) for x in ids):
            return "this save is corrupt: '%s' should be a set of id strings" % f
        unknown |= {x for x in ids if x not in s.nodes}
    unknown |= {k for k in active if k not in s.nodes}
    for f in _SET_FIELDS_OF_TRADE_NAMES:
        v = blob.get(f)
        if v is None:
            continue
        ids = v.get("__set__") if isinstance(v, dict) else None
        if ids is None or not all(isinstance(x, str) for x in ids):
            return "this save is corrupt: '%s' should be a set of trade names" % f
        strange = [x for x in ids if x not in WAGES]
        if strange:
            return ("this save refers to trade(s) this game does not have: %s"
                    % ", ".join(sorted(strange)[:6]))
    if unknown:
        sample = ", ".join(sorted(unknown)[:6])
        more = "" if len(unknown) <= 6 else " and %d more" % (len(unknown) - 6)
        return ("this save refers to node(s) the current tech tree does not "
                "have: %s%s. The tree has changed since this was saved; it "
                "cannot be loaded against this version of the game."
                % (sample, more))
    return None


def civ_of_save(path):
    """Which civilisation a save file is from, or None if it will not say.

    A save records the game it is; a command line resuming it should not have
    to be told again. A playtester was handed `play --session england_1300.json`
    by the game itself, ran exactly that, and was refused with "this save is
    from a different civilisation" - because the flag defaulted to Rome. The
    file knew the answer the whole time.
    """
    try:
        with open(path) as fh:
            return (json.load(fh) or {}).get("_civ")
    except (OSError, ValueError, AttributeError):
        return None


def goal_of_save(path):
    """Which goal a save file was playing toward, or None if it will not
    say (an older save, or one the file on disk does not match). Same
    reasoning as civ_of_save just above, and used the same way: a resumed
    session should not need --goal repeated any more than it needs --civ
    repeated, and a strategy order picked before the save is even read
    would be picked for the wrong goal.
    """
    try:
        with open(path) as fh:
            return (json.load(fh) or {}).get("_goal")
    except (OSError, ValueError, AttributeError):
        return None


def load_state(s, path):
    """Read a save from `path` and apply it to `s`, or raise ValueError with
    a clear reason and leave `s` completely untouched.

    Validation (see _validate_save) always runs to completion first; nothing
    below it can execute against a file that failed. A half-loaded game is
    worse than a refused one.
    """
    blob = json.load(open(path))
    bad = _validate_save(blob, s)
    if bad:
        raise ValueError(bad)
    # FOG IS A PROPERTY OF THE GAME YOU CHOSE, NOT A FIELD IN A FILE, and this
    # has to be checked BEFORE anything is applied - the fog flag is restored
    # further down, so a check placed after it is checking the value it was
    # about to reject. `load` validated the filename carefully and the contents
    # barely at all, so a hand-edited save with "_fog": false turned the fog
    # off in a running fogged game and `path` began answering, in a game whose
    # own help says there is no way to view the whole tree. A break tester did
    # exactly that. A save may resume the fog it was played with; it may not
    # switch the fog off underneath you.
    if getattr(s, "fog", False) and blob.get("_fog") is False:
        raise ValueError("that save was played without fog of war and this "
                         "game is being played with it. A save cannot turn the "
                         "fog off; start a new game without it if that is what "
                         "you want.")
    for f in SAVE_FIELDS:
        if f not in blob:
            continue
        v = blob[f]
        # NEVER restore a null over a live default. A field that had not been
        # initialised yet when the game was saved, spend_last_year and
        # insolvent_years among them, was written as null and then loaded back
        # OVER the number the constructor had just set, so the next `state`
        # died on round(None). A naive tester hit this on the very first
        # save-and-restart, which is the exact workflow the welcome text tells
        # players is safe, and went back to holding a process open through a
        # FIFO instead. My own round-trip tests missed it because I happened to
        # step the clock first, which initialises those fields.
        if v is None:
            continue
        if isinstance(v, dict) and "__set__" in v:
            v = set(v["__set__"])
        setattr(s, f, v)
    # PROMOTE THE ACCUMULATORS BACK, before anything adds to one. JSON has no
    # defaultdict and no Counter, so the loop above has just put plain dicts
    # where projects.py does `self.failed_attempts[k] += 1` and economy.py
    # does `self.shortages[who] += 1`, both of which raise KeyError on a new
    # key in a plain dict. Same shape as economy.py's own _material_stock
    # promotion, done here rather than lazily because these two are written
    # to directly rather than through an accessor.
    s.failed_attempts = collections.defaultdict(
        int, {k: int(v) for k, v in (getattr(s, "failed_attempts", None) or {}).items()})
    s.shortages = collections.Counter(getattr(s, "shortages", None) or {})
    # A SAVE FROM BEFORE WORKINGS EXISTED still names real capacity, under
    # the old field name "mine_capacity" (one float per material - see
    # SAVE_FIELDS's own comment on "mines"). "mines" is not in SAVE_FIELDS
    # any more, so the loop above never touches it, and a file that
    # predates this change has no "mines" key at all to have skipped. Carry
    # that capacity forward as one working per material rather than losing
    # it outright - but do NOT invent the year it was commissioned, which
    # this file never recorded and a dashboard agent was right to refuse to
    # fabricate: "opened_year": None, shown as "unknown" rather than a
    # guess (see _agent_mines/render_mines).
    if "mines" not in blob and isinstance(blob.get("mine_capacity"), dict):
        s.mines = [{"material": m, "capacity": float(amt),
                    "opened_year": None, "capex_paid": None,
                    "intensity_yrs": 0.0}
                   for m, amt in sorted(blob["mine_capacity"].items())
                   if isinstance(amt, (int, float)) and amt > 0]
    # `operating` JUST WENT BACK TO BEING A PLAIN SET. The generic setattr
    # above has no idea self.operating is normally an _InvalidatingSet (see
    # economy.py) and replaced it with whatever plain `set(...)` came out of
    # the save - correct in content, but silently unable to invalidate
    # capability_factor()'s cache on any future .add/.discard. That is a
    # real gap, not a theoretical one: `load` reached through the agent/play
    # JSON protocol runs this against the SAME long-lived Sim a session goes
    # on playing in, not a fresh one, and every open/close/mothball after
    # this point mutates .operating directly. Re-wrap it, once, here.
    s._reset_operating()
    # The game this save IS, not whatever the command line happened to say.
    if "_fog" in blob:
        s.fog = bool(blob["_fog"])
        if s.fog and not hasattr(s, "revealed"):
            s.revealed = set()
    if "_immortal" in blob:
        s.cfg["immortal"] = bool(blob["_immortal"])
    # A save from before goal selection existed has no "_goal" at all, and
    # one whose goal node a later tree edit removed should not crash a
    # resume - either way, fall back to whatever the command line/default
    # already set on `s` before this was called, rather than raise.
    if blob.get("_goal") in s.nodes:
        s.goal = blob["_goal"]
    if blob.get("_rng"):
        try:
            _v, _keys, _g = blob["_rng"]
            s.rng.setstate((_v, tuple(int(x) for x in _keys), _g))
        except Exception:
            pass          # an old save without dice is still a loadable save

    for k, v in (blob.get("_civ_live") or {}).items():
        if v is not None:
            s.civ[k] = v
    s.w.update(blob.get("_weights") or {})
    s.state_capacity = float(s.civ.get("state_capacity", s.state_capacity))
    s.fog = bool(blob.get("_fog", False))
    return s
