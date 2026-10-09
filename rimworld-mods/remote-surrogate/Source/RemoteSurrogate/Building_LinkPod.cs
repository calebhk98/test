using System.Collections.Generic;
using System.Linq;
using RimWorld;
using RimWorld.Planet;
using UnityEngine;
using Verse;
using Verse.AI;

namespace RemoteSurrogate
{
    public class Building_LinkPod : Building, IThingHolder
    {
        protected ThingOwner innerContainer;
        public Pawn surrogate;
        private int cooldownUntilTick;
        private int powerOffSinceTick = -1;
        private bool ending;

        private CompPowerTrader powerComp;

        public Building_LinkPod()
        {
            innerContainer = new ThingOwner<Thing>(this, false, LookMode.Deep);
        }

        public Pawn Operator => innerContainer.Count > 0 ? innerContainer[0] as Pawn : null;
        public bool Occupied => innerContainer.Count > 0;
        private bool PowerOn => powerComp == null || powerComp.PowerOn;
        private int CooldownTicksLeft => Mathf.Max(0, cooldownUntilTick - Find.TickManager.TicksGame);

        // ---- holder plumbing -------------------------------------------------

        public ThingOwner GetDirectlyHeldThings() => innerContainer;

        public void GetChildHolders(List<IThingHolder> outChildren)
        {
            ThingOwnerUtility.AppendThingHoldersFromThings(outChildren, GetDirectlyHeldThings());
        }

        public override void ExposeData()
        {
            base.ExposeData();
            Scribe_Deep.Look(ref innerContainer, "innerContainer", this);
            Scribe_References.Look(ref surrogate, "surrogate");
            Scribe_Values.Look(ref cooldownUntilTick, "cooldownUntilTick");
            Scribe_Values.Look(ref powerOffSinceTick, "powerOffSinceTick", -1);
            if (Scribe.mode == LoadSaveMode.PostLoadInit && innerContainer == null)
                innerContainer = new ThingOwner<Thing>(this, false, LookMode.Deep);
        }

        public override void SpawnSetup(Map map, bool respawningAfterLoad)
        {
            base.SpawnSetup(map, respawningAfterLoad);
            powerComp = GetComp<CompPowerTrader>();
            UpdatePowerUse();
        }

        private void UpdatePowerUse()
        {
            if (powerComp == null) return;
            float use = Occupied ? 650f : 150f;
            powerComp.PowerOutput = -use;
        }

        // ---- entering ---------------------------------------------------------

        public AcceptanceReport CanEnter(Pawn p)
        {
            if (p == null || !p.RaceProps.Humanlike || p.Faction != Faction.OfPlayer)
                return false;
            if (Hediff_SurrogateBody.Of(p) != null) return "RS_CantSurrogate".Translate();
            if (Occupied) return "RS_PodOccupied".Translate();
            if (!PowerOn) return "NoPower".Translate();
            if (CooldownTicksLeft > 0) return "RS_PodRecharging".Translate(CooldownTicksLeft.ToStringTicksToPeriod());
            if (p.Downed || p.Dead) return false;
            return true;
        }

        public override IEnumerable<FloatMenuOption> GetFloatMenuOptions(Pawn selPawn)
        {
            foreach (FloatMenuOption o in base.GetFloatMenuOptions(selPawn)) yield return o;
            if (selPawn.Faction != Faction.OfPlayer || !selPawn.RaceProps.Humanlike) yield break;

            AcceptanceReport report = CanEnter(selPawn);
            string label = "RS_EnterPod".Translate();
            if (!report.Accepted)
            {
                if (!report.Reason.NullOrEmpty())
                    yield return new FloatMenuOption(label + " (" + report.Reason + ")", null);
                yield break;
            }
            if (!selPawn.CanReach(this, PathEndMode.InteractionCell, Danger.Deadly))
            {
                yield return new FloatMenuOption(label + " (" + "NoPath".Translate() + ")", null);
                yield break;
            }
            yield return new FloatMenuOption(label, () =>
            {
                Job job = JobMaker.MakeJob(RSDefOf.RS_EnterLinkPod, this);
                selPawn.jobs.TryTakeOrderedJob(job, JobTag.Misc);
            });
        }

        /// <summary>Called by the job driver once the operator has walked to the pod.</summary>
        public bool TryStartLink(Pawn op)
        {
            if (!CanEnter(op).Accepted || !Spawned) return false;

            bool wasSelected = Find.Selector.IsSelected(op);
            Pawn s = SurrogateFactory.Make(op, this);

            op.DeSpawn();
            if (!innerContainer.TryAdd(op, false))
            {
                // Could not store the operator. Put them back and throw the body away.
                GenSpawn.Spawn(op, InteractionCell, Map);
                DisposeSurrogate(s);
                return false;
            }
            surrogate = s;
            powerOffSinceTick = -1;
            IntVec3 cell = CellFinder.StandableCellNear(InteractionCell, Map, 3f);
            if (!cell.IsValid) cell = InteractionCell;
            GenSpawn.Spawn(s, cell, Map);
            UpdatePowerUse();
            if (wasSelected)
            {
                Find.Selector.ClearSelection();
                Find.Selector.Select(s, false);
            }
            Messages.Message("RS_LinkEstablished".Translate(op.LabelShortCap), s, MessageTypeDefOf.PositiveEvent, false);
            return true;
        }

        // ---- ending -----------------------------------------------------------

        /// <summary>Called by the Kill patch: remember the end, let a game component finish it next tick.</summary>
        public void QueueEnd(LinkEndReason reason)
        {
            var h = Hediff_SurrogateBody.Of(surrogate);
            if (h == null) { EndLink(reason); return; }
            if (h.endPending) return;
            h.endPending = true;
            h.pendingReason = reason;
            RSManager.Enqueue(h);
        }

        public void EndLink(LinkEndReason reason)
        {
            if (ending) return;
            ending = true;
            try
            {
                Pawn op = Operator;
                Pawn s = surrogate;
                surrogate = null;

                if (s != null && !s.Destroyed)
                {
                    if (op != null) PassBackExperience(op, s);
                    bool wasSelected = Find.Selector.IsSelected(s);
                    DisposeSurrogate(s);
                    if (wasSelected && op != null) selectAfter = true;
                }

                if (op != null)
                {
                    Map map = Map;
                    if (map != null)
                    {
                        IntVec3 cell = InteractionCell;
                        innerContainer.TryDrop(op, cell, map, ThingPlaceMode.Near, out Thing _);
                    }
                    else
                    {
                        innerContainer.TryDrop(op, ThingPlaceMode.Near, out Thing _);
                    }
                    if (op.Spawned) ApplyWakeEffects(op, reason);
                    if (selectAfter && op.Spawned)
                    {
                        Find.Selector.ClearSelection();
                        Find.Selector.Select(op, false);
                    }
                }
                selectAfter = false;

                if (reason != LinkEndReason.Disconnected)
                    cooldownUntilTick = Find.TickManager.TicksGame + (int)(RemoteSurrogateMod.Settings.cooldownDays * 60000f);
                else
                    cooldownUntilTick = Find.TickManager.TicksGame + 250;
                powerOffSinceTick = -1;
                UpdatePowerUse();
            }
            finally
            {
                ending = false;
            }
        }

        private bool selectAfter;

        private void ApplyWakeEffects(Pawn op, LinkEndReason reason)
        {
            if (reason == LinkEndReason.Disconnected) return;
            ThoughtDef thought = reason == LinkEndReason.BodyLost ? RSDefOf.RS_DiedRemotely : RSDefOf.RS_LinkSevered;
            op.needs?.mood?.thoughts?.memories?.TryGainMemory(thought);
            int stun = RemoteSurrogateMod.Settings.stunTicks;
            if (reason != LinkEndReason.BodyLost) stun *= 2;
            if (stun > 0) op.stances?.stunner?.StunFor(stun, this, false, false);
            string key = reason == LinkEndReason.BodyLost ? "RS_LetterBodyLost" : reason == LinkEndReason.PowerLost ? "RS_LetterPowerLost" : "RS_LetterPodDestroyed";
            Messages.Message(key.Translate(op.LabelShortCap), op, MessageTypeDefOf.NegativeEvent, false);
        }

        private static void PassBackExperience(Pawn op, Pawn s)
        {
            var h = Hediff_SurrogateBody.Of(s);
            if (h == null || op.skills == null) return;
            float share = RemoteSurrogateMod.Settings.xpShare;
            if (share <= 0f) return;
            foreach (var kv in h.xpGained)
            {
                if (kv.Value <= 0f) continue;
                op.skills.Learn(kv.Key, kv.Value * share, true, true);
            }
        }

        /// <summary>Removes a remote body without a death: gear is dropped or destroyed, no corpse, no colonist-death thoughts.</summary>
        public static void DisposeSurrogate(Pawn s)
        {
            if (s == null || s.Destroyed) return;
            var h = Hediff_SurrogateBody.Of(s);
            var generated = h != null ? new HashSet<int>(h.generatedGearIds) : new HashSet<int>();

            s.jobs?.StopAll();
            IntVec3 pos = s.Spawned ? s.Position : IntVec3.Invalid;
            Map map = s.MapHeld;

            if (s.Spawned)
            {
                s.carryTracker?.TryDropCarriedThing(pos, ThingPlaceMode.Near, out Thing _);
            }
            if (s.apparel != null)
            {
                foreach (Apparel a in s.apparel.WornApparel.ToList())
                {
                    if (generated.Contains(a.thingIDNumber)) a.Destroy();
                    else if (pos.IsValid) s.apparel.TryDrop(a, out Apparel _, pos, false);
                }
            }
            if (s.equipment != null)
            {
                foreach (ThingWithComps e in s.equipment.AllEquipmentListForReading.ToList())
                {
                    if (generated.Contains(e.thingIDNumber)) { s.equipment.Remove(e); e.Destroy(); }
                    else if (pos.IsValid) s.equipment.TryDropEquipment(e, out ThingWithComps _, pos, false);
                }
            }
            if (s.inventory != null)
            {
                foreach (Thing t in s.inventory.innerContainer.ToList())
                {
                    if (generated.Contains(t.thingIDNumber)) { s.inventory.innerContainer.Remove(t); t.Destroy(); }
                }
                if (pos.IsValid) s.inventory.DropAllNearPawn(pos, false, false);
            }

            var caravan = s.GetCaravan();
            if (caravan != null) caravan.RemovePawn(s);
            if (Find.WorldPawns != null && Find.WorldPawns.Contains(s)) Find.WorldPawns.RemovePawn(s);
            if (s.Spawned) s.DeSpawn(DestroyMode.Vanish);
            if (!s.Destroyed) s.Destroy(DestroyMode.Vanish);
            if (!s.Discarded) s.Discard(true);
        }

        public override void DeSpawn(DestroyMode mode = DestroyMode.Vanish)
        {
            if (Occupied || surrogate != null)
            {
                bool destroyed = mode == DestroyMode.KillFinalize || mode == DestroyMode.KillFinalizeLeavingsOnly;
                EndLink(destroyed ? LinkEndReason.PodDestroyed : LinkEndReason.Disconnected);
            }
            base.DeSpawn(mode);
        }

        // ---- upkeep -----------------------------------------------------------

        public override void TickRare()
        {
            base.TickRare();
            if (!Spawned) return;
            UpdatePowerUse();
            if (!Occupied)
            {
                powerOffSinceTick = -1;
                if (surrogate != null) { var s = surrogate; surrogate = null; DisposeSurrogate(s); }
                return;
            }

            var h = Hediff_SurrogateBody.Of(surrogate);
            if (surrogate == null || surrogate.Destroyed || surrogate.Discarded || h == null || h.pod != this)
            {
                EndLink(LinkEndReason.BodyLost);
                return;
            }
            if (h.endPending)
            {
                EndLink(h.pendingReason);
                return;
            }
            if (surrogate.MapHeld != Map || !surrogate.Spawned)
            {
                // Out of range (left the map or joined a caravan): the link cannot follow.
                EndLink(LinkEndReason.PowerLost);
                return;
            }

            if (PowerOn)
            {
                powerOffSinceTick = -1;
            }
            else
            {
                int now = Find.TickManager.TicksGame;
                if (powerOffSinceTick < 0)
                {
                    powerOffSinceTick = now;
                    Messages.Message("RS_PowerWarning".Translate(), this, MessageTypeDefOf.NegativeEvent, false);
                }
                else if (now - powerOffSinceTick >= RemoteSurrogateMod.Settings.powerGraceTicks)
                {
                    EndLink(LinkEndReason.PowerLost);
                }
            }
        }

        // ---- UI ---------------------------------------------------------------

        public override IEnumerable<Gizmo> GetGizmos()
        {
            foreach (Gizmo g in base.GetGizmos()) yield return g;
            if (Occupied && Faction == Faction.OfPlayer)
            {
                yield return new Command_Action
                {
                    defaultLabel = "RS_Disconnect".Translate(),
                    defaultDesc = "RS_DisconnectDesc".Translate(),
                    icon = ContentFinder<Texture2D>.Get("UI/RS_Disconnect"),
                    action = () => EndLink(LinkEndReason.Disconnected)
                };
            }
        }

        public override string GetInspectString()
        {
            var sb = new System.Text.StringBuilder(base.GetInspectString());
            if (sb.Length > 0) sb.AppendLine();
            Pawn op = Operator;
            if (op != null)
            {
                sb.AppendLine("RS_InspectLinked".Translate(op.LabelShortCap));
                if (powerOffSinceTick >= 0)
                {
                    int left = Mathf.Max(0, RemoteSurrogateMod.Settings.powerGraceTicks - (Find.TickManager.TicksGame - powerOffSinceTick));
                    sb.AppendLine("RS_InspectPowerGrace".Translate(left.ToStringTicksToPeriod()));
                }
            }
            else if (CooldownTicksLeft > 0)
                sb.AppendLine("RS_PodRecharging".Translate(CooldownTicksLeft.ToStringTicksToPeriod()));
            else
                sb.AppendLine("RS_InspectReady".Translate());
            return sb.ToString().TrimEndNewlines();
        }
    }
}
