# Chapters 25–29 renumbered into chronological order

The printed datelines on line 3 of every chapter from 20 onward put five chapters out of sequence.
Chapters 20–24 ran in order and 30–35 ran in order; the block between them did not. Chapter 27 sat
two years ahead of the two chapters printed after it.

The block has been reordered to match its own dates. File contents are unchanged apart from the
chapter number and word in each header.

| was | is | title | dateline |
| :-- | :-- | :-- | :-- |
| 26 | **25** | Ten Targets | November 2023 |
| 29 | **26** | The Exercise | February 2024 |
| 28 | **27** | Nadia | May 2024 |
| 25 | **28** | Nineteen | September 2024 – April 2025 |
| 27 | **29** | The File | October 2025 |

The whole run now reads forward: ch24 September 2023 → 25 November 2023 → 26 February 2024 →
27 May 2024 → 28 September 2024–April 2025 → 29 October 2025 → 30 September 2025–January 2026.
Chapter 30 opens a month before 29 closes, which is a span chapter overlapping a point chapter and
not an ordering fault.

## What this invalidates

Every `chapters/NN_*.md` path in `characters/`, `chronology/`, the top-level documents and
`passes/D_FINDINGS.md` was updated mechanically and is correct.

**Prose references by number were not.** Sentences like "Chapter 27's 'six years ago'" in
`chronology/BOOK.md`, `chronology/RUTH.md`, `chronology/RUTH_MIT.md`, `chronology/CALENDAR.md` and
`BETA_NOTES.md` still use the old numbers, and they were left alone deliberately: those documents
argue *about* the old ordering, and renumbering their prose would leave the arguments intact while
making them describe something that is no longer true. Read them against this table. The chapter
each one means is the **was** column.

Reports under `passes/d/` and `passes/fix/` are dated artifacts of the old numbering and are not
being updated at all.
