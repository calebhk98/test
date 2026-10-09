using RimWorld;
using Verse;

namespace RemoteSurrogate
{
    [DefOf]
    public static class RSDefOf
    {
        public static HediffDef RS_SurrogateBody;
        public static JobDef RS_EnterLinkPod;
        public static ThoughtDef RS_DiedRemotely;
        public static ThoughtDef RS_LinkSevered;

        static RSDefOf() => DefOfHelper.EnsureInitializedInCtor(typeof(RSDefOf));
    }
}
