# The repetition pass

Outside readers reported a set of habits by feel. `tics.py` counts them against
the same 23-book corpus the other measures use. Sixteen of seventeen sit above
**every** reference book, several by more than an order of magnitude.

## The target is a reasonable rate, not the corpus

The author's instruction, in his words:

> *"we don't have to get down to the corpus, which is also a very limited amount
> of text. I would say that we should try to cut ours to a reasonable amount.
> Like, hands flat we could possibly get to like 10/100k words, 1/3rd our rate,
> but still like 10x the corpus max."*

So the targets in `tics.py` are roughly a third of the current rate. Most of
them still leave the book far above every reference book afterwards, and that is
correct: a voice is made of repetition, and twenty-three books is a small
sample. **Do not chase the corpus. Hit the target and stop.**

Run `python3 tics.py` for the table and `python3 tics.py --show "hand(s) flat"`
to print every instance with context.

## What each cut actually means

**The gestures** — hands flat, turning an object over, eyes on/eyes down.
Do not delete the beat; give it to a different part of the body. The book lives
almost entirely in hands and eyes. What is happening in the feet, the breathing,
the jaw, the stomach, the shoulders, the back of the neck? A character who has
gone still is not the same as one who has started moving.

Where two characters share a gesture, one of them loses it. A gesture that
belongs to everybody belongs to nobody.

**The numbers** — four, nine, eleven, forty. The problem is not precision, it is
that the *same three numbers* recur in every context and from every mouth.
Chloe counting is characterisation; a librarian, a drill sergeant and the
narrator all dealing in elevens is an authorial fingerprint.

Two moves. Replace some with other numbers. Delete others entirely: *he was gone
six minutes* is usually better as *he was gone a few minutes*, and the precision
is then available where it means something.

**These numbers are load-bearing and must not change:**
ninety-one in the cohort; eleven years at the school; the nine minutes of
chapter 35; the forty targets of chapter 25 and Sam's forty percent; the
twenty-two seconds in the parking lot; the seventy-five in chapter 36; the
nineteen-year-old file; the hundred and thirty-five thousand dollar offer; the
sixty-fourth of ninety-one. When in doubt about whether a figure is doing work,
leave it and cut a different one.

**"About N"** — approximation bolted to specificity. Usually the fix is to drop
one half or the other.

**"The whole of it" / "the rest of it"** — a rhetorical closer. If the sentence
before it worked, this is redundant; if it did not, this will not save it.

**"That's not X, that's Y"** — keep it where the correction is the actual point.
Elsewhere state the positive claim and let the negation be implied. Note that
several characters have this recorded on their sheets as a signature; it can
stay for at most one of them.

**"The way you would"** — the author's best construction, which is exactly why
it is in the manuscript sixty-odd times. Keep the ones doing characterisation.
Cut the ones doing texture.

**Announced withholding** — *keeps it to himself*. An announced silence is not
subtext; it is text describing the place where subtext would be. Cut and let the
reader notice.

**"Same"** — usually deletable with no replacement.

**"Flat"** — doing four different jobs. Hands flat, a flat voice, a flat crack,
flat grey. Vary the ones that are description; keep the ones that are the word
for the thing.

**Sentences opening "She/He + verb"** — vary the opening, not the sentence. Start
with the object, a prepositional phrase, a participle, the setting, or dialogue.

## What does not change

- No em dashes, no curly quotes, one blank line between paragraphs.
- House Rule 1 still governs: nothing you write may explain a beat to the reader.
- Reading-grade bands, word ceilings and the 5% negative-space cap all still
  apply. Check before and after; a cut that breaks one of those is not done.
- **Two scenes are protected and must not be touched at all**: the intrusion
  incident in chapter 15 and the fight plus Chloe's speech in chapter 20.
- Do not lower a chapter's reading grade to make a cut. If a substitution costs
  grade, find a different substitution.
