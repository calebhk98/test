using System.Collections.Generic;
using Verse;

namespace RemoteSurrogate
{
    /// <summary>
    /// Ends links one tick after the surrogate's "death" was intercepted, so the link is
    /// never torn down in the middle of the health tracker's own state change.
    /// </summary>
    public class RSManager : GameComponent
    {
        private static readonly List<Hediff_SurrogateBody> queue = new List<Hediff_SurrogateBody>();

        public RSManager(Game game) { }

        public static void Enqueue(Hediff_SurrogateBody h)
        {
            if (!queue.Contains(h)) queue.Add(h);
        }

        public override void GameComponentTick()
        {
            if (queue.Count == 0) return;
            var work = new List<Hediff_SurrogateBody>(queue);
            queue.Clear();
            foreach (var h in work)
            {
                if (h.pod != null && h.pod.Spawned) h.pod.EndLink(h.pendingReason);
            }
        }

        public override void LoadedGame() { queue.Clear(); }
        public override void StartedNewGame() { queue.Clear(); }
    }
}
