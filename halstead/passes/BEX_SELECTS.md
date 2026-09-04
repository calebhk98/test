# Bex selects: building the boy/girl asymmetry

The blind-read finding this brief starts from: five outside readers called Bex
a rival rather than an antagonist because her credit-taking "applies to
everyone around her," so no single person reads as her target. The fix
decided by the author is selection: she takes credit from girls and gives
credit to boys, by name, and the two need to sit close enough on the page for
a reader to notice both halves without being told to.

This pass touches four files: `chapters/12_nine.md`, `chapters/13_ten_pages.md`,
`chapters/14_sixty_degrees.md`, `chapters/16_thirteen.md`. Three of the four
now carry a side-by-side instance; `12_nine.md` is unchanged, for reasons given
at the end.

## Scene 1 — chapters/13_ten_pages.md, paintball, age nine turning ten

**Girl's work taken:** Chloe and Ruth work out the barrel-as-hose read
(watch the barrel and the feet, move before the shot) together in the
corridor after class. On the Monday, Bex tells Bell she has worked this out
herself and gives him the whole mechanism; Bell puts it on the board under
her name. This beat was already in the chapter before this pass.

**Boy credited by name:** New in this pass. In the same practice stretch
(the Thursday before that Monday), Kavi is shown at the wall bars, on his
own, timing the paintball marker's pump against his own count until it comes
out even — a separate, smaller discovery about the marker's reload gap. Bex
is present (lacing a shoe at the far end of the mats) and says nothing to him
at the time. On the Monday, in the same speech where she gives Bell the
Chloe/Ruth mechanism as her own, she adds the pump-timing detail and names
Kavi for it: "which Kavi had off the wall bars days before anybody asked
him."

**Distance on the page:** One sentence. Both attributions (Kavi named, Chloe
and Ruth unnamed) sit inside the same paragraph, in back-to-back clauses of
the same sentence Bex speaks to Bell.

## Scene 2 — chapters/14_sixty_degrees.md, astronomy dinner, age eleven

**Girl's work taken:** Chloe works out both methods for dating the universe
and says at dinner, to Kavi, that she means to take it to the teacher
herself once the two-week unit ends. Bex asks her about it three times across
the table until she has the whole thing, then brings it to the teacher first,
before Chloe says a word of it to him. This beat was already in the chapter.

**Boy credited by name:** New in this pass, added between the two halves of
the existing beat, at the same dinner. Sam is shown further down the table
working out why a rocket needs to be mostly fuel, getting the ratio backward
twice before Kavi corrects him, then getting it right on his own on the third
try. Bex turns from her own plate and repeats it whole to the boy next to
her, with Sam's name on it.

**Distance on the page:** One paragraph break. The Sam beat is the paragraph
immediately following the sentence where Bex finishes extracting Chloe's
astronomy answer, both at the same dinner, same table.

## Scene 3 — chapters/16_thirteen.md, the Saturday plan, age thirteen

This is the scene named in the brief as flagged by three readers for
muddying the pattern: Bex organizing a Saturday competently, with no visible
edge. It is fixed by giving it the pattern rather than replacing it.

**Girl's work taken:** This half was already latent in the existing text and
did not need new material to surface it. Chloe has already worked out her own
plan for the Saturday — workshop first, kitchens after — in her own head, the
same shape Bex then announces to the table a beat later as her own settled
plan, cutting off Chloe's sentence to finish it for her ("If we leave the
workshop till after, we're—" / "Doing it in the dark..."). Chloe is never
credited for having had the same plan first; the exchange plays as Bex's
signature move, the completed ending.

**Boy credited by name:** New in this pass. Immediately before Bex's
announcement, Sam is given a one-sentence beat at the same table working out
that the kitchens are worth hitting after one o'clock, once lunch trays go
back and leftovers get put out. When Bex lays out the plan a moment later,
she keeps that piece attached to him by name: "the kitchens after one for
whatever is going spare, Sam's timing."

**Distance on the page:** Two sentences / one paragraph break. Sam's beat is
the paragraph directly before Bex's plan; the credit to him sits inside the
same sentence as the plan itself, spoken at the same meal Chloe's own
unspoken, unattributed version came from.

This gives the chapter an edge where the flag said it had none: Bex is not
simply competent, she is quietly attaching her own name to Chloe's shape of
the day while explicitly attaching Sam's name to his one piece of it, in
front of the same table, seconds apart.

## What was not touched, and why

**chapters/12_nine.md.** Read in full against this brief; left unchanged.
The bridge scene here — Bex saying "we" and then giving the entire account in
"I," the joints Chloe alone spent a fortnight getting right — is the
founding instance of the credit-taking pattern in the book and is already on
record (`passes/BEX_NO_UPSIDE.md`) as needing to stay legible as ordinary Bex
at this age rather than escalating. It has no boy-credited beat next to it,
and none was added. This is consistent with the age-and-change instruction in
this brief: at eight and nine the boy/girl selection is meant to read as
occasional, not yet a rule a reader could state, so a single ambiguous
instance with no paired contrast is the correct shape for this chapter. The
sharpening starts in chapters 13 and 14 and holds by 16, which is where the
three built scenes above sit.

## Verification run

`python3 measures/style_report.py` was run on each edited chapter individually
(not `grade.py`, per instruction).

- `chapters/13_ten_pages.md`: 4248 words. TIC SCAN found one hit, the
  pre-existing superlative sentence about the best time in the room, already
  on record in `BEX_NO_UPSIDE.md` as predating any pass and outside the
  edited material. Nothing in the new text triggered a tic.
- `chapters/14_sixty_degrees.md`: 4139 words. TIC SCAN: none found.
- `chapters/16_thirteen.md`: 4142 words. TIC SCAN: none found.

`measures/check_edits.py` was run across all chapters: 13, 14 and 16 show 0
em dashes, 0 curly quotes, 0 trailing-space lines, with word-count deltas of
+87, +68 and +38 respectively against the prior version, all still inside the
2,000-5,000 band and nowhere near either edge of it.

All new material was checked by hand, and by grep across the diff, against
the banned-word and banned-phrase list in the brief (instead, both hands,
leaves it, puts it back down, rather than, hands flat, turning it over, for
the first time, never once, in order), plus "same" and "the whole/rest of
it," neither of which was added anywhere in the new text. The one instance of
", because" introduced (chapter 16, "over the last of his own plate, that the
kitchens are worth trying after one... because that is when whatever is left
over gets put out") is narration, not dialogue, and the constraint is
dialogue-only. No named emotional states were introduced in narration. Every
boy named (Kavi, Sam) was already an existing character before this pass; no
new characters were invented. Every quotation reproduced in this document was
copied from the file and checked against it. `grade.py` was not run.
`HALSTEAD.md` was not touched.

## Honest estimate

A cold reader who reads chapters 13, 14 and 16 in sequence has, by the third
scene, seen the identical shape occur three times: a boy's name kept on his
own small piece of work, a girl's identical-caliber work folded into Bex's
account with no name on it, both inside the same short stretch of page,
across three different subjects (paintball, astronomy, a Saturday plan) and
two different boys (Kavi, Sam). That repetition across unrelated contexts is
the thing a single instance cannot give a reader: it is not "Bex did this to
Chloe once," it is "Bex does this, specifically, along this line, every time
a boy and a girl are both in reach." I think a reader stopping to compare the
Sam or Kavi clause against the sentence next to it would be able to state the
rule after chapter 14 alone, and would have it confirmed rather than
introduced by chapter 16. A reader moving faster, who does not pause on the
naming clause, would still likely notice something is off about chapter 16 in
particular, since the Sam attribution sits directly inside the sentence where
Bex takes Chloe's plan, which is a tighter join than either of the earlier
two scenes.

What I have not done, and think should stay undone in these four chapters, is
tip the ratio further: none of the three scenes was pushed to a fourth
sentence, a callback, or a second boy in the same beat, since the brief's own
warning against overuse applies here as much as anywhere else in this
manuscript, and three clean instances across three chapters is closer to "a
device that would be good seven times and currently appears zero" than to a
tic in need of restraint.
