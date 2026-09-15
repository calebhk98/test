# Fix pass C — report

All edits made in `chapters/`, then synced with `python3 sync_chapter.py <file>` for each of the
three files touched. Each sync printed `-> MANUSCRIPT_FULL.md, HALSTEAD.md` with no `!!` warning.
Paragraph convention confirmed by `grep -c '  $'` (0 for all three files) — chapters 10-12 use
blank-line paragraphs, not the two-trailing-space convention of chapters 1-6.

## chapters/10_april.md

**1. Rock count, L57 vs L163 (March discrepancy)**
- Before: "...because two new ones came in during March, which Fen had kept to herself."
- After: "...because one more came in during March, which Fen had kept to herself."
- Why smallest: night-one dialogue already establishes one specific rock ("This one came in
  March") that Fen showed Chloe outright. Changing "two new ones" to "one more" makes the June
  line describe a *different*, undisclosed March arrival rather than contradicting the disclosed
  one — one word swap, no touch to the night-one line.

**2. L43 vs L41 (Chloe already knew the count)**
- Before: "It's four before Ruth even says it. She'd counted them herself, the week it happened."
- After: "She already knows it's four. She'd counted them herself, the week it happened, before
  Ruth ever said so."
- Why smallest: the original construction reads as if the number is revealed only now, right
  after Ruth has already said "four" aloud one paragraph earlier, which is backwards. Rewording to
  state Chloe's prior knowledge directly, with "before Ruth ever said so" attached to the counting
  clause instead of the number reveal, removes the contradiction without adding a new sentence.

**3. L165-173 (five unattributed farewell lines)**
- Before: five consecutive untagged quotes ("Ten weeks is a long time...", "I'll call you on a
  Wednesday.", "Wednesday's fine...", "September.", "September, then.")
- After: tagged alternately — Ruth ("Ten weeks is a long time...", "Wednesday's fine...",
  "September, then.") and Chloe ("I'll call you on a Wednesday.", "September."), using the "X
  says" tag already established as the chapter's convention (e.g. L31, L105, L143).
- Why: checked RUTH.md and SAM.md first. Sam is present in the scene (per L163) but is described
  as occupied elsewhere, talking to someone else's grandmother, so I read this specific exchange
  as Ruth and Chloe's farewell, with Sam left as scene-setting rather than forced into a third
  speaking role. Ruth's lines fit her assertion-then-reason shape (L1) and flat declaratives
  (L3, L5); none of the five lines end in a hedge or violate her no-question-mark rule. Tagging all
  five (rather than only enough to seed the alternation) matches how the manuscript already tags
  Chloe's own lines elsewhere in this chapter (L35, L143, L151), so it isn't an added convention.

**4. L79 (untagged "Yours is a triangle")**
- Before: "Yours is a triangle." (untagged)
- After: "Yours is a triangle," the cooking teacher says.
- Why smallest: one tag, matching the manuscript's habit of introducing an unnamed teacher generically ("the teacher") rather than inventing a name; "the cooking teacher" (vs. plain "the teacher") avoids ambiguity with the swimming and literature teachers named earlier in the same montage.

## chapters/11_eight.md

**5. L67 vs L75 ("nine" argued before it exists)**
- Before: "In week three she comes in at nine forty and her mother is standing in the front hall."
- After: "In week three she comes in at nine forty, forty minutes past her nine o'clock curfew, and
  her mother is standing in the front hall."
- Why smallest: one inserted clause establishes Chloe's curfew as nine before she argues from it
  ("somebody picked ten the same way somebody picked nine"), so her mother's later flat "Nine." is
  read as reasserting the known rule rather than introducing the number for the first time. No
  other line touched.

**6. L111 (ambiguous "they"/"her")**
- Before: "...while they say hello in corridors all year, once in November Fen shows her a piece
  of quartz the size of a fist."
- After: "...while she and Chloe say hello in corridors all year, once in November Fen shows
  Chloe a piece of quartz the size of a fist."
- Why smallest: pronoun-for-noun swap only, resolving both ambiguous pronouns against the
  just-introduced "girl from Maine."

**7. L195 ("the four of them" unnamed)**
- Before: "On a Tuesday in April the four of them end up on the grass behind the science building..."
- After: "On a Tuesday in April Sam, Kavi, Ruth, and Chloe end up on the grass behind the science
  building..."
- Why smallest: names substituted directly for the pronoun phrase; rest of sentence untouched, and
  all four names are already active in the surrounding paragraph.

**8. L89-97 (grandmother's line untagged)**
- Before: "\"She's put on weight.\"" (untagged)
- After: "\"She's put on weight,\" her grandmother says."
- Why smallest: one tag on the first line of the exchange establishes the grandmother/mother
  alternation for the rest of the four-line exchange, matching the existing tag on the mother's
  final "I know" (L97).

## chapters/12_nine.md

**9. L97/L101 (weekday vs. date)**
- Before: "Then thirty people watch me not do it, and that's still Tuesday."
- After: "Then thirty people watch me not do it, and that's still Monday."
- Why smallest: 11 May 2015 (within the chapter's September 2014-July 2015 span) was a Monday.
  One word changed; the date itself ("the eleventh of May") is left alone.

**10. L89 vs L91 (dislike not landing — larger edit authorised)**
- Before: "Bex talks over the ends of sentences. Iyad agrees with you loudly in a way that means
  he stopped listening around the second sentence. In the second term she builds a bridge with Bex
  that carries nineteen pounds, coming down a plank at a time instead of all at once. Two people
  ask them afterwards how they did the joints. She works with Iyad in chemistry for six weeks,
  during which he is careful and fast, and she would take him again tomorrow."
- After: "Bex talks over the ends of sentences, hers most of all, until Chloe has learned to get
  to the point before Bex can start talking over the last three words of it. Iyad agrees with you
  loudly in a way that means he stopped listening around the second sentence, then repeats your own
  idea back to you at dinner as if it were his. In the second term she builds a bridge with Bex
  that carries nineteen pounds, coming down a plank at a time instead of all at once, and she
  answers the two people who ask afterwards how they did the joints before Bex can get a word in.
  She works with Iyad in chemistry for six weeks, during which he is careful and fast, and she
  would take him again tomorrow rather than sit through another dinner listening to her own idea
  come back to her secondhand."
- Why: kept the original two-sentence character sketch and the professional-respect facts (the
  bridge, the six weeks in chemistry) intact, but gave each a concrete, specific grievance —
  Bex talking over her particularly, Iyad appropriating her ideas at dinner — and let those
  grievances visibly shape how Chloe behaves around them (racing to answer before Bex can, taking
  Iyad's competence over his company). This is the one item the brief authorised for a larger
  edit; I kept it to the same paragraph and did not touch anything else in the chapter.

**11. L103 (untagged book)**
- Before: "Ruth is screaming, and Kavi has both arms straight up over his head. Chloe finds
  afterwards that she has torn the corner off the book she was holding, though she does not
  remember doing it."
- After: "Ruth is screaming, Kavi has both arms straight up over his head, and Chloe is on her
  feet with the book she'd brought down still in one hand. She finds afterwards that she has torn
  the corner off it, though she does not remember doing it."
- Why smallest: the book is placed in Chloe's hand in the same reaction beat, immediately before
  the line that requires it, rather than building a separate earlier scene to introduce it.

**12. L99 (untagged "What if you don't?")**
- Before: "\"What if you don't?\"" (untagged)
- After: "\"What if you don't?\" Chloe asks."
- Why: tagged to Chloe. Ruth's dial rules out a question mark for her ("she asks by flat
  declarative, never a question mark"), and Kavi's questions chase mechanism, not hypothetical
  outcome, so neither fits. "Chloe asks" matches her established pattern of blunt hypothetical
  questions to friends (e.g. "Why do you bother, if you're leaving the room in August?" to Fen,
  chapters/10_april.md) and the tag form already used for her elsewhere ("Chloe asks",
  chapters/10_april.md:163).

## Notes

Nothing else in these three chapters was touched. No item on the list turned out to be a
non-problem on inspection — all twelve were real as described and fixed as listed above. No
unrequested issues spotted worth flagging.
