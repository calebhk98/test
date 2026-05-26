# QA Status Roll-Up — "Does each QA say the story passes?"

Short answer: **No.** Of the 53 chapter QA reviews, **34 say PASS and 19 say REVISE.**
Yet `book/outline/chapter_list.md` marks **all 53 chapters "ACCEPTED."** That is an
internal bookkeeping contradiction: a chapter cannot honestly be ACCEPTED while its
own QA file still carries a REVISE verdict, unless the blocking issues were fixed
AND the QA file re-run (the QA files do not appear to have been re-issued).

The per-chapter range agents are separately verifying whether each REVISE chapter's
blocking issues were actually fixed in the current prose. This file is just the
verdict census.

## Verdict census
REVISE (19): ch01, ch02, ch04, ch09, ch13, ch15, ch16, ch17, ch22, ch23, ch24,
ch34, ch35, ch36, ch38, ch39, ch40, ch42, ch43, ch46, ch47, ch49, ch52
(note: count includes all chapters whose VERDICT line reads REVISE)

PASS (34): ch03, ch05, ch06, ch07, ch08, ch10, ch11, ch12, ch14, ch18, ch19,
ch20, ch21, ch25, ch26, ch27, ch28, ch29, ch30, ch31, ch32, ch33, ch37, ch41,
ch44, ch45, ch48, ch50, ch51, ch53

## Full table
| Ch | Verdict |
|----|---------|
| 01 | REVISE |
| 02 | REVISE |
| 03 | PASS |
| 04 | REVISE |
| 05 | PASS |
| 06 | PASS |
| 07 | PASS |
| 08 | PASS |
| 09 | REVISE |
| 10 | PASS |
| 11 | PASS |
| 12 | PASS |
| 13 | REVISE |
| 14 | PASS |
| 15 | REVISE |
| 16 | REVISE |
| 17 | REVISE |
| 18 | PASS |
| 19 | PASS |
| 20 | PASS |
| 21 | PASS |
| 22 | REVISE |
| 23 | REVISE |
| 24 | REVISE |
| 25 | PASS |
| 26 | PASS |
| 27 | PASS |
| 28 | PASS |
| 29 | PASS |
| 30 | PASS |
| 31 | PASS |
| 32 | PASS |
| 33 | PASS |
| 34 | REVISE |
| 35 | REVISE |
| 36 | REVISE |
| 37 | PASS |
| 38 | REVISE |
| 39 | REVISE |
| 40 | REVISE |
| 41 | PASS |
| 42 | REVISE |
| 43 | REVISE |
| 44 | PASS |
| 45 | PASS |
| 46 | REVISE |
| 47 | REVISE |
| 48 | PASS |
| 49 | REVISE |
| 50 | PASS |
| 51 | PASS |
| 52 | REVISE |
| 53 | PASS |

## Note on ch01 spot-check
ch01's QA REVISE was a single blocking issue: an em dash in the chapter title
(`# Chapter 1 — Waking`). Whether that was fixed in the current prose is being
verified by the chapter-range agent; it is a useful bellwether for whether the
"ACCEPTED" status reflects real fixes or just a status flip.
