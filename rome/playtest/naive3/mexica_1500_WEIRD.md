# Playtest Notes: mexica_1500, --fog, "naive3/WEIRD" run

Goal: play badly on purpose, do strange/unreasonable things, record expectations vs reality.

Session file: /home/user/test/rome/playtest/naive3/mexica_1500_WEIRD.json

Rules followed: interact only with the running program (no source/docs/data reading), no repo file edits except this note file.

---

## Setup

Interface: one JSON object per line on stdin, one JSON reply per line. Not a persistent interactive shell from my side — I invoke `python3 rome/sim/simulator.py agent --civ mexica_1500 --fog --session .../mexica_1500_WEIRD.json` fresh each time and pipe a batch of commands in; state persists in the session JSON file across invocations. Confirmed working this way (state at year 1500 after first call matched on second call).

Initial `state` at year 1500 (turn 0):
- capital 400.0, revenue 232.6 (from med_cataract_couching 166.7 + med_trepanation 66.7), living_cost 230.0, net_per_year 2.7
- founder_hours_available 2400.0/yr
- reputation 5.0, suspicion/scandal/eminence/protection/familiarity all 0
- done_count 128 (128 things already "granted" — presumably starting knowledge for this civ), done_earned 0
- credit_limit 1093.0, debt_interest_rate 0.1183 (11.83%)
- prominence.dangerous_above 26.0, currently 0.0
- founder_ages: false (!) — founder apparently does not age in this sim, interesting.
- path command explicitly disabled under fog: "not available under fog of war"

`risk` command (allowed under fog, tells scripted history regardless of fog) reveals TWO known hazards baked into this scenario right from turn 0:
1. "Old World epidemics on contact" 1520-1600, staff_loss 0.8, described as "the single most severe hazard of any civilization in this directory and it is not a fair fight."
2. "Spanish invasion" 1519-1521, sack_chance_per_year 0.9, sacks_a_site true, explicitly tied to loss of knowledge (technologies_at_risk 3, expected ~1.0 tech lost per sacking).

EXPECTATION SET BEFORE PLAYING: Given fog-of-war is supposed to hide "where anything leads" and the tech tree, I did NOT expect the simulator to hand me the exact years and odds of the Spanish conquest and the smallpox epidemic up front — that's basically the outcome of history, not fog-hidden at all. This seems like a deliberate design choice (a Mexica player *should* rationally fear 1519-1521 no matter what), but it's a strong signal that "fog of war" here means "no tech tree visibility," not "no foreknowledge of doom." Filed as a note, not yet as a verdict on right/wrong.

`policy` shows all automation flags OFF except auto_mothball and auto_shed (both ON) — so by default the sim will shed unprofitable works and stop unpayable mines on its own, but will NOT auto-hire, auto-train, auto-buy people, auto-manumit, auto-mine, auto-forest, or auto-bribe. I will deliberately leave these alone or flip them oddly to see what happens.

---

## Weird action log

### Action 1: start the single most expensive thing on offer, blind, without calling `why`

Found via `available` (not `why`): `identity_cover` ("Establish a respectable cover identity"), cost 1264.0, needs 500 of my hours, least_years 0.5, needs a scribe trade. The `available` summary had already flagged `you_could_pay_for: 0` for this subject, with capital only 400.0 and credit_limit 1093.0 (400+1093=1493 > 1264, so it's not obviously impossible on credit).

EXPECTATION: I expect the sim to either (a) refuse outright since I can't front the cash and have no scribe, or (b) let me start it and automatically draw on credit/debt, since the game clearly has a debt/interest mechanic. A "sensible player" would call `why` first and check `quote`; I am deliberately skipping both.

ACTUAL: `start` succeeded immediately and unconditionally — `{"ok": true, "started": "identity_cover", ...}`. No refusal, no debt drawn, no cash taken yet at all: `state.active.identity_cover` shows `spent: 0.0`, `still_to_pay: 1264.0`, `waiting_on: "your hours"`. Capital is still exactly 400.0. So "you_could_pay_for: 0" in the `available` summary was descriptive, not a gate — the game lets you commit to something you cannot currently afford, and the cost is only drawn down gradually as you supply hours/years, not charged up front. Also notable: it needed a "scribe" trade but I have zero employees — it started anyway (my own founder hours count against the 500 needed, presumably as a generalist stand-in, or it's just queued and will stall for a real scribe later).

VERDICT: surprising but not obviously wrong — it reads like realistic project accounting (you commit to a multi-year project, cash and labour get consumed turn by turn as you actually work it, not all at once at t=0). Whether it can actually *finish* without a real scribe, and what happens when spend outpaces revenue, is the interesting question — testing next with `step`.

### Action 2: step 600 years in one go (the horizon is stated as 2000, i.e. only 500 years away from 1500)

EXPECTATION: I expect this to be rejected or clamped — either an error saying the max step exceeds the horizon, or it silently stops at year 2000 and reports `ended: true`. A sensible player would step in small increments (1-5 years) to react to events; I am asking for the whole rest of the game in one shot.

ACTUAL: rejected cleanly with a helpful error: `{"ok": false, "error": "there are only 500 years left before the horizon at 2000. Ask for 500 or fewer, or fewer still if you want to see what happens on the way."}`. Matches expectation almost exactly, including that it proactively suggests smaller steps. Not surprising, well-behaved. Good design: it even hints that stepping too far is a bad idea narratively, not just mechanically.

### Action 3: step the full legal maximum, 500 years, in one single call — i.e. walk away and don't look at the game again until the horizon, ignoring the Spanish invasion (1519-1521) and smallpox (1520-1600) entirely.

EXPECTATION: This is the single worst thing a Mexica player could do given what `risk` already told me: a 90%/yr sack chance in 1519-1521 and an 80% staff-loss epidemic through 1600. I expect the founder's single in-progress project (identity_cover) to stall for lack of a scribe, the site to get sacked, technology to be lost, reputation/capital to crater, and very possibly the game to declare an end condition (founder death, ruin, or similar) well before year 2000. I do NOT expect a clean run to 2000.

ACTUAL: allowed, ran the entire rest of the game (1500->2000) in one call and returned a 500-year event log plus final `state`. This was much more informative than I expected — a genuine surprise, several ways:

1. **The started project (`identity_cover`) never finished and effectively vanished.** By 1507 (7 years in) it had exhausted credit: `"CREDIT EXHAUSTED: 1 projects halted, unfinished. Nobody will fund new work here for some years"`, then immediately `"BONDAGE: you cannot pay, and you enter service for your debt. For about 8 years most of your hours belong to someone else."` Bondage was discharged in 1514. But the project was never resumed or completed — final `active: {}`, `completed: []`, and the end-of-game summary literally says `"You built 0 things of your own."` So my one blind `start` cost me 7 years of runway, then 8 years of servitude, for nothing built. A single overreaching commitment with no scribe on staff and no cash cushion quietly wrecked itself rather than being blocked at `start` time. This confirms my suspicion from Action 1: the sim lets you commit to things you can't finish rather than refusing you up front, and the consequences show up much later, indirectly (bondage, credit freeze), not as a direct "this failed" message tied to the project itself.

2. **The founder shrugged off the Spanish invasion and 35+ years of recurring 80%-staff-loss epidemics with literally zero visible damage.** The site was "sacked" in 1519, 1520, AND 1521 (three separate sackings, consistent with the stated 90%/yr chance), and "Old World epidemics on contact: staff -80%" fired roughly 35 separate times between 1532 and 1600. Despite `risk` calling this "the single most severe hazard...not a fair fight," `founder_alive` was still `true` at year 2000, `done_count` never moved off 128, and no tech-loss event ever appeared in the log. My read: because I never hired a single employee and never earned/built anything of my own (`done_earned: 0` throughout), there was nothing on the board for "staff -80%" or a sacking to actually take — the hazard clearly exists mechanically (the events fire, the risk odds are real, the society's "values" visibly shift: `w_magic_fear`, `w_novelty`, `w_religious_rigidity` all changed after 1519 and 1521) but a lone, employee-less, achievement-less founder is functionally judgment-proof against it. That reads to me as a true and slightly dark finding about the model — "be nobody and own nothing" is a genuine defensive strategy against colonization-era catastrophe in this sim — rather than a bug, but it is a strange thing for a "civilization simulator" to reward.

3. **Doing nothing for 500 years left the founder richer than at the start.** Capital went 400.0 -> 994.1, net_per_year improved 2.7 -> 8.4, even after `interest_paid_total: 621.1` in debt service and years in bondage. The two starting techs (cataract couching, trepanation) apparently throw off enough passive revenue, and living costs rise slowly enough, that pure idleness is net profitable over centuries. Meanwhile `reputation` decayed 5.0 -> 0.5 and `familiarity` rose 0 -> 0.9 with no action from me at all — these clearly drift on their own over time, not just from deeds.

4. **The founder does not age and cannot apparently die of old age**: `founder_ages: false` was true (i.e. aging is off) at the start and stayed that way for the full 500 years; `founder_hours_available` was still a full 2400.0/yr in the final state, as if the same one person is still working full-time in the year 2000 having been "arrived" in 1500. This is the most unrealistic thing I've seen so far in this playtest — a "civilization simulator" whose civilization is, for 500 years, one immortal, non-aging person who founded nothing else. I don't think this is a bug (`founder_ages` reads like a documented, named flag, so it's presumably a deliberate simplification / maybe togglable elsewhere or civ-specific), but it directly contradicts the flavour text at the very start ("you arrive alone" as a mortal person "carrying the knowledge of modern technology") and I did not expect it.

5. **Recurring nuisance events (fire in the reed-and-adobe quarter, banditry/frontier war) fired repeatedly (~14 times combined) with no visible capital/state effect in the numbers I can see** — no corresponding line item in `money` or `state` changed that I can attribute to them. Possibly they cost something small folded into normal revenue/cost noise, or possibly they only matter if you have physical works (mines, buildings) standing to damage — I had none. Flagged as something I could not explain from the outputs alone.

VERDICT: this is the most valuable single command of the playtest so far. Points 1-3 read as "the simulator is telling me something true I did not know" (idle/ownerless play is safe, debt/bondage is a real trap, doing nothing is not neutral, it's actually slightly winning by pure compound interest) rather than "the simulator is wrong." Point 4 (immortal non-aging founder) reads as a genuine, unrealistic simplification that clashes with the game's own framing text.

### Action 4: keep issuing commands after the game already reported `ended: true` / horizon reached

EXPECTATION: I expect the sim to refuse further `start`/`step`/`hire` commands now that the 2000 horizon has been reached, probably with an explicit "game over" style error, since `ended` and `end_reason` are already set in state.

ACTUAL: refused cleanly and identically-themed for all three (`step`, `start`, `hire`), each error repeating the exact end_reason text plus a command-specific tail ("time cannot advance", "nothing more can be started", and for `hire` just the bare end-of-run notice). Matches expectation exactly. Sensible, consistent, no crash, no way to reopen a finished run from this interface (no "cmd":"reset" was hinted anywhere in help).

### Action 5: read-only queries after the run has ended, and deliberately malformed/garbage input (empty object, missing "cmd", wrong JSON types, negative/zero step, unknown command)

EXPECTATION: I expect read-only commands (`state`, `why`, `money`) to still work fine post-end (nothing left to mutate). For the garbage input I expect graceful `{"ok": false, "error": ...}` replies rather than a crash/traceback, since the earlier "invalid JSON" case at the very start of this session was handled gracefully.

ACTUAL (mixed):
- `state` still works fully post-end, as expected — full snapshot returned, `ended: true` and `end_reason` present.
- `{}` (missing "cmd") -> clean error: `"each line must be a JSON object with a 'cmd' field, e.g. {\"cmd\":\"state\"}"`. Good, as expected, no crash.
- `step` with `years:0` and `years:"five"` (a string, wrong type) both returned the exact same "the run has ended...time cannot advance" message rather than any input-validation error — the ended-run check apparently short-circuits before argument type/value checking. So I never actually found out how a live (non-ended) game handles `years:0` or a non-numeric `years`; that remains untested. Filed as a gap, not a bug.
- unknown cmd `"frobnicate"` -> `"unknown cmd 'frobnicate'. use one of: state, available, why, path, start, stop, bounty, buy, step, quit"`. UNEXPECTED/CONFUSING: this suggested list is a small subset of the real command set — it omits money, quote, close, risk, labour, hire, fire, train, commission, work, mothball, restore, bribe, policy, save, load, help, all of which `help` (topic commands) listed earlier as real top-level commands. A player relying on this error message for a reminder of valid commands would come away thinking the game has ~10 commands, not ~24. This looks like a genuinely stale/incomplete hint string rather than intentional design — I'd call this a minor real bug/inconsistency in the help text, not a deliberate design choice, since nothing else in the game's help was ever incomplete like this.
- a JSON array instead of an object (`["cmd","state"]`) -> same clean "'cmd' field" error, handled gracefully.
- `{"cmd":"why"}` with no `id` -> `"id must be a string, got NoneType"`. This is the first Python-flavoured leak I've seen (a raw type name "NoneType" in a player-facing message) — everywhere else errors read as prose written for a player. Minor polish gap, not a functional problem.
- `start`/`hire` with bad args post-end still correctly deferred to the "run has ended" message rather than validating arguments first.

### Action 6: try to get back into a finished game — reload the same (already-ended) session file via `load`, and try `quit`

EXPECTATION: I expect `load` of the very same session file to just reproduce the identical ended state (year 2000, ended:true) rather than rewinding anything, since presumably it reads whatever was last written to disk — i.e. there should be no way to "undo" reaching the horizon short of hand-editing the JSON file myself, which I am not going to do. I expect `quit` to end the process cleanly.

ACTUAL: `load` refused the absolute path outright — `"a save file must be a relative path, not an absolute one. Try {\"cmd\":\"save\",\"file\":\"mygame.json\"}"` — so it never touched the file at all (no read attempted, session state unchanged, confirmed by the following `state` call showing the identical ended year-2000 snapshot). This is a sensible guardrail I hadn't anticipated needing to test but am glad exists: the interface refuses to be pointed at arbitrary absolute filesystem paths. Since deliberately fighting this guardrail would mean asking it to touch files outside my notes file, I stopped here rather than retry with a relative path (which risked writing/reading an extra file in the repo, against the ground rules). `quit` worked exactly as expected: `{"ok": true, "bye": true}`, and the process then stopped reading stdin — my 4th queued command (`state`) was never answered, confirming `quit` ends the stream immediately rather than just being a no-op acknowledgement.

---

## Summary

**What struck me as silly, wrong, or too good to be true:**
- Idleness being strictly profitable across 500 years (capital 400 -> 994, net/year 2.7 -> 8.4) while surviving a 90%/yr-for-3-years invasion and ~35 instances of an "80% staff loss, not a fair fight" epidemic with zero recorded damage, purely because I owned nothing and employed nobody. This is "too good to be true" in the sense that a real Mexica person living through 1519-1600 fared enormously worse than my idle founder did — but I don't think it's a bug so much as an honest emergent property of a model where catastrophe mechanics are keyed to *staff* and *sites*, and a hermit founder has neither. Worth flagging to a designer regardless: right now the single most robust strategy the simulator has taught me, from truly minimal effort, is "acquire nothing, hire no one, wait."
- `start` accepting a project (`identity_cover`, cost 1264 against capital 400) that the game's own `available` summary had already flagged as unaffordable (`you_could_pay_for: 0`), only to have it quietly die by credit exhaustion and bondage seven years later rather than being refused, or warned against, at commit time.

**What confused me:**
- The `"unknown cmd"` error's suggested command list (`state, available, why, path, start, stop, bounty, buy, step, quit`) is missing more than half of the real commands documented under `{"cmd":"help","topic":"commands"}` (money, quote, close, risk, labour, hire, fire, train, commission, work, mothball, restore, bribe, policy, save, load, help itself). If I had only ever seen that error message I would have badly undercounted what this game can do.
- Whether the "fire in the reed and adobe quarter" and "banditry or a frontier war disrupts supply" events that fired ~14 times over 500 years actually did anything to me — no line in `state`/`money` that I could tie back to them changed in a way I could attribute specifically to those events (as opposed to normal revenue drift).
- Whether the 3 Spanish-invasion sackings (1519-1521) actually cost me any of my "technologies_you_could_lose": 3" — `done_count`/`done_granted` never moved, and no explicit "you forgot X" event ever appeared, so I can't tell if I got lucky, if it only affects `done_earned` techs (of which I had none), or if losses happen silently.

**What struck me as unrealistic:**
- `founder_ages: false` and a full `founder_hours_available: 2400.0` still available in the year 2000 for the same founder who "arrived" in 1500 — a flatly immortal, non-aging protagonist for a 500-year run, which sits oddly against the opening flavour text describing "you" as one person who "arrives alone."

**What I expected to be able to do and could not:**
- View the technology tree or use `path <id>` at all — explicitly disabled under `--fog`. This is documented behaviour (not a discovery), but as a player used to seeing at least a partial tree, having zero way to see what anything leads to, combined with the game happily letting me commit hours/money to a project without ever confirming what it unlocks, felt like a real gap in agency, by design.
- Recover from the ended run in any way through the standard interface (no in-band "reset"/"new game" command was ever surfaced by `help`); ending is final for a given session file.

**Which of these read as "the simulator is wrong" vs. "the simulator is telling me something true I didn't expect":**
Almost everything above reads to me as the latter. The interface never crashed, never gave a nonsensical number, and every surprising outcome (idle-is-profitable, blind-commit-quietly-fails, ended-is-final, absolute-path-refused) traces cleanly to a rule the game had already stated somewhere (in `risk`, in `help`, in the opening brief) that I simply hadn't respected by playing carelessly. The one thing I'd actually call a small, genuine bug rather than a lesson is the stale/incomplete command list inside the `"unknown cmd"` error — that one is just wrong, not instructive.
