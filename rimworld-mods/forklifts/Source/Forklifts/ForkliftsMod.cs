using UnityEngine;
using Verse;

namespace Forklifts
{
    public class ForkliftsMod : Mod
    {
        public static ForkliftsSettings Settings;

        public ForkliftsMod(ModContentPack content) : base(content)
        {
            Settings = GetSettings<ForkliftsSettings>();
        }

        public override string SettingsCategory()
        {
            return "Forklifts_SettingsCategory".Translate();
        }

        public override void DoSettingsWindowContents(Rect inRect)
        {
            var l = new Listing_Standard();
            l.Begin(inRect);
            l.CheckboxLabeled("Forklifts_RequireForklift".Translate(), ref Settings.requireForklift,
                "Forklifts_RequireForkliftTip".Translate());
            Slider(l, ref Settings.stacksPerPallet, 2, 20, "Forklifts_StacksPerPallet", "Forklifts_StacksPerPalletTip");
            Slider(l, ref Settings.minStacksPerTrip, 1, 10, "Forklifts_MinStacks", "Forklifts_MinStacksTip");
            Slider(l, ref Settings.pickupRadius, 5, 60, "Forklifts_PickupRadius", "Forklifts_PickupRadiusTip");
            Slider(l, ref Settings.unloadRadius, 2, 20, "Forklifts_UnloadRadius", "Forklifts_UnloadRadiusTip");
            Slider(l, ref Settings.loadTicks, 0, 90, "Forklifts_LoadTicks", "Forklifts_LoadTicksTip");
            if (Settings.minStacksPerTrip > Settings.stacksPerPallet)
            {
                Settings.minStacksPerTrip = Settings.stacksPerPallet;
            }
            l.End();
        }

        private static void Slider(Listing_Standard l, ref int value, int min, int max, string labelKey, string tipKey)
        {
            string label = labelKey.Translate() + ": " + value;
            value = Mathf.RoundToInt(l.SliderLabeled(label, value, min, max, 0.6f, tipKey.Translate()));
        }
    }
}
