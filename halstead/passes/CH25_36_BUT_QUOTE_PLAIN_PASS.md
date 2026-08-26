# Chapters 25-36: but/and pass, quote-length pass, plain-prose pass, floor fix

Scope: chapters/25_forty_targets.md through chapters/36_seventy_five.md only.
No files outside that range touched. `check_edits.py --chapters 25 26 27 28 29
30 31 32 33 34 35 36` reports 0 problems after this pass.

## Job 1: "but"

Genuine contrasts only, converted from an "and" join, a semicolon, or a plain
sentence boundary. Chat transcripts (lowercase, no terminal punctuation) left
untouched throughout, including the "but" occurrences already inside them in
26, 28, 31, 36.

| chapter | but before | but after | and before | and after |
|---|---|---|---|---|
| 25 forty_targets | 2 | 9 | 69 | 63 |
| 26 the_exercise | 1 | 4 | 87 | 84 |
| 27 nadia | 0 | 9 | 129 | 123 |
| 28 nineteen | 2 (both chat) | 12 (2 chat, 10 prose) | 82 | 80 |
| 29 the_file | 1 | 4 | 50 | 48 |
| 30 cleared | 2 | 7 | 74 | 71 |
| 31 ruth | 1 (prepositional) | 10 | 77 | 71 |
| 32 the_money | 0 | 4 | 52 | 51 |
| 33 the_other_one | 1 (prepositional) | 6 | 63 | 60 |
| 34 the_files | 0 | 5 | 49 | 47 |
| 35 nine_minutes | 1 (chat) | 7 (chat+6 prose) | 34 | 34 |
| 36 seventy_five | 3 (2 chat) | 9 (2 chat, 7 prose) | 71 | 67 |
| **span total** | **18** | **86** | **837** | **799** |

Span "but" rate goes from 0.06% to 0.28% of all words, a 4.8x increase (target
was roughly 3x). Examples of the contrast fixed, not the mechanical swap:

- ch25: "that's a good sheet **and** a bad number" -> "**but** a bad number"
  (Sam, to the captain, on the qualification score).
- ch27: "Hanley carries thirty-one filings on that address, **and**
  twenty-six of them belong to somebody who is not in this room" -> **but**
  (undercuts the men's numbers as she threatens them).
- ch31: "He nods at the first, **and** at the second the nod does not
  arrive" -> **but** (the professor loses her mid-proof).
- ch33: "Eli proposes the second worm **and** Theo says no" -> **but**
  (opening line of the chapter; a real refusal, not a list item).
- ch35: "different would say clumsy, **and** the same number twice says
  measured" -> **but**.
- ch36: "is told the flights are absurd, **and** offers again the following
  day" -> **but** (Sam ignores the refusal).

No mechanical tripling: several candidate "and"s were left alone because the
join was additive, not contrastive (e.g. ch27 "you put thirteen employer
accounts on my site... and you asked nine people for a bank routing number" —
sequential facts, not opposed ones).

## Job 2: quote length

Measured with `quote_length.py`'s own `quotations()`/`sentences()` functions
so chat is excluded the same way the script excludes it.

| chapter | quotes before | mean before | 1-sent% before | quotes after | mean after | 1-sent% after |
|---|---|---|---|---|---|---|
| 25 forty_targets | 56 | 1.59 | 53.6 | 56 | 1.59 | 53.6 |
| 26 the_exercise | 35 | 1.54 | 57.1 | 35 | 1.54 | 57.1 |
| 27 nadia | 48 | 1.65 | 62.5 | 48 | 1.65 | 62.5 |
| 28 nineteen | 23 | 1.39 | 65.2 | 20 | 1.60 | 60.0 |
| 29 the_file | 9 | 1.00 | 100.0 | 6 | 1.50 | 50.0 |
| 30 cleared | 39 | 1.62 | 61.5 | 39 | 1.62 | 61.5 |
| 31 ruth | 19 | 1.63 | 52.6 | 19 | 1.63 | 52.6 |
| 32-36 | n<15 real dialogue (chat-heavy) | — | — | same | — | — |
| **span (25-36)** | **233** | **1.55** | — | **227** | **1.59** | — |

The task brief's per-chapter numbers for ch27 (1.04, 96.2% single) and ch31
(1.29) do not match what is in the file now; the repository's git log shows
several dialogue/repetition passes already landed on this span before this
task started (e.g. "ch27's repetition spoken twice", "the office hours
dramatized"). Measured directly, ch27 and ch31 were already at or above the
1.6 target going in. Work went instead to the chapters that were actually
weak: **28** (1.39 -> 1.60) and **29** (1.00 -> 1.50, the real 96%-single
chapter in this span).

Method used throughout: where a single speaker's multi-sentence turn was
split into two quotation-mark spans by a mid-speech attribution ("X," Y says.
"Z."), the attribution was moved to the front or the end and the speech left
whole ("Y says, X. Z."). No dialogue content was changed, added, or cut in
this job — only where the closing/opening quote marks and the attribution
sit. Examples: ch28 (Chloe's certification and match-logic explanations,
each split by "Chloe says" into a 1-sentence and a 2-sentence quote, now one
3-sentence quote), ch29 (the retiring coworker's line, Theo's supervisor
exchange, the grandmother's call).

Left clipped, on purpose, per the brief: Sam's turns throughout; the
Whitaker interrogation in ch30 (his questions stay one or two words; Chloe's
answers already run long — "Sir, that's a good sheet..." class of turns);
the chat-driven interrogations in ch34/36.

## Job 3: plain the literary prose down

This span is the "adult half" and the most literary, per the brief. Changes
made: flattening a periodic/inverted opener, cutting a "less like X than Y"
or "rather than something softer built to..." rhetorical balance, splitting
a heavily-subordinated sentence that held its main verb to the end.

| chapter | before | after |
|---|---|---|
| 28 | "Being years younger than everyone else at the company, she takes it, at first, to mean she is basically the intern..." | "She is years younger than everyone else at the company, and at first she takes that to mean she is basically the intern..." |
| 28 | "Checked against the actual treaty text, both summaries turn out to leave out a sentence..." | "She checks both summaries against the actual treaty text. Both leave out a sentence..." |
| 30 | "That's the whole answer, first try, the real one rather than something softer built to sound reassuring." | "That's the whole answer, first try, not something softer built to sound reassuring." |
| 31 | "What eventually breaks it is a professor she likes, in office hours, someone she is genuinely fond of, who cannot follow her past the third step of her reasoning and says so, before asking her to go back." | "A professor breaks it. She likes him, genuinely, and in office hours he cannot follow her past the third step of her reasoning. He says so, then asks her to go back." |
| 35 | "Pulling its own report now feels less like checking a tool than rereading his own handwriting for a lie he'd have to have told himself first." | "Pulling its own report doesn't feel like checking a tool. It feels like rereading his own handwriting, checking for a lie he'd have had to tell himself first." |

Kept as-is on purpose: long compound sentences joined with commas (house
voice, not a defect), concrete metaphors ("wearing different currencies at
different times," ch32; "the way it finds a light switch in her own house
in the dark," ch35), and the Whitaker/Priya interrogation scenes, which are
plain by design already. This was a light pass, not a rewrite — most of the
span's prose (Sam's Army chapters, the chat-driven chapters) was already
plain; the handful of edits above were the clearest cases of a sentence
built for rhythm over information.

## Job 4: word floor

- **ch35 (nine_minutes): 1928 -> 2028 words.** The third check-in gap
  ("By the third time the days are properly hot...") was previously a single
  summary sentence with no detail on the gap itself. Dramatized it: when it
  lands, that it runs longer than the first two, and that the report still
  comes back clean. This is the same beat the chapter already tracks twice
  in detail (the June gap, the second-Tuesday gap); the third only ever got
  a weather clause. No new information invented — same tool, same behavior,
  just shown instead of skipped.
- **ch36 (seventy_five): 1934 -> 2029 words.** Three beats that were pure
  summary got one dramatized beat each: the two prisoners' first "good
  morning" and first unprompted gesture (previously two flat report
  sentences), Eli's list of physical security fixes for Priya's room
  (previously "a list of things," unspecified), and Kavi's follow-up message
  (previously just "the name of a piece of software," now the two follow-up
  messages that fit his established habit of over-explaining a tool once he
  builds it). Nothing padded; all three are beats the chapter already gestures
  at without showing.

Both chapters stay well under the ceiling and near the book's target band.

## Final checks

- `check_edits.py --chapters 25-36`: 0 problems (em dashes, curly quotes,
  hard breaks, word count all clean).
- `grade.py` band 23-36: average 8.85, floor 8.0. Individual chapters below
  8.0 within this span (25: 7.7, 27: 7.9, 30: 7.2, 31: 7.9) were already
  below floor before this pass and are judged on the band average per house
  rule 5/6; none of this pass's edits were reading-grade reductions aimed at
  a number, and no chapter that already cleared its band was pushed down on
  purpose.
- No spelled number word (one-fifteen, forty) was introduced in any chapter
  without a corresponding removal in the same chapter; new dramatized
  passages in ch35/36 were written to avoid cardinal number words entirely
  (ordinals like "third," "second" are unaffected by that rule).
- characters/, other chapters, and all reference docs: untouched.
