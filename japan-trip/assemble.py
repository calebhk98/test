#!/usr/bin/env python3
"""Build ITINERARY.md: front matter + a generated day index + all 30 day blocks."""
import re, pathlib
FX=155.0
ROOT=pathlib.Path("/home/user/test/japan-trip"); D=ROOT/"days"
ORDER=["days-01-10-tokyo.md","days-11-14-fuji-transfer.md","days-15-19-kyoto-a.md",
       "days-20-23-kyoto-b.md","days-24-27-hiroshima.md","days-28-30-osaka.md"]
HDR=re.compile(r"^##\s+Day\s+(\d+)\s*[-—]\s*(.+)$",re.M)
TOT=re.compile(r"^\|\s*\*{0,2}Day total\*{0,2}\s*\|\s*\*{0,2}\s*¥?([\d,]+)\s*\*{0,2}\s*\|",re.M)

rows=[]
for f in ORDER:
    t=(D/f).read_text()
    marks=[(m.start(),("h",int(m.group(1)),m.group(2).strip())) for m in HDR.finditer(t)]
    marks+=[(m.start(),("t",int(m.group(1).replace(",","")),None)) for m in TOT.finditer(t)]
    marks.sort()
    cur=None
    for _,(k,a,b) in marks:
        if k=="h": cur=(a,b)
        elif cur: rows.append((cur[0],cur[1],a)); cur=None

run=0; idx=["| Day | Date | Base / focus | Day cost ¥ | $ | Cumulative $ |","|---|---|---|---|---|---|"]
for day,title,cost in rows:
    run+=cost
    parts=[p.strip() for p in re.split(r"\s+[-—]\s+",title)]
    date=parts[0] if parts else ""
    focus=" / ".join(parts[1:]) if len(parts)>1 else ""
    idx.append(f"| {day} | {date} | {focus} | {cost:,} | {round(cost/FX):,} | {round(run/FX):,} |")
idx.append(f"| | | **Day-line total** | **{run:,}** | **{round(run/FX):,}** | |")

out=[(ROOT/"00-overview.md").read_text().rstrip(),
     "\n---\n\n## 6. The thirty days at a glance\n",
     "\n".join(idx),
     f"""
Day-line spend covers lodging, food, transport and activities. Two further lines sit
at trip level and are not repeated daily: baby consumables (diapers, formula, purees)
at ¥68,000 ($439), and miscellaneous (eSIM, coin laundry, lockers, luggage forwarding)
at ¥38,000 ($245). Adding those gives **¥{run+106000:,} (${round((run+106000)/FX):,})** planned against a
**¥1,400,000 ($9,032)** budget, leaving **¥{1400000-run-106000:,} (${round((1400000-run-106000)/FX):,})** in reserve.

---

# Part II: The daily itinerary

Every day below records the schedule with durations, the lodging and its nightly cost,
every meal with its adult calorie count, every transport leg with fare and duration,
and every activity with location and admission. Adult calories sum to 1,950-2,100 per
person per day throughout. Infants are costed on their own meal row and ride free on
all rail and transit.
"""]
for f in ORDER:
    out.append("\n---\n\n"+(D/f).read_text().strip())
# Part III: the places, Part IV: coverage, Part V: booking, Part VI: shopping, Part VII: appendices
out.append("""
---

# Part III: The five places

Five stops in thirty days, and a first-time visitor cannot be expected to know how
they differ. Each profile below says what the place actually is, what walking around
it feels like, how it contrasts with the other four, and then audits what this
itinerary sees there against what a first-time visitor would want to see.
""")
for name, f in [("Tokyo","tokyo.md"), ("Kawaguchiko and the Fuji Five Lakes","kawaguchiko.md"),
                ("Kyoto","kyoto.md"), ("Hiroshima and Miyajima","hiroshima.md"), ("Osaka","osaka.md")]:
    out.append("\n---\n\n"+(ROOT/"places"/f).read_text().strip())
for title, f in [("Part IV: Covering the group's stated interests","interests.md"),
                 ("Part V: Whole-trip coverage audit","coverage-audit.md"),
                 ("Part VI: Advance booking","advance-booking.md"),
                 ("Part VII: Shopping lists and supply runs","shopping-lists.md"),
                 ("Part VIII: Open decisions and things to check","open-decisions.md")]:
    out.append("\n---\n\n# "+title+"\n\n"+(ROOT/f).read_text().strip())
out.append("\n---\n\n"+(ROOT/"99-appendix.md").read_text().strip().replace("# Part III: Appendices","# Part IX: Appendices"))
(ROOT/"ITINERARY.md").write_text("\n".join(out)+"\n")
print(f"ITINERARY.md written: {len(rows)} days, day-line total ¥{run:,} (${round(run/FX):,})")
