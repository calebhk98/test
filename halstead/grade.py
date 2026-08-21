#!/usr/bin/env python3
"""One command for the whole picture: readability, style, numbers, voice, integrity.

The measurements live in five scripts that grew separately and each answer one
question. This runs all of them, in a fixed order, with the arguments that make
them comparable, so there is one thing to run and one report to read.

    python3 grade.py                 the whole report
    python3 grade.py --table         just the per-chapter table
    python3 grade.py --targets       just the table plus the distance to target
    python3 grade.py --brief         drop the slow sections (voice, citations)

What comes from where:

  prose_grade.py       sixteen measures graded as percentiles against 23 real
                       books, plus Flesch-Kincaid, ARI and an approximate
                       Lexile. This is the spine of the report.
  style_report.py      the two things prose_grade does not measure: how much of
                       a chapter is dialogue, and how far spoken and narrated
                       sentence lengths sit apart. Its PASS/FAIL thresholds are
                       invented and are deliberately not reproduced here.
  number_report.py     whether the same handful of numbers keeps recurring.
  voice_separation.py  whether each character's dialogue is distinguishable
                       from everyone else's.
  verify_citations.py  quotations in the character sheets that are not in the
                       manuscript.
  prose_check.py       PROSE_RULES violations in the character sheets.
  check_edits.py       em dashes and the hard-line-break convention.

Targets are the author's: Flesch-Kincaid about 7, Lexile about 1000. The
corpus median is shown beside them because a target with nothing to compare it
against is a number somebody made up.
"""

import argparse
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHAPTERS = sorted((HERE / "chapters").glob("*.md"))
BOOK = HERE / "HALSTEAD.md"

FK_TARGET = 7.0
LEXILE_TARGET = 1000


def load(name):
    spec = importlib.util.spec_from_file_location(name[:-3], HERE / name)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run(script, *args, quiet_rc=True):
    """Run one of the sibling scripts and return its stdout.

    Several of them exit non-zero when they find something, which is correct
    behaviour and not a failure, so the return code is ignored by default.
    """
    r = subprocess.run([sys.executable, str(HERE / script), *map(str, args)],
                       capture_output=True, text=True)
    if r.returncode and not quiet_rc:
        return f"({script} exited {r.returncode})\n{r.stdout}{r.stderr}"
    return r.stdout.rstrip("\n")


def rule(title):
    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")



# metric -> (label, goal, comparison, source of the goal)
#   ">=" pass at or above, "<=" pass at or below, "~" pass within the band
GOALS = [
    ("_words",   "word count",                   (2000, 3400), "~",  "author"),
    ("fk",       "reading grade (Flesch-Kincaid)", 7.0,        ">=", "author"),
    ("lexile",   "Lexile (approx)",               1000,        ">=", "author"),
    ("ari",      "reading grade (ARI)",           6.0,         ">=", "corpus 5.2, rounded up"),
    ("wps",      "words per sentence",            14.3,        ">=", "corpus median"),
    ("slcv",     "sentence-length variation CV",  85.3,        ">=", "corpus median"),
    ("wpp",      "words per paragraph",           (22, 48),    "~",  "corpus median 33.7"),
    ("spp",      "sentences per paragraph",       (1.8, 3.2),  "~",  "corpus median 2.4"),
    ("wlen",     "mean word length",              4.1,         ">=", "corpus median"),
    ("long7",    "words of 7+ characters %",      13.2,        ">=", "corpus median"),
    ("sttr",     "lexical diversity sTTR",        40.7,        ">=", "corpus median"),
    ("top100",   "commonest-100 words %",         48.1,        "<=", "corpus median"),
    ("commas",   "commas per sentence",           0.9,         ">=", "corpus median"),
    ("subord",   "sentences with subordination %", 22.2,       ">=", "corpus median"),
    ("relcl",    "sentences with a relative clause %", (14, 26), "~", "corpus median 19.5"),
    ("simple",   "clause-free sentences %",       65.9,        "<=", "corpus median"),
    ("u10",      "sentences under 10 words %",    45.7,        "<=", "corpus median"),
    ("b2035",    "sentences of 20-35 words %",    15.9,        ">=", "corpus median"),
    ("shortruns","sentences in a run of 3+ short %", 17.1,     "<=", "corpus median"),
    ("negative", "negative-space sentences %",    5.0,         "<=", "author"),
    ("front",    "sentences opening on a subordinate clause %", (0.5, 3.0), "~", "corpus median 1.6"),
    ("andrate",  '"and" as a share of words %',   3.3,         "<=", "corpus median"),
]


def one_chapter(path):
    """One chapter down the page instead of across it.

    The wide table has twenty-seven columns and adjacent ones are easy to
    confuse; an agent working chapter 22 read the and-rate column as the
    negative-space column and reported a fall where there had been a rise.
    This format has one metric per line with its goal beside it, so there is
    nothing to miscount.
    """
    pg = load("prose_grade.py")
    text = Path(path).read_text(encoding="utf-8")
    m = pg.measure(text, floor=10)
    if not m:
        sys.exit(f"{path}: too short to measure")

    name = Path(path).stem
    print("\n" + name + "\n" + "-" * len(name) + "\n")
    print(f"  {'metric':<40}{'value':>9}{'goal':>14}  {'':<6}{'goal from'}")
    print("  " + "-" * 84)

    failed = []
    for key, label, goal, cmp_, src in GOALS:
        v = m.get(key)
        if v is None:
            print(f"  {label:<40}{'-':>9}{'':>14}  {'':<6}{src}")
            continue
        if cmp_ == "~":
            lo, hi = goal
            ok = lo <= v <= hi
            gtxt = f"{lo:g} to {hi:g}"
        elif cmp_ == ">=":
            ok = v >= goal
            gtxt = f">= {goal:g}"
        else:
            ok = v <= goal
            gtxt = f"<= {goal:g}"
        mark = "pass" if ok else "FAIL"
        if not ok:
            failed.append(label)
        print(f"  {label:<40}{v:9.1f}{gtxt:>14}  {mark:<6}{src}")

    print("  " + "-" * 84)
    print("\n  %d of %d at goal." % (len(GOALS) - len(failed), len(GOALS)))
    if failed:
        print("  short on: " + ", ".join(failed))
    print("\n  A FAIL is a prompt to look, not an instruction to change the number.")
    print("  Several of these goals are the corpus median, which half of 23 real")
    print("  books sit below. A chapter can be right and still fail three of them.")


def table():
    rule("1. EVERY MEASURE, ONE ROW PER CHAPTER")
    print(run("prose_grade.py", "--summary", *CHAPTERS))


def targets():
    """Distance to the author's targets, per chapter and for the book."""
    pg = load("prose_grade.py")
    rule(f"2. AGAINST TARGET (Flesch-Kincaid {FK_TARGET}, Lexile {LEXILE_TARGET})")

    rows = []
    for p in CHAPTERS:
        m = pg.measure(p.read_text(encoding="utf-8"), floor=10)
        if m:
            rows.append((p.stem, m["fk"], m["lexile"]))
    whole = pg.measure(BOOK.read_text(encoding="utf-8"))

    under = [r for r in rows if r[1] < FK_TARGET - 1]
    print(f"\n  book       F-K {whole['fk']:5.1f}   Lexile {whole['lexile']:7.1f}")
    print(f"  target     F-K {FK_TARGET:5.1f}   Lexile {LEXILE_TARGET:7.1f}")
    print(f"  gap        F-K {whole['fk'] - FK_TARGET:+5.1f}   "
          f"Lexile {whole['lexile'] - LEXILE_TARGET:+7.1f}")

    print(f"\n  {len(under)} of {len(rows)} chapters are more than a grade under "
          f"the Flesch-Kincaid target:\n")
    for name, fk, lx in sorted(under, key=lambda r: r[1]):
        bar = "#" * int(round((FK_TARGET - fk) * 4))
        print(f"    {name:<24}{fk:5.1f}  {lx:7.1f}  {bar}")
    print("\n  Flesch-Kincaid counts syllables per word; Lexile counts how common the")
    print("  words are. This book writes fairly long sentences out of short, ordinary")
    print("  words, so it scores far better on Lexile than on Flesch-Kincaid. Closing")
    print("  the Flesch-Kincaid gap means longer words, and in the early chapters that")
    print("  costs the child narrator. Weigh it per chapter, not book-wide.")


def grade_vs_corpus():
    rule("3. GRADED AGAINST THE CORPUS")
    print(run("prose_grade.py", BOOK))


def dialogue():
    """Dialogue share and the spoken/narration split, per chapter.

    style_report prints these alongside PASS/FAIL against thresholds that have
    no source behind them. The numbers are worth having; the verdicts are not,
    so only the numbers are pulled through.
    """
    rule("4. DIALOGUE SHARE AND THE SPOKEN / NARRATION SPLIT")
    print(f"\n  {'chapter':<24}{'quoted':>8}{'spoken':>9}{'narration':>11}{'gap':>7}")
    print("  " + "-" * 57)
    q_all, gaps = [], []
    for p in CHAPTERS:
        out = run("style_report.py", p)
        q = re.search(r"QUOTED\s+([\d.]+)%", out)
        sp = re.search(r"spoken\s+mean\s+([\d.]+) words", out)
        na = re.search(r"narration\s+mean\s+([\d.]+) words", out)
        if not (q and sp and na):
            continue
        qv, sv, nv = float(q.group(1)), float(sp.group(1)), float(na.group(1))
        q_all.append(qv)
        gaps.append(nv - sv)
        print(f"  {p.stem:<24}{qv:7.1f}%{sv:9.1f}{nv:11.1f}{nv - sv:7.1f}")
    if q_all:
        import statistics as st
        print("  " + "-" * 57)
        print(f"  {'median':<24}{st.median(q_all):7.1f}%"
              f"{'':9}{'':11}{st.median(gaps):7.1f}")
    print("\n  quoted    share of words inside quotation marks")
    print("  gap       narration mean minus spoken mean, in words. A wide gap is")
    print("            ordinary; a gap near zero means the narration has gone as")
    print("            clipped as the dialogue.")


def numbers():
    rule("5. NUMBERS")
    print(run("number_report.py", BOOK))


def voice():
    rule("6. VOICE SEPARATION")
    print(run("voice_separation.py", "--prose"))
    print(run("voice_separation.py", "--chat"))


def integrity():
    rule("7. INTEGRITY")
    for label, script, args in (
            ("Character-sheet quotations not found in the manuscript",
             "verify_citations.py", ()),
            ("PROSE_RULES violations in the character sheets",
             "prose_check.py", ()),
            ("Em dashes and the hard-line-break convention",
             "check_edits.py", ())):
        out = run(script, *args)
        tail = [l for l in out.split("\n") if l.strip()][-3:]
        print(f"\n  {label}")
        for l in tail:
            print(f"    {l}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--table", action="store_true", help="only the per-chapter table")
    ap.add_argument("--targets", action="store_true", help="only the table and targets")
    ap.add_argument("--brief", action="store_true",
                    help="skip voice separation and citation checking")
    ap.add_argument("--one", metavar="CHAPTER",
                    help="one chapter, down the page, each metric against its goal")
    a = ap.parse_args()

    if a.one:
        return one_chapter(a.one)

    if not BOOK.exists():
        sys.exit(f"{BOOK.name} is missing; run build_manuscript.py first")

    table()
    if a.table:
        return
    targets()
    if a.targets:
        return
    grade_vs_corpus()
    dialogue()
    numbers()
    if not a.brief:
        voice()
    integrity()
    print()


if __name__ == "__main__":
    main()
