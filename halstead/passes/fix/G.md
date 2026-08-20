# Fix report — G

## chapters/29_the_exercise.md

**Quote before:** "because three separate two-and-fours over four days is a lot of walking for not much."

**Quote after:** "because a two, a four, and a one over four days is a lot of walking for not much."

**Why smallest fix:** The chapter gives exactly three contacts: a two-man fence line (L14), a four-man culvert (L17), and a lone man on bad ground (L20). "Three separate two-and-fours" miscounts the third as another pair. Swapped in the actual sizes as a number-first list, which matches Sam's dial (states a number before the point, flat clause, no subordinate qualifier) rather than adding an explanation of the discrepancy.

## chapters/30_cleared.md

**Quote before:** *September 2025 – January 2026*

**Quote after:** *February 2025 – January 2026*

**Why smallest fix:** L42's seven-month investigation has to finish by the "autumn" clearance in L95, which lands before the January start in L97 — so the investigation must begin around February 2025, six months before the old dateline's September 2025 open. Opened the dateline to February 2025 per the brief's own math and stated preference for changing the dateline over shortening the seven-month duration referenced in the body. Left the body text untouched.

## chapters/32_the_money.md

**Quote before:** "The financial one takes eleven weeks."

**Quote after:** "The financial one takes sixteen weeks."

**Why smallest fix:** A month of testing (L11, ~4.3 weeks) plus "the following two months" of results (L31, ~8.7 weeks) already total ~13 weeks before Ruth even starts building the proof, so eleven weeks couldn't hold. Sixteen weeks clears that ~13-week floor with room for the proof-building and closing chat, and still fits inside the chapter's own November 2025 – February 2026 dateline (~15–17 weeks). Only the top-line figure changed; L11 and L31 are untouched.

## chapters/35_nine_minutes.md

**Quote before:** "He pulls the logs."

**Quote after:** "Eli pulls the logs."

**Why smallest fix:** Third paragraph, no person named yet. Eli is the one who built the tool in question (ch. 32: "Eli builds it") and is the first to post a diagnosis in the chat that follows, so naming him here is a one-word fix that doesn't require touching anything else in the scene.

**Quote before:** "which has three wrong answers on file and no idea that seven people in their twenties settled it in eleven weeks."

**Quote after:** "which has two wrong answers on file and no idea that seven people in their twenties settled it in sixteen weeks."

**Why smallest fix:** "three wrong answers" contradicted Theo's own count in chapter 32 ("theyve been wrong twice and theyre still wrong"), with nothing between the chapters adding a third; changed to "two" to agree with chapter 32, per the brief's instruction to fix chapter 35 rather than chapter 32. "Eleven weeks" is the same figure corrected in chapter 32 above; updated to "sixteen weeks" so the two chapters agree.

## Mechanical

Ran `python3 sync_chapter.py` on all four files individually. Each reported writing only to `HALSTEAD.md` (none of these chapters live in `MANUSCRIPT_FULL.md`, `CHAPTERS_16_22_v2.md`, or `CHAPTERS_23_30_v2.md`, since those cover an earlier chapter range). No `!!` warnings on any file. Verified all five changed lines are present in `HALSTEAD.md` after sync.

## Nothing else flagged

No additional problems noticed in the assigned passages beyond what was on the list.
