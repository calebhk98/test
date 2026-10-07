# Endless Siege

After the first raid, raids never stop. Instead of one big raid every few days,
a few more enemies walk onto the map every in-game hour.

## How it plugs into the game

- A `MapComponent` that switches on after the first raid ends (or arrives).
- Every 2,500 ticks (one in-game hour) it spends a small slice of raid points
  to generate a group with `PawnGroupMakerUtility` and drops it at a map edge.
- New arrivals join the existing raid `Lord` if one is active, so they behave
  as one ongoing assault rather than dozens of tiny separate raids.
- Points per hour grow with colony wealth and with how long the siege has run.

## Performance and fairness

- Cap the number of live enemies on the map; skip a wave while over the cap.
- Corpses and dropped gear will pile up fast. Option to rot or despawn enemy
  corpses after a while.
- Give a breathing window option ("quiet hours" or a short pause after a
  big wave) so it is hard, not hopeless. Or leave it off for "good luck" mode.

## Open questions

- One faction or a mix?
- Does it ever end (a win condition like "survive 60 days"), or is it forever?

## Status

Builds with 0 errors and 0 warnings. Implemented in `Source/EndlessSiege/`:

- `MapComponent_EndlessSiege` (one per map, saved): watches the player home map every 250 ticks for a hostile `LordJob_AssaultColony` lord with pawns. When the first raid is seen it switches on, sends a letter, and starts the clock.
- Once on, every `hoursBetweenWaves` (default 1 hour = 2,500 ticks) it generates a combat group with `PawnGroupMakerUtility.GeneratePawns`, spawns it near a random reachable map edge cell, and adds it to an existing siege lord of that faction, or makes a new `LordJob_AssaultColony` (no kidnap, no flee, no timeout) if none exists.
- Points per wave = `StorytellerUtility.DefaultThreatPointsNow` (wealth based) x fraction x growth (1 + growth/day, capped), minimum 60.
- Live enemy cap: a wave is skipped while hostile, non-prisoner, spawned pawns are at or over the cap.
- Corpse cleanup: hourly, destroys corpses of hostile-faction pawns older than the set lifetime (gear on them goes with them).
- Settings window (`EndlessSiegeMod`): all numbers below, via `Languages/English/Keyed/EndlessSiege.xml`.
- No Harmony patches and no XML defs; About.xml still lists Harmony as a dependency (left as stamped).

## Decisions

- Trigger: the siege starts when the first raid arrives, not when it ends (so there is no gap). Detected by scanning lords, so it catches any raid, vanilla or from other mods that use `LordJob_AssaultColony`.
- One faction or a mix: default is the faction of the first raid; a setting switches to a random hostile faction per wave.
- Does it end: forever by default. Setting "Siege ends after N days" (0 = never) stops reinforcements and sends a letter.
- Breathing window: off by default ("good luck" mode). Setting "quiet break after every N waves" with a length in hours.
- Defaults: wave = 12% of normal raid points, +5% per siege day, max x4, cap 40 live enemies, corpses removed after 12 hours.
- Dropped gear on the ground is not cleaned separately; vanilla forbidden-item and deterioration rules apply. Only corpses are removed.
- Only the player home map is affected.

## Unverified

Nothing has run in the game. Vanilla defs referenced by name (all compile-checked as C# fields, not run): `PawnGroupKindDefOf.Combat`, `RaidStrategyDefOf.ImmediateAttack`, `LetterDefOf.ThreatBig`, `LetterDefOf.PositiveEvent`. No vanilla textures or XML defNames used.

Behaviour to check in game:
- That the first raid is detected reliably (lord with `LordJob_AssaultColony`) and that sapper, siege-camp or drop-pod raids do not confuse it.
- That pawns added to an existing siege lord fight as one assault. (The `LordJob_AssaultColony` constructor argument order was checked against the 1.6 reference assemblies: faction, canKidnap, canTimeoutOrFlee, sappers, useAvoidGridSmart, canSteal, then breachers and canPickUpOpportunisticWeapons with defaults.)
- That settings values persist across reloads and the mod-settings scroll area is tall enough.
- Performance with many pawns on the map at the default cap.
- Factions that cannot field a group at low points: the wave is just skipped.

## Not done

- No textures (none needed).
- No cleanup of non-corpse dropped gear.
- No gizmo or UI showing siege status, wave count or time to next wave.
- Does not handle multiple player maps or non-home maps.
- Does not wait for the first raid to end before starting.
