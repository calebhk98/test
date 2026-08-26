# Feedback.md author-fiat check

Scope: `passes/review/Feedback.md`, the `# AUTHOR FIAT` section and `## IV. Author
Fiat` only. Every claim checked against current chapter text. Read-only; nothing
in `chapters/` was touched.

Cross-reference: `passes/audit/AUTHOR_FIAT.md` (earlier pass) covers all eight
reviewer items plus three of its own. **Two of its required fixes have since been
applied to chapter 20** — the box clause and the fence sentence are both already
rewritten. Where that report already rules, this one states the ruling, verifies it
against current text, and does not re-argue it.

---

## 1. The footage erasure (ch 20 into ch 34)

**Claim:** Ruth's box works only on nearby networks, so the ch 34 file's erasure of
Waffle House, adjacent units, traffic and municipal camera footage is unexplained.

**VERDICT: REVIEWER MISSED A CHAPTER — and the clause that caused the miss has
already been fixed.**

Independently confirmed. The device is specified in `16_thirteen.md`, not ch 20:

> "It goes looking for recorders, anything on any network in range that's recording
> video, and about half are still on the password they shipped with, so it tries
> those first."
>
> "Then it does everything else at once, cracking, sniffing, brute force, and others
> besides. It runs the lot together and takes whichever arrives first, so it's eight
> ugly things in a box rather than one clever thing, and one of them is always
> working."
>
> "Then it writes noise into the recording every so often, over part of the file.
> Delete a file and somebody notices a file is missing. Make it noisy for a bit and
> that's a camera being a camera."

That is corruption-not-deletion and eight parallel attack paths, which is exactly
what `34_the_files.md` reports:

> All of it is unrecoverable wherever the students appear, and intact everywhere
> else. No known method.

Eight methods across mixed hardware leaves no single signature; "no known method" is
the file being precise, not the book waving a hand.

**Current ch 20 clause, quoted as it now stands** (`20_the_parking_lot.md`, para 7):

> Ruth brings her box, which throws all its ugly things simultaneously at any
> recorder in range and writes noise over whatever it reaches

The old reductive version (default passwords only) is gone. Both reviewers read the
old clause. The prior audit's one *required* fix is **done**.

Range still holds up on the page: the box walks the route and runs all night — Ruth
carries the bag over the fence, and "Ruth shuts the box off in the corridor" on
return — with two hours of dwell time in the booth.

**Residual, one item only.** The pole-mounted municipal camera is the single recorder
in the ch 34 list that would not plausibly be on a network a passing box can join.
Everything else is covered.

**Smallest fix (optional):** one chat line in ch 34, from Ruth, in the run at lines
72-78 where she is already talking about the box:

> ruth: the diner i understand. the pole camera up the road i do not.

It costs nothing and converts the one soft spot into a named mystery.

**Second optional line, still not applied.** The larger sub-claim — the observation
unit's own recordings gone — is paid for nineteen chapters earlier and never cashed:
ch 15 establishes this class of federal team runs consumer gear on factory defaults,
and the box tries factory defaults first. One line from Kavi in the ch 34 chat joins
them. Not required.

**Severity: was high, now low.** A reader who has read ch 16 will not stumble. The
damage was done by the old ch 20 clause and it is repaired.

---

## 2. The eight-foot chain link fence (ch 20)

**Claim:** Three sixteen-year-olds clear an eight-foot fence, one "in one clean vault".

**VERDICT: ALREADY PAID FOR IN THE TEXT — and the misreading has been edited out.**

No height is stated anywhere in the manuscript. `grep -ri "eight foot|eight-foot|eight
feet"` across all thirty-six chapters returns nothing. The sentence the reviewer
parsed as a height was a *distance* and now reads (`20_the_parking_lot.md`):

> There is chain link a few strides behind them and a loading dock on the other side
> of it, and the three of them are over the fence and gone before the man at the
> front has finished turning his head to follow. [...] Chloe is half a second behind
> her, over the rail in one clean vault. [...] The fence drill has been run at this
> speed every term since they were nine

The vault is paid by the drill line. The prior audit's disambiguation fix is **done**.

**Fix: none.** Claim is stale.

**Severity: none. A reader would not notice.**

---

## 3. The ch 15 radio exploit

**Claim:** An elite federal team on commercial radios with default six-digit factory
pairing codes, broken by a twelve-year-old in four seconds.

**VERDICT: ALREADY PAID FOR IN THE TEXT.** Covered by prior audit item 8; verified
unchanged. Not duplicating the full argument.

Current wording, `15_twelve.md`:

> "It's AES-256," he says. "But, it's a six-digit pairing code and they never changed
> it off default." [...] "It's four seconds of compute. It's not even interesting."
>
> "Because the box says AES-256," Kavi says. "The box always says AES-256."
>
> Ruth reads over his shoulder, "They're almost certainly actors, look at this. This
> is a consumer handset with a default code. My dad's work has better than this and
> my dad sells insurance."

What the book pays, all still on the page:

- **The payload is a dud.** "The problem is that they barely talk. Two transmissions
  in six minutes, both of them position checks [...] One of them said he's at the
  corner and one of them said copy. That's it." Kavi wins instantly and gets nothing;
  Sam still has to build a plan and Chloe still has to walk in as bait.
- **The amateurism is a clue the characters read**, not a convenience handed to them.
- The marketing claim is named as a marketing claim.
- The grade sheet later itemises the night's failures, including "Traceable agent
  selected" and "Four personnel deployed where three would have served" — the
  institution scores its own sloppiness.

**Fix: none required.**

**Severity: low.** A reader with radio knowledge may raise an eyebrow at the ease; the
worthless payload absorbs it within a page.

---

## 4. Theo gets the retirement box (ch 29)

**Claim:** The nineteen-year-old classified file on Halstead lands on the desk of the
one person in the building who went to Halstead.

**VERDICT: NEEDS AUTHOR DECISION.** Covered by prior audit item 3; still live and
unchanged in the text.

The coincidence itself is cheap-but-fine and paid in the usual currencies
(`29_the_file.md`): the box is a routine artefact of a twenty-six-year retirement,
handed over for a reason that is not about him — "Somebody has to read it eventually.
Might as well be the new guy." — the Halstead folder is "near the bottom" after ninety
minutes of embassy postings and shipping manifests, and it takes him a day and a half
to work out what he has.

The sharper problem, unchanged: `34_the_files.md` establishes the unit tracks all
ninety-one graduates by "Address, employer, family, where their parents work, where
everybody banks", and specifically logs that Chloe "has recently accepted employment
requiring a background investigation." So the unit tracks its subjects into federal
employment — and hands one of them the box. That is a counterintelligence question,
not a coincidence question, and nobody in the book raises it.

The book may already answer it, in ch 34:

> Theo's has a note on it that makes him close the laptop with both hands, the careful
> two-handed close of something that might spill, and go outside for twenty minutes.
> [...] That's the whole account anyone else gets of it.

**The decision the author owes himself:** if that note says his employment was known
or permitted, the retirement box is setup rather than coincidence and nothing needs
changing. If it does not, one line — from Kavi, who annotates everything, or Chloe,
who reads the file as a translation problem — should notice that a graduate works in
the building.

**Severity: medium if unresolved.** Both reviewers reached for it, so readers do too.

---

## 5. University admission rate (ch 21)

**Claim:** "Ninety-one out of ninety-one bought something" implies a near-100 percent
admission rate.

**VERDICT: ALREADY PAID FOR IN THE TEXT.** Covered by prior audit item 7; verified.

The headline number is not an admission rate. `21_the_applications.md`, paragraph 7,
establishes that every list contains a guaranteed admit:

> the Ivies first, eight of them, bought like lottery tickets and forgotten about by
> dinner; then the college a parent went to; then the community college an hour from
> home, quietly listed by everybody and named out loud by almost nobody

Ninety-one of ninety-one placing *somewhere* is unremarkable. The real load is the
top-end hit rate ("Twelve of fourteen, every time I count them."), and the chapter
pays for that from the admissions side rather than asserting it: offices asking for
the real transcript, the ghostwriting theory raised and killed by laying essays side
by side ("no two of them argue alike, and a pair of the ninety-one take opposite
positions on a question with both worth reading"), the Penn officer reading a sentence
three times before she picks up the phone, thirty-plus institutions with open files by
January, the Caltech representative's whole day in a windowless room.

One thing to be deliberate about, not to change: Chloe's store-sign line is a
rationalisation by a seventeen-year-old, not the book's thesis. Per
`CALIBRATION_AUDIT.md` §2 these characters must explain away contrary evidence.
Strengthening it would break the calibration.

**Fix: none.**

**Severity: none.**

---

## 6. Seven students find the founder in sixteen weeks (ch 32)

**Claim:** Seven people with day jobs beat nineteen years of federal work.

**VERDICT: ALREADY PAID FOR IN THE TEXT, one line short.** Covered by prior audit
item 4; the suggested line has **not** been added.

The chapter pays in visible failure and iteration, a month of rehearsal on a system
they own, the grind rather than a montage, and above all a stated methodology rather
than an assertion (`32_the_money.md`):

> ruth: the government is arguing from absence. theyre saying "no state would leave
> this little" and thats not evidence, thats a shrug
>
> ruth: im arguing from presence

Then three concrete tells: unexplained three-to-five day gaps, a seven-hour decision
band drifting forty minutes across two decades, an instrument preference held since
2003. Those are claims only a private party holding the full time series can make.

The missing joint is *why* the government could not hold that series. The answer is in
the next chapter and nobody connects it — `33_the_other_one.md`:

> ruth: section 1030, eli. unauthorized access to a nonpublic government system, five
> years first offense, ten if theres a financial angle attached

**Smallest fix:** one chat line in ch 32, immediately after

> sam: twenty years and were the first people to look? that cant be right
> nadia: somebody has to have looked
> kavi: who though. needs motive and funding.

add to Kavi's line, or as the next line:

> kavi: theyre not the first to look. theyre the first who could do it illegally.

In register, in character (Kavi already supplies the framing question), and does not
explain anything to the reader that a character would not say.

**Severity: low-medium.** A reader notices the size of the claim; most will accept it
on the drift argument alone.

---

## 7. Seventy-five men sent for Priya (ch 36)

**Claim:** Seventy-five armed men for one twenty-year-old is an absurd expenditure.

**VERDICT: ALREADY PAID FOR IN THE TEXT.** Covered by prior audit item 5; verified.

The number is paid five ways in `36_seventy_five.md`. Priya raises the absurdity
herself rather than accepting the flattering reading:

> priya: then tell me why seventy-five was the number, because whoever picked
> seventy-five was working off something
>
> priya: if those two are what they say they are, then one of them on his own should
> be worth a sam and then some, and there were seventy-five

Capture-not-kill is demonstrated, and the obvious counter-question is answered in
dialogue: "you do not put those in a person, because a person watches you raise it and
steps left". The quality is downgraded in her calibration, not the narrator's: "they
came in like thirteen year olds. a couple of fourteens." And Ruth prices the geometry
privately and keeps it to herself, which is the house style working.

**Fix: none for the number.** See item 11 for the aftermath.

**Severity: none.**

---

## 8. Marek fails and nothing happens (ch 16)

**Claim:** Marek refuses to submit work, fails, and the consequences are waved away.

**VERDICT: ALREADY PAID FOR IN THE TEXT.** Covered by prior audit item 9; verified.
The second reviewer reaches the same conclusion in Feedback itself.

`16_thirteen.md`:

> Marek fails the course, because a blank sheet leaves the mark scheme exactly one
> option, and Chloe is the one who writes it in. In January he is at breakfast as he
> was in December, in his own year, working through the building, so whatever a fail
> costs a student here, expulsion is no part of it. What it does cost, whether it
> follows him onto anything that matters, whether anybody sat him down about it, stays
> outside her reach for years, and she is careful for a long time about how she asks.

The gap is named, attributed to a character's position (a thirteen-year-old teacher
with no standing to ask), and shown persisting for a decade. That is withholding, not
fiat.

**Fix: none.** One caution carried forward from the prior audit: this is only a held
card if a later volume pays it. Belongs on the outstanding-promises list, not here.

**Severity: none.**

---

# The three items the earlier audit raises and this reviewer does not

All three verified against current text. **All three are still live.**

## 9. Chloe's clearance generates no friction

**VERDICT: REAL FIAT (by omission).** Still the most exposed unpaid item in the book,
and nothing has been added since the earlier audit.

Three acts, all on monitored federal systems, all frictionless:

- She writes the intrusion rules. `33_the_other_one.md`: Theo will not put his name on
  a document describing how to break the law he is paid to uphold, "So it goes to
  Chloe." She signs "the night she finishes the last of it" and is "four months into
  that job when she writes those pages".
- She reads the stolen file at her federal desk. `34_the_files.md`: "Chloe reads hers
  at her own desk, five months into a job whose clearance she is stretching a long way
  past its purpose to do this. The government badge is still clipped to the strap of
  her bag".
- She runs a query at work. `36_seventy_five.md`: "The search she runs mid-morning has
  an entirely different name in the box, and what comes back is a form number she saw
  once already that morning, in a message from a man across town who is careful about
  what he puts in writing. The entry is read and closed".

The only acknowledgement in the book is `33_the_other_one.md`: "What that actually
costs her she works through exactly once, on the drive home from the office the week
the document arrives, and the thought ends in about as long as it takes a light to
change." That establishes she is not thinking about it. It does not establish that the
system is not.

Why it stands out here specifically: everyone else pays. Sam's range score generates
four documents that travel upward. Nadia's confrontation costs her the latch, the
plate read aloud twice, the till counted three times. Eli's five vulnerabilities get
him a lawyer. Theo's refusal is dramatised over nine days. Chloe's exposure is the
largest and is the only one that generates nothing.

**Smallest fix: one sentence in ch 36**, appended to the search paragraph:

> The search is one of eleven she runs that morning, and the only one she could not
> defend to anybody who pulled the log.

Fact about her morning and about her, not an explanation to the reader. Converts the
last movement of the book from oversight into suspense.

**Severity: high. A reader who works anywhere near a cleared job will notice
immediately.**

## 10. The traceable sedative thread

**VERDICT: REAL FIAT (dropped thread), or an undeclared held card.** Verified: the
whole book contains exactly three references to it, all in ch 15.

`15_twelve.md`:

> "They're actors," Ruth says, reading the vial and putting it back. "If they get a
> work physical in three weeks they're going to fail it and they're going to have to
> explain why."

Ruth loses that argument, they use the traceable agent, and the grade sheet dings them
for it: "Traceable agent selected." So four federal operators went home with a
traceable school-issued drug in their blood, and the file in ch 29 and the file in
ch 34 never pick it up — which is conspicuous in a book that otherwise pulls every
thread it plants.

**Smallest fix, if the author wants it closed:** one line in the ch 29 file summary,
in the register of the surrounding document, e.g. a line noting a medical follow-up on
the four operators with no result recorded. Alternatively leave it and log it as an
outstanding promise alongside Marek.

**Severity: low-medium.** Only a reader tracking the ch 15 grade sheet will feel it,
but that is exactly this book's reader.

## 11. Nobody comes back for Priya's two prisoners (ch 36)

**VERDICT: REAL FIAT (by omission).** Verified unchanged. The number is paid (item 7);
the aftermath is not.

`36_seventy_five.md`, the entire account of the two men:

> What she says about them over the following week arrives in pieces, and all of it is
> logistics. The smaller one has a knee that wants ice twice a day. The pair of them
> eat more than she budgeted for, and one of them puts every piece of onion on the
> edge of the plate. By the Thursday one of them says good morning first. By the
> Saturday the other is sitting up when she comes in with the tray.

Seventy-five men, three vans and two disabled engine blocks in a foreign country
produce no local police, no diplomatic noise, no second visit and no retrieval
attempt. The beat itself is one of the best in the chapter; the silence around it is
the problem.

**Smallest fix: one chat line from Priya**, in the run after "eli: you took prisoners
/ priya: i took two men who were asleep in a field in october":

> priya: nobody has come for these two. that is the part i keep coming back to

Turns an absence into an observation, which is the technique the book uses everywhere
else. She already uses "the bit i keep coming back to" about the darts in the same
chapter, so the phrasing is in her mouth.

**Severity: medium. A reader will feel the quiet without being able to name it.**

---

# Summary

| # | Claim | Verdict |
|---|---|---|
| 1 | Footage erasure, ch 20 into ch 34 | **Reviewer missed a chapter** (ch 16 specs the box); ch 20 clause already fixed; one residual, the municipal pole camera |
| 2 | Eight-foot fence, ch 20 | **Already paid for** — no height in the text; the misparsed sentence is already rewritten |
| 3 | Radio pairing code, ch 15 | **Already paid for** — the win's payload is deliberately worthless |
| 4 | Theo's retirement box, ch 29 | **Needs author decision** — what the note on Theo's own file says |
| 5 | Admission rate, ch 21 | **Already paid for** — the headline number is not an admission rate |
| 6 | Founder in sixteen weeks, ch 32 | **Already paid for**, one chat line short of airtight |
| 7 | Seventy-five men, ch 36 | **Already paid for** — the objection is in the beneficiary's mouth |
| 8 | Marek, ch 16 | **Already paid for** — named withholding, not a gap |
| 9 | Chloe's clearance, ch 33/34/36 | **Real fiat** — one sentence in ch 36 |
| 10 | Traceable sedative, ch 15 | **Real fiat / dropped thread** — one line in the ch 29 file |
| 11 | Priya's two prisoners, ch 36 | **Real fiat** — one chat line from Priya |

Of the eight reviewer claims, none is fiat. Two were misreadings of text that has
since been repaired anyway. The three live items all come from the earlier audit, and
each costs one line.
