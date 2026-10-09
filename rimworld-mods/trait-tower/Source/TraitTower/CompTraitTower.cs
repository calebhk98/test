using System.Collections.Generic;
using System.Linq;
using RimWorld;
using UnityEngine;
using Verse;

namespace TraitTower
{
    public class CompProperties_TraitTower : CompProperties
    {
        public ThoughtDef thoughtGood;
        public ThoughtDef thoughtBad;

        public CompProperties_TraitTower()
        {
            compClass = typeof(CompTraitTower);
        }
    }

    public class CompTraitTower : ThingComp
    {
        private const int RareInterval = 250;
        private const float TicksPerDay = 60000f;

        // false: add good traits / remove bad ones. true: add bad traits / remove good ones.
        public bool reverse;

        private CompProperties_TraitTower Props => (CompProperties_TraitTower)props;
        private TraitTowerSettings S => TraitTowerMod.Settings;

        public override void PostExposeData()
        {
            base.PostExposeData();
            Scribe_Values.Look(ref reverse, "reverse", false);
        }

        public override IEnumerable<Gizmo> CompGetGizmosExtra()
        {
            foreach (Gizmo g in base.CompGetGizmosExtra())
            {
                yield return g;
            }
            if (parent.Faction == Faction.OfPlayer)
            {
                yield return new Command_Toggle
                {
                    defaultLabel = "TraitTower_ReverseLabel".Translate(),
                    defaultDesc = "TraitTower_ReverseDesc".Translate(),
                    icon = ContentFinder<Texture2D>.Get("TraitTower/TraitTower", true),
                    isActive = () => reverse,
                    toggleAction = () => reverse = !reverse
                };
            }
        }

        public override string CompInspectStringExtra()
        {
            string mode = reverse ? "TraitTower_ModeReverse".Translate() : "TraitTower_ModeNormal".Translate();
            return "TraitTower_InspectMode".Translate(mode) + "\n"
                + "TraitTower_InspectRadius".Translate(S.radius.ToString("F0"));
        }

        public override void PostDrawExtraSelectionOverlays()
        {
            base.PostDrawExtraSelectionOverlays();
            GenDraw.DrawRadiusRing(parent.Position, S.radius);
        }

        public override void CompTickRare()
        {
            base.CompTickRare();
            if (!parent.Spawned)
            {
                return;
            }
            CompPowerTrader power = parent.GetComp<CompPowerTrader>();
            if (power != null && !power.PowerOn)
            {
                return;
            }
            CompFlickable flick = parent.GetComp<CompFlickable>();
            if (flick != null && !flick.SwitchIsOn)
            {
                return;
            }

            // Convert "percent per day" into a chance for one rare tick.
            float perDay = Mathf.Clamp01(S.chancePerDayPercent / 100f);
            float perRoll = 1f - Mathf.Pow(1f - perDay, RareInterval / TicksPerDay);
            float radiusSq = S.radius * S.radius;

            IReadOnlyList<Pawn> pawns = parent.Map.mapPawns.AllPawnsSpawned;
            for (int i = pawns.Count - 1; i >= 0; i--)
            {
                Pawn p = pawns[i];
                if (!Eligible(p))
                {
                    continue;
                }
                if ((p.Position - parent.Position).LengthHorizontalSquared > radiusSq)
                {
                    continue;
                }
                if (Rand.Value < perRoll)
                {
                    TryChange(p);
                }
            }
        }

        private bool Eligible(Pawn p)
        {
            if (p.Dead || p.story == null || p.story.traits == null || !p.RaceProps.Humanlike)
            {
                return false;
            }
            if (p.IsColonist && p.HomeFaction == Faction.OfPlayer)
            {
                return true;
            }
            return S.includeSlaves && p.IsSlaveOfColony;
        }

        // The trait-class a pawn gains, and the class it loses.
        private int AddClass => reverse ? -1 : 1;

        private struct Candidate
        {
            public TraitDef def;
            public int degree;
        }

        private void TryChange(Pawn pawn)
        {
            TraitSet traits = pawn.story.traits;

            List<Trait> removable = traits.allTraits
                .Where(t => !t.ScenForced && t.sourceGene == null && !t.Suppressed
                    && S.Classify(t.def, t.Degree) == -AddClass)
                .ToList();

            int cap = Mathf.Max(1, S.maxTraits);
            bool atCap = traits.allTraits.Count >= cap;

            // Without a trait to swap out, a pawn at the cap cannot gain anything.
            bool canAdd = !atCap || removable.Count > 0;
            bool canRemove = removable.Count > 0;
            if (!canAdd && !canRemove)
            {
                return;
            }

            bool doAdd;
            if (canAdd && canRemove)
            {
                doAdd = Rand.Bool;
            }
            else
            {
                doAdd = canAdd;
            }

            if (!doAdd)
            {
                Trait victim = removable.RandomElement();
                string label = victim.LabelCap;
                traits.RemoveTrait(victim, true);
                Refresh(pawn);
                Announce(pawn, null, label);
                return;
            }

            Trait swapOut = null;
            if (atCap)
            {
                swapOut = removable.RandomElement();
            }
            List<Candidate> candidates = CollectCandidates(pawn, swapOut);
            if (candidates.Count == 0 && swapOut != null && removable.Count > 1)
            {
                // The first choice of trait to drop may be what blocks every candidate. Try the others once.
                foreach (Trait other in removable.Where(t => t != swapOut))
                {
                    candidates = CollectCandidates(pawn, other);
                    if (candidates.Count > 0)
                    {
                        swapOut = other;
                        break;
                    }
                }
            }
            if (candidates.Count == 0)
            {
                return;
            }

            Candidate pick = candidates.RandomElement();
            string lost = null;
            if (swapOut != null)
            {
                lost = swapOut.LabelCap;
                traits.RemoveTrait(swapOut, true);
            }
            Trait gained = new Trait(pick.def, pick.degree, false);
            traits.GainTrait(gained, false);
            Refresh(pawn);
            Announce(pawn, gained.LabelCap, lost);
        }

        private List<Candidate> CollectCandidates(Pawn pawn, Trait ignore)
        {
            List<Candidate> result = new List<Candidate>();
            int want = AddClass;
            foreach (TraitDef def in DefDatabase<TraitDef>.AllDefs)
            {
                foreach (TraitDegreeData data in def.degreeDatas)
                {
                    if (S.Classify(def, data.degree) != want)
                    {
                        continue;
                    }
                    if (CanGain(pawn, def, data.degree, ignore))
                    {
                        result.Add(new Candidate { def = def, degree = data.degree });
                    }
                }
            }
            return result;
        }

        private static bool CanGain(Pawn pawn, TraitDef def, int degree, Trait ignore)
        {
            foreach (Trait t in pawn.story.traits.allTraits)
            {
                if (t == ignore)
                {
                    continue;
                }
                // Same def at any degree (Industrious vs Lazy) and every declared conflict.
                if (t.def == def || def.ConflictsWith(t) || t.def.ConflictsWith(def))
                {
                    return false;
                }
                // A trait the pawn already has may need a work type this one would disable.
                if ((t.def.requiredWorkTags & def.disabledWorkTags) != WorkTags.None)
                {
                    return false;
                }
            }

            foreach (BackstoryDef b in pawn.story.AllBackstories)
            {
                if (b != null && b.DisallowsTrait(def, degree))
                {
                    return false;
                }
            }

            if ((pawn.story.DisabledWorkTagsBackstoryTraitsAndGenes & def.requiredWorkTags) != WorkTags.None)
            {
                return false;
            }

            if (pawn.skills != null)
            {
                foreach (SkillRecord skill in pawn.skills.skills)
                {
                    if (def.ConflictsWithPassion(skill.def) && skill.passion != Passion.None)
                    {
                        return false;
                    }
                    if (def.RequiresPassion(skill.def) && skill.passion == Passion.None)
                    {
                        return false;
                    }
                }
            }
            return true;
        }

        // GainTrait and RemoveTrait do part of this themselves; refreshing again is cheap and harmless.
        private static void Refresh(Pawn pawn)
        {
            pawn.story.traits.RecalculateSuppression();
            pawn.Notify_DisabledWorkTypesChanged();
            if (pawn.skills != null)
            {
                pawn.skills.Notify_SkillDisablesChanged();
            }
            if (pawn.workSettings != null)
            {
                pawn.workSettings.Notify_DisabledWorkTypesChanged();
            }
            if (pawn.needs != null)
            {
                pawn.needs.AddOrRemoveNeedsAsAppropriate();
            }
            if (pawn.health != null)
            {
                pawn.health.capacities.Clear();
            }
            if (pawn.Drawer != null && pawn.Drawer.renderer != null)
            {
                pawn.Drawer.renderer.SetAllGraphicsDirty();
            }
        }

        private void Announce(Pawn pawn, string gainedLabel, string lostLabel)
        {
            if (S.showMessages)
            {
                string text;
                if (gainedLabel != null && lostLabel != null)
                {
                    text = "TraitTower_MsgSwap".Translate(pawn.LabelShortCap, lostLabel, gainedLabel);
                }
                else if (gainedLabel != null)
                {
                    text = "TraitTower_MsgGained".Translate(pawn.LabelShortCap, gainedLabel);
                }
                else
                {
                    text = "TraitTower_MsgLost".Translate(pawn.LabelShortCap, lostLabel);
                }
                Messages.Message(text, pawn, reverse ? MessageTypeDefOf.NegativeEvent : MessageTypeDefOf.PositiveEvent, false);
            }

            if (S.moodThought && pawn.needs != null && pawn.needs.mood != null)
            {
                ThoughtDef thought = reverse ? Props.thoughtBad : Props.thoughtGood;
                if (thought != null)
                {
                    pawn.needs.mood.thoughts.memories.TryGainMemory(thought);
                }
            }
        }
    }
}
