# Getting to Flesch-Kincaid 9

## Where the book actually is

After the whole-book dialogue pass the book reads 6.44. The target is 9.0.

The gap is not spread across the book. It is one half of it.

| | words | w/sentence | mean F-K |
|---|---|---|---|
| chapters 1-22 (childhood) | 74,598 | 15.8 | **5.7** |
| chapters 23-35 (adult) | 28,350 | 21.2 | **9.2** |
| whole book | 102,948 | 16.9 | 6.44 |

**Chapters 23-35 are already at target and need nothing.** Chapters 1-22 hold
72% of the words and average 5.7. Every point of the remaining gap lives there.

## The arithmetic

`F-K = 0.39 x (words/sentence) + 11.8 x (syllables/word) - 15.59`

The book runs 1.307 syllables per word. Holding that fixed:

    F-K 9.0 requires 23.5 words per sentence.

Chapters 1-22 are at 15.8. That is a 49% increase in sentence length, in the
half of the book narrated closest to a child.

The other lever is vocabulary. Every +0.01 syllables/word is worth +0.118 F-K.
Trading between the two:

| route | w/sentence | syl/word | who writes like this |
|---|---|---|---|
| length only | 23.5 | 1.307 | longer sentences than any book in the corpus |
| balanced | 22.0 | 1.357 | Black Beauty's sentences, Little Women's words |
| vocabulary-led | 20.1 | 1.442 | Wharton |

## What F-K 9 is, in the corpus

Of 23 books measured, exactly one clears 9.

    Age of Innocence (Wharton)   9.3    20.1 w/sent   1.442 syl/word   18.2% 7+ char
    Black Beauty                 8.0    22.9 w/sent   1.245 syl/word    8.9%
    Little Women                 8.0    19.8 w/sent   1.345 syl/word   13.3%
    Wind in the Willows          7.7    18.8 w/sent   1.351 syl/word   14.1%
    Treasure Island              6.7    18.3 w/sent   1.285 syl/word   11.5%
    Peter Pan                    5.7    14.6 w/sent   1.323 syl/word   12.7%
    HALSTEAD (now)               6.4    16.9 w/sent   1.307 syl/word   12.3%

Black Beauty reaches 8.0 on sentence length alone, with a *smaller* vocabulary
than this book. Wharton reaches 9.3 by doing both at once. Nothing in the corpus
reaches 9 on one lever.

So F-K 9 across chapters 1-22 means those chapters end up with longer sentences
than Black Beauty and a wider vocabulary than Little Women, in the childhood
half. That is the actual size of the ask. It is reachable. It is not a polish.

## The two techniques that carry it

Both come out of `passes/WHY_HIGHER.md`, read off the corpus chapters that
score highest, and both raise words-per-sentence without inflating the prose.

**1. Cataloguing.** Where the draft names a category, name the members instead,
in series, inside one sentence. Three items joined with commas is one long
sentence where the draft had one short one and an unstated list.

**2. Spelling out the logical joint.** The draft repeatedly puts two clauses
next to each other and lets the reader supply "because", "so that", "which
meant", "even though". Writing the joint in is what separates 15-word sentences
from 24-word ones, and it is the single biggest difference between the top and
bottom corpus chapters.

**What does not work, and has already been tried:** splicing short sentences
with commas. Same words, fewer sentences, and it reads spliced. The dialogue
pass caught one instance of the reverse (a period added inside a 35-word line
dropped chapter 23's mean with no other change) which is the same effect
running backwards.

## Word length

7+ character words: 12.3% now, corpus median 13.2%, Wharton 18.2%.

The place to find them is the narration, not the dialogue, and specifically the
narration of things that have real names. A child narrator does not need a
larger vocabulary for the reader to get one: the objects, procedures and
subjects around her already have precise names, and the draft mostly reaches
for the general word.

## Ceiling per chapter

Do not push a chapter past 3,400 words to get there. Longer sentences carrying
the same content is the goal; more content is not.
