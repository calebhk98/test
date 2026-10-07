# Room Optimizer

Pick a room and a goal, and the mod proposes (and optionally carries out) a
new furniture layout.

## The goal needs pinning down first

In vanilla, furniture position barely moves the room stats. Beauty and
wealth come from what is in the room, not where it is, and space counts free
cells. So "maximise impressiveness" mostly means "add better furniture", which
is a shopping list, not a layout.

Goals where position does matter:

- **Workshops**: shortest walking distance from stockpile to bench to output.
- **Hospitals**: beds next to the medicine shelf and vitals monitors.
- **Bedrooms / barracks**: fit the most beds while keeping every bed reachable.
- **Dining / rec**: chairs reachable, tables adjacent to the kitchen door.

## How it plugs into the game

- Read the room (`Room.Cells`, contained buildings) and the goal.
- Search layouts with a simple optimiser (greedy placement, then simulated
  annealing swaps), scoring each candidate with the goal function and a
  reachability check.
- Show the result as ghost blueprints. On confirm, place uninstall and
  reinstall designations so pawns move the furniture with normal jobs.

## Open questions

- Which goals matter to you most? The workshop case is the most useful and the
  easiest to score.
