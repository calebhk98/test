using System;
using System.Collections.Generic;
using RimWorld;
using UnityEngine;
using Verse;
using Verse.AI;

namespace DigitalStorage
{
    /// <summary>
    /// The network core. Stored items are despawned and kept in a ThingOwner, so they cost no map
    /// space and no ticks. Inserted drives set the capacity (item types and total items).
    /// Idea of holding despawned items in a ThingOwner and counting them for bills follows
    /// Project RimFactory (Storage/Building_ColdStorage.cs), MIT licence; no code is copied.
    /// </summary>
    public class Building_DSCore : Building, IThingHolder
    {
        private ThingOwner<Thing> stored;
        private ThingOwner<Thing> drives;
        private CompPowerTrader power;

        private readonly Dictionary<ThingDef, int> counts = new Dictionary<ThingDef, int>();
        private readonly List<KeyValuePair<ThingDef, int>> sorted = new List<KeyValuePair<ThingDef, int>>();
        private int totalItems;
        private bool dirty = true;

        public Building_DSCore()
        {
            stored = new ThingOwner<Thing>(this, false, LookMode.Deep);
            drives = new ThingOwner<Thing>(this, false, LookMode.Deep);
        }

        private CoreExtension Ext => def.GetModExtension<CoreExtension>() ?? new CoreExtension();
        public int DriveSlots => Ext.driveSlots;
        public List<Thing> Drives => drives.InnerListForReading;
        public bool Online => Spawned && power != null && power.PowerOn;

        // ---- IThingHolder ----
        public ThingOwner GetDirectlyHeldThings() => stored;

        public void GetChildHolders(List<IThingHolder> outChildren)
        {
            ThingOwnerUtility.AppendThingHoldersFromThings(outChildren, GetDirectlyHeldThings());
            ThingOwnerUtility.AppendThingHoldersFromThings(outChildren, drives);
        }

        // ---- save / load ----
        public override void ExposeData()
        {
            base.ExposeData();
            Scribe_Deep.Look(ref stored, "storedItems", this);
            Scribe_Deep.Look(ref drives, "insertedDrives", this);
            if (Scribe.mode == LoadSaveMode.PostLoadInit)
            {
                if (stored == null) stored = new ThingOwner<Thing>(this, false, LookMode.Deep);
                if (drives == null) drives = new ThingOwner<Thing>(this, false, LookMode.Deep);
                dirty = true;
            }
        }

        public override void SpawnSetup(Map map, bool respawningAfterLoad)
        {
            base.SpawnSetup(map, respawningAfterLoad);
            power = GetComp<CompPowerTrader>();
            stored.dontTickContents = true;
            drives.dontTickContents = true;
            dirty = true;
        }

        public override void DeSpawn(DestroyMode mode = DestroyMode.Vanish)
        {
            Map map = Map;
            IntVec3 pos = Position;
            base.DeSpawn(mode);
            // Vanish means the map itself is going away; keep the data.
            if (mode == DestroyMode.Vanish || map == null) return;
            drives.TryDropAll(pos, map, ThingPlaceMode.Near);
            int budget = Math.Max(0, DSMod.Settings.spillStacks);
            var list = new List<Thing>(stored.InnerListForReading);
            foreach (Thing t in list)
            {
                if (budget-- > 0) stored.TryDrop(t, pos, map, ThingPlaceMode.Near, out Thing _);
                else t.Destroy();
            }
            dirty = true;
        }

        // ---- capacity ----
        public int MaxItems
        {
            get
            {
                int n = 0;
                foreach (Thing d in drives.InnerListForReading)
                    n += d.def.GetModExtension<DriveExtension>()?.totalItems ?? 0;
                return n;
            }
        }

        public int MaxTypes
        {
            get
            {
                int n = 0;
                foreach (Thing d in drives.InnerListForReading)
                    n += d.def.GetModExtension<DriveExtension>()?.itemTypes ?? 0;
                return n;
            }
        }

        private void EnsureFresh()
        {
            if (!dirty) return;
            dirty = false;
            counts.Clear();
            sorted.Clear();
            totalItems = 0;
            foreach (Thing t in stored.InnerListForReading)
            {
                counts.TryGetValue(t.def, out int c);
                counts[t.def] = c + t.stackCount;
                totalItems += t.stackCount;
            }
            foreach (var kv in counts) sorted.Add(kv);
            sorted.Sort((a, b) =>
            {
                int r = b.Value.CompareTo(a.Value);
                return r != 0 ? r : string.CompareOrdinal(a.Key.label, b.Key.label);
            });
        }

        public int TotalItems { get { EnsureFresh(); return totalItems; } }
        public int TypeCount { get { EnsureFresh(); return counts.Count; } }
        public int FreeItems => Math.Max(0, MaxItems - TotalItems);
        public List<KeyValuePair<ThingDef, int>> SortedContents { get { EnsureFresh(); return sorted; } }
        public int CountOf(ThingDef d) { EnsureFresh(); return counts.TryGetValue(d, out int c) ? c : 0; }

        public IEnumerable<ThingDef> DefsInStorage()
        {
            EnsureFresh();
            return counts.Keys;
        }

        // ---- moving items ----
        /// <summary>Whether at least some of this stack would fit and the core is online.</summary>
        public bool CanTake(Thing t)
        {
            if (!Online || !DSNet.IsNetworkItem(t)) return false;
            if (FreeItems <= 0) return false;
            EnsureFresh();
            return counts.ContainsKey(t.def) || counts.Count < MaxTypes;
        }

        /// <summary>Takes as much of the stack as fits. Returns how many items were absorbed.</summary>
        public int TryAbsorb(Thing t)
        {
            if (!CanTake(t)) return 0;
            int take = Math.Min(t.stackCount, FreeItems);
            if (take <= 0) return 0;
            Thing part;
            if (take >= t.stackCount)
            {
                part = t;
                if (t.Spawned) t.DeSpawn();
            }
            else
            {
                part = t.SplitOff(take);
            }
            int amount = part.stackCount;
            if (!stored.TryAdd(part, true))
            {
                // Could not store it (should not happen); put it back on the map.
                GenPlace.TryPlaceThing(part, Position, Map, ThingPlaceMode.Near);
                return 0;
            }
            dirty = true;
            return amount;
        }

        /// <summary>Removes up to count items of the first stack matching the predicate. Result is not spawned.</summary>
        public Thing Extract(Predicate<Thing> match, int count)
        {
            if (!Online || count <= 0) return null;
            List<Thing> list = stored.InnerListForReading;
            for (int i = 0; i < list.Count; i++)
            {
                Thing t = list[i];
                if (!match(t)) continue;
                Thing result = stored.Take(t, Math.Min(count, t.stackCount));
                dirty = true;
                return result;
            }
            return null;
        }

        /// <summary>Puts back something that was taken out and could not be used.</summary>
        public void Return(Thing t)
        {
            if (t == null || t.Destroyed) return;
            if (!stored.TryAdd(t, true)) GenPlace.TryPlaceThing(t, Position, Map, ThingPlaceMode.Near);
            dirty = true;
        }

        public void AddStoredDirect(Thing t) { if (stored.TryAdd(t, true)) dirty = true; }

        // ---- drives ----
        public bool TryInsertDrive(Pawn carrier, Thing drive)
        {
            if (drive == null || drive.def.GetModExtension<DriveExtension>() == null) return false;
            if (drives.Count >= DriveSlots) return false;
            if (!carrier.carryTracker.innerContainer.TryTransferToContainer(drive, drives, false)) return false;
            dirty = true;
            return true;
        }

        public bool CanRemoveDrive(Thing drive)
        {
            var ext = drive.def.GetModExtension<DriveExtension>();
            if (ext == null) return true;
            return MaxItems - ext.totalItems >= TotalItems && MaxTypes - ext.itemTypes >= TypeCount;
        }

        private void EjectDrive(Thing drive)
        {
            if (!CanRemoveDrive(drive))
            {
                Messages.Message("DS_CannotEject".Translate(), this, MessageTypeDefOf.RejectInput, false);
                return;
            }
            drives.Remove(drive);
            GenPlace.TryPlaceThing(drive, Position, Map, ThingPlaceMode.Near);
            dirty = true;
        }

        private void OpenInsertMenu()
        {
            if (drives.Count >= DriveSlots)
            {
                Messages.Message("DS_NoFreeSlot".Translate(), this, MessageTypeDefOf.RejectInput, false);
                return;
            }
            var options = new List<FloatMenuOption>();
            foreach (Thing t in Map.listerThings.ThingsInGroup(ThingRequestGroup.HaulableEver))
            {
                if (t.def.GetModExtension<DriveExtension>() == null || t.IsForbidden(Faction.OfPlayer)) continue;
                Thing drive = t;
                options.Add(new FloatMenuOption(drive.LabelCap + " (" + drive.Position.x + "," + drive.Position.z + ")",
                    () => OrderInsert(drive), drive.def, null, false, MenuOptionPriority.Default));
            }
            if (options.Count == 0)
            {
                Messages.Message("DS_NoDriveOnMap".Translate(), this, MessageTypeDefOf.RejectInput, false);
                return;
            }
            Find.WindowStack.Add(new FloatMenu(options));
        }

        private void OrderInsert(Thing drive)
        {
            Pawn best = null;
            float bestDist = float.MaxValue;
            foreach (Pawn p in Map.mapPawns.FreeColonistsSpawned)
            {
                if (p.Downed || p.Drafted || p.WorkTagIsDisabled(WorkTags.ManualDumb)) continue;
                if (!p.CanReserveAndReach(drive, PathEndMode.ClosestTouch, Danger.Deadly)) continue;
                if (!p.CanReserveAndReach(this, PathEndMode.Touch, Danger.Deadly)) continue;
                float d = p.Position.DistanceToSquared(drive.Position);
                if (d < bestDist) { best = p; bestDist = d; }
            }
            if (best == null)
            {
                Messages.Message("DS_NoPawn".Translate(), this, MessageTypeDefOf.RejectInput, false);
                return;
            }
            Job job = JobMaker.MakeJob(DSDefOf.DS_InsertDrive, drive, this);
            job.count = 1;
            best.jobs.TryTakeOrderedJob(job, JobTag.Misc);
        }

        private void OpenEjectMenu()
        {
            var options = new List<FloatMenuOption>();
            foreach (Thing d in new List<Thing>(drives.InnerListForReading))
            {
                Thing drive = d;
                options.Add(new FloatMenuOption(drive.LabelCap, () => EjectDrive(drive), drive.def, null, false, MenuOptionPriority.Default));
            }
            if (options.Count == 0)
            {
                Messages.Message("DS_NoDrives".Translate(), this, MessageTypeDefOf.RejectInput, false);
                return;
            }
            Find.WindowStack.Add(new FloatMenu(options));
        }

        public override IEnumerable<Gizmo> GetGizmos()
        {
            foreach (Gizmo g in base.GetGizmos()) yield return g;
            if (Faction != Faction.OfPlayer) yield break;
            yield return new Command_Action
            {
                defaultLabel = "DS_InsertDrive".Translate(),
                defaultDesc = "DS_InsertDriveDesc".Translate(),
                icon = ContentFinder<Texture2D>.Get("UI/DS_Insert", true),
                action = OpenInsertMenu
            };
            yield return new Command_Action
            {
                defaultLabel = "DS_EjectDrive".Translate(),
                defaultDesc = "DS_EjectDriveDesc".Translate(),
                icon = ContentFinder<Texture2D>.Get("UI/DS_Eject", true),
                action = OpenEjectMenu
            };
            if (Prefs.DevMode)
            {
                yield return new Command_Action
                {
                    defaultLabel = "DEV: add drive",
                    action = () =>
                    {
                        var opts = new List<FloatMenuOption>();
                        foreach (ThingDef d in DefDatabase<ThingDef>.AllDefs)
                        {
                            if (d.GetModExtension<DriveExtension>() == null) continue;
                            ThingDef dd = d;
                            opts.Add(new FloatMenuOption(dd.label, () =>
                            {
                                if (drives.Count < DriveSlots) { drives.TryAdd(ThingMaker.MakeThing(dd), false); dirty = true; }
                            }));
                        }
                        Find.WindowStack.Add(new FloatMenu(opts));
                    }
                };
                yield return new Command_Action
                {
                    defaultLabel = "DEV: add 1000 items",
                    action = () =>
                    {
                        var opts = new List<FloatMenuOption>();
                        foreach (string n in new[] { "Steel", "WoodLog", "Silver", "MealSimple" })
                        {
                            ThingDef td = DefDatabase<ThingDef>.GetNamedSilentFail(n);
                            if (td == null) continue;
                            opts.Add(new FloatMenuOption(td.label, () =>
                            {
                                int left = 1000;
                                while (left > 0)
                                {
                                    Thing t = ThingMaker.MakeThing(td);
                                    t.stackCount = Math.Min(left, td.stackLimit);
                                    left -= t.stackCount;
                                    if (TryAbsorb(t) < t.stackCount) break;
                                }
                            }));
                        }
                        Find.WindowStack.Add(new FloatMenu(opts));
                    }
                };
            }
        }

        // ---- ticking, power, inspection ----
        public override void TickRare()
        {
            base.TickRare();
            if (power == null) return;
            float want = -(power.Props.PowerConsumption + Ext.powerPerDrive * drives.Count);
            if (Math.Abs(power.PowerOutput - want) > 0.01f) power.PowerOutput = want;
            EnsureFresh();
        }

        public override void DrawExtraSelectionOverlays()
        {
            base.DrawExtraSelectionOverlays();
            GenDraw.DrawRadiusRing(Position, DSMod.Settings.networkRange);
        }

        public override string GetInspectString()
        {
            string s = base.GetInspectString();
            string add = (Online ? "DS_Online" : "DS_Offline").Translate()
                + "\n" + "DS_ItemsLine".Translate(TotalItems, MaxItems)
                + "\n" + "DS_TypesLine".Translate(TypeCount, MaxTypes)
                + "\n" + "DS_DrivesLine".Translate(drives.Count, DriveSlots);
            return string.IsNullOrEmpty(s) ? add : s + "\n" + add;
        }
    }
}
