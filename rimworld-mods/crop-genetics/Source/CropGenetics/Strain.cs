using Verse;

namespace CropGenetics
{
    public class Strain : IExposable
    {
        public string plantDefName;
        public string name;
        public int generation;
        public float yieldMult = 1f;
        public float growthMult = 1f;
        public float hardiness = 0f;

        public Strain() { }

        public Strain(string plantDefName)
        {
            this.plantDefName = plantDefName;
        }

        public Strain Copy()
        {
            return new Strain(plantDefName)
            {
                name = name,
                generation = generation,
                yieldMult = yieldMult,
                growthMult = growthMult,
                hardiness = hardiness
            };
        }

        public bool IsBase
        {
            get { return generation == 0 && yieldMult == 1f && growthMult == 1f && hardiness == 0f; }
        }

        public string Summary()
        {
            return "CropGenetics_StrainSummary".Translate(
                yieldMult.ToStringPercent("F0"),
                growthMult.ToStringPercent("F0"),
                hardiness.ToStringPercent("F0"),
                generation);
        }

        public void ExposeData()
        {
            Scribe_Values.Look(ref plantDefName, "plantDefName");
            Scribe_Values.Look(ref name, "name");
            Scribe_Values.Look(ref generation, "generation", 0);
            Scribe_Values.Look(ref yieldMult, "yieldMult", 1f);
            Scribe_Values.Look(ref growthMult, "growthMult", 1f);
            Scribe_Values.Look(ref hardiness, "hardiness", 0f);
        }
    }
}
