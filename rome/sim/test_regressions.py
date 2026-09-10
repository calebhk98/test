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
    print("  %-58s %s%s" % (name, "ok" if ok else "FAIL " + detail,
                            "   %4.0fs" % took if took >= 1.0 else ""))
    if not ok:
        FAILURES.append(name + " " + detail)


def proto(lines, civ="rome_100ad", kit=None):
    """Drive the real protocol in a real subprocess, as a player would."""
    cmd = [sys.executable, os.path.join(HERE, "simulator.py"), "agent", "--civ", civ]
    if kit:
        cmd += ["--kit", kit]
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
up_before = s.upkeep()
ok_mb, _ = s.mothball_work("fin_pawnshop")
check("a finished work can be shut down to stop its upkeep",
      ok_mb and s.upkeep() < up_before,
      "upkeep %.0f -> %.0f" % (up_before, s.upkeep()))

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
_menu_input = "1\ny\n\ny\n" + json.dumps({"cmd": "state"}) + "\n" + json.dumps({"cmd": "quit"}) + "\n"
_pm = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py")],
                     input=_menu_input, capture_output=True, text=True, timeout=120,
                     cwd=_menu_dir)
check("the menu says it is starting, not offering a command to run later",
      "Starting now" in _pm.stdout, _pm.stdout[-500:])
check("the menu names a resumable --session file ending in .json",
      "--session" in _pm.stdout and ".json --pretty" in _pm.stdout, _pm.stdout[-500:])
_saved = [f for f in os.listdir(_menu_dir) if f.endswith(".json")]
check("the menu's chosen session file actually exists on disk after playing",
      len(_saved) == 1, os.listdir(_menu_dir))
_menu_replies = []
for _ln in _pm.stdout.splitlines():
    _ln = _ln.strip()
    if _ln.startswith("{"):
        try:
            _menu_replies.append(json.loads(_ln))
        except ValueError:
            pass
_menu_states = [o for o in _menu_replies if isinstance(o, dict) and "year" in o and "capital" in o]
check("the menu drops straight into a playable session, no extra prompt",
      _pm.returncode == 0 and bool(_menu_states), _pm.stdout[-300:])
check("the mortality choice made in the menu reaches the actual game",
      bool(_menu_states) and _menu_states[-1].get("founder_ages") is True,
      _menu_states[-1] if _menu_states else None)

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

_shutil.rmtree(_loadtest_abs, ignore_errors=True)


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
