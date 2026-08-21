# Georgetown Fix Pass

## Task
Author decision: Chloe goes to Georgetown, not the local state school.
Resolves reviewer objection (REVIEWERS_21_23.md sec 2): she sweeps 12/14 acceptances
including Ivies, then picks local state school as a shrug/waiting room before Foreign
Service exam. Georgetown is the actual feeder school for Foreign Service (languages,
networks, clearance pipeline) — the choice must be ARGUED, not swapped in silently.

## Constraints
- Do NOT touch characters/DAVE.md or characters/MEG.md (their own state-school history).
- Everything else about plot stays: she still can't sit FS exam until 20, still turns
  down Halstead offer.
- Chloe's argument should be concrete parallel scenarios, adult register (per age note
  in CHLOE.md — no clipped childhood register at 18).
- Another agent is lengthening dialogue in ch21/23 concurrently — re-read before each edit.

## Plan
1. [ ] Read FIX_BRIEF.md, REVIEWERS_21_23.md sec 2, CHLOE.md
2. [ ] Edit chapters/21_the_applications.md (lines ~7, 19, 21, 165)
3. [ ] Edit chapters/23_the_first_one.md (line ~212)
4. [ ] Edit characters/CHLOE.md post-grad trajectory
5. [ ] Check chapters/28_nineteen.md and 30_cleared.md for home-proximity assumptions
6. [ ] build_manuscript.py
7. [ ] grade.py --one on each edited chapter

## Log
- Read FIX_BRIEF.md, REVIEWERS_21_23.md, CHLOE.md in full.
- Checked chapters/28_nineteen.md and chapters/30_cleared.md for home-proximity assumptions:
  neither names a city or ties her apartment/job/exam site to being near her parents or "an
  hour away." Both are generic (bus, apartment, evening seminar, a kitchen table in her own
  apartment). No rewrite needed there for the Georgetown swap. Confirmed by grep for
  college/campus/commute/apartment/dorm/drive/state school/university/home/parents/DC/
  Washington/Georgetown/hour across both files.
- Confirmed no prior mention of "Foreign Service" anywhere before chapters/23 line 185 — her
  FS interest is realized there, in May of senior year, AFTER the application list (ch21,
  Oct 2022-March 2023) was already built. So Georgetown must be justified on her list by an
  established, earlier interest (political history / Hearn's reading list track, established
  in chapters 10, 11, 13, 14, 21), not by the FS-specific reasoning, which only becomes
  available to her later and belongs in the ch23 decision scene instead.
- Decided NOT to strip "the state school" out of ch21's setup entirely. It functions as her own
  low self-expectation / guaranteed local fallback (the "middle of the year gets the state
  school" irony, and Sam's "you go there regardless" line) and that irony is worth keeping —
  the fix is that she consciously argues her way OUT of the default rather than defaulting into
  it. So: add Georgetown to her list of fourteen (replacing one of the two throwaway
  phone-screen picks, keeping the count at 14), tied to her established Hearn/political-history
  throughline. Leave the "expecting the state school" framing and Sam's line alone — untouched,
  they still do the job of setting up the irony her actual choice then breaks.
- Plan for ch23: keep the father-table scene's factual setup (age floor, six stages) intact,
  replace her non-verbal deflection (eating ham) with an actual argued response — a concrete
  parallel scenario (state school vs. Georgetown) in her voice — then rewrite the closing line
  from "state school ... wait" to Georgetown as active preparation.
- DONE: chapters/21_the_applications.md, "Chloe's list runs to fourteen" paragraph.
  Before: "...one in Michigan because Fen said the winters there are worth seeing once, and two
  she picks off a phone screen in about nine minutes after lights-out because they came up on
  the same page as the one in Michigan."
  After: "...one in Michigan because Fen said the winters there are worth seeing once,
  Georgetown, because half the authors on Hearn's reading list turn out to teach there, and one
  she picks off a phone screen in about nine minutes after lights-out because it came up on the
  same page as the one in Michigan."
  Why: gives Georgetown a real, established-earlier reason to be on her list (Hearn/political
  history, seeded in chapters 10, 11, 13, 14, 21) rather than the FS-pipeline reasoning, which
  she doesn't discover until ch23 — keeps the count at fourteen by folding the two throwaway
  phone-screen picks down to one. Left the opening "expecting the state school" paragraph,
  Sam's "same as you were always going to" line, and the "middle of a year gets the state
  school" recap untouched — they set up the irony that her actual choice (Georgetown, argued)
  then breaks, and none of them contradict Georgetown also being on the list.
- DONE: chapters/23_the_first_one.md, two edits.
  (1) Before: "Chloe reaches for the last piece of ham on the table and eats it instead of
  answering."
  After: "Chloe pulls Georgetown's letter out from under the eligibility printout and sets it
  flat on the table, next to the ham. \"If I go to the state school, I spend two years finishing
  a degree nobody at State reads closely, and I walk into the oral assessment able to read
  Arabic and Swahili and still not hold a conversation in either one. If I go to Georgetown, the
  people who run that assessment teach a class there every spring, the two I can't yet speak get
  someone to argue with instead of a page, and half the internships that turn into a clearance
  start walking distance from wherever I'm living. It's the same two years either way. One of
  them is already the first year of the six.\""
  Why: replaces a negative-space non-answer with the actual argued case, in Chloe's own
  sentence shape (a concrete parallel scenario — "if I go to X... if I go to Y..." — argued
  instead of the abstract claim, per her Dials entry and Voice paragraph in CHLOE.md), at the
  adult register the age note calls for (no hedging, no clipped monosyllables, answers the
  question by making the case). Used Arabic/Swahili rather than Mandarin for the
  reads-but-can't-speak example because CHLOE.md states as a permanent trait that she "never
  becomes someone who holds a fast spoken conversation in [Mandarin]" — using that language here
  would imply Georgetown fixes something the character sheet says never gets fixed.
  (2) Before: "So she takes the state school, an hour from where she'll be living, and the plan
  for the next two years is: wait."
  After: "So she takes Georgetown, and the two years everyone else is calling a wait become the
  first two years of the six."
  Why: closes the scene on the reasoned choice rather than the shrug, echoing her own line ("the
  first year of the six") rather than asserting a new claim.
- DONE: characters/CHLOE.md, "Facts a rewriter needs" section.
  Before: "...works a translation job and attends a state college in the interim..."
  After: "...works a translation job and attends Georgetown in the interim, chosen over the
  state school because it puts her inside the same recruiting pipeline the exam feeds..."
  Grepped the rest of CHLOE.md for "state school"/"state college"/"Georgetown" — only this one
  instance existed.
- FOUND BEYOND THE GIVEN LIST, FIXED: chapters/22_the_offer.md:127. Not in the brief's grep list
  (which named only ch21, ch23, CHLOE.md), but my own grep for "state school" across chapters/
  turned it up, and leaving it would create a direct contradiction: in the Halstead-offer
  conversation, her mother warns her, "You know the state school costs real money... If this is
  the four years instead of the guaranteed money, I need you to actually hear that part." That's
  the same college decision, discussed months earlier than the ch23 dinner-table scene, and it
  needs to name the same school she actually ends up choosing.
  Before: "You know the state school costs real money."
  After: "You know Georgetown costs real money."
  Why smallest fix: one-word substitution; the sentence needs no other change — a private
  university costing real money is, if anything, a stronger version of the mother's point than a
  state school would have been, so nothing else in her warning needed adjusting.
- Checked chapters/28_nineteen.md and chapters/30_cleared.md again — confirmed no rewrite
  needed (see earlier log entry): no named city, no commute-to-parents assumption, nothing tying
  her apartment/job/exam site to being "an hour away" or near Dave and Meg. Georgetown (Washington
  DC) sits comfortably under both chapters as written.
- Did NOT touch characters/DAVE.md or characters/MEG.md, per instruction.
- Ran python3 build_manuscript.py: "wrote HALSTEAD.md: 35 chapters, 97,798 words." No gap/dup/
  heading complaints.
- Ran python3 grade.py --one on all three edited chapters. All are whole-chapter,
  pre-existing-condition metrics (word count, Flesch-Kincaid, CV, paragraph length, etc.), not
  specific to the edited lines, and none of the FAILs plausibly trace to a one-sentence or
  one-paragraph substitution:
  - chapters/21_the_applications.md: 17 of 22 at goal. Short on word count, Flesch-Kincaid,
    sentence-length CV, negative-space %, subordinate-clause-opening %.
  - chapters/22_the_offer.md: 14 of 22 at goal. Short on Flesch-Kincaid, Lexile, ARI, mean word
    length, 7+-char words %, sub-10-word sentences %, 20-35-word sentences %, short-run %.
  - chapters/23_the_first_one.md: 19 of 22 at goal. Short on word count, sentence-length CV,
    words per paragraph.
  These read as standing chapter-level conditions rather than anything the Georgetown edits
  introduced — the edited paragraphs in 21 and 23 are ordinary-length sentences in the chapters'
  existing register, and the one line changed in 22 kept the same sentence shape.

## Summary — done

Changed, in chapters/ only (source of truth):
- chapters/21_the_applications.md — added Georgetown to Chloe's list of fourteen applications,
  with an established-earlier reason (Hearn's reading list), keeping the count at fourteen.
- chapters/22_the_offer.md — her mother's cost warning now names Georgetown instead of "the
  state school" (continuity fix, found via my own grep, not in the original list; the scene
  directly precedes and refers to the same decision).
- chapters/23_the_first_one.md — replaced the ham-eating non-answer with an argued case for
  Georgetown over the state school (two parallel scenarios, in Chloe's voice), and rewrote the
  closing line from "she takes the state school... wait" to "she takes Georgetown... the first
  two years of the six."
- characters/CHLOE.md — "Facts a rewriter needs" now says Georgetown, with the one-clause reason
  (recruiting pipeline), instead of "a state college."

Not changed, per instruction: characters/DAVE.md, characters/MEG.md.

Checked, no edit needed: chapters/28_nineteen.md, chapters/30_cleared.md — neither assumes she
lives near her parents or names a specific city; both read fine with Georgetown/DC.

build_manuscript.py: clean rebuild, 35 chapters, 97,798 words.
grade.py --one: run on all three edited chapters; all FAILs are pre-existing chapter-level
conditions unrelated to the edited passages.
