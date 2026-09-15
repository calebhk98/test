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

**The numbers — read this twice, because the first pass got it wrong.**

Every number word from *one* to *fifteen* sits above the highest-numbered book
in the corpus. The book runs about 2,800 number words per 100,000 against a
corpus maximum of 1,520. This is not a problem with three unlucky numbers. It is
a habit of precision applied to everything.

The author's ruling, in his words:

> *"None of the numbers are [a motif]. ANY that are over, needs to be fixed.
> Changing from 1 number to a different one, just hides the issue in other
> numbers. We don't need precision to such a degree that readers are bothered
> by it."*

So:

- **Do not substitute one number for another.** The first pass did this
  extensively and it moved the problem rather than solving it: eleven became
  thirteen, nine became ten, four hundred became three hundred. Every one of
  those cuts one row of the table and raises another.
- **Delete the precision instead.** *He was gone six minutes* becomes *he was
  gone a few minutes*. *Four of them stood by the door* becomes *a group of them
  stood by the door*. *She reads it three times* becomes *she reads it again*,
  or *she keeps reading it*. Most counted things in this book do not need to be
  counted for the sentence to work.
- **Keep the precision where being exact is the point.** A scored drill, a
  timed exercise, a figure a character is arguing about, a number that recurs
  because somebody is tracking it. Chloe counting is characterisation. The
  narrator counting everything is the habit.
- **A number is not saved by being load-bearing in one place if it also appears
  six times incidentally.** Protect the instance that matters and delete the
  rest.

The target for each number is the corpus maximum: no more numerous than the most
number-heavy of twenty-three published novels. That is still a great deal of
counting.

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
