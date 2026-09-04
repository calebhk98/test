# Voice pass: chapters 15 and 16

Scope: `chapters/15_twelve.md` and `chapters/16_thirteen.md` only. Dialogue and
chat lines were not touched anywhere. `passes/HOUSE_RULES.md` and
`passes/DO_NOT_FLAG.md` read first. Bex claiming the Saturday plan
(16, "Chloe has her Saturday half out... moving the kitchens and then moving
them back") and Iyad's retelling of the napkin evening (16, "Iyad tells it at
breakfast two days later... probably closer to twenty minutes") were left
untouched, per instruction, and nothing below edits or quotes from inside
either passage.

Checked with `measures/style_report.py` on both files after every edit. No
new tics, no banned phrases, no curly quotes or em dashes introduced. Word
counts after editing: chapter 15 stays at 4,871 words, chapter 16 at 4,142 —
both inside the 2,000-5,000 band, and the edits were all same-length
substitutions so neither count moved by more than a word or two.

## Changed

### 1. chapters/15_twelve.md — fake agency (active voice, nobody in it)

**Before:** "Physics starts in September and hands back half of what she was
told at ten with the reasoning underneath it, and psychology runs a term on
mostly reading, a third of each hour spent arguing over whether the studies
show what their authors claim."

**After:** "Physics starts in September, and half of what she was told at ten
is handed back this year, with the reasoning underneath it, while psychology
runs a term on mostly reading, a third of each hour spent arguing over
whether the studies show what their authors claim."

**Why:** "Physics ... hands back" gives the class itself the transfer verb —
a concrete handing-over motion with no one behind it, the book's own fault by
name. "Runs a term" is left alone; that one is schedule idiom (a term running
its length), not a transfer. Fixed with a passive: the doer here really is
diffuse (whichever teachers taught her at ten and now), so a passive that
keeps "what she was told" as the subject suits rule 1 better than inventing a
named teacher who never appears in the paragraph.

### 2. chapters/15_twelve.md — fake agency

**Before:** "The library draws her in about once a week now, because most
evenings there are people in the third floor common room with a game spread
over the table and a space kept for her at it."

**After:** "She goes to the library about once a week now, because most
evenings there are people in the third floor common room with a game spread
over the table and a space kept for her at it."

**Why:** A room does not draw anyone anywhere; she walks there. Fixed with the
person doing it, per the brief's first preference — no invention needed, she
is right there in the rest of the sentence.

### 3. chapters/15_twelve.md — person in the subject of a passive

**Before:** "By Christmas she can hold twenty-four seconds in the 10v1,
though she is still ranked only thirtieth out of ninety."

**After:** "By Christmas she can hold twenty-four seconds in the 10v1, though
she still sits thirtieth out of ninety."

**Why:** "She is ranked" is a person as the subject of a passive — the same
shape as "she is given," just about a number instead of an object. The
ranking body (the school's ladder) is never named or needed; "sits thirtieth"
states the same fact active, with her as the one doing it, and matches the
sports-standings idiom already natural to the scene.

### 4. chapters/16_thirteen.md — person in the subject of a passive

**Before:** "Ivy and Tomas want the answer handed over, though they can be
talked out of it inside a month, Beatriz arrives already knowing most of the
material and so takes a few minutes of the hour and uses them well, two more
turn up, work, leave."

**After:** "Ivy and Tomas want the answer handed over, though Chloe can talk
them out of it inside a month, Beatriz arrives already knowing most of the
material and so takes a few minutes of the hour and uses them well, two more
turn up, work, leave."

**Why:** "They can be talked out of it" puts Ivy and Tomas as subjects of a
passive. Chloe is the tutor of this class and the only person who could be
doing the talking-out; naming her costs nothing the paragraph does not
already establish and removes the passive.

### 5. chapters/16_thirteen.md — person in the subject of a passive (two clauses)

**Before:** "Differential equations run alongside real analysis from two
weeks into September; the analysis is what turns everything over, because for
years she has been handed a problem and asked to produce a number, at which
she was quick. Now she is handed something the whole room already believes
and asked to show that it follows from four lines at the top of the page that
stand outside argument."

**After:** "Differential equations run alongside real analysis from two weeks
into September; the analysis is what turns everything over, because for
years her teachers handed her a problem and asked her to produce a number, at
which she was quick. Now they hand her something the whole room already
believes and ask her to show that it follows from four lines at the top of
the page that stand outside argument."

**Why:** "She has been handed" and "she is handed" are the exact construction
named in the brief ("she is given"). "Her teachers" / "they" is a safe doer to
supply — the whole passage is about her schooling and teachers are the only
people who hand her problems and mark her proofs; nothing is invented that
the paragraph does not already imply.

**Totals: 5 edits, 6 clauses changed — 2 fake-agency fixes (one repaired with
a passive, one with a person as active subject) and 4 person-in-a-passive
fixes, all repaired active. Nothing was changed from active to passive; the
chapters had no case of that.**

## Called out, not changed

### chapters/16_thirteen.md, line 87 — the assigned borderline

**Current:** "It goes looking for recorders, anything on any network in range
that's recording video, and about half are still on the password they shipped
with, so it tries those first. For the changed ones it does everything else
at once, cracking, sniffing, brute force, and others besides," Ruth says,
watching Chloe's face throughout. "It runs the lot together and takes
whichever arrives first, so it's eight ugly things in a box and not one
clever thing, and one of them is always working. Once it's in, it writes
noise into the recording every so often, over part of the file. Delete a file
and somebody notices a file is missing. Make it noisy for a bit and that's a
camera being a camera."

**Why the voice might look wrong:** Read as narration, this would be exactly
the book's fault: an inanimate device given "goes," "tries," "runs," "takes,"
and "writes" with no one behind any of them, and it is not one of the three
chapters (32, 33, 35) where personified software is on the protected list.

**Why I did not change it:** It is not narration. Every clause quoted above,
start to finish, sits inside quotation marks and is spoken by Ruth — the
paragraph opens with her taking the lid off the box, the whole passage runs
in first person about "it," and it is broken only by "Ruth says, watching
Chloe's face throughout" mid-speech, which confirms rather than interrupts
the attribution. The house rule is explicit that dialogue is never touched
regardless of what voice a character chooses to use, so the question of
whether this device is on the protected personification list does not arise
— that list only matters for narration, and this is Ruth's own way of
describing something she built. A person is allowed to talk about her
machine like it has a mind of its own; that is characterization, not the
narrator's fault. Left exactly as written.

### chapters/16_thirteen.md, line 49

**Current:** "asking him is the whole of what she is allowed to do about it."

**Why the voice is wrong:** "She is allowed" puts Chloe, a named character, in
the subject of a passive, which the brief marks as the highest-priority fix
regardless of how obvious the institution behind it is.

**Why I did not change it:** "Allowed" here reads more like a statement of a
rule's reach than an event done to her by an actor, closer in shape to "she
is able to" than to "she is told." I was not confident that converting it
would read as an improvement rather than an invented bureaucratic subject
("the school lets her"), and this sentence closes out the whole Marek
thread, so I preferred to flag it rather than risk the landing line of that
strand.

**Replacement 1:** "asking him is the whole of what the mark scheme lets her
do about it."
**Replacement 2:** "asking him is the whole of what she can do about it."

### chapters/16_thirteen.md, line 91

**Current:** "What she has done is read three messages off the top of a
screen over somebody's shoulder, which she is entitled to do and which costs
a couple of seconds."

**Why the voice is wrong:** Same shape as the line above — "she is entitled"
is a person in the subject of a passive.

**Why I did not change it:** Same reasoning as line 49: "entitled" describes
a standing permission rather than something done to her at a moment, and I
was not confident a rewrite would not sound more like a rulebook than the
narrator. Flagging alongside the line-49 instance rather than guessing at a
fix for both.

**Replacement 1:** "What she has done is read three messages off the top of a
screen over somebody's shoulder, which the rules let her do and which costs a
couple of seconds."
**Replacement 2:** "What she has done is read three messages off the top of a
screen over somebody's shoulder, and she has every right to, which costs a
couple of seconds."

### chapters/16_thirteen.md, line 107

**Current:** "That takes the rest of the term; what results is slow, ugly,
and pushes exactly as much traffic at three on a Sunday morning, with all of
them asleep, as on a Thursday night with all of them typing."

**Why the voice is wrong:** "What results ... pushes" hands the finished
program the active verb for something they built it to do; nobody in the
sentence is doing the pushing.

**Why I did not change it:** This sentence sits three lines below "the
encryption holds throughout" (line 99) and two above "they run it ... and it
holds. It is still holding at Christmas" (also line 107) — an established run
of sentences describing this specific system's behavior once it is running,
none of which read as a slip so much as a way of marking that the thing now
runs itself. Rewriting just this one clause to add "they" would break that
pattern rather than fit it, and rewriting the whole run was outside what one
borderline call justified. Flagging rather than pulling on a thread that
reaches past this sentence.

**Replacement 1:** "That takes the rest of the term, and what they build is
slow and ugly, pushing exactly as much traffic at three on a Sunday morning,
with all of them asleep, as on a Thursday night with all of them typing."
**Replacement 2:** "That takes the rest of the term, and they build it slow
and ugly on purpose, so it pushes exactly as much traffic at three on a
Sunday morning, with all of them asleep, as on a Thursday night with all of
them typing."

### chapters/15_twelve.md, line 285

**Current:** "A man's chest going up and down a few feet away sits on that
list with the bolt cutters."

**Why the voice is wrong:** "A man's chest ... sits on that list" is a body
part as the subject of an active verb standing in for something Chloe is
actually doing — mentally filing the detail.

**Why I did not change it:** It is the last sentence of a passage that is
explicitly about her making a mental list ("she turns it over the whole way
through," two clauses earlier), and "sits on that list" reads as a
continuation of that list-metaphor rather than the flat, undirected fake
agency the brief's own examples show (the sheet, the name, the item that
"goes to Deb"). I was not confident this is the fault at all rather than a
deliberate extension of the sentence before it, so I flagged it instead of
cutting the metaphor the paragraph is building.

**Replacement 1:** "She puts a man's chest going up and down a few feet away
on that list with the bolt cutters."
**Replacement 2:** "A man's chest goes up and down a few feet away, and she
adds it to that list with the bolt cutters."

## Report

- Changed: 5 edits, 6 clauses — 2 fake-agency ("active with nobody in it")
  fixes and 4 person-in-a-subject-of-a-passive fixes. Every fix moved toward
  active voice with a real doer, or, in one case, toward a passive that
  properly hides an institutional doer nobody needed named. No active-to-passive
  fixes were needed in either chapter.
- Called out, not changed: 5, including the assigned borderline.
- Strongest call-out: the assigned one, chapters/16_thirteen.md line 87. It
  reads exactly like the book's central fault — an inanimate hacking device
  given "goes," "tries," "runs," "takes," "writes" with nobody behind any of
  them — until the quotation marks are checked against the paragraph, at
  which point the entire passage turns out to be Ruth's own dialogue about
  her own invention, attributed mid-speech ("Ruth says, watching Chloe's face
  throughout"), which puts it outside the pass entirely rather than merely
  off the protected personified-software list. Left unchanged for that
  reason.
