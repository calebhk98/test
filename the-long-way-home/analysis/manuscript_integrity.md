# Manuscript / Build Integrity Notes

## 1. Em dashes survive in the COMPILED manuscript (minor, build-script sourced)
- The 53 chapter source files in `book/chapters/` contain **0 em dashes** (clean).
- The compiled `book/manuscript/The_Long_Way_Home.md` contains **8 em dashes**, and
  all 8 are in auto-generated PART/EPILOGUE headers, e.g. `## PART ONE — Arrival & Survival`.
- Source: `book/build_manuscript.py`, the `PARTS = {...}` dict (lines ~24-32) hard-codes
  the em dash in every part title; `build` emits them as `## {PARTS[num]}`.
- Net: the "no em dashes anywhere, no exception for titles" rule (same rule ch01's QA
  enforced on the chapter title) is violated 8 times in the shipped manuscript, purely
  from the build script. Fix is one search/replace in `build_manuscript.py`.

## 2. Chapter sources are the corrected canonical text
- ch01 title is fixed to `# Chapter 1: Waking` (the original em-dash QA blocker is resolved
  in the source). The chapter files reflect the post-QA fixes; the manuscript was rebuilt
  from them except for the part headers above.

## 3. "ACCEPTED" vs "REVISE" reconciliation (cross-agent result)
- chapter_list.md marks all 53 ACCEPTED; 19 QA files still read REVISE.
- The five chapter-range audits verified the REVISE blocking issues against current prose.
  Result: nearly all REVISE blockers were ACTUALLY FIXED in the prose (status flip is
  largely justified), with ONE confirmed exception:
  - **ch40 [MAJOR]: an unfixed banned correctio survives** — "...she said so to me one
    evening over the third copy, not as a complaint, as a figure" (~L71). QA flagged it;
    it is still live in the current prose.
