# Child-voice pass: the brief

One agent, one chapter. Nobody edits a file that is not their chapter.

**Read `THEY_ARE_CHILDREN.md` first.** It is the diagnosis and the specification.
Then `PROSE_RULES.md` and `STYLE_RULES.md`, then the character sheets in
`characters/` for everyone who appears in your chapter.

## The problem you are fixing

Outside readers of chapter 1 concluded Chloe was not human: an alien
anthropologist, an artificial intelligence, a creature passing. The readers who
did think she was human thought she was autistic. She is meant to be a gifted
six-year-old.

The cause is in `THEY_ARE_CHILDREN.md` and you must read it before touching a
line. In short: the narration is flat, the book is inside Chloe's head, so her
inner life is rendered as measurement, and analysis appears where a feeling
should be.

## What to do

1. **Find every place a feeling was skipped.** The tell is a sentence that reports
   an absence ("nothing is wrong", "nothing big enough to cry about"), or analysis
   arriving with no feeling in front of it. Put the feeling on the page first, as
   something in the body or in what she does, and let the working-out follow. The
   order is the fix. A clever child who is hurt and then picks the moment apart is
   human; one who picks it apart instead of being hurt is not.
2. **Give the children bodies.** Fidgeting, running, being hungry or tired or too
   hot, sitting on hands, wanting to be picked up, hanging off a parent, kicking a
   chair leg. Almost none of this is in the book and all of it is free.
3. **Make wanting visible.** These children want things constantly and the text
   currently renders only the behaviour that follows from wanting.
4. **Let them be children.** Silly, loud, unfair, wrong, interrupting each other,
   laughing at something that is not funny, embarrassed by a parent. They believe
   they are ordinary children at an ordinary school. Nothing about their register
   should be cold or adult. What marks them out is what they notice and how many
   steps they hold at once, never how little they feel.
5. **Ration the exact numbers.** Rule 32 already bans this as a default. "Two
   days", "four minutes ago", "twenty-seven blanks", "three separate occasions" in
   ordinary scene-setting is the narration counting, not the character. Keep it
   where precision is the character under pressure; use ordinary description
   elsewhere.
6. **Check the morals.** They are children with a child's ethics, slightly off
   baseline. Their reasons for doing things are a child's reasons: fear of being in
   trouble, not wanting a friend to be hurt, not wanting to look stupid. Never an
   operative's risk calculus.

## What not to do

- **Do not name the feeling in the narration.** Rule 23 stands. No "she felt sad",
  no "her heart going". The feeling arrives as a specific physical thing or as an
  action, and it is unexpected rather than stock.
- **Do not let the narrator editorialise, rank, explain, or console.** The
  flatness of the narration is not the problem and is not changing. What is
  changing is that the narration reports a child rather than an instrument.
- **Do not change the plot.** Same events, same order, same outcomes.
- **Do not lower the chapter's reading level.** Run `python3 prose_grade.py
  chapters/NN_x.md` before and after. The last three passes raised these numbers
  and this pass must not spend them. Expect the word count to rise.
- **No em dashes, no curly quotes.** Heading on line 1, date line on line 3.

## When you are done

    python3 check_edits.py --chapters NN

Report what you changed, and the grade before and after.
