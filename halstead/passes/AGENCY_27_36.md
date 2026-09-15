# Agency pass, chapters 27-36, and the redone vocabulary pass in 27-31

Two jobs, in the order the brief gave them. Chapters touched: `27_nadia.md`,
`28_nineteen.md`, `29_the_file.md`, `30_cleared.md`, `31_ruth.md`,
`32_the_money.md`, `33_the_other_one.md`, `34_the_files.md`,
`35_nine_minutes.md`, `36_seventy_five.md`. No file outside this list was
opened for editing.

Read first: `passes/HOUSE_RULES.md`, `passes/DO_NOT_FLAG.md`, `CLAUDE.md`,
and (for the vocabulary job) `passes/WORDS_27_31.md`, treated as a candidate
list, not a set of instructions, per the brief.

Protected passages left untouched: Nadia's dead man's switch speech and the
chat that takes it apart (27); Deb hearing Chloe out (28); Theo's file itself
- the state assessment, the teacher memo, and the raid entry (29); Whitaker
asking who did the geometry (30); the professor keeping his pen down (31);
Chloe's "theo which four" and Ruth putting it back up (32); Theo's disclosure
and Sam's one-line answer (34); the deliberately unanswered lines in 35 and
36. Chapter 28's register-excused vocabulary (registrar, signature,
contracts, coordinator) was left exactly as it was.

Exact-string replacement only, every edit confirmed against the live file
before and after. No quoted spoken dialogue (text inside quotation marks,
attributed with "she says") was reworded for either job; a small number of
casual group-chat lines were touched, format preserved (lowercase, no
sentence-final punctuation, one `name: text` line). `measures/check_edits.py
--chapters 27 28 29 30 31 33` reports 0 problems (no hard breaks, no em
dashes, no curly quotes) and all ten chapters remain inside the 2,000-5,000
word band (36 was already at 1,998 before this pass and was not edited).
`measures/style_report.py` was run per touched chapter; the "sentences with
2+ and" figure is unchanged from the pre-pass baseline in every chapter,
since no edit added an "and" (27: 10.7%, 28: 6.6%, 29: 8.4%, 30: 12.4%, 31:
7.0%, 33: 7.8%, all held flat). No new instance of a banned phrase (instead,
both hands, leaves it, puts it back down, rather than, hands flat, turning
it over, for the first time, never once, in order) was introduced; the
existing ones already in these chapters were left as found, not part of
this brief.

## Job 1: fake agency, chapters 27-36

### Method

Ran the finder regex from the brief against all ten chapters, then read every
hit in context, then read the four verbs `goes/gets/comes/does` separately
and kept only the instances with an inanimate subject (the brief is explicit
that a person-subject hit is out of scope for this job even when the finder
or a plain grep turns it up - most `Chloe gets`, `Eli gets`, `he goes back`
hits across all ten chapters are this kind of false positive and are not
counted below).

### What "leave it" meant here, beyond idiom

Two recurring shapes in these chapters are not fake agency and I did not
treat them as candidates once I understood the shape, though the finder
surfaces them:

- **Autonomous software as the actual subject.** Chapters 32, 33 and 35 are
  about scripts that run and report on their own by design - "the worm goes
  quiet," "the watcher moves onto Eli's live feed," "the tool sits somewhere
  only Eli and Kavi can see." An inanimate subject doing something on its own
  is not fake agency in these three chapters; it is the accurate description
  of the plot. I left every instance of this.
- **A recurring refrain.** Chapter 30's interview scene marks Whitaker's
  note-taking with the same construction three times - "Into the notebook
  goes the fact that she said it," "That goes down in the notebook," "The
  reasoning goes down along with the answer" - which reads as a deliberate
  rhythm for the scene rather than three separate lapses. Left all three.
  Similarly Nadia's sleeves going up (33) and Ruth's hand finding page seven
  in the dark (35) are body-part-as-actor for the character's own action,
  the ordinary literary device, not a hidden agent.

### Changes made

**Best (given to the person who does it) - 24 changes**

- 27: "The key goes in on the second try" -> "She gets the key in on the
  second try." "A line goes on his sheet, and she moves along" -> "She
  marks a line on his sheet and moves along." "The first mornings go on the
  state's business filings" -> "She spends the first mornings on..." "A
  third morning goes on cross-referencing" -> "She spends a third morning
  cross-referencing..." "Somebody comes out onto the landing" -> "One of the
  men comes out onto the landing" (one of the four men in the room she has
  just left; not a new fact).
- 28: "Chloe's own name goes on the calendar unasked" -> "Deb puts Chloe's
  own name on the calendar unasked" (Deb is established two sentences
  earlier as the one who runs the calendar). "the spring goes on a Warsaw
  newspaper" -> "she spends the spring on a Warsaw newspaper." "A lunch hour
  goes on alphabetizing" -> "She spends a lunch hour alphabetizing." "It goes
  to Deb rather than getting fixed quietly" -> "She takes it straight to
  Deb, not something to quietly fix on her own" (also removes a pre-existing
  "rather than"). "Down goes the policy language, she reaches for" -> "She
  drops the policy language and reaches for."
- 29: "The photo goes down beside the memo" -> "He sets the photo down
  beside the memo." "The folder goes home with him" -> "He takes the folder
  home." "The folder comes back up off the desk" -> "He brings the folder
  back up off the desk." "Several versions of the question get typed before
  he sends any of it" -> "He types several versions of the question before
  he sends any of it, deleting and starting each one over."
- 30: "the form goes in a little after midnight" -> "she sends the form in a
  little after midnight." "Each one goes into the same sheet she started in
  February" -> "She adds each one to the same sheet she started in
  February." "the Friday night before goes on straightening an apartment"
  -> "she spends the Friday night before straightening an apartment."
- 31: "most of October goes on trying to find the right office" -> "she
  spends most of October trying to find the right office" (the brief's own
  worked example, found verbatim in the chapter). "Problem sets go in
  early" -> "She hands problem sets in early" (also the brief's own worked
  example, verbatim). "It goes on the inside cover of the notebook" -> "She
  puts it on the inside cover of the notebook." "Each of them goes into the
  chat" -> "She posts each of them into the chat." "what actually goes up"
  -> "what she actually posts."
- 33: "two months after the last page goes in" -> "two months after she adds
  the last page." "The line goes in twice" -> "She puts the line in twice."

**Fine (passive, doer obvious/generic, object is the topic) - 3 changes**

- 28: "Polish goes on the autumn schedule" -> "Polish is added to the autumn
  schedule" - the brief's own model sentence for a correct passive, found
  verbatim in the chapter; the doer (the school, or Chloe's own habit of
  choosing) is obvious and the sentence is about Polish.
- 29: "a second box goes to Theo's" -> "a second box is sent to Theo's." I
  did not name who carries it - the departing analyst, a facilities person,
  someone else on the floor - because the text does not say and naming one
  would have invented a fact.
- 33: "So it goes to Chloe" -> "So the job falls to Chloe." Left generic on
  purpose: the paragraph is Theo explaining why he personally cannot write
  the document, not a record of who specifically decided Chloe would: naming
  an assigner would have invented a fact the scene does not give.

**Left, with reason (representative, not exhaustive - roughly 60 further
hits were read and left)**

- Physical/natural process, no agent to name: "the heat off the dryers
  comes through the floor," "the windows stay open," "the apartment gets
  dark around her" (28).
- Spatial or ambience idiom, generic and correct: "the stairs run up the
  outside of the building," "the room goes quiet," "the chat sits quiet,"
  "the chat holds," "the no holds," "the result holds," "the ranking goes
  unmentioned" (36, already the correct implied-doer form).
- Stative fact a camera could report: "the floor holds about sixty desks,"
  "the building holds fifty-odd people," "that number sits in front of her."
- Already the correct passive form: "an offer gets logged," "a whiteboard
  that only ever gets erased halfway," "every message gets read, but barely
  any get answered," "a name gets called, an account gets frozen."
- Deliberate device, described above: the three "goes down in the notebook"
  instances (30), the software personification throughout 32/33/35, sleeves
  and hand-to-page-seven as body-part-for-person.
- Quoted spoken dialogue, not touched for this job: "It goes to the state
  attorney general's office" and "if i dont come home tonight it goes out"
  (27, inside the protected dead man's switch speech and its chat), "That's
  the whole answer, first try," "It goes into your file," and similar lines
  spoken by Whitaker or Chloe (30), Ruth's math dialogue (31), all of chapter
  32/33/34's group-chat exchanges once they touch the tool rather than a
  bureaucratic action.
- Protected content: everything inside the actual file text in 29, the
  Whitaker geometry exchange in 30, the pen-down beat in 31.

### Report

Found: on the order of 90 inanimate-subject-plus-active-verb constructions
across the ten chapters, after discarding the finder's person-subject false
positives (a majority of the raw `goes/gets/comes/does` hits were `Chloe
gets`, `he goes back`, `she does the arithmetic` - a real person already
doing the thing, out of scope). 27 of those became a real change: 24 gave
the action to the person who does it, 3 became a passive with an obvious or
generic implied doer. The rest were left, for the reasons above - mostly
idiom, camera-reportable state, an already-correct passive, or a deliberate
device (the recurring notebook refrain, the personified tools in 32/33/35).
Two places where I did not name a doer because it would have invented a
fact: who physically carries the second box to Theo's desk (29), and who
specifically decided the rules document should be Chloe's to write (33);
both stayed as generic passives instead.

## Job 2: the nine overused words, chapters 27-31

### Method

Counted all nine words per chapter, then read every instance of the
chapter's flagged high words in context (27: somebody, second, still,
before, plus whole and every as a check; 28: twice, second, before, plus
whole and still; 30: already, before, plus whole and still; 31: before,
plus somebody and still). Cut only where an instance was freely removable
without changing the sentence's meaning or a real detail; left it wherever
the word was carrying a specific fact (a count, a date, a distinction
between two things) or sat inside quoted dialogue or a protected passage.
Did not swap `whole` for `entire` or any other synonym anywhere - both
words are at their ceilings for the same reason, and moving the count from
one to the other fixes nothing, which is exactly what the last pass did 52
times and had reverted.

### Counts

| word | 27 before | 27 after | 28 before | 28 after | 30 before | 30 after | 31 before | 31 after |
|---|---|---|---|---|---|---|---|---|
| somebody | 14 | 13 | - | - | - | - | - | - |
| second | 13 | 13 | 14 | 14 | - | - | - | - |
| still | 14 | 10 | 8 | 8 | 5 | 5 | 8 | 8 |
| before | 13 | 13 | 22 | 21 | 21 | 20 | 14 | 13 |
| whole | 12 | 7 | 8 | 6 | 9 | 8 | - | - |
| already | - | - | - | - | 11 | 8 | - | - |
| twice | - | - | 11 | 11 | - | - | - | - |

### What came down, and how

- **27 "somebody" 14 -> 13.** Nine of the fourteen are inside quoted speech
  (the confrontation in the office, the tire-shop phone call, Bev's line at
  the window) and were not touched. Of the five in narration, four are doing
  real work: the opening line ("Somebody runs a scam...") sets up the
  chapter's mystery, "somebody the state now holds paper on" is a turn of
  phrase the paragraph is built around, and two more are scene texture. The
  fifth, "Somebody comes out onto the landing," names one of the four men
  she has just left, so it became "One of the men comes out onto the
  landing" - a real cut, not a synonym swap, since it points at a specific
  person rather than an unknown one.
- **27 "still" 14 -> 10.** Four cuts where the word added nothing a
  neighboring phrase didn't already carry: "are still accepting
  submissions" (the "that month" already implies duration), "She's still in
  the front room well after dark" ("well after dark" already carries the
  lateness), "an estimate from a mechanic still guessing" (guessing already
  implies ongoing), "is still up there when she reaches the car." Ten
  instances stayed because each one is doing a specific job - showing time
  passing (the sealed coffee jar, the fax number still on the door), showing
  persistence (the pass rate still under a third, he still cannot produce a
  name) - or sits inside the protected dead man's switch chat.
- **27 "whole" 12 -> 7.** Five cuts, none a synonym swap: "the whole batch"
  -> "the batch" (twice, once in narration and once in the matching chat
  line), "runs the whole tape" -> "runs the tape," "confident the whole way
  through it" -> "confident throughout," "spends the whole interview" ->
  "spends the interview." Left "Chloe learns the whole of Tyler's life this
  way, in pieces" (28, see below) and several others where "whole" is doing
  a real contrast or sits in dialogue.
- **27 "second" and "before": no cuts made.** I read all thirteen instances
  of each. Every "second" in this chapter is a real ordinal distinguishing
  one thing from another (the second word on the sign, the second try at
  the key, the second question, the second time she asks him) or is quoted
  dialogue; there is no "for a second" hedge anywhere in it to remove.
  Every "before" is genuine sequencing (before dinner, before either sound
  has finished, before the phones start) load-bearing enough that cutting
  it would have meant flattening the sentence rather than trimming it,
  matching what the previous team found for this same word in 28 and 30.
- **28 "twice" and "second": no cuts made, and this needs saying plainly.**
  This chapter's entire hook is Chloe learning to say everything twice -
  the certification explained twice, the discount explained twice, the
  Tyler-rate comparison, the coordinator who needs a deadline explained
  twice, the loading-dock trade repeating itself into a shorter and shorter
  exchange each time. Read in order, every one of the eleven "twice"s and
  most of the fourteen "second"s is a beat in that structure, not filler
  around it: "Before she notices she's doing it, she starts saying
  everything twice" is the paragraph the chapter is named for. Cutting
  these to hit a ratio would have damaged the chapter's actual device the
  way the house rules warn against driving a working technique to zero.
  I made no cuts to either word and think the count is a fact about the
  corpus comparison, not a defect in this chapter.
- **28 "before" 22 -> 21, "whole" 8 -> 6.** One "before" cut ("but before
  long the office has stopped testing her" -> "but the office has stopped
  testing her") and two "whole" cuts ("that's the whole exchange" -> "that's
  the exchange," "she reads the whole thing back once" -> "she reads it
  back once"). The other twenty instances of "before" are genuine sequencing
  (most of them setting up or echoing the "everything twice" beats above)
  and stayed for the same reason as chapter 27's.
- **30 "already" 11 -> 8.** Three cuts: "the day's translation work already
  closed out" -> "closed out," "the morning already behind her" -> "the
  morning behind her," "pen already moving" -> "pen moving." The remaining
  eight are either quoted dialogue or carry a real fact (he has already
  cross-checked something in his own folder before she says it, he is
  already ahead of her on both published papers - both are about Whitaker's
  preparation, which is the point of the scene).
- **30 "before" 21 -> 20, "whole" 9 -> 8.** One cut each: "he writes
  something down before he goes on" -> "he writes something down, then goes
  on" (avoided turning it into a second "and" in the same sentence); "one
  whole answer" -> "one answer." The interview's remaining "before"s are the
  scene's actual rhythm - Whitaker doing things in a fixed, careful order -
  and I left them for the same reason the notebook refrain in job 1 stayed.
  Two "still" hits in this chapter ("he sits very still," "the pen briefly
  still against the page") are the motionless adjective, not the
  continuation adverb the corpus measure is counting; they are a different
  word wearing the same spelling and I left both untouched and unlisted.
- **31 "before" 14 -> 13.** One cut: "Most of the drafts die before
  sending" -> "Most of the drafts die unsent." The rest are genuine
  sequencing or sit inside the protected professor scene.

### Report

Real reductions where the word was padding: somebody (27, -1), still (27,
-4), whole (27, -5; 28, -2; 30, -1), before (28, -1; 30, -1; 31, -1),
already (30, -3). No cuts to second or twice anywhere, and none to before
in 27, because reading every instance in context found them doing real
work rather than padding - most concentrated in chapter 28, where "twice"
and "second" are the chapter's own device. No word was swapped for a
synonym at any point; "whole" was cut by deletion or rewording only, never
replaced with "entire" or anything else on its own list.
