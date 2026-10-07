using System.Collections.Generic;
using RimWorld;
using Verse;

namespace DigitalStorage
{
    /// <summary>
    /// Network membership. Chosen design: wireless range. A port or access point belongs to every
    /// online core on its map whose centre is within the range setting.
    /// </summary>
    public static class DSNet
    {
        private struct Entry { public int stamp; public List<Building_DSCore> list; }
        private static readonly Dictionary<Map, Entry> cache = new Dictionary<Map, Entry>();

        public static List<Building_DSCore> CoresOnMap(Map map)
        {
            int stamp = Find.TickManager.TicksGame / 30;
            if (cache.TryGetValue(map, out Entry e) && e.stamp == stamp) return e.list;
            var list = new List<Building_DSCore>();
            foreach (Building_DSCore c in map.listerBuildings.AllBuildingsColonistOfClass<Building_DSCore>())
                list.Add(c);
            cache[map] = new Entry { stamp = stamp, list = list };
            return list;
        }

        public static void CoresInRange(Map map, IntVec3 pos, List<Building_DSCore> result)
        {
            result.Clear();
            if (map == null) return;
            float range = DSMod.Settings.networkRange;
            List<Building_DSCore> all = CoresOnMap(map);
            for (int i = 0; i < all.Count; i++)
            {
                Building_DSCore c = all[i];
                if (c.Spawned && c.Online && c.Position.DistanceTo(pos) <= range) result.Add(c);
            }
        }

        public static Building_DSCore FindAcceptingCore(Map map, IntVec3 pos, Thing t)
        {
            if (map == null) return null;
            float range = DSMod.Settings.networkRange;
            List<Building_DSCore> all = CoresOnMap(map);
            for (int i = 0; i < all.Count; i++)
            {
                Building_DSCore c = all[i];
                if (c.Spawned && c.Position.DistanceTo(pos) <= range && c.CanTake(t)) return c;
            }
            return null;
        }

        public static bool InRangeOfOnlineCore(Map map, IntVec3 pos)
        {
            if (map == null) return false;
            float range = DSMod.Settings.networkRange;
            List<Building_DSCore> all = CoresOnMap(map);
            for (int i = 0; i < all.Count; i++)
                if (all[i].Spawned && all[i].Online && all[i].Position.DistanceTo(pos) <= range) return true;
            return false;
        }

        /// <summary>What may live in the network: real items only, not drives, corpses or packed furniture.</summary>
        public static bool IsNetworkItem(Thing t)
        {
            if (t == null || t.def.category != ThingCategory.Item) return false;
            if (t is Corpse || t is MinifiedThing) return false;
            if (t.def.GetModExtension<DriveExtension>() != null) return false;
            if (!DSMod.Settings.allowPerishables && t.TryGetComp<CompRottable>() != null) return false;
            return true;
        }
    }
}
