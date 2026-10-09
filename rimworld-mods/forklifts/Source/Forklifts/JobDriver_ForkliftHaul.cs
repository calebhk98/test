using System.Collections.Generic;
using System.Linq;
using RimWorld;
using Verse;
using Verse.AI;

namespace Forklifts
{
    /// <summary>
    /// A = pallet, B (queue) = stacks to load, C = destination cell.
    /// The operator lifts the pallet, visits each stack and loads it straight onto the
    /// forks, drives to the destination once and unloads every stack there.
    /// </summary>
    public class JobDriver_ForkliftHaul : JobDriver
    {
        private const TargetIndex PalletInd = TargetIndex.A;
        private const TargetIndex ItemInd = TargetIndex.B;
        private const TargetIndex DestInd = TargetIndex.C;

        public override bool TryMakePreToilReservations(bool errorOnFailed)
        {
            if (!pawn.Reserve(job.GetTarget(PalletInd), job, 1, -1, null, errorOnFailed)) return false;
            pawn.ReserveAsManyAsPossible(job.GetTargetQueue(ItemInd), job);
            return true;
        }

        protected override IEnumerable<Toil> MakeNewToils()
        {
            AddFinishAction(delegate { Finish(); });

            this.FailOnDestroyedOrNull(PalletInd);
            yield return Toils_Goto.GotoThing(PalletInd, PathEndMode.ClosestTouch);
            yield return Toils_Haul.StartCarryThing(PalletInd, false, false, false, true, false);

            Toil extract = Toils_JobTransforms.ExtractNextTargetFromQueue(ItemInd, false);
            Toil afterLoad = Toils_Jump.JumpIfHaveTargetInQueue(ItemInd, extract);
            Toil toDest = Toils_Goto.GotoCell(DestInd, PathEndMode.OnCell);

            yield return Toils_Jump.JumpIfHaveTargetInQueue(ItemInd, extract);
            yield return Toils_Jump.Jump(toDest);

            yield return extract;
            yield return Toils_Jump.JumpIf(afterLoad, ItemInvalid);
            yield return Toils_Goto.GotoThing(ItemInd, PathEndMode.Touch);
            yield return Toils_General.Wait(System.Math.Max(1, ForkliftsMod.Settings.loadTicks), ItemInd);
            yield return LoadToil();
            yield return afterLoad;

            // Nothing loaded: end quietly.
            yield return Toils_Jump.JumpIf(toDest, () => CarriedPallet() != null && !CarriedPallet().Empty);
            yield return new Toil
            {
                initAction = delegate { EndJobWith(JobCondition.Incompletable); },
                defaultCompleteMode = ToilCompleteMode.Instant
            };

            yield return toDest;
            yield return UnloadToil();
        }

        private Pallet CarriedPallet()
        {
            return pawn.carryTracker?.CarriedThing as Pallet;
        }

        private bool ItemInvalid()
        {
            Thing item = job.GetTarget(ItemInd).Thing;
            Pallet pallet = CarriedPallet();
            if (pallet == null || pallet.Full) return true;
            return item == null || item.Destroyed || !item.Spawned || item.IsForbidden(pawn);
        }

        private Toil LoadToil()
        {
            var toil = new Toil();
            toil.defaultCompleteMode = ToilCompleteMode.Instant;
            toil.initAction = delegate
            {
                if (ItemInvalid()) return;
                Pallet pallet = CarriedPallet();
                Thing item = job.GetTarget(ItemInd).Thing;
                IntVec3 where = item.Position;
                Map map = item.Map;
                item.DeSpawn();
                if (!pallet.inner.TryAdd(item, false))
                {
                    GenPlace.TryPlaceThing(item, where, map, ThingPlaceMode.Near);
                }
            };
            return toil;
        }

        private Toil UnloadToil()
        {
            var toil = new Toil();
            toil.defaultCompleteMode = ToilCompleteMode.Instant;
            toil.initAction = delegate
            {
                Pallet pallet = CarriedPallet();
                if (pallet == null) return;
                IntVec3 dest = job.GetTarget(DestInd).Cell;
                Map map = pawn.Map;
                foreach (Thing t in pallet.inner.ToList())
                {
                    Thing placed;
                    bool ok = pallet.inner.TryDrop(t, dest, map, ThingPlaceMode.Near, out placed, null,
                        c => StoreUtility.IsValidStorageFor(c, map, t), false);
                    if (!ok)
                    {
                        pallet.inner.TryDrop(t, pawn.Position, map, ThingPlaceMode.Near, out placed, null, null, false);
                    }
                }
            };
            return toil;
        }

        /// <summary>Runs on every way the job can end: nothing stays stuck on the pallet.</summary>
        private void Finish()
        {
            Pallet pallet = CarriedPallet();
            if (pallet == null || pawn.Map == null) return;
            if (!pallet.Empty)
            {
                pallet.inner.TryDropAll(pawn.Position, pawn.Map, ThingPlaceMode.Near);
            }
            pawn.carryTracker.TryDropCarriedThing(pawn.Position, ThingPlaceMode.Near, out Thing _);
        }
    }
}
