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
