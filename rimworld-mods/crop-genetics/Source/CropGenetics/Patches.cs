using System.Collections.Generic;
using HarmonyLib;
using RimWorld;
using UnityEngine;
using Verse;

namespace CropGenetics
{
    public static class StrainUtil
    {
        /// <summary>The strain a planted crop grows under, or null (wild plants, no zone).</summary>
        public static Strain StrainFor(Plant p)
        {
            if (p == null || !p.Spawned || !p.sown) return null;
            var zone = p.Map.zoneManager.ZoneAt(p.Position) as Zone_Growing;
            if (zone == null) return null;
            StrainLibrary lib = StrainLibrary.Instance;
            return lib == null ? null : lib.PeekStrain(zone, p.def);
        }

        public static Zone_Growing ZoneFor(Plant p)
        {
            if (p == null || !p.Spawned) return null;
            return p.Map.zoneManager.ZoneAt(p.Position) as Zone_Growing;
        }

        /// <summary>Roll one harvest's chance to improve or mutate the zone strain.</summary>
        public static void RollHarvest(Zone_Growing zone)
        {
            StrainLibrary lib = StrainLibrary.Instance;
            if (lib == null) return;
            Strain s = lib.GetStrain(zone);
            if (s == null) return;
            CropGeneticsSettings set = CropGeneticsMod.Settings;

            if (Rand.Chance(set.improveChance))
            {
                Bump(s, Rand.RangeInclusive(0, 2), set.improveStep, set);
                s.generation++;
            }
            if (Rand.Chance(set.mutationChance))
            {
                float delta = Rand.Range(-set.mutationSize, set.mutationSize);
                Bump(s, Rand.RangeInclusive(0, 2), delta, set);
                s.generation++;
            }
        }

        private static void Bump(Strain s, int stat, float delta, CropGeneticsSettings set)
        {
            switch (stat)
            {
                case 0: s.yieldMult = Mathf.Clamp(s.yieldMult + delta, set.minMult, set.maxMult); break;
                case 1: s.growthMult = Mathf.Clamp(s.growthMult + delta, set.minMult, set.maxMult); break;
                default: s.hardiness = Mathf.Clamp(s.hardiness + delta, 0f, set.maxHardiness); break;
            }
        }
    }

    [HarmonyPatch(typeof(Plant), nameof(Plant.GrowthRate), MethodType.Getter)]
    public static class Patch_Plant_GrowthRate
    {
        public static void Postfix(Plant __instance, ref float __result)
        {
            Strain s = StrainUtil.StrainFor(__instance);
            if (s != null) __result *= s.growthMult;
        }
    }

    // Hardiness: pulls a poor temperature factor toward 1.
    [HarmonyPatch(typeof(Plant), nameof(Plant.GrowthRateFactor_Temperature), MethodType.Getter)]
    public static class Patch_Plant_TemperatureFactor
    {
        public static void Postfix(Plant __instance, ref float __result)
        {
            if (__result >= 1f) return;
            Strain s = StrainUtil.StrainFor(__instance);
            if (s != null && s.hardiness > 0f) __result = Mathf.Lerp(__result, 1f, s.hardiness);
        }
    }

    [HarmonyPatch(typeof(Plant), nameof(Plant.YieldNow))]
    public static class Patch_Plant_YieldNow
    {
        public static void Postfix(Plant __instance, ref int __result)
        {
            if (__result <= 0) return;
            Strain s = StrainUtil.StrainFor(__instance);
            if (s == null || s.yieldMult == 1f) return;
            // Round to nearest but never turn a real harvest into zero.
            __result = Mathf.Max(1, Mathf.RoundToInt(__result * s.yieldMult));
        }
    }

    // Harvest rolls for improvement or mutation. HarvestableNow is read before the plant is removed.
    [HarmonyPatch(typeof(Plant), nameof(Plant.PlantCollected))]
    public static class Patch_Plant_PlantCollected
    {
        public static void Prefix(Plant __instance, Pawn by)
        {
            if (by == null || !__instance.sown || !__instance.HarvestableNow) return;
            Zone_Growing zone = StrainUtil.ZoneFor(__instance);
            if (zone != null) StrainUtil.RollHarvest(zone);
        }
    }

    [HarmonyPatch(typeof(Zone_Growing), nameof(Zone_Growing.GetGizmos))]
    public static class Patch_Zone_Gizmos
    {
        public static IEnumerable<Gizmo> Postfix(IEnumerable<Gizmo> __result, Zone_Growing __instance)
        {
            foreach (Gizmo g in __result) yield return g;
            if (__instance.GetPlantDefToGrow() == null) yield break;

            Zone_Growing zone = __instance;
            yield return new Command_Action
            {
                defaultLabel = "CropGenetics_StrainGizmo".Translate(),
                defaultDesc = "CropGenetics_StrainGizmoDesc".Translate(),
                icon = ContentFinder<Texture2D>.Get("CropGenetics/UI/Strain", false),
                action = () => OpenMenu(zone)
            };
        }

        private static void OpenMenu(Zone_Growing zone)
        {
            StrainLibrary lib = StrainLibrary.Instance;
            ThingDef def = zone.GetPlantDefToGrow();
            if (lib == null || def == null) return;
            Strain current = lib.GetStrain(zone);

            var options = new List<FloatMenuOption>();
            options.Add(new FloatMenuOption("CropGenetics_SaveStrain".Translate(), () =>
            {
                lib.SaveToLibrary(current);
                Messages.Message("CropGenetics_Saved".Translate(), MessageTypeDefOf.TaskCompletion, false);
            }));
            options.Add(new FloatMenuOption("CropGenetics_ResetStrain".Translate(), () => lib.ResetStrain(zone)));
            foreach (Strain s in lib.SavedFor(def))
            {
                Strain captured = s;
                options.Add(new FloatMenuOption("CropGenetics_UseStrain".Translate(captured.name, captured.Summary()), () =>
                {
                    Strain copy = captured.Copy();
                    lib.SetStrain(zone, copy);
                }));
            }
            Find.WindowStack.Add(new FloatMenu(options));
        }
    }

    [HarmonyPatch(typeof(Zone_Growing), nameof(Zone_Growing.GetInspectString))]
    public static class Patch_Zone_Inspect
    {
        public static void Postfix(Zone_Growing __instance, ref string __result)
        {
            StrainLibrary lib = StrainLibrary.Instance;
            if (lib == null || __instance.GetPlantDefToGrow() == null) return;
            Strain s = lib.GetStrain(__instance);
            if (s == null) return;
            string line = "CropGenetics_InspectLine".Translate(s.Summary());
            __result = string.IsNullOrEmpty(__result) ? line : __result + "\n" + line;
        }
    }
}
