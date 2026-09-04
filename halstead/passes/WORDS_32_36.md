# Vocabulary pass: chapters 32-36

Scope: `chapters/32_the_money.md`, `chapters/33_the_other_one.md`,
`chapters/34_the_files.md`, `chapters/35_nine_minutes.md`,
`chapters/36_seventy_five.md`. No other chapter opened for editing.

This is the lightest span in the book for these thirteen words. Fewer changes
were made here than the brief's "roughly a third fewer" guideline would
suggest across the board, because a close read showed most instances in this
span doing real work rather than sitting as filler — see the "left alone"
section below. The number was never the target; each cut or non-cut is a
individual judgment call.

## Counts, before -> after

| word | 32 | 33 | 34 | 35 | 36 |
|---|---|---|---|---|---|
| somebody | 2 -> 2 | 2 -> 1 | 2 -> 1 | 3 -> 3 | 6 -> 5 |
| twice | 4 -> 4 | 8 -> 7 | 4 -> 4 | 2 -> 2 | 4 -> 4 |
| already | 8 -> 6 | 10 -> 6 | 6 -> 3 | 10 -> 6 | 7 -> 7 |
| second | 9 -> 8 | 3 -> 3 | 1 -> 1 | 8 -> 8 | 7 -> 7 |
| whole | 3 -> 0 | 4 -> 1 | 8 -> 2 | 4 -> 0 | 2 -> 2 |
| end | 2 -> 2 | 7 -> 6 | 0 -> 0 | 2 -> 2 | 0 -> 0 |
| still | 7 -> 4 | 3 -> 3 | 9 -> 6 | 7 -> 5 | 3 -> 3 |
| every | 5 -> 5 | 4 -> 4 | 6 -> 6 | 4 -> 4 | 3 -> 3 |
| before | 18 -> 16 | 10 -> 9 | 10 -> 9 | 16 -> 15 | 6 -> 6 |
| gets | 5 -> 4 | 10 -> 9 | 3 -> 3 | 2 -> 2 | 4 -> 4 |
| goes | 5 -> 4 | 8 -> 7 | 2 -> 2 | 9 -> 9 | 4 -> 4 |
| comes | 5 -> 5 | 3 -> 3 | 2 -> 2 | 4 -> 4 | 4 -> 4 |
| does | 7 -> 5 | 3 -> 3 | 3 -> 3 | 4 -> 4 | 5 -> 5 |
| **chapter total** | **80 -> 65** | **75 -> 62** | **56 -> 42** | **75 -> 64** | **55 -> 54** |

Span total: 341 -> 287 (about 16% fewer). Word counts stayed inside the
2,000-5,000 band and none grew: 32 is 2262->2251, 33 is 2090->2081 (net -9
after one line was lengthened by a hedge), 34 is 2031->2014, 35 is
2117->2106, 36 is 1998->1998 (one word-neutral swap only, since 36 was
already under the 2,000 floor before this pass started — see below).

`measures/style_report.py` run on each of the five files afterward: tic scan
came back "none found" on all five (no trailing explanatory clauses
introduced), and none of the fragile book-wide margins the brief flagged were
touched in the direction that would hurt them — no "and" was added, no
quotation was shortened, and the two dialogue edits below both lengthened an
existing line rather than adding a new short one.

## Edits made, by chapter

### 32_the_money.md
- "The whole design problem" -> "The design problem"
- "a thing that goes looking" -> "a thing that hunts" (more exact verb)
- "The polling interval gets rewritten again and again before it finally
  reads as tired" -> "...is rewritten again and again until it finally reads
  as tired" (cuts both `gets` and `before`)
- "The shop itself does exactly what it always does" -> "...keeps to what it
  always does" (cuts one of a doubled `does`)
- "reads it back a second time" -> "reads it back once more"
- "checks the watcher every morning before he does anything else, the habit
  that already has him checking a server" -> "checks the watcher first every
  morning, the habit that has him checking a server" (cuts `before`, `does`,
  `already` in one pass)
- "taped index cards for the ones still missing a clean date" -> cut `still`
- "the radiator ticks through the whole night" -> cut `whole`
- "the version she has already checked and rechecked" -> cut `already`
- "Kavi reads the whole exchange..., marker still in hand" -> cut `whole`
  and `still`
- "the water glass still full at his elbow" -> cut `still` (kept the other
  two `still`s in the same sentence — see below)
- hedge: `kavi: who though. needs motive and funding.` -> `kavi: who though.
  i dont know, needs motive and funding.`

### 33_the_other_one.md
- "the financial worm's whole design" -> cut `whole`
- "the unit Theo already told them exists" -> cut `already`
- "they already have a file on their own school" -> cut `already`
- "and Ruth already has two numbers ready for him" -> cut `already`
  (redundant with "Ruth is already in it" two clauses earlier in the same
  sentence)
- "They go up before anything that's going to cost her something" -> "They
  go up when something is going to cost her" (cuts `before`)
- "somebody shows up at a door" -> "a stranger shows up at a door" (concrete
  noun, per the brief's suggestion)
- "Kavi's watcher runs the whole time too" -> "...runs throughout too"
- "Eli spends the whole run of it" -> cut `whole`
- "the coffee going cold twice before she remembers it's there. What she has
  at the end of it..." -> "the coffee going cold before she remembers it's
  there. What she has once it's finished..." (cuts `twice` and `end`)
- "because she already knows which of them is going to be the one" -> cut
  `already`
- "The stop clause gets exactly one line" -> "...is exactly one line"
- "It goes to all of them at once" -> "It reaches all of them at once"
  (more exact verb)
- hedge: `eli: as long as it takes to get in and out once` -> `eli: i dont
  know. as long as it takes to get in and out once`

### 34_the_files.md
- "The government badge is still clipped" -> cut `still`
- "the till already counted and the drawer already locked" -> cut the
  second `already`
- "because he was already standing up" -> cut `already`
- "taps two fingers against the wood the whole way through" -> "...while he
  reads"
- "Every page carries the same header before anything else on it" -> "Every
  page carries the same header first" (cuts `before`)
- "the whole company at that point three rooms over a laundromat" -> cut
  `whole`
- "the paper stock still visible through the scan" -> cut `still`
- "retyped once a year by somebody who has stopped expecting" -> "...by a
  clerk who has stopped expecting" (concrete noun)
- "The one number in the whole report" -> cut `whole`
- "the only detail in the whole account that was" -> cut `whole`
- "reads the whole thing again from the start" -> "reads it again from the
  start"
- "the chat has already started without him" -> cut `already`
- "the rhythm holding steady the whole time" -> "...holding steady
  throughout"
- "the file still open behind her on the bench, still on that page" -> cut
  the second `still`

### 35_nine_minutes.md
- "the process reports itself running the whole time" -> "...running
  throughout"
- "opens the thread where Kavi already is" -> cut `already`
- "reports a healthy process across the whole window" -> cut `whole`
- "that exact shape of quiet was the whole design brief" -> cut `whole`
- "how much he'd rather already have the answer" -> cut `already`
- "The whole exchange reaches him" -> cut `whole`
- "comes with the door out already built into the design" -> cut `already`
- "while she's already back on that page, the paragraph lit up once more
  before she shuts the laptop" -> "while she's back on that page, the
  paragraph lit up once more, then she shuts the laptop" (cuts `already`
  and one `before`)
- "a dozen ordinary explanations could still cover it" -> cut `still`
- "All of the logs still describe what they have always described" -> cut
  `still` (redundant with "have always described" right after it)

### 36_seventy_five.md
- "whether she wants somebody in the yard with her" -> "whether she wants
  company in the yard with her" (concrete noun, word-neutral)

That is the only edit made to chapter 36. It came in at 1,998 words before
this pass, already under the 2,000 floor, and every one of the thirteen
words in it turned out to be doing real work on inspection (see below), so
per the brief ("if a chapter is already clean, say so and leave it") it was
left otherwise untouched rather than cut to hit a number.

## Hedges added: 2

Both in dialogue, both lowercase and apostrophe-free to match the surrounding
thread convention:

1. `chapters/32_the_money.md`: `kavi: who though. i dont know, needs motive
   and funding.` — Kavi is speculating about who else might have found the
   pattern; the line read more certain than his actual state.
2. `chapters/33_the_other_one.md`: `eli: i dont know. as long as it takes to
   get in and out once` — Sam's next line, "thats not a number," is a direct
   complaint about Eli's vagueness; giving Eli's line an explicit "i dont
   know" makes the exchange land better and costs nothing plot-wise.

No hedges were added to chapters 34, 35, or 36. All three already carried a
reasonable existing supply (`already think`, `very slightly`, `much more
useful`, `i can see`, half a dozen existing `dont`s in dialogue), and 36 in
particular is carried almost entirely by Priya, whose established voice is
blunt and quantifying ("give or take," "about what i expected," "top sixty
on a generous day") — forcing "i think" or "very" into her lines would have
worked against that characterization rather than for it. Given the brief's
own criterion — add one only where a line currently sounds more certain than
the character is, and "a few, not one per page" — two across the whole span
was the honest count of places that qualified.

## Words judged to be doing real work, and left uncut

- **32**: "every decision in this, for twenty years..." and "every single
  time since 2003" in Ruth's chat argument — these are load-bearing to the
  proof itself (the whole case is that the pattern holds *without
  exception*), not a filler absolute.
- **33**: "the second worm" in the chapter's opening line is a direct
  callback to the chapter's own title ("The Other One") and to "second" as
  the book's word for it; "thats the whole qualification" (Nadia) is her
  argument's own claim to completeness, not decoration. Most `gets`/`goes`/
  `comes` in this chapter were already precise phrasal or idiomatic uses
  ("gets denied," "goes to Chloe," "comes back three words long") and were
  left per the brief's caution on the four tense-inflated verbs.
- **34**: every one of the six `every` instances sets up a structural or
  behavioral pattern (file format, the "every table" friendship detail, the
  persistent-failure "comes back empty every time") — none read as
  rhetorical padding. `before` in this chapter came back essentially clean
  for the same reason: nearly all ten instances sequence something that
  actually matters (Theo's twenty minutes outside, Nadia checking before she
  speaks, Sam's twenty-minute delay). Only one `before` needed cutting.
- **35**: this chapter is arguably the strongest case in the span for
  leaving these words alone. Its whole plot mechanism is exact timing (nine
  minutes, "to the second," a number repeating), so `second` (8, zero cut),
  `twice` (2, zero cut), `every` (4, zero cut) and most of its 16 `before`s
  are the mechanism, not filler describing it. `somebody stopped it and
  started it` (Eli, dialogue) names the book's central unnamed antagonist —
  cutting or naming that "somebody" would give away the mystery the whole
  book is built on. `goes`/`comes`/`does` (9/4/4) were all already precise
  physical or idiomatic uses and needed no verb swaps.
- **36**: the same pattern, more so. `somebody` at line 89 ("off a list
  somebody handed them") and line 99 ("somebody has been keeping paper on
  what came out of it") both point at the book's unnamed watchers and were
  left alone for the same reason as chapter 35's. Ruth and Priya's `gets`
  ("gets you thirty," said and then repeated back) is a deliberate rhetorical
  echo between two speakers, not a passive filler. The chapter's `second`
  count (7) is entirely literal ordinals (second bus, second bench, second
  message) with nothing to cut.

## Do-not-disturb constraints respected

Not touched, per the brief: Theo's disclosure and Sam's one-line answer in
34 (`"mine has a name in it I already know," ... whose name`); Chloe's "theo
which four" and Ruth putting it back up in 32; Eli running Ruth's twenty
years against his own logs in 32; the deliberately unanswered lines in 35
(`ruth: why hasnt anybody already used this`) and 36 (`ruth: seventy-five
people across a field...` and the following `she does not say it a second
way`). None of these lines, or the sentences immediately carrying them, were
edited, even where they contained one of the thirteen words.
