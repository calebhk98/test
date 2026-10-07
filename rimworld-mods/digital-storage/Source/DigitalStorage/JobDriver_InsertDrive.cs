using System.Collections.Generic;
using RimWorld;
using Verse;
using Verse.AI;

namespace DigitalStorage
{
    /// <summary>A colonist fetches a drive (target A) and slots it into a core (target B).</summary>
    public class JobDriver_InsertDrive : JobDriver
    {
        public override bool TryMakePreToilReservations(bool errorOnFailed)
        {
            return pawn.Reserve(job.GetTarget(TargetIndex.A), job, 1, -1, null, errorOnFailed)
                && pawn.Reserve(job.GetTarget(TargetIndex.B), job, 1, -1, null, errorOnFailed);
        }

        protected override IEnumerable<Toil> MakeNewToils()
        {
            this.FailOnDestroyedOrNull(TargetIndex.A);
            this.FailOnDestroyedOrNull(TargetIndex.B);
            this.FailOnForbidden(TargetIndex.A);
            yield return Toils_Goto.GotoThing(TargetIndex.A, PathEndMode.ClosestTouch).FailOnSomeonePhysicallyInteracting(TargetIndex.A);
            yield return Toils_Haul.StartCarryThing(TargetIndex.A, false, false, false, true, false);
            yield return Toils_Goto.GotoThing(TargetIndex.B, PathEndMode.Touch);
            yield return Toils_General.Wait(60, TargetIndex.B).WithProgressBarToilDelay(TargetIndex.B);
            yield return Toils_General.Do(delegate
            {
                var core = (Building_DSCore)job.GetTarget(TargetIndex.B).Thing;
                Thing carried = pawn.carryTracker.CarriedThing;
                if (carried == null || !core.TryInsertDrive(pawn, carried))
                {
                    Messages.Message("DS_NoFreeSlot".Translate(), core, MessageTypeDefOf.RejectInput, false);
                    pawn.carryTracker.TryDropCarriedThing(pawn.Position, ThingPlaceMode.Near, out Thing _);
                }
            });
        }
    }
}
