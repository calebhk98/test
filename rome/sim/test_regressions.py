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
s.revenue = lambda: 0.0        # force a loss regardless of the rest of the economy
s.shed_loss_makers(100)
check("shed_loss_makers cannot make the founder forget knowledge",
      _LOSS not in s.done and _KNOW1 in s.done,
      "loss-maker shed=%s knowledge shed=%s" % (_LOSS not in s.done, _KNOW1 not in s.done))
check("shed_loss_makers mothballs, and NAMES, what it takes",
      _LOSS in s.mothballed and any(_LOSS in m for _, m in s.log),
      [m for _, m in s.log])

s = sim(capital=-100000.0)
s.done.add(_LOSS); s.done.add(_KNOW2)
s.credit_limit = lambda: 0.0   # force straight past the credit floor
s.enforce_credit_limit(100)
check("creditors cannot seize knowledge either",
      _LOSS not in s.done and _KNOW2 in s.done,
      "loss-maker taken=%s knowledge taken=%s" % (_LOSS not in s.done, _KNOW2 not in s.done))
check("creditors' seizure mothballs, and NAMES, what it takes",
      _LOSS in s.mothballed and any(_LOSS in m for _, m in s.log),
      [m for _, m in s.log])

# --- C: a repossessed work must not look like fresh research
s = sim(capital=100000.0)
s.mothballed.add(_LOSS)
ok, why = s.start_reason(_LOSS)
check("a mothballed work refuses to be started as if it were new research",
      not ok and "restore" in why, why)
avail = S._agent_available(s, NODES, {"all": True})
check("a mothballed work does not appear in available looking like new research",
      not any(e["id"] == _LOSS for e in avail["available"]), avail["count"])

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
_saved = [f for f in os.listdir(_menu_dir) if f.endswith(".json")]
check("the menu's chosen session file actually exists on disk after playing",
      len(_saved) == 1, os.listdir(_menu_dir))
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
check("a hazard names things in front of you that hedge against it",
      any(e["can_begin_now"] for e in _steps),
      [(e["id"], e["can_begin_now"]) for e in _steps])
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
check("no command names a prerequisite of something you have not heard of",
      all(r.get("ok") is False and "never heard of" in (r.get("error") or "")
          for r in _bt),
      [r.get("error", "")[:70] for r in _bt])

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
_earned, _err = s.work_for_wages("labourer", s.director_pool())
check("hours sold as a labourer are not also spent practising medicine",
      _err is None and _rev_before > 0 and s.revenue() < _rev_before * 0.05,
      "revenue %.1f -> %.1f having sold every hour" % (_rev_before, s.revenue()))
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
_v, _, _ = proto([{"cmd": "start", "id": "fin_pawnshop"},
                  {"cmd": "step", "years": 6},
                  {"cmd": "money"},
                  {"cmd": "open", "id": "fin_pawnshop"},
                  {"cmd": "money"}], kit="equestrian")
_before, _open, _after = _v[2], _v[3], _v[4]
check("working out how to do something does not by itself pay you",
      "fin_pawnshop" not in (_before.get("where_the_money_comes_from") or {}),
      _before.get("where_the_money_comes_from"))
check("opening the doors is what pays you",
      _open.get("ok") is True
      and (_after.get("where_the_money_comes_from") or {}).get("fin_pawnshop"),
      _after.get("where_the_money_comes_from"))

s2 = sim(capital=200000.0)
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
_heavy = [k for k in NODES if NODES[k]["art"] >= 3 and NODES[k]["rev"] > 0][:1]
if _heavy:
    s3.done.add(_heavy[0]); s3._done_changed()
    s3.artisans = 0.0
    _okh, _whyh = s3.open_venture(_heavy[0])
    check("a concern nobody is free to run cannot be opened",
          _okh is False and "nobody free" in (_whyh or ""), _whyh)

# Shutting it stops both sides and keeps the knowledge.
s4 = sim(capital=200000.0)
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
_rt, _, _ = proto([{"cmd": "start", "id": "fin_pawnshop"},
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
      and any("work for wages" in w for w in _diag["what_would_change_it"]),
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
