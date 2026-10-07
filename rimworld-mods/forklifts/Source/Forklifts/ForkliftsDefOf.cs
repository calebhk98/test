using RimWorld;
using Verse;

namespace Forklifts
{
    [DefOf]
    public static class ForkliftsDefOf
    {
        public static ThingDef Forklifts_Pallet;
        public static ThingDef Forklifts_Forklift;
        public static JobDef Forklifts_HaulPallet;

        static ForkliftsDefOf()
        {
            DefOfHelper.EnsureInitializedInCtor(typeof(ForkliftsDefOf));
        }
    }
}
