# Forklifts and Pallets

Forklifts move pallets, pallets hold many stacks, and hauling stops being one
pawn walking back and forth with 75 steel.

## Design options for the forklift

1. **Forklift as a pawn-like machine** (mechanoid-style): it hauls on its own
   with a huge carry capacity. Simplest, reuses the haul AI.
2. **Forklift as a vehicle a pawn drives**: more realistic, much harder. The
   Vehicle Framework mod exists for this; building on it saves months.
3. **Forklift as equipment**: a pawn "equips" it and gets a big carry and
   speed boost while hauling. Middle ground, no new AI.

Option 1 or 3 is the suggested start.

## Pallets

A pallet is a building (or minified item) with a `ThingOwner` holding several
stacks. Loading a pallet at one stockpile and unloading at another is one
haul job for the forklift instead of many for pawns.

## Open questions

- Do forklifts need roads/floors (slow on soil, fast on concrete)?
- Fuel or power?
- Is the goal fewer pawn hours hauling, or the look and feel of a warehouse?
