using System.Collections.Generic;
using RimWorld;
using Verse;

namespace MountainBreaker
{
    /// <summary>Per-map queue of cells waiting to be erased, drained a few per tick to avoid a hitch.</summary>
    public class BreakQueue : MapComponent
    {
        private List<IntVec3> cells = new List<IntVec3>();
        private int head;

        public BreakQueue(Map map) : base(map) { }

        public void Enqueue(IEnumerable<IntVec3> toAdd)
        {
            cells.AddRange(toAdd);
        }

        public override void MapComponentTick()
        {
            if (head >= cells.Count) return;
            var s = MountainBreakerMod.Settings;
            int budget = s.cellsPerTick;
            while (budget-- > 0 && head < cells.Count)
                BreakCell(cells[head++], s);
            if (head >= cells.Count)
            {
                cells.Clear();
                head = 0;
            }
        }

        private void BreakCell(IntVec3 c, MountainBreakerSettings s)
        {
            if (!c.InBounds(map)) return;

            // Natural rock (mountain walls and ore veins).
            Building edifice = c.GetEdifice(map);
            if (edifice != null && edifice.def.building != null && edifice.def.building.isNaturalRock)
            {
                ThingDef drop = edifice.def.building.mineableThing;
                int yield = edifice.def.building.EffectiveMineableYield;
                edifice.Destroy(DestroyMode.Vanish);
                if (s.dropResources && drop != null && yield > 0)
                {
                    int count = GenMath.RoundRandom(yield * s.yieldPercent);
                    if (count > 0)
                    {
                        Thing t = ThingMaker.MakeThing(drop);
                        t.stackCount = count;
                        GenPlace.TryPlaceThing(t, c, map, ThingPlaceMode.Near);
                    }
                }
            }

            // Overhead roof. Thick (mountain) roof cannot be removed any other way.
            RoofDef roof = map.roofGrid.RoofAt(c);
            if (roof != null && (s.clearAllRoofs || roof.isThickRoof))
                map.roofGrid.SetRoof(c, null);
        }
    }
}
