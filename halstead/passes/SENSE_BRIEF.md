# Reading for sense

You are checking one thing: **does the writing make sense.** Not whether it is
good. Not whether the style is right. Not whether words repeat. Whether each
sentence means something, and whether each thing that happens could happen.

Do not rewrite anything. Do not suggest replacements. Identifying the problem is
the whole job, and a precise identification is worth more than a fix.

---

## Pass one: the chapter on its own

Read nothing but your chapter. Work down it from the top, one paragraph at a
time, and for each paragraph **say to yourself, in your own plain words, what
happens in it.** Most paragraphs will be fine and you write nothing.

Write an entry whenever one of these seven tests fails. Each test has an action
you perform, not a pattern you match. Do the action.

**1. Say it in your own words.** If you cannot restate a sentence plainly, quote
it. Some sentences have the shape of meaning without the meaning.
*Invented example:* "He crossed the room and then, softly and second, sat down."
"Softly and second" cannot be restated because it does not mean anything.

**2. Name what each joining word joins.** For every *instead, anyway, but, so,
then, for once, even so, which is why*, say out loud what is on each side of it.
If you cannot, quote it.
*Invented example:* "She checked it twice and handed it in anyway." Anyway
despite what? Nothing before it gives a reason not to hand it in.

**3. Say where each object came from.** For every physical thing named, say when
it entered the scene. Quote anything that appears from nowhere, and anything
described in detail that then does nothing at all.
*Invented example:* a character eats someone's chips in a scene where no food has
been mentioned.

**4. Say why each person did that.** For every action and every line of dialogue,
answer: why did this person do this? If your only answer is "so the scene could
happen" or "so the reader would learn something", quote it.

**5. Say where everybody is.** Can you place the people in a room, and say what
their bodies are doing? A conversation happening nowhere, with nobody moving, is
an entry.

**6. Check the order and the arithmetic inside this chapter.** Does anything
happen before the thing it depends on? Does a number, a count, a date or a season
change between one paragraph and another?

**7. Check the size of each reaction.** Somebody gets remarkable news and does not
react; somebody reacts enormously to nothing; an institution notices something
alarming and does nothing about it.

Write these to your report under `## Pass one`, in chapter order, each with a
line number, a verbatim quote, and one sentence saying what is wrong.

---

## Pass two: with the context

Now, and not before, read `SYNOPSIS_CHARACTERS_TIMELINE.md`, `chronology/BOOK.md`,
and the sheet in `characters/` for every named person who appears in your chapter.

Then go back through the chapter with one question in mind for every person in
it: **does this person know what the text has them knowing, and would this person
do what the text has them doing?**

Four things in particular.

- **Something a character could not know.** The narration sits close to Chloe. If
  she believes something, she cannot act as though she knows otherwise, and the
  narration cannot know it either. The same applies to any character in their own
  scene.
- **Something a character would not do or say.** Check every line against the
  person's sheet: their register, what they care about, how they behave when
  challenged, what they are and are not good at.
- **A number or fact that contradicts the sheets or the rest of the book.** Ages,
  rates, workloads, who taught what, who was where.
- **Somebody behaving unlike their profession.** A doctor, an admissions officer,
  a soldier, a teacher, a police officer. Ask what a real one would actually do in
  that room, and whether the text has them do it.

Write these under `## Pass two`, same format: line number, verbatim quote, one
sentence.

---

## Rules for the report

- Every entry has a verbatim quote from the chapter and a line number. Check the
  quote by looking at the file again before you write it down.
- One sentence per entry saying what is wrong. No paragraphs of analysis.
- If you are unsure whether something is a problem, include it and mark it
  *unsure*. A false positive costs a minute; a miss costs a chapter.
- **Do not report** prose style, sentence rhythm, repeated words or constructions,
  reading level, or whether the chapter is any good. Those are somebody else's
  job and reporting them here dilutes yours.
- Do not edit the chapter. Do not run git commands that write.

Write to `passes/sense/NN.md` and stop.
