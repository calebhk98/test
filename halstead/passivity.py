#!/usr/bin/env python3
"""How often a character handles a thing and declines to act on it.

The author, by ear: *"Can we check for how often the characters are passive?
Like they read something, and then put it back down, they choose not to act,
they ignore something, etc."*

This is not the grammatical passive voice and grep for "was -ed" will not find
it. It is a beat: a character is given something to push against and does not
push. The book uses it deliberately and often - Chloe leaving a question alone
is characterisation, and the flat register depends on people not making
speeches. The question a count answers is whether it has stopped being a choice
and become the only move the book knows.

Six shapes, counted separately, because they are not the same beat and the
right number for each is different. Rates per 100,000 words against the same
23 reference books every other script here uses.

    python3 passivity.py                 the manuscript against the corpus
    python3 passivity.py --show SHAPE    print every hit for one shape
"""
import argparse, glob, re, statistics as st
from pathlib import Path

HERE = Path(__file__).resolve().parent
CORPUS = [
    "/tmp/claude-0/-home-user-test/e98b5ab4-e37f-5614-9ff3-15e67e5c0180/scratchpad/agent_gutenberg/raw",
    "/tmp/claude-0/-home-user-test/e98b5ab4-e37f-5614-9ff3-15e67e5c0180/scratchpad/agent_modern/texts",
]

SHAPES = {
    # Handles the object and returns it unchanged.
    "puts it back down":
        r"\b(?:puts?|put|sets?|set|lays?|laid|places?)\s+(?:it|them|the\s+\w+|his\s+\w+|her\s+\w+)"
        r"\s+(?:back\s+)?down\b"
        r"|\b(?:puts?|put|sets?|set)\s+(?:it|them|the\s+\w+)\s+back\b",

    # Declines to pursue the thing in front of them.
    "leaves it / lets it go":
        r"\b(?:leaves?|left)\s+(?:it|that|them|the\s+\w+)\s+(?:there|alone|where|at\s+that|be)\b"
        r"|\blets?\s+(?:it|that|them)\s+(?:go|sit|stand|lie|drop|rest)\b"
        r"|\blet\s+(?:it|that|them)\s+(?:go|sit|stand|lie|drop|rest)\b",

    # Declines to speak.
    "says nothing":
        r"\bsays?\s+nothing\b|\bsaid\s+nothing\b"
        r"|\b(?:does|did|do)(?:n't| not)\s+(?:say|answer|reply|respond)\b"
        r"|\bwithout\s+saying\b|\bsays?\s+none\s+of\s+it\b"
        r"|\bnever\s+says?\s+(?:so|it|anything)\b",

    # Declines to inquire, in a book whose subject is asking.
    "does not ask":
        r"\b(?:does|did|do)(?:n't| not)\s+ask\b|\bnever\s+asks?\b"
        r"|\bwithout\s+asking\b|\bstops?\s+(?:short\s+of\s+)?asking\b",

    # Substitutes a smaller action for the one the scene set up.
    "does X instead":
        r"\binstead\b",

    # Registers the thing and does not act on it.
    "notices and does nothing":
        r"\b(?:notices?|noticed|sees?|saw|reads?|hears?|heard)\b[^.;!?]{0,60}"
        r"\band\s+(?:says?|does|do)(?:n't| not)\b",
}

def words(t): return re.findall(r"[A-Za-z']+", t)

def strip_gut(t):
    m = re.search(r"\*\*\* ?START OF.*?\*\*\*(.*?)\*\*\* ?END OF", t, re.S)
    return m.group(1) if m else t

def measure(text):
    n = len(words(text))
    return {k: 100000 * len(re.findall(p, text, re.I | re.M)) / n
            for k, p in SHAPES.items()}, n

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--show")
    a = ap.parse_args()

    files = sorted(glob.glob(str(HERE / "chapters" / "*.md")))
    if a.show:
        pat = SHAPES.get(a.show) or a.show
        for f in files:
            for i, line in enumerate(Path(f).read_text().split("\n"), 1):
                for m in re.finditer(pat, line, re.I):
                    s = max(0, m.start() - 70)
                    print(f"{Path(f).stem}:{i}  ...{line[s:m.end()+70]}...")
        return

    book = "\n".join(Path(f).read_text() for f in files)
    bk, bn = measure(book)

    ref = []
    for d in CORPUS:
        for f in sorted(Path(d).rglob("*.txt")):
            if "stripped" in f.stem:
                continue
            r, n = measure(strip_gut(f.read_text(encoding="utf-8", errors="replace")))
            if n > 20000:
                ref.append(r)

    print(f"\n{len(ref)} reference books. Rates per 100,000 words.\n")
    print(f"  {'shape':<28}{'book':>8}{'corpus med':>12}{'corpus max':>12}"
          f"{'vs max':>9}")
    print("  " + "-" * 72)
    over = 0
    rows = []
    for k in SHAPES:
        vals = sorted(r[k] for r in ref)
        med, mx = st.median(vals), max(vals)
        rows.append((bk[k] / mx if mx else 99, k, bk[k], med, mx))
    for ratio, k, b, med, mx in sorted(rows, reverse=True):
        flag = ""
        if mx and b > mx:
            flag, over = f"  {ratio:.1f}x", over + 1
        elif mx:
            flag = f"  {ratio:.1f}x"
        print(f"  {k:<28}{b:>8.1f}{med:>12.1f}{mx:>12.1f}{flag:>9}")

    print(f"\n  {over} of {len(SHAPES)} shapes above every reference book.")
    print("  No targets here on purpose. Declining to act is this book's chosen")
    print("  register and a number cannot say how much of it is too much - it can")
    print("  only say which shapes have stopped being unusual. Read the hits with")
    print("  --show before cutting anything.")

if __name__ == "__main__":
    main()
