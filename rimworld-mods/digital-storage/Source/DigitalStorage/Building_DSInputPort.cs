using System.Collections.Generic;
using RimWorld;
using Verse;

namespace DigitalStorage
{
    /// <summary>A storage building pawns haul into. Everything left in its cells is absorbed by a core in range.</summary>
    public class Building_DSInputPort : Building_Storage
    {
        private CompPowerTrader power;
        private readonly List<Thing> temp = new List<Thing>();

        private bool Powered => power == null || power.PowerOn;

        public override void SpawnSetup(Map map, bool respawningAfterLoad)
        {
            base.SpawnSetup(map, respawningAfterLoad);
            power = GetComp<CompPowerTrader>();
        }

        /// <summary>Called from Patch_StorageAccepts after the vanilla filter check passed.</summary>
        public bool NetworkAccepts(Thing t)
        {
            if (!Spawned || !Powered) return false;
            return DSNet.FindAcceptingCore(Map, Position, t) != null;
        }

        public override void TickRare()
        {
            base.TickRare();
            if (!Spawned || !Powered) return;
            foreach (IntVec3 c in AllSlotCellsList())
            {
                temp.Clear();
                List<Thing> things = Map.thingGrid.ThingsListAt(c);
                for (int i = 0; i < things.Count; i++)
                    if (things[i].def.category == ThingCategory.Item) temp.Add(things[i]);
                foreach (Thing t in temp)
                {
                    Building_DSCore core = DSNet.FindAcceptingCore(Map, Position, t);
                    if (core != null) core.TryAbsorb(t);
                }
            }
            temp.Clear();
        }

        public override string GetInspectString()
        {
            string s = base.GetInspectString();
            string add = (Powered ? (DSNet.InRangeOfOnlineCore(Map, Position) ? "DS_Connected" : "DS_NoCore") : "DS_Offline").Translate();
            return string.IsNullOrEmpty(s) ? add : s + "\n" + add;
        }
    }
}
