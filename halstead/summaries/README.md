# Chapter summaries

## What this folder is for

`STORY_SO_FAR.md` is one file: a short high-level recap of the whole book, one entry per chapter, so an agent can learn the story up to a point without reading the chapters. The `chNN.md` files (ch01 to ch36) are optional detail: scenes, facts established, who knows what, open threads.

## How to use it

- For work on chapter N, read the entries for chapters 1 to N-1 in `STORY_SO_FAR.md`. That is one short document, not many separate files.
- Optionally read `chNN.md` for a specific chapter you need more detail on.
- Read the chapter itself in `../chapters/` before relying on any detail that matters, and always before editing it.

## Staleness

The high-level recap in `STORY_SO_FAR.md` should rarely need updating, because it covers premise, people and the shape of the story rather than scene detail. The `chNN.md` detail files were generated from the chapters on 2026-10-23 and can drift after chapter edits. The chapters are the only source of truth (see CLAUDE.md), and no summary overrides a chapter. If a summary and a chapter disagree, the chapter wins.

## Possible continuity conflicts noticed while summarizing

Each was checked against the chapter text. Other apparent conflicts in the chNN.md files turned out to be summarizer errors or not conflicts, and are not listed.

1. Sam's age. Chapter 04: Sam says "I'm seven and a half. That's fine" in July 2012, which makes him about seven months older than Chloe (born August 2005, turning 7 that August). Chapter 20 (June 2022): Nadia says "That's thirty-four years of being in situations, against your sixteen". Chapter 36 repeats "you were sixteen" for the same night. On the chapter 04 count Sam would be 17 in June 2022.
2. Where Sam is in September 2023. Chapter 24 opens: "Sam is at a processing station somewhere the Army won't name, where they hand his phone back a few minutes at a stretch." Chapter 25 has him arriving at his training company by bus from the reception depot in the first week of August 2023 and qualifying in week ten, in October. By September he would be in training, not at a processing station.
3. What the rules document governs. Chapter 33 has Chloe write the rules document (limits, definition of "noticed," stop clause) for Eli's second tool, the one meant to read the government file. Chapter 35 opens "The financial worm goes quiet on a Thursday in June" and then tests that worm's logs against "Page five of the document", the definition of being noticed, and Ruth rereads "page seven" ("Any one of them can end it, no vote required") as "the document Chloe wrote". The same document is applied to the financial worm, which chapter 32 shows going live in late November 2025, before the rules were written. It is not stated whether the rules were extended to the first tool or whether the chapter 35 tool is the second one.
