#!/usr/bin/env python3
"""Split the manuscript into one file per chapter under halstead/chapters/.

A default run produces 35 files, one per chapter, named NN_slug.md.

    python3 split_manuscript.py
    python3 split_manuscript.py --check                 report the split, write nothing
    python3 split_manuscript.py --source OTHER.md       split one file on its own

The book arrives in three files rather than one. MANUSCRIPT_FULL.md holds
chapters 1-20 as markdown with '## ' headings. The two v2 exports hold the rest
as plain text with bare 'Chapter Sixteen: The Applications' lines, a byte-order
mark, and their own numbering that restarts at sixteen. Those numbers are a
leftover from when they were drafted as a separate run: the chapters follow
chapter 20, so each is shifted by five and the book reads 1 to 35 continuously.

Everything is written in one pass because the output directory is rebuilt from
scratch each run. Splitting one source at a time would delete the chapters
written by the run before it.

--parts groups consecutive chapters into N files of roughly equal word count.
It is a no-op when the chapter count already equals N.
"""

import argparse
import re
import shutil
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "MANUSCRIPT_FULL.md"
OUTDIR = HERE / "chapters"

HEADING = re.compile(r"^##\s+(.*)$")
# The v2 exports have no markdown. A chapter opens on a bare line reading
# "Chapter Twenty-Three: Nadia" and nothing else on that line.
HEADING_PLAIN = re.compile(r"^(Chapter\s+[A-Za-z][A-Za-z\- ]*(?::.*)?)\s*$")
WORD = re.compile(r"[A-Za-z][A-Za-z']*")

# (file, heading pattern, number shift). The v2 files number from sixteen and
# sit after chapter 20, so five is added to each of their chapter numbers.
BOOK = [
    ("MANUSCRIPT_FULL.md", HEADING, 0),
    ("CHAPTERS_16_22_v2.md", HEADING_PLAIN, 5),
    ("CHAPTERS_23_30_v2.md", HEADING_PLAIN, 5),
]

# "Chapter Seventeen: Fourteen" -> ordinal 17, so filenames sort correctly
# without relying on the order headings happen to appear in.
ORDINALS = """one two three four five six seven eight nine ten eleven twelve
thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty twentyone
twentytwo twentythree twentyfour twentyfive twentysix twentyseven twentyeight
twentynine thirty""".split()


TENS = {20: "Twenty", 30: "Thirty"}
UNITS = ("One Two Three Four Five Six Seven Eight Nine Ten Eleven Twelve "
         "Thirteen Fourteen Fifteen Sixteen Seventeen Eighteen Nineteen").split()


def ordinal_word(n):
    """3 -> 'Three', 21 -> 'Twenty-One'. Matches the headings already in use."""
    if n <= 19:
        return UNITS[n - 1]
    tens, unit = divmod(n, 10)
    word = TENS[tens * 10]
    return f"{word}-{UNITS[unit - 1]}" if unit else word


def slugify(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_") or "untitled"


def chapter_number(title, fallback):
    """Read the ordinal out of 'Chapter Seventeen: Fourteen', else use position."""
    match = re.match(r"chapter\s+([a-z\- ]+?)\s*(?::|$)", title.strip(), re.I)
    if match:
        word = re.sub(r"[^a-z]", "", match.group(1).lower())
        if word in ORDINALS:
            return ORDINALS.index(word) + 1
    return fallback


def parse_chapters(text, heading=HEADING, shift=0):
    """Return [{number, title, slug, body, words}] split on chapter headings.

    A heading with no text after the hashes is an artifact of the source file,
    not a chapter. It is dropped along with its (empty) body.

    `shift` is added to every chapter number, which is how the v2 files' own
    numbering from sixteen becomes chapters 21 onward.
    """
    chapters, current = [], None
    for line in text.splitlines():
        match = heading.match(line)
        if match:
            if current:
                chapters.append(current)
            current = {"title": match.group(1).strip(), "lines": []}
        elif current:
            current["lines"].append(line)
        elif line.strip():
            sys.exit(f"error: content before the first '## ' heading: {line[:60]!r}")
    if current:
        chapters.append(current)

    kept = []
    for chapter in chapters:
        body = "\n".join(chapter["lines"]).strip()
        if not chapter["title"] and not body:
            continue
        number = chapter_number(chapter["title"], len(kept) + 1) + shift
        kept.append({
            "number": number,
            "title": chapter["title"],
            # The ordinal can be hyphenated ("Chapter Twenty-One: Ten Targets"),
            # so the strip has to reach past the hyphen to leave "Ten Targets".
            "name": (name := re.sub(r"^chapter\s+[a-z\- ]+?\s*:\s*", "",
                                    chapter["title"], flags=re.I)),
            "slug": slugify(name),
            "body": body,
            "words": len(WORD.findall(chapter["title"])) + len(WORD.findall(body)),
        })
    return kept


def group_into(chapters, parts):
    """Bundle consecutive chapters into `parts` groups of similar word count."""
    if parts >= len(chapters):
        return [[chapter] for chapter in chapters]

    total = sum(chapter["words"] for chapter in chapters)
    groups, current, running = [], [], 0
    for index, chapter in enumerate(chapters):
        current.append(chapter)
        running += chapter["words"]
        remaining_groups = parts - len(groups) - 1
        remaining_chapters = len(chapters) - index - 1
        target = total * (len(groups) + 1) / parts
        if remaining_groups and (running >= target or remaining_chapters <= remaining_groups):
            groups.append(current)
            current = []
    if current:
        groups.append(current)
    return groups


def heading_for(c):
    """Rebuild the heading from the chapter's number so the two agree.

    Chapters 1-20 come out byte-identical to the source. The v2 chapters carry
    their old numbering in the text as well as the filename, so chapter 21 opens
    "Chapter Sixteen: The Applications" while chapter 16 opens "Chapter Sixteen:
    Thirteen". Regenerating the ordinal from the shifted number settles that.
    The source files keep their own numbering; only the split output is renumbered.
    """
    return f"## Chapter {ordinal_word(c['number'])}: {c['name']}".rstrip(": ")


def render(group):
    """One chapter per file keeps its own heading; a bundle keeps all of them."""
    return "\n\n".join(f"{heading_for(c)}\n\n{c['body']}".strip() for c in group) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", type=Path,
                        help="split just this one file instead of the whole book")
    parser.add_argument("--root", type=Path, default=HERE, help="where the sources live")
    parser.add_argument("--outdir", type=Path, default=OUTDIR, help="directory to write into")
    parser.add_argument("--parts", type=int, help="force exactly N output files")
    parser.add_argument("--check", action="store_true", help="report the split, write nothing")
    args = parser.parse_args()

    if args.parts is not None and args.parts < 1:
        sys.exit("error: --parts must be at least 1")

    # --source splits that one file alone; otherwise the whole book, in order.
    if args.source:
        sources = [(args.source, HEADING, 0)]
    else:
        sources = [(args.root / name, pattern, shift) for name, pattern, shift in BOOK]

    chapters, source_words = [], 0
    for path, pattern, shift in sources:
        if not path.is_file():
            sys.exit(f"error: no manuscript at {path}")
        # utf-8-sig: the v2 exports open with a byte-order mark, which would
        # otherwise sit in front of the first chapter heading and hide it.
        text = path.read_text(encoding="utf-8-sig")
        found = parse_chapters(text, pattern, shift)
        if not found:
            sys.exit(f"error: no chapter headings found in {path.name}")
        chapters.extend(found)
        # Body words only. Headings are excluded on both sides of the check
        # because renumbering rewrites them, and "Sixteen" becoming
        # "Twenty-One" is a word the WORD pattern counts twice. What has to
        # round-trip is the prose, not the chapter numbering.
        source_words += sum(len(WORD.findall(l)) for l in text.splitlines()
                            if not pattern.match(l))

    numbers = [c["number"] for c in chapters]
    if len(numbers) != len(set(numbers)):
        clash = sorted(n for n in set(numbers) if numbers.count(n) > 1)
        sys.exit(f"error: two chapters share a number: {clash}")
    if numbers != sorted(numbers):
        sys.exit(f"error: chapter numbers are out of order: {numbers}")

    groups = group_into(chapters, args.parts) if args.parts else [[c] for c in chapters]

    files = []
    for index, group in enumerate(groups, start=1):
        if len(group) == 1:
            name = f"{group[0]['number']:02d}_{group[0]['slug']}.md"
        else:
            name = f"{index:02d}_{group[0]['slug']}__{group[-1]['slug']}.md"
        files.append((name, render(group), sum(c["words"] for c in group)))

    if len(files) != len({name for name, _, _ in files}):
        sys.exit("error: chapter titles produced duplicate filenames")

    total = sum(words for _, _, words in files)
    names = ", ".join(p.name for p, _, _ in sources)
    print(f"{names}: {len(chapters)} chapters, {total:,} words -> {len(files)} files")
    for name, _, words in files:
        print(f"  {name:<44} {words:>6,} words")

    if args.check:
        return

    # Rewritten from scratch each run, so a renamed chapter never leaves a stale file.
    if args.outdir.exists():
        shutil.rmtree(args.outdir)
    args.outdir.mkdir(parents=True)
    for name, body, _ in files:
        (args.outdir / name).write_text(body, encoding="utf-8")

    written = sum(len(WORD.findall(l))
                  for name, _, _ in files
                  for l in (args.outdir / name).read_text(encoding="utf-8").splitlines()
                  if not HEADING.match(l))
    print(f"\nwrote {len(files)} files to {args.outdir}")
    print(f"body words: source {source_words:,}, split {written:,}, "
          f"{'match' if written == source_words else 'MISMATCH'}")


if __name__ == "__main__":
    main()
