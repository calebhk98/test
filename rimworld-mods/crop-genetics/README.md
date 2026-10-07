# Crop Genetics

Every crop has stats. Good plants are saved and replanted, and the farm gets
better over generations.

## Stats per strain

- Yield (multiplier on `harvestYield`)
- Growth speed (multiplier on growth rate)
- Hardiness (temperature range, blight resistance)
- Nutrition or quality of the harvested item
- Maybe a "mutation" chance per harvest

## How it plugs into the game

Per-plant data lives in a `ThingComp` added to every sowable plant by an XML
patch, so modded crops get it too. Growth and yield are hooked with Harmony
on `Plant.GrowthRate` and `Plant.YieldNow()`.

The hard part is where genetics live between plantings. Vanilla has no seeds:
a pawn sows whatever the grow zone says. Two options:

1. **Strain on the grow zone.** `Zone_Growing` gets a "strain" setting next to
   its plant setting. The colony keeps a library of strains, and harvesting
   a field rolls a chance to improve or mutate its strain. Simple, no new items.
2. **Seed items.** Harvesting drops seeds carrying the stats; sowing consumes
   them. More realistic, much more hauling, and it touches the sow job.

Option 1 is the suggested start.

## Open questions

- Is there a cap, or can yield climb forever?
- Do traders sell strains?
- Should cross-breeding two fields be a thing (adjacent zones mixing)?

## Status

Builds with 0 errors and 0 warnings. Nothing has been run in the game.

Implemented (option 1, strain on the grow zone):
- Each `Zone_Growing` has a strain (yield multiplier, growth multiplier, hardiness 0 to 1, generation count) for its current crop. Changing the zone's crop gives a fresh base strain.
- Harmony patches: `Plant.GrowthRate` (x growth multiplier), `Plant.YieldNow` (x yield multiplier, never below 1 if the vanilla yield was positive), `Plant.GrowthRateFactor_Temperature` (hardiness pulls a poor temperature factor toward 1).
- Each plant harvested in a zone rolls a small chance to improve one stat, and a smaller chance to mutate one stat (up or down).
- Zone gizmo "Strain": save the zone's strain to the colony library, reset to base, or apply a saved strain (for the same crop) to the zone. The zone inspect text shows the current strain.
- Strains and the library are saved in a `GameComponent` (`StrainLibrary`), keyed by zone ID.
- Mod settings for chances, step sizes and caps.
- Works for modded crops, because it keys on any plant growing in a growing zone, with no per-def patch.

Files: `Source/CropGenetics/{Strain,StrainLibrary,Patches,CropGeneticsMod}.cs`, `Languages/English/Keyed/CropGenetics.xml`, `Textures/CropGenetics/UI/Strain.png` (placeholder), `Assemblies/CropGenetics.dll`. There are no Defs.

## Decisions

- Option 1 chosen, as suggested. No blocker found.
- Per-plant `ThingComp` was dropped. A plant's strain is looked up from the grow zone it stands in. Simpler, no XML patch of every crop, and no save-compat risk. Consequence: changing a zone's strain affects plants already growing in it, not only new sowings.
- Cap: yes. Yield and growth multipliers are clamped to 0.5x to 2x, hardiness to 0 to 1 (all settings).
- Traders selling strains: not implemented. Library strains only come from your own fields.
- Cross-breeding of adjacent zones: not implemented. Partial substitute: the library lets you copy a good strain into other zones.
- Defaults: improve chance 2% per harvested plant, +1% to one random stat (yield, growth, hardiness); mutation chance 0.4%, swing up to +/-8%; each counts as a generation. A big field therefore improves steadily but slowly.
- Applying a library strain copies it, so the zones then evolve separately.

## Unverified

- Only in-game testing confirms: that `Plant.PlantCollected` is called on a normal harvest while `HarvestableNow` is still true (this is the hook that rolls improvements), that Harmony patching the property getters `GrowthRate` and `GrowthRateFactor_Temperature` takes effect (if the game inlines them it will not), and that `Zone_Growing.GetGizmos` / `GetInspectString` patches show the button and line.
- `ZoneAt(plant.Position)` as the plant-to-zone link, and `Plant.sown` being true for crops sown by pawns (not for map-generated or pre-existing plants, which get no bonus).
- Texture path `CropGenetics/UI/Strain` (placeholder green circle, `Textures/CropGenetics/UI/Strain.png`). No vanilla defNames or textures are used.
- Save/load round trip of the zone-strain dictionary, and loading mid-game on an existing save.
- Whether the harvest rate of improvement feels right.

## Not done

- Nutrition/quality stat, blight resistance, trader strains, cross-breeding between zones, per-plant genetics, option 2 (seed items), a strain library management window, strain names editable by the player.
