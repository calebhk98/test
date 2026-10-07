# Adaptive Raiders

Raiders learn from where their side died. Once a kill box has eaten a few
raids, later raids stop walking into it.

## How it plugs into the game

A `MapComponent` (or `WorldComponent`, so the lesson is per faction across
maps) keeps a "death heat map": each enemy death adds heat to the cells around
it and to the path the pawn walked in. Heat decays over time so the AI can
forget a defence you removed.

Two levels, from cheap to deep:

1. **Strategy choice.** When a raid is generated, if the heat map shows a
   known kill box, weight the raid strategy toward ones that ignore it:
   sappers, breachers, siege, or drop pods behind the line. Vanilla already
   has these strategies, so this is a Harmony patch on raid strategy
   selection plus a check of the heat map. Robust and cheap.
2. **Pathing.** Add the heat as extra cost to cells in pathfinding, so even
   assault raiders walk around the kill zone, or attack the wall next to it.
   RimWorld 1.6 changed pathfinding; check what per-cell cost hooks it
   exposes before designing around it.

Level 1 already makes kill boxes much weaker. Level 2 is where it gets hard.

## Open questions

- Per faction or global? Per faction is more believable ("the pirates learned").
- Should there be a way to fool them, such as a decoy kill box?
- Mechanoids too, or only humanlike factions?
