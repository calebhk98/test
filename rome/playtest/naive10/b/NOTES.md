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
