# Variant D: restate everything, then prosecute it

A chapter is known to contain a large number of problems. A careful reader
working through it slowly found something wrong in most paragraphs. Your job is
to find them. Do not edit anything. Do not rewrite. Reporting that the chapter is
fine is the one outcome that is certainly wrong.

There are three stages and the first is not optional. It is the stage that makes
the other two work.

---

## Stage one: restate every paragraph, in writing

Under `## Restatement`, write **one line per paragraph, every paragraph, in
order, numbered by line**, saying in your own plain words what happens in it or
what it says.

Not a summary of the chapter. Not the interesting ones. Every paragraph.

**Work out what a paragraph is in your file first, because it differs.** Most
chapters separate paragraphs with a blank line. Chapters one to six do not: every
paragraph is a line ending in two trailing spaces, with no blank lines anywhere,
so the file looks like three enormous blocks and is actually a hundred and
twenty-odd paragraphs. Run

    grep -c '  $' chapters/NN_x.md

If that number is large, that is your paragraph count and restating the three
blocks instead will find you nothing. This has already sunk one pass.

This is mechanical and it will feel like a waste of time. It is not. A fluent
chapter reads as though it makes sense, and reading it will tell you that it
does. Writing each paragraph back in your own words is the only reliable way to
find the ones that cannot be written back, and those are the worst problems in
the book.

Three things happen while you do this, and all three are findings:

- A phrase resists restatement. It has the shape of meaning and no meaning.
- You write the restatement and it says something that could not happen.
- You write a restatement and realise you already wrote it, four paragraphs ago,
  in different words.

---

## Stage two: sit in every chair

Go back through. Every time somebody other than the viewpoint character does
something, or is spoken to, or is handed something, **become them for a moment**
and write three lines:

- *I am ...* who they are, and what their job or position is.
- *What I have just been given, asked or shown is ...*
- *What I would actually do about that is ...*

Then look at what the text has them do. Where the two differ, that is a finding.

Do this for the one-line people especially: the person behind a desk, the rep who
gets a single sentence, the classmate at the next table. They are the ones a
writer stops thinking about, and they are where the errors are.

Then do the same for the viewpoint character wherever she is told, given or asked
something: *what do I know at this moment, what do I not know, and what would I
do?*

---

## Stage three: clear each paragraph against the list

Nothing is innocent until you have answered all of these for it.

- **Joining words.** For every *instead, anyway, then, but, so, for once, which
  is why*, name what sits on each side. A missing side is a finding.
- **Objects.** Where did that come from, and does it do anything afterwards?
- **Reaction.** Did anybody react to what just happened, and is the size right? A
  remarkable thing passing without a reaction is a finding even though there is
  no sentence to quote. Quote the sentences on either side of the gap.
- **Position.** Where are these people and what are their bodies doing? A
  conversation happening nowhere is a finding.
- **Redundancy.** Has this already been said earlier in the chapter in other
  words? Two paragraphs doing one job is a finding.
- **Order.** Does this depend on something that has not happened yet?
- **Voice.** Is the narrator explaining the scene to the reader, telling them what
  it means, or what to think? That is a finding.
- **Specificity.** Is a comparison, an image or an example vague where a real one
  would be exact? A person reaches for the particular thing; writing reaches for
  the category.

---

## Two things that are not findings

Both of these have produced false positives. Clear every candidate finding against them before you
write it down.

**Check what the person actually knows.** This is a tight third-limited book. A character can be
wrong, can be guessing, can be working from a partial account, and none of that is the text being
wrong. Before you call a statement false, establish what that person has been told on the page.
Before you call a reaction undersized, establish what they have been told on the page. A parent who
hasn't been given the impressive detail cannot react to it. A child who believes the emergency was a
drill is not contradicting a fact she witnessed — she is telling you what she believes.

**Competence is not an omission.** These children train daily for years. Fear, fuss and adrenaline
drain out of them as they get older, and the cast gets flatter and more capable with every chapter,
on purpose. Calm after violence is characterisation. A sixteen-year-old who walks away from a fight
without shaking is the point, not a missing beat. Before flagging an absent reaction, check whether
the text has already given you the reason — twice now the justification has been sitting inside the
same sentence as the flagged line.

Two related non-findings: **people share surnames**, so a minor character with a main character's
last name is what a real roll of students looks like; and **an institution's vocabulary can go
unglossed**, because the reader is reading chapter one to chapter thirty-five in order, not landing
here at random.

---

## Aim

**Expect at least thirty findings.** Fewer than that means you read for gist.
Small ones count. A single word with nothing to attach to counts. Obvious counts.

## Then the context

Read `SYNOPSIS_CHARACTERS_TIMELINE.md`, `chronology/BOOK.md`, and the sheet in
`characters/` for every named person. Add anything the chapter gets wrong about
who these people are, what they know, what they can do, or how fast they work.

## Rules

- Quote verbatim with line numbers, checked against the file.
- One line per finding.
- Mark the unsure ones *unsure* and include them.
- Do not report prose style, rhythm, word repetition or quality.
- Do not rewrite. Do not edit the chapter.
