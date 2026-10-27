#!/usr/bin/env python3
"""Count the measurable prose habits in drafted chapters.

Usage: python3 prose_metrics.py chapter.md [chapter.md ...]

Reads only the prose: stops at the first line that is exactly "---"
(the drafter-notes divider) and skips markdown headings.
"""
import re
import sys
from collections import Counter

BODY_CLICHES = [
    r"face (went|got|grew) (warm|hot|red)", r"cheeks? (burned|flushed|went warm)",
    r"chest (fluttered|flutter|did|tightened|went tight|turn)", r"heart (flipped|did a|skipped|leapt|lurched|went up)",
    r"stomach (dropped|lurched|rolled|turned|flipped|knotted)", r"face lit up", r"lit up before",
    r"breath caught", r"swallowed hard", r"something (shifted|flickered) in his",
    r"mouth did something", r"smile came out", r"face went (tight|careful|still)",
    r"a beat too long", r"jaw (worked|tightened)",
]
STOCK_PHRASES = [
    r"\bi know\.\"", r"\bwhich was the worst part\b", r"\bmaybe both\b", r"\bnot dramatically\b",
    r"\bfiled (it|that) away\b", r"\btwo years\b", r"\btwelve inches\b",
]
SIMILE = r"\bthe way (you|someone|a |an |people)"


def label(pat):
    """Readable label for a regex: first alternative of each group."""
    lab = re.sub(r"\(([^)|]*)(\|[^)]*)?\)", r"\1", pat)
    return re.sub(r"\\b|\\|\?", "", lab).strip()


def prose(path):
    lines = []
    for line in open(path, encoding="utf-8"):
        if line.strip() == "---":
            break
        if line.lstrip().startswith("#"):
            continue
        lines.append(line.rstrip("\n"))
    return "\n".join(lines)


def sentences(text):
    flat = re.sub(r"\s+", " ", text)
    parts = re.split(r"(?<=[.!?])[\"']?\s+(?=[\"'A-Z*])", flat)
    return [p.strip() for p in parts if re.search(r"[A-Za-z]", p)]


def words(s):
    return re.findall(r"[A-Za-z0-9']+", s)


def report(path):
    text = prose(path)
    sents = sentences(text)
    lens = [len(words(s)) for s in sents]
    n = len(lens) or 1
    short = [l for l in lens if l < 6]
    run, best = 0, 0
    for l in lens:
        run = run + 1 if l < 6 else 0
        best = max(best, run)
    lower = text.lower()
    paras = [p for p in text.split("\n\n") if p.strip()]
    dialogue_paras = sum(1 for p in paras if '"' in p)
    tri = Counter()
    toks = [w.lower() for w in words(text)]
    for i in range(len(toks) - 3):
        tri[" ".join(toks[i:i + 4])] += 1
    common = {"i didn't know", "i don't know", "at the same time", "for the first time", "one of the"}
    repeats = [(k, v) for k, v in tri.most_common(40) if v >= 3 and k not in common][:8]

    print(f"== {path}")
    print(f"words: {sum(lens)}   sentences: {len(lens)}   mean words/sentence: {sum(lens)/n:.1f}")
    print(f"sentences under 6 words: {len(short)} ({100*len(short)/n:.0f}%)   longest run of short sentences: {best}")
    narr = re.sub(r'"[^"]*"', " ", text)
    nl = [len(words(x)) for x in sentences(narr)]
    nn = len(nl) or 1
    print(f"narration only: mean words/sentence {sum(nl)/nn:.1f}, under 6 words {100*sum(1 for l in nl if l < 6)/nn:.0f}%")
    print(f"paragraphs: {len(paras)}   with dialogue: {dialogue_paras}   one-line paragraphs under 6 words: "
          f"{sum(1 for p in paras if len(words(p)) < 6)}")
    print(f"em dashes: {text.count(chr(8212))}   exclamation marks: {text.count('!')}   "
          f"'the way you/someone' similes: {len(re.findall(SIMILE, lower))}")
    hits = [(pat, len(re.findall(pat, lower))) for pat in BODY_CLICHES]
    hits = [h for h in hits if h[1]]
    print("body-language cliches: " + (", ".join(f"{label(p)} x{c}" for p, c in hits) or "none"))
    stock = [(pat, len(re.findall(pat, lower))) for pat in STOCK_PHRASES]
    stock = [h for h in stock if h[1]]
    print("stock phrases: " + (", ".join(f"{label(p)} x{c}" for p, c in stock) or "none"))
    print("repeated 4-word phrases (3+): " + (", ".join(f'"{k}" x{v}' for k, v in repeats) or "none"))
    print()


if __name__ == "__main__":
    for p in sys.argv[1:]:
        report(p)
