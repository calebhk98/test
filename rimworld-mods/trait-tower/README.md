# Trait Enhancer Tower

A powered building. Pawns within its radius have a small chance each day to
gain a good trait or lose a bad one. A reverse mode exists for people who want it.

## How it plugs into the game

- Building with a `ThingComp` that does a rare tick, finds colonists within
  the radius, and rolls the chance.
- Adding: `pawn.story.traits.GainTrait(new Trait(def, degree))`.
  Removing: `pawn.story.traits.RemoveTrait(trait)`.
- A settings list (mod settings or the building's gizmo) chooses which traits
  count as "good" and "bad". Defaults: add Tough, Industrious, Fast Learner;
  remove Pyromaniac, Wimp, Slothful, etc.

## Rules to respect

- Trait count: pawns generate with one to three traits. Pick a cap, or
  make "replace a bad trait" the only way to add one when at the cap.
- Conflicting traits (`conflictingTraits`, spectrum traits like Industriousness)
  must be checked so a pawn does not end up Industrious and Lazy at once.
- Trait changes mid-game need the pawn's cached stats/work types refreshed;
  removing a trait like Pyromaniac also has to clear any work-disable it set.

## Open questions

- Power cost, fuel, or research tier?
- Should pawns get a mood thought when it fires ("I feel... different")?
- Chance per day: 1% per pawn feels slow but not broken. Configurable.

## Status

Builds with 0 errors and 0 warnings. Nothing has been run in the game.

- `Trait tower` building (2x2, 500 W, flickable) unlocked by its own research project.
- `CompTraitTower` does a rare tick (every 250 ticks). Each eligible colonist in radius rolls a chance scaled from the per-day setting.
- A per-building "Reverse mode" toggle gizmo (saved with the building). Normal: add good, remove bad. Reverse: add bad, remove good.
- Add checks: no same-def trait at another degree, `conflictingTraits` both ways, backstory `DisallowsTrait`, passion conflicts and requirements, required/disabled work tags.
- Trait cap (default 4). At the cap a pawn can only change by swapping out a trait of the opposite kind.
- Scenario-forced traits, gene traits and suppressed traits are never removed.
- After a change the pawn's work types, skill disables, needs, capacities and render graphics are refreshed.
- Mod settings: chance per day, radius, trait cap, mood thought, messages, slaves, and a searchable list of every trait degree (including modded) that can be marked Good, Neutral or Bad. Reset buttons restore defaults.
- Mood thought: a +3 memory in normal mode, -3 in reverse mode, for 3 days.

## Decisions

- Power cost, fuel or research: 500 W, no fuel, one own research project (`TraitTowerResearch`, 1500 points, Industrial, no prerequisites) so it does not depend on vanilla research names. Cost 150 steel, 8 components, 40 gold.
- Mood thought: yes, on by default, toggle in settings.
- Chance per day: 1% per colonist, slider 0.1% to 20%.
- Trait cap: 4, slider 1 to 8. At the cap, a swap with an opposite-kind trait is the only way to change.
- Reverse mode: per-building toggle, default off. Settings do not change it.
- Add versus remove: when a pawn can do either, it is a coin flip.
- Who is affected: free colonists, plus slaves if enabled. Prisoners and guests never.
- Good/bad lists are keyed by `defName|degree` so Industrious and Lazy are separate entries. Defaults cover Tough, Fast Learner, Industrious, Nimble, Kind, Pretty, Super-Immune, Jogger and Optimist as good, and Pyromaniac, Wimp, Lazy, Abrasive, Ugly, Delicate, Slow Learner and similar as bad.
- Mod settings hold the radius for every tower; it is not per building.

## Unverified

- Vanilla def names used in XML: `Steel`, `ComponentIndustrial`, `Gold`, `Misc` (designation category), `Light` (terrain affordance), `Beauty`, `MaxHitPoints`, `WorkToBuild`, `Flammability`, `Building` altitude layer, `CompPowerTrader`, `CompProperties_Flickable`.
- Default trait keys: `Tough|0`, `FastLearner|0`, `Industriousness|1/2/-1/-2`, `Nimble|0`, `Kind|0`, `Beauty|1/2/-1/-2`, `Immunity|1/2/-1`, `SpeedOffset|1/2/-1`, `NaturalMood|2/-1/-2`, `Pyromaniac|0`, `Wimp|0`, `Abrasive|0`, `Delicate|0`, `SlowLearner|0`, `AnnoyingVoice|0`, `CreepyBreathing|0`, `Greedy|0`, `Jealous|0`. Unknown keys are ignored silently; the settings list shows the real names to fix any.
- Whether a research project with no tab specified lands on the Main tab, and whether the research view position is clear of other projects.
- That `GainTrait`/`RemoveTrait` handle forced passions and trait abilities; the refresh calls are in place but not tested.
- The settings window layout, the search box and the scroll list.
- Texture `Textures/TraitTower/TraitTower.png` is a placeholder (grey block with a teal top). It is also used as the gizmo icon.
- The building's `thingClass` Building, `drawerType` and placement rules were written without Core XML to compare against.

## Not done

- No per-building radius or chance, and no per-building good/bad lists.
- No weighting by trait commonality; the pick is uniform among valid traits.
- Prisoners and guests, and non-human pawns, are not supported.
- No special handling for Ideology/Biotech trait sources beyond skipping gene traits.
- Powered-down towers simply do nothing; no fuel or other upkeep.
