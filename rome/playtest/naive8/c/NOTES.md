# TOP PROBLEMS

Ordered by severity. Full repros with exact input/output are in the numbered
findings below.

1. **`bribe N` charges N and does nothing above ~100 denarii (F16).** `bribe 100`
   and `bribe 1000000` both move protection 0% -> 32%; the second one leaves you
   with 0 denarii. No warning, no cap, no refund. One command can end a run.

2. **Hiring charges a year's wages twice (F11).** A smith listed at 281 den/yr
   costs 566 den for his first year: `hire` takes a year in advance and the next
   `step` bills the same year again. `fire` refunds nothing, so hire-then-fire
   in one turn destroys the advance for zero work.

3. **The affordability check is skipped for your first project (F8).** With 400
   den and 1,367 credit, `start tx2_watch_case` (17,415 den) is accepted. Start a
   5-denarius project first and the same command is refused, quoting exactly the
   money you do not have. Taking the offer leads to CREDIT EXHAUSTED, two
   insolvencies, reputation 5 -> 0.2 and 1,306 den of interest, with nothing built.

4. **Concurrent games silently share one save file (F26).** Six games started at
   once: five were all assigned `rome_100ad_78.json` and overwrote each other,
   against a banner that promises you can "come back to exactly where you left
   off". The namer also refills any gap, so a save you move or delete is a slot a
   future game will take.

5. **`why` cost breakdowns are not the cost (F17/F6).** "COST: 258 den total (0
   labour + 0 materials + 200 capital, then x1.2 your civ, x1 distance, x1
   scarcity, x1 prices)" - 200 x 1.2 = 240. scientific_method: 200 shown as 230.
   fin_plantation: 10,075 shown as 10,831. The hidden factor (up to 1.29) is not
   constant and is not disclosed; the *total* is what you are charged.

6. **`ventures` and `money` disagree about whether anything is running, and `why`
   overstates income 3x (F1/F2/F7).** Turn one: `money` pays 233.5 den/yr from
   two named ventures; `ventures` says "RUNNING: nothing" and "Only what you are
   RUNNING earns anything"; `why` says those two earn 500 and 200 den/yr against
   the 166.7 and 66.7 actually paid. (The 1/3 rule is explained in the ledger -
   but that explanation disappears when you resume a saved session, F28.)

7. **After a sack, `path`, `start` and the prerequisite check give three
   different answers (F29).** `path` lists lead_chamber as remaining, `start
   lead_chamber` says you already know how and to use `restore`, and downstream
   nodes report it as a missing prerequisite. A player driving off `path` +
   `start` is stuck for good; mine sat at 106 technologies and 760,403 unspent
   denarii from 460 AD to the horizon.

8. **A failure announces a penalty it never charges (F18).** "60% of the work is
   to do again and 80 is gone" - the same screen then shows "0 still owed", and
   the retry completes the next year at no extra cost.

9. **Events take money without naming the amount (F19).** "EVENT 104: fire in the
   insula district" removed 75.1 den (18% of everything I had) with no figure on
   screen and no line in the ledger.

10. **With fog of war OFF, unknown-id errors blame fog of war (F30).** `help fog`
    says "OFF. You can see the whole tree." and `why zzzzzzzz` in the same
    session says "under fog of war I can only suggest things you have heard of",
    so the players who turned fog off get no suggestions at all.

11. **`available` pagination is unordered (F21).** Page 1 runs 6 -> 1,580 den,
    page 2 restarts at 5 den. The cheapest node in the game is item 31.

12. **The arrears rescue text is wrong three ways (F22/F23/F24).** It quotes a
    loss of 46 den/yr when the ledger says 159.5; it recommends wage work, which
    the game answers with "this cost you 50 ... Wage work is for when you have no
    practice to lose"; and it is still printed after the run has ended, when
    every action it suggests is refused.

13. **Wage arithmetic contradicts itself on one screen (F12/F13).** "smith 1, 281
    den/yr each / annual wage bill: 282.9"; with two, "281 den/yr each / 574".
    Two identical hires in the same turn cost 281.2 and 283.0.

14. **Mexica scenario sells horse technology to a society it says has no horses
    (F27).** `horse_collar` (900 den/yr) and `en_horse_gin` are startable on
    arrival in a scenario the menu describes as "no draught animals".

15. **Three different answers to "can I afford this" (F32).** The AFFORD column
    uses cash + half your credit, `start` uses cash + all of it, and the first
    project of a run is not checked at all.

16. Smaller: `help economy` prints the money topic verbatim (F5); "YOU COULD
    HIRE" hides trades you already employ (F14); hiring *increases* the labour
    market's supply (F15); `quote` ignores credit while `start` uses it (F20);
    reputation penalties are announced then silently clamped (F10); a
    money-blocked project reports "waiting on your hours" while 2,000 hours sit
    free (F9); float artefacts in prices (F31); holding capital costs ~1.5%/yr
    with no documentation (F33); several printed sums that do not add up (F34).

17. **Seen once, not reproduced:** after `help money` / `quote nitre 20000` /
    `buy nitre 20000` in a 273 AD session, `money`, `step` and `state` all
    returned "REFUSED: internal error handling that command: TypeError:
    unsupported operand type(s) for +: 'float' and 'str'." 35+ replays of the
    same commands from the same save did not reproduce it, so something in the
    ledger path can be handed a string. Worth chasing in the source.

---
# Playtest notes - "One person, and everything they know" (rome/sim/simulator.py)

Session setup used for most repros (unless stated):

    cd /home/user/test && printf '2\nn\npoor_scholar\nn\n...commands...\n' | python3 rome/sim/simulator.py

(scenario 2 = Rome 100 AD, fog OFF, poor_scholar 400 den, no ageing)

---

## Findings (in discovery order; see TOP PROBLEMS at end/top)

### F1. `ventures` contradicts `money`: you earn 233.5 den/yr from ventures that are "not running"

Repro (turn 1, no commands before):

    money
    ventures

`money` prints:

    Capital: 400 den     Revenue: 233.5 den/yr
      from:
        med_cataract_couching                  166.7
        med_trepanation                        66.7
        (these add up to the revenue above)

`ventures` prints:

    RUNNING
      nothing
    YOU KNOW HOW, AND HAVE NOT OPENED
      nothing
    ... "Only what you are RUNNING earns anything or costs anything."

`state` also prints `RUNNING: nothing`. So the two screens disagree about
whether anything is running, and the help text's promise ("until you do
[open], it earns nothing") is false: I am paid 233.5 den/yr on turn 1.

### F2. `why` reports a revenue 3x larger than the ledger actually pays

    why med_cataract_couching   ->  REVENUE: 500 den/yr    (ledger pays 166.7)
    why med_trepanation         ->  REVENUE: 200 den/yr    (ledger pays  66.7)

Both are paid at exactly 1/3 of the advertised figure, with no explanation
anywhere on either screen. Also both say "THIS SOCIETY ALREADY HAS THIS. You
did not build it and do not maintain it." while still crediting you the money.

### F3. Ledger addition is off: 166.7 + 66.7 = 233.4, printed as 233.5
The line literally says "(these add up to the revenue above)". They do not.

### F4. `ventures` says you have staff; `labour` says you have none

    ventures -> "free to put behind something new: 1 scholars, 1 craftsmen"
    labour   -> "ON YOUR STAFF: nobody ... Total employed: 0"
    why med_cataract_couching -> "STAFF NEEDED: 1 scholars, 0 artisans (you have 1, 0)"

Three screens, three different craftsman/artisan counts (1 craftsmen / 0 / 0).

### F5. `help economy` and `help money` print identical text
`help commands` advertises both `economy` and `money` topics; `help economy`
silently prints the money topic. (Minor.)

### F6. `why` cost lines do not add up

    why scientific_method
    -> COST: 230 den total  (100 labour + 0 materials + 100 capital, then x1 your civ,
                             x1 distance, x1 scarcity, x1 prices)

100 + 0 + 100 = 200, and every multiplier is printed as x1, but the total is 230.
Same shape elsewhere, smaller:

    why hom_toys_dolls -> COST: 75.5 den total (21.8 labour + 3.6 materials + 50 capital)
    21.8 + 3.6 + 50 = 75.4, printed 75.5.

So the breakdown the game shows a player is not the number it charges them.

### F7. Hidden 1/3 (really hours/6000) scaling of practice revenue, never stated

`why med_cataract_couching` says REVENUE: 500 den/yr. The ledger pays 166.7.
Measured by spending founder-hours on wage work:

    work labourer 1000 -> money -> med_cataract_couching 83.3
    work labourer 1500 -> money -> med_cataract_couching 41.7
    work labourer 1900 -> money -> med_cataract_couching  8.3
    work labourer 2000 -> money -> Revenue: 0 den/yr

Revenue = 500 * (founder hours left / 6000). You only ever have 2,000 hours, so
the advertised 500 den/yr is unreachable by a factor of 3 and nothing on any
screen says so. (Built ventures like hom_toys_dolls DO pay the advertised
number, so the rule is not even uniform.)

### F8. **The affordability check is not applied to your first project.**

Fresh game, 400 den in hand, credit limit 1,367:

    start tx2_watch_case      -> "started ... the bill you have taken on: 17,415"
    start fin_plantation      -> "REFUSED: you already owe 17,415 denarii on work in
                                  hand; this would take it to 28,245, and between cash
                                  and credit you can raise 1,767."

The engine clearly knows I can only raise 1,767. It refuses the *second* start on
exactly that ground, but happily accepted a 17,415-denarius commitment as the
first one. Stepping from there:

    step 1  -> Money: -820.1 den, "spent on projects last step: 1,224"
    step 30 -> EVENT 105: CREDIT EXHAUSTED: 1 projects halted, unfinished.
               EVENT 105: INSOLVENCY SETTLED ... (reputation -12)
               EVENT 115: INSOLVENCY SETTLED ... (reputation -12)
               reputation 5 -> 0.20, 1,306 den paid in interest, nothing built.

A new player has no way to know the first `start` is unchecked; the game
volunteers the check only after it is too late.

### F9. Project status line says "waiting on your hours" when it is waiting on money

Same session, 101 AD with 2,000 founder-hours free:

    RUNNING (1):
      tx2_watch_case   7% of your hours spent, 16,191 still owed - waiting on your hours
          this year's instalment is more than the purse will bear

Two lines that contradict each other. Also "7% of your hours spent" is not hours
at all - 1,224/17,415 = 7.03% is the fraction of the *bill* paid; the project
only needs 80 founder-hours out of the 2,000 I have free.

### F10. Reputation penalties are silently clamped
Two INSOLVENCY events each announce "reputation -12" against a reputation of
4.9. Reputation ends at 0.20, so the second -12 did nothing at all. The number
announced is not the number applied.

### F11. **Hiring charges a full year's wage twice for one year of work**

Baseline, no staff:

    step 1 ; money  ->  Capital: 403.5 den   (wages 0, net +3.5)

Same start, hire one smith (listed at 281 den/yr):

    hire smith 1   -> "annual wage bill: 282.9 / capital: 118.8"   (400 - 281.2 paid in advance)
    step 1 ; money -> Capital: -162.4 den    (wages 272 charged for the year)

One year of one smith at 281 den/yr should cost 281. It cost
403.5 - (-162.4) = 565.9, i.e. roughly two years' wages. The advance payment
taken by `hire` is never credited against the year that follows.

Firing does not give it back either:

    hire smith 2 -> capital: -162.5 ;  fire smith 2 -> "annual wage bill: 0", capital still -162.5

so hire-then-fire in the same turn destroys 562 den for zero work, with no warning.

### F12. Wage arithmetic disagrees with itself on the same screen

    hire smith 1 ; labour
      ON YOUR STAFF:  smith  1   281 den/yr each
      Total employed: 1     annual wage bill: 282.9 den        (1 x 281 = 281)

    hire smith 1 (again) ; labour
      smith  2   281 den/yr each
      Total employed: 2     annual wage bill: 574 den          (2 x 281 = 562)

and the cash actually taken differs between two identical hires in the same
turn: the first smith cost 281.2, the second cost 283.0.

### F13. People come in fractions

    hire smith 1 ; step 1 ; state
      EMPLOY: 0.96 people, 272 den/yr in wages
        smith            0.96
      labour -> "smith  0.96  281 den/yr each   Total employed: 0.96"

You paid for one person in advance and after one year own 0.96 of them.
(0.96 x 281 = 269.8, and the bill is printed as 272, so even the fraction does
not multiply out.)

### F14. "YOU COULD HIRE" hides trades you already employ
After `hire smith 1`, `labour` no longer lists smith under "YOU COULD HIRE",
which reads as "no more smiths available". `hire smith 1` still works. The list
is really "trades you do not yet employ", which is not what it says.

### F15. Hiring increases the labour market's supply
    labour trade smith            -> "you employ: 0   market can supply: 22,500 hours"
    hire smith 1 ; labour trade smith -> "you employ: 1   market can supply: 24,500 hours"
    (and 26,500 after a second hire)
Taking smiths out of the market makes more smith-hours available.

### F16. **`bribe N` charges you N and gives the same result for N=100 as for N=1,000,000**

Start `absurd` (1,000,000 den), Rome, fog off:

    bribe 10      -> protection 0.00 -> 0.06
    bribe 100     -> protection 0.00 -> 0.32
    bribe 1000    -> protection 0.00 -> 0.32
    bribe 10000   -> protection 0.00 -> 0.32
    bribe 100000  -> protection 0.00 -> 0.32
    bribe 1000000 -> protection 0.00 -> 0.32   and:  money -> Capital: 0 den

(each from the same fresh save). The effect saturates at ~100 denarii, but the
command takes every denarius you name, silently, with no warning and no refund.
One mistyped `bribe` wipes out the entire game. A following `bribe 1` is then
refused with "you have 0 denarii".

Related: `help protection` says protection "caps at 92%", but the second bribe
is refused with "you are already as protected as money can make you here" at 32%.

### F17. `why` cost breakdowns disagree with the totals by up to 29%

The line is written as an equation and is not one. Cleanest cases:

    why sc2_notation_positional
      COST: 258 den total  (0 labour + 0 materials + 200 capital, then x1.2 your civ,
                            x1 distance, x1 scarcity, x1 prices)
      -> 200 x 1.2 = 240, shown 258   (a hidden extra x1.075)

    why scientific_method
      COST: 230 den total  (100 + 0 + 100, then x1 ...)   -> 200, shown 230  (x1.15)

    why mat_papyrus
      COST: 402.5 den total (12 + 0 + 300, then x1.2 ...) -> 374.4, shown 402.5

    why fin_plantation
      COST: 10,831 den total (75 + 0 + 10,000, then x1 ...) -> 10,075, shown 10,831

and yet others are exact (units_standards 104+90+250 = 444 x1 = 444;
horse_collar 261+173.6+400 = 834.6 x0.85 = 709.4). So the hidden factor is
neither constant nor disclosed. The charged amount is the *total*, so it is the
breakdown that is wrong.

### F18. A failure announces a penalty it does not charge

    start sc2_notation_positional ; step 1
      EVENT 100: FAILED at Positional notation and place value: it did not work.
                 60% of the work is to do again and 80 is gone. Attempt 2.
      RUNNING (1): sc2_notation_positional  100% of your hours spent, 0 still owed
                                            - waiting on the calendar
    step 1
      COMPLETED 101: Positional notation and place value

"60% of the work is to do again" but 0 is still owed and the next year finishes
it at no further cost (money 65.5 -> 74.1, which is just the year's net income).
Also the project is "waiting on the calendar" although `why` reports
"CALENDAR FLOOR: 0 years".

### F19. Events take money without saying how much

    step 1 (x5 from a fresh game, nothing built)
      EVENT 104: fire in the insula district, where the tenements stand six storeys in wood
      money before: Capital 413.8, Net/yr +3.3  -> money after: Capital 342.0

75.1 denarii vanished (18% of everything I had). The event text names no cost and
the ledger has no line for it.

### F20. `quote` ignores credit, `start` uses it
    quote mine coal 500 -> "you have: 284.8 / you can afford about: 31.6" (tonnes)
Cash only. `start` and the `start` refusal message both use cash+credit
("between cash and credit you can raise 1,767").

### F21. `available` pagination is not ordered - the cheapest item is on page 2

    available afford 1580             -> "1-30", first row tx2_bleaching_sun 6 den,
                                         ascending to identity_cover 1,580
    available afford 1580 offset 30   -> "31-60", first row hom_eraser_breadcrumb 5 den,
                                         ascending again to sea_lead_sheathing 1,445

Each page is sorted internally but the pages are not a sorted sequence, so
"the cheapest thing I can start" is not on page 1 and a player paging through
sees costs go 6...1,580 then 5...1,445. (hom_eraser_breadcrumb at 5 den is the
cheapest node in the game and appears at position 31.)

### F22. The arrears warning quotes a loss that is not the loss

    step 200 ; state ; money
      !! YOU HAVE BEEN IN ARREARS 63 YEARS AND YOU LOSE 46 DENARII A YEAR ...
      LEDGER ... Net/yr: -159.5

46 vs 159.5. Same at the horizon: "YOU LOSE 66 DENARII A YEAR" against Net/yr -200.4.

### F23. The escape advice the game gives is advice the game itself calls a mistake

The arrears banner says:

    it is escapable, and none of these need anybody to lend you a denarius
     - work for wages: you have 2000 of your own hours left this year ...

Taking that advice:

    work labourer 2000
      earned: 125.1
      but: you earned 125, and the practice those hours were running was worth 175
           a year - so this cost you 50. Wage work is for when you have no practice to lose.

The recommendation and the response to following it are contradictory, and the
recommendation is the losing move.

### F24. The end-of-run screen still tells you to do things it will refuse

At 600 AD ("THE RUN HAS ENDED") `state` still prints the arrears banner with
"it is escapable ... work for wages: you have 2000 of your own hours left this
year". Every one of those is refused:

    work labourer 2000 -> REFUSED: the run has ended ...
    start hom_toys_dolls -> REFUSED: ... nothing more can be started
    hire smith 1 -> REFUSED: the run has ended ...

### F25. `open <bad id>` gives no "did you mean", `why <bad id>` does
    why nonexistent_thing -> REFUSED: unknown node 'nonexistent_thing'. did you mean: ...
    open nonexistent      -> REFUSED: no such node

### F26. **Concurrent games silently share one save file and overwrite each other**

The auto-chosen session name is the lowest free `rome_100ad_N.json`, chosen
without any locking or exclusive create:

    cd /home/user/test
    for i in 1 2 3 4 5 6; do
      ( printf '2\nn\npoor_scholar\nn\nstep 3\nquit\n' | python3 rome/sim/simulator.py | grep '^Saved to' ) &
    done; wait

    Saved to rome_100ad_77.json.
    Saved to rome_100ad_78.json.
    Saved to rome_100ad_78.json.
    Saved to rome_100ad_78.json.
    Saved to rome_100ad_78.json.
    Saved to rome_100ad_78.json.

Five different games were all told to "come back with --session rome_100ad_78.json";
four of them are gone. The banner promises "Progress is written to this file
after every command, so you can stop any time ... and come back to exactly where
you left off", which is false in this case.

It also fills gaps, so any save you move or delete leaves a slot a later game
takes over:

    rm rome_100ad_40.json ; (new game) -> "Saved to rome_100ad_40.json"

I also observed an existing save being clobbered in normal sequential use:
rome_100ad_7.json was 18,128 bytes at 15:29 and 18,177 bytes at 15:47 after a
new game claimed that name.

### F27. Mexica scenario sells horse-powered technology to a society it says has no horses

Scenario 5 is described on the menu as "no draught animals, no iron, no wheel in
practical use". On arrival:

    5 / n / poor_scholar / n
    available find horse
      en_horse_gin    Horse gin        63.2  ... EARNS/YR 52.7
      lnd_hobby_horse Hobby horse     434.8
      horse_collar    Rigid padded horse collar  863.1 ... EARNS/YR 900

`horse_collar` is startable on arrival, with no prerequisite that gets you a
horse, in the Valley of Mexico in 1500. (`why horse_collar` there still
describes it as a collar for a draught horse.)

### F28. The one explanation of the 1/3 practice rule does not survive a resume

A fresh in-process game prints it under the ledger:

    money -> "YOUR PRACTICE: med_cataract_couching, med_trepanation are your own
              practice, and they pay about a third of what the tree quotes ..."

The same session resumed with `play --session FILE` prints the ledger without
that block, so a player who takes the game's own advice to stop and come back
never sees the reason their income is a third of the quoted number, and `why`
still says "REVENUE: 500 den/yr".

### F29. `path` and `start` disagree about technologies lost in a sack

Late run, after "EVENT 460: KNOWLEDGE LOST: 36 technologies forgotten":

    path point_contact_transistor -> remaining: ... lead_chamber, high_temp_furnace ...
    start lead_chamber -> REFUSED: you built this once and let it go; you already
                          know how, so restoring it is cheaper than starting over:
                          restore lead_chamber for about N denarii
    start (anything downstream) -> REFUSED: missing prerequisites: high_temp_furnace

So `path` says it is missing, `start` says you already have it, and the
downstream node says it is a missing prerequisite. The only way forward is
`restore`, which `path` never mentions. Following `path` + `start` mechanically
leaves the run permanently stuck (mine sat at 106 technologies and 760,403
denarii from 460 AD to the 600 AD horizon).

### F30. With fog of war OFF, an unknown-id error still blames fog of war

Same session, one command apart:

    help fog       -> "fog of war: OFF. You can see the whole tree."
    why zzzzzzzz   -> "REFUSED: unknown node 'zzzzzzzz'. did you mean: no idea,
                       and under fog of war I can only suggest things you have
                       heard of"

Reproducible from a fresh game (`2 / n / poor_scholar / n`), so the suggester is
reading the wrong flag and gives no suggestions to exactly the players who
turned fog off in order to see everything.

### F31. Float artefacts leak into player-facing prices
    hire smith 999999999999999999999
    -> "REFUSED: hiring 1e+21 smiths costs 281250000000000012058624 denarii and you have 400"

### F32. `available afford N` uses a different affordability rule than `start`
The subject summary's AFFORD column and `available afford` use cash + half the
credit line (the hint offers "available afford 1,083" when cash is 400 and the
credit limit 1,367). `start` uses cash + the whole credit line (1,767), and the
first project of a run is not checked at all (F8). Three different answers to
"can I afford this".

### F33. Holding money costs ~1.5% a year and nothing says so
    absurd start (1,000,000 den), 100 AD, nothing built, nobody hired:
      money -> living and appearances ~14,990 ;  Net/yr: -14,990
    poor_scholar (400 den): living and appearances 230

"living and appearances" scales with capital, so an idle million bleeds ~15,000
a year. `help money` and `help economy` never mention it.

### F34. Numbers that do not reconcile, collected
- `money`: "med_cataract_couching 166.7 + med_trepanation 66.7 ... (these add up
  to the revenue above)" against "Revenue: 233.5" (=233.4).
- `state` "net -70.8 den/yr (after 75.5 den into projects)" against `money`
  "Net/yr: 4.6" (4.6 - 75.5 = -70.9).
- `labour` "smith 1  281 den/yr each ... annual wage bill: 282.9"; with two,
  "281 den/yr each ... 574" (=562).
- `work labourer 2000`: "you earned 128, and the practice ... was worth 234 ...
  so this cost you 105" (234 - 128 = 106).
- ledger after auto-open: 306.7+170.4+153.4+68.2 = 698.7 printed as 698.4.
