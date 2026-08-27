# Open findings: calibration audits, merged and re-checked

> **Read `../DO_NOT_FLAG.md` before acting on anything in this file.** These are
> agent extractions from the audit round of 2026-08-27, not verdicts. Several
> findings in this batch were checked line by line against the current chapters
> and did not reproduce — including one ranked in a top ten that reads a scene
> as the inverse of what it does, and one built on a quotation that is not in
> the book. The refuted list is at the end of `DO_NOT_FLAG.md`.


Source: `CAL_01-05.md` through `CAL_31-35.md` (eight audits, written 2026-08-21,
covering chapters 1-35 with no overlap between spans). Every quoted line below
was re-checked against the current chapter text on 2026-08-27. The manuscript
has been heavily edited in the six days since the audits were written — three
separate editing passes (`git log -- chapters/`) touched narration-voice,
reading grade, and "the children stop talking like the narrator" specifically
— so a large fraction of what the audits flagged is already fixed. That is the
headline result: **most of what was open is now closed**, and the closures
mostly match the exact fix the audits recommended.

`passes/DO_NOT_FLAG.md` was written 2026-08-27, after all eight audits. I
checked every finding below against it. **Nothing needed to be dropped**: none
of the eight audits flagged the chapter-20 "retarded" line, the Aymar
coincidence, the repeated devices, or any other DO_NOT_FLAG item as a
calibration defect in the first place — where they touch those scenes at all
(CAL_19-22 on chapter 20), they already read them as calibration *working*,
which is the ruling arriving after the fact rather than a conflict.

---

## The one cross-cutting pattern (all eight audits)

Every one of the eight audits, independently, flagged the same shape of
problem at least once: **the narrator does a piece of noticing, comparing, or
concluding that a calibrated character is not allowed to do herself.** Most
instances are House-Rule-1 violations (talking to the reader) rather than
pure calibration failures, but a meaningful minority are both at once — the
narrator supplies the favorable comparison the standard requires the
*character* to be denied.

This is the one item in this report that is a book-wide tic rather than a
scene problem, by the letter of the brief ("found in five spans is a
character problem"). It appears, in some form, in all eight spans:

- CAL_01-05: four instances (§4.1-4.4) — **all four now fixed** in the text.
- CAL_06-10: four "narratorial half-steps" — **the two live-recommendation
  ones (`06:95`, `06:85`) are now fixed** (one exactly, one reworded but the
  same shape persists).
- CAL_11-14: `13:160`, `13:164` — **both now fixed**, one by deletion, one by
  removing the whole aphorism.
- CAL_15-18: `18:141` (Ruth's argument delivered by the narrator) — **still
  open**, verbatim in substance. `16:9` (staff-room voice) — **still open**,
  unchanged.
- CAL_19-22: `20:83` (fence drill, protected span), `21:63` (now fixed —
  whole passage rewritten), `22:33` (now fixed — closing gloss removed).
- CAL_23-26: `23:101` (now fixed), `23:125`/`23:98`/`25:28`/`25:121` (echo
  glosses — **all now fixed**, matching the commit titled "The reads-it-twice
  tell, cut and put under measurement").
- CAL_27-30: `27:103` (now fixed — whole scene rewritten), `28:5` (now fixed),
  `30:7` (now fixed), `30:23` — **still open**, `27:89`, `27:92` — **still
  open**, `28:92` — **still open**, `30:63` — **still open** (minor).
- CAL_31-35: `35:143`, the book's closing sentence — **now fixed**, the
  ending is rewritten and no longer totals anything. `31:106` — not
  re-checked line-for-line (chapter 31 is substantially rewritten around it;
  low confidence either way).

Net: of roughly twenty instances of this pattern across the eight audits,
about fourteen are now fixed. The six still open are listed individually
below. The pattern is a genuine repeated tic, but it is trending down and
being actively worked, not neglected.

---

## Open findings, individually

Each entry: what / where / how many spans this shape appears in / status
against current text / how to check it / severity and scope.

### 1. Chloe hears the one clean sentence of her own assessment and it lands unopposed — `02_march_4th.md:247` (originally `:175`)

**What.** Dr. Prentice tells Chloe's mother, in Chloe's hearing, "on the
talking and reasoning she's at the top of it, but on the speed she's
ordinary, so what comes out says bright kid, but bright kid undersells the
room I sat in this morning." Her only reaction is bodily ("Chloe shifts on
the chair, her feet nowhere near the floor"). Everything else in the same
scene is either technical or about her *deficits*; this is the one plain,
unhedged, favorable clause, and nothing absorbs, misreads, or explains it
away.

**Found by.** CAL_01-05 only (its single headline finding — "the one real
finding below"). Scene problem, not a character pattern, but it is the
earliest and clearest instance of the book's central risk, in the book's
second chapter.

**Status.** **Still open.** Verbatim in substance: the sentence survives
essentially unchanged from the quoted audit text, and the surrounding scene
(mother asking "how far at the top," Chloe's only response still purely
physical) is unchanged.

**Checkable.** `grep -n "at the top of it" chapters/02_march_4th.md` → line
247. Read lines 235-260 for the full exchange and Chloe's reaction.

**Severity.** High. Single scene, but it is chapter 2, it is the standard's
own worked example (a child handed plain evidence and giving no absorbing
beat), and the audit itself judged it "close to working" with a
one-sentence fix available (move the muffling that already covers the
deficit half onto this clause too).

### 2. The Marek fail is routed entirely through inference, never through feeling — `16_thirteen.md:51`

**What.** Chloe processes a classmate's course failure — one she is
structurally responsible for signing off — as a chain of institutional
deduction ("whatever a fail costs a student here, expulsion is no part of
it... whether it follows him onto anything that matters... stays outside her
reach for years"), never as relief, guilt, or worry about facing him on
Thursday.

**Found by.** CAL_15-18 only.

**Status.** **Still open**, essentially unchanged (minor rewording: "In
January he is at breakfast as he was in December, in his own year" replaces
"He is at breakfast in January as he was in December, in the same year").

**Checkable.** `grep -n "blank sheet leaves the mark" chapters/16_thirteen.md`

**Severity.** Moderate. Single scene. The audit's own read is that most of
the paragraph is right (her lack of discretion, her hand on the pen); only
the *shape* of her worry is adult ("whether it follows him onto anything that
matters" vs. "whether he is angry with her, and whether she has to sit in a
room with him on Thursday").

### 3. The narrator delivers Ruth's argument for her — `18_fifteen.md:163`

**What.** "Priya says at dinner that the lock held, which Ruth calls the
wrong sentence... The right sentence is that a single lock stood between a
lectern drawer and everything the table has said to each other since the
chat started..." Ruth is named as having the objection; the narrator, not
Ruth, then makes it, in the narrator's own construction.

**Found by.** CAL_15-18 only, but see the cross-cutting pattern above — this
is the sharpest surviving instance of it.

**Status.** **Still open.** The passage is present with light rewording
("since the chat started" replaces "for three days") but the structure —
Ruth named, narrator makes the argument — is unchanged.

**Checkable.** `grep -n "right sentence is" chapters/18_fifteen.md`

**Severity.** Moderate-high. Single scene. The audit's own fix is on the
record and is a small one: give the second sentence to Ruth as dialogue,
since "correction-first-reason-second" is her established signature move,
and let the next line land off her line instead of the narrator's.

### 4. The exam-room comparison the narrator builds for Chloe — `30_cleared.md:21`

**What.** "around her, other candidates chew pens and glance up at the clock
every few minutes... but her own eyes stay on the page from the first
question to the last." Chloe herself never looks at, or judges, the other
candidates — but the comparison is built and handed to the reader by the
narrator instead, which the audit calls "precisely the problem": the
noticing she's correctly not allowed to do has moved up one level rather
than disappearing.

**Found by.** CAL_27-30 only. Companion instance in the same chapter, lower
severity: `30:63`, "it takes **a full** twenty minutes," where "a full" is
the only narratorial thumb on an otherwise clean scale-burying sentence
— unchanged, still present, one word.

**Status.** **Still open**, essentially verbatim (only cosmetic changes: "her
own eyes stay on the page" is now embedded in a longer sentence about the
exam room, but the comparison clause itself is intact).

**Checkable.** `grep -n "eyes stay on the page" chapters/30_cleared.md`

**Severity.** High for visibility, moderate in isolation. This is the
security-clearance chapter — the single highest-stakes place in the book for
a reader to conclude Chloe looks down on people — and the audit's
recommended fix (cut the contrasting clause, or drop the comparison and keep
the other candidates as color) costs nothing structurally.

### 5. Chloe's biggest moral decision gets a steady hand and no shown cost — `33_the_other_one.md:151`

**What.** Spending a federal clearance on a file it was meant to keep from
her — the single largest ethical choice she makes in the book — is
dispatched in one sentence: "What that costs her she works through once, on
the drive home the week the document arrives, and the thought ends in about
as long as it takes a light to change." `CHLOE.md` states her emotion runs
"big or it isn't there... She has no small setting"; this is the biggest
decision in the book taking the smallest visible toll.

**Found by.** CAL_31-35 only.

**Status.** **Open, and arguably worse than when audited.** The
audited version continued "her hand steady through all nine of them, and she
does not stop," which at least gave a small physical marker. That clause is
now **gone** — the chapter ends one line after "takes a light to change,"
with no further beat at all in the chapter.

**Checkable.** `sed -n '145,151p' chapters/33_the_other_one.md` — chapter
ends there.

**Severity.** Moderate-high. Single scene, but load-bearing for the book's
climax; worth the author's attention precisely because it got quieter, not
louder, in the intervening edit.

### 6. Kavi described through two stacked adult-register similes — `22_the_offer.md:39` (originally `:67`)

**What.** "He gives her the look he saves for a mark scheme, and says the
next part in the register he'd use to correct a wrong exponent." Two similes
comparing Kavi's manner to a teacher grading work. `passes/notes/ch22.md`
flagged this exact clause for "talking to the reader and interiority" and
the prior revision dropped one half of it ("and moves on before it lands")
but kept this half.

**Found by.** CAL_19-22 only.

**Status.** **Still open**, essentially unchanged in substance (the sentence
is intact, just relocated in a rewritten scene).

**Checkable.** `grep -n "wrong exponent" chapters/22_the_offer.md`

**Severity.** Low-moderate. Single scene, and the audit itself says "Kavi
himself reads as a person, not a machine" in the same scene, because of a
grounding physical detail (the coil of cable) — this is a leftover half-fix,
not a live defect in his behavior.

### 7. The staff-room-voice paragraph — `16_thirteen.md:9`

**What.** "Six of the seven are straightforward: Ivy and Tomas want the
answer handed over... Beatriz arrives already knowing most of the material
and so takes a few minutes of the hour and uses them well, two more turn up,
work, leave." A competent teacher's end-of-year summary of a class,
compressed into two sentences, in Chloe's mouth/head at thirteen.

**Found by.** CAL_15-18 only. Noted explicitly as "noted, not actioned" in
the original audit — the audit judged it lands on balance (the very next
line has her on the floor for forty minutes with a crying twelve-year-old,
which no staff-room summary would include), but flagged the register as the
chapter's closest approach to that failure mode.

**Status.** **Still open**, unchanged, word for word.

**Checkable.** `grep -n "Ivy and Tomas" chapters/16_thirteen.md`

**Severity.** Low. Single scene, already judged not-a-defect by its own
audit; carried forward only because the brief asks specifically for every
place a child sounds like an adult.

### 8. The "sounds like X, so she keeps it to herself" construction, used twice — `08_the_asking.md:171` and `10_april.md:157`

**What.** Both instances close on the same shape: Chloe has a thought that
would sound like she thinks she's exceptional, and suppresses it rather than
say it. Individually each is in calibration (she is afraid of *sounding*
exceptional, not of *being* it); used twice, two chapters apart, in
identical form, the audit worried it starts to imply a suppressed
self-assessment rather than no self-assessment at all.

**Found by.** CAL_06-10 only, but flagged explicitly as "the one note worth
acting on in chapters 7-10."

**Status.** **Partially addressed.** `08:171` is unchanged. `10:157` has
lost its closing clause — the 2026-08-21 version ended "...against them, so
she keeps it to herself"; the current text ends "...against them," full
stop. The repeated "so she keeps it to herself" pattern the audit flagged is
gone even though the "sounds like X" phrasing itself persists in both
places.

**Checkable.** `grep -n "sounds like" chapters/08_the_asking.md
chapters/10_april.md`

**Severity.** Low. The repetition concern has been substantially defused by
the edit; what's left is coincidental phrasing similarity rather than a
repeated mechanism.

### 9. Theo's narrated professional comparisons — `29_the_file.md:11`

**What.** "the halves of a region most analysts only get one side of...
pairing them turns up exactly the kind of mismatch a single-language reader
would miss." Two favorable comparisons against unnamed colleagues, made by
the narrator, not by Theo.

**Found by.** CAL_27-30 only, and the audit's own read is that this is
information about the job (matching `THEO.md`'s stated reason a federal
agency wanted him) rather than admiration of the man — a phrasing question,
not a substance question.

**Status.** **Still open**, verbatim.

**Checkable.** `grep -n "single-language reader would miss"
chapters/29_the_file.md`

**Severity.** Low. Single scene, and the audit itself already says the
sentence works without the second comparison since the clause after it
states the mismatch directly.

### 10. Sheet-vs-manuscript: Kavi is given an unambiguous figurative line — `12_nine.md:73`

**What.** `KAVI.md` states his figurative dial as "not allowed, ever. Zero
instances anywhere in the manuscript." The dinner-table argument now reads:
Chloe — "It's got eleven people in it, Kavi, which makes it a coincidence
with a p-value attached to it." Kavi — "Small result, so round it down,
because a room that size is basically noise dressed up as a finding." The
line is now unambiguously his (the original audited text had it
unattributed in an alternating two-hander, leaving room to read it as
Chloe's ventriloquism of him).

**Found by.** CAL_11-14 only, and explicitly flagged there as "a voice
question, not calibration."

**Status.** **Open, and clarified in the wrong direction** — the edit that
attributed the line more clearly to Kavi makes the sheet conflict sharper,
not weaker, though it is not a calibration defect either way.

**Checkable.** `sed -n '69,74p' chapters/12_nine.md`

**Severity.** Low. Voice-consistency question for whoever owns the
character sheets, not a calibration finding as such — carried here only
because it's a live, checkable discrepancy.

### 11. The named-mental-state clause on the "girl who repeats the number twice" — `22_the_offer.md:9`

**What.** "...says the whole thing twice, the number, the car, all of it,
**as though saying it again will make it hold still long enough to be
believed**." A House-Rule-1 named-state clause (not itself a calibration
defect — the scene around it is judged fully in calibration) attached to a
minor character's only characterization in the chapter.

**Found by.** CAL_19-22 only, and explicitly filed there as an HR1 note
rather than a calibration finding.

**Status.** **Still open**, verbatim.

**Checkable.** `grep -n "hold still long enough to be believed"
chapters/22_the_offer.md`

**Severity.** Very low; included only for completeness since the brief asks
for every quote checked. Not a calibration item.

---

## Findings closed since the audits were written

Listed briefly, by original audit, so the author can see the pass already
credited: `02:241/243` (ch1-5, narrator ranking + gloss, both cut),
`06:95/85` chapter 6 half-steps (both addressed, one exactly per
recommendation), `05:97` (the "whole of it and all it ever was" cadence,
rewritten out), `01:203`/`02:47` region — the "question was built to hold
one" clause is gone (the "files...adults say when they want you to sit
still" register issue at `02:45` **remains open** but was not one of the
audit's flagged recommendations for edit), `13:160/164` (both cut, ch12's
"noise dressed up" aphorism relocated and clarified), `18:17` (the
February/November turret-chronology contradiction — fixed to November,
matching the audit's own recommendation, confirmed by the commit "fix ch18
turret dateline"), `21:63` (ghostwriting-theory passage rewritten), `22:33`
(closing gloss on Chloe's résumé cut), `23:101` (narrator's "field stopped
contesting it" cut), `23:98`/`25:28`/`25:121` (all three "echo gloss"
instances removed — matches the commit "The reads-it-twice tell, cut and put
under measurement"), `25:74-77` (captain-dialogue garble — whole scene
rewritten, no longer contradicts itself), `24:14`/`24:154` (both stale "nine
years" figures removed), `26:41` (arithmetic error — whole exercise
sequence rewritten, hand-on-sternum tally no longer exists), `27:103`
(Nadia's staff-competence paragraph rewritten), `27:20` and `23:98` echo
notes (both gone), `28:5` (the "first room... full of people unlike her"
category-difference sentence rewritten), `30:7` (the "runs the length of a
normal article" comparison rewritten out of the opening), `35:143` (**the
book's final sentence, previously the single largest finding in CAL_31-35**
— the "seven people in their twenties... settled it in sixteen weeks"
narrator total is gone; the book now ends "The next day, she goes in and
does her job."), `31:70` and `31:85/91` (the "beneath her" motivated-denial
passage and the four-tries/two-tries arithmetic mismatch — chapter 31's
whole confrontation-with-the-professor scene has been rewritten; the exact
audited sentences no longer exist), and the chapter-33 birthday continuity
error (she now turns twenty-one in August, matching her established
birthday, instead of May/June).

One item closed by omission rather than by fix: CAL_31-35's note that
"seven people in their twenties" implies a headcount of seven when Priya
(an eighth chat member per chapter 24) is never accounted for — the phrase
itself is gone along with the rest of that sentence, and a scan of chapters
31-35 turns up no other "the seven" headcount language, so the
inconsistency appears to have been retired along with the sentence that
carried it.

**One residual concern in a rewritten scene, flagged for the author's
attention even though it isn't the original quoted finding.** Chapter 31's
professor scene was rewritten to fix the "four tries vs. two tries" problem
CAL_31-35 raised, but the replacement introduces a new version of the same
shape: the professor now says his graduate students "would not have got me
there at all," but Ruth's very next line still measures herself against a
hypothetical peer who "would have needed two tries at what took her five" —
a figure the professor never actually gave. Not one of the eight audits'
quoted findings (the text has changed too much to be the same finding), so
it is reported here only as a footnote, not counted in the list above.
`grep -n "would not have got me there\|two tries" chapters/31_ruth.md`

---

## The two things most wanted

### Where a child sounds like an adult

By character, every instance found across the eight audits that is still
open in the current text:

- **Chloe** — the largest concentration, and the only character with a
  finding rated "high severity." `02:247` (finding 1, above): hears her own
  assessment stated plainly and reacts only physically. `02:45`: "files the
  last part with everything else adults say when they want you to sit
  still" — a categorized generalization about adults rather than a
  six-year-old's suspicion of one man (content is right for her age, the verb
  and framing are not; not independently edited since the audit).
  `16:51` (finding 2): the Marek paragraph, worry routed through
  institutional deduction. `30:21` (finding 4): the narrator's exam-room
  comparison. `33:151` (finding 5): the clearance decision timed like a
  traffic light, no shown cost.
- **Kavi** — one instance, and it is the most explicit self-knowledge given
  to any character in the book: `35:51`, "the only reason i built that is
  because im me." CAL_31-35 judged this earned (by two chapters of setup)
  but flagged it as "the outer edge" — if the author wants the ending to
  keep any reticence, this is the line to look at before Ruth's. Confirmed
  still present, lightly reworded.
- **Marek** (not Chloe) — `16:21`, "he says it the way he says everything,
  with his hands still and his voice level," reads Vulcan in isolation but
  is immediately undercut twice in the same chapter (halfway out of his
  seat; visibly thinking for ten seconds). Judged in calibration by its own
  audit; not independently re-checked, listed for completeness since it was
  the second-closest call in CAL_15-18.
- **Nobody else.** Sam, Ruth, Nadia, Eli, Theo, Priya, Odile, and Fen have no
  open "sounds like an adult" finding across any of the eight audits. Sam
  and Ruth each came the closest to a genuine violation (Ruth's professor
  scene, Sam's "not going to be wrong") and both were explicitly checked and
  cleared by their own audits, on grounds recorded above.

### Where someone acts on knowledge they haven't earned yet

**No open finding.** This is the question the eight audits checked hardest
and hardest to break, and none of them succeeded. Every capability the
audits traced back to its source found a planted, earlier scene: Ruth's
camera box to her chapter-15/34 electronics elective, Kavi's file-tampering
detection to the sensor-gap caution seeded at `33:123`, Chloe's read of a
hollow vendor contract to the logic class planted at `11:123`, Eli's
"besting an ordinary system without registering it" to the file entry at
`34:12` rather than a needed earlier scene. The one place an audit called
for a missing plant (`ELI.md` Known problem 1, asking for an earlier scene
showing Eli operating outside Halstead's ranking) turned out to already
exist, later in the same chapter, better placed than a seeded one would
have been. If this remains the one clean axis in the book, it is worth the
author knowing it, rather than only hearing about the six things above.

---

## Per-character summary

**Chloe.** Holds overall, but carries essentially all of the book's open
calibration findings (five of six major items above). The pattern across
them is consistent: her *behavior* and *dialogue* are almost never the
problem (the audits found zero instances of her claiming or believing she
is exceptional across all 35 chapters); the *narrator* around her keeps
supplying the comparison or the cost she is correctly denied. `02:247` is
the earliest and clearest case and the one most worth fixing.

**Ruth.** Holds. The two-year arc to her realization is well-earned and
well-paced per CAL_31-35, and the chapter-31 confrontation scene that was
audited as having a backwards-reading arithmetic problem has since been
substantially rewritten — closer to right, though a new, smaller version of
the same mismatch is now present (see the footnote above). No open "sounds
like an adult" finding.

**Sam.** Holds throughout, and is repeatedly cited by the audits as the
best-defended character in the book against the AI/Sheldon failure modes —
wrong turns, forgotten details, and flat non-recognition of praise across
every span he appears in (chapters 6-35). No open findings of any kind.

**Kavi.** Holds, with one item to watch: `35:51`, the most explicit
self-knowledge given to any character, judged earned but at "the outer
edge." One voice-consistency (not calibration) discrepancy at `12:73` where
a sheet rule against figurative language is now unambiguously broken.

**Nadia.** Holds completely. Her mechanism — cross-examine rather than
reflect, land the point on someone else, take nothing for herself — is
noted as working in every span she appears in, with no open finding.

**Priya.** No finding in any of the eight audits, in either direction. She
exits the story at chapter 29 (confirmed absent from 31-35, consistent with
her character sheet); nothing flags her as a risk at any point.

**Odile.** No open finding. Appears mainly in the protected chapter-15
intrusion sequence, which the audits read as the standard's own worked
example of rationalization done correctly, and briefly elsewhere without
incident.

**Eli.** Holds, and his turn (`35:82`, "he's very slightly wrong about how
good we are") is the smallest and best-controlled of the seven turns in
CAL_31-35's telling — framed as a fact about an adversary's model rather
than a claim about himself.

**Theo.** Holds. One open, low-severity finding (`29:11`, narrated
professional comparisons). His own turning point is deliberately withheld
from the page entirely, which the audit calls the strongest instance of
House Rule 1 discipline applied to the most tempting possible beat.

**Fen.** Appears only in the character list for CAL_15-18's scope and is
never the subject of a specific finding in any of the eight audits — clean
by omission rather than by a verified pass.

---

## Top ten, ordered by improvement to the book

1. **`02_march_4th.md:247`** — Chloe's unhedged "she's at the top of it,"
   no absorbing beat. Earliest, clearest, most consequential open instance
   of the book's central risk. *(Finding 1)*
2. **`18_fifteen.md:163`** — the narrator delivers Ruth's own argument for
   her. Sharpest surviving case of the book-wide narrator-encroachment
   pattern, with a cheap, on-the-record fix (give the line to Ruth).
   *(Finding 3)*
3. **`30_cleared.md:21`** — the narrator builds the exam-room comparison
   Chloe never makes herself, in the single highest-visibility "does she
   look down on people" scene in the book. *(Finding 4)*
4. **`33_the_other_one.md:151`** — the book's biggest ethical decision, and
   the smallest shown cost; got quieter rather than louder in editing since
   the audit. *(Finding 5)*
5. **`16_thirteen.md:51`** — the Marek fail routed through institutional
   deduction instead of feeling. *(Finding 2)*
6. **`35_nine_minutes.md:51`**, Kavi — earned but at the outer edge of
   explicit self-knowledge; worth one more look before the ending locks.
   *(Most-wanted section)*
7. **`22_the_offer.md:39`** — Kavi via two stacked adult-register similes,
   a half-applied fix from the author's own line notes. *(Finding 6)*
8. **`08_the_asking.md:171` / `10_april.md:157`** — the "sounds like X, so
   she keeps it to herself" construction; mostly defused already, worth
   finishing. *(Finding 8)*
9. **`16_thirteen.md:9`** — the staff-room-voice class summary; low
   severity but the cleanest remaining example of the register (not
   behavior) risk the author named as the priority. *(Finding 7)*
10. **`31_ruth.md`, professor scene** — not one of the eight audits' named
    findings (the text changed too much), but the rewrite meant to resolve
    CAL_31-35's arithmetic complaint has left a smaller version of the same
    problem in place, at the hinge of the book's whole seven-person arc.
    *(Footnote, "Findings closed" section)*
