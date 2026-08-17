#!/usr/bin/env python3
"""Validate and summarise the per-chapter prose-rule violation reports.

Ten agents read PROSE_RULES.md and STYLE_RULES.md and audited one chapter each,
writing prose_violations/<chapter>.jsonl. One JSON object per line, one reported
violation per object:

    {"file": "chapters/04_pluto.md",
     "line": 45,
     "rule": 24,
     "rule_name": "Filtering",
     "quote": "She can hear the whole table",
     "why": "filter verb between the reader and the sound",
     "suggestion": "The whole table, at once."}

Nothing here rewrites the manuscript. The report is a queue to work from, and
this script exists because a report that cites lines it cannot find is worse
than no report: it sends a rewriter to a line that does not say what the entry
claims. So every entry is checked against the chapter on disk before it counts.

    python3 prose_violations.py                  validate everything, summarise
    python3 prose_violations.py --chapter 04     one chapter
    python3 prose_violations.py --rule 24        one rule, across all chapters
    python3 prose_violations.py --show           print each entry in full
    python3 prose_violations.py --strict         exit nonzero on any problem

Checks, in order: the JSON parses, every field is present, the cited file
exists, `quote` appears verbatim in that file, and it appears at or near the
cited line. `rule` has to be 0 (a STYLE_RULES section) or 1-35.
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPORTS = HERE / "prose_violations"
LINE_SLACK = 3          # a citation may drift by a line or two
REQUIRED = ("file", "line", "rule", "rule_name", "quote", "why", "suggestion")
MAX_RULE = 35


def norm(t):
    """Fold whitespace and quote styles so a curly-vs-straight quote is not a miss."""
    return re.sub(r"\s+", " ", t.replace("“", '"').replace("”", '"')
                  .replace("‘", "'").replace("’", "'")).strip()


_cache = {}


def chapter_lines(path):
    if path not in _cache:
        _cache[path] = [norm(l) for l in path.read_text(encoding="utf-8").split("\n")]
    return _cache[path]


def check(entry, root):
    """Return a list of problems. Empty means the entry is usable."""
    bad = [f"missing field: {k}" for k in REQUIRED if k not in entry]
    if bad:
        return bad

    if not isinstance(entry["rule"], int) or not 0 <= entry["rule"] <= MAX_RULE:
        bad.append(f"rule {entry['rule']!r} is not 0-{MAX_RULE}")
    if not str(entry["quote"]).strip():
        bad.append("empty quote")
    if not str(entry["suggestion"]).strip():
        bad.append("empty suggestion")

    target = root / entry["file"]
    if not target.is_file():
        return bad + [f"no such file: {entry['file']}"]

    lines = chapter_lines(target)
    quote = norm(entry["quote"])
    hits = [i + 1 for i, l in enumerate(lines) if quote and quote in l]
    if not hits:
        return bad + ["quote not found in the chapter"]

    n = entry["line"]
    if not any(abs(h - n) <= LINE_SLACK for h in hits):
        near = ", ".join(str(h) for h in hits[:4])
        bad.append(f"not at line {n}, found at {near}")
    return bad


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=HERE)
    ap.add_argument("--reports", type=Path, default=REPORTS)
    ap.add_argument("--chapter", help="only reports whose filename starts with this")
    ap.add_argument("--rule", type=int, help="only entries for this rule number")
    ap.add_argument("--show", action="store_true", help="print every valid entry")
    ap.add_argument("--strict", action="store_true", help="exit 1 if anything failed")
    a = ap.parse_args()

    if not a.reports.is_dir():
        sys.exit(f"error: no report directory at {a.reports}")

    good, problems = [], []
    per_chapter = Counter()
    per_rule = Counter()
    rule_names = {}

    for f in sorted(a.reports.glob("*.jsonl")):
        if a.chapter and not f.name.startswith(a.chapter):
            continue
        for i, raw in enumerate(f.read_text(encoding="utf-8").split("\n"), 1):
            if not raw.strip() or raw.lstrip().startswith("//"):
                continue
            try:
                entry = json.loads(raw)
            except json.JSONDecodeError as exc:
                problems.append((f.name, i, raw[:50], [f"bad JSON: {exc}"]))
                continue
            if a.rule is not None and entry.get("rule") != a.rule:
                continue
            bad = check(entry, a.root)
            if bad:
                problems.append((f.name, i, str(entry.get("quote", ""))[:50], bad))
                continue
            good.append(entry)
            per_chapter[f.stem] += 1
            per_rule[entry["rule"]] += 1
            rule_names.setdefault(entry["rule"], entry["rule_name"])
            if a.show:
                print(f"\n{entry['file']}:{entry['line']}  rule {entry['rule']} "
                      f"({entry['rule_name']})")
                print(f"  text: {entry['quote']}")
                print(f"  why:  {entry['why']}")
                print(f"  fix:  {entry['suggestion']}")

    if problems:
        print("\nPROBLEMS")
        for name, i, snippet, bad in problems:
            print(f"  {name} line {i}: {snippet}")
            for b in bad:
                print(f"      {b}")

    print(f"\n{len(good)} verified, {len(problems)} with problems.")

    if per_chapter:
        print("\nBY CHAPTER")
        words = {}
        for stem in per_chapter:
            ch = a.root / "chapters" / f"{stem}.md"
            words[stem] = len(ch.read_text(encoding="utf-8").split()) if ch.is_file() else 0
        for stem, n in sorted(per_chapter.items()):
            per_k = n / words[stem] * 1000 if words[stem] else 0
            print(f"  {stem:24} {n:>4}   {per_k:>5.1f} per 1000 words")

    if per_rule:
        print("\nBY RULE")
        for rule, n in per_rule.most_common():
            print(f"  {rule:>3}  {n:>4}  {rule_names[rule]}")

    return 1 if (problems and a.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
