# TOP PROBLEMS

Ordered by how much they hurt the experience. Numbers in brackets point at the
detailed entry further down.

1. **The endgame is a book-keeping puzzle about a number the game never shows
   you.** [11] The last three nodes each demand "25 trained scholars". `labour`
   said I employed ~51 scholar-class people; `ventures` said 19.0 were free;
   the refusal said I had 20.0. Three screens, three numbers, none reconciled,
   and the one the game checks is visible *only inside the refusal message*.
   I mothballed all 259 running concerns and the free count did not move,
   so ~17 scholars are held by something invisible. This cost me ~70 in-game
   years and was the single least enjoyable part of a 500-year run. Show the
   supervision ledger: total, assigned, to what, free.

2. **`stuck` — the command explicitly advertised for this — never helped once.**
   [16][29] It says `nothing: you have work in hand, money to pay for it and
   people to do it` on turn one of a fresh game with nothing started, and again
   when I had 50 nodes to go, nothing running, and nothing on the path
   startable. It never mentioned the staff ceilings that had me pinned. It does
   not look at the goal at all. `help stuck` promises "why you are not getting
   on"; it delivers a canned reassurance.

3. **Rounded-to-zero requirements make refusals self-contradictory.** [1][8]
   > `REFUSED: nobody free to keep an eye on it: it needs 0.0 scholars and 0.0
   > craftsmen to supervise, and you have 1.0 and 0.0 not already watching
   > something else.`
   By the numbers printed, that is satisfiable. It is not. This same rounding
   is why mothballing 259 concerns freed no scholars — dozens of concerns
   listed as needing "0 sch" actually need a fraction each. One decimal place
   would fix the message; a stated minimum ("at least one craftsman on staff")
   would fix the concept.

4. **Nothing points you at the economy, and the economy is the whole opening.**
   [see "First real problem"] I started with revenue 233.5, living costs 230,
   **net +3.5/yr**, against a 1,580-denarius first node. The answer is to build
   cheap concerns and `open` them, but `available` has no way to sort by return
   and no NET column, so I dumped all 207 rows and did the arithmetic by hand.
   Meanwhile several listed items are silent money-losers (`hom_toothbrush`:
   costs 30.3, earns 30, upkeep 40). Add a "BEST RETURNS" block beside
   "CHEAPEST SIX" and "MOST RESTS ON THESE", and show net.

5. **With mortality on, your age is never shown.** [21][22] `state` says only
   `alive and ageing`. No age, no life expectancy, no warning. I died at year 49
   of a 500-year run, and the death message blamed me for "not training
   successors" — a mechanic that appears nowhere in `help`, in any node name I
   saw, or in any prompt. The mode the game calls "the honest number" is the one
   mode you cannot plan for.

6. **Endless re-opening busywork.** [7] `EVENT: nobody left to keep an eye on 3
   concerns, so X, Y, Z closed` fired on essentially every step for four
   centuries, as 3.5%/yr attrition nibbled supervisors. There is no `open all`,
   no priority, no pinning, and `auto_open` loses the race. The optimal play is
   to retype a dozen `open` lines every turn. That is not a decision, it is
   typing.

7. **Failure risk hides catastrophic downside.** [10] `FAILURE RISK: 15%` reads
   as "you may lose some time". In practice: `FAILED at Tall shaft blast furnace
   ... 126,180 is gone`, `Endow the institute in land ... 63,232 is gone`,
   `Central generation and distribution ... 284,800 is gone`. `why <id>` should
   state what a failure costs, not only its probability.

8. **`commission` works for craftsmen, silently not for scholars.** [14]
   `power_grid` refused with "needs 200 trained craftsmen, **on your staff or
   under contract**"; `commission artisan 200000` fixed it instantly. The
   scholar refusal omits "or under contract" and I spent 130,000 denarii on
   scholar-, chemist-, engineer-, machinist-, optician- and electrician-hours
   before working out that it can never help. Same command, same-shaped
   requirement, opposite behaviour, no explanation.

9. **Advice that does not work.** [6][13] Two live examples: `labour` under a
   full household prints `to make room:` followed by instructions for *hiring
   more people* — the thing you cannot do — and never names what actually raises
   the cap (a better version of this message does exist and appears elsewhere:
   "Room is not bought, it is built: power_grid (+130 places); academy_network
   (+50)"; the good one should always be used). And every scholar refusal says
   "Printing, paper, schools and academies widen the pool"; I built all of them
   and the plain-scholar ceiling sat at exactly **6.4** from year 174 to 596.

10. **Fog withholds direction while you live and hands it over when you die.**
    [23] `path <goal>` is refused under fog; the death screen prints
    `the next steps would have been: arithmetic_positional, algebra_symbolic,
    patron_local, ...`. Show one or two next steps while the player can still
    use them.

11. **Trap nodes at the top of the cheapest list.** [27] `lnd_cursus_publicus`
    (the Roman imperial post) and `sea_pharos_lighthouse` are rows 1 and 2 of
    "CHEAPEST SIX RIGHT NOW" in Viking Age Scandinavia and in Tenochtitlan, at
    cost 0. Both are revenue 0, upkeep 200/yr, `HOW MUCH RESTS ON THIS: nothing
    else`. A free-looking item that bleeds you forever, offered to a society
    with no state and (in Mexico) no draught animals at all.

12. **Small stuff that adds up.** [2] techs I never started appear in my
    COMPLETED list with no marker; [9] `policy X on` always answers
    `changed: (none)`; [12] `hire scholar 5` refuses entirely while telling me 4
    would work; [15] `mothball` refuses on upkeep grounds when I am trying to
    free a supervisor; [18] a 200-denarius node capped at "26 a year goes into
    this" while I hold 1.8 million; [19] `commission smith 400` never says
    whether 400 is hours or denarii (it is hours); [30] years printed as
    `1,550 AD`; [28] "Type commands in plain words" then `no command called
    'what'`, and a fuzzy matcher that answers "build a windmill" with eight
    `ag2_*` nodes matched on the letter "a".

## WHAT IS GOOD (so this reads fairly)

- `risk` is the best screen in the game: dated hazards, your exposure, what
  would blunt each, and which candidate mitigations are startable *right now*
  versus blocked and by what. Nothing else I have played does this.
- Counterfactual feedback: `Antonine plague: staff -21% ... (would have been
  -28%: fields that do not fail together; fodder that keeps through a bad
  winter)`. It tells you your preparation worked and by how much.
- `KNOWLEDGE LOST: 6 technologies forgotten ... (the corpus was never printed
  and dispersed)` — the punishment names the thing you should have built.
- Beating the 2,000-hour wall by *building institutions*: `you now have 1 deputy
  directing work in your name: your year is 4,146 hours instead of 2,000. They
  came with the institutions you built.` Elegant, and it lands as a reward.
- The Norse credit warning [26]: threshold, consequence, three named remedies.
- `available` summarising 207 things by subject plus "CHEAPEST SIX" and "MOST
  RESTS ON THESE" — the single best affordance in the game.
- The setting blurbs, the scenario differentiation (Rome vs Norse vs Mexica
  really do play differently), the market-saturation line quietly appearing in
  the ledger, fractional FTE staffing explained in plain English, and the
  refusal to hide slavery from the model.

---

# Playtest notes — "One person, and everything they know"

(Notes taken live while playing. TOP PROBLEMS section will be added at the top at the end.)

## Session 1 — first contact

Launched with `python3 rome/sim/simulator.py`. Title screen offers 5 settings.
Nice: the setting blurbs are genuinely interesting and each states a real
constraint (Mexica: "no draught animals, no iron, no wheel in practical use").

First confusion: the prompt line prints TWICE when input is piped:
```
   Which one? [1-5, or q to leave]    -- a number from 1 to 5.
   Which one? [1-5, or q to leave]
```
The "-- a number from 1 to 5." looks like an error message for an empty line,
but it's attached to the same line as the prompt, so it reads like part of the
prompt itself. Minor, but it made me think I'd already done something wrong.

## Setup screens

- Setting chooser, wealth chooser, mortality chooser, fog chooser. All good, all
  explained. The wealth blurb for `absurd` is oddly defensive/meta ("It used to
  make things worse and no longer does"). Reads like a changelog entry aimed at
  a previous playtester, not at me.
- Same problem, worse, in `help protection`: "a break tester read the 92 as the
  ceiling on bribery, offered a million, and stopped at the same 32% a hundred
  had bought." I am being told about *another player's* mistake inside the
  in-fiction help. Slightly charming, mostly confusing — I had to reread it
  twice to work out it wasn't describing a game mechanic.
- **Session files land in the repo root and never get cleaned up.** Just picking
  a setting and quitting at the first prompt writes `rome_100ad_83.json`. There
  are already 83 of them in the working directory. If I hadn't looked, I'd never
  have known which was mine. The game *tells* you the filename, which is good,
  but auto-numbering into cwd is messy.

## Good stuff early

- `help` is genuinely excellent: topic-based, and every topic answers the real
  question. `help stuck` existing at all is a great idea.
- `state` ends with a "more:" line pointing at the command that explains each
  section. Very good.
- `available` summarising 207 things by subject, then giving "CHEAPEST SIX" and
  "MOST RESTS ON THESE", is the single best affordance in the game so far. It
  told me instantly that `identity_cover` (2,030 downstream) and
  `units_standards` (1,714) are the openings.
- `path point_contact_transistor` printing all 142 remaining nodes in
  topological order is a gift with fog off.

## First real problem: I am broke and the numbers say I always will be

`money` says: Revenue 233.5/yr, living costs 230/yr, **net +3.5 den/yr**.
`identity_cover` costs 1,580. At +3.5/yr that is 337 years to afford the single
most important node in the game. Clearly I'm meant to do something else, but
nothing in `state`, `available` or the opening text told me what. The game says
"you arrive with about enough money to eat for a few months" and then hands me
an economy where eating consumes 98.5% of my income.

## The economy clicks (years 100-113)

Turned out the answer to "I only net +3.5/yr" is: **build cheap concerns and
`open` them**, then borrow against the rising credit limit. Once I saw
`hom_toys_dolls` (75 den → 150/yr) I understood the game. That is a great
moment. But NOTHING pointed me at it:

- `available` shows an EARNS/YR column, but has no way to sort or filter by it.
  I had to dump `available all` (207 rows) into my terminal and eyeball the
  ratio of COST to EARNS/YR by hand. `available afford N` exists; `available
  earns` or a "BEST RETURNS RIGHT NOW" block alongside "CHEAPEST SIX" and "MOST
  RESTS ON THESE" would have saved me twenty minutes of arithmetic.
- Several listed items are **flatly negative** and nothing warns you:
  `hom_toothbrush` costs 30.3, earns 30/yr, upkeep 40/yr — you pay 10/yr
  forever to run it. `med_amputation` earns 8.2 against 50 upkeep.
  `pwr_oil_shale` earns 31.7 against 30. I only avoided these by doing the
  subtraction myself. If the game intends upkeep traps, fine, but the list
  should at least show NET.

## Confusing / wrong things so far

1. **`open` refusal message is self-contradictory.** Trying to open
   `hom_umbrella` with no artisans:
   > `REFUSED: nobody free to keep an eye on it: it needs 0.0 scholars and 0.0
   > craftsmen to supervise, and you have 1.0 and 0.0 not already watching
   > something else.`
   It needs 0.0 and I have 1.0 and 0.0 — by the numbers printed, that is fine.
   Presumably it needs 0.04 and rounds to 0.0. I genuinely could not tell what
   to do; I only fixed it by accident later when I hired artisans for an
   unrelated reason. Print more decimals, or say "you need at least one
   craftsman on staff".

2. **Techs complete that I never started.** After my first `step 1`:
   > `COMPLETED 100: Guano` / `COMPLETED 100: Amphitheatre with tiered seating`
   > / `COMPLETED 100: Barrel vault`
   I started Guano. I did not start an amphitheatre or a barrel vault. They
   just appear in the completion list, mixed in with mine, with no marker
   saying "this is a free contemporary advance, not your work". I spent a while
   convinced I had mis-typed something.

3. **Calendar floors seem not to bite.** `identity_cover` says "CALENDAR FLOOR:
   0.50 years" and `fin_guild` says "calendar floor years: 1", yet both
   completed inside the same single `step 1`. `tr_wooden_waggonway` said
   "YEARS 2" in `available` and finished in one. So the years column in
   `available` is not something I can plan against, and I stopped reading it.

4. **`stuck` said "you have work in hand" when RUNNING was `nothing`.**
   > `nothing: you have work in hand, money to pay for it and people to do it`
   printed on a turn where `state` said `RUNNING: nothing`. Contradiction.

5. **Failure messages don't say the real cost.** "FAILED at Umbrella: it did not
   work. 40% of the hours are to do again (32 of your own) and 36 is gone.
   Attempt 2." — 36 *what*? Denarii, presumably, but the unit is never given,
   and the same sentence gives hours with units.

## Pleasant surprises

- `risk` is superb. It lists the Antonine plague with dates, tells me I take
  100% of the staff loss now, tells me what would blunt it, AND tells me which
  candidate mitigation is startable and which is blocked and by what.
  This is the best-designed screen in the game.
- The economy has a demand ceiling: `what the market will not absorb  -35.1`
  quietly appearing in the ledger. Nice touch, and it appeared exactly when I
  started stacking similar concerns.
- Employment is fractional FTE with attrition and the game explains it in
  plain words ("1.32 artisans is the wage and output of one artisan plus a
  third of another's"). I'd have complained about the decimals if it hadn't.
- The credit limit rising with revenue is exactly right, and it turned "I am
  broke" into a real strategic lever.

## Mid-game (years 120-165): supervision, not money, is the real game

Once the concerns compound, money stops mattering (1.4 million denarii by 165)
and the binding constraints become **household places** and **free craftsmen to
supervise concerns**. That's a nice twist. But the interface fights you here:

6. **The "to make room" hint is circular and wrong.** With HOUSEHOLD PLACES at
   28.0 of 28.0 used, `labour` prints:
   > `to make room: To get more artisans: hire smith 3 or any trade in labour;
   > or commission smith 400 ...; buy slaves N then manumit`
   That is advice on *getting artisans*, which is precisely the thing I cannot
   do because there is no room. And `buy slaves 10` then refuses with "you can
   supervise, house and teach 1.99 more people, not 10". The header says "to
   make room" and then never tells you how to make room. What actually raises
   the cap is building `workshop_first`, `freedman_staff`, `school_founded`,
   `endowment_land` etc. — and I only discovered that by watching the number
   jump from 28 to 43 to 65 to 93 as a side effect of unrelated projects.
   Nothing in `why <id>` for those nodes says "+15 household places" except
   `freedman_staff`, which does say "Grants +8 artisans".

7. **Concerns silently close every single turn and you re-open them forever.**
   > `EVENT 133: nobody left to keep an eye on 3 concerns, so cn_gypsum_plaster,
   > fin_tariff, gp_carbon_brushes closed.`
   This happened on roughly every step for forty years. Attrition (3.5%/yr)
   nibbles the craftsman count, a supervisor slot goes under, and a concern
   drops. There is no `open all`, no priority order, no "keep this one open"
   flag, so the correct play is to re-type a dozen `open` lines every turn. It
   is pure busywork. A `policy auto_reopen` (or letting `auto_open` cover
   already-known concerns) would remove it entirely. Note `auto_open` IS on —
   it opens some but evidently loses the race with attrition.

8. **Supervisor arithmetic is invisible.** `ventures` shows per-concern
   "0 sch 1 cr", but there is no total, and no list of who is watching what. So
   when I have 48 concerns and 0.2 free craftsmen, I cannot tell which concerns
   to mothball to free up the biggest supervisor block. I resorted to firing
   scholars at random.

9. **`policy X on` prints "changed: (none)".** I set seven policies in a row and
   every response ended `changed: (none)` even though the listing above it
   showed the new values. I assumed nothing had happened and set them twice.

10. **A quarter-million-denarii failure with no warning.** 
   > `EVENT 145: FAILED at Tall shaft blast furnace and cast iron: it did not
   > work. 40% of the hours are to do again (360 of your own) and 126,180 is
   > gone.`
   and later `Endow the institute in land: ... 63,232 is gone`. The FAILURE
   RISK shown in `why` was 15-20%, which I read as "one in five attempts wastes
   some time". Losing 126,180 denarii — more than my entire net worth twenty
   years earlier — to one dice roll is a much bigger deal than the phrase
   "FAILURE RISK: 15%" prepares you for. `why` should say what a failure costs,
   not just how likely it is.

## More pleasant surprises

- `EVENT 165: Antonine plague: staff -21%, 217,619 gone with the trade that
  stopped (would have been -28%: fields that do not fail together; fodder that
  keeps through a bad winter)`. Telling me the counterfactual — what it *would*
  have been without my mitigations — is a lovely, generous piece of feedback.
- `EVENT 152: your patron dies; his heir must be courted afresh ... your
  protection falls from 77% to 46%`. Sharp, thematic, and it made me care about
  a stat I'd been ignoring.
- `EVENT 161: you now have 1 deputy directing work in your name: your year is
  4,146 hours instead of 2,000. They came with the institutions you built.`
  Beating the 2,000-hour wall by building institutions is a genuinely elegant
  bit of design and it landed as a reward, not a number.
- Techs that "change the society": `Rag paper from linen changes the society:
  literacy_elite, literacy_general`. I don't know what those knobs do, but
  seeing them move felt significant.

## WON — Rome, 595 AD

```
  goal reached: point_contact_transistor completed in 595 AD
  ended in 596 AD
  you built 474 things; this society already had 141
  24,657,000 in hand, 108.1 people, reputation 39.3, 23 concerns running
  THE ROAD TO POINT_CONTACT_TRANSISTOR
    146 nodes in all; you had 146 of them and 0 were still to build
  the largest things you built: zinc_industry_scale, mat_bulk_steel, power_grid, ...
```
495 in-game years, with 5 to spare. Good ending screen — but it only appears if
you type `state` after winning. At the moment of victory all you get is one
line: `*** THE RUN HAS ENDED: goal reached ... ***`, buried among that year's
plague and fire events. Print the summary automatically.

## The endgame is where the design falls down

The last three nodes (`power_grid`, `single_crystal`,
`point_contact_transistor`) each demand 25 *scholars* and 200 / 25 / 20
*artisans*. Getting artisans was fine. Getting 25 scholars took me roughly
**seventy in-game years and about fifteen real-world minutes of pure
book-keeping**, and here is why:

11. **Three screens report three different scholar counts and none of them is
    the one that matters.**
    - `labour` said I employed `chemist 9.8, electrician 9.8, engineer 9.8,
      machinist 9.8, optician 9.8, scholar 1.9` — about 51 scholar-class people.
    - `ventures` said `free to put behind something new: 19.0 scholars`.
    - `start single_crystal` said `needs 25 trained scholars, you have 20.0`.
    Three numbers (51 / 19.0 / 20.0), no screen reconciles them, and the one the
    game actually checks appears nowhere except in the refusal. I mothballed
    **all 259 running concerns** to free scholars and the free count moved from
    19.0 to 19.0 — so roughly 17 scholars are permanently consumed by something
    the game never shows me. I still do not know what.

12. **Every `hire`/`train` refuses the whole request instead of doing what it
    can, while telling me the number it would have accepted.**
    > `REFUSED: this society's literacy will not supply more than 6.4 scholars
    > ... 4 more is the most you can take right now.`
    So `hire scholar 5` does nothing and `hire scholar 4` works. I typed a lot
    of these. Just hire the 4 and say so.

13. **The literacy ceiling advice does not work.** Every scholar refusal says
    "Printing, paper, schools and academies widen the pool - they raise how many
    people here can read, and this ceiling rises with it." I built `rag_paper`,
    `printing_press`, `prn_wire_mould_deckle`, `school_founded`,
    `fin_lending_library`, `prn_newspaper_institution`, `fin_university`, all
    eight `sc2_institution_*` nodes, and finally `academy_network` — and the
    plain-`scholar` ceiling stayed at **exactly 6.4** from year 174 to year 596.
    (The taught trades did creep, 11.3 → 12.1, over four centuries.) If the
    ceiling is effectively fixed, the advice is a lie; if it moves, it moves far
    too slowly to be actionable.

14. **`commission` works for craftsmen and silently doesn't for scholars.**
    `power_grid` refused with "needs 200 trained craftsmen, **on your staff or
    under contract**"; `commission artisan 200000` fixed it instantly. So on the
    next wall I bought 81,000 scholar-hours, 24,000 chemist-hours,
    24,000 engineer-hours, machinist, optician and electrician hours —
    **130,000 denarii** — and the requirement did not move a decimal place,
    because the scholar refusal quietly omits "or under contract". Same command,
    same shape of requirement, opposite behaviour, no explanation.

15. **`mothball` refuses on the wrong resource.** Supervision is the scarce
    thing; mothballing is the tool for releasing it. But:
    > `REFUSED: that costs nothing to keep; there is nothing to save`
    for every zero-upkeep concern — even though that concern is holding a
    supervisor hostage. I could not shut down `med_bone_setting` (earns 6.2/yr)
    to free the scholar it was sitting on.

16. **`stuck` is useless exactly when you are stuck.** With `RUNNING: nothing`,
    50 nodes to go and nothing on the path startable, `stuck` said:
    > `nothing: you have work in hand, money to pay for it and people to do it`
    It never once mentioned the staff ceilings that had me pinned for seventy
    years. It does not look at the goal path at all.

## Other things worth fixing

17. **`available` truncates ids with capitals out of nothing — no, worse: I
    lost ~30 years because I could not see that `cap_pure_2N` was startable.**
    That one was my own fault (my filter), but the underlying issue is real:
    node ids mix cases (`cap_pure_2N`, `cap_vac_1e6`, `prc_gauge_blocks_johansson`)
    and the NAME column is hard-truncated at 20 characters, so `available` shows
    `Deliberately water-cl`, `Rigid padded horse c`, `Tolerances, jigs, fix`.
    On an 80-column terminal that is fine; there is no reason not to use the
    width available.

18. **The money-absorption cap is wildly inconsistent.** A 200-denarii
    institutional node:
    > `sc2_institution_doctorate — waiting on the pace it can absorb money: at
    > most 26 a year goes into this (130 still owed, about 5 more years)`
    while a 126,000-denarii blast furnace happily absorbed 16,632/yr. I had 1.8
    million denarii sitting idle and could not spend 130 of it on a doctorate
    for five years. The rule may be principled but it reads as arbitrary.

19. **`commission smith 400` — 400 what?** `help labour` and `help economy` both
    give that example and never say whether the number is hours or denarii. It
    is hours (`commission artisan 200000` cost 48,882 den). The one-line help
    should say so.

20. **Session files pile up in the working directory.** 83 `rome_100ad_*.json`
    files were already there before I started, and merely reaching the setting
    chooser and quitting creates another.

## Run 2 — the Mexica, fog ON, destitute, mortality ON (died 1549)

Ended: `RUN ENDS: the founder died without training successors; the school
dispersed and the work was forgotten`. 99 things built, 7 of the 146 goal nodes.
An honest and thematic death, and I do not object to losing. I object to this:

21. **With mortality on, the game never tells you your age or how long you have
    left.** `state` says only `You: alive and ageing`. `state full:true` adds
    nothing. There is no birth year, no age, no life expectancy, no "you are
    beginning to feel it". The entire mode is a lifespan clock and the clock is
    invisible. I planned as if I had centuries because nothing said otherwise,
    and died 49 years in.

22. **The death message names a mechanic that is never mentioned anywhere
    else.** "died **without training successors**". There is no `successor`
    command, no node with "successor" in the name that I ever saw, and `help`
    has no topic on it. I still do not know what I was supposed to build.
    (`school_founded`? `academy_network`? `corpus_dispersed`? The game does not
    say, and under fog I could not have seen them.)

23. **Under fog, `path <goal>` is refused** —
    > `REFUSED: that is what you are aiming at, and you cannot act on it yet:
    > everything it rests on is still beyond what you have heard of.`
    — which is a defensible design choice. But then, the moment I die, the
    end screen prints exactly the thing I needed:
    > `the next steps would have been: arithmetic_positional, algebra_symbolic,
    > patron_local, atomic_theory, statistics_basic, geometry_analytic,
    > workshop_first, calculus`
    Withholding all direction while alive and then handing over the list at
    death is the worst of both worlds. Fog should still tell me the *next* step
    or two toward the goal — that is what "you see the next step, never the
    road" promises, and it is not what it does.

24. **The epidemic fires forever and the risk screen does not say so.**
    `risk` reported one line: `staff loss after what you have built: 80%`.
    In play, `Old World epidemics on contact: staff -80%` fired in 1522, 1524,
    1526, 1530, 1533, 1535, 1537, 1538, 1542... roughly a dozen times across
    twenty years. Each one wiped four fifths of my staff. My revenue went from
    4,659/yr to 272/yr and never recovered. The number in `risk` reads as
    "this will cost you 80% once", not "80%, repeatedly, for a generation".

25. **The wealth-selection screen is Rome-only text in every setting.** Playing
    the Mexica, whose currency is cacao beans, I was offered
    `equestrian 100,000 den — the equestrian census exactly` and
    `absurd 1,000,000 den — four senatorial fortunes in unminted gold`.
    Everything else in the game localises beautifully (hacksilver, cacao beans,
    "the reed and adobe quarter by the canal"), which makes this stand out.

## Run 3 — Scandinavia 900, fog ON, artisan (sampled ~20 years)

Well differentiated: prices 1.4x, credit limit 2,768 instead of Rome's ~1,400
rising to millions, and revenue crawls. The scenario blurb ("nobody will stop
you, and nobody can fund you either") is exactly what it plays like. Also:

26. **Excellent warning I want to praise:**
    > `EVENT 903: CLOSE TO THE LIMIT: you owe 2,021 of the 2,768 anyone here
    > will advance you (73%). Past it every project in hand is halted unfinished
    > and nobody funds new work for some years. 'stop' a project, 'mothball' a
    > loss-maker or 'fire' somebody while it is still your choice`
    Threshold, consequence, and three named remedies. Every warning in the game
    should look like this.

27. **`lnd_cursus_publicus` is offered in Viking Age Scandinavia and in
    Tenochtitlan, and it is a trap.** It is the *first row* of "CHEAPEST SIX
    RIGHT NOW" in both, at cost 0 / 0 hours / 0% risk. `why` says: "A dispatch
    relay using stations and fresh horses is already established wherever a
    state has the capacity to maintain one (Rome's cursus publicus is the
    model). It shows that this state already recognises that speed of
    information matters." — in a society the game itself describes as having
    "no state to ask permission from" (state capacity 0.15), and in one with no
    horses at all ("no horse, no ox, no donkey anywhere in the hemisphere").
    Its actual effect is REVENUE 0, UPKEEP 200/yr, `HOW MUCH RESTS ON THIS:
    nothing else`. A free-looking item at the top of the cheapest list that
    costs 200 a year forever and does nothing. (`sea_pharos_lighthouse` is the
    second row, also 0 cost.)

28. **"Type commands in plain words" is not true.**
    - `what should I do` → `no command called 'what'. Type 'help' for the list.`
    - `how much money do I have` → `no command called 'how'.`
    - `build a windmill` → `REFUSED: you have never heard of any such thing...
      Did you mean: ag2_baler, ag2_chaff_cutter, ag2_composting,
      ag2_contour_ploughing, ag2_coulter, ag2_cultivator, ag2_grafting,
      ag2_guano` — eight suggestions, none containing "wind" or "mill",
      apparently matched against the article "a". The fuzzy matcher should
      either match on the meaningful word or say nothing.

29. **`stuck` says "you have work in hand" on turn one of a brand-new game.**
    Norse, year 900, nothing started, `RUNNING: nothing`:
    > `nothing: you have work in hand, money to pay for it and people to do it`
    It says this whenever it has no complaint, which makes the one command
    designed to unstick you actively misleading.

30. **Years are printed with thousands separators.** `ended in 1,550 AD`,
    `most recently in 1,520`. Small, but it looks like a bug every time.
