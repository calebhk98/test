# Digital Storage

A storage network like Applied Energistics or Refined Storage: a core, drives
that hold thousands of items as data, and access points where items come out.

## How it plugs into the game

- **Core**: a powered building that is the network. Items stored in it are
  despawned into a `ThingOwner`, so 10,000 steel costs no map space and no ticks.
- **Drives**: slot into the core to raise capacity (by stack count or by
  item types, AE-style).
- **Input port**: a storage cell that accepts hauled items and pulls them into
  the network.
- **Access point / output port**: items come back onto the map here, for pawns
  to use.
- **Cables or wireless range**: decides which buildings are on the network.

## The hard part

Vanilla jobs only see items that are spawned on the map. A bill looking for
steel, a pawn looking for a meal, the colony resource counter: none of them
look inside a container. So either:

1. Harmony-patch the item searches (bill ingredient search, food search,
   resource counter) to see network contents and pull from the nearest
   access point, or
2. Keep a small "working stock" spawned at each access point and refill it
   from the network.

Option 1 is the real feature and the hard work. Option 2 is cheaper and leaks.

## Before building

Project RimFactory has a digital storage unit, and LWM's Deep Storage covers
dense storage. Look at how they solved the item-search problem before writing
it from scratch.

## Status

First playable version, compiles clean, never run in the game. Built in the scope order given:

1. **Core** (`DS_Core`, 2x2, powered). Items live despawned in a `ThingOwner<Thing>` (no map space, no ticks, `dontTickContents`). Up to 6 drives slot in; their `DriveExtension` values (item types, total items) add up to the core's limits, shown as "N item types, M total items". Power use rises with the number of drives. Unpowered core: `Online` is false, so it refuses input, refuses extraction and is not counted by bills; ports and access points on it do nothing. Items and drives are saved with `Scribe_Deep` (`storedItems`, `insertedDrives`). Destroying a core drops its drives and up to a setting's worth of stacks (default 300); the rest are lost.
2. **Input port** (`DS_InputPort`, 2x2 storage building). Haulers fill it like any stockpile. Its `Accepts` is patched so it only takes items an online core in range can store, and every rare tick (about 4 s) it absorbs what is in its cells, splitting stacks when the core is nearly full.
3. **Access point** (`DS_AccessPoint`, 3x2 storage building). Uses the working stock approach (below). Its storage filter chooses what it provides. Each cell is kept at one full stack of an allowed item that the network has, refilled every rare tick. Items in its cells that the filter no longer allows go back to the network.
4. **Network membership: wireless range** (default 30 cells, setting, ring shown when the core is selected). A port or access point works with every online core in range.
5. **UI**: a "Contents" tab on the core (status, item and type bars, drive count, scrolling list of item icon, name and count, sorted by count). Gizmos: Insert drive (pick a drive on the map, nearest free colonist hauls it in via `JobDriver_InsertDrive`), Eject drive (refused if the rest could not hold the contents). Dev mode adds two test gizmos (add a drive, add 1000 of an item).

Also: drives (small 10 types / 2,000 items, medium 25 / 8,000, large 60 / 30,000) with fabrication bench recipes, a research project, and a build category. "Do until X" bills count items in online cores (Harmony postfix on `RecipeWorkerCounter.CountProducts`, setting to disable).

Files: `Source/DigitalStorage/` (`DSMod.cs` settings, defs-of and extensions; `DSNet.cs` range and acceptance; `Building_DSCore.cs`; `Building_DSInputPort.cs`; `Building_DSAccessPoint.cs`; `ITab_DSContents.cs`; `JobDriver_InsertDrive.cs`; `Patch_CountProducts.cs` holds both Harmony patches), `Defs/DS_Misc.xml`, `DS_Drives.xml`, `DS_Buildings.xml`, `Languages/English/Keyed/DigitalStorage.xml`, placeholder textures.

Attribution: the patch pattern in `Patch_CountProducts.cs` and the idea of a `ThingOwner` cold store counted by bills follow Project RimFactory (MIT licence, `Patch_RecipeWorkerCounter_CountProducts.cs`, `Building_ColdStorage.cs`). The code is written fresh, adapted in shape only. Nothing from LWM Deep Storage (GPL) was used.

## Decisions

- **Item access: working stock (option 2), not search patches.** Reason: reliability. Real spawned items at the access point are found by every vanilla search (bills, construction delivery, meals, hauling) and every other mod's, with no patches that could miss a code path or break on a game update. The cost is the leak the design warned about: only what is stocked is visible, one stack per cell. Mitigation: the access point is big (6 cells), you choose what it holds, and the bill counter patch means "do until X" bills still see the whole network. A search-patching option 1 (bill ingredient search, food search, resource counter) is not done.
- **Network: wireless range, not cables.** Much simpler and needs no graph, rebuild or save data. Costs the "wire it up" feel.
- **Stock priority.** The access point defaults to Critical storage priority so haulers never carry its stock out to another stockpile and into the input port (which would loop forever). Side effect: loose items its filter allows get hauled into its free cells too. They are simply extra stock.
- **Input port priority** defaults to Normal with everything allowed. Raise it to funnel items in from stockpiles.
- **Capacity**: total items counts every item in every stack. Item types count distinct `ThingDef`s (qualities and materials share one type).
- **Not storable**: drives, corpses, packed (minified) furniture, anything not in the Item category.
- **Perishables**: stored items do not tick, so food does not rot in the core. This is on by default (setting "Allow perishable items" turns it off). Rot progress is kept and resumes when the item comes out.
- **Drive insertion** is a real hauling job with a colonist, not instant.
- **Core destroyed**: spill up to 300 stacks (setting, 0 to 2000), lose the rest, to avoid spawning tens of thousands of things.
- **Costs and research** are my numbers, not balanced.
- Settings: range, bill counting, perishables, spill limit.

## Unverified

Nothing has run in the game. Only an in-game run confirms:

- Vanilla defNames used: `BuildingBase` (parent), `Steel`, `ComponentIndustrial`, `ComponentSpacer`, `Gold`, `Plasteel`, `FabricationBench`, `MicroelectronicsBasics`, `Items` (ThingCategoryDef parent), `Root`, `Smith` (effecter), `Recipe_Machining` (sound), `GeneralLaborSpeed`, `Crafting`, `Heavy` (terrain affordance), `ITab_Storage`, `Designator_Cancel`, `Designator_Deconstruct`, stat names in `statBases`, and dev-gizmo item names (`Steel`, `WoodLog`, `Silver`, `MealSimple`).
- That the `Building_Storage.Accepts` postfix is hit for haul decisions (the method is an interface implementation).
- Hauling into the input port, absorption, and that haulers stop when the core is full or off.
- Access point refill: placement with `ThingPlaceMode.Direct`, stack top-up, return of unwanted items, no hauling loops with Critical priority.
- Drive insertion job and float menus, eject check, the ITab layout, power draw changes (`PowerOutput` set from `TickRare`).
- Save and load of a populated core (`Scribe_Deep` on two `ThingOwner<Thing>`), including items with quality, art or comps. Written to the usual pattern but not exercised.
- Behaviour when a core is destroyed, deconstructed, or a map is removed.
- All textures are generated placeholders (flat coloured boxes and arrows): `Things/Building/DS_*`, `Things/Item/DS_Drive*`, `UI/DS_Insert`, `UI/DS_Eject`.
- The research project's position (`researchViewX/Y`) and balance of costs, power and capacities.

## Not done

- Search patches (option 1) for ingredient, food and resource-counter lookups. The colony resource readout does not show network items.
- Cables / graph networks, multiple networks with separate membership, network priority between cores.
- Per-item stock targets at an access point (it keeps one full stack per allowed type per cell).
- Search, filter, and "take out N" in the contents tab.
- Wealth counting of stored items, trading from the network, caravans, mod-compat for other storage mods.
- Drive hot-swap while an extraction is mid-job, and a cap on how long one scan can take with very many stacks.
