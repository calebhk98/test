# norse_900ad / BREAK

## What I did

I drove `python3 rome/sim/simulator.py agent --civ norse_900ad` (mostly with
`--seed` fixed so results are reproducible) purely through the documented
JSON protocol on stdin/stdout. I wrote a small Python harness that spawns the
process and feeds it one JSON object per line, reading back one reply per
line — this is exactly "writing your own script that pipes commands into it"
that BRIEF.md explicitly allows; I never imported `simulator` as a module,
never called `load_strategy`/`Sim` directly, never touched `run`, `compare`,
`sensitivity`, `sweep`, `path`/`why`/`costs` as CLI verbs, or `treetool.py`,
and I did not read `rome/data/strategies/`. I read `rome/data/tech_tree.json`
exactly twice, both times only to check a specific claim the game itself had
just made me doubt (see F1 and F5 below), and I say so at each point — I did
not use it to plan a route to the goal.

Given the brief for this civilization ("poorest, smallest population, price
index 1.4, almost no state capacity... everything scaled by population,
revenue or state capacity is at its limit here"), I did not attempt a WIN
run. I spent the session on: (1) re-testing every item on the "already
fixed" list against this specific civ's numbers, since a fix proven on Rome
or Han China does not necessarily hold at Norse's extreme small-number end;
(2) the mine and forest economy at a scale this civ cannot really afford;
(3) deliberately engineering insolvency and watching the abandonment/
mothballing mechanics in detail, denarius by denarius; (4) `knowledge_risk`
against what the civ's own hazard list says can actually happen to it; (5)
boundary and malformed-input attacks — non-string ids, negative and huge
quantities, non-object top-level JSON, and querying every node `available`
returns via `why` in bulk, which is how I found the two crash bugs below.

The most consequential turn in the session: while systematically calling
`why` on every id in `available`'s first batch (a boring, mechanical sweep,
not a clever attack), the process died outright on `mat_obsidian_blade`. I
checked the raw tree file to see whether this was one bad node or a wider
gap (see F1) and found it also affects two of this civ's own four starting
technologies — so a Norse player asking `why` about the shipbuilding or
ironworking they supposedly start with crashes their own game on the first
question they would naturally ask.

## Result

I never pursued the transistor goal — this was a BREAK pass. Across several
separate seeded runs I: ran a fresh civ to the year-1400 horizon untouched
(`end_reason: "ran out of horizon (1400 AD) without reaching the goal"`, no
crash, no sacking ever fired — see F5); deliberately bankrupted a run via an
oversized mine and watched capital get clamped to exactly `-revenue()` twice
in a row (F4); and found two independent, fully reproducible whole-process
crashes (F1, F2) that would end a real player's session with no save state,
since the protocol has no persistence between invocations.

Starting state for every run below (fresh `norse_900ad`, seed noted per
finding): year 900, capital 400.0, founder_hours_available 2400.0, artisans
3.0, scholars 1.0, `done_count: 4` (all four `starting_techs` — sea clinker
hull, deep keel, bog-iron bloomery, open-ocean navigation — matching the civ
file exactly, and `done_granted: 4 / done_earned: 0`, so the earlier
Han-China fix for granted-vs-earned starting techs generalizes correctly to
Norse; no `WARNING: ... starting technologies that do not exist` appeared on
stderr, so none of Norse's four starting techs are silently dropped — see
WORKS-WELL note under F1).

## FINDINGS

### F1. `why` on a real, currently-available node kills the whole process — and it hits two of Norse's own four starting technologies
- **Severity**: BUG, critical (crash)
- **What I saw**: Sweeping `why` across everything `available` returns on a
  fresh run (`--seed 1`):
  ```
  {"cmd":"available"}
  -> {"count": 319, "available": [... "mat_obsidian_blade" ...]}
  {"cmd":"why","id":"mat_obsidian_blade"}
  ```
  produced no JSON reply at all — just this on stderr, and the process exited
  (returncode 1):
  ```
  Traceback (most recent call last):
    File ".../rome/sim/simulator.py", line 2907, in <module>
      sys.exit(main() or 0)
    File ".../rome/sim/simulator.py", line 2901, in main
    File ".../rome/sim/simulator.py", line 2624, in cmd_agent
      resp = _agent_dispatch(s, nodes, cmd)
    File ".../rome/sim/simulator.py", line 2429, in _agent_dispatch
      return dict(ok=True, **_node_explain(s, nodes, k))
    File ".../rome/sim/simulator.py", line 2384, in _node_explain
      "suspicion": n["sus"], "state_interest_trait_score": n["gov"],
                   ~^^^^^^^
  KeyError: 'sus'
  ```
  I doubted this was a one-off, so (per BRIEF.md's exception) I opened
  `rome/data/tech_tree.json` to check the specific claim that this node's
  record is missing fields, and confirmed it: `mat_obsidian_blade`'s node
  object in the tree has no `"sus"` and no `"gov"` key at all (every other
  field a normal node has is present — `ph`, `cap`, `rev`, `up`, `risk`,
  `traits`, etc.). I then counted across the whole tree: of 2,828 nodes,
  exactly 7 are missing both `sus` and `gov`:
  `exp_import_draught_animals, fud_chinampa, civ_monumental_stone,
  mat_obsidian_blade, sea_clinker_hull, sea_keel_deep,
  met_bloomery_bog_iron`.
  Three of those seven are **Norse's own starting techs**. Confirmed live,
  fresh run, first command after `state`:
  ```
  {"cmd":"why","id":"sea_clinker_hull"}
  -> KeyError: 'sus'  (process dead, zero JSON output)
  {"cmd":"why","id":"met_bloomery_bog_iron"}
  -> KeyError: 'sus'  (process dead, zero JSON output, separate fresh run)
  ```
- **Why it is wrong**: `_node_explain` (`rome/sim/simulator.py` ~line 2384)
  reads `n["sus"]` and `n["gov"]` with plain dict indexing instead of
  `.get(..., 0)`, so any node missing those keys is a guaranteed, unguarded
  crash of the entire interpreter process, not a contained error. This is
  the exact failure class the brief lists as "already fixed" — a malformed
  *command* used to kill the whole process on a non-string id, and that hole
  was closed with a central guard in `_agent_dispatch`. But that guard only
  protects against a bad *command*; it does nothing for a well-formed
  command against bad *data*, which is what this is. `why` and `available`
  are the two commands the brief singles out as ones a player should use
  freely to decide what to do next, and `available` unconditionally lists
  `mat_obsidian_blade` (and, for Norse, all three of its broken starting
  techs) as things you can legally ask about. There is no way for a player
  to know in advance which ids are landmines, and once the process dies
  there is no save state — the entire run, including everything already
  built, is gone. For Norse specifically this is not an edge case: `why` on
  either of two named starting advantages (the shipbuilding, the
  ironworking) that the civ's own blurb advertises ("superb shipbuilding and
  ironworking") is a completely natural first question, and it is fatal.
- **Reproduce**:
  ```
  python3 rome/sim/simulator.py agent --civ norse_900ad --seed 1
  {"cmd":"why","id":"sea_clinker_hull"}
  ```
  Single command, fresh run, first line after start. Crashes immediately
  with `KeyError: 'sus'` and no JSON reply at all. `met_bloomery_bog_iron`
  and `mat_obsidian_blade` reproduce identically.
- **Also confirmed WORKS-WELL nearby**: the *previous* fix this generalizes
  from held up: no starting-tech id for Norse is silently dropped (no
  stderr warning on a fresh run, and `done_count` at turn zero is exactly 4,
  matching `len(starting_techs)` in `rome/data/civilizations/norse_900ad.json`
  precisely), and `done_granted`/`done_earned` correctly puts all four in
  `granted` (`done_granted: 4, done_earned: 0` before any action), so the
  Han-China "starting techs get exposed to sacking as if you'd personally
  discovered them" bug is genuinely fixed for Norse too.

### F2. A syntactically-valid top-level JSON value that isn't an object kills the process one command later — the exact "one bad line kills the game" bug, reopened via a different code path
- **Severity**: BUG, critical (crash)
- **What I saw**: Any JSON line whose top-level value parses fine but is not
  a `{...}` object (a bare `null`, a bare number, a bare string, a bare
  list) gets a *polite, correct-looking* reply for that line, then silently
  kills the process before the *next* line is even read:
  ```
  $ printf '%s\n%s\n' 'null' '{"cmd":"state"}' \
      | python3 rome/sim/simulator.py agent --civ norse_900ad --seed 1
  {"ok": false, "error": "each line must be a JSON object with a 'cmd' field, e.g. {\"cmd\":\"state\"}"}
  Traceback (most recent call last):
    File ".../rome/sim/simulator.py", line 2907, in <module>
      sys.exit(main() or 0)
    File ".../rome/sim/simulator.py", line 2901, in main
    File ".../rome/sim/simulator.py", line 2626, in cmd_agent
      if cmd.get("cmd") == "quit":
         ^^^^^^^
  AttributeError: 'NoneType' object has no attribute 'get'
  ```
  I confirmed the same shape with a bare list (`[1,2,3]`), a bare number
  (`42`), and a bare string (`"hello"`) — same traceback, same line number,
  only the type name in the `AttributeError` changes (`'list'`, `'int'`,
  `'str'`). In every case the FIRST reply looked completely fine — `ok:
  false` with a sensible, actionable error message that gives no indication
  anything is wrong — and the crash only becomes visible when the *next*
  command gets no reply at all.
- **Why it is wrong**: `_agent_dispatch` (line ~2405) does correctly guard
  against a non-dict `cmd`, returning a clean error — that is the fix the
  brief lists as already done for "a non-string `id` killing the whole
  process." But the REPL driver loop in `cmd_agent` that calls it (line
  ~2613-2626) does its own, second, unguarded access to the same raw parsed
  value immediately afterward: `if cmd.get("cmd") == "quit": break`. For
  `cmd == None`/a list/a number/a string, `.get` does not exist and the
  process dies right there, one statement after `_agent_dispatch` had
  already handled the very same malformed value safely. The dispatcher's
  fix did not reach this second, independent, un-guarded use of the same
  variable, so the whole class of bug the brief says was already closed is
  open again through a different door — and this one is arguably worse,
  because the first reply masks it: nothing about `{"ok": false, "error":
  "each line must be a JSON object..."}` tells the caller the process is
  about to die on their very next line, whatever it is.
- **Reproduce**:
  ```
  printf '%s\n%s\n' 'null' '{"cmd":"state"}' \
      | python3 rome/sim/simulator.py agent --civ norse_900ad --seed 1
  ```
  Also reproduces with `[1,2,3]`, `42`, or `"hello"` in place of `null`.

### F3. Topping up a mine investment before it matures resets the maturation clock for the WHOLE pending batch, so realistic incremental funding never commissions any capacity at all
- **Severity**: BUG, severe (this is close to the exact opposite of the
  already-fixed "freeing untrained people skips the training lag" exploit —
  here, the lag never ends)
- **What I saw**: A single `buy mine` commissions correctly and on time when
  left alone:
  ```
  {"cmd":"buy","what":"mine","material":"iron","n":100000}
  -> {"ok": true, "commissioned_t_per_yr": 4.76, "ready_year": 903.0, "capital": 0.0}
  {"cmd":"step","years":1}  x4, no further buys
  -> year 901..903: mine_capacity: {}
  -> year 904: mine_capacity: {"iron": 4.8}     (correct: ready_year 903 -> commissions on the step that carries 903 into 904)
  ```
  But Norse's whole premise is that you are *capital-constrained*, not
  ceiling-constrained (state_capacity 0.15, poorest civ in the set), so the
  ordinary, sensible thing to do — top up the same mine every year with
  whatever spare capital you have, since you can never afford the ceiling in
  one shot — never lets it commission at all:
  ```
  (loop: while capital > threshold, buy mine iron n:100000 every step)
  year 901  cap=-210.0  mine_cap={}  buy_ready=903.0
  year 902  cap=220.7   mine_cap={}  buy_ready=None   (capital too low that check to buy)
  year 903  cap=751.1   mine_cap={}  buy_ready=905.0
  year 904  cap=751.1   mine_cap={}  buy_ready=906.0
  year 905  cap=615.9   mine_cap={}  buy_ready=907.0
  ...
  year 960  cap=676.0   mine_cap={}  buy_ready=962.0
  ```
  60 straight years, every single one funded with real capital (the `buy`
  call reports `ok:true` and a rising `ready_year` almost every time), and
  `mine_capacity` never once leaves `{}`. The mine never earns a single
  tonne of capacity in 60 years despite being paid for every year.
- **Why it is wrong**: `open_mine()` (`rome/sim/simulator.py` ~line 1104)
  stores all not-yet-mature investment in one pooled `mine_pending[mat]`
  number with a single `mine_ready[mat]` date, and sets that date with
  `self.mine_ready[mat] = max(self.mine_ready.get(mat, 0.0), self.year +
  MINE_LEAD_YEARS)`. Because it's a `max()` against "now + 3 years" rather
  than something tied to the specific tranche just bought, ANY top-up before
  the pool matures pushes the *entire pool's* maturity — including money
  invested years earlier — three more years into the future. A player who
  is capital-constrained (exactly Norse's condition) and does the obviously
  correct thing — invest spare capital in the mine you're building whenever
  you have some, rather than sitting on cash — is caught in a trap where
  ordinary play perpetually defers the payoff and the capacity never
  arrives. Nothing in the `buy` reply warns that this top-up reset the
  clock on money already committed; `ready_year` just quietly creeps forward
  by exactly one year per step, forever, and the only way to actually get
  the capacity is to know to STOP buying and wait, which the protocol never
  suggests.
- **Reproduce**:
  ```
  python3 rome/sim/simulator.py agent --civ norse_900ad --seed 1
  {"cmd":"state"}
  # then, every year: if capital > 50, buy mine iron n:100000, then step 1 year
  ```
  `mine_capacity` stays `{}` indefinitely as long as top-ups continue before
  each batch matures; stop buying and it commissions on schedule.

### F4. The insolvency floor forgives debt down to exactly `-revenue()` in one step, as long as you hold ANY nonzero mine capacity — verified to the cent, twice in a row
- **Severity**: EXPLOIT / BUG, severe
- **What I saw** (`--seed 1`, deterministic): grew capital passively for 200
  years doing nothing, then spent everything on one oversized copper mine:
  ```
  {"cmd":"step","years":200}                 -> year 1100, capital 32167.5, revenue 1022.4
  {"cmd":"buy","what":"mine","material":"copper","n":1000000}
  -> {"ok": true, "commissioned_t_per_yr": 95.74, "ready_year": 1103.0, "capital": 0.0}
  {"cmd":"step","years":1} x7:
  year 1101  cap=751.10   mine_cost=0.00     mine_cap={}
  year 1102  cap=1490.90  mine_cost=0.00     mine_cap={}
  year 1103  cap=2219.60  mine_cost=0.00     mine_cap={}
  year 1104  cap=2937.40  mine_cost=7371.70  mine_cap={'copper': 95.7}
  year 1105  cap=-41.50   mine_cost=3685.90  mine_cap={'copper': 47.9}   [MOTHBALLED half the copper workings]
  year 1106  cap=-1022.40 mine_cost=1842.90  mine_cap={'copper': 23.9}   [MOTHBALLED half the copper workings]
  year 1107  cap=-1022.40 mine_cost=921.50   mine_cap={'copper': 12.0}   [MOTHBALLED half the copper workings]
  ```
  Note `capital` at year 1106 AND year 1107 is exactly `-1022.40` — exactly
  `-revenue()` to the cent, on two separate steps with different amounts of
  mine capacity mothballed in between. Hand-checking year 1106 from the
  reported numbers: start capital -41.5, +1022.4 revenue, -271.3ish living
  cost, -3685.9 mine opex (still charged at the OLD 47.9t capacity) puts raw
  capital at roughly -2976.3 before any mothballing. Mothballing then halves
  copper 47.9->23.9 and refunds `23.95 * 55 * 1.4 = 1843.85`, landing at
  about -1132.5 — still clearly below -1022.4. The reported figure is
  exactly -1022.4 anyway.
- **Why it is wrong**: `mothball_mines()` (`rome/sim/simulator.py` ~line
  1168) ends with an unconditional line, run every single time it is
  called, regardless of how much was actually recovered by halving mines:
  `self.capital = max(self.capital, -abs(self.revenue()))`. This is not a
  consequence of mothballing math — it is a hard floor bolted on afterward
  that manufactures however much money is needed to make the deficit stop
  at `-revenue()`, and it fires as long as `self.mine_capacity` is
  non-empty at all (the caller guard is `if self.capital < 0 and
  self.mine_capacity: self.mothball_mines()`), independent of whether the
  deficit came from the mine or from something else entirely (living cost,
  upkeep, a shock). In this run the forgiven amount was a modest ~110
  denarii; the mechanism does not scale-check at all, so the same code path
  would forgive an arbitrarily large deficit — accrued from ANY source — the
  moment a player happens to be holding even a token amount of mine
  capacity (a single tonne is enough to make `self.mine_capacity`
  non-empty and trigger the clamp). A player who deliberately keeps even a
  trivial 1-tonne coal mine open at all times effectively cannot go below
  `-revenue()` capital ever again, no matter how reckless their other
  spending is — a free, permanent insurance policy the insolvency mechanic's
  own design comments (which describe a *deliberately survivable but real*
  cost — staff bleed, works abandoned) explicitly say should not exist ("the
  consequence is deliberately the realistic one... nobody arrests you for
  debt" is not the same claim as "your debt cannot exceed X denarii if you
  happen to own a mine").
- **Reproduce**: exactly the command sequence above (seed 1). The two
  `-1022.4` readings at years 1106/1107 are the signature; they persist
  across differing amounts of mothballed capacity, which is only possible
  if the floor, not the mothballing math, is what set the final number both
  times.

### F5. `knowledge_risk` reports a live, nonzero sacking risk and suggests hedging against it for the entire 500-year game, even though Norse's only hazard can never sack a site
- **Severity**: CONFUSING / BUG
- **What I saw**: Turn zero, fresh run:
  ```
  {"cmd":"state"}
  -> "knowledge_risk": {"technologies_at_risk": 1, "loss_chance_if_a_site_is_sacked": 0.8,
       "fraction_lost_when_it_happens": 0.4, "expected_technologies_lost_per_sacking": 0.3,
       "hedged_by": null, "better_hedge_available": "corpus_dispersed",
       "known_hazards_ahead": [{"name": "Christianisation and political consolidation",
         "years": [995, 1100], "in_progress": false, "sacks_a_site": false,
         "sack_chance_per_year": null, "staff_loss": null,
         "note": "changes the value vector rather than killing people"}]}
  ```
  Note `known_hazards_ahead` correctly and honestly says `"sacks_a_site":
  false` for the one hazard Norse has — good, that part is right. But the
  top-level `expected_technologies_lost_per_sacking: 0.3` and the
  `better_hedge_available: "corpus_dispersed"` nudge are computed and shown
  unconditionally, every single time `state` is called, regardless of
  whether any hazard that could sack a site even exists for this
  civilization. I ran a fresh seed all the way to the horizon untouched to
  check:
  ```
  {"cmd":"step","years":100000}
  -> end_reason: "ran out of horizon (1400 AD) without reaching the goal", year: 1400
  ```
  Across the full 500-year run (22 logged events total — fires, banditry —
  see below), there is not one `"...sacked"` or `"KNOWLEDGE LOST"` event,
  because Norse's hazard list has no `sack_chance` key at all, and `_shocks`
  only fires a sacking when that key is present. At the very end of the run,
  with the one hazard long past (`known_hazards_ahead: []`, empty), the
  `knowledge_risk` block still reports `expected_technologies_lost_per_sacking:
  0.3` — a number describing an event with zero probability of ever
  occurring for this civilization, for the entire game, every time it is
  read.
- **Why it is wrong**: `knowledge_risk()` (`rome/sim/simulator.py` ~line
  809) computes `chance`/`frac`/`expected_technologies_lost_per_sacking`
  purely from whether the player holds `corpus_dispersed`/`corpus_written`
  and from `at_risk` (a straight count of tier>=2 done nodes), with no
  reference at all to whether the civ's hazard list contains anything with
  a `sack_chance` — the very thing `known_hazards_ahead`, three lines later
  in the same function, DOES check correctly. This is the exact bug the
  code's own docstring says it was built to fix ("the risk existed solely
  as prose... a tool that shows you one graph while the guide insists a
  second one governs you is a tool that misleads by omission") — except now
  it has reintroduced a milder version of the same shape of problem in the
  opposite direction: for Norse, the numeric risk fields overstate a threat
  that structurally cannot happen, and a player reading only the top-level
  numbers (not cross-referencing every entry in `known_hazards_ahead` by
  hand every time) would reasonably spend founder hours pursuing
  `corpus_dispersed` to defend against a sacking that will never come. Han
  China's report on this same mechanic marked it WORKS-WELL because Han's
  hazard (Yellow Turban) genuinely does sack sites and the numbers played
  out exactly as advertised; the mechanism is correct there but breaks for
  a civilization whose hazard doesn't sack sites at all, which is precisely
  Norse's case.
- **Reproduce**:
  ```
  python3 rome/sim/simulator.py agent --civ norse_900ad --seed 2
  {"cmd":"state"}                 # note knowledge_risk.expected_technologies_lost_per_sacking > 0
  {"cmd":"step","years":100000}   # runs cleanly to year 1400, end_reason "ran out of horizon"
  ```
  Grep the returned `events` list for "sack" or "KNOWLEDGE LOST": zero
  matches, for the entire game, on this civilization.

### F6. Buying slaves in several small calls is still measurably cheaper than one big call — the volume-surcharge fix is incomplete, not closed
- **Severity**: BUG (re-test of an "already fixed" item; regression/leak,
  not a full reopening)
- **What I saw** (`--seed 9`, identical starting capital both runs — grown
  to 15,310.4 den with 40 no-op `step` calls first, no purchases yet, so
  `market_pressure` is 0 going in for both):
  ```
  run A — one call:
  {"cmd":"buy","what":"slaves","n":12}
  -> {"ok": true, "bought": 12, "slaves": 12, "capital": 3800.2}
  total spent: 15310.4 - 3800.2 = 11510.2 denarii for 12 people

  run B — four calls of 3, no `step` between any of them:
  {"cmd":"buy","what":"slaves","n":3} -> capital 13552.6   (spent 1757.8)
  {"cmd":"buy","what":"slaves","n":3} -> capital 11395.2   (spent 2157.4)
  {"cmd":"buy","what":"slaves","n":3} -> capital 8868.5    (spent 2526.7)
  {"cmd":"buy","what":"slaves","n":3} -> capital 5990.9    (spent 2877.6)
  total spent: 1757.8 + 2157.4 + 2526.7 + 2877.6 = 9319.5 denarii for the same 12 people
  ```
  Slicing into four calls costs 9,319.5 against 11,510.2 for one call — a
  2,190.7 denarius, ~19%, discount for buying the exact same 12 people the
  exact same "instant" (no `step` in between, so the market has had no
  chance to restock), purely by the shape of the calls.
- **Why it is wrong**: `slave_quote()` prices an entire batch of size `n`
  at ONE surcharge rate, computed from the pressure level AFTER adding the
  whole batch: `surcharge = 1 + ((already + n_people) / depth) ** 0.85`,
  then `price = 300 * n_people * surcharge`. That correctly remembers
  pressure BETWEEN calls (`market_pressure` accumulates and is not reset,
  which is genuinely the fix for the original flat-price exploit — I could
  not get free people this way, and that part WORKS WELL), but WITHIN one
  batch it still charges every unit in the batch at the surcharge computed
  for the batch's endpoint, rather than integrating marginal cost across
  the batch. Splitting a large purchase into smaller ones therefore still
  approximates the true marginal cost curve more closely and comes out
  cheaper, in direct proportion to how finely you slice it — the smaller
  each call, the closer you get to true marginal pricing and the bigger the
  discount, right down to single-person calls. The fix closed the "reset
  between calls" hole but left the "batch-level flat rate versus marginal
  rate" hole in the same formula open; a player who buys people one at a
  time instead of in bulk still pays measurably less for the same
  headcount, delivered the same instant.
- **Reproduce**: as above, `--seed 9`, `--civ norse_900ad`, 40 `step`s of 1
  year each to reach identical capital with `market_pressure` at 0, then
  compare `buy slaves n:12` once against `buy slaves n:3` four times in a
  row with no `step` between them.

## Additional WORKS-WELL notes (attacked, could not break)

- **Negative and absurdly large `buy` quantities**: `buy forest n:-5` and
  `buy forest n:1e18` both correctly return `ok:false` with no state
  mutation (`capital`/`forest_ha` unchanged before and after). The fix for
  "negative quantity mints money" holds for Norse's 1.4 price index exactly
  as documented.
- **Non-string `id`**: `{"cmd":"why","id":{"a":1}}` and
  `{"cmd":"start","id":123}` both return a clean `ok:false` naming the wrong
  type, no crash, no state change. Holds for Norse.
- **Unicode node ids**: `{"cmd":"why","id":"☃🚀_unicode_test"}` returns a
  normal "unknown node" error, no crash.
- **Malformed single-line JSON** (`not json at all`, missing a closing
  brace, etc.) returns `{"ok": false, "error": "invalid JSON: ..."}` and the
  process survives to answer the next command — this is distinct from F2
  (a value that IS valid JSON but not an object); genuinely-invalid JSON
  text is handled correctly.
- **Manumission of untrained people**: bought slaves still queue through
  the full 3-year `TRAINING_YEARS` lag even after being freed; freeing an
  untrained person upgrades their eventual payout (0.55 -> up to 1.0) but
  does not move `ready_year` earlier and does not create a second credit. I
  also checked the multi-batch case (two separate `buy slaves` calls with
  different maturity dates, then a partial `manumit`): the total value
  added across all pending training rows always comes out to exactly `0.45
  * (people manumitted who were still untrained)`, split proportionally
  across whichever rows are pending, regardless of how many separate
  batches are in flight — I could not get a double credit or lose a
  fraction of a person this way.
- **`step`/`start`/`buy` after the game has ended**: all three correctly
  refuse with the end reason instead of silently no-opping, confirmed by
  actually running a fresh Norse civ to its year-1400 horizon and issuing
  each command afterward.
- **Conservation of `net_after_project_spend`**: once a project has been
  running for at least one full step, the `net_after_project_spend` value
  reported in one `state` call predicts the EXACT capital delta of the next
  `step` call, to the cent, across five consecutive years I checked
  (728.7 predicted / 728.7 actual, 717.8/717.8, etc.). The only place this
  does not hold is the very first step after `start`, where
  `project_spend_last_year` is still 0 because no step has run yet to
  populate it — an honestly-labeled cold-start gap, not a hidden
  inconsistency.
