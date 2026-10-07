using System.Collections.Generic;
using RimWorld;
using Verse;

namespace StorytellerHundred
{
    // Sends a letter at 25%, 50%, 75% and 100% of the target while The Hundred is the storyteller.
    public class GameComponent_Milestones : GameComponent
    {
        private int reachedQuarter;

        public GameComponent_Milestones(Game game) { }

        public override void ExposeData()
        {
            Scribe_Values.Look(ref reachedQuarter, "reachedQuarter", 0);
        }

        public override void GameComponentTick()
        {
            if (Find.TickManager.TicksGame % 2500 != 0) return;
            if (Find.Storyteller == null || Find.Storyteller.def.defName != "SH_TheHundred") return;
            var settings = HundredMod.Settings;
            if (!settings.letters) return;
            int have = StorytellerComp_Arrivals.ColonistCount();
            int goal = settings.target;
            int quarter = have * 4 / goal;
            if (quarter > 4) quarter = 4;
            if (quarter <= reachedQuarter) return;
            reachedQuarter = quarter;
            if (quarter >= 4)
            {
                Find.LetterStack.ReceiveLetter("SH_TargetLabel".Translate(), "SH_TargetText".Translate(goal),
                    LetterDefOf.PositiveEvent);
            }
            else
            {
                int shown = goal * quarter / 4;
                Find.LetterStack.ReceiveLetter("SH_MilestoneLabel".Translate(shown), "SH_MilestoneText".Translate(have),
                    LetterDefOf.PositiveEvent);
            }
        }
    }
}
