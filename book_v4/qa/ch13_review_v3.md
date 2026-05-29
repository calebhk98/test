# QA — Chapter 13: The Fall
**Reviewer:** QA Agent (Claude Sonnet 4.6)
**Date:** 2026-05-29
**Word count:** 3,389 words
**V2 change notes applied:** Partial — three of five V2 BLOCKERS resolved; two correctio-adjacent constructions survive; one new zero-tolerance issue (meta-disclaimer variant) introduced

---

## 1. Plot Beats

*(Source: `outline/updated_ch01_18.md` ch13 entry; `bible/08_canon_log.md` ch13 entry)*

| Beat | Present? | Notes |
|---|---|---|
| Manned free-flight balloon to scout Dacians behind "the Loaf" | Yes | Fully rendered |
| Daniel warns about wind; overruled because slave | Yes | Explicit: L53, L59 |
| Sabinus volunteers; named; wife and children planted | Yes | L45, L81 — names revealed post-death (V2 requirement met) |
| Apollodorus dismisses the balloon; advises Daniel to find someone who can stop it | Yes | L25–35 — rendered as requested |
| Naso present, warns "make him keep his seat" | Yes | L47 — his V2 spoken line delivered |
| Bag rises clean to ~100 ft; crosswind tips fire-bowl; seam ignites; Sabinus falls | Yes | Detailed, specific, correct failure mode per V2 tech spec |
| Daniel on knees in dirt; Naso's wordless hand over his fist | Yes | L85 — strong silence-cut execution |
| Celer takes responsibility; bans further manned ascent; challenges Daniel on "what kind of man" | Yes | L89–95 |
| Pamphilus at the river; small fire; Daniel burns the rag | Yes | L99–111 |
| Vow reframed as engineer's rule ("I will not rush untrained people into an untested design") | Yes | L107 — the word "rush" present; correctly framed as process rule, not abandonment |

**Over-resolved beats:** None. The chapter does not answer questions that belong to later chapters (the reassessment is seeded without resolution).

**Unplanned beats:** The Apollodorus scene at L25–35 is richer than the outline specifies — it earns its space and plants the "hated and envied him in turns" retrospect line.

**Missing beats from V2 spec:** None. All V2 requirements for ch13 are present.

---

## 2. New V2 Arcs

- **Food arc** (`V2_FOOD_ARC.md`): Absent. N/A — ch13 is a battle-front chapter; no food arc beat required here.
- **Prize/innovation arc** (`V2_PRIZE_INNOVATION.md`): Absent. N/A for ch13.
- **Children's education arc** (`V2_ULPIA_EDUCATION.md`): Absent. N/A — Lucanus not born yet.
- **Tech/bootstrapping** (`V2_TECH_DEEP_DIVE.md`): The failure is technically specific (treated linen + crosswind tipping the fire-bowl = seam ignition). Daniel's post-mortem at L105–107 correctly identifies the design gap (never flown free; untested in wind). This is the correct Phase B humbling beat.
- **Atlantic/New World**: N/A for ch13.
- **Historical divergence**: Ch13 plants the manned-balloon attempt as a divergence (a Roman soldier dies in a way that never happened historically). No explicit divergence logging required here; it is embedded in the event.

---

## 3. Prose Tics — Zero-Tolerance Sweep

### 3a. Correctio / "Not X, it's Y" (ZERO allowed)

**Two instances found:**

- [x] Found: **L67** — `"the fire was not in its bowl anymore, it was a sheet of flame being pressed flat against the side of the bag by the wind"`
  - This is the exact banned form: "was not X... it was Y." The V2_CHAPTER_CHANGE_NOTES ch13 flagged a different correctio (L43 in V1, now fixed) but this instance, apparently present in V3, was not in the original BLOCKER list — meaning it either survived from V1 or was introduced in V3.
  - **Fix:** State the physical fact directly. Example: "The fire had left the bowl entirely; the wind had laid it flat against the linen, a sheet of flame."

- [x] Found: **L35** — `"for a moment there was something in it that was not rivalry, something that was just one man who builds things looking at another man who builds things"`
  - This is the soft form: "not X, something that was just Y." Defines the emotion by negating the wrong word first. The PERMIT list in V2_CHAPTER_CHANGE_NOTES ch13 explicitly preserves the "I have hated and envied him" line (L35 tail), but the correctio is in the same sentence's opening clause — it was not caught in the ch13 V2 BLOCKER review.
  - **Fix:** Cut the negation opening. Example: "For a moment across that problem, we were just two men who built things." The hated/envied line that follows is permitted and should stay.

**Ruling: REVISE. Two correctio instances. Zero-tolerance rule is violated. Both must be fixed.**

---

### 3b. Em dashes (ZERO allowed)

- [x] None found. Em dash search returned zero results. PASS.

---

### 3c. Meta-disclaimers / throat-clearing (ZERO allowed)

- [x] Found: **L71** — `"a sound I am not going to write down"`
  - This is TIC V1 / V14 — the narrator prefaces a moment by announcing what he will not do. The banned variants include "I am not going to dress up what I felt" and similar. The construction here ("a sound I am not going to write down") announces the narrator's restraint rather than exercising it. It performs discretion rather than being discreet. Direct statement — "the sound of all of him arriving at the ground at once" already follows immediately and does the work. The meta-frame is surplus.
  - **Fix:** Delete "a sound I am not going to write down." The sentence already contains the description: "the sound of all of him arriving at the ground at once." Simply join: "...and the sound of it reached me a moment after I saw it — the sound of all of him arriving at the ground at once."
  - **Note:** Do not use an em dash in the fix. Use a comma or period: "...the sound of it reached me a moment after I saw it, the sound of all of him arriving at the ground at once."

**Ruling: REVISE. One meta-disclaimer. Zero-tolerance rule is violated.**

---

### 3d. Narrator stepping outside time / future-vantage (ZERO allowed)

The V2_CHAPTER_CHANGE_NOTES ch13 explicitly PERMITS certain retrospect lines in this chapter. This review applies that ruling.

**Permitted (per explicit V2 ruling):**
- L35: `"I have hated and envied him in turns across many years"` — close retrospect reporting a known ongoing state. PERMITTED.
- L45: `"which I have never forgiven the army for letting a man do"` — retrospective emotional fact, not dramatic irony announcement. PERMITTED per the ch13 ruling.
- L81: `"I have them still, the names, in the order he said them"` — explicitly permitted per V2_CHAPTER_CHANGE_NOTES ch13. PERMITTED.
- L111: `"that smell I will not get out of the back of my throat as long as I live"` — explicitly permitted per V2_CHAPTER_CHANGE_NOTES ch13. PERMITTED.

**Questionable — review recommended:**
- L61: `"it was the most beautiful thing I have ever built"` — this is a retrospective superlative that functions as a significance announcement ("the most beautiful thing I have EVER built"). This is borderline: it is a claim about subjective experience (permitted retrospect) but its placement just before the disaster makes it a de facto significance-from-the-future flag. The style guide's "permitted exception" is "reports retrospective knowledge"; this is on the edge. Not flagging as BLOCKER given the ch13 explicit permits, but recommend editorial review.

**Ruling: No new future-vantage BLOCKERs beyond what V2 already resolved. One borderline instance noted above.**

---

### 3e. "The way you / the way a man / the way a child" constructions (max 3 per chapter)

Instances found:

1. **L31**: `"This holds heat the way a sieve holds water"` — Apollodorus dialogue.
2. **L61**: `"the first part went exactly the way the whole idea promised"` — narration.
3. **L81**: `"He'd said it the way soldiers say these things before a risk"` — narration.

Count: **3**. At the hard limit. Within cap.

- [x] Within limit (exactly 3). No flag.

---

### 3f. Wisdom-button scene/chapter endings (max 1 per chapter; aim 0 per 3 chapters)

**Scene-ending audit:**

- Scene 1 close (L21): `"and at the bottom of it he set the tablet down, weighing exactly what it could do and not an inch more."` — IMAGE CUT. Strong concrete ending.
- Scene 2 close (L37): `"and obeying a slave was not a thing a tribune did in front of an army three days from a fight."` — This is a STATEMENT close — summarizes the power reality. Borderline wisdom-button: the sentence states a general social truth (a slave's no is not real). It is not a portable aphorism in the gnomic sense, but it does restate what the scene already showed. FLAG: mild wisdom-button tendency. Not a full button, but worth noting.
- Scene 3 close (L49): `"he checked the cord on his own and closed his fingers around it."` — ACTION CUT. Excellent.
- Scene 4 close (L71): `"The cloth came down after him, still burning, and laid itself over him like something being tucked in."` — IMAGE CUT. The simile ("like something being tucked in") borders on the poetic-summary; the image is concrete and carries the horror without naming it. PASS — this is the model TYPE 1/4 ending the style guide calls for.
- Scene 5 close (L85): `"a man with a ruined hand can still tend mules and the work does not stop for anybody."` — WISDOM BUTTON. This is a portable generalization ("the work does not stop for anybody") appended to a concrete action (Naso limping away). The concrete action (limping toward baggage) is the correct ending; the appended axiom names what the reader already felt. This is one wisdom button used.
- Scene 6 close (L95): `"He went to send the litter and write the letter."` — ACTION CUT. Clean and correct.
- Chapter close (L111): `"that smell I will not get out of the back of my throat as long as I live."` — This is a quasi-wisdom-button: a portable personal truth that could be extracted and stand alone. However, it is explicitly PERMITTED per V2_CHAPTER_CHANGE_NOTES ch13 as an earned close-retrospect. It is not a general maxim — it is a specific sensory fact of this specific narrator. The permit stands. Count it as the chapter's one allowed button, or as a retrospect (the rule permits one type-5 per chapter). Either way, the Scene 5 close (L85) and this chapter close compete for the one-per-chapter wisdom-button budget.

**Assessment:** Scene 5 (L85) is the cleaner REVISE target — it appends a general truth to a concrete action that already does the work. The chapter close (L111) is the permitted retrospect. **Scene 5 must be trimmed to end on the action (Naso limping) rather than the axiom.**

- Chapter ending type: permitted close-retrospect (sensory fact)
- Wisdom-button count: 1 soft (Scene 5, L85) + 1 permitted (chapter close L111) = over limit if Scene 5 is counted as a button.
- [ ] Over limit — **Scene 5 close at L85** should be revised: cut "and the work does not stop for anybody." End: "and limped off toward the baggage."

---

### 3g. "Thing" as vague placeholder

Problematic uses:

- **L37**: `"obeying a slave was not a thing a tribune did"` — "thing" is placeholder for "act" or "practice." Minor.
- **L59**: `"the thing about being property is that your no is a sound you make, not a thing that happens"` — "thing" used twice, the second as abstract placeholder for "event" or "fact." The construction is load-bearing and the double "thing" is slightly sloppy but not the worst instance.
- **L99**: `"that was a thing that worked and did not lie on a good day"` — "thing" is placeholder for "practice."
- **L105**: `"into something I had only flown on a rope"` — "something" as a vague substitute for "a design" or "a bag."

- [ ] Worst cases: L99 `"that was a thing that worked"` → "a practice that worked"; L105 `"something I had only flown"` → "a design I had only flown." These are SHOULD FIX items, not BLOCKERs.

---

### 3h. Gnomic aphorism stacking (flag if 2+ in a single chapter)

- **L37**: Scene 2 close — general social truth about slave's obedience (borderline button).
- **L85**: Scene 5 close — "the work does not stop for anybody" (confirmed button).
- **L107**: `"An engineer owes the people under his work better than I had given Sabinus."` — This is Daniel's post-disaster self-assessment. Borderline gnomic: it states a general engineering principle. In context it is specific self-recrimination, not an abstract maxim. Borderline, not flagging as stacked aphorism.

**Two gnomic instances in L37 and L85.** Not a hard-block violation but worth trimming one.

---

## 4. Secondary Tic Check

- **Polysyndeton runs** (max 1 per chapter): One clear instance at **L41** — "I lined the fire-bowl... and set it on a wet plank and rigged a lid... I soaked the willow. I soaked the hides. I made him a hood and gloves..." This is controlled and appropriate (inventory of safety measures, Daniel's anxiety visible in the listing). Count: 1. — [x] OK.
- **"Nobody tells you" formula**: Absent. — [x] Absent.
- **False-modesty rhythm**: Absent in this chapter — Daniel does not call himself an idiot before doing sophisticated analysis. — [x] Absent.
- **"Which is to say" pivot**: Absent. — [x] OK (0/10-chapter budget used).
- **"Looked at me"** (max 2 per chapter): **L21** `"I watched it land"` (not a "looked at me"), **L59** `"I looked at Sabinus and Sabinus looked back at me"` — this is one instance of the "looked at me" form. Count: **1**. — [x] Within limit.
- **One-sentence paragraphs** (max 15%): Count = **7 of 49 paragraphs = 14.3%**. — [x] Within limit (barely). The seven are:
  1. L5: "So they sent for me to put a man over the Loaf." — pivot sentence, justified.
  2. L13 (Apollodorus): his single-line question — dialogue paragraph, justified.
  3. L15: "I know," I said." — dialogue, justified.
  4. L23 (Scene 4 open): "The wind was wrong from the start..." — good tension opener.
  5. L57 (Celer): "'On your word,' Celer said." — dialogue, justified.
  6. L37 (post-wisdom): see Scene 2 close concern above.
  7. L103: "I thought about what Celer had said. About what kind of man builds a thing like that." — Two-sentence para counted as one para block. The second sentence is a fragment completing the first. This is borderline; the repetition of Celer's question could be trimmed.
- **Cycle of defeat**: Present, but this IS the defeat chapter and it is structurally justified. Not a tic here; it is the content.
- **Ledger-as-catharsis**: Absent. Daniel does not list or count his way through the grief. Notably, the post-death sequence does NOT pivot to inventory. This is correct and good — the scene earns the emotions directly.
- **Socratic echo**: Near-absent. Naso's "Make him keep his seat" is not a mirror of Daniel's analysis; it is its own independent voice. Pamphilus is correctly silent and does not echo Daniel. [x] Absent.
- **"Let it sit / let that hang"**: Absent. [x] Single-instance only (it does not appear at all).

---

## 5. Canon Consistency

- **Daniel's age this chapter**: Ch13 = 101–102 AD. Daniel born 81 AD (story-relative). Age: 20–21. Not stated explicitly in the chapter (correct — no age statement needed). — [x] Consistent.
- **Sabinus's name**: Chapter gives `"Marcus Aurelius Sabinus."` Canon log ch13 entry also lists `"MARCUS AURELIUS SABINUS."` — [x] Consistent.
- **Sabinus's family**: Chapter: "a wife in a town in Pannonia and two children, a boy old enough to mind the goats and a girl." Canon log: "a wife and two children (a boy who minds the goats, and a girl) in Pannonia." — [x] Consistent.
- **Naso's injuries**: Chapter: "his left hand curled against his chest as it had healed, a claw of shiny skin, and his ankle still putting a hitch in his walk." Canon log ch11: "BADLY burned (back, neck, arm; a ruined LEFT HAND; a broken ankle)." — [x] Consistent.
- **Pamphilus**: Canon log ch12: "PAMPHILUS came north with Daniel; TYCHE stayed in Rome." Chapter: Pamphilus present at river. — [x] Consistent.
- **Apollodorus**: Canon log ch12: introduced at the Danube bridge. Chapter: Apollodorus already known to Daniel, reuses "a clever toy that does one thing" — consistent with ch12 canon. — [x] Consistent.
- **Daniel's free-flight envelope design**: Chapter: "oversized slow envelope... longer basket, Macer's design from Rome... lined the fire-bowl in wet clay and set it on a wet plank and rigged a lid he could drop by pulling one cord... soaked the willow. I soaked the hides." Canon log ch13: lists exactly these measures. — [x] Consistent.
- **Tyche** (age): Not referenced in this chapter. N/A.
- **Lucanus** (age): Not born yet. N/A.
- **Daniel's status**: He is "a slave on loan" at L37. This is correct for 101–102 AD (freedom not granted until ch17, ~104–105 AD). — [x] Consistent.
- **Name convention**: Daniel referenced as "the Thulean" by Sabinus at L59 (`"Let it go, Thulean"`). Canon: his cover name is well established by this chapter. — [x] Consistent.
- **Celer's rank**: Referred to as "tribune" at L37. Canon log ch11: "equestrian tribune." — [x] Consistent.
- **Tech state**: The "long basket, Macer's design from Rome" references Macer as already involved in balloon engineering direction. The canon log ch13 notes "oversized slow envelope, a long low basket (sit low, keep weight under the bag)." The detail "Macer's design from Rome" is a minor new fact not in the canon log (the long basket being attributed to Macer). This is plausible given Macer's contractor interest in the balloon, but the canon log does not record this attribution. Note for coordinator.

**New canon facts introduced this chapter:**
- The long basket design is attributed to Macer (L41: "I built a longer basket, Macer's design from Rome"). This is not in the canon log. Coordinator should log or verify this attribution.
- Sabinus's home town is "a town in Pannonia" (not more specific). This is consistent with the canon log's general "Pannonia" reference but not further specified.

---

## 6. Voice

- **Daniel's voice**: Dry and self-deprecating — intact. The voice is mature but not solemn: "my old burn-scars screamed where I'd grabbed it and I held it tighter" (L79) is the right register — physical, specific, not sentimental. The post-disaster reasoning at L105–107 is close to earnest-engineer mode rather than teen-dry-voice, but it is 101 AD (Daniel is 20) and the transition toward more measured narration is legitimate arc progression.
- **Celer's voice**: Correctly rendered. "You said the wind. You said all of it. I heard you and I let it go anyway. That's mine." — Clipped, consequence-stating, gallows soldier. Excellent. He does not become warm. "I can't decide it for you" — exactly right as a Celer line. Note: the quoted V2 fix (Celer saying his soldier's oath once) is NOT present in this chapter. The V2 character brief requires Celer to have one quoted crude oath somewhere in his arc. Ch13 is a plausible candidate (it is a high-stress failure scene); this was not placed here. Coordinator should track whether Celer's oath appears in any chapter before ch29 (his death).
- **Apollodorus's voice**: Correctly preserved. The "clever toy that does one thing" callback is consistent. His physical detail (crouching with the ease of a man who has carried himself up scaffolds for thirty years) is very good. His contempt is "total and serene" as the character spec requires.
- **Naso's voice**: The V2 required pre-disaster crude/cocky line was supposed to appear in ch11. In this chapter, Naso appears POST-disaster (his injuries are from ch11). His ch13 dialogue ("Make him keep his seat." / "Tell him I said. The standing up. Tell him.") is correct for the post-injury register — clipped, weight-bearing, not cocky. His face at L47 — "His face when he said it was not a young face anymore" — is permitted close-retrospect, not a banned future-vantage construction. The observation is about what Daniel sees in Naso's face right now, not a future annotation.
- **Pamphilus**: The chapter contains the construction "he didn't say anything" at L99 — this is the V1 problem the characters bible explicitly flags. The V2 FIX requires at least 4 spoken Pamphilus lines across the book. The canon log entry for ch13 also notes `"Pamphilus did not say anything"` as a recurring V1 problem. In ch13 Pamphilus's silence is thematically motivated (his wordless act of starting the boiling-water fire IS his communication), and the silence is framed through his action rather than blank absence. HOWEVER: if this is one of his major appearances and he remains silent, it depletes the book's Pamphilus-voice budget. Coordinator should track how many speaking Pamphilus lines appear in ch10–13 combined. If fewer than 2 direct quotations exist in ch10–13, a line must be added somewhere in this window.
- **Class-marked secondary voices**: The men at the launch ("soldiers laugh") are not quoted individually, which is acceptable here — the chapter's focus is on the central principals. No crowd-heckler requirement for this scene (it is a military operation, not a public demo).
- **Info-delivering monologue check**: Apollodorus's speech at L31 runs 4+ lines for a single character (`"They always want to... You have a man and a flame and the wind, in a basket... A clever toy that does one thing... The one thing is not this."`). This is 4 sentences/beats of continuous uninterrupted speech. It is at the hard limit. The speech is dramatically appropriate (Apollodorus dismissing the balloon in a single visit), but it is dense monologue. Borderline flag — not a BLOCKER but note for coordinator.
- **Daniel competence**: He genuinely gets things wrong — the wind-under-load failure was knowable but not foreseen in its specific dynamics. His post-death analysis at L105 correctly identifies his error without making him too analytical too fast. He did panic (the wordlessness, the knees-in-dirt); he faked nothing here. — [x] Competence correctly calibrated.

---

## 7. Verdict

**REVISE**

### Blocking issues (must fix before next use)

1. **CORRECTIO — L67**: `"the fire was not in its bowl anymore, it was a sheet of flame being pressed flat against the side of the bag by the wind"` — Exact banned "was not X... it was Y" construction. Fix: state the physical fact directly without the negation pivot. Example: "The fire had left the bowl; the wind had laid it flat against the linen, a sheet of flame pressed to the cloth." Do not use an em dash.

2. **CORRECTIO — L35**: `"for a moment there was something in it that was not rivalry, something that was just one man who builds things"` — Soft "not X, something that was just Y" form. Fix: open the clause directly. "For a moment, across a problem neither of them could stop, it was just one man who builds things looking at another." The "I have hated and envied him" tail is permitted; only the opening negation must be cut.

3. **META-DISCLAIMER — L71**: `"a sound I am not going to write down"` — This is TIC V1/V14: the narrator announces his restraint instead of exercising it. The sentence already contains the description immediately after. Fix: Delete the meta-frame entirely. "...and the sound of it reached me a moment after I saw it, the sound of all of him arriving at the ground at once."

### Revise items (should fix)

4. **WISDOM BUTTON — Scene 5 close, L85**: `"a man with a ruined hand can still tend mules and the work does not stop for anybody"` — The action (Naso limping off) is the correct ending. The appended axiom restates what the scene already showed. Fix: end on the action: "and limped off toward the baggage." Cut "because a man with a ruined hand can still tend mules and the work does not stop for anybody."

5. **"THING" PLACEHOLDER — L99**: `"that was a thing that worked"` — Replace with the specific noun: "a practice that worked." L105: `"into something I had only flown"` → "into a design I had only flown." Minor but cumulative.

6. **APOLLODORUS MONOLOGUE — L31**: Four-sentence uninterrupted speech runs at the hard limit for info-delivery (4+ consecutive unbroken lines). Not a full BLOCKER — the speech is dramatically motivated and Apollodorus's voice is correctly rendered — but it should be interrupted or broken: add one physical beat mid-speech (Daniel picking something up, or a pause in Apollodorus's movement) to break the static delivery. The content should stay.

7. **PAMPHILUS VOICE TRACKING**: In this chapter Pamphilus receives no spoken lines. Coordinator must verify: does Pamphilus have the required minimum 4 spoken lines distributed across ch10–ch13 or later? If ch10–13 contain zero or one direct quotation, a line must be placed in one of these chapters.

8. **CELER CRUDE OATH TRACKING**: Celer's one required crude oath (per character bible) is not in ch13. Coordinator: confirm it appears somewhere in ch11–ch29 (before his death). If not yet placed, ch13 or ch14 are appropriate candidates given the intensity of these frontier chapters.

### Notes for coordinator

- **New canon to log**: The long basket is attributed to Macer ("Macer's design from Rome," L41). This attribution is plausible but not in the canon log. Add to ch13 canon entry: `[ch13] The long low basket design is attributed to Macer (from prior Rome work)`.
- **Borderline future-vantage**: L61 `"it was the most beautiful thing I have ever built"` is a retrospective superlative placed immediately before the disaster. It is not a banned construction per the permitted-retrospect rule, but it does function as a significance flag. Coordinator decision: leave as is (explicitly permitted ch13 retrospect window), or read as borderline and apply the V4 future-vantage test strictly.
- **"The way" count at exactly 3**: The chapter is at the hard cap for this construction. Any V4 editing pass that introduces additional "the way" comparisons would push it over the limit.
- **Chapter length**: 3,389 words. Within the 2,500–4,000 word target.
- **What this chapter gets right (preserve)**: The Naso handclasp (L85) is a genuine prose high point — wordless, specific, non-sentimental. The Sabinus names revealed post-death (not pre-loaded before the flight) correctly follows the V2 restructuring. The Apollodorus physical detail is excellent. The failure sequence at L63–71 is technically precise without being clinical. The chapter-close (burning the rag into the fire) is earned and correctly permitted by the V2 ruling. These must not be touched in revision.
