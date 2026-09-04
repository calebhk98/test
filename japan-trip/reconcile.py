#!/usr/bin/env python3
"""Recompute running totals across all day files and audit the segment envelopes.

Each writing agent could only see its own segment, so every file's "Running total
after Day N" line starts from a guess. This walks the days in order, recomputes the
cumulative figure from the per-day totals, rewrites those lines in place, and prints
an audit of day totals against the trip budget.
"""
import re, sys, pathlib

FX = 155.0
DAYS_DIR = pathlib.Path("/home/user/test/japan-trip/days")
ORDER = [
    "days-01-10-tokyo.md",
    "days-11-14-fuji-transfer.md",
    "days-15-19-kyoto-a.md",
    "days-20-23-kyoto-b.md",
    "days-24-27-hiroshima.md",
    "days-28-30-osaka.md",
]

DAY_HDR   = re.compile(r"^##\s+Day\s+(\d+)\b", re.M)  # matches "## Day 11 - ..." and "## Day 11 — ..."
DAY_TOTAL = re.compile(r"^\|\s*\*{0,2}Day total\*{0,2}\s*\|\s*\*{0,2}\s*¥?([\d,]+)\s*\*{0,2}\s*\|", re.M)
RUNNING   = re.compile(r"^\*\*Running total after Day (\d+):.*$", re.M)

def parse(path):
    """Return [(day_number, day_total_yen)] in file order."""
    text = path.read_text()
    marks = [(m.start(), int(m.group(1)), "hdr") for m in DAY_HDR.finditer(text)]
    marks += [(m.start(), int(m.group(1).replace(",", "")), "tot") for m in DAY_TOTAL.finditer(text)]
    marks.sort()
    out, cur = [], None
    for _, val, kind in marks:
        if kind == "hdr":
            cur = val
        elif cur is not None:
            out.append((cur, val))
            cur = None
    return out

def main():
    missing = [f for f in ORDER if not (DAYS_DIR / f).exists()]
    if missing:
        print("MISSING FILES:", ", ".join(missing)); return 1

    ledger, running = [], 0
    for fname in ORDER:
        for day, total in parse(DAYS_DIR / fname):
            running += total
            ledger.append((day, total, running, fname))

    days = [d for d, _, _, _ in ledger]
    if days != list(range(1, 31)):
        print("DAY SEQUENCE PROBLEM. Got %d days: %s" % (len(days), days))
        gaps = sorted(set(range(1, 31)) - set(days))
        dupes = sorted({d for d in days if days.count(d) > 1})
        if gaps:  print("  missing days:", gaps)
        if dupes: print("  duplicated days:", dupes)

    # Rewrite the running-total lines in place.
    by_day = {d: r for d, _, r, _ in ledger}
    for fname in ORDER:
        p = DAYS_DIR / fname
        text = p.read_text()
        def fix(m):
            d = int(m.group(1))
            r = by_day.get(d)
            if r is None:
                return m.group(0)
            return "**Running total after Day %d: ¥%s ($%s)**" % (d, f"{r:,}", f"{round(r/FX):,}")
        p.write_text(RUNNING.sub(fix, text))

    print(f"{'Day':>4} {'Yen':>10} {'USD':>7} {'Cumul yen':>12} {'Cumul USD':>10}")
    for d, t, r, _ in ledger:
        print(f"{d:>4} {t:>10,} {round(t/FX):>7,} {r:>12,} {round(r/FX):>10,}")

    print(f"\nPlanned day-line total: ¥{running:,} (${round(running/FX):,})")
    trip_level = 68_000 + 38_000          # baby consumables + misc
    grand = running + trip_level
    print(f"Trip-level lines:       ¥{trip_level:,} (${round(trip_level/FX):,})")
    print(f"Subtotal:               ¥{grand:,} (${round(grand/FX):,})")
    print(f"Budget:                 ¥1,400,000 ($9,032)")
    print(f"Contingency left:       ¥{1_400_000-grand:,} (${round((1_400_000-grand)/FX):,})")
    print(f"Per adult:              ${round(grand/FX/3):,}")
    print(f"Per adult per day:      ${grand/FX/3/30:.2f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
