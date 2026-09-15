# Information structure: what decides the subject slot, the order, and the passive

My half of the brief. The other half (Celce-Murcia's own three reasons, applied
by whoever is doing the companion file) overlaps with mine at exactly one
point, the passive, so I have gone and read the same grammar they were pointed
to rather than take it on trust, and I report what it actually says even where
it repeats the other file.

## Method and how sure I am of each source

I have web access this session and used it. Where I could get the actual page
of text (a PDF that rendered as text, not an image), I quote it word for word
and say so. Where a source would not render as text for me and I am relying on
a search engine's summary of it, I say that too, plainly, next to the claim.
Nothing below is from memory alone with no check against a live source.

What I actually did, so it can be checked:

- Fetched and read as plain text: Gopen & Swan, "The Science of Scientific
  Writing," *American Scientist*, Nov-Dec 1990 (via
  gatsby.ucl.ac.uk/~pel/misc/gopen_swan.pdf, converted to text with
  `pdfminer.six` after direct fetch, since the summarizing tool choked on the
  raw PDF twice). Full text obtained, quotes below are copied out of that file.
- Fetched and read as plain text: Clark & Haviland, "Comprehension and the
  Given-New Contract," in *Discourse Production and Comprehension* (ed.
  Freedle), 1977 (via web.stanford.edu/~clark/1970s/, same method). Full text
  obtained; the scan has some OCR noise (stray periods, a few swapped
  letters) which I have not silently cleaned inside quotation marks, so a
  quote below may show it.
- Tried and failed to get readable text: Celce-Murcia & Larsen-Freeman, *The
  Grammar Book* (2nd ed., 1999), and Williams, *Style: Toward Clarity and
  Grace*. Both PDFs I found are either scanned images with no text layer or
  broke every extraction tool I had (a `cryptography` package on this machine
  is broken in a way that also blocked two other PDF libraries; I documented
  the actual error rather than guess past it). For both of these I am relying
  on search-engine summaries of the text and on other papers that quote them
  directly. I mark every claim from these two sources as **secondhand** below,
  and I would not want anyone treating my wording of them as a direct quote.
- Ferreira (1994), *Journal of Memory and Language* 33(6), on animacy and
  passive choice: same problem, PDF is a scan, so this is also **secondhand**,
  from the paper's own abstract as surfaced by search and from a second paper
  citing it. The citation itself (author, journal, volume, year) I am
  confident of; the exact wording of any specific sentence I am not quoting
  because I never saw it as text.
- Daneš (1974) on thematic progression, Prince (1981) on the given/new
  taxonomy, and Shibatani on agent defocusing: **secondhand**, from search
  summaries and citing papers, not the originals. I could not reach usable
  full text for any of the three in the time I had.

So: some of what follows is a primary-source quote I can point at, and some is
a well-attested paraphrase I could not verify against the original page. I
have kept them visibly separate rather than let the confident ones lend
borrowed confidence to the shaky ones.

---

## 1. Theme and rheme (Halliday)

**Source:** M.A.K. Halliday, *An Introduction to Functional Grammar* (1985,
later editions with Christian Matthiessen). Secondhand: I read summaries and
citing papers, not the book itself.

**What it says:** Halliday split every English clause into two parts. The
**theme** is whatever comes first, what the sentence is announced as being
about. The **rheme** is everything after it, what gets said about the theme.
"Bees disperse pollen" has *bees* as theme; "Pollen is dispersed by bees" has
*pollen* as theme. Same fact, two different announced subjects, because theme
is a position in the sentence, not a property of the thing itself.

**The test:** Read only the first constituent of the clause (usually the
grammatical subject, though not always). Ask: is this what a reader would say
the sentence is "about"? If the answer does not match what the paragraph is
actually tracking, the theme is wrong for the job even though the sentence is
grammatical.

**What it costs when broken:** The reader loses the thread of who or what a
stretch of paragraph is following. Not a comprehension failure on any single
sentence, but a fog over the paragraph as a whole: five sentences that are
each individually clear, adding up to a paragraph nobody could summarize in
one line, because the "about" kept changing without the reader being told.

**Can we measure it:** Only by hand. A script can find the grammatical subject
of every sentence. It cannot judge whether that subject is the right thing for
that sentence to be about, because that judgment needs the whole paragraph and
some sense of what the writer is tracking.

## 2. Thematic progression: constant, linear, derived (Daneš)

**Source:** František Daneš, "Functional Sentence Perspective and the
Organization of the Text," in *Papers on Functional Sentence Perspective*
(1974). Secondhand. Often wrongly credited to Halliday in casual writing about
it; Halliday supplied theme/rheme, Daneš is the one who named the patterns
below.

**What it says:** Across a paragraph, the theme of each sentence tends to
fall into one of three shapes:

- **Constant theme.** The same thing is theme, sentence after sentence. "Ruth
  sits down. She opens the folder. She reads the first page." Ruth, Ruth,
  Ruth (the pronoun standing in for her) is theme three times running.
- **Linear theme.** What was said *about* the theme (the rheme) becomes the
  next sentence's theme. "Ruth opens a folder. The folder holds a diagnostic
  test." Folder moves from rheme to theme.
- **Derived theme.** Several sentences each take their own theme, but all of
  those themes are pieces of one larger thing introduced earlier. "The exam
  has three parts. The first part is timed. The second allows a calculator.
  The third is oral." Part one, part two, part three are all derived from
  "three parts."

**The test:** Underline the theme (first main constituent) of every sentence
in a paragraph. Do they form one of the three patterns above, in some
combination? If the themes just jump around with no relation from one to the
next, the paragraph will read as disconnected even if each sentence parses
fine alone.

**What it costs when broken:** Same cost as theme/rheme generally, a fog over
the paragraph, but this gives a name to the specific shapes that avoid it,
which makes it possible to look at a paragraph and say which pattern it is
using rather than just "it flows" or "it doesn't."

**Can we measure it:** Not well by script. A script could flag paragraphs
where five consecutive sentences have five different grammatical subjects with
no repeated word between them, as a rough proxy for "no visible progression."
It would both miss real derived-theme paragraphs (which legitimately vary the
subject) and falsely flag some of them. Better as a read-through check.

## 3. The given-new contract (Haviland & Clark; Clark & Haviland)

**Source:** Susan Haviland and Herbert Clark, "What's New? Acquiring New
Information as a Process in Comprehension," *Journal of Verbal Learning and
Verbal Behavior* 13 (1974); the term itself, "the given-new contract," is
from Clark & Haviland, "Comprehension and the Given-New Contract," in
*Discourse Production and Comprehension* (1977). I read the 1977 chapter as
text (see Method above). This is one of the sources verified against the
original page.

**What it actually says**, quoted from the chapter: the speaker is expected
to construct a sentence so that "the listener has one and only direct
antecedent for any given information and that it is the intended antecedent,"
which the chapter calls the "Maxim of Antecedence." Put more plainly: a
sentence carries some information the writer expects the reader to already
know (**given**) and some the writer expects to be new (**new**). The reader's
strategy, according to the 1974 study, is to search memory for the given part
first, find where it hooks onto something already read, and only then attach
the new part to that hook. If the given part has no clear match, or matches
two different things, the hook fails and the reader has to stop and guess.

**The test:** For any sentence past the first in a passage, ask: what part of
this sentence is old, and does the reader already have exactly one thing in
memory that it points back to? If the "old" part is actually brand new to the
reader, or if it could point to two different earlier things, the contract is
broken.

**What it costs when broken:** A concrete, measured cost, this is one of the
few in this file with an actual experiment behind it. Haviland and Clark
timed readers and found they were reliably slower to read a sentence when its
given information had to be inferred rather than matched directly to
something already stated, and Clark & Haviland report that a paragraph
respecting the contract is easier to remember afterward than one that
violates it while stating the same facts. So: measurable extra reading time,
and worse recall, not just a vague sense of confusion.

**Can we measure it:** Roughly, and only for the crude cases. A script can
flag a sentence that opens with a definite noun phrase ("the report," "the
decision") that has not been mentioned in the previous few sentences, since
that is a likely broken antecedent. It cannot catch the subtler failures
(where the antecedent exists but is ambiguous between two candidates), which
need a human read.

## 4. End-focus and end-weight (Quirk, Greenbaum, Leech, Svartvik)

**Source:** Quirk, Greenbaum, Leech and Svartvik, *A Comprehensive Grammar of
the English Language* (1985). Secondhand for the exact wording, but this is
the standard citation for both terms and it is consistent across every
description I could find of it.

**What it says:** Two separate tendencies that usually point the same
direction. **End-focus**: the most important, most newsworthy piece of
information in a clause belongs at the end, because that is where English
readers expect emphasis to land by default, with no special typography
needed. **End-weight**: the longest, most complicated piece of grammar in a
sentence (a long relative clause, a heavy list) also belongs at the end,
because a reader who has to hold a long complicated phrase in their head
before reaching the verb that governs it works harder than a reader who gets
the short simple part first. Most of the time, in ordinary English, the most
important information and the heaviest phrase are the same phrase, so the two
principles reinforce each other. When they pull apart, that is when a
sentence needs a rewrite.

**The test:** Read the sentence's last main clause element out loud on its
own. Is it the thing the sentence most wants the reader to take away? Now
count words or clauses in each major constituent. Is the biggest one at the
end? Two "no" answers is a genuine end-focus/end-weight problem, not a style
preference.

**What it costs when broken:** A specific, felt cost: the reader hits the
sentence's real point in the middle, already coasting toward the period,
and has to double back once they reach the end and realize the middle
mattered more than they gave it credit for. Or the opposite: a huge,
complicated phrase lands early and the reader has to carry it, unresolved,
through the rest of the sentence before finding out what it was for.

**Can we measure it:** Yes, better than most of these. Sentence length, clause
count per constituent, and position of the longest constituent are all things
a script can compute. It cannot judge "most newsworthy," which still needs a
human, but it can flag every sentence where the longest clause is NOT the
last one, as candidates for a human to look at.

## 5. Topic position and stress position (Gopen & Swan)

**Source:** George Gopen and Judith Swan, "The Science of Scientific
Writing," *American Scientist* 78 (Nov-Dec 1990). Verified against the actual
text (see Method).

**What it actually says.** Quoting the article directly:

> "In the stress position the reader needs and expects closure and
> fulfillment; in the topic position the reader needs and expects perspective
> and context."

And on what belongs in each:

> "Readers expect a unit of discourse to be a story about whoever shows up
> first. 'Bees disperse pollen' and 'Pollen is dispersed by bees' are two
> different but equally respectable sentences about the same facts. The first
> tells us something about bees; the second tells us something about pollen.
> The passivity of the second sentence does not by itself impair its quality;
> in fact, 'Pollen is dispersed by bees' is the superior sentence if it
> appears in a paragraph that intends to tell us a continuing story about
> pollen. Pollen's story at that moment is a passive one."

This is Gopen and Swan making, in 1990, in a hard-science-writing journal, the
exact same point the functional grammarians make about the passive: the
passive is not a defect, it is what you write when the receiver of the action
is what the paragraph is actually following. Their overall rule, stated
directly:

> "Put in the topic position the old information that links backward; put in
> the stress position the new information you want the reader to emphasize."

And on what goes wrong when a writer does not do this:

> "It misleads the reader as to whose story is being told; it burdens the
> reader with new information that must be carried further into the sentence
> before it can be connected to the discussion; and it creates ambiguity as to
> which material the writer intended the reader to emphasize."

**The test:** For any sentence, ask two questions. First, whose story is the
sentence telling, meaning what has the paragraph been following, and is that
thing sitting in the topic position (the start)? Second, what is the one
piece of information this sentence most wants to land, and is that sitting in
the stress position (the end, where a reader feels a sentence come to a
close)? A sentence that puts a genuinely new fact at the front and the
already-established thing at the back has these backward.

**What it costs when broken:** Gopen and Swan's own list, quoted above:
confusion about whose story it is, new information the reader has to carry
without anywhere to put it yet, and ambiguity about what actually mattered in
the sentence. All three are real reading costs, not aesthetic ones, and this
is the closest thing in this file to a direct, checkable diagnostic a person
can run on one sentence at a time without needing the whole paragraph in
front of them the way Halliday's test does.

**Can we measure it:** Partially. A script can find the grammatical subject
(candidate topic position) and check whether its head noun or an obvious
synonym appeared in the previous sentence, as a rough proxy for "is this old
information." It is a much cruder tool than an actual read, since real
antecedents get pronominalized, referred to by description, or dropped when
genuinely obvious, all of which a keyword match will miss.

## 6. Characters as subjects, actions as verbs (Joseph Williams)

**Source:** Joseph M. Williams, *Style: Toward Clarity and Grace* (1990; later
editions as *Style: Lessons in Clarity and Grace*, with Joseph Bizup after
Williams's death). Secondhand: could not get readable text from the PDF I
found, relying on summaries and citing articles.

**What it says, as best I can report it secondhand:** Williams's core claim is
that a sentence reads as clear when its **characters** (the people or things
the sentence is actually about) sit in the **grammatical subjects**, and its
**actions** (what those characters do) sit in the **main verbs**. Prose goes
murky, in his account, when a writer pulls the action out of the verb and
buries it in a noun instead ("we conducted an investigation of the failure"
instead of "we investigated why it failed") and leaves an abstraction in the
subject slot where a person belongs. He also, separately, recommends the same
old-to-new ordering Gopen, Swan, Halliday, and Clark & Haviland all describe,
under his own label of a sentence's "topic" and its point of "emphasis."

**Where Williams disagrees with the functional-grammar side, and this
matters:** the functional grammarians (Halliday, and the Celce-Murcia/
Larsen-Freeman textbook the other half of this brief is working from) present
theme/rheme and the passive's three legitimate uses as a **description** of
how English actually works, true of good and bad writing alike, with no
inherent verdict attached to which voice a given sentence uses. A search
summary of reviews of Williams's book puts his own position as explicitly
softer than the flat "avoid the passive" rule he is sometimes remembered for:
he is reported as offering "diagnostic principles of interpretation" rather
than "draconian rules of composition," and as saying "the alternative to
blind obedience is selective observance." So the real disagreement is not as
sharp as "Williams says never use the passive, Halliday says the passive is
fine." It is narrower and still real: Williams's book is a craft manual aimed
at revision, built around a default expectation that a concrete human agent
in the subject slot is usually the stronger choice, with the passive treated
as a deliberate exception to reach for. Halliday's account has no default at
all: it simply describes which slot carries which information, with the
passive equally at home as the active whenever the receiver is what a
paragraph is tracking. In practice, on any given sentence, both would very
often reach the same verdict, since a genuinely continuous topic and a
genuinely relevant human agent frequently point at the same choice, but
Williams's framework has a thumb on the scale toward the active and toward
naming a person, in a way Halliday's does not.

**The test:** Find the main verb. Is the actual action of the sentence
expressed by that verb, or has it been smuggled into a noun ("gave
consideration to" instead of "considered")? Find the grammatical subject. Is
it a person or a live agent that the paragraph is actually about, or an
abstraction standing in for one?

**What it costs when broken:** Nominalizations (verbs turned into nouns) make
sentences longer and force extra, meaningless verbs like "make," "give," and
"conduct" to appear just to hold the noun up. The reader has to unpack the
noun back into an action before the sentence means anything, which is
measurable extra work even when the sentence is grammatical.

**Can we measure it:** The nominalization half, yes, reasonably well: a
script can flag common nominalizing suffixes (-tion, -ment, -ance, -ence)
sitting as the object of a light verb (make, give, conduct, perform, have).
The "character in the subject slot" half is the same problem as Halliday's
test above and needs a human.

## 7. Assumed familiarity: a finer given/new taxonomy (Prince)

**Source:** Ellen Prince, "Toward a Taxonomy of Given-New Information" (1981).
Secondhand.

**What it says:** Prince's complaint about Haviland & Clark's original binary
(given vs. new) is that real information is not just old-or-new, it comes in
degrees. She proposes a scale running roughly: **evoked** (mentioned
explicitly moments ago), **unused** (something the reader could reasonably be
assumed to already know, like a famous name, but that has not appeared in
this text yet), **inferrable** (not mentioned, but derivable from something
that was, "a car" implies "an engine"), down to fully **brand-new**. Treating
all of these the same, as "old" or "new," misses real differences in how much
work the reader has to do to place them.

**The test:** For a definite noun phrase the reader has not seen before ("the
engine," "the founder"), ask which category it falls into. If it is
inferrable from something on the page, it usually reads fine. If it is
brand-new dressed up as if it were old (a definite article on something with
no antecedent and no obvious inference path), that is the specific defect
Prince's finer grid catches that the coarse given/new test would call
"broken" without saying exactly why.

**What it costs when broken:** A moment of "wait, what engine?" that a coarse
given/new check would also catch, but Prince's grid explains why some
definite-noun-phrase surprises land fine (inferrable) and others do not
(brand-new).

**Can we measure it:** No, not with a script. This one genuinely needs a
human judgment call about what a reader could plausibly infer, which is
exactly the kind of world-knowledge judgment a keyword-matching tool cannot
make.

## 8. Agent defocusing across languages (Shibatani and others)

**Source:** Masayoshi Shibatani's work on the passive prototype, and later
typological work using his term "agent defocusing." Secondhand, from search
summaries and citing papers only.

**What it says:** Shibatani's claim, as reported by the papers that cite him,
is that the passive's real cross-linguistic job is not, as older grammar
taught, "promote the object to subject." It is to push the agent out of
focus, and promoting the object is just the mechanical side effect of doing
that in a language like English, which needs every finite clause to have a
subject. Languages that do not need a subject in every clause (many
verb-final and pro-drop languages) have other ways to defocus an agent
without touching subject position at all: a form that simply drops the doer,
a special "impersonal" verb ending, a construction that turns the whole
predicate into a noun phrase with no one attached to it. The point being
made, across all these different grammatical tools, is that every language
studied has *some* way to say "this happened" without naming who did it, which
suggests defocusing an unwanted or unknown agent is a real, universal
communicative need, not a quirk of English grammar or a mark of weak writing.

**The test:** Not really a sentence-level test; this is a fact about why the
passive (and its cross-linguistic cousins) exist at all, which is background
for judging function 2 of Celce-Murcia's account (agent unknown, irrelevant,
or obvious) rather than a separate diagnostic of its own.

**What it costs when broken:** Not applicable in the usual sense; this
principle argues that a language having agent-defocusing machinery is not a
cost, it is confirmation the need is real everywhere. If anything, it is
evidence against a house rule that treats every dropped agent as a problem to
be solved by finding one.

**Can we measure it:** No, this is not a per-sentence measure at all.

---

## The author's two questions

### 1. "Is animacy of the subject even a thing in the literature, or is that just me?"

**It is a real, well-documented thing, but not in the sources this project was
pointed to, and not for the reason the house rule assumes.**

None of the functional-discourse writers above, Halliday, Daneš, Clark &
Haviland, Gopen & Swan, frame the passive's rightness in terms of whether the
subject is a person or a thing. Their entire framework is about whether the
subject is the paragraph's established **topic**, full stop, regardless of
whether that topic happens to be animate. "Pollen is dispersed by bees" is
Gopen and Swan's own example of a correct passive with an inanimate subject,
and Celce-Murcia and Larsen-Freeman's own textbook example (the one search
results kept surfacing, a car that "was towed" and then "was rammed by a
truck," used across several sentences to keep the car as topic) is exactly
the same shape: object-subject, topic continuity, no claim anywhere that
animacy is the reason it works.

But animacy shows up as a real, measured effect in a different, separate body
of work: psycholinguistics of sentence production, not discourse grammar.
Fernanda Ferreira, "Choice of Passive Voice Is Affected by Verb Type and
Animacy," *Journal of Memory and Language* 33 (1994), found exactly what the
title says: speakers produce more passives when the patient (the thing the
action happens to) is animate than when it is inanimate. The finding I could
verify only secondhand (see Method) reports it as: people are more likely to
say "the man was hit by the swing" than "the scooter was hit by the swing,"
holding the rest of the sentence equal. Related work on what psycholinguists
call **accessibility** (how easily a concept comes to mind, with animacy as
one of several factors alongside definiteness and concreteness) shows the
same general pattern: whatever is more accessible to the speaker gets pulled
toward the subject slot, and animate things tend to be more accessible than
inanimate ones. Cross-linguistically this connects to what is sometimes
called an "animacy hierarchy," the well-attested tendency for animate
participants to gravitate toward subject position across many unrelated
languages.

So: yes, it is a real thing, but notice what it actually predicts. The
psycholinguistic literature says people **produce more passives, not fewer**,
when the receiver is a person. That is close to the opposite of the author's
impression that the good passives are the ones with a thing in the subject
slot. The two facts are not actually in conflict, because they are measuring
different things: Ferreira's result is about which sentences people spontaneously
generate; the author's read is about which passives, once generated, feel
right sitting inside this specific manuscript. Nothing in either literature
says an animate-subject passive reads worse in general prose. What is
happening instead is almost certainly specific to this book (see the answer to
question 2), not a fact about English.

### 2. "Is 'person-subject passive is a fault, object-subject passive is fine' a defensible rule, or one we made up that correlates with something real?"

**It is one we made up. It correlates with something real in this specific
book, but the correlation is not "animacy," it is something else, and the
rule will misfire the moment it is applied outside the pattern that produced
it.**

Here is the evidence, straight from the sample chapters, checked against the
live files:

- `chapters/13_ten_pages.md`, line 85: *"The boy she is paired with says,
  'Lucky,'"* Chloe (a person, "she") is the subject of a passive verb. It has
  never been flagged, and it should not be: the agent (whoever runs the
  paintball pairings) is exactly the kind of irrelevant, unnamed agent
  Celce-Murcia's function 2 describes, and Chloe stays topic across the whole
  paragraph. This is a textbook-correct person-subject passive, sitting
  unflagged in the actual manuscript right now.
- `chapters/26_the_exercise.md`, line 15: *"Then the card, carrying its grids
  of figures and listing the checkpoints between them in the order he is
  required to take them."* "He" (Sam) is the subject of a passive verb. Same
  story: the agent (the exercise's designers, the Army's own protocol) is
  obvious and irrelevant to name here, Sam is the topic, and the sentence is
  fine as it stands.

Both are person-subject passives. Both are correct by every source in this
file that actually addresses the passive. Neither has ever needed fixing.
Meanwhile, the fixes this project has already made elsewhere, quoted from the
project's own pass records, tell you what the rule is actually chasing:
`passes/VOICE_29_30.md` changed "he was asked, directly, what he would have
given them" to "the children asked him" because the paragraph immediately
above had already established the askers as "the children," a specific,
knowable, relevant group being erased by the passive; `passes/VOICE_25_26.md`
changed "before he is placed anywhere at all" to "before the Army places him
anywhere," which is a person-subject passive becoming an active with a named
institution, not an inanimate object, as the new subject.

Look at what the actually-fixed cases have in common that the two
left-alone cases above do not: in every fix, the missing agent was a
**specific party already on the page**, whose relationship to the person
being acted on is a live part of the scene, and the passive's job in that
sentence was not topic continuity, it was quietly removing a second person
from a scene that is fundamentally about what one person does to another.
That is not a fact about animacy. It is a fact about this particular book:
it is a novel about institutions and specific named people doing things to a
child and to each other, growing up, an Army posting him, a school asking
her, an interviewer offering her a job, and in that kind of book, a passive
that drops a nameable person doing something to another nameable person costs
the reader the exact thing the book is about. A passive that drops an
unnamed clerk stapling a form, or an unnamed pairing algorithm assigning a
paintball partner, costs nothing, because nobody in the scene cares who did
that.

The house's own current rule (person-subject passive: fault, object-subject
passive: fine) happens to point the right direction most of the time in this
book, because in a character-driven story, a "person did something to a
named person" passive usually is the kind that erases a relevant, already-
present agent, and an "object" ends up as subject more often in exactly the
paperwork-and-mechanism passages where the agent really is beside the point
(a folder, a worm, a schedule). But that is a correlation borrowed from this
book's subject matter, not a rule of English. Feed the rule a sentence like
"the boy she is paired with" and it will flag a correct sentence for no
reason. Feed it a sentence like "the report was filed" where the actual
missing filer is a specific person the scene needs the reader to notice (say,
a supervisor covering for someone), and it will wave the sentence through for
no reason, because the subject of "was filed" is an object, and the rule
never asked whether the missing agent was actually irrelevant.

**My recommendation:** replace the person/object test with the actual
Celce-Murcia test the project was pointed to in the first place: is the
missing agent unknown, irrelevant, or already obvious from context, and does
the sentence keep the paragraph's actual topic in the subject slot? That test
gives the right answer on all four examples above (both the two left alone
and the two already fixed) and it will not misfire on the cases where this
book's own genre-driven correlation runs out.

---

## Deliverable 2: findings in the eight sample chapters

I read each of the eight files individually, not concatenated. Across all
eight, the narration is, on the whole, already carrying good information
structure; this is a book that has been through many editing passes already,
and it shows here specifically. I did not pad the list to hit a number. What
follows is what I actually found, plus the two counter-examples above (not
repeated here since they are not defects).

### chapters/13_ten_pages.md, line 91, end-focus (Gopen & Swan / Quirk et al.)

**Current:** "On the Monday, with the whole floor sitting down and the
markers on the mats, it is Bex who tells Bell she has worked something out,
and then tells him what: that nobody can react to the ball, that the barrel
is a hose and what you watch is where the hose is pointed, that every marker
in this building throws at a single speed, and that the pump gives you a
count you can time, not one you wait to see, which Kavi had off the wall bars
days before anybody asked him."

**What is wrong:** The single most damaging fact in this sentence, that Kavi
had already worked out the timing days before Bex ever asked him, and is
therefore the one being written out of his own discovery, is not given its
own sentence or even its own clause. It is buried as a relative clause
hanging off the fourth item of a four-item list, the least prominent position
available. By end-focus, the reader's attention naturally lands on the last
full idea before the period; here that idea is real but it arrives already
flattened by three items of throat-clearing ahead of it, and the relative
clause structure ("which Kavi had...") reads as a footnote to the sentence
rather than its point. A reader who skims the list, which this sentence's own
shape invites, can miss that this is the chapter's actual accusation.

**Why it is not being changed here:** Judgment call, not obvious. It is
possible the burying is deliberate, matching how casually and effectively
credit gets stolen in this scene, Bex's whole method is to make the theft
sound like paperwork. If that is the intent, the fix below would work against
it. House Rule 1 does not block a fix here; this is a narration sentence, not
protected dialogue, and nothing in `DO_NOT_FLAG.md` covers this scene.

**Replacement, active:** "On the Monday, with the whole floor sitting down and
the markers on the mats, Bex tells Bell she has worked something out: that
nobody can react to the ball, that the barrel is a hose pointed at where the
ball is going, and that every marker in the building throws at the same
speed. She gives him the timing trick last, the one that lets you count the
pump instead of watching for it. It is the piece Kavi had off the wall bars,
days before anybody asked him."

**Replacement, passive:** "On the Monday, with the whole floor sitting down
and the markers on the mats, Bell is told all of it by Bex: that nobody can
react to the ball, that the barrel is a hose, that every marker in the
building throws at the same speed. The timing trick, the one that turns the
pump into a count instead of a guess, was worked out by Kavi off the wall
bars, days before Bex ever asked him."

**Replacement, third option:** "On the Monday, with the whole floor sitting
down and the markers on the mats, Bex tells Bell she has worked something
out: the barrel, the hose, the single speed. She saves the timing trick for
last. It was Kavi's, off the wall bars, days before she asked him a single
question about it."

### chapters/10_april.md, line 47, whose story is being told (Gopen & Swan)

**Current:** "The dining hall is long tables under a roof high enough to keep
the noise, so the far end of it comes back down the room with the words gone
out of it."

**What is wrong:** The subject of "comes back down the room" is "the far end
of it," a location, not the thing that is actually moving, which is sound.
Nothing about a location can "come back down" anything; this is the same
shape as the manuscript's own recurring fake-agency fault (an inanimate,
non-agentive noun phrase carrying an active verb of motion that only the
missing real actor, here the sound or the noise, could perform. It also
happens to match `HOUSE_RULES.md`'s own named pattern, comma-plus-"so"
explaining what a camera fact causes rather than just reporting it, which is
a second, independent reason this sentence is due for a look regardless of my
half of the brief. Practically: a reader has to stop, work out that "the far
end of it" cannot literally travel, and reconstruct that the sentence means
the *sound* from the far end arrives without its words intact. That
reconstruction is exactly the "misleads the reader as to whose story is being
told" cost Gopen and Swan describe.

**Why it is not being changed here:** Looks obvious rather than a judgment
call: the intended meaning (a high-ceilinged hall where a far-off voice
reaches you only as noise) survives the fix easily, nothing here looks
deliberately unclear the way the Kavi sentence above might be.

**Replacement, active:** "The dining hall is long tables under a roof high
enough to swallow the noise, so a voice from the far end reaches her only as
sound, the words gone out of it by the time it crosses the room."

**Replacement, passive:** "The dining hall is long tables under a roof high
enough to hold the noise, so by the time it is carried down the room from the
far end, the words are gone out of it."

**Replacement, third option:** "The dining hall is long tables under a high
roof that holds the noise in. From the far end, all that reaches her is
sound, no words left in it."

### chapters/18_fifteen.md, line 219, characters as subjects (Williams; secondhand source, see above)

**Current:** "In both her hands she spreads it open, where there is a burn
across the base of the thumb from March and a smaller burn in the web between
her fingers."

**What is wrong:** This is the sentence carrying the chapter's most private
information, that Chloe has been quietly hurting herself and hiding it for
months, and the grammatical subject throughout is the grandmother ("she,"
referring back to her), with Chloe present only as "her hands" and "it," an
object being examined. By Williams's own account (secondhand, flagged above),
the character whose story this actually is drops out of the subject slot at
exactly the moment the sentence matters most. This is a genuine judgment call
rather than a clean rule violation: the distancing may well be the point, the
scene is written from a controlled, unshowy remove on purpose, and Chloe
herself would not want the sentence to dwell on her hand. I am reporting it
because the principle applies cleanly, not because I am confident the current
version is wrong for the scene.

**Why it is not being changed here:** Judgment call. This reads like a
deliberate register choice (the whole scene keeps its distance from
Chloe's feelings on purpose, right down to the deflection in her own line
a few sentences later, "I'm not telling you which corridor"), and a version
that puts Chloe more squarely in the subject slot risks over-explaining a
moment the manuscript is clearly trying to underplay. No house rule
technically blocks a fix, but the "named states" rule (Rule 1) is adjacent
here: a version that makes Chloe more clearly the subject could tip into
naming what she feels about the scars, which would need to spend one of the
five permitted named-state uses, and it has not been.

**Replacement, active:** "She spreads Chloe's hand open in both of hers, a
burn across the base of the thumb from March, a smaller one in the web
between her fingers."

**Replacement, passive:** No workable passive version exists here without
either naming an agent that was never established (who burned her, how) or
producing an even more distancing sentence than the current one, which is
already the direction I think this sentence should not go further in. I am
not writing one rather than force a bad option onto the page.

**Replacement, third option:** "Her hand goes still while her grandmother
spreads it open: a burn across the base of the thumb from March, a smaller
one in the web between her fingers."

### chapters/22_the_offer.md, line 209, end-weight, inside protected dialogue

**Current:** "You turned it down and left whether it's still on the table
later completely unasked."

**What is wrong:** The direct object is a full embedded clause ("whether
it's still on the table later"), and its complement ("unasked") is stranded
at the very end of the sentence, three words and a full clause away from the
verb it completes ("left... unasked"). By end-weight, the heaviest
constituent belongs at the end, which this sentence does follow, but the
specific problem here is that the light, meaning-bearing word "unasked"
should be reunited with "left" for the sentence to parse on a first read;
as written, a reader has to hold "left whether it's still on the table
later" as an open question before "unasked" arrives to close it, which
reads as a stumble rather than a deliberate build. This is the father's
dialogue in a tense phone call, a register where a person might genuinely
construct an awkward sentence on the fly, which is exactly why it is
reported rather than treated as a plain defect.

**Why it is not being changed here:** Blocked by convention, not by a
written house rule I could find in `HOUSE_RULES.md` or `DO_NOT_FLAG.md`
naming dialogue outright, but every existing pass in this project's history
(`passes/AGENCY_27_36.md` and others) treats quoted, attributed dialogue as
off limits for line-level rewriting, on the reasoning that real speech is not
built to satisfy written information-structure rules and a character's
occasional stumble is often the character, not a defect. I am reporting this
one anyway per the brief's instruction to surface what our own conventions
are protecting, since the sentence genuinely does what it looks like it
does: it is momentarily hard to parse.

**Replacement, active:** "You turned it down and left whether it's still on
the table for later completely unasked." is what would fix the order, but a
more natural spoken version:  "You turned it down and never even asked
whether it's still on the table."

**Replacement, passive:** "You turned it down, and whether it's still on the
table later was never asked."

**Replacement, third option:** "You turned it down. Whether it's still on
the table later, you never asked."
