#!/usr/bin/env python3
"""How many sentences a character gets to say before the quotation marks close.

The book was written with a strong one-line-per-turn habit, and the habit is
measurable: 82% of its quotations were a single sentence against a corpus
median of 76%, and only 6% ran to three or more against a median of 12%. That
puts it at the clipped end of the corpus, beside Peter Pan and Alice, when the
prose everywhere else is at the other end. Characters should be able to say
"What? No. We can't do that, it hurts us. We should do X instead." in one
breath, and mostly they cannot.

Chat transcripts are excluded: they are lowercase, unpunctuated and follow
their own convention, so counting sentences in them is meaningless.
"""
import glob
import os
import re
import statistics
import sys

CORPUS_DIRS = [
    "/tmp/claude-0/-home-user-test/e98b5ab4-e37f-5614-9ff3-15e67e5c0180/"
    "scratchpad/agent_gutenberg/raw",
    "/tmp/claude-0/-home-user-test/e98b5ab4-e37f-5614-9ff3-15e67e5c0180/"
    "scratchpad/agent_modern/texts",
]

# The corpus median, which is the target. Not the maximum: Winesburg runs 3.33
# and that is a different book from this one.
TARGET_MEAN = 1.60
TARGET_THREE_PLUS = 11.0


def quotations(text):
    text = re.sub(r"(?m)^#.*$", "", text)
    text = re.sub(r"(?m)^[a-z]+: .*$", "", text)   # chat transcript lines
    text = text.replace("“", '"').replace("”", '"')
    return re.findall(r'"([^"]{2,})"', text)


def sentences(quote):
    return max(1, len(re.findall(r"[.!?]+(?:\s|$)", quote.strip())) or 1)


def profile(text):
    counts = [sentences(q) for q in quotations(text)]
    if not counts:
        return None
    return {
        "quotes": len(counts),
        "mean": sum(counts) / len(counts),
        "one": sum(1 for c in counts if c == 1) / len(counts) * 100,
        "three": sum(1 for c in counts if c >= 3) / len(counts) * 100,
    }


def corpus():
    rows = []
    for d in CORPUS_DIRS:
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            try:
                text = open(os.path.join(d, name), encoding="utf-8",
                            errors="ignore").read()
            except OSError:
                continue
            p = profile(text)
            if p and p["quotes"] >= 200:
                rows.append((name.replace("_stripped", "")[:24], p))
    return rows


def main():
    files = sorted(glob.glob("chapters/*.md"))
    if not files:
        sys.exit("run from the halstead directory")
    book = profile("\n".join(open(f).read() for f in files))
    ref = corpus()

    print(f"\n  {'chapter':<26}{'quotes':>7}{'mean':>7}{'1 sent %':>10}{'3+ %':>7}")
    print("  " + "-" * 57)
    for f in files:
        p = profile(open(f).read())
        if not p or p["quotes"] < 15:
            continue
        flag = "  <-- clipped" if p["mean"] < 1.25 else ""
        print(f"  {os.path.basename(f)[:-3]:<26}{p['quotes']:>7}"
              f"{p['mean']:>7.2f}{p['one']:>10.1f}{p['three']:>7.1f}{flag}")

    print("  " + "-" * 57)
    print(f"  {'BOOK':<26}{book['quotes']:>7}{book['mean']:>7.2f}"
          f"{book['one']:>10.1f}{book['three']:>7.1f}")
    if ref:
        med = statistics.median(p["mean"] for _, p in ref)
        med_one = statistics.median(p["one"] for _, p in ref)
        med_three = statistics.median(p["three"] for _, p in ref)
        lo = min(ref, key=lambda r: r[1]["mean"])
        hi = max(ref, key=lambda r: r[1]["mean"])
        print(f"  {'corpus median':<26}{'':>7}{med:>7.2f}{med_one:>10.1f}"
              f"{med_three:>7.1f}   ({len(ref)} books)")
        print(f"  {'corpus low  ' + lo[0]:<26}{'':>7}{lo[1]['mean']:>7.2f}")
        print(f"  {'corpus high ' + hi[0]:<26}{'':>7}{hi[1]['mean']:>7.2f}")
    print(f"\n  target mean {TARGET_MEAN}, target 3+ {TARGET_THREE_PLUS}%: "
          f"{'ok' if book['mean'] >= TARGET_MEAN else 'UNDER'}\n")


if __name__ == "__main__":
    main()
