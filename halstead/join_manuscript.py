#!/usr/bin/env python3
"""Write the per-chapter files back into the three manuscript sources.

split_manuscript.py goes one way: three source files out to chapters/01..35.
This goes the other way, and exists because editing happens in chapters/. One
agent per chapter can work without colliding with anyone else, which is not
true of three shared files. But chapters/ is rebuilt from the sources on every
split, so an edit that only lives there is one `python3 split_manuscript.py`
away from being erased. Run this after editing, and the sources catch up.

    python3 join_manuscript.py --check    report what would change, write nothing
    python3 join_manuscript.py            write the sources
    python3 join_manuscript.py --verify   write, then re-split and prove it round-trips

What gets undone on the way back:
  - the date line under each title, which is generated from
    chronology/chapter_dates.json and is not part of the manuscript
  - the renumbering, so the v2 files keep their own count from sixteen
  - the markdown heading, for the two v2 files, which are plain text
  - the byte-order mark, which both v2 files carry on their first line

Chapter bodies are copied verbatim. Whitespace around a chapter boundary is
normalised to one blank line, so the first run after an edit may show a
whitespace-only difference in a source file even where no prose changed.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUTDIR = HERE / "chapters"

# (source file, chapters it holds, number shift back, markdown headings, BOM)
SOURCES = [
    ("MANUSCRIPT_FULL.md", range(1, 21), 0, True, False),
    ("CHAPTERS_16_22_v2.md", range(21, 28), -5, False, True),
    ("CHAPTERS_23_30_v2.md", range(28, 36), -5, False, True),
]

HEADING = re.compile(r"^##\s+(.*)$")
DATELINE = re.compile(r"^\*[A-Z][a-z]+ \d{4}(?:\s*[–-]\s*[A-Z][a-z]+ \d{4})?\*$")
TENS = {20: "Twenty", 30: "Thirty"}
UNITS = ("One Two Three Four Five Six Seven Eight Nine Ten Eleven Twelve "
         "Thirteen Fourteen Fifteen Sixteen Seventeen Eighteen Nineteen").split()


def ordinal_word(n):
    if n <= 19:
        return UNITS[n - 1]
    tens, unit = divmod(n, 10)
    return f"{TENS[tens * 10]}-{UNITS[unit - 1]}" if unit else TENS[tens * 10]


def read_chapter(path):
    """Return (title without the 'Chapter N:' prefix, body) for one chapter file."""
    lines = path.read_text(encoding="utf-8").split("\n")
    m = HEADING.match(lines[0])
    if not m:
        sys.exit(f"error: {path.name} does not open with a '## ' heading")
    name = re.sub(r"^chapter\s+[a-z\- ]+?\s*:\s*", "", m.group(1).strip(), flags=re.I)
    rest = lines[1:]
    # Drop the generated date line and the blank line that follows it.
    while rest and not rest[0].strip():
        rest.pop(0)
    if rest and DATELINE.match(rest[0].strip()):
        rest.pop(0)
    return name, "\n".join(rest).strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=HERE)
    ap.add_argument("--outdir", type=Path, default=OUTDIR)
    ap.add_argument("--check", action="store_true", help="report, write nothing")
    ap.add_argument("--verify", action="store_true",
                    help="after writing, re-split and confirm chapters/ is unchanged")
    a = ap.parse_args()

    by_number = {}
    for p in a.outdir.glob("*.md"):
        m = re.match(r"(\d+)_", p.name)
        if m:
            by_number[int(m.group(1))] = p

    changed = []
    for name, numbers, shift, markdown, bom in SOURCES:
        missing = [n for n in numbers if n not in by_number]
        if missing:
            sys.exit(f"error: no chapter file for {missing} (needed by {name})")
        blocks = []
        for n in numbers:
            title, body = read_chapter(by_number[n])
            head = f"Chapter {ordinal_word(n + shift)}: {title}".rstrip(": ")
            # The markdown source puts a blank line under its heading; the two
            # plain-text exports run straight into the first line of prose.
            gap = "\n\n" if markdown else "\n"
            blocks.append(f"{'## ' if markdown else ''}{head}{gap}{body}")
        text = "\n\n".join(blocks) + "\n"
        if bom:
            text = "﻿" + text

        target = a.root / name
        old = target.read_text(encoding="utf-8") if target.is_file() else None
        if old == text:
            print(f"  {name}: unchanged")
            continue
        changed.append(name)
        words = len(re.findall(r"[A-Za-z][A-Za-z']*", text))
        was = len(re.findall(r"[A-Za-z][A-Za-z']*", old)) if old else 0
        print(f"  {name}: rewritten, {was:,} -> {words:,} words ({words - was:+,})")
        if not a.check:
            target.write_text(text, encoding="utf-8")

    if a.check:
        print(f"\n{len(changed)} source file(s) would change.")
        return 0

    print(f"\n{len(changed)} source file(s) written.")

    if a.verify:
        before = {p.name: p.read_text(encoding="utf-8") for p in a.outdir.glob("*.md")}
        r = subprocess.run([sys.executable, str(HERE / "split_manuscript.py")],
                           capture_output=True, text=True)
        if r.returncode:
            print(r.stdout + r.stderr)
            sys.exit("error: re-split failed")
        after = {p.name: p.read_text(encoding="utf-8") for p in a.outdir.glob("*.md")}
        drift = sorted(set(before) ^ set(after)) + \
            sorted(k for k in set(before) & set(after) if before[k] != after[k])
        if drift:
            print("\nROUND TRIP FAILED, these differ after re-splitting:")
            for k in drift:
                print(f"  {k}")
            return 1
        print("round trip: re-splitting the sources reproduces chapters/ exactly")
    return 0


if __name__ == "__main__":
    sys.exit(main())
