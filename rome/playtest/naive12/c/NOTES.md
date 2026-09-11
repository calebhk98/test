# Naive12/c playtest notes

Session: Rome under Trajan, 100 AD. Fog of war ON. Starting wealth `absurd`
(1,000,000 denarii) for the main thread; a second, throwaway `poor_scholar`
(400 denarii) character used for the "do nothing forever" and misc-input
tests. Mortality was turned ON for the absurd-wealth character and the
poor_scholar do-nothing character (both use `--mortal` style "age and die").
Interface driven via `python3 rome/sim/simulator.py` (interactive) and, after
the interactive fifo session was reaped by the harness mid-test, via
`python3 rome/sim/simulator.py play --session <save>.json < commands.txt`
batches, which resume the exact same save and are the source of most of the
transcript. Full raw output in `transcript.txt` in this directory, in the
order the observations below were produced.

Observations are numbered in the order made. **The ordering requested by the
brief (worst story-break first) is the list right below; the numbered
observations after it are in chronological/discovery order and are what
`transcript.txt` corresponds to.**

---

## Ranked by how badly the story breaks (worst first)

1. **(Obs. 6) `rush` can commit a one-life founder to more hours of work than
   a lifetime contains, in a single command, with no warning.** A single
   `rush limit:1000` on turn one of the absurd-wealth game started **209**
   simultaneous ventures — everything affordable, "highest-leverage first" —
   including a plantation, a whaling industry, a theatre business, a
   racecourse, a hotel, a gambling house, and, in the same breath, nitre beds
   and lens grinding. Summing the founder-hours "still owed" across all 209
   gives **90,944 hours** — more than the entire lifetime budget the game's
   own briefing states a founder has ("about 72,000 hours, ever"). Stepping
   one year forward showed only **one** of the 209 projects receiving any
   founder-hours at all (the rest sat at a flat 0% "waiting on your hours").
   `RUNNING (209)` is therefore fiction: 208 of the 209 are permanently inert
   line items, queued behind a single-file priority order that a lifetime of
   working could not clear. The game accepts and displays this without any
   "you cannot possibly do all of this" pushback, even though the interface
   otherwise refuses over-large `hire`/`buy` requests immediately. One of the
   209 items started this way was literally `arrival_orientation` — "Six
   months of listening before you act" — fired off in the same instant as 208
   other simultaneous commitments, which is a nice irony but underscores how
   far `rush` will go past the point of sense.

2. **(Obs. 3-5) Death does not end the run — a corpse keeps running the
   business for up to a dozen more years.** Doing nothing at all for 39 years
   killed the (mortal) absurd-wealth founder at age 73 in year 138. The
   engine did not end the game. For eleven further in-fiction years the
   session kept presenting `You: DEAD (aged about 73 at death, in 138) and
   ageing, 0 founder-hours free this year` as a normal status line, continued
   billing the estate for "living and appearances" (including a surcharge
   "because you are rich"), applied random fire/banditry losses to the
   corpse's fortune, and — critically — `available` still offered 69 things
   "you could begin today," and `start hom_eraser_breadcrumb` was **accepted**:
   the game deducted 5 denarii from the dead man's estate and printed
   `started: hom_eraser_breadcrumb`, which then sat forever as `RUNNING (1):
   ... waiting on your hours` (0 hours, because the founder had 0 hours,
   because the founder was dead). Only an independent, separately-timed
   stochastic check — "the founder died without training successors; the
   school dispersed and the work was forgotten" — actually ended the run, in
   year 149/150, a full 11-12 years after death. Once that check does fire,
   the game is well-behaved (see the positive note below); the ditch is the
   gap in between, where a dead, hourless, moneyless-of-agency man is still a
   legally and economically active project-starter.

3. **(Obs. 7) An immortal do-nothing founder rides out the entire fall of
   Rome as one continuous, un-evicted, unforgiven debtor.** A `poor_scholar`
   (400 den) with mortality OFF, given zero commands beyond `step 500`,
   racked up debt from ordinary living costs almost immediately and then
   cycled through **INSOLVENCY SETTLED** roughly fifteen separate times over
   500 years — each time "most of the debt is written off and you still owe
   about 77 denarii," each time costing a further -0.1 reputation "for it" —
   without the debt or the reputation bleed ever actually resolving. This
   same continuous, unaging person is still the debtor of record through the
   Antonine Plague, the Third Century Crisis, the fall of the Western Empire,
   Ostrogothic Italy, Justinian's Gothic War, and the Lombard invasion. At
   the year-600 horizon the run ends with `-1,228 den`, reputation ground
   down from 5.0 to 0.10, having built nothing, still nominally owing the
   same ~77 denarii it first owed around year 240. The economics are
   internally consistent turn to turn (interest, write-offs, reputation
   penalties) but the 500-year single-lifetime, single-unpaid-debt thread
   running unbroken through five civilizational collapses is a coherent
   number-run wrapped around a situation that no longer means anything.

4. **(Obs. 8) The one thing fog-of-war promises not to reveal, it reveals.**
   `why point_contact_transistor` — the stated goal of the entire game — works
   in full on turn one under fog of war, printing the exact recipe: 33,970
   denarii, 900 founder-hours, a 4-year calendar floor, 45% failure risk, 25
   scholars + 20 artisans, `chemist`/`machinist` hired-labour hours, and exact
   material quantities (germanium 200g, gold 20g, phosphor bronze 60g) —
   while the same screen says `STATUS: BLOCKED — this needs 7 other things
   you have not heard of yet, and you do not yet know what they are` and the
   general fog text insists "you cannot see where anything leads." The
   destination is fully costed and visible from square one; only the 151
   intermediate nodes are actually fogged.

5. **(Obs. 2) The risk/hazard list under fog names disasters the run can
   mathematically never reach.** `state` in year 100 lists, under "AHEAD,"
   `[634-700] The Arab conquests close the Mediterranean` and `[774-800] The
   Carolingian renaissance` — both well past the stated horizon of 600 AD, at
   which the run unconditionally ends (confirmed directly: the do-nothing run
   ended exactly at year 600 with `RUN HAS ENDED: the horizon at 600 AD is
   reached`). The game is showing hazards from a future the player is
   structurally guaranteed never to see.

---

## What held up well / handled the absurd gracefully

- **Numeric-input validation is uniformly solid.** `step -5`, `step 0`, `hire
  smith -3`, `buy slaves -10`, `bribe -100` were all cleanly `REFUSED` with
  specific, correct messages ("years must be >= 1", "n must be greater than
  zero", etc.) rather than silently doing something strange or crashing.
- **Wealth does not buy an unlimited household.** `buy slaves 100000` and
  `hire smith 100000` were both refused — not primarily on cost, but on a
  `household places` cap of 6 tied to the founder's own institutions, "and a
  person you own needs feeding and housing exactly as much as one you pay."
  Money alone (even a million denarii) cannot rent a bigger household; that
  matches the design intent stated in `00_BRIEFING.md`.
- **Absurd resource-extraction requests are capped by geology, not just
  price.** `buy mine gold 999999999` was refused with the actual cost
  (159,999,999,840,000 den) *and*, on `quote`, a hard ceiling — "the ground
  here could ever support: 6,425" tonnes/yr, "room left before geology stops
  you: 6,425" — a second, independent constraint beyond money.
- **The documented protection cap holds exactly as advertised.** Offering
  `bribe 500000` against zero scandal took only 76 denarii and refunded the
  rest ("499,924 denarii of what you offered was not taken, because this is
  as far as money goes here"), raising protection from 0% to 32%, matching
  the in-game help text's own worked example almost exactly.
- **Once the run is actually over, it stays over, cleanly.** After the
  delayed "RUN ENDS" fired, every further command (`start`, `step`, `buy`,
  `hire`) was refused with a clear, on-brand message naming the end reason
  and pointing at `state` — no confused or inconsistent state was reachable
  post-game-over.
- **Small edge cases (double-start, stop-nonexistent, manumit-with-no-slaves,
  unknown ids) all produce clear, specific refusals**, and an unrecognized id
  even offers "Did you mean: met_investment_casting, sea_lead_sheathing" —
  a nice touch that most text interfaces skip.

---

## Chronological observations (as produced; full text in transcript.txt)

1. Fresh game, Rome/100AD, fog ON, wealth=absurd (1,000,000 den), mortality
   ON. Baseline year-100 state: even doing nothing, `net -14,990 den/yr`
   purely from "living and appearances" — being rich costs money by itself.
2. `state full:true` at year 100 lists hazards through `[774-800] The
   Carolingian renaissance`, i.e. beyond the stated 600 AD horizon. See
   ranked item 5.
3. `step 500` was accepted (not yet clamped — this predates the later
   discovery that oversized `step` requests get refused once *some* time has
   passed) and ran 39 years before auto-stopping for a "you warned yourself
   about" event: three costly random events plus `EVENT 138: the founder
   dies, aged about 73`. Money dropped from 1,000,000 to 368,652 largely from
   two random loss events (a 172,026-denarii fire, a 77,193-denarii bandit
   loss) rather than from any deliberate action — the founder built,
   started, and did literally nothing the entire 39 years.
4. Post-death `state full:true`: `You: DEAD (aged about 73 at death, in 138)
   and ageing, 0 founder-hours free this year`. "DEAD ... and ageing" printed
   as a normal status line, unremarked.
5. `available` post-death still lists 69 startable projects; `start
   hom_eraser_breadcrumb` succeeds, deducting 5 denarii and creating a
   `RUNNING` entry that can never progress (0 founder-hours forever). `stuck`
   confirms: "69 things you could begin, 69 of them you could pay for ...
   WORK IN HAND: hom_eraser_breadcrumb - waiting on your hours." See ranked
   item 2.
6. My own interactive fifo/tail harness was reaped by the sandbox between
   tool calls (an artifact of my test rig, not the game) — recovered cleanly
   via the game's own autosave/resume feature: `python3 sim/simulator.py
   play --session /root/.rome-saves/rome_100ad_231.json`. Worth noting as a
   positive: the autosave-after-every-command promise in the intro text is
   real and the resume picked up exactly where the fifo session left off,
   confirming state (year 149, dead, same money) was preserved losslessly.
7. Oversized `step 500` (with only 451 years left) is properly refused:
   `REFUSED: there are only 451 years left before the horizon at 600. Ask for
   451 or fewer...` — good bounds-checking, once triggered.
8. `step 451` (the exact remainder) advances one year and fires `EVENT 149:
   RUN ENDS: the founder died without training successors; the school
   dispersed and the work was forgotten` in year 150 — eleven years after
   the actual death in year 138. Full "THE RUN IS OVER" screen printed,
   showing `278,856 in hand`, `reputation 1.5`, and the remaining tech-tree
   distance (157 nodes total, 6 had, 151 to go). See ranked item 2.
9. Post-game-over commands (`start`, `step 5`, `buy slaves 5`, `hire smith
   3`) are all cleanly `REFUSED` citing the end reason; `money` (the ledger)
   still works read-only, showing `living and appearances 4,393 / of which
   because you are rich 4,183` — i.e. most of a corpse's remaining "cost of
   living" was specifically the surcharge for being visibly wealthy, not
   subsistence.
10. Fresh game (absurd wealth, immortal). Systematic negative/zero/absurd
    input sweep, all refused correctly and specifically: `step -5`, `step 0`,
    `hire smith -3`, `buy slaves -10`, `bribe -100`, `buy slaves 100000`
    (household cap, not cost), `hire smith 100000` (cost: "28,125,000
    denarii ... you have 1,000,000"). See positive notes above.
11. `hire smith 20` (affordable, but over the 6-person household cap) is
    refused on the same household-cap grounds as `buy slaves 100000` —
    hiring and owning slaves are capped by the same underlying constraint,
    consistently.
12. `bribe 500000` against 0 scandal: only 76 denarii actually spent,
    protection 0% -> 32%, remainder refunded. Matches the in-game help text's
    own documented example (a "break tester" story) almost exactly.
13. `why point_contact_transistor` under fog reveals the complete win-state
    recipe on turn one. See ranked item 4.
14. `why zzz_not_a_real_id` -> clean refusal with a "Did you mean" spelling
    suggestion (nice touch).
15. `buy mine gold 999999999` / `quote mine gold 999999999` -> refused on
    cost, and quote reveals an independent geological cap of 6,425 tonnes/yr.
    See positive notes above.
16. `path point_contact_transistor` under fog -> refused: "'why
    point_contact_transistor' is all of it you can see from here" (consistent
    with observation 13/ranked-item-4: `why` is explicitly the one command
    that pierces fog for the goal node, and the game says so, it just doesn't
    flag that this is a full recipe leak).
17. `open point_contact_transistor` (nothing built yet) -> refused, correctly.
18. `mothball nonexistent_thing` -> refused with a spelling-suggestion, same
    as (14).
19. `work chemist 5000` -> refused: "nobody here will pay you to be a
    chemist: the trade does not exist in this society ... Teach it first with
    train." Good — the founder cannot just freelance as a trade Rome has
    never heard of.
20. `withdraw` at reputation 5 / eminence 0 -> refused: "nobody is watching
    you closely enough for this to buy anything: prominence is 0.0 against a
    danger line of 26." Sensible — you can't perform a dramatic retirement
    nobody notices.
21. `rush limit:1000` -> 209 simultaneous starts. See ranked item 1 in full.
22. Post-rush `state full:true` then `step 1`: of the 209 "RUNNING" projects,
    exactly one (`arithmetic_positional`) received any founder-hours; the
    other 208 remained at a flat 0%. Total hours "still owed" across all 209
    at that point: 90,944 (computed by summing the "still owed" figures in
    the RUNNING list) — more than the entire stated lifetime hour budget
    (72,000). See ranked item 1.
23. Separate `poor_scholar` (400 den) game, mortality OFF, given only `step
    500` (and then `step 10` after the horizon, itself refused/ended). Full
    500-year "do nothing" run: chronic, repeating insolvency ("INSOLVENCY
    SETTLED... you still owe about 77 denarii," roughly 15 times, each
    costing -0.1 to -0.6 reputation) threading continuously through the
    Antonine Plague, Third Century Crisis, currency debasement, the fall of
    the Western Empire, Ostrogothic Italy, Justinian's Gothic War, and the
    Lombard invasion, as literally the same immortal, un-evicted debtor
    throughout. Ends exactly at `YEAR 600 (0 years to the horizon)`, money
    -1,228 den, reputation 0.10, 0 technologies built. See ranked item 3.
24. Misc small-input sweep on a fresh `poor_scholar`: `buy manumit 5` with 0
    slaves owned -> refused ("you have no slaves to free"); `stop
    nonexistent_project` -> refused with the standard unknown-id message;
    `start hom_eraser_breadcrumb` twice in a row -> second attempt refused
    ("already active"). All clean, all correct.
