using RimWorld;
using Verse;

namespace MagicalCrops
{
    // Situational thought: the more mature mood blooms within a few cells, the stronger the stage.
    // Evaluated by the game at its normal situational-thought interval, so no per-plant ticking.
    public class ThoughtWorker_MoodBloomNearby : ThoughtWorker
    {
        const string BloomDefName = "MC_Plant_MoodBloom";

        protected override ThoughtState CurrentStateInternal(Pawn p)
        {
            if (!p.Spawned || p.Map == null) return ThoughtState.Inactive;
            var bloomDef = DefDatabase<ThingDef>.GetNamedSilentFail(BloomDefName);
            if (bloomDef == null) return ThoughtState.Inactive;

            Map map = p.Map;
            int radius = MagicalCropsMod.Settings != null ? MagicalCropsMod.Settings.bloomRadius : 3;
            int count = 0;
            foreach (IntVec3 c in GenRadial.RadialCellsAround(p.Position, radius, true))
            {
                if (!c.InBounds(map)) continue;
                var plant = c.GetPlant(map);
                if (plant != null && plant.def == bloomDef && plant.LifeStage == PlantLifeStage.Mature)
                    count++;
            }
            if (count == 0) return ThoughtState.Inactive;
            if (count < 5) return ThoughtState.ActiveAtStage(0);
            if (count < 13) return ThoughtState.ActiveAtStage(1);
            return ThoughtState.ActiveAtStage(2);
        }
    }
}
