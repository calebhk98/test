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
