#!/usr/bin/env python3
"""Count the repeated constructions outside readers flagged, against the corpus.

Reviewers reported a set of habits by feel. Most of them are countable, and a
count settles whether a habit is a voice or a tic. Rates are per 100,000 words
so the book and a 70,000-word novel compare directly.

    python3 tics.py                 the manuscript against the corpus
    python3 tics.py --show PATTERN  print every hit for one pattern
"""
import argparse, glob, json, re, statistics as st
from pathlib import Path

HERE = Path(__file__).resolve().parent
CORPUS = [
    "/tmp/claude-0/-home-user-test/e98b5ab4-e37f-5614-9ff3-15e67e5c0180/scratchpad/agent_gutenberg/raw",
    "/tmp/claude-0/-home-user-test/e98b5ab4-e37f-5614-9ff3-15e67e5c0180/scratchpad/agent_modern/texts",
]

PATTERNS = {
    "number: eleven":        r"\beleven\b",
    "number: nine":          r"\bnine\b",
    "number: four":          r"\bfour\b",
    "number: forty":         r"\bforty\b",
    "hedged exact (about N)": r"\babout (?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|twenty|thirty|forty|fifty|a hundred)\b",
    "hand(s) flat":          r"\bhands? (?:flat|pressed flat)\b|\bflat on the (?:table|counter|desk|bench|wall|floor)\b",
    "the word 'flat'":       r"\bflat(?:ly)?\b",
    "'the way you/she would'": r"\bthe way (?:you|she|he|they|somebody|a person|anybody)\b",
    "announced withholding": r"\bkeeps? (?:it|that|the rest of it|them) to (?:him|her|them)sel(?:f|ves)\b|\bkept (?:it|that) to (?:him|her)self\b",
    "'that's not X, that's Y'": r"\b(?:that|this|it)'s not [^.,;!?]{1,40}, (?:that|it)'s\b",
    "'the whole/rest of it'": r"\bthe (?:whole|rest|entire) of it\b",
    "the word 'same'":       r"\bsame\b",
    "'though' at clause end": r",\s+though\b",
    "'except' as connector": r",\s+except\b",
    "turning an object":     r"\bturn(?:s|ing|ed)? (?:it|the \w+) over\b",
    "eyes on / eyes down":   r"\beyes (?:on|down|still on)\b|\bnot looking up\b",
    "sentence opens She/He + verb": r"(?:^|(?<=[.!?]\s))(?:She|He) [a-z]+s\b",
}

def words(t): return re.findall(r"[A-Za-z']+", t)

def strip_gut(t):
    m = re.search(r"\*\*\* ?START OF.*?\*\*\*(.*?)\*\*\* ?END OF", t, re.S)
    return m.group(1) if m else t

def measure(text):
    n = len(words(text))
    return {k: 100000 * len(re.findall(p, text, re.M)) / n for k, p in PATTERNS.items()}, n

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--show")
    a = ap.parse_args()

    book = "\n".join(Path(f).read_text() for f in sorted(glob.glob(str(HERE/"chapters"/"*.md"))))
    if a.show:
        pat = PATTERNS.get(a.show) or a.show
        for f in sorted(glob.glob(str(HERE/"chapters"/"*.md"))):
            for i, line in enumerate(Path(f).read_text().split("\n"), 1):
                for m in re.finditer(pat, line):
                    s = max(0, m.start()-60)
                    print(f"{Path(f).stem}:{i}  ...{line[s:m.end()+60]}...")
        return

    bk, bn = measure(book)
    ref = []
    for d in CORPUS:
        for f in sorted(Path(d).rglob("*.txt")):
            if "stripped" in f.stem: continue
            r, n = measure(strip_gut(f.read_text(encoding="utf-8", errors="replace")))
            if n > 20000: ref.append(r)

    print(f"\n{len(ref)} reference books. Rates per 100,000 words.\n")
    print(f"  {'construction':<34}{'book':>9}{'corpus med':>12}{'corpus max':>12}{'':>4}")
    print("  " + "-"*74)
    rows = []
    for k in PATTERNS:
        vals = sorted(r[k] for r in ref)
        med, mx = st.median(vals), max(vals)
        ratio = bk[k]/med if med else float("inf")
        rows.append((ratio, k, bk[k], med, mx))
    for ratio, k, b, med, mx in sorted(rows, reverse=True):
        flag = "  <-- above every book" if b > mx else ("  <-- 2x+ median" if ratio >= 2 else "")
        print(f"  {k:<34}{b:>9.1f}{med:>12.1f}{mx:>12.1f}{flag}")
    print("\n  A high rate is not automatically a defect; a voice is made of repetition.")
    print("  Above every book in the corpus is the line worth looking at.")

if __name__ == "__main__":
    main()
