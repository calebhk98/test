# TOP PROBLEMS

In the order I would want them fixed. Numbers in brackets point at the detailed
note further down.

1. **Fog of war hides help text that is not about the tree at all, and that
   leaves the player genuinely stuck for a hundred in-game years.** [2, 12, 13, 25]
   With fog OFF, `labour` says "to make room: **Room is not bought, it is built:
   school_founded (+12 places); endowment_land (+8 places); patron_senatorial
   (+6 places)**" and `state` explains that a chemist counts toward the
   "scholars" figure that `why` and `start` test against. With fog ON, the same
   fields say only "'labour' says what raises it" (it doesn't) and print two
   numbers that contradict `ventures`. Neither sentence reveals anything about
   where the tree goes. Show them under fog.

2. **Under fog, the game tells you to do things it will not let you find.** [7, 12]
   For ~50 in-game years the frontier said "the state is wary of this; **get at
   least a local patron first**". There is no `patron` command; `available find
   patron` said "nothing matching 'patron'"; `help` never mentions one. I found
   `patron_local` by hand-walking every subject heading. It unlocked
   `workshop_first` (filed under the subject "the briefing"), which is flagged
   "HOW MUCH RESTS ON THIS: almost everything" and which tripled my household
   places the year it finished. The intended opening spine - identity_cover →
   patron_local → workshop_first → freedman_staff/collegium → school_founded - is
   effectively undiscoverable under fog. If a blocker message names a
   requirement, it should name the node that satisfies it.

3. **`policy auto_hire true` bankrupted a healthy game in eight years, and
   `auto_train` did the same on a smaller scale.** [3, 9] Described as "grow the
   staff toward what you can house and pay", it hired 5.5 scholars at 625/yr when
   every concern I owned needed craftsmen, squeezed my artisans out of the
   household places, closed seven concerns, and ended in "CREDIT EXHAUSTED" and
   "INSOLVENCY SETTLED ... reputation -12.0". Either make it hire the trades the
   work actually needs and respect the budget, or warn before it commits.

4. **A multi-year `step` runs straight through its own emergency warnings.**
   [10, 23, 31] Inside one `step 8` I got "CLOSE TO THE LIMIT ... 'stop' a
   project, 'mothball' a loss-maker or 'fire' somebody **while it is still your
   choice**" and then insolvency, with no chance to act. Elsewhere a step ate ten
   consecutive years of "SHORT OF SALTPETRE: work running at 5% of plan" and
   "nobody left to keep an eye on 68 concerns ... closed". `step` should stop on
   these classes of event and hand control back.

5. **You cannot see how far along you are until the run is over.** [20, 29]
   The ending prints "146 nodes in all; you had 122 of them and 24 were still to
   build". That single line is the most useful thing in the game, and under fog it
   arrives after the clock has run out. Give a progress figure during play - even
   just counts, no names - and ideally "N years of irreducible calendar floor
   remain on the critical path", because the endgame is decided by calendar, not
   money.

6. **Mortality mode buries its own terminal event and then soft-locks.** [26, 27, 28]
   "EVENT 938: the founder dies, aged about 73" appears as one line among
   completion messages. The game then ran twelve more years with
   "You: DEAD and ageing, 0 founder-hours" and 25 projects "waiting on your
   hours", accepting `start` commands, before finally printing the (very good)
   ending. Also: with ageing on, the game never tells you your age or your
   expected remaining years, which is the one number that mode exists to make you
   plan around.

7. **The "unopened concerns" nag counts things that would lose money.** [16, 17]
   "you know how to run 481 more and have not opened them - those shut concerns
   would clear 39,524 den/yr" reads like a to-do list. In fact most earn 0 and
   cost upkeep (`scientific_method`: 0 revenue, 100 upkeep), and `auto open`
   rightly refuses them. Worse, listing `scientific_method` and `units_standards`
   under "YOU KNOW HOW, AND HAVE NOT OPENED" implies their stated multipliers only
   work while open. They don't - DONE is enough. Say so.

8. **Your own backlog silently throttles you and nothing points at it.** [30]
   110 cheap unrelated projects I started "to unlock things" sat in RUNNING for
   eighty years eating founder-hours. `stuck` listed 115 identical lines of
   "X - waiting on your hours" with no ranking. Stopping 111 of them took path
   progress from 2 nodes/24 years to 17 nodes/30 years.

9. **Displayed FAILURE RISK does not match observed failures, and there is no
   feedback loop.** [4, 21] `ag2_refrigeration_ice` at "FAILURE RISK: 15%" failed
   four years running (p = 0.05%). Across one run: "807 attempts failed and had to
   be begun again", never summarised until the end.

10. **Smaller papercuts.** `open` silently charges a year's upkeep up front and
    `why`/`help` never mention it [5]. Staff attrition (3.5%/yr) quietly hollows
    out your workshop during long steps with no trend indicator [14]. `train
    chemist 8` is refused entirely when the ceiling allows 7, in a message that
    says 7 is allowed [33]. `state`'s headline "net -631.5 den/yr" folds one-off
    project spend into a per-year rate and makes a healthy position look fatal [8].
    Hidden hired-labour supply ceilings ("machinist wants 1250 hours a year; this
    society can field 216 at most") are invisible in `why` until a project stalls
    [19].

---
# Playtest notes — naive player, session "naive11/b"

(Notes written as I play. TOP PROBLEMS section will be added at the top at the end.)

## First contact

Ran `python3 rome/sim/simulator.py`. Title screen:

```
                      ONE PERSON, AND EVERYTHING THEY KNOW
   You are one person, dropped into a pre-industrial society, carrying the
   knowledge of how modern technology works and none of the industry that makes
   it.
```

Then a menu of 5 settings (Han 100, Rome 100, Viking 900, England 1300, Mexica 1500)
with population / state capacity / price multiplier. Nice framing, clear premise.
I have no idea yet what "state capacity 0.85" does mechanically — it's presented as
a stat but never explained. Guessing it means "how much the government can help or
hinder me".

## Run 1 — Rome 100 AD, poor_scholar, fog ON, no ageing

Goal revealed only in `state`: "Aiming at: Point-contact transistor", horizon 600 AD.
Nice: the opening tutorial line ("the five to start with are 'state', 'available',
'why', 'start', 'step'") is genuinely enough to get going. `help` is deep and good.

### What worked well (pleasant surprises)
- `available` collapsing 207 items into a subject table with CHEAPEST/DEAREST/AFFORD,
  plus "MOST RESTS ON THESE", is a really good answer to "there are 207 things, help".
- `why <id>` is excellent: cost broken into labour/materials/capital with the
  multipliers shown (`x0.85 your civ, x1 distance, x1 scarcity, x1.025 opposition`).
- The one big gotcha is called out up front and repeatedly: "Finishing something
  earns you nothing... 'open' it". I still got caught once, but the game told me.
- `money` ledger that says "(these add up to the revenue above)" and explains
  the 1/3 practice discount. Very legible.
- Saving after every command + `--session` resume. My process got killed mid-game
  and I lost nothing. Excellent.
- The hazard timeline in `state full:true` (Antonine plague 165-180, etc.) is a
  lovely piece of texture and actually actionable.

### Confusing / annoying
1. **`why` and `ventures` disagree about how many staff I have.**
   `ventures` said "free to put behind something new: 1 scholars, 1 craftsmen
   (one of each of those is you)". At the same moment `why tr_hopper_wagon` said
   "STAFF NEEDED: 0 scholars, 1 artisans   (you have 1, 0)". So do I have one
   craftsman (me) or zero? I could not tell whether I could start it. (I could.)

2. **"household places: 7.3 of 7.3 used - 'labour' says what raises it." `labour`
   does NOT say what raises it.** It says:
   "HOUSEHOLD PLACES: 4.2 of 6 used, room for 1.8 more / to make room: To get more
   artisans: hire smith 3 ... or buy slaves N then manumit". That is how to FILL
   places, not how to raise the CAP. I watched the cap wander 6 -> 7.3 -> 6.6 with
   no explanation and never learned what drives it. This was the single most
   opaque number in the game for me.

3. **`policy auto_train true` quietly bankrupted me.** With no project running it
   trained ~2 chemists and ~2 machinists. Wage bill went from 486/yr to 4,175/yr,
   my net went from +518 to -278, and worse: those five idle scholars filled every
   household place, so I could not hire the artisans I needed to *open* the
   concerns I had already paid to build. Nothing warned me. I would expect either
   "auto train: teach trades ... when a project needs them" to mean exactly that,
   or a warning like "this will add 3,700 den/yr in wages".

4. **Displayed FAILURE RISK felt wrong.** `ag2_refrigeration_ice` is listed at 15%
   risk. It failed four years running (attempts 2,3,4,5), each costing 112 den and
   28 of my hours. p = 0.15^4 = 0.05%. Either the shown number is not the number
   used, or repeated attempts are penalised and it doesn't say so. Very annoying
   with no feedback.

5. **`open` silently charges you.** "opened: tex_indigo ... capital: -300". Each
   open cost me one year's upkeep up front. `why` never mentions this, and `help`
   says open "starts actually running something" with no note of a cost. Small,
   but I was already in the red and didn't budget for it.

6. **The fog frontier tells me a door is locked but never gives me a key.**
   "case_hardening: this needs 1 other thing you have not heard of yet, and you do
   not yet know what it is". There is no hint about *where* to look. My only
   strategy is "build everything cheap and hope". With 260 startable items that is
   a lot of blind flailing.

7. **"the state is wary of this (state interest -0.9); get at least a local patron
   first"** — but nothing in `help`, `available find patron` or the command list
   tells me how to get a patron. `help protection` lists "A patron, citizenship, a
   licensed collegium, land endowed in public, a school" as sources of protection,
   all of which sound like things I should be able to *do*, and none of which are
   commands or (visible) tech ids.

8. **`state` prints "net -631.5 den/yr (after 618.3 den into projects this year)"
   and `money` prints "Net/yr after it: -416.5".** These are backward-looking
   one-off project spend folded into a per-year rate. It made my finances look
   like a death spiral when they were fine. I'd rather see the steady-state rate
   as the headline.

### The middle game (140-195 AD)

9. **`policy auto_hire true` destroyed my run.** Its one-line description is
   "grow the staff toward what you can house and pay". What it actually did over
   8 years of `step`: hired 5.5 *scholars* (625 den/yr each) when every concern I
   owned needed *craftsmen*; the scholars filled every household place; my artisans
   were squeezed out; 7 concerns closed for want of a supervisor; revenue collapsed;
   and I hit "CREDIT EXHAUSTED ... INSOLVENCY SETTLED: most of the debt is written
   off ... reputation -12.0". A single policy toggle took me from +11,669 den and
   16 running concerns to -7,296 den and 11. It did not "hire toward what I can
   pay" - it hired well past it, and it hired the wrong trade.

10. **`step 8` ploughed straight through its own warning.** The log contains
    "EVENT 137: CLOSE TO THE LIMIT: you owe 7,940 of the 9,927 ... 'stop' a project,
    'mothball' a loss-maker or 'fire' somebody **while it is still your choice**"
    and then, one year later, insolvency. But I was inside `step 8` and never got
    a choice. A multi-year step should stop at that warning and hand control back.

11. **REFUSED messages scroll past inside a batch.** `start corpus_written` came
    back "REFUSED: nobody here will fund new work: your creditors were left unpaid".
    Perfectly clear message - but I only noticed 5 years later when `state` said
    "RUNNING: nothing". Some kind of persistent "last refusal" marker in `state`
    would help.

12. **The spine of the game is invisible under fog, and the hints point at things
    `available` will not show you.** From year ~128 the frontier kept telling me
    "the state is wary of this; **get at least a local patron first**". There is no
    `patron` command; `available find patron` returned "nothing matching 'patron'";
    `help` never mentions one. I found `patron_local` (1,200 den, subject "society
    and politics") at year 173 by manually walking every subject heading. It then
    unlocked `workshop_first` (subject "**the briefing**", of all places), which is
    marked "HOW MUCH RESTS ON THIS: almost everything" and which instantly raised my
    household places from 6 to 18 - the single number that had been strangling me
    for seventy years. The intended opening is clearly
    identity_cover -> patron_local -> workshop_first, and I found it by accident
    45 in-game years late. Under fog, "get a patron first" should name the node.

13. **The household-places cap answer finally appeared - but only after I'd already
    solved it.** After building workshop_first, `labour` started saying
    "to make room: ... **build freedman_staff** (buy, teach and free a technical
    staff)". That sentence is exactly what I needed at year 110. Before that,
    the same field said only how to fill places, never how to add them.

14. **Attrition quietly eats the staff you need and nothing shouts about it.**
    3.5%/yr compounding meant my artisans went 4.5 -> 1.1 over ~15 years of
    stepping while I was busy elsewhere; concerns closed one at a time inside
    multi-year steps. `state`'s EMPLOY block shows the number but not the trend.

### Pleasant surprises (continued)
- `risk` is the best screen in the game. For "[IN PROGRESS] Antonine plague" it
  names the mitigations *and* prices them: "you could begin now: md2_sand_filtration
  (291.8, filtered water), horse_collar (709.4, a step toward fields that do not
  fail together)". That is exactly the right amount of hand-holding.
- The pace cap is elegant: "at most 473 a year goes into this ... Money in hand
  cannot buy it down faster". Ten-year projects really do take ten years.
- The frontier messages get *better* as you get closer: "needs 2 trained scholars,
  you have 1.6 (you are one of them)" and "this needs engineers and there is not
  one left here to do it: you taught the trade and nobody is currently holding it".
- Insolvency is survivable and clearly narrated. I lost 12 reputation and kept my
  knowledge. That felt fair.

### Late game (200-280 AD)

15. **The snowball is enormous and the game stops pushing back.** Once
    `workshop_first` + `freedman_staff` + `school_founded` land, household places
    go 6 -> 18 -> 53 -> 118, founder hours go 2,000 -> 7,250 ("2,000 of your own,
    plus 2.9 deputies directing work in your name at 1,800 hours each"), and money
    goes from "can I afford 709 denarii for a horse collar" to 6,000,000 denarii
    with +85,000/yr. From about year 230 the only real constraint is my own typing.
    The interesting game is roughly years 100-190.

16. **`state` says "you know how to run 481 more and have not opened them - those
    shut concerns would clear 39,524 den/yr" as if it were a to-do list.** It is
    not actionable: most of them earn 0 and cost upkeep, and `auto open` correctly
    refuses them. Earlier, at 16 unopened, exactly 4 were worth opening and the
    other 12 were pure loss (`algebra_symbolic` 0 earns / 50 upkeep,
    `identity_cover` 0 earns / 200 upkeep, `scientific_method` 0 earns / 100
    upkeep). A new player reads that nag as "you are leaving money on the table"
    and opens them all. There should be a "worth opening: N" count instead.

17. **You cannot tell whether a foundation node needs to be OPEN to give its
    benefit.** `scientific_method` says "Multiplier on every research node
    thereafter" and has UPKEEP 100 / REVENUE 0. Is the multiplier active because
    it is DONE, or only while it is running as a concern? `ventures` listing it
    under "YOU KNOW HOW, AND HAVE NOT OPENED" strongly implies the latter. It
    turned out DONE is enough (it satisfied `corpus_written`'s prerequisite while
    shut). I spent several turns agonising over 100 den/yr for no reason.

18. **Repeatedly told a trade doesn't exist without being told the fix, then told
    it beautifully.** Compare year 128: "this needs engineers and there is not one
    left here to do it" (dead end for me at the time) with year 272: "this needs
    opticians and there are none in this society. Teach one: **train optician 2**
    (about 450 of your own hours each, two years)". The second form is perfect.
    The first form appeared for ~100 in-game years first.

19. **Hidden supply ceilings surface only as a stalled project.** After starting
    ~90 things I got: "waiting on nobody to do the work: machinist (wants 1250
    hours a year; this society can field 216 at most)". That is a good message,
    but nothing in `why` warns you before you commit: `why balance_analytical`
    lists HIRED LABOUR: machinist 1,250h and does not say the society can only
    field 216.

### Run 1 result (Rome 100 AD, poor_scholar, fog on, no ageing)

```
THE RUN IS OVER
  the horizon at 600 AD is reached. You built 2349 things of your own and did
  not reach point-contact transistor.
  617,448,063 in hand, 334.2 people, reputation 98.9, 335 concerns running
  807 attempts failed and had to be begun again
  THE ROAD TO POINT_CONTACT_TRANSISTOR
    146 nodes in all; you had 122 of them and 24 were still to build
    the next steps would have been: motor_transformer_ac, diffusion_pump, ...
```

20. **The end screen is superb and it is the first time the game ever showed me
    the shape of the problem.** "146 nodes in all; you had 122 of them and 24 were
    still to build" - that is the single most useful sentence in five hundred
    years of play, and I got it after the clock ran out. Under fog I never had any
    idea whether I was 10% or 90% of the way there. Even a crude "you have N of
    the M nodes on the road" (without naming them) during play would transform the
    experience from blind flailing into a race.

21. **807 failed attempts.** That is a lot of invisible tax. Failures are reported
    but never summarised until the end, and the per-node "FAILURE RISK: 20%" never
    seems to reflect what actually happens on repeats.

22. **The real bottleneck at the end was a per-trade literacy ceiling nobody told
    me about until I hit it.** "this society's literacy will not supply more than
    16.1 chemists in total, ever, at any price". Fine - but two related things bite:
    (a) technical staff apparently count as HALF a scholar each for STAFF NEEDED
    (43.5 tradesmen showed as "21.5 scholars"), which is never stated anywhere; and
    (b) `train chemist 8` when the ceiling allows 7 is **refused entirely** rather
    than training 7. The refusal even says "7 more is the most you can take right
    now" - so just do 7.

23. **Concerns silently close en masse inside a `step`.** "EVENT 593: nobody left
    to keep an eye on **68 concerns**, so ag2_cheese_families, ag2_composting,
    ag2_maize_newworld, ag2_marling **and others** closed." Sixty-eight at once,
    named four, inside a multi-year step, because my artisan headcount had drifted
    down. There is no "staff shortfall" warning before it happens.

## Run 2 — Scandinavia 900, artisan, fog OFF, MORTALITY ON

Chosen partly by accident (I typed 'y' at "Let the founder age and die? [y/N]"),
which turned out to be the most revealing thing I did all session.

24. **`path <id>` with fog off is a completely different game, and it is the good
    one.** `path point_contact_transistor` prints the entire 142-node route in
    build order. Suddenly there is a plan. Compare five hundred years of fog where
    the only feedback was "this needs 1 other thing you have not heard of yet".
    The gap between the two modes is enormous - there is nothing in between.

25. **Fog hides help text that has nothing to do with the tree.** With fog OFF,
    `state` prints:
    "counting yourself and hours you have bought: 1.0 scholars and 1.0 craft
    hands. That pair is what the prompt shows and what 'why' and 'start' test a
    project against; the count above is people on your payroll."
    and `labour` prints:
    "to make room: **Room is not bought, it is built: school_founded (+12 places);
    endowment_land (+8 places); patron_senatorial (+6 places).**"
    Both of those are precisely the sentences I needed in run 1 and could not get
    at any price. Neither reveals anything about where the tree leads. Hiding
    them behind fog is, I think, simply a bug.

26. **The founder dying is a one-line event in the middle of a completion list.**
    ```
    EVENT 938: completed: Composting
    EVENT 938: the founder dies, aged about 73
    EVENT 939: nobody left to keep an eye on 3 concerns, ...
    ```
    No banner, no pause, no "THE RUN IS OVER". I did not notice for two commands.

27. **And then the game kept going for twelve dead years.** `state` said
    "You: DEAD and ageing, 0 founder-hours free this year" and listed 25 projects
    "waiting on your hours" that could never advance. `hire` returned "REFUSED:
    there is nobody left to take anyone on: the founder is dead and no deputy
    remains to direct the work". I could still type `start`, and it accepted them.
    Only when I typed `step 20` did I get the (excellent, well-written) ending:
    "the founder died without training successors; the school dispersed and the
    work was forgotten". That should fire the moment the founder dies with no
    deputy - or at minimum `state` should say the run is effectively over.

28. **With mortality on, the game never tells you your age or your odds.**
    "You: alive and ageing" - that is all. No age, no life expectancy, no "you are
    62 and the actuarial table says you have about 11 years". I had no way to plan
    the one decision the mode exists to force (build the institution before you
    die). I died at 73 having built workshop_first and freedman_staff but not the
    school, and lost everything.

## Run 3 — Later Han 100 AD, rich_merchant, fog OFF, no ageing

Played to win, using `path` as a build order. Final:
```
  ran out of horizon (600 AD) without reaching the goal
  you built 897 things; ... 86,736,219 in hand, 297.6 people, 400 concerns running
  98 attempts failed and had to be begun again
  THE ROAD TO POINT_CONTACT_TRANSISTOR
    146 nodes in all; you had 140 of them and 6 were still to build
    the next steps would have been: germanium_extraction, gecl4_purification,
    ge_reduction, zone_refining, single_crystal, point_contact_transistor
```
Six nodes short. The tail of the tree is pure calendar floor - germanium_extraction
5y, gecl4_purification 5y, ge_reduction 3y, zone_refining 6y, single_crystal 5y,
point_contact_transistor 4y = 28 years of wall clock that no amount of the
86 million denarii in my hand can buy down. That is a legitimate and even elegant
design point, but it means:

29. **The last hundred years are decided by a decision you made in the first
    thirty, and nothing tells you that until it is far too late.** By 500 AD I had
    money, staff, hours and reputation to spare; the only thing I lacked was
    calendar. A "critical path: N years of irreducible calendar floor remain"
    number would make the endgame a race instead of a slow realisation.

30. **Starting the wrong things is silently, permanently expensive.** Early on I
    started ~110 cheap unrelated projects "to unlock things". They then sat in
    RUNNING for eighty years soaking up my founder-hours at 34-87% completion,
    while my path nodes crawled. Nothing in `state` or `stuck` ranks work in hand
    by whether it is on any road; `stuck` just lists 115 lines of
    "X - waiting on your hours". When I finally `stop`ped 111 of them, path
    progress went from 2 nodes / 24 years to 17 nodes / 30 years. A player has no
    way to see they are being throttled by their own backlog.

31. **Raw-material and supply throttles fire once a year, forever, inside a step,
    and only stop the world silently.** Ten years of
    "EVENT 3xx: SHORT OF SALTPETRE: work running at **5% of plan**." went past
    inside `step` calls and I only found it by grepping my own scrollback. The
    message itself is excellent ("Saltpetre is made in nitre beds, not mined:
    'buy nitre 20000' ... it is cheap: 1.50 cash the square metre") - it just
    needs to interrupt, or at minimum appear in `state`.

32. **Yongjia disaster: "a site is sacked - 3,123,568 taken, 22.7 of your people
    gone, 5 projects back to the beginning".** Losing five in-flight projects
    entirely, plus 27 already-built technologies, is brutal and I had no warning
    that "5 projects back to the beginning" was even a possible outcome. `risk`
    lists the sack chance but describes the consequence only as "technologies at
    risk".

33. Small: **`train chemist 8` when the ceiling allows 7 refuses the whole
    command** and tells you 7 is the max. Just train 7. Same for
    `hire scholar 8`. I lost several turns to this.

34. Small: **ids are not all lower-case-with-underscores** (`cap_pure_2N`,
    `cap_pure_4N`, `cap_pure_6N`). Harmless for a human, but the inconsistency
    surprised me when scanning lists.

## Things I liked a lot (summary)
- The writing. "Sejanus was the most protected man in Rome until the morning he
  was not." The per-hazard history notes. "a break tester read the 92 as the
  ceiling on bribery, offered a million, and stopped at the same 32% a hundred
  had bought."
- `why <id>` cost decomposition with the multipliers, and "This is the price as of
  today, and it is now fixed for this project."
- `risk` naming priced, startable mitigations for each coming disaster.
- Calendar floors that money cannot buy down, and the "at most X a year goes into
  this" pace cap. It makes the century feel like a century.
- Different civilisations really do differ: in Rome school_founded needed
  freedman_staff; in Norse and Han it needed collegium_licensed (and in Han,
  citizenship first). Han's literacy ceiling was 10.5 per trade vs Rome's 16.1.
- Save-after-every-command. My terminal died three times and I lost nothing.
- The end screen.
