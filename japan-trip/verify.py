#!/usr/bin/env python3
"""Cross-check each day's schedule against its own Meals, Transport and Activities tables.

Three relationships, only one of which should be exact:

- Activity rows in the schedule vs rows in the Activities table: should match, except
  where one scheduled block deliberately covers several priced items, or where a table
  row is a fee with no time of its own. Those exceptions are listed below by name.
- Food rows vs the Meals table: the Meals table always carries an "Infant food" row that
  is not a scheduled block, so Meals is normally one higher, more if a day has a snack.
- Transit rows vs the Transport table: the schedule shows every walk, the Transport table
  only fare-bearing legs, so the schedule is normally higher.
"""
import re, pathlib, sys

D = pathlib.Path(__file__).parent / "days"
ORDER = ["days-01-10-tokyo.md", "days-11-14-fuji-transfer.md", "days-15-19-kyoto-a.md",
         "days-20-23-kyoto-b.md", "days-24-27-hiroshima.md", "days-28-30-osaka.md"]
HDR = re.compile(r"^##\s+Day\s+(\d+)\s*[-–]", re.M)

# One schedule block that legitimately covers more than one Activities row, or an
# Activities row that is a fee rather than a timed stop.
KNOWN = {
    13: "one Oshino Hakkai block covers the free village walk and the paid garden pond",
    16: "two Kyoto Gyoen blocks cover the single Jidai Matsuri viewing entry",
    18: "the lanes are walked up and back down, one Activities row",
    20: "deer are fed on arrival and again before leaving, one senbei row",
    25: "the Miyajima visitor tax is a fee with no time of its own",
    27: "one Dotonbori block covers the canal walk and the Pokemon Centre",
}

# Days where the schedule splits food into buying, cooking and eating blocks, so there
# are more Food rows than there are meals.
KNOWN_FOOD = {
    11: "buying the eki-ben, the OGINO grocery run and cooking are separate blocks from eating",
}

def table_rows(block):
    n, started = 0, False
    for line in block.split("\n"):
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if all(set(c) <= set("-: ") and c for c in cells):
                started = True; continue
            if started: n += 1
        elif started and not line.strip():
            break
    return n

bad = []
print(f"{'Day':>4} | {'Food':>4} {'Meals':>5} | {'Trans':>5} {'Tport':>5} | {'Act':>4} {'Acts':>4}  note")
for f in ORDER:
    t = (D / f).read_text()
    idx = [(m.start(), int(m.group(1))) for m in HDR.finditer(t)] + [(len(t), None)]
    for i in range(len(idx) - 1):
        chunk, day = t[idx[i][0]:idx[i + 1][0]], idx[i][1]
        sm = re.search(r"### Schedule\n(.*?)(?=\n### )", chunk, re.S)
        counts = {"Food": 0, "Transit": 0, "Activity": 0}
        if sm:
            started = False
            for line in sm.group(1).split("\n"):
                if not line.startswith("|"): continue
                c = [x.strip() for x in line.strip("|").split("|")]
                if all(set(x) <= set("-: ") and x for x in c): started = True; continue
                if not started or len(c) < 3: continue
                ty = re.sub(r"\[|\]\(#[^)]*\)", "", c[2])
                if ty in counts: counts[ty] += 1
        def sect(name):
            m = re.search(rf"### {name}\n(.*?)(?=\n### |\Z)", chunk, re.S)
            return table_rows(m.group(1)) if m else 0
        meals, tport, acts = sect("Meals"), sect("Transport"), sect("Activities")
        note = ""
        if counts["Activity"] != acts:
            note = KNOWN.get(day, "** UNEXPLAINED **")
            if day not in KNOWN: bad.append(day)
        if meals and counts["Food"] > meals:
            if day in KNOWN_FOOD:
                note += ("  " if note else "") + KNOWN_FOOD[day]
            else:
                note += "  ** more Food blocks than Meals rows **"; bad.append(day)
        if tport and counts["Transit"] < tport:
            note += "  ** fewer Transit blocks than Transport legs **"; bad.append(day)
        print(f"{day:>4} | {counts['Food']:>4} {meals:>5} | {counts['Transit']:>5} {tport:>5} | "
              f"{counts['Activity']:>4} {acts:>4}  {note}")

print()
if bad:
    print(f"UNEXPLAINED MISMATCHES on days: {sorted(set(bad))}")
    sys.exit(1)
print("All 30 days consistent: every Activities row has schedule time, or a documented reason not to.")
