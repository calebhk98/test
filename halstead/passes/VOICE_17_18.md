# Voice pass, chapters 17 and 18

Scope: `chapters/17_fourteen.md`, `chapters/18_fifteen.md`. Dialogue and chat
lines were not touched anywhere. Protected passages left untouched as
instructed: Iyad's manufactured rumour in 18 (the sign-up sheet paragraph and
the confrontation where Chloe names the sheet and he answers with a question
about Aurel), and Bex's account of the fight at the sinks in 17. The prior
ruling on "Her name is listed on an internal research paper in March" (18,
line 159) also stands untouched — that research thread is not clearly
Sanders's, and a doer was not invented for it.

Baseline confirmed with `measures/style_report.py` before and after: 17 went
from 5,043 to 5,036 words (shorter, as required), 18 from 4,687 to 4,689
words (well inside the 2,000-5,000 band). Conjunction rates, sentence-length
buckets, and the tic scan are unchanged or improved in both files; no new
"sentence opens She/He + verb" instance was introduced (three of the six
fixes below would otherwise have opened with "She" and were written with the
name instead for that reason), and no fix used "puts/sets it down."

## Changed

### 1. chapters/17_fourteen.md, line 69

**Before:** "What comes back to her at the sinks from a girl in her own year
she has barely spoken to is the question, whether it is true she taught the
lot of them backwards."

**After:** "A girl in her own year she has barely spoken to asks her at the
sinks whether it is true she taught the lot of them backwards."

**Why:** The actual doer (the girl) was already named in the sentence, just
buried in a "from" clause under a cleft ("what comes back... is the
question") that put the abstract rumour in the subject slot instead of the
person asking it. Making her the grammatical subject is a direct active fix
with no invented fact, and it drops seven words, which chapter 17 needed.

### 2. chapters/17_fourteen.md, line 103

**Before:** "The groups for engineering and design go up on the noticeboard
in the first week of February, a handful of names under each, the school
choosing all of it, with the brief on a single page underneath."

**After:** "The school chooses the groups for engineering and design, then
puts them up on the noticeboard in the first week of February, a handful of
names under each, with the brief on a single page underneath."

**Why:** Textbook fake agency — "the groups... go up on the noticeboard" is
the same construction as "the sheet goes up on the wall" in the brief's own
example list. The doer was already sitting in the sentence as a dangling
participle ("the school choosing all of it"); this promotes it to the main
clause instead, which also removes the loose participial tail and saves a
word.

### 3. chapters/17_fourteen.md, line 127

**Before:** "Kavi has it in a fortnight, but then has it no further, and the
number surfaces at dinner in the middle of March, with his hands flat either
side of the tray."

**After:** "Kavi has it in a fortnight, but then has it no further, and he
gives the number at dinner in the middle of March, with his hands flat
either side of the tray."

**Why:** "The number surfaces" hides the fact that Kavi is the one revealing
it — confirmed two lines later when he says so directly in dialogue. Naming
him as the doer of his own disclosure is the clean fix; the rest of the
sentence, including the physical detail at the end, is untouched.

### 4. chapters/18_fifteen.md, line 37

**Before:** "The old things get tried in turn: the count runs on her leg
walking down to the range, the way it did on the archery field, but the
number turns out unchanged on the Friday."

**After:** "Chloe tries the old things in turn: the count runs on her leg
walking down to the range, the way it did on the archery field, but the
number turns out unchanged on the Friday."

**Why:** This opens a montage of Chloe's own escalating attempts to break her
plateau; every sentence after it already has her as an explicit active
subject ("she holds her breath," "she has weeks of cards fanned out"). The
passive opener was the odd one out, hiding the one person the whole passage
is about. Word count is identical.

### 5. chapters/18_fifteen.md, line 65

**Before:** "Chloe goes, running the numbers again all the way down. The box
returns to the shelf that evening, square on top of the year below's, and
she leaves both of them where they are."

**After:** "Chloe goes, running the numbers again all the way down. That
evening she returns the box to the shelf, square on top of the year below's,
and leaves both of them where they are."

**Why:** "The box returns to the shelf" is the same fault as "It goes to
Deb" — an object moving with nobody credited, when the very next clause
("she leaves both of them where they are") shows it is obviously Chloe doing
it. Folding both actions onto one subject also removes a redundant subject
switch. Word count is identical.

### 6. chapters/18_fifteen.md, line 123

**Before:** "Forty goes to a girl called Fen at ten percent against a table
saw, and the last thirty to Priya at twelve, unsecured, because it is
Priya."

**After:** "Chloe lends forty to a girl called Fen at ten percent against a
table saw, and the last thirty to Priya at twelve, unsecured, because it is
Priya."

**Why:** This is close to verbatim the brief's own example of the fault
("It goes to Deb"): a sum of money moving on its own, when the whole
surrounding scene is about Chloe deciding who to lend to and at what rate.
Naming her as lender costs one word, well inside chapter 18's room.

### 7. chapters/18_fifteen.md, line 173

**Before:** "Then she takes a week over it and builds the case against
first: somebody her age asked to guard a secret that already had other
names on it."

**After:** "Then she takes a week over it and builds the case against
first: Sandoval asking somebody her age to guard a secret that already had
other names on it."

**Why:** "Somebody her age asked to guard a secret" is a reduced passive
built on a person (Chloe herself, referred to obliquely) — the same shape as
"Chloe is told," just with the pronoun swapped for a description of her.
Sandoval is the doer and is already on the page two paragraphs earlier
asking exactly this of her; naming her turns the fragment into an active
gerund phrase instead. One word longer, inside chapter 18's room.

### 8. chapters/18_fifteen.md, line 191

**Before:** "A few minutes with Kavi at a terminal puts him back inside."

**After:** "Kavi gets him back inside in a few minutes at a terminal."

**Why:** The grammatical subject was a stretch of time, not the person doing
the fixing. Kavi is named two sentences earlier as the one who built the
whole security scheme; making him the subject of his own fix is a direct
swap with no word-count change.

## Called out, not changed

### chapters/17_fourteen.md, line 67

**Current:** "One of the twelves tells it at their own table, where it is
funny and nothing else, and it takes two days to get from there to Iyad."

**Why the voice is wrong:** "It takes two days to get from there to Iyad"
gives an abstract subject ("it," the rumour) an active verb of motion with
nobody credited for carrying it, the shape the brief flags as the book's
recurring fault.

**Why I did not change it:** The doer here is genuinely diffuse — this is
the rumour mill (per `DO_NOT_FLAG.md`, deliberately never signposted or
attributed to one carrier), not a single traceable person the way the
noticeboard or the loan above were. Naming one student as the carrier would
invent a fact the text does not support, and a passive that implies a single
carrier ("it has been carried") would be smuggling in the same invented
specificity from the other direction. I was not confident either fix is
better than the original, so I left it for the author to rule on.

**Replacement 1:** "One of the twelves tells it at their own table, where it
is funny and nothing else, and the year below carries it to Iyad within two
days."

**Replacement 2:** "One of the twelves tells it at their own table, where it
is funny and nothing else, and within two days it has been carried from
there to Iyad."

### chapters/18_fifteen.md, line 17

**Current:** "Voss delivers it like a thing he has said a thousand times to
a thousand students, and it is round the year by Thursday and back at
Chloe's own table before the end of the month, quoted with the settled
confidence of something printed in a manual."

**Why the voice is wrong:** "It is round the year by Thursday" is the same
pattern as the chapter 17 case above — the line's spread through ninety
students given as something that just happens to have occurred, with no one
credited for repeating it.

**Why I did not change it:** Same reasoning as the chapter 17 case: this is
ninety students independently repeating something Voss said to all of them
at once, not a single chain of hand-offs. There is no one person in the text
to credit, and this sentence sits right next to the chapter's other
diffuse-spread case, so I treated them the same way and left both for the
author.

**Replacement 1:** "Voss delivers it like a thing he has said a thousand
times to a thousand students, and the year passes it around by Thursday,
back at Chloe's own table before the end of the month, quoted with the
settled confidence of something printed in a manual."

**Replacement 2:** "Voss delivers it like a thing he has said a thousand
times to a thousand students, and by Thursday it has gone round the year and
back to Chloe's own table before the end of the month, quoted with the
settled confidence of something printed in a manual."
