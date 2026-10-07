using HarmonyLib;
using UnityEngine;
using Verse;

namespace CropGenetics
{
    public class CropGeneticsSettings : ModSettings
    {
        public float improveChance = 0.02f;   // per harvested plant
        public float improveStep = 0.01f;     // added to one stat on improvement
        public float mutationChance = 0.004f; // per harvested plant
        public float mutationSize = 0.08f;    // max swing, can be negative
        public float maxMult = 2f;            // cap for yield and growth multipliers
        public float minMult = 0.5f;          // floor for the same
        public float maxHardiness = 1f;       // cap for hardiness (0 to 1)

        public override void ExposeData()
        {
            Scribe_Values.Look(ref improveChance, "improveChance", 0.02f);
            Scribe_Values.Look(ref improveStep, "improveStep", 0.01f);
            Scribe_Values.Look(ref mutationChance, "mutationChance", 0.004f);
            Scribe_Values.Look(ref mutationSize, "mutationSize", 0.08f);
            Scribe_Values.Look(ref maxMult, "maxMult", 2f);
            Scribe_Values.Look(ref minMult, "minMult", 0.5f);
            Scribe_Values.Look(ref maxHardiness, "maxHardiness", 1f);
        }
    }

    public class CropGeneticsMod : Mod
    {
        public static CropGeneticsSettings Settings;

        public CropGeneticsMod(ModContentPack content) : base(content)
        {
            Settings = GetSettings<CropGeneticsSettings>();
            new Harmony(content.PackageIdPlayerFacing).PatchAll();
        }

        public override string SettingsCategory()
        {
            return "CropGenetics_SettingsCategory".Translate();
        }

        public override void DoSettingsWindowContents(Rect inRect)
        {
            var l = new Listing_Standard();
            l.Begin(inRect);
            Slider(l, ref Settings.improveChance, 0f, 0.2f, "CropGenetics_ImproveChance", "P1");
            Slider(l, ref Settings.improveStep, 0.001f, 0.1f, "CropGenetics_ImproveStep", "P1");
            Slider(l, ref Settings.mutationChance, 0f, 0.05f, "CropGenetics_MutationChance", "P1");
            Slider(l, ref Settings.mutationSize, 0.01f, 0.3f, "CropGenetics_MutationSize", "P0");
            Slider(l, ref Settings.maxMult, 1f, 5f, "CropGenetics_MaxMult", "P0");
            Slider(l, ref Settings.minMult, 0.1f, 1f, "CropGenetics_MinMult", "P0");
            Slider(l, ref Settings.maxHardiness, 0f, 1f, "CropGenetics_MaxHardiness", "P0");
            if (l.ButtonText("CropGenetics_ResetSettings".Translate()))
            {
                var d = new CropGeneticsSettings();
                Settings.improveChance = d.improveChance;
                Settings.improveStep = d.improveStep;
                Settings.mutationChance = d.mutationChance;
                Settings.mutationSize = d.mutationSize;
                Settings.maxMult = d.maxMult;
                Settings.minMult = d.minMult;
                Settings.maxHardiness = d.maxHardiness;
            }
            l.End();
        }

        private static void Slider(Listing_Standard l, ref float value, float min, float max, string key, string format)
        {
            l.Label(((string)key.Translate()) + ": " + value.ToString(format));
            value = l.Slider(value, min, max);
        }
    }
}
