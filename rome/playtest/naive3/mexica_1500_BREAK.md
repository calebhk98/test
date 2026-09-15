# Playtest notes: mexica_1500 (fog) — session naive3

Tester: Claude (agent), session BREAK
Rules followed: interact only with the running program via its own interface/output.
No source, data files, or docs were read. No repo files modified except this notes file.

Command used to start:
```
cd /home/user/test
python3 rome/sim/simulator.py agent --civ mexica_1500 --fog --session /home/user/test/rome/playtest/naive3/mexica_1500_BREAK.json
```

---

## Setup
Ran simulator as a persistent background process, feeding commands through a FIFO and reading a log file, so I can send many JSON commands across tool calls in this environment. This does not touch the repo except the session json the program itself writes.

## Initial state
Expect: starting state at year 1500, some starting capital, no employees.
Command: {"cmd":"state"}
Actual (trimmed key fields): year 1500, capital 400.0, revenue 232.6, living_cost 230.0, net_per_year 2.7, founder_hours_available 2400.0, reputation 5.0, done_count 128 (done_granted 128, done_earned 0), credit_limit 1093.0, debt_interest_rate 0.1183, fog_of_war true, manual true, ended false.

Interesting immediately: "done_count": 128 with "done_granted": 128 and "done_earned": 0 at the very start of the game, before I have done anything. Need to investigate what "done" means (finished projects/techs?) — if it means completed technologies/projects, having 128 already done before any turn looks odd. Will check with `why` / `help` once I find the right topic.

## Command discovery
`{"cmd":"help","topic":"commands"}` lists: state, available, why, start, stop, step, money, quote, close, risk, labour, hire/fire/train/commission, buy, work, bounty, mothball/restore, bribe, policy, path (not available under fog), save/load, help, quit.

`{"cmd":"available"}` at turn 0: 83 things visible, grouped by subject (finance, roads/bridges/canals, household, farming, power and precision, textiles, agriculture and food, medicine and biology, the remaining arts, signals and media, glass and optics, the briefing, society and politics, metallurgy, electricity, printing and information). Cheapest available: hom_eraser_breadcrumb at cost 4.0.

Re "done_count": 128 at turn 0 — checked `why hom_eraser_breadcrumb` (an available, not-done item) and it correctly reports "done": false. So done_count=128 is plausibly pre-granted background knowledge/starting techs for the civ, not a bug. Not filing as a defect, but noting it was initially confusing that a fresh game reports 128 things already "done". Would want a `{"cmd":"help","topic":"done"}` or similar to explain this line in `state` output; none was offered in the four-things primer.

## Input validation probes
Expect: step with negative years should be rejected; step 0 rejected; step beyond horizon (500 years remain to 2000) rejected with a helpful message; start of an unknown id rejected; why of an unknown id rejected.

Actual, all as expected, clean error messages, no crash:
- `{"cmd":"step","years":-5}` -> `{"ok": false, "error": "years must be >= 1"}`
- `{"cmd":"step","years":0}` -> `{"ok": false, "error": "years must be >= 1"}`
- `{"cmd":"step","years":100000}` -> `{"ok": false, "error": "there are only 500 years left before the horizon at 2000. Ask for 500 or fewer, or fewer still if you want to see what happens on the way."}`
- `{"cmd":"start","id":"nonexistent_thing_xyz"}` -> `{"ok": false, "error": "unknown node id 'nonexistent_thing_xyz'. use {\"cmd\":\"available\"} or {\"cmd\":\"why\",\"id\":...} to find valid ids"}`
- `{"cmd":"why","id":"nonexistent_thing_xyz"}` -> `{"ok": false, "error": "unknown node 'nonexistent_thing_xyz'. did you mean: no idea"}` (deliberately funny flavour text, not a bug)

No crash / no bad-state mutation observed from any of these. Good robustness so far.

## step: fractional years silently truncated
Expect: `step` takes a `years` value; docs say "let time pass", four-things primer example is `{"cmd":"step","years":5}` (an integer). I expected either (a) fractional years rejected like negative/zero years are ("years must be >= 1" covers <1 but does not say "must be an integer"), or (b) fractional years honoured to fractional-year precision, since money/reputation/etc are all reported to 1 decimal place and clearly accrue continuously.

Actual: fractional years are silently floored to an integer and the request is otherwise treated as success, with no note that less time passed than requested:
- `{"cmd":"step","years":1.5}` from year 1500 -> year 1501 (+1)
- `{"cmd":"step","years":2.5}` from year 1501 -> year 1503 (+2)
- `{"cmd":"step","years":1.99}` from year 1503 -> year 1504 (+1, not +2)
- `{"cmd":"step","years":0.999}` -> rejected: `{"ok": false, "error": "years must be >= 1"}`

So years=1.99 is silently treated as years=1 (a ~50% shortfall from what was asked), while years=0.999 is rejected outright. The boundary is inconsistent (floor to 0 is an error, floor to 1..N is silently accepted) and the reply JSON never says how many years actually elapsed vs. requested — the caller has to diff `year` before/after to notice. This could quietly cost a player who is fine-tuning around an event or deadline (e.g. stepping 4.5 years hoping to land partway through year 5) a full year of hours/spend they thought they were getting.
Confidence this is a real defect (vs intended integer-year design): MEDIUM. Rejecting non-integers outright, or accepting fractional years properly, would both be more consistent than silently flooring one but not the other. At minimum the reply should state the years actually applied.

## start/stop project basics — worked as expected
- `{"cmd":"start","id":"hom_eraser_breadcrumb"}` -> ok, started.
- Starting the same id again while active -> `{"ok": false, "error": "already active"}`. Correct.
- `{"cmd":"stop","id":"bogus_id"}` -> `{"ok": false, "error": "not active"}` (not "unknown id" — a real-but-unstarted id gives the same "not active" message; acceptable, not a bug, just noting it does not distinguish "unknown" from "not currently active" the way `start`/`why` distinguish "unknown node id").
- Stepping 1 year completed the eraser: `done_earned` went 0 -> 1, `done_count` 128 -> 129, upkeep appeared (0.5/yr), reputation rose slightly (4.5 -> 5.2). All consistent with expectations.

## Flavor/setting mismatch (not a functional bug, but confusing)
Expect: since this is billed as "The Mexica Triple Alliance, beginning in 1500", flavor text and units should reflect Mesoamerica.
Actual: currency errors talk in "denarii" (a Roman coin), e.g. `{"cmd":"hire","trade":"smith","n":1000000}` -> `{"ok": false, "error": "hiring 1e+06 smiths costs 112500000 denarii in advance and you have 480"}`. And a tech note for `med_cataract_couching` (which is one of the civ's 128 pre-granted starting technologies, confirmed via `why` showing `"done": true`) reads: "an ancient technique attested from Mesopotamia through Rome to India" — again Old World framing with no Mesoamerican adaptation.
This strongly suggests the whole tech tree / cost model is a shared, unlocalized "Rome" knowledge base (matches the file path `rome/sim/simulator.py`) reused verbatim for a Mexica playthrough, including the currency name. Not a crash and probably intended as a reused generic engine, but it undercuts the "you are playing the Mexica Triple Alliance" framing pretty badly, and a literal reading of "denarii" is simply wrong for 1500 Tenochtitlan. Confidence this is worth reporting: HIGH that the mismatch exists as observed; LOW that it counts as a "bug" rather than acknowledged scope-limitation of a shared engine — flagging as a realism/immersion issue either way.

## Labour, buy, quote edge cases — all clean
Expect: negative/zero counts rejected; unknown trades/materials rejected with a helpful message; firing more than you employ should either error or clamp harmlessly.
Actual, all as hoped, no crashes:
- `{"cmd":"hire","trade":"smith","n":-3}` -> rejected, "n must be greater than zero. Nothing was changed."
- `{"cmd":"hire","trade":"chemist","n":1}` (a trade that "does not exist here") -> rejected with guidance to `train` instead.
- `{"cmd":"hire","trade":"smith","n":1000000}` -> rejected for cost, quoting the actual price ("costs 112500000 denarii in advance and you have 480") vs capital on hand. Correctly refuses rather than letting capital go absurdly negative.
- `{"cmd":"hire","trade":"smith","n":1.5}` -> ACCEPTED. Fractional employee counts are a real, intentional mechanic here (state already showed "artisans": 1.5 type fields, and `labour` echoes "you_employ": 1.0 etc. after later firing 0.5). Not a bug — the game models partial-year / partial-FTE staff explicitly.
- `{"cmd":"fire","trade":"smith","n":0.5}` on 1.5 employed -> ok, left with 1.0.
- `{"cmd":"fire","trade":"smith","n":100}` on 1.0 employed (asking to fire far more than exist) -> accepted and silently clamped to 0, no error, no warning that fewer than 100 were actually let go. Minor: same "doesn't report what actually happened" pattern as the `step` truncation above. Low severity (firing all staff when you meant to overfire is a safe direction to clamp), but the reply gives no signal that the requested 100 differed from the 1.0 actually available.
- `{"cmd":"buy","what":"manumit","n":5}` with 0 slaves owned -> rejected, "you have no slaves to free".
- `{"cmd":"buy","what":"slaves","n":-5}` -> rejected, "n must be greater than zero, got -5".
- `{"cmd":"buy","what":"forest","n":0}` -> rejected, "n must be greater than zero, got 0".
- `{"cmd":"buy","what":"unicorns","n":5}` -> rejected, "what must be one of: forest, mine, slaves, manumit".
- `{"cmd":"quote","what":"unicorns"}` -> rejected, "only mines can be quoted so far".

## risk command — thematically strong, opposite of the "denarii" complaint above
`{"cmd":"risk"}` at year 1504 correctly lists Mexica-specific historical hazards: "Old World epidemics on contact" (1520-1600, staff_loss up to 0.8) and "Spanish invasion" (1519-1521, sack_chance_per_year 0.9, with flavor text specifically about friars suppressing indigenous ritual and the tlatoani's court). This is well-written and specific to the civilization, in contrast to the generic/Roman-flavored cost-engine text noted above. Worth recording as something that works well / could NOT break: the historical-hazard content is civ-specific and consistent with the "Mexica_1500" framing even though economic flavor text is not.

## `path` gives a misleading reason when blocked under fog
Expect: per `{"cmd":"help","topic":"commands"}`, the `path` command is annotated "not available under fog of war". I expected calling it under fog to say something like "path is disabled while fog of war is on", regardless of which id is given.
Actual: the error text instead claims the *thing itself* has not been discovered, e.g.:
- `{"cmd":"path","id":"totally_bogus_zzz"}` (an id that does not exist at all) -> `{"ok": false, "error": "you cannot plan a route to something you have not discovered. Nobody can tell you what a thing requires until you know the thing exists. Use 'available' to see what you could begin now."}`
- `{"cmd":"path","id":"med_cataract_couching"}` — this is one of the civ's 128 pre-granted starting technologies, confirmed via `{"cmd":"why","id":"med_cataract_couching"}` returning full detail and `"done": true` — gets the EXACT SAME error text: "you cannot plan a route to something you have not discovered..."

This is wrong on its face for the second case: the technology plainly *has* been discovered (it is done, generating revenue, and fully described by `why`). The real reason `path` fails is that the command is switched off entirely under fog of war (as the help topic says), not that this particular id is undiscovered. Telling the player "you haven't discovered this" about a technology they've already completed is actively misleading — a player debugging why `path` won't work on a finished tech would reasonably conclude something is broken with their save/discovery state, when actually the whole command is just fog-gated.
Confidence this is a real defect: HIGH for "the stated reason is factually wrong for a done technology"; the intended behaviour (block path under fog) is presumably correct per the help text, but the justification message given to the player is not.

## Parser/dispatcher edge cases
- Missing `cmd` field -> clean error: "each line must be a JSON object with a 'cmd' field, e.g. {\"cmd\":\"state\"}". Good.
- Malformed JSON (`{cmd: start}`, unquoted key) -> clean parse error naming line/column. Good, no crash.
- Blank input line -> silently ignored, no reply at all (not even an error). Mildly surprising but harmless; not treating as a bug since a human operator would notice nothing happened and just retype.
- Unknown extra JSON fields (e.g. `{"cmd":"state","bogus_extra_field":123}`) -> ignored, command still runs normally. Reasonable/lenient parsing.
- `{"cmd":"start"}` (id omitted) -> `{"ok": false, "error": "unknown node id None. use {\"cmd\":\"available\"} ..."}`. Works but the message stringifies Python's `None` into the text ("unknown node id None") rather than saying something like "id is required" — cosmetic rough edge, not a functional bug.

### Stale hint list in the "unknown cmd" error — confirmed defect
Expect: the suggestion list in an "unknown cmd" error to match the real command set (I already confirmed via `{"cmd":"help","topic":"commands"}` that money, quote, close, risk, labour, hire, fire, train, commission, work, mothball, restore, bribe, policy, save, load, help are all real, working commands).
Actual: `{"cmd":"frobnicate"}` -> `{"ok": false, "error": "unknown cmd 'frobnicate'. use one of: state, available, why, path, start, stop, bounty, buy, step, quit"}`. This hint list has only 10 entries and omits at least 17 other real commands (money, quote, close, risk, labour, hire, fire, train, commission, work, mothball, restore, bribe, policy, save, load, help), all of which I separately confirmed work in this same session. A player who mistypes a command name and reads this list would be told a materially incomplete picture of what commands exist.
Confidence this is a real defect: HIGH. It is a small thing (both the full `help` and this fallback list exist and disagree), but it is objectively inconsistent with the program's own `help` output from the same running session.

## Debt goes negative gracefully; auto_shed silently reverses "wasted" hires with no log entry
Setup: drained capital by hiring staff with no project running to give them.
Expect: capital should be allowed to go negative up to some credit limit (per `help economy`: "You may spend past what you have, as far as somebody will lend you and no further. Arrears cost interest."), and interest should accrue on the negative balance.

Actual, mostly as expected:
- `{"cmd":"hire","trade":"smith","n":3}` while capital was 311.0 -> accepted, `"capital": -83.5"`. Debt is allowed as documented.
- Stepping forward, `interest_paid_total` rose (0.0 -> 7.2 -> 12.5 -> 14.7 ...) and `credit_limit` shrank each year (1140.3 -> 1115.4 -> 1091.2 -> 1067.7), consistent with "arrears cost interest" and a shrinking headroom. Good, no crash, no runaway.

Unexpected: after hiring the 3 idle smiths (no project assigned to use them), the very next `{"cmd":"step","years":1}` silently fired all of them — `employees` back to `{}`, `annual_wage_bill` back to `0.0` — with **no event or message anywhere in that step's reply** saying staff were let go. The only way to notice is diffing `labour`/`state` before and after. I confirmed this again by hiring 2 more smiths the same way: identical silent disappearance on the next step, the step's own `"events"` list contained only an unrelated flavor line ("fire in the reed and adobe quarter by the canal"), nothing about the firing.
This matches the documented `policy.auto_mothball`/`auto_shed` defaults (`{"cmd":"policy"}` shows `"auto_shed": true` by default, described as "let go of works that cost more than they return"), so the *mechanism* is intended and documented as ON by default. But:
1. The help text for `auto_shed` says it sheds "works" (i.e. completed projects/buildings), and does not mention that it also fires idle hired *staff*. Employees are a distinct concept from "works" everywhere else in the interface (`labour` vs. `available`/`why`/`active`). A player reading the policy help would not expect hiring a person to be undone by "auto_shed".
2. Nothing in the `step` reply's `events`/`completed` lists, nor any other field I found, records that the firing happened. A player who hires staff and doesn't immediately hand them a project loses real capital (hiring 3 smiths cost about 338 capital up front here) for literally zero benefit, with no explanation offered by the program.

By contrast, when I hired 1 smith and immediately `start`ed a project needing artisan labour (`med_bone_setting`) in the same turn before stepping, the project completed successfully using that staff, and the smith was shed only afterward once idle again — so the shedding logic itself is sensible; it is the total silence about it, and the "works" vs "staff" wording gap in `policy` help, that I'm flagging.

Confidence: MEDIUM-HIGH that the missing event/log line is a real gap (the game logs other, less consequential things like a random fire event, but not the loss of your own staff you paid for). MEDIUM that the `policy` help text describing `auto_shed` as being about "works" rather than staff is a documentation/wording bug rather than deliberate broad phrasing.

Reproduce:
```
{"cmd":"hire","trade":"smith","n":3}      # capital drops, "you_now_employ": 3.0
{"cmd":"step","years":1}                  # employees now {} again, annual_wage_bill 0.0, no mention of it in events/completed
```

## `state.living_cost` silently bundles wages in with personal living expenses — confirmed defect
Expect: the welcome text says "You are charged for food, rent and appearances every year whether or not you are building anything," and `state` reports `living_cost` right next to `revenue` and `upkeep` as if it were that fixed personal charge. `money`'s breakdown (`what_it_costs_you`) separately itemises `living_and_appearances` and `wages` as two different lines, so I expected `state.living_cost` to correspond only to the `living_and_appearances` figure.

Actual: `state.living_cost` is actually `living_and_appearances + wages` added together, NOT just personal living expenses. Verified precisely in a clean isolated session (mexica_1500, fresh):
- No staff: `state.living_cost = 230.0`, `money.living_and_appearances ≈ 230`, `annual_wage_bill = 0.0`.
- After hiring 1 smith, one step later: `state.living_cost = 338.1`, `annual_wage_bill = 110.4` — difference from baseline living cost is ~108-110, matching the wage bill, not zero.
- After hiring 5 more smiths (total wage bill 884.2): `state.living_cost = 1109.1` and, in the SAME snapshot, `money` reports `"living_and_appearances": 224.9, "wages": 884.2` — and 224.9 + 884.2 = 1109.1 EXACTLY, matching `state.living_cost` to the decimal.

So `state`'s `living_cost` field name is misleading: it is really "living cost + entire staff payroll," while the `money` command's field of the same underlying concept is correctly split into two clearly-labelled parts. Since `state` is one of "the four you need first" per the welcome text, and a player would reasonably read `living_cost` as the fixed personal charge described in the welcome ("charged for food, rent and appearances every year"), this field name actively misleads about where a growing cost is coming from once staff are hired — a player watching only `state` could easily conclude their base cost-of-living itself is spiraling for no reason, when really it's their own payroll.
Confidence this is a real defect: HIGH. It's not a crash, but the same number is labelled two different, incompatible ways by two different commands in the same program, and the more prominent one (`state`, the one the onboarding text pushes you to use) is the misleading one.

Reproduce (fresh game):
```
{"cmd":"state"}                              # living_cost ~230, no staff
{"cmd":"hire","trade":"smith","n":1}
{"cmd":"step","years":1}                     # living_cost now ~338 (includes wages)
{"cmd":"money"}                              # shows living_and_appearances + wages separately, summing to the same total
```

## Staff are force-fired to zero even with `auto_shed` explicitly OFF — likely a real defect
This is the clearest bug found so far.

Expect: `{"cmd":"policy"}`'s own note says "Anything switched off here you can still do by hand: hire, train, buy, commission, mothball, restore, bribe." — i.e. with `auto_shed:false`, the engine should NOT automatically let staff go; if my payroll becomes unsustainable that should be my problem to solve by hand (fire them myself, or let debt/interest handle it), not something the engine does for me silently.

Steps (isolated fresh session, mexica_1500, fog on):
```
{"cmd":"policy","set":{"auto_shed":false}}     # confirmed in reply: "auto_shed": false
{"cmd":"hire","trade":"smith","n":1}           # ok, 1 employed
{"cmd":"step","years":1}                       # employees now {"smith":0.96} -- survives, only ~3.5% attrition (documented elsewhere as normal attrition rate). Good so far.
{"cmd":"hire","trade":"smith","n":5}           # ok, "you_now_employ": 5.96, annual_wage_bill 884.2, capital -378.9 (credit_limit 1072.3, i.e. only ~35% of credit used, well short of the limit)
{"cmd":"step","years":1}                       # -> employees: {}, annual_wage_bill: 0.0
```
Actual: the entire staff (5.96 FTE) was let go in a single step, dropping straight to zero — not the ~3.5%/yr attrition rate documented elsewhere (`state.staff_are_fractional_because`: "attrition (about 3.5%/yr) trims everyone a little rather than dismissing one person at a time"), and NOT something I did by hand, despite `auto_shed` being explicitly `false` at the time (confirmed by re-reading the `policy` reply immediately before). This happened again on every subsequent step in the same deep-debt condition — I re-hired and it was wiped again, and I let 5 further steps run with capital between roughly -380 and -440 (well inside the ~950-1070 credit_limit throughout, so this is not "hitting the credit ceiling" either) and `employees` stayed at `{}` throughout, `ended` stayed `false`.

I also reproduced the same "staff silently vanish exactly one step after being hired with no active project" pattern in the main playthrough session BEFORE explicitly touching the `auto_shed` policy (i.e. with it at its default `true`), so at first I assumed `auto_shed` (documented as "let go of works that cost more than they return") was responsible, and that its help text just under-described covering staff as well as "works". This isolated test rules that reading out: it happens identically with `auto_shed:false`, so either (a) there is a second, undocumented forced-layoff mechanism independent of the `auto_shed` switch that fires whenever payroll looks unaffordable relative to net income, or (b) the `auto_shed` switch is simply not wired up to whatever code path is actually doing this. Either way, the `policy` command's own promise — "Anything switched off here you can still do by hand" — is false for this behaviour, since I did not do it by hand and could not stop it by switching off the one policy that claims to govern it.

Confidence this is a real defect: HIGH. It is directly falsifiable against the program's own stated contract (`policy`'s note) using only the program's own commands, and I reproduced it twice (two separate hire batches) in a controlled session with the relevant switch off the whole time and capital comfortably within the credit limit.

Also note: no event/log entry accompanies this loss either (same gap as noted above), and no field in `state`/`money` explains why or that it happened — a player has to notice their `annual_wage_bill` dropped to 0.0 on their own.

## `work` lets you personally earn wages in a trade the game says "does not exist here"
Expect: `{"cmd":"hire","trade":"chemist","n":1}` was already rejected earlier with "there are no chemists to hire in this society at any price: does not exist yet; you must create this trade" and `labour` explicitly lists `chemist` under `do_not_exist_here`. I expected `{"cmd":"work","trade":"chemist",...}` (the founder personally doing "an ordinary job for ordinary pay" per the help text) to be rejected the same way — you cannot moonlight in a trade nobody in the society practices or even recognises.

Actual: it succeeded and paid out.
```
{"cmd":"work","trade":"chemist","hours":10}
```
-> `{"ok": true, "trade": "chemist", "hours": 10, "earned": 1.3, "capital": -549.0, "your_hours_left_this_year": 2390.0}`

For comparison, a real, existing trade (`scribe`) at the same hour count pays a different, specific rate (`{"cmd":"work","trade":"scribe","hours":10}` -> `earned: 0.6`), so this isn't a generic/default fallback rate — the engine has a genuine wage-rate entry for "chemist" and is willing to pay it, contradicting its own claim elsewhere that the trade "does not exist yet" in this society.
Confidence this is a real defect: HIGH. `hire` and `labour` both gate on the same "does this trade exist here" concept and agree with each other; `work` simply does not apply that gate, so the fiction that chemistry/electricity/engineering/machining/optics are unknown to 1500 Tenochtitlan (per `do_not_exist_here: ["chemist","electrician","engineer","machinist","optician"]`) is broken by the one command that should be checking it hardest, since it's the founder personally claiming expertise nobody around them has.

(`{"cmd":"work","trade":"scribe","hours":100000}` correctly capped to available hours: `{"ok": false, "error": "you have 2380 of your own hours left this year, not 100000"}` — that guard works fine, so the missing check really is specific to trade-existence, not hours validation in general.)

Further confirmation of the `work`-ignores-trade-existence bug: also reproduced with `electrician` (earned 1.3 for 10 hrs) and `engineer` (earned 1.6 for 10 hrs), both of which `labour` lists under `do_not_exist_here`. And tellingly, `{"cmd":"work","trade":"wizard","hours":10}` (a name that is not a trade at all) is correctly rejected with: `"no such trade. you could work as: artisan, carpenter, chemist, electrician, engineer, engraver, furnaceman, glassblower, labourer, machinist, mason, master, merchant, millwright, miner, optician, plumber, potter, sailor, scholar, scribe, smith"` — note this whitelist is the full civ-agnostic trade roster (it literally includes chemist/electrician/engineer/machinist/optician alongside the real ones), confirming `work` was never filtered by which trades this specific society has. This looks like a straightforward missing filter (the same one `hire`/`labour` clearly do apply), not intentional design — there is no in-fiction explanation offered anywhere for how the founder alone can practice electrical engineering in 1500 Tenochtitlan for pocket change.

---

# Summary

## Confirmed defects, ranked by confidence

1. **HIGH — `work <trade>` ignores trade-existence gating that `hire`/`labour` enforce.** The founder can earn real wages "working" as chemist, electrician, or engineer — trades the game itself says do not exist in this society (`do_not_exist_here` in `labour`, and `hire` refuses them outright) — at distinct, trade-specific pay rates, not a generic fallback. The `work` command's own "no such trade" error whitelist is the full, civ-agnostic trade list rather than what actually exists in 1500 Mexica society. Repro: `{"cmd":"work","trade":"chemist","hours":10}` -> `{"ok": true, ..., "earned": 1.3, ...}`.

2. **HIGH — Staff are force-fired to zero even with `policy.auto_shed` explicitly set to `false`.** Contradicts the `policy` command's own stated contract ("Anything switched off here you can still do by hand"). Reproduced twice in an isolated session with ample credit headroom remaining (capital well within credit_limit). No event/log line records the layoff either. Repro:
```
{"cmd":"policy","set":{"auto_shed":false}}
{"cmd":"hire","trade":"smith","n":5}
{"cmd":"step","years":1}   # employees -> {} anyway
```

3. **HIGH — `state.living_cost` silently bundles the entire staff wage bill into what reads as the founder's personal living expense.** `money`'s breakdown cleanly separates `living_and_appearances` from `wages`; `state.living_cost` is their undocumented sum (verified to match to the decimal: 224.9 + 884.2 = 1109.1). `state` is one of "the four you need first" per onboarding, so this is the more visible of the two, and the misleading one.

4. **HIGH — `path`'s error message under fog is factually wrong for a completed technology.** It claims "you cannot plan a route to something you have not discovered" even when called on a technology confirmed `"done": true`. The real reason (the whole command is disabled under fog, per its own `help` entry) is never stated.

5. **HIGH (but low severity/cosmetic) — the "unknown cmd" fallback error's suggestion list is stale.** It names only 10 of the ~27 real commands, omitting money, quote, close, risk, labour, hire, fire, train, commission, work, mothball, restore, bribe, policy, save, load, help — all confirmed working commands in the same session.

6. **MEDIUM — fractional `step years` values are silently floored with no acknowledgement**, and the floor-vs-reject boundary is inconsistent: 0.999 is rejected ("years must be >= 1") but 1.99 is silently accepted and treated as exactly 1 year, with nothing in the reply indicating less time passed than requested.

## What I attacked and could NOT break
- Input validation on numeric fields across the board: negative/zero `n`, `hours`, `amount`, `years` on `hire`, `fire`, `train`, `commission`, `buy`, `bribe`, `work`, `step` — all cleanly rejected with a specific, sensible message and (per state checks) no side effects ("Nothing was changed." is stated explicitly on several).
- Absurdly large numbers (`hire ... n:1000000`, `step years:100000`, `work hours:100000`) — all cleanly rejected before committing any change, quoting real figures back (actual cost vs. capital on hand, actual hours remaining vs. requested).
- Unknown/bogus ids and trade names across `start`, `stop`, `why`, `bounty`, `mothball`, `buy`, `quote`, `work` — all rejected with clear, on-topic errors; never a stack trace, never a silent no-op that also returned `ok:true`.
- Malformed JSON and missing-`cmd`-field lines — clean parse-error / validation messages, no crash, program kept accepting further input afterward.
- Double-starting an already-active project — rejected ("already active"), no duplicate spend.
- Buying/manumitting with nothing to buy/free — rejected with an accurate reason ("you have no slaves to free").
- Debt mechanics: capital was allowed to run deeply negative (well past -500 against 400 starting capital) without crashing, interest accrued correctly year over year, `credit_limit` shrank sensibly with rising debt, and the game never silently corrupted state; `ended`/`end_reason` stayed consistently `false`/`null` throughout (I did not manage to trigger a genuine bankruptcy end-state, but I also did not push capital past its still-substantial credit_limit headroom before running low on turns to test with, since 500 years is a lot to burn through by hand).
- Save/resume across process restarts (the `--session FILE` "sittings" mechanism): quit mid-game, relaunched pointing at the same session file, and `year`, `capital`, `done_count`, `reputation`, and `revenue` all matched exactly what was in flight before quitting. No corruption, no drift.
- `quit` command itself: clean acknowledgement (`{"ok": true, "bye": true}`) and the process actually exited.
- Fractional employee counts (e.g. 1.5, 0.96 after attrition) are a deliberate, documented mechanic (`staff_are_fractional_because`), not a bug, and firing more staff than you employ safely clamps to zero rather than going negative or erroring oddly.
- The `risk` command's historical-hazard content is genuinely Mexica-specific and well-written (Spanish invasion 1519-1521, Old World epidemics 1520-1600, with period-appropriate flavor about friars and the tlatoani's court) — this stands in real contrast to the generic/Roman-flavored cost-engine text (see below) and I could not find any inconsistency in it.

## Things that struck me as confusing or unrealistic (not necessarily bugs)
- The whole cost/currency layer speaks in Roman terms ("denarii" in `hire`'s cost-refusal message) and tech-note flavor text references "Rome" and "Mesopotamia" for a nominally Mexica, 1500 CE playthrough (`med_cataract_couching`'s note). Strongly suggests a shared, unlocalized knowledge base/engine (matches the `rome/sim/simulator.py` path) — thematically jarring against the otherwise careful, civ-specific `risk` content, but I'm not confident this counts as a "bug" versus a known scope limit of a reused engine.
- `state.done_count` reporting 128 pre-existing "done" technologies at turn 0, before any player action, was initially confusing since nothing in the four-command onboarding primer explains `done_granted` vs `done_earned`; turned out to be legitimate (starting societal knowledge), confirmed via `why` on an available (not-done) item correctly showing `"done": false`.
- Several commands (`stop` on a valid-but-inactive id, `fire` beyond what's employed, the forced staff-layoff above) silently no-op or clamp without ever surfacing an event/log line, in contrast to how the world DOES log unrelated flavor events (e.g. "fire in the reed and adobe quarter by the canal") on the very same steps. The asymmetry — trivia gets logged, consequential involuntary losses of the player's own money/staff do not — was the single most disorienting thing about play.

## Session artifacts
- Final session file: `/home/user/test/rome/playtest/naive3/mexica_1500_BREAK.json` (written by the program itself).
- These notes: `/home/user/test/rome/playtest/naive3/mexica_1500_BREAK.md`.
- No repository file was read (source, data, or docs) or modified other than this notes file, per the rules. A second, throwaway isolated session used to isolate the `auto_shed`/`living_cost` findings was run against the same program with its session file kept outside the repo (`/tmp/.../scratchpad/mexica_scratch2.json`), and is not part of the deliverable.
