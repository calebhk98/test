# Fix report — D

Four chapters, nine items. All edited in `chapters/` and synced via `sync_chapter.py`; each run
printed only the two expected write targets (`MANUSCRIPT_FULL.md`, `HALSTEAD.md`), no `!!` warnings.

## chapters/13_ten_pages.md

**L23 vs L164 — Christmas reading contradicts Hamilton's already-finished range**
- Before: `Over Christmas at her grandmother's she reads Federalist 70 and 78 on the floor of the spare room with the door shut.`
- After: `Over Christmas at her grandmother's she reads Federalist 70 and 78 again on the floor of the spare room with the door shut.`
- Chose the reread option over moving to Madison: one word marks it as her going back over papers she finished by "the middle of December" (L23), rather than requiring new Madison numbers that would need to be picked and checked against nothing else in the chapter ever naming Madison again.

**L37-39 — twos/October reordered before ones/November**
- Before: `...the same thing slightly faster. In November it goes to twos. Kowalczyk tells her in October that she is planting her back foot before she knows where she is going, and that she needs to stop deciding so early.`
- After: `...the same thing slightly faster. Kowalczyk tells her in October that she is planting her back foot before she knows where she is going, and that she needs to stop deciding so early. In November it goes to twos.`
- Pure reorder, no rewording: swapped the two sentences so October precedes November, matching the chapter's otherwise strict chronology.

**L116-122 — three untagged confession lines**
- Before: `"Six is me." / "Six is four of us." / "I was standing in it." / "So was I, and so was Wes..." Ruth is still looking at the sheet.`
- After: `"Six is me," Chloe says. / "Six is four of us, Chloe." / "I was standing in it." / "So was I, and so was Wes..." Ruth is still looking at the sheet.`
- Only two of the three untagged lines needed touching. L112 already established Chloe stood in the stairwell, so tagging her first line fixes the anchor; from there the exchange is a two-person alternation (Chloe/Ruth/Chloe/Ruth-tagged). Per RUTH.md, Ruth's signature move is naming the person she's correcting inside her own sentence rather than in a dialogue tag ("It is not better, Sam."), so her correcting line got "Chloe" folded into it instead of a bolted-on "Ruth says" — that both identifies the speaker and matches her established voice. The third line ("I was standing in it.") is now recoverable as Chloe's by the alternation and was left untouched.

## chapters/14_sixty_degrees.md

**L47 — Odile's run pace was slower than a walk**
- Before: `Coming up the field at a run from her end, Odile covers seventy metres in about forty seconds.`
- After: `Coming up the field at a run from her end, Odile covers seventy metres in about twelve seconds.`
- One number changed. Twelve seconds over seventy metres (~5.8 m/s) reads as a hard run for the fastest student in the year, instead of 1.75 m/s. Note: `characters/ODILE.md` (not in scope for this pass) cites the same "seventy metres in about forty seconds" figure twice, sourced from this chapter — it will now be out of sync with the corrected line and may be worth a follow-up pass.

## chapters/15_twelve.md

**L41 vs L53 — bread-test headcount didn't close**
- Before: `...marks the underside of the four plates, and leaves the eating to the other three.`
- After: `...marks the underside of the four plates, and leaves the eating to the other four.`
- L41 puts five people in the room (the core four plus Priya). One word fix: "four" tasters + 1 cutter = 5, matching the room, and matching four plates one-per-taster. It also closes a second, unflagged gap I checked as a sanity test: two rounds x four tasters = eight tasting instances, which is exactly the "five right out of eight" scored later (L83) — with "three" tasters that total would have been six, not eight. Confirms four is the right number, not just an equally-valid alternative.

**L53 vs L81/83 — plural separate keys vs. one key, one reader**
- Before: `Each of them writes their own key on a scrap and folds it before anybody starts.`
- After: `Kavi writes the key on a scrap and folds it before anybody starts.`
- Smallest fix that matches what follows: a single key, held by Kavi ("Kavi's got the key in his pocket," L81) and read out once by him alone (L83). Swapped the plural/reflexive construction for the singular one rather than adding text elsewhere to explain multiple keys being collected.

**L97 vs L291 — Christmas-dated clause sat before the Thanksgiving scene**
- Before: `By Christmas she can hold twenty-four seconds in the 10v1, but she is still only ranked thirty out of ninety. She gets to the library about once a week now, ...` — followed by the Defensive Watch sequence, then the Thanksgiving scene.
- After: the Christmas sentence was cut from that spot (leaving `She gets to the library about once a week now, ...` in place) and moved to a new short closing beat at the end of the chapter, after the Thanksgiving scene's last line, set off by a `---` in the same way the chapter already uses section breaks: `"Huh," her father says, and holds his hand out for the ham. / --- / By Christmas she can hold twenty-four seconds in the 10v1, but she is still only ranked thirty out of ninety.`
- Per the brief's preference, moved the clause rather than the scenes. This also matches the pattern already used in chapters/13_ten_pages.md, where academic/training progress resumes in a short beat right after the Thanksgiving scene — and the chapter's own date range ("September 2017 – January 2018") supports a Christmas-dated line landing at the very end.

## chapters/16_thirteen.md

**L47 — "it is not that" has no antecedent**
- Before: `...working through the same building, so whatever a fail is for here, it is not that.`
- After: `...working through the same building, so whatever a fail is for here, it is not expulsion.`
- One-word swap supplying the ruled-out consequence (visibly true: he's still in the same building, same year) without touching the very next sentence, which still withholds what the fail actually costs him.

**L133-149 — napkin handoff to Chloe never shown**
- Before: `Kavi takes it off him inside a minute, offhand about it. Ruth reads it upside down from across the table...`
- After: `Kavi takes it off him inside a minute, offhand about it, and slides it across to Chloe. Ruth reads it upside down from across the table...`
- One clause added at the point the handoff actually happens, so "Ruth reads it upside down from across the table" now has a fixed point (in front of Chloe) to read across from, Nadia's later "turn the napkin round toward Chloe" reads as a re-angling rather than a first arrival, and "since Kavi passed it" (L149) is now a callback to something shown rather than a retroactive assertion.

## Nothing else flagged

No items were dropped or found to be non-problems on review; all nine went in as the smallest available fix.
