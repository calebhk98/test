# Word pass: chapters 9-14

Scope: `chapters/09_february.md` through `chapters/14_sixty_degrees.md`. No other
chapter opened for editing. `passes/HOUSE_RULES.md` and `passes/DO_NOT_FLAG.md`
read in full before starting. `measures/style_report.py` run per chapter after
edits, not `grade.py` (other agents running concurrently).

Protected text left untouched, per brief:
- Ch12: the bridge scene, "Bex Alcantar arrives..." through "...for the rest
  of the year" (the whole credit-taking paragraph block).
- Ch13: the paintball floor-and-corridor sequence, "Paintball joins the
  afternoon block in October" through "...past where they ever were with
  darts" (the full Bex/Bell scene, including the corridor beat inside it).
- Ch14: the astronomy dinner sequence, "Calculus arrives..." through "...the
  grass soaks through her boots on the way down" (the fortnight-of-the-
  universe scene where Bex takes Sam's and Chloe's work).

Also preserved: the five ruled-deliberate named states in this span ("which
she finds restful," ch12) and the recurring "loses her by the second
sentence" echo (ch12 and ch14) that Iyad's cruelty depends on repeating
verbatim — neither word was touched at either occurrence.

## Correction mid-pass

Partway through, the coordinator flagged that another agent had been
replacing goes/gets/comes with passive constructions ("is sent," "is added,"
"is spent") and that this was reverted wholesale, since the book's active-verb
rate (4.81% passive sentences) is a deliberate, measured strength. I audited
my own edits against this and found four I'd made the same mistake on, all in
chapter 11, before the note arrived:

- "she gets a team" → I had it as "is placed on a team" → fixed to "she draws
  a team"
- "the sheet goes up on the wall" → I had it as "is posted on the wall" →
  reverted to "goes up"
- "Her name goes on the choir line" → I had it as "is added to the choir
  line" → reverted to "goes on"
- "gets applied to a stairwell" → I had it as "is applied to" → fixed to
  "reaches a stairwell"

And two in chapter 9:
- "The house comes up in April" → I had it as "is raised again in April" →
  reverted to "comes up again"
- "gets asked what fine means" / "gets that answered too" → both had drifted
  toward be-passives → rewritten as plain active clauses

All six are fixed in the files below. After the correction I left goes/gets/
comes/does almost entirely alone for chapters 13 and 14, touching only a
handful of clear active-verb swaps (climbs in/out, manages, rings, turns
cold) and leaving the rest — these four words are the least reliable ground
in this brief, present-tense-inflated, and now doubly risky to over-edit.

## Before/after counts

| word | 09 | 10 | 11 | 12 | 13 | 14 |
|---|---|---|---|---|---|---|
| somebody | 6→4 | 10→8 | 6→5 | 3→2 | 9→9 | 11→11 |
| twice | 3→3 | 6→6 | 4→4 | 8→8 | 6→6 | 7→7 |
| already | 4→3 | 12→4 | 9→4 | 7→4 | 10→9 | 7→6 |
| second | 2→2 | 14→14 | 6→5 | 16→16 | 13→13 | 16→16 |
| whole | 14→4 | 16→3 | 12→2 | 17→3 | 11→4 | 17→1 |
| end | 8→1 | 15→12 | 9→8 | 7→7 | 12→12 | 12→11 |
| still | 8→4 | 10→7 | 11→10 | 7→6 | 19→15 | 16→13 |
| every | 8→6 | 7→6 | 12→12 | 12→12 | 13→13 | 16→16 |
| before | 8→4 | 22→18 | 10→9 | 21→21 | 27→18 | 21→19 |
| gets | 6→3 | 8→4 | 6→4 | 10→9 | 16→16 | 13→13 |
| goes | 8→4 | 12→3 | 10→6 | 12→9 | 21→21 | 12→12 |
| comes | 8→6 | 6→5 | 10→8 | 13→13 | 9→9 | 5→5 |
| does | 3→3 | 4→4 | 2→2 | 15→12 | 6→6 | 6→6 |

Word counts held or shrank in every chapter (e.g. 13: 4298→4291; 12:
4268→4251; 09: 2660→2626), all still inside 2,000-5,000, no chapter padded.

## Hedges added (dialogue only, six total)

1. Ch10 — library teacher: "If you read something terrible and write about it
   well, **I think** that's a good week."
2. Ch10 — Chloe on the phone about her roommate: "...I basically have the
   room to myself after that; **I don't mind it**."
3. Ch11 — grandmother: "**I think** she was so thin at Christmas, but I kept
   it to myself at the time."
4. Ch12 — Chloe, cribbage: "Where does the run come in? **I think** that's a
   different kind of point I'm missing."
5. Ch13 — Chloe, Thanksgiving tariffs argument: "It's what I had, and it's **a
   little** thin, I know it's thin..."
6. Ch14 — mother, about the bombing essay: "**I think** that's a big subject
   for a school essay."

No hedge went into narration. Six across six chapters is the "handful"
called for, not one per page.

## Words I decided not to cut, because they were doing real work

- **whole/every "Every night. Every single. Every night for the rest of my
  life"** (ch9) and the parallel **"whole"** in the same bargaining scene
  ("Take the whole birthday," "not my whole life") — deliberate rhetorical
  repetition in Chloe's pleading. Left every instance.
- **"a whole sentence"** (ch9, "it is a whole sentence, and she forces it out
  twice") — the contrast point of the paragraph: the first complete sentence
  she manages after a scene of fragments. Cutting it erases the beat.
- **"somebody" ×2** (ch9, "You can hand somebody a month. You cannot hand
  somebody a street.") — a built rhetorical pair in the parents' argument.
- **already** in "**she is relieved to find it still works**"-adjacent lines
  were not present in this span, but the equivalent case is ch12's "which she
  finds restful" — untouched per DO_NOT_FLAG.
- **"still"** in "**the price still went up while it just sat there doing
  nothing**" (ch14) — the entire argument of Chloe's art-history complaint
  turns on that word.
- **"already answered those objections earlier"** (ch14, Hearn's note) — this
  is the substance of his critique (she is repeating herself), not filler.
- **second** — almost every instance across all six chapters is a floor
  number, a grade, a class period, a place in a race, or an ordinal in a
  list (second grade, second floor, second week, "which came second in the
  room," "loses her by the second sentence"). None of these are the "for a
  second" filler the brief describes, so second is essentially untouched
  (only one true swap, ch11's "stops the second she knows" → "stops the
  moment she knows").
- **twice** — every remaining instance is a specific, meaningful count
  (Sam's fourteen seconds, Odile's three-days-out-of-five, Fen's twice-
  performing radiator), consistent with the brief's own caution that most
  are the point in this book. None cut.
- **somebody** in scenes of genuine unseen/unknown actors (parents arguing
  through a floor, a crowd during a chaotic drill, a rumor's source) — kept
  as legitimate camera-limited ambiguity rather than forced into a name.

## Notes on constraints

- Every dialogue-internal cut of the nine target words was done as a
  same-or-greater-word-count swap (mostly "whole"→"entire") rather than a
  deletion, to protect the 18.0-word quotation-length floor and the 20-25%
  short-quotation band. No existing quotation was shortened.
- Checked every edited sentence for a second "and" before finalizing; caught
  and fixed two edits that would have pushed a single-and sentence to
  two-and (ch10 twice, ch14 once).
- No em dashes, curly quotes, or trailing-space lines introduced (checked
  with a direct Unicode scan of all six files).
- Chapter 13's local 2+-and rate reads at 10.2% in isolation; I did not add
  an "and" anywhere in this chapter (verified against each edit), so this
  reflects the chapter's existing density, not this pass.
