# Scene audit brief

The author worked chapter 1 through by hand and wrote up what he found. This
brief is that method, generalised. Follow it exactly. Chapter 1 is done and is
not your chapter.

## What you produce

One file, `passes/scenes/CHNN.md`, for the one chapter you own. You do not edit
the chapter. You do not edit anything in `chapters/`. Report only.

## Before you start

Read, in this order:

1. `CLAUDE.md` at the repository root
2. `passes/HOUSE_RULES.md` — rule 1 in particular
3. `passes/DO_NOT_FLAG.md` — every ruling in it is closed. Do not raise them.

## Two constraints on how you write

**Nothing concrete.** You are guessing at intent and you must sound like it.
Write *looks to*, *appears to*, *may be*, *what I think this is doing*,
*possibly*. Never write "The purpose of this is", "The exact reason is", "This
clearly shows", "The author is doing X here". You do not know. Say so in the
grammar of the sentence.

**No praise.** Do not tell the author a line is beautiful, strong, effective,
elegant, or working well. "No issue" is a permitted verdict. "This is excellent"
is not. If a sentence has nothing wrong with it, write "No issue" and move on.

## The work, in order

### 1. Scenes

Split the chapter into its scenes. For each one:

- A sentence or two on what appears to happen.
- **Content:** what happens, in order, flat and factual.
- **Possible purpose:** what the scene may be for. Hedged.
- **What I think it tells the reader:** hedged.

### 2. Every sentence, then every paragraph

Walk the scene paragraph by paragraph, numbered. For each, quote it and say
what is wrong with it, or "No issue". The things chapter 1 turned out to be
full of, in rough order of how often they appeared:

- **Narrator explanation.** The prose stating what it has already shown, or
  explaining a character to the reader. Chapter 1 had thirteen. Examples that
  were cut: *because it's still going*, *which Chloe knows*, *because she has
  been told to*, *so that bedtime runs long*, *working out which part was the
  wrong part*, *alone the whole time*, *which she is good at*. This is house
  rule 1 and it outranks everything.
- **Grammar and syntax defects.** Real errors, not style. Chapter 1 had about
  twelve: a list with no main verb, *while he types, the keys the only sound*
  (no verb), *sits in a smell of floor wax*, *cannot learn the rules of by
  watching* (dangling of), *puts his eyes back on the road*, pronouns with no
  antecedent (*and she counts them*), a missing conjunction.
- **Narrated speech that should be spoken.** *Her grandmother says well,
  somebody got grown up this year* became *"Well, somebody got grown up this
  year," her grandmother says.* Chapter 1 had six. Expect these everywhere.
- **Redundancy.** The same thing said twice a few sentences apart. *since the
  reading part is already fine. The reading is fine.*
- **Vague where it should be concrete** (*by a visible amount* → *by two
  inches*) and **falsely precise where it should be natural** (*about a minute
  and a half* → *under two minutes*). A number belongs in the prose when a
  person in the scene would have it, not when the narrator is measuring.
- **Missing staging.** Dialogue starting before the reader knows where they
  are, or an object referred to before it exists on the page.
- **Thin paragraphs.** A single-sentence non-dialogue paragraph given the
  visual weight of a whole beat.

### 3. Paragraph count

Count the paragraphs in the scene. Name the thin ones by number. Say which
should merge into which, and give the resulting count. Dialogue keeps the
new-speaker-new-paragraph rule; that is not negotiable and those stay.

Paragraphs should be cut to beats, not one every two sentences.

### 4. The chapter whole

After every scene: does each scene need to exist? Can any be combined, and if
so, how, concretely? Chapter 1 went from thirteen sections to five. Two scenes
doing the same job with the same character merge into one pattern rather than
two anecdotes. Say what a merge would look like, not just that one is possible.

Merging means writing something across the seam. Removing a section break and
butting two scenes together is not a merge. Say what carries across it — a time
cue already in the prose, an object that travels from one scene to the next, a
sensory bridge.

### 5. Check your own work

Go back over everything you have written and look for claims that are wrong,
quotes that do not match the file, counts that do not add up, and two notes
that contradict each other. Fix them. If you would rather have a second pair of
eyes, you may spawn one Haiku or Sonnet agent to read your notes and argue with
them; the author has authorised Haiku for this one role. Never Opus, for
anything, ever, in this repository.

Fabricated quotes are the failure that has done the most damage in this
project. Every quotation you print must be copied from the file. Check them.

### 6. Then write the Feedback section

Last section of the file, headed `## Feedback`. This is the part the author
acts on, so it is a list of changes, not an essay. Each entry:

    **"the old text, quoted exactly"**
    One or two sentences on what is wrong.
    Action: what to do.
    Replace with: "the new text"

Give two or three alternative new texts where you are not sure which is right.
Where the action is a deletion or a merge, say that instead of giving new text.

## Calibration you need before you start

The protagonist reads as autistic when she is written as rule-bound, and the
author does not want that. She should be a child with a strong sense of
fairness who reads social situations and sometimes gets them wrong, not one who
cannot process an inconsistent rule. In chapter 1 the fix was that she *knows*
another child cheated, and her confusion is about why nobody else minds.

She also reads wrong when she is too computational. *Chloe files that* was cut
for this reason. Six-year-olds do not file.

Masking, where it appears, is a skill she is learning across the book rather
than one she has. It should cost her something visible, and it should
sometimes fail. In chapter 1 the sequence is: she talks freely at dinner in
September, learns to compress herself in November, and by Christmas in December
is doing it to her own family. The variable is time, not who she is with.

The narration flags nothing, ever. It does not tell the reader what to think
about a scene, and it does not close a scene by explaining it.
