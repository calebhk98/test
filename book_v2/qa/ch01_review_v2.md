# QA — Chapter 1: Waking
**Reviewer:** QA Agent (claude-sonnet-4-6)
**Date:** 2026-05-27
**Word count:** ~3,620 words (title line excluded)
**V2 change notes applied:** Partial — see section-by-section notes below

---

## 1. Plot Beats
*(Expected beats from `chapter_list.md` ch01 entry.)*

| Beat | Present? | Notes |
|---|---|---|
| Sensory landing: light, smell, sound — ancient Rome before the word "Rome" appears | yes | Opening sequence: wrong birds, wrong air, broken stubble, woodsmoke — excellent. "Rome" never named. |
| Phone as ticking clock: uses it wrong at first, corrects, starts voice-recording | partial | Phone used (camera, dialer, maps) but the "corrects" beat is absent. He does NOT pivot to voice-recording anything useful in this chapter. He takes a photo and calls 911 and his mom. No survival-recording behavior begins here. |
| First words attempted in Latin: failure; humiliation; dark comedy | no | He speaks English at the villagers; they don't understand. But no Latin attempted — no Latin in this chapter at all. This is consistent with the chapter ending before cell/Heras, but the brief lists it as a ch01 beat. The first Latin attempt appears to be deferred to ch02+. Flag for coordinator: brief may be slightly over-ambitious for scope. |
| The rope: arrested, hands bound, led toward Rome | no | Chapter ends at the moment four spearmen approach. The arrest and rope are ch02 per canon log. The chapter covers only the arrival-to-arrest moment. This is consistent with the prose as written, but the brief includes "the rope" as a ch01 beat. Mild scope mismatch between brief and prose. |
| The cell: time to think; beginning of deliberate calculation | no | Deferred to ch02, consistent with canon. |
| Phone death: final entry is something mundane, not heroic | no | Phone does NOT die in ch01. It reads 98% at end. Phone death occurs in ch04 per canon log. The brief describes a two-week arc, so phone death was never going to occur in a chapter that ends hours after arrival. Brief description is a summary of the arc, not all ch01 beats. |
| Daniel's interior monologue establishes his register: dry, self-deprecating, profane, not a hero | yes | Register is well-established. Dry, self-deprecating, panicked-but-functional teen voice. Not profane in the text as drafted (no profanity), but the voice is correct. |

**Over-resolved beats:** None. The Colosseum reveal is architecturally built, never declared.

**Unplanned beats:** None significant — the chapter stays precisely within the arc of waking to first contact with armed men.

**Scope note for coordinator:** The ch01 brief compresses the full two-week arc (arrest, cell, phone death) into what the prose correctly renders as a single morning. The prose ends at the right place. The brief is written as a summary of the arrival sequence, not as a strict per-scene checklist. No action required; just flag so future QA agents don't mark "no rope" as a miss when the chapter's scope is correct.

---

## 2. New V2 Arcs
*(Check only arcs the chapter_list.md specifies for this chapter.)*

- **Food arc** (`V2_FOOD_ARC.md`): Absent — N/A. Ch01 is pre-any food encounter.
- **Prize/innovation arc** (`V2_PRIZE_INNOVATION.md`): N/A. Too early.
- **Children's education arc** (`V2_ULPIA_EDUCATION.md`): N/A. Ch01 = 98 AD. Lucanus born ~108 AD, Ulpia ~118 AD. No child scenes present or expected. Chronology check: PASS.
- **Tech/bootstrapping** (`V2_TECH_DEEP_DIVE.md`): N/A for ch01.
- **Atlantic/New World** (`V2_NEW_WORLD_CONTACT.md`): N/A.
- **Historical divergence** (`V2_HISTORICAL_IMPACT.md`): N/A — arrival chapter; divergence ledger correctly empty.

---

## 3. Prose Tics — Zero-Tolerance Sweep

### 3a. Correctio / "Not X, it's Y" (ZERO allowed)

- [ ] Instances found:
  - L47: "Not Spanish. We get a lot of Spanish at the store and I can fake my way through a little and this was not it, not French from two years of it in school, not anything." — The standalone "Not Spanish." is a correctio sentence fragment followed by elaboration. Ruling: **borderline / revise**. The full construction is a list-of-negations without naming a positive ("it was Latin" never gets said in the same breath), which slightly differentiates it from the pure correctio template ("Not X. Y."), but it shares the same structure and rhythm and should be revised to move away from the flagged pattern. Suggest: "It had the edges of something old, something I couldn't place — not Spanish, not French, not anything from two years of school."
  - L39: "She did not look annoyed, not the expression of someone spotting a trespasser on a set." — A soft correctio ("did not look X, [it was] Y"). The Y is implied rather than stated, which mitigates it, but the construction opens with a negation and then names what it wasn't. Ruling: **borderline / revise**. Minor; suggest reconsidering the phrasing.
  - L45: "this was not it. It was thick and uneven and it hung wrong." — Structure: [negation]. [positive]. This is a correctio. "This was not it" followed by "It was thick and uneven" is exactly "It was not X. It was Y." Ruling: **violation**. Line 45: "...I know what machine-made cloth looks like and this was not it. It was thick and uneven and it hung wrong." Fix: cut "this was not it." Start with the positive: "I know what machine-made cloth looks like. This was thick and uneven and it hung wrong."

**Total correctio violations: 1 confirmed (L45), 2 borderline (L47, L39).**

### 3b. Em dashes (ZERO allowed)
- [x] None found. Clean.

### 3c. Meta-disclaimers / throat-clearing (ZERO allowed)
- [x] None found. Clean.

### 3d. Narrator stepping outside time / future-vantage (ZERO allowed)

- [x] Future-vantage line flagged in V2_CHAPTER_CHANGE_NOTES — **CONFIRMED REMOVED in V2**. The line "I want to be careful here, because later on people would ask me about this morning and I would lie about how clear it was, how I knew right away" does **not appear** in the chapter. This is a V2 fix confirmed applied. PASS.

- Additional instances to check:
  - L25: "That was the thing that made my chest go tight, and I couldn't have told you why at the time." — The phrase "at the time" signals retrospective narration. Ruling: **permitted**. This is close-retrospect that reports what Daniel felt then, not future-vantage that announces significance from the future. It does not declare what it "would mean" later.
  - L39: "...a thing I have never had a face do to me before." — "I have never" is a retrospective assertion from narrative present. Ruling: **permitted within the memoir frame**. It reports Daniel's personal experience inventory, not future significance. Comparable to the "I know now" permitted form. Not a blocker.

### 3e. "The way you / the way a man / the way a child" constructions (max 3 per chapter)
- L63: "I looked at it the way you look at anything."
- L77: "my brain went to numbers the way it always does"

**Count: 2** — Within limit (3 or fewer). PASS.

### 3f. Wisdom-button scene/chapter endings (max 1 per chapter; aim 0 per 3 chapters)

- **Chapter ending type:** action / image — The chapter ends on: "I put the phone in my pocket. I put my hands up, palms out, the only word I had in any language they could possibly want." This is an action cut at the moment of surrender/contact. Not a wisdom button. PASS.

- Scene-ending audit (the chapter has one continuous scene with embedded sub-moments):
  - Colosseum reveal close (L67): "I stood on the path with the wind moving the dry grass around my boots and I looked at the unbroken Colosseum and the bottom went out of everything." — Image cut. Concrete. Not a button. PASS.
  - Math paragraph close (L79): "Two thousand years. The number sat in front of me. I could not make it mean anything. I tried to and it just sat there, too big, a count that had stopped being a count and become a wall." — This is borderline. "A count that had stopped being a count and become a wall" has the rhythm of a gnomic closer. It restates the meaning (the number is incomprehensible) in a slightly aphoristic form. **Revise note:** the line is acceptable as written since it's mid-chapter, not a scene-close, but flag for the "stopped being a count / become a wall" framing — it leans toward wisdom-button.
  - Chapter close (L87-88): action cut. PASS.

- [x] Within limit.

### 3g. "Thing" as vague placeholder

Multiple uses; worst cases:
- L3: "The first thing I got wrong" — acceptable; "thing" is the standard idiom here; no specific noun is better.
- L9: "the first thing I did" — acceptable.
- L13: "the only thing that did" — acceptable.
- L13: "the sky was doing that thing where" — **flag**. "That thing where" is the vague-placeholder form. Suggest: "the sky was at that in-between state where it's the kind of blue..."
- L19: "the first thing my body understood" — acceptable.
- L25: "That was the thing that made my chest go tight" — **flag**. "That was the thing" is vague. Suggest: "That was what made my chest go tight" or name it directly ("The sound was what made my chest go tight").
- L35: "A movie set. That was the word my brain reached for and grabbed and held with both hands." — no "thing" issue.
- L51: "which is the stupidest thing you can do" — acceptable.
- L53: "There was a thing painted on the wall" — **flag**. "A thing painted" should be "a word painted" or "an inscription."
- L59: "the thing I'd say to the first cop" — acceptable idiom.
- L69: "this is a thing people do" — acceptable (dismissive register, intentional).
- L77: "a strange thing to reach for" — **acceptable** in context (self-aware).

**Three flagged uses** (L13, L25, L53) where a specific noun was available. None rising to blocking level; revise note.

### 3h. Gnomic aphorism stacking (flag if 2+ in a single chapter)
- L79 close: "a count that had stopped being a count and become a wall" — borderline gnomic.
- No second instance rises to the level of a standalone maxim.

- [x] No stacking found.

---

## 4. Secondary Tic Check

- **Polysyndeton runs** (max 1 per chapter): The chapter has one strong polysyndeton run at L69: "But the mud huts. But the cloth. But the letters that weren't words and the man who put his kid behind him and the pigs and the cart with the wooden axle and the air that was full and the birds I didn't know and the path with no tire tracks, none, not one..." This works; it's a genuine panic-cascade. There is a second lighter run at L45 ("and they looked at my jeans and they looked at my boots and they looked at the shirt..."). Count: 2 polysyndeton runs. **Flag**: the L45 instance is shorter and lower-pressure; consider breaking the anaphora ("They looked at my jeans, my boots, the shirt...") to keep the L69 run as the chapter's single deployed polysyndeton.

- **"Nobody tells you" formula** (max 1 per book): absent. PASS.
- **False-modesty rhythm** ("I was an idiot" then immediate sophistication): L77 — "I know that sounds like a strange thing to reach for sitting in the dirt outside a city that couldn't exist, but it's true, it's the one thing I've always had." This is a mild version: Daniel prefaces his math ability with a self-deprecating disclaimer, then immediately demonstrates sophisticated estimation. Not a full "I was an idiot" instance, but the rhythm is present. PASS — acceptable level, single occurrence.
- **"Which is to say" pivot** (max 1 per 10 chapters): count 0 — PASS.
- **"Looked at me"** (max 2 per chapter): L47 only instance close to the construction: "They looked at my jeans and they looked at my boots and they looked at the shirt." — "looked at me" in the specific banned sense (direct eye contact as filler) does not appear. PASS.
- **One-sentence paragraphs** (max 15% of paragraphs): count ~13 single-sentence paragraphs of ~43 total paragraphs = **~30%**. This is over the 15% limit. The chapter's one-sentence paragraphs include:
  - L7: "I sat up." — earned.
  - L11: "There were no roads." — strong.
  - L23: "Birds started." — strong.
  - L27: "I started walking because standing was worse." — this is two clauses and somewhat earned.
  - L33: "The settlement came up on me slow." — fine as a new-section opener.
  - L57: "There was a city." — strong, the setup for the reveal.
  - L61: "And then I saw the building on the near edge of it." — strong delay.
  - L65: "And this one was whole." — strong payoff.
  - L67: "I stood on the path with the wind moving the dry grass around my boots and I looked at the unbroken Colosseum and the bottom went out of everything." — this is a longer sentence, not a fragment, but it stands alone.
  - L71: "The phone." — strong pivot.
  - Several others (L37: "Then there were more buildings..."; L43: "Nothing."; L83: "I got up...").

  **Flag**: At ~30%, this exceeds the 15% cap. However, given the chapter's dramatic structure — the Colosseum reveal is explicitly built through a series of short paragraphs — many of these are structurally load-bearing. The one-sentence paragraph budget could be trimmed by absorbing L27, L33, and the L37 sentence into adjacent paragraphs without harming the reveal. Suggest: target ~8-10 one-sentence paragraphs (to ~19-23%), preserving the reveal sequence.

- **Cycle of defeat** (idea → works once → fails → depression → pivot): not present — N/A for ch01.
- **Ledger-as-catharsis**: absent. PASS.
- **Socratic echo**: absent (no secondary character present long enough). PASS.
- **"Let it sit / let that hang"**: absent. PASS.

---

## 5. Canon Consistency
*(Check against `bible/08_canon_log.md` and `bible/03_timeline.md`.)*

- **Daniel's age this chapter**: expected 17 (98 AD) / not stated in text but consistent — timeline says 17 in 98 AD; no age is stated; no contradiction. PASS.
- **Other character ages**: no named characters introduced this chapter; villagers and spearmen unnamed and ageless. PASS.
- **Dates / era**: Chapter era is 98 AD. Phone shows 6:14 AM (no date). Colosseum is described as "whole and new," consistent with 80 AD completion. Season reads as late-summer/harvest (stubble field, dry pale gold cut wheat). Canon log confirms "late-summer/harvest." PASS.
- **Tech state**: N/A — arrival only. No tech introduced beyond the phone.
- **Named objects / relics**:
  - Phone: 98% battery, no signal, displays time — matches canon log exactly ("98%, no signal/GPS, displays time"). PASS.
  - Clothes: "blue jeans, gray hardware-store T-shirt (Brentwood Hardware logo, cracked to a ghost, small triangular hole at left shoulder seam), brown steel-toe leather work boots, cheap nylon belt, house key / spare to mom's Corolla / store back-door key." Canon log lists: "blue jeans, gray T-shirt with a small hole at the collar, brown steel-toe leather work boots, a cheap nylon belt." PARTIAL MATCH — the canon log says "small hole at the collar" but the prose places the hole "at the left shoulder seam." Also the canon says "gray T-shirt" with no brand, but the prose adds "Brentwood Hardware logo cracked and faded to a ghost." See V2 change notes: the shirt was intentionally given a specific identifier (Brentwood Hardware). **Canon log needs updating to reflect V2 shirt details** — flag for coordinator.
  - Colosseum: described as "round" and estimated at "six hundred feet across at least" with "four rows of arches, call it forty feet a row with the stuff on top, that's a hundred sixty, hundred eighty feet." Actual: 188m × 156m ellipse (~617 ft × 512 ft), 48.5m tall (~159 ft). The prose's "six hundred feet across at least" and "a hundred sixty, hundred eighty feet" are accurate within error for a panicked teen estimating at distance. However, the prose calls it "round" (L63: "It was round. It was huge...") and later in the math passage treats it as a circle ("if that's the curve of a circle then the diameter"). The Colosseum is an ellipse, not a circle. Daniel's estimate of "six hundred feet" suggests he's catching the long axis, not the short (512 ft). **Architectural flag (non-blocking):** A teen eyeballing an ellipse from a valley floor might genuinely call it round, but the diameter estimate from a partial curve is shakier than the prose implies. This is within acceptable POV limits — Daniel is guessing — but "if that's the curve of a circle" slightly over-states his precision. The reveal still works architecturally. Suggest a minor hedge: "if that's the arc of something close to a circle" or simply note that a 17-year-old's estimate is by definition imprecise. Not a blocker.
- **Photo count**: Canon log says "He took a photo of the Colosseum" (and L55 in ch02 log says "Phone now holds 2 photos: the Colosseum + a selfie"). This chapter shows the Colosseum photo taken at L73. No selfie is taken in this chapter — the selfie must be taken in ch02 (canon log's L55). PASS — consistent.
- **Colosseum canon note**: Canon says "the intact, new, gleaming Colosseum on its near edge." The prose says the building "was clean, it was bright, the morning sun was just catching the top of it and the stone was so pale it was almost white." PASS — matches.

**Children chronology check**: Lucanus born ~108 AD, Ulpia ~118 AD. Ch01 is 98 AD. No child scenes appear. PASS.

**New canon facts introduced this chapter** (log for coordinator):
- Daniel's hardware store is named "Brentwood Hardware" (on the T-shirt logo). Canon log only says "a hardware store." Update canon log.
- T-shirt has "Brentwood Hardware logo cracked and faded to a ghost across the chest" + "small triangular hole worn through at the left shoulder seam." Canon log says "small hole at the collar" — discrepancy, update canon log to match prose.
- Phone at 98% battery at 6:14 AM. One photo taken (Colosseum). No calls connected. Maps app has cached data showing rivers/roads but cannot locate.
- Coworker/manager: Marcus (referenced as the man "who never replaced a flickering light over the fastener aisle"). Canon log already has this. PASS.

---

## 6. Voice
*(Narrator and secondary characters.)*

- **Daniel's voice**: dry / self-deprecating / specific? YES — consistent with V2 spec. The voice is a panicked teen with a dry undercurrent ("Such a small, ordinary, idiotic sound"; "I made a sound I'm not proud of"). Competent at math, faking calm, reaches for rationalization. Not a hero. PASS.
- **Class-marked secondary voices**: no named secondary characters speak more than implied sounds (the woman says something "low and quick" behind a cloth; the man says two words of an unknown word). No voiced secondary dialogue to check. PASS.
- **No muted mutes**: Pamphilus / crowd heckler / Naso not present — N/A.
- **Info-delivering monologue check**: no secondary character present long enough to monologue. PASS.
- **Child dialogue**: no children speak — the two barefoot kids "stopped dead and stared at my feet." N/A. PASS.
- **Daniel competence**: He gets things wrong (thinks he fainted, thinks it's a movie set, calls 911 twice knowing it won't work). He panics in private. He does not fake confidence in public — there is no public yet, just a terrified attempt to speak English at Latin speakers. The "I'm okay at staying calm if I have something to do with my hands or my feet" line is accurate self-knowledge presented without self-congratulation. PASS.

---

## 7. Verdict

**REVISE**

### Blocking issues (must fix before next use)

1. **Correctio violation** — L45: "...I know what machine-made cloth looks like and this was not it. It was thick and uneven and it hung wrong." The "this was not it. It was X" construction is the canonical banned form. Fix: "I know what machine-made cloth looks like. This was thick and uneven and it hung wrong." (Drop "this was not it" entirely.)

2. **"Photo made it a fact" tricolon — NOT FIXED in V2.** V2_CHAPTER_CHANGE_NOTES explicitly requires: "Cut the third clause or replace the three-beat close with a single concrete image." The V1 tricolon as flagged was "that did not help at all. It made it worse. The photo made it a fact." In this V2 draft, the third clause ("The photo made it a fact") has been removed. What remains is: "and I took the picture and the fake shutter clicked and I had it now, and that did not help at all. It made it worse." This is now a **two-beat close** ("that did not help at all. It made it worse.") which is still a rhythmic restatement. The change-notes ask for a single concrete image instead. Current state is better than V1 but still two declarative beats restating the same thing. Revise to one image or action: e.g., "and I had it now, in a glass rectangle in my hand, exactly the size of nothing." Consider whether this is a blocker or a revise; ruling it **blocking** per the explicit change-note instructions that the fix must move to a single concrete image.

3. **One-sentence paragraph rate at ~30%** — exceeds 15% cap. While many of the one-sentence paragraphs earn their place in the Colosseum reveal sequence, the chapter should be trimmed to approximately 19-23% (absorbing ~4-5 one-sentence paragraphs into adjacent text). Flag as **blocking** per PROSE_PATTERNS_TO_AVOID §2.2.

### Revise items (should fix)

1. **Borderline correctio at L47** — "Not Spanish. We get a lot of Spanish at the store and I can fake my way through a little and this was not it, not French from two years of it in school, not anything." The "Not Spanish." standalone sentence and "not it, not French, not anything" list-of-negatives runs close to the banned form. Rephrase to a positive construction: describe the sound's actual quality rather than what it wasn't.

2. **Borderline correctio at L39** — "She did not look annoyed, not the expression of someone spotting a trespasser on a set." Rephrase to drop the leading negation.

3. **"Thing" as vague placeholder** — three instances where a specific noun was available:
   - L13: "the sky was doing that thing where" → describe the condition directly.
   - L25: "That was the thing that made my chest go tight" → "That was what made my chest go tight" or more specific.
   - L53: "There was a thing painted on the wall" → "There was a word painted on the wall" (which the text subsequently clarifies was a word, so "thing" is technically wrong as well as vague).

4. **Polysyndeton count = 2** — trim the L45 anaphora ("they looked at my jeans and they looked at my boots and they looked at the shirt...") to avoid using the chapter's polysyndeton budget on the minor beat, saving it for the earned panic cascade at L69.

5. **"A count that had stopped being a count and become a wall" (L79)** — gnomic-adjacent close to an interior paragraph. Not a chapter-end button; acceptable at this level, but watch this rhythm in adjacent chapters.

6. **False-modesty rhythm at L77** — "I know that sounds like a strange thing to reach for... but it's true, it's the one thing I've always had." One occurrence, acceptable, but watch the "I know that sounds like X but..." preface across the book — it seeds the TIC V3 pattern.

### Notes for coordinator

- **Canon log update required**: The T-shirt in V2 prose is "Brentwood Hardware logo cracked and faded to a ghost across the chest, the collar stretched..., a small triangular hole worn through at the left shoulder seam." The canon log says "gray T-shirt with a small hole at the collar." Two discrepancies: (a) no brand name in canon; (b) hole location differs (collar vs. left shoulder seam). The prose is more specific and consistent with the V2 change note requiring "one specific identifying marker." Update `bible/08_canon_log.md` ch01 entry to match prose.

- **Future-vantage line confirmed removed**: The V2_CHAPTER_CHANGE_NOTES flagged line ("I want to be careful here, because later on people would ask me about this morning and I would lie...") is absent from this draft. Confirmed fixed.

- **Chapter scope vs. brief note**: The ch01 brief lists beats (the rope, the cell, phone death) that the prose correctly defers to ch02 and ch04. The chapter ends at the right moment — four spearmen approaching. No action needed; just note for any future brief-vs-prose mismatch checks.

- **Colosseum "round" vs. ellipse**: flagged above as non-blocking. The Colosseum is an ellipse; Daniel calls it "round." This is defensible POV (terrified teen at distance) but watch if any later chapter corrects this — if the Colosseum geometry is ever stated precisely in later chapters, this "round" reading should be revisited or left as a first-impression error Daniel never corrected because he never thought about it again.

- **Plant confirmed**: The Colosseum photo is taken. Canon log shows this photo exists through ch17+ (phone kept as a relic). Photo established correctly.

- **The chapter opening** ("The first thing I got wrong was thinking I'd fallen asleep on the job.") is a retrospective-entry per the style guide's "use sparingly" category. It works well — event-first, the frame doesn't assign future weight. Not a flagged issue.
