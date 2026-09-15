# Fix pass E — chapters 17, 18, 19

All edits made in `chapters/` and propagated with `python3 sync_chapter.py` to
`MANUSCRIPT_FULL.md` and `HALSTEAD.md` (the script reported no `!!` warnings for
any of the three files).

## chapters/17_fourteen.md

### L167 — recap paragraph timeline + "could not stand up"
**Before:** "Sam grew four inches over the summer and there is a pencil mark on a door frame about it. Sam had a girlfriend and then did not. Ruth built a thing that makes sound out of nothing, and Chloe was on the floor of her room at one in the morning helping her find forty milliseconds. She teaches now. She has seven of them and she taught one thing to all seven of them backward and had to go in and say so. She held fifty seconds against ten people on a Tuesday and could not stand up afterward. There is a boy called Ferris who does everything the long way round and gets there every time. Japanese, four months of it. Abstract algebra, contracts, logistics, the fracture tests, her name in the back of a paper, a clamp that closes on the wrong axis, three hinges in a bin."

**After:** "Sam grew four inches over the summer and there is a pencil mark on a door frame about it. Sam had a girlfriend. She teaches now. She has seven of them and she taught one thing to all seven of them backward and had to go in and say so. There is a boy called Ferris who does everything the long way round and gets there every time. Japanese, four months of it. Abstract algebra, contracts, logistics, the fracture tests, a clamp that closes on the wrong axis, three hinges in a bin."

**Why:** cut the four future-dated items (Ruth's sound project — spring; "could not stand up" — Feb, and factually wrong regardless; the fracture-tests acknowledgment — March) rather than move the scene, since the scene's own "Winter break" dating and the later "she calls home... through January... March... April" timeline anchor it in place. "Sam had a girlfriend and then did not" is trimmed to "Sam had a girlfriend" — true as of winter break, since the relationship started in October; the breakup clause is what was future. Cutting the "fifty seconds... could not stand up" sentence entirely also resolves the separate contradiction with L57 ("Chloe gets her feet under her on the third attempt") in the same stroke, since that whole sentence is gone.

### L131-139 — untagged exchange, Kavi addressed but never seated
**Before:**
> "How did he actually ask her?"
>
> "He said, 'Do you want to do something?' And she said, 'What?' And he said he didn't know yet."
>
> Ruth puts her fork down and leaves it down. [...]
>
> "He's got a lake, Kavi. A lake and a boat shed."

**After:**
> "How did he actually ask her?" Kavi asks.
>
> "He said, 'Do you want to do something?' And she said, 'What?' And he said he didn't know yet," Odile says.
>
> Ruth puts her fork down and leaves it down. [...]
>
> "He's got a lake, Kavi. A lake and a boat shed," Priya says.

**Why:** tagging the first line to Kavi seats him in the scene as an actual present speaker, so Priya addressing him by name two lines later is no longer addressing an absentee. Tagging the second line to Odile (established elsewhere in this chapter) brings the recoverable participant count to four (Priya, Kavi, Odile, Ruth), matching the brief's "at least four participants." No dialogue content was changed, only attribution.

### L193-195 — untagged line
**Before:** "That's a hold. That is a hold, that's been a hold all night."
**After:** "That's a hold. That is a hold, that's been a hold all night," her mother says.
**Why:** smallest possible fix — one tag, on the character the scene already points to (she's the one who just sat on the arm of the chair to watch the game).

## chapters/18_fifteen.md

### L33 — leg-counting age
**Before:** "...the way it did when she was nine..."
**After:** "...the way it did when she was eleven..."
**Why:** matches chapters/14_sixty_degrees.md, where the leg-counting habit is established and Chloe is eleven; chapter 12 ("Nine") has no leg-counting to anchor "nine" to.

### L37 / L41 — "same place" vs. four different values, and "started at forty or twelve" vs. "everyone started at zero"
**Before (L37):** "The curve flattens in the same place for all eleven, whether they started at forty or at twelve."
**After (L37):** "The curve flattens into the same narrow band for all eleven, whether it took them forty sessions or twelve."

**Before (L41):** "Eleven of us stopped in the same place and it doesn't matter where we started."
**After (L41):** "Eleven of us stopped in the same narrow band and it doesn't matter where we started."

**Why:** "narrow band" replaces "same place" in both the narration and the echoing dialogue line, since the data given (60/58/55/63) is a spread, not one value. In L37, "started at forty or at twelve" is reassigned from initial score (which contradicts L11 — everyone starts at zero) to number of sessions taken to reach the plateau, which both keeps the two numbers and removes the contradiction.

### L119 vs L107 — "sold four" vs. "turning over"
**Before:** "...and he had already sold four."
**After:** "...and he already had four turning over."
**Why:** makes Chloe's claim the same claim as L107's "four of which are turning over by Christmas" — running motors, not sold ones.

### L117-125 — loan figure pivot
**Before:** "How much of it could you have lost?" / "Thirty." / "Thirty dollars, across nine months."
**After:** "How much of it could you have lost?" / "A hundred and twenty." / "A hundred and twenty dollars, across nine months."
**Why:** the whole rebuke up to this point is about the Rustem loan specifically; $120 is the amount actually at risk on that loan (L109), not the $30 that belongs to the separate, unsecured Priya loan. Fixing the figure (two spots) was smaller than inserting a marked pivot to a second loan mid-rebuke.

### L145 — Sandoval double-counted
**Before:** "Then she builds the other one, from Sandoval's side, and from her own, and from the side of the four names on the form."
**After:** "Then she builds the other one, from her own, and from the side of the four names on the form."
**Why:** L139 already establishes Sandoval as one of the four signatories, so naming her separately double-counted her. Cut the redundant clause; "the four names on the form" still covers her.

### L115 — blocking ("her" ambiguity)
**Before:** "Hark has her at the board in April with the ledger written up. She stands at the back with her arms folded and reads all three columns before she says anything."
**After:** "Hark has her at the board in April with the ledger written up. Hark stands at the back with her arms folded and reads all three columns before she says anything."
**Why:** the unresolved pronoun "She" in the second sentence read as continuing the subject of the first (Chloe, at the board), which contradicts "at the back" and L127 ("Chloe wipes the board and sits down"). Naming Hark explicitly resolves it in one word and matches L125, where Hark "comes across the room" from the back toward the front row as she talks.

## chapters/19_sixteen.md

### L105 — Pruitt summary vs. the following three lines
**Before:** "...in four years the whole of his commentary has been telling her which end to hold."
**After:** "...in four years the whole of his commentary has come to a handful of sentences."
**Why:** the three Pruitt lines that immediately follow are about her schedule, not metal, so the old claim was disproved in the next breath. Fixed the narrated summary rather than touching Pruitt's dialogue, per the brief — his three lines stay exactly as written.

### L131 vs L135 — the glass
**Before:** "...then gets up, takes the empty glass with her, and goes back inside."
**After:** "...then gets up and goes back inside."
**Why:** removing the mother's glass-removal is the smaller fix than inventing a refill; the glass stays with Chloe throughout, consistent with L135's "Chloe has the glass on the step beside her."

### L163 — father's ungrounded glass, and "the two of them"
**Before:** "Her father turns his glass a quarter round on the step, and then asks her what the two of them are like at a table together now, a question that stops her with the glass halfway up."
**After:** "Her father asks her what Priya and Nadia are like at a table together now, a question that stops her with the glass halfway up."
**Why:** cut the father's glass, since he's never given one in this scene (only Chloe's iced tea, from L127, is established — the "the glass" at the end of the sentence is hers and is left untouched). Named the two under discussion as Priya and Nadia, since they're the live topic of the two lines just before (the negotiation board, Priya letting Nadia have it).

### L33 — cohort total
**Before:** "Fifty-one in the year pass and thirty-nine do not..."
**After:** "Fifty-two in the year pass and thirty-nine do not..."
**Why:** 52 + 39 = 91, matching the cohort size used everywhere else in the manuscript (graduation count, Ruth's "I'm on ninety-one," the ninety-one-name file). Changed the pass count rather than the fail count so L97's "the retake for the thirty-nine who failed" stays correct without a second edit.

### L101 — October pass needs a beat
**Before:** "She passes by twenty-two."
**After:** "She passes by twenty-two, and she reads the number twice before she puts the page away."
**Why:** small, flat, no celebration — a checking/verifying beat consistent with how Chloe is shown handling numbers elsewhere in the book (rereading marks, rereading papers), giving the retake's resolution a beat without restaging the April corkboard scene.

### L151 — "the maps"
**Before:** "...so she tells him about Kavi and the maps, and then about Priya..."
**After:** "...so she tells him about Kavi, and then about Priya..."
**Why:** "the maps" has no antecedent anywhere in the chapter; cutting it was smaller than inventing one.

## Notes

- Nothing else in these three chapters was touched.
- No item turned out to be a non-problem on inspection; all sixteen items were fixed as described above.
- All `sync_chapter.py` runs completed cleanly (no `!!` warnings); verified by grep that the new text appears correctly in both `MANUSCRIPT_FULL.md` and `HALSTEAD.md`.
