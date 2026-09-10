# Playtest notes - rome/sim/simulator.py (naive9/c)

Adversarial playtest. All observations from program output only.

Setup prefix used in most repros (Rome, fog off, poor_scholar, no mortality):
```
2
n
poor_scholar
n
```
Run as: `cd /home/user/test && printf '<lines>' | python3 rome/sim/simulator.py`

## Findings log (in discovery order)

### F1. `--seed` does not make a run reproducible (hash-order nondeterminism)
Identical command sequence, identical `--seed 7`, three separate runs:

```
(year, capital, techs_done, reputation, eminence)
(160, 587300.2, 751, 97.4, 14.22)
(160, 6664218.2, 848, 97.6, 16.87)
(160, 6652459.6, 848, 97.6, 16.87)
```
Capital differs by more than 10x between run 1 and runs 2/3, and runs 2 and 3
still differ from each other (6,664,218 vs 6,652,459).

With `PYTHONHASHSEED=0` exported, the same script gives the same answer every
time:
```
(160, 6648743.2, 848, 97.6, 16.87)
(160, 6648743.2, 848, 97.6, 16.87)
(160, 6648743.2, 848, 97.6, 16.87)
```
So the engine iterates string-keyed sets/dicts somewhere that changes outcomes.
Consequence: `--seed`, `run --mc`, `compare`, and any "same save = same game"
expectation are all unreliable. Repro script:
`/tmp/.../scratchpad/naive9c/det2.py` (drives `simulator.py agent --civ rome_100ad
--kit absurd --seed 7`, starts the 25 cheapest startable things each year, steps
1 year, 60 times).

### F2. `logarithms` can be started but can NEVER be finished by hired labour
`why logarithms` reports `hired_labour: {"scribe": 40000.0}` and
`calendar_floor_years: 4.0`, i.e. 10,000 scribe-hours a year.
`labour scribe` reports `hours_available_to_you_in_all: 8750.0`, and
`hire scribe 20` is refused: "this society's literacy will not supply more than
5.9 scribes in total, ever, at any price".

Nothing in `why logarithms` warns about this. `start logarithms` succeeds and
commits you to 12,255 den. The project then sits for ever:

```
ACTIVE logarithms yrs=20.0 hrs_offered=100.0
  waiting_on: "nobody to do the work: scribe (wants 10000 hours a year;
               this society can field 8750 at most)"
```
Repro (agent protocol, rome_100ad, kit absurd, --no-events):
```
{"cmd":"hire","trade":"scholar","n":2}
{"cmd":"start","id":"arithmetic_positional"} {"cmd":"start","id":"units_standards"}
{"cmd":"step","years":4}
{"cmd":"start","id":"algebra_symbolic"} {"cmd":"step","years":5}
{"cmd":"start","id":"logarithms"}          -> ok:true, bill 12,255
{"cmd":"step","years":20}                  -> still active, 0 progress, forever
```
The only escape is `commission scribe <hours>` to top the pool above 10,000 -
which no message anywhere suggests.

### F3. One unsatisfiable project starves every other project in the same trade
In a 200-year run the eight active projects were ALL blocked on scribes:
```
YEAR 300 cap 4,166,180
  logarithms             "wants 10000 hours a year; this society can field 8750 at most"
  scientific_method      "wants 250 hours a year; the scribes here can supply 8750
                          but your other work has them booked"
  calculus               "wants 600 ... your other work has them booked"
  hom_printed_books      "wants 120 ..."
  fin_newspaper_business "wants 100 ..."
  fin_bond               "wants 50 ..."
  fin_commodity_exchange "wants 75 ..."
  fin_customs_house      "wants 100 ..."
```
The satisfiable demand sums to 1,295 hours out of a pool of 8,750, yet none of
it is served: the impossible 10,000-hour job takes the whole pool and produces
nothing. All eight had been stuck for 34 years and stayed stuck for the rest of
the 500-year run (`scientific_method` - a 230-denarius, year-100-startable node
- was still unbuilt in 600 AD with 10.6 million denarii in the chest).
One `{"cmd":"commission","trade":"scribe","hours":5000}` cleared all eight at
once, proving the pool was never really exhausted.

### F4. "A concern you open starts small ... full figure over about three years" is false
`help money` says: "a concern you open starts small: It reaches its full figure
over about three years."
Measured (rome_100ad, merchant, --no-events), `tex_horizontal_loom` opened at
several different delays; the number is the loom's own line in `money`:
```
wait=0 y102:399.8 y103:399.8 y104:399.8 y105:399.8 y106:399.8
wait=1 y103:399.8 y104:399.8 y105:399.8 y106:399.8 y107:399.8
wait=3 y105:399.8 y106:399.8 y107:399.8 y108:399.8 y109:399.8
```
Full 400/yr from the first year, every time. There is no ramp.

### F5. `bribe 1` is refused with a false explanation
Fresh game, protection 0.000:
```
{"cmd":"bribe","amount":1}
 -> "you have no scandal to answer and you are already as protected as money can
     make you here, so this would buy nothing."
{"cmd":"bribe","amount":2}
 -> ok, "protection 0.00 -> 0.03"
```
Protection was 0%, and 76 denarii buys 32%. The stated reason is simply untrue.

### F6. Doing nothing at all bankrupts you, then loops bankruptcy for ever
Rome / poor_scholar / no mortality / `step 500` with no commands at all:
opening ledger is revenue 233.5, living 230, "net +3.5/yr" - so the game
presents idling as (just) solvent. Random fires and the debasement erode the
float, and from ~238 AD the run enters a permanent cycle:
```
EVENT 238: interest on 76 denarii of arrears at 11.0% a year
EVENT 240: INSOLVENCY SETTLED: most of the debt is written off and you still owe
           about 77 denarii. Your name is worth less for it (reputation -12)
EVENT 250: INSOLVENCY SETTLED: ... (again)
EVENT 260: INSOLVENCY SETTLED: ... (again)   [repeats every 10 years to 600 AD]
```
Reputation floors at 0.10, the credit limit collapses from 1,367 to 219, and
nothing the player can do escapes. Final: -1,227 den, interest "paid so far:
18,081" on a starting capital of 400.

### F7. The "CLOSE TO THE LIMIT" warning fires when you are already past it, and its threat never happens
```
EVENT 292: CLOSE TO THE LIMIT: you owe 228 of the 220 anyone here will advance
           you (103%). Past it every project in hand is halted unfinished and
           nobody funds new work for some years.
```
103% is not "close to" the limit, it is over it, and nothing was halted.

### F8. A dead state the player cannot leave, past the end of the game
After an insolvency the credit ban can be quoted with an end date beyond the
horizon:
```
workshop_first ... "nobody here will fund new work: your creditors were left
unpaid and the word is out. They will deal with you again in 609"
```
The horizon is 600. Capital was -1,304, so the offered alternative ("pay for
something out of money you actually hold") is impossible too. Every one of the
130 remaining goal nodes was unstartable, and stayed that way to the end.

### F9. `FULL CHAIN BEHIND IT: ... N den` ignores every price multiplier the game itself applies
`why <id>` prints the node's own COST with its multipliers spelled out, and then a
"FULL CHAIN BEHIND IT" total for the prerequisites. That total is the sum of the
prerequisites' *base* prices - the civilisation factor, distance, scarcity,
opposition and the price index are all dropped.

The same 8 prerequisites of `telescope` are quoted as 24,175 in EVERY
civilisation, while the actual sum of the same 8 nodes' own `why` COST lines is:
```
civ               "FULL CHAIN BEHIND IT"   real sum of those nodes   error
norse_900ad             24,175                   35,108             -31.1%
mexica_1500             24,175                   20,665             +17.0%
han_china_100ad         24,175                   18,970             +27.4%
england_1300            24,175                   25,184              -4.0%
rome_100ad              24,175                   23,848              +1.4%
```
Text-UI repro (Norse, fog off, absurd, `why telescope`):
```
COST: 2,756 hacksilver total  (321 labour + 72.5 materials + 700 capital,
      then x1.8 your civ, x1 distance, x1 scarcity, x1 opposition, x1.4 prices)
...
FULL CHAIN BEHIND IT: 8 nodes, 2,810 of your hours, 24,175 hacksilver, 6.5-year serial floor
```
The chain really costs 35,108 hacksilver there. The number is worst in the
poorest civilisation, which is where a budget matters most.
(`chain_size` and `chain_founder_hours` are both exactly right - it is only the
money that is wrong.)

### F10. The concern ramp is described as 3 years, is really 1 year, and is skipped entirely if you delay opening
The ledger itself states the rule and then breaks it. Repro (Rome, fog off,
merchant, no mortality):
```
start tex_horizontal_loom / step 1 / open tex_horizontal_loom / money
  ...  tex_horizontal_loom  266.6
       STILL BUILDING UP: tex_horizontal_loom at 66% of full takings. A concern you
       open reaches its full figure over 3 years, so what the ledger shows is not
       what it will be.
step 1 / money
  ...  tex_horizontal_loom  399.8        <- 100% one year later, not three
```
And the ramp is keyed to the year the tech was BUILT, not the year it was OPENED:
```
start tex_horizontal_loom / step 3 / open tex_horizontal_loom / money
  ...  tex_horizontal_loom  399.8        <- full takings immediately, no ramp at all
```
So sitting on a finished concern for a year and opening it later is strictly
better than opening it at once, which is the opposite of what the text implies.

### F11. The run can end with no warning and no visible number: "denounced: as a sorcerer"
Rome / absurd / seed 11, starting the 20 cheapest startable things each year with
`auto_bribe` at its default of False:
```
y101 scandal=21.92 ... y109 scandal=32.50  y110 scandal=33.55  y111 scandal=33.16
     RUN ENDS: denounced: as a sorcerer
```
Eleven years of warning-free drift, then the run is over. Nothing tells the
player that scandal has a danger line:
* `state` prints `scandal 33.55` with no threshold, no per-year chance, and no
  note - while printing, for EMINENCE, "dangerous above 26 ... 0% chance
  something lands this year, of which 0% would end the run".
* `state full:true` has exactly one scandal field: `{'scandal': 33.55}`.
* `risk` never mentions denunciation at all.
* No event fires beforehand.
Turning on `policy auto_bribe on` in the same seed keeps scandal under 11.5 and
the run survives - so the mechanic is survivable, it is just invisible. The
default is off.

### F12. The price index advertised on the selection screen does not touch your income or your living costs
The menu advertises "prices 0.75x Rome / 1.00x / 1.40x / 1.10x / 0.80x", and
`why` applies an explicit "x1.4 prices" to everything you build. But at 100/900/
1300/1500 the opening figures are:
```
civ                revenue   living   labourer/yr
rome_100ad          233.5     230.0      125
han_china_100ad     233.5     230.0       66
norse_900ad         232.7     230.0      105
england_1300        232.8     230.0      110
mexica_1500         232.6     230.0       50
```
Living and appearances is 230.0 to the decimal in all five, and the subsistence
floor is 224.0 in all five (kit `destitute`). Your practice earns the same
everywhere. So in the "prices 1.40x" civilisation, food and rent cost exactly
what they cost in Rome while every project costs 40% more; and the hired-wage
rates do not follow the advertised index either (Norse is 1.40x but its labourer
is 0.84x Rome's).

### F13. Your starting money makes literally no difference if you do not spend it
Idling `step 500` (or to the horizon), `destitute` (0 den) vs `poor_scholar`
(400 den), seed 4:
```
rome_100ad       destitute -> -1226.7 ;  poor_scholar -> -1226.7
han_china_100ad  destitute ->  -172.3 ;  poor_scholar ->  -172.3
england_1300     destitute ->  1010.5 ;  poor_scholar ->  1010.5
mexica_1500      destitute ->     0.0 ;  poor_scholar ->     0.0
```
Identical to the last decimal. The repeated-insolvency writedown (see F6) resets
everyone to the same attractor.

### F14. `labour <trade>` quotes a wage the recurring bill does not match
```
{"cmd":"labour","trade":"scholar"} -> a_year_of_one: 625.0
{"cmd":"hire","trade":"scholar","n":3} -> charged up front 1,875.0 (= 3 x 625, correct)
                                          annual_wage_bill: 2,154.2 (= 3 x 718, +14.9%)
```
Same shape for every trade tested (smith +4%, scribe +15%, labourer +4%). The
number `labour` advertises is the one you pay on day one and not the one you pay
every year after.

### F15. Mine `ready_year` is a year early
```
{"cmd":"quote","what":"mine","material":"coal","n":500}
  -> to_sink_it 4500, every_year_it_stands 750, years_before_it_produces 3
{"cmd":"buy","what":"mine","material":"coal","n":500}   (in year 100)
  -> ready_year: 103, years_until_producing: 3
```
`state` in 103: `mine_capacity {}`, mines standing 0.
`state` in 104: `mine_capacity {'coal': 500.0}`, mines standing 750.
It is ready in 104, not the promised 103.

### F16. Small display disagreements between the status bar and the panel it sits under
On one screen, same instant:
```
[136 AD | 20103 den | you:2000 hr | sch 0 art 0 | rep 5] >
   Money: 20,104 den   ...  EMPLOY: 0.32 people ... artisan 0.32
   STANDING: reputation 4.7 ...
```
The bar truncates money (20,103 vs 20,104), floors staff (0 vs 0.32) and rounds
reputation up (5 vs 4.7). At the end of a broken run the bar reads `rep 0` while
`state` reads `reputation 0.10`.
Also on that screen: "1.32 artisans is the wage and output of one artisan plus a
third of another's" - the player has 0.32 artisans, not 1.32.

### F17. `open` does not check the staff a concern needs
`ventures` lists `needs: {craftsmen: 1.0}` for each of five textile concerns.
With exactly 1 artisan employed, all five `open` calls succeed:
```
open tx2_bleaching_sun -> ok, upkeep 40
open tx2_retting       -> ok, upkeep 80
open tx2_shed          -> ok, upkeep 120
open tx2_count_standard-> ok, upkeep 160
open tx2_selvedge      -> ok, upkeep 200
```
The requirement is only enforced later, by an event that closes them again.

### F18. Every run drops a save file in the working directory and never cleans up
Each bare `python3 rome/sim/simulator.py` invocation writes a new
`rome_100ad_<n>.json` into the CWD - even a two-command probe. 70 of them
accumulated during this session; 66 identical ones are already tracked in git at
the repository root, and `git status` shows one of them dirty.

### F19. Commissioned hours are bought a second time out of a pool the game calls a hard ceiling
`labour scribe` says the whole supply is 8,750 hours a year:
```
{"trade":"scribe", "hours_the_market_can_supply":8750.0, "hours_available_to_you_in_all":8750.0}
{"cmd":"commission","trade":"scribe","hours":9000}
  -> "the scribes here can spare 8750 more hours this year, not 9000"
```
and `logarithms` is refused progress because it "wants 10000 hours a year; this
society can field 8750 at most". Yet commissioning the full 8,750 each year on
top of the standing pool lets the 10,000-hour project run and finish:
```
start logarithms; then each year: {"cmd":"commission","trade":"scribe","hours":8750} + step 1
 y110 commission_ok=True  logarithms 400.0 effective hours
 y111 commission_ok=True
 y112 commission_ok=True
 y113 logarithms COMPLETED
```
So the real ceiling is 17,500 (8,750 standing + 8,750 commissioned), not the
8,750 the game states in three separate places. This is also the only escape
from the deadlock in F2/F3, and nothing points the player at it.

### F20. `start` warns that an impossible project "will crawl"; it does not crawl, it stops dead
```
{"cmd":"start","id":"logarithms"}
 -> ok:true, bill 12,255, but: "started, but this society cannot supply the labour
    it wants and it will crawl until you can: scribe (wants 10000 hours a year;
    this society can field 8750 at most)"
```
20 years later: `hours_effective_this_year: 0.0`, `founder_hours_left: 5.0`,
`spent: 12255.0`, `still_to_pay: 0.0`. Zero progress, full price paid.
"until you can" is also not reachable through `hire` (capped at 5.9 scribes
"ever, at any price") or `train` (the trade already exists). Only `commission`
works, and it is not mentioned.
Note also that `why logarithms` gives no hint at all: `can_start_now: true`,
`start_blocked_reason: null`.

### F21. Credit is capped at your annual living bill, which is never explained
```
kit            capital     living_and_appearances   credit_limit
destitute            0            224.0               1,366.8
poor_scholar       400            230.0               1,366.8
rich_merchant   20,000            524.0               1,366.8
equestrian     100,000          1,724.0               1,724.0
absurd       1,000,000         15,224.0              15,224.0
```
The limit is exactly `max(reputation floor, living cost)`. A founder with 20,000
den in hand and 1,531 den/yr of income could borrow 1,935 - i.e. the size of his
grocery bill, not of his business. `help money` only says "as far as somebody
will lend you and no further".

### F22. Eminence, billed as the one hazard nothing protects you from, is unreachable at the scale the economy actually reaches
`state` says "EMINENCE is dangerous above 26". Measured settling points:
```
capital 1,000,000  -> settles at 8.1
capital 1.37e9 (end of a won run, reputation 98) -> 17.15, ruin chance 0.0
```
A brute-force run reached 1,369,921,440 denarii, 2,826 of the tree's 2,831
nodes, and the goal in 522 AD, with prominence never crossing 18 and
`chance_the_run_ENDS_this_year` at 0.0 throughout.

### F23. The economy has no ceiling
Same run: revenue 31,134,176 den/yr against a `validate` figure of 52,527,995 den
to build the ENTIRE 2,831-node tree. By 400 AD the founder holds ~1 billion
denarii in an empire the game itself describes as having an equestrian census of
100,000 - about ten thousand equestrian fortunes - while the annual wage bill for
906 employees is 318,235, i.e. 1.4% of the "living and appearances" line.
A single 225.8-denarius node (`tex_horizontal_loom`, no staff needed, startable
in year 100) returns 400 den/yr gross, 370 net: a 164% annual return, for ever.

### F24. `run` - the documented batch command - produces no output for as long as you leave it
```
run --mc 1 --horizon 150 --civ rome_100ad --seed 2   ->  3.6 s, prints a summary
run --mc 1 --horizon 300                             -> 52.5 s
run --mc 1 --horizon 400                             -> 70.9 s
run       --horizon 150   (default --mc)             -> killed at 110 s, no output
run --strategy rush --civ rome_100ad --seed 5        -> killed at 600 s, ZERO bytes of output
```
The last one is the form the CLI help advertises (`The command line: validate,
costs, path, run, compare, play, agent`). At the default horizon of 600 and the
default `--mc`, it runs for tens of minutes and prints nothing at all until it is
done - no progress line, no partial result. `step 500` in the interactive game
covers the same 500 years in a few seconds.

### F25. `risk` prints two numbers that do not agree with each other or with the outcome
`risk` shows "chance lost if a site is sacked: 80%", "fraction lost when it
happens: 40%", and an "expected_technologies_lost_per_sacking". Measured:
```
at_risk=132  expected_per_sacking=42.2   actual loss when it landed: 52
at_risk=100  expected_per_sacking=32.0   actual loss when it landed: 40
at_risk= 61  expected_per_sacking=19.5   actual loss when it landed: 24
at_risk= 37  expected_per_sacking=11.8   actual loss when it landed: 14
```
The "expected" figure folds the 80% in a second time; the player who multiplies
the two published rates (132 x 0.4 = 52.8) gets the number that actually happens,
and the game's own headline number is 20% low. `state` reports the same figure as
"N lost per sacking on average".
(The loss itself is honestly reported - a separate "KNOWLEDGE LOST: 52
technologies forgotten - ... and 44 more" event names them.)

### F26. `train` accepts trades that already exist and then claims you invented them
`help labour` says "train: teaches a trade that does not exist here", and
`labour` splits trades into "YOU COULD HIRE: ... smith ..." and "MUST BE TAUGHT:
chemist, electrician, engineer, machinist, optician". But:
```
{"cmd":"train","trade":"smith","n":2}
 -> ok, "2 smiths will be ready in 2 years", 675 den and 900 founder hours
{"cmd":"state","full":true} -> "trades_you_created": ["chemist", "smith"]
```
The game now says you created the smith trade in Trajan's Rome. (It is not an
exploit - 2 smiths cost 562 den and 0 hours to hire - just a false statement.)

### F27. "ready in N years" / "ready_year N" is consistently a year early
Two separate systems, same off-by-one:
```
{"cmd":"train","trade":"chemist","n":2}  -> "ready in 2 years", ready_year 102
   state in 102: still in_training, ready_year 102
   state in 103: employees 4.0        <- actually ready in 103
{"cmd":"buy","what":"mine","material":"coal","n":500} in year 100
   -> ready_year 103, years_until_producing 3
   state in 103: mine_capacity {}     <- nothing
   state in 104: mine_capacity {'coal': 500.0}
```

### F28. Eminence never fires because the stated per-year chance is 0 everywhere below the line
Over 25 runs x up to 120 years (~3,000 run-years) with prominence sitting between
11 and 17 against a danger line of 26, the sum of every `chance_of_ruin_this_year`
the game reported was exactly 0.00. It is a step function at 26, not a rising
risk, and (F22) 1.37 billion denarii only gets you to 17.

### Things that checked out clean (tested, no defect found)
* Ledger arithmetic: the income rows always sum exactly to revenue, and
  revenue - upkeep - living - wages - mines - interest equals the printed net,
  at 400 den and at 21 million den.
* Year-to-year capital transition matches the ledger to rounding.
* Stated FAILURE RISK is honest: 60 trials each gave 6/60 at 10%, 3/60 at 5%,
  0/60 at 0%.
* Calendar floors are honoured (a 2-year floor never finishes in 1).
* `why` and `available` never disagree: all 7 fields cross-checked on all 207
  startable nodes, 0 mismatches.
* `chain_size` and `chain_founder_hours` are exactly right (only `chain_cost` is
  wrong - F9).
* Input validation is solid: negative/zero/huge/garbage arguments to step, hire,
  fire, buy, manumit, commission, train, start, stop, open, why, bounty, close
  and bribe are all refused cleanly with "Nothing was changed".
* `save`/`load` refuse absolute paths and path traversal, and survive a corrupt
  file without losing the running game.
* Bribery is capped as documented (~32 protection points, the rest refunded).
* Fog of war does not leak: `why telescope` and `path` are refused under fog.
* Bounties cannot be double-posted or double-charged.
* Mortality mode ends the run some years after the founder dies, as described.
