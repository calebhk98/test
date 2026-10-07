using System.Collections.Generic;
using RimWorld;
using Verse;

namespace Forklifts
{
    /// <summary>
    /// An item that holds several stacks. It is only loaded while a forklift operator
    /// carries it, and it is always emptied again before the job ends.
    /// </summary>
    public class Pallet : ThingWithComps, IThingHolder
    {
        public ThingOwner<Thing> inner;

        public Pallet()
        {
            inner = new ThingOwner<Thing>(this, false, LookMode.Deep);
        }

        public int Capacity
        {
            get { return ForkliftsMod.Settings != null ? ForkliftsMod.Settings.stacksPerPallet : 8; }
        }

        public bool Full
        {
            get { return inner.Count >= Capacity; }
        }

        public bool Empty
        {
            get { return inner.Count == 0; }
        }

        public ThingOwner GetDirectlyHeldThings()
        {
            return inner;
        }

        public void GetChildHolders(List<IThingHolder> outChildren)
        {
            ThingOwnerUtility.AppendThingHoldersFromThings(outChildren, GetDirectlyHeldThings());
        }

        public override void ExposeData()
        {
            base.ExposeData();
            Scribe_Deep.Look(ref inner, "inner", this);
            if (inner == null)
            {
                inner = new ThingOwner<Thing>(this, false, LookMode.Deep);
            }
        }

        public override void SpawnSetup(Map map, bool respawningAfterLoad)
        {
            base.SpawnSetup(map, respawningAfterLoad);
            // A loaded pallet must never sit on the ground (carrier downed or killed).
            if (inner.Count > 0)
            {
                inner.TryDropAll(Position, map, ThingPlaceMode.Near);
            }
        }

        public override void Destroy(DestroyMode mode = DestroyMode.Vanish)
        {
            Map map = MapHeld;
            if (map != null && inner.Count > 0)
            {
                inner.TryDropAll(PositionHeld, map, ThingPlaceMode.Near);
            }
            base.Destroy(mode);
        }

        public override string GetInspectString()
        {
            string s = base.GetInspectString();
            string line = "Forklifts_PalletContents".Translate(inner.Count, Capacity);
            return s.NullOrEmpty() ? line : s + "\n" + line;
        }
    }
}
