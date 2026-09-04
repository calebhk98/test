# Fake-agency pass: chapters 15-26

Scope: `chapters/15_twelve.md` through `chapters/26_the_exercise.md` (twelve
chapters, Chloe age twelve through school-leaving). No other chapter touched.

Read first, and followed: `passes/HOUSE_RULES.md`, `passes/DO_NOT_FLAG.md`,
root `CLAUDE.md`. Did not run `grade.py` (other agents running it); checked
each edited chapter with `measures/style_report.py chapters/<file>.md`
instead, before and after.

## Method

Ran the finder regex from the brief across all twelve chapters, then read
every hit in context by hand, plus a few more instances the regex could not
catch (pronoun subjects like "It goes up"). For each real hit, chose one of:

1. **Person** - give the action to whoever actually does it.
2. **Passive, implied doer** - correct when the doer is obvious, generic, or
   irrelevant and the object is what the sentence is about.
3. **Leave** - idiom, natural phenomenon, a body-part-as-subject with the
   person right there, a subject that was already a person (regex false
   positive), or protected content.

Totals: **108 raw regex hits** in the finder's own count (varies chapter to
chapter, see table), plus a handful of hand-found pronoun cases. Of the
instances actually read, **20 were changed** (15 to a person doing it, 5 to
a passive with an implied doer); the rest were left, each for a stated
reason below. Two of the twenty person-fixes name a generic institutional
actor ("admin", "he" for a teacher already in the scene) rather than an
individual, which I'm counting under "person" since it's active voice with
a real doer, not a passive.

No chapter grew past its prior word count; two required exact neutrality
and got it (see Chapters 17 and 21 below). No synonym swaps were made to
move a count. No new instances of the words on the avoid list were
introduced.

---

## Chapter 15 (twelve.md) - 4,875 words, unchanged

| hit | verdict | reason |
| --- | --- | --- |
| "The bread comes up in Ruth's room" | leave | idiom - a topic "coming up" in conversation, not a physical transfer |
| "the key goes onto a folded scrap" | **FIXED -> person** | Ruth is running this round of the taste test; she is the one who would record the key. "and the key goes onto a folded scrap" -> "and she folds the key onto a scrap." |
| "watching the pen move rather than the men" | leave | subordinate perception clause ("watching X move"), not a main-clause agentless event |
| "before the alarm went" | leave | idiom, parallel to "the bell goes" which the brief names as acceptable |

## Chapter 16 (thirteen.md) - 4,149 words, +2 words

| hit | verdict | reason |
| --- | --- | --- |
| "The words come out ahead of the thought" | **FIXED -> person** | Marek is blurting the words out mid-thought while Chloe is still speaking. "The words come out ahead of the thought before she has finished" -> "He gets the words out ahead of the thought, before she has finished." |
| "The timetable lands in front of her" | **FIXED -> person** | Marek is physically placing the timetable (his solved homework) in front of Chloe. "The timetable lands in front of her, and he leans in..." -> "He slides the timetable in front of her, leaning in..." |
| "A mark on a sheet stays exactly as true" | leave | abstract philosophical claim in Marek's dialogue, not a narrated event |
| "Chloe thanks her and goes" | leave | regex false positive - "goes" belongs to Chloe, already a person, via the conjunction |
| "the vocabulary outside that frame sits close enough to English" | leave | generic statement about a language's structure, not an event |
| "the logs hold far more runs than the paper reports" | leave | stative "hold" = contain; describes document content |
| "The box sits in the drawer under Ruth's window" | leave | resting-state description, not an event of placement |
| "the encryption holds throughout" | leave | idiom - "holds" = stays secure |
| "The log sits on the table between them" | leave | resting-state description, same as the box |
| "how the table sat on that napkin for most of an hour" | leave, protected | Iyad's selective retelling - explicitly on the do-not-disturb list |
| "a riser comes out four millimeters proud" | leave | idiom - "comes out X" = turns out X, a measurement result, not physical transfer |
| "the steps hold" | leave | idiom - structural, describes bearing weight, not an omitted-agent action |

## Chapter 17 (fourteen.md) - 5,047 words, unchanged (word-neutral edit required and met)

| hit | verdict | reason |
| --- | --- | --- |
| "the smell of the place stays in her hair" | leave | sensory persistence, not an event |
| "a minute runs on the clock" | leave | idiom for time passing, no human agent |
| "before the test came out identical" | leave | idiom - "came out" = turned out |
| "The kanji arrive with most of their meaning already on them" | leave | generic linguistic fact about the writing system, not a discrete transfer |
| "a clamp that could hold anything" | leave | agent already given two words earlier ("he built a clamp...") |
| "The sound lands where the staff put it" | leave | agent already named in the same clause ("the staff put it") |
| "she sits in the room while the numbers come in" | leave | idiom, standard for reported results/scores arriving |
| "The sound comes back thin, flat" | leave | acoustic/physical description (an echo), not fake agency |
| "Her name lands in the acknowledgments" | **FIXED -> person** | Sanders is her materials-lab supervisor on this exact project and is the one who tells her about it two sentences later - a defensible, not invented, attribution. "Her name lands in the acknowledgments of the write-up in March... on a paper that stays inside the department. Sanders tells her..." -> "Sanders adds her name to the acknowledgments... on a paper kept inside the department. He tells her..." Trimmed "that stays" to "kept" in the same sentence to hold the chapter's word count exactly level (27 words before and after). |
| "The forge stays where it has been" | leave | resting-state description |
| "The bit the shell comes out of" | leave | generic mechanical fact naming a rifle part, not an event |
| "The game comes on" | leave | domestic idiom (TV switched on); doer is one of two parents and genuinely ambiguous - naming either would invent a fact, and the chapter cannot grow to accommodate a fix |

## Chapter 18 (fifteen.md) - 4,679 words, +2 words

| hit | verdict | reason |
| --- | --- | --- |
| "His hand stays where it is" | leave | body-part-as-subject; Voss is right there in the scene, not an effaced agent |
| "the count runs on her leg" | leave | Chloe tapping out a rhythm on her own leg while walking - she is the doer, described by metonymy |
| "Her plate sits full in front of her" | leave | stative description of an untouched plate, not an event |
| "The envelopes go out in October" | **FIXED -> person** | Hark is shown one sentence earlier running this exact exercise ("Hark puts the last envelope down"). "The envelopes go out in October..." -> "He sends the envelopes out in October..." |
| "Sam asks Iyad what his own came to" | leave | idiom - "came to" = totaled, like a bill |
| "Her name lands on an internal research paper" | **FIXED -> passive** | Second occurrence of the acknowledgments motif, but this project (Sandoval's, under NDA) is not clearly Sanders's - naming a specific person here would invent a fact I can't check, so a passive with an obviously institutional doer instead: "Her name is listed on an internal research paper..." |
| "the consequences land on us instead" | leave | Sandoval's own dialogue, idiomatic for "we bear the consequences" |
| "the lock held" | leave | idiom (security terminology), inside a reported line of dialogue |

## Chapter 19 (sixteen.md) - 4,174 words, +1 word

| hit | verdict | reason |
| --- | --- | --- |
| "along the front sit the teachers" | leave | regex false positive - inverted word order, subject is "the teachers," already people |
| "When the list goes up on the corkboard" | **FIXED -> passive** | Exam results posted by generic exam-administration staff; doer obvious and generic, not worth inventing an individual. "the list goes up" -> "the list is posted" (word-count neutral: 2 words either way) |
| "the names run down the left" | leave | describes layout on a page, not an event |
| "His hand comes up over his mouth" | leave | body-part-as-subject, Kavi is right there |
| "A mark for where the rule comes from" (x2) | leave | Amberg's dialogue, legal idiom for a rule's origin, said twice deliberately as part of the same lesson |
| "you've written *and so the risk sits with the buyer*" (x2) | leave, protected | this is the literal exam-answer text under discussion; the whole scene is about criticizing this exact sentence, so it cannot be paraphrased away |
| "the car goes through it" | **FIXED -> person** | Chloe is driving; Delacroix has spent the whole scene coaching her hands. "and the car goes through it" -> "and takes the car through it" (word-count neutral) |
| "she let the clock run out on herself" | leave | agent already explicit via the causative "she let" |
| "The tongs go home to the hook" | **FIXED -> person** | Pruitt has just told Chloe to take them ("Take them with you"); she is the one carrying them. "The tongs go home..." -> "She takes the tongs home..." |
| "The sun goes off the garage roof" | leave | natural phenomenon, no agent to name |

## Chapter 20 (the_parking_lot.md) - 3,385 words, unchanged, no edits

The fight and its lead-up are on the do-not-disturb list, and this chapter's
hits turned out not to need touching regardless:

| hit | verdict | reason |
| --- | --- | --- |
| "the letter came Thursday" | leave | idiom, in Ruth's dialogue |
| "the waitress comes back with the check" | leave | false positive - "waitress" is already a person |
| "at a dead run" / "a fourth run" | leave | false positives - "run" is a noun here (a sprint / an attempt), not a verb |
| "The men come out a few blocks later" | leave | false positive - "men" is already a person-plural, the regex's person list just doesn't include the plural form |
| "the swing goes past his ear" | leave, protected | inside the fight itself |
| "watching his chest move" | leave | subordinate perception clause, plus inside the fight |
| "the answer came out wrong" | leave | idiom - "came out" = turned out |
| "like the question landed for somebody else" | leave | idiom for a question's social target, not physical transfer |

## Chapter 21 (the_applications.md) - 5,048 words, unchanged (word-neutral edits required and met)

| hit | verdict | reason |
| --- | --- | --- |
| "the college a parent went to" | leave | false positive - "a parent" is already a person |
| "The call comes through on a Thursday" | leave | idiom; the caller is named in the very next sentence |
| "The escort stays in the corner" | leave | false positive - "escort" is already a person |
| "the questions came faster than the answers" | leave | idiom describing classroom pace |
| "how long the essays run" | leave | idiom - "run" = are, of length/duration |
| "the line goes quiet" | leave | idiom - a phone line |
| "the lines run to a hundred and ninety" | leave | idiom the chapter itself already uses for list length ("Chloe's list runs to fourteen," same chapter) |
| "A reply lands minutes after she sends it" | **FIXED -> passive** | the reply's origin (recruiter or auto-responder) is unknown; doer generic/irrelevant. "A reply lands... on a form that had taken her fifty minutes" -> "A reply is returned... on a form that took her fifty minutes" (dropped "had" to hold the sentence at 17 words either way) |
| "The first stays silent through the month" | leave | describes an absence of a reply, not an event with an omitted actor |
| "the count holds" | leave | idiom - stays consistent |
| "the letters go back in the drawer" | **FIXED -> person** | Chloe is the one who took them out two sentences earlier and would be the one putting them away. "the letters go back in the drawer and stay there" -> "she puts them back in the drawer to stay there" (25 words either way) |

## Chapter 22 (the_offer.md) - 4,789 words, +2 words

| hit | verdict | reason |
| --- | --- | --- |
| "a roster goes up outside the staff office" | **FIXED -> person** | admin is named in the very same sentence ("a runner coming down from admin"). "a roster goes up..." -> "admin posts a roster..." (word-count neutral) |
| "the range runs its Saturday relays" / "the forge stays open" | leave | scheduling idiom, parallel structure describing the term's fixed routine |
| "the end of the table stays on it" | leave | describes attention lingering on a topic, not physical transfer |
| "the roster goes up outside the staff office and each name is where he put it" | **FIXED -> passive** | "he" here is Iyad's private prediction of the order, not the poster - converting the posting itself to passive keeps that meaning intact while fixing the fake agency. "the roster goes up" -> "the roster is posted" (word-count neutral) |
| "both of them in the chairs...before their names come up" | leave | idiom, the calling process (the runner) is established elsewhere in the same scene |
| "His office holds a desk, two chairs" | leave | camera description of room contents |
| "the post stays open until you finish" (x2) | leave | Amberg's formal dialogue, idiomatic HR phrasing, part of his register |
| "the whole of this place came down to a letter" | leave | idiom - "came down to" |
| "all of their names go up inside the first few days" | **FIXED -> passive** | same posting-of-results pattern as above. "their names go up" -> "their names are posted" (word-count neutral) |
| "The list comes in the order he gives everybody" | leave | agent already present in the same clause ("he gives") |
| "Her hands stay where they were" / "Her hands stay where they are" | leave | body-part-as-subject, Nadia is right there |
| "A degree comes up on none of them" | leave | idiom, Nadia's dialogue |
| "his name comes up in the common room" | leave | idiom; the sentence already credits "somebody else" with supplying the number |
| "Chloe is up the kitchen-end stairs before the pudding goes round" | leave | idiom for food being served at a table |
| "the post held open until I finish" (x2) | leave, protected | Chloe repeating Amberg's offer verbatim to both parents - a deliberate callback, not incidental phrasing |
| "The silence on the line runs long enough" | leave | idiom for a pause stretching, not an omitted actor |

## Chapter 23 (the_first_one.md) - 4,679 words, +2 words

| hit | verdict | reason |
| --- | --- | --- |
| "The gowns come in three sizes" | leave | idiom - a product coming in sizes |
| "pins where a size runs long" | leave | idiom, standard clothing usage |
| "The booth holds several seconds of dead air" | leave | technical/stative description of the sound booth's delay |
| "That sentence goes straight past Chloe" | leave | idiom for something not registering |
| "Her hand stays there a second longer" | leave | body-part-as-subject |
| "a few moves into a card game" | leave | false positive - "moves" is a noun (turns), not a verb here |
| "His eyes go to the ledger" | leave | body-part-as-subject |
| "the subject stays off the counter on a Sunday" | leave | Nadia's dialogue, idiomatic |
| "his hand goes out, the way he closes with a supplier" | leave | body-part-as-subject, her father is right there |
| "The complaint goes to the chat" | **FIXED -> person** | Nadia is the one who just found the billing error and would post it. "The complaint goes to the chat that week..." -> "She posts the complaint to the chat that week..." |
| "It goes up days after the gowns are returned" | **FIXED -> person** | "It" is the hiring site Nadia built; she is the one launching it. "It goes up..." -> "She puts it up..." |

## Chapter 24 (the_chat.md) - 3,807 words, +2 words

Format of the chat exchanges themselves is fixed per the brief and untouched;
edits below are all in the surrounding narration.

| hit | verdict | reason |
| --- | --- | --- |
| "the phone goes face down on the counter" | **FIXED -> person** | Nadia herself sets it down while she works. "the phone goes face down on the counter" -> "she puts the phone face down on the counter" |
| "usually inside a minute, whatever she's doing when the message lands" | leave | digital-notification idiom, kept consistent with other message/call-arrival idioms left elsewhere (line goes quiet, call comes through) |
| "The question goes up on a Tuesday afternoon" | **FIXED -> person** | Nadia is named as posting it in the sentence just before. "The question goes up..." -> "She posts the question..." (word-count neutral) |
| "In October the question comes round again, in an email from Iyad" | leave | agent already present in the same clause |
| "she posts whenever the signal holds long enough" | leave | idiom, technical (cell signal) |
| "The bank holds incoming payments before it releases them" | leave | correct institutional active voice - "the bank" is a legitimate organizational actor, not an effaced person, same as "Polish goes on the schedule" being fine because the school is the obvious doer |
| "it sits in your branch instead of in my hand" | leave | Nadia's dialogue, stative |
| "that report comes out every month" | leave | banker's dialogue, idiom for a generated report |
| "The list holds him long enough" | leave | metaphor for a document holding someone's attention, not an omitted physical action |
| "The fee comes off for a year" | **FIXED -> person** | the banker (present throughout the scene) is the one waiving it. "The fee comes off for a year..." -> "He takes the fee off for a year..." |
| "before this year moved everyone else out of it" | leave | temporal/collective metaphor, no single agent to name |
| "The chat moves on within minutes" | leave | idiom for group conversation shifting topic, diffuse collective doer |

## Chapter 25 (forty_targets.md) - 3,376 words, unchanged, no edits

This chapter carries several of the officers' deliberately formal set-piece
speeches, and the brief is explicit that a passive is stiffer than the active
it would replace, so the instruction here was "prefer person or leave it
alone." Every hit found already had its agent present or was a natural/
generic-institutional description not worth converting:

| hit | verdict | reason |
| --- | --- | --- |
| "with the pen held clear of the paper" | leave | absolute participial phrase, same subject (the grader) as the main clause |
| "The rifle arrives in the third week" | leave | Army issue is a generic institutional process; naming a specific supply-room soldier would invent a fact, and converting to passive would raise formality in a chapter that must not go back up |
| "his was the number that never moved" | leave | describes an invariant statistic, not an event |
| "watches the paper go into the bin" | leave | subordinate perception clause; Sam himself is the one who balled and threw it, established the sentence before |
| "The morning comes up gray and low" | leave | weather, natural phenomenon |
| "a fourth sits under his hand" | leave | agent (the captain) already present via "his hand," he is mid-scene writing it |
| "The second goes to the supporting counterintelligence office" | leave | part of the deliberately formal bureaucratic paragraph describing standard routing procedure; institutional/regulatory, not a person's discretionary act |
| "A letter comes back from his grandmother" | leave | agent already present via "from his grandmother" |

## Chapter 26 (the_exercise.md) - 3,609 words, +1 word

Same formality constraint as Chapter 25 applied here.

| hit | verdict | reason |
| --- | --- | --- |
| "Then the harness goes on over the top of everything else" | **FIXED -> person** | Sam is mid-equipment-draw in the surrounding sentences (draws his rifle, lets go of the weapon). "Then the harness goes on..." -> "Then he puts the harness on..." |
| "A specialist runs a controller gun" | leave | false positive - "specialist" is already a person |
| "The report goes out flat across the fallow ground" | leave | acoustic description (a rifle's report/echo), physics, not an omitted human actor |
| "A hand arrives on his sling from the left" | leave | inside a close-quarters night engagement where Sam cannot see who grabbed him; naming an individual would invent an identity the scene deliberately withholds |
| "The lane goes cold for the better part of an hour" | leave | military-slang idiom for a lull |
| "The medic comes off the back of a truck" | leave | false positive - "medic" is already a person |
| "A controller comes down off the road" | leave | false positive - "controller" is already a person |
| "The AAR runs the following afternoon" | leave | scheduling idiom, parallel to other "X runs/goes out" scheduling language left elsewhere in the manuscript |

---

## Summary

- **Found:** 108 automated hits plus several hand-found pronoun cases (e.g.
  "It goes up"), read individually in context across all twelve chapters.
- **Became a person doing it:** 15 (including two where the named doer is a
  generic institutional actor - "admin," a teacher already in the scene -
  rather than an individual, since both are still active voice with a real
  subject).
- **Became a passive with an implied doer:** 5.
- **Left alone:** the rest - mostly regex false positives where the subject
  was already a person (waitress, escort, medic, controller, specialist, the
  men, a parent), body-part-as-subject constructions with the person present
  in the scene (his hand, her hands, his eyes), stative descriptions of an
  object's resting location or a document's contents, idioms (comes up,
  runs to, goes quiet, comes out, holds), natural or acoustic phenomena
  (weather, gunfire reports, echoes), and a handful of places where the
  agent was already named in the same sentence or clause.
- **Where naming the doer would have invented a fact:** the second
  "Her name lands..." instance in Chapter 18 (a different, NDA-covered
  research thread from the one Sanders runs in Chapter 17, so passive was
  used instead of guessing an author); "The game comes on" in Chapter 17
  (either parent could plausibly have the remote, and the chapter cannot
  grow to accommodate a fix regardless); and "A hand arrives on his sling"
  in Chapter 26 (Sam cannot identify his attacker in the dark, and the
  scene is built on that not being resolvable).
- **Protected content left untouched:** Iyad's selective retelling in
  Chapter 16; the sign-up-sheet rumour and Chloe's confrontation about it in
  Chapter 18; Bex claiming the technique/corridor beat in Chapter 16 and the
  geometry in Chapter 21; Ruth's seat with somebody else's bag on it in
  Chapter 21; Chloe's "everybody leaves school" reasoning in Chapter 22; the
  officers' formal speeches in Chapters 25-26; the entire fight in Chapter
  20; and the fixed lowercase chat format in Chapter 24.
- **Chapters 17 and 21** (both near the 5,000-word ceiling) ended at the
  exact same word count as before the pass. **Chapters 25 and 26** (the
  formality-reduced chapters) were edited with "person" preferred over
  "passive" per instruction, and Chapter 25 needed no edits at all - every
  hit in it already had its agent present, was a false positive, or was a
  natural/institutional description not worth converting.
- No word from the avoid list was newly introduced, and no synonym swaps
  were made to move any count.
