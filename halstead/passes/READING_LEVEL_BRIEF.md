# Reading-level pass: the brief

One agent, one chapter. Nobody edits a file that is not their chapter.

The book measures at a fourth-grade reading level and loses to all 23 books in
the comparison corpus. The goal is to raise the measured level toward ninth
grade without breaking the prose rules, the style rules, or the characters.

## Read before you touch anything

- `PROSE_RULES.md` and `STYLE_RULES.md`. These are binding.
- `RAISING_THE_LEVEL.md`. This is the method: five mechanisms that work, the
  paragraph finding, the front-loading ceiling, and what not to do.
- The character sheet in `characters/` for anyone who speaks in your chapter.
  Each has a "When they talk at length" section naming the conditions that open
  that person up and what it costs them. **This is an invitation.** Where a scene
  meets one of those conditions, giving that character more to say is authorised
  and wanted, and you do not need to come back and ask. Where it does not, leave
  the line alone.

## The order of work

**1. Measure.**

    python3 prose_grade.py chapters/NN_x.md
    python3 style_report.py chapters/NN_x.md

Your chapter's three worst measures are in your task. Confirm them yourself.
The chapters differ: one is choppy, another is already long-sentenced and
short-paragraphed. A change that helps one hurts another.

**2. Plan, in writing, before editing.**

Write `passes/plans/NN.md` first. For each change: the quoted text now, what it
becomes, and which measure it moves. Then look at the list as a whole and cut
anything that moves a measure the chapter is already winning on, anything that
is padding, and any added dialogue whose character sheet condition the scene does
not actually meet.

This step is the point of the pass. The previous round edited immediately, got
the mechanical wins, and missed everything that needs the whole chapter in
view, which is both paragraph measures and sentence-length variation.

**3. Edit, then measure again.** Report the before and after for all sixteen.
A pass that improved your three targets and quietly cost words per paragraph
has not finished.

## The levers, strongest first

1. **Break runs of three or more short sentences.** The highest-leverage change
   in the book. Combine two of them with a subordinator so the run becomes a
   long sentence next to a short one. The runs that matter straddle narration
   and dialogue, where the pattern hides across a quotation mark.
2. **Join paragraphs that belong to one beat.** 54.2% of the book's paragraphs
   are a single sentence, against a corpus high of 54.5%. Ask of each
   one-sentence paragraph whether the break above it is doing work. Where it
   is, keep it: a one-sentence paragraph after four long ones is a device.
   Where it is habit, join.
3. **Vary the length deliberately.** Sentence-length CV is the measure almost
   every chapter loses worst on, and it does not improve by making everything
   longer. It improves by making the long ones longer and leaving the short
   ones alone.
4. **Absorb an "and" chain into subordination.** "She did X and then Y" becomes
   "When she had done X, Y", or the same clause placed mid-sentence.
5. **Stage the physical correlate.** Rule 23 asks for the physical action
   instead of the named feeling, and a located action wants a subordinate
   clause to place it. Complexity from staging, not from commentary.

## Hard limits

- **No em dashes.** Anywhere, dialogue included.
- **No curly quotes.** The manuscript is written with straight ones.
- **No trailing explanatory clause.** Banned, and moving it to the front is not
  the answer either, see below.
- **Front-loading is capped at 3.3% of sentences.** That is the highest rate any
  book in the corpus reaches. `prose_grade.py` prints yours under "monitored,
  not graded". If you go over, move the clause inside the sentence instead of
  deleting it: same subordination, same comma, no habit.
- **Do not pad.** Every added word must be a real combination or a real
  subordination. Filler raises words-per-sentence and makes the prose worse.
- **Do not reach for a fancier word.** Lexical diversity improves by choosing a
  different ordinary word, not a longer one, and it is a drafting property that
  a line edit will not move much. Do not spend your budget on it.
- **Keep the heading on line 1 and the italic date line on line 3.**
- **Do not change what happens.** No new events, no new dialogue beats, no
  changed facts. This is a sentence-level pass.

## When you are done

    python3 check_edits.py --chapters NN

It compares your chapter against the version in git and fails on a lost hard
line break, an em dash, a new curly quote, or a missing date line.
