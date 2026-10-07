# Existing storage mods, checked before building (2026-10-07)

Read from cloned source of Project RimFactory Revived (PRF), LWM's Deep
Storage, Deep Storage Plus and Adaptive Storage Framework. GitHub issues and
Steam comments were not readable from here, so known bugs come from source
and commit history only. Worth a look in a browser before going far.

## Project RimFactory's "Digital Storage Unit"

- Maintained and on 1.6: last commit 2026-10-05, tag v2.9.5. MIT licence.
- **It is a big crate, not a network.** Stored items stay spawned on the map,
  all stacked in the unit's one cell (`Storage/Building_MassStorageUnit.cs`),
  with drawing and menus patched out. Vanilla searches find them for free
  because they are real map items. A full unit is up to 768 live Things.
- Capacity is a stack count. No drives, no item-type limits.
- I/O ports are bound to a unit through a menu. No cables, no range.
- Power: 10 W per stored stack. Unpowered, items stay reachable, so there is
  no "network down" state.
- Its "Cold Storage" variant does hold items despawned in a `ThingOwner`
  (10,000 stacks), but only bill "do until X" counts can see inside it
  (`Patch_RecipeWorkerCounter_CountProducts.cs`). Pawns reach it via ports only.
- Cannot be installed alone: the storage code depends on PRF's map component,
  settings and shared Harmony patches, so players get all of PRF (assemblers,
  conveyors, drones). The code itself (~2,300 lines in `Storage/`) could be
  extracted.

## Others

- **LWM's Deep Storage**: several items per cell, items stay spawned. GPL-3.0,
  so copying its code would make this mod GPL. No 1.6 branch in its repo.
- **Deep Storage Plus**: content defs for LWM-style storage. MIT, on 1.6.
- **Adaptive Storage Framework**: storage UI and rendering, no haul changes. MIT, on 1.6.
- No AE2 or Refined Storage style RimWorld mod was found.

## Conclusion

Build new. None of these does a core with drives, type limits, cables or
range, or keeps thousands of items off the map while still usable by pawns.
PRF's MIT code is a usable reference for the bill-count patch, `ThingOwner`
handling and port output placement, with attribution.
