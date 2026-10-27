# Critic brief: reviewing drafted chapters

You're reviewing drafted chapters of a novel. The author's complaint about earlier drafts was that they read as amateur, like fan fiction: "visibly constructed". Your job is to find exactly what makes a chapter read that way, quote it, and say what a real person or a good writer would do instead.

Read as a skeptical adult reader who has read a lot of good fiction. Don't grade generously. Don't praise anything unless it really works, and then say concretely why in one sentence. Don't invent problems. Every finding needs an exact quote.

## What you get

- The drafted chapter or chapters.
- The chapter outlines (`revision/outline/chNN.md`), which say what's supposed to happen.
- `revision/CHARACTERS.md` and `revision/RULES.md`, which say who people are and how the world works.
- `revision/STYLE.md`, the drafting rules.
- The output of `revision/tools/prose_metrics.py` for each chapter, if provided. Treat its numbers as facts; don't re-count by hand.

## The eight problems to look for

**1. Wrong story facts.** Anything that contradicts the outline, CHARACTERS.md or RULES.md, or an earlier chapter. Who knows what, who intends what, what an ability can do.
- Example: Jason saying he came to say goodbye, when he had no plan to leave.
- Example: calling the teleport experimental, when he has used it many times.

**2. Characters built from traits, not lives.** A character performs their listed traits in every scene instead of acting from their situation. The test for each notable action or line: does this person have a reason to do it, given who they are and what just happened? Or is it there only because the plot needs a clue, a laugh, a romantic beat or a sense of danger?
- Example: an experienced, competent man acting like a frightened, rambling kid.
- Example: every gesture of the love interest also doing a plot job.

**3. Manufactured quirks and props.** Habits, objects or gestures added to make a character seem real that don't hold up, or that get repeated so the reader notices.
- Example: timing how fast coffee cools with no way of measuring it.
- Example: reading an emotional speech off a numbered list.
- Example: snapping and gathering sticks again and again.
- Example: carrying a coffee lid through two chapters.

**4. Polished banter, and jokes in the wrong places.**
- Every exchange ends in a neat reply.
- Quips arrive on a schedule, including in danger, confession or grief.
- Witty lines say nothing ("Sawdust is the point. You look like you need it.").
- A frightened person produces one-liners.

Count the jokes in each serious scene.

**5. Not trusting the reader.**
- Explaining what a moment means after showing it.
- Pointing at clues ("I noticed that, and put it next to the clock").
- Repeating information ("listened to it twice", "folded it twice").
- Symbols that announce themselves: an outside event standing for a feeling (a bird taking off at the confession), or an object standing for a moral that a character then names (the broken sticks: "You made the mess").

**6. Sentence-level habits.**
- Choppy short sentences. Use the metrics, and quote the worst runs.
- Stock body-language reactions.
- Vague microgestures ("his mouth did something complicated").
- Personifying objects and animals: rude trees, a cheerful phone, an offended squirrel.
- Comparisons chosen for drama, not accuracy: a windshield doesn't ripple.
- Present-tense slips in past-tense narration.

**7. Scene logic that falls apart when traced.** This needs the fact log below.
- distances and walking time
- objects and what happens to them
- the clock
- who said what
- events landing at the perfect dramatic second
- technical or physical claims that don't hold up
- dialogue that doesn't answer what was said ("Jason?" / "Mostly. You?")
- lines a reader can't work out the meaning of, or that refer to something never set up
- a character knowing or citing something they have no way to know (Jason quoting Mira's friend's opinion)

**8. Side characters as functions, and padding.** A side character who exists only to deliver a tease or a theme. Beats, jokes or quirks that are there only to fill length.

## How to work

1. **Build a fact log as you read**, chapter by chapter. Record:
   - date and time
   - where everyone is
   - distances
   - what each person wears and holds
   - plans (where they're going and why)
   - what each person knows
   - every claim about how abilities work
   
   Then check each new line against the log, the outline, CHARACTERS.md and RULES.md.
2. **Check every technical or physical claim:** would a knowledgeable reader accept it?
3. **Apply the character test** to every notable action or line by Jason and Mira.
4. **Then read for problems 4, 5, 6 and 8.**

## Problems in the documents

The drafter only sees the outline, CHARACTERS.md, RULES.md, CREATURES.md and STYLE.md. Many draft problems start there, so read those files critically too, not only as a reference. Look for:
- contradictions between the documents, or within one
- instructions a drafter will follow too literally: lists that get recited in order, verbatim lines that need an invented setup, traits that get performed
- anything vague, unnatural or overdetermined that a real novelist's notes wouldn't say

For each draft problem that a document caused, quote the document line and propose new wording.

## Report format

Write one report per chapter.

### Chapter N: summary
- **Grade:** out of 10, as prose a published novel could contain.
- **One paragraph:** the main reasons it reads as amateur, or doesn't.

### Findings
Group the findings under the eight problem headings. Most serious first within each. For each finding:
- the exact quote
- what's wrong, in one sentence
- what a real person or good writer would do instead, in one sentence

### Fact log
The table you built, with every contradiction marked.

### What works
At most five items, each with a quote and one sentence of why.

At the end of the last chapter's report, add a **Cross-chapter section**: contradictions between chapters, and patterns that repeat across chapters.

Then add a **Documents section**: every document problem found, with the quote, the problem and the proposed wording.
