# QA — Chapter 23: The Things That Don't Work
**Reviewer:** QA Agent (claude-sonnet-4-6)
**Date:** 2026-05-29
**Word count:** ~4,580 words (raw file count ~4,584 including headers)
**V2 change notes applied:** Yes — stone-cutter's yard kept per V2 note; both economic defeat and capability argument present; no corrections needed from V2 BLOCKER list (chapter was STATUS: PASS)

---

## 1. Plot Beats

*(Expected beats from `updated_ch19_36.md`, ch23 entry)*

| Beat | Present? | Notes |
|---|---|---|
| Mechanical clock escapement failure (memory gap) | YES | Rendered in full at L15–L29; escapement specifically named as the gap; Hermes dialogue earns its place |
| Water clock substitute (clepsydra with float mechanism) | YES | L33–L47; the float-and-pointer mechanism described in functional detail; keeps inconsistent time; Tyche corrects by the sun |
| Telescope failure (Roman glass striae/bubbles) | YES | L51–L79; *striae* named and illustrated; chromatic aberration rendered sensory; Demetrios introduced |
| Rail cart demo worked, NOT adopted (economic defeat) | YES | L83–L111; both the capability argument (mine inclines, heavy loads) and the economic defeat ("you own the men, Maximus") are each present and individually defeated per V2 requirement |
| Marcia voices the economic logic | YES | L97 and L101; "You own the men, Maximus" / "It is a machine for a man who has to pay his haulers" |
| Daniel recommits to "the books" as the ladder | PARTIAL | L117–L121 shows the act (writing into the cipher, filing fire codes for a future reader) but the explicit reaffirmation from the canon log ("he cannot win in his lifetime, recommits to the books as rungs") is shown through behavior rather than stated. Acceptable — behavioral rendering is correct per style guide. |

**Over-resolved beats:** None. The rail failure in particular resists any clean resolution — the demonstration succeeded, the economics won, and the chapter ends without Daniel finding the counter-argument that works. Both the economic and capability cases are defeated, as specified.

**Unplanned beats (not in outline):**
- The Subura tenement fire and Gavinius the aedile (L113–L116): not mentioned in the ch23 outline entry. Functions as a fourth failure beat — fire codes rejected on political grounds. This is thematically consistent (the failure arc extends to civic institutions) and the Gavinius scene is tightly written and earns its place. However, the compass planting at L117 ("A reader would need it someday") introduces a future-vantage issue (see Section 3d below).
- The chapter opening references Marcia having taken over the books (L5), which is correct continuity from ch22 and does not conflict.

---

## 2. New V2 Arcs

- **Food arc** (`V2_FOOD_ARC.md`): Absent — N/A for this chapter per outline.
- **Prize/innovation arc** (`V2_PRIZE_INNOVATION.md`): Present — the contest entries (glass to see the moon, glass to show the invisible ones) are the result of the prize model's flywheel working. The contest is driving public expectation in a way Daniel cannot fully control. Beat present.
- **Children's education arc** (`V2_ULPIA_EDUCATION.md`): N/A — Lucanus not yet born in this chapter's timeframe (~109-110 AD; he is born ~112 AD per ch26 canon).
- **Tech/bootstrapping:** All three failures correctly blocked per V2_TECH_DEEP_DIVE. No "just works" cheating. The clock is blocked on escapement memory; the telescope on materials; the rails on economics. Rail cart specifically is not a tech failure but an economic one — correct per the outline.
- **Atlantic/New World:** Absent — N/A for this era.
- **Historical divergence:** Per V2_HISTORICAL_IMPACT (103-109 AD row), no specific on-page divergence is required. The failures are consistent with the divergence ledger: the invisible things (numerals, germ practices) spread without being shown; the visible projects fail. The chapter handles this contrast implicitly through the Dacian-coffle reference at L99 and Marcia's economics.

---

## 3. Prose Tics — Zero-Tolerance Sweep

### 3a. Correctio / "Not X, it's Y" (ZERO allowed)

**Two instances found:**

- [x] **Found: L115** — "He was not unkind. He was telling me exactly how it worked."
  This is a textbook correctio: "He was not X. He was Y." The second sentence redefines the first by cancellation. The prose is doing what it always does in this construction — performing nuance by negation. Fix: collapse into one direct statement. Example: "He told me exactly how it worked, and he was civil about it." Or: "Gavinius had the voice of a man who gives the bad news kindly because he has done it a hundred times." The current form as written is a zero-tolerance violation.

- [x] **Found: L31** — "A specific flavor of shame, knowing a true thing and being unable to use it. Worse than not knowing."
  The second sentence ("Worse than not knowing") pivots back to define the first by negating its opposite. Structure: [X described] → [pivot: "not Y"] → implicit: therefore X is worse than Y. The construction "Worse than not knowing" is a correctio-adjacent negation used as a rhetorical intensifier — defining the experience by what it exceeds, not by what it is. This is the "Less X than Y as a rhetorical pivot" form prohibited in PROSE_PATTERNS_TO_AVOID §1.1. Fix: the preceding sentence already carries the weight; cut "Worse than not knowing." entirely. The passage reads cleanly without it: "A specific flavor of shame, knowing a true thing and being unable to use it. When you don't know, you can go find out. There was no finding out here."

**Borderline, ruled NOT correctio:**
- L19: "and it was not there" — descriptive statement of absence, not a pivot structure. The sentence reports what Daniel found; there is no implied "it was Y instead." Not a correctio.
- L39: "It was gorgeous. I won't pretend it wasn't." — The second sentence is a meta-disclaimer (see 3c below), not a correctio pivot. The form is not "it was not X; it was Y."

**Zero-tolerance verdict: 2 correctio violations. Chapter is REVISE on this criterion.**

---

### 3b. Em dashes (ZERO allowed)

- [x] **None found.** The chapter uses commas, semicolons, and full stops throughout. Zero em dashes. Clean.

---

### 3c. Meta-disclaimers / throat-clearing (ZERO allowed)

- [x] **Found: L39** — "It was gorgeous. I won't pretend it wasn't."
  "I won't pretend" is a named variant of the meta-disclaimer pattern (PROSE_PATTERNS_TO_AVOID §6, TIC V1). The narrator is pre-emptively hedging against the reader's possible skepticism about his pride in the water clock. The prose announces its own honesty. Fix: cut the second sentence entirely. "It was gorgeous." can stand alone — the full description that follows proves it. "I won't pretend it wasn't" actively weakens the line by suggesting Daniel expects not to be believed.

---

### 3d. Narrator stepping outside time / future-vantage (ZERO allowed)

**Two instances found:**

- [x] **Found: L29** — "...the one small bronze argument that would be the heart of every mechanical clock built for the next two thousand years."
  This sentence steps outside the narrative present to announce the object's historical significance from a future vantage point. The narrator is not reporting what Daniel knew at the time — he is arriving from the future to assign weight to the escapement. The phrase "for the next two thousand years" is precisely the future-tense prediction embedded in past narration that PROSE_PATTERNS_TO_AVOID §1.2 prohibits. Fix: report what Daniel knew at the time instead: "the one small bronze argument that every clockmaker from here to the end of Rome would have to find." Or: "a piece of metal whose geometry I couldn't reconstruct from memory, though I'd watched a craftsman file one on a screen I no longer owned." Both stay inside the retrospective frame without the future-vantage announcement.

- [x] **BORDERLINE, ruled PRESENT: L117** — "A compass, I wrote in the cipher. A reader would need it someday to find their way across water where there are no landmarks."
  "A reader would need it someday" projects forward into a future the narrator is announcing as certain. The permitted form is "I wrote it because I thought a reader might need it." The actual form predicts — "would need" — from the vantage of someone who knows the outcome. This is the same mechanism as "I did not know then what that meeting would cost him": the narrator steps forward in time to assign purpose retrospectively. Borderline because "someday" is vague. However, the construction "A reader would need it someday" is functioning to assign confirmed future significance, not merely to report a hope. Ruling: **PRESENT**, a soft future-vantage instance. Fix: "I wrote it for whoever came after, who would want to know which way was north when there was no shore to navigate by."

**Zero-tolerance verdict: 1 clear future-vantage violation (L29), 1 soft instance (L117). Chapter is REVISE on this criterion.**

---

### 3e. "The way you / the way a man / the way a child" constructions (max 3 per chapter)

- Count: **3**
- L15: "I knew it the way a man knows a word he can't spell."
- L63: "no way to test the curve but to stop and look through it and guess" — uses "way" but not the simile form; not counted.
- L87: "on the way to the brick I needed" — literal use; not counted.
- The three "the way" instances at L15, L63 (partial), and L87 (literal) include only ONE of the simile/comparative subtype (L15: "the way a man knows a word he can't spell"). The other two are non-figurative uses.

- [x] **Within limit (1 figurative simile use, well within the 3-use cap).** No flag.

---

### 3f. Wisdom-button scene/chapter endings (max 1 per chapter; aim 0 per 3 chapters)

**Scene-ending audit:**

- **Scene 1 close (clock section):** L47 — "I watch her do it sometimes." — TYPE: silence/image cut. Tyche correcting the clock with her thumb, Daniel watching: a physical act. Not a wisdom button. Clean.

- **Scene 2 close (telescope section):** L79 — "I kept the first tube too. It and the water clock sit near each other in the tally-room, the two prettiest things I have made that don't do what I said they would." — TYPE: image cut + embedded aphorism. The sentence is close to a wisdom button: "the two prettiest things I have made that don't do what I said they would" restates the chapter's theme. However, the sentence is grounded in a specific physical inventory (the tube and the clock near each other in the tally-room) and does not abstract to a maxim about failure generally. It describes objects, not a principle. Borderline — probably acceptable as an image cut with a thematic hinge rather than a pure button.

- **Scene 3 close (rail section):** L109 — "I built a clean, true, simple machine that took the killing labor off men's backs, and it lost, fair and square, in the open court of arithmetic, to the plain fact that a man already owned the backs and a back costs less than a wheel." — TYPE: **wisdom button.** "A back costs less than a wheel" is a portable aphorism restating the chapter's theme. It could be extracted and used as a standalone epigram. This is the chapter's most rhetorically finished sentence and it closes the rail section as a summary verdict. Per style rules, 1 per chapter is permitted; this is the one. However, see below.

- **Scene 4 close (fire codes / compass section):** L117–L121. The chapter ends at L121. The final sentence — "and outside on the wharf somebody was still hauling something heavy the old way, the rope creaking, the men counting the pull in a language I dream in now, and I wrote it down." — TYPE: silence/action cut. Ends on a sound and an act. Not a wisdom button. This is a strong ending: the old labor going on outside while Daniel documents the better way he cannot make anyone adopt. The image works.

**Assessment:** 1 wisdom button (L109, rail section close). Within the 1-per-chapter limit. However, the telescope section close (L79) is borderline — it does not fully abstract to a maxim but it restates the chapter theme in a crafted sentence. If L79 is read as a second soft button, the chapter has 2, which would exceed the limit. Flag as a SHOULD FIX.

- [x] **At limit (1 confirmed wisdom button at L109). Chapter ending is clean (action/image cut). Borderline at L79.**

---

### 3g. "Thing" as vague placeholder

Multiple instances, mostly functional:

- L3: "when a thing is supposed to move and doesn't" — "thing" here is a deliberately vague placeholder for any device. Given the chapter's opening context (the workshop silence before a failed demonstration), this works as a generalization. Acceptable.
- L9: "A thing of wheels" — deliberately used for brevity and voice. Acceptable.
- L15: "a thing that is stopped, over and over" — describes the clock's function. Acceptable.
- L57: "a thing for an old man's failing eyes" — specific enough in context. Acceptable.
- L65: "until a far thing swam into a kind of focus" — "far thing" is vague where "the far bank" would be more specific. Minor.
- L95: "the thing I had been not-thinking for a month" — this is a vague placeholder for the economic defeat. A specific noun — "the calculation," "the sum," "the arithmetic" — would be sharper. Mild flag.

- [x] **No egregious abstract-"thing" cases; L95 is the weakest use.** Not a blocking issue.

---

### 3h. Gnomic aphorism stacking

- L15 contains one aphorism-adjacent sentence: "The tick was the clock." (short, declarative, closing the paragraph on a portable maxim).
- L109 closes the rail section with "a back costs less than a wheel."
- L107: "Hermes turned them so true." — not gnomic; registers as elegy, not aphorism.

**Two gnomic closings within one chapter** — the "tick was the clock" line at L15 and "a back costs less than a wheel" at L109. These are in separate sections and separated by ~4,000 words. They are not stacked (appearing consecutively). The chapter's natural three-section structure distributes them. Marginal but within acceptable range.

- [x] **Not stacked; separated by the chapter's full middle section.** Acceptable.

---

## 4. Secondary Tic Check

- **Polysyndeton runs** (max 1 per chapter): L21 contains a polysyndeton run ("I filed the points. I changed the angle. I made Hermes cut... I rigged a crossbar... the swing just died..."). This is a deliberate accumulation of attempts — not an "and...and...and" run per se, but an iteration structure. Count: 1. — **Within limit.**
- **"Nobody tells you" formula**: Absent. — **Clean.**
- **False-modesty rhythm** ("I was an idiot" then immediate sophistication): L7 opens with "It started, like most of my worst ideas, with me being smug." This is the setup to the clock failure. The next paragraph shows Daniel immediately making a competent engineering decision (drawing the gear train correctly). The false-modesty frame ("my worst ideas") is followed by a sophisticated mechanical description. Mild instance — not a full-blown false-modesty pivot because the failure is genuine, not just prefaced. Flag but not blocking.
- **"Which is to say" pivot** (max 1 per 10 chapters): Absent. — **Clean.**
- **"Looked at me"** (max 2 per chapter): L9 — "He looked at me with the look of a man pricing your funeral." Count: 1. — **Within limit.**
- **One-sentence paragraphs** (max 15% of paragraphs): Count: **10 of 56 paragraphs = 17.9%.** This EXCEEDS the 15% cap (cap = 8–9 at this chapter's paragraph count). The violation is marginal (2 over cap) but real.
  - Offending one-sentence paragraphs with lowest justification:
    - [2] "I got to know that silence well the winter Marcia took over my books." — could absorb into the previous paragraph; functions as a transition, not a pivot.
    - [24] "The glass was a longer disappointment, and a more expensive one, and the only one I brought entirely on myself with my own big mouth." — functions as a section opener, not a dramatic pivot; could open the paragraph it now stands alone before.
    - [44] "Then we sat down to the arithmetic, and Marcia did it, because she does it better than I do and because I think she already knew where it went." — transition paragraph with low dramatic weight; should absorb.
  - Genuinely justified one-sentence paragraphs (hard pivots, reversals, silences):
    - [8] "I could not remember the piece." — pivot/revelation. Justified.
    - [16] "So I built the water clock I could build and called it the clock I'd promised." — decision after failure. Justified.
    - [20] "It did not keep time." — reversal. Justified.
    - [39] "The rails I want to tell last, because the rails worked, and that was the worst of the three by a long way." — structural pivot. Justified.
    - [46] "'You own the men, Maximus.'" — dialogue beat, full weight. Justified.
  - **Flag: 3 low-justification one-sentence paragraphs should absorb into adjacent text. Count exceeds cap.**

- **Cycle of defeat** (idea → works once → fails → depression → pivot): The chapter is structured around three failures. This IS the Cycle of Defeat pattern (V1 TIC V16) deployed at chapter level. However, V2 explicitly designates this chapter as the "honest failure chapter" — its structure is deliberately the failure arc. The three-failure structure is the chapter's brief; this is not a case where the cycle needs breaking. The failures are also three distinct types (memory gap / materials / economics), which diversifies the pattern. Not flagged as a problem for this chapter specifically.
- **Ledger-as-catharsis**: The Marcia sequence (L93–L101) involves arithmetic and column-tallying. This is not using the ledger to resolve an emotional beat — it is using arithmetic to deliver the chapter's hardest scene (the economic defeat of the rails). The ledger here is the villain, not a comfort. Not a tic instance.
- **Socratic echo**: Absent. — Hermes's line ("It wants to go or it wants to stop. You are asking it to do both.") is a practical observation, not a perfect mirror of Daniel's explanation. Marcia's economics speech is her own original formulation, not a reflection of Daniel's. **Clean.**
- **"Let it sit / let that hang"**: L101 — "She let it sit." — One instance, Marcia's character, single use. Within limit.

---

## 5. Canon Consistency

- **Daniel's age this chapter** (ch23 covers ~103-109 AD per outline; ~109-110 AD per canon log ch23 entry): expected ~22-28 / ~28-29 — consistent with the chapter's arc from early clock experiments to the rail failure. No explicit age stated on the page. **Consistent.**

- **Tyche's age**: Born ~85 AD (canon log: "~14 in 99 AD"). Chapter set ~109-110 AD → expected age ~24. The chapter does not state her age explicitly. Canon log ch23 entry: "Tyche (~24)." No age stated on the page, so no arithmetic error. **Consistent; no discrepancy.**

- **Lucanus (b. ~112 AD)**: Not mentioned; consistent with era (~109-110 AD, pre-birth). **Consistent.**

- **Daniel's full name**: Not used in this chapter. Per canon: **Marcus Ulpius Danihel.** No use, no discrepancy.

- **Marcia's status**: Running the books (L5 "the winter Marcia took over my books"). Per canon log ch22: she is married to Daniel by spring ~109 AD and runs the books. Consistent. Her voice — flat, arithmetic, transactional — is consistent with character bible.

- **Hermes** (introduced ch15): Named at L7 ("I had Hermes, who could cut a gear so clean you could shave with the teeth") and in multiple later lines. His role as the precise metalworker turning the wheels is consistent with canon. His L23 dialogue ("It wants to go or it wants to stop. You are asking it to do both.") — terse, fragmentary, spoken between hammer-blows — matches his voice profile exactly.

- **Pamphilus** (freed ch18; on wages at wharf yard): Mentioned at L11 — "a lead cylinder Pamphilus cast in sand." This is a brief functional reference; he speaks no lines in this chapter. Per the V2 FIX requirement, Pamphilus must have at least 4 spoken lines across the book. His absence of dialogue in this chapter is not individually a violation, but should be tracked in the global Pamphilus line count. **Flag for coordinator: check Pamphilus running dialogue count across book.**

- **Macer** (L39): "his thumb working his ring" — the ring-turning gesture. Per V2_GLOBAL_TRACKER.md, Macer's ring gesture has a global cap of 3 total uses. **Flag for coordinator: log this use in the global gesture budget.**

- **Apollodorus quotation** (L89): "a demonstration is a lie you tell on a good day" — correctly attributed; this was established in ch12 canon. Consistent.

- **Phone relic**: L7 — "the little square of glass I still carried dead against my chest." Correctly described as dead, carried as a relic. Consistent with ch17 canon (kept wrapped in oiled wool in a box under a floorboard — minor discrepancy: L7 suggests he carries it on his person, ch24 canon says it's in a box under a floorboard). This may be a continuity error depending on when exactly in the chapter's arc this is set. If the clock failure is early in the period (~103-106 AD) and the phone-in-box is a later development (~110 AD, ch24 era), the reference at L7 could be temporally valid. **Minor continuity note — flag for coordinator: by ch23's late period (~110 AD) the phone is in the box per ch24; if L7 refers to an early moment in ch23's arc, it may be consistent.**

- **Demetrios** (new character, L63): Introduced as "the Greek, Demetrios, a glass-cutter." Canon log ch23 notes his introduction. **Consistent.**

- **Maximus** (new character, L89): Introduced as "a hard dry equestrian named Maximus." Canon log ch23 notes his introduction. **Consistent.**

- **Gavinius** (new character, L115): Introduced as the aedile. Not mentioned in the outline or canon log ch23 entry. **New canon fact — log below.**

- **Dates / era**: Chapter covers ~103-110 AD per outline; internal references are consistent. The contest ("Three years of the prize," L53) places the telescope section at ~109 AD (contest launched ~106-107 per ch19), which is internally consistent with the chapter's ~109-110 AD setting in the canon log.

- **Tech state**: No anachronistic technology on the page. The water clock, the attempted mechanical clock, the telescope, and the rail carts all correctly reflect Phase C capabilities. The compass is in prototype ("getting the alignment right, losing it, getting it back"), consistent with the Phase C/D tech schedule.

**New canon facts introduced this chapter** (log for coordinator):
- GAVINIUS: an aedile (administrative office), named in the Subura fire aftermath. Politely told Daniel that fire code reform would require the senator/equestrian building-owners' interest before he could act. Not unkind; a practical impediment.
- SUBURA TENEMENT FIRE: a block burned to the footings; fourteen dead; wind from the north limited spread. Date: "that spring" = roughly spring ~110 AD.
- COMPASS in prototype: Daniel is working on a magnetized-needle compass in the back of the tally-room; not yet reliable. Written into the English cipher.
- FIRE CODE NOTES: written up and filed by Tyche into the cipher/records.
- RING-TURNING GESTURE: appears at L39 (Macer) — log for global gesture budget.

---

## 6. Voice

- **Daniel's voice**: Dry, self-deprecating, specific throughout. "It started, like most of my worst ideas, with me being smug" (L7); "God, I tried" (L21); the baseball game binoculars memory (L57). The modern-reference intrusions are calibrated: the documentary, the baseball game, the idiom "I'll answer for." The voice has acquired Latin cadence in places ("the same words he used for the first balloon that wouldn't lift" reads more like a Latin periodic sentence than a 2020s American kid) while retaining the dry American core. The drift is correct per the style guide's direction for late-Part III Daniel. — **Consistent and strong.**

- **Class-marked secondary voices**:
  - Hermes (L23, L27): "It wants to go or it wants to stop. You are asking it to do both." / "What does it look like, in your country, the part that quarrels?" — correctly fragmentary, practical, spoken between hammer-blows. In register. **Clean.**
  - Macer (L39): "prettiest piece of foolery on the river" / "so did the sun, for free" — characteristically blunt, mercantile, dismissive. In register. The ring-turning gesture is present. **Clean.**
  - Heras (L45): "It is very beautiful... I would not plan a funeral by it." — dry, compressed, aphoristic without warmth. Correct register; the reference back to the balloon's first failure ("the same words he used") is a subtle character note. **Clean.**
  - Marcia (L97, L101): "You own the men, Maximus." / "It is a machine for a man who has to pay his haulers. You do not have to pay your haulers." — flat, transactional, arithmetic. This is her strongest scene in the book so far. The voice is in exact register: she lays out the whole case, she lets it sit, she states the verdict. **Strong.**
  - Gavinius (L115): "'I would be very interested... if any of those men were interested.'" — correctly bureaucratic; politely obstructive without malice. Minimal but accurate.

- **No muted mutes**: Pamphilus appears in one functional reference (L11) and does not speak. This is not a violation for a single chapter; see coordinator note above about global line count.

- **Info-delivering monologue check**: Marcia's speech at L95–L101 is close to the 4-line threshold but is broken internally (narrator summary at L95, then Marcia's spoken line at L97, then Daniel's interjection/narration at L99, then Marcia's longer speech at L101). The longest unbroken stretch of Marcia's speech at L101 is one paragraph (~4 lines). It is internally complex — it opens with accounting, pivots to the verdict, lets it sit, then delivers the closing logic. It functions more like rapid-fire cross-examination than a monologue because the listener (Maximus) is present and responsive and the speech is structured around his implied counter-argument. **Not flagged as an info-dump; the Hadrian standard (fragments under pressure) is partially met.**

- **Info-delivering monologue — L105**: Daniel's own narration of the capability argument ("I tried the capability argument afterward, the one I should have led with...") runs for one full paragraph presenting the case he should have made. This is narration, not dialogue, so the 4-line monologue rule does not technically apply, but it is an instance of Daniel arguing with himself on the page. The argument is well-constructed but risks reading as an after-the-fact lecture about why he was right. Minor voice note.

- **Daniel competence**: Gets things genuinely wrong (cannot remember the escapement geometry; the telescope produces a blurry rainbow; the rail demo wins the engineering argument and loses the commercial one). He does not win. He does not fake confidence in this chapter — he actually fails, repeatedly, in public. This is the chapter's defining quality. **Strong.**

- **Child dialogue**: No child characters present. N/A.

- **Frozen epiphany** (TIC V13): L71 — "I stood there on the wharf holding it and I felt the whole bright tower of what I'd promised lean and not quite fall." This is a frozen epiphany: Daniel physically stops and has a realization. Per PROSE_PATTERNS_TO_AVOID (TIC V13): "Protagonist physically stops moving to have a profound realization." The realization here is rendered through the image of the tower leaning ("lean and not quite fall") rather than as clean cognitive insight — which partially mitigates the tic. However, the protagonist is stopped, holding the tube, watching the world reorganize itself around his failure. The key test: does the stasis IS the point? Here, the stasis is the dramatic beat — he cannot do anything; he can only hold the bad telescope and feel the gap between promise and delivery. Borderline. If the next lines gave him a complete analytical realization, it would be TIC V13. The chapter instead cuts to Marcia's practical response (L73). **Borderline — not flagged as blocking; note for revision consideration.**

---

## 7. Verdict

**REVISE**

### Blocking issues (must fix before next use)

1. **Correctio at L115** — "He was not unkind. He was telling me exactly how it worked." — Classic "He was not X. He was Y." structure. Zero-tolerance violation. Fix: collapse into a single direct statement or render as pure action. Example: "He told me exactly how it worked, and he closed the tablet while he did." or: "Gavinius rolled the tablet back toward me. 'I would be very interested,' he said, 'if any of those men were interested.' His voice had the particular flatness of a man who says the hard thing often enough that it no longer costs him anything."

2. **Correctio at L31** — "A specific flavor of shame, knowing a true thing and being unable to use it. Worse than not knowing." — The second sentence defines the first by negating its opposite ("not knowing"), constituting a correctio-adjacent negation pivot. Zero-tolerance violation. Fix: cut "Worse than not knowing." The passage reads cleanly and with more force without it.

3. **Future-vantage at L29** — "...the one small bronze argument that would be the heart of every mechanical clock built for the next two thousand years." The narrator steps outside the narrative present to announce the escapement's historical significance. The phrase "for the next two thousand years" is a declaration of confirmed future significance, which is banned. Fix: report what Daniel knew at the time, or what he suspected, without the future-certainty declaration. Example: "...the one small bronze argument at the center of every clock a clockmaker would ever build." (The significance is implied by "every clock" without requiring the narrator to confirm it from the future.)

### Revise items (should fix)

4. **Meta-disclaimer at L39** — "It was gorgeous. I won't pretend it wasn't." The second sentence is a meta-disclaimer — the narrator announces his own honesty before the scene demonstrates it. Per TIC V1 (PROSE_PATTERNS_TO_AVOID §6): "Appears in almost every chapter — it is the manuscript's single most damaging pattern." Fix: cut "I won't pretend it wasn't." entirely. "It was gorgeous." stands alone and is stronger for the solitude.

5. **Borderline future-vantage at L117** — "A reader would need it someday to find their way across water where there are no landmarks." The construction "would need it someday" projects forward with certainty. Fix: "I wrote it for whoever came after, who would need to know which way was north when there was no shore to navigate by." This stays inside the retrospective frame without confirming the future need.

6. **One-sentence paragraph density at 17.9%** (10 of 56 paragraphs) — 2-3 over the 15% cap. Three low-justification one-sentence paragraphs should absorb into adjacent text:
   - Paragraph 2 ("I got to know that silence well the winter Marcia took over my books.") — absorb into para 1 or 3.
   - Paragraph 24 ("The glass was a longer disappointment...") — begin as the opening line of the next substantive paragraph rather than a free-standing sentence.
   - Paragraph 44 ("Then we sat down to the arithmetic...") — absorb into the rail section's preceding paragraph.

7. **Template chapter opening** — "There is a particular silence a workshop makes when a thing is supposed to move and doesn't." The V4 AUDIT notes that this "There is a [sound/silence/thing]..." construction is one of the three recurring chapter opening templates, and that ch23 and ch24 both use it back-to-back. Ch24 opens: "There is a sound a yard makes when it is working and nobody is fighting about anything." Two consecutive "There is a [sound/silence]..." openings. Per V2_AUDIT_REVIEW Issue 1 sub-note: "The 'there is a [X] a [place] makes when...' templated chapter opening (back-to-back in ch23 and ch24)." Ch23's opening is strong prose on its own terms, but the template repetition with ch24 is a specific flagged concern. Since the reviewer cannot edit either chapter, the flag goes to the coordinator for resolution (revise one of the two openings).

### PRESERVE

- **The Marcia economics scene** (L93–L107): The entire rail failure section is the chapter's best writing. Marcia's "You own the men, Maximus" and the full economic argument are the V1 brief's "best honest beat" and the execution is fully earned. Do not touch.
- **The clock failure's specificity**: The escapement description (L19, L21) — "a sort of anchor-shaped bit rocking on a pin, two little points dipping into a toothed wheel, click, click, click" — is the book's best rendering of the "knows what it looks like but can't build it" failure mode. Preserve exactly.
- **The Hermes dialogue** (L23, L27): In register, fragmentary, practical. Earns its place.
- **The water clock description** (L37): The float-cord-pointer mechanism is rendered as working engineering without explanation or pride. Preserve.
- **The chapter ending** (L121): "...outside on the wharf somebody was still hauling something heavy the old way, the rope creaking, the men counting the pull in a language I dream in now, and I wrote it down." — a silence/action cut; ends on sound and the act of writing. Not a wisdom button. Strong.
- **Heras's one line** (L45): "I would not plan a funeral by it." — in voice, dry, correctly modeled on his prior instance with the balloon. Preserve.
- **Marcia's closing line to Daniel** (L75): "A bad toy that no one else has is still the only one." — Marcia-register, not a wisdom button (it's her practical verdict, not Daniel's philosophical reflection), transactional. Preserve.
- **"I dream in now"** (L121): The language-drift marker — "in a language I dream in now" — shows the Latin/Roman assimilation without announcing it. Per style guide: "By the late book he thinks partly in Latin and has to reach for the English word. Show this drift gradually; do not announce it." This is the correct execution. Preserve.

### Notes for coordinator

- **Ch23/ch24 template opening clash**: Both chapters open with "There is a [silence/sound] a [place] makes when..." — back-to-back in the same template. One must be revised. Assign to the writer for ch24 or ch23 (ch23's is stronger prose; ch24's is more mechanical). See V4_AUDIT_REVIEW_AND_CLEANUP.md Issue 1 sub-note.
- **Gavinius canon entry**: New character introduced. Log as: "[ch23] GAVINIUS — aedile. Heard Daniel's fire-code proposal after the Subura tenement fire (~spring 110 AD). Politely declined to act without senatorial/equestrian support from building owners. Not named as hostile. Function: demonstrates that the administrative path to civic improvement is as blocked as the commercial path."
- **Subura fire event**: Log in canon: "[ch23] A tenement block in the Subura burned to footings, fourteen dead, wind from north limited spread. Spring ~110 AD."
- **Compass first noted**: "[ch23] Magnetic needle compass in prototype. Daniel working on it in the back of the tally-room; unreliable alignment. Written into the English cipher."
- **Pamphilus dialogue count**: This chapter contains zero Pamphilus dialogue. Track in global count — V2 requires ≥4 spoken lines total across all appearances.
- **Macer ring gesture**: Appears at L39 — log in V2_GLOBAL_TRACKER.md ring-gesture budget (cap: 3 total across book).
- **Phone relic location**: Minor continuity question — L7 describes Daniel carrying the phone dead against his chest; ch24 canon log says it is "kept wrapped in oiled wool in a box under a floorboard." If L7 refers to the early period of ch23's arc (~103-106 AD) before the phone was put away, this may be consistent. Worth verifying against the chapter's internal timeline. If the clock section is set late in the ~103-110 arc, there may be a discrepancy.
- **"The way" count for ch23 appears to use only 1 comparative-simile instance** (the "the way a man knows a word he can't spell" at L15), well within the 3-use cap. Noted as clean.

---

*QA reviewer note: Ch23 is among the strongest chapters in the V3 draft. The three-part failure structure is clean, the economic argument in the rails section is the book's best social-realist writing, and the chapter ending is the correct type (action/image cut, not a wisdom button). The three blocking issues are mechanical violations of zero-tolerance rules and are all fixable in a single revision pass. The chapter's core — especially the rails section — should not be touched except at the flagged lines.*
