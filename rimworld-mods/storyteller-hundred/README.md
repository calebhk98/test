# Storyteller: The Hundred

A storyteller who wants you at 100 colonists and pushes until you get there.

## How it plugs into the game

A `StorytellerDef` in XML. Vanilla storytellers control recruiting through a
population curve (`populationIntentFactorFromPopCurve` in the Core defs;
confirm the exact field names against the 1.6 defs before copying). Vanilla
curves taper off far below 100; this one stays high until 100.

Extra `StorytellerComp`s raise the rate of people-arriving events: wanderer
joins, refugee quests, escape pods, prisoners worth recruiting.

Threats scale with colony size, so 100 colonists means raids sized for 100.

## Open questions

- After 100: does it relax, keep going, or flip to pure threat?
- Is there a reward or "win" at 100?
- 100 pawns is heavy on performance. Pairs well with `underground-animal-barn`
  freeing CPU from animals.
