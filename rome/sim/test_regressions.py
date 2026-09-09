#!/usr/bin/env python3
"""Every bug a playtester found, as a test that fails if it comes back.

Nine of these were found by agents playing the game through the JSON protocol,
and three of those were defects in the fix for the previous one. That pattern is
the reason this file exists: a fix verified once by hand is a fix that silently
rots. Run it with `python3 rome/sim/test_regressions.py`.
"""
import json, os, random, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import simulator as S

TREE, PRICES, NODES, WAGES, GOODS = S.load()
GOAL = TREE["meta"]["goal_node"]
_LAB, ORDER, _B = S.load_strategy("recommended", NODES, GOAL)
FAILURES = []


def sim(civ="rome_100ad", capital=None, manual=True, events=False):
    cfg = {"start_capital": capital} if capital is not None else None
    s = S.Sim(NODES, ORDER, random.Random(1), events=events, manual=manual,
              civ=S.load_civ(civ), cfg=cfg)
    s.goal, s.done_year = GOAL, {}
    return s


def check(name, ok, detail=""):
    print("  %-58s %s" % (name, "ok" if ok else "FAIL " + detail))
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
r, _, _ = proto([{"cmd": "state"}], civ="norse_900ad")
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
r, _, _ = proto([{"cmd": "available"}])
offered = {a["id"] for a in r[0]["available"]} & early
check("no advanced physics is startable in year one", not offered, str(offered))

# --- naive A: debasement must not make everything cheaper
s = sim()
base = s.cost_money_factor()
s.money_real = 0.005
check("a debased currency does not collapse prices",
      abs(s.cost_money_factor() - base) < 1e-9,
      "%.4f -> %.4f" % (base, s.cost_money_factor()))

# --- reproducibility: the same seed must give the same answer
outs = set()
for _ in range(2):
    p = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py"),
                        "run", "--mc", "3", "--seed", "42"],
                       capture_output=True, text=True, timeout=600, cwd=ROOT)
    outs.add(p.stdout)
check("the same seed gives the same result", len(outs) == 1)

print("=" * 72)
print("%d checks, %d failures" % (20, len(FAILURES)))
for f in FAILURES:
    print("   FAILED:", f)
sys.exit(1 if FAILURES else 0)
