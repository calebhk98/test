#!/usr/bin/env python3
"""What the viewpoint character's verbs are doing, against the corpus.

This exists because the obvious approach did not work. Six agents logged 141
passivity instances; the passages they quoted were pulled out and searched for a
shared signature - says nothing, lets it go, goes back to, there is a version
where - and the patterns barely fired. Ten constructions across 581 flagged
passages returned thirty-one hits between them.

That is the whole problem in one number. Passivity has no lexical signature,
which is exactly why `tics.py` could cap three phrasings and pass while the
author kept seeing it everywhere. It is not in the words that are present. It
is in which verb the sentence reaches for.

So this counts verbs by what they ask of the person doing them, the same way
for this book and for twenty-three published novels.

READ THE RESULT BEFORE YOU USE IT. The book comes out at 23.8% inward against a
corpus median of 43.7%, near the bottom of the range: it is markedly MORE
verb-active than the median novel, not less. A second hypothesis was tested and
failed the same way - verbs aimed at another person rather than at an object,
where the book sits at the 78th percentile of the corpus.

Two measures, both saying the prose is not passive at the sentence level. That
is not a licence to tell the author he is wrong. Six agents reading carefully
found 141 instances and the strongest of them are real: a character who states
inaction as a strategy, a line that says he does nothing immediately before he
does something, a protagonist who receives the sharpest thing anybody says
about her and puts her hand in her lap.

What it means is that the passivity is structural and not lexical. The prose is
full of action verbs describing small physical business - putting a glass down,
going to a door - while the scene reaches the same end it would have reached
without her. No word-frequency measure can see that, which is why this file
reports numbers and sets no target. The thing that does catch it is the
initiates-a-scene count in passes/passive/, which was done by reading.

    STILLNESS   waits, sits, stays, stands, watches, listens, holds still
    INTERIOR    thinks, knows, works out, notices, wonders, remembers, decides
    ACTION      says, asks, goes, takes, opens, pulls, writes, hands, calls

Only verbs with a personal-pronoun subject are counted, which is a rough proxy
for the viewpoint character and is rough in the same direction for every book.
The number that matters is the last column: what share of a character's verbs
are things that happen inside them or to them, against what share get something
done. A book of pure action would be a bad book; the corpus range is the point
of the comparison, not zero.

    python3 measures/agency.py              the book against the corpus
    python3 measures/agency.py --chapters   per chapter, worst first
    python3 measures/agency.py --show CLASS print every hit for one class
"""
import argparse, glob, re, statistics as st
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
CORPUS = [
    "/tmp/claude-0/-home-user-test/e98b5ab4-e37f-5614-9ff3-15e67e5c0180/scratchpad/agent_gutenberg/raw",
    "/tmp/claude-0/-home-user-test/e98b5ab4-e37f-5614-9ff3-15e67e5c0180/scratchpad/agent_modern/texts",
]

STILLNESS = r"""wait|waits|waited|sit|sits|sat|stay|stays|stayed|stand|stands|stood|
lie|lies|lay|watch|watches|watched|listen|listens|listened|look|looks|looked"""
INTERIOR = r"""think|thinks|thought|know|knows|knew|notice|notices|noticed|wonder|wonders|
wondered|remember|remembers|remembered|realise|realises|realised|realize|realizes|realized|
understand|understands|understood|feel|feels|felt|decide|decides|decided|
consider|considers|considered|expect|expects|expected"""
ACTION = r"""say|says|said|ask|asks|asked|tell|tells|told|go|goes|went|take|takes|took|
put|puts|give|gives|gave|open|opens|opened|pull|pulls|pulled|push|pushes|pushed|
write|writes|wrote|hand|hands|handed|call|calls|called|throw|throws|threw|
catch|catches|caught|run|runs|ran|walk|walks|walked|climb|climbs|climbed|
answer|answers|answered|start|starts|started|carry|carries|carried|build|builds|built"""

def _alt(s):
    return "|".join(w.strip() for w in s.replace("\n", "").split("|") if w.strip())

CLASSES = {
    "stillness": re.compile(rf"\b(?:she|he|they|I)\s+(?:{_alt(STILLNESS)})\b", re.I),
    "interior":  re.compile(rf"\b(?:she|he|they|I)\s+(?:{_alt(INTERIOR)})\b", re.I),
    "action":    re.compile(rf"\b(?:she|he|they|I)\s+(?:{_alt(ACTION)})\b", re.I),
}


def strip_gut(t):
    m = re.search(r"\*\*\* ?START OF.*?\*\*\*(.*?)\*\*\* ?END OF", t, re.S)
    return m.group(1) if m else t


def profile(text):
    c = {k: len(rx.findall(text)) for k, rx in CLASSES.items()}
    total = sum(c.values())
    c["total"] = total
    c["inward"] = 100 * (c["stillness"] + c["interior"]) / total if total else 0
    return c


def corpus():
    out = []
    for d in CORPUS:
        for f in sorted(Path(d).rglob("*.txt")):
            if "stripped" in f.stem:
                continue
            t = strip_gut(f.read_text(encoding="utf-8", errors="replace"))
            if len(re.findall(r"[A-Za-z']+", t)) > 20000:
                out.append((f.stem, profile(t)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapters", action="store_true")
    ap.add_argument("--show")
    a = ap.parse_args()

    files = sorted(glob.glob(str(HERE / "chapters" / "*.md")))

    if a.show:
        rx = CLASSES.get(a.show)
        if not rx:
            print(f"  classes: {', '.join(CLASSES)}")
            return
        for f in files:
            for i, line in enumerate(Path(f).read_text().split("\n"), 1):
                for m in rx.finditer(line):
                    s = max(0, m.start() - 55)
                    print(f"  {Path(f).stem}:{i}  ...{line[s:m.end()+55]}...")
        return

    book = profile("\n".join(Path(f).read_text() for f in files))
    ref = corpus()
    vals = sorted(p["inward"] for _, p in ref)
    med, lo, hi = st.median(vals), vals[0], vals[-1]

    print(f"\n{len(ref)} reference books. Verbs with a personal-pronoun subject.\n")
    print(f"  {'':<22}{'stillness':>10}{'interior':>10}{'action':>9}{'inward %':>11}")
    print("  " + "-" * 62)
    print(f"  {'HALSTEAD':<22}{book['stillness']:>10}{book['interior']:>10}"
          f"{book['action']:>9}{book['inward']:>10.1f}%")
    print(f"  {'corpus median':<22}{'':>10}{'':>10}{'':>9}{med:>10.1f}%")
    print(f"  {'corpus range':<22}{'':>10}{'':>10}{'':>9}"
          f"{lo:>7.1f} to {hi:.1f}%")

    over = book["inward"] > hi
    print(f"\n  {'OVER every reference book' if over else 'inside the corpus range'}"
          f"   {book['inward'] - med:+.1f} points against the median")

    if a.chapters:
        print(f"\n  {'chapter':<24}{'still':>7}{'inter':>7}{'act':>7}{'inward %':>11}")
        print("  " + "-" * 58)
        rows = [(Path(f).stem, profile(Path(f).read_text())) for f in files]
        for stem, p in sorted(rows, key=lambda r: -r[1]["inward"]):
            print(f"  {stem:<24}{p['stillness']:>7}{p['interior']:>7}"
                  f"{p['action']:>7}{p['inward']:>10.1f}%")

    print()
    return 1 if over else 0


# Run from grade.py, not on its own. Every measure in measures/ reports one
# slice; the scorecard is the whole picture.
def _solo_notice():
    import sys, os
    if os.environ.get("HALSTEAD_VIA_GRADE"):
        return
    print("  [one measure of thirteen. the scorecard is: python3 grade.py]",
          file=sys.stderr)


if __name__ == "__main__":
    _solo_notice()
    raise SystemExit(main())
