using RimWorld;
using UnityEngine;
using Verse;

namespace MagicalCrops
{
    public class MagicalCropsSettings : ModSettings
    {
        public bool requireResearch = true;
        public float resourceYieldMult = 1f;   // steel vine, stone gourd
        public float heatMult = 1f;            // heat pepper, frost lily
        public float moodMult = 1f;            // mood bloom thought strength
        public int bloomRadius = 3;

        public override void ExposeData()
        {
            Scribe_Values.Look(ref requireResearch, "requireResearch", true);
            Scribe_Values.Look(ref resourceYieldMult, "resourceYieldMult", 1f);
            Scribe_Values.Look(ref heatMult, "heatMult", 1f);
            Scribe_Values.Look(ref moodMult, "moodMult", 1f);
            Scribe_Values.Look(ref bloomRadius, "bloomRadius", 3);
        }
    }

    public class MagicalCropsMod : Mod
    {
        public static MagicalCropsSettings Settings;

        public MagicalCropsMod(ModContentPack content) : base(content)
        {
            Settings = GetSettings<MagicalCropsSettings>();
        }

        public override string SettingsCategory() => "MC_SettingsCategory".Translate();

        public override void DoSettingsWindowContents(Rect inRect)
        {
            var l = new Listing_Standard();
            l.Begin(inRect);
            l.CheckboxLabeled("MC_RequireResearch".Translate(), ref Settings.requireResearch, "MC_RequireResearchTip".Translate());
            l.Label("MC_YieldMult".Translate(Settings.resourceYieldMult.ToString("0.00")));
            Settings.resourceYieldMult = l.Slider(Settings.resourceYieldMult, 0.25f, 4f);
            l.Label("MC_HeatMult".Translate(Settings.heatMult.ToString("0.00")));
            Settings.heatMult = l.Slider(Settings.heatMult, 0f, 4f);
            l.Label("MC_MoodMult".Translate(Settings.moodMult.ToString("0.00")));
            Settings.moodMult = l.Slider(Settings.moodMult, 0f, 4f);
            l.Label("MC_BloomRadius".Translate(Settings.bloomRadius));
            Settings.bloomRadius = Mathf.RoundToInt(l.Slider(Settings.bloomRadius, 1f, 6f));
            l.Label("MC_RestartNote".Translate());
            l.End();
        }

        public override void WriteSettings()
        {
            base.WriteSettings();
            DefTweaks.Apply();
        }
    }
}
