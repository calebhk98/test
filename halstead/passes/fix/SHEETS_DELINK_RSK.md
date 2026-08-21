# De-linking pass: RUTH, SAM, KAVI

Rewritten against `characters/_SHEET_RULES.md`. Three sheets, full rewrites
rather than edits, because the hard-linking was structural: on all three the
evidence was doing the work the description should have been doing, and pulling
the quotations out of the old text would have left holes rather than prose.

**Success condition met.** `python3 verify_citations.py characters/RUTH.md
characters/SAM.md characters/KAVI.md` now reports **0 quotations checked, 0 not
found**. Before: RUTH 40 checked / 15 stale, SAM 33 / 15, KAVI 6 / 2. The
whole-set figure moved from 298 checked / 165 stale to 129 / 86; the remainder
belongs to sheets other agents own.

Also cleared on all three: no manuscript quotation marks of any kind (zero `"`
characters in all three files), no `chapters/` paths anywhere, no line numbers,
no em dashes or curly quotes, and no statistic computed from the draft.

Each sheet ends with one clearly separated **Continuity and navigation**
section, facts only, and each passes the delete-it-and-read-what-is-left test.

---

## 1. What came out, and what replaced it

### Draft statistics (rule 3)

Removed from all three: the `Dials` tables entire, along with every number in
them. Words per line in chat versus tagged prose; percentage of lines at three
words or fewer; percentage hedged; percentage of turns that are questions;
counts of turns spoken and typed; "speaks ~190 turns, 98 of them in the group
chat"; "~61 lines total, heavily front-loaded"; "roughly 110 lines"; "zero
instances anywhere in the manuscript"; "44% of his chat lines"; "a third of his
turns"; "9.5 words a line". Also gone: the recurring parenthetical "a
measurement, not a target", which is an admission that the line was measuring a
draft.

What each number was actually measuring has been converted to a tendency:

| removed statistic | what the sheet now says |
|---|---|
| Ruth 9.5 / 9.8 words a line, steady | mid-length, evenly built, and the length does not move: she does not clip when frightened or pad to be liked |
| Ruth 3% hedging | no hedge on a claim she has finished testing; a qualifier survives only while she is still assembling one |
| Ruth 22% of lines at three words or fewer | dropped; it was measuring nothing about her that the conclusion-first description does not already carry |
| Ruth "41 of 191 questions, 16 with a question mark" | she asks a great many and punctuates them as questions; what is hers is the shape, described in three named forms |
| Sam 5.5 / 6.5 words a line, "no room above it" | one flat clause, said and done, plus an explicit account of what the terseness is and is not (see 3 below) |
| Sam hedging 0% with one crack | absolute on facts, plans and himself; the single soft word survives only where the subject is whether another person is all right |
| Sam "longest message is twenty words" | dropped |
| Kavi 6.5 / 6.8 words, bimodal, 44% clipped | clipped by default; lengthens exactly as far as the mechanism takes and stops at the end of the explanation rather than at the listener's reaction |
| Kavi "questions 0% measured" | few, aimed at one unresolved mechanism, plus the person-directed exception (see 4 below). The zero was false. |

### Quotations (rule 1)

Every quoted line is gone, including the ones that currently match the
manuscript. Where a quotation was carrying a real observation, the observation
was rewritten as a property:

**Ruth.** The two signature-move lines (both replaced in the manuscript since
the sheet was written, both real now) are out; the move is described instead:
she puts the other person's name inside the sentence doing the correcting, so
the correction is addressed rather than announced. The three quoted questions
are out; they became the three question shapes, which is more useful than the
examples were, since a writer on a lunar colony can build all three. The
quoted deflection of credit became a general habit with a reason attached: she
prices her own work downward because a compliment resting on a wrong estimate
of difficulty is a wrong claim standing. The quoted marksmanship figure became
a disposition (she answers a question about her own ability with a figure,
including an unflattering one) with the number itself moved to continuity. The
quoted arm-writing sentence became the habit plus the part the quotation did not
carry: she forgets it is there and finds out from someone else's face. The
Arabic-versus-Latin speech became the principle underneath it, a language with
living speakers who can tell her when she is wrong.

**Sam.** The room-shaped-object line, the accuracy speech, the culvert
self-critique, the dance exchange, the boredom question, the water-reaching
line, the kit line, the Odile exchange, the two number-first examples and the
Ruiz description are all out. What they were evidencing survives as: the
deflating literalism as his single permitted figurative channel; talking the
record down as the one thing that reliably makes him go long, in both
directions (refusing a compliment he did not earn, volunteering blame nobody
assigned); the number-first habit; and the physical business.

**Kavi.** The compute-cost line, the volcano stage direction, the put-down, the
art-history exchange, the AES label line, the deadline-clause line and the
`[PROPOSED]` invented line are out. Note that the `[PROPOSED]` entry was
precisely the failure mode `verify_citations.py` exists to catch: a line that
reads exactly like the book, sitting in a table of real citations, that nobody
ever wrote. It is gone rather than de-quoted.

### Chapter and line references (rule 2)

No sheet cites a file or a line any more. Chapter *numbers* appear once per
sheet, in the navigation line at the bottom, as a list of where the character
appears. Nothing in the body of any sheet rests on a location.

### Known problems sections

Dropped where they were draft archaeology: entries recording lines that have
already been fixed and no longer exist in the manuscript ("left here so it is
not re-found" is unnecessary once the line it names is unfindable). Kept, moved
into the continuity section and rewritten without quotations, the three that a
later pass could still act on wrongly:

- Ruth: the surname collision with a background student, which the author has
  ruled is fine and is not to be renamed.
- Ruth: the Kavi/Ruth shared elective, raised as a defect three times and ruled
  not one.
- Kavi: the still-unanswered surname, and the fact that Rao is a sheet-level
  decision, not a manuscript one.
- Sam: the apparent tension between his no-ceiling habit and his contentment at
  forty percent, with the distinction that resolves it.
- Kavi: his line-count problem across ordinary ensemble scenes.

---

## 2. What was carried across

Nothing in the author's "what must survive" list was dropped.

**Ruth.** How she reasons (conclusion first, outcome is not an argument, the
measure has to be named before a comparative claim gets evaluated, a small
deliberately reused vocabulary). What she does with a number (takes it at face
value; chases a bad mark to find the marking rather than to change it; produces
a figure about herself flatly; goes and finds the number herself rather than
argue about impressions; prices her own work downward). Friend versus examiner,
now a section of its own: unpaid unglamorous labour on one side, the same
person with the affection switch stuck off on the other, and the note that
being fond of somebody makes her more likely to correct them.

Her being wrong has the most new writing on it, because the brief asks for the
disposition that makes the late arc possible without narrating the arc. What
the sheet now says: she can build and hold a plausible false theory for months
rather than say a half-formed wrong thing in public; contrary signals get
analysed with the same forensic pass she would run on anyone else's mistake,
which keeps returning the wrong answer because it is aimed at the wrong object;
contradiction from an opponent cannot reach her, and being asked to slow down
by somebody she likes and rates can; and once it breaks she does not argue, she
goes and collects the evidence herself, one piece at a time, each worse than
the last. The load-bearing sentence is that she cannot hold a wrong idea
against evidence she gathered with her own hands, because then it is her own
work saying it. Also kept: the drafting habit, long versions written and short
ones sent, so a confession reads to everyone as characteristic curtness.

**Sam.** The terseness, with an explicit account of what it is not (see 3). The
self-mockery, including the instruction that he does not have a forbidden
subject. The physical confidence, including that he does not remark on it and
only ever remarks on the numbers attached to it. What he does when someone he
likes is struggling, now its own section: the joke rather than the correction,
the flat plain question about whether they are all right (the only place a soft
word gets into his speech), and the apology delivered as a carried bag or a
taken turn rather than as words.

**Kavi.** Playing the person rather than the board, which was **not on the old
sheet at all** and is now the second section, framed as the resolution of the
apparent contradiction in him: he reads people fast and accurately and has
simply never thought to use it for their comfort. The conclusion-first habit.
What he is like when he has decided something is unjust, also now its own
section: not loud, not personal, thorough and unbudgeable, spending
disproportionate effort exactly where there is nothing in it for him, preferring
paper to confrontation, and assuming an institution is a system with a correct
output, which is usually wrong and which he does not learn from one experience.

**Age and change** is a full section on all three, six to twenty-one, written in
bands. Ruth's runs from compulsively public corrections at six through the
teaching years to the years where she becomes capable of holding a belief
privately, which the sheet is explicit is fear rather than maturity. Sam's runs
from defending the half on his age through the body arriving all at once at
fourteen (with the note that his manner did not change at all) to meeting an
institution that would rather be flattered than corrected. Kavi's runs from
silence that is not shyness through the year several subjects turn out to be
one idea, to being the one who does not want to leave.

---

## 3. Wrong about the character, not merely hard-linked

Flagged separately as requested.

1. **Ruth, questions.** The old sheet had already been partly corrected in its
   Dials row, but the correction sat next to a Voice paragraph that still
   asserted she never hedges and a rule set that treated her question shape as
   an exception to a low rate. The false zero is an artefact of a tagged-line
   script, which cannot see the answering half of a two-hander, and questions
   are exactly what rides on the untagged half. The rewrite states the opposite
   of the original defect: she asks a great many and punctuates them as
   questions, and anybody writing her as a person who avoids them has her wrong.
   The true thing is the shape, and it is now described in three forms rather
   than by example, including the flat declarative that works as a question and
   gets answered as one.

2. **Ruth, internal contradiction on hedging.** Voice said she never hedges;
   Dials said 3% is right for her and should not be driven to zero. Both cannot
   be instructions. Resolved as: no hedge on a settled claim, a qualifier
   possible only while she is still assembling one.

3. **Ruth, the signature evidenced by lines nobody wrote.** Both invented lines
   have since been replaced by real ones in the manuscript, so the sheet was no
   longer citing fiction, but the episode is the reason the rule exists. The
   move is now described and cannot go stale.

4. **Sam, the cast-wide uniqueness claim.** "Nobody else in the cast opens a
   line this way" is false; Ruth does it five times. A claim about the cast is a
   claim about the draft twice over. Narrowed to a property of his own lines:
   what is his is that the number is about himself and closes the subject rather
   than opening one, and the sheet says explicitly that he does not have sole
   possession of the move.

5. **Sam, subordinate clauses.** The absolutism survived in the Dials row and in
   a NO rule even after the Voice paragraph had been corrected. He subordinates
   whenever the sense needs it. What he does not build is a clause that takes
   weight off a claim, which is a different statement and is the one now on the
   sheet.

6. **Sam, "the book cannot afford more of it".** The terseness dial carried
   "there is no room above it", which is a note to a drafter about a manuscript,
   not a fact about a person. Converted into the what-it-is-and-is-not list: not
   reticence, since he will talk for an hour about a story where he came off
   badly; not an inability to build a sentence; not coldness, since it is the
   same length whether he is agreeing or refusing.

7. **Sam, the laughed-at claim.** The version I inherited had already been
   corrected and its Known problem withdrawn, so there was nothing to reverse.
   Preserved and hardened: the deflection trigger is being asked how he felt,
   not being laughed at, and the sheet now instructs directly that he must not
   be given a subject he refuses to discuss on the grounds of embarrassment. His
   response to the feelings question is unchanged and is a disposition rather
   than a scene: he picks up the nearest object and talks about that, at his
   ordinary volume, with no visible tension, because he does not have an answer
   in that register rather than because he is protecting a wound.

8. **Kavi, "questions 0% measured".** Same script artefact, same false law. He
   asks few questions, but his two most consequential ones in the book are aimed
   at a person's state rather than at a mechanism. Rather than treat that as an
   exception, the sheet folds it into the trait: when the unexplained thing is a
   person he interrogates the person the way he would interrogate a machine, and
   the result is not brutal, because it is the only response in the room that
   treats the other person as somebody with an answer rather than somebody to be
   handled. This is the same faculty as playing the person rather than the
   board, and the two sections now support each other.

9. **Kavi, "no scene shows him wrong".** A statement about coverage, not about
   him. Converted to the disposition the rest of the sheet implies: he corrects
   the record about himself exactly as he corrects it about anyone, flatly, and
   asks for no credit for the honesty.

---

## 4. Close to the line

Judgement calls, listed so somebody else can overrule them.

- **Skill figures kept in continuity.** Ruth at ninety-one percent and Sam at
  forty on the intercept drill are still on the sheets, in the continuity
  section only. These are facts of the world a writer must not contradict, like
  a surname, rather than statistics computed from the draft, and both sheets
  carry the interpretation portably in the body (each reads a local ranking as a
  global one). If the ruling is that any number goes, these three lines are
  where to cut.
- **Kavi's line-count problem, Sam's no-ceiling tension, and the note that
  Kavi's home life is built past the page.** All three are notes about the
  manuscript rather than facts of continuity, and all three sit in the
  delete-safe section. Kept because a later pass could otherwise re-find and
  wrongly "fix" them. They are the least rule-compliant lines I have left.
- **Cast-relative statements.** Each sheet keeps a short not-to-be-confused-with
  section and a relationships section, both of which name other characters. They
  survive the test only if the rest of the cast travels to the lunar colony too,
  which they do, and none of them cites a scene. Sam's uniqueness claim was the
  one that was false and it has been narrowed; the rest are contrasts of move,
  not counts.
- **Ruth's "would never let an old wrong statement go unaddressed".** True of
  other people's statements and conspicuously not true of her own, which she can
  sit on for the better part of a year. The asymmetry is now written into the
  body rather than left for a reader to hit as a contradiction, but the two
  lines still have to be read together.
- **Halstead as a setting word.** Kept out of the body of all three sheets
  almost entirely; where the closed comparison class matters to character it is
  phrased as one small selected population, which works anywhere. The school
  appears by name only in continuity.
- **Length.** The sheets are between a third and 40% shorter than the ones they
  replace (Ruth 36KB to 24KB, Sam 37KB to 22KB, Kavi 31KB to 21KB). Nearly
  all of that is evidence, tables and line references. The only substance I
  deliberately let go is the per-language commentary on subject lists, which is
  now a fact list at the bottom with the portable principle (she wants a
  language whose speakers can correct her; he wants one that behaves like a
  closed rule system) kept in the body.
