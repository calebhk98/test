# Task Ordering

Control the order pawns do jobs inside one work type. Example: sow every
growing zone before harvesting anything.

## How it plugs into the game

Each `WorkTypeDef` (Growing, Construction...) is made of `WorkGiverDef`s
(sow, harvest, cut plants...). Inside a work type the givers are tried in
order of `priorityInType`. This mod lets the player reorder or reprioritise
those givers, per colony or per pawn, through a UI tab.

## Before building

Fluffy's **Work Tab** already lets you set priorities per WorkGiver
(and by time of day). Check whether it, or a fork of it, is current for 1.6.
If it is, this mod might shrink to a preset ("farmers sow first") on top of it.

## Open questions

- Per pawn or per colony? Per pawn is more flexible and more clicking.
- A caution for the sow-before-harvest case: at the end of the growing season,
  delaying harvest risks frost killing ripe crops. Maybe the order flips
  automatically when a cold snap or winter is near.
