# Fix brief — sections 1–4 of passes/D_FINDINGS.md

You are making small, surgical corrections to a novel manuscript. Every item you are given has
already been verified against the file and approved by the author. You are not reviewing, not
looking for more problems, and not improving anything you were not asked about.

## The rules

**Fix only what is on your list.** If you notice something else wrong, write it at the bottom of
your report and leave the text alone. An unrequested edit is worse than the defect it fixes, because
nobody asked for it and nobody will be looking for it.

**Make the smallest change that closes the problem.** A wrong number becomes the right number. A
dangling pronoun gets its noun. An untagged line gets a tag. Most of these are one word or one
clause. If your fix runs past a sentence, you have almost certainly overreached — stop and say so in
the report instead.

**Match the prose you are editing.** Read the paragraphs on either side first. Same register, same
sentence length, same vocabulary. Your sentence should be invisible next to its neighbours.

**Do not narrate the fix.** Never add a clause explaining a thing the reader can now work out. The
manuscript has a standing problem with over-explanation and with telling the reader what to
conclude; do not add to it.

**Do not use negative space.** The manuscript has a standing problem with characters not-doing
things: "she doesn't look up," "nobody says anything," "he never asks." It was flagged as appearing
several times per paragraph. Write what a person does, not what they fail to do.

**Match the character.** Before you put words in anyone's mouth, read `characters/NAME.md`. Ruth
names the person she's correcting. Kavi is three words or one unbroken technical run. Sam is one
flat clause. Chloe builds a concrete parallel scenario. Getting a tag right means getting the voice
right, not just attaching a name.

**Ages matter.** These children are six and seven in the early chapters. Read
`characters/CHLOE.md`, section "The thing to get right first," before you write a line for a young
Chloe. She does not know she is gifted, she thinks the defect is hers, and with her friends and her
parents she is open, loud and enthusiastic.

## The mechanical part, which is easy to get wrong

`chapters/` is the source of truth and the only place you edit. `HALSTEAD.md` is generated from
it. After editing, run

    python3 build_manuscript.py

which rebuilds `HALSTEAD.md` from `chapters/` in filename order. It refuses to run if the chapter
numbers have gaps or duplicates, or if a chapter's heading disagrees with its filename. Report
anything it complains about.

Nothing goes the other way. The script that regenerated `chapters/` from a manuscript file has been
deleted, because running it discarded work.


Check the paragraph convention before you count lines. Chapters 1–6 put every paragraph on one line
ending in two trailing spaces, with no blank lines between them; 7 onward use blank-line paragraphs.

    grep -c '  $' chapters/NN_name.md

Line numbers in your list came from `cat -n` and will shift as you edit. Re-grep for the quoted text
rather than trusting a line number after your first change.

## Your report

Write to the path you are given. For each item: the quote before, the quote after, and one line on
why that was the smallest fix. If you decided an item needed a larger change than the brief allows,
say what you would do and leave the text unedited. If an item turns out not to be a problem when you
read it in context, say that and leave it alone — that has already happened repeatedly on this
manuscript and reporting it is more useful than forcing a fix.
