# Expansion brief — the short chapters

Ten chapters in the last third of the book run between 150 and 800 words. The rest of the book runs
2,000 to 4,600. They are not short because their events are small; they are short because they were
drafted in summary and never opened out. Your job is to write the missing scenes.

**Target: 2,000–3,000 words.** Roughly triple to five times what is on the page. This is a real
writing job, not a padding job.

## What to add

**Scenes, in place of the sentences that report them.** The chapters currently say things like "the
captain files it as a concern" and "they test it for a month." Find the moments the summary skips
over and write them: the room, the people in it, what is said, what is done with hands. A paragraph
that summarises three weeks is usually one good scene plus two sentences.

**The people who are already there but off the page.** These chapters name colleagues, officers,
roommates, clerks, and then never let them speak. Give them lines. Check `characters/` for anyone
with a sheet, and stay inside it.

**Physical staging.** Several of these chapters have conversations happening nowhere — no room, no
furniture, no bodies. That was one of the largest findings of the last review pass. Put them
somewhere.

**Time actually passing.** Where the text jumps a month in a clause, use the month.

## What not to add

**No new plot.** Nothing that changes what happens, who knows what, or when they learn it. The
events of the chapter are fixed. You are showing them, not adding to them.

**Do not explain the school.** Halstead's methods, selection, and reasons stay unexplained. If a
character would plausibly wonder about them, they can wonder; nobody answers.

**No new named characters** unless the chapter already names them.

**Do not restate.** If the text already establishes something, the new material assumes it. Two
paragraphs doing one job is the defect this pass is supposed to remove, not create.

## How it has to read

**Write at the level, not flat.** These are the adult chapters. The book's median is a Flesch-Kincaid
of 5.5 and about 945L; chapters 21 to 24 and 28, which are the strongest of the late run, sit at 1000
to 1170L. Aim for that end. Longer sentences with real subordination, precise vocabulary, and varied
length — not short declaratives in a row.

Measure yourself before and after:

    python3 prose_grade.py --summary chapters/NN_name.md

Your chapter should not come out flatter than it went in. Watch `w/sent`, `sl CV`, `F-K`, `Lexile`
and `simple`.

**No negative space.** The manuscript has a standing problem with people not-doing things: "she
doesn't look up," "nobody says anything," "he never asks." Write what a person does. The `neg%`
column measures this; do not raise it.

**Do not talk down to the reader.** Never add a clause explaining what the reader can already work
out, and never tell them what to conclude about a character. The narrator reports; it does not
interpret.

**Match the character sheets.** Read `characters/NAME.md` for everyone who speaks. Ruth names the
person she is correcting. Kavi is three words or one unbroken technical run. Sam is one flat clause,
and his one permitted image is the deflating literalism. Chloe builds a concrete parallel scenario
and argues that. Nadia is exact rather than loud.

**The cast is competent and has stopped being frightened of things.** Years of training have burned
the adrenaline out of them. Calm after violence is characterisation, not a missing beat. Do not add
fear they would not feel — and equally, do not make them cold. They are funny with each other, they
argue, they like each other.

## Mechanics

`chapters/` is derived. After editing, run

    python3 build_manuscript.py

which writes back into `MANUSCRIPT_FULL.md` and `HALSTEAD.md`. Report any `!!` warning.

Chat-transcript chapters use `name: text` lines. Those are cheap words and the metric script strips
them before grading, so a chapter padded with chat will not move. Prose is what counts.

## Report

Write to the path you are given: the before and after word counts, the before and after metric line,
what scenes you added and where, and anything you decided against adding and why.
