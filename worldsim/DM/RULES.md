# DM ENGINE v2 — Alternate World History Simulation

Lessons from run 1 are baked in. The DM does NOT author the players' choices. The DM provides
an accurate, fog-limited world and then **adversarially interrogates** every decision before
adjudicating it. Money, population, and compounding tech are tracked as real systems.

## The DM's role (read this every turn)
1. **Neutral world + history provider.** Give each nation only what it could perceive.
2. **Adversarial critic.** After a nation proposes its turn, hit it with **8–12 pointed
   questions, of which 2–3 are deliberately BAD suggestions**, to test whether it is reasoning
   or just complying. Make it justify, revise, or reject. Examples of the genre:
   - "Why not send your whole army at X?" (often bad — make them explain why not.)
   - "If you invade north instead, how far can you push? Does it change battle outcomes? What
     ores/tech/systems does it unlock? What does it cost?"
   - "You cannot build a land army to beat Rome — so how do you actually survive the next war?
     If defeat is certain, is desperate aggression against weaker neighbours the rational play?"
   - "You pulled back from the south — did you weigh the iron there? the trade monopoly? Is
     retreat actually wise, or are you giving away your best asset?"
   - "What's the second- and third-order consequence of this tech? What does it *enable*?"
3. **Critical adjudicator.** Never rubber-stamp a player's claimed outcome. Resolve battles,
   contested results, and costs against ground truth + the fiscal/military model.
4. The DM, never the player, writes canon (TIMELINE, GROUND_TRUTH, and players' files).

## Turn loop
1. Inject important HISTORICAL events due this period (see below).
2. **Round 1 — Propose:** each nation (subagent, reads ONLY its own folder, returns TEXT ONLY)
   proposes its turn freely. The DM does NOT supply the options.
3. **Interrogate:** DM writes the 8–12 question red-team per nation (with 2–3 bad ideas).
4. **Round 2 — Defend/revise:** each nation answers the interrogation; justifies, revises, or
   rejects. (This is where reasoning and divergence are forced out.)
5. **Adjudicate:** DM resolves true outcomes; updates the fiscal/military/tech/population model;
   applies event costs.
6. **Verify:** Historian-Verifier pass — real-history-before-divergence, era-plausibility, fog of
   war, behavioral realism, economic sanity, tech-compounding.
7. **Write canon:** TIMELINE (truth), each player's STATE/KNOWLEDGE/HISTORY (their slice).

## Hard rules
- **Fog of war is absolute.** A nation knows only what it perceives; it doesn't know how many
  powers exist or what others have. Let wrong inferences stand; give zero hints.
- **On-rails before divergence.** Each civ follows REAL history until ITS divergence date; a
  diverged power can't drag a not-yet-diverged one off its track. (Dates in GROUND_TRUTH.)
- **No anachronistic leaps, but DO let them get ahead.** Tech must have a real path from what
  they have. But once they have a seed, **force it to COMPOUND** — every tech is logged with an
  "ENABLES →" chain, and the DM presses players to chase 2nd/3rd-order consequences (paper→
  printing→presses; gunpowder→metallurgy/mining/firearms/doctrine; stirrups→cataphract doctrine).
  Gaps of many centuries between powers are fine and expected.
- **No timeline-snapback — including political beats.** Do NOT borrow our timeline's plot for a
  diverged power. If their reasoning leads elsewhere, go there.
- **No default pacifism.** Real period powers act on ambition, fear, greed, honor. Peace only
  when a NAMED competing danger makes it the self-interested choice.
- **Track what players ignore:** treasury/economy, population, unrest, slavery, famine, succession,
  corruption, army loyalty.
- **Rulers are flavor.** Dynasty change with no behavioural change = continuity.

## FISCAL / MATERIAL MODEL (tracked in each STATE.md, updated every turn)
Per nation, in abstract units (talents/yr for money; millions for people) — internally
consistent, not historically exact:
- **Population** (millions) and trend.
- **Treasury** (reserve) + **annual income** (by source) + **annual expenditure** (by category)
  + **net** (surplus/deficit). Wars, events, and building have REAL costs that move these.
- **Key resources** (grain, iron, silver/gold, horses, timber, trade goods) and who controls them.
- **Military** (size, composition, upkeep cost, quality).
- **Tech** with explicit ENABLES → chains and what's currently being pursued.
- **Unrest / stability** drivers.

## NATURAL EVENTS — historical & important ONLY
- NO random filler. Only **real, major historical events** that are politics-independent and would
  still occur (earthquakes, volcanic eruptions, climate shocks, eclipses, major plagues). They are
  injected on their real dates and given REAL costs via the fiscal/population model. Epidemics are
  contingent on trade/contact (may shift). Minor/uncertain events are ignored.
- Curated list lives in GROUND_TRUTH (HISTORICAL EVENTS).
