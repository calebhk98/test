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

body += ["", "---", "", "## The thirty days at a glance", "", "\n".join(idx), f"""
Day-line spend covers lodging, food, transport and activities. Two further lines sit at
trip level and are not repeated daily: baby consumables at ¥68,000 ($439), and
miscellaneous (eSIM, coin laundry, lockers, luggage forwarding) at ¥38,000 ($245).
Adding those gives **¥{run+106000:,} (${round((run+106000)/FX):,})** planned against a
**¥1,400,000 ($9,032)** budget, leaving **¥{1400000-run-106000:,} (${round((1400000-run-106000)/FX):,})** in reserve.

"""]

for f in ORDER:
    body += ["", "---", "", (D / f).read_text().strip()]

body += ["", "---", "", "# Appendices", "",
         "Reference material. The topic index is the fastest way in if you want to find",
         "something by subject rather than by date.", "",
         "---", "", "## Appendix A: Topic index", "",
         demote((ROOT / "topic-index.md").read_text(), 1), "",
         "---", "", "## Appendix B: Food index", "",
         demote((ROOT / "food-index.md").read_text(), 1), "",
         "---", "", "## Appendix C: The five places", "",
         "Five stops in thirty days. Each profile says what the place is, what walking",
         "around it feels like, and how it differs from the other four."]

for f in ["tokyo.md", "kawaguchiko.md", "kyoto.md", "hiroshima.md", "osaka.md"]:
    txt = (ROOT / "places" / f).read_text().strip()
    m = re.match(r"^#\s+(.*)$", txt.split("\n")[0])
    heading = m.group(1) if m else f
    body += ["", "### " + heading, "", demote(txt, 2)]

for letter, name, fn in [("D", "Hotels and lodging", "hotels.md"),
                         ("E", "Advance booking", "advance-booking.md"),
                         ("F", "Shopping lists and supply runs", "shopping-lists.md"),
                         ("G", "Open decisions", "open-decisions.md"),
                         ("H", "Transport", "transport.md"),
                         ("I", "Why these dates", "why-dates.md"),
                         ("J", "Why this route", "why-route.md"),
                         ("K", "How the money works", "money.md")]:
    body += ["", "---", "", f"## Appendix {letter}: {name}", "",
             demote((ROOT / fn).read_text(), 1)]

app = (ROOT / "99-appendix.md").read_text()
for old, new_h in [(r"^##\s*Appendix B\..*$", "## Appendix L: Japan with a 12-month-old and a 20-month-old"),
                   (r"^##\s*Appendix C\..*$", "## Appendix M: How 2,000 calories a day actually gets bought")]:
    app = re.sub(old, new_h, app, flags=re.M)
m = re.search(r"^## Appendix L:", app, re.M)
body += ["", "---", "", app[m.start():].strip()]

doc = "\n".join(body)

# --------------------------------------------------- anchors and cross-links --
seen = {}
anchors = {}                       # heading text -> anchor
day_sections = {}                  # day number -> {section name: anchor}
cur_day_for_sections = None
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
        cur_day_for_sections = int(dm.group(1))
    elif text in ("Schedule", "Meals", "Transport", "Activities") and cur_day_for_sections:
        day_sections.setdefault(cur_day_for_sections, {})[text] = a

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

# Build a name -> topic-section-anchor map from the topic and food indexes.
def norm(t):
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)      # unwrap existing links
    t = re.sub(r"[*`]", "", t)
    t = re.sub(r"\([^)]*\)", "", t)                       # drop parentheticals
    t = re.sub(r"[^\w\s]", " ", t.lower())
    return re.sub(r"\s+", " ", t).strip()

topic_of = {}
a_start = doc.index("## Appendix A: Topic index")
a_end = doc.index("## Appendix C: The five places")
cur_anchor = None
for line in doc[a_start:a_end].split("\n"):
    hm = re.match(r"^(#{3,4})\s+(.*)$", line)
    if hm:
        cur_anchor = anchors.get(hm.group(2).strip())
        continue
    if cur_anchor and line.startswith("|"):
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) >= 2 and cells[0].lower() not in ("what", "") and not set(cells[0]) <= set("-: "):
            k = norm(cells[0])
            if len(k) > 2:
                topic_of.setdefault(k, cur_anchor)

ALIAS = {
    "shibuya scramble crossing hachiko statue": "shibuya scramble crossing and hachiko statue",
    "kawaguchiko tenjozan panoramic ropeway": "mt kachi kachi ropeway",
    "kobo ichi temple market to ji": "kobo ichi to ji",
    "togetsukyo bridge riverside": "togetsukyo bridge and riverside",
    "higashiyama lanes": "sannenzaka and ninenzaka",
    "nishijin textile center hands on weaving kimono show": "nishijin hand loom weaving",
    "kimono rental for the day": "kimono rental worn for the day",
    "peace memorial park atomic bomb dome": "peace memorial park and the atomic bomb dome exterior",
    "atomic bomb dome riverside": "atomic bomb dome exterior",
}

def lookup(name):
    """Match a day's activity name to a topic section, tolerating name variants."""
    k = norm(name)
    if k in topic_of:
        return topic_of[k]
    if k in ALIAS and ALIAS[k] in topic_of:
        return topic_of[ALIAS[k]]
    # try the leading fragment before a separator: "Shukkei-en garden", "Senso-ji + Nakamise-dori"
    for sep in (" + ", " - ", ": ", ", ", " ("):
        if sep.strip() and sep in name:
            frag = norm(name.split(sep)[0])
            if frag in topic_of:
                return topic_of[frag]
    # an index entry that is a prefix of this name, longest first
    cands = [key for key in topic_of if k.startswith(key + " ") or key.startswith(k + " ")]
    if cands:
        return topic_of[max(cands, key=len)]
    # an index entry wholly contained in this name, longest first
    cands = [key for key in topic_of if len(key) > 6 and key in k]
    if cands:
        return topic_of[max(cands, key=len)]
    return None

# Apply to every Activities table in Part II.
ACT_HDR = "| Activity | Duration | Adult (¥) | Party (¥) | Location | Details |"
out_lines, in_act = [], False
p2_start = re.search(r"^# Days 1-10\b", doc, re.M).start()
p2_end = doc.index("# Appendices")
head, mid, tail = doc[:p2_start], doc[p2_start:p2_end], doc[p2_end:]
linked = 0
for line in mid.split("\n"):
    if line.strip() == ACT_HDR:
        in_act = True; out_lines.append(line); continue
    if in_act:
        if not line.startswith("|"):
            in_act = False; out_lines.append(line); continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if set(cells[0]) <= set("-: ") or "](#" in cells[0]:
            out_lines.append(line); continue
        a = lookup(cells[0])
        if a:
            cells[0] = f"[{cells[0]}](#{a})"
            linked += 1
            out_lines.append("| " + " | ".join(cells) + " |"); continue
    out_lines.append(line)
doc = head + "\n".join(out_lines) + tail
print(f"activity rows linked to topic sections: {linked}")

start = doc.index("## Appendix A: Topic index")
end = doc.index("## Appendix C: The five places")
section = re.sub(r"(\|\s)([\d,\s/]+?)(\s\|)", link_day_cell, doc[start:end])
doc = doc[:start] + section + doc[end:]

# Link each schedule row's Type cell to that day's own Meals, Transport or
# Activities table. Markdown anchors headings rather than table rows, so a row
# link lands on the right table for the right day, not on the individual line.
TYPE_SECTION = {"Food": "Meals", "Transit": "Transport", "Activity": "Activities"}
SCH_HDR = "| Time | Duration | Type | Item |"
sc_start = re.search(r"^# Days 1-10\b", doc, re.M).start()
sc_end = doc.index("# Appendices")
sseg = doc[sc_start:sc_end]
type_links = 0
out5, in_sch, cur_day = [], False, None
for line in sseg.split("\n"):
    dm = re.match(r"^##\s+Day\s+(\d+)\s*[-–]", line)
    if dm:
        cur_day = int(dm.group(1))
    if line.strip() == SCH_HDR:
        in_sch = True; out5.append(line); continue
    if in_sch:
        if not line.startswith("|"):
            in_sch = False; out5.append(line); continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 4 or set(cells[2]) <= set("-: ") or "](#" in cells[2]:
            out5.append(line); continue
        sec = TYPE_SECTION.get(cells[2])
        a = day_sections.get(cur_day, {}).get(sec) if sec else None
        if a:
            cells[2] = f"[{cells[2]}](#{a})"
            type_links += 1
            out5.append("| " + " | ".join(cells) + " |"); continue
    out5.append(line)
doc = doc[:sc_start] + "\n".join(out5) + doc[sc_end:]
print(f"schedule Type cells linked to their day's tables: {type_links}")

# Link each day's Transport modes to the transport appendix, and the appendix back.
MODE_SECTION = [
    ("area pass", "1. The rail pass decision"),
    ("jr ticket office", "1. The rail pass decision"),
    ("shinkansen", "2. The five intercity moves"),
    ("liner", "2. The five intercity moves"),
    ("highway bus", "2. The five intercity moves"),
    ("keisei", "3. Airport transfers"),
    ("nankai", "3. Airport transfers"),
    ("haruka", "3. Airport transfers"),
    ("tokyo metro", "Getting around Tokyo"), ("toei", "Getting around Tokyo"), ("yurikamome", "Getting around Tokyo"),
    ("yamanote", "Getting around Tokyo"), ("keihin-tohoku", "Getting around Tokyo"), ("ueno tokyo line", "Getting around Tokyo"),
    ("tokyo cruise", "Getting around Tokyo"), ("enoden", "Getting around Tokyo"), ("odakyu", "Getting around Tokyo"),
    ("green line", "Getting around Kawaguchiko"), ("red line", "Getting around Kawaguchiko"),
    ("blue line", "Getting around Kawaguchiko"), ("fujikyu railway", "Getting around Kawaguchiko"),
    ("kyoto city bus", "Getting around Kyoto"), ("hankyu", "Getting around Kyoto"), ("keihan", "Getting around Kyoto"),
    ("kintetsu", "Getting around Kyoto"), ("nara line", "Getting around Kyoto"), ("karasuma", "Getting around Kyoto"),
    ("tozai", "Getting around Kyoto"), ("sagano", "Getting around Kyoto"), ("randen", "Getting around Kyoto"),
    ("hiroden", "Getting around Hiroshima"), ("miyajima ferry", "Getting around Hiroshima"), ("jr sanyo", "Getting around Hiroshima"),
    ("osaka metro", "Getting around Osaka"), ("osaka loop", "Getting around Osaka"), ("midosuji line", "Getting around Osaka"),
]
tp_start = re.search(r"^# Days 1-10\b", doc, re.M).start()
tp_end = doc.index("# Appendices")
tseg = doc[tp_start:tp_end]
TR_HDR = "| Leg | Mode | Duration | Adult fare (¥) | Party cost (¥) |"
mode_links = 0
out3, in_tr = [], False
for line in tseg.split("\n"):
    if line.strip() == TR_HDR:
        in_tr = True; out3.append(line); continue
    if in_tr:
        if not line.startswith("|"):
            in_tr = False; out3.append(line); continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2 or set(cells[1]) <= set("-: ") or "](#" in cells[1]:
            out3.append(line); continue
        low = cells[1].lower()
        for kw, sec in MODE_SECTION:
            if kw in low and anchors.get(sec):
                cells[1] = f"[{cells[1]}](#{anchors[sec]})"
                mode_links += 1
                break
        out3.append("| " + " | ".join(cells) + " |"); continue
    out3.append(line)
doc = doc[:tp_start] + "\n".join(out3) + doc[tp_end:]

# Appendix H back to the days: Day columns in its tables, and prose "day N".
h_start = doc.index("## Appendix H: Transport")
h_end = doc.index("## Appendix I:")
hseg = doc[h_start:h_end]
back = 0
out4, daycol = [], None
for line in hseg.split("\n"):
    if line.startswith("|"):
        cells = [c.strip() for c in line.strip("|").split("|")]
        if any(c.lower() == "day" for c in cells):
            daycol = next(i for i, c in enumerate(cells) if c.lower() == "day")
            out4.append(line); continue
        if daycol is not None and daycol < len(cells) and re.fullmatch(r"\d{1,2}", cells[daycol]):
            d = int(cells[daycol])
            if d in day_anchor:
                cells[daycol] = f"[{d}](#{day_anchor[d]})"; back += 1
                out4.append("| " + " | ".join(cells) + " |"); continue
        out4.append(line); continue
    daycol = None
    def prose(m):
        global back
        d = int(m.group(2))
        if d in day_anchor:
            back += 1
            return f"{m.group(1)} [{d}](#{day_anchor[d]})"
        return m.group(0)
    out4.append(re.sub(r"\b([Dd]ay)\s+(\d{1,2})\b(?!\])", prose, line))
doc = doc[:h_start] + "\n".join(out4) + doc[h_end:]
print(f"transport modes linked: {mode_links}; appendix day references linked: {back}")

# Link dish names inside each day's Meals table to their food-index section.
FOOD_KEYWORDS = {
    "Noodles": ["houtou", "yakisoba", "ramen", "udon", "soba"],
    "Rice dishes": ["katsudon", "katsu curry", "gyudon", "shirasu-don", "fried rice", "donburi"],
    "Grilled and skewered": ["yakitori", "kushikatsu", "ika-yaki", "negiyaki", "skewer"],
    "Seafood and sushi": ["kakinoha-zushi", "kaiten-zushi", "nigiri", "sushi", "sashimi"],
    "Hot pot": ["yosenabe", "shabu-shabu", "nabe"],
    "Street snacks": ["menchi-katsu", "nikuman", "takoyaki", "taiyaki", "croquette", "senbei", "crepe"],
    "Sweets and tea": ["mitarashi dango", "momiji manju", "warabimochi", "kudzu-mochi",
                        "wagashi", "matcha", "dango", "hojicha", "mochi"],
    "Regional specialities": ["okonomiyaki", "obanzai", "yudofu", "kaiseki", "kasujiru", "anago-meshi"],
    "Konbini, bento and set meals": ["eki-ben", "onigiri", "teishoku", "karaage", "tonkatsu", "bento"],
}
food_anchor = {sec: anchors.get(sec) for sec in FOOD_KEYWORDS}
# longest keywords first so "mitarashi dango" wins over "dango"
KEYWORDS = sorted(((kw, sec) for sec, kws in FOOD_KEYWORDS.items() for kw in kws),
                  key=lambda kv: -len(kv[0]))

MEAL_HDR = "| Meal | What / Where | Address or store | kcal/adult | Cost (¥) |"
p2s2 = re.search(r"^# Days 1-10\b", doc, re.M).start()
p2e2 = doc.index("# Appendices")
seg2 = doc[p2s2:p2e2]
food_links = 0
out2, in_meals = [], False
for line in seg2.split("\n"):
    if line.strip() == MEAL_HDR:
        in_meals = True; out2.append(line); continue
    if in_meals:
        if not line.startswith("|"):
            in_meals = False; out2.append(line); continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2 or set(cells[0]) <= set("-: "):
            out2.append(line); continue
        cell, used = cells[1], set()
        for kw, sec in KEYWORDS:
            a = food_anchor.get(sec)
            if not a or sec in used:
                continue
            pat = re.compile(r"(?<!\[)\b(" + re.escape(kw) + r")\b(?![^\[]*\]\()", re.I)
            cell, n = pat.subn(lambda m: f"[{m.group(1)}](#{a})", cell, count=1)
            if n:
                used.add(sec); food_links += n
        cells[1] = cell
        out2.append("| " + " | ".join(cells) + " |"); continue
    out2.append(line)
doc = doc[:p2s2] + "\n".join(out2) + doc[p2e2:]
print(f"dish names linked to the food index: {food_links}")

# Link each day's Hotel field to its entry in the hotels appendix.
def link_hotel(m):
    name = m.group(1).rstrip()
    a = anchors.get(name)
    return f"**Hotel:** [{name}](#{a})  " if a else m.group(0)
doc = re.sub(r"^\*\*Hotel:\*\*\s*([^\n]*?)\s*$", link_hotel, doc, flags=re.M)
print("hotel fields linked:", len(re.findall(r"\*\*Hotel:\*\* \[", doc)))

# Link store names in the day schedules to their shopping-run section.
STORE_CITY = {
    "Gyomu Super Ueno-Hirokoji": "Tokyo shopping runs",
    "Gyomu Super Ueno-Koen": "Tokyo shopping runs",
    "LIFE Bioral": "Tokyo shopping runs",
    "OK Store": "Tokyo shopping runs",
    "OGINO Kawaguchiko": "Kawaguchiko shopping runs",
    "Gyomu Super Saiin": "Kyoto shopping runs",
    "Fresco Omiya": "Kyoto shopping runs",
    "ekie": "Hiroshima shopping runs",
    "Life Namba": "Osaka shopping runs",
    "Cocokara Fine Namba": "Osaka shopping runs",
}
shop_links = 0
p2s = re.search(r"^# Days 1-10\b", doc, re.M).start(); p2e = doc.index("# Appendices")
seg = doc[p2s:p2e]
# Prefer the specific dated run for that day over the city section.
run_anchor = {}
for text, a in anchors.items():
    m = re.match(r"^Run.*?-\s*Day\s+(\d+)", text)
    if m:
        run_anchor[int(m.group(1))] = a

out_s, cur_d = [], None
for line in seg.split("\n"):
    dm = re.match(r"^##\s+Day\s+(\d+)\s*[-–]", line)
    if dm:
        cur_d = int(dm.group(1))
    for store, section in sorted(STORE_CITY.items(), key=lambda kv: -len(kv[0])):
        a = run_anchor.get(cur_d) or anchors.get(section)
        if not a:
            continue
        pat = re.compile(r"(?<!\[)\b" + re.escape(store) + r"\b(?![^\[]*\]\()")
        line, n = pat.subn(f"[{store}](#{a})", line)
        shop_links += n
    out_s.append(line)
doc = doc[:p2s] + "\n".join(out_s) + doc[p2e:]
print(f"store names linked to shopping runs: {shop_links}")

# Render bare website URLs in the index tables as compact domain labels.
def shorten_url(m):
    url = m.group(1)
    host = re.sub(r"^https?://(www\.)?", "", url).split("/")[0]
    return f"| [{host}]({url}) |"
doc = re.sub(r"\|\s*(https?://[^\s|]+)\s*\|", shorten_url, doc)
print("website cells rendered as domain links:", len(re.findall(r"\|\s\[[a-z0-9.-]+\]\(https?://", doc)))

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
