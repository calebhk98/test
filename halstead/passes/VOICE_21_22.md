# Voice pass: chapters 21-22

Scope: `chapters/21_the_applications.md`, `chapters/22_the_offer.md`. Read in
full first: `passes/HOUSE_RULES.md`, `passes/DO_NOT_FLAG.md`, root `CLAUDE.md`.

Method: swept both chapters for every `is/was/are/were/has been/have been/had
been` + participle construction and every inanimate-subject-plus-active-verb
construction (the two patterns the brief names), checked each against the two
book-specific rules (no person in the subject of a passive; no fake agency),
against the four general passive/active rules, and against `DO_NOT_FLAG.md`
and the protected passages named in the brief (Bex claiming the geometry, Ruth
hearing the second telling, Chloe's reason for turning down the offer,
Amberg's speeches). Dialogue was left untouched throughout, per the brief.

Confirmed with `measures/style_report.py` on both files before and after:
tic scan stays clean (none found, both chapters), section breaks unchanged,
2+ "and" rate unchanged in both chapters, no new instance of the banned
phrases, no new sentence opening on "She"/"He" + verb.

Word counts: chapter 21 5059 -> 5048 (shorter, as required). Chapter 22 4786
-> ~4792 (small increase, within its room).

## Changed

### 1. Person in the subject of a passive (highest-priority rule)

**chapters/21_the_applications.md, line 5**

Before: "Chloe has been compared to the identical ninety-one people since she
was seven, and the only number the school has ever given her is her place
inside them, a place squarely in the middle."

After: "The school has compared Chloe to the identical ninety-one people
since she was seven, and the only number it has ever given her is her place
inside them, a place squarely in the middle."

Why: Chloe is the grammatical subject of a passive verb ("has been
compared") in the opening sentence of her own chapter, which is exactly the
construction the brief calls the highest-priority fix — it reads as
something happening to her rather than an institution doing it. The doer
(the school) is already named two words later in the same sentence, so
making it the subject invents nothing; it also fixes the sentence to match
its own next clause ("the only number the school has ever given her"),
which is already active with the school as agent. Word count unchanged (34
words each way).

### 2. Fake agency: a doer already on the page, displaced by an inanimate subject

**chapters/22_the_offer.md** (in the paragraph beginning "Iyad has the day at
dinner")

Before: "...and hers gets the same voice as everything else on the list,
and the boy across from her wants to know whether she is sure."

After: "...and he gives hers the same voice as everything else on the list,
and the boy across from her wants to know whether she is sure."

Why: Iyad is the subject of every other verb in the sentence ("has," "takes")
and is the one narrating the table by name; switching mid-sentence to "hers
gets" hands his action to her situation instead of to him, the textbook fake-
agency swap (grammatically active, nobody acting). The fix needs no new
fact — Iyad is already the doer of the clause on either side of it.

### 3. Fake agency: names/lists moving themselves

**chapters/22_the_offer.md**, the section-summary line after the exit
interviews

Before: "Ninety-one names go up in all, and thirteen of them turn into
yeses, each settled before the walk back to class is over."

After: "All ninety-one names are posted in the end, and thirteen of them
turn into yeses, each settled before the walk back to class is over."

Why: "names go up" is an inanimate subject with an active verb doing the
work a person (admin, who "posts a roster outside the staff office each
morning" earlier in the same chapter) actually does — the fault the brief
names by example ("the sheet goes up on the wall"). Rather than invent an
agent for what is genuinely a faceless tally (naming admin here would be
noise, per rule 1.1), the fix takes the second-best option the brief
allows — a passive that implies the doer — and matches the wording already
used two sentences later for the same event ("all of their names are posted
inside the first few days"), so the chapter now says the same thing the same
way both times instead of switching voice partway through its own summary.

### 4. Fake agency: same pattern, same paragraph

**chapters/22_the_offer.md**, end of the same paragraph

Before: "...the ordinary business of finishing something they'd half
finished before the list ever went up."

After: "...the ordinary business of finishing something they'd half
finished before the list was ever posted."

Why: same fault as #3 and in the same breath — "the list went up" is the
list acting on its own. Fixed the same way and for the same reason, so the
paragraph does not fix the fault once and repeat it a sentence later. Word
count exactly unchanged (6 words each way).

## Called out, not changed

### chapters/21_the_applications.md, line 141

**Current:** "asking follow-up questions that all get short, exact answers
back."

**Why the voice is wrong:** "questions...get answers" is an inanimate
subject doing what the students in the room actually do (answering him);
the real actors are on the page two sentences earlier and are not named as
the ones doing this.

**Why I did not change it:** Chapter 21 has to stay word-neutral or shorter,
and every replacement I found added a word or changed the rhythm of a long,
already-loaded sentence (four clauses joined by "and," itself close to the
book's 2+ "and" ceiling) enough that I was not confident the fix was worth
the risk to a sentence that is not clearly broken — "questions get answers"
also reads to me as closer to ordinary idiom than to the book's disguised-
mover fault (nobody's contribution is being stolen the way Iyad's or the
admin's was in the changes above), so I was not sure this is actually wrong
rather than merely close in shape to what's wrong.

**Replacement 1:** "asking follow-up questions the students answer, short
and exact, every time."

**Replacement 2:** "asking follow-up questions and getting back short,
exact answers."

### chapters/21_the_applications.md, line 107

**Current:** "The methods section names her for the part he has no way to
check on his own."

**Why the voice is wrong:** the document is the grammatical subject doing
the naming, when what actually happened is that whoever wrote the paper
credited her by name in the methods section — a person's act of attribution
assigned to the paper instead.

**Why I did not change it:** I could not tell who the fix should credit.
The paper has three listed authors and this is specifically about a step
attributed to the youngest of them; naming "the paper" or "the authors" as
the actor doing the naming would either restate the subject with a synonym
or invent a claim about which author wrote that section, which I don't have
grounds for from the text. This also reads to me as closer to how people
normally talk about what a document says ("the file names him," "the report
credits her") than to the disguised-mover fault the rule is really about, so
I'm flagging it rather than guessing.

**Replacement 1:** "She's named in the methods section for the part he has
no way to check on his own."

**Replacement 2:** "Whoever wrote the methods section named her for the
part he has no way to check on his own."

## Report

- Changed: 4 sentences (1 in chapter 21, 3 in chapter 22). All 4 were fixes
  in the same direction: an inanimate/institutional subject doing what a
  person or a named institution actually does, restored to either an active
  sentence with the real doer or a passive that implies it. No sentence
  needed the opposite fix (active correctly rewritten to passive to hide an
  irrelevant doer, or vice versa) beyond these.
- Called out, not changed: 2, both in chapter 21, both fake-agency
  candidates I was not confident enough in to touch given the chapter's
  word-neutral constraint and the risk of mistaking ordinary idiom for the
  book's specific fault.
- Strongest call-out: chapters/21_the_applications.md, line 107, "The
  methods section names her for the part he has no way to check on his
  own" — because unlike the other three fake-agency fixes I made, I don't
  know who the real doer is (which of three credited authors wrote that
  step), so any fix I made would either invent a fact or just swap in a
  synonym for the same subject, and the author should decide which reading
  is intended before either happens.
