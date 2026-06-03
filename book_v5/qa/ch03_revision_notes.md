# Chapter 3 Revision Notes (v5 working log)

Tracking decisions across the multi-round ch03 rewrite. Working file: `chapters/ch03.md`.

## Standing decisions

### Bead microscope (outline lines 246-253) — DEFERRED OUT of ch03
The outline marks a Leeuwenhoek bead microscope as an "ADD / first physical build"
for ch03. Decision: **do not add it here.** In ch03 Daniel is a prisoner on ~day 2-3
with no glass rod, no workshop, no lamp of his own, no freedom of movement, and no
shared language. Melting a glass bead in a flame and keeping it requires materials
and liberty he does not have until he has earned standing. Forcing it in would break
the honesty rule (premise: tech obeys material reality).
**ACTION FOR OUTLINE OWNER:** move the bead-microscope "first physical build" beat to
a later chapter where Daniel has workshop/glass access (Phase A-B, after he has some
standing — candidate around the lens/glass thread, which REVISION_DELTA E7 already
flags as planted too early in ch05). Neither the QA nor the blind read caught that the
beat was missing from ch03, so this gap is currently untracked anywhere else.

### Dialogue density — honest floor for a language-wall chapter
`analyze.py` flagged ch03 at 1.8% dialogue vs the book's ~50% target. This chapter's
premise is the total language wall: Daniel cannot converse. We will NOT fake a
conversation he can't have. Instead, per the bible's "muting problem" rule, we unmute
the Romans in their own register — quoting the magistrate, the pot-seller heckler, and
the optio in Latin that Daniel (and the reader) cannot parse. This is honest to the
language wall and raises density off the floor without inventing comprehension. Expect
ch03 to stay below baseline dialogue %; that is correct for this chapter, not a defect.

## Round log

### Round 1 (deeper-restructure pass)
Focus: de-poeticize the narration register (the thesis-breaking problem the internal
QA praised), unmute the Romans, smooth the staccato (1-5 word sentences were 26.2%),
compress the stacked interior-reflection blocks.
- Killed/plained: "hungry had started eating itself", "true in the bones", "the great
  inventor of worlds tripping over his own dead foot", "a hard little stone in a stream
  of water", "the great encircling river at the rim of the map", the "Not yet. Not for
  fourteen hundred years." staccato future-vantage.
- Removed a correctio that had crept into the food beat ("it wasn't strategy. It was
  hunger") — rewrote as pure positive.
- Added quoted Latin (Quis es? / Unde venis? / Quid est? / Auferte. / pot-seller line /
  Ita) — Daniel does not understand any of it; honest unmuting.
- Preserved plants: phone 11%, offline-map-app crutch, map east-to-west with the two
  western continents drawn with conviction (ch36 seed), clerk copies map ("loose now"),
  physician summoned (healer + foreigner-slur), optio bread + name exchange, variolation
  note, bread-as-final-image ending.

### Round 2 (intersection of 4 blind reviews — harsh+neutral x Sonnet+Haiku)
Fixed the highest-consensus issues: compressed the 3 stacked post-map reflection
paragraphs and cut the worst line (the "read too much sci-fi / knowledge you can't put
back in the box" meta line, named worst by 3/4); plained "stillness of somebody used to
people waiting on his mouth to open", "smell of the whole world now", "it had company
now"; trimmed the backward-narration gloss (healer/slur, army-yes); dropped the
"Take him away. Done." gloss on Auferte for Latin consistency; dissolved the "shelf"
fragment. Confirmed working: register direction validated (the round-1-plained "big
visiting genius" line is now praised, not flagged).

### Round 3 (intersection of round-2 reviews)
- VARIOLATION RELOCATED to ch04 (user decision). Removed the note from ch03 prose;
  edited outline (ch03 MOVED-out note + checkbox; added the withheld beat to ch04 where
  the physician arrives). All 3 reviewers, both rounds, rejected it as a cold/abrupt
  author-note in ch03's prisoner scene; ch04 (Heras) is the natural anchor.
- Prose: cut "Sherlock lives" + the "movies got everything else wrong" wink; simplified
  the "dead language... deciding what to do with me" line (grounded in school-Latin);
  cut "doing sums" doubling; "seemed to step back" -> plain; trimmed Africa "nobody in
  that room" repetition; compressed the Asia geography inventory and varied its sentence
  openings (was a monotone "I + verb" list).
- OPEN/CARRIED: short-sentence (1-5 word) ratio still ~28% vs <15% target — fragment
  density is the next category to address; do carefully (some fragments are voice).
- KEPT against blind-reviewer notes (filtered vs thesis): "I'd have eaten a tire" (voice;
  split 2-2); the B-minus art-class line (thesis "ordinary kid underselling himself"
  beat, an established pattern); "It was loose now" (load-bearing plant + praised).

### Round 4 (round-3 intersection)
- De-purpled the final phone/battery paragraph (cut "the last library on earth that
  spoke my language" and "I was a learned man... checks his sources" — both reviewers'
  #1 remaining slip); trimmed para 47 (cut the "there's a thing that happens when a room
  pays attention to you" pre-announced motive); cut "already there before my brain caught
  up"; trimmed the food beat's "growing with nobody to pick it"; clarified the fetch
  gesture; merged the "Fix the boot/Fix Africa" fragment trio.
- Short 1-5-word sentences: 28% -> 25% across rounds (still above the <15% target).

### CONVERGENCE / DIMINISHING RETURNS (assessment after 4 rounds, 8 blind reviews)
The harsh panel is now recycling the same ~5 "worst lines" each round, and they are
mostly REQUIRED PLANTS or THESIS beats already deliberately kept and filtered against
the bible: the "treasure map you can't take back" reflection (ch36 plant), the B-minus
underselling line (thesis), the healer/slur decoder beat (ch04 physician setup), the
food/Atlantic-motivation beat (C9 plant). The genuinely poetic/QA-praised-but-wrong
register that started this pass is gone. Remaining objective gap: short-sentence ratio
(~25% vs <15%), which is largely the chapter's deliberate fragment voice + the
language-wall quoted Latin; pushing it to target would require flattening the voice.
RECOMMENDATION: treat ch03 as good-enough to ship pending the user's call on whether to
trade voice for the sentence-length metric.
