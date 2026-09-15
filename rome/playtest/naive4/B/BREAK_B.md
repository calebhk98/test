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

## FINDING 9 (CRITICAL) — `bounty <id>` is an oracle that defeats fog of war entirely
Setup chose fog of war ON. The game states: "With it on ... You cannot see where anything
leads", and `path` is refused with "route planning is switched off under fog of war".
`why <hidden id>` correctly refuses: "you have never heard of that."

But `bounty` validates prerequisites BEFORE it checks whether you have heard of the thing,
and prints the missing prerequisites **by name**:

```
[1302 AD] > bounty point_contact_transistor
REFUSED: missing prerequisites: galena_detector, gp_whisker_forming, micrometer_gauges,
prc_lapping_plate, quantum_solidstate_theory, single_crystal, vacuum_tube

[1302 AD] > bounty vacuum_tube
REFUSED: missing prerequisites: cap_vac_1e6, copper_refining, diffusion_pump,
discharge_xray, gp_exhaust_pinchoff, gp_getter, gp_glass_metal_seal,
in2_electron_source_cathode

[1302 AD] > why vacuum_tube
REFUSED: you have never heard of that.
```
Two commands in the same session disagree about whether I have heard of `vacuum_tube`.

This is recursively exploitable. I wrote a breadth-first crawl that does nothing but
issue `bounty <id>` and read the refusal text (script kept in my scratch dir, it drives the
program only through stdin):

```
round 1: queried 1,  learned 1 nodes,   frontier 7
round 2: queried 7,  learned 8 nodes,   frontier 27
round 3: queried 27, learned 32 nodes,  frontier 53
round 4: queried 53, learned 67 nodes,  frontier 59
round 5: queried 59, learned 100 nodes, frontier 35
round 6: queried 35, learned 121 nodes, frontier 13
TOTAL distinct ids discovered: 134
```
In six rounds, from a standing start under fog, I recovered 134 hidden technology ids and
the complete dependency graph from the goal backwards — precisely the thing the mode
exists to withhold, and precisely what `path` refuses to give me.
Confidence this is a real defect: **very high**. `stop`, `mothball`, `restore`, `why`,
`path` and `available find` all guard the same information correctly; `bounty` is the
single hole.

## FINDING 10 (MEDIUM) — agent JSON protocol leaks into the plain-words UI
`available` / `available all`, HEARD OF section:
```
  fin_company_town   needs 1 trained craftsmen on your own staff, you have 0.0. To get
  more artisans: hire smith 3 or any trade in labour; or commission smith 400 to buy one
  job instead of employing anybody; {"cmd":"buy","what":"slaves","n":N} then manumit,
  though they are untrained for three years.
```
That `{"cmd":"buy","what":"slaves","n":N}` is machine protocol shown to a human player,
in the middle of a sentence whose other two suggestions are in plain words. Pairs with
Finding 3 (`help` telling a human to send JSON). Confidence: high.

## FINDING 11 (LOW-MEDIUM) — `available find X` does not filter the "HEARD OF" section
```
> available find transistor
AVAILABLE: 0 startable now
1-0 matching 'transistor'
(empty table)
HEARD OF, CANNOT BEGIN YET:
  cap_measure_time_ms ... chm_continuous_batch ... fin_company_town ... (all 9, unfiltered)
```
The same nine unrelated entries print for `available find vacuum`, `available find furnace`,
etc. The search says "matching 'transistor'" and then lists nine things that do not match.
Confidence: medium-high.

## FINDING 12 (MEDIUM) — `bounty` says it buys the work from someone else, then charges
## your own hours anyway (in the display at least)
`help commands`: "bounty <id>: pay someone else to solve it instead".
```
[1301 AD] > bounty fin_employment_contract
posted: fin_employment_contract / price: 23.4 / capital: 1,060
[1301 AD] > state
RUNNING (1):
  Contract of employment        65% of your hours spent, 0 den still owed - waiting on your hours
```
It did complete a year later without consuming founder hours (state still showed 2,400 free),
so the *outcome* looks right and the *status line* is wrong — "waiting on your hours" for a
job you explicitly paid someone else to do. Confidence it's a display bug: medium-high.
Side note: posting a bounty raised suspicion from 0 to 2, which is never explained anywhere.

## Positive: bounty eligibility rules are well written
```
> bounty opt_gravimeter
REFUSED: not bounty-eligible (tier 3, category measurement): a craftsman in England under
Edward I could not recognise success at this without understanding the theory, so there is
nothing to award the prize for. A bounty works where the craft already exists here and
success is visible.
```
Good rule, well explained — which makes it more jarring that the same command leaks the tree.

## Save-file handling: attacked, could not break
- `save /tmp/x.json` -> "a save file must be a relative path, not an absolute one."
- `save ../../../../../tmp/traversal2.json` -> "a save file cannot be written outside the
  directory you started in." Nothing was written to /tmp.
- `load /etc/passwd` -> refused (absolute path).
- `load` of non-JSON, empty file, truncated JSON, and a valid-JSON-wrong-shape file all
  produced clean REFUSED lines, including a helpful "A save this game writes always has all
  of: year, capital, done, active, _civ, _version".
- Hand-editing `capital` to `1e30` in the save and loading it is accepted (single-player,
  low severity) and does NOT crash: stepping a year with 1e30 den works, and living costs
  scale with wealth so it self-corrects downward. Worth noting: 1e30 denarii in 1302 England
  produced suspicion 0 — conspicuous wealth appears not to be modelled as conspicuous.

## FINDING 13 (MEDIUM-HIGH) — in the default England 1300 playthrough the Great Famine
## never happens, though the game names it twice as a dated certainty
Expectation: the scenario briefing says "Fifteen years to the Great Famine. Forty-eight to
the Black Death", and `risk` lists `[1315-1317] Great Famine  staff loss: you take 100% of it`.
I expected both to land on schedule.

Repro — six independent fresh games, identical configuration, no player actions at all:
```
for i in 1..6:  printf '4\ny\npoor_scholar\nn\nstep 60\nstate\n' | python3 rome/sim/simulator.py
```
Every one produced: `EVENT 1348: Black Death: staff -45%`, `EVENT 1349: Black Death: staff -45%`
and **zero** Great Famine events. `grep -i famine` finds the word only in the opening blurb.

Two further points from the same experiment:
- All six fresh games produced byte-identical event histories: same fires (1304, 1329, 1336,
  1340), same war, same plague years. A new game is fully deterministic, so "the lifespan
  lottery" the setup screen contrasts itself against does not exist for hazards either.
- Yet the hazard rolls ARE perturbed by ordinary play. From a save made after a couple of
  `work`/`start` commands, the Great Famine DOES fire (`EVENT 1315: Great Famine: staff -12%`,
  `EVENT 1317: ...`); from another save two years later the **Black Death never fires at all**
  across 1300-1800 (`grep -c 'Black Death'` = 0 over the whole run to the horizon).
  So which of the two defining catastrophes of the scenario you get depends on incidental
  earlier commands. Confidence: medium-high that at least the "certain, dated" framing is wrong.

Related realism note: both plagues report "staff -12%" / "staff -45%" when you employ nobody,
so in a solo run the two demographic catastrophes the scenario is built around have exactly
zero mechanical effect. And `EVENT: fire in the thatched lanes behind the market` fires
repeatedly against a player who owns no buildings.

## FINDING 14 (MEDIUM) — `bribe` will take any amount of money to fix a scandal of zero
```
[1302 AD | 1052 den] > bribe 500
bribed: scandal 0.00 -> 0.00 for 500 denarii
capital: 552.8
```
Half my capital, gone, for a no-op. Every other command in the game refuses a pointless or
impossible action with "Nothing was changed." (`buy manumit 999` -> "you have no slaves to
free"; `close coal` -> "you have no coal workings"; `mothball fin_employment_contract` ->
"that costs nothing to keep; there is nothing to save"). `bribe` alone silently burns it.
Confidence: high.

## FINDING 15 (MEDIUM) — `auto shed` is on by default and quietly deletes your score
`policy` shows `auto shed: True`, described as "let go of WORKS that cost more than they
return (this is about buildings and practices, not people)". In a long run:
```
EVENT 1359: stopped maintaining 1 works that cost more than they returned: cap_measure_time_s
```
and `state` went from "2 built by you" to "1 built by you". The end-of-run verdict is
"You built 1 things of your own" — the game's only score, silently revised downward by an
automation that is on unless you find and switch it off. Note the very first thing
`available` offers a new player, `cap_measure_time_s`, is a 0-cost 0-hour item with 20 den/yr
upkeep and no revenue, i.e. exactly the thing auto-shed will later delete.
Also "You built 1 things" — grammar.

## FINDING 16 (LOW) — mothball/restore is free and instant, so upkeep is optional
```
> mothball cap_measure_time_s
mothballed: ... you stop paying 20 a year for it
> restore cap_measure_time_s
restored: cap_measure_time_s back in service for 0 denarii
```
No cost, no delay, unlimited repetition. Upkeep can be dodged by mothballing in the years
you do not need a thing. Confidence it is exploitable: high; severity low.

## FINDING 17 (MEDIUM) — the ledger pays you for things the game says are not yours
`money` at 1302:
```
Capital: 552.8 den     Revenue: 253.5 den/yr
  from:
    med_cataract_couching        181.5
    med_trepanation               72.6
```
That is my entire income. But:
```
> mothball med_cataract_couching
REFUSED: that is something the society has, not something you maintain; there is no upkeep
of yours to stop
```
So the same two technologies are simultaneously "the society's, not yours" and the sole
source of your personal revenue, and you cannot stop, sell or mothball them. It also means
the "poor scholar, 400 den, about enough to eat for a few months" framing is wrong: you
actually start with a ~250 den/yr medieval eye-surgery and skull-drilling practice that you
never chose and cannot decline. Confidence something is inconsistent: high.

## FINDING 18 (LOW) — repeating insolvency loop with no way out and no warning
Left alone, the England run goes bankrupt on a fixed 10-year cycle for centuries:
```
EVENT 1385: INSOLVENCY SETTLED: the debt is written off, you keep your name and your
knowledge, and you begin again poor
EVENT 1395: INSOLVENCY SETTLED: ...
EVENT 1405: ... 1415 ... 1425 ... 1435 ... 1445 ... 1455 ... 1470 ...
```
Also note the text says "you keep your ... knowledge", yet my built-tech count had already
dropped from 2 to 1 (Finding 15) — the two messages tell the player opposite things about
whether what they built survives.

## Determinism: attacked, could not break
Same save + same commands is bit-for-bit reproducible. Slicing time differently does not
change history: `step 60`, `step 20`x3, `step 1`+`step 59`, and `step 1`x60 from the same
save all produce the identical 42-event log. Read-only commands (`state`, `labour`) inserted
before a step do not perturb it. That is a good property and I could not shake it.

## FINDING 19 (HIGH) — `buy mine` takes every denarius you have, silently, and the only
## tool the game tells you to use first was broken
`help economy`: "buy mine coal 500 ... ASK THE PRICE FIRST with quote mine coal 500".
At the time, `quote` was unusable (Finding 5). What `buy` actually did, with 1,084 den:
```
[1301 AD | 1083 den] > buy mine coal 500
material: coal
you asked for t per yr: 500
commissioned t per yr: 109.5
ready year: 1,304
years until producing: 3
capital: 0
note: less than you asked for: limited by capital, by the ceiling your standing supports,
or both. Nothing was wasted, you paid only for what was sunk.
[1301 AD | 0 den ...]
```
It spent 100% of my capital on 22% of what I asked for, with no confirmation step, and the
consolation note is "Nothing was wasted". Four years later:
```
Costs:  mines standing 180.6      Net/yr: -172.9
> close coal
closed: ... You stop paying 181 a year. What you spent sinking them is gone
```
i.e. 1,084 den sunk and destroyed, plus 181/yr, for coal that fed nothing. A single
mistyped order can end a poor-scholar run. Confidence it is at least a serious usability
defect: high. (Note the ledger also shows `mines standing 0` during the three years the
shaft is being sunk, so the cost is invisible until it starts.)

## FINDING 20 (MEDIUM) — "the debt is written off" leaves you in debt, and takes your name
Repro: fresh England game, build two things, then start three projects you cannot afford
(`fud_whaling_industry`, `chm_phosphorus_extraction`, `fin_inn`) and `step 12`:
```
EVENT 1310: CREDIT EXHAUSTED: 3 projects halted, unfinished. Nobody will fund new work here for some years
EVENT 1310: INSOLVENCY SETTLED: the debt is written off, you keep your name and your knowledge, and you begin again poor
```
After it: `Capital: -820.4 den`, `Credit limit: 271.5`, `reputation 0.10` (was 8.6).
So of the sentence's three promises — debt written off, keep your name, begin again — the
debt is NOT written off (you are left owing three times your new credit limit, hence
immediately insolvent again), and your name is gone. Only "knowledge" held up: built
technologies did survive.
This is the engine of Finding 18's endless 10-year insolvency cycle: settlement leaves you
below your own credit line, so it re-fires forever. Confidence: high.

## FINDING 21 (MEDIUM) — starting many projects at once blows past the stated credit limit
```
(fresh 1300 game, 400 den, "Credit limit: 1,503")
> start <each of the 102 available ids>
> step 1
```
102 projects accepted with no cap and no warning; `Still owed on work in hand: 44,063`
against 400 den. From a 1,084-den save the same move spent 6,339 den in one year and left
`Capital: -5,554` — 3x the 1,772 credit limit that was displayed when I made the decision.
The limit is recomputed upward afterwards (reputation jumped 5.9 -> 31.7 from the 20
completions), so the engine ends up "in limit" against a number that did not exist when the
money was committed. `help economy` says "You may spend past what you have, as far as
somebody will lend you and no further" — this is further. Confidence: medium-high.

## FINDING 22 (MEDIUM) — the setup screen's claim about starting wealth is not true in play
The purse menu says of `absurd`: "What it does NOT do is make you a magician, and across the
whole kit range the medians sit inside the noise band anyway."
I ran the identical scripted strategy (each year: start everything affordable within 60% of
capital, then step) for 12 years, once per purse, same scenario, same fog setting:
```
destitute:      1312  built=8    money=83
poor_scholar:   1312  built=51   money=2,366
artisan:        1312  built=84   money=4,720
merchant:       1312  built=115  money=16,862
rich_merchant:  1312  built=143  money=30,590
equestrian:     1312  built=109  money=35,459
absurd:         1312  built=109  money=407,990
```
8 to 143 is not a noise band. A cruder strategy (bounty+start everything, unbudgeted) gives
`poor_scholar built=0` vs `absurd built=86` over the same 12 years. Two secondary oddities:
the curve is non-monotonic above 20,000 den (rich_merchant beats both equestrian and absurd,
because "living and appearances" scales with capital), and `bounty` turns money straight into
technology with no founder-hours at all — 9 completions in a single year from one round of
bounty posting. Confidence the quoted claim is wrong as a player would read it: medium-high.

## FINDING 23 (LOW) — misc parser/UI observations
- `step 1; step 1` executes one step and silently discards the rest of the line.
- `why AAAA...(5,000 chars)` echoes the whole 5,000-char string back inside the error.
- `WHY AG2_MARLING` -> "unknown node 'AG2_MARLING'. did you mean: ag2_marling". It knows the
  answer and still refuses; ids are case-sensitive with no reason given.
- More JSON leaking into human errors: `start ../../etc/passwd` ->
  `use available or {"cmd":"why","id":...} to find valid ids`.
- Project status says "waiting on money" for a 10.2-den project while holding 1,084 den.
- `EMPLOY: 0.05 people, 5.8 den/yr in wages` — fractional human beings on the payroll.
- Bounty ineligibility reasons are category-derived and often absurd for the item:
  `bounty hom_eraser_breadcrumb` (a breadcrumb used as an eraser) and
  `bounty med_obstetric_practice` (tier 0 obstetrics) are both refused because "a craftsman
  in England under Edward I could not recognise success at this without understanding the
  theory". Midwives and bread existed.
- The founder earns 0.28 den/hr doing `work scholar`, while `labour scholar` says the market
  wage for a hired scholar is 0.35 den/hr. The man with all modern knowledge is paid 20%
  below the going rate for an ordinary literate man.

## FINDING 24 (REALISM) — chattel slaves for sale in Edward I's England
```
> buy slaves 5
REFUSED: cannot afford 5 slaves: 2124 denarii (425 each after the market moves against a
purchase this size) and you have 1084
```
The refusal is purely financial — the market exists and is priced. `help economy` defends the
mechanic as "the ordinary condition of production in most of these societies", but chattel
slavery was gone from England by ~1200; Edward I's England ran on villeinage. The same screen
also prices everything in denarii and describes fortunes as multiples of "the equestrian
census" and "senatorial fortunes" (Finding 4), and `available` in 1300 England offers me
Papyrus, Parchment, Roman cosmetics, Obsidian blade knapping, a Groma, a Chorobates, a
societas, argentarii and the Annona grain dole. The England scenario is very thinly
localised over a Roman one. Confidence it is unintended: medium.

---

## LIVE-PATCH NOTE (important for reproducing my findings)
The repository was being edited by someone else throughout this session. At 06:38 UTC,
`git log --oneline -3` showed:
```
88d65a5 A save knows what game it is; the command line had to be told again
0044f6e A project could be refunded hours it never spent
```
Re-verifying at 06:38 against the current build:
- FINDING 5 (`quote` unusable) is now **FIXED**: `quote mine coal 500` and `quote coal 500`
  both print a proper quote ("to sink it: 4,950 / every year it stands: 825 / years before
  it produces: 3 / you can afford about: 109.5"). It was genuinely broken earlier in the
  session; I am recording it because Finding 19 (`buy mine` eats your capital) was only
  survivable in the window where it was broken.
- FINDING 1b (`--civ` needed to resume) is now **FIXED**: `play --session england_1300.json`
  resumes England correctly.
- FINDING 1a still reproduces on the current build:
  ```
  mkdir /tmp/ttt && cd /tmp/ttt
  printf '4\ny\npoor_scholar\nn\n' | python3 /home/user/test/rome/sim/simulator.py
  -> "Saved to england_1300.json. Come back with: python3 rome/sim/simulator.py play --session england_1300.json"
  ls /tmp/ttt   -> empty, no save written
  printf 'state\n' | python3 rome/sim/simulator.py play --session england_1300.json
  -> "You arrive in 100 AD ..."  (Rome, silently)
  ```
- FINDING 6 (`state` shows 2,400 founder-hours after spending them), FINDING 9 (bounty leaks
  the hidden tree), FINDING 14 (`bribe` burns money on zero scandal) all still reproduce
  at 06:38.

## FINDING 25 (MEDIUM-HIGH) — the only warning in the STANDING block is inert, and its
## prediction never comes true
`state` prints, every turn:
```
STANDING: reputation 5   suspicion 0   scandal 0   eminence 0
  dangerous above 26 (settles near 0.10 if nothing changes; 0% chance of ruin this year)
```
Expectation: crossing 26 should make ruin possible, and "settles near X" should be where the
number drifts if I stop provoking it. Also, the line never says *which* of the four numbers
26 applies to; by experiment it is suspicion (each `bounty` posted adds +2).

Repro: load a save with 500,000 den, post ~15 bounties a year for three years, then idle:
```
STANDING: reputation 26.5   suspicion 30   scandal 2.0   eminence 0.43
  dangerous above 26 (settles near 6 if nothing changes; 0% chance of ruin this year)
> step 20
STANDING: reputation 18.9   suspicion 30   scandal 0.20   eminence 4.3
  dangerous above 26 (settles near 4.5 if nothing changes; 0% chance of ruin this year)
```
- suspicion sits at exactly 30 — four points past "dangerous" — and the chance of ruin is
  reported as 0% every year for 23 consecutive years.
- suspicion is apparently hard-capped at 30: further bounties do not move it.
- "settles near 4.5 if nothing changes" — nothing changed for twenty years and it did not
  move one point.
So the game's single standing danger indicator names a threshold that does nothing, and
makes a prediction that is contradicted by the next twenty turns of its own output.
Confidence: high that at least the text is wrong.

---

# SUMMARY OF WHAT I ATTACKED AND COULD NOT BREAK
- **Numeric validation.** Negative, zero, NaN, Infinity, 1e9 and non-numeric arguments to
  `work`, `hire`, `fire`, `train`, `commission`, `buy`, `bribe`, `step`, `quote` are all
  refused cleanly, usually with "Nothing was changed." NaN/Infinity are called out by name.
- **Founder-hour budget.** Cannot be overdrawn; `work` is correctly capped at the remaining
  hours (only the *display* of the remaining hours is wrong, Finding 6).
- **Path handling.** `save`/`load` refuse absolute paths and `../` escapes; nothing was ever
  written outside the start directory.
- **Malformed saves.** Non-JSON, empty, truncated and wrong-shape JSON all refused with clear
  messages; no traceback. Hand-tampered capital of 1e30 is accepted but does not overflow or
  crash, and the wealth-scaled living costs pull it back down.
- **Determinism.** Same save + same commands is bit-identical. `step 60` == `step 20`x3 ==
  `step 1`x60 (identical 42-event log). Read-only commands do not perturb the RNG.
- **Fog of war, everywhere except `bounty`.** `why`, `path`, `start`, `stop`, `mothball`,
  `restore` and `available find` all refuse to name a technology you have not heard of.
- **Duplicate/illegal state changes.** `start` twice -> "already active"; `stop` twice ->
  "not active"; `restore` something not mothballed -> refused; `close` a mine you do not own
  -> refused; `mothball` something with no upkeep -> refused.
- **Command injection / odd input.** Shell metacharacters, SQL-ish strings, HTML, NUL bytes,
  5,000-character ids, empty lines, tabs and non-ASCII all produce ordinary refusals, never
  a crash.
- No traceback or unhandled exception was ever produced by anything I typed. The single
  crash I saw (`SyntaxError` in the engine, ~06:22) was another agent editing the source
  mid-session, not my input.
