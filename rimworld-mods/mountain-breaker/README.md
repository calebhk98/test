# Mountain Breaker

A high-tech weapon that erases mountain rock and the overhead mountain roof
in an area. For building in a mountain without mining for a week, or for
opening a base's roof to the sky.

## How it plugs into the game

- A weapon `ThingDef` with a `Verb_LaunchProjectile` (or a turret / orbital
  targeter version) and a custom `Projectile`.
- On impact, for every cell in the radius: destroy any natural rock
  (`def.building.isNaturalRock`), optionally drop chunks or ore, and clear the
  roof with `map.roofGrid.SetRoof(cell, null)`.
- Overhead mountain (`RoofRockThick`) cannot be removed by any vanilla means,
  so clearing it this way is the one thing this weapon does that nothing else
  does.

## Open questions

- Does it drop the resources (ore, chunks) or vaporise them? Dropping them
  makes it a mining tool; vaporising makes it a terraforming tool.
- What happens to pawns and buildings under the blast? Harmless beam, or a
  real explosion?
- Should it be hand-held, a turret, or an orbital strike? Orbital avoids the
  "pawn walks up and shoots a mountain" look.
- Huge radius plus `SetRoof` on hundreds of cells at once may cause a hitch;
  spread it over several ticks if so.
