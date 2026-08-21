# House rules

Standing constraints for anyone editing this manuscript. These outrank the
target in any brief: a pass that hits its number by breaking one of these has
failed, and the number gets given back.

## 1. Never talk to the reader

Nothing in the prose may exist to make sure the reader knows something. Not to
repeat a point already made, not to nudge, not to wink, not to explain what a
beat means. Scenes read as real interaction between people who are unaware of
being read.

The author's position, in his words: *it is talking down to the reader, and
assuming they are too stupid to figure anything out themselves. It is
patronizing and a lot of readers hate it.*

What this looks like in practice, all of it found in this manuscript:

- A sentence that restates what the scene just dramatized.
- A clause appended to name the feeling the action already carried.
- The narrator glossing an echo the reader can see: *"which is either a
  symmetry or a warning and she has fifteen minutes to decide which."*
- *"which is exactly what X had always done"* constructions.
- A character explaining something the draft left implicit, because the
  rewrite needed a longer sentence and the explanation was the nearest filler.

The last one is the specific hazard of the reading-grade work. Spelling out a
logical joint is one keystroke away from spelling out the point. The joint is
between two clauses; the point belongs to the reader.

## 2. One paragraph convention

Blank line between paragraphs. No two-trailing-space markdown hard breaks
anywhere in the book. Chapters 1-6 used the old convention and are being
converted; `check_edits.py` reports any trailing-space line as a defect.

## 3. No em dashes, no curly quotes

Straight quotes throughout. Em dashes are banned in narration and dialogue
alike; use a comma, a colon, a semicolon, or a second sentence.

## 4. Word count

2,000 to 4,000 per chapter, and the average is meant to sit around 2,500 to
3,000. A few longer chapters and the occasional short one are fine. The
ceiling is not a target: do not expand a chapter toward it.

## 5. Reading grade climbs with Chloe's age

There is no single book-wide number. Each band has a floor, judged on the band
average rather than per chapter, and a chapter already above its band is left
where it is:

| chapters | ages | floor |
|---|---|---|
| 1-10 | 6-8 | 5.5 |
| 11-15 | 8-12 | 6.0 |
| 16-22 | 13-19 | 7.0 |
| 23-35 | adult | 8.0 |

Book floor 7.0. The point of the bands is that the book gets harder as she
gets older, so raising an early chapter above a late one works against the
design even when both clear their floors.

`grade.py --one <chapter>` prints the band the chapter is judged against.

## 6. Never lower a chapter that is already there

If a chapter already clears its band, leave the number alone. Prose repair
that costs a little reading grade is fine and expected; deliberately reducing
a figure to fit a lower bar is not.
