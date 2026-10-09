using System.Collections.Generic;
using RimWorld;
using Verse;

namespace RemoteSurrogate
{
    /// <summary>
    /// Marks a pawn as a remote body and stores the link: which pod it belongs to, the
    /// ids of the gear it was generated with (destroyed when the link ends) and the
    /// experience it has earned (partly passed back to the operator).
    /// </summary>
    public class Hediff_SurrogateBody : Hediff
    {
        public Building_LinkPod pod;
        public bool endPending;
        public LinkEndReason pendingReason;
        public List<int> generatedGearIds = new List<int>();
        public Dictionary<SkillDef, float> xpGained = new Dictionary<SkillDef, float>();

        // scribe scratch lists
        private List<SkillDef> keysTmp;
        private List<float> valuesTmp;

        public override void ExposeData()
        {
            base.ExposeData();
            Scribe_References.Look(ref pod, "pod");
            Scribe_Values.Look(ref endPending, "endPending");
            Scribe_Values.Look(ref pendingReason, "pendingReason");
            Scribe_Collections.Look(ref generatedGearIds, "generatedGearIds", LookMode.Value);
            Scribe_Collections.Look(ref xpGained, "xpGained", LookMode.Def, LookMode.Value, ref keysTmp, ref valuesTmp);
            if (Scribe.mode == LoadSaveMode.PostLoadInit)
            {
                if (generatedGearIds == null) generatedGearIds = new List<int>();
                if (xpGained == null) xpGained = new Dictionary<SkillDef, float>();
            }
        }

        public void AddXp(SkillDef def, float xp)
        {
            xpGained.TryGetValue(def, out float cur);
            xpGained[def] = cur + xp;
        }

        public static Hediff_SurrogateBody Of(Pawn p)
        {
            return p?.health?.hediffSet?.GetFirstHediffOfDef(RSDefOf.RS_SurrogateBody) as Hediff_SurrogateBody;
        }
    }
}
