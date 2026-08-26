#!/usr/bin/env python3
"""Prose statistics and tic scan for a Halstead chapter.

This is the script embedded at the end of STYLE_GUIDES.md, reconstructed into a
runnable file. That copy was pasted through a markdown escaper, which put
backslashes in front of most operators ("t \\= load(path)") and mangled the
regex character classes, so it could not run as printed. Thresholds, output
format and metric definitions are unchanged from it.

Only deliberate change: numpy is replaced with the standard library. np.median,
np.mean and np.std(ddof=1) are statistics.median, fmean and stdev exactly, so
the numbers are identical and the script has no dependencies.

    python3 style_report.py chapters/01_before.md
    python3 style_report.py chapters/01_before.md "Ch1 draft 3"
    python3 style_report.py chapters/*.md          # one report per file
"""

import re
import sys
from collections import Counter
from statistics import fmean, median, stdev

ABBR = r'(?:Mrs|Mr|Ms|Dr|St|Jr|Sr|vs|etc|[A-Z])'


def load(p):
    return open(p, encoding='utf-8').read()


def hard_breaks(t):
    """True if the text uses markdown hard line breaks to end paragraphs."""
    return any(l.endswith('  ') for l in t.split('\n') if l.strip())


def _clean(blk):
    blk = blk.strip()
    if not blk or blk == '---':
        return []
    blk = blk.replace('---', ' ').strip()
    return [re.sub(r'\s+', ' ', blk)] if blk else []


def paragraphs(t):
    """Split into paragraphs on blank lines AND on markdown hard line breaks.

    The original script split on blank lines only. Chapters 1-6 of the
    manuscript separate paragraphs with two trailing spaces and a single
    newline instead, so on those it saw one paragraph per chapter and every
    per-paragraph number was meaningless (chapter 1: "1 paras", 321
    sentences/paragraph). Splitting inside each blank-line block, rather than
    picking one convention per file, also keeps a mixed file honest, which
    HALSTEAD.md is: chapters 1-6 hard-break, 7-20 blank-line.

    A plain newline is a soft wrap and does not end a paragraph, so
    conventionally wrapped text still measures correctly.
    """
    t = re.sub(r'^#.*$', '', t, flags=re.M)
    out = []
    for blk in re.split(r'\n\s*\n', t):
        current = []
        for line in blk.split('\n'):
            current.append(line)
            if line.endswith('  '):
                out.extend(_clean(' '.join(current)))
                current = []
        if current:
            out.extend(_clean(' '.join(current)))
    return out


def sents(t):
    t = re.sub(rf'\b({ABBR})\.', r'\1<DOT>', t)
    t = re.sub(r'([.!?])(["”\']?)\s+', r'\1\2|', t)
    return [p.strip().replace('<DOT>', '.') for p in t.split('|') if p.strip()]


def words(t):
    return re.findall(r"[A-Za-z][A-Za-z']*", t)


def quoted_words(body):
    """Count words inside double quotes, counting curly quotes as quotes.

    The original scanned the whole file with '"[^"]*"'. That regex cannot see
    the 12 paragraphs of HALSTEAD.md that use curly quotes, so straight
    quotes on either side of them paired across the intervening narration and
    counted it as dialogue. The manuscript came out at 38.2% quoted against a
    ~30% target, a FAIL, when the real figure is 28.1%, a PASS.

    Normalising the curly quotes fixes that. Restarting the scan at each
    paragraph keeps any future unbalanced quote from inverting dialogue and
    narration for the whole rest of the file.
    """
    body = body.replace('“', '"').replace('”', '"')
    return sum(len(words(m))
               for para in body.split('\n')
               for m in re.findall(r'"[^"]*"', para))


def split_speech(paras):
    """Split into (spoken, narration) sentence word-counts.

    Anything inside double quotes is spoken; everything else, including the
    "she says" tags, is narration.
    """
    spoken, narration = [], []
    for p in paras:
        p = p.replace('“', '"').replace('”', '"')
        pos, told, utterances, current = 0, [], [], []
        for m in re.finditer(r'"[^"]*"', p):
            gap = p[pos:m.start()]
            told.append(gap)
            # A split quote ("A," she says, "B.") is one utterance and must be
            # rejoined. Two utterances ("A," Ruth says. "B," Sam says.) must not
            # be. The difference is whether the narration between them closes a
            # sentence. Joining every quoted span in a paragraph, as this did
            # until now, glued separate speakers together and inflated the
            # spoken mean wherever a chapter put several voices in one
            # paragraph: chapter 6 had single "sentences" 83 words long made of
            # three people talking.
            if current and re.search(r'[.!?]', gap):
                utterances.append(' '.join(current))
                current = []
            current.append(m.group(0).strip('"'))
            pos = m.end()
        if current:
            utterances.append(' '.join(current))
        told.append(p[pos:])
        for chunk in utterances:
            spoken.extend(n for n in (len(words(s)) for s in sents(chunk)) if n)
        narration.extend(
            n for n in (len(words(s)) for s in sents(' '.join(told))) if n)
    return spoken, narration


def report(path, label):
    t = load(path)
    paras = paragraphs(t)
    spp = [len(sents(p)) for p in paras]
    sl = [len(words(s)) for p in paras for s in sents(p)]
    wl = [len(w) for p in paras for w in words(p)]
    body = re.sub(r'^#.*$', '', t, flags=re.M).replace('---', ' ')
    tot = len(words(body))
    q = quoted_words(body)

    # Guards the original lacked: every statistic below divides by one of these.
    if not paras or not sl or not tot:
        print("=" * 66)
        print(f"{label} | {tot} words | {len(paras)} paras | {len(sl)} sentences")
        print("\nnot enough text to report on")
        return

    qs = 100 * q / tot
    mode = Counter(sl).most_common(1)[0][0]
    sd = stdev(sl) if len(sl) > 1 else 0.0
    cv_sl = 100 * sd / fmean(sl)

    def ok(b):
        return 'PASS' if b else 'FAIL'

    print("=" * 66)
    print(f"{label} | {tot} words | {len(paras)} paras | {len(sl)} sentences"
          f"{'  [paragraphs split on hard line breaks]' if hard_breaks(t) else ''}")
    print(f"\nWORDS/SENTENCE  mode {mode}  median {median(sl):.0f}  mean {fmean(sl):.2f}  "
          f"sd {sd:.2f}  CV {cv_sl:.1f}%  max {max(sl)}")
    print(f"  mode<median<mean  {ok(mode < median(sl) < fmean(sl))}     "
          f"mean 11-18  {ok(11 <= fmean(sl) <= 18)}     "
          f"CV 68-100%  {ok(66 <= cv_sl <= 100)}")
    for name, f, lo, hi in [('<10', lambda v: v < 10, 35, 45),
                            ('10-20', lambda v: 10 <= v <= 20, 30, 35),
                            ('20-35', lambda v: 20 < v <= 35, 15, 20),
                            ('>35', lambda v: v > 35, 0, 5)]:
        pct = 100 * sum(1 for v in sl if f(v)) / len(sl)
        print(f"  {name:>6}: {pct:5.1f}%  target {lo}-{hi}%  {ok(lo <= pct <= hi)}")

    print(f"\nQUOTED  {qs:.1f}%  target ~30%  {ok(26 <= qs <= 34)}")

    # Spoken and narration measured separately. STYLE_GUIDES.md section 6 calls
    # this "the most useful diagnostic in the whole spec" because the combined
    # number hides which half is broken, but the script never implemented it.
    spoken, narration = split_speech(paras)
    if spoken and narration:
        sp_mean, na_mean = fmean(spoken), fmean(narration)
        na_u10 = 100 * sum(1 for v in narration if v < 10) / len(narration)
        print(f"\nSPOKEN vs NARRATION")
        print(f"  spoken     mean {sp_mean:5.2f} words  ({len(spoken):4d} sentences)  "
              f"target 8-10   {ok(8 <= sp_mean <= 10)}")
        print(f"  narration  mean {na_mean:5.2f} words  ({len(narration):4d} sentences)  "
              f"target 14-17  {ok(14 <= na_mean <= 17)}")
        print(f"  narration under 10 words  {na_u10:.1f}%   target <40%  {ok(na_u10 < 40)}")

    sd_spp = stdev(spp) if len(spp) > 1 else 0.0
    cv = 100 * sd_spp / fmean(spp)
    print(f"\nSENT/PARA  mean {fmean(spp):.2f}  median {median(spp):.0f}  "
          f"sd {sd_spp:.2f}  CV {cv:.1f}%  max {max(spp)}")
    print(f"  mean 2.9-3.5 {ok(2.9 <= fmean(spp) <= 3.5)}   CV>=100% {ok(cv >= 100)}")
    print("  bucket  this   YA")
    for name, f, ya in [('1', lambda v: v == 1, 36.7),
                        ('2', lambda v: v == 2, 24.0),
                        ('3', lambda v: v == 3, 15.1),
                        ('4', lambda v: v == 4, 8.0),
                        ('5', lambda v: v == 5, 5.9),
                        ('6-7', lambda v: 6 <= v <= 7, 5.3),
                        ('8-9', lambda v: 8 <= v <= 9, 2.2),
                        ('10+', lambda v: v >= 10, 2.8)]:
        print(f"   {name:>4} {100 * sum(1 for v in spp if f(v)) / len(spp):6.1f}% {ya:6.1f}%")

    print(f"\nWORD LEN  mean {fmean(wl):.2f}   "
          f">=7 chars {100 * sum(1 for x in wl if x >= 7) / len(wl):.1f}%")

    # conjunction rates
    _w = [x.lower() for x in words(body)]
    _c = Counter(_w)
    _n = len(_w)
    print("\nCONJUNCTIONS (% of all words)")
    for k, lo, hi in [('and', 2.5, 3.5), ('but', 0.4, 0.9), ('so', 0.2, 0.6),
                      ('because', 0.2, 0.7), ('which', 0.1, 0.4)]:
        pct = 100 * _c[k] / _n
        flag = 'PASS' if lo <= pct <= hi else 'FAIL'
        print(f"  {k:<8} {_c[k]:4d}  {pct:5.2f}%   target {lo}-{hi}%   {flag}")
    _multi = sum(1 for s in [x for p in paras for x in sents(p)]
                 if len(re.findall(r'\band\b', s.lower())) >= 2)
    print(f"  sentences with 2+ 'and': {100 * _multi / len(sl):.1f}%   target <10%")

    # section breaks
    _raw = load(path)
    # The book was unified onto the underscore rule; the old '---' form is gone,
    # so this counted zero everywhere and reported PASS on every file.
    _br = len([x for x in _raw.split('\n') if set(x.strip()) == {'_'}])
    print(f"\nSECTION BREAKS  {_br}   target 2-6   "
          f"{'PASS' if 2 <= _br <= 6 else 'FAIL'}")

    # tic scan
    print("\nTIC SCAN")
    _pats = [
        (r'which is (?:the|what|how|why|a|his|her|its)\b', 'narrator evaluation'),
        (r',\s+which is ', 'trailing explanatory clause'),
        (r'\b(best|worst|funniest|nicest|only time|never once|for the first time)\b', 'superlative'),
        (r"it'?s not \w+[,;] it'?s ", 'not-X-but-Y'),
        (r'—', 'em dash'),
    ]
    _hits = 0
    for p_ in paras:
        for s in sents(p_):
            for rx, name in _pats:
                if re.search(rx, s, re.I):
                    print(f"  [{name}] {s[:110]}")
                    _hits += 1
    if not _hits:
        print("  none found")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(f"usage: {sys.argv[0]} <chapter.md> [label]")
    # One path plus an optional label, as the original took. More than one path
    # and they are all treated as files, so a glob reports on each in turn.
    if len(sys.argv) == 3 and not sys.argv[2].endswith('.md'):
        report(sys.argv[1], sys.argv[2])
    else:
        for _p in sys.argv[1:]:
            report(_p, _p.split('/')[-1])
