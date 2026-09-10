#!/usr/bin/env python3
"""Every bug a playtester found, as a test that fails if it comes back.

Nine of these were found by agents playing the game through the JSON protocol,
and three of those were defects in the fix for the previous one. That pattern is
the reason this file exists: a fix verified once by hand is a fix that silently
rots. Run it with `python3 rome/sim/test_regressions.py`.
"""
import json, os, random, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import simulator as S
from engine import commodities as COMMOD

TREE, PRICES, NODES, WAGES, GOODS = S.load()
GOAL = TREE["meta"]["goal_node"]
_LAB, ORDER, _B = S.load_strategy("recommended", NODES, GOAL)
FAILURES = []
# Counted rather than hand-maintained: the tally in the summary line was a
# literal that three separate rounds of additions had to remember to update.
CHECKS_RUN = []
SKIPPED = []
_LAST_AT = time.time()


def sim(civ="rome_100ad", capital=None, manual=True, events=False):
    cfg = {"start_capital": capital} if capital is not None else None
    s = S.Sim(NODES, ORDER, random.Random(1), events=events, manual=manual,
              civ=S.load_civ(civ), cfg=cfg)
    s.goal, s.done_year = GOAL, {}
    return s


# SLOW CHECKS ARE OPT-IN. Three of these cost 83 of the suite's 89 seconds,
# because they each simulate a couple of hundred years to test a long-run
# property. A suite you run after every change has to be seconds, or you stop
# running it, which is the exact rot this file exists to prevent. So the
# default run is fast and the expensive ones go behind --slow, to be run every
# few commits and before anything is called finished.
SLOW = "--slow" in sys.argv or os.environ.get("ROME_SLOW_TESTS")


def slow_check(name, fn, detail_fn=None):
    """Run an expensive check only when asked; otherwise say it was skipped."""
    if not SLOW:
        SKIPPED.append(name)
        return
    ok, detail = fn()
    check(name, ok, detail)


def check(name, ok, detail=""):
    """Record a check, and how long the work before it took.

    The elapsed figure is the gap since the previous check, which is near
    enough to "what did this one cost" and needs no instrumentation at the
    call sites. It exists because the suite grew past fifteen minutes and got
    killed before finishing, and nobody could say which checks were expensive
    without timing them one at a time by hand.
    """
    global _LAST_AT
    now = time.time()
    took = now - _LAST_AT
    _LAST_AT = now
    CHECKS_RUN.append((name, took))
    # str(): a failing check whose detail was a dict, a list or None used to
    # kill the whole suite here on a TypeError, so the one run that had
    # something to report was the one run that reported nothing.
    detail = "" if detail is None else str(detail)
    print("  %-58s %s%s" % (name, "ok" if ok else "FAIL " + detail,
                            "   %4.0fs" % took if took >= 1.0 else ""))
    if not ok:
        FAILURES.append(name + " " + detail)


def proto(lines, civ="rome_100ad", kit=None, fog=False):
    """Drive the real protocol in a real subprocess, as a player would."""
    cmd = [sys.executable, os.path.join(HERE, "simulator.py"), "agent", "--civ", civ]
    if kit:
        cmd += ["--kit", kit]
    if fog:
        cmd += ["--fog"]
    p = subprocess.run(cmd, input="\n".join(json.dumps(c) for c in lines) + "\n",
                       capture_output=True, text=True, timeout=300, cwd=ROOT)
    out = []
    for ln in p.stdout.splitlines():
        try:
            out.append(json.loads(ln))
        except ValueError:
            pass
    return out, p.stdout, p.returncode


print("PLAYTEST REGRESSIONS\n" + "=" * 72)

# --- Rome BREAK: negative quantity minted money while reporting failure
r, _, _ = proto([{"cmd": "state"},
                 {"cmd": "buy", "what": "forest", "n": -5},
                 {"cmd": "state"}])
check("negative buy quantity changes nothing",
      r[0]["capital"] == r[-1]["capital"] and r[-1]["forest_ha"] == 0,
      "capital %s -> %s" % (r[0]["capital"], r[-1]["capital"]))

# --- Rome BREAK: a non-string id killed the process
r, _, rc = proto([{"cmd": "why", "id": {"a": 1}}, {"cmd": "state"}])
check("non-string id does not kill the session", rc == 0 and len(r) == 2)

# --- Norse BREAK: bare non-object JSON killed the process one line later
_, raw, rc = proto([])  # placeholder to keep the helper simple
p = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py"), "agent"],
                   input='null\n42\n"x"\n[1,2]\n{"cmd":"state"}\n',
                   capture_output=True, text=True, timeout=300, cwd=ROOT)
check("bare null/number/string/list does not kill the session",
      p.returncode == 0 and p.stdout.count("\n") >= 5)

# --- Norse BREAK: `why` crashed on nodes missing the v1 scalars
missing = [x["id"] for x in TREE["nodes"]
           if any(f not in x for f in ("sus", "gov", "tier", "cat", "pre"))]
check("no node is missing a required field", not missing, str(missing[:4]))

# --- Rome WEIRD: buy+manumit minted labour from money
s = sim(capital=200000.0)
a0 = s.artisans
s.buy_slaves(10); s.manumit(10)
check("manumission does not double-count the same person",
      s.artisans - a0 < 5.0, "gained %.1f artisans from 10 people" % (s.artisans - a0))

# --- Han WEIRD / Norse BREAK: slicing dodged the volume surcharge
def spend(slices, per):
    t = sim(capital=1e9)
    # ROOM TO PUT THEM. Buying now respects the same feed/house/oversee cap
    # `hire` always did, so a test about PRICING has to make room first or it
    # is really testing the cap.
    t.done.add("workshop_first")
    t.done.add("freedman_staff")
    t._done_changed()
    c0 = t.capital
    for _ in range(slices):
        t.buy_slaves(per)
    return c0 - t.capital
one, four, twelve = spend(1, 12), spend(4, 3), spend(12, 1)
check("buying in slices costs the same as buying at once",
      max(one, four, twelve) - min(one, four, twelve) < 1.0,
      "%.0f / %.0f / %.0f" % (one, four, twelve))

# --- Rome WEIRD: manumitting untrained people skipped the training lag
s = sim(capital=200000.0)
a0 = s.artisans
s.buy_slaves(10); s.manumit(10)
check("freeing untrained people does not skip the training lag",
      s.artisans - a0 < 0.01, "instant gain %.2f" % (s.artisans - a0))

# --- Han BREAK: why quoted a civilization-blind cost
q = {}
for civ in ("rome_100ad", "han_china_100ad"):
    r, _, _ = proto([{"cmd": "why", "id": "blast_furnace"}], civ=civ)
    q[civ] = r[0]["cost"]["total"]
check("why quotes a civilization-specific cost",
      q["rome_100ad"] != q["han_china_100ad"], str(q))

# --- Han BREAK: starting techs that do not exist were silently dropped
bad = []
for f in sorted(os.listdir(S.CIVDIR)):
    if not f.endswith(".json") or f.startswith("_"):
        continue
    c = json.load(open(os.path.join(S.CIVDIR, f)))
    ids = {x["id"] for x in TREE["nodes"]}
    bad += [t for t in (c.get("starting_techs") or []) if t not in ids]
check("every civilization's starting techs exist", not bad, str(bad))

# --- Han BREAK: one society was granted another's institutions
s = sim(civ="han_china_100ad", manual=False)
for _ in range(2):
    s.step()
foreign = [k for k in s.granted if "_roman" in k or "annona" in k]
check("a society is not granted another society's institutions",
      not foreign, str(foreign[:4]))

# --- Norse WIN: handicap_remedies was never wired
s = sim(civ="norse_900ad")
before = s.civ_cost_factor("blast_furnace")
s.done.add("collegium_licensed")
after = s.civ_cost_factor("blast_furnace")
check("building a remedy lifts the handicap", after < before,
      "%.2f -> %.2f" % (before, after))

# --- Norse WIN: _TECH_EFFECTS was never wired
s = sim()
f0 = s.w["w_magic_fear"]
s.apply_tech_effects("scientific_method")
check("a technology changes the society that built it",
      s.w["w_magic_fear"] < f0, "%.2f -> %.2f" % (f0, s.w["w_magic_fear"]))

# --- Norse WEIRD: abandonment shed a persona and softlocked the run
s = sim(civ="norse_900ad", capital=1000000.0)
s.start_project("identity_cover")
for _ in range(4):
    s.step()
s.buy_slaves(150)
for _ in range(40):
    s.step()
check("bankruptcy never abandons a persona or institution",
      "identity_cover" in s.done, "identity_cover was shed")

# --- Norse BREAK: topping up a mine reset the whole pool's clock
s = sim(capital=5e6)
for _ in range(8):
    s.open_mine("coal", 200)
    s.step()
check("topping up a mine still delivers capacity",
      s.mine_capacity.get("coal", 0) > 0, str(s.mine_capacity))

# --- Norse BREAK: knowledge_risk advertised risk a civ could not face
r, _, _ = proto([{"cmd": "risk"}], civ="norse_900ad")
kr = r[0]["knowledge_risk"]
check("no loss risk is reported where nothing sacks",
      kr["expected_technologies_lost_per_sacking"] == 0.0, str(kr)[:80])

# --- naive BREAK: read-only commands before the first step
r, _, rc = proto([{"cmd": "available"}, {"cmd": "state"}, {"cmd": "help"}])
check("state/available/help work before the first step",
      rc == 0 and all(x.get("ok") for x in r), str(r[:1])[:90])

# --- naive C/A/BREAK: save then restart must not brick the game
import tempfile
sp = os.path.join(tempfile.mkdtemp(), "sess.json")
proto([{"cmd": "state"}], )  # warm
subprocess.run([sys.executable, os.path.join(HERE, "simulator.py"), "agent",
                "--session", sp], input='{"cmd":"state"}\n',
               capture_output=True, text=True, timeout=300, cwd=ROOT)
p2 = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py"), "agent",
                     "--session", sp], input='{"cmd":"state"}\n',
                    capture_output=True, text=True, timeout=300, cwd=ROOT)
check("a saved game reloads without bricking",
      '"ok": true' in p2.stdout, p2.stdout[:90])

# --- naive BREAK: no advanced physics on the first morning
early = {"sc2_physics_nuclear_fission", "sc2_physics_wave_mechanics",
         "el2_sonar_acoustic_detection_ranging", "el2_photomultiplier_single_photon"}
# all:true, because `available` is a digest by default now
r, _, _ = proto([{"cmd": "available", "all": True}])
offered = {a["id"] for a in r[0]["available"]} & early
check("no advanced physics is startable in year one", not offered, str(offered))

# --- naive A: debasement must not make everything cheaper
s = sim()
base = s.cost_money_factor()
s.money_real = 0.005
check("a debased currency does not collapse prices",
      abs(s.cost_money_factor() - base) < 1e-9,
      "%.4f -> %.4f" % (base, s.cost_money_factor()))

# --- reviewer: debt must be bounded and ruin must be recoverable.
#     Two hundred simulated years; the single most expensive check here.
def _ruin_run():
    s = sim(manual=False, capital=1e6)
    s.buy_slaves(400)
    worst = 0.0
    for _ in range(200):
        s.step()
        worst = min(worst, s.capital)
    return s, worst


_RUIN = {}


def _ruin():
    if not _RUIN:
        _RUIN["s"], _RUIN["worst"] = _ruin_run()
    return _RUIN["s"], _RUIN["worst"]


slow_check("debt stays inside a credit limit",
           lambda: (_ruin()[1] > -200000, "worst capital %.0f" % _ruin()[1]))
slow_check("a ruined founder rebuilds rather than freezing",
           lambda: (len(_ruin()[0].done - _ruin()[0].granted) > 200,
                    "earned %d in 200 years"
                    % len(_ruin()[0].done - _ruin()[0].granted)))
slow_check("ruin never deletes a step the goal needs",
           lambda: ("identity_cover" in _ruin()[0].done, ""))

# --- naive B: the game must not buy people on the player's behalf
s = sim(capital=200000.0, manual=True)
for _ in range(40):
    s.step()
check("manual play never buys people for you", s.slaves == 0 and s.freedmen == 0,
      "slaves %d freedmen %d" % (s.slaves, s.freedmen))

# --- naive WEIRD: nothing should repay its whole cost in weeks
pumps = [k for k, n in NODES.items()
         if float(n.get("rev") or 0) > 0 and n["_total_cost"] > 0
         and n["_total_cost"] / float(n["rev"]) < 0.5]
check("no node repays its entire cost in under six months", not pumps,
      "%d pumps, e.g. %s" % (len(pumps), pumps[:3]))

# --- naive WEIRD 7 / Han BREAK 5: a project must actually be PAID for
s = sim(capital=400.0, manual=True)
ok, why = s.start_project("identity_cover")         # 1,580 den against 400
for _ in range(6):
    s.step()
paid = s.active.get("identity_cover", {}).get("spent", 0.0)
check("an unfunded project never completes",
      ok and "identity_cover" not in s.done,
      "started=%s (%s) done=%s paid=%.0f" % (ok, why, "identity_cover" in s.done, paid))

# --- the user: you arrive alone
s = sim()
check("you arrive with no employees and no slaves",
      not s.employees and s.slaves == 0 and s.freedmen == 0 and s.artisans == 0.0,
      "employees %r artisans %.1f" % (s.employees, s.artisans))

# --- the user: a skilled smith is not a skilled writer
s = sim()
ok_hire, err = s.hire("engineer", 1)
check("a trade this society does not have cannot be hired",
      not ok_hire and "no engineer" in (err or "").lower(),
      "hire engineer -> %s / %s" % (ok_hire, err))
s.capital = 20000.0
ok_train, _ = s.train("machinist", 2)
check("you can teach a trade into existence",
      ok_train and "machinist" in s.trades_created and not s.trade_available("chemist"),
      "trained %s created %r" % (ok_train, sorted(s.trades_created)))

# --- the user: hire a job, not a person
s = sim(capital=5000.0)
before = s.capital
ok_job, _ = s.commission("smith", 200)
check("you can buy a job without employing anybody",
      ok_job and not s.employees and s.capital < before,
      "ok %s employees %r" % (ok_job, s.employees))

# --- the user: everything automatic must be switchable
s = sim(manual=False)
check("every automatic behaviour has a switch",
      set(s.policy) >= {"auto_hire", "auto_buy_people", "auto_manumit", "auto_train",
                        "auto_mine", "auto_forest", "auto_mothball", "auto_shed",
                        "auto_bribe"},
      sorted(s.policy))

# --- naive B/C: there must be a way to shed the upkeep of a finished work
s = sim(capital=200000.0)
s.hire("artisan", 2)
s.done.add("fin_pawnshop")
s._done_changed()
# OPEN IT FIRST. Upkeep follows what you RUN, not what you know, so a node
# sitting in `done` has no running cost to stop until you open its doors.
_ok_open, _why_open = s.open_venture("fin_pawnshop")
up_before = s.upkeep()
ok_mb, _ = s.mothball_work("fin_pawnshop")
check("a finished work can be shut down to stop its upkeep",
      _ok_open and ok_mb and up_before > 0 and s.upkeep() < up_before,
      "open %s (%s), upkeep %.0f -> %.0f"
      % (_ok_open, _why_open, up_before, s.upkeep()))
check("shutting a concern down does not make you forget how it worked",
      "fin_pawnshop" in s.done and "fin_pawnshop" not in s.operating,
      "done %s operating %s" % ("fin_pawnshop" in s.done,
                                "fin_pawnshop" in s.operating))

# --- the user: hazards must be answerable with technology
s = sim()
bare, _ = s.hazard_relief("staff_loss")
s.done.add("sanitation_antisepsis")
s.done.add("germ_theory")
better, why = s.hazard_relief("staff_loss")
check("medicine blunts a plague", bare == 1.0 and better < 0.6 and why,
      "%.2f -> %.2f %s" % (bare, better, why))
s2 = sim()
s2.mine_capacity["gold"] = 1.0
gold, _ = s2.hazard_relief("real_erosion")
check("your own gold mine blunts a debasement", gold < 0.5, "%.2f" % gold)

# --- the user: downstream_count is a fog spoiler
p = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py"), "agent",
                    "--civ", "rome_100ad", "--fog"],
                   input='{"cmd":"why","id":"identity_cover"}\n',
                   capture_output=True, text=True, timeout=120, cwd=ROOT)
reply = json.loads([l for l in p.stdout.splitlines() if l.strip()][0])
check("fog hides the exact downstream count",
      reply.get("downstream_count") is None and reply.get("how_much_rests_on_this"),
      "downstream %r band %r" % (reply.get("downstream_count"),
                                 reply.get("how_much_rests_on_this")))

# --- the user: debt bondage is worked off where a society had it, and Rome did not
check("debt bondage follows the society, and is a term of years",
      S.load_civ("rome_100ad").get("debt_bondage") is False
      and S.load_civ("han_china_100ad").get("debt_bondage") is True
      and S.load_civ("han_china_100ad").get("bondage_years", 0) > 0,
      "rome %r han %r" % (S.load_civ("rome_100ad").get("debt_bondage"),
                          S.load_civ("han_china_100ad").get("debt_bondage")))

# --- the user: a reply nobody can read is a reply nobody reads
r, _, _ = proto([{"cmd": "state"}, {"cmd": "available"}, {"cmd": "help"},
                 {"cmd": "labour"}])
sizes = {c: len(json.dumps(x)) for c, x in
         zip(("state", "available", "help", "labour"), r)}
check("no ordinary reply is a wall of text",
      all(v < 6000 for v in sizes.values()), str(sizes))

# a late-game available must not blow up either: it was 165KB at year 250.
# 150 simulated years to get the tree open enough to be worth measuring.
def _late_available():
    s = sim(capital=1e6, manual=False)
    s.fog = True
    for _ in range(150):
        s.step()
    avail = S._agent_available(s, NODES)
    digest = len(json.dumps(avail))
    return (digest < 12000,
            "%d bytes at year %d with %d things startable"
            % (digest, s.year, avail["count"]))


slow_check("available stays a summary as the tree opens up", _late_available)

# --- the menu: a bare invocation must open it, and every civ must be playable
p = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py")],
                   input="q\n", capture_output=True, text=True, timeout=120, cwd=ROOT)
check("a bare invocation opens the menu rather than a usage error",
      p.returncode == 0 and "ONE PERSON" in p.stdout, p.stdout[:80] + p.stderr[:80])

check("the menu offers every civilisation with its lore",
      all(w in p.stdout for w in ("Later Han", "Trajan", "Viking", "Edward I", "Mexica")),
      "missing one of the five")

# `play` was Rome-only and its loop ended at 100+horizon, so any civ that does
# not start in year 100 ended before the player could type anything.
for civ, first_year in (("norse_900ad", "900 AD"), ("mexica_1500", "1500 AD")):
    p = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py"), "play",
                        "--manual", "--civ", civ],
                       input="n\nq\n", capture_output=True, text=True, timeout=120, cwd=ROOT)
    check("play runs a civilisation that does not start in 100 AD (%s)" % civ,
          first_year in p.stdout and "Ended %s" % first_year not in p.stdout,
          p.stdout[-120:])

civ_files = [f for f in os.listdir(os.path.join(ROOT, "rome", "data", "civilizations"))
             if f.endswith(".json") and not f.startswith("_")]
missing_lore = []
for f in civ_files:
    d = json.load(open(os.path.join(ROOT, "rome", "data", "civilizations", f)))
    op = d.get("opening") or {}
    if not all(op.get(k) for k in ("arrival", "what_you_can_see",
                                   "what_is_missing", "what_is_coming")):
        missing_lore.append(d.get("id", f))
check("every civilisation has its opening written", not missing_lore, str(missing_lore))

# --- round two, section M: the robustness batch
r, _, _ = proto([{"cmd": "save", "file": "/etc/should_not_happen.json"},
                 {"cmd": "save", "file": "../../escape.json"},
                 {"cmd": "save", "file": "notasave.txt"}])
check("a save cannot be written outside the game directory",
      all(not x.get("ok") for x in r), str([x.get("ok") for x in r]))
check("/etc was not written to", not os.path.exists("/etc/should_not_happen.json"))

r, _, _ = proto([{"cmd": "step", "years": 100000}, {"cmd": "step", "years": True}])
check("step refuses more years than the game contains", not r[0].get("ok"),
      str(r[0])[:80])
check("step refuses true as a number of years", not r[1].get("ok"), str(r[1])[:80])

r, _, _ = proto([{"cmd": "hire", "trade": "smith", "n": "banana"},
                 {"cmd": "bribe", "amount": "lots"},
                 {"cmd": "state"}])
check("a quantity that is not a number is refused, not defaulted",
      not r[0].get("ok") and not r[1].get("ok") and not r[2].get("employees"),
      str(r[0].get("error"))[:70])

r, _, _ = proto([{"cmd": "quote", "what": "mine", "material": "gold", "n": 1}])
check("a mine can be priced before it is bought",
      r[0].get("ok") and r[0].get("to_sink_it", 0) > 0
      and r[0].get("every_year_it_stands", 0) > 0, str(r[0])[:90])

r, _, _ = proto([{"cmd": "buy", "what": "mine", "material": "coal", "n": 20},
                 {"cmd": "step", "years": 5}, {"cmd": "state"},
                 {"cmd": "close", "material": "coal"}, {"cmd": "state"}])
check("a mine can be closed, and stops costing",
      r[2].get("mine_operating_cost", 0) > 0 and r[4].get("mine_operating_cost") == 0,
      "before %s after %s" % (r[2].get("mine_operating_cost"),
                              r[4].get("mine_operating_cost")))

# --- Mexica WEIRD: the unknown-command message advertised ten commands while
#     the game had twenty-four, so a player who mistyped was handed a list that
#     silently omitted labour, hire, train, money, risk, policy and the rest.
r, _, _ = proto([{"cmd": "definitely_not_a_command"}], civ="mexica_1500")
_advertised = r[0].get("error", "")
_real = [c for c in S.KNOWN_COMMANDS]
check("the unknown-command message advertises every command there is",
      all(c in _advertised for c in _real),
      "missing: %s" % [c for c in _real if c not in _advertised])

# and every command it advertises must actually answer
_dead = []
for _c in _real:
    if _c in ("quit", "save", "load"):
        continue                      # need arguments or end the session
    rr, _, _ = proto([{"cmd": _c}], civ="mexica_1500")
    if rr and "unknown cmd" in str(rr[0].get("error", "")):
        _dead.append(_c)
check("every advertised command is one the game answers to", not _dead, str(_dead))

r, _, _ = proto([{"cmd": "why"}], civ="mexica_1500")
check("a missing id asks for one rather than naming a Python type",
      "NoneType" not in r[0].get("error", "") and "available" in r[0].get("error", ""),
      r[0].get("error", "")[:90])

# --- reproducibility: the same seed must give the same answer, and it must not
#     depend on PYTHONHASHSEED.
#
# This used to shell out to `run --mc 3 --seed 42` twice and compare stdout,
# which is six complete 500-year Monte-Carlo runs and took longer than the
# other seventy-odd checks put together - the whole suite stopped finishing
# inside fifteen minutes and started getting killed. A check nobody can afford
# to run is a check that rots, which is the exact thing this file exists to
# prevent. It also could not pass at all while a second process was editing
# the tree, because then it was comparing two different programs.
#
# Same property, measured directly: run the model in-process over a short
# horizon and compare the state, under two different hash seeds. Set
# explicitly, because Python randomises string hashing per process and three
# separate bugs in this project have come from iterating a set of node ids.
def _det_fingerprint():
    src = """
import sys, random
sys.path.insert(0, %r)
import simulator as S
TREE, PRICES, NODES, WAGES, GOODS = S.load()
GOAL = TREE["meta"]["goal_node"]
_L, ORDER, _B = S.load_strategy("recommended", NODES, GOAL)
out = []
for seed in (42, 43):
    s = S.Sim(NODES, ORDER, random.Random(seed), events=True, manual=False,
              civ=S.load_civ("rome_100ad"))
    s.goal, s.done_year = GOAL, {}
    for _ in range(60):
        s.step()
    out.append("%%d|%%.9f|%%.9f|%%.6f" %% (len(s.done), s.capital, s.revenue(),
                                         s.eminence))
print(";".join(out))
""" % HERE
    seen = set()
    for hashseed in ("0", "12345"):
        env = dict(os.environ, PYTHONHASHSEED=hashseed)
        r = subprocess.run([sys.executable, "-c", src], capture_output=True,
                           text=True, timeout=600, cwd=ROOT, env=env)
        seen.add(r.stdout.strip() or ("ERROR: " + r.stderr[-200:]))
    return seen


def _determinism():
    seen = _det_fingerprint()
    return (len(seen) == 1 and not any(x.startswith("ERROR") for x in seen),
            " || ".join(sorted(seen))[:160])


slow_check("the same seed gives the same result, whatever PYTHONHASHSEED is",
           _determinism)

# --- round 2 A: the setting is Rome wearing a hat -- notes must generalise
_ROME_TEMPLATES = ("ROME ALREADY HAS THIS", "ROME HAS THIS", "ROME POSSIBLY HAS THIS")
bare_rome_notes = [k for k, n in NODES.items()
                    if any(t in (n.get("note") or "") for t in _ROME_TEMPLATES)]
check("no node note bluntly claims 'Rome [already] has this'",
      not bare_rome_notes, str(bare_rome_notes[:5]))

bare_rome_prices = [k for k, v in PRICES["wage_rates_denarii_per_hour"].items()
                     if not k.startswith("_") and isinstance(v, dict)
                     and ("Rome has" in (v.get("note") or "")
                          or "Rome already has" in (v.get("note") or ""))]
check("no wage-rate note bluntly claims 'Rome has these'",
      not bare_rome_prices, str(bare_rome_prices))

check("the cover identity is not named after one civilization's version",
      "Alexandrian" not in NODES["identity_cover"]["name"],
      NODES["identity_cover"]["name"])

# --- round 2 A: institutions Rome already has must cost real work for
# anyone else, and still be free for Rome (via starting_techs, not via a
# zero price tag every civilization can exploit)
_ROMAN_INSTITUTIONS = ["civ_arch_roman", "fin_annona", "fin_argentarii",
                       "fin_collegium", "fin_societas", "hom_cosmetics_roman"]
rome_missing = [k for k in _ROMAN_INSTITUTIONS
                if k not in (S.load_civ("rome_100ad").get("starting_techs") or [])]
check("Rome is granted its own institutions through starting_techs",
      not rome_missing, str(rome_missing))
still_free = [k for k in _ROMAN_INSTITUTIONS if NODES[k]["cap"] == 0 and NODES[k]["ph"] == 0]
check("Rome's institutions are not free for whoever starts them",
      not still_free, str(still_free))
s = sim(civ="norse_900ad")
norse_has_them_free = [k for k in _ROMAN_INSTITUTIONS if k in s.done]
check("a Norse founder is not handed Rome's institutions for nothing",
      not norse_has_them_free, str(norse_has_them_free))

# --- round 2 A: geography-locked agriculture must not be startable
# anywhere on earth
s = sim(civ="norse_900ad")
ok_chinampa = s.can_start("fud_chinampa")
check("chinampa agriculture is not startable in Norway",
      not ok_chinampa)
s = sim(civ="mexica_1500")
check("chinampa agriculture is still free for the Mexica",
      "fud_chinampa" in s.done)

# --- round 2 B: anachronism is gated by nothing much
s = sim(civ="rome_100ad")
_ANACHRONISMS = ["mil_chemical_mustard", "mil_trace_italienne", "mil_general_staff",
                 "mil_conscription_reserve", "mil_trench", "hot_air_balloon",
                 "mil_observation_balloon", "mil_gunpowder_base"]
startable_turn_one = [k for k in _ANACHRONISMS if s.can_start(k)]
check("no anachronistic weapon or doctrine is startable turn one",
      not startable_turn_one, str(startable_turn_one))
check("mustard gas needs industrial chlorine and a delivery shell",
      set(["mat_chlorine", "mil_artillery_shell"]) <= set(NODES["mil_chemical_mustard"]["pre"]),
      str(NODES["mil_chemical_mustard"]["pre"]))
check("trace italienne fortification answers an actual cannon",
      "mil_artillery_piece" in NODES["mil_trace_italienne"]["pre"],
      str(NODES["mil_trace_italienne"]["pre"]))
check("a trench answers an actual machine gun and shellfire",
      set(["mil_machine_gun_recoil", "mil_artillery_shell"]) <= set(NODES["mil_trench"]["pre"]),
      str(NODES["mil_trench"]["pre"]))
check("gunpowder claims no saltpetre it has not earned via nitre_beds",
      "nitre_beds" in NODES["mil_gunpowder_base"]["pre"],
      str(NODES["mil_gunpowder_base"]["pre"]))

# --- round 2 G: five centuries, two events -- Norse hazards must do something
norse_hazards = S.load_civ("norse_900ad")["hazards"]
check("the Norse civilization has more than one dated hazard",
      len(norse_hazards) > 1, "only %d" % len(norse_hazards))
_EFFECT_FIELDS = ("staff_loss", "sack_chance", "output_factor", "real_erosion")
inert = [h["name"] for h in norse_hazards if not any(f in h for f in _EFFECT_FIELDS)]
check("no Norse hazard is purely decorative (no effect field the engine reads)",
      not inert, str(inert))

# ============================================================================
# Round two, sections C-F: knowledge vs plant, the automatic policies, warning
# a player before they commit to work nobody can do, and legible hours.
# ============================================================================
import time as _time

# --- C: knowledge is not a building. A tester watched creditors make the
# founder forget Newton's laws and basic textile technique. "physics" was
# already protected; "theory" and "knowledge" (what the tree itself calls the
# rest of abstract science) were not, even though several of those nodes carry
# real upkeep the same way Newton's laws does. A loss-making node that is
# neither is the control: it SHOULD still be shed.
_KNOW1, _KNOW2, _LOSS = "md2_cell_theory", "md2_dna", "hom_eraser_breadcrumb"
s = sim()
check("theory and knowledge categories are protected the same way physics is",
      s.never_abandon(_KNOW1) and s.never_abandon("sc2_physics_newtons_laws"),
      "%s cat=%s" % (_KNOW1, NODES[_KNOW1]["cat"]))
check("a loss-making, non-knowledge node is NOT protected (the control case)",
      not s.never_abandon(_LOSS), NODES[_LOSS]["cat"])

s = sim(capital=-100000.0)
s.done.add(_LOSS); s.done.add(_KNOW1)
s._done_changed()
# IT HAS TO BE OPEN TO BE WORTH CLOSING. Upkeep follows `operating`, so a
# concern already shut is already costing nothing; shedding it saves nothing
# and would only destroy what you know. shed_loss_makers scanned `done` and
# did exactly that.
s.operating.add(_LOSS); s.operating.add(_KNOW1)
s.revenue = lambda: 0.0        # force a loss regardless of the rest of the economy
s.shed_loss_makers(100)
check("shed_loss_makers closes a loss-making concern, and spares knowledge",
      _LOSS not in s.operating and _KNOW1 in s.operating,
      "loss-maker closed=%s knowledge closed=%s"
      % (_LOSS not in s.operating, _KNOW1 not in s.operating))
check("...and what it closed is still something you know how to do",
      _LOSS in s.done and _KNOW1 in s.done,
      "still known: %s %s" % (_LOSS in s.done, _KNOW1 in s.done))
check("shed_loss_makers mothballs, and NAMES, what it takes",
      _LOSS in s.mothballed and any(_LOSS in m for _, m in s.log),
      [m for _, m in s.log])
# The control: a loss-maker that is SHUT is left alone entirely.
s_sh = sim(capital=-100000.0)
s_sh.done.add(_LOSS); s_sh._done_changed()
s_sh.revenue = lambda: 0.0
s_sh.shed_loss_makers(100)
check("a loss-maker that is already shut is not unlearned to no purpose",
      _LOSS in s_sh.done and _LOSS not in s_sh.mothballed,
      "known=%s mothballed=%s" % (_LOSS in s_sh.done, _LOSS in s_sh.mothballed))

s = sim(capital=-100000.0)
s.done.add(_LOSS); s.done.add(_KNOW2)
s._done_changed()
# A creditor seizes a CONCERN, not a memory, so it has to be open to be taken.
s.operating.add(_LOSS); s.operating.add(_KNOW2)
s.credit_limit = lambda: 0.0   # force straight past the credit floor
s.enforce_credit_limit(100)
# NOW ABOUT WHAT IS RUNNING, not about what is known. Creditors close and sell
# up a concern; they cannot take away your memory of how it worked, which is
# also why a weird-play tester could reach a state where a node was
# simultaneously forgotten and running and no verb would touch it.
check("creditors close a loss-making concern and cannot touch knowledge",
      _LOSS not in s.operating and _KNOW2 in s.operating,
      "loss-maker closed=%s knowledge closed=%s"
      % (_LOSS not in s.operating, _KNOW2 not in s.operating))
check("a concern the creditors took is still a thing you know how to do",
      _LOSS in s.done,
      "still known: %s" % (_LOSS in s.done))
check("creditors' seizure mothballs, and NAMES, what it takes",
      _LOSS in s.mothballed and any(_LOSS in m for _, m in s.log),
      [m for _, m in s.log])

# --- C: a repossessed work must not look like fresh research
s = sim(capital=100000.0)
s.done.add(_LOSS); s._done_changed()      # you BUILT it; that is what mothballing means
s.mothballed.add(_LOSS)
ok, why = s.start_reason(_LOSS)
check("a mothballed work refuses to be started as if it were new research",
      not ok and "restore" in why, why)
avail = S._agent_available(s, NODES, {"all": True})
check("a mothballed work does not appear in available looking like new research",
      not any(e["id"] == _LOSS for e in avail["available"]), avail["count"])

# --- ROUND 8: THE DEADLOCK. A play tester lost precision_three_plate to a
# third-century sack and could not get it back by any verb: `start` sent them
# to `restore`, `restore` said they no longer knew how, `open` said they had
# not built it, `mothball` said there was nothing to shut. That node gates the
# whole precision branch, so `available` read "0 startable now" for a hundred
# and eighty years while they held a quarter of a billion denarii.
s_dl = sim(capital=100000.0)
s_dl.mothballed.add(_LOSS)                # mothballed, and NOT known: the trap
ok_dl, why_dl = s_dl.start_reason(_LOSS)
check("a work whose knowledge was destroyed can be built again",
      ok_dl, why_dl)
ok_rs, why_rs = s_dl.restore_work(_LOSS)
check("...and restore says to build it, not that it cannot be restored",
      not ok_rs and "start" in why_rs, why_rs)
_av_dl = S._agent_available(s_dl, NODES, {"all": True})
check("...and it is visible in available, not hidden behind a stale mothball",
      any(e["id"] == _LOSS for e in _av_dl["available"]), _av_dl["count"])
s_dl.start_project(_LOSS)
check("...and starting it clears the stale mothball entry",
      _LOSS not in s_dl.mothballed and _LOSS in s_dl.active,
      (_LOSS in s_dl.mothballed, _LOSS in s_dl.active))

# The path that created it: insolvency abandonment discarded from `done` AND
# added to `mothballed`, the same pair of lines already fixed twice elsewhere.
s_ab = sim(capital=-100000.0)
s_ab.done.add(_LOSS); s_ab._done_changed()
s_ab.operating.add(_LOSS)
s_ab.revenue = lambda: 0.0
for _ in range(6):
    s_ab.step()
check("no path in the engine leaves a work mothballed but unknown",
      not (s_ab.mothballed - s_ab.done),
      sorted(s_ab.mothballed - s_ab.done)[:4])

# --- D1: auto_hire must not take on staff this year's income cannot carry
s = sim(civ="rome_100ad", capital=400.0, manual=False, events=False)
s.step()
check("auto_hire does not overcommit turn one against a thin surplus",
      s.scholars < 0.2 and s.artisans < 0.6,
      "scholars %.3f artisans %.3f capital %.1f" % (s.scholars, s.artisans, s.capital))

# --- D2/E: auto_train (and a `start` warning) must be demand-led: driven by
# what is startable now but for the trade, not by every node whose direct
# prerequisites happen to be satisfied somewhere deep in the tree.
s = sim(civ="rome_100ad", capital=1e6, manual=True, events=False)
ok_ig, why_ig = s.start_reason("ag2_hydrometer", ignore_trade=True)
check("ignore_trade accepts a node that is startable but for the trade alone",
      ok_ig, why_ig)
ok_norm, why_norm = s.start_reason("ag2_hydrometer")
check("without ignore_trade the same node is refused specifically for the trade",
      not ok_norm and "optician" in why_norm, why_norm)
ok_staff, why_staff = s.start_reason("ag2_cold_store", ignore_trade=True)
check("ignore_trade still refuses a node blocked by missing STAFF, not just the trade",
      not ok_staff and "craftsmen" in why_staff, why_staff)

s = sim(civ="rome_100ad", capital=1e6, manual=True, events=False)
node = "ag2_cold_store"
for p in NODES[node]["pre"]:
    s.done.add(p)
s.artisans, s.scholars = 10.0, 10.0
r0 = S._agent_dispatch(s, NODES, {"cmd": "start", "id": node})
check("start refuses outright when a needed trade has never been taught",
      not r0["ok"] and "engineer" in r0.get("error", ""), r0)
s.train("engineer", 2)          # training begun; nobody is ready for two years
r1 = S._agent_dispatch(s, NODES, {"cmd": "start", "id": node})
check("start accepts work nobody can do yet only WITH a warning naming the trade",
      r1["ok"] and "engineer" in r1.get("warning", ""), r1)

# --- D4: fractional staff counts are explained, not silently shown
s = sim(civ="rome_100ad", capital=400.0, manual=False, events=False)
s.step()
st = S._agent_state(s, NODES, {})
check("a fractional staff count comes with an explanation of what the fraction means",
      (abs(s.scholars - round(s.scholars)) < 0.02 and abs(s.artisans - round(s.artisans)) < 0.02)
      or bool(st.get("staff_are_fractional_because")),
      "scholars %.3f artisans %.3f" % (s.scholars, s.artisans))
s2 = sim(civ="rome_100ad")
st2 = S._agent_state(s2, NODES, {})
check("a whole-number staff carries no fraction footnote",
      st2.get("staff_are_fractional_because") is None, st2.get("staff_are_fractional_because"))

# --- F: say how the founder's hours were spent
s = sim(civ="rome_100ad", capital=400.0, manual=False, events=False)
ratios = []
for _ in range(6):
    s.step()
    h = s.hours_this_year
    total = h["wage_work"] + h["teaching"] + h["offered_to_projects"] + h["unused"]
    check("a year's founder hours are fully accounted for (year %d)" % s.year,
          abs(total - h["available"]) < 1e-6, h)
    for k, pst in s.active.items():
        off = pst.get("hours_offered_this_year", 0.0)
        eff = pst.get("hours_effective_this_year", 0.0)
        if off > 1:
            ratios.append(eff / off)
check("an underfunded project's refund is proportional, not always exactly half",
      any(abs(r - 0.5) > 0.02 for r in ratios), ratios)
st = S._agent_state(s, NODES, {})
check("state reports the year's hours summary",
      st.get("hours_this_year") == s.hours_this_year, st.get("hours_this_year"))
check("state reports hours offered/effective per active project",
      not st["active"] or any("hours_offered_this_year" in v for v in st["active"].values()),
      st["active"])

# --- performance: `available` must return quickly even deep in the tree under
# fog. A regression here (start_reason recursing into is_visible, which
# recurses into start_reason, unmemoised) took a single `available` call under
# fog on norse_900ad from instant to over a minute.
s = sim(civ="norse_900ad")
s.fog = True
s.revealed = set()
t0 = _time.time()
S._agent_available(s, NODES, {})
elapsed = _time.time() - t0
check("available returns quickly under fog, not in tens of seconds",
      elapsed < 5.0, "%.2fs" % elapsed)

# ============================================================================
# Round two, section P: a hazard can carry a `values` delta, the same way a
# technology does, and it must land gradually and be visible while it is
# happening. Norse Christianisation (995-1100) is the case in point: it now
# carries a `values` block in the civ file instead of the ENGINE TODO note
# that used to stand in for it.
# ============================================================================

_christ = next(h for h in S.load_civ("norse_900ad")["hazards"]
              if h["name"].startswith("Christianisation"))
check("Christianisation now carries a values delta, not just a TODO note",
      bool(_christ.get("values")), _christ.get("values"))

# --- gradual, not a single jump: one year of a 106-year hazard should move
# the needle by roughly a hundredth of the total, not all of it at once.
s = sim(civ="norse_900ad")
before = dict(s.w)
s._shocks(995)
step1 = s.w["w_religious_rigidity"] - before["w_religious_rigidity"]
total_asked = _christ["values"]["w_religious_rigidity"]
check("a hazard's values shift lands gradually: one year moves it a fraction "
      "of the total, not the whole amount",
      0 < step1 < total_asked * 0.5, "%.4f of %.2f" % (step1, total_asked))

# --- and by the hazard's last year the FULL delta has landed, spread evenly
# across every year in between (995 already applied above; finish the span).
for yr in range(996, 1101):
    s._shocks(yr)
total_moved = s.w["w_religious_rigidity"] - before["w_religious_rigidity"]
check("a hazard's values shift reaches its full stated amount across the "
      "full span of years",
      abs(total_moved - total_asked) < 1e-6,
      "%.6f vs %.2f asked" % (total_moved, total_asked))

# --- visible WHILE it happens: the society turning against the player has to
# show up in the log more than once, and not only at the first or last year,
# or a player has no way to see it coming except by reading the future.
shift_years = [y for y, msg in s.log if "values are shifting" in msg]
check("a values shift is logged more than once while the hazard is running, "
      "not only as a single note",
      len(shift_years) >= 3, shift_years)
check("some of those log lines land mid-hazard, not only at the first or "
      "last year",
      any(995 < y < 1100 for y in shift_years), shift_years)

# --- a hazard with no staff_loss/sack_chance/output_factor/real_erosion at
# all, only `values`, must still be applied (the mechanism must not be
# piggy-backing on one of the four old fields being present).
s2 = sim(civ="norse_900ad")
s2.civ = dict(s2.civ)
s2.civ["hazards"] = [{"name": "values-only test hazard",
                      "values": {"w_novelty": -0.2}, "years": [900, 909]}]
s2.w = s2.civ["values"] = dict(s2.w)
f0 = s2.w["w_novelty"]
for yr in range(900, 910):
    s2._shocks(yr)
check("a hazard that carries ONLY a values delta (no staff_loss, sack_chance, "
      "output_factor or real_erosion) still moves the society",
      abs(s2.w["w_novelty"] - (f0 - 0.2)) < 1e-6,
      "%.4f -> %.4f" % (f0, s2.w["w_novelty"]))

# --- foreseeable, not just felt: knowledge_risk must let a player see the
# shift coming before it starts, the same complaint that section G raised
# about Christianisation producing "no event and no visible consequence".
r, _, _ = proto([{"cmd": "risk"}], civ="norse_900ad")
kr = r[0]["knowledge_risk"]
christ_row = next((h for h in kr["known_hazards_ahead"]
                   if h["name"].startswith("Christianisation")), None)
check("knowledge_risk lists Christianisation among the hazards ahead, "
      "before it starts",
      christ_row is not None, kr.get("known_hazards_ahead"))
check("knowledge_risk's note on Christianisation says what it does to the "
      "society, not only what it does to output",
      christ_row is not None and "values" in christ_row.get("note", "").lower(),
      christ_row and christ_row.get("note"))

# --- the "Norse cannot be sacked" finding this mechanism must not disturb:
# a values shift is not a sack, and Christianisation still has none of the
# sack_chance fields that would make it one.
check("Christianisation still carries no sack_chance (a values shift is not "
      "a sacking, and Norse assembly society still has no capital to sack)",
      "sack_chance" not in _christ, _christ)

# ============================================================================
# Section S: three nodes the machine list was missing. Honest prerequisites
# matter more than the node existing at all, especially for the LED, which
# is not a light bulb.
# ============================================================================

check("the light-emitting diode exists and sits behind a real semiconductor "
      "diode, not the lighting branch",
      "com_led" in NODES and "com_semiconductor_diode" in NODES["com_led"]["pre"],
      NODES.get("com_led", {}).get("pre"))
check("the LED needs the same purity/single-crystal semiconductor lineage a "
      "diode needs, not a shortcut around it",
      "com_led" in NODES and "junction_transistor" in S.closure(NODES, "com_led"),
      None)

check("the clothes dryer exists as its own node, distinct from the washing "
      "machine it builds on",
      "hom_clothes_dryer_electric" in NODES
      and NODES["hom_clothes_dryer_electric"]["id"] != "hom_washing_machine_electric"
      and "hom_washing_machine_electric" in NODES["hom_clothes_dryer_electric"]["pre"],
      NODES.get("hom_clothes_dryer_electric", {}).get("pre"))

check("the domestic freezer exists as its own node, distinct from the "
      "refrigerator it builds on",
      "hom_freezer_domestic" in NODES
      and NODES["hom_freezer_domestic"]["id"] != "hom_refrigerator_home_electric"
      and "hom_refrigerator_home_electric" in NODES["hom_freezer_domestic"]["pre"],
      NODES.get("hom_freezer_domestic", {}).get("pre"))
# New work: a human-readable rendering (--pretty), the menu starting the game
# instead of describing how to, and `load` refusing a file that is not a
# save from this game.
# ============================================================================

def _run_agent(input_lines, extra_args=(), civ="rome_100ad", cwd=None):
    """Drive the real `agent` subcommand in a real subprocess, optionally with
    extra CLI flags (--pretty among them). Returns (stdout, stderr, returncode)."""
    cmd = [sys.executable, os.path.join(HERE, "simulator.py"), "agent", "--civ", civ] + list(extra_args)
    p = subprocess.run(cmd, input="\n".join(json.dumps(c) for c in input_lines) + "\n",
                       capture_output=True, text=True, timeout=300, cwd=(cwd or ROOT))
    return p.stdout, p.stderr, p.returncode


_PRETTY_CMDS = [
    {"cmd": "state"}, {"cmd": "available"}, {"cmd": "why", "id": "blast_furnace"},
    {"cmd": "money"}, {"cmd": "labour"}, {"cmd": "risk"},
    {"cmd": "step", "years": 1}, {"cmd": "hire", "trade": "smith", "n": 1},
    {"cmd": "quit"},
]

# --- I/N: the one guarantee the whole feature rests on. A script that only
# ever reads stdout must not be able to tell --pretty was even passed.
_out_plain, _err_plain, _rc_plain = _run_agent(_PRETTY_CMDS)
_out_pretty, _err_pretty, _rc_pretty = _run_agent(_PRETTY_CMDS, extra_args=["--pretty"])
_first_diff = next((i for i in range(min(len(_out_plain), len(_out_pretty)))
                    if _out_plain[i] != _out_pretty[i]), None)
check("stdout is byte-for-byte identical whether or not --pretty is passed",
      _rc_plain == 0 and _rc_pretty == 0 and _out_plain == _out_pretty,
      "plain %d bytes, pretty %d bytes, first differs at %s"
      % (len(_out_plain), len(_out_pretty), _first_diff))

_bad_lines = []
for _ln in _out_pretty.splitlines():
    try:
        json.loads(_ln)
    except ValueError:
        _bad_lines.append(_ln)
check("with --pretty on, every stdout line is still exactly one JSON object",
      not _bad_lines, _bad_lines[:3])

# --- N: the rendering actually renders something recognisable for each of
# state/available/why/money/labour/risk, and stays silent on stderr when
# nobody asked for it.
check("--pretty renders state as a position, to stderr",
      "YEAR" in _err_pretty and "RUNNING" in _err_pretty and "EMPLOY" in _err_pretty,
      _err_pretty[:200])
check("--pretty renders available as a table, to stderr",
      "AVAILABLE" in _err_pretty and "COST" in _err_pretty, "")
check("--pretty renders why as a page about one thing, to stderr",
      "COST:" in _err_pretty and "STATUS:" in _err_pretty, "")
check("--pretty renders money as a ledger, to stderr",
      "LEDGER" in _err_pretty, "")
check("--pretty renders labour readably, to stderr",
      "ON YOUR STAFF" in _err_pretty, "")
check("--pretty never mixes a Python dict repr into the risk rendering",
      "{'" not in _err_pretty, [l for l in _err_pretty.splitlines() if "{'" in l])
check("why does not print the missing-prerequisites list twice",
      _err_pretty.count("bellows_water_blown") <= 1 or "MISSING PREREQUISITES" not in _err_pretty,
      [l for l in _err_pretty.splitlines() if "bellows_water_blown" in l])
check("without --pretty, stderr carries no rendered reply (only the welcome banner)",
      "RUNNING (" not in _err_plain and "LEDGER" not in _err_plain, _err_plain[:200])

_out_kit, _err_kit, _ = _run_agent([{"cmd": "state"}, {"cmd": "quit"}],
                                   extra_args=["--pretty", "--kit", "equestrian"])
check("large numbers in the pretty rendering carry thousands separators",
      "100,000" in _err_kit or "100,000" in _err_kit.replace(",", "", 0), _err_kit[:300])

# --- 2: the menu ends by starting the game, not by printing a command line
# and asking permission to run it. It must also honour the mortality choice
# made in the menu, which `agent` never had a flag for at all before this.
_menu_dir = tempfile.mkdtemp()
# THE MENU NOW DROPS INTO `play`, NOT `agent`. It used to hand a person a JSON
# prompt, which is the right front end for a script and the wrong one for the
# human the menu exists to greet; `play` speaks typed words over the same
# dispatcher. So the commands fed here are typed, and what comes back is the
# rendered view rather than JSON.
_menu_input = "1\ny\n\ny\nstate\nquit\n"
_pm = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py")],
                     input=_menu_input, capture_output=True, text=True, timeout=120,
                     cwd=_menu_dir)
check("the menu says it is starting, not offering a command to run later",
      "Starting now" in _pm.stdout, _pm.stdout[-500:])
check("the menu names a resumable --session file ending in .json",
      "--session" in _pm.stdout and ".json" in _pm.stdout, _pm.stdout[-500:])
# Saves live in ~/.rome-saves now, not beside the source: eighty-nine of them
# had piled up in the repository root and a play tester said so.
_save_dir = os.path.join(os.path.expanduser("~"), ".rome-saves")
check("saves are written somewhere of their own, not beside the source",
      os.path.isdir(_save_dir)
      and not [f for f in os.listdir(_menu_dir) if f.endswith(".json")],
      _save_dir)
_saved = ([f for f in os.listdir(_save_dir) if f.endswith(".json")]
          if os.path.isdir(_save_dir) else [])
# The one this run chose, by name out of the banner, rather than "exactly one
# file in the directory" - the save directory is the user's and keeps every
# game they have played.
_named = [ln.split("--session")[1].strip()
          for ln in _pm.stdout.splitlines() if "--session" in ln]
check("the menu's chosen session file actually exists on disk after playing",
      _named and os.path.exists(_named[0]), (_named[:1], len(_saved)))
check("the menu drops straight into a playable session, no extra prompt",
      _pm.returncode == 0 and "YEAR" in _pm.stdout and "RUNNING" in _pm.stdout,
      _pm.stdout[-300:])
check("the mortality choice made in the menu reaches the actual game",
      "and ageing" in _pm.stdout, _pm.stdout[-300:])
# --- the user: "I wanted agents to play under the play that we were just
# making". Everything built since the split went into the JSON protocol only,
# and `play` still understood six commands of its own. It must now reach the
# whole game, in typed words, and it must never answer a person in JSON.
_PLAY_DIR = "_playtest_tmp"
os.makedirs(os.path.join(ROOT, _PLAY_DIR), exist_ok=True)


def _play(lines, civ=None, extra=()):
    p_ = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py"), "play"]
                        + (["--civ", civ] if civ else []) + list(extra),
                        input="".join(l + "\n" for l in lines),
                        capture_output=True, text=True, timeout=240, cwd=ROOT)
    # BOTH STREAMS. A refusal printed on stderr is still a refusal the player
    # sees, and a check that reads only stdout silently passes a game that
    # started the wrong civilisation over the top of a save.
    return p_.stdout + p_.stderr, p_.returncode


_pl, _rc = _play(["state", "money", "labour", "risk", "policy", "available",
                  "hire smith 1", "step 1", "quit"])
check("typed play reaches the whole game, not six commands of its own",
      all(t in _pl for t in ("YEAR", "LEDGER", "ON YOUR STAFF", "AVAILABLE")) and _rc == 0,
      [t for t in ("YEAR", "LEDGER", "ON YOUR STAFF", "AVAILABLE") if t not in _pl])
check("typed play never answers a person in JSON",
      '{"cmd"' not in _pl, [l for l in _pl.splitlines() if '{"cmd"' in l][:3])
_pl2, _ = _play(["available metallurgy", "quit"])
check("a typed narrowing of available works as the reply advertises it",
      "AVAILABLE" in _pl2 and "metallurgy" in _pl2.lower(), _pl2[:200])
_pl3, _ = _play(["frobnicate", "state", "quit"])
check("an unknown typed word is refused without ending the session",
      "no command called" in _pl3 and "YEAR" in _pl3, _pl3[:300])
_sess = "%s/typed.json" % _PLAY_DIR
# START FROM NOTHING. The first version of this check left its save behind, so
# the NEXT run of the suite resumed it and stepped three more years: it passed
# once and failed for ever after, on state left by itself.
if os.path.exists(os.path.join(ROOT, _sess)):
    os.remove(os.path.join(ROOT, _sess))
# --civ on the FIRST call, because that is the call that creates the game; the
# resume below deliberately omits it, which is the whole point of the check.
_pl4, _ = _play(["step 3", "quit"], civ="rome_100ad", extra=["--session", _sess])
_pl5, _ = _play(["state", "quit"], extra=["--session", _sess])
check("a typed game can be stopped and resumed from its own save file",
      "Resumed from" in _pl5 and "YEAR 103" in _pl5, _pl5[:300])
_pl6, _rc6 = _play(["state"])       # stdin ends without 'quit'
check("running out of input ends a typed game cleanly, not on a traceback",
      _rc6 == 0 and "Traceback" not in _pl6, _pl6[-200:])

# --- 3: `load` validates the file before touching the running game. `save`
# and `load` both refuse an absolute path (see the robustness checks above),
# so every file here lives in a relative scratch directory under ROOT, the
# same place a real player's save would land.
import shutil as _shutil
_LOADTEST_DIR = "_loadtest_tmp"
_loadtest_abs = os.path.join(ROOT, _LOADTEST_DIR)
os.makedirs(_loadtest_abs, exist_ok=True)


def _rel(name):
    return "%s/%s" % (_LOADTEST_DIR, name)


_good, _, _ = proto([{"cmd": "step", "years": 1}, {"cmd": "save", "file": _rel("sess.json")}])
check("a legitimate save from this game loads cleanly",
      _good[-1].get("ok") is True, _good[-1])

_bad_saves = {
    "not an object at all": "[1, 2, 3]",
    "an unrelated JSON object": json.dumps({"hello": "world"}),
    "missing required fields": json.dumps({"year": 100, "capital": 400}),
}
for _i, (_label, _content) in enumerate(_bad_saves.items()):
    _name = "bad%d.json" % _i
    open(os.path.join(_loadtest_abs, _name), "w").write(_content)
    _r, _, _ = proto([{"cmd": "state"}, {"cmd": "load", "file": _rel(_name)}, {"cmd": "state"}])
    ok_before, resp, ok_after = _r[0], _r[1], _r[2]
    check("load refuses %s with a clear message, not a crash" % _label,
          resp.get("ok") is False and "Traceback" not in resp.get("error", "")
          and len(resp.get("error", "")) < 400,
          resp)
    check("a refused load (%s) leaves the running game untouched" % _label,
          ok_before.get("year") == ok_after.get("year")
          and ok_before.get("capital") == ok_after.get("capital"),
          (ok_before.get("year"), ok_after.get("year")))

# a save for a civilisation other than the one currently running
_r, _, _ = proto([{"cmd": "save", "file": _rel("norse.json")}], civ="norse_900ad")
_r2, _, _ = proto([{"cmd": "load", "file": _rel("norse.json")}], civ="rome_100ad")
check("load refuses a save from a different civilisation",
      _r2[0].get("ok") is False and "civilisation" in _r2[0].get("error", ""), _r2[0])

# a save that refers to a node id the current tree does not have
_blob = json.load(open(os.path.join(_loadtest_abs, "sess.json")))
_blob["done"]["__set__"].append("this_node_does_not_exist_anymore")
json.dump(_blob, open(os.path.join(_loadtest_abs, "unknown_node.json"), "w"))
_r3, _, _ = proto([{"cmd": "state"}, {"cmd": "load", "file": _rel("unknown_node.json")}, {"cmd": "state"}])
check("load refuses a save that refers to a node the tree no longer has",
      _r3[1].get("ok") is False and "this_node_does_not_exist_anymore" in _r3[1].get("error", ""),
      _r3[1])
check("that refusal leaves the running game untouched too",
      _r3[0].get("year") == _r3[2].get("year"), (_r3[0].get("year"), _r3[2].get("year")))

# --- the Mexica break tester, six findings, one check each ------------------
# Every one of these was reproduced from the tester's own transcript before it
# was fixed; each check is the tester's repro, kept.

# 1. `work` earned wages as a chemist in a society whose `hire` and `labour`
#    both said chemists do not exist there.
_wk, _, _ = proto([{"cmd": "hire", "trade": "chemist", "n": 1},
                   {"cmd": "work", "trade": "chemist", "hours": 10},
                   {"cmd": "work", "trade": "scribe", "hours": 10}])
check("you cannot be paid for a trade this society does not have",
      _wk[0].get("ok") is False and _wk[1].get("ok") is False
      and _wk[2].get("ok") is True,
      [r.get("ok") for r in _wk])

# 2. Staff force-fired to zero with credit still to spare, and nothing logged.
# The tester's exact condition: staff on the books, capital NEGATIVE but only a
# third of the way into a credit line nobody has withdrawn. A household with
# credit left borrows and makes payroll; that is what credit is for.
# (a) A payroll the remaining credit COVERS costs you nobody but attrition.
s = sim(capital=6000.0)
s.policy["auto_hire"] = False
s.hire("smith", 2)
s.capital = -s.credit_limit() * 0.35
_before = sum(s.employees.values())
_room = s.capital + s.credit_limit() - (s.living_cost() - s.wage_bill())
s.step()
_after = sum(s.employees.values())
check("staff are not let go while there is still credit to pay them",
      _room > 0 and _after > _before * 0.95,
      "%.2f -> %.2f with %.0f still to spend against a %.0f payroll"
      % (_before, _after, _room, s.wage_bill()))

# (b) A payroll it only PARTLY covers costs you part of the staff, not all of
#     it. The tester's five went to zero in one step with two thirds of the
#     credit line untouched; what should happen is that you keep as many as
#     your remaining means will pay for.
s = sim(capital=6000.0)
s.policy["auto_hire"] = False
s.hire("smith", 5)
s.capital = -s.credit_limit() * 0.35
_b3 = sum(s.employees.values())
s.step()
check("an unaffordable payroll is trimmed to what you can pay, not emptied",
      0.5 < sum(s.employees.values()) < _b3,
      "%.2f -> %.2f" % (_b3, sum(s.employees.values())))

# ...and when they DO go, because there is genuinely no money left to borrow,
# it is said. The old code logged only in the branch that never happened.
s = sim(capital=6000.0)
s.policy["auto_hire"] = False
s.hire("smith", 5)
s.capital = -s.credit_limit() * 1.5
_b2 = sum(s.employees.values())
s.step()
check("losing staff you cannot pay is written in the log, never silent",
      sum(s.employees.values()) < _b2
      and any("cannot pay everyone" in m for _y, m in s.log),
      "%.2f -> %.2f, log %r" % (_b2, sum(s.employees.values()), s.log[-3:]))

# 3. state.living_cost was living_and_appearances PLUS the whole payroll, while
#    `money` reported the two separately, to the decimal.
_lc, _, _ = proto([{"cmd": "hire", "trade": "smith", "n": 3},
                   {"cmd": "state"}, {"cmd": "money"}])
_st, _mo = _lc[1], _lc[2]
_costs = (_mo.get("what_it_costs_you") or {})
check("state and money do not label the same money two different ways",
      abs(_st.get("living_cost", 0) - _costs.get("living_and_appearances", -1)) < 0.15
      and abs(_st.get("wage_bill", 0) - _costs.get("wages", -1)) < 0.15,
      "state %r / money %r" % ({k: _st.get(k) for k in ("living_cost", "wage_bill")},
                               {k: _costs.get(k) for k in ("living_and_appearances", "wages")}))

# 4. `path` under fog said "you have not discovered this" about a technology
#    the same session reported as done.
_pa, _, _ = proto([{"cmd": "path", "id": "identity_cover"}], fog=True)
check("path under fog gives the real reason, not a false one about discovery",
      _pa[0].get("ok") is False and "not been" in (_pa[0].get("error") or "")
      and "have not discovered" not in (_pa[0].get("error") or ""),
      _pa[0].get("error"))

# 5. The unknown-command hint named 10 of 27 real commands. (Fixed earlier;
#    kept because a hand-maintained list drifts again the moment one is added.)
_uc, _, _ = proto([{"cmd": "frobnicate"}])
check("the unknown-command hint names every command there is",
      all(c in (_uc[0].get("error") or "") for c in S.KNOWN_COMMANDS if c != "quit"),
      [c for c in S.KNOWN_COMMANDS if c not in (_uc[0].get("error") or "")])

# 6. 0.999 years was refused and 1.99 was silently floored to one.
_fy, _, _ = proto([{"cmd": "step", "years": 1.99}, {"cmd": "step", "years": 2}])
check("a fractional number of years is refused, not silently rounded",
      _fy[0].get("ok") is False and _fy[1].get("ok") is True,
      [r.get("ok") or r.get("error") for r in _fy])

# --- the Mexica play tester: a project's own accounting -----------------------
# Their three findings, each with the condition that produced it. All three need
# the SAME year to be short of a trade AND short of money, which is why none of
# them showed up in an ordinary run.


def _starved(cost_left, supply=0.02, arrears=0.9, capital=20000.0):
    """One project that cannot finish, in a year that is short of both the
    trade it needs and the money to pay for it."""
    s = sim(capital=capital)
    s.start_project("identity_cover")
    s.active["identity_cover"]["cost_left"] = cost_left
    _real = s.market_supply
    s.market_supply = lambda t, _r=_real: _r(t) * supply
    s.capital = -s.credit_limit() * arrears      # in arrears, inside the limit
    return s


# 1. Hours could be refunded twice - once for the trade shortage and again for
#    the money - and both refunds were worked out from the hours OFFERED rather
#    than the hours actually taken off. The tester's project ended with 581.5
#    hours left against a 450-hour total, which the display read out as "-67%
#    of your hours spent". Here: 612.5 against 500 before the fix.
s = _starved(9e5)
s.step()
_st = s.active.get("identity_cover") or {}
check("a project can never be given back more hours than it has spent",
      _st.get("ph_left", 0) <= NODES["identity_cover"]["ph"] + 1e-6,
      "%.1f left of a %.1f total" % (_st.get("ph_left", -1),
                                     NODES["identity_cover"]["ph"]))
check("an underfunded project says why it is underfunded",
      _st.get("underfunded_this_year") and "arrears" in (_st.get("why_underfunded") or ""),
      _st.get("why_underfunded"))

# 2. A shortage used to scale the PAYMENT rather than the instalment, so once
#    the balance was smaller than a year's instalment you paid a fraction of
#    what was left, every year, approaching zero without arriving - while
#    completion needs the bill under half a denarius. The tester watched one sit
#    at "71% done" for twenty-five years. Sixty years and 15.9 denarii still
#    owed, before the fix.
s = _starved(60.0, supply=0.001, arrears=0.0, capital=500000.0)
s.active["identity_cover"]["ph_left"] = 0.0
for _i in range(60):
    s.step()
    if "identity_cover" not in s.active:
        break
check("a small remaining bill is actually paid off, not approached for ever",
      "identity_cover" not in s.active,
      "%.4f den still owed after 60 years"
      % (s.active.get("identity_cover", {}).get("cost_left", 0.0)))

# --- the Mexica play tester: advice you cannot act on is not advice ----------
# They were told the answer to the Spanish was "walls, firearms, powerful
# friends, and copies of your work kept somewhere else", played 154 years with
# 269 startable things in view, and reported finding no hedge of any kind. The
# hedges were there. Nothing ever connected the words to the list.
s = sim(civ="mexica_1500", manual=False)
s.fog = True
s.revealed = set()
for _i in range(45):
    s.step()
_adv = s.hazard_advice("staff_loss")
_steps = _adv.get("you_could_begin_now_toward_it") or []
# THE GUARANTEE IS THAT IT NAMES THEM, with what each is waiting on - not that
# one happens to be startable in the particular year this check stops at. The
# tester's complaint was "nothing connected the words to the 269 things in
# view", and naming the hedge and its blocker is what connects them. Requiring
# a startable one made this check hostage to how a 45-year run happens to
# develop, and it duly broke the first time the economy changed underneath it.
check("a hazard names things in front of you that hedge against it",
      _steps and all(e.get("id") and (e["can_begin_now"] or e.get("waiting_on"))
                     for e in _steps),
      [(e["id"], e["can_begin_now"], (e.get("waiting_on") or "")[:40]) for e in _steps])
check("anything you could begin toward a hedge is listed before what you cannot",
      [e["can_begin_now"] for e in _steps] == sorted(
          (e["can_begin_now"] for e in _steps), reverse=True),
      [e["can_begin_now"] for e in _steps])
# ...and it must not do that by naming whatever sits first in the strategy
# order. An earlier version walked the whole ancestry and advised beginning a
# "respectable cover identity" as a hedge against smallpox.
_counters = {n for n, _s2, _l in s.HAZARD_COUNTERS["staff_loss"]}
_near = _counters | {p_ for n in _counters if n in NODES for p_ in NODES[n]["pre"]}
check("a hedge is a hedge, not any ancestor of one",
      all(e["id"] in _near for e in _steps),
      [e["id"] for e in _steps if e["id"] not in _near])

# --- the England weird-play tester -------------------------------------------
# 1. The game printed its own resume command, `play --session england_1300.json`,
#    and then refused it: --civ defaulted to Rome and the save was England. A
#    save says what game it is; the command line should not have to.
_rs = "%s/resume.json" % _PLAY_DIR
if os.path.exists(os.path.join(ROOT, _rs)):
    os.remove(os.path.join(ROOT, _rs))
_r1, _ = _play(["step 2", "quit"], civ="england_1300", extra=["--session", _rs, "--fog"])
_r2, _ = _play(["state", "quit"], extra=["--session", _rs])       # no --civ, as printed
check("a save resumes without being told again which game it is",
      "Resumed from" in _r2 and "1302" in _r2, _r2[:400])
check("fog survives a save and reload, rather than opening the whole tree",
      "Fog of war is on" in _r2, [l for l in _r2.splitlines() if "og of war" in l])
_r3, _ = _play(["quit"], civ="rome_100ad", extra=["--session", _rs])
check("a --civ that contradicts the save is refused, not started over the top",
      "that save is a" in _r3 or "different civilisation" in _r3, _r3[:300])

# 2. Every documented three-word buy lost its material to the typed parser, so
#    the whole mining subsystem was unreachable from the front door.
_mq, _ = _play(["quote mine coal 500", "quote coal 500", "quit"], civ="england_1300")
check("the mining commands the help gives actually parse",
      _mq.count("to sink it") == 2, _mq[:400])

# --- the England break tester -------------------------------------------------
# 1. THE FOG EXPLOIT. `bounty` checked prerequisites before it checked whether
#    you had heard of the thing, so refusing a bounty on the goal printed the
#    goal's seven missing prerequisites by name. The tester crawled that error
#    recursively and recovered 134 hidden ids and the whole graph to the
#    transistor, in six rounds, with fog on throughout.
_bt, _, _ = proto([{"cmd": "bounty", "id": "point_contact_transistor"},
                   {"cmd": "start", "id": "point_contact_transistor"},
                   {"cmd": "mothball", "id": "point_contact_transistor"},
                   {"cmd": "why", "id": "point_contact_transistor"}], fog=True)
# The PROPERTY, not the wording: no reply may contain the id of anything the
# player has not heard of. (`why` on the goal is answered now - the status line
# names the goal every turn - but it still may not name what the goal rests on.)
_GOAL_PRE = NODES["point_contact_transistor"]["pre"]
_bt_text = json.dumps(_bt)
check("no command names a prerequisite of something you have not heard of",
      not any(p_ in _bt_text for p_ in _GOAL_PRE),
      [p_ for p_ in _GOAL_PRE if p_ in _bt_text])
check("...and only `why` answers about the goal at all; the rest still refuse",
      all(r.get("ok") is False for r in _bt[:3]) and _bt[3].get("ok") is True,
      [r.get("ok") for r in _bt])
check("...and what `why` says about the goal counts what it cannot name",
      "have not heard of" in json.dumps(_bt[3]), json.dumps(_bt[3])[:200])

# 2. The menu promises "Saved to X. Come back with ..."; a tester quit before
#    typing anything, found no file, followed the printed line, and landed in a
#    different civilisation's fresh game.
_sv = "%s/promised.json" % _PLAY_DIR
if os.path.exists(os.path.join(ROOT, _sv)):
    os.remove(os.path.join(ROOT, _sv))
_play(["quit"], civ="england_1300", extra=["--session", _sv])
check("a save the game promised exists even if you type nothing",
      os.path.exists(os.path.join(ROOT, _sv)), _sv)

# 3. state and the prompt both said 2,400 founder-hours free after 2,300 of
#    them had been sold, and then refused one more hour for having none.
# Derived from the pool, not a literal: this check hardcoded 2,300 hours and
# started failing the moment the founder's year came down to 2,000, because
# `work` correctly refused to sell hours that no longer existed.
_pool = sim().director_pool()
_sell = _pool - 100
_st2, _, _ = proto([{"cmd": "work", "trade": "scholar", "hours": _sell},
                    {"cmd": "state"}])
check("hours already sold for wages are not still reported as free",
      _st2[0].get("ok") is True and _st2[1]["founder_hours_available"] < 200,
      "%r free after selling %g of %g" % (_st2[1].get("founder_hours_available"),
                                          _sell, _pool))

# 4. auto_shed discards technologies you built - under fog the only score there
#    is - and it was on by default for a player.
check("nothing that deletes your work is on by default for a player",
      sim(manual=True).policy["auto_shed"] is False
      and sim(manual=False).policy["auto_shed"] is True,
      (sim(manual=True).policy["auto_shed"], sim(manual=False).policy["auto_shed"]))

# 5. You could sell every one of your 2,400 hours as a labourer and still
#    collect the full fee from a surgery you were demonstrably not in. The
#    practice is your own two hands; that was the same hours sold twice.
s = sim()
_rev_before = s.revenue()
_earned, _note = s.work_for_wages("labourer", s.director_pool())
check("hours sold as a labourer are not also spent practising medicine",
      _earned > 0 and _rev_before > 0 and s.revenue() < _rev_before * 0.05,
      "revenue %.1f -> %.1f having sold every hour" % (_rev_before, s.revenue()))
# ...and the player is told, rather than left to find it in the ledger. A
# tester measured a year of labour at 66 denarii against a 227 cost of living
# and a 259-a-year practice switched off, and called `work` self-destructive.
# It is, for a physician; the defect was that nothing said so.
check("selling your hours at a loss says so, and still happens",
      _note and "cost you" in _note, _note)
s2 = sim()
s2.work_for_wages("labourer", s2.director_pool() * 0.5)
check("selling half your hours costs you half the practice, not all of it",
      abs(s2.revenue() - _rev_before * 0.5) < _rev_before * 0.06,
      "%.1f against half of %.1f" % (s2.revenue(), _rev_before))

# 6. `buy mine` spent every denarius you had and handed back a fraction of the
#    mine you asked for, without asking. A command you typed is not a standing
#    order to spend everything.
_mn, _, _ = proto([{"cmd": "buy", "what": "mine", "material": "coal", "n": 500},
                   {"cmd": "state"}])
check("a mine you cannot pay for is refused, not part-bought with all your money",
      _mn[0].get("ok") is False and "Nothing was changed" in (_mn[0].get("error") or "")
      and _mn[1]["capital"] > 300,
      (_mn[0].get("error", "")[:80], _mn[1].get("capital")))

# --- the England normal-play tester -------------------------------------------
# 1. `train optician 1` destroyed the save. trades_created holds TRADE names and
#    was validated against the tech tree, so teaching any of the five trades
#    that gate chemistry, precision and electricity wrote a name the next load
#    refused as a missing technology. It cost that tester two runs and, by their
#    own measurement, 1,230 technologies.
_tr = "%s/trained.json" % _PLAY_DIR
if os.path.exists(os.path.join(ROOT, _tr)):
    os.remove(os.path.join(ROOT, _tr))
_play(["train optician 1", "quit"], civ="rome_100ad", extra=["--session", _tr])
_t2, _ = _play(["labour", "quit"], extra=["--session", _tr])
check("teaching a trade does not destroy the save",
      "Resumed from" in _t2 and "optician" in _t2 and "does not have" not in _t2,
      _t2[:300])

# 2. The one number that decides anything was the one `available` did not show.
#    The tester scripted 460 `why` calls to reconstruct revenue, upkeep and how
#    much rests on a node, and called competent play "writing a scraper".
_av, _, _ = proto([{"cmd": "available"}], fog=True)
_row = (_av[0].get("cheapest_six") or [{}])[0]
check("available shows what a thing earns, costs after, and what rests on it",
      all(f in _row for f in ("earns_per_year", "costs_per_year_after",
                              "how_much_rests_on_this")),
      sorted(_row))
check("available names the high-leverage things, not only the cheap ones",
      any(e.get("id") in ("identity_cover", "units_standards")
          for e in (_av[0].get("most_rests_on_these") or [])),
      [e.get("id") for e in (_av[0].get("most_rests_on_these") or [])])

# 3. Under fog the game said "there is no score but what you have built" while
#    an ending screen named a goal. The founder knows what a transistor is; fog
#    hides the society's tree, not the player's own intent. The NAME, never the
#    id - the id would hand back the prerequisite crawl.
_gh, _, _ = proto([{"cmd": "help"}, {"cmd": "state"}], fog=True)
_hw = json.dumps(_gh[0])
check("fog hides the road to the goal, not the goal",
      "transistor" in _hw.lower() and "point_contact_transistor" not in _hw
      and _gh[1].get("goal") is None and _gh[1].get("goal_in_words"),
      (_gh[1].get("goal"), _gh[1].get("goal_in_words")))

# 4. downstream_count is asked for once a row now, so it cannot be the old
#    per-call closure over all 2,831 nodes.
_t0 = time.time()
for _k in list(NODES)[:400]:
    S.downstream_count(NODES, _k)
check("what rests on a node is cheap enough to put in a table",
      time.time() - _t0 < 1.0, "%.2fs for 400" % (time.time() - _t0))

# 5. Losing a finished work was silent. A tester lost fourteen inside one
#    `step 12`, corpus_written and school_founded among them, with every
#    arrival named and no departure named.
s = sim(capital=-50000.0, manual=False)
s.done.add("fin_pawnshop")
s.done.add("civ_road_paved")
s._done_changed()
_lost_before = set(s.done)
_ls, _, _ = proto([{"cmd": "start", "id": "hom_eraser_breadcrumb"},
                   {"cmd": "step", "years": 1}])
check("a step reports what left as well as what arrived",
      "lost" in _ls[-1], sorted(_ls[-1])[:12])

# 6. A quote read years ago is not what you pay: project_cost moves with
#    prices, the coinage and materials. The bill IS fixed when you start, and
#    nothing said what it was fixed at.
_q1, _, _ = proto([{"cmd": "why", "id": "hom_eraser_breadcrumb"},
                   {"cmd": "start", "id": "hom_eraser_breadcrumb"}])
check("starting something says what bill you have just taken on",
      _q1[1].get("the_bill_you_have_taken_on") is not None
      and _q1[0]["cost"].get("as_of_year"),
      (_q1[1].get("the_bill_you_have_taken_on"), _q1[0]["cost"].get("as_of_year")))

# 7. `suspicion` was replaced by `scandal` and then reported, unchanging, for
#    five hundred years. Two testers read a dead vestige as a broken mechanic.
_su, _, _ = proto([{"cmd": "state"}])
check("no dead field is reported every turn as though it were a mechanic",
      "suspicion" not in _su[0], [k for k in _su[0] if "susp" in k])

# --- the playtest-notes sweep -------------------------------------------------
# S1: every capital loss was written `capital *= x`, which is sign-blind. At
# minus a thousand denarii a sacking multiplied the DEBT by 0.4 and PAID the
# player six hundred, which made the deepest hole in the game the safest place
# to stand. Caught live twice in the notes: a Mexica sack -251 -> -100.5, an
# England thatch fire -629.2 -> -569.4.
s = sim()
s.capital = -1000.0
_gave = s.lose_capital(0.60)
check("a catastrophe never pays off a debt",
      s.capital == -1000.0 and _gave == 0.0,
      "capital %.1f, took %.1f" % (s.capital, _gave))
s.capital = 1000.0
s.lose_capital(0.60)
check("a catastrophe still takes its share of what you actually have",
      abs(s.capital - 400.0) < 1e-6, "%.1f" % s.capital)

# A1: hours_effective_this_year was `per - refunded`, and `per` is what was
# OFFERED, which may exceed what the project had left. The refunds are capped at
# spent_hours; this line was not, so a project reported 387.2 effective hours a
# year for four years while founder_hours_left never moved.
s = _starved(9e5)
_before_left = s.active["identity_cover"]["ph_left"]
s.step()
_st3 = s.active.get("identity_cover") or {}
check("hours reported as effective are hours that actually came off the work",
      _st3.get("hours_effective_this_year", 0)
      <= _before_left - _st3.get("ph_left", 0) + 1e-6,
      "reported %.1f, actually %.1f"
      % (_st3.get("hours_effective_this_year", -1),
         _before_left - _st3.get("ph_left", 0)))

# --- the strategy order must actually put first what the goal needs first ----
# Han China reached the transistor in 0% of runs, and the reason was never
# economic: a run sat at year 700 holding 3.37 MILLION denarii, 57 scholars and
# 99 artisans, having never built cap_heat_1100 - tier 0, 225 denarii, two
# artisans, a prerequisite of the goal, and startable at any moment. It was at
# index 589 in the order the optimizer works down, because topo_stable was told
# nothing about the 128 nodes the strategy names explicitly and so could never
# place anything that depended on them. 100% after the fix.
_lab_o, _order_o, _b_o = S.load_strategy("recommended", NODES, GOAL)
_idx_o = {k: i for i, k in enumerate(_order_o)}
_viol = [(k, p_) for k in _order_o for p_ in NODES[k]["pre"]
         if _idx_o.get(p_, -1) > _idx_o[k]]
check("no technology is ordered before something it requires",
      not _viol, "%d violations, e.g. %s" % (len(_viol), _viol[:3]))
_need_o = S.closure(NODES, GOAL)
_last = max(_idx_o[k] for k in _need_o if k in _idx_o)
check("everything the goal needs is near the front, not spread over the tree",
      _last < 400, "the last goal-critical node sits at index %d of %d"
                   % (_last, len(_order_o)))

# --- the sweep of every playtest note: what was still live ------------------
# S2. `start` took all 104 available projects in a fresh England game - 43,914
# denarii of work in hand against 400 in cash and a displayed credit limit of
# 1,503 - and put the player at -3,672 one step later. `help economy` promises
# "as far as somebody will lend you and no further"; nothing enforced it.
s = sim(civ="england_1300")
_taken, _refused = 0, None
for _k in list(s.order):
    if s.can_start(_k):
        _ok, _why = s.start_project(_k)
        if _ok:
            _taken += 1
        elif "work in hand" in (_why or ""):
            _refused = _why
            break
_owed = sum(st.get("cost_left") or 0.0 for st in s.active.values())
check("you cannot commit to more work than cash and credit could ever cover",
      _refused is not None and _owed <= max(0.0, s.capital) + s.credit_limit() + 1,
      "took %d projects, owing %.0f against %.0f of cash and credit"
      % (_taken, _owed, max(0.0, s.capital) + s.credit_limit()))

# S14. A node that costs nothing to build and 20 a year to keep could be shut
# down and brought back around the annual tick for nothing, so its upkeep was
# optional. The engine already gets this right for mines.
s = sim(civ="england_1300", capital=50000.0)
_free = [k for k in NODES if NODES[k]["up"] > 0 and s.project_cost(k) < 1.0
         and k not in s.granted and not NODES[k]["pre"]]
s.done.add(_free[0])
s._done_changed()
s.mothball_work(_free[0])
_cap = s.capital
s.restore_work(_free[0])
check("shutting a work down and reopening it is never free",
      _cap - s.capital >= NODES[_free[0]]["up"],
      "%s round trip cost %.0f against %.0f a year of upkeep"
      % (_free[0], _cap - s.capital, NODES[_free[0]]["up"]))

# S23/S24, both in the typed front end.
_tp, _ = _play(["why AG2_MARLING", "step 1; step 1", "state", "quit"],
               civ="england_1300")
check("a typed id is not case-sensitive when the game knows the right one",
      "COST:" in _tp, [l for l in _tp.splitlines() if "REFUSED" in l][:2])
check("two commands on one line are refused, not half-executed",
      "one command per line" in _tp and "YEAR 1300" in _tp, _tp[:200])

# S3. Naming a save file that is not there started a brand new default game
# and then wrote it over that filename. A tester nearly lost a forty-year
# England run to a mistyped path.
_missing, _rc_m = _play(["quit"], extra=["--session", "%s/no_such.json" % _PLAY_DIR])
check("a save file that is not there is a typo, not a new game",
      "do not know what game you meant" in _missing
      and not os.path.exists(os.path.join(ROOT, _PLAY_DIR, "no_such.json")),
      _missing[:200])

# A3. `why cap_heat_1300` on Han reported done:true and
# missing_prerequisites:["cap_heat_1100"] in the same object. Nothing a player
# reads should be able to say a thing they have is missing something.
_g3, _, _ = proto([{"cmd": "why", "id": "cap_heat_1300"}], civ="han_china_100ad")
check("nothing this society already has is also reported as missing something",
      _g3[0].get("done") is True and not _g3[0].get("missing_prerequisites")
      and _g3[0].get("held_without_building_it") is True,
      {k: _g3[0].get(k) for k in ("done", "missing_prerequisites",
                                  "held_without_building_it")})
# ...and the fix must NOT be to close the grant over its prerequisites, which
# would hand Tenochtitlan sextants and cementation steel for nothing, because
# maize hangs off "cross the Atlantic and found a trading post".
_mx = sim(civ="mexica_1500")
check("a society is not granted the route another society would take to it",
      "cementation_steel" not in _mx.done and "clock_pendulum" not in _mx.done
      and "fud_maize" in _mx.done,
      [k for k in ("fud_maize", "cementation_steel", "clock_pendulum")
       if k in _mx.done])

# --- knowing how, and actually running it ------------------------------------
# The user, on the deepest thing anyone said about this model: "you research
# the finance stuff and instantly make money -- but shouldn't that just unlock
# the ABILITY to do it? You research loans, now you can give out loans. What if
# you didn't give out any?" 1,337 nodes carried revenue and 1,256 of those also
# carried upkeep, so the tree already called them going concerns; the only
# thing missing was the act of opening the doors.
# Hire somebody first: a concern needs a pair of your hands to run it, which
# is the whole point of the staffing floor. Nobody runs a pawnshop alone from
# nowhere.
_v, _, _ = proto([{"cmd": "hire", "trade": "artisan", "n": 2},
                  {"cmd": "start", "id": "fin_pawnshop"},
                  {"cmd": "step", "years": 6},
                  {"cmd": "money"},
                  {"cmd": "open", "id": "fin_pawnshop"},
                  {"cmd": "money"}], kit="equestrian")
_before, _open, _after = _v[3], _v[4], _v[5]
check("working out how to do something does not by itself pay you",
      "fin_pawnshop" not in (_before.get("where_the_money_comes_from") or {}),
      _before.get("where_the_money_comes_from"))
check("opening the doors is what pays you",
      _open.get("ok") is True
      and (_after.get("where_the_money_comes_from") or {}).get("fin_pawnshop"),
      _after.get("where_the_money_comes_from"))

s2 = sim(capital=200000.0)
s2.hire("artisan", 2)
s2.done.add("fin_pawnshop")
s2._done_changed()
_cap0 = s2.capital
s2.open_venture("fin_pawnshop")
check("opening a concern costs stock and premises, not nothing",
      _cap0 - s2.capital >= NODES["fin_pawnshop"]["up"],
      "%.0f to open against %.0f a year of running cost"
      % (_cap0 - s2.capital, NODES["fin_pawnshop"]["up"]))

# You cannot run fifty businesses with three people.
s3 = sim(capital=1000000.0)
# BIG ENOUGH THAT ONE PERSON CANNOT RUN IT. The founder counts as a pair of
# hands now, so a small shop is exactly what they CAN open alone; the staffing
# rule is about scale, and this check has to test scale.
_heavy = [k for k in NODES if NODES[k]["rev"] >= 6000][:1]
if _heavy:
    s3.done.add(_heavy[0]); s3._done_changed()
    s3.artisans = 0.0
    _okh, _whyh = s3.open_venture(_heavy[0])
    check("a concern nobody is free to run cannot be opened",
          _okh is False and "nobody free" in (_whyh or ""), _whyh)

# Shutting it stops both sides and keeps the knowledge.
s4 = sim(capital=200000.0)
s4.hire("artisan", 2)
s4.done.add("fin_pawnshop"); s4._done_changed()
s4.open_venture("fin_pawnshop")
_rev_on, _up_on = s4.revenue(), s4.upkeep()
s4.mothball_work("fin_pawnshop")
check("closing a concern stops what it earned and what it cost, both",
      s4.revenue() < _rev_on and s4.upkeep() < _up_on
      and "fin_pawnshop" in s4.done,
      "rev %.0f->%.0f up %.0f->%.0f, still known %s"
      % (_rev_on, s4.revenue(), _up_on, s4.upkeep(), "fin_pawnshop" in s4.done))

check("opening things for you is on for the optimizer and off for a player",
      sim(manual=True).policy["auto_open"] is False
      and sim(manual=False).policy["auto_open"] is True,
      (sim(manual=True).policy["auto_open"], sim(manual=False).policy["auto_open"]))

# What you run has to survive a save, or reloading quietly shuts your business.
_vs = "%s/ventures.json" % _LOADTEST_DIR
_rt, _, _ = proto([{"cmd": "hire", "trade": "artisan", "n": 2},
                   {"cmd": "start", "id": "fin_pawnshop"},
                   {"cmd": "step", "years": 6},
                   {"cmd": "open", "id": "fin_pawnshop"},
                   {"cmd": "save", "file": _vs},
                   {"cmd": "load", "file": _vs},
                   {"cmd": "state"}], kit="equestrian")
check("what you are running survives a save and reload",
      _rt[-1].get("concerns_you_run") == 1,
      "runs %r after a round trip" % _rt[-1].get("concerns_you_run"))

# --- a run that has stopped has to say so --------------------------------
# A weird-play tester's "most important finding": a run sat at exactly -924.5
# denarii for fifty years, completing nothing, while INSOLVENCY SETTLED fired
# once a decade for ever, and nothing anywhere said the run had effectively
# stopped or that it was escapable. It WAS escapable - they got out by working
# for wages - which is exactly why silence was the defect.
s = sim(civ="norse_900ad", capital=40000.0)
s.hire("smith", 3)
_loser = [k for k in NODES if NODES[k]["up"] > NODES[k]["rev"] > 0][:1]
if _loser:
    s.done.add(_loser[0]); s._done_changed(); s.open_venture(_loser[0])
s.capital = -900.0
s.insolvent_years = 12
_diag = s.stall_diagnosis()
check("a run that has effectively stopped says so, and says what would restart it",
      _diag and _diag["what_would_change_it"]
      # "work for wages" became "work as a <trade>", because advice that does
      # not say which job to take can be followed into a loss.
      and any(w.startswith("work as a ") for w in _diag["what_would_change_it"]),
      _diag)
check("a solvent run is not told it is stuck",
      sim(civ="norse_900ad").stall_diagnosis() is None,
      sim(civ="norse_900ad").stall_diagnosis())

# A one-character typo used to be answered with the words "did you mean: no idea".
_dm, _, _ = proto([{"cmd": "why", "id": "ag2_marlingg"}])
check("a typo in a name gets a real suggestion, not 'no idea'",
      "ag2_marling" in (_dm[0].get("error") or ""), _dm[0].get("error"))

# Two Roman-branded grants were still being handed free to every civilisation.
_ROMAN = ("_roman", "_rome", "annona", "insula", "societas", "collegium",
          "argentarii", "latifundi", "cursus", "pharos")
for _civ in ("han_china_100ad", "norse_900ad", "mexica_1500", "england_1300"):
    _sc = sim(civ=_civ)
    _bad = sorted(k for k in _sc.granted if any(m in k for m in _ROMAN))
    check("%s is not handed Roman institutions for nothing" % _civ,
          not _bad, _bad)

# --- the Norse deadlock ------------------------------------------------------
# A Norse run ended at year 1500 with 31,068 denarii, 136 technologies and 1.6
# craftsmen, unable to build workshop_first because it needs 2 - while every
# institution that raises the staff ceiling (freedman_staff, collegium_licensed,
# school_founded) needs workshop_first first. You needed two craftsmen to build
# the place craftsmen work, and could never get to two. The Norse reached the
# goal in 0% of runs and it was never about money.
#
# The gate read self.artisans alone, so work you had already paid an outside
# shop to do did not count - and the refusal's own advice was to go and
# commission it.
s = sim(civ="norse_900ad", capital=100000.0)
# Prerequisites are tested before staff, so satisfy them: the point of this
# check is the staff gate, not the ladder above it.
for _p in NODES["workshop_first"]["pre"]:
    s.done.add(_p)
s._done_changed()
_ok0, _why0 = s.start_reason("workshop_first")
_blocked_on_staff = "craftsmen" in (_why0 or "")
s.commission("carpenter", 4000)
_ok1, _why1 = s.start_reason("workshop_first")
check("craftsmen you have under contract count toward what a project needs",
      _blocked_on_staff and "craftsmen" not in (_why1 or ""),
      "before: %s | after: %s" % ((_why0 or "")[:60], (_why1 or "")[:60]))
check("commission can unblock the gate whose own advice is to commission",
      s.craft_hands_available() >= 2.0,
      "%.2f craft hands from 4,000 contracted hours" % s.craft_hands_available())

# --- the invariant behind a whole class of contradiction ---------------------
# A weird-play tester reached, in seven years from a fresh start, a node that
# was simultaneously forgotten and running: `state` said the concern was
# running, `ventures` billed for it, `money` charged nothing, and all four
# verbs refused it on mutually contradictory grounds - `start` said restore it,
# `restore` said start it, `open` said you do not know it, `mothball` said you
# never built it. The entry could never be cleared. Every one of those symptoms
# is the same broken invariant: you cannot be running something you do not know
# how to do.
def _operating_subset_of_done(s_):
    return sorted(s_.operating - s_.done)


s = sim(capital=-100000.0, civ="norse_900ad")
s.done.add(_LOSS); s._done_changed(); s.operating.add(_LOSS)
s.credit_limit = lambda: 0.0
s.enforce_credit_limit(100)
check("creditors' seizure cannot leave you running what you no longer know",
      not _operating_subset_of_done(s), _operating_subset_of_done(s))

s = sim(civ="han_china_100ad", manual=False)
for _ in range(60):
    s.step()
check("a long run never ends up running something it does not know",
      not _operating_subset_of_done(s), _operating_subset_of_done(s)[:5])

# The typo suggester searched the whole tree with fog on: `why transistor` gave
# back junction_transistor and point_contact_transistor, and the tester pointed
# out that two-letter prefixes would reconstruct the entire namespace.
_fg, _, _ = proto([{"cmd": "why", "id": "transistor"},
                   {"cmd": "why", "id": "vacuum"},
                   {"cmd": "why", "id": "semiconductor"}], fog=True)
check("a misspelling cannot be used to enumerate the tree through the fog",
      all("transistor" not in (r.get("error") or "").replace("'transistor'", "")
          and "vacuum_tube" not in (r.get("error") or "") for r in _fg),
      [r.get("error", "")[:80] for r in _fg])

# open/ventures are how technology turns into income and were missing from the
# command list; `open` on the founder's own practice denied it was theirs while
# `money` itemised it as their largest source of income.
_hc, _, _ = proto([{"cmd": "help", "topic": "commands"},
                   {"cmd": "open", "id": "med_cataract_couching"}],
                  civ="han_china_100ad")
check("every way of turning knowledge into income is in the command list",
      all(c in json.dumps(_hc[0]) for c in ("open", "ventures")),
      sorted((_hc[0].get("commands") or {}).keys())[:6])
check("the game does not deny that your own practice is yours",
      "already doing that" in (_hc[1].get("error") or ""), _hc[1].get("error"))

# --- round 5, the Han testers --------------------------------------------
# 1. THE WORST: resuming a save re-rolled the dice. Nothing saved the random
#    state, so a project sitting at its completion threshold re-rolled its
#    failure check on every resume: `start fin_bimetallism` then one `step`
#    per process oscillated 100%/60%/100%/60% for ever, burning hours and
#    money and never finishing. Reproduced 5 times out of 5. It also silently
#    re-drew every hazard and event a returning player would meet.
_rngdir = "%s/rng" % _PLAY_DIR
os.makedirs(os.path.join(ROOT, _rngdir), exist_ok=True)
_rs2 = "%s/dice.json" % _rngdir
if os.path.exists(os.path.join(ROOT, _rs2)):
    os.remove(os.path.join(ROOT, _rs2))


def _agent_session(cmds, first=False):
    a = [sys.executable, os.path.join(HERE, "simulator.py"), "agent",
         "--session", _rs2]
    if first:
        a += ["--civ", "han_china_100ad"]
    p_ = subprocess.run(a, input="\n".join(json.dumps(c) for c in cmds) + "\n",
                        capture_output=True, text=True, timeout=240, cwd=ROOT)
    return [json.loads(l) for l in p_.stdout.splitlines() if l.strip()]


_agent_session([{"cmd": "start", "id": "fin_bimetallism"}], first=True)
_finished_in = None
for _i in range(8):
    _o = _agent_session([{"cmd": "step", "years": 1}, {"cmd": "state"}])
    if "fin_bimetallism" not in (_o[-1].get("active") or {}):
        _finished_in = _i + 1
        break
check("a project finishes across resumes instead of oscillating for ever",
      _finished_in is not None,
      "still unfinished after 8 resumes" if _finished_in is None
      else "finished after %d" % _finished_in)

# 2. Founder hours could be spent twice: `train` wrote its own counter and
#    `work` read only the wage one, so 3,800 hours went into a 2,000-hour year.
_dh, _, _ = proto([{"cmd": "train", "trade": "machinist", "n": 2},
                   {"cmd": "train", "trade": "chemist", "n": 2},
                   {"cmd": "state"},
                   {"cmd": "work", "trade": "smith", "hours": 2000}],
                  civ="han_china_100ad", kit="equestrian")
check("hours spent teaching are not still available to sell",
      _dh[2]["founder_hours_available"] < 400 and _dh[3].get("ok") is False,
      "%r free, work accepted=%r" % (_dh[2].get("founder_hours_available"),
                                     _dh[3].get("ok")))

# 3. A bribe that buys nothing said so and charged 5,000 anyway.
_bb, _, _ = proto([{"cmd": "bribe", "amount": 5000},
                   {"cmd": "bribe", "amount": 5000},
                   {"cmd": "state"}], kit="equestrian")
check("a bribe that would buy nothing is refused, not charged",
      _bb[1].get("ok") is False and "Nothing was changed" in (_bb[1].get("error") or ""),
      _bb[1].get("error"))

# 4. Eleven ids carry capitals, among them the whole cap_pure_2N..9N purity
#    ladder on the critical path to germanium. Lowercasing what the player
#    typed made them unreachable from the typed front end.
_cap, _ = _play(["why cap_pure_2N", "why CAP_PURE_2N", "why AG2_MARLING", "quit"])
check("ids that carry capitals are reachable, and case is not the player's problem",
      _cap.count("COST:") == 3, [l for l in _cap.splitlines() if "REFUSED" in l][:2])

# 5. `available` truncated ids at 30 characters, so the longest could not be
#    copied out of the table that told you to use them.
_av, _ = _play(["available all", "quit"])
_longest = max(NODES, key=len)
check("no id is truncated in the table a player copies ids from",
      all(len(w) <= 30 or w in _av for w in [_longest]) or _longest not in _av,
      "longest id is %d chars" % len(_longest))

# 6. A year's hours must add up. Block 5b reused the name `pool`, clobbering
#    the project budget the report was computed against, and a year came to
#    2,900 hours out of 2,000.
s = sim(civ="rome_100ad", capital=400.0, manual=False, events=False)
for _ in range(4):
    s.step()
    _h = s.hours_this_year
    _tot = _h["wage_work"] + _h["teaching"] + _h["offered_to_projects"] + _h["unused"]
    check("a year's hours add up to a year (%d)" % s.year,
          _tot <= _h["available"] + 1.0, _h)

# 7. A project blamed the wrong resource for 275 years. `logarithms` sat at
#    "waiting on your hours" from 325 AD to the horizon with 1,900 idle founder
#    hours, while the real cause was 40,000 scribe-hours wanted from a society
#    that can field a few thousand. waiting_on was read off whatever the last
#    step happened to record instead of being worked out against today.
s = sim(civ="han_china_100ad", capital=500000.0)
for _p in NODES["logarithms"]["pre"]:
    s.done.add(_p)
s._done_changed()
s.hire("scholar", 2)
s.start_project("logarithms")
s.step()
_w = S._waiting_on(s, NODES, "logarithms", s.active["logarithms"], 0)
check("a stalled project names the resource actually stalling it",
      "scribe" in _w and "your hours" not in _w, _w)
check("...and says how far short the society is, in numbers",
      "can field" in _w or "booked" in _w, _w)

# A play tester watched their year grow from 2,000 hours to 6,090 with nothing
# saying why. It is deputies, not the founder working harder.
_hrs, _, _ = proto([{"cmd": "state"}])
check("state says where the founder's hours actually come from",
      (_hrs[0].get("where_your_hours_come_from") or {}).get("hours_each_deputy_adds"),
      _hrs[0].get("where_your_hours_come_from"))

# 8. `policy auto_hire on`, nothing else done at all, put a break tester into
#    ten years of debt bondage in ten steps - while the policy's own
#    description promises to "grow the staff toward what you can house and
#    pay". The whole careful affordability calculation was undone by a floor
#    beneath it: scale was max(0.10, ...), so a household with no surplus
#    still hired a tenth of its headroom.
s = sim(civ="han_china_100ad")
s.policy["auto_hire"] = True
for _ in range(10):
    s.step()
check("auto_hire on a poor household hires nobody and stays solvent",
      s.bondage_years_left == 0 and s.capital > 0,
      "capital %.0f, staff %.2f, bondage %s"
      % (s.capital, sum(s.employees.values()), s.bondage_years_left))
s = sim(civ="han_china_100ad", capital=100000.0)
s.policy["auto_hire"] = True
for _ in range(10):
    s.step()
check("...and on a rich one it actually hires",
      sum(s.employees.values()) > 1.0,
      "staff %.2f on 100,000" % sum(s.employees.values()))

# --- the persona is a persona, not a licence to do arithmetic ----------------
# The user, on identity_cover: "does anything building on it actually require
# it, or does it just make it so that you have social metrics that help? You
# could build a hot air balloon or bike without an identity, you are just more
# likely to be called a witch."
#
# They were right, and it was worse than that. identity_cover's whole
# implementation was +1.0 to the reputation floor and +400 to the credit
# limit; the "reduces all future suspicion" in its own description referred to
# a field that no longer exists. Its real function was to gate a quarter of
# the tree - and it was empirically the single node blocking England and
# Mexica from ever reaching the goal, because arithmetic_positional needs it
# and nothing else.
check("writing down zero does not require a respectable persona",
      "identity_cover" not in NODES["arithmetic_positional"]["pre"]
      and "identity_cover" not in NODES["scientific_method"]["pre"],
      (NODES["arithmetic_positional"]["pre"], NODES["scientific_method"]["pre"]))
check("...but being received by a patron, and publishing, still do",
      "identity_cover" in NODES["patron_local"]["pre"]
      and "identity_cover" in NODES["world_map"]["pre"],
      (NODES["patron_local"]["pre"], NODES["world_map"]["pre"]))


def _persona(has):
    s_ = sim(civ="england_1300")
    if has:
        s_.done.add("identity_cover")
        s_._done_changed()
    s_.update_protection()
    return s_


_no, _yes = _persona(False), _persona(True)
_n = NODES["hot_air_balloon"]
check("a persona makes the same strange work less alarming, as it says it does",
      _yes.alarm_of(_n) < _no.alarm_of(_n) * 0.85
      and _yes.protection > _no.protection,
      "alarm %.2f -> %.2f, protection %.3f -> %.3f"
      % (_no.alarm_of(_n), _yes.alarm_of(_n), _no.protection, _yes.protection))
check("...and you can still build the balloon without one",
      _no.alarm_of(_n) > 0 and "identity_cover" not in NODES["hot_air_balloon"]["pre"],
      NODES["hot_air_balloon"]["pre"])

# --- the history notes must not rebuild the wall ----------------------------
# Every dated hazard now carries a real historical note and England has
# fifteen of them. Embedded whole, they took one `state full` reply to nearly
# twenty thousand bytes and one `risk` reply to seventeen thousand - which is
# the exact wall this interface was broken up to stop producing.
for _civ_big in ("england_1300", "mexica_1500", "rome_100ad"):
    _sf, _, _ = proto([{"cmd": "state", "full": True}, {"cmd": "risk"}],
                      civ=_civ_big, fog=True)
    check("%s: state full stays readable" % _civ_big,
          len(json.dumps(_sf[0])) < 9000, "%d bytes" % len(json.dumps(_sf[0])))
    check("%s: risk stays readable" % _civ_big,
          len(json.dumps(_sf[1])) < 9000, "%d bytes" % len(json.dumps(_sf[1])))

# A hazard should report the harm it did to YOU, not the harm it would have
# done to somebody with something to lose: a tester with no staff and no money
# read "staff -45%, and 0 pence gone" three years running.
s = sim(civ="england_1300")
s.scholars = s.artisans = 0.0
s.employees = {}
s.capital = 0.0
s.year = 1348
s._shocks(1348)
_plague = [m for _y, m in s.log if "Black Death" in m]
check("a hazard that took nothing from you says so",
      not _plague or all("-45%" not in m or "nothing it could take" in m
                         for m in _plague),
      _plague)

# --- round 6, the England break tester ---------------------------------------
# 1. THE EXPLOIT THE VENTURE MODEL CREATED. `open` refused without supervisors
#    and then nothing ever looked again, so the tester hired five craftsmen,
#    opened eleven concerns in one turn, fired all six people and watched net
#    income RISE - seventeen concerns running against "EMPLOY: 0 people", and
#    the same loom still paying 435 a year in 1800 through the Black Death.
s = sim(civ="england_1300", capital=500000.0)
s.hire("artisan", 6)
_big = [k for k in NODES if 2000 <= NODES[k]["rev"] <= 9000][:4]
for _k in _big:
    s.done.add(_k)
s._done_changed()
_opened = [k for k in _big if s.open_venture(k)[0]]
_rev_staffed = s.revenue()
s.fire("artisan", 6)
s.step()
check("a concern nobody is left to watch stops trading",
      _opened and not s.operating and s.revenue() < _rev_staffed * 0.2,
      "revenue %.0f -> %.0f, still running %d"
      % (_rev_staffed, s.revenue(), len(s.operating)))
check("...and the game says which ones closed and why",
      any("nobody left to keep an eye on" in m for _y, m in s.log),
      [m for _y, m in s.log][-2:])

# 2. Failure risk fired correctly and announced nothing, so a tester watched
#    about 113 builds, expected nine failures and found no occurrence of
#    "fail", "abandon" or "lost" anywhere, and concluded the mechanic was dead.
s = sim(capital=5000000.0)
_risky = [k for k in NODES if NODES[k]["risk"] >= 0.15][:1][0]
_fails = 0
for _i in range(120):
    s.active[_risky] = dict(ph_left=0.0, yrs=99.0, spent=0.0, cost_left=0.0)
    s.done.discard(_risky)
    s._complete(_risky)
    if _risky in s.active:
        _fails += 1
        del s.active[_risky]
check("a failed attempt is announced, not silently absorbed",
      _fails > 0 and any("FAILED at" in m for _y, m in s.log),
      "%d failures in 120 at risk %.2f, logged %d"
      % (_fails, NODES[_risky]["risk"],
         sum(1 for _y, m in s.log if "FAILED at" in m)))

# 3. Three distinguishable refusals were themselves the tree: real-and-heard-of,
#    real-but-unheard-of, and nonexistent. Sixteen plain-English guesses
#    correctly classified ten real technologies and five invented ones.
_tri, _, _ = proto([{"cmd": "why", "id": "telescope"},
                    {"cmd": "why", "id": "zzzzznotathing"},
                    {"cmd": "why", "id": "dynamo"}],
                   civ="england_1300", fog=True)
_msgs = {(r.get("error") or "").split("Did you mean")[0].strip() for r in _tri}
check("a name you have not heard of and a name that does not exist read alike",
      len(_msgs) == 1, [m[:60] for m in _msgs])

# --- round 6, the England play tester ----------------------------------------
# 1. Bought people counted at full worth from the day of purchase, so the
#    training lag buy_slaves documents did nothing - and when a row finally
#    matured, step() added its capacity to self.artisans, which _resync_pools
#    then recomputed from scratch and threw away. A tester watched their
#    craftsmen fall from 35 to 3.8 at the moment the training finished.
s = sim(capital=500000.0)
s.done.add("workshop_first")
s.done.add("freedman_staff")
s._done_changed()
s.buy_slaves(12)
_at_purchase = s.artisans
for _ in range(4):
    s.step()
_trained = s.artisans
s.manumit(12)
s._resync_pools()
check("people you buy are worth nothing until they have learned the work",
      _at_purchase < 0.5, "%.2f craftsmen the day 12 were bought" % _at_purchase)
check("...and are worth something once they have, and do not vanish",
      _trained > 7.0, "%.2f craftsmen after the training lag" % _trained)
check("freeing them is worth more than holding them, as the model claims",
      s.artisans > _trained * 1.3,
      "%.2f held -> %.2f freed" % (_trained, s.artisans))

# 2. arithmetic_positional wants 2,500 scribe-hours a year against a national
#    ceiling of 1,321, and sat at "81% spent" from 1309 to about 1440. The
#    engine knows this at start time.
_imp, _, _ = proto([{"cmd": "start", "id": "arithmetic_positional"}],
                   civ="england_1300")
check("starting work this society cannot staff says so at the time",
      _imp[0].get("ok") is True and "cannot supply the labour" in (_imp[0].get("but") or ""),
      _imp[0].get("but"))

# 3. The stat that ends the run had no warning and no help topic.
s = sim(capital=400.0)
s.eminence = s.cfg["eminence_danger"] * 0.9
s.step()
check("becoming conspicuous is said out loud before it kills you",
      any("BECOMING CONSPICUOUS" in m for _y, m in s.log),
      [m for _y, m in s.log][-2:])
_he, _, _ = proto([{"cmd": "help", "topic": "eminence"}])
check("...and there is a help topic for it",
      "eminence" in json.dumps(_he[0]).lower() and "no such topic" not in json.dumps(_he[0]),
      list(_he[0])[:4])

# Money is counted in the money of the place, and in ONE name for it. A break
# tester read "needs about 1959 pence, you have 612 den" in a single sentence:
# one clause localised from the payload, the next from the renderer.
_cur, _ = _play(["state", "money", "quote mine coal 500", "quit"], civ="england_1300")
check("an English game is counted in pence and never in denarii",
      " den " not in _cur and "denarii" not in _cur and "pence" in _cur,
      [l for l in _cur.splitlines() if " den " in l or "denarii" in l][:2])
_cur2, _ = _play(["state", "quit"], civ="han_china_100ad")
check("a Han game is counted in cash",
      "cash" in _cur2 and "denarii" not in _cur2,
      [l for l in _cur2.splitlines() if "denarii" in l][:2])

# The help shows {"cmd":"labour","trade":"smith"}, so `labour trade smith` is
# the obvious typed reading of it - and was answered "no such trade: trade".
_syn, _ = _play(["available subject metallurgy", "labour trade smith", "quit"],
                civ="england_1300")
check("the typed form of what the help shows actually works",
      "no such trade: trade" not in _syn and "AVAILABLE: 0 startable" not in _syn,
      [l for l in _syn.splitlines() if "REFUSED" in l][:2])

# `ventures` fell through to the generic dump and printed lists of dicts as
# raw Python.
_vr, _ = _play(["ventures", "quit"], civ="england_1300")
check("ventures is rendered as a table, not as raw Python",
      "CONCERNS" in _vr and "{'id':" not in _vr and "{\"id\":" not in _vr,
      [l for l in _vr.splitlines() if "{'" in l][:2])

# effective_scholars() has always counted the founder as one of the scholars;
# nothing counted them as a pair of hands, though the premise of the game is a
# person who knows how every one of these things is made. workshop_first wants
# two craftsmen, so a Norse run that could field one could never build the
# place craftsmen work.
s = sim(civ="norse_900ad")
check("the founder is one of the craftsmen as well as one of the scholars",
      s.craft_hands_available() >= 1.0 and s.effective_scholars() >= 1.0,
      "%.1f hands, %.1f scholars, with nobody hired"
      % (s.craft_hands_available(), s.effective_scholars()))
s2 = sim(civ="norse_900ad")
for _p in NODES["workshop_first"]["pre"]:
    s2.done.add(_p)
s2._done_changed()
s2.hire("carpenter", 1)
check("...so one hired hand is enough to raise your first workshop",
      s2.start_reason("workshop_first")[0],
      s2.start_reason("workshop_first")[1])

# A break tester summed what the ledger listed - 7,101.9 - against a stated
# revenue of 6,738 and reported that the accounts do not add up. They were
# right: it showed the fifteen largest rows and nothing else, so smaller
# concerns, the workshop's own output, state funding and the market saturation
# that caps the whole figure were all invisible.
s = sim(civ="rome_100ad", manual=False)
for _ in range(120):
    s.step()
_src = s.revenue_sources()
check("the ledger's parts add up to the revenue it states",
      abs(sum(_src.values()) - s.revenue()) < 1.0,
      "rows %.1f against revenue %.1f" % (sum(_src.values()), s.revenue()))

# A play tester spent about eight years and 5,952 denarii working out that
# negative capital silently disables hiring and opening while both switches
# still read ON.
s = sim(civ="rome_100ad")
s.policy["auto_hire"] = True
s.policy["auto_open"] = True
s.capital = -500.0
_pol = S._agent_dispatch(s, NODES, {"cmd": "policy"})
check("a switch that is on but cannot act says so",
      set(_pol.get("switched_on_but_cannot_act_right_now") or {})
      >= {"auto_hire", "auto_open"},
      _pol.get("switched_on_but_cannot_act_right_now"))
check("...and says nothing when they all can",
      "switched_on_but_cannot_act_right_now" not in
      S._agent_dispatch(sim(capital=50000.0), NODES, {"cmd": "policy"}),
      "field present on a solvent household")

# `quote` existed because a tester went from 38,151 denarii to zero on one
# unpriced mine command. A break tester then spent 27,500 - 68% of capital -
# on `buy forest 100`, with no price shown and no way to ask for one.
_qf, _, _ = proto([{"cmd": "quote", "what": "forest", "n": 100},
                   {"cmd": "quote", "what": "slaves", "n": 5}], kit="equestrian")
check("you can ask the price of a forest before you buy one",
      _qf[0].get("ok") is True and _qf[0].get("to_buy_it", 0) > 0,
      _qf[0].get("error") or _qf[0].get("to_buy_it"))
check("...and of people",
      _qf[1].get("ok") is True and _qf[1].get("to_buy_them", 0) > 0,
      _qf[1].get("error") or _qf[1].get("to_buy_them"))
s = sim(capital=100000.0)
_before_f = s.capital
_quoted = _qf[0]["to_buy_it"]
s.buy_forest(100)
check("the quoted price of a forest is the price you are charged",
      abs((_before_f - s.capital) - _quoted) < 1.0,
      "quoted %.1f, charged %.1f" % (_quoted, _before_f - s.capital))

# A taught trade still read "does not exist yet" alongside "exists here: True".
_tn, _, _ = proto([{"cmd": "train", "trade": "machinist", "n": 2},
                   {"cmd": "labour", "trade": "machinist"}], kit="equestrian")
_row = (_tn[1].get("trade") or {})
check("a trade you taught does not still say it does not exist",
      _row.get("exists_here") is True
      and "does not exist yet" not in (_row.get("note") or ""),
      (_row.get("exists_here"), (_row.get("note") or "")[:60]))

# "Zero-cost nodes gate whole ages and are invisible... twice one of them was
# the only thing between me and a branch." The two digest lists deduplicated
# the wrong way round: the leverage column dropped anything that was also in
# the cheapest six, and the spine of this game is precisely the nodes that are
# both - free, zero-revenue, and holding up an age.
_dg, _, _ = proto([{"cmd": "available"}], fog=True)
_lev = [x["id"] for x in (_dg[0].get("most_rests_on_these") or [])]
check("the leverage column is not emptied by things being cheap",
      len(_lev) >= 4, _lev)
_by_reach = sorted(_lev, key=lambda k: -S.downstream_count(NODES, k))
check("...and it really is the highest-leverage work available",
      _lev and S.downstream_count(NODES, _lev[0]) >= 50,
      [(k, S.downstream_count(NODES, k)) for k in _lev])

# A break tester multiplied out the factors `why` shows for clock_pendulum,
# got 4,747.6 against a stated 4,834, and called it the one card in the game
# whose arithmetic does not work. It was: project_cost multiplies in the
# scarce-material premium and the breakdown never listed it. A breakdown that
# omits a factor is worse than no breakdown, because it invites this exact
# check and then fails it.
_bad_math = []
for _civ_m in ("england_1300", "rome_100ad", "norse_900ad"):
    _sm = sim(civ=_civ_m)
    for _k in ("clock_pendulum", "hot_air_balloon", "blast_furnace", "lens_grinding"):
        if _k not in NODES:
            continue
        _e = S._node_explain(_sm, NODES, _k)["cost"]
        _prod = (_e["base_total"] * _e["civ_domain_factor"]
                 * _e["material_distance_factor"] * _e["opposition_factor"]
                 * _e["scarce_material_premium"] * _e["price_index"])
        if abs(_prod - _e["total"]) > max(2.0, _e["total"] * 0.005):
            _bad_math.append((_civ_m, _k, round(_prod, 1), _e["total"]))
check("every cost breakdown multiplies out to the total it states",
      not _bad_math, _bad_math[:3])

# --- round 7, the Rome weird-play tester -------------------------------------
# 1. `money`'s Net/yr omitted interest on arrears, with the interest RATE
#    printed two lines below it on the same screen. They read "+9.5 a year"
#    while capital fell 105, then 117, accelerating - a household in a debt
#    spiral being told it was recovering.
s = sim(civ="rome_100ad")
s.capital = -3000.0
_m = S._agent_dispatch(s, NODES, {"cmd": "money"})
check("the net counts interest on arrears, which is a cost like any other",
      _m["net_per_year"] < 0 and _m["what_it_costs_you"]["interest_on_arrears"] > 0,
      "net %.1f with %.1f of interest"
      % (_m["net_per_year"], _m["what_it_costs_you"]["interest_on_arrears"]))

# 2. "Told to my face I could take 6 more people, I took 7 with a different
#    verb." buy went round the feed/house/oversee cap that hire enforces.
s = sim(capital=1000000.0)
_room = s.household_room()
_ok_over = s.buy_slaves(int(_room) + 5)
check("buying people obeys the same household cap as hiring them",
      _ok_over == 0 and s.slaves == 0,
      "room %.2f, bought %s" % (_room, _ok_over))
check("...and buying within it still works",
      s.buy_slaves(max(1, int(_room) - 1)) > 0, "room %.2f" % _room)

# 3. Ten people bought showed as "ON YOUR STAFF: nobody" and "EMPLOY: 0
#    people" while the prompt said art 7, and IN TRAINING printed the trade as
#    the literal string "None" in fractions.
_hh, _ = _play(["buy slaves 5", "labour", "quit"], civ="rome_100ad",
               extra=["--kit", "equestrian"])
check("people you own appear in your household, not as nobody",
      "people you own" in _hh, [l for l in _hh.splitlines() if "STAFF" in l][:2])
check("a training row without a trade is not printed as None",
      "None x" not in _hh and "None" not in _hh.split("IN TRAINING")[-1][:200],
      _hh.split("IN TRAINING")[-1][:120])

# 4. `step abc` silently advanced a year while step 0 and step -5 were refused.
_sa, _ = _play(["step abc", "state", "quit"], civ="rome_100ad")
check("a step that is not a number is refused, not silently taken as one",
      "not a number" in _sa and "YEAR 100" in _sa,
      [l for l in _sa.splitlines() if "YEAR" in l][:2])

# 5. "A site is sacked" took 62% of a tester's money, restarted every project
#    and cut their people nearly in half, and printed only those five words -
#    against a player who owned no sites. The plague family had already been
#    taught to report the harm it actually did; this one had not.
s = sim(civ="mexica_1500", capital=50000.0)
s.year = 1519
for _ in range(6):
    s._shocks(s.year)
    s.year += 1
_sacks = [m for _y, m in s.log if "sacked" in m]
check("a sacking says what it took from you",
      _sacks and ("taken" in _sacks[0] or "nothing it could take" in _sacks[0]),
      _sacks[:1])
s2 = sim(civ="mexica_1500", capital=0.0)
s2.year = 1519
for _ in range(6):
    s2._shocks(s2.year)
    s2.year += 1
_sacks2 = [m for _y, m in s2.log if "sacked" in m]
check("...and says so plainly when it took nothing",
      not _sacks2 or "nothing it could take" in _sacks2[0], _sacks2[:1])

# 6. `bribe` sells protection, protection decides whether strange work reads as
#    learning or as sorcery, and it appeared on no screen and in no help topic.
_pr, _ = _play(["state", "bribe 700", "state", "quit"],
               civ="rome_100ad", extra=["--kit", "equestrian"])
_lines = [l for l in _pr.splitlines() if "STANDING:" in l]
check("protection is on the screen that shows your standing",
      len(_lines) >= 2 and "protection" in _lines[0] and _lines[0] != _lines[1],
      _lines[:2])
_hp, _, _ = proto([{"cmd": "help", "topic": "protection"}])
check("...and has a help topic of its own",
      "no such topic" not in json.dumps(_hp[0]), list(_hp[0])[:3])

_shutil.rmtree(_loadtest_abs, ignore_errors=True)
_shutil.rmtree(os.path.join(ROOT, _PLAY_DIR), ignore_errors=True)

# =============================================================================
# FINDINGS_ROUND2 section Q: literacy bounds who you can hire.
# =============================================================================

# --- Q: a low-literacy society genuinely cannot hire scribes a high-literacy
# one can, at any price. This is the exact case the finding asked for: "if
# only 0.001% of the population can read... you can only hire 0.001%".
s_hi = sim(civ="rome_100ad", capital=1e9)
s_lo = sim(civ="norse_900ad", capital=1e9)
check("a low-literacy society's literate-trade pool is smaller than a "
      "high-literacy one's",
      s_lo.literate_capacity("scribe") < s_hi.literate_capacity("scribe"),
      "norse=%.2f rome=%.2f" % (s_lo.literate_capacity("scribe"),
                                s_hi.literate_capacity("scribe")))
ok_hi, why_hi = s_hi.hire("scribe", 3)
ok_lo, why_lo = s_lo.hire("scribe", 3)
check("money alone cannot hire scribes a low-literacy society has nobody to "
      "supply, at any price",
      ok_hi and not ok_lo and "literacy" in why_lo,
      "rome ok=%s / norse ok=%s (%s)" % (ok_hi, ok_lo, why_lo))

# --- Q: the same wall applies to TEACHING a trade into existence, the only
# way engineer/chemist/machinist/optician can ever exist at all (hire()
# refuses them outright until train() has made them real).
ok_lo, why_lo = sim(civ="norse_900ad", capital=1e9).train("machinist", 2)
check("a society that cannot read cannot be taught machinists into "
      "existence either",
      not ok_lo and "literacy" in why_lo, why_lo)
ok_hi, why_hi = sim(civ="rome_100ad", capital=1e9).train("machinist", 2)
check("the same teaching succeeds where enough people can read",
      ok_hi, why_hi)

# --- Q: the institutional scholar ceiling (staff_capacity, which is what
# auto_hire actually grows) is bounded by literacy_elite too, not only the
# named `scholar`/`scribe` trades hired one at a time.
s_hi = sim(civ="rome_100ad", capital=1e9); s_hi.done.add("school_founded")
s_lo = sim(civ="norse_900ad", capital=1e9); s_lo.done.add("school_founded")
sc_hi, sc_lo = s_hi.staff_capacity()[0], s_lo.staff_capacity()[0]
check("a school trains fewer scholars where fewer of the propertied class "
      "can read",
      sc_lo < sc_hi, "norse sc=%.2f rome sc=%.2f" % (sc_lo, sc_hi))

# --- Q: printing, schools and libraries WIDEN the pool -- the whole point --
# rather than raising a number nothing reads. Played out on Norse, where
# there is room for it to move; Rome starts at this file's own reference
# literacy and is not expected to move much.
s = sim(civ="norse_900ad", capital=1e9)
cap0 = s.literate_capacity("scribe")
s.apply_tech_effects("rag_paper")
s.apply_tech_effects("printing_press")
cap1 = s.literate_capacity("scribe")
# THRESHOLD CHANGED, deliberately, and the reason belongs here rather than in
# a commit message. This asserted cap1 > cap0 * 2, which was true of the
# original implementation because the pool was purely multiplicative: Norse
# elite literacy is a sixth of Rome's, so the ceiling came out at 0.2 people
# and printing multiplied a very small number. 0.2 people means "there is no
# such person in Scandinavia, at any price, ever", which is false about a
# society with rune-carvers who cut inscriptions for hire and, from the tenth
# century, priests who read Latin. The pool is now 1.5 findable people plus a
# literacy-scaled body on top, and no floor large enough to fix that falsehood
# can also leave room for a doubling. So the pair below pins both properties
# the mechanism actually needs, which is more than the single ratio did.
check("printing and paper widen the literate-trade hiring pool",
      cap1 > cap0 * 1.4, "before=%.2f after=%.2f" % (cap0, cap1))
check("a literate person can always be found, even before any teaching",
      cap0 >= 1.0, "norse scribe ceiling before teaching = %.2f" % cap0)

# =============================================================================
# FINDINGS_ROUND2 section R: the market responds to demand, and to supply.
# =============================================================================

# --- R: taking a large share of a trade's local supply raises what it costs
# (labour_price_factor), the same principle market_pressure already applies
# to slaves -- and it decays, the same way.
s = sim(civ="rome_100ad", capital=1e9)
f0 = s.labour_price_factor("millwright")
s._add_labour_pressure("millwright", 6 * s.HOURS_PER_PERSON_YEAR)
f1 = s.labour_price_factor("millwright")
check("leaning hard on a scarce trade's local supply raises what it costs",
      f1 > f0 * 1.5, "before=%.3f after=%.3f" % (f0, f1))
s.year += 5
f2 = s.labour_price_factor("millwright")
check("recent demand pressure decays: the same trade is not dearer forever",
      f2 < f1 and f2 < 1.3, "immediate=%.3f +5yr=%.3f" % (f1, f2))

# --- R: the SAME recent demand costs less once the trade's own supply is
# bigger -- this is "teaching fifty machinists is what makes hiring the
# fifty-first one cheap again", tested directly against pressure rather than
# waiting on a training run to mature.
thin = sim(civ="rome_100ad", capital=1e9)
thick = sim(civ="rome_100ad", capital=1e9)
thick.employees["millwright"] = 20.0
pressure_hours = 6 * thin.HOURS_PER_PERSON_YEAR
thin._add_labour_pressure("millwright", pressure_hours)
thick._add_labour_pressure("millwright", pressure_hours)
check("a bigger trained workforce in a trade makes the same recent demand "
      "cheaper to satisfy",
      thick.labour_price_factor("millwright") < thin.labour_price_factor("millwright"),
      "thin supply=%.3f thick supply=%.3f"
      % (thin.labour_price_factor("millwright"), thick.labour_price_factor("millwright")))

# --- R, end to end: hiring the same trade repeatedly through `hire` really
# does cost more each time, not only in the internal factor.
s = sim(civ="rome_100ad", capital=1e9)
s.done.update({"workshop_first", "school_founded", "academy_network", "patron_imperial"})
fees = []
for _ in range(3):
    before = s.capital
    ok, msg = s.hire("millwright", 10)
    if not ok:
        break
    fees.append(before - s.capital)
check("hire's own fee rises the more of a trade you have taken on recently",
      len(fees) == 3 and fees[-1] > fees[0] * 1.15, fees)

# --- R: materials respond to demand too -- MARKET_SHARE (economy.py) was a
# supply ceiling with no price response, so buying up to it cost the same
# per tonne as buying one kilogram. Saltpetre (MARKET_SHARE 0.0: no open
# market for it at all without a trade route) makes the effect dramatic;
# gunpowder is the cheapest node that needs it.
s = sim(civ="rome_100ad", capital=1e9)
s.active["gunpowder"] = {}
f_no_beds = s.material_price_factor("saltpetre")
check("demand for a material the market barely sells costs a real premium "
      "over the flat catalogue price",
      f_no_beds > 1.5, "%.3f" % f_no_beds)
s.nitre_bed_m2 = 2_000_000.0
f_with_beds = s.material_price_factor("saltpetre")
check("owning enough of your own supply (nitre beds) relieves the premium "
      "-- this is 'opening a mine lowers what iron costs you', generalised",
      f_with_beds < f_no_beds, "no beds=%.3f with beds=%.3f" % (f_no_beds, f_with_beds))

# --- R: the price response actually reaches the number the game quotes and
# charges (project_cost), not only an internal factor nothing reads.
s = sim(civ="rome_100ad", capital=1e9)
s.active["gunpowder"] = {}
cost_no_beds = s.project_cost("gunpowder")
s.nitre_bed_m2 = 2_000_000.0
cost_with_beds = s.project_cost("gunpowder")
check("project_cost itself falls once your own supply covers the demand",
      cost_with_beds < cost_no_beds * 0.6,
      "no beds=%.0f with beds=%.0f" % (cost_no_beds, cost_with_beds))

# --- refactor safety: resource_throttle()'s own quantity ceiling (unrelated
# to price, and pre-existing) is unchanged by factoring its material lookup
# out for material_price_factor() to share.
s = sim(civ="rome_100ad", capital=1e9)
s.active["gunpowder"] = {}
check("resource_throttle still throttles a material the market will not "
      "sell you at all",
      s.resource_throttle() < 1.0, s.resource_throttle())
s.nitre_bed_m2 = 2_000_000.0
check("...and stops once your own supply covers the need",
      s.resource_throttle() > 0.99, s.resource_throttle())

# --- COMMODITY FRAMEWORK (rome/data/world/COMMODITIES.md,
# rome/sim/engine/commodities.py). Standalone from Sim, so these checks
# build a CommodityLedger directly off commodities.json and the tech tree's
# NODES rather than going through `sim()`/`proto()`. See the design doc for
# what each claim below is meant to prove and why.

LED = COMMOD.CommodityLedger(nodes=NODES)

check("commodities.json defines the nine commodities the design doc promises",
      set(LED.commodities) == {"iron", "copper", "copper_wire", "coal", "gold",
                                "wool", "cloth", "cotton", "coffee"},
      sorted(LED.commodities))

# --- gold: a water pump and chemical extraction should compound, not just
# pick the better of the two, because they are independent improvements
# stacked on the same mine (COMMODITIES.md section 3, "multiplier" entries).
mult_none = LED.best_multiplier("gold", built=[])
mult_pump = LED.best_multiplier("gold", built=["met_mine_pumping"])
mult_both = LED.best_multiplier("gold", built=["met_mine_pumping", "mt2_cyanidation"])
check("a mine with a water pump and chemical extraction multiplies gold "
      "output by roughly the brief's own '20x' figure",
      19.0 <= mult_both <= 23.0, mult_both)
check("the two gold technologies compound rather than the model just taking "
      "the better of the two",
      mult_both > mult_pump > mult_none == 1.0,
      "none=%.1f pump=%.1f both=%.1f" % (mult_none, mult_pump, mult_both))

# --- cloth: automated looms make cloth more available, which drops its
# price, which makes a hot air balloon (400 kg of linen_kg) cheaper to build.
CLOTH_DEMAND_T = 20000.0
price_hand = LED.price("cloth", CLOTH_DEMAND_T, LED.market_available("cloth", built=[]))
price_power = LED.price("cloth", CLOTH_DEMAND_T, LED.market_available("cloth", built=["tex_power_loom"]))
check("a power loom makes cloth more available (higher national output) "
      "than the baseline loom, at the same demand",
      LED.country_output("cloth", ["tex_power_loom"]) > LED.country_output("cloth", []))
check("...which drops the market price of cloth, not just a premium on top "
      "of a flat floor (the thing economy.py's material_price_factor cannot do)",
      price_power < price_hand * 0.5,
      "hand loom=%.2f power loom=%.2f den/kg" % (price_hand, price_power))
balloon_linen_kg = NODES["hot_air_balloon"]["mat"]["linen_kg"]
cost_hand = balloon_linen_kg * price_hand
cost_power = balloon_linen_kg * price_power
check("...which makes the real hot_air_balloon node's linen bill cheaper "
      "to buy once the power loom exists",
      cost_power < cost_hand, "hand=%.0f power=%.0f denarii" % (cost_hand, cost_power))

# --- copper wire: the real test. A modest order is fully met; an industrial
# order of 'kilometres of copper wire' is not, and the shortfall is
# attributed to copper (the ore), not to copper_wire (the smiths' craft),
# even though copper_wire also comes up short -- this is the distinction a
# flat resource_throttle() cannot draw at all.
modest = LED.propagate_demand("copper_wire", 5.0, built=[])
check("a modest order of copper wire (5 t/yr) is fully met by the ordinary "
      "market for copper",
      modest["met_fraction"] > 0.999, modest["met_fraction"])

big = LED.propagate_demand("copper_wire", 500.0, built=[])
check("an industrial order for copper wire is NOT fully met: there is not "
      "enough copper being mined to meet the demand",
      big["met_fraction"] < 0.95, big["met_fraction"])
check("the shortfall is attributed to copper specifically, not to copper_wire "
      "-- the smiths' wire-drawing bench is not the bottleneck",
      LED.bottlenecks(big) == ["copper"], LED.bottlenecks(big))
check("copper_wire itself is NOT flagged as its own bottleneck: it only "
      "inherited the shortage from its input",
      big["bottleneck"] is None, big["bottleneck"])
check("copper_wire's own wire-drawing capacity is not, in fact, the "
      "constraint (it is far above what was asked)",
      big["own_capacity_t"] > big["requested_t"], big["own_capacity_t"])

fixed = LED.propagate_demand("copper_wire", 500.0, built=[],
                             own_production={"copper": 100.0})
check("opening your own copper mine (Sim.open_mine's real-world analogue) "
      "relieves the same industrial order",
      fixed["met_fraction"] > 0.999, fixed["met_fraction"])

# --- monopoly: you know where coffee grows and how to process it, so you
# sell it at a margin nobody can undercut, bounded by what a buyer's next
# best alternative would cost them.
sole = LED.monopoly_price("coffee", marginal_cost=2.0, alternative_price=None)
competitive = LED.monopoly_price("coffee", marginal_cost=2.0, alternative_price=2.4)
check("a sole supplier with no rival prices well above what a competitive "
      "market (many sellers, price near marginal cost) would charge",
      sole > competitive * 2, "sole=%.1f competitive=%.1f" % (sole, competitive))
undercut = LED.monopoly_price("coffee", marginal_cost=2.0, alternative_price=9.0)
check("...but never above what a buyer's next-best alternative would cost "
      "them, once one exists",
      undercut == 9.0, undercut)

# --- price never runs away in either direction, however extreme the ratio
# (price_floor_factor / price_ceiling_factor, COMMODITIES.md section 2).
c = LED.commodities["iron"]
base = c["base_price_denarii_per_kg"]
lo = LED.price("iron", demand_t=0.0001, supply_t=1e9)
hi = LED.price("iron", demand_t=1e9, supply_t=0.0001)
check("a total glut never prices a commodity below its floor",
      abs(lo - base * c["price_floor_factor"]) < 1e-6, lo)
check("a total shortage never prices a commodity above its ceiling",
      abs(hi - base * c["price_ceiling_factor"]) < 1e-6, hi)

rng = random.Random(3)
noisy = [LED.price_with_noise("iron", 2000.0, 2475.0, rng) for _ in range(200)]
check("fluctuation stays within the same floor/ceiling bounds over many draws",
      all(base * c["price_floor_factor"] - 1e-9 <= p <= base * c["price_ceiling_factor"] + 1e-9
          for p in noisy),
      (min(noisy), max(noisy)))
check("fluctuation actually varies year to year rather than being decorative",
      len(set(round(p, 4) for p in noisy)) > 50, len(set(noisy)))

# --- 'how much you have' is a stock, tracked separately from the flows
# above (COMMODITIES.md section 8): a minimal Ledger proves the distinction
# is representable even though Sim itself has no inventory today.
ledger = COMMOD.Ledger()
ledger.add("copper", 500.0)
taken = ledger.remove("copper", 800.0)
check("a stock ledger cannot be overdrawn: taking more than is on hand "
      "returns only what was actually there",
      taken == 500.0 and ledger.on_hand("copper") == 0.0,
      (taken, ledger.on_hand("copper")))

# ======================================================================
# ROUND 8: four fixes from the seventh break-testing round.
# ======================================================================

# --- BREAK: when the staff ran short, the closer picked the concern that
# needed the MOST hands, which is very nearly the same as picking the most
# profitable one. A tester watched a 600-a-year wagon shop close twice while a
# concern earning nothing and staffed identically stayed open.
s_cl = sim(capital=200000.0)
_pair = [k for k in NODES
         if NODES[k]["rev"] > 0 and NODES[k]["up"] >= 0 and not NODES[k]["pre"]]
s_cl.done.update(NODES)                 # know everything, so `open` is free
s_cl.operating = set()
_rich = max(NODES, key=lambda k: NODES[k]["rev"] - NODES[k]["up"])
_poor = min((k for k in NODES if NODES[k]["rev"] > 0),
            key=lambda k: NODES[k]["rev"] - NODES[k]["up"])
s_cl.operating.update([_rich, _poor])
s_cl.scholars = s_cl.artisans = 0
s_cl.founder_alive = False              # nobody at all: it must close both,
_shut = s_cl.close_unstaffed_ventures(200)      # and in the right ORDER
check("an unstaffed shutdown closes the least valuable concern first",
      _shut[0] == _poor, (_shut[:2], _rich, _poor))
check("...and keeps going until the payroll actually covers what is left",
      not s_cl.operating, sorted(s_cl.operating)[:4])
check("...and what it closed is still KNOWN, only stopped",
      _rich in s_cl.done and _rich in s_cl.mothballed)

# --- BREAK: player-facing hazard notes quoted the values vector by its
# internal names ("raises w_magic_fear"), which is engine jargon a player has
# no way to read. Nothing shown to a player may name a values-vector key.
_JARGON = ("w_magic_fear", "w_eminence_danger", "w_religious_rigidity",
           "w_labour_saving", "w_commerce", "w_information", "w_novelty",
           "w_military", "adaptation_rate", "patronage_weight", "bribability")
_dirty = []
for _f in sorted(os.listdir(os.path.join(ROOT, "rome/data/civilizations"))):
    if not _f.endswith(".json") or _f.startswith("_"):
        continue
    _civ = json.load(open(os.path.join(ROOT, "rome/data/civilizations", _f)))
    for _h in _civ.get("hazards", []):
        _txt = " ".join(str(_h.get(x, "")) for x in ("name", "note"))
        _dirty += [(_f, _h.get("name"), _j) for _j in _JARGON if _j in _txt]
check("no hazard a player reads names an internal values-vector key",
      not _dirty, _dirty[:3])

# --- BREAK: `risk` offered `horse_collar` as a hedge against the Antonine
# plague with no word of why. Every entry must say what it leads to.
s_hz = sim()
_steps = []
for _kind in sorted(S.Sim.HAZARD_COUNTERS):
    _steps += s_hz.hedge_first_steps(_kind)
check("every hedge the game suggests says what it gets you",
      _steps and all(e.get("because_it_gives_you") for e in _steps),
      [e["id"] for e in _steps if not e.get("because_it_gives_you")][:3])
check("...and a prerequisite says which counter it is a step toward",
      any(str(e["because_it_gives_you"]).startswith("a step toward")
          for e in _steps))

# --- BREAK: a save written with the fog OFF loaded into a fogged game and
# handed the player the whole tree. The check has to run BEFORE the save's own
# fog flag is restored, or it validates the value it is about to reject.
_sv = "_fogtamper_test.json"          # saves must be relative paths
_svp = os.path.join(ROOT, _sv)
if os.path.exists(_svp):
    os.remove(_svp)
proto([{"cmd": "save", "file": _sv}])                       # written unfogged
_r8, _out8, _rc8 = proto([{"cmd": "load", "file": _sv}, {"cmd": "state"}],
                         fog=True)
check("a save played without fog cannot be loaded into a fogged game",
      any("fog" in json.dumps(x).lower() and x.get("ok") is False for x in _r8),
      _out8[:200])
check("...and refusing it does not kill the session", _rc8 == 0)
if os.path.exists(_svp):
    os.remove(_svp)

# ======================================================================
# ROUND 8b: the game saying what it did, and two attribute-level defects.
# ======================================================================

# --- BREAK: the patron-death guard read `_last_patron_death` and the body set
# `last_patron_death`, so the 25-year cooling-off never applied and the 5%
# roll fired every year for ever - the exact bug its comment claims to fix.
s_pd = sim(capital=50000.0, events=True)
s_pd.done.add("patron_local"); s_pd._done_changed()
s_pd.rng = random.Random(4)
_deaths = []
for _y in range(100, 400):
    s_pd.year = _y
    _before = len(s_pd.log)
    s_pd._random_events(_y)
    _deaths += [m for _, m in s_pd.log[_before:] if "patron dies" in m]
check("a patron cannot die twice inside the cooling-off period",
      len(_deaths) <= 300 // 25 + 1,
      "%d deaths in 300 years" % len(_deaths))
_years = [y for y, m in s_pd.log if "patron dies" in m]
check("...and the gap between them is at least the 25 years it promises",
      all(b - a > 25 for a, b in zip(_years, _years[1:])), _years)
check("a patron's death names what it cost you",
      not _years or any("courting cost" in m and "protection falls" in m
                        for _, m in s_pd.log if "patron dies" in m),
      [m for _, m in s_pd.log if "patron dies" in m][:1])

# --- BREAK: a fire and a raid announced themselves and left the player to
# diff their own state to find out whether anything had happened.
s_fx = sim(capital=10000.0, events=True)
s_fx.rng = random.Random(7)
for _y in range(100, 200):
    s_fx.year = _y
    s_fx._random_events(_y)
_dis = [m for _, m in s_fx.log if "fire in" in m or "banditry" in m]
check("a fire or a raid says what it took",
      _dis and all("denarii" in m or "holding none" in m for m in _dis),
      _dis[:2])

# --- BREAK: shed_loss_makers scanned `done`, so it could unlearn a concern
# that was already shut - saving nothing, since upkeep follows `operating`.
# (The positive cases are checked in round two, section C.)

# --- BREAK: auto_open threw away every refusal open_venture handed it, so a
# concern earning 150 against 15 of upkeep sat shut for six years in silence.
s_ao = sim(capital=1.0)
# Dear to open and plainly worth opening: auto_open must refuse it and SAY SO.
_v = max((k for k in NODES if NODES[k]["rev"] > NODES[k]["up"] > 0),
         key=lambda k: NODES[k]["rev"] - NODES[k]["up"])
s_ao.done.add(_v); s_ao._done_changed()
_opened = s_ao.auto_open_ventures()
check("auto_open opens nothing it cannot pay the capex on",
      _v not in _opened, (_v, _opened[:3]))
check("auto_open says why the best concern is still shut",
      any(_v in m for _, m in s_ao.log), [m for _, m in s_ao.log][:2])

# --- BREAK: `buy nitre`. Saltpetre is made, not mined, and there was no
# command that made any: only step(), which took 5% of a MANUAL player's
# capital every year they were short, silently.
s_ni = sim(capital=100000.0)
_laid = s_ni.build_nitre(20000)
check("nitre beds can be laid by hand, and cost what the quote says",
      _laid == 20000 and abs(s_ni.capital
                             - (100000.0 - 20000 * s_ni.NITRE_COST_PER_M2
                                * s_ni.price_index)) < 1e-6,
      (_laid, s_ni.capital))
check("...and they actually supply saltpetre",
      s_ni._own_material_supply("nitre") > 0, s_ni._own_material_supply("nitre"))
s_ni2 = sim(capital=10.0)
check("...and one you cannot afford changes nothing at all",
      s_ni2.build_nitre(20000) == 0.0 and s_ni2.nitre_bed_m2 == 0.0
      and s_ni2.capital == 10.0,
      (s_ni2.nitre_bed_m2, s_ni2.capital))
_r_ni, _, _ = proto([{"cmd": "quote", "what": "nitre", "n": 20000},
                     {"cmd": "buy", "what": "nitre", "n": 20000},
                     {"cmd": "buy", "what": "nitre", "n": -1}])
check("the nitre quote and the nitre purchase agree on the price",
      _r_ni[0].get("to_lay_it") is not None
      and _r_ni[1].get("ok") is False,        # 400 denarii cannot buy 40,000
      (_r_ni[0].get("to_lay_it"), _r_ni[1].get("error")))
check("a negative nitre order is refused, not credited",
      _r_ni[2].get("ok") is False, _r_ni[2])

# --- BREAK: a MANUAL player's capital was spent on nitre beds by step().
s_mn = sim(capital=100000.0, manual=True)
s_mn.binding = "saltpetre"
_cap_before = s_mn.capital
s_mn.policy["auto_mine"] = False
for _ in range(3):
    s_mn.step()
check("with the automatic policies off, nothing lays a nitre bed but you",
      s_mn.nitre_bed_m2 == 0.0, s_mn.nitre_bed_m2)

# --- BREAK: "SHORT OF SALTPETRE: work at 5% of plan" for thirty years, with
# no way to find out what saltpetre was for or what would fix it.
s_rm = sim(capital=100000.0)
for _b in ("charcoal", "saltpetre", "iron"):
    _msg = s_rm.shortage_remedy(_b)
    check("a %s shortage names a command that would end it" % _b,
          "buy " in _msg or "quote " in _msg, _msg[:80])

# --- BREAK: the practice paid a third of the quoted figure with nothing
# anywhere saying so, because a granted node has no done_year and the revenue
# ramp pinned it at step one of three for ever. It is now a named constant,
# and the arithmetic is unchanged.
s_pr = sim()
_prac = sorted(s_pr._practice_set())
_expect = sum(NODES[k]["rev"] for k in _prac) * s_pr.PRACTICE_SHARE
check("the practice pays its share of the quoted figure, not a ramp step",
      abs(s_pr.revenue() - _expect) < 0.5, (s_pr.revenue(), _expect))
s_pr5 = sim()
for _ in range(6):
    s_pr5.step()
check("...and it does not grow into the full figure over the ramp years",
      abs(s_pr5.revenue() - _expect) < 0.5, (s_pr5.revenue(), _expect))
check("the ledger says why the practice pays less than the tree quotes",
      s_pr.practice_note() and "a third" in s_pr.practice_note(),
      s_pr.practice_note())
check("a concern you opened is NOT described as your practice",
      all(k in s_pr.granted for k in _prac), _prac[:3])

# --- BREAK: `available` carried nine numbers and not one of them was the
# staff, so six projects picked on cost and hours all waited on people.
s_av = sim()
_av, _, _ = proto([{"cmd": "available", "find": "flax"}])
_rows = _av[0].get("available") or []
check("available says what standing staff a project needs",
      _rows and any(r.get("needs_staff") for r in _rows),
      [(r["id"], r.get("needs_staff")) for r in _rows][:3])
# The marker uses the SAME measure the gate uses - the founder's own hands and
# anything under contract included - so on turn one, when the founder can do a
# one-craftsman job themselves, nothing is starred. A break tester read "* means
# the work waits" beside projects that built at full speed with nobody hired.
from engine.protocol import _short_of_staff
_s_star = sim()
check("...and marks exactly the ones the start gate would refuse for staff",
      all(bool(r.get("short_of_staff"))
          == (NODES[r["id"]]["art"] > _s_star.craft_hands_available() + 1e-9
              or NODES[r["id"]]["sch"] > _s_star.effective_scholars() + 1e-9)
          for r in _rows),
      [(r["id"], r.get("short_of_staff"), NODES[r["id"]]["art"],
        _s_star.craft_hands_available()) for r in _rows][:3])
_big = [k for k in sorted(NODES) if NODES[k]["art"] > 20][:1]
if _big:
    check("...and a job wanting twenty craftsmen IS starred on turn one",
          _short_of_staff(_s_star, NODES[_big[0]]), _big[0])
_av2, _, _ = proto([{"cmd": "available", "find": "zzzznosuchthing"}])
check("a search that matches nothing says so instead of printing '1-0'",
      _av2[0].get("nothing_matched") and "1-0" not in str(_av2[0].get("showing")),
      _av2[0].get("showing"))
from engine.protocol import render_pretty as _RP
_pretty = _RP("available", _av2[0])
check("...and the empty result prints no column headings over no rows",
      "COST" not in _pretty and "matches" in _pretty, _pretty[:120])

# --- BREAK: with knowing and running split apart, nothing said which one a
# prerequisite wants.
# One node with its prerequisites met, one without: both have to say which
# state a prerequisite wants, since knowing and running became separate.
_wy, _, _ = proto([{"cmd": "why", "id": "horse_collar"},
                   {"cmd": "why", "id": "point_contact_transistor"}])
_wp = "\n".join(_RP("why", x) for x in _wy)
check("why states that a prerequisite must be finished, and stays finished",
      "FINISHED" in _wp or "finished counts for ever" in _wp,
      [l for l in _wp.splitlines() if "PREREQ" in l][:3])

# --- BREAK: a debasement announced itself and moved no price a player could
# see, because the model is in real terms. Say so, and name the real bite.
s_db = sim(capital=100000.0, events=True)
_before_price = s_db.project_cost("horse_collar")
while s_db.year < 210:
    s_db.step()
check("debasement does not move a real price quote (the model is real terms)",
      abs(s_db.project_cost("horse_collar") - _before_price) < 1e-6,
      (_before_price, s_db.project_cost("horse_collar")))
_dbm = [m for _, m in s_db.log if "coin is worth" in m]
check("...and the announcement says so, rather than leaving it to be found",
      _dbm and "do not move" in _dbm[0] and "your chest" in _dbm[0],
      _dbm[:1])
check("...and names what the debasement actually took this year",
      _dbm and ("denarii" in _dbm[0] or "holding none" in _dbm[0]), _dbm[:1])


# ======================================================================
# ROUND 8c: eminence had no lever, and "chance of ruin" was not the chance
# of ruin. Both play testers died to it and both described it the same way.
# ======================================================================

def _big(rep=98.0, em=39.0, yr=250, cap=5000000.0):
    s_ = sim(capital=cap)
    s_.done.update(list(NODES)[:1400]); s_._done_changed()
    s_.reputation, s_.eminence, s_.year = rep, em, yr
    return s_

_em = _big()
_rep0, _em0 = _em.reputation, _em.eminence
_ok_w, _why_w = _em.withdraw_from_public_life()
check("there is a command that lowers prominence the year you use it",
      _ok_w and _em.eminence < _em0 * 0.6, (_em0, _em.eminence))
check("...and its price is reputation, not money",
      _em.reputation < _rep0 - 5 and abs(_em.capital - 5000000.0) < 1e-6,
      (_rep0, _em.reputation, _em.capital))
check("...but never below what the work you built is worth on its own",
      _em.reputation >= _em.standing_floor() - 1e-6,
      (_em.reputation, _em.standing_floor()))
check("...and it cannot be done twice in a decade",
      _em.withdraw_from_public_life()[0] is False,
      _em.withdraw_from_public_life()[1])
_em2 = _big()
_em2.year += _em2.WITHDRAW_EVERY + 1
check("...and can be done again once enough years have passed",
      _em2.withdraw_from_public_life()[0], _em2.year)

# It must not take the price when there is nothing to buy - the same rule
# `bribe` learned the hard way.
_quiet = _big(rep=40.0, em=1.0)
_rq = _quiet.reputation
check("withdrawing when nobody is watching is refused, not charged",
      _quiet.withdraw_from_public_life()[0] is False
      and _quiet.reputation == _rq,
      (_quiet.reputation, _rq))

# The settling point was ABOVE the danger line, which is a promise that a
# successful run dies. Familiarity - the model's own measure of how
# unsurprising you have become - now damps it.
_fam = _big()
_fam.familiarity = 0.0
_cold = _fam.prominence_hazard()
_fam.familiarity = 0.9
_warm = _fam.prominence_hazard()
check("a city that has watched you for a century is less alarmed by you",
      _warm < _cold * 0.92, (_cold, _warm))
# A sixth off, not a third: the first attempt at this damping took the hazard
# so far down that a break tester measured three thousand run-years with the
# sum of every reported chance of ruin at exactly 0.00.
check("...but never stops being alarmed altogether",
      _warm > _cold * 0.8, (_cold, _warm))
# The shape that matters: build the counter and you sit under the line;
# do not and you sit well over it.
_em_shape = {}
for _acad in (False, True):
    _s = sim(capital=50000000.0)
    _s.done.update(list(NODES)[:1400]); _s.done.add("patron_imperial")
    if not _acad:
        _s.done.discard("academy_network")
    _s._done_changed()
    _s.reputation, _s.year, _s.familiarity = 98.0, 400, 0.9
    _em_shape[_acad] = _s.eminence_report()["settles_at_if_nothing_changes"]
check("a great man near the throne who built no academies is over the line",
      _em_shape[False] > sim().cfg["eminence_danger"], _em_shape)
check("...and the same man who built them is under it",
      _em_shape[True] < sim().cfg["eminence_danger"], _em_shape)

# "7% chance of ruin" was the chance SOMETHING landed; four fifths of those
# are survivable. A play tester survived two and was ended by the third.
_rep = _big().eminence_report()
check("the report separates 'something happens' from 'the run ends'",
      _rep["chance_the_run_ENDS_this_year"] < _rep["chance_of_ruin_this_year"],
      (_rep["chance_of_ruin_this_year"], _rep["chance_the_run_ENDS_this_year"]))
check("...and says which outcomes there are and how likely each is",
      abs(sum(_rep["if_it_lands_it_is"].values()) - 1.0) < 1e-9,
      _rep["if_it_lands_it_is"])
check("...and names the lever, by the word you would type",
      "withdraw" in str(_rep["the_one_lever"]), _rep["the_one_lever"])

# It has to survive a save, or a --session game gets a free retirement a year.
_wsv = "_withdrawtest.json"
_wsvp = os.path.join(ROOT, _wsv)
if os.path.exists(_wsvp):
    os.remove(_wsvp)
_rw, _, _ = proto([{"cmd": "withdraw"}, {"cmd": "save", "file": _wsv},
                   {"cmd": "load", "file": _wsv}, {"cmd": "withdraw"}])
check("a retirement cannot be repeated by saving and reloading",
      _rw[-1].get("ok") is False, _rw[-1])
if os.path.exists(_wsvp):
    os.remove(_wsvp)


# ======================================================================
# ROUND 8d: things the game said that were not true, and levers it lacked.
# ======================================================================

# --- BREAK: "waiting on money" while holding 73,234,107 denarii against
# 45,448 owed. step() pays at most one year's instalment - the cost over the
# node's calendar floor - so a ten-year work absorbs a tenth a year however
# rich you are, and nothing anywhere said there was a pace at all.
from engine.protocol import _waiting_on as _WO
s_pace = sim(capital=50000000.0)
_slow = "academy_network"
s_pace.active[_slow] = dict(ph_left=0.0, yrs=1.0, spent=0.0,
                            cost_left=s_pace.project_cost(_slow))
_msg_rich = _WO(s_pace, NODES, _slow, s_pace.active[_slow],
                s_pace.active[_slow]["cost_left"])
check("a rich player is told the pace, not that they are short of money",
      "pace" in _msg_rich and "a year" in _msg_rich, _msg_rich)
check("...and is told how many more years that pace needs",
      "year" in _msg_rich and any(c.isdigit() for c in _msg_rich), _msg_rich)
s_broke = sim(capital=1.0)
s_broke.credit_limit = lambda: 0.0
s_broke.active[_slow] = dict(ph_left=0.0, yrs=1.0, spent=0.0,
                             cost_left=s_broke.project_cost(_slow))
_msg_poor = _WO(s_broke, NODES, _slow, s_broke.active[_slow],
                s_broke.active[_slow]["cost_left"])
check("...and a player who really cannot raise the instalment is told that",
      _msg_poor.startswith("money"), _msg_poor)

# --- BREAK: auto_train started engineers, chemists AND machinists against a
# thinner revenue than their wages, and turning the policy off did not stop
# what was in flight. No command anywhere could.
s_tr = sim(capital=200000.0)
ok_t, _ = s_tr.train("machinist", 3)
check("teaching a trade puts people in training", ok_t and s_tr.training, s_tr.training)
ok_f, note_f = s_tr.fire("machinist", 3)
check("dismissing a trade you are teaching cancels the apprenticeship",
      ok_f and not [r for r in s_tr.training if len(r) > 3 and r[2] == "machinist"],
      (note_f, s_tr.training))
check("...and says so, because what you paid to feed them is spent",
      note_f and "stopped teaching" in note_f, note_f)
s_tr2 = sim(capital=200000.0)
check("firing a trade you neither employ nor teach is still refused",
      s_tr2.fire("machinist", 1)[0] is False, s_tr2.fire("machinist", 1)[1])

# --- BREAK: `work` silently took the hours out of the practice. 500 hours as
# a scribe paid 80.1 and cost 58.3 of practice income the same instant.
_rw, _, _ = proto([{"cmd": "work", "trade": "scribe", "hours": 500}])
check("selling your hours says what it cost your own practice",
      _rw[0].get("it_cost_your_own_practice", 0) > 0.5, _rw[0])
check("...and says what you are actually up on the trade",
      abs((_rw[0]["earned"] - _rw[0]["it_cost_your_own_practice"])
          - _rw[0]["so_you_are_up"]) < 0.11, _rw[0])

# --- BREAK: the run ended with one sentence and then a queue of identical
# refusals. A play tester started a whole second game with the fog off just to
# learn how far along the road they had died.
s_fin = sim()
s_fin.year = 600
from engine.protocol import final_report as _FRPT, render_final as _RF
_fr = _FRPT(s_fin, NODES)
check("the end of a run reports how far along the road it got",
      _fr.get("the_whole_road_was", 0) > 100
      and _fr.get("still_to_build_when_it_ended") is not None, _fr.get("the_goal"))
check("...and names the steps that would have come next",
      len(_fr.get("the_next_things_would_have_been") or []) > 0,
      _fr.get("the_next_things_would_have_been"))
check("...and renders as a page, not a dict dump",
      "THE RUN IS OVER" in _RF(_fr) and "{" not in _RF(_fr), _RF(_fr)[:80])

# --- BREAK: `help money` and `help economy` printed the same page, and both
# were listed as separate topics.
_hm, _, _ = proto([{"cmd": "help", "topic": "money"},
                   {"cmd": "help", "topic": "economy"}])
check("help money and help economy are not the same page",
      json.dumps(_hm[0]) != json.dumps(_hm[1]),
      list((_hm[0].get("help") or {}).keys())[:3])
check("...and help money explains why the practice pays a third",
      "third" in json.dumps(_hm[0]), json.dumps(_hm[0])[:120])

# --- BREAK: `available "power and precision"` matched nothing while the
# unquoted form worked, and said nothing about why.
_aq, _, _ = proto([{"cmd": "available", "subject": '"power and precision"'},
                   {"cmd": "available", "subject": "power and precision"}])
check("a quoted subject means the same as an unquoted one",
      _aq[0].get("count") == _aq[1].get("count") and _aq[0].get("count", 0) > 0,
      (_aq[0].get("count"), _aq[1].get("count")))

# --- BREAK: HEARD OF was a silent slice at 25 in a game with a thousand nodes
# in play: no note that it was cut, and no way to see the rest.
s_h = sim()
s_h.fog = True
s_h.done.update(list(NODES)[:900]); s_h._done_changed()
for _k in list(NODES)[:900]:
    s_h.reveal_from(_k)
_p1 = S._agent_available(s_h, NODES, {})
_p2 = S._agent_available(s_h, NODES, {"heard_offset": 25})
check("a truncated 'heard of' list says it was truncated",
      _p1.get("and_more_you_have_heard_of"), _p1.get("and_more_you_have_heard_of"))
check("...and can be paged through",
      _p2.get("heard_of_but_cannot_begin")
      and not ({x["id"] for x in _p1["heard_of_but_cannot_begin"]}
               & {x["id"] for x in _p2["heard_of_but_cannot_begin"]}),
      len(_p2.get("heard_of_but_cannot_begin") or []))

# --- BREAK: `_TECH_EFFECTS` offered as a playable civilisation.
_civerr = ""
try:
    S.load_civ("rome")
except SystemExit as e:
    _civerr = str(e)
check("the reference data files are not offered as civilisations to play",
      "_TECH_EFFECTS" not in _civerr and "rome_100ad" in _civerr, _civerr)


# --- BREAK: the Mexica menu says "no draught animals, no iron, no wheel in
# practical use" and horse_collar was startable on arrival in the Valley of
# Mexico in 1500, with `why` still calling it a collar for a draught horse.
_mex = sim(civ="mexica_1500")
_HORSE = "horse_collar"
_ok_h, _why_h = _mex.start_reason(_HORSE)
check("a society with no draught animal cannot begin draught-animal work",
      not _ok_h and "draught animal" in _why_h, _why_h)
check("...and the refusal names the one thing that would open it",
      "exp_import_draught_animals" in _why_h, _why_h)
check("...and it is not in what you could begin today",
      not any(e["id"] == _HORSE
              for e in S._agent_available(_mex, NODES, {"all": True})["available"]),
      _HORSE)
_mex.done.add("exp_import_draught_animals"); _mex._done_changed()
check("...and bringing the animals across opens all of it at once",
      _mex.needs_first(_HORSE)[0] is None, _mex.needs_first(_HORSE))
_rom = sim(civ="rome_100ad")
check("a society that HAS horses is not gated at all (the control case)",
      _rom.needs_first(_HORSE)[0] is None, _rom.needs_first(_HORSE))
# Every gate has to be liftable, or it is a wall rather than a handicap.
for _cf in sorted(os.listdir(os.path.join(ROOT, "rome/data/civilizations"))):
    if not _cf.endswith(".json") or _cf.startswith("_"):
        continue
    _cv = json.load(open(os.path.join(ROOT, "rome/data/civilizations", _cf)))
    for _lbl, _ent in (_cv.get("needs_first") or {}).items():
        if _lbl.startswith("_"):
            continue
        check("%s: the '%s' gate names a real node that lifts it"
              % (_cv["id"], _lbl),
              _ent.get("node") in NODES and _ent["node"] not in (_ent.get("ids") or []),
              _ent.get("node"))
        check("%s: every id behind the '%s' gate is a real node"
              % (_cv["id"], _lbl),
              all(x in NODES for x in (_ent.get("ids") or [])),
              [x for x in (_ent.get("ids") or []) if x not in NODES])


# ======================================================================
# ROUND 8e: three answers to "can I afford this", and advice you cannot take.
# ======================================================================

s_af = sim(capital=400.0)
check("there is ONE affordability rule, and it says which it is using",
      abs(s_af.spending_power("buy") - (400.0 + s_af.credit_limit() * 0.5)) < 1e-6
      and abs(s_af.spending_power("start") - (400.0 + s_af.credit_limit())) < 1e-6,
      (s_af.spending_power("buy"), s_af.spending_power("start")))
_q, _, _ = proto([{"cmd": "quote", "what": "mine", "material": "coal", "n": 500},
                  {"cmd": "available"}])
check("quote counts the credit a lender would actually advance",
      _q[0].get("you_could_raise", 0) > _q[0].get("you_have", 0), _q[0].get("you_could_raise"))
check("...and says what its 'afford' figure means",
      "credit" in str(_q[0].get("afford_means")), _q[0].get("afford_means"))
_hint = str((_q[1].get("to_see_more") or {}).get("what you can pay for", ""))
check("the AFFORD hint uses the rule `start` uses, since it is about starting",
      str(int(sim(capital=400.0).spending_power("start"))).replace(",", "")
      in _hint.replace(",", ""), _hint)

# --- BREAK: the arrears banner quoted 46 a year against a ledger Net/yr of
# -159.5, because it left out the interest that exists BECAUSE of the arrears.
s_ar = sim(capital=-4000.0)
s_ar.insolvent_years = 20
s_ar.revenue = lambda: 0.0
_diag = s_ar.stall_diagnosis()
_led = (s_ar.revenue() - s_ar.upkeep() - s_ar.living_cost()
        - s_ar.mine_operating_cost()
        - max(0.0, -s_ar.capital) * s_ar.debt_interest_rate())
check("the arrears banner quotes the same loss the ledger does",
      _diag and "{:,.0f}".format(-_led) in _diag["you_are_stuck"],
      (_diag or {}).get("you_are_stuck"))
check("...and names the part of it that is interest on the arrears themselves",
      any("interest on the arrears" in w for w in _diag["what_would_change_it"]),
      _diag["what_would_change_it"])

# --- BREAK: the banner recommended wage work, and `work` answered the player
# who took it with "this cost you 50. Wage work is for when you have no
# practice to lose." The game recommended a mistake and then named it as one.
s_w = sim(capital=-4000.0)
s_w.insolvent_years = 20
_dw = s_w.stall_diagnosis()
_wages = [w for w in (_dw or {}).get("what_would_change_it", [])
          if w.startswith("work as a ")]
if _wages:
    _trade = _wages[0].split("work as a ")[1].split(":")[0].strip()
    _pay, _note = sim(capital=-4000.0).work_for_wages(_trade, 2000)
    check("the trade the banner names is one that actually gains",
          not (_note and "cost you" in _note), (_trade, _note))
else:
    check("the banner does not recommend wage work when it would lose money",
          True, "not offered")

# --- BREAK: at the horizon the banner still said "it is escapable ... work for
# wages", and every action it named was refused with "the run has ended".
s_end = sim()
s_end.year = 9999
check("a finished run is not given advice it will refuse to act on",
      S._agent_state(s_end, NODES).get("stuck") is None,
      S._agent_state(s_end, NODES).get("stuck"))

# --- BREAK: `why` on a mistyped id suggested; `open` said "no such node".
_ro, _, _ = proto([{"cmd": "open", "id": "fin_pawnshopp"}])
check("open on a mistyped id suggests, the way why does",
      "did you mean" in (_ro[0].get("error") or ""), _ro[0].get("error"))

# --- BREAK: "hiring 1e+21 smiths costs 281250000000000012058624 denarii".
_rn, _, _ = proto([{"cmd": "hire", "trade": "smith", "n": 1e21},
                   {"cmd": "buy", "what": "forest", "n": 1e30},
                   {"cmd": "buy", "what": "forest", "n": 3}])
check("an absurd quantity is refused as absurd, not priced in scientific notation",
      all("e+" not in (r.get("error") or "") for r in _rn[:2])
      and all(r.get("ok") is False for r in _rn[:2]),
      [r.get("error", "")[:60] for r in _rn[:2]])
check("...and an ordinary quantity still goes through the same reader",
      _rn[2].get("ok") is not None, _rn[2])

# --- BREAK: an idle million bled 15,000 a year with nothing anywhere saying why.
_rr, _, _ = proto([{"cmd": "money"}], kit="absurd")
check("the ledger names the part of your living costs that is your wealth",
      (_rr[0].get("what_it_costs_you") or {}).get("_of_which_because_you_are_rich", 0) > 1000,
      _rr[0].get("what_it_costs_you"))

# --- BREAK: `path` after a sack never mentioned the one verb that would move
# the player on, and a run driven mechanically from it sat stuck for 140 years.
s_pth = sim()
s_pth.done.add("lead_chamber"); s_pth._done_changed()
s_pth.mothballed.add("lead_chamber")
_rp = S._agent_dispatch(s_pth, NODES, {"cmd": "path", "id": GOAL})
check("path names what on the route is shut rather than unbuilt",
      "lead_chamber" in (_rp.get("on_this_route_but_shut_down") or []),
      _rp.get("on_this_route_but_shut_down"))
check("...and names restore, which is the verb that reopens it",
      "restore" in str(_rp.get("reopen_them_with")), _rp.get("reopen_them_with"))


# ======================================================================
# ROUND 8f: screens that disagreed with each other.
# ======================================================================

# --- BREAK: "(these add up to the revenue above)" - 166.7 + 66.7 = 233.4
# under a stated 233.5. A claim of exact addition, checkable in one line.
for _civ_name in ("rome_100ad", "han_china_100ad", "norse_900ad", "england_1300"):
    _s = sim(civ=_civ_name, capital=200000.0)
    for _i, _k in enumerate(k_ for k_ in NODES if NODES[k_]["rev"] > 0):
        if _i >= 6:
            break
        _s.done.add(_k); _s.operating.add(_k)
    _s._done_changed()
    _src = _s.revenue_sources()
    _sum = sum(v for v in _src.values() if isinstance(v, (int, float)))
    check("%s: the ledger rows add up to the revenue they are printed under"
          % _civ_name, abs(_sum - _s.revenue()) < 0.05, (_sum, _s.revenue()))

# --- BREAK: "market can supply 22,500 hours", then 24,500 after hiring one
# smith. market_supply is hours available TO YOU, your own staff included.
s_ms = sim(capital=200000.0)
_town0, _mine0 = s_ms.market_supply_split("smith")
s_ms.hire("smith", 1)
_town1, _mine1 = s_ms.market_supply_split("smith")
check("hiring does not conjure more of a trade into the town",
      abs(_town0 - _town1) < 1e-6, (_town0, _town1))
check("...and what your own people add is counted separately",
      _mine1 > _mine0 and abs(_town1 + _mine1 - s_ms.market_supply("smith")) < 1e-6,
      (_mine0, _mine1, s_ms.market_supply("smith")))

# --- BREAK: after `hire smith 1`, `labour` dropped smith from YOU COULD HIRE,
# which reads as "no more smiths available" - and `hire smith 1` still worked.
_rl, _, _ = proto([{"cmd": "hire", "trade": "smith", "n": 1}, {"cmd": "labour"}])
check("a trade you employ is still listed as one you could hire",
      "smith" in (_rl[1].get("you_could_hire_here") or []),
      _rl[1].get("you_could_hire_here"))


# ======================================================================
# ROUND 8g: two losses a player could not see coming or prevent.
# ======================================================================

# --- BREAK: staff attrition runs at 3.5% a year, so a household near the
# supervision line loses a concern most years and paid the full stock and
# premises to reopen it. A play tester watched four close at once, every year.
s_ch = sim(capital=500000.0)
s_ch.done.update(NODES); s_ch._done_changed()
s_ch.artisans = s_ch.scholars = 5.0
_v = next(k for k in NODES if s_ch.is_venture(k) and NODES[k]["rev"] > 500)
s_ch.open_venture(_v)
_full = s_ch.venture_capex(_v)
s_ch.artisans = s_ch.scholars = 0.0
s_ch.founder_alive = False
check("a concern nobody is left to watch is closed",
      _v in s_ch.close_unstaffed_ventures(105), _v)
s_ch.artisans = s_ch.scholars = 5.0
s_ch.founder_alive = True
s_ch.year = 107
_cap = s_ch.capital
s_ch.open_venture(_v)
check("...and reopening it soon costs the difference, not the whole shop",
      (_cap - s_ch.capital) < _full * 0.2, (_cap - s_ch.capital, _full))
# Past the grace it really has been given up.
s_ch2 = sim(capital=500000.0)
s_ch2.done.update(NODES); s_ch2._done_changed()
s_ch2.artisans = s_ch2.scholars = 5.0
s_ch2.open_venture(_v)
s_ch2.artisans = s_ch2.scholars = 0.0
s_ch2.founder_alive = False
s_ch2.close_unstaffed_ventures(105)
s_ch2.artisans = s_ch2.scholars = 5.0
s_ch2.founder_alive = True
s_ch2.year = 105 + s_ch2.STAFF_CLOSURE_GRACE + 1
_cap2 = s_ch2.capital
s_ch2.open_venture(_v)
check("...but a shop left shut for years is opened again in full",
      (_cap2 - s_ch2.capital) > _full * 0.8, (_cap2 - s_ch2.capital, _full))
# A shop you closed BY CHOICE was never cheap, and must not become cheap.
s_ch3 = sim(capital=500000.0)
s_ch3.done.update(NODES); s_ch3._done_changed()
s_ch3.artisans = s_ch3.scholars = 5.0
s_ch3.open_venture(_v)
s_ch3.close_venture(_v)
_cap3 = s_ch3.capital
s_ch3.open_venture(_v)
check("a concern you shut on purpose still costs the full price to reopen",
      (_cap3 - s_ch3.capital) > _full * 0.8, (_cap3 - s_ch3.capital, _full))

# --- BREAK: six projects wiped in one year. The countdown to abandonment ran
# silently for three years and then took everything spent.
s_hl = sim(capital=500000.0)
_need_eng = "ag2_cold_store"
s_hl.active[_need_eng] = dict(ph_left=float(NODES[_need_eng]["ph"]), yrs=0.0,
                              spent=0.0, cost_left=s_hl.project_cost(_need_eng))
s_hl.step()
check("a project that cannot go on says so the first year, not the fourth",
      any(_need_eng in m and "before it is abandoned" in m for _, m in s_hl.log),
      [m for _, m in s_hl.log][:2])
_st_all = S._agent_state(s_hl, NODES)
_st_hl = _st_all["active"][_need_eng]
check("...and state carries the countdown and the trade that would save it",
      _st_hl.get("will_be_abandoned_in_years") == 3
      and "engineer" in (_st_hl.get("because_nobody_here_can") or []),
      _st_hl)
check("...and the page says the one command that keeps your hours",
      "stop %s" % _need_eng in _RP("state", _st_all),
      [l for l in _RP("state", _st_all).splitlines() if "ABANDONED" in l])


# --- BREAK: the advice on how to get artisans said "build workshop_first (you
# need somewhere for them to work)" while `why workshop_first` said it was
# blocked for want of artisans. A play tester quoted the two lines at each
# other.
s_circ = sim()
s_circ.done.add("patron_local"); s_circ._done_changed()
_adv = s_circ._staff_advice("artisans")
check("advice never points at a remedy waiting on the thing it supplies",
      "workshop_first" not in _adv or "waiting on artisans" in _adv, _adv)
s_circ.artisans = 20.0
check("...and names it plainly once it is actually reachable",
      "waiting on artisans" not in s_circ._staff_advice("artisans"),
      s_circ._staff_advice("artisans"))
check("giving that advice does not recurse into itself",
      isinstance(sim().start_reason("workshop_first")[1], str), "no RecursionError")

# --- BREAK: "no viable option in a required substitution group (fuel, vessel,
# etc.)" - the one blocked-reason a play tester never decoded. It named no
# candidate and no fix.
s_sub = sim()
_gap = next((k for k in sorted(NODES) if NODES[k].get("req_any")
             and not s_sub.substitution_quality(k)[1]
             and all(p in s_sub.done for p in NODES[k]["pre"])), None)
if _gap:
    _why_sub = s_sub.start_reason(_gap)[1]
    check("a substitution group says what it wants and what would serve",
          "substitution group" not in _why_sub and "would do" in _why_sub,
          _why_sub)
else:
    check("a substitution group says what it wants and what would serve",
          True, "no unmet group reachable in rome_100ad")
# And it may not name an option under fog that the player has not heard of.
s_sub_f = sim()
s_sub_f.fog = True
for _k in sorted(NODES):
    if not NODES[_k].get("req_any") or s_sub_f.substitution_quality(_k)[1]:
        continue
    _msg = s_sub_f.start_reason(_k)[1]
    _named = [o for o in NODES if o in _msg and not s_sub_f.is_visible(o)]
    if _named:
        check("a substitution refusal never names a node you cannot see",
              False, (_k, _named[:3]))
        break
else:
    check("a substitution refusal never names a node you cannot see", True, "")


# ======================================================================
# ROUND 8h: mechanics that only announced themselves after they had bitten.
# ======================================================================

# --- BREAK: a recoverable cash dip became "CREDIT EXHAUSTED: 4 projects
# halted" and a forty-year dead run. "money shows a credit limit but nothing
# shows how close to insolvency you are."
s_lim = sim()
s_lim.capital = -s_lim.credit_limit() * 0.75
s_lim.warn_near_the_limit(105)
check("the credit limit warns you BEFORE you cross it",
      any("CLOSE TO THE LIMIT" in m for _, m in s_lim.log), [m for _, m in s_lim.log])
check("...and names what you could still do about it",
      any("stop" in m and "mothball" in m for _, m in s_lim.log),
      [m for _, m in s_lim.log][:1])
_n_before = len(s_lim.log)
s_lim.warn_near_the_limit(106)
check("...and does not say it again every year",
      len(s_lim.log) == _n_before, len(s_lim.log) - _n_before)
s_ok = sim()
s_ok.warn_near_the_limit(105)
check("a solvent player is not warned about a limit they are nowhere near",
      not s_ok.log, [m for _, m in s_ok.log])
_rm, _, _ = proto([{"cmd": "money"}])
check("the ledger says how much of the credit line is used",
      _rm[0].get("of_that_limit_you_have_used") is not None,
      _rm[0].get("of_that_limit_you_have_used"))

# --- BREAK: engineers went from 781 a year to 1,094 and the premium appeared
# in the bill and nowhere else.
s_wg = sim(capital=2000000.0)
_r0, _, _ = proto([{"cmd": "labour", "trade": "smith"}])
_base = _r0[0]["trade"]["a_year_of_one"]
for _ in range(6):
    s_wg.hire("smith", 3)
_dear = S._agent_dispatch(s_wg, NODES, {"cmd": "labour", "trade": "smith"})["trade"]
check("leaning on a trade shows up in its quoted price, not only in the bill",
      _dear["a_year_of_one"] > _base, (_base, _dear["a_year_of_one"]))
check("...and says why, and what brings it back down",
      _dear.get("dearer_than_usual_by") and "supply" in (_dear.get("because") or ""),
      _dear.get("because"))

# --- BREAK: engineers count as SCHOLARS and cannot supervise a workshop. A
# play tester was poor for thirty years over it; swapping three engineers for
# three artisans took their net from -155 a year to +4,164.
_rv, _, _ = proto([{"cmd": "ventures"}])
check("the concerns screen says scholars and craftsmen are not interchangeable",
      "scholar cannot watch a workshop"
      in str(_rv[0].get("these_are_not_interchangeable")),
      _rv[0].get("these_are_not_interchangeable"))
_re, _, _ = proto([{"cmd": "labour", "trade": "engineer"}])
check("...and a trade says which of the two it is",
      _re[0]["trade"].get("kind") == "scholar", _re[0]["trade"].get("kind"))

# --- BREAK: the founder's year quietly grew from 2,000 hours to 10,175 and
# nothing ever said so - the largest change to the resource the game is built
# on, noticed by accident.
s_dp = sim(capital=2000000.0, manual=False)
for _k in ("school_founded", "patron_imperial", "academy_network"):
    s_dp.done.add(_k)
s_dp._done_changed()
for _ in range(30):
    s_dp.step()
check("gaining a deputy is announced, with what it does to your year",
      any("deput" in m and "your year is" in m for _, m in s_dp.log),
      [m for _, m in s_dp.log if "deput" in m][:1])
check("...once per whole deputy, not every year",
      len([m for _, m in s_dp.log if "deput" in m]) <= int(s_dp.directors_extra) + 1,
      len([m for _, m in s_dp.log if "deput" in m]))


# --- BREAK: F34, "numbers that do not reconcile, collected". Every one of
# these was a subtraction a break tester did on figures printed together.
_rn2, _, _ = proto([{"cmd": "hire", "trade": "smith", "n": 2},
                    {"cmd": "labour"},
                    {"cmd": "work", "trade": "scribe", "hours": 500},
                    {"cmd": "start", "id": "units_standards"},
                    {"cmd": "step", "years": 1},
                    {"cmd": "money"}], kit="absurd")
_lab = _rn2[1]
_rows = {r["trade"]: r for r in (_lab.get("on_your_staff") or [])}
if "smith" in _rows:
    check("the wage bill is the quoted wage times the number of people",
          abs(_rows["smith"]["a_year_of_one"] * _rows["smith"]["you_employ"]
              - _lab["annual_wage_bill"]) < 1.0,
          (_rows["smith"], _lab["annual_wage_bill"]))
_wk = _rn2[2]
check("work's three figures subtract to each other",
      abs((_wk["earned"] - _wk["it_cost_your_own_practice"])
          - _wk["so_you_are_up"]) < 0.051, _wk)
_mn = _rn2[5]
check("money's net before and after the work in hand differ by exactly that",
      abs((_mn["net_per_year"] - _mn["spent_on_projects_last_year"])
          - _mn["net_after_project_spend"]) < 0.11, _mn)
_st2, _, _ = proto([{"cmd": "state"}], kit="absurd")
check("...and the after figure is the one `state` prints, to the decimal",
      "net_after_project_spend" in _st2[0], list(_st2[0])[:5])


# --- BREAK: `why med_cataract_couching` said "REVENUE: 500 den/yr" beside a
# ledger crediting 166.7 for the same node - `why` overstating income
# threefold, as a break tester put it.
_rwy, _, _ = proto([{"cmd": "why", "id": "med_cataract_couching"}])
check("why says what a practice node pays YOU, not only what the trade is worth",
      _rwy[0].get("but_it_pays_YOU") is not None
      and _rwy[0]["but_it_pays_YOU"] < _rwy[0]["revenue"],
      (_rwy[0].get("revenue"), _rwy[0].get("but_it_pays_YOU")))
_st_r, _, _ = proto([{"cmd": "money"}])
_led = _st_r[0].get("where_the_money_comes_from") or {}
check("...and that figure is the ledger's, to the decimal",
      abs(_rwy[0]["but_it_pays_YOU"]
          - _led.get("med_cataract_couching", -1)) < 0.11,
      (_rwy[0].get("but_it_pays_YOU"), sorted(_led)[:4]))
_rwy2, _, _ = proto([{"cmd": "why", "id": "horse_collar"}])
check("...and a node that is NOT your practice carries no such line",
      _rwy2[0].get("but_it_pays_YOU") is None, _rwy2[0].get("but_it_pays_YOU"))

# --- BREAK: `ventures` "1 scholars, 1 craftsmen" on the same screen as
# `labour`'s "ON YOUR STAFF: nobody". Three screens, three counts.
_rv2, _, _ = proto([{"cmd": "ventures"}, {"cmd": "labour"}])
check("the free-hands count says that one of them is you",
      _rv2[0].get("one_of_each_of_those_is_you") is True
      and _rv2[1].get("you_employ_in_total") == 0,
      (_rv2[0].get("people_free_to_run_something_new"),
       _rv2[1].get("you_employ_in_total")))

# --- BREAK: two settlements each announced "reputation -12" against a
# reputation of 4.9, and the second did nothing at all.
s_ins = sim(capital=-99999.0)
s_ins.reputation = 4.9
s_ins.insolvent_years = 30
s_ins.enforce_credit_limit(150)
_m1 = [m for _, m in s_ins.log if "INSOLVENCY" in m][-1]
check("a reputation penalty announces what it actually took",
      "-4.9" in _m1, _m1)
s_ins.capital = -99999.0
s_ins.insolvent_years = 30
s_ins.enforce_credit_limit(200)
_m2 = [m for _, m in s_ins.log if "INSOLVENCY" in m][-1]
check("...and says plainly when there was nothing left to take",
      "already at nothing" in _m2, _m2)


# --- BREAK: "this society's literacy will not supply more than 5.9 scholars
# in total, ever, at any price" - and it never moved, through paper, printing,
# a university and three academies. The factor was clamped at 1.0 and Rome
# starts AT the reference, so for Rome the whole mechanism was inert.
s_lit = sim()
_cap0 = s_lit.literate_capacity("machinist")
for _k in ("rag_paper", "printing_press", "if_movable_type", "school_founded",
           "academy_network", "corpus_written"):
    if _k in NODES:
        s_lit.apply_tech_effects(_k)
_cap1 = s_lit.literate_capacity("machinist")
check("teaching a society to read raises what it can staff",
      _cap1 > _cap0 * 1.5, (_cap0, _cap1))
check("...but not without bound",
      _cap1 < _cap0 * 5, (_cap0, _cap1))
check("a trade that needs no letters is not capped by literacy at all",
      s_lit.literate_capacity("smith") == float("inf"),
      s_lit.literate_capacity("smith"))
# --- BREAK: `train electrician 20` gave 27 while machinists stopped at 5.9.
check("every taught trade is bounded by literacy, electrician included",
      not (set(S.Sim.LITERATE_TRADES) ^ set(S.Sim.LITERATE_TRADES))
      and all(t in S.Sim.LITERATE_TRADES for t in S.TRADES_ABSENT),
      sorted(set(S.TRADES_ABSENT) - set(S.Sim.LITERATE_TRADES)))
s_el = sim(capital=2000000.0)
_ok_el, _why_el = s_el.train("electrician", 20)
check("...so twenty electricians cannot be taught into a society of twelve",
      not _ok_el and "literacy" in str(_why_el), _why_el)


# ======================================================================
# ROUND 9: what the two play testers of round nine found.
# ======================================================================

# --- BREAK: a sacking destroyed technologies and named none of them. A play
# tester discovered theirs decades later, when `start X` said "missing
# prerequisites: <thing you built two hundred years ago>", and rebuilt the
# chain one refusal at a time.
s_sack = sim(events=True, capital=500000.0)
for _k in list(NODES)[:400]:
    s_sack.done.add(_k)
s_sack._done_changed()
s_sack.rng = random.Random(11)
for _y in range(150, 320):
    s_sack.year = _y
    s_sack._shocks(_y)
    if getattr(s_sack, "forgotten", None):
        break
check("a sacking names the technologies it destroyed",
      any("KNOWLEDGE LOST" in m and "_" in m.split("forgotten")[-1]
          for _, m in s_sack.log),
      [m for _, m in s_sack.log if "KNOWLEDGE LOST" in m][:1])
_kr = s_sack.knowledge_risk()
check("...and `risk` lists what you have to build again",
      _kr.get("you_have_already_lost", 0) > 0
      and _kr.get("and_have_to_build_again"),
      _kr.get("you_have_already_lost"))
check("...and everything it lists really is gone from what you know",
      all(x not in s_sack.done for x in _kr["and_have_to_build_again"]),
      [x for x in _kr["and_have_to_build_again"] if x in s_sack.done])
# The hedge follows what you KNOW, not what you run: a play tester thought it
# followed `operating` because a sacking had quietly taken their corpus.
s_hg = sim(capital=500000.0)
_h0 = s_hg.knowledge_risk()["hedged_by"]
s_hg.done.add("corpus_written"); s_hg._done_changed()
_h1 = s_hg.knowledge_risk()["hedged_by"]
s_hg.open_venture("corpus_written")
_h2 = s_hg.knowledge_risk()["hedged_by"]
check("building the corpus hedges you; opening it changes nothing",
      _h0 is None and _h1 == "corpus_written" and _h2 == _h1, (_h0, _h1, _h2))

# --- BREAK: twenty concerns, twenty-five years, income flat, because nothing
# said on the main screen what leaving them shut was costing.
s_sh = sim(capital=50000.0)
for _k in list(NODES)[:200]:
    s_sh.done.add(_k)
s_sh._done_changed()
_stsh = S._agent_state(s_sh, NODES)
check("state says in money what your shut concerns would earn",
      _stsh.get("shut_concerns_would_earn_a_year", 0) > 0,
      _stsh.get("shut_concerns_would_earn_a_year"))
check("...and a player running everything is not nagged about it",
      S._agent_state(sim(), NODES).get("shut_concerns_would_earn_a_year") is None,
      S._agent_state(sim(), NODES).get("shut_concerns_would_earn_a_year"))

# --- BREAK: auto_mine took 353,039 a year against 467,227 of revenue and
# there was no command that named what you owned or what it cost.
s_mn = sim(capital=2000000.0)
s_mn.open_mine("coal", 400, partial=False)
_rmn_new = S._agent_dispatch(s_mn, NODES, {"cmd": "mines"})
check("a shaft you have just sunk is listed while it is still being sunk",
      _rmn_new["mines_you_own"] != "none"
      and _rmn_new["still_being_sunk"].get("coal"),
      _rmn_new.get("mines_you_own"))
for _ in range(int(s_mn.MINE_LEAD_YEARS) + 1):
    s_mn.year += 1
    s_mn.commission_mines()
_rmn = S._agent_dispatch(s_mn, NODES, {"cmd": "mines"})
check("there is a command that lists the mines you own and their cost",
      _rmn["mines_you_own"] != "none"
      and _rmn["they_cost_you_a_year_in_all"] > 0, _rmn.get("mines_you_own"))
check("...and each row says how to shut it",
      all("close" in r["shut_it_with"] for r in _rmn["mines_you_own"]),
      _rmn["mines_you_own"][:1])
check("...and it renders as a table, not a dict dump",
      "YOUR OWN WORKINGS" in _RP("mines", _rmn) and "{" not in _RP("mines", _rmn),
      _RP("mines", _rmn)[:60])

# --- BREAK: Han China was told it writes its corpus "in plain quantitative
# Greek and Latin" and seeks "Senatorial patronage".
for _cid, _bad in (("han_china_100ad", "Greek and Latin"),
                   ("norse_900ad", "Senatorial patronage"),
                   ("mexica_1500", "Greek and Latin"),
                   ("england_1300", "Senatorial patronage")):
    _rl, _, _ = proto([{"cmd": "why", "id": "corpus_written"},
                       {"cmd": "why", "id": "patron_senatorial"}], civ=_cid)
    check("%s is not handed Rome's own words" % _cid,
          _bad not in json.dumps(_rl), _bad)
_rr, _, _ = proto([{"cmd": "why", "id": "corpus_written"}], civ="rome_100ad")
check("...and Rome, which the tree is written from, is left alone",
      "Greek and Latin" in json.dumps(_rr), json.dumps(_rr)[:120])

# --- BREAK: "unknown_source" reached a player-facing refusal, which is data,
# not English.
s_sl = sim()
s_sl.done.update(NODES)
s_sl.done.discard("el2_potentiometer_method_measurement")
s_sl.done.discard("dynamo")
s_sl._done_changed()
_msl = s_sl.start_reason("el2_potentiometer_method_measurement")[1]
check("a substitution group reads as English, not as a data slug",
      "_" not in _msl.split("you have none")[0], _msl[:90])


# ======================================================================
# ROUND 9, the break tester: a deadlock, a silent death, and the same seed
# giving three different answers.
# ======================================================================

# --- BREAK: `--seed` did not reproduce a run. Same script, same seed, three
# runs: 587,300 / 6,664,218 / 6,652,459 in capital. PYTHONHASHSEED=0 made them
# identical. Float sums over SETS: addition is not associative, the total
# gates open_venture with a hard comparison, and one bit decides a century.
def _one_run(seed=9, years=180, civ="rome_100ad"):
    s_ = S.Sim(NODES, ORDER, random.Random(seed), events=True, manual=False,
               civ=S.load_civ(civ), cfg={"start_capital": 100000.0})
    s_.goal, s_.done_year = GOAL, {}
    for _ in range(years):
        s_.step()
        if s_.dead_reason or s_.goal_year:
            break
    return (round(s_.capital, 6), len(s_.done), len(s_.operating),
            round(s_.reputation, 9))

_r_a = _one_run()
check("the same seed gives the same run, twice in one process",
      _one_run() == _r_a, (_r_a, _one_run()))
_det = subprocess.run(
    [sys.executable, "-c",
     "import random,sys;sys.path.insert(0,%r);import simulator as S;"
     "T,P,N,W,Gd=S.load();_l,O,_b=S.load_strategy('recommended',N,T['meta']['goal_node']);"
     "s=S.Sim(N,O,random.Random(9),events=True,manual=False,civ=S.load_civ('rome_100ad'),"
     "cfg={'start_capital':100000.0});s.goal,s.done_year=T['meta']['goal_node'],{};"
     "[s.step() for _ in range(180)];"
     "print(round(s.capital,6),len(s.done),len(s.operating),round(s.reputation,9))" % HERE],
    capture_output=True, text=True, timeout=600,
    env=dict(os.environ, PYTHONHASHSEED="1234"))
check("...and the same run in a process with a different string hash seed",
      _det.stdout.split() == [str(x) for x in _r_a],
      (_det.stdout.strip(), _r_a))

# --- BREAK: a permanent deadlock. `logarithms` wants 10,000 scribe-hours a
# year where the society can field 8,750, so the throttle gives back a
# fraction of the work every year - and with no floor under the refund it gave
# back ALL of it. Founder-hours sat at exactly 5.0 for ever, the bill paid,
# the calendar long past, holding the whole scribe pool and freezing eight
# projects behind it - one of them scientific_method, a 230-denarius node
# startable in year 100 and still unbuilt at the horizon.
s_dl = sim(capital=20000000.0)
for _p in NODES["logarithms"]["pre"]:
    s_dl.done.add(_p)
s_dl.scholars = s_dl.artisans = 50.0
s_dl._done_changed()
check("a project needing more of a trade than exists is startable",
      s_dl.start_project("logarithms")[0], s_dl.start_reason("logarithms"))
for _ in range(60):
    s_dl.step()
    if "logarithms" not in s_dl.active:
        break
check("...and it finishes, slowly, instead of freezing for ever",
      "logarithms" in s_dl.done, (s_dl.year, s_dl.active.get("logarithms")))
check("...and it took longer than its calendar floor, because it crawled",
      s_dl.done_year.get("logarithms", 0) - 100 > NODES["logarithms"]["yrs"],
      s_dl.done_year.get("logarithms"))

# --- BREAK: "RUN ENDS: denounced: as a sorcerer" after eleven quiet years,
# with `state` showing "scandal 33.55" and no threshold and no probability -
# on the same screen where eminence explains itself in full.
s_sc = sim(events=True)
s_sc.scandal = 30.0
s_sc.year = 150
s_sc._said_scandal = 0
_st_sc = S._agent_state(s_sc, NODES)
check("state says what scandal is dangerous above",
      _st_sc.get("scandal_danger") is not None, _st_sc.get("scandal_danger"))
check("...and what the chance of being denounced this year is",
      _st_sc.get("chance_of_being_denounced_this_year", 0) > 0,
      _st_sc.get("chance_of_being_denounced_this_year"))
check("...and the page prints both, next to the eminence line that already did",
      "SCANDAL is dangerous above" in _RP("state", _st_sc),
      [l for l in _RP("state", _st_sc).splitlines() if "dangerous above" in l])

# --- BREAK: the advertised price index touched nothing a player feels.
# Revenue ~233 and living costs 230.0 TO THE DECIMAL in all five civs, against
# a selection screen advertising "prices 0.75x to 1.40x Rome" - while project
# costs, wages, the workshop's output and state funding all did scale, so an
# expensive society paid 1.4x to build and ate at Roman prices.
_lc, _rv = {}, {}
for _cid in ("rome_100ad", "han_china_100ad", "norse_900ad", "mexica_1500",
             "england_1300"):
    _s = sim(civ=_cid)
    _lc[_cid] = round(_s.living_cost(), 2)
    _rv[_cid] = round(_s.revenue(), 2)
check("living costs follow this society's price level",
      len(set(_lc.values())) == 5, _lc)
check("...and so does what your practice pays",
      len(set(_rv.values())) == 5, _rv)
check("...and the dearest society really is the dearest",
      max(_lc, key=lambda c: _lc[c]) == "norse_900ad", _lc)
check("...and the cheapest really is the cheapest",
      min(_lc, key=lambda c: _lc[c]) == "han_china_100ad", _lc)


# --- BREAK: "A concern you open reaches its full figure over 3 years" - and a
# concern built in 100 and opened in 130 was at full takings the day its doors
# opened, because the ramp read the year you worked it OUT. Delaying `open`
# was strictly better than opening promptly.
s_rp = sim(capital=500000.0)
_vr = next(k for k in sorted(NODES)
           if s_rp.is_venture(k) and NODES[k]["rev"] > 500 and not NODES[k]["pre"])
s_rp.done.add(_vr); s_rp.done_year[_vr] = 100; s_rp._done_changed()
s_rp.artisans = s_rp.scholars = 20.0
s_rp.year = 130
s_rp.open_venture(_vr)
_ramps = []
for _y in (130, 131, 132, 133):
    s_rp.year = _y
    _ramps.append(round(s_rp.venture_ramp(_vr), 3))
check("a concern opened late still starts small",
      _ramps[0] < 0.4, _ramps)
check("...and reaches its full figure over the years the ledger promises",
      _ramps == [1 / 3.0, 2 / 3.0, 1.0, 1.0][:4]
      or (_ramps[0] < _ramps[1] < _ramps[2] == _ramps[3] == 1.0), _ramps)
# Reopening something you already ran does not restart its custom.
s_rp.year = 140
s_rp.close_venture(_vr)
s_rp.open_venture(_vr)
check("...and reopening a shop the town already knows does not start it over",
      s_rp.venture_ramp(_vr) == 1.0, s_rp.venture_ramp(_vr))

# --- BREAK: "FULL CHAIN BEHIND IT: ... N den" summed the tree's BASE cost and
# applied none of the multipliers the same page prints. The eight
# prerequisites of a telescope came out at 24,175 in all five civilisations.
_chains = {}
for _cid in ("rome_100ad", "han_china_100ad", "norse_900ad"):
    _rc, _, _ = proto([{"cmd": "why", "id": "telescope"}], civ=_cid)
    _chains[_cid] = _rc[0].get("chain_cost")
check("the full-chain bill is quoted at this society's prices",
      len(set(_chains.values())) == 3, _chains)
check("...and the dearest society's chain really is the dearest",
      max(_chains, key=lambda c: _chains[c]) == "norse_900ad", _chains)
# The parts have to add up to the whole, at whatever prices.
_s_ch = sim(civ="norse_900ad")
from engine.data import closure as _closure
# The chain is what is BEHIND it, so the node itself is not in the bill.
_behind = sorted(_closure(NODES, "telescope") - {"telescope"})
check("...and it is the sum of what each of those nodes would actually cost",
      abs(_chains["norse_900ad"]
          - sum(_s_ch.project_cost(x) for x in _behind)) < 0.5,
      (_chains["norse_900ad"],
       round(sum(_s_ch.project_cost(x) for x in _behind), 1)))

# --- BREAK: `risk` applied the 80% chance twice, so "expected lost per
# sacking" was exactly 20% low - a sacking that has happened has happened.
s_rk = sim()
for _k in list(NODES)[:300]:
    s_rk.done.add(_k)
s_rk._done_changed()
_krk = s_rk.knowledge_risk()
check("what a sacking costs is not discounted by the chance it happens",
      abs(_krk["expected_technologies_lost_per_sacking"]
          - _krk["technologies_at_risk"] * _krk["fraction_lost_when_it_happens"]) < 0.6,
      _krk["expected_technologies_lost_per_sacking"])
check("...and the chance it costs you anything is reported separately",
      _krk.get("and_the_chance_a_sacking_costs_you_anything") is not None,
      _krk.get("and_the_chance_a_sacking_costs_you_anything"))

# --- BREAK: "CLOSE TO THE LIMIT ... (103%) ... every project in hand is
# halted" in a year when nothing was halted, because it had already happened.
s_pl = sim()
s_pl.capital = -s_pl.credit_limit() * 1.03
s_pl.warn_near_the_limit(105)
check("the limit warning is about what is ahead of you, not behind",
      not s_pl.log, [m for _, m in s_pl.log])

# --- BREAK: `bribe 1` refused at 0% protection as "already as protected as
# money can make you".
_rb, _, _ = proto([{"cmd": "bribe", "amount": 1}])
check("a bribe too small to matter says so, not that you are already covered",
      "too little" in (_rb[0].get("error") or ""), _rb[0].get("error"))


# --- BREAK: "FULL CHAIN BEHIND IT" printed identical figures in year 436
# after 227 technologies as in year 100 with nothing built.
s_cn = sim()
_r_before = S._agent_dispatch(s_cn, NODES, {"cmd": "why", "id": "telescope"})
for _p in ("patron_local", "workshop_first", "identity_cover"):
    s_cn.done.add(_p)
s_cn._done_changed()
_r_after = S._agent_dispatch(s_cn, NODES, {"cmd": "why", "id": "telescope"})
check("the chain behind a node counts down as you build it",
      _r_after["chain_size"] < _r_before["chain_size"],
      (_r_before["chain_size"], _r_after["chain_size"]))
check("...in hours as well as in nodes",
      _r_after["chain_founder_hours"] < _r_before["chain_founder_hours"],
      (_r_before["chain_founder_hours"], _r_after["chain_founder_hours"]))
check("...and in money",
      _r_after["chain_cost"] < _r_before["chain_cost"],
      (_r_before["chain_cost"], _r_after["chain_cost"]))
check("...and it still says how long the whole road was",
      _r_after["chain_size_counting_what_you_have_built"]
      == _r_before["chain_size_counting_what_you_have_built"],
      _r_after["chain_size_counting_what_you_have_built"])

# --- BREAK: the household-room refusal handed back the advice for BUYING
# people, every word of which needs room you do not have. A play tester with a
# ceiling of 166.9 against a node wanting 200 craftsmen wrote that none of the
# three remedies the message suggests works.
s_rm = sim(capital=1000000.0)
_ok_rm, _why_rm = s_rm.hire("smith", 20)
check("a room refusal names what raises the room, not what buys people",
      not _ok_rm and "built" in _why_rm and "hire" not in _why_rm.split(".")[1],
      _why_rm)
check("...and names the nearest of them first, not the largest",
      _why_rm.index("workshop_first") < _why_rm.index("school_founded"),
      _why_rm[_why_rm.index("built"):][:120])
s_rm2 = sim(capital=1000000.0)
s_rm2.done.update(NODES); s_rm2._done_changed()
check("...and says so plainly when you already hold every one of them",
      "every one of them" in s_rm2._room_advice(), s_rm2._room_advice())


# --- BREAK: three places said the town could field 8,750 scribe-hours a year,
# and commissioning the full 8,750 ON TOP of the standing pool let a
# 10,000-hour project finish. Real ceiling 17,500; every one of the three
# statements false.
# TWO CHANNELS, each bounded and each named. Hiring draws on the people who
# live here; a commission is a job placed with an outside shop, which
# subcontracts - dearer per hour, and bounded in turn by what the local trade
# can spare. Stated as ONE ceiling of 8,750 it was false (the real one was
# 17,500); collapsed into one it made commissioning buy byte-identical
# progress and be pointless. Both statements have to be on the screen.
s_cm = sim(capital=5000000.0)
_ceiling = s_cm.market_supply("scribe")
s_cm.commission("scribe", _ceiling * 0.9)
check("commissioning does not raise how many of a trade LIVE here",
      abs(s_cm.market_supply_split("scribe")[0]
          - sim(capital=5000000.0).market_supply_split("scribe")[0]) < 1e-6,
      s_cm.market_supply_split("scribe")[0])
check("...and it does add hours you can actually call on",
      s_cm.hours_you_can_call_on("scribe") > _ceiling, 
      (_ceiling, s_cm.hours_you_can_call_on("scribe")))
check("...and you cannot commission past what the trade here can spare",
      s_cm.commission("scribe", _ceiling)[0] is False,
      s_cm.commission("scribe", _ceiling)[1])
_rc2, _, _ = proto([{"cmd": "labour", "trade": "scribe"}])
check("...and `labour` names both channels, not one ceiling",
      _rc2[0]["trade"].get("hours_you_could_still_commission") is not None
      and _rc2[0]["trade"].get("hours_available_to_you_in_all")
      >= _rc2[0]["trade"].get("hours_the_market_can_supply"),
      _rc2[0]["trade"])

# --- BREAK: a senatorial patron added 15,000 to the credit line whoever you
# were, so a household with 1,800 of revenue could owe 23,000 - about 1,500 a
# year of interest against 1,800 of income, which no practice can ever repay.
s_cl = sim()
_thin = s_cl.credit_limit()
s_cl.done.add("patron_senatorial"); s_cl._done_changed()
check("a grand friend does not lend you more than your income can carry",
      s_cl.credit_limit() < _thin * 3, (_thin, s_cl.credit_limit()))
check("...and the interest on the whole line stays under what you earn",
      s_cl.credit_limit() * s_cl.debt_interest_rate() < s_cl.revenue(),
      (s_cl.credit_limit() * s_cl.debt_interest_rate(), s_cl.revenue()))
check("...while a founder with a practice can still just reach a cover identity",
      sim().capital + sim().credit_limit() >= sim().project_cost("identity_cover"),
      (sim().capital + sim().credit_limit(), sim().project_cost("identity_cover")))

# --- BREAK: status upkeep was unconditional - 1,100 a year for a citizenship
# and a senatorial patron a ruined household could not afford and had no way
# to shed - and it bled a Rome run 741 a year for sixty-four years.
s_st = sim()
s_st.done.update({"citizenship", "patron_senatorial"}); s_st._done_changed()
_rich = sim(capital=2000000.0)
_rich.done.update({"citizenship", "patron_senatorial"}); _rich._done_changed()
# The two ranks are worth 1,100 a year of show at Rome's prices; a household
# with 233 of income does not pay it.
check("a ruined household stops keeping up appearances",
      s_st.living_cost() < sim().living_cost() + 50.0,
      (s_st.living_cost(), sim().living_cost()))
check("...and a household that can afford the show still pays for it",
      _rich.living_cost() > s_st.living_cost() * 2, (_rich.living_cost(),
                                                     s_st.living_cost()))

# --- BREAK: the optimizer's budget for new work counted upkeep, living costs
# and mines and NOT the interest it was already paying, so a household bleeding
# 552 a year decided it had five years of headroom against money that did not
# exist.
s_bd = sim(capital=-20000.0, manual=False)
s_bd.insolvent_years = 20
_before = len(s_bd.active)
s_bd.step()
check("a household deep in arrears does not commit to new work",
      len(s_bd.active) <= _before + 1, (len(s_bd.active), _before))


# --- BREAK: "There's no 'why am I stuck?' view - three separate 90-250-year
# stalls, each caused by one node blocked on one thing, each found by typing
# `why` at a guess." Every tester of rounds eight and nine said some version.
_rs, _, _ = proto([{"cmd": "stuck"}])
check("there is one command that answers why you are not getting on",
      _rs and _rs[0].get("ok") and "what_is_holding_you_up" in _rs[0],
      list(_rs[0])[:5] if _rs else None)
check("...and on turn one it says nothing is holding you up",
      isinstance(_rs[0]["what_is_holding_you_up"], str), _rs[0]["what_is_holding_you_up"])
check("...and names the cheapest thing you could actually begin",
      _rs[0].get("and_the_cheapest_thing_you_could_start_now") in NODES,
      _rs[0].get("and_the_cheapest_thing_you_could_start_now"))
_rs2, _, _ = proto([{"cmd": "start", "id": "identity_cover"},
                    {"cmd": "step", "years": 3},
                    {"cmd": "stuck"}])
_held = _rs2[-1]["what_is_holding_you_up"]
check("...and once you are committed and in the red it names both",
      not isinstance(_held, str)
      and {"work in hand", "arrears"} <= {r["what"] for r in _held},
      [r.get("what") for r in _held] if not isinstance(_held, str) else _held)
check("...and says what each piece of work in hand is waiting for",
      any(r.get("each_waiting_on") for r in _held if isinstance(r, dict)), _held)
check("...and it renders as a page, not a dict dump",
      "WHY YOU ARE NOT GETTING ON" in _RP("stuck", _rs2[-1])
      and "{" not in _RP("stuck", _rs2[-1]), _RP("stuck", _rs2[-1])[:70])
_rst, _, _ = proto([{"cmd": "state"}])
check("...and `state` advertises it every turn",
      any("stuck" in x for x in (_rst[0].get("also_available") or [])),
      _rst[0].get("also_available"))


# --- BREAK: a trade you taught counts as existing for ever, so once the last
# machinist had died of old age auto_train skipped every node that needed one
# and nobody was ever taught again. A Rome run built 829 technologies, sat on
# 31.9M denarii, and could not begin precision_three_plate - which gates
# master_screw, the screw lathe and ninety-nine of the hundred and forty-six
# nodes on the road to the goal.
s_rt = sim(capital=2000000.0, manual=False)
s_rt.trades_created.add("machinist")          # taught once, long ago
s_rt.employees.pop("machinist", None)
s_rt._resync_pools()
check("a trade taught and then lost counts as gone, not as available",
      s_rt.trade_available("machinist")
      and s_rt.market_supply("machinist") <= 0.0,
      (s_rt.trade_available("machinist"), s_rt.market_supply("machinist")))
for _ in range(6):
    s_rt.step()
check("...and the engine teaches it again rather than skipping every node "
      "that needs it",
      s_rt.market_supply("machinist") > 0
      or s_rt._trade_headcount_pending("machinist") > 0,
      (s_rt.market_supply("machinist"),
       s_rt._trade_headcount_pending("machinist")))
# But not every year: teaching two costs about 900 of a 2,000-hour year.
s_rt2 = sim(capital=2000000.0, manual=False)
s_rt2.trades_created.add("machinist")
# Per TRADE: teaching four different trades over forty years is fine; teaching
# the same one four times is the treadmill that cost three Rome seeds most of
# what they built.
_per_trade = {}
for _ in range(40):
    _before = dict(getattr(s_rt2, "last_taught", {}))
    s_rt2.step()
    for _t, _y in getattr(s_rt2, "last_taught", {}).items():
        if _before.get(_t) != _y:
            _per_trade[_t] = _per_trade.get(_t, 0) + 1
check("...and no more than once a generation FOR THE SAME TRADE",
      all(v <= 40 // s_rt2.RETEACH_EVERY + 1 for v in _per_trade.values()),
      _per_trade)


# --- BREAK: `train machinist 4` quietly ate 1,800 of a play tester's 2,000
# founder-hours and, with nothing left to supervise with, closed a dozen
# concerns as a side effect. The reply was six words about two years' time.
_rt3, _, _ = proto([{"cmd": "train", "trade": "machinist", "n": 4}], kit="absurd")
check("teaching says what it took out of your year",
      "of your own hours" in json.dumps(_rt3[0])
      and "left this year" in json.dumps(_rt3[0]), _rt3[0])
check("...and what it cost to keep them while they learn",
      "denarii" in json.dumps(_rt3[0]), _rt3[0])


# --- BREAK: household_room exists because `hire` and `buy` used different
# numbers. `train` was the third verb and checked nothing at all, so the
# optimizer taught its way to a headcount of 26.9 against room for 6 - minus
# eighteen places - and then could not hire the artisans to supervise
# anything.
s_tr3 = sim(capital=2000000.0)
# Widen the literacy ceiling first, so the ROOM is what binds rather than the
# pool of people who can read - the tightest constraint should be the one that
# speaks, and here we are testing the other one.
for _k in ("rag_paper", "printing_press", "if_movable_type", "academy_network"):
    if _k in NODES:
        s_tr3.apply_tech_effects(_k)
_room0 = s_tr3.household_room()
check("a fresh household has room for a few people and no more",
      0 < _room0 < 20, _room0)
check("...and the literacy ceiling is not what binds here",
      s_tr3.literate_capacity("machinist") > _room0 + 1,
      (s_tr3.literate_capacity("machinist"), _room0))
# Fill the household first, which is the state the tester was in: the hours
# check bites long before the room does at any larger number, because teaching
# costs 450 founder-hours a head.
s_tr3.hire("smith", int(_room0))
_ok_t3, _why_t3 = s_tr3.train("machinist", 1)
check("teaching past what you can feed and house is refused",
      not _ok_t3 and "feed, house and oversee" in _why_t3, _why_t3)
check("...and it says there is no room for even one",
      "no room for even one" in _why_t3, _why_t3)
check("...and what makes room, which is not what buys people",
      "built" in _why_t3, _why_t3)
s_tr4 = sim(capital=2000000.0)
check("...and teaching within the room still works",
      s_tr4.train("machinist", 1)[0], s_tr4.train("machinist", 1)[1])
# The three verbs must agree, which is the whole reason household_room exists.
s_ag = sim(capital=2000000.0)
_r = s_ag.household_room()
s_ag.hire("smith", int(_r))          # fill it exactly
check("hire, buy and train are all bounded by the same one number",
      s_ag.hire("smith", 1)[0] is False
      and s_ag.train("machinist", 1)[0] is False
      and s_ag.buy_slaves(1) <= 0,
      (_r, s_ag.household_room()))


# --- BREAK: "this society's literacy will not supply more than 6.4 scholars
# in total, ever" gates the GOAL, which wants twenty-five, and appeared in no
# screen at all: a play tester found it in a refusal message in year 463 of a
# 500-year game. The single thing that decided whether their run could be won.
_rl3, _, _ = proto([{"cmd": "labour", "trade": "scholar"},
                    {"cmd": "labour", "trade": "smith"},
                    {"cmd": "why", "id": "point_contact_transistor"}])
check("a lettered trade shows the ceiling on how many can ever exist here",
      _rl3[0]["trade"].get("most_this_society_can_ever_supply") is not None,
      _rl3[0]["trade"].get("most_this_society_can_ever_supply"))
check("...and says what widens it",
      "printing" in str(_rl3[0]["trade"].get("what_widens_it")),
      _rl3[0]["trade"].get("what_widens_it"))
check("...and a trade needing no letters carries no such ceiling",
      _rl3[1]["trade"].get("most_this_society_can_ever_supply") is None,
      _rl3[1]["trade"].get("most_this_society_can_ever_supply"))
check("and `why` warns when a node wants more scholars than can ever exist",
      _rl3[2].get("more_scholars_than_this_society_can_supply"),
      _rl3[2].get("more_scholars_than_this_society_can_supply"))
check("...and more craftsmen than the household could ever hold",
      _rl3[2].get("more_craftsmen_than_your_household_can_hold"),
      _rl3[2].get("more_craftsmen_than_your_household_can_hold"))
_rl4, _, _ = proto([{"cmd": "why", "id": "horse_collar"}])
check("...and says nothing of the kind about a node you could staff",
      not _rl4[0].get("more_scholars_than_this_society_can_supply"),
      _rl4[0].get("more_scholars_than_this_society_can_supply"))


# ======================================================================
# ROUND 10: two testers won, and the break tester found four ways the game
# was wrong about its own numbers.
# ======================================================================

# --- BREAK: paying off your debt IN FULL made you insolvent. `work scholar
# 2000` sells the founder's whole year, which takes the practice's income to
# nothing FOR that year, which collapsed the credit line from 1,397 to 210 in
# the middle of a step - and the project spending already committed against
# the old line breached the new one. Owing 628 was safe; owing nothing was
# ruin.
_rd, _, _ = proto([{"cmd": "start", "id": "arithmetic_positional"},
                   {"cmd": "step", "years": 1},
                   {"cmd": "work", "trade": "scholar", "hours": 2000},
                   {"cmd": "step", "years": 1},
                   {"cmd": "state"}])
check("clearing your debt by working does not make you insolvent",
      not any("INSOLVENCY" in json.dumps(x) for x in _rd), 
      [e for x in _rd for e in (x.get("events") or []) if "INSOLVENCY" in str(e)])
check("...and does not take your whole reputation with it",
      _rd[-1].get("reputation", 0) > 1.0, _rd[-1].get("reputation"))
s_cc = sim()
_full = s_cc.credit_limit()
s_cc.wage_hours_this_year = s_cc.director_pool()
check("a lender does not cut your line because you took a job this year",
      abs(s_cc.credit_limit() - _full) < 1e-6, (_full, s_cc.credit_limit()))

# --- BREAK: a dead founder kept playing - starting projects, hiring staff,
# and his surgical practice went on taking fees for eleven years.
s_dd = sim(capital=50000.0)
_alive = s_dd.revenue()
s_dd.founder_alive = False
check("a dead physician has no practice",
      _alive > 0 and s_dd.revenue() == 0.0, (_alive, s_dd.revenue()))
check("...and cannot sell hours he does not have",
      s_dd.work_for_wages("scholar", 100)[0] == 0.0,
      s_dd.work_for_wages("scholar", 100)[1])
check("...and cannot take anyone on with no deputy to direct them",
      S._agent_dispatch(s_dd, NODES,
                        {"cmd": "hire", "trade": "smith", "n": 1}).get("ok") is False,
      S._agent_dispatch(s_dd, NODES, {"cmd": "hire", "trade": "smith", "n": 1}))

# --- BREAK: `ventures` understated every concern by a uniform 2.234x against
# the `money` ledger, and its NEEDS column printed the BUILD crew where the
# engine charges supervision - a quarter of it, and never the number the
# refusal quotes.
s_vv = sim(capital=5000000.0)
s_vv.done.update(NODES); s_vv._done_changed()
s_vv.artisans = s_vv.scholars = 40.0
_opened = 0
for _k in sorted(NODES):
    if s_vv.is_venture(_k) and _opened < 5 and s_vv.open_venture(_k)[0]:
        _opened += 1
for _ in range(4):
    s_vv.step()
_vr = S._agent_dispatch(s_vv, NODES, {"cmd": "ventures"})
_led = s_vv.revenue_sources()
check("ventures quotes the same earnings the ledger credits",
      all(abs(r["earns_a_year"] - _led.get(r["id"], r["earns_a_year"])) < 0.11
          for r in _vr["running"]),
      [(r["id"], r["earns_a_year"], _led.get(r["id"])) for r in _vr["running"]][:2])
check("...and its NEEDS column is the supervision the engine charges",
      all(abs(r["needs"]["craftsmen"] - s_vv.venture_hands(r["id"])[1]) < 0.011
          for r in _vr["running"]),
      [(r["id"], r["needs"]) for r in _vr["running"]][:2])


# --- BREAK: "CREDIT EXHAUSTED: 2 projects halted, unfinished" - "halted"
# means paused to a reader and meant deleted here. A break tester watched 795
# denarii and about 800 founder-hours vanish, with scientific_method dying 115
# denarii short of done and every hour already spent, and `stop` losing the
# same thing so no branch saved it.
s_ce = sim()
s_ce.start_project("identity_cover")
for _ in range(3):
    s_ce.step()
_spent = s_ce.active["identity_cover"]["spent"]
check("a project part-paid for has really been part-paid for",
      _spent > 100, _spent)
s_ce.credit_limit = lambda: 0.0
s_ce.enforce_credit_limit(s_ce.year)
check("the creditors stopping your work does not burn what you paid",
      abs(s_ce.paid_towards.get("identity_cover", 0.0) - _spent) < 0.5,
      s_ce.paid_towards)
check("...and the event says so, and names what it stopped",
      any("identity_cover" in m and "stands to your credit" in m
          for _, m in s_ce.log),
      [m for _, m in s_ce.log if "CREDIT EXHAUSTED" in m][:1])
s_ce.capital, s_ce.credit_frozen_until = 50000.0, 0
s_ce.start_project("identity_cover")
check("...and beginning again takes it off the bill",
      abs(s_ce.active["identity_cover"]["cost_left"]
          - (s_ce.project_cost("identity_cover") - _spent)) < 0.5,
      (s_ce.active["identity_cover"]["cost_left"],
       s_ce.project_cost("identity_cover")))
check("...and the credit is spent once, not every time",
      "identity_cover" not in s_ce.paid_towards, s_ce.paid_towards)

# --- BREAK: `restore` charged the full price for a concern the staffing rule
# had shut, while the closing message promises a tenth.
s_rs = sim(capital=500000.0)
s_rs.done.update(NODES); s_rs._done_changed()
s_rs.artisans = s_rs.scholars = 5.0
_vv = next(k for k in sorted(NODES)
           if s_rs.is_venture(k) and NODES[k]["rev"] > 500)
s_rs.open_venture(_vv)
_fullfee = max(s_rs.project_cost(_vv) * 0.3, NODES[_vv]["up"] * 2.0)
s_rs.artisans = s_rs.scholars = 0.0
s_rs.founder_alive = False
s_rs.close_unstaffed_ventures(105)
s_rs.artisans = s_rs.scholars = 5.0
s_rs.founder_alive = True
s_rs.year = 107
_cap_rs = s_rs.capital
s_rs.restore_work(_vv)
check("restoring a shop the staffing rule shut costs the tenth it promised",
      (_cap_rs - s_rs.capital) < _fullfee * 0.2,
      (_cap_rs - s_rs.capital, _fullfee))


# --- BREAK: `stop` burned the money as well as the hours, "same as a real
# abandoned enterprise" - so when the creditors were about to take everything,
# stopping something yourself cost exactly as much as letting them, and `stop`
# was never the right move. The site does not un-dig itself either way.
s_sp = sim()
s_sp.start_project("identity_cover")
for _ in range(2):
    s_sp.step()
_spent_sp = s_sp.active["identity_cover"]["spent"]
_ok_sp, _why_sp = s_sp.stop_project("identity_cover")
check("stopping a project keeps the money already paid",
      _ok_sp and abs(s_sp.paid_towards.get("identity_cover", 0.0)
                     - _spent_sp) < 0.5,
      (s_sp.paid_towards, _spent_sp))
check("...and says so",
      "comes off the bill" in str(_why_sp), _why_sp)
s_sp.capital = 50000.0
s_sp.start_project("identity_cover")
check("...and beginning again bills only the remainder",
      abs(s_sp.active["identity_cover"]["cost_left"]
          - (s_sp.project_cost("identity_cover") - _spent_sp)) < 0.5,
      s_sp.active["identity_cover"]["cost_left"])
check("...but the hours really are gone: that was your year",
      abs(s_sp.active["identity_cover"]["ph_left"]
          - NODES["identity_cover"]["ph"]) < 1e-6,
      s_sp.active["identity_cover"]["ph_left"])
# And the affordability gate has to test the REMAINDER, or a nearly-paid-for
# project is refused for a bill it no longer owes.
s_sp2 = sim()
s_sp2.paid_towards = {"identity_cover": s_sp2.project_cost("identity_cover") - 5.0}
check("...and a nearly-paid project is not refused for its gross price",
      s_sp2.start_project("identity_cover")[0],
      s_sp2.start_reason("identity_cover"))


print("=" * 72)
print("%d checks, %d failures, %.0fs%s"
      % (len(CHECKS_RUN), len(FAILURES), sum(t for _, t in CHECKS_RUN),
         ("   (%d slow checks skipped: run with --slow)" % len(SKIPPED))
         if SKIPPED else ""))
slow = sorted(CHECKS_RUN, key=lambda r: -r[1])[:5]
if slow and slow[0][1] >= 5.0:
    print("slowest:")
    for nm, t in slow:
        if t >= 5.0:
            print("   %5.0fs  %s" % (t, nm))
for f in FAILURES:
    print("   FAILED:", f)
sys.exit(1 if FAILURES else 0)
