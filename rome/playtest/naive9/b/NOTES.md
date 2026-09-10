# Playtest notes — "ONE PERSON, AND EVERYTHING THEY KNOW"
(naive9/b — first-time player, no docs, no source reading)

## Session log / observations

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
