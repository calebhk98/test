# Voice pass: chapters 13-14

Scope: `chapters/13_ten_pages.md` and `chapters/14_sixty_degrees.md` only. The
paintball floor and corridor in chapter 13 (the barrel-as-hose discovery
through Bex telling Bell, roughly "Paintball joins the afternoon block in
October" to "past where they ever were with darts") and the astronomy dinner
in chapter 14 (the fortnight on dating the universe through the lecture the
next day, "Astronomy runs the autumn term" through "the grass soaks through
her boots on the way down") were read but not touched, per the brief and per
`passes/BEX_SELECTS.md` / `BEX_DELIBERATE.md`, which built the boy-named,
girl-unnamed asymmetry into exactly those two passages.

`measures/style_report.py` run on both chapters before and after: no measure
crossed a pass/fail line in either direction. Word counts moved by single
digits (13: 4262 -> 4269; 14: 4153 -> 4154), both still well inside 2,000-5,000.
The chapter 13 "sentences with 2+ 'and'" figure (10.2%, over the 10% ceiling)
and the "because" conjunction rate are pre-existing and unaffected by any
edit here, confirmed by diffing the report against the pre-pass file.

## Changed

### 1. chapters/13_ten_pages.md — the Federalist reading schedule

**Before:** "Number 6 goes that week and 9 the week after."

**After:** "She reads number 6 that week and 9 the week after."

**Why:** Fake agency. The essay number cannot move itself through a week;
Chloe is the one reading through Hamilton's papers in order, and the rest of
the paragraph ("she is going through them," "she starts on Madison's") is
already in her voice. Naming her costs nothing and matches the surrounding
sentences.

### 2. chapters/13_ten_pages.md — the outline

**Before:** "so she builds the outline first, though outlines have always
been for other people, and it gets the pages out the other end anyway."

**After:** "so she builds the outline first, though outlines have always
been for other people, and she gets the pages out the other end of it
anyway."

**Why:** Fake agency. "It" (the outline) cannot get pages out of anything;
she does, using it. The fix keeps the machine image (in one end, out the
other) but puts a person back at the machine.

### 3. chapters/13_ten_pages.md — Kowalczyk's hand

**Before:** "A hand goes up, fingers spread, and turns."

**After:** "Kowalczyk holds up a hand, fingers spread, and turns it."

**Why:** Fake agency, and an easy one: Kowalczyk is mid-demonstration two
lines earlier ("Kowalczyk has the clock in her hand") and speaks the next
line. This is not the book's protected involuntary-reaction category — it is
a teacher deliberately showing the class something with her hand, not a
knee-going-loose reflex — so it should read as her doing it, not as a hand
acting on its own.

### 4. chapters/13_ten_pages.md — the note on the essay

**Before:** "she checks the back of the last page twice, in case the note
went there."

**After:** "she checks the back of the last page twice, in case Hearn wrote
the note there."

**Why:** Fake agency. Notes do not travel to pages by themselves; Hearn
either wrote it on the back or he did not, and he is the subject two
sentences earlier ("In December Hearn hands an essay back with no note on it
at all"), so naming him again here is free.

### 5. chapters/13_ten_pages.md — essays turned in before the break

**Before:** "More go in ahead of the break, but they are the essays they
have been since October."

**After:** "More are handed in ahead of the break, but they are the essays
they have been since October."

**Why:** Fake agency corrected the other direction from most of this pass.
This is genuine school machinery — a class's worth of essays going in over
several weeks, no single doer worth naming — so the fix is a passive with an
obvious, irrelevant implied agent (the students handing work in), not an
active sentence forcing a person into the subject slot. It also keeps "the
essays" as the throughline into the next clause, which is what the sentence
is actually about. This matches the same move already used two paragraphs
earlier in this chapter for "Most of them are announced" about the drills.

### 6. chapters/13_ten_pages.md — the last line of the essay

**Before:** "The last line goes down late, and there is an hour before
lights out, which she spends on a book she picked herself."

**After:** "She writes the last line late, and there is an hour before
lights out, which she spends on a book she picked herself."

**Why:** Fake agency. A line of an essay does not descend onto the page on
its own; she writes it, late, the same night. Kept "writes...late" rather
than any phrasing built on "down," since the "puts it back down"/set-down
beat is at its cap for the book and this sentence had no reason to go near
that construction anyway.

### 7. chapters/14_sixty_degrees.md — Kavi's question about the essay

**Before:** "Kavi asks whether the essay went in all right, meaning yes or
no, and gets the two ways of measuring the age of the universe..."

**After:** "Kavi asks whether she got the essay in all right, meaning yes or
no, and gets the two ways of measuring the age of the universe..."

**Why:** Fake agency. This is indirect narration, not a quoted line, so it
is in scope, and an essay cannot submit itself; she did, the previous
chapter's whole plot is her turning that essay in. Naming her is a two-word
change with no cost to the sentence.

**Count: 7 changes.** All seven were fake-agency corrections (active voice
with no one in it), six fixed by putting a person in as the subject and one
(essays going in ahead of the break) fixed by turning it into a passive with
an obvious, unnamed institutional doer, because that one really is the
school's collective machinery rather than any one person's act. None
involved a passive-with-a-person-as-subject; I did not find one of those in
either chapter outside the protected passages.

## Called out, not changed

### chapters/13_ten_pages.md, line 206

**Current:** "but this time all the pages do what only the third used to."

**Why the voice is wrong:** Fake agency — pages cannot do anything; Chloe
writes them. On its own this would be an easy fix (put her back as the
subject of the sentence).

**Why I did not change it:** This sentence is a direct callback to Hearn's
own line earlier in the same chapter: "the third page of an essay is doing
the work of the pages in front of it." That is a teacher's diagnosis, given
as dialogue, and the payoff here is the narration confirming his read came
true, in his own terms — pages "doing work." Rewriting it to "she writes
every page the way she used to write only the third" breaks the callback,
because it stops echoing the specific thing he said and starts describing
her effort instead of the pages' quality, which is the actual point of the
sentence (that all ten pages now do what one page used to). I could not find
a phrasing that kept the echo and named a doer at the same time without
either lengthening the sentence past what the moment needs or losing the
callback outright, so I am leaving it for a call on whether the callback is
worth more than the fix.

**Replacement 1:** "But this time she writes every page the way she used to
write only the third."

**Replacement 2:** "But this time she gets ten pages doing what only the
third used to do."

### chapters/14_sixty_degrees.md, line 7

**Current:** "Archery is ordinary at first, because the start of it is butts
at twenty meters, then thirty, then fifty, an hour a day of being told what
your elbow is doing by an instructor who walks the line every so often to
say it again."

**Why the voice is wrong:** "Being told" puts the person on the receiving
end of instruction into a passive without naming her, which brushes against
the rule against ever putting a person in the subject of a passive — the
implied subject of "being told" is Chloe, or any archer standing in for her,
not the instructor.

**Why I did not change it:** The "you" here is genuinely generic, describing
the whole class's daily routine rather than singling Chloe out the way
"Chloe is told" or "she is given" would, and the sentence already names the
actual doer in the same breath ("by an instructor who walks the line"), so
it is not hiding who is responsible. I was not confident this is the
violation the rule is aimed at rather than an ordinary way of describing a
recurring class routine, and forcing the instructor into the subject slot
changes the sentence from being about Chloe's experience of archery to being
about the instructor's habits, which is not what the paragraph is doing.

**Replacement 1:** "Archery is ordinary at first, because the start of it is
butts at twenty meters, then thirty, then fifty, an hour a day of an
instructor walking the line to tell you what your elbow is doing, then
walking it again to say it a second time."

**Replacement 2:** "Archery is ordinary at first, because the start of it is
butts at twenty meters, then thirty, then fifty, an hour a day of an
instructor telling you what your elbow is doing and walking the line to tell
you again."

**Count: 2 called out.**
