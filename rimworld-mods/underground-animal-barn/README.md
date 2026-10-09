# Underground Animal Barn

Animals go into an "underground" barn building and stop being individual
ticking pawns. 200 cows cost about as much CPU as one building.

## How it plugs into the game

The barn is a `Building` that implements `IThingHolder` with a
`ThingOwner<Pawn>`, the same pattern vanilla uses for the cryptosleep casket.
Pawns inside a container are not on the map, so they do not path, do not
think, and do not tick on their own.

The barn then runs one cheap simulation on a long interval (say once per
in-game hour, which is 2,500 ticks) for the whole herd:

- **Food**: sum the herd's hunger rate, pull that much nutrition from a linked
  hopper or storage area. Not enough food means starvation applied to the herd
  as a whole.
- **Products**: read each species' `CompProperties_Milkable`,
  `CompProperties_Shearable` and `CompProperties_EggLayer` and produce milk,
  wool and eggs on the matching schedule into an output stockpile.
- **Ageing and breeding**: advance ages in bulk, roll births from the number
  of fertile male/female pairs.
- **Culling**: an option to auto-slaughter above a herd size, producing meat
  and leather the way butchering would.

Animals stored as real `Pawn` objects keep their identity, so taking one out
gives you back the same animal, aged correctly.

## Open questions

- Does it need upkeep (power, a handler pawn's work) so it is not free?
- Bonded animals: allowed in, or blocked so you do not lose track of them?
- Disease and fights are skipped entirely in the abstraction. Fine?
- Save size: 200 stored pawns still save as 200 pawns. If that matters,
  the herd could be stored as counts per species/age instead, at the cost of
  losing individual animals.

## Status

Builds with 0 errors and 0 warnings. Nothing has run inside the game.

What is implemented:

- `UB_UndergroundBarn`, a 3x3 powered building (`Building_UndergroundBarn : Building, IThingHolder`) holding
  a `ThingOwner<Pawn>`. It never calls `ThingOwnerTick` and sets `dontTickContents`, so stored animals do
  no per-tick work. The barn itself uses `tickerType Rare` (every 250 ticks) and only counts up to the
  herd interval; an empty barn does nothing at all.
- Storing: the "Store animals" gizmo targets animals one by one (repeat until right-click), "Store a whole
  kind" marks every tame animal of a kind on the map. Marked animals get a `UB_StoreAnimal` designation. A
  work giver (`Handling` work type) sends a colonist who walks to the animal, carries it to the barn and
  hands it in (`JobDriver_StoreAnimal`).
- Releasing: "Release animals" menu (all, or one kind) then a count slider. Animals appear next to the hatch.
  Destroying the building also lets everyone out.
- Herd simulation, once per interval (default 2500 ticks), in `BarnSimulation.cs`:
  - Ageing: `Pawn.TickMothballed(interval)` on each pawn (the game's own call for pawns off the map). The
    food bar is saved and restored around it so the barn stays the only thing that feeds them.
  - Food: total hunger per race (`FoodFallPerTickAssumingCategory`) plus a top-up to half a belly, taken from
    edible non-meal items within a radius of the barn that the race `CanEverEat` and that are not forbidden
    (hay, kibble, a hopper next to the hatch). Leftover nutrition from a part-used stack is kept as credit
    in a saved dictionary. A shortfall is shared by the whole race: animals with an empty belly gain
    Malnutrition, and die when it reaches lethal severity. Fed herds recover.
  - Products: from the species' own `CompProperties_Milkable`, `_Shearable` and `_EggLayer`, for adults of the
    right sex, scaled by how well the herd was fed. Fractions carry over between updates in the saved buffer
    and whole items are placed near the hatch in one batch.
  - Births: per race, fertile (reproductive life stage) males and females; litters expected =
    `min(females, males x femalesPerMale) x days / (gestationPeriodDays + rest days)`, litter size from the
    race's `litterSizeCurve`. Newborns are real pawns with Parent relations to their mother and father.
    Starving herds do not breed. Capacity caps births.
  - Culling: per-kind limit set from a slider (0 = off). Surplus males beyond a breeding quota go first, then
    the oldest adults, then the oldest juveniles. Bonded and named animals are never culled. Meat and leather
    come from the pawn's `MeatAmount` and `LeatherAmount` stats times a setting (default 70 percent).
- Save/load: the pawns are saved with `Scribe_Deep` inside the barn (same pattern as the casket), plus the
  interval counter, the cull limit and the fractional buffers. Display caches are rebuilt on demand.
- ModSettings window: herd interval, capacity, power requirement, ageing, breeding, products, bonded animals,
  females per male, rest days, cull yield, feed radius, starvation speed, reset button.
- A god-mode gizmo "DEV: run herd update" forces a pass for testing.

## Decisions

- Upkeep (open question 1): the barn draws 300 W and each herd update needs food lying near the hatch. With
  "requires power" on (default), no power means no breeding and no products, but animals still eat and can
  starve. No handler job is needed after the animals are in.
- Bonded animals (open question 2): blocked by default (setting "Allow bonded animals" turns it on). If
  allowed, the bond relation survives because the pawn is still saved in the barn, but the bond mood benefit
  of having the animal around is lost while it is stored.
- Disease and fights (open question 3): skipped, as the README proposed. Injuries and illnesses are frozen
  in storage (nothing heals or worsens except malnutrition).
- Save size (open question 4): kept as real pawns, so a 200-animal barn saves 200 pawns. Individual identity
  (names, training, bonds, age) is worth more than save size here, and counts per species could not give
  the same animal back. A smaller cap (setting) limits save growth.
- Interval: the README suggested 2500 ticks, which is the default; it is a slider from 250 to 15000 in steps
  of 250 because the barn is driven by the rare tick.
- Eggs: unfertilized eggs only. Egg-laying species do not hatch chicks in the barn; their herd only produces
  eggs. Fertilized eggs and hatching are left out to avoid chick floods on the floor.
- Output location: items are placed near the hatch's interaction cell, so a stockpile there collects them.
  There is no separate output stockpile link.
- Starved animals are killed through `Pawn.Kill` after being removed from the container, then kept as world
  pawns if the game wants them (they may be bonded); culled animals are discarded.
- Harmony is not used. The brief's Harmony id rule only applies when patching, and no patches are needed.

## Unverified

Everything below needs a run in the real game.

- Vanilla defNames used in XML: `BuildingBase` (parent), `Misc` (designation category), `Handling`
  (work type), `Manipulation` (capacity), `Steel`, `ComponentIndustrial`, stats `MaxHitPoints`,
  `WorkToBuild`, `Flammability`, terrain affordance `Heavy`, `CompProperties_Power` / `CompPowerTrader` /
  `CompProperties_Flickable`.
- Vanilla enum/def accesses in C#: `HediffDefOf.Malnutrition`, `PawnRelationDefOf.Bond` and `.Parent`,
  `StatDefOf.Nutrition`, `MeatAmount`, `LeatherAmount`, `MessageTypeDefOf.NegativeEvent`,
  `RejectInput`, `TaskCompletion`.
- That the 3x3 building is registered with the map as a thing holder, so its stored animals count in
  `MapPawns` unspawned lists like cryptosleep pawns do, and that no vanilla code ticks them.
- That `Pawn.TickMothballed` ages animals correctly and does not throw for tame animals with a player
  faction (wrapped in a try/catch that logs one warning).
- Carrying a walking, non-downed animal with `Toils_Haul.StartCarryThing` (vanilla does this when arresting
  or rescuing, but not for animals), and that animals do not run from the handler.
- `Pawn.Kill(null)` on a pawn that is in no map, `PassToWorld` and `Discard(true)` afterwards.
- Newborn generation (`PawnGenerationRequest` with fixed age 0 and the player faction) and removing the
  result from `WorldPawns` before adding it to the barn.
- That relations (bonds, parents) of stored pawns resolve after a save and reload, and that the world
  pawn cleanup does not touch pawns held by the barn.
- The malnutrition rate: the game's own rate is private, so the mod uses its own 0.4 severity per day
  (about 2.5 days fully unfed to lethal). Needs tuning.
- Wealth, animal-count alerts and the colony's animal limits probably do not count stored animals; not checked.
- Placeholder textures: all of them (`Things/Building/UndergroundBarn.png`, `UI/UndergroundBarn/Store`,
  `StoreKind`, `Cancel`, `Release`, `Cull`, `StoreMark`) are flat colored shapes.
- The 3x3 footprint, interaction cell offset (0,0,-2) and rotation behavior.

## Not done

- No research project; the building is available from the start in the Misc menu.
- No hopper-specific linking: food is any suitable item within the feed radius.
- Fertilized eggs and hatching, animal training, mood and bond effects while stored.
- Disease, injuries and fights in storage (skipped by design).
- A list tab of stored animals with per-animal release; release is by kind and count only.
- Animals dying of old age in storage is not modelled beyond what `TickMothballed` does.
- Animals on other maps or in caravans cannot be stored; only spawned tame animals on the barn's map.
- Translations other than English.
