using HarmonyLib;
using RimWorld;
using Verse;

namespace DigitalStorage
{
    /// <summary>
    /// Makes "Do until you have X" bills count items held in online cores, so a bill does not keep
    /// building something the network already has. Pattern adapted from Project RimFactory's
    /// Patch_RecipeWorkerCounter_CountProducts (MIT licence, Project RimFactory contributors).
    /// Only counts; ingredient search still needs the access point's spawned working stock.
    /// </summary>
    [HarmonyPatch(typeof(RecipeWorkerCounter), nameof(RecipeWorkerCounter.CountProducts))]
    public static class Patch_CountProducts
    {
        public static void Postfix(RecipeWorkerCounter __instance, ref int __result, Bill_Production bill)
        {
            if (!DSMod.Settings.countInBills) return;
            if (bill.GetIncludeSlotGroup() != null) return;
            Map map = bill.Map;
            var products = __instance.recipe?.products;
            if (map == null || products == null || products.Count == 0) return;
            ThingDef target = products[0].thingDef;
            foreach (Building_DSCore core in DSNet.CoresOnMap(map))
                if (core.Online) __result += core.CountOf(target);
        }
    }
}

namespace DigitalStorage
{
    /// <summary>Input ports only accept items an online core in range can actually take.</summary>
    [HarmonyLib.HarmonyPatch(typeof(RimWorld.Building_Storage), "Accepts")]
    public static class Patch_StorageAccepts
    {
        public static void Postfix(RimWorld.Building_Storage __instance, ref bool __result, Verse.Thing t)
        {
            if (__result && __instance is Building_DSInputPort port) __result = port.NetworkAccepts(t);
        }
    }
}
