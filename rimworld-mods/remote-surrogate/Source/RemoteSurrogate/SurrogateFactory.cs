using System.Collections.Generic;
using RimWorld;
using UnityEngine;
using Verse;

namespace RemoteSurrogate
{
    public static class SurrogateFactory
    {
        /// <summary>Builds (but does not spawn) a remote body that mirrors the operator.</summary>
        public static Pawn Make(Pawn op, Building_LinkPod pod)
        {
            var request = new PawnGenerationRequest(
                kind: op.kindDef ?? PawnKindDefOf.Colonist,
                faction: Faction.OfPlayer,
                context: PawnGenerationContext.NonPlayer,
                forceGenerateNewPawn: true,
                canGeneratePawnRelations: false,
                allowAddictions: false,
                allowPregnant: false,
                fixedBiologicalAge: op.ageTracker.AgeBiologicalYearsFloat,
                fixedChronologicalAge: op.ageTracker.AgeBiologicalYearsFloat,
                fixedGender: op.gender,
                forcedXenotype: op.genes?.Xenotype,
                forceNoIdeo: op.Ideo == null,
                fixedIdeo: op.Ideo);
            Pawn s = PawnGenerator.GeneratePawn(request);

            CopyIdentity(op, s);
            CopySkills(op, s);
            CopyWorkSettings(op, s);

            var hediff = (Hediff_SurrogateBody)HediffMaker.MakeHediff(RSDefOf.RS_SurrogateBody, s);
            hediff.pod = pod;
            if (s.apparel != null)
                foreach (Apparel a in s.apparel.WornApparel) hediff.generatedGearIds.Add(a.thingIDNumber);
            if (s.equipment != null)
                foreach (ThingWithComps e in s.equipment.AllEquipmentListForReading) hediff.generatedGearIds.Add(e.thingIDNumber);
            if (s.inventory != null)
                foreach (Thing t in s.inventory.innerContainer) hediff.generatedGearIds.Add(t.thingIDNumber);
            s.health.AddHediff(hediff);
            return s;
        }

        private static void CopyIdentity(Pawn op, Pawn s)
        {
            if (op.Name is NameTriple nt)
            {
                string nick = nt.Nick.NullOrEmpty() ? nt.First : nt.Nick;
                s.Name = new NameTriple(nt.First, "RS_SurrogateNick".Translate(nick).Resolve(), nt.Last);
            }
            else if (op.Name != null)
            {
                s.Name = new NameSingle("RS_SurrogateNick".Translate(op.Name.ToStringShort).Resolve());
            }

            if (s.story != null && op.story != null)
            {
                s.story.Childhood = op.story.Childhood;
                s.story.Adulthood = op.story.Adulthood;
                if (s.story.traits != null && op.story.traits != null)
                {
                    foreach (Trait t in new List<Trait>(s.story.traits.allTraits))
                        s.story.traits.RemoveTrait(t);
                    foreach (Trait t in op.story.traits.allTraits)
                        s.story.traits.GainTrait(new Trait(t.def, t.Degree, true));
                }
            }
        }

        private static void CopySkills(Pawn op, Pawn s)
        {
            float frac = RemoteSurrogateMod.Settings.skillFraction;
            foreach (SkillRecord rec in s.skills.skills)
            {
                SkillRecord src = op.skills.GetSkill(rec.def);
                if (src == null) continue;
                rec.Level = Mathf.Clamp(Mathf.RoundToInt(src.Level * frac), 0, SkillRecord.MaxLevel);
                rec.passion = src.passion;
                rec.xpSinceLastLevel = 0f;
                rec.xpSinceMidnight = 0f;
            }
            s.skills.Notify_SkillDisablesChanged();
        }

        private static void CopyWorkSettings(Pawn op, Pawn s)
        {
            if (s.workSettings == null || op.workSettings == null) return;
            s.workSettings.EnableAndInitializeIfNotAlreadyInitialized();
            s.Notify_DisabledWorkTypesChanged();
            foreach (WorkTypeDef w in DefDatabase<WorkTypeDef>.AllDefsListForReading)
            {
                if (s.WorkTypeIsDisabled(w)) continue;
                s.workSettings.SetPriority(w, op.workSettings.GetPriority(w));
            }
        }
    }
}
