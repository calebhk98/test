using System.Collections.Generic;
using System.Linq;
using RimWorld;
using Verse;
using Verse.AI;

namespace Forklifts
{
    public static class ForkliftUtility
    {
        public static bool IsOperator(Pawn pawn)
        {
            if (pawn?.apparel == null) return false;
            List<Apparel> worn = pawn.apparel.WornApparel;
            for (int i = 0; i < worn.Count; i++)
            {
                if (worn[i].def == ForkliftsDefOf.Forklifts_Forklift) return true;
            }
            return false;
        }

        public static Pallet FindPallet(Pawn pawn)
        {
            Map map = pawn.Map;
            List<Thing> pallets = map.listerThings.ThingsOfDef(ForkliftsDefOf.Forklifts_Pallet);
            Pallet best = null;
            float bestDist = float.MaxValue;
            for (int i = 0; i < pallets.Count; i++)
            {
                var p = pallets[i] as Pallet;
                if (p == null || !p.Spawned || !p.Empty) continue;
                float d = (p.Position - pawn.Position).LengthHorizontalSquared;
                if (d >= bestDist) continue;
                if (p.IsForbidden(pawn)) continue;
                if (!pawn.CanReserve(p)) continue;
                best = p;
                bestDist = d;
            }
            if (best != null && !pawn.CanReach(best, PathEndMode.ClosestTouch, Danger.Deadly)) return null;
            return best;
        }

        /// <summary>
        /// Builds one job that loads many hauls onto the pallet. Returns null when there are
        /// fewer worthwhile stacks than the minimum, so normal hauling takes over.
        /// </summary>
        public static Job PlanJob(Pawn pawn, Pallet pallet)
        {
            ForkliftsSettings s = ForkliftsMod.Settings;
            Map map = pawn.Map;
            ICollection<Thing> haulables = map.listerHaulables.ThingsPotentiallyNeedingHauling();
            if (haulables == null || haulables.Count < s.minStacksPerTrip) return null;

            var candidates = new List<Thing>();
            int scanned = 0;
            foreach (Thing t in haulables)
            {
                if (++scanned > 600) break;
                if (t == pallet || t is Pallet || !t.Spawned || t.def == ForkliftsDefOf.Forklifts_Forklift) continue;
                candidates.Add(t);
            }
            IntVec3 pos = pawn.Position;
            candidates.Sort((a, b) => (a.Position - pos).LengthHorizontalSquared.CompareTo((b.Position - pos).LengthHorizontalSquared));

            // Find a seed: the nearest stack that can actually be hauled somewhere better.
            Thing seed = null;
            IntVec3 seedDest = IntVec3.Invalid;
            int tries = 0;
            for (int i = 0; i < candidates.Count && tries < 25; i++)
            {
                Thing t = candidates[i];
                if (!IsUsable(pawn, t)) continue;
                tries++;
                if (TryGetDest(pawn, t, out IntVec3 dest))
                {
                    seed = t;
                    seedDest = dest;
                    break;
                }
            }
            if (seed == null) return null;

            SlotGroup seedGroup = seedDest.GetSlotGroup(map);
            int pickupSq = s.pickupRadius * s.pickupRadius;
            int unloadSq = s.unloadRadius * s.unloadRadius;
            var chosen = new List<Thing> { seed };

            var nearSeed = candidates.Where(t => t != seed && (t.Position - seed.Position).LengthHorizontalSquared <= pickupSq).ToList();
            IntVec3 seedPos = seed.Position;
            nearSeed.Sort((a, b) => (a.Position - seedPos).LengthHorizontalSquared.CompareTo((b.Position - seedPos).LengthHorizontalSquared));
            int checks = 0;
            for (int i = 0; i < nearSeed.Count && chosen.Count < pallet.Capacity && checks < 80; i++)
            {
                Thing t = nearSeed[i];
                if (!IsUsable(pawn, t)) continue;
                checks++;
                if (!TryGetDest(pawn, t, out IntVec3 dest)) continue;
                if ((dest - seedDest).LengthHorizontalSquared > unloadSq) continue;
                if (seedGroup != null && !seedGroup.Settings.AllowedToAccept(t)) continue;
                chosen.Add(t);
            }
            if (chosen.Count < s.minStacksPerTrip) return null;

            Job job = JobMaker.MakeJob(ForkliftsDefOf.Forklifts_HaulPallet, pallet);
            job.count = 1;
            job.targetC = seedDest;
            job.targetQueueB = new List<LocalTargetInfo>();
            foreach (Thing t in chosen) job.targetQueueB.Add(t);
            return job;
        }

        private static bool IsUsable(Pawn pawn, Thing t)
        {
            if (!t.Spawned || t.IsForbidden(pawn)) return false;
            if (!HaulAIUtility.PawnCanAutomaticallyHaul(pawn, t, false)) return false;
            return pawn.CanReserve(t);
        }

        private static bool TryGetDest(Pawn pawn, Thing t, out IntVec3 dest)
        {
            return StoreUtility.TryFindBestBetterStoreCellFor(t, pawn, pawn.Map,
                StoreUtility.CurrentStoragePriorityOf(t, false), pawn.Faction, out dest, true);
        }
    }
}
