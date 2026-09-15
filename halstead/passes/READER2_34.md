# Reader pass, chapter 34 (The Files)

Word count before: 1,960. Word count after: 1,944. Shorter, as required.
`grade.py` scorecard: 59 of 59 measures passing (checked before and after;
no regression, see the register.py note below for the one measure that came
close).

## The twenty-two-second consensus

Line 25 (as written): "...agreed on by all of them, the only detail in the
account that was." The finding is right: men who disagree on sequence and
can't describe a face would not independently agree to the second on a
duration. Changed the source of the number from the men's testimony to the
one thing in the chapter that could produce an exact number without anyone's
memory: the footage gap. New line: "...taken off the gap in the footage
instead of out of anyone's memory, the only precise thing in the account."
This also answers "were the observers timing it" without spelling it out,
and it sits two paragraphs ahead of the footage reveal at line 31, so it
reads as a plant rather than a spoiler.

## Graduates since 2013

Confirmed the problem: the standing line says the file has "kept the
sentence" since it opened in 2013, when the cohort was six or seven years
old and the first graduation (per the brief) was 2023. Fixed by making the
retyping-clerk sentence acknowledge the one word that did change: "the word
changing once, from students, the year the first class left, and after that
only the date stamped under it." This keeps the "same paragraph get
retyped" image intact while admitting the file didn't always say
"graduates."

## All ninety-one files from 2013

Checked this against the backstory in commit 94fddc0 ("the government does
not know about the school until roughly five years after it opens"), which
puts the case-opening in 2013 as the moment the government found the whole
cohort at once, not a slow one-by-one process. So a shared opening date for
the case is not itself implausible. But the sentence "Every file starts
with a name, a date, a single photograph..." was reusing "a date" right
after "opened in 2013," and could be misread as claiming every individual
photo and letter is dated to that same year. Changed "a date" to "its own
date" so each file's first page is explicitly its own, not the case's.

## Ruth reading the paragraph about the box

Confirmed: the quoted report (lines 31-33) is about missing footage and
missing recordings; it never identifies whose device caused it. Changed
"Ruth reads the paragraph about the box" to "...about the footage," which
keeps the investigators' ignorance intact and matches the vocabulary
already used two lines earlier ("Footage was sought...").

## Theo's twenty minutes, twice

Confirmed the loop, and confirmed it is not already resolved by the
existing text. Line 9 said Theo goes outside "for twenty minutes before he
comes back in," then "keeps reading from the line he left off on" - a
completed round trip, narrated early. Line 125 then has him "finish his
twenty minutes and go back in, the file exactly where he left it, closed" -
the same walk, restated as still in progress at the end. Cut from line 9:
"for twenty minutes before he comes back in" and "He keeps reading from the
line he left off on." Now the opening list's promise ("the twenty minutes
outside still ahead of him"), the trigger and the text to Sam (line 9,
unresolved), and the actual return (line 125) run in one direction with no
rewind. Net eight words saved.

## Chloe "half a country away"

Checked chapters 24, 29, 30, 32, 33 for anything placing Chloe's
clearance job at a specific distance from Ruth's Cambridge lab; found
none. Her geography is desk, kitchen counter, an apartment whose lease she
signed. Rather than invent a relocation this chapter has no room to
establish, cut "half a country away" from the line about her typing into
the group chat.

## Ruth reading a page she hadn't found

Confirmed the sentence as written compares "unexplained now" to "the first
time she read it... years before she ever found out the file existed,"
which has her reading a specific page before she knew of the file that
contains it. Changed the comparison to the event rather than the reading:
"...exactly as unexplained now as it was the night it happened, years
before she ever knew the file existed at all." This also reads as a nod to
the earlier chat lines about her having built the box "in a weekend" without
understanding it fully at the time.

## "It is not wrong any more"

Cut, per the brief. It follows the file's own logic sentence ("...the file
has no way of knowing it, so the two of them appear side by side in it"),
and the extra sentence was the only place in the paragraph asserting a
change in Chloe and Nadia's relationship without any surrounding evidence
for what changed. The paragraph is a beat shorter and no longer makes that
claim.

## Opening inventory (floors, counters, badges, pens)

Checked git history before touching this: commit `fe68cbd` (2026-09-10,
yesterday) already cut this exact paragraph for this exact reason ("chapter
34's opening no longer walks all seven of them through a gesture each
before the file says anything, which the author had already flagged"). The
reader was almost certainly looking at the pre-cut version. Left it alone.
It's already down to one clause per person, Kavi's pen-turning gesture is
already gone, and this pass didn't need the word budget from it (the fixes
above net a savings of 16 words on their own).

## Register regression caught and fixed

My first pass at the fixes above (before this final version) added
"recordings" and a second "graduates," both nine-plus-letter words, and
pushed chapter 34 from 4.09% (passing, under the 4.11% flag) to 4.22%
(failing) on `measures/register.py`. This is the exact failure mode the
brief warned about. Fixed it three ways: used "footage" instead of
"recordings" for the box-paragraph fix above (matches vocabulary already in
the chapter), dropped the redundant second "graduates" from the students
line (the word only needs to be named once, since the standing line already
says it), and swapped one pre-existing, untouched "paragraph" for "part" at
line 29 to bring the chapter back under the line. Final register score:
4.07%, below the original 4.09%.

## Not changed

Sam's own twenty-minute wait at line 101 ("a good twenty minutes before
they're stood down") is a separate, unrelated use of the same number and
was left alone; it isn't part of the Theo loop.
