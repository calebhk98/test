# Magical Crops

Crops whose harvest is something other than plain food.

## Ideas for crops

- **Healroot+**: grows herbal medicine at a better rate, or a better medicine tier.
- **Mood bloom**: a field of it gives a small "pretty flowers" mood buff to pawns who walk through.
- **Steel vine / stone gourd**: harvests steel or stone blocks slowly. Lets a colony with no ore survive.
- **Glow cap**: emits light like a lamp, so a dark cave farm lights itself.
- **Heat pepper / frost lily**: pushes room temperature up or down a little.
- **Mana bean**: a resource for the other magical items, if this grows into a bigger magic mod.

## How it plugs into the game

Most of this is XML. A crop is a `ThingDef` with a `<plant>` block
(`sowTags`, `growDays`, `harvestedThingDef`, `harvestYield`, `sowMinSkill`).
Steel vine, mood bloom and glow cap need no C#: change the harvested thing,
add a `CompGlower`, or give the plant beauty.

Effects that act on the area (mood aura, temperature) need a small `ThingComp`
ticking on the plant. Use a rare tick, since a field is hundreds of plants.

## Open questions

- Research-gated? A "Magical Botany" research project is the obvious gate.
- How rare are the seeds? Vanilla has no seeds, so the gate is research or a
  quest reward that unlocks the sow option.
- Balance: steel vine must be slower than mining or it replaces mining.

## Status

Builds with 0 errors, 0 warnings. Not run in game.

- Eight crops in `Defs/Plants.xml`, all gated behind research `MC_MagicalBotany` (`Defs/Research.xml`):
  - Healroot+ (herbal medicine, 11 per plant vs 7 for plain healroot, needs skill 8).
  - Mood bloom (no harvest, beauty 4, gives the `MC_PrettyFlowers` thought).
  - Steel vine (5 steel per 30 days) and stone gourd (8 granite blocks per 22 days).
  - Glow cap (`CompGlower`, radius 5, grows in the dark).
  - Heat pepper and frost lily (`CompHeatPusher`, +1.5 / -1.5 heat per second, limited by room temperature).
  - Mana bean (yields the new `MC_ManaBean` item, `Defs/Items.xml`).
- Mood bloom thought: `ThoughtWorker_MoodBloomNearby`, a situational thought. Counts mature blooms near the pawn: 1-4 gives +2, 5-12 gives +4, 13+ gives +6 mood. No ticking on the plants.
- Mod settings (`Settings.cs`, `DefTweaks.cs`): research gate on/off, steel/stone yield multiplier, heat multiplier, mood multiplier, bloom radius. Applied to the loaded defs at startup and when the settings window closes.
- English strings in `Languages/English/Keyed/MagicalCrops.xml`.

## Decisions

- Research-gated? Yes, `MC_MagicalBotany` (600 points, Neolithic, no prerequisite). Setting turns the gate off.
- How rare are the seeds? Sowing is unlocked by research alone, no quest reward or trade. Vanilla has no seeds, so this is the simplest honest gate.
- Balance of steel vine: 5 steel per 30 days per plant, plus harvest skill 8. Roughly 0.17 steel per plant per day. Multiplier setting 0.25 to 4. Not playtested.
- Mood aura: situational thought read at the game's normal interval rather than a ThingComp on every plant, since a field is hundreds of plants.
- Temperature: pure XML `CompHeatPusher`, no C#. Heat pepper stops heating above 24C, frost lily stops cooling below 16C. Outdoors the heat is effectively lost, so these are for greenhouses and caves.
- Mood bloom, glow cap, heat pepper and frost lily were given little or no yield (glow cap, pepper, lily give 1 mana bean) so they are decoration or utility, not food.
- Mana bean has no use yet. It is only a resource for a future magic mod.
- Harmony is not used. No patches were needed.

## Unverified

Vanilla defNames and fields (all need a run in the real game):
- Abstract parents: `PlantBase`, `ResourceBase`.
- ThingDefs: `MedicineHerbal`, `Steel`, `BlocksGranite`; thing category `Manufactured`.
- Stat defs: `MaxHitPoints`, `Beauty`, `MarketValue`, `Mass`.
- Research tab `Main`, tech level `Neolithic`, research screen position (1.0, 6.0) may overlap other projects.
- Plant tags `Ground`, `Hydroponic`, purpose `Misc`.
- Behaviour: that `CompHeatPusher` works on plants as intended, that glow cap grows in darkness with the `growMinGlow 0` setup (it may need to be lit once to start), that a plant with no `harvestedThingDef` (mood bloom) is accepted without errors, that `Graphic_Single` plant textures render well, and the mood thresholds feel right.
- Settings changes apply to defs live; confirm heat and mood changes take effect without restart.

## Not done

- Textures are placeholders: plain coloured shapes in `Textures/MagicalCrops/Plants/` and `Items/`. No immature or leafless graphics.
- No quest or trader seed source.
- No use for mana bean, no recipes.
- No wild spawning of these plants.
- No other-language files.
- `Source/MagicalCrops/obj/` is build output (check it is ignored).
