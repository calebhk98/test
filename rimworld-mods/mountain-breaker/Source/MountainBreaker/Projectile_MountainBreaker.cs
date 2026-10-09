using System.Linq;
using RimWorld;
using Verse;

namespace MountainBreaker
{
    public class Projectile_MountainBreaker : Projectile
    {
        protected override void Impact(Thing hitThing, bool blockedByShield = false)
        {
            Map map = Map;
            IntVec3 center = hitThing != null && hitThing.Spawned ? hitThing.Position : Position;
            Thing instigator = launcher;
            if (map != null)
            {
                var s = MountainBreakerMod.Settings;
                // Closest cells first so the hole opens from the middle outward.
                var cells = GenRadial.RadialCellsAround(center, s.radius, true)
                    .Where(c => c.InBounds(map)).ToList();
                map.GetComponent<BreakQueue>().Enqueue(cells);
                if (s.blastDamage > 0)
                {
                    GenExplosion.DoExplosion(center, map, s.radius, DamageDefOf.Bomb, instigator, s.blastDamage,
                        0f, null, equipmentDef, def, intendedTarget.Thing);
                }
            }
            Destroy();
        }
    }

    public class Verb_ShootMountainBreaker : Verb_Shoot
    {
        public override float HighlightFieldRadiusAroundTarget(out bool needLOSToCenter)
        {
            needLOSToCenter = false;
            return MountainBreakerMod.Settings.radius;
        }
    }
}
