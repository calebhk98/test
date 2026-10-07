# Remote Surrogate

A pawn lies down in a link pod and controls a remote body: a robot or a clone.
The body is weaker. If it dies, the real pawn wakes up in the pod with a mood
debuff and maybe a short stun.

## How it plugs into the game

- **Link pod**: a `Building` holding the operator pawn in a `ThingOwner`
  (cryptosleep casket pattern), so the operator is safe and off-map while linked.
- **Surrogate**: a separate pawn (a custom race or a mechanoid-style kind) that
  copies the operator's name and skills at reduced levels, with lower health
  and speed. It is the player's controllable colonist while the link lasts.
- **Death**: a Harmony postfix on `Pawn.Kill` (or a `HediffComp`/death hook on
  the surrogate) ejects the operator and gives them a thought like
  "Died remotely" (-10 mood, a few days).
- **Range**: link works on the home map; caravans or other maps could need a
  relay building.

## Open questions

- Skills: does experience the surrogate earns go back to the operator?
- Is the surrogate built (steel, components) or grown (clone vat, time)?
- Does the operator need food while linked? Cryptosleep says no; a pod that
  feeds them through a tube is a nice upkeep cost.
- If the pod loses power, does the link drop? It should, with a worse debuff.
