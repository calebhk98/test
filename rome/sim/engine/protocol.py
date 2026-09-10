"""The JSON protocol a player or an agent speaks.

One object per line in, one object per line out. It explains itself: there is
no protocol document to read, on purpose.
"""
import collections, json, math, os, random, re
from collections import defaultdict

from .data import *          # the shared tables and loaders
from .data import (WAGES, ANNUAL_WAGE, TRADE_NOTES, TRADES_ABSENT,
                   TRADE_FAMILY, TECH_EFFECTS, DEFAULTS, SHOCKS,
                   STARTING_KITS, trade_family, closure, critical_path,
                   topo_order, load, load_civ, haversine_km,
                   load_geography, load_resources, money_word,
                   downstream_count, is_downstream)


from .core import Sim


def _agent_end_reason(s):
    """None while the run is live; otherwise why it stopped, for state() and
    to refuse further start/stop/bounty/buy commands once it has."""
    end_year = getattr(s, "end_year", s.cfg["start_year"] + s.cfg["horizon_years"])
    if s.dead_reason:
        return s.dead_reason
    if s.goal_year:
        return "goal reached: %s completed in %d AD" % (s.goal, s.goal_year)
    if s.year >= end_year:
        # Under fog there IS no stated goal, so saying the player failed to reach
        # one is incoherent. A tester finished a 500 year run and was told they
        # had missed a goal they were never shown and had no way to set.
        if getattr(s, "fog", False):
            # It said "there was no target to hit", which was false: there is
            # one, `help` names it now, and telling a player at the end that
            # they were never aiming at anything is the same lie the other way
            # round.
            return ("the horizon at %d AD is reached. You built %d things of your "
                    "own and did not reach %s."
                    % (end_year, len(s.done - s.granted),
                       s.nodes[s.goal]["name"].lower() if s.goal in s.nodes else "the goal"))
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
    short = []
    for t, want in (n["lab"] or {}).items():
        need = want * frac
        if need <= 0:
            continue
        supply = s.market_supply(t) + s.contract_hours.get(t, 0.0)
        have = supply - s.trade_hours_used.get(t, 0.0)
        if have < need:
            # The society's CAPACITY is the durable fact and the one a player
            # can act on; what is left after this year's bookings is noise that
            # changes every step. Say the first, and only mention the second
            # when it is what is actually binding.
            if supply < need:
                short.append("%s (wants %.0f hours a year; this society can "
                             "field %.0f at most)" % (t, need, max(0.0, supply)))
            else:
                short.append("%s (wants %.0f hours a year; the %ss here can "
                             "supply %.0f but your other work has them booked)"
                             % (t, need, t, max(0.0, supply)))
    if short:
        return "nobody to do the work: " + "; ".join(sorted(short)[:3])
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
    return "your hours"


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
    L.append("=" * 70)
    return "\n".join(L)


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
        "net_after_project_spend": round(s.revenue() - s.upkeep() - s.living_cost()
                                         - s.mine_operating_cost()
                                         - max(0.0, -s.capital) * s.debt_interest_rate()
                                         - getattr(s, "spend_last_year", 0.0), 1),
        "net_per_year": round(s.revenue() - s.upkeep() - s.living_cost()
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
        out["also_available"] = elided
        out["everything_at_once"] = '{"cmd":"state","full":true}'
    return out


HELP_TOPICS = ("commands", "labour", "economy", "money", "automatic",
               "sittings", "fog", "eminence", "risk", "protection")


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
            "the four you need first": {
                "state": "where you stand",
                "available": "what you could begin today",
                "why <id>": "everything known about one thing",
                "step <years>": "let time pass",
            },
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
                         'add subject, find, afford, limit/offset, or all:true',
            "why <id>": "everything known about one thing",
            "start <id>": "begin work on something",
            "stop <id>": "abandon it, losing what you have spent",
            "step <years>": "let time pass",
            "money": "the whole ledger: what comes in, what goes out",
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
                          else "what something still needs"),
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
                            + ", ".join(Sim.MINE_CAPEX_PER_T_YR),
                "buy slaves": '{"cmd":"buy","what":"slaves","n":5}. This is '
                              "available because it was the ordinary condition of "
                              "production in most of these societies, and a model "
                              "that hides it lies about the cost of everything.",
                "manumit": '{"cmd":"buy","what":"manumit","n":5} frees people you '
                           "hold. They then work better, and it is the decent thing.",
                "debt": "You may spend past what you have, as far as somebody will "
                        "lend you and no further. Arrears cost interest."}

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
    """True when you could NOT staff this today. Marks the row with a *."""
    return bool(n["art"] > s.artisans + 1e-9
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
        return {"id": k, "name": n["name"],
                "cost": round(s.project_cost(k), 1),
                "your_hours": n["ph"],
                "least_years": n["yrs"],
                "chance_of_failure": n["risk"],
                "earns_per_year": round(n["rev"], 1),
                "costs_per_year_after": round(n["up"], 1),
                "how_much_rests_on_this": rests,
                **_staff_fields(s, n)}
    return {"id": k, "name": n["name"], "tier": n["tier"], "cat": n["cat"],
            **_staff_fields(s, n),
            "cost": round(s.project_cost(k), 1), "founder_hours": n["ph"],
            "calendar_floor_years": n["yrs"], "risk": n["risk"],
            "earns_per_year": round(n["rev"], 1),
            "costs_per_year_after": round(n["up"], 1),
            "downstream_count": downstream_count(nodes, k)}


def _full_entry(s, nodes, k, fog):
    e = _brief(s, nodes, k, fog)
    n = nodes[k]
    if fog:
        e["summary"] = s.fog_summary(k)
        if n["lab"]:
            e["trades_needed"] = sorted(n["lab"])
    else:
        e["prerequisites"] = n["pre"]
        e["note"] = n["note"]
    return e


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
    if find or want_subject or limit or offset or show_all or afford is not None:
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
        page = sel if show_all else sel[offset:offset + (limit or 30)]
        out = {"ok": True, "count": len(sel), "of_everything_startable": len(ok),
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
        if not show_all and offset + len(page) < len(sel):
            out["more"] = ('%d more; ask again with "offset": %d'
                           % (len(sel) - offset - len(page), offset + len(page)))
        if fog and heard_block and offset == 0:
            out["heard_of_but_cannot_begin"] = heard_block
            if heard_more:
                out["and_more_you_have_heard_of"] = (
                    "%d more, nearest first; ask again with heard_offset %d"
                    % (heard_more, heard_from + len(heard_block)))
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
               "a page of everything": '{"cmd":"available","limit":30,"offset":0}',
               "all of it at once": '{"cmd":"available","all":true} (large)'}}
    if fog and heard_block:
        out["heard_of_but_cannot_begin"] = heard_block
        if heard_more:
            out["and_more_you_have_heard_of"] = (
                'ask again with {"cmd":"available","heard_offset":%d} for %d '
                "more, nearest first"
                % (heard_from + len(heard_block), heard_more))
    if fog:
        out["note"] = ("Under fog you see only what you could begin now, and things "
                       "you have heard of. There is no way to see the whole tree.")
    return out


def _rests_band(n):
    """How much rests on a node, in the words a person in the year 100 could
    actually use. The exact count is a fog spoiler; the band is not."""
    return ("almost everything" if n > 1200 else
            "a great deal" if n > 300 else
            "a fair amount" if n > 40 else
            "a few things" if n > 3 else
            "nothing else; this is worth having for itself")


def _node_explain(s, nodes, k):
    n = nodes[k]
    need = closure(nodes, k) - {k}
    unlocks = [] if getattr(s, "fog", False) else [m for m in nodes if k in nodes[m]["pre"]]
    # Was: {m for m in nodes if k in closure(nodes, m)} - a full ancestor
    # closure of all 2,831 nodes, per call. Same answers, computed once for the
    # whole tree and cached. See data.descendants.
    n_blocks = downstream_count(nodes, k)
    bounty_by_type = (n["tier"] <= 2 and n["cat"] in ("glass_optics", "metallurgy", "precision",
                      "power", "agriculture", "information", "instruments"))
    started = k in s.done or k in s.active
    out = {
        "id": k, "name": n["name"], "tier": n["tier"], "cat": n["cat"], "confidence": n["conf"],
        "note": n["note"], "kb": n["kb"],
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
                         "and what a material costs to get."},
        "upkeep": n["up"], "revenue": n["rev"],
        "calendar_floor_years": n["yrs"], "risk": n["risk"],
        "staff_needed": {"scholars": n["sch"], "artisans": n["art"]},
        "you_have": {"scholars": round(s.effective_scholars(), 1),
                     "artisans": round(s.artisans, 1)},
        "suspicion": n.get("sus", 0), "state_interest_trait_score": n.get("gov", 0),
        "bounty_eligible_by_type": bounty_by_type,
        # NOT CHARGED UNTIL YOU OPEN IT. A tester read the upkeep off `why`,
        # built the thing, and found nothing on the bill - correctly, because
        # revenue and upkeep follow what you RUN. The figure is real; it just
        # is not yours yet.
        "revenue_and_upkeep_apply_only_once_opened": (
            True if (n["rev"] > 0 or n["up"] > 0) and k not in s.granted
            and k not in s.operating else None),
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
        "chain_founder_hours": (sum(nodes[x]["ph"] for x in need)
                                if not getattr(s, "fog", False) else None),
        "chain_cost": (round(sum(nodes[x]["_total_cost"] for x in need), 1)
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


def _pct(v):
    """A 0..1 fraction as a percentage a person reads at a glance."""
    if v is None:
        return "-"
    try:
        return "%.0f%%" % (100.0 * float(v))
    except (TypeError, ValueError):
        return str(v)


def _wrap(text, width=76, indent=""):
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
    money_line = "Money: %s den" % _fmt_num(out.get("capital"))
    if net_after is not None:
        money_line += "    net %s%s den/yr (after %s den into projects this year)" % (
            "+" if net_after >= 0 else "", _fmt_num(net_after), _fmt_num(spend or 0))
    elif net_plain is not None:
        money_line += "    standing net %s%s den/yr (does not count project spend)" % (
            "+" if net_plain >= 0 else "", _fmt_num(net_plain))
    L.append(money_line)
    if out.get("in_bondage_for_debt"):
        L.append("IN DEBT BONDAGE: %s years left owing %s den"
                 % (_fmt_num(out["in_bondage_for_debt"]), _fmt_num(out.get("debt_still_to_work_off"))))

    # WHETHER YOU AGE IS A FACT ABOUT THE GAME YOU ARE PLAYING, and the human
    # rendering did not carry it: a mortal run and an immortal one looked
    # identical here, though the menu asks you to choose between them and one
    # of them ends with everything you have not made permanent dying with you.
    _src = out.get("where_your_hours_come_from") or {}
    _dep = _src.get("deputies_who_direct_work_for_you") or 0
    L.append("You: %s%s, %s founder-hours free this year%s"
             % ("alive" if out.get("founder_alive") else "DEAD",
                " and ageing" if out.get("founder_ages") else " (you do not age)",
                _fmt_num(out.get("founder_hours_available")),
                ("   (%s of your own, plus %s deputies directing work in your "
                 "name at %s hours each)"
                 % (_fmt_num(_src.get("you")), _fmt_num(_dep),
                    _fmt_num(_src.get("hours_each_deputy_adds"))))
                if _dep else ""))

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
        L.append("AHEAD: %s technologies at risk, %s lost per sacking on average, hedged by %s"
                 % (_fmt_num(kr.get("technologies_at_risk")),
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
    elif out.get("goal"):
        L.append("")
        L.append("Goal: %s%s" % (out["goal"],
                 ("  -- REACHED in %s AD" % out.get("goal_year")) if out.get("goal_reached") else ""))

    completed = out.get("completed")
    events = out.get("events")
    lost = out.get("lost")
    if completed or events or lost:
        head = []
        for c in completed or []:
            head.append("  COMPLETED %s: %s" % (c.get("year"), c.get("name")))
        for c in lost or []:
            head.append("  LOST %s: %s%s"
                        % (c.get("year"), c.get("name"),
                           " (restore brings it back for a fraction of the cost)"
                           if c.get("can_be_restored") else ""))
        for e in events or []:
            head.append("  EVENT %s: %s" % (e.get("year"), e.get("message")))
        L = head + [""] + L if head else L

    also = out.get("also_available")
    if also:
        L.append("")
        L.append("more: " + "; ".join(also))
    return "\n".join(L)


# The short forms of the bands, so the column stays a column.
_RESTS_SHORT = {"almost everything": "ALL", "a great deal": "much",
                "a fair amount": "some", "a few things": "few",
                "nothing else; this is worth having for itself": "-"}


def _available_row(e, w=34):
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
        _fmt_num(e.get("cost")), _fmt_num(hours), _fmt_num(years), _pct(risk),
        _fmt_num(e.get("earns_per_year")), _fmt_num(e.get("costs_per_year_after")),
        staff, rests)


def render_available(out):
    """A scannable table: every column aligned, sorted cheapest-first so the
    same eye scan works whether you are looking for a bargain or a subject.
    """
    L = ["AVAILABLE: %s startable now" % _fmt_num(out.get("count"))]
    if out.get("showing"):
        L.append(out["showing"])
    L.append("")
    # Sized to the longest id ON THIS PAGE, so the table stays aligned without
    # ever cutting the one string the player has to type next.
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
            L.append(_available_row(e, _w))
        if out.get("most_rests_on_these"):
            L.append("")
            L.append("MOST RESTS ON THESE, of what you could begin today:")
            L.append(header)
            for e in out["most_rests_on_these"]:
                L.append(_available_row(e, _w))
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
        for e in sorted(out["available"], key=lambda e: e.get("cost", 0)):
            L.append(_available_row(e, _w))
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
            L.append("  A * means you do not have them yet - 'hire' or 'train' "
                     "first, or the work waits.")

    heard = out.get("heard_of_but_cannot_begin")
    if heard:
        L.append("")
        L.append("HEARD OF, CANNOT BEGIN YET:")
        for h in heard:
            L.append("  %-34s %s" % (h["id"], h.get("why_not") or ""))
        if out.get("and_more_you_have_heard_of"):
            L.append("  " + str(out["and_more_you_have_heard_of"]))
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
    L.append("YOUR HOURS: %s     CALENDAR FLOOR: %s years     FAILURE RISK: %s"
             % (_fmt_num(out.get("founder_hours")), _fmt_num(out.get("calendar_floor_years")),
                _pct(out.get("risk"))))
    staff, have = out.get("staff_needed") or {}, out.get("you_have") or {}
    L.append("STAFF NEEDED: %s scholars, %s artisans   (you have %s, %s)"
             % (_fmt_num(staff.get("scholars")), _fmt_num(staff.get("artisans")),
                _fmt_num(have.get("scholars")), _fmt_num(have.get("artisans"))))
    lab = out.get("hired_labour") or {}
    if lab:
        L.append("HIRED LABOUR: " + ", ".join("%s %sh" % (t, _fmt_num(h)) for t, h in lab.items()))
    mat = out.get("materials") or {}
    if mat:
        L.append("MATERIALS: " + ", ".join("%s %s" % (m, _fmt_num(q)) for m, q in mat.items()))
    if out.get("upkeep") or out.get("revenue"):
        L.append("UPKEEP: %s den/yr     REVENUE: %s den/yr"
                 % (_fmt_num(out.get("upkeep")), _fmt_num(out.get("revenue"))))

    L.append("")
    status = ("DONE" if out.get("done") else
              "ACTIVE" if out.get("active") else
              "CAN START NOW" if out.get("can_start_now") else "BLOCKED")
    L.append("STATUS: %s" % status)
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
            # KNOWN, NOT RUNNING. Since knowing a thing and operating it became
            # two different states, a play tester reasonably asked which one a
            # prerequisite wants, and nothing anywhere said. It wants the
            # knowledge: finish the work once and it counts for ever, whether
            # or not you keep the concern open.
            L.append("MISSING PREREQUISITES: " + ", ".join(missing))
            L.append("  (a prerequisite has to be FINISHED, not merely started, "
                     "and it stays finished: you need not keep it running.)")
        elif direct:
            L.append("PREREQUISITES (all met, and finished counts for ever): "
                     + ", ".join(direct))
        else:
            L.append("PREREQUISITES: none, you can start this on arrival")

    if out.get("chain_size") is not None:
        L.append("")
        L.append("FULL CHAIN BEHIND IT: %s nodes, %s of your hours, %s den, %s-year serial floor"
                 % (_fmt_num(out["chain_size"]), _fmt_num(out.get("chain_founder_hours")),
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
    costs = out.get("what_it_costs_you") or {}
    if costs:
        L.append("Costs:")
        for k, v in costs.items():
            if v is None:
                continue
            L.append("  %-30s %s"
                     % (k.lstrip("_").replace("_", " "), _fmt_num(v)))
    L.append("Net/yr: %s     spent on projects last step: %s"
             % (_fmt_num(out.get("net_per_year")), _fmt_num(out.get("spent_on_projects_last_year"))))
    L.append("Credit limit: %s (%s used)     interest on arrears: %s     paid so far: %s"
             % (_fmt_num(out.get("credit_limit")),
                out.get("of_that_limit_you_have_used") or "none",
                _pct(out.get("interest_rate_on_arrears")),
                _fmt_num(out.get("interest_paid_in_total"))))
    if out.get("still_owed_on_work_in_hand"):
        L.append("Still owed on work in hand: %s" % _fmt_num(out["still_owed_on_work_in_hand"]))
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
            L.append("your own %ss add %s, so %s hours a year are available to you"
                     % (t.get("trade"), _fmt_num(t.get("hours_your_own_people_add")),
                        _fmt_num(t.get("hours_available_to_you_in_all"))))
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
    L.append("")
    L.append("YOU COULD HIRE: " + (", ".join(out.get("you_could_hire_here") or []) or "nobody new"))
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
    L.append("free to put behind something new: %s scholars, %s craftsmen"
             % (_fmt_num(free.get("scholars")), _fmt_num(free.get("craftsmen"))))
    if out.get("these_are_not_interchangeable"):
        L.append(_wrap(out["these_are_not_interchangeable"], indent="  "))
    L.append("")
    run = out.get("running")
    L.append("RUNNING")
    if isinstance(run, list) and run:
        L.append("  %-34s %10s %10s %8s" % ("ID", "EARNS/YR", "COSTS/YR", "NEEDS"))
        for r in run:
            nd = r.get("needs") or {}
            L.append("  %-34s %10s %10s %4s sch %3s cr"
                     % (r.get("id"), _fmt_num(r.get("earns_a_year")),
                        _fmt_num(r.get("costs_a_year")),
                        _fmt_num(nd.get("scholars")), _fmt_num(nd.get("craftsmen"))))
    else:
        L.append("  nothing")
    idle = out.get("you_know_how_but_have_not_opened")
    L.append("")
    L.append("YOU KNOW HOW, AND HAVE NOT OPENED")
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
    L = ["KNOWLEDGE AT RISK"]
    L.append("technologies at risk: %s     chance lost if a site is sacked: %s     fraction lost when it happens: %s"
             % (_fmt_num(kr.get("technologies_at_risk")), _pct(kr.get("loss_chance_if_a_site_is_sacked")),
                _pct(kr.get("fraction_lost_when_it_happens"))))
    L.append("hedge: %s" % (kr.get("hedged_by") or "none yet"))
    if kr.get("note"):
        L.append(_wrap(kr["note"]))
    L.append("")
    for h in kr.get("known_hazards_ahead") or []:
        yrs = h.get("years") or [0, 0]
        tag = "IN PROGRESS" if h.get("in_progress") else "%s-%s" % (yrs[0], yrs[-1])
        L.append("[%s] %s" % (tag, h.get("name")))
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


_RENDERERS = {
    "state": render_state, "step": render_step, "available": render_available,
    "why": render_why, "money": render_money, "ledger": render_money,
    "accounts": render_money, "labour": render_labour, "risk": render_risk,
    "hazards": render_risk, "ventures": render_ventures,
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
    "state", "available", "why", "path", "start", "stop", "step",
    "money", "risk", "labour", "policy", "help",
    "hire", "fire", "train", "commission", "work",
    "buy", "quote", "close", "bounty", "mothball", "restore", "bribe",
    "open", "ventures", "withdraw",
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
    "people": "labour", "staff": "labour", "workers": "labour",
    "dismiss": "fire", "sack": "fire", "lay": "fire",
    "job": "commission", "hireout": "commission",
    "teach": "train", "learn": "train",
    "price": "quote", "cost": "quote",
    "shut": "close", "closemine": "close", "close_mine": "close",
    "begin": "start", "research": "start", "build": "start",
    "explain": "why", "look": "why", "inspect": "why",
    "route": "path", "plan": "path",
    "retire": "withdraw", "step_back": "withdraw", "obscurity": "withdraw",
}


def _typed_number(tok):
    """The token as a number, or None. Tolerates 1,000 and 1_000 because
    people type both, and a thousand-separator is not a syntax error."""
    try:
        return float(str(tok).replace(",", "").replace("_", ""))
    except (TypeError, ValueError):
        return None


# The real ids, and a case-folded index onto them. Built once: parse_typed has
# no Sim to ask and runs on every line a player types.
NODE_IDS = frozenset(load()[2])
NODE_IDS_LOWER = {k.lower(): k for k in NODE_IDS}


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

    if op in ("money", "risk", "quit"):
        return {"cmd": op}, None

    if op == "state":
        # 'state full' and 'state full:true' both mean the same thing, and a
        # player who has read the JSON docs will type the second.
        want_full = bool(rest) and rest[0].lower().split(":")[0] == "full"
        return {"cmd": "state", "full": want_full}, None

    if op == "available":
        # 'available' alone is the digest. The rest are the same narrowings the
        # digest itself suggests, spelled the way a person would say them:
        #   available metallurgy      available find furnace
        #   available afford 900      available all
        #   available limit 30 offset 30
        out = {"cmd": "available"}
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
        want = rest[0]
        if want not in NODE_IDS:
            want = NODE_IDS_LOWER.get(want.lower(), want)
        return {"cmd": op, "id": want}, None

    if op in ("withdraw", "retire"):
        return {"cmd": "withdraw"}, None

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
    return _localise_money(_agent_dispatch_inner(s, nodes, cmd), money_word(s.civ))


def _agent_dispatch_inner(s, nodes, cmd):
    if not isinstance(cmd, dict) or "cmd" not in cmd:
        return {"ok": False, "error": "each line must be a JSON object with a 'cmd' field, "
                                      "e.g. {\"cmd\":\"state\"}"}
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
            return {"ok": False,
                    "error": "you have never heard of any such thing. You know "
                             "what you have built and what you could begin next; "
                             "nothing tells you what lies beyond that.%s"
                             % ((" Did you mean: " + ", ".join(near)) if near else "")}
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
        out = {"ok": True, "id": k, "done": k in s.done,
               "remaining_count": len(remaining), "remaining": remaining}
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
            return {"ok": False, "error": "the run has ended (%s); nothing more can be started" % ended}
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
        _impossible = []
        _n0 = nodes[k]
        _frac0 = min(1.0, 1.0 / max(1.0, _n0["yrs"]))
        for _t, _want in (_n0["lab"] or {}).items():
            _need = _want * _frac0
            if _need > 0 and s.market_supply(_t) + s.contract_hours.get(_t, 0.0) < _need:
                _impossible.append("%s (wants %.0f hours a year; this society can "
                                   "field %.0f at most)"
                                   % (_t, _need, max(0.0, s.market_supply(_t))))
        ok, why = s.start_project(k)
        if not ok:
            return {"ok": False, "error": why}
        n = nodes[k]
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
               "the_bill_you_have_taken_on": bill,
               "note": "This is the price as of today, and it is now fixed for "
                       "this project. Quotes move with prices, the coinage and "
                       "what a material costs to get: a figure you read years "
                       "ago is not what you will pay."}
        if _warn_staff:
            out["but"] = _warn_staff
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
        return {"ok": True, "stopped": k}

    if op == "bounty":
        if ended:
            return {"ok": False, "error": "the run has ended (%s); nothing more can be bought" % ended}
        k = cmd.get("id")
        if k not in nodes:
            return {"ok": False, "error": "unknown node id %r" % k}
        if k in s.done:
            return {"ok": False, "error": "%s is already done" % k}
        if k in s.active:
            return {"ok": False, "error": "%s is already active; stop it first if you want "
                                          "to switch to a bounty instead" % k}
        if not s.bounty_eligible(k):
            n = nodes[k]
            missing = [p for p in n["pre"] if p not in s.done]
            if missing:
                return {"ok": False, "error": "missing prerequisites: " + ", ".join(missing)}
            return {"ok": False,
                    "error": "not bounty-eligible (tier %d, category %s): a craftsman "
                             "in %s could not recognise success at this without "
                             "understanding the theory, so there is nothing to "
                             "award the prize for. A bounty works where the craft "
                             "already exists here and success is visible."
                             % (n["tier"], n["cat"],
                                s.civ.get("name", "this society"))}
        price = (nodes[k]["_total_cost"] * 2.5 * s.civ_cost_factor(k)
                 * s.material_cost_factor(k) * s.cost_money_factor())
        if not s.post_bounty(k):
            return {"ok": False, "error": "cannot afford the bounty: needs about %.0f denarii, "
                                          "you have %.0f. Earn or wait, then try again" % (price, s.capital)}
        return {"ok": True, "posted": k, "price": round(price, 1), "capital": round(s.capital, 1)}

    if op == "buy":
        if ended:
            return {"ok": False, "error": "the run has ended (%s); nothing more can be bought" % ended}
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
            if mat not in s.MINE_CAPEX_PER_T_YR:
                return {"ok": False, "error": "material must be one of: "
                                              + ", ".join(s.MINE_CAPEX_PER_T_YR)}
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
            return {"ok": False, "error": "the run has ended (%s)" % ended}
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
            out["it_cost_your_own_practice"] = round(_cost, 1)
            out["so_you_are_up"] = round(pay - _cost, 1)
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
        return {"ok": True, "knowledge_risk": kr,
                "note": "What history is about to do to you, and what you have "
                        "built that blunts it. Every hazard here is fightable."}

    if op in ("money", "ledger", "accounts"):
        fixed = s.upkeep() + s.living_cost() + s.mine_operating_cost()
        _ramp, _prac = s.still_ramping(), s.practice_note()
        return {"ok": True,
                "capital": round(s.capital, 1),
                "revenue": round(s.revenue(), 1),
                "where_the_money_comes_from": s.revenue_sources(),
                **({"still_building_up_custom": _ramp} if _ramp else {}),
                **({"about_your_own_practice": _prac} if _prac else {}),
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
                    "mines_standing": round(s.mine_operating_cost(), 1),
                    # A COST LIKE ANY OTHER. It was printed two lines below the
                    # net that ignored it, so a tester in a debt spiral read
                    # "+9.5 a year" while capital fell 105 and then 117.
                    "interest_on_arrears": round(
                        max(0.0, -s.capital) * s.debt_interest_rate(), 1)},
                "net_per_year": round(
                    s.revenue() - fixed
                    - max(0.0, -s.capital) * s.debt_interest_rate(), 1),
                "spent_on_projects_last_year": round(getattr(s, "spend_last_year", 0.0), 1),
                "credit_limit": round(s.credit_limit(), 1),
                "interest_rate_on_arrears": round(s.debt_interest_rate(), 4),
                "interest_paid_in_total": round(getattr(s, "interest_paid", 0.0), 1),
                # HOW CLOSE, not just how far it goes. See warn_near_the_limit.
                "of_that_limit_you_have_used": (
                    "%d%%" % (100.0 * -s.capital / max(1e-9, s.credit_limit()))
                    if s.capital < 0 and s.credit_limit() > 0 else "none"),
                "still_owed_on_work_in_hand": round(
                    sum(st.get("cost_left") or 0.0 for st in s.active.values()), 1)}

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
                          "hours_available_to_you_in_all": round(s.market_supply(t), 0),
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
        # NOT "TRADES YOU DO NOT YET EMPLOY". Excluding the ones you have reads
        # as "no more smiths available" the moment you hire your first smith,
        # which is false and which `hire smith 1` then contradicts. It is every
        # trade this society has.
        hirable = sorted(t for t in WAGES if s.trade_available(t))
        absent = sorted(t for t in WAGES if not s.trade_available(t))
        return {"ok": True,
                "on_your_staff": [row(t) for t in have] or "nobody",
                "you_could_hire_here": hirable,
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
                "what_raises_that_room": s._staff_advice("artisans"),
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
            return {"ok": False, "error": "the run has ended (%s)" % ended}
        n, err = _qty(cmd, "n", 1)
        if err:
            return {"ok": False, "error": err + ". Nothing was changed."}
        ok, err = s.hire(cmd.get("trade"), n)
        if not ok:
            return {"ok": False, "error": err}
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
        out = {"ok": True, "let_go": cmd.get("trade"),
               "annual_wage_bill": round(s.wage_bill(), 1)}
        if err:
            out["what_happened"] = err
        return out

    if op == "train":
        if ended:
            return {"ok": False, "error": "the run has ended (%s)" % ended}
        n, err = _qty(cmd, "n", 1)
        if err:
            return {"ok": False, "error": err + ". Nothing was changed."}
        ok, msg = s.train(cmd.get("trade"), n, cmd.get("from"))
        if not ok:
            return {"ok": False, "error": msg}
        return {"ok": True, "training": msg, "capital": round(s.capital, 1),
                "your_hours_left_this_year": round(
                    max(0.0, s.director_pool() - s.director_hours_committed()), 1)}

    if op in ("commission", "job"):
        if ended:
            return {"ok": False, "error": "the run has ended (%s)" % ended}
        hours, err = _qty(cmd, "hours")
        if err:
            return {"ok": False, "error": err + ". Nothing was changed."}
        ok, msg = s.commission(cmd.get("trade"), hours)
        if not ok:
            return {"ok": False, "error": msg}
        return {"ok": True, "commissioned": msg, "capital": round(s.capital, 1),
                "note": "These hours are available to your projects this year only."}

    if op == "mothball":
        ok, msg = s.mothball_work(cmd.get("id"))
        if not ok:
            return {"ok": False, "error": msg}
        return {"ok": True, "mothballed": msg, "upkeep": round(s.upkeep(), 1)}

    if op == "restore":
        ok, msg = s.restore_work(cmd.get("id"))
        if not ok:
            return {"ok": False, "error": msg}
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
            return {"ok": False, "error": "no such material: %r. Mineable: %s"
                    % (cmd.get("material"), ", ".join(sorted(Sim.MINE_CAPEX_PER_T_YR)))}
        return dict(ok=True, **q)

    if op in ("close", "close_mine"):
        if ended:
            return {"ok": False, "error": "the run has ended (%s)" % ended}
        ok, msg = s.close_mine(cmd.get("material") or cmd.get("what"))
        if not ok:
            return {"ok": False, "error": msg}
        return {"ok": True, "closed": msg,
                "mine_operating_cost": round(s.mine_operating_cost(), 1)}

    if op == "withdraw":
        if ended:
            return {"ok": False, "error": "the run has ended (%s)" % ended}
        ok, msg = s.withdraw_from_public_life()
        if not ok:
            return {"ok": False, "error": msg}
        return {"ok": True, "withdrew": msg,
                "eminence": round(s.eminence, 2),
                "reputation": round(s.reputation, 1),
                "protection": round(s.protection, 3)}

    if op == "bribe":
        if ended:
            return {"ok": False, "error": "the run has ended (%s)" % ended}
        amount, err = _qty(cmd, "amount")
        if err:
            return {"ok": False, "error": err + ". Nothing was changed."}
        ok, msg = s.bribe(amount)
        if not ok:
            return {"ok": False, "error": msg}
        return {"ok": True, "bribed": msg, "capital": round(s.capital, 1)}

    if op == "open":
        if ended:
            return {"ok": False, "error": "the run has ended (%s)" % ended}
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
        ok, msg = s.open_venture(k)
        if not ok:
            return {"ok": False, "error": msg}
        return {"ok": True, "opened": msg, "capital": round(s.capital, 1),
                "revenue": round(s.revenue(), 1), "upkeep": round(s.upkeep(), 1)}

    if op == "ventures":
        sch_free, art_free = s.venture_staff_free()
        running = sorted(s.operating)
        idle = sorted(k for k in s.done
                      if s.is_venture(k) and k not in s.operating)

        def _vrow(k):
            n = nodes[k]
            return {"id": k, "name": n["name"], "earns_a_year": n["rev"],
                    "costs_a_year": n["up"],
                    "needs": {"scholars": n["sch"], "craftsmen": n["art"]}}

        out = {"ok": True,
               "running": [_vrow(k) for k in running] or "nothing",
               "you_know_how_but_have_not_opened":
                   [dict(_vrow(k), to_open_it=round(s.venture_capex(k), 1))
                    for k in idle[:20]] or "nothing",
               "people_free_to_run_something_new": {
                   "scholars": round(sch_free, 2), "craftsmen": round(art_free, 2)},
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
                       "knowledge either way."}
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
        if len(idle) > 20:
            out["and_more_you_could_open"] = len(idle) - 20
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
                "what_each_does": {
                    "auto_hire": "grow the staff toward what you can house and pay",
                    "auto_buy_people": "buy slaves when the workshop is short-handed",
                    "auto_manumit": "free people you hold, over time",
                    "auto_train": "teach trades this society does not have when a "
                                  "project needs them",
                    "auto_mine": "sink a mine when a mineral is holding work up",
                    "auto_forest": "buy coppice when charcoal is holding work up",
                    "auto_mothball": "stop working mines you cannot pay for",
                    "auto_bribe": "pay your way out of a scandal before it kills you",
                    "auto_shed": "let go of WORKS that cost more than they return "
                                 "(this is about buildings and practices, not people)",
                    # SAY WHAT IT WILL NOT DO. A play tester found their
                    # nitre beds, lab apparatus and glassware left closed by
                    # this and concluded the lesson was "don't trust the
                    # automation". It is not broken; it only opens what plainly
                    # pays, and a capability you need but which earns less than
                    # it costs is exactly what it will leave shut.
                    "auto_open": "open concerns that plainly pay for themselves. "
                                 "It will NOT open anything whose upkeep exceeds "
                                 "its takings, however much you need it - open "
                                 "those yourself with 'open <id>'",
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
        # LOST, not only completed. A normal-play tester lost fourteen finished
        # works inside a single `step 12` - among them corpus_written and
        # school_founded, which they called the pivot of the entire game - and
        # wrote that "completions get EVENT lines; losses get nothing". The
        # engine does log the shedding, but nothing in the reply put a name
        # against what left, while every arrival got one. A game whose only
        # score is what you have built has to report subtraction at least as
        # loudly as addition.
        completed, lost, events = [], [], []
        end_year = s.end_year
        for _ in range(years):
            if s.dead_reason or s.goal_year or s.year >= end_year:
                break
            before_done, before_log = set(s.done), len(s.log)
            s.step()
            # sorted(), because this is a set difference and a set of strings
            # iterates in an order that depends on PYTHONHASHSEED. Two runs of
            # the same game with the same seed reported the same completions in
            # different orders, which is a small thing that makes the protocol's
            # own output impossible to diff. Caught by fingerprinting the
            # engine before and after being split into modules: every number
            # matched and this list did not.
            for k in sorted(s.done - before_done):
                completed.append({"id": k, "name": nodes[k]["name"], "year": s.done_year.get(k)})
            for k in sorted(before_done - s.done):
                lost.append({"id": k, "name": nodes[k]["name"], "year": s.year,
                             "can_be_restored": k in getattr(s, "mothballed", set())})
            for y, m in s.log[before_log:]:
                events.append({"year": y, "message": m})
        out = dict(ok=True, completed=completed, lost=lost, events=events)
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
    "year", "capital", "done", "granted", "active", "done_year", "training",
    "scholars", "artisans", "directors_extra", "reputation", "suspicion",
    "scandal", "eminence", "protection", "familiarity", "forest_ha",
    "nitre_bed_m2", "mine_capacity", "mine_pending", "mine_ready",
    "mine_tranches", "market_pressure", "slaves", "freedmen",
    "manumitted_total", "goal_year", "dead_reason", "insolvent_years",
    "bribes_ytd", "living_cost_paid", "mine_cost_paid", "spend_last_year",
    "output_factor", "economy", "throttle", "binding", "bountied",
    "stalled", "life_left", "founder_alive", "revealed", "last_settlement",
    "employees", "trades_created", "policy", "mothballed", "operating",
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
    "_said_deputies",
    "_said_near_limit",
    "shut_for_staff",
    "last_withdrawal",
    "wages_prepaid",
    # hours_this_year: last year's founder-hours accounting (see step(), just
    # before the within-year tallies above reset). Without it, `state` right
    # after a `--session` reload would report nothing for a figure the player
    # just saw.
    "hours_this_year",
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
_SET_FIELDS_OF_TRADE_NAMES = ("trades_created",)


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
    # The game this save IS, not whatever the command line happened to say.
    if "_fog" in blob:
        s.fog = bool(blob["_fog"])
        if s.fog and not hasattr(s, "revealed"):
            s.revealed = set()
    if "_immortal" in blob:
        s.cfg["immortal"] = bool(blob["_immortal"])
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
