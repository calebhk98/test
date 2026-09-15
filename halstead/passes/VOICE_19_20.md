# Voice pass: chapters 19-20

Span: `chapters/19_sixteen.md`, `chapters/20_the_parking_lot.md`. Read first,
in full: `passes/HOUSE_RULES.md`, `passes/DO_NOT_FLAG.md`, root `CLAUDE.md`.
Also checked `passes/AGENCY_15_26.md` and `passes/AGENCY2_15_26.md` (a prior
fake-agency regex pass over this same span, three items already fixed there
and confirmed still in place: "the list is posted" at 19:25, "takes the car
through it" at 19:109, "She takes the tongs home" at 19:141) and
`passes/passive/CH19-24_FIXES.md` (a separate, unrelated pass on character
*plot* passivity, not grammatical voice — its edits are already in the text
and were left alone here).

Method: read every narration sentence in both chapters against the four
rules in the brief. Dialogue and chat lines were read but never touched, per
the brief's own rule. Chapter 20's fight (roughly the men appearing through
the argument about the waitress, lines 77-163) was read in full and treated
as protected per this brief's instruction; nothing in it needed a change
regardless, including two textbook cases of the book's own fake-agency
pattern ("the gun that was waving is waving," "the second gun comes half out
of a jacket") that would be flagged anywhere else in the book. Left as
found, deliberately, per instruction. Chapter 19's bar-exam board and marks
were read as institutional and their passives left alone on that basis; the
Amberg "second line" refrain was read and not touched.

Verified with `python3 measures/style_report.py chapters/NN_name.md` on both
files, before and after. Word counts unchanged: 19_sixteen.md 4,172 words,
20_the_parking_lot.md 3,381 words. Both edits below are word-count neutral
(swap of equal word count) and neither changed a conjunction, quote, or
section-break count. No new tic-scan hits in either file.

## Changed (2)

### 1. Chapter 19, the negotiation board (fake agency)

**File:** chapters/19_sixteen.md

**Before:**
> Her father nods at that and asks about Kavi, so she tells him about Kavi, and then about Priya, and then about the negotiation board in the hallway, where every pairing in adversarial negotiation goes up the week it happens and stays up all year, nothing changing hands but the score.

**After:**
> Her father nods at that and asks about Kavi, so she tells him about Kavi, and then about Priya, and then about the negotiation board in the hallway, where every pairing in adversarial negotiation is posted the week it happens and stays up all year, nothing changing hands but the score.

**Why:** "every pairing... goes up" is an inanimate subject with an active
verb and nobody behind it — the book's own named fault, the same shape as
"the sheet goes up on the wall" in the brief and the same shape as "the list
goes up on the corkboard" that an earlier pass already fixed at 19:25 (now
"the list is posted"). The prior fake-agency pass's regex did not catch this
one because it looks for "the/a + noun + verb," not "every + noun phrase +
verb," so it survived that pass. Fixed to a passive that implies the same
doer as the exam-board sentence 156 words earlier in the same chapter — a
faceless institutional process (the school posting a result), which is
exactly the case the brief lists first for passive being correct. Word-count
neutral ("goes up" / "is posted," both two words).

### 2. Chapter 20, Sam's waffle ritual (person in subject of passive)

**File:** chapters/20_the_parking_lot.md

**Before:**
> They order too much and then Sam orders more, a full stack for himself and half of Nadia's once she stops eating a third of the way through it, and he works his way around the crisp top edge of his own stack before he touches the syrup at all, a ritual he performs on every waffle he has ever been handed.

**After:**
> They order too much and then Sam orders more, a full stack for himself and half of Nadia's once she stops eating a third of the way through it, and he works his way around the crisp top edge of his own stack before he touches the syrup at all, a ritual he performs on every waffle anyone has ever handed him.

**Why:** "he has ever been handed" puts Sam, a named character, in the
subject of a passive — the highest-priority fix in the brief regardless of
how minor the sentence. The doer is generic and lifelong (whoever has ever
handed him a waffle, which is not one person and not worth inventing), so
the fix is the generic-subject active the brief itself models ("mistakes
were made" becomes active with a doer, even a vague one) rather than a
name. "anyone has ever handed him" keeps Sam as the person he is throughout
the rest of the sentence and removes him from the passive slot. Word-count
neutral (five words either way).

## Called out, not changed (1)

### chapters/20_the_parking_lot.md, line 27

**Current:** "The coffee cup goes a quarter turn on the table under her hand, and then another."

**Why the voice is wrong:** Inanimate subject, active verb, and the actor
is not named as the sentence's grammatical subject — the cup does not turn
itself. This is the same shape as the brief's own examples ("the sheet goes
up on the wall," "the name of it goes across the table").

**Why I did not change it:** The hand that is doing it is already in the
sentence ("under her hand"), which is not true of the brief's examples,
where the actor is missing entirely rather than just ungrammaticalized —
so this reads less like the book's fault than like a deliberate camera
choice: staying on the object while Ruth works up to the news about her
brother, rather than naming her as the one fidgeting. Ten lines later the
same gesture is given the ordinary active treatment once she has already
said the news out loud ("Ruth turns the cup again, a quarter turn at a
time, always clockwise," line 37), which reads as the pair being a matched
before/after rather than one correct sentence and one mistake — the
suppressed-agent version while she is holding something back, the named
one once she has said it. I was not confident enough that this is the
defect and not the technique to touch it, and the two sentences are far
enough apart in the file that fixing one without the other would break
whatever the pairing is doing.

**Replacement 1:** "Ruth's coffee cup goes a quarter turn on the table, and then another."
**Replacement 2:** "Her hand turns the coffee cup a quarter turn on the table, and then another."

## Report

- **Fixed active-to-passive (fake agency removed):** 1 (chapter 19, the
  negotiation board).
- **Fixed passive-to-active (person removed from a passive subject):** 1
  (chapter 20, Sam's waffle ritual).
- **Called out, not changed:** 1 (chapter 20, the coffee cup).
- **Strongest call-out:** the coffee cup at 20:27. It is a textbook instance
  of the book's named fault by the letter of the rule, but it sits ten lines
  from an explicit, active, named-actor version of the identical gesture
  performed by the identical character once the news she was working up to
  has actually been said — which reads as authorial before/after rather than
  as an oversight, and is exactly the kind of case the brief asks to be
  written up rather than guessed at.
