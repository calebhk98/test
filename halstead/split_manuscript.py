#!/usr/bin/env python3
"""Split MANUSCRIPT_FULL.md into one file per chapter under halstead/chapters/.

Default run produces 20 files, one per chapter, named NN_slug.md.

    python3 split_manuscript.py
    python3 split_manuscript.py --parts 20     # force exactly 20 files
    python3 split_manuscript.py --check        # report the split, write nothing

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
WORD = re.compile(r"[A-Za-z][A-Za-z']*")

# "Chapter Seventeen: Fourteen" -> ordinal 17, so filenames sort correctly
# without relying on the order headings happen to appear in.
ORDINALS = """one two three four five six seven eight nine ten eleven twelve
thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty twentyone
twentytwo twentythree twentyfour twentyfive twentysix twentyseven twentyeight
twentynine thirty""".split()


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


def parse_chapters(text):
    """Return [{number, title, slug, body, words}] split on '## ' headings.

    A heading with no text after the hashes is an artifact of the source file,
    not a chapter. It is dropped along with its (empty) body.
    """
    chapters, current = [], None
    for line in text.splitlines():
        match = HEADING.match(line)
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
        number = chapter_number(chapter["title"], len(kept) + 1)
        kept.append({
            "number": number,
            "title": chapter["title"],
            "slug": slugify(re.sub(r"^chapter\s+[a-z]+\s*:\s*", "", chapter["title"], flags=re.I)),
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


def render(group):
    """One chapter per file keeps its own heading; a bundle keeps all of them."""
    return "\n\n".join(f"## {c['title']}\n\n{c['body']}".strip() for c in group) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", type=Path, default=SOURCE, help="manuscript to split")
    parser.add_argument("--outdir", type=Path, default=OUTDIR, help="directory to write into")
    parser.add_argument("--parts", type=int, help="force exactly N output files")
    parser.add_argument("--check", action="store_true", help="report the split, write nothing")
    args = parser.parse_args()

    if not args.source.is_file():
        sys.exit(f"error: no manuscript at {args.source}")
    if args.parts is not None and args.parts < 1:
        sys.exit("error: --parts must be at least 1")

    chapters = parse_chapters(args.source.read_text(encoding="utf-8"))
    if not chapters:
        sys.exit(f"error: no '## ' headings found in {args.source}")

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
    print(f"{args.source.name}: {len(chapters)} chapters, {total:,} words -> {len(files)} files")
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

    written = sum(len(WORD.findall((args.outdir / name).read_text(encoding="utf-8")))
                  for name, _, _ in files)
    source_words = len(WORD.findall(args.source.read_text(encoding="utf-8")))
    print(f"\nwrote {len(files)} files to {args.outdir}")
    print(f"word count: source {source_words:,}, split {written:,}, "
          f"{'match' if written == source_words else 'MISMATCH'}")


if __name__ == "__main__":
    main()
