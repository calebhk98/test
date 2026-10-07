# Underground Animal Barn

Animals go into an "underground" barn building and stop being individual
ticking pawns. 200 cows cost about as much CPU as one building.

## How it plugs into the game

The barn is a `Building` that implements `IThingHolder` with a
`ThingOwner<Pawn>`, the same pattern vanilla uses for the cryptosleep casket.
Pawns inside a container are not on the map, so they do not path, do not
think, and do not tick on their own.

The barn then runs one cheap simulation on a long interval (say once per
in-game hour, which is 2,500 ticks) for the whole herd:

- **Food**: sum the herd's hunger rate, pull that much nutrition from a linked
  hopper or storage area. Not enough food means starvation applied to the herd
  as a whole.
- **Products**: read each species' `CompProperties_Milkable`,
  `CompProperties_Shearable` and `CompProperties_EggLayer` and produce milk,
  wool and eggs on the matching schedule into an output stockpile.
- **Ageing and breeding**: advance ages in bulk, roll births from the number
  of fertile male/female pairs.
- **Culling**: an option to auto-slaughter above a herd size, producing meat
  and leather the way butchering would.

Animals stored as real `Pawn` objects keep their identity, so taking one out
gives you back the same animal, aged correctly.

## Open questions

- Does it need upkeep (power, a handler pawn's work) so it is not free?
- Bonded animals: allowed in, or blocked so you do not lose track of them?
- Disease and fights are skipped entirely in the abstraction. Fine?
- Save size: 200 stored pawns still save as 200 pawns. If that matters,
  the herd could be stored as counts per species/age instead, at the cost of
  losing individual animals.
