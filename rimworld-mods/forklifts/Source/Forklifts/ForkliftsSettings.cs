using Verse;

namespace Forklifts
{
    public class ForkliftsSettings : ModSettings
    {
        public int stacksPerPallet = 8;
        public int minStacksPerTrip = 3;
        public int pickupRadius = 20;
        public int unloadRadius = 8;
        public int loadTicks = 15;
        public bool requireForklift = true;

        public override void ExposeData()
        {
            Scribe_Values.Look(ref stacksPerPallet, "stacksPerPallet", 8);
            Scribe_Values.Look(ref minStacksPerTrip, "minStacksPerTrip", 3);
            Scribe_Values.Look(ref pickupRadius, "pickupRadius", 20);
            Scribe_Values.Look(ref unloadRadius, "unloadRadius", 8);
            Scribe_Values.Look(ref loadTicks, "loadTicks", 15);
            Scribe_Values.Look(ref requireForklift, "requireForklift", true);
        }
    }
}
