using RimWorld;
using UnityEngine;
using Verse;

namespace UndergroundBarn
{
    /// <summary>Tunable numbers. Everything a player would reasonably want to change lives here.</summary>
    public class UndergroundBarnSettings : ModSettings
    {
        // Herd simulation runs once per this many ticks (rounded to a multiple of 250, the rare tick).
        public int simIntervalTicks = 2500;
        // Maximum number of animals one barn holds.
        public int capacity = 250;
        // When true the barn only breeds and produces while powered. Animals always eat.
        public bool requirePower = true;
        public bool ageing = true;
        public bool breeding = true;
        public bool products = true;
        // How many fertile females one fertile male can cover.
        public int femalesPerMale = 4;
        // Days a mother rests after a birth, added to the species' gestation period.
        public float restDays = 5f;
        // Fraction of normal butchering yield when the barn culls.
        public float cullEfficiency = 0.7f;
        // Food is taken from items lying within this many cells of the barn.
        public int feedRadius = 5;
        // Bonded animals are blocked by default so you do not lose track of them.
        public bool allowBonded = false;
        // 1 = vanilla malnutrition speed.
        public float starvationMultiplier = 1f;

        public override void ExposeData()
        {
            Scribe_Values.Look(ref simIntervalTicks, "simIntervalTicks", 2500);
            Scribe_Values.Look(ref capacity, "capacity", 250);
            Scribe_Values.Look(ref requirePower, "requirePower", true);
            Scribe_Values.Look(ref ageing, "ageing", true);
            Scribe_Values.Look(ref breeding, "breeding", true);
            Scribe_Values.Look(ref products, "products", true);
            Scribe_Values.Look(ref femalesPerMale, "femalesPerMale", 4);
            Scribe_Values.Look(ref restDays, "restDays", 5f);
            Scribe_Values.Look(ref cullEfficiency, "cullEfficiency", 0.7f);
            Scribe_Values.Look(ref feedRadius, "feedRadius", 5);
            Scribe_Values.Look(ref allowBonded, "allowBonded", false);
            Scribe_Values.Look(ref starvationMultiplier, "starvationMultiplier", 1f);
            base.ExposeData();
        }
    }

    public class UndergroundBarnMod : Mod
    {
        public static UndergroundBarnSettings Settings;
        private Vector2 scroll;

        // No Harmony patches are needed: the barn is a plain Building plus a job and a work giver.
        public UndergroundBarnMod(ModContentPack content) : base(content)
        {
            Settings = GetSettings<UndergroundBarnSettings>();
        }

        public override string SettingsCategory() => "UB_SettingsTitle".Translate();

        public override void DoSettingsWindowContents(Rect inRect)
        {
            var view = new Rect(0f, 0f, inRect.width - 20f, 640f);
            Widgets.BeginScrollView(inRect, ref scroll, view);
            var l = new Listing_Standard();
            l.Begin(view);

            l.Label("UB_SetInterval".Translate(Settings.simIntervalTicks, (Settings.simIntervalTicks / 2500f).ToString("0.0")));
            Settings.simIntervalTicks = Mathf.Clamp(Mathf.RoundToInt(l.Slider(Settings.simIntervalTicks, 250f, 15000f) / 250f) * 250, 250, 15000);

            l.Label("UB_SetCapacity".Translate(Settings.capacity));
            Settings.capacity = Mathf.RoundToInt(l.Slider(Settings.capacity, 10f, 1000f));

            l.CheckboxLabeled("UB_SetRequirePower".Translate(), ref Settings.requirePower, "UB_SetRequirePowerTip".Translate());
            l.CheckboxLabeled("UB_SetAgeing".Translate(), ref Settings.ageing);
            l.CheckboxLabeled("UB_SetBreeding".Translate(), ref Settings.breeding);
            l.CheckboxLabeled("UB_SetProducts".Translate(), ref Settings.products);
            l.CheckboxLabeled("UB_SetAllowBonded".Translate(), ref Settings.allowBonded, "UB_SetAllowBondedTip".Translate());

            l.Label("UB_SetFemalesPerMale".Translate(Settings.femalesPerMale));
            Settings.femalesPerMale = Mathf.RoundToInt(l.Slider(Settings.femalesPerMale, 1f, 12f));

            l.Label("UB_SetRestDays".Translate(Settings.restDays.ToString("0.0")));
            Settings.restDays = Mathf.Round(l.Slider(Settings.restDays, 0f, 30f) * 2f) / 2f;

            l.Label("UB_SetCullEfficiency".Translate((Settings.cullEfficiency * 100f).ToString("0")));
            Settings.cullEfficiency = Mathf.Round(l.Slider(Settings.cullEfficiency, 0.1f, 1f) * 20f) / 20f;

            l.Label("UB_SetFeedRadius".Translate(Settings.feedRadius));
            Settings.feedRadius = Mathf.RoundToInt(l.Slider(Settings.feedRadius, 1f, 10f));

            l.Label("UB_SetStarvation".Translate(Settings.starvationMultiplier.ToString("0.00")));
            Settings.starvationMultiplier = Mathf.Round(l.Slider(Settings.starvationMultiplier, 0f, 3f) * 20f) / 20f;

            if (l.ButtonText("UB_SetReset".Translate()))
            {
                var d = new UndergroundBarnSettings();
                Settings.simIntervalTicks = d.simIntervalTicks; Settings.capacity = d.capacity;
                Settings.requirePower = d.requirePower; Settings.ageing = d.ageing;
                Settings.breeding = d.breeding; Settings.products = d.products;
                Settings.femalesPerMale = d.femalesPerMale; Settings.restDays = d.restDays;
                Settings.cullEfficiency = d.cullEfficiency; Settings.feedRadius = d.feedRadius;
                Settings.allowBonded = d.allowBonded; Settings.starvationMultiplier = d.starvationMultiplier;
            }

            l.End();
            Widgets.EndScrollView();
        }
    }

    [DefOf]
    public static class UBDefOf
    {
        public static DesignationDef UB_StoreAnimal;
        public static JobDef UB_StoreAnimalJob;
        public static ThingDef UB_UndergroundBarn;

        static UBDefOf() { DefOfHelper.EnsureInitializedInCtor(typeof(UBDefOf)); }
    }

    [StaticConstructorOnStartup]
    public static class UBTex
    {
        public static readonly Texture2D Store = ContentFinder<Texture2D>.Get("UI/UndergroundBarn/Store", false) ?? BaseContent.BadTex;
        public static readonly Texture2D StoreKind = ContentFinder<Texture2D>.Get("UI/UndergroundBarn/StoreKind", false) ?? BaseContent.BadTex;
        public static readonly Texture2D Cancel = ContentFinder<Texture2D>.Get("UI/UndergroundBarn/Cancel", false) ?? BaseContent.BadTex;
        public static readonly Texture2D Release = ContentFinder<Texture2D>.Get("UI/UndergroundBarn/Release", false) ?? BaseContent.BadTex;
        public static readonly Texture2D Cull = ContentFinder<Texture2D>.Get("UI/UndergroundBarn/Cull", false) ?? BaseContent.BadTex;
    }
}
