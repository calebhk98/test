# Delinking the teacher sheets

Ten sheets rewritten to `characters/_SHEET_RULES.md`: ALDANA, AMBERG, BAPTISTE, BELL,
DOYLE, HEARN, KOWALCZYK, PRAHL, SINCLAIR, VANCE.

`python3 verify_citations.py` on all ten now reports **0 quotations checked, 0 not found**.
Before the pass it found 49 citation-anchored quotations across the ten, of which about
thirty no longer matched the manuscript.

## What was removed everywhere, and what replaced it

**Every manuscript quotation.** Not one of the ten sheets now contains a double quotation
mark, with the single exception of the nickname in Kowalczyk's title. Where a quotation was
load-bearing it was rewritten as the move that produced it, so a writer can produce the next
one instead of repeating the one that exists.

**Every inline file and line reference.** Chapter references now appear only in a final
`Book-specific: navigation and continuity only` block that each sheet is complete without.

**Every statistic computed from the draft.** Words per line, percentage terse, percentage
hedged, percentage questions, counts of turns, counts of instances. The `Dials` tables were
rebuilt on the template's current rows (`length`, `at length`, `emotional range`) with
qualitative entries only.

**Every trait whose evidence was a count.** Signatures that were really "he does this twice,
six chapters apart" are now described as constructions: what shape they have, what triggers
them, and what breaks them if overused.

## Structural change

All ten now open, after the one-line identity, with two sections that did not exist before:

- **How they think people learn** - the teacher's theory, stated so it survives a change of
  setting.
- **What they do when a student fails** - the behaviour the theory produces when it meets a
  person it is not working on.

That pair is the portable core the brief asked for, and it is what the removed quotations
were standing in for. The rest of each sheet follows the current `_TEMPLATE.md`: `How they
talk`, `Under pressure`, `What they are good at and what they are not`, `Body and physical
business`, `How they treat people`, `Age and change`, `Do not write them as`.

`Known problems` sections were deleted from all ten, per the template's instruction that a
list of draft defects belongs in a pass document rather than in a character sheet. The
substantive contents of those sections are reproduced below.

---

## Per sheet

### BELL (10 quotations, 1 stale)

Removed the physics monologue that was quoted three times over as voice, signature and
length condition; the two-instance signature list; the "0/10 jokiness, 0% hedging, 0%
questions, 0% terseness" block flagged this morning.

Replaced with: honesty about the physics beats encouragement, so state the real dimensions
and let the instruction fall out of the figure; most of what looks like talent is counting;
escalate by increments and never announce them. When a student fails: run the same drill for
weeks with the whole room failing and hold the line, give the mechanism and withhold the
answer, concede the narrow point and keep the frame, and never praise a hit.

The **questions 0%** figure is gone, and gone as a fact rather than as a number. He now asks
few questions because what he needs is visible from where he stands, and the ones he asks
exist to make a student say a count out loud. A range coach with no questions in him is not a
person, and the flat zero was an artefact.

The metronome fact stands as corrected: on a post at the near end of the field for two years,
into his coat in front of the whole line the day it comes down.

### HEARN (7 quotations, 5 stale)

Removed the Federalist arithmetic, the two-word correction, the returned-paper economy quoted
against a line number, and the crisis line.

Replaced with the disposition the brief named: **he makes a demand ordinary by attaching it
to something the students already accept.** He picks a real person who already did several
times as much with worse tools, puts the numbers up where everyone can see them, does the
subtraction in public, and lets the arithmetic persuade instead of arguing. The specific
historical figure is now an example of the move rather than the definition of it, so a Hearn
in another setting reaches for a settler's logbook or a dead diarist and the character is
unchanged. Paired with the second half, which is the part that costs: quantity and quality
are separate problems, he says so once, and he marks only the second.

What he does when a student fails: he does not explain again. The case is made once, on day
one, before anything is graded, and that is the whole year's budget. After that a short note
naming one structural fault, and withholding as the sharpest thing he has.

The silent first pass looking for the first hedge is kept as his signature, with the note that
it stops working the moment anyone knows it is happening.

### AMBERG (1 quotation, stale)

Removed the four quoted fragments in the voice paragraph and the cryptography line quoted
from a chapter.

Replaced with the theory the brief identified, promoted from a footnote in the old
"what he'd teach if he could" section to the top of the sheet: **you cannot build a thing
until you have taken apart something somebody else built.** A design fails in the one place
its designer stopped looking, the only way to find that place is to open the thing, and after
thirty of them you know where people stop looking. Attempt it the other way round and you are
guessing at what the thing was for. He states the sequence as a sequence, numbered, on day
one, so the class knows it is being made to wait on purpose.

Two more theories sit under it: a page is marked on what is written on it and not on what is
in the writer's head, so a correct conclusion is not a demonstrated one; and young people get
the real governing document unabridged, framed as an ordinary obligation arriving on a
schedule.

His two subjects are now stated together at the top rather than one being discovered in a
subsection. See the flag below.

### KOWALCZYK (2 quotations, 1 stale)

Removed the headcount derivation, the inherited simile quoted verbatim, and the
"you're not getting worse" line.

Replaced with: fear is arithmetic that has not been done yet, so convert the threat into a
count and the cause of the count and it becomes a problem with a shape. Her portable trait,
as the brief specified, is now its own section: **what she tells a student who has stopped
improving.** You are not getting worse, the field got harder; here is the mechanism, in
numbers; this is the first real test you have had; it will happen to you again at a named
future age; the only instruction that exists is to learn faster than they do; now go, you are
holding up the next class. No comfort, no apology, no stopping what her hands are doing, and
she will not offer any of it unprompted.

Her gender is confirmed feminine throughout and the sheet says so in the continuity block.

### SINCLAIR (7 quotations, 4 stale)

Removed the intercom announcement, the diagnostic exchange, the closing instruction, the dry
aside, and the observation beat.

Replaced with: an announced exercise measures technique and an unannounced one measures
whether technique survives surprise, and only the second is trusted; and the register for a
real event and an exercise must be identical or the exercise was never worth running. What he
does when a student fails is the same thing he does when they succeed, which is the point: a
grade in the morning, against a stated standard, listing what went wrong, with no waiver for
a frightening night and no bonus for a good outcome.

His signature is now the look before the two words: he takes the scene in entirely, in
silence, first, which is what makes a two-word question sufficient.

**Three unsupported imports dropped.** See the flags below.

### PRAHL (5 quotations, 3 stale)

Removed the knights-and-knaves premise quoted at length, both refusals, and the
"that's absolutely fine, take your time" line.

Replaced with: a good hour is a complete one, built for the slowest listener, and depth comes
from time rather than from level, because she has a year of hours. And, held sincerely rather
than as cover, that patience is correct for a child this young and a request for something
harder is enthusiasm to reward rather than information to act on.

Her warmth and her refusals are written as the same gesture, which the brief asked for: the
ceiling is never named, the calendar is offered in its place, and something physical goes into
the child's hands so the exchange ends as a gift. The offer is real and generous and is more
of the same, and she does not notice that more of the same is not what was asked for. Naming
the ceiling would require having something behind it, and she has been given nothing to put
there.

### VANCE (3 quotations, all 3 stale)

Removed both signature quotations and the characteristic line.

Replaced with: nothing goes in until the child is safe enough to let it, built with structure
rather than sentiment - a rule that never renegotiates, a place in the room usable without
permission, a promise made out loud before a question is asked. When a student fails she goes
to them, gets to their level and stays down, and asks short doubled questions built to find an
event, which is genuinely good training and reliably misses a condition. Then she goes around
the building entirely and telephones the house herself, which is the most forceful thing she
does.

Short sheet kept short in the front half; the invented Home and small-stuff material carried
over unchanged.

### ALDANA (4 quotations, 3 stale)

Removed the characteristic line, both signature quotations, and the confiscation phrase.

Replaced with: together, or it isn't fair. The class is one body at one speed set by whoever
is last, and consistency is her whole ethic and also the mechanism by which she loses the
fastest child in the room. Ritual over intervention. Praise attached to work with the name
withheld. When a student fails: name the fact and stop, no why, no escalation, a small
time-boxed consequence and nothing afterward, and go quiet rather than sharp.

### BAPTISTE (4 quotations, all 4 stale)

Removed all four, including the two-word praise that the sheet had built its whole identity
on.

Replaced with: a rule handed over intact is a rule the student is renting, so redirect to the
question underneath, build the thing the rule is about, and never supply the shortcut. A rule
belongs to whoever has tested it, so go and try it, and a case that breaks the rule is the most
useful case there is. Praise attaches to the question, never to the child. When a student
fails: do it again from the beginning, identically, with no comment on the repetition, however
many times it is asked for, and never resolve a frustration you can see.

Single-scene caution applied: everything is stated as disposition, and the continuity block
says his whole speaking presence is one chapter.

### DOYLE (6 quotations, all 6 stale)

Every quotation on the sheet was dead, including the two words the sheet called his entire
verified dialogue. The manuscript now has him acknowledge the correction differently, which is
exactly the failure mode `_SHEET_RULES.md` describes.

Removed all six. Replaced with: put a claim on the record and then find out, so wrongness is a
measurement rather than a verdict; demonstrate the same standard on yourself and never say that
you are doing it; a mistake is only useful while it is still standing. When a student fails:
write down which part gave way and how far off the prediction was, grade against their own
number rather than a target, and leave the failed thing where it fell. When he is corrected: go
back to the source before agreeing, fix and acknowledge in one motion, then nothing at all for
the rest of the day, in either direction.

Kept short. The `Do not write him as` section carries the specific trap, which is that a warm
version and a cold version break the character identically.

---

## Flags: things that were wrong rather than merely hard-linked

1. **SINCLAIR's background does not exist in the manuscript.** The old sheet gave him
   classified special-operations tasking and cleared physical-security consulting, sourced to
   `SYNOPSIS_CHARACTERS_TIMELINE.md`. The independent audit in `SYNOPSIS_FROM_TEXT.md` is
   right: the manuscript's only special-forces reference is an unnamed line on a faculty page,
   and nothing attaches it to Sinclair. **Removed.** He has been given an invented background
   instead, security assessment of buildings full of people who could not be told they were
   being tested, which is portable, does not contradict the page, and produces the doctrine of
   the unannounced arrival from something other than a rank. It is invention and is marked as
   such here rather than on the sheet.

2. **SINCLAIR did not author the Watch doctrine.** The old sheet said the exercise is scored
   "against a standard he authored himself". Nothing in the manuscript attaches the doctrine to
   anyone. **Removed.**

3. **SINCLAIR does not run paintball.** Bell hands the markers out. The old Sinclair sheet did
   not claim it, but the reference document does, and both sheets now say so in their
   continuity blocks so the error cannot be reimported.

4. **SINCLAIR's locked door was somebody else's.** "Checks a locked door twice, out of what he
   calls procedure" appeared three times on the old sheet, in the signature, the `Would do`
   list and the continuity facts. The only character in the manuscript who checks a door lock
   twice is Eli, in ch32, reacting to something he has just read. **Removed entirely.** The
   check-it-twice disposition is retained only where the manuscript supports it, which is the
   silent read of a scene before he speaks.

5. **HEARN's last stand was wrong by nearly a factor of two, and by a factor of eighteen on the
   other axis.** The old sheet said "finally being caught after forty minutes"; the reference
   document says forty minutes against two hundred children. The manuscript has twenty past
   three to eighteen minutes to four, which is twenty-two minutes, against eleven students
   rising to twenty. Corrected in the continuity block.

6. **HEARN's subject was overstated.** He is listed in reference documents as teaching writing
   and history. The manuscript gives him writing and essays; political history is a separate
   slot with a different, unnamed teacher. Corrected. He still teaches through founding-era
   political prose, which is a method rather than a second subject.

7. **AMBERG teaches cryptography as well as law**, which the older synopsis missed and the old
   sheet had demoted to a subsection and hedged with "whether or not he holds the chalk for that
   particular class". The manuscript has him opening the cryptography year himself, on the first
   day, with the order of it. Promoted: both subjects are now in the first line of the sheet,
   and the theory of teaching that the brief identifies as his core is the theory he states in
   that cryptography opening.

8. **BAPTISTE and the synopsis's unnamed mathematics teacher are one person.** The old sheet
   already said this, in a note above the header that read as a research memo. Moved into the
   continuity block as a fact.

9. **DOYLE's one quoted line has changed under the sheet twice.** A first clause was cut by a
   prose pass as a banned construction; the surviving two words have since been rewritten again.
   No sheet should have been tracking it. It now tracks nothing.

10. **ALDANA and VANCE both carried a defect count as characterisation.** ALDANA's "the earlier
    brief's estimate of roughly 12 speaking lines overcounts what's quoted, which is 7" and
    VANCE's "the earlier brief's roughly 2 lines undercounted her; she has 10 quoted lines".
    Both are draft bookkeeping about a superseded brief and are recorded here rather than on a
    person's sheet.

## Not done

Nothing on these ten was deleted for being inconvenient to the lint check. Where a quotation
was carrying something real, the real thing was written out in the character's own terms and is
longer than the quotation was. All ten sheets grew.
