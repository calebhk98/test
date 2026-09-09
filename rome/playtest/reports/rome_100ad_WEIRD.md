# rome_100ad / WEIRD

## What I did

I read the brief, `ROME_BOOTSTRAP.md`, `rome/knowledge/00_NONOBVIOUS_TRICKS.md`, `rome/knowledge/03_SOCIAL_POLITICS.md`
and the first part of `rome/knowledge/96_finance.md` for context, then drove the game entirely
through `python3 rome/sim/simulator.py agent --civ rome_100ad --kit <kit>` with hand-written
JSON piped over stdin, exactly as the protocol prescribes. I never called `run`, `compare`,
`sensitivity`, `sweep`, the CLI `path`/`why`/`costs`, or `treetool.py`, never imported
`simulator` as a module, and never opened `rome/data/strategies/` or the tech tree JSON. The one
exception, disclosed per the brief's own carve-out: I used `path` and `why` (the in-protocol
commands, explicitly allowed) to check the specific claim that `school_founded` and its
neighbouring institution nodes are not technically required for `point_contact_transistor` — the
guide says this in prose and I wanted to see the simulator's own dependency data confirm it
before repeating the claim. I did not open the JSON file itself.

My plan was to hunt for a money/labour pump first (the brief's "get rich doing nothing sensible"
lead), because `96_finance.md` reads like a shopping list of financial inventions and the
protocol exposes a raw `buy` command for `slaves` and `manumit` sitting right next to the
elaborate, costed, multi-year `freedman_staff` tech node that is supposed to be the *only*
legitimate way to build a free technical staff. That mismatch — a slow, expensive, narrated
institution next to a one-line free command that seems to do the same thing — was too obviously
promising to ignore, and it turned out to be the best thing I found all session.

I tested it at three scales (10, 500, 1000-3333 slaves) across two kits (`absurd`, 1,000,000
denarii; `destitute`, 0 denarii) and multiple seeds. I also checked whether the exploit actually
lets you skip the school/patronage chain the guide insists on, whether it breaks the founder's
personal-hours bottleneck, whether mines and forest purchases are priced with the same disregard
for scale, what a destitute start looks like in year one, and what "stop" and "bounty" do to
capital. The run that mattered most ended the game outright, in year 101, with a cause of death
I had not engineered and that is not mentioned anywhere in the accessible knowledge base.

## Result

No run reached the transistor; that was never the goal for this role. The most important single
data point is a full player death: starting from `--kit absurd` (1,000,000 denarii), a single
slave-buy-and-manumit cycle at n=3333 followed by one `step` call ended the game in year 101 with
`end_reason: "too eminent: brought down not for what you built but for how large you had become"`,
capital at **-150,096.5 denarii**, reputation 1298.1, eminence 220.56, and 139 technologies marked
done that I had never explicitly started. A moderate version of the same trick (n=500) survived
five years with reputation 205→85.9 (it decays) and eminence only reaching 7.15, so the exploit is
real at any scale but only fatal at the top of it.

## FINDINGS

### F1. Buying and instantly manumitting slaves mints reputation and labour from nothing, in zero calendar time
- **Severity**: EXPLOIT
- **What I saw**:
  ```
  {"cmd":"state"}
  {"cmd":"buy","what":"slaves","n":10}
  {"cmd":"state"}
  {"cmd":"buy","what":"manumit","n":10}
  {"cmd":"state"}
  ```
  ```
  {"ok": true, "year": 100, "capital": 1000000.0, ... "artisans": 3.0, "reputation": 5.0, ... "slaves": 0, "freedmen": 0, ...}
  {"ok": true, "bought": 10, "slaves": 10, "capital": 997000.0}
  {"ok": true, "year": 100, ... "artisans": 8.5, "reputation": 5.0, ... "slaves": 10, "freedmen": 0, ...}
  {"ok": true, "manumitted": 10, "freedmen": 10, "slaves": 0}
  {"ok": true, "year": 100, ... "artisans": 14.0, "reputation": 9.0, ... "slaves": 0, "freedmen": 10, ...}
  ```
  Buying does not touch reputation; **manumitting does**, immediately, for free (no capital charge,
  no founder-hours, no calendar time — `year` never advances). Scaling up to n=1000 confirms it is
  linear and repeatable up to whatever capital you have:
  ```
  {"cmd":"buy","what":"slaves","n":1000}  -> {"bought":1000,"slaves":1000,"capital":700000.0}
  {"cmd":"buy","what":"manumit","n":1000} -> {"manumitted":1000,"freedmen":1000,"slaves":0}
  {"cmd":"state"} -> {"artisans":1103.0, "reputation":405.0, ...}
  ```
  repeated three times (still year 100, still one `step` call away): reputation climbed
  405 → 805 → 1205, artisans 1103 → 2203 → 3303, for a flat, un-scaling 300 denarii per slave.
- **Why it is wrong**: `rome/knowledge/03_SOCIAL_POLITICS.md#freedman_staff` describes manumission
  as a deliberate, costed, multi-year institutional act ("Set the manumission term in advance and
  in public, five to seven years, and keep it exactly... Founder hours 900. Capital 2,000 den,
  upkeep 1,400 den/yr... Calendar 2 years"). The raw `buy manumit` protocol command does the same
  thing — frees slaves, and per the numbers above earns *more* reputation than the entire
  `patron_local` node buys you (a halving of suspicion, costing 1,200 capital and 400 founder
  hours) — for zero founder-hours, zero calendar time, and no prerequisite at all, not even
  `identity_cover`. A modern person cannot emancipate a thousand people from a standing start in
  a single instant and have Roman society register it as reputation before anyone has even met
  him. It also means the entire narrated `freedman_staff` node is strictly dominated: nothing in
  the protocol stops you from getting its output for free and faster.
- **Reproduce**: `python3 rome/sim/simulator.py agent --civ rome_100ad --kit absurd --seed 1`,
  then feed `{"cmd":"buy","what":"slaves","n":1000}` followed immediately by
  `{"cmd":"buy","what":"manumit","n":1000}`, then `{"cmd":"state"}`.

### F2. Slave purchases have no market depth or bulk pricing; mines do
- **Severity**: UNREALISTIC
- **What I saw**: 3,333 slaves bought in one instant call at a flat 300 denarii each
  (`{"cmd":"buy","what":"slaves","n":3333}` → `{"ok": true, "bought": 3333, "slaves": 3333,
  "capital": 100.0}` starting from 1,000,000), with no price increase, no annual cap, and no
  wait time — contrast with mines, which are throttled and delayed:
  ```
  {"cmd":"buy","what":"mine","material":"iron","n":10}
  {"ok": true, "commissioned_t_per_yr": 10.0, "ready_year": 103.0, "capital": 999400.0}
  {"cmd":"buy","what":"mine","material":"silver","n":10}
  {"ok": true, "commissioned_t_per_yr": 10.0, "ready_year": 103.0, "capital": 909400.0}
  ```
  Mines cost different amounts per material (silver ~150x iron per tonne/yr of capacity here) and
  take three years to come online regardless of how much you spend. The slave market has neither
  friction. I also confirmed the cap is purely "can you afford it": buying 100,000 slaves at once
  is refused only for insufficient funds (`"cannot afford 100000 slaves at 300 denarii each (you
  have 1000000 denarii)"`), never for market size.
- **Why it is wrong**: the Roman slave market was large but not infinite and not flat-priced —
  buying three thousand people in a single city in a single instant would move the price and take
  time neither of which the model charges for. The economics module (`96_finance.md`) is full of
  careful notes about market depth and trust-building elsewhere (bills of exchange, banking) that
  simply don't apply to the one purchase that turns out to matter most.
- **Reproduce**: same session as F1; compare with `{"cmd":"buy","what":"mine",...}` calls above.

### F3. Extreme use of the exploit gets you killed by an undocumented mechanic: "too eminent"
- **Severity**: BUG / CONFUSING (the mechanic itself is arguably WORKS-WELL — see F4)
- **What I saw**:
  ```
  {"cmd":"buy","what":"slaves","n":3333}
  {"cmd":"buy","what":"manumit","n":3333}
  {"cmd":"start","id":"units_standards"}
  {"cmd":"step","years":5}
  ```
  ```
  {"ok": true, "completed": [ ...139 nodes... ],
   "events": [{"year": 100, "message": "RUN ENDS: too eminent: brought down not for what you built but for how large you had become"}],
   "year": 101, "capital": -150096.5, "revenue": 666.7, "upkeep": 0.0,
   "artisans": 2734.51, "reputation": 1298.1, "eminence": 220.56, "protection": 0.3,
   "done_count": 139, "ended": true,
   "end_reason": "too eminent: brought down not for what you built but for how large you had become"}
  ```
  I grepped every file the brief allows me to read for the exploit's specific words:
  `grep -rn "eminen" rome/knowledge/ rome/*.md` returns **nothing**. `03_SOCIAL_POLITICS.md`
  (both copies) discuss "your own success" as a danger in prose (the Vespasian anecdote) but never
  name an `eminence` stat, never give a threshold, and never warn that a single large benefaction
  binge can end the game outright the same year it happens, with no chance to react — the message
  arrives in the same `step` response that caused it.
- **Why it is wrong**: a real player relying on the knowledge base (which the brief explicitly
  says "a real player would have") has no way to see this coming or to budget against it. The
  in-game `why` output for nodes never mentions eminence either — I checked `patron_local` and
  `identity_cover` specifically (F1 notwithstanding) and neither surfaces the concept. This is a
  fail-state with no signposting, which is a design/documentation gap even where the underlying
  check is reasonable.
- **Reproduce**: exact sequence above, `--civ rome_100ad --kit absurd --seed 1`.

### F4. The eminence check does cap the exploit at the top end — the game is not trivially winnable this way
- **Severity**: WORKS-WELL
- **What I saw**: the same trick at n=500 instead of n=3333 does **not** end the run:
  ```
  {"cmd":"buy","what":"slaves","n":500}
  {"cmd":"buy","what":"manumit","n":500}
  {"cmd":"start","id":"units_standards"}
  {"cmd":"step","years":5}
  ```
  ```
  {"ok": true, "completed": [...141 items...],
   "year": 105, "capital": 680781.3, "revenue": 1000.0, "upkeep": 30.0,
   "artisans": 129.57, "reputation": 85.9, "eminence": 7.15, ... "ended": false}
  ```
  Reputation and artisan counts also **decay** over time rather than staying pinned at their
  post-manumission peak (reputation 205→85.9, artisans 553→129.57 over five years with no further
  purchases), so the boost is a burst, not a permanent state you can bank.
- **Why it is right**: this is close to exactly what the brief asked me to hunt for under "become
  untouchable" — I found a lever that manufactures reputation for nearly nothing, and the game
  has a countervailing mechanic (rising `eminence`, an unforgiving one-shot end-state) that
  specifically punishes pulling that lever too hard, plus a decay that stops it from being a
  free permanent stat bank. It's exactly the "your own success can end you" thesis of
  `03_SOCIAL_POLITICS.md` actually enforced in code, even though (F3) it is not documented well
  enough for a player to predict the threshold.
- **Reproduce**: same as F1 but with n=500 instead of n=3333.

### F5. Founder-hours stay fixed at 2,400/yr no matter how many freedmen you buy — the exploit inflates the wrong resource for reaching the transistor
- **Severity**: WORKS-WELL
- **What I saw**: across every state dump in every test (0, 10, 500, 1000, 3333 slaves bought and
  manumitted), `"founder_hours_available": 2400.0` never changed. Only `artisans` and
  `reputation` moved.
- **Why it is right**: the guide's central claim is that the founder's own hours, not capital, not
  raw manpower, are the scarce resource that research-heavy nodes actually consume, and that
  scholars (gained mainly through the school) are what multiplies *that*. My attempt to use the
  slave/manumit pump as a shortcut around founding a school does not touch the one number that
  would actually matter for the deep tech chain. The exploit is real and can probably accelerate
  labour- and capital-heavy construction nodes for free, but it does not appear able to shortcut
  the calendar-floor-and-founder-hours bottleneck the guide says is the real gate.
- **Reproduce**: compare `founder_hours_available` across the `state` outputs quoted in F1.

### F6. The transistor's raw prerequisite chain really does not require the school or the deep patronage ladder — confirmed via `path`, matching the guide's own claim
- **Severity**: WORKS-WELL / CONFUSING (see caveat)
- **What I saw**: (`path` and `why` are explicitly allowed protocol commands per the brief.)
  ```
  {"cmd":"path","id":"point_contact_transistor"}
  ```
  returns `"remaining_count": 168` prerequisite nodes. I checked membership in that list for the
  social/institution nodes `03_SOCIAL_POLITICS.md` calls mandatory:
  `school_founded, collegium_licensed, freedman_staff, citizenship, patron_senatorial,
  patron_imperial, endowment_land, academy_network` — **all eight are absent** from the technical
  remaining-prerequisite list. Only `identity_cover` and `patron_local` (the two cheapest, earliest
  social nodes) appear in the 168, presumably because something further downstream needs them for
  an unrelated reason, not because the school chain does.
  I also tried starting `school_founded` directly with none of its prerequisites done:
  `{"cmd":"start","id":"school_founded"}` → `{"ok": false, "error": "missing prerequisites:
  arithmetic_positional, collegium_licensed, freedman_staff"}` — a normal, expected refusal, not a
  hard block on the strategy of skipping it forever.
- **Why it is right (with a caveat)**: this exactly matches `ROME_BOOTSTRAP.md`'s own claim —
  "Nothing in physics requires a patron, a school or citizenship... Bare topological order to the
  goal succeeds 0% of the time. The institution-first strategy succeeds 100%." The technical graph
  and the "real" graph (founder-hours, calendar floors, money) genuinely are different graphs, and
  the game does not lie about that. The caveat: I did not have session budget to actually attempt
  a full "never found a school" run to the transistor to see it fail for the founder-hours reasons
  the guide predicts — I only confirmed the prerequisite-graph claim, not the outcome claim. That
  would be the natural next test for a longer session.
- **Reproduce**: `{"cmd":"path","id":"point_contact_transistor"}` and
  `{"cmd":"start","id":"school_founded"}` from a fresh `--kit absurd` session.

### F7. Roughly 140 "Rome already has this" technologies complete for free in year one regardless of capital, kit, or what you started
- **Severity**: CONFUSING
- **What I saw**: in a **destitute** run (0 starting denarii), having done nothing but
  `{"cmd":"start","id":"identity_cover"}` and one `{"cmd":"step","years":2}`, the response listed
  139 completed nodes I never started — `sea_merchant_ships_large`, `civ_aqueduct_roman`,
  `mat_gold`, `fin_coined_money`, `civ_road_paved`, `mil_gunpowder_base`, `hom_public_bath`, and
  so on — alongside `identity_cover` itself, with `capital` unchanged at `0.0` throughout. The same
  set (with a couple of differences depending on kit) also appeared in every `absurd`-kit run I
  made. `done_count` jumped from 0 to 139-141 in a single step no matter the kit.
- **Why it is confusing rather than a bug**: these read as background/ambient civilizational
  technology Rome already possesses (roads, aqueducts, coined money, basic metals) rather than
  things the *player* invented, which is thematically defensible — the founder shouldn't have to
  "research" the wheel. But the protocol surfaces them in the same `completed` list, with the same
  shape, as the player's own deliberate `start`s, and `done_count` is a single undifferentiated
  number. A player using only the protocol (as the brief mandates) has no way to tell "things Rome
  already had" from "things I built" from the state alone, which makes it easy to over-credit your
  own progress, and it happens identically whether you are destitute or a millionaire, which is a
  strange thing for a supposedly struggling newcomer's civilization to hand you for free in year
  one regardless of his standing.
- **Reproduce**: `python3 rome/sim/simulator.py agent --civ rome_100ad --kit destitute --seed 1`,
  then `{"cmd":"start","id":"identity_cover"}` followed by `{"cmd":"step","years":2}`.

### F8. `start` and `stop` charge nothing up front; cost is only realized on completion
- **Severity**: WORKS-WELL (worth noting because it makes F1-style probing cheap and safe)
- **What I saw**:
  ```
  {"cmd":"state"} -> capital 1000000.0
  {"cmd":"start","id":"identity_cover"} -> {"ok": true, "started": "identity_cover", ...}
  {"cmd":"stop","id":"identity_cover"} -> {"ok": true, "stopped": "identity_cover"}
  {"cmd":"state"} -> capital 1000000.0  (unchanged)
  ```
- **Why it is right**: this is sensible — you shouldn't be charged for a project you abandon
  before finishing it — and it also means a player can safely `start` something just to read its
  `founder_hours_needed`/`calendar_floor_years` and then `stop` it with no penalty, which is a
  reasonable, low-risk way to explore the tree through the protocol instead of reading the JSON
  directly.
- **Reproduce**: sequence above, any kit.

## Honesty note

I did not attempt a full multi-century run to the transistor in either direction (institution-first
or bare-topological). Given the session's purpose (WEIRD/exploit-hunting, not a full playthrough)
I judged that chasing the single biggest rules-hole (F1/F2/F3) to a confirmed, reproducible,
game-ending result was the higher-value use of the budget than a long grind toward the goal node.
F6's caveat is the one place I'm explicitly flagging an untested prediction rather than an observed
result.
