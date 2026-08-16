#!/usr/bin/env python3
"""Measure how distinguishable each character's dialogue is from the others'.

The swap test - would anyone notice if this line moved to another character? -
is a judgement call. This is the measurable version: extract each character's
lines, compute the same statistics for each speaker, and show how far apart
they sit. Characters whose numbers coincide have no voice yet.

    python3 voice_separation.py            # both channels
    python3 voice_separation.py --chat     # group chat only
    python3 voice_separation.py --prose    # tagged prose dialogue only

Two channels, measured separately because they are attributable with very
different confidence.

CHAT is exact. Messages are "name: text", so every line has a known speaker
and none are missed.

PROSE IS A BIASED SAMPLE and its numbers must be read with that in mind. Only
lines carrying an explicit "<name> says" tag can be attributed, and the book
drops the tag once a two-hander is established, which is the style guide's own
advice. Tagged lines therefore skew towards the openings of exchanges, which
run short. Treat the prose figures as comparable BETWEEN characters, since the
bias hits every character alike, and not as an estimate of that character's
true average line length.
"""

import argparse
import collections
import re
import statistics as st
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHAT_FILES = ["CHAPTERS_16_22_v2.md", "CHAPTERS_23_30_v2.md"]
CAST = ["chloe", "ruth", "sam", "kavi", "nadia", "eli", "theo"]
TAGGED = r"(Chloe|Ruth|Sam|Kavi|Nadia|Eli|Theo|Odile|her mom|her mother|her dad|her father)"
SAYS = r"(?:says|said|asks|asked|tells|told|shouts|screams|whispers)"
HEDGE = r"\b(i think|maybe|probably|idk|i dont know|i don't know|kind of|sort of|i guess)\b"


def words(t):
    return re.findall(r"[A-Za-z][A-Za-z']*", t)


def normalise(t):
    return t.replace('“', '"').replace('”', '"')


def collect_chat(root):
    out = collections.defaultdict(list)
    for name in CHAT_FILES:
        f = root / name
        if not f.is_file():
            continue
        for line in f.read_text(encoding="utf-8").split("\n"):
            m = re.match(r"^\s*(%s):\s*(.+)$" % "|".join(CAST), line.strip(), re.I)
            if m:
                out[m.group(1).lower()].append(m.group(2).strip())
    return out


def collect_prose(root):
    """Lines with an explicit speaker tag. See the module docstring on bias."""
    out = collections.defaultdict(list)
    files = sorted((root / "chapters").glob("*.md")) + [root / n for n in CHAT_FILES]
    patterns = [
        (rf'"([^"]+)"[,]?\s+{TAGGED}\s+{SAYS}', 0, 1),
        (rf'"([^"]+)"[,]?\s+{SAYS}\s+{TAGGED}', 0, 1),
        (rf'{TAGGED}\s+{SAYS}[,:]?\s+"([^"]+)"', 1, 0),
    ]
    for f in files:
        if not f.is_file():
            continue
        for line in normalise(f.read_text(encoding="utf-8")).split("\n"):
            for pat, ti, wi in patterns:
                for m in re.finditer(pat, line):
                    g = m.groups()
                    who = g[wi].lower().replace("her ", "")
                    who = {"mother": "mom", "father": "dad"}.get(who, who)
                    out[who].append(g[ti])
    return out


def profile(lines):
    tokens = [words(x) for x in lines]
    flat = [w.lower() for t in tokens for w in t]
    if not flat:
        return None
    return {
        "n": len(lines),
        "words": len(flat),
        "wpl": len(flat) / len(lines),
        "ttr": 100 * len(set(flat)) / len(flat),
        "q": 100 * sum(1 for x in lines if "?" in x) / len(lines),
        "short": 100 * sum(1 for t in tokens if len(t) <= 3) / len(lines),
        "long": 100 * sum(1 for t in tokens if len(t) > 15) / len(lines),
        "hedge": 100 * sum(1 for x in lines if re.search(HEDGE, x, re.I)) / len(lines),
    }


def show(title, data, floor, note):
    rows = {k: p for k, v in data.items() if (p := profile(v)) and p["n"] >= floor}
    if not rows:
        print(f"\n{title}: nothing with at least {floor} lines")
        return
    print(f"\n{title}   ({note})")
    print(f"  {'speaker':10}{'lines':>7}{'words':>7}{'w/line':>8}{'TTR%':>7}"
          f"{'quest%':>8}{'1-3w%':>7}{'>15w%':>7}{'hedge%':>8}")
    for k, p in sorted(rows.items(), key=lambda kv: -kv[1]["wpl"]):
        print(f"  {k:10}{p['n']:>7}{p['words']:>7}{p['wpl']:>8.1f}{p['ttr']:>7.1f}"
              f"{p['q']:>8.0f}{p['short']:>7.0f}{p['long']:>7.0f}{p['hedge']:>8.0f}")
    for key, label in (("wpl", "words per line"), ("short", "1-3 word share")):
        vals = [p[key] for p in rows.values()]
        lo, hi = min(vals), max(vals)
        spread = (hi - lo) / st.fmean(vals)
        print(f"  {label:16} {lo:.1f} to {hi:.1f}   "
              f"spread {100 * spread:.0f}% of the mean"
              f"{'   <- speakers barely differ' if spread < 0.5 else ''}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=HERE)
    ap.add_argument("--chat", action="store_true")
    ap.add_argument("--prose", action="store_true")
    ap.add_argument("--min-lines", type=int, default=8)
    a = ap.parse_args()
    both = not (a.chat or a.prose)
    if a.chat or both:
        show("GROUP CHAT", collect_chat(a.root), a.min_lines,
             "exact attribution, every message counted")
    if a.prose or both:
        show("PROSE DIALOGUE", collect_prose(a.root), a.min_lines,
             "tagged lines only, biased short - compare speakers, not absolutes")


if __name__ == "__main__":
    main()
