# Playtest notes — rome_100ad, fog of war ON

Session under test: `/home/user/test/rome/playtest/naive/rome_100ad_BREAK.json`
Started with:
```
cd /home/user/test
python3 rome/sim/simulator.py agent --civ rome_100ad --fog --session /home/user/test/rome/playtest/naive/rome_100ad_BREAK.json
```
Protocol: one JSON object per line in, one JSON object per line out. Session is a JSON file rewritten after every command, so the game can be stopped/restarted and resumes from that file.

All testing is via the game's own stdin/stdout JSON protocol. No repo file was ever opened/read directly (per the rules); the "session file" is only ever touched through `--session` on the CLI, never cat'ed. Scratch copies of the session used for isolating bugs live outside the repo, under the scratchpad dir, e.g. `/tmp/.../scratchpad/clean3.json`, and were driven with the exact same CLI/protocol.

---

## FINDING 1 (critical, reproducible 100%): `state` permanently breaks itself after being called once, then reloaded

Steps (fresh session each time; `$S` is any `--session` path):

1. Start the game once (any input, e.g. a single blank line) to create the session file.
2. Send `{"cmd":"state"}` as the *only* command in a process invocation. Reply: `ok: true`, full state dump, e.g.:
   `{"ok": true, "year": 100, "capital": 400.0, ... }`
3. Stop the process (EOF). Start a *new* process against the *same* `--session` file and send `{"cmd":"state"}` again (i.e. this is the second time `state` has ever been asked for, but the first time in a fresh process after a save/reload round trip).
   Reply:
   `{"ok": false, "error": "internal error handling that command: TypeError: type NoneType doesn't define __round__ method. The game is intact; try something else."}`
4. Every subsequent call to `state` (3rd, 4th, ...) on that same session file fails the same way, forever. The session is permanently wedged for the `state` command. `available` fails identically (see below), with a different exception:
   `{"ok": false, "error": "internal error handling that command: TypeError: '>=' not supported between instances of 'NoneType' and 'int'. The game is intact; try something else."}`

This is NOT specific to the designated BREAK.json session — it reproduces on a brand-new, never-touched session file every time, deterministically, in 3/3 controlled trials plus 8/8 in an earlier looser trial.

Exact repro transcript (scratch session, not the graded one, same protocol):
```
$ echo '' | python3 rome/sim/simulator.py agent --civ rome_100ad --fog --session clean3.json
(prints the welcome banner, creates the session)

$ printf '%s\n' '{"cmd":"state"}' | python3 rome/sim/simulator.py agent --civ rome_100ad --fog --session clean3.json
{"ok": true, "year": 100, "capital": 400.0, "revenue": 0.0, "upkeep": 0, "living_cost": 216.0, ... "manual": true, "ended": false, "end_reason": null}

$ printf '%s\n' '{"cmd":"state"}' | python3 rome/sim/simulator.py agent --civ rome_100ad --fog --session clean3.json
{"ok": false, "error": "internal error handling that command: TypeError: type NoneType doesn't define __round__ method. The game is intact; try something else."}

$ printf '%s\n' '{"cmd":"state"}' | python3 rome/sim/simulator.py agent --civ rome_100ad --fog --session clean3.json
{"ok": false, "error": "internal error handling that command: TypeError: type NoneType doesn't define __round__ method. The game is intact; try something else."}
```

Interpretation: something about processing (or more likely *serializing to / reloading from the session file*) `state` writes a field into the save file whose value is `None` where the code later expects a number to `round()`. Once that bad value lands in the save, EVERY future `state` call on that file crashes the same way, forever — this looks like an unrecoverable, permanent corruption of a save file caused by the single most basic read-only command in the game. `available` shows the same class of bug with a different offending comparison (`None >= int`), also permanent once triggered.

This is exactly what happened to the designated session `/home/user/test/rome/playtest/naive/rome_100ad_BREAK.json`: the very first exploratory commands sent to it (`state`, `available`) on the second process invocation already came back with these two errors, and they have not recovered since (confirmed by re-querying `state` on it again later — still the same error).

**Impact**: this makes the whole "save across sittings" feature (the game's own headline pitch: "you do not need to hold a process open or write a script") actively dangerous — the ordinary act of quitting and resuming (the officially supported workflow) can silently and permanently brick the save's two most basic introspection commands, with no warning, no recovery command, and a message ("The game is intact; try something else") that is simply false — the game state is not intact, `state` and `available` are both dead forever after this.

---

## FINDING 2 (design/realism, not yet confirmed exploitable): `available` at year 100 Rome lists absurdly anachronistic, trivially-cheap technologies

On a session where `available` still worked (before it got bricked by Finding 1), the very first `available` call in year 100 (Trajan's Rome, 1 scholar, 3 artisans, 2400 founder-hours/year, 400 capital) included, among ~normal ancient items, entries such as:

- `sc2_physics_nuclear_fission` "Nuclear fission and chain reaction" — summary literally says "Meitner and Frisch (1938-1939); Manhattan Project (1942-1945)" — cost 252.0, your_hours 140.0, least_years 2.0, chance_of_failure 0.15
- `sc2_physics_wave_mechanics` "Wave mechanics and Schrödinger equation" — "Schrödinger (1926)" — cost 316.8, your_hours 180.0, least_years 15.0
- `sc2_statistics_anova` "Analysis of variance (ANOVA)" — "Fisher (1920s)" — cost 240.0, your_hours 140.0, least_years 6.0
- `el2_sonar_acoustic_detection_ranging` "Sonar acoustic detection and ranging" — cost 208.2, your_hours 180.0, least_years 3.5
- `el2_photomultiplier_single_photon` "Photomultiplier single photon detector" — cost 199.8, your_hours 140.0, least_years 2.0

These are all offered as things a lone person in Trajan's Rome could **begin today**, for a couple hundred sestertii and a few hundred hours, with no visible prerequisite chain (fog of war shows only "what you could begin today" — by the game's own description these are things with no unmet prerequisite). Nuclear fission for less money than a Roman "Drawing office" (504.0) is on its face absurd for a 1st-century-AD start state. Need to confirm by actually trying to `start` one of these whether the backing project logic is equally nonsensical (e.g. actually completable in 2 years by 3 Roman artisans), or whether `available` is just mis-listing things that would immediately fail a hidden prerequisite check. Follow-up needed once a working (non-bricked) session is available.

---

## Open questions / next steps
- Confirm whether Finding 1 is triggered by `state` specifically, or by *any* command once it's been asked twice / once the file has been saved-and-reloaded once. Testing `available`-first and other commands next.
- If a session can be kept alive (avoid Finding 1), try to `start` sc2_physics_nuclear_fission or similar and see what happens — either the game lets a Roman research nuclear fission in 2 years (very bad), or it errors out, or `available`'s cost/time figures are lies.
- Try negative/huge `step years`, negative `buy n`, buying/manumitting more slaves than owned, starting the same project twice, starting a nonexistent id, malformed JSON, unknown `cmd`.

---

## FINDING 3 (critical, reproducible, on the actual graded session): spamming a *failing* `step` command silently manufactures money, unboundedly, while the calendar year never moves

This builds directly on Finding 1. Once `state`/`available` are bricked (see Finding 1 — which happens after the very first real command in *any* fresh session, including the designated `rome_100ad_BREAK.json`), the `step` command also starts failing on every call:

```
{"cmd":"step","years":1}
-> {"ok": false, "error": "internal error handling that command: TypeError: 'NoneType' object is not iterable. The game is intact; try something else."}
```
This happens for `years:1` and for `years:100000` alike (same exception, so the crash happens very early — likely on the first simulated year, before any multi-year loop even matters).

Because `state`/`available` are also dead, I could not read `capital` directly. Instead I used the *error message* from an intentionally-too-big `buy` as a side-channel probe, since it always echoes current capital: `{"cmd":"buy","what":"forest","n":999999}` → `"cannot afford ... (you have N denarii)"`. I confirmed this probe is trustworthy: two real `buy forest n=1` / `n=2` purchases later cost exactly 250 and 500 denarii (consistent 250/ha) and left capital exactly where the probe predicted, so the probe is accurate and buy's own accounting is sane.

Sequence of capital readings, each separated by one *failing* `{"cmd":"step","years":1}` call, all on `/home/user/test/rome/playtest/naive/rome_100ad_BREAK.json`:

| after N failed `step` calls | capital (denarii) | delta |
|---|---|---|
| 0 (start of game) | 400 | — |
| 1 | 184 | −216 (exactly the `living_cost` from the very first `state` reply) |
| 2 | 285 | **+101** |
| 3 | 384 | +99 |
| 4 | 481 | +97 |
| 5 | 577 | +96 |
| 6 | 672 | +95 |
| 7 | 765 | +93 |
| 8 | 857 | +92 |
| 9 | 948 | +91 |
| 10 | 1037 | +89 |
| 11 | 1124 | +87 |
| 12 | 1211 | +87 |

So: the *first* failing `step` correctly charges one year's `living_cost` (216) and stops there (net_per_year at game start was reported as **-216.0**, i.e. explicitly a loss). Every failing `step` *after* that instead **adds** roughly 90-100 denarii, slowly shrinking but still positive after 11 more calls, net total after 12 failed calls in a row: **+811 denarii from nothing**, generated purely by repeatedly sending a command that itself reports `"ok": false` every single time.

Proof the calendar never actually advanced while this was happening: `{"cmd":"save","file":"..."}` (issued right after the 12th failed step, capital already at 1211) replied `{"ok": true, "saved": "...", "year": 100}` — still year 100, the game's starting year. So this is not "a real turn happened and the display is merely stale" — the authoritative save file itself says no year has passed, yet 811 denarii of capital appeared from nowhere.

Exact commands to reproduce end-to-end from a brand new session:
```
{"cmd":"help"}                     (or any real command — see Finding 1, this is what bricks state/available)
{"cmd":"step","years":1}           -> ok:false, NoneType not iterable   (capital -216, correct, one real year's upkeep)
{"cmd":"step","years":1}           -> ok:false, NoneType not iterable   (capital +~100, WRONG, no year passed)
{"cmd":"step","years":1}           -> ok:false, NoneType not iterable   (capital +~95, WRONG, repeat as many times as you like)
...
{"cmd":"save","file":"anywhere.json"}   -> ok:true, "year": 100   (still turn 1! all that money came from nothing)
```

**Impact**: this is an unbounded, repeatable, no-cost exploit to generate free capital — exactly "let you do something it clearly did not mean to allow." Combined with Finding 1 it also means: the very first time anyone plays this game as instructed (start it, do something, come back later — the game's own pitch), the *correct*, intended way to advance time (`step`) stops working at all, but *spamming the now-permanently-broken `step` command* is a strictly-better move than playing correctly, because every call is free money. A player who understood this would just loop `step` forever instead of building anything.

Root-cause guess (not verified against source, per the rules): the per-year economic update (revenue/upkeep) looks like it is applied to `capital` *before* the code hits whatever is actually `None` and throws (a hazard-schedule or event-iteration bug, probably touching the same poisoned field from Finding 1) — and the exception handler at the top level catches the crash and reports failure, but never rolls back the partial mutation, and never advances `year` either. So the effect is non-atomic *and* sign-inverting: the game's own numbers said this year should cost 216, but every following "no-op" (because it errors!) year nets you positive money instead.

---

## FINDING 4: `save` still works from a session already broken by Finding 1/3

`{"cmd":"save","file":"..."}` succeeds and returns `{"ok": true, "saved": "<path>", "year": 100}` even when `state`, `available`, and `step` are all permanently throwing internal errors on the same session. This is useful (it's how Finding 3's "year never moved" claim was confirmed without a working `state`), but also means a player would have no in-band clue anything is wrong beyond the errors themselves — `save`/`buy`/`why`/`start` all keep reporting a perfectly normal, if quietly-inflated, game.

`quit` also returns cleanly (`{"ok": true, "bye": true}`) from the broken state.

---

## Things attacked hard and NOT broken (clean, sane behavior)

- `step` with `years:0` or negative → clean rejection: `"years must be >= 1"`.
- `step` with `years:"five"` (string) → clean rejection: `"years must be an integer"`.
- Unknown `cmd` → clean, helpful error listing valid commands.
- Missing `cmd` field → clean error.
- Malformed (non-JSON) input line → clean `"invalid JSON"` error, does not crash the process.
- `start` with a bogus/nonexistent id → clean error, and usefully suggests using `available`/`why`.
- `why` with a bogus id → clean error (though see cosmetic note below).
- `path` under fog of war → correctly refused with an in-character explanation, does not leak tree structure.
- `buy` with negative `n` → clean rejection, explicitly says "Nothing was changed."
- `buy manumit` with no slaves owned → clean rejection ("you have no slaves to free"), does not go negative.
- `stop` on an id that was never started → clean `"not active"` error.
- `buy forest` pricing itself is internally consistent: 1 ha costs 250, 2 ha costs 500, and it correctly refuses when unaffordable, quoting the true current capital (used this as a reliable side-channel probe above).

## Merely confusing / cosmetic

- `why` on an unknown id replies `"did you mean: no idea"` — reads like a debugging placeholder/joke rather than a real suggestion (compare `start`'s much more useful unknown-id message). Not a crash, just an odd inconsistency in polish between two very similar error paths.

## Unrealistic (design smell, separate from the crash bugs)

- Finding 2 (above): at year 100 in Trajan's Rome, `available` under fog of war listed things like nuclear fission (explicitly citing Meitner/Frisch 1938-39 and the Manhattan Project in its own summary text), Schrödinger wave mechanics (1926), and ANOVA statistics (Fisher, 1920s) as buildable **right now** for a few hundred denarii and a few hundred founder-hours, i.e. cheaper and faster than "Drawing office" (504 denarii) or "Coffee house as information market" (2610 denarii). I was not able to confirm whether `start`ing one of these would itself be blocked by a hidden prerequisite check, because by the time I found this, Finding 1 had already bricked `available`/`state` on every session I tried it against (this is itself telling: I never managed to get a long enough clean run to chase this before the save-corruption bug ate the session). Flagging as unverified but worth a second pass in a future session.

