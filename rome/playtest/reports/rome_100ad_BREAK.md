# rome_100ad / BREAK

## What I did

My brief was to break the simulator, not to win it, so I never tried to reach
`point_contact_transistor` for real. I drove
`python3 rome/sim/simulator.py agent --civ rome_100ad --seed 1` (and a few
unseeded runs) entirely through the JSON protocol on stdin/stdout, piping in
whole scripts of commands built with `printf`/Python rather than typing
turn-by-turn, so I could hold every other variable constant and vary one thing
at a time. I did not touch `run`, `compare`, `sensitivity`, `sweep`, the CLI
`path`/`why`/`costs`, or `treetool.py`, and I did not import `simulator` as a
module. I read the tech tree JSON exactly once, to check a specific claim I
doubted (see F5), and I say so there.

I went after the categories in the brief in roughly this order: affordability
and arithmetic on `buy`, degenerate quantities (0, negative, 1e9) on every
resource, malformed/adversarial JSON on every command that takes an `id`, the
start/stop/start state machine, whether `available` and `start` ever
disagree, whether `path`/`why`/`bounty` agree on missing prerequisites, the
resource-throttle mechanic, the time horizon at 0/negative/huge step sizes,
and the founder-mortality mechanic that `00_BRIEFING.md` says the whole game
hinges on.

The most interesting turn in the session: partway through, identical command
sequences against a fixed `--seed 1` started returning **different** results
for `buy slaves`. I initially treated this as a determinism bug worth
reporting on its own, until `git log` showed why: another Claude session
(role WEIRD, reported in `rome_100ad_WEIRD.md`) found and reported the same
`buy_slaves`/`manumit` double-counting exploit I was independently
rediscovering, and the developer committed a live fix
(`397b2ab "Close the slave-manumit exploit a playtester found in under an
hour"`) to `rome/sim/simulator.py` **while my session was running**. Every
result below is stated against the code as of that commit
(`397b2aba6c65b84df8cf663bde8989a654b84baa`, checked with `git rev-parse
HEAD` at the time of testing), and I flag anywhere my evidence spans the
patch boundary.

## Result

I never stepped past year 105 in any run that mattered for a finding — this
report is about breaking mechanics, not about survival — except for one
deliberate `step years=100000` used to test the time-horizon boundary, which
the simulator correctly clamped to year 600 AD (`end_reason: "ran out of
horizon (600 AD) without reaching the goal"`) with no crash. In every targeted
test the starting state was the fresh civ default: year 100, capital 400.0,
founder_hours_available 2400.0, artisans 3.0, forest_ha 0.0, slaves 0.

## FINDINGS

### F1. `buy forest` with a negative quantity mints money and creates negative land, while reporting failure
- **Severity**: EXPLOIT / BUG (still open at HEAD 397b2ab)
- **What I saw**:
  ```
  > {"cmd":"state"}
  {"ok": true, "year": 100, "capital": 400.0, ..., "forest_ha": 0.0, ...}
  > {"cmd":"buy","what":"forest","n":-5}
  {"ok": false, "error": "cannot afford -5 ha of coppice woodland (you have 1650 denarii)"}
  > {"cmd":"state"}
  {"ok": true, "year": 100, "capital": 1650.0, ..., "forest_ha": -5.0, ...}
  ```
  The command is reported `"ok": false` — the protocol's own convention says
  a `false` reply means nothing happened — yet capital jumped from 400.0 to
  1650.0 (+1250, i.e. `-5 * -250`) and `forest_ha` went to **-5.0**, an
  impossible amount of land. Scaling it up is worse:
  ```
  > {"cmd":"buy","what":"forest","n":-1000000}
  {"ok": false, "error": "cannot afford -1000000 ha of coppice woodland (you have 250000400 denarii)"}
  > {"cmd":"state"}
  {"ok": true, "year": 100, "capital": 250000400.0, ..., "forest_ha": -1000000.0, ...}
  ```
  A single line manufactures a quarter of a billion denarii from a starting
  balance of 400, and it works from any fresh state, repeatably, with no
  founder hours and no prerequisites.
- **Why it is wrong**: The cost formula is evidently `cost = n * price_per_ha`
  with no sign check, so a negative `n` produces a negative cost, and
  `capital -= cost` credits the player. Whatever downstream check decided
  this should fail (probably `cost <= 0` rather than `capital < cost`) fires
  and returns `ok:false`, but the mutation happens either before that check
  or regardless of it. The exact sibling exploit for `buy slaves`/`manumit`
  was found by another playtester this same session and patched in commit
  `397b2ab` (see "What I did"); `buy forest` was not touched by that commit
  and is still exploitable at HEAD.
- **Reproduce** (fresh process, `--civ rome_100ad --seed 1`):
  ```
  {"cmd":"buy","what":"forest","n":-5}
  {"cmd":"state"}
  ```

### F2. `buy manumit` with a negative quantity fabricates a slave and negative freedmen out of nothing
- **Severity**: EXPLOIT / BUG (still open at HEAD 397b2ab)
- **What I saw**: from a fresh state with 0 slaves and 0 freedmen:
  ```
  > {"cmd":"buy","what":"manumit","n":-1}
  {"ok": false, "error": "you have no slaves to free"}
  > {"cmd":"state"}
  {"ok": true, ..., "slaves": 1, "freedmen": -1, "artisans": 2.55, ...}
  ```
  (`artisans` was 3.0 before the call.) The error message is entirely
  reasonable on its face — you do have no slaves — but the call still
  materialised one slave, drove `freedmen` to a negative, impossible value,
  and silently cut `artisans` by 0.45 (the exact figure the F397b2ab patch
  now uses for a *legitimate* single manumission — see WORKS-WELL F10 below
  for the correct version of this same arithmetic).
- **Why it is wrong**: Same family of bug as F1 — a negative quantity is not
  rejected before mutating state, it is mutated and then reported as
  refused. `slaves: -1 -> 1` from a call that is supposed to *reduce*
  slaves by freeing them, when you had none to free, is a direction error on
  top of the missing guard.
- **Reproduce**:
  ```
  {"cmd":"buy","what":"manumit","n":-1}
  {"cmd":"state"}
  ```

### F3. The equivalent `buy slaves` exploit existed for the whole session and was live-patched mid-test
- **Severity**: EXPLOIT (historical) / now fixed, noted for the record
- **What I saw**: Early in the session, from a fresh state:
  ```
  > {"cmd":"buy","what":"slaves","n":-1}
  {"ok": false, "error": "cannot afford -1 slaves at 300 denarii each (you have 700 denarii)"}
  > {"cmd":"state"}
  {"ok": true, ..., "capital": 700.0, "slaves": -1, "artisans": 2.45, ...}
  ```
  Re-running the identical command later in the same session gave a
  different, safe result:
  ```
  > {"cmd":"buy","what":"slaves","n":-1}
  {"ok": false, "error": "cannot afford -1 slaves: 0 denarii (0 each after the market moves against a purchase this size) and you have 400"}
  > {"cmd":"state"}
  {"ok": true, ..., "capital": 400.0, "slaves": 0, "artisans": 3.0, ...}
  ```
  `git log -- rome/sim/simulator.py` shows commit `397b2ab`, timestamped
  during my session, added `if n_people <= 0: return 0` to `buy_slaves` and
  reworked the pricing/training/reputation model. I did not edit anything;
  the fix landed from outside while I was testing the same civ.
- **Why I'm reporting this at all**: it is a real demonstration that the
  exact bug class in F1/F2 is fixable with a one-line guard (`if n <= 0:
  return 0` before any capital or resource mutation), and it shows the fix
  for `slaves`/`manumit` did not get mirrored into `forest`. I verified `buy
  slaves n=-1` is safe at current HEAD (see the second transcript above,
  captured after the patch) and treat that path as closed for the rest of
  this report.
- **Reproduce**: not reproducible any more for `slaves` — this entry is
  informational. F1 and F2 above are the live, still-open equivalents.

### F4. Passing a JSON object or array as `"id"` crashes the whole simulator process
- **Severity**: BUG (crash)
- **What I saw**:
  ```
  $ printf '%s\n' '{"cmd":"start","id":{"nested":"object"}}' | python3 rome/sim/simulator.py agent --civ rome_100ad --seed 1
  Traceback (most recent call last):
    File "/home/user/test/rome/sim/simulator.py", line 2556, in <module>
      sys.exit(main() or 0)
    File "/home/user/test/rome/sim/simulator.py", line 2550, in main
      return {"validate": cmd_validate, ...}[a.cmd](a)
    File "/home/user/test/rome/sim/simulator.py", line 2273, in cmd_agent
      resp = _agent_dispatch(s, nodes, cmd)
    File "/home/user/test/rome/sim/simulator.py", line 2116, in _agent_dispatch
      if k not in nodes:
  TypeError: unhashable type: 'dict'
  ```
  The process exits (exit code 1) and the whole session — every other
  in-progress project, all accumulated state — is gone; there is no `{"ok":
  false, ...}` reply at all, just a dead pipe. I confirmed the same crash,
  same shape, for **every** command that takes an `id`: `start`, `why`,
  `path`, `bounty`, and `stop` (the last one crashes one line lower, in
  `stop_project`, but with the identical `TypeError: unhashable type`). A
  JSON array (`"id":[1,2,3]`) crashes the same way (`unhashable type:
  'list'`). This is still true at HEAD `397b2ab`.
  All other malformed input I tried was handled gracefully: missing `id`,
  `id` as a number, `id` as a string that doesn't exist, `id` containing
  emoji/unicode, missing `cmd`, unknown `cmd`, `years` as a string, `years`
  missing (defaults to 1) — every one of those returned a clean `{"ok":
  false, "error": "..."}` and the process kept running. Only object/array
  `id` values crash.
- **Why it is wrong**: every one of the five call sites does something like
  `if k not in nodes: ...` where `nodes` is a `dict` keyed by node id, and a
  `dict`/`list` is unhashable as a dict key, so the membership test itself
  raises before any validation code runs. A single malicious or merely
  buggy client line ends the entire game for that process — there is no
  way for a player-side script to recover short of restarting and losing
  everything since the last checkpoint (and the protocol has no
  checkpoint/save command at all, as far as I found, so "everything" is
  "everything since year 100").
- **Reproduce** (any of these, on a fresh process):
  ```
  {"cmd":"start","id":{"a":1}}
  {"cmd":"why","id":{"a":1}}
  {"cmd":"path","id":{"a":1}}
  {"cmd":"bounty","id":{"a":1}}
  {"cmd":"stop","id":{"a":1}}
  {"cmd":"start","id":[1,2,3]}
  ```

### F5. A node's real cost overshoots its own quoted `why` price by 50%+, and the in-progress hour counter goes non-monotonic and negative with no logged event
- **Severity**: BUG (arithmetic)
- **What I saw**: `hot_air_balloon` quotes, via `why`, `cost.total: 4361.5`,
  `founder_hours: 400.0`, `calendar_floor_years: 2.0`. I started it alone (no
  other active project competing for founder hours) and stepped one year at
  a time:
  ```
  start hot_air_balloon
  step 1 -> active.hot_air_balloon = {founder_hours_left: 0.0,   years_in_progress: 1.0, spent: 2180.8}
  step 1 -> active.hot_air_balloon = {founder_hours_left: 160.0, years_in_progress: 0.0, spent: 4361.5}
  step 1 -> active.hot_air_balloon = {founder_hours_left: -40.0, years_in_progress: 1.0, spent: 6542.2}
  step 1 -> (project gone from active; done_count went 139 -> 140)
  ```
  `events` was `[]` on every one of those steps — nothing was logged to
  explain any of this. Walking through it:
  - Year 1: all 400 founder-hours are already spent (`founder_hours_left:
    0.0`) but only half the money (`2180.8` of `4361.5`) has been paid —
    fine so far, cost tracks the 2-year calendar floor, hours front-load.
  - Year 2: `founder_hours_left` **increases** from 0.0 to 160.0 — a
    "hours remaining" counter that goes back up after reaching zero is not
    a progress counter, it's broken — and `years_in_progress` resets to
    0.0, as if the project had restarted, with no stop/start command issued
    and no event. Total spent is now the *entire* quoted cost (4361.5), and
    the project has still not completed.
  - Year 3: `founder_hours_left` goes **negative** (-40.0, i.e. -10% of the
    total requirement), and total spent reaches 6542.2 — **50% more than
    the node's own quoted total cost of 4361.5** — before it finally
    completes on the *next* step.
  So the honest cost of `hot_air_balloon`, measured by capital actually
  debited, is at least 6542.2, not the 4361.5 that `why` advertises before
  you start it and that `active.founder_hours_total` still claims while it's
  running.
- **Why it is wrong**: This directly answers the brief's suggested attack
  ("do costs charged match costs quoted by `why`?") with "no." A player
  budgeting off the quoted price for a single, uncontested, one-item project
  will be short by roughly half the node's price by the time it finishes,
  with no warning and no event explaining the extra draw. The non-monotonic
  and negative `founder_hours_left` values indicate whatever accrual loop
  computes progress-per-step is not clamping or is double-applying/undoing
  work between steps.
- **Reproduce** (fresh process; the negative forest buy is only there to
  fund the project past the 400-denarii starting capital and is unrelated
  to the bug being demonstrated — the same non-monotonic hours/cost overrun
  reproduces on any sufficiently funded single active project with a
  multi-year calendar floor):
  ```
  {"cmd":"buy","what":"forest","n":-200}
  {"cmd":"start","id":"hot_air_balloon"}
  {"cmd":"step","years":1}
  {"cmd":"state"}
  {"cmd":"step","years":1}
  {"cmd":"state"}
  {"cmd":"step","years":1}
  {"cmd":"state"}
  ```

### F6. Capital drops with nothing active, zero upkeep, and zero pre-step revenue, and the state has no field that explains where the money went
- **Severity**: BUG (conservation) / possibly CONFUSING if it's an
  undocumented mechanic
- **What I saw**, from the civ's fresh default state, with no command
  issued except a single step:
  ```
  > {"cmd":"state"}
  {"ok": true, "year": 100, "capital": 400.0, "revenue": 0.0, "upkeep": 0, "active": {}, ...}
  > {"cmd":"step","years":1}
  {"ok": true, "year": 101, "capital": 184.0, "revenue": 666.7, "upkeep": 0.0, "active": {}, ...}
  ```
  Capital fell by 216 (400 -> 184) over a step in which: no project was
  active, the pre-step state reported `upkeep: 0` and `revenue: 0.0`, and
  the post-step state *still* reports `upkeep: 0.0`. The 139 techs that
  auto-completed this step (Rome's ambient, already-known "civilizational"
  nodes — `mat_bronze`, `civ_aqueduct_roman`, `fin_market`, etc.) all show
  `cost: 0` / `founder_hours: 0` in `available`, and I cross-checked: every
  single one of the 139 ids has `cost == 0` in the `available` listing
  fetched immediately beforehand, so they cannot be the source either. I
  re-ran this exact two-command sequence multiple times (same seed and
  unseeded) and the -216 delta is stable, so it isn't a stray RNG draw. I
  went on to run three consecutive 1-year steps with nothing ever started,
  and each step lost a *different* amount of money relative to the
  displayed revenue figure (step 2: revenue shown 666.7, capital actually
  rose by only 413.9, a hidden cost of ~252.8; step 3: revenue shown 1000.0,
  capital rose by only 721.0, a hidden cost of ~279), so this is not a
  fixed founder-living-cost constant either — it's some cost that scales
  with something (population size and reputation both drift over these
  steps) that the state object never surfaces.
- **Why it is wrong**: the brief's own conservation check — "track capital
  across a step and see whether revenue minus costs actually explains the
  change" — fails on the very first step of the very first turn of the
  game, before the player has done anything at all. Either there is a real
  cost here (a founder-living-expense or population-upkeep term) that
  belongs in the `upkeep` field and isn't there, or the number is wrong.
  Either way, a player cannot audit their own finances from the numbers the
  protocol hands them, which is exactly the property the brief asked me to
  test for.
- **Reproduce** (fresh process, nothing else issued):
  ```
  {"cmd":"state"}
  {"cmd":"step","years":1}
  ```

### F7. `start` never checks affordability — you can start all 295 currently-available projects at once on 400 denarii
- **Severity**: CONFUSING (possibly intentional design, flagged because it
  interacts badly with F6's opaque accounting)
- **What I saw**: I fetched `available` (295 items, including
  `tx2_watch_case` at 17,414.6 denarii and `fin_plantation` at 10,075.0, both
  far beyond the starting 400 denarii) and issued a `start` for every single
  one of them in one batch. All 295 returned `{"ok": true, "started": ...}`
  — zero rejections, including for the items costing 40x the player's cash
  on hand. Stepping one year afterward produced `"ended": true,
  "end_reason": "denounced: as a sorcerer"` (reputation had spiked to 85.0,
  scandal to 87.44), which is a sensible narrative consequence of trying to
  do 295 things at once — but the underlying fact remains that `start` has
  no capital gate at all; cost is only ever charged incrementally as
  `spent` accrues (as seen in F5), never checked up front. I separately
  confirmed a single `arrival_orientation` (quoted total cost 600.0) starts
  fine on a capital of 400.0 with no error and no partial-refusal.
- **Why it's worth flagging rather than filing as a plain BUG**: I can't
  tell from the protocol alone whether "start anything regardless of
  capital, and let debt catch up with you as denunciation/suspicion" is the
  intended design (it produces a coherent, even elegant, failure mode) or
  whether an affordability check on `start` was simply never written. I'm
  flagging it as CONFUSING because `why`'s `can_start_now`/
  `start_blocked_reason` fields never mention money as a blocker, and the
  brief specifically asks "can you buy something you cannot afford?" — for
  `start`, the answer is unconditionally yes, for anything, at any capital,
  including 0 or negative (see F6).
- **Reproduce**:
  ```
  {"cmd":"available"}
  ```
  then issue `{"cmd":"start","id":"<id>"}` for `tx2_watch_case` or
  `fin_plantation` from the fresh 400-denarii starting state; both succeed.

### F8. `buy ... n:0` is unconditionally reported as unaffordable
- **Severity**: CONFUSING (minor; does not corrupt state)
- **What I saw**:
  ```
  > {"cmd":"buy","what":"forest","n":0}
  {"ok": false, "error": "cannot afford 0 ha of coppice woodland (you have 400 denarii)"}
  > {"cmd":"state"}
  {"ok": true, "year": 100, "capital": 400.0, ..., "forest_ha": 0.0, ...}
  ```
  Unlike F1/F2, this one is at least honest — nothing is mutated — but
  buying zero of something costs zero denarii and should never be
  "unaffordable." It reads as an off-by-one on a `cost <= 0` guard that was
  presumably meant to catch exactly the negative-quantity case in F1, and
  instead swallows the harmless n=0 case into the same wrong branch.
- **Reproduce**:
  ```
  {"cmd":"buy","what":"forest","n":0}
  ```

### F9. `step` silently no-ops after the run has ended, while `start`/`buy` correctly refuse
- **Severity**: CONFUSING (minor)
- **What I saw**, after triggering the denunciation ending from F7:
  ```
  > {"cmd":"start","id":"units_standards"}
  {"ok": false, "error": "the run has ended (denounced: as a sorcerer); nothing more can be started"}
  > {"cmd":"buy","what":"forest","n":1}
  {"ok": false, "error": "the run has ended (denounced: as a sorcerer); nothing more can be bought"}
  > {"cmd":"step","years":1}
  {"ok": true, "completed": [], "events": [], "year": 101, ...}
  ```
  `start` and `buy` both correctly detect the terminal state and refuse with
  a clear, specific error. `step` instead returns `"ok": true` and quietly
  does nothing (no year change, no completions, no events) rather than
  returning the same kind of "run has ended" error. It's harmless — nothing
  advances — but it's an inconsistent contract: two of three mutating
  commands tell you the game is over, one just pretends to comply.
- **Reproduce**: reach any ending (e.g. the F7 mass-start denunciation, or
  `step years=100000` to exhaust the horizon), then issue `step` again.

### F10. WORKS-WELL — bounty pricing matches its documentation exactly
- **Severity**: WORKS-WELL
- **What I saw**: `04_ECONOMICS.md` documents bounties as "about 2.5x the
  honest cost," "65% hours saved," "none" supervision cost, and "+2
  suspicion." I built up to a bounty-eligible, prerequisite-satisfied node
  (`lens_grinding`, via `identity_cover` -> `patron_local` ->
  `workshop_first`) and posted a bounty on it:
  ```
  > {"cmd":"why","id":"lens_grinding"}
  {..., "cost": {"total": 1891.0}, "bounty_eligible_by_type": true, ...}
  > {"cmd":"state"}
  {"ok": true, ..., "capital": 12741.6, "suspicion": 0.0, ...}
  > {"cmd":"bounty","id":"lens_grinding"}
  {"ok": true, "posted": "lens_grinding", "price": 4727.5, "capital": 8014.1}
  > {"cmd":"state"}
  {"ok": true, ..., "capital": 8014.1, "suspicion": 2.0,
   "active": {"lens_grinding": {"founder_hours_left": 210.0, "founder_hours_total": 600.0, "spent": 4727.5, "bountied": true}}}
  ```
  `4727.5 / 1891.0 = 2.5` exactly. `12741.6 - 4727.5 = 8014.1` exactly —
  capital debited to the denarius. `210.0 / 600.0 = 0.35`, i.e. exactly 65%
  of the founder-hours requirement was waived. `suspicion` moved by exactly
  +2.0. Every number the documentation promises, the protocol delivered,
  precisely.
- **Why it's right**: I went into this expecting to find a mismatch (I'd
  just found one for `hot_air_balloon` in F5) and instead found the
  documented formula reproduced to the decimal. I also confirmed `bounty`
  on a non-eligible node (`tx2_watch_case`, tier 1 consumer_goods) and on a
  node with missing prerequisites (`point_contact_transistor`) both fail
  with clear, correct reasons that match what `why` already told me.
- **Reproduce**: the sequence above, from a fresh civ.

### F11. WORKS-WELL — `available`, `start`, `why`, and `bounty` never contradicted each other
- **Severity**: WORKS-WELL
- **What I saw**: I fetched the full `available` list from a fresh state
  (295 entries) and issued `start` for every single one of them in a single
  batch. All 295 returned `ok: true` — no case where `available` listed
  something `start` then refused for a missing-prerequisite reason (the
  brief's specific worry). Separately, for the goal node itself,
  `path`, `why`, and `bounty` all agreed on the identical missing-prereq set
  in the same run:
  ```
  {"cmd":"path","id":"point_contact_transistor"} -> remaining includes galena_detector, gp_whisker_forming, ...
  {"cmd":"why","id":"point_contact_transistor"}  -> missing_prerequisites: [galena_detector, gp_whisker_forming, micrometer_gauges, prc_lapping_plate, quantum_solidstate_theory, single_crystal, vacuum_tube]
  {"cmd":"bounty","id":"point_contact_transistor"} -> {"ok": false, "error": "missing prerequisites: galena_detector, gp_whisker_forming, micrometer_gauges, prc_lapping_plate, quantum_solidstate_theory, single_crystal, vacuum_tube"}
  ```
  Word-for-word identical prerequisite sets from three independent code
  paths.
- **Why it's right**: this is exactly the contradiction the brief asked me
  to hunt for, and across every id I tried (295 available starts plus the
  unreachable goal node) I could not produce one.
- **Reproduce**: `{"cmd":"available"}` then `start` on every returned id
  from a fresh civ; separately, run `path`/`why`/`bounty` on
  `point_contact_transistor`.

### F12. WORKS-WELL — stopping a project loses progress and the money already spent; restarting does not refund either
- **Severity**: WORKS-WELL
- **What I saw**:
  ```
  start units_standards -> founder_hours_needed 300.0
  step 1 -> active.units_standards = {founder_hours_left: 150.0, spent: 184.0}
  stop units_standards -> {"ok": true, "stopped": "units_standards"}
  state -> capital unchanged at 0.0 (the 184.0 already spent was not refunded), active {} (project gone)
  start units_standards -> {"ok": true, ...}
  state -> active.units_standards = {founder_hours_left: 300.0, spent: 0.0}  (back to full cost, no discount)
  ```
  I also confirmed `start` on an already-active project is rejected
  (`"already active"`), `stop` on an inactive one is rejected
  (`"not active"`), and `stop` on a made-up id is rejected the same way —
  no crash, no partial state change.
- **Why it's right**: this closes off an obvious exploit path (start, stop
  right before a bad outcome, restart for free) that a lot of games get
  wrong. Money already spent stays spent, and hours already worked are not
  banked.
- **Reproduce**: the sequence above, from a fresh civ.

### F13. WORKS-WELL — time-step boundaries are handled without crashing or overflowing
- **Severity**: WORKS-WELL
- **What I saw**:
  ```
  {"cmd":"step","years":0}     -> {"ok": false, "error": "years must be >= 1"}
  {"cmd":"step","years":-5}    -> {"ok": false, "error": "years must be >= 1"}
  {"cmd":"step","years":100000} -> {"ok": true, ..., "year": 600, "ended": true,
                                     "end_reason": "ran out of horizon (600 AD) without reaching the goal"}
  ```
  A step of 100,000 years does not try to actually simulate 100,000 years or
  overflow anything; it correctly recognises the civ's 500-year horizon (100
  AD -> 600 AD) and clamps the run to a clean ending. Zero and negative
  years are both rejected with the same clear message rather than being
  silently clamped to 1 or causing a divide-by-zero somewhere in a
  per-year loop.
- **Reproduce**: the three commands above, in any order, from a fresh civ.

### F14. CONFUSING — the "did you mean" suggestion for a bad node id always says "no idea," even for an obvious one-letter typo
- **Severity**: CONFUSING (minor)
- **What I saw**:
  ```
  > {"cmd":"why","id":"units_stadards"}
  {"ok": false, "error": "unknown node 'units_stadards'. did you mean: no idea"}
  > {"cmd":"why","id":"xyzzy_totally_wrong"}
  {"ok": false, "error": "unknown node 'xyzzy_totally_wrong'. did you mean: no idea"}
  ```
  `units_stadards` is a transposition of two letters away from the real,
  very common id `units_standards`, which I'd started successfully minutes
  earlier in the same testing session. Any reasonable fuzzy-match (edit
  distance, prefix match) should surface it. Instead the literal string
  `"no idea"` is printed as if it were the suggestion, for every bad id I
  tried, close typo or wildly wrong string alike.
- **Why it's wrong**: it's not a crash and it doesn't corrupt anything, but
  it reads like a template bug — either the suggestion feature was never
  actually wired up to a real matcher and "no idea" is a leftover
  placeholder, or the matcher's threshold is so tight it never fires. A
  real player typing a near-miss id gets no help finding the right one.
- **Reproduce**:
  ```
  {"cmd":"why","id":"units_stadards"}
  ```

## Honesty note

I did not attempt a "real" playthrough toward the goal node and have no
opinion on whether the game is winnable in the sense the other roles are
testing — that wasn't my job this session. Every number above is copy-pasted
from an actual transcript (some passed through a small Python pretty-printer
to collapse the 139-item `completed` lists for readability; the underlying
JSON lines are unedited). Where I couldn't get a clean state (the founder-
mortality check, F-not-numbered below) I say so rather than rounding it up
into a confirmed bug.

One more observation I want to flag honestly rather than number as a hard
finding, because I could not rule out that it needs a trigger I didn't find:
I stepped a fresh civ straight from year 100 to the year-600 horizon (`step
years=100000`) with no projects ever started, and the event log recorded two
named pandemics ("Antonine plague," "Plague of Cyprian," each "staff -28%"),
repeated fires, banditry, and the "Third century crisis" sacking sites
multiple times — but `founder_alive` was still `true` at year 600, five
hundred years after arrival, and no event ever mentioned the founder
specifically. `00_BRIEFING.md` states founder survival is *the* central
constraint of the game ("10 years survive: 0% success... 45 years: 88%"), so
either founder mortality isn't wired into this "agent" JSON-protocol mode at
all, or it needs a precondition (an active risky project, a specific
civilization setting, a different seed) that a 500-year idle step never
satisfies. I'm reporting the observation rather than a diagnosis: a founder
who is provably immortal against two plagues and three and a half centuries
of crisis, in the one mode a real player would actually use, is either a
major realism gap or a mechanic that simply never got exercised by anything
I tried.
