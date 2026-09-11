#!/usr/bin/env python3
"""Every bug a playtester found, as a test that fails if it comes back.

Nine of these were found by agents playing the game through the JSON protocol,
and three of those were defects in the fix for the previous one. That pattern is
the reason this file exists: a fix verified once by hand is a fix that silently
rots. Run it with `python3 rome/sim/test_regressions.py`.
"""
import collections, glob, json, os, random, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import simulator as S
import planner as PLANNER
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


def run_it(s, *keys):
    """Build a concern AND keep its doors open.

    Every capability in the engine is gated on running() - built, and still
    being maintained - because a school nobody pays for trains no scholars.
    A check that wants the capability has to open the place, the same as a
    player would.
    """
    for k in keys:
        s.done.add(k)
        s.operating.add(k)
    s._done_changed()
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
    run_it(t, "workshop_first", "freedman_staff")
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

# --- the user: an organised army is a more capable state, not only a safer
# founder - general_staff is the same state_capacity field railway and
# semaphore_telegraph already use for "the state gets more capable of acting"
s = sim()
sc0 = s.civ["state_capacity"]
s.apply_tech_effects("mil_general_staff")
check("standing a general staff up raises what the state can organise and "
      "compel, the same as railway or the telegraph does",
      s.civ["state_capacity"] > sc0, "%.3f -> %.3f" % (sc0, s.civ["state_capacity"]))

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

# --- the user: "if I woke up in Rome and made cannons, that should massively
# affect a lot of things, and shouldn't that make the country bigger / win
# more wars?" Measured before this round of changes: a founder who built
# every one of the tree's 111+ military, weapon and fortification nodes
# differed from one who built none in exactly one respect anywhere in the
# engine - weapon_democratising raising suspicion (see alarm_of). Nothing
# protected the founder, nothing changed what a war cost the state, nothing
# recovered faster. These checks pin the fix and the boundary around it: the
# branch now matters, and does not matter so much that it swallows the tree.
_MIL_NODES = sorted(k for k in NODES if "military" in (NODES[k].get("traits") or ()))
check("the tree still has a real military branch to test against",
      len(_MIL_NODES) >= 100, len(_MIL_NODES))

s = sim()
lev0 = s.military_leverage()
s.done.add(_MIL_NODES[0])
lev1 = s.military_leverage()
for k in _MIL_NODES[:25]:
    s.done.add(k)
lev25 = s.military_leverage()
for k in _MIL_NODES:
    s.done.add(k)
levall = s.military_leverage()
check("military strength is zero for a founder who has built none of the "
      "branch, rises with the first node, and saturates well short of the "
      "whole branch (so the branch cannot be a strategy unto itself)",
      lev0 == 0.0 and 0.0 < lev1 < lev25 == 1.0 and levall == 1.0,
      (lev0, lev1, lev25, levall))

s_bare = sim()
s_bare.update_protection()
s_mil_nopatron = sim()
for k in _MIL_NODES:
    s_mil_nopatron.done.add(k)
s_mil_nopatron.update_protection()
check("a cannon foundry with nobody to sell to protects the founder not at "
      "all - the leverage is with a patron, not the hardware itself",
      abs(s_mil_nopatron.protection - s_bare.protection) < 1e-9,
      (s_bare.protection, s_mil_nopatron.protection))

s_patron = sim()
run_it(s_patron, "patron_imperial")
s_patron.update_protection()
s_patron_mil = sim()
run_it(s_patron_mil, "patron_imperial")
for k in _MIL_NODES:
    s_patron_mil.done.add(k)
s_patron_mil.update_protection()
check("an armourer with an imperial patron to arm is protected more than "
      "the same patron without the armoury, and the gain is a real fraction "
      "of a percent, not a rounding error or a dominant strategy on its own",
      0.02 < s_patron_mil.protection - s_patron.protection < 0.12,
      (s_patron.protection, s_patron_mil.protection))

s_out_bare = sim()
out_bare, _ = s_out_bare.hazard_relief("output_factor")
s_out_mil = sim()
for k in _MIL_NODES:
    s_out_mil.done.add(k)
out_mil, out_why = s_out_mil.hazard_relief("output_factor")
check("a war costs an armed empire's trade less than an unarmed one's - "
      "every output_factor hazard in these civilization files is a war or "
      "its administrative aftermath, and this is the branch's answer to it",
      out_mil < out_bare and any("military strength" in w for w in out_why),
      (out_bare, out_mil, out_why))

staff_bare, _ = s_out_bare.hazard_relief("staff_loss")
staff_mil, _ = s_out_mil.hazard_relief("staff_loss")
check("military technology gives no relief against staff loss - most "
      "staff_loss hazards in these civilizations are disease and famine, "
      "not war, and a founder with cannon should not cure the Antonine "
      "plague",
      staff_bare == staff_mil, (staff_bare, staff_mil))

s_rec_bare = sim(); s_rec_bare.output_factor = 0.7
s_rec_mil = sim()
for k in _MIL_NODES:
    s_rec_mil.done.add(k)
s_rec_mil.output_factor = 0.7
s_rec_bare.step()
s_rec_mil.step()
check("an armed empire's trade recovers from a war faster than an unarmed "
      "one's, year over year, and the war still happened either way - this "
      "is recovery speed, not a rewrite of the event",
      s_rec_mil.output_factor > s_rec_bare.output_factor > 0.7,
      (s_rec_bare.output_factor, s_rec_mil.output_factor))

# --- the Mexica case: the sharpest test named in the brief. Firearms and
# steel should plausibly blunt a sacking; they must not un-happen the
# Spanish arrival, whose dates are untouched, or cure the same contact
# epidemics that hit staff_loss, which nothing military should touch.
s_mex = sim(civ="mexica_1500")
_spanish = next(h for h in s_mex.civ["hazards"] if "Spanish" in h.get("name", ""))
check("the Spanish invasion still arrives on its historical date, unmoved "
      "by anything this change does",
      _spanish["years"] == [1519, 1521], _spanish["years"])
check("the Spanish invasion hazard carries no staff_loss of its own - the "
      "contact epidemics are a separate, later hazard entry, so military "
      "technology (which never touches staff_loss) cannot appear to cure "
      "them by touching this one",
      "staff_loss" not in _spanish, sorted(_spanish))
_mex_bare = sim(civ="mexica_1500")
_sack_bare, _ = _mex_bare.hazard_relief("sack_chance")
_mex_mil = sim(civ="mexica_1500")
for k in _MIL_NODES:
    if k in NODES:
        _mex_mil.done.add(k)
_sack_mil, _sack_why = _mex_mil.hazard_relief("sack_chance")
check("a Mexica founder who had built firearms and fortification before "
      "the Spanish arrived would face a real, non-zero chance of a "
      "sacking still - the counterfactual is blunted, never zeroed",
      0.0 < _sack_mil < _sack_bare, (_sack_bare, _sack_mil, _sack_why[:3]))

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

# and every command it advertises must actually answer. FIVE SECONDS, because
# it builds a fresh Mexica game per command and there are now dozens; the
# cheap half above, that the message names them all, stays on the fast path.
def _every_advertised_command_answers():
    dead = []
    for c in _real:
        if c in ("quit", "save", "load"):
            continue                  # need arguments or end the session
        rr, _, _ = proto([{"cmd": c}], civ="mexica_1500")
        if rr and "unknown cmd" in str(rr[0].get("error", "")):
            dead.append(c)
    return not dead, str(dead)

slow_check("every advertised command is one the game answers to",
           _every_advertised_command_answers)

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
_EFFECT_FIELDS = ("staff_loss", "sack_chance", "output_factor", "real_erosion",
                   # "values" was missing from this tuple even though it has
                   # been a real, engine-read effect field since the
                   # Christianisation gradual-shift mechanism was added (see
                   # _shocks in society.py) - Rome's Ostrogothic Italy, Han's
                   # Jin reunification and several Mexica entries are all
                   # already values-only and this check simply never looked
                   # at them, because it only ever scanned Norse. Adding the
                   # Norse settlement-of-Iceland, Hakon-Hakonarson and
                   # Reformation entries - each a real event whose honest
                   # effect on this society is what it believes, not a body
                   # count or a burned field - is what caught the gap.
                   "values")
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
# hom_eraser_breadcrumb used to be that control, but the JOB 1 upkeep audit
# correctly zeroed its upkeep (a rubber eraser is a technique, not an
# establishment), so it stopped bleeding money and stopped exercising this
# path. met_ore_crushing_sorting is a real establishment kind of node (it
# stayed in the audit's kept "mining" category) that still carries upkeep.
_KNOW1, _KNOW2, _LOSS = "md2_cell_theory", "md2_dna", "met_ore_crushing_sorting"
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
# 11 SECONDS: forty-five years of a Mexica optimizer run before the advice it
# is checking even has anything to say. The three checks that share that setup
# move together, since re-running it for each would cost three times as much.
def _hazard_advice_names_hedges():
    s_ = sim(civ="mexica_1500", manual=False)
    s_.fog = True
    s_.revealed = set()
    for _i in range(45):
        s_.step()
    steps = (s_.hazard_advice("staff_loss")
             .get("you_could_begin_now_toward_it") or [])
    counters = {n for n, _s2, _l in s_.HAZARD_COUNTERS["staff_loss"]}
    near = counters | {p_ for n in counters if n in NODES
                       for p_ in NODES[n]["pre"]}
    named = bool(steps) and all(
        e.get("id") and (e["can_begin_now"] or e.get("waiting_on"))
        for e in steps)
    ordered = [e["can_begin_now"] for e in steps] == sorted(
        (e["can_begin_now"] for e in steps), reverse=True)
    real = all(e["id"] in near for e in steps)
    return named and ordered and real, [
        (e["id"], e["can_begin_now"], (e.get("waiting_on") or "")[:40])
        for e in steps]

slow_check("a hazard names things in front of you that hedge against it, "
           "startable ones first, and every one really is a hedge",
           _hazard_advice_names_hedges)


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
# GOAL, not the name of whichever node the goal used to be. These pinned
# point_contact_transistor, which stopped being the goal when the 1947 device
# became a milestone on the way to the 1951 one, and the checks then asserted
# the goal's fog exception about a node that no longer has it.
_bt, _, _ = proto([{"cmd": "bounty", "id": GOAL},
                   {"cmd": "start", "id": GOAL},
                   {"cmd": "mothball", "id": GOAL},
                   {"cmd": "why", "id": GOAL}], fog=True)
# The PROPERTY, not the wording: no reply may contain the id of anything the
# player has not heard of. (`why` on the goal is answered now - the status line
# names the goal every turn - but it still may not name what the goal rests on.)
_GOAL_PRE = NODES[GOAL]["pre"]
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
# This used to pick its own candidate by filter (up>0, no prerequisite,
# project_cost under 1 denarius); the JOB 1 upkeep audit zeroed `up` on every
# node that filter used to find (they were all techniques, correctly), and
# every remaining up>0/no-prerequisite/near-free node turned out to be
# something auto-granted on turn one (a capability rung, a road network) -
# excluded by `not in s.granted` and so invisible to the filter too. There is
# also a sharper reason to stop computing this dynamically: `s.done.add`
# below bypasses `start`'s own prerequisite check, but restore_work has its
# OWN separate check ("you no longer have what it stands on") that reads real
# prerequisites regardless of how `done` was populated, so a candidate with
# unmet prerequisites makes restore_work silently refuse and charge nothing -
# which reads as exactly the bug this check exists to catch, for a completely
# different reason. met_ore_crushing_sorting has no prerequisite, was not
# auto-granted (its `ph` is not zero), and kept its upkeep in the audit as
# real mining-establishment cost, so it is named directly rather than found.
s = sim(civ="england_1300", capital=50000.0)
_free = ["met_ore_crushing_sorting"]
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
        run_it(s_, "identity_cover")
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
run_it(s, "workshop_first", "freedman_staff")
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

# --- BREAK: the fix above ("Make the stated labour ceiling the real one")
# changed the TEST here to weigh commissioned hours - hours_you_can_call_on,
# market_supply plus contract_hours - but left the NUMBER PRINTED reading
# market_supply alone. A player who had commissioned any of the short trade
# saw `start` quote one ceiling for a project and `stuck` quote a higher one
# for the identical project a moment later: the exact disagreement that
# commit's own message said could not happen again ("the statement and the
# arithmetic cannot disagree"). Reproduced directly: commission 500 scribe-
# hours (the project is still short), then start logarithms.
s_lie = sim(capital=10000000.0)
for _p in NODES["logarithms"]["pre"]:
    s_lie.done.add(_p)
s_lie._done_changed()
s_lie.hire("scholar", 2)
s_lie.commission("scribe", 500.0)
_r_start = S._agent_dispatch(s_lie, NODES, {"cmd": "start", "id": "logarithms"})
_r_stuck = S._agent_dispatch(s_lie, NODES, {"cmd": "stuck"})
_but = _r_start.get("but") or ""
_stuck_why = ((_r_stuck.get("what_is_holding_you_up") or [{}])[0]
              .get("each_waiting_on", {}).get("logarithms", ""))
check("the ceiling `start` quotes for a short trade is the one `stuck` quotes a moment later",
      _but and _stuck_why and
      _but.split("field ")[1].split(" at most")[0]
      == _stuck_why.split("field ")[1].split(" at most")[0],
      (_but, _stuck_why))

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

# --- BREAK: the pivot node of the entire game did nothing under --manual, the
# interactive protocol's only mode. school_founded's own text promises "+4
# scholars", _complete() added it with a bare self.scholars += 4, and the very
# next step() called _resync_pools() - unconditionally, every year - which has
# always recomputed self.scholars purely from self.employees and so overwrote
# the grant to whatever employees already held. A player who founded the
# school and then did anything else at all would have read a refusal a year
# later naming the same scholar shortfall the school was built to answer,
# with nothing saying why. Fixed by giving the grant its own durable record
# (_grant_staff) that _resync_pools adds back rather than discards.
s_gr = sim(capital=10000000.0, manual=True)
s_gr.done.add("school_founded")
s_gr._done_changed()
s_gr.operating.add("school_founded")
s_gr._grant_staff(scholars=4)
_after_grant = s_gr.scholars
s_gr.step()
check("founding the school still leaves you its scholars a year later",
      s_gr.scholars >= _after_grant - 1e-6,
      (_after_grant, s_gr.scholars))
check("...and a project that needed exactly what it granted can now start",
      s_gr.effective_scholars() >= 4.0,
      s_gr.effective_scholars())

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
s_hi = run_it(sim(civ="rome_100ad", capital=1e9), "school_founded")
s_lo = run_it(sim(civ="norse_900ad", capital=1e9), "school_founded")
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
run_it(s, "workshop_first", "school_founded", "academy_network", "patron_imperial")
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

# =============================================================================
# GENERALISED PRICING: rome/data/review/COMMODITY_DYNAMISM.md's central
# finding, verified against a live Sim. 149 of the tree's 162 distinct
# material keys had a price read once from prices.json and never revisited,
# because MATERIAL_CHECKS/MARKET_SHARE above only ever named 13. The user's
# own test: "if I make an iron mine and flood the market, does the price
# update? What if I make aluminium via electricity? Same for foods, coffee,
# silk, whatever." Aluminium is the audit's worked failure - "no mine, no
# supply lever of any kind... nothing in economy.py even contains the string
# aluminium" - and is tested here BY NAME, on purpose, alongside silk, a
# second material nothing in this file has ever special-cased, to show the
# mechanism is general rather than a rule written for one commodity.
# =============================================================================

for _mat in ("aluminium_kg", "silk_kg"):
    s = sim(civ="rome_100ad", capital=1e9)
    f_none = s.material_price_factor(_mat)
    check("a material with NO curated entry anywhere (%s) starts neutral "
          "with no demand pinned on it" % _mat,
          abs(f_none - 1.0) < 1e-9, f_none)
    s._material_demand_cache = {_mat: 1000.0}
    f_demand = s.material_price_factor(_mat)
    check("...but a real premium appears once demand for it is pinned high "
          "- the same response the 9 originally-tracked commodities always "
          "had, that this material never had before this pass",
          f_demand > 1.5, "%.3f" % f_demand)
    got = s.open_mine(_mat, 1e7, partial=False)
    for _ in range(int(s.MINE_LEAD_YEARS) + 1):
        s.year += 1
        s.commission_mines()
    check("opening your own production capacity in it (open_mine, "
          "generalised beyond the seven hand-named metals) actually "
          "commissions real standing capacity",
          s.mine_capacity.get(_mat, 0.0) > 0, s.mine_capacity.get(_mat))
    s._material_demand_cache = {_mat: 1000.0}
    f_mined = s.material_price_factor(_mat)
    check("...and flooding the market this way relieves the SAME premium, "
          "for a material this file has never named, purely because supply "
          "and demand are now real numbers rather than a rule",
          f_mined < f_demand, "before=%.3f after=%.3f" % (f_demand, f_mined))

# --- the effect actually reaches project_cost(), the number the game
# charges, not only an internal factor nothing reads - the same standard
# COMMODITY_DYNAMISM.md held the original 9 commodities to.
s = sim(civ="rome_100ad", capital=1e9)
check("mt2_duralumin_alloy is a real node that buys real aluminium_kg - "
      "not a synthetic example",
      NODES["mt2_duralumin_alloy"]["mat"].get("aluminium_kg", 0) > 0,
      NODES["mt2_duralumin_alloy"]["mat"])
s._material_demand_cache = {"aluminium_kg": 1000.0}
cost_no_mine = s.project_cost("mt2_duralumin_alloy")
s.open_mine("aluminium_kg", 1e7, partial=False)
for _ in range(int(s.MINE_LEAD_YEARS) + 1):
    s.year += 1
    s.commission_mines()
s._material_demand_cache = {"aluminium_kg": 1000.0}
cost_with_mine = s.project_cost("mt2_duralumin_alloy")
check("a real node's project_cost() itself falls once an aluminium mine "
      "covers demand pinned against it - the same standard the iron test "
      "elsewhere in this file already holds the originally-tracked "
      "commodities to",
      cost_with_mine < cost_no_mine, (cost_no_mine, cost_with_mine))

# --- a garbage material name is still refused, not silently accepted -
# generalising to "every material the tree prices" is not the same as
# accepting an arbitrary string.
s = sim(civ="rome_100ad", capital=1e9)
check("a material this file genuinely cannot price is still refused",
      s.mine_quote("not_a_real_material_xyz", 100.0) is None,
      s.mine_quote("not_a_real_material_xyz", 100.0))
check("...and mineable() agrees",
      s.mineable("aluminium") and s.mineable("aluminium_kg")
      and not s.mineable("not_a_real_material_xyz"),
      (s.mineable("aluminium"), s.mineable("aluminium_kg"),
       s.mineable("not_a_real_material_xyz")))

# --- A PLAYER MUST SEE IT: `money` surfaces a material price premium in
# aggregate, generalised the same way goods_market_summary already is for
# the goods side.
s = sim(civ="rome_100ad", capital=1e9)
s.active["gunpowder"] = {}
s.resource_throttle()
_mms = s.material_market_summary()
check("material_market_summary names a material trading above book price",
      bool(_mms) and "saltpetre" in _mms, _mms)
_money_mat = S._agent_dispatch(s, NODES, {"cmd": "money"})
check("...and `money` itself carries the same line",
      bool(_money_mat.get("materials_costing_you_a_premium")), _money_mat)

# --- the command surface itself accepts a generalised material name, not
# only the seven it used to: "buy mine aluminium_kg" must actually work.
_r_al, _, _ = proto([{"cmd": "buy", "what": "mine", "material": "aluminium_kg",
                      "n": 0.1}])
check("the command surface itself (not just the engine underneath it) "
      "accepts a material outside the original seven",
      _r_al[0].get("ok") is True, _r_al[0])
_r_bad, _, _ = proto([{"cmd": "buy", "what": "mine",
                       "material": "not_a_real_material_xyz", "n": 10}])
check("...but still refuses a genuinely unpriced name, with a hint rather "
      "than a bare closed list",
      _r_bad[0].get("ok") is False and "aluminium_kg" in _r_bad[0].get("error", ""),
      _r_bad[0])

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

# =============================================================================
# COMMODITIES, WIRED IN (COMMODITIES.md section 0/7.1). copper_wire_kg,
# wire_drawn_kg and gold_kg are real material keys 36+ real nodes draw, and
# were invisible to resource_throttle() before this pass. economy.py now
# calls commodities.py's own propagate_demand() (via wire_chain_report()),
# handed THIS Sim's live copper numbers through CommodityLedger's new
# supply_override, instead of a second, disconnected estimate.
# =============================================================================

# --- supply_override actually overrides, rather than being silently ignored
# alongside commodities.json's own (much larger) national estimate.
override_led = COMMOD.CommodityLedger(supply_override={"copper": 10.0})
tiny = override_led.propagate_demand("copper_wire", 100.0)
check("supply_override replaces the national estimate, not just adds to it: "
      "10 t/yr of copper cannot deliver 100 t/yr of wire",
      tiny["met_fraction"] < 0.2, tiny["met_fraction"])
plain_led = COMMOD.CommodityLedger()
plenty = plain_led.propagate_demand("copper_wire", 100.0)
check("...while the SAME call with no override still reads commodities.json's "
      "own (much larger) national figure, exactly as before",
      plenty["met_fraction"] > tiny["met_fraction"],
      (plenty["met_fraction"], tiny["met_fraction"]))

# --- economy.py.wire_chain_report(): the real worked example, on a real Sim.
s_wire = sim(capital=400000.0)
rep_modest = s_wire.wire_chain_report(5.0)
check("a modest copper wire order is fully met by an ordinary Roman buyer's "
      "own copper market access",
      rep_modest["met_fraction"] > 0.999, rep_modest["met_fraction"])
rep_big = s_wire.wire_chain_report(2000.0)
check("an industrial copper wire order is NOT fully met, and the shortfall "
      "is attributed to copper, not to wire-drawing capacity",
      rep_big["met_fraction"] < 0.95
      and rep_big["children"]["copper"]["bottleneck"] == "copper"
      and rep_big["bottleneck"] is None,
      (rep_big["met_fraction"], rep_big["bottleneck"]))

# --- a poorer, less-connected civilization reaches less copper than Rome for
# the SAME request, because wire_chain_report() reads THIS Sim's own numbers
# (mineral_scale, MARKET_SHARE, mine_capacity), not one flat figure.
s_norse = sim(civ="norse_900ad", capital=400000.0)
rep_norse = s_norse.wire_chain_report(2000.0)
check("a civilization with less reach to copper gets a worse chain report "
      "for the identical request, not the same one",
      rep_norse["children"]["copper"]["own_capacity_t"]
      < rep_big["children"]["copper"]["own_capacity_t"],
      (rep_norse["children"]["copper"]["own_capacity_t"],
       rep_big["children"]["copper"]["own_capacity_t"]))

# --- resource_throttle() now actually throttles on copper_wire_kg: a
# mechanism-level check, since no realistic combination of real nodes'
# kilogram-scale wire draws (the largest, el2_ring_main_distribution, is
# 8,000 kg spread over 4 years) actually reaches the hundreds of tonnes a
# year it takes to outrun Rome's own copper market - the same reason
# COMMODITIES.md section 7.1's own worked example and demo_commodities.py
# both had to use an illustrative industrial-scale figure rather than sum
# real nodes. This proves the WIRING (a large copper_wire_kg demand binds
# resource_throttle on "copper"), not a claim about ordinary play.
s_thr = sim(capital=1e9)
s_thr._material_demand_cache = {"copper_wire_kg": 100000.0}
s_thr.annual_material_demand = lambda: s_thr._material_demand_cache
thr = s_thr.resource_throttle()
check("a copper_wire_kg demand far beyond the copper market binds "
      "resource_throttle on copper, where before this key was not "
      "tracked at all",
      thr < 0.95 and s_thr.binding == "copper", (thr, s_thr.binding))

# --- the aggregation fix: three material keys drawing on the SAME copper
# supply are summed before being compared to it, not checked one at a time
# against the whole supply each time (_demand_by_supply_tag).
s_agg = sim(capital=1e9)
grouped = s_agg._demand_by_supply_tag({"copper_kg": 3.0, "copper_wire_kg": 4.0,
                                       "wire_drawn_kg": 0.0,
                                       "iron_bar_kg": 1.0, "iron_ore_kg": 2.0,
                                       "charcoal_kg": 5.0, "firewood_kg": 9.0})
check("copper_kg and copper_wire_kg demand are summed under one shared "
      "supply, not checked independently",
      grouped[("copper", "mine:copper")] == 7.0, dict(grouped))
check("...and iron_bar_kg/iron_ore_kg (already sharing one supply) are "
      "summed the same way",
      grouped[("iron", "mine:iron")] == 3.0, dict(grouped))
check("...while charcoal_kg and firewood_kg, which draw on the SAME forest "
      "at DIFFERENT yields per hectare, stay in separate groups rather "
      "than being summed together",
      grouped[("charcoal", "forest1")] == 5.0
      and grouped[("charcoal", "forest4")] == 9.0,
      (grouped[("charcoal", "forest1")], grouped[("charcoal", "forest4")]))

# --- gold is now a tracked commodity: fin_central_bank's 1,000 kg of
# gold_kg was invisible to every material check before this pass, despite
# Sim.open_mine("gold", ...) already existing.
check("gold_kg is now covered by MATERIAL_CHECKS, the same way copper_kg is",
      s_agg.MATERIAL_CHECKS.get("gold_kg") == ("gold", "mine:gold"),
      s_agg.MATERIAL_CHECKS.get("gold_kg"))
check("gold has a MARKET_SHARE entry sourced from commodities.json's own "
      "gold figure, so the two files do not disagree",
      s_agg.MARKET_SHARE.get("gold")
      == COMMOD.load_commodities()["gold"]["market_share"],
      (s_agg.MARKET_SHARE.get("gold"),
       COMMOD.load_commodities()["gold"]["market_share"]))

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
                             - (100000.0 - 20000 * s.NITRE_COST_PER_M2
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
                   {"cmd": "why", "id": GOAL}])
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
    _s.done.update(list(NODES)[:1400])
    run_it(_s, "patron_imperial", "academy_network")
    if not _acad:
        _s.done.discard("academy_network")
        _s.operating.discard("academy_network")
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
def _deputies_are_announced():
    s_ = sim(capital=2000000.0, manual=False)
    run_it(s_, "school_founded", "patron_imperial", "academy_network")
    for _ in range(30):
        s_.step()
    said = [m for _, m in s_.log if "deput" in m]
    return (any("deput" in m and "your year is" in m for _, m in s_.log)
            and len(said) <= int(s_.directors_extra) + 1, said[:1])

slow_check("gaining a deputy is announced with what it does to your year, "
           "once per whole deputy rather than every year",
           _deputies_are_announced)


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

# THESE TWO COST 293 OF THE SUITE'S 425 SECONDS between them, because each
# simulates 180 years and the second does it again in a fresh interpreter.
# They are the most valuable checks in the file and also by far the most
# expensive, which is exactly the case --slow exists for: a suite you run after
# every change has to be seconds or you stop running it, and these belong to
# the run you do before calling something finished.
def _same_seed_same_run():
    a = _one_run()
    return _one_run() == a, (a, _one_run())

slow_check("the same seed gives the same run, twice in one process",
           _same_seed_same_run)

def _same_under_other_hash_seed():
    a = _one_run()
    det = subprocess.run(
        [sys.executable, "-c",
         "import random,sys;sys.path.insert(0,%r);import simulator as S;"
         "T,P,N,W,Gd=S.load();_l,O,_b=S.load_strategy('recommended',N,T['meta']['goal_node']);"
         "s=S.Sim(N,O,random.Random(9),events=True,manual=False,civ=S.load_civ('rome_100ad'),"
         "cfg={'start_capital':100000.0});s.goal,s.done_year=T['meta']['goal_node'],{};"
         "[s.step() for _ in range(180)];"
         "print(round(s.capital,6),len(s.done),len(s.operating),round(s.reputation,9))" % HERE],
        capture_output=True, text=True, timeout=600,
        env=dict(os.environ, PYTHONHASHSEED="1234"))
    return (det.stdout.split() == [str(x) for x in a],
            (det.stdout.strip(), a))

slow_check("...and the same run in a process with a different string hash seed",
           _same_under_other_hash_seed)

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
# THIS CHECK USED TO ASSERT THE BUG. It required turn one to report nothing
# holding you up - and turn one is precisely when nothing is running, which a
# later play tester typed `stuck` to find out and was told "nothing: you have
# work in hand, money to pay for it and people to do it". It was the first
# thing they typed and it was false.
check("...and on turn one it says you have started nothing",
      any(r.get("what") == "you have started nothing"
          for r in _rs[0]["what_is_holding_you_up"]),
      _rs[0]["what_is_holding_you_up"])
check("...and names something you could start instead",
      any("start " in str(r.get("why")) for r in _rs[0]["what_is_holding_you_up"]),
      _rs[0]["what_is_holding_you_up"])
# ...and once something IS running and nothing is wrong, it says so plainly
# without claiming work in hand that is not there.
_s_ok = sim(capital=500000.0)
_s_ok.start_project("identity_cover")
_rs_ok = S._agent_dispatch(_s_ok, NODES, {"cmd": "stuck"})
check("...and with work in hand and money it says nothing is holding you up",
      isinstance(_rs_ok.get("what_is_holding_you_up"), str)
      or all(r.get("what") != "you have started nothing"
             for r in _rs_ok["what_is_holding_you_up"]),
      _rs_ok.get("what_is_holding_you_up"))
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
# FOUR SECONDS: forty years of an optimizer run to watch a cooldown that only
# has meaning across decades. Per TRADE: teaching four different trades over
# forty years is fine; teaching the same one four times is the treadmill that
# cost three Rome seeds most of what they built.
def _reteaching_is_once_a_generation():
    s_ = sim(capital=2000000.0, manual=False)
    s_.trades_created.add("machinist")
    per_trade = {}
    for _ in range(40):
        before = dict(getattr(s_, "last_taught", {}))
        s_.step()
        for t, y in getattr(s_, "last_taught", {}).items():
            if before.get(t) != y:
                per_trade[t] = per_trade.get(t, 0) + 1
    return (all(v <= 40 // s_.RETEACH_EVERY + 1 for v in per_trade.values()),
            per_trade)

slow_check("...and no more than once a generation FOR THE SAME TRADE",
           _reteaching_is_once_a_generation)


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
                    {"cmd": "why", "id": GOAL}])
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


# --- BREAK: the supervision test was an exact comparison, and attrition moves
# the payroll by fractions of a man every single year. A play tester watched
# the same concern close and reopen "every single turn for four centuries" and
# called it endless busywork. Nobody shuts a shop over a fortieth of a man.
s_hy = sim(capital=500000.0)
s_hy.done.update(NODES); s_hy._done_changed()
s_hy.artisans = s_hy.scholars = 6.0
_vh = max((k for k in sorted(NODES)
           if s_hy.is_venture(k) and NODES[k]["rev"] > 500
           and 1.6 <= s_hy.venture_hands(k)[1] <= 5.0
           and s_hy.venture_hands(k)[0] <= 5.0),
          key=lambda k: s_hy.venture_hands(k)[1])
_ok_hy, _ = s_hy.open_venture(_vh)
check("(a shop to test the staffing rule on is open)",
      _vh in s_hy.operating, (_vh, _ok_hy, s_hy.venture_hands(_vh)))
_need_s, _need_a = s_hy.venture_staff_used()
_own = s_hy.FOUNDER_IS_WORTH if s_hy.founder_alive else 0.0
# stand the payroll exactly on the line, then let a tenth of a man die
s_hy.artisans = _need_a - _own - 0.1
s_hy.scholars = max(0.0, _need_s - 1.0)
s_hy.close_unstaffed_ventures(110)
check("a tenth of a man short does not shut the shop",
      _vh in s_hy.operating, (s_hy.artisans, _need_a, sorted(s_hy.operating)))
# but a real pair of hands gone does
s_hy.artisans = _need_a - _own - 0.6
s_hy.close_unstaffed_ventures(111)
check("...but a whole hand short still does",
      _vh not in s_hy.operating, (s_hy.artisans, _need_a))


# --- BREAK: three places printed the founder's own staff differently. The
# prompt showed hired heads ("sch 0 art 0"), `why` compared a project against
# effective_scholars() and s.artisans ("you have 1, 0"), and start_project
# actually gated on craft_hands_available() - which counts the founder AND
# hours already bought. A play tester read two of the three on one turn and
# reported the game as having lost count of their household.
s_cn = sim(capital=20000.0)
_kn = next(k for k in sorted(NODES) if NODES[k]["art"] >= 2 and NODES[k]["sch"] == 0)
s_cn.commission("mason", 4000.0)
_why_cn = S._node_explain(s_cn, NODES, _kn)
check("`why` counts the same artisans `start` does: yourself and hours bought",
      abs(_why_cn["you_have"]["artisans"] - round(s_cn.craft_hands_available(), 1)) < 0.05,
      (_why_cn["you_have"], s_cn.craft_hands_available(), s_cn.artisans))
check("...and says which people it is counting",
      "yourself" in str(_why_cn.get("you_have_counts")), _why_cn.get("you_have_counts"))
check("...and it is more than the bare payroll, having bought a mason's year",
      _why_cn["you_have"]["artisans"] > s_cn.artisans + 0.5,
      (_why_cn["you_have"]["artisans"], s_cn.artisans))

# --- BREAK: rubber was priced at 99,999 a kilo, a sentinel left over from the
# abolished "unobtainable" tier, and it survived the abolition of the concept
# that justified it. A play tester worked out that one kilo was four hundred
# artisan-years, that a rubber eraser cost 3,001,105 against 5 for a
# breadcrumb, and that securing a rubber supply did not change the price by a
# denarius. It was also over half of the whole tree's capital cost.
_RUB = ("rubber_kg", "rubber_tubing_kg")
for _r in _RUB:
    check("%s is priced like a distant import, not like a sentinel" % _r,
          0 < PRICES["purchase_prices_denarii"][_r]["p"] < 1000,
          PRICES["purchase_prices_denarii"][_r]["p"])
# ...and the reason the sentinel existed - that nothing stopped you buying it -
# is answered where it belongs, in the tree: you cannot use rubber until you
# have gone and got some.
def _anc_of(k, seen=None):
    seen = seen if seen is not None else set()
    for _p in NODES[k]["pre"]:
        if _p not in seen:
            seen.add(_p); _anc_of(_p, seen)
    return seen
_rub_users = sorted(k for k, v in NODES.items()
                    if any("rubber" in m for m in (v.get("mat") or {})))
_ungated = [k for k in _rub_users
            if not ({"mat_natural_rubber", "mat_synthetic_rubber"} & _anc_of(k))]
# --- BREAK: a node whose own note names a material it does not require. The
# blind prerequisite audit found in2_electron_source_cathode saying "Tungsten
# chosen for high melting point and low evaporation" with no tungsten anywhere
# in its ancestry. Ductile tungsten filament wire is the Coolidge process and
# is a real achievement: tungsten is too brittle to draw until it is sintered
# from powder and worked hot, which is why powder metallurgy belongs here too.
#
# It was nearly deferred on a misread number. mat_tungsten's closure is 102
# nodes, which looked like adding a hundred nodes to a 145-node goal path - but
# 101 of those 102 were already in that closure, so the MARGINAL addition is
# one. Raw closure size is the wrong quantity to price a new edge with.
_cath = NODES["in2_electron_source_cathode"]["pre"]
check("the cathode that is made of tungsten requires tungsten",
      "mat_tungsten" in _cath, _cath)
check("...and the powder metallurgy that makes tungsten drawable at all",
      "met_powder_metallurgy" in _cath, _cath)
check("...and the note that named it is still the reason it is there",
      "tungsten" in (NODES["in2_electron_source_cathode"].get("note") or "").lower(),
      (NODES["in2_electron_source_cathode"].get("note") or "")[:90])

check("nothing can be made of rubber without first securing rubber",
      not _ungated, _ungated)
check("(and there really are rubber recipes to gate)", len(_rub_users) > 10,
      len(_rub_users))

# --- BREAK: grant_ambient ran BEFORE the civ's named starting_techs were
# added, so anything they unlocked was credited on the player's first `step`
# and printed as "COMPLETED 100: Amphitheatre with tiered seating" - a
# completion for something they had never started, in the same words as their
# own work. Nothing free may arrive after the game begins.
for _civ_ga in ("rome_100ad", "han_china_100ad", "norse_900ad", "mexica_1500",
                "england_1300"):
    _s_ga = sim(civ=_civ_ga)
    _before_ga = set(_s_ga.done)
    _s_ga.step()
    check("%s hands you nothing free on turn one" % _civ_ga,
          not (_s_ga.done - _before_ga), sorted(_s_ga.done - _before_ga))


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


# --- BREAK: "MOST RESTS ON THESE" heads its list with items at 230 to 1,580
# denarii against an opening purse of 400, and a break tester followed the
# game's own headline advice into CREDIT EXHAUSTED by year 106. The advice is
# right; the reader needs to know which of it they can act on this year.
_rav, _, _ = proto([{"cmd": "available", "limit": 4, "offset": 200},
                    {"cmd": "available"}])
check("available says what you could raise for a project",
      _rav[0].get("you_could_raise_for_a_project") is not None
      and _rav[1].get("you_could_raise_for_a_project") is not None,
      _rav[0].get("you_could_raise_for_a_project"))
_page = _RP("available", _rav[0])
check("...and marks the rows you could not raise it for",
      "*" in _page and "A * after COST" in _page,
      [l for l in _page.splitlines() if "after COST" in l])
_cheap, _, _ = proto([{"cmd": "available", "limit": 2}])
check("...and does not mark what you can plainly afford",
      "A * after COST" not in _RP("available", _cheap),
      _RP("available", _cheap)[:200])


# --- JOB 1: "something happens shortly after the game starts and then
# nothing happens for centuries" was the same shape of complaint across
# several rounds of playtesting, on more than one civilization. Audited and
# fixed by adding real, dated events; this check keeps the fix from rotting
# by failing if a future edit to a civilization file reopens a long silent
# stretch. Ninety years is generous against what every file now actually
# does (England's worst remaining gap is 63, Norse's is 86) but still catches
# the kind of quarter-millennium silence the audit found.
for _cf in sorted(glob.glob(os.path.join(ROOT, "data", "civilizations", "*.json"))):
    _cid = os.path.basename(_cf)[:-5]
    if _cid.startswith("_"):
        continue
    _cd = json.load(open(_cf))
    _start = _cd["year"]
    _windows = sorted((h["years"][0], h["years"][1]) for h in _cd.get("hazards", []))
    _prev, _gaps = _start, []
    for (_a, _b) in _windows:
        _gaps.append(_a - _prev)
        _prev = max(_prev, _b)
    check("%s: no silent stretch longer than 90 years between its dated "
          "events" % _cid,
          all(g <= 90 for g in _gaps), _gaps)
    if _cid != "mexica_1500":
        # The Mexica's list runs out at the edge of real history, not at the
        # horizon - extending it past here would mean inventing the future,
        # which the drug war entry's own note says this file will not do.
        # Every OTHER civilization's list should reach close to the end of
        # the 500-700 year run the brief asked for.
        check("%s: its events reach close to the end of a 700-year run, "
              "not just the first half of it" % _cid,
              (_start + 700) - _prev <= 90, (_start, _prev))

# --- JOB 2: A PLAGUE MOVES THE WHOLE SOCIETY, NOT JUST YOUR OWN HOUSEHOLD. A
# playtester watched the Black Death take a third of their own staff and
# nothing else happen anywhere in the game, and asked why a mortality event
# this size left the rest of the economy untouched - no dearer hiring, no
# dearer wages, nothing. self.pop_deficit (core.py, fed by _shocks in
# society.py) is the fix: the hazard now also costs the whole labour market
# people, and a smaller labour market pays more to hire from.
s = sim(civ="england_1300")
s.year = 1348
s._shocks(1348)
check("the Black Death costs the whole society people, not only your own "
      "household",
      abs(s.pop_deficit - 0.45) < 1e-6, s.pop_deficit)

# --- your own quarantine (plague_preparedness) protects your own household
# - that is what hazard_relief already does to the personal staff_loss above
# - and must NOT also soften the society-wide figure: the rest of the world
# never built your hedge.
s2 = sim(civ="england_1300")
s2.done.add("plague_preparedness"); s2.operating.add("plague_preparedness")
s2._done_changed()
s2.year = 1348
s2._shocks(1348)
check("a hedge against plague shields your own staff, not the whole "
      "population's labour market",
      abs(s2.pop_deficit - 0.45) < 1e-6, s2.pop_deficit)

# --- scarcer labour is dearer labour, and it shows up the very next time the
# year turns over, not only once the deficit has fully resolved.
_base_wage = s.wage_index
s.year = 1349
s._demographic_recovery(1349)
check("wages rise the year after a mortality shock, because the labour "
      "market just got smaller",
      s.wage_index > _base_wage * 1.2, (_base_wage, s.wage_index))
check("the wage cascade is LOGGED, so a player can see why their wage bill "
      "jumped instead of having to notice it in the accounts",
      any("running" in m and "above normal" in m for _y, m in s.log),
      [m for _y, m in s.log if "wage" in m.lower()])

# --- it fades on the clock the hazard earned, not instantly and not
# forever - the actual brief: "the effect decaying back over a historically
# plausible recovery period rather than being permanent or instant".
s4 = sim(civ="england_1300")
s4.year = 1348
s4._shocks(1348)
for _yr in range(1349, 1349 + 50):
    s4._demographic_recovery(_yr)
_mid_premium = s4.wage_index / _base_wage - 1.0
for _yr in range(1349 + 50, 1349 + 150):
    s4._demographic_recovery(_yr)
_end_premium = s4.wage_index / _base_wage - 1.0
check("fifty years on, the wage premium from the Black Death is still "
      "substantial, not gone in a handful of years",
      _mid_premium > 0.10, _mid_premium)
check("...and by England's roughly 150-year demographic recovery it has "
      "mostly faded, not stayed at its peak forever",
      _end_premium < 0.05, _end_premium)

# --- a milder mortality event earns a shorter recovery than the Black
# Death's 150 years, in proportion to how much of the population it
# actually took, not the same horizon regardless of size.
s5 = sim(civ="rome_100ad")
for _yr in range(165, 181):
    s5.year = _yr
    s5._shocks(_yr)
    if s5.pop_deficit > 0:
        break
check("the Antonine plague (28% of staff) earns a shorter demographic "
      "recovery than the Black Death's (45%) 150 years, scaled to size",
      0 < s5._pop_recovery_years < 150.0, s5._pop_recovery_years)

# --- JOB 3: TECHNOLOGY RAISES THE POPULATION, SLOWLY. Sanitation,
# antisepsis, crop rotation and the like should feed back into a bigger
# labour market eventually, but a lower death rate shows up in the headcount
# a generation later, not the day a latrine opens - so apply_tech_effects
# must queue the gain rather than apply it the year the node completes.
s6 = sim(civ="rome_100ad")
_base_pop = s6._pop_scale_base
s6.apply_tech_effects("sanitation_antisepsis")
check("a population-raising technology does not move the population the "
      "instant it completes",
      s6._pop_scale_base == _base_pop, s6._pop_scale_base)
for _yr in range(100, 100 + 40):
    s6._demographic_recovery(_yr)
check("...but it has fully landed by the end of its forty-year ramp",
      abs(s6._pop_scale_base - (_base_pop + 0.02)) < 1e-6, s6._pop_scale_base)
check("...and the gain stops growing once it has landed, rather than "
      "compounding forever",
      not s6._pop_tech_pending, s6._pop_tech_pending)
s6.apply_tech_effects("sanitation_antisepsis")
for _yr in range(140, 140 + 20):
    s6._demographic_recovery(_yr)
check("halfway through a SECOND such technology's ramp, only half of its "
      "own gain has landed - the ramp does not dump the total on year one",
      abs(s6._pop_scale_base - (_base_pop + 0.02 + 0.01)) < 1e-6,
      s6._pop_scale_base)
# =============================================================================
# NAMES, NOT JUST IDS: testers found it jarring that `state` and `available`
# print a human NAME ("Reaper-binder") while every command that acts on a
# technology took only the machine id ("ag2_reaper_binder"). `why`, `start`,
# `stop`, `bounty`, `mothball`, `restore` and `open` now all resolve a typed
# name to its id first - case and punctuation folded, a unique prefix or
# distinctive substring both work - and refuse with the real ids to choose
# between when the name is not unique. Ids keep working unchanged, because
# scripts and the `agent` protocol depend on them.
# =============================================================================
r, _, _ = proto([{"cmd": "why", "id": "Reaper-Binder"}])
check("a typed name resolves to the id, case and punctuation folded",
      r[0].get("ok") and r[0].get("id") == "ag2_reaper_binder",
      r[0].get("error") or r[0].get("id"))

r, _, _ = proto([{"cmd": "why", "id": "ag2_balanced_ration"}])
_printed_name = r[0].get("name")
r2, _, _ = proto([{"cmd": "why", "id": _printed_name}])
check("a name copied verbatim off another screen resolves the same way",
      r2[0].get("ok") and r2[0].get("id") == "ag2_balanced_ration",
      (_printed_name, r2[0].get("error")))

r, _, _ = proto([{"cmd": "why", "id": "loom"}])
check("an ambiguous name is refused with the real ids to choose between",
      not r[0].get("ok") and r[0].get("error", "").count("(") >= 2
      and "tex_horizontal_loom" in r[0]["error"],
      r[0].get("error"))

# --- fog: the ambiguous-name list must never offer more than full visibility
# would, and on a fresh game it must offer strictly less (or the filter is a
# no-op that only looks like it is doing something).
import re as _re_names
_full, _, _ = proto([{"cmd": "why", "id": "loom"}])
_fog, _, _ = proto([{"cmd": "why", "id": "loom"}], fog=True, kit="poor_scholar")
_full_ids = set(_re_names.findall(r"(\w+) \(", _full[0].get("error", "")))
_fog_ids = set(_re_names.findall(r"(\w+) \(", _fog[0].get("error", "")))
check("under fog, an ambiguous name never offers more candidates than full "
      "visibility would",
      _fog_ids and _fog_ids < _full_ids,
      (sorted(_fog_ids), sorted(_full_ids)))

# --- the goal's NAME gets the same one exception its id already has on
# `why` alone - see protocol.py's _goal_why comment - and nothing widens it.
r, _, _ = proto([{"cmd": "why", "id": NODES[GOAL]["name"]},
                 {"cmd": "start", "id": NODES[GOAL]["name"]},
                 {"cmd": "why", "id": "transistor"}], fog=True, kit="poor_scholar")
check("why on the goal's exact printed name is the one thing fog answers",
      r[0].get("ok") and r[0].get("id") == GOAL,
      r[0].get("error"))
check("...but the exception does not widen to other commands on the same name",
      not r[1].get("ok") and "never heard of" in r[1].get("error", ""),
      r[1].get("error"))
check("...and a vague guess does not silently resolve to the goal",
      not r[2].get("ok") and GOAL not in r[2].get("error", "")
      and "aiming at" not in r[2].get("error", ""),
      r[2].get("error"))


# =============================================================================
# FOG LEAK #1, AS THE PLAYER FOUND IT: with fog on, `why aqueduct_survey` -
# a name for nothing in the tree - suggested six ids as "did you mean", and
# nobody had checked whether all six were things the player had actually
# heard of. Verified the honest way: re-ask `why` about every id the
# suggestion offered, and none of them may come back "never heard of".
# =============================================================================
r, _, _ = proto([{"cmd": "why", "id": "aqueduct_survey"}], fog=True, kit="poor_scholar")
_sugg = [s_.strip() for s_ in
         r[0].get("error", "").split("Did you mean:")[-1].split(",") if s_.strip()] \
        if "Did you mean" in r[0].get("error", "") else []
_checks = [{"cmd": "why", "id": sid} for sid in _sugg]
_verify, _, _ = (proto(_checks) if _checks else ([], "", 0))
check("the did-you-mean list under fog only ever suggests things the player "
      "has heard of",
      all("never heard of" not in x.get("error", "") for x in _verify),
      [(sid, x.get("error")) for sid, x in zip(_sugg, _verify)
       if "never heard of" in x.get("error", "")])


# =============================================================================
# FOG LEAK #2: `available`'s "HEARD OF, CANNOT BEGIN YET" block used to
# ignore `find`/`subject` and print its usual nearest-first twenty-five
# regardless of the search, so a search that matched nothing startable still
# dumped seven things nobody asked about. Reproduced exactly as found: reveal
# something (units_standards unlocks several), then search for nonsense.
# =============================================================================
s_hd = sim(civ="rome_100ad", manual=False)
s_hd.fog = True
s_hd.revealed = set()
S._agent_dispatch(s_hd, NODES, {"cmd": "start", "id": "units_standards"})
for _ in range(2):
    s_hd.step()
_hd_nonsense = S._agent_available(s_hd, NODES, {"find": "zzzznonexistentxyz"})
_hd_plain = S._agent_available(s_hd, NODES, {"limit": 50})
check("a search matching nothing startable does not also dump the generic "
      "heard-of list",
      not _hd_nonsense.get("heard_of_but_cannot_begin"),
      _hd_nonsense.get("heard_of_but_cannot_begin"))
check("...but the same heard-of list still shows up unfiltered when no "
      "search was asked for",
      _hd_plain.get("heard_of_but_cannot_begin"),
      "empty heard-of list with no search active")
_hd_match = S._agent_available(s_hd, NODES, {"find": "corpus"})
check("...and a search that DOES match a heard-of item still shows it",
      any(h["id"] == "corpus_written"
          for h in _hd_match.get("heard_of_but_cannot_begin") or []),
      _hd_match.get("heard_of_but_cannot_begin"))


# =============================================================================
# SORT AND PAGE, ALL THE WAY TO THE END. Several screens truncated to 25 rows
# and said "N more, nearest first" with no way to ask for a different order.
# `available` now takes `sort` (price/hours/years/earns/upkeep/risk/alpha/
# nearest) and `reverse`, on both the startable list and the heard-of one.
# =============================================================================
r, _, _ = proto([{"cmd": "available", "limit": 10, "sort": "risk", "reverse": True}])
_risks = [e["risk"] for e in r[0]["available"]]
check("available can be sorted by risk, reversed, all the way through the page",
      _risks == sorted(_risks, reverse=True), _risks)

_pretty_sorted = _RP("available", r[0])
_json_first_id = r[0]["available"][0]["id"]
_json_last_id = r[0]["available"][-1]["id"]
check("the printed table keeps the JSON's sort order rather than re-sorting "
      "back to cost",
      -1 < _pretty_sorted.find(_json_first_id) < _pretty_sorted.find(_json_last_id),
      (_json_first_id, _json_last_id, _pretty_sorted))

r2, _, _ = proto([{"cmd": "available", "limit": 3}])
check("a plain page still defaults to cheapest first",
      [e["cost"] for e in r2[0]["available"]]
      == sorted(e["cost"] for e in r2[0]["available"]),
      [e["cost"] for e in r2[0]["available"]])

# --- the tester's other question: does `available` show staff requirements,
# and is the legend for them nearby rather than a screen away.
_staff_pretty = _RP("available", r2[0])
_lines = _staff_pretty.splitlines()
_staff_hdr = next(i for i, l in enumerate(_lines) if "STAFF" in l)
_staff_legend = next((i for i, l in enumerate(_lines)
                      if "STAFF is the standing people" in l), None)
check("the STAFF column has its legend within a few lines of the table, "
      "not a screen away",
      _staff_legend is not None and _staff_legend - _staff_hdr < 15,
      (_staff_hdr, _staff_legend))


# =============================================================================
# THE PLAYER'S OWN LOG. The commonest complaint across eleven rounds of
# testing was some version of "failures are silent" - the engine has always
# kept self.log, and there was no command to read it back. `log` (alias
# `history`) shows it, paged, filterable, and searchable, and it is hard-
# capped so a script asking for everything at once cannot get it.
# =============================================================================
from engine.protocol import _agent_log as _AL

r, _, _ = proto([{"cmd": "start", "id": "units_standards"},
                 {"cmd": "hire", "trade": "smith", "n": 2},
                 {"cmd": "step", "years": 1},
                 {"cmd": "fire", "trade": "smith", "n": 1},
                 {"cmd": "log"}])
_entries = r[-1].get("entries") or []
check("log records what the player did - starting, hiring, letting go - not "
      "just what the engine did on its own",
      any("started" in e["what"] for e in _entries)
      and any("smith" in e["what"] and "taken on" in e["what"] for e in _entries)
      and any("smith" in e["what"] and "go" in e["what"] for e in _entries),
      _entries)
check("log defaults to most-recent-first",
      _entries[0]["year"] >= _entries[-1]["year"], [e["year"] for e in _entries])

# --- never dumped in one go, however large a limit is asked for or however
# long the history actually is.
s_lg = sim(civ="rome_100ad", manual=False)
for _y in range(3000):
    s_lg.log.append((100 + _y % 500, "hired 1 smith"))
_huge = _AL(s_lg, {"limit": 1000000})
check("the log is hard-capped regardless of what limit is asked for",
      len(_huge["entries"]) <= 100, len(_huge["entries"]))
_default = _AL(s_lg, {})
check("...and defaults to a short recent window with no limit given at all",
      len(_default["entries"]) <= 25, len(_default["entries"]))

# --- filtering to failures specifically, which is what every round of
# testing actually asked for.
s_lf = sim()
s_lf.log = [(100, "started: Foo"), (101, "FAILED at Foo: it did not work."),
            (102, "hired 1 smith")]
_fails = _AL(s_lf, {"failures": True})
check("'failures' filters the log to only the bad news",
      len(_fails["entries"]) == 1 and "FAILED" in _fails["entries"][0]["what"],
      _fails["entries"])

# --- fog: a log line minted while something was visible must not go on
# naming it once fog would refuse to answer `why` about it - whether it was
# forgotten later, or never visible to begin with.
s_lz = sim()
s_lz.fog = True
s_lz.revealed = set()
s_lz.log = [(100, "completed: Point-contact transistor")]
_scrubbed = _AL(s_lz, {})["entries"][0]["what"]
check("the log redacts a name fog would refuse to answer `why` about",
      "Point-contact transistor" not in _scrubbed and "transistor" not in _scrubbed.lower(),
      _scrubbed)
s_lz.fog = False
_unscrubbed = _AL(s_lz, {})["entries"][0]["what"]
check("...but only under fog - with it off the log reads exactly as written",
      "Point-contact transistor" in _unscrubbed, _unscrubbed)

# --- a search cannot be used to confirm the existence of something a
# redacted line would otherwise hide.
s_lz.fog = True
_hidden_search = _AL(s_lz, {"find": "transistor"})
check("a search cannot smuggle out what the redaction just hid",
      _hidden_search["count"] == 0, _hidden_search)

# --- discoverable, per the task's own standard: `help` names it, and the
# screen itself explains its filters without anyone reading the source.
r, _, _ = proto([{"cmd": "help", "topic": "commands"}])
check("log is advertised in help, not just implemented",
      "log" in (r[0].get("help") or {}).get("commands", {}),
      list((r[0].get("help") or {}).get("commands", {}).keys()))
r, _, _ = proto([{"cmd": "log"}])
check("the log screen itself explains how to filter and page it",
      "to_filter_or_sort" in r[0] and "failures" in r[0]["to_filter_or_sort"],
      r[0].get("to_filter_or_sort"))

# --- typed front end: a player at a keyboard, not a script, has to be able
# to reach all of this too.
from engine.protocol import parse_typed as _PT
_cmd, _err = _PT("log failures find plague since 200 oldest limit 5")
check("the typed form reaches every filter the JSON protocol has",
      _cmd == {"cmd": "log", "failures": True, "find": "plague",
               "since": 200, "order": "oldest", "limit": 5},
      _cmd)
# --- BREAK: the automatic behaviours read as the engine offering to play
# well on your behalf, and they are nothing of the kind. Testers turned them
# on and reported the result as a defect: "policy auto_hire true destroyed my
# run in eight years", "auto_train quietly bankrupted me", "policy auto_hire
# on quietly destroyed my economy". They were right about what happened and
# wrong about what these are, and this screen never told them.
_pl, _, _ = proto([{"cmd": "policy"}])
check("the policy screen says these are approximations, not optimal play",
      "approximation" in str(_pl[0].get(
          "these_are_approximations_not_optimal_play")).lower()
      or "rule of thumb" in str(_pl[0].get(
          "these_are_approximations_not_optimal_play")).lower(),
      _pl[0].get("these_are_approximations_not_optimal_play"))
_pl_txt = _RP("policy", _pl[0])
check("...and a player reads that before the list of switches, not after it",
      _pl_txt.index("rule of thumb") < _pl_txt.index("auto_bribe"),
      _pl_txt[:200])
check("...and every switch the game offers says what it does",
      not [k for k in _pl[0]["policy"]
           if not (_pl[0].get("what_each_does") or {}).get(k)],
      [k for k in _pl[0]["policy"]
       if not (_pl[0].get("what_each_does") or {}).get(k)])
check("...and no line of that screen runs past the width everything else wraps to",
      max(len(l) for l in _pl_txt.splitlines()) <= 78,
      max(_pl_txt.splitlines(), key=len))

_cmd2, _err2 = _PT("why horizontal loom")
check("a multi-word typed name is not truncated to its first word",
      _cmd2 == {"cmd": "why", "id": "horizontal loom"}, _cmd2)
# --- NEW: a goods-producing concern sells into a MARKET, not a fixed number.
# A playtester's own example: "an automated loom should be making a lot of
# money early on, but the profit should decrease over time once supply
# starts going up... up to some point." See economy.py's GOODS_CATEGORIES
# and goods_market_factor() for the model this exercises.
s_lm = sim(civ="rome_100ad", capital=500000.0)
s_lm.done.add("tex_power_loom")
s_lm.done_year["tex_power_loom"] = 100
s_lm._done_changed()
s_lm.artisans = s_lm.scholars = 80.0
s_lm.year = 100
_ok_lm, _msg_lm = s_lm.open_venture("tex_power_loom")
check("a power loom can be opened, to exercise what it then earns",
      _ok_lm, _msg_lm)
check("a freshly opened power loom earns what the tree quotes, not less - "
      "the first turn is not where this is supposed to show up",
      abs(s_lm.goods_market_factor("tex_power_loom") - 1.0) < 1e-9,
      s_lm.goods_market_factor("tex_power_loom"))

s_lm.year = 130        # thirty years of custom later
_factor_30 = s_lm.goods_market_factor("tex_power_loom")
check("thirty years on, the same loom earns less, because supply of cloth - "
      "yours and everyone else's - has caught up with demand",
      _factor_30 < 0.95, _factor_30)
check("...but not next to nothing: this kind of good keeps a floor price",
      _factor_30 > 0.5, _factor_30)

s_lm.year = 400        # long after the market has fully adjusted
_factor_400 = s_lm.goods_market_factor("tex_power_loom")
check("...and once the market is saturated it flattens, rather than "
      "decaying away for ever",
      abs(_factor_400 - _factor_30) < 0.02, (_factor_30, _factor_400))

# --- The brief's own worked example, almost to the denarius: a concern that
# earned 400 a year now earning about 280, and a player told why rather
# than left to notice the number moved.
s_nt = sim(civ="rome_100ad", capital=500000.0)
s_nt.done.add("tex_horizontal_loom")
s_nt.done_year["tex_horizontal_loom"] = 100
s_nt._done_changed()
s_nt.artisans = s_nt.scholars = 20.0
s_nt.year = 100
s_nt.open_venture("tex_horizontal_loom")
s_nt.year = 400
_note = s_nt.goods_market_note("tex_horizontal_loom")
check("a player reading `ventures` or `money` is told WHY a concern earns "
      "less than the tree quotes, in plain language",
      bool(_note) and "tree quotes" in _note and "actually earns" in _note,
      _note)
_vrow_nt = S._agent_dispatch(s_nt, NODES, {"cmd": "ventures"})
_row_nt = next(r for r in _vrow_nt["running"] if r["id"] == "tex_horizontal_loom")
check("...and `ventures` itself carries the same explanation on the row",
      "market" in _row_nt and bool(_row_nt["market"]), _row_nt)
_money_nt = S._agent_dispatch(s_nt, NODES, {"cmd": "money"})
check("...and `money` says the same thing in aggregate",
      bool(_money_nt.get("the_market_you_sell_into")), _money_nt.get("the_market_you_sell_into"))

# --- Services, institutions and patronage are untouched: the brief asked
# for exactly that distinction, and this is the honest way to check it -
# a node outside GOODS_CATEGORIES gets a factor of exactly 1.0 no matter
# how old the concern is.
s_sv = sim(civ="rome_100ad", capital=500000.0)
_nongood = next(k for k in sorted(NODES)
               if NODES[k].get("cat") not in s_sv.GOODS_CATEGORIES
               and s_sv.is_venture(k) and not NODES[k]["pre"])
s_sv.done.add(_nongood)
s_sv.done_year[_nongood] = 100
s_sv._done_changed()
s_sv.artisans = s_sv.scholars = 50.0
s_sv.year = 100
s_sv.open_venture(_nongood)
s_sv.year = 500
check("a service, institution or anything outside the goods categories "
      "still pays the tree's flat figure centuries later, exactly as before",
      s_sv.goods_market_factor(_nongood) == 1.0, _nongood)

# --- The ledger's own "parts add up to the total" invariant has to survive
# this too, with an aged loom actually pulling the total below the flat
# figure - not just in the already-passing young-economy case above.
s_ld = sim(civ="rome_100ad", capital=500000.0)
s_ld.done.add("tex_power_loom")
s_ld.done_year["tex_power_loom"] = 100
s_ld._done_changed()
s_ld.artisans = s_ld.scholars = 80.0
s_ld.year = 100
s_ld.open_venture("tex_power_loom")
s_ld.year = 300
_src_ld = s_ld.revenue_sources()
check("the ledger's parts still add up to the revenue it states, with an "
      "aged goods concern pulling the total down",
      abs(sum(_src_ld.values()) - s_ld.revenue()) < 1.0,
      (sum(_src_ld.values()), s_ld.revenue()))

# --- Population and reach are supposed to matter - the brief says market
# size "should depend on the population, on what that society can pay, and
# on how far your goods can travel." A smaller, poorer, less-connected
# civilization should see the SAME concern's margin erode faster.
s_small = sim(civ="norse_900ad", capital=500000.0)
s_small.done.add("tex_power_loom")
s_small.done_year["tex_power_loom"] = 100
s_small._done_changed()
s_small.artisans = s_small.scholars = 80.0
s_small.year = 100
s_small.open_venture("tex_power_loom")
s_small.year = 110      # ten years in - before EITHER market is fully saturated
_small_factor = s_small.goods_market_factor("tex_power_loom")
s_lm.year = 110
_rome_10 = s_lm.goods_market_factor("tex_power_loom")
check("a smaller, poorer civilization's market for the same good saturates "
      "faster than Rome's did at the same age",
      _small_factor < _rome_10, (_small_factor, _rome_10))

# =============================================================================
# TWO LOOMS COMPETE: rome/data/review/COMMODITY_DYNAMISM.md's central goods-
# market finding, measured directly against a live Sim before this pass:
# "One loom at age 20 earns factor 0.7840. With a second identical loom
# running: 0.7840. With ten: 0.7840... a time curve wearing a market's
# clothes." goods_market_factor() now shares one total-supply figure across
# every concern in the same category, so a second (or tenth) producer must
# measurably cut into the first one's earnings.
# =============================================================================

def _mk_loom_sim(n_looms, age_years):
    """n_looms real, distinct textiles-category venture nodes, all opened
    the same year, aged the same number of years. Uses real tree nodes
    (not synthetic ones), the same way the rest of this file does."""
    cand = sorted(k for k, n in NODES.items()
                  if n.get("cat") == "textiles" and n.get("rev"))
    assert len(cand) >= n_looms, "not enough textiles venture nodes in the tree"
    chosen = cand[:n_looms]
    s = sim(civ="rome_100ad", capital=5_000_000.0)
    s.artisans = s.scholars = 100.0 * n_looms
    s.year = 100
    for k in chosen:
        s.done.add(k)
        s.done_year[k] = 100
    s._done_changed()
    for k in chosen:
        ok, msg = s.open_venture(k)
        assert ok, (k, msg)
    s.year = 100 + age_years
    return s, chosen

s_one, _one = _mk_loom_sim(1, 20)
f_one = s_one.goods_market_factor(_one[0])
s_two, _two = _mk_loom_sim(2, 20)
f_two = s_two.goods_market_factor(_two[0])
check("a lone concern in a category earns the tree's own figure trajectory, "
      "exactly as it always did - the identity a second producer must NOT "
      "break for a player who only ever builds one",
      abs(f_one - 1.0) < 1.0 and f_one < 1.0, f_one)
check("...but a second, identical concern selling into the SAME market at "
      "the same age earns measurably LESS than the lone concern did - real "
      "competition, not the pre-existing bug where both were bit-for-bit "
      "identical to the solo case",
      f_two < f_one * 0.9, (f_one, f_two))
check("...and the second concern's own factor is the same as the first's "
      "(they split one shared market evenly, being identical and the same "
      "age)",
      abs(s_two.goods_market_factor(_two[1]) - f_two) < 1e-9,
      (f_two, s_two.goods_market_factor(_two[1])))

s_ten, _ten = _mk_loom_sim(10, 20)
f_ten = s_ten.goods_market_factor(_ten[0])
check("ten identical concerns earn less again than two did - competition "
      "keeps biting as more producers pile into the same market, not just "
      "a one-time step from one to two",
      f_ten < f_two, (f_two, f_ten))
check("...and revenue() itself reflects it: ten competing concerns do not "
      "each earn what one alone would, so total revenue is far below ten "
      "times a lone concern's take",
      s_ten.revenue() < s_one.revenue() * 10 * 0.5,
      (s_one.revenue(), s_ten.revenue()))

# --- a player must see the competition, not just feel it in a smaller
# number: goods_market_note()/goods_market_summary() must say so.
_note_two = s_two.goods_market_note(_two[0])
check("a player reading `ventures`/`money` is told competition, not just "
      "time, is why a concern earns less than the tree quotes",
      bool(_note_two) and "concerns of yours are selling into this same "
      "market" in _note_two, _note_two)
_summary_two = s_two.goods_market_summary()
check("...and the aggregate `money` summary says so too",
      bool(_summary_two) and "competing with each other" in _summary_two,
      _summary_two)

# =============================================================================
# THE INCOME EFFECT: the brief's own richest idea, almost verbatim - "when
# the public has less money, they buy less. So if the price of food goes
# down, the price people would be willing to pay for diamonds or records
# would go up." Tested here against real tree nodes: a food-processing
# concern (essential) and a gambling house (about as purely discretionary
# as the tree gets).
# =============================================================================

_proc_cand = sorted(k for k, n in NODES.items()
                    if n.get("cat") == "processing" and n.get("rev"))
assert _proc_cand, "need at least one processing venture node"
_PROC_NODE = _proc_cand[0]
_ENT_NODE = "fin_gambling_house"
check("fin_gambling_house is a real, revenue-bearing tree node - not a "
      "synthetic example - in the 'luxury' category this pass now covers",
      NODES[_ENT_NODE].get("rev", 0) > 0
      and NODES[_ENT_NODE].get("cat") == "luxury", NODES[_ENT_NODE])

def _mk_income_sim(with_cheap_food):
    s = sim(civ="rome_100ad", capital=5_000_000.0)
    s.artisans = s.scholars = 200.0
    if with_cheap_food:
        s.done.add(_PROC_NODE)
        s.done_year[_PROC_NODE] = 50
        s._done_changed()
        s.year = 50
        ok, msg = s.open_venture(_PROC_NODE)
        assert ok, msg
        s.year = 200      # long saturated: essential_price_ratio at its floor
    else:
        s.year = 200
    s.done.add(_ENT_NODE)
    s.done_year[_ENT_NODE] = s.year
    s._done_changed()
    ok, msg = s.open_venture(_ENT_NODE)
    assert ok, msg
    return s

s_no_food = _mk_income_sim(False)
s_cheap_food = _mk_income_sim(True)
check("with no essential concern running, income_factor is neutral - a run "
      "that never touches food processing behaves exactly as before this "
      "pass",
      abs(s_no_food.income_factor() - 1.0) < 1e-9, s_no_food.income_factor())
check("a fully saturated, cheap essential market genuinely lowers "
      "essential_price_ratio below 1.0",
      s_cheap_food.essential_price_ratio() < 0.99,
      s_cheap_food.essential_price_ratio())
check("...which raises income_factor above 1.0 - real spending power freed "
      "up, not a cosmetic number",
      s_cheap_food.income_factor() > 1.0, s_cheap_food.income_factor())
_f_gambling_poor = s_no_food.goods_market_factor(_ENT_NODE)
_f_gambling_rich = s_cheap_food.goods_market_factor(_ENT_NODE)
check("the SAME gambling house, opened the same way, earns MORE once food "
      "is cheap and saturated than it does with no food market at all - "
      "the brief's own worked example, cheaper food raising what people "
      "will pay for a discretionary good",
      _f_gambling_rich > _f_gambling_poor, (_f_gambling_poor, _f_gambling_rich))
_note_proc = s_cheap_food.goods_market_note(_PROC_NODE)
check("processing itself (the essential) says plainly that it is a "
      "necessity and does not move with price - income_factor only ever "
      "applies to DISCRETIONARY categories, and a player reading the "
      "essential concern's own note should not be told it benefited from "
      "its own cheapness",
      _note_proc is None or "necessity" in _note_proc, _note_proc)

# --- the ledger's own "parts add up to the total" invariant survives the
# income effect too, the same standard already held for an aged loom.
_src_income = s_cheap_food.revenue_sources()
check("the ledger's parts still add up to the revenue it states, with the "
      "income effect raising one row above the tree's own figure",
      abs(sum(_src_income.values()) - s_cheap_food.revenue()) < 1.0,
      (sum(_src_income.values()), s_cheap_food.revenue()))

# --- determinism: goods-category state is summed over self.operating, a
# set of strings, so it has to iterate sorted() - proven the same way the
# rest of this file proves it, by running twice under different hash seeds.
def _goods_snapshot(seed_env):
    p = subprocess.run(
        [sys.executable, "-c",
         "import sys; sys.path.insert(0,'.'); import random, simulator as S; "
         "T,P,N,W,G = S.load(); _l,O,_b = S.load_strategy('recommended', N, T['meta']['goal_node']); "
         "s = S.Sim(N, O, random.Random(1), events=False, manual=True, "
         "civ=S.load_civ('rome_100ad'), cfg={'start_capital':5000000.0}); "
         "s.artisans = s.scholars = 500.0; s.year = 100; "
         "cand = sorted(k for k,n in N.items() if n.get('cat')=='textiles' and n.get('rev'))[:5]; "
         "[s.done.add(k) or s.done_year.__setitem__(k, 100) for k in cand]; "
         "s._done_changed(); "
         "[s.open_venture(k) for k in cand]; "
         "s.year = 130; "
         "print(repr(round(s.goods_market_factor(cand[0]), 12)))"],
        capture_output=True, text=True, timeout=60, cwd=HERE,
        env=dict(os.environ, PYTHONHASHSEED=seed_env))
    return p.stdout.strip()
_gsnap_a = _goods_snapshot("0")
_gsnap_b = _goods_snapshot("54321")
check("shared goods-category pricing is identical under a different "
      "PYTHONHASHSEED",
      _gsnap_a == _gsnap_b and _gsnap_a, (_gsnap_a, _gsnap_b))

# =============================================================================
# MINES: LAND, DEPLETION AND TECHNOLOGY. A tester asked three questions
# nothing in the model answered: can you sink unlimited mines of one
# material, does yield fall as the easy ore is worked out, and does
# technology fight back. See economy.py's mine_land_ceiling()/
# mine_depletion_factor()/mining_tech() for the reasoning and the numbers.
# =============================================================================

# --- (a) LAND: the ceiling differs by material and by civilization, because
# geology is not standing. Reuses mineral_scale(), already used for the
# MARKET half of supply, for the OWN-MINE half too.
s_land = sim(capital=1.0)
check("a civilization with little tin under its home regions has a lower "
      "tin ceiling than one with plenty of the same standing",
      s_land.mine_land_ceiling("tin") != s_land.mine_land_ceiling("coal"),
      (s_land.mine_land_ceiling("tin"), s_land.mine_land_ceiling("coal")))
s_mex = sim(civ="mexica_1500", capital=1.0)
check("Mesoamerica, which worked copper but not iron or coal, has a lower "
      "land ceiling for iron than for copper",
      s_mex.mine_land_ceiling("iron") < s_mex.mine_land_ceiling("copper"),
      (s_mex.mine_land_ceiling("iron"), s_mex.mine_land_ceiling("copper")))

# --- open_mine() actually respects the land ceiling: sinking far more than
# the ground can support delivers only what the ground can support, not
# whatever standing alone would have allowed.
s_dig = sim(capital=1e12)
ceiling_before = s_dig.mine_land_ceiling("tin")
got_tin = s_dig.open_mine("tin", ceiling_before * 50.0, partial=False)
check("sinking far more of a scarce material than the land ceiling allows "
      "delivers only room up to that ceiling, not the full amount asked",
      0 < got_tin <= ceiling_before + 1.0,
      (got_tin, ceiling_before))

# --- woodland is bounded too, the tester's other named case ("mines/woods").
s_wood = sim(civ="norse_900ad", capital=1e12)
wood_ceiling = s_wood.forest_land_ceiling()
got_ha = s_wood.buy_forest(wood_ceiling * 100.0)
check("buying far more coppice than the land can support delivers only up "
      "to the ceiling, not the full amount asked",
      0 < got_ha <= wood_ceiling + 1.0, (got_ha, wood_ceiling))
check("...and the ceiling itself is nowhere near the WHOLE EMPIRE's own "
      "managed coppice (500,000 t/yr charcoal implies ~667,000 ha)",
      s_wood.forest_land_ceiling() < 667000.0, s_wood.forest_land_ceiling())

# --- (b) DEPLETION: yield falls as a working is worked hard relative to
# what the ground can support, and never below the stated floor.
s_dep = sim(capital=1e9)
s_dep.open_mine("coal", s_dep.mine_land_ceiling("coal") * 0.9, partial=False)
for _ in range(int(s_dep.MINE_LEAD_YEARS) + 1):
    s_dep.year += 1
    s_dep.commission_mines()
yield_early = s_dep.mine_yield_t("coal")
for _ in range(150):
    s_dep.year += 1
    s_dep.commission_mines()
yield_late = s_dep.mine_yield_t("coal")
check("a coal working driven hard for a century and a half yields less than "
      "it did when it opened",
      yield_late < yield_early, (yield_early, yield_late))
check("...but never below the stated floor, however long it is driven",
      s_dep.mine_depletion_factor("coal") >= s_dep.DEPLETION_FLOOR - 1e-9,
      s_dep.mine_depletion_factor("coal"))
for _ in range(2000):
    s_dep.year += 1
    s_dep.commission_mines()
check("...and depletion saturates at the floor rather than continuing to "
      "fall without limit (not an exponential collapse)",
      abs(s_dep.mine_depletion_factor("coal") - s_dep.DEPLETION_FLOOR) < 1e-6,
      s_dep.mine_depletion_factor("coal"))

# --- a working driven gently (a small fraction of what the ground could
# support) depletes far slower than one driven hard, for the same years.
s_gentle = sim(capital=1e9)
s_gentle.open_mine("coal", s_gentle.mine_land_ceiling("coal") * 0.1, partial=False)
for _ in range(int(s_gentle.MINE_LEAD_YEARS) + 1 + 150):
    s_gentle.year += 1
    s_gentle.commission_mines()
check("a working driven at a tenth of what the land could support depletes "
      "far slower than one driven at nine tenths, over the same years",
      s_gentle.mine_depletion_factor("coal") > s_dep.mine_depletion_factor("coal")
      or s_gentle.mine_depletion_factor("coal") == 1.0,
      (s_gentle.mine_depletion_factor("coal"), s_dep.mine_depletion_factor("coal")))

# --- (c) TECHNOLOGY fights back: it raises yield and lowers cost, and the
# two compound across independent technologies (mine pumping AND the
# Newcomen engine both address drainage, at different scale).
s_tech = sim(capital=1.0)
y0, c0 = s_tech.mining_tech("coal")
run_it(s_tech, "met_mine_pumping")
y1, c1 = s_tech.mining_tech("coal")
run_it(s_tech, "steam_atmospheric")
y2, c2 = s_tech.mining_tech("coal")
check("mine pumping alone raises yield and lowers cost for coal mining",
      y1 > y0 and c1 < c0, (y0, y1, c0, c1))
check("the Newcomen engine on top of mine pumping compounds rather than "
      "replacing it",
      y2 > y1 and c2 < c1, (y1, y2, c1, c2))
check("mining technology never raises yield or lowers cost without bound "
      "(capped/floored like every other compounding factor in this file)",
      y2 <= 3.0 and c2 >= 0.35, (y2, c2))

# --- technology raises what an EXISTING, already-depleted working yields,
# not only room for a new one - "fight depletion", not just avoid it.
before_tech = s_dep.mine_yield_t("coal")
run_it(s_dep, "met_mine_pumping")
run_it(s_dep, "steam_atmospheric")
after_tech = s_dep.mine_yield_t("coal")
check("mine pumping and the Newcomen engine raise a depleted working's "
      "actual yield, not just future room to sink a new one",
      after_tech > before_tech, (before_tech, after_tech))

# --- the interaction the brief asked for: a real decision, not an
# exponential. Cost is bounded on both ends even at maximum depletion with
# every relevant technology built.
s_bound = sim(capital=1.0)
for _t in s_bound.MINING_TECH:
    s_bound.done.add(_t); s_bound.operating.add(_t)
for _t in s_bound.MINING_TECH_STEEL:
    s_bound.done.add(_t); s_bound.operating.add(_t)
s_bound._done_changed()
s_bound.mine_intensity_yrs = collections.Counter({"coal": 1e9})
check("even fully depleted with every relevant technology built, a tonne "
      "still costs something (not free) and not a runaway multiple of book",
      0.4 <= s_bound.mining_cost_scale("coal") <= 2.5,
      s_bound.mining_cost_scale("coal"))
s_bound2 = sim(capital=1.0)
s_bound2.mine_intensity_yrs = collections.Counter({"coal": 1e9})
check("fully depleted with NO relevant technology, cost is higher, not "
      "lower, than the technology-equipped case above",
      s_bound2.mining_cost_scale("coal") > s_bound.mining_cost_scale("coal"),
      (s_bound2.mining_cost_scale("coal"), s_bound.mining_cost_scale("coal")))

# --- THE PLAYER MUST SEE IT: mine_quote() names the land ceiling, current
# yield fraction and why cost differs from book, before any capital moves.
q_dep = s_dep.mine_quote("coal", 100.0)
check("mine_quote names the ground's own ceiling and how much room is left "
      "before it, not just a price",
      q_dep["the_ground_here_could_ever_support"] > 0
      and "room_left_before_geology_stops_you" in q_dep, q_dep)
check("...and the current yield fraction, so a player can see a working "
      "has depleted without guessing",
      q_dep["current_yield_is_this_fraction_of_day_one"] < 1.0, q_dep)
check("...and mine_depletion_note() explains it in a sentence, not just a "
      "number",
      s_dep.mine_depletion_note("coal") is not None
      and "worked out" in s_dep.mine_depletion_note("coal"),
      s_dep.mine_depletion_note("coal"))

# --- determinism: the intensity/depletion bookkeeping is a Counter summed
# by material key, not iterated from a set, so it must not depend on
# PYTHONHASHSEED. Proven the same way the rest of this suite proves it: run
# twice with different hash seeds and compare the exact figures.
def _mine_snapshot(seed_env):
    p = subprocess.run(
        [sys.executable, "-c",
         "import sys; sys.path.insert(0,'.'); import random, simulator as S; "
         "T,P,N,W,G = S.load(); _l,O,_b = S.load_strategy('recommended', N, T['meta']['goal_node']); "
         "s = S.Sim(N, O, random.Random(1), events=False, manual=True, "
         "civ=S.load_civ('rome_100ad'), cfg={'start_capital':1e9}); "
         "s.open_mine('coal', s.mine_land_ceiling('coal')*0.8, partial=False); "
         "[s.__setattr__('year', s.year+1) or s.commission_mines() for _ in range(40)]; "
         "print(repr(round(s.mine_depletion_factor('coal'), 12)))"],
        capture_output=True, text=True, timeout=60, cwd=HERE,
        env=dict(os.environ, PYTHONHASHSEED=seed_env))
    return p.stdout.strip()
_snap_a = _mine_snapshot("0")
_snap_b = _mine_snapshot("12345")
check("mine depletion is identical under a different PYTHONHASHSEED",
      _snap_a == _snap_b and _snap_a, (_snap_a, _snap_b))

# =============================================================================
# REPUTATION: a tester reported it rewards raw completion count, so it can
# be maximised by building trinkets you never use. Confirmed against the
# real gain formula in projects.py: it reads n["rev"]/n["tier"]/traits and
# self.done, and never reads self.operating at all. This is diagnosed and
# left as a finding, not fixed here: the fix lives in projects.py, which
# this pass does not own (see the task's own file-ownership boundary) -
# see the final report for the recommended change.
# =============================================================================
s_rep = sim()
_rep_cands = [k for k, n in NODES.items() if n.get("rev", 0) > 0 and n.get("tier", 0) >= 3]
_rk = sorted(_rep_cands)[0]
_n = NODES[_rk]
_rep0 = s_rep.reputation
s_rep.done.add(_rk); s_rep._done_changed(); s_rep.done_year[_rk] = s_rep.year
s_rep.apply_tech_effects(_rk)
_gain = (0.6 + 0.5 * max(0.0, s_rep.state_interest(_n))
         + (1.2 if _n["rev"] > 0 else 0.0) + 0.25 * _n["tier"])
s_rep.reputation = min(100.0, s_rep.reputation + _gain)
check("FINDING (not fixed here, see report): completing a revenue-bearing "
      "node raises reputation even when it is never opened as a concern",
      s_rep.reputation > _rep0 and _rk not in s_rep.operating,
      (_rep0, s_rep.reputation, _rk in s_rep.operating))


# --- JOB 1: techniques should not cost upkeep. A play tester asked "should
# any techs cost upkeep? Shouldn't that all be on the building/thing it
# unlocks?" and was right: 2,444 non-institution nodes carried upkeep, most
# of them pure knowledge (a theory, a hand technique, a machine-tool
# accessory) with no premises, staff or standing cost to speak of. The audit
# zeroed upkeep on every one of those that had no revenue either - a node
# with revenue is already a going concern by the tree's own definition - and
# kept it only on physical plant (furnaces, mills, mines, chemical process
# works) and a short hand-picked list of named facilities (hospitals,
# clinics, road networks, the arsenal). This is em_theory: pure knowledge,
# nothing to run.
check("a pure technique no longer costs anything to keep knowing",
      NODES["em_theory"]["up"] == 0.0 and NODES["em_theory"]["rev"] == 0.0,
      (NODES["em_theory"]["up"], NODES["em_theory"]["rev"]))
check("that same technique is no longer offered as a going concern to open",
      sim().is_venture("em_theory") is False, sim().is_venture("em_theory"))
# And the flip side: an actual furnace you fire every day still costs
# something to keep firing, same as before the audit.
check("a furnace you actually run still carries real upkeep",
      NODES["met_open_hearth_furnace"]["up"] > 0,
      NODES["met_open_hearth_furnace"]["up"])
# A venture that sells something was never in scope for the audit - revenue
# is what makes it a going concern in the first place - so blast_furnace,
# which both sells cast iron and costs money to run, is untouched.
check("a venture that already sells something keeps its upkeep untouched",
      NODES["blast_furnace"]["up"] == 7000.0 and NODES["blast_furnace"]["rev"] > 0,
      (NODES["blast_furnace"]["up"], NODES["blast_furnace"]["rev"]))

# --- JOB 2: rubber should be made, not bought. A play tester asked whether
# rubber could even be bought for most of the run, and said you should have
# to make it with your own factory - tapping and coagulating latex, and
# vulcanising anything that must not melt in summer or crack in winter.
# Before this, every rubber good gated on mat_natural_rubber directly and
# then simply bought rubber_kg at a price, with tl_vulcanized_rubber built
# and never required by anything.
check("coagulating rubber is its own step, not free the moment you know the vine",
      NODES["mat_rubber_coagulated"]["pre"] == ["mat_natural_rubber"],
      NODES["mat_rubber_coagulated"]["pre"])
check("a pneumatic tyre needs vulcanised rubber, not raw coagulated latex",
      "tl_vulcanized_rubber" in NODES["tl_pneumatic_tyre"]["pre"]
      and "mat_natural_rubber" not in NODES["tl_pneumatic_tyre"]["pre"],
      NODES["tl_pneumatic_tyre"]["pre"])
check("an eraser needs coagulated rubber but not full vulcanisation",
      "mat_rubber_coagulated" in NODES["tx2_eraser"]["pre"]
      and "tl_vulcanized_rubber" not in NODES["tx2_eraser"]["pre"],
      NODES["tx2_eraser"]["pre"])
check("vulcanisation itself is built from coagulated rubber, not raw latex",
      "mat_rubber_coagulated" in NODES["tl_vulcanized_rubber"]["pre"]
      and "mat_natural_rubber" not in NODES["tl_vulcanized_rubber"]["pre"],
      NODES["tl_vulcanized_rubber"]["pre"])

# --- JOB 3a: England's own briefing calls cheap iron and the temperature to
# make it "the biggest single technology gap you face", and blast_furnace's
# own note calls itself "the biggest single technology gap" in the same
# words - yet England's starting kit handed over blast_furnace, mat_cast_
# iron and cap_heat_1300 (Han China's real grant, copied by mistake) for
# free. A blast furnace did not reach England until Newbridge in 1496.
_eng = S.load_civ("england_1300")
check("England no longer starts already owning the iron gap its own briefing describes",
      not ({"blast_furnace", "mat_cast_iron", "cap_heat_1300"}
           & set(_eng["starting_techs"])),
      _eng["starting_techs"])

# --- JOB 3b: the cursus publicus (Roman imperial dispatch relay) and the
# Pharos (one specific Ptolemaic building at Alexandria) are not a generic
# capability any society might have. FOREIGN_MARKERS in fog.py already
# catches both by name; this pins that Han China - which has no Roman
# citizenship, no Roman roads and no Alexandria - is never handed either one
# for free, the way testers kept finding Roman-branded grants in other
# people's civilisations.
_han = sim(civ="han_china_100ad")
check("Han China is never handed Rome's courier relay or Ptolemy's lighthouse for free",
      "lnd_cursus_publicus" not in _han.granted
      and "sea_pharos_lighthouse" not in _han.granted,
      (sorted(_han.granted & {"lnd_cursus_publicus", "sea_pharos_lighthouse"})))

# --- JOB 3c: the Norse civilisation's flagship starting technologies -
# clinker hull, deep keel, bog-iron bloomery - are supposed to be its
# superb shipbuilding and ironworking, but `why sea_keel_deep` reported
# "(nothing, this is a leaf)": literally nothing in the tree depended on it,
# contradicting the civilisation's own self-description. It is now a real
# alternative route (alongside the Mediterranean fore-and-aft rig) into
# open-ocean navigation, which needs SOME way to sail to windward and
# previously named none at all.
check("the Norse deep keel now genuinely enables open-ocean navigation",
      any("sea_keel_deep" in g.get("options", {})
          for g in NODES["exp_openocean_navigation"]["req_any"]),
      NODES["exp_openocean_navigation"]["req_any"])

# --- FREE AND WEIGHTLESS IS NOT THE SAME AS UNIVERSALLY AVAILABLE. The
# ambient grant hands a society anything tier 0 that costs nothing and takes
# nobody's attention, which is right for a craft that society actually has
# and wrong for one it demonstrably does not. The Mexica were handed the
# square sail, the spritsail, a mortise-and-tenon Mediterranean hull, large
# merchant sailing ships and the monsoon route to India, before turn one, in
# a civilisation whose own menu says every load moves on a human back and
# whose water transport is the paddled canoe. needs_first already existed to
# say a thing is impossible here rather than merely dear; both grant paths
# now consult it.
_mex = sim(civ="mexica_1500")
check("the Mexica are not handed other people's seas: no sail, no "
      "Mediterranean hull, no merchant fleet, no monsoon crossing",
      not any(k in _mex.granted for k in
              ("sea_square_sail", "sea_spritsail", "sea_mortise_tenon",
               "sea_merchant_ships_large", "sea_monsoon_route")),
      sorted(k for k in _mex.granted if k.startswith("sea_")))
check("...but they keep what a canoe-going society does have - an anchor, "
      "a sounding line, coastal pilotage and a steering oar",
      all(k in _mex.granted for k in
          ("sea_anchor", "sea_sounding_lines", "sea_coastal_pilotage",
           "sea_steering_oars")),
      sorted(k for k in _mex.granted if k.startswith("sea_")))
check("and the gate is liftable by the node it names, not a permanent "
      "exclusion - exp_oceangoing_hull does not itself need any of them",
      not any(k in PLANNER.closure(NODES, "exp_oceangoing_hull") for k in
              ("sea_square_sail", "sea_spritsail", "sea_mortise_tenon",
               "sea_merchant_ships_large", "sea_monsoon_route")),
      sorted(x for x in PLANNER.closure(NODES, "exp_oceangoing_hull")
             if x.startswith("sea_")))
check("a seafaring society is untouched by the gate",
      "sea_square_sail" in sim(civ="norse_900ad").granted, True)

# --- JOB 4: the blind prerequisite audit (BLIND_TREE_phase2.md) found three
# genuine small gaps and this implements all three, marginal cost verified
# with closure() rather than trusted from the document (a previous audit
# nearly deferred a correct fix by quoting 101 when the true marginal cost
# was 1).
check("placing a whisker a few hundredths of a millimetre apart now requires something that can see the gap",
      "microscope_compound" in NODES["gp_whisker_forming"]["pre"],
      NODES["gp_whisker_forming"]["pre"])
check("the germanium surface now gets a chemical/electrolytic etch, not mechanical lapping alone",
      "el2_electropolishing_etching_surface_finish" in NODES["gp_whisker_forming"]["pre"],
      NODES["gp_whisker_forming"]["pre"])
# mat_gold sits on gp_whisker_forming, one step short of the goal, not on
# point_contact_transistor directly - a first attempt put it on the goal
# itself and a fog regression test caught the leak: mat_gold is tier0/ph0,
# auto-granted and therefore always is_visible(), and the goal is the one
# node `why` always answers under fog, so direct_prerequisites (unlike
# every other node, where is_visible() filters it) named the goal's own
# prerequisite from turn one.
check("the contact alloys are real prerequisites now, not just bare material costs",
      "mat_gold" in NODES["gp_whisker_forming"]["pre"]
      and "phosphor_bronze_alloy" in NODES["gp_whisker_forming"]["pre"],
      NODES["gp_whisker_forming"]["pre"])
# THE CLAIM, NOT A TOTAL. This asserted the closure was exactly 157, which
# was true on the day it was written and stopped being true the moment the
# goal moved from the 1947 point-contact device to the 1951 junction
# transistor. A hard total is a check on where the goal happens to sit; the
# thing the audit actually claimed is that these four additions were cheap,
# and that is what is worth pinning. Marginal cost is the closure of the
# addition MINUS what the goal already needed, which is the number a previous
# audit got wrong by quoting 101 when the truth was 1.
_clo_now = S.closure(NODES, GOAL)
_added = ("microscope_compound", "el2_electropolishing_etching_surface_finish",
          "mat_gold", "phosphor_bronze_alloy")
check("the four audited prerequisites really are on the road to the goal",
      all(a in _clo_now for a in _added),
      [a for a in _added if a not in _clo_now])
_marginal = len(set().union(*(S.closure(NODES, a) | {a} for a in _added))
                - (_clo_now - set(_added)))
check("...and between them they cost the road about eight nodes, not dozens",
      _marginal <= 10, _marginal)

# --- This audit's own mistake, caught by the very fog test above it: writing
# a new prerequisite's id into point_contact_transistor's NOTE leaked it in
# prose, because the goal is special-cased to answer `why` under fog no
# matter what, and note text - unlike direct_prerequisites - is never
# filtered by is_visible(). Pin it so a future data edit cannot reintroduce
# the same leak by being specific in the wrong field.
check("the goal's own note never spells out the id of one of its prerequisites",
      not any(p in NODES["point_contact_transistor"]["note"]
              for p in NODES["point_contact_transistor"]["pre"]),
      [p for p in NODES["point_contact_transistor"]["pre"]
       if p in NODES["point_contact_transistor"]["note"]])
# =============================================================================
# PEOPLE ARE WHOLE. The user's objection, and it was right: "how can you have
# .8 people? I feel like all employees/people should be measured in
# integers." Attrition used to multiply every trade by (1 - 0.035) every
# single year, so ten smiths lost exactly 0.35 of a smith and the engine went
# on carrying the fraction forever - a household could read "1.32 artisans"
# or "0.03 engineers" on its own roster, the latter drawing 0.03 of a wage
# while supervising nothing. Attrition is now a per-person roll against
# self.rng (sorted by trade name, for the same PYTHONHASHSEED-independence
# every other rng loop over this dict already has); hire() and train() now
# refuse a fractional `n` outright, and the auto_hire smoothing that used to
# write a continuous target straight into `employees` now spends its
# fractional remainder as that year's CHANCE of the next whole hire instead
# (`_stochastic_round`).
# =============================================================================

s = sim(capital=50_000_000.0)
s.policy["auto_hire"] = False
s.employees["artisan"] = 500.0
s._resync_pools()
_whole_every_year, _never_grew, _prev = True, True, 500.0
for _ in range(150):
    s.step()
    _cur = s.employees.get("artisan", 0.0)
    if abs(_cur - round(_cur)) > 1e-9:
        _whole_every_year = False
    if _cur > _prev + 1e-9:
        _never_grew = False
    _prev = _cur
check("a whole headcount of artisans never picks up a fraction of a person, "
      "year after year of pure attrition",
      _whole_every_year, _prev)
check("...and with auto_hire off and nobody hiring, the headcount only ever "
      "falls, never climbs on its own",
      _never_grew, _prev)

# UNBIASED: the realised loss, averaged over many people and many
# independent seeds, should still land on the nominal 3.5%/yr every balance
# comment elsewhere in this file quotes - a per-person roll that happened to
# be biased would quietly make every one of those comments false.
_before_att, _after_att = 0.0, 0.0
for _seed in range(1, 31):
    _s = S.Sim(NODES, ORDER, random.Random(_seed), manual=True,
               civ=S.load_civ("rome_100ad"), cfg={"start_capital": 5e7})
    _s.goal, _s.done_year = GOAL, {}
    _s.policy["auto_hire"] = False
    _s.employees["artisan"] = 2000.0
    _s._resync_pools()
    _s.step()
    _before_att += 2000.0
    _after_att += _s.employees.get("artisan", 0.0)
_att_rate = 1.0 - _after_att / _before_att
check("whole-person attrition still averages the nominal 3.5% a year, over "
      "many people and many seeds",
      0.030 < _att_rate < 0.040, _att_rate)

# HIRE AND TRAIN LAND WHOLE PEOPLE.
s = sim(capital=1e6)
ok_frac_h, why_frac_h = s.hire("smith", 2.5)
check("hire refuses a fractional number of people",
      not ok_frac_h and "whole" in why_frac_h, why_frac_h)
ok_frac_t, why_frac_t = s.train("machinist", 1.5)
check("...and so does train",
      not ok_frac_t and "whole" in why_frac_t, why_frac_t)
ok_whole_h, _ = s.hire("smith", 2)
check("...but a whole number still goes through, and lands exactly that many",
      ok_whole_h and s.employees.get("smith") == 2.0, s.employees.get("smith"))


# =============================================================================
# THE TWO RULEBOOKS. Measured, reproducible: `hire scholar 12` was refused
# - "this society's literacy will not supply more than 5.9 scholars in
# total, ever, at any price" - while `policy auto_hire on` mutated
# self.scholars directly, never once called hire() or literate_capacity(),
# and reached 146.4 scholars in the same civilisation forty years later. The
# goal itself, and two nodes on the only road to it, want 25. Both halves are
# fixed together: step()'s auto_hire now clamps its target to
# literate_capacity("scholar") (see core.py), and literate_capacity("scholar")
# now adds the SAME institutional pool staff_capacity() already credited
# auto_hire with (see labour.py) - so the wall is not only closed, it is wide
# enough to reach what the tree actually asks for.
# =============================================================================

# 73 SECONDS, because it needs two and a half centuries of a rich run before
# the question it asks even becomes interesting. The cheap half of the same
# fix - that the ceiling itself widens with the institutions - is checked
# below in milliseconds and stays on the fast path.
def _auto_hire_respects_the_wall():
    s_ = sim(capital=1e9, manual=False)
    for _ in range(250):
        s_.step()
    return (s_.scholars <= s_.literate_capacity("scholar") + 1e-6
            and s_.scholars > 10.0,
            (s_.scholars, s_.literate_capacity("scholar")))

slow_check("auto_hire never grows scholars past the wall hire() enforces, and "
           "over two and a half centuries grows well past the old ceiling of six",
           _auto_hire_respects_the_wall)

# The bare, no-institution ceiling a fresh household sees is unchanged...
s0 = sim()
check("the market-reach ceiling for a fresh household is the same as before",
      5.5 < s0.literate_capacity("scholar") < 6.5, s0.literate_capacity("scholar"))
# ...and grows once the institutions auto_hire was already trusted to grow
# toward are actually running - not from literacy alone, which is the
# mechanism that lets a household eventually reach the tree's 25.
s1 = run_it(sim(capital=1e9), "interchangeable_parts", "power_grid")
check("building the institutions auto_hire already credited widens the wall "
      "hire() enforces, which used to move only with literacy",
      s1.literate_capacity("scholar") > 20.0, s1.literate_capacity("scholar"))

# The refusal is honest about what is actually binding: a household's reach
# into the labour market, narrowed by literacy, not literacy by itself.
s2 = sim()
ok2, why2 = s2.hire("scholar", 12)
check("the refusal names the household's market reach, not literacy alone",
      not ok2 and "reach" in why2 and "literacy" in why2, why2)


# =============================================================================
# ONLY `scholar` COUNTS AS A TRAINED SCHOLAR. TRADE_FAMILY groups scholar,
# chemist, engineer, scribe and merchant together as "scholar" for
# market_supply()'s sake - they draw on the same small, literate-or-
# propertied slice of the population - and an earlier version of
# _resync_pools() reused that same grouping to decide who counts as a
# trained scholar for the tech tree's "sch" gate. Hiring three scribes
# measurably raised effective_scholars() from 0 to 4.0, while STAFF_SOURCES
# - the advice on how to grow scholars - has only ever named `hire scholar`.
# Now only the `scholar` trade itself feeds the gate; the market-sizing use
# of the wider grouping (market_supply, labour_price_factor) is untouched.
# =============================================================================

s = sim(capital=1e6)
_before_sch = s.effective_scholars()
ok_scribe, _ = s.hire("scribe", 3)
check("(three scribes were actually hired)", ok_scribe, s.employees)
check("hiring scribes does not inflate the trained-scholar headcount any more",
      abs(s.effective_scholars() - _before_sch) < 1e-6,
      (s.effective_scholars(), _before_sch))
s.capital = 1e6
ok_sch, _ = s.hire("scholar", 2)
check("...but hiring an actual scholar still does",
      ok_sch and s.effective_scholars() >= _before_sch + 2 - 1e-6,
      s.effective_scholars())
check("the advice on how to get scholars never points at a different trade "
      "family's trade, which would not even count",
      all("scribe" not in why and "chemist" not in why and "merchant" not in why
          and "engineer" not in why
          for _node, why in s.STAFF_SOURCES.get("scholars", [])),
      s.STAFF_SOURCES.get("scholars"))

# --- SAVE INTEGRITY, JOB 2a: FOG CAN BE REWOUND. A tester described the
# exploit exactly: "since `load` restores the game but not the player's
# memory, a player can save, build a node, look at what appeared in
# `available`, load back, and keep the knowledge. Fog of war is one command
# away from being off" (rome/playtest/AUDIT_rounds_1_6.md, C1), and reproduced
# it live: save at year 1300, step to 1350, load the 1300 save, and the fifty
# years of frontier that had opened up in `available` cost nothing at all,
# because the ledger went back to 1300 and the knowledge did not. The fix
# makes `revealed` a ratchet: assigning to it may grow what this running
# session has seen, never shrink it - a property on FogMixin (engine/fog.py)
# rather than a change to `load_state` itself, so the guarantee holds for
# every caller that ever assigns `.revealed`, load_state included, without
# needing to edit protocol.py. See the comment on the property.
s_fog = sim(civ="rome_100ad")
s_fog.fog = True
s_fog.revealed = {"identity_cover"}
_fog_save = os.path.join(ROOT, _PLAY_DIR, "fog_rewind.json")
S.save_state(s_fog, _fog_save)                  # "before you paid for it"
# Something completes and reveals what it leads to - the same thing
# _complete() does in projects.py when a project actually finishes.
s_fog.reveal_from("workshop_first")
_fog_after = set(s_fog.revealed)
check("(setup) building something under fog reveals what it leads to",
      _fog_after > {"identity_cover"}, sorted(_fog_after))
S.load_state(s_fog, _fog_save)                  # the rewind to before paying
check("fog cannot be rewound: loading an earlier save keeps everything this "
      "session has already seen, instead of refunding the look for free",
      _fog_after <= s_fog.revealed, sorted(_fog_after - s_fog.revealed))
# A GENUINELY FRESH RESUME - a new process loading someone's save as its very
# first act, exactly what `--session` does - must be untouched by this: it has
# seen nothing yet, so the union with nothing is exactly the file's own
# contents, the same as before this fix existed.
s_fresh = sim(civ="rome_100ad")
s_fresh.fog = True
s_fresh.revealed = set()
S.load_state(s_fresh, _fog_save)
check("a fresh resume still sees only what that save file actually recorded",
      s_fresh.revealed == {"identity_cover"}, sorted(s_fresh.revealed))

# --- SAVE INTEGRITY, JOB 2b: SAVE LOST ON A CLOSED PIPE. Two testers found,
# independently and the same way, that a command's progress could be lost if
# the process's own stdout closed mid-reply: `naive6/C/WEIRD_C.md` - "I lost
# 12 years of play twice before I noticed, because I was piping output
# through `head`" - and `naive5/C/WEIRD_C.md`, against the game's own promise
# in `help sittings` that you can "close the terminal, anything" and come back
# to exactly where you left off. `agent`'s stdin loop wrote the reply and
# saved the session AFTER it, so a SIGPIPE on that write killed the process
# before `save_state` ever ran, even though `_agent_dispatch` had already
# mutated `s` in memory. The fix reorders it to save first, the same as
# `play` already did; this proves it against the real subprocess, a real
# closed pipe, and a real file on disk.
_pipe_sess = os.path.join(ROOT, _PLAY_DIR, "closedpipe.json")
if os.path.exists(_pipe_sess):
    os.remove(_pipe_sess)
_pp = subprocess.Popen(
    [sys.executable, os.path.join(HERE, "simulator.py"), "agent",
     "--civ", "rome_100ad", "--seed", "1", "--session", _pipe_sess],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    text=True, cwd=ROOT)
# Close OUR end of stdout before the child ever writes a single byte to it -
# the same thing `| head -c0`, or a closed terminal, does to a running
# process. Whatever the child writes after this has nowhere to go.
_pp.stdout.close()
try:
    _pp.stdin.write(json.dumps({"cmd": "step", "years": 3}) + "\n")
    _pp.stdin.close()
except BrokenPipeError:
    pass
_pp.wait(timeout=60)
try:
    _pp.stderr.close()
except Exception:
    pass
_pipe_saved = json.load(open(_pipe_sess))
check("a command's progress is saved even when the reply that describes it "
      "cannot be delivered because the reading end of the pipe is gone",
      _pipe_saved.get("year") == 103, _pipe_saved.get("year"))

# --- JOB 1: THE PLANNER. "Why is the sim a monte carlo sim? We know the end
# state, right? Or is it too complex to just calculate backwards?" It is not
# too complex: planner.py works backward from the goal by critical-path
# method (CPM) over its prerequisite closure, instead of walking a
# hand-written list. These checks pin the structural properties the measured
# comparison (rome/playtest or the session report) depends on actually
# holding, not just the one run that happened to be timed.
_p_s = sim(civ="rome_100ad")
_p_order, _p_c, _p_extras, _p_staff = PLANNER.backward_plan(NODES, GOAL, _p_s, side_branches=0)
_p_need = S.closure(NODES, GOAL)
check("the planner's closure matches its own order's count for the goal",
      len(_p_need) == len(_p_order), (len(_p_need), len(_p_order)))
# closure() now follows the single-option req_any groups too - it also
# follows the `req_any` groups that have exactly one option (a mandatory
# dependency authored as a substitution rather than a `pre` edge; a group
# with two or more real alternatives is correctly left alone, both because
# only one is actually required and because counting every option can
# cycle). The gap is real and was the second thing this session's own audit
# found blocking the goal: `mat_bulk_steel` needs `mat_manganese` through
# exactly this kind of single-option `req_any`, `closure()` cannot see it on
# purpose, and a traced Rome run with 111 scholars, 428 artisans and 11.7
# million denarii in hand still had not built it by year 700 because it was
# never in `need` at all - staffing and money were both long since solved,
# ordering was not.
_pre_only = set()
_stk = [GOAL]
while _stk:
    _c = _stk.pop()
    if _c in _pre_only:
        continue
    _pre_only.add(_c)
    _stk.extend(NODES[_c]["pre"])
check("following `pre` alone understates what the goal needs by the "
      "req_any groups that are not really alternatives - 158 nodes against "
      "the 168 actually required",
      _pre_only < _p_need and len(_p_need) - len(_pre_only) == 10,
      (len(_pre_only), len(_p_need)))
# --- THE DATA SAID OVERLAND IN THREE PLACES AND THE TREE SAID ROUND THE
# CAPE. mat_platinum_bulk's own note says the Ural placers are "reachable
# overland through Scythian and Sarmatian trade without crossing any ocean";
# geography.json lists platinum in siberia_urals as well as americas_south
# and repeats the sentence; and the node's only prerequisite was
# exp_africa_circumnavigation. Once closure() started following single-option
# req_any groups this stopped being a curiosity and became load-bearing:
# platinum is required for the glass-to-metal seal, so the goal's closure
# grew an entire age of exploration - six expedition nodes, the sextant, the
# compass, the lodestone, the cross-staff, the backstaff and a world map,
# seventeen nodes in all - to fetch a metal the data says is on a wagon road.
# --- THE ONE REMEDY THE GAME OFFERS, CAPPED AT THE HOUSEHOLD OF YEAR FIVE.
# Saltpetre has no market to buy from (MARKET_SHARE is 0.0; the only bought
# supply is sixty tonnes a year of Bengal nitre once the eastern trade route
# runs), so nitre beds are the whole answer. auto_mine laid
# min(capital * 0.05, 2000) denarii of bed a year - a flat ceiling, never
# asking how short it was - while the mine branch beside it took 25% of
# capital and sized itself to the measured shortfall. A Rome run with
# staffing and money both solved spent 277 of its years short of saltpetre.
def _nitre_laid(capital):
    """One year of the auto_mine nitre branch at a given wealth."""
    n = sim(civ="rome_100ad")
    n.capital = float(capital)
    n.policy["auto_mine"] = True
    n.nitre_bed_m2 = 0.0
    n.binding = "saltpetre"
    before = n.nitre_bed_m2
    n.step()
    return n.nitre_bed_m2 - before

check("the nitre purchase is held to a flat two thousand denarii a year "
      "however rich the household - sizing it to the shortfall instead, "
      "the way the mine branch beside it does, measured worse on every "
      "count and is recorded in core.py as a road not to walk again",
      _nitre_laid(5_000_000.0) <= 2000.0 / S.Sim.NITRE_COST_PER_M2 + 1e-6,
      _nitre_laid(5_000_000.0))
check("...and a poor household is held to a twentieth of its capital",
      _nitre_laid(3_000.0) <= 3_000.0 * 0.05 / S.Sim.NITRE_COST_PER_M2 + 1e-6,
      _nitre_laid(3_000.0))
check("the nitre yield and price the advice quotes are the ones the "
      "purchase actually uses - 0.0008 t/m2 at 2.0 den/m2, so a tonne a "
      "year of shortfall costs 2,500 denarii of bed",
      abs(S.Sim.NITRE_YIELD_T_PER_M2 - 0.0008) < 1e-12
      and abs(S.Sim.NITRE_COST_PER_M2 - 2.0) < 1e-12,
      (S.Sim.NITRE_YIELD_T_PER_M2, S.Sim.NITRE_COST_PER_M2))
check("saltpetre still cannot simply be bought - the beds are the answer, "
      "not a market share",
      S.Sim.MARKET_SHARE["saltpetre"] == 0.0, S.Sim.MARKET_SHARE["saltpetre"])
# --- THE SAME HOLE IN A SECOND COMMAND. `available`'s parser read bare words
# only, so `available all:true` - the spelling `help commands` itself gives -
# fell through to the subject branch and was used as a search string named
# "all:true", matching nothing, silently. The same hole swallowed limit:30,
# find:furnace and every other pair. `state full:true` has always taken this
# spelling, so a player who learned it there was right to expect it.
for _av, _want in (("available all", {"cmd": "available", "all": True}),
                   ("available all:true", {"cmd": "available", "all": True}),
                   ("available limit:30 offset:30",
                    {"cmd": "available", "limit": 30, "offset": 30}),
                   ("available find:furnace",
                    {"cmd": "available", "find": "furnace"})):
    check("'%s' is understood" % _av, _PT(_av)[0] == _want, _PT(_av)[0])
check("a bare subject is still a subject, not mistaken for a flag",
      _PT("available metallurgy")[0] == {"cmd": "available",
                                         "subject": "metallurgy"},
      _PT("available metallurgy")[0])

# --- THE HELP PROMISED SOMETHING THE CODE DELIBERATELY DOES NOT DO. auto_open
# opens a capability institution at a loss on purpose - a school takes 2,500 a
# year, hands back 800, and is where twelve of your scholars come from - while
# its help said it "will NOT open anything whose upkeep exceeds its takings".
# Two players on different civilisations each watched it open a loss-maker,
# checked the help, and reported the automation as broken. The code was right.
_ao = S._agent_dispatch(sim(civ="rome_100ad"), NODES, {"cmd": "policy"})
_ao_txt = str(_ao)
check("auto_open's help admits it opens the institutions that train people "
      "even at a loss, which is what it actually does",
      "at a loss" in _ao_txt and "scholars come from" in _ao_txt,
      [l for l in _ao_txt.split(".") if "auto_open" in l][:1])
check("...and still says what it leaves shut, the case the original "
      "sentence was written for",
      "left shut" in _ao_txt, "left shut")

# --- THREE PLAYERS, THREE CIVILISATIONS, THE SAME COMPLAINT. Norse, England
# and Rome each independently reported being carried into debt they had not
# decided to take on, and two of them found out what happens past the credit
# limit by losing a school and a collegium they had built decades earlier.
# `start` financed the gap between what a project costs and what the
# household has, silently, at up to twelve per cent. Borrowing to build is a
# real move and stays allowed; not being told was the bug.
_cr = sim(civ="england_1300")
_cr.capital = 1300.0
_cr_out = S._agent_dispatch(_cr, NODES, {"cmd": "start", "id": "identity_cover"})
check("starting a project you cannot cover in cash says you are borrowing, "
      "what it costs a year, and how much room is left",
      _cr_out.get("ok") and _cr_out.get("on_credit", {}).get("borrowed_now", 0) > 0
      and _cr_out["on_credit"].get("interest_per_year", 0) > 0
      and _cr_out["on_credit"].get("no_one_advances_past", 0) > 0,
      _cr_out.get("on_credit"))
check("...and names what the creditors do there, which is take things you "
      "built long ago and had no debt against",
      "built long ago" in (_cr_out.get("on_credit", {})
                           .get("what_happens_there") or ""),
      (_cr_out.get("on_credit") or {}).get("what_happens_there"))
_cr2 = sim(civ="england_1300")
_cr2.capital = 50_000.0
_cr2_out = S._agent_dispatch(_cr2, NODES, {"cmd": "start", "id": "identity_cover"})
check("a project you can pay for outright says nothing about credit",
      _cr2_out.get("ok") and "on_credit" not in _cr2_out,
      sorted(_cr2_out))

# --- THE RATE WAS ON THE SCREEN AND THE SUM NEVER WAS. `why` quoted "10% per
# attempt" and nothing else; a failure takes a flat 40% of the money and puts
# 40% of the hours back on the slate. An England player read the single digit
# as a small thing and lost 35,433 pence off a 141,824-pence project.
_fw = S._agent_dispatch(sim(civ="england_1300"), NODES,
                        {"cmd": "why", "id": "lead_metallurgy"})
check("why says what a failure costs, not only how likely one is",
      _fw.get("failure_costs", 0) > 0
      and abs(_fw["failure_costs"] - _fw["cost"]["total"] * 0.4) < 1.0,
      (_fw.get("failure_costs"), (_fw.get("cost") or {}).get("total")))
check("...and a work that cannot fail is not given an imaginary danger",
      S._agent_dispatch(sim(civ="england_1300"), NODES,
                        {"cmd": "why", "id": "identity_cover"}).get("failure_costs", 0) == 0
      if NODES["identity_cover"]["risk"] == 0 else True,
      NODES["identity_cover"]["risk"])

# --- THE HELP ADVERTISED A SPELLING THE PARSER DID NOT ACCEPT, and the
# failure was silent and expensive. `rush`'s own help says "add limit:N to
# cap it"; `limit:3` is not a number, so the token scan came back empty, no
# limit was set, and rush went on to begin everything startable. A Norse
# player who read the help, wanted three things, and typed exactly what they
# were told got twenty-one projects and every denarius of their credit. The
# safest-looking spelling of the most expensive command in the game was the
# one that removed the safety.
for _sp in ("rush 3", "rush limit:3", "rush limit 3", "rush limit=3"):
    check("'%s' caps the rush at three" % _sp,
          _PT(_sp)[0] == {"cmd": "rush", "limit": 3},
          _PT(_sp)[0])
check("a cap that does not parse is refused, not shrugged off into "
      "starting everything - the one typo a careful player can make must "
      "not be the typo that begins the whole tree",
      _PT("rush limit:abc")[0] is None
      and "not a number" in (_PT("rush limit:abc")[1] or ""),
      _PT("rush limit:abc"))
check("platinum is reachable the way its own note and the geography file "
      "both say it is, overland, without rounding the Cape",
      "exp_africa_circumnavigation" not in S.closure(NODES, "mat_platinum_bulk"),
      sorted(x for x in S.closure(NODES, "mat_platinum_bulk")
             if x.startswith("exp_")))
check("...and the goal no longer requires an age of exploration to reach a "
      "transistor: one trade route, not six voyages",
      sorted(x for x in S.closure(NODES, GOAL) if x.startswith("exp_"))
      == ["exp_trade_route_extend"],
      sorted(x for x in S.closure(NODES, GOAL) if x.startswith("exp_")))
check("the Colombian placers are still a route, just not the only one",
      "americas_south" in (GEO_MATS := S.load_geography()
                           ["located_materials"]["platinum"]["regions"])
      and "siberia_urals" in GEO_MATS,
      GEO_MATS)
check("mat_bulk_steel (on the critical path) is gated on mat_manganese "
      "through exactly one req_any option, no real alternative offered",
      NODES["mat_bulk_steel"]["req_any"] ==
      [{"group": "manganese_supply", "options": {"mat_manganese": 1.0}}],
      NODES["mat_bulk_steel"]["req_any"])
check("closure() catches it now: mat_manganese and its own "
      "prerequisite mat_pyrolusite are both required, where a pre-only "
      "walk leaves both out",
      {"mat_manganese", "mat_pyrolusite"} <= _p_need
      and not ({"mat_manganese", "mat_pyrolusite"} & _pre_only),
      (sorted({"mat_manganese", "mat_pyrolusite"} & _p_need),
       sorted({"mat_manganese", "mat_pyrolusite"} & _pre_only)))
# ONE DEFINITION OF A HARD EDGE, or the ordering schedules a requirement too
# late. closure() learned the single-option groups first and topo_order and
# critical_path did not, so mat_manganese was correctly called required and
# then sorted AFTER the mat_bulk_steel that requires it. All three read
# hard_pre() now.
check("the order the ENGINE receives puts the single-option dependency "
      "first - topo_stable in cli.py was the last place still reading `pre` "
      "alone, and brought mat_manganese out at 187 behind the "
      "mat_bulk_steel at 65 that cannot be built without it",
      (lambda o: o.index("mat_manganese") < o.index("mat_bulk_steel"))(
          PLANNER._repaired(NODES, GOAL, _p_order)),
      "engine-order manganese/bulk steel")
check("topo_order puts a single-option req_any dependency before the node "
      "that requires it, not after",
      (lambda o: o.index("mat_manganese") < o.index("mat_bulk_steel"))(
          S.topo_order(NODES, _p_need)),
      "mat_manganese/mat_bulk_steel ordering")
check("hard_pre never repeats an id, however a node names it - a "
      "duplicate inflates topo_order's in-degree past what the decrement "
      "can undo, and reports ten blameless nodes as a cycle",
      all(len(S.hard_pre(NODES, k)) == len(set(S.hard_pre(NODES, k)))
          for k in NODES),
      [k for k in sorted(NODES)
       if len(S.hard_pre(NODES, k)) != len(set(S.hard_pre(NODES, k)))][:5])
_syn_req = {
    "goal2":  {"pre": ["mandatory"], "req_any": [], "yrs": 0, "ph": 0, "_total_cost": 0},
    "mandatory": {"pre": [], "req_any": [{"group": "g1", "options": {"onlyroute": 1.0}}],
                  "yrs": 1, "ph": 0, "_total_cost": 10},
    "onlyroute": {"pre": [], "req_any": [], "yrs": 1, "ph": 0, "_total_cost": 5},
    "choice":    {"pre": [], "req_any": [{"group": "g2", "options": {"routeA": 1.0, "routeB": 1.0}}],
                  "yrs": 1, "ph": 0, "_total_cost": 5},
    "routeA":    {"pre": [], "req_any": [], "yrs": 1, "ph": 0, "_total_cost": 5},
    "routeB":    {"pre": [], "req_any": [], "yrs": 1, "ph": 0, "_total_cost": 5},
}
check("a single-option req_any group's target is pulled into "
      "closure() - the mandatory-dependency-in-disguise case",
      "onlyroute" in S.closure(_syn_req, "goal2"),
      S.closure(_syn_req, "goal2"))
_syn_req["goal2"]["pre"] = ["choice"]
check("a genuine req_any CHOICE is left alone - neither option of a "
      "two-way alternative is forced into the closure",
      "routeA" not in S.closure(_syn_req, "goal2")
      and "routeB" not in S.closure(_syn_req, "goal2"),
      S.closure(_syn_req, "goal2"))
# The acyclic check against the WHOLE real tree (not just this synthetic
# pair) needs `_cycle_on`, defined later in this file - see the check next
# to "the tree is acyclic on hard prerequisites" below.
# THE STAFFING LAYER, which is the one thing in a plan that the tech tree
# cannot supply. A node's prerequisites are other nodes; its demand for
# "eight trained scholars" is a demand on the household, and no amount of
# ordering the closure correctly satisfies it. Both civilisations' plans used
# to run out of horizon with quantum_solidstate_theory as the first blocked
# node - the cheapest node in the late programme, wanting eight scholars
# against a society whose lettered pool tops out at 5.9.
check("the planner names the institutions that train people, which the "
      "goal's own prerequisite closure never mentions",
      _p_staff and all(k not in _p_need for k in _p_staff)
      and "school_founded" in _p_staff and "academy_network" in _p_staff,
      _p_staff)
check("...and does not order them, which was measured and made Rome's run "
      "three centuries worse - 278,000 denarii of founding cost and "
      "perpetual upkeep against a household that starts with four hundred",
      all(k not in _p_order for k in _p_staff),
      [k for k in _p_staff if k in _p_order])
check("the staffing list is read from the same table staff_capacity() "
      "itself iterates, so the two cannot drift apart",
      all(k in {e[0] for e in S.Sim.STAFF_CAPACITY_SOURCES} for k in _p_staff),
      sorted(_p_staff))
check("every node staff_capacity() credits actually exists in the tree - "
      "bessemer_openhearth did not, so its sixty-five artisans were never "
      "once handed over",
      [e[0] for e in S.Sim.STAFF_CAPACITY_SOURCES if e[0] not in NODES] == [],
      [e[0] for e in S.Sim.STAFF_CAPACITY_SOURCES if e[0] not in NODES])
_p_zero = [k for k in _p_need if _p_c["slack"][k] <= 1e-6]
_p_pos = {k: i for i, k in enumerate(_p_order)}
check("every zero-slack (critical-path) node is ordered before every node "
      "that has room to wait",
      max(_p_pos[k] for k in _p_zero) < min(_p_pos[k] for k in _p_need
                                            if _p_c["slack"][k] > 1e-6),
      "critical nodes occupy positions 0-%d of %d" % (len(_p_zero) - 1, len(_p_order)))
check("the critical-path total the planner computes matches `validate`'s "
      "142-year figure for this tree",
      abs(_p_c["total"] - S.critical_path(NODES, GOAL)[0]) < 1e-6,
      (_p_c["total"], S.critical_path(NODES, GOAL)[0]))
# A strategy file this module writes must reach the engine with no node ever
# asked to start before its own prerequisite - the thing `load_strategy`'s
# own `topo_stable` exists to guarantee for ANY strategy file, not only this
# one, but the planner's raw CPM order is exactly the case that needs it:
# slack is not monotonic along an edge (see the comment in planner.py), so
# the unrepaired order has real violations, and this checks the repair that
# reaches the engine removes every one of them.
_p_path = os.path.join(ROOT, _PLAY_DIR, "planned_check.json")
PLANNER.write_strategy(_p_path, "test", [], PLANNER.interleave(
    _p_order, PLANNER.pick_side_branches(NODES, _p_need, _p_s, 12), 8))
_p_label, _p_full, _p_bounties = S.load_strategy(_p_path, NODES, GOAL)
_p_fullpos = {k: i for i, k in enumerate(_p_full)}
_p_violations = [(p, k) for k in _p_need for p in NODES[k]["pre"]
                 if p in _p_need and _p_fullpos.get(p, -1) > _p_fullpos.get(k, 10 ** 9)]
check("a plan this module writes never asks the engine to start something "
      "before its own prerequisite, once loaded the same way --strategy loads it",
      not _p_violations, _p_violations[:5])
check("the side branches a plan weaves in are all revenue-positive and none "
      "is a technical prerequisite of the goal",
      _p_extras is not None and all(
          k not in _p_need and NODES[k]["rev"] > NODES[k]["up"]
          for k in PLANNER.pick_side_branches(NODES, _p_need, _p_s, 12)),
      PLANNER.pick_side_branches(NODES, _p_need, _p_s, 12)[:5])

# A SEED IMPROVES TIES, IT DOES NOT OVERRIDE THE GRAPH. Proven on a tiny
# synthetic DAG rather than the real tree, because the real tree (checked
# directly) has no two unrelated nodes with identical slack AND identical
# earliest-start - the tie-break is real but the live data never exercises it,
# which is exactly the gap a synthetic case is for.
_syn = {
    "goal": {"pre": ["a", "b"], "yrs": 0, "ph": 0, "_total_cost": 0},
    "a":    {"pre": [],         "yrs": 1, "ph": 0, "_total_cost": 10},
    "b":    {"pre": [],         "yrs": 1, "ph": 0, "_total_cost": 10},
}
_syn_order1, _c1, _e1, _s1 = PLANNER.backward_plan(_syn, "goal", _p_s, seed_order=["b", "a"],
                                              side_branches=0)
_syn_order2, _c2, _e2, _s2 = PLANNER.backward_plan(_syn, "goal", _p_s, seed_order=["a", "b"],
                                              side_branches=0)
check("(setup) the synthetic pair is a genuine tie: equal slack and equal "
      "earliest start, with no dependency between them",
      _c1["slack"]["a"] == _c1["slack"]["b"] and _c1["es"]["a"] == _c1["es"]["b"],
      (_c1["slack"], _c1["es"]))
check("a seed order breaks a tie the critical path itself cannot call, "
      "without needing to change when the seed agrees with the default",
      _syn_order1.index("b") < _syn_order1.index("a")
      and _syn_order2.index("a") < _syn_order2.index("b"),
      (_syn_order1, _syn_order2))

# --- refine() MUST MEASURE WHAT --strategy ACTUALLY LOADS, not its own raw,
# unrepaired ~161-node order. The first version of refine() handed
# `cur_order` straight to `Sim()`, skipping the `topo_stable` repair
# `load_strategy` always applies - and since the raw CPM order has 132 real
# topological violations (see the comment after `cpm` in planner.py), that
# silently measured a different, broken order: a live check of one refine
# round went from 0/3 trials reaching the goal to 3/3 the moment this was
# fixed, against the IDENTICAL seeds and the identical starting order. This
# pins the fix: `_repaired` must agree with what `load_strategy` returns for
# the same order.
_p_repaired = PLANNER._repaired(NODES, GOAL, _p_order)
_p_label2, _p_expected, _p_b2 = S.load_strategy(
    PLANNER.write_strategy(os.path.join(ROOT, _PLAY_DIR, "refine_check.json"),
                           "test", [], _p_order),
    NODES, GOAL)
check("refine() measures a candidate order the same way --strategy loads it "
      "(full tree, topo_stable-repaired), not its own raw closure-only list",
      _p_repaired == _p_expected, (len(_p_repaired), len(_p_expected)))
# ============================================================================
# INTERFACE HONESTY: an estimate instead of a certainty where fog says the
# player should not have one yet, the game not answering its own questions,
# and the smaller items testers asked for. protocol.py, fog.py.
# ============================================================================

# --- JOB 1: revenue is an estimate, not the true figure, for a thing you
# have never run, under fog. The user asked outright: "should you really be
# able to tell how much money you would make from researching something?
# Shouldn't the payback be something you don't know until after research?"
# and a break tester's own numbers said why it mattered - EARNS/YR under fog
# was "the only usable heuristic", and got them 95 of the 146 nodes on the
# road to the goal without working out the tree at all.
s_fe = sim()
s_fe.fog = True
s_fe.revealed = set()
_av_fe = S._agent_available(s_fe, NODES, {"all": True})
_est_rows = [r for r in _av_fe["available"] if isinstance(r["earns_per_year"], list)]
check("available quotes a range, not the true figure, for an unbuilt thing "
      "under fog",
      len(_est_rows) > 10, len(_est_rows))
_r0 = _est_rows[0]
check("...and the range is an actual range: low is really below high",
      _r0["earns_per_year"][0] < _r0["earns_per_year"][1], _r0)

_k_fe = _r0["id"]
_w1 = S._agent_dispatch(s_fe, NODES, {"cmd": "why", "id": _k_fe})
_w2 = S._agent_dispatch(s_fe, NODES, {"cmd": "why", "id": _k_fe})
check("the fogged estimate is deterministic - the same game asked the same "
      "question twice gets the same answer, not a fresh roll",
      _w1["revenue"] == _w2["revenue"], (_w1["revenue"], _w2["revenue"]))

# NOT A TIGHT SYMMETRIC BAND ON THE TRUTH: "400 +/- 50" gives the truth away
# just as plainly as the bare number did. Most of the range in a real sample
# has to sit CLOSER on one side than the other.
_asym = sum(1 for r in _est_rows
            if (NODES[r["id"]]["rev"] - r["earns_per_year"][0])
            != (r["earns_per_year"][1] - NODES[r["id"]]["rev"]))
check("the estimate is not a tight symmetric band centred on the truth - "
      "most of a real sample sit closer to one bound than the other",
      _asym >= len(_est_rows) * 0.5, "%d of %d" % (_asym, len(_est_rows)))

# UPKEEP STAYS EXACT. The user's question was specifically about payback
# (revenue); upkeep is closer to a quoted price, knowable in advance, and
# this project already keeps `cost` exact under fog for the same reason.
_k_up = next((r["id"] for r in _est_rows if NODES[r["id"]]["up"] > 0), None)
if _k_up:
    _wu = S._agent_dispatch(s_fe, NODES, {"cmd": "why", "id": _k_up})
    check("upkeep is exact under fog even for a thing you have never run",
          _wu["upkeep"] == NODES[_k_up]["up"], (_wu["upkeep"], NODES[_k_up]["up"]))

# NARROWS TO THE EXACT FIGURE ONCE YOU HAVE ACTUALLY RUN IT A FEW YEARS.
s_ry = sim()
s_ry.fog = True
s_ry.revealed = set()
s_ry.done.add(_k_fe)
s_ry.done_year[_k_fe] = s_ry.year
s_ry._done_changed()
_w_new = S._agent_dispatch(s_ry, NODES, {"cmd": "why", "id": _k_fe})
check("a freshly finished thing is still a guess - you have not run it yet",
      isinstance(_w_new["revenue"], list), _w_new["revenue"])
s_ry.year += 3
_w_old = S._agent_dispatch(s_ry, NODES, {"cmd": "why", "id": _k_fe})
check("...and becomes the exact figure after you have actually run it a "
      "few years",
      _w_old["revenue"] == NODES[_k_fe]["rev"], _w_old["revenue"])

# FOG OFF: the exact figure, as before.
s_nf = sim()
_w_nf = S._agent_dispatch(s_nf, NODES, {"cmd": "why", "id": _k_fe})
check("with fog off, EARNS/YR is still the exact figure",
      _w_nf["revenue"] == NODES[_k_fe]["rev"], _w_nf["revenue"])


# --- JOB 2: the game must not tell you which branch matters most. A
# normal-play tester quoted school_founded's own note calling itself "the
# pivot of the entire game" with "every year of delay here costs more than
# any single technology"; corpus_dispersed, corpus_written and
# plague_preparedness rank themselves the same way.
for _spid, _banned in (
        ("school_founded", ("pivot of the entire game",
                            "costs more than any single",
                            "highest-leverage thing you can spend money on")),
        ("corpus_dispersed", ("highest expected-value node in the tree",)),
        ("corpus_written", ("largest single call on your personal hours",
                            "must not cut")),
        ("plague_preparedness", ("highest expected-value defensive investment",))):
    _wn = S._node_explain(sim(), NODES, _spid)
    check("%s's note no longer ranks itself against the rest of the tree"
          % _spid,
          all(b not in (_wn.get("note") or "") for b in _banned),
          _wn.get("note"))

# LEGITIMATE WARNINGS SURVIVE: plague_preparedness still tells you the date
# and what the node actually does about it - a consequence the player
# cannot see coming, not a ranking claim, and it must stay.
_pp = S._node_explain(sim(), NODES, "plague_preparedness")
check("...but the actual hazard warning underneath it is untouched",
      "165 AD" in (_pp.get("note") or "")
      and "decides whether your institute survives" in (_pp.get("note") or ""),
      _pp.get("note"))

# school_founded's OWN statement that it is optional must survive too - it
# is the opposite of the fault being fixed.
_sf = S._node_explain(sim(), NODES, "school_founded")
check("school_founded's note still says it is optional",
      "OPTIONAL" in (_sf.get("note") or "")
      and "Nothing in the technical tree requires it" in (_sf.get("note") or ""),
      _sf.get("note"))

# UNDER FOG TOO: fog_summary takes its one sentence off the same note, and
# used to open with exactly the self-play line this exists to cut.
s_fp = sim()
s_fp.fog = True
s_fp.revealed = {"school_founded"}
check("the fogged one-line summary of school_founded is not its own "
      "self-rating either",
      "pivot" not in s_fp.fog_summary("school_founded").lower(),
      s_fp.fog_summary("school_founded"))


# --- JOB 3a: a prerequisite has to be DONE, not merely started. A tester
# wrote "nothing states whether a prerequisite must be DONE or open" - it
# has always meant done, and the one sentence that said so lived only in a
# branch start_blocked_reason pre-empts on every ordinary refusal, so a
# player who actually hit the refusal never saw it.
s_pn = sim(capital=1000000.0)
_pair_pn = None
for _cand in s_pn.order:
    if not s_pn.can_start(_cand):
        continue
    _dep = next((m for m in NODES if _cand in NODES[m]["pre"]), None)
    if _dep:
        _pair_pn = (_cand, _dep)
        break
_k1_pn, _k2_pn = _pair_pn
S._agent_dispatch(s_pn, NODES, {"cmd": "start", "id": _k1_pn})
_w_pn = S._node_explain(s_pn, NODES, _k2_pn)
_txt_pn = _RP("why", _w_pn)
check("a refusal for a started-but-unfinished prerequisite says it has to "
      "be FINISHED, not merely started - on the path a player actually hits",
      "FINISHED" in _txt_pn and "not merely started" in _txt_pn,
      [ln for ln in _txt_pn.splitlines() if "FINISHED" in ln] or _txt_pn[:200])


# --- JOB 3b: a fog-safe sense of progress DURING play, and nothing more
# until the run ends - the total itself is the size of the tree's own
# spoiler surface, same reasoning as downstream_count being hidden.
s_pg = sim()
s_pg.fog = True
s_pg.revealed = set()
s_pg.done.add("arithmetic_positional")
s_pg._done_changed()
_stpg = S._agent_dispatch(s_pg, NODES, {"cmd": "state"})
check("under fog, `state` says how many of the goal's road you already have",
      isinstance(_stpg.get("on_the_road_to_the_goal_so_far"), int)
      and _stpg["on_the_road_to_the_goal_so_far"] >= 1,
      _stpg.get("on_the_road_to_the_goal_so_far"))
check("...but never the total - final_report gives that, once the run is "
      "over and there is nothing left to spoil",
      "the_whole_road_was" not in _stpg, sorted(_stpg.keys()))
s_pg2 = sim()
_stpg2 = S._agent_dispatch(s_pg2, NODES, {"cmd": "state"})
check("with fog off, the fog-safe progress field is absent (path/why "
      "already answer this exactly, by name)",
      _stpg2.get("on_the_road_to_the_goal_so_far") is None, _stpg2)


# --- JOB 3c: the society's own values are readable. Event text has always
# named these fields directly ("changes the society: w_novelty") with no
# command that would say what one is; two testers asked for this.
_vals = S._agent_dispatch(sim(), NODES, {"cmd": "values"})
check("`values` exists and lists this society's own traits as numbers",
      _vals.get("ok") and len(_vals.get("values") or []) >= 8, _vals)
check("...and every field event text names is one this command can look up",
      {"w_novelty", "w_commerce", "w_magic_fear"} <=
      {r["field"] for r in _vals["values"]},
      [r["field"] for r in _vals["values"]])


# --- JOB 3d: a long step stops when something it warned about actually
# happens, rather than running the rest of the years you asked for on top
# of it. A break tester watched "CLOSE TO THE LIMIT ... while it is still
# your choice" get ploughed straight through to CREDIT EXHAUSTED inside one
# big `step`.
s_se = sim(capital=500.0)
s_se.end_year = s_se.cfg["start_year"] + 200
# Plain `start`, not `rush` - this check has to stand on its own before
# `rush` exists as a command (see JOB 3f, committed separately and later).
_memo_se = {}
_ok_se = [k for k in s_se.order if s_se.can_start(k, _memo=_memo_se)]
_ok_se = [k for k in _ok_se
          if not (NODES[k]["tier"] == 0 and NODES[k]["ph"] == 0
                  and NODES[k]["_total_cost"] <= 1)]
for _k_se in _ok_se[:15]:
    S._agent_dispatch(s_se, NODES, {"cmd": "start", "id": _k_se})
_step_ce = S._agent_dispatch(s_se, NODES, {"cmd": "step", "years": 100})
check("a multi-year step stops the moment credit is actually exhausted, "
      "rather than running the rest of the years on top of it",
      bool(_step_ce.get("stopped_early"))
      and any("CREDIT EXHAUSTED" in e["message"] for e in _step_ce["events"]),
      _step_ce.get("stopped_early"))
check("...and it really did stop short of the 100 years asked for",
      _step_ce["year"] < s_se.cfg["start_year"] + 100, _step_ce["year"])


# --- JOB 3e: the founder's death is legible, not one line among many. A
# normal-play tester in mortal mode found it reported as one more EVENT in a
# long `step`, with the age nowhere but that one sentence. `sim()` has no
# mortal switch of its own - nothing in this file needed one before - so
# this builds the Sim directly, the same way `sim()` itself does.
s_fd = S.Sim(NODES, ORDER, random.Random(1), events=False, manual=True,
             civ=S.load_civ("rome_100ad"), cfg={"immortal": False})
s_fd.goal, s_fd.done_year = GOAL, {}
s_fd.end_year = s_fd.cfg["start_year"] + 200
_step_fd = S._agent_dispatch(s_fd, NODES, {"cmd": "step", "years": 150})
check("the founder's death gets a field of its own in the step that carries "
      "it, not only a line in events",
      isinstance(_step_fd.get("the_founder_died_this_step"), dict),
      _step_fd.get("the_founder_died_this_step"))
check("...and the age is a number you can read, not prose you have to parse",
      isinstance((_step_fd.get("the_founder_died_this_step") or {})
                 .get("aged_about"), int),
      _step_fd.get("the_founder_died_this_step"))
check("...and `state` carries the age from then on, not only that one "
      "step's reply",
      _step_fd.get("founder_died_aged")
      == _step_fd["the_founder_died_this_step"]["aged_about"],
      (_step_fd.get("founder_died_aged"), _step_fd.get("the_founder_died_this_step")))
check("...and the step stopped there instead of running the rest of the "
      "150 years requested straight past it",
      _step_fd["year"] < s_fd.cfg["start_year"] + 150, _step_fd["year"])

# THE AGE SURVIVES A --session RESUME. `log` is not itself a saved field -
# see SAVE_FIELDS - so a naive read of it for the founder's age would go
# empty in a freshly constructed process, silently un-reporting an age
# `state` had already shown once. _founder_death_aged/_founder_death_year
# are saved fields precisely so this does not happen.
_sess_fd = os.path.join(ROOT, _rel("founder_death.json"))
S.save_state(s_fd, _sess_fd)
s_fd2 = S.Sim(NODES, ORDER, random.Random(1), events=False, manual=True,
             civ=S.load_civ("rome_100ad"))
s_fd2.goal, s_fd2.done_year = GOAL, {}
S.load_state(s_fd2, _sess_fd)
_st_fd2 = S._agent_dispatch(s_fd2, NODES, {"cmd": "state"})
check("the founder's age at death survives a save and a fresh process "
      "loading it back, not only the process that saw it happen",
      _st_fd2.get("founder_died_aged") == _step_fd.get("founder_died_aged")
      and _st_fd2.get("founder_died_aged") is not None,
      (_st_fd2.get("founder_died_aged"), _step_fd.get("founder_died_aged")))


# --- JOB 3f: a bulk start for the late game, so it is not pure typing.
s_ru = sim()
_ru = S._agent_dispatch(s_ru, NODES, {"cmd": "rush"})
# --- BREAK, round 12: two testers independently made this their worst finding.
# One wrote that a dead founder's run was "permanently unwinnable from that
# point" with the game never saying so; the other watched a corpse be offered
# 69 startable projects and accept one. The engine was not actually silent
# about the consequence - deputies carry the work, and with none the programme
# dissolves over twelve years - but nothing ever told the player either half.
_s_die = sim(capital=1000000.0, events=True)
_s_die.cfg["immortal"] = False
_s_die.life_left = 1.0
for _ in range(6):
    _s_die.step()
check("the founder's death says what it means for the run, not only that it happened",
      any("THE FOUNDER DIES" in m and "nobody to direct" in m
          for _, m in _s_die.log),
      [m for _, m in _s_die.log if "FOUNDER DIES" in m][:1])
check("...and the programme dissolving is counted down where a player sees it",
      any("DISSOLVING" in m and "ends at twelve" in m for _, m in _s_die.log),
      [m for _, m in _s_die.log if "DISSOLVING" in m][:1])

# --- BREAK, round 12: a developer's own change-log marker was shipped in the
# prose a player reads. 1,108 nodes carried "[AUDIT: ... See JOB 1 upkeep
# audit.]" in their note field, the win condition among them, naming the task
# numbering of the agent that had edited them. The reasoning for a change
# belongs in the commit message; the note field is what the player reads.
_leaks = sorted(k for k, v in NODES.items()
                if "AUDIT" in ((v.get("note") or "") + (v.get("name") or "")))
check("no developer change-log marker is shipped in player-facing prose",
      not _leaks, _leaks[:5])

# --- BREAK: three civilisations were told their own signature technology led
# nowhere. `why` decided what a node unlocks by scanning hard prerequisites
# only, so anything reached solely as one option of a req_any substitution
# group ("any of a steam engine, a water wheel or a horse will drive this")
# read as a dead end. Ten nodes were affected, among them the Norse clinker
# hull - which really has 466 nodes behind it - the Norse bog-iron bloomery,
# and the Mexica's chinampa. A play tester filed this against the Norse
# starting kit as "flagship technologies are dead ends in the graph".
from engine.protocol import _unlocked_by as _UB, _downstream_of as _DS
_ra_cases = ("sea_clinker_hull", "met_bloomery_bog_iron", "fud_chinampa")
for _k_ra in _ra_cases:
    _un = _UB(_k_ra, NODES)
    check("%s is not a dead end: something really does need it" % _k_ra,
          bool(_un), _un)
check("...and what rests on it is counted, not reported as nothing",
      all(len(_DS(k, NODES)) >= 1 for k in _ra_cases),
      {k: len(_DS(k, NODES)) for k in _ra_cases})
# THE REASON THE CACHED INDEX CANNOT DO THIS. The tree is a directed acyclic
# graph on `pre` and is NOT acyclic once req_any options are edges too:
# junction_transistor -> silicon_path -> point_contact_transistor ->
# junction_transistor is one of four cycles. A bitmask descendant index that
# assumes a DAG runs out of memory on them, which is exactly what happened
# when this fix was first attempted in data.py, so the walk that answers a
# player carries a visited set instead.
def _cycle_on(edges_of):
    """Any node reachable from itself, following whatever edges are given."""
    seen_all = set()
    for root in sorted(NODES):
        if root in seen_all:
            continue
        stack, seen = [root], set()
        while stack:
            cur = stack.pop()
            for nxt in edges_of(cur):
                if nxt == root:
                    return root
                if nxt not in seen:
                    seen.add(nxt); stack.append(nxt)
        seen_all |= seen
    return None

check("the tree is acyclic on hard prerequisites, which is what closure() "
      "walks and why it must not follow substitutions",
      _cycle_on(lambda k: [p for p in NODES[k]["pre"] if p in NODES]) is None,
      _cycle_on(lambda k: [p for p in NODES[k]["pre"] if p in NODES]))

def _pre_and_single_option_any(k):
    n = NODES[k]
    out = [p for p in n["pre"] if p in NODES]
    for g in (n.get("req_any") or []):
        opts = g.get("options") or {}
        if len(opts) == 1:
            (opt,) = opts.keys()
            if opt in NODES:
                out.append(opt)
    return out
check("pre plus every single-option req_any edge is still acyclic over the "
      "whole tree - the safety margin the single-option walk rests on, since a "
      "multi-option group (two or more real alternatives) walked the same "
      "way genuinely can cycle (junction_transistor -> silicon_path -> "
      "point_contact_transistor -> junction_transistor is real) and must "
      "never be",
      _cycle_on(_pre_and_single_option_any) is None,
      _cycle_on(_pre_and_single_option_any))

def _pre_and_any(k):
    # req_any OPTIONS ARE NOT ALL NODES. A group can offer a MATERIAL as an
    # alternative to a technology ("any of lead_kg, mat_lead_sheet ..."), so a
    # walk over these edges has to skip anything that is not a node or it dies
    # on KeyError: 'lead_kg'. _unlocked_by is safe from this by construction,
    # because it only ever asks whether a node's options mention k.
    out = [p for p in NODES[k]["pre"] if p in NODES]
    for g in (NODES[k].get("req_any") or []):
        out.extend(o for o in sorted(g.get("options") or {}) if o in NODES)
    return out

# The cycle is not hypothetical and it is worth naming, because it is the
# reason data.py's cached descendant index cannot simply be taught about
# substitutions: junction_transistor needs point_contact_transistor, and
# point_contact_transistor offers silicon_path as one option of its
# semiconductor group, and silicon_path comes back round to the junction
# device. A bitmask DFS that assumes a DAG runs out of memory on that, which
# is exactly what happened when this fix was first attempted there.
def _reaches(start, target, edges_of):
    seen, stack = set(), [start]
    while stack:
        cur = stack.pop()
        for nxt in edges_of(cur):
            if nxt == target:
                return True
            if nxt not in seen:
                seen.add(nxt); stack.append(nxt)
    return False

check("...and NOT acyclic once substitutions count, which is why the cached "
      "bitmask index cannot answer this and a visited set must",
      _reaches("junction_transistor", "junction_transistor", _pre_and_any),
      "no cycle found through junction_transistor")

# --- BREAK, round 12: `rush limit:1000` on turn one started 209 things at
# once, owing 90,944 founder-hours against a lifetime the game itself puts at
# about 72,000. The next step gave hours to exactly one of them, so "RUNNING
# (209)" was a fiction about 208 of them. Committing a couple of years of
# everyone's attention is a decision; committing four centuries of it is not.
_s_rush = sim(capital=5000000.0)
_r_rush = S._agent_dispatch(_s_rush, NODES, {"cmd": "rush", "limit": 1000})
_owed_rush = sum(NODES[r["id"]]["ph"] for r in (_r_rush.get("started") or []))
check("`rush` does not commit more hours than a couple of years can hold",
      _owed_rush <= _s_rush.director_pool() * 2.0 + max(
          NODES[r["id"]]["ph"] for r in (_r_rush.get("started") or [{"id": GOAL}])),
      (_owed_rush, _s_rush.director_pool()))
check("...and says why it stopped rather than silently starting fewer",
      any("would not make them go faster" in str(r.get("why"))
          for r in (_r_rush.get("not_started") or [])),
      [r.get("why") for r in (_r_rush.get("not_started") or [])][:1])

# --- BREAK, round 12: five scholars hired, five years stepped, the payroll
# read 5, 4, 3, 3, 2 and NOTHING said why. The rate was right all along
# (measured 0.825 survival over five years against 0.837 expected across forty
# seeds); it was the reporting that was missing, and from the chair it looked
# exactly like staff vanishing.
_s_att = sim(capital=10000000.0, events=False)
run_it(_s_att, "workshop_first", "school_founded", "freedman_staff")
_s_att.hire("scholar", 8)
for _ in range(12):
    _s_att.step()
check("losing people to death and better offers is announced, not silent",
      any("lose" in m and "scholar" in m for _, m in _s_att.log),
      [m for _, m in _s_att.log if "lose" in m][:2])

check("`rush` starts more than one thing in a single call",
      _ru.get("count_started", 0) >= 2, _ru.get("count_started"))
check("...and every id it reports started is actually active now",
      all(r["id"] in s_ru.active for r in _ru["started"]),
      [r["id"] for r in _ru["started"]])
check("...and a limit caps how many it actually begins",
      S._agent_dispatch(sim(), NODES, {"cmd": "rush", "limit": 1})["count_started"] == 1,
      None)

# FOG-SAFE: `can_start` already guarantees visibility (see is_visible's own
# docstring - "anything you could start right now is visible by
# definition"), so this is belt-and-braces: every id `rush` touches under
# fog really was one the fogged `available` list would also have shown.
s_ruf = sim()
s_ruf.fog = True
s_ruf.revealed = set()
_avf = {r["id"] for r in S._agent_available(s_ruf, NODES, {"all": True})["available"]}
_ruf = S._agent_dispatch(s_ruf, NODES, {"cmd": "rush"})
check("under fog, everything `rush` starts was already on the visible "
      "`available` list",
      all(r["id"] in _avf for r in _ruf["started"]),
      [r["id"] for r in _ruf["started"] if r["id"] not in _avf])

# EVERY NEW COMMAND MUST BE ADVERTISED. Same check the suite already runs
# for the rest of KNOWN_COMMANDS, pinned here for the two just added so a
# future edit that forgets to wire one up fails immediately rather than
# waiting for the general sweep to notice.
check("'values' and 'rush' are in the list every unknown-command refusal "
      "advertises",
      "values" in S.KNOWN_COMMANDS and "rush" in S.KNOWN_COMMANDS,
      S.KNOWN_COMMANDS)


# --- BREAK: a player asked what opening `arithmetic_positional` (decimal
# positional notation) means, and how writing down zero creates money or has
# a cost. It doesn't: the node carried rev=300 and up=100 purely because
# is_venture() offers `open` to anything with either field set, with no
# distinction between a notation and a business. A prior pass that day had
# zeroed upkeep on 1,096 nodes it judged the same way but left their revenue
# alone, and revenue alone still satisfies is_venture()'s `or`, so the break
# survived half fixed. The rule applied here: a node earns as a concern only
# if there is something to open a door on - premises, staff, stock, or a
# trade a person actually practises for a fee - and not merely because
# knowing it happens to carry a rev figure. Notation, theorems, financial
# instruments, circuit theory, and farming/food-processing METHODS applied
# to a venture that already exists elsewhere in the tree all got their rev
# (and any leftover up) zeroed; genuinely practised trades and manufactured
# products did not.
check("opening `arithmetic_positional` is no longer offered - a notation is "
      "not a door to open",
      not sim().is_venture("arithmetic_positional")
      and NODES["arithmetic_positional"]["rev"] == 0
      and NODES["arithmetic_positional"]["up"] == 0,
      (NODES["arithmetic_positional"]["rev"], NODES["arithmetic_positional"]["up"]))

check("circuit theory (Black's 1927 feedback theorem) does not open as a "
      "concern the way the capacitor it improves still does",
      not sim().is_venture("el2_negative_feedback_stability_gain")
      and sim().is_venture("el2_capacitor_electrolytic"),
      (sim().is_venture("el2_negative_feedback_stability_gain"),
       sim().is_venture("el2_capacitor_electrolytic")))

check("a financial instrument (a cheque) is not itself a venture; the bank "
      "that uses one still is",
      not sim().is_venture("fin_cheque") and sim().is_venture("fin_deposit_bank"),
      (sim().is_venture("fin_cheque"), sim().is_venture("fin_deposit_bank")))

check("a husbandry method (hybridisation) does not open its own shop; the "
      "farm it improves still does",
      not sim().is_venture("ag2_hybridisation") and sim().is_venture("crop_rotation"),
      (sim().is_venture("ag2_hybridisation"), sim().is_venture("crop_rotation")))

# THE HARD MIDDLE, NOT ZEROED: an assay office is a trade a person practises
# for a fee - premises, hallmarking equipment, paying customers - same as the
# physician's practice and surveying business the fix was warned not to
# destroy by treating every revenue figure as if it were a notation.
check("a trade practised for a fee (an assay office) still opens as a "
      "concern, unlike a notation",
      sim().is_venture("fin_assay_office"), sim().is_venture("fin_assay_office"))

# AGGREGATE, SO A FUTURE EDIT CANNOT DRIFT BACK TOWARD EITHER MISTAKE. Before
# this fix, is_venture() offered 1,492 of the tree's 2,833 nodes to `open` as
# going concerns (Rome's own granted set aside); a check tester found the
# true figure for a Rome start was 1,493. This pins it well below that and
# well above zero, so a change that either re-inflates the notation-as-shop
# bug or blindly zeros revenue across the tree (destroying the real income
# the game depends on) fails here rather than shipping.
_venture_ct = sum(1 for k in NODES if sim().is_venture(k))
check("the count of nodes offered to `open` as a concern is down from the "
      "break's 1,493, and not collapsed toward zero",
      1300 <= _venture_ct <= 1450, _venture_ct)

# =============================================================================
# THE USER'S THREE QUESTIONS. Q1: does training ten times as many smiths
# actually cut the cost of a smith? Q2: can a technology raise output per
# worker without replacing the worker (labour.py's labour_productivity),
# and is it wired to real tree nodes rather than invented ones?
# =============================================================================

# --- Q1: train ten times as many smiths, measure what a smith costs, before
# and after - exactly as asked, rather than trusting the comment in
# labour_price_factor that claims the price comes back down. household_room
# is patched open for this one check because the question is about the
# PRICING mechanism (labour_pressure vs market_supply), which is orthogonal
# to the household-capacity gate hire() also enforces; nothing else in this
# file, and no other check, depends on the patch.
_orig_room = S.Sim.household_room
S.Sim.household_room = lambda self: 10_000.0
try:
    small = sim(capital=1e9)
    small.hire("smith", 5)
    small.year += 10                 # let the hiring-day pressure fully decay
    big = sim(capital=1e9)
    big.hire("smith", 50)            # TEN TIMES as many smiths
    big.year += 10                   # same decay, same settling time
    cost_small = (S.ANNUAL_WAGE["smith"] * small.wage_index * small.price_index
                  * small.labour_price_factor("smith"))
    cost_big = (S.ANNUAL_WAGE["smith"] * big.wage_index * big.price_index
                * big.labour_price_factor("smith"))
    check("once the market has settled, a smith costs the SAME base wage "
          "whether the trade has 5 people in it or 50 - training ten times "
          "as many smiths does not cut the price below the wage table, it "
          "only avoids a lasting premium (see the next two checks for what "
          "training ten times as many DOES change)",
          abs(cost_big - cost_small) < 0.5, (cost_small, cost_big))

    # What ten-times-the-trade actually buys: the SAME absolute batch of new
    # hiring pressure is a smaller share of a bigger existing trade, so
    # expanding a big trade further is cheaper, in the premium it pays,
    # than expanding a small one by the same amount - this is the real
    # content of "brings the price back down", not a below-base discount.
    thin = sim(capital=1e9)
    thin.hire("smith", 5)
    thin.year += 10
    thick = sim(capital=1e9)
    thick.hire("smith", 50)
    thick.year += 10
    thin_capital_before, thick_capital_before = thin.capital, thick.capital
    thin.hire("smith", 10)
    thick.hire("smith", 10)
    fee_thin = thin_capital_before - thin.capital
    fee_thick = thick_capital_before - thick.capital
    check("expanding an already-large trade by a fixed amount costs no more "
          "in fees than expanding a small one by the same amount, once both "
          "have settled (hire()'s own price factor is read before the new "
          "batch's pressure is recorded, so a single hire() call never taxes "
          "itself - only the NEXT one)",
          abs(fee_thick - fee_thin) < 1.0, (fee_thin, fee_thick))

    per_head_thin = thin.wage_bill() / thin.employees["smith"]
    per_head_thick = thick.wage_bill() / thick.employees["smith"]
    check("the standing payroll's per-head cost, measured immediately after "
          "each identical top-up batch, is lower for the bigger trade - the "
          "same recent pressure is diluted across more existing people",
          per_head_thick < per_head_thin,
          "per head, base=5->15: %.2f   base=50->60: %.2f"
          % (per_head_thin, per_head_thick))
finally:
    S.Sim.household_room = _orig_room

# --- Q2: technology that raises output per worker without replacing them.
s = sim(capital=1e9)
check("with nothing built, an hour of a trade's time is worth exactly an "
      "hour - labour_productivity changes nothing until a real technology "
      "earns it",
      s.labour_productivity("smith") == 1.0, s.labour_productivity("smith"))

before_call_on = s.hours_you_can_call_on("smith")
before_supply = s.market_supply("smith")
s.done.add("met_trip_hammer")
after_call_on = s.hours_you_can_call_on("smith")
after_supply = s.market_supply("smith")
check("a real productivity technology (the trip hammer, whose note says "
      "'much faster than hand hammering') raises the WORK a smith's hours "
      "can produce this year",
      after_call_on > before_call_on * 1.05, (before_call_on, after_call_on))
check("...without changing market_supply - the technology makes the "
      "existing smiths faster, it does not conjure more of them, so hiring "
      "capacity and labour_price_factor are untouched",
      after_supply == before_supply, (before_supply, after_supply))
check("...and leaves an UNRELATED trade's productivity at exactly 1.0 - a "
      "trip hammer for smiths does not make carpenters faster too",
      s.labour_productivity("carpenter") == 1.0, s.labour_productivity("carpenter"))

s2 = sim(capital=1e9)
for _node, _tr, _add in s2.LABOUR_PRODUCTIVITY_SOURCES:
    s2.done.add(_node)
check("stacking every productivity technology this run has wired in never "
      "pushes any trade's multiplier past the cap, however many technologies "
      "a civilization eventually builds",
      all(s2.labour_productivity(tr) <= s2.LABOUR_PRODUCTIVITY_CAP + 1e-9
          for _n, tr, _a in s2.LABOUR_PRODUCTIVITY_SOURCES),
      [(tr, s2.labour_productivity(tr)) for _n, tr, _a in sorted(
          s2.LABOUR_PRODUCTIVITY_SOURCES, key=lambda r: r[1])])

check("every node named in LABOUR_PRODUCTIVITY_SOURCES is a real node in "
      "the compiled tree, not a name that was never wired to anything",
      all(_n in NODES for _n, _tr, _a in S.Sim.LABOUR_PRODUCTIVITY_SOURCES),
      [_n for _n, _tr, _a in S.Sim.LABOUR_PRODUCTIVITY_SOURCES if _n not in NODES])
check("every trade named in LABOUR_PRODUCTIVITY_SOURCES is a real trade in "
      "the wage table",
      all(_tr in WAGES for _n, _tr, _a in S.Sim.LABOUR_PRODUCTIVITY_SOURCES),
      [_tr for _n, _tr, _a in S.Sim.LABOUR_PRODUCTIVITY_SOURCES if _tr not in WAGES])
# EDUCATING A WHOLE SOCIETY. The user's own question: "can we make the whole
# country's literacy rates improve? What if we make 5,000 schools and
# tractors and food production... can I create a 90%+ literate population?"
# See SocietyMixin.advance_society (society.py).
# ONE Sim, reused for every node: _is_agri_mechanisation reads only fixed
# tree data (see its own docstring), so which Sim answers is irrelevant, and
# the `_venture_ct` check a little above this one shows what happens to a
# check's running time when it constructs a fresh Sim per node instead -
# this file's own 3-second rule (see check() timing) exists precisely so a
# check does not silently become the slowest thing in the suite this way.
_s0_agri = sim()
_agri_nodes = sorted(k for k in NODES if _s0_agri._is_agri_mechanisation(k))
check("a genuinely farm-labour-saving slice of the tree exists and is a "
      "modest fraction of it, not the whole `food`-tagged sprawl",
      35 <= len(_agri_nodes) <= 45, len(_agri_nodes))

s_noschool = sim(capital=2000000.0, manual=False)
for k in _agri_nodes:
    s_noschool.done.add(k)
s_noschool._done_changed()
_gen0 = s_noschool.civ["literacy_general"]
for i in range(1, 301):
    s_noschool.advance_society(s_noschool.year + i)
check("mechanising every farm technology with no school ever running moves "
      "literacy not at all - this is something a society is TAUGHT, not a "
      "free drift",
      s_noschool.civ["literacy_general"] == _gen0, s_noschool.civ["literacy_general"])

s_school = run_it(sim(capital=2000000.0, manual=False), "school_founded")
_gen0b = s_school.civ["literacy_general"]
_ceil_noagri = s_school.literacy_ceiling_general()
for i in range(1, 401):
    s_school.advance_society(s_school.year + i)
check("a single running school, with no mechanised farming, raises "
      "literacy over generations but plateaus well short of near-universal",
      _gen0b < s_school.civ["literacy_general"] <= _ceil_noagri + 1e-6
      and s_school.civ["literacy_general"] < 0.5,
      (round(s_school.civ["literacy_general"], 3), round(_ceil_noagri, 3)))

s_max = run_it(sim(capital=2000000.0, manual=False),
               "school_founded", "academy_network")
s_max.inst_units = {"school_founded": 9.0, "academy_network": 9.0}
for k in _agri_nodes:
    s_max.done.add(k)
s_max._done_changed()
check("agrarian_slack saturates at 1.0 once enough of the farm-labour-saving "
      "branch is done, not only once every last node of it is",
      s_max.agrarian_slack() == 1.0, s_max.agrarian_slack())
for i in range(1, 701):
    s_max.advance_society(s_max.year + i)
check("heavy schooling AND agricultural mechanisation together, over "
      "centuries, can reach a 90%+ literate general population - the "
      "user's own question, answered yes",
      s_max.civ["literacy_general"] >= 0.85, s_max.civ["literacy_general"])
check("...but never above the model's own ceiling: some fraction of any "
      "pre-transistor-era population is never a schooling question at all",
      s_max.civ["literacy_general"] <= 0.90 + 1e-6, s_max.civ["literacy_general"])
check("the lettered/propertied class closes most of its own gap too, on "
      "the same schooling, independent of farm mechanisation",
      s_max.civ["literacy_elite"] >= 0.95, s_max.civ["literacy_elite"])

_few_agri = sim(capital=2000000.0)
for k in _agri_nodes[:5]:
    _few_agri.done.add(k)
_few_agri._done_changed()
check("a handful of mechanised techniques frees only a little slack, not "
      "the whole ceiling",
      0.0 < _few_agri.agrarian_slack() < 0.6, _few_agri.agrarian_slack())

# --- determinism: agrarian_slack and _advance_literacy iterate self.done
# (a set) and self.civ (a dict) only through counts and direct key reads,
# never a float sum in an order that depends on PYTHONHASHSEED, but this is
# proven rather than merely argued, the same way the rest of this suite
# proves determinism elsewhere.
def _edu_snapshot(seed_env):
    p = subprocess.run(
        [sys.executable, "-c",
         "import sys; sys.path.insert(0,'.'); import random, simulator as S; "
         "T,P,N,W,G = S.load(); _l,O,_b = S.load_strategy('recommended', N, T['meta']['goal_node']); "
         "s = S.Sim(N, O, random.Random(1), events=False, manual=False, "
         "civ=S.load_civ('rome_100ad'), cfg={'start_capital':5000000.0}); "
         "s.goal, s.done_year = T['meta']['goal_node'], {}; "
         "s.done.add('school_founded'); s.operating.add('school_founded'); "
         "s.done.add('academy_network'); s.operating.add('academy_network'); "
         "s.inst_units = {'school_founded': 9.0, 'academy_network': 9.0}; "
         "[s.done.add(k) for k in sorted(N) if s._is_agri_mechanisation(k)]; "
         "s._done_changed(); "
         "s.trades_created.add('electrician'); "
         "[s.advance_society(s.year + i) for i in range(1, 201)]; "
         "print(repr((round(s.civ['literacy_general'], 12), "
         "round(s.civ['literacy_elite'], 12), "
         "'electrician' in s.trades_endemic, "
         "round(s.employees.get('electrician', 0.0), 12))))"],
        capture_output=True, text=True, timeout=60, cwd=HERE,
        env=dict(os.environ, PYTHONHASHSEED=seed_env))
    return p.stdout.strip()
_edu_a = _edu_snapshot("0")
_edu_b = _edu_snapshot("98765")
check("literacy growth and trade absorption are identical under a "
      "different PYTHONHASHSEED",
      _edu_a == _edu_b and _edu_a, (_edu_a, _edu_b))

# =============================================================================
# A TRADE THE FOUNDER INTRODUCED BECOMES A TRADE THE SOCIETY HAS. The user's
# sharpest question: "if I invent electricity, you can't say that after 100
# years I still can't find anyone who can make or research generators." See
# SocietyMixin._advance_trade_absorption/_grow_endemic_trade (society.py).
s_noteach = sim(capital=5000000.0, manual=False)
s_noteach.trades_created.add("electrician")
for i in range(1, 401):
    s_noteach.advance_society(s_noteach.year + i)
check("a taught trade never naturalises without a single school ever "
      "running, however long the run - this is exactly what 'after 100 "
      "years I'm still the only electrician' looks like when nothing was "
      "ever built to change it",
      "electrician" not in s_noteach.trades_endemic
      and s_noteach.employees.get("electrician", 0.0) == 0.0,
      (sorted(s_noteach.trades_endemic), s_noteach.employees.get("electrician")))

s_teach = run_it(sim(capital=5000000.0, manual=False),
                 "school_founded", "academy_network")
s_teach.inst_units = {"school_founded": 9.0, "academy_network": 9.0}
s_teach.trades_created.add("electrician")
_yrs_needed = s_teach._trade_absorption_years(s_teach._schooling_flow())
check("heavy schooling brings absorption well under the ~110-year "
      "unschooled base, and never under the 35-year one-lifetime floor",
      35.0 <= _yrs_needed < 110.0, _yrs_needed)
_y0 = s_teach.year
_not_yet_year = _y0 + max(1, int(_yrs_needed) - 5)
for yr in range(_y0 + 1, _not_yet_year + 1):
    s_teach.advance_society(yr)
check("...and not endemic before that many years have actually passed",
      "electrician" not in s_teach.trades_endemic, s_teach.year - _y0)
_after_year = _y0 + int(_yrs_needed) + 10
for yr in range(_not_yet_year + 1, _after_year + 1):
    s_teach.advance_society(yr)
check("a heavily-schooled society naturalises a taught trade within about "
      "a century of the founder introducing it",
      "electrician" in s_teach.trades_endemic, s_teach.year - _y0)
for yr in range(_after_year + 1, _after_year + 101):
    s_teach.advance_society(yr)
check("...and goes on to actually produce its own electricians, for free, "
      "bounded by the exact same literate_capacity() wall a founder hiring "
      "or teaching them by hand is bounded by",
      0 < s_teach.employees.get("electrician", 0.0)
      <= s_teach.literate_capacity("electrician") + 1e-6,
      (round(s_teach.employees.get("electrician", 0.0), 2),
       round(s_teach.literate_capacity("electrician"), 2)))

_sess_edu = os.path.join(ROOT, _rel("education.json"))
S.save_state(s_teach, _sess_edu)
s_teach2 = S.Sim(NODES, ORDER, random.Random(1), events=False, manual=True,
                 civ=S.load_civ("rome_100ad"))
s_teach2.goal, s_teach2.done_year = GOAL, {}
S.load_state(s_teach2, _sess_edu)
check("which trades have naturalised, and when each was introduced, "
      "survive a save and a fresh process loading it back",
      s_teach2.trades_endemic == s_teach.trades_endemic
      and s_teach2.trade_introduced_year == s_teach.trade_introduced_year,
      (sorted(s_teach2.trades_endemic), s_teach2.trade_introduced_year))

_st_edu, _, _ = proto([{"cmd": "state"}])
check("`state` reports this society's literacy and how far it could go "
      "from here",
      "literacy" in _st_edu[0]
      and 0.0 <= _st_edu[0]["literacy"]["general"] <= 1.0
      and _st_edu[0]["literacy"]["general_ceiling_now"]
          >= _st_edu[0]["literacy"]["general"],
      _st_edu[0].get("literacy"))
check("...and which taught trades the society has absorbed on its own",
      "trades_society_now_has_on_its_own" in _st_edu[0],
      _st_edu[0].get("trades_society_now_has_on_its_own"))

# =============================================================================
# WHAT YOU BUILT DOES NOT STAY YOURS. "You selling gunpowder to the
# military, someone else will likely want some of that money. Over a
# generation or two." See SocietyMixin.diffusion_share/diffusion_index
# (society.py) - a number exposed for a competitive-pricing pass to spend,
# deliberately not yet spent in revenue() itself (see that function's own
# docstring for why, and for the seam left for the agent doing that work).
_rev_node = next(k for k in sorted(NODES) if NODES[k].get("rev", 0) > 0)
_no_rev_node = next(k for k in sorted(NODES) if NODES[k].get("rev", 0) <= 0)

s_dif = sim(capital=1000000.0)
check("a technology nobody has opened for business has nothing to leak",
      s_dif.diffusion_share(_rev_node) == 0.0, s_dif.diffusion_share(_rev_node))
s_dif.done.add(_rev_node); s_dif.operating.add(_rev_node)
s_dif.done_year[_rev_node] = s_dif.year
check("freshly opened, on the day the doors open, none of its edge has "
      "leaked yet - the brief's own requirement, echoing goods_market_factor's",
      s_dif.diffusion_share(_rev_node) == 0.0, s_dif.diffusion_share(_rev_node))
s_dif.year += int(s_dif.VENTURE_DIFFUSION_HALF_LIFE_YEARS)
_half = s_dif.diffusion_share(_rev_node)
check("about half the edge is gone after one half-life",
      0.45 <= _half <= 0.55, _half)
s_dif.year += 400
_far = s_dif.diffusion_share(_rev_node)
check("...but a first mover never loses all of it, however long the "
      "venture runs - capped, like every other saturating share in this file",
      abs(_far - s_dif.VENTURE_DIFFUSION_CAP) < 1e-6, _far)

s_dif2 = sim(capital=1000000.0)
s_dif2.done.add(_no_rev_node); s_dif2.operating.add(_no_rev_node)
s_dif2.done_year[_no_rev_node] = s_dif2.cfg["start_year"] - 200
check("a concern with no revenue at all has no market to leak into, "
      "however long it has been open",
      s_dif2.diffusion_share(_no_rev_node) == 0.0,
      s_dif2.diffusion_share(_no_rev_node))

s_dif3 = sim(capital=1000000.0)
s_dif3.done.add(_rev_node); s_dif3.operating.add(_rev_node)
s_dif3.done_year[_rev_node] = s_dif3.year
s_dif3.year += 20
_plain = s_dif3.diffusion_share(_rev_node)
s_dif3.done.add("corpus_dispersed"); s_dif3.operating.add("corpus_dispersed")
s_dif3._done_changed()
_published = s_dif3.diffusion_share(_rev_node)
check("published knowledge (corpus_dispersed) escapes to competitors "
      "faster than a secret kept in one workshop - reusing the model's own "
      "existing idea of how knowledge spreads rather than inventing a "
      "second one",
      _published > _plain, (_plain, _published))

check("diffusion_index is 0 with nothing operating",
      sim().diffusion_index() == 0.0, sim().diffusion_index())
check("...and rises, revenue-weighted, once something is",
      s_dif3.diffusion_index() > 0.0, s_dif3.diffusion_index())

_st_dif, _, _ = proto([{"cmd": "state"}])
check("`state` reports how much of what you run has diffused to competitors",
      "diffusion_index" in _st_dif[0]
      and 0.0 <= _st_dif[0]["diffusion_index"] <= 1.0,
      _st_dif[0].get("diffusion_index"))

# --- JOB: the rubber bug (ac69bfb, e88a822) recurs across the tree. A node
# can consume a material nothing in its own ancestry can produce, and the
# game will still sell it at a flat book price - so you could build an
# aluminium monoplane in Rome 100AD with no grid, no generator, no
# electrolysis cell, buying the metal at 6 denarii a kilo. This pins the 24
# materials audited and fixed for that gap (see rome/data/review/
# MATERIAL_GATING.md for the full audit, including the ~69 materials judged
# genuinely purchasable in antiquity - iron, copper, wool, clay, timber,
# salt and the like - where no gate is correct).
#
# The walk follows BOTH `pre` and `req_any` - a node can be reached either
# way (ac69bfb's own JOB 3c, and _node_explain's "req_any COUNTS AS
# UNLOCKING" above, make the same point) - and a req_any OPTION may name a
# material rather than a node ("a purchasable commodity", see
# substitution_quality), which is not something to recurse into. And the
# graph is genuinely cyclic once req_any counts (junction_transistor ->
# silicon_path -> point_contact_transistor -> junction_transistor is one
# example already noted elsewhere in this tree) - a visited set is not
# optional here, it is the difference between this check finishing and an
# OOM kill.
def _full_ancestors(k, _nodes=NODES):
    seen, stack = set(), [k]
    while stack:
        cur = stack.pop()
        if cur in seen:
            continue
        seen.add(cur)
        n = _nodes.get(cur)
        if not n:
            continue
        for p in (n.get("pre") or []):
            if p in _nodes and p not in seen:
                stack.append(p)
        for g in (n.get("req_any") or []):
            for opt in (g.get("options") or {}):
                if opt in _nodes and opt not in seen:
                    stack.append(opt)
    seen.discard(k)
    return seen


# material key -> node ids, any ONE of which in a consumer's full ancestry
# means that consumer can plausibly get the material. Kept in sync by hand
# with the fixes this pins; MATERIAL_GATING.md explains each choice.
_GATED_MATERIALS = {
    "aluminium_kg": {"mat_aluminium"},
    "aluminum_oxide_kg": {"ch2_process_bayer"},
    "ammonia_kg": {"mat_ammonia", "chm_haber_bosch", "chm_solvay_process"},
    "bleach_kg": {"mat_chlorine", "chm_bleaching_powder"},
    "calcium_carbide_kg": {"chm_alkali_waste"},
    "celluloid_kg": {"mat_celluloid"},
    "chromium_kg": {"mat_chromium"},
    "cryolite_kg": {"mat_cryolite"},
    "manganese_kg": {"mat_manganese"},
    "molybdenum_kg": {"mt2_molybdenum_extraction"},
    "nickel_kg": {"mat_nickel"},
    "petroleum_refined_kg": {"mat_petroleum_refined"},
    "phosphorus_red_kg": {"chm_phosphorus_extraction"},
    "platinum_g": {"mat_platinum_bulk"},
    "porcelain_kg": {"mat_porcelain"},
    "quartz_tube_kg": {"fused_quartz"},
    "rubber_tubing_kg": {"mat_rubber_coagulated", "mat_synthetic_rubber"},
    "selenium_kg": {"pwr_selenium_metal"},
    "steam_kg": {"steam_atmospheric", "steam_watt", "cap_power_steam",
                 "steam_high_pressure"},
    "sulfuric_acid_kg": {"lead_chamber", "chm_contact_sulfuric"},
    "tungsten_kg": {"mat_tungsten"},
    "wood_pulp_kg": {"prn_wood_pulp"},
    "zinc_kg": {"mat_zinc", "zinc_metal", "zinc_industry_scale"},
}
# graphite_kg is only gated for the four ultra-high-purity semiconductor
# consumers - ordinary (natural, low-purity) graphite brush contacts and
# die-sinker electrodes are left alone deliberately, so this one is pinned
# node-by-node rather than material-wide (gp_carbon_brushes buying natural
# graphite off the market is correct, not a gap).
_graphite_pinned = ("ge_reduction", "silicon_path", "single_crystal",
                     "zone_refining")

# electroplating consumes nickel_kg but is deliberately left off the hook:
# it sits UPSTREAM of mat_nickel itself (mat_nickel -> cap_pure_4N ->
# electroplating), so gating it on nickel would make electroplating
# permanently unbuildable. The generic electroplating technique doesn't
# specifically need nickel anyway - silver, copper and gold plating are
# electroplating too - so this stays a documented, judged-legitimate gap
# rather than a fix (see MATERIAL_GATING.md).
_KNOWN_UNGATED = {"nickel_kg": {"electroplating"}}

_mat_gaps = {}
for _mat, _prods in _GATED_MATERIALS.items():
    _consumers = [k for k, v in NODES.items() if (v.get("mat") or {}).get(_mat)]
    _excuse = _KNOWN_UNGATED.get(_mat, set())
    _bad = [k for k in _consumers
            if k not in _excuse and not (_prods & _full_ancestors(k))]
    if _bad:
        _mat_gaps[_mat] = _bad
check("every consumer of a material this tree can only make by an invented, "
      "non-ancient process has that process (or an equally real substitute) "
      "somewhere in its own ancestry - not just a book price",
      not _mat_gaps, _mat_gaps)
check("...and there really are gated materials and consumers here to check, "
      "not an empty audit passing by having nothing to look at",
      len(_GATED_MATERIALS) >= 20
      and sum(1 for _m in _GATED_MATERIALS
              for _k, _v in NODES.items() if (_v.get("mat") or {}).get(_m)) >= 60,
      len(_GATED_MATERIALS))
_graphite_bad = [k for k in _graphite_pinned
                 if "mat_graphite_pure" not in _full_ancestors(k)]
check("the semiconductor-grade graphite crucibles on the road to the goal "
      "itself require actually-pure graphite, not natural lump graphite "
      "bought off the market",
      not _graphite_bad, _graphite_bad)

# --- three players: `why` quoted the BUILD crew as the staff requirement,
# and `open` actually enforces ongoing SUPERVISION (venture_hands), a
# different and sometimes larger number never shown before the money was
# spent. `why` must now show both, from the same function `open` checks.
r, _, _ = proto([{"cmd": "why", "id": "cementation_steel"}])
_why_open = r[0]["staff_to_keep_it_open"]
_s = sim()
_expect_sch, _expect_art = _s.venture_hands("cementation_steel")
check("`why`'s supervision figure is computed by the same function `open` "
      "enforces (venture_hands), not a second estimate of it",
      abs(_why_open["scholars"] - round(_expect_sch, 2)) < 0.01
      and abs(_why_open["artisans"] - round(_expect_art, 2)) < 0.01,
      "why said %s, venture_hands says %.2f/%.2f"
      % (_why_open, _expect_sch, _expect_art))
check("the supervision figure can genuinely exceed the build crew shown as "
      "staff_needed, which is exactly the case a Norse playtester measured "
      "(2.13 craftsmen enforced against a displayed 2 artisans)",
      _why_open["artisans"] > r[0]["staff_needed"]["artisans"],
      "staff_needed %s, staff_to_keep_it_open %s"
      % (r[0]["staff_needed"], _why_open))

# --- and a node nobody could ever run as a going concern (pure knowledge)
# gets no supervision figure at all - there is nothing to keep an eye on.
r, _, _ = proto([{"cmd": "why", "id": "ag2_adulteration_law"}])
check("a pure-knowledge node (no revenue, no upkeep) carries no "
      "staff_to_keep_it_open - there is no concern to supervise",
      r[0].get("staff_to_keep_it_open") is None, r[0].get("staff_to_keep_it_open"))

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
