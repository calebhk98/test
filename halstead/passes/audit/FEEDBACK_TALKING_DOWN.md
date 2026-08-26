# Feedback.md — "TALKING DOWN" and "I. Does the Text Talk Down to the Reader?"

Verification pass over the two named sections of `passes/review/Feedback.md`
only. Every claim checked against the current text in `chapters/`. Nothing in
this pass was edited; all proposed fixes are proposals.

Cross-referenced against `passes/audit/TALKING_DOWN.md` (the earlier 991-line
sweep). That report made exactly one edit (ch6, logged at its bottom). Every
other recommendation in it is still unapplied as of this pass — I re-grepped
items 1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 13, 14 and 21 and all of them are present
verbatim. So "already reported" below means reported and still sitting there,
unless it says otherwise.

Other agents are editing concurrently. Re-grep every quote before acting.

---

## 1. The triple-statement habit: the fraction scene, third beat (Dave to Meg)

**Claim:** the fraction thesis is stated three times — dramatized in ch5, said
by Chloe to her father, then restated by Dave to Meg on the phone: *"She said
getting it right and knowing why it's right are two different things."*

**VERDICT: ALREADY FIXED.** Already reported (TALKING_DOWN.md "EDIT MADE"), and
the edit was made. `grep -rn "getting it right and knowing why" chapters/`
returns nothing. The phone beat now reads, in `chapters/06_the_list.md`:

> "And she explained fractions to me, not how to do them but why it works, with
> drawings, on a napkin, and then again because I asked her to," he says, and
> after a pause, "She talked at me in Spanish for about a minute and every word
> of it went by me."

The third beat is gone. The list rhythm (CPR, fractions, Spanish, karate,
cooking) survived the cut intact.

**Residue, optional, low severity.** The surviving clause `not how to do them
but why it works` is still a compressed version of the thesis, and there is now
a *further* statement of it one chapter on, `chapters/07_the_same_room.md`:

> "And I can divide fractions now," she says... "Not just do them, I know why it
> works, and I got that part on my own, on the floor of my room, at night, and
> it took me about an hour with the door shut."

That one is a seven-year-old boasting to her grandmother, in her own words, with
the physical detail attached — it reads as character, not as thesis, and I would
leave it. Flagging only because if the author wants *no* restatement of the
fraction thesis anywhere after ch5, these two clauses are what is left of it.

**Severity if left: negligible.**

---

## 2. Chloe's own line — "Anybody can do the flipping"

**Claim:** the reviewer floats cutting the second beat too, then rules against
himself: *"The reason I wouldn't cut it is to show she understands it."*

**VERDICT: AUTHOR HAS RULED KEEP.** Present and untouched,
`chapters/06_the_list.md`:

> "Anybody can do the flipping," Chloe says, putting the pen down, "and you do it
> and it comes out right, but the rightness belongs to him and not to you,
> because all you actually know is that he said so."

With the phone call gone this is now the only statement of the thesis in the
chapter, which is the shape the author asked for. No action.

---

## 3. The four percent / MIT store-sign passage

**Claim:** the second line is the author checking you followed — but the author
annotates that it is a deliberate trick and he wants both lines kept.

**VERDICT: AUTHOR HAS RULED KEEP. Passage intact.**
`chapters/21_the_applications.md`, both lines present and adjacent:

> "It's on their site, though, in writing, where anyone can look it up."
>
> "It's on their site," Ruth says, "and it still isn't a real number, because
> both of those can be true at once, the site and the lie on it."

The whole store-sign chain is intact: Chloe's sign question, Ruth's `You'd think
the sign was doing a job that had nothing to do with the store`, Chloe's
`Ninety-one out of ninety-one bought something`, Sam's `Or you'd want your money
back for the trip in`. No action on either protected line.

**Two flags, neither a talking-down defect:**

- The page says **three** percent, not four: `"It said three percent," she says,
  when Sam finds her there an hour later, still on the floor.` The author's
  annotation and the reviewer both say four. Already flagged in TALKING_DOWN.md
  item 12; still unreconciled. Someone with the numbers pass should settle it.
- The unprotected fifth speech in the chain is still there and is still the one
  weak link: Ruth's `"That's probably it, what the watch companies do: a school
  wants to look exclusive, so it puts a small number on the website."` That is
  the figure with the figure taken out, and it arrives *before* the protected
  line, blunting it. Already reported (item 12), still live. Cutting it does not
  touch either line the author protected. **Severity: low, but it is free.**

---

## 4. The exam metaphor twice, near-verbatim, same chapter

**Claim:** *"Staying keeps the question open. It just makes the room permanent."*
to Amberg, and a near-identical line to her parents in the same chapter.

**VERDICT: STILL LIVE.** Already reported (TALKING_DOWN.md item 5), not acted
on. Both are in `chapters/22_the_offer.md`, roughly a hundred and twenty lines
apart.

**Instance A**, to Amberg in the interview:

> "If you sat one exam every year, in a single room, against the same ninety
> people, and you kept coming out near the top of it, would you ever actually
> find out if you were good at the exam, or just good against that particular
> room?" She keeps going before he can answer it, because she has been
> assembling the answer since the clock on his desk started. "I don't know
> what's outside this building, and everyone I've ever been measured against my
> whole life is inside it. **Staying keeps the question open. It just makes the
> room permanent.**"

**Instance B**, to her parents on the phone, same chapter:

> "If I take it, I already know exactly what the next decade looks like," Chloe
> says. "I've seen the building. I've seen the work. I've watched what everyone
> in it does with a bad afternoon and what they do with a good one since I was
> seven. I could tell you what the first year looks like, and probably the
> fifth." She hears her own voice picking up pace and keeps going anyway.
> "Everyone I've ever been ranked against my whole life is inside those two
> buildings, and I don't know what I'd be if I got ranked against anyone else.
> **Staying keeps that question open. It just makes it permanent.**"

(Note: B's opening has drifted from `the next ten years` to `the next decade`
since the earlier audit quoted it. The repeated sentences are unchanged.)

**Proposed fix: delete two sentences from B only** — `Staying keeps that
question open. It just makes it permanent.` Nothing before them in that speech
goes; the parents asked a direct question and the paraphrase answers it. Nothing
needs rewriting around the cut, because the line that follows is her mother's

> "So you're saying no to guaranteed money for the chance of finding out you're
> not as good as you think you are,"

which is a better, hostile restatement of the same thought and draws Chloe's best
line in the chapter (`I'm not saying I think I'm good, only that I don't know,
and I'd rather find out than get paid not to`). That exchange is untouched by the
cut.

**Keep A.** A owns the figure — one exam, one room, the same ninety people —
and lands on `the room`, the figure's own noun. B has dropped the exam, so
`makes it permanent` has no antecedent but "the question": it is the copy with
the picture removed. A is also the line said to the man holding the offer at the
moment of refusal, and it is the only reason he ever gets.

**Severity: high.** This is the book's thesis sentence. Said once it is the line
the whole book has been walking toward; said twice in one chapter it reads as a
draft the author liked so much he used it again, and the second use retroactively
cheapens the first.

---

## 5. Amberg's mark-scheme scene states "showing your work" three times

**Claim:** three statements in one conversation.

**VERDICT: STILL LIVE — and the reviewer undercounted.** Already reported
(TALKING_DOWN.md item 4), not acted on. The literal phrase appears once
book-wide; the *point* is stated five times inside the conversation in
`chapters/19_sixteen.md` and a sixth time two scenes later.

In order:

1. Amberg, setup (keep): `There are four marks underneath that answer. A mark
   for the rule you are relying on. A mark for where the rule comes from. A mark
   for why a shed is inside it. A mark for what happens if the shed burns down
   on the Tuesday before delivery.`
2. Amberg (keep): `They follow if the person reading has your head and has
   already done the working you skipped, whereas a marker with a stack of these
   in front of them has about ten seconds each, not enough to rebuild your
   reasoning for you.`
3. Amberg, the best version, and the one to end on: `You wrote that answer for a
   reader who already has your head, who already knows the rule and where it
   comes from and why a shed counts and what happens if it burns... There was a
   single reader like that in this building in April, and the man marking your
   paper was somebody else entirely.`
4. Chloe restating it back: `So the points are for saying the obvious part out
   loud, in the right order, a row at a time, even though anyone reading it
   already knows every word of it is true before they get to your line.`
5. Amberg restating her restatement: `"The points are for showing your work,"
   Amberg says, tapping the scheme once where the rows are and then closing it
   over them. "A page gets marked on what's written on it, not on what's in your
   head, and right now your page has one correct sentence and four empty rows
   underneath it. Take the paper."`

And a sixth, from Kavi two scenes on, same chapter, line 77:

> "It's the same sentence to you, because you already know why the risk sits
> with the buyer, whereas the marker has to be given that reasoning rather than
> assumed to already have it, and right now the page hands them one idea wearing
> two coats instead."

**Proposed fix: cut 4 and 5 entirely** — from `"So the points are for saying the
obvious part out loud` through `Take the paper."`, and keep the physical beats
around them. The scene then ends on 3 plus `Chloe reads the rows twice, then
looks up at him and back down at them.` Add nothing. She does not need to prove
on the page that she understood; the Kavi scene and the practice papers prove it,
which is what they are for. If the author wants Amberg to have the last word,
keep only the four words `Take the paper.` as a bare line and drop the rest of 5.

**Do not touch Kavi's version.** It is a different scene, a different teacher,
and it is doing work (he is handing the page back with an instruction).

**Severity: medium-high.** The chapter's own subject is not writing the same
sentence twice in a different hat, and it writes it six times in different hats.
Kavi's phrase `one idea wearing two coats` is a literal description of the
passage it sits in. Six repetitions read as a draft, not a joke.

---

## 6. Nadia narrates her investigative method to the men above the tire shop

**Claim:** *"They don't need it. The reader does, which is the tell."*

**VERDICT: REVIEWER WRONG (fixed before he was read).** Already reported as
fixed in TALKING_DOWN.md; re-confirmed against the current
`chapters/27_nadia.md`. Do not run this pass over ch27 again.

The investigation is dramatized first, over four paragraphs — the legal pad at
the kitchen table before first light, the state business filings, the
cross-reference against county property records, the call to the tire shop's
front counter. By the time she is in the room the reader already has all of it.

What she says in the room is not exposition, because the room has turned hostile
around it: the man in the doorway has `pushed the door shut with the heel of his
hand`, another has photographed her car and `read her registration out loud,
every character of it, slowly, and then again`, and a third has come around the
table and stopped `close enough that she has to tilt her head back to keep his
face in view` to say `"Say that again, slower, so everybody in the room gets the
benefit of it."` She says it again word for word at the same speed. The facts are
the weapon, and the text shows them landing rather than explaining that they do:

> A man at the folding table turns a printout face down.

No action. **Severity of leaving it: zero — it is not a defect.**

---

## 7. Chapter 21 admissions narrates the officers' reasoning

**Claim:** the text walks the reader through the admissions officers' thought
process step by step instead of dramatizing it.

**VERDICT: STILL LIVE.** Already reported (TALKING_DOWN.md item 7), not acted
on. Both paragraphs are present verbatim in `chapters/21_the_applications.md`:

> Then somebody reads the essays, and what everybody notices first is the
> graduate-level prose, while what everybody thinks first is ghostwriting:
> ninety-one applicants from a single school, all at such a level, is a mill or
> a very good teacher with a template. A review committee, reading blind, spends
> most of a meeting on the transfer-cohort theory before somebody checks the
> birth years.
>
> Then they lay them side by side, the standard method for catching a template,
> and the theory dies there, because no two of them argue alike, and a pair of
> the ninety-one take opposite positions on a question with both worth reading,
> the thing a template could not possibly produce.

The precise fault is narrower than the reviewer states. It is not that the
reasoning is narrated — the book narrates institutional process well elsewhere in
this chapter. It is that the narrated version comes **first** and the dramatized
version comes **second**, in the very next paragraph: the Penn officer with the
mug going cold, Odile's over-length essay, the 10v1 paragraph read three times,
the colleague in the doorway with his own coffee, `It means exactly what it says,
with no second meaning folded into it.` That scene does the identical job through
two people in a room, thirty seconds later. The reader is told the answer and
then shown it.

**Proposed fix, in order of preference:**

1. **Move the template beat into the Penn scene.** She is already on the phone to
   the colleague down the hall; he can be the one who has laid two of them side
   by side and found they argue opposite ways. Costs one exchange, buys back two
   paragraphs, and turns the best line in the section into a discovery.
2. **Failing that, invert the order.** Run the Penn scene first, then one
   compressed sentence of narration afterwards as the general case of the
   particular thing the reader just watched.
3. **Minimum viable cut, if the paragraphs must stay where they are:** delete
   `, the standard method for catching a template,` and `, the thing a template
   could not possibly produce`. The first names a method the reader does not need
   named; the second restates what the clause before it just said. Two clean
   deletions, no rewriting.

Leave the rest of the chapter alone. The transcript nobody believes and the
reading room with the escort and the paperback are dramatized properly.

**Severity: medium.** It spoils its own scene, which is worse per word than a
flat restatement, and it is the most expository stretch in the book — the place a
skeptical reader will point at.

---

## 8. Chapter 25, the Army PT list of six events with point values

**Claim:** a list dropped into the narrative, reads like a briefing document; the
text could simply say "he maxed the test."

**VERDICT: REVIEWER WRONG on the substance; the load-bearing part must stay.**
Already reported (TALKING_DOWN.md, "Where the reviewer is wrong"). The text has
also moved since he read it — his quote says `meeting four of the six`, the page
now says `most of them`. Current text, `chapters/25_forty_targets.md`:

> Six events, a hundred points available on each, sixty required to pass on each,
> and Sam is meeting most of them for the first occasion in his life: deadlift,
> standing power throw, hand-release push-ups, the sprint-drag-carry, a plank,
> two miles.

The scoring frame is the setup for the payoff three lines later:

> The score is six hundred.
>
> The grader adds the column a second time with the pen held clear of the paper,
> checking rather than writing, then puts the total down in ink, then looks up
> from the clipboard.

Without `six events, a hundred points available on each`, six hundred is a number
with no meaning and the grader re-adding the column is a beat about nothing. The
reviewer's proposed replacement ("he maxed the test") would cost the best image
in the scene. The book also pays this back later — `The six hundred stays out of
the letter, on the grounds that it would require a paragraph of explanation`.

**Optional trim only, low priority:** the six event names. `standing power throw`
and `sprint-drag-carry` are not needed by the sentence. Against trimming: the
section immediately after has Sam running the events again on his own time with a
stopwatch, which needs there to be named events, and this book's reader enjoys
knowing exactly what is on the test.

**Severity if left as is: zero.** Recommend no change.

---

## 9. Chapter 14, the sixty-degree archery geometry

**Claim:** several paragraphs of explanation; Chloe could figure it out while
doing it rather than having Bell explain it to the class.

**VERDICT: REVIEWER WRONG on both halves.** Already reported
(TALKING_DOWN.md, "Where the reviewer is wrong"); re-confirmed against the
current `chapters/14_sixty_degrees.md`, which is unchanged.

The geometry occupies **one** narrated sentence:

> Bell walks them down the field to show them the lanes, two firing lines seventy
> metres apart, side by side, both facing north, each bending in toward the other
> until they meet at a point where the angle holds at sixty degrees. That is
> where the flight paths cross, at the top of the arc, where an arrow released
> early from one line and an arrow released on time from the other can end up in
> the same patch of sky at the same instant, and whatever is left of them keeps
> travelling and comes down together in open grass a hundred and fifty metres on,
> behind a rope and a sign where the target block stays all year.

Everything around it is dramatized instruction with a student arguing inside it,
which is the opposite of a lecture — Bell holding a hand out flat for the hang at
the top, `Keep your eyes off each other... and you count instead.`

And Chloe *does* discover it in action, over the length of the chapter:

> It is a counting problem, and it takes Chloe until the third week to admit that.

then the four fingers going against her leg walking to dinner in the dark, Ruth
catching her at it (`Mine's late, always late, by the same amount`), the counts
compared in the corridor until they are late into dinner, and finally the first
collision with Odile arriving as `a small dry click a long way up, before
anything is visible`. That progression is the spine of the chapter.

No action. **Severity: zero.**

---

## 10. The general claim: "the book's dominant explanatory habit is triple statement"

**VERDICT: STILL LIVE as a book-wide habit, though not in the instances the
reviewer named.** Two of his five named cases were already fixed (fraction phone
call, Nadia) and two of the three in section I are wrong (archery, PT test). But
the habit itself is real and the earlier audit found eleven unnamed instances
that are worse than most of his. Re-grepped this pass, all still present and
unedited:

- `chapters/31_ruth.md` — Ruth's five chat bullets still index chapters 25-30 in
  the order the reader read them, plus both closers (`we are not slightly ahead`
  / `i dont think we're the same kind of thing`). TALKING_DOWN.md item 1, the
  worst one in the book.
- `chapters/24_the_chat.md` — the chat's amateur encryption stated three times,
  lines 5, 69 and 501. Item 2.
- `chapters/22_the_offer.md` line 33 — the interview montage glossing itself
  twice (`because the standard she was holding the work to was hers before it was
  anyone else's...` and `and the folder open on the desk now has the same name
  typed on the tab`). Item 6. Worth doing at the same time as claim 4 above,
  since it is the same chapter.
- `chapters/33_the_other_one.md` line 119, `chapters/26_the_exercise.md` line 67
  (narration duplicating Sam's AAR line at 127), `chapters/25_forty_targets.md`
  line 157 (turret speech recited near-verbatim from ch18 line 11),
  `chapters/20_the_parking_lot.md` line 5 (`the entire reason it is worth doing`),
  `chapters/17_fourteen.md` line 179, `chapters/28_nineteen.md` line 35, and the
  ch35 closing sentence. Items 3, 8, 10, 11, 13, 14, 21.

Nothing new to add: that list is complete and correct and the fixes in it are
written up. The only thing worth saying here is that of the earlier audit's
twenty-one findings, exactly one has been actioned.

**Severity: high in aggregate.** Individually most are one sentence. Together
they are the pattern the reviewer named, and the reviewer named it from a draft
in which almost all of them were already present.

---

## Summary table

| # | Claim | Verdict | Where |
|---|---|---|---|
| 1 | Fraction thesis restated by Dave to Meg (third beat) | **ALREADY FIXED** | ch06 |
| 2 | Chloe's "anybody can do the flipping" line | **AUTHOR HAS RULED KEEP** | ch06 |
| 3 | Four percent / store-sign explained twice | **AUTHOR HAS RULED KEEP** (intact; two side-flags) | ch21 |
| 4 | Exam metaphor twice, near-verbatim | **STILL LIVE** — cut two sentences from the parents' version | ch22 |
| 5 | Mark scheme states its point three times | **STILL LIVE** — six times, not three; cut beats 4 and 5 | ch19 |
| 6 | Nadia narrates her method above the tire shop | **REVIEWER WRONG** (fixed before he read it) | ch27 |
| 7 | Admissions reasoning narrated, not dramatized | **STILL LIVE** — narration precedes the scene that proves it | ch21 |
| 8 | Army PT list of six events with point values | **REVIEWER WRONG** — scoring frame is load-bearing | ch25 |
| 9 | Sixty-degree archery delivered as explanation | **REVIEWER WRONG** — one sentence, and she discovers it | ch14 |
| 10 | Triple statement is the dominant habit | **STILL LIVE** book-wide, but in unnamed instances | ch17, 20, 22, 24, 25, 26, 28, 31, 33, 35 |

### Side-flags raised, not talking-down defects

- ch21 says `three percent`; the author's ruling and the reviewer both say four.
  Unreconciled since the last audit.
- ch21's Ruth line `That's probably it, what the watch companies do: a school
  wants to look exclusive, so it puts a small number on the website` is the one
  unprotected link in the store-sign chain and weakens the line the author
  protected. Free cut.
