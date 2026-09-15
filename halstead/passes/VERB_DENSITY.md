# How many verbs a sentence carries, against the corpus

The author asked after fixing this sentence:

> "They carry the bracket rule into the summer, applying it to a stairwell, a
> laundry chute, and one of the goals on the field."

which is better than either version before it, and made him wonder how many
sentences in the book are carrying more than one verb.

Measured with a parser rather than a regex, because "how many verbs" is not a
thing a regex can answer. `passes/verb_density.py` uses spaCy's small English
model and counts a verb as a VERB or AUX token that is not an auxiliary hanging
off another verb, so "has been taught" counts once, not three times. 23
reference books, 90,000 characters sampled from the middle of each, 6,816
sentences from this book.

| measure | book | corpus median | corpus min | corpus max | ratio |
| --- | --- | --- | --- | --- | --- |
| words per sentence | 19.41 | 16.09 | 8.99 | 24.62 | 1.21x |
| verbs per sentence | 3.14 | 2.82 | 1.79 | 4.15 | 1.12x |
| verbs per 100 words | 16.20 | 17.41 | 15.29 | 20.51 | **0.93x** |
| sentences with 1 verb | 23.1% | 25.3% | 12.3% | 46.7% | 0.91x |
| sentences with 2 or more | 73.8% | 72.6% | 49.7% | 86.7% | 1.02x |
| sentences with 3 or more | 52.3% | 46.6% | 18.0% | 68.6% | 1.12x |
| sentences with 5 or more | 22.5% | 14.3% | 2.7% | 36.7% | 1.57x |
| coordinated verbs per sentence | 0.54 | 0.41 | 0.20 | 0.87 | 1.32x |
| sentences with a coordinated verb | 39.7% | 30.1% | 15.3% | 56.4% | 1.32x |

## What it says

**Multi-verb sentences are not the problem.** 73.8% of this book's sentences
carry two or more verbs against a corpus median of 72.6%. That is parity.

The book's sentences are 21% longer than the median book, and the verbs go up
with the length, but slightly slower: **verbs per 100 words is below the corpus
median, and below every other measure's direction.** So the extra length is not
extra action. It is nouns, modifiers, and appositives hung off the same number
of things happening. That is the shape the register pass keeps finding.

Two numbers do stand out, and both point at the same habit:

- **22.5% of sentences carry five or more verbs**, against a median of 14.3%.
  Three reference books are higher (Little Women at 36.7%, Black Beauty, Wind
  in the Willows), so this is inside the range, but it is the top quarter of
  it.
- **39.7% of sentences have two verbs joined by "and" or a comma**, against a
  median of 30.1%. That is the bracket-rule shape exactly: one subject, two
  things it does, strung together.

## Why this is not going in the scorecard

Every figure above sits inside the corpus range, most of them near the middle
of it. A measure that says the book is ordinary cannot drive a pass, which is
the same reason `measures/quotable.py` was written and left unwired. This is a
diagnostic to rerun when a pass is suspected of stringing clauses together, not
a target to hit. It also takes about four minutes and needs spaCy, which is not
worth putting in front of every `grade.py` run.

Rerun it with `python3 passes/verb_density.py` from `halstead/`.
