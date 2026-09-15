# Talking down: triple statement and over-explanation

Audit of the whole manuscript against Feedback.md "TALKING DOWN" / "Does the Text
Talk Down to the Reader?" and HOUSE_RULES Rule 1. Report only, ranked by damage.
One edit made, logged at the bottom.

Test applied throughout, in the reviewer's words: *if a character says a sentence
that could be the book's blurb, cut it or bury it.*

Everything quoted was re-grepped at the time of writing. Four other agents are
editing concurrently; re-grep before acting on anything below.

---

## Summary of the sweep

The reviewer's five named instances hold up in three cases out of five. Two have
already been fixed by the rewrites of the last two days (ch14 archery, ch27
Nadia) and should not be touched again. See "Where the reviewer is wrong" at the
end.

The sweep turned up eleven instances the reviewer did not name, two of which
(ch24, ch31) do more damage than three of the five he did.

The book-wide tone construction Rule 1 flags as recurring is effectively gone.
`grep` for "the tone/voice/look X uses when" returns three hits book-wide, all
three of them clean (a train-station-announcement voice, a laying-a-number-down
voice, a voice used about a thing already lost). None names a mental state. That
pass worked; nothing below is a relapse into it.

What is left is a different animal, and it has two shapes:

- **Triple statement**, as the reviewer describes it: dramatize, articulate,
  restate. Almost always the third statement is the one to lose, and almost
  always it is a *narrator* sentence rather than a line of dialogue.
- **Tell-then-show**, which is the same fault run backwards: a paragraph of
  narrated summary sitting directly on top of the scene that would have proved
  it. Ch21 and ch26 are the clean cases. This one is worse than triple statement
  because it spoils the scene before the reader gets to it.

---

# THE RANKED LIST

## 1. Ch31 — Ruth's chat message indexes the previous six chapters

**Chapter:** 31, Ruth. The turn of the whole book.

> ruth: nadia cant find anyone who can finish a thought. thats not a hiring pool
> ruth: sam asked when the real assessment was. it was the real assessment
> ruth: theo writes out his reasoning and gets told hes skipping ten steps
> ruth: eli found five holes in an afternoon in a system a company pays people to protect and they didnt think one was possible
> ruth: chloe writes what a newsroom writes, twice a week, after work, and people keep asking who her team is
> ruth: every single one of us has a story like this and every single one of us has decided it means something about the other person
> ruth: we are not slightly ahead
> ruth: i dont think we're the same kind of thing

**What is being explained:** the premise of the novel.

**Who already established it:** chapters 25, 26, 27, 28, 29 and 30, one scene
each, in that order. The five bullets are those five chapters in the order the
reader read them. The reader finished the Chloe one four pages ago.

**Recommendation: bury.** Not cut. This is the plot's hinge and Ruth has to say
it. The damage is not the thesis, it is the *enumeration* — five lines that
reconstruct evidence the reader is still holding, which turns a discovery into a
table of contents and makes Ruth sound like she is briefing someone who came in
late.

Specifically:

- Keep `every single one of us has a story like this and every single one of us
  has decided it means something about the other person`. That is the actual
  insight and no bullet does its work.
- Keep one of the two closers, not both. `we are not slightly ahead` and `i dont
  think we're the same kind of thing` are the same sentence twice; the second is
  better because it is hedged and she is frightened.
- Cut three of the five bullets. Keep at most two, and keep the two furthest
  back (Nadia, Sam) rather than the two the reader just finished (Chloe, Eli).
  Ruth naming other people's stories and not her own is the characterful part;
  naming all five is the index.

The exchange that follows is already perfect and needs nothing:
`kavi: why didnt you say` / `ruth: because i didnt want it to be true`.

---

## 2. Ch24 — the chat's encryption is stated three times in one chapter

**Chapter:** 24, The Chat. Not named by the reviewer. This is the cleanest
textbook triple statement in the book after the fraction scene.

**First statement**, paragraph one:

> The chat is five years old. They wrote the encryption themselves in their
> first year here, mostly to keep a teacher from reading it while they arranged
> getting out of the building, and none of them has ever used another.

**Second statement**, after the Eli speedrun section:

> The build pipeline flaw is the kind of gap a company checks for insiders and
> outages, not for somebody like Eli looking at it sideways. Their own
> encryption has gone five years without anyone who had real reason to try it.
> Eli wrote part of it. The rest has sat as untested by him as by everyone else,
> year after year.

**Third statement**, four lines from the end of the chapter:

> The lock they built at thirteen to get past a teacher is still the only thing
> standing between this chat and anyone outside it, one lock, five years
> running, untouched and unreplaced. Whatever internal means, it's a wall each
> of them keeps running into.

**What is being explained:** that the chat is protected by amateur teenage
crypto, and that this will matter.

**Who already established it:** the first paragraph of the chapter, in the
book's ordinary declarative register, where it belongs. Also ch16, where the
reader watched Ruth write it and watched Chloe break the *metadata* around it in
six days.

**Recommendation: cut two of the three.** Keep the opening paragraph. Cut the
Eli gloss entirely — the Eli scene is funny and self-sufficient, and the
paragraph exists only to make sure the reader draws the line from "Eli got into
a real company in an afternoon" to "our own thing is untested," which is the
one inference the reader will certainly draw unaided. Then cut the first
sentence of the closing paragraph and keep only `Whatever internal means, it's a
wall each of them keeps running into`, which is about something else and earns
its place.

The chapter already ends on the right image after that: `Chloe leaves the tab
open on her desk for the rest of the evening, the cursor sitting in the empty
box where a reply would go.`

---

## 3. Ch17 — the pie scene names its own subtext, twice

**Chapter:** 17, Fourteen. Winter break, the rifle conversation.

**The gloss**, and it is the purest instance of Rule 1 in the manuscript:

> "That's a hold. That is a hold, that's been a hold all night," her mother
> says, **and it is the closest either of them comes to naming what has been
> going on at the table all evening.**

**And four paragraphs above it**, the same point in narration:

> The real sentence stays exactly where it's been all evening, buried under the
> one about pie: how much of the last four years already happened at a range and
> a mat three hours from this table, with her mother getting it secondhand and
> six months late. The kitchen gets a few minutes and the plates get stacked
> instead, and that turns out to be as much of the sentence as the room can
> hold.

**What is being explained:** that the family is talking about the football game
and not about the four years.

**Who already established it:** the scene. Meg walks into the kitchen and stays
there. Dave moves the salt and puts it back. Plates get stacked half full. Meg
comes back and offers to warm the pie. Then she says "that's a hold" about a
football game while sitting on the arm of her husband's chair. There is no
reader alive who misses this.

**Recommendation: cut** the clause `, and it is the closest either of them comes
to naming what has been going on at the table all evening`. Full stop after
`her mother says`. This is a single unambiguous deletion and the line becomes
the best line in the chapter the moment it is alone.

**Second recommendation, your call:** the "real sentence" paragraph is doing the
same job in advance. Its middle clause (`how much of the last four years already
happened at a range and a mat three hours from this table, with her mother
getting it secondhand and six months late`) is the tell — it is the sentence
nobody says, said. Cutting from `buried under the one about pie:` to the end of
that clause leaves `The real sentence stays exactly where it's been all evening.
The kitchen gets a few minutes and the plates get stacked instead`, which is
enough. But this one is a judgement call, not a deletion, so it is yours.

---

## 4. Ch19 — the mark scheme scene states its point four times, and a fifth in the next scene

**Chapter:** 19, Sixteen. The reviewer named this one and undercounted it.

In order, inside one conversation:

1. **Amberg, setup (keep):** `There are four marks underneath that answer. A
   mark for the rule you are relying on...`
2. **Amberg (keep):** `They follow if the person reading has your head, and has
   already done the working you skipped, whereas a marker with a stack of these
   in front of them has about ten seconds each, not enough to rebuild your
   reasoning for you.`
3. **Amberg, the best version of it:** `You wrote that answer for a reader who
   already has your head... There was a single reader like that in this building
   in April, and the man marking your paper was somebody else entirely.`
4. **Chloe restating it back:** `So the points are for saying the obvious part
   out loud, in the right order, a row at a time, even though anyone reading it
   already knows every word of it is true before they get to your line.`
5. **Amberg restating her restatement:** `"The points are for showing your
   work," Amberg says... "A page gets marked on what's written on it, not on
   what's in your head, and right now your page has one correct sentence and
   four empty rows underneath it. Take the paper."`

And then a sixth time, two scenes later, from Kavi:

> "It's the same sentence to you, because you already know why the risk sits
> with the buyer, whereas the marker has to be given that reasoning rather than
> assumed to already have it, and right now the page hands them one idea wearing
> two coats instead."

**Who already established it:** the board. `Chloe reads her own row twice, once
for the verdict and once for the margin.` `"Fail," she says. "By four points,
out of two hundred."` The reader has the problem before Amberg opens the folder.

**Recommendation: cut 4 and 5.** End the conversation on 3, the killer line,
plus the physical beat. Amberg slides the paper across, she reads the blank rows,
he says `Take the paper`, and she takes it. She does not need to prove she
understood; the practice papers in May prove it, which is what the Kavi scene is
for.

**One flag, and it may be worth a laugh rather than a cut.** This is the chapter
about not writing the same sentence twice in a different hat, and it writes the
same sentence six times in different hats. Kavi's phrase for the fault —
`one idea wearing two coats` — is a literal description of the passage it
appears in. If that is deliberate it is a very good joke and no reader will ever
find it, because six repetitions read as a draft, not a device. If it is not
deliberate, cut 4 and 5 and it goes away.

---

## 5. Ch22 — the exam metaphor, twice in eight pages

You asked for both in full and a recommendation on which to lose.

**Instance A**, to Amberg, in the interview:

> "If you sat one exam every year, in a single room, against the same ninety
> people, and you kept coming out near the top of it, would you ever actually
> find out if you were good at the exam, or just good against that particular
> room?" She keeps going before he can answer it, because she has been
> assembling the answer since the clock on his desk started. "I don't know
> what's outside this building, and everyone I've ever been measured against my
> whole life is inside it. Staying keeps the question open. It just makes the
> room permanent."

**Instance B**, to her parents on the phone, same chapter:

> "If I take it, I already know exactly what the next ten years look like,"
> Chloe says. "I've seen the building. I've seen the work. I've watched what
> everyone in it does with a bad afternoon and what they do with a good one
> since I was seven. I could tell you what the first year looks like, and
> probably the fifth." She hears her own voice picking up pace and keeps going
> anyway. "Everyone I've ever been ranked against my whole life is inside those
> two buildings, and I don't know what I'd be if I got ranked against anyone
> else. Staying keeps that question open. It just makes it permanent."

**Recommendation: lose B, keep A.** Four reasons, in order of weight.

1. **A owns the metaphor; B has lost it.** A builds the figure out — one exam,
   one room, the same ninety people — and then lands on `the room`, which is the
   figure's own noun. B has dropped the exam entirely, so `makes it permanent`
   has no antecedent but "the question." B is a copy with the picture removed.
2. **A is the decision; B is a report of a decision.** A is said to the man
   holding the offer, at the moment of refusing it, and it is the only reason he
   ever gets. B is said afterwards, to people who cannot change the outcome.
3. **B's beat is already covered by the line after it.** Her mother answers with
   `So you're saying no to guaranteed money for the chance of finding out you're
   not as good as you think you are` — which is a third statement of the same
   thought, and a much better one, because it is hostile and it draws Chloe's
   best line in the chapter: `I'm not saying I think I'm good, only that I don't
   know, and I'd rather find out than get paid not to.` Delete B and that
   exchange is untouched. Nothing is lost.
4. **The parents' scene has a better ending available and B is in its way.** The
   scene's real subject is money, Georgetown and whose fault the number is, and
   it closes on `it was your name on the first one too, eleven years ago`. B
   pulls the scene back toward a thesis it has already left behind.

**The deletion:** the two sentences `Staying keeps that question open. It just
makes it permanent.` only. Everything before them in that speech stays; it is
paraphrase rather than repetition, and the parents asked a direct question that
needs a direct answer.

**Do not cut A.** With B gone, A is unique, it is the line the book has been
building toward since chapter 1, and it is said once.

---

## 6. Ch22 — the interview's interior montage glosses itself twice

Same chapter, earlier, and worth doing at the same time.

> She's taught the twelves real analysis out of a room two floors below, working
> through the proofs handed to her at that age, by a teacher always making it
> sound like the ordinary next thing rather than a favor. She's dropped flawed
> hinges of her own into the scrap bin rather than let them stand, and gone back
> to the forge every Thursday for five years without anyone having to ask her
> twice, **because the standard she was holding the work to was hers before it
> was anyone else's, and all of it sits outside any dollar figure, in a place
> the number on the desk in front of her leaves entirely alone.** At the start,
> the whole of this place came down to a letter with her name typed across the
> front of it, in an envelope she still has, in a drawer she still checks, **and
> the folder open on the desk now has the same name typed on the tab.**

**What is being explained:** that she is not weighing this in money, and that
the folder rhymes with the envelope.

**Who already established it:** the recalled details themselves, and the fact
that the reader watched her put the hinges in the bin (ch17) and watched her
open the envelope at the mailbox (ch3).

**Recommendation: cut both bolded stretches.** The details are excellent and
should stay. The first gloss tells the reader what the details mean; the second
points at an echo the reader can see on the same page — the folder with her name
typed on the tab is described two paragraphs earlier. Two clean deletions,
nothing needs rewriting around them.

---

## 7. Ch21 — the admissions section tells, then shows the same thing

The reviewer's second named over-explanation. He is right, and the diagnosis is
more specific than he puts it: the fault is not that the reasoning is narrated,
it is that the narrated version comes *first* and the dramatized version comes
second.

**The narrated version:**

> Then somebody reads the essays, and what everybody notices first is the
> graduate-level prose, while what everybody thinks first is ghostwriting:
> ninety-one applicants from a single school, all at such a level, is a mill or a
> very good teacher with a template. A review committee, reading blind, spends
> most of a meeting on the transfer-cohort theory before somebody checks the
> birth years.
>
> Then they lay them side by side, the standard method for catching a template,
> and the theory dies there, because no two of them argue alike, and a pair of
> the ninety-one take opposite positions on a question with both worth reading,
> the thing a template could not possibly produce.

**The dramatized version, immediately after:** the Penn officer with the mug
going cold, Odile's over-length essay, the 10v1 paragraph read three times, the
colleague in the doorway with his own coffee, `It means exactly what it says,
with no second meaning folded into it.`

**Who already established it:** nobody yet — but the Penn scene is thirty
seconds away and does the identical job through two people in a room.

**Recommendation: bury, not cut.** The template theory is real plot and cannot
just go. But it should reach the reader the way the 10v1 discovery does, through
somebody's morning. Options, in order of preference:

1. Give the template beat to the Penn officer and her colleague. She is already
   on the phone to him; he can be the one who lays two of them side by side.
   This costs one exchange and buys back two paragraphs.
2. Failing that, invert the order: run the Penn scene first, then let one
   compressed sentence of narration carry the template theory afterward, as the
   general case of the particular thing the reader just watched.
3. Failing that, cut `the standard method for catching a template` (the reader
   does not need the method named) and `the thing a template could not possibly
   produce` (the sentence has already said it).

The two other explained beats in this chapter — the transcript that eight
offices refuse to believe, and the reading room with the escort and the paperback
— are dramatized properly and should be left alone. The reading-room section is
one of the best things in the book.

---

## 8. Ch33 — the clearance irony, three times in three sentences

> **A clearance is a piece of paper that says the government has already decided
> to trust her with things it keeps far from most people, and she's about to
> spend that trust on a file it always meant to keep sealed from her too.** What
> that actually costs her she works through exactly once, on the drive home from
> the office the week the document arrives, and the thought ends in about as
> long as it takes a light to change.
>
> **Chloe is four months into that job when she writes those pages, her hand
> steady through all of them, and she does not stop.**

**What is being explained:** that she is using her clearance against the people
who gave it to her.

**Who already established it:** chapter 30, all of it, at length, including
Whitaker sitting at her kitchen table asking her to account for ten years. And
the second sentence here, which is the good one.

**Recommendation: cut the first sentence and the third.** The middle sentence is
the book at its best — she works it through once, on a drive, and the thought
ends inside a traffic light. That is the whole characterization and it does not
need a definition of a clearance in front of it or a verdict behind it. The
paragraph should be one sentence long.

---

## 9. Ch23 — two one-sentence glosses on echoes the reader can see

Both are single unambiguous deletions but neither is one you have ruled on, so
they are here rather than done.

**(a) The door frame:**

> At the propped courtyard door she reaches up for the top of the frame, which
> she used to have to jump for as a child, and finds her palm against the wood
> with room to spare, her whole arm straight. **The frame is exactly where it's
> always been; she's grown well past having to reach for it.** Her hand stays
> there a second longer than the box in her other arm makes comfortable...

The first sentence contains `which she used to have to jump for as a child` and
`with room to spare, her whole arm straight`. The bolded sentence then explains
the first sentence. **Cut it.**

**(b) The photograph:**

> Theo gets a photograph of the group before anyone's arranged themselves for
> it, and Chloe counts the heads in it before she's decided to: all of them,
> still in it. **She still remembers wanting the last names after camp and
> coming up short, and this time she gets the count while it's still in front of
> her.**

`counts the heads in it before she's decided to` already carries the whole of
ch7. The bolded sentence footnotes it. **Cut it.**

A third in the same chapter is milder and I would leave it: `she finds her
mother's face before she finds anyone else's, the reflex that used to send her to
the fridge twice in a night to check a magnet was still holding a note in place.`
The echo is fused into the image rather than appended to it, which is the
difference.

---

## 10. Ch28 — "saying everything twice," said four times

The section opens `She starts saying everything twice before she notices she's
doing it`, then gives three labelled instances (`The first time it's a
certification page` / `The second time it's a discount` / `The third time is a
deadline`), then a summary paragraph that adds a fourth and fifth (a coordinator,
a translator, her mother on the phone).

**Recommendation: cut the third instance (the deadline).** The certification one
establishes the pattern. The discount one is the best of the three and the only
one that produces anything — the Tyler rate, which survives into the next
paragraph and gets a manager involved. The deadline one repeats the shape a third
time and produces nothing. Cutting it also stops the section from performing its
own subject at the reader.

Keep the closing clause `and thinks of it as ordinary courtesy, the kind you'd
offer anybody in a loud room` — that is not a gloss, it is her misreading herself,
and it is the point.

---

## 11. Ch35 — the last sentence of the chapter is the blurb

> She goes in the next day and does her job, which is the job of a government
> that has been trying to find this man since before she could read, and which
> has two wrong answers on file and no idea that seven people in their twenties
> settled it in sixteen weeks.

**What is being explained:** the entire back third of the plot.

**Who already established it:** ch29 (the nineteen-year file, the two wrong
answers), ch32 (sixteen weeks, `its him. one man.`), ch34 (she read the file at
that desk with the badge still clipped to her bag).

**Recommendation: bury.** This is exactly the reviewer's rule — a sentence that
could be the back cover. But the *position* is right; a chapter should end on
her going in and doing the job. Cut back to one clause. `She goes in the next
day and does her job` is already the whole irony, because the reader knows what
the job is. If you want one qualifier, keep the shortest one, not all three.

---

## 12. Ch21 — the fourth statement of the store-sign analogy

You ruled on this scene and I am not relitigating the line you protected. This
is a different line in the same exchange, three speeches earlier.

The chain, in order:

1. Chloe: `If a store put a sign in its window saying only a few percent of the
   people who walk in buy something, would you think the store was doing well,
   or badly run?`
2. Ruth: `You'd think the sign was doing a job that had nothing to do with the
   store.`
3. Chloe: `Ninety-one out of ninety-one bought something, and that's the number
   the sign should say.`
4. Sam: `Or you'd want your money back for the trip in.`
5. **Ruth: `That's probably it, what the watch companies do: a school wants to
   look exclusive, so it puts a small number on the website.`**
6. Chloe: `It's on their site, though, in writing, where anyone can look it up.`
7. Ruth: `It's on their site, and it still isn't a real number, because both of
   those can be true at once, the site and the lie on it.` **(protected — keep)**

**Recommendation: cut 5.** It is the only line in the chain that translates the
analogy back into plain statement — "a school wants to look exclusive, so it puts
a small number on the website" is the figure with the figure removed, and it
arrives after four people have already made the point in better shapes. It also
weakens 7, which is the line doing the trick you want, because 7 lands hardest
when the exchange has stayed inside the store and never explained itself.

**Separate note, not a talking-down issue:** the page currently reads `"It said
three percent," she says`. Your ruling refers to four percent throughout. Worth
a look — either the number moved in a recent pass or the reviewer misremembered
it, but the two documents disagree.

---

## 13. Ch25 — Sam recites the turret speech near-verbatim from ch18

**Ch18, Voss, to the students:**

> "That is a turret, and it puts a live round down the lane on a cycle you can
> set a watch by. Left to right, sixty metres of open ground, in front of you,
> behind the glass, and you will be firing across its path on a count you take
> off the mechanism... The target is the round. Not the turret, not a clay, not a
> plate hung off a rope. You are shooting the bullet."

**Ch25, Sam, to the captain:**

> "There's a machine at the end of the lane that puts a live round across your
> front, left to right, sixty metres of open ground, on a cycle you can set a
> watch by. You stand behind glass, taking your count off the mechanism rather
> than off the round. The target is the round. You're shooting the bullet."

**Recommendation: trim, with a real argument on the other side.**

For the defence: the captain needs it, the reader's pleasure here is watching him
receive what the reader already has, and Sam reciting his instructor's words
verbatim seven years on is characterful in a way nothing else in the chapter is.
This is dramatic irony, not talking down, and that distinction matters.

Against: it is four sentences and a whole paragraph, seven chapters after the
original, in a chapter that has already spent its exposition budget on the
fitness test. The captain does not need the mechanism to be convinced; he needs
`The target is the round. You're shooting the bullet.` The two short sentences
are what make him go quiet. The setup sentences are for the reader, who has it.

Cut to the last two sentences plus one clause of setup and it lands harder, not
softer.

---

## 14. Ch26 — the culvert regret, narrated then spoken

**Narration, after the incident:**

> The fifteen seconds before the pipe are what he carries away with him. He had
> thirty feet of open ground to read it from and he went in regardless, and that
> is the part he keeps returning to on the walk, worrying it like a bad weld.
> Whatever happened once he was inside he can account for, apart from the
> portion Ives wrote down. The seconds where he decided the culvert was worth
> going into blind.

**Sam, to the major, at the AAR:**

> "The worse part is earlier, sir. I had thirty feet of open ground to read that
> pipe from and I went in anyway. I was watching the clock instead of the pipe."

**Recommendation: trim the narration.** Tell-then-show again, and the spoken
version is better — it is shorter, it has `I was watching the clock instead of the
pipe`, which the narration does not, and it costs Sam something to say it in a
room. Keep one sentence of the walk (`worrying it like a bad weld` is worth
keeping) and lose the rest, so the AAR line is the first time the thought is
articulated rather than the second.

---

## 15. Ch20 — Ruth restates Chloe's read of the muggers

Chloe's analysis is earned: Sam asks `How.` and genuinely does not know. But
Ruth then says most of it again in different words four speeches later:

> "A gun's a prop unless you actually use it, and all of them just stood there
> holding theirs." ... "They let you walk all the way in. They gave you the
> wrist. They stood in a clump and waited their turn." ... "They fought like
> ten-year-olds, the whole seven of them, and you could have done that at that
> age."

Against Chloe's `They were all bunched between two cars` / `The one at the front
had it up and his elbow was locked out; he was holding it for show`.

**Recommendation: trim Ruth's middle sentence.** `They let you walk all the way
in. They gave you the wrist. They stood in a clump and waited their turn` is
Chloe's paragraph with the reasoning removed. `A gun's a prop unless you actually
use it` is new and should stay; `They fought like ten-year-olds` is the line the
chapter needs and is quoted back by the reviewer as a strength. Cut the three
sentences between them.

---

## 16. Ch30 — the blog and the "research team" beat re-run from ch28

Ch28 establishes the blog in detail (the fishing dispute, the summary at the top,
two or three a week, ten at night to two in the morning) and closes the research-
team beat perfectly:

> Her reply says she doesn't. It's her. Six thousand words is about a day's
> work... He doesn't reply.

Ch30 then opens by re-establishing all of it (`The rate is two or three times a
week. The pieces run long, with a five-hundred-word summary at the top...`) and
re-runs the research-team beat as a summary with a gloss attached:

> Roughly a third of those conversations end there... Another third turn into a
> second email asking the same question in different words... The pattern repeats
> often enough, the same question and then the drop-off, that she decides it's
> people being funny about credentials and stops turning it over between emails.

**Recommendation: cut most of ch30's first three paragraphs.** Ch28's single
exchange with the one man is worth more than ch30's statistical version of the
same thing, because the reader watched it happen once and can extrapolate. What
ch30 needs from this material is one line: that it keeps happening and she has
filed it under people being odd about credentials. Everything else in those three
paragraphs the reader already has.

The one sentence in that stretch worth keeping outright is `none of it registers
as a load, because her actual timetable at fourteen was heavier than this and
included getting hit.`

---

## 17. Ch16 — the Marek unfairness, dramatized then summarized

> It is not fair, and she works out on the stairs exactly how unfair it is. Marek
> does the work and keeps it. The sheet has one column and the column is for
> paper. The number that comes out of the column goes onto her record as well as
> his, and she has been asking him for it since October, and asking him is the
> whole of what she is allowed to do about it.

**Who already established it:** four scenes of Marek refusing, in which he
explains his position better than the narrator does (`Copying it out afterwards
is a receipt for something I've already done, and a receipt is a different object
from work`), plus the December sheet she folds into quarters and pockets.

**Recommendation: cut the first sentence and keep the rest, or cut the lot.**
`It is not fair, and she works out on the stairs exactly how unfair it is` is the
reader-nudge; the four clauses after it are a genuine accounting she is doing on
a staircase, which is different. If it goes, nothing is lost — the paragraph that
follows (`Marek fails the course, because a blank sheet leaves the mark scheme
exactly one option, and Chloe is the one who writes it in`) is devastating on its
own and is the better first line for the beat.

---

## 18. Ch13 — two narrator aphorisms

**(a)**

> She would rather have had a line telling her it was bad. A line she could argue
> with. A mark with no line under it leaves her only her own doubt to argue
> against, **and that's the harder version of being told she's wrong.**

Three sentences that say one thing, the third of which explains the second. Cut
the bolded clause.

**(b)**

> A plateau and a beginning look exactly alike from inside a week; only which way
> the next goes tells you which you were in.

An author-voice epigram naming the meaning of the sequence the reader is inside.
It is a good sentence, which is the problem — it is the narrator being cleverer
than the scene needs and it tips the outcome. **Recommendation: cut**, or move it
into Chloe's head as a question rather than a statement.

---

## 19. Ch18 — "The right sentence is that..."

> Priya says at dinner that the lock held, which is almost certainly true, and
> which Ruth calls the wrong sentence before Priya has finished saying it. **The
> right sentence is that a single lock stood between a lectern drawer and
> everything the table has said to each other since they were thirteen, for three
> days, and that whether it held is a question they are asking on Friday instead
> of one they had already answered on Monday.**

**Recommendation: leave, reluctantly, or give it to Ruth.** This is the narrator
articulating what Ruth said instead of letting Ruth say it, which is a Rule 1
problem in form. But it is compact, it avoids a dialogue scene the chapter does
not have room for, and the reasoning is genuinely load-bearing for what Kavi
builds next. If you want it fixed rather than tolerated, the cleanest version is
two lines of Ruth's dialogue, which also gets her voice into a chapter she is
otherwise absent from.

---

## 20. Ch31 — Ruth's denial named twice

> **The idea that the material could simply be beneath her, rather than mismatched
> to her, is available to her the whole time.** Reaching for it would mean the
> numbers she already half-suspects are the real ones, so it stays where it is.

And a paragraph earlier, the same psychology: `filed as evidence for the theory
rather than against it`.

**Recommendation: cut the first sentence.** The second says it and says it
better, and `filed as evidence for the theory rather than against it` has already
done the work two lines up.

Same chapter, one more:

> Most of the drafts die before sending, because a paragraph like that commits
> her to defending it in a way three numbers on their own don't. What she posts
> instead reads, to everyone reading it, like Ruth being Ruth: a fact, stated
> bare, no setup. **Everyone reading it in the chat takes it for the whole thought
> rather than the fourth draft of one, with no way of knowing that the drafts
> before it said the actual thing underneath the numbers before she deleted
> them.**

The bolded sentence restates the two before it. Cut it.

---

## 21. Minor, listed for completeness

Each of these is one sentence or one clause. None does much damage on its own;
together they are the residue of the habit.

- **Ch1**, chapter-closing recap: `Her day comes with a parking lot to watch, an
  Icarus to say out loud and a book taken off her in reading` — the three beats
  the chapter just dramatized, listed back. The conclusion she draws from them
  (get good at sitting there) is the part doing work. **Trim the list.**
- **Ch2**: `and all she knows about it is that being quiet is what makes her
  disappear` restates the rule stated one clause earlier. The sentence that
  follows it (`She still knows all twenty-eight of their names, and not one of
  them has needed to learn hers`) is the correct way to say it. **Cut the
  clause.**
- **Ch4**: `She has done this herself, in January with chapter nine, when Mrs.
  Aldana came down the row, took the book off her desk by the spine, and kept it
  until the end of the day.` Glossing an echo forty pages old. The sentence after
  it (`Chloe has a very clear idea of what is supposed to happen`) carries it.
  **Cut or compress to a clause.**
- **Ch5**: `She had expected the speed to feel like a punishment, and it feels
  instead like being let out` — names the feeling the whole scene carries. The
  counter-clause after it saves it. **Leave, low priority.**
- **Ch11**: `so that January, the month she stopped checking, is the month the
  notebook says it turned` — the narrator connecting two dates the reader can
  connect. **Trim.**
- **Ch20**, opening line: `They are the first to sneak out in ten years, the
  entire reason it is worth doing.` The second clause states the motive the
  chapter then dramatizes. **Cut the clause.** (The ten years figure is also on
  the reviewer's inconsistency list, which is somebody else's section.)
- **Ch23**, closing line: `and the two years everyone else is calling a wait
  become the first two of the six` — a gloss, but a clean chapter-closing turn.
  **Leave.**
- **Ch34**: two `reading down the file is like...` similes in adjacent paragraphs
  (`like watching a chart of exactly how hard somebody was still looking` and
  `like watching the same paragraph get retyped once a year`). Not talking down —
  the same device twice in fifteen lines. **Vary one.**
- **Ch35**: `Because a single log is a story somebody wrote, and logs that agree
  read closer to a fact.` A good aphorism explaining a decision the sentence
  before it already showed. **Leave or cut, your taste.**

---

# WHERE THE REVIEWER IS WRONG

Three of his named items, and one of the second reviewer's, do not survive
contact with the current text.

### Ch14, the archery geometry — he is wrong, leave it alone

He says the text "spends several paragraphs explaining the geometry" and that
"Chloe could figure it out while doing it rather than having Bell explain it to
the class." Both halves are wrong as the chapter now stands.

The geometry occupies **one** narrated sentence:

> Bell walks them down the field to show them the lanes, two firing lines seventy
> metres apart, side by side, both facing north, each bending in toward the other
> until they meet at a point where the angle holds at sixty degrees. That is
> where the flight paths cross, at the top of the arc, where an arrow released
> early from one line and an arrow released on time from the other can end up in
> the same patch of sky at the same instant, and whatever is left of them keeps
> travelling and comes down together in open grass a hundred and fifty metres on,
> behind a rope and a sign where the target block stays all year.

Everything else is Bell teaching a class, which is dramatized instruction, not
narration — and Kavi argues with him inside it, which is the opposite of a lecture.
And Chloe *does* figure it out while doing it: `It is a counting problem, and it
takes Chloe until the third week to admit that`, then the fingers against her leg
walking to dinner, then Ruth catching her at it, then the corridor, then the first
collision with Odile. The discovery is the whole spine of the chapter.

The only trimmable clause is `and whatever is left of them keeps travelling and
comes down together in open grass a hundred and fifty metres on`, and I would keep
it, because it is the answer to the question any reader asks (where do the pieces
land) and it is the only safety fact in the section.

**Recommendation: leave.** If anything was over-explained here it was fixed before
I got to it.

### Ch27, Nadia narrating her method — fixed by the rewrite, leave it alone

The reviewer's tell was exact for the old version: *they don't need it, the reader
does.* It no longer applies, because the rewrite turned the confrontation hostile
and thereby changed what the recitation is *for*.

The investigation is now dramatized first, over four paragraphs: the legal pad at
the kitchen table before eight, the state business filings, the cross-reference
against county property records, the call to the tire shop counter in the
unbothered voice of somebody scheduling a delivery.

Then in the room, the same facts come out of her mouth — but the door has been
pushed shut behind her, her plate has been read aloud twice, and a man is standing
close enough that she has to tilt her head back. In that room the facts are not
exposition, they are the weapon. And the text shows them landing: `A man at the
folding table turns a printout face down.` That is the difference between a
character telling the reader something and a character using something.

The one clause that is still method rather than threat is `It's field six, and
it's a required field, which is why you filled it in` — and it earns its place as
a sneer.

**Recommendation: leave.** Do not run this pass over ch27 again.

**One note that is not mine to fix:** the narration says `Every last one of them
typed a genuine state registration number into her employer form`, and in the room
she says `Nine of you typed a live state registration number into my form`. Also
nineteen accounts in the queue against thirteen in her accusation. Possibly all
deliberate subsets; worth one look from whoever has the numbers pass.

### Ch25, the Army PT list — largely resolved, one optional trim

The second reviewer calls it "a list dropped into the narrative" that "reads like
a briefing document." What survives the rewrite is one sentence:

> Six events, a hundred points available on each, sixty required to pass on each,
> and Sam is meeting four of them for the first occasion in his life: deadlift,
> standing power throw, hand-release push-ups, the sprint-drag-carry, a plank, two
> miles.

The scoring frame is **load-bearing** and must stay: without "six events, a
hundred points available on each," the next beat — `The score is six hundred` —
is a number with no meaning, and six hundred is the whole point of the section.
The reviewer's proposed fix (`simply say "he maxed the test"`) would cost you the
grader adding the column a second time with the pen held clear of the paper, which
is the best image in the scene.

The optional trim is the six event names. The reader does not need `standing power
throw` or `sprint-drag-carry`; the sentence works with the frame, the count of
four, and one or two named events. Against that: this book's readers are the kind
who enjoy knowing exactly what is on the test, and the section immediately after
is Sam running the events again on his own time with a stopwatch, which needs
there to be events.

**Recommendation: leave, or trim the name list only. Low priority.**

### The four percent — no change, per your ruling, but check the number

Both lines are present and both stay. Flagging only that the page says `three
percent` where your ruling says four. See item 12.

---

# WHERE THE BOOK DOES THIS WELL

The reviewer is right that the book is good at hiding. It is worth naming the
techniques, because in every case above the fix is to do one of these instead.

### 1. The answer that runs too long, so she doesn't give it

The book's single best recurring move. A character has the true answer, works out
that saying it requires four prior explanations, and says something short instead.
The reader assembles the unsaid version and the character stays in character.

- Ch1: `her dad asks whether she likes school, and Chloe opens her mouth and
  stops, because the real answer runs long and the car is nearly home. "It's
  good," she says.`
- Ch14: `to say what the small things are she has to start with the release, and
  the release needs the count, and the count needs the field and the lanes and the
  sixty degrees, while her father waits with his hand on the glass. "You mostly
  can't," she says.`
- Ch14 again, the dishes: `Chloe opens her mouth, then works out that the answer
  starts with the hat, and after the hat it needs the deadline... "That it was
  wrong," she says. "I got a B."`
- Ch17: `And Chloe has nothing at all.` followed by the list of everything she
  could have opened with, then `Which one was she supposed to have opened with?
  Why is it the rifle?`

Note what these do that a gloss does not: they show the *cost* of not saying it,
which is the actual subject, rather than the content, which is not.

### 2. The counted thing

A number in place of a feeling, every time. The reader does the arithmetic and
the arithmetic is the emotion.

- `Chloe reads her own row twice, once for the verdict and once for the margin.`
  (ch19)
- `eleven minutes, which she counts` on the conference-night corridor floor. (ch1)
- `She still knows all twenty-eight of their names, and not one of them has
  needed to learn hers.` (ch2)
- `She already knows the number, because she counted them herself the week it
  happened, before Ruth ever said so.` (ch10)
- `a column of marks, one for every day that passes without a yes` (ch7)
- `Twice in the week Chloe takes the letters out and counts them, and both times
  the count holds.` (ch21)

### 3. The object that carries it, unmentioned

- The envelope in the drawer under the socks, across eleven years and five
  chapters, never once explained.
- The strawberry magnet, which holds the appointment note, then holds a grocery
  list instead — the entire collapse of chapter 8 in one prop.
- Fen's rocks, reordered by size when a new one arrives.
- The hair tie Chloe pulls off her own wrist for Priya. (ch6)
- The mother still sitting in the car with the engine off after the Halstead
  visit, seen through a kitchen window. (ch9) — the whole of her objection,
  and not one word of it is stated.
- Kavi's file margin, annotated the same single word every year: *continuity*.

### 4. The listener's reaction instead of the speaker's state

Exactly what Rule 1's worked example prescribes, and the book does it repeatedly:

- The grandmother turning Chloe's burned hand over in both of hers, then patting
  it twice and asking about the ring. (ch18) The scene never says what she has
  understood.
- `A decade and more of parking in the overflow lot, and each of them still only
  knows the other from a folding chair.` (ch23)
- Priya's `it isn't` about the hair tie; the mother's `I wrote it down` about the
  same-day rule she was told twice. (ch4)

### 5. Letting a character be wrong and not correcting them

- Sam's `He tells anyone who asks, straight out, because to him it's a dent`.
- The grandmother's `once in a whole year is hardly a lot, is it`.
- Deb's `You don't get to know which door was the right one until you're already
  through it` — delivered as a live question, never resolved by the book.
- Ruth spending an entire chapter believing she has been put in a remedial track,
  with the narration refusing to step in.

### 6. The scene that ends one beat early

- Ch13's close: `"Then how come you're not miserable about it any more?" / "I
  don't know," Chloe says, and goes back to eating.`
- Ch31's close: `kavi: why didnt you say / ruth: because i didnt want it to be
  true`
- Ch32's close: `eli: so lets go and read it`
- Ch36's close: `By the time he sends it she has been out at the fence for the
  better part of an hour, because the mare is due and the mare keeps her own
  hours.`

Every one of the twenty-one findings above would be fixed by ending one beat
earlier than it currently does.

---

# EDIT MADE

One, and only the one already ruled on.

**Ch6, `chapters/06_the_list.md`** — the third statement of the fraction-division
thesis, Dave to Meg on the car phone. Pure deletion, no words added or changed.

Removed:

> , and after a pause, "She said getting it right and knowing why it's right are
> two different things."
>
> "What?"
>
> "That's the sentence," he says, and after another pause

The two lines below the thesis had to go with it: `"That's the sentence"` has no
referent once the sentence is gone, and leaving it orphaned would be a worse
defect than the one being fixed. Meg's `"What?"` was carried out on the same cut
because it sits between them; it was a response to the thesis specifically, not
to the fractions.

The line now reads:

> "And she explained fractions to me, not how to do them but why it works, with
> drawings, on a napkin, and then again because I asked her to," he says, and
> after a pause, "She talked at me in Spanish for about a minute and every word
> of it went by me."

The `and after a pause` construction and the paragraph rhythm are both preserved;
the beat now runs CPR, fractions, Spanish, karate, cooking, which is the list
Dave is working through anyway.

**One thing to be aware of, not fixed:** the surviving clause `not how to do them
but why it works` is itself a compressed statement of the same thesis. It reads as
a father reporting rather than a thesis in a mouth, and cutting it would gut the
line's information, so I left it. If you decide the beat should carry no version
of the thought at all, that clause is the last of it.

Chloe's own line in the same chapter (`Anybody can do the flipping...`) is
untouched, per your ruling.
