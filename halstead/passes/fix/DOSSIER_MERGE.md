# DOSSIER.md: what went in, what stayed, what was wrong

One document at `DOSSIER.md`, built from the four reviewer dossiers in
`passes/review/Dossiers.md` merged with `passes/CALIBRATION_AUDIT.md`,
`passes/HOUSE_RULES.md`, `characters/_CALIBRATION.md`,
`characters/_DIFFERENTIATION.md`, `characters/_ALLOCATIONS.md`,
`CURRICULUM_GRID.md`, `THEY_ARE_CHILDREN.md` and `SYNOPSIS_FROM_TEXT.md`, then
checked line by line against `chapters/`.

`python3 verify_citations.py DOSSIER.md` reports 15 quotations checked and 0 not
found. That script only sees double-quoted strings on lines carrying a chapter
citation, so every blockquote in the file was additionally checked by hand
against `chapters/*.md` alone: 31 quoted fragments, 0 misses. `chapters/` was
used rather than `HALSTEAD.md`, which is a build artefact and is behind the
chapters in at least three places (see section 3 below).

No em dashes, no curly quotes, blank line between paragraphs, no trailing-space
hard breaks. Nothing outside `DOSSIER.md` and this report was touched.

---

## 1. What was taken from the reviewers

**The architecture.** Their organisation is better than anything we had and the
new document uses it end to end:

- **The scale misconception as the opening move.** Section 1 is their
  outsider-assumption versus reality contrast, rebuilt as a two-column table
  with our verified figures in the right-hand column.
- **The three developmental ages** as the spine of the psychology, now section
  4, with our chapter ranges written into the table.
- **"Why the room exists"** from their fourth dossier. This is the strongest
  single passage in their material: the normal one-in-thirty-thousand outcome,
  the inversion, and the line that the class rank is manufactured rather than
  concealed and is the load-bearing wall of the institution. Kept nearly whole,
  with the arithmetic changed to ours.
- **The misconceptions section** as a standing list of wrong readings to test a
  draft against, now section 7, with two of their entries corrected and three of
  ours added.
- **The one-paragraph summary**, now section 8, rewritten with our numbers.
- **Their calibration test** ("she dumbed it down, hiding her contempt" is
  wrong; she translated) folded into section 7, because it is the fastest
  diagnostic in either document.
- **Their two permanent blind spots** (individual prediction, and the upper
  tail) in 4.4, because both survive the calibration and both give a writer
  honest surprise to work with at any age.
- **Their "build your own graduate" advice** rebuilt as section 6, which is now
  a much bigger section for the reason given below.

**One ruling in their favour.** Sinclair is a former Navy SEAL who served in
special operations. Their dossiers are right about this and it is now stated in
section 2. The manuscript itself only puts an unnamed SEAL on the faculty page
Meg reads in ch 3 and never attaches it to Sinclair, so the dossier states the
ruling and quotes the faculty-page line, without claiming the manuscript makes
the connection.

---

## 2. What was kept from ours

- **`CALIBRATION_AUDIT.md` governs section 4.1 outright.** The Vulcan / Sheldon
  / AI / mini-adult list, "intelligence changes what she can do, it does not
  change what she wants or how much things hurt", the ban on modesty as well as
  arrogance, and above all the rule that contrary evidence gets rationalised
  rather than absorbed. The reviewers have the belief but not the mechanism, and
  the mechanism is what a writer actually needs.
- **`THEY_ARE_CHILDREN.md`** supplies 4.2 entire: children are social,
  talkative, silly and unfair to each other; their morals are a child's morals,
  not an operative's; and the correction that fear decays as the years at the
  school accumulate, so eight and sixteen are different settings. None of the
  four reviewer documents has any of this, and without it the childhood scenes
  come out as small adults.
- **`HOUSE_RULES.md` rule 1** is in the writing checklist as item 2: the scale
  lives in lists and asides, a skimming reader should undercount, and a passage
  that explains the scale is the defect rather than the cure. The reviewer
  documents actively encourage the opposite.
- **`characters/_CALIBRATION.md`** supplies the enrolment curve, the geography
  (one in thirty thousand, about a hundred and twenty per birth year, two per
  state, no two students from the same county), the teachers (world leaders,
  research is the job, no wounded backstories, and they never let a student know
  they are exceptional), Owen at about 140, and the rule for writing a weakness
  as a genius outperformed by ninety other geniuses.
- **`CURRICULUM_GRID.md`** supplies the structure of section 5: ten one-hour
  blocks, six permanent tracks, two rotating slots, the compulsory afternoon and
  the unrecorded one, the hidden ramp (fixed standard, shrinking taught hours),
  the no-credentials rule, and the three different kinds of "bad at" that the
  book uses the same words for. That last one is the single most useful thing we
  have that the reviewers do not.
- **`_DIFFERENTIATION.md` and `_ALLOCATIONS.md`** supply the whole of section 6.

### On the flattening

The brief asked whether the dossier describes the cohort as a type where it
should be describing nine people. The reviewers' documents do this everywhere:
all four describe a single graduate and then attach a specialism list. Section 6
now runs the other way. It states the shared baseline as eight bullets and says
that is the whole of it, then gives the axes that vary: sentence shape (nine
exclusive slots), how each one disagrees, who hedges (only Theo) and who asks
questions, who is allowed invented images (Chloe, plus Sam's deflating
literalism and Priya's animal comparisons, nobody else ever), and then the axis
that matters most and that no reviewer document has at all, which is that no two
of them have the same relationship to rank. Chloe measures constantly and keeps
expired readings forever; Priya is indifferent to it; Odile cannot register it;
Sam wants the test made harder; Kavi pre-empts praise; Ruth goes and finds the
denominator. Their ethics get their own subsection for the same reason: Ruth
arguing for the untraceable sedative and losing, Nadia refusing to let Eli near
the registered agent, Theo refusing for nine days, Ruth losing the argument
about requiring a reason on the stop clause. Those are four different moral
temperaments, not one.

Priya is flagged explicitly as the proof that the school does not produce a
uniform speech register, since she is the one character who runs on.

### On the naivety-as-weapon material

Their strongest section and the one most likely to break the book, so it is
scoped three ways and the scope is unmissable:

1. Section 4 opens with a bold instruction to read the scope before the content,
   and the three-age table carries the chapter ranges: **chapters 1 to 23**,
   **chapters 24 to 36**, and **not in the book**.
2. Section 4.4 opens by saying everything in it is outside the manuscript and
   that applying it to anyone under about twenty-two will break the book.
3. Section 7's last misconception entry points back at 4.4.

It also draws the line the reviewers do not draw, which is the one that makes
both halves true at once. **They can lie about facts and intentions from
childhood, and they cannot lie about their own level until they know their own
level, which is not until twenty.** Chloe at twelve running a decoy in pyjamas
and Nadia at sixteen cloning a badge are tactical deceptions, taught and scored.
The adult mask is a lie about capability, and a lie about capability needs a
self-model to lie about. The dossier adds one more brake: Chloe is bad at acting
and says so while doing it, so competence at deception is not uniform across the
cohort either.

---

## 3. Every factual error corrected

### From the reviewers' text

| Their claim | The manuscript |
| --- | --- |
| 150 recruited, or 90 enrolled of a top 150, or 800 students, or "top 150 IQs born in the US each year" | About 120 children a year sit near 160 nationally, roughly two per state. The school takes about a hundred a year and grows with Chloe's cohort: about 200 around third grade, close to 1,000 in her last year. The 800 is the number on the grass at graduation, behind 91 who are graduating |
| Cohort of 90 | 90 in the early chapters, 91 from ch 19 on. 91 graduate |
| "They sit the actual state Bar Exam at age 16" | The school's own paper, two days, six hours each, written, marked and proctored by the seven teachers who set it. Chloe tells a background investigator it is accredited nowhere and would not hold up in an actual court |
| Eleven teachers wrote and mark the bar | Seven |
| Chloe passes the bar at 16 | She fails at 16 by four points of two hundred, 39 of the year fail with her, and she passes the retake at 17 by twenty-two |
| Chloe turns down $135k at 18 | At 17. The offer is April 2023 and she turns eighteen that August |
| Chloe graduates at 18 | At 17 |
| Chloe joins the Foreign Service at 21 | She sits the exam three weeks after turning 20 and starts the job in January at 20 |
| Chloe writes 6,000-word blog posts at 20 | She starts the blog at 19, in September 2024 |
| "Chloe hacking government-grade encryption at twelve" | Kavi breaks a consumer handset's AES-256 pairing at twelve, in four seconds of compute, because the pairing code was left on the six-digit default. Chloe's break is the group chat at thirteen, in six days, through the network's connection records rather than the cipher |
| Chloe breaks the chat in nine days; the cover traffic mimics 140 machines | Six days; 160 machines |
| Sam fights off 7 armed muggers at 12 | June 2022. Chloe, Ruth and Nadia are sixteen; Sam is about a year older. Sam takes all seven alone in twenty-two seconds while the other three go over a fence onto a loading dock |
| Sam scores 40/40 marksmanship, "unheard of in the Army" | He hits forty of forty. It is the first the company commander has signed for in two cycles |
| The captain has been in eleven years | Sixteen |
| Sam's line: "My accuracy runs about forty percent" | "My accuracy runs forty percent" |
| Nadia confronts four armed men at 20 | She is eighteen, and says so in the room. The manuscript does not arm the four men. What is on the page is a locked door, a photographed number plate read aloud twice, and three words with sweetheart on the end of them |
| Nadia interviews 41 people, 39 fail; or 400 people | She meant to sit down with twelve that year and sat down with thirty-one. The take-home was made easier twice, down to something she would have handed a twelve-year-old at Halstead, and the pass rate is still under a third |
| Nadia's company makes a diagnostic reader for independent mechanics | It replaces the resume: short tests build a profile, and the thing fills in and sends the applications. Eleven months old, four people besides her, three rooms over a laundromat |
| Priya's ambush at 21 | October 2026. She is in Chloe's cohort, so twenty or twenty-one; the manuscript does not give her age. The dossier says "three years out of school" |
| Priya "fights off 75 armed operatives, defeated them all" | She gets through the line about thirty in, is hit with a tranquilliser dart on the third attempt, and gets out with a hand that will not close and two prisoners. She did not defeat them |
| Priya is 64th of 91 and "bottom third" | Correct, and it is her own line. Kept |
| Eli finds a nine-minute gap in his own surveillance at 20 | The nine minutes are outages in the worm, three of them over six weeks, in mid-2026. Eli is about twenty-one |
| Eli builds a worm to penetrate government systems at 19 | The first worm, Nov 2025 to Feb 2026, follows the money. The second, mid-2026, targets the unit holding the file. Eli is twenty and then twenty-one |
| Ruth's professor: four tries against two | Five tries |
| Chloe's essay: an eleven-line note about hedging in three places | A half-page note: twice on page eight, once on page twenty-two, and the whole conclusion. Her complaint is that she put those hedges in on purpose and they were the only two in twenty-eight pages |
| "Nine admissions offices wrote back asking for the real transcript" | Correct. Kept |
| Ruth "collects national statistics" and Chloe guesses ninety percent | The ninety is Sam's guess. Kavi says 85ish, Theo 70. The figures are 25 percent, 21 percent below sixth-grade reading, about a third for three quarters minus one half |
| The government has tried to collect against the chat eleven times | The standing line has been rewritten at least fifteen times, redated each year |
| "Chloe explains why clouds are the ocean going somewhere else" at seven | She is six, in first grade, and she takes the sentence down to one word rather than saying it |
| "Ruth doesn't want to use traceable agents because it's rude" | She argues for it and loses. They use the fast traceable agent, and *traceable agent selected* goes on the scoring sheet as a listed failure. She then counts the men's respirations every two minutes |
| The 4 a.m. Watch: they were frightened / it was a real attack they knew about | They believe it is a scored drill. The first question anybody asks is whether it is one, Ruth's reading is that the intruders are almost certainly actors with a default pairing code, and they argue about their own grade in front of the men. That it was real is something Chloe learns eight years later, in ch 32 |
| Chapter numbering throughout their summaries | Renumbered against the current 36 chapters. Ch 25 is "Forty Targets", not "Ten Targets", and the qualification is forty pop-up silhouettes |
| Their combined Chloe quote about the $135k offer | Two separate speeches in ch 22, joined. Neither is quoted in the merged form |
| The school runs "age 7 to 18, eleven years, ten classes per day" from the start | Ten blocks a day is the mature form. Seven hours at seven, eight rising to nine at eight, eight academic plus two afternoon from nine |
| "Ten pages a week from age 13" / "at age 13 they write one per week" | The ten pages start at ten, with Hearn |
| Founded 2008, roughly 800 students, first graduating class 2023 | Founded about 2008 and first class 2023 are right. The 800 is corrected above |
| Halstead is a "shelter" the students are grateful for and the school is right to have built | Kept as the book's argument, but the dossier does not editorialise it as a verdict. The book never says what the school is for, and the dossier says so |

### Errors that came from our own reference documents

These were carried into the draft from our files and corrected against
`chapters/`, so they are also live defects in the sources named.

- **`CURRICULUM_GRID.md`** says the bar at sixteen "is the only external exam any
  of them sits". It is not external. Ch 19 and ch 30 both make it the school's
  own, with no standing anywhere.
- **`CURRICULUM_GRID.md`** lists poker at real stakes, blindfold chess and go, the
  lost-position drill, navigation with a map and no clock, and fencing by sound.
  None of these appear in `chapters/`. The grid marks proposed items in plain
  text, which is easy to lose when reading it as a fact source. They are out of
  the dossier.
- **`CURRICULUM_GRID.md`** gives the fighting numbers as 31 at ten, 38 at twelve,
  45 at fourteen, 41 at fifteen. The manuscript gives 4 seconds on day one at
  ten, 11 by that June, 24 at twelve and thirtieth of ninety, 50 on a good
  Tuesday at fourteen, and a 41 average at fifteen against 45 at fourteen. The
  dossier uses the manuscript's.
- **`CURRICULUM_GRID.md`** describes languages as graded by a ten-page report in
  the target language. Not in the manuscript. The dossier says the standard is
  reading and writing and cites the three-language spot check in ch 30 instead.
- **`SYNOPSIS_FROM_TEXT.md`** was written from 35 chapters and does not cover
  ch 36, "Seventy-Five", which is where Priya's ambush, the seventy-five men,
  the two prisoners, and Ruth's top-ten-percent estimate actually live. It also
  predates the current ch 27, which now has a resume-replacement company, a
  registered agent called Hanley, and thirty-one interviews rather than four
  hundred.
- **`THEY_ARE_CHILDREN.md`** quotes Ruth's line at the 4 a.m. Watch as "They're
  actors." The current text reads "They're almost certainly actors, look at
  this." Same reading, different words.
- **`HALSTEAD.md`** is behind `chapters/` on at least the captain's years of
  service, Sam's accuracy line, and the wood shop joint. Because
  `verify_citations.py` searches both, a quotation can pass the script while
  being stale. Every quotation in the dossier was re-checked against
  `chapters/` alone.

### Two manuscript-internal inconsistencies noticed while checking

Not fixed, since the brief is the dossier only. The dossier writes around both.

1. **The stop clause length.** Ch 33 says it "gets exactly one line and no
   examples". Ch 35 says "The paragraph is four lines long."
2. **The corner joint's age.** Ch 14 puts it in the spring of Chloe's eleventh
   year, at a dozen attempts. Ch 23 calls it "the same corner joint half of them
   first cut at fourteen".

Also worth a look, though it may be deliberate: ch 14 and ch 15 both put the
whole school at two hundred students at ages eleven and twelve, where the
enrolment curve wants five to six hundred. `SYNOPSIS_FROM_TEXT.md` 6.3 already
logs this.
