# Stripping the negative-space tic: the brief

One agent, a named set of chapters. Nobody edits a file outside their set.

Read the section "The corrections to this document" at the end of
`THEY_ARE_CHILDREN.md` before anything else, then `PROSE_RULES.md` and
`STYLE_RULES.md`.

## The problem

Told to show a feeling without naming it, the last pass reached for the same
shape every time: the thing a character did not do.

> He doesn't look up. Nobody says anything. She reads it twice and doesn't add to
> the thread. He doesn't put his hand up again for the rest of the lesson. Ruth
> glances at him and doesn't say anything about it. She isn't hungry.

Measured against 23 books:

| | all negation | the device alone |
| :-- | --: | --: |
| corpus median | 7.8% of sentences | 3.2% |
| corpus highest | 17.5% | 6.1% |
| this book | 17.8% | 5.5% |

The book uses more negation than any book in the comparison set. **955 sentences
carry a negative and 295 of them are the device**, a narration sentence whose
whole beat is an absence.

## What you are doing

**Target: no more than one or two device instances per chapter, and cut ordinary
negation wherever a positive says the same thing.** The device is a real
technique and the book may keep its best instance in each chapter. Everything
else goes.

Three ways out, in order of preference:

1. **Replace with what the character does.** This is almost always available and
   almost always better. Not "he doesn't put his hand up again" but what his hands
   do instead. Not "she doesn't add to the thread" but what she does with the
   phone. The withholding survives; the announcement of it does not.
2. **Replace with what the next person does.** "Nobody says anything" is usually
   somebody changing the subject, or the scene moving, or one specific person
   looking somewhere specific.
3. **Cut the sentence.** A surprising number of these carry nothing. If removing
   it costs the paragraph nothing, it was never a beat.

## What not to touch

- **Dialogue.** People say "I don't know" and "that's not a number" constantly and
  that is speech, not the device. Only narration is in scope.
- **A negative that is the actual fact.** "The school doesn't call" is the event of
  that scene. "He never learned to swim" is a fact about a person. Keep these.
- **The best one in the chapter.** Pick it deliberately and say in your report
  which one you kept and why.

## The second fault, in the same pass

**Explaining a thing straight after staging it.** Rule 6, arriving in a new
costume: "Nobody explains to her afterward that she got the length wrong the first
time. Nobody has to." "The chat is the one place all of them are still in the same
room." Stage the thing and stop. If the meaning is not reachable from the staging,
the staging is wrong and a sentence of explanation will not rescue it. Cut every
one of these you find. They are frequently attached to a negative, so the two jobs
overlap.

## Measuring your work

    python3 prose_grade.py chapters/NN_x.md

prints `sentences whose beat is a negative %` under `monitored, not graded`, with
the corpus low, median and high beside it. Run it before and after on each of
your chapters and report both.

Do not lower any chapter's maturity percentile, do not change any plot, and do not
reintroduce a named feeling in narration to replace a negative you removed. No em
dashes, no curly quotes, heading on line 1, date line on line 3. Finish with
`python3 check_edits.py --chapters NN`.
