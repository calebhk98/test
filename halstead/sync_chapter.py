#!/usr/bin/env python3
"""Join an edited chapters/NN_*.md file back into the manuscript source files.

chapters/ is derived. Any edit made there has to be pushed back into whichever
of MANUSCRIPT_FULL.md / HALSTEAD.md / CHAPTERS_16_22_v2.md / CHAPTERS_23_30_v2.md
carries that chapter, or the next regeneration silently reverts it.

    python3 sync_chapter.py chapters/20_the_parking_lot.md [...]
"""
import sys, os, re, glob

SOURCES = ['MANUSCRIPT_FULL.md', 'HALSTEAD.md',
           'CHAPTERS_16_22_v2.md', 'CHAPTERS_23_30_v2.md']

def header_of(text):
    for line in text.split('\n'):
        if line.startswith('## Chapter '):
            return line
    raise SystemExit('no chapter header found')

def sync(chapter_path):
    new = open(chapter_path).read().rstrip('\n')
    hdr = header_of(new)
    touched = []
    for src in SOURCES:
        if not os.path.exists(src):
            continue
        lines = open(src).read().split('\n')
        try:
            start = next(i for i, l in enumerate(lines) if l == hdr)
        except StopIteration:
            continue
        end = next((i for i in range(start + 1, len(lines))
                    if lines[i].startswith('## Chapter ')), len(lines))
        # keep the blank-line padding that separated this chapter from the next
        tail = lines[end:]
        body = new.split('\n')
        if tail:
            body = body + ['', '']
        open(src, 'w').write('\n'.join(lines[:start] + body + tail))
        touched.append(src)
    if not touched:
        print(f'  !! {chapter_path}: header not found in any source file')
    else:
        print(f'  {os.path.basename(chapter_path)} -> {", ".join(touched)}')

if __name__ == '__main__':
    targets = sys.argv[1:] or sorted(glob.glob('chapters/*.md'))
    for t in targets:
        sync(t)
