using UnityEngine;
using Verse;

namespace MountainBreaker
{
    public class MountainBreakerSettings : ModSettings
    {
        public int radius = 5;
        public bool dropResources = true;
        public float yieldPercent = 0.5f;
        public bool clearAllRoofs = false;
        public int blastDamage = 0;
        public int cellsPerTick = 30;

        public override void ExposeData()
        {
            Scribe_Values.Look(ref radius, "radius", 5);
            Scribe_Values.Look(ref dropResources, "dropResources", true);
            Scribe_Values.Look(ref yieldPercent, "yieldPercent", 0.5f);
            Scribe_Values.Look(ref clearAllRoofs, "clearAllRoofs", false);
            Scribe_Values.Look(ref blastDamage, "blastDamage", 0);
            Scribe_Values.Look(ref cellsPerTick, "cellsPerTick", 30);
        }
    }

    public class MountainBreakerMod : Mod
    {
        public static MountainBreakerSettings Settings;

        public MountainBreakerMod(ModContentPack content) : base(content)
        {
            Settings = GetSettings<MountainBreakerSettings>();
            new HarmonyLib.Harmony(content.PackageIdPlayerFacing);
        }

        public override string SettingsCategory() => "MB_SettingsCategory".Translate();

        public override void DoSettingsWindowContents(Rect inRect)
        {
            var l = new Listing_Standard();
            l.Begin(inRect);
            Settings.radius = (int)l.SliderLabeled("MB_Radius".Translate(Settings.radius), Settings.radius, 1, 15, 0.6f, "MB_RadiusTip".Translate());
            l.CheckboxLabeled("MB_DropResources".Translate(), ref Settings.dropResources, "MB_DropResourcesTip".Translate());
            if (Settings.dropResources)
                Settings.yieldPercent = l.SliderLabeled("MB_YieldPercent".Translate(Settings.yieldPercent.ToStringPercent()), Settings.yieldPercent, 0f, 1f, 0.6f);
            l.CheckboxLabeled("MB_ClearAllRoofs".Translate(), ref Settings.clearAllRoofs, "MB_ClearAllRoofsTip".Translate());
            Settings.blastDamage = (int)l.SliderLabeled("MB_BlastDamage".Translate(Settings.blastDamage), Settings.blastDamage, 0, 100, 0.6f, "MB_BlastDamageTip".Translate());
            Settings.cellsPerTick = (int)l.SliderLabeled("MB_CellsPerTick".Translate(Settings.cellsPerTick), Settings.cellsPerTick, 5, 200, 0.6f, "MB_CellsPerTickTip".Translate());
            l.End();
        }
    }
}
