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
