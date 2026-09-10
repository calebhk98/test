# BREAK_B — playtest notes (naive6/B)

Rules I'm following: only the running program tells me anything. No source, no data files, no docs, no other notes.

## Log

## Setup
England 1300, fog ON, poor_scholar (400 den), founder does not age.
Session file: /home/user/test/rome/playtest/naive6/B/england_1300.json

### Nit 0 — the resume command it prints is wrong from where it told me to run
On exit it always prints:
    python3 rome/sim/simulator.py play --session england_1300.json
That relative path only works if cwd == /home/user/test. I was told to run it from
/home/user/test/rome/playtest/naive6/B, where `rome/sim/simulator.py` does not exist.
Cosmetic, but it is the program telling me how to come back and the instruction does not work.
Confidence: certain it's wrong-as-printed; low stakes.

## EXPECTATION LOG

E1. Expect: `money` revenue should only come from things `ventures` lists as RUNNING,
because help says "open <id>: ... until you do, it earns nothing and costs nothing"
and ventures says "Only what you are RUNNING earns anything or costs anything."

ACTUAL (turn 1, no commands yet):
  money  -> Revenue: 232.8 den/yr   from: med_cataract_couching 166.7, med_trepanation 66.7
  ventures -> "running: nothing / you know how but have not opened: nothing"
  state  -> "technologies: 0 built by you, 132 granted for free (132 total)"

**FINDING 1 (contradiction): income from ventures that are neither running nor openable.**
Repro: `printf 'money\nventures\n' | python3 .../simulator.py play --session england_1300.json`
Two of the 132 free-granted technologies pay me 232.8 den/yr, yet the ventures screen
claims nothing is running and nothing is available to open, and states as a rule that
only RUNNING things earn. One of the two statements is false.
Confidence it's a real inconsistency in what the program says: high.
Whether the *money* is intended (era-granted background income) : plausible, but then
the ventures note and the `open` help text are both lying.

E2. Expect `risk` to agree with `state`. state said "3 technologies at risk, 0 lost per
sacking on average, hedged by nothing yet".
ACTUAL: risk says "technologies at risk: 3, chance lost if a site is sacked: 80%,
fraction lost when it happens: 40%" and then, two lines later,
"no remaining hazard for this civilization sacks a site, so nothing here is currently
at risk of being forgotten".
So the headline "3 technologies at risk" is misleading: nothing is at risk. Minor
presentation bug, not a mechanical one. Confidence: medium that it is unintended.

---
## FINDING 2 — the `why` refusal messages are an oracle that defeats fog of war
Fog help says: "You cannot see where anything leads, and there is no way to view the whole tree."
`available` says: "There is no way to see the whole tree."

But `why <id>` gives THREE distinguishable answers:
  - a real node I have heard of  -> the full card
  - a real node I have NOT heard of -> "REFUSED: you have never heard of that."
  - an id that does not exist    -> "REFUSED: unknown node 'X'. did you mean: ..."

Repro (1301):
  why point_contact_transistor -> REFUSED: you have never heard of that. ...
  why zzzz_nonsense            -> REFUSED: unknown node 'zzzz_nonsense'. did you mean: no idea...
So I can test any guessed id for EXISTENCE for free, unlimited, with no cost and no
time passing. That is a membership oracle over the whole tree.
Confidence this is unintended: high — the program explicitly promises the opposite.

## FINDING 3 — the "did you mean" suggester leaks ids I have not heard of, while saying it won't
It prints "did you mean: no idea, and under fog of war I can only suggest things you
have heard of". That claim is false.
Repro (1301):
  why steam_engine      -> did you mean: sea_log_line, sea_sounding_lines
  why met_blast_furnace -> did you mean: blast_furnace, mat_cast_iron
`sea_sounding_lines`, `blast_furnace` and `mat_cast_iron` were in NEITHER my
`available all` (105 items) NOR the "heard of, cannot begin yet" list. Following the
leak, `why blast_furnace` then printed the complete card for a tier-2 node.
So: fuzzy-matching junk strings walks the tree. Confidence unintended: high.

## FINDING 4 — England 1300 already owns the blast furnace, which the briefing says nobody has built
Scenario briefing at setup, verbatim:
  "WHAT IS MISSING / Cheap iron, and the temperature to make it. Everything downstream
   of steel waits on a furnace nobody has yet built."
`why blast_furnace` in that same game:
  "STATUS: DONE / THIS SOCIETY ALREADY HAS THIS. You did not build it and do not maintain it."
and its own blurb: "this is the biggest single technology gap you face."
`why mat_cast_iron` -> also DONE.
So the single thing the scenario is built around being missing is pre-granted.
(The briefing is also self-contradictory: "WHAT YOU CAN SEE ... the blast-furnace
arriving" vs "a furnace nobody has yet built".)
Confidence something is wrong: high. Which half is wrong I can't tell from inside.

## FINDING 5 — `ventures` reports a venture's staffing need as 0.0/0.0; `open` then refuses it for staffing
Repro (1301, after building tex_horizontal_loom):
  ventures ->
    - id=tex_horizontal_loom, ..., needs={'scholars': 0.0, 'craftsmen': 0.0}, to_open_it=30.0
  open tex_horizontal_loom ->
    REFUSED: nobody free to keep an eye on it: it needs 0.0 scholars and 0.3 craftsmen
    to supervise, and you have 1.0 and 0.0 not already watching something else.
0.0 craftsmen in the listing, 0.3 craftsmen in the refusal. The screen whose job is to
tell me what a venture needs rounds the requirement away to zero.
Confidence it's a real reporting bug: high.

## FINDING 6 — `available find X` does not filter the "heard of" section
Repro: `available find transistor` -> "1-0 matching 'transistor'" then lists 9
HEARD-OF entries, none of which contain "transistor" (chm_continuous_batch,
opt_gravimeter, cap_measure_time_ms, ...). Cosmetic. Confidence: high it's a bug.

## FINDING 7 — a cost card whose own arithmetic does not add up
Every other card checks out exactly:
  units_standards (104+90+250)=444 x0.85 x1.1 = 415.14  -> printed 415.1  OK
  civ_arch_roman  (19.2+350)=369.2 x0.90 x1.1 = 365.5   -> printed 365.5  OK
  sea_lodestone   (32+100)=132 x0.85 x1.1 = 123.42      -> printed 123.4  OK
  chm_continuous_batch (100+500)=600 x1 x1.1 = 660      -> printed 660    OK
  opt_stellar_parallax (135+5.6+500)=640.6 x1.1 = 704.66-> printed 704.7  OK
But:
  why clock_pendulum ->
  "COST: 4,834 den total (1,566 labour + 550 materials + 2,200 capital, then x1 your civ, x1 distance, x1.1 prices)"
  (1566+550+2200) x 1 x 1.1 = 4,747.6, not 4,834.  Off by 86.4 (+1.8%).
Confidence it's a real discrepancy: high (arithmetic). Cause unknown from inside;
it is the only card I found so far with an untaught trade (machinist) in HIRED LABOUR
AND a non-zero total, but chm_continuous_batch also has an untaught trade and adds up,
so that is not the explanation.

## FINDING 8 — England 1300 is granted the pendulum clock, dated 1656 in reality
`why clock_pendulum` -> "STATUS: DONE. THIS SOCIETY ALREADY HAS THIS."
The setup briefing for this scenario says "the mechanical clock arriving" — i.e. the
verge escapement, not Huygens' pendulum. As a consequence the tier-2 capability
`cap_measure_time_s` ("Time to the second (pendulum)") is startable in 1300 for
0 den, 0 hours, 0 years. I built it in 1300, turn one. Realism/balance, not a crash.
Confidence unintended: medium-high.

## FINDING 9 — granted technologies pay revenue, but only some of them, and nothing says why
`money` at 1300: Revenue 232.8/yr, from med_cataract_couching 166.7 and med_trepanation 66.7.
`ventures`: "running: nothing / you know how but have not opened: nothing" plus
  "Only what you are RUNNING earns anything or costs anything."
`why med_cataract_couching` -> STATUS DONE (granted), REVENUE: 500 den/yr. I receive 166.7.
`why blast_furnace` -> also DONE (granted), REVENUE: 22,000 den/yr, upkeep 7,000. I receive 0.
So of 132 free-granted technologies exactly two pay me, at one third of their listed
rate, without being "run", and the biggest earner of the lot pays nothing.
Confidence something here is wrong: high.

---
## EXPECTATION LOG (continued)

E3. Expect: `work <trade> <hours>` is a side job that does not touch anything else.
ACTUAL: `work scholar 2000` (spending all 2,000 founder-hours) made the ledger's
Revenue go from 248.4 to **0**; med_cataract_couching and med_trepanation vanished
from the income list entirely. After `step 1` they came back. `work scholar 1`
shaved 0.2 off revenue. So those "granted" incomes are silently prorated by my
UNSPENT founder-hours. Nothing in help, `money`, `ventures` or `why` says so.
Not a bug on its own, but it proves the two granted incomes are really MY labour,
which makes `ventures`' "running: nothing" flatly wrong (see FINDING 9).

## FINDING 10 — open once, fire everyone, keep the money forever
`open` enforces a supervision requirement. Nothing ever re-checks it.
Repro from the 1302 save (1 artisan employed, tex_horizontal_loom open):
  fire artisan 1   -> "let go: artisan / annual wage bill: 0"
  labour           -> "ON YOUR STAFF: nobody"
  money            -> Revenue 683.5, of which tex_horizontal_loom 435.5. Net/yr
                      jumps from +169.8 to +382.1 purely by firing the man.
  step 1 ; money   -> still 435.5 from tex_horizontal_loom, still nobody employed.
And in the 500-year fast-forward the same venture was still paying exactly 435.5/yr
in 1800 with "EMPLOY: 0 people" after the Black Death had taken everyone.
So the optimal play is: hire one artisan for a single command, open every concern
you can, fire him. Confidence this is unintended: high — `open` refuses with
"nobody free to keep an eye on it ... Hire, teach, or close something", i.e. the
game states supervision is required to run the thing, not merely to start it.

## FINDING 11 — a venture's earnings are frozen at open time and never re-derived
`open tex_horizontal_loom` announced "it earns 400 a year".
Ledger the same turn: tex_horizontal_loom **284.5**.
Ledger one year later: **435.5**.
Ledger in 1800, 498 years later, after the Black Death, with reputation fallen from
8.9 to 1.5 and living costs doubled from 251 to 517: still **435.5**, to the decimal.
Meanwhile the granted medical incomes DO move with reputation early on
(166.7 at rep 5 -> 177.8 at rep 9.1) but then also stick at 181.5 from 1302 to 1800
while reputation falls to 1.5.
So: three different numbers for "what this earns" (400 advertised, 284.5 first year,
435.5 forever after), and a revenue line that stops responding to the things it
visibly responded to earlier. Confidence something is wrong: high.

## FINDING 12 — the Black Death is applied three times at its full advertised rate
`risk` says: "[1348-1350] Black Death ... staff loss after what you have built: 45%".
Actual events in the 500-year run:
  EVENT 1348: Black Death: staff -45%, and 1,642 pence gone with the trade that stopped
  EVENT 1349: Black Death: staff -45%, ...
  EVENT 1350: Black Death: staff -45%, ...
That is 0.55^3 = 83% of staff gone, not 45%. The risk screen quotes one number and
charges it once per year of the date range. Confidence it's misreported: high;
whether the triple application is intended: medium.

## FINDING 13 — currency unit slips from "den" to "pence"
Everywhere: "den". But:
  bounty tex_knitting_frame -> "REFUSED: cannot afford the bounty: needs about 1959
  pence, you have 612."  (compares 1959 "pence" against 612 "den" in one sentence)
  EVENT 1348: "... and 1,642 pence gone with the trade that stopped"
Confidence it's a bug: high (at minimum an inconsistency; at worst two different
units are being compared as if equal).

## FINDING 14 — a canned example number presented as if it were my staff
`state` with one artisan employed prints:
  "EMPLOY: 0.96 people ... 1.32 artisans is the wage and output of one artisan plus
   a third of another's."
1.32 is not my number (0.96 is). It reads as a statement about my workshop.
Confidence: high it's a hardcoded illustration leaking into a status line.

## Attacked and could NOT break
- Negative / zero arguments are all guarded:
  step -5 / step 0 -> "years must be >= 1"; hire smith -3 -> "n must be greater than
  zero. Nothing was changed."; bribe -1000, buy slaves -5, work scribe -100000 all refused.
- Overlong requests: `work scholar 1e9` -> "you have 0 of your own hours left this
  year, not 1000000000". No overflow, no free money.
- Path traversal on `save`: absolute paths refused ("must be a relative path");
  `save ../escaped.json` -> "a save file cannot be written outside the directory you
  started in"; `save sub/deep/x.json` works and stays inside. Clean.
- The save file itself does NOT leak the tech tree: it contains only my own state
  (done/granted/revealed sets), no unheard-of node ids, no "transistor". Fog holds there.
- `step 500` at 1302 -> refused with the correct remaining count (498). Horizon
  enforced; after 1800 `step` refuses and the run is marked ended.
- `why` on a BLOCKED node does not reveal its missing prerequisites: it still says
  "this needs 3 other things you have not heard of yet". Fog holds on that axis.

---
## FINDING 15 — `labour <trade>` contradicts itself inside one block
Repro: `train machinist 2`, then `labour machinist`:
  TRADE: machinist (craft)
  exists here: True
  ...
  does not exist yet; you must create this trade
"exists here: True" and "does not exist yet" printed three lines apart about the
same trade. Also `labour` moves machinist out of "MUST BE TAUGHT" into
"YOU COULD HIRE" the instant training STARTS (ready 1305, shown as hireable in 1303),
while `hire machinist 3` refuses. Confidence: high.

## FINDING 16 — `train` charges money it never mentions
The hint (in `why chm_continuous_batch`) is: "Teach one: train chemist 2 (about 450 of
your own hours each, two years)". Hours only.
Repro at 1303 with 306 den: `train machinist 2` ->
  "training: 2 machinists will be ready in 2 years / capital: -289.8 / your hours left this year: 1,100"
900 founder-hours as advertised, plus 595.8 den never mentioned, straight into debt
with no warning and no confirmation. Confidence it's under-documented: high.

## FINDING 17 — the housing/supervision cap applies to hired people but not to bought people
Same save, same turn:
  hire artisan 50 -> "REFUSED: you can supervise, house and teach 15.99 more people,
                      not 50 - 15 is the most whole people you can take."
  buy slaves 500  -> "bought: 500 / slaves: 500 / capital: 2,460,574"
500 > 15.99. The constraint the game states as physical ("supervise, house and teach")
is simply not checked on the purchase path.
(Caveat: I had to tamper my save's `capital` to afford 500; the capacity refusal and
the successful purchase were in the same turn at the same capacity, so the asymmetry
itself is real regardless of where the money came from.)
Confidence unintended: medium-high.

## FINDING 18 — bought people are invisible to every people-reporting screen
After `buy slaves 500`:
  state  -> "EMPLOY: 0 people, 0 d/yr in wages / nobody"
  labour -> "ON YOUR STAFF: nobody ... Total employed: 0"
and `labour` grows an entry reading literally:
  IN TRAINING:
    None x275, ready 1306.0
A trade named "None". The help for `buy slaves` says the option exists because
"a model that hides it lies about the cost of everything" — and then the labour
screen hides it. Confidence the "None x275" line is a bug: high.

## FINDING 19 — the currency is printed three different ways
  normal:            "400 den", "Money: 259.4 den"
  any money refusal: "needs about 1959 pence, you have 612"; "hiring 50 artisans costs
                      11000 pence in advance and you have 407"; "restored: ... for 40 pence";
                      "EVENT 1348: ... 1,642 pence gone"
  once capital is large: "Money: 2,460,574 d ... net -52,276 d/yr ... 0 d/yr in wages"
Three labels for one unit, and the "pence" lines compare a pence figure to a den figure
in the same sentence. Confidence it's a bug: high.

## FINDING 20 — the goal needs 25 scholars; this society will supply 2.2, ever
  why point_contact_transistor -> "STAFF NEEDED: 25 scholars, 20 artisans"
  hire scholar 10000 -> "REFUSED: this society's literacy will not supply more than
     2.2 scholars in total, ever, at any price; you already have 0.0 ... Raise
     literacy_general or literacy_elite -- printing, schools and libraries do."
So the win condition is unreachable until literacy is raised, and under fog of war
nothing on the `available`, `state` or `why` screens tells you that literacy is a
resource you must farm. Not necessarily a bug — but the only place the game ever
mentions it is inside a refusal you only see if you ask for an absurd number of people.
Confidence it's a design/telegraphing hole rather than a defect: medium.

## FINDING 21 — fog-on `why` says nothing depends on a node that something depends on
Cross-checked against a SEPARATE, legitimately-created fog-OFF England 1300 game
(the setup screen offers fog off, so this is a fair comparison; same civ, same year,
same 105 startable items, so the two games agree on everything else).
  fog ON : why sea_pharos_lighthouse -> "HOW MUCH RESTS ON THIS: nothing else; this is
           worth having for itself"
  fog OFF: why sea_pharos_lighthouse -> "DIRECTLY UNLOCKS: sea_fresnel_lens /
           TOTAL DOWNSTREAM: 1 thing(s) depend on this"
Fog is supposed to make you vaguer, not wrong. "nothing else" is a false statement,
and it is exactly the statement a player uses to decide not to build something.
Also fog ON calls cap_measure_time_s "a few things"; fog OFF says 35 depend on it,
while civ_arch_roman at 41 gets called "some". Confidence: high.

## FINDING 22 — the granted-technology set is internally inconsistent with its own tree
In the fog-OFF England 1300 game:
  why blast_furnace       -> STATUS: DONE (society already has it)
  why bellows_water_blown -> STATUS: BLOCKED     <- a listed route into blast_furnace
  why mat_bronze          -> STATUS: DONE
  why mat_copper          -> STATUS: BLOCKED, cost 217,092 den
England 1300 is granted bronze but not copper, and the blast furnace but not the
water-blown bellows. Confidence something is wrong: high.

## More I attacked and could NOT break
- JSON commands: `{"cmd":"state"}` works; `{"command":...}`/`{"action":...}`/`{}` are
  refused with "a JSON command needs a 'cmd' field". No hidden verbs: debug, tree,
  dump, cheat, set, grant all -> "unknown cmd", and the refusal lists exactly the 29
  documented commands.
- Fog cannot be turned off through a JSON field: `{"cmd":"available","all":true,"fog":false}`
  and `{"cmd":"path","id":"...","fog":false}` behave exactly as under fog.
- Trade supply is capped and the caps hold: `commission smith 1000000` ->
  "the smiths here can spare 6393 more hours this year"; `commission machinist 5000`
  after training started -> "the machinists here can spare 0 more hours this year".
- `hire artisan 10000` refused on cash, and at capacity refused on capacity.
- Under fog, the same capacity refusal correctly SUPPRESSES the node ids
  (`freedman_staff`, `workshop_first`) that the fog-off version names. Fog holds there.
- mothball/restore is not an upkeep dodge: restoring costs 2x the annual upkeep
  (20/yr -> "40 pence", 30/yr -> "60 pence") and mothballing stops the revenue too.

## THINGS THAT STRUCK ME AS UNREALISTIC
- A horizontal loom I own outright earns 435 den a year for 498 straight years with
  nobody working it, through the Black Death, at an unchanging price, while my own
  cost of living doubles.
- Hiring one artisan and firing him the same afternoon permanently satisfies the
  requirement to have someone "keep an eye on" a workshop.
- Working a year as a jobbing scholar (575 den) pays better per hour than the
  cataract-couching practice the game hands me for free (0.29 vs 0.12 den/hr).
- 500 slaves appear on no screen that counts people.
- 500 tonnes a year of gold is quotable (88,000,000 den to sink) with no comment.

---
## CAVEAT: the program was being edited while I played it
`find /home/user/test/rome -newermt "2026-09-10 14:15"` shows engine/economy.py,
engine/projects.py, engine/cli.py, engine/labour.py, engine/protocol.py and
engine/data.py all rewritten DURING this session (14:24 - 14:32; my session started
~14:17). I only looked at timestamps, not contents.
One consequence I actually observed: at the start of the session `money` printed
"Capital: 400 den / Revenue: 232.8 den/yr"; later the byte-identical save file with
the identical command printed "Capital: 400 d / Revenue: 232.8 d/yr", while the
prompt bar kept saying "400 den". So the "den"/"d" split in FINDING 19 may be a
live edit rather than one build's inconsistency — but "den" in the prompt bar vs
"d" in the body of the same screen is a real disagreement in the build I now have.
I re-verified findings 1/2/3/4/9 against the build as of 14:32 and they all still
reproduce.

---
## FINDING 23 — the ledger's itemised revenue does not add up to its own total
help money says: "the ledger: money itemises what comes in and what goes out,
including where the income comes from".
At 1300 (fresh game, two income lines):
  Revenue: 232.8   from: med_cataract_couching 166.7 + med_trepanation 66.7 = 233.4
At 1319 in my main run (17 concerns open):
  Revenue: 6,738   from: 15 listed rows summing to 7,101.9   (gap 363.9, 5.4%)
and the total is the authoritative one: Net/yr 4,908 = 6,738 - 608 upkeep - 1,222 living.
On top of that the breakdown is silently truncated at 15 rows: tex_canvas (running,
earns ~100) and med_trepanation (running, earns ~80) appear in `ventures` and in the
running set but not in the "from:" list, with no "and 2 more" line. So the list is
both short of entries and over the total at the same time.
Repro: `printf 'money\n' | python3 .../simulator.py play --session england_1300.json`
and add the "from:" column up.
Confidence it's a real defect: high (arithmetic, reproducible at two very different scales).

## FINDING 24 — the same hazard is applied once or three times depending on which hazard it is
  risk: "[1315-1317] Great Famine ... staff loss after what you have built: 12%"
  actual: a single "EVENT 1316: Great Famine: staff -12%" — one hit in a three-year window.
  risk: "[1348-1350] Black Death ... staff loss after what you have built: 45%"
  actual: three hits, "EVENT 1348/1349/1350: Black Death: staff -45%" - 83% compounded.
Two multi-year hazards described in the same format behave completely differently.
Confidence one of them is wrong: high.

## FINDING 10 (confirmed at scale)
At 1310, in the main run: `hire artisan 5` (bringing me to 6), `open` eleven concerns
in the same turn, then `fire artisan 6`. Result:
  labour -> "ON YOUR STAFF: nobody / Total employed: 0"
  money  -> Revenue 5,632 d/yr, Net/yr 4,476 (up from 2,876 with the staff)
  ventures -> 16 concerns listed under "running:", "craftsmen: 0"
By 1319, with nobody employed for nine years and a famine in between:
  Money 40,511 d, Revenue 6,738 d/yr, "RUNNING AS CONCERNS: 17", "EMPLOY: 0 people".
Total wage cost of the whole industrial base: about 1,100 den, paid once, for one turn.
Confidence unintended: high.

## FINDING 25 — eminence is advertised as the danger and never moves
Every `state` prints "EMINENCE is dangerous above 26 (settles near X if nothing
changes; 0% chance of ruin this year)". After building 18 things and running 17
concerns, with reputation at 37.5, eminence was 0.26 and "settles near 1.7"; by 1319
eminence 0.97, "settles near 1.8", still "0% chance of ruin this year". The whole
warning apparatus has never produced a non-zero risk in 19 years of aggressive,
conspicuous building. Confidence it's mis-tuned rather than broken: medium.

---
## FINDING 26 — FAILURE RISK appears never to fire
Every `why` card carries "FAILURE RISK: n%" (0-45% across the tree) and every
`available` row has a RISK column. I built, across this session:
  - 19 projects in the main run (1300-1319),
  - 60 more in one fork where I started all 94 startable ids at once and stepped 25 years,
  - 15 deliberately chosen high-risk ones (whaling 30%, coal seam 25%, gambling house 25%,
    skeleton-first 22%, diving bell 20%, phosphorus 20%, bimetallism 20%, hay 20%,
    safety lamps 16%, knitting frame 16%, pulp stamper 15%, leat and weir 15%,
    oil shale 15%, mortgage 15%, cartel 20%) in one turn.
Total ~113 builds. Mean advertised risk over the 105-item 1300 list is 7.9%, so the
expected number of failures is roughly 9-10. Observed: **zero**. Not one event,
message or line containing "fail", "abandon" or "lost" in any run
(`step 20` output grepped case-insensitively -> 0 matches).
P(0 failures | lambda ~ 9) is about 1 in 8,000.
Either the risk is not applied, or "failure" is silent and invisible - and if it is
silent, the number on the card promises a consequence the game never shows you.
Confidence something is wrong: high.

## FINDING 27 — "waiting on money" with half a million in the bank; "waiting on your hours" with 2,000 hours free
Repro (start_1300 save with capital set to 500,000 so money cannot be the constraint):
  start pwr_leat_and_weir ; start met_safety_lamps_ventilation ; start tex_knitting_frame ; step 1 ; state
  [1301 AD | 490409 den | you:2000 hr | ...]
    met_safety_lamps_ventilation  100% of your hours spent, 491.3 still owed - waiting on money
    pwr_leat_and_weir             100% of your hours spent, 155.9 still owed - waiting on money
    tex_knitting_frame             60% of your hours spent, 0 still owed - waiting on your hours
  "You: alive ..., 2,000 founder-hours free this year"
491.3 owed against 490,410 held, and 2,000 free founder-hours against a project said to
be waiting on my hours. The real constraint is evidently a per-year pacing rule (the
CALENDAR FLOOR - the engine does print "waiting on the calendar" elsewhere, so the
wording exists), but the status line names money and hours instead.
Confidence the reason given is wrong: high.

## FINDING 28 — "this society can field 1321 at most" is not the most
`state full:true` on a stalled project:
  arithmetic_positional  81% of your hours spent, 0 still owed - waiting on nobody to do
  the work: scribe (wants 2500 hours a year; this society can field 1321 at most)
It sat like that for 25 years. But `hire scribe 2` (allowed - the literacy cap is 2.2)
raises `labour scribe` "market can supply" from 1,321 to 5,321, and then
`commission scribe 2500` succeeds and the project unsticks. So "at most, ever" is
"at most until you hire two scribes". Given that arithmetic_positional's own card says
"Highest return on personal hours in the entire tree" and "HOW MUCH RESTS ON THIS:
almost everything", a player who believes the refusal will simply abandon the most
important node in the game. Confidence the wording is wrong: high.

## Corrected: CALENDAR FLOOR is respected
I first thought floors were being beaten (a 2-year floor completing one year after
start in a `step 25`). A clean single-project test shows it is honoured:
  start pwr_leat_and_weir (floor 2 years) at 1300 -> still RUNNING at 1301 ->
  "COMPLETED 1301" reported on the step that ends in 1302. Two calendar years. Fine.

## Corrected: `commission` does not exceed the trade's supply
`commission scribe 2500` succeeding after "market can supply 1,321" looked like a cap
violation; it was not - hiring 2 scribes had raised the pool to 5,321 first, and
`commission scribe 100000` / `5000` are then refused with "the scribes here can spare
2821 more hours this year". The cap holds.
