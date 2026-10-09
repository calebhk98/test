using System.Collections.Generic;
using RimWorld;
using Unity.Collections;
using UnityEngine;
using Verse;

namespace AdaptiveRaiders
{
    /// <summary>Holds the death heat map, one sparse grid per hostile faction, on one map.</summary>
    public class DeathHeatMap : MapComponent
    {
        private const int DecayInterval = 2500;
        private const int TrailInterval = 45;
        private const int TrailLength = 12;
        private const int RetireDelay = 600;
        private const int RebuildThrottle = 250;
        private const float ForgetBelow = 0.05f;
        private const float TrailHeat = 0.4f;

        // faction loadID -> (cell index -> heat)
        private readonly Dictionary<int, Dictionary<int, float>> heat = new Dictionary<int, Dictionary<int, float>>();
        private readonly Dictionary<int, List<IntVec3>> trails = new Dictionary<int, List<IntVec3>>();
        private readonly Dictionary<int, HeatGrid> grids = new Dictionary<int, HeatGrid>();
        private readonly HashSet<int> dirty = new HashSet<int>();
        private readonly Dictionary<int, int> lastBuild = new Dictionary<int, int>();
        private readonly List<KeyValuePair<int, NativeArray<ushort>>> retired = new List<KeyValuePair<int, NativeArray<ushort>>>();
        private readonly List<int> tmpKeys = new List<int>();

        public DeathHeatMap(Map map) : base(map) { }

        public static DeathHeatMap For(Map map) => map?.GetComponent<DeathHeatMap>();

        // ---------- recording ----------

        public void RecordDeath(Pawn pawn)
        {
            Faction f = pawn.Faction;
            if (f == null) return;
            int fid = f.loadID;
            if (!heat.TryGetValue(fid, out var cells))
                heat[fid] = cells = new Dictionary<int, float>();

            IntVec3 pos = pawn.Position;
            int radius = Mathf.Max(1, AdaptiveRaidersMod.Settings.deathRadius);
            foreach (IntVec3 c in GenRadial.RadialCellsAround(pos, radius, true))
            {
                if (!c.InBounds(map)) continue;
                float w = 1f - pos.DistanceTo(c) / (radius + 1f);
                if (w > 0f) Add(cells, c, w);
            }

            // The path walked in, fading toward the start.
            if (trails.TryGetValue(pawn.thingIDNumber, out var trail))
            {
                for (int i = 0; i < trail.Count; i++)
                {
                    float w = TrailHeat * (i + 1) / trail.Count;
                    foreach (IntVec3 c in GenAdj.CellsAdjacent8Way(new TargetInfo(trail[i], map)))
                        if (c.InBounds(map)) Add(cells, c, w * 0.5f);
                    if (trail[i].InBounds(map)) Add(cells, trail[i], w);
                }
                trails.Remove(pawn.thingIDNumber);
            }
            dirty.Add(fid);
        }

        private void Add(Dictionary<int, float> cells, IntVec3 c, float amount)
        {
            int i = map.cellIndices.CellToIndex(c);
            cells.TryGetValue(i, out float cur);
            cells[i] = cur + amount;
        }

        // ---------- queries ----------

        /// <summary>Peak cell heat for a faction divided by the learning threshold. 1 or more means a known kill box.</summary>
        public float KillBoxScore(Faction f)
        {
            if (f == null || !heat.TryGetValue(f.loadID, out var cells) || cells.Count == 0) return 0f;
            float peak = 0f;
            foreach (float v in cells.Values) if (v > peak) peak = v;
            return peak / Mathf.Max(0.1f, AdaptiveRaidersMod.Settings.minDeathsToLearn);
        }

        public float HeatAt(Faction f, IntVec3 c)
        {
            if (f == null || !heat.TryGetValue(f.loadID, out var cells)) return 0f;
            return cells.TryGetValue(map.cellIndices.CellToIndex(c), out float v) ? v : 0f;
        }

        /// <summary>The path cost customizer for this faction, or null if it has learned nothing.</summary>
        public Verse.PathRequest.IPathGridCustomizer CustomizerFor(Faction f)
        {
            if (f == null || !heat.TryGetValue(f.loadID, out var cells) || cells.Count == 0) return null;
            int fid = f.loadID;
            int now = Find.TickManager.TicksGame;
            grids.TryGetValue(fid, out HeatGrid current);
            lastBuild.TryGetValue(fid, out int built);
            if (current == null || (dirty.Contains(fid) && now - built >= RebuildThrottle))
            {
                var s = AdaptiveRaidersMod.Settings;
                var arr = new NativeArray<ushort>(map.cellIndices.NumGridCells, Allocator.Persistent, NativeArrayOptions.ClearMemory);
                foreach (var kv in cells)
                {
                    if (kv.Value < 0.25f) continue;
                    arr[kv.Key] = (ushort)Mathf.Clamp(kv.Value * s.pathCostPerHeat, 0f, Mathf.Min(s.pathMaxCost, ushort.MaxValue));
                }
                if (current != null) retired.Add(new KeyValuePair<int, NativeArray<ushort>>(now, current.Array));
                current = new HeatGrid(arr);
                grids[fid] = current;
                lastBuild[fid] = now;
                dirty.Remove(fid);
            }
            return current;
        }

        // ---------- ticking ----------

        public override void MapComponentTick()
        {
            int t = Find.TickManager.TicksGame;
            if (t % TrailInterval == 0) SampleTrails();
            if (t % DecayInterval == 0) Decay();
            if (retired.Count > 0 && t % 120 == 0) DisposeRetired(false, t);
        }

        private void SampleTrails()
        {
            var s = AdaptiveRaidersMod.Settings;
            var pawns = map.mapPawns.AllPawnsSpawned;
            var seen = new HashSet<int>();
            for (int i = 0; i < pawns.Count; i++)
            {
                Pawn p = pawns[i];
                if (!Patches.IsLearnable(p)) continue;
                seen.Add(p.thingIDNumber);
                if (!trails.TryGetValue(p.thingIDNumber, out var trail))
                    trails[p.thingIDNumber] = trail = new List<IntVec3>(TrailLength);
                if (trail.Count == 0 || trail[trail.Count - 1] != p.Position)
                {
                    if (trail.Count >= TrailLength) trail.RemoveAt(0);
                    trail.Add(p.Position);
                }
            }
            if (trails.Count > seen.Count)
            {
                tmpKeys.Clear();
                foreach (int k in trails.Keys) if (!seen.Contains(k)) tmpKeys.Add(k);
                foreach (int k in tmpKeys) trails.Remove(k);
            }
        }

        private void Decay()
        {
            float halfLifeTicks = Mathf.Max(1f, AdaptiveRaidersMod.Settings.halfLifeDays * GenDate.TicksPerDay);
            float factor = Mathf.Pow(0.5f, DecayInterval / halfLifeTicks);
            foreach (var fc in heat)
            {
                var cells = fc.Value;
                tmpKeys.Clear();
                foreach (var key in cells.Keys) tmpKeys.Add(key);
                foreach (int key in tmpKeys)
                {
                    float v = cells[key] * factor;
                    if (v < ForgetBelow) cells.Remove(key); else cells[key] = v;
                }
                dirty.Add(fc.Key);
            }
        }

        private void DisposeRetired(bool all, int now)
        {
            for (int i = retired.Count - 1; i >= 0; i--)
            {
                if (all || now - retired[i].Key >= RetireDelay)
                {
                    if (retired[i].Value.IsCreated) retired[i].Value.Dispose();
                    retired.RemoveAt(i);
                }
            }
        }

        public override void MapRemoved()
        {
            foreach (var g in grids.Values) if (g.Array.IsCreated) g.Array.Dispose();
            grids.Clear();
            DisposeRetired(true, 0);
        }

        // ---------- saving ----------

        public override void ExposeData()
        {
            // Flatten (faction, cell) into one long key: faction in the high 32 bits.
            Dictionary<long, float> flat = null;
            if (Scribe.mode == LoadSaveMode.Saving)
            {
                flat = new Dictionary<long, float>();
                foreach (var fc in heat)
                    foreach (var cv in fc.Value)
                        flat[((long)fc.Key << 32) | (uint)cv.Key] = cv.Value;
            }
            Scribe_Collections.Look(ref flat, "heat", LookMode.Value, LookMode.Value);
            if (Scribe.mode == LoadSaveMode.LoadingVars && flat != null)
            {
                heat.Clear();
                foreach (var kv in flat)
                {
                    int fid = (int)(kv.Key >> 32);
                    int cell = (int)(kv.Key & 0xFFFFFFFF);
                    if (!heat.TryGetValue(fid, out var cells)) heat[fid] = cells = new Dictionary<int, float>();
                    cells[cell] = kv.Value;
                }
            }
        }
    }

    /// <summary>
    /// Wraps a NativeArray handed to the pathfinder as a per-cell cost offset. Dispose is a no-op on purpose:
    /// the grid is shared by many requests and is owned (and freed after a delay) by DeathHeatMap.
    /// </summary>
    public class HeatGrid : Verse.PathRequest.IPathGridCustomizer
    {
        public readonly NativeArray<ushort> Array;
        public HeatGrid(NativeArray<ushort> array) { Array = array; }
        public NativeArray<ushort> GetOffsetGrid() => Array;
        public void Dispose() { }
    }
}
