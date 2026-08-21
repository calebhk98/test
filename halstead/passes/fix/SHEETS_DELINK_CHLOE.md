# De-linking CHLOE.md and the four meta sheets

Scope: `characters/CHLOE.md`, `_TEMPLATE.md`, `_CALIBRATION.md`, `_DIFFERENTIATION.md`,
`_ALLOCATIONS.md`, `CHARACTER_SHEETS.md`. No chapter was touched. No other character sheet
was touched.

Governing instruction, in the author's words: *the character sheets shouldn't be ABLE to
drift, because they shouldn't have quotations in them. It's to describe the character, not
the book.* The working test on every line was whether it would help somebody writing this
person into a ghost story.

## Result

    python3 verify_citations.py characters/CHLOE.md
    0 quotations checked, 0 not found in the manuscript.

Same for all five other files, including at `--min-words 1`. `CHLOE.md` now contains no
quotation marks at all, and one remaining `chapters/` reference: the appears-in line in the
bottom navigation block, which `_SHEET_RULES.md` explicitly permits.

Word count went from about 8,950 to about 8,100 while gaining an *Under pressure* section,
an *Age and change* treatment, a second blind spot, and a separated continuity block. No
observation was dropped for being inconvenient to paraphrase.

---

## CHLOE.md: what came out and what replaced it

### The twenty-one quotations

All gone. The twelve that no longer matched the book are marked **stale**. Each row is what
the sheet was actually trying to say, which is what it now says.

| what was quoted | now says |
| :-- | :-- |
| Her age-six self-assessment, quoted from narration (**stale**) | Her settled account of herself at six is that everybody else can manage the part of the day everybody has to do, and she cannot. Stated twice, once in the governing section and once in *Interior life*, because it is the load-bearing sentence on the sheet. |
| The table-walk line, quoted twice as her signature | The move that produces it: she converts an abstract disagreement into a concrete physical scenario built out of the room in front of her, and argues the scenario. A writer with the move can build the next one. |
| The tariff line, quoted as the second signature instance | Folded into the same description. |
| A dry concession about cut food, quoted as evidence of jokiness (**stale**) | Her wit is dry, flat and technical: a concession delivered as a fact, a technicality offered straight-faced. That describes her wit, not her capacity for delight, which is enormous. |
| Four questions quoted to prove she asks questions | She asks real questions constantly at six and seven, because she wants to know and has not learned which questions are not supposed to be asked. The thinning of them later is damage, not maturity. |
| A one-word refusal to hear a diagnosis, quoted with its scene | Kept as behaviour: she will decline the information rather than take it from a person who has already made her careful, even one she likes. |
| Icarus, clouds, the moon, named as her three protected images (**stale** line numbers) | The law rather than the list: her images come from whatever she has read lately, mapped onto something physically present, said once, flat, unexplained, never repeated, and never a joke. The list itself survives only as a one-line continuity note that the three images are hers and must not be reassigned. |
| The narrated economy she learns at six | Finish first, sit still, say nothing, written as a survival tactic for one hostile room that she later stops noticing she is running. |
| A yelling-in-Russian narration (**stale**) | Russian is what surfaces under real feeling, and it is not the language she is technically strongest in. |
| A twice-refused request to drop dance (**stale**) | She asks outright at eight and is refused flatly, twice, the second refusal pre-empting the other four subjects she might have come about. |
| The Latin-is-cheating justification (**stale**) | She defends the choice on the grounds that the year pays for itself twice, because the language is already sitting inside two she has. |
| A friend saying twice that a drawing is a hand | Her fortieth attempt at her own left hand comes out accurate, and the friend who picks it up says so twice, unprompted, because it is a hand. |
| The four-millimetre riser justification (**stale**) | Kept in her own words on the sheet: nobody is going to measure the steps. It is the sentence that carries her father's whole relationship to finished work. |
| Her mother's line about local money (**stale**) | It is the kind of street where nobody nearby has money to give away, and her mother will say so flatly if anyone suggests otherwise. |
| An aside about taking an afternoon off (**stale**) | She can take a full afternoon off without friction, which is the ease of steady salaried work rather than hourly. |
| The line about summer novels leaving nothing behind | Kept as description: the novels she reads over those summers leave nothing behind them and are read purely to switch off. |
| A tactical self-assessment at twelve (**stale**) | She is small and light and will use it tactically when a plan needs somebody who reads as harmless. |
| Her flat closing of the riding friendship (**stale**) | Told plainly that it had been fun, she does not soften it: she agrees, and says she had been waiting for the fun to arrive. |
| Two pivot lines quoted as a habit (**stale**) | She pivots away from a vulnerable moment with a flat fact rather than a feeling. |
| An adult's warm refusal (**stale**) | An adult telling her to slow down and wait for the room is the thing she likes least in the world, and the fastest way to shorten her answers, even said kindly. |
| One line she tries when asked to explain herself | She tries once, and what she has is that nobody was ever mean to her, not once, which is true and explains nothing. |
| Two quoted outbursts at six and seven | Saying she hates someone, saying she cannot do it anymore, and hours of unrationed talking are all correct for her at that age. When she breaks, she breaks out loud. |
| A misattributed image quoted from another character's mouth | Off the sheet entirely. It is a manuscript and style-guide defect, recorded below. |
| A narration line quoted to prescribe a cut | Dropped. See *Corrections on facts*. |

### The statistics

Removed under rule 3, converted to the tendency each was measuring:

- **8.2 and 6.0 words per line.** Now: long is her default with people she trusts, and the
  short register is the exception aimed at particular people. The sheet says outright not
  to write her to a word count, and says why the old averages were misleading: they were
  measured over a draft in which most of her lines fell in guarded scenes.
- **48% of lines three words or fewer.** Same treatment.
- **0% hedging.** Now: she does not open a claim with a hedge, and an unhedged *I do not
  know* is her commonest answer when hurt.
- **0% questions.** This one was a false artefact of a script that could not see untagged
  dialogue, and the old sheet already said so in the same table cell. Now stated as a
  positive fact about her: she asks constantly at six and seven.
- **230+ attributed lines, front-loaded into chapters 1-15.** Gone. It is a fact about a
  draft.
- **3/10 jokiness, 10/10 emotional range.** Converted to descriptions.

### The stale line references

Not corrected, removed. A sample of the drift, which is what makes the case that the
citations should never have been there:

| the sheet said | the manuscript has |
| :-- | :-- |
| Icarus at `01_before.md:53` | `01_before.md:121` |
| the fraction-division floor scene at `05_behind.md:49-53` | `05_behind.md:91` |
| the table-walk line at `05_behind.md:95` | `05_behind.md:179` |
| the room-shaped object at `04_pluto.md:47` | `04_pluto.md:113` |
| Deb at `28_nineteen.md:17, 614-620` | the file is 284 lines long, and line 17 is about college credits, not Deb |

Around thirty citations of this kind were carried on the sheet. All are gone.

### Substance that was kept and strengthened

Everything the brief named survives, most of it expanded rather than trimmed:

- **The governing section** is still first and still says it wins over anything below it
  that contradicts it.
- **She does not know she is gifted** now carries a paragraph reconciling the sheet with
  `passes/CALIBRATION_AUDIT.md`: two samples, neither of which ever tells her what she is;
  contrary evidence rationalised rather than absorbed; and the audit's sharpest point, that
  she is not modest about her ability because modesty would require knowing there is
  something to be modest about.
- **Openness is natural, hiding is a bruise.** Kept verbatim in substance, with the three
  proofs rewritten as behaviour rather than as scenes.
- **She needs the mechanism.** Expanded: it is not vanity, not a refusal of the rule, and
  the resolution is quiet and private rather than triumphant.
- **She sorts adults by fairness, not rank.** Kept, with the point made explicit that rank
  means nothing to her in either direction.
- **She feels everything at full size.** Kept whole.
- **Reading is not an intellectual act.** Kept, with the writer-useful consequence added:
  it is the most reliable early-warning signal anyone around her has.
- **Both age-scoping corrections** are kept and stated as corrections, so they cannot be
  reverted by somebody working from an older copy: the compliant minimum is a bruise that
  mostly heals, and the Mandarin difficulty is a problem at nine rather than a permanent
  ceiling.
- **She is physically six** became **She is the age she is**, which is the portable form of
  the same note.

### Sections added

- **Under pressure**, which `_SHEET_RULES.md` calls the most portable section and usually
  the thinnest. The old sheet had this material scattered across four headings.
- **Trained skill versus raw speed**, pulled out of the *Body* bullet list because it is the
  one place a writer needs two apparently contradictory facts at once.
- **A second blind spot**: she reads a ranking as a statement about her ability rather than
  about the company she is in, in both directions.
- **Age and change** absorbed into the governing section rather than made a separate
  heading, since it was already written there.
- **A separated continuity block** at the bottom. Delete it and the sheet is still complete.

---

## Corrections on facts

**1. Her twenty-first birthday.** The sheet's continuity list said she turns twenty-one in
June. The manuscript says August, twice over: `30_cleared.md:113` states it directly, and
`33_the_other_one.md:129` puts the birthday inside a five-week stretch that is consistent
with August and not with June. The sheet's own header already said she was born in August
2005, so the sheet contradicted itself. Now August, with a note saying the June version was
wrong so nobody restores it.

**2. The chapter 30 prescription, dropped.** Known problem #2 said her defining trait was
stated directly in narration as *She does not read the result as information about herself.
She reads it as having sat an exam*, and instructed a rewriter to **cut the second
sentence**. The manuscript has already made the fix, and made it the other way round:
`30_cleared.md:25` now reads *The result arrives by mail six weeks later. She reads it as
having sat an exam.* The telling sentence is already gone. Following the sheet would have
deleted the surviving dramatised half and left the beat with nothing in it. Dropped
entirely rather than rewritten.

---

## Things in the old sheet I believe were simply wrong about the character

These are separate from the hard-linking. Flagged for the author.

**1. The signature was described as thin, and it is not.** Known problem #3 said only two
clean instances of her parallel-scenario opening existed across the whole reading list.
There is a third, and it is one of her best: `13_ten_pages.md:77`, where she explains
reading a barrel by asking you to imagine standing behind somebody holding a hose and
watching where the hose is pointing rather than watching the water. Three instances, and
the construction is productive rather than rare.

**2. Known problem #4 had the same scene backwards.** It listed the paintball barrel
explanation as an example of her *losing* her parallel-scenario shape and taking on another
character's clipped-fact shape. That passage is the shape, executed cleanly, and it is at
`:77` rather than the `:79` the sheet cited. The general worry behind #4 may still be sound,
but its headline example disproves it. I have kept the portable half of #4, that her lines
should build or reference a physical parallel, in *Do not confuse with*, and dropped the
claim about that scene.

**3. The signature was defined as a phrase rather than as a construction.** Writing it as an
opening formula is what made it look thin and what would have produced a catchphrase if a
writer had tried to add instances. It is a move, not a phrase, and the sheet now says so.

**4. An MBTI conflict between two files I own.** `CHLOE.md` said INTJ and the index said
INFJ. I harmonised to INTJ, the sheet's own value. If INFJ was the considered choice, the
index is the file to change back.

**5. The Deb relationship was probably written from the wrong scene.** The citation pointed
at a line that does not exist and a line about college credits. The behaviour described,
undemanding daily company with no bargain attached and nothing held back, is supported by
the material that actually is there, so I kept it. Worth a second look by whoever owns the
Deb sheet.

---

## Close to the line, and kept deliberately

- **The four-millimetre riser and the reason for it.** The sentence about nobody measuring
  the steps is the sheet's own paraphrase now, not a quotation, but it is close to the
  book's phrasing because it is the exact shape of her father's attitude to finished work
  and the sheet loses something real without it.
- **The specific numbers in her biography**: eleven languages in a fixed order, ranked
  ninetieth of ninety, four hundred photographs, eleven hours of sleep in a depression, the
  fortieth attempt at a hand. These are facts of a life rather than statistics computed from
  a draft, and rule 3 does not reach them. They are what makes her concrete.
- **Naming the school.** Halstead appears on the sheet. The portable statements are written
  so the school could be any place that fits her, and the governing bullet is phrased as
  *the place where the work makes sense is not special to her*, but pretending she has no
  biography would cost more than it gained.
- **`CURRICULUM_GRID.md` and `_ALLOCATIONS.md` cross-references** are in the continuity
  block only. They point at other reference documents rather than at the manuscript, so they
  cannot go stale the way a line number does.
- **The three named invented images.** Reduced to a single continuity note that they are
  hers exclusively. The images themselves are book-specific; the note exists because another
  document currently gives one of them away, and losing the note would lose the guard.

---

## The four meta files

### `_TEMPLATE.md`

The most important of the four, because it is the mould. Six places in it actively required
the disease and have been rewritten:

| was | now |
| :-- | :-- |
| *Name the single most characteristic line and quote it exactly with its file and line number.* | *Instead of naming their most characteristic line, name the move that produced it, so a writer can produce the next one.* |
| Dials rows asking for measured words per line, measured terse %, measured hedge %, measured question % | Qualitative rows, plus a boxed **No measured statistics** rule explaining why, including the false-zero artefact |
| *Signature: two real examples from the text if they exist* | *Described as a construction. Do not reproduce an instance of it.* |
| *Quote exactly, with file and line, when quoting.* | Deleted, replaced by the no-quotations rule stated at the top of the file |
| *Where the manuscript shows something, quoting it is still the strongest way to say it.* | Deleted. This was the single line most responsible for the problem regrowing |
| *Known problems: the specific places they are off-voice, with file and line* | Deleted as a sheet section. Draft defects belong in `passes/`, and the rules list says so |

Added to the template, from `_SHEET_RULES.md`: the lunar-colony test at the top, and new
sections for **Under pressure**, **How they treat people**, **Age and change**, **blind
spots** and **what they do instead of admitting the fear**, plus the separated
**book-specific navigation** block with the delete-it-and-check instruction.

### `_CALIBRATION.md`

The school-enrolment section stayed, as instructed. It is a world fact and the curve it
describes is the useful part. Two things were cleared out of it:

- The quoted phone call establishing that the students come from all over. Now stated as
  what the school told her mother, in the sheet's own words, with the four-hour-drive
  detail kept because it is what makes the geography argument land.
- Three chapter-and-line citations supporting the roll numbers, and the quotations attached
  to them. The reconciliation survives in full, including the important part: **the two
  different student counts have been logged as an inconsistency and are not one**, because
  the school is genuinely a different size early and late.

Also changed: the opening now points at `_SHEET_RULES.md` alongside itself, and the *no
tags* rule no longer ends by telling sheet writers to quote the manuscript.

### `_DIFFERENTIATION.md`

- **Axis 3** was a table of measured percentages with numeric targets. Replaced with
  directions. The two deliberate reversals it existed to record, that Theo should be the
  cast's only hedger and Meg its question-asker, are kept and are now easier to read.
- **Axis 4** quoted three signatures. All three are now descriptions of the construction,
  which is also more useful: a writer can build a new instance from a description and can
  only repeat one from a quotation.
- **Axis 1** had a quoted schema in Eli's row; rewritten as prose.
- **Axis 5** quoted the deflating-literalism image. Now described as what the move does.
- **Known collisions** kept as a numbered list of the rule each illustrates, with the
  chapters and line numbers moved into this file, below. Two of the five turned out to be
  already fixed in the manuscript once the line numbers were checked.

### `_ALLOCATIONS.md`

Two line citations, both removed: the one supporting Ruth's Portuguese and the one
supporting the spelling of her surname. Both facts are kept as facts. A line was added
saying that everything on the page is a fact about a person and nothing on it should ever
acquire a quotation or a line number, since this is the file most likely to attract one.

### `CHARACTER_SHEETS.md`

- The core-seven dials table, six columns of measured statistics, is now a one-line voice
  description per character.
- Mention counts, quoted-line counts and scene counts for the other students are now
  qualitative.
- Four quoted signature lines in the staff and outside-adults tables are now descriptions.
- The blind-reassignment statistic for the parents is now stated as the finding rather than
  the number.
- The note that sheets quote the manuscript with a file and line is replaced by a pointer to
  `_SHEET_RULES.md` and a statement of the opposite.
- The reference-error table, the self-collision list and the open contradiction are
  summarised there and recorded in full below.

---

## Manuscript and reference notes rescued from the sheets

These left the character sheets because they describe the draft rather than any person.
They are real and actionable, and `_DIFFERENTIATION.md` and `CHARACTER_SHEETS.md` now point
here for them.

### Open, and worth someone's attention

1. **`STYLE_GUIDES.md:39` lists the room-shaped object among Chloe's protected invented
   images. It is Sam's line**, at `chapters/04_pluto.md:113`. Either strike it from her
   protected list or move the line into her mouth in that scene. The fix belongs in that
   scene, not further on. This is the only one of the old known problems that is both still
   live and still correctly diagnosed.
2. **Several age-six lines carry her age-sixteen rhetorical polish**, including the
   four-books argument at `chapters/01_before.md:23` and her private read on Dr. Prentice at
   `chapters/02_march_4th.md:28`. Flagged for the author's judgment; no rewrite proposed.
   The portable half of this is now on her sheet, under *Do not write her as*: at six she
   has the perception and not yet the phrasing.
3. **Chapters most likely to need the openness correction applied**, on reasoning rather
   than a fresh read: `chapters/01` through `08`, where she should still be open and is
   progressively burned; `chapters/04` through `06`, the camp chapters, where she is among
   friends for the first time and should be at her loudest; and any scene from `chapters/09`
   onward where she is with the four of them and the dialogue reads clipped. Any chapter
   revised against the pre-correction version of her sheet should be re-read against the
   current one, earliest chapters first.

### Closed

4. **The chapter 30 narration.** Already fixed in the manuscript. See *Corrections on facts*
   above.
5. **The thin signature and the barrel scene.** Both wrong. See the flagged list above.

### Collisions the manuscript makes on itself

6. **Already fixed, and the meta files had not caught up.** Both duplicated-sentence
   collisions the notes recorded are gone from the manuscript. The six-word sentence the
   notes had appearing twice in `chapters/32_the_money.md` now appears once, at `:88`, and
   the one they had appearing twice in `chapters/35_nine_minutes.md` now appears once, at
   `:105`. A full-text search finds no second instance of either. The two source documents
   also disagreed with each other about where the duplicates were, which is the same
   staleness the sheets had. Both entries are closed.
7. *(merged into 6.)*
8. `chapters/13_ten_pages.md`: Sam is given a short why-that-number question twice, which is
   Kavi's mechanism-interrogation move in Sam's mouth.
9. Meg and Dave both use exact-phrase repetition under stress. Assign it to Meg per Axis 4
   and take it off Dave. **Not** the exchange at `chapters/03_the_letter.md:64`, which is one
   deliberately echoing the other and works.
10. Eli and Theo collapse into identical low-stakes filler. Whoever speaks second should be
    doing their Axis 2 move instead.

### Reference-document errors, all verified against the manuscript

11. The notes make a particular maternal line Meg's defining one, cited six times across the
    beta notes and the synopsis. It does not exist anywhere in the manuscript.
12. Bell is masculine, twice, `chapters/14_sixty_degrees.md:13` and `chapters/15_twelve.md:29`.
    The notes flag the gender as unstated.
13. Kowalczyk is feminine throughout, `chapters/13_ten_pages.md:39` and
    `chapters/17_fourteen.md:57`. The notes say male.
14. Sandoval is named only in `chapters/18_fifteen.md` and is feminine. The claimed
    chapter-14 conflict does not exist; there is no Sandoval in chapter 14.
15. Fen is named as a girl in `chapters/18_fifteen.md:111` and returns three times. The notes
    say gender unstated, one line, never returns.
16. The father is named repeatedly by Meg. The notes say he is unnamed.
17. The room-shaped object, as above.
18. The MIT four-percent call is Sam's; Kavi is not in the scene. The notes attribute it to
    Kavi.
19. Mr. Baptiste is the synopsis's unnamed mathematics teacher and appears nowhere in the
    notes under his own name.

### Not errors

20. **Two different characters are called Deb.** A swim instructor at camp when Chloe is
    seven, `chapters/05_behind.md:55`, and a colleague at the translation company when she is
    nineteen, `chapters/28_nineteen.md`. Twelve years apart with no connection. Names
    repeating is fine and needs no fixing.
21. **The two student-body counts.** Different because the school is a different size at the
    two points. See `_CALIBRATION.md`.

### Open contradiction

22. `chapters/10_april.md:39` has Ruth call Owen the one who would not do the water thing.
    `:103` has Kavi say he did the water thing, and the bridge, and was fine. Sixty-six lines
    apart. Kavi's line is shaped as correcting an assumption, so this may be deliberate, but
    nothing signposts it.
