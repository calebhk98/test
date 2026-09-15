# Dialogue Fix Pass — Log

Owner chapters: 13, 17, 21, 22, 23

## Plan
- Read passes/WHY_HIGHER.md in full first.
- Read characters/ for voice.
- Apply narrow fixes per report guidance.
- Grade before/after each chapter.
- Run build_manuscript.py at the end.

## Read: WHY_HIGHER.md, RUTH.md, SAM.md
Guidance distilled: (1) leave drill/command register alone (Kowalczyk, Voss,
Aymar corrections, Sam's decisions); (2) give reasoning/teaching/justifying
speech its logical joints (because/so/though), not just more words — Ruth's
"Six is me" (ch13) is the named example; (3) ordinary peer banter clipped by
default (no world-logic reason) gets the second half of a thought; (4) at
highest-stakes beats let the narrator risk one generalising sentence — ch13's
December essay doldrums and ch17's dinner-table aftermath are named.

## Baseline negative-space check (all 5 owned chapters, before any edits)
- 13_ten_pages: 8.7% (already above the 5% ceiling, pre-existing)
- 17_fourteen: 7.2% (already above, pre-existing)
- 21_the_applications: 5.9% (already above, pre-existing)
- 22_the_offer: 3.8% (pass)
- 23_the_first_one: 1.7% (pass)
This is a separate, already-completed pass's territory (see
passes/NEGATIVE_SPACE_BRIEF.md — "one agent, a named set of chapters,
nobody edits a file outside their set"). Ch13/17/21 already exceed 5% before
I touch them. My constraint is not to add to that count with my own new
sentences — I'm checking negative-space delta on every edit, not doing a
negation sweep.

## Survey of chapters 21, 22, 23 against the four items
Read in full. Findings before editing:
- Ch21 (applications): already runs "reasoning register" correctly throughout
  (Chloe's tariffs-style because-clauses, Sam's PT-score-style short reasons,
  Ruth's percentage argument at the end). No drill register present. No
  clipped peer banter found that isn't already completed by a following line.
  Word count already 3440, over the 3400 ceiling pre-edit — not adding to it.
  Plan: no edits, or at most a trivial one if found on closer pass.
- Ch22 (the offer): almost entirely reasoning-register dialogue already
  (Amberg interview, the phone call home) — already does exactly what the
  brief asks for. No drill register. No accumulation gaps found.
  Plan: no edits expected.
- Ch23 (the first one): explicitly the chapter the brief holds up as already
  doing the narrator-generalization move well ("eleven years compress into
  about forty feet of plywood..."). Sam's recruiter scene is the drill/
  command-register example to leave alone. Word count already 3723, over
  budget pre-edit.
  Plan: no edits expected; this chapter is the model, not a target.

## Plan for ch13
1. Ruth's "Six is me" exchange — add one Ruth sentence with a "so" joint
   making the argument she's gesturing at (four people covering, not one).
2. December essay-doldrums — add 1-2 narrator generalising sentences.
3. Post-10v1 "Four's fine, everybody's four" banter — give the group (Ruth)
   the second half of the thought connecting the four-second mark to the
   full-minute drill logic.

## Plan for ch17
1. Leave the rifle/paintball drill scenes (Kowalczyk, Voss, Aymar correction)
   untouched.
2. Leave Ruth's "It's the attack" sound-design scene untouched — brief names
   it as the clearest evidence of deliberate design.
3. Leave the dinner-table dialogue itself untouched (mother's withheld
   reasoning is the right kind of repression per the brief's own test).
4. Add 1-2 narrator generalising sentences in the dinner-table aftermath
   paragraph (kitchen retreat / plate-stacking / TV-hold beat).

## Edits made — ch13 (chapters/13_ten_pages.md)

1. **Ruth's "Six is me" exchange.** Added one sentence to Ruth's existing
   speech: "So the six should be on whoever wrote the drill and left it
   that vague, not on the one of us who noticed first." This gives her the
   argument the report says the scene gestures at and cuts away from,
   using her established assertion-then-consequence shape (see her
   signature line "That's not an argument, that's an outcome... so we are
   losing marks"). Did not touch Chloe's lines or add a hedge.
   First draft used "without saying," which trips the negative-space
   regex (`\bwithout \w+ing\b`); rewrote to "and left it that vague" to
   avoid adding to that count.

2. **December essay-doldrums.** Added two narrator generalising sentences
   in the run where Hearn hands back a blank mark and the essays plateau:
   "Three lines she could argue with. A mark with no line under it leaves
   her only her own doubt to argue against, and that's the harder version
   of being told she's wrong." and "A plateau and a beginning look exactly
   alike from inside the same week; only which way the next one goes tells
   you which one you were in." Both are one-sentence aphorisms in the
   register Ch23 already uses ("Eleven years compress into about forty
   feet of plywood..."), placed at the chapter's lowest-visible-progress
   beat per the brief's guidance item 4. First draft of the first one used
   "Nothing under the mark gives her nothing to push against" — two
   negative-space hits — rewritten to "no line under it... leaves her
   only" to avoid the regex.

3. **Post-10v1 peer banter ("Four's fine, everybody's four").** Added one
   line, attributed to Ruth: "'A minute's the whole fight,' Ruth says, arm
   still over her eyes. 'Four's just where you ran out first.'" This is
   the ordinary-peer-banter accumulation case (item 3) — exhausted kids
   trading clipped lines with no world-logic reason to stay clipped — and
   gives the exchange its missing second half without touching Sam's
   lines, which stay exactly as flat as they were (Sam's dial: one flat
   clause, no subordinate clause).

Left alone in ch13, per item 1: the Kowalczyk 10v1 explanation, the Watch
briefing/scoresheet reading (drill/command register), and the Thanksgiving
tariffs exchange with her father (already fully reasoned, quoted approvingly
in the brief). Also left "Then how come you're not miserable about it any
more?" / "I don't know" at the chapter's end — Chloe's flatness there is
real uncertainty, not a suppressed argument, so it fails the report's own
test for a fix.

### Grade: 13_ten_pages, before -> after

| metric | before | after |
| :-- | --: | --: |
| word count | 3222 (pass) | 3324 (pass) |
| Flesch-Kincaid | 5.1 | 5.1 |
| Lexile | 938.6 | 940.9 |
| ARI | 4.7 | 4.7 |
| negative-space % | 8.7 (FAIL, pre-existing) | 8.5 (still FAIL, but did not rise) |
| sentences with subordination % | 20.1 | 19.6 |
| metrics at goal | 7 of 22 | 7 of 22 |

Negative space was already 8.7% before I touched the chapter (a pre-existing
condition from before this pass — see baseline note above; full negation
stripping is a separate, already-scoped pass per NEGATIVE_SPACE_BRIEF.md,
not this one). My net effect was to hold it essentially flat (8.7 -> 8.5,
i.e. a slight decrease) rather than add to it, by avoiding "without ___ing"
and doubled "nothing" constructions in my own new sentences. I could not
bring it under the 5% ceiling within this chapter without doing the fuller
negation sweep that's out of this pass's scope.

## Edits made — ch17 (chapters/17_fourteen.md)

1. **Dinner-table aftermath.** Left the confrontation dialogue itself
   completely untouched (mother's clipped "It is not just school." / "It's
   like clays but harder." / "What in God's name is clays?" stays exactly
   as written — this is the report's own example of the right kind of
   repression, the unsaid thing too large for a stated line). Added two
   narrator sentences in the aftermath beat, both avoiding "nobody" /
   "isn't" / "without ___ing" constructions:
   - After "...gets up and starts stacking plates still half full.":
     "The real sentence stays exactly where it's been all evening, buried
     under the one about pie: how much of the last four years already
     happened at a range and a mat four hours from this table, with her
     mother getting it secondhand and six months late. The kitchen gets
     six minutes and the plates get stacked instead, and that turns out to
     be as much of the sentence as the room can hold."
   - After "'That's a hold. That is a hold, that's been a hold all
     night,' her mother says.": "It's the closest either of them comes all
     night to naming what's actually been going on at the table."
   These name the unsaid thing at the meta level (that it's staying unsaid)
   without putting the actual repressed sentence in anyone's mouth, per
   guidance item 4 and Ch23's own technique.

Left alone in ch17, per item 1: Voss's dry-drill setup, Kowalczyk's
self-defense pairs/rounds calls, Aymar's stopwatch correction and Voss's
"The card says nine, Aymar" reply (all drill/command register). Left Ruth's
"It's the attack. Every time I fix the attack it breaks the tail." scene
completely untouched — the report names this exact passage as the clearest
evidence the clipped-dialogue design is deliberate, not a gap. Left the
Sam/Odile "Ruth's already bored" / "Ruth was bored in the briefing" beat and
the Priya/Kavi/Ruth commentary on Sam's date alone: Ruth already carries a
full reasoned rant in that scene ("He had a whole Thursday afternoon and
every building on this campus and he didn't know...") so it already passes
the report's own test — someone in the scene is available to say the
reasoned version, and does.

### Grade: 17_fourteen, before -> after

| metric | before | after |
| :-- | --: | --: |
| word count | 2954 (pass) | 3046 (pass) |
| Flesch-Kincaid | 5.6 | 5.7 |
| Lexile | 985.1 | 991.8 |
| ARI | 5.3 | 5.5 |
| lexical diversity sTTR | 40.2 | 39.3 |
| negative-space % | 7.2 (FAIL, pre-existing) | 7.1 (still FAIL, slight decrease) |
| metrics at goal | 11 of 22 | 11 of 22 |

Same story as ch13 on negative space: pre-existing, held flat rather than
raised. Lexile moved from 985.1 to 991.8, closer to the 1000 target, on two
sentences of added narratorial generalization — the cheapest technique per
the report's own claim.

## Chapters 21, 22, 23 — no edits made

Read all three in full against the same four items before deciding. None
needed changes:

- **21_the_applications**: already runs the reasoning register correctly
  throughout (Chloe's "because getting it to six hundred is harder than
  getting it to four thousand," Sam's PT-adjacent "at that length they're
  guessing," Ruth's closing percentage argument). No drill/command register
  present to leave alone. No clipped peer banter found that isn't already
  completed by a following line in the same scene. Word count already 3440,
  over the 3400 ceiling before I looked at it; adding anything would only
  push it further over, so I left it. Graded 17 of 22 at goal already.
- **22_the_offer**: almost entirely reasoning-register dialogue already
  (the Amberg interview, the phone call home) — this chapter already does
  exactly what the brief is asking for elsewhere. No drill register, no
  accumulation gaps. Graded 14 of 22 at goal already; the misses are mostly
  short-sentence-run metrics, not dialogue-register problems.
- **23_the_first_one**: this is the chapter the brief explicitly holds up as
  the model for narrator generalization ("Eleven years compress into about
  forty feet of plywood and four seconds of applause") and for the
  drill/command register done right (Sam's recruiter scene, left alone).
  Graded 19 of 22 at goal already, the strongest of my five chapters. Word
  count already 3723, well over the 3400 ceiling; I did not add to it.

## Final steps
- `python3 check_edits.py --chapters 13 17`: 0 problems (no em dashes, no
  curly quotes, hard breaks unchanged, heading/date lines intact).
- `python3 build_manuscript.py`: wrote HALSTEAD.md, 35 chapters, 97,992
  words.

## Status: DONE

