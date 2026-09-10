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
                   load_geography, load_resources)


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
            return ("the horizon at %d AD is reached. You built %d things of your "
                    "own. There was no target to hit; how far you got is the whole "
                    "of the result." % (end_year, len(s.done - s.granted)))
        return "ran out of horizon (%d AD) without reaching the goal" % end_year
    return None


def _agent_state(s, nodes, cmd=None):
    active = {}
    for k, st in s.active.items():
        n = nodes[k]
        bill = st.get("cost_left")
        if bill is None:
            bill = max(0.0, s.project_cost(k) - st["spent"])
        active[k] = {"name": n["name"], "founder_hours_left": round(st["ph_left"], 1),
                     "founder_hours_total": n["ph"], "years_in_progress": st["yrs"],
                     "spent": round(st["spent"], 1), "still_to_pay": round(bill, 1),
                     # A tester poured 1,200 hours into a project that was
                     # calendar-locked and could not use them, and only noticed by
                     # reading state closely. Say which of the three things it is
                     # actually waiting for.
                     "waiting_on": (
                         ("nobody to do the work: " + ", ".join(st["short_of_trade"]))
                         if st.get("short_of_trade")
                         else "money" if st["ph_left"] <= 0 and bill > 0.5
                         else "the calendar" if st["ph_left"] <= 0
                         else "your hours"),
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
        # net_per_year counts the STANDING flows only. It never counted what
        # projects consume, which is usually the largest outflow by far, so a
        # playtester watched it report a healthy positive number for eight
        # consecutive years while capital sat at exactly 0.0, every denarius
        # going into the work in progress. A field that says you are making
        # money while you are visibly making none is worse than no field.
        # Named for what it is. The roll happens after the spending loop, so this
        # is the year just simulated, not the one before it.
        "project_spend_this_year": round(getattr(s, "spend_last_year", 0.0), 1),
        "net_after_project_spend": round(s.revenue() - s.upkeep() - s.living_cost()
                                         - s.mine_operating_cost()
                                         - getattr(s, "spend_last_year", 0.0), 1),
        "net_per_year": round(s.revenue() - s.upkeep() - s.living_cost()
                              - s.mine_operating_cost(), 1),
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
            max(0.0, s.director_pool()
                - getattr(s, "wage_hours_this_year", 0.0)), 1),
        "founder_hours_sold_for_wages_this_year": round(
            getattr(s, "wage_hours_this_year", 0.0), 1),
        # LAST YEAR'S HOURS, ACCOUNTED FOR. Set in step(); see the comment
        # there. available is this year's fresh figure, not last year's -
        # read it alongside, not in place of, hours_this_year.
        "hours_this_year": getattr(s, "hours_this_year", None),
        "founder_alive": s.founder_alive,
        "scholars": round(s.scholars, 2), "artisans": round(s.artisans, 2),
        "directors_extra": round(s.directors_extra, 2),
        "reputation": round(s.reputation, 1), "suspicion": round(s.suspicion, 2),
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
        "knowledge_risk": s.knowledge_risk(),
        "resource_throttle": round(s.throttle, 3), "throttle_binding": s.binding,
        "forest_ha": round(s.forest_ha, 1),
        "mine_capacity": {m: round(v, 1) for m, v in s.mine_capacity.items()},
        "slaves": s.slaves, "freedmen": s.freedmen,
        "scholars_including_you": round(s.effective_scholars(), 2),
        "founder_ages": not s.cfg.get("immortal", True),
        "goal": None if getattr(s, "fog", False) else s.goal,
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
               "sittings", "fog")


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
            "what you are trying to do": (
                "Advance as far as you can before the horizon at %d. There is no "
                "score but the state of what you have built." % s.end_year
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
            "buy": "forest, mine, slaves, or manumit; see the economy topic",
            "work <trade> <hours>": "do an ordinary job for ordinary pay",
            "bounty <id>": "pay someone else to solve it instead",
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

    if topic in ("economy", "money", "buy"):
        return {"the ledger": '{"cmd":"money"} itemises what comes in and what '
                              "goes out, including where the income comes from",
                "buy forest": '{"cmd":"buy","what":"forest","n":100} hectares of '
                              "coppice, which is where charcoal comes from",
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


def _brief(s, nodes, k, fog):
    n = nodes[k]
    if fog:
        return {"id": k, "name": n["name"],
                "cost": round(s.project_cost(k), 1),
                "your_hours": n["ph"],
                "least_years": n["yrs"],
                "chance_of_failure": n["risk"]}
    return {"id": k, "name": n["name"], "tier": n["tier"], "cat": n["cat"],
            "cost": round(s.project_cost(k), 1), "founder_hours": n["ph"],
            "calendar_floor_years": n["yrs"], "risk": n["risk"]}


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

    want_subject = (cmd.get("subject") or cmd.get("group") or "").strip().lower()
    find = (cmd.get("find") or cmd.get("search") or "").strip().lower()
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
    if afford is not None:
        sel = [k for k in sel if s.project_cost(k) <= afford]

    heard = []
    if fog:
        heard = sorted(k for k in getattr(s, "revealed", set())
                       if k not in s.done and k not in s.active
                       and not s.start_reason(k)[0])[:25]
    heard_block = [{"id": k, "name": nodes[k]["name"],
                    "why_not": s.start_reason(k)[1]} for k in heard]

    # A LIST was asked for: a subject, a search, an explicit page, or everything.
    if find or want_subject or limit or offset or show_all or afford is not None:
        page = sel if show_all else sel[offset:offset + (limit or 30)]
        out = {"ok": True, "count": len(sel), "of_everything_startable": len(ok),
               "showing": "%d-%d%s" % (offset + 1, offset + len(page),
                                       (" " + why_these) if why_these else ""),
               "available": [_full_entry(s, nodes, k, fog) for k in page]}
        if not show_all and offset + len(page) < len(sel):
            out["more"] = ('%d more; ask again with "offset": %d'
                           % (len(sel) - offset - len(page), offset + len(page)))
        if fog and heard_block and offset == 0:
            out["heard_of_but_cannot_begin"] = heard_block
        return out

    # DEFAULT: the digest.
    groups = {}
    for k in ok:
        g = groups.setdefault(_subject_of(nodes[k]), [])
        g.append(k)
    purse = s.capital + s.credit_limit() * 0.5
    rows = []
    for name, ks in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        costs = sorted(s.project_cost(k) for k in ks)
        rows.append({"subject": name, "things": len(ks),
                     "cheapest": round(costs[0], 1),
                     "dearest": round(costs[-1], 1),
                     "you_could_pay_for": sum(1 for c in costs if c <= purse)})
    cheap = sorted(ok, key=lambda k: s.project_cost(k))[:6]
    out = {"ok": True, "count": len(ok),
           "showing": "a summary by subject, because the full list is %d things"
                      % len(ok),
           "subjects": rows,
           "cheapest_six": [_full_entry(s, nodes, k, fog) for k in cheap],
           "to_see_more": {
               "one subject": '{"cmd":"available","subject":"metallurgy"}',
               "by name": '{"cmd":"available","find":"furnace"}',
               "what you can pay for": '{"cmd":"available","afford":%d}' % int(max(0, purse)),
               "a page of everything": '{"cmd":"available","limit":30,"offset":0}',
               "all of it at once": '{"cmd":"available","all":true} (large)'}}
    if fog and heard_block:
        out["heard_of_but_cannot_begin"] = heard_block
    if fog:
        out["note"] = ("Under fog you see only what you could begin now, and things "
                       "you have heard of. There is no way to see the whole tree.")
    return out


def _node_explain(s, nodes, k):
    n = nodes[k]
    need = closure(nodes, k) - {k}
    unlocks = [] if getattr(s, "fog", False) else [m for m in nodes if k in nodes[m]["pre"]]
    blocks = {m for m in nodes if k in closure(nodes, m)} - {k}
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
                 "total": round(s.project_cost(k), 1)},
        "upkeep": n["up"], "revenue": n["rev"],
        "calendar_floor_years": n["yrs"], "risk": n["risk"],
        "staff_needed": {"scholars": n["sch"], "artisans": n["art"]},
        "you_have": {"scholars": round(s.effective_scholars(), 1),
                     "artisans": round(s.artisans, 1)},
        "suspicion": n.get("sus", 0), "state_interest_trait_score": n.get("gov", 0),
        "bounty_eligible_by_type": bounty_by_type,
        "direct_prerequisites": n["pre"],
        "missing_prerequisites": [p for p in n["pre"] if p not in s.done],
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
        "downstream_count": (len(blocks) if not getattr(s, "fog", False) else None),
        "how_much_rests_on_this": (
            None if not getattr(s, "fog", False) else
            "almost everything" if len(blocks) > 1200 else
            "a great deal" if len(blocks) > 300 else
            "a fair amount" if len(blocks) > 40 else
            "a few things" if len(blocks) > 3 else
            "nothing else; this is worth having for itself"),
        # Under fog there is no goal, so a boolean saying whether this is "on the
        # goal path" is either meaningless or a leak. A tester read it as
        # true/false for five hundred years while `state.goal` was null and
        # reasonably asked what path it could possibly mean.
        "on_goal_path": (None if getattr(s, "fog", False)
                         else (k == s.goal or s.goal in blocks)),
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
    L.append("You: %s%s, %s founder-hours free this year"
             % ("alive" if out.get("founder_alive") else "DEAD",
                " and ageing" if out.get("founder_ages") else " (you do not age)",
                _fmt_num(out.get("founder_hours_available"))))

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
        L.append("  %-28s %3.0f%% of your hours spent, %s den still owed - waiting on %s"
                 % ((st.get("name") or k)[:28], pct, _fmt_num(st.get("still_to_pay")),
                    st.get("waiting_on") or "-"))
        if st.get("why_underfunded"):
            L.append("      %s" % st["why_underfunded"])

    employees = out.get("employees") or {}
    L.append("")
    L.append("EMPLOY: %s people, %s den/yr in wages"
             % (_fmt_num(out.get("employees_total")), _fmt_num(out.get("annual_wage_bill"))))
    for t, v in sorted(employees.items()):
        L.append("  %-16s %s" % (t, _fmt_num(v)))
    if not employees:
        L.append("  nobody")
    if out.get("staff_are_fractional_because"):
        L.append(_wrap(out["staff_are_fractional_because"], indent="  "))

    L.append("")
    L.append("STANDING: reputation %s   suspicion %s   scandal %s   eminence %s"
             % (_fmt_num(out.get("reputation")), _fmt_num(out.get("suspicion")),
                _fmt_num(out.get("scandal")), _fmt_num(out.get("eminence"))))
    prom = out.get("prominence") or {}
    if prom:
        # SAY WHICH NUMBER IT IS ABOUT. This line sat directly under the row
        # showing reputation, suspicion, scandal and eminence, and refers to the
        # LAST of those - so a break tester with suspicion pinned at 30 read
        # "dangerous above 26 ... 0% chance of ruin this year" as a flat
        # contradiction, and wrote the whole mechanic off as inert. It was
        # answering a question they had not asked.
        L.append("  EMINENCE is dangerous above %s (settles near %s if nothing "
                 "changes; %s chance of ruin this year)"
                 % (_fmt_num(prom.get("dangerous_above")),
                    _fmt_num(prom.get("settles_at_if_nothing_changes")),
                    _pct(prom.get("chance_of_ruin_this_year"))))
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
        L.append("Fog of war is on. No score but what you built: %s of your own so far."
                 % _fmt_num(out.get("done_earned")))
    elif out.get("goal"):
        L.append("")
        L.append("Goal: %s%s" % (out["goal"],
                 ("  -- REACHED in %s AD" % out.get("goal_year")) if out.get("goal_reached") else ""))

    completed = out.get("completed")
    events = out.get("events")
    if completed or events:
        head = []
        for c in completed or []:
            head.append("  COMPLETED %s: %s" % (c.get("year"), c.get("name")))
        for e in events or []:
            head.append("  EVENT %s: %s" % (e.get("year"), e.get("message")))
        L = head + [""] + L if head else L

    also = out.get("also_available")
    if also:
        L.append("")
        L.append("more: " + "; ".join(also))
    return "\n".join(L)


def _available_row(e):
    hours = e.get("founder_hours", e.get("your_hours"))
    years = e.get("calendar_floor_years", e.get("least_years"))
    risk = e.get("risk", e.get("chance_of_failure"))
    return "%-32s %-32s %10s %8s %6s %6s" % (
        (e.get("id") or "")[:32], (e.get("name") or "")[:32],
        _fmt_num(e.get("cost")), _fmt_num(hours), _fmt_num(years), _pct(risk))


def render_available(out):
    """A scannable table: every column aligned, sorted cheapest-first so the
    same eye scan works whether you are looking for a bargain or a subject.
    """
    L = ["AVAILABLE: %s startable now" % _fmt_num(out.get("count"))]
    if out.get("showing"):
        L.append(out["showing"])
    L.append("")
    header = "%-32s %-32s %10s %8s %6s %6s" % ("ID", "NAME", "COST", "HOURS", "YEARS", "RISK")

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
            L.append(_available_row(e))
        L.append("")
        for k, v in (out.get("to_see_more") or {}).items():
            L.append("  %s: %s" % (k, v))
    elif "available" in out:
        L.append(header)
        for e in sorted(out["available"], key=lambda e: e.get("cost", 0)):
            L.append(_available_row(e))
        if out.get("more"):
            L.append("")
            L.append(out["more"])

    heard = out.get("heard_of_but_cannot_begin")
    if heard:
        L.append("")
        L.append("HEARD OF, CANNOT BEGIN YET:")
        for h in heard:
            L.append("  %-28s %s" % (h["id"][:28], h.get("why_not") or ""))
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
    L.append("COST: %s den total  (%s labour + %s materials + %s capital, then x%s your civ, x%s distance, x%s prices)"
             % (_fmt_num(cost.get("total")), _fmt_num(cost.get("labour")),
                _fmt_num(cost.get("materials")), _fmt_num(cost.get("capital")),
                _fmt_num(cost.get("civ_domain_factor")), _fmt_num(cost.get("material_distance_factor")),
                _fmt_num(cost.get("price_index"))))
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
        if missing:
            L.append("MISSING PREREQUISITES: " + ", ".join(missing))
        elif direct:
            L.append("PREREQUISITES (all met): " + ", ".join(direct))
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
        for k, v in sorted(src.items(), key=lambda kv: -(kv[1] if isinstance(kv[1], (int, float)) else 0)):
            L.append("    %-28s %s" % (k, _fmt_num(v)))
    costs = out.get("what_it_costs_you") or {}
    if costs:
        L.append("Costs:")
        for k, v in costs.items():
            L.append("  %-30s %s" % (k.replace("_", " "), _fmt_num(v)))
    L.append("Net/yr: %s     spent on projects last step: %s"
             % (_fmt_num(out.get("net_per_year")), _fmt_num(out.get("spent_on_projects_last_year"))))
    L.append("Credit limit: %s     interest on arrears: %s     paid so far: %s"
             % (_fmt_num(out.get("credit_limit")), _pct(out.get("interest_rate_on_arrears")),
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
        L.append("you employ: %s     market can supply: %s hours" % (_fmt_num(t.get("you_employ")), _fmt_num(t.get("hours_the_market_can_supply"))))
        if t.get("note"):
            L.append(_wrap(t["note"]))
        return "\n".join(L)
    L = ["LABOUR", "ON YOUR STAFF:"]
    staff = out.get("on_your_staff")
    if isinstance(staff, list) and staff:
        for r in staff:
            L.append("  %-16s %8s   %s den/yr each" % (r["trade"], _fmt_num(r["you_employ"]), _fmt_num(r["a_year_of_one"])))
    else:
        L.append("  nobody")
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
            indent, ", ".join("%s (%s den)" % (e["id"], _fmt_num(e["cost"])) for e in now))
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
    "hazards": render_risk,
}


# A REPLY IS FULL OF WORKED EXAMPLES, and until now every one of them was
# JSON: 'more: knowledge_risk -> {"cmd":"risk"}'. That is exactly right when a
# script is reading, and exactly wrong in front of a person who has just been
# told to type words. The JSON payload itself must not change - it is the
# protocol - so the translation happens here, on the rendered text only, and
# only when the caller says the reader is typing.
TYPED_HINTS = False


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
        out = fn(resp)
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
}


def _typed_number(tok):
    """The token as a number, or None. Tolerates 1,000 and 1_000 because
    people type both, and a thousand-separator is not a syntax error."""
    try:
        return float(str(tok).replace(",", "").replace("_", ""))
    except (TypeError, ValueError):
        return None


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
            elif _typed_number(w) is not None:
                out["afford"] = _typed_number(w)
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
        # A bare 'n' is one year, which is what it has always meant.
        return {"cmd": "step", "years": (nums[0] if nums else 1)}, None

    if op in ("why", "path", "start", "stop", "bounty", "mothball", "restore"):
        if not rest:
            return None, ("%s needs the name of a technology, e.g. '%s "
                          "fud_wheelbarrow'. 'available' lists what you can "
                          "begin now." % (op, op))
        return {"cmd": op, "id": rest[0]}, None

    if op == "bribe":
        if not nums:
            return None, "bribe needs an amount, e.g. 'bribe 500'."
        return {"cmd": "bribe", "amount": nums[0]}, None

    if op == "labour":
        return {"cmd": "labour", "trade": (words[0].lower() if words else None)}, None

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
        if out["what"] not in ("forest", "slaves", "mine", "mines", "people",
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


def _agent_dispatch(s, nodes, cmd):
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
        if _op in _ID_COMMANDS and isinstance(_k, str) and _k in nodes \
                and not s.is_visible(_k):
            return {"ok": False,
                    "error": "you have never heard of that. You know what you have "
                             "built and what you could begin next; nothing tells you "
                             "what lies beyond that."}
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
        if isinstance(k, str) and k in nodes and not s.is_visible(k):
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
            near = [x for x in nodes if str(k).lower() in x.lower()]
            return {"ok": False, "error": "unknown node %r. did you mean: %s"
                    % (k, ", ".join(near[:8]) or "no idea")}
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
        return {"ok": True, "id": k, "done": k in s.done,
                "remaining_count": len(remaining), "remaining": remaining}

    if op == "start":
        if ended:
            return {"ok": False, "error": "the run has ended (%s); nothing more can be started" % ended}
        k = cmd.get("id")
        if k not in nodes:
            return {"ok": False, "error": "unknown node id %r. use {\"cmd\":\"available\"} "
                                          "or {\"cmd\":\"why\",\"id\":...} to find valid ids" % k}
        ok, why = s.start_project(k)
        if not ok:
            return {"ok": False, "error": why}
        n = nodes[k]
        out = {"ok": True, "started": k, "name": n["name"], "founder_hours_needed": n["ph"],
               "calendar_floor_years": n["yrs"]}
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
        try:
            n = float(cmd.get("n", 0))
        except (TypeError, ValueError):
            return {"ok": False, "error": "n must be a number"}
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
            got = s.buy_slaves(int(n))
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
        pay, err = s.work_for_wages(cmd.get("trade"), cmd.get("hours", 0))
        if err:
            return {"ok": False, "error": err}
        return {"ok": True, "trade": cmd.get("trade"), "hours": cmd.get("hours"),
                "earned": round(pay, 1), "capital": round(s.capital, 1),
                "your_hours_left_this_year": round(
                    max(0.0, s.director_pool() - s.wage_hours_this_year), 1)}

    if op in ("risk", "hazards"):
        kr = s.knowledge_risk()
        return {"ok": True, "knowledge_risk": kr,
                "note": "What history is about to do to you, and what you have "
                        "built that blunts it. Every hazard here is fightable."}

    if op in ("money", "ledger", "accounts"):
        fixed = s.upkeep() + s.living_cost() + s.mine_operating_cost()
        return {"ok": True,
                "capital": round(s.capital, 1),
                "revenue": round(s.revenue(), 1),
                "where_the_money_comes_from": s.revenue_sources(),
                "what_it_costs_you": {
                    "upkeep_of_what_you_built": round(s.upkeep(), 1),
                    "living_and_appearances": round(s.living_cost() - s.wage_bill(), 1),
                    "wages": round(s.wage_bill(), 1),
                    "mines_standing": round(s.mine_operating_cost(), 1)},
                "net_per_year": round(s.revenue() - fixed, 1),
                "spent_on_projects_last_year": round(getattr(s, "spend_last_year", 0.0), 1),
                "credit_limit": round(s.credit_limit(), 1),
                "interest_rate_on_arrears": round(s.debt_interest_rate(), 4),
                "interest_paid_in_total": round(getattr(s, "interest_paid", 0.0), 1),
                "still_owed_on_work_in_hand": round(
                    sum(st.get("cost_left") or 0.0 for st in s.active.values()), 1)}

    if op == "labour":
        one = (cmd.get("trade") or "").strip().lower()
        if one and one not in WAGES:
            return {"ok": False, "error": "no such trade: %s. They are: %s"
                    % (one, ", ".join(sorted(WAGES)))}
        def row(t, long=False):
            r = {"trade": t,
                 "a_year_of_one": round(ANNUAL_WAGE.get(t, 375.0) * s.wage_index
                                        * s.price_index, 0),
                 "you_employ": round(s.employees.get(t, 0.0), 2)}
            if long:
                r.update({"kind": trade_family(t),
                          "wage_per_hour": round(WAGES[t] * s.wage_index
                                                 * s.price_index, 3),
                          "hours_the_market_can_supply": round(s.market_supply(t), 0),
                          "note": TRADE_NOTES.get(t, "")})
            return r
        if one:
            r = row(one, long=True)
            r["exists_here"] = s.trade_available(one)
            return {"ok": True, "trade": r}
        have = sorted(t for t in WAGES if s.employees.get(t, 0.0) > 0.005)
        hirable = sorted(t for t in WAGES
                         if s.trade_available(t) and t not in have)
        absent = sorted(t for t in WAGES if not s.trade_available(t))
        return {"ok": True,
                "on_your_staff": [row(t) for t in have] or "nobody",
                "you_could_hire_here": hirable,
                "do_not_exist_here": absent,
                "you_employ_in_total": round(sum(s.employees.values()), 2),
                "slaves": s.slaves, "freedmen": s.freedmen,
                "annual_wage_bill": round(s.wage_bill(), 1),
                "craftsmen_on_your_staff": round(s.artisans, 2),
                "scholars_including_you": round(s.effective_scholars(), 2),
                "in_training": [
                    {"trade": (r_[2] if len(r_) > 2 else None),
                     "people": (r_[3] if len(r_) > 3 else round(r_[0], 2)),
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
        return {"ok": True, "let_go": cmd.get("trade"),
                "annual_wage_bill": round(s.wage_bill(), 1)}

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
        if what != "mine":
            return {"ok": False, "error": 'only mines can be quoted so far: '
                                          '{"cmd":"quote","what":"mine",'
                                          '"material":"coal","n":500}'}
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
        return {"ok": True, "policy": dict(s.policy), "changed": changed,
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
        completed, events = [], []
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
            for y, m in s.log[before_log:]:
                events.append({"year": y, "message": m})
        out = dict(ok=True, completed=completed, events=events)
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
    "employees", "trades_created", "policy", "mothballed", "contract_hours",
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
    "last_patron_death", "_said_debasement",
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
    blob["_version"] = 1
    tmp = path + ".tmp"
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
_SET_FIELDS_OF_NODE_IDS = ("done", "granted", "mothballed", "bountied",
                           "trades_created", "revealed")


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
    for k, v in (blob.get("_civ_live") or {}).items():
        if v is not None:
            s.civ[k] = v
    s.w.update(blob.get("_weights") or {})
    s.state_capacity = float(s.civ.get("state_capacity", s.state_capacity))
    s.fog = bool(blob.get("_fog", False))
    return s
