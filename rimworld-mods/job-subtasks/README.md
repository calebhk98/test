# Job Subtasks

Split a work type into subtasks and assign them by pawn and by skill.
Example: the level-20 builder does beds and furniture (where quality matters),
and the level-10 builder does walls, floors and repairs.

## How it plugs into the game

Construction in vanilla is a few WorkGivers (deliver resources, build frames,
repair, deconstruct...). Building a bed and building a wall are the same
giver, so splitting by work giver is not enough.

This mod adds a filter on top: categories of buildable things, decided by the
thing's `designationCategory` (Furniture, Structure, Floors, Production...)
or by whether it has quality (`CompQuality`). A Harmony patch on the
construct-frame work giver skips frames that do not match the pawn's
allowed categories.

UI: a per-pawn panel of category checkboxes, plus a rule like "quality items
only for the colony's best builder".

Same idea extends to other work types: crafting (weapons vs. components),
cooking (fine meals vs. simple), doctoring (surgery vs. tending).

## Overlap

`task-ordering/` also works at the WorkGiver level. These two could become one
mod once both exist.

## Open questions

- Should a frame wait for the right pawn forever, or fall back to anyone after
  some hours? Waiting forever can stall a build if the master builder is sick.
