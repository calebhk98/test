# Fix report — B

Four chapters, ten items. All edited in `chapters/` and synced via `sync_chapter.py`; each run
printed only the two expected write targets (`MANUSCRIPT_FULL.md`, `HALSTEAD.md`), no `!!` warnings.

## chapters/06_the_list.md

**Karate missing from Chloe's recitation (L119 vs L28-41)**
- Before: `Then chess, which Sam is also better at.` / `Then the nerf guns at the end, because she just remembered.`
- After: `Then chess, which Sam is also better at.` / `Then karate.` / `Then the nerf guns at the end, because she just remembered.`
- Smallest fix: a new one-line paragraph in the same terse "Then X." shape already used for chess, dropped in without reaction or elaboration — nothing else in the recitation changed.

## chapters/07_the_same_room.md

**L5 — Kavi given "she"**
- Before: `...from whom she gets a hand up, before a family walks between them, and by the time they pass, he's gone.`
- After: `...from whom he gets a hand up, before a family walks between them, and by the time they pass, he's gone.`
- One-word pronoun swap; the sentence already gets it right nine words later.

**L45 — unfinished comparison**
- Before: `her mouth goes tight at the corners, the way it does right before.`
- After: `her mouth goes tight at the corners, the way it does right before she cries.`
- Chloe is already wiping her eye one line earlier (L41), so "before she cries" completes the comparison without adding a new beat.

**L189 — "there" with no referent**
- Before: `That's over a year from now, and she's in there right now.`
- After: `That's over a year from now, and she's in second grade right now.`
- The chapter has already established (L99, L109) that this whole section takes place during Chloe's second grade year, and the call is about testing for third grade; naming the grade is the minimal fix.

## chapters/08_the_asking.md

**L35 — second person breaks the list**
- Before: `...working down through who ran it, and how they found you, and whether Chloe stayed overnight...`
- After: `...working down through who ran it, and how they found her, and whether Chloe stayed overnight...`
- One-word fix to match the third person used everywhere else in the list.

**L67 — "her" ambiguous between mother and Chloe**
- Before: `...on the phone first and then in the building itself, where they give her a chair in a corridor.`
- After: `...on the phone first and then in the building itself, where they give Chloe's mom a chair in a corridor.`
- Chloe isn't present for these meetings (she "gets it in pieces" two lines later), so the chair is the mother's; naming her with the chapter's standing "Chloe's mom" phrasing (already used once at L11) removes the ambiguity without changing who it refers to.

**L115 — "it" with no concrete referent**
- Before: `...and then it's happening and her throat hurts before she has got four words out of it.`
- After: `...and then the fight is happening and her throat hurts before she has got four words out of it.`
- Names the fight once, at the point the reader needs it; the second "it" a few words later now has a clear antecedent.

**L109-113 vs L137 — ordering**
- Before: the Monday/Tuesday/Wednesday paragraph was followed immediately by "The jacket is Friday...", and "The second Thursday is the same as the first one" only appeared later, after the fight and the dinner scene, attached to "So is the third, except that..."
- After: `On the Wednesday her mom says not now, Chloe.` is now followed by its own paragraph, `The second Thursday is the same as the first one.`, and only then `The jacket is Friday, and any excuse would have done as well.` The later paragraph now opens directly with `So is the third, except that Mrs. Prahl puts them in pairs...`, immediately after the dinner scene.
- This is a pure reorder: one sentence was moved from after the fight to before the Friday jacket scene, with no rewording. The second Thursday now falls, chronologically, between the Wednesday and the jacket Friday, matching the calendar the brief laid out; the third Thursday (and the "something about the Thursday that needs an answer" at dinner) still reads correctly following the fight, since that Thursday is still upcoming at that point.

## chapters/09_february.md

**L31 vs L15 — birthday offered twice in dialogue, once on the page**
- Before: `"She said take my birthday, Dave, and then she said it a second time."`
- After: `"She said take my birthday, Dave."`
- Per the brief's preference, changed L31 rather than L15; the litany at L15 gives the birthday once, so the claim of a second time is simply cut.

**L65 — untagged line, confirmed as Meg**
- Before: `"We're saying yes, Chloe. We're saying yes."`
- After: `"We're saying yes, Chloe. We're saying yes," her mom says.`
- Tagged with the chapter's own convention (`her mom says` / `her dad says`, used throughout, including the first "We're saying yes" three lines earlier).

**L95 — unnamed object**
- Before: `Her mother keeps hold of what she's holding. "No. Absolutely not."`
- After: `Her mother keeps hold of her mug. "No. Absolutely not."`
- `characters/MEG.md` establishes the mug ("takes her coffee milky, in a mug that says nothing in particular, reheated at least once every morning because she keeps putting it down mid-task") as her standing prop, so naming it here matches the character file rather than inventing a new object.

## Notes

Nothing else was touched in these four chapters. No item required a larger change than the brief allows, and none turned out to be a non-problem on inspection.
