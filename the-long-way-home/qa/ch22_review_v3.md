# QA — Chapter 22: Marcia
**Reviewer:** QA agent (v3 pass)
**Date:** 2026-05-29
**Word count:** ~4,290 words
**V2 change notes applied:** Partial — correctio BLOCKERs partially fixed, age error fixed; monologue problem partially addressed

---

## 1. Plot Beats

*(Source: `outline/updated_ch19_36.md` ch22 entry; `bible/08_canon_log.md` ch22 entry)*

| Beat | Present? | Notes |
|---|---|---|
| Marcia introduced via Heras referral | Yes | Warehouse scene, full entry, characterization strong |
| Marcia enters as profit-sharing partner, refuses wage | Yes | L61 — share vs. wage argument present and load-bearing |
| Tyche–Marcia wary alliance, resolved by error Tyche missed | Yes | Cartage fraud discovery, L79–85 |
| First working small-scale steam pump (C4b required) | Yes | L89–95 — pump runs, leaks, Newcomen insight established |
| Expedition prep: citrus/scurvy provision (C5a required) | Yes | L97 — scurvy note with "sailor who cannot hold a rope" line |
| Expedition prep: food as personal motivation (C5b required) | Yes | L97 — tomatoes/potatoes/cacao drawn from memory |
| Multiple crops on return provision (C5c required) | Yes | L97 — "everything plant-like that grew in quantity and looked like food" |
| Marriage: Marcia proposes, unsentimental, her terms | Yes | L101–116 — spring, year after meeting; share-estate logic intact |
| Marcia proposes, Daniel accepts, witnesses present | Yes | L119 — Heras, Pamphilus + wife, Tyche at wedding |
| Marcia knows Tyche reads English cipher; approves survival plan | Yes | L131–137 — closes chapter |
| Contubernium stage (V2 optional note) | No | Chapter goes directly to lawful marriage. V2 noted this deviation is acceptable if explicitly noted; it is not annotated in the chapter. Flag for coordinator continuity record. |
| Marcia's designs on enterprise survival named | Yes | L121–123 — explicit, in her voice, doing sums |

**Over-resolved beats:** None. The chapter withholds appropriately — Marcia's full "designs" are named at the edge of the visible without being explicated.

**Unplanned beats:** The narrator-analysis of Tyche–Marcia dynamics (L83–85) adds thematic weight not in the outline. It functions as a quiet wisdom-level observation but is grounded in action; acceptable addition.

---

## 2. New V2 Arcs

- **Food arc** (`V2_FOOD_ARC.md`): Present. L97 — tomatoes ("red fruit on vines"), potatoes ("starchy tuber"), cacao ("brown seed pod, bitter, ground and mixed with honey"). Ingredients are era-plausible description (not named; described from Daniel's interior memory). Correct.
- **Prize/innovation arc** (`V2_PRIZE_INNOVATION.md`): N/A for this chapter specifically; Marcia's goal to make prize "grow teeth" is planted at L121.
- **Children's education arc** (`V2_ULPIA_EDUCATION.md`): N/A — children not yet present.
- **Tech/bootstrapping** (`V2_TECH_DEEP_DIVE.md`): Steam pump works at ~1-2% efficiency, leaks, piston-jam on fourth stroke. Correctly rendered as proof of concept, not a win. Newcomen insight accurately stated. Passes.
- **Atlantic/New World** (`V2_NEW_WORLD_CONTACT.md`): Planning notes present. Era is ~108-109 AD, well before Phase D (110+ AD) when ocean program becomes serious. The notes are in Daniel's private cipher — appropriate staging.
- **Historical divergence** (`V2_HISTORICAL_IMPACT.md`): Chapter is a domestic/character chapter. No macro-divergence required. Marcia's enterprise-structuring work (consolidating legal/commercial operations) is background divergence that will pay forward.

---

## 3. Prose Tics — Zero-Tolerance Sweep

### 3a. Correctio / "Not X, it's Y" (ZERO allowed)

**TWO violations found:**

- [x] **CONFIRMED BLOCKER — L97:** `"Not for the pump. For myself."` — Classic "Not [X]. [Y]." pivot. Daniel introduces a second column of expedition notes and defines its purpose by first negating the pump (not for that) then stating himself (for this). Direct-statement fix: *"The second column was mine, not the pump's. I had been eating Roman food for ten years..."* or *"I wrote a second column for myself — not engineering."*

- [x] **BORDERLINE — L95:** `"the steam only needs to push, not to hold"` — This is a "X, not Y" defining-by-negation construction in Daniel's cipher note labeling the Newcomen principle. Per zero-tolerance rules, the form is banned even in technical specifications. Fix: *"the steam pushes; it does not need to hold pressure between strokes"* or *"the piston moves on the push alone; the exhaust does the rest."* The physics is correct; the structure is banned.

No other correctio instances found. The V2 BLOCKER from the outline ("[A share,]" line and the "isn't a wharf" negation) are both resolved in V3: L61 correctly reads "A share means you can stop me — tell me I'm done and hand me my coin" (no negation pivot). L69 reads "building something nobody has the shape of yet" (negation removed).

### 3b. Em dashes (ZERO allowed)

- [x] **None found.** Chapter uses hyphens (-) for compounds and dashes consistently. Clean.

### 3c. Meta-disclaimers / throat-clearing (ZERO allowed)

- [x] **None found.** Clean.

### 3d. Narrator stepping outside time / future-vantage (ZERO allowed)

- [x] **None found.** Close-retrospect narration is used throughout (e.g., "I found, standing in the pepper smell, that I trusted...") and stays within the permitted form — reports what Daniel felt at the time, does not declare forward significance.

One line worth monitoring: L83, "They were never going to be friends in the soft sense." This is retrospective assessment of a relationship that goes forward into the book, but it reports a fact (they remained professional allies, not intimate friends) rather than announcing dramatic significance. **Permitted.**

### 3e. "The way you / the way a man / the way a child" constructions (max 3 per chapter)

- Count: **3**
  - L15: "he said things he'd already decided about, dry, over the top of a cup" — this is not actually a "the way" construction. Checking actual instances:
  - L15: `"the way he said things he'd already decided about"` — 1
  - L121: `"spreading the way the figures had spread"` — 2
  - L27: No "the way" construction here.

Recount from grep data: 3 instances total at L15, L35 ("He used a kinder word. He's a kind man"), and L121. Wait — grep showed exactly 3: L15, L35 ("the way"), and L121. All three:

  - L15: `"the way he said things he'd already decided about, dry, over the top of a cup"` — earned; characterizes Heras's delivery
  - L35: `"You've outgrown your own counting"` — not a "the way" construction; the grep hit was elsewhere on L35. The actual hit from grep: L15 and L121. Third hit was L35's paragraph. Confirmed from grep output: hits at L15, L35, and L121.

- Count: **3** — at the limit. **Within cap.**
- [ ] Within limit (3 or fewer)

### 3f. Wisdom-button scene/chapter endings (max 1 per chapter; aim 0 per 3 chapters)

Scene-ending audit:

| Scene | Close line | Type |
|---|---|---|
| Scene 1 (L12) | "I found a woman instead." | Revelation/action cut |
| Scene 2 (L22) | "Don't be charming at her. She's had charming men...and she counts the spoons after." | Dialogue cut |
| Scene 3 (L48) | "That was a test. You failed it. Now I know what I'd be dealing with." | Dialogue cut |
| Scene 4 (L71) | "I trusted that combination more than I'd trusted anyone since Heras." | **Mild wisdom-button** |
| Scene 5 (L86) | "Within a season the contracts were clean, the cartage thief was gone, and the shed lease had been renegotiated." | Action cut (inventory) |
| Scene 6 (L98) | "Then I went back to the cipher for the parts I didn't want anyone to read." | Action cut |
| Scene 7 (L116) | "'Don't,' she said, 'look at me like that. We're doing the year's reckoning.'" | Dialogue cut (strong) |
| Scene 8 (L124) | "She finished her column and went on to the next." | Silence/action cut (strong) |
| Scene 9/chapter (L138) | "she put her ink-stained hand over mine on the closed book, flat, the whole hand this time, and left it there." | Image cut (excellent) |

- **Wisdom buttons: 1** (Scene 4 close, L71)
- Chapter ending: Image cut — ink-stained hand over the closed book. Clean.
- [x] Within limit (1 or fewer)

**Note on L71:** "I trusted that combination more than I'd trusted anyone since Heras" — this is a scene closer that does interpretive work (assigns trust-weight to the combination of Marcia's competence + her acknowledged ignorance). It is gentle as wisdom buttons go and does not extract as a standalone aphorism without context. Flagged as a SHOULD FIX rather than MUST FIX — the scene could end on "and I found, standing in the pepper smell, that I trusted that combination" and drop the Heras comparison.

### 3g. "Thing" as vague placeholder

Lines with "thing": L39, L51, L55, L71, L111, L129, L137.

- L39: `"whether the thing works"` — Marcia's speech; refers to Daniel's inventions collectively. Context-dependent vagueness; not ideal but defensible.
- L51: `"the most useful thing anyone had done for me in months"` — vague. "The number was the most useful fact anyone had given me in months" is sharper.
- L55: `"the prize money that went out as a clean gift and could have gone out as a thing that bought me obligation"` — "thing" substituting for "instrument" or "lever." Flag.
- L71: `"the one thing that wasn't her business"` — "the fact she didn't know" or "the secret she hadn't asked for." Flag.
- L111: `"let it be mine to take or not, laid out plain, no leash on it"` — "thing" not present here.
- L129: `"the brittle batch beside the good one, indistinguishable to the eye, the whole stubborn wall of it"` — "thing" not present here.
- L137: `"between us the thing lives"` — refers to the enterprise/work. Vague but in Marcia's register, where compression is characteristic.

**Worst cases:** L51 ("the most useful thing") and L55 ("a thing that bought me obligation") have specific nouns available.

- [ ] Worst cases: L51 → "the most useful reckoning anyone had done for me in months" or "the most useful number"; L55 → "a thing that bought me obligation" → "an instrument of obligation" or "leverage I held"

### 3h. Gnomic aphorism stacking (flag if 2+ in a single chapter)

Candidates:
- L39: `"Everything is a toy until it makes money"` — Marcia's first meeting; in character, not Daniel's voice
- L61: `"A share means we sink together"` — functional, not aphoristic
- L69: `"I'm not doing you a kindness. I want in while in is cheap."` — transactional, not a maxim
- L83: `"Tyche out of a slave's hidden cleverness, Marcia out of a widow's held breath"` — narrator summary, elegant parallel
- L121: `"something that spreads on its own cannot be killed by killing one man"` — **portable maxim, extractable**

Two candidates rise to gnomic level: L39 (Marcia's voice, characterization-embedded) and L121 (narrator analysis, extractable). L83 is elegant but structural rather than maxim-form.

- [x] **Stacked:** L39 (in-character aphorism) + L121 (narrator maxim) — within the chapter's 2-instance tolerance, but note that L121 also ends the Scene 8 block (before the final scene) and functions almost as a wisdom button there. It is embedded in a long inventory sentence about Marcia's designs, so it does not close a scene cleanly — mitigated. Flag as SHOULD FIX for the narrator's voice extracting a maxim at L121.

---

## 4. Secondary Tic Check

- **Polysyndeton runs** (max 1 per chapter): count 2–3 notable runs (L5 opening paragraph with its list of obligations; L69 with "Because...Because...Because..."; L121 with "She wanted...She wanted...She wanted"). L5 is a legitimate inventory of Daniel's obligations — appropriate for the opening. L69 is a structural "Because" train (3 repetitions) in Marcia's voice explaining motivation — her syntax; borderline but in-character. L121 is the narrator's summary tripling. **Flag L69 and L121 as the second polysyndeton run; the chapter carries two.**
  - count 2 — [ ] flag: L69 ("Because" train) and L121 ("She wanted...She wanted...She wanted")

- **"Nobody tells you" formula** (max 1 per book): [ ] absent

- **False-modesty rhythm** ("I was an idiot" then immediate sophistication): [ ] absent — Daniel fails Marcia's test genuinely; this is not false modesty followed by sophistication. The failure lands.

- **"Which is to say" pivot** (max 1 per 10 chapters): count 0 — [ ] OK

- **"Looked at me"** (max 2 per chapter): count 2 (L69: "She looked at me directly"; L119: "looked at me and said...") — [x] at limit, OK

- **One-sentence paragraphs** (max 15% of paragraphs): count 16 of 60 paragraphs = **26.7%** — [ ] **FLAG: over the 15% cap (cap = 9 paragraphs)**

  Excess one-sentence paragraphs (beyond the 9-paragraph budget): 7 should be absorbed. Candidates for absorption (not doing pivot/revelation work):
  - L8: `"Why would she take it on, then."` — could be absorbed into preceding narration
  - L13: `"I don't fly anymore."` — dialogue beat; earns isolation (Marcia already knows; the line's brevity is the point); KEEP
  - L16: `"They're not toys."` — dialogue beat; earns isolation; KEEP
  - L26: `"And your price."` — dialogue; KEEP
  - L45: `"It was Marcia who said the word first, of course it was, because she said the hard words first about everything."` — could be absorbed into following paragraph
  - L47: `"She picked up the stylus, set it down again."` — earns isolation (action beat in high-stakes scene); borderline KEEP
  - L55: scene 8 (L124): `"She was building the part that came after me..."` — this is a FULL paragraph, not one-sentence. Not in this count.
  - L59: `"Tyche reads that."` / L58: `"Tyche reads that," she said.` — The call-and-response pair earns isolation; KEEP both.

  Candidates most appropriate to absorb: L8 (fold into preceding Heras narration) and L45 (fold into the marriage proposal scene-opening). These would bring the total to 14 (23.3%) — still over cap. Additional absorption needed: L33 (`"Tyche and Marcia were always going to be a problem..."` — opens a scene, OK as standalone). L39 (`"Around this time Hermes and I got the first small pump to run."` — scene-opening; earns isolation as pivot). L44 (`"We married a little over a year after the day I failed her test..."` — scene-opening; earns isolation).

  **Net: 26.7% is a hard overage. Even absorbing the weakest 4–5 candidates lands at ~18–20%, still over the 15% cap. This is a SHOULD FIX with a specific audit list.**

- **Cycle of defeat** (idea → works once → fails → depression → pivot): The steam pump sequence (L89–95) is explicitly NOT a cycle of defeat — the pump works on first try (leaky, imperfect, but works). The outline requirement for "show the pump running, not described afterward" is met. [ ] not present as the cycle pattern.

- **Ledger-as-catharsis** (counting/tallying to resolve every emotional beat): The year's reckoning at L41–55 is a tally, but it is in service of Marcia's test, not to resolve Daniel's emotion. The marriage scene at L101–116 is deliberately set during the year's reckoning, but the choice is not made through arithmetic. [ ] absent as a catharsis mechanism.

- **Socratic echo** (secondary character mirrors Daniel's explanation): [ ] absent — Marcia does not mirror Daniel; she corrects and instructs.

- **"Let it sit / let that hang"**: Marcia "let me find out" at L33 — one instance, assigned to one character. [ ] single character only, OK.

---

## 5. Canon Consistency

*(Check against `bible/08_canon_log.md`, `bible/03_timeline.md`, `bible/02_characters.md`)*

- **Daniel's age this chapter** (ch01 = 17 in 98 AD; ch22 = ~108-109 AD): expected 27–28 / stated or implied ~28 (canon log entry: "Daniel ~28") — [x] consistent

- **Other character ages:**
  - Tyche stated "a freedwoman of twenty-four" (L9). Born ~85 AD, chapter ~108-109 AD = 23–24 years old. [x] consistent. The V2 BLOCKER (age error: original "eighteen") is confirmed FIXED in V3.
  - Marcia stated "a woman of about thirty-five" (L27) and "I'm thirty-five" (L69). Canon log: "b. ~73 AD." 108 – 73 = 35. [x] consistent.
  - Marcia's "eleven years" of running Caepio's (L17, L83): if she's ~35 and her husband died when she was ~24, this is ~73+24 = 97 AD. Consistent with her being a widow running the warehouse before Daniel arrived (98 AD). [x] consistent.

- **Dates / era:** Chapter era ~108-109 AD — [x] consistent with timeline (Phase C/D border).

- **Tech state (`bible/04_tech_schedule.md`):**
  - Steam pump: first run in this chapter. Matches C4b requirement (Phase C, ~108-109 AD). [x] yes
  - Powder/cannon: referenced as existing ("cannon drawings," "corned powder") — consistent with ch21 events. [x] yes
  - Press: running, Eros the pressman on monthly wage (L5). [x] consistent
  - Niter beds / sulfur: mentioned in L5 ("niter beds I had to pretend belonged to a man in volcano country, the sulfur that came up the river under another name") — consistent with ch21 cover. [x] yes
  - Steel: Hermes's forge described as "swallowing money on steel that worked one batch in four" (L5) and "Hermes's failed steel, the brittle batch beside the good one" (L129). [x] consistent — steel still unsolved.

- **Named objects / relics:**
  - "The little book...with the dead glass folded in the cloth" (L131) — consistent with canon log (phone kept wrapped in oiled wool under a floorboard; known to Tyche). [x] consistent. Small note: the phone was "kept under a floorboard in a box" per canon log (ch24 records this); here in ch22 it's in the tally-room and Marcia handles it. This is set ~108-109 AD, before the explicit ch24 "under a floorboard" canon. No direct contradiction — the floorboard hiding comes later. [x] acceptable.
  - The cipher: Tyche reads it. Marcia correctly deduces "Tyche reads that." [x] consistent with ch21 (cipher in English, only Tyche can read it).

- **Pamphilus:**
  - Present at the wedding (L119) with his wife. Freed in ch18 (manumission). [x] consistent.
  - Wedding line: "You done good" — this is Pamphilus's first directly quoted speech in the chapter and matches the V2 FIX requirement (at least 4 spoken lines across the book; here he gets one). Voice register: 3 words, grammatically compressed, class-marked ("done" not "did"), concrete, no subordinate clauses. [x] correct register.

- **Other established facts:**
  - Marcia suppressed knowledge of the soldier's death: L33, "You stopped after the soldier...that was not the public story." [x] consistent with canon log ch22 entry ("She knows the SUPPRESSED truth that the dead Danube soldier was not a tethered observer").
  - Macer still called "Titus Flavius Macer" and prize attributed to him (L39). [x] consistent with ch19 "Macer Prize" structure.
  - Heras as Marcia's household physician: L15 establishes this explicitly. [x] consistent with canon log ch22 ("Heras (her household physician for years) referred Daniel").
  - Geta described as "in his room off the well" (L5) — Geta's room was built by Daniel after the accident per ch21 canon. [x] consistent.

**New canon facts introduced this chapter:**
- Marcia born ~73 AD (age 35 at ~108 AD); confirmed and canonized.
- Tyche confirmed as "a freedwoman of twenty-four" (~108-109 AD), birth ~85 AD confirmed.
- Steam pump: first run, leaky, three joints, wooden valve, waist-high cylinder; piston jams on fourth stroke; Newcomen principle named in cipher.
- First expedition provisioning notes written in cipher: tomatoes/potatoes/cacao pictures + citrus-for-scurvy instruction in Latin.
- Marcia + Tyche alliance formed; Marcia pays Tyche a fee from her own share for the new figures instruction.
- Formal marriage: spring ~109 AD; witnesses: Heras, Pamphilus + wife, Tyche.
- Marcia's full agenda named: sheets by the thousand; prize to "grow teeth"; enterprise to survive Daniel's death.
- Marcia knows about the English cipher and approves it as the enterprise's survival mechanism.

---

## 6. Voice

- **Daniel's voice:** Dry, self-deprecating, specific. The opening paragraph (L5) is the book's characteristic inventory-under-pressure voice. The Marcia meeting renders Daniel as genuinely wrong-footed (fails the test; can't answer the year's-end question). He does not smooth it into charm. Voice is [x] consistent with V2 spec.

- **Class-marked secondary voices:**
  - Pamphilus: "You done good" (L119) — 3-word, ungrammatical, correct register. [x] good.
  - Hermes: "It keeps stopping" (L91) — terse, demand-form, hammer-rhythm. [x] correct.
  - Tyche: "She's right, though" (L51); "Show me how you saw that" (L79); "He's careless with money but he's not a liar, watch the first and trust the second" (L119). Her wedding-gift line at L119 is the most polished thing she says in the chapter and lands on the aphoristic end of her register. It is a quotable line given to Marcia (not stated aloud to Daniel), which is consistent with how Tyche operates; the reportage frame ("Marcia told me later") distances the sharpness appropriately. Borderline — could be slightly plainer — but not a blocker.
  - Heras: "Don't be charming at her. She's had charming men in her warehouse her whole life and she counts the spoons after." (L21) — dry, ironic, elliptical. [x] correct Heras register.

- **No muted mutes:** Pamphilus speaks (L119). Heras speaks (L15, L21). No crowd scene requiring hecklers. [x] N/A for crowd; present for named characters.

- **Info-delivering monologue check:**
  - L57: 8-sentence paragraph, but broken mid-speech by "She tapped the tablet." Two speech halves: (1) law-as-tool framing (4 sentences) + (2) partnership terms (4 sentences). The action break mitigates the info-dump concern. **BORDERLINE** — the second half runs 4 sentences unbroken on a single business proposition. SHOULD FIX: break the second speech half with one more mid-speech action (e.g., she moves to the door, glances at the loading floor, then turns back).
  - L105: 9-sentence paragraph for the marriage proposal. Broken by "She paused and squared the tablet she'd been working on." First half: 4 sentences (legal/practical case). Second half: 4 sentences (children/standing argument). The second half particularly runs the legal case about freeborn children for 4 sentences without interruption. **SHOULD FIX:** add one beat in the second half — Marcia setting down the stylus, or a pause — to break the lecture rhythm.
  - L69: "Because...Because...Because..." — 6 sentences, broken by two action tags. OK. Not a blocker.

- **Child dialogue** (if child under 12 present): N/A — no children present in this chapter.

- **Daniel competence:** He fails the year's-end question genuinely (L41–44). He admits he came looking to hire a clerk and found something else (L63). He cannot read the contract Latin (L7). He is genuinely wrong-footed by Marcia throughout. [x] competence is appropriately limited; he does not fake confidence here.

---

## 7. Verdict

**REVISE**

### Blocking issues (must fix before next use)

1. **Correctio — L97 — "Not for the pump. For myself."**
   Banned "Not X. Y." construction. Fix: *"The second column was personal — what I wanted to bring back for my own table, not engineering notes."* or *"I started a second column. The pump was in the first; this one was mine."* The food-motivation content (tomatoes, potatoes, cacao) is load-bearing and must be preserved; only the negation-pivot needs reworking.

2. **One-sentence paragraph density — 26.7% (16 of 60 paragraphs) — cap is 15%**
   Seven paragraphs need to be absorbed into adjacent text. Priority candidates for absorption (not doing irreplaceable pivot work):
   - L8: `"Why would she take it on, then."` — absorb into preceding narration: *"...and she has not been cheated in eleven years that anyone can name. I asked why she would take it on." [then Heras's response]*
   - L45: `"It was Marcia who said the word first, of course it was, because she said the hard words first about everything."` — absorb into the following paragraph as its opening clause.
   - L33: `"Tyche and Marcia were always going to be a problem, and they were, for about a month, and then they weren't, and I had almost nothing to do with the resolving of it, which is the only reason it worked."` — this scene-opener can have one clause folded into the scene above, reducing the one-liner count.
   - L39: `"Around this time Hermes and I got the first small pump to run."` — earns its isolation as a scene pivot; KEEP this one specifically.
   - L44: `"We married a little over a year after the day I failed her test, in the spring, by which point we had been running the business together long enough that the marriage was the smaller change of the two."` — absorb opening sentence of following paragraph.

### Revise items (should fix)

1. **Correctio borderline — L95 — "the steam only needs to push, not to hold"**
   Technically matches the "X, not Y" defining-by-negation form. Fix: *"the steam pushes; the pressure does not have to hold between strokes"* or *"the steam does one job, push, and the rest is atmosphere."*

2. **Monologue length — L57 and L105**
   Both Marcia speeches exceed 4 unbroken sentences in their second halves. Each needs one mid-speech action break. L57: add a beat after "eat well" (she stands, or moves to the door) before "I'll take it on." L105: add a beat after "we've been partners a year" or within the freeborn-children argument.

3. **Wisdom-button — L71 — "I trusted that combination more than I'd trusted anyone since Heras"**
   Scene 4 closer assigns interpretive weight where the scene has already done the work. The scene could end on: *"We did. She was right about everything she could see, and didn't know the one thing that wasn't her business, and I found, standing in the pepper smell, that I trusted that combination."* — drop the Heras comparison. The scene earns its own trust; the Heras anchor explains rather than deepens.

4. **"Thing" as vague placeholder — L51 and L55**
   - L51: "the most useful thing anyone had done for me in months" → *"the most useful number anyone had put in front of me in months"*
   - L55: "a thing that bought me obligation" → *"a lever of obligation"* or *"an instrument that bought me obligation in return"*

5. **Second polysyndeton run — L121 ("She wanted...She wanted...She wanted")**
   The triple "She wanted" in the narrator's inventory of Marcia's designs is a structural echo of L69's "Because...Because...Because." Two polysyndeton runs in a chapter is at the limit. The L121 run is gentler (it's narration, not dialogue), but consider breaking the third "She wanted" with a different construction: *"She wanted the prize to grow teeth... She wanted the enterprise built to outlive Daniel. She had said as much, doing the reckoning..."*

6. **Gnomic aphorism — L121 — "something that spreads on its own cannot be killed by killing one man"**
   Extractable maxim embedded in the narrator's summary of Marcia's designs. The maxim does the analytical work the scene should leave to the reader. Consider: end the paragraph after "let it fail" and cut the "spreading the way the figures had spread because something that spreads on its own cannot be killed by killing one man." The container image (strongbox, shape, people who can't let it fail) is sufficient.

### Notes for coordinator

- **Contubernium stage omitted:** V2 outline notes this is acceptable if documented. The chapter goes directly from partnership to lawful marriage without an informal union stage. This is now confirmed omitted in V3 — coordinator should decide whether to flag this as a continuity note for the canon log.
- **Phone relic location:** In ch22 (L131) the dead phone is in the tally-room for Marcia to handle on wedding night. Canon log ch24 places it "under a floorboard in a box" — but ch24 is set ~110 AD, one year after ch22 (~109 AD). No contradiction; the hiding under the floorboard is a later precaution. No fix needed, but writers of ch23–24 should be aware the phone was still accessible in the tally-room at ch22.
- **New canon to log:** Steam pump first run (~108-109 AD), all specs above. Expedition provisioning notes begun in cipher. Marriage spring ~109 AD with witness list. Marcia's explicit awareness of and endorsement of the cipher/Tyche survival plan.
- **Pamphilus spoken line count:** He has one quoted line in this chapter ("You done good"). Running count across the book should be tracked against the V2 minimum of 4 spoken lines; this chapter contributes 1.
- **Tyche's wedding-gift line (L119):** "He's careless with money but he's not a liar, watch the first and trust the second" — this is the sharpest, most aphoristic line she's given in the chapter. It is framed as reported speech (Marcia tells Daniel later), which is appropriate. Monitor: if Tyche accumulates too many quotable epigrams across chapters, it flattens her "terse/fragmentary" register. One here is fine; watch in ch23 and beyond.
