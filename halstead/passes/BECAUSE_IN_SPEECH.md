# Because-in-speech: every instance, catalogued and judged

This is a catalogue, not a pass. No chapter has been edited. Every row below is
a judgment call for the author to weigh, not an instruction to cut; the point
is that the cutting, when it happens, works from this list instead of from
whoever gets there first.

## An urgent finding before anything else

The finder script was run twice at the start of this catalogue, a few minutes
apart, before any chapter had been read for judging. The first run found
**132** instances. The second, run only to double-check line numbers, found
**129**. Three instances (`07_the_same_room:209`, `07_the_same_room:213`,
`10_april:101`) had gone from the files in between — not by anything this
catalogue did, but by some other process editing the manuscript concurrently
while this list was being built. `git diff` at the time showed uncommitted
changes across some fifteen chapter files and most of the character sheets,
timestamped about a minute before this task began.

This is exactly the situation the brief was written to prevent: a cut landing
before the catalogue that was supposed to precede it. The three vanished
instances were not judged here, because they no longer existed to judge —
`"Are you hurt anywhere? Is something actually hurting? Because that's the
first thing I have to rule out."` and `"Did somebody say something to you?
Because you can tell me if they did, and you are safe either way."` in
chapter 7, and one instance in chapter 10, now read with a question mark and
a capitalized *Because* instead of the comma the script was looking for. Two
of those three are, in this catalogue's judgment, defensible cuts on their own
merits (see chapter 7 below) — but they were not this catalogue's cuts to
make, and whoever made them made three more, one of them (`10_april:101`)
never independently reviewed by anyone. **Find out who is editing the same
noun the catalogue was asked to cover, and stop them until this list is
approved**, or the "before whoever gets there first" instruction has already
partly failed.

All figures below are current as of the final scan, after that drift: **129
locations** flagged by the finder script.

## What "found" actually means: 11 are not real instances

Of the 129 flagged locations, **11 are false positives** produced by how the
regex reads quotation marks. The pattern `"[^"]{20,400}?,\s+because` doesn't
require the *because* to be inside the same piece of dialogue it started
matching from — it only requires a quote character somewhere upstream. In
eleven places a short line of dialogue closes with a quotation mark, and the
narration that follows contains its own unrelated "**, because**," and the
regex bridges the two, reporting a character explaining themselves in speech
when actually a *narrator* is explaining a reason in prose immediately after
the character stopped talking. Two examples, verbatim:

> `"I know," her mother says, keeping her voice down to match, because the
> door is open and Chloe is close enough to hear every word.` (`11_eight:97`)
> — "I know" is the entire quotation; everything after it is narration.

> `"Fine," Theo says, and takes his hand down. The folder comes back up off
> the desk, because leaving it open there is worse than finishing it.`
> (`29_the_file:77`) — same shape.

These are marked **EXCLUDE** below rather than folded silently out of the
count, because the brief asked for every location the script found. They are
not part of the "because in speech" problem at all (a couple of them may be
worth a look under a different finding — narrator explanatory clauses — but
that is `style_report.py`'s job, not this one, and is outside this catalogue's
scope). Subtracting them leaves **118 real instances** of a character
explaining themselves inside their own dialogue with a "**, because**"
clause. All rates and the KEEP/CUT/REWORD split below are against that 118.

## The scorecard

| | count |
|---|---|
| Locations flagged by the script (current state) | 129 |
| Of which, script false positives (narration, not speech) | 11 |
| Real instances of the construction | **118** |
| KEEP | **49** |
| CUT | 31 |
| REWORD | 38 |

**The author asked for roughly 48 kept. This catalogue lands at 49.** That is
closer than the process that produced it deserves credit for: the first pass
through every instance, judged chapter by chapter as it was read, came out at
**75** keeps — badly over target. Nothing about that first pass was dishonest;
almost every one of those 75 does *something* defensible by the stated test
(a real argument, a piece of teaching that lands, a character's own way of
talking). The problem is exactly the one `HOUSE_RULES.md` names for a
different construction: *"a device that would be good seven times in a book
and appears forty times needs to come down to about seven. It does not need
to reach nothing."* A scene can be well-written and still be one instance too
many of a shape the book has already used. Once every instance was back on
one page together, the second pass went back through all 75 keeps and applied
a harder question to each one: does cutting the clause lose something the
reader cannot get any other way, or is this a good scene that would survive
fine without this particular tic. Twenty-six of the original 75 failed that
harder question and moved to CUT or REWORD. The 49 that remain are listed as
KEEP below; nothing was forced to make the number — see "Where more would
come from" at the end if the real target turns out to be under 49.

---

## Chapter 1: Before

- **01_before:65** — Chloe's mother, reporting to someone on the phone.
  `"She had to be told twice to eat, because she couldn't do both."`
  **CUT.** Restates a scene the reader just watched play out at the table;
  the phone listener needed the reason, the reader already has it.

- **01_before:197** — her father, at dinner.
  `"Well, that's the class, though, because they all read it together, so
  nobody gets to the end ahead of anybody else."`
  **CUT.** A mild, generic domestic reassurance any parent in the book could
  have said in the same shape; nothing is lost by trimming it.

- **01_before:201** — not dialogue.
  `" She laughs at her own joke, and Chloe laughs too, because it's her mom"`
  **EXCLUDE.** Narration ("Chloe laughs too, because it's her mom") caught
  only because the regex bridged it from the closing quote of a line of
  dialogue two sentences earlier. No character is explaining anything here.

## Chapter 2: March 4th

- **02_march_4th:23** — Chloe's mother, answering Chloe's direct challenge
  about the intake form. `"I'm doing my best guess on some of these, because
  I only get to see the outside of you, so I guess honestly. If I get it
  wrong, you can tell me afterward and I'll change it,"`
  **KEEP.** Real justification to a child who has just called her out;
  establishes the book's core irony about being judged from outside.

- **02_march_4th:235** — Ben, the psychologist, to Chloe's mother, overheard
  through a door. `"I'm not seeing what the school is seeing, because she
  finishes in the first few minutes and then she's got the rest of the hour
  left over and nowhere to put it."`
  **KEEP.** Load-bearing diagnostic information the reader needs and gets
  nowhere else in the book.

- **02_march_4th:251** — Ben, answering "how far at the top of it?"
  `"That is the part I can't give you, because on a couple of them she got to
  the end of what the form has for her age and I kept going with a different
  one, and none of that counts. The form ran out before she did."`
  **REWORD.** Third "because" in a four-beat Q&A with the mother; the
  ceiling-effect fact matters, the causal glue between sentences doesn't.
  *Reword:* "That is the part I can't give you. On a couple of them she got
  to the end of what the form has for her age, and I kept going with a
  different one, but none of that counts. The form ran out before she did."

- **02_march_4th:257** — Ben. `"A good one, but that's exactly the trouble
  with it, because it's bad numbers that move a system, and this one is
  going to read as good on the page."`
  **KEEP.** The book's central irony about scores and help, stated once and
  never stated better.

- **02_march_4th:261** — Ben. `"The lever is the school, because that's
  where the empty hour is, so I can write it all up and you can walk it in
  there, and some of them do move on a report like that."`
  **REWORD.** Fourth "because" in the same short exchange. *Reword:* "The
  lever is the school. That's where the empty hour is. I can write it all
  up, and you can walk it in there. Some of them do move on a report like
  that."

## Chapter 3: The Letter

- **03_the_letter:71** — mother, on the phone with the district receptionist.
  `"Okay, thank you, and I do appreciate it, because I know it's not your
  job to go looking."`
  **CUT.** Generic phone courtesy; carries no plot weight.

- **03_the_letter:79** — mother, relaying the receptionist's warning.
  `"She said people do this. There are people who send things to houses
  with a child's name on the outside, because a child opens it, and that's
  how you find out which houses write back. She told me to look at the
  postmark."`
  **KEEP.** The only place the book explains the mechanism by which Chloe
  was found; information the reader needs with no other route to it.

- **03_the_letter:101** — mother, pressing the school on the phone.
  `"Okay, but somebody made the list, because a person made it, somebody
  sat down and typed my kid's name. I want the name of that person."`
  **CUT.** The clause restates the sentence's own first half almost word for
  word; the demand for a name works without it.

- **03_the_letter:123** — mother, to the father. `"Usually pretty good is
  the vaguest possible way anybody could answer that question, because a
  phrase is what you reach for when you haven't got a number. That's the
  one thing she said all night that wasn't a fact."`
  **REWORD.** Sharp and genuinely her voice, but the book returns to this
  shape (a parent parsing a stranger's language) often enough that it should
  come down. *Reword:* "Usually pretty good is the vaguest possible way
  anybody could answer that question. A phrase is what you reach for when
  you haven't got a number. That's the one thing she said all night that
  wasn't a fact."

- **03_the_letter:135** — mother. `"Not one town, not one state, because
  she said they come from all over, and then she said we're one of the
  closer ones."`
  **REWORD.** Exists mainly to feed the father's punchline a line later
  ("Four hours is one of the closer ones"); doesn't need the causal word to
  get there. *Reword:* "Not one town, not one state. She said they come
  from all over, and then she said we're one of the closer ones."

- **03_the_letter:205** — mother, arguing with the father late at night.
  `"She's been flat since Christmas, and you've seen it, because she comes
  home and she says it was good."`
  **KEEP.** Real disagreement between the parents that answers the father's
  dismissal directly; the hinge that starts them toward saying yes.

- **03_the_letter:221** — the librarian, to Chloe. `"That's not how it
  works, honey, because it resets every time you come in, so it is still
  four however long you wait. It isn't a bank. You can't save them up."`
  **CUT.** A nice callback to chapter 1, but the rule and Chloe's next move
  land fine without the explanatory clause.

## Chapter 4: Pluto

- **04_pluto:81** — mother, on the phone. `"Okay, yeah, okay, stay right
  where you are, because I'm coming."`
  **REWORD.** Pure comfort language; the two halves work as two short
  sentences. *Reword:* "Okay, yeah, okay, stay right where you are. I'm
  coming."

## Chapter 5: Behind

- **05_behind:203** — Ruth, correcting the table at dinner. `"The word is
  tidally locked. It isn't stuck and it isn't on purpose either. It got
  slowed down until it matched. It used to spin. Then it stopped spinning,
  over a really long time, because of us."`
  **CUT.** Charming on its own, but "a character corrects the table with a
  science explainer" is one of the most repeated scene-shapes in the whole
  book (Ruth, Kavi, Chloe, Nadia and Priya all get a turn at it); the scene
  plays fine without the trailing clause, and the rate is exactly what this
  finding is measuring.

## Chapter 6: The List

- **06_the_list:7** — an unnamed father, breakfast-room chatter.
  `"We drove it, both ways, because there was no version of this where we
  put her on a bus. We looked at the map for an hour and decided we'd
  rather just drive it ourselves,"`
  **CUT.** Background ensemble voice explaining an ordinary choice;
  interchangeable with any parent in the room.

- **06_the_list:11** — an unnamed parent, same scene. `"Somebody must have
  taken it, because a letter that lists transportation has somebody in
  mind."`
  **CUT.** Second instance in four lines in the same generic ensemble
  exchange.

- **06_the_list:111** — Chloe's father, at the graduation dinner.
  `"But you could already do them, because you told me you got all eight of
  them right."`
  **REWORD.** Sets up Chloe's genuinely good reply about the difference
  between a right answer and understanding one; the challenge itself
  doesn't need the causal glue. *Reword:* "But you could already do them.
  You told me you got all eight of them right."

## Chapter 7: The Same Room

- **07_the_same_room:29** — mother. `"That's all right, we can look him
  up, because everybody is in the book. What's his last name, sweetie,
  since that will get us there faster than the first name will,"`
  **CUT.** First of two near-identical "we'll manage this logistics
  problem" lines in one scene; the more generic of the pair.

- **07_the_same_room:49** — mother. `"It's OK, the last names can go,
  because we can just ask the school instead,"`
  **REWORD.** The actual pivot into the phone-call scene; keep the content,
  not the shape. *Reword:* "It's OK, the last names can go. We can just ask
  the school instead."

- **07_the_same_room:67** — mother, answering a persistent Chloe.
  `"Honestly, sweetheart, it's hard to say, because it could be one week or
  it could be a month, and every call moves at its own pace."`
  **REWORD.** *Reword:* "Honestly, sweetheart, it's hard to say. It could be
  one week or it could be a month, and every call moves at its own pace."

- **07_the_same_room:123** — Ms. Vance, teaching the time-capsule exercise.
  `"Here's the part I want you thinking about while you're writing, because
  you're not writing it to me and you're not writing it to your friends at
  your table. The person who opens that box is you, three years older, and
  whatever's on that paper is what they get."`
  **KEEP.** Sets up Chloe's own good in-class insight a few lines later; the
  whole exercise's logic depends on this framing being said aloud.

- **07_the_same_room:151** — mother, noticing Chloe has stopped reading.
  `"What happened to getting more books this week, because that's not like
  you at all?"`
  **KEEP.** The line that opens the chapter's concealment thread; the first
  of a pair, and the one that actually introduces the worry.

- **07_the_same_room:155** — mother, four lines later. `"Since when do you
  skip an entire week, though, because that's new."`
  **CUT.** Restates the worry the line before it just raised, in the same
  breath.

- **07_the_same_room:205** — Ms. Vance, to a crying Chloe. `"Hey, hey, hey,
  what's going on down here, because you're all right, so just talk to
  me."`
  **KEEP.** Opens the chapter's emotional turn. Originally the first of
  three in a row in this scene; the other two were independently rewritten
  out of the flagged shape during this session (see the note at the top) —
  this catalogue would likely have kept exactly one of the three regardless,
  since three back-to-back reassurances from the same speaker is the
  clustering this finding exists to catch.

## Chapter 8: The Asking

- **08_the_asking:7** — mother, on the phone with Ms. Vance. `"No, I
  appreciate you calling, because most people wouldn't have. She's been
  like this since August, and it's about her, not about you or the house,
  she was completely fine in July, but then school started."`
  **CUT.** Generic phone gratitude; the substantive information doesn't
  need it.

- **08_the_asking:59** — Dr. Ammons, to a defensive mother. `"I'm sure she
  did, but I'm asking anyway, because loving a place and something
  happening there can both be true at once. I ask everybody this. It isn't
  about the place."`
  **KEEP.** Plants a suspicion the book's larger mystery about Halstead
  depends on; directly answers the mother's challenge.

- **08_the_asking:183** — mother. `"What was different there, not the fun
  parts, because I've already heard every single fun part, but what was
  actually different about it, underneath all that? I keep getting the
  bridge and the apples and I still don't know what the place was."`
  **KEEP.** Produces "Nobody was mean," one of the book's key emotional
  beats; no other route there.

- **08_the_asking:197** — mother. `"You can tell me if somebody is, because
  telling me keeps you out of trouble and goes nowhere except me. I
  wouldn't go to the school with it unless you said so."`
  **CUT.** Generic parental reassurance; the scene's real weight is carried
  by 183 and by Chloe's answer, not by this line.

## Chapter 9: February

- **09_february:41** — mother, to a sobbing Chloe. `"Baby, breathe for me,
  just breathe, because you have to breathe before you can talk about any
  of it."`
  **CUT.** Near-tautological; "breathe for me, just breathe" already
  carries the scene.

- **09_february:67** — mother, to the father, in a real argument.
  `"Then say it out loud at this table, because I need to actually hear it
  from you, not guess at it from the other side of the room. I've been
  filling in your side of this conversation in my head for months now, and
  I could be filling it in wrong."`
  **KEEP.** Genuine marital confrontation with real vulnerability; central
  to the parents' arc.

- **09_february:129** — father. `"Then give me one reason, because I have
  been sitting here trying to think of one, but I can't."`
  **REWORD.** First of three "because" beats in one eight-line argument
  (129, 135, 137); the softest of the three. *Reword:* "Then give me one
  reason. I have been sitting here trying to think of one, but I can't."

- **09_february:135** — father. `"That's a hell of a way to put it, Meg,
  because you make it sound like I already agreed to hand over the roof
  over her head. I said yes to a summer camp, not to putting our whole
  address inside their gate, and there is a difference between those two
  things even if you've stopped seeing it. You can hand somebody a month.
  You cannot hand somebody a street."`
  **KEEP.** One of the best lines in the book; real self-justification under
  real pushback.

- **09_february:137** — mother. `"It's how it is, though, and you know it
  is, because you said yes to the whole idea back in July, before either of
  us had even heard the word furnished."`
  **KEEP.** Closes the argument with the point that actually wins it; the
  necessary counterpart to 135.

- **09_february:145** — Mrs. Okonkwo, a Halstead administrator. `"I can't
  tell you who's enrolled here, sweetheart, because those are other
  families, and that's between them and us."`
  **CUT.** A privacy line any administrator would give in the same shape;
  low stakes.

## Chapter 10: April

- **10_april:29** — Kavi, comic complaint. `"I have been through this
  whole building since lunch, the office, then the laundry, then outside to
  the road, because I thought you might still be sitting in the car. Then a
  girl in the stairwell whose name I don't even know told me you'd been
  here an hour. Sam knew the entire time and let me do the whole tour
  anyway."`
  **CUT.** Funny, but the clause is pure comic texture setting up a prank
  punchline it doesn't actually carry.

- **10_april:35** — Chloe, making a room list. `"What's your last name,
  because you're going right under Ruth's, and then I've got everybody here
  except Sam's number,"`
  **CUT.** Restates the list-keeping mechanic the narration already showed
  two paragraphs earlier.

- **10_april:53** — Fen, answering a real question about her rock
  collection. `"By size, smallest closest to the door, and if two look the
  same I hold one in each hand, because heavier's always a little bigger
  even when you can't see it."`
  **REWORD.** Specific and characterful, but not essential. *Reword:* "By
  size, smallest closest to the door. If two look the same I hold one in
  each hand. Heavier's always a little bigger even when you can't see it."

- **10_april:75** — Ruth, defending her knife work. `"It's just wider at
  one end, because that's how the onion grew."`
  **CUT.** The teacher's next line delivers the actual payoff; Ruth's
  defense is dispensable.

- **10_april:93** — the literature teacher, on the school library's rules.
  `"As many as you can carry, because there's no card and no record, and
  the desk empties out in the evening. Take what you want, bring it back
  when you're finished with it, and if you lose one then come and say you
  lost it."`
  **KEEP.** The direct thematic payoff of Chloe's chapter-1 fight with the
  home librarian over the four-book limit; essential contrast.

- **10_april:117** — the writing teacher, on who gets sent home. `"Not for
  being bad at something, if that's what you're asking. People do go home
  sometimes, because their family decides they want them home, and that
  happens now and then in an ordinary year, which makes this a school
  rather than a prison, and certainly rather than a competition you can be
  knocked out of,"`
  **KEEP.** Necessary institutional rule that sets up the whole Owen thread
  the rest of the chapter explores.

- **10_april:121** — Kavi, on Owen's departure. `"Owen wanted to stay, and
  before you ask, I am going off something I saw with my own eyes. I know
  you're about to ask me how I know. He was crying by the kitchens on the
  Thursday and I saw him, but I didn't say anything, because I was seven
  and I didn't know what you say to that, and then on the Saturday his
  mom's car was outside and he was in the back of it."`
  **KEEP.** The load-bearing account of Owen's departure, supporting the
  Thursday/Saturday timeline the book's own continuity depends on
  (see `passes/DO_NOT_FLAG.md`, "Owen leaves on a Tuesday in one chapter and
  a Saturday in another").

- **10_april:125** — Kavi, continuing. `"About going, because she came and
  got him and he wanted to stay. And he was keeping up, if that's the next
  one, because he was doing exactly what the rest of us were doing, the
  water thing and the bridge and all of it, and doing all of it fine,"`
  **REWORD.** Second "because" beat in the same answer as 121. *Reword:*
  "About going. She came and got him and he wanted to stay. And he was
  keeping up, if that's the next one. He was doing exactly what the rest of
  us were doing, the water thing and the bridge and all of it, and doing
  all of it fine."

- **10_april:129** — Kavi, closing the conversation. `"You already have
  all of it, Chloe, because his mom came and that was the whole of it. You
  keep asking about this, and you asked Ruth in April, at the trays, while
  I was standing right there,"`
  **CUT.** Third "because" in the same Owen exchange (121, 125, 129);
  restates what 121 already gave the reader.

- **10_april:159** — not dialogue. `Fen has to check, running a finger
  along the sill before she answers, because another came in during March`
  **EXCLUDE.** Narration, caught only because the regex bridged from the
  closing quote of Chloe's question two clauses earlier.

- **10_april:165** — Ruth. `"Though not before ten, because my dad's
  asleep by then and the phone's right outside his door."`
  **CUT.** Nice incidental detail, no plot or character weight beyond what
  the scene already carries.

## Chapter 11: Eight

- **11_eight:5** — mother, buying a new bike. `"We'll get you a bigger
  one, because that's not fitting you again even by September."`
  **CUT.** States the obvious; nothing is lost cutting the reason.

- **11_eight:49** — mother, asking Chloe to repeat a Spanish word.
  `"Say it again, slower this time, because I lost it somewhere in the
  middle."`
  **CUT.** A request for repetition needs no justification.

- **11_eight:53** — Chloe, teaching her mother Spanish. `"The first part's
  right, but it's the middle that goes wrong, because you keep putting the
  weight on the wrong bit, and that turns it into a different word, so just
  do the one word on its own. Están."`
  **KEEP.** Chloe's precision turned, with real tenderness, on her mother;
  the only scene of its kind in the book.

- **11_eight:97** — not dialogue. `"I know," her mother says, keeping her
  voice down to match, because the door is open and Chloe is close enough
  to hear every word.`
  **EXCLUDE.** "I know" is the whole quotation; the reason belongs to the
  narrator describing an action, not to a character explaining herself.

- **11_eight:145** — Coach Bell, teaching the class to dodge darts.
  `"It isn't, and I'll tell you why now instead of letting you spend a week
  deciding it is. Look at the size of the thing next to your hand, and look
  how slowly it comes at you once you're watching for it, because you can
  watch the entire flight end to end, and that makes it the easiest thing
  in this building to hit. You'll all be bad at it until Thursday."`
  **REWORD.** Good teaching, but the "watch the body, not the projectile"
  lesson recurs in a tighter form in chapter 14; trim the longer, earlier
  version. *Reword:* "Look at the size of the thing next to your hand, and
  look how slowly it comes at you once you're watching for it. You can
  watch the entire flight end to end. That makes it the easiest thing in
  this building to hit."

- **11_eight:201** — the choir teacher. `"Stand next to Amara and match
  her, because she's doing the thing I keep asking you for and can't tell
  you how either."`
  **CUT.** Minor logistical direction; nice touch, replaceable.

## Chapter 12: Nine

- **12_nine:9** — an office administrator. `"Nine-year-olds get eight,
  that's just how the sheet works this year, and you were on seven, so it's
  one more than you're used to. It goes up every single year, because that
  is supposed to be the whole idea of a school, so is there a problem with
  it?"`
  **CUT.** A brusque minor character's aphorism; cutting it loses nothing of
  her voice or the scene's information.

- **12_nine:17** — Kavi, first of an enumerated complaint. `"The first is
  that the form does nothing, because it asks you for three, but it gave me
  zero of them."`
  **REWORD.** *Reword:* "The first is that the form does nothing. It asks
  you for three, but it gave me zero of them."

- **12_nine:21** — Kavi, second beat of the same rant. `"Then it should say
  that on the top of it, because what it says is preferences. The second is
  that two of them are running in this building this year."`
  **REWORD.** *Reword:* "Then it should say that on the top of it. What it
  says is preferences. The second is that two of them are running in this
  building this year."

- **12_nine:59** — Mrs. Sun, teaching tone in Mandarin. `"You're hearing
  tone as emphasis, and that's English doing it to you, because in English
  you go up at the end to make a word matter. Here the pitch sits inside
  the word. The pitch *is* the word. It's the same as changing a letter in
  it."`
  **REWORD.** Real linguistic content worth keeping; split it rather than
  count it toward the rate along with every other classroom-explainer
  scene. *Reword:* "You're hearing tone as emphasis, and that's English
  doing it to you. In English you go up at the end to make a word matter.
  Here the pitch sits inside the word."

- **12_nine:63** — Mrs. Sun, same exchange. `"You won't, and nobody hears
  their own, so stop sitting there trying to fix it from the inside. Record
  yourself and play it back, because you'll hear it coming out of a
  speaker, sit next to somebody in this room who already has it, and run
  the recordings on the machines in the library while you're doing
  something else."`
  **REWORD.** Second "because" in the same exchange as 59. *Reword:*
  "Record yourself and play it back. You'll hear it coming out of a
  speaker. Sit next to somebody in this room who already has it, and run
  the recordings on the machines in the library while you're doing
  something else."

- **12_nine:73** — Kavi, dinner-table argument with Chloe. `"Small result,
  so round it down, because a room that size is basically noise dressed up
  as a finding."`
  **CUT.** Sets up Chloe's sharper rebuttal at 75; the weaker half of the
  pair.

- **12_nine:75** — Chloe, cut off mid-word. `"Small is the wrong word,
  because that is the size of result a room that small hands you by
  accident, which is the entire-"`
  **KEEP.** Her half of a real intellectual sparring match, distinctly her
  precision, and cut off comedically before she finishes.

- **12_nine:85** — Vasquez, teaching chemistry. `"Glassware, reagent, or
  you, take your pick, because it is always one of the three. Friday, and
  dry every piece of glass before you touch it this time,"`
  **REWORD.** *Reword:* "Glassware, reagent, or you, take your pick. It is
  always one of the three. Friday, and dry every piece of glass before you
  touch it this time."

- **12_nine:133** — Sam, before his big climbing-wall attempt. `"Then
  thirty people watch me not do it, and that's still Monday. Left foot
  first, like she told me in January, because left foot's what does it, not
  the arms, not the grip, just where that one foot lands. She said so, and
  she was right, and I believed her before I even tried it."`
  **KEEP.** Sam's own deadpan resignation right before his payoff moment;
  earns its place.

- **12_nine:151** — Chloe, apologizing to Priya. `"Yeah, and I should have
  told you instead of just not showing up on the Thursday, because I know
  that's the worse way to do it."`
  **KEEP.** A real apology that opens the "what's fun for you isn't fun for
  me" exchange, a theme the book returns to with Nadia later.

## Chapter 13: Ten Pages

- **13_ten_pages:11** — Mr. Hearn, setting the chapter's terms.
  `"One ten-page essay a week, and that's less than half his rate, you've
  got a keyboard, and nobody is waiting on you to walk it to a printer on
  Saturday morning. The first is due Monday. It has to be as good, and
  that's the part that's actually hard, because the length is easy, it is
  just hours, so if you want to know what I'm marking against, go and read
  them, and they're short enough that there's no excuse not to."`
  **KEEP.** Sets the chapter's engine in motion; not repeated anywhere else.

- **13_ten_pages:39** — Kowalczyk. `"A few rounds a class, and the rest of
  the hour is what you've been doing since September, because that carries
  on regardless. Nobody gets to skip conditioning just because they've
  started sparring. You'll be doing both right up until the day you stop
  coming to this room at all."`
  **CUT.** The very next sentence already restates the same point; the
  "because" clause is filler between two versions of one rule.

- **13_ten_pages:152** — Chloe, arguing tariffs with her father.
  `"Steel says it, textiles said it, and somebody's going to say it about
  something neither of us has heard of. That's the actual problem, because
  it's an argument anybody can use for anything, so it doesn't sort them,
  and the guy asking has the same sentences whether he's right or not."`
  **KEEP.** One of the best father-daughter exchanges in the book; her own
  reasoning, on the record, earning real respect.

## Chapter 14: Sixty Degrees

- **14_sixty_degrees:11** — Kavi, comparing paintball to archery.
  `"That's the opposite of what we do with the paintballs. We watch the
  person rather than the dart, so we're moving before he shoots. The whole
  tell is in the shoulder, not the barrel, and it happens before the
  trigger does. You can train yourself to stop flinching at the sound, but
  you can't train the shoulder out of somebody, because it moves before
  they know they're going to shoot."`
  **KEEP.** Pays off across chapters; specific and technical, distinctly
  Kavi's mind at work.

- **14_sixty_degrees:69** — Chloe, arguing with Ruth over Latin.
  `"Answering back is beside the point, because what I want is to read
  what's already sitting in it."`
  **REWORD.** *Reword:* "Answering back is beside the point. What I want is
  to read what's already sitting in it."

## Chapter 15: Twelve

- **15_twelve:17** — Chloe, on her forge work. `"The scroll's wrong, right
  at the top curve. It goes tight and then opens out, right where my thumb
  is, because that's two curves welded in the middle pretending to be one,
  so hold it up at the window and you'll see it."`
  **REWORD.** *Reword:* "The scroll's wrong, right at the top curve. It
  goes tight and then opens out, right where my thumb is. That's two curves
  welded in the middle pretending to be one. Hold it up at the window and
  you'll see it."

- **15_twelve:39** — Coach Bell. `"That's the two of you to sort out," he
  says, buttoning the pocket, "and I'd think about it first, because
  whoever calls the count is the one whose bad afternoon everybody else has
  to have."`
  **REWORD.** *Reword:* "That's the two of you to sort out, and I'd think
  about it first. Whoever calls the count is the one whose bad afternoon
  everybody else has to have."

- **15_twelve:51** — Ruth, teasing Chloe about height. `"People stop at
  different times, and my mother was exactly this height at twelve, but
  finished a good deal taller, so make the most of your next few years,
  because that's the whole of what you're getting."`
  **CUT.** Fun teasing, no plot weight; the joke lands without the closing
  clause.

- **15_twelve:79** — Kavi, on the bread test. `"We're doing them and they
  have to come out identical," he says, already pulling a tray down, "so it
  has to be the big oven, because that's a box with one temperature in it
  and the conveyor cooks the front of a run harder than the back."`
  **KEEP.** Establishes why it's specifically a *gas oven*, the detail the
  Thanksgiving scene later turns on; needed connective tissue.

- **15_twelve:117** — Sam, inventory-counting banter. `"There were not
  sixteen of anything left over, because I counted it twice before I wrote
  the number down."`
  **CUT.** Throwaway comic beat with no lasting stakes.

- **15_twelve:315** — mother, at Thanksgiving. `"It was a gas oven." ...
  "A gas oven, lit, in the middle of the night, with children alone in the
  room, and which one of you lit it is beside the point, because what I
  mind is a flame going while the room is empty."`
  **KEEP.** Real parental fear, directly answering Chloe's minimizing;
  opens the chapter's closing confrontation.

- **15_twelve:327** — Chloe, defending herself in the same argument.
  `"I'm on it, Kavi's on it, Sam and Ruth are on it, and anyway the oven is
  the one part they let go, because what they got us for was being out of
  our rooms and in a kitchen alone when the rule says you tell somebody
  first."`
  **REWORD.** Third "because" in the same family argument (315, 327, 331).
  *Reword:* "I'm on it, Kavi's on it, Sam and Ruth are on it. The oven is
  the one part they let go. What they got us for was being out of our
  rooms and in a kitchen alone when the rule says you tell somebody first."

- **15_twelve:331** — mother, closing the argument. `"Four hours of
  counting tomatoes sounds about right to me," her mother says, "and you
  stay in your own room after lights out, Chloe, whatever list you happen
  to be on, because you are twelve years old."`
  **KEEP.** Closes the chapter and its title theme in one line; irreplaceable.

## Chapter 16: Thirteen

- **16_thirteen:139** — Amberg, opening his law class. `"You are citizens,
  and in two years most of you will be driving. After that you'll sign a
  lease, then a contract, then probably a marriage licence, and each of
  those is a rule somebody wrote down before you got here. So you're going
  to learn the law of your country, because at sixteen you'll take the bar.
  That's the examination this country uses to check whether a person knows
  it, and every citizen in this room ought to pass it."`
  **KEEP.** Establishes the bar exam the plot depends on in chapters 19 and
  25; appears nowhere else.

- **16_thirteen:165** — Iyad, at dinner. `"That's what it is, that's a
  registration off the system itself, sitting right in the middle of the
  thing, and everybody's been reading the ends of it, but nobody looked at
  the middle, which is where I went first. And Chloe's had it a while and
  she'll not say, because she never says until she's certain, and she's
  never certain."`
  **REWORD.** *Reword:* "And Chloe's had it a while and she'll not say. She
  never says until she's certain, and she's never certain."

## Chapter 17: Fourteen

- **17_fourteen:65** — Chloe, admitting to her own students that she taught
  them wrong. `"No. Your answers all follow from what I taught you, and
  what I taught you was wrong. You'll get a different one in two weeks and
  it'll be harder, because by then you'll actually have it."`
  **KEEP.** A real moment of professional integrity that mirrors the Marek
  thread running through the book.

- **17_fourteen:93** — Chloe, technical brainstorm on the sound array.
  `"Then hand me arrival differences and I'll hand you the place. And the
  boxes don't go along the near edge, whatever the cable wants, because
  boxes in a line give you a direction instead of a point, so we'd be fine
  down the middle and no good at all at either end."`
  **CUT.** First of five near-identical technical "because" statements from
  five different characters in one scene (93, 99, 103, 115, 121) — the
  clearest single tell in the book that the construction has become house
  voice rather than any one person's.

- **17_fourteen:99** — Kavi, same scene. `"Then the air isn't the same
  speed at both ends, and half a degree is a third of a metre a second, so
  we want the temperature at every post at the instant the sound goes,
  which is a person at every post holding a thermometer, because we are not
  building sensors as well."`
  **KEEP.** The one instance worth keeping from that cluster, for its
  specific sensory detail and Kavi's own precision.

- **17_fourteen:103** — Priya, same scene. `"You're going to set the clocks
  off a sound, though, and if you make the sound at a spot you've measured
  and slide the clocks about until the boxes agree about that spot,
  everything wrong with the boxes has gone into the clocks and you've
  written calibration on it, so it reads beautifully at that spot and lies
  everywhere else, and the staff are not going to put it where we
  calibrated, because not doing that is the whole of what they told us
  they'd do."`
  **REWORD.** The actual insight the group needs, too important to cut
  outright, but part of the same overcrowded scene. *Reword:* "You're going
  to set the clocks off a sound, though. If you make the sound at a spot
  you've measured and slide the clocks about until the boxes agree about
  that spot, everything wrong with the boxes has gone into the clocks and
  you've written calibration on it. It reads beautifully at that spot and
  lies everywhere else. The staff are not going to put it where we
  calibrated. Not doing that is the whole of what they told us they'd do."

- **17_fourteen:115** — Ruth, angry at Kavi, same scene. `"A fortnight. So
  we've been building against a number you knew was the wrong number, and
  I've spent a fortnight tuning against recordings that were never going to
  be any use, and none of that had to happen, because the whole of what it
  needed was you saying it in that room a fortnight ago."`
  **KEEP.** Interpersonal, not technical — Ruth's real anger, distinct in
  kind from the technical exposition surrounding it.

- **17_fourteen:121** — Nadia, closing the same scene. `"Then it's wire,
  and the clock goes down the wire, and Priya's problem goes away on its
  own, because nothing gets calibrated off a sound any more."`
  **CUT.** Fifth "because" in the same scene, restating the resolution the
  reader already has from 103.

- **17_fourteen:141** — Ruth, late at night, snapping at Chloe.
  `"Then it's picking the road up at all of them and I need to know that,
  and now I can't, because you've made that box different from the rest of
  them. Do your own end again, or go to bed, or go and find me something to
  eat, and leave mine alone."`
  **REWORD.** *Reword:* "Then it's picking the road up at all of them and I
  need to know that, and now I can't. You've made that box different from
  the rest of them. Do your own end again, or go to bed, or go and find me
  something to eat, and leave mine alone."

- **17_fourteen:169** — Chloe, helping Ruth debug her sound project.
  `"Play it again and let me hear the part before the note, because you
  keep starting where you think it starts."`
  **REWORD.** *Reword:* "Play it again and let me hear the part before the
  note. You keep starting where you think it starts."

## Chapter 18: Fifteen

- **18_fifteen:153** — Dr. Sandoval. `"There is a non-disclosure agreement
  on that project. Four people have signed it, and one of them is me, while
  your name is on none of it, and I would refuse to put a federal agreement
  in front of a fifteen-year-old, because asking you to sign would be wrong
  and would fail in court besides. But your work feeds ours, so if you talk
  about it at home, or on a telephone, or at a table with a dozen people
  round it, you walk away untouched and the consequences land on us
  instead."`
  **KEEP.** Irreplaceable plot information; drives Chloe's withdrawal from
  her friends for the rest of the chapter.

## Chapter 19: Sixteen

- **19_sixteen:41** — Chloe, interrupted mid-sentence. `"It's the margin,
  though, because as a share of the whole paper that's about a..."`
  **REWORD.** The joke is Bex finishing the sentence for her; doesn't need
  "because" to set up the interruption. *Reword:* "It's the margin, though.
  As a share of the whole paper that's about a..."

- **19_sixteen:57** — Amberg, the chapter's central lesson. `"They follow
  if the person reading has your head and has already done the working you
  skipped. A marker with a stack of these in front of him has about ten
  seconds a page, but that is not enough time to rebuild your reasoning for
  you, and he is also not allowed to give you a mark for something you did
  not write down, whatever you happened to be thinking while you left it
  out, because thinking it and writing it down are not the same action to a
  marker, whatever they feel like from inside your own head while you're
  doing the first and not the second."`
  **KEEP.** The essential, once-stated version of the lesson the rest of the
  chapter is built on.

- **19_sixteen:61** — Amberg, immediately after. `"I would like you to sit
  down while I say the rest, because you're going to want to argue before
  I've finished, and I'd rather you had it all first."`
  **REWORD.** Pure scene management right after the substantive lesson.
  *Reword:* "I would like you to sit down while I say the rest. You're
  going to want to argue before I've finished, and I'd rather you had it
  all first."

- **19_sixteen:81** — Kavi, marking Chloe's practice paper. `"Two out of
  four," Kavi says... "Then you've written *and so the risk sits with the
  buyer*, which is your second line in a different hat, and then you've
  stopped. The marker reads a sentence that sounds like new information,
  but finds it's what he already had. That is worse for you than leaving
  the line out, because a blank space tells him you knew where to stop and
  a repeated sentence tells him you didn't."`
  **REWORD.** Restates Amberg's lesson from earlier in the same chapter in a
  second mouth. *Reword:* "That is worse for you than leaving the line out.
  A blank space tells him you knew where to stop. A repeated sentence tells
  him you didn't."

- **19_sixteen:85** — Kavi, continuing. `"It's the same sentence to you,
  because you already know why the risk sits with the buyer. The marker has
  to be given that reasoning rather than assumed to already have it, and
  right now the page hands him a single idea wearing two coats. He can only
  mark what is actually on the paper in front of him, not the paper you'd
  have written if you'd had more room to write it."`
  **REWORD.** Fourth "because"-shaped beat on the same lesson in one
  chapter (57, 61, 81, 85). *Reword:* "It's the same sentence to you. You
  already know why the risk sits with the buyer. The marker has to be given
  that reasoning, not assumed to already have it, and right now the page
  hands him a single idea wearing two coats."

- **19_sixteen:145** — mother, checking in on Chloe's malaise. `"There's a
  shelf in the garage your father's been meaning to put up since March, and
  at this rate it'll still be leaning against the wall at Christmas. Or
  skip it entirely. I'm not asking you to put up a shelf, I'm asking
  whether you actually want to sit still this much, because that's not the
  girl who left here for that school in the first place."`
  **KEEP.** A real challenge a mother is entitled to make; resonant with the
  post-Halstead malaise this chapter is tracking.

- **19_sixteen:157** — Chloe, recounting a conversation with Sam.
  `"That's what I asked him, more or less word for word, standing right
  outside the range. He said he knows, that he does plenty of other stuff
  with its own number on it, and this is only the number for the range. He
  wasn't even annoyed that I brought it up. Then he told me to go and be
  miserable at Ruth about it, because Ruth's on ninety-one and apparently
  that's more my speed. I told him misery isn't a speed you pick, and he
  said that was exactly the kind of thing Ruth would say back to me too, so
  apparently we sound alike whenever we're annoyed at him."`
  **REWORD.** Charming, and worth mostly keeping, but the "because" sits one
  clause deep inside a long anecdote. *Reword the flagged clause only:*
  "...miserable at Ruth about it. Ruth's on ninety-one, apparently, and
  that's more my speed."

- **19_sixteen:175** — Chloe, to her father, about Priya. `"I think she
  knew straight away and let it run anyway, because stopping it right then
  would have meant explaining why in front of everybody. She'd have had to
  say out loud who she was doing it to."`
  **KEEP.** The only place in the book we learn what Priya actually did and
  why; irreplaceable character information.

## Chapter 20: The Parking Lot

- **20_the_parking_lot:21** — Ruth, about Amberg's car. `"He tells anyone
  who asks, straight out, because to him it's a dent, and a dent is the
  least interesting thing about a car. He's had that car since before any
  of us got here."`
  **REWORD.** *Reword:* "He tells anyone who asks, straight out. To him
  it's a dent, and a dent is the least interesting thing about a car."

- **20_the_parking_lot:69** — not dialogue. `They argue about it until the
  waitress comes back with the check, and Nadia has exact change out on the
  table before it lands, split to the cent, because she has been dividing
  the bill in her head since the second round of coffee.`
  **EXCLUDE.** Narration, caught only via the closing quote of an unrelated
  earlier line.

- **20_the_parking_lot:137** — Chloe, analyzing the muggers. `"If you had
  one usable skill, any skill at all, you would make money doing literally
  anything other than this. You wouldn't be standing behind a hardware
  store at two in the morning taking phones off teenagers, because that's
  the worst-paid dangerous job there is."`
  **KEEP — protected.** `passes/DO_NOT_FLAG.md` already names this passage
  as the book's clearest instance of a standing character theme
  ("Chloe literally sees them as retarded... the clearest instance in the
  book of the standing rule that these people rationalise evidence of their
  own ability rather than accept it"). This catalogue is not the place to
  touch it.

## Chapter 21: The Applications

- **21_the_applications:31** — Chloe, defending her college essay to Ruth.
  `"I know what they want. I just think the limit leaves out anything
  that's actually true, because the true part of that year is that the boy
  was right and I still never got a page out of him. That doesn't go in the
  box they gave me and it doesn't survive being remembered at lunch."`
  **KEEP.** Continues the Marek thread; Chloe defending a real choice
  against a real challenge.

- **21_the_applications:89** — an admissions officer, on the phone.
  `"Read this paragraph and tell me what you think it means. Don't tell me
  what it stands in for, because I have spent an hour deciding it has to
  stand in for something,"`
  **REWORD.** *Reword:* "Read this paragraph and tell me what you think it
  means. Don't tell me what it stands in for. I have spent an hour deciding
  it has to stand in for something."

- **21_the_applications:245** — Chloe. `"Ninety-one out of ninety-one
  bought something, and that's the number the sign should say. Nobody is
  ever going to put that in a window, because a window like that stops
  being an advertisement and starts being an accusation."`
  **KEEP.** The chapter's thematic capstone, tying back to the percentile
  theme from chapter 2; one of the best lines in the book.

- **21_the_applications:253** — Ruth, immediately after. `"It's on their
  site," Ruth says, "and it still isn't a real number all the same, because
  both of those can be true at once."`
  **CUT.** A coda that restates the same point at lower wattage right after
  245 already landed it.

## Chapter 22: The Offer

- **22_the_offer:43** — not dialogue. `She keeps going before he can
  answer it, because she has been assembling the answer since the clock on
  his desk started.`
  **EXCLUDE.** Narration bridged from the closing quote of Chloe's actual
  question two sentences earlier.

- **22_the_offer:103** — Nadia, in her exit interview. `"The afternoon
  block is unrecorded, so it's been in there since the last week of March.
  If it comes to nothing by next spring, it comes to nothing and I take
  whichever of those jobs is still open, like anybody else. That's the
  part I've checked. It's the only part I've checked, because checking the
  rest of it before there's anything to check would just be a way of not
  starting."`
  **REWORD.** Nadia's business reasoning gets a fuller, better version in
  chapter 23; trim this earlier one. *Reword:* "That's the part I've
  checked. It's the only part I've checked. Checking the rest of it before
  there's anything to check would just be a way of not starting."

- **22_the_offer:125** — Kavi, answering Chloe's direct challenge.
  `"Because what I want to do is happening in one building and I'm standing
  in it," Kavi says... "I brought them a false positive rate on Tuesday and
  the whole building had to wait to find out whether it was wrong, because
  it was still unchecked. That's a research problem, not a classroom one,
  because a classroom's whole job is already knowing."`
  **KEEP.** The book's clearest statement of the research-versus-classroom
  theme, delivered as a direct answer to a real challenge.

- **22_the_offer:161** — Chloe's father, on the phone. `"Say that whole
  thing again for me," her father says, "every part of it, from the start,
  because I want to hear it properly."`
  **REWORD.** Pure mechanical scene transition. *Reword:* "Say that whole
  thing again for me, every part of it, from the start. I want to hear it
  properly."

- **22_the_offer:163** — not dialogue. `She keeps the parts in Amberg's
  order, because the order is the only thing about it she can hand over
  intact.`
  **EXCLUDE.** Narrator describing Chloe's method, not Chloe speaking.

- **22_the_offer:171** — Chloe, answering her father's real challenge.
  `"I understand what it is, because I did the math myself before I ever
  walked into that room, and I understood it fully before I said no. I
  wrote it out on the back of the deadline list in February and I still
  have the page."`
  **KEEP.** Central to the chapter's climax; a direct answer to a real
  question about whether she understands what she's turning down.

- **22_the_offer:173** — father. `"Then explain it to me, because from
  here it looks like you turned down more money than your mother and I
  have made in any five years combined, for a reason you haven't said yet.
  Say it to me the way you said it to him in the room, word for word, and
  don't soften any part of it on my account."`
  **KEEP.** The prompt that produces Chloe's key monologue about not
  knowing whether she's good outside the ranking system; structurally
  necessary.

- **22_the_offer:183** — Chloe. `"That's not something I asked him,
  because my head was still on the room and the desk, not on whatever might
  happen years from now. I should have asked him. It didn't come into my
  head at all until you just said it."`
  **REWORD.** A nice, honest admission, but the scene's weight is carried
  by 171 and 173. *Reword:* "That's not something I asked him. My head was
  still on the room and the desk, not on whatever might happen years from
  now. I should have asked him."

- **22_the_offer:197** — mother. `"That's not what I..." her mother
  starts, then stops and starts again. "It's not your fault, and I need you
  to actually hear that, because it's a fact about a number and only that.
  There's a difference between a fact and a fault, and I want you to know
  it."`
  **REWORD.** Warm and needed, but the fifth "because" beat in one long
  scene (103, 125, 171, 173, 197). *Reword:* "It's not your fault, and I
  need you to actually hear that. It's a fact about a number and only
  that. There's a difference between a fact and a fault, and I want you to
  know it."

## Chapter 23: The First One

- **23_the_first_one:15** — not dialogue. `That sentence goes straight
  past Chloe anyway, because Sam has spent the whole speech trying to make
  her laugh and finally succeeds on that word.`
  **EXCLUDE.** Narration, caught on the quote marks around the single word
  "accomplishment" earlier in the same sentence.

- **23_the_first_one:127** — Nadia, negotiating with her father.
  `"You have them from somebody who is going to be on a freight desk in
  Ambridge in a few months, if the freight desk ever calls. You'd be paying
  for that by August. Sundays at the counter, the back room the remainder
  of the week, and an end date attached to it. If it is still earning zero
  by the last day of March I take whatever job is open and I stop, and I
  won't ask you for the counter back, because I'll have used up the year
  you gave me for it, fair and square, same as anybody who takes a chance
  and it doesn't pay off."`
  **KEEP.** A real negotiation that resolves her arc; specific and
  irreplaceable.

- **23_the_first_one:177** — father, closing the chapter. `"So the two
  years in the middle, that's a long stretch to spend just waiting on one
  date. Find something in it you'd actually want to do anyway, because
  waiting well is still waiting, and I've never met anybody who got good at
  it on purpose."`
  **KEEP.** Sets up the chapter's actual resolution; a genuinely good line
  the reader needs to get there.

## Chapter 25: Forty Targets

- **25_forty_targets:25** — not dialogue. `Okoro is shaving with the water
  off, because the water is a privilege the bay forfeited on Tuesday, with
  no immediate prospect of recovering it.`
  **EXCLUDE.** Narration following the closing quote of Okoro's actual
  line.

- **25_forty_targets:85** — Sam, choosing honesty over bragging in front of
  skeptical Army buddies. `"The board's fine, it's just got a top on it,
  and everybody who hits the top gets the same number." ... "There was a
  girl at that school called Odile. She took me apart on a mat in front of
  thirty people, put me down twice inside a minute, but then came and found
  me afterwards to apologise for it, because she reckoned she'd embarrassed
  me in front of the year."`
  **KEEP.** One of Sam's best moments; irreplaceable characterization of his
  integrity.

## Chapter 26: The Exercise

- **26_the_exercise:63** — Ives, explaining the rules violation to Sam.
  `"Every harness in that pipe was in a steady tone simultaneously, which
  makes the engagement void, because there is no soldier in there who can
  tell me who shot who. Which leaves exactly one thing that happened
  tonight, which is that you put hands on two people on an exercise that
  has no hands on it, and the tone being confusing doesn't move that rule
  an inch."`
  **KEEP.** Necessary rules exposition that sets up the AAR scene.

- **26_the_exercise:107** — the major, addressing a different soldier.
  `"You went the whole exercise untouched," he tells the second... "The
  opposing element apparently failed to locate your line of travel at any
  point in the whole exercise. That is only sometimes good news, so hold
  the compliment for later, because it might simply mean they had better
  things to do than come looking for you."`
  **CUT.** Texture establishing the major's style before he reaches Sam;
  not about a character central to the plot.

- **26_the_exercise:125** — the major, to Sam. `"You had four men, no
  room, and a tone you couldn't sort out." ... "That leaves you precisely
  one option, Marsh, but it is the opposite of the option you took, because
  the option is to be dead. That is what the tone is for. It settles the
  engagement, and it settles it before anybody has to put a hand on
  anybody, which is the entire reason the harness exists in the first
  place."`
  **KEEP.** The exercise's central lesson and one of the sharpest lines in
  Sam's arc.

## Chapter 27: Nadia

- **27_nadia:35** — Nadia, coaching a scam victim. `"Call the bank the
  minute they open and read them that number," Nadia says... "If they hand
  you a form, fill it in standing at the counter, because a form that goes
  home in a bag gets filled in never. And stop apologising to me, because
  what you did was answer a message from an employer on a site with my own
  name up on the window of it."`
  **REWORD.** Good, specific Nadia wisdom, but the chapter keeps a stronger
  instance at 125. *Reword the flagged clause:* "If they hand you a form,
  fill it in standing at the counter. A form that goes home in a bag gets
  filled in never."

- **27_nadia:125** — Nadia, confronting the scam operation. `"I'm not
  calling the police, because a county detective gets a stack of form
  submissions and a Tuesday he already had plans for. He takes the report,
  he gives me a number to ring back on, and that is the end of it. So that
  isn't a threat I've got, but I'm not going to stand in your office
  pretending I've got it, and I'm not going to waste the drive out here on
  a threat that doesn't actually work, so you can stop waiting for it to
  land."`
  **KEEP.** Real leverage-claiming under genuine danger; essential to the
  confrontation.

- **27_nadia:241** — Tomas, a minor employee. `"The ceiling was working. I
  don't go through a thing changing whatever already works, because then
  it's all mine, but none of it's theirs, and I'd rather fix the part
  that's actually broken."`
  **REWORD.** *Reword:* "The ceiling was working. I don't go through a
  thing changing whatever already works. Then it's all mine, but none of
  it's theirs, and I'd rather fix the part that's actually broken."

## Chapter 28: Nineteen

- **28_nineteen:39** — Chloe, giving a client the too-technical version.
  `"The certification's a signed statement that the translation is
  complete and accurate. It's filed on its own, and it gets redone
  entirely if a single word in the document changes afterward. The price
  is set by the job as a whole, whether the document runs a single word or
  a whole manual, because the signature is what costs money, not the paper
  it sits on."`
  **KEEP.** Deliberately sets up the chapter's whole "says everything
  twice" structure; needed exactly as written, since Deb's simplified
  version right after it is the point.

## Chapter 29: The File

- **29_the_file:77** — not dialogue. `"Fine," Theo says, and takes his
  hand down. The folder comes back up off the desk, because leaving it
  open there is worse than finishing it.`
  **EXCLUDE.** "Fine" is the whole quotation; the rest is narration.

## Chapter 30: Cleared

- **30_cleared:69** — Chloe, in her background-check interview, on Marek.
  `"Mine. He did the whole year of the work but handed none of it in, and
  getting it out of him was the job, and I never found the way to do it. He
  gave me back a stack of practice papers a year later with nothing written
  on any of them except a better question on the back of the top sheet, and
  I still don't know whether that counts as him answering me or not,
  because a better question isn't the same thing as a finished answer, and
  he handed me the question rather than the answer on purpose."`
  **KEEP.** Resolves the Marek thread across the whole book; irreplaceable.

## Chapter 31: Ruth

- **31_ruth:15** — a department office worker, at MIT. `"The sequence
  you're in is the only sequence there is. There isn't another track to be
  moved onto, not in this department and not upstairs either, and there
  has not been anything else in all the years I have worked in this
  office. I'm sorry, because I can see how much of this you did before you
  came in here, and none of it was wasted, it just wasn't going to change
  what's already been decided."`
  **KEEP.** The flat rejection that launches Ruth's arc in this chapter;
  structurally necessary.

- **31_ruth:55** — not dialogue. `"No," she says, and it's close enough to
  true, because being stuck and being wrong about the reason feel like
  different things from the inside.`
  **EXCLUDE.** "No" is the entire quotation; the rest is narrator
  commentary on Ruth's inner state.

## Chapter 33: The Other One

- **33_the_other_one:97** — not dialogue. `The line goes in twice, in
  different words each time, because she already knows which of them is
  going to be the one squinting at an ordinary blip at two in the morning
  someday, wondering if this is the real thing.`
  **EXCLUDE.** This whole passage is the narrator describing Chloe drafting
  a legal-style document; no character is speaking.

---

## The KEEP count, and where more would come from

**49 kept**, against a target of "roughly 48." Nothing here was massaged to
hit that number — it is the honest result of applying one consistent
question to every instance a second time: *does removing this clause cost the
reader information they cannot get anywhere else, or a confrontation that
actually needs it, or is this a genuinely well-written scene that happens to
share a shape with forty other scenes in the book.* Good writing lost that
test often. If the real number needs to come down further, the next places to
look, in order, are:

1. **Chapter 22's climax scene** still keeps three in a row (125, 171, 173)
   out of what was originally seven "because" beats across one extended
   exit-interview-plus-phone-call sequence. All three are strong, but three
   in one scene is still a cluster.
2. **Chapter 15's Thanksgiving argument** keeps two of three (315, 331).
3. Any of the individually-KEEP "teaching" moments that are good but not
   irreplaceable — 07:123, 10:117, 16:139, and 26:63 are functional
   exposition rather than confrontation or unique voice, and would be the
   next four to go if the target moved from 48 down toward, say, 40.

## Grouping: who carries it, and where it clusters

**Two characters carry nearly forty percent of the whole finding between
them.** Chloe's mother, Meg, accounts for **25 of the 118 real instances** —
by a wide margin the single largest share, spread across nearly every
chapter she appears in (three separate scenes in chapter 3 alone). Chloe
herself accounts for **21**. Between the two of them that is 46 of 118. No
other character comes close: Kavi is a distant third with 13, Ruth has 8,
Chloe's father has 7. If the goal is a natural-sounding cut rather than an
even shave across the whole cast, these two are where it should be found —
and Meg in particular, since a parent explaining her reasoning to a child
is the single most repeated relationship-shape carrying this construction in
the book.

**Scenes where three or more sit together**, worst first:

- **Chapter 17, the sound-array brainstorm (93, 99, 103, 115, 121):** five
  "because" statements from five different characters in one continuous
  scene — the clearest evidence in the book that this shape has become house
  voice rather than any one person's. Only one of the five (99, Kavi) is
  kept here.
- **Chapter 22, the exit-interview-and-phone-call climax (103, 125, 161,
  171, 173, 183, 197):** seven real instances across one extended sequence,
  the largest raw cluster by count in the book, though also the book's
  emotional and thematic climax; three survive this catalogue's judgment.
- **Chapter 9, the house-offer argument (129, 135, 137):** three in eight
  lines between the two parents; two survive.
- **Chapter 10, Kavi's account of Owen (121, 125, 129):** three in one
  continuous answer; one survives.
- **Chapter 15, the Thanksgiving gas-oven argument (315, 327, 331):** three
  in one family confrontation; two survive.
- **Chapter 19, the "show your work" lesson (57, 61, 81, 85):** the same
  lesson delivered by two different teachers across one chapter, four times
  in the identical shape; one survives.
- **Chapter 2, the diagnostic Q&A (235, 251, 257, 261):** four beats of Ben
  answering the mother's questions in a row; two survive.

## Totals for the report back

- **Instances the finder script located (current state of the files):** 129
  — down from 132 at the start of this task because of concurrent editing;
  see the warning at the top.
- **Real instances of the construction (script false positives excluded):**
  118
- **KEEP: 49 / CUT: 31 / REWORD: 38**
- **Three chapters carrying the most** (by real-instance count): **Chapter
  10 (April)** and **Chapter 12 (Nine)**, tied at 10 each, followed by a
  three-way tie between **Chapter 15 (Twelve)**, **Chapter 17 (Fourteen)**,
  and **Chapter 19 (Sixteen)** at 8 each.
