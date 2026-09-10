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
