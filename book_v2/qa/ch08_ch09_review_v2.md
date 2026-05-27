# QA — Chapters 8-9
**Reviewer:** claude-sonnet-4-6 (agent)
**Date:** 2026-05-27
**Word count:** ch08 ≈ 3,387 words / ch09 ≈ 3,224 words (≈ 6,611 total)
**V2 change notes applied:** partial — see Section 3 and Section 7

---

## STRUCTURAL NOTE (read first)

There is a chapter-numbering discrepancy that must be resolved before these chapters are used in production. The prose files `ch08.md` and `ch09.md` contain:

- **ch08.md** ("Fire That Flies"): the public balloon demonstration in the Subura lot, ~mid/late 99 AD, Daniel ~18. This matches `bible/08_canon_log.md` entry `[ch08]`.
- **ch09.md** ("Macer"): Daniel meeting Titus Flavius Macer, same day, ~mid/late 99 AD. This matches canon log entry `[ch09]`.

However, `outline/chapter_list.md` assigns:
- **ch08** = "The Frontier (Part I)" — 101 AD, First Dacian War, Apollodorus introduction
- **ch09** = "The Frontier (Part II)" — 101-102 AD, Sabinus's death, flight vow

The prose chapters labeled ch08 and ch09 correspond to what `chapter_list.md` calls **ch06** ("First Flight": the public demo + Tyche's assignment) and a chapter that may not exist in the current outline (the Macer negotiation scene, which is covered as backstory in ch06's "Tyche's assignment" beat and in ch07 framing).

**Flag for coordinator:** The prose files carry canon-log numbering (pre-renumbering). The chapter_list has renumbered these events. QA is conducted against the prose as written; beats are checked against the canon_log's established facts for these events rather than against the chapter_list's ch08/ch09 entries (which describe the Dacian War frontier chapters, not yet drafted).

**The remainder of this review treats the prose content on its own terms and flags the discrepancy throughout.**

---

## 1. Plot Beats

*(Checked against canon_log entries [ch08] and [ch09], which match the actual prose content.)*

### ch08 ("Fire That Flies") — beats from canon_log [ch08]

| Beat | Present? | Notes |
|---|---|---|
| Public demo in Subura lot during festival | yes | Opening. Specific location (corner lot, Subura), festival crowd, butcher block, fountain. |
| Show bag: ~11 ft, pale gray greased linen, green ash hoop, no string | yes | L5: exact dimensions, construction detail, smell of cold lamp. |
| Helpers: Stichus (coal-pot) and Davus (keeps Daniel from bolting) | yes | Both named and characterized at L9. |
| Flight: ~60-70 ft, drifted, clipped five-story roof, tore washing, smoldering street flame | yes | L41-L45: specific sequence, height, minor injuries (scorched arm, tunic burned). No deaths. |
| Crowd fractured: wonder/fear/"witch" | yes | L37-L39: delight + fear + "witch" word named and rising. Not uniform awe. |
| Vibenius present, pronounces deliberate ambiguous omen | yes | L55-L63: both doors left open, his verdict as craft explained. |
| Steward summons Daniel to master immediately after | yes | L75-L79: ending beat, Daniel rising from the ash. |
| Celer in crowd with military perspective | no | Chapter_list ch06 specifies Celer introduced at this launch. Absent from prose ch08. However, this may be an outline beat not yet assigned to the canon-log version of the chapter. Flag for coordinator. |
| Manned attempt beginning | no | Prose ends at the summons; no manned attempt in this chapter. Per ch06 brief, first manned attempt follows the demo. Absent here — may be intended for a subsequent scene. |

Over-resolved beats: None. Vibenius's omen is deliberately unresolved. The crowd's verdict is earned and uncertain.

Unplanned beats: None detected beyond the brief chapter.

---

### ch09 ("Macer") — beats from canon_log [ch09]

| Beat | Present? | Notes |
|---|---|---|
| Macer met and named (same day as demo) | yes | L47: steward formally names him. |
| Macer's physical description: big shoulders going soft, gray cropped, broken-veined face, plain tunic no stripe, gold ring he turns | yes | L13: all details present. Ring-turning tic established. |
| Macer calls Daniel "Thulean" | yes | L51: "Here is where we are, Thulean." First use noted. |
| The Deal: cloth, two slaves (won't run), walled yard at timber wharf, peculium | yes | L67-L77: tally of four terms, finger-by-finger, specific. |
| Freedom refused: not Macer's to give, citizens made by men higher | yes | L107: verbatim logic. |
| Daniel status unchanged: slave with peculium, finer cage | yes | L99: "a cage so well made it looked from the inside like a workshop." |
| Balloon named by Macer, claimed as his possession | yes | L95: "He used the word like he owned it, which he did." |
| Tyche introduced: ~14, plain tunic, short uneven hair, quick city Latin, watchful, "does not run" | yes | L119-L129: all details present. |
| Workshop relocating to walled yard off timber wharf | partial | Stated as part of the deal (L73: "a yard I hold off the timber wharf") but not shown as a relocation scene — this is backstory for the next chapter. Appropriate — no flag. |
| Heras present as witness/broker | yes | L9, L39, L45: three scenes. |

Over-resolved beats: None.

Unplanned beats: The wooden disc as Macer's physical tic (turning/inspecting) is an addition not in the canon log. It functions as a parallel to his ring-turning and is character-consistent. Log it for the coordinator.

---

## 2. New V2 Arcs

*(Checked against applicable V2 arc files. Both chapters are ~99 AD, Phase A.)*

- **Food arc** (`V2_FOOD_ARC.md`): **Absent / N/A for ch08.** For ch09: one brief food beat present — bread and watered wine given to Daniel by Tyche in the corridor (L123: "the best thing I had tasted in a year"). No garum, no omelette, no food experiment. Per `V2_FOOD_ARC.md`, Section 7, the Phase A food note for these chapters is limited to army food texture or a brief note that workshop food makes Daniel appreciate later cooking; it doesn't require a garum or omelette beat in the demo/Macer chapters. **No flag.** Era-correct: bread and watered wine are unambiguously Roman and Period A-appropriate. No New World crops. **Pass.**

- **Prize/innovation arc** (`V2_PRIZE_INNOVATION.md`): **N/A.** These chapters predate the contest and prize structure entirely.

- **Children's education arc**: **N/A.** Era is ~99 AD; Lucanus is not born until ~110 AD. No child scenes present. **Pass** — correct absence.

- **Tech/bootstrapping** (`V2_TECH_DEEP_DIVE.md`): **N/A** for the demo/Macer chapters. The balloon technology is shown practically (fill method, heat loss problem, eleven-foot dimensions, seam technique). Daniel's explanation of the failure to Macer (L87: "It came down because I cannot keep the heat in it. I know why.") is appropriately compressed — no lecture.

- **Atlantic/New World** (`V2_NEW_WORLD_CONTACT.md`): **N/A.** Phase A.

- **Historical divergence** (`V2_HISTORICAL_IMPACT.md`): **N/A.** Per divergence ledger in `bible/03_timeline.md`, divergence ledger is empty through ~ch35. These ~99 AD chapters are pre-divergence. Vibenius's ambiguous omen is historically plausible; no divergence introduced. **Pass.**

---

## 3. Prose Tics — Zero-Tolerance Sweep

### 3a. Correctio / "Not X, it's Y" (ZERO allowed)

**ch08:**
- [x] Found: L49 — "Not to comfort me. To hold me where I was" — this is the banned "Not X. Y." two-sentence pivot. First sentence defines the act by what it is not; second supplies the true thing.
- [ ] Candidate L7: "Not a good square." — this is a brief qualifying clause, not a correctio pivot; the following sentence explains the location rather than supplying the "true" thing. Borderline but likely fine.
- [ ] Candidate L77: "Not the steward, not Heras, not a messenger with a tablet at the workshop, none of the ways the household had spoken to me for a year through every mouth but the one. The master." — This is a rhetorical enumeration of negatives building to a positive. Per `PROSE_PATTERNS_TO_AVOID.md`, the banned form is "Not X. Y." as a rhetorical pivot. This enumeration functions differently (listing specifics before a revelation) and is not the banned form. **Permitted.**

**ch09:**
- [ ] None found. All negation patterns in ch09 ("not running," "not to look at the furniture," "It is not mine to give") are functional negation in dialogue or description, not the banned pivot.

**Ruling:** ch08 has one correctio violation (L49). Fix required before acceptance.

---

### 3b. Em dashes (ZERO allowed)

**ch08:** None found.
**ch09:** None found.

- [x] None found in either chapter. Pass.

---

### 3c. Meta-disclaimers / throat-clearing (ZERO allowed)

**ch08:**
- [x] Found: L5 — "I want that on the record, because everything else that day got bigger in the telling." This is a banned meta-disclaimer variant ("I want that plain" / "I want to be exact"). It signals the narrator's concern that the reader won't trust the details without the frame. The frame is also unnecessary — the specific measurements that follow establish precision without announcement.

**ch09:**
- [ ] None found.

**Ruling:** ch08 has one meta-disclaimer (L5). Fix required.

---

### 3d. Narrator stepping outside time / future-vantage (ZERO allowed)

**ch08:**
- [x] Found: L63 — "And the genius of it, which I only understood later and hated..." — **Ruling: borderline permitted.** The phrase "which I only understood later" does step outside the story's present moment, but it is a close-retrospect admission of delayed understanding rather than a dramatic-irony announcement of significance. It does not say "I did not know then what this would cost him" or telegraph a future event. The construction reports retrospective knowledge without spoiling or inflating. Under the `PROSE_PATTERNS_TO_AVOID.md` rule: "Permitted: close-retrospect that reports what Daniel knew or felt at the time." This narrowly qualifies. However, "which I only understood later and hated" could be tightened to remove the retrospect frame entirely ("The genius of it — and I hated it — was...") if the writer wants to stay strictly in the present.

- [x] Found: L55 — "I knew him before I could have known him." — **Ruling: permitted.** This is an immediate recognition moment, not a future-vantage statement. Daniel is explaining his visceral response to Vibenius before he had conscious grounds for it. Close-retrospect, no spoiler.

**ch09:**
- [ ] None found.

**Ruling:** ch08 has one borderline future-vantage (L63) that is technically permitted but worth tightening.

---

### 3e. "The way you / the way a man / the way a child" constructions (max 3 per chapter)

**ch08:** Count: 6
- L11: "looked at the bag the way you look at a dog you have been told bites"
- L25: "I felt the moment coming the way you feel a sneeze"
- L53: "the way a crowd parts for someone it is afraid of in the other direction"
- L55: "the way he had watched the entrails on his board"
- L57: "put two fingers on a fold of the gray linen the way Heras put two fingers on a pulse"
- L65: "I felt it tip the way I had felt the bag tip"
- L75: "looked at me the way you look at a sum"
- L77: "He said it the way you would say a wall had decided to move"

**Over limit.** Count: 8. Limit is 3. Five instances must be cut or rewritten.

**ch09:** Count: 4
- L11: "the way water moves around a stone"
- L65: "the way a contractor counts a tally"
- L119: "the way you drop something hot"
- L105 area: "the fondness a man feels for a thing that has done exactly what he expected it to do" — this is not the construction but is adjacent.

**Over limit.** Count: 4. Limit is 3. One instance must be cut.

**Ruling:** Both chapters are over the "the way" limit. BLOCKER for ch08 (8 instances vs limit of 3). Revise for ch09 (4 vs limit of 3).

---

### 3f. Wisdom-button scene/chapter endings (max 1 per chapter)

**ch08:**
- Chapter ending type: **action/image** — the last paragraph ends on Daniel rising from the ash with the folded bag, the smoke going up between the insulae. Not a wisdom-button. Good.
- Scene 1 close (pre-first scene break): paragraph ending on "this is the dumbest place in the world to light a fire" — dialogue cut / internal line. Not a wisdom-button.
- Scene 2 close (pre-second break): "Now. / They let go." — action cut. Excellent.
- Scene 3 close (pre-third break): "I have tried to say the next part right and I always fail, so here is the failure." — transition framing. This is meta-commentary (similar to a throat-clear), borderline. Functions as scene-opening more than scene-closing.
- Scene 4 close (pre-fourth break): The smoke of my best bag going up in the sky — image cut. Good.
- Within L63: "The haruspex is never wrong. That is the whole craft." — **Wisdom-button within a scene,** not at a chapter end. It restates Vibenius's skill as a portable aphorism. It could be extracted as a tweet with no context. This is the definition of the banned form. At L65, the paragraph immediately following also contains "A man can be visible and dead in the same hour" — another wisdom-button.

**Count: 2 wisdom-buttons within ch08** (L63 and L65). Limit is 1 per chapter. One must be removed.

**ch09:**
- Chapter ending type: **action/image** — the final sentence is Daniel following Tyche out "into the loud bright city." Image + motion cut. Not a wisdom-button.
- "That was the meeting" (L113) — **Wisdom-button within scene.** Short declarative summary sentence at scene close. Could be extracted as an epigram. Flag.
- "a cage so well made it looked from the inside like a workshop" (L99) — **Wisdom-button within scene.** Strong epigram, portable as a tweet. Flag.

**Count: 2 wisdom-buttons within ch09** (L99 and L113). Limit is 1 per chapter. One must be removed.

- [x] Over limit — both chapters.

---

### 3g. "Thing" as vague placeholder

**ch08:**
- L37: "the kind of sound that has no word in it because the word hadn't been invented yet for what they were seeing" — "thing" not present here but adjacent.
- L41: "the thing that had gone up like a soul going up" — "thing" as stand-in for "balloon." Specific noun available: "the balloon."
- L47: "By the standard of the thing it was nothing" — "thing" as stand-in; "the landing" or "the crash" would be more specific.

**ch09:**
- L51: "a thing I forgot I owned" — "thing" as stand-in for "you/the foreigner."
- L55: "a thing a person actually did" — "thing" as stand-in for "action."
- L59: "a thing that requires keeping" — acceptable: keeping alive is not easily named more specifically.
- L87: "The thing this morning" — stand-in for "the flight" or "the demonstration."
- L95: "He used the word like he owned it, which he did. It went through me anyway — first time anyone but me had named the thing" — "thing" as stand-in for "balloon." Available specific noun.
- L111: "He looks like a thing I bought cheap" — "thing" in dialogue, in character voice. Acceptable: Macer speaks this way about people deliberately.

**Worst cases:**
- [x] ch08, L41: "the thing that had gone up" → "the balloon" or "the bag"
- [x] ch09, L87: "The thing this morning" → "The flight" or "the demonstration"
- [x] ch09, L95: "named the thing" → "named it" or "named the balloon"

---

### 3h. Gnomic aphorism stacking (flag if 2+ in a single chapter)

**ch08:** L63 ("The haruspex is never wrong. That is the whole craft.") + L65 ("A man can be visible and dead in the same hour.") — **Stacked.** Two standalone moral observations in the same chapter. Flag.

**ch09:** L99 ("a cage so well made it looked from the inside like a workshop") + L113 ("That was the meeting.") — **Borderline.** The first is clearly gnomic. The second is a flat statement that functions as a button but is not a moral observation. Count as 1 true gnomic aphorism stacked with 1 wisdom-button.

- [x] ch08: stacked — L63 + L65
- [x] ch09: one gnomic + one button — L99

---

## 4. Secondary Tic Check

*(Flagged items only)*

- **Polysyndeton runs** (max 1 per chapter):
  - ch08: 2 polysyndeton runs — L35 ("no smoke, no bird, no thrown thing... it went up and kept going, a man-sized gray shape climbing...") and L37 ("Delight, yes. A woman... laughing and pointing and shaking..."). The L35 run is the stronger and more earned (the release moment). The L37 run is weaker and could be cut. Flag: cut or compress L37 polysyndeton.
  - ch09: 0 full polysyndeton runs. OK.

- **"Nobody tells you" formula** (max 1 per book): absent in both chapters. OK.

- **False-modesty rhythm** ("I was an idiot" then immediate sophistication):
  - ch08: absent. OK.
  - ch09: L101: "the part of me that was still eighteen and stupid and a year homesick" — Daniel calls himself stupid, then the next paragraph shows him calculating (L83: keeping tally on the other side). This is the false-modesty rhythm. Flag. However, in this instance he actually does make a mistake (asking for freedom), so the "stupid" self-assessment lands correctly — it's a genuine error, not a setup for sophistication. **Permitted.**

- **"Which is to say" pivot** (max 1 per 10 chapters): absent in both. OK.

- **"Looked at me"** (max 2 per chapter):
  - ch08: count 3 (L61, L67, L75). **Over limit.** One must be cut or replaced. L67 ("Vibenius looked at me one more time before he went") is the weakest — "The same flat three-count" can carry the beat without the setup.
  - ch09: count 2 (L17, L127). At limit. OK.

- **One-sentence paragraphs** (max 15% of paragraphs):
  - ch08: 6 of approximately 35 paragraphs = 17%. Slightly over limit. "Now." and "They let go." are both essential — they function as the launch beat's rhythm. The other 4 are more compressible. Flag as marginal.
  - ch09: The count is harder here because the dialogue-heavy structure generates many short paragraphs. Approximately 23 short/one-sentence units of ~64 total = 36%. **Well over limit.** Many of these are dialogue exchanges where the beats are being carved into single lines for emphasis. Revise to absorb several into adjacent paragraphs — particularly the sequence L69-L75 (Macer's tally) which chops dialogue + reaction into many small beats.

- **Cycle of defeat** (idea → works once → fails → depression → pivot): not present as a structural tic in these chapters. The demo both succeeds and fails as intended by the chapter's design.

- **Ledger-as-catharsis**: L83 of ch09 (Daniel tallying the other side of the ledger after Macer's speech). This is one instance, used correctly — Daniel calculates because that is his mode, and the scene doesn't use it to resolve emotion. **Not a flag.**

- **Socratic echo**: absent in both. OK.

- **"Let it sit / let that hang"**: L61 of ch08: "He let that sit." (Vibenius letting the omen announcement sit.) One instance, assigned to Vibenius — appropriate. OK.

---

## 5. Canon Consistency

*(Checked against `bible/08_canon_log.md` and `bible/03_timeline.md`)*

- **Daniel's age this chapter:** ~99 AD; Daniel born ~81 AD (17 in spring 98 AD). Expected: ~18 by mid-99 AD. Neither chapter states his age explicitly. ch09 has Daniel calling himself "still eighteen and stupid" (L101), which is consistent with ~18 at this point. Consistent.

- **Other character ages:** Tyche "fourteen maybe" (ch09 L119, L127). Canon log says "~14." Consistent. (See also Section 6 / Key Check below.)

- **Dates / era:** Both chapters ~mid/late 99 AD per canon log. Internal evidence: the demo is during a festival with "the emperor came" framing (L7), consistent with Trajan's 99 AD adventus into Rome per `bible/03_timeline.md`. Consistent.

- **Tech state:** Balloon is unmanned, greased linen, ash-wood hoop, no sustained heat mechanism — consistent with Phase A balloon state (no basket, no sustained flight). L41 establishes the heat-loss problem explicitly. Consistent with canon log and tech schedule.

- **Named objects / relics:**
  - Daniel's burn scar: ch08 L23 describes "the scar on my right forearm and the newer one across the back of the same hand." The canon log V2 change note (#6) flags "burn-scar re-explanation" as a problem to avoid by ch08 — readers already know it. The description here names both scars as context-specific ("both of them screaming in the warmth") rather than re-explaining their origin. This is a reference, not a re-explanation. **Borderline permitted.** The phrase "the scar on my right forearm" is fine; remove any origin explanation if one exists.
  - Phone: not referenced. Appropriate — the phone is dead by this point.
  - Daniel's machine-made boots: referenced at L19 of ch09 ("boots... soled in a black stuff no cobbler could make"). Consistent with canon log. Pass.

- **Macer's deal terms (ch09):**
  - Canon log says: cloth, two slaves, walled yard off timber wharf, peculium. Prose says: cloth, two slaves, yard off timber wharf, peculium. **Consistent.**
  - Canon log says freedom refused ("men a great deal higher"). Prose L107 matches verbatim. Consistent.
  - Canon log says Macer acquired Daniel for "less than a season's mules." Prose L31: "I bought you for less than I pay for a season's mules." Consistent.

- **Vibenius (ch08):**
  - Canon log says Vibenius was present, pronounced deliberate ambiguous omen, "still no meeting/words with Daniel beyond the locked-eyes look" — but wait. The canon log says "Still no meeting/words with Daniel beyond the locked-eyes look." However, in the prose, Vibenius speaks aloud to the crowd in Daniel's presence, and Daniel hears and interprets it. **Discrepancy.** The canon log for [ch08] says "still no meeting/words"; the prose has Vibenius speaking a formal pronouncement in Daniel's direct presence (L61). This is not a private conversation — it is a public statement to the crowd that Daniel overhears — but it is more than a "locked-eyes look." Coordinator should clarify whether this constitutes the "no words" canon or whether the canon log needs updating.

**New canon facts introduced:**
- Davus (new named character; household slave; "does not run").
- Vibenius's public omen phrasing established: both-doors structure, haruspex-never-wrong craft.
- Macer's wooden disc as physical tic (in addition to ring-turning).
- Tyche's first words to Daniel established: "The yard is by the wharf... Long walk. You should eat the bread while you walk."
- The balloon named in-world by Macer on this day.

---

## 6. Voice

- **Daniel's voice:** dry, self-deprecating, specific throughout both chapters. L55 of ch09: "I hated that some animal part of me, after a year of being a sum, was glad to be laughed at like a person" — this is exactly the voice spec. The dry register holds. No drift toward earnest or solemn. **Pass.**

- **Heras:** dry, ironic, characteristically watching rather than acting. L39 of ch09: "I sold you the sum: a strange foreigner, cheap, possibly worth nothing, possibly worth a great deal." Correct register. **Pass.**

- **Macer:** blunt, transactional, mean-funny, crude-register. Voice is strong throughout ch09. The wooden disc tic is appropriate. His line "He looks like a thing I bought cheap" lands correctly. He does not perform warmth. **Pass.**

- **Vibenius:** formal, Latin slow and careful, face unchanged, deliberate. Ch08's Vibenius scene is one of the chapters' strongest sections. The craft explanation (both doors) is built into his action and Daniel's retrospect, not stated as a character description. **Pass.**

- **Tyche's introduction (KEY CHECK):**
  - Age: "fourteen maybe" (L119) and "fourteen" (L127). The QA brief requires a specific age, not "younger." **Present and specific.** Pass.
  - "Eyes not quiet at all": L119: "except that her eyes were not quiet at all." **Present verbatim.** Pass.
  - Register: terse, guarded, gives nothing back, drops eyes as practiced reflex. Final lines: "The yard is by the wharf... Long walk. You should eat the bread while you walk. He won't give you time to eat it there." These are concrete, functional, no warmth performed. **Pass.**
  - Note: Tyche's eyes-not-quiet observation is embedded inside a correctio-adjacent construction: "she moved... quiet, ready, gone... except that her eyes were not quiet at all." The "not X... except" pivot is not the banned correctio form (it is a qualification, not a premise-cancellation). **Permitted.**

- **Crowd voices (ch08):** fragmented — delight, fear, "witch," wonder. Not uniform awe. Chapter-list ch06 spec requires this. **Pass.**

- **No muted mutes:** Pamphilus not present. N/A.

- **Info-delivering monologue:** Macer's tally speech (L67-L77) is 4+ consecutive lines of explanation without interruption. However, it is cast as a first-person offer to Daniel rather than an explanation to the reader, and it is broken by the finger-counting physical business. Borderline but acceptable in context — it is a negotiation scene, and Macer's monologue is in character (he controls the room). No flag.

- **Daniel competence:** He panics (L7: "my heart going like a fist on a door"), makes a mistake he knows he made (asking for freedom prematurely), and his Latin fails under pressure ("the cases sliding, the v turning to w"). **Pass.**

---

## 7. Verdict

### ch08 ("Fire That Flies"): **REVISE**

Strong chapter. The balloon scene is well-paced and sensory. Vibenius is excellent. Three issues require attention:

### Blocking issues

1. **Correctio violation — L49:** "Not to comfort me. To hold me where I was" — rewrite to lead with the positive. Suggested fix: "His hand closed on my arm to hold me where I was, not to comfort me — because the steward had told him to, and because running is the one thing that turns *what god* into *kill it*."

2. **"The way" limit exceeded — 8 instances vs. limit of 3.** Cut or rewrite 5 instances. Priority cuts: L11 (simplest), L57 (can be absorbed), L77 (the wall-analogy one; rewrite). Preserve L25 (the sneeze comparison — specific and earned) and L65 (the tipping sensation — structural callback).

3. **Wisdom-button stacking at L63-L65:** "The haruspex is never wrong. That is the whole craft." plus "A man can be visible and dead in the same hour." Two portable aphorisms in the same chapter. Cut L65's button; the preceding paragraph already delivers the insight through action and observation.

### Revise items

4. **Meta-disclaimer — L5:** "I want that on the record" — cut the frame. Begin: "The bag was the size of a man hung head-down. Folded, it was an armful." The precision that follows justifies itself.

5. **"Looked at me" count — 3 instances vs. limit of 2.** Cut or replace L67: "Vibenius looked at me one more time before he went" can become: "He gave me one more flat three-count before he turned."

6. **Polysyndeton — L37 second run:** the crowd-response paragraph ("Delight, yes. A woman near the fountain was laughing and pointing...") is a weaker polysyndeton. Compress.

---

### ch09 ("Macer"): **REVISE**

Excellent chapter. Macer's voice is exactly right. Tyche's introduction delivers both required elements (specific age, "eyes not quiet at all"). Two structural issues require attention:

### Blocking issues

1. **"The way" limit exceeded — 4 instances vs. limit of 3.** Cut one: L11 ("the way water moves around a stone") is the weakest — "all of it moving around one chair" is already a good image without the simile.

2. **One-sentence paragraph density — approximately 36% vs. limit of 15%.** The dialogue sequences in the Macer negotiation section (approximately L67-L113) need consolidation. The single-line exchanges ("Macer glanced up... 'Still with me.'" / '"Yes," I said.') are effective but cluster too densely. Merge several adjacent short paragraphs in the negotiation sequence.

### Revise items

3. **Wisdom-button stacking — L99 and L113:** "a cage so well made it looked from the inside like a workshop" is strong and can stay as the chapter's one permitted button. "That was the meeting" (L113) is the weaker one — cut it. The preceding paragraph ("the room closing over the place where I had been... He would see me. Now. Today") makes a better close to that movement.

4. **Vibenius canon discrepancy:** The canon log says "still no meeting/words with Daniel" after the demo. The prose has Vibenius delivering a formal public pronouncement in Daniel's presence. Coordinator must clarify canon: update the log to reflect the public speech, or restrict Vibenius's ch08 role to the ambiguous omen without direct address.

---

### Notes for coordinator

- **Chapter numbering:** `ch08.md` and `ch09.md` prose files carry canon-log numbering (~99 AD public demo + Macer meeting). `chapter_list.md` assigns these numbers to the Dacian War chapters (~101-102 AD). The prose files may be early drafts that predate a renumbering of the outline. Resolve before the next chapter is drafted — the Frontier chapters (currently labeled ch08/ch09 in the outline) need different file names, or the prose needs renaming.
- **New canon to log:** Davus (named character, household slave, assigned to the demo). Macer's wooden disc tic. Tyche's first words established (the yard/bread/walk). Balloon named in-world on this day by Macer.
- **Celer:** Not present in prose ch08 despite ch06 (chapter_list) specifying he appears at the launch. Either: (a) Celer is to be added to the demo scene, or (b) the outline's ch06 intent is split across the two prose chapters and Celer appears in neither, requiring a subsequent chapter to introduce him. Flag for writer.
- **Burn-scar:** ch23's note in V2_CHAPTER_CHANGE_NOTES applies — by this chapter the burn should be referenced, not re-explained. The prose reference in ch08 is a reference, not a re-explanation. No action needed, but confirm this is the first time the scar appears in prose.
- **"Not quiet at all" and Tyche's age:** Both required elements present and correct. No action needed.
- **Children chronology:** Clean. No child scenes in either chapter. Lucanus is not born until ~108-110 AD; these chapters are ~99 AD. Pass.
- **Food arc:** No garum, omelette, or Phase A food beat in either chapter. Per `V2_FOOD_ARC.md` Section 7, the demo/Macer chapters are not assigned a food beat. The one food moment (bread and watered wine in the corridor) is era-appropriate and characterful. No New World crops. Pass.
