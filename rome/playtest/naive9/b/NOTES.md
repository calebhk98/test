# Playtest notes — "ONE PERSON, AND EVERYTHING THEY KNOW"
naive9/b. Three full runs to the 600 AD horizon, all losses (102/146, 81/146, 135/146 nodes).
No source, docs or tests read; everything below comes from what the program printed.

---

## TOP PROBLEMS
In the order they hurt the experience.

1. **The sacking hedge only works if `corpus_written` is OPENED, and nothing says so.**
   I finished `corpus_written` and `risk` went on printing "hedge: none yet" for 90 game-years
   while sackings took back 24 technologies I had already built. `open corpus_written` fixed it
   instantly ("hedge: corpus_written", sack loss 80%→45%). This one hidden rule was the
   difference between 81/146 nodes and 135/146 in otherwise identical runs. Worse, `ventures`
   lists corpus_written among a dozen *other* zero-revenue things that cost upkeep and do
   nothing when opened, so the one you must open looks exactly like the ones you must not.

2. **Sackings destroy built technologies and never tell you which ones.** "a site is sacked -
   304,663 taken, 32.4 of your people gone, 5 projects back to the beginning" — but the
   technologies you lost are invisible. You find out fifty years later when `start
   interchangeable_parts` says "missing prerequisites: master_screw" for a thing you finished
   two centuries ago, and then rebuild a five-node chain one refusal at a time. This is what
   killed run A. Print what was lost, or add a `lost` command.

3. **The open-while-broke catch-22.** The engine lends you 1,186 denarii to *build*
   horse_collar and then refuses to lend you 150 to *switch it on*:
   "REFUSED: opening it costs 150 denarii in stock and premises and you have -1,186" — while
   horse_collar would earn 900/yr and dig me out. I idled 14 game-years to save 150 denarii.
   And going negative at all silently freezes every project ("in arrears: after fixed costs
   there is nothing left to draw on"), which is only ever explained at 92% of the credit limit.

4. **`policy auto_mine on` quietly ate 75% of my income, and there is no way to see or list
   your mines.** `money` showed one aggregate line, "mines standing 353,039", against a total
   revenue of 467,227. I had never typed `buy mine`. There is no command that enumerates them;
   I found them by guessing materials until `close iron` answered "You stop paying 258536 a
   year." Net income went from −61,884/yr to +291,156/yr in two commands.

5. **`auto_open` is off by default, so everything you build earns nothing until you notice.**
   Twenty concerns, twenty-five game-years, income unchanged. One `policy auto_open on` took
   revenue from 90/yr to 1,863/yr in a single step. Combined with (3), a new player's first
   hour is mostly the game quietly not working.

6. **"'labour' says what raises it" is false, and it hides the most important building.**
   Household places gate everything, and both `state` and `labour` point at `labour`, which
   prints the *how-to-hire* text under a "to make room:" heading and never mentions the answer
   (`workshop_first`, which took me from 6.0 places to 14.8). I sat at the 6-place ceiling for
   ~15 years watching concerns close.

7. **`auto_hire` fills every household place with the cheapest trade and thereby blocks the
   tree.** It hires artisans until the household is exactly full; then you cannot train the
   machinists/chemists/opticians the next tier requires, and `path` simply stops advancing
   with no explanation. Twice I had to `fire artisan 20` before I could `train machinist 2`.
   Related: a project started with zero of a required trade is accepted, then killed three
   years later — "HALTED sulfuric_retort: there is nobody here who can do this work (chemist).
   What you spent is lost" — while `labour` was simultaneously saying "YOU COULD HIRE: ...
   chemist ... MUST BE TAUGHT: none". `start` should refuse or warn up front.

8. **`why <goal>` is the best tool in the game and nothing points you at it.** Typed on a whim
   in year 477, `why point_contact_transistor` printed the full prerequisite list under fog of
   war, and `why` on each of those printed theirs. That is the whole roadmap. I had spent 380
   game-years guessing from "MOST RESTS ON THESE". Put it in the opening four commands.

9. **Fog off is a much better game than fog on, and the menu undersells it.** "you can see the
   whole tree" understates `path <goal>`, which prints the 138-node route in build order, and
   the three lines `why` adds with fog off: "FULL CHAIN BEHIND IT: 95 nodes, 34,850 of your
   hours, 3,751,306 cash, **102.2-year serial floor**" and "TOTAL DOWNSTREAM: 144 thing(s)
   depend on this -- INCLUDING THE GOAL". The serial-floor number is what decides whether a run
   is winnable; a fog-on player never sees anything like it.

10. **The final gate is a staffing wall with no lever.** `power_grid` "needs 200 trained
    craftsmen"; my household ceiling was 166.9 places *in total*, and none of the three
    remedies the refusal offers works (`commission` buys hours not craftsmen — I tested it;
    `buy slaves` is refused for lack of places; `freedman_staff` was already built). The ceiling
    does drift upward on its own but nothing says what moves it, so the single requirement that
    decides the run is the one you cannot plan against.

11. **Rome leaking into the other civilisations.** Playing the Later Han Empire, `why
    corpus_written` reads "everything you know, in plain quantitative **Greek and Latin**", and
    the top of my tech list offered `patron_senatorial` ("Senatorial patronage") and
    `civ_arch_roman` ("Roman masonry arch"). `identity_cover` handles this beautifully — it
    names the local equivalent for each society — which makes the rest look unfinished.
    Also seen in player-facing text: "this needs **unknown_source** and you have none of the
    things that would serve".

12. **Smaller but constant friction:** `available`'s default view is "CHEAPEST SIX RIGHT NOW",
    which is always six 6-denarius textile nodes out of 207 items; there is no way to sort or
    filter by revenue (`available sort earns` → "nothing in 'sort earns'"); `policy X on`
    reprints the entire 20-line policy manual every time; `hire chemist 6` when 5.9 are
    available refuses entirely instead of hiring 5; the `NEEDS` column in `ventures` rounds
    "0.2 craftsmen" up to "1 cr" for six concerns at once, so it reads as six people; and every
    bare launch drops another 18KB `rome_100ad_N.json` in the repository root.

---
## FULL PLAY LOG AND DETAILED NOTES (in the order I hit them)

### Startup
Ran `python3 rome/sim/simulator.py`. Title screen offers 5 settings (Han 100, Rome 100,
Viking 900, England 1300, Mexica 1500) with population / state capacity / price multipliers.
Nice framing text: "Knowing how a thing works is free. Building it is not."

- Empty input prints `-- a number from 1 to 5.` then re-prompts. Fine.

### Game A: Rome 100 AD, fog ON, poor_scholar, immortal

Goal revealed by `help`: "Build point-contact transistor, before the horizon at 600."
Nice: the goal is stated plainly and `state` repeats it ("Aiming at: Point-contact transistor").

**Good things**
- Every run drops you straight into a readable `state` block; the status bar
  `[100 AD | 400 den | you:2000 hr | sch 0 art 0 | rep 5] >` is genuinely useful.
- `why <id>` is excellent: cost broken into labour/materials/capital with the multipliers
  spelled out (`x0.85 your civ, x1 distance...`), hours, calendar floor, risk, staff, upkeep, revenue.
- The error when I resumed a nonexistent save was perfect: "there is no save at '...', and no --civ
  given, so I do not know what game you meant."
- `help protection` volunteering that a previous tester tried to bribe their way to 92% and
  couldn't is a lovely touch.

**Confusions / problems**
1. **`available` default ordering is near-useless.** With 207 things startable, the default
   "CHEAPEST SIX RIGHT NOW" is six textile micro-nodes at 6 den each
   (`tx2_bleaching_sun`, `tx2_retting`, `tx2_shed`...). Nothing about them matters. The
   "MOST RESTS ON THESE" table right below it is the one I actually used. Cheapest-first is
   the wrong default when 54 of 207 items are textile filler.
2. **`available sort earns` fails** with "nothing in 'sort earns'". There is no way to sort or
   filter by revenue, which is the single number a cash-starved founder cares about. I had to
   read `available subject finance` and eyeball the EARNS/YR column by hand.
3. **`policy <x> on` prints the entire 20-line policy manual every single time.** Four policy
   changes in a row printed ~90 lines of identical boilerplate. Just print the change.
4. **auto_train nearly killed the run with no warning.** I switched `auto_train on`; two years
   later: "you begin teaching the first engineers this world has ever had" and my wage bill went
   from 0 to **1,562 den/yr** against a revenue of 704 den/yr. Nothing warned me the trained
   staff would be permanent salaried employees, or asked. I only found it by reading `money`
   and seeing `wages 1,562`. Expected: a policy that spends >2x my annual revenue should say so.
5. **Debt is a stealth death spiral and the message is buried.** Once capital went negative,
   every project printed "in arrears: after fixed costs there is nothing left to draw on, so
   the hours offered this year did almost nothing". So going into debt doesn't just cost
   interest, it *stops all progress*. Nothing before that point told me borrowing would freeze
   my projects - and the game cheerfully advertises "You may spend past what you have" and
   quotes me a credit limit of 4,119 as if it were usable working capital. It is not.
6. **Inconsistent: auto_open refused, manual open worked.** With capital -1,445 the log said
   "fin_mortgage would earn 38 a year against 0 of upkeep and is still shut: you have no money
   to open it with". I typed `open fin_mortgage` and it opened fine, for 8.6 den, from the same
   negative balance. Two rules for the same act.
7. Scandal appeared at 3.9 with no explanation of which of my four finance projects caused it
   (seigniorage? the cartel?). `state` shows the number but nothing says where it came from.

### The debt trap, confirmed (and the catch-22 that goes with it)
At 131 AD the game finally said what had been happening for 25 years:
"CLOSE TO THE LIMIT: you owe 1,186 of the 1,285 anyone here will advance you (92%).
Past it every project in hand is halted unfinished and nobody funds new work for some years."
That is a good message - but it arrives at 92%, and it explains a rule that silently destroyed
three projects (fin_pawnshop at 61% done, scientific_method, units_standards) during an earlier
`step 20`, with *no* message at all at the time. I only noticed because `state` said
"RUNNING: nothing" and my money was gone.

8. **The open-while-broke catch-22 is the single most frustrating thing in the game.** I finished
   `horse_collar`. It earns 900/yr against 150 upkeep. The game refuses:
   "REFUSED: opening it costs 150 denarii in stock and premises and you have -1,186".
   So the engine will happily lend me 1,186 denarii to *build* a thing, then refuse to lend me
   150 to *switch it on* and dig myself out. I sat idle for 14 game-years waiting to afford
   150 den. Either let borrowing cover opening, or don't let me borrow to build in the first place.

9. **`start scientific_method` once answered "REFUSED: you have never heard of any such thing"**
   in 126 AD - for a technology that `available` had listed as startable since year 100 and that
   I had already had in progress. Three game-years later the identical command worked. Never
   reproduced it deliberately, but it read as a plain bug.

10. **"'labour' says what raises it" is false, and it hid the most important building in the game.**
    `state` and `labour` both say household places are "what you can feed, house and oversee.
    'labour' says what raises it". `labour` says:
      "HOUSEHOLD PLACES: 3.6 of 6 used, room for 2.4 more
       to make room: To get more artisans: hire smith 3 or any trade in labour; or commission..."
    That is the *how to hire* text pasted under a *how to make room* heading. It never mentions
    the answer, which is `workshop_first` ("First workshop and laboratory", 5,757 den) - that
    took me from 6.0 places to 14.8. I was stuck at the 6-place ceiling for ~15 game years,
    watching concerns close for lack of a supervisor, with the game pointing me at a help text
    that answered a different question.

11. **Concerns silently close from staff attrition and you have to keep re-opening them.**
    "nobody left to keep an eye on 1 concern, so tr_block_tackle closed". Attrition is 3.5%/yr,
    so a 5-artisan staff drifts below what 20 concerns need and things switch off one at a time,
    each costing money to reopen. `policy auto_hire on` fixes it, but auto_hire is off by default
    and nothing suggests it when the first concern closes.

12. **`ventures` invites you to open things that do nothing.** It lists, under
    "YOU KNOW HOW, AND HAVE NOT OPENED": `identity_cover  0 earns  200 costs  237 to open`,
    same for `scientific_method` and `units_standards`. I opened all three to see whether their
    protection/method effects needed to be "running". Protection stayed at exactly 25% and I was
    down 330 den/yr for nothing. Things with no revenue and no running effect should not be
    offered as openable.

13. **The `NEEDS` column in `ventures` is rounded to whole people and misleads.** It shows
    "1 cr" for six different concerns while the actual requirement (per the event text) is
    "0.2 craftsmen". Reading `ventures` I thought I needed 6 craftsmen; I needed about 1.2.

14. **Duplicate-looking tech nodes.** I built `arithmetic_positional`, described as "Decimal
    positional notation, zero, negative numbers, decimal fractions". The tree then still offers
    `sc2_notation_zero` ("Zero as a number", 5 years), `sc2_notation_negative` ("Negative numbers",
    8 years), `sc2_notation_decimal_fraction`, `sc2_notation_positional`. It looks like the same
    knowledge sold to me twice, and I have no way under fog to tell whether they matter.

### Game A ending (Rome, fog on, poor scholar, immortal)
```
  the horizon at 600 AD is reached. You built 132 things of your own and did
  not reach point-contact transistor.
  THE ROAD TO POINT_CONTACT_TRANSISTOR
    146 nodes in all; you had 102 of them and 44 were still to build
    the next steps would have been: charcoal_industrial, gp_laminated_core,
    gp_glass_metal_seal, mirror_amalgam, blast_furnace, mercury_supply, ...
```
The ending screen is genuinely good - "146 nodes in all; you had 102" is exactly the number
I wanted all game. **But look at that "next steps" list: I had built charcoal_industrial,
blast_furnace, mercury_supply and gp_glass_metal_seal - sackings destroyed them.**

15. **`why <goal>` is the best tool in the game and nothing tells you it exists.** Late in the run
    I idly typed `why point_contact_transistor` and got the complete prerequisite list
    ("missing prerequisites: galena_detector, gp_whisker_forming, prc_lapping_plate,
    quantum_solidstate_theory, single_crystal, vacuum_tube") *under fog of war*. That is a
    roadmap, and it works recursively - `why` on each prerequisite gives its prerequisites.
    I spent 180 game-years reading "MOST RESTS ON THESE" and guessing, when three `why` calls
    would have given me the spine of the tree. The tutorial line lists `why <name>` as
    "what a thing is for and what it costs"; it never hints that you can `why` the goal.

16. **Sacking losses are invisible. You find out by tripping over them.** Events say
    "a site is sacked - 304,663 taken, 32.4 of your people gone, 5 projects back to the
    beginning" but never *which technologies you lost*. I discovered the losses only when
    `start interchangeable_parts` answered "missing prerequisites: master_screw" for a thing
    I had finished 200 years earlier. I then had to re-derive and rebuild a chain of five
    nodes (refractory_fireclay -> cementation_steel -> master_screw -> prc_dividing_head ->
    interchangeable_parts), one at a time, each discovered by another refusal. Late game this
    consumed about 80 years and is why I lost. A "you lost the following: ..." line, or a
    `lost` command, would turn a frustrating guessing game into a real setback.

17. **`policy auto_mine on` quietly ate 75% of my income and there is no way to see it.**
    At 366 AD my ledger read:
      `Revenue: 467,227 den/yr ... mines standing 353,039 ... Net/yr: -61,884`
    I had never typed `buy mine`. auto_mine had sunk workings on its own. There is no command
    that lists your mines - `help commands` has `close <material>` but nothing to enumerate
    them, and `money` shows only the single aggregate line. I found them by typing
    `close coal`, `close iron`, `close copper`... until the refusals stopped:
      "closed: the iron workings are closed. You stop paying 258536 a year."
    Net went from -61,884/yr to +291,156/yr in one command. That is enormous, invisible, and
    caused by a policy switch whose description is a harmless-sounding "sink a mine when a
    mineral is holding work up".

18. **"what the market will not absorb  -144,368"** appeared as a line in `money` with no
    explanation anywhere in `help money` or `help economy`. A negative revenue row worth a
    third of my income deserves a sentence.

19. **A halted project blames the society when the real cause is my full household.**
    "HALTED sulfuric_retort: there is nobody here who can do this work (chemist). What you
    spent is lost" - while `labour` simultaneously said "YOU COULD HIRE: artisan, carpenter,
    **chemist**, ... MUST BE TAUGHT: none". The truth was that auto_hire had packed all 89
    household places with artisans so there was no room for a chemist. This cost me the
    project twice (about 12,000 den and 6 years) before I worked it out. `start` should refuse
    or warn up front when the required trade is at zero, instead of accepting the project and
    killing it three years later.

20. **auto_hire fills every household place with the cheapest trade.** Once on, it hires
    artisans until the household is exactly full, which then blocks hiring the chemists,
    engineers and machinists that projects actually need. I had to `fire artisan 20` before I
    could hire five engineers. The policy has no notion of what my running projects require.

21. **Trade caps are announced only on refusal, and only one at a time.**
    "this society's literacy will not supply more than 5.9 chemists in total, ever, at any
    price ... Raise literacy_general or literacy_elite -- printing, schools and libraries do".
    I then built `school_founded` AND `printing_press` (which the event log confirmed
    "changes the society: literacy_elite, literacy_general") and the cap was still exactly 5.9
    chemists. Either the cap does move and far too slowly to notice, or the advice is wrong;
    from inside the game it looks wrong.
    `labour` should show, for every trade, "you have N, this society can supply M".

22. Batch/ordering friction: `hire chemist 6` when only 5.9 are available refuses **entirely**
    rather than hiring what it can. Same for `hire artisan 3` with 2.4 places
    ("2 is the most whole people you can take" - so hire 2, then).

### Game B: Han China 100, fog OFF, poor scholar
Result: ran out of horizon; 81 of 146 nodes.

23. **Fog off is a completely different (and much better) game, and the menu undersells it.**
    The fog prompt says only "With it off you can see the whole tree and plan a route through
    it". What it actually gives you is `path <goal>`, which prints the entire 138-node route
    **in build order**. That is the difference between playing and guessing. With fog on,
    `path` answers "not available under fog of war" and the game's own advice
    ("MOST RESTS ON THESE") walked me into dead ends for 300 years. I would tell a new player
    to turn fog off; the menu makes it sound like a minor spoiler toggle.

24. **`auto_open` is OFF by default, and with it off nothing you build earns anything.**
    In game B I built ~20 revenue concerns over 25 years and my income never moved. `ventures`
    eventually showed all of them sitting in "YOU KNOW HOW, AND HAVE NOT OPENED", each costing
    2-40 to switch on. One `policy auto_open on` took revenue from 90/yr to 1,863/yr in a
    single step. The tutorial mentions `open`, but a default where built things silently
    produce nothing is the single easiest way for a new player to conclude the game is broken.

25. **Rome-specific text and content leaking into the Han game.**
    - `why corpus_written` in the LATER HAN EMPIRE: "Write the corpus: everything you know,
      in plain quantitative **Greek and Latin**".
    - The Han tree offered me `patron_senatorial` ("Senatorial patronage") and
      `civ_arch_roman` ("Roman masonry arch") as top "MOST RESTS ON THESE" items, and
      `citizenship` ("Legal standing: a status the courts will hear") behaves like Roman
      citizenship. `identity_cover` at least handles this properly - its text explicitly names
      the local equivalent for each society - which makes the others look like oversights.
26. **A placeholder id in player-facing text**:
    "REFUSED: this needs **unknown_source** and you have none of the things that would serve:
     any of dynamo would do". "unknown_source" is not a thing a player can act on.

### Game C: Han China, fog off, absurd wealth - the lessons-applied run
Result: 135 of 146 nodes, still short. Closest run.

27. **THE BIG ONE: the sacking hedge only counts if `corpus_written` is OPENED, not built.**
    In game B I finished `corpus_written` at 242 AD. `risk` continued to say
    "hedge: none yet" for the next 90 years while three separate sackings took back 24 nodes
    I had already built. In game C I finally tried `open corpus_written`:
      `opened: corpus_written open: it earns 0 a year and costs 600 a year to run`
      `risk` -> `hedge: corpus_written` (sack loss 80% -> 45%, fraction 40% -> 22%)
    Nothing anywhere says the hedge has to be running. Worse, this directly contradicts
    problem #12 above: `ventures` lists corpus_written among the zero-revenue things that look
    pointless to open. The one zero-revenue concern that absolutely must be opened is
    indistinguishable from the dozen that must not be.
    With the hedge on from 313 AD, game C went from 61 nodes remaining to 16 in 66 years -
    roughly four times the rate of the unhedged run.

28. **`why <id>` with fog OFF prints three lines that ought to exist under fog too, and they
    are the best UI in the game**:
      `FULL CHAIN BEHIND IT: 95 nodes, 34,850 of your hours, 3,751,306 cash, 102.2-year serial floor`
      `DIRECTLY UNLOCKS: ...`
      `TOTAL DOWNSTREAM: 144 thing(s) depend on this -- INCLUDING THE GOAL`
    "102.2-year serial floor" is the number that decides whether a run is winnable. I would
    have planned entirely differently had I seen it in year 100.

29. **The final gate is a staffing wall with no lever.** `power_grid` (which 144 things
    including the goal depend on) "needs 200 trained craftsmen"; my household ceiling at that
    point was 166.9 places *in total*, so 200 craftsmen was arithmetically impossible, and the
    refusal's own suggestions do not solve it: `commission` buys hours, not standing
    craftsmen (I bought 100 hours of a smith and the count did not move), `buy slaves` is
    refused for lack of household places, and `freedman_staff` was already built. The ceiling
    does keep creeping up on its own (149.5 -> 152 -> 166.9 -> eventually 211 people by 600 AD)
    but nothing in the game tells you what makes it move or how fast, so you cannot plan
    around the one requirement that decides the run.

30. **Nothing stops you starting 146 projects at once, and doing so starves all of them.**
    Founder-hours are shared; when I had 146 running, `corpus_written` sat at "35% of your
    hours spent" for a decade. `state` does report "waiting on your hours", which is good, but
    there is no warning at `start` time and no "you are spread across N projects" summary.

31. **Spend-rate caps only appear once you are stuck in one.**
    "waiting on the pace it can absorb money: at most 7,594 a year goes into this
     (167,422 still owed, about 23 more years at that rate). Money in hand cannot buy it down
     faster". Excellent sentence - but `why steam_high_pressure` before I started it showed
     only "COST: ... CALENDAR FLOOR: 12 years", not the absorption rate. With 39 million in
     the bank and 27 years on the clock, that hidden cap was the whole game.

### Small things
32. `state` says "Aiming at: Point-contact transistor" with fog on and "Goal:
    point_contact_transistor" (raw id) with fog off. The pretty name is nicer; use it in both.
33. Every run drops a new ~18KB `rome_100ad_N.json` in the repository root
    (I generated rome_100ad_4 through _17 just poking at the menus). A bare
    `python3 rome/sim/simulator.py` should probably save somewhere less public, or reuse a slot.
34. `available sort earns` / any sort or filter by revenue does not exist; the reply is
    "nothing in 'sort earns'" as though I had searched for a technology called that.
35. `policy X on` reprints the entire policy manual (~20 lines) on every single call.
36. Nice: the failure texts are excellent - "FAILED at Crucible steel: it did not work.
    40% of the hours are to do again (240 of your own) and 8,155 is gone. Attempt 2."
    tells you exactly what it cost. Same for the debasement line:
    "the coin is worth 94% less than it was ... what debases is the money in your chest, and
    this year it took 31,891 denarii".
37. Nice: `risk` reads like a good history book and still contains the numbers. The Diocletian
    entry explaining that hereditary collegia, not the persecutions, are why "how much trade
    is honoured" falls, is the kind of thing that makes you trust the model.
38. Nice: "you now have 1 deputy directing work in your name: your year is 3,930 hours instead
    of 2,000. They came with the institutions you built" - a reward that arrives as a sentence
    rather than a stat change. More of this.
39. Nice: the ending screen's "146 nodes in all; you had 102 of them" is the perfect summary,
    and "the next steps would have been: ..." makes you want to play again immediately.
