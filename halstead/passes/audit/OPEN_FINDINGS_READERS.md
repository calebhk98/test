# Open Findings — Reader Reports, Deduplicated

> **Read `../DO_NOT_FLAG.md` before acting on anything in this file.** These are
> agent extractions from the audit round of 2026-08-27, not verdicts. Several
> findings in this batch were checked line by line against the current chapters
> and did not reproduce — including one ranked in a top ten that reads a scene
> as the inverse of what it does, and one built on a quotation that is not in
> the book. The refuted list is at the end of `DO_NOT_FLAG.md`.


Source: BLIND_FULL.md, BLIND_01-12.md, BLIND_13-24.md, BLIND_25-36.md,
WHOLE_BOOK.md, READ_01-09.md, READ_10-18.md, READ_19-27.md, READ_28-36.md,
VOICE_VS_SHEETS.md (10 files; the brief calls them "nine reader reports" —
VOICE_VS_SHEETS is the tenth, a distinct methodology). Checked against
`DO_NOT_FLAG.md` first; checked against the actual chapter files wherever a
report gave a quotable line. Spot-verification, not exhaustive — every
chapter file exists and was grepped for the specific claims below, but I did
not re-read all 36 chapters end to end myself.

**Important context finding, upfront:** several specific quotes cited by
these reports as current problems **do not match the current chapter text**.
Spot-checking the most-quoted "worst sentences" turned up at least five cases
where the flaw described is no longer on the page — either fixed since the
report was filed, or the report was inaccurate to begin with (see the
"Already fixed / not found" list below). Treat every remaining quoted finding
below as re-verified against the live file as of this pass, with the
verification noted inline. Where I could not verify, I say so.

---

## 1. Voice differentiation — the cast collapses into one register

**What it is:** Characters across a 15-year age range and every social class
argue in the same precision-built rhetorical shape (state a claim, qualify
it, land a one-line verdict), and in several specific scenes a character
uses another character's own signed, sheet-exclusive verbal signature.

**Where:**
- General pattern: identical three-clause "and / because / so" cascade used
  by six-year-old Chloe, both parents, Ben the psychologist, Mr. Baptiste,
  Dr. Ammons, and the librarian (READ_01-09, ch. 1–9).
- Chloe and Nadia build an analogy and land a one-line verdict in near-
  identical cadence in ch. 21 (READ_19-27) — "If a store put a sign in its
  window..." vs. "So the form isn't reading the person, it's reading its own
  listing back to itself." **Verified present, current text, ch. 21.**
- Chloe uses Ruth's signed, sheet-exclusive move (dropping the addressee's
  name mid-correction) twice in one scene with Marek, ch. 16 — "I need
  something with your name on it... Marek" / "I can't take this in pencil on
  the back of Ivy's Tuesday, Marek, I need your name on it." **Verified
  present, current text, ch. 16, line 35.**
- Kavi uses the same Ruth-exclusive move in ch. 10 — "You already have all of
  it, Chloe, because his mom came and that was the whole of it... while I was
  standing right there." **Verified present, current text, ch. 10, line 129.**
- Odile's one long, fully-reasoned four-clause argument in ch. 21 breaks her
  sheet's "bare, a number and nothing else" register. **Verified present,
  current text, ch. 21, line 49.**
- Sam hedges twice in three lines in the ch. 24 chat ("i dont think its
  measuring anything" / "its just meant to be fun") against his sheet's one
  absolute rule ("would never hedge about a fact, a plan, or himself").
  **Verified present, current text, ch. 24, lines 211/213.**
- Marek's entire ch. 16 scene argues that the record-keeping requirement is
  conceptually empty ("There is no sheet... a receipt is a different object
  from work... Nothing would [make me hand something in]") — the exact
  "argues the rule is stupid" / "cold monk" failure mode his own character
  sheet forbids by name, twice. **Verified present, current text, ch. 16,
  lines 21/33/43.**

**How many independent reports:** 4 — READ_01-09, WHOLE_BOOK, READ_19-27,
VOICE_VS_SHEETS. Four different methods (line-by-line first read, whole-book
synthesis, first read of a different span, systematic sheet-cross-check) all
land on the same underlying complaint independently, which is the strongest
corroboration in this whole audit.

**Checkable:** Yes, directly. `voice_separation.py` and `dialogue_study.py`
are the scripts built for exactly this question — run them and read the
scorecard. The specific line collisions above are all quote-verified against
the current chapter files.

**Severity: High.** This is the author's own named top complaint (per
CLAUDE.md: "I'm having to go back through to pull it back towards normal
human readers... everyone sounds logical, silent, direct, honest") — 4 of 10
reports independently reach the same verdict, several with exact, still-live
quotes, and one instance (Marek) is a flat contradiction of a binding
character-sheet rule rather than a matter of taste.

---

## 2. Marek's chapter 16 scene contradicts his own character sheet outright

**What it is:** Marek's sheet states twice, explicitly, that he would never
argue a requirement is beneath him or that a rule is stupid — his objection
is that the rule "simply does not reach him," delivered as unbothered
stillness, not argument. Chapter 16 gives him a three-beat philosophical case
that record-keeping is conceptually empty, then has him walk out after making
it — the "cold monk making a principled stand" failure mode the sheet
explicitly names and rules out.

**Where:** Ch. 16 ("Thirteen"), the Marek grading scene. Quotes verified
above.

**How many independent reports:** 1 (VOICE_VS_SHEETS) — but the finding is
a direct, textual contradiction of `_SHEET_RULES.md`'s binding standard, not
a matter of interpretation, and CLAUDE.md states sheet violations outrank
target numbers. One high-confidence, well-evidenced report should carry more
weight here than the "count" alone suggests.

**Checkable:** Yes — reread `characters/MAREK.md` (or wherever his sheet
lives) against ch. 16 lines 21, 33, 43 directly.

**Severity: High.** Same reasoning as above (§1) — a named, binding rule is
being broken in the character's single largest scene, not a background
extra's stray line.

---

## 3. Reading level runs meaningfully above the stated 9th-grade target

**What it is:** Vocabulary stays plain throughout, but sentence architecture
(long multi-clause sentences stacked on "and / but / which / so," fifty-plus
words with several deferred subordinate clauses) sits closer to adult
literary fiction than 9th-grade prose. One report gives a specific
chapter-level number: chapter 10's Flesch-Kincaid grade (8.0) is the highest
in its span — meaning a chapter for a six/seven-year-old character reads
harder by the numbers than chapter 18, where she's fifteen, which cuts
against the book's own stated design that the prose should get harder as she
ages.

**Where:** General, cited with specific examples from ch. 12 and ch. 34
opening paragraphs (WHOLE_BOOK); specific F-K numbers for ch. 10 (8.0) vs.
ch. 18 (6.9) (READ_10-18); BLIND-series commentary repeatedly independently
estimates "7th–9th grade... pulled up a notch," rising effectively (if not
mechanically) to "asking a 9th grader to track cryptographic key derivation
and acoustic triangulation" by the middle third.

**How many independent reports:** 3 direct (WHOLE_BOOK, READ_10-18, and the
BLIND-series' repeated by-ear estimate across BLIND_01-12/13-24/25-36, which
is one methodology run three times rather than three independent methods).
Call it 2 independent methodologies in agreement.

**Checkable:** Directly — this is exactly what `prose_grade.py` measures.
Run it and check whether the chapter-by-chapter curve actually rises with
Chloe's age the way the house design intends, and specifically compare ch.
10 against its neighbors.

**Severity: High.** This is the single measure most directly on-point for
the author's stated goal (9th-grade readers) and it is a script this repo
already runs — if `prose_grade.py`'s scorecard shows the same non-monotonic
curve READ_10-18 describes by ear, that is a concrete, fixable finding.

---

## 4. Escalating "outclass armed adults" pattern, same rationalization each time

**What it is:** Three set pieces, escalating in scale, all resolved the same
way: a child or very young adult defeats a disproportionate number of trained
or armed adults, and the book's own characters supply the identical excuse
each time — "they were bad at it." Four twelve-year-olds subdue four armed
adult operators (ch. 15, later confirmed real in ch. 29); four teenagers
disarm seven armed muggers in 22 seconds with no injuries (ch. 20); one
twenty-two-year-old defeats seventy-five armed operatives virtually unharmed
(ch. 36).

**Where:** Ch. 15/29, ch. 20, ch. 36.

**How many independent reports:** 4 — WHOLE_BOOK (names the pattern
explicitly as "three times, escalating, is the pattern a Mary-Sue read would
point to"), BLIND_25-36 end-of-span assessment, BLIND_FULL closing section
("Mary Sues?" question), READ_28-36 (more forgiving — argues ch. 36 is
"mostly believable... because the book pre-pays part of it," but still flags
the pattern and specifically notes the characters pre-empting the objection
in dialogue rather than answering it).

**Checkable:** Not machine-checkable (this is a story-design judgment, not a
countable prose feature); the three instances themselves are simple to
re-read and compare (ch. 15/29, ch. 20, ch. 36).

**Severity: Medium.** Real and multiply corroborated, but it's a structural/
craft-taste question for the author to weigh, not a rule violation — three of
four reports treat it as a genuine weakness, one treats it as mostly earned.
See also the Disagreements section below.

---

## 5. Recurring prose tics, several confirmed by direct count

**5a. "Considerable" cluster in Sam's two Army chapters.** "Considerable /
considerably / a considerable while" appears 5 times in ch. 25 and 4 times in
ch. 26, and 0 times in the very next chapter (27), which is not Sam's. Report:
BLIND_25-36. **Verified by direct grep count** — 5 / 4 / 0, matching the
report closely (it estimated "four" in each; actual is 5 and 4). Checkable
via `tics.py` or a direct grep; this reads as a real, localized author tic
tied to one character's chapters rather than noise.
**Severity: Low** (cosmetic, easy find-and-vary fix).

**5b. "A second time / a third time" repetition device, corpus-wide.**
WHOLE_BOOK says "I stopped counting past twenty." **Verified by direct count:
26 instances across 18 of the 36 chapters** — so the magnitude claim holds up
(not inflated), and it is a genuine recurring narrator habit, not a
per-character tic. **Severity: Low-medium** — worth a `tics.py` line item;
harmless in small doses but this is a lot of repetitions of the same
narrative gesture (someone re-reading/re-counting something to make sure).

**5c. Object-as-punctuation habit (mug turned a quarter turn, papers
squared, a pen recapped).** WHOLE_BOOK claims this happens to "every single
adult and child in the book, at every age." **Partially verified: real but
overstated** — direct grep finds "quarter turn" in 4 chapters and "squared"
variants in roughly 2, not universal. Treat the underlying observation
(recurring physical fidget-as-characterization gesture) as real; treat "every
single character, every age" as an inflated magnitude per the report's own
prose, not a literal count. **Severity: Low.**

**5d. Ruth's name-drop signature used 3–4 times in one exchange (ch. 33).**
VOICE_VS_SHEETS's own signature note says 3–4 uses across the *whole book* is
already at the line before it reads as a catchphrase. **Verified: 3 direct
"Eli"-suffixed lines found in the flagged exchange** (ch. 33, lines 27/31/35)
— close to, not quite, the "four in one exchange" claim, but still a real
local cluster of her signature move. **Severity: Low.**

---

## 6. House Rule 1 (named emotional states) — mostly already fixed, one live example

Multiple reports flagged specific named-state violations. On verification
against current text:

- "annoyed" opening ch. 15's intrusion sequence — **NOT FOUND in current
  text.** Already fixed or the report was inaccurate.
- "annoyed" in Theo's ch. 29 flashback — **NOT FOUND in current text.**
  Already fixed.
- "By Thursday afternoon she has stopped being angry and started being
  interested" (ch. 14) — **NOT FOUND in current text.** Already fixed.
- "proud" in ch. 31 — **NOT FOUND in current text.** Already fixed.
- Ch. 33's closing paragraph narrating the emotional cost of Chloe's biggest
  moral risk instead of dramatizing it ("What that costs her she works
  through once, on the drive home... the thought ends in about as long as it
  takes a light to change") — **VERIFIED STILL PRESENT**, ch. 33, line 151,
  essentially unchanged from the quote in READ_28-36.

**How many independent reports:** READ_10-18 and READ_28-36, both quoting
specific lines. Most of what they quote is already gone; one instance
(ch. 33) is not.

**Checkable:** `tics.py` and `style_report.py` both scan for this
construction directly; `grade.py` rolls it up.

**Severity: Low** as a body of findings (mostly stale/fixed already), but
**the one surviving instance (ch. 33) is Medium-High**, because it lands
exactly on the chapter's biggest stated stake (Chloe's federal clearance
being spent on a felony) — this is precisely the shape House Rule 1 exists to
catch, at the highest-leverage moment in the span it appears in.

---

## 7. Word-count clustering at the chapter-length floor, last four chapters

**What it is:** Chapters 33–36 all land within a narrow band just over
whatever the house word-count floor is — READ_28-36 reports 2,007 / 2,024 /
2,026 / 2,025 words and ties chapter 35 specifically to a documented pass
history ("Expand chapter 35... from 422 words to ~2,057... trimmed to 2,026")
that contradicts a brief describing that same chapter as "deliberately short,
under the word floor, and left that way."

**Verified independently** with a plain `wc -w`: 1,997 / 2,024 / 2,025 /
2,012 for ch. 33–36 respectively — different exact numbers than the report
(different counting method — the house scripts likely count words
differently than `wc -w`), but the same finding: **all four chapters cluster
inside a 30-word band, which is not coincidental variation.**

**How many independent reports:** 1 (READ_28-36), but independently
reproduced by this pass with a different counting method, landing on the
same conclusion.

**Checkable:** `check_edits.py` (word counts are exactly what it reports) —
rerun it and look at the last four chapters together, and check the pass
history for chapter 35 specifically for whether "left deliberately short" is
still an accurate description of any brief or comment anywhere.

**Severity: Medium.** Not a defect a reader would notice, but it is direct,
current-file-verified evidence that a pass optimized to a number instead of
to the scene on four consecutive chapters, which is exactly the failure mode
CLAUDE.md warns "gets the number given back."

---

## 8. Chapter 36 has zero section breaks against every neighboring chapter's 2–6

**What it is:** Every other chapter in the closing run uses 2–6 section
breaks; chapter 36 uses none.

**Verified independently:** ch. 34 and ch. 35 both show 3 section breaks by
direct grep; ch. 36 shows 0. Confirmed exactly as reported.

**How many independent reports:** 1 (READ_28-36), which itself notes this
may be a deliberate choice (one continuous transcript, 41% chat by word
count) rather than a defect, and asks the author to confirm intent rather
than treating it as an error.

**Checkable:** `style_report.py`'s section-break count, directly.

**Severity: Low** — flagged by the report itself as possibly intentional;
include only so the author can confirm it was a choice, not drift.

---

## 9. Foreign Service age math requires the reader to do work chapters 23 and 30 don't do for them

**What it is:** Chapter 23 sets up, at length, that Chloe cannot be *sworn
in* to the Foreign Service before 21, with a distinct "training year" after
the age-20 floor. Chapter 30 then has her sit the exam at 20 and start "the
job" in January, turning 21 the following August — without the text
reminding the reader that "the job" here means the training year, not the
sworn commission chapter 23 built suspense around.

**Verified:** the relevant lines exist as described in both chapters (ch.
23: "the training year that sits behind the floor," "twenty-one to be sworn
in"; ch. 30: "the job starts in January. She turns twenty-one in August").
The distinction is present in ch. 23 in one clause, seven chapters earlier,
and not restated in ch. 30 itself.

**How many independent reports:** 1 (READ_28-36).

**Checkable:** Reread ch. 23 and ch. 30 back to back; this is a
comprehension/signposting question, not a hard date contradiction — the
dates check out under the "job = training year" reading, but nothing in ch.
30 confirms that reading is the intended one.

**Severity: Low.** A clarity gap, not a contradiction — one added clause in
ch. 30 (e.g., "the training year, not the badge yet") would close it.

---

## 10. Dangling setups that were given real narrative weight and then dropped

Several threads are introduced with enough weight that a reader expects a
return, and don't get one. Distinct from the ending's *deliberate* large-plot
non-resolution (funder, the seventy-five, the prisoners — see Dropped list),
these are smaller, more local setups:

- **Marek's fail is framed as a real, years-long moral cost to Chloe, and he
  then resurfaces for a decade unaffected**, feeding her practice questions
  with no visible consequence ever collected. Reports: BLIND_13-24,
  BLIND_FULL (ch. 16/19 entries), WHOLE_BOOK. **3 reports.**
- **Dr. Sandoval's NDA-adjacent research request (ch. 18) is never followed
  up** — what she wanted, what Chloe did with the request, gone. Reports:
  BLIND_13-24, BLIND_FULL. **2 reports.**
- **The Aurel rumor (ch. 18) is introduced, costs Chloe a real behavior
  change (avoiding a staircase), and never resolves or gets an anchor** — it
  even resurfaces once, isolated, in the ch. 24 chat with no other context in
  that span. Reports: BLIND_13-24, READ_19-27. **2 reports.**
- **Iyad's compulsive tracking/gossip habit, an established running trait,
  simply stops appearing in the last third with no closure.** Report:
  BLIND_25-36 end-of-span list. **1 report.**
- **The Chloe/Nadia/Sam "always between them at the table" detail (ch. 34)
  is introduced with real narrative weight two chapters from the end and
  never returned to.** Report: READ_28-36. **1 report.**
- **The counterintelligence irony of chapter 29 is never noticed by anyone
  in the story:** the same government unit that has watched Halstead for
  over a decade hands its file to Theo, who is himself one of the
  ninety-one tracked graduates, right as another graduate (Chloe) is cleared
  into the very agency that employs him. Report: READ_28-36. **1 report,**
  but specific and easy to check by rereading ch. 29 and ch. 30 together.
- **Chloe's federal clearance is dramatized as the single largest personal
  risk in the friend group's late-book felony, and then produces zero
  visible cost or friction anywhere on the page** — contrasted explicitly
  against Theo (two-handed laptop closes), Nadia (a counted till), and Eli
  (checked locks), all of whom show some physical tell of the risk. Reports:
  BLIND_FULL closing section, WHOLE_BOOK, READ_28-36 ("hardest to believe").
  **3 reports.**

**Checkable:** Not script-checkable; these are read-and-confirm items — does
each thread get a line anywhere later in the manuscript that a plain-text
search would find? Search each character/topic name across `chapters/*.md`
to confirm before deciding whether it's a gap or something this pass missed.

**Severity: Low-Medium each**, individually; worth a single pass to decide
which (if any) deserve one closing line, since several already have real
setup investment sitting unpaid.

---

## Items already raised by DO_NOT_FLAG as "still open, not ruled" — re-surfaced here for visibility, nothing new added

- **"Furious" (ch. 5, line 65) and "relieved" (ch. 7, line 113) as named
  states** — both verified still present verbatim in the current text. Per
  DO_NOT_FLAG, the author has asked to look at these specifically and wants
  new reasoning, not a repeat of the existing objection. This pass has
  nothing new to add beyond what's already on record (two agents have raised
  it; both are structurally identical to the "state a feeling right after
  already showing it physically" pattern flagged elsewhere in this doc as
  fixed everywhere else it appeared) — flagging only so it isn't lost, not as
  a new finding.
- **Amberg's long job-offer speech (ch. 22)** — DO_NOT_FLAG lists this as
  still open. On verification, the specific sentence READ_19-27 quotes as
  "the worst sentence in the book" (a ~145-word run beginning "Everybody on
  staff signed something close to this same sheet at some point...") **does
  not match the current text.** The live version (ch. 22, line 29) is
  roughly a third the length and reads as plain, itemized dialogue ("Four
  things, then... Everybody on staff signed something close to this same
  sheet, and nobody has ever come back to this office asking for different
  terms"). This appears to already be fixed, or the report is describing an
  older draft — either way, the specific complaint (over-literary,
  145-word single sentence) is not reproducible against the file as it
  stands. Recommend the author re-examine only the current, shorter version
  when they get to this item, not the version quoted in the report.

---

## Disagreements between reports

1. **Is chapter 36's Priya-vs-75 believable?** BLIND_FULL, BLIND_25-36, and
   WHOLE_BOOK all treat it as the point where the book's credibility
   "finally breaks" or becomes "comic-book scale." READ_28-36 disagrees
   directly, arguing it's "mostly believable, and better than a first read
   suggests" because the book pre-pays the capability (four kids vs. four
   operators in ch. 15/29; seven muggers in ch. 20) and because the chapter
   itself downgrades the threat (extraction not combat, a hand that won't
   close, two prisoners rather than a clean sweep). **What would settle it:**
   this is a craft-judgment disagreement, not a fact one — there's no script
   for it. The one semi-objective angle: READ_28-36 also notes the chapter
   has the characters themselves pre-empt the exact objection a skeptical
   reader would raise ("so either they are lying about who they work for, or
   somebody has spent a lot of money on people who are not very good at it")
   without answering it — which either reads as the book being self-aware
   (READ_28-36's read) or as the text noticing its own strain and trying to
   defuse it in advance (the other three reports' implicit read). The author
   is the only one who can settle which effect was intended.

2. **Does the ch. 20 mugger fight (and its escalation pattern) work?**
   READ_19-27 says it "mostly still works," and separates out two fixable
   local defects (an attribution seam, the slur) from the choreography
   itself, which it praises. WHOLE_BOOK and BLIND_FULL treat the same scene
   as the first real crack in the book's plausibility, independent of any
   attribution issue. **What would settle it:** the attribution-seam
   complaint is independently checkable and, per this pass's verification,
   **does not currently exist in the text** — ch. 20 lines 81/83 show Sam's
   and Ruth's lines both fully and normally attributed. So that specific
   half of READ_19-27's argument no longer applies; the broader
   plausibility disagreement remains a judgment call for the author.

3. **Is the withheld/unresolved ending a strength or a structural failure?**
   Every report agrees the plot mechanically stops rather than resolves —
   DO_NOT_FLAG already rules this itself as intentional and off-limits for
   "fix this" proposals. But reports genuinely split on whether the
   *character* arcs land well enough to carry an unresolved plot: WHOLE_BOOK
   and BLIND_FULL argue the character throughline (nobody who was raised
   only against each other can know their real worth) lands and mostly
   redeems the plot non-ending; READ_28-36 argues the character ending is
   real and warm but still closes on the *wrong* character's smaller
   question (Priya's mare) instead of anything that touches the book's
   actual open question, and that a different last line (Ruth's arithmetic,
   or the group's own "why seventy-five") would have closed the book's real
   question instead of one member's private one. **This is explicitly
   fenced off by DO_NOT_FLAG from "fix the ending" proposals** — surfaced
   here only as a disagreement about whether the *last line specifically*
   (not the plot) is the right closing image, since that's a narrower,
   possibly still-open craft question distinct from "resolve the founder."

---

## Findings dropped, and why

Per `DO_NOT_FLAG.md`, ruled deliberate by the author — not reported above
even though multiple reviewing agents raised each of these:

- Ruth's surname Aymar shared with another student in the same year
  (raised independently across BLIND_01-12 methodology's predecessor
  passes per DO_NOT_FLAG's own count of "three separate agents" — not
  re-litigated here).
- Meg and Dave (the parents) sounding similar to each other.
- Chloe calling the parking-lot muggers "retarded" (ch. 20) — raised by
  nearly every report in this batch (BLIND_FULL, BLIND_25-36, WHOLE_BOOK,
  READ_19-27 all flag it, several at length, one calling it "the ugliest
  instance" in the book) — **all dropped per DO_NOT_FLAG's explicit ruling**
  that this is calibration (how a ~100 IQ opponent reads to her), not
  authorial oversight.
- "Finishes first, checks it, waits" recurring — deliberate repetition.
- Chloe asking about Halstead across ch. 3/7/8 — deliberate, and the three
  instances are not equivalent per the author's own note.
- The accumulating "and X, and Y, and Z" list device — never flag.
- Contradictory accounts of why Owen left — the rumor mill working as
  intended.
- "She is relieved to find it still works like it worked in first grade"
  (ch. 7) — the author's own dictated sentence; stays regardless of the
  Rule-1 argument against it (raised again in this batch by READ_01-09,
  which calls it the single worst sentence in its span — dropped per
  standing ruling, not re-argued here).
- The book's ending not resolving the founder, the seventy-five, or the
  prisoners — known and intended; not treated as a defect above (see
  Disagreements §3 for the narrower, not-yet-ruled question about the
  specific *last line* choice, which is surfaced separately rather than as
  "fix the ending").

Also dropped, as already fixed on direct verification against the current
manuscript (not defects the author needs to see again):

- The "annoyed" named-state opener in ch. 15's intrusion scene (READ_10-18).
- The "annoyed" named-state in Theo's ch. 29 flashback (READ_28-36).
- "By Thursday afternoon she has stopped being angry and started being
  interested" (ch. 14) (READ_10-18).
- The "proud" named state in ch. 31 (READ_28-36).
- The doubled, empty section-break in ch. 15 ("two `________________` lines
  in a row with nothing between them") — checked directly; the current file
  has exactly one break before and one after the inserted "DEFENSIVE WATCH"
  document, which is normal bracketing, not a doubled seam (READ_10-18).
  Either fixed or inaccurate as originally reported.
- The unattributed double-quote seam in ch. 20 ("Hang on." / "Let me have
  this one." with no dialogue tag) — checked directly; both lines in the
  current file carry full, normal attribution ("Sam says," "she says").
  Either fixed or inaccurate as originally reported (READ_19-27).
- Amberg's ~145-word run-on job-offer sentence in ch. 22 — checked directly;
  the current line is a third the length and does not exhibit the flaw
  described (READ_19-27). Cross-referenced in the "still open" section above
  since DO_NOT_FLAG hasn't ruled on Amberg's speech generally, only noting
  this specific quoted version is stale.

Also dropped as inflated-magnitude claims that did not hold up on a direct
count (per this pass's own verification, not the author's ruling):

- Priya's "which is [evaluative tag]" tic in ch. 36, claimed as three uses —
  direct search found only **one** genuine instance; the other two quoted
  "instances" use different phrasing ("thats the bit," "about what i
  expected") without "which is" at all (READ_28-36).
- Ruth's "eli" name-drop claimed as four uses in one ch. 33 exchange — found
  **three** in the flagged passage, not four (VOICE_VS_SHEETS). Still a real
  local cluster; just not the exact count claimed.
- The object-as-punctuation gesture (mug turns, squared papers) claimed as
  present in "every single character... every age" — real but narrower on
  direct count (4 chapters for "quarter turn," roughly 2 for "squared"
  variants) (WHOLE_BOOK).

Praise, not reported as findings (per instructions): the emotional honesty
of the Ch. 9 bargaining scene, the Ch. 31 Ruth chapter's construction, the
Ch. 24 chat-format shift, the essay-writing arc, the group-project
interdependence in ch. 17, Amberg/Hearn/Voss as consistently excellent
teacher characters, the "why each character chooses their post-graduation
path" material, and Nadia/Priya/Sam's individually well-differentiated
motives — all repeatedly and specifically praised across multiple reports,
none of it reported above as a finding needing action.

---

## Top ten, ordered by expected improvement to the book

1. **Voice differentiation collapse (§1).** The single most-corroborated,
   most fixable, most on-target-with-the-author's-own-stated-frustration
   finding in the whole batch. Four independent methods agree; several
   exact, still-live line collisions are handed to the author already
   quote-and-location-ready. Fixing this raises the ceiling on every other
   scene in the book, because it's the difference between an ensemble and
   one voice wearing name tags.

2. **Marek's ch. 16 contradiction of his own character sheet (§2).** Small
   in page count, large in principle — it's the one item in this whole
   audit that is a flat, binding-rule violation rather than a matter of
   degree, in his single largest scene. Fast to fix (the report even
   supplies the fix: keep the stillness and the outcome, cut the two lines
   that turn it into an argued stance), and it stops the character sheets
   from being decorative.

3. **Reading-level curve (§3).** Directly, mechanically checkable against
   the author's own stated audience, with a specific, concrete anomaly
   already identified (ch. 10 reading harder than ch. 18 despite the
   character being eight years younger). `prose_grade.py` will either
   confirm or dismiss this in one run.

4. **Ch. 33's undramatized cost of Chloe's biggest moral risk (§6).** One
   sentence, one chapter, sitting on the single highest-stakes moment in the
   back third of the book (a federal clearance spent on a felony). This is
   the cheapest fix on the list with real payoff — dramatize it instead of
   narrating it closed.

5. **Word-count clustering, chapters 33–36 (§7).** Confirmed independently
   with a different tool than the original report used. Worth the author's
   attention specifically because it's evidence a pass optimized to a
   number on four consecutive chapters — exactly the failure mode CLAUDE.md
   warns against, and the kind of thing that's invisible to a casual reread
   but obvious the moment someone runs the numbers.

6. **The escalating "outclass armed adults, same excuse" pattern (§4).** Not
   a line-level fix, but worth the author's attention because it is the
   most load-bearing craft complaint that four separate reports converge on
   from different angles (three call it a real problem, one calls it mostly
   earned) — a five-minute decision by the author (are three escalating
   instances of the same resolution the point, or the drift?) settles a
   disagreement no script can.

7. **Dangling setups with real invested weight (§10).** Individually minor,
   collectively a pattern: Marek's fail, the Sandoval NDA, the Aurel rumor,
   Chloe's frictionless clearance exposure. None require a plot change —
   each needs at most one sentence somewhere later confirming the cost was
   real, or one sentence explicitly closing the thread on purpose.

8. **"Considerable" tic in Sam's Army chapters (§5a).** Trivial to fix,
   confirmed by direct count, and it's the kind of thing `tics.py` should
   already be catching per the house measuring table — worth checking why
   it wasn't.

9. **Chapter 36's zero section breaks (§8).** Likely intentional, but cheap
   to confirm — one line from the author ("yes, on purpose, it's one
   transcript") closes this permanently.

10. **The stale-quote problem itself.** Not a manuscript defect — a process
    one. Multiple "worst sentence in the book" citations across these nine
    reports (the Amberg speech, the ch. 20 attribution seam, the doubled
    section break, several named-state examples) turned out not to match
    the current file. That's good news about the manuscript, but it means
    at least one of these reports was working from a stale snapshot or
    reasoning without rechecking the live file. Before the next audit round,
    it's worth confirming what state each report actually read against, so
    findings don't keep circulating after they've already been fixed.
