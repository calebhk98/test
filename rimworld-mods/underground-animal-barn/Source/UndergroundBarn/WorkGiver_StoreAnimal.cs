using System.Collections.Generic;
using RimWorld;
using Verse;
using Verse.AI;

namespace UndergroundBarn
{
    /// <summary>Hands out the "store animal in barn" job for animals the player designated.</summary>
    public class WorkGiver_StoreAnimal : WorkGiver_Scanner
    {
        public override PathEndMode PathEndMode => PathEndMode.Touch;

        public override IEnumerable<Thing> PotentialWorkThingsGlobal(Pawn pawn)
        {
            foreach (Designation d in pawn.Map.designationManager.SpawnedDesignationsOfDef(UBDefOf.UB_StoreAnimal))
            {
                if (d.target.Thing != null) yield return d.target.Thing;
            }
        }

        public override bool ShouldSkip(Pawn pawn, bool forced = false)
        {
            return !pawn.Map.designationManager.AnySpawnedDesignationOfDef(UBDefOf.UB_StoreAnimal);
        }

        public override bool HasJobOnThing(Pawn pawn, Thing t, bool forced = false)
        {
            return MakeJob(pawn, t, forced) != null;
        }

        public override Job JobOnThing(Pawn pawn, Thing t, bool forced = false)
        {
            return MakeJob(pawn, t, forced);
        }

        private static Job MakeJob(Pawn pawn, Thing t, bool forced)
        {
            if (!(t is Pawn animal) || animal == pawn || !animal.Spawned) return null;
            if (pawn.Map.designationManager.DesignationOn(animal, UBDefOf.UB_StoreAnimal) == null) return null;
            if (!pawn.CanReserve(animal, 1, -1, null, forced)) return null;

            Thing barn = GenClosest.ClosestThingReachable(animal.Position, animal.Map,
                ThingRequest.ForDef(UBDefOf.UB_UndergroundBarn), PathEndMode.InteractionCell,
                TraverseParms.For(pawn), 9999f,
                b => b is Building_UndergroundBarn bb && bb.HasRoom && bb.CanStore(animal, out _) && !b.IsForbidden(pawn));
            if (barn == null) return null;

            return JobMaker.MakeJob(UBDefOf.UB_StoreAnimalJob, animal, barn);
        }
    }
}
