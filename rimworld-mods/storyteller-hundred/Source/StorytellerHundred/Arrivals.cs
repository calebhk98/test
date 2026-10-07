using System.Collections.Generic;
using System.Linq;
using RimWorld;
using Verse;

namespace StorytellerHundred
{
    public class StorytellerCompProperties_Arrivals : StorytellerCompProperties
    {
        public float mtbDays = 2.5f;
        public List<IncidentDef> incidents = new List<IncidentDef>();

        public StorytellerCompProperties_Arrivals()
        {
            compClass = typeof(StorytellerComp_Arrivals);
        }
    }

    // Fires people-arriving incidents more often the further the colony is from the target.
    public class StorytellerComp_Arrivals : StorytellerComp
    {
        private StorytellerCompProperties_Arrivals Props => (StorytellerCompProperties_Arrivals)props;

        public static int ColonistCount()
        {
            return PawnsFinder.AllMapsCaravansAndTravellingTransporters_Alive_FreeColonists.Count;
        }

        public override IEnumerable<FiringIncident> MakeIntervalIncidents(IIncidentTarget target)
        {
            var settings = HundredMod.Settings;
            if (!(target is Map map) || !map.IsPlayerHome) yield break;
            int have = ColonistCount();
            int goal = settings.target;
            float mtb = Props.mtbDays / settings.rate;
            if (have >= goal)
            {
                if (settings.relaxAfterTarget) yield break;
            }
            else
            {
                // Up to 3x as frequent when the colony is tiny, 1x right at the target.
                float missing = (goal - have) / (float)goal;
                mtb /= 1f + 2f * missing;
            }
            if (!Rand.MTBEventOccurs(mtb, 60000f, 1000f)) yield break;

            var options = new List<IncidentDef>();
            foreach (var def in Props.incidents)
            {
                if (def == null) continue;
                var parms = GenerateParms(def.category, target);
                if (def.Worker.CanFireNow(parms)) options.Add(def);
            }
            if (options.Count == 0) yield break;
            var pick = options.RandomElement();
            yield return new FiringIncident(pick, this, GenerateParms(pick.category, target));
        }
    }
}
