using System.Collections.Generic;
using RimWorld;
using Verse;
using Verse.AI;

namespace UndergroundBarn
{
    /// <summary>A handler walks to a designated animal, carries it to the barn and stores it.</summary>
    public class JobDriver_StoreAnimal : JobDriver
    {
        private Pawn Animal => (Pawn)job.GetTarget(TargetIndex.A).Thing;
        private Building_UndergroundBarn Barn => job.GetTarget(TargetIndex.B).Thing as Building_UndergroundBarn;

        public override bool TryMakePreToilReservations(bool errorOnFailed)
        {
            return pawn.Reserve(job.GetTarget(TargetIndex.A), job, 1, -1, null, errorOnFailed);
        }

        protected override IEnumerable<Toil> MakeNewToils()
        {
            this.FailOnDestroyedOrNull(TargetIndex.A);
            this.FailOnDestroyedOrNull(TargetIndex.B);
            this.FailOn(() => Barn == null || !Barn.HasRoom);
            this.FailOn(() => Animal.Faction != Faction.OfPlayer);

            yield return Toils_Goto.GotoThing(TargetIndex.A, PathEndMode.Touch)
                .FailOnDespawnedNullOrForbidden(TargetIndex.A);
            yield return Toils_Haul.StartCarryThing(TargetIndex.A);
            yield return Toils_Goto.GotoThing(TargetIndex.B, PathEndMode.InteractionCell);

            Toil store = ToilMaker.MakeToil("StoreAnimalInBarn");
            store.initAction = () =>
            {
                Pawn carried = pawn.carryTracker.CarriedThing as Pawn;
                if (carried != null && Barn != null && Barn.TryAcceptPawn(carried, pawn))
                    return;
                EndJobWith(JobCondition.Incompletable);
            };
            store.defaultCompleteMode = ToilCompleteMode.Instant;
            yield return store;
        }
    }
}
