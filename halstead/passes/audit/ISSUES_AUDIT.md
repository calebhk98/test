# `passes/review/Issues.md`, audited item by item

Every numbered item in the 884-line file, checked against `chapters/` as it
stands today. Read-only pass: **nothing in `chapters/` or `characters/` was
edited.** Other agents are editing concurrently, so every quotation below was
re-grepped at the time of writing; quotes are the citation, line numbers are a
convenience only. Re-grep before acting.

`Issues.md` is **four** reviews concatenated, not two. They are labelled here:

| tag | review | items |
|---|---|---|
| **A** | `### 1.` … `### 6.` plus "Summary of What to Fix" | A1-A6 |
| **B** | `# PROSE ANALYSIS` — ISSUE 1-11, Opportunities 1-6, two scene rewrites | B1-B11, BO1-BO6, BS1-BS2 |
| **C** | `# Prose Issues in the Text` — 1-20 (6 and 12 are missing from the source) | C1-C20 |
| **D** | `# PROSE NOTES — A REVISION CHECKLIST` | D1-D13 |

## Instruments used

All figures are from `chapters/`, not `HALSTEAD.md`, and all corpus figures are
the same 23 reference books the repo's other measures use.

- `python3 tics.py` — 29 constructions, book / target / corpus median / corpus max
- `python3 absolutes.py` — absolutes by book, narration and dialogue
- `python3 grade.py` — per-chapter structure, band averages, voice separation
- `python3 voice_separation.py` — per-speaker dialogue profile
- Four ad-hoc measures written for this audit, described where they are used:
  the number+action composite, the dialogue subordinator rate, per-speaker
  category-construction rate, and scene-end/scene-open shape.

## The one-line headline

`tics.py` says **2 of 27 rows are over target and both are over by 2%**. That
is true and it is not the whole picture, because three of the loudest things
these reviewers complained about are **not rows in `tics.py`** and all three
are running above every book in the corpus:

1. **Dialogue subordination.** 26.9% of spoken lines carry a
   *because / so / since / which*, against a corpus maximum of 16.9%. `because`
   alone is on 10.9% of lines against a corpus maximum of 3.3%.
2. **The number + physical action composite.** 5.1% of all sentences, against a
   corpus maximum of 1.9%. The individual number words are all at target; the
   formula they sit inside is not counted anywhere.
3. **`both hands`.** 33.6 per 100k against a corpus maximum of 7.2.

Everything else worth doing is downstream of those three.

---

# REVIEW A

## A1. The "number + physical action" sentence formula

**Claim:** a rigid formula, `[character] + hyper-specific small physical action
+ exact count + before/while/instead of + speaking`, used fifty-odd times.

**VERDICT: STILL LIVE. The worst-measuring construction in the book after the
dialogue subordinator, and no instrument currently tracks it.**

### Measurement

Sentences carrying a number word, a unit noun (*second, minute, inch, step,
beat, time, turn, breath, pace, foot, metre*) and a body-action verb (*shifts,
turns, holds, waits, presses, sets, leans, lifts, taps, folds, reaches*), against
the same 23 books:

| | book | corpus low | median | high | percentile |
|---|---:|---:|---:|---:|---:|
| number + unit + body verb, same sentence | **5.07%** of 3,826 sentences | 0.14% | 0.55% | 1.91% | 100 |
| tight form, `N <unit>` adjacent + body verb | **1.75%** | 0.03% | 0.09% | 0.31% | 100 |

**2.7x the highest of twenty-three novels on the loose form, 5.6x on the tight
form.** 194 sentences and 67 sentences respectively.

This is the failure mode `passes/TIC_BRIEF.md` warned about, in a shape the
brief did not anticipate. The number-word rows in `tics.py` all pass — *eleven*
9.6 against a corpus max of 10.3, *nine* 30.7 against 31.2, *four* 115.7 against
119.3. The precision was not deleted, it was redistributed into a sentence shape
nothing counts.

Three that are in the text now:

> Chloe shifts the clipboard half an inch, squares it, and looks up.

> Chloe had held his sleeve a second longer than the door needed, and not
> knowing whether this is the kind of appointment you bring a dad to, she reads
> the waiting room instead.

> She reads the line back twice before adding a new line at the bottom with the
> date, then puts the notebook in the drawer and goes down to dinner two steps
> at a time.

**Fix.** Add the composite as a row in `tics.py` so the number stops hiding, and
set the target at the corpus maximum, 1.9% loose. Then delete the count, not the
action: *shifts the clipboard half an inch, squares it* → *squares the
clipboard*; *held his sleeve a second longer than the door needed* → *held his
sleeve after the door was open*; *goes down to dinner two steps at a time* is
fine as it stands because the count is the action. The test is whether the
sentence loses anything when the figure comes out. On the 194 hits, most of the
time it does not.

**Work:** one instrument row, then a sweep of 194 sentences to get to ~72. Two
agent-days. **Severity: HIGH.**

---

## A2. Syntactical monotony: the comma-splice / polysyndeton rhythm

**Claim:** almost every paragraph is compound sentences chained by *and*,
*, and*, *, so that*, *, which*; almost zero cadence variation.

**VERDICT: SPLIT. The comma-splice half is REVIEWER WRONG. The monotony half is
STILL LIVE and is the largest single structural finding in this audit.**

### Measurement

Comma splice (independent clause, comma, independent clause, no conjunction):

| | book | corpus low | median | high | percentile |
|---|---:|---:|---:|---:|---:|
| candidate comma splices | 1.80% of sentences | 0.69% | 2.14% | 7.95% | **39** |

The book splices *less* than the median novel. That part of the complaint is
not real.

Cadence variation is a different story:

| measure | book | corpus low | median | high | pct |
|---|---:|---:|---:|---:|---:|
| sentence-length variation (CV%) | 72.29 | 64.29 | 85.30 | 100.57 | **4** |
| sentences under 10 words % | 25.83 | 21.62 | 45.67 | 71.82 | **4** |
| sentences inside a run of 3+ short ones % | 4.85 | 3.49 | 17.11 | 48.25 | **4** |
| sentences with a subordinate clause % | 36.31 | 8.33 | 22.24 | **36.27** | **100** |
| sentences with a relative clause % | 30.52 | 7.76 | 19.55 | **29.97** | **100** |
| sentences with neither % | 47.81 | **49.73** | 65.86 | 85.30 | **0** |
| words per sentence | 21.04 | 8.50 | 14.27 | 22.85 | 96 |
| sentences with 2+ "and" | 17.47 | 4.24 | 11.72 | 25.83 | 83 |

Read the last four rows together: the book carries **more subordinate clauses
than any of the twenty-three books, more relative clauses than any of them, and
fewer bare simple sentences than any of them**, while sitting in the bottom 4%
for every measure of variation. The polysyndeton itself (17.47%, 83rd
percentile) is inside the corpus range. It is the subordination and the absence
of short sentences doing the damage, not the *and*s.

**Fix.** This is the same fix as D12 and it is mechanical: every page needs one
sentence under ten words. The cheapest source is the existing subordinate
clauses, which mostly want to be their own sentence. Not new material, a knife.
*"There are thirty subtraction problems on the worksheet and all thirty are the
same problem, which she works out partway through the second, eight minus three,
so the other twenty-eight are that again with different numbers"* becomes
*"There are thirty subtraction problems on the worksheet. All thirty are the
same problem. She works it out partway through the second, eight minus three."*
Same content, same reading grade band, three sentences.

**Work:** a per-chapter pass with `grade.py --one <n>` as the gate; target the
CV up from 72.29 toward the corpus median 85.3, and u10 up from 25.8 toward 35.
Six to eight agent-days across 36 chapters. **Severity: HIGH.**

---

## A3. Chronic physical restraint tics ("hands flat", "turning objects")

**Claim:** everyone puts their hands flat on tables and turns objects a quarter
turn; ears go hot, jaws set, feet dangle.

**VERDICT: MOSTLY ALREADY FIXED, and the measurements prove it. One gesture the
reviewer did not name is worse than every gesture he did name.**

### Measurement, `tics.py` (per 100k words)

| gesture | book | target | corpus med | corpus max | status |
|---|---:|---:|---:|---:|---|
| hand(s) flat | **5.3** | 10.0 | 0.0 | 1.8 | pass, at 53% of target |
| turning an object | **6.1** | 6.0 | 0.0 | 2.8 | 2% over target |
| the word 'flat' | **28.0** | 35.0 | 8.1 | 39.7 | pass, **below the corpus max** |
| eyes on / eyes down | **7.0** | 12.0 | 1.9 | 14.7 | pass, **below the corpus max** |

Ad-hoc counts for the gestures the reviewer named that `tics.py` does not track:

| gesture | instances, whole book |
|---|---:|
| jaw (set/tight/working) | 8 |
| ears going hot | 1 |
| thumbnail pressed into something | 2 |
| feet/heels dangling or not reaching the floor | 2 |
| corner of her/his mouth | **0** |

"Hands flat" is at a third of its old rate and 53% of target. "Ears hot" is one
instance in 113,000 words. "Corner of the mouth", which review D also names, has
been eliminated entirely. **This complaint does not hold at these rates.**

### The one that does hold, and it is not on the reviewer's list

| | book | corpus low | median | high |
|---|---:|---:|---:|---:|
| `both hands` | **33.6** /100k (38 uses) | 0.0 | 0.0 | 7.2 |

**4.7x the highest of twenty-three books, and the corpus median is zero.** Also
above every book, at small absolute counts: `a quarter turn` 3.5 (4 uses),
`under her/his breath` 5.3 (6 uses), `sets/puts it back down` 1.8 (2 uses).

`both hands` is now doing exactly what `hands flat` used to do: it is the
book's universal two-handed gesture and it belongs to everybody. Present-text
examples, three different characters in three different chapters:

> The head of school hands her the folder with both hands and says her name
> once, correctly, plain.

> Theo's has a note on it that makes him close the laptop with both hands, the
> careful two-handed close of something that might spill

> Chloe does two of them, working down each ribcage with both hands flat,
> counting under her breath

The third one carries `both hands`, `flat` and `under her breath` in a single
clause.

**Fix.** Add `both hands` to `tics.py` with a target of 12 per 100k (a third of
current, still 1.7x the corpus max, consistent with how every other target in
that file was set). Then apply the rule the TIC_BRIEF already states: where two
characters share a gesture, one loses it. Theo's two-handed laptop close is
characterising and should stay; the head of school handing over a folder with
both hands is filler and the phrase can simply come out.

**Work:** one instrument row plus a 38-instance sweep. Half an agent-day.
**Severity: MEDIUM.**

---

## A4. The "X is a different category from Y" construction

**Claim:** every character wins arguments by re-sorting two things into
different classes, and *this is the single reason readers thought all the
characters sound the same*.

**VERDICT: REVIEWER WRONG ON THE CAUSE. The construction is real but rare and
too thin to explain anything. The actual cause of voice sameness is measurable,
it is one clause type, and it is in A2/D1 above.**

### The construction, measured

Twelve regex families for "re-sorts two things into different classes" run over
every quoted line in the book: *that's not X that's Y*, *X isn't Y it's Z*,
*a different thing / kind / category / object*, *not the same thing as*,
*a fact about X not a fact about Y*, *X is one thing and Y is another*,
*that's not what X is*, *is a rule, not a Y*.

**30 raw hits. Four are false positives on reading. 26 genuine instances in
113,435 words — roughly 23 per 100,000, or one every 4,400 words.**

Attributed by hand from surrounding context:

| speaker | instances |
|---|---:|
| Chloe | 7 |
| Ruth | 5 |
| Sam | 3 |
| her mom | 2 |
| Nadia | 2 |
| her dad | 1 |
| Priya | 1 |
| Kayleigh (playground child) | 1 |
| Marek | 1 |
| the maths teacher | 1 |
| camp staff | 1 |
| **Kavi** | **0** |

Same measure run through `voice_separation.py`'s tagged-line attribution, as a
share of each speaker's tagged lines: dad 3.2%, mom 1.9%, Ruth 1.4%, Chloe 1.0%,
Sam 0.0%, Kavi 0.0%, Nadia 0.0%, Priya 0.0%.

So: the reviewer is right that it is not confined to one character, and wrong
about the density. Chloe carries 27% of it, which is what you would expect from
the protagonist of a book whose good scenes are arguments. Kavi, whom the
reviewer names specifically, never does it once. The narrow `tics.py` row
`'that's not X, that's Y'` is at **1.8 per 100k against a target of 2.0 and a
corpus maximum of 1.8** — it is at the corpus ceiling, which for a book built on
argument is where it should be. Review D9 counts this construction at "perhaps
eighty times"; it is now about two.

**A construction appearing once every 4,400 words cannot be why readers thought
everyone sounds the same.** Something on nearly every line has to be, and there
is one:

### What is actually doing it

Every quoted line in the book, 2,006 of them, against the same 23 books' quoted
lines:

| | book | corpus low | median | high |
|---|---:|---:|---:|---:|
| spoken lines carrying *because / so / since / which / whether* | **26.9%** | 1.9% | 6.0% | **16.9%** |
| spoken lines carrying *because* | **10.9%** | 0.3% | 0.9% | **3.3%** |
| spoken lines of 3 words or fewer | **14.2%** | **11.3%** | 33.8% | 45.9% |

The book is **59% above the most subordinating book in the corpus** (Little
Women) and **3.3x the highest `because` rate of any of them**. It has the
second-lowest share of short lines of the twenty-four texts.

By age band, which is the part that matters:

| band | lines | *sub* % | *because* % | ≤3 words % |
|---|---:|---:|---:|---:|
| ch01-10, Chloe age 6-8 | 733 | **31.2** | **16.2** | 13.5 |
| ch11-15 | 479 | 27.8 | 9.8 | 12.9 |
| ch16-22 | 508 | 26.2 | 8.5 | 13.8 |
| ch23-36, adult | 286 | 15.7 | 3.5 | 18.5 |

**The six-to-eight-year-olds are the most heavily subordinated speakers in the
book**, at nearly five times the corpus maximum for `because`.

Per speaker, tagged lines only (biased short, comparable between speakers):

| speaker | lines | mean words | *sub* % | *because* % | ≤3 words % |
|---|---:|---:|---:|---:|---:|
| dad | 31 | 8.8 | 25.8 | 9.7 | 19.4 |
| Chloe | 100 | 9.3 | 21.0 | 8.0 | 28.0 |
| Kavi | 29 | 9.4 | 20.7 | 13.8 | 24.1 |
| Ruth | 69 | 9.6 | 18.8 | 8.7 | 20.3 |
| mom | 53 | 10.8 | 17.0 | 9.4 | 24.5 |
| Nadia | 15 | 7.8 | 13.3 | 0.0 | 13.3 |
| Priya | 9 | 7.4 | 11.1 | 11.1 | 33.3 |
| **Sam** | 63 | **5.8** | **7.9** | 4.8 | **41.3** |

Sam has a voice. Nadia has half of one. Chloe, Ruth, Kavi, mom and dad are one
speaker at five names.

**Fix.** The reviewer's own mechanical prescription in D1 is the right one and
it is cheap: mark every *because / so / since / which* in a page of dialogue,
and if more than a third of lines carry one, delete until they do not. Most of
those clauses can simply come out, because the reason is already in the scene.
Concretely, from ch09, at the emotional peak of Part 1, three lines running:

> "Baby, breathe for me, just breathe, **because you have to breathe before you
> can talk about any of it**."
>
> "Do what, **because you have to tell me what it is and then I'll fix it,
> whatever it is**."
>
> Chloe can't answer that, **because school, the sheets and Kayleigh Burns are
> each a piece of it** …

Struck: *"Baby, breathe for me, just breathe."* / *"Do what? Tell me what it is
and I'll fix it."* Nothing is lost, and the mother stops explaining her own
imperatives to her sobbing child.

Then give three characters a standing rule, per D1: **Ruth states and does not
justify. Kavi answers before he explains, in a second sentence or not at all.
Sam already has his rule and should keep it.** Chloe keeps the *because* — she
is the one character for whom it is characterisation rather than habit, and if
everyone else drops it, it becomes hers.

**Work:** the largest job in the book. Book-wide dialogue pass, gated on the
26.9% figure coming to 15% or below and the ch01-10 `because` rate coming to 5%.
Ten to fourteen agent-days. **Severity: HIGHEST. This is the fix that changes
what a reader feels.**

---

## A5. Summary dumping instead of dramatising the aftermath

**Claim:** the most dramatic scenes are delivered as retrospective summary over
a meal or in a chat log. Three named: the 4am federal breach, the Waffle House
mugging, Priya's 75-man ambush.

**VERDICT: ONE OF THREE HOLDS, AND IT IS THE LAST CHAPTER OF THE BOOK.**

### Waffle House — REVIEWER WRONG

Chapter 20 dramatises the fight in real time across roughly forty lines,
present tense, blow by blow:

> The front one says hey and then says it again and Sam is inside four meters,
> then three, and the gun that was waving is waving at something much too close.
> Past the muzzle, he takes the wrist and turns it out and down until the man
> bends, strips the gun one-handed while he's still folded over, and throws the
> slide under a parked car.

Chapter 34's police-report version is a deliberate later echo of a scene the
reader has already lived. The reviewer appears to have read ch34 and not ch20.
Ch20 also carries the book's highest cadence variation, CV 95.0 and 40.0% short
sentences against a book median of 68.6 and 21.9 — the prose does exactly what
the reviewer elsewhere asks for.

### The nine-minutes breach — REVIEWER WRONG

Chapter 35 opens inside the moment, at Eli's desk and then at Kavi's, and only
moves to chat after the discovery:

> A check-in doesn't arrive. Nine minutes later, everything is precisely where
> it should be. State, position, byte for byte what it was.

Chat is 12.4% of that chapter.

### Priya's seventy-five — STILL LIVE, and badly

Chapter 36 is the last chapter of the novel. Its climax — a woman fighting
through seventy-five trained men and going over a wall — is delivered entirely
as chat transcript, after the fact, in Priya's own clipped typing:

> priya: tuesday night there were seventy-five
>
> priya: give or take. there were more behind the line i never got to
>
> sam: how long
>
> priya: a while

**Chat is 40.6% of chapter 36 by word count** — 57 lines, 821 words — the second
highest share in the book after ch24, which is a chapter *about* the chat.
Book-wide chat is only 4.6%, but it is concentrated: every chapter from 24 to 36
carries some, and the last chapter carries the most.

The reviewer's framing note is worth keeping in view: the device *is* the book's
argument about how these people report themselves. That argument has been made
by ch36. Making it a fourth time, on the climax, at 40%, spends the last chapter
of the novel on a form the reader has already understood.

**Fix, in bounds.** Do not narrate the ambush and do not add a paragraph
explaining it. Give the chapter a real-time frame that is not the fight:
**Priya typing.** She is in the room over the feed merchant's, which the chapter
already establishes, and the chat lines are being written by hands that a page
earlier were shaking. Interleave the existing chat lines, unchanged, with what
that room and those hands are doing between messages — the lock she changed
herself, the gap before "a while", the phone going down and coming back up. The
reader gets the seventy-five through the chat, as now, and gets the cost through
the woman typing it, which is the thing the chat is designed to omit. No new
narration of the fight, no commentary, no one explaining anything.

**Work:** one chapter, roughly 800 new words of frame around existing lines.
Two agent-days. **Severity: HIGH — it is the ending.**

---

## A6. The clock and time obsession

**Claim:** almost every paragraph carries an explicit time measurement.

**VERDICT: PARTLY LIVE, and the live part is A1, not this.**

### Measurement

| | count | per 100k |
|---|---:|---:|
| `N second(s)/minute(s)/hour(s)` | 249 | 219.1 |
| "seconds" any use | 323 | 284.2 |
| "minutes" any use | 167 | 146.9 |
| explicit clock times ("11:40", "eleven forty") | **6** | 5.3 |
| `inside a/N <unit>` | 26 | 22.9 |

And from `tics.py`, the construction the reviewer describes as the secondary
version — precision hedged with "about":

| | book | target | corpus med | corpus max |
|---|---:|---:|---:|---:|
| hedged exact (`about N`) | **5.3** | 18.0 | 10.9 | 57.3 |

The hedged-exact tic is **below the corpus median** and at 29% of its own
target. That half of the complaint is dead. Explicit clock times are six in the
whole book. `grade.py`'s number audit shows the book at 17.0 numbers per 1000
words against a corpus range of 4.9 to 17.6 — inside the range, at the top of
it — and using 70 distinct values against a corpus median of 39, which is the
opposite of the "same three numbers" complaint in D3.

What is left is duration counting, and it is not a separate problem from A1:
most of the 249 duration phrases are the composite formula measured there.
**Fix it once, in A1.** No separate work item. **Severity: covered by A1.**

---

## A-Summary. "Summary of What to Fix"

Four bullets, all restatements: break the cadence (= A2), diversify physical
habits (= A3), diversify argumentative styles (= A4), show real-time scenes
(= A5). No separate verdicts. One caution: bullet 2 asks for "biting nails,
tugging earlobes, pacing, slumping, cracking knuckles, picking lint". Those are
stock. D6's version of the same instruction is better because it assigns
gestures to named people, and `passes/TIC_BRIEF.md` already carries it.

---

# REVIEW B — "PROSE ANALYSIS"

## B1. The "understatement trap"

**Claim:** joy, grief, terror and a maths worksheet all get the same flat
observational cadence.

**VERDICT: STILL LIVE, in a precise and narrower form than the reviewer states.
The book modulates for violence and does not modulate for feeling.**

### Measurement

Sentence-length variation and short-sentence share, for the window around each
of the book's peaks, against the chapter that contains it:

| peak | short sentences in the peak window | in the chapter overall |
|---|---:|---:|
| ch07, mother on the phone | **0.0%** | 7.8% |
| ch08, the doctor's office | **0.0%** | 13.5% |
| ch09, the begging on the floor | **0.0%** | 11.3% |
| ch10, the April reunion | **0.0%** | 10.9% |
| ch23, the graduation | **0.0%** | 10.6% |
| ch20, the parking-lot fight | **33.3%** | 24.4% |
| ch31, Ruth's year | 20.8% | 18.3% |

**At five of the book's emotional peaks there is not one sentence under ten
words in the peak window**, while the chapters around them run 8-14% and the
one action peak runs 33%. Per-chapter cadence variation says the same thing:
ch10, the reunion, has the second-lowest CV in the book at 59.5; ch20, the
fight, has the highest at 95.0.

The reviewer's own two examples are both still in the text. The ch09 begging
paragraph is intact:

> She says she'll be good, and that she'll do the dishes every single night for
> the rest of her life. She'll do her dad's jobs as well, all of them, before
> anybody has to ask her. They can take the bike back, because she has no use
> for it and had none for it in July either.

Note that the paragraphs on either side of it have already been fixed and are
doing what the reviewer asks — *"what comes out is please, over and over, in
pieces, in the gaps where she can get any air"* and *"This," she says … "This,
this, all of this."* The summary block is a leftover sitting between two good
beats.

**Fix.** Not the reviewer's rewrite. His version adds *"She's crying now. She
can't stop. She's not even sure when it started"*, which names the state and is
a Rule 1 violation; the text already has the crying in the paragraph above. The
fix is to convert the reported speech into the speech, which the scene has
already earned: *"I'll do the dishes. Every night. Dad's jobs too, all of them,
before you ask."* Then the bike, then Christmas, then the birthday, each as its
own short line, and cut the narrator's *"since a birthday is one more thing she
can do without"* entirely — that clause is the narrator explaining a
seven-year-old's offer to the reader.

Do the same at ch07, ch08, ch10 and ch23. **The target is a number, not a
feeling: bring the short-sentence share inside each peak window up to the
chapter's own baseline.** That is measurable and it stops the fix from becoming
an emotional-adjective pass.

**Work:** five scenes, half a day each. **Severity: HIGH.**

## B2. Negative-space overuse

**Claim:** the book conveys everything through what characters don't do, and it
is exhausting.

**VERDICT: ALREADY FIXED, and arguably overcorrected. This is the cleanest
measured win in the audit.**

`passes/NEGATIVE_SPACE_BRIEF.md` recorded the book at **17.8%** of sentences
carrying the device, against a corpus median of 7.8% and a corpus maximum of
17.5% — above every reference book. The same measure, run over `chapters/`
today:

| | book | corpus low | median | high | percentile |
|---|---:|---:|---:|---:|---:|
| sentences whose beat is a negative | **3.27%** | 2.88% | 7.80% | 17.49% | **9** |

From above every book to the 9th percentile. Supporting rows in `tics.py`:
announced withholding **0.9** per 100k against a target of 3.0 and a corpus
maximum of 1.3 — below every reference book. *"keeps it to herself"* and its
family: **one** instance in the whole book. *"Nobody says anything"*: two.

The reviewer's specific examples are worth answering individually, because the
one that matters is not a defect: Ruth's six-month silence *is* structurally
resolved, in ch31, exactly as the reviewer says it should be ("Then you read
Ruth's chapter and find out why"). He proposed the fix the book already has.

**Recommendation: no further cutting.** At the 9th percentile the next pass
would take the book below the corpus floor. If anything, the ch23-36 chapters
could afford one or two back. **Severity: NONE — do not action.**

## B3. The flat dialogue problem

**Claim:** characters speak in the same cadence, same formality, no personality;
lines could belong to anyone.

**VERDICT: STILL LIVE on formality and subordination. REVIEWER WRONG on
cadence, which is now separated. Fully covered by A4 — see the tables there.**

Two additions the reviewer's frame misses.

`voice_separation.py` shows real separation on the measures the reviewer says
are absent: words per line ranges 5.8 (Sam) to 10.8 (mom), a spread of 58% of
the mean, and the 1-3 word share ranges 13.3% to 41.3%, a spread of 109% of the
mean. The characters are no longer identical in cadence. They are identical in
clause architecture, which is A4.

`absolutes.py` adds a second axis nobody has named:

> dialogue only: this book **18.64** per 1000, at the **100th percentile** of the
> corpus (corpus low 9.40, median 13.10, high 18.40)

while narration sits at the 57th percentile. **Every character in this book
speaks in absolutes at a higher rate than any of twenty-three novels**, and the
narration does not. Nobody hedges: Chloe and Ruth are at 6% hedged lines, Priya
11%, and mom, dad, Kavi and Nadia are at **zero**. That is a second mechanical
cause of "they all sound the same" and it has a cheap fix: give two or three
characters a hedge and let them keep it. Kavi qualifying nothing while Nadia
qualifies everything is a voice difference that costs four words a chapter.

Two of the reviewer's three example lines are still present verbatim ("I know,
Chloe. Fun's one thing…", ch05; "That's not what lying is…", ch05, in Ruth's
mouth not the quoted form).

**Work:** folded into A4, plus a half-day hedge pass. **Severity: HIGHEST, via A4.**

## B4. The "list" problem

**Claim:** the book lists everything; the lists are emotionally flat.

**VERDICT: LARGELY REVIEWER-SELF-ANSWERED. The reviewer's own carve-out covers
his own main example.**

### Measurement

Paragraphs opening on "Then " — the list-continuation shape — 57 book-wide, of
which **37 are in chapters 1 to 6**: ch02 12, ch06 9, ch03 6, ch01 5, ch04 5.
From ch07 onward the shape appears at most twice per chapter and usually once.

Both passages the reviewer quotes are still in the text. But his own note says:

> **Times it's good:** When you are purposely trying to overload the reader…
> The summer camp with a list is useful, to make readers miss how much she did.

That is chapter 6, which is titled *The List*, is the largest cluster in the
book, and is now more dramatised than his quotation suggests — the CPR dummy is
demonstrated on the table edge, the bridge is built out of the salt and pepper,
the fractions are drawn on a napkin, and a father two tables over is sitting
through the same thing. The catalogue tail ("Then the wood shop… Then the
eggs… Then chess…") is the deliberate overload he endorses.

The live residue is **ch02, 12 "Then" paragraphs**, which is a testing chapter
and not a place where overload is doing thematic work.

**Fix.** Leave ch06 alone. In ch02, convert half the "Then" openers to something
else — the subtest itself, the examiner's hand, the room. Three or four
sentences of work.

**Work:** half a day, ch02 only. **Severity: LOW.**

## B5. The "too clean" problem

**Claim:** every sentence is correct, balanced and predictable; the author never
lets the prose get ugly.

**VERDICT: STILL LIVE, but it is not a separate item. It is A2/D12 restated as
an aesthetic complaint.** The measurement is the same: CV at the 4th percentile,
u10 at the 4th, short-runs at the 4th, simple sentences below every book. Both
of the reviewer's example sentences are still in the text (ch01, both). Fix and
work are A2's. **Severity: covered by A2.**

One caution on the prescription. "Write some ugly sentences" and "take risks
with unexpected words" is not what the measurement asks for and would raise the
reading-grade figures the bands are gating. The measured deficit is *short
sentences*, which is a different instruction and a cheaper one.

## B6. The "invisible verbs" problem

**Claim:** the book leans on *is, has, says, does*; action is described in the
most basic way.

**VERDICT: REVIEWER WRONG, and the reviewer half-says so himself.**

| | book | corpus low | median | high |
|---|---:|---:|---:|---:|
| `says`+`said` as a share of all speech tags | **60.7%** | 49.9% | 69.2% | 92.2% |

The book uses a *more* varied set of attribution verbs than the median novel.
The reviewer's own "Careful" note ("it should be <10% used… Sometimes you should
keep the invisible verbs, to keep the user passive. The book is heavily reliant
on controlling readers perspective. Keep that.") is correct and is what the book
already does. **No action. Severity: NONE.**

## B7. The "telling not showing" problem

**Claim:** the book tells the reader how characters feel.

**VERDICT: REVIEWER WRONG. Measurably the least guilty book in the comparison
set.**

Constructions of the form *X is/was/gets/feels/looks + <emotion adjective>*
(angry, sad, pleased, scared, proud, upset, relieved, frustrated, embarrassed
and 20 more):

| | book | corpus low | median | high |
|---|---:|---:|---:|---:|
| emotion-naming per 100k | **9.7** | 12.9 | 30.0 | 88.2 |

**Eleven instances in 113,435 words, below every one of the twenty-three
books.** The commonest are *annoyed* (3), *pleased* (2), *bored* (2).

The reviewer's three examples do not support his claim. *"Then the corner of her
mom's mouth drops and stays down"* is a physical fact, not a stated feeling —
it is the thing he asks for elsewhere. *"He says it without any particular
feeling about it"* is no longer in the text. The third describes duration, not
emotion.

Where the complaint *is* real is the different fault `passes/audit/TALKING_DOWN.md`
already documents at length — triple statement and tell-then-show. **ALREADY
REPORTED ELSEWHERE**, in a 991-line report with a ranked list; do not re-audit
it. **Severity: NONE here.**

## B8. The "same beat" problem

**Claim:** character does something, observes something, has a quiet
realisation, repeating.

**VERDICT: WEAKLY LIVE, and the reviewer's own warning is the right answer.**

The named pattern that is checkable is "Chloe does something impressive,
somebody says you talk weird, she goes quiet." It occurs three times and the
third is a variation:

> "You talk weird," she says, the way you would report the weather, turning back
> before Chloe has worked out whether an answer is expected. *(ch01)*

> "It's fine, I guess, except there's a girl there who says I talk weird, so
> mostly I just keep quiet in class now." *(ch04, Chloe reporting it)*

> "You were weird before, and now you're weirder than that even," Bryce says,
> with interest, the way you would tell somebody the time. *(ch07)*

Three instances is a motif, not a tic — and the third inverts it, because Bryce
says it *with interest* and it is not an exclusion. What is worth noting is that
two of the three carry `the way you would`, which is D5's construction, so the
beat and the simile arrived together.

The reviewer's own warning applies: *"Don't replace every instance, it's only
predictable because it is done so much. Replacing all instances makes the new
method the predictable rhythm."* At three, nothing needs replacing.

**Fix.** One only: strike `the way you would tell somebody the time` from the
ch07 line. It is the weaker of the two and its removal separates the beats.
**Work: one sentence. Severity: LOW.**

## B9. The "overly intellectual" problem

**Claim:** everything is analysed; a six-year-old does not narrate her own
social failure this way.

**VERDICT: STILL LIVE in chapters 1-10, and it has a second, harder proof the
reviewer did not have.**

All three example sentences are still in the text verbatim:

> …working out which part was the wrong part, because it is either the Icarus
> or the saying it a second time louder. *(ch01)*

> Chloe sits with that while he waits, because the real answer has two halves
> and the question was built to hold one. *(ch01)*

> Chloe has a very clear idea of what is supposed to happen to a child who does
> what Ruth just did, so she watches for it the whole rest of the period *(ch04)*

Note that all three carry a `because` or `so` — the same clause the dialogue
carries in A4. The narrator and the six-year-old share one syntax.

### The harder proof

`grade.py`'s band averages, which are the house's own gate:

| band | ages | floor | **average F-K** |
|---|---|---:|---:|
| ch1-10 | 6-8 | 5.5 | **8.49** |
| ch11-15 | 8-12 | 6.0 | **7.63** |
| ch16-22 | 13-19 | 7.0 | **8.03** |
| ch23-36 | adult | 8.0 | 9.18 |

**The chapters where Chloe is six to eight read harder than the chapters where
she is eight to twelve, and harder than the chapters where she is thirteen to
nineteen.** Chapter 5, age six, reads at F-K 9.2 — higher than every chapter in
both middle bands except ch16. Chapter 3, age six, reads at 9.0; chapter 19,
age sixteen, reads at 8.4.

`passes/HOUSE_RULES.md` §5 states the design in as many words: *"raising an
early chapter above a late one works against the design even when both clear
their floors."* The early band clears its floor by three grades and inverts the
design while doing it.

**Fix.** Do not simplify the *content* of the early chapters; the observations
are the character. Take the reading grade out of the *joint*. Every one of the
three examples is one sentence carrying an explicit logical connective that a
child would not supply:

- *"…working out which part was the wrong part, because it is either the Icarus
  or the saying it a second time louder."* → *"She works out which part was
  wrong. The Icarus, or saying it a second time louder."*
- *"Chloe sits with that while he waits, because the real answer has two halves
  and the question was built to hold one."* → *"Chloe sits with that while he
  waits. The answer has two halves and the question only holds one."*

Same content, same perception, one grade lower, and the *because* is gone — so
this pass and A4's are the same pass run over narration instead of dialogue.
Target: band 1-10 average down to about 7.0, still 1.5 above its floor and below
both later bands.

**Work:** chapters 1-10, gated on `grade.py --one <n>`. Four agent-days, and it
should be run by the same agent as A4 because the edits are the same edit.
**Severity: HIGH.**

## B10. Lack of sensory detail

**Claim:** the book is sparse on sensory detail; ten chapters at the school and
we do not know what the school looks or smells like.

**VERDICT: SPLIT. Mostly REVIEWER WRONG on the general claim. STILL LIVE, and
exactly right, on the school.**

| sense word | book /100k | corpus low | median | high | percentile |
|---|---:|---:|---:|---:|---:|
| smell* | 7.1 | 0.0 | 5.7 | 29.6 | **61** |
| sound / noise | 65.3 | 14.5 | 43.7 | 93.7 | **78** |
| taste / flavour | 3.5 | 1.3 | 8.7 | 25.5 | 22 |
| cold / warm / hot / cool | 50.3 | 23.6 | 64.9 | 142.7 | 30 |
| hands | 284.0 | 59.2 | 134.4 | 326.2 | **96** |
| eyes | 45.0 | 23.6 | 116.3 | 200.4 | **4** |
| voice | 36.2 | 7.3 | 63.2 | 174.9 | 17 |

Smell is above the corpus median. Sound is at the 78th percentile. Review C11's
version of this claim ("the text lives in the eyes and the hands") is **half
wrong**: hands are at the 96th percentile, eyes at the 4th. The eyes-down pass
worked, and it worked so well that the book now mentions eyes less than 96% of
the corpus.

The school sub-point is a different matter and it is exactly right:

> **Zero uses of "smell" in chapters 7 and 11 through 19.** All five uses in the
> book are in ch22, ch23, ch26, ch27 and ch31 — the corridor outside Amberg's
> office, the head of school's office, an army tent, Nadia's stairwell, and a
> lab couch at MIT. Not one of them is inside the school during the ten
> chapters set there.

**Fix.** Five sentences, one per chapter, none of them a description paragraph.
The rule that keeps this inside Rule 1: **the smell has to be attached to
something a character is already doing.** Not "the corridor smelled of floor
wax" but the floor wax getting on her hands off the bannister; not "the forge
smelled of coal" but her jumper smelling of it in the dining hall two hours
later, which the ch15 forge scenes are already set up for. Temperature is the
other cheap one and it is at the 30th percentile: Building Three in February,
the stairwell that is colder than the rooms.

**Work:** five to eight sentences across ch11-19. One day. **Severity: MEDIUM,
and the best value-per-word item in this audit.**

## B11. Repetitive sentence structure

Same claim as A2, B5, C1, C14 and D12, with different examples. **VERDICT:
STILL LIVE, covered by A2.** All three example sentences are still in the text
(ch01 ×2, ch01). No separate work item.

## BO1-BO6. "Opportunities"

Restatements of B3 (BO1), B7 (BO2), B3 (BO3), B1 (BO4), B10 (BO5), B11 (BO6).
No separate verdicts. Two of the six carry example rewrites that **violate
HOUSE_RULES Rule 1 and must not be used as models**:

- BO2: *"Her chest tightens. She can't breathe. She presses her forehead against
  the cold wall and squeezes her eyes shut."* The first two sentences name the
  state; only the third is a fact about the room.
- BO5: *"The clock ticks, it's eleven-forty and the hands haven't moved in
  years."* Adds a figure of speech about tedium on top of a scene that has
  already dramatised tedium.

BO1's per-character verbal tics are the same instruction as D1 and A4 and are
better specified there.

## BS1. Scene rewrite: Chloe begging (the reviewer says ch8; it is ch9)

**VERDICT: THE COMPLAINT IS HALF LIVE; THE PROPOSED REWRITE VIOLATES RULE 1.**
Covered in B1 above, with a fix that keeps the summary out and the narrator's
commentary out. Do not use the reviewer's version: *"She's crying now. She can't
stop. She's not even sure when it started"* and *"She's on her knees now. She
doesn't remember getting there"* both narrate the character's unawareness of
her own state to the reader.

## BS2. Scene rewrite: the graduation (ch23)

**VERDICT: REVIEWER WRONG, AND THE FOURTH REVIEWER IN THIS SAME FILE SAYS SO.**

The current text is one paragraph:

> Then it's Kessler, and eleven years compress into thirty feet of plywood and a
> moment of applause. … The head of school hands her the folder with both hands
> and says her name once, correctly, plain. That turns out to be the entire
> weight of ceremony the place hands out.

Review D, in the same file, lists this exact scene under **WHAT'S WORKING**:

> **Restraint at the payoffs.** Sam's overhang, the first arrow collision, the
> graduation — each gets a paragraph and then the next thing starts. That
> discipline is rare and it's why the book doesn't read as triumphalist.

The proposed rewrite ends on *"She made it."* — a sentence that exists only to
make sure the reader knows something, which is Rule 1's exact prohibition — and
adds *"Tears streaming down her face"* on the mother, which is B7's own
complaint. **Do not action.** One small thing is worth doing: `both hands` in
the head-of-school sentence is one of A3's 38 and can come out without touching
anything else. **Severity: NONE, beyond the A3 word.**

---

# REVIEW C — "Prose Issues in the Text"

## C1. Sentence structure monotony
Same as A2. **STILL LIVE**, CV 4th percentile, u10 4th percentile, simple
sentences below every book. Covered by A2.

## C2. The "and then" chain
**REVIEWER WRONG at the current rate.** Sentences with two or more "and":
17.47%, corpus 4.24 / 11.72 / **25.83** — 83rd percentile, inside the range.
"and" as a share of all words: 3.56%, corpus 2.30 / 3.34 / 5.10. The *and*s are
ordinary; the subordination underneath them is not (A2). No separate action.

## C3. The "because" explanation loop
**STILL LIVE and this reviewer named the mechanism correctly before anyone
measured it.** `because` on 10.9% of spoken lines against a corpus maximum of
3.3%, and 16.2% in the chapters where Chloe is six to eight. Full measurement
and fix in A4. **Severity: HIGHEST, via A4.**

## C4. Over-explanation / hand-holding
**ALREADY REPORTED ELSEWHERE.** `passes/audit/TALKING_DOWN.md` is a 991-line
ranked sweep of exactly this, and `passes/audit/FEEDBACK_TALKING_DOWN.md`
re-verifies it and records which items are still unapplied. Do not re-audit.
Worth noting from that report: *"The book-wide tone construction Rule 1 flags as
recurring is effectively gone"* — I re-checked and confirm it. `grep` for
"the tone/voice/look X uses when" returns three hits, none naming a mental state.

## C5. Physical grounding becomes repetitive
Same as A3. **MOSTLY FIXED** on the named gestures, **STILL LIVE** on `both
hands` (33.6/100k against a corpus max of 7.2). This reviewer's diagnostic is
the best one in the file — *"What does the character do with their feet? Their
breathing? Their jaw? What's happening in their stomach?"* — and it is
answerable with numbers: `stomach` appears **once** in 113,435 words,
`breath/breathing` 26 times, `shoulders` 40, against `hands` 322. Covered by A3.

## C7. Dialogue attribution
**PARTLY LIVE, low value.** The reviewer is right that the book prefers action
beats to speech verbs and right that this is good. His second point, that long
multi-speaker exchanges go unattributed, is checkable and mostly does not hold.
In the book's three biggest multi-hander chapters, the share of dialogue
paragraphs carrying a tag or an action beat is **ch20 91%, ch15 78%, ch13 74%**.
The unattributed runs are short and sit inside established two-handers, which is
what `STYLE_GUIDES.md` asks for. `says`+`said` at 60.7% of tags is below the corpus median. The
one real residue is that the action beats themselves repeat (*sets down*, *keeps
her eyes on*, *turns*), which is A3's `both hands` problem in a second costume.
Covered by A3. **Severity: LOW.**

## C8. The "which" clause problem
**STILL LIVE.** Relative clauses on **30.52%** of sentences, corpus 7.76 / 19.55
/ **29.97** — above every book in the corpus. This is one of the two rows in the
whole structure table where the book exceeds the corpus ceiling; the other is
subordination. Same fix as A2: a `which` clause is the cheapest available second
sentence. Covered by A2, and it should be the *first* thing that pass targets,
because breaking a `which` clause both raises CV and lowers relcl in one cut.

## C9. Children speaking too well
**STILL LIVE, and it is the most acute case of A4.** Chapters 1-10, Chloe age
six to eight: **31.2%** of spoken lines carry a subordinator and **16.2%** carry
`because`, against corpus maxima of 16.9% and 3.3%. The six-year-olds are the
most heavily subordinated speakers in the book, and they are more subordinated
than the adults in chapters 23-36 (15.7% and 3.5%).

The reviewer's own worked example is exactly right and is the model for the fix:
*"A seven-year-old says 'That's not— it's not stuck. Stuck is when you can't
move. It CAN move.'"* Content identical, subordination gone, and it is not
baby-talk — it is a bright child's actual syntax.

Do chapters 1-10 first in the A4 pass. **Severity: HIGHEST, via A4.**

## C10. The "same" problem
**AT TARGET, STILL ABOVE THE CORPUS.** `tics.py`: the word `same` at **124.4**
per 100k against a target of 125.0, a corpus median of 49.7 and a corpus maximum
of **87.9** — 42% above the most `same`-heavy book of twenty-three. The phrase
`the same way` specifically is at 6.2/100k against a corpus maximum of 4.4.

This one is a deliberate house decision: the target was set at a reasonable rate
rather than corpus parity, per `passes/TIC_BRIEF.md`, and it has been hit. But
`same` is the one word in the tic list whose repetition a reader consciously
notices, because it is a common word doing an uncommon job. **Recommendation:
lower the target to 90 (corpus max) and take the extra 40 instances.** Most are
deletable — *"the same sentence said louder"* keeps it, *"in the same way that"*
does not need it. **Work: one day. Severity: MEDIUM.**

## C11. Lack of sensory variety
Same as B10, with the eyes/hands claim. **HALF WRONG** — hands 96th percentile,
eyes **4th**. **STILL LIVE** on taste (22nd), temperature (30th), and the school
(zero smells in ten chapters). Covered by B10.

## C13. Emotional beats too evenly spaced
**NOT SUPPORTED AND NOT WORTH MEASURING.** The reviewer offers no examples and
the claim ("every three or four paragraphs there will be a small emotional
moment") is not falsifiable without a definition of an emotional moment that
would itself be an opinion. What is measurable and adjacent is B1: the beats are
not evenly spaced, but the *prose cadence* is, which is the real version of this
complaint and is already an action item. **Severity: NONE — merged into B1.**

## C14. The "She/He [verb]" opening
**REVIEWER WRONG at the current rate.** `tics.py`: sentences opening on
She/He + verb at **122.7** per 100k against a target of 120.0, a corpus median of
74.7 and a corpus maximum of **195.0**. The book is well inside the corpus range
and there are books in the reference set that do it half again as often. It is
2% over its own house target, which is a rounding error. **No action.**

## C15. The text doesn't trust silence
**ALREADY FIXED.** This is B2's measure from the other side: the narrated
absence is at the 9th percentile after the negative-space pass, *"Nobody says
anything"* appears twice book-wide, and announced withholding is at 0.9/100k,
below every reference book. The book now under-narrates silence relative to the
corpus. **No action.**

## C16. The "though" and "except" crutch
**MARGINAL, EFFECTIVELY AT CEILING.** `tics.py`: `though` at clause end
**65.7** per 100k, corpus 29.5 / 70.8 — under the corpus maximum, and monitored
rather than targeted for that reason. `except` as a connector **8.8**, corpus
6.0 / 14.6 — mid-range. An independent regex puts clause-final `though` at 71.7
against a corpus high of 70.8, so the honest reading is *at the ceiling, not
over it*. 81 instances.

**Recommendation: leave it, but stop it climbing.** If the A2 sentence-splitting
pass runs, watch this row: splitting a long sentence often strands a
`, though` at the end of the new short one, and this is the row that will absorb
that. **Severity: LOW, monitor only.**

## C17. Repetition of specific phrases
**MIXED — three of the ten are genuinely above every book, but at small absolute
counts.** All against the 23-book corpus, per 100k:

| phrase | book | corpus high | uses |
|---|---:|---:|---:|
| **both hands** | **33.6** | 7.2 | **38** |
| the way you/she would | 21.2 | 14.5 | 24 |
| the whole of it / the rest of it | 8.8 | 6.4 | 10 |
| the same way | 6.2 | 4.4 | 7 |
| eyes on / eyes down | 7.1 | 14.1 | 8 |
| set it back down | 1.8 | 0.0 | 2 |
| which is the whole / exactly | 3.5 | 0.0 | 4 |
| before she/he could | 0.9 | 15.8 | 1 |

Only `both hands` has both a rate above the corpus and a count large enough to
be felt. `the way you would` is D5 and is at its target. The rest are between
one and ten uses in a 113,000-word novel and are below the threshold at which a
reader notices anything. **Action: `both hands` only, via A3.**

## C18. The text tells you what to feel
**REVIEWER WRONG, measurably.** Eleven emotion-naming constructions in the whole
book, 9.7 per 100k, against a corpus low of 12.9 and a median of 30.0. Below
every one of the twenty-three books. Same finding as B7. The reviewer's own
qualifier — *"It's fine to do occasionally, but it should remain rare"* — is
satisfied several times over. **No action.**

## C19. Scene transitions are too smooth
**LARGELY NOT SUPPORTED.** Of 160 scene openings across the book, **16 (10%)**
open on a time marker of the *"In September / The following week / By March"*
kind the reviewer describes. Ninety percent open on a person, an object or an
action.

The observation underneath it is worth keeping, though, and it is structural
rather than stylistic: **the book has 196 scene breaks in 36 chapters**, an
average of 5.4 per chapter, and every one of them is a typographic rule. The
reviewer's audiobook point survives the measurement — a listener gets a pause
and nothing else, 196 times. That is a real and cheap thing to vary in a handful
of places (end a scene mid-action and open the next inside the same object), but
it is a different job from the one he describes and it is low priority against
everything above. **Severity: LOW.**

## C20. The prose doesn't change with the character's age
**STILL LIVE, AND IT IS WORSE THAN THE REVIEWER SAYS — the prose does change,
and it changes in the wrong direction for the first two bands.** Full
measurement in B9: band 1-10 averages F-K 8.49, band 11-15 averages 7.63, band
16-22 averages 8.03. The six-to-eight-year-old chapters are the second hardest
band in the book. This is a direct conflict with `HOUSE_RULES.md` §5.

The reviewer's prescription — *"shorter, more sensory sentences for the young
child"* — is the right one and it converges with A2, A4, B9 and B10: shorter
sentences, fewer `because` clauses, and the sensory detail that is currently
missing. **One pass over chapters 1-10 discharges four items at once, and it
should be the first thing done after A4's dialogue rules are written.**
**Severity: HIGH.**

---

# REVIEW D — "PROSE NOTES"

## D1. The house sentence
**STILL LIVE. The single most damaging finding in this audit, and this reviewer
diagnosed it correctly by feel before anything measured it.** Full treatment in
A4: 26.9% of spoken lines carry a subordinator against a corpus maximum of
16.9%; `because` on 10.9% against a corpus maximum of 3.3%; 31.2% and 16.2% in
the chapters where Chloe is six.

All four of his example speakers are still speaking that way. Two, re-grepped:

> "That was different, because Maddie kind of scoops it instead of catching it
> properly, so it's basically a whole other move." *(Kayleigh, ch01)*

> "It's not obviously, because you have to actually go and do things," Ruth
> says. "My mom asked, and there's a form, and there's a day where you come
> back and they look at you, and that day sits in the fall, not in the summer."
> *(ch06)*

His fix is the correct fix and is specified in A4. **Severity: HIGHEST.**

## D2. Nobody speaks in fragments
**STILL LIVE, and it is the same measurement from the other end.** Spoken lines
of three words or fewer: **14.2%**, corpus low **11.3%**, median 33.8%, high
45.9% — the second lowest of twenty-four texts. Per speaker, Sam is the
exception at 41.3% and everyone else sits between 13.3% and 28.0%.

Colloquial markers (*gonna, wanna, dunno, gotta, yeah, nah, huh, nope*) appear on
**3.1%** of lines book-wide, and **1.0%** in chapters 23-36. Nobody in the adult
third of this novel says *yeah*.

The one caution: the fragment fix and the reading-grade bands pull against each
other in chapters 16-36, where the floors are 7.0 and 8.0. Fragments cost grade.
The fix is to take the fragments from *dialogue*, where they cost least, and the
short sentences from *narration* subordination, where the grade is actually
sitting. `grade.py`'s spoken/narration gap column is the gate: the median gap is
10.5 words and there is room.

Covered by A4. **Severity: HIGHEST, with A4.**

## D3. The numbers
**ALREADY FIXED. Every number row in `tics.py` passes.**

| number | book /100k | target | corpus max |
|---|---:|---:|---:|
| eleven | **9.6** | 10.3 | 10.3 |
| nine | **30.7** | 31.2 | 31.2 |
| four | **115.7** | 119.3 | 119.3 |
| forty | **26.3** | 30.0 | 30.0 |
| four hundred / hundred | within `grade.py` share table, 3.4% vs corpus max 4.7% |

Every one of the five numbers the reviewer names is now at or below the highest
rate in twenty-three published novels. `grade.py`'s distribution audit says the
same thing from a different angle: the book uses **70 distinct number values**
against a corpus median of 39, and puts **59.2%** of its numbers on its five
commonest values against a corpus *low* of 62.1% — i.e. the book's numbers are
spread more widely than any book in the reference set. The "same three numbers"
complaint is dead.

The secondary claim, hedged exact numbers, is also dead: **5.3** per 100k against
a target of 18.0 and a corpus **median** of 10.9.

**But see A1.** The number *words* were driven down and the number+action
*sentence shape* was not, and that shape is at the 100th percentile. The fix
worked on the thing it measured. **Severity: NONE here; the residue is A1.**

## D4. Announced withholding
**ALREADY FIXED, below the corpus.** `tics.py`: **0.9** per 100k against a target
of 3.0, a corpus median of 0.0 and a corpus **maximum of 1.3**. One instance of
the *"keeps it to herself"* family in the whole book. The reviewer described this
as "on nearly every other page". **No action.**

## D5. "The way you would" similes
**AT TARGET, STILL ABOVE THE CORPUS.** `tics.py`: **17.5** per 100k against a
target of 20.0, corpus median 3.3, corpus maximum **14.4**. Independent count:
24 instances. The reviewer counted "sixty-odd" and asked to keep the best
fifteen; the book is at about twenty-four and the target was set at twenty.

His prioritisation rule is the right one and has not been applied: *keep the ones
that do characterisation work over the ones that do texture work.* Two that
survive and should not both survive, because they are the same beat in two
chapters (see B8):

> "You talk weird," she says, **the way you would report the weather** *(ch01)*
>
> "You were weird before, and now you're weirder than that even," Bryce says,
> with interest, **the way you would tell somebody the time** *(ch07)*

**Fix:** cut the ch07 one. Four more of the twenty-four are texture-only and can
go the same way, which lands the row at ~14, under the corpus maximum. **Work:
one hour. Severity: LOW.**

## D6. "Flat"
**ALREADY FIXED on the word, MOSTLY FIXED on the gesture.** `tics.py`: the word
`flat` at **28.0** per 100k against a target of 35.0 and a corpus **maximum of
39.7** — below every-book territory is not required and the book is inside the
corpus range. `hand(s) flat` at **5.3** against a target of 10.0. `jaw`: 8 uses
book-wide. `corner of her/his mouth`: **zero**.

The reviewer's per-character gesture assignment (*Ruth knocks things over, Kavi
realigns objects, Nadia pushes her sleeves up, Priya reties her hair, Eli drums
two fingers, Theo squares paper*) has visibly been executed — ch34 gives Eli
*"taps two fingers against the wood the whole way through"*, Kavi *"turning a pen
over and setting it back exactly where it was between paragraphs"*, and Theo the
two-handed close. **This one was done.**

Residue: `both hands` (A3) and `turning an object` at 6.1 against a target of
6.0, 2% over. **Severity: covered by A3.**

## D7. The eavesdrop
**REDUCED, STILL CONCENTRATED.** The reviewer counts "north of fourteen". A
grep for every form (stairs, landing, fourth step, through the door / wall /
floor, from the hall, overhear) returns **eight genuine instances of Chloe
overhearing adults, and all eight are in chapters 1 to 8.** After ch08 the
device stops.

> On the other side of the wall Chloe sits on the living room floor with a book
> open in front of her, listening instead of reading. *(ch01)*

> Ms. Vance calls the house on the Friday, which Chloe hears from the stairs
> *(ch08)*

> Chloe comes down that night in her pajamas, because the word program has come
> up through the floor of her room twice already. *(ch08)*

Eight in eight chapters is one a chapter, and it is still the primary delivery
mechanism for the structural facts of Part 1 — which is the reviewer's real
objection, and it survives the lower count.

**Fix, and it is the reviewer's:** convert two of the eight. Chapter 8's
*"which Chloe hears from the stairs"* is the best candidate to become an object
— the Vance call leaves a note, or a form, or a name written on the pad by the
phone that Chloe reads the next morning. One should become a thing she was
*meant* to hear: her mother saying it at the table, once, and not repeating it.
This also removes two of the eight `because`-carrying narration sentences in
A4/B9's territory.

**Work:** two scenes in ch03 and ch08. One day. **Severity: MEDIUM.**

## D8. The scene-ending physical beat
**REVIEWER OVERSTATED BY AN ORDER OF MAGNITUDE.** He says "roughly two hundred
times". Measured over all **196 scene ends** in the book (every typographic
break plus every chapter end):

- last sentence contains a tight object gesture (*sets/puts it down, folds,
  squares, closes it, picks it up, turns a page, puts it in a pocket*): **21
  (11%)**
- last sentence contains any physical action at all, including *walks, stands,
  goes, leaves*: **100 (51%)**

Eleven percent is a motif. Fifty-one percent of scene endings containing a verb
of motion is what prose does. The reviewer counted the *device* and reported the
*category*.

The residue is real but small, and it clusters: ch02 has four of the twenty-one
and ch26 has two adjacent. **Fix: vary three or four of the twenty-one, all in
ch02 and ch26.** **Work: an hour. Severity: LOW.**

## D9. "That's not X, that's Y"
**ALREADY FIXED, at the corpus ceiling.** `tics.py`: **1.8** per 100k against a
target of 2.0 and a corpus **maximum of 1.8**. That row's exact shape (`X's not
A, X's B`) returns **two** hits in the whole book, both verified by hand: ch15
*"That's not an argument, that's an outcome"* and ch16 *"It's not a date, it's a
plate."* The reviewer estimated "perhaps eighty times".

Three of his six quoted examples are gone from the manuscript entirely
(*"That's not lying, that's just being stuck"*, *"That's not a number, that's a
phrase somebody reaches for"*, and the *"same sentence said louder"* form, which
survives only as a variant in ch11). Three remain, and they remain because they
are outside the row's shape rather than inside it: *"It's not one second,
Chloe"* (ch08), *"That's not detention. That's home"* (ch20, split into two
sentences), *"That's not what lying is"* (ch05). Those three are counted in the
broader measure below, not in this row.

See A4 for the broader construction he was reaching for, which is also thin
(26 instances, 23 per 100k) and which is **not** the cause of voice sameness.
**No action.**

## D10. "And that's the whole of it"
**AT TARGET, MARGINALLY ABOVE THE CORPUS.** `tics.py`: `the whole/rest of it`
at **8.8** per 100k against a target of 10.0, corpus median 0.0, corpus maximum
6.4-6.9 depending on the regex. Ten instances book-wide, across ch01, 05 (×2),
09, 11, 14, 15 and 28.

Ten is not "every character uses it". But the reviewer's test is a good one and
one instance visibly fails it — ch10, where Kavi says *"his mom came and that
was the whole of it"* two paragraphs after the scene has established exactly
that. **Fix: cut that one, leave the other nine.** **Work: one sentence.
Severity: LOW.**

## D11. Eyes-down dialogue
**ALREADY FIXED, twice over.** `tics.py`: eyes on / eyes down at **7.0** per
100k against a target of 12.0, a corpus median of 1.9 and a corpus **maximum of
14.7** — half the corpus ceiling. And the word `eyes` itself is at 45.0 per 100k
against a corpus median of 116.3, the **4th percentile of twenty-three books**.

The reviewer's worry was that "very few characters ever look directly at each
other". At the current rate the book mentions eyes less than 96% of the corpus,
which means the fix has run past the problem. **Recommendation: no further
cutting; the row is done. Severity: NONE.**

## D12. Sentences that won't end
**STILL LIVE. Same finding as A2, and this reviewer states the fix most
usefully.** CV 4th percentile, u10 4th percentile, short-runs 4th percentile,
subordination and relative clauses above every book, simple sentences below
every book, 21.04 words per sentence at the 96th percentile.

His prescription — *"every page needs at least one short sentence. Two on
emotional pages."* — is the right target and it is measurable per chapter:
`grade.py`'s `u10` and `sl CV` columns. The "two on emotional pages" half is B1,
where five peak windows currently carry **zero**.

Note which chapters already do it, because they are the model and they are in
the book: ch15 (CV 94.0, u10 50.0), ch20 (95.0, 40.0), ch22 (87.4, 39.0), ch25
(83.6, 40.3). Four chapters out of thirty-six already sit at or above the corpus
median for variation, so this is not a voice the book cannot write. It is a
voice it writes when there is action and not when there is feeling.
**Severity: HIGH, via A2.**

## D13. Mechanical cleanup
**PARTLY FIXED, PARTLY STILL LIVE, and one part is a live in-flight conversion
that must not be touched by a find-and-replace.**

| item | status |
|---|---|
| em dashes | **0 in the book.** Fixed. |
| curly quotes | **0.** Fixed. |
| trailing double-space hard breaks | **0.** Fixed; `check_edits.py` gates it. |
| chapter headers | **Standardised.** All 36 are `## Chapter <Word>: <Title>` followed by an italic date range. Fixed. |
| escaped characters | **5 escaped periods, 1 escaped `\!`.** Still live. |
| scene-break markers | **Three conventions in use.** Still live. |

The five escaped periods, all after a numeral: ch12 *"out of walnut in about
1961\."*, ch13 *"she read number 10\."*, ch13 *"then 65 through 85\."*, ch14
*"and again in 1998\."*, ch16 *"Thursday, room 4\.*"*. The escaped bang: ch08
*"you want me to stay exactly like this\!"*.

Scene-break markers, and this is the part to be careful with:

| marker | chapters | count |
|---|---|---:|
| `\---` | 01-06, plus one stray in 15 | 44 |
| `---` | 07-20 | 45 |
| `________________` | 21-35 | 72 |

The `\---` block is **not** a random artefact. `HOUSE_RULES.md` §2 records that
chapters 1-6 are mid-conversion from the old hard-break paragraph convention, so
that block is the tail of a conversion somebody is still running. **A global
find-and-replace across all three would collide with that work.** The stray
`\---` in ch15 is a genuine defect and can go now.

**Fix.** Six one-character deletions for the escapes, now, no risk. Then pick one
scene-break marker and convert *after* the ch1-6 paragraph conversion is
confirmed finished — and record the choice in `HOUSE_RULES.md` so it stops
drifting, since three conventions in one manuscript means nobody has written it
down. **Work: ten minutes now, one hour later. Severity: LOW, but free.**

---

# THE QUEUE

Hardest-hitting first. The first three items are one pass, run by one agent,
over chapters 1-10 first and then the rest, because the edits are the same edit
seen from three angles.

### 1. The dialogue subordinator — A4 / D1 / D2 / C3 / C9 / B3
The largest measured defect in the manuscript and the actual cause of the
"everyone sounds the same" and "it sounds like AI" notes. 26.9% of spoken lines
carry a *because / so / since / which* against a corpus maximum of 16.9%;
`because` alone is on 10.9% against a corpus maximum of 3.3%; the six-year-olds
are the worst offenders in the book at 31.2% and 16.2%.

Gate: book-wide subordinated lines to 15% or under, ch01-10 `because` to 5% or
under. Write the per-character rules first (Ruth states and does not justify;
Kavi answers before he explains; Sam keeps what he has; Chloe keeps the
*because* and thereby owns it) and add a `dialogue subordination` row to
`tics.py` so it cannot drift back.
**10-14 agent-days. Nothing else in this queue moves the reader as much.**

### 2. Cadence: short sentences and the `which` clause — A2 / B5 / B11 / C1 / C8 / D12
CV at the 4th percentile, sentences under ten words at the 4th, short runs at
the 4th, relative clauses above every book, simple sentences below every book.
Break `which` clauses first: one cut raises CV and lowers relcl together. Gate
on `grade.py`'s `sl CV` toward 85 and `u10` toward 35. Four chapters already do
this (15, 20, 22, 25) and are the in-house model.
**6-8 agent-days.**

### 3. Chapters 1-10, the age inversion — B9 / C20 / B10-school
Band 1-10 averages F-K **8.49** against band 11-15's **7.63** and band 16-22's
**8.03**. The six-year-old chapters are the second hardest band in the book, in
direct conflict with `HOUSE_RULES.md` §5. Items 1 and 2 run over these chapters
first and will do most of it; finish with the sensory sentences B10 asks for.
Gate: band 1-10 to about 7.0, still 1.5 above floor and below both later bands.
**4 agent-days, largely overlapping items 1 and 2.**

### 4. The number + physical action composite — A1
5.07% of sentences against a corpus maximum of 1.91%; the tight form is 5.6x the
highest book. Untracked by any instrument, which is why it survived the number
pass. Add the row to `tics.py` at a 1.9% target, then delete 120-odd counts that
are not doing work.
**2 agent-days, and the instrument row is the half that matters.**

### 5. Chapter 36 — A5
The last chapter of the novel delivers its climax as 40.6% chat transcript. Frame
it on Priya typing in the room over the feed merchant's: existing chat lines
unchanged, what her hands are doing between them added. No narration of the
fight, no commentary.
**2 agent-days. It is the ending, which is why it is above cheaper items.**

### 6. The emotional peaks — B1
Five peak windows (ch07, 08, 09, 10, 23) contain **zero** sentences under ten
words while their own chapters run 8-14% and the ch20 fight runs 33%. Convert
reported speech to speech; cut the narrator's summarising clauses. Gate on the
peak window matching its chapter's baseline. Do **not** use the reviewer's
rewrites — both violate Rule 1.
**2-3 agent-days.**

### 7. `both hands`, and the gesture row that replaced the old one — A3 / C17
33.6 per 100k against a corpus maximum of 7.2, 38 uses, spread across every
character. Add to `tics.py` at a target of 12. The gestures the reviewers named
are all fixed; this is the one that grew while nobody was counting.
**Half a day.**

### 8. School sensory detail — B10
Zero uses of "smell" in chapters 7 and 11-19, the ten chapters set at Halstead.
Five to eight sentences, each attached to something a character is already
doing. Best value per word in the audit.
**1 day.**

### 9. Two eavesdrops — D7
Eight instances, all in ch01-08. Convert one to an object and one to something
she was meant to hear.
**1 day.**

### 10. The word `same` — C10
124.4 per 100k against a corpus maximum of 87.9. At its house target, but it is
the one repeated word a reader consciously notices. Lower the target to 90.
**1 day.**

### 11. Free mechanical fixes — D13
Six escaped characters and one stray `\---` in ch15. Do not touch the ch01-06
scene-break block until the paragraph conversion in `HOUSE_RULES.md` §2 is
confirmed finished, then standardise all three markers and write the choice down.
**10 minutes now.**

### 12. Small cuts, one sentence each — D5 / D10 / B8 / D8
The ch07 *"the way you would tell somebody the time"*; Kavi's *"and that was the
whole of it"* in ch10; three or four scene-end object gestures in ch02 and ch26.
**1 hour total.**

---

## Do not action

| item | why |
|---|---|
| **B2 / C15** negative space | 3.27% against a corpus median of 7.80%, 9th percentile. Already overcorrected. |
| **B6** invisible verbs | `says`/`said` at 60.7% of tags, *below* the corpus median. Reviewer's own caveat agrees. |
| **B7 / C18** telling not showing | 9.7 emotion-namings per 100k, **below every book in the corpus**. |
| **BS2** the graduation rewrite | Review D, in the same file, lists this scene under "what's working". The proposed ending, *"She made it."*, is a Rule 1 violation. |
| **C2** the "and then" chain | 17.47% two-or-more-"and" sentences, 83rd percentile, inside the corpus range. |
| **C14** "She/He + verb" openings | 122.7 against a corpus maximum of 195.0. |
| **D3** the numbers | Every number row at or under its corpus maximum; 70 distinct values against a corpus median of 39. |
| **D4** announced withholding | 0.9 against a corpus maximum of 1.3. Below every book. |
| **D9** "that's not X, that's Y" | 1.8, at the corpus ceiling. About two instances remain of a claimed eighty. |
| **D11** eyes-down | 7.0 against a target of 12.0, and `eyes` at the 4th percentile of the corpus. |
| **A2** comma splices | 1.80%, 39th percentile. Below the median novel. |
| **C13** evenly spaced beats | No examples given, not falsifiable as stated; the real version is B1. |
| **C4** over-explanation | `passes/audit/TALKING_DOWN.md` and `FEEDBACK_TALKING_DOWN.md`. Already reported, ranked, and partly applied. |

## A note on the proposed fixes

Every fix above was written against `passes/HOUSE_RULES.md` Rule 1. None of them
is a paragraph explaining something to the reader, and three of the reviewers'
own suggested rewrites are rejected on that ground and named where they appear
(BO2, BS1, BS2). Where a fix adds words at all — chapter 36's frame, the school
sensory sentences — the words are what a person in the room is doing, never what
a moment means.
