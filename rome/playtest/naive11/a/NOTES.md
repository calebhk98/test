# TOP PROBLEMS

Ordered by how much they hurt the experience. Two runs of the Rome 100 AD scenario
as `poor_scholar`: run 1 with fog of war ON (died of eminence, 218 AD, 95 of 146
nodes on the road), run 2 with fog OFF (won — point-contact transistor, 509 AD).

1. **Fog of war, which is the default, makes the stated goal effectively
   unreachable and turns the game into a spreadsheet.** With fog on there is no
   signal whatsoever about which of 200-1,000 startable things lead to the
   transistor, so the only usable heuristic is EARNS/YR. I built 540 technologies
   and finished 95 of the 146 on the road. With fog off, `path
   point_contact_transistor` prints the whole road and I won having built *fewer*
   things (378). Fog needs to withhold the *shape* of the tree, not whether the
   thing in front of you is on the road at all. At minimum, mark startable nodes
   that lead to the goal, and let `stuck` say "everything on the road is blocked
   behind X".

2. **Some nodes only do their job while OPEN, and nothing anywhere says which.**
   `school_founded` says "Grants +4 scholars and +2 scholars/yr thereafter". That
   grant silently stops if the school is not a running concern. Meanwhile
   `identity_cover`, `patron_local`, `workshop_first`, `units_standards` all show
   REVENUE 0 / UPKEEP 200-900 and their effects (protection, unlocking
   patron-gated nodes, household places) persist perfectly well when mothballed.
   So the rule I learned from experiment — "opening a zero-revenue node is a pure
   money sink" — is right for four nodes and catastrophically wrong for the fifth.
   I lost ~60 in-game years to this. Worse: the engine had *auto-closed* my school
   ("EVENT 172: nobody left to keep an eye on 10 concerns, so ... closed") as one
   id in a list of ten, so the +2 scholars/yr just stopped with no warning.

3. **Run-ending probabilities are rounded to `0%`.** The turn eminence killed me,
   `state` said `1% chance something lands this year, of which 0% would end the
   run`. Print `<1%`, or two decimals — never round a fatal probability to zero.
   Related: when the run *does* end mid-batch, every queued command gets its own
   identical `REFUSED: the run has ended (...)` line and the actual THE RUN IS
   OVER report only appears if you happen to type `state`.

4. **`labour` does not answer the question `state` sends you to it with.**
   `household places: 5.8 of 6 used ... 'labour' says what raises it` -> `labour`
   only tells you how to *fill* places. The real answers (workshop_first,
   freedman_staff, blast_furnace +15, patron_imperial +50, power_grid +130) only
   ever appear inside a `hire` refusal when you ask for too many people. The same
   goes for the literacy ceilings ("no more than 6.4 scholars ... ever, at any
   price", "no more than 14.3 machinists"), which are invisible until refused and
   which quietly gate half the tech tree.

5. **`stuck` is wrong in the case it exists for.** With `RUNNING: nothing` it
   printed `nothing: you have work in hand, money to pay for it and people to do
   it` — twice, 158 years apart. Under fog it never mentions the goal at all.
   (Under fog-off, with work running, it is genuinely excellent — it prints THE
   ROAD TO THE GOAL and ROOM FOR PEOPLE. That version should be what you always
   get.)

6. **`available` is unusable at scale and offers no way to sort by what matters.**
   207 startable at the start, 1,026 by the end. 54 of the first 207 are `tx2_*`
   textile nodes that cost 6-30 den, earn 0 and cost 40/yr upkeep. There is no
   sort option (it is always by cost), so finding the one node that returns
   560 den/yr on a 266 den outlay means reading every row. I ended up scraping the
   output with awk; a real player cannot. Also, the `HEARD OF, CANNOT BEGIN YET`
   tail prints 25 irrelevant rows on *every* call — including
   `available find germanium`, which matched nothing.

7. **Trained trades silently decay to nothing and there is no maintenance view.**
   Machinists, engineers, chemists, opticians and electricians all rot toward zero
   (I found 0.14-0.28 of each where I had trained 10), and every road node that
   needs them just stops being startable, with no line anywhere saying "you have
   let these trades lapse". `auto_train` claims to replace them and did not.
   Re-teaching costs 450 founder-hours per person, which is not quoted before you
   commit (`quote` only supports mines).

8. **Three different staffing numbers per node, unlabelled.** `available` says
   `STAFF 1s1a`; `why` says `STAFF NEEDED: 0 scholars, 1 artisans`; `open` refuses
   with `it needs 0.00 scholars and 2.13 craftsmen to supervise`. And the prompt's
   `sch 7 art 104` matches none of them. These are genuinely different quantities
   (to start / to run / to supervise) but nothing tells you that.

9. **The middle game is "press step".** By ~200 AD I had +450,000 den/yr and
   nothing to spend it on; every stall message was `waiting on the calendar` or
   `Money in hand cannot buy it down faster`. Three hundred years of the run were
   a single repeated command. Some way to convert money into calendar, even at a
   punitive rate, would keep the decisions alive.

10. **Winning looks exactly like losing.** Same `*** THE RUN HAS ENDED ***`
    banner, same `THE RUN IS OVER` block, only the reason string differs. After
    409 in-game years the payoff was a line of text and then twenty `REFUSED:`
    prompts.

Smaller things: `COMPLETED` lines for free technologies I never started are mixed
in with mine; `FAILED` lines are formatted identically to `COMPLETED` and vanish
into 50-line step reports (75 failures across the winning run, of which I noticed
maybe five); `policy` prints setting names with spaces but requires underscores;
`hire scholar 8` reports success while actually hiring 1; and `path` silently went
*backwards* (43 -> 47 remaining) when the Third-century crisis burned nine of my
technologies, with no line connecting the two.

Best things, so they do not get lost: `why <id>` (especially fog-off, with
`TOTAL DOWNSTREAM: 1,629 thing(s) depend on this -- INCLUDING THE GOAL`); the
`risk` screen, which dates every historical hazard, says what share of it lands on
you and names what you could start *today* to blunt it; `withdraw`, which is one
command with an honestly-priced cost; autosave-after-every-command with a
copy-pasteable resume line (my process died once and I lost nothing); the
end-of-run road report; and the writing throughout, which is genuinely good and
frequently taught me something ("Unlicensed associations are illegal; Trajan
refuses Pliny even a fire brigade at Nicomedia (Ep. 10.34) for fear of factions").

---

# Playtest notes — naive player, session A

(Filling in as I go. TOP PROBLEMS section will be added at the top at the end.)

## Session 1 — first contact

Ran `python3 rome/sim/simulator.py`. Title screen:

```
                      ONE PERSON, AND EVERYTHING THEY KNOW
   You are one person, dropped into a pre-industrial society, carrying the
   knowledge of how modern technology works and none of the industry that makes
   it.
```

Then a menu of 5 settings (Han 100, Rome 100, Viking 900, England 1300, Mexica 1500).
Pleasant surprise: the setting blurbs are genuinely informative and give a hint of the
strategic problem each one poses ("nobody will stop you, and nobody can fund you either").

## Session 1 — Rome, poor_scholar, fog ON, no mortality

Opening is clear and the tutorial line ("the five to start with are 'state', 'available',
'why <name>', 'start <name>', 'step'") is genuinely helpful. `help` is good.

### Confusions / annoyances so far

1. **`stuck` lied to me on turn 1.** With zero projects running it said:
   `nothing: you have work in hand, money to pay for it and people to do it`
   I had no work in hand at all. It should have said "you have started nothing".

2. **`available` is drowned in filler.** 207 startable things, of which 54 are `tx2_*`
   textile nodes all costing 6-30 den, all with `EARNS/YR 0` and `UPKEEP 40`, e.g.
   `tx2_shed  Shed: warp separatio  6  30  0  15%  0  40  1a`. Opening one is a pure
   -40/yr loss. They exist as a wall between me and the ~30 things that actually matter.
   The summary-by-subject view helps, but there is no way to sort by "what earns".
   I had to scrape the output myself with awk to find that `tr_hopper_wagon` returns
   560 den/yr net on a 266 den outlay. A naive player will never find that.

3. **Column headers are ambiguous.** `EARNS/YR` and `UPKEEP` sit next to `RISK` and
   `STAFF`, and `STAFF` prints as `1a`/`1s1a`/`-` with the legend a full screen below.
   Fine once learned; opaque at first.

4. **Things completed that I never started.**
   ```
   COMPLETED 100: Guano
   COMPLETED 100: Amphitheatre with tiered seating
   COMPLETED 100: Barrel vault
   ```
   I started Guano and the Horizontal loom. Amphitheatre and Barrel vault appeared from
   nowhere with no explanation. Nice if it's a freebie, but tell me why.

5. **Pleasant surprise:** the "you know how, but nothing earns until you `open` it"
   rule is called out in `help` *and* in the completion event *and* in `ventures`.
   That is exactly the kind of thing that usually eats an hour of a new player's life.

6. **Pleasant surprise:** `why <id>` is excellent. It gives the historical reasoning
   ("The size of the improvement is disputed in modern scholarship, so claim a real but
   modest gain, not the old textbook figure of four times"), the cost breakdown with
   every multiplier, prerequisites and what rests on it.

7. **Opening a concern silently charges money.** `open ag2_guano` dropped me 58.8 -> 40.9
   and `open tex_horizontal_loom` dropped 40.9 -> 7.1. The printed line only said
   "it earns 100 a year and costs 0 a year to run" — it never mentioned a setup fee.
   I only noticed because my cash nearly hit zero.

### Run 1 result: DIED of eminence in 218 AD, 382 years short

```
  EVENT 217: RUN ENDS: too eminent: brought down not for what you built but for how large you had become
  THE ROAD TO POINT_CONTACT_TRANSISTOR
    146 nodes in all; you had 95 of them and 51 were still to build
```
Ended with 26 million denarii, 297 staff, 540 technologies built, 240 concerns running.

More notes from this run:

8. **The run-end probability display is unfair.** The turn I died, `state` said:
   `EMINENCE is dangerous above 26 (settles near 33.8 ... 1% chance something lands
   this year, of which 0% would end the run)`. "0% would end the run" and then the
   run ended. Rounding a fatal probability down to 0% is the one number you must
   never round. Show `<1%` or two decimals.

9. **The run ended and the program did not tell me until I asked.** The batch I had
   queued kept getting `REFUSED: the run has ended (...)` twenty times in a row, one
   per queued command, all identical. I only realised the game was over when I typed
   `state` for an unrelated reason. Expected: the very first refusal should print the
   full THE RUN IS OVER block (or at least "type `state` to see the final position"),
   not the twentieth.

10. **`available` gets less usable as the game goes on, not more.** By 218 AD it was
    `AVAILABLE: 1,026 startable now`, and the "HEARD OF, CANNOT BEGIN YET" tail
    printed 25 entries plus `632 more, nearest first; ask again with heard_offset 25`
    on *every* `available` call, including `available find germanium` which matched
    nothing. Filtering the startable list does not filter the blocked list, so a
    zero-result search still dumps 25 irrelevant lines.

11. **`labour` does not answer the question `state` sends you to it with.**
    `household places: 5.8 of 6 used - what you can feed, house and oversee.
    'labour' says what raises it.` — `labour` then says only
    `to make room: To get more artisans: hire smith 3 ...`, which is how to *fill*
    places, not how to *raise the cap*. The actual answers (workshop_first,
    freedman_staff, school_founded) are never named there. I found workshop_first by
    guessing the word "workshop" in `available find`.

12. **`open` on a zero-revenue node is a pure trap.** `identity_cover`,
    `scientific_method`, `units_standards`, `patron_local` and `workshop_first` all
    show `REVENUE: 0 den/yr` and `UPKEEP: 200-900 den/yr`. The help text
    ("Finishing something earns you nothing. A concern earns when you 'open' it")
    strongly implies you should open things. Opening these does literally nothing but
    drain money — every effect (protection, the patron unblocking `state is wary`
    nodes, the household-place increase) already fires when the node *finishes*.
    I mothballed all of them and nothing whatsoever changed. That is a costly,
    invisible newbie tax.

13. **Pleasant surprise: `risk`.** Listing each historical hazard with dates,
    what fraction of it lands on you, what would reduce it, and *what you could begin
    right now* to reduce it, with prices, is the best screen in the game:
    `you could begin now: endowment_land (158,080, wealth held as land, not as coin),
     fin_bimetallism (53.5, a standard the coin can be held to)`.

14. **Pleasant surprise: the end-of-run report.** Telling me the road was 146 nodes,
    that I had 95, and naming the next eight steps is exactly right, and made me want
    to play again immediately.

15. **Pleasant surprise: crash recovery.** The game process died on me mid-session
    (silently, no traceback on stdout). `python3 rome/sim/simulator.py play --session
    /root/.rome-saves/rome_100ad_35.json` put me back exactly where I was. Autosave
    after every command is excellent.

16. **Annoying: staff attrition versus the household cap.** I hired 5 artisans; four
    years later I had 2.4. There is no "keep my staff topped up" other than
    `policy auto_hire on`, which then overshoots and bankrupts you because it hires
    up to what you can *house*, not what you can *pay*. I went from +1,600 den/yr to
    -6,900 den in three steps purely from auto_hire plus auto_train buying me
    chemists, engineers, machinists and opticians I had no work for.

## Session 2 — Rome, poor_scholar, fog OFF

Turning fog off changes the game completely, and mostly for the better:

17. **`path point_contact_transistor` is the game.** It prints all 142 remaining
    nodes in dependency order. Without it, under fog, I had no way to tell that
    (say) `nitre_beds` or `mercury_supply` were on the critical road and
    `fud_whaling_industry` was not. Under fog I built 540 technologies and got
    95/146 of the road — i.e. roughly 80% of my effort was off-road. That is not
    "you cannot see where anything leads", that is "you cannot play well".
    Suggestion: under fog, still tell me whether a node I can start today is on
    the road to the goal, even if not how far.

18. **The `RESTS` column changes meaning between fog on and fog off and nobody
    says so.** Fog on: `?`, `few`, `some`, `much`, `ALL`. Fog off: an integer
    (`0`, `1`, `5`, `73`). I only noticed by accident. The word ladder is much
    harder to act on than the number.

19. **`hire` gives better documentation than `labour` does.** Refusals like
    `REFUSED: you can supervise, house and teach 47.47 more people, not 60 - 47 is
    the most whole people you can take. Room is not bought, it is built:
    patron_senatorial (+6 places); blast_furnace (+15 places); patron_imperial
    (+50 places).` and
    `REFUSED: this society's literacy will not supply more than 6.3 scholars in
    total, ever, at any price ... Printing, paper, schools and academies widen the
    pool` are superb. But you only see them by trying to hire too many. `labour`,
    which `state` explicitly points you at for this exact question, says none of it.

20. **`hire scholar 8` silently gave me 1 scholar and I did not notice for 20
    years.** Because the society's literacy cap was ~6 and I already had some, the
    command reported success (`hired: scholar`) without saying how many it actually
    took on. 20 years later `state` said `scholar 1.0` and half the tree was
    blocked on "needs 2 trained scholars". Either report the number actually hired
    or warn when it is less than asked.

21. **Founder-hours are the real bottleneck and the game barely explains them.**
    `You: alive, 7,012 founder-hours free this year (2,000 of your own, plus 2.8
    deputies directing work in your name at 1,800 hours each)`. Deputies appeared
    at some point without any announcement, and nothing in `help` tells you what
    creates one or how to get more. It is the single most valuable resource in the
    late game.

22. **Blocked-node messages are inconsistent about *what* is blocking.** In one
    listing I got all of these forms for "you cannot start this yet":
    - `missing prerequisites: ag2_cultivator, fud_seed_drill`
    - `this needs 1 other thing you have not heard of yet, and you do not yet know what it is`
    - `the state is wary of this (state interest -0.6); get at least a local patron first`
    - `this needs engineers and there are none in this society. Teach one: train engineer 2`
    - `needs 2 trained scholars, you have 1.9 (you are one of them)`
    - `this needs a binder and you have none of the things that would serve: any of mat_celluloid, chm_bakelite would do`
    - `this needs a power and you have none of the things that would serve: any of cap_power_electric, cap_power_steam would do`
    The last two are excellent (they name the alternatives). The "wary of this,
    get a patron first" one never names *which* patron node to build —
    `patron_local` is sitting right there in `available society and politics`
    and is never mentioned by id.

23. **`why <id>` and `available` disagree about what "STAFF" means.** `available`
    prints `STAFF 1s1a` and the legend says "the standing people it needs". `why`
    prints `STAFF NEEDED: 0 scholars, 1 artisans (you have 1, 0)`. Then `open`
    refuses with a *third* number: `it needs 0.00 scholars and 2.13 craftsmen to
    supervise`. Three different staffing numbers for one node (to start, to run,
    to supervise) with almost no signposting that they are different things. This
    cost me several wasted turns.

24. **Pleasant surprise: prices are quoted and then frozen.** `the bill you have
    taken on: 709.4 / note: This is the price as of today, and it is now fixed for
    this project.` Good, and it matters during the currency debasement.

25. **Pleasant surprise: `withdraw`.** A single command with a real, clearly
    stated price ("halves your prominence now and gives up half the reputation you
    hold above what your work by itself is worth ... you cannot do it twice in
    twelve years"), and the message afterwards tells you exactly what you paid:
    `reputation 98.0 -> 66.0, eminence 21.9 -> 11.0`. This is the best-designed
    single mechanic I met.

26. **The biggest single trap in the game: some nodes only do their job while
    OPEN, and nothing tells you which.** I had reasoned (correctly, I thought)
    that `open` was only for revenue: I mothballed `identity_cover`,
    `patron_local`, `scientific_method`, `units_standards` and `workshop_first`
    because they show `REVENUE: 0 den/yr` and `UPKEEP: 200-900 den/yr`, and
    nothing visible changed — protection stayed at 37%, the patron-gated nodes
    stayed unlocked. So `open` looked like a pure money sink.
    Thirty in-game years later I was hard stuck: `academy_network` needs 10
    scholars, and `hire scholar` said *"this society's literacy will not supply
    more than 6.4 scholars in total, ever, at any price"*. The fix turned out to
    be `open school_founded` — the "+4 scholars and +2 scholars/yr thereafter"
    grant only accrues while the school is a running concern. Nowhere does
    `why school_founded`, `help`, or `ventures` say that a grant is conditional on
    being open. `ventures` even lists it under EARNS/YR 800 COSTS/YR 2500, i.e.
    as a loss-maker you should obviously mothball.

27. **A blocked node's advice pointed at itself.** `why academy_network`:
    ```
    STATUS: BLOCKED
      needs 10 trained scholars, you have 7.4 (you are one of them). To get more
      scholars: hire scholar 2 hires literate men by the year; see labour; build
      academy_network eventually (three academies produce more than one school) -
      but it is itself waiting on scholars, so hire or commission first.
    ```
    It tells me to build academy_network in order to build academy_network, then
    notes that this is circular, then tells me to hire — which the literacy cap
    forbids. The one thing that actually works (open the school you already built)
    is not mentioned.

28. **`stuck` was wrong again at the moment I was most stuck.** With the path
    completely blocked behind one node it said
    `439 things you could begin, 439 of them you could pay for` and listed only
    two projects in hand. It never mentions the goal, or that everything on the
    road to it is blocked behind one prerequisite. A `stuck` that knows about
    `path` would be enormously more useful.

29. **Pleasant surprise: `why` under fog-off is outstanding.**
    ```
    STILL TO BUILD BEHIND IT: 0 of 5 nodes, 0 of your hours, 0 den, 5-year serial floor
    DIRECTLY UNLOCKS: balance_analytical, cap_tol_100um, ... prc_square_reference
    TOTAL DOWNSTREAM: 1,629 thing(s) depend on this -- INCLUDING THE GOAL
    ```
    "INCLUDING THE GOAL" in capitals is exactly the signal a player needs. It is
    invisible under fog, which is where a player needs it most.

30. **Pleasant surprise: `path` tells you about your own mistakes.**
    `on this route but shut down: identity_cover, patron_local, workshop_first /
     reopen them with 'restore <id>'` — caught my own mothballing for me.

31. **The pace of the endgame is dominated by "CALENDAR FLOOR" and there is no
    way to buy it down, which is fine — but the game keeps offering to let you
    try.** Typical stall message:
    `academy_network - waiting on the pace it can absorb money: at most 5,681 a
     year goes into this (28,405 still owed, about 5 more years at that rate).
     Money in hand cannot buy it down faster`
    I had 11 million denarii sitting idle. By ~200 AD money had stopped being a
    decision at all: net +450,000/yr with nothing to spend it on. The whole middle
    game is "press step". A money sink that actually converts cash into calendar
    (even at a terrible rate) would restore the tension the first fifty years had.

32. **Minor: `step` with no argument steps one year, but `step 5` is what you
    always want, and `help` shows `step <years>` without saying the default.**
    Small thing, but I typed `step` about forty times before realising.

33. **Minor: the status bar's `sch N art N` does not match `state`'s numbers.**
    Prompt said `sch 7 art 104`; `labour` said `scholar 4.6 ... artisan 137`;
    `why` said `you have 11.8 scholars and 137.1 craft hands - counting yourself,
    and hours you have bought`. Three different scholar counts on screen at once.
    Fog-off `state` does explain it ("counting yourself and hours you have bought
    ... the count above is people on your payroll"), but the prompt does not, and
    the prompt is what you look at.

34. **Failure messages are good, but failure is invisible unless you read the
    event log carefully.** `EVENT 170: FAILED at Ammonia: it did not work. 40% of
    the hours are to do again (24 of your own) and 800 is gone. Attempt 2.` —
    clear and fair. But by the end of run 1 the summary said
    `61 attempts failed and had to be begun again` and I had noticed maybe three
    of them, because a `step 5` prints fifty lines of COMPLETED and the FAILED
    lines are formatted identically and buried among them. A running "failures
    this step: N" counter, or putting failures last, would help.

35. **Confusing: things complete that I never started.** Run 1, first `step`:
    `COMPLETED 100: Guano / COMPLETED 100: Amphitheatre with tiered seating /
     COMPLETED 100: Barrel vault / COMPLETED 100: Horizontal loom`. I started two
    of those four. This happens throughout — free/"granted" technologies get
    COMPLETED lines mixed in with mine. `state` separately reports
    `technologies: 2 built by you, 139 granted for free`, so the game clearly
    knows the difference; the event log should mark it.

36. **Interface friction: there is no way to say "start everything on the path
    that I can start".** Every turn of the endgame is: run `path`, copy 40 ids,
    type `start <id>` 40 times, and read 38 `REFUSED: missing prerequisites`
    lines. A `start next` / `start path` / `start all affordable in <subject>`
    would remove a huge amount of pure typing. (I ended up writing a shell script
    to do it, which a normal player will not.)

37. **Interface friction: `available` has no sort option.** It sorts by cost,
    always. The columns that matter for a decision are EARNS/YR minus UPKEEP, and
    RESTS. `available sort earns` / `available sort rests` would have saved me the
    awk scripts.

38. **A self-contradictory refusal, and a genuinely dangerous silent failure.**
    ```
    REFUSED: this society's literacy will not supply more than 6.4 scholars in
    total, ever, at any price, and you have 50.1 (hired and still being taught).
    There is no room for even one more.
    ```
    Cap 6.4, and I have 50.1. Whatever the two numbers mean they are not
    comparable, and the message reads as a bug.
    Worse: the reason my scholars had collapsed from 55 to 0.4 was that
    `school_founded` had been **silently closed** by the engine
    (`EVENT 172: nobody left to keep an eye on 10 concerns, so ... closed`), which
    switched off the +2 scholars/yr grant. Nothing warned me that the school in
    particular had gone; it was one id in a list of ten, most of them irrelevant
    workshops. `restore school_founded` for 5,000 denarii instantly took me from
    2 scholars to 55. I lost roughly 60 in-game years to that.
    Suggestion: institutions that *grant* people or capacity should never be
    auto-closed silently; and if they are, say so loudly and by name.

39. **Household places and staff decay are a treadmill with no maintenance
    command.** Every trade you *train* (machinist, engineer, chemist, optician,
    electrician) decays toward zero and has to be re-taught, at 450 of your own
    hours each. At year 258 I found:
    ```
      chemist      0.28    electrician  0.14    engineer  0.28
      machinist    0.28    optician     0.14    scholar   0.42
    ```
    down from 10 of each, and every node on the road that needed them had been
    silently unstartable for decades. There is no `state` line that says
    "trades you have let lapse". `auto_train` claims to "replace any trade you
    taught as its people die off" but plainly had not.

40. **Small thing that bit me twice: `policy` syntax.** `policy auto open true`
    gets `say 'on' or 'off', e.g. 'policy auto_hire off'.` — the error names the
    right form, which is good, but the listing above it prints the names with
    spaces (`auto bribe: False`, `auto buy people: False`) while the setter needs
    underscores (`auto_bribe`, `auto_buy_people`). Print them the way they must be
    typed.

41. **Small thing: the first-run seed/session file is not mentioned again.**
    The opening says progress is saved to `/root/.rome-saves/rome_100ad_35.json`
    and how to resume, which is great — but if you scroll past it you can never
    get it back; no `save`/`session`/`where` command prints the current path.
    (`save <file>` exists but writes a *new* file.)

42. **The Third-century crisis actually landed, and it was the best moment in
    either run.**
    ```
    EVENT 280: Third century crisis: a site is sacked - 9,133,133 taken, 244.1 of
      your people gone, 2 projects back to the beginning
    EVENT 280: KNOWLEDGE LOST: 9 technologies forgotten - blast_furnace,
      cap_measure_temp, crucible_steel, ... and 1 more
    EVENT 280: fire in the insula district ... it destroyed 1,095,134 denarii
    ```
    That is a real setback with real texture, telegraphed years in advance by
    `risk`, and partially blunted by the hedges I had chosen to build. Exactly
    right. Two small complaints: (a) `path` silently went *backwards*
    (`remaining count: 43` -> `47`) with no line connecting that to the sack, and
    (b) I had built `corpus_dispersed` and `endowment_land` precisely for this and
    `state` had said `hedged by corpus_dispersed`, so losing nine technologies
    anyway felt like the hedge had not been explained honestly. Say what fraction
    the hedge actually removes.

43. **The "literacy ceiling" applies to trades you have to TEACH, which makes no
    obvious sense and is never explained.**
    `REFUSED: this society's literacy will not supply more than 14.3 machinists in
     total, ever, at any price`
    A machinist is a hands-on craft; the game itself says "Engineers, chemists and
    machinists are scholars here" only in a parenthesis inside `ventures`. So the
    literacy cap silently limits every technical trade, and the cap number
    (6.4 scholars, 14.3 machinists) never appears anywhere except in a refusal.
    A `labour` line "ceilings: scholar 6.4, machinist 14.3, ... raised by
    printing_press / school_founded / academy_network" would fix this entirely.

44. **Founder-hours are consumed by teaching at a brutal rate and it is not
    signposted.** `train machinist 12` = 5,400 of my own hours, i.e. more than an
    unaugmented founder has in two whole years. Three `train` commands emptied an
    18,714-hour year. Nothing before you type it tells you the price; you find out
    from the receipt. `quote train machinist 12` would be the obvious fix
    (`quote` exists but only supports mines).

45. **Correction/nuance to (28): `stuck` is excellent under fog-off *when
    something is running*.** At year 404 it printed:
    ```
      THE ROAD TO THE GOAL:
        11 of its nodes are still to build and NONE of them is startable today.
        The nearest is power_grid: already active
      ROOM FOR PEOPLE:
        you can take 0.00 more people. Room is not bought, it is built:
        power_grid (+130 places); telegraph_electric (+25 places)
    ```
    That is exactly the screen I wanted for 300 years. The bug is the *other*
    branch: with `RUNNING: nothing` it still says
    `nothing: you have work in hand, money to pay for it and people to do it`.
    It also never appears under fog of war, where being stuck is far more likely.

### Run 2 result: WON. Point-contact transistor, 509 AD, 91 years to spare.

```
*** THE RUN HAS ENDED: goal reached: point_contact_transistor completed in 509 AD ***
  you built 378 things; this society already had 141
  90,636,046 in hand, 786.4 people, reputation 52.7, 296 concerns running
  75 attempts failed and had to be begun again
  THE ROAD TO POINT_CONTACT_TRANSISTOR
    146 nodes in all; you had 146 of them and 0 were still to build
```

46. **The victory screen is identical in shape to the death screen.** Same
    `*** THE RUN HAS ENDED: ... ***`, same `THE RUN IS OVER` banner, same stats.
    Only the reason string differs. After 400 in-game years and two runs, winning
    read exactly like dying. Give the win its own banner, and say something about
    what it means — the whole framing of the game ("one person and everything they
    know") deserves a closing paragraph, not a `REFUSED:` prompt.

47. **After the win, the same 20 stacked commands got 20 identical REFUSED lines**
    (same problem as (9)), plus a bonus of three `REFUSED: you have not shut that
    down` from my `restore` commands. The end-of-run state should swallow queued
    input, or say once "the run is over" and stop repeating.

48. **What actually decided both runs, for the record:**
    - Run 1 (fog on): died of eminence at 218 AD with 540 technologies and 95/146
      of the road. Everything I built was chosen by "what earns most per denarius",
      because that was the only signal fog gave me.
    - Run 2 (fog off): won at 509 AD with 378 technologies — *fewer* things built,
      because `path` let me stop building the wrong ones. The three things that
      mattered were `path`, opening `school_founded` (see 26), and `withdraw`ing
      whenever eminence passed 21.
    Fog of war does not make the game harder in an interesting way; it makes the
    goal unreachable and replaces strategy with a spreadsheet of EARNS/YR. If fog
    is the default (`Fog of war? [Y/n]`), most players will bounce off.
