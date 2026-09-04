# Sentence-level clarity and cohesion: the rules nobody named

Scope: everything about sentence-level clarity and cohesion that is not the
active/passive question. That question has its own file; where a finding
below overlaps with fake agency (an inanimate or abstract noun doing a
person's job), I say so and leave the fix to that side, because that ground
is already covered by the AGENCY and VOICE passes in this folder.

**Web access confirmed.** Every source below was actually searched for and,
where the page allowed it, fetched. Search queries are given so the work can
be checked. Two sources could not be fetched directly (a paywalled journal
page returned 403, one PDF returned 503); where that happened I say so and
report only what the search results themselves state, not what I inferred
the paper must say.

Read `halstead/CLAUDE.md`, `halstead/passes/HOUSE_RULES.md`, and
`halstead/passes/DO_NOT_FLAG.md` before this file. Nothing here overrides
those. No chapter file was edited to produce this report.

---

## 1. Nominalization

**Name:** Nominalization (turning a verb into a noun: *decide* into
*decision*, *assume* into *assumption*).

**Source:** Joseph M. Williams, *Style: Toward Clarity and Grace* (University
of Chicago Press, 1981; later editions as *Style: Lessons in Clarity and
Grace*, with Joseph Bizup). Searched "Joseph Williams nominalization style
toward clarity and grace zombie nouns" and "Joseph Williams fake agency
nominalization character agent style." Williams also coined the related test
that "characters" (real people or things) should be the grammatical subjects
of sentences and their "actions" should be the verbs; a companion term,
"zombie nouns," was coined later by Helen Sword in a 2012 *New York Times*
piece and in her book *Stylish Academic Writing* (2012), and is not
Williams's own term, though it describes the same thing.

**What it actually says:** When a sentence buries an action inside a noun
("her assumption is," "a decision was made," "the discussion of the
problem") instead of putting that action in a verb ("she assumes," "she
decided," "they discussed the problem"), the reader has to work to find out
who is doing what. Williams's own qualification matters: nominalizations
are not always bad. He lists real exceptions: when the nominalization
refers back to an idea already stated in a previous sentence, when it
replaces an awkward "the fact that," when it names the object of a verb, or
when the concept is so familiar to the reader that it functions as a
character in its own right (his example is "the war"). The rule is a
tendency to prefer verbs, not a ban on nouns ending in -tion, -ment, -ance,
-ity.

**Relationship to "fake agency":** these are close but not the same defect,
and the difference is worth being exact about, since the brief asked for it.
Fake agency, as this project has been using the term, is a *subject* problem:
an inanimate or abstract noun (a rule, an answer, a pen) is given a verb only
a person can do, while the real person who did it disappears from the
sentence. Nominalization is a *predicate* problem: the action itself is
turned into a noun, which frequently (not always) then requires some fake or
empty verb to carry it ("makes a decision," "the discussion of it happens"),
and it is that empty verb slot that then invites a fake or vague subject to
fill it. In other words: nominalization is very often what *creates room*
for fake agency to move in. Williams says exactly this: he lists "who did
what" as the underlying question and shows that clearing the nominalization
usually restores the real actor automatically. So the two are stages of the
same failure, not duplicates of each other: fix the nominalization, and the
fake-agency problem in that sentence often disappears on its own, because
there is no longer an empty verb needing a subject.

**The test:** find the main clause. Is there a noun in it ending in -tion,
-ment, -ance, -ence, -ity, or a bare gerund, that is standing in for an
action a specific person or thing actually performs in the scene? Try
rewriting the sentence with that person as the subject and the buried action
restored as the verb. If the rewrite is shorter, names an actor the original
left vague, and loses nothing, the original was a nominalization problem. If
the nominalization refers back to something already named, or names a
concept the reader already treats as a fixture (Williams's "the war" case),
leave it.

**What it costs when broken:** the reader has to do a small extra inference
to recover who is doing what, sentence by sentend. In an isolated sentence
this cost is genuinely small (this is a "very little" case much of the
time, and the honest answer is that most of this manuscript's problems in
this territory are not nominalization; it's a clean, fast-moving,
present-tense book that doesn't nominalize much to begin with). The cost
gets real when nominalizations cluster in a paragraph and the reader loses
track of whose thoughts they're inside.

**Can we measure it:** partially. A script can flag candidate words (a
dictionary of common nominalizing suffixes: -tion, -sion, -ment, -ance,
-ence, -ity, -ness used with an abstract sense) and report a rate per 1,000
words, the way `style_report.py` already does for conjunctions. It cannot
tell you which hits are Williams's legitimate exceptions (backward
reference, familiar concept, avoiding "the fact that") without a human
reading each one; a raw count would produce a lot of noise. Worth adding as
a triage list (flagged, read every hit), not a verdict, the same way the
existing "so/because tail" tic is handled.

**Conflicts with house rules:** none directly. It sits comfortably next to
Rule 7 (Sonnet, avoid over-literary prose), if anything: nominalization is
usually the *more* formal, more Latinate choice, so cutting it tends to move
a sentence toward ninth-grade register, not away from it. No conflict found.

---

## 2. Subject-verb separation (long-distance dependency)

**Name:** subject-verb separation, or, in the psycholinguistic literature,
a long-distance (or long-locality) syntactic dependency.

**Source:** Edward Gibson, "The Dependency Locality Theory: A
Distance-Based Theory of Linguistic Complexity" (in *Image, Language,
Brain*, MIT Press, 2000), and Gibson's earlier "Linguistic Complexity:
Locality of Syntactic Dependencies" (*Cognition*, 1998). Searched
"subject-verb separation long noun phrase interruption reading comprehension
processing cost linguistics" and "Gibson 2000 Dependency Locality Theory."

**What it actually says:** the further apart two words are that depend on
each other grammatically (most importantly, a subject and its verb), the
harder the sentence is to hold in working memory while reading it. Gibson's
theory gives this a name (Dependency Locality Theory, or DLT) and ties it to
a measurable cost: every word inserted between a subject and its verb, if
that word introduces a new discourse referent (a new noun that has to be
tracked), adds a small memory cost that the reader pays while waiting for
the verb to arrive. This is not folk wisdom about "short sentences good,
long sentences bad." A long sentence with the subject and verb adjacent, and
the length carried instead in what comes after the verb, is cheap. A short
sentence that shoves a relative clause between subject and verb is not.

**The test:** find the sentence's grammatical subject and its main verb.
Count the words between them. If that gap contains a full relative clause
with its own subject and verb (not just an adjective or two), the sentence
is a candidate. Then ask: does the inserted material introduce a new
character or object the reader has to track before getting back to the main
verb? If yes, that is the expensive case Gibson's theory predicts; if the
insert is short or only restates something already active in the sentence,
the cost is minor.

**What it costs when broken:** the reader has to hold the subject in
suspension, sometimes has to backtrack to it once the verb finally lands,
and in the worst cases loses the thread of who the sentence is even about.
For a book whose Fifteen-through-adult chapters are meant to be reading
harder than the child chapters, a little of this is fine and even a mark of
maturity; too much of it in the ages-6-through-12 chapters would work
directly against the reading-grade bands in `HOUSE_RULES.md`.

**Can we measure it:** yes, approximately, with a script. Parse each
sentence for its first finite verb and its subject noun phrase (a
crude heuristic: main-clause subject is usually the first noun phrase before
the first verb not inside a subordinate clause), count intervening words,
and flag anything over a threshold (worth calibrating against the corpus
the other measures already use, the same way `tics.py` calibrates against
23 books). A syntactic parser would do this properly; a decent regex
heuristic would catch the worst offenders even without one.

**Conflicts with house rules:** none found. If anything this measure would
help enforce the reading-grade bands more precisely than sentence length
alone does, since `prose_grade.py` presumably measures length, not the shape
of where the length sits inside the sentence.

---

## 3. Dangling and misplaced modifiers (including the participial opener)

**Name:** dangling modifier and misplaced modifier. Related but distinct:
a dangling modifier's implied subject is not present anywhere in the
sentence; a misplaced modifier's intended subject is present but the
modifier has drifted next to the wrong noun.

**Source:** standard composition grammar, sourced here via Purdue OWL,
"Dangling Modifiers and How To Correct Them," and the *Wikipedia* article
"Dangling modifier" (both consistent with each other and with every college
handbook that covers this). Searched "dangling modifier misplaced modifier
participial phrase opener grammar rule definition."

**What it actually says:** an introductory participial phrase ("Walking
into the room," "Having finished the essay,") is grammatically required to
describe the subject of the very next clause. If that subject is not the
one doing the walking or finishing, the sentence is broken even though every
word in it is spelled correctly and the syntax parses: "Walking into the
room, the smell was overpowering" makes the smell do the walking. A
misplaced modifier is the same failure without the dangle: the modifying
phrase or clause is simply sitting next to the wrong noun.

**Why this book specifically needs the check, per the brief:** the
participial opener ("Verb-ing, [subject] [verb]...") is a common way to
dodge a *different* measured tic (the "sentence opens She/He + verb" count
mentioned in `CLAUDE.md`, whose target is 120 per 100,000 words). Swapping
"She pushed the drawer shut and said" for "Pushing the drawer shut, she
said" lowers the She-plus-verb count but is only safe if the person doing the
pushing is, in fact, the subject of the very next clause. This is exactly
the kind of thing `CLAUDE.md` warns a pass can do without anyone measuring
the side effect it created.

**The test:** find the introductory participial phrase (or any modifying
phrase not glued directly to a noun). Ask: who or what is performing the
action named by the participle? Now find the grammatical subject of the
main clause. Are they the same? If not, the sentence dangles. If they are
the same but a different noun sits physically closer to the modifier and
could be misread as its target, the sentence is misplaced rather than
dangling, and the fix is usually to move the phrase, not rewrite it.

**What it costs when broken:** at its worst (the smell walking into the
room) it produces unintentional comedy and a genuine parsing failure the
reader has to solve by guessing. At its mildest, when context makes the
intended subject obvious anyway, the cost is close to nothing, which is
worth saying plainly since not every technically dangling modifier actually
confuses a reader.

**Can we measure it:** partially, with real limits. A script can flag every
sentence that opens with a present participle or "Having + past participle"
and diff the participle's likely subject (usually the first noun after the
comma) against context, but confirming an actual dangle requires reading the
sentence, since the check is semantic (who did the action) not syntactic. A
script can report the count of participial openers as a rate (the way
`tics.py` already tracks a set of surface constructions) so a spike is
visible even without full disambiguation.

**Conflicts with house rules:** watch this against Rule 1 (never talk to
the reader). The specific failure mode Deliverable's finding below shows
is a participial or absolute phrase used to tack an explanatory fact onto
the end of a sentence, in a shape that is functionally the same move the
"trailing explanatory clause" rule already bans, just built out of a
different part of speech so the tic-scanner's regex does not catch it.
That is not a new principle so much as a warning that the trailing-clause
rule can be dodged by construction rather than fixed, and the scanner should
not be trusted as the last word.

---

## 4. Parallelism in coordination and lists

**Name:** parallel structure (parallelism).

**Source:** William Strunk Jr., *The Elements of Style* (1918; the
Strunk-White edition, Macmillan, 1959, restates it as "Rule 15: Express
coordinate ideas in similar form"). Searched "parallelism parallel structure
grammar rule coordination lists Strunk White." This one really is as old
and as settled as a rule gets in this territory; every college writing
center handbook restates it without disagreement.

**What it actually says:** when two or more items are joined by *and*,
*or*, or set out in a list, they should share the same grammatical shape.
"She likes hiking, to swim, and reading" breaks it (gerund, infinitive,
gerund); "She likes hiking, swimming, and reading" does not. The reasoning
Strunk gives is about the reader's parsing effort, not decoration: "the
likeness of form enables the reader to recognize more readily the likeness
of content and function." Mismatched form makes the reader briefly wonder
whether the mismatch means something.

**The test:** find the coordinated items (joined by *and*/*or*, or set off
by commas in a list after a colon). Reduce each to its grammatical core: is
it a noun, a gerund phrase, a finite clause, an adjective, a participial
phrase? If the list mixes forms with no reason for the mismatch, it fails.
The exception, and it matters for this book specifically: `DO_NOT_FLAG.md`
protects "the lists" (accumulating "and X, and Y, and Z" runs) as a
deliberate reader-facing device. A mismatched list built for rhythm on
purpose, in the voice of a specific narrator or speaker, is not what this
rule is for; the rule is for the unintentional mismatch that just reads as
sloppy rather than deliberate.

**What it costs when broken:** small on its own, real in aggregate. A
single mismatched pair rarely stops a reader. A list that starts in one
grammatical shape and drifts partway through into another reads as a
stumble, and in dialogue it can read as the character losing their own
train of thought, which is sometimes exactly right (characters do that) and
sometimes just an editing miss.

**Can we measure it:** hard to automate well. A script could flag
coordinated items after "and" that differ in obvious surface form (one item
ending in -ing, the next not), but real parallelism checking needs a parser
to know each item's grammatical role, which this project's tooling does not
have. Best treated as a human-read category, the way `verify_citations.py`
and the character-sheet checks already are.

**Conflicts with house rules:** none. It sits well next to the lists
exception already written into `DO_NOT_FLAG.md`; that document already gets
the distinction right (a deliberate rhythmic list is not a parallelism bug),
which this principle should defer to rather than override.

---

## 5. Existential "there is / there are"

**Name:** existential *there*, sometimes called dummy or expletive
*there*.

**Source:** Thomas N. Huckin and Linda Hutz Pesante, "Existential There,"
*Written Communication*, Vol. 5, No. 3 (1988), pp. 368-391. Searched
"existential there is there are when justified linguistics functional
grammar"; the SAGE journal page for the article itself returned an HTTP 403
when fetched directly (subscription wall), so what follows is drawn from
the search-result abstract and citation record, not from the full text; I
flag this explicitly rather than guess at their examples.

**What it actually says, per the available abstract:** *there* as a dummy
subject is not automatically weak writing, contrary to what most
composition handbooks teach students by rote ("never start a sentence with
there is"). Huckin and Pesante's argument, confirmed independently by
several handbook summaries in the same search, is that existential *there*
earns its place when a sentence needs to (a) assert that something exists,
(b) introduce a new topic or character into the discourse for the first
time, or (c) summarize a quantity or a state of affairs, all of which put
genuinely new information into the sentence. It fails when it is used out
of habit, in a sentence that could instead put the real subject (something
already active in the discourse) into the subject slot where the reader
expects the topic to be.

**The test:** find the noun phrase that follows "there is / there are."
Ask: is this the first time this noun has come up in the passage (or is it
new information the sentence exists to introduce)? If yes, existential
*there* is doing real work: it holds the subject slot open for something
the sentence is about to introduce, which is exactly what the slot is for
when there is no established topic yet to put there instead. If the noun
was already active a sentence or two earlier, and the sentence is really
about *that* noun doing or being something, *there is/are* has displaced
the real subject for no reason, and the sentence should be rewritten with
the real noun in front.

**What it costs when broken:** a wasted subject position, one sentence at a
time. On its own this is a small cost: English readers are used to
existential *there* and it rarely causes a comprehension failure. It
becomes worth noticing only when several such sentences cluster and the
paragraph keeps declining to put an actual character in the subject slot
where the reader expects one.

**Can we measure it:** yes, easily, as a rate. A script can count "there
is/are/was/were" per 1,000 words the way `style_report.py` counts
conjunctions, and report a corpus range the same way it already does for
*and*/*but*/*so*/*because*/*which*. It cannot automatically tell you which
instances are earning their place (new information) versus which are lazy
(displaced known information) without a human read, so the number should be
a rate to watch, not a verdict on its own, in the same "triage, not verdict"
spirit `style_report.py` already uses for its "so/because tail" tic.

**Finding from the eight sample chapters:** worth reporting as a clean
result rather than a violation. Every existential-*there* sentence found in
`04_pluto.md`, `10_april.md`, `13_ten_pages.md`, `26_the_exercise.md`, and
`31_ruth.md` was introducing a genuinely new noun into the scene (a first
mention of parents, license plates, fruit in bowls, a corkboard, a dormant
tone, professors she likes). None displaced an already-active subject. This
is the honest "costs very little, and isn't currently broken" case the
brief asked for: it did not need fixing in these eight chapters, but it is
worth watching as a rate going forward, since it is an easy habit to slip
into during a fast prose pass.

**Conflicts with house rules:** none found.

---

## 6. Cleft and pseudo-cleft sentences

**Name:** cleft sentence ("It was X who...") and pseudo-cleft, also called
wh-cleft ("What she did was...").

**Source:** Ellen F. Prince, "A Comparison of Wh-Clefts and It-Clefts in
Discourse," *Language*, Vol. 54, No. 4 (1978), pp. 883-906, and the general
survey in the *Wikipedia* article "Cleft sentence," which itself cites
Knud Lambrecht's *Information Structure and Sentence Form* (Cambridge
University Press, 1994) as the standard modern reference. Searched "cleft
sentence pseudo-cleft it was X who what she did was function information
structure focus" and fetched the *Wikipedia* summary directly.

**What it actually says:** a cleft sentence splits ("clefts") one simple
sentence into two clauses specifically to put a spotlight on one piece of
it. "Bex told Bell" becomes "It was Bex who told Bell" to put emphasis and,
often, contrast on *Bex specifically, and not someone else*, on the fact
being told. A pseudo-cleft does the reverse ordering: "What Bex did was
tell Bell," putting the given, already-known part first ("what Bex did")
and the new, focused information last ("tell Bell"). Prince's specific,
sourced finding is that the two are not interchangeable the way older
grammars assumed: wh-clefts present the presupposed clause as something the
reader is already thinking about, while it-clefts do not carry that same
requirement. In practice: it-clefts are for contrast ("it was Bex, not
someone else, who..."), and wh-clefts are for delivering a punchline the
setup has been building toward.

**The test:** find any sentence built on "It was/is [X] who/that..." or
"What [X] did/was... [is/was]...". Ask what the cleft is doing that the
plain sentence would not. If removing the cleft (rewriting as a simple
subject-verb-object sentence) loses a real contrast or a real emphasis the
scene needs, the cleft is earning its place. If the plain sentence reads
exactly the same and nothing is lost, the cleft is empty decoration, adding
two extra words ("it was," "what... was") for nothing.

**What it costs when broken:** very little on a single instance, since a
cleft is rarely actually confusing, only sometimes unnecessary. The real
cost, if the device is overused, is the opposite of the book's plain style:
every cleft signals "pay special attention to this part," and a narrator
that does that too often stops being able to signal it at all.

**Finding from the eight sample chapters:** this device is rare in the
sample and, where it appears, it is doing exactly the job Prince describes.
`13_ten_pages.md`, line 91: "it is Bex who tells Bell she has worked
something out" is an it-cleft used for real contrast: Bex is publicly
credited with a discovery that the same chapter has just shown belongs to
Chloe and Ruth. The cleft's emphasis on *Bex specifically* is doing real
work; it is the grammatical shape of the unfairness the scene is about. Not
a violation, reported here because it is the closest thing to a clean,
correct example this territory produced in the sample, and the author asked
what these devices are actually for.

**Can we measure it:** yes, mechanically, as a count (search for the
"it (is|was) .{1,40} (who|that|which)" and "what .{1,40} (is|was|did)"
patterns), but whether a given hit is earning its place is a judgment call
a script cannot make; report the rate, read every hit.

**Conflicts with house rules:** none found.

---

## 7. Pronoun reference: ambiguous antecedents

**Name:** ambiguous pronoun reference (a pronoun with two or more equally
plausible antecedents), as distinct from vague or broad reference (a pronoun
that points at a whole idea rather than any single noun, covered under
principle 11 below).

**Source:** two threads, both checked. First, the standard composition-
handbook account (Purdue OWL and equivalent university writing-center pages,
all consistent): "Jane told Ruth that her roommate is a nightmare" is
ambiguous because *her* could be either woman, and the fix is to repeat the
name rather than trust the pronoun. Second, and more precisely diagnostic
for why the mistake happens even to a careful writer: Barbara J. Grosz,
Aravind K. Joshi, and Scott Weinstein, "Centering: A Framework for Modeling
the Local Coherence of Discourse," *Computational Linguistics*, Vol. 21,
No. 2 (1995), pp. 203-225. Searched "ambiguous pronoun reference two
possible antecedents same gender editing rule test" and "Grosz Joshi
Weinstein 1995 Centering local coherence discourse pronoun preferred
antecedent."

**What it actually says:** the handbook rule is the simple case: two people
of the same gender named near each other, then a pronoun that could belong
to either. Centering theory explains the mechanism underneath it: readers
do not check every possible antecedent equally; they have a strong,
automatic preference for whichever noun phrase was most recently the
grammatical subject (the discourse's current "center"). This means an
ambiguous pronoun is not equally ambiguous in both directions: a reader's
first guess defaults to whichever woman was the subject of the clause just
before the pronoun, correct or not. A writer who knows who they mean can
still produce a sentence that hands the reader the wrong first guess,
because the writer isn't reading the sentence cold.

**The test:** find every pronoun with a possible antecedent of the same
grammatical gender within the previous sentence or two. List every
candidate antecedent. If there is more than one, check which was most
recently the grammatical subject; that is the reading a first-time reader
will reach for automatically, per Centering theory. If that automatic
reading is the wrong one, the sentence is broken regardless of whether the
intended meaning is recoverable from broader context, because the recovery
costs the reader a re-read.

**What it costs when broken:** a re-read, at minimum, the moment the
sentence's real referent turns out to contradict the reader's first,
automatic guess. In a fast-moving present-tense narration switching between
characters quickly, this is a real and recurring risk, not a theoretical
one; the brief notes the project has already found one instance.

**Can we measure it:** partially. A script can flag any sentence with two
or more same-gender third-person pronouns and two or more same-gender named
characters in the surrounding two sentences, as a rate to read, the same
"triage, not verdict" pattern used elsewhere. It cannot resolve the
ambiguity itself; that needs a human reading the sentence cold, the way an
actual first-time reader would.

**Conflicts with house rules:** none. If anything this is squarely inside
what Rule 1 (never talk to the reader) is trying to protect: the fix here
is never to add an explanation, only to swap a pronoun for the name it
should have been, which costs nothing in register or tone.

---

## 8. Lexical cohesion: repetition, synonym chains, and elegant variation

**Name:** lexical cohesion (Halliday and Hasan's term for how vocabulary
choices tie a text together), and, for the specific mistake of avoiding a
repeated word, elegant variation (Fowler's term, used pejoratively).

**Source:** M. A. K. Halliday and Ruqaiya Hasan, *Cohesion in English*
(Longman, 1976), which set out five types of cohesive tie in English, one
of them lexical cohesion (repetition, synonymy, and the like); and H. W.
Fowler and F. G. Fowler, *The King's English* (1906), with Fowler's later
solo *A Dictionary of Modern English Usage* (1926) restating the same
warning under the heading "elegant variation." Searched "Halliday Hasan
cohesion in English 1976 lexical cohesion reiteration synonym repetition"
and "Fowler elegant variation Modern English Usage avoid synonym
repetition definition."

**What it actually says:** Halliday and Hasan's descriptive claim is that
repeating the same word, using a synonym, or using a more general word
("reiteration by superordinate," their term: "dog" reiterated later as
"the animal") are all legitimate ways prose ties itself together across
sentences, and repetition of the exact word is one of the strongest ties
available, not a failure to be edited out. Fowler's prescriptive claim,
about eighty years earlier and independently well known, targets the
specific bad habit this creates when writers get nervous about repeating a
word: swapping in a near-synonym purely to avoid saying the same word twice,
even when the synonym introduces a distinction the sentence does not need.
Fowler's own words: variation should happen "only when there is some
awkwardness, such as ambiguity or noticeable monotony, in the word
avoided," and he calls unforced variation "few literary faults so
prevalent." The two sources agree completely: repeating a word on purpose
is a cohesive device, not a defect, and reaching for a synonym out of
nervousness about repetition is very often the actual defect.

**The test:** find a word repeated within a short span (a paragraph, a
scene). Ask why it was repeated: is it naming the same specific thing each
time (a fine, deliberate tie), or does a synonym appear nearby clearly
standing in for it out of a fear of saying the word twice? A telltale sign
of the second case: the synonym is slightly wrong for the register, slightly
more formal or more precise than the plain word it is replacing, purely
because it had to be a different word.

**What it costs when broken:** when a repeated word is wrongly swapped for
a synonym, the reader briefly wonders whether the different word signals a
different thing (is the "folder" now a "dossier" because it changed, or
just because the writer got bored of "folder"?). This is a real cost, small
per instance, and it directly explains something this project has already
learned the hard way: the brief notes three agents have already been
"burned" making exactly this mistake, presumably by treating a repeated
word as an error to be fixed rather than a tie to be respected.

**Can we measure it:** a script can flag near-synonym pairs appearing close
together (this needs a small thesaurus, or a check against the book's own
`word_frequency.json`, which already exists in this repo, for a word whose
frequency drops sharply right where a plausible synonym's frequency rises in
the same scene) but distinguishing a deliberate repetition from a
nervous-synonym-swap is a judgment call, not a mechanical one. Best used as
a checklist item during review rather than a script.

**Conflicts with house rules:** direct and important. `HOUSE_RULES.md`
does not currently say anything about this, but should, given how often it
has already cost the project agent-hours: any future instruction to "vary
the language" or "avoid repeating X" needs this principle attached as a
condition, specifically that repetition of a plain word is very often
correct and should not be treated as a defect on sight.

---

## 9. Tense and aspect consistency in present-tense narration with past backstory

**Name:** no single term in the literature covers exactly this combination;
the underlying mechanism is Hans Reichenbach's three-point tense theory.

**Source:** Hans Reichenbach, *Elements of Symbolic Logic* (Macmillan,
1947), chapter on tense, as summarized on Glottopedia and in Susanne
Hackmack's application paper, "Reichenbach's Theory of Tense and Its
Application to English." Searched "Reichenbach 1947 tense theory point of
speech point of reference point of event" and "present tense narration past
tense backstory consistency fiction craft verb tense flashback rule" (the
second search returned craft-guide consensus rather than an academic
source; flagged as such below).

**What it actually says, academically:** every tensed clause fixes three
points in time relative to each other: S (speech time, when the sentence is
uttered, which for a narrator is "now" in the fiction), E (event time, when
the described action happens), and R (reference time, the vantage point the
sentence is describing E from). Present tense sets R and S together (the
narration's vantage point is its own "now"). A past-tense clause inside
present-tense narration sets E before R (an event finished before the
vantage point being described), which is exactly what backstory needs to
signal. This is not a stylistic opinion; it is the actual grammatical
machinery that lets a reader track "this happened before now" without being
told so directly. The craft-guide consensus (Reedsy, WritersRumpus, and
similar sites, none of them an academic source, searched separately and
flagged as craft opinion rather than research) agrees on the practical
upshot: pick a tense for "now," use past tense (or past perfect for a
flashback-within-a-flashback) for anything before it, and never drift
between the two inside the same "now" without a signal (a scene break, a
clear time marker) that a shift is happening.

**The test:** find the narration's "now" tense (this book's is present).
For every clause describing something that happened before the scene's
current moment, check it is in past tense (or past perfect, if it needs to
be further back than an adjacent past-tense clause). Check the reverse too:
no clause describing something happening in the story's actual present
moment should drift into past tense without a scene break signaling the
jump.

**What it costs when broken:** real disorientation, because tense is one of
very few signals a present-tense narration has for "this already happened"
versus "this is happening now." An accidental slip reads as a continuity
error even when the underlying facts are fine.

**Finding from the eight sample chapters:** clean. Every present/past
transition checked across all eight chapters (camp backstory in
`04_pluto.md`; the counted arrival numbers and Owen's departure in
`10_april.md`; Hearn's essay history in `13_ten_pages.md`; the swimming
teacher's Olympics history in `18_fifteen.md`; Ruth's yearlong private
diagnosis in `31_ruth.md`) signals its shift correctly, either with an
explicit time marker ("that first fall," "since March") or with present
perfect used exactly where Reichenbach's theory predicts it belongs (an
event completed before now, with continuing relevance to now). This is
another honest "not currently broken here" result. Worth keeping the check
in the toolkit anyway, since a pass that speeds up prose by chopping
sentences (the kind `CLAUDE.md` already warns caused a different regression)
is exactly the kind of pass that could introduce a tense slip without
anyone noticing until a reader does.

**Can we measure it:** partially, with a part-of-speech tagger identifying
verb tense per clause and flagging tense changes not adjacent to a time
marker or scene break; without a tagger already in this project's toolkit,
this would be new infrastructure, not a quick script.

**Conflicts with house rules:** none found.

---

## 10. Definiteness: "the" on first mention

**Name:** definiteness, specifically the familiarity theory of the
definite article, and Clark and Haviland's given-new contract for how a
reader processes it.

**Source:** Paul Christophersen, *The Articles: A Study of Their Theory and
Use in English* (Munksgaard, 1939), the founding statement of the
familiarity theory of "the"; and Herbert H. Clark and Susan E. Haviland,
"Comprehension and the Given-New Contract," in Roy O. Freedle (ed.),
*Discourse Production and Comprehension* (Ablex, 1977). Searched
"Christophersen 1939 familiarity theory definite article the givenness Heim
novelty" and "Clark Haviland 1977 given-new contract definite article first
mention reader processing"; the Clark and Haviland PDF itself returned an
HTTP 503 on fetch, so the summary below is drawn from the search-result
description of the paper (consistent across three independent citations
found) rather than the primary text directly.

**What it actually says:** "the" tells a reader "you already know which one
I mean," while "a/an" tells a reader "here is one you haven't met." Clark
and Haviland's given-new contract describes what a reader does when a
sentence violates that promise: given a definite noun phrase with no
matching antecedent, the reader performs what they call a bridging
inference, silently supplying a connection ("the door" after "a house,"
without ever being told the house has a door) rather than stopping to ask
where this door came from. Bridging works when the connection is obvious
from what came before (a house implies a door; a school implies a nurse's
office). It fails, and the reader notices the failure as confusion rather
than as an inference quietly made, when the needed bridge is not obvious.

**The test:** find a noun introduced with "the" that has not been named
before in the passage. Ask: can the reader construct the bridge to
something already established, without effort, in one step? (A registration
desk at camp implies a woman working it; a school implies a nurse.) If yes,
the definite article is earning its place, using the reader's own inference
rather than a clunky "a woman was working the desk; the woman found..."
introduction. If the connection requires two steps, or requires information
the passage has not given the reader yet, the definite article has jumped
ahead of what the reader actually knows.

**What it costs when broken:** a moment of "wait, what door" confusion,
followed by either a correct guess or, if the bridge really isn't there, a
flat sense that the text skipped something.

**Finding from the eight sample chapters:** clean, and worth reporting as a
demonstrated strength rather than leaving unmentioned. This book uses "the"
on first mention constantly, as a matter of house style (the nurse's
office, the woman at the registration table, the corkboard by the stairs),
and every instance checked in the eight sample chapters bridges cleanly from
something already established: a first day of camp implies staff and
signage; a self-defense class implies an instructor and a mat room. This is
in fact a big part of why the book's camera-only narration (per `HOUSE_RULES.md`)
reads as confident rather than confusing: definiteness on first mention is
functioning exactly the way Christophersen's and Clark and Haviland's
accounts predict a skilled writer's would.

**Can we measure it:** not well, automatically. Detecting "the X" with no
prior mention of X is mechanical; judging whether the bridge is one
inferential step or two requires world knowledge a script does not have.
Not worth building; better left to a human editor's ear, which this
project's own writing already demonstrates has this instinct.

**Conflicts with house rules:** none. This principle actively supports "the
camera is not talking to the reader" (Rule 1's sub-rule): a well-placed
definite article lets the camera show something as simply there, without
the narrator stopping to introduce it, which is exactly the reportorial,
non-explaining stance the house rule wants.

---

## 11. The question the author asked: does the sentence still refer to
something real after the rewrite?

The two examples given ("nobody has gotten over it," where *it* no longer
points at anything; "they carry the bracket rule into a stairwell," which
was never coherent even before the fix) are the same underlying failure
from two different directions: one made a working sentence grammatical by
stripping its referent out; the other made a broken sentence grammatical
without noticing it was never referring to anything real in the first
place. Both pass every check a grammar checker runs and fail the one this
project actually needs.

There is no single, one-word name for this exact check in the literature,
but there are several adjacent, precisely named ideas worth putting
together, because together they *are* the check:

**Chomsky's grammaticality/meaningfulness distinction.** Noam Chomsky,
*Syntactic Structures* (Mouton, 1957), used "colorless green ideas sleep
furiously" to prove that a sentence can be perfectly grammatical and
completely without meaning; grammaticality (does the syntax parse) and
semantic well-formedness (does it refer to something coherent) are two
separate properties, and a sentence can pass the first while failing the
second. This is the exact shape of both examples given: after each edit,
the syntax is clean and the meaning is not there. Searched "Chomsky
colorless green ideas sleep furiously grammatical but meaningless
distinction grammaticality semantics."

**Ryle's category mistake**, for the second example specifically. Gilbert
Ryle, *The Concept of Mind* (Hutchinson, 1949), page 17, defines a category
mistake as treating something that belongs to one logical category as if it
belonged to another (his own example: someone shown every building of a
university asking "but where is the university itself," treating an
institution as though it were a building). "They carry the bracket rule
into a stairwell" does exactly this: a rule is an abstract thing, not a
physical object, and "carry... into a stairwell" is a verb phrase that only
makes sense for a physical object. This is a specific, nameable diagnosis
for why that sentence never worked, in either its original or its fixed
form: the fix corrected the grammar around a category mistake without
touching the category mistake itself. Searched "Gilbert Ryle category
mistake definition concept of mind 1949."

**Broad (or vague) pronoun reference**, for the first example. Standard
composition handbooks (the same family of sources as principle 7 above)
distinguish ambiguous reference (a pronoun with two specific, competing
antecedents) from broad or vague reference (a pronoun, most often *it*,
*this*, *that*, or *which*, that points at a whole idea, situation, or
implied fact rather than any actual noun in the sentence). "Nobody has
gotten over it" is broad reference at its most damaging: *it* needs an
antecedent, the antecedent it used to have (the lip that beat everyone who
tried it) was removed by the edit, and nothing else in the new sentence can
fill that slot. The sentence now points at nothing, which a reader
registers as vagueness rather than as an outright error, because the
sentence still parses. Searched "broad reference vague pronoun this which
refers to whole idea not specific noun grammar handbook."

**Halliday and Hasan's cohesive tie**, reused from principle 8: a pronoun is
a cohesive device that only works if its tie to an antecedent actually
holds. When an edit removes the antecedent and leaves the pronoun standing,
the tie breaks, and Halliday and Hasan's own framework (1976) already has
language for this: it is a text that has lost cohesion at exactly that
point, even though every individual sentence in it is grammatical.

**Practical answer, put together as one usable check, since none of the
individual sources hands over a ready-made procedure:**

1. After any rewrite, find every pronoun (*it*, *this*, *that*, *they*,
   *which*) in the new sentence and physically point at the exact word or
   phrase in the actual text that it refers to. If you cannot point at
   one, the sentence has the first failure (Chomsky/broad-reference:
   grammatical, but nothing to refer to).
2. For every verb whose subject is an abstract noun (a rule, an answer, a
   decision, a feeling), ask whether that specific verb is something the
   abstract noun could literally do, or whether it is borrowed from a
   physical action that only makes sense for a physical object. If
   borrowed and nothing signals it as a deliberate metaphor, the sentence
   has the second failure (a category mistake).
3. Read the sentence in isolation, with no memory of the sentence it
   replaced. If it does not stand on its own as a real claim about the
   world of the book, the edit made something grammatical instead of
   making something true, and the fact that it used to be one specific
   broken sentence and is now a different, better-formed one does not
   matter: it still has to pass this test on its own.

This is close to what Amy Einsohn's *The Copyeditor's Handbook* (University
of California Press, several editions since 2000) calls the difference
between mechanical editing (spelling, punctuation, grammar) and language
editing (does it actually mean what it is trying to mean); Einsohn's own
summary of a copyeditor's job is the "4 Cs": clarity, coherency,
consistency, and correctness, in service of what she calls the "Cardinal C,"
communication. Grammatical correctness is only one of the four, and it is
possible to fully satisfy it while failing the other three, which is
precisely what happened in both of the author's examples. Searched "Einsohn
Copyeditor's Handbook levels of edit mechanical correctness language editing
meaning."

**The short answer to the author's question:** there is no single named
test, but the closest working name for the diagnosis is a *category
mistake* (Ryle) when the sentence gives an abstract thing a concrete verb,
and *broken cohesion* or *broad/vague reference* (Halliday and Hasan;
standard handbooks) when a pronoun survives an edit that removed its
antecedent. The check itself, since nobody has packaged it as one
procedure, is stated above as three steps, and it is a check that has to be
run by a person reading the finished sentence cold, the same way principle
7's ambiguity check does; nothing in this project's current toolkit
performs it, and nothing described above claims a script safely could.

---

# Deliverable 2: findings in the eight sample chapters

Read one file at a time, per the brief. Every quoted sentence below was
checked against the chapter file with grep immediately before writing it
down. Chapters not producing a strong new-principle finding beyond what is
already reported inside Deliverable 1 (existential *there*, cleft, tense,
definiteness) are not padded with a weak one; several principles above
report "clean" for the whole sample rather than manufacturing a violation.

### chapters/04_pluto.md, line 221 - Parallelism in a list

**Current:** "There's a fourth in Pluto who stays silent day after day,
answering when the teacher calls on him, in as few words as he can,
laughing at Sam, and otherwise silent."

**What is wrong:** the list following "who stays silent day after day"
mixes three different grammatical forms doing the same job (describing
Kavi's behavior): two present participles ("answering," "laughing") and one
bare adjective phrase ("otherwise silent"), with a subordinate clause ("in
as few words as he can") wedged between the first participle and the
second, describing the first rather than standing as its own list item.
Strunk's rule (principle 4 above) says coordinate items should share form so
the reader recognizes the list as a list; here the reader has to work out,
mid-sentence, that "in as few words as he can" is not a fourth item.

**Why it is not being changed here:** this is a judgment call, not an
obvious fix, because the sentence is introducing Kavi for the first time
and the loose, run-on shape may be doing real work mimicking a first
impression assembled from several separate observations rather than one
clean description. No house rule blocks touching it; this is narration, not
protected dialogue.

**Replacement, active:** "There's a fourth in Pluto who stays silent day
after day: he answers when the teacher calls on him, always in as few words
as he can, laughs at Sam, and stays silent the rest of the time." (Converts
the list into four parallel finite verbs sharing "he" as subject, which
also resolves the "in as few words as he can" problem by making it a
genuine fourth clause rather than a stray modifier.)

**Replacement, passive:** genuinely awkward to write, and here is why: every
item in the list is something Kavi does or is (answering, using few words,
laughing, staying silent), not something done to him, so passive voice has
no natural receiver to promote into the subject slot. Forced anyway: "The
teacher's calls get answered in as few words as he can manage, Sam gets
laughed at, and the rest of the time is spent silent." This is worse: it
introduces "the teacher's calls" and "Sam" as two different, competing
grammatical subjects inside one supposed description of Kavi, actively
destroying the parallelism the fix was trying to create. Passive is the
wrong tool for this specific defect.

**Replacement, third option:** "There's a fourth in Pluto who stays silent
day after day, answering the teacher in as few words as he can, laughing at
Sam, and staying silent through the rest." (Keeps the participial shape of
the original but makes all three items genuine parallel participles, and
folds "in as few words as he can" into the first item as its modifier
rather than a stray fourth element.)

---

### chapters/10_april.md, line 121 - Dangling modifier off a dummy subject

**Current:** "It takes her a while to work out what actually gets somebody
sent home from Halstead, checking off a list she keeps only in her head."

**What is wrong:** the participial phrase "checking off a list she keeps
only in her head" has no one to attach to. The subject of the main clause
is the dummy "It" (as in "it takes time"), and a dummy pronoun cannot check
off a list. The person actually doing the checking, Chloe, never appears as
a grammatical subject anywhere in the sentence. This is principle 3 exactly:
a dangling modifier, produced here not by a sentence-opener dodge but by a
dummy-subject construction that quietly displaced the real subject.

**Why it is not being changed here:** the fix is close to obvious (give the
participle a real subject to attach to) and is a small, safe edit that
loses nothing.

**Replacement, active:** "She takes a while to work out what actually gets
somebody sent home from Halstead, checking off a list she keeps only in her
head." (Chloe, as "she," is now the grammatical subject the participle
correctly attaches to.)

**Replacement, passive:** "What actually gets somebody sent home from
Halstead is worked out slowly by her, against a list kept only in her
head." Grammatically legal but noticeably worse: it buries her twice, once
behind "is worked out... by her" and again behind "kept" (a second passive),
and it is exactly the kind of sentence functional-grammar sources would
call unjustified passive, since the agent (her) is known, specific, and the
actual point of the sentence; there is no topic-continuity or unknown-agent
reason to prefer it here. Given only to show the passive direction was
tried and rejected, not recommended.

**Replacement, third option:** "Working out what actually gets somebody
sent home from Halstead takes her a while; she is checking off a list she
keeps only in her head." (Splits the sentence in two so the participle
becomes its own finite clause with an explicit subject, avoiding the dangle
without needing "It" at all.)

---

### chapters/13_ten_pages.md, line 130 - Referential failure (broad/vague
"her" with no working antecedent)

**Current:** "Somebody is off her feet before she turns around."

**What is wrong:** this is the exact failure the author asked about
directly (principle 11). "Somebody" is grammatically indefinite and
ungendered; "her" needs an antecedent that is either Chloe (established
several sentences earlier as the point-of-view character in this scene) or,
read cold, could just as easily seem to belong to "somebody" itself, which
makes no sense (a person cannot be off their own feet in that construction;
being "off one's feet" describes someone being knocked down, which requires
an agent doing the knocking). As written, nobody is doing anything to
anybody: the sentence has a stative description with the causal verb
missing, and the connection between "somebody" and "her" is closer to
Chomsky's grammatical-but-not-meaningful gap than to ordinary ambiguity: it
is not that two candidates compete for "her," it is that the sentence never
actually says who did what to whom.

**Why it is not being changed here:** the fix requires a judgment call about
what actually happened in the drill (does an attacker physically knock
Chloe down, or does she simply lose her footing on her own), which is a
narrative fact this report should not invent. Nothing in `HOUSE_RULES.md`
blocks fixing it; the obstacle is factual, not procedural.

**Replacement, active:** "Somebody knocks her off her feet before she turns
around." (Restores the missing causal verb; "somebody" is the agent, "her"
now clearly ties to Chloe as established two sentences earlier.)

**Replacement, passive:** "She is knocked off her feet before she turns
around." This is a legitimate, arguably better choice under the sibling
brief's own functional-grammar standard: the agent ("somebody," from a
chaotic mock-attack in the dark) is genuinely unknown and unimportant to the
sentence's point, while the receiver (Chloe, the point-of-view character)
is exactly what the paragraph is about, which is the textbook case for
preferring passive.

**Replacement, third option:** "She goes down before she can turn around."
(Avoids the "her feet" construction and the vague "somebody" entirely by
making the receiver the subject of an intransitive verb; loses the detail
that an attacker was responsible, which may or may not matter to the scene.)

---

### chapters/18_fifteen.md, line 95 - Ambiguous pronoun reference between
two named women

**Current:** "Odile asks her something on the way out and she answers it
badly, so she finds her at dinner to say it properly."

**What is wrong:** this is the exact case named in the brief: a "she" that
could belong to either of two women named in the paragraph before. "Odile"
is the immediately preceding grammatical subject; Centering theory
(principle 7) predicts a reader's automatic first guess for the following
"she" is Odile, since she was just the subject of her own clause. But the
sentence needs "she" to mean Chloe throughout (Chloe answers badly, Chloe
finds Odile at dinner), while "her" needs to mean Odile both times. Four
pronouns in one thirteen-word sentence, splitting 50/50 between two women
with no name to anchor any of them, is exactly the ambiguity the brief says
has already turned up once elsewhere in the book.

**Why it is not being changed here:** the fix is obvious and safe (name
Chloe, since she is the point-of-view character and the paragraph's actual
subject); nothing blocks it.

**Replacement, active:** "Odile asks her something on the way out and Chloe
answers it badly, so Chloe finds her at dinner to say it properly." (Naming
Chloe twice removes all four pronoun readings that depended on guessing
which woman "she" meant, while "her" now unambiguously means Odile both
times, since Chloe is named as the other party.)

**Replacement, passive:** "Something Odile asks her on the way out gets
answered badly, so Odile is found at dinner and given a proper answer."
Rejected: passivizing the second clause ("Odile is found") makes Odile the
subject of being found, which buries exactly the fact that matters, that
Chloe is the one who goes and does the finding. This is not a passive/active
problem to begin with; changing voice does not fix an antecedent problem,
and this rewrite proves it by producing a new sentence that is grammatical,
gender-unambiguous, and still gives the wrong character the agency.

**Replacement, third option:** "Odile asks Chloe something on the way out.
Chloe answers it badly, so she finds Odile at dinner to say it properly."
(Splits into two sentences, naming both women once each; the remaining
pronoun, "she" in the second sentence, has only one available antecedent
by that point, Chloe, since Odile was just named in the same sentence as an
object, not a subject.)

---

### chapters/22_the_offer.md, line 209 - Long-distance dependency between a
verb and its complement (dialogue)

**Current:** "You turned it down and left whether it's still on the table
later completely unasked."

**What is wrong:** the verb "left" and its complement "unasked" are
separated by a full embedded question, "whether it's still on the table
later," eleven words long. Per Gibson's Dependency Locality Theory
(principle 2), this is the same cost as subject-verb separation applied to
a verb and its object complement instead: the reader has to hold "left...
[what?]" open in memory across the entire embedded clause before "unasked"
finally resolves what was left undone. On a first read this genuinely
produces a small stumble, because "left X unasked" is an unusual enough
construction that the reader cannot predict the ending early.

**Why it is not being changed here:** this is the father's dialogue, and
Rule 1 protects dialogue as something people actually say, imperfections
included; a real, agitated father talking on the phone plausibly produces
exactly this kind of run-on construction. Reported per the brief's
instruction to report what house rules protect, with the dialogue rule
named as the reason it stands.

**Replacement, active:** "You turned it down, and you never asked whether
it's still on the table later." (Closes the gap: "asked" now sits right
next to its object clause, with no separation.)

**Replacement, passive:** "You turned it down, and whether it's still on
the table later was never asked." Grammatically possible but strained: it
promotes the embedded question itself to subject position, which is an
unusual and formal move for spoken dialogue, and actively fights the
ninth-grade, spoken register the character needs. Given to show that
passive does not solve a separation problem either; the separation is the
whole defect, not the voice.

**Replacement, third option:** "You turned it down without ever asking if
it's still on the table." (The most natural-sounding option for spoken
dialogue: shorter, no separation, and closer to how an agitated parent
would actually phrase it out loud.)

---

### chapters/26_the_exercise.md, line 131 - Misplaced-modifier ambiguity
from missing punctuation (dialogue)

**Current:** "The man who took you had been in position since twenty-one
hundred, which is seven hours without moving through the entire drop in
temperature that arrives after midnight, and it took him under two seconds
once you finally got there."

**What is wrong:** "moving through the entire drop in temperature" is,
on a first pass, readable as one unit, as if someone physically moved
through a temperature drop the way one moves through a doorway. The
intended meaning is "seven hours without moving, [held that position]
through the entire drop in temperature," two separate facts (he did not
move; the temperature dropped the whole time), run together without the
comma that would keep them apart. This is a misplaced-modifier-shaped
garden path (principle 3): the reader's first parse is wrong, and the
sentence has to be re-read once "that arrives after midnight" makes the
literal reading fall apart.

**Why it is not being changed here:** this is the major's dialogue,
delivered as a single continuous speech, and Rule 1 protects the run-on,
accumulating quality of his monologue as characterization (a man building
one long, relentless point). This particular fix is not a voice change and
not really an obvious/judgment-call split either: it is a comma, which
changes nothing about the register or the content, only the parse. Reported
because it is dialogue, and named as such, per the brief.

**Replacement, active:** "which is seven hours without moving, through the
entire drop in temperature that arrives after midnight" (the punctuation
fix alone, keeping every word).

**Replacement, passive:** not really available as a separate axis here:
recasting "he had been in position" as some more passive form ("the
position had been held by him") does nothing to the actual defect, which is
purely a matter of where the comma sits, not who the grammatical subject is.
Given for completeness: "the position was held, unmoved, through the entire
drop in temperature that arrives after midnight," which is legal but
noticeably more formal than the major's spoken voice elsewhere in the same
speech, and probably a worse fit for that reason.

**Replacement, third option:** "which is seven hours holding still through
the entire drop in temperature that arrives after midnight" (recast to
remove the negative-modifier shape entirely, so there is nothing left to
misparse).

---

### chapters/31_ruth.md, line 7 - Nominalization

**Current:** "Her assumption is that a real sequence exists somewhere the
school hasn't placed her in, a bureaucratic problem, and she spends most of
October trying to find the right office."

**What is wrong:** "Her assumption is that..." buries the actual action
(Ruth assuming something) inside the noun "assumption," with "is" left to
do the grammatical work a real verb should be doing. Per Williams's test
(principle 1), Ruth is a specific, known character, already established as
the subject three sentences earlier and the subject of the very next
clause ("she spends most of October"); there is no legitimate reason
(backward reference, familiar-concept shorthand, avoiding "the fact that")
to prefer the nominalized form here. This is a clean, low-stakes case of the
principle, chosen because it shows the fix working exactly the way Williams
predicts: restoring the verb restores Ruth as the subject of her own
thought, for free.

**Why it is not being changed here:** the fix is obvious, cheap, and loses
nothing; no house rule stands against it.

**Replacement, active:** "She assumes a real sequence exists somewhere the
school hasn't placed her in, a bureaucratic problem, and she spends most of
October trying to find the right office." (Restores "assumes" as the verb,
with Ruth, already the subject of the surrounding sentences, carrying it
directly. Same word count.)

**Replacement, passive:** "That a real sequence exists somewhere she hasn't
been placed is assumed by her, a bureaucratic problem, and most of October
is spent trying to find the right office." Given to show why passive is
wrong here rather than merely unwritten: it takes an already-mild
nominalization problem and makes it worse, adding a second passive ("is
spent") and burying Ruth, the paragraph's actual subject and the character
the whole chapter is about, behind two separate "by her"/implied-agent
constructions. Functional grammar's own criteria for preferring passive
(unknown agent, topic continuity, receiver as what the sentence is about)
all point the other way in this sentence: Ruth is known, is the topic, and
is not the receiver of anyone else's action here.

**Replacement, third option:** not needed; the active version above is
clean and requires no compromise.

---

### chapters/35_nine_minutes.md, line 105 - Dangling appositive (a
reference that does not point at anything the sentence actually
established)

**Current:** "Months into the job now, her badge scans without a second
glance and the elevator ride already reads like a formality, the kind of
building that stopped feeling strange to walk into somewhere early on."

**What is wrong:** "the kind of building that stopped feeling strange to
walk into somewhere early on" is an appositive with nothing correct to
attach to. The two nouns immediately available to it are "her badge" and
"the elevator ride," and neither of those is "a kind of building"; an
elevator ride is not a building. The sentence clearly means the building
itself (implied by "the job," never named directly in this sentence) is
what stopped feeling strange, but as written the appositive is grammatically
glued to "the elevator ride," producing exactly the author's second
example's failure: a sentence that reads as fine on a fast pass and, looked
at directly, refers to nothing that is actually there (Ryle's category
mistake in miniature: an elevator ride cannot be "a kind of building" any
more than a rule can be carried into a stairwell).

**Why it is not being changed here:** the fix is close to obvious (give
"the building" its own clause to attach the description to) and costs
nothing in tone or meaning.

**Replacement, active:** "Months into the job now, her badge scans without
a second glance and the elevator ride already reads like a formality; the
building stopped feeling strange to walk into somewhere early on." (Splits
the sentence so "the building" gets stated directly and the description has
something real to describe.)

**Replacement, passive:** "Months into the job now, her badge is scanned
without a second glance and the elevator ride already reads like a
formality; the building stopped feeling strange to be walked into somewhere
early on." Both changes are strained: "her badge is scanned" removes the
sense that the scanning is now routine and automatic (closer to what an
active "scans" conveys about her own habituation) for no gain, and "to be
walked into" is clumsy in a way spoken or narrated English rarely produces.
Given to show the defect is not a voice problem: fixing the reference does
not require touching voice at all, and forcing passive onto this sentence
only adds new awkwardness without touching the actual error.

**Replacement, third option:** "Months into the job now, her badge scans
without a second glance, the elevator ride already a formality, the kind of
building that stopped feeling strange to walk into somewhere early on."
(Keeps the single-sentence shape and the accumulating rhythm of the
original by demoting "the elevator ride already reads like a formality"
into its own appositive phrase, which then puts "the elevator ride" and
"the kind of building" in parallel as two descriptions of the same
workplace, rather than making the second one falsely modify the first.)

---

### chapters/35_nine_minutes.md, lines 101 and 103 - Ambiguous pronoun
across a scene break (a "she" that could belong to either of two women)

**Current:** "It's still warm enough at midnight that she's got the window
cracked, the ordinary noise of the street coming up thin through the screen
over the sound of the fan." Followed, after no further naming, by: "Chloe
reads that at one in the morning, with work waiting on the other side of a
short night."

**What is wrong:** the paragraph immediately before this one ends on Ruth
("Ruth's screen dims... then she shuts the laptop for the night"), so Ruth
is the most recently named, most recently subject female character when the
scene break happens. Per Centering theory (principle 7), a reader's default
guess for the next unattributed "she," even across a scene break, is
whichever woman was last the grammatical subject, which is Ruth. But the
"she" at line 101 is actually Chloe, revealed only two sentences later when
"Chloe reads that at one in the morning" retroactively identifies whose
midnight window this was. This is the cross-paragraph version of the same
ambiguity found in `18_fifteen.md`, and arguably a harder case, since a
scene break is normally exactly the signal a reader relies on to expect a
new, soon-to-be-named subject, not a continuing pronoun from the last
scene; here the break gives no warning that the pronoun is about to switch
women.

**Why it is not being changed here:** the fix is obvious and safe: name
Chloe at her actual first mention in the new scene rather than after the
fact.

**Replacement, active:** "It's still warm enough at midnight that Chloe has
the window cracked, the ordinary noise of the street coming up thin through
the screen over the sound of the fan. She reads that at one in the
morning, with work waiting on the other side of a short night." (Chloe
named at first mention in the new scene; "she" in the following sentence
now has exactly one possible antecedent.)

**Replacement, passive:** "It's still warm enough at midnight that the
window is left cracked, the ordinary noise of the street coming up thin
through the screen over the sound of the fan. The messages are read by
Chloe at one in the morning, with work waiting on the other side of a short
night." Rejected on the same functional-grammar grounds as the earlier
nominalization finding: Chloe is known, is the topic of the whole
paragraph, and is not a receiver here so much as the person the scene is
about; passivizing "reads" into "are read by Chloe" buries exactly the
character the sentence needs up front to resolve the ambiguity, which
defeats the fix's whole purpose.

**Replacement, third option:** not needed beyond the active version; naming
Chloe at first mention is a complete fix on its own.
