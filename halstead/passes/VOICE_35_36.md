# Voice pass, chapters 35 and 36

Scope: `chapters/35_nine_minutes.md` and `chapters/36_seventy_five.md` only.
Dialogue and chat lines were not touched. The personified worm/watcher in
chapter 35, the deliberately unanswered lines in both chapters, and chapter
36's opening paragraph about unnamed benefactors were left exactly as
written, per brief. Checked against `passes/HOUSE_RULES.md` and
`passes/DO_NOT_FLAG.md` first.

Both chapters re-measured with `measures/style_report.py` before and after:
sentence count unchanged in both (121 in 35, 122 in 36), word count 2103 to
2102 in 35, 2003 to 2005 in 36 (chapter 36 did not shrink, per the floor
constraint in the brief).

## Changed

### 1. chapters/35_nine_minutes.md — fake agency (two inanimate subjects doing a person's physical task)

**Before:** "The laptop closes, the phone comes back up, and she types a question into the chat."

**After:** "Closing the laptop, she lifts the phone again and types a question into the chat."

**Why:** Textbook instance of the book's own fault: the laptop cannot close
itself and the phone cannot lift itself, and the very next scene in this
chapter ("Ruth's screen dims on its own... then she shuts the laptop for the
night") shows the author elsewhere giving Ruth the same action directly. The
fix moves both actions onto Ruth. Rewritten as a participial opener rather
than a plain "She + verb" sentence, because that sentence-opener count is
already sitting at its target of 120/100k per the brief and a straight "She
closes the laptop..." would have pushed a new instance onto a full measure.

### 2. chapters/36_seventy_five.md, line 147 — person in the subject of a passive

**Before:** "Sam offers to come out for a fortnight of his leave and is told the flights are absurd, but offers again the following day with a screenshot of a cheaper flight."

**After:** "Sam offers to come out for a fortnight of his leave, and Priya tells him the flights are absurd, but he offers again the following day with a screenshot of a cheaper flight."

**Why:** "Sam... is told" is exactly the banned pattern, and this is the
highest-priority fix category in the brief. The doer is unambiguous from
context — this is Priya's exchange with the group about her situation, and
she is the one turning down offers of help — so naming her invents nothing.
Word count moves from 31 to 33 words, which is fine since chapter 36 may not
get shorter.

### 3. chapters/36_seventy_five.md, line 7 — person in the subject of a passive

**Before:** "Sam is at a unit in a state he first set foot in the day he was posted to it, with a phone he can use in the evenings."

**After:** "Sam is at a unit in a state where his posting began the day he first set foot in it, with a phone he can use in the evenings."

**Why:** "he was posted" puts Sam in the subject of a passive. The text never
names which branch or office posted him, and inventing one ("the army posted
him") would have added a fact not on the page, so the fix moves the sentence
onto "his posting" as the acting subject instead of naming an institution —
active, not passive, with no new fact introduced. Word count unchanged (29
words both ways).

## Called out, not changed

### chapters/35_nine_minutes.md, line 11

**Current:** "Three logs come open instead of one: the process's own record, the host underneath it, and the outbound trace Kavi built to sit beneath both, each blind to the other's existence."

**Why the voice is wrong:** Same fault as the fixed example above: logs do
not open themselves, and this is the fake agency the pass is looking for.

**Why I did not change it:** The very next paragraph is "Eli pulls the logs.
No error, no restart, no gap." Making this sentence active with Eli as the
doer ("He opens three logs instead of one...") would put his name on the
action twice in two consecutive paragraphs for what may be a deliberate
split — this sentence reads as the general methodology (why three logs, not
one) and the next as the specific act of pulling them that night. I could not
tell whether that split is intentional pacing or an oversight, and a fix that
guesses wrong here creates a new problem (flat repetition) worse than the one
it solves.

**Replacement 1:** "He opens three logs instead of one: the process's own record, the host underneath it, and the outbound trace Kavi built to sit beneath both, each blind to the other's existence."

**Replacement 2:** "Three logs exist for exactly this, not one: the process's own record, the host underneath it, and the outbound trace Kavi built to sit beneath both, each blind to the other's existence."

**Replacement 3:** "He checks three logs instead of one, because a single log is a story somebody wrote and logs that agree read closer to a fact: the process's own record, the host underneath it, and the outbound trace Kavi built to sit beneath both, each blind to the other's existence."

## Summary

- Changed: 3 sentences, all in the same direction — fake-active/passive-with-a-person-in-it corrected toward a real, named, active doer (2 person-in-passive-subject fixes in chapter 36, 1 fake-agency fix in chapter 35). No sentence needed the opposite correction (active-that-should-be-passive) in either chapter; nearly everything else already keeps its object as topic correctly or is protected (the worm, the watcher, involuntary body reactions, timers, idiom, or the stillness beats named in the brief).
- Called out: 1.
- Strongest call-out: the "Three logs come open instead of one" sentence in chapter 35 (line 11) — it is a clean instance of the book's fake-agency fault, but the paragraph immediately after it already names Eli doing almost the same thing ("Eli pulls the logs"), and I was not confident enough about whether the split between general methodology and specific action is deliberate to risk flattening it into repetition.
