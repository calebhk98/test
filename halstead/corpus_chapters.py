#!/usr/bin/env python3
"""Split reference books into chapters, rank the chapters by reading grade.

The book-level comparison says Little Women is a third dialogue and reads five
grades above Hemingway. This goes a level down, so somebody can read the actual
pages: the chapters that score highest inside the high books, against the
chapters that score lowest inside the low ones.

    python3 corpus_chapters.py --write OUTDIR

Chapter detection is per-book because Gutenberg texts agree on nothing. A book
whose chapters cannot be found is split into equal blocks instead, which is
fine for this purpose: the question is what a page of it looks like, not where
its chapter breaks fall.
"""

import argparse
import importlib.util
import re
import statistics as st
from pathlib import Path

HERE = Path(__file__).resolve().parent
SP = Path("/tmp/claude-0/-home-user-test/e98b5ab4-e37f-5614-9ff3-15e67e5c0180/scratchpad")

spec = importlib.util.spec_from_file_location("pg", HERE / "prose_grade.py")
pg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pg)

HIGH = [("black_beauty", SP / "agent_gutenberg/raw"),
        ("little_women", SP / "agent_gutenberg/raw"),
        ("wind_in_willows", SP / "agent_gutenberg/raw")]
LOW = [("SunAlsoRises_Hemingway", SP / "agent_modern/texts"),
       ("MenWithoutWomen_Hemingway", SP / "agent_modern/texts"),
       ("My_Man_Jeeves_Wodehouse", SP / "agent_modern/texts")]

HEADING = re.compile(r"^\s*(?:CHAPTER|Chapter)\b.*$|^\s*[IVXLC]{1,6}\s*$", re.M)


def split(text):
    """Chapters if the book marks them, equal blocks of about 3,000 words if not."""
    marks = [m.start() for m in HEADING.finditer(text)]
    marks = [m for m in marks if m > len(text) * 0.02]
    if len(marks) >= 5:
        parts = [text[a:b] for a, b in zip(marks, marks[1:] + [len(text)])]
        parts = [p for p in parts if len(p.split()) > 900]
        if len(parts) >= 5:
            return parts
    words = text.split()
    n = 3000
    return [" ".join(words[i:i + n]) for i in range(0, len(words), n)
            if len(words[i:i + n]) > 900]


def title_of(chunk, i):
    first = chunk.strip().split("\n", 1)[0].strip()
    if 3 < len(first) < 70:
        return re.sub(r"[^A-Za-z0-9 ]+", "", first).strip().replace(" ", "_")[:44]
    return f"part{i:02d}"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", type=Path, help="directory to write the six chapters into")
    ap.add_argument("--n", type=int, default=3, help="how many from each end")
    a = ap.parse_args()

    def rank(books, reverse):
        rows = []
        for name, d in books:
            f = d / f"{name}.txt"
            if not f.exists():
                print(f"  missing: {f}")
                continue
            text = f.read_text(encoding="utf-8", errors="ignore")
            for i, ch in enumerate(split(text), 1):
                m = pg.measure(ch, floor=15)
                if m:
                    rows.append((m["fk"], m["lexile"], m["wps"], len(ch.split()),
                                 name, title_of(ch, i), ch))
        rows.sort(key=lambda r: r[0], reverse=reverse)
        return rows

    hi = rank(HIGH, True)
    lo = rank(LOW, False)

    def show(label, rows):
        print(f"\n{label}")
        print(f"  {'book':<28}{'chapter':<40}{'words':>7}{'w/sent':>8}{'F-K':>6}{'Lexile':>8}")
        for fk, lx, wps, w, book, title, _ in rows[:a.n]:
            print(f"  {book:<28}{title[:38]:<40}{w:>7}{wps:>8.1f}{fk:>6.1f}{lx:>8.0f}")

    print(f"{len(hi)} chapters in the three high books, {len(lo)} in the three low.")
    show(f"HIGHEST {a.n} chapters of the high-scoring books", hi)
    show(f"LOWEST {a.n} chapters of the low-scoring books", lo)

    if a.write:
        a.write.mkdir(parents=True, exist_ok=True)
        for tag, rows in (("HIGH", hi[:a.n]), ("LOW", lo[:a.n])):
            for fk, lx, wps, w, book, title, ch in rows:
                p = a.write / f"{tag}_{book}_{title}.txt"
                p.write_text(
                    f"[{book} | {w} words | words per sentence {wps:.1f} | "
                    f"Flesch-Kincaid {fk:.1f} | Lexile {lx:.0f}]\n\n{ch.strip()}\n",
                    encoding="utf-8")
                print(f"  wrote {p.name}")


if __name__ == "__main__":
    main()
