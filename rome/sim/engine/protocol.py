"""The JSON protocol a player or an agent speaks.

One object per line in, one object per line out. It explains itself: there is
no protocol document to read, on purpose.
"""
import collections, json, math, os, random
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
                     "bountied": k in s.bountied}
    end_reason = _agent_end_reason(s)
    full = bool((cmd or {}).get("full"))
    out = {
        "year": s.year, "capital": round(s.capital, 1), "revenue": round(s.revenue(), 1),
        "upkeep": round(s.upkeep(), 1),
        # A playtester watched capital fall 400 to 184 on the first step with
        # nothing active and both revenue and upkeep reported as zero, and no
        # field in the protocol explained where the money went. It went on food,
        # rent, tax and keeping up appearances, which the model has always
        # charged and never showed. Anything that moves your money should be
        # visible in the state that claims to describe your money.
        "living_cost": round(s.living_cost(), 1),
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
        "founder_hours_available": round(s.director_pool(), 1),
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
            "how to send a command": (
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
                            "to sink. Materials: " + ", ".join(Sim.MINE_CAPEX_PER_T_YR),
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


def _agent_dispatch(s, nodes, cmd):
    if not isinstance(cmd, dict) or "cmd" not in cmd:
        return {"ok": False, "error": "each line must be a JSON object with a 'cmd' field, "
                                      "e.g. {\"cmd\":\"state\"}"}
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
                "error": "id must be a string, got %s. Nothing was changed."
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
            return {"ok": False, "error": "id must be a string, got %s" % type(k).__name__}
        if k not in nodes:
            near = [x for x in nodes if str(k).lower() in x.lower()]
            return {"ok": False, "error": "unknown node %r. did you mean: %s"
                    % (k, ", ".join(near[:8]) or "no idea")}
        return dict(ok=True, **_node_explain(s, nodes, k))

    if op == "path":
        if getattr(s, "fog", False):
            return {"ok": False,
                    "error": "you cannot plan a route to something you have not "
                             "discovered. Nobody can tell you what a thing requires "
                             "until you know the thing exists. Use 'available' to see "
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
            got = s.open_mine(mat, n)
            if got <= 0:
                return {"ok": False, "error": "could not commission any %s capacity right now "
                                              "(capital too low, ceiling reached, or standing "
                                              "too low for a concession that size)" % mat}
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
        ok, err = s.hire(cmd.get("trade"), _num(cmd.get("n"), 1))
        if not ok:
            return {"ok": False, "error": err}
        return {"ok": True, "hired": cmd.get("trade"), "n": cmd.get("n"),
                "you_now_employ": round(s.employees.get(str(cmd.get("trade")).lower(), 0.0), 2),
                "annual_wage_bill": round(s.wage_bill(), 1),
                "capital": round(s.capital, 1)}

    if op in ("fire", "dismiss"):
        ok, err = s.fire(cmd.get("trade"), _num(cmd.get("n"), 1))
        if not ok:
            return {"ok": False, "error": err}
        return {"ok": True, "let_go": cmd.get("trade"),
                "annual_wage_bill": round(s.wage_bill(), 1)}

    if op == "train":
        if ended:
            return {"ok": False, "error": "the run has ended (%s)" % ended}
        ok, msg = s.train(cmd.get("trade"), _num(cmd.get("n"), 1), cmd.get("from"))
        if not ok:
            return {"ok": False, "error": msg}
        return {"ok": True, "training": msg, "capital": round(s.capital, 1),
                "your_hours_left_this_year": round(
                    max(0.0, s.director_pool() - s.director_hours_committed()), 1)}

    if op in ("commission", "job"):
        if ended:
            return {"ok": False, "error": "the run has ended (%s)" % ended}
        ok, msg = s.commission(cmd.get("trade"), _num(cmd.get("hours"), 0))
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

    if op == "bribe":
        ok, msg = s.bribe(_num(cmd.get("amount"), 0))
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
                    "auto_shed": "let go of works that cost more than they return",
                    "auto_bribe": "pay your way out of a scandal before it kills you",
                },
                "note": "Anything switched off here you can still do by hand: hire, "
                        "train, buy, commission, mothball, restore, bribe."}

    if op in ("save", "load"):
        path = cmd.get("file") or cmd.get("path")
        if not isinstance(path, str) or not path:
            return {"ok": False, "error": 'give a filename, e.g. {"cmd":"save","file":"mygame.json"}'}
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
        try:
            years = int(cmd.get("years", 1))
        except (TypeError, ValueError):
            return {"ok": False, "error": "years must be an integer"}
        if years < 1:
            return {"ok": False, "error": "years must be >= 1"}
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

    return {"ok": False, "error": "unknown cmd %r. use one of: state, available, why, path, "
                                  "start, stop, bounty, buy, step, quit" % op}


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
    blob["_version"] = 1
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(blob, fh, indent=1, sort_keys=True, default=str)
    os.replace(tmp, path)          # atomic: a crash mid-save cannot eat the game
    return path


def load_state(s, path):
    blob = json.load(open(path))
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
    for k, v in (blob.get("_civ_live") or {}).items():
        if v is not None:
            s.civ[k] = v
    s.w.update(blob.get("_weights") or {})
    s.state_capacity = float(s.civ.get("state_capacity", s.state_capacity))
    s.fog = bool(blob.get("_fog", False))
    return s
