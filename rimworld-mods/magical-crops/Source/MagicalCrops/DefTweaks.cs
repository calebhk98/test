using System.Collections.Generic;
using RimWorld;
using Verse;

namespace MagicalCrops
{
    // Applies the mod settings to the loaded defs. Base values are captured once.
    [StaticConstructorOnStartup]
    public static class DefTweaks
    {
        static readonly Dictionary<string, float> baseYield = new Dictionary<string, float>();
        static readonly Dictionary<string, float> baseHeat = new Dictionary<string, float>();
        static readonly Dictionary<string, float> baseMood = new Dictionary<string, float>();
        static readonly Dictionary<string, List<ResearchProjectDef>> basePrereqs = new Dictionary<string, List<ResearchProjectDef>>();

        static readonly string[] resourcePlants = { "MC_Plant_SteelVine", "MC_Plant_StoneGourd" };
        static readonly string[] heatPlants = { "MC_Plant_HeatPepper", "MC_Plant_FrostLily" };
        static readonly string[] allPlants =
        {
            "MC_Plant_HealrootPlus", "MC_Plant_MoodBloom", "MC_Plant_SteelVine", "MC_Plant_StoneGourd",
            "MC_Plant_GlowCap", "MC_Plant_HeatPepper", "MC_Plant_FrostLily", "MC_Plant_ManaBean"
        };

        static DefTweaks()
        {
            Apply();
        }

        public static void Apply()
        {
            var s = MagicalCropsMod.Settings;
            if (s == null) return;

            foreach (var name in resourcePlants)
            {
                var plant = DefDatabase<ThingDef>.GetNamedSilentFail(name)?.plant;
                if (plant == null) continue;
                if (!baseYield.ContainsKey(name)) baseYield[name] = plant.harvestYield;
                plant.harvestYield = UnityEngine.Mathf.Max(1f, baseYield[name] * s.resourceYieldMult);
            }

            foreach (var name in heatPlants)
            {
                var props = DefDatabase<ThingDef>.GetNamedSilentFail(name)?.GetCompProperties<CompProperties_HeatPusher>();
                if (props == null) continue;
                if (!baseHeat.ContainsKey(name)) baseHeat[name] = props.heatPerSecond;
                props.heatPerSecond = baseHeat[name] * s.heatMult;
            }

            var thought = DefDatabase<ThoughtDef>.GetNamedSilentFail("MC_PrettyFlowers");
            if (thought?.stages != null)
            {
                for (int i = 0; i < thought.stages.Count; i++)
                {
                    string key = "t" + i;
                    if (!baseMood.ContainsKey(key)) baseMood[key] = thought.stages[i].baseMoodEffect;
                    thought.stages[i].baseMoodEffect = baseMood[key] * s.moodMult;
                }
            }

            foreach (var name in allPlants)
            {
                var plant = DefDatabase<ThingDef>.GetNamedSilentFail(name)?.plant;
                if (plant == null) continue;
                if (!basePrereqs.ContainsKey(name))
                    basePrereqs[name] = plant.sowResearchPrerequisites != null ? new List<ResearchProjectDef>(plant.sowResearchPrerequisites) : new List<ResearchProjectDef>();
                plant.sowResearchPrerequisites = s.requireResearch ? new List<ResearchProjectDef>(basePrereqs[name]) : new List<ResearchProjectDef>();
            }
        }
    }
}
