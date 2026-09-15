#!/usr/bin/env python3
"""Apply the requested layout changes to every day block, deterministically.

1. Header meta split onto its own line each (Base / Weather / Theme).
2. Schedule table columns reordered from Time|Duration|Item|Type to Time|Duration|Type|Item.
3. Lodging block expanded to labelled lines: Night / Hotel / Address / Unit / Nightly.
"""
import re, pathlib

D = pathlib.Path("/home/user/test/japan-trip/days")
FILES = sorted(D.glob("days-*.md"))

def split_header(t):
    # "**Base:** X | **Weather (typical):** Y"  ->  one per line
    return re.sub(r"^(\*\*Base:\*\*[^\n|]*?)\s*\|\s*(\*\*Weather[^\n]*)$",
                  r"\1\n\2", t, flags=re.M)

def reorder_schedule(t):
    """Swap the 3rd and 4th cells of every row in a Time|Duration|Item|Type table."""
    out, in_tbl = [], False
    for line in t.split("\n"):
        s = line.strip()
        is_row = s.startswith("|") and s.endswith("|")
        if is_row:
            cells = [c.strip() for c in s[1:-1].split("|")]
            if len(cells) == 4:
                low = [c.lower() for c in cells]
                if low[0] == "time" and low[1] == "duration" and low[2] == "item" and low[3] == "type":
                    in_tbl = True
                    out.append("| Time | Duration | Type | Item |"); continue
                if in_tbl:
                    if all(set(c) <= set("-: ") and c for c in cells):
                        out.append("|---|---|---|---|"); continue
                    cells[2], cells[3] = cells[3], cells[2]
                    out.append("| " + " | ".join(cells) + " |"); continue
        else:
            in_tbl = False
        out.append(line)
    return "\n".join(out)

LODG = re.compile(
    r"^\*\*(?P<name>[^*\n]+)\*\*\s*[-–]\s*(?P<addr>[^\n]+)\n"
    r"Unit:\s*(?P<unit>.+?)\s*\|\s*Nightly:\s*(?P<rate>[^|\n]+?)\s*\|\s*Night\s*(?P<night>[^\n]+?)\s*$",
    re.M)

def reformat_lodging(t):
    def sub(m):
        return ("**Night:** %s\n**Hotel:** %s\n**Address:** %s\n**Unit:** %s\n**Nightly:** %s"
                % (m.group("night").strip(), m.group("name").strip(),
                   m.group("addr").strip(), m.group("unit").strip(), m.group("rate").strip()))
    return LODG.sub(sub, t)

tot = {"hdr": 0, "sched": 0, "lodg": 0}
for f in FILES:
    t0 = f.read_text()
    t1 = split_header(t0)
    tot["hdr"] += len(re.findall(r"^\*\*Base:\*\*", t1, re.M))
    t2 = reorder_schedule(t1)
    tot["sched"] += t2.count("| Time | Duration | Type | Item |")
    t3 = reformat_lodging(t2)
    tot["lodg"] += t3.count("**Night:**")
    f.write_text(t3)

print("Headers split      :", tot["hdr"], "/ 30")
print("Schedules reordered:", tot["sched"], "/ 30")
print("Lodging blocks      :", tot["lodg"], "/ 30  (Day 30 has no lodging, so 29 expected)")
