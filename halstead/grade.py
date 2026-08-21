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

LEXILE_TARGET = 1000

# The reading grade rises with Chloe's age instead of sitting flat across the
# book. Each band is (first chapter, last chapter, floor, ceiling-of-intent).
# The floor is what the band should reach; the second number is where the band
# stops being worth pushing. A chapter already above its band is left alone.
FK_BANDS = [
    (1, 10, 5.5, 7.0),   # ages 6-8, home and the first year
    (11, 15, 6.0, 7.0),  # ages 8-12
    (16, 22, 7.0, 8.0),  # ages 13-19
    (23, 35, 8.0, 99.0),  # adult
]
FK_BOOK_TARGET = 7.0


def fk_band(stem):
    """The (floor, ceiling) this chapter's number is judged against."""
    try:
        n = int(stem[:2])
    except ValueError:
        return None
    for lo, hi, floor, ceil in FK_BANDS:
        if lo <= n <= hi:
            return floor, ceil
    return None


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
    ("_words_all", "word count",                 (2000, 4000), "~",  "author, transcript included"),
    ("fk",       "reading grade (Flesch-Kincaid)", 9.0,        ">=", "author, see band"),
    ("lexile",   "Lexile (approx)",               1000,        ">=", "author"),
    ("ari",      "reading grade (ARI)",           9.0,         ">=", "author, tracks F-K"),
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


def dialogue_share(path):
    """Share of words inside quotation marks, and the spoken-sentence count.

    The spoken mean is blind to the worst failure available. A chapter that
    narrates every exchange - "the sergeant tells him", "what the debrief tells
    him" - has no quoted sentences to measure, so it scores nothing at all, and
    a chapter with five spoken sentences can post a better mean than a chapter
    with two hundred. Chapter 26 measured 17.0 off five sentences while being
    four per cent dialogue. Always read the share and the count beside the mean.
    """
    import statistics as _st
    spec2 = importlib.util.spec_from_file_location("ds", HERE / "dialogue_study.py")
    ds = importlib.util.module_from_spec(spec2)
    import sys as _sys
    _argv, _sys.argv = _sys.argv, ["x"]
    try:
        spec2.loader.exec_module(ds)
    finally:
        _sys.argv = _argv
    t = Path(path).read_text(encoding="utf-8")
    t, _ = ds.pg.strip_transcript(t)
    sp, na = ds.spoken_and_narrated(t)
    sl = ds.sent_lengths(sp)
    sw, nw = len(ds.pg.words(sp)), len(ds.pg.words(na))
    if not (sw + nw):
        return None
    return {"quoted": 100 * sw / (sw + nw),
            "spoken": _st.fmean(sl) if sl else None,
            "n": len(sl),
            "short": 100 * sum(1 for x in sl if x <= 3) / len(sl) if sl else None}


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

    band = fk_band(name)
    failed = []
    for key, label, goal, cmp_, src in GOALS:
        if band and key in ("fk", "ari"):
            goal, src = band[0], f"band {band[0]:g}-{band[1]:g} for this chapter"
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

    d = dialogue_share(path)
    pgm = load("prose_grade.py")
    tshare = (pgm.measure(Path(path).read_text(encoding="utf-8"), floor=10)
              or {}).get("_transcript", 0)
    if d and tshare >= 25:
        # A chat chapter carries its dialogue as transcript lines, which are
        # stripped before measurement, so the quoted-share and spoken-mean
        # gates below are measuring the handful of lines that happen to sit in
        # quotation marks. Chapter 32 scored 0.2% quoted and a spoken mean of
        # 2.0 while being mostly people talking to each other.
        print("  " + "-" * 84)
        print(f"  dialogue measures skipped: {tshare:.0f}% of this chapter is chat")
        print("  transcript, which is stripped before measurement, so quoted share")
        print("  and spoken mean would describe a few stray lines rather than the")
        print("  chapter. Read the transcript itself.")
        d = None
    if d:
        print("  " + "-" * 84)
        print(f"  {'dialogue, share of words quoted %':<40}{d['quoted']:9.1f}{'>= 15':>14}  "
              f"{'pass' if d['quoted'] >= 15 else 'FAIL':<6}corpus talky books 25-39")
        if d["spoken"] is not None:
            print(f"  {'mean spoken sentence, words':<40}{d['spoken']:9.1f}{'>= 16':>14}  "
                  f"{'pass' if d['spoken'] >= 16 else 'FAIL':<6}author")
            print(f"  {'spoken lines of 1-3 words %':<40}{d['short']:9.1f}{'<= 8':>14}  "
                  f"{'pass' if d['short'] <= 8 else 'FAIL':<6}author")
        if d["n"] < 20:
            print(f"\n  ** Only {d['n']} spoken sentences in this chapter. The mean above is")
            print("     measured over almost nothing and means almost nothing. A chapter this")
            print("     quiet has usually narrated its dialogue instead of writing it; check")
            print("     the narration for 'he tells her', 'she asks him whether', and the like.")
    print("  " + "-" * 84)
    if band:
        print(f"\n  Reading grade is judged against this chapter's band, not one")
        print(f"  book-wide number: floor {band[0]:g}, and past {band[1]:g} it stops being")
        print(f"  worth pushing. A chapter already above its band is left alone.")
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
    """Distance to the author's targets, per band and for the book."""
    pg = load("prose_grade.py")
    rule("2. AGAINST TARGET (reading grade by band, Lexile %d)" % LEXILE_TARGET)

    rows = []
    for p in CHAPTERS:
        m = pg.measure(p.read_text(encoding="utf-8"), floor=10)
        if m:
            rows.append((p.stem, m["fk"], m["lexile"]))
    whole = pg.measure(BOOK.read_text(encoding="utf-8"))

    print(f"\n  book       F-K {whole['fk']:5.1f}   Lexile {whole['lexile']:7.1f}")
    print(f"  target     F-K {FK_BOOK_TARGET:5.1f}   Lexile {LEXILE_TARGET:7.1f}")
    print(f"  gap        F-K {whole['fk'] - FK_BOOK_TARGET:+5.1f}   "
          f"Lexile {whole['lexile'] - LEXILE_TARGET:+7.1f}")

    print("\n  The reading grade is meant to climb with Chloe's age rather than sit")
    print("  flat, so each band is judged on its own average, not against one number.\n")
    print(f"  {'band':<12}{'chapters':<12}{'floor':>7}{'average':>9}{'':>3}{'under floor'}")
    print("  " + "-" * 62)

    for lo, hi, floor, ceil in FK_BANDS:
        got = [r for r in rows if lo <= int(r[0][:2]) <= hi]
        if not got:
            continue
        avg = sum(r[1] for r in got) / len(got)
        low = sorted((r for r in got if r[1] < floor), key=lambda r: r[1])
        mark = "" if avg >= floor else "  <-- band under floor"
        names = ", ".join(f"{r[0][:2]} ({r[1]:.1f})" for r in low) or "none"
        print(f"  {str(lo) + '-' + str(hi):<12}{len(got):<12}{floor:>7.1f}{avg:>9.2f}{mark}")
        print(f"  {'':<12}{'':<12}{'':>7}{'':>9}   {names}")

    print("\n  A chapter already above its band is left where it is. The bands are")
    print("  floors for the band average, not per-chapter quotas, and a chapter with")
    print("  a structural reason to sit low (chapter 20's protected fight holds 57%")
    print("  of its sentences) is allowed to.")


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
