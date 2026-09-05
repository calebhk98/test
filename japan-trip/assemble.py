#!/usr/bin/env python3
"""Build ITINERARY.md, the traveller-facing deliverable.

Only content a traveller uses goes in. The research packs, proposal files and
coverage audits under research/ and proposals/ stay in the repo as working
documents; they are not part of the report.
"""
import re, pathlib

FX = 155.0
ROOT = pathlib.Path("/home/user/test/japan-trip")
D = ROOT / "days"
ORDER = ["days-01-10-tokyo.md", "days-11-14-fuji-transfer.md", "days-15-19-kyoto-a.md",
         "days-20-23-kyoto-b.md", "days-24-27-hiroshima.md", "days-28-30-osaka.md"]

HDR = re.compile(r"^##\s+Day\s+(\d+)\s*[-–]\s*(.+?)\s*$", re.M)
TOT = re.compile(r"^\|\s*\*{0,2}Day total\*{0,2}\s*\|\s*\*{0,2}\s*¥?([\d,]+)\s*\*{0,2}\s*\|", re.M)

# --- day index -------------------------------------------------------------
rows = []
for f in ORDER:
    t = (D / f).read_text()
    marks = [(m.start(), ("h", int(m.group(1)), m.group(2).strip())) for m in HDR.finditer(t)]
    marks += [(m.start(), ("t", int(m.group(1).replace(",", "")), None)) for m in TOT.finditer(t)]
    marks.sort()
    cur = None
    for _, (k, a, b) in marks:
        if k == "h":
            cur = (a, b)
        elif cur:
            rows.append((cur[0], cur[1], a)); cur = None

run = 0
idx = ["| Day | Date | Base / focus | Day cost ¥ | $ | Cumulative $ |", "|---|---|---|---|---|---|"]
for day, title, cost in rows:
    run += cost
    parts = [p.strip() for p in re.split(r"\s+[-–]\s+", title)]
    date = parts[0] if parts else ""
    focus = " / ".join(parts[1:]) if len(parts) > 1 else ""
    idx.append(f"| {day} | {date} | {focus} | {cost:,} | {round(cost/FX):,} | {round(run/FX):,} |")
idx.append(f"| | | **Day-line total** | **{run:,}** | **{round(run/FX):,}** | |")

out = [(ROOT / "00-overview.md").read_text().rstrip(),
       "\n---\n\n## 6. The thirty days at a glance\n",
       "\n".join(idx),
       f"""
Day-line spend covers lodging, food, transport and activities. Two further lines sit
at trip level and are not repeated daily: baby consumables at ¥68,000 ($439), and
miscellaneous (eSIM, coin laundry, lockers, luggage forwarding) at ¥38,000 ($245).
Adding those gives **¥{run+106000:,} (${round((run+106000)/FX):,})** planned against a
**¥1,400,000 ($9,032)** budget, leaving **¥{1400000-run-106000:,} (${round((1400000-run-106000)/FX):,})** in reserve.

---

# Part II: The daily itinerary

Every day records the schedule with durations, the lodging and its nightly cost, every
meal with its adult calorie count, every transport leg with fare and duration, and every
activity with location, admission and what it actually is. Adult calories sum to
1,950-2,100 per person per day throughout. Infants ride free on all rail and transit and
are free at essentially every site; the exceptions are noted where they occur.
"""]

for f in ORDER:
    out.append("\n---\n\n" + (D / f).read_text().strip())

out.append("""
---

# Part III: The five places

Five stops in thirty days. Each profile says what the place is, what walking around it
feels like, and how it differs from the other four.
""")
for f in ["tokyo.md", "kawaguchiko.md", "kyoto.md", "hiroshima.md", "osaka.md"]:
    out.append("\n---\n\n" + (ROOT / "places" / f).read_text().strip())

for title, f in [("Part IV: Topic index", "topic-index.md"),
                 ("Part V: Advance booking", "advance-booking.md"),
                 ("Part VI: Shopping lists and supply runs", "shopping-lists.md"),
                 ("Part VII: Open decisions", "open-decisions.md")]:
    p = ROOT / f
    if p.exists():
        out.append("\n---\n\n# " + title + "\n\n" + p.read_text().strip())

out.append("\n---\n\n" + (ROOT / "99-appendix.md").read_text().strip()
           .replace("# Part III: Appendices", "# Part VIII: Appendices"))

(ROOT / "ITINERARY.md").write_text("\n".join(out) + "\n")
print(f"ITINERARY.md written: {len(rows)} days, day-line total ¥{run:,} (${round(run/FX):,})")
