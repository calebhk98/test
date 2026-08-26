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

# Sentences per quotation alone can be gamed, and the author said so before it
# happened: "some agents may try to cheat by doing like 'Hi. I am Sam. What's
# your name?', which is 3 sentences, but way too simplistic per sentence."
# Words per quotation is the guard.
#
# Percentiles across the 22 reference books:
#
#                        p50     p75     p90     max      Halstead
#   mean words/quote    14.8    22.3    27.6    46.3        17.6
#   variation (CV %)     227     272     346     884          95
#   4 words or under    42.5%   46.7%   50.6%   51.7%       19.4%
#   30 words or over    12.4%   17.8%   22.9%   28.9%       18.4%
#
# The author wants this book in the 75th-to-100th band rather than at the
# median: "I like dialogue a bit more." So the targets below are p75, capped
# short of Winesburg, which is a book of monologues and not this one.
#
# The shape that gets there is bimodal, not uniformly long. Black Beauty runs a
# mean of 31.6 with 51% of its quotations at four words or under: short
# exchanges with real speeches set among them. Halstead currently has neither
# extreme. Its median quotation is 13 words against a corpus median of 6, and
# its variance is below every one of the 22 including Peter Pan. Almost every
# line is a medium-length considered utterance, which is the same defect the
# author keeps naming from the other end: everybody sounds alike.
#
# So: MORE short replies and LONGER long turns, at once. Adding four-word lines
# alone will pull the mean down and fail the first row. Padding every turn will
# fail the third. Both moves together raise the mean and the CV.
TARGET_WORD_MEAN = (22.0, 32.0)
TARGET_WORD_CV = 200.0
TARGET_SHORT_SHARE = 35.0
TARGET_LONG_SHARE = 17.0


def quotations(text):
    text = re.sub(r"(?m)^#.*$", "", text)
    text = re.sub(r"(?m)^[a-z]+: .*$", "", text)   # chat transcript lines
    text = text.replace("“", '"').replace("”", '"')
    return re.findall(r'"([^"]{2,})"', text)


def sentences(quote):
    return max(1, len(re.findall(r"[.!?]+(?:\s|$)", quote.strip())) or 1)


def profile(text):
    qs = quotations(text)
    counts = [sentences(q) for q in qs]
    if not counts:
        return None
    wl = [len(re.findall(r"[A-Za-z']+", q)) for q in qs]
    mean_w = sum(wl) / len(wl)
    sd = statistics.stdev(wl) if len(wl) > 1 else 0.0
    return {
        "quotes": len(counts),
        "mean": sum(counts) / len(counts),
        "one": sum(1 for c in counts if c == 1) / len(counts) * 100,
        "three": sum(1 for c in counts if c >= 3) / len(counts) * 100,
        "wmean": mean_w,
        "wmed": statistics.median(wl),
        "wcv": 100 * sd / mean_w if mean_w else 0.0,
        "short": sum(1 for v in wl if v <= 4) / len(wl) * 100,
        "long": sum(1 for v in wl if v >= 30) / len(wl) * 100,
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
    print(f"\n  sentences per quotation: target mean {TARGET_MEAN}, "
          f"target 3+ {TARGET_THREE_PLUS}%: "
          f"{'ok' if book['mean'] >= TARGET_MEAN else 'UNDER'}")

    lo, hi = TARGET_WORD_MEAN
    print("\n  words per quotation, which is what stops a long turn being four "
          "short ones")
    print(f"    {'mean':<22}{book['wmean']:>7.1f}    corpus p75 22.3   "
          f"target {lo:.0f}-{hi:.0f}      "
          f"{'ok' if lo <= book['wmean'] <= hi else 'FAIL'}")
    print(f"    {'median':<22}{book['wmed']:>7.0f}    corpus median 6")
    print(f"    {'variation (CV %)':<22}{book['wcv']:>7.0f}    corpus p75 272    "
          f"target over {TARGET_WORD_CV:.0f}   "
          f"{'ok' if book['wcv'] >= TARGET_WORD_CV else 'FAIL'}")
    print(f"    {'4 words or under':<22}{book['short']:>7.1f}%   corpus p75 46.7%  "
          f"target over {TARGET_SHORT_SHARE:.0f}%  "
          f"{'ok' if book['short'] >= TARGET_SHORT_SHARE else 'FAIL'}")
    print(f"    {'30 words or over':<22}{book['long']:>7.1f}%   corpus p75 17.8%  "
          f"target over {TARGET_LONG_SHARE:.0f}%  "
          f"{'ok' if book['long'] >= TARGET_LONG_SHARE else 'FAIL'}")
    print("\n  Aim at both ends at once. Short exchanges with real speeches set")
    print("  among them, not every turn the same middling length. The same person")
    print("  says four words in one scene and a paragraph in another.\n")


if __name__ == "__main__":
    main()
