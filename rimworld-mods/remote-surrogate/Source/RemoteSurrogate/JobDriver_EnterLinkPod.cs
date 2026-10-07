using System.Collections.Generic;
using RimWorld;
using Verse;
using Verse.AI;

namespace RemoteSurrogate
{
    public class JobDriver_EnterLinkPod : JobDriver
    {
        private Building_LinkPod Pod => job.targetA.Thing as Building_LinkPod;

        public override bool TryMakePreToilReservations(bool errorOnFailed)
        {
            return pawn.Reserve(job.targetA, job, 1, -1, null, errorOnFailed);
        }

        protected override IEnumerable<Toil> MakeNewToils()
        {
            this.FailOnDespawnedOrNull(TargetIndex.A);
            yield return Toils_Goto.GotoThing(TargetIndex.A, PathEndMode.InteractionCell);
            Toil wait = Toils_General.Wait(60, TargetIndex.A);
            wait.WithProgressBarToilDelay(TargetIndex.A);
            yield return wait;
            Toil enter = ToilMaker.MakeToil("RS_Enter");
            enter.initAction = () =>
            {
                Building_LinkPod pod = Pod;
                if (pod == null || !pod.TryStartLink(pawn))
                {
                    Messages.Message("RS_LinkFailed".Translate(), pawn, MessageTypeDefOf.RejectInput, false);
                }
            };
            enter.defaultCompleteMode = ToilCompleteMode.Instant;
            yield return enter;
        }
    }
}
