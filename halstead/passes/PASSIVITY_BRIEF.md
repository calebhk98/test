# Finding the passivity

The author keeps seeing it and the instruments keep saying it is not there.
Both are true, and the second one is the reason for this brief.

`tics.py` caps three shapes and all three pass:

    does X instead          49.0 against a cap of 53.5
    puts it back down       26.5 against 29.4
    leaves it / lets it go  12.1 against 13.3

Those count *strings*. A character can decline to act in a hundred phrasings,
none of which contain the word *instead*. So do not grep for this. Read.

## What passivity means here

A character is handed something to push against, and does not push.

The shapes it takes in this manuscript, in rough order of how often it shows up:

**1. Auditing instead of reacting.** Somebody does something to the protagonist
and her response is to go back over her own behaviour looking for where she
gave it away, or to work out what the other person's incentive was. This is the
single commonest form and it is the one the author names most. A child who has
just been humiliated does not run an analysis. She goes red, she avoids a
staircase, she rehearses the comeback in bed and comes up short, she tells
somebody, or she says nothing and is furious about having said nothing.

**2. Receiving a scene.** The point-of-view character is present for something
and makes no decision in it. Information arrives, she registers it accurately,
the scene ends. Ask of every scene: what does she *decide*? If the answer is
nothing, say so.

**3. Declining, repeatedly.** She works out that she could do a thing and then
does not do it. Once is character. Four times in a chapter is a habit the book
has stopped noticing.

**4. Somebody else drives.** Every scene is started by another person, and she
answers. Count who initiates across your chapters and say what the ratio is.

**5. The considered non-action, stated.** "She could have said X" or "there is
a version of this where she does Y" — the book getting credit for an action it
never spends.

## Stillness is not an excuse

An earlier version of this brief said deliberate stillness was a legitimate
technique and told you not to flag it. That was wrong and the author has said
so plainly: *"Deliberate stillness IS a form of passivity. It's super common,
annoyingly too much imo."*

So there is no stillness exemption. If a character watches, waits, declines,
holds back, chooses silence, or registers something accurately and moves on,
that is an instance, and you log it. Whether any given one is worth keeping is
the author's call, not yours, and he cannot make it on instances you never
showed him. Err toward reporting.

The only things still out of scope: a character who is genuinely not in the
scene, and reading a group chat without replying, which is what a chat is.

## There is no good chapter to copy

An earlier version pointed at two repaired scenes as the standard. The author
has read them: *"I have yet to read a good chapter anywhere here that is a good
standard for the fix."* Do not hold anything in this manuscript up as the
model. You are not matching an existing scene, you are describing what is
missing.

What an active scene has, stated from first principles rather than from an
example in this book:

- She wants something in the scene, and the want is visible before the scene
  resolves.
- She does something to get it. Not thinks about it, not decides against it.
- The attempt costs her something, or fails, or works and creates the next
  problem.
- The scene ends in a different place than it started, and the difference is
  attributable to something she did.

A scene can have all four and still be quiet. A person can lose. What it cannot
be is a scene the plot would reach the same way if she had stayed in her room.

## What you produce

One file, `passes/passive/CHNN-NN.md`, covering your span. No chapter edits.

Per instance:

  - file:line, and Chloe's age in that chapter
  - the passage, quoted exactly from the file
  - **which of the five shapes**, and why
  - **what she does now** / **what a child that age would do**
  - **Proposed:** actual replacement prose in the book's register

End with: how many instances in your span, which chapter is worst, the
initiates-a-scene ratio you counted, and the three you would fix first.

## Constraints on anything you propose

The narration explains nothing and evaluates nothing. No named emotional states
in narration; the book has five and they are spent. No `, because` inside
dialogue. Do not use: instead, both hands, leaves it, puts it back down, rather
than, hands flat, turning it over, for the first time, never once. No physical
violence, and Chloe does not cry in public.

Every quotation you print must be copied from the file and checked. Fabricated
quotes have done more damage in this project than anything else.

---

# Second pass: cutting, not cataloguing

The six reports logged 141 instances. That is more than the book should lose
and the author has set a ceiling: **each span comes down to at most fifteen**.

So this pass is triage and then surgery.

## Triage

Read your own span's report. Rank every instance. You are looking for two
things at opposite ends:

- **The worst.** Where the passivity costs the book most: a scene that would
  read the same without the viewpoint character in it, a moment the plot needs
  her to meet and she does not, a beat repeated a third and fourth time.
- **The best.** Where it is doing real work and should be defended. Say so
  plainly and give the reason. A report that finds nothing worth keeping has
  not been read carefully.

Keep at most fifteen. Everything you drop, list in one line with why.

## Surgery

For the ones you keep, change them. This is the part that matters and it is
where the last pass failed.

**Do not reword the same event.** Two scenes were repaired last week by giving
the protagonist a richer inner life — a pillow, a rehearsed comeback, a
thinner-sounding thank you — and both still fail, because nothing that happens
happens differently. Adding interiority to inaction is not a fix. It is the
same defect in better prose, and the author caught it from the outside.

A changed instance has to pass all four:

1. She wants something and it is visible to somebody in the scene.
2. She does something about it that another character can see.
3. It costs her, or fails, or works and makes the next problem.
4. The scene ends somewhere it would not have ended otherwise.

She is allowed to lose. She is allowed to make it worse. What she is not
allowed to do is leave the room the way she entered it.

This applies to everyone, not only Chloe. Sam, Ruth, Nadia, Eli, Theo and
Priya all carry logged instances, and a viewpoint character who receives their
own chapter is the same defect.

## Editing rules for this pass

You are editing chapters now, not reporting. Chapters 1 and 2 are LOCKED by the
author: read them if you need context, change nothing in them, and if your span
includes them, take your fifteen from the rest.

Keep the chapter's word count inside 2,000 to 5,000.

Five other agents are editing five other spans at the same time as you, so
`grade.py` would read their half-finished work as well as yours and tell you
nothing you can act on. Do not run it. Check your own span with
`python3 measures/style_report.py chapters/NN_name.md`, which takes a path and
only sees what you point it at. The scorecard is run once, afterwards, over all
six spans together.
