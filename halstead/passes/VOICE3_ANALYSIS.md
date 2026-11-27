# VOICE3: do the teens all talk in one voice? Analysis only

Nothing in `chapters/` was changed. Sources read: the `# halstead/` rules, `HOUSE_RULES.md`, `DO_NOT_FLAG.md`, `_SHEET_RULES.md`, the seven sheets (the "How he/she talks" sections in full), the earlier voice and dialogue passes, and the dialogue in chapters 12-28 line by line. `voice_separation.py` and `dialogue_study.py` were run. Line numbers are against the current chapters.

## 1. Is the claim true?

**Partly, and it is narrower than the reader says.**

What the numbers show. The measures cannot settle this, because they only see tagged lines and short ones. A rough attribution I ran over chapters 12-28 (name next to the quote; undercounts) gives:

| speaker | quotes | mean words | 30+ word speeches | 1-3 word lines |
| --- | --- | --- | --- | --- |
| Sam | 35 | 5.4 | 0% | 34% |
| Kavi | 20 | 6.7 | 5% | 45% |
| Nadia | 11 | 8.1 | 0% | 18% |
| Chloe | 53 | 11.8 | 7.5% | 28% |
| Ruth | 46 | 12.8 | 13% | 22% |

`voice_separation.py` agrees on the tagged prose lines: Sam is shortest and plainest (6.6 words a line, 41% one to three words), Kavi short, Chloe and Ruth close to each other. So the casts do separate on ordinary lines. The reader is not wrong about the ordinary lines being sorted; the trouble is in the **long speeches**.

What is true:

1. **Every long set-piece speech converges on one build.** Claim, then a defining distinction ("X is a different thing from Y", "that's a research problem, not a classroom one"), then a tidy closing aphorism. Ruth, Chloe, Kavi, Nadia, Priya and, worse, Sam all produce it, and so do the instructors (Amberg, Kowalczyk, Voss, Bell, the major). There are about 130 quotations of 45+ words in chapters 12-28, so this is a recurring shape, not a handful of lines.
2. **Nobody speaks badly.** Counting self-interruption, "I mean", "sorry", "wait", cut-off dashes, ellipses in quoted speech: about 1 per 1,000 quoted words in chapters 12-28 (chapter 20-28 shows zero cut-off sentences at all). Kavi's "Sorry, what was the actual question, the sheet, right, sorry" (16:27) is nearly the only well-built wander in the teen years. Nobody trails off, misstates and repairs, or answers a different question than the one asked.
3. **Drift is worst in 19-23 and 12-13.** Chapters 21-23 (applications, offer, first one) are where the cast is eighteen and arguing about their lives; the voices there merge hardest, and Sam, Nadia and Kavi each lose their own register. Chapter 12-13 (ages nine and ten) has the age problem: 100-word grievance speeches from a nine-year-old.
4. **Instructors share a lecturer's frame**: numbered steps, "the order is deliberate", "the other way round, you are guessing". Five different adults, one cadence.

What is not true: adults outside the school (Dave, Meg, grandmother, Deb) mostly keep their own register, and the 29-36 chapters have almost no long speeches. Chloe is not generally "qualification-heavy" (see below), and the drift is not the whole cast all the time.

### Does the reader's map match the sheets?

| character | reader's map | sheet | verdict |
| --- | --- | --- | --- |
| Sam | short, playful, practical, absurd | one clause, then stops; jokes first; can build an if/then when the sense needs it; does not construct a second argument under pushback | matches. Violations are lines where he constructs the second argument. |
| Ruth | precise, argumentative, blunt | even mid-length sentences, never hedges, names the person in the sentence correcting them | matches. She is the baseline the others drift toward. |
| Chloe | analytical, qualification-heavy, persistent, exact | explicitly **does not hedge** ("no I think, maybe, sort of"); her signature is the concrete physical scenario and the invented image she never explains; talks past where anyone asked | **disagrees.** Her marker is the image and the scenario, not qualifiers. Quoted hedges are rare for everyone. |
| Kavi | technical, enthusiastic, absorbed in mechanisms | conclusion first; clipped to three words unless a mechanism needs stating; no padding, no cushioning; not enthusiastic in tone | mostly matches; "enthusiastic" is not on the sheet. Out of voice when he argues about institutions or definitions. |
| Nadia | economical, organizational, direct | short independent clauses, decision first, at most one short clause of reason; **no figurative language ever** | matches, and the sheet is stricter than the map. |
| Priya | assumptions, consequences, ethics | warm, runs on, chained clauses, short launch line then a long one, animals only for figures, demonstrates rather than argues | **disagrees.** The sheet gives her no ethics lane; "assumptions and consequences" is Ruth's job. Her lawfulness question at 16:161 follows the map and not the sheet. |
| Dave | conversational, humorous, practical | plain, cost questions, no images, no hedge, one low-commitment closing word at home | **partly disagrees.** Practical yes; "humorous" is thin on the sheet (he laughs long, he does not wit). Do not add jokes to him. |

Recommendation on the disagreements: **the sheets win** (they were built from the four-reader process and the author signed them off). Tell the fix pass what the sheets say, and note to the author that the map's Chloe, Priya and Dave entries differ if he wants the sheets changed.

## 2. Worst lines, ranked

1. **21:263 Sam**: "That's not what that figure is counting, not by the definition they're using. It counts something else and puts our word on top of it." Defining distinction from a boy who said "They lie." thirty lines earlier.
2. **21:43 Sam**: "At that length they're guessing rather than reading. Everybody who wrote a paragraph knows it, and everybody who reads one knows it too." Epigram, symmetrical clause.
3. **19:89 Kavi**: "...a single idea wearing two coats." Same idea as his 19:85 "your second line in a different hat". Two clothing metaphors in adjacent speeches; Kavi is mechanism, not rhetoric.
4. **22:73 Nadia**: "a desk with nobody calling it isn't a job, it's just furniture with my name near it." Figurative, and says the desk point twice. The sheet forbids both.
5. **22:125 Kavi**: "That's a research problem, not a classroom one. A classroom's whole job is already knowing." Aphoristic definition. Not a mechanism.
6. **15:57 Ruth**: "a room agreeing with itself before anybody has chewed anything... what the whole school tastes now is the saying of it." Literary; the narrator in Ruth's mouth.
7. **22:103 Nadia**: "Checking the rest of it before there's anything to check would just be a way of not starting." Self-diagnosing maxim.
8. **23:115 Nadia**: "...nobody has to explain a gap on a form that was never asking about the gap in the first place, because the form only ever asked what a person can actually do, and it doesn't have a box anywhere on it for the year spent waiting..." Long chain of qualifications; her sheet says decision first, one short reason.
9. **17:123 Priya**: "everything wrong with the boxes has gone into the clocks and you've written calibration on it. It reads beautifully at that spot and lies everywhere else." Crisp premise-challenge, which is Ruth's engine, with none of Priya's run-on warmth.
10. **19:59 Amberg**: "...thinking it and writing it down are not the same action to a marker, whatever they feel like from inside your own head while you're doing the first and not the second." A distinction stated, then restated.
11. **16:73 Amberg**: "One... Two... Three... The other way round, you are guessing what a lock is for." Lecture frame; the numbered steps also appear in Kavi's mouth at 17:33.
12. **26:151 the major**: "a soldier who wants the next one made harder has decided the exercise is about him, when it is about every man in front of me." Explains the point.
13. **13:168 Chloe (age ten)**: "it's an argument anybody can use for anything, so it doesn't sort them, and the guy asking has the same sentences whether he's right or not." College seminar; a ten-year-old would say what happened to her, not name the flaw.
14. **12:21 Kavi (age nine)**: "the thing that stopped me is my age, which they had written down before they handed me anything to fill in. I went back the next day with a letter from the head..." Hundred-word grievance in one breath; fine as content, wrong as one unbroken statement.
15. **14:97 Chloe (age eleven)**: "the number is measuring something other than the picture, and every adult in that room changed the subject when I asked what." The thought is right; the framing is a critic's.
16. **19:179 Chloe**: "once she's said yes to something she follows through completely, whether or not the thing itself actually interests her." Character analysis spoken as if it were narration.
17. **16:21 Kavi**: "a receipt is a different object from work." Analogy plus distinction in one beat. (His next speech, 16:27, is right.)
18. **27:129 Nadia**: "I'm not calling the police, because a county detective gets a stack of form submissions... so that isn't a threat I've got, but I'm not going to stand in your office pretending I've got it, and I'm not going to waste the drive..." Double negatives; she should say it flat.
19. **23:111 Nadia**: "Every listing on there is designed to look almost right and never quite close, because closing costs them a subscriber..." Motive analysis in three clauses.
20. **15:69 Priya**: "the thing we're actually testing is whether Sam can taste a Wednesday, so Sam has to be in the room and not knowing." Experimental design as one tidy sentence; right ideas, Ruth's phrasing.
21. **18:15 Voss**: "a gun you can only point at a man is a weapon, but a gun you can put a bullet onto a bullet with is a tool." Slogan. (Keep a slogan or two; instructors are allowed one.)
22. **13:47 Kowalczyk**: "ten is the shape of every long fight there is." Aphorism.

## 3. Models that already work

- **Sam, 21:255**: "They lie." Then eating a sandwich. The right length, content and body.
- **Sam, 20:67**: "That's three sentences, but you only asked for one, so I win twice over." Playful, practical, says something, no abstraction. **Sam, 18:89**: "Because I'm where I am and I do other stuff." Leave alone; also 26:143 "Was that it, sir, or is that the practice one and there's a real one after it?" and 25:159.
- **Kavi, 16:27**: the paper from 1981, then "Sorry, what was the actual question, the sheet, right, sorry." He does not track the conversational layer; this is the sheet exactly.
- **Kavi, 14:11**: "The whole tell is in the shoulder, not the barrel, and it happens before the trigger does." Mechanism, conclusion first.
- **Ruth, 12:47** ("You were good at dance, which is why you liked it, Sam...") and **20:61** ("It's in the dictionary, which makes it a word whether you like the sound of it or not"): blunt, names the person, argues to a stop.
- **Chloe, 13:75** (the hose): concrete scenario, argued instead of the claim. **Chloe, 28:45**: "It's like Tyler's spelling test", the analogy arrives before she has decided to use it and the narration marks it as a mistake for a client. Both match the sheet.
- **Priya, 12:161** ("It's fun for me, though, even the boring parts... even the smell of the barn in the rain") and **23:161** (the horses, the bus from the airport): chained, warm, concrete.
- **Nadia, 27:35** ("A form that goes home in a bag gets filled in never") and **27:157** ("That's the whole offer, and I'm not improving it while I stand here"): flat, decision first.
- **Dave, 12:201**: finds the sentence doing no work. His voice is intact.

## 4. Recommended approach

**What the pass does.** Edit lines, not chapters. Aim for **25-35 speeches book-wide** (about 20 percent of the 45+ word speeches in 12-28, plus a few instructor lines), all from the list in section 2 plus whatever one read-through of 12-28 turns up. Per line, pick one of three moves:

1. **Swap the abstract for the particular.** Replace "defining distinction" with the thing itself: names, objects, numbers, a sandwich. This keeps word count, so it does not hurt words-per-quotation.
2. **Hand the premise back to its owner.** Defining and challenging belong to Ruth. Distinctions in Sam's, Nadia's or Priya's mouth become a plain statement plus a reaction.
3. **Cut the closing aphorism**, which is the "talks to the reader" tail. The strike-the-clause test from house rule 1 applies: if the page loses nothing, delete.

**A small amount of badly-said speech**: add roughly 8-12 moments book-wide in 12-28 (a cut-off sentence, a wrong word corrected, a change of subject, an answer to a different question). That is a rate of about one a chapter, not a dialect. Spend them mostly on Sam, Priya and Kavi. Do not make Ruth stumble.

**Rate, per house rules.** This is cut back, not to zero. Instructors should keep their set-piece lectures: one or two memorable lines each. Each of the five instructors keeps one slogan.

**Guard rails.**
- **Words-per-quotation is at its floor** (17.8 of an 18-24 target). Do not shorten speeches wholesale. Rewrite in place at roughly the same length, and where a line gets shorter, give the words back as concrete content in the same speech. Run `measures/quote_length.py` before and after and do not let the mean fall.
- **Do not dumb kids down.** The kids are 160-176 IQ. The fix is a different kind of sentence (specific, physical, sometimes wrong), not a smaller vocabulary. A pass that comes back sounding like a sitcom has failed.
- **Do not touch what is ruled.** Do not reword the 20:139 mugger lines (DO_NOT_FLAG), Nadia's fronted objects in chapter 27, Chloe's offer speech at 22:199, Sam's "doing other stuff" (18:89), or the five restored named states. Owen's rumour accounts stay contradictory.
- **House rule 1.** Do not add a trailing explanatory clause to make a speech longer; when one is cut, nothing replaces it.
- **Character-sheet conflicts**: where the reader's map and the sheet differ (Chloe, Priya, Dave), follow the sheet.
- **Measures to run after the pass**: `grade.py` scorecard no worse than before; check `tics.py`, `voice_separation.py`, `register.py`, `quote_length.py`, and the She/He-opener rate, since moving objects forward is exactly how that measure gets gamed. Reading-grade floors (7.0 for 16-22, 8.0 for 23-35) may dip slightly; per rule 6 that is acceptable but not a goal.
- **Subagents on Sonnet only**, and the rewrites below are for illustration. Sonnet agents will still lean literary, so the brief should say "read it aloud as the character would" and have the agent show the original beside each change.

**Risk worth naming.** If agents are told to "make Sam shorter", they will cut to two-word lines and break the dialogue-pass floor. The better instruction is "make Sam concrete", since that is what the sheet says.

## 5. Sample rewrites (samples only, not to be pasted)

**21:263 Sam** (counting on his fingers with the sandwich):
> Ruth got every one she asked for. Kavi got all three of his. I got everything but the twelfth, and the twelfth was the one I wanted. So we all count as happy, and they get to write down fourteen.

**21:43 Sam:**
> Ten pages a week since I got here, and it all comes down to one paragraph. Who reads one paragraph? They'll look at it for ten seconds and pick.

**22:73 Nadia:**
> I'd be good at a few hours a month of that job. The hours where somebody names the problem and I go argue with a supplier about it. The rest is a desk and a paper at the end, and every paper I've finished went to a marker and stopped there. Nobody in this building has ever rung me up wanting a price. I'd rather sit at a desk where somebody does.

**22:125 Kavi:**
> It stopped being school a while ago. The problems stopped having answers written down somewhere. I brought them a false positive rate on Tuesday and the whole building had to wait to find out if it was wrong, because nobody knew. That doesn't happen in a class.

**19:89 Kavi:**
> It's the same sentence twice. You know why the risk sits with the buyer, but he doesn't, and he can only mark what's on the page. Write me the shed burning down. Goods inside, fire on the Tuesday, who's holding the loss when the smoke clears, and why that person and not somebody else.
