# Iyad, confirmed: the napkin fix and one piece of inside evidence

Files read in full: `passes/HOUSE_RULES.md`, `passes/DO_NOT_FLAG.md`,
`characters/IYAD.md`, `THEY_ARE_CHILDREN.md`, `passes/IYAD_DELIBERATE.md`.
File edited: `chapters/16_thirteen.md`. `chapters/17_fourteen.md`,
`chapters/18_fifteen.md`, and `chapters/24_the_chat.md` were read in full
and left untouched: 17 is at its word ceiling and the Aurel material in 18
and 24 is the work the reader already credited and was told not to touch or
add to; the loan-figures read-out in 18 was left exactly as flat as it was
told to stay. No proposal was written to `IYAD_PROPOSED_12_13.md`; nothing
about the chapter 12 or 13 beats bore on either problem in this brief.

## Change — chapter 16, the cipher napkin retelling

**Old:**

> Iyad tells it at breakfast two days later, to a boy who was not at the
> table that night: how the table sat on that napkin for most of an hour
> while Chloe held the answer back until Nadia took the corner off her. The
> boy asks whether she was right, in the end. "She generally is," Iyad says,
> and starts on somebody else's week.

**Reason:** the reader called this line fond, correctly. "She generally is"
answers "was she right", and being told a clever friend is usually right is
a compliment with no second meaning available to a reader who takes it at
face value. The retelling around it (the wait, the corner Nadia had to take
off her) was meant to carry the sting, but nothing in the payoff line
converts that setup into anything other than praise. A line that compliments
her accuracy cannot double as the thing that damages her, no matter what
precedes it.

**New:**

> Iyad tells it at breakfast two days later, to a boy who was not at the
> table that night: how the table sat on that napkin for most of an hour
> while Chloe held the answer back until Nadia took the corner off her. The
> boy asks whether she does that a lot. "She generally does," Iyad says, and
> starts on somebody else's week.
>
> When Nadia catches part of it from a few tables over and asks him whether
> it really went an hour, he says it was probably closer to twenty minutes
> and starts on somebody else's week.

**Why this cannot be read as fondness:** the boy's question changed from
asking about a fact (was she right) to asking about a habit (does she do
that a lot), and Iyad's answer confirms the habit rather than the fact. "She
generally does" turns one evening at one table into a standing character
trait, told to somebody with no way to check either the single evening or
the generalization built on top of it: that she is someone who makes a table
wait on her. That is not a compliment on its face the way "she is generally
right" is; it is a label, applied in front of a stranger to her reputation,
built from a scene the boy never saw. There is no reading of "she does that
a lot" that lands as warm.

## The second paragraph, and why it is there

The brief's second problem is separate from the first: the reader's read of
Iyad rests on repetition and timing, not on anything he does that only makes
sense if he already knew what his own material was doing. The added
paragraph is that moment, placed here because chapter 16 was already open
and because the Aurel material elsewhere was ruled off limits for exactly
this kind of addition.

Iyad tells two different people two different sizes of the same hour. To the
boy who was not there, an hour, no hedge, offered as the more strikingly
unfair version. To Nadia, who was there and would know if the number were
wrong, the same hour becomes "probably closer to twenty minutes" the moment
she asks. Nothing in the text says why the number shrinks between the two
listeners. But a boy simply repeating an impression he holds would report
the same length to both, and a boy genuinely unsure of the length would
hedge for both listeners rather than only the one who was in the room. The
size of the claim tracks, exactly, whether the person asking could catch him
in it. That tracking is not visible unless he already knows which version is
the inflated one and which listener can tell the difference, which is
knowledge from the inside shown entirely from the outside: two answers, two
audiences, no line of narration connecting them.

## Verification

`python3 measures/style_report.py chapters/16_thirteen.md` was run after the
edit: the tic scan on the chapter's narration returns none found, and no new
section break, conjunction spike, or sentence-length anomaly appears at the
edited lines specifically (the chapter's existing whole-book baseline
numbers are unchanged in kind, since only two sentences were touched and one
short paragraph added). `python3 measures/check_edits.py --chapters 16`
reports 0 hard breaks, 0 em dashes, 0 curly quotes, and 0 problems, with the
word count at 4110 (+34 from 4076 pre-edit), inside the 2,000-5,000 band.
`grep` for every word and phrase on the banned list (instead, both hands,
leaves it, puts it back down, rather than, hands flat, turning it over, for
the first time, never once, in order, ", because") found only pre-existing
instances elsewhere in the chapter; none appear in the new text. The word
"always" was deliberately avoided in the boy's question ("does that a lot"
rather than "always does that") to keep from adding to the book's absolutes
count. No instance of "same" or "the whole/rest of it" was added; "starts on
somebody else's week" is repeated verbatim from the existing sentence rather
than restated with "same," which was avoided on purpose given that word's
ceiling. `grade.py` was not run, per instruction. `HALSTEAD.md` was not
touched. Chapters 17, 18, and 24 are byte-for-byte unchanged.

## Honest estimate

A cold reader would still be inferring some of this from pattern rather than
being told it outright, because house rule 1 and Chloe's viewpoint both
forbid anything closer than that. What has changed is the grade of pattern
being inferred from. Before this pass, the available pattern was repetition
and timing across multiple chapters and years: a boy who keeps choosing
targets he cannot check and keeps arriving at the worst item without
slowing down. That is compatible with a very good nose and no filter. After
this pass, chapter 16 alone contains two answers to two people about the
same event, sized differently, in the same scene, with the size tracking
exactly who could contradict him. A reader does not need chapters 17 or 18
to notice that; it is sitting in one paragraph. I would call that closer to
demonstration than inference, though it stops short of proof only because
the text still declines to say the word "lie" or show him privately
satisfied: it shows two numbers and lets the reader do the arithmetic. I
expect a careful reader to still describe their conclusion as an inference,
in the sense that no sentence in the book states his intent, but I would
expect the confidence behind that inference to be markedly higher than
"repetition and timing," and I would be surprised if this specific paragraph
were read as affectionate.
