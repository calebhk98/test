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

### The camera is not talking to the reader

The rule bars explaining people and events. It does not bar description. The
narration may tell the reader anything a camera in the room could record, or
anything Chloe can see from where she is standing: the floor is green, the
walls are purple, the room is bright, the pipe rings when a thrown apple hits
it. That is addressed to the reader and it is allowed, because it reports a
surface rather than a meaning.

**The camera stops at the surface.** The moment a clause says what the surface
causes, means, or costs, it has stopped being a camera and started being the
narrator. From the author, ruling on an example this document previously got
wrong:

> *the radiator is under the window at the far end* is a camera, and allowed.
> *so whoever gets there early sits down that end* is talking to the reader,
> and would fail.

### The trailing explanatory clause

This is the commonest way the rule gets broken, and it survives every pass
because the first half of the sentence is legitimate. A camera observation is
made, and then a tail is bolted on telling the reader what to take from it.

Every one of these was in this manuscript and every one of them failed.
All six have since been repaired, checked against the chapters on
2026-08-29. They are kept here as the shape to recognise, not as work
outstanding: do not go looking for them in the text, and do not treat a
sentence as broken because it resembles one. The **bold** part is what
had to come out in each case.

- a rail at chair height **so the chairs cannot reach the plaster**
- a light that throws everything back off the glass, **so the bottom of a
  sheet has to be read at an angle**
- the brick is a shade darker either side of it **from the run of the rain**
- the language-block stairs, **which cost her a minute each way**
- **the only** part of the building that smells of nothing at all
- **the coldest table in the hall from November on and the table everybody
  wants in June**

The tell is a comma followed by *so*, *which*, *because*, *from*, or a
superlative doing comparison work the reader did not ask for. Cut at the
comma. If the consequence matters, show somebody living it: a person sitting
down at the warm end, a girl tilting a sheet to read the bottom of it.

`measures/style_report.py` counts these. It reports 74 trailing explanatory clauses,
37 narrator evaluations and 18 superlatives book-wide. Run it.

### An overused technique is cut back, not to zero

Every finding in this repository is a rate, not a prohibition. A device that
would be good seven times in a book and appears forty times needs to come down
to about seven. It does not need to reach nothing, and driving it to nothing
is its own defect. The same holds in reverse: a technique the book never uses,
which a reviewer says it should, gets added in a few places, not everywhere it
would fit.

### Named states, and why the rule says never

A declared emotional state is allowed if a camera could see it, and it is
allowed perhaps five times in thirty-six chapters, deliberately, in scenes
built to carry it. That is roughly one chapter in seven, and every use has to
be a decision.

The rule is written as a flat ban anyway, because a permission at that rate is
not a permission an editing pass can hold. Anyone told the technique is
available will reach for it on the first difficult paragraph and the budget is
gone by chapter four. Treat it as banned. Spending one is the author's call,
not a pass's.

### The tone construction, and how to fix it

The commonest form this takes in the manuscript is the narrator naming a tone
by explaining the mental state behind it: *"the tone that she uses when she
already knows the answer and has to hear it again anyway."* The author flags
this one as recurring book-wide.

It does the reader's work twice: it identifies the tone and then tells you what
it means. The character genuinely does read tone, so the perception has to
stay. The rule that works:

> **Give the sound, then give what the listener does about it. Never give the
> state.** Tone is a fact about the air. Meaning is a fact about the listener.
> The mental state belongs to nobody in the room.

Worked example, chapter 7. Before, the narrator explained the mother's state.
After:

> Coming down for water, Chloe gets the end of one of the calls, and the
> sentence she arrives on has two pleases in it. Her mom is at the counter with
> one hand flat on it, and Chloe stops in the doorway with the glass still
> empty.

Two pleases is the sound. Stopping in the doorway with an empty glass is what
the listener does about it. Neither sentence names a feeling.

**The test: strike the clause and read the page.** If nothing is lost, it was
talking to the reader. In the chapter 7 case nothing was lost, because the
mother says the thing out loud four lines later. That is the general pattern:
this construction tends to sit directly above the beat that would have proved
it, so the usual fix is deletion rather than replacement.

## 2. One paragraph convention

Blank line between paragraphs. No two-trailing-space markdown hard breaks
anywhere in the book. Chapters 1-6 used the old convention and are being
converted; `measures/check_edits.py` reports any trailing-space line as a defect.

## 3. No em dashes, no curly quotes

Straight quotes throughout. Em dashes are banned in narration and dialogue
alike; use a comma, a colon, a semicolon, or a second sentence.

## 4. Word count

2,000 to 5,000 per chapter. The ceiling is deliberately loose and one long
chapter costs the book nothing, so it is not what is judged.

**The book average is what is judged.** It has to land between 2,600 and 3,600,
which is what keeps the book near the 300 printed pages the author wants. He
will accept fifty pages either way and will not accept six hundred. What the
band refuses is not one long chapter, it is every chapter drifting up.

The ceiling is not a target: do not expand a chapter toward it, and never pad a
short chapter to reach the floor. A chapter that comes in under 2,000 because a
pass cut explanation out of it is a better chapter than one inflated back over
the line. Say so and leave it short.

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

## 7. Subagents run on Sonnet

Every subagent spawned for work on this manuscript uses `model: "sonnet"`.

The author's reason, in his words: *I can tell when Opus writes it, as Opus
writes too eloquently and literary. I'm having to go back through to pull it
back towards normal human readers. The target audience is 9th graders, and the
text keeps being written for college students.*

This applies to prose passes above all, and to analysis passes as well, since
an analysis agent writes example rewrites that get pasted into chapters. There
is no exception for a hard chapter or an important scene. A pass that comes
back reading like an essay has failed whatever else it hit.

## 8. The passive is not the fault. Losing a person who is standing there is.

Seventeen agents were handed a flat ban on putting a person in the subject of
a passive. Two of them obeyed it and broke a correct sentence: *"the way he
has been taught since he was small"* became *"the way he learned it since he
was small"*, which is not English, and *"a state he first set foot in the day
he was posted to it"* became a circle. Who taught Sam, and who posted him,
are unknown and beside the point. That is the case where English wants the
passive.

The ban was a proxy. The real rule, which is a hundred years old and which
nobody on this project looked up until the author went and asked somebody,
has three parts. A passive is the right choice when any of them holds:

1. **Topic continuity.** The thing the paragraph is about stays in the
   subject slot instead of jumping around. Old information before new.
2. **The agent is unknown, irrelevant, or obvious.** Nobody needs telling
   that the Army posts soldiers or that a school pairs students.
3. **The receiver is what the sentence is about.** *"Polish is added to the
   autumn schedule"* is about the schedule, not about whichever office
   clicked the button.

So the test on any suspect sentence is: **is the missing doer a specific
person who is already in this scene, and does the sentence lose something
the reader needs by leaving them out?** If yes, put them back. If no, leave
the passive alone, and leave it alone whether the subject is a person or a
thing.

Two sentences sitting in the manuscript right now that the old rule would
have flagged and the real rule correctly leaves alone: *"The boy she is
paired with says, 'Lucky'"* in chapter 13, and *"in the order he is required
to take them"* in chapter 26. Both have a person in the subject of a passive.
Both are right.

The person/object split correlated with the truth in this book only because
it is a book about named people and institutions doing things to a child. It
is not a rule of English and it will misfire in both directions. The full
working, with sources, is in `passes/PROSE_PRINCIPLES_STRUCTURE.md`.
