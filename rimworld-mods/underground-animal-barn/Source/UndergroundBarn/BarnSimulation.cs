using System;
using System.Collections.Generic;
using System.Linq;
using RimWorld;
using UnityEngine;
using Verse;
using RimWorld.Planet;

namespace UndergroundBarn
{
    /// <summary>
    /// The abstract herd simulation. One pass over the herd every Settings.simIntervalTicks
    /// (default 2500 = one in-game hour). Order: ageing, food, products, births, culling, output.
    /// </summary>
    public partial class Building_UndergroundBarn
    {
        private const float TicksPerDay = 60000f;
        // Animals are topped up to this fraction of their food bar when food is plentiful.
        private const float BellyTarget = 0.5f;
        private const float MalnutritionRecoveryPerDay = 0.6f;
        // Own constant: the game's rate is private. About 2.5 days fully unfed to reach lethal severity 1.
        private const float MalnutritionSeverityPerDay = 0.4f;
        private const int MaxStacksPerFlush = 400;

        private readonly List<Pawn> scratch = new List<Pawn>();
        private readonly HashSet<ThingDef> touchedOutputs = new HashSet<ThingDef>();
        private readonly Dictionary<ThingDef, float> fedByRace = new Dictionary<ThingDef, float>();
        private bool warnedAgeing;
        private string lastReport;

        public string LastReport => lastReport;

        public void RunSimulation(int elapsed)
        {
            Map map = Map;
            if (map == null || innerContainer.Count == 0) return;

            float days = elapsed / TicksPerDay;
            bool working = WorkingNow;
            int born = 0, culled = 0, starved = 0;

            touchedOutputs.Clear();
            fedByRace.Clear();

            // 1. Ageing. Pawn.TickMothballed is the game's own entry point for advancing a pawn that is
            // not on a map (it is what world pawns use), so no per-tick pawn code runs.
            if (Settings.ageing) AgeHerd(elapsed);
            RefreshScratch();

            // 2. Food, for every race, always (power does not feed animals).
            var starvedPawns = new List<Pawn>();
            lastFedFraction = FeedHerd(elapsed, starvedPawns);
            foreach (Pawn p in starvedPawns)
            {
                RemoveStored(p, true);
                starved++;
            }
            if (starvedPawns.Count > 0) RefreshScratch();

            // 3. Products and 4. births need the barn to be running.
            if (working)
            {
                if (Settings.products) ProduceGoods(days);
                if (Settings.breeding) born = BreedHerd(days);
            }

            // 5. Culling keeps the herd at the player's chosen size per kind.
            culled = CullHerd();

            // 6. One batch of output items, not one spawn per animal.
            FlushOutputs(map);

            kindCountsTotal = -1;
            lastReport = "UB_LastReport".Translate(born, culled, starved);
            if (starved > 0)
                Messages.Message("UB_StarvedMessage".Translate(starved), this, MessageTypeDefOf.NegativeEvent, false);
        }

        private void RefreshScratch()
        {
            scratch.Clear();
            foreach (Pawn p in innerContainer.InnerListForReading)
            {
                if (p != null && !p.Dead && !p.Destroyed) scratch.Add(p);
            }
        }

        // ---------------------------------------------------------------- ageing

        private void AgeHerd(int elapsed)
        {
            RefreshScratch();
            foreach (Pawn p in scratch.ToList())
            {
                Need_Food food = p.needs?.food;
                float level = food != null ? food.CurLevel : 0f;
                try
                {
                    p.TickMothballed(elapsed);
                }
                catch (Exception e)
                {
                    if (!warnedAgeing)
                    {
                        warnedAgeing = true;
                        Log.Warning("[Underground Animal Barn] Ageing a stored animal threw, further errors are silent: " + e);
                    }
                }
                // The barn owns the food bar; undo any hunger the call may have applied.
                if (food != null) food.CurLevel = level;
                // Dying in storage is handled by the game (Pawn.Kill takes the pawn out of its holder).
            }
        }

        // ---------------------------------------------------------------- food

        /// <summary>Returns the overall fraction of the herd's food need that was met (0..1).</summary>
        private float FeedHerd(int elapsed, List<Pawn> starvedOut)
        {
            float totalWanted = 0f, totalGot = 0f;
            float recovery = elapsed / TicksPerDay * MalnutritionRecoveryPerDay;

            foreach (var group in scratch.GroupBy(p => p.def))
            {
                ThingDef race = group.Key;
                var pawns = group.Where(p => p.needs?.food != null).ToList();
                var fall = new float[pawns.Count];
                var refill = new float[pawns.Count];
                float wanted = 0f;
                for (int i = 0; i < pawns.Count; i++)
                {
                    Need_Food f = pawns[i].needs.food;
                    fall[i] = f.FoodFallPerTickAssumingCategory(HungerCategory.Fed, true) * elapsed;
                    refill[i] = Mathf.Max(0f, f.MaxLevel * BellyTarget - f.CurLevel);
                    wanted += fall[i] + refill[i];
                }
                float got = wanted > 0.0001f ? ConsumeFood(race, wanted) : 0f;
                float fed = wanted > 0.0001f ? Mathf.Clamp01(got / wanted) : 1f;
                fedByRace[race] = fed;
                totalWanted += wanted;
                totalGot += got;

                for (int i = 0; i < pawns.Count; i++)
                {
                    Pawn p = pawns[i];
                    Need_Food f = p.needs.food;
                    f.CurLevel = Mathf.Clamp(f.CurLevel + fed * refill[i] - (1f - fed) * fall[i], 0f, f.MaxLevel);

                    if (fed >= 0.999f)
                    {
                        if (recovery > 0f && p.health.hediffSet.HasHediff(HediffDefOf.Malnutrition))
                            HealthUtility.AdjustSeverity(p, HediffDefOf.Malnutrition, -recovery);
                    }
                    else if (f.CurLevel <= 0.001f)
                    {
                        float delta = MalnutritionSeverityPerDay * elapsed / TicksPerDay * (1f - fed) * Settings.starvationMultiplier;
                        if (delta > 0f)
                        {
                            HealthUtility.AdjustSeverity(p, HediffDefOf.Malnutrition, delta);
                            Hediff h = p.health.hediffSet.GetFirstHediffOfDef(HediffDefOf.Malnutrition);
                            if (h != null && h.def.lethalSeverity > 0f && h.Severity >= h.def.lethalSeverity)
                                starvedOut.Add(p);
                        }
                    }
                }
            }
            return totalWanted > 0.0001f ? Mathf.Clamp01(totalGot / totalWanted) : 1f;
        }

        /// <summary>
        /// Takes up to <paramref name="needed"/> nutrition for one race from food lying within the feed
        /// radius of the barn (a hopper or a stockpile next to it). Leftover nutrition from a partly
        /// used stack is kept as credit so nothing is wasted.
        /// </summary>
        private float ConsumeFood(ThingDef race, float needed)
        {
            string key = "food|" + race.defName;
            buffers.TryGetValue(key, out float credit);
            if (credit >= needed)
            {
                buffers[key] = credit - needed;
                return needed;
            }

            Map map = Map;
            float got = credit;
            foreach (IntVec3 c in GenRadial.RadialCellsAround(Position, Settings.feedRadius, true))
            {
                if (got >= needed) break;
                if (!c.InBounds(map)) continue;
                List<Thing> things = c.GetThingList(map);
                for (int i = things.Count - 1; i >= 0 && got < needed; i--)
                {
                    Thing t = things[i];
                    if (t is Corpse || t is Pawn) continue;
                    IngestibleProperties ing = t.def.ingestible;
                    if (ing == null || ing.preferability >= FoodPreferability.MealAwful) continue; // keep colonist meals
                    if (!race.race.CanEverEat(t)) continue;
                    if (t.IsForbidden(Faction.OfPlayer)) continue;
                    float nut = t.GetStatValue(StatDefOf.Nutrition);
                    if (nut <= 0f) continue;
                    int units = Mathf.Min(t.stackCount, Mathf.CeilToInt((needed - got) / nut));
                    if (units <= 0) continue;
                    got += units * nut;
                    if (units >= t.stackCount) t.Destroy();
                    else t.SplitOff(units).Destroy();
                }
            }

            float used = Mathf.Min(got, needed);
            buffers[key] = Mathf.Max(0f, got - used);
            return used;
        }

        // ---------------------------------------------------------------- products

        private void AddOutput(ThingDef def, float amount)
        {
            if (def == null || amount <= 0f) return;
            string key = "out|" + def.defName;
            buffers.TryGetValue(key, out float v);
            buffers[key] = v + amount;
            touchedOutputs.Add(def);
        }

        private void ProduceGoods(float days)
        {
            foreach (var group in scratch.GroupBy(p => p.def))
            {
                ThingDef race = group.Key;
                fedByRace.TryGetValue(race, out float fed);
                if (!fedByRace.ContainsKey(race)) fed = 1f;
                if (fed <= 0f) continue;

                var milk = race.GetCompProperties<CompProperties_Milkable>();
                var wool = race.GetCompProperties<CompProperties_Shearable>();
                var eggs = race.GetCompProperties<CompProperties_EggLayer>();
                if (milk == null && wool == null && eggs == null) continue;

                foreach (Pawn p in group)
                {
                    LifeStageDef stage = p.ageTracker.CurLifeStage;
                    if (stage == null) continue;
                    bool female = p.gender == Gender.Female;

                    if (milk != null && stage.milkable && (!milk.milkFemaleOnly || female))
                        AddOutput(milk.milkDef, milk.milkAmount * days / Mathf.Max(1, milk.milkIntervalDays) * fed);

                    if (wool != null && stage.shearable)
                        AddOutput(wool.woolDef, wool.woolAmount * days / Mathf.Max(1, wool.shearIntervalDays) * fed);

                    if (eggs != null && stage.reproductive && (!eggs.eggLayFemaleOnly || female) && eggs.eggLayIntervalDays > 0f)
                    {
                        // Unfertilized eggs only; see README "Not done".
                        float avg = (eggs.eggCountRange.min + eggs.eggCountRange.max) * 0.5f;
                        AddOutput(eggs.eggUnfertilizedDef, avg * days / eggs.eggLayIntervalDays * fed);
                    }
                }
            }
        }

        // ---------------------------------------------------------------- births

        private int BreedHerd(float days)
        {
            var newborns = new List<Pawn>();
            foreach (var group in scratch.GroupBy(p => p.def).ToList())
            {
                ThingDef race = group.Key;
                // Egg layers are handled by ProduceGoods (eggs), not by live births.
                if (race.GetCompProperties<CompProperties_EggLayer>() != null) continue;
                float gestation = race.race.gestationPeriodDays;
                if (gestation <= 0f) continue;
                if (fedByRace.TryGetValue(race, out float fed) && fed < 0.5f) continue; // starving herds do not breed

                var females = new List<Pawn>();
                int males = 0;
                var maleList = new List<Pawn>();
                foreach (Pawn p in group)
                {
                    LifeStageDef stage = p.ageTracker.CurLifeStage;
                    if (stage == null || !stage.reproductive) continue;
                    if (p.gender == Gender.Female) females.Add(p);
                    else if (p.gender == Gender.Male) { males++; maleList.Add(p); }
                }
                if (females.Count == 0 || males == 0) continue;

                int pairs = Mathf.Min(females.Count, males * Mathf.Max(1, Settings.femalesPerMale));
                float expected = pairs * days / (gestation + Settings.restDays);
                int litters = GenMath.RoundRandom(expected);
                for (int i = 0; i < litters; i++)
                {
                    Pawn mother = females.RandomElement();
                    Pawn father = maleList.RandomElement();
                    int size = 1;
                    if (race.race.litterSizeCurve != null)
                        size = Mathf.Max(1, Mathf.RoundToInt(Rand.ByCurve(race.race.litterSizeCurve)));
                    for (int k = 0; k < size; k++)
                    {
                        if (innerContainer.Count + newborns.Count >= Capacity) goto full;
                        Pawn baby = MakeBaby(mother, father);
                        if (baby != null) newborns.Add(baby);
                    }
                }
            }
        full:
            int added = 0;
            foreach (Pawn baby in newborns)
            {
                // The generator may list the pawn as a world pawn; the barn owns it from here on.
                if (Find.WorldPawns.Contains(baby)) Find.WorldPawns.RemovePawn(baby);
                if (innerContainer.TryAdd(baby, false)) added++;
                else baby.Discard(true);
            }
            return added;
        }

        private static Pawn MakeBaby(Pawn mother, Pawn father)
        {
            try
            {
                var request = new PawnGenerationRequest(mother.kindDef, Faction.OfPlayer, PawnGenerationContext.NonPlayer,
                    forceGenerateNewPawn: true, canGeneratePawnRelations: false,
                    fixedBiologicalAge: 0f, fixedChronologicalAge: 0f);
                Pawn baby = PawnGenerator.GeneratePawn(request);
                if (baby == null) return null;
                baby.relations?.AddDirectRelation(PawnRelationDefOf.Parent, mother);
                if (father != null) baby.relations?.AddDirectRelation(PawnRelationDefOf.Parent, father);
                return baby;
            }
            catch (Exception e)
            {
                Log.Warning("[Underground Animal Barn] Could not generate a newborn: " + e.Message);
                return null;
            }
        }

        // ---------------------------------------------------------------- culling

        private int CullHerd()
        {
            if (cullAbove <= 0) return 0;
            int culled = 0;
            int fpm = Mathf.Max(1, Settings.femalesPerMale);
            int keepMales = Mathf.Max(1, Mathf.CeilToInt(cullAbove / (float)(fpm + 1)));

            foreach (var group in scratch.GroupBy(p => p.kindDef).ToList())
            {
                int surplus = group.Count() - cullAbove;
                if (surplus <= 0) continue;

                // Never cull bonded or named animals.
                var eligible = group.Where(p => p.Name == null && !IsBonded(p)).ToList();
                bool Adult(Pawn p) => p.ageTracker.CurLifeStage != null && p.ageTracker.CurLifeStage.reproductive;
                long Age(Pawn p) => p.ageTracker.AgeBiologicalTicks;

                // Keep the youngest adult males as breeders; the other males go first.
                var adultMales = eligible.Where(p => p.gender == Gender.Male && Adult(p)).OrderBy(Age).ToList();
                var keepers = new HashSet<Pawn>(adultMales.Take(keepMales));
                var surplusMales = adultMales.Skip(keepMales).OrderByDescending(Age);
                var otherAdults = eligible.Where(p => Adult(p) && !keepers.Contains(p) && !(p.gender == Gender.Male)).OrderByDescending(Age);
                var young = eligible.Where(p => !Adult(p)).OrderByDescending(Age);

                foreach (Pawn p in surplusMales.Concat(otherAdults).Concat(young).Take(surplus).ToList())
                {
                    AddButcherProducts(p);
                    RemoveStored(p, false);
                    culled++;
                }
            }
            if (culled > 0) RefreshScratch();
            return culled;
        }

        private void AddButcherProducts(Pawn p)
        {
            float eff = Settings.cullEfficiency;
            try
            {
                if (p.RaceProps.meatDef != null)
                    AddOutput(p.RaceProps.meatDef, p.GetStatValue(StatDefOf.MeatAmount) * eff);
                if (p.RaceProps.leatherDef != null)
                    AddOutput(p.RaceProps.leatherDef, p.GetStatValue(StatDefOf.LeatherAmount) * eff);
            }
            catch (Exception e)
            {
                Log.Warning("[Underground Animal Barn] Could not compute butcher yield: " + e.Message);
            }
        }

        /// <summary>
        /// Removes a stored pawn for good (starved or culled). It is taken out of the container first,
        /// then killed through the normal path so relations and the world pawn list stay consistent.
        /// Pawns that matter (starved ones, who may be bonded) are kept as world pawns; culled ones,
        /// which are never bonded or named, are discarded.
        /// </summary>
        private void RemoveStored(Pawn p, bool keepIfImportant)
        {
            innerContainer.Remove(p);
            try
            {
                if (!p.Dead) p.Kill(null);
            }
            catch (Exception e)
            {
                Log.Warning("[Underground Animal Barn] Killing a stored animal threw: " + e.Message);
            }
            if (!p.Destroyed && !Find.WorldPawns.Contains(p))
            {
                if (keepIfImportant) Find.WorldPawns.PassToWorld(p, PawnDiscardDecideMode.Decide);
                else p.Discard(true);
            }
        }

        // ---------------------------------------------------------------- output

        private void FlushOutputs(Map map)
        {
            foreach (ThingDef def in touchedOutputs)
            {
                string key = "out|" + def.defName;
                buffers.TryGetValue(key, out float v);
                int n = Mathf.FloorToInt(v);
                buffers[key] = v - n;
                int stacks = 0;
                while (n > 0 && stacks < MaxStacksPerFlush)
                {
                    int c = Mathf.Min(n, Mathf.Max(1, def.stackLimit));
                    Thing t = ThingMaker.MakeThing(def);
                    t.stackCount = c;
                    n -= c;
                    stacks++;
                    if (!GenPlace.TryPlaceThing(t, InteractionCell, map, ThingPlaceMode.Near))
                    {
                        t.Destroy();
                        break;
                    }
                }
            }
            touchedOutputs.Clear();
        }
    }
}
