using System.Collections.Generic;
using RimWorld;
using UnityEngine;
using Verse;
using Verse.AI.Group;

namespace EndlessSiege
{
    public class MapComponent_EndlessSiege : MapComponent
    {
        private const int HourTicks = 2500;

        private bool active;
        private bool finished;
        private int startTick;
        private int nextWaveTick;
        private int wavesSent;
        private Faction siegeFaction;

        public MapComponent_EndlessSiege(Map map) : base(map) { }

        public override void ExposeData()
        {
            Scribe_Values.Look(ref active, "active");
            Scribe_Values.Look(ref finished, "finished");
            Scribe_Values.Look(ref startTick, "startTick");
            Scribe_Values.Look(ref nextWaveTick, "nextWaveTick");
            Scribe_Values.Look(ref wavesSent, "wavesSent");
            Scribe_References.Look(ref siegeFaction, "siegeFaction");
        }

        public override void MapComponentTick()
        {
            if (!map.IsPlayerHome || finished) return;
            var s = EndlessSiegeMod.Settings;
            if (s == null || !s.enabled) return;
            int now = Find.TickManager.TicksGame;

            if (!active)
            {
                if (now % 250 == 0) TryDetectFirstRaid(now);
                return;
            }

            if (now % HourTicks == 0 && s.cleanupCorpses) CleanupCorpses(s, now);

            if (s.surviveDays > 0 && now - startTick >= s.surviveDays * GenDate.TicksPerDay)
            {
                finished = true;
                Find.LetterStack.ReceiveLetter("ES_SurvivedLabel".Translate(), "ES_SurvivedText".Translate(s.surviveDays), LetterDefOf.PositiveEvent);
                return;
            }

            if (now < nextWaveTick) return;
            nextWaveTick = now + Mathf.Max(250, Mathf.RoundToInt(s.hoursBetweenWaves * HourTicks));
            if (CountLiveEnemies() >= s.liveEnemyCap) return;
            if (SendWave(s, now))
            {
                wavesSent++;
                if (s.quietEveryWaves > 0 && wavesSent % s.quietEveryWaves == 0)
                    nextWaveTick += Mathf.RoundToInt(s.quietHours * HourTicks);
            }
        }

        private void TryDetectFirstRaid(int now)
        {
            var lords = map.lordManager.lords;
            for (int i = 0; i < lords.Count; i++)
            {
                var lord = lords[i];
                if (lord.LordJob is LordJob_AssaultColony && lord.faction != null && lord.faction.HostileTo(Faction.OfPlayer) && lord.ownedPawns.Count > 0)
                {
                    active = true;
                    startTick = now;
                    siegeFaction = lord.faction;
                    nextWaveTick = now + Mathf.RoundToInt(EndlessSiegeMod.Settings.hoursBetweenWaves * HourTicks);
                    Find.LetterStack.ReceiveLetter("ES_BeginLabel".Translate(), "ES_BeginText".Translate(), LetterDefOf.ThreatBig);
                    return;
                }
            }
        }

        private int CountLiveEnemies()
        {
            int n = 0;
            var pawns = map.mapPawns.AllPawnsSpawned;
            for (int i = 0; i < pawns.Count; i++)
            {
                var p = pawns[i];
                if (p.Faction != null && p.Faction.HostileTo(Faction.OfPlayer) && p.HostFaction == null && !p.Dead)
                    n++;
            }
            return n;
        }

        private Faction PickFaction(float points, bool mix)
        {
            if (!mix && siegeFaction != null && !siegeFaction.defeated && PawnGroupMakerUtility.CanGenerateAnyNormalGroup(siegeFaction, points))
                return siegeFaction;
            Faction f;
            if (PawnGroupMakerUtility.TryGetRandomFactionForCombatPawnGroup(points, out f, x => x.HostileTo(Faction.OfPlayer), false, false, false, false))
                return f;
            return null;
        }

        private bool SendWave(EndlessSiegeSettings s, int now)
        {
            float days = (now - startTick) / (float)GenDate.TicksPerDay;
            float mult = Mathf.Min(s.maxPointsMultiplier, 1f + s.growthPerDay * days);
            float points = StorytellerUtility.DefaultThreatPointsNow(map) * s.pointsFraction * mult;
            points = Mathf.Max(points, 60f);

            Faction faction = PickFaction(points, s.mixFactions);
            if (faction == null) return false;

            var gp = new PawnGroupMakerParms
            {
                groupKind = PawnGroupKindDefOf.Combat,
                tile = map.Tile,
                faction = faction,
                points = points,
                generateFightersOnly = true,
                raidStrategy = RaidStrategyDefOf.ImmediateAttack,
                forceOneDowned = false
            };
            var pawns = new List<Pawn>(PawnGroupMakerUtility.GeneratePawns(gp));
            if (pawns.Count == 0) return false;

            IntVec3 edge;
            if (!CellFinder.TryFindRandomEdgeCellWith(c => c.Standable(map) && !c.Fogged(map) && map.reachability.CanReachColony(c), map, CellFinder.EdgeRoadChance_Hostile, out edge))
            {
                for (int i = 0; i < pawns.Count; i++) Find.WorldPawns.PassToWorld(pawns[i], RimWorld.Planet.PawnDiscardDecideMode.Discard);
                return false;
            }

            for (int i = 0; i < pawns.Count; i++)
            {
                IntVec3 spot = CellFinder.RandomClosewalkCellNear(edge, map, 6, c => c.Standable(map));
                GenSpawn.Spawn(pawns[i], spot, map, Rot4.Random);
            }

            Lord lord = FindSiegeLord(faction);
            if (lord != null)
                lord.AddPawns(pawns, true);
            else
                LordMaker.MakeNewLord(faction, new LordJob_AssaultColony(faction, false, false, false, false, false), map, pawns);
            return true;
        }

        private Lord FindSiegeLord(Faction faction)
        {
            var lords = map.lordManager.lords;
            for (int i = 0; i < lords.Count; i++)
                if (lords[i].faction == faction && lords[i].LordJob is LordJob_AssaultColony && lords[i].ownedPawns.Count > 0)
                    return lords[i];
            return null;
        }

        private void CleanupCorpses(EndlessSiegeSettings s, int now)
        {
            int lifetime = Mathf.RoundToInt(s.corpseLifetimeHours * HourTicks);
            var corpses = map.listerThings.ThingsInGroup(ThingRequestGroup.Corpse);
            for (int i = corpses.Count - 1; i >= 0; i--)
            {
                var c = corpses[i] as Corpse;
                if (c == null || c.Destroyed || c.InnerPawn == null) continue;
                var f = c.InnerPawn.Faction;
                if (f == null || !f.HostileTo(Faction.OfPlayer)) continue;
                if (now - c.timeOfDeath < lifetime) continue;
                c.Destroy(DestroyMode.Vanish);
            }
        }
    }
}
