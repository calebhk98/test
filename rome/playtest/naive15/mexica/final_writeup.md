# Final summary - Mexica Triple Alliance playtest

## How far I got

Played from game setup through 1580 AD (80 in-game years from the 1500 AD
start), against an "Endless" horizon and the default goal (Grown and alloy
junction transistors, closure 168, floor 142 years). Ended the session
mid-way through the THIRD debt-bondage cycle of the run, with:

- 15 technologies built by me personally (130 total counting the 115 free
  starting grants)
- 17 of the 168 nodes on the road to the transistor goal
- 7 concerns known how to run; at the final save, 2 open and earning
  (`tex_rope_walk`, `world_map`), one fully built but permanently unopenable
  due to a staffing deadlock (`case_hardening`, worth ~1,500/yr), plus my own
  uncloseable medical practice
- Reputation 8, protection 29%, scandal near zero, eminence low
- Survived: the Spanish invasion (1519-1521, no technology losses landed on
  me), the opening decades of the Old World epidemic (1520-1600, ongoing,
  repeatedly wiping out hired staff but never touching the founder), and the
  start of the colonial order (1550-1700, a standing 28% output penalty)

I did not reach anywhere close to the 168-node goal - 17/168 is roughly 10%
of the way there by node count, though node count is not linear with
difficulty (early nodes are cheap and foundational; later ones are surely
far more expensive). Given the floor is 142 years and I'd used 80 of those
just getting to node 17 while cycling through three debt crises, I think a
realistic honest projection is that this particular playthrough, played
this way, was on pace to take many centuries rather than approach the
142-year floor - which the setup screen itself warned was true ("a real run
takes substantially longer than its floor").

## What stopped me

Not a hard wall - the session ended by my own choice, not because the game
blocked me from continuing. What I chose to stop on:

1. I had just gone through the same "big commitment -> debt -> (sometimes
   failure) -> credit exhaustion -> debt bondage -> clean discharge -> boom"
   cycle three full times in 80 years, including once while actively
   managing the ledger, diversifying income, and reacting correctly to every
   in-game warning I was given. That repetition, more than any single event,
   told me I had seen the game's core economic rhythm clearly enough to
   describe it honestly.
2. I had run into a genuine, unresolved puzzle - a fully-built, highly
   valuable concern (`case_hardening`, ~1,500/yr) that I could not open
   because I was short exactly 0.01 of a craftsman's supervision-time, and
   could not find any in-game way to free that fraction (see notes.md for
   the full chase). That felt like a natural, honest stopping point rather
   than something to brute-force past by spending real-world effort hunting
   for a workaround the game itself never surfaced.
3. I had by then exercised a very wide slice of the command surface (state,
   available, why, start, step, stuck, ventures, open, mothball, restore,
   labour, hire, work, money, policy, risk, portfolio, help) and both of the
   game's two big structural surprises (the scripted 1519 Spanish invasion
   landing exactly on the schedule promised at setup, and the full
   historical hazard timeline running to 2024) had already happened and been
   documented.

## What I would change

In rough order of how much I'd prioritize them:

1. **The 0.01-craftsman deadlock is worth fixing or explaining.** I found a
   real state where a completed, valuable concern was permanently unopenable
   because the one resource blocking it (craftsman supervision-time) could
   not be freed by the one tool that frees committed resources (`mothball`),
   because `mothball` is gated on money-upkeep ("that costs nothing to keep;
   there is nothing to save") rather than on the staff-time it also
   visibly occupies. If this is intentional, the game should say so
   explicitly rather than leaving me to conclude, after real effort, that a
   valuable building I earned honestly is simply stuck shut until I can
   somehow scrape together cash for a second craftsman I can't yet afford
   because the thing that would fund that craftsman is the very concern
   that's stuck shut.

2. **Make the failure-risk mechanic's timing explicit.** `why <id>` states a
   clear failure percentage and cost up front, which is good and honest -
   but nothing told me that risk is checked once, near completion, against
   the FULL committed cost, rather than being some kind of ongoing per-year
   hazard. Losing 1,842 beans at 98% done on `workshop_first` (an 8% risk I
   had accepted knowingly) was fair, but I only understood the TIMING of
   that risk after it happened to me. One added sentence in `why`'s output
   ("this is checked once, near completion, against the full cost") would
   preserve all of the sting while removing the confusion about when to
   expect it.

3. **The fog-of-war hint text for `patron_local` leaked its real id early.**
   Several turns before `patron_local` actually became reachable, the
   `available` blocked-items list printed "get at least a local patron
   first: 'start patron_local'" verbatim - a real, correct id, shown before
   the fog should have allowed me to see it (confirmed because `start
   patron_local` and `why patron_local` both refused it as unknown at the
   time). A sibling code path, `why corpus_written`'s own STATUS block,
   rendered the identical blocking condition correctly and honestly
   ("'start something you have not heard of'"). One of these two renderers
   is leaking information the other one correctly withholds - worth
   reconciling.

4. **Either enforce "no iron" for the Mexica, or say so more precisely.** I
   went back and forth on this one across the session (see the
   self-correction in notes.md) and landed on: the game DOES model
   civilisation-appropriateness for ironworking via a cost multiplier (I saw
   up to x1.76 on `case_hardening`, an explicitly ironworking-themed tech),
   which is honestly a more elegant solution than a hard block. But some
   early, cheap items (`tex_rope_walk`, needing `iron_bar_kg`; `med_herbal_pharmacy`,
   needing `olive_oil_kg` and built on a `mat_linen` prerequisite) carried no
   such penalty (a flat x1 civ multiplier) despite using materials
   (iron, olive oil, flax/linen) that are not indigenous to Mesoamerica
   at all in 1500. If the multiplier system is the intended mechanism for
   this, it isn't applied consistently across every tech that should trigger
   it; if some of these items are meant to represent small imported
   quantities via trade networks (plausible!), that reasoning isn't stated
   anywhere the fog-of-war player can see it, and it's worth a line of
   flavour text saying so, the same way the opening briefing was so precise
   about what WASN'T available.

5. **`available`'s default view is overwhelming for a first-time player.**
   211 startable items on turn 1, bucketed by subject with no goal-directed
   ranking (because fog forbids it - I understand why), left me relying
   entirely on the "MOST RESTS ON THESE" shortlist and `why <id>`'s "HOW
   MUCH RESTS ON THIS" field to make any sense of where to start. Those two
   features did the job well once I found them, and I'd suggest surfacing
   them even more prominently on the very first `available` call, since a
   genuinely new player (which I was) will not know to look past the
   "CHEAPEST SIX" table without being told.

## What I would keep exactly as it is

- The scripted 1519 arrival of the Spanish invasion, landing on the day the
  opening briefing promised, was the best single moment of the run. It cost
  me nothing to appreciate and everything to see coming, in the right way.
- The full historical hazard timeline running to 2024 (drug war, the two
  recent earthquakes, NAFTA, the Porfiriato, all named, dated, and
  percentaged) is an enormous, well-researched surprise that I did not
  expect a game like this to contain, and it made me want to keep reading
  `risk` output well past the point where it was strictly useful.
- Debt bondage itself: severe, well-telegraphed at game setup, mechanically
  fair (it discharges cleanly and completely, on schedule, every single
  time), and thematically apt for this specific society. I went through it
  three times and never once felt cheated by it - only by my own choices
  leading up to it.
- The distinction between "knowing how" (built, permanent) and "running"
  (opened, costs and earns money) is consistently applied and consistently
  explained everywhere it matters (`ventures`, `why`, completion messages).
  I never once found the game contradicting itself on this specific point.

Full turn-by-turn notes, including every dead end, misunderstanding, and
correction to my own earlier conclusions, are in `notes.md` in this same
directory.
