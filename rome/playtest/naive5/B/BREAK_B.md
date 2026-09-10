# BREAK_B — playtest notes

Started. Goal: Han China, 100 AD, fog of war ON, poor scholar purse, founder NOT ageing.

## Setup
Answers piped: `1` (Han China 100), `y` (fog of war ON), `poor_scholar`, `n` (founder does not age).
Save file created: `/home/user/test/rome/playtest/naive5/B/han_china_100ad.json`.
Opening prompt line: `[100 AD | 400 den | you:2000 hr | sch 0 art 0 | rep 5] >`

EXPECTATION going in: a tech-tree sim where hours + money + reputation gate projects.
Suspicion targets, in order: (1) save-file trust / resume semantics, (2) fog of war leaking
info via `why`/error messages, (3) money and hour accounting (negative values, overspend),
(4) time: `step` with weird args, (5) people/hiring economics.

## First look (year 100)
- 135 technologies "granted for free"; 0 built by me. Already earning 233.5 den/yr from
  `med_cataract_couching` (166.7) and `med_trepanation` (66.7) — a penniless newcomer who has
  never introduced anything is already running a surgical practice. EXPECTED: 0 income at start
  for a "poor scholar ... must earn". ACTUAL: +233.5/yr revenue, net +3.5/yr. Suspicious, noted.
- `available` shows `med_obstetric_practice`: cost 14.1, hours 0, years 0, earns 12.5/yr.
  EXPECTATION: a project costing 0 hours and 0 years that pays 12.5/yr forever is a money pump.
  If several exist, the "poor founder choosing between eating and building" framing is broken.
  Going to test.
- Attack surface list from `help commands`: save/load arbitrary file, JSON command paste,
  work <trade> <hours>, bounty, bribe, quote, step <years>, hire/fire/train/commission, buy.

## Guards that HELD (could not break)
- `step -5` / `step 0` -> "REFUSED: years must be >= 1". `step 0.001` -> "REFUSED: years must be a
  whole number of years; 0.001 is not. Nothing was changed."
- `work smith -1000` -> REFUSED hours>0. `work smith 1000000` -> "REFUSED: you have 2000 of your own
  hours left this year, not 1000000".
- `bribe -5000`, `hire smith -3`, `buy slaves -5`, `commission smith -400` all REFUSED with
  "Nothing was changed."  Negative-number injection is properly guarded everywhere I tried.

## FINDING 1 (confirmed, mechanic): free-granted revenue is a linear function of unspent founder hours
Repro, from a fresh 100 AD save:
  `money`                -> Revenue 233.5/yr (med_cataract_couching 166.7, med_trepanation 66.7)
  `work smith 1`         -> earned 0.10; `money` -> Revenue 233.4 (166.6 + 66.6)
  `work smith 1999`      -> earned 151.3; `money` -> Revenue 0, no "from:" block at all
EXPECTED: taking a side job would not delete a standing medical practice's whole annual income;
at worst it should prorate. ACTUAL: it does prorate, exactly linearly with founder-hours left, and
at 0 hours the income silently disappears from the ledger with no message. Defensible as a model
(you can't operate if you're at the forge) but there is NO warning: nothing tells you that spending
hours costs you revenue, and `work` is advertised as "do an ordinary job for ordinary pay".

## FINDING 2 (numbers contradict the game's own claims)
- Setup screen: "poor_scholar 400 den — A few months' subsistence". Ledger says living and
  appearances = 230 den/yr. 400 den is therefore ~1.7 YEARS of subsistence, not "a few months".
- `work smith 2000` (an entire working year of skilled smithing) earns 151.3 den, i.e. 0.076 den/hr,
  while merely existing costs 230 den/yr. An ordinary tradesman in this world cannot feed himself
  by working. Confidence this is wrong: high that it is internally inconsistent, medium that it
  is unintended.
- Side effect: after `work smith 2000`, "living and appearances" DROPPED 230 -> 218.3 and the credit
  limit dropped 1,025 -> 937.5, purely because revenue went to 0. Expenses that shrink when your
  income shrinks were not explained anywhere.

## FINDING 3 (undocumented commands)
`help commands` lists 20-odd commands and does NOT include `open` or `ventures`, yet NOTHING you
build earns anything until you `open` it. You only learn this from the completion event text.

## FINDING 4 — HEADLINE BUG: resuming a saved game silently destroys project progress,
## and any project with a calendar floor of 2 years can NEVER be completed if you play
## one year per sitting.

The game promises exactly this play pattern:
  `help sittings`: "The game is written to that file after every command and read back when
   you start again, so you do not need to hold a process open or write a script."
  startup text: "you can stop any time - close the terminal, anything - and come back to
   exactly where you left off".
EXPECTATION from that: N separate `step 1` invocations == one `step N`. It is not.

REPRO A (same logical state, two different outcomes)
  cp a fresh 100 AD save twice.
  (i) ONE process:
      printf 'start fin_bimetallism\nstep 1\nstate\nstep 1\nstate\n' | python3 .../simulator.py play --session B2.json
      -> at 101: "Bimetallism and fixed exchan 100% of your hours spent, 24.2 den still owed"
      -> next step: "COMPLETED 101: Bimetallism and fixed exchange", 102 AD, "1 built by you"
  (ii) TWO processes, identical commands:
      proc1: printf 'start fin_bimetallism\nstep 1\n'   -> 101 AD, "100% of your hours spent, 24.2 den still owed"  (IDENTICAL display)
      proc2: printf 'step 1\n'                          -> 102 AD, "60% of your hours spent, 0 den still owed - waiting on your hours"  NOT completed
  Deterministic: ran proc2 from 5 identical copies, all 5 gave 60%. Also inserting
  `state`/`help`/`money`/`available` before the step changes nothing, so it is not RNG order.

REPRO B (the project never finishes at all)
  start fin_bimetallism at 100 AD, then run `step 1` in a SEPARATE process eight times.
  Years 101..108 alternate forever:
    101 "100% ... waiting on money"     102 "60% ... waiting on your hours"
    103 "100% ... waiting on the calendar"  104 "60% ..."   105 "100%..."  106 "60%..."
    107 "100%..."  108 "60%..."
  Eight years in, `state` still shows RUNNING (1) and "0 built by you". Money (48.45 den) and
  ~50 founder hours a year are consumed with no possibility of completion.
  Inspecting the save the game itself writes shows the mechanism: the project's accumulated
  calendar years `yrs` and its remaining founder hours `ph_left` oscillate
    yrs 1.0 / ph_left 0.0  ->  yrs 0.0 / ph_left 40.0  ->  yrs 1.0 / ph_left 0.0  -> ...
  i.e. every resume throws away the founder hours already booked, which resets the calendar
  clock, which can never then reach the 2-year floor.
CONFIDENCE: very high that this is a real defect. The game's own documentation states the
opposite behaviour, and the two paths disagree on identical input.
IMPACT: worst case for the advertised "play across sittings" mode. Anything with floor >= 2
years is unbuildable; everything else is slower than it should be.

## FINDING 5 — fog of war leaks the whole tech-tree namespace through the "did you mean" suggester
`help fog` claims: "You cannot see where anything leads, and there is no way to view the whole tree."
`why point_contact_transistor` correctly REFUSES: "you have never heard of that."
BUT a *misspelling* is answered with real node ids from anywhere in the tree:
  > why transistor
  REFUSED: unknown node 'transistor'. did you mean: junction_transistor, point_contact_transistor,
  tl_radiator, tr_pantograph, tl_tractor
  > why silicon
  ... did you mean: ch2_polymer_silicone, mt2_silicon_steel_transformer, silicon_path
  > why semiconductor
  ... did you mean: com_semiconductor_diode, semiconductor_metrology
  > why photolith
  ... did you mean: com_photolithography, if_chromolithography, if_lithography, prn_offset_lithography, photography
  > why germanium   -> germanium_extraction
  > why turbine     -> en_fourneyron_turbine, en_francis_turbine, en_gas_turbine, en_kaplan_turbine,
                      en_steam_turbine_curtis, en_steam_turbine_impulse, en_steam_turbine_reaction, en_turbine_blading
20 guessed words harvested ~120 node ids I have "never heard of", including the ones obviously on
the road to the goal (silicon_path, germanium_extraction, semiconductor_metrology, com_photolithography,
com_vacuum_tube_*). CONFIDENCE: high that this contradicts the stated fog rule. It leaks node NAMES,
not edges, so it is a partial leak - but the ids are descriptive enough to reconstruct most of the map.
Cosmetic bug in the same place: `why radio` replies "did you mean: no idea", which reads as a node name.


## FINDING 6 — `policy auto_hire on` bankrupts you while claiming to hire only what you can pay
Description given by the game: "auto hire: grow the staff toward what you can house and pay".
REPRO (fresh 100 AD save, nothing else done):
  printf 'policy auto_hire on\nstep 10\nstate\nmoney\n' | ... --session ah.json
EXPECTED: with no projects running and no ventures open, nothing to staff, so no hiring.
ACTUAL: it hires artisans anyway - 0.86 FTE, 113 den/yr of wages against 259 den/yr of revenue
and 226 den/yr of living costs - and the log reads:
  EVENT 105: interest on 361 denarii of arrears at 11.9% a year
  EVENT 108: you cannot pay everyone: 0.3 of your staff leave for work that pays
  EVENT 108: BONDAGE: you cannot pay, and you enter service for your debt. For about 12 years
             most of your hours belong to someone else.
Ten years of doing literally nothing but switching one automation on takes you from 400 den to
debt bondage. CONFIDENCE: high that this contradicts the stated behaviour.

## FINDING 7 — `policy auto_open on` silently stops working once you are in debt
In the main session (capital -460 den) seven finished ventures worth ~1,000 den/yr of revenue sat
unopened for 3 years with `auto open: True`; each needed only 3.6-40 den to open against a
credit limit of 3,455. In a solvent game the same policy opens them on the next step, so the
policy works but gives up in exactly the situation where you need it, with NO message. Combined
with Finding 6 this is a trap: auto_hire puts you in debt, which disables auto_open.

## FINDING 8 — `work` is a trap, and forced labour is free while voluntary labour is ruinous
`help commands`: "work <trade> <hours>: do an ordinary job for ordinary pay".
Revenue from the practices the society grants you is scaled by (hours you spend at wage work) /
(hours available). So:
  at 111 AD, in debt bondage, 500 hours available, 0 worked -> Revenue 259.3 den/yr (FULL)
  `work smith 500` -> "earned: 37.6" and Revenue collapses to 0 den/yr, Net/yr -75.3 -> -319
A year of smithing earns 37.6 den and destroys 259.3 den of income: a net loss of 221.7 den.
Nothing in the game warns you; `work` is presented as the way to earn when you are poor, and it
is the single worst thing a poor player can do.
Also inconsistent: being in DEBT BONDAGE, where the game says "for about 12 years most of your
hours belong to someone else", costs the medical practice NOTHING (revenue stays 259.3), while
choosing to work 500 hours costs it everything. Forced labour is free; voluntary labour is fatal.
CONFIDENCE: high that the bondage/work asymmetry is unintended.

## FINDING 9 — two separate debts that never reconcile
While in bondage: `state` shows "IN DEBT BONDAGE: 9 years left owing 740.8 den" while the same
screen shows "Money: -183.4 den" and `money` shows "Capital: -183.4". Paying capital back up
(work smith 500 -> capital -145.8) does not touch the 740.8 owed. There are two debt numbers and
the game never explains the relationship. Confidence: medium that it is a bug; certain it is confusing.

## FINDING 10 — `available` prints TRUNCATED ids that every other command rejects
The ID column is 30 characters wide and ids are cut without any marker.
  > available all
  ... air_observation_balloon_tether   Tethered observation ballo  1,004 ...
  ... hom_sewer_stormwater_separatio   Sewer separated from storm  1,636 ...
  > start air_observation_balloon_tether
  REFUSED: unknown node id 'air_observation_balloon_tether'. use available or why ... to find valid ids
  > why air_observation_balloon_tether
  REFUSED: unknown node 'air_observation_balloon_tether'. did you mean: air_observation_balloon_tethered, ...
  > why hom_sewer_stormwater_separatio
  ... did you mean: hom_sewer_stormwater_separation, ...
So `available` - the command the game tells you to use to find valid ids, and the ONLY way to see
them under fog - emits ids that cannot be used, and the error message tells you to go back to the
command that produced them. CONFIDENCE: certain this is a bug.

## FINDING 11 — reported staffing requirements disagree between `ventures` and `open`
  > ventures
    - id=ag2_contour_ploughing, ... needs={'scholars': 0.0, 'craftsmen': 1.0}, to_open_it=40.0
  > open ag2_contour_ploughing
    REFUSED: nobody free to keep an eye on it: it needs 0.0 scholars and 0.2 craftsmen to supervise
1.0 vs 0.2 for the same venture in the same turn. Confidence: certain they disagree; medium that
one of them is wrong rather than two different quantities sharing one label.

## FINDING 12 — the premise ("you arrive alone; anyone who works for you is hired") is not enforced
At 130 AD in an ordinary greedy playthrough: "RUNNING AS CONCERNS: 51 ... EMPLOY: 0 people,
0 den/yr in wages". Those 51 concerns include `fud_whaling_industry` (Organized whaling industry,
1,610 den/yr), `fin_gambling_house`, `fin_inn`, `fin_pawnshop`, `pwr_coal_seam` (a coal mine) and
`chm_phosphorus_extraction` - all running with literally zero employees and zero wages, because
`ventures` reports needs={'scholars': 0.0, 'craftsmen': 0.0} for them. A one-man whaling industry
and a one-man coal seam is exactly the thing the opening screen says the model refuses to do.

## FINDING 13 — the economy compounds without limit and contradicts the setup screen's own framing
Greedy but entirely legal play from the 400-den poor-scholar start, all inside one process:
   100 AD    400 den
   115 AD  22,400 den
   130 AD 153,422 den, revenue 13,434 den/yr, 51 concerns, 0 employees
   245 AD 530,108 den, revenue 34,393 den/yr
   325 AD 601,572 den, revenue ~49,000 den/yr
The setup screen says the `absurd` purse of 1,000,000 den is "four senatorial fortunes" and buys
"perhaps a tenth off the time"; ordinary play passes half of it inside 150 years and would pass all
of it. Once nothing new is startable, revenue still grows ~3.3%/yr by itself forever
(34,689 -> 48,999 den/yr from 250 to 325 AD with zero new technologies and zero actions).

## FINDING 14 — FOUNDER HOURS CAN BE SPENT TWICE: `train` and `work` use different counters
REPRO from a fresh 100 AD save (2,000 founder-hours in the year):
  > train machinist 2
    training: 2 machinists will be ready in 2 years
    capital: 45.6
    your hours left this year: 1,100          <- train's own counter: 2000-900
  > train chemist 2
    your hours left this year: 200            <- 1100-900
  > train engineer 2
    REFUSED: teaching 2 engineers takes 900 of your own hours and you have 200 uncommitted   <- guard works
  > state
    You: alive (you do not age), 2,000 founder-hours free this year   <- WRONG, 1,800 were just spent
  > work smith 2000
    earned: 151.3 ... your hours left this year: 0                     <- ACCEPTED
Total founder hours spent in the year 100: 1,800 teaching + 2,000 smithing = 3,800 of 2,000.
The prompt also never moves: it reads `you:2000 hr` throughout the two trainings.
The asymmetry is one-directional - `work smith 2000` first DOES make `train` refuse
("teaching 2 machinists takes 900 of your own hours and you have 0 uncommitted this year"),
so `train` reads the shared counter but never writes to it.
CONFIDENCE: certain. This is the clearest resource-accounting bug I found.

## FINDING 15 — `train` will teach a trade the society already has, contradicting its own help
`help labour`: "train: teaches a trade that does not exist here, out of your own hours" and
"A trade that does not exist here cannot be hired at any price; teach one with train."
`labour` lists smith under "YOU COULD HIRE" and MUST BE TAUGHT: chemist, electrician, engineer,
machinist, optician.
  > train smith 2
    training: 2 smiths will be ready in 2 years
    capital: 53.2 (i.e. 354 den) ... 900 of your own hours
Accepted, at 354 den and 900 founder-hours, for people you could simply hire. No warning.

## FINDING 16 — reputation only ever costs you money
`buy slaves 20` then `buy manumit 20`, repeated 5 times inside one turn at 130 AD:
  reputation 59 -> 63.5 -> 66.5 -> 68.9 -> 70.8 -> 72.4 (diminishing; slave price rises each time,
  so the pump self-limits - a guard that HELD)
but `money` before and after: Revenue unchanged at 13,434 den/yr, while "living and appearances"
went 3,317 -> 7,063 den/yr. 50,000 den spent to double your own overheads and gain nothing visible.
Reputation is printed in the status bar of every single screen and the only measurable effect I
could find is that it raises your annual expenses and your credit limit.
Also unrealistic: 100 people can be bought and freed inside a single turn with no time passing.

## More guards that HELD
- `hire smith 100000` -> "REFUSED: hiring 100000 smiths costs 14765625 denarii in advance and you have 601225"
- `train machinist 4` when the pool is exhausted -> "REFUSED: this society's literacy will not supply
  more than 3.5 machinists in total, ever, at any price" (good hard cap)
- `start hom_button` twice -> "REFUSED: already active"; `stop` an inactive id -> "REFUSED: not active"
- `fire smith 5` with none -> "REFUSED: you employ no smiths"; `close coal` with no mine -> refused
- `buy manumit 100` with 0 slaves -> "REFUSED: you have no slaves to free"
- mothball/open cycling costs money every time; no free-money loop there
- save/load round-trips state faithfully (year, capital, hours) - only the ACTIVE-PROJECT bug (Finding 4) leaks
- `save` outside the start directory: both `save /etc/x` and `save ../../../../../../../tmp/x.json`
  refused ("a save file must be a relative path" / "cannot be written outside the directory you started in")
- JSON command paste works as advertised: `{"cmd": "work", "trade": "smith", "hours": 100}` ran;
  `{"cmd":"step","years":-3}` was refused by the same guard as the text form; `{"cmd":"capital","amount":999999}`
  -> "REFUSED: unknown cmd 'capital'". No extra powers via the JSON channel that I could find.
