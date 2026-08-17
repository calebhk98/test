#!/usr/bin/env python3
"""Validate and summarise the per-chapter prose-rule violation reports.

One agent per chapter read PROSE_RULES.md and STYLE_RULES.md and audited its
chapter, writing prose_violations/<chapter>.jsonl. One JSON object per line, one
reported violation per object:

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

Every chapter has its own file under chapters/, numbered 01 to 35. Chapters
21-35 come from the two v2 exports, whose own numbering restarts at sixteen;
split_manuscript.py shifts them by five so the book reads continuously, and
the reports here follow the shifted numbers.
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


def style_key(name):
    """Fold an agent's spelling of a STYLE_RULES section into (section, subtype).

    The ten agents wrote the same section as "Automatic-fail narrator
    constructions", "8. Automatic-fail narrator constructions (Interiority of
    non-POV characters)", "Automatic-fail narrator constructions (STYLE_RULES
    section 8)" and "STYLE_RULES §8 automatic-fail narrator constructions",
    among others. Drop the section numbering however it is written, keep a
    parenthesised subtype when it names a real subtype rather than restating
    the section number, and casefold so the count lands in one row.
    """
    name = name.strip()
    # Leading section numbering, in every form the agents used: "8. ",
    # "STYLE_RULES §8 ", "§2/§4 ", "Section 11: ", "STYLE_RULES 8/13: ".
    name = re.sub(r"(?i)^(?:style[_ ]rules?)?\s*(?:§\s*\d+\s*/?\s*)+", "", name)
    name = re.sub(r"(?i)^\s*(?:style[_ ]rules?)?[\s,]*(?:section)?\s*"
                  r"\d+(?:\s*/\s*\d+)?\s*[.:]\s*", "", name)
    name = re.sub(r"^\s*\d+\.\s*", "", name)
    # Some agents append the subtype after an em/en dash instead of in parens.
    name = re.sub(r"\s*(?:--|[—–])\s*", " (", name, count=1)
    if name.count("(") == 1 and not name.endswith(")"):
        name += ")"
    sub = ""
    m = re.match(r"^(.*?)\s*\(([^)]*)\)\s*$", name)
    if m:
        name, inner = m.group(1), m.group(2).strip()
        if not re.fullmatch(r"(?i)style[_ ]rules?,?\s*(section)?\s*\d+", inner):
            sub = cap(inner)
    return cap(name), sub


def cap(s):
    """Casefold for grouping, then restore a leading capital for display."""
    s = s.strip().casefold()
    return s[:1].upper() + s[1:]


_cache = {}


def chapter_lines(path):
    if path not in _cache:
        raw = path.read_text(encoding="utf-8")
        _cache[path] = [norm(l) for l in raw.split("\n")]
    return _cache[path]


def chapter_words(root, stem):
    """Word count for the chapter a report covers."""
    ch = root / "chapters" / f"{stem}.md"
    return len(ch.read_text(encoding="utf-8").split()) if ch.is_file() else 0


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
            # Rule 0 covers every STYLE_RULES section, so the first name seen
            # would misreport the whole bucket as whichever one landed first.
            rule_names.setdefault(
                entry["rule"],
                "STYLE_RULES — see breakout below" if entry["rule"] == 0
                else entry["rule_name"])
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
        words = {stem: chapter_words(a.root, stem) for stem in per_chapter}
        for stem, n in sorted(per_chapter.items()):
            per_k = n / words[stem] * 1000 if words[stem] else 0
            print(f"  {stem:24} {n:>4}   {per_k:>5.1f} per 1000 words")

    if per_rule:
        print("\nBY RULE")
        for rule, n in per_rule.most_common():
            print(f"  {rule:>3}  {n:>4}  {rule_names[rule]}")

    # Rule 0 is every STYLE_RULES section at once, so the single line above
    # says nothing about which of them the manuscript actually breaks. Ten
    # agents named the same section six different ways, so fold the spellings
    # together before counting or the largest category looks like six small
    # ones.
    style = Counter(style_key(e["rule_name"]) for e in good if e["rule"] == 0)
    if style:
        rollup = Counter()
        for (section, _), n in style.items():
            rollup[section] += n
        print("\nRULE 0 BROKEN OUT (STYLE_RULES sections)")
        for section, n in rollup.most_common():
            print(f"       {n:>4}  {section}")
            subs = sorted(((s, c) for (sec, s), c in style.items() if sec == section and s),
                          key=lambda x: -x[1])
            for sub, c in subs:
                print(f"            {c:>3}    {sub}")

    return 1 if (problems and a.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
