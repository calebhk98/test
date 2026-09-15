# The prescriptions, one by one

`passes/audit/ISSUES_AUDIT.md` audited the reviewers' **diagnoses**. This file
audits their **prescriptions**: every place a reviewer named a specific passage,
wrote a replacement, or asked for a specific addition. Each entry says where it
comes from, what it actually asks for, whether it has been done, and, if not,
what doing it costs.

Read-only pass. Nothing in `chapters/` or `characters/` was edited. Four agents
are editing concurrently, so every quotation below was re-grepped at the time of
writing; **quote, not line number, is the citation.** Re-grep before acting.

## Sources

| file | prescriptions found | note |
|---|---|---|
| `passes/review/Issues.md` | 52 | four concatenated reviews, A/B/C/D as in `ISSUES_AUDIT.md` |
| `passes/review/Feedback.md` | 24 | two reviews, one with the author's own annotations interleaved |
| `passes/review/IQ_Test.md` | 14 | three reviews of the chapter 2 test scene, the later two correcting the first |
| `passes/review/Some_Spark_notes.md` | **0** | four study guides. Pure summary. Contains no criticism and no prescription. Nothing to action. |
| `passes/review/Dossiers.md` | **0** | three collaborator briefings on what a Halstead graduate is. Prescribes how to *write a new character* in this world, not how to change this manuscript. Its one "quick calibration test" is a warning about three sentences that do not appear in the book. Nothing to action. |

## Headline

**Most of the sentence-level prescriptions were executed. Most of the
scene-level and structural ones were not.**

The tic work is real and it is measurable: `tics.py` now passes 25 of 27 rows,
`hand(s) flat` is down to 6.8 per 100k from a reviewer-reported epidemic,
announced withholding is at 0.8, the scene-ending physical beat is down to 11
scene-ends out of 196, `eyes on / eyes down` is at 8 instances book-wide. Every
one of `Feedback.md`'s eight numbered inconsistencies is fixed. The whole of
`IQ_Test.md`'s instrument critique is fixed, and fixed well.

What nobody executed is the part that needs prose written rather than prose
deleted:

1. **The school has a floor plan and no surfaces.** Eighteen chapters, roughly
   62,000 words, set inside Halstead. Four sensory facts about the building
   exist in all of them.
2. **Scene transitions.** 74 of 161 scene openings put a date or a time
   expression in the first clause. Zero use the transition as a tool.
3. **The reading grade is inverted against the book's own design.** Chapters
   1-10 average grade 8.11; chapters 11-15 average 7.68; chapters 16-22 average
   7.90. The youngest band is the hardest-reading band in the book.
4. **Nobody speaks in fragments.** Sixteen disfluencies in 117,000 words.
5. **Five chapters still run long, unbroken and short-sentence-free** (3, 6, 7,
   11, 16; chapter 11 contains zero sentences of six words or fewer).

Verdict counts are at the end, followed by the queue.

---

# PART 1 — THE FIVE CALIBRATION CASES

These are the five the brief named. Everything else follows in source order.

---

## P1. The Chloe Begging rewrite

**Source.** `Issues.md`, review B, "SECTION 4: SPECIFIC SCENES THAT COULD BE
IMPROVED — Scene: Chloe Begging to Go to Halstead (Chapter 8)". Quotes the old
summarised paragraph, supplies a full replacement scene.

**Asks for.** Break the summary paragraph into live, broken speech; put her
physically on the floor; let the pleading repeat and fail to complete.

**VERDICT: DONE.** The scene now lives in chapter 9, not 8.

Current text, `chapters/09_february.md`:

> The crying is still ahead of her, and she is sitting in the gap with a
> fistful of carpet in either hand.
>
> "Chloe, honey, what are you doing down there on the floor?"
>
> Then it comes out of her all at once and she can't get one word of it out
> whole, so what comes out is please, over and over, in pieces, in the gaps
> where she can get any air.
>
> "Please. I'll be good, I'll be so good, please."
>
> [...]
>
> "I'll do the dishes. Every night. Every single. Every night for the rest of
> my life, please."
>
> [...]
>
> "Take my birthday." Her face is wet all the way to her chin. "Take the whole
> birthday, the cake, the candles, take all of it, please."

**Does ours answer what the reviewer was asking for?** Yes, and it is better
than theirs, which is the correct outcome. The reviewer's replacement names
states three times: *She's crying now. She can't stop.* / *She's choking on
them.* / *She's on her knees now.* Rule 1 forbids all three. Our version gives
the same information as facts about the room and the body: *the crying is still
ahead of her* (position in time, not a state), *a fistful of carpet in either
hand*, *she can't get one word of it out whole*, *her face is wet all the way to
her chin*. The mother's "Baby, breathe for me" does the work the reviewer's
*She's choking on them* was doing, and does it from inside the scene.

The reviewer's structure was followed exactly: broken clauses, abandoned
sentences (*"You can take the bike back. I don't. I never even."*), the please
repeated until it stops being a word, the escalation from dishes to birthday,
the closing collapse. Their sentences were not followed. That is the right
reading of the note.

**One defect introduced.** Later in the same chapter, when the parents say yes:

> Chloe is on her feet before he has got to the end of it.
> [...]
> "Say it again," Chloe says, still standing, "say all of it again."
> [...]
> She screams, at a volume that surprises everybody in the room, and then she
> is **up off the floor** and onto her dad

She is standing. She has been standing for three exchanges. "Up off the floor"
is a fossil from the pre-rewrite blocking. **One-word fix, chapter 9.**

---

## P2. The Graduation rewrite

**Source.** `Issues.md`, review B, "Scene: The Graduation (Chapter 23)". Quotes
the paragraph, supplies a nine-paragraph replacement.

**Asks for.** Expand the graduation crossing; put the mother's tears on the
page; end on *She made it.*

**VERDICT: SHOULD NOT BE DONE.** Three independent reasons.

Current text, `chapters/23_the_first_one.md`:

> Then it's Kessler, and eleven years compress into thirty feet of plywood and
> a moment of applause. Chloe crosses a stage that existed for the first time a
> month ago, built by people she's spent a decade arguing with about hot dogs
> and the size of the moon. It holds dead steady under her the whole way
> across. The head of school hands her the folder with both hands and says her
> name once, correctly, plain. That turns out to be the entire weight of
> ceremony the place hands out. On the walk back to her seat she finds her
> mother's face before she finds anyone else's, the reflex that used to send
> her to the fridge twice in a night to check a magnet was still holding a note
> in place.
>
> Her mother cries from the K's onward, a tissue out early, and her father
> keeps a hand on the back of her chair the whole time.

1. **The proposed version breaks Rule 1 four times.** *"The name lands like a
   punch"* is the narrator interpreting. *"Tears streaming down her face"* is
   handled better in our next line, off-camera and dated to the K's. *"She wants
   to laugh. She wants to cry. She does neither."* names two states and then
   announces the restraint instead of performing it. *"She made it."* is the
   narrator telling the reader what the chapter meant.
2. **A reviewer inside the same file rules against it.** `Issues.md`, review D,
   "WHAT'S WORKING": *"Restraint at the payoffs. Sam's overhang, the first arrow
   collision, the graduation — each gets a paragraph and then the next thing
   starts. That discipline is rare and it's why the book doesn't read as
   triumphalist."* Review B wants exactly the thing review D identifies as the
   reason the book works. When two reviewers split, the one whose note survives
   contact with Rule 1 wins.
3. **The diagnosis underneath it was already actioned anyway.** The reviewer's
   real complaint is that we never see the mother. We now do, twice, in the
   sentence about finding her mother's face and in the tissue out early, plus
   the whole second half of the chapter is Meg's POV on the grass. The
   prescription is redundant as well as wrong.

**What the scene actually needs, if anything.** Nothing. Leave it.

---

## P3a. Sensory rewrite: the clock and the pencil shavings

**Source.** `Issues.md`, review B, "Opportunity 5 — Add More Sensory Details".

> Instead of: "The classroom clock holds at eleven-forty."
> Try: "The clock ticks, it's eleven-forty and the hands haven't moved in
> years. The room smells like pencil shavings and floor wax. Chloe can hear the
> radiator breathing."

**Asks for.** Smell and sound in the chapter 1 classroom.

**VERDICT: NOT DONE.** The number was removed by the numbers pass; nothing was
added. Current text, `chapters/01_before.md`:

> Because the pattern is already found, she writes the answer and then sits
> with the pencil motionless, since what is left is doing it over and over
> while the classroom clock holds where it is.

Chapter 1 contains two instances of any smell word in 3,641 words. The
first-grade classroom has a clock, a window, a parking lot, a board with
yesterday's spelling list half erased, and nothing else.

**In this book's register.** *"The hands haven't moved in years"* and *"the
radiator breathing"* are both the narrator performing; the first is a figure of
speech a six-year-old would not produce and the second is a metaphor this book
does not use. What survives the filter is the smell and the temperature, given
flat, as facts about the room and not as mood: pencil shavings, floor wax,
whatever the radiator actually does. Chapter 2 already shows how this book does
it, and does it well: *"somewhere in the building there is a clock she can't see
but can hear, once she has started listening for it."* That is the model.

**Cost.** Chapter 1, the subtraction-worksheet scene. **Addition, 15-25 words**,
one sentence, placed in the paragraph that already stalls her at the desk.

---

## P3b. Sensory rewrite: the living-room floor and the carpet

**Source.** `Issues.md`, review B, "Opportunity 6 — Vary the Rhythm".

> Instead of: "She sits on the living room floor with a book open in front of
> her, listening instead of reading."
> Try: "The book is open. The words are there. She can't see them. Her mother's
> voice is coming through the wall, and Chloe is on the floor, and the carpet is
> rough under her knees, and she's trying to hear every word."

**Asks for.** Two things at once, and it is worth separating them: a **rhythm**
change (four short sentences before one long one) and a **tactile** detail (the
carpet).

**VERDICT: NOT DONE.** Current text, `chapters/01_before.md`, unchanged:

> On the other side of the wall Chloe sits on the living room floor with a book
> open in front of her, listening instead of reading.

**In this book's register.** This is the rare reviewer rewrite that is almost
compliant. It names no state. *"She's trying to hear every word"* is the only
soft spot and is easily dropped, since the paragraph after it is the phone call
she is hearing. The rhythm move is exactly what review D's item 12 asks for
book-wide, and chapter 1 is the right place to start, because it is the opening
page and because the band-1 reading grade is currently the highest in the book
(8.11 against 7.68 for chapters 11-15). Four short sentences here buy the
chapter something the whole band needs.

**Cost.** Chapter 1, third paragraph. **Rewrite in place, 35 words for 22**, net
+13. Do P3a and P3b in the same edit.

---

## P4. "10+ chapters of them at the school, and we have no idea what the school looks like"

**Source.** `Issues.md`, review B, ISSUE 10, final bullet:

> **10 chapters** You have 10+ chapters of them at the school, and we have no
> idea what the school looks like. Add in descriptions through all the
> chapters, in different rooms, floors, different senses. Don't flood the
> details in the 1st chapter. The 1st chapters should have the most when Chloe
> arrives, but don't overwhelm the reader.

Also `Issues.md` review C item 11 ("Lack of Sensory Variety"), and review B
ISSUE 10's three opening questions: *What does Halstead smell like? What does it
sound like? What does it feel like to walk down the hall?*

**Asks for.** Physical description of the school, spread across every Halstead
chapter, rotating rooms, floors and senses, weighted toward Chloe's arrival,
without dumping it in chapter one.

**VERDICT: NOT DONE. This is the largest unactioned item in the entire review
set, and the gap is bigger than the reviewer thought.**

### What actually exists

Halstead appears in eighteen chapters (4-6, 10-23), about 62,000 words. The
building has a **floor plan** and no **surfaces**.

The floor plan is genuinely good and should not be touched. Rooms named after
planets. The nurse on the first floor beside the stairwell with the red door.
Fruit in bowls by the stairs. The corkboard on the second floor by the stairs.
The robot arm on the second floor. The first-floor alcove phone with a chair
beside it. The library across the whole back of the ground floor, two levels,
a staircase inside it. Building Three with the long field running north from the
back of it. And, best of all, chapter 14's Watch, where the geography becomes
tactical:

> the students know which third floor door hangs loose in its frame, which
> second floor cupboard has a window in the back of it, where the bannister has
> a gap you can get an arm through, and which kitchen door makes a noise when it
> opens.

That is a building the students know. It is not a building the reader can see.

Here is the complete inventory of sensory description of Halstead in all
eighteen chapters:

| chapter | the entire physical description |
|---|---|
| 4 | *"the sound that many people make in a hallway with hard floors is enormous"* |
| 6 | *"the lights in that hall go off in sections late on, so that they are down to the last section, in a strip of light about the width of a doorway"* |
| 10 | *"the third-floor radiator makes a noise in the middle of the night you stop hearing after a week"*; *"corridor light in a bar along the floor"* |
| 19 | *"with the windows open because the room retains heat"* |
| 22 | *"The corridor smells like the coffee cart set up near the stairwell every April, and the runner's shoes squeak on the steps of tile outside the door"* |

Six sentences. That is all of it.

There is **no exterior**. The family drives four hours to it twice in chapters 3
and 9 and the building is never described from outside; the closest the book
gets is chapter 8, from a parked car in a different state: *"looking out the
windshield at the wall of the building."* We do not know whether Halstead is old
or new, brick or concrete or glass, one building or a campus (chapter 22 says
"those two buildings", chapter 14 says "Building Three", and these are never
reconciled visually). We do not know how many storeys it has; the text uses
first, second and third floor and never a fourth, which is an inference the
reader has to make.

There is **one smell in the whole school** and it arrives in chapter 22, the
seventeenth Halstead chapter, four pages before she leaves. Across the whole
book, smell words appear in 8 of 36 chapters and total 8 uses in 117,000 words.

Chapter 4 is the arrival chapter the reviewer specifically wanted weighted, and
it is one of the thinnest: the reader gets a registration table with letters
taped along the front, folding chairs, a room with two beds and a window that
opens a few inches. The noise line is the only sense engaged, and it is engaged
once, in the sixth sentence, and then dropped for the rest of the chapter.

### What doing it would involve

An addition, not a rewrite; nothing needs cutting. Word budget is not a
constraint: the book average is 3,284 against a ceiling of 3,600, so there is
roughly 11,000 words of headroom and this needs under 800.

Weighted as the reviewer asked, heaviest at arrival, one sense per location,
never two in the same paragraph:

| chapter | where | what | words |
|---|---|---|---|
| 4 | the walk from the lot to the doors; the first corridor; Pluto at night | exterior seen once and plainly, from a seven-year-old's height; what the corridor is made of; what the room smells of that her own house does not | 140 |
| 5 | the pool, the maths room | chlorine and echo; the second-week classroom she is failing in | 50 |
| 6 | the hall outside Pluto | extend the light-in-sections image that is already there and already good | 30 |
| 10 | her real arrival, April, age 8 | the building in April against the building in July; the library at two in the morning; the alcove phone | 120 |
| 11 | the gym and the new climbing wall | 40 |
| 12 | Mrs. Sun's room, the chemistry lab | the lab after Vasquez sets something on fire | 50 |
| 13 | the self-defence mats | the smell of a room used every day by ninety children | 40 |
| 14 | the long field, Building Three | it is described as a direction, never as a thing | 40 |
| 15 | the forge | the one place with an obvious sensory signature and it is not used | 50 |
| 16-18 | the twelves' classroom, the range | cold, noise discipline, what a range smells like after | 90 |
| 19 | the second-floor examination room | already has heat; add one more | 25 |
| 21-22 | the sports building, Amberg's corridor | already has the coffee cart; add the wall she has walked past for eleven years | 35 |
| 23 | the last look at it | the exterior again, closing the bracket opened in chapter 4 | 40 |

**Total: an addition of roughly 750 words across fourteen chapters.** Largest
single item in the queue and the one with the highest ratio of reader-visible
gain to risk, because none of it touches an existing sentence.

---

## P5. The eavesdrop, re-counted across all 36 chapters

**Source.** `Issues.md`, review D, item 7 ("THE EAVESDROP"): *"the most-repeated
device in the book: Chloe overhears adults... I count somewhere north of
fourteen instances."* Fix proposed: *"convert a third of them. Some facts she
should be told directly. Some she should misread. Some she should find as an
object... One or two should be things she was meant to hear."*

**VERDICT: PARTLY DONE, and the earlier audit's count was right but its
conclusion was wrong.**

Full re-count across all 36 chapters. Chloe overhearing adults who are not
addressing her:

| # | chapter | the instance |
|---|---|---|
| 1 | 1 | *"On the other side of the wall Chloe sits on the living room floor with a book open in front of her, listening instead of reading."* |
| 2 | 1 | *"On the way home Chloe has her head against the cold part of the window with her eyes shut and her breathing kept deliberately even, so that the conversation in the front seat goes on over the top of her."* |
| 3 | 2 | *"Only pieces reach her, her mom's voice saying the teacher says, then Ben's voice running on... until one comes through clean, because he has turned toward the door."* |
| 4 | 3 | *"Chloe coming down from the top of the stairs to listen while her mom gives the name"* |
| 5 | 3 | *"comes out a second time in her socks, skipping the fourth stair, which is the stair that gives her away"* |
| 6 | 6 | *"An hour into the drive, with her head against the cold part of the window and her eyes shut... In the back seat, under the tire noise, Chloe keeps her eyes shut and her breathing slow and even, on purpose."* |
| 7 | 7 | *"Coming down for water, Chloe gets the end of a call, and the sentence she arrives on has two pleases in it."* |
| 8 | 8 | *"Ms. Vance calls the house on the Friday, which Chloe hears from the stairs"* |
| 9 | 8 | *"Chloe comes down that night in her pajamas, because the word program has come up through the floor of her room twice already."* |
| 10 | 8 | *"From the stairs on a Sunday she hears her mom saying she thinks the Thursdays are helping"* |
| 11 | 9 | *"their voices come up through the part of the floor that's thin"* |
| 12 | 9 | *"Chloe is out on the landing with a drawer open in front of her when her dad says something downstairs, and she catches only the end of it"* |

Twelve. Plus one displaced onto another child in chapter 6, Ruth: *"I heard half
of it through the door, which is half more than you heard, before Mom noticed I
was there."*

**Chapters 10 through 36 contain none.** The device stops dead at the point
Chloe stops living at home, which is the correct place for it to stop and is
almost certainly not an accident.

**Ruling.** The earlier audit said "eight, all in chapters 1-8, reduced." The
count is twelve, in chapters 1-9. Twelve instances inside 29,000 words is one
every 2,400 words, and in chapters 8 and 9 alone there are five in 5,600 words.
That is still the primary structural-information delivery mechanism of the first
act, and review D's objection stands: *"it also makes the parents feel like an
information delivery system rather than people."*

But the fix is smaller than the count suggests, because the reviewer's own
proposed conversions have mostly happened elsewhere. She *is* told directly, at
length, in chapter 9 ("They tell her on the fourteenth of March", her dad
working out beforehand what order he wants it in). She *does* find things as
objects: the yellow sticky note on the fridge, the letter addressed to *Miss
Chloe Kessler*, the map her mom writes on the back of, the RECORD FORM read
upside down before his forearm covers it. Those are the reviewer's prescription,
already in the book.

**What doing it would involve.** Convert two, not four. The two weakest are
adjacent and do the same job:

- Chapter 8, *"the word program has come up through the floor of her room twice
  already"* — she comes downstairs and joins the conversation anyway, so the
  overhear is a runway and not a scene. Cut the overhear, open on her already in
  the doorway.
- Chapter 8, *"From the stairs on a Sunday she hears her mom saying she thinks
  the Thursdays are helping"* — this is pure information transfer and the
  content (that the Thursdays are helping, that the fighting has stopped) is
  something Meg would say to Chloe's face. Convert to a direct exchange, or to
  Chloe finding the Thursday appointment card.

Also worth doing: one of the two identical car scenes should go or change. Both
have the same blocking (*"head against the cold part of the window"*, eyes shut,
breathing kept deliberately even), thirty pages apart, chapters 1 and 6. The
chapter 6 one is better written and load-bearing. **Chapter 1's should be
re-blocked: 25 words, rewrite in place.**

**Total: two conversions (~150 words of rewrite) plus one re-blocking (~25
words).** Not the biggest item, but the cheapest structural win in the set.

---

## P6. "Heels swinging / feet off floor" at four ages

**Source.** `Issues.md`, review A, item 3, table row 4: *"Chloe's feet dangling
at 6; Chloe's feet dangling at the doctor; Chloe's feet dangling at Halstead;
Chloe's feet dangling at graduation."*

**VERDICT: DONE as specified, but a new density problem has replaced the old
spread problem.**

The complaint was that the gesture recurred at four *ages* across eleven years.
The graduation instance is gone; chapter 23 has no dangling feet. What remains:

| chapter | age | text |
|---|---|---|
| 1 | 6 | *"The chair is too big for her at the grown-up table, so her heels swing free while she eats her potatoes"* |
| 2 | 6 | *"She hooks her heels on the rung of the chair, then comes up onto her knees on it to reach the middle of the table"* |
| 2 | 6 | *"Chloe waits in the corridor on a chair too tall for her feet"* / *"Chloe shifts on the chair, her feet nowhere near the floor."* |
| 3 | 6 | *"her feet swinging free under the chair while he talks"* |
| 4 | 7 | *"Chloe's feet hang well above the floor, and she kicks the chair leg in front of her a few times"* |

Five instances in the first four chapters, all inside one age. The spread
complaint is answered — a six-year-old at adult furniture genuinely does this,
and it is age-locked now rather than a tic applied to a seventeen-year-old. But
five in 14,000 words is once every 2,800 words of the opening, and two of them
are in chapter 2 within twenty paragraphs of each other.

**What doing it would involve.** Cut two. The chapter 2 pair should become one:
*"a chair too tall for her feet"* is the better of the two and *"her feet
nowhere near the floor"* forty lines later is the redundant one. And chapter 3's
*"feet swinging free under the chair"* is doing nothing chapter 1's *"heels swing
free"* has not already done. **Two cuts, about 15 words total.** Five minutes.

---

# PART 2 — `Issues.md`, REVIEW BY REVIEW

## Review A (items 1-6 and the closing summary)

### A1. The number + physical action formula
**Asks for:** stop building sentences on `[small physical action] + [exact
count] + [before/while/instead of]`.
**VERDICT: PARTLY DONE.** A narrow measure (an explicit count of
seconds/minutes/inches/steps hinged on before/while/instead of) finds 37
instances in 4,058 sentences, 0.91%. `ISSUES_AUDIT.md`'s broader composite
measure puts it at 5.1% against a corpus maximum of 1.9%. Both are true; the
difference is definitional. Chapters 21 (5) and 35 (4) are the densest.
**Cost:** 37 targeted cuts, one clause each, spread across 24 chapters. Roughly
two hours. Low priority: it is no longer visible at the paragraph level.

### A2. Comma-splice / polysyndeton monotony
**VERDICT: PARTLY DONE.** See D12 below, which is the actionable form of it.

### A3. The four repeated gestures
- **hands flat:** DONE. 8 occurrences book-wide, 6.8 per 100k against a target
  of 10 and a corpus max of 1.8. Note chapter 20 carries 4 of the 8, two of them
  in adjacent paragraphs on the loading dock (*"crouched at the lip with their
  hands flat on the edge"*, then *"working down each ribcage with both hands
  flat"*). **One cut, chapter 20.**
- **turning an object:** DONE at 5.9 per 100k, but **the quarter-turn is shared
  between two characters.** Review D's rule was one gesture per character. Ruth
  owns it in chapter 20 (*"Ruth turns the cup again, a quarter turn at a time,
  always clockwise"*, plus one more in the same scene). Chloe does it in
  chapter 19 (*"Chloe turns the glass a quarter turn on the wood"*) and chapter
  30 (*"She turns the coffee mug a quarter turn on the table"*). **PARTLY DONE.
  Two cuts or substitutions, chapters 19 and 30.**
- **ears hot / jaw:** DONE. 3 and 8 occurrences.
- **heels swinging:** see P6.

### A4. The "X is a different category from Y" dialogue construction
**VERDICT: DONE.** `that's not X, that's Y` is down to 1 occurrence book-wide
(1.7 per 100k, corpus max 1.8). The wider category construction (*a different
thing/object/question/category*) is at 13.

### A5. Summary dumping instead of dramatisation, three named scenes
- **The 4am federal breach (ch 15): DONE.** Fully dramatised in real time,
  including Chloe's own approach: *"Chloe walks around the corner at a normal
  speed with her hands empty and her arms down."*
- **The Waffle House mugging (ch 20): DONE.** Twenty-two seconds of fight,
  blow by blow, from a loading dock, followed by the casualty check. Nothing is
  summarised.
- **Priya's 75-man ambush (ch 36): NOT DONE, and should not be.** Still
  delivered as chat log after the fact — but it is now framed by real-time prose
  on both sides (the room over the feed merchant's, the timing of the van at the
  bend, the two prisoners and the onion on the edge of the plate). The
  reviewer's objection was *"doing it every single time"*; with two of three
  converted, the third is the closing chapter's chosen form and works. Leave it.

### A6. The clock/time obsession
**VERDICT: PARTLY DONE.** Time words (second/minute/hour) run at 6.0 per 1,000
words book-wide. Outliers: chapter 35 at 11.8 and chapter 13 at 11.3, both
thematically earned (*Nine Minutes*, *Ten Pages*). Chapters 10-21 sit at 6-8 per
1,000, which is where the residue is. Hedged exact numbers (*about four
seconds*) are down to 5.1 per 100k against a target of 18. **Low priority.**

### A-summary item 2: give characters unique somatic habits
**VERDICT: PARTLY DONE.** Assignments exist and are visible: Kavi turns a pen or
a cable, Ruth the cup, Eli taps two fingers, Theo closes a laptop with both
hands. `both hands` remains at 38 occurrences book-wide, once per 3,100 words,
and it is the last shared gesture. **Cost: 15 cuts.**

---

## Review B (ISSUE 1-11, Opportunity 1-6, two scene rewrites)

### B1. The Understatement Trap — the scream
**Source:** ISSUE 1, third example, repeated as Opportunity 4.

> Instead of: "She screams, at a volume that surprises all three of them."
> Try: "She screams. The sound rips out of her. She can't stop it. She doesn't
> want to. She's on her feet, and then she's on her dad, and she's sobbing into
> his shoulder, and she can't get the words out fast enough."

And, in the same item, in what reads as the author's own hand: *"Use the actual
scene, don't add summaries when it gets emotional, say 'She screams "AHHHH", so
loud that her parents wince, and she is jumping onto her dad...'"*

**VERDICT: NOT DONE.** Current text, `chapters/09_february.md`:

> She screams, at a volume that surprises everybody in the room, and then she is
> up off the floor and onto her dad, who catches her most of the way, and she is
> saying thank you into his shoulder with no gap between the words.

The only change from what the reviewer quoted is *all three of them* →
*everybody in the room*.

**Ruling.** The reviewer's rewrite fails Rule 1 twice (*She can't stop it. She
doesn't want to.*) and the "AHHHH" is not a register this book has anywhere. But
the diagnosis is correct and is the same one the begging scene two pages earlier
already accepted: **this is a summary of a scream where the rest of the chapter
is a scene.** *"at a volume that surprises everybody in the room"* is the
narrator reporting the room's reaction instead of giving the sound. The book
knows how to do this; the begging scene does it four paragraphs up.

**What the scene needs, in this book's register.** Give the sound and give what
the listeners do about it, per the house-rules worked example. The scream is one
sentence. The parents' recoil is one clause of physical fact. Then the run at
her dad, which is already right. Nothing needs to be added about how she feels.

**Cost:** chapter 9, one sentence. **Rewrite in place, ~25 words for 20.** Fold
the "up off the floor" continuity fix (P1) into the same edit. This is a
five-minute job on the book's second-biggest emotional beat and it is the single
highest value-per-word item in the queue.

### B2. Negative space overuse — Ruth's silence needs findable clues
**Asks for:** the reader should be able to read Ruth's six-month silence three
ways, and then chapter 31 should pay it off.
**VERDICT: DONE.** Chapter 28: *"In April Ruth stops posting. The chat keeps
moving through May the way it always does between her questions, until the gap
outlasts every gap before it."* Chapter 31 is Ruth's chapter and supplies the
reason (the remedial-track belief, the registrar, the folder). Exactly the
structure the reviewer described.

### B3 / BO1. Flat dialogue, distinct voices
**Asks for:** verbal tics per character (*Chloe hesitates and starts sentences
multiple times. Sam interrupts. Ruth uses precise declaratives. Kavi says very
little*), contractions, *gonna/wanna/dunno*.
**VERDICT: PARTLY DONE, and done the right way rather than the prescribed way.**
`voice_separation.py` now shows real separation by line length and register
rather than by slang: Sam 6.0 words per line with 39% of his lines at 1-3 words;
Priya 16.6; Ruth 9.6 with the highest declarative rate; Odile 78% type-token
ratio on 8 lines. Spread is 112% of the mean.
**Not done:** the *gonna/wanna/dunno* prescription, and it should not be. Nobody
in this book speaks that way and importing it would break eleven characters to
fix a note about five.
**Still open:** Chloe's prescribed tic (starting sentences multiple times) is
the one that would actually help and is missing outside the chapter 9 collapse.
See B/BO3 below.

### B4. The list problem
**VERDICT: SHOULD NOT BE DONE.** The author has ruled: the lists manipulate the
reader on purpose and stay. The review file itself carries his annotation:
*"When you are purposely trying to overload the reader, or cause them to skim...
Don't remove all lists."* Closed.

### B5. The "too clean" problem — two named sentences
- *"Chloe turns a page she stopped reading two sentences ago"* → now *"a page
  she stopped reading a while back"*. **DONE** (softened by the numbers pass).
- *"The question has already happened somewhere behind her, while she was out
  in the parking lot with the coffee cup."* No longer present in that form.
  **DONE.**
The general prescription (*write some ugly sentences*) is not actionable as
stated and is superseded by D12.

### B6. Invisible verbs
**VERDICT: SHOULD NOT BE DONE, per the author's own annotation in the file:**
*"Don't go overboard with this, it should be <10% used... Sometimes you should
keep the invisible verbs, to keep the user passive. The book is heavily reliant
on controlling readers perspective. Keep that."* Closed.

### B7. Telling not showing — three named lines
- *"She talks through the clearing of the plates and is still going when her mom
  says okay, upstairs, teeth, so that bedtime takes forty minutes."* → now
  *"so that bedtime runs long."* **DONE.**
- *"She works out the corner of her mom's mouth drops and stays down."* → now
  *"Then the corner of her mom's mouth drops and stays down. She gets up and
  starts the dishes before anybody at the table has finished eating."*
  **DONE** — and the reviewer had misdiagnosed this one; it was showing, and the
  fix removed the *"she works out"* frame that was the actual tell.
- *"He says it without any particular feeling about it."* → now *"He says it
  without any particular feeling."* **NOT DONE.** Still in chapter 2, still a
  narrator gloss on delivery, and the line it attaches to (*"The rest of them put
  it in the folder."*) does not need it. **Cut of 6 words.**

### B8. The "same beat" problem
**VERDICT: no action.** The author's annotation in the file: *"Don't replace
every instance, it's only predictable, because it is done so much. Replacing all
instances makes the new method the predictable rhythm."*

### B9. The overly intellectual six-year-old — three named lines
All three are still present, verbatim:
- ch 1: *"working out which part was the wrong part, because it is either the
  Icarus or the saying it a second time louder"*
- ch 1: *"Chloe sits with that while he waits, because the real answer has two
  halves and the question was built to hold one."*
- ch 4: *"Chloe has a very clear idea of what is supposed to happen to a child
  who does what Ruth just did, so she watches for it the whole rest of the
  period"*

**VERDICT: PARTLY DONE / mostly SHOULD NOT BE DONE.** The reviewer's remedy
(*"Chloe is six. Let her think like a six-year-old"*) is wrong for this book: a
close third on a 160-IQ child who has already learned to mask is the premise,
and review D's version of the same note is the correct one — *"complexity of
thought does not produce complexity of clause structure at that age."* The
problem is the **syntax**, not the reasoning.

Of the three, one is a genuine Rule-1 hit and should go: *"the real answer has
two halves and the question was built to hold one"* is the narrator explaining
the shape of a beat the next two lines dramatise. The other two are her thought
content, and they stay — but both are hung off a trailing *because* / *so*
clause, which is D1's construction. **One cut (~14 words) plus two syntax
re-breaks.**

### B10. Lack of sensory detail
See **P4**. The largest item in the file.

### B11. Repetitive sentence structure
Superseded by C14 and D12, both below.

### BO2. "Let the characters have more emotions"
> Instead of: "She turns her face toward the wall."
> Try: "Her chest tightens. She can't breathe. She presses her forehead against
> the cold wall and squeezes her eyes shut."

**VERDICT: SHOULD NOT BE DONE.** *Her chest tightens. She can't breathe.* is the
exact construction Rule 1 exists to prevent, and the reviewer's third sentence
(*presses her forehead against the cold wall*) is what the book already does and
does better. The diagnosis under it — that some payoffs are underwritten — is
answered by B1 and P3b, which are the two concrete cases.

### BO3. "Let the dialogue be messier"
> Instead of: "I don't know," she says.
> Try: "I don't—" she stops. "I mean, I don't know. I just. I don't know."

**VERDICT: NOT DONE, and partly warranted.** Book-wide there are **16**
disfluencies (*I mean*, *uh*, *hang on*) in 117,000 words and **3** ellipses
inside dialogue. Review D's item 2 says the same thing harder: *"Nobody in this
book says 'No — no, hang on.' Nobody says 'What?' Nobody trails off."*

This is not a Rule 1 problem; false starts name nothing. It is a register
decision, and the register is currently absolute: every character of every age
speaks in finished sentences. The one place the book breaks it — the chapter 9
begging scene — is the best-written page in the first act, which is evidence.

**What doing it would involve.** Not book-wide. **Chapters 1-9 only, and only
for characters aged six to eight**, which is where review D locates the acute
case and where the reading-grade inversion (see C20) says the prose is running
too old anyway. Ten to fifteen lines converted from complete subordinate
sentences to additive fragments, keeping the content exactly. Review D's example
of the target: Chloe's four-books argument with the librarian can be exactly as
clever with none of the subordination. **Rewrite in place, ~300 words touched
across 9 chapters.** No net length change.

### BO4. "Let the prose match the emotion"
Same passage as B1. See B1.

### BO5 / BO6. The two sensory rewrites
See **P3a** and **P3b**.

---

## Review C (items 1-20; 6 and 12 absent from the source)

| # | prescription | verdict | note |
|---|---|---|---|
| C1 | vary sentence shape away from S+V+O, comma, conjunction | PARTLY | see D12 |
| C2 | break the "and then" chains | PARTLY | book mean sentence 29.3 words; chapters 3 (43.4), 6 (45.4) and 11 (45.6) are the residue |
| C3 | characters explain their own reasoning out loud | PARTLY | see D1 |
| C4 | over-explanation / hand-holding | DONE | `passes/audit/TALKING_DOWN.md` pass executed; spot checks below confirm |
| C5 | physical grounding repetitive; "the text lives almost entirely in the hands and eyes" | DONE for hands and eyes; NOT DONE for the positive half | feet, breathing, jaw, stomach are still largely unused as grounding. Folds into P4. |
| C7 | attribution beats don't vary; 4-5 speakers with no attribution | DONE | multi-speaker scenes (ch 6 hall, ch 15 comms, ch 24) all carry attribution |
| C8 | long "which" clauses could be their own sentences | PARTLY | 29.9% of sentences carry a relative clause, 96th percentile against corpus |
| C9 | children speaking too well | NOT DONE | see BO3 |
| C10 | the word "same" | **NOT DONE** | 129.8 per 100k against a corpus **maximum** of 87.9 and a target of 125. One of only two rows `tics.py` still fails. **~10 cuts.** |
| C11 | sensory variety: smell, taste, temperature, proprioception | NOT DONE | 8 smell words in the book. Folds into P4. |
| C13 | emotional beats too evenly spaced | no action | not measurable as stated |
| C14 | "She/He + verb" sentence openings | **NOT DONE** | 128.9 per 100k against target 120 and corpus median 74.7. The other failing `tics.py` row. **~25 re-openings.** |
| C15 | the text doesn't trust silence | no action | not separable from C4, which was done |
| C16 | "though" and "except" as end-of-clause qualifiers | PARTLY | `though` at 67.0 per 100k, corpus max 70.8. At the line, not over it. |
| C17 | seventeen named repeated phrases | DONE except one | *set it back down* 0, *before she could* 0, *the whole of it* 5, *which is the whole* 3, *the same way* 8, *the rest of it* 8, *the whole way through* 10 — all cleared. **`both hands` at 38 is the exception.** |
| C18 | the text tells you what to feel | DONE | one residue, B7's *"without any particular feeling"* |
| C19 | scene transitions are too smooth | **NOT DONE** | see below |
| C20 | the prose doesn't change with the character's age | **NOT DONE, and inverted** | see below |

### C19. Scene transitions (expanded)

> There's a tendency to end one scene and begin the next with a simple time
> marker ("In September," "The following week," "By March"). This works, but it
> also means the text rarely uses the transition itself as a tool. A hard cut. A
> jump in time that disorients. A callback to an earlier image. [...] If you
> were to listen to the book via audio book, there is no obvious transition, no
> good merging of scenes. Each scene is stand alone.

**VERDICT: NOT DONE.** 161 scene openings across the book (excluding each
chapter's first). **74 of them (46%) place a date, a month, a weekday or a
duration inside the first clause.** 47 (29%) open on the time expression itself.

A representative run, chapter 25: *"The fitness test comes in the second week"*
/ *"The rifle arrives in the third week"* / *"September is tactical foot
marches"* / *"Qualification is the second Thursday of October"* / *"Sam has a
good October"*. Five consecutive scenes, five calendar openings.

Chapter 7 runs eight of ten: *"In August her mom is standing at the counter"* /
*"On a Sunday, in the car"* / *"Since the book has to go back, they go on
Tuesday"* / *"The second week Ms. Vance"* / *"The library books are due on a
Thursday"* / *"By the end of September"* / *"Her mom starts on the school in the
last week of September"* / *"In the first week of October"*.

The exceptions in the whole book number about four: chapter 19's *"'Two of you,
brothers, one of you has sold something belonging to the other.'"* opening cold
on dialogue; chapters 24, 31 and 34 opening scenes on a chat line. That is the
entire inventory of transitions used as a tool.

**Why it matters more than it looks.** The reviewer's audiobook point is the
real one. A scene that opens on a date tells the listener *where we are* before
it tells them *what is happening*, and 74 consecutive uses of that order train
the ear to stop listening for the first clause.

**What doing it would involve.** Not all 74. Twenty, chosen for spread: no
chapter should run more than two calendar openings in a row. Three techniques,
all of which the book already owns and uses once each:
- open on the object and let the date arrive in the second sentence
- open on a line of dialogue, cold
- open on a callback image (chapter 23's *"the reflex that used to send her to
  the fridge twice in a night to check a magnet was still holding a note in
  place"* is the book proving it can do this)

**Cost: 20 rewrites, first sentence only, roughly 25 words each. About 500
words touched, net zero.** Second-largest item in the queue and the one the
author explicitly asked about.

### C20. The prose doesn't change with the character's age (expanded)

**VERDICT: NOT DONE, and the book is currently running the opposite of its own
design.** From `grade.py`:

| band | chapters | ages | floor | current average |
|---|---|---|---|---|
| 1-10 | 10 | 6-8 | 5.5 | **8.11** |
| 11-15 | 5 | 8-12 | 6.0 | 7.68 |
| 16-22 | 7 | 13-19 | 7.0 | 7.90 |
| 23-36 | 14 | adult | 8.0 | 8.99 |

House rule 5: *"The point of the bands is that the book gets harder as she gets
older, so raising an early chapter above a late one works against the design
even when both clear their floors."* The band covering ages six to eight is
currently reading harder than the band covering ages eight to twelve and harder
than the band covering thirteen to nineteen. The reviewer noticed this without
being able to measure it, and the house rules already forbid it.

This is not a request to lower any chapter — rule 6 forbids that. It is the
reason P3b, BO3 and B9's syntax re-breaks all point at the same nine chapters.
**Doing the early-band work in the queue below moves this number as a
side-effect, which is why those items are grouped.**

---

## Review D (items 1-13 plus "what's working")

| # | prescription | verdict | evidence |
|---|---|---|---|
| D1 | the house sentence: *statement, comma, because/so/which/since*. "Mark every one. If more than a third of the lines carry one, cut them until they don't." | **PARTLY DONE** | book-wide 22.4% of spoken lines. **Six chapters are still over the reviewer's own one-third threshold or within a point of it: 16 (45%), 1 (41%), 7 (37%), 11 (35%), 6 (32%), 10 (32%).** Chapters 21-36 are all under 20%. The pass was run and stopped early. |
| D2 | nobody speaks in fragments | NOT DONE | see BO3 |
| D3 | the numbers: eleven, nine, four, forty, four hundred | DONE | every number row in `tics.py` passes: eleven 9.3 (target 10.3), nine 30.5 (31.2), four 110.3 (119.3), forty 25.4 (30.0) |
| D4 | announced withholding, "cut two-thirds outright" | DONE | 0.8 per 100k, 6 occurrences book-wide, against a corpus max of 1.3 |
| D5 | "the way you would" similes, "keep the best fifteen" | DONE | 17.0 per 100k, 10 raw occurrences |
| D6 | "flat", one character owns hands-flat | DONE | 30.5 per 100k for the word (target 35), 8 for the gesture |
| D7 | the eavesdrop | PARTLY DONE | see **P5** |
| D8 | the scene-ending physical beat, "used roughly two hundred times" | DONE | 11 of 196 scene-ends |
| D9 | "that's not X, that's Y" | DONE | 1 occurrence |
| D10 | "and that's the whole of it" | DONE | 5 occurrences |
| D11 | eyes-down dialogue | DONE | 8 occurrences |
| D12 | sentences that won't end; **"every page needs at least one short sentence. Two on emotional pages."** | **NOT DONE** | book: 11% of sentences are six words or fewer; `grade.py` puts sentences-inside-a-run-of-3+-short-ones at 5.24% against a benchmark of 15.08%, and sentence-length variation at the **9th percentile** of the corpus. Worst offenders: **chapter 11, zero sentences of six words or fewer in 3,602 words**; chapter 3 (3%), chapter 6 (3%), chapter 7 (3%), chapter 16 (3%), chapter 4 (4%). |
| D13 | mechanical cleanup | **PARTLY DONE** | see below |

### D13, itemised

- **Escaped characters.** **NOT DONE.** Six survive: `1961\.` (ch 12), `10\.`
  and `85\.` (ch 13), `1998\.` (ch 14), `room 4\.` (ch 16), `like this\!`
  (ch 8). Plus 43 instances of `\---` used as a scene break in chapters 1-6 and
  15. **Global find-and-replace, ten minutes.**
- **Inconsistent scene breaks.** **NOT DONE.** Three markers still in use, and
  they partition the book by block: `\---` in chapters 1-6 and 15 (43 uses),
  `---` in chapters 7-20 (45 uses), `________________` in chapters 21-35 (~90
  uses). House rule 2 flags chapters 1-6 as mid-conversion, so this is known,
  but the 7-20 / 21-35 split is not covered by that. **Pick one. Global
  replace, twenty minutes.**
- **Chapter headers.** **DONE.** All 36 are `## Chapter <Word>: <Title>`
  followed by an italic date range. No exceptions.

### D's "what's working" — treat as constraints, not prescriptions
The child's-eye interpretation; physical detail as emotion; restraint at the
payoffs (Sam's overhang, the first arrow collision, **the graduation**); the
dialectic scenes. Any pass that damages one of these has failed regardless of
what it fixed. The graduation entry is load-bearing against **P2**.

---

# PART 3 — `Feedback.md`

## Talking down

| prescription | verdict | evidence |
|---|---|---|
| Triple statement on fraction division: scene, then Chloe's thesis line, then Dave repeating it to Meg on the phone. "Cut the third, and consider cutting the second." | **DONE.** The phone call is gone. The second stays, which is what the author's own annotation asked for: *"The reason I wouldn't cut it is to show she understands it."* Chapter 6 retains *"Anybody can do the flipping... but the rightness belongs to him and not to you"* and ends on Dave folding the napkin into his shirt pocket. | |
| The four percent explained twice | **SHOULD NOT BE DONE.** Author annotation in the file: *"It's a good trick, I wouldn't cut it."* Current text, chapter 21: *"It's on their site," Ruth says, "and it still isn't a real number, because both of those can be true at once, the site and the lie on it."* Closed. | |
| The exam metaphor appears twice near-verbatim in chapter 22 | **DONE.** Only one survives, to Amberg: *"Staying keeps the question open. It just makes the room permanent."* The version to her parents is now differently worded: *"Everyone I've ever been ranked against my whole life is inside those two buildings, and I don't know what I'd be if I got ranked against anyone else."* | |
| Amberg's mark scheme scene states "showing your work" three times | **PARTLY DONE.** The phrase itself is gone from the book. The argument is still made three ways in one scene: the four marks read off the scheme, then *"a marker with a stack of these in front of them has about ten seconds each"*, then *"You wrote that answer for a reader who already has your head."* Defensible, because Chloe pushes back between each and a teacher answering a second objection is not the narrator restating. **Judgment call; if trimmed, cut the middle one (~30 words).** |
| Nadia narrates her investigative method to the men above the tire shop; "show the investigation as she does it" | **DONE, and this is a model execution.** Chapter 27 now spends a full scene on the week of investigation at first light (state business filings, the single registered agent, the county property records, the phone call to the tire shop counter in *"the unbothered voice of somebody scheduling a delivery"*). What she says in the room upstairs is now leverage rather than exposition, and it lands differently for it. | |

## Inconsistencies — all eight

| # | issue | verdict |
|---|---|---|
| 1 | Chloe turns twenty-one twice | **DONE.** Ch 33 now: *"Chloe turns twenty-one in August, two months after the last page goes in"*, consistent with ch 30's *"She's twenty-one in August."* |
| 2 | Is the bar exam real or internal | **DONE, and done as prescribed.** Ch 30 Chloe now says *"There's the bar as well. Everyone sits it at sixteen. It's the one that checks you know the law of the country you live in"* — she does not know it is unaccredited, exactly the reviewer's recommendation. Ch 19 plants the tell without stating it: *"along the front sit the teachers who wrote the paper and will mark it, proctoring both days themselves."* |
| 3 | The pairing-code arithmetic (six digits ≠ a few billion) | **DONE.** Rewritten as a key-derivation attack: *"the key is whatever they typed at pairing, run through nothing. No salt, nothing stretching it, straight in... Run everything a person can type in a hurry."* The arithmetic now works. |
| 4 | "First to sneak out in ten years" | **DONE.** Now *"They are the first to sneak out since the school opened."* |
| 5 | Clearance timing (October + ten weeks ≠ autumn) | **DONE.** Now *"The clearance comes through in December, on an ordinary Tuesday."* |
| 6 | Duplicated Sam attribution in ch 15 | **DONE.** Now *"They didn't even do costumes properly," Kavi says* / *"It worked," Sam says.* **New minor defect: the tag is now *"Sam says, looking pleased with himself"*, which names a state. Rule 1. Six-word cut.** |
| 7 | Theo's three different standards | **DONE.** Ch 32 now shows the deliberation: *"Minutes pass before Theo posts again. Those minutes go where anything with real weight goes with him: laptop closed with both hands, out onto the back steps... Partway through he comes back inside, sets a full glass of water next to the keyboard."* |
| 8 | The government has metadata and still can't see the chat | **DONE.** Ch 16 plants the answer: the system *"pushes exactly as much traffic at three on a Sunday morning, with all of them asleep, as on a Thursday night with all of them typing."* Ch 34 pays it off in the file's own language. |
| — | The footage erasure, ch 20 → ch 34 (the reviewer's "biggest unresolved issue") | **DONE.** Ch 20 now establishes that Ruth carried the box into town and ran it the whole time: it *"throws all its ugly things simultaneously at any recorder in range"*, and she *"shuts the box off in the corridor"* on the way back in. Ch 34 closes it in Ruth's own voice: *"they had a team on us and my box got their cameras too and i didnt know their cameras existed."* Range was never the problem; the box travelled. |
| — | Owen's departure | **no action needed**, reviewer ruled it intentional ambiguity and it reads that way |
| — | The chapter 18-19 gap (July 2021 to April 2022) | **NOT DONE, no action recommended.** Ch 18 is *September 2020 – July 2021*, ch 19 is *April 2022 – June 2023*. The reviewer called it *"probably intentional"*. It is the only unnarrated year in eleven and the book gains nothing by filling it. |

## Author fiat

| item | verdict |
|---|---|
| The eight-foot chain link fence; "five or six and nothing is lost" | **DONE.** The height is simply gone. Chapter 20 now: *"There is chain link a few strides behind them... Nadia goes first because she's nearest, one hand on the top rail and no pause on it."* A hand on the top rail sets the height implicitly and correctly. |
| The default AES-256 exploit turning a federal team into amateurs | **DONE.** Same rewrite as inconsistency 3, plus the characters now flag it in-scene: *"They're almost certainly actors, look at this. This is a handset you can buy in a shop. My dad's work has better than this and my dad sells insurance."* The fiat became a clue. |
| Theo gets the file | no action; reviewer supplied his own mitigation and the text carries it |
| The 91-of-91 admission rate | no action; reviewer ruled it commentary, not fiat |
| The 75 men | no action; reviewer ruled it borderline and the text carries the mitigation |
| Marek's consequences | no action; reviewer ruled it deliberate withholding and quoted the paragraph that makes it so |

## Expository stretches

| item | verdict |
|---|---|
| The university admissions section (ch 21) — "narrating the admissions process rather than letting the reader watch it" | **PARTLY DONE.** Half is now scene: an officer at Penn with a mug going cold, a colleague reading in a doorway (*"I put two of these side by side on Friday, looking for the template, and they argued opposite sides of the same question"*). Half is still narrator: *"what everybody notices first is the graduate-level prose, while what everybody thinks first is ghostwriting: ninety-one applicants from a single school, all at such a level, is a mill or a very good teacher with a template."* **One paragraph could be handed to a character. ~50 words, rewrite.** Note also that *"a mug going cold at her elbow"* and *"it goes cold at his elbow"* appear within twenty lines of each other in this chapter. |
| The Army PT test (ch 25) — "could simply say he maxed the test" | **SHOULD NOT BE DONE.** The list is now one sentence and it is load-bearing: it establishes the six-hundred ceiling four lines before *"The score is six hundred."* Remove the list and the number means nothing. The scene around it is fully dramatised (gravel, breath showing, a folding table with a clipboard and a scale, *"Under his breath he counts himself down, and pulls the bar off the ground"*). Leave it. |
| The sixty-degree archery setup (ch 14) — "several paragraphs of explanation; Chloe could figure it out while doing it" | **PARTLY DONE / effectively done.** The geometry is now one paragraph inside a scene, bracketed by Bell's dialogue and Kavi's objection, and the discovery *is* dramatised in the next section: *"It is a counting problem, and it takes Chloe until the third week to admit that"*, then the fingers-against-the-leg practice, then Ruth in the hall. Leave it. |

---

# PART 4 — `IQ_Test.md`

Three reviews of the chapter 2 test scene. The second and third correct the
first on two points, and the manuscript has followed the later ones. **This file
is the most completely executed of the five.**

| prescription | verdict | evidence |
|---|---|---|
| **Block Design must be "correct and too late", not "couldn't find it"** — the load-bearing fix, named by all three reviews | **DONE, and done exactly.** *"The picture comes apart while she is still looking at it: the top strip solid, then the middle band where every block is cut corner to corner..."* She sees the decomposition; the reader sees her see it. Then: *"Her thumb will do the square turn but it goes past the corner-to-corner every time and has to come back, and while she is coming back she knocks the block beside it crooked."* Then: *"The last block is under her hand when Ben says okay and lifts his thumb off the watch, and she puts it in anyway, because that's where it goes."* Correct and too late. |
| **"That also requires a stopwatch to be visible during the blocks"** | **DONE.** *"He puts a card down, presses the watch with his thumb, and says go."* Introduced in the paragraph before, with the physical detail of *"a silver watch with a button worn into a dip where his thumb goes."* |
| **Coding form must be Coding A — no numerals for a six-year-old** | **DONE.** *"a star, a circle, a triangle, a cross, a shape like a house, each with a different little mark inside it, a line standing up, a line lying down, a ring, two dots."* No digits. |
| **Cancellation must be visibly better than Coding, or the motor story dies** | **DONE, and this is the sharpest execution in the chapter.** Coding: *"her hand won't go as fast as the page wants... by the end of the first row the web of her thumb aches with it."* Symbol Search: *"one line is one line, which is better, and it is still slow."* Cancellation: *"She gets to the bottom and looks up, and Ben still has his thumb on the watch, and there is time left over, which hasn't happened yet today."* Three points on a curve, in order. |
| **Mazes cannot coexist with Cancellation; pick WISC-IV** | **DONE.** No maze anywhere in the manuscript. |
| **Matrix Reasoning and Picture Concepts are missing and their absence is expensive** | **DONE.** Both added, both untimed, both answered by pointing. Picture Concepts: *"a booklet stands up between them with pictures in rows... There is no watch for this one, and his thumb stays where it is."* Matrix Reasoning: *"a square of pictures with a piece cut out of it and a row of pieces along the bottom... The pieces stop being shapes and start being rules about shapes, and she keeps pointing, and Ben is turning pages faster than he has turned anything all morning."* |
| **Letter-Number Sequencing** | **DONE**, and used for characterisation: she returns the first two strings unsorted because the previous subtest wanted that, and *"the back of her neck goes hot."* |
| **Replace the mother's questionnaire with a Record Form** | **DONE.** *"the top one reading RECORD FORM upside down, which is how she reads it, before his forearm comes across and covers everything under that line."* |
| **Move the undersell from Vocabulary to Comprehension, where two-reason items make it cost something** | **DONE, exactly as prescribed.** *"Tell me another reason."* twice, then: *"Every answer she gives seems to be the right answer, so she stops trusting the questions and watches the pen instead, and the pen moves the same amount whatever she says."* |
| Review 1: reduce Vocabulary to one failure, or make them 1-point answers | **SHOULD NOT BE DONE — overruled by review 3 in the same file.** The text now runs three consecutive stops (*"one of them stops her cold... then another stops her too... and that one goes past her too, and then he closes the booklet"*), which is the correct WISC-IV discontinue rule of 3-5 consecutive zeros and is what actually ends the subtest. Review 3: *"Words stopping her cold is universal and expected... She hits hers long after the scaled ceiling, so it costs nothing."* The manuscript follows the better review. |
| Review 1: bump Digit Span to 9/7 for a 165 read | **SHOULD NOT BE DONE.** All three reviews say 8/6 is right for the target and near the biological ceiling at six. Unchanged and correct. |
| **The ceiling problem: "no test performance at age six is accurate for a 160... the form ran out before she did"** | **DONE, and it is the best line in the chapter.** Ben to Meg: *"That is the part I can't give you, because on a couple of them she got to the end of what the form has for her age and I kept going with a different one, and none of that counts. The form ran out before she did."* The two moments the review said were the only ones carrying information above 150 are both preserved: the extra Similarities booklet out of the drawer, and the hour-and-year answer. |
| **No FSIQ number should be stated** | **DONE.** No number appears. Ben gives the shape instead: *"a composite that averages two very different pictures into a single score."* |
| Add Information and Arithmetic subtests | **SHOULD NOT BE DONE.** The review itself says *"You don't have to include them."* Chapter 2 is already 4,009 words, second-longest in the book, and the scene is 16 subtests long as it stands. |

**One residue.** *"He says it without any particular feeling."* — flagged
separately as B7. Six-word cut.

---

# VERDICT COUNTS

| verdict | count |
|---|---|
| **DONE** | 51 |
| **PARTLY DONE** | 19 |
| **NOT DONE** | 14 |
| **SHOULD NOT BE DONE** | 8 |
| noted, no action recommended | 8 |
| **total prescriptions extracted** | **100** |

By source: `Issues.md` 52, `Feedback.md` 24, `IQ_Test.md` 14, plus 10 defects
and sub-items found while checking. `Some_Spark_notes.md` and `Dossiers.md`
contributed zero prescriptions.

**Read honestly:** the sentence-level and continuity work is close to finished.
Every one of `Feedback.md`'s eight inconsistencies is fixed; both of its author-
fiat items are fixed; `IQ_Test.md` is fixed almost line for line; twenty-five of
`tics.py`'s twenty-seven rows pass. What is left is not cleanup. It is writing:
one building that needs a body, twenty scene openings that need a different
first sentence, one scream that needs to be a scene, and nine early chapters
whose prose is running older than the child inside it.

---

# THE QUEUE

Hardest-hitting first. Every item names the chapters, the operation and the
words.

### 1. Give the school a body — **addition, ~750 words, 14 chapters**
`P4`. Fourteen chapters, one sensory fact each, weighted 140 words at chapter 4
and 120 at chapter 10 and thinning after. Rotate the sense and the location; the
floor plan already exists and must not be touched. Nothing is cut, so nothing
can break, and the book has 11,000 words of headroom against the average. This
is the largest gap in the review set, the reviewer said so explicitly, and it is
the only item here that adds something the book does not currently have at all.
**Half a day.**

### 2. Twenty scene openings — **rewrite, ~500 words touched, net zero**
`C19`. 74 of 161 openings currently lead with a calendar. Fix twenty so that no
chapter runs more than two in a row; chapters 7 and 25 first, then 1, 13, 26,
30. Three techniques, all already in the book once each: open on the object,
open cold on dialogue, open on a callback image. **Half a day.** The author
named this one; it is the item most likely to change how the book reads aloud.

### 3. The chapter 9 scream, and the floor it happens on — **rewrite, 25 words**
`B1` plus the `P1` continuity fix. *"She screams, at a volume that surprises
everybody in the room"* is a summary sitting four paragraphs below the best
dramatised page in the first act, and *"up off the floor"* contradicts three
lines that put her on her feet. Give the sound, give what the parents do about
it, delete the volume gloss. **Twenty minutes, and it repairs the second-biggest
emotional beat in the book.**

### 4. The early band: syntax, fragments and reading grade — **rewrite, ~350 words touched, chapters 1-9**
`BO3` + `C9` + `D2` + `B9`'s syntax half + `C20`. One job, not five. Chapters
1-10 currently read at grade 8.11 against 7.68 for the band above them, which
inverts house rule 5. The lever is clause structure, not vocabulary: break ten
to fifteen of Chloe's and the other children's subordinated lines into additive
fragments, keeping the content exactly, and let four or five of them fail to
finish. Start with chapter 1 (41% subordinated lines) and chapter 7 (37%).
**Includes `P3b`,** the living-room-floor rewrite, which is the model for the
whole item. **A day.**

### 5. D1's unfinished half — **cuts, six chapters**
Chapters 16 (45%), 1 (41%), 7 (37%), 11 (35%), 6 (32%), 10 (32%) are still over
the reviewer's own one-third threshold for dialogue subordinators. Chapters
21-36 are all under 20%, which proves the pass works and shows where it stopped.
Most of these clauses delete cleanly. **Overlaps item 4 in chapters 1, 6, 7 and
10 — do them together. Two hours on top.**

### 6. Short sentences where there are none — **additions, six chapters**
`D12`. Chapter 11 contains **zero** sentences of six words or fewer in 3,602
words; chapters 3, 6, 7 and 16 are at 3%. `grade.py` puts sentence-length
variation at the 9th percentile of the corpus. Target one short sentence per
page in those six chapters, which is roughly forty sentences. Usually achieved
by breaking an existing chain, not by adding text. **Half a day.**

### 7. Two eavesdrop conversions and one re-blocking — **rewrite, ~175 words**
`P5`. Chapter 8's *"the word program has come up through the floor"* and *"From
the stairs on a Sunday"* are the two doing pure information transfer; convert
one to a direct exchange and one to an object. Re-block chapter 1's car scene so
it does not duplicate chapter 6's word for word. **Two hours.**

### 8. Mechanical cleanup — **global, thirty minutes**
`D13`. Six escaped characters (`1961\.`, `10\.`, `85\.`, `1998\.`, `room 4\.`,
`like this\!`). Three scene-break markers reduced to one: `\---` (43),
`---` (45), `________________` (~90). Trivial, visible in every export, and the
only item on this list a script can do unsupervised.

### 9. The residue — **cuts, about 60 words total**
- `C10` "same" at 129.8 per 100k, over the corpus maximum: ~10 cuts
- `C14` "She/He + verb" openings at 128.9: ~25 re-openings
- `C17` `both hands` at 38 occurrences: ~15 cuts
- `A3` the quarter-turn shared between Ruth and Chloe: 2 substitutions, ch 19 and 30
- `A3` chapter 20's two hands-flat in adjacent paragraphs: 1 cut
- `B7` *"He says it without any particular feeling"*, ch 2: 6-word cut
- `Feedback` *"Sam says, looking pleased with himself"*, ch 15: 6-word cut
- `B9` *"because the real answer has two halves and the question was built to hold one"*, ch 1: 14-word cut
- `P6` two of the five feet-off-the-floor beats, ch 2 and ch 3: ~15 words
- `Feedback` the doubled *"mug going cold at her elbow"*, ch 21: 1 cut
- `Feedback` Amberg's middle restatement, ch 19: optional, ~30 words

**A morning, and it can be done in any order by anyone.**

### Not in the queue, deliberately

The graduation rewrite (`P2`), the "chest tightens" emotional register
(`BO2`), *gonna/wanna/dunno* (`B3`), the lists (`B4`), invisible verbs (`B6`),
letting six-year-old Chloe stop reasoning (`B9`'s content half), the Army PT
list (`Feedback`), the archery geometry (`Feedback`), Vocabulary reduced to one
failure and Digit Span at 9/7 (`IQ_Test` review 1), Information and Arithmetic
(`IQ_Test`), and filling the chapter 18-19 gap. Reasons are given at each entry.
Six of the eleven are rejected because they break Rule 1; three because a later
or better-informed reviewer in the same file overrules them; two because the
author has already ruled.

### Total

**Roughly three and a half days of work.** Item 1 is a third of it and is the
one the reviewers were loudest about. Items 3, 8 and 9 together are under a day
and clear twenty-odd separate notes. Items 4, 5 and 6 are one continuous job on
chapters 1-11 and should be run as one pass, not three.
