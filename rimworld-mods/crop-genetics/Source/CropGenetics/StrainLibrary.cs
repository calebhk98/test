using System.Collections.Generic;
using RimWorld;
using Verse;

namespace CropGenetics
{
    /// <summary>
    /// Save-game data: the strain of every growing zone, plus the colony's saved strain library.
    /// </summary>
    public class StrainLibrary : GameComponent
    {
        private Dictionary<int, Strain> zoneStrains = new Dictionary<int, Strain>();
        public List<Strain> saved = new List<Strain>();
        private int nextStrainNumber = 1;

        // Scribe helpers
        private List<int> tmpKeys;
        private List<Strain> tmpValues;

        public StrainLibrary(Game game) { }

        public static StrainLibrary Instance
        {
            get { return Current.Game != null ? Current.Game.GetComponent<StrainLibrary>() : null; }
        }

        /// <summary>Strain of a zone for its current crop. Returns null if the zone grows nothing.</summary>
        public Strain GetStrain(Zone_Growing zone)
        {
            ThingDef def = zone.GetPlantDefToGrow();
            if (def == null) return null;
            Strain s;
            if (!zoneStrains.TryGetValue(zone.ID, out s) || s.plantDefName != def.defName)
            {
                s = new Strain(def.defName);
                zoneStrains[zone.ID] = s;
            }
            return s;
        }

        /// <summary>Read-only lookup that never creates an entry (used on hot paths).</summary>
        public Strain PeekStrain(Zone_Growing zone, ThingDef plantDef)
        {
            Strain s;
            if (zoneStrains.TryGetValue(zone.ID, out s) && s.plantDefName == plantDef.defName) return s;
            return null;
        }

        public void SetStrain(Zone_Growing zone, Strain s)
        {
            zoneStrains[zone.ID] = s;
        }

        public void ResetStrain(Zone_Growing zone)
        {
            zoneStrains.Remove(zone.ID);
        }

        public void SaveToLibrary(Strain s)
        {
            Strain copy = s.Copy();
            copy.name = "CropGenetics_StrainName".Translate(nextStrainNumber++, s.generation);
            saved.Add(copy);
        }

        public IEnumerable<Strain> SavedFor(ThingDef def)
        {
            foreach (Strain s in saved)
                if (s.plantDefName == def.defName) yield return s;
        }

        public override void FinalizeInit()
        {
            // Drop strains of zones that no longer exist.
            var live = new HashSet<int>();
            foreach (Map map in Find.Maps)
                foreach (Zone z in map.zoneManager.AllZones) live.Add(z.ID);
            var dead = new List<int>();
            foreach (int id in zoneStrains.Keys) if (!live.Contains(id)) dead.Add(id);
            foreach (int id in dead) zoneStrains.Remove(id);
        }

        public override void ExposeData()
        {
            Scribe_Collections.Look(ref zoneStrains, "zoneStrains", LookMode.Value, LookMode.Deep, ref tmpKeys, ref tmpValues);
            Scribe_Collections.Look(ref saved, "saved", LookMode.Deep);
            Scribe_Values.Look(ref nextStrainNumber, "nextStrainNumber", 1);
            if (Scribe.mode == LoadSaveMode.PostLoadInit)
            {
                if (zoneStrains == null) zoneStrains = new Dictionary<int, Strain>();
                if (saved == null) saved = new List<Strain>();
                saved.RemoveAll(s => s == null);
            }
        }
    }
}
