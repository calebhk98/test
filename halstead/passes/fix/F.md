# Fix report — F

All edits made in `chapters/`, then synced with `python3 sync_chapter.py chapters/NN_name.md` for each
of the five files. Each run printed exactly one destination (`-> HALSTEAD.md`) and no `!!` warning.

---

## chapters/22_the_offer.md

**1. L5 vs L61 (interview length contradiction)**
- Before: "He runs each one the full fifteen minutes, by the staff's own count, even the ones that could have ended in under a minute."
- After: "He runs most of them the full fifteen minutes, by the staff's own count, even the ones that could have ended in under a minute."
- Why smallest fix: the six-minute exit at L61 is load-bearing — Chloe's "Six?" and the reply about "already had the desk" pay it off immediately after. So the absolute claim had to give, not the scene. Swapping "each one" for "most of them" is a one-phrase change that keeps the sentence's point (he generally lingers) while allowing the one dialogue-anchored exception to stand.

**2. L23 (forge tenure)**
- Before: "gone back to the forge every Thursday for four years before anyone had to make her."
- After: "gone back to the forge every Thursday for five years before anyone had to make her."
- Why smallest fix: forge starts at twelve; this chapter is April 2023 with Chloe seventeen, so five years elapsed (going on six) since chapters/19_sixteen.md's correct "four years" a year earlier. One-word number change.

---

## chapters/23_the_first_one.md

**3. L104 (three forms / fourth form)**
- Before: "The recruiter slides three separate forms across the desk and starts explaining what each one means... but he reads the fourth form properly, twice, because it's the one about pay grade..."
- After: "The recruiter slides four separate forms across the desk and starts explaining what each one means... but he reads the fourth form properly, twice, because it's the one about pay grade..."
- Why smallest fix: the pay-grade detail on "the fourth form" is specific and worth keeping; changing the count word at the front (three→four) is the one-word fix rather than rewriting the payoff detail.

**4. L101 (that evening / already packing, booking)**
- Before: "That evening, before anyone's started packing anything, or booking anything, or signing anything, they are all still on the same patch of grass at the same time..."
- After: "That evening, before anyone's driven off, or said goodbye, or signed anything, they are all still on the same patch of grass at the same time..."
- Why smallest fix: Chloe's box is already packed and carried earlier that same day (L93-95), and Ruth's is "labeled and half packed before the ceremony even starts" (L107) — so "packing" and "booking" (Ruth is already on her third dorm call in this same paragraph) are false. "Signing" stays true and untouched (Sam doesn't sign until July, later in the same passage). Replaced only the two false items with two true, parallel ones, same triplet shape, same point (they're still together before anyone scatters).

---

## chapters/24_the_chat.md

**5. L5, L107, L552 (chat age: nine → five years)**
- Before: "The chat is nine years old." / "Their own encryption has gone nine years without anyone who had real reason to try it... the same nine years running." / "the same lock nine years running, untouched and unreplaced."
- After: "The chat is five years old." / "...gone five years without anyone... the same five years running." / "the same lock five years running, untouched and unreplaced."
- Why smallest fix: chapter is September 2023, cast is eighteen, encryption written at thirteen — five years, not nine. Number swap only, all three instances, nothing else in the sentences touched.

**6. L432 (Nadia: interviews → running her company)**
- Before: "Nadia is behind the counter more hours a week now than she's ever been, since none of the two months of interviews turned into anything worth taking. A regular customer asks her, not unkindly, when she's going to go do something with herself. She rings up his sandpaper and hands him his change."
- After: "Nadia is behind the counter fewer hours a week now than she used to be, since the company she started in June is three months in and already paying two people who aren't her. A regular customer asks her, not unkindly, when she's going to go do something with herself. She rings up his sandpaper and hands him his change."
- Also, the immediately-following chat exchange that was built on the false "job interviews" premise:
  - Before: `kavi: whats wrong with the jobs you interviewed for` / `nadia: theyre all two years behind where i already am. i sat through someone explaining margin to me`
  - After: `kavi: whats the headcount` / `nadia: two, so far. i sat through the bank explaining a business account to me like it was new information`
  - The rest of the exchange (guy-asking / sandpaper joke / "i would have said something" / "brutal" / "it was tedious, not brutal. brutal implies effort") was left untouched — it doesn't depend on the interview premise and still lands the same way off the new line.
- Why this scope: chapters/23_the_first_one.md:137 (June 2023 founding, hiring by September) and chapters/28_nadia.md:8 (forty people, eleven months old by May 2024, same June 2023 founding) agree with each other; this September 2023 chapter is the outlier and was the one flagged to fix. The brief explicitly said to read the surrounding Nadia material and rewrite it so she's running a young company, which is why the edit extends past the single narration line into the chat line it directly set up (Kavi's question and Nadia's answer) — the line right after it would otherwise still assert she was job-hunting. Kept her register: flat, no hedging, states a number first, no adjective on the tedium (matches "it was tedious, not brutal. brutal implies effort," which was left as-is and now lands on the bank story instead of the margin story). Nothing in chapters 23 or 28 was touched.

---

## chapters/25_nineteen.md

**7. L86 (most of a Saturday vs. three days)**
- Before: "She opens both countries' newspapers in adjacent tabs before noon and reads them against each other for three days before she writes a line."
- After: "...reads them against each other for hours before she writes a line."
- Why smallest fix: the paragraph frames the piece as one Saturday ("takes most of a Saturday," "before noon," "by midnight the piece runs past six thousand words"); "three days" was the one phrase off that scale. One-phrase swap, no other change to the paragraph.

**8. L278 ("she" → Ruth)**
- Before: "In April she stops posting. The chat keeps moving through May..."
- After: "In April Ruth stops posting. The chat keeps moving through May..."
- Why smallest fix: the paragraph follows a recurring device earlier in the chapter of Ruth periodically posting statistics questions to the chat ("She comes back to it. Nine days later:" / "Four days after that:" / "Three days after that:", all `ruth:` lines) — that's the posting habit this paragraph closes off, not Chloe's blog. Three lines later "Chloe reads both messages twice" about the disappearance confirms the vanished poster isn't Chloe. Named the pronoun, changed nothing else.

---

## chapters/26_ten_targets.md

**9. L74 (nineteen-year-old private → eighteen)**
- Before: "The fourth asks where a nineteen-year-old private learned to do it,"
- After: "The fourth asks where an eighteen-year-old private learned to do it,"
- Why smallest fix: Sam is born January 2005 (characters/SAM.md); chapter is November 2023, so he's eighteen throughout. Number swap plus the required article change (a → an).

**10. L14 (deleted per author instruction)**
- Before: "He does that with everything. There's no version of a task anywhere in Sam's head where he reaches a number, decides that's enough, and stops there. By week nine his file has a lot of numbers in it and somebody has started printing them out."
- After: "He does that with everything. There's no version of a task anywhere in Sam's head where he reaches a number, decides that's enough, and stops there."
- Why: cut, not repaired, per the brief. The paragraph now ends cleanly on "...stops there." and the following section break is unaffected.

---

## Notes

Nothing else in these five chapters was touched. No item on the list turned out to be a non-problem —
all ten checked out as described once read in context.
