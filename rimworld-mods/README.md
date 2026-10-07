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

All of them target RimWorld 1.6 and depend on Harmony.

Built (first versions, compiled but not yet run in the game): every mod below
except the three on hold. Each mod's README has Status, Decisions, Unverified
and Not done sections; the Unverified list is what to watch for in the first
playtest.

On hold: `room-optimizer/` (existing code elsewhere), `task-ordering/` and
`job-subtasks/` (checking Fluffy's Work Tab first).

## Author name

The author and the packageId prefix live in `author.config`. Edit it, then run
`python3 tools/apply_author.py` to stamp every `About/About.xml`. Code never
hardcodes either: the Harmony id comes from the mod's packageId at runtime.

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

Needs the .NET SDK (8 or later). Each mod's C# project is in
`<mod>/Source/<ModName>/`, made from `tools/Mod.csproj.template`. It targets
.NET Framework 4.7.2 and compiles against `Krafs.Rimworld.Ref` (RimWorld's
public API as a NuGet package) and `Lib.Harmony`, so no game install is
needed to build:

```
cd <mod>/Source/<ModName> && dotnet build
```

The DLL lands in `<mod>/Assemblies/` and is committed, so a mod can be tested
without building. To test, symlink or copy the mod folder into RimWorld's
`Mods/` folder.

`tools/apiquery.sh <TypeName>` lists a RimWorld type's fields and methods from
the same reference assemblies, and `tools/apiquery.sh --find <text>` searches
type names. A Def's public fields are the XML tags it accepts.
