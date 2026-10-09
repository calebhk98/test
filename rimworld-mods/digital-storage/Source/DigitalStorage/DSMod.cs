using HarmonyLib;
using RimWorld;
using UnityEngine;
using Verse;

namespace DigitalStorage
{
    public class DSSettings : ModSettings
    {
        public float networkRange = 30f;
        public bool countInBills = true;
        public bool allowPerishables = true;
        public int spillStacks = 300;

        public override void ExposeData()
        {
            base.ExposeData();
            Scribe_Values.Look(ref networkRange, "networkRange", 30f);
            Scribe_Values.Look(ref countInBills, "countInBills", true);
            Scribe_Values.Look(ref allowPerishables, "allowPerishables", true);
            Scribe_Values.Look(ref spillStacks, "spillStacks", 300);
        }
    }

    public class DSMod : Mod
    {
        public static DSSettings Settings;

        public DSMod(ModContentPack content) : base(content)
        {
            Settings = GetSettings<DSSettings>();
            new Harmony(content.PackageIdPlayerFacing).PatchAll();
        }

        public override string SettingsCategory() => "DS_SettingsCategory".Translate();

        public override void DoSettingsWindowContents(Rect inRect)
        {
            var l = new Listing_Standard();
            l.Begin(inRect);
            l.Label("DS_SetRange".Translate(Settings.networkRange.ToString("F0")));
            Settings.networkRange = l.Slider(Settings.networkRange, 5f, 100f);
            l.CheckboxLabeled("DS_SetBills".Translate(), ref Settings.countInBills, "DS_SetBillsTip".Translate());
            l.CheckboxLabeled("DS_SetPerish".Translate(), ref Settings.allowPerishables, "DS_SetPerishTip".Translate());
            l.Label("DS_SetSpill".Translate(Settings.spillStacks));
            Settings.spillStacks = (int)l.Slider(Settings.spillStacks, 0f, 2000f);
            l.End();
        }
    }

    public class DriveExtension : DefModExtension
    {
        public int itemTypes = 10;
        public int totalItems = 1000;
    }

    public class CoreExtension : DefModExtension
    {
        public int driveSlots = 6;
        public float powerPerDrive = 50f;
    }

    [DefOf]
    public static class DSDefOf
    {
        public static JobDef DS_InsertDrive;

        static DSDefOf() => DefOfHelper.EnsureInitializedInCtor(typeof(DSDefOf));
    }
}
