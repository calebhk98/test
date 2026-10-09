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

## Status

Built against the 1.6 reference assemblies, 0 warnings, 0 errors. Nothing has run in the game.

- **Death heat map.** `DeathHeatMap` is a `MapComponent`. A prefix on `Pawn.Kill` records the death of a hostile, non-player pawn on a player home map, when the killer is the player or unknown (traps, fire). Heat goes to the cells within a radius of the death (linear falloff) and, more weakly, to the last ~12 positions the pawn walked (sampled every 45 ticks, so the path in is part of the lesson). Heat is kept per faction, decays on a half-life every 2500 ticks, and is saved with the map.
- **Level 1, strategy.** Postfixes on `IncidentWorker_Raid.ResolveRaidStrategy` and the `IncidentWorker_RaidEnemy` override. If the faction's peak cell heat reaches the learning threshold, the strategy is swapped, with a chance that rises with the heat, for one of `ImmediateAttackSappers`, `ImmediateAttackBreaching` or `Siege` that passes its own `CanUseWith` and minimum points check. A strategy already set by a quest or the caller is left alone. A second postfix on `ResolveRaidArriveMode` sometimes swaps a walk-in for a drop arrival the chosen strategy allows.
- **Level 2, pathing.** Implemented. 1.6 does have a clean per-cell hook, see below.
- **Settings** (mod options): both levels on or off, mechanoids on or off, deaths before learning, avoid chance range, drop pod chance, half-life in days, heat radius, path cost per heat, path cost cap.

### What 1.6 pathfinding exposes (level 2)

Pathfinding is now job based (`PathFinder`, `PathRequest`, `PathFinderMapData`). Found with `apiquery.sh`:

- `PathFinder.CreateRequest(..., IPathGridCustomizer customizer)` has two overloads and both take a customizer.
- `PathRequest.IPathGridCustomizer` has one member, `NativeArray<ushort> GetOffsetGrid()`, and is `IDisposable`. A per-cell offset grid is exactly a per-cell extra cost. Vanilla's own `UsedRectPathGridCustomizer` implements it, so it is a real, used extension point and not a private detail.
- `PathFinderCostTuning` (per-request costs for danger, doors, walls, water) has no per-cell input, so it is not the hook.
- `PathGrid` computes static costs from things; patching it would change cost for every pawn including colonists, so it was not used.

So a Harmony prefix on both `CreateRequest` overloads fills in `customizer` when it is null, for hostile non-player pawns on a map where their faction has heat. The offset grid is `heat * costPerHeat`, capped. Raiders still go to their target; the cost only makes them prefer a way round, so a kill box that is the only route is still walked.

Memory: the grid is a persistent `NativeArray<ushort>` the size of the map, one per faction per map, built on request and rebuilt at most every 250 ticks when the heat changed. The wrapper handed to the pathfinder has a no-op `Dispose`, because the grid is shared. A replaced grid is freed 600 ticks later, so a job still reading it is safe. All grids are freed in `MapRemoved`.

## Decisions

- **Per faction or global?** Per faction, per map. The pirates learn, the tribals do not. Heat is keyed by cell, so it only makes sense on the map where it was earned, which is why it is a `MapComponent` and not a `WorldComponent`.
- **Decoy kill box?** No special mechanic, because none is needed: heat comes only from real deaths, so a cheap bait position that kills a few raiders teaches them to fear it, and heat fades, so after the half-life (default 20 days) they come back. Not built: a way to deliberately fake heat.
- **Mechanoids?** Off by default, a setting turns them on. Insects never learn. Hidden factions and the player never learn.
- **What counts as a kill box?** The hottest single cell, divided by the "deaths before learning" setting (default 3). One death puts about 1 on its cell and less around it, and trail heat overlaps on a funnel, so about three deaths in one spot trips it. Scattered deaths across a map do not.
- **Strength of the lesson.** Chance to switch goes from 40% at the threshold to 90% at three times the threshold. Drop pod chance is 20%, only when a lesson exists.
- **Drop pods.** Chosen by arrival mode, not strategy, because in vanilla drops are arrival modes. Only modes the chosen strategy lists are eligible.
- **Pathing strength.** 40 cost per unit of heat, capped at 600 per cell. Normal walking is about 13 per cell, so a hot cell is a strong deterrent but not a wall.

## Unverified

Everything below needs a run in the real game.

- Vanilla `RaidStrategyDef` defNames: `ImmediateAttackSappers`, `ImmediateAttackBreaching`, `Siege`. Missing names are skipped silently; if none exist, level 1 does nothing.
- That `ResolveRaidStrategy` runs before `ResolveRaidArriveMode`, and that `IncidentWorker_RaidEnemy.ResolveRaidStrategy` calls the base in some cases (the code handles both, but the order is assumed).
- That swapping `parms.raidStrategy` after resolution is safe for later steps, and that calling `TryResolveRaidSpawnCenter` again after changing the arrival mode gives a sensible drop location.
- That vanilla pawn path requests reach `PathFinder.CreateRequest` with a null customizer for ordinary raiders. If the follower builds requests another way, level 2 silently does nothing.
- That `GetOffsetGrid` is added to the per-cell cost and indexed by `CellIndices.CellToIndex`, with length `NumGridCells`. The reference assemblies have no method bodies, so units and indexing are inferred from the type signature only. If costs look wrong, check this first.
- That the path job does not call `Dispose` on a customizer it did not create (mine is a no-op either way) and does not hold the array longer than 600 ticks.
- That `Pawn.Kill` is reached for every death on a player home map (including deaths by traps and fire) and that the killing instigator check matches your expectations.
- No textures are used. No vanilla defs are referenced except the three strategy names above.
- Performance of the trail sampler on very large raids. It scans spawned pawns every 45 ticks.

## Not done

- No in-game visualisation of the heat map (a dev overlay would help tuning).
- No decoy item or way to inject heat on purpose.
- Pathing only changes costs. Raiders are not told to attack the wall next to the kill zone; that would need a lord job change.
- Heat is not shared across maps or quests.
- Trails are not saved; a reload loses the path part of a lesson not yet turned into a death.
