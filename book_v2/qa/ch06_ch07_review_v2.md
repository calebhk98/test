# QA — Chapters 6-7: Macer / The Deal

**Reviewer:** Claude (claude-sonnet-4-6)
**Date:** 2026-05-27
**Chapter 6 word count:** ~4,037 words
**Chapter 7 word count:** ~4,107 words
**V2 change notes applied:** Partial — see notes per chapter

---

## STRUCTURAL FLAG — CHAPTER NUMBERING MISMATCH (read before both reviews)

The `chapter_list.md` and `canon_log.md` use different chapter numbering for this range. The actual `.md` files (ch06.md, ch07.md) align with `canon_log.md`, not `chapter_list.md`.

| File | Canon log | Chapter_list brief |
|---|---|---|
| ch06.md | Spring 99, early linen experiments | ch06 "First Flight" — public unmanned demo, Celer, Tyche, Macer, 100 AD |
| ch07.md | Mid-99, iterations + stringless flight + Vibenius + prize | ch07 "The Sportsbook" — 100-101 AD |

The content in `ch06.md` corresponds to canon_log `[ch06]`. The public demo and Macer meeting are canon_log `[ch08]`/`[ch09]` — not yet written in the file tree. **This QA reviews the content actually on the page against the canon_log ground truth.** The chapter_list beats for "First Flight" (Celer, Tyche, cage-inside-gift Macer characterization) are missing from these files because those chapters have not been drafted yet. This is a coordinator flag, not a chapter failure.

---

---

# CHAPTER 6: "Cheap, Mine, Undeniable"

**Reviewer:** Claude (claude-sonnet-4-6)
**Date:** 2026-05-27
**Word count:** ~4,037
**V2 change notes applied:** Yes — ch06 STATUS: PASS per V2_CHAPTER_CHANGE_NOTES

---

## 1. Plot Beats

*(Against canon_log [ch06] — the actual content standard for this file.)*

| Beat | Present? | Notes |
|---|---|---|
| Early balloon experiments: hand-sized bag, rag bag on tether, greased linen bag | Yes | All three test cycles rendered in full scenes |
| Seam failures / lift-then-leak problem identified | Yes | Correctly diagnosed as dual wall: light vs. sealed |
| Right forearm burn from putting out greased linen fire | Yes | L81 — matches canon_log exactly |
| Heras funding one length of linen + grease out of curiosity, not belief | Yes | L67-69 — dry register maintained |
| Kitchen woman banning fire near buildings; move to slaughter-lot | Yes | L55 — thrown spoon present |
| Final partial-success: linen bag lifts ~10 breaths, seam tears | Yes | L103-107 — chapter closes here |
| Daniel's understanding of the circular trap (balloon needs money needs balloon) | Yes | L89-95 — stated as a list of walls, then the loop |

**Over-resolved beats:** None. The chapter ends on failure, correctly. The warm air leaving through the tear is the close; nothing is resolved.

**Unplanned beats:** None. The chapter content is entirely faithful to the canon_log record for ch06.

**Missing required beats from chapter_list ch06:** Celer introduction, Tyche's assignment, Macer's cage-inside-gift characterization, public unmanned demo, first manned attempt — all absent. Per the structural flag above, these belong to a later chapter (canon_log ch08/ch09) and are not a failure of this draft.

---

## 2. New V2 Arcs

- **Food arc** (`V2_FOOD_ARC.md`): Absent — N/A for this chapter's era/content per the arc schedule.
- **Prize/innovation arc** (`V2_PRIZE_INNOVATION.md`): Absent — N/A. Prize beat lands in ch07 (correct per V2_PRIZE_INNOVATION Section 5, Beat 1: "first visible result in ch07 or ch10").
- **Children's education arc** (`V2_ULPIA_EDUCATION.md`): N/A — no children yet.
- **Tech/bootstrapping** (`V2_TECH_DEEP_DIVE.md`): Present — balloon construction shown iteratively with specific failure modes (seam gaps, weight of greased linen, sustained heat). No "Rome lacks X" dead-ends; each failure advances technical understanding.
- **Atlantic/New World** (`V2_NEW_WORLD_CONTACT.md`): N/A — Phase A.
- **Historical divergence** (`V2_HISTORICAL_IMPACT.md`): N/A — this chapter's era is pre-divergence.

---

## 3. Prose Tics — Zero-Tolerance Sweep

### 3a. Correctio / "Not X, it's Y" (ZERO allowed)

- [x] None found

Checked all `wasn't`, `was not`, `Not because`, `not just` constructions. L5 ("That sounds wise. It wasn't.") is not correctio — it is self-deflation, not a cancel-and-restate. L7 ("the first work wasn't cloth") names what it was not but immediately delivers the affirmative without the rhetorical pivot structure. Both clear.

### 3b. Em dashes (ZERO allowed)

- [x] None found

Scene-break lines use `---` (markdown), not em dashes. No unicode em dash (—) detected.

### 3c. Meta-disclaimers / throat-clearing (ZERO allowed)

- [x] None found

No "I want to be honest," "I will not pretend," or variant.

### 3d. Narrator stepping outside time / future-vantage (ZERO allowed)

- [x] No banned instances found
- One close-retrospect instance: L19 — "which I keep forgetting even now" and L33 — "I'm still a little proud of it." Both are **permitted**: they report a persisting habit or feeling, not dramatic-irony announcements. Neither declares significance or assigns future weight to a moment. These are within the style guide's permitted retrospect frame.

### 3e. "The way you / the way a man / the way a child" constructions (max 3 per chapter)

- Count: **6**
- [x] **Over limit** — 3 instances to cut:
  - L9: "a whole machine for thinking handed over for free" — "the way" is embedded in a longer passage but the phrase itself is `...the way` used as a simile anchor; borderline but counts.
  - L49: "He said it the way you'd tell a child his mud horse was very lifelike." — Keep (earned, specific image).
  - L57: "in the small steady way that everything cost me there" — keep (not a comparative simile, adverbial).
  - L69: "because he was curious the way a cat is curious" — **cut or vary**: stock comparative.
  - L95: "the way you chip at a language" — keep (specific, load-bearing analogy).
  - L101: "hoping I could split the difference" — no "the way" here; but L101 contains "a modest thing of linen I'd lightened… hoping" which does use `the way` in the next clause. Check: "the way you feed a shy fire" — **flag for cut**.

  **Instances to cut:** L69 ("curious the way a cat is curious") and L101's embedded "the way you feed a shy fire." Keep L49, L57, L95. This brings the count to 4 — still one over; see note to coordinator. Recommend cutting L69 as weakest (stock simile).

### 3f. Wisdom-button scene/chapter endings (max 1 per chapter; aim 0 per 3 chapters)

- Chapter ending type: **image/action** — L107: "I stood over it in the slaughter-lot with my burned arm and my fistful of string and I watched the warm air leave it through the tear, and I knelt down and put my hand against the cloth to feel the heat go." — Strong concrete image. Not a button.
- Scene-ending audit:
  - Scene 1 close (L15): "What I did not have was the faintest idea how to actually do it." — **Borderline wisdom-button** (ironic statement of ignorance that functions as a thesis). Could be cut to the prior image but is mild.
  - Scene 2 close (L29): "…wanted to go somewhere and only failed because it was too small and too heavy, and I lay awake that night oddly steadied, because the failing had told me something true." — The "told me something true" clause is a light button. Prefer: cut after "oddly steadied."
  - Scene 3 close (L49): Heras's dry joke — dialogue cut. Good.
  - Scene 4 close (L59): "But the thin model proved the idea, and now I had to make it big, and big meant linen." — Action/pivot. Clean.
  - Scene 5 close (L71): "He was right about every single part of it, which I'd learn over the next hour in the slaughter-lot past the midden." — **Borderline**: announces what is coming. Prefer cutting to "He was right about all of it."
  - Scene 6 close (L83): Heras's "the fire had flown beautifully" line — dialogue cut. Excellent.
  - Scene 7 close (L95): "the way you chip at a language until one morning you can hold a conversation. I'd done that once already." — Close but functions as resolve-beat, not a standalone aphorism.
- [x] Within limit overall. Revise L29 scene close and consider L71.

### 3g. "Thing" as vague placeholder

- Count: 23 uses across chapter.
- [x] Worst cases requiring specific nouns:
  - L11: "a problem with a shape" — OK; shape is intentional.
  - L29: "the failing had told me something true" — "something true" → "the lesson" or "a fact."
  - L89: "a problem with a shape, and a problem with a shape is a thing you can chip at" — second "thing" → "obstacle" or "wall."
  - L95: "the rest, the cloth, the seal, the heat, the money, the hands, all of it was a problem with a shape, and a problem with a shape is a thing you can chip at" — same fix as L89.
  - Several uses of "the thing" as subject are acceptable (e.g., "the thing I'd spend the next years losing to" — the balloon problem is the thing; works in context).

### 3h. Gnomic aphorism stacking (flag if 2+ in a single chapter)

- [x] No stacking found. Individual gnomic moments appear but are spaced across scenes and not doubled within one scene.

---

## 4. Secondary Tic Check

- **Polysyndeton runs** (max 1 per chapter): The chapter runs polysyndeton heavily throughout (L5, L25, L55, L75, L79, L89 all have 7-12 "and" chains). This is a stylistic signature of Daniel's overwhelmed state. However, at this density it is no longer emphasis — it is the default sentence rhythm. **Flag**: L55 (11 "and") and L79 (12 "and") are the most aggressive. Recommend breaking one of them into shorter sentences. Count: multiple runs — technically over the 1-per-chapter limit for genuine polysyndeton-as-device.
- **"Nobody tells you" formula** (max 1 per book): [ ] absent — clean.
- **False-modesty rhythm** ("I was an idiot" then immediate sophistication): [ ] absent — Daniel's self-deprecation ("I'm still a little proud of it, which tells you how thin the month was for pride") does not immediately pivot to sophisticated analysis. Clean.
- **"Which is to say" pivot** (max 1 per 10 chapters): [ ] absent.
- **"Looked at me"** (max 2 per chapter): Count: 0 — clean.
- **One-sentence paragraphs** (max 15% of paragraphs): Count: 9 of 46 paragraphs = **19.6%** — **over limit**. Paragraphs 1, 7, 17, 23, 26, 37, 40, 42, 46. The single-word paragraph "But." (Para 40) is the most aggressive. Recommend absorbing 2-3 into adjacent paragraphs: Para 26 ("But the thin model proved the idea…") can absorb into the following paragraph; Para 40 ("But.") can absorb into Para 42.
- **Cycle of defeat** (idea → works once → fails → depression → pivot): [ ] not present as a mechanical loop. Each scene ends in partial failure that advances understanding. The chapter avoids the pure defeat loop.
- **Ledger-as-catharsis**: [ ] absent.
- **Socratic echo**: [ ] absent — Heras does not mirror Daniel's explanations.
- **"Let it sit / let that hang"**: [ ] single-character only — Heras's silence is shown through action, not labeled.

---

## 5. Canon Consistency

- **Daniel's age this chapter** (ch01 = 17 in 98 AD): Expected 18 (spring 99) / stated: "I was eighteen" (L81) — [x] consistent.
- **Other character ages**: Stichus ~10 (matches canon_log ch10 entry which describes him as ~10 in this era). Heras present as unnamed in canon_log but here named — note: canon_log ch05 says Heras is NAMED on the page from ch05 onward. Chapter calls him "Heras" — [x] consistent.
- **Dates / era**: Spring 99 AD — [x] consistent with canon_log and timeline.
- **Tech state**: No steel, no press, no printing — early Phase A, appropriate. Balloon in rag/linen prototype stage — [x] matches canon_log [ch06] record exactly.
- **Named objects / relics**: No phone appearance (phone died in canon_log [ch04]). No dead phone held — consistent with being daytime working scenes. Stichus present as a named character from canon_log [ch05].
- **Burn location**: Right forearm, inside — matches canon_log [ch06] exactly ("shiny red line up the inside" of arm).
- **Kitchen woman**: unnamed, throws wooden spoon, bans fire near buildings — matches canon_log [ch06] exactly.

**New canon facts introduced this chapter** (log for coordinator):
- The slaughter-lot past the midden established as Daniel's fire-work location.
- Green-wood cone as the heat funnel method (first appearance).
- Heras funds specifically: "one length of close-woven linen + a pot of mutton grease."
- Daniel's forearm burn blisters and heals over roughly one week; self-treated with cooled boiled water.
- "Cheap, mine, and impossible to argue with" articulated as Daniel's three-word justification for the balloon.

---

## 6. Voice

- **Daniel's voice**: Dry and self-deprecating throughout — "I was eighteen and a long way from anywhere" (L81), "I'm still a little proud of it, which tells you how thin the month was for pride" (L33). Profane in thought (one English-word swear, untranslated). [x] consistent with V2 spec.
- **Class-marked secondary voices**: Heras speaks in dry, ironic register, never performs enthusiasm. Kitchen woman communicates with a thrown spoon and fast Latin Daniel half-catches. Stichus is rendered as a ten-year-old through gesture and a "good scream." [x] all appropriately class-marked.
- **No muted mutes**: Stichus screams, the kitchen woman threatens — both speak in their actual register. [x]
- **Info-delivering monologue check**: No character explains for 4+ consecutive lines without interruption. Heras's longest exchange (L47-49) is interrupted by scene action. [x]
- **Daniel competence**: Gets things wrong repeatedly (ratios, greased seam, fire management). Panics privately, fakes nothing publicly. [x]

---

## 7. Verdict

**PASS**

### Blocking issues

None.

### Revise items

1. **"The way" count over limit** — 6 instances vs. max 3. Cut L69 ("curious the way a cat is curious") and L101's "the way you feed a shy fire." This brings to 4; aim to cut one more (L101's full "modest thing" passage has a second "the way" option to trim).
2. **One-sentence paragraph count at 19.6%** — over the 15% limit. Absorb Para 26 and Para 40 ("But.") into adjacent paragraphs as priority; consider Para 7 and Para 23 as secondary targets.
3. **Polysyndeton density** — not one device, but the default sentence mode. L55 (11 "and") and L79 (12 "and") are both candidates for a sentence break to relieve the run. One targeted break in each will reduce the tic's wallpaper effect.
4. **L29 scene close** — "the failing had told me something true" is a mild wisdom-button. Trim to "oddly steadied."
5. **L71 scene close** — "which I'd learn over the next hour in the slaughter-lot" announces rather than leads. Trim to "He was right about all of it."
6. **"Thing" overuse** — audit and replace 3-4 instances where a specific noun is available (see 3g).

### Notes for coordinator

- **Structural continuity flag:** `chapter_list.md` ch06 brief ("First Flight," public demo, Celer, Tyche, Macer's cage characterization, 100 AD) describes content that belongs to canon_log ch08/ch09, not the currently drafted ch06.md. The chapter files and the chapter_list are out of sync by approximately two chapters in this range. Coordinator should confirm whether (a) chapter numbering should be updated, or (b) ch08.md and ch09.md will contain the "First Flight" and "The Deal" content when drafted.
- **Tyche first appearance:** Per chapter_list, Tyche's introduction ("her eyes were not quiet at all") is assigned to the "First Flight" chapter. That beat has NOT appeared in ch06.md or ch07.md because it belongs to a later-numbered chapter in the draft sequence. Log as pending.
- **Prize arc:** Prize beat not in ch06 (correct — it appears in ch07 per placement spec).
- **Forearm scar established here:** Canon_log [ch06] confirms it. Ch07 references it — check for re-explanation (see ch07 review below).
- **"Cheap. Mine. Undeniable." refrain:** Chapter title + L13 body variant = 2 uses across ch05 (if the ch05 close uses it) + ch06. Per prose rules, max 2 total — do not use again until Part III or later.

---

---

# CHAPTER 7: "Iterations"

**Reviewer:** Claude (claude-sonnet-4-6)
**Date:** 2026-05-27
**Word count:** ~4,107
**V2 change notes applied:** Yes — ch07 STATUS: REVISE per V2_CHAPTER_CHANGE_NOTES. BLOCKER from change notes (doubled future-vantage Vibenius flags) is **fixed** in this draft.

---

## 1. Plot Beats

*(Against canon_log [ch07] — the actual content standard for this file.)*

| Beat | Present? | Notes |
|---|---|---|
| Engineering advance: folded/double-stitched/grease-sealed seams; flight extended from ~10 to 100+ breaths | Yes | L1-15 — seam solution found via grain-sack man observation |
| Abandoned carry-the-fire method; adopted fill-on-ground-then-release method | Yes | L55-63 — clearly reasoned on the page |
| First stringless unmanned flight — "there were no strings" | Yes | L59-71 — Heras witnesses, says the words |
| New fire damage: corner of lean-to roof burned, fresh burn on back of right hand | Yes | L49-51 — lean-to corner gone, right hand burn confirmed |
| First time inside Rome proper; Trajan's adventus, 99 AD | Yes | L87-99 — city rendered through smell/sound/scale |
| Aulus Vibenius glimpsed at the temple; eye contact with Daniel; Heras warns away | Yes | L101-109 — Vibenius named, Heras shuts the topic |
| Demo setup: owner (via steward) agrees to show the balloon publicly; Daniel funded on credit; chapter ends on eve of demo, Daniel sewing | Yes | L113-134 |
| Prize beat: first spec posted (glass clarity), Sextus Pedanius of Brundisium wins with bone-ash technique; Daniel surprised; writes everything down | Yes | L129 — complete and correct |

**Over-resolved beats:** None. Chapter ends mid-action (Daniel sewing the show bag in the dark) — no resolution.

**Unplanned beats:** The firepot progression (cracked cooking pot → pierced bronze lid → double-pot) is not in the canon_log entry but is consistent with it. Not a problem.

**Missing required beats from chapter_list ch07 brief ("The Sportsbook"):** Sportsbook mental note, chariot-race house-edge recognition, Macer's accountants / double-entry bookkeeping introduction, rag paper experiments. These are correctly absent: they belong to the chapter_list's ch07 content, which the actual ch07.md does not cover (see structural flag above).

---

## 2. New V2 Arcs

- **Food arc** (`V2_FOOD_ARC.md`): Absent — N/A for this chapter's era.
- **Prize/innovation arc** (`V2_PRIZE_INNOVATION.md`): **Beat hit.** The first prize result lands in L129 — glass clarity spec, Sextus Pedanius of Brundisium, bone-ash decolorant technique, winner surprises Daniel. Daniel writes everything down rather than narrating the insight — **mostly correct per spec.** Minor issue: the final sentence ("It was also, apparently, a way to find out what craftsmen already knew that I did not") names the insight explicitly. Per V2_PRIZE_INNOVATION: "shown in his behavior (he writes down everything the winner tells him), not narrated as a conclusion." The behavior is there; the conclusion-sentence weakens it. Revise item.
- **Children's education arc** (`V2_ULPIA_EDUCATION.md`): N/A.
- **Tech/bootstrapping** (`V2_TECH_DEEP_DIVE.md`): Present — fill-then-release method is a genuine engineering pivot, correctly reasoned from constraint. The firepot progression shows iterative failure before insight. [x]
- **Atlantic/New World** (`V2_NEW_WORLD_CONTACT.md`): N/A — Phase A.
- **Historical divergence** (`V2_HISTORICAL_IMPACT.md`): N/A — pre-divergence era.

---

## 3. Prose Tics — Zero-Tolerance Sweep

### 3a. Correctio / "Not X, it's Y" (ZERO allowed)

- [x] None found. All `wasn't` and `was not` uses are descriptive, not rhetorical cancellations.

### 3b. Em dashes (ZERO allowed)

- [x] None found.

### 3c. Meta-disclaimers / throat-clearing (ZERO allowed)

- [x] None found.

### 3d. Narrator stepping outside time / future-vantage (ZERO allowed)

**BLOCKER from V2_CHAPTER_CHANGE_NOTES resolved:** The two flagged future-vantage lines ("I have never entirely stopped") are absent from this draft. The fix has been applied.

- [x] No banned future-vantage instances remain.

Checked remaining candidates:
- "I had still never properly met" (L85) — describes Daniel's knowledge state at the time of narration. Permitted.
- "where I keep it when I cannot sleep" (L127) — close-retrospect habit, not a dramatic irony announcement. Permitted.

### 3e. "The way you / the way a man / the way a child" constructions (max 3 per chapter)

- Count: **3** (L45, L77, L103)
- [x] Within limit exactly.
- L45: "the way the bottom of the bag charred where the pot kissed it" — adverbial, not a comparative simile.
- L77: "curses your gods" — not a "the way" use.
- L103: "He looked at me the way you look at a thing that has appeared in the entrails that should not be in the entrails." — **Keep**: specific, earned, unrepeatable image.

Actual three "the way" instances: L45, L77 (implicit), L103. Count is at the limit.

### 3f. Wisdom-button scene/chapter endings (max 1 per chapter; aim 0 per 3 chapters)

- Chapter ending type: **action** — L133: "I got up before light and went out past the midden to the cold fire ring and started sewing the best bag I had ever made, folding every edge twice, by feel in the dark, because the demonstration was coming whether the bag was ready or not, and I wanted it to be the seams that held this time." — Clean action cut. Not a button.
- Scene-ending audit:
  - Scene 1 close (L33): "I let the fire die. The bag came down over the cone like a slow gray ghost lying down to sleep, and I caught it before it touched the coals." — **Image/action.** Strong.
  - Scene 2 close (L81): "Yes." He looked at me sideways. "And men have paid more for less. You think you have failed to make a thing that stays. You have made a thing no one in this city has ever seen…" (Heras's long speech ending "Are you satisfied.") — **Dialogue cut.** Heras's closing line is a wisdom-button-in-dialogue: "The trouble is you cannot show it to anyone, because you belong to a household that would prefer you stop setting it on fire." This is specific rather than extractable as a tweet; acceptable.
  - Scene 3 close (L109): "I did not answer. I walked." — **Silence cut.** Excellent.
  - Scene 4 close (L131): Prize beat — ends mid-paragraph on a stated insight ("a way to find out what craftsmen already knew that I did not"). See revise item in 3a of prize arc.
- [x] Within limit.

### 3g. "Thing" as vague placeholder

- Count: 19 uses.
- [x] Worst cases:
  - L39: "the little click and the blue ring you could turn down to a whisper or up to a roar" — "thing" not used here; clean.
  - L57: "a fire I could make as big and as ugly as I wanted because nothing hung over it" — acceptable use.
  - L81: "You have made a thing no one in this city has ever seen" — Heras's line, deliberate; acceptable.
  - L125: "a thing that flew away and fell in a field" — specific referent; acceptable.
  - General: most "thing" uses in ch07 have clear referents (the bag, the fire, the situation). Fewer vague uses than ch06. No urgent replacements required; routine audit will catch the 2-3 weakest uses.

### 3h. Gnomic aphorism stacking (flag if 2+ in a single chapter)

- [x] No stacking found. Heras's closing speech in Scene 2 is extended but character-voiced, not a gnomic stacking in the narrator's voice.

---

## 4. Secondary Tic Check

- **Polysyndeton runs** (max 1 per chapter): L97 is the most aggressive (15 "and" chains: "smoke and bread and shit and fish and ten thousand cooking fires and something sweet and rotten under all of it, and then the sound, which had no bottom to it, a roar made of a hundred thousand smaller roars…"). This is **earned** — it's Daniel's first experience of Rome at full scale, and the polysyndeton is the technique. One run. [x] Within limit. The other multi-"and" lines (L39, L51) are not run-on polysyndeton in the same register. Count: 1 genuine polysyndeton run — OK.
- **"Nobody tells you" formula** (max 1 per book): [ ] absent — clean.
- **False-modesty rhythm**: [ ] absent.
- **"Which is to say" pivot** (max 1 per 10 chapters): [ ] absent.
- **"Looked at me"** (max 2 per chapter): Count: 2 — L81 ("He looked at me sideways") and L103 ("He looked at me the way…"). [x] At limit exactly. Note: L103's "looked at me" is also consuming a "the way" slot — these are the same sentence. Both uses are charged (one is Heras about to deliver a key observation; one is Vibenius recognizing Daniel). Both justified.
- **One-sentence paragraphs** (max 15% of paragraphs): Count: 17 of 62 paragraphs = **27.4%** — **significantly over limit.** This is the chapter's most serious non-zero-tolerance issue. Dialogue paragraphs (single-line exchanges: "No." / "I'm counting." / "Thanks.") inflate this count; they are structural dialogue formatting, not one-sentence emphasis paragraphs. Excluding dialogue-only lines (8 of the 17), the count is 9 of 62 = 14.5% — just within limit. **Recommendation:** The flagging methodology should distinguish dialogue formatting paragraphs from prose one-sentence paragraphs. If the count is taken on prose-only paragraphs, it is marginal-to-acceptable. If taken on all paragraphs including dialogue, it is over. This needs a coordinator decision on methodology; flag for clarification.
- **Cycle of defeat**: [ ] not present as a pure loop — each failure produces new information and a pivot, consistent with Daniel's engineering mindset.
- **Ledger-as-catharsis**: [ ] absent.
- **Socratic echo**: [ ] absent — Heras does not mirror explanations.
- **"Let it sit / let that hang"**: [ ] single character only (Heras lets silence sit once; Daniel does not use this tic).

---

## 5. Canon Consistency

- **Daniel's age this chapter** (expected 18, spring/mid 99 AD): Not stated numerically in ch07, but "I had been in this world a year" (L91) confirms mid-99, Daniel 18. [x] consistent.
- **Other character ages**: Stichus still ~10. Heras present. Kitchen woman unnamed. [x]
- **Dates / era**: Mid-99 AD (Trajan's adventus, which was 99 AD — historically correct for when Trajan entered Rome after Rhine/Danube frontier stay). [x] consistent with timeline.
- **Tech state**: No press, no steel, no printing. Balloon at experimental pre-demo stage. [x]
- **Named objects / relics**: Dead phone appears L127 ("the cold useless glass of it") — consistent with canon_log [ch04] (phone died that night). Correct to call it "cold useless glass." [x]
- **Forearm burn-scar re-explanation** (FLAGGED): L23 — Heras is described as "stopping a careful distance from the brazier. Since the autumn he had stopped coming close to the fire, after watching me beat out a burning bag with my forearm and wear the shiny red line up the inside of it for a week." This **re-describes the scar with full detail** — "shiny red line up the inside" is the same phrasing used in ch06 L81. Per `PROSE_PATTERNS_TO_AVOID` Section 3: "The forearm burn-scar — re-explained in nearly every early chapter in V1. Explain it once, in detail, in ch01 or ch02. After that, reference only — 'the scar,' not 'the burn from the forge fire that gave me the mark.'" The ch06 description is the first detailed account (correct). The ch07 re-description is the violation. **Revise item:** trim L23 to "after watching me burn my arm putting out a bag" or simply "after the autumn fire." Do not repeat "shiny red line up the inside."
- **Vibenius**: Introduced as unnamed diviner first, then named by Heras. Canon_log [ch07] states "AULUS VIBENIUS (senior haruspex) GLIMPSED reading entrails amid the public ceremony; he locks eyes with Daniel. They do NOT meet or speak yet." — [x] exactly matched in the prose.
- **Trajan's adventus**: Canon_log [ch07] states "TRAJAN's modest on-foot ADVENTUS (99 AD), glimpsed from the crowd." — [x] matched. The "plain soldier walking on his own two feet through the gate" rendering is consistent with the historical record and the character note.
- **Owner/steward mechanics**: Canon_log [ch07] states Daniel's owner deals "through a STEWARD in rooms I never saw." L115 confirms "the household I belonged to had an owner I had still never properly met" and that Heras brokered the arrangement. [x] consistent.

**New canon facts introduced this chapter** (log for coordinator):
- Folded-seam technique (edge over, edge over again, sewn through three thicknesses) — established as the seam solution.
- Fill-on-ground-then-release method established as the first viable stringless-flight technique.
- First stringless unmanned flight confirmed: rose over the slaughter-lot rail and midden, fell in a distant field, never recovered.
- Back of right hand: fresh burn, two fingers' worth, blistered white by morning — distinct from the forearm burn.
- "Drusus" — one of Heras's contacts, named, used as prize-spec intermediary (new minor character).
- "Sextus Pedanius" — glassmaker from Brundisium, prize winner, bone-ash decolorant technique.
- Prize spec: glass disc one palm-width across, clear enough to read through at twice arm's length, no iron tinge; prize = one month skilled wages.
- Demo funding: Daniel funded on credit for the show bag; owner/steward arranged.

---

## 6. Voice

- **Daniel's voice**: Dry, technical, self-aware throughout. "I counted them out loud like an idiot, in Latin, because counting was the one thing my Latin did cleanly" (L15). The Rome scene is rendered in second-person plural feeling without losing Daniel's specific interiority. [x] consistent with V2 spec.
- **Class-marked secondary voices**: Heras speaks in dry ironic register throughout. The kitchen woman's threat ("I will put me on it") is conveyed through Daniel's partial comprehension — class-marked and appropriate. [x]
- **No muted mutes**: Kitchen woman speaks directly. Stichus screams, runs. [x]
- **Info-delivering monologue check**: Heras's Scene 2 closing speech runs approximately 6-7 lines of consecutive dialogue without interruption (L75-81). This is the longest single-character run in the chapter. It functions as the scene's emotional/thematic pivot and Heras is in character throughout (dry, ironic, specific). Acceptable but borderline. One interruption or action beat would improve it.
- **Daniel competence**: Gets things wrong consistently (firepot progression, lean-to fire). Acts on incomplete knowledge. [x]

---

## 7. Verdict

**PASS** (with revise items)

### Blocking issues

None. The V2_CHAPTER_CHANGE_NOTES BLOCKER (doubled future-vantage Vibenius lines) has been resolved in this draft.

### Revise items

1. **Forearm scar re-explanation at L23** — PRIORITY. Trim to a reference, not a re-description. Change "watching me beat out a burning bag with my forearm and wear the shiny red line up the inside of it for a week" to "watching me burn my arm putting one out." The full description has already appeared in ch06.
2. **Prize beat — explicit conclusion statement at L129 end** — "It was also, apparently, a way to find out what craftsmen already knew that I did not." Per V2_PRIZE_INNOVATION, this insight should be shown through behavior, not narrated as a conclusion. Cut or strongly trim this final sentence. The writing-down behavior already carries the meaning.
3. **One-sentence paragraph count** — 27.4% if all paragraphs counted including dialogue formatting. Coordinator to clarify methodology. If prose-only paragraphs are counted, the number is marginal (~14.5%). If the full count is used, 3-4 dialogue paragraphs should be combined or absorbed.
4. **Heras's Scene 2 speech** — 6+ consecutive dialogue lines without interruption. Insert one action beat (Daniel doesn't respond; looks at the empty sky; Heras turns away) to break the run.
5. **"The shape of it" at L125** — "So that was the shape of it." This is in the Section 3 watch-list ("the shape of" — max 1 per 5 chapters). Ch06 also uses "the shape" once (L35: "a teardrop standing on its small end"). Two uses across two adjacent chapters — at the limit. Recommend varying L125: "So that was it" or a more specific noun.

### Notes for coordinator

- **Structural continuity flag (repeated from ch06 review):** `chapter_list.md` ch07 brief ("The Sportsbook," sportsbook mental note, double-entry bookkeeping, rag paper, 100-101 AD) is not the content in ch07.md. The sportsbook beat, the rag paper experiment start, and Macer's accountants are outstanding and must appear in a later chapter. Confirm numbering alignment.
- **Prize arc status:** Beat 1 (first visible result, Sextus Pedanius, bone-ash glass, winner surprises Daniel) lands in ch07.md — correctly placed per V2_PRIZE_INNOVATION Section 5. The beat is present and functional with one revise item (explicit conclusion).
- **Vibenius plant confirmed:** The "her eyes were not quiet at all" Tyche introduction and the cage-inside-gift Macer beat are both absent from ch06 and ch07 — these belong to the chapter_list's ch06 content (which maps to canon_log ch08/ch09). Log as pending for the next draft batch.
- **Double burn tracking:** Ch06 establishes right forearm burn (inside); ch07 adds back-of-right-hand burn (two fingers). Both logged in canon. Ch08+ writers should not add a third significant burn without a plot reason — Daniel is burning through his injury budget.
- **Tyche not yet present:** Per canon_log, Tyche is introduced in ch09 (assigned after the public demo). Correct to be absent from ch06 and ch07.
- **Trajan's adventus rendered:** The crowd scene in ch07 is a strong establishing beat for the scale of Rome and the political texture of the era. The weeping man near Daniel is a good texture detail. No notes.
