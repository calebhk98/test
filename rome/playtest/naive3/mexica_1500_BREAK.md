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
