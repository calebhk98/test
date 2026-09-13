# BREAK_B — playtest notes

Target: `/home/user/test/rome/sim/simulator.py`
Scenario requested: Rome, 100 AD; fog of war ON; poor scholar purse; founder does NOT age.
Rule I am following: I only learn things from the running program. No source reading.

## Log

### Step 0 — before I start
Expectation: an interactive setup wizard asks era/place, fog, purse, ageing; then hands me a
session file and a `play --session <file>` invocation. I expect piping lines to work.

### Setup
Answers piped: `2` (Rome), `y` (fog), `poor_scholar`, `n` (no ageing).
Session file: `rome_100ad.json` written into cwd. Resume works exactly as advertised.

Baseline at 100 AD: 400 den, 2000 founder-hr, rep 5, scandal 0, eminence 0,
137 technologies "granted for free", 0 built. Target: point-contact transistor by 600.

**Observation 1 (candidate inconsistency).** `help commands` says:
  "open <id>: start actually running something you have worked out how to do;
   until you do, it earns nothing and costs nothing"
But `money` on turn 0, with nothing started and nothing opened, already shows
  Revenue: 233.5 den/yr  from: med_cataract_couching 166.7, med_trepanation 66.7
Expectation was 0 revenue. Need to check `ventures` to see whether these count as "open".

**Observation 2.** `available` suggests `available afford 1,083` as "what you can pay for"
while capital is 400 and credit limit 1,367. 1083 is neither. To check.

### FINDING 1 (confirmed contradiction) — revenue from ventures that do not exist
Expected: `ventures` and `money` agree about what is earning.
Actual, same session, no commands in between:
```
> ventures
RUNNING
  nothing
YOU KNOW HOW, AND HAVE NOT OPENED
  nothing
Knowing how to do a thing and running it are different. Only what you are
RUNNING earns anything or costs anything.
> money
Capital: 400 den     Revenue: 233.5 den/yr
  from:
    med_cataract_couching        166.7
    med_trepanation              66.7
```
`ventures` says nothing is running and nothing earns; `money` says 233.5 den/yr is coming in
from two named concerns. The screen's own sentence ("Only what you are RUNNING earns
anything") is falsified by the other screen. Confidence this is wrong: HIGH — the two
statements cannot both be true.

### FINDING 2 (candidate) — risk mitigation advice does not match the stated remedy
```
> risk
[165-180] Antonine plague
  probably smallpox or measles
  staff loss: you take 100% of it
    what would help: clean water, quarantine, and eventually inoculation
    you could begin now: horse_collar (709.4 den)
```
The prose remedy is sanitation/quarantine/inoculation; the concrete suggestion is a
**horse collar**. A padded horse collar does nothing about smallpox. Looks like the
"you could begin now" line is picking from a generic list rather than from the hazard's
actual mitigators. Confidence: MEDIUM-HIGH that this is a bug.

Also in the same block: "staff loss: you take 100% of it" immediately followed by
"staff loss after what you have built: 28%" — with nothing built. Two numbers for the
same quantity in adjacent lines.

### FINDING 3 (confirmed contradiction) — how many people do I have?
Four screens, same turn, four different answers:
- prompt line:            `sch 0 art 0`
- `labour`:               "ON YOUR STAFF: nobody ... Total employed: 0"
- `ventures`:             "free to put behind something new: 1 scholars, 1 craftsmen"
- `why horse_collar`:     "STAFF NEEDED: 0 scholars, 1 artisans   (you have 1, 0)"
So ventures claims a spare craftsman that `why` says I do not have, and `why`/`ventures`
claim a scholar that the prompt and `labour` say I do not have. Confidence: HIGH that at
least two of these are inconsistent (the founder is plausibly the "1 scholar", but that
cannot also explain the "1 craftsmen").

### FINDING 4 (confirmed contradiction) — per-venture revenue disagrees with the ledger
`why med_trepanation` -> "REVENUE: 200 den/yr" and "STATUS: DONE / THIS SOCIETY ALREADY
HAS THIS. You did not build it and do not maintain it."
`money` -> "med_trepanation 66.7".
200 vs 66.7 for the same line item, and it is money from something the game explicitly
says I did not build and do not maintain. Confidence: HIGH on the mismatch.

### work
`work scholar 500` -> earned 160.2 (0.3204 den/hr), capital 400 -> 560.2, hours 2000 -> 1500.

### FINDING 5 (mechanic never disclosed) — "revenue" is really the founder's own unspent hours
Revenue tracks remaining founder-hours exactly:
  2000 hr free -> Revenue 233.5   (cataract 166.7 + trepanation 66.7)
  1500 hr free -> Revenue 175.2   (125 + 50)          = 233.5 x 0.75
     0 hr free -> Revenue 0
So the 233.5 den/yr is the founder personally doing surgery, prorated by idle hours.
Nothing in `why`, `ventures`, `money` or `help` says this. `why med_trepanation` states a
flat "REVENUE: 200 den/yr" that is never the number you actually get, and `ventures`
insists nothing is running. Confidence the display is misleading: HIGH.
Also `work scholar 2000` would pay 640.8 den vs 233.5 passive, so the "free" revenue is
strictly the worst use of the same hours - a trap for a player reading `money`.

### FINDING 6 (candidate) — credit limit ignores capital, and falls as you get richer
  capital  400 den, revenue 233.5 -> credit limit 1,367
  capital  560 den, revenue 175.2 -> credit limit 1,338
  capital 1041 den, revenue   0   -> credit limit 1,250
Fit: credit = 1250 + 0.5 x revenue. Capital contributes nothing. Tripling my cash
LOWERED my credit limit. A Roman lender who cares about your surgical income but not at
all about the money in your strongbox is odd. Confidence: MEDIUM (could be deliberate
"lending against income", but the direction of travel is clearly wrong to a player).
Living-and-appearances also *fell* (230 -> 228.9 -> 225.6) as capital rose, which is
backwards for a cost described as "appearances".

### Note: the program became unrunnable mid-session (not caused by me)
At 103 AD, after `available all`, every invocation began dying at import time:
```
Traceback (most recent call last):
  File "/home/user/test/rome/sim/simulator.py", line 46, in <module>
    from engine.protocol import (_agent_available, _agent_dispatch,  # noqa: F401
ImportError: cannot import name 'load_state' from 'engine.protocol'
```
I have modified nothing in the repository; this appeared between two consecutive runs of
the same command line, so the tree is being edited underneath me. Waiting and retrying.

### FINDING 7 (confirmed) — "waiting on your hours" when my hours are not the constraint
`start tr_hopper_wagon` (needs 50 founder hours, calendar floor 1 year), then `step 1`:
```
RUNNING (1):
  tr_hopper_wagon   60% of your hours spent, 0 still owed - waiting on your hours
You: alive (you do not age), 2,000 founder-hours free this year
```
It claims to be waiting on my hours while 2,000 of my hours sit unspent and it needs 20
more. It was actually waiting on the one-year calendar floor - it finished the next step.
A status line whose stated reason is not the real reason. Confidence: HIGH.

### FINDING 8 (confirmed) — staff requirements are advertised and then not enforced
`why tr_hopper_wagon` -> "STAFF NEEDED: 0 scholars, 1 artisans   (you have 1, 0)" and in
the same breath "STATUS: CAN START NOW". `labour` says "Total employed: 0 ... nobody".
I started and completed it with zero artisans on the staff. `help labour` insists
"Trades are NOT interchangeable: a project asking for an engineer cannot be built by
smiths however many you have" - but a project asking for an artisan can apparently be
built by nobody at all. Confidence: HIGH that STAFF NEEDED is cosmetic here.

### FINDING 9 (candidate) — the founder's hour has two prices, 24x apart
`work scholar` pays the founder 0.3204 den/hr (80% of the 0.40 den/hr market scholar wage).
`bounty tr_hopper_wagon` costs "about 649" against a build cost of 266.1 - i.e. 383 den to
avoid spending 50 founder hours, or 7.66 den/founder-hour. The same hour is worth 0.32 den
when you sell it and 7.66 den when you buy your way out of it. Confidence: MEDIUM
(defensible as scarcity pricing, but nothing in the game says so).

### Guarded successfully (could NOT break)
- `work scholar -1000` / `hire scholar -3` / `buy slaves -5` / `bribe -1000` /
  `commission smith -400` / `step -5` / `step 0`: all REFUSED with a clear reason.
- `work scholar 99999` refused ("you have 1500 of your own hours left this year").
- `work chemist 100` refused because the trade does not exist here - correct and consistent
  with `labour`.
- `work nonexistent 100` refused with the list of real trades.
- Fog of war held: `path point_contact_transistor`, `why point_contact_transistor` and
  `available find transistor` all reveal nothing ("you have never heard of any such thing").
- `fire scholar 5` with 1 employed succeeded silently rather than refusing (cosmetic).

### FINDING 10 (confirmed, serious) — `load` validates the filename and nothing else
`save backup1.json`, then edit that file by hand (`capital` -> 1e12, `_fog` -> false),
then in the running game:
```
> load cheat.json
loaded: cheat.json
year: 107
[107 AD | 1000000000000 den | ...] > help fog
  fog of war: OFF. You can see the whole tree.
> path arithmetic_positional
id: arithmetic_positional ...
```
The `state` header even flips from "Fog of war is on: you see the next step, never the
road." to "Goal: point_contact_transistor", and `path` - which had been refusing with
"not available under fog of war" - starts answering.
Notable because the path checks ARE careful: `load /nonexistent/x.json` is refused with
"a save file must be a relative path", `load BREAK_B.md` with "a save file should end in
.json or .save". So the filename is validated and the contents are not at all.
Confidence: HIGH that this is unintended for the fog switch specifically - fog is chosen
once at setup and `help fog` says "there is no way to view the whole tree".
(I restored `backup1.json` afterwards and kept playing with fog ON. The 1e12 experiment
also revealed that living-and-appearances is ~1.5% of capital plus a base:
capital 1e12 -> "living and appearances 15,000,000,270".)

### FINDING 11 (confirmed) — supervision is enforced for some concerns and not others
I employ nobody (`labour`: "Total employed: 0", wages 0). Yet:
```
> ventures
RUNNING
  tr_hopper_wagon    600  40   NEEDS 0 sch   1 cr      <- running on zero employees
YOU KNOW HOW, AND HAVE NOT OPENED
  tex_mordanting     150  15   TO OPEN 19.4
> open tex_mordanting
REFUSED: nobody free to keep an eye on it: it needs 0.0 scholars and 0.1 craftsmen to
supervise, and you have 1.0 and 0.0 not already watching something else.
```
A concern needing 1 craftsman runs with none; a concern needing 0.1 craftsmen is refused.
And in the same breath `ventures` says "free to put behind something new: 1 scholars,
0.03 craftsmen" while `open` says "you have 1.0 and 0.0". 0.03 vs 0.0 for the same
quantity, one line apart. Confidence: HIGH.

### FINDING 12 (confirmed) — `policy auto_open` does not do what its own text says
Text: "auto open: open concerns that plainly pay for themselves. It will NOT open anything
whose upkeep exceeds its takings, however much you need it."
With `auto_open` ON, 6,262 den in hand, `tex_mordanting` (earns 150/yr, upkeep 15/yr) sat
unopened for 6 consecutive years. The real reason is the craftsman-supervision check above,
which the policy text never mentions and which makes the stated rule wrong: the thing
plainly pays for itself and is not opened. Confidence: HIGH that the description is wrong;
MEDIUM that the behaviour is.

### Hire/open/fire probe — engine catches it, but punishes the wrong thing
`hire artisan 3` -> `open tex_mordanting` -> `fire artisan 3` -> `step 1` gives:
"EVENT 114: nobody left to keep an eye on 1 concern, so tr_hopper_wagon closed."
It closed the 600 den/yr concern and kept the 150 den/yr one I had just sneaked open.
Not exploitable for profit, but the choice of victim is the worst possible one.

### FINDING 13 (confirmed, single-screen arithmetic error) — wage bill vs "each"
In a scratch game (`scratch_hire.json`, seeded from my own save with capital raised):
```
> hire artisan 3   -> you now employ: 3   annual wage bill: 779.9
> fire artisan 3
> hire artisan 3   -> annual wage bill: 869.7
> hire artisan 1   -> you now employ: 4   annual wage bill: 1,190
> labour
ON YOUR STAFF:
  artisan                 4   250 den/yr each
Total employed: 4     annual wage bill: 1,190 den
```
4 x 250 = 1,000, not 1,190. `labour trade artisan` also says "a year of one: 250 den".
The real behaviour is a rising scarcity premium per extra head (259.97, then 289.9, then
320.3 for the fourth) that no screen ever shows. Confidence: HIGH that the display is wrong.

### FINDING 14 (confirmed) — bought slaves do nothing at all
```
> buy slaves 100
bought: 100
slaves: 100                (capital 200,000 -> 134,665, so 65,335 den)
> labour
ON YOUR STAFF: nobody      Total employed: 0     annual wage bill: 0 den
IN TRAINING:
  None x27.5, ready 110.0          <- the trade is literally named "None"
> ventures
free to put behind something new: 1 scholars, 0.33 craftsmen   (unchanged)
> open tr_hopper_wagon
REFUSED: nobody free to keep an eye on it: it needs 0.0 scholars and 0.4 craftsmen to
supervise, and you have 1.0 and 0.3 not already watching something else.
```
65,335 denarii of human beings bought and nothing anywhere changed. Worse, the refusal
message itself advertises them as the fix: "To get more artisans: ... buy slaves N then
manumit, though they are untrained for three years." Confidence: HIGH that the "None x27.5"
label is a bug; MEDIUM-HIGH that the three-year delay is the intent and the message is
merely wrong to offer it as a fix for a same-turn problem.

### FINDING 15 (confirmed) — manumission is a free, unlimited, same-turn reputation pump
In one turn at 107 AD, with no time passing:
```
buy slaves 20 / buy manumit 20   x40
```
`buy manumit` is free (capital never moves on the manumit line) and each cycle adds
reputation. Reputation went 8.1 -> 39.7 inside a single year, past the "EMINENCE is
dangerous above 26" line, while eminence stayed at 0.04 and scandal at 1.7. 800 freedmen
and `labour` still says "Total employed: 0". `help money` says freedmen "then work better",
which they cannot, since they do not work at all.
Cost was ~1.9M den for +31.6 reputation, so it needs a big purse - but there is no per-turn
limit, no eminence penalty and no scandal. Confidence: HIGH that unbounded same-turn
cycling is unintended.

### FINDING 16 (candidate) — a refusal that tells you to do the thing it just refused
```
> hire artisan 2
REFUSED: you can supervise, house and teach 0.00 more people, not 2 - you have no room for
even one. To get more artisans: hire smith 3 or any trade in labour; or commission smith 400
...; buy slaves N then manumit
```
It refuses hiring on a capacity ground and then advises hiring. Confidence: HIGH that the
advice is wrong for this refusal.

### Mine standing cost — quote vs behaviour
`quote mine coal 500` promises "every year it stands: 750" and "The yearly cost is charged
whether or not you use the output". Ledger shows "mines standing 0" for the whole 3-year
sinking period (107-110) and 750 only from 111. Confidence: LOW that this is a bug - the
wording is ambiguous - but a player reading "charged whether or not you use the output"
will budget for it from the day they buy.

### FINDING 17 (confirmed) — "waiting on money" with the money in hand; and two identical
### calendar floors behaving differently
Scratch from `backup1.json` (107 AD, 320 den, revenue 1,005/yr):
```
> start tr_wooden_waggonway        (bill 204.9, CALENDAR FLOOR 1 years)
> step 1
> state
  tr_wooden_waggonway   100% of your hours spent, 102.5 still owed - waiting on money
Money: 904 den
```
904 denarii in the purse, 102.5 owed, and the game says it is waiting on money. It is not:
it finished on the next step regardless. Exactly half the bill (102.4 of 204.9) was paid in
year one, so there is an undisclosed per-year spend throttle and the status line blames the
wrong thing.

Control, same starting save, same 1-year calendar floor, same 320 den:
```
> start arithmetic_positional      (bill 1,032, CALENDAR FLOOR 1 years)
> step 1
  COMPLETED 107: Decimal positional notation ...
```
The 1,032-denarius project completed in one year out of a 320-denarius purse without a
murmur, while the 204.9-denarius one stalled "waiting on money". Confidence: HIGH that at
least the message is wrong, MEDIUM-HIGH that the throttle rule itself is inconsistent.

(Earlier instance of the same bug with a different wording: `tr_hopper_wagon`, 50 founder
hours needed, 2,000 free, reported "60% of your hours spent ... waiting on your hours".)

### FINDING 18 (confirmed, and the biggest one) — the currency debasement changes no price
`start <id>` prints, every single time:
  "note: This is the price as of today, and it is now fixed for this project. Quotes move
   with prices, the coinage and what a material costs to get: a figure you read years ago
   is not what you will pay."
`risk` lists "[190-275] Currency debasement / real erosion: you take 100% of it".
Scratch run from 107 AD, `step 100`, `step 100`:
```
  EVENT 220: Currency debasement: the coin is worth 85% less than it was
  EVENT 235: Currency debasement: the coin is worth 94% less than it was
  EVENT 250: Currency debasement: the coin is worth 97% less than it was
  EVENT 265: Currency debasement: the coin is worth 99% less than it was
```
and the quote for the same technology, read at 107 AD, at 207 AD and at 307 AD:
```
COST: 709.4 den total  (261 labour + 173.6 materials + 400 capital, then x0.85 your civ,
                        x1 distance, x1 scarcity, x1 prices)
```
Identical to the decimal, with the price multiplier still x1, after the game has told me
four times that the coin lost 99% of its value. Revenue fell only about a third
(1,005 -> 657.9 den/yr) and living costs rose only 282 -> 343. A player who took the
"quotes move with the coinage" note seriously and hoarded goods instead of coin was misled;
a player who hoarded coin lost nothing. Confidence: HIGH that the promise is not kept.
(The save file has a `money_real` field, so there may be a real-terms figure behind the
scenes - but nothing the player is shown moves.)

### FINDING 14 (revised and sharpened) — `labour` never shows the people you bought
Clean scratch (capital raised to 5,000,000, 107 AD):
```
> buy slaves 20
bought: 20   slaves: 20   capital: 4,992,201        (7,799 den, ~390 each)
> labour
ON YOUR STAFF: nobody
IN TRAINING:
  None x11, ready 110.0                    <- trade name "None"; 11, not the 20 I bought
Total employed: 0     annual wage bill: 0 den
> step 3
  EVENT 110: 20 of the people you bought finish learning the work
> labour
ON YOUR STAFF: nobody       Total employed: 0     annual wage bill: 0 den
> ventures
free to put behind something new: 1 scholars, 14.5 craftsmen
```
Three separate defects on one mechanic:
1. the trade of a bought person prints as the literal string "None";
2. IN TRAINING shows 55% of the true number every time (20 -> 11, and 50 -> 27.5 in a
   second run), while the arrival event correctly reports all 20;
3. once trained, 20 enslaved craftsmen exist and are usable (`ventures` jumps from 0.5 to
   14.5 free craftsmen) but `labour` - the screen whose entire job is "who you employ and
   what trades exist here" - still says "nobody", "Total employed: 0".
Confidence: HIGH on all three. Also there is no `quote` for a person, though the game
elsewhere insists "ASK THE PRICE FIRST".

### Small things
- `commission smith 400` -> "400 hours of a smith bought for 115 denarii" = 0.2875 den/hr
  against a stated smith wage of 0.18 den/hr. A 60% premium for buying a job, undisclosed
  but reasonable.
- `train machinist 2` cost 675 den and 900 founder hours, "ready in 2 years". Worked.
- `bribe 100` at -470 den -> "REFUSED: you have -470 denarii", even though `help money`
  says "You may spend past what you have, as far as somebody will lend you" and the credit
  limit was 2,519. Projects may use credit; bribes may not. Nothing says so.
- People are fractional: "EVENT 110: 170.5 of the people you bought finish learning the
  work", "IN TRAINING: None x27.5", "free to put behind something new: 0.03 craftsmen".

### FINDING 19 (confirmed, single screen) — the prompt and the EMPLOY block disagree
Scratch at 115 AD after buying 20 slaves and waiting three years:
```
> state full:true
EMPLOY: 0 people, 0 den/yr in wages
  nobody
...
[115 AD | 4424134 den | you:2000 hr | sch 0 art 14 | rep 6] >
```
The status prompt printed at the bottom of that same `state` output says "art 14"; the
EMPLOY block eight lines above says 0 people, nobody; `labour` says "Total employed: 0".
Confidence: HIGH.

### Eminence: works, but essentially cannot be triggered by wealth
With capital hand-set to 1,000,000,000 den (four thousand senatorial fortunes) and
reputation left alone, over 60 years eminence settles at ~8 against a danger line of 26 and
the game reports "0% chance of ruin this year" the whole way. `help eminence` says eminence
"rises with how well known you are and how visibly rich" - visible wealth moves it from
0.10 to 8 across a 2.5-million-fold increase in money, which is not enough to matter.
Reputation is doing nearly all the work.
When eminence IS forced above the line the mechanic does fire and is brutal:
"EVENT 107: PROMINENCE: property confiscated, 541750380 den lost". So the hazard is
implemented; it is just very hard to reach the way the help text says you reach it.

### Resolved, not a bug — the `afford` hint
Opening `available` suggests "what you can pay for: available afford 1,083" with 400 den
cash and a 1,367 credit limit; later "available afford 8,619" with 6,833 cash and 3,574
credit. Both are exactly cash + half the credit limit. Internally consistent, never
explained anywhere.

### Also checked and sound
- `mothball tex_indigo` -> revenue drops by exactly 306.7 and upkeep by 40, both reflected
  in `money` immediately; `restore tex_indigo` costs 80 den and restores both exactly.
- `stop tex_horizontal_loom` on an already-finished work -> "REFUSED: not active". Correct.
- `close iron` with no iron mine -> "REFUSED: you have no iron workings, and none being sunk".
- Debt works: overcommitting drove capital to -1,605, interest was charged (131 den at 11%)
  and the position recovered; the refusal message when overcommitting quotes cash + credit
  correctly ("between cash and credit you can raise 2,839" = 320 + 2,519).

### FINDING 20 (confirmed, two lines apart on one screen) — 0 artisans or 1.0 craftsmen?
```
> why ag2_nitrogen_cycle
STAFF NEEDED: 0 scholars, 3 artisans   (you have 1, 0)
...
STATUS: BLOCKED
  needs 3 trained craftsmen, on your staff or under contract, and you have 1.0.
```
"(you have 1, 0)" and "you have 1.0" [craftsmen] are the same quantity, printed two lines
apart with different values, on a screen where I employ nobody at all. The same mismatch
explains FINDING 8: `why tr_hopper_wagon` printed "1 artisans (you have 1, 0)" and
"STATUS: CAN START NOW" simultaneously - the gate uses the 1.0 figure, the display uses the
employee count. Confidence: HIGH.

### FINDING 21 (confirmed) — designer's notes leak into the player-facing risk screen
```
> risk
[235-284] Third century crisis
  Rome's baseline `values` note that it is magic, not heterodoxy, that is criminal here,
  ... That is a real tightening of religious rigidity, not merely more of the old
  magic-suspicion, so it is modelled as its own small shift below rather than folded into
  w_magic_fear.
[284-305] Diocletian's reforms and the Price Edict
  ... That, and not the persecution of 303-311, is why w_commerce falls here. The state
  also gets stronger and its favour correspondingly more decisive, which is the patronage
  shift.
```
Internal variable names (`w_magic_fear`, `w_commerce`), a reference to "Rome's baseline
`values`" file, and first-person modelling justifications ("is modelled as", "is why ...
falls here") are printed to the player as in-world briefing text. Confidence: HIGH that
this is not meant to be player-visible.

### FINDING 2 (strengthened) — one generic mitigation offered for every hazard
`horse_collar` is offered as "you could begin now" under all of:
Antonine plague, Plague of Cyprian, Third century crisis (output factor) and Diocletian's
Price Edict - alongside prose remedies that are, respectively, "clean water, quarantine and
eventually inoculation" (twice) and "land and power of your own". A padded horse collar is
not a plague measure. `statistics_basic` is likewise offered under both plagues AND the
third-century crisis. The suggestion engine is clearly not reading the hazard's own
mitigator list. Confidence: HIGH.

### FINDING 22 (confirmed) — when it must close a concern, it closes the most profitable one
`scratch_fuzz.json`, staff wiped out by the Antonine plague. Two concerns each need 1
craftsman: `tr_hopper_wagon` (earns 600/yr, costs 40) and `tx2_retting` (earns 0/yr,
costs 40). The engine's choice:
```
EVENT 177: nobody left to keep an eye on 1 concern, so tr_hopper_wagon closed.
```
It kept the one that earns nothing and costs 40 a year, and closed the one earning 600.
This is the second time I have seen it pick the worst victim (the first was at 114 AD).
Confidence: HIGH that this is wrong.

### FINDING 23 (candidate) — `policy auto_shed` never fires
`auto shed: let go of WORKS that cost more than they return (this is about buildings and
practices, not people)". Switched ON, with `tx2_retting` open at 0 den/yr earned and
40 den/yr paid, and 33 years passing (168-201). It was never shed. Three more zero-revenue
concerns (identity_cover 0/200, scientific_method 0/100, units_standards 0/30) also
survived - those plausibly have non-monetary value, but `tx2_retting` does not obviously.
Confidence: MEDIUM.

### Small: a hardcoded example in a live number
`state` prints "1.32 artisans is the wage and output of one artisan plus a third of
another's" while the line above it says "artisan 0.09". The illustrative number is static
and does not match the figure it is illustrating.

### Fuzzing the parser — could NOT break it
`step 1e9`, `step 999999999` -> refused with the correct remaining-years figure (432).
`step 2.5` -> "years must be a whole number". `why` / `start` / `buy` / `quote` with no
argument -> a helpful usage line. `state; money` -> "one command per line - I will not
guess which half you meant." `help nosuchtopic` -> lists real topics.
`policy auto_nonexistent on` -> lists real policies. `policy auto_hire maybe` -> "say 'on'
or 'off'". `quote mine unobtainium 5` -> "no such material ... Mineable: coal, copper,
gold, iron, lead, silver, tin". No traceback anywhere.
Two nits: `buy forest abc` parses "abc" as 0 and reports "n must be greater than zero,
got 0" rather than "not a number"; `start hom_toys_dolls hom_safety_pin` silently ignores
the second id.

### Expectation before the long run
I am at 168 AD in the honest session with 9 technologies built, ~14,800 den and revenue
1,871/yr. I am going to switch on every automatic policy and step to the horizon.
I expect: the founder is immortal so no succession problem; money compounds slowly because
living costs are ~1.5% of capital plus a base; the binding constraint should be founder
hours (2,000/yr) and calendar floors, not money. With 432 years and roughly 142 nodes still
between me and the transistor (I know the count only because the save-editing exploit let
me run `path` once in a scratch game), a purely automatic run should get nowhere near it -
I expect fewer than 40 things built and no transistor.

### FINDING 24 (confirmed) — during a hazard the ledger keeps quoting pre-hazard numbers
Calm years: the ledger is exact. 106 AD -> 107 AD, `money` said "Net/yr: 153.4" and capital
went 206.5 -> 360.0, a change of +153.5. Perfect.
During the Third century crisis (scratch copy of the main save at 268 AD):
```
> money      Capital: 1,012   Revenue: 1,106 den/yr   Net/yr: 269.3
> step 1     EVENT 268: Third century crisis: trade and output fall to 65% of normal
> money      Capital: 1,217   Revenue: 1,106 den/yr   Net/yr: 267.8      (actual change +205)
> step 1
> money      Capital: 1,411                                             (actual change +194)
```
Revenue is still printed as 1,106 after the program has said output fell to 65% of normal,
and Net/yr overstates the real change by 24-27% two years running, with no line item for
the difference - on a screen that advertises itself as "the whole ledger: what comes in,
what goes out" and asserts "(these add up to the revenue above)". Confidence: HIGH.

### The honest run, 168 -> 268 AD with every policy switched on
Result: technologies built went DOWN, 9 -> 8 (one lost to a sacking), capital 14,809 -> 1,012,
reputation 12.8 -> 0.90, staff 4 artisans -> 0.17 full-time-equivalents.
So "Nothing happens unless you make it" is honest: the automation will not advance the tree
for you. It did teach an optician (a trade that "MUST BE TAUGHT"), which is a nice touch.

## Reproduction of the headline findings from a brand-new game
```
mkdir repro && cd repro
printf '2\ny\npoor_scholar\nn\n' | python3 /home/user/test/rome/sim/simulator.py
printf 'ventures\nmoney\nlabour\nwhy med_cataract_couching\n' \
  | python3 /home/user/test/rome/sim/simulator.py play --session rome_100ad.json
```
On the very first turn of a fresh Rome/100 AD/fog-on/poor-scholar/no-ageing game:
- `ventures`: "RUNNING: nothing" ... "Only what you are RUNNING earns anything"
              "free to put behind something new: 1 scholars, 1 craftsmen"
- `money`:    "Revenue: 233.5 den/yr  from: med_cataract_couching 166.7, med_trepanation 66.7"
- `labour`:   "ON YOUR STAFF: nobody   Total employed: 0   annual wage bill: 0 den"
- `why med_cataract_couching`: "STAFF NEEDED: 1 scholars, 0 artisans (you have 1, 0)",
              "REVENUE: 500 den/yr", "STATUS: DONE / THIS SOCIETY ALREADY HAS THIS.
              You did not build it and do not maintain it."
So on turn zero: nothing is running, but 233.5 den/yr is coming in; I employ nobody, but I
have 1 scholar and 1 craftsman; and the technology's own page quotes 500 den/yr for the
thing the ledger books at 166.7.
The 166.7 is exactly 500/3, and 66.7 is exactly 200/3, scaled by (free founder hours/2000).
Neither the /3 nor the hour-scaling appears anywhere in the game's text.

## Final tally of the honest run
Started 100 AD, 400 den, poor scholar, fog on, immortal founder. Reached the horizon at
600 AD with 8 technologies of my own built, 5,323 den, reputation 2.4, and no transistor.
`state` at the end reported "AHEAD: 0 technologies at risk if a hazard lands, hedged by
nothing yet" while also reporting "8 built by you" - the at-risk count never tracked the
built count at any point in the run (9 built / 1 at risk; 8 built / 0 at risk).
A field "protection 13%" appeared in STANDING at the end that had never been shown before
and is not explained by `help` or by any command.

## What could NOT be broken
- Argument validation (negatives, zeroes, non-numbers, out-of-range years, unknown ids,
  unknown trades, unknown materials, unknown policies, unknown help topics, two commands
  on one line). Never a traceback.
- Fog of war from inside the game: `path`, `why` and `available find` all refuse to reveal
  anything past the frontier. The only way through was editing a save file.
- Save/session persistence across invocations: exact, every time, including mid-year state
  (hours already spent, part-paid projects).
- End-of-run lockout: `step`, `start`, `work`, `buy` are all refused after 600 AD.
- The credit system: limits are quoted correctly and enforced, interest is charged.
- The eminence ruin, once actually triggered, is implemented and severe.
- Trades genuinely are not interchangeable for *hiring* (you cannot hire a chemist in Rome,
  and you cannot work as one either).
- Market saturation exists ("what the market will not absorb" appears as a negative line).
- Staff attrition (~3.5%/yr) and plague staff losses are real and compounding.
