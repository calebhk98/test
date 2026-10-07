# RimWorld mods

Each folder here is its own mod, laid out the way RimWorld loads one:

```
<mod>/
  About/About.xml        name, packageId, supported version, Harmony dependency
  Defs/                  XML defs (ThingDefs, WorkGiverDefs, StorytellerDefs...)
  Source/                C# project; build output goes to Assemblies/
  Textures/              PNGs, referenced by path from the defs
  Languages/English/Keyed/  translatable UI strings
  README.md              the design notes for that mod
```

All of them target RimWorld 1.6 and depend on Harmony. Each README is a design
sketch: the idea, how it plugs into the game, and the open questions. None has
code yet.

## The mods

| folder | idea | rough difficulty |
| --- | --- | --- |
| `magical-crops/` | crops that yield more than food | easy, mostly XML |
| `crop-genetics/` | crops with stats you breed up | medium |
| `storyteller-hundred/` | storyteller that wants 100 colonists | easy to medium |
| `trait-tower/` | building that adds good traits / removes bad ones nearby | easy to medium |
| `mountain-breaker/` | gun that deletes mountains and mountain roofs | medium |
| `endless-siege/` | after the first raid, enemies arrive every in-game hour | medium |
| `task-ordering/` | order jobs inside a work type (sow before harvest) | medium |
| `job-subtasks/` | split work types by subtask and skill (furniture vs walls) | medium |
| `remote-surrogate/` | pawn sleeps in a pod and drives a remote body | medium to hard |
| `underground-animal-barn/` | 200 animals simulated as one herd | hard |
| `adaptive-raiders/` | raiders learn to avoid kill boxes | hard |
| `forklifts/` | forklifts and pallets | hard |
| `digital-storage/` | AE2 / Refined Storage style networked storage | hard |
| `room-optimizer/` | auto-arrange a room's furniture | hard, and the goal needs pinning down |

`task-ordering/` and `job-subtasks/` both work at the WorkGiver level and could
become one mod. They are kept apart for now because they can ship separately.

## Building

Each `Source/` will hold a C# class library targeting .NET Framework 4.7.2,
referencing `Assembly-CSharp.dll` and `UnityEngine.CoreModule.dll` from
`RimWorldWin64_Data/Managed/` (do not copy them into the repo) and Harmony
from the `Lib.Harmony` NuGet package with its runtime excluded. The compiled
DLL goes to `<mod>/Assemblies/`. To test, symlink the mod folder into
RimWorld's `Mods/` folder.
