#!/usr/bin/env python3
"""Merge chapters/01..35 into one markdown file, normalising the formats.

The book was drafted in three files at three different times and the per-chapter
files still carry the marks of that. This produces a single readable manuscript
with one convention throughout.

    python3 merge_manuscript.py            write HALSTEAD.md
    python3 merge_manuscript.py --check    report what would change, write nothing
    python3 merge_manuscript.py --out X.md write somewhere else

What gets normalised:

  Paragraphs. Chapters 1 to 6 use markdown hard line breaks: every line ends in
  two spaces and there are no blank lines between them, so one line is one
  paragraph. Chapters 7 to 35 separate paragraphs with a blank line. Both become
  blank-line separated, which is the majority convention and the one that
  survives being pasted anywhere. Paragraph boundaries are preserved exactly:
  a hard-break line becomes a paragraph, it is not merged with its neighbours.

  Section breaks. Three markers are in use, "________________" from the two v2
  exports, "---", and "\\---" escaped so it renders as literal text rather than
  a rule. All become "---".

  Blank runs. Four consecutive blank lines around some section breaks become one.

  Headings. Already consistent as "## Chapter One: Before" after the renumbering,
  and passed through unchanged, along with the italic date line under each.

This file is derived, like chapters/. Edits belong in chapters/, which
join_manuscript.py writes back to the three sources. Anything typed straight
into the merged file is lost the next time this runs.
"""

import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHAPTERS = HERE / "chapters"
OUT = HERE / "HALSTEAD.md"

HEADING = re.compile(r"^##\s+")
DATELINE = re.compile(r"^\*[A-Z][a-z]+ \d{4}(?:\s*[–-]\s*[A-Z][a-z]+ \d{4})?\*$")
# The three section-break markers in use, including the backslash-escaped form.
BREAK = re.compile(r"^\s*(?:\\?-{3,}|_{3,}|\*{3,})\s*$")
WORD = re.compile(r"[A-Za-z][A-Za-z']*")


def paragraphs(text):
    """Split a chapter body into paragraphs under either convention.

    A line ending in two spaces closes a paragraph on its own. Otherwise a run
    of consecutive non-blank lines is one paragraph, closed by a blank line.
    Section breaks come back as the marker string so the caller can keep them
    in place.
    """
    out, buf = [], []

    def flush():
        if buf:
            out.append(" ".join(l.strip() for l in buf).strip())
            buf.clear()

    for line in text.split("\n"):
        if BREAK.match(line):
            flush()
            out.append("---")
        elif not line.strip():
            flush()
        elif line.endswith("  "):
            buf.append(line)
            flush()
        else:
            buf.append(line)
    flush()
    return [p for p in out if p]


def read_chapter(path):
    lines = path.read_text(encoding="utf-8").split("\n")
    if not HEADING.match(lines[0]):
        sys.exit(f"error: {path.name} does not open with a '## ' heading")
    heading, rest = lines[0].rstrip(), lines[1:]
    while rest and not rest[0].strip():
        rest.pop(0)
    date = ""
    if rest and DATELINE.match(rest[0].strip()):
        date = rest.pop(0).strip()
    return heading, date, paragraphs("\n".join(rest))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--chapters", type=Path, default=CHAPTERS)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--check", action="store_true", help="report, write nothing")
    a = ap.parse_args()

    files = sorted(a.chapters.glob("*.md"), key=lambda p: int(re.match(r"(\d+)", p.name).group(1)))
    if not files:
        sys.exit(f"error: no chapters in {a.chapters}")

    blocks, rows, total_paras, total_words, breaks = [], [], 0, 0, 0
    for f in files:
        heading, date, paras = read_chapter(f)
        body = [heading] + ([date] if date else []) + paras
        blocks.append("\n\n".join(body))
        n_break = sum(1 for p in paras if p == "---")
        words = sum(len(WORD.findall(p)) for p in paras)
        rows.append((f.stem, len(paras) - n_break, n_break, words))
        total_paras += len(paras) - n_break
        total_words += words
        breaks += n_break

    text = "\n\n".join(blocks) + "\n"

    print(f"{'chapter':<24}{'paragraphs':>12}{'breaks':>8}{'words':>9}")
    for stem, p, b, w in rows:
        print(f"  {stem:<22}{p:>12}{b:>8}{w:>9}")
    print(f"  {'TOTAL':<22}{total_paras:>12}{breaks:>8}{total_words:>9}")

    # The merge must not lose or invent prose. Compare against the chapters as
    # they sit on disk, counting words the same way on both sides.
    src_words = 0
    for f in files:
        for line in f.read_text(encoding="utf-8").split("\n"):
            s = line.strip()
            if HEADING.match(line) or DATELINE.match(s) or BREAK.match(line):
                continue
            src_words += len(WORD.findall(line))
    ok = src_words == total_words
    print(f"\nbody words: chapters {src_words:,}, merged {total_words:,}, "
          f"{'match' if ok else 'MISMATCH'}")
    if not ok:
        sys.exit("error: the merge changed the word count, refusing to write")

    left = sum(1 for l in text.split("\n") if l.endswith("  ") and l.strip())
    odd = sorted({m.group(0) for m in re.finditer(r"(?m)^\s*(?:\\-{3,}|_{3,}|\*{3,})\s*$", text)})
    print(f"hard line breaks remaining: {left}")
    print(f"unnormalised break markers: {odd if odd else 'none'}")

    if a.check:
        print(f"\nwould write {len(text):,} characters to {a.out}")
        return
    a.out.write_text(text, encoding="utf-8")
    print(f"\nwrote {a.out} ({len(text):,} characters)")


if __name__ == "__main__":
    main()
