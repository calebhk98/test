# QA — Chapter 8: Fire That Flies
**Reviewer:** QA Agent (Sonnet 4.6)
**Date:** 2026-05-28
**Word count:** 3,463 words
**V2 change notes applied:** Partial — three named V2 blockers resolved; one new zero-tolerance violation remains; sportsbook beat partially executed.

---

## 1. Plot Beats

*(Source: `outline/updated_ch01_18.md` ch08 entry, `outline/master_outline.md`)*

| Beat | Present? | Notes |
|---|---|---|
| Public unmanned demo amid festival crowds | Yes | Fully rendered — ground-fill method, hoop-walking trick, countdown, release. Excellent. |
| Bag rises before crowd; awe + cry of witchcraft vs. marvel | Yes | L16–L37. Crowd noise, fear, the witch-word picked up. |
| Balloon clips rooftop; washing fire; no deaths | Yes | L43. Required V2 addition — load-bearing for Vibenius's ambiguous reading. Well executed. |
| Aulus Vibenius reads the flying fire as omen — deliberate ambiguity | Yes | L51–L65. Vibenius's speech and reasoning fully dramatized. |
| Daniel summoned to meet the master (Macer) | Yes | L69–L81. Strong action-cut chapter ending. |
| Sportsbook launches (beat C6; required in ch08 per outline) | Partial | L79: probability principle stated on the page ("implied chance of all four outcomes added up to more than one hundred"). However, the outline requires "the expected-value math must be rendered on the page — even one sentence of arithmetic showing the logic." The margin math is described as a principle but no specific number or calculation appears. SHOULD FIX. |
| Crowd hecklers directly quoted in Pompeii-graffiti register | Partial | L25: "Thulean witch" and "What's he got hidden on him, go on, search him" are quoted. Register is correctly rough but falls short of the required "obscene / crude" Pompeii-graffiti level — no crude oath, no dirty joke at Daniel's expense. The requirement (outline, CHARACTER_VOICE_GUIDE.md Rule 6) calls for at least one crude or obscene line. SHOULD FIX. |

**Over-resolved beats:** None. The Macer meeting is properly withheld for ch09.

**Unplanned beats:** None — the sportsbook interior thought at L79 is explicitly required by the outline; it is in the right place.

---

## 2. New V2 Arcs

- **Food arc:** N/A for ch08.
- **Prize/innovation arc:** Sportsbook is the relevant V2 beat here (not the prize model). Partially present (see above).
- **Children's education arc:** N/A.
- **Tech/bootstrapping:** The balloon demonstration is the Phase B tech beat. Correctly rendered: it works imperfectly (goes up, comes down on the roof). No cheating or hand-waving.
- **Atlantic/New World:** N/A.
- **Historical divergence:** N/A — the outline notes only "strange kite over Campus Martius" at year 100; no divergence claim in ch08. Consistent.

---

## 3. Prose Tics — Zero-Tolerance Sweep

### 3a. Correctio / "Not X, it's Y" (ZERO allowed)

**VIOLATION FOUND — BLOCKER:**

- [x] Found: **L45** — "the question hanging over the lot was **not is it a wonder but what do we do** with the man who made it"

Full context: *"…it was the worst possible nothing, because now the question hanging over the lot was not is it a wonder but what do we do with the man who made it, and that question, in a Roman crowd that has just been frightened, has an old and ugly answer."*

This is a textbook "not X but Y" correctio construction. The sentence defines the question by first negating one framing (not is it a wonder) and pivoting to the alternative (what do we do). Per `PROSE_PATTERNS_TO_AVOID.md` §1.1 and §2.6: zero instances per chapter, no exceptions.

**Fix:** State the shift directly without the negation pivot. E.g.: *"…the question hanging over the lot had changed. It was no longer about wonder. Four hundred frightened people were working out what to do with the foreigner who had dropped fire on their rooftops."*

Note: Three previous V2 blockers called out in the outline (the "not a cheer" correctio, the "years now" future-vantage, and the "not knowing it" dramatic-irony tail) are all ABSENT from V3. Those specific fixes hold. One new correctio instance was introduced.

### 3b. Em dashes (ZERO allowed)

- [x] None found. Clean.

### 3c. Meta-disclaimers / throat-clearing (ZERO allowed)

- [x] **Borderline found: L35** — *"I have tried to say the next part right and I always fail, so here is the failure: it went up."*

This matches the banned pattern (TIC V14 / TIC V1): the narrator refuses to trust the prose before a scene by announcing its own difficulty. "I have tried to say the next part right and I always fail" is a variant of "I want to be exact about this" — it prefaces the balloon-rise scene with an authorial apology about the inadequacy of language. Per `PROSE_PATTERNS_TO_AVOID.md` §TIC V1, §TIC V14: delete 80–100% of these.

Assessment: The sentence that follows ("it went up. It went up as nothing in their world went up…") is strong enough to stand alone without the disclaimer. The prose does NOT need to announce it will fail before it succeeds. Treat as a **SHOULD FIX.**

Ruling: Not zero-tolerance on the meta-disclaimer axis (it lacks the exact "I want to be honest/exact/careful" phrasing), but it IS the preamble-relapse pattern and should be cut.

### 3d. Narrator stepping outside time / future-vantage (ZERO allowed)

**VIOLATION FOUND — BLOCKER:**

- [x] Found: **L61** — *"And the genius of it, which I only understood later and hated, was that whichever way it went now, he had read it true."*

The phrase "which I only understood later" is the exact banned construction: the narrator arrives from a future vantage point to announce that the significance of a present moment was not grasped at the time. Per `bible/06_style_guide.md`: *"Must not step outside time. No 'I would not understand until years later'… The retrospective frame licenses knowing what did happen; it does not license announcing what mattered."* Per `PROSE_PATTERNS_TO_AVOID.md` §1.2: *"Any sentence that tells the reader the future emotional state of the narrator as a way of assigning weight to the present moment."*

The sentence also contains the scene's thesis ("The haruspex is never wrong. That is the whole craft.") which, if the future-vantage annotation is removed, can stand on its own as Daniel's post-hoc reflection in close-retrospect — permitted form.

**Fix:** Change "which I only understood later and hated" to close-retrospect language that reports what Daniel concluded without announcing the delay. E.g.: *"And the cleverness of it, which I hated, was that whichever way it went now, he had read it true."* OR simply: *"The genius of it — and I hated the genius — was that whichever way it went now, he had read it true."*

### 3e. "The way you / the way a man / the way a child" constructions (max 3 per chapter)

Figurative uses:
- L51: "the way a crowd parts for someone it is afraid of" — comparative simile (counts: 1)
- L79: "the way you hold a stone in your pocket for the weight of it" — "the way you" comparative simile (counts: 2)
- L53: "cleared the way ahead" — directional, not figurative (does not count)
- L75: "all the ways the household had spoken to me" — plural noun, not simile frame (does not count)

Count: **2** of 3 allowed.
- [x] Within limit.

### 3f. Wisdom-button scene/chapter endings (max 1 per chapter; aim 0 per 3 chapters)

Scene-ending audit:
- **Scene 1 close (L13):** "I did not lay eyes on him that morning either" — action cut. Clean.
- **Scene 2 close (L31–32):** "They let go." — action cut. Excellent.
- **Scene 3 close (L47):** "I was glad of it." — emotional disclosure, brief. Borderline but acceptable; the physical grounding of Davus's hand holds the moment.
- **Scene 4 close (L65):** "he was gone." — action cut. Clean.
- **Chapter close (L81):** Image cut — the smoke going thin and blue into the sky. No aphorism. Correct type.

Internal gnomic aphorism (NOT a scene-closer but notable):
- L61: "The haruspex is never wrong. That is the whole craft." — This is inside a paragraph mid-scene, not at the scene's close. It is Daniel's internal analysis of Vibenius's method. It functions as an epigram and could be extracted as a tweet. However, since it is not a scene-ending button, it does not trigger the hard limit. Flag as a **gnomic aphorism** (see §3h below).

Chapter ending type: **image cut.** Within limit.
- [x] Within limit — no scene ends on a wisdom button. Clean.

### 3g. "Thing" as vague placeholder

Search for " thing" — instances reviewed:
- L7: "because the word hadn't been invented yet for what they were seeing" — no "thing" issue.
- L45: "the worst possible nothing" — modified noun, not lazy placeholder.
- L71: "a thing seen and survived and now a thing to tell over wine" — "thing" x2. Both are borderline: "a thing seen and survived" and "a thing to tell over wine" could be replaced with more specific nouns (an event, a story). Minor.
- L79: "the small careful thing I had been running in my head" — "thing" used for the sportsbook scheme. Specific noun available: "the small careful scheme" or "the small careful numbers." SHOULD FIX (minor).

- [x] No blocking uses, but two instances where specific nouns are available.

### 3h. Gnomic aphorism stacking (flag if 2+ in a single chapter)

- L61: "The haruspex is never wrong. That is the whole craft." — standalone extractable maxim.
- L5: "There was no string. That was the whole point and the whole terror. There would be no string." — this is more situational description than a portable maxim; does not stack against the above.
- L45: "an old and ugly answer" — implied rather than stated; not a full aphorism.

Count: **1** true standalone gnomic aphorism (L61). No stacking.
- [x] No stacking found.

---

## 4. Secondary Tic Check

- **Polysyndeton runs** (max 1 per chapter): L35 contains a polysyndeton run ("it went up and kept going, a man-sized gray shape climbing straight off the fire… and it turned slowly as it rose… and the whole square opened its throat at once") — count: **1**. Within limit. [x] OK.
- **"Nobody tells you" formula**: [x] Absent.
- **False-modesty rhythm** ("I was an idiot" then immediate sophistication): [x] Absent in this chapter.
- **"Which is to say" pivot**: [x] Absent.
- **"Looked at me"** (max 2 per chapter): L59: "He looked at me, the burned hands…" — count: **1**. [x] OK.
- **One-sentence paragraphs** (max 15% of paragraphs): 6 of 36 paragraph blocks = **16.7%** — marginally over the 15% cap. The 6 single-sentence blocks are: the opening "The bag was the size of a man hung head-down." (L1); the Davus dialogue beat (L10); "Now." (L13); "They let go." (L14); the Vibenius crowd-parting entry (L22); and "I did not get to gather up my bag." (L30). The first four earn their isolation strongly (the opener is exemplary; the two-word beats at L13–14 are the chapter's best prose moment). L22 and L30 are less essential — L22 could be absorbed into the paragraph that follows it; L30 is a transitional beat that could open the next paragraph rather than stand alone. FLAG: marginally over limit; trim 1–2 to come within range.
- **Cycle of defeat**: Present in structure (balloon goes up → fails on the roof → crowd turns) but this is the correct dramatic arc for this chapter, not a tech-iteration structural tic. [x] Not a flag.
- **Ledger-as-catharsis**: [x] Absent.
- **Socratic echo**: [x] Absent — Vibenius is not mirroring Daniel; he is doing his own independent reading.
- **"Let it sit / let that hang"**: L59 — "He let that sit." Single use, Vibenius only. [x] Single character only.

---

## 5. Canon Consistency

*(Checked against `bible/08_canon_log.md`, `bible/03_timeline.md`, `bible/02_characters.md`)*

- **Daniel's age this chapter:** Canon log says "Daniel 18, mid/late 99 AD." Outline says "100-101 AD, Daniel 19-20." The chapter text implies approximately one year since ch07's events (mid-99 AD), making the demo late 99 or early 100 AD. Daniel's age is not stated on the page. The canon log entry and chapter content are consistent with each other; the outline's "100-101 AD" dating is slightly later. FLAG for coordinator — minor dating discrepancy between canon log and outline; the chapter text does not contradict either. No in-chapter age stated, so no prose error.
- **Stichus's age:** Stated "ten years old" at L9. Canon log: "~10." [x] Consistent.
- **Davus:** Introduced as a new character (L9), per canon log entry for ch08: "new named character." [x] Consistent.
- **Macer as owner:** Present but unnamed/unseen — Daniel has still never met him; he watches from the crowd. Steward intermediates. [x] Consistent with canon ("first meeting = ch09").
- **Tyche:** Absent from ch08. No age check needed.
- **The bag's construction:** "nine days," green ash-wood hoop, pale gray greased linen, ~11 ft tall. Canon log: "9 days' work; NO string; green ash-wood mouth-hoop." [x] Consistent.
- **The flight specifics:** "rose ~60-70 ft, hung, cooled, drifted, clipped a five-story insula roof, smoldering corner." Canon log: "rose ~60-70 ft, hung, cooled, drifted on the river wind, clipped a five-story insula roof, tore down washing, brief street flame." [x] Consistent.
- **Vibenius:** Reads the omen as ambiguous — gods let it rise / gods turned it back. Canon log: "pronounced the flight an OMEN, deliberately AMBIGUOUS: the gods let it rise (no god favors what it hates), yet the gods turned the fire back down." [x] Consistent.
- **Helpers:** Stichus (coal-pot) and Davus (hoop). Canon log: "STICHUS (works the coal-pot) and a household slave named DAVUS (new named character; he keeps Daniel from bolting)." [x] Consistent.
- **Heras:** Present, described as "satisfied and wary at once." [x] Consistent with his established characterization.

**New canon facts introduced this chapter:**
- Davus is confirmed as a household slave (distinct from the workshop/yard staff) sent by the steward to prevent Daniel from bolting.
- The steward is described on-page: "a dry narrow man with a tablet, sized up the bag with the flat attention of someone pricing livestock." (No name given — consistent with prior canon.)
- Heras attends the demonstration "in his good cloak with his arms folded, being a Greek physician of Pergamon, a man whose word a buyer might trust" — his protective reputational function is active.
- Daniel is already mentally running a small sportsbook operation (3 weeks established by L79) before meeting Macer. This is consistent with the V2 beat that the sportsbook precedes the patron relationship.

---

## 6. Voice

- **Daniel's voice:** Dry, self-deprecating, and specific throughout. "This is the dumbest place in the world to light a fire" (L7) is exactly the 2020s teen register. The counting-breaths pacing during the fill sequence (sixty breaths, a hundred, a hundred and forty, a hundred and eighty) is restrained and earned. The private sportsbook math at the end ("Six asses and an idea") is appropriately dry. [x] Consistent with V2 spec.
- **Daniel's competence:** He makes the right technical call (tipping the hoop to keep cloth from the flame), runs his magician's trick, and panics privately. He is glad of Davus's restraining hand. [x] Fallible-but-functional — correct register.
- **Class-marked secondary voices:**
  - Davus: "Heavy," — two words, to nobody. [x] Correct lower-register economy.
  - Crowd hecklers: "Thulean witch" and "What's he got hidden on him, go on, search him." Quoted but clean. The outline and CHARACTER_VOICE_GUIDE.md require at least one crude or obscene heckler line (Pompeii-graffiti register). The current hecklers sound like concerned skeptics, not Roman dockers. **SHOULD FIX.**
  - Vibenius: Formal, indirect, grave. The level of eloquence is correct for a senior haruspex speaking for the record. [x] Voice consistent.
  - Steward: "the master would see me… in the voice of a man announcing a wall had decided to move." Functionary register, no dialogue quoted directly. [x] Acceptable.
  - Heras: Present but not quoted in ch08. [x] N/A.
- **No muted mutes:** Pamphilus is absent from this chapter. No other required-quoted character is silenced. [x] No muting issue.
- **Info-delivering monologue check:** Vibenius's reading (L59) is the chapter's longest single-character speech. It runs approximately 120 words without interruption in the prose. However, this is reported speech (Daniel's retrospective rendering of Vibenius's words), not direct dialogue. It is compressed by narrative distance and broken into its logical components (what he said → what he implied → the ambiguity). The outline explicitly notes Vibenius's ambiguous omen-reading; this is the required beat. The prose handles it by embedding the speech in Daniel's retrospective translation rather than transcribing it as a long uninterrupted address. [x] Acceptable — the 4-line uninterrupted-speech rule applies to dialogue; reported summary is within limits.
- **Child dialogue:** Stichus is present but does not speak. He "cried without sound." [x] N/A.

---

## 7. Verdict

**REVISE**

### Blocking issues (must fix before next use)

1. **Future-vantage — L61:** *"which I only understood later and hated"* — narrator steps outside time to annotate that the present scene's significance was not grasped at the time. Banned per style guide and PROSE_PATTERNS §1.2. Fix: change to close-retrospect form, e.g. *"the cleverness of it, which I hated, was that whichever way it went now, he had read it true."*

2. **Correctio — L45:** *"the question hanging over the lot was not is it a wonder but what do we do with the man who made it"* — classic "not X but Y" correctio. Zero-tolerance per PROSE_PATTERNS §1.1. Fix: state the shift directly without the negation pivot: e.g., *"the question hanging over the lot had shifted: four hundred frightened people were now working out what to do with the man who had dropped fire on their rooftops."*

### Revise items (should fix)

3. **Meta-disclaimer / preamble relapse — L35:** *"I have tried to say the next part right and I always fail, so here is the failure:"* — TIC V14 (preamble relapse). The prose that follows is strong enough to stand without the apology. Cut the entire preface clause; begin: *"It went up."*

4. **Crowd heckler register — L25 (and L37):** Hecklers are quoted (requirement met) but in a too-clean register. Outline requires "rough, dumb, superstitious, obscene; Pompeii-graffiti register." Add one crude or obscene line — e.g., a dirty joke at the foreigner's expense, a sexual or scatological insult, or the kind of crude oath Celer's soldiers would use. The current *"What's he got hidden on him, go on, search him"* is suspicion, not crudeness.

5. **Sportsbook math specificity — L79:** The outline requires "the expected-value math must be rendered on the page." The probability principle is present ("implied chance of all four outcomes added up to more than one hundred") but no actual arithmetic appears. Add one sentence with a concrete number or margin calculation — e.g., *"Set the Greens at three-in-five and the Blues at one-in-two and the Whites and Reds each at one-in-three, and the whole added to one hundred and twenty — that twenty is the house's take, divided by everything wagered."*

6. **One-sentence paragraph density — marginally over limit:** 6 of 36 blocks = 16.7% (cap: 15%). L22 ("Then the crowd parted from the temple side, the way a crowd parts for someone it is afraid of in the other direction, and the old man came through it.") and L30 ("I did not get to gather up my bag.") are the weakest isolated blocks. Either absorb L22 into the paragraph that follows, or absorb L30 into the preceding paragraph's tail.

7. **"Thing" placeholder — L71 and L79:** L71: *"a thing seen and survived and now a thing to tell over wine"* — both instances can be replaced with specific nouns ("an event," "a tale"). L79: *"the small careful thing I had been running in my head"* — replace with "scheme" or "the small careful numbers." Minor but addressable.

### Notes for coordinator

- **Date discrepancy:** Canon log records ch08 as "mid/late 99 AD, Daniel 18." The outline entry records ch08 as "100-101 AD, Daniel 19-20." The chapter text is consistent with either (it says "a year" since the preceding chapter). No in-text age statement to contradict. Recommend aligning canon log and outline to a single date; the chapter text requires no prose change.

- **The three V2 BLOCKER fixes from the outline are confirmed resolved:** (a) The "years now" future-vantage clause is gone; (b) the "not knowing it" dramatic-irony tail is gone; (c) the "not a cheer. A cheer has words in it" correctio is gone. Credit due — those three were the hardest named fixes.

- **Vibenius's speech:** Excellent characterization. The "both doors" construction — he gives the crowd a blessing and a warning simultaneously so the haruspex is never wrong — is one of the chapter's strongest moments and should be preserved in its entirety.

- **Chapter close (L81):** The smoke image is exactly the right ending type (image cut). Preserve it.

- **"Now. / They let go." (L13–14):** The two-beat release is the chapter's single best prose moment. Preserve unconditionally.

- **Stichus's soundless crying (L71):** Small, right. No interpretation. Preserve.
