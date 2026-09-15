# Playtest notes - naive11/c

Adversarial playtest of `python3 rome/sim/simulator.py`. Everything below was learned only
from what the program printed. Roughly 60 sessions, several of them full 500-year runs to
the 600 AD horizon, plus scripted probes.

**Caveat on the build:** the engine and data files were being edited by someone else while
I played (`rome/sim/engine/*.py`, then `rome/data/prices.json` and `tech_tree.json`, all
with mtimes inside my session). Every item below was re-run against the build present at
the very end of the session. One finding (D13, rubber) was **fixed under me** mid-session
and is marked as such; all the others still reproduce.

---

# TOP PROBLEMS

**1. (D20) The run-ending denunciation fires in the same year as its only warning, and the
last number the player was given was "0% chance".**
`repro_denounced.txt` in this directory reproduces it exactly, in five game-years, using
nothing but ordinary profitable `start`s. The final screen before the fatal step reads
`scandal 21.9` and `SCANDAL is dangerous above 25 (0% chance of being denounced this year,
which ends the run; 'bribe' buys it down...)`. One `step 1` later the log prints the first
warning (`scandal 29 against a line of 25 ... about 7% a year`) and `RUN ENDS: denounced:
as a sorcerer` in the same batch. `bribe`, the remedy the text names twice, can never be
used. Cause: `state` computes the risk from the current scandal, but scandal is recomputed
during the step from the work finished that year, so the printed probability is always a
year stale - and reads 0% in the year it kills you. This is the single most unfair thing in
the game: a run destroyed with no actionable warning, contradicting a printed figure.

**2. (D10) A project that fails costs 40% of its price again; the quote, the `why` page and
the ledger all deny it, and the capital change does not match the printed net.**
`merchant` start: 4,000 den, `Net/yr after it: -50.5`, `start fud_whaling_industry` ->
"the bill you have taken on: 2,070 ... it is now fixed for this project". After `step 1`
the ledger says `spent on projects last step: 2,070` and capital is **1,052**.
4,000 - 50.5 - 2,070 = 1,879.5. The missing 827.5 is the failure's "828 is gone", charged
but not reported anywhere in the ledger. On a project seen failing three times in a long
run that is a 2,484-denarius overrun on an 828-denarius line item.

**3. (D1) `money` and `state` mis-state next year's net by the entire wage bill in the year
you hire.** `merchant`, `hire artisan 4` (charges 1,000 up front), then `money` says
`wages 1,062 ... Net/yr after it: -1,097 (this is the figure state prints)`. `step 1` and
capital goes 3,000 -> **2,939**, a change of -61. The forecast is wrong by ~1,036, i.e. the
prepaid wages are counted twice. From year two the same figure is accurate to a few
denarii, which makes the error harder to spot, not easier.

**4. (D14) On the default start the goal is not reachable, including by the engine's own
recommended strategy.** `run --mc 6 --civ rome_100ad` -> `reached transistor: 0 (0%)`,
100% "ran out of horizon", stopped most often at `atomic_theory` (the seventh node in the
path: 1,100 den, 1,000 hours, 2 scholars). With `--kit absurd` (1,000,000 den) it is 2/3.
Meanwhile `validate` prints "OK: ... goal reachable" and every `state` prints
"Goal: point_contact_transistor". My own best hand-driven 500-year run from `absurd`
finished 698 of 2,831 nodes, ended holding 31,800,097 unspent denarii, and was still 51
nodes short.

**5. (D15) Opening concerns - "the one rule that catches everybody" in the tutorial text -
makes you strictly worse off.** Two identical 500-year runs differing only in
`policy auto_open on/off`: ON gave 580 things built, 27,112,726 in hand, 63 goal-nodes
left; OFF gave 698 built, 31,800,097 in hand, 51 left. Every open concern permanently ties
up craftsmen (`ventures`: "HELD BY ... crucible_steel 7.3 craftsmen") and craftsmen are
what gate starting anything, while the actual money comes from "what your own workshop
sells", which needs no supervision. The game's headline advice steers straight into the
worse line and nothing warns that opening costs staff.

**6. (D4 / D19) `stuck` - the command whose entire job is "why you are not getting on" -
does not name the blocker.** In one state it reports `151 things you could begin, 150 of
them you could pay for` while 39 finished concerns worth thousands a year sit shut for want
of a free craftsman, which `open` then says outright. In another, insolvent with a credit
freeze, `stuck` prints "NOTHING YOU COULD BEGIN: everything in front of you is either
built, already running, or waiting on something" - and `open ag2_botanic_garden` plus
`open ag2_coffee_voyage` immediately succeed and lift revenue from 480.8 to 823.9 a year.

**7. (D2) The credit-freeze event advertises the wrong date.** "CREDIT EXHAUSTED ... Nobody
will fund new work here until 110" - at 110, and at 111, `start` is refused with "They will
deal with you again in 117". Seven years of a player's plan, wrong.

**8. (D5) `policy auto_open` never fires and its description is not the rule.** With the
switch on and 10,820 denarii in hand, 39 concerns stayed shut, some with zero upkeep and
hundreds a year of takings. The real gate is free supervisory craftsmen, which the policy
screen never mentions.

**9. (D3) A 360-year insolvency doom loop with no exit and no verdict.** Doing nothing but
`step 1` from turn one, the run enters an exact ten-year cycle at year 240 - debt grows
-77 -> -1,227, `INSOLVENCY SETTLED` writes it back to -77, repeat - identical to the
decimal, until the horizon at 600. Reputation pinned at 0.10, credit dead, nothing
startable, and the game never says you have lost.

**10. (D18) `open`, `ventures` and the ledger give three different earnings for the same
concern.** `ventures` -> `ag2_botanic_garden 535.4`; `open ag2_botanic_garden` -> "it earns
260 a year"; the ledger then adds 178.5, which is 33% of 535.4. The message the player
reads at the moment of deciding understates the return by half.

**11. (D13, FIXED UNDER ME) Rubber was priced at 99,999 denarii per kilogram.** For most of
this session `why tx2_eraser` read `3,001,105 den total (35 labour + 2,999,970 materials +
1,100 capital, then ... x1 scarcity)` for 30 kg of rubber - against 5 denarii for the
breadcrumb eraser that does the same job - and the 22-node chain that gets you the rubber
in the first place costs 75,638 in total. `mil_gas_mask` was 1,000,001. Someone changed
`rome/data/prices.json` late in my session and it now reads 4,735; recording it because it
was live and reproducible for hours and the same sentinel-price pattern may exist for other
materials.

**12. (D6) `help commands` says `stop` loses your money; the game refunds it in full.**
"stop <id>: abandon it, losing what you have spent" vs the actual "The 1,224 denarii
already paid stands to your credit and comes off the bill if you begin again", verified by
restarting for 356.4 instead of 1,580. A player who believes the help never uses the one
lever that gets them out of a project they cannot finish.

Smaller items, with repros, are D9, D11, D12, D16, D17 and D21 below.

---

## Log (in the order I found them)

### D1. `money` / `state` net-per-year is wrong by the whole wage bill in the year you hire
The game prints a forecast and labels it "this is the figure `state` prints", but capital
moves in the opposite direction.

Repro (setup: `2` Rome, `n` fog off, `merchant`, `n` no mortality):
```
money            -> Capital 4,000  Net/yr after it: -50.5
hire artisan 4   -> annual wage bill: 1,062 ; capital: 3,000   (charged 1,000 = 250 x 4)
money            -> Capital 3,000  wages 1,062  Net/yr after it: -1,097
step 1           -> Money: 2,939 den
```
Predicted change -1,097, actual change **-61**. Off by ~1,036, i.e. the wage bill is
charged once as a hiring advance and then *also* shown as a cost for the same year,
even though it is not deducted again.

Same with one artisan from `poor_scholar`:
```
hire artisan 1  -> annual wage bill: 251.5 ; capital: 150
money           -> Net/yr after it: -244.2
step 1          -> Money: 164.6 den     (i.e. capital went UP 14.6)
```
A player budgeting from the printed number is misinformed by ~100% of the wage bill.
(From the second year onward the figure is accurate to within a few denarii.)

### D2. "Nobody will fund new work here until 110" is false - the real date is 117
Setup: `2 / n / poor_scholar / n`
```
start identity_cover
step 1  x5                      (capital runs to -1,188)
start tr_hopper_wagon
step 1
  EVENT 105: CREDIT EXHAUSTED: 2 projects stopped, unfinished ...
             Nobody will fund new work here until 110
  EVENT 105: INSOLVENCY SETTLED: ... you still owe about 423 denarii
step 1 x4          (now year 110)
start identity_cover
  REFUSED: nobody here will fund new work: ... They will deal with you again in 117 ...
```
The event promises 110, the refusal says 117. Same restriction, two different dates,
and a player who planned around the printed 110 loses seven years.

### D3. Permanent, unescapable insolvency loop - the run never ends and never resolves
Setup: `2 / n / poor_scholar / n`, then `step 1` repeatedly, doing NOTHING else.
From 240 onward the game enters an exact 10-year cycle that repeats for the remaining
360 years:
```
240  -157.4
241   -76.7   EVENT 240: INSOLVENCY SETTLED: most of the debt is written off and you
                         still owe about 77 denarii
242  -157.9
...
250 -1,227
251   -76.7   EVENT 250: INSOLVENCY SETTLED: ... you still owe about 77 denarii
...
260 -1,227
261   -76.7   EVENT 260: INSOLVENCY SETTLED ...
270 -1,227 / 271 -76.7 / 280 -1,227  (identical numbers to the decimal, forever)
```
Reputation is pinned at 0.10, credit limit 219, nothing can be started, no loss is ever
declared. This is a soft-lock: the simulation keeps running for centuries with literally
the same six numbers repeating. A player who simply pressed `step` is placed in a state
they cannot lose from, cannot win from, and is never told about.
Note also that the trigger was pure bad luck the player could not have known about
("Third century crisis: trade and output fall to 65% of normal", year 235) applied to a
player with zero assets.

### D4. `stuck` - the command whose whole job is "why you are not getting on" - misses the actual blocker
Repro: Rome / fog off / `equestrian` / no mortality, `policy auto_open on`, then 25 years of
starting the most profitable available projects (script: /tmp/play2.py style). At year 125:
```
stuck
  WHY YOU ARE NOT GETTING ON
    151 things you could begin, 150 of them you could pay for
    cheapest of them: hom_eraser_breadcrumb
    WORK IN HAND:
      fin_restaurant - waiting on your hours
```
At that same moment `ventures` lists ~39 FINISHED concerns that cannot be opened, worth
several thousand denarii a year (ag2_refrigeration_ice 331 earns / 0 costs / 42 to open,
ag2_pyrethrum 281 / 40, arithmetic_positional 497 / 100 ...), and:
```
open ag2_refrigeration_ice
  REFUSED: nobody free to keep an eye on it: it needs 0.00 scholars and 0.25 craftsmen
  to supervise, and you have 0.25 and 0.00 not already watching something else.
```
`stuck` never mentions the unopened concerns, never mentions that free craftsmen are zero,
never says "hire". The one number it does print ("150 of them you could pay for") is about
a constraint that is not binding at all.

### D5. `policy auto_open` does not do what its own description says
`policy` prints: "auto open: open concerns that plainly pay for themselves. It will NOT
open anything whose upkeep exceeds its takings". With `auto_open on` and 10,820 den in hand,
39 concerns sit shut, including ones with **zero** upkeep and hundreds a year of takings.
The real gate is free supervisory staff, which the policy text never mentions - so the
switch silently does nothing and the player has no way to learn why from the policy screen.

### D6. `help commands` says `stop` loses your money; the game refunds it
```
help commands  ->  "stop <id>: abandon it, losing what you have spent"
start identity_cover ; step 1     (1,224 den paid)
stop identity_cover
  -> "stopped. The 1,224 denarii already paid stands to your credit and comes off the
      bill if you begin again; the hours are gone"
start identity_cover
  -> "the bill you have taken on: 356.4"     (= 1,580 - 1,224)
```
The help text and the behaviour disagree. A player who believes the help will never use
`stop`, which is the one lever that gets you out of a project you cannot finish.

### D7. RETRACTED - `help protection` is correct
I first read "money is only 30 points" against an observed 32% as a contradiction. It is
not: bribing adds exactly 30 points on top of whatever base protection you have
(`bribe 100` with protection 0.07 -> 0.37 in a later test), and the 32% quoted in the help
is 2 base + 30 bought. The bribery ceiling is properly enforced - offering 1,000, 10,000,
100,000 and 500,000 all return "you are already as protected as money can make you here"
and take nothing.

### D8. RETRACTED - the `*` marker is documented
I noted that `available all` marks unaffordable rows with a trailing `*` with no legend.
It does have one; it is printed only when a starred row is actually on screen:
"A * after COST means you could not raise it today: between cash and credit you can put
1,767 into a project." Not a defect.

### D9. Minor: manumitting inflates the headcount the game reports
```
(rich_merchant) buy slaves 5 ; buy manumit 5 ; labour
  -> IN TRAINING: people you bought, learning the work x9.1, ready 103.0
```
You own five people; after freeing them the trainee line reads 9.1. (Without the manumit
it correctly reads x5.) `buy manumit` itself is free of charge and raises reputation
5 -> 6.7 instantly, so it is a strictly-dominant free action.

### D10. A project that FAILS costs 40% of its price again, but the quoted bill, the `why`
### page and the ledger all deny it - the capital change does not match the printed net
Setup: `2 / n / merchant / n`
```
money
   Capital: 4,000 den    Net/yr after it: -50.5
why fud_whaling_industry
   COST: 2,070 den total ... FAILURE RISK: 30%
start fud_whaling_industry
   the bill you have taken on: 2,070
   note: This is the price as of today, and it is now fixed for this project.
money
   Still owed on work in hand: 2,070      Net/yr after it: -50.5
step 1
   EVENT 100: FAILED at Organized whaling industry ... 40% of the hours are to do again
              (120 of your own) and 828 is gone. Attempt 2.
money
   Capital: 1,052 den    spent on projects last step: 2,070
```
Check by hand: 4,000 - 50.5 (net) - 2,070 (the whole bill) = **1,879.5**.
The game says **1,052**. The missing **827.5** is the "828 is gone" from the failure -
40% of the 2,070 bill charged a second time.
So three printed numbers are wrong at once:
  * "it is now fixed for this project" - it is not; you paid 2,898 for a 2,070 quote;
  * `why`'s "COST: 2,070 den total" - the expected cost at 30% risk is higher;
  * the ledger's "spent on projects last step: 2,070" - it actually spent 2,898.
This scales: a project seen failing three times in a long run
("Customs house ... 828 is gone. Attempt 2 / 3 / 4") overran its quote by 2,484 denarii.

### D11. Minor: the game's own worked example for `available find` returns nothing
`available` footer suggests `by name: available find furnace`.
```
available find furnace
  AVAILABLE: 0 startable now
  nothing matching 'furnace'
```
(Retracted an earlier note about the `*` marker: the legend IS printed whenever a starred
row is on screen.)

### D12. Minor: the founder's "lifespan lottery" is not a lottery
With mortality on, `2 / n / <any wealth> / y / step 200` prints
`EVENT 138: the founder dies, aged about 73` for destitute, poor_scholar, artisan,
merchant, rich_merchant, equestrian and absurd alike - the same year and age every time.
The setup screen sells this as "one human life and everything you have not made permanent
dies with you", i.e. a risk; in fact it is a fixed 38-year clock the player can plan around
exactly (once they have played once).

### D13. Rubber is priced at 99,999 denarii per kilogram, and securing a rubber supply
### does not change it - a whole branch of the tree is priced into absurdity
```
python3 rome/sim/simulator.py costs        (top of the list)
  tl_tractor        448 labour  5,000,776 materials    10,000 capital  5,011,224 TOTAL
  tx2_rubber_soles   52          3,999,960              1,100          4,001,112
  tx2_eraser         35          2,999,970              1,100          3,001,105
  tx2_elastic        32          2,999,970              1,100          3,001,102
```
In game: `why tx2_eraser`
```
  COST: 3,001,105 den total  (35 labour + 2,999,970 materials + 1,100 capital,
        then x1 your civ, x1 distance, x1 scarcity, x1 opposition, x1 prices)
  MATERIALS: rubber_kg 30
```
2,999,970 / 30 = **99,999 den per kg of rubber**, and every rubber node prices it the
same (mil_gas_mask 10 kg = 1,000,001; tx2_ballpoint_pen 8 kg = 799,992;
tl_pneumatic_tyre 5 kg = 500,003). An artisan costs 250 den a YEAR in this game, so one
kilo of rubber is four hundred artisan-years.
The tree has a node whose entire job is to get you rubber:
```
why mat_natural_rubber
  "NOT UNOBTAINABLE. Hevea is Amazonian, but Landolphia and Funtumia vines ..."
  COST: 0 den total   YOUR HOURS: 60   FAILURE RISK: 95%
  DIRECTLY UNLOCKS: ch2_rxn_vulcanisation, tl_pneumatic_tyre, tl_solid_rubber_tyre,
                    tl_vulcanized_rubber, tx2_elastic, tx2_eraser, tx2_rubber_soles
```
and the CLI's own summary of the eraser proves the price is not reduced by it:
```
python3 rome/sim/simulator.py why tx2_eraser
  FULL CHAIN BEHIND IT: 22 nodes, 5,940.0 of your hours, 75,638 denarii, 16-year serial floor
  Cost : 35 den labour + 2,999,970 materials + 1,100.0 capital = 3,001,105 TOTAL
```
Getting rubber costs 75,638 for the whole 22-node chain; the eraser you then make with it
costs 3,001,105. Note also the printed multiplier line says **x1 scarcity** - the engine
insists rubber is not scarce while charging a sentinel price for it.
Compare `hom_eraser_breadcrumb`, cost **5 den**, which does the same job.

### D14. The game's own recommended strategy reaches the goal 0% of the time
```
python3 rome/sim/simulator.py run --mc 1 --civ rome_100ad
  === RECOMMENDED: revenue and institutions first, knowledge dispersed before the collapse ===
  runs                : 1
  reached transistor  : 0  (0%)
  final reputation    : median 1/100
  failure modes       : ran out of horizon   1 (100%)
  first blocked node  : atomic_theory        1
```
`python3 rome/sim/simulator.py validate` asserts "OK: tree is a valid DAG, fully priced,
goal reachable", and every `state` screen prints "Goal: point_contact_transistor".
`atomic_theory` costs 1,100 den, 1,000 founder-hours and 2 scholars, and it sits seventh
in the path - so the recommended line is not falling over on something exotic.
My own best hand-driven runs agree: from `absurd` (1,000,000 den), 500 years, all
automation on, I finished 698 of the tree's 2,831 nodes and ended with 31,800,097 denarii
unspent and 51 of the goal's 146 nodes still to build.

### D15. Opening concerns - the thing the game tells you is "the one rule that catches
### everybody" - makes you strictly worse off
Two identical 500-year runs from `absurd`, same script, differing only in whether
concerns were opened (`policy auto_open on` vs `off`):
```
auto_open ON : built 580 things, 27,112,726 in hand, 304 concerns running,
               63 of the goal's nodes still to build
auto_open OFF: built 698 things, 31,800,097 in hand, 0 concerns running,
               51 of the goal's nodes still to build
```
Opening concerns is worse on both axes. The reason is visible in `ventures`: every open
concern permanently ties up craftsmen ("HELD BY ... crucible_steel 7.3 craftsmen"), and
craftsmen are what gate starting anything. Meanwhile the ledger shows the money comes from
"what your own workshop sells" (473,043/yr at year 260 in one run) which costs no
supervision at all. The tutorial text - "the one rule that catches everybody: Finishing
something earns you nothing. A concern earns when you 'open' it" - steers a new player
straight into the worse line, and nothing anywhere warns that opening costs you staff.

### D16. Minor: `civs` and the game disagree about how much the society already knows
`python3 rome/sim/simulator.py civs` -> "rome_100ad ... starts with 14 technologies"
In game, turn one: "technologies: 0 built by you, 137 granted for free (137 total)".
Likewise England: `civs` says 11, the game says 130.

### D17. Minor: `close <material>` on a mine that is still being sunk reports the wrong figure
```
(absurd) quote mine coal 500    -> to sink it: 4,500   every year it stands: 750
         buy mine coal 500      -> capital: 995,500 ; ready year 103
         close coal             -> "the coal workings are closed. You stop paying 0 a year."
```
You have just thrown away 4,500 denarii and the message says you were paying nothing.
(Once the mine is producing the same command correctly says "You stop paying 750 a year".)

### D18. `ventures`, `open` and the ledger give three different earnings for the same concern
Mid-game (Rome / absurd / 45 years of building, reputation 44), year 145:
```
ventures
  YOU KNOW HOW, AND HAVE NOT OPENED
    ID                      EARNS/YR   COSTS/YR   TO OPEN
    ag2_botanic_garden         535.4        0        75.6
    ag2_coffee_voyage          494.2        0        48.0

open ag2_botanic_garden
  opened: ag2_botanic_garden open: it earns 260 a year and costs 0 a year to run
  revenue: 659.3                      <- ledger revenue rose by 178.5 = 33% of 535.4
open ag2_coffee_voyage
  opened: ag2_coffee_voyage open: it earns 240 a year and costs 0 a year to run
  revenue: 823.9                      <- rose by 164.6 = 33% of 494.2
```
`open` prints the raw tree quote (260 / 240); `ventures` and the ledger use the scaled
figure (535.4 / 494.2). The confirmation message a player reads at the moment of deciding
understates the earnings by half. (Early in a run, before the scaling kicks in, the two
agree - `open tr_hopper_wagon` -> "earns 600 a year", `ventures` -> 600 - which makes the
later disagreement harder to spot.)

### D19. `stuck` says "NOTHING YOU COULD BEGIN" while two concerns can be opened right now
Same state as D18, insolvent at -1,565 den with a credit freeze:
```
stuck
  WHY YOU ARE NOT GETTING ON
    0 things you could begin, 0 of them you could pay for
    ...
    NOTHING YOU COULD BEGIN:
      everything in front of you is either built, already running, or waiting on
      something. 'available' says which.
```
Immediately afterwards, `open ag2_botanic_garden` and `open ag2_coffee_voyage` both
succeed and raise revenue from 480.8 to 823.9 a year - a 71% increase - which is exactly
what an insolvent player needs. `state` in the same breath prints "you know how to run 178
more and have not opened them ... those shut concerns would clear 44,163 den/yr between
them". `stuck` never mentions opening anything.

### D20. The run-ending denunciation fires in the same year as its only warning, and the
### last figure the player was given was "0% chance"
Deterministic repro, saved as `repro_denounced.txt` in this directory:
```
cd /home/user/test && python3 rome/sim/simulator.py < rome/playtest/naive11/c/repro_denounced.txt
```
(It is `2 / n / equestrian / n`, then four batches of eight ordinary profitable `start`s -
hopper wagon, looms, dyes, waggonway, horse collar, guano, fish curing, guild, insurance,
cheques ... - one batch per year, `step 1` between them. Nothing exotic, nothing warned
against.)

What the player sees, year 104, the last screen before acting:
```
STANDING: reputation 62.6   protection 24%   scandal 21.9   eminence 1.6
  SCANDAL is dangerous above 25 (0% chance of being denounced this year, which ends
  the run; 'bribe' buys it down and it falls a tenth a year on its own)
```
Scandal 21.9, under the stated line of 25, and an explicit **0% chance**. They `step 1`:
```
  EVENT 104: YOU ARE BEING TALKED ABOUT: scandal 29 against a line of 25. Past it you may
             be denounced ... about 7% a year at this level. 'bribe' buys advocacy and piety
  EVENT 104: RUN ENDS: denounced: as a sorcerer
*** THE RUN HAS ENDED: denounced: as a sorcerer ***
```
The warning and the death are printed in the same batch, so `bribe` - the remedy the text
names twice - can never be used. The whole run is over in five years, at 105 AD, with
70,178 denarii in hand and 39 things built.

Root cause is visible from the numbers: `state` computes the denunciation chance from the
CURRENT scandal, but scandal is recomputed during the step from the work finished that
year. Scandal moves 0 -> 24 in a single step in this run, so the printed probability is
always a year stale and reads 0% in the year it kills you.

Two smaller things in the same message:
 * "scandal 24 against a line of 25. **Past it** you may be denounced" - 24 is not past 25,
   and the same sentence then quotes "about 0% a year at this level".
 * `state` never shows scandal rising while you are choosing; you only learn after the step.

### D3 (correction)
The insolvency loop does not hang - the run does terminate at the 600 AD horizon with a
proper summary. What is wrong is that from 240 to 600 the identical ten-year cycle repeats
with no way out offered and no loss declared: 360 years in which nothing the player can do
changes anything.

### D14 (extra data)
`python3 rome/sim/simulator.py run --mc 6 --civ rome_100ad`  (default kit)
```
  runs : 6      reached transistor : 0  (0%)
  failure modes : ran out of horizon 6 (100%)
  first blocked node : atomic_theory 3, case_hardening 1, calculus 1, charcoal_industrial 1
```
`... run --mc 3 --civ rome_100ad --kit absurd`
```
  runs : 3      reached transistor : 2  (67%)   year reached: best 372, median 442
  years spent short of a raw material (median run): coal 113 run-years
  coppice woodland owned: median 0 hectares
```
So the goal is reachable, but only from the joke starting fortune. On the default kit the
engine's own recommended line loses every time, and the thing that stops it is the seventh
node in the path (atomic_theory: 1,100 den, 1,000 hours, 2 scholars). Note also the median
winning run spends 113 years short of coal while `buy mine coal` and `policy auto_mine on`
both exist, and ends owning 0 hectares of coppice while charcoal_industrial is one of the
recorded blockers.

### Note on the build under test
The engine files under `rome/sim/engine/` were being edited by another process while I was
playing (`economy.py` and `projects.py` both had mtimes inside my session). Every finding
above was re-checked against the build present at the end of the session unless marked
otherwise; D1, D2, D10 and D13 were explicitly re-run and still reproduce.

### D21. Minor: "to make room" advice that cannot make room
Mid-game, `labour` with a full household:
```
HOUSEHOLD PLACES: 137.9 of 137.9 used, room for 0 more
  to make room: To get more artisans: hire smith 3 or any trade in labour; or
  commission smith 400 to buy one job instead of employing anybody; buy slaves
  N then manumit, though they are untrained for three years.
```
None of hiring, buying slaves or manumitting makes room - they all consume it, and `hire`
is refused at that moment for exactly that reason. Early in a run the same field correctly
suggests `workshop_first` / `freedman_staff` / `school_founded`; once those are built it
falls through to advice that cannot work.

### D22. Minor: `bribe` refusal message is unhelpfully terse
```
(95,584 den in hand)  bribe 100000
  REFUSED: you have 95584 denarii
```
No thousands separators, no statement of what was wanted, and unlike every other refusal
in the game it does not end with "Nothing was changed."

### D23. Minor: `&&` slips past the one-command-per-line guard
```
why tr_hopper_wagon; step 1   -> "one command per line - I will not guess which half you meant."
step 1 && step 1              -> silently advances one year and ignores the rest
```

### D13 status
Confirmed fixed late in the session: `why tx2_eraser` now reads
`35 den labour + 3,600 materials + 1,100.0 capital = 4,735 TOTAL` (120 den/kg of rubber).
It read 99,999 den/kg for the whole of the rest of the session.
