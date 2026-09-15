# Reading all 111 changes back

The author found two bad changes in the ones he happened to read, which is a
worrying hit rate, so every sentence the voice pass touched got read back
against what it replaced. `scratchpad/sentpairs.txt` was built by diffing the
chapters against the pinned baseline sentence by sentence rather than
paragraph by paragraph, which is the only way to see what actually changed
inside a long paragraph.

111 changed sentence groups. Eleven were wrong. Here they are, in the four
kinds they fall into.

## 1. The fix threw away the thing the sentence pointed at

The author's own two.

**chapters/12_nine.md** — "the lip has beaten everyone who's tried it" became
"nobody has gotten over it", and then "nobody has made it over". Over what?
The lip was still in the sentence before, but the pronoun that reached back to
it was gone. Now: "nobody has made it over the lip."

**chapters/11_eight.md** — "The bracket rule survives into the summer and
reaches a stairwell" became "They carry the bracket rule into the summer, into
a stairwell". A rule cannot be carried into a stairwell, but the sentence it
replaced could not be carried there either: the original was already confused,
and the pass made it grammatical without ever asking what it meant. What it
means is that people keep using the rule on new targets, so: "They apply the
bracket rule all summer, to a stairwell, a laundry chute, and one of the goals
on the field."

**chapters/23_the_first_one.md** — "Chloe gives her father the version of it
that reaches him first" says the same thing twice and lands on neither. The
point is that he is the first person she tells. Now: "Chloe tells her father
first."

## 2. The fix was right and its side effect was not

**chapters/06_the_list.md** — "drawing the rectangles the way Mr. Baptiste drew
them, running all the way through to why you turn the second fraction over"
leaves "running" attached to Baptiste, who is the nearest subject and is not
the one doing it. An "and" puts it back on Chloe.

**chapters/23_the_first_one.md** — "Her grandmother catches Chloe on her way
past ... 'And what are you doing next?' she asks." Two women in the sentence
and "she" is the book's default word for Chloe. The explicit tag goes back in.

**chapters/24_the_chat.md** — "The list holds him long enough that..." became
"The manager stays on the list", which reads as though he were an item on it.
He is reading it: "The manager reads the list long enough that..."

## 3. The fix was made to dodge a measure

**chapters/28_nineteen.md** — two sentences were written as fronted objects
("Both countries' newspapers she opens in adjacent tabs", "A short summary she
puts at the top") specifically to avoid adding to the She/He opener count. That
construction is more literary than anything else on the page, in the chapter
that just had its formality pulled down. One is a plain stative now, the other
uses her name.

**chapters/11_eight.md** — "A novel about a lighthouse takes her a week"
became "She spends a week on a novel about a lighthouse", which is a worse
sentence and one more opener against a measure already at its ceiling. The
original is back.

## 4. The rule was applied to a passive that was already correct

These are the ones that matter for the rules themselves, because both were
textbook-correct passives and the pass broke them anyway.

**chapters/26_the_exercise.md** — "the way he has been taught since he was
small" is a person in the subject of a passive, so the pass changed it to "the
way he learned it since he was small", which is not English. Who taught him is
unknown and does not matter; that is exactly the case where the passive is the
right call. Reverted.

**chapters/36_seventy_five.md** — "a state he first set foot in the day he was
posted to it" became "a state where his posting began the day he first set foot
in it", which turns a clear sentence into a circle. The Army posted him. Nobody
needs telling. Reverted.

## What this says about the rule we gave the agents

Person-subject passive was given to seventeen agents as a flat ban, and two of
them broke a correct sentence obeying it. The ban is not the rule; it is a
proxy for the rule, and it is wrong wherever the doer is unknown, obvious, or
beside the point. Two agents are out looking up what the actual rule is.
