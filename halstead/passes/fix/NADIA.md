# Nadia fix pass — log

## Task
- Add missing characterisation to characters/NADIA.md (near top, matching CHLOE.md format for "the thing to get right first"):
  1. Labour-as-scarce-input worldview (inverse of every company/founder she studies: they ask how to need fewer people, she asks how to get enough people). Not argued, not political — a thing she notices that others don't, and the engine of what she builds.
  2. Takes on far too much — 50 things at once. Reckless AND justified simultaneously, unresolved, unremarked by narrative or other characters.
- Work both into chapters/27_nadia.md (May 2024, company 40 people / 11 months old, industrial espionage traced in a week). Use hiring scenes to carry labour idea. Let overload show in action, not commentary. Nobody explains it, she doesn't win an argument about it.
- Do NOT touch chapter 23 (see passes/fix/N23.md for context, another agent owns it).
- Finish: python3 build_manuscript.py && python3 grade.py --one chapters/27_nadia.md
- Watch negative-space line in grading — prior agents have spiked it. Keep prose grounded/concrete, avoid abstract narration of absence.

## Status
- [ ] Read FIX_BRIEF.md
- [ ] Read CHARACTERS/CHLOE.md for format reference
- [ ] Read characters/NADIA.md current state
- [ ] Read chapters/27_nadia.md current state
- [ ] Read passes/fix/N23.md for context on ch23 rebuild (don't touch, just context)
- [ ] Edit characters/NADIA.md
- [ ] Edit chapters/27_nadia.md
- [ ] Build manuscript
- [ ] Grade chapter 27
- [ ] Iterate if negative-space or other issues flagged

## Notes (appended as I go)

## Investigation findings (2026-08-21)

- `characters/NADIA.md` ALREADY had the full "thing to get right first" section
  covering both the labour-scarcity worldview and the fifty-things-at-once
  overload, near the top, in CHLOE.md format (what it is / how it shows /
  how a writer gets it wrong). This was present at session start (git log
  shows it was part of an already-committed state, not something I wrote).
  Verified it matches the brief: no theory explained to the reader, no
  argument won, "sometimes it costs her nothing at all" framing for the
  reckless/justified duality. Left this section untouched — it already
  satisfies job 1.
- `chapters/27_nadia.md` (job 2) did NOT yet carry the labour idea or an
  explicit overload beat beyond what the plot already implied. Baseline
  grade before edits: word count 1898 (FAIL, needs 2000-3400), negative-space
  0.0% (well clear of the <=5 ceiling).
- Confirmed I have not touched chapters/23_the_first_one.md (already rebuilt
  by another agent per passes/fix/N23.md).

## Edits made to chapters/27_nadia.md

1. Investigation-week paragraph (between the "third/fourth morning" beat and
   "She keeps the rest of it to herself"): added a short paragraph — "None of
   it moves anything else on her list..." — tying the espionage tracing to
   three other things running in parallel that same week: the housings
   tolerance fix, payroll, and grading that month's take-home tests (this
   last foreshadows the hiring section). Shows the fifty-things-at-once
   overload in action, unremarked by anyone.

2. Hiring section, inserted before "She interviews four hundred people...":
   a paragraph about her writing job postings herself (labor-contract shape,
   just what the job needs and pays) versus two competitors' postings
   bragging about doing more with fewer hands — and her own board flagging
   her hiring pace, which she reads and answers by posting two more roles.
   Carries the labour-scarcity idea entirely through action/contrast, no
   internal monologue, no argument, nobody explains it.

3. End of the "She hires excellent people anyway..." paragraph: added a
   vendor-pitch beat — a company selling a tool to flag the exact skill gap
   she's hiring around (machine-scored, headcount-reducing) — she takes the
   calls, says she'll think about it, and hires two more people instead.
   Direct dramatization of "get enough labour" vs. "need fewer people,"
   again with no comment from her or anyone else.

All new sentences checked by hand against prose_grade.py's NEGATIVE regex
(doesn't/does not/didn't/wasn't/never/nobody/no one/nothing/none of them/
without -ing) to avoid spiking negative-space — rewrote a couple of drafts
that would have tripped it (e.g. "hasn't opened the hood" -> "still guessing
at what's under the hood"; "doesn't call back" -> "the call goes to
voicemail" -> ultimately cut in favor of the vendor-call version above).

Did not touch: the espionage confrontation scene, the chat blocks, the
opening company-description paragraph, or anything in characters/NADIA.md
beyond reading it.

## Next: build + grade

## Build + grade results

`python3 build_manuscript.py` -> "wrote HALSTEAD.md: 35 chapters, 97,690 words" — no gap/duplicate/heading warnings.

`python3 grade.py --one chapters/27_nadia.md` before -> after:

- word count: 1898 (FAIL) -> 2135 (pass, target 2000-3400)
- negative-space sentences %: 0.0 -> 0.0 (pass, held at zero — did not spike it)
- sentences per paragraph: 3.2 (FAIL) -> 3.1 (pass)
- overall: 16/22 at goal -> 19/22 at goal

Remaining fails (all pre-existing, present before my edits, unchanged by them
in kind): sentence-length variation CV, words per paragraph (78.9, driven by
several long pre-existing paragraphs e.g. the interview/edge-case paragraph
I did not touch), sentences with a relative clause %. These are structural
properties of paragraphs I was not asked to rewrite; per FIX_BRIEF's
"smallest change" rule and the task's specific scope (work the two ideas
into the hiring scenes without spiking negative space), I left them alone
rather than restructuring paragraphs outside my brief. Flagging here rather
than fixing unrequested.

## Status: DONE

- [x] Read FIX_BRIEF.md
- [x] Read CHLOE.md for format reference
- [x] Read characters/NADIA.md — already had the required section, untouched
- [x] Read chapters/27_nadia.md
- [x] Read passes/fix/N23.md for context (chapter 23 not touched)
- [x] characters/NADIA.md — no edit needed, already satisfies job 1
- [x] chapters/27_nadia.md — 3 insertions made (investigation-week overload
      beat, job-postings labour-idea beat, vendor-pitch labour-idea beat)
- [x] build_manuscript.py — clean
- [x] grade.py --one chapters/27_nadia.md — word count now passes,
      negative-space held at 0.0%, 19/22 goals met (up from 16/22)
