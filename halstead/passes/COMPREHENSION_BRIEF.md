# Comprehension review: the brief

**You are a reviewer. Do not edit any chapter. Do not rewrite anything.** Your
only output is one report file.

A reader who already knew the plot read the bar-exam chapter and got it wrong.
Another reader finished it believing the protagonist had passed the exam by four
points. She failed it by four. Several other chapters have the same problem
somewhere in them, and nobody has checked which.

## Do these in this order. The order is the method.

### 1. Read your chapter and nothing else

Do not open the synopsis, the character sheets, the chronology, or any other
chapter. Do not search the repository for context. If a name or an event is
unfamiliar, that is the data.

### 2. Write the blind summary, before you read anything else

In your report, under `## What I understood`, write what happened in this
chapter, in order, in plain language. Say who did what and what changed. Where
you are unsure, say so in the summary itself rather than smoothing it over.

Then, under `## Where I got lost`, list every place you had to re-read, guess, or
could not resolve. For each one: the quoted text, and what the two or more
possible readings are. **This is the most valuable part of the report.** A
confusion you felt and then worked out still counts, because most readers will
not work it out.

Then, under `## Ninth grader`, answer plainly: could a ninth-grade reader follow
this chapter? Where would they stop being able to?

### 3. Only now, read the reference material

`SYNOPSIS_CHARACTERS_TIMELINE.md` and `chronology/BOOK.md`.

Under `## Against the synopsis`, report every place your blind reading differed
from what actually happens. Be specific: what you thought happened, what the
synopsis says, and which sentence in the chapter sent you the wrong way.

## The worked example

Chapter 19 puts the failure in three overlapping pieces:

- Eleven lines earlier, "I gave it four" means four pages of writing.
- The results board has "a column showing the distance from the pass line",
  which does not say which side of the line.
- "Four points," she says. Then Kavi says "I got it by nine", which reads
  naturally as a bigger pass.

Nothing in the passage states that she failed. That is the shape you are looking
for: not bad prose, but a passage where a reasonable reader assembles the wrong
event and is never corrected.

Other shapes worth flagging:

- A pronoun whose owner is genuinely unclear.
- A time jump the text does not signal.
- A number or unit that could be two things.
- A speaker you cannot identify in an exchange.
- A scene where you cannot tell where the characters are.
- A paragraph you could not paraphrase after two readings.

## Write to your report file and stop

One file, at `passes/comprehension/NN.md`, with the four sections above. Do not
touch the chapter. Do not run git commands that write. Do not suggest rewrites;
finding the problem is the whole job.
