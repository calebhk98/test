using System.Collections.Generic;
using System.Linq;
using System.Text;
using RimWorld;
using UnityEngine;
using Verse;

namespace UndergroundBarn
{
    /// <summary>
    /// A container building (same pattern as the cryptosleep casket) that holds animals as real Pawn
    /// objects. Stored pawns are not on the map and nothing here ever calls their Tick, so they cost
    /// nothing per tick. The whole herd is simulated in one pass every few thousand ticks
    /// (see BarnSimulation.cs).
    /// </summary>
    public partial class Building_UndergroundBarn : Building, IThingHolder
    {
        private ThingOwner<Pawn> innerContainer;
        private int ticksSinceSim;
        private int cullAbove; // per kind, 0 = off
        // Fractional leftovers: food credit ("food|race") and product progress ("out|thing").
        private Dictionary<string, float> buffers = new Dictionary<string, float>();

        // Not saved. Display caches.
        private Dictionary<PawnKindDef, int> kindCounts = new Dictionary<PawnKindDef, int>();
        private int kindCountsTotal = -1;
        private float lastFedFraction = 1f;
        private CompPowerTrader power;

        public Building_UndergroundBarn()
        {
            innerContainer = NewContainer();
        }

        private ThingOwner<Pawn> NewContainer()
        {
            return new ThingOwner<Pawn>(this, false, LookMode.Deep)
            {
                dontTickContents = true // belt and braces: this class never ticks the contents either
            };
        }

        private static UndergroundBarnSettings Settings => UndergroundBarnMod.Settings;

        public int Capacity => Settings.capacity;
        public int StoredCount => innerContainer.Count;
        public bool HasRoom => innerContainer.Count < Capacity;
        public IReadOnlyList<Pawn> Stored => innerContainer.InnerListForReading;

        public bool WorkingNow => !Settings.requirePower || power == null || power.PowerOn;

        // ---- IThingHolder ----

        public ThingOwner GetDirectlyHeldThings() => innerContainer;

        public void GetChildHolders(List<IThingHolder> outChildren)
        {
            ThingOwnerUtility.AppendThingHoldersFromThings(outChildren, GetDirectlyHeldThings());
        }

        // ---- save / load ----

        public override void ExposeData()
        {
            base.ExposeData();
            // Deep save: the pawns are written inside the barn. Other pawns' relations (bonds, parents)
            // refer to them by load id and are resolved after loading, exactly as for a casket.
            Scribe_Deep.Look(ref innerContainer, "innerContainer", this);
            Scribe_Values.Look(ref ticksSinceSim, "ticksSinceSim");
            Scribe_Values.Look(ref cullAbove, "cullAbove");
            Scribe_Collections.Look(ref buffers, "buffers", LookMode.Value, LookMode.Value);
            if (Scribe.mode == LoadSaveMode.PostLoadInit)
            {
                if (innerContainer == null) innerContainer = NewContainer();
                innerContainer.dontTickContents = true;
                if (buffers == null) buffers = new Dictionary<string, float>();
                kindCountsTotal = -1;
            }
        }

        public override void SpawnSetup(Map map, bool respawningAfterLoad)
        {
            base.SpawnSetup(map, respawningAfterLoad);
            power = GetComp<CompPowerTrader>();
        }

        public override void Destroy(DestroyMode mode = DestroyMode.Vanish)
        {
            // Nobody is lost with the building: the herd walks out. Same idea as the casket.
            if (Spawned && innerContainer != null && innerContainer.Count > 0)
            {
                Map map = Map;
                innerContainer.TryDropAll(InteractionCell, map, ThingPlaceMode.Near);
            }
            base.Destroy(mode);
        }

        // ---- the only recurring work: one rare tick (every 250 ticks) and an interval counter ----

        public override void TickRare()
        {
            base.TickRare();
            if (innerContainer.Count == 0)
            {
                ticksSinceSim = 0;
                return;
            }
            ticksSinceSim += 250;
            if (ticksSinceSim >= Settings.simIntervalTicks)
            {
                int elapsed = ticksSinceSim;
                ticksSinceSim = 0;
                RunSimulation(elapsed);
            }
        }

        // ---- entering and leaving ----

        public bool CanStore(Pawn p, out string reason)
        {
            reason = null;
            if (p == null || p.Dead || !p.RaceProps.Animal || p.Faction != Faction.OfPlayer)
            {
                reason = "UB_NotYourAnimal".Translate();
                return false;
            }
            if (!Settings.allowBonded && IsBonded(p))
            {
                reason = "UB_Bonded".Translate();
                return false;
            }
            if (!HasRoom)
            {
                reason = "UB_BarnFull".Translate();
                return false;
            }
            return true;
        }

        public static bool IsBonded(Pawn p)
        {
            return p.relations != null && p.relations.GetFirstDirectRelationPawn(PawnRelationDefOf.Bond) != null;
        }

        /// <summary>
        /// Takes the pawn into the barn. If a carrier is holding it, the pawn is moved out of the
        /// carrier's hands so it is never in two holders at once.
        /// </summary>
        public bool TryAcceptPawn(Pawn p, Pawn carrier)
        {
            if (p == null || !HasRoom) return false;
            Map map = Map ?? carrier?.Map;
            map?.designationManager.TryRemoveDesignationOn(p, UBDefOf.UB_StoreAnimal);

            bool ok;
            if (carrier != null && carrier.carryTracker.CarriedThing == p)
                ok = carrier.carryTracker.innerContainer.TryTransferToContainer(p, innerContainer, false);
            else
                ok = innerContainer.TryAddOrTransfer(p, false);
            if (!ok) return false;

            // A freshly generated or recently despawned pawn may still be listed as a world pawn.
            // The barn owns it now; a world pawn that is also in a container would be discarded by the
            // world pawn cleanup while the barn still holds it.
            if (Find.WorldPawns.Contains(p)) Find.WorldPawns.RemovePawn(p);
            kindCountsTotal = -1;
            return true;
        }

        public int Release(PawnKindDef kind, int max)
        {
            Map map = Map;
            if (map == null || max <= 0) return 0;
            var picked = new List<Pawn>();
            foreach (Pawn p in innerContainer.InnerListForReading)
            {
                if (kind != null && p.kindDef != kind) continue;
                picked.Add(p);
                if (picked.Count >= max) break;
            }
            int released = 0;
            foreach (Pawn p in picked)
            {
                if (innerContainer.TryDrop(p, InteractionCell, map, ThingPlaceMode.Near, out Pawn _))
                    released++;
            }
            kindCountsTotal = -1;
            return released;
        }

        // ---- display ----

        private void RefreshKindCounts()
        {
            if (kindCountsTotal == innerContainer.Count) return;
            kindCounts.Clear();
            foreach (Pawn p in innerContainer.InnerListForReading)
            {
                kindCounts.TryGetValue(p.kindDef, out int c);
                kindCounts[p.kindDef] = c + 1;
            }
            kindCountsTotal = innerContainer.Count;
        }

        public override string GetInspectString()
        {
            var sb = new StringBuilder();
            string baseStr = base.GetInspectString();
            if (!baseStr.NullOrEmpty()) sb.AppendLine(baseStr);
            sb.Append("UB_Stored".Translate(innerContainer.Count, Capacity));
            if (innerContainer.Count > 0)
            {
                RefreshKindCounts();
                sb.AppendLine();
                sb.Append(string.Join(", ", kindCounts.OrderByDescending(k => k.Value).Take(6)
                    .Select(k => k.Key.GetLabelPlural(k.Value) + " " + k.Value)));
                sb.AppendLine();
                sb.Append("UB_Fed".Translate((lastFedFraction * 100f).ToString("0")));
                sb.AppendLine();
                int left = Mathf.Max(0, Settings.simIntervalTicks - ticksSinceSim);
                sb.Append("UB_NextUpdate".Translate(left.ToStringTicksToPeriod()));
                if (Settings.requirePower && !WorkingNow)
                {
                    sb.AppendLine();
                    sb.Append("UB_NoPower".Translate());
                }
            }
            if (cullAbove > 0)
            {
                sb.AppendLine();
                sb.Append("UB_CullInfo".Translate(cullAbove));
            }
            return sb.ToString().TrimEndNewlines();
        }

        // ---- gizmos ----

        public override IEnumerable<Gizmo> GetGizmos()
        {
            foreach (Gizmo g in base.GetGizmos()) yield return g;

            yield return new Command_Action
            {
                defaultLabel = "UB_GizmoStore".Translate(),
                defaultDesc = "UB_GizmoStoreDesc".Translate(),
                icon = UBTex.Store,
                action = BeginStoreTargeting
            };
            yield return new Command_Action
            {
                defaultLabel = "UB_GizmoStoreKind".Translate(),
                defaultDesc = "UB_GizmoStoreKindDesc".Translate(),
                icon = UBTex.StoreKind,
                action = OpenStoreKindMenu
            };
            if (Map != null && Map.designationManager.AnySpawnedDesignationOfDef(UBDefOf.UB_StoreAnimal))
            {
                yield return new Command_Action
                {
                    defaultLabel = "UB_GizmoCancel".Translate(),
                    defaultDesc = "UB_GizmoCancelDesc".Translate(),
                    icon = UBTex.Cancel,
                    action = () => Map.designationManager.RemoveAllDesignationsOfDef(UBDefOf.UB_StoreAnimal)
                };
            }
            if (innerContainer.Count > 0)
            {
                yield return new Command_Action
                {
                    defaultLabel = "UB_GizmoRelease".Translate(),
                    defaultDesc = "UB_GizmoReleaseDesc".Translate(),
                    icon = UBTex.Release,
                    action = OpenReleaseMenu
                };
            }
            yield return new Command_Action
            {
                defaultLabel = "UB_GizmoCull".Translate(),
                defaultDesc = "UB_GizmoCullDesc".Translate(cullAbove > 0 ? cullAbove.ToString() : "UB_Off".Translate().ToString()),
                icon = UBTex.Cull,
                action = OpenCullDialog
            };
            if (DebugSettings.godMode && innerContainer.Count > 0)
            {
                yield return new Command_Action
                {
                    defaultLabel = "DEV: run herd update",
                    action = () =>
                    {
                        int elapsed = Mathf.Max(ticksSinceSim, Settings.simIntervalTicks);
                        ticksSinceSim = 0;
                        RunSimulation(elapsed);
                    }
                };
            }
        }

        private static readonly TargetingParameters StoreTargetParams = new TargetingParameters
        {
            canTargetPawns = true,
            canTargetAnimals = true,
            canTargetHumans = false,
            canTargetMechs = false,
            canTargetBuildings = false,
            canTargetItems = false,
            validator = t => t.Thing is Pawn p && p.Spawned && p.RaceProps.Animal && p.Faction == Faction.OfPlayer
        };

        private void BeginStoreTargeting()
        {
            Find.Targeter.BeginTargeting(StoreTargetParams, target =>
            {
                if (target.Thing is Pawn p) Designate(p, true);
                BeginStoreTargeting(); // keep going until the player right-clicks or presses Escape
            });
        }

        private bool Designate(Pawn p, bool messageOnFail)
        {
            if (!CanStore(p, out string reason))
            {
                if (messageOnFail && reason != null)
                    Messages.Message(reason, p, MessageTypeDefOf.RejectInput, false);
                return false;
            }
            DesignationManager dm = p.Map.designationManager;
            if (dm.DesignationOn(p, UBDefOf.UB_StoreAnimal) == null)
                dm.AddDesignation(new Designation(p, UBDefOf.UB_StoreAnimal));
            return true;
        }

        private void OpenStoreKindMenu()
        {
            Map map = Map;
            if (map == null) return;
            var opts = new List<FloatMenuOption>();
            var groups = map.mapPawns.SpawnedColonyAnimals
                .Where(p => p.Faction == Faction.OfPlayer && !p.Dead)
                .GroupBy(p => p.kindDef).OrderBy(g => g.Key.label);
            foreach (var g in groups)
            {
                PawnKindDef kind = g.Key;
                int n = g.Count();
                opts.Add(new FloatMenuOption("UB_StoreKindOption".Translate(kind.GetLabelPlural(n), n), () =>
                {
                    int done = 0;
                    foreach (Pawn p in map.mapPawns.SpawnedColonyAnimals.ToList())
                    {
                        if (p.kindDef != kind) continue;
                        if (done >= Capacity - StoredCount) break;
                        if (Designate(p, false)) done++;
                    }
                    Messages.Message("UB_Designated".Translate(done, kind.GetLabelPlural(done)), this, MessageTypeDefOf.TaskCompletion, false);
                }));
            }
            if (opts.Count == 0) opts.Add(new FloatMenuOption("UB_NoAnimals".Translate(), null));
            Find.WindowStack.Add(new FloatMenu(opts));
        }

        private void OpenReleaseMenu()
        {
            RefreshKindCounts();
            var opts = new List<FloatMenuOption>();
            opts.Add(new FloatMenuOption("UB_ReleaseAll".Translate(innerContainer.Count), () => AskReleaseCount(null, innerContainer.Count)));
            foreach (var kv in kindCounts.OrderBy(k => k.Key.label))
            {
                PawnKindDef kind = kv.Key;
                int n = kv.Value;
                opts.Add(new FloatMenuOption("UB_ReleaseKind".Translate(kind.GetLabelPlural(n), n), () => AskReleaseCount(kind, n)));
            }
            Find.WindowStack.Add(new FloatMenu(opts));
        }

        private void AskReleaseCount(PawnKindDef kind, int available)
        {
            Find.WindowStack.Add(new Dialog_Slider(
                v => "UB_ReleaseCount".Translate(v),
                1, Mathf.Max(1, available),
                v =>
                {
                    int n = Release(kind, v);
                    Messages.Message("UB_Released".Translate(n), this, MessageTypeDefOf.TaskCompletion, false);
                },
                Mathf.Min(available, 5)));
        }

        private void OpenCullDialog()
        {
            Find.WindowStack.Add(new Dialog_Slider(
                v => v == 0 ? "UB_CullOff".Translate() : "UB_CullSetTo".Translate(v),
                0, Mathf.Max(10, Capacity),
                v => cullAbove = v,
                cullAbove));
        }
    }
}
