# QA — Chapter 18: The Siege
**Reviewer:** QA Agent (claude-sonnet-4-6)
**Date:** 2026-05-29
**Word count:** ~4,100 words (4,255 including title/heading)
**V2 change notes applied:** Partial — the two named BLOCKER fixes (honesty-scaffolding lines; "Not gratitude. Need." correctio) have been resolved. However, new or residual violations remain.

---

## 1. Plot Beats

*(Source: `outline/updated_ch01_18.md` §ch18; `bible/08_canon_log.md` [ch18].)*

| Beat | Present? | Notes |
|---|---|---|
| Pamphilus bought (4,000 sesterces) and freed before march | YES | L3–L37; price correct per canon |
| Informal manumission (lesser-free, not full citizen) | YES | L9; "cheap door...makes a free man but a lesser-free man" — correct |
| Pamphilus's "go where" moment — triumph smaller than dreamed | YES | L21–L35; well-rendered |
| Pamphilus ≥4 spoken lines in fragmented register | YES (5 lines) | L17, L27, L89, L93, L99 — all fragmented/wrong-tense |
| March as imperial freedman, named in orders | YES | L41–L43 |
| Apollodorus's stone bridge at Drobeta (20 piers) | YES | L47–L49 |
| Celer alive, basket-rigging checked, Sabinus never named | YES | L77, L83 |
| Camp sanitation / latrine-siting / barrel-battery filters | YES | L69 |
| Tethered observation balloon (empty basket, short tether) | YES | L71 |
| Manned flights with crossbowmen at Sarmizegetusa | YES | L77–L81 |
| Figures spread through army (grudging quartermaster) | YES | L85 |
| Water supply cut at Sarmizegetusa | YES | L103–L113 |
| Water identified from aerial surveillance | PARTIAL | Chapter shows ground-based reading by Daniel + Apollodorus's engineer; no aerial surveillance of water routes depicted. Outline specifies "identified from kite altitude in days not weeks." This is the primary beat deviation. |
| Apollodorus: "It's the same knowledge" | YES | L115 |
| Decebalus's suicide; head and hand carried south | YES | L123 |
| Dacia annexed; Dacian gold in carts counted | YES | L125–L131 |
| Powder demolition charges at walls (optional beat) | ABSENT | Outline brackets this as "[Optional beat]"; only passing reference at L113 to "drag my feet on the powder." The beat is optional but its absence removes one layer of the moral accounting set up for ch45. |
| Divergence question planted (history vs watched) | YES | L135 |
| Return over stone bridge; Tyche planted as "next" | YES | L137 |

**Over-resolved beats:** None. The moral complexity is appropriate — Daniel does not resolve the water-cut dilemma.

**Unplanned beats:** The "That is the dullest sentence I will ever write" line at L69 is a mild editorial aside not in the brief. Acceptable.

---

## 2. New V2 Arcs

- **Food arc:** N/A for this chapter.
- **Prize/innovation arc:** N/A for this chapter.
- **Children's education arc:** N/A.
- **Tech/bootstrapping:** Manned balloon with double-basket construction and crossbowmen is present (L77–L81). Water-cut hydraulics is present and correct. The absent powder demolition beat is a noted optional gap.
- **Atlantic/New World:** N/A.
- **Historical divergence:** Substantially present — manned balloon archers, crossbow standardization, water supply sabotage. The aerial identification of the water routes is partially absent (see beat table above). Measurable divergence on-page.

---

## 3. Prose Tics — Zero-Tolerance Sweep

### 3a. Correctio / "Not X, it's Y" (ZERO allowed)

**Named BLOCKER fixed:** "Not gratitude. Need." has been replaced with "Need spread the figures. The grudging man's version of it..." (L85). Clean rewrite. No longer a violation.

**Residual correctio found:**

- [x] **L13 (BLOCKER):** "In my head freeing a man was a sentence said and a tablet signed and the man stood up different. **The man did not stand up different.**"
  This is a distributed two-sentence correctio: sets up an expectation, then negates it as the pivot. Structurally identical to "I expected X. It was not X." The correct technique is to begin with what actually happened, not to establish an expectation for the purpose of denying it.
  **Fix:** Begin the collar paragraph at "He sat on the bench with his hands on his knees..." Cut the setup expectation. The collar detail carries the scene without the negation scaffold.

- [x] **L45 (SHOULD FIX):** "An intermission, not an ending."
  A compact definitional correctio: X, not Y. The form is X positive, negating an alternative framing. This is the "Not X. Y." pattern in reversed order (Y, not X).
  **Fix:** Cut the phrase and let the previous sentence do the work: "...had always meant to come back and finish." The reader grasps it. The appositive label is unnecessary.

### 3b. Em dashes (ZERO allowed)

- [x] **None found.** Clean.

### 3c. Meta-disclaimers / throat-clearing (ZERO allowed)

The named BLOCKER ("I want to be exact about my own hands here") is gone. However, four near-equivalent constructions remain that constitute the same pattern:

- [x] **L67 (BLOCKER):** "What I did in that war, **set down plainly:**"
  A preamble that announces the narrator will now be plain/honest. Exactly the TIC V1/V14 pattern. The war-summary section does not need this credential.
  **Fix:** Delete the sentence. Begin the section at "I sited camps."

- [x] **L75 (BLOCKER):** "**I am setting this down because it needs to be set down.**"
  The narrator tells the reader why he is recording this. This is the meta-disclaimer scaffolding pattern: the narrator prefaces a difficult section by announcing its necessity. The section is good; the announcement is not needed.
  **Fix:** Delete. Begin the paragraph at "By the time we moved against Sarmizegetusa..."

- [x] **L79 (BLOCKER):** "So there were manned flights at Sarmizegetusa. **I need to say it plain.**"
  Another "I want to be plain/honest/exact" variant. Three of these in a twelve-paragraph span constitutes the chapter's single most damaging pattern.
  **Fix:** Delete "I need to say it plain." The sentence "So there were manned flights at Sarmizegetusa" is already plain. The claim to plainness undermines the plainness.

- [ ] **L83 (borderline):** "**I am setting that down because** I spent every month of it braced for the other thing..."
  This one is arguable. Unlike L75 and L79, the "because" clause here delivers actual content (the narrative fact of Daniel's fear for Celer), not just a claim of honesty. Mark as borderline — reviewers should note it clusters with three cleaner violations above. If any one of L67, L75, L79 is cut, L83 is a SHOULD FIX; if all three are cut, L83 is tolerable.

### 3d. Narrator stepping outside time / future-vantage (ZERO allowed)

- [ ] **L81:** "I have wondered whether those men were grateful or terrified and I think probably both."
  PERMITTED. This is close-retrospect (narrator reports a thought he has had since, which he identifies as ongoing). It does not announce significance from the future; it reports a lingering open question. Within the retrospective frame.

- [ ] **L111:** "That is what I keep coming back to..."
  PERMITTED. Reports the narrator's continuing relationship with a fact, not a future-announced significance. The sentence reports what Daniel felt and keeps feeling — the present-tense "I keep coming back" is the memoir's licensed retrospective voice.

- [ ] **L131:** "I would hear about those games from the city when I got back down..."
  BORDERLINE. This says "I would hear" (from within the warcamp) — it is the narrator predicting his own near future from within the scene. This is mild: it uses the memoir's vantage to report an imminent sequence ("I would later learn") rather than announcing long-term significance. Not a clear BLOCKER but note for coordinator.

- [ ] **L135:** "I do not entirely have the measure of the difference even now, writing it."
  PERMITTED. The phrase "even now, writing it" is a licensed memoir marker — the narrator acknowledges the memoir frame directly. This is the permitted retrospective frame, not the banned dramatic-irony form.

### 3e. "The way you / the way a man / the way a child" constructions (max 3 per chapter)

**Count: 3** — exactly at the limit.

- L53: "He said *freed* the way you'd say a man had been promoted into a worse job..."
- L79: "That is either the honorable version or **the way a man** tells himself it is..."
- L115: "He said it **the way** he had said the bridge would outlast Rome..."

- [x] **Within limit.** No over-limit flag required. However, all three are deployed in their introspective/comparative mode (TIC V10), and the chapter is at the absolute cap. Future chapters must absorb the cost.

### 3f. Wisdom-button scene/chapter endings (max 1 per chapter; aim 0 per 3 chapters)

**Chapter ending type:** IMAGE / ACTION CUT — Daniel puts his hand on the cold stone, a mule balks, he crosses to the Roman bank. Last sentence ends on forward motion and a deferred promise ("a girl at the wharf I had promised, next, to buy"). This is a clean action cut. NOT a wisdom button. Correct.

**Scene-ending audit:**
- Scene 1 close (L37–39): Image cut — "Heras took the collar halves away... I think he simply did not want them in the yard where I would keep looking at them." IMAGE CUT. Good.
- Scene 2 close (L63–65): Dialogue cut — "Don't put a man under it. I heard about that too." DIALOGUE CUT. Good. (The editorial tag after is slightly long but not a wisdom button.)
- Scene 3 close (L99–101): Dialogue cut — "'Right,' Pamphilus said, and went back to the rope." Clean DIALOGUE CUT. Excellent.
- Scene 4 close (L119–121): Dialogue cut — "'Then don't make the face,' he said, and walked off down the slope." DIALOGUE CUT. Good.
- Scene 5 close (L131–133): Narration — "Rome was going to spend the gold on the longest games anyone could remember. I would hear about those games from the city when I got back down, the days and days of them, the killing made into a holiday, paid for out of the carts I had helped count." Borderline action/summary close. Not a wisdom button proper — it is descriptive summary, not portable maxim.

**Internal wisdom buttons (not scene-closers but extractable aphorisms):**

- **L29:** "The chain you can't see is the better fitted of the two." Portable aphorism embedded mid-paragraph. This is the most extractable maxim in the chapter. It restates the scene's thesis (freedom as one cage swapped for another). At mid-paragraph it is less damaging than a scene-closer, but it lands as a pronounced interpretive moment.
- **L123:** "the state does cold sums and a head is a sum that balances." Strong sentence; not extractable without context; probably acceptable.
- **L129:** "because the marks always balance, that is the whole virtue of them." Extractable aphorism at paragraph end. This is a mid-chapter wisdom button. Combined with L29, the chapter has two portable maxims embedded (one above the chapter limit for scene/chapter buttons; neither at a scene close, so technically not triggering the rule — but the density is notable).

- [x] **Within technical limit** (no wisdom button at a scene or chapter close). The two embedded mid-paragraph buttons (L29, L129) are SHOULD FIX items.

### 3g. "Thing" as vague placeholder

- **L9:** "a thing mattered" — acceptable, means "a significant event."
- **L13:** "you do not unlock a thing like that" — acceptable, refers to the collar.
- **L21:** "do some version of the thing that happens in the story" — WEAK. "Thing" here is genuinely vague; the specific noun is "scene" or "moment" or "drama."
- **L21:** "I wanted Pamphilus to make me feel like I had done a **good thing**" — acceptable: the vagueness is intentional (Daniel can't name what he wanted).
- **L43:** "a thing on loan" — acceptable.
- **L45:** "had been **a thing** Trajan always meant to come back and finish" — weak. Replace "a thing" with "a pause" or "an intermission."
- **L49:** "the thing running bank to bank" — acceptable, refers to the bridge.
- **L55:** "I wanted to see what he would do with a **true thing** said plainly" — weak. The noun is "truth" or "compliment."
- **L77:** "the **thing** that killed Sabinus" — acceptable: refers to the described mechanism.
- **L95:** "the kindest **thing** anyone said to me that week" — acceptable.

Worst cases: L21 ("some version of the **thing** that happens in the story"), L45 ("had been **a thing** Trajan..."), L55 ("a **true thing**").

### 3h. Gnomic aphorism stacking

- **L29:** "The chain you can't see is the better fitted of the two." (standalone maxim)
- **L129:** "the marks always balance, that is the whole virtue of them." (standalone maxim)

- [x] **Two standalone aphorisms** embedded in the chapter body (not at scene closes). This is the stacking threshold. SHOULD FIX: cut or absorb one.

---

## 4. Secondary Tic Check

- **Polysyndeton runs** (max 1 per chapter): L5 contains one polysyndeton run ("I counted out the coin... and Macer's clerk weighed it and bit two of the aurei and wrote the receipt, and Pamphilus belonged to me"). One more at L69 ("and the water-point here, upstream, above the horse-lines, above the fouling, and I made them mean it"). Count: 2 runs. At the limit — the second is milder (it is list-of-instructions, not racing panic). Flag for coordinator: technically over, though the second barely qualifies.

- **"Nobody tells you" formula:** Absent. Clean.

- **False-modesty rhythm:** Absent. Clean.

- **"Which is to say" pivot:** Absent. Clean.

- **"Looked at me":** 2 instances — L13 ("Hermes looked at me once, flat") and L59 ("Then he looked at me"). Exactly at the 2-per-chapter limit. Both are earned (the first is Hermes asking a question without words; the second is Apollodorus pivoting to Daniel's work). Within limit.

- **One-sentence paragraphs:** **22 of 63 paragraphs = 34.9%.** Cap is 15% (~9–10 paragraphs for this chapter size). This is the chapter's most severe quantitative violation. At 35%, nearly every dramatic beat is set off in its own paragraph, which exhausts the device. The Pamphilus freeing scene (L5–L37) has 8 one-sentence paragraphs in 21 paragraphs = 38% in that section alone.
  MUST FIX: Absorb at minimum 12–15 one-sentence paragraphs into adjacent text. Priority candidates: L5 (opening paragraph works better as part of the Macer scene); L19 ("He marched north in the spring with my name on the orders" — works as scene-opener but could attach to the scene body); L22 ("And there was the bridge" — scene transition, could attach to L23); L34 ("And then, between the second and third month..."); L35 ("I am setting this down...").

- **Cycle of defeat** (structural tic): Not applicable — no tech arc this chapter. The manned-balloon resumption is handled correctly as earned progress, not as another cycle.

- **Ledger-as-catharsis:** L129 — Daniel balancing the column of looted gold is exactly this pattern: "the marks always balance" as a resolution to a moral crisis. This is notable as one of the specific instances the guide warns about (every emotional beat resolved by counting). SHOULD FIX: End the gold-counting paragraph before the aphorism. Let the image of the column carry it without the summation.

- **Socratic echo:** Absent. Apollodorus's "It's the same knowledge" is not a mirror of Daniel's explanation — it is Apollodorus completing the analysis independently, which is correct for his character.

- **"Let it sit / let that hang":** L77 — "with something under the dryness I won't name." This is a single instance (Daniel, narrator), not deployed across multiple characters. Within limit.

---

## 5. Canon Consistency

- **Daniel's age this chapter:** Expected 24–25 (105–106 AD; born ~81 AD equivalent). Not explicitly stated. Consistent with timeline.

- **Pamphilus's collar ("eleven years"):** L13 — "the eleven years Pamphilus had worn it." Calculation: freed 105–106 AD; collar put on ~94–95 AD (pre-Daniel's arrival in 98 AD). At ch31 (~117–118 AD), collar should have been gone ~12 years — consistent with V4 audit finding that "five years gone" (ch31 V1 error) should be ~12–13 years. The "eleven years of wearing" figure at ch18 is internally consistent. **PASS.**

- **Tyche:** Referenced as "a girl at the wharf I had promised, next, to buy" (L137). Tyche b. ~85 AD; in 105–106 AD she would be ~20–21. "Girl" is acceptable Roman usage and not a precision age claim. Consistent.

- **Lucanus:** Not yet born (ch25–26). Not referenced. No issue.

- **Daniel's name:** "Marcus Ulpius Danihel" appears at L5 in the bill of sale. Correct.

- **Celer:** Alive, present, checks basket rigging (L77). Outline says "Celer alive; not killed here." PASS.

- **Apollodorus:** L47–L63, L115–L119. Described as "gone grayer," consistent with established characterization. His "It will outlast the province" speech (L59) is consistent with his cold-long-view voice profile. PASS.

- **Manned balloon vow:** L79 — "I won't rush untrained people into untested designs." This matches the corrected wording from C1 editorial fix applied to the outline. PASS.

- **Hermes cuts collar:** L13 — "while Hermes set a cold chisel against the rivet at the back of his neck." Canon log [ch18] confirms "HERMES cut off the riveted collar." PASS.

- **Bridge piers:** L49 — "Twenty piers of dressed stone." Canon log [ch18]: "Apollodorus's stone bridge at Drobeta shown (~20 piers)." PASS.

- **Aerial identification of water routes:** The outline requires "Sarmizegetusa water supply identified from aerial surveillance in days not weeks." The chapter shows ground-based identification by Daniel reading the slope and a Greek engineer tracing the lines on foot. The crossbowmen in baskets are described for pass-clearing, not for water-route identification. **PARTIAL MISS** — not a BLOCKER (the outline notes it as a divergence consequence, not a narrative necessity), but the aerial dimension of this beat is absent.

**New canon facts introduced this chapter:**
- Pamphilus freed (informal manumission, Junian Latin status), spring 105 AD, 4,000 sesterces, collar removed by Hermes with cold chisel. Stays at wharf on wages.
- Manned observation balloons with crossbowmen deployed at Sarmizegetusa, double-basket construction, two trained teams (~50+ hours tethered each), voluntary.
- Crossbow bolts standardized, pre-spanned, same quarrel from any basket.
- Apollodorus at Drobeta bridge, 20 stone piers, still alive, still critical of Daniel.
- Sarmizegetusa water supply cut and fouled; city falls by attrition, not assault.
- Decebalus committed suicide (throat); head and right hand carried to Rome.
- Dacian gold counted by Daniel in new figures.
- Celer alive through entire Second Dacian War.

---

## 6. Voice

- **Daniel's voice:** Dry, self-deprecating, controlled. The "I wanted Pamphilus to make me feel like I had done a good thing" (L21) is excellent — honest about his own selfishness without announcing it. "God help me" (L21) is a natural idiom. The war-summary register at L67–L85 is slightly more formal/monumental than Daniel's usual voice (it reads as commemorative), but this is calibrated to the moral weight of the chapter. Consistent with V2 spec. The "I chose to live, and I am not calling that a moral act" (L113) is the clearest instance of his dry, self-aware register doing its best work.

- **Class-marked secondary voices:** Pamphilus speaks in correct register throughout. "You free" (wrong pronoun), "Go where" (no article), "That man. Loud." (telegraphic), "You want I move the ropes so he trips" (wrong subjunctive). All five lines are fragmented, wrong-tense, or missing articles. The CHARACTER_VOICE_GUIDE spec is met.

- **Macer's voice** (L5): "You I'll bleed slow because you'll come back for the girl and I want you to remember I was kind." Correct register — transactional, mean-funny, blunt.

- **Apollodorus's voice** (L53, L59, L115): Cold, peer-level, no softening. "Don't put a man under it. I heard about that too." Consistent with his established profile.

- **No muted lower-class voices:** Pamphilus is given voice throughout. No muting by summary. PASS.

- **Info-delivering monologue check:** No character delivers 4+ consecutive uninterrupted lines. Apollodorus's longest speech is three beats separated by action tags. PASS.

- **Child dialogue:** N/A.

- **Daniel competence:** He is genuinely skilled at what he does (water engineering, logistics), genuinely anxious about what he's done (the water cut), and does not resolve the moral question. He fakes competence in public (makes the cut without hesitation; the private uncertainty is in the memoir). Correctly calibrated.

---

## 7. Verdict

**REVISE**

### Blocking issues (must fix before next use)

1. **One-sentence paragraph density: 34.9% (22 of 63 paragraphs).** Cap is 15%. This is the chapter's most severe structural violation. The device is exhausted across the Pamphilus freeing scene and the war summary. Absorb at least 12 one-sentence paragraphs into adjacent text. Priority: L19 ("I marched north..."), L22 ("And there was the bridge."), L24, L31 (preceding or following dialogue), L34, L35, L43 (attach to preceding paragraph), L47 (attach to following sentence). The Pamphilus dialogue is largely protected (those short lines are the character's voice, not narrative beat-hammering), but the surrounding narration paragraphs can absorb.

2. **L13 — Correctio (negation-before-affirmation):** "the man stood up different. **The man did not stand up different.**" Classic distributed correctio: sets up expectation, then denies it as the structural pivot. Fix: remove the expectation sentence ("In my head freeing a man was...the man stood up different") and begin with the actual scene: "He sat on the bench with his hands on his knees while Hermes set a cold chisel..."

3. **L67, L75, L79 — Three meta-disclaimers clustered in one scene (ZERO allowed):**
   - L67: "What I did in that war, set down plainly:" — Delete.
   - L75: "I am setting this down because it needs to be set down." — Delete.
   - L79: "I need to say it plain." — Delete.
   All three are variants of the banned "I want to be honest/plain/exact" pattern. The prose that follows each of them is strong and does not need the credential. Delete all three.

### Revise items (should fix)

4. **L45 — Correctio-adjacent:** "An intermission, not an ending." A compact "Y, not X" definition. Remove the appositive; the preceding sentence already conveys the point.

5. **L29 — Internal wisdom button:** "The chain you can't see is the better fitted of the two." Extractable maxim mid-paragraph. The image of Pamphilus picking up the shears and going back to the cloth (L35) does the same work more powerfully. Cut this sentence and trust the scene's conclusion.

6. **L129 — Ledger-as-catharsis / wisdom button:** "the marks always balance, that is the whole virtue of them." Cut the aphoristic summation. End the gold-counting paragraph at "the same marks, the same hand." The reader has the moral weight without the label.

7. **Aerial identification of Sarmizegetusa's water routes (missing beat):** The outline specifies this was identified from balloon altitude. The chapter shows ground-based identification. The divergence beat ("aerial surveillance in days not weeks") is claimed in the outline's historical divergence section but is not rendered on the page. Suggest adding one sentence to the water-supply scene: Daniel reading the slope with reference to what he had already seen from altitude, confirming from above what the engineer found on foot. This closes the gap without rewriting the scene.

8. **Powder demolition charges (absent optional beat):** The outline brackets this as "[Optional beat]," so its absence is not a blocker. However, the "inch I had used for two years to drag my feet on the powder" (L113) implies powder is in use elsewhere at the siege. A single sentence noting Daniel saw or heard a demolition charge — without naming it explicitly — would plant the ch45 moral accounting seed at no cost to the scene.

9. **L83 — Borderline meta-disclaimer:** "I am setting that down because I spent every month of it braced for the other thing..." After removing L67, L75, and L79, this one is more exposed as part of the same tic pattern. Trim or integrate: "I spent every month of it braced for the other thing, and the other thing did not come, not in Dacia."

10. **Polysyndeton second run (L69):** "and the water-point here, upstream, above the horse-lines, above the fouling, and I made them mean it" — acceptable as instructions-under-pressure. However, with one run already at L5, this should be the only polysyndeton in the chapter. The two runs together are at the limit. If space allows, vary L69's rhythm slightly.

### Notes for coordinator

- **Aerial water-route identification:** The outline's claim that Sarmizegetusa's water supply was "identified from aerial surveillance in days not weeks" is a stated historical divergence beat. The chapter renders this as ground-based, which is historically plausible and dramatically effective — but it means this specific divergence point is not demonstrated on the page. The coordinator should decide: is the divergence claim in the outline correct and the chapter needs adjustment, or should the outline note be revised to reflect the ground-based rendering?

- **The "I would hear about those games" (L131):** Near-future narration from within the scene. Strictly borderline under the future-vantage rule. Not a BLOCKER (it is the memoir's vantage reporting an imminent sequence, not announcing dramatic significance), but should be watched as a pattern if it recurs in adjacent chapters.

- **Cannon/powder demolition beat (absent optional):** The ch45 moral accounting of Daniel's powder contributions is stronger if ch18 planted a visible demolition moment. Currently only the line at L113 establishes powder awareness. Coordinator should decide whether to add the beat here or accept that ch21 (where powder is fully developed) carries the accounting backward.

- **Pamphilus: collar-years math confirmed consistent.** "Eleven years" at ch18 (105 AD) → collar put on ~94 AD. At ch31 (~117–118 AD), collar gone ~12 years. Consistent with V4 audit's note that "five years gone" (ch31 V1 error) should be ~12–13 years. No continuity error in V3 text.

- **Chapter ending is a genuine image/action cut.** Preserve the hand-on-stone + mule-balks + crosses-the-bridge close. It is the best ending in the chapter and earns the chapter's weight.
