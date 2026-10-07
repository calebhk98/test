using UnityEngine;
using Verse;

namespace AdaptiveRaiders
{
    public class AdaptiveSettings : ModSettings
    {
        public bool enableStrategy = true;
        public bool enablePathing = true;
        public bool includeMechanoids = false;
        public float minDeathsToLearn = 3f;
        public float avoidChanceMin = 0.4f;
        public float avoidChanceMax = 0.9f;
        public float dropChance = 0.2f;
        public float halfLifeDays = 20f;
        public int deathRadius = 3;
        public float pathCostPerHeat = 40f;
        public float pathMaxCost = 600f;

        public override void ExposeData()
        {
            Scribe_Values.Look(ref enableStrategy, "enableStrategy", true);
            Scribe_Values.Look(ref enablePathing, "enablePathing", true);
            Scribe_Values.Look(ref includeMechanoids, "includeMechanoids", false);
            Scribe_Values.Look(ref minDeathsToLearn, "minDeathsToLearn", 3f);
            Scribe_Values.Look(ref avoidChanceMin, "avoidChanceMin", 0.4f);
            Scribe_Values.Look(ref avoidChanceMax, "avoidChanceMax", 0.9f);
            Scribe_Values.Look(ref dropChance, "dropChance", 0.2f);
            Scribe_Values.Look(ref halfLifeDays, "halfLifeDays", 20f);
            Scribe_Values.Look(ref deathRadius, "deathRadius", 3);
            Scribe_Values.Look(ref pathCostPerHeat, "pathCostPerHeat", 40f);
            Scribe_Values.Look(ref pathMaxCost, "pathMaxCost", 600f);
        }
    }

    public class AdaptiveRaidersMod : Mod
    {
        public static AdaptiveSettings Settings;

        public AdaptiveRaidersMod(ModContentPack content) : base(content)
        {
            Settings = GetSettings<AdaptiveSettings>();
            var harmony = new HarmonyLib.Harmony(content.PackageIdPlayerFacing);
            harmony.PatchAll();
        }

        public override string SettingsCategory() => "AR_SettingsCategory".Translate();

        public override void DoSettingsWindowContents(Rect inRect)
        {
            var l = new Listing_Standard();
            l.Begin(inRect);
            l.CheckboxLabeled("AR_EnableStrategy".Translate(), ref Settings.enableStrategy, "AR_EnableStrategyTip".Translate());
            l.CheckboxLabeled("AR_EnablePathing".Translate(), ref Settings.enablePathing, "AR_EnablePathingTip".Translate());
            l.CheckboxLabeled("AR_IncludeMechs".Translate(), ref Settings.includeMechanoids, "AR_IncludeMechsTip".Translate());
            Slider(l, "AR_MinDeaths", ref Settings.minDeathsToLearn, 1f, 15f, "F1");
            Slider(l, "AR_AvoidMin", ref Settings.avoidChanceMin, 0f, 1f, "P0");
            Slider(l, "AR_AvoidMax", ref Settings.avoidChanceMax, 0f, 1f, "P0");
            Slider(l, "AR_DropChance", ref Settings.dropChance, 0f, 1f, "P0");
            Slider(l, "AR_HalfLife", ref Settings.halfLifeDays, 2f, 120f, "F0");
            float r = Settings.deathRadius;
            Slider(l, "AR_Radius", ref r, 1f, 8f, "F0");
            Settings.deathRadius = Mathf.RoundToInt(r);
            Slider(l, "AR_PathCost", ref Settings.pathCostPerHeat, 5f, 200f, "F0");
            Slider(l, "AR_PathMax", ref Settings.pathMaxCost, 50f, 3000f, "F0");
            if (Settings.avoidChanceMax < Settings.avoidChanceMin) Settings.avoidChanceMax = Settings.avoidChanceMin;
            l.End();
        }

        private static void Slider(Listing_Standard l, string key, ref float value, float min, float max, string fmt)
        {
            l.Label(key.Translate() + ": " + value.ToString(fmt));
            value = l.Slider(value, min, max);
        }
    }
}
