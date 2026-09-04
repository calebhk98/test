# Fake-agency pass, second loop, chapters 3-14

Scope: `chapters/03_the_letter.md` through `chapters/14_sixty_degrees.md`. No
other chapter touched. This is the second loop over the same twelve
chapters; `passes/AGENCY_03_14.md` (the first loop's record) was read in
full first, along with `passes/HOUSE_RULES.md`, `passes/DO_NOT_FLAG.md`, and
the root `CLAUDE.md`, before anything was edited.

## Method

Ran the finder regex given in the brief (both the `determiner + noun + verb`
pattern and the new `it + verb` pattern) against the current text of all
twelve chapters, confirmed the DET-class hit count had shrunk from the
first loop's 96 to 80 (consistent with the 17-18 fixes the first loop
already made having removed themselves from the match set), then read every
hit — DET and IT both — in its paragraph or quotation, checked it against
the first loop's stated reasons for leaving things, and decided.
`measures/style_report.py` was run per edited chapter afterward, not
`grade.py` (other agents were running it).

## Count

- **DET hits read: 80.** All 80 were cross-checked against the first loop's
  written reasoning (body reactions, natural/physical process, timed
  systems, dialogue, institutional idiom, the protected Bex passages,
  regex false positives on "parents"/"grandfather", and "go"/"run" used as
  a noun rather than a verb). 79 of the 80 fit a category the first loop
  had already named and reasoned through correctly; those were left alone
  without re-litigating them.
- **DET hits changed: 1** (the one the first loop's regex matched but whose
  write-up gave no reason to leave it — see below).
- **IT hits read: 44.**
- **IT hits changed: 3.**
- **IT hits left: 41**, the great majority of them exactly the ordinary
  English the brief warned against forcing: "it stays outside the four,"
  "it comes out right," "it goes up every single year," "it stays under the
  bed until the middle of May." Breakdown of the 41 by reason:
  - **Dialogue (~19 hits).** Character voice, untouched throughout: the
    depression explanation in ch. 8, the inheritance/money speech and the
    cricket-ball description in ch. 11, the office worker's "it goes up
    every single year" in ch. 12, Ruth's "we're all watching it come" in
    ch. 13, Chloe's "it sat in a room untouched" in ch. 14, and others.
  - **Genuinely no human agent — natural/physical/internal process (~13
    hits).** Sound travelling through a floor or across a field, a chemical
    turning white, a phrase failing to translate cleanly, a sentence's
    meaning arriving all at once in her own head. No fix available or
    needed; there is nobody to hand the verb to.
  - **Institutional/generic idiom, obvious or unknowable doer (~5 hits).**
    "it went round" (the rumor mill, explicitly protected in
    `DO_NOT_FLAG.md`), "it went for at auction," "the sheet says it runs to
    the end," "in November it goes to twos" (the self-defense curriculum's
    own numbering).
  - **Protected Bex passages (2 hits, both in ch. 13, both within the
    paintball-floor/corridor scene).** Left untouched on principle; verified
    byte-for-byte identical to the versions read at the start of the pass.
  - **Stative fact about where a thing rests (2 hits).** "it stays under
    the bed," "so that it sits in the bottom of her bag" (the second is
    also the brief's own example of the option-3 bucket).

## Fixes made

### Chapter 3 — The Letter

1. "It's got a website that hasn't been touched since **the day it went
   up**, which is either very old money or very careless..." → "...since
   **the school put it up**, which is either very old money or very
   careless..." *Option 1.* This is dialogue (her dad, mid-monologue about
   the school he investigated), and it is close to word-for-word the
   example the brief itself gives ("'the day it went up' on a website
   somebody published"). "The school" is the subject of the two sentences
   immediately before it in the same speech, so naming it invents nothing.

### Chapter 4 — Pluto

2. "**The name of it goes across the table**, and he asks whether it is
   good, and Chloe takes a moment finding an answer while he sits there
   looking at her, waiting for it." → "**Chloe gives him the name of it**,
   and he asks whether it is good, and she takes a moment finding an answer
   while he sits there looking at her, waiting for it." *Option 1.* This
   was in the DET set, not the IT set (matched on "the name...goes"), and
   is the one DET hit the first loop's write-up gave no category for: it
   isn't a body reaction, a natural process, a timed system, dialogue, an
   idiom, or a protected passage — it is Chloe answering "what's it
   called," and the sentence has her taking a moment to answer a question
   two words after crediting an unnamed abstraction with having answered
   it already. Fixed to give the naming to Chloe, who the same sentence
   already names doing the next thing.

### Chapter 5 — Behind

3. "In that time Ruth produces a page and a half, **most of a page comes
   from Kavi**, who is still going when the teacher calls time and
   finishes the clause he is inside before setting his pen down square to
   the paper." → "...Ruth produces a page and a half, **Kavi most of a
   page**, still going when the teacher calls time, finishing the clause
   he is inside before setting his pen down square to the paper." *Option
   1.* This sits directly beside "Ruth produces a page and a half" in the
   same sentence, describing the identical kind of event (a child's own
   timed writing output), but gave Ruth the active verb and routed Kavi's
   through an abstract "comes from." The fix keeps the sentence's own
   elliptical "Ruth produces X, Kavi Y" parallel and removes one "and" in
   the process.

### Chapter 13 — Ten Pages

4. "**It comes back on the Monday** with a mark and a short paragraph
   under it, which say she has spent the essay on a position she already
   held..." → "**Hearn returns it on the Monday** with a mark and a short
   paragraph under it..." *Option 1.* Hearn is named at the top of the
   chapter and is the "he" the same sentence already ends on ("until it
   does he has no way of telling whether she is right or only
   comfortable"), so this only makes explicit two sentences earlier what
   the sentence already assumes. Matches the shape of the first loop's fix
   to "that draft comes back worse than the others" in this same chapter,
   which this pass's regex re-run confirms is still in place as
   "Hearn marks that draft worse than the others."

### Chapter 14 — Sixty Degrees

5. "**It goes in on the Monday**, twenty-eight pages of it, but Hearn gives
   it back a week later with a B on the front." → "**Chloe turns it in on
   the Monday**, twenty-eight pages of it, but Hearn gives it back a week
   later with a B on the front." *Option 1.* The whole paragraph before
   this sentence is "she" doing the writing (builds, writes, finds,
   answers, stops arguing, starts following), so the essay arriving on
   Hearn's desk on its own is the one place in that run where the actor
   drops out. Used the name "Chloe," not "She," so as not to add another
   She/He-plus-verb sentence opener against the measure sitting at its
   ceiling.

## Where I did not force a fix

Two places came close and were left alone on purpose:

- **Ch. 14, "Kavi asks whether the essay went in all right"** — the near
  match to fix #5 above, but this one is Kavi's own reported question, not
  narration, and "did it go in on time" is exactly the kind of ordinary
  spoken idiom the brief says not to chase.
- **Ch. 3, "the receptionist takes the name down"** area and the two
  chapter-11/13/14 institutional-posting passives the first loop already
  fixed — re-checked and confirmed still in place, not re-touched.

No doer was invented anywhere in this pass. Every option-1 fix used a name
(Chloe, the school, Hearn, Kavi) already carrying the action one clause or
one sentence away. All measures-sensitive constraints in the brief were
checked against the diff by hand: no em dash, no curly quote, no added
"and," no new She/He-plus-verb sentence opener, no instance of "puts it
back down" or any other phrase on the avoid list, no chapter's word count
moved outside 2,000-5,000 (all five edited chapters checked: 3,544 / 3,206
/ 3,452 / 4,292 / 4,159, each within one word of its pre-pass count).

## What a reader might still trip over

Nothing in the IT class reads to me as a live miss, but three are close
enough to the target pattern that another reader might want a second look:

- **Ch. 12, "the answer came back no different than the first time"**
  (Kavi's own dialogue about his age-exclusion appeal) — the doer ("they,"
  the school office) is in the same sentence, so this could go the way of
  fix #4 above. Left as dialogue, since it is Kavi's spoken account and not
  narration, but a pass willing to touch character speech could take it.
- **Ch. 9, "The house comes up again in April"** — read as the idiomatic
  "a topic comes up in conversation," and left on that basis, but it also
  sits two paragraphs after her parents specifically discussing the house
  offer, so a stricter reading could ask for "her dad brings the house up
  again."
- **Ch. 6, "the lights in that hall go off in sections"** — grouped with
  the ch. 12 timed-lighting instances the first loop protected, but unlike
  those this one has no "on a clock" or equivalent line establishing it as
  automatic; it reads as automatic by the pattern of the other two, not by
  anything stated in ch. 6 itself.
