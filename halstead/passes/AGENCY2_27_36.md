# Agency pass, round two: the "it" pattern, chapters 27-36

Second loop over the same ten chapters as `passes/AGENCY_27_36.md`, whose
record was read first, along with `passes/HOUSE_RULES.md`, `passes/DO_NOT_FLAG.md`,
and `CLAUDE.md`. This pass's job was the class the first loop's narrower
`determiner + noun + verb` finder never ran against: `it + verb`, plus a
second look at the determiner class using the wider verb list this loop's
brief supplied (adding sits/stays/holds/lands/arrives/moves to the
goes/gets/comes/does the first loop checked).

Chapters touched: `31_ruth.md`, `35_nine_minutes.md`. No other file in the
span was edited. Chapters 32-36's `name: text` chat lines were not opened for
editing at all; only their surrounding narration was read.

## What stayed settled

Both refusals named in the first loop's record were left exactly as they
are: who carries the second box to Theo's desk in 29, who assigned the rules
document in 33. The personified autonomous software in 32, 33, and 35 (the
worm, the watcher, the tool) was read again under the "it + verb" finder and
left everywhere it appeared, for the same reason the first loop gave: it is
the plot's actual subject, not a hidden human agent. Chapter 28's
register-excused vocabulary was not touched. Chapter 31's new block where
Ruth asks who chose her at six was read but not edited, as instructed. Every
"do not disturb" passage in the brief (Nadia's dead man's switch speech and
its chat in 27; Deb hearing Chloe out in 28; Theo's file in 29; the Whitaker
geometry exchange in 30; the professor's pen-down beat in 31; "theo which
four" and Ruth putting it back up in 32; Theo's disclosure and Sam's one-line
answer in 34; the unanswered lines in 35 and 36) was confirmed in context and
left alone.

## Method

Ran the finder regex from the brief (`DET` and `IT` patterns) against all ten
chapters, lowercased for matching, then read every hit against the live file
in its actual case. For each hit I checked: is there a real person the
sentence could name instead, or is this idiom, a natural/physical process, a
stative camera fact, an already-settled device (the software personification;
body-part-as-actor for a character's own action, e.g. Nadia's sleeves in 33,
Ruth's hand to page seven in 35, the hand rising and falling in 36; a
deliberate refrain, e.g. the notebook beats in 30, "And it moves." four times
in 28's chat-interlude narration, the chat-goes/sits/stays-quiet family used
throughout), or quoted dialogue (never touched for this job, including chat
lines).

## Counts

- **"it" + verb read: 34** across the ten chapters (the finder's raw hit
  count before discarding regex artifacts, e.g. "emails like it land" where
  the true subject is "emails," not "it"; "Deb hears it out" where "it" is
  an object, not matched at all by the verb list).
- **"determiner + noun + verb" read: 61**, the wider verb list applied to
  the same ten chapters (this necessarily re-reads the narrower goes/gets/
  comes/does hits the first loop already resolved; those were not
  reopened, only the additional verbs were treated as new candidates).
- **Changed: 2**, both category 1 (the person who does it does it), both
  in the "it" class. Nothing in the wider determiner class needed a change:
  every added-verb hit was idiom, a stative camera fact, a natural process,
  an already-credited actor caught by a regex artifact (e.g. "the doorway
  comes off the frame" for "the man in the doorway comes off the frame,"
  "the desk sits back" for "the man behind the desk sits back," both cases
  where the real subject is a named person one or two words earlier than the
  regex's one-word window allows for), or one of the already-settled
  devices above.

## The two changes

- **31, narration.** "The mistake, she decides, is bigger than one office
  can fix, something upstream of advising and the registrar both. It goes
  in the folder under problems she'll solve once she works out who actually
  owns them." -> "...**Ruth puts it** in the folder under problems she'll
  solve once she works out who actually owns them." Ruth is the stated
  actor one clause earlier ("she decides"); the folder is a real object
  established two sentences before ("Ruth keeps the folder"). This is the
  same shape as a fix the first loop already made in this same chapter
  ("It goes on the inside cover of the notebook" -> "She puts it on the
  inside cover of the notebook"), just in the "it" class instead of the
  determiner class, which is exactly the gap this loop exists to close. I
  used "Ruth" rather than "She" as the subject on purpose, since the brief
  flags "sentence opens She/He + verb" as sitting at its target already.

- **35, narration.** "The rest of the messages get read once, and the
  phone goes face down on the nightstand." -> "**Chloe reads** the rest
  of the messages once and sets the phone face down on the nightstand."
  The paragraph's actor is Chloe (established a few lines up: "her badge
  scans," "she taps out one line to Ruth"), but the most recently named
  person in the two sentences before this one is Ruth ("Ruth answers within
  a minute"), so an unnamed "she" here would misdirect the reader as well
  as hide the actor; naming Chloe fixes both problems at once. This also
  matches the sentence immediately above it in the same scene, where Sam is
  named as the one who "sets his phone face down" rather than the phone
  doing it on its own - the parallel sentence already had it right, this
  one did not.

## What I read and left, with reasons (representative)

- **Idiom, already an established family in this manuscript.** "The room
  goes quiet" (27), "The chat sits quiet" (28), "the chat stays open" /
  "The chat stays empty" (31), "The chat holds" (32), "The chat sits on
  that line" (34), "And it moves." x4 as a narration refrain closing four
  chat exchanges in 28. None of these hide a person; a chat or a room going
  quiet is the ordinary way English says nothing more happened.
- **Stative camera fact.** "that number sits in front of her" (27), "the
  building holds fifty-odd people" (28), "The floor holds about sixty
  desks" (29), "a door that always sits half open" (31), "the float stays
  half counted in front of her" (36).
- **Natural or bureaucratic process with an obvious or irrelevant doer.**
  "the heat off the dryers comes through the floor" (27), "Bloods drawn at
  the debrief... came back the same" (29), "The result arrives by mail"
  (30), "The clearance comes through in December" (30), "collection
  against the channel comes back empty" (34), "the document arrives" (33).
- **Already-settled device, re-confirmed.** The worm/watcher/tool
  personification in 32, 33, 35; the notebook refrain in 30 ("Into the
  notebook goes the fact...," "The reasoning goes down..."); body-part-
  as-actor in 33 (Nadia's sleeves), 35 (Ruth's hand to page seven), 36 (a
  hand rising and falling in Priya's account of captivity).
- **Regex artifact, real actor already named nearby.** "the doorway comes
  off the frame" / "the desk sits back" (27, both actually "the man...");
  "A woman by that window runs an office pool" (28, the woman is the
  stated subject, not hidden).
- **Quoted dialogue and chat lines, not in scope.** Nadia's switch speech
  and its chat (27); Whitaker's "It goes into your file" and Chloe's lines
  in the clearance interview (30); Ruth's "It holds because the boundary
  term cancels" inside the protected pen-down scene (31); every chat line
  in 32, 33, 34, 36 that used one of these verbs, including the ones about
  the tool itself ("it moves about forty minutes total," "then two of you
  carry it if it goes wrong").
- **Deliberate ambiguity, the chapter's own point.** Chapter 36's opening
  paragraph (a bench that "arrived without anybody asking him," a card
  "slotted into a bracket," blinds "already down") describes an unnamed
  support network on purpose; none of these were run through the
  DET/IT patterns as-is but came up while reading the surrounding hits, and
  naming a doer here would answer a question the chapter is built to leave
  open, matching the brief's note on the unanswered lines in 35 and 36.

## Verification

`measures/style_report.py chapters/31_ruth.md` and
`measures/style_report.py chapters/35_nine_minutes.md` were run after the
edits: tic scan reports none found in either chapter, sentences with 2+
"and" sit at 8.2% (31) and 5.8% (35), both comfortably under the 10%
ceiling the brief warns about, and neither number moved in a direction the
brief flags as a risk. `measures/check_edits.py --chapters 31 35` reports 0
problems (no hard breaks, no em dashes, no curly quotes) and both chapters
remain inside the 2,000-5,000 word band, at 2,863 words (31, +1 against
the pre-pass baseline) and 2,108 words (35, +0), both single-word deltas
from swapping a subject in for "it." `grade.py` was not run, per instruction, since other
agents were working at the same time.

## Report

Read 34 "it + verb" instances and 61 wider-verb "determiner + noun + verb"
instances (this second number necessarily overlaps with the first loop's own
reading of the narrower goes/gets/comes/does slice of the same pattern,
which was not reopened). Changed 2, both by giving the action to the person
who does it: Ruth putting a problem in her own folder (31), Chloe reading
her messages and setting her own phone down (35). Both were "it" instances
sitting one sentence away from where the true actor was already named,
exactly the small share the brief describes. Nothing in either class was
downgraded to a passive; nothing was left that reads to me as a person
disguised as a process, beyond the small number of regex artifacts and
idioms catalogued above, which a reader would not trip on because in every
one of those cases either the real actor is already stated in the same
sentence or the vagueness is the chapter doing something on purpose (the
software's own agency, the unnamed support network in 36).
