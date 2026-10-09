using System.Collections.Generic;
using HarmonyLib;
using RimWorld;
using UnityEngine;
using Verse;

namespace RemoteSurrogate
{
    /// <summary>
    /// A surrogate never dies. Pawn.Kill is intercepted before any of the death side effects run
    /// (corpse, "colonist died" thoughts for everyone else, letters, tales, storyteller counters),
    /// and the link is ended instead on the next tick.
    /// </summary>
    [HarmonyPatch(typeof(Pawn), nameof(Pawn.Kill))]
    public static class Patch_Pawn_Kill
    {
        public static bool Prefix(Pawn __instance)
        {
            Hediff_SurrogateBody h = Hediff_SurrogateBody.Of(__instance);
            if (h == null) return true;
            Building_LinkPod pod = h.pod;
            if (pod == null || pod.Destroyed || !pod.Spawned || pod.Operator == null) return true; // orphan: let it die normally
            pod.QueueEnd(LinkEndReason.BodyLost);
            return false;
        }
    }

    [HarmonyPatch(typeof(Pawn), nameof(Pawn.GetGizmos))]
    public static class Patch_Pawn_GetGizmos
    {
        public static IEnumerable<Gizmo> Postfix(IEnumerable<Gizmo> __result, Pawn __instance)
        {
            foreach (Gizmo g in __result) yield return g;
            Hediff_SurrogateBody h = Hediff_SurrogateBody.Of(__instance);
            if (h?.pod != null && __instance.Faction == Faction.OfPlayer)
            {
                Building_LinkPod pod = h.pod;
                yield return new Command_Action
                {
                    defaultLabel = "RS_Disconnect".Translate(),
                    defaultDesc = "RS_DisconnectDesc".Translate(),
                    icon = ContentFinder<Texture2D>.Get("UI/RS_Disconnect"),
                    action = () => pod.EndLink(LinkEndReason.Disconnected)
                };
            }
        }
    }

    /// <summary>Remembers the experience a surrogate earns so part of it can go back to the operator.</summary>
    [HarmonyPatch(typeof(SkillRecord), nameof(SkillRecord.Learn))]
    public static class Patch_SkillRecord_Learn
    {
        private static readonly AccessTools.FieldRef<SkillRecord, Pawn> PawnRef =
            AccessTools.FieldRefAccess<SkillRecord, Pawn>("pawn");

        public static void Postfix(SkillRecord __instance, float xp, bool direct, bool ignoreLearnRate)
        {
            if (xp <= 0f) return;
            Pawn p = PawnRef(__instance);
            Hediff_SurrogateBody h = Hediff_SurrogateBody.Of(p);
            if (h == null) return;
            float eff = ignoreLearnRate ? xp : xp * __instance.LearnRateFactor(direct);
            h.AddXp(__instance.def, eff);
        }
    }
}
