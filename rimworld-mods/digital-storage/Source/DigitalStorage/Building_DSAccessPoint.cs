using System.Collections.Generic;
using RimWorld;
using Verse;

namespace DigitalStorage
{
    /// <summary>
    /// Makes network items usable. Chosen approach: a working stock (README option 2). Each cell
    /// holds up to one full stack of an item allowed by this building's storage filter, refilled
    /// from cores in range. The stock is real map items, so vanilla bill, construction, meal and
    /// haul searches find it with no patches. Items the filter no longer allows go back to the network.
    /// </summary>
    public class Building_DSAccessPoint : Building_Storage
    {
        private CompPowerTrader power;
        private readonly List<Building_DSCore> cores = new List<Building_DSCore>();

        private bool Powered => power == null || power.PowerOn;

        public override void SpawnSetup(Map map, bool respawningAfterLoad)
        {
            base.SpawnSetup(map, respawningAfterLoad);
            power = GetComp<CompPowerTrader>();
        }

        private static Thing ItemAt(Map map, IntVec3 c)
        {
            List<Thing> l = map.thingGrid.ThingsListAtFast(c);
            for (int i = 0; i < l.Count; i++)
                if (l[i].def.category == ThingCategory.Item) return l[i];
            return null;
        }

        private Thing ExtractAny(System.Predicate<Thing> match, int count)
        {
            foreach (Building_DSCore core in cores)
            {
                Thing t = core.Extract(match, count);
                if (t != null) return t;
            }
            return null;
        }

        public override void TickRare()
        {
            base.TickRare();
            if (!Spawned || !Powered) return;
            DSNet.CoresInRange(Map, Position, cores);
            if (cores.Count == 0) return;
            Refill();
        }

        private void Refill()
        {
            var stocked = new HashSet<ThingDef>();
            var empty = new List<IntVec3>();
            foreach (IntVec3 c in AllSlotCellsList())
            {
                Thing item = ItemAt(Map, c);
                if (item == null) { empty.Add(c); continue; }
                if (!settings.AllowedToAccept(item))
                {
                    foreach (Building_DSCore core in cores)
                        if (core.CanTake(item)) { core.TryAbsorb(item); break; }
                    continue;
                }
                stocked.Add(item.def);
                int need = item.def.stackLimit - item.stackCount;
                if (need <= 0) continue;
                Thing extra = ExtractAny(t => t.def == item.def && item.CanStackWith(t) && settings.AllowedToAccept(t), need);
                if (extra == null) continue;
                item.TryAbsorbStack(extra, true);
                if (!extra.Destroyed && extra.stackCount > 0) ReturnToAny(extra);
            }
            if (empty.Count == 0) return;

            var wanted = new List<ThingDef>();
            foreach (Building_DSCore core in cores)
                foreach (ThingDef d in core.DefsInStorage())
                    if (!stocked.Contains(d) && !wanted.Contains(d) && settings.AllowedToAccept(d)) wanted.Add(d);
            wanted.Sort((a, b) => string.CompareOrdinal(a.label, b.label));

            int w = 0;
            foreach (IntVec3 c in empty)
            {
                while (w < wanted.Count)
                {
                    ThingDef d = wanted[w++];
                    Thing t = ExtractAny(x => x.def == d && settings.AllowedToAccept(x), d.stackLimit);
                    if (t == null) continue;
                    CompForbiddable forb = t.TryGetComp<CompForbiddable>();
                    if (forb != null) forb.Forbidden = false;
                    if (!GenPlace.TryPlaceThing(t, c, Map, ThingPlaceMode.Direct) && !t.Destroyed && t.stackCount > 0)
                        ReturnToAny(t);
                    break;
                }
            }
        }

        private void ReturnToAny(Thing t)
        {
            if (cores.Count > 0) cores[0].Return(t);
        }

        public override string GetInspectString()
        {
            string s = base.GetInspectString();
            string add = (Powered ? (DSNet.InRangeOfOnlineCore(Map, Position) ? "DS_Connected" : "DS_NoCore") : "DS_Offline").Translate();
            return string.IsNullOrEmpty(s) ? add : s + "\n" + add;
        }
    }
}
