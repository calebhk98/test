#!/usr/bin/env python3
"""Add markdown hard line breaks (two trailing spaces) inside the header and
lodging blocks, so each labelled field renders on its own line.

Splitting the source onto separate lines is not enough: markdown joins
consecutive lines into one paragraph unless the preceding line ends with two
spaces. Wrapped continuation lines are left alone so they still flow.
"""
import pathlib, re

LABELS = ("**Base:**", "**Weather", "**Theme:**",
          "**Night:**", "**Hotel:**", "**Address:**", "**Unit:**", "**Nightly:**")

n = 0
for f in sorted(pathlib.Path("/home/user/test/japan-trip/days").glob("days-*.md")):
    lines = f.read_text().split("\n")
    for i in range(len(lines) - 1):
        if lines[i + 1].lstrip().startswith(LABELS):
            cur = lines[i]
            if cur.strip() and not cur.endswith("  "):
                lines[i] = cur.rstrip() + "  "
                n += 1
    f.write_text("\n".join(lines))
print(f"hard breaks added: {n}")
