using UnityEngine;
using Verse;

namespace StorytellerHundred
{
    public class HundredSettings : ModSettings
    {
        public int target = 100;
        public float rate = 1f;
        public bool relaxAfterTarget = true;
        public bool letters = true;

        public override void ExposeData()
        {
            Scribe_Values.Look(ref target, "target", 100);
            Scribe_Values.Look(ref rate, "rate", 1f);
            Scribe_Values.Look(ref relaxAfterTarget, "relaxAfterTarget", true);
            Scribe_Values.Look(ref letters, "letters", true);
        }
    }

    public class HundredMod : Mod
    {
        public static HundredSettings Settings;

        public HundredMod(ModContentPack content) : base(content)
        {
            Settings = GetSettings<HundredSettings>();
        }

        public override string SettingsCategory()
        {
            return "SH_SettingsTitle".Translate();
        }

        public override void DoSettingsWindowContents(Rect inRect)
        {
            var l = new Listing_Standard();
            l.Begin(inRect);
            l.Label("SH_Target".Translate() + ": " + Settings.target);
            Settings.target = Mathf.RoundToInt(l.Slider(Settings.target, 10, 300));
            l.Label("SH_Rate".Translate() + ": " + Settings.rate.ToString("0.0#") + "x");
            Settings.rate = Mathf.Round(l.Slider(Settings.rate, 0.25f, 4f) * 4f) / 4f;
            l.CheckboxLabeled("SH_RelaxAfter".Translate(), ref Settings.relaxAfterTarget, "SH_RelaxAfterTip".Translate());
            l.CheckboxLabeled("SH_Letters".Translate(), ref Settings.letters);
            l.End();
        }
    }
}
