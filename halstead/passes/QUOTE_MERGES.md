# Quote merge pass: closing the words-per-quotation floor without adding words

Follow-up to `DIALOGUE_MEASURES.md`, which closed most of the gap on this
measure by lengthening quotations and left a note that the remaining ~950
words needed would break the word-count house rule. This pass uses the
author's alternative instead: merge a speaker's own consecutive quotations,
split only by a tag or a short beat, into one quotation. No prose was added
anywhere; the only words removed are dialogue-tag words which were kept in
every case here, just moved to the end of the merged quotation, so the book's
word count did not change at all (129,806 words before and after). Chapters
`01_before.md` and `02_march_4th.md` were not touched (locked).

## The five numbers

| measure | before | after | target | result |
| --- | --- | --- | --- | --- |
| words per quotation, mean | 17.85 | 18.10 | 18.0 or higher | pass |
| 4 words or under | 25.0% (540/2162) | 23.5% (501/2132) | 20-25% | pass |
| 30 words or over | 19.4% (420/2162) | 19.7% (420/2132) | 18-26% | pass |
| variation (CV %) | 121 | 120 | 115-135 | pass |
| sentences with 2+ "and" | 9.94% | 9.94% (unchanged) | under 10% | pass |

`python3 grade.py` at the end: 58 of 58 measures passing (100%), up from
57 of 58. Book word count: 129,806 words before and after, exact
(`build_manuscript.py` confirms). No chapter's word count changed by even
one word, since every merge only repositioned an existing dialogue tag
rather than adding or deleting text; the book average therefore did not
move either.

## How the lever works

`measures/quote_length.py` extracts every `"..."` span and takes the mean of
its word count across all ~2,162 quotations in the book. Merging two of a
single speaker's quotations (split by a tag or beat) into one quotation
removes one quotation from the count while keeping the sum of all quoted
words exactly the same (the words don't move, the quote marks around them
do), so the mean rises automatically. Total quoted words were 38,593 both
before and after; the count of quotations dropped from 2,162 to 2,132 (30
merges), which is exactly what moves the mean from 17.85 to 18.10 with no
prose added.

The 4-words-or-under bucket was the tight constraint (24.98%, essentially
at the 25% ceiling already). Merges were chosen so that most of them
consumed at least one short (<=4 word) quotation into a longer combined
one, which pulls quotations *out* of the short bucket rather than leaving
it untouched while the total count shrinks (which would have pushed the
percentage up instead). No merge was selected where the combined quotation
would itself still land at 4 words or under, and none where a previously
mid-length pair (neither individually >=30 words) combined to newly cross
the 30-word line, except by leaving already-long quotations alone (several
selected pairs already had one half individually >=30 words, so the merge
made no difference to the long-bucket count, only to the denominator).

## The 30 merges

Format: chapter, before, after. Every "before" string was copied from the
file and verified against it before editing; every "after" was applied with
an exact-string replacement, never a line-index splice.

### 04_pluto.md

> "Tomorrow," Chloe says. "After dinner, when she's back at the hotel, so
> she isn't out somewhere when it rings."

->

> "Tomorrow. After dinner, when she's back at the hotel, so she isn't out
> somewhere when it rings," Chloe says.

### 06_the_list.md (three merges)

> "Obviously," Sam says. "A place spends a month teaching you all of that,
> it's got plans for the rest of it."

->

> "Obviously. A place spends a month teaching you all of that, it's got
> plans for the rest of it," Sam says.

> "And they did karate," her dad says, "and she cooked, an actual dish with
> onions in it, and the whole table ate it."

->

> "And they did karate, and she cooked, an actual dish with onions in it,
> and the whole table ate it," her dad says.

> "Okay," her mom says, "so what is that, what's the name for that."

->

> "Okay, so what is that, what's the name for that," her mom says.

### 07_the_same_room.md

> "I don't know," Chloe says. "I don't..." She tries to stop, but she
> can't.

->

> "I don't know, I don't..." Chloe says. She tries to stop, but she can't.

### 08_the_asking.md (three merges)

> "The whole time," her mom says. "Every night of it."

->

> "The whole time, every night of it," her mom says.

> "That's absolutely fine," Mrs. Prahl says. "Take your time."

->

> "That's absolutely fine, take your time," Mrs. Prahl says.

> "She really does," her mom says. "Look at her go."

->

> "She really does, look at her go," her mom says.

### 09_february.md (two merges)

> "It's true," her dad says, "it's a true thing and I'm not saying it a
> third time."

->

> "It's true, it's a true thing and I'm not saying it a third time," her
> dad says.

> "Yes," her mom says, "and when you get there you can tell whoever you
> like."

->

> "Yes, and when you get there you can tell whoever you like," her mom
> says.

### 11_eight.md (two merges)

> "The whole summer," her mother says, "and I already know I'm going to
> count every single day of it."

->

> "The whole summer, and I already know I'm going to count every single day
> of it," her mother says.

> "She has," her mother says. "She eats like somebody who intends to
> finish."

->

> "She has. She eats like somebody who intends to finish," her mother says.

### 13_ten_pages.md (two merges)

> "What?" Ruth says. "What are you talking about?"

->

> "What? What are you talking about?" Ruth says.

> "That's not it," Ruth says. "None of this was in the briefing."

->

> "That's not it. None of this was in the briefing," Ruth says.

### 14_sixty_degrees.md (two merges)

> "Ask her again," Kavi says. "Properly this time."

->

> "Ask her again, properly this time," Kavi says.

> "October," she says. "Well, you'll get there, dear, once in a whole year
> is hardly a lot, is it."

->

> "October. Well, you'll get there, dear, once in a whole year is hardly a
> lot, is it," she says.

(The genuine beat here, "Her grandmother pats her on the arm," sits before
both quotations and was left untouched; only the plain tag between the two
quotations was moved.)

### 15_twelve.md (three merges)

> "Noted," Sam says. "It's still the plan. Anybody got a better one in the
> next thirty seconds?"

->

> "Noted. It's still the plan. Anybody got a better one in the next thirty
> seconds?" Sam says.

> "Uh," she says. "Hi. Who are you?" She tilts her head like a lost puppy.

->

> "Uh, hi. Who are you?" she says. She tilts her head like a lost puppy.

> Ruth reads them off her arm, and Sinclair nods. "Grading's in the
> morning," he says. "Go to bed. Now."

->

> Ruth reads them off her arm, and Sinclair nods. "Grading's in the
> morning, go to bed. Now," he says.

### 16_thirteen.md

> "Four hours," Eli says. "That took me. Somebody at this table beat it."

->

> "Four hours. That took me. Somebody at this table beat it," Eli says.

### 17_fourteen.md (two merges)

> "It's true," she says. "Who told you?"

->

> "It's true. Who told you?" she says.

> "You remember," Chloe says. "You said it with a week attached."

->

> "You remember. You said it with a week attached," Chloe says.

### 18_fifteen.md

> "That's it?" Chloe says. "That's all you've got for me?"

->

> "That's it? That's all you've got for me?" Chloe says.

### 19_sixteen.md

> "Paper on Thursday," Chloe says. "Same as the last few."

->

> "Paper on Thursday, same as the last few," Chloe says.

### 20_the_parking_lot.md

> "We told you there were seven of them," Ruth says. "Not seventy."

->

> "We told you there were seven of them, not seventy," Ruth says.

### 21_the_applications.md

> "She's sixteen," the escort says. "And she's in class until four."

->

> "She's sixteen, and she's in class until four," the escort says.

### 22_the_offer.md

> "Eleven years," Mr. Amberg says. "Anything for the file."

->

> "Eleven years, anything for the file," Mr. Amberg says.

(This exact line also appears earlier in the chapter, spoken by Amberg to
Chloe, with an extra clause in the tag: `"Eleven years," he says, before
she's fully settled in the chair. "Anything for the file."` That instance
was left alone: "before she's fully settled in the chair" is a real beat,
showing Amberg starting before Nadia has sat down, and the sentence is
different enough from the merged one below that the exact-string edit only
ever matched the second, un-beated occurrence.)

### 23_the_first_one.md

> "Probably me," Chloe says. "I want the car for the fall anyway. I'd
> rather do the drive on my own."

->

> "Probably me. I want the car for the fall anyway. I'd rather do the drive
> on my own," Chloe says.

### 25_forty_targets.md

> "Mine posts me word searches clipped out of the local paper, a couple a
> week," Okoro says. "I've started doing them."

->

> "Mine posts me word searches clipped out of the local paper, a couple a
> week, I've started doing them," Okoro says.

### 30_cleared.md

> "Two others," Chloe says. "Same kind of project, same person asking, and
> I gave her the answer I have just given you. Both of them are older than
> the third and neither of them ran as long."

->

> "Two others, same kind of project, same person asking, and I gave her the
> answer I have just given you. Both of them are older than the third and
> neither of them ran as long," Chloe says.

## Merges found and refused

- **23_the_first_one.md**, the grandmother's receiving line: `"What are you
  doing next?" she asks. "The Army," he tells her, and she pats his arm.`
  This looked like a same-speaker split on first pass (a plain "she asks."
  sits between the two quotations), but it is not: the first quotation is
  the grandmother's question and the second, "The Army," is Sam's answer,
  attributed by the "he tells her" that follows it. Merging would have put
  two different people's words inside one pair of quotation marks, which
  the brief rules out explicitly. Left untouched.
- **22_the_offer.md**, the first "Eleven years" line (to Chloe rather than
  Nadia): the beat "before she's fully settled in the chair" is doing real
  work, showing Amberg starting the interview before she's even sat down,
  which is part of the chapter's characterization of him. Left in place;
  only the second, unbeated occurrence of the same line (to Nadia) was
  merged.
- **07_the_same_room.md**, "Twice." Chloe is already talking before the card
  is all the way turned, up on her toes at the desk... "I'd have gone for a
  third, only there wasn't any time left in the month," she says. The beat
  between "Twice." and the next quotation describes Chloe talking before
  the librarian has even finished turning the card, which is the specific
  thing being dramatized in that beat (her eagerness/interruption). Left
  alone.
- General note: a large number of "X says." plain-tag pairs were found
  across nearly every chapter (roughly 95 candidates with at least one side
  at or under 4 words, out of ~200 short-priority candidates and ~317 total
  quote-tag-quote patterns found). Only 30 were used, chosen to (a) spread
  across as many chapters as possible rather than concentrate in a few, (b)
  keep the 4-words-or-under bucket safely inside its 20-25% band rather than
  push it to the ceiling, and (c) avoid creating new 30+-word quotations
  where the two halves individually sat in the middle band. The remaining
  ~65 plain-tag candidates were left as future headroom rather than used,
  since 30 was already enough to clear the floor with margin.

## What was not touched

- No quotation was deleted or shortened to raise the mean; the brief for
  the 4-words-or-under bucket explicitly rules that out, and it was
  checked directly (see table above: the short bucket's raw count dropped
  from 540 to 501, its share from 25.0% to 23.5%, comfortably inside
  20-25%).
- No `, because` was added inside speech (`measures/tics.py`'s target for
  that stays at its already-passing count, unaffected since nothing was
  added).
- No banned phrase or avoid-list word was introduced; every merge only
  recombines text that already existed, so occurrence counts of "same,"
  "the whole/rest of it," and the rest of the avoid list are identical
  before and after.
- No chapter's word count changed, so the 2,000-5,000 band and the 3,600
  book-average ceiling were never at risk from this pass.
