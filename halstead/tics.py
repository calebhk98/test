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

# The target is a reasonable rate, not corpus parity. The corpus is 23 books and
# a voice is made of repetition; the author's instruction is to cut roughly to a
# third of the current rate on the worst offenders and stop there. Several of
# these will still sit far above every reference book afterwards, on purpose.
# Every number word from one to fifteen sits above the highest-numbered book in
# the corpus, so this is a habit of precision rather than three unlucky numbers.
# The target for each is that corpus maximum: no more numerous than the most
# number-heavy of twenty-three published novels. Substituting one number for
# another does not help and only moves the problem, so the fix is to delete the
# precision wherever it is not doing work.
NUMBER_TARGET = {
    "one": 515.7, "two": 282.1, "three": 172.7, "four": 119.3, "five": 112.4,
    "six": 57.3, "seven": 45.9, "eight": 45.9, "nine": 31.2, "ten": 73.4,
    "eleven": 10.3, "twelve": 18.9, "thirteen": 9.7, "fourteen": 11.3,
    "fifteen": 14.5, "forty": 30.0,
}
TARGETS = {
    "habit stated for the reader": 0.0,

    "the word 'same'": 125.0,
    "sentence opens She/He + verb": 120.0,


    "the word 'flat'": 35.0,

    "'the way you/she would'": 20.0,
    "hedged exact (about N)": 18.0,
    "eyes on / eyes down": 12.0,
    "hand(s) flat": 10.0,
    "'the whole/rest of it'": 10.0,
    "turning an object": 6.0,
    "announced withholding": 3.0,
    "'that's not X, that's Y'": 2.0,
}

PATTERNS = {
    # The author, on "He says it the way he says everything": this is done
    # constantly, for different people for different actions, and it is talking
    # to the reader. It tells you an action is characteristic instead of letting
    # the repetition do it. Target 0: there is no good instance of it.
    "habit stated for the reader":
        r"\b(?:the way|as)\s+(?:he|she|they)\s+"
        r"(?:(?:always|normally|usually|invariably|generally)\s+\w+"
        r"|(?:says?|said|does?|did|answers?|handles?|takes?|reads?)\s+"
        r"(?:everything|anything|it all|all of it|every\s+\w+|each\s+\w+)"
        r"|does\s+with\b)",

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

# Every pattern is matched case-insensitively except the sentence-opening one,
# which needs the capital to find a sentence start. Without this the counter
# silently missed every instance that began a sentence: the "that's not X,
# that's Y" row read six book-wide when the true figure was nine.
CASE_SENSITIVE = {"sentence opens She/He + verb"}

for _n, _t in NUMBER_TARGET.items():
    PATTERNS[f"number: {_n}"] = r"\b" + _n + r"\b"
    TARGETS[f"number: {_n}"] = _t


def measure(text):
    n = len(words(text))
    out = {}
    for k, p in PATTERNS.items():
        flags = re.M if k in CASE_SENSITIVE else re.M | re.I
        out[k] = 100000 * len(re.findall(p, text, flags)) / n
    return out, n

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--show")
    a = ap.parse_args()

    book = "\n".join(Path(f).read_text() for f in sorted(glob.glob(str(HERE/"chapters"/"*.md"))))
    if a.show:
        pat = PATTERNS.get(a.show) or a.show
        flags = 0 if a.show in CASE_SENSITIVE else re.I
        for f in sorted(glob.glob(str(HERE/"chapters"/"*.md"))):
            for i, line in enumerate(Path(f).read_text().split("\n"), 1):
                for m in re.finditer(pat, line, flags):
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
    print(f"  {'construction':<32}{'book':>8}{'target':>9}{'corpus med':>12}{'corpus max':>12}{'':>3}")
    print("  " + "-"*78)
    rows, over = [], 0
    for k in PATTERNS:
        vals = sorted(r[k] for r in ref)
        med, mx = st.median(vals), max(vals)
        t = TARGETS.get(k)
        excess = bk[k]/t if t else 0
        rows.append((excess, k, bk[k], t, med, mx))
    for excess, k, b, t, med, mx in sorted(rows, reverse=True):
        if t is None:
            print(f"  {k:<32}{b:>8.1f}{'-':>9}{med:>12.1f}{mx:>12.1f}")
            continue
        ok = b <= t
        over += 0 if ok else 1
        print(f"  {k:<32}{b:>8.1f}{t:>9.1f}{med:>12.1f}{mx:>12.1f}"
              f"{'  pass' if ok else '  CUT ' + f'{100*(1-t/b):.0f}%'}")
    print(f"\n  {over} of {len(TARGETS)} still over target.")
    print("  The target is a reasonable rate, not the corpus. Several of these stay")
    print("  above every reference book after the cut, which is intended: a voice is")
    print("  made of repetition and the corpus is only twenty-three books.")

if __name__ == "__main__":
    main()
