using System.Collections.Generic;
using System.Linq;
using HarmonyLib;
using RimWorld;
using UnityEngine;
using Verse;

namespace TraitTower
{
    public class TraitTowerMod : Mod
    {
        public static TraitTowerSettings Settings;

        private Vector2 scroll;
        private string filter = "";
        private List<TraitEntry> entries;

        public TraitTowerMod(ModContentPack content) : base(content)
        {
            Settings = GetSettings<TraitTowerSettings>();
            new Harmony(content.PackageIdPlayerFacing).PatchAll();
        }

        public override string SettingsCategory()
        {
            return "TraitTower_SettingsCategory".Translate();
        }

        private class TraitEntry
        {
            public string key;
            public string label;
            public string search;
        }

        private void BuildEntries()
        {
            entries = new List<TraitEntry>();
            foreach (TraitDef def in DefDatabase<TraitDef>.AllDefs)
            {
                foreach (TraitDegreeData data in def.degreeDatas)
                {
                    string label = data.LabelCap.ToString();
                    entries.Add(new TraitEntry
                    {
                        key = TraitTowerSettings.Key(def, data.degree),
                        label = label + "  (" + def.defName + ")",
                        search = (label + " " + def.defName).ToLowerInvariant()
                    });
                }
            }
            entries = entries.OrderBy(e => e.label).ToList();
        }

        public override void DoSettingsWindowContents(Rect inRect)
        {
            Listing_Standard top = new Listing_Standard();
            Rect topRect = new Rect(inRect.x, inRect.y, inRect.width, 200f);
            top.Begin(topRect);
            Settings.chancePerDayPercent = top.SliderLabeled(
                "TraitTower_ChancePerDay".Translate(Settings.chancePerDayPercent.ToString("F1")),
                Settings.chancePerDayPercent, 0.1f, 20f, 0.6f, "TraitTower_ChancePerDayTip".Translate());
            Settings.radius = Mathf.Round(top.SliderLabeled(
                "TraitTower_Radius".Translate(Settings.radius.ToString("F0")),
                Settings.radius, 3f, 40f, 0.6f, "TraitTower_RadiusTip".Translate()));
            Settings.maxTraits = Mathf.RoundToInt(top.SliderLabeled(
                "TraitTower_MaxTraits".Translate(Settings.maxTraits),
                Settings.maxTraits, 1f, 8f, 0.6f, "TraitTower_MaxTraitsTip".Translate()));
            top.CheckboxLabeled("TraitTower_MoodThought".Translate(), ref Settings.moodThought,
                "TraitTower_MoodThoughtTip".Translate());
            top.CheckboxLabeled("TraitTower_Messages".Translate(), ref Settings.showMessages);
            top.CheckboxLabeled("TraitTower_Slaves".Translate(), ref Settings.includeSlaves,
                "TraitTower_SlavesTip".Translate());
            top.End();

            float y = inRect.y + 205f;
            Widgets.Label(new Rect(inRect.x, y, inRect.width, 26f), "TraitTower_ListHelp".Translate());
            y += 28f;
            Widgets.Label(new Rect(inRect.x, y + 3f, 70f, 26f), "TraitTower_Search".Translate());
            filter = Widgets.TextField(new Rect(inRect.x + 75f, y, 240f, 28f), filter);
            if (Widgets.ButtonText(new Rect(inRect.xMax - 320f, y, 150f, 28f), "TraitTower_ResetLists".Translate()))
            {
                Settings.ResetLists();
            }
            if (Widgets.ButtonText(new Rect(inRect.xMax - 160f, y, 160f, 28f), "TraitTower_ResetAll".Translate()))
            {
                Settings.ResetAll();
            }
            y += 34f;

            if (entries == null)
            {
                BuildEntries();
            }
            string f = (filter ?? "").Trim().ToLowerInvariant();
            List<TraitEntry> shown = f.NullOrEmpty() ? entries : entries.Where(e => e.search.Contains(f)).ToList();

            const float rowH = 28f;
            Rect outRect = new Rect(inRect.x, y, inRect.width, inRect.yMax - y);
            Rect viewRect = new Rect(0f, 0f, outRect.width - 18f, shown.Count * rowH);
            Widgets.BeginScrollView(outRect, ref scroll, viewRect, true);
            float btnW = 80f;
            for (int i = 0; i < shown.Count; i++)
            {
                TraitEntry e = shown[i];
                float ry = i * rowH;
                if (i % 2 == 0)
                {
                    Widgets.DrawLightHighlight(new Rect(0f, ry, viewRect.width, rowH));
                }
                Widgets.Label(new Rect(4f, ry + 2f, viewRect.width - btnW * 3f - 12f, rowH), e.label);
                int cls = Settings.Classify(e.key);
                float bx = viewRect.width - btnW * 3f - 4f;
                if (DrawChoice(new Rect(bx, ry + 1f, btnW, rowH - 2f), "TraitTower_Good".Translate(), cls == 1))
                {
                    Settings.SetClass(e.key, 1);
                }
                if (DrawChoice(new Rect(bx + btnW, ry + 1f, btnW, rowH - 2f), "TraitTower_Neutral".Translate(), cls == 0))
                {
                    Settings.SetClass(e.key, 0);
                }
                if (DrawChoice(new Rect(bx + btnW * 2f, ry + 1f, btnW, rowH - 2f), "TraitTower_Bad".Translate(), cls == -1))
                {
                    Settings.SetClass(e.key, -1);
                }
            }
            Widgets.EndScrollView();
        }

        private static bool DrawChoice(Rect rect, string label, bool selected)
        {
            Color old = GUI.color;
            if (selected)
            {
                GUI.color = new Color(0.6f, 1f, 0.6f);
            }
            bool clicked = Widgets.ButtonText(rect, label);
            GUI.color = old;
            return clicked && !selected;
        }
    }

    public class TraitTowerSettings : ModSettings
    {
        // Chance that one pawn in range changes a trait, per in-game day, in percent.
        public float chancePerDayPercent = 1f;
        public float radius = 10f;
        public int maxTraits = 4;
        public bool moodThought = true;
        public bool showMessages = true;
        public bool includeSlaves = false;

        public List<string> goodKeys = new List<string>();
        public List<string> badKeys = new List<string>();
        private bool listsInitialised;

        private HashSet<string> goodSet;
        private HashSet<string> badSet;

        // Keys are "defName|degree". Names that do not exist in the loaded game are ignored.
        private static readonly string[] DefaultGood =
        {
            "Tough|0", "FastLearner|0", "Industriousness|1", "Industriousness|2", "Nimble|0",
            "Kind|0", "Beauty|1", "Beauty|2", "Immunity|1", "Immunity|2", "SpeedOffset|1", "SpeedOffset|2",
            "NaturalMood|2"
        };

        private static readonly string[] DefaultBad =
        {
            "Pyromaniac|0", "Wimp|0", "Industriousness|-1", "Industriousness|-2", "Abrasive|0",
            "Beauty|-1", "Beauty|-2", "Delicate|0", "SlowLearner|0", "AnnoyingVoice|0",
            "CreepyBreathing|0", "NaturalMood|-1", "NaturalMood|-2", "Greedy|0", "Jealous|0",
            "Immunity|-1", "SpeedOffset|-1"
        };

        public static string Key(TraitDef def, int degree)
        {
            return def.defName + "|" + degree;
        }

        public TraitTowerSettings()
        {
            ResetLists();
        }

        public void ResetLists()
        {
            goodKeys = new List<string>(DefaultGood);
            badKeys = new List<string>(DefaultBad);
            listsInitialised = true;
            Rebuild();
        }

        public void ResetAll()
        {
            chancePerDayPercent = 1f;
            radius = 10f;
            maxTraits = 4;
            moodThought = true;
            showMessages = true;
            includeSlaves = false;
            ResetLists();
        }

        private void Rebuild()
        {
            goodSet = new HashSet<string>(goodKeys);
            badSet = new HashSet<string>(badKeys);
        }

        public int Classify(string key)
        {
            if (goodSet == null)
            {
                Rebuild();
            }
            if (goodSet.Contains(key))
            {
                return 1;
            }
            return badSet.Contains(key) ? -1 : 0;
        }

        public int Classify(TraitDef def, int degree)
        {
            return Classify(Key(def, degree));
        }

        public void SetClass(string key, int cls)
        {
            goodKeys.Remove(key);
            badKeys.Remove(key);
            if (cls > 0)
            {
                goodKeys.Add(key);
            }
            else if (cls < 0)
            {
                badKeys.Add(key);
            }
            Rebuild();
        }

        public override void ExposeData()
        {
            base.ExposeData();
            Scribe_Values.Look(ref chancePerDayPercent, "chancePerDayPercent", 1f);
            Scribe_Values.Look(ref radius, "radius", 10f);
            Scribe_Values.Look(ref maxTraits, "maxTraits", 4);
            Scribe_Values.Look(ref moodThought, "moodThought", true);
            Scribe_Values.Look(ref showMessages, "showMessages", true);
            Scribe_Values.Look(ref includeSlaves, "includeSlaves", false);
            Scribe_Values.Look(ref listsInitialised, "listsInitialised", false);
            Scribe_Collections.Look(ref goodKeys, "goodKeys", LookMode.Value);
            Scribe_Collections.Look(ref badKeys, "badKeys", LookMode.Value);
            if (Scribe.mode == LoadSaveMode.PostLoadInit)
            {
                if (!listsInitialised || goodKeys == null || badKeys == null)
                {
                    ResetLists();
                }
                Rebuild();
            }
        }
    }
}
