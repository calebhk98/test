# Delinking pass: NADIA, ELI, THEO, PRIYA, ODILE, FEN, OWEN, BRYCE, KAYLEIGH, DEB

Ten sheets rewritten to `characters/_SHEET_RULES.md`. No chapter was touched.

The governing instruction, in the author's words:

> The characters sheets shouldn't be ABLE to drift, because they shouldn't have
> quotations in them. That is hard linking. It's to describe the character, not
> the book. If you keep the exact dialogue, then you can't pick her up, and drop
> her onto a scifi lunar colony, or into a horror book with ghosts, or a Korean
> Drama.

`python3 verify_citations.py` now finds **0 quotations to check** across all ten,
down from 83 checked and 48 stale. The whole `characters/` directory is at zero.

## What was removed from all ten, without further note below

- **Every quotation**, including the ones inside tables, dial cells, bullet
  lists, Signature sections and Relationships lines. Where a quotation was
  carrying a real observation, the observation was rewritten as a property of
  the person: the move that produced the line rather than the line.
- **Every file and line reference used as the basis of a trait.** Chapter lists
  survive only in the navigation section at the bottom of each sheet.
- **Every measured statistic**: words per line, percentage terse, percentage
  hedged, percentage questions, line counts, turn counts, and the `Speaks: N
  lines` header field. Each was converted into the tendency it was measuring.
- **Every draft-defect list.** Per the updated `_TEMPLATE.md`, a list of things
  wrong with the manuscript does not belong in a character sheet. The ones worth
  keeping are recorded at the bottom of this document instead.
- **The `Do not confuse with` sections were kept** (the template allows exactly
  one section to mention another character) but rewritten without quotations and
  without the two stale line references both ELI and THEO were carrying.

Each sheet now follows the updated `_TEMPLATE.md` order and ends with a
`Book-specific: navigation and continuity only` section that can be deleted
without the sheet losing anything.

---

## NADIA

The thickest of the ten, and the one with a substantive correction in it.

**The priority was reframed, per the author's note.** The old opening section was
headed *She thinks everyone else has the problem backwards*, and described the
labour idea as "a pattern she keeps noticing that nobody around her seems to
notice." That is the framing the brief rules out: it makes her right and
everyone else slow. The replacement keeps the whole disposition, which is
portable exactly as it stands, and removes the superiority:

> The organisations around her treat people as a cost, and the question they are
> all solving is how to need fewer of them. Nadia's question is how to get enough
> of them. [...] Plenty of people around her are as sharp as she is and have
> simply ordered their wants differently: they want margin, she wants capacity,
> and neither of them got there by being cleverer than the other. Write her as
> someone with a different appetite, never as someone with a superior analysis.

The three things that made the old section good are all kept: that she never
argues it, that the overload is the same appetite pointed at herself, and that
the prose does not pick a side between reckless and justified.

**Removed:** twelve quotations, eight of them stale. Her "most characteristic
line" and both Signature examples were quoted proposals against specific line
numbers; the Signature is now written as a construction (she names the person
where a pronoun would be ordinary, flat, aimed at nobody) so a writer can build
the next one instead of repeating the one on file. Three Likes/dislikes bullets
were nothing but quotations with a label; they are now the dispositions
underneath them.

**Rule 3 defect fixed.** The dials asserted "questions measure 0% of her lines"
and "target 0%", and then the voice paragraph immediately described a rhetorical
question she does ask. A statistic contradicted on the same sheet by its own
evidence. Now: she essentially does not ask, and what looks like a question from
her is a statement wearing a question mark.

**Rule 2 defect fixed.** The old Known problems section opened by counting how
many substantive lines the whole sheet rested on and where they sat. That is a
measurement of a draft.

**Kept and rewritten in my own words:** the proportionality, the four-minute
command register and what it costs her, the money-for-her-father length
condition, the joint-resetting cleanup instinct, the asleep-and-straight-back
pattern, the bar-drift blind spot, the whole of Home, and the note about what is
actually funny about the confidence-outrunning-competence joke, which is a real
insight and did not need the scene to carry it.

## ELI

**Both stale Known problems dropped, as instructed.** `passes/audit/CAL_31-35.md`
found them today:

- Problem 1 asked for "one small beat anywhere earlier that shows him operating
  entirely outside Halstead's ranking." The manuscript already contains it, in
  the file, a few paragraphs above the line it calibrates, and better placed
  than a seeded earlier scene would be.
- Problem 3 flagged Ruth and Eli saying an identical six words back to back. The
  manuscript resolved it: the line is Ruth's now and Eli answers it with
  something of his own.

Neither was carried forward in any form. The calibration insight that Problem 1
existed to protect is not lost: it is now the sheet's opening section, written as
what it always was, a fact about him rather than a fix for the draft.

**Removed:** twelve quotations, four stale. The characteristic line, the
Signature pair, the twenty-minute teaching quotation, the delight-at-being-
outthought quotation, the speedrunning joke, the flat refusal to Chloe, and five
Likes/Relationships bullets that were quotations with labels.

**Rewritten as:** the reframe-then-answer move described as a move; the
contraction-removal signature described as an escalation ladder with a ceiling;
the gamified-stakes humour described as a register with a reason attached ("how
he keeps a thing interesting enough to go on working on"); and the
delight-at-being-outthought moved into `Under pressure`, where it is flagged as
his most distinctive reaction and the easiest to write wrong.

## THEO

**The thin section is now the thick one.** The brief asked for what he does with
a thing he cannot say, and it was previously scattered across five sections as
scene reports. It is now the opening section of the sheet, in five parts: he
keeps it completely; it does not sit still in him, and the delay is all anyone
sees; when he does disclose, the whole chain comes with it and the length shows
how long he sat on it; he gives the restriction before the content and does not
notice how much trust that is; and there is a version he never discloses at all,
which must stay unexplained. Plus what it costs him, which is the load-bearing
part: from inside, he cannot tell the difference between discretion and a step
he skipped without noticing. The fear underneath is not exposure, it is error.

That is the most portable thing on any of these ten sheets. It works unchanged
on the lunar colony, and it works in the ghost story with no adjustment at all.

**Removed:** fourteen quotations, four stale, including the characteristic line,
both Signature instances, the throat-clearing word, the disclosure quotation
(twice, in two sections), and five quotation-plus-label bullets.

**Rule 3 defect fixed.** The hedging dial read "target 15%+, no longer proposed.
His measured dialogue currently sits at 0%." A target percentage written into a
sheet as a law of the character, with the acknowledgement in the same cell that
the measurement contradicts it. Now: he hedges visibly and often, and the hedge
is an accuracy habit rather than a nerve.

**Rule 4 defect fixed.** The Signature section noted that both real instances sat
in one low-stakes chapter and asked a writer to extend the tic elsewhere. The
signature is now described as a construction with a trigger and a ceiling.

**Kept:** the whole of Home, which is where his syntax comes from and is entirely
portable; the objection-then-compliance pattern and the blind spot it produces
(the objection has never changed an outcome and he has not noticed); the
glasses; the shoulder tuck; the beehives.

## PRIYA

**No assertion about her presence in the ending survives.** The old sheet opened
"still at the same dinner table nine years later", argued in Known problems that
she is "named outright as one of the fixed core group" at the daily table, and
built a bullet around her being present and referenced in every chapter on the
list. All of it is gone, along with the counts it rested on. The navigation
section now states only which chapters she appears in and stops there. I did not
act on the manuscript question and have not touched a chapter.

**Removed:** five quotations, four stale, including her characteristic line, the
nine-minute horse monologue, the falling-asleep line, and the two-word signature
examples.

**Rewritten as:** the run-on described as a property with a warning attached
(trimming her to match the room removes the one thing the cast needs her for);
the start-mid-thought signature as a construction; and the horses condition with
its physical cost intact, because the cost is the good part.

**Rule 4 note.** Known problem 5 correctly observed that "still doing the horse
thing years later" overreaches what the draft shows. The sheet no longer claims
it as a textual fact; the riding is written as a disposition, and the navigation
section records only that she has ridden since she was six.

## ODILE

**Removed:** six quotations, three stale, all of them the same line. Her one long
speech was quoted in full three separate times, in the voice paragraph, in the
length condition, and again in Home, plus twice more in fragments.

**Rule 3 defect fixed, and it was severe.** The dials read "her three lines run
6, 7, and 25 words" and "2 of 3 lines 7 words or fewer". A percentage computed
from three lines is not a trait, it is arithmetic about a draft. The same three
lines were also the whole evidentiary base for the voice paragraph, the
Signature, and six of the ten `Would they say this?` bullets.

**Signature rewritten.** It was previously a pair of invented question-and-answer
exchanges set in quotation marks, which reads as text and is not. It is now
described as what it is: the bare number as a complete answer, with the absence
of the sentence around it as the actual signature.

**Kept, because it is the best thing on the sheet:** the ban on registering rank,
restated at the top with the important qualifier intact (it is a ban on
registering rank, not on feeling anything), and the emotional-legibility rule,
that everything she feels shows in breath, stillness, grip, appetite and pace and
never in a word. The two cut proposals from an earlier draft, the negotiated
language year and the fear of water, are recorded in the navigation section as
things not to reinstate, which is a continuity fact rather than characterisation.

## FEN

**Removed:** seven quotations, three stale.

**She now has a voice, and the sheet said she did not.** See the flagged item
below; this is a factual error rather than a hard link. The sheet's `Dials`
section opened "No quoted line exists to measure" and Known problem 1 read "No
verbatim line exists to build on. Any dialogue written for Fen from this point is
new work." The manuscript now gives her real dialogue, and it is precise,
systematic and completely in character. Her `How they talk` section is written
from it: she gives the complete rule of a system including what happens to
everything else when one item changes, and she closes an account of her own
method by saying whose it is.

**The length condition was right and is now confirmed by the text.** The old
sheet predicted, with no evidence, that what opens her up is somebody asking
about the *system* rather than the objects. That is exactly what happens in the
draft now. The condition is kept, with its cost, and the line about sitting up in
the dark to answer.

**Rewritten as:** the room-history list and the rock order described as one
instinct, with the blind spot named (she thinks impermanence means she should not
invest in a place, when the records are a real form of investment aimed at
objects instead of walls).

## OWEN

**Removed:** eleven quotations, eight stale. His sheet was the most hard-linked
of the ten by proportion: he has no dialogue at all, so every quotation on it was
somebody else talking about him, and the passes that rewrote those chapters
rewrote nearly all of it.

**Rewritten as:** the three-part correction at the top, which is the whole
character and needs no scene. He wanted to stay and could not do the work, and
the leaving was not a preference. Both things are true at once, that he wanted
the hard days to stop and did not want to leave his friends, and a writer who
resolves that into one feeling has lost him. He is not slow; he is behind only in
a room built out of exceptions.

The conflicting accounts of him, which the old sheet spent two Known problems
reconciling, are now one line in `How he treats people`: what he is to the other
children is a friend they liked, whose leaving they each account for differently
afterward, describing the version they saw. That carries the same insight and
survives the chapter being rewritten again.

**Cut without replacement:** the paragraph rebutting a theory in the reference
documents about which families stayed near the camp. That is a note about a
reference document, not about a person.

## BRYCE

Short sheet, kept short. **Removed:** eight quotations, six stale, including his
one substantive line quoted three times and the narrator's frame for how to read
it quoted alongside.

**The frame was the important part and it is now stated as the character.** He is
never being cruel: he reports a change with interest and no judgement in either
half of it, and then turns back around. That is at the top of the sheet.

**Internal contradiction fixed.** The `Dials` row read "at length: no attested
circumstance, and none should be invented", directly above a `When they talk at
length` section giving a real and good one (machinery behaving wrongly with
somebody about to touch it). The dial now names the condition the section
describes.

**Kept:** the uncle, the diagnose-before-you-touch method, and the observation
that his slowness and his accuracy come from the same place, which is the only
reason the character works.

## KAYLEIGH

Short sheet, kept short. **Removed:** five quotations, all five stale, which is
the whole of the quotation content on the sheet.

**A real correction, not just a delink.** The sheet's rule read "NO if it
contains a 'because', a qualifier, or any explanation of why she thinks what she
thinks." The manuscript contradicts this in both her scenes: she uses
because-clauses freely. What she actually does is give a reason-shaped answer
that is not a reason, and then, pressed on the real mechanism, restate the bare
assertion and move the game along. That is now the second half of the opening
section, and it is a better character note than the old rule was.

**Name-collision ruling.** She has no collision; the sheet carried a *name check*
line instead. The navigation section now records the ruling in one line, as a
fact, with no recommendation restated.

**Kept:** the delivery-while-turned-away signature, the rulebook-before-the-game
length condition and what it costs her, and the blind spot that she has no idea a
remark she has forgotten can be the thing somebody else is still carrying months
later.

## DEB

Short sheet, kept short. **Removed:** three quotations, all three stale, which is
all of them.

**Name-collision ruling kept as one line, in the navigation section**, stating
that both keep the name and neither should be renamed, with no recommendation
restated. The `Do not confuse with` entry survives, since that section exists for
exactly this and the risk of a later pass merging the two people is real.

**Rewritten as:** the kindly-and-inadequate section, which was the best thing on
the sheet, folded into the opening correction: the friction is ordinary, it costs
nobody anything, and the relationship reads warm on both sides. Plus a Signature
she did not previously have, which is the thing the old sheet was circling: she
converts an abstraction into a person, which is why the reframed explanation is
the one that lands for her.

---

# Flagged separately: things that were wrong, not merely hard-linked

1. **NADIA's priority was written as a superiority.** Addressed above. This is the
   one that mattered most, and it had leaked into three other places on the sheet
   besides the section it lived in.

2. **`FEN.md` asserted she has no dialogue. She does.** The sheet said "0 directly
   quoted lines", "No quoted line exists to measure", and "No verbatim line exists
   to build on." `chapters/10_april.md` now gives her a real exchange, in which she
   explains the ordering rule of the collection, how a new arrival displaces
   everything after it, and that she is taking the whole thing with her rather than
   leaving it behind. Any pass still working from the old claim will invent a voice
   for a character who already has one, and the one she has is good.

3. **`ELI.md` and `THEO.md` both pointed at a line collision that does not exist.**
   Both `Do not confuse with` sections told a writer to watch
   `chapters/35_nine_minutes.md:78 and :847`. That file is 172 lines long, so the
   second reference was never possible, and the echo the note describes is gone
   from the draft. Removed from both.

4. **`THEO.md` carried a hedging *target* as a law of the character**, with the
   contradicting measurement in the same table cell. This is the exact defect
   `_SHEET_RULES.md` rule 3 names.

5. **`ODILE.md` computed dials from three lines.** Percentages and word-count
   averages over a three-line sample, presented as her register.

6. **`KAYLEIGH.md` banned a construction she actually uses.** Corrected above.

7. **`BRYCE.md` and `OWEN.md` both had a `Dials` row saying no length condition
   exists and none should be invented**, sitting directly above a section
   supplying one. Both fixed by pointing the dial at the section.

8. **Still open in the manuscript, recorded here so it is not lost with the Known
   problems sections it came from.** None of these are sheet problems and I have
   not acted on any of them:
   - `chapters/29_the_file.md` states an internal cause for Theo's action in the
     narrator's own voice. No character other than the point-of-view figure gets
     one anywhere else in the book, and this one sits in his most important
     chapter. It should become an observable action.
   - Eli has one childhood scene and nothing between it and adulthood. Theo has no
     childhood dialogue at all and arrives fully formed as an adult.
   - Under low stakes, both Eli's and Theo's chat lines collapse into filler that
     could belong to anyone in the same conversation.
   - Owen has no directly quoted line anywhere in the book. Worth the author
     confirming that this is deliberate rather than an oversight; the sheet is now
     written as though it is, because the character is stronger that way.
   - Priya's absence from the closing chapters, against the text's repeated "all
     seven", is a manuscript question and is already recorded in
     `passes/audit/CAL_31-35.md`. Nothing on her sheet asserts anything about it
     either way.
