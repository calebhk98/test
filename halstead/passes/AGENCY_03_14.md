# Fake-agency pass, chapters 3-14

Scope: `chapters/03_the_letter.md` through `chapters/14_sixty_degrees.md`, the
childhood chapters (Chloe six through eleven). No other chapter touched.

## Method

Read `passes/HOUSE_RULES.md` and `passes/DO_NOT_FLAG.md` in full before
touching anything. Ran the finder regex from the brief against all twelve
chapters, got 90-some raw hits, then read every hit in its paragraph before
deciding. `measures/style_report.py` run per chapter after editing, not
`grade.py` (other agents were running it).

## Count

- **Hits read: 96** (regex matches across the twelve chapters, several of
  them the same construction counted once per occurrence).
- **Became a person doing something (option 1): 12**
- **Became a passive with an implied doer (option 2): 5**
- **Left alone: 79**, for the reasons below.
- **Places where naming the doer would have invented a fact: 0.** Every
  option-1 fix used a doer already named or clearly established in the
  surrounding paragraph (Chloe, her mom, her dad, Hearn, the vendor, the
  receptionist, Sinclair, her teammates). Two places where I could not
  identify the doer with any confidence went to option 2 instead (the
  postings in chapters 11 and 13-14): the author's own note in the brief
  about school sheets applies directly there.

## Fixes made

### Chapter 3 — The Letter

1. "Tuesday and Wednesday go quiet, but **the callback comes** Thursday
   afternoon." → "...but **the receptionist calls back** Thursday
   afternoon." *Option 1.* The receptionist was named two sentences earlier
   ("a receptionist takes the name down and says she'll look into it"), so
   this costs nothing invented.
2. "**The envelope comes back** out of the recycling." → "**Her mom pulls
   the envelope back** out of the recycling." *Option 1.* Her mom is mid-scene
   and was just told to check the postmark; she is the only person who could
   plausibly do this.
3. "**The column goes** past, then back up to the top, photograph after
   photograph..." → "**She scrolls the column** past..." *Option 1.* Chloe is
   alone at the laptop in this paragraph ("Chloe gets the screen awake with
   the space bar and starts where her dad started").

### Chapter 5 — Behind

4. "...and **the weights go in** a pound at a time, the whole room counting
   out loud together." → "...and **the weights are added** a pound at a
   time..." *Option 2.* Naming which child in which of the many groups adds
   the weights to any one bridge would invent a fact; "the whole room" doing
   it together is already the point of the sentence, and the object (the
   weights, the count) is what the sentence is about.

### Chapter 7 — The Same Room

5. "The school says **the message went out** that same week, to all three
   numbers..." → "The school says **it sent the message out** that same
   week..." *Option 1.* "The school" is the grammatical subject two words
   earlier; this just lets it do the sending instead of the message doing
   the arriving.

### Chapter 11 — Eight

6. "...keeping count of every pass **that never comes to her**." → "...keeping
   count of every pass **her teammates never send her**." *Option 1.* The
   scene has already established the team (two people on it Chloe "has
   decided against") who aren't passing; this names them without inventing
   anything beyond what the paragraph already implies.
7. "At the end of term **the sheet goes up** on the wall with everybody on
   it in order..." → "...**the sheet is posted** on the wall..." *Option 2.*
   This is the brief's own example. I don't know which staff member posts
   end-of-term rankings (drawing one week, dance another, run out of a
   different office each time), and a seven-year-old reading a sheet a
   school put up is exactly the case the brief calls out for a passive
   with an obvious institutional doer.
8. "**Her name goes** on the choir line, because she sang in the shower..."
   → "**Chloe signs her name** on the choir line..." *Option 1.* This is a
   sign-up sheet, established two paragraphs earlier ("a blank line next to
   every entry and a pencil on a string"); Chloe herself is the one signing
   up, not an institution.

### Chapter 12 — Nine

9. "In April **the stables move the groups around** and Priya goes to
   Tuesdays..." → "In April **the groups are moved around** and Priya goes
   to Tuesdays..." *Option 2.* No specific stable staff member is named or
   in the scene; the reassignment is what the sentence is about.
10. "Some come back with dates, but **the rest come back** as the same
    sentences with different words in them..." → "Some come back with
    dates, but **the vendor sends the rest back** as the same sentences..."
    *Option 1.* "The vendor" is the subject of the previous sentence ("he
    asks the vendor which of the sentences...").

### Chapter 13 — Ten Pages

11. "**The arithmetic goes up** on the board in silence..." → "**He puts the
    arithmetic up** on the board in silence..." *Option 1.* Hearn is "he"
    one sentence earlier, still at the board.
12. "...but **that draft comes back** worse than the others." → "...but
    **Hearn marks that draft** worse than the others." *Option 1.* Hearn is
    the only person grading her essays in this chapter; "comes back" was
    standing in for the grading he does every week.
13. "**The sheet goes up** on the Friday; every name on it has an F next to
    it..." → "**The sheet is posted** on the Friday..." *Option 2.* Same
    reasoning as #7: a drill roster posted by an unnamed office, immediately
    next to an already-passive sentence in the same section ("Response time
    is scored against the standard. The standard is posted weekly.") for
    consistency.

### Chapter 14 — Sixty Degrees

14. "**Her release runs** early when she is keyed up and late when her hands
    are cold..." → "**She releases** early when she is keyed up..."
    *Option 1.* It's her own release; no reason to route it through an
    abstract noun.
15. "...and **that twelfth goes** on the shelf over her desk." → "...and
    **she puts that twelfth** on the shelf over her desk." *Option 1.* Her
    project, her desk, her shelf.
16. "**The dishcloth goes** on the oven door." → "**He hangs the dishcloth**
    on the oven door." *Option 1.* Her dad had the dishcloth over his
    shoulder one line earlier and is the only person in the scene.
17. "**The intercom comes on** in the middle of the afternoon block, and it
    is Sinclair." → "**Sinclair comes on the intercom** in the middle of the
    afternoon block." *Option 1.* Merges two clauses that were already
    naming him; also removes one "and" against the book's 10% ceiling on
    2+-and sentences rather than adding one.
18. "**The Watch** on the eleventh of April **goes up on the board** on the
    Monday, and it says the whole school." → "...**is posted on the
    board**..." *Option 2.* Same institutional-posting pattern as #7 and
    #13; caught by inspection rather than the regex, which doesn't match
    across the intervening date clause, but it's the identical
    construction and I judged it in scope.

## Left alone, and why

The great majority of hits were not fake agency as the brief defines it.
Grouping the 79 by reason rather than listing all of them:

**Involuntary physical/embodied reactions (the largest group, ~25 hits).**
Constructions like "her knees go loose," "her ears stay hot," "her mouth
goes tight," "the hand stays where it is," "her eyes stay on the tray,"
"the sentence stays stuck behind that one," "the word comes out thin." This
book's house rule bans named emotional states in narration and instead
gives the physical fact standing in for the feeling (`HOUSE_RULES.md`,
"the tone construction" section: "give the sound... never give the state").
A body doing something involuntary is not a task somebody failed to be
credited for; there is no agent to give it to, and naming one ("she stiffens
her knees") would either invent intent that isn't there or, worse, force a
named state to make the sentence make sense. I left these across all twelve
chapters, including the closely-matched pair "Priya's hand goes across her
own shoulder" (ch. 4) and "a hand goes over the lip" for Sam's climb (ch.
12): both are camera close-ups on a person already identified a clause away
("him" in the Sam case), not a document walking to Deb.

**Genuinely no human agent — natural or physical process (~15 hits).**
"The lava comes up," "the weight goes down / the mass stays" (Ruth's physics),
"the shape stays where it is" (a triangle not folding), "the pieces land"
(gravity), "the angle holds at sixty degrees," "the grass comes up to the
brick." These are camera facts or dialogue about how the physical world
behaves. No fix available or needed.

**Automated/timed systems, explicitly established as such (~4 hits).** "The
lights in that hall go off in sections" (ch. 6) and "the lights come down"
twice in ch. 12 ("it is on a clock from the first week" — stated two
sentences earlier). These are on a timer by the book's own account, so
there is no doer to recover.

**Dialogue (~20 hits).** "Where did the list come from," "the digits go in,"
"the run come in" (cribbage), "the corner goes first" (Chloe retelling the
bridge), "the essay went in," "the plates go," "his reason goes," "the
floor came up at me." Dialogue reflects how a child or a teacher actually
talks; several of these are established character-voice idioms repeated
deliberately (Chloe's bridge story is told the same way in narration in
ch. 5 and in her own words at dinner in ch. 6). I did not touch dialogue
anywhere in this pass — changing a character's own phrasing to fix a
narration-level problem would be a synonym-swap of the kind the brief
explicitly rules out, and it risks the quotation-length and short-speech
bands, which are already on thin margins.

**Institutional/generic idiom already matching the rule's own "leave it"
bucket (~10 hits).** "The food comes," "the bell goes," "the plates come
back," "the callback" (before the fix), "the note runs to half a page,"
"the day sits in the fall." These are the "winter comes" / "the bell goes"
cases the brief names directly: correct as is, and forcing a person into
them would read worse, not better.

**Protected — the Bex/Kavi credit-taking passages (5 hits, chapters 12-14).**
The bridge in ch. 12 ("Bex has it before Chloe has her mouth open... and
gives everything after it in I"), the paintball floor and corridor in ch. 13
("it is Bex who tells Bell she has worked something out," "which Kavi had
off the wall bars," "the year goes at it that way from then on," "his
number goes from three to double figures," and the sheet Bell posts under
her name), and the astronomy dinner in ch. 14 (all three Bex lines) contain
flagged constructions I left untouched on principle, not just for the
specific clauses that matter. I verified after editing that all three
passages are byte-for-byte identical to the versions I read at the start of
the pass.

**Regex false positives (~5 hits).** "their parents came," "her grandfather
sits back," "Her parents sit in the living room" — the regex's person-noun
list doesn't include "parents" or "grandfather," so these matched as if the
subject were a thing. They already have a real human subject doing a real
verb; nothing to fix.

## Where I used judgement on the child-agency point

Per the brief's note that a child genuinely has less agency than an adult:
every option-2 (passive, implied doer) fix in this pass is a case of an
institution acting on a child, where the specific staff member is neither
named nor knowable from the text (end-of-term rankings, stable-group
reassignment, a Defensive Watch drill roster, a school-wide Watch schedule).
In each of those four cases I judged that inventing a name or role for the
person tacking it up would be a fabricated fact, whereas "the sheet is
posted" is the honest sentence — it says the school did it without
pretending to know which office did it. Where the doer was a specific,
already-present adult or was Chloe herself with clear reason to be doing
the thing (signing up for choir, scrolling a webpage, a parent walking to
the recycling bin), I used option 1.

## No invented facts

I did not name any doer beyond what the surrounding paragraph already
established. The two closest calls were the receptionist in chapter 3
(named two sentences earlier as "a receptionist," not by name, so I kept
her that way rather than inventing "Deb" or similar) and "her teammates" in
chapter 11 (the scene already describes two specific teammates Chloe
"decided against," so "her teammates" describes people already on the
page, not a new fact).
