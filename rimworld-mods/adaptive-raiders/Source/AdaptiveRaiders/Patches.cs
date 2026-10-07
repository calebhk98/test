using System.Collections.Generic;
using System.Linq;
using HarmonyLib;
using RimWorld;
using Verse;

namespace AdaptiveRaiders
{
    public static class Patches
    {
        // Vanilla strategies that do not walk into the front door of a kill box. defNames are unverified.
        public static readonly string[] AvoidStrategyDefNames =
            { "ImmediateAttackSappers", "ImmediateAttackBreaching", "Siege" };

        private static IncidentParms lastHandled;

        public static bool IsLearnableFaction(Faction f)
        {
            if (f == null || f.IsPlayer || f.Hidden) return false;
            if (!f.HostileTo(Faction.OfPlayer)) return false;
            if (f == Faction.OfMechanoids && !AdaptiveRaidersMod.Settings.includeMechanoids) return false;
            if (f == Faction.OfInsects) return false;
            return true;
        }

        /// <summary>Hostile, non-player pawns we learn from and path for.</summary>
        public static bool IsLearnable(Pawn p) => p != null && IsLearnableFaction(p.Faction);

        public static bool IsAvoidStrategy(RaidStrategyDef d) => d != null && AvoidStrategyDefNames.Contains(d.defName);

        // ---------- recording deaths ----------

        [HarmonyPatch(typeof(Pawn), nameof(Pawn.Kill))]
        public static class Pawn_Kill_Patch
        {
            public static void Prefix(Pawn __instance, DamageInfo? dinfo)
            {
                try
                {
                    Pawn p = __instance;
                    if (!p.Spawned || p.Map == null || !p.Map.IsPlayerHome || !IsLearnable(p)) return;
                    Thing instigator = dinfo?.Instigator;
                    if (instigator != null && instigator.Faction != Faction.OfPlayer) return;
                    DeathHeatMap.For(p.Map)?.RecordDeath(p);
                }
                catch (System.Exception e) { Log.ErrorOnce("[Adaptive Raiders] death record failed: " + e, 7731001); }
            }
        }

        // ---------- level 1: strategy choice ----------

        public static void StrategyPrefix(IncidentParms parms, out bool __state)
        {
            __state = parms.raidStrategy != null;
        }

        public static void StrategyPostfix(IncidentParms parms, PawnGroupKindDef groupKind, bool __state)
        {
            try
            {
                var s = AdaptiveRaidersMod.Settings;
                if (!s.enableStrategy || __state || ReferenceEquals(lastHandled, parms)) return;
                lastHandled = parms;
                if (!(parms.target is Map map) || parms.faction == null || parms.raidStrategy == null) return;
                if (!IsLearnableFaction(parms.faction)) return;
                if (IsAvoidStrategy(parms.raidStrategy)) return;
                var comp = DeathHeatMap.For(map);
                if (comp == null) return;
                float score = comp.KillBoxScore(parms.faction);
                if (score < 1f) return;
                float chance = UnityEngine.Mathf.Lerp(s.avoidChanceMin, s.avoidChanceMax, UnityEngine.Mathf.Clamp01((score - 1f) / 2f));
                if (!Rand.Chance(chance)) return;

                var options = new List<RaidStrategyDef>();
                foreach (string name in AvoidStrategyDefNames)
                {
                    var d = DefDatabase<RaidStrategyDef>.GetNamedSilentFail(name);
                    if (d == null) continue;
                    if (parms.points < d.Worker.MinimumPoints(parms.faction, groupKind)) continue;
                    if (!d.Worker.CanUseWith(parms, groupKind)) continue;
                    options.Add(d);
                }
                if (options.Count == 0) return;
                RaidStrategyDef pick = options.RandomElement();
                if (Prefs.DevMode)
                    Log.Message("[Adaptive Raiders] " + parms.faction.Name + " learned (score " + score.ToString("F1") + "): " + parms.raidStrategy.defName + " -> " + pick.defName);
                parms.raidStrategy = pick;
            }
            catch (System.Exception e) { Log.ErrorOnce("[Adaptive Raiders] strategy patch failed: " + e, 7731002); }
        }

        [HarmonyPatch(typeof(IncidentWorker_Raid), nameof(IncidentWorker_Raid.ResolveRaidStrategy))]
        public static class Raid_Strategy_Base
        {
            public static void Prefix(IncidentParms parms, out bool __state) => StrategyPrefix(parms, out __state);
            public static void Postfix(IncidentParms parms, PawnGroupKindDef groupKind, bool __state) => StrategyPostfix(parms, groupKind, __state);
        }

        [HarmonyPatch(typeof(IncidentWorker_RaidEnemy), nameof(IncidentWorker_RaidEnemy.ResolveRaidStrategy))]
        public static class Raid_Strategy_Enemy
        {
            public static void Prefix(IncidentParms parms, out bool __state) => StrategyPrefix(parms, out __state);
            public static void Postfix(IncidentParms parms, PawnGroupKindDef groupKind, bool __state) => StrategyPostfix(parms, groupKind, __state);
        }

        // Drop pods behind the line: sometimes swap a walk-in arrival for a drop arrival.
        [HarmonyPatch(typeof(IncidentWorker_Raid), nameof(IncidentWorker_Raid.ResolveRaidArriveMode))]
        public static class Raid_Arrival
        {
            public static void Postfix(IncidentParms parms)
            {
                try
                {
                    var s = AdaptiveRaidersMod.Settings;
                    if (!s.enableStrategy || s.dropChance <= 0f) return;
                    if (!(parms.target is Map map) || parms.faction == null || parms.raidStrategy == null) return;
                    if (parms.raidArrivalMode == null || !parms.raidArrivalMode.walkIn) return;
                    if (parms.raidArrivalModeForQuickMilitaryAid || parms.faction.IsPlayer) return;
                    if (!parms.faction.HostileTo(Faction.OfPlayer)) return;
                    var comp = DeathHeatMap.For(map);
                    if (comp == null || comp.KillBoxScore(parms.faction) < 1f) return;
                    if (!Rand.Chance(s.dropChance)) return;
                    var modes = parms.raidStrategy.arriveModes;
                    if (modes == null) return;
                    var options = modes.Where(m => m != null && !m.walkIn && !m.forQuickMilitaryAid
                        && m.Worker.CanUseOnMap(map) && m.Worker.CanUseWith(parms)).ToList();
                    if (options.Count == 0) return;
                    PawnsArrivalModeDef pick = options.RandomElement();
                    parms.raidArrivalMode = pick;
                    pick.Worker.TryResolveRaidSpawnCenter(parms);
                }
                catch (System.Exception e) { Log.ErrorOnce("[Adaptive Raiders] arrival patch failed: " + e, 7731003); }
            }
        }

        // ---------- level 2: pathing ----------

        public static void InjectCustomizer(Pawn pawn, ref PathRequest.IPathGridCustomizer customizer)
        {
            try
            {
                if (customizer != null || !AdaptiveRaidersMod.Settings.enablePathing) return;
                if (pawn == null || !pawn.Spawned || !IsLearnable(pawn)) return;
                customizer = DeathHeatMap.For(pawn.Map)?.CustomizerFor(pawn.Faction);
            }
            catch (System.Exception e) { Log.ErrorOnce("[Adaptive Raiders] path patch failed: " + e, 7731004); }
        }

        [HarmonyPatch(typeof(PathFinder), nameof(PathFinder.CreateRequest),
            new[] { typeof(IntVec3), typeof(LocalTargetInfo), typeof(IntVec3?), typeof(Pawn),
                    typeof(PathFinderCostTuning?), typeof(Verse.AI.PathEndMode), typeof(PathRequest.IPathGridCustomizer) })]
        public static class CreateRequest_Pawn
        {
            public static void Prefix(Pawn pawn, ref PathRequest.IPathGridCustomizer customizer) => InjectCustomizer(pawn, ref customizer);
        }

        [HarmonyPatch(typeof(PathFinder), nameof(PathFinder.CreateRequest),
            new[] { typeof(IntVec3), typeof(LocalTargetInfo), typeof(IntVec3?), typeof(TraverseParms),
                    typeof(PathFinderCostTuning?), typeof(Verse.AI.PathEndMode), typeof(Pawn), typeof(PathRequest.IPathGridCustomizer) })]
        public static class CreateRequest_Traverse
        {
            public static void Prefix(Pawn pawn, ref PathRequest.IPathGridCustomizer customizer) => InjectCustomizer(pawn, ref customizer);
        }
    }
}
