# Forklifts and Pallets

Forklifts move pallets, pallets hold many stacks, and hauling stops being one
pawn walking back and forth with 75 steel.

## Design options for the forklift

1. **Forklift as a pawn-like machine** (mechanoid-style): it hauls on its own
   with a huge carry capacity. Simplest, reuses the haul AI.
2. **Forklift as a vehicle a pawn drives**: more realistic, much harder. The
   Vehicle Framework mod exists for this; building on it saves months.
3. **Forklift as equipment**: a pawn "equips" it and gets a big carry and
   speed boost while hauling. Middle ground, no new AI.

Option 1 or 3 is the suggested start.

## Pallets

A pallet is a building (or minified item) with a `ThingOwner` holding several
stacks. Loading a pallet at one stockpile and unloading at another is one
haul job for the forklift instead of many for pawns.

## Open questions

- Do forklifts need roads/floors (slow on soil, fast on concrete)?
- Fuel or power?
- Is the goal fewer pawn hours hauling, or the look and feel of a warehouse?

## Status

A first playable version, built and compiled (0 errors, 0 warnings), never run in the game.

- **Pallet** (`Forklifts_Pallet`): an item, `Forklifts.Pallet`, with a `ThingOwner` that holds several stacks (default 8, settable 2 to 20). Craftable at the machining table for 30 steel. It only holds goods while a forklift operator carries it. It is saved and loaded with its contents, and any loaded pallet that ends up on the ground (operator downed, killed, job interrupted) spills its goods at once, so nothing is ever stranded inside a pallet.
- **Forklift rig** (`Forklifts_Forklift`): worn apparel on the belt layer. It gives +100 carrying capacity and marks the wearer as an operator. Craftable at the machining table (120 steel, 4 components, Crafting 6).
- **Work giver** `Forklifts_HaulPallet` (Hauling work type, priority above normal hauling): an operator picks the nearest free empty pallet, plans a batch from the colony's normal haulables list, and gets one job.
- **Job driver** `JobDriver_ForkliftHaul`: walk to the pallet, lift it, visit each stack in the batch and load it straight onto the pallet (the pallet travels with the operator, so there is no walking back and forth), drive to the destination once, and unload every stack into the storage there. If too few stacks can be grouped (default under 3) the work giver returns nothing and normal hauling runs as before.
- Batching rule: stacks must lie near the first stack (pickup radius, default 20) and have a better storage destination near the first stack's destination (unload radius, default 8), and the destination storage must accept them.
- Mod settings window: stacks per pallet, minimum stacks per trip, pickup radius, unload radius, load time per stack, and whether a forklift rig is required.
- No Harmony patches and no dependency on Vehicle Framework. (`About.xml` still lists Harmony as a dependency from the template; this mod does not use it, so the line can be dropped.)

## Decisions

- **Which forklift option: 3 (equipment), not 1 (pawn-like machine).** Option 1 needs a new race, pawn kind, work settings, spawning and upkeep, and a bug in any of those only shows up in a live game. Option 3 is one apparel def plus a work giver, and every part of it uses code paths that are well known (`WorkGiver_Scanner`, `JobDriver`, `Toils_*`). I could check all of it against the 1.6 API here, which is why I chose it.
- **The pallet is the real multiplier.** In vanilla a pawn can never carry more than one stack at a time, so a carrying capacity boost on its own would change nothing. The forklift rig is what lets a pawn run the pallet job; the pallet is what moves many stacks per trip.
- **Pallets load only while carried.** Stacks go on the pallet as the operator reaches them and come off at the destination, so the pallet is empty whenever it lies on the ground. That avoids stuck loaded pallets, storage-filter questions and save/load edge cases. Cost: no pre-loaded pallets sitting in a warehouse.
- **Unloading is one stop.** Every stack is placed in storage cells near the destination cell (as if the forks reach), instead of one walk per stack. If a stack cannot be placed, it drops near the operator and normal hauling picks it up.
- **Open question: floors.** No. Speed by floor type adds a per-pawn stat part and a lot of tuning for little gain.
- **Open question: fuel or power.** Neither. The rig is just worn, which keeps it out of the way of the colony's power and fuel logistics.
- **Open question: goal.** Fewer pawn hours hauling. The warehouse look is left to better textures later.
- Pallets and rigs need no research (research projects would depend on vanilla defs I cannot see).

## Unverified

Only a run in the real game confirms these.

- Vanilla defNames used: `TableMachining` (bench), `Steel`, `ComponentIndustrial`, thing categories `Manufactured` and `Apparel`, body part group `Waist`, apparel layer `Belt`, stats `Mass`, `Flammability`, `MaxHitPoints`, `WorkToMake`, `DeteriorationRate`, `EquipDelay`, `CarryingCapacity`, `GeneralLaborSpeed`, skill `Crafting`, work type `Hauling`, capacity `Manipulation`, effecter `Smith`, sound `Recipe_Machining`.
- Whether `recipeMaker` with `costList` on an apparel def yields a correct bench recipe in 1.6, and whether apparel needs an unfinished-thing def.
- The forklift rig has no `wornGraphicPath`, so it is expected to be invisible on the pawn. Not tested that this causes no render error.
- That the work giver outranks vanilla general hauling at priority 90 and is picked up by the Hauling work type.
- That `ThingOwner.TryAdd` on a just-despawned stack and `TryDrop` with a storage validator behave as expected, including stacking onto existing stacks in storage.
- That the carried pallet is drawn sensibly by the carry tracker and that jumping between toils (skipping stacks that vanished mid-trip) works without error.
- Reservation of the whole batch across several operators at once.
- Settings sliders layout.

## Not done

- Pre-loadable pallets that sit loaded in storage, and pallet storage shelves.
- A visible forklift on the map, and a worn texture for the rig.
- Speed by floor type, fuel or power, and any hauling skill or injury effects.
- Hauling to non-storage destinations (bills, containers, construction); only stockpile storage is batched.
- A research unlock and bench variety.
- Translations other than English.

## Textures (all placeholders)

`Textures/Things/Item/Forklifts_Pallet.png` and `Forklifts_Forklift.png` are plain colored shapes generated by a throwaway script.
