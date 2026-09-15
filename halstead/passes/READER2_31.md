# Reader pass: chapters/31_ruth.md

Word count before: 2865
Word count after: 2865

## Findings addressed

### Professor scene reads as competent supervision, not "expert can't keep up"

The finding is right that the scene mixed two different beats and let the
wrong one carry the frame. Checked against the actual exchange: the professor
does catch a real, specific gap (the two skipped lines between the sign
convention and the boundary term), and Ruth's "cancellation" vs. "absence"
distinction is a genuine piece of precision, not a correction of an error
(the text already establishes this is the claim "she has always kept private,
checked only against her own head, where it always came out fine" - i.e. she
was never wrong, she'd just never had to say it out loud before). The problem
was narrower than a full rewrite: the lead-in sentence blamed her *reasoning*,
which invites exactly the "he's doing legitimate rigor-checking on a shaky
argument" reading the finding describes.

Fix: reframed the lead-in around her explanation's compression rather than
her logic, so what follows reads as "skipped steps a Halstead peer would fill
in without being asked," not "an unclear argument":

- "in office hours he cannot follow her past the third step of her
  reasoning, and he says so, then asks her to go back." -> "in office hours
  he stops her three steps into an explanation and won't let her go on until
  she spells out what she skipped."

Left the rest of the exchange, including the cancellation/absence beat and
"The tail dies before the boundary does," untouched: the professor's own
closing lines already do the explicit favorable comparison the brief wants
("I have graduate students in their third year who would not have got me
there at all. Most of them would have told me the step was obvious and
waited for me to agree with them. But you went off and found the sentence"),
and that payoff was not in question.

### "The tail dies before the boundary does" - checked, not changed

The finding wants the actual expression and conditions behind this line. Not
changed: the line directly answers the professor's own instruction one beat
earlier, "Shorter," and he accepts it and moves on ("he tells her the result
holds, and caps the pen"), which is the in-scene evidence that it satisfies
his rigor. Writing out the real expression and conditions would mean putting
math notation and limiting-argument language into a book graded for ninth
graders, which the brief's own instructions rule out (no jargon or joke that
wouldn't read to an average teenager). Leaving it a compressed, accepted
answer to an explicit "shorter" is the correct trade here.

### Tangled comparison: who needed how many tries

"...somebody her own age ... would have needed two tries at what took her
five" left the two numbers unattached to anyone. Fixed to state plainly that
the peer would need only two of the five passes the professor needed:

"would have needed two tries at what took her five." -> "would have gotten
there in two of the five passes he needed."

### "Ever" reaches back through all of Halstead

Checked against the established teaching model; the finding is right that
"ever pushed back on a proof of hers" claims something about her entire
education, which is a much bigger claim than the scene needs or than the
rest of the book supports. Used the finding's own suggested fix:

"He's the only person who has ever pushed back on a proof of hers rather
than simply crediting the answer." -> "He's the only professor here who has
pushed back on a proof of hers rather than simply crediting the answer."

### Reading two weeks ahead - no reason given

Since she already knows the material, "something to do once it catches up"
doesn't hold up, and the finding is right that it doesn't explain why she
stays inside the official sequence instead of choosing harder material on
her own. Tied it instead to the folder/petition campaign already established
earlier in the same paragraph's section (the folder of problem sets she's
building as evidence for her placement appeal): she stays inside the
syllabus on purpose because work outside it wouldn't count as part of that
record.

"The reading stays two weeks ahead so she'll have something to do once it
catches up." -> "The reading stays two weeks ahead of the syllabus and no
further: nothing outside it goes in the folder."

### Portuguese, bottom third - level and population missing

Added the missing context so finishing in the bottom third reads as
consistent with her established ability rather than an unexplained weak
spot:

"the Portuguese class she sat all last year and finished in the bottom third
of" -> "the advanced Portuguese class of native speakers she sat all last
year and finished in the bottom third of."

### Chapter 28's message accounting

Read chapter 28's paragraph ("Sam brings it up in June...") as instructed.
It draws a real distinction the finding flags correctly: Chloe's first direct
message gets a reply, but the second "sits there with the single check mark
it gets on send; no second check mark ever joins it" - never confirmed
delivered, not merely unread. Chapter 31's "Every message gets read" is a
different, broader claim that would contradict that undelivered message if
read as covering the same channel.

Scoped the claim to the group chat, which is what the surrounding sentences
in chapter 31 are actually about (the numbers she posts, the unread count
climbing) and leaves chapter 28's separate account of the two direct
messages to Chloe alone:

"Every message gets read, but barely any get answered." -> "Every group
message gets read, but barely any get answered."

The "barely any get answered" wording was already compatible with chapter
28's one answered direct message, so no change was needed there.

## Not changed

No joke was added or specified; the study-group joke stays exactly as
opaque as it was.

## Verification

- `python3 -c "import re;print(len(re.findall(r\"[A-Za-z']+\",open('chapters/31_ruth.md').read())))"` -
  2865 words, matching the pre-edit count exactly.
- `python3 measures/style_report.py chapters/31_ruth.md` run before and after:
  every PASS/FAIL matches the baseline in the same direction (the one
  metric that briefly flipped, sentences under 10 words, was caused by a
  trim I didn't need for budget; restored the cut sentence and it returned
  to PASS at 35.3%, matching baseline).
- `python3 measures/check_edits.py --chapters 31` - 0 problems (word count,
  em dashes, curly quotes, hard breaks all clean).
- `python3 measures/prose_grade.py` for this chapter - reading grade (ARI
  8.65, Flesch-Kincaid 8.28) stays above the adult-band floor of 8.0.
- `python3 measures/banned_phrases.py` - nothing flagged for this chapter.
