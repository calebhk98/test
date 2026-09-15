# Expansion pass: the brief

One agent, one chapter. Nobody edits a file that is not their chapter.

Chapters 1 to 19 run 1,900 to 4,500 words. Chapters 20 to 25 run 199 to 1,028.
They are not short chapters, they are outlines: the beats are named and the scenes
around them were never written. This pass writes them.

## What you are adding

**Word count is the point of this pass, and it has to be real prose.** Your target
is in your task. Expect to roughly triple or quadruple what is there. That comes
from:

- **Scenes that are currently summary.** Where the chapter says a thing happened,
  stage it: who is in the room, what they are doing with their hands, what gets
  said. A sentence like "The essays take an evening each" is a scene nobody wrote.
- **Dialogue.** Read the "When they talk at length" section on the sheet of anyone
  who speaks. It names the conditions that open that person up. **It is an
  invitation, not a permit.** Where your scene meets one of those conditions,
  giving that character a real turn is authorised and wanted. Half the spoken lines
  in this book run to three words or fewer, and the last pass over ten chapters
  added zero words of dialogue, which is the problem this instruction exists to fix.
- **Consequence.** Most of these chapters state an outcome and move on. What did it
  cost, who noticed, what happened the following week.
- **The people already named but not present.** Several of these chapters mention a
  character in one clause who could be in the room instead.

## What you are not adding

- **No new plot.** Every event in your chapter stays, in the order it is in, with
  the same outcome. You are writing the parts between and around them. If your
  chapter says Chloe applies to fourteen places and gets twelve, that is still what
  happens.
- **Nothing that contradicts an adjacent chapter.** Read the chapter before yours
  and the chapter after before you write a word.
- **No explanation of the school itself.** Several things about Halstead are
  deliberately unexplained at this point in the book: how students are selected and
  why, why the ages are what they are, why they are taught to shoot, who set the
  place up and what for. These are answered later, elsewhere, and they are not
  yours to answer, guess at, hint at, or have a character work out. A character may
  wonder aloud. Nobody may be right.
- **No padding.** Length from filler is worse than no length. Every paragraph you
  add has to carry an event, an image, a fact, or a line somebody says.

## Write it at the level, do not write it flat and fix it later

Three passes have now been spent raising the reading level of prose that was
drafted flat. Do not create more of that work. Before you start, run:

    python3 prose_grade.py chapters/NN_x.md
    python3 style_report.py chapters/NN_x.md

and again when you finish. **The new prose should not drag the chapter's numbers
down.** In practice that means: sentences that carry two clauses as often as one,
paragraphs that run to two or three sentences rather than always one, and a
handful of genuinely long sentences per chapter. The corpus benchmark is 14.6
words per sentence and 28.6 words per paragraph. `RAISING_THE_LEVEL.md` has the
mechanisms; read it.

## The rules that bind

- `PROSE_RULES.md` and `STYLE_RULES.md`, in full, before writing.
- **No em dashes.** Anywhere, dialogue included.
- **No curly quotes.** Straight ones only.
- **No trailing explanatory clause.** Front-loading a subordinate clause is capped
  at 3.3% of sentences; `prose_grade.py` prints your rate.
- **The narrator stays flat.** The flatness is the narrator's, not the cast's. The
  characters can be emotional, funny, and difficult; the prose reporting them does
  not editorialise.
- **Keep the heading on line 1 and the italic date line on line 3.** Do not change
  the date line. Anything you write has to fit inside the months it names.
- **Section breaks in these chapters are a line of sixteen underscores.** Match what
  the file already does.

## When you are done

    python3 check_edits.py --chapters NN

It fails on an em dash, a new curly quote, a lost hard line break, or a missing
date line. A large positive word delta is expected here and is not a failure.
