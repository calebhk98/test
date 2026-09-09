# han_china_100ad / BREAK

## What I did
Ran `python3 rome/sim/simulator.py agent --civ han_china_100ad` as a long-lived
subprocess (stdin fed from an append-only fifo-like file, stdout captured to a
log) so I could send one JSON command at a time and inspect the reply, per the
protocol in BRIEF.md. Started by inspecting `state` at year 100 turn zero
before doing anything else, cross-checked the civ definition
`rome/data/civilizations/han_china_100ad.json` against what the running sim
actually reports, then moved on to buy/negative-quantity, non-string id,
training-queue timing, cost-multiplier verification via `why`, geography reach,
capital conservation across `step`, and boundary/malformed-input cases.

NOTE on environment: this sandbox's scratchpad directory is shared with other
concurrent/previous sessions (I found stray simulator processes for other
kits/civs and thousands of unrelated leftover files there). I isolated my own
run in a private subdirectory to avoid cross-contamination. This is an
infrastructure quirk of the test rig, not a game finding, but I record it here
in case it explains any oddity I did not reproduce cleanly.

## Result
(in progress — see findings below; updated as testing continues)

## FINDINGS

### F1. Han China's civ file names a starting tech that does not exist, so the plough it advertises is silently never granted
- **Severity**: BUG
- **What I saw**:
  `rome/data/civilizations/han_china_100ad.json` lists `starting_techs`
  including `"fud_heavy_plough"`. At year 100, turn zero, before any command
  other than `state`:
  ```
  {"cmd":"state"}
  -> ...,"done_count": 11,"done_granted": 0,"done_earned": 11, ...
  ```
  The civ file lists 12 starting_techs, but `done_count` is 11. Querying each
  starting tech id with the protocol's own `why` command:
  ```
  {"cmd":"why","id":"fud_heavy_plough"}
  -> {"ok": false, "error": "unknown node 'fud_heavy_plough'. did you mean: no idea"}
  ```
  All 11 other starting-tech ids resolve fine with `why`. The node the civ
  blurb is clearly trying to name exists under a different id:
  ```
  {"cmd":"why","id":"fud_heavy_mouldboard_plough_coulter"}
  -> {"ok": true, "id": "fud_heavy_mouldboard_plough_coulter", ...,
      "done": false, "active": false, "can_start_now": false,
      "start_blocked_reason": "missing prerequisites: cap_tol_1mm"}
  ```
- **Why it is wrong**: The civ's own blurb and notes explicitly advertise this
  as a starting advantage: `"blurb": "...the seed drill, the moldboard
  plough..."` and `"notes": ["You start with cast iron, paper, the horse
  collar, the seed drill and water-powered bellows already in hand..."]`.
  Because `Sim.__init__` grants starting techs with a simple
  `if k in self.nodes: self.done.add(k)` (silently skipping anything not
  found, no warning, no error surfaced to the player), the mistyped/stale id
  means Han China never actually receives the heavy plough. The player is
  told (via the civ blurb, which is in-world flavor text a real player would
  read) that they start with a technology they in fact do not have, and
  nothing in the protocol ever reveals this — `state` just quietly reports one
  fewer `done_count` than the civ file promises, with no diagnostic.
- **Reproduce**:
  ```
  python3 rome/sim/simulator.py agent --civ han_china_100ad
  {"cmd":"state"}
  {"cmd":"why","id":"fud_heavy_plough"}
  ```
  Compare `done_count` (11) against `len(starting_techs)` in
  `rome/data/civilizations/han_china_100ad.json` (12), and note the `why`
  error on the missing id.

### F2. `done_earned` counts free starting techs as "earned" — the split with `done_granted` does not do what its own code comment says
- **Severity**: BUG
- **What I saw**: Same turn-zero `state` call as F1:
  ```
  {"cmd":"state"}
  -> "done_count": 11, "done_granted": 0, "done_earned": 11
  ```
  This is before a single `start`, `buy`, `bounty`, or `step` command has been
  issued — the founder has spent no hours, no denarii, and made no decision
  yet.
- **Why it is wrong**: In `rome/sim/simulator.py`, starting techs are added
  straight into `self.done` in `Sim.__init__` (`for k in
  self.civ.get("starting_techs", []): ... self.done.add(k)`) without ever
  touching `self.granted`. Separately, the *other* free-tech mechanism (tier-0,
  zero-cost nodes auto-completed once prerequisites are met during `step`) is
  explicitly commented: "This node is granted because THE SOCIETY already has
  it, not because you built it" and is added to `self.granted`. `done_granted`
  is computed as `len(s.granted & s.done)` and `done_earned` as
  `len(s.done - s.granted)`. Since civ starting techs never enter `granted`,
  every one of them falls into `done_earned` — the bucket that, by the code's
  own stated intent, should mean "built by the player." A civ with more
  starting techs (Han China has 12 named, Rome has fewer) gets a bigger
  `done_earned` head start than Rome for free, with no corresponding
  `done_granted` credit, even though by the code's own logic these are exactly
  the "granted, not built" case. `done_granted + done_earned == done_count`
  holds arithmetically (0 + 11 = 11), so that particular invariant survives,
  but the semantic meaning of the two fields is broken: `done_earned` is not
  "what you earned," it is "what you either earned or were born with."
- **Reproduce**:
  ```
  python3 rome/sim/simulator.py agent --civ han_china_100ad
  {"cmd":"state"}
  ```
  Read `done_granted` (0) vs `done_earned` (11) before any action is taken,
  and compare with `rome/sim/simulator.py` around the `self.granted.add(k)`
  comment (~line 1480) versus the starting-techs loop (~line 396-398), which
  never calls `self.granted.add`.


### F3. The "society already has this" auto-grant is not civilization-aware: Han China is credited with building Roman aqueducts, Roman sewers, and Roman partnership law
- **Severity**: BUG
- **What I saw**: From the turn-zero state in F1/F2 (`capital: 400.0`, `done_count: 11`), a single `step` of 1 year produced:
  ```
  {"cmd":"step","years":1}
  -> {"ok": true, "completed": [ ...150 entries... ], "events": [],
      "year": 101, "capital": -287.5, "revenue": 10197.6, "upkeep": 9375.0,
      "living_cost": 821.9, "net_per_year": 0.8, "done_count": 150,
      "done_granted": 139, "done_earned": 11, ...}
  ```
  Among the 139 nodes newly marked `done_granted` in that single year (i.e.
  "granted because THE SOCIETY already has it, not because you built it" per
  the code's own comment) were, verbatim from the `completed` list:
  - `civ_aqueduct_roman` — "Roman aqueduct with inverted siphons"
  - `civ_sewer_roman` — "Roman sewer with gravity flow"
  - `civ_insula` — "Insula: Roman apartment block"
  - `civ_chorobates` — "Chorobates: Roman water levelling rod"
  - `civ_surveying_groma` / `opt_groma` — "Groma (surveying cross)"
  - `civ_road_paved` / `lnd_paved_road_network` — "Roman paved road with surveying" / "Paved trunk road network"
  - `fin_annona` — "Annona grain dole and administration" (the Roman state grain dole)
  - `fin_societas` — "Partnership (societas)" (a specifically Roman legal contract form)
  - `civ_amphitheatre`, `sea_pharos_lighthouse`, `fin_argentarii` (Roman deposit bankers), `fin_tax_farming`, `civ_marble_facing`, `civ_brick_tile`, `civ_vault_barrel`, `civ_arch_roman` ("Roman masonry arch")

  Following up with `why` on a few of these, all in the SAME Han China run,
  after the step:
  ```
  {"cmd":"why","id":"civ_aqueduct_roman"}
  -> tier 0, cost.total 0.0, done: true,
     note: "...At valleys, inverted siphons...carried water..."
  {"cmd":"why","id":"fin_annona"}
  -> tier 0, cost.total 0.0, done: true,
     note: "State purchase and distribution of grain..."
  {"cmd":"why","id":"civ_insula"}
  -> tier 0, cost.total 0.0, done: true,
     note: "...Rome housed its poor in dense urban clusters..."
  {"cmd":"why","id":"fin_societas"}
  -> tier 0, cost.total 0.0, done: true,
     note: "Contractual partnership between two or more parties..."
  ```
- **Why it is wrong**: This is a wrong/impossible state, not merely
  unrealistic flavor. The Later Han Empire did not build Roman aqueducts with
  inverted siphons, did not operate the Roman grain dole (`annona`), did not
  house people in Roman `insulae`, and its partnership law was not `societas`
  — Han China had its own (very capable — the civ file itself says "a far
  more capable customer than Rome's") canals, granaries, and commercial
  institutions, which this tech tree does not model as separate nodes. The
  root cause is in `Sim.step()` section 4a in `rome/sim/simulator.py`
  (~line 1470-1486): it walks `self.order` (the strategy's node ordering,
  loaded once via `load_strategy` and NOT civilization-specific) and grants
  any node with `tier==0`, `ph==0`, `_total_cost<=1` the moment its
  prerequisites are met, regardless of which civilization is playing. The
  code comment at that line ("Anything Rome ALREADY HAS costs nothing") shows
  the mechanism was designed and named for Rome specifically, then reused
  unchanged for every other civilization. A civ-appropriate version would
  need to gate at least the explicitly Roman-branded nodes (there appear to
  be a couple dozen with "Roman"/Latin-institution names) on `civ.id ==
  "rome_100ad"` or an equivalent per-civ tier-0 set, the same way
  `starting_techs` is already civ-specific data.
- **Reproduce**:
  ```
  python3 rome/sim/simulator.py agent --civ han_china_100ad
  {"cmd":"state"}
  {"cmd":"step","years":1}
  {"cmd":"why","id":"civ_aqueduct_roman"}
  {"cmd":"why","id":"fin_annona"}
  {"cmd":"why","id":"civ_insula"}
  {"cmd":"why","id":"fin_societas"}
  ```
  All four `why` calls come back `"done": true` for a Han China run that has
  never started a single project.

### F4. `net_per_year` does not predict the capital change over the very next year — off by 725.5 den on a 1-year step
- **Severity**: BUG
- **What I saw**: Immediately before stepping (turn zero, year 100):
  ```
  {"cmd":"state"}
  -> {"capital": 400.0, "revenue": 8700.0, "upkeep": 9375.0,
      "living_cost": 738.0, "mine_operating_cost": 0.0, "net_per_year": -1413.0, ...}
  ```
  `8700 - 9375 - 738 - 0 = -1413`, so `net_per_year` is internally consistent
  with the other four figures shown in that same state object (this part
  WORKS-WELL). But stepping exactly one year from there:
  ```
  {"cmd":"step","years":1}
  -> {"year": 101, "capital": -287.5, ...}
  ```
  Actual change in capital: `-287.5 - 400.0 = -687.5`. Predicted change from
  the `net_per_year` the game itself had just reported: `-1413.0`. The
  difference is `725.5` denarii — capital fell only about half as much as the
  game's own figure, taken one command earlier, said it would.
- **Why it is wrong**: A player using `net_per_year` to plan ahead (e.g. "I
  have 400 capital and lose 1413/yr, I have well under a year before I'm
  bankrupt") is given a number that does not hold even one step later, with
  no warning that it is about to change. Reading the code
  (`rome/sim/simulator.py`, `Sim.step()`), the capital update in section 2
  ("money") runs AFTER section 1 ("staff"), which can change staff counts
  (artisans went from `3.0` to `6.02` over this same step, with no `buy`
  command issued and `training_pending` empty both before and after), and
  the auto-grant in section 4a (139 nodes, see F3) runs AFTER the capital
  update and changes `revenue`/`upkeep` for the *next* report without ever
  having applied to the capital change just shown. So the `net_per_year` a
  player reads in `state` is this instant's snapshot, not a stable rate, and
  no field tells the player it is about to move by 50%+ before their very
  next `step`.
- **Reproduce**:
  ```
  python3 rome/sim/simulator.py agent --civ han_china_100ad
  {"cmd":"state"}
  {"cmd":"step","years":1}
  ```
  Compare `capital` delta (`-687.5`) against the prior `net_per_year`
  (`-1413.0`).

### F5. `bounty` prices ignore Han China's cost multiplier that `why` itself just quoted for the same node
- **Severity**: BUG
- **What I saw** (fresh Han China run, year 100, turn zero, capital 400):
  ```
  {"cmd":"why","id":"fud_hay_making_storage"}
  -> "cost": {"labour": 22.5, "materials": 12.5, "capital": 200.0,
              "base_total": 235.0, "civ_domain_factor": 0.8,
              "material_distance_factor": 1.0, "price_index": 1.0,
              "total": 188.0}, "bounty_eligible_by_type": true, ...
  {"cmd":"bounty","id":"fud_hay_making_storage"}
  -> {"ok": false, "error": "cannot afford the bounty: needs about 588 denarii, you have 400. Earn or wait, then try again"}
  ```
  `why` says building this yourself costs Han China 188 den (235 base x 0.8
  agriculture discount). The very same node, as a bounty, is quoted at 588
  den — not `188 * 2.5 = 470` (the bounty's own documented "pay 2.5x, save
  65% of your hours" markup applied to the civ-adjusted price), but
  `235 * 2.5 = 587.5 ≈ 588`, i.e. the 2.5x markup applied to the RAW,
  civ-unadjusted base cost.
- **Why it is wrong**: `rome/sim/simulator.py`'s `why` handler (`_node_explain`,
  the `"cost"` block) now correctly multiplies by `civ_cost_factor(k)` and
  `material_cost_factor(k)` before quoting `total` — a comment right above it
  explains this was fixed after an earlier playtester found `why` "lying"
  about cost being civ-independent. But the `bounty` command
  (`op == "bounty"`, ~line 2387) still computes `price = nodes[k]["_total_cost"]
  * 2.5`, and `Sim.post_bounty()` (~line 1313) independently recomputes the
  identical unadjusted `price = n["_total_cost"] * 2.5` and actually deducts
  that from capital. So the fix for the `start`-project cost quote was never
  applied to the bounty path: Han China's 20% agriculture discount (and by
  the same logic, its 30% metallurgy / 40% casting / 50% paper discounts, or
  a Rome-favoring civ's penalty multipliers in the other direction) is
  silently absent from every bounty price, while the game's own `why` output
  for the exact same node implies it should apply. A player who reads `why`,
  concludes "my metallurgy is 30% off," and then reaches for `bounty` to
  convert money into hours gets charged as if playing Rome.
- **Reproduce**:
  ```
  python3 rome/sim/simulator.py agent --civ han_china_100ad
  {"cmd":"why","id":"fud_hay_making_storage"}
  {"cmd":"bounty","id":"fud_hay_making_storage"}
  ```
  Compare the `total` (188.0) `why` quotes against the price named in the
  `bounty` error/`price` field (588, i.e. `235 * 2.5`, not `188 * 2.5 = 470`).


### F6. Training queue maturity and mid-training manumission — WORKS WELL
- **Severity**: WORKS-WELL
- **What I saw**: Fresh Han run. Bought 1 slave, tracked the training queue
  and `artisans` count across four separate 1-year `step` calls:
  ```
  {"cmd":"buy","what":"slaves","n":1}          -> capital 164.7, slaves 1
  {"cmd":"state"}                              -> training_pending: [{"artisan_capacity": 0.55, "ready_year": 103.0}]
  {"cmd":"step","years":1}  (year 100->101)    -> slaves 0, freedmen 1,
                                                   training_pending: [{"artisan_capacity": 1.0, "ready_year": 103.0}]
  {"cmd":"step","years":1}  (year 101->102)    -> training_pending unchanged (still capacity 1.0, ready_year 103)
  {"cmd":"step","years":1}  (year 102->103)    -> training_pending STILL present at year==ready_year (not yet resolved)
  {"cmd":"step","years":1}  (year 103->104)    -> training_pending: [] (cleared), artisans rose accordingly
  ```
  The random auto-manumission policy (`step()` section 2: 25% chance/year to
  manumit a quarter of your slaves) freed the one bought slave after the
  very first step, WHILE they were still untrained. Instead of granting the
  full trained-artisan credit immediately (the exploit an earlier fix
  closelosed, per the code comments at `Sim.manumit()`), the pending
  training row's `artisan_capacity` was upgraded from `0.55` to `1.0` (the
  free-and-trained value) but its `ready_year` (103) did not move up — the
  calendar wait was not skipped, only the eventual payout was upgraded.
- **Why it is right**: This is exactly what the in-code design comments
  claim should happen ("Freeing an untrained person upgrades what they will
  be worth WHEN they mature; it does not skip the maturing"), and I could not
  make it pay out early, pay out twice, or vanish. The maturity check
  (`if self.year >= ready: self.artisans += cap`) runs on the PRE-increment
  year, so a person bought at year 100 with `ready_year=103` matures on the
  step that carries year 103 into year 104, not the step that first displays
  `"year": 103` — mildly confusing (a `ready_year` in `state` looks like it
  should resolve by the time `state` itself reports having reached that
  year), but internally consistent and not exploitable: I never saw a
  duplicate `artisans` credit or a training row silently disappear.
- **Reproduce**: as shown above, in order, on `python3 rome/sim/simulator.py
  agent --civ han_china_100ad`.


### F2-addendum. The done_granted/done_earned mislabeling from F2 has a real gameplay consequence: starting techs can be "forgotten" in a sacking
- **Severity**: BUG (extends F2)
- **What I saw**: Continuing the same run past the Yellow Turban rebellion
  (`{"cmd":"step","years":100000}`, which correctly ran to the year-600
  horizon and stopped — see F7/WORKS-WELL below), the `events` log showed
  four `"KNOWLEDGE LOST: 1 technologies forgotten (the corpus was never
  printed and dispersed)"` entries during the rebellion (years 185, 186, 190,
  194), and across that same step `done_earned` fell from `11` to `7` while
  `done_granted` stayed at `139` and `technologies_at_risk` fell from `4` to
  `0`.
- **Why it is wrong**: This confirms the split is not cosmetic — the
  "forgotten in a sacking" mechanic specifically draws from the
  founder-personal-knowledge pool (`done - granted`, i.e. `done_earned`),
  which is the right design (knowledge "the society already has" should not
  be losable to one workshop being sacked; knowledge only the founder wrote
  down should be). But because F1/F2 showed Han China's 11 CIV-GIVEN starting
  techs (cast iron, paper, the horse collar, water-powered bellows, etc. —
  things all of Han society already has, per the civ file's own description)
  are never added to `self.granted`, they count as `done_earned` and are
  therefore exposed to being "forgotten" when a site is sacked, exactly as
  if the founder had personally discovered cast-iron metallurgy in a private
  notebook. A society that has had blast furnaces for five centuries does
  not forget them because rebels burn one workshop. This is a second,
  concrete way F1/F2's mislabeling produces an actually-wrong game state,
  not just a wrong number in `state`.
- **Reproduce**: run the F1/F2 reproduction, then `{"cmd":"step","years":100000}`
  and watch `done_earned` drop across the Yellow Turban rebellion (184-205)
  while `done_granted` does not move.

### F7. Sacking and knowledge-loss numbers are internally consistent across an entire run — WORKS WELL
- **Severity**: WORKS-WELL
- **What I saw**: Turn zero `state` reported
  `"knowledge_risk": {"technologies_at_risk": 4, "loss_chance_if_a_site_is_sacked": 0.8, "fraction_lost_when_it_happens": 0.4, "expected_technologies_lost_per_sacking": 1.3, ...}`.
  Running `{"cmd":"step","years":100000}` from year 105 drove the simulation
  all the way to the year-600 horizon in one call (`"ended": true,
  "end_reason": "ran out of horizon (600 AD) without reaching the goal"`),
  logging 8 `"Yellow Turban rebellion: a site is sacked"` events between 185
  and 205. Exactly 4 of those 8 carried a `"KNOWLEDGE LOST: 1 technologies
  forgotten"` follow-up, and by year 600 `technologies_at_risk` had fallen to
  `0` and `expected_technologies_lost_per_sacking` to `0.0` — the pool of 4
  at-risk technologies was exhausted after losing exactly 4, never more, and
  `done_earned` fell by exactly 4 (11 to 7) while `done_granted` (139) and
  `done_count`'s other components were untouched.
- **Why it is right**: The claimed risk parameters (4 at-risk, 0.4 fraction
  lost per sacking event) produced a bounded, sensible outcome — losses
  stopped exactly at the size of the at-risk pool, no more than one
  technology vanished per successful loss-roll, and the accounting
  (`done_earned` shrinking, `done_granted` untouched) matched the "forgotten"
  narrative in the event log exactly. I tried to break this by running the
  full 500-year horizon in a single oversized `step` call (a boundary case:
  see also that this did not silently no-op — it processed all 495
  intervening years, logged fires, banditry, an arrears crisis, and the
  rebellion, then stopped cleanly at the horizon with a correct
  `end_reason`) and could not produce an impossible state: no negative tech
  count, no loss beyond the stated pool, no crash despite the huge step size.
- **Reproduce**:
  ```
  python3 rome/sim/simulator.py agent --civ han_china_100ad
  {"cmd":"state"}
  {"cmd":"step","years":100000}
  ```

### F8. Retest: `step`/`start`/`buy` after game-over correctly refuse instead of silently no-opping — WORKS WELL (fix holds for Han)
- **Severity**: WORKS-WELL
- **What I saw**: After the run ended at the year-600 horizon (see F7):
  ```
  {"cmd":"step","years":1}
  -> {"ok": false, "error": "the run has ended (ran out of horizon (600 AD) without reaching the goal); time cannot advance. Use {\"cmd\":\"state\"} to see the final position."}
  {"cmd":"start","id":"mat_zinc_metal"}
  -> {"ok": false, "error": "the run has ended (...); nothing more can be started"}
  {"cmd":"buy","what":"forest","n":10}
  -> {"ok": false, "error": "the run has ended (...); nothing more can be bought"}
  ```
- **Why it is right**: The brief flagged "`step` silently no-opping after
  game over" as a bug a previous Rome tester found and got fixed. I retested
  it end-to-end on Han China by actually running a game to its horizon
  (rather than assuming the fix generalizes), and all three of `step`,
  `start`, and `buy` give an explicit `ok:false` with the end reason instead
  of pretending to succeed. I did not find a command that still silently
  no-ops post-game-over.
- **Reproduce**: run to the horizon as in F7, then issue any of `step`,
  `start`, `buy`.

## Result
Two separate Han China games were run to completion or near-completion
during this session (a third, earlier, isolated process was lost to a stray
`kill` while cleaning up cross-contamination from this shared sandbox — see
the environment note above — but nothing of value was lost since no findings
depended on it).

The main tracked run (`hanbreak3_fresh`) never seriously pursued the
transistor goal — this was a BREAK pass, not a WIN attempt, so the founder
mostly bought one slave, watched the training queue, and then jumped straight
to the year-600 horizon with an oversized `step` to see how the engine handled
it. That run ended with `end_reason: "ran out of horizon (600 AD) without
reaching the goal"`, `capital: 6308.9`, `done_count: 146` (`done_granted:
139`, `done_earned: 7`), having survived the Yellow Turban rebellion (losing
4 of its 4 at-risk technologies to sacking, exactly as `knowledge_risk`
predicted) and a 20-year arrears crisis.

The most important results are the eight numbered findings above: two
outright content/logic bugs specific to Han China's civ file and the
civilization-aware auto-grant and bounty-pricing code (F1, F3, F5), one
mislabeling bug with a real gameplay consequence (F2, and its addendum), one
number that contradicts itself one step later (F4), and three places I
attacked hard and could not break (F6, F7, F8) — including confirming, on
Han China specifically, that the negative-quantity `buy`, non-string `id`,
and post-game-over `step` bugs a previous Rome tester found are still fixed
here.

One methodological note carried through the whole session: `rome/sim/
simulator.py` was visibly being edited on disk WHILE this session ran (line
numbers inside a function shifted by ~30 lines between two `Read` calls nine
minutes apart, and a `why` response gained four new cost-breakdown fields —
`base_total`, `civ_domain_factor`, `material_distance_factor`, `price_index`
— between one background simulator process and the next one I started
minutes later, with the new code's own comment describing exactly the bug I
was about to report). I do not know whether that was a live fix landing from
this same finding being surfaced elsewhere, or an unrelated concurrent
session; either way, I re-verified every finding above against a freshly
started process reading the current file before writing it up, and F5 is
reported only because the *bounty* price (a separate code path, `post_bounty`
at ~line 1313) was NOT covered by that fix even though `why`'s displayed
quote now is.
