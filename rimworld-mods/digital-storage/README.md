# Digital Storage

A storage network like Applied Energistics or Refined Storage: a core, drives
that hold thousands of items as data, and access points where items come out.

## How it plugs into the game

- **Core**: a powered building that is the network. Items stored in it are
  despawned into a `ThingOwner`, so 10,000 steel costs no map space and no ticks.
- **Drives**: slot into the core to raise capacity (by stack count or by
  item types, AE-style).
- **Input port**: a storage cell that accepts hauled items and pulls them into
  the network.
- **Access point / output port**: items come back onto the map here, for pawns
  to use.
- **Cables or wireless range**: decides which buildings are on the network.

## The hard part

Vanilla jobs only see items that are spawned on the map. A bill looking for
steel, a pawn looking for a meal, the colony resource counter: none of them
look inside a container. So either:

1. Harmony-patch the item searches (bill ingredient search, food search,
   resource counter) to see network contents and pull from the nearest
   access point, or
2. Keep a small "working stock" spawned at each access point and refill it
   from the network.

Option 1 is the real feature and the hard work. Option 2 is cheaper and leaks.

## Before building

Project RimFactory has a digital storage unit, and LWM's Deep Storage covers
dense storage. Look at how they solved the item-search problem before writing
it from scratch.
