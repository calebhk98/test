#!/usr/bin/env python3
"""Absolute statements, counted and benchmarked against the reference corpus.

Two things are measured, and the second matters more than the first.

**Rate.** How often the prose reaches for never / always / nobody / everything.
Every novel uses these; the question is whether this one leans on them harder
than twenty-three published books do.

**The flat absolute with an exception behind it.** The defect pattern found by
hand in this manuscript: a sentence states something universal, and within the
next few sentences the text supplies a case it does not cover.

    "Nobody has ever sent Chloe anything."  ... then a letter arrives for her.
    "She tells him everything."             ... then she declines to say what
                                                one project was about.

The absolute reads as authorial fact rather than as a character's belief, so
the exception lands as a contradiction instead of as a turn. Where the turn is
deliberate the fix is usually to soften the absolute, not to drop the
exception.

    python3 absolutes.py                  the manuscript, chapter by chapter
    python3 absolutes.py --corpus DIR...  rebuild the corpus benchmark
"""

import argparse
import importlib.util
import json
import re
import statistics as st
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("pg", HERE / "prose_grade.py")
pg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pg)

REF = HERE / "absolutes_reference.json"

# Strong universals only. "all" and "every" on their own are far too common in
# ordinary prose to separate signal from noise, so they count only in the
# constructions that actually assert a universal.
ABSOLUTE = re.compile(r"""
    \b(?:
        never | always | nobody | no\s+one | nothing | not\s+once | not\s+ever
      | everything | everyone | everybody | none\s+of
      | without\s+exception | invariably | in\s+every\s+case
      | every\s+(?:time|single) | each\s+time
      | the\s+only\s+(?:one|thing|time|person|way)
    )\b
""", re.I | re.X)

# Dialogue is excluded. People speak in absolutes constantly and it is
# characterisation, not error: "everyone hates it", "you never listen". The
# defect is the narrator asserting a universal as fact and the text then
# supplying a case it does not cover, which is why both of the instances found
# by hand are narration:
#     "Nobody has ever sent Chloe anything."
#     "She tells him everything."
QUOTED = re.compile(r'"[^"]*"')


def denarrate(text):
    """Drop everything inside quotation marks."""
    return QUOTED.sub(" ", text)


# What an exception looks like arriving behind one.
EXCEPTION = re.compile(r"""
    \b(?:
        except | apart\s+from | other\s+than | aside\s+from | save\s+for
      | with\s+the\s+exception | but\s+for\s+the
      | the\s+one\s+(?:time|thing|exception|person)
      | the\s+first\s+time\s+(?:she|he|they|it)
    )\b
""", re.I | re.X)

WINDOW = 3   # sentences after the absolute in which an exception counts


def measure(text, side="narration"):
    text, _ = pg.strip_transcript(text)
    text = denarrate(text) if side == "narration" else " ".join(
        m.group(0).strip('"') for m in QUOTED.finditer(text))
    paras = [p for p in pg.paragraphs(text) if p.strip() != "---"]
    ss = [s for p in paras for s in pg.sents(p) if pg.words(s)]
    if len(ss) < 10:
        return None if side == "narration" else {
            "words": len(pg.words(text)), "sentences": len(ss),
            "absolutes": 0, "per1000": 0.0, "share": 0.0,
            "pairs": [], "lines": []}
    n_w = len(pg.words(text))
    hits = [i for i, s in enumerate(ss) if ABSOLUTE.search(s)]
    pairs = []
    for i in hits:
        for j in range(i + 1, min(i + 1 + WINDOW, len(ss))):
            if EXCEPTION.search(ss[j]):
                pairs.append((ss[i], ss[j]))
                break
    return {
        "words": n_w,
        "sentences": len(ss),
        "absolutes": len(hits),
        "per1000": 1000 * len(hits) / n_w,
        "share": 100 * len(hits) / len(ss),
        "pairs": pairs,
        "lines": [ss[i] for i in hits],
    }


def build(dirs):
    out = {}
    for d in dirs:
        for f in sorted(Path(d).rglob("*.txt")):
            if "stripped" in f.stem:
                continue
            t = f.read_text(encoding="utf-8", errors="replace")
            t = pg.strip_gutenberg(t) if hasattr(pg, "strip_gutenberg") else t
            m = measure(t)
            if m:
                out[f.stem] = {k: m[k] for k in ("per1000", "share", "words")}
                out[f.stem]["pairs"] = len(m["pairs"])
                sp = measure(t, side="spoken")
                out[f.stem]["spoken_per1000"] = sp["per1000"] if sp else 0.0
                print(f"  {f.stem:<36}{m['per1000']:6.2f} per 1000")
    REF.write_text(json.dumps(out, indent=1, sort_keys=True), encoding="utf-8")
    print(f"\nwrote {len(out)} books to {REF.name}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", nargs="*")
    ap.add_argument("--pairs", action="store_true",
                    help="print every absolute-then-exception pair in full")
    ap.add_argument("--list", metavar="CHAPTER",
                    help="print every narration absolute in one chapter")
    a = ap.parse_args()
    if a.corpus:
        return build(a.corpus)

    if a.list:
        m = measure(Path(a.list).read_text(encoding="utf-8"))
        for line in m["lines"]:
            print("  " + line.strip()[:300])
        print(f"\n  {len(m['lines'])} narration absolutes in {Path(a.list).stem}")
        return

    ref = json.loads(REF.read_text()) if REF.exists() else {}
    rates = sorted(v["per1000"] for v in ref.values())
    shares = sorted(v["share"] for v in ref.values())

    print(f"\n{'chapter':<24}{'words':>7}{'absolutes':>11}{'per 1000':>10}"
          f"{'% of sents':>12}{'exceptions':>12}")
    print("-" * 76)
    tot_a = tot_w = tot_p = 0
    all_pairs = []
    for p in sorted((HERE / "chapters").glob("*.md")):
        m = measure(p.read_text(encoding="utf-8"))
        if not m:
            continue
        tot_a += m["absolutes"]; tot_w += m["words"]; tot_p += len(m["pairs"])
        all_pairs += [(p.stem, x, y) for x, y in m["pairs"]]
        flag = "  <--" if rates and m["per1000"] > max(rates) else ""
        print(f"{p.stem:<24}{m['words']:>7}{m['absolutes']:>11}"
              f"{m['per1000']:>10.2f}{m['share']:>12.1f}{len(m['pairs']):>12}{flag}")

    book = 1000 * tot_a / tot_w if tot_w else 0
    print("-" * 76)
    print(f"{'BOOK':<24}{tot_w:>7}{tot_a:>11}{book:>10.2f}{'':>12}{tot_p:>12}")
    if rates:
        pct = 100 * sum(1 for r in rates if r < book) / len(rates)
        print(f"\n  corpus of {len(rates)} books:  low {min(rates):.2f}   "
              f"median {st.median(rates):.2f}   high {max(rates):.2f}")
        print(f"  this book {book:.2f} per 1000 words, "
              f"at the {pct:.0f}th percentile of the corpus")
        cp = sorted(v["pairs"] / (v["words"] / 1000) for v in ref.values())
        bp = 1000 * tot_p / tot_w
        print(f"\n  absolute followed within {WINDOW} sentences by an exception:")
        print(f"  corpus  low {min(cp):.3f}   median {st.median(cp):.3f}   "
              f"high {max(cp):.3f}   per 1000 words")
        print(f"  this book {bp:.3f}")

    sw = sa = 0
    for p in sorted((HERE / "chapters").glob("*.md")):
        sp = measure(p.read_text(encoding="utf-8"), side="spoken")
        if sp:
            sw += sp["words"]; sa += sp["absolutes"]
    if sw and ref:
        srates = sorted(v.get("spoken_per1000", 0) for v in ref.values())
        srates = [r for r in srates if r]
        bs = 1000 * sa / sw
        spct = 100 * sum(1 for r in srates if r < bs) / len(srates)
        print(f"\n  inside dialogue, where a character asserting a universal is")
        print(f"  characterisation rather than authorial fact:")
        print(f"  corpus  low {min(srates):.2f}   median {st.median(srates):.2f}   "
              f"high {max(srates):.2f}   per 1000 spoken words")
        print(f"  this book {bs:.2f}, at the {spct:.0f}th percentile")

    if a.pairs and all_pairs:
        print(f"\n{'=' * 76}\nEVERY ABSOLUTE WITH AN EXCEPTION BEHIND IT\n{'=' * 76}")
        for stem, x, y in all_pairs:
            print(f"\n{stem}")
            print(f"  absolute : {x.strip()[:300]}")
            print(f"  exception: {y.strip()[:300]}")
    elif all_pairs:
        print(f"\n  {len(all_pairs)} pairs found. Run with --pairs to read them.")


if __name__ == "__main__":
    main()
