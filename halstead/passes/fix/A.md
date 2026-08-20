# Fix report — A

Four chapters, eight items to fix plus one flagged as too large. All edits made in `chapters/` and
synced via `sync_chapter.py`; each run printed only the two expected write targets
(`MANUSCRIPT_FULL.md`, `HALSTEAD.md`), no `!!` warnings.

## chapters/01_before.md

**L41 — food-prompt count**
- Before: `"She had to be told three times to eat, because she couldn't do both," her mom says into the phone, laughing.`
- After: `"She had to be told twice to eat, because she couldn't do both," her mom says into the phone, laughing.`
- The scene gives exactly two prompts ("Eat something," L35; "Two more bites and then the last part," L39); changed the number rather than adding a third prompt, per the brief's stated preference.

## chapters/03_the_letter.md

**L7 — contradicted "nobody has ever sent Chloe anything"**
- Before: `Nobody has ever sent Chloe anything, though her grandmother sends a card at Christmas with her name written inside it in pen, on an envelope whose outside says her parents.`
- After: `Nobody has ever sent Chloe anything with her name on the outside, though her grandmother sends a card at Christmas addressed to her parents, with a card for Chloe inside it.`
- Narrows the claim to "with her name on the outside" and recasts the grandmother's card as addressed to the parents with a card for Chloe inside it, matching the author's stated fix exactly.

**L10 — dangling "it"**
- Before: `...and where somebody has typed her name on the front of it.`
- After: `...and where somebody has typed her name on the front of the envelope.`
- Supplies the noun; "it" was grammatically reaching for the camp in the preceding "where" clauses instead of the envelope.

**L125 — dangling "it"**
- Before: `"Okay." Chloe stands there doing something else with it. "Can you keep one out for four weeks? So it doesn't go late."`
- After: `"Okay." Chloe stands there doing something else with the argument. "Can you keep one out for four weeks? So it doesn't go late."`
- "The argument" is already established at L120 ("Chloe has the argument ready"), so this reuses an existing noun already in play rather than introducing a new one, and reads as her pivoting to a different angle on the same request.

**L101 — "It takes them nine days" vs. the weekday sequence — NOT FIXED, needs a larger change than the brief allows**
- Left unedited: `It takes them nine days.` (and the following "the fourth day, the sixth day, and the eighth" / "the ninth night" sequence)
- Traced the weekdays in order: Sunday (L39, day 0) → Monday (L41, day 1) → Thursday (L44, day 4) → Saturday (L49, day 6) — consistent with a single week, and consistent with "forgets to ask again for four days" landing on the Thursday. But the next weekday, "a Friday" (L77), is narrated *after* that Saturday and tied to the same call ("that night"), so it can only be the *following* Friday (day 12, not day 5) — within any 9-day window that starts on the first Sunday, Friday necessarily falls *before* the next Saturday, never after it. "The Sunday" at L85 (mom's own research) then follows that Friday, landing at day 14. So the weekday markers alone already require at least 14 days before the "fourth day / sixth day / eighth / ninth night" argument countdown even begins — and that countdown is internally self-consistent (ninth night = the resolution), so it can't simply be moved earlier without also renumbering "fourth," "sixth," "eighth," and "ninth" throughout the same paragraph, plus possibly retiming L77/L85. That's a multi-sentence, multi-number rewrite, not a one-word or one-clause fix, so per the brief's own overreach test I stopped and am reporting it here instead. What I'd do: either (a) change "nine days" to something in the 20s to cover the full span and renumber "fourth/sixth/eighth/ninth" to match, or (b) move the Friday/second-Sunday beats earlier in the week (contradicting their own "that night" continuity with the Saturday-anchored school call) so the whole thing closes inside nine days. Neither is a small edit; left the text alone pending author input on which restructuring they want.

## chapters/04_pluto.md

**L69 — Pluto reclassification predates Chloe's birth**
- Before: `"Since before I was born," Chloe says, and her mom laughs at it anyway.`
- After: `"Since before I can remember," Chloe says, and her mom laughs at it anyway.`
- Same length, same voice, and now a claim a six-year-old could hold correctly (Pluto was reclassified in August 2006, after Chloe's August 2005 birth, but well before she'd remember anything).

**L42 — planet corridor skips three planets**
- Before: `Mercury, Venus, Earth, on little brass plates screwed in beside the doors at adult height, then Mars, then Jupiter. Then a water fountain, then one more door past the fountain at the very end, with a plate on it that says PLUTO.`
- After: `Mercury, Venus, Earth, on little brass plates screwed in beside the doors at adult height, then Mars, then Jupiter, then Saturn, Uranus, Neptune. Then a water fountain, then one more door past the fountain at the very end, with a plate on it that says PLUTO.`
- Adds the three missing planets in the same "then X" list shape already used for Mars and Jupiter — no new sentence, no elaboration.

**L30 — "how far" missing its object**
- Before: `Chloe sleeps in the second bed with the bathroom light on and the door open, her mom asking first how far, one hand pressed flat against the spare pillow that smells like the hotel's detergent and not their own.`
- After: `Chloe sleeps in the second bed with the bathroom light on and the door open, her mom asking first how far to leave the door open, one hand pressed flat against the spare pillow that smells like the hotel's detergent and not their own.`
- Attaches "how far" to the door already named earlier in the same clause (light/door being the two things just set for the night), rather than introducing an unrelated object.

## chapters/05_behind.md

**L87 — fact count goes three then two, with only one fact named**
- Before: `going back through the same three facts: Owen must not have liked the bridge, and the two facts sit crosswise, and neither one will move over for the other.`
- After: `going back through the same two facts: the bridge was fun, and Owen must not have liked it, and the two facts sit crosswise, and neither one will move over for the other.`
- Changed "three" to "two" to match the "the two facts" already in the sentence, and split the single stated conclusion ("Owen must not have liked the bridge") into the two facts actually in tension: the bridge was fun (established at L76, "We broke the bridge yesterday... mine went at the corner") against Owen having left because he wasn't having fun (L70-73).

**L36 — unparseable sentence about the fraction lesson**
- Before: `Then the pieces stop being pieces of the thing they were pieces of, and after that she is looking at a rectangle with lines in it.`
- After: `Then she loses track of what the pieces are pieces of, and after that she is looking at a rectangle with lines in it.`
- One clause swapped for a plain, parseable one; keeps "a rectangle with lines in it" as the payoff image, but now the sentence states outright that she's lost the connection between the diagram and what it represents.

## Notes

Everything above was on the list; nothing else in these four chapters was touched. Item 03_the_letter.md
L101 is the one exception noted above — flagged rather than force-fixed, since closing it correctly
touches several numbers across more than one sentence.
