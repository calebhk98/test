#!/usr/bin/env python3
"""Grade prose maturity against a reference corpus, not against invented targets.

style_report.py checks a chapter against the numbers written into
STYLE_GUIDES.md. Several of those have no source behind them, and some have
floors that reward choppier writing: chapter 8, the most grown-up chapter in
the book, fails there partly for not having ENOUGH short sentences.

This grades differently. Every measure is compared against 23 real books, and
reported as a percentile in that field plus a straight win/loss against one
named book. The default benchmark is Peter Pan, which is below the target
audience, so losing to it on a measure is a clear signal rather than a
judgement call.

    python3 prose_grade.py MANUSCRIPT_FULL.md
    python3 prose_grade.py chapters/*.md --brief
    python3 prose_grade.py draft.md --benchmark treasure_island
    python3 prose_grade.py --list-benchmarks
    python3 prose_grade.py --build-reference DIR1 DIR2   # regenerate the corpus file

Reference data lives in prose_reference.json next to this script.
"""

import argparse
import json
import re
import statistics as st
import sys
from pathlib import Path

from style_report import paragraphs, sents, words

HERE = Path(__file__).resolve().parent
REFERENCE = HERE / "prose_reference.json"

SUBORDINATOR = (r"\b(because|although|though|while|whereas|since|unless|until|after|before"
                r"|if|when|whenever|as|so that|even though|rather than|whether)\b")
RELATIVE = r"\b(who|whom|whose|which|that)\b"

# The 100 commonest English words. A high share of these means a small
# working vocabulary, which is one of the two things that reads young.
TOP100 = set("""the be to of and a in that have i it for not on with he as you do at this
but his by from they we say her she or an will my one all would there their what so up out
if about who get which go me when make can like time no just him know take people into year
your good some could them see other than then now look only come its over think also back
after use two how our work first well way even new want because any these give day most us""".split())

# metric key -> (label, higher_is_more_mature)
METRICS = {
    "fk":        ("reading grade (Flesch-Kincaid)", True),
    "wps":       ("words per sentence", True),
    "sttr":      ("lexical diversity (sTTR)", True),
    "commas":    ("commas per sentence", True),
    "subord":    ("sentences with a subordinate clause %", True),
    "relcl":     ("sentences with a relative clause %", True),
    "b2035":     ("sentences of 20-35 words %", True),
    "long7":     ("words of 7+ characters %", True),
    "u10":       ("sentences under 10 words %", False),
    "simple":    ("sentences with no subordinate/relative clause %", False),
    "shortruns": ("sentences inside a run of 3+ short ones %", False),
    "top100":    ("words from the commonest 100 %", False),
}


def syllables(w):
    w = w.lower()
    n = len(re.findall(r"[aeiouy]+", w))
    if w.endswith("e") and not w.endswith(("le", "ee")) and n > 1:
        n -= 1
    return max(n, 1)


def measure(text):
    """All twelve metrics for one text. Returns None if the text is too short."""
    paras = paragraphs(text)
    sl_all = [(s, len(words(s))) for p in paras for s in sents(p)]
    sl_all = [(s, n) for s, n in sl_all if n]
    if len(sl_all) < 40:
        return None
    ss = [s for s, _ in sl_all]
    sl = [n for _, n in sl_all]
    w = words(text)
    lw = [x.lower() for x in w]
    n_s, n_w = len(sl), len(w)

    runs = inrun = 0
    for v in sl:
        if v < 8:
            runs += 1
        else:
            inrun += runs if runs >= 3 else 0
            runs = 0
    inrun += runs if runs >= 3 else 0

    win = [len(set(lw[i:i + 1000])) / 1000 for i in range(0, len(lw) - 1000, 1000)]
    wps = st.fmean(sl)

    return {
        "fk": 0.39 * wps + 11.8 * (sum(syllables(x) for x in w) / n_w) - 15.59,
        "wps": wps,
        "sttr": 100 * st.fmean(win) if win else 100 * len(set(lw)) / n_w,
        "commas": text.count(",") / n_s,
        "subord": 100 * sum(1 for s in ss if re.search(SUBORDINATOR, s, re.I)) / n_s,
        "relcl": 100 * sum(1 for s in ss if re.search(RELATIVE, s, re.I)) / n_s,
        "b2035": 100 * sum(1 for v in sl if 20 < v <= 35) / n_s,
        "long7": 100 * sum(1 for x in w if len(x) >= 7) / n_w,
        "u10": 100 * sum(1 for v in sl if v < 10) / n_s,
        "simple": 100 * sum(1 for s in ss
                            if not re.search(SUBORDINATOR, s, re.I)
                            and not re.search(RELATIVE, s, re.I)) / n_s,
        "shortruns": 100 * inrun / n_s,
        "top100": 100 * sum(1 for x in lw if x in TOP100) / n_w,
        "_words": n_w,
    }


def strip_gutenberg(t):
    m = re.search(r"\*\*\* ?START OF.*?\*\*\*(.*?)\*\*\* ?END OF", t, re.S)
    return m.group(1) if m else t


def build_reference(dirs, out):
    books = {}
    for d in dirs:
        for f in sorted(Path(d).rglob("*.txt")):
            if "stripped" in f.stem:
                continue
            got = measure(strip_gutenberg(f.read_text(encoding="utf-8", errors="replace")))
            if got:
                books[f.stem] = got
                print(f"  measured {f.stem} ({got['_words']:,} words)")
    out.write_text(json.dumps(books, indent=1, sort_keys=True), encoding="utf-8")
    print(f"\nwrote {len(books)} books to {out}")


def percentile(values, x):
    return 100 * sum(1 for v in values if v < x) / len(values)


def grade(path, ref, benchmark, brief):
    # Strip Gutenberg boilerplate here too, or a reference book graded against
    # itself scores differently from its own stored entry.
    text = strip_gutenberg(Path(path).read_text(encoding="utf-8"))
    got = measure(text)
    if not got:
        print(f"{Path(path).name}: too short to grade (needs 40+ sentences)")
        return None

    bench = ref[benchmark]
    losses, pcts = [], []
    lines = []
    for key, (label, higher) in METRICS.items():
        vals = [b[key] for b in ref.values()]
        p = percentile(vals, got[key])
        if not higher:
            p = 100 - p
        pcts.append(p)
        # >= / <= so a book tied with the benchmark, including the benchmark
        # itself, is not scored as a loss.
        beat = got[key] >= bench[key] if higher else got[key] <= bench[key]
        # Distance from the benchmark in corpus standard deviations, so gaps on
        # measures with different units can be ranked against each other.
        sd = st.stdev(vals)
        gap = (bench[key] - got[key]) / sd * (1 if higher else -1)
        if not beat:
            losses.append((-gap, label, got[key], bench[key], gap))
        lines.append((p, label, got[key], bench[key], beat))

    print("=" * 78)
    print(f"{Path(path).name}  |  {got['_words']:,} words  |  "
          f"benchmark: {benchmark}  |  corpus: {len(ref)} books")
    print(f"\nmaturity percentile (median of 12 measures): {st.median(pcts):.0f}"
          f"      lost to benchmark on {len(losses)} of 12")
    if not brief:
        print(f"\n  {'measure':46}{'this':>8}{'bench':>8}{'pct':>6}")
        for p, label, mine, theirs, beat in sorted(lines):
            print(f"  {label:46}{mine:>8.2f}{theirs:>8.2f}{p:>5.0f}%  "
                  f"{'' if beat else '<-- loses'}")
    if losses:
        print(f"\n  fix first, by size of the gap to {benchmark} "
              f"(in corpus standard deviations):")
        for _, label, mine, theirs, gap in sorted(losses)[:4]:
            print(f"    {label:46}{mine:>8.2f} vs {theirs:>7.2f}   {gap:>4.1f} sd")
    return st.median(pcts), len(losses)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", type=Path)
    ap.add_argument("--benchmark", default="peter_pan")
    ap.add_argument("--reference", type=Path, default=REFERENCE)
    ap.add_argument("--brief", action="store_true", help="summary line per file only")
    ap.add_argument("--list-benchmarks", action="store_true")
    ap.add_argument("--build-reference", nargs="+", metavar="DIR")
    a = ap.parse_args()

    if a.build_reference:
        return build_reference(a.build_reference, a.reference)
    if not a.reference.is_file():
        sys.exit(f"error: no reference corpus at {a.reference}; "
                 f"rebuild with --build-reference DIR")
    ref = json.loads(a.reference.read_text(encoding="utf-8"))

    if a.list_benchmarks:
        print(f"{len(ref)} books in {a.reference.name}, by reading grade:")
        for name in sorted(ref, key=lambda k: ref[k]["fk"]):
            print(f"  {ref[name]['fk']:5.1f}  {name}")
        return
    if not a.paths:
        sys.exit("error: give one or more files to grade")
    if a.benchmark not in ref:
        sys.exit(f"error: no book named {a.benchmark}; try --list-benchmarks")

    results = []
    for p in a.paths:
        got = grade(p, ref, a.benchmark, a.brief)
        if got:
            results.append((p.name, *got))
        print()
    if len(results) > 1:
        print("=" * 78)
        print(f"{'file':30}{'percentile':>12}{'losses/12':>12}")
        for name, pct, lost in sorted(results, key=lambda r: r[1]):
            print(f"{name[:29]:30}{pct:>11.0f}%{lost:>12}")


if __name__ == "__main__":
    main()
