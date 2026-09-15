# Voice pass: chapters 27-28

Scope: `chapters/27_nadia.md`, `chapters/28_nineteen.md`. Dialogue and chat
lines untouched throughout. Word counts after the pass: 4,814 (27) and 3,426
(28), both inside the 2,000-5,000 band and each within a handful of words of
where the pass found them (4,810 and 3,424). Ran `measures/style_report.py`
on both files before and after: identical scorecards, no measure moved from
PASS to FAIL or the reverse. No new sentence opens with "She" or "He" plus a
verb (checked every rewritten sentence against this by hand, since the
measure is already at its 120/100k target and the brief said not to add to
it). Nadia's dead man's switch speech and the chat that takes it apart
(27, roughly lines 119-225) were not touched. Deb hearing Chloe out to the
end, twice (28, lines 39 and 43 — "Deb hears it out to the end." / "Deb lets
her finish.") were not touched.

## Changed

### chapters/27_nadia.md, line 21

**Before:** "...and a good week puts a handful of names in front of her."
**After:** "...and in a good week she finds a handful of names on it."
**Why:** Fake agency — "a good week" is an inanimate subject given the active
verb "puts," with nobody doing anything. Nadia is already the sentence's
real actor (she is the one reading the queue); this puts her back as the one
finding the names instead of a time period placing them for her.

### chapters/27_nadia.md, line 77

**Before:** "The agent's name is Hanley, and the address carries a stack of
his filings."
**After:** "The agent's name is Hanley, and he has filed a stack of
paperwork against that address."
**Why:** Fake agency — "the address carries" gives an inanimate subject the
work of a person. Hanley is named one clause earlier and is exactly who
matters here (rule: a specific person did it and it matters who), since the
whole investigation in this section is about tracing filings back to him.

### chapters/27_nadia.md, line 85

**Before:** "Parking is out front, where the upstairs window can see the
car, and she leaves the doors unlocked..."
**After:** "Parking is out front, where anyone upstairs can see the car, and
she leaves the doors unlocked..."
**Why:** Fake agency — a window cannot see anything; the men upstairs can.
"Anyone upstairs" keeps the doer exactly as unspecific as the original
intended (she does not know who is up there yet), while giving the seeing to
a person instead of the glass.

### chapters/27_nadia.md, line 277

**Before:** "Tomas catches it off a graph well outside anything he had ever
been asked to watch... Asked why the retry ceiling stayed where it was while
he was in there, he says..."
**After:** "Tomas catches it off a graph well outside anything Nadia had
ever asked him to watch... When Nadia asks him why the retry ceiling stayed
where it was while he was in there, he says..."
**Why:** Two instances of a person (Tomas) in the subject of a passive in
the same paragraph — "been asked" and the elliptical "[being] asked" that
opens the next sentence. Nadia is the only person in the chapter who could
plausibly set the scope of what Tomas watches or ask him to account for a
change; she is already active two sentences later ("She writes the ceiling
herself that night"), so naming her here invents nothing.

### chapters/28_nineteen.md, line 13

**Before:** "It takes her an afternoon rather than the fortnight she's been
given... mostly because the registrar told her she couldn't and then, asked
which rule said so, came back off hold with an answer that only sounded
like a rule."
**After:** "It takes her an afternoon rather than the fortnight the course
gives her... mostly because the registrar told her she couldn't and then,
when Chloe asked which rule said so, came back off hold with an answer that
only sounded like a rule."
**Why:** Two instances of a person in the subject of a passive — "she's been
given" (Chloe) and the elliptical "[the registrar, being] asked" a few
clauses later, which reverses who is doing the asking. The political history
course that set the reading is named two sentences earlier and is the actual
doer of the first; Chloe is plainly the one who asks the registrar a
question in the second, not the other way around.

### chapters/28_nineteen.md, line 25

**Before:** "...but the office has stopped testing her and started routing
the Russian and the Mandarin straight to her desk without a memo about it."
**After:** "...but Deb has stopped testing her and started routing the
Russian and the Mandarin straight to her desk without a memo about it."
**Why:** Hidden doer behind a faceless institution. This chapter is
specifically about documents moving through an office, and Deb is
established as the one who coordinates the queue of jobs coming in and sits
across from Chloe — she is who is actually routing work to Chloe's desk, not
"the office" in the abstract. Matches the brief's own flag that Deb is
"often the one actually doing the thing."

### chapters/28_nineteen.md, line 47

**Before:** "The name survives a manager asking what a Tyler rate is and
having to be told it's shorthand, not a joke..."
**After:** "The name survives a manager asking what a Tyler rate is and Deb
explaining that it's shorthand, not a joke..."
**Why:** Person (the manager) in the subject of a passive. Deb is the one
who coined and uses the name two sentences earlier, so she is the one who
would field a manager's question about it; naming her invents nothing and
keeps the office's document/office culture grounded in a person, per the
brief's steer for this chapter.

### chapters/28_nineteen.md, line 55

**Before:** "Both countries' newspapers go up in adjacent tabs before noon,
and she reads them against each other for hours..."
**After:** "Both countries' newspapers she opens in adjacent tabs before
noon, and she reads them against each other for hours..."
**Why:** Fake agency — newspapers do not open their own tabs. Fronted the
object ("Both countries' newspapers she opens...") rather than opening the
sentence with "She opens," both to keep Chloe as the actor and to avoid
adding to the book's already-capped rate of sentences opening "She/He +
verb." The fronted-object shape matches the book's own established pattern
elsewhere in these two chapters ("That queue she reads herself," "Every
posting she writes herself," "Both calls she takes standing at the desk").

### chapters/28_nineteen.md, line 55 (second sentence of the same
paragraph)

**Before:** "A short summary goes at the top for anyone who wants the
conclusion without the treaty text; she reads it back once..."
**After:** "A short summary she puts at the top for anyone who wants the
conclusion without the treaty text; she reads it back once..."
**Why:** Fake agency, same fault as the sentence above it and fixed the same
way, for the same reason (avoiding a new "She + verb" sentence opener while
keeping Chloe as the one doing it).

## Called out, not changed

### chapters/27_nadia.md, line 227

**Current:** "The site stays clean after that, and Hanley's filings all go
dead in July, all of them inside a fortnight, which she spots in August and
keeps to herself."

**Why the voice is wrong:** "Hanley's filings all go dead" gives the filings
an active verb with nobody named as the one who kills them — a candidate for
fake agency.

**Why I did not change it:** I could not tell who does it. It could be
Hanley abandoning them himself once the site he was feeding goes quiet, or
the state revoking them, or something Nadia's own complaint upstream
triggered without her hearing back about it — the text gives Nadia only the
outcome, spotted after the fact and in August, not the mechanism, and that
gap looks deliberate (she "keeps it to herself" rather than finding out).
Naming any of those doers would invent a fact the chapter does not supply.

**Replacement 1:** "The site stays clean after that, and by July all of
Hanley's filings are dead, all of them inside a fortnight, which she spots
in August and keeps to herself."
**Replacement 2:** "The site stays clean after that, and Hanley's filings
all lapse in July, all of them inside a fortnight, which she spots in
August and keeps to herself."

### chapters/28_nineteen.md, line 49

**Current:** "The policy language goes, and she reaches for the closest
thing her mother has actually paid for and lost money on, and it works
there too."

**Why the voice is wrong:** "The policy language goes" gives an abstract,
inanimate subject an active verb with no actor — a fake-agency candidate,
and Chloe is clearly the one talking to her mother.

**Why I did not change it:** I was not confident which sense of "goes" the
sentence means, and the two readings would need different fixes. It could
mean the policy explanation is delivered and lands fine (parallel to "That
lands" a few lines earlier for the Tyler-rate comparison), or it could mean
the opposite — that the first, technical attempt falls flat, which is why
she then reaches for the comparison. Guessing wrong would reverse whether
her mother understood the policy language on its own or needed the
comparison to get anywhere, and that is a fact about the scene, not just its
phrasing.

**Replacement 1:** "She gives her the policy language, and then reaches for
the closest thing her mother has actually paid for and lost money on, and
it works there too."
**Replacement 2:** "The policy language does not land, so she reaches for
the closest thing her mother has actually paid for and lost money on, and
it works there too."

## Left alone, and why

A number of constructions that look like candidates on a first pass were
left alone as deliberate, as correct under the book's own rules, or as
idiom:

- **"The thing fills the forms and sends them out for her" (27, line 7)**
  and **"It reads the requirement text off live listings, pulls down
  whatever public documentation..." (27, line 235)** — an inanimate subject
  with active verbs, but "the thing" is introduced by name in the same or
  preceding sentence as Nadia's own product, and the paragraph is
  specifically about what it does. That is topic continuity (rule 2), not
  the book's fault, which is a subject with no established referent at all.
- **"Hanley carries thirty-one filings on that address" (27, line 145)** —
  looks like the same fault as the address-carries sentence I did fix at
  line 77, but this one is inside Nadia's dialogue in the confrontation
  scene, which the brief marks untouchable regardless of voice.
- **"The hiring changes Nadia's mind" (27, line 231), "College runs
  alongside it" (28, line 13), "The blog starts in September..." (28, line
  53)** — abstract-noun subjects with active verbs, but these are the
  chapters' own recurring device for opening a new subsection, parallel to
  "The first thing is..." and "The second thing is..." a few lines later in
  27. Standard English usage for this kind of topic sentence, not a hidden
  physical doer.
- **"A good week..." aside**, the earlier "The Python set ran her a few
  minutes" (27, line 237) and "cost her a few hours a week" (28, line 13) —
  a recurring, deliberate idiom pairing a task with the time or cost it
  extracts from someone. Distinct from the "goes to Deb" fault because
  nothing is being moved or delivered; it is a stock way of describing
  effort, used consistently across both chapters.
- **"An unfiled tray gets noticed by somebody who isn't her" (28, line
  23)** — passive, but the subject is a thing (the tray), not a person, and
  the agent is named right there ("by somebody who isn't her"), which is the
  whole point of the sentence: Chloe is counting how long the anonymity
  holds.
- **The involuntary/idiom exemptions used as written**: "Deb's eyebrows go
  up" (28, line 43, involuntary reaction), "gets furious, genuinely and at
  length" (28, line 9, one of the five restored named states, not a voice
  issue at all), "the fire alarm goes off" and "the room goes quiet" (28
  line 9, 27 line 101, both "it goes quiet"-class idiom), "It comes out
  three dollars under" (27, line 167, financial idiom).

## Report

Sentences changed: 10 across the two chapters (4 in 27, 6 in 28). All ten
run the same direction: a person removed from the subject of a passive, or a
fake-agency inanimate subject given back to the person actually doing the
thing (Nadia, Tomas as the one asked, Chloe, or Deb). No active-should-be-
passive fixes were needed, and no correct existing passive was disturbed.
Two write-ups, both in the "not confident which fact I'd be inventing"
category rather than "no doer available at all."

Strongest call-out: the policy-language sentence in 28 (line 49). It sits
inside the "Chloe starts saying everything twice" set piece, right next to
two protected passages (Deb hearing her out, twice), and the two candidate
fixes do not just differ in style — they disagree about whether Chloe's
first, technical explanation worked on its own or whether the comparison was
load-bearing from the start. That is a plot-level fact about how Chloe reads
her audience, not a phrasing choice, so I left it for the author rather than
picking one.
