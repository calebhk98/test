using System.Collections.Generic;
using RimWorld;
using Verse;
using Verse.AI;

namespace Forklifts
{
    public class WorkGiver_ForkliftHaul : WorkGiver_Scanner
    {
        public override PathEndMode PathEndMode
        {
            get { return PathEndMode.ClosestTouch; }
        }

        public override bool ShouldSkip(Pawn pawn, bool forced = false)
        {
            if (pawn.Map == null) return true;
            if (ForkliftsMod.Settings.requireForklift && !ForkliftUtility.IsOperator(pawn)) return true;
            return pawn.Map.listerThings.ThingsOfDef(ForkliftsDefOf.Forklifts_Pallet).Count == 0;
        }

        public override IEnumerable<Thing> PotentialWorkThingsGlobal(Pawn pawn)
        {
            Pallet p = ForkliftUtility.FindPallet(pawn);
            if (p != null) yield return p;
        }

        public override bool HasJobOnThing(Pawn pawn, Thing t, bool forced = false)
        {
            return JobOnThing(pawn, t, forced) != null;
        }

        public override Job JobOnThing(Pawn pawn, Thing t, bool forced = false)
        {
            var pallet = t as Pallet;
            if (pallet == null || !pallet.Spawned || !pallet.Empty) return null;
            if (pallet.IsForbidden(pawn) || !pawn.CanReserve(pallet)) return null;
            return ForkliftUtility.PlanJob(pawn, pallet);
        }
    }
}
