using RimWorld;
using UnityEngine;
using Verse;

namespace DigitalStorage
{
    public class ITab_DSContents : ITab
    {
        private Vector2 scroll;
        private const float RowH = 28f;

        public ITab_DSContents()
        {
            size = new Vector2(440f, 480f);
            labelKey = "DS_TabContents";
        }

        public override bool IsVisible => SelThing is Building_DSCore;

        protected override void FillTab()
        {
            var core = SelThing as Building_DSCore;
            if (core == null) return;
            Rect rect = new Rect(0f, 0f, size.x, size.y).ContractedBy(10f);
            Text.Font = GameFont.Small;
            float y = rect.y;

            Widgets.Label(new Rect(rect.x, y, rect.width, 24f), (core.Online ? "DS_Online" : "DS_Offline").Translate());
            y += 26f;
            y = Bar(rect, y, core.TotalItems, core.MaxItems, "DS_ItemsLine".Translate(core.TotalItems, core.MaxItems));
            y = Bar(rect, y, core.TypeCount, core.MaxTypes, "DS_TypesLine".Translate(core.TypeCount, core.MaxTypes));
            Widgets.Label(new Rect(rect.x, y, rect.width, 24f), "DS_DrivesLine".Translate(core.Drives.Count, core.DriveSlots));
            y += 30f;

            var list = core.SortedContents;
            Rect outRect = new Rect(rect.x, y, rect.width, rect.yMax - y);
            if (list.Count == 0)
            {
                Widgets.Label(outRect, "DS_Empty".Translate());
                return;
            }
            Rect view = new Rect(0f, 0f, outRect.width - 16f, list.Count * RowH);
            Widgets.BeginScrollView(outRect, ref scroll, view);
            int first = Mathf.Max(0, (int)(scroll.y / RowH));
            int last = Mathf.Min(list.Count, first + (int)(outRect.height / RowH) + 2);
            for (int i = first; i < last; i++)
            {
                Rect row = new Rect(0f, i * RowH, view.width, RowH);
                if (i % 2 == 0) Widgets.DrawLightHighlight(row);
                Widgets.ThingIcon(new Rect(row.x + 2f, row.y + 2f, RowH - 4f, RowH - 4f), list[i].Key);
                Widgets.Label(new Rect(row.x + RowH + 6f, row.y + 3f, view.width - RowH - 90f, RowH), list[i].Key.LabelCap);
                Text.Anchor = TextAnchor.UpperRight;
                Widgets.Label(new Rect(row.xMax - 90f, row.y + 3f, 88f, RowH), list[i].Value.ToString("N0"));
                Text.Anchor = TextAnchor.UpperLeft;
                TooltipHandler.TipRegion(row, list[i].Key.description);
            }
            Widgets.EndScrollView();
        }

        private static float Bar(Rect rect, float y, int value, int max, string label)
        {
            Rect r = new Rect(rect.x, y, rect.width, 22f);
            Widgets.FillableBar(r, max > 0 ? Mathf.Clamp01((float)value / max) : 0f);
            Text.Anchor = TextAnchor.MiddleCenter;
            Widgets.Label(r, label);
            Text.Anchor = TextAnchor.UpperLeft;
            return y + 26f;
        }
    }
}
