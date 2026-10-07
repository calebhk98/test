using HarmonyLib;
using UnityEngine;
using Verse;

namespace RemoteSurrogate
{
    public class RSSettings : ModSettings
    {
        public float skillFraction = 0.6f;
        public float xpShare = 0.5f;
        public float cooldownDays = 1f;
        public int powerGraceTicks = 1500;
        public int stunTicks = 180;

        public override void ExposeData()
        {
            Scribe_Values.Look(ref skillFraction, "skillFraction", 0.6f);
            Scribe_Values.Look(ref xpShare, "xpShare", 0.5f);
            Scribe_Values.Look(ref cooldownDays, "cooldownDays", 1f);
            Scribe_Values.Look(ref powerGraceTicks, "powerGraceTicks", 1500);
            Scribe_Values.Look(ref stunTicks, "stunTicks", 180);
        }
    }

    public class RemoteSurrogateMod : Mod
    {
        public static RSSettings Settings;

        public RemoteSurrogateMod(ModContentPack content) : base(content)
        {
            Settings = GetSettings<RSSettings>();
            new Harmony(content.PackageIdPlayerFacing).PatchAll();
        }

        public override string SettingsCategory() => "RS_SettingsCategory".Translate();

        public override void DoSettingsWindowContents(Rect inRect)
        {
            var l = new Listing_Standard();
            l.Begin(inRect);
            l.Label("RS_SetSkillFraction".Translate(Settings.skillFraction.ToStringPercent()));
            Settings.skillFraction = l.Slider(Settings.skillFraction, 0.1f, 1f);
            l.Label("RS_SetXpShare".Translate(Settings.xpShare.ToStringPercent()));
            Settings.xpShare = l.Slider(Settings.xpShare, 0f, 1f);
            l.Label("RS_SetCooldown".Translate(Settings.cooldownDays.ToString("0.0")));
            Settings.cooldownDays = l.Slider(Settings.cooldownDays, 0f, 5f);
            l.Label("RS_SetGrace".Translate(Settings.powerGraceTicks, (Settings.powerGraceTicks / 2500f).ToString("0.0")));
            Settings.powerGraceTicks = (int)l.Slider(Settings.powerGraceTicks, 0f, 15000f);
            l.Label("RS_SetStun".Translate(Settings.stunTicks, (Settings.stunTicks / 60f).ToString("0.0")));
            Settings.stunTicks = (int)l.Slider(Settings.stunTicks, 0f, 900f);
            l.End();
        }
    }
}
