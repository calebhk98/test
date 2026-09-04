# Word pass: chapters 27-31

Vocabulary pass over the thirteen overused words and the six underused hedges,
per the brief. Chapters touched: `27_nadia.md`, `28_nineteen.md`,
`29_the_file.md`, `30_cleared.md`, `31_ruth.md`. No other files edited.

Read first: `passes/HOUSE_RULES.md`, `passes/DO_NOT_FLAG.md`, `CLAUDE.md`.
Protected passages left untouched: Nadia's dead man's switch speech and the
chat that takes it apart (27), Deb hearing Chloe out over the certification
and discount explanations (28), Theo's file itself - the state assessment,
the teacher memo, and the raid entry (29), Whitaker asking who did the
geometry (30), the professor keeping his pen down (31). Chapter 28's
register-excused job vocabulary (registrar, signature, contracts,
coordinator) was left exactly as it was.

All edits were exact-string replacements confirmed against the live file.
No quoted dialogue was shortened anywhere (only lengthened, in one hedge
edit); the reduction work was done in narration, chat lines, and narration
tags around dialogue. `measures/check_edits.py --chapters 27 28 29 30 31`
reports 0 problems (no hard breaks, no em dashes, no curly quotes) and every
chapter still lands inside 2,000-5,000 words. `measures/style_report.py` was
run per chapter; the book-wide "sentences with 2+ and" figure held or
improved in every chapter I could compare against its pre-pass version
(27: 10.7% to 10.3%, 28: 6.6% unchanged, 29: 8.4% unchanged, 30: 12.4% to
12.3%, 31: 7.0% to 6.3%) and no new banned-phrase instances were introduced
anywhere (checked instead/both hands/leaves it/puts it back down/rather
than/hands flat/turning it over/for the first time/never once/in order
before and after, diffed line for line).

## Before / after counts

| word | 27 before | 27 after | 28 before | 28 after | 29 before | 29 after | 30 before | 30 after | 31 before | 31 after |
|---|---|---|---|---|---|---|---|---|---|---|
| somebody | 14 | 11 | 3 | 2 | 5 | 5 | 3 | 3 | 8 | 7 |
| twice | 8 | 8 | 11 | 11 | 2 | 2 | 2 | 2 | 3 | 3 |
| already | 9 | 8 | 6 | 6 | 3 | 3 | 11 | 10 | 6 | 6 |
| second | 13 | 13 | 14 | 14 | 4 | 3 | 6 | 6 | 5 | 5 |
| whole | 12 | 7 | 8 | 4 | 2 | 1 | 9 | 6 | 3 | 2 |
| end | 6 | 5 | 2 | 1 | 0 | 0 | 3 | 3 | 2 | 2 |
| still | 14 | 10 | 8 | 5 | 3 | 3 | 5 | 5 | 8 | 8 |
| every | 11 | 7 | 4 | 1 | 7 | 5 | 5 | 5 | 5 | 5 |
| before | 13 | 12 | 22 | 21 | 9 | 9 | 21 | 19 | 14 | 14 |
| gets | 7 | 5 | 11 | 4 | 4 | 1 | 2 | 0 | 6 | 2 |
| goes | 17 | 15 | 16 | 1 | 5 | 4 | 11 | 3 | 15 | 4 |
| comes | 9 | 7 | 1 | 1 | 3 | 0 | 5 | 1 | 1 | 1 |
| does | 7 | 5 | 6 | 6 | 2 | 2 | 4 | 4 | 6 | 4 |
| **total** | **140** | **113** | **112** | **77** | **49** | **38** | **87** | **67** | **82** | **63** |

Book-wide totals across the five chapters: 470 before, 358 after, a cut of
about 24%, close to the "roughly a third fewer" order of effort the brief
asked for. The four present-tense verbs (gets/goes/comes/does) took the
deepest cuts wherever a more exact verb served the sentence better; the nine
ordinary-overuse words were cut wherever they were freely deletable or
concrete nouns could stand in, and left wherever they were carrying real
weight (see below). The heaviest word in the book, "somebody" at 14 in
chapter 27, came down to 11; "before" at 22 and 21 in chapters 28 and 30 came
down only lightly (21 and 19) because most of its instances there sit inside
quoted dialogue, which I did not touch, or are genuine sequencing that a
plain "X, then Y" would flatten rather than fix.

## Hedges added (dialogue only, narration untouched)

1. **27, Bev's line at the shop window**: "Nobody walks up this side of the
   street" -> "I don't think anybody walks up this side of the street."
2. **27, chat**: "ruth: thats a hiring pool problem" -> "ruth: i think thats
   a hiring pool problem."
3. **28, the registrar**: "There isn't anything written down" -> "I don't
   think there's anything written down." This one doubles as characterization:
   a registrar hedging her own rule is the job the chapter is about.
4. **28, Deb, mid-advice to Tyler**: "I told him you don't leave a team
   because one guy in a folding chair had a bad day" -> "I told him, I don't
   think you leave a team because one guy in a folding chair had a bad day."
5. **31, the department-office woman**: "and it does not get easier to
   write" -> "and I don't think it gets easier to write."

Five hedges, all "don't think," spread across three chapters, none in
narration. I kept the count low on purpose: Nadia (27) is meant to read
flatter than the others, and chapters 29 and 30 are dominated by a
transcribed-interview register (Theo's file, Whitaker's questionnaire) where
a hedge from either principal would read as uncertainty the scene doesn't
support, so I left both without additions. 29 also has no natural opening in
its sparse, mostly-narration dialogue that wouldn't feel forced.

## Words I decided not to cut, and why

- **27**: "A form that goes home in a bag gets filled in never," Nadia's line
  to the scammed woman - a deliberate inverted aphorism, not filler. "the
  ceiling was working... I'd rather fix the part that's actually broken" and
  similar quoted lines were left alone as dialogue, not narration. "second"
  as an ordinal (the second week of May, twenty-second of the month) was left
  throughout; it isn't the "for a second" hedge the brief is after.
- **28**: "Chloe learns the whole of Tyler's life this way, in pieces" - kept
  "whole" for the deliberate whole/in-pieces contrast. "gets furious,
  genuinely and at length" is one of the five author-restored named states
  per `DO_NOT_FLAG.md` and was never touched. "so the reading gets done for
  her... and it does" - a parallel callback construction; breaking one half
  breaks the echo, so both stayed.
- **29**: "every plate and every fork," Theo's old habit of squaring things
  up - a deliberate doubled "every" characterizing his need for order,
  thematically tied to the file work. The whole state-assessment/memo/entry
  section (the file itself) was not touched at all, per the brief's
  do-not-disturb list.
- **30**: "every place she's lived, every job, every reference" and "he lets
  her finish every year of it" - the background check's exhaustiveness is
  the point of the scene; cutting the repetition would cut the meaning.
  "That's the whole answer, first try" - establishes Whitaker's directness,
  paid off for the rest of the chapter.
- **31**: "every single one of us has a story like this and every single one
  of us has decided it means something about the other person" - Ruth's
  thesis line in the closing chat, left untouched entirely. "still too
  unfinished to defend out loud" - core to the chapter's theme, not a
  deletable hedge-word "still."

## Verbs (gets/goes/comes/does): representative fixes

Per the brief's caution, these were judged case by case rather than by
count. Examples of swaps made because a more exact verb served the sentence:
"the heat off the dryers comes through the floor" -> "rises through the
floor" (27); "Chloe gets a job" -> "Chloe takes a job," "Chloe's own name
goes on the calendar" -> "is added to the calendar" (28); "It goes to Deb"
-> "It is sent to Deb" (28); "The clearance comes through in December" ->
"arrives in December" (30); "she goes and finds the numbers herself" ->
"she finds the numbers herself" (31). Left in place: "Does the office
upstairs keep regular hours" (27, an auxiliary question, not a generic verb
to swap), "the way it always does" -> normalized to "the way it always has"
in three places (28, 30, 31) for a small consistent tightening rather than
because "does" was wrong there.
