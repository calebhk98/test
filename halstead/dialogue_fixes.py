#!/usr/bin/env python3
"""Validate, review and apply proposed dialogue rewrites.

Each character agent writes one JSONL file to dialogue_fixes/<NAME>.jsonl. One
JSON object per line, one proposed change per object:

    {"file": "chapters/12_nine.md",
     "line": 25,
     "speaker": "Sam",
     "current": "I liked dance and I was good at dance",
     "replacement": "I liked dance. I was good at dance",
     "reason": "flat declaratives, no subordinate clause"}

`current` has to appear verbatim in `file`, and has to sit inside quotation
marks or inside a group-chat message, because this pass changes only what
characters say. Everything else on the page stays. Chat lines carry no quotes
and look like "nadia: im FINE. im insulted"; the text after the colon counts.

    python3 dialogue_fixes.py                 validate every file
    python3 dialogue_fixes.py --speaker Sam   one character
    python3 dialogue_fixes.py --show          print each proposed change
    python3 dialogue_fixes.py --apply         write the changes to the chapters

Validation checks, in order: the JSON parses, the named file exists, `current`
appears in that file, it appears at or near the stated line, it sits inside
quotation marks, and `replacement` differs from `current`. Anything that fails
is reported and skipped rather than applied.
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXES = HERE / "dialogue_fixes"
LINE_SLACK = 3          # a citation may drift by a line or two
REQUIRED = ("file", "line", "speaker", "current", "replacement", "reason")
CHAT_NAMES = {"chloe", "ruth", "sam", "kavi", "nadia", "eli", "theo"}


def norm(t):
    return re.sub(r"\s+", " ", t.replace("“", '"').replace("”", '"')
                  .replace("‘", "'").replace("’", "'")).strip()


# The group chat carries dialogue without quotation marks: a line is
# "nadia: im FINE. im insulted". That is speech, and most of what Eli and Theo
# ever say arrives this way, so the inside-quotes check has to admit it.
CHAT_LINE = re.compile(r"^\s*([a-z]+):\s*(.+)$", re.I)


def dialogue_spans(text):
    """Character ranges holding speech: inside double quotes, or a chat message.

    A chat line yields two spans: the message after the colon, and the whole
    line including the name. The second exists because two speakers sometimes
    say the identical words back to back, and the only way to point at one of
    them is to include the prefix. Rewriting "kavi: X" to "kavi: Y" changes
    the speech and leaves the attribution alone, so it stays in scope.
    """
    m = CHAT_LINE.match(text)
    if m and m.group(1).lower() in CHAT_NAMES:
        return [(m.start(2), m.end(2)), (m.start(), m.end())]
    return [(m.start(), m.end()) for m in re.finditer(r'"[^"]*"', text)]


def check(entry, root):
    """Return a list of problems. Empty means the entry is usable."""
    bad = [f"missing field: {k}" for k in REQUIRED if k not in entry]
    if bad:
        return bad

    target = root / entry["file"]
    if not target.is_file():
        return [f"no such file: {entry['file']}"]

    raw = target.read_text(encoding="utf-8")
    lines = raw.split("\n")
    cur, rep = norm(entry["current"]), norm(entry["replacement"])

    if cur == rep:
        bad.append("replacement is identical to current")
    if norm(raw).count(cur) == 0:
        return bad + ["current text not found in the file"]
    if norm(raw).count(cur) > 1:
        bad.append(f"current text appears {norm(raw).count(cur)} times, ambiguous")

    n = entry["line"]
    window = range(max(0, n - 1 - LINE_SLACK), min(len(lines), n + LINE_SLACK))
    hit = next((i for i in window if cur in norm(lines[i])), None)
    if hit is None:
        found = next((i + 1 for i, l in enumerate(lines) if cur in norm(l)), None)
        bad.append(f"not at line {n}" + (f", found at {found}" if found else ""))
    else:
        line = lines[hit]
        pos = norm(line).find(cur)
        inside = any(s <= pos < e for s, e in dialogue_spans(norm(line)))
        if not inside:
            bad.append("current text is not inside quotation marks or a chat message, "
                       "so it is not dialogue")
    return bad


def apply_all(entries, root):
    by_file = {}
    for e in entries:
        by_file.setdefault(e["file"], []).append(e)
    for name, group in sorted(by_file.items()):
        target = root / name
        raw = target.read_text(encoding="utf-8")
        n = 0
        for e in group:
            if e["current"] in raw:
                raw = raw.replace(e["current"], e["replacement"], 1)
                n += 1
        target.write_text(raw, encoding="utf-8")
        print(f"  {name}: {n} of {len(group)} applied")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=HERE)
    ap.add_argument("--fixes", type=Path, default=FIXES)
    ap.add_argument("--speaker", help="only entries for this speaker")
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--apply", action="store_true", help="write valid changes to disk")
    a = ap.parse_args()

    if not a.fixes.is_dir():
        sys.exit(f"error: no fix directory at {a.fixes}")

    good, problems, per_speaker = [], [], Counter()
    for f in sorted(a.fixes.glob("*.jsonl")):
        for i, raw in enumerate(f.read_text(encoding="utf-8").split("\n"), 1):
            if not raw.strip() or raw.lstrip().startswith("//"):
                continue
            try:
                entry = json.loads(raw)
            except json.JSONDecodeError as exc:
                problems.append((f.name, i, entry_id := raw[:40], [f"bad JSON: {exc}"]))
                continue
            if a.speaker and entry.get("speaker", "").lower() != a.speaker.lower():
                continue
            bad = check(entry, a.root)
            if bad:
                problems.append((f.name, i, entry.get("current", "")[:40], bad))
            else:
                good.append(entry)
                per_speaker[entry["speaker"]] += 1
                if a.show:
                    print(f"\n{entry['speaker']}  {entry['file']}:{entry['line']}")
                    print(f"  now:  {entry['current']}")
                    print(f"  new:  {entry['replacement']}")
                    print(f"  why:  {entry['reason']}")

    if problems:
        print("\nPROBLEMS")
        for name, i, snippet, bad in problems:
            print(f"  {name} line {i}: {snippet}")
            for b in bad:
                print(f"      {b}")

    print(f"\n{len(good)} usable, {len(problems)} with problems.")
    for who, n in per_speaker.most_common():
        print(f"  {who:12} {n}")

    if a.apply and good:
        print("\napplying:")
        apply_all(good, a.root)
    elif a.apply:
        print("\nnothing valid to apply")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
