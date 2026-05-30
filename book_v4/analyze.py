#!/usr/bin/env python3
"""
Fiction Paragraph Structure Analyzer
Compares your manuscript chapters against a baseline of 26 classic novels.

Place this script in book_v4/
Run:  python3 analyze.py
Output:  analysis_output.png  (comparison charts)
         analysis_summary.txt (text report)

Dependencies: pip install nltk matplotlib numpy
"""

import re
import sys
import textwrap
from pathlib import Path
from collections import Counter, defaultdict

# ── Dependency check ─────────────────────────────────────────────
try:
    import nltk
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec
    import numpy as np
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Run:  pip install nltk matplotlib numpy")
    sys.exit(1)

# Download NLTK sentence tokenizer quietly
for pkg in ('punkt', 'punkt_tab'):
    try:
        nltk.data.find(f'tokenizers/{pkg}')
    except LookupError:
        nltk.download(pkg, quiet=True)

# ── BASELINE DATA (78,774 paragraphs, 26 classic novels) ─────────
# Source: Project Gutenberg corpus analysis

BASELINE = {
    # % of paragraphs with exactly N sentences (key 11 = "11+")
    "sent_per_para": {
        1: 38.57, 2: 23.74, 3: 13.30, 4: 7.98,  5: 4.91,
        6:  3.28, 7:  2.11, 8:  1.61, 9: 1.06, 10: 0.73, 11: 2.71
    },
    # % of words in paragraphs of each sentence-count bin
    "words_in_para_bin": {
        1: 14.14, 2: 15.13, 3: 13.33, 4: 11.20, 5: 8.71,
        6:  7.18, 7:  5.47, 8:  4.71, 9:  3.47, 10: 2.69, 11: 13.98
    },
    # % of sentences in each word-count range
    "words_per_sent": [
        ("1-5",   13.45), ("6-10",  21.95), ("11-15", 16.76),
        ("16-20", 12.76), ("21-25",  9.60), ("26-30",  7.15),
        ("31-40",  8.86), ("41-50",  4.51), ("51+",    4.94),
    ],
    "sent_mean":   19.48,
    "sent_median": 15,
    # Quote ratio in 1-sentence dialogue paragraphs (low→high quoted %)
    "quote_ratio_1sent": [
        ("0-10%\n(tag-heavy)",      2.0),
        ("10-30%",                   8.3),
        ("30-50%\n(balanced)",      10.1),
        ("50-70%",                  15.8),
        ("70-90%\n\"Help!\" she said.", 21.7),
        ('90-100%\n"HELP." bare quote', 42.1),
    ],
    # Individual quote length distribution
    "quote_lengths": [
        ("1-3w", 17.4), ("4-7w", 24.0), ("8-12w", 18.9),
        ("13-20w", 13.8), ("21-35w", 11.5), ("36+w", 14.4),
    ],
    "quote_len_median": 9,
    "quote_len_mean":   20.7,
}

# ── QUOTE DETECTION ───────────────────────────────────────────────
# Supports ASCII double quotes, curly double quotes, and single curly quotes.
OPEN_Q  = r'["\u201c\u2018]'
CLOSE_Q = r'["\u201d\u2019]'
QUOTE_RE = re.compile(r'(?:"|")(.*?)(?:"|")', re.DOTALL)


def extract_quotes(text):
    """Return list of strings found inside quote marks."""
    # Try curly first, fall back to ASCII
    curly = re.findall('\u201c(.*?)\u201d', text, re.DOTALL)
    if curly:
        return curly
    return re.findall(r'"(.*?)"', text, re.DOTALL)


# ── WORD COUNT ────────────────────────────────────────────────────
def wc(text):
    return len(re.findall(r"\b\w+(?:'\w+)?\b", text))


# ── MARKDOWN CLEANING ─────────────────────────────────────────────
def clean_markdown(text):
    """Strip markdown formatting, return plain prose text."""
    # Remove fenced code blocks
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'`[^`]+`', '', text)
    # Remove HTML tags if any
    text = re.sub(r'<[^>]+>', '', text)
    # Remove images
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    # Remove links but keep text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # Remove bold/italic markers (**, __, *, _)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'__([^_]+)__',     r'\1', text)
    text = re.sub(r'\*([^*]+)\*',     r'\1', text)
    text = re.sub(r'_([^_]+)_',       r'\1', text)
    # Remove horizontal rules
    text = re.sub(r'^[ \t]*[-*_]{3,}[ \t]*$', '', text, flags=re.MULTILINE)
    return text


def is_heading(line):
    """True if this line is a markdown heading."""
    return bool(re.match(r'^#{1,6}\s', line.strip()))


def is_junk(para):
    """Filter out non-prose paragraphs."""
    s = para.strip()
    if len(s) < 20:
        return True
    if is_heading(s):
        return True
    # Scene break markers (* * *, ----, etc.)
    if re.match(r'^[*\-_\s]+$', s):
        return True
    # All-caps short lines (chapter labels)
    if s.isupper() and len(s) < 80:
        return True
    # Roman numeral / number only
    if re.match(r'^[IVXLCDM\d\.]+\s*$', s):
        return True
    return False


# ── PARSE A SINGLE .MD FILE ───────────────────────────────────────
def parse_file(path):
    """
    Returns list of paragraph dicts:
      ns       - number of sentences
      tw       - total words
      nq       - number of quote segments
      qw       - words inside quotes
      tagw     - words outside quotes
      qr       - quote ratio (qw / tw)
      qwcs     - list of per-quote word counts
      sent_wcs - list of per-sentence word counts
    """
    raw = path.read_text(encoding='utf-8', errors='replace')
    raw = clean_markdown(raw)

    records = []
    for para in re.split(r'\n{2,}', raw):
        # Flatten internal newlines (continuation lines)
        para = re.sub(r'\n', ' ', para).strip()
        para = re.sub(r'  +', ' ', para)

        if not para or len(para) < 20 or is_junk(para):
            continue
        # Skip lines that begin with # (heading that survived cleaning)
        if re.match(r'^#+\s', para):
            continue

        sents    = [s for s in nltk.sent_tokenize(para) if len(s.strip()) > 5]
        if not sents:
            continue

        sent_wcs  = [wc(s) for s in sents]
        n_sents   = len(sents)
        total_wc  = wc(para)

        quote_texts = extract_quotes(para)
        quote_wcs   = [wc(q) for q in quote_texts]
        n_quotes    = len(quote_wcs)
        quoted_wc   = sum(quote_wcs)
        tag_wc      = total_wc - quoted_wc
        quote_ratio = quoted_wc / total_wc if total_wc else 0.0

        records.append({
            "ns":       n_sents,
            "tw":       total_wc,
            "nq":       n_quotes,
            "qw":       quoted_wc,
            "tagw":     tag_wc,
            "qr":       quote_ratio,
            "qwcs":     quote_wcs,
            "sent_wcs": sent_wcs,
        })

    return records


# ── AGGREGATE STATS FROM RECORDS ──────────────────────────────────
def aggregate(records):
    all_sent_counts = [r["ns"]  for r in records]
    all_sent_wcs    = [w for r in records for w in r["sent_wcs"]]
    all_words       = [r["tw"]  for r in records]
    dlg_records     = [r for r in records if r["nq"] > 0]
    one_sent_dlg    = [r for r in dlg_records if r["ns"] == 1]
    all_qwcs        = [w for r in records for w in r["qwcs"]]

    total_paras = len(records)
    total_sents = len(all_sent_wcs)
    total_words = sum(all_words)

    # Sentences per paragraph
    spp_counter = Counter(all_sent_counts)
    spp_dist = {}
    for i in range(1, 11):
        spp_dist[i] = spp_counter.get(i, 0) / total_paras * 100
    spp_dist[11] = sum(v for k, v in spp_counter.items() if k > 10) / total_paras * 100

    # Words per paragraph bin
    word_bin_totals = defaultdict(int)
    for r in records:
        b = min(r["ns"], 11)
        word_bin_totals[b] += r["tw"]
    wpb_dist = {k: v / total_words * 100 for k, v in word_bin_totals.items()}

    # Words per sentence ranges
    wps_ranges = [(1,5),(6,10),(11,15),(16,20),(21,25),(26,30),(31,40),(41,50),(51,9999)]
    wps_labels = ["1-5","6-10","11-15","16-20","21-25","26-30","31-40","41-50","51+"]
    wps_dist = []
    for (lo, hi), lab in zip(wps_ranges, wps_labels):
        pct = sum(1 for w in all_sent_wcs if lo <= w <= hi) / total_sents * 100
        wps_dist.append((lab, pct))

    sent_mean   = sum(all_sent_wcs) / total_sents if total_sents else 0
    sent_median = sorted(all_sent_wcs)[total_sents // 2] if all_sent_wcs else 0

    # Quote ratio in 1-sentence dialogue paras
    qr_bins = [(0,.10),(0.10,.30),(0.30,.50),(0.50,.70),(0.70,.90),(0.90,1.01)]
    qr_labels = ['0-10%\n(tag-heavy)','10-30%','30-50%\n(balanced)',
                 '50-70%','70-90%\n"Help!" she said.',
                 '90-100%\n"HELP." bare quote']
    qr_dist = []
    n1d = len(one_sent_dlg)
    for (lo, hi), lab in zip(qr_bins, qr_labels):
        pct = sum(1 for r in one_sent_dlg if lo <= r["qr"] < hi) / n1d * 100 if n1d else 0
        qr_dist.append((lab, pct))

    # Individual quote lengths
    ql_ranges  = [(1,3),(4,7),(8,12),(13,20),(21,35),(36,9999)]
    ql_labels  = ["1-3w","4-7w","8-12w","13-20w","21-35w","36+w"]
    nq_total   = len(all_qwcs)
    ql_dist = []
    for (lo, hi), lab in zip(ql_ranges, ql_labels):
        pct = sum(1 for w in all_qwcs if lo <= w <= hi) / nq_total * 100 if nq_total else 0
        ql_dist.append((lab, pct))

    ql_mean   = sum(all_qwcs) / nq_total if nq_total else 0
    ql_median = sorted(all_qwcs)[nq_total // 2] if all_qwcs else 0

    return {
        "total_paras":  total_paras,
        "total_sents":  total_sents,
        "total_words":  total_words,
        "spp_dist":     spp_dist,
        "wpb_dist":     wpb_dist,
        "wps_dist":     wps_dist,
        "sent_mean":    sent_mean,
        "sent_median":  sent_median,
        "qr_dist":      qr_dist,
        "n_1sent_dlg":  n1d,
        "ql_dist":      ql_dist,
        "ql_mean":      ql_mean,
        "ql_median":    ql_median,
        "dlg_para_pct": len(dlg_records) / total_paras * 100 if total_paras else 0,
    }


# ── CHART BUILDING ────────────────────────────────────────────────
TEXT   = "#e8e8e8"
GRID   = "#2a2a3a"
BG     = "#1a1d27"
YOUR   = "#e07b54"   # amber  - your book
BASE   = "#5b9bd5"   # blue   - baseline
GREEN  = "#6abf69"

def style(ax):
    ax.set_facecolor(BG)
    ax.tick_params(colors=TEXT, labelsize=8)
    for sp in ax.spines.values():
        sp.set_color(GRID)
    ax.yaxis.grid(True, color=GRID, linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)


def make_charts(stats, output_path):
    fig = plt.figure(figsize=(16, 16), facecolor="#0f1117")
    gs  = gridspec.GridSpec(3, 2, figure=fig,
                            height_ratios=[1.0, 1.0, 1.0],
                            hspace=0.50, wspace=0.35)

    W = 0.38

    # ── 1: Sentences per paragraph ───────────────────────────────
    ax1 = fig.add_subplot(gs[0, :])
    style(ax1)

    bins = list(range(1, 12))
    xlabs = [str(i) for i in range(1, 11)] + ["11+"]
    x  = np.arange(len(bins))
    b_vals = [BASELINE["sent_per_para"].get(i, 0) for i in bins]
    y_vals = [stats["spp_dist"].get(i, 0)          for i in bins]

    bars_b = ax1.bar(x - W/2, b_vals, width=W, color=BASE,  alpha=0.85,
                     label="Baseline (26 classic novels)", edgecolor="#0f1117", lw=0.6)
    bars_y = ax1.bar(x + W/2, y_vals, width=W, color=YOUR, alpha=0.85,
                     label="Your manuscript", edgecolor="#0f1117", lw=0.6)

    ax1.set_xticks(x)
    ax1.set_xticklabels(xlabs, color=TEXT)
    ax1.set_ylabel("% of paragraphs", color=TEXT, fontsize=10)
    ax1.set_xlabel("Sentences per paragraph", color=TEXT, fontsize=10)
    ax1.set_title(
        f"Sentences per Paragraph\n"
        f"Your manuscript: {stats['total_paras']:,} paragraphs  |  "
        f"Baseline: 78,774 paragraphs across 26 novels",
        color=TEXT, fontsize=12, fontweight="bold", pad=10)
    ax1.legend(fontsize=9, facecolor=BG, edgecolor=GRID, labelcolor=TEXT)

    for bar, pct in zip(bars_y, y_vals):
        if pct > 1.0:
            ax1.text(bar.get_x() + bar.get_width()/2, pct + 0.2,
                     f"{pct:.1f}%", ha="center", va="bottom",
                     color=YOUR, fontsize=7.5)
    for bar, pct in zip(bars_b, b_vals):
        if pct > 1.0:
            ax1.text(bar.get_x() + bar.get_width()/2, pct + 0.2,
                     f"{pct:.1f}%", ha="center", va="bottom",
                     color=BASE, fontsize=7.5)

    # ── 2: Words per sentence ─────────────────────────────────────
    ax2 = fig.add_subplot(gs[1, :])
    style(ax2)

    wps_labs = [r[0] for r in BASELINE["words_per_sent"]]
    b_wps    = [r[1] for r in BASELINE["words_per_sent"]]
    y_wps    = [r[1] for r in stats["wps_dist"]]
    xw       = np.arange(len(wps_labs))

    ax2.plot(xw, b_wps, color=BASE,  linewidth=2.2, marker="o", markersize=5,
             label=f"Baseline  (mean {BASELINE['sent_mean']:.1f}w, median {BASELINE['sent_median']}w)")
    ax2.plot(xw, y_wps, color=YOUR, linewidth=2.2, marker="o", markersize=5,
             label=f"Your manuscript  (mean {stats['sent_mean']:.1f}w, median {stats['sent_median']}w)")
    ax2.fill_between(xw, b_wps, y_wps,
                     where=[y > b for y, b in zip(y_wps, b_wps)],
                     alpha=0.15, color=YOUR)
    ax2.fill_between(xw, b_wps, y_wps,
                     where=[b >= y for y, b in zip(y_wps, b_wps)],
                     alpha=0.15, color=BASE)

    ax2.set_xticks(xw)
    ax2.set_xticklabels(wps_labs, color=TEXT)
    ax2.set_ylabel("% of sentences", color=TEXT, fontsize=10)
    ax2.set_xlabel("Words per sentence", color=TEXT, fontsize=10)
    ax2.set_title("Words per Sentence Distribution", color=TEXT,
                  fontsize=12, fontweight="bold", pad=10)
    ax2.legend(fontsize=9, facecolor=BG, edgecolor=GRID, labelcolor=TEXT)

    # ── 3: Quote ratio in 1-sent dialogue paras ───────────────────
    ax3 = fig.add_subplot(gs[2, 0])
    style(ax3)

    qr_labs  = [r[0] for r in BASELINE["quote_ratio_1sent"]]
    b_qr     = [r[1] for r in BASELINE["quote_ratio_1sent"]]
    y_qr     = [r[1] for r in stats["qr_dist"]]
    xqr      = np.arange(len(qr_labs))

    ax3.bar(xqr - W/2, b_qr, width=W, color=BASE,  alpha=0.85, label="Baseline",
            edgecolor="#0f1117", lw=0.6)
    ax3.bar(xqr + W/2, y_qr, width=W, color=YOUR, alpha=0.85, label="Your manuscript",
            edgecolor="#0f1117", lw=0.6)
    ax3.set_xticks(xqr)
    ax3.set_xticklabels(qr_labs, color=TEXT, fontsize=7.5)
    ax3.set_ylabel("% of 1-sentence dialogue paras", color=TEXT, fontsize=9)
    ax3.set_title(
        f"Quote Ratio in 1-Sentence Dialogue Paras\n"
        f"(n={stats['n_1sent_dlg']:,} in your manuscript)",
        color=TEXT, fontsize=10, fontweight="bold", pad=8)
    ax3.legend(fontsize=8, facecolor=BG, edgecolor=GRID, labelcolor=TEXT)

    # ── 4: Individual quote lengths ───────────────────────────────
    ax4 = fig.add_subplot(gs[2, 1])
    style(ax4)

    ql_labs  = [r[0] for r in BASELINE["quote_lengths"]]
    b_ql     = [r[1] for r in BASELINE["quote_lengths"]]
    y_ql     = [r[1] for r in stats["ql_dist"]]
    xql      = np.arange(len(ql_labs))

    ax4.bar(xql - W/2, b_ql, width=W, color=BASE,  alpha=0.85, label="Baseline",
            edgecolor="#0f1117", lw=0.6)
    ax4.bar(xql + W/2, y_ql, width=W, color=YOUR, alpha=0.85, label="Your manuscript",
            edgecolor="#0f1117", lw=0.6)
    ax4.set_xticks(xql)
    ax4.set_xticklabels(ql_labs, color=TEXT)
    ax4.set_ylabel("% of all quotes", color=TEXT, fontsize=9)
    ax4.set_title(
        f"Individual Quote Length Distribution\n"
        f"Baseline: median 9w, mean 20.7w  |  "
        f"Yours: median {stats['ql_median']}w, mean {stats['ql_mean']:.1f}w",
        color=TEXT, fontsize=10, fontweight="bold", pad=8)
    ax4.legend(fontsize=8, facecolor=BG, edgecolor=GRID, labelcolor=TEXT)

    fig.text(0.5, 0.005,
             "Baseline: 26 novels, Project Gutenberg (1811-1925) · "
             "Quotes detected via curly/ASCII double-quote pairs · "
             "Sentences via NLTK",
             ha="center", fontsize=7, color="#888888")

    plt.savefig(output_path, dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    print(f"  Chart saved: {output_path}")


# ── TEXT SUMMARY ─────────────────────────────────────────────────
def print_summary(stats, file_count):
    lines = []
    div   = "=" * 60

    def row(label, yours, baseline, unit=""):
        diff = yours - baseline
        flag = " ◄ HIGH" if diff > 8 else (" ◄ LOW" if diff < -8 else "")
        lines.append(f"  {label:<30s} {yours:>6.1f}{unit}  (baseline {baseline:>5.1f}{unit}){flag}")

    lines += [
        "  FICTION STRUCTURE ANALYSIS",
        f"  {file_count} chapter file(s) analyzed",
        f"  {stats['total_paras']:,} paragraphs · {stats['total_sents']:,} sentences · "
        f"{stats['total_words']:,} words",
        div,
        "",
        "  SENTENCES PER PARAGRAPH",
        "  (>8pp difference flagged)",
    ]
    for i in range(1, 12):
        if i == 1:
            lab = "1 sentence"
        elif i < 11:
            lab = f"{i} sentences"
        else:
            lab = "11+ sentences"
        row(lab, stats["spp_dist"].get(i, 0),
            BASELINE["sent_per_para"].get(i, 0), "%")

    lines += [
        "",
        "  WORDS PER SENTENCE",
    ]
    for (lab, y_pct), (_, b_pct) in zip(stats["wps_dist"], BASELINE["words_per_sent"]):
        row(lab, y_pct, b_pct, "%")
    row("Mean words/sentence",   stats["sent_mean"],   BASELINE["sent_mean"],   "w")
    row("Median words/sentence", stats["sent_median"], BASELINE["sent_median"], "w")

    lines += [
        "",
        "  DIALOGUE STRUCTURE",
    ]
    row("% paragraphs with dialogue", stats["dlg_para_pct"], 57.9, "%")
    row("Quote length median",  stats["ql_median"], BASELINE["quote_len_median"], "w")
    row("Quote length mean",    stats["ql_mean"],   BASELINE["quote_len_mean"],   "w")

    lines += [
        "",
        "  1-SENTENCE DIALOGUE PARAGRAPH STRUCTURE",
        "  (What portion of words is inside the quotes?)",
    ]
    for (lab, y_pct), (_, b_pct) in zip(stats["qr_dist"], BASELINE["quote_ratio_1sent"]):
        short_lab = lab.replace('\n', ' ')[:32]
        row(short_lab, y_pct, b_pct, "%")

    lines.append(div)
    report = "\n".join(lines)
    print(report)
    return report


# ── MAIN ──────────────────────────────────────────────────────────
def main():
    script_dir   = Path(__file__).parent
    chapters_dir = script_dir / "chapters"

    if not chapters_dir.exists():
        print(f"ERROR: Could not find chapters/ folder at {chapters_dir}")
        sys.exit(1)

    md_files = sorted(chapters_dir.glob("*.md"))
    if not md_files:
        print(f"ERROR: No .md files found in {chapters_dir}")
        sys.exit(1)

    print(f"\nFound {len(md_files)} markdown file(s) in {chapters_dir}\n")

    all_records = []
    for path in md_files:
        records = parse_file(path)
        all_records.extend(records)
        print(f"  {path.name:<30s}  {len(records):4d} paragraphs")

    if not all_records:
        print("ERROR: No parseable paragraphs found.")
        sys.exit(1)

    print(f"\nTotal: {len(all_records):,} paragraphs\n")
    print("Computing statistics...")

    stats       = aggregate(all_records)
    out_chart   = script_dir / "analysis_output.png"
    out_text    = script_dir / "analysis_summary.txt"

    print("\n" + "=" * 60)
    report = print_summary(stats, len(md_files))

    make_charts(stats, out_chart)

    out_text.write_text(report, encoding='utf-8')
    print(f"  Report saved: {out_text}")
    print()


if __name__ == "__main__":
    main()
