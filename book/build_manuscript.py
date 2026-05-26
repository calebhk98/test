#!/usr/bin/env python3
"""Assemble the individual chapter files into a single manuscript.

Non-destructive: reads book/chapters/chNN.md and writes
book/manuscript/The_Long_Way_Home.md. It never modifies or deletes any
source file. Re-running it simply overwrites the assembled output.

Usage:
    python3 book/build_manuscript.py
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
CHAPTERS_DIR = os.path.join(ROOT, "chapters")
OUT_DIR = os.path.join(ROOT, "manuscript")
OUT_FILE = os.path.join(OUT_DIR, "The_Long_Way_Home.md")

TITLE = "The Long Way Home"
SUBTITLE = "a novel"

# First chapter number of each part -> the divider heading to print before it.
PARTS = {
    1:  "PART ONE — Arrival & Survival",
    7:  "PART TWO — The Man Who Flew",
    15: "PART THREE — How Far to Go",
    25: "PART FOUR — Too Valuable",
    32: "PART FIVE — Starting Over",
    39: "PART SIX — The Ladder",
    47: "PART SEVEN — The Long Way Home",
    52: "EPILOGUE — Someone Climbs",
}


def chapter_files():
    """Return [(num, path), ...] sorted by chapter number."""
    found = []
    for name in os.listdir(CHAPTERS_DIR):
        m = re.fullmatch(r"ch(\d+)\.md", name)
        if m:
            found.append((int(m.group(1)), os.path.join(CHAPTERS_DIR, name)))
    found.sort()
    return found


def main():
    files = chapter_files()
    if not files:
        sys.exit("No chapter files (chNN.md) found in " + CHAPTERS_DIR)

    os.makedirs(OUT_DIR, exist_ok=True)

    out = []
    # Title page.
    out.append(f"# {TITLE}\n")
    out.append(f"*{SUBTITLE}*\n")
    out.append("\n---\n")

    for num, path in files:
        if num in PARTS:
            out.append("\n")
            out.append(f"## {PARTS[num]}\n")
            out.append("\n---\n")
        with open(path, encoding="utf-8") as fh:
            text = fh.read().strip()
        out.append("\n" + text + "\n")
        # A thematic break between chapters keeps them visually separate and
        # converts cleanly to a page break under pandoc.
        out.append("\n---\n")

    assembled = "".join(out).rstrip() + "\n"
    with open(OUT_FILE, "w", encoding="utf-8") as fh:
        fh.write(assembled)

    words = len(re.findall(r"\S+", assembled))
    print(f"Assembled {len(files)} chapters (ch{files[0][0]:02d}-ch{files[-1][0]:02d})")
    print(f"-> {OUT_FILE}")
    print(f"Word count: {words:,}")


if __name__ == "__main__":
    main()
