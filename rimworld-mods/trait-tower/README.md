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
