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

## Status

Builds with 0 warnings and 0 errors. Nothing has run in the game.

- Hand-held weapon `MB_MountainBreaker` (own ThingDef, no vanilla parent) firing
  `MB_MountainBreakerCharge`, a custom `Projectile_MountainBreaker`.
- On impact every cell in the radius is queued on a per-map `BreakQueue`
  (`MapComponent`). Each tick it drains `cellsPerTick` cells: natural rock
  (`building.isNaturalRock`) is destroyed, optionally dropping its ore, and the
  thick mountain roof is removed with `roofGrid.SetRoof(c, null)`.
- Custom verb shows the blast radius while aiming.
- Mod settings: radius, drop resources and yield percent, also remove built
  roofs, blast damage, cells per tick.
- Craftable at the fabrication bench; keyed strings in
  `Languages/English/Keyed/MountainBreaker.xml`.
- Textures are placeholders: `Textures/MountainBreaker/MountainBreaker.png`
  (weapon) and `Charge.png` (projectile).

## Decisions

- Resources: dropped by default (a mining tool), at 50% of the normal yield.
  A setting turns drops off for the vaporise/terraforming behaviour. Plain rock
  (no `mineableThing`) drops nothing; chunks are not produced.
- Pawns and buildings: harmless by default (blast damage 0). A slider adds a
  real `Bomb` explosion of that damage at the impact point.
- Delivery: hand-held, range about 25, minimum range about 4, no line of sight
  required, 3 second warmup. Turret and orbital versions were left out.
- Hitch: cells are processed 30 per tick by default (adjustable 5 to 200).
- Roof: only roofs with `isThickRoof` are removed by default. A setting also
  removes built roofs in the radius.
- Radius: 5 cells by default (1 to 15), circular, same for rock and roof.

## Unverified

Only an in-game run can confirm:

- Vanilla defNames: `WeaponsRanged` (thing category), `FabricationBench`,
  `UnfinishedGun`, `Steel`, `Plasteel`, `ComponentSpacer`, `GeneralLaborSpeed`,
  `Crafting`, `Smith` (effecter), `Recipe_Machining`, `Shot_Autocannon`,
  `GunTail_Heavy`, `Explosion_Bomb`, `Bomb` damage def (also used in C# via
  `DamageDefOf.Bomb`), `TransparentPostLight` shader, and the stat names
  `MaxHitPoints`, `Mass`, `MarketValue`, `Flammability`, `WorkToMake`.
- That the projectile reaches or impacts a rock cell target and that the impact
  position used (`hitThing.Position` or the projectile cell) is the intended
  centre.
- That `Destroy(DestroyMode.Vanish)` on natural rock leaves the map, regions
  and fog consistent, and that `SetRoof(c, null)` on `RoofRockThick` behaves
  (roof drawing, fog, no collapse messages).
- That `building.mineableThing` / `EffectiveMineableYield` give sensible drops.
- The `MapComponent` is created for new and loaded maps automatically.
- Placeholder textures display and the weapon looks acceptable when held.
- Whether the verb counts as a usable ranged weapon for AI pawns.

## Not done

- Turret and orbital strike versions.
- Rock chunks from plain rock.
- Saving the queue: a half-drained blast is saved only as it was queued, so
  cells waiting when the game is saved are lost (the `BreakQueue` has no
  `ExposeData`).
- Research project, ammo or charge limits, trader stock tuning, other languages.
