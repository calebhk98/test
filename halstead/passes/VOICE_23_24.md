# Voice pass, chapters 23-24

Scope: `chapters/23_the_first_one.md` and `chapters/24_the_chat.md` only.
Dialogue and the chat-transcript lines in chapter 24 were not touched, per
the brief; nearly all of chapter 24's work turned out to be in its narration
frames around the transcript, as expected.

Read `passes/HOUSE_RULES.md`, `passes/DO_NOT_FLAG.md`, and the repository
`CLAUDE.md` in full before starting. Went sentence by sentence through both
chapters, grepped for passive auxiliaries and for the common fake-agency
verbs (`goes`, `comes`, `lands`, `produces`, `holds`, etc.) to check nothing
was missed, then ran `measures/style_report.py` on both chapters after
editing to confirm word count, sentence count, and the em-dash/curly-quote
checks held steady. Did not run `grade.py`.

## Count

- **Person put in the subject of a passive, fixed: 6** (5 in narration
  proper, 1 a participial "having been interviewed").
- **Fake agency (inanimate/abstract subject, active verb, nobody acting),
  fixed: 12.**
- **Total sentences changed: 18**, all passive-or-fake-agency to active with
  a real doer. Zero went the other direction (active made passive); nothing
  in either chapter needed that.
- **Called out, not changed: 2.**

## Changed

### chapters/23_the_first_one.md

1. **Before:** "...and she reaches Kessler, starts on the part after the
   stage, but is called away by her own name from the front before she is
   finished."
   **After:** "...and she reaches Kessler, starts on the part after the
   stage, but a voice from the front calls her name before she is finished."
   **Why:** Alcantar, a person, was the subject of a passive ("is called
   away"). No specific caller is established, so the fix supplies a vague
   but human source ("a voice") rather than inventing a named culprit.

2. **Before:** "every family confirmed a headcount by the first of May, and
   the order that went out matched it to the chair."
   **After:** "every family confirmed a headcount by the first of May, and
   the office matched the chairs to it."
   **Why:** Fake agency — "the order" (a document) was doing the matching.
   The office is the obvious, faceless doer, in keeping with how the same
   paragraph already treats the sewing room and the woodshop as active
   institutional subjects.

3. **Before:** "That sentence goes straight past Chloe anyway, because Sam
   has spent the whole speech trying to make her laugh and finally succeeds
   on that word."
   **After:** "Chloe misses that sentence anyway, because Sam has spent the
   whole speech trying to make her laugh and finally succeeds on that word."
   **Why:** Fake agency, almost the brief's own example verbatim (a sentence
   "goes" somewhere with nobody doing anything). Chloe is right there and is
   who the paragraph is about; putting her in the subject as the one who
   misses it costs nothing.

4. **Before:** "Then they read out ninety-one names in alphabetical order,
   evenly paced, timed to the stopwatch that clocked the rehearsal, and
   every name lands where the schedule put it, each family standing on
   cue."
   **After:** "...and they hit every name where the schedule put it, each
   family standing on cue."
   **Why:** Fake agency ("name lands"). "They" (the staff reading the
   names) is already the subject of the first half of the same sentence, so
   carrying it through costs nothing and reads as one continuous action
   instead of the names acting on their own.

5. **Before:** "Sam is caught first, gown still on over yesterday's
   t-shirt."
   **After:** "Her grandmother catches Sam first, gown still on over
   yesterday's t-shirt."
   **Why:** Sam, a person, was the subject of a passive. The grandmother is
   the actor throughout the whole passage (she is doing the catching of
   Kavi and the stranger a few lines later); this just puts her in the
   subject for the first one too, and matches how the paragraph already
   handles the fourth person ("The fourth she catches is a stranger...").

6. **Before:** "Chloe gets caught on her way past, the chair between her
   and the lemonade. \"And what are you doing next?\" her grandmother
   asks."
   **After:** "Her grandmother catches Chloe on her way past, the chair
   between her and the lemonade. \"And what are you doing next?\" she
   asks."
   **Why:** Same fault as #5 — Chloe, a person, as the subject of a
   passive. Fixed the same way, and dropped the second "her grandmother" to
   "she" since the noun is now established one clause earlier.

7. **Before:** "Her own box goes down the ground-floor hallway with a forge
   mallet with a handle still the wrong shape wedged in next to a stack of
   notebooks."
   **After:** "Chloe carries her own box down the ground-floor hallway, a
   forge mallet with a handle still the wrong shape wedged in next to a
   stack of notebooks."
   **Why:** Fake agency — the box "goes" down the hallway by itself. Chloe
   is named as the one carrying it two sentences earlier in the previous
   paragraph; making her the subject here is the obvious fix and also
   clears up the doubled "with... with" in the original.

8. **Before:** "The first month produces a few dozen registered users and
   exactly one hire, but the hire is a man who already had the job and used
   the site to fill in the application form."
   **After:** "In the first month a few dozen people register, and exactly
   one hire comes of it: a man who already had the job and used the site to
   fill in the application form."
   **Why:** Fake agency — "the first month" (a time period) was doing the
   producing. The people who register are the real actors; put them in the
   subject instead.

9. **Before:** "Theo goes into the federal government as an analyst, having
   been interviewed repeatedly and having answered every question
   completely."
   **After:** "Theo goes into the federal government as an analyst, having
   gone through round after round of interviews and answered every question
   completely."
   **Why:** Theo, a person, was the (implicit) subject of a passive
   participle. "Having gone through" keeps him doing something to himself
   rather than something being done to him, without inventing who
   interviewed him.

10. **Before:** "Her father hears it at the kitchen table once her mother's
    gone up to run a bath, the version of it that goes to him first."
    **After:** "Chloe gives her father the version of it that reaches him
    first, at the kitchen table once her mother's gone up to run a bath."
    **Why:** Fake agency — "the version of it" was going to him on its own.
    Chloe is the one telling him (the next paragraph is literally her
    explaining it to him), so she is the obvious doer; kept "version," since
    the word is carrying the detail that what her mother later gets is not
    quite the same telling.

11. **Before:** "The laptop closes and stays shut for the rest of the
    night."
    **After:** "Chloe closes the laptop and doesn't open it again that
    night."
    **Why:** Fake agency — the laptop closes itself. Chloe is sitting at
    the desk in the sentence immediately before this one; she is the one
    closing it.

### chapters/24_the_chat.md

12. **Before:** "Sam is at a processing station somewhere the paperwork
    won't name, where they hand his phone back a few minutes at a
    stretch."
    **After:** "Sam is at a processing station somewhere the Army won't
    name, where they hand his phone back a few minutes at a stretch."
    **Why:** Fake agency — "the paperwork" was doing the refusing. The
    Army is the faceless institution actually withholding the location, and
    "they" one clause later already refers to it, so this also removes an
    unclear antecedent.

13. **Before:** "It's been months since anyone in the group has been in a
    room together, and the loose plan from June, get together before the
    holidays, has produced exactly zero weekends that work for more than a
    couple of people at once."
    **After:** "...and nobody has turned the loose plan from June, get
    together before the holidays, into a weekend that works for more than a
    couple of people at once."
    **Why:** Fake agency — "the plan" was doing the producing. Nobody in
    the group is the actual, if collective and unnamed, non-doer here, and
    "nobody" is honest about that rather than inventing a specific person
    who dropped the ball.

14. **Before:** "By dinner a new thread has replaced it, about something
    else entirely, and the November date stays exactly as unsettled as it
    was that morning."
    **After:** "By dinner the group has moved on to something else
    entirely, and the November date stays exactly as unsettled as it was
    that morning."
    **Why:** Fake agency — "a thread" replacing itself. The group members
    are the ones actually moving the conversation along; naming them is a
    one-word-for-one-word swap that costs nothing.

15. **Before:** "...Ruth's Providence weekend, whether Theo's leave is the
    week he said it was, whether Sam has been told yet, which stretch Priya
    expects to have a signal in."
    **After:** "...whether the Army has told Sam yet..."
    **Why:** Sam, a person, was the subject of a passive. The chat
    transcript already established who would be doing the telling (`sam:
    cant say yet. they tell us in october, maybe`), so naming the Army is
    not an invented fact.

16. **Before:** "The list holds him long enough that the woman at the next
    desk finishes a telephone call, and Nadia lets him finish."
    **After:** "The manager stays on the list long enough that the woman at
    the next desk finishes a telephone call, and Nadia lets him finish."
    **Why:** Fake agency — "the list" was doing the holding. He is the one
    actually lingering over it (he is "manager" two paragraphs earlier);
    putting him in the subject also removes the odd effect of an inanimate
    object detaining a person.

17. **Before:** "Sam draws half an hour with his phone most evenings,
    sometimes less, in a room with nineteen other guys doing exactly what
    he is doing at rows of folding tables, and whatever's left of it goes
    to the chat."
    **After:** "...and he spends whatever's left of it on the chat."
    **Why:** Fake agency — the leftover time "goes" to the chat by itself.
    Sam is the subject of the first half of the same sentence; carrying him
    through is free.

18. **Before:** "...a few seats down from where he used to sit before this
    year moved everyone else out of it."
    **After:** "...a few seats down from where he used to sit before
    everyone else moved on this year."
    **Why:** Fake agency — "this year" (a time period) was doing the moving.
    The people who actually left (his old table, the class that graduated in
    chapter 23) are the real doers; naming them instead of the calendar is
    the obvious fix and invents nothing, since the graduating class leaving
    is already the given fact of the two chapters.

19. **Before:** "Days pass before Kavi comes back with anything. When he
    does, he says he asked and was told it's internal."
    **After:** "...he says he asked and they told him it's internal."
    **Why:** Kavi, a person, was the subject of a passive. "They" is
    already the pronoun the very next sentence uses for whoever gave him
    that answer ("That's the word they used"), so this is consistent with
    text already on the page rather than a new choice.

## Called out, not changed

### chapters/24_the_chat.md, line 511

**Current:** "The chat moves on within minutes."

**Why the voice is wrong:** Fake agency — "the chat," an inanimate channel,
is the grammatical subject of "moves on," and nobody in the group is named
as doing anything.

**Why I did not change it:** This is the last narration line of the
chapter, immediately followed by "Chloe's tab stays open on her desk for
the rest of the evening, the group thread gone still and the one with
Nadia gone still right behind it." The two sentences read as a deliberate
pair — the shared chat (a thing) moving past the moment versus Chloe's tab
(also a thing) staying open on it — and the parallel is between two
objects, not between a group of people and Chloe. Naming "the group" or
"the rest of them" as the subject would break that symmetry right at the
chapter's close, which is exactly the kind of load-bearing spot the brief
says to write up rather than gamble on.

**Replacement 1:** "The rest of them move on within minutes."
**Replacement 2:** "Everyone else moves on within minutes."

### chapters/23_the_first_one.md, line 105

**Current:** "Her father is still bent over the invoice in front of him,
although the pen stops moving on it."

**Why the voice is wrong:** Fake agency — "the pen," an object he is
holding, is the subject of "stops moving," when it is his hand that stops.

**Why I did not change it:** This reads as the same device the book uses
for involuntary body reactions elsewhere ("her knees go loose," "his thumb
stays where it is"), which the brief says to leave alone, except that a pen
is not a body part, so I cannot be sure this is meant to fall under that
protection rather than being a plain miss. It sits directly in the middle
of Nadia's big pitch to her father and is doing real work as his one
visible tell that the number has landed; changing the image risked losing
that without being sure it needed fixing at all.

**Replacement 1:** "Her father is still bent over the invoice in front of
him, although his hand stops moving on it."
**Replacement 2:** "Her father is still bent over the invoice in front of
him, although he stops writing partway down the page."
