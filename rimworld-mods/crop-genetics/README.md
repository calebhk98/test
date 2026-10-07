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
