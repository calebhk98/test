# BREAK_B — playtest notes

Playtester B. Goal: break the simulator. Rules: only the running program tells me anything.

Config target: England, 1300, fog of war ON, poor scholar purse, founder does NOT age.

## Log

### 0. Startup
Expectation: an interactive setup wizard asks a handful of questions, then hands me a session file
and a `play --session <file>` command. I expect piping to work since the task says so.

### Setup transcript
Answers: scenario `4` (England under Edward I, 1300) -> fog `y` -> purse `poor_scholar` -> ageing `n`.
Setup ends with:

```
   Starting now. Progress is written to this file after every command, so you
   can stop any time - close the terminal, anything - and come back to exactly
   where you left off with:

      python3 rome/sim/simulator.py play --session england_1300.json
```

---

## FINDING 1 (HIGH) — "Saved to england_1300.json" is false, and resuming a
## missing session silently starts a *different game* instead of erroring

Expectation: the program said progress "is written to this file after every command"
and told me to come back with `play --session england_1300.json`. I expected that
file to exist after setup, and I expected `play --session` on it to resume England 1300.

Repro A (no save is written):
```
cd /home/user/test/rome/playtest/naive4/B
printf '4\ny\npoor_scholar\nn\n' | python3 /home/user/test/rome/sim/simulator.py
ls          # -> england_1300.json DOES NOT EXIST
```
Program nevertheless printed:
```
Ended 1300 AD. stopped
Saved to england_1300.json. Come back with:
   python3 rome/sim/simulator.py play --session england_1300.json
```
It appears the save is only flushed after at least one in-game command; ending the
session with zero commands writes nothing but still claims it saved.

Repro B (missing session silently becomes a brand new Roman game):
```
printf 'state\n' | python3 /home/user/test/rome/sim/simulator.py play --session /tmp/does_not_exist_xyz.json
```
Reply begins:
```
   You arrive in 100 AD with 400 denarii ...
[100 AD | 400 den | you:2400 hr | sch 0 art 0 | rep 5] >
YEAR 100
```
and `help` in that session says "You are playing The Roman Empire under Trajan,
beginning in 100." No warning that the named session did not exist. It then WRITES
a Rome-100 game to that filename, so the England name is now attached to a Roman game.

Chained together, a player who does exactly what the game told them to do loses their
entire scenario/fog/purse/mortality configuration and is silently dropped into the
default scenario under the England file name. Confidence this is wrong, not intended:
**high** — the "Saved to ..." line is a direct factual claim that is untrue.

## FINDING 2 (LOW) — resume command it prints is a relative path that can't work
It prints `python3 rome/sim/simulator.py play --session england_1300.json`. The save
goes in the CWD (my playtest dir), but `rome/sim/simulator.py` only resolves from the
repo root. There is no directory from which that copy-pasted line works. Confidence: high
that it's inaccurate; low severity.

## FINDING 3 (LOW) — help contradicts the tutorial about input format
Tutorial: "Type commands in plain words." `help` says:
"how to send a command: One JSON object per line on standard input, for example
available or step 5. Each reply is one JSON object."
Plain words do work; JSON is not required and replies are not JSON. Leftover
machine-protocol text leaking into the human help. Confidence: high.

## FINDING 4 (COSMETIC) — Roman framing leaks into the England 1300 setup
The purse menu (shown *after* I had already chosen England 1300) prices things as
"well under the equestrian census of 100,000", "the equestrian census exactly",
"four senatorial fortunes in unminted gold", and the currency is denarii in 1300s
England (pennies/marks would be expected). Also "no employees, no slaves" for England.
Probably intended as a fixed yardstick, but it reads as unlocalised.

## FINDING 1b (HIGH) — the printed resume command is *wrong*, and it keeps printing it
Once a real England save exists, following the game's own instruction fails outright:
```
$ printf 'help commands\n' | python3 /home/user/test/rome/sim/simulator.py play --session england_1300.json
could not read the save file 'england_1300.json': this save is from a different
civilisation ('england_1300'); this game is running 'rome_100ad'. Start the agent
with --civ england_1300 to load it.
```
The working command is `play --civ england_1300 --session england_1300.json`.
Yet after every single session the game *still* signs off with the broken line:
```
Saved to england_1300.json. Come back with:
   python3 rome/sim/simulator.py play --session england_1300.json
```
So the only instruction the game gives for resuming a non-Roman scenario never works,
and in the one case where the file is absent it does something worse than fail
(silently starts Rome 100 — Finding 1). Confidence: **very high** this is a bug.

### Command list (from `help commands`)
state / available / why / start / stop / step / money / quote / close / risk / labour /
hire,fire,train,commission / buy / work / bounty / mothball,restore / bribe / policy /
path (disabled under fog) / save,load / help / quit

### Note on the first `available` output (1300 AD, 400 den)
- 103 startable. Cheapest six listed. Top of the list:
  `cap_measure_time_s  Time to the second (pendulum)   cost 0  hours 0  years 0  risk 0%`
  Expectation: a genuinely free, instant technology is suspicious — if it unlocks
  anything it is a free lunch. TO TEST.
- The hint line says "what you can pay for: available afford 1,151" while I hold
  400 den. Odd number to suggest to a player who cannot afford it. TO TEST.

### ENVIRONMENT NOTE (not a game bug)
At ~06:22 the repo copy of the simulator became un-importable mid-playtest:
```
File "/home/user/test/rome/sim/engine/core.py", line 782
    else:
    ^^^^
SyntaxError: invalid syntax
```
Somebody is editing the source live while I test. Not caused by my input; I waited
for it to come back. Recording it because it means my repros must be re-checked
against whatever version is current.

## FINDING 5 (HIGH, hard defect) — `quote` is completely unusable: the two error
## messages point at each other

Expectation: `help commands` says
`quote <what>: what something would cost before you commit to it; so far quote mine coal 500`
and `help economy` says "ASK THE PRICE FIRST with `quote mine coal 500`".
So I expected `quote mine coal 500` to print a mine price.

Actual (session: England 1300, 1301 AD):
```
> quote mine coal 500
REFUSED: no such material: None. Mineable: coal, copper, gold, iron, lead, silver, tin
> quote coal 500
REFUSED: only mines can be quoted so far: quote mine coal 500
```
Every variant tried — `quote mine coal`, `quote mine 500 coal`, `quote mine coal 500 tonnes`,
`quote mine`, `quote mine coal=500` — gives "no such material: None".
Every variant without the word `mine` — `quote coal 500`, `quote iron 500`, `quote coal` —
gives "only mines can be quoted so far: quote mine coal 500".
And bare `quote` gives a THIRD syntax: "quote needs something to quote, e.g. 'quote iron 500'."
which is itself refused.

So the documented command cannot be executed at all, and the game tells you to
buy a mine without ever being able to ask its price, which is the one thing the
help text insists you do first. Confidence it is a real defect: **very high**.

## FINDING 6 (MEDIUM) — `state` lies about founder-hours remaining
Repro (1300 AD, fresh England game):
```
> work scholar 2300
trade: scholar / hours: 2,300 / earned: 648.3 / capital: 1,076
your hours left this year: 0
> state
You: alive (you do not age), 2,400 founder-hours free this year   <-- wrong
> work scholar 1
REFUSED: you have 0 of your own hours left this year, not 1
```
The prompt header also stays at `you:2400 hr` all year. `state` is documented as
"where you stand"; the one number that changes hour to hour is the one it never
updates. Confidence: **high** it's a bug (the engine plainly knows the real figure).

## FINDING 7 (MEDIUM) — `risk` contradicts itself in consecutive lines
```
> risk
KNOWLEDGE AT RISK
technologies at risk: 4     chance lost if a site is sacked: 80%
hedge: none yet
no remaining hazard for this civilization sacks a site, so nothing here is
currently at risk of being forgotten
```
and `state` reinforces the first reading: "AHEAD: 4 technologies at risk if a hazard
lands, hedged by nothing yet". A player is told simultaneously that 4 techs are at
risk and that nothing is at risk. Confidence: medium-high that the headline is
misleading rather than intended.

## FINDING 8 (LOW) — misc text/rounding defects
- RUNNING line truncates the name and eats its closing bracket, so it reads:
  `Time to the second (pendulum 100% of your hours spent, 0 den still owed - waiting on the calendar`
- Prompt shows `1083 den` in the same breath as `state` showing `Money: 1,084 den`.
- `help money` prints the identical text to `help economy` (money has no topic of its own,
  though `help` advertises both).
- Developer shorthand leaks into player prose: `why med_cataract_couching` says
  "The rev is patient fees."; the Hundred Years War hazard text says
  "both applied gradually below as `values`" — backticks and all.
- `train machinist -3` replies "REFUSED: hours must be greater than zero" although
  `help labour` documents the argument as a number of people ("train machinist 2").

## WHAT I ATTACKED AND COULD **NOT** BREAK (good hardening)
Argument validation is genuinely solid. All of these were cleanly refused with
"Nothing was changed." and no state drift:
`hire smith -5`, `hire smith 1e9`, `hire nonexistent_trade 1`, `hire smith nan`,
`buy slaves -5`, `buy forest -10`, `buy forest inf`, `buy manumit 999` (no slaves),
`bribe -1000`, `bribe inf`, `commission smith -400`, `train machinist -3`,
`work scholar -100000`, `work scholar 100000` (bounded by remaining hours),
`work scholar inf`, `work scholar nan`, `step -5`, `step 0`, `step inf`,
`step 1e9` ("only 499 years left before the horizon at 1800").
NaN/Infinity are explicitly named and rejected everywhere I tried.
