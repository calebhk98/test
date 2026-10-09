# Storyteller: The Hundred

A storyteller who wants you at 100 colonists and pushes until you get there.

## How it plugs into the game

A `StorytellerDef` in XML. Vanilla storytellers control recruiting through a
population curve (`populationIntentFactorFromPopCurve` in the Core defs;
confirm the exact field names against the 1.6 defs before copying). Vanilla
curves taper off far below 100; this one stays high until 100.

Extra `StorytellerComp`s raise the rate of people-arriving events: wanderer
joins, refugee quests, escape pods, prisoners worth recruiting.

Threats scale with colony size, so 100 colonists means raids sized for 100.

## Open questions

- After 100: does it relax, keep going, or flip to pure threat?
- Is there a reward or "win" at 100?
- 100 pawns is heavy on performance. Pairs well with `underground-animal-barn`
  freeing CPU from animals.

## Status

Builds with 0 errors, 0 warnings. Nothing has been run in the game.

- `Defs/StorytellerHundred.xml`: `SH_TheHundred` StorytellerDef. Population intent curve stays at 8 down to 3 until 99 colonists, then 0 at 100 and negative above, so vanilla "population increasing" incidents are favoured until the target.
- Vanilla comps for the rest: OnOffCycle (ThreatBig), RandomMain (ThreatSmall, Misc), Disease, two FactionInteraction (visitors, traders), RandomQuest (GiveQuest).
- Custom `StorytellerComp_Arrivals` (`Source/StorytellerHundred/Arrivals.cs`): extra WandererJoin and RefugeePodCrash incidents on a mean time of 2.5 days, shortened up to 3x when the colony is tiny, with the rate scaled by a setting.
- `GameComponent_Milestones`: letters at 25%, 50%, 75% and 100% of the target, only while this storyteller is active.
- `Settings.cs`: target, arrival rate multiplier, stop-after-target, milestone letters. Strings in `Languages/English/Keyed/`.
- Threats are sized by the game's own scaling from colonist count and wealth, so no threat code was written. Raids for 100 colonists come from that.
- Textures: `Textures/UI/Storyteller/TheHundredLarge.png` and `TheHundredTiny.png` are placeholder colored rectangles.

## Decisions

- After 100: relax. The population curve goes to zero and negative, and the extra arrival comp stops (setting "stop extra arrivals", default on; turn it off to keep arrivals at base pace). Threats and normal visitors continue. Not flipped to pure threat.
- Reward at 100: a positive letter only. No items, no victory screen.
- Performance: no change here; the README note about `underground-animal-barn` stands. The storyteller does not slow itself down at high counts.
- Colonist count is free colonists on all maps, caravans and transporters (`PawnsFinder.AllMapsCaravansAndTravellingTransporters_Alive_FreeColonists`), so children count and prisoners do not.

## Unverified

Field names on `StorytellerDef`, the comp properties classes, `IncidentDef` and `IncidentCategoryEntry` were all checked with apiquery. Meaning and units were not.

Vanilla def names used, only a game run confirms them:
- Incidents: `WandererJoin` (a field of `IncidentDefOf`, so very likely right), `VisitorGroup`, `TraderCaravanArrival` (both `IncidentDefOf` fields), `RefugeePodCrash` (NOT in `IncidentDefOf`, guessed from memory; a wrong name makes the comp skip it with a load error but not crash).
- Categories: `ThreatBig`, `ThreatSmall`, `Misc`, `DiseaseHuman`, `GiveQuest` (all `IncidentCategoryDefOf` fields).
- Comp class names written short (`StorytellerCompProperties_OnOffCycle` etc.) rely on the RimWorld namespace being searched; they exist per apiquery.
- `LetterDefOf.PositiveEvent` (checked in the assembly).

Behaviour not tested:
- Whether `populationIntentFactorFromPopAdaptDaysCurve` flat at 1 means "no adaptation effect"; the curve values I picked for the whole population/adaptation/points block are guesses at sensible shapes, not copies of vanilla.
- Whether the curve values give a strong enough push in practice; the real arrival rate comes from vanilla incident weights times this intent.
- `acceptFractionByDaysPassedCurve` on the ThreatBig cycle, and the `RandomQuest` comp running with only the fields set.
- `FiringIncident` constructor use and `CanFireNow` with parms from `GenerateParms` (compiles; unrun).
- The Core `ClassicIntro` comp was left out, so there is no scripted first-days sequence. Early threats are gated by `minDaysPassed` instead.

## Not done

- No reward beyond a letter, and no pure-threat mode after 100.
- No settings for threat strength; use the game's difficulty settings.
- No Harmony patches (the About.xml Harmony dependency is unused by this mod).
- No portrait art beyond placeholders.
