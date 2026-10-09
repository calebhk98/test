using UnityEngine;
using Verse;

namespace EndlessSiege
{
    public class EndlessSiegeSettings : ModSettings
    {
        public bool enabled = true;
        public bool mixFactions = false;
        public float hoursBetweenWaves = 1f;
        public float pointsFraction = 0.12f;
        public float growthPerDay = 0.05f;
        public float maxPointsMultiplier = 4f;
        public int liveEnemyCap = 40;
        public bool cleanupCorpses = true;
        public float corpseLifetimeHours = 12f;
        public int quietEveryWaves = 0;
        public float quietHours = 6f;
        public int surviveDays = 0;

        public override void ExposeData()
        {
            Scribe_Values.Look(ref enabled, "enabled", true);
            Scribe_Values.Look(ref mixFactions, "mixFactions", false);
            Scribe_Values.Look(ref hoursBetweenWaves, "hoursBetweenWaves", 1f);
            Scribe_Values.Look(ref pointsFraction, "pointsFraction", 0.12f);
            Scribe_Values.Look(ref growthPerDay, "growthPerDay", 0.05f);
            Scribe_Values.Look(ref maxPointsMultiplier, "maxPointsMultiplier", 4f);
            Scribe_Values.Look(ref liveEnemyCap, "liveEnemyCap", 40);
            Scribe_Values.Look(ref cleanupCorpses, "cleanupCorpses", true);
            Scribe_Values.Look(ref corpseLifetimeHours, "corpseLifetimeHours", 12f);
            Scribe_Values.Look(ref quietEveryWaves, "quietEveryWaves", 0);
            Scribe_Values.Look(ref quietHours, "quietHours", 6f);
            Scribe_Values.Look(ref surviveDays, "surviveDays", 0);
        }
    }

    public class EndlessSiegeMod : Mod
    {
        public static EndlessSiegeSettings Settings;
        private Vector2 scroll;

        public EndlessSiegeMod(ModContentPack content) : base(content)
        {
            Settings = GetSettings<EndlessSiegeSettings>();
            // No Harmony patches are needed: everything runs from a MapComponent.
        }

        public override string SettingsCategory()
        {
            return "ES_Category".Translate();
        }

        public override void DoSettingsWindowContents(Rect inRect)
        {
            var s = Settings;
            var view = new Rect(0f, 0f, inRect.width - 20f, 640f);
            Widgets.BeginScrollView(inRect, ref scroll, view);
            var l = new Listing_Standard();
            l.Begin(view);
            l.CheckboxLabeled("ES_Enabled".Translate(), ref s.enabled);
            l.CheckboxLabeled("ES_Mix".Translate(), ref s.mixFactions, "ES_MixTip".Translate());
            s.hoursBetweenWaves = Slider(l, "ES_Interval".Translate(s.hoursBetweenWaves.ToString("0.#")), s.hoursBetweenWaves, 0.25f, 12f);
            s.pointsFraction = Slider(l, "ES_Fraction".Translate(s.pointsFraction.ToString("P0")), s.pointsFraction, 0.02f, 0.6f);
            s.growthPerDay = Slider(l, "ES_Growth".Translate(s.growthPerDay.ToString("P0")), s.growthPerDay, 0f, 0.5f);
            s.maxPointsMultiplier = Slider(l, "ES_MaxMult".Translate(s.maxPointsMultiplier.ToString("0.#")), s.maxPointsMultiplier, 1f, 10f);
            s.liveEnemyCap = Mathf.RoundToInt(Slider(l, "ES_Cap".Translate(s.liveEnemyCap), s.liveEnemyCap, 5f, 200f));
            l.GapLine();
            l.CheckboxLabeled("ES_Cleanup".Translate(), ref s.cleanupCorpses, "ES_CleanupTip".Translate());
            if (s.cleanupCorpses)
                s.corpseLifetimeHours = Slider(l, "ES_CorpseHours".Translate(s.corpseLifetimeHours.ToString("0.#")), s.corpseLifetimeHours, 1f, 120f);
            l.GapLine();
            s.quietEveryWaves = Mathf.RoundToInt(Slider(l, "ES_QuietEvery".Translate(s.quietEveryWaves), s.quietEveryWaves, 0f, 48f));
            if (s.quietEveryWaves > 0)
                s.quietHours = Slider(l, "ES_QuietHours".Translate(s.quietHours.ToString("0.#")), s.quietHours, 1f, 48f);
            s.surviveDays = Mathf.RoundToInt(Slider(l, "ES_SurviveDays".Translate(s.surviveDays), s.surviveDays, 0f, 120f));
            l.End();
            Widgets.EndScrollView();
        }

        private static float Slider(Listing_Standard l, string label, float val, float min, float max)
        {
            l.Label(label);
            return l.Slider(val, min, max);
        }
    }
}
