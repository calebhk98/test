# Quantitative text metrics (computed on the full 197,752-word manuscript)

Scripts: /tmp/syntax_stats.py and /tmp/freq_stats.py (run against
book/manuscript/The_Long_Way_Home.md, markdown headings stripped).

## Zipf's law (word-frequency distribution)
The "common-words frequency formula" is **Zipf's law**: frequency is roughly
proportional to 1/rank. This text fits it almost perfectly.

- Total tokens: 197,752 | Unique types: 7,080 | Type-token ratio: 0.036
- Hapax legomena (words used once): 2,541 = 35.9% of vocabulary
- **Zipf log-log fit:** slope **-0.962** over the top 100 ranks and **-1.066** over the
  top 1000 ranks (ideal = -1.0), **R^2 = 0.994** in both cases — a textbook fit.
- Top words are the expected English function words, in the expected order:
  the(8.07%), and(4.66%), a(3.94%), I(2.76%), it, of, to, was, in, had, that, he, not,
  you... — with I/me/my elevated, as expected for first person.

**Interpretation (important):** near-perfect Zipf adherence is a property of ALL fluent
natural-language prose — human OR AI. It confirms the text is well-formed English; it
does **NOT** discriminate AI from human writing, and would only be notable if it
DEVIATED. It doesn't. Treat this as "clean, but not diagnostic."

## Paragraph sentence-count distribution
| Sentences in paragraph | Count | Share |
|---|---|---|
| 1 | 624 | 26.1% |
| 2 | 358 | 15.0% |
| 3 | 372 | 15.5% |
| 4 | 265 | 11.1% |
| 5 | 256 | 10.7% |
| 6+ | 518 | 21.6% |
- Paragraphs: 2,393 | Mean sentences/paragraph: **3.7** | Median: **3**
- One-sentence paragraphs: **26.1% overall**; **23.5%** excluding dialogue-led paragraphs
  (i.e. of 1,791 narrative paragraphs, 420 are a lone sentence).
- Dialogue-led paragraphs: 602 (25.2% of all).

**Human-writing context for single-sentence paragraphs:**
- The "paragraphs should be ~5 sentences" guideline is an EXPOSITORY/essay convention,
  not a fiction norm. Published fiction varies enormously.
- Dialogue inherently produces many one-sentence paragraphs (one per speaker turn) — so
  ~25% dialogue-led paragraphs is normal and correct.
- Commercial/genre fiction (thriller/YA/contemporary) uses one-sentence paragraphs
  heavily for pace — frequently 30%+.
- LITERARY fiction (the register this book targets) uses them sparingly for deliberate
  emphasis — typically ~5-15% of narrative paragraphs.
- Therefore the book's **23.5% narrative single-sentence rate is high for its intended
  literary lane**, corroborating the syntax/cadence audit's finding that the dramatic
  one-line paragraph is overused until it loses impact (by ch50 the device "consumes its
  own climax"). NB: these comparison ranges are editorial norms, not a measured corpus;
  a true side-by-side requires running the same script on a named comparison novel.

## Sentence-shape recap (from syntax_stats.py)
Mean sentence 23.7 words; median 15; stdev 22.5 (high variation). 36.9% of sentences are
>=25 words; 46.3% carry a subordinator; only 14.5% are <=4 words. The book skews LONG and
hypotactic, NOT staccato/paratactic — its cadence issue is a predictable long/medium/short
3-beat, not a "no-conjunctions" problem.
