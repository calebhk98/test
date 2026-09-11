# Reader pass: chapter 36 (seventy_five)

Word count before: 2010. Word count after: 2010. (`grep -c` via the counting
one-liner in the brief; `style_report.py` also confirms 2005 vs 2005 in its
own tokenizer, unchanged.)

## Findings addressed

**"I cannot get those two to sit together."** Ambiguous between physical
placement, cooperation, and matching accounts. Given the surrounding lines
(four days of near-nothing out of interrogating them, then "what they will
say, over and over, is that it was me they came for") the intended meaning is
that their two accounts will not corroborate. Changed to "i cannot get their
two stories to agree" (line 87), per the reader's own suggested fix.

**Ruth's hundred-and-ten-meter calculation.** Two separate problems, both
fixed. First, seventy-five people need a stated formation to produce a
distance; added "arm's length apart" so the math has a basis a reader can
check (line 139). Second, "I can see the whole of it at once" was ambiguous
among three readings; changed to "I can see the whole of it straight through,"
which commits to the spatial reading (she can hold the whole line in view,
end to end, because she has personally walked that exact distance) rather
than reading as a claim about handling the fight herself or about her general
mental state.

**Theo's form and Chloe's search.** Both instances of "form" were left
completely unspecified. Named it as an "intake form" in both places (lines
127 and 145) — enough for a reader to place the two hits (Theo's message,
then the same number resurfacing in Chloe's own agency search) as a form used
for processing people, which is what makes the coincidence significant
without spelling out the file's contents.

**Timeline: "a building i left four years ago."** Checked against
`chronology/BOOK.md` and the chapter headers before touching it. Chapter 23
("The First One") is dated June 2023 and is the graduation chapter Priya
leaves in ("Priya takes two years and goes to South America with a bag,"
`23_the_first_one.md:157`, in the same scene as the other graduates
scattering). Chapter 36 is headed October 2026. June 2023 to October 2026 is
three years and four months, not four years. Changed "four years ago" to
"three years ago" (line 15). The reader was right.

**Timeline: "since before any of us started."** Checked against the chapter
headers and against chapter 10. The file is dated to 2013 in three other
chapters (`29_the_file.md:19`, `32_the_money.md:107`, `34_the_files.md:7`),
all just "2013" with no month. Chapter 10 ("April," headed *April 2013 – June
2013*) has Ruth tell Chloe on arrival "Priya arrived in January," meaning
Priya was already at Halstead before Chloe's April 2013 start, and the whole
cohort's shared entry point — the camp of chapters 3-6 — is headed July-August
2012, a full year before the file. So the file cannot be shown to predate
"any of us," and the camp positively predates it. Changed nadia's line to
"since we were kids" (line 99), which is true without asserting a chronology
the book doesn't support. The reader was right on both timeline points.

**"The two I took off the grass."** This referred to the two guns she picked
up (see the line just before it: "they had guns from the start and left them
alone"), but the bare "the two" reads as people, especially with "two men"
established as her actual prisoners forty lines later. Added "guns": "the two
guns i took off the grass" (line 57). Left the later "two of the small ones"
(the darts) and "two men" (the prisoners) alone — those are already
unambiguous on their own terms, so this was the one spot doing the confusing.

**The kettle.** Fixed by making it a stovetop kettle rather than an
unspecified one: "the kettle whistling on the stove behind him" (line 53). An
electric kettle would have clicked off on its own; a stovetop one boiling dry
while Eli reads is the version that supports "leaves it to boil dry" as a
plausible sign he's stopped tracking anything else in the room.

## Findings not changed

**Her injuries and scale of action, generally.** Beyond the "two off the
grass" fix above, the specifics already on the page (the hand that won't
close, the third-dart hit, thirty in before the guns came out) read as
deliberately kept at that level of precision, and the reader's own list of
what's working ("the hand that will not close, the changed lock, and the
interrupted counting") already includes most of this material. Left alone.

## House rules and constraints checked

- No new em dashes or curly quotes introduced.
- No dialogue voice changed except where the finding was specifically about
  what a character says or knows (all seven dialogue edits above qualify).
- No sentence now opens with "She" or "He."
- No new instance of a capped number word: "four years ago" to "three years
  ago" swaps one already-present number word for another rather than adding
  one; the book-wide count of "four" goes down by one and "three" up by one,
  net zero on total number-word volume.
- `style_report.py chapters/36_seventy_five.md` run after the pass: word
  count, sentence/paragraph shape, and conjunction rates are identical to the
  pre-pass baseline (checked by diffing against `git show HEAD:...`); no tics
  found in narration, same as before. The chapter's pre-existing FAILs
  (QUOTED, SENT/PARA, SECTION BREAKS, `so` rate) are unchanged and were not
  introduced by this pass — this chapter is a chat log and those shapes are
  structural to it, not something these seven edits touch.
