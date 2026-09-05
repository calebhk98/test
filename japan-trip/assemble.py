#!/usr/bin/env python3
"""Build ITINERARY.md: the traveller-facing deliverable.

Two parts and a set of appendices, with a linked table of contents. Anchors are
computed with the GitHub heading-slug algorithm from the real headings, so the
links need no raw HTML and survive any renderer that auto-anchors headings.
"""
import re, pathlib

FX = 155.0
ROOT = pathlib.Path("/home/user/test/japan-trip")
D = ROOT / "days"
ORDER = ["days-01-10-tokyo.md", "days-11-14-fuji-transfer.md", "days-15-19-kyoto-a.md",
         "days-20-23-kyoto-b.md", "days-24-27-hiroshima.md", "days-28-30-osaka.md"]

HDR = re.compile(r"^##\s+Day\s+(\d+)\s*[-–]\s*(.+?)\s*$", re.M)
TOT = re.compile(r"^\|\s*\*{0,2}Day total\*{0,2}\s*\|\s*\*{0,2}\s*¥?([\d,]+)\s*\*{0,2}\s*\|", re.M)

def slug(text, seen):
    """GitHub heading anchor: lowercase, strip punctuation, spaces to hyphens."""
    s = text.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    s = re.sub(r"\s", "-", s)
    n = seen.get(s, 0)
    seen[s] = n + 1
    return s if n == 0 else f"{s}-{n}"

def demote(text, levels=1, drop_title=True):
    out = []
    for line in text.split("\n"):
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            depth = len(m.group(1))
            if depth == 1 and drop_title:
                continue
            out.append("#" * min(depth + levels, 6) + " " + m.group(2))
        else:
            out.append(line)
    return "\n".join(out).strip()

# ---------------------------------------------------------------- day index --
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

run_total = sum(c for _, _, c in rows)

# ------------------------------------------------------------ build the body --
ov = (ROOT / "00-overview.md").read_text().rstrip()
title_line, ov_rest = ov.split("\n", 1)

body = [title_line, "", "@@TOC@@", "", ov_rest.strip()]

idx = ["| Day | Date | Base / focus | Day cost ¥ | $ | Cumulative $ |", "|---|---|---|---|---|---|"]
run = 0
for day, title, cost in rows:
    run += cost
    parts = [p.strip() for p in re.split(r"\s+[-–]\s+", title)]
    date = parts[0] if parts else ""
    focus = " / ".join(parts[1:]) if len(parts) > 1 else ""
    idx.append(f"| @@DAYLINK:{day}@@ | {date} | {focus} | {cost:,} | {round(cost/FX):,} | {round(run/FX):,} |")
idx.append(f"| | | **Day-line total** | **{run:,}** | **{round(run/FX):,}** | |")

body += ["", "---", "", "## 6. The thirty days at a glance", "", "\n".join(idx), f"""
Day-line spend covers lodging, food, transport and activities. Two further lines sit at
trip level and are not repeated daily: baby consumables at ¥68,000 ($439), and
miscellaneous (eSIM, coin laundry, lockers, luggage forwarding) at ¥38,000 ($245).
Adding those gives **¥{run+106000:,} (${round((run+106000)/FX):,})** planned against a
**¥1,400,000 ($9,032)** budget, leaving **¥{1400000-run-106000:,} (${round((1400000-run-106000)/FX):,})** in reserve.

---

# Part II: The daily itinerary

Every day records the schedule with durations, the lodging and its nightly cost, every
meal with its adult calorie count, every transport leg with fare and duration, and every
activity with location, admission and what it actually is. Adult calories sum to
1,950-2,100 per person per day. Infants ride free on all rail and transit and are free at
essentially every site; the exceptions are noted where they occur.
"""]

for f in ORDER:
    body += ["", "---", "", (D / f).read_text().strip()]

body += ["", "---", "", "# Appendices", "",
         "Reference material. The topic index is the fastest way in if you want to find",
         "something by subject rather than by date.", "",
         "---", "", "## Appendix A: Topic index", "",
         demote((ROOT / "topic-index.md").read_text(), 1), "",
         "---", "", "## Appendix B: The five places", "",
         "Five stops in thirty days. Each profile says what the place is, what walking",
         "around it feels like, and how it differs from the other four."]

for f in ["tokyo.md", "kawaguchiko.md", "kyoto.md", "hiroshima.md", "osaka.md"]:
    txt = (ROOT / "places" / f).read_text().strip()
    m = re.match(r"^#\s+(.*)$", txt.split("\n")[0])
    heading = m.group(1) if m else f
    body += ["", "### " + heading, "", demote(txt, 2)]

for letter, name, fn in [("C", "Advance booking", "advance-booking.md"),
                         ("D", "Shopping lists and supply runs", "shopping-lists.md"),
                         ("E", "Open decisions", "open-decisions.md")]:
    body += ["", "---", "", f"## Appendix {letter}: {name}", "",
             demote((ROOT / fn).read_text(), 1)]

app = (ROOT / "99-appendix.md").read_text()
for old, new in [(r"^##\s*Appendix B\..*$", "## Appendix F: Japan with a 12-month-old and a 20-month-old"),
                 (r"^##\s*Appendix C\..*$", "## Appendix G: How 2,000 calories a day actually gets bought"),
                 (r"^##\s*Appendix D\..*$", "## Appendix H: Confidence and sources")]:
    app = re.sub(old, new, app, flags=re.M)
m = re.search(r"^## Appendix F:", app, re.M)
body += ["", "---", "", app[m.start():].strip()]

doc = "\n".join(body)

# --------------------------------------------------- anchors and cross-links --
seen = {}
anchors = {}                       # heading text -> anchor
day_anchor = {}                    # day number  -> anchor
for line in doc.split("\n"):
    m = re.match(r"^(#{1,6})\s+(.*)$", line)
    if not m:
        continue
    text = m.group(2).strip()
    a = slug(text, seen)
    anchors.setdefault(text, a)
    dm = re.match(r"^Day\s+(\d+)\s*[-–]", text)
    if dm:
        day_anchor[int(dm.group(1))] = a

doc = re.sub(r"@@DAYLINK:(\d+)@@", lambda m: f"[{m.group(1)}](#{day_anchor[int(m.group(1))]})", doc)

# Base field on each day -> that city's profile in Appendix B.
PLACE = {"Tokyo": "Tokyo", "Kawaguchiko": "Kawaguchiko and the Fuji Five Lakes",
         "Kyoto": "Kyoto", "Hiroshima": "Hiroshima and Miyajima", "Osaka": "Osaka"}
def link_base(m):
    val = m.group(1).rstrip()
    for city, heading in PLACE.items():
        if city.lower() in val.lower() and heading in anchors:
            return f"**Base:** [{val}](#{anchors[heading]})  "
    return m.group(0)
doc = re.sub(r"^\*\*Base:\*\*\s*([^\n]*?)\s*$", link_base, doc, flags=re.M)

# Topic-index day cells -> the day sections.
def link_day_cell(m):
    head, cell, tail = m.group(1), m.group(2), m.group(3)
    parts = [p.strip() for p in re.split(r"[,/]", cell)]
    if not parts or not all(re.fullmatch(r"\d{1,2}", p) for p in parts):
        return m.group(0)
    if not all(int(p) in day_anchor for p in parts):
        return m.group(0)
    return head + ", ".join(f"[{p}](#{day_anchor[int(p)]})" for p in parts) + tail

start = doc.index("## Appendix A: Topic index")
end = doc.index("## Appendix B: The five places")
section = re.sub(r"(\|\s)([\d,\s/]+?)(\s\|)", link_day_cell, doc[start:end])
doc = doc[:start] + section + doc[end:]

# ------------------------------------------------------------ table of contents --
BOILERPLATE = {"schedule", "lodging", "meals", "transport", "activities"}
toc = ["## Table of Contents", ""]
seg_days = {}          # segment heading -> [day numbers]
cur_seg = None
for line in doc.split("\n"):
    m = re.match(r"^(#{1,3})\s+(.*)$", line)
    if not m:
        continue
    depth, text = len(m.group(1)), m.group(2).strip()
    if depth == 1 and text.startswith("Days "):
        cur_seg = text; seg_days[text] = []
    dm = re.match(r"^Day\s+(\d+)\s*[-–]", text)
    if dm and cur_seg and int(dm.group(1)) not in seg_days[cur_seg]:
        seg_days[cur_seg].append(int(dm.group(1)))

cur_seg = None
for line in doc.split("\n"):
    m = re.match(r"^(#{1,3})\s+(.*)$", line)
    if not m:
        continue
    depth, text = len(m.group(1)), m.group(2).strip()
    if text.startswith("Table of Contents") or text == title_line.lstrip("# "):
        continue
    if re.match(r"^Day\s+\d+\s*[-–]", text):
        continue                                  # linked from the segment rows below
    if depth == 3 and (text.lower() in BOILERPLATE or re.match(r"^Day \d+ Cost$", text)):
        continue                                  # per-day boilerplate
    a = anchors.get(text)
    if not a:
        continue
    if depth == 1:
        toc.append(f"- **[{text}](#{a})**")
        if text in seg_days and seg_days[text]:
            links = "  ".join(f"[{d}](#{day_anchor[d]})" for d in seg_days[text])
            toc.append(f"  - Days: {links}")
    elif depth == 2:
        toc.append(f"  - [{text}](#{a})")
    else:
        toc.append(f"    - [{text}](#{a})")
doc = doc.replace("@@TOC@@", "\n".join(toc))

(ROOT / "ITINERARY.md").write_text(doc.rstrip() + "\n")
print(f"ITINERARY.md written: {len(rows)} days, day-line total ¥{run_total:,} (${round(run_total/FX):,})")
print(f"anchors: {len(anchors)}, day links: {len(day_anchor)}")
