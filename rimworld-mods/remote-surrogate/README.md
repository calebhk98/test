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

## Status

First playable version, builds with 0 errors and 0 warnings. Nothing has been run in the game.

- **Link pod** (`RS_LinkPod`, `Building_LinkPod`, 1x2, needs power, Misc build menu, behind the research `RS_RemoteSurrogates`). Right-click the pod with a colonist: "Link in to remote body". The colonist walks to the pod, waits a moment, and is stored in the pod's own `ThingOwner` (cryptosleep casket pattern). The stored pawn does not tick, so needs and hediffs freeze while linked.
- **Surrogate**: a freshly generated pawn of the operator's kind, gender, age, xenotype and ideo, with the operator's name (nickname becomes "Name (remote)"), backstories, traits, passions and work priorities. Skill levels are a share of the operator's (default 60 percent). It carries the `RS_SurrogateBody` hediff: 0.85x move speed, 0.8x global work speed, 1.5x incoming damage, no food/rest/joy needs, no random mental breaks. It spawns next to the pod as a normal player colonist.
- **Death**: a Harmony prefix on `Pawn.Kill` stops the surrogate from dying. No corpse is made, and none of the colonist-death side effects run (everyone else's "colonist died" thoughts, letters, tales, storyteller colonist-death counters). The link is ended one tick later by a `GameComponent`, so it never runs inside the health tracker's own state change. The operator is dropped at the pod's interaction cell with the "died remotely" thought (-10 mood, 3 days) and a short stun.
- **Power loss**: the pod draws 150 W idle and 650 W linked. If power is lost the pod warns, and after a grace period (default 1500 ticks, checked every rare tick) the link is cut: the operator is thrown out with the worse "link torn away" thought (-15, 4 days) and double the stun.
- **Pod destroyed**: `DeSpawn` ends the link first, then despawns. Destroyed by damage (`KillFinalize`) gives the "severed" debuff; any other removal (deconstruct, vanish, minify) is treated as a clean disconnect. The operator is never lost with the pod.
- **Disconnect**: a gizmo on the pod and on the surrogate ends the link safely with no debuff.
- **Save/load**: the operator is deep-saved in the pod; the pod and the surrogate reference each other (`Scribe_References`); the hediff also saves pending-end state, the ids of the gear the body was generated with, and the experience it has earned. A pending end that was queued when the game was saved is finished by the pod's next rare tick. A pod that loads with an operator but no valid surrogate treats the body as lost and wakes the operator.
- **Cleanup**: ending a link drops carried items, inventory, equipment and any apparel the player put on the body; the gear the body was generated with is destroyed. The body is removed with `Destroy` and `Discard`, which leaves no corpse.
- **Settings** (mod options): skill share, experience share, pod recharge days, power grace ticks, stun ticks.

## Decisions

- **Skills earned by the surrogate**: yes, half goes back (setting, default 50 percent). A `SkillRecord.Learn` postfix records the experience the body earns, and it is handed to the operator when the link ends, for any reason.
- **Built or grown**: neither per link. The pod itself is built (steel and components). A body is made instantly on link-in, but after a lost body the pod recharges for a day (setting) before it can be used again, standing in for regrowing it. A clean disconnect only blocks the pod for a few seconds.
- **Food while linked**: the operator needs none (frozen), and the surrogate has no food or rest needs. The upkeep cost is power: 650 W while linked against 150 W idle.
- **Pod loses power**: the link drops after a grace period, with the worse debuff and a longer stun.
- **Range**: same map only. If the surrogate leaves the pod's map or joins a caravan, the link is cut at the next rare tick (severed debuff). A relay building is not implemented.
- **Mood debuff and stun**: -10 for 3 days and 180 ticks for a lost body; -15 for 4 days and 360 ticks for severed. Mood values and durations are in XML; the stun is a setting.
- **Death handling**: block `Kill` rather than let it happen and clean up, because that is the only way to keep a colonist death out of the storyteller, thoughts and letters.

## Unverified

Only a run in the real game can confirm these.

- Vanilla defNames used in XML: `BuildingBase` (parent), `Steel`, `ComponentIndustrial`, `Misc` (designation category), stats `MoveSpeed`, `WorkSpeedGlobal`, `IncomingDamageFactor` (the last one is confirmed as a `StatDefOf` field, the first two too, but the XML names are assumed to match), needs `Food`, `Rest`, `Joy`, stat `MaxHitPoints`, `WorkToBuild`, `Flammability`, the default research tab, and the vanilla translation keys `NoPower` and `NoPath`.
- That `thoughtClass` `Thought_Memory` plus `durationDays` makes a working memory thought, and that `disablesNeeds` on a hediff stage really removes Food/Rest/Joy from a human.
- That `blocksMentalBreaks` on the stage stops random mood breaks for the body.
- That the Kill prefix is enough: other death paths that skip `Pawn.Kill` (for example a destroy call from another mod) would still remove the body, and the pod then treats it as lost on its next rare tick.
- That generating a pawn with the operator's `kindDef` works when that kind is unusual (a modded or non-colonist kind). The fallback is `PawnKindDefOf.Colonist` only when the kind is null.
- Pawn generation with `forcedXenotype`, `fixedIdeo` and gear: gear tracking assumes generated apparel, equipment and inventory are present right after `GeneratePawn`.
- That `Discard(true)` after `Destroy` leaves no dangling references or world-pawn entries, and that a spawned pawn with a player faction does not trigger a "new colonist" side effect.
- The colonist bar and wealth: the surrogate counts as a colonist while linked, so it will raise storyteller raid points a little, and the operator also still shows on the bar.
- Float menu entry, job flow, the interaction-cell offset `(0,0,-1)` and rotation, and the drawn size of the placeholder texture.
- Mod-compatibility with anything that patches `Pawn.Kill` earlier (Harmony prefix ordering was not set).

Textures are placeholders drawn by a throwaway script: `Textures/Things/Building/RS_LinkPod.png` (a blue-grey pod shape) and `Textures/UI/RS_Disconnect.png` (a round disconnect icon).

## Not done

- A relay building or range limit beyond "same map".
- Caravan travel for surrogates (they are cut off instead), and blocking them from the form-caravan dialog.
- A body cost per link (materials) or a visible growth timer; only a cooldown exists.
- Operators other than humanlike colonists, multiple operators per pod, and a surrogate for animals or mechs.
- Copying genes beyond the xenotype, apparel, hair and body type; the body looks like a generated pawn, not a visual clone. Appearance copy would be a nice follow-up.
- A research prerequisite chain; the single research project has no prerequisites.
- Translations other than English.
