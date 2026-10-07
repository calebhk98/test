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
