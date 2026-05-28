# QA — Chapter 2: The Cell
**Reviewer:** QA Agent (claude-sonnet-4-6)
**Date:** 2026-05-27
**Word count:** ~3,857 words
**V2 change notes applied:** Partial — see Section 2 detail

---

## 1. Plot Beats

**Note on chapter alignment:** The `chapter_list.md` entry for ch02 is titled "The Map" and covers Heras's arrival, the dirt map, the numerals demonstration, and the start of Latin instruction. The prose file `ch02.md` is titled "The Cell" and covers Daniel's arrest, march through town, arrival in the cell, phone rationing, cover story decision, guards examining the phone, the optio cutting the rope, and the ending on food. This content matches what the `bible/08_canon_log.md` logs as ch02 events — the canon log and the prose are internally consistent with each other. The chapter_list.md treats this content as the tail end of ch01 ("Waking Up"), creating a numbering split between the outline and the prose. The review below evaluates the prose against the canon log's ch02 beats (which it matches) rather than the chapter_list.md's ch02 beats (which are a different chapter).

Expected beats per `bible/08_canon_log.md` ch02 entry:

| Beat | Present? | Notes |
|---|---|---|
| Bound with rope, marched through town to cell | Yes | L9–19: rope bound, full town walk rendered |
| Cell described (stone/brick, iron bars, dirt floor, clay pot, ~8x10ft) | Yes | L21–22: matches canon precisely |
| Phone rationing: airplane mode, low brightness | Yes | L37: both stated explicitly |
| Phone rationing: rushed, disorganized notes | Yes | L41–43: notes written in panic, unorganized |
| Selfie taken | Yes | L49–51: selfie scene, second photo added |
| What he CAN write: "ROME 98 AD??", water boils at 212, pi, quadratic formula | Yes | L41: all present with appropriate uncertainty |
| What he CANNOT recall: high-altitude boiling rule, third gunpowder ingredient | Yes | L41: "can't remember" and "???" both present |
| Phone note: "for whoever found my body" | Yes | L45: present verbatim in meaning |
| Cover story spine decided: far northern country, not the future | Yes | L85–87: both options worked through, decision made |
| Guards discover and examine phone (V2 addition) | Yes | L57–73: full scene, guard examines shirt fabric and phone |
| Optio arrives: junior officer rank mark, cuts rope, trades names | Yes | L93–101: soldier's build, shoulder mark, rope cut, name exchange |
| Ends on eating garum grain mush in the dark | Yes | L103: matches canon exactly |

Over-resolved beats: None. The cover-story decision in L85–87 works through both options methodically but stays on-surface (Daniel gets as far as "I am from far away and I am learned"; the word "Thule" is absent; the full story is deferred). This is correct per canon.

Unplanned beats: The guard examining the shirt weave before the phone (L57–62) is a small unscripted lead-in that works — it makes the phone discovery feel earned. Not a problem; adds texture. The "two photos on the phone now. The white building and my face. The proof and the proven." (L51) is an internal line that functions as a sub-section close — see Section 3f.

---

## 2. New V2 Arcs

- **Food arc** (`V2_FOOD_ARC.md`): Absent / N/A. The garum is present in the ending meal (L103: "sour-sharp reek of the fish sauce") and Daniel eats it without commentary. At this earliest chapter, no food-arc beat is required; Daniel's first exposure to garum is handled correctly as sensory, not reactive speech.
- **Prize/innovation arc** (`V2_PRIZE_INNOVATION.md`): N/A. Not required in ch02.
- **Children's education arc** (`V2_ULPIA_EDUCATION.md`): N/A. Not required in ch02.
- **Tech/bootstrapping** (`V2_TECH_DEEP_DIVE.md`): N/A. The phone is handled correctly as a dying resource, not a tech win. Daniel fails to recall the third gunpowder ingredient (???) — knowledge ceiling intact.
- **Atlantic/New World** (`V2_NEW_WORLD_CONTACT.md`): N/A. Not required in ch02.
- **Historical divergence** (`V2_HISTORICAL_IMPACT.md`): N/A. No divergence expected at this stage.

**V2 change notes items — status:**
- [DONE] Guards discover and examine the phone: scene fully present (L57–73). Guard examines shirt weave, spots phone in pocket, has Daniel display it, presses dark screen, turns it over, finds volume buttons, finds no response, hands it back. Approximately 350 words — slightly over the 200-word guidance, but the extra length earns its place (the volume-button detail and the guard's thumbnail along the seam are strong).
- [RESOLVED] Canon conflict on address/phone number (V2 change notes flagged line 43): the prose shows Daniel writing both his mom's number and home address (1147 Clearwater) successfully. The current `bible/08_canon_log.md` has been updated to list both in "What he COULD write." The conflict has been resolved by updating the canon log to match the prose. This is the cleanest fix. No further action needed.
- [DONE] Cleanliness preservation: no correctio, no future-vantage in V1 prose — see Section 3 for V2 status.

---

## 3. Prose Tics — Zero-Tolerance Sweep

### 3a. Correctio / "Not X, it's Y" (ZERO allowed)

- [X] Found: L7 — "Not to hurt. To feel it."

This is a clear "Not X. Y." correctio. The sentence cancels its premise before naming the action. The guard reaching for the shirt could be rendered without the construction. Suggested fix: "He reached out and took a fistful of my T-shirt at the shoulder, slowly, feeling the cotton between his thumb and two fingers." The phrase "Not to hurt" is also functioning as an explanatory interjection Daniel makes in retrospect — which is itself a mild throat-clear about his own interpretation of another person's action.

No other correctio instances found. The pattern does not recur.

**Ruling: ONE violation at L7. Blocking (zero-tolerance).**

Variants checked: "It was not X. It was Y." / "Not X. Y." / "It wasn't X, exactly." / "Not because X. Because Y." / "Less X than Y" / "Not just X, but Y" — no other instances found.

### 3b. Em dashes (ZERO allowed)

- [X] None found. Confirmed: zero em dashes in the chapter.

### 3c. Meta-disclaimers / throat-clearing (ZERO allowed)

- [X] Found: L25 — "I sat in the half-dark and shook for a while. I'm not going to pretend I didn't."

This is a direct instance of the banned "I will not pretend" construction (PROSE_PATTERNS_TO_AVOID §TIC V1). The sentence performs authorial honesty rather than trusting the prose. The shaking is already shown in the phrasing; the disclaimer is redundant and breaks immersion. Fix: delete "I'm not going to pretend I didn't." and let "I sat in the half-dark and shook for a while." stand alone. That sentence is already strong enough.

**Ruling: ONE violation at L25. Blocking (zero-tolerance).**

### 3d. Narrator stepping outside time / future-vantage (ZERO allowed)

Two candidates reviewed:

**L15 — "I have tried a lot of times since to put the town in order and I can't..."**
Ruling: PERMITTED. This is close-retrospect within the memoir frame. It reports what the narrator knows now (he has tried to reconstruct the sequence) without declaring the scene's significance or assigning weight from the future. It puts the reader inside Daniel's experience of confusion rather than announcing "this walk would prove important." PERMITTED under the style guide's close-retrospect exception.

**L15 — "...a thick rotten low note I'd later learn was the tannery and a sharp one I'd learn was the fish sauce they put on everything..."**
Ruling: PERMITTED. "I'd later learn" is retrospective identification, not dramatic-irony announcement. The narrator is reporting that he eventually understood what he was smelling; he is not declaring the importance of the moment. This is the permitted form per PROSE_PATTERNS_TO_AVOID §1.2: "Reports retrospective knowledge — fine, within the retrospective frame."

**L95 — "...which I took, correctly as it turned out, to mean he ranked them."**
Ruling: PERMITTED. Brief parenthetical confirmation that Daniel's read was right. No drama-irony weight assigned; just narrative bookkeeping.

- [X] No banned future-vantage found.

### 3e. "The way you / the way a man / the way a child" constructions (max 3 per chapter)

All instances (idiomatic uses excluded):

1. L15: "the lane filled up with people the way water fills a low spot" — rhetorical simile, counts.
2. L67: "the way you show something to a customs officer, or to a child" — rhetorical simile, counts.
3. L83: "the way I'd work any problem, badly and in circles" — rhetorical simile, counts.
4. L101: "the way I'd tried to say my own name to the other one and failed" — rhetorical simile, counts.

Excluded from count (idiomatic/directional, not simile): "all the way down" (L37), "all the way" (L53), "out of the way" (L17), "the way I meant it to" (L41 — directional).

- Count: 4 rhetorical simile uses
- [X] Over limit by 1 — one instance to cut.

Recommended cut: L83 "the way I'd work any problem, badly and in circles" is the weakest of the four — "badly and in circles" already does the work; the simile is redundant. Cut to: "I worked the problem badly and in circles, but I worked it."

### 3f. Wisdom-button scene/chapter endings (max 1 per chapter; aim 0 per 3 chapters)

Chapter ending: "...and I licked the bowl after, and I was not ashamed." — Image/action cut. The ending is on a concrete physical act and Daniel's interior state expressed without aphorism. Not a wisdom button. Strong.

Internal sub-section closings to audit:

- L51: "Two photos on the phone now. The white building and my face. The proof and the proven." — This is a wisdom button embedded mid-chapter as a scene close (immediately before the guard enters). "The proof and the proven" is extractable as a standalone epigram. It restates the meaning of the selfie-taking rather than trusting the selfie-taking scene. Flag for revision: trim to "Two photos on the phone now. The Colosseum and my face." and cut the aphoristic final clause.

- L87 (end of the cover-story reasoning section): "A man from the future is a horror or a god, and both of those die young." — This is a gnomic aphorism ending the Option 1 section. It is extractable as a standalone maxim. The reasoning in the paragraph does the work; this sentence announces the conclusion rather than letting it land. Flag for revision (not blocking since it is mid-chapter, but it is a wisdom button and this chapter has budget for 1 max, and the chapter ending is not a button — so technically within limit at 1 mid-chapter button).

- Chapter ending type: image/action — CLEAN.
- Scene-ending audit: no explicit scene breaks; chapter is continuous. Two sub-section closings flagged above.
- [X] Within limit (1 mid-chapter button at L87; chapter ending clean) — but recommend cutting L51's "The proof and the proven" clause as a non-blocking improvement.

### 3g. "Thing" as vague placeholder

Instances found (L7, L15, L17, L19, L27, L35, L37, L47, L85, L89):

Worst cases where a specific noun was available:
- L17: "I was the strange thing. I was the thing that was wrong in the picture." — "the strange thing" and "the thing that was wrong" both use "thing" as a placeholder. Suggest: "I was the wrong one in the picture. Every single person on that lane knew how the world worked and I was the only one who didn't." (Cuts both vague uses.)
- L27: "I did the thing I do, the only thing, I started counting." — "the thing I do" is characterful and earned here; "the only thing" immediately after is redundant. Minor: cut "the only thing" or compress to "I did what I always do: counted."
- L47: "Then I picked it back up, because there was one more thing." — "one more thing" is acceptable colloquial usage; not a specific noun was unavailable. Low priority.
- L85: "Not one thing on me proved it." — "thing" here is correct; "item" or "object" would be over-formal.

- [X] Two problematic uses (L17 worst case); no single use is fatal but L17 should be revised.

### 3h. Gnomic aphorism stacking (flag if 2+ in a single chapter)

Two gnomic closings identified:
- L51: "The proof and the proven." (sub-section close, mid-chapter)
- L87: "A man from the future is a horror or a god, and both of those die young." (end of Option 1 section)

- [X] Two gnomic aphorisms in one chapter — stacking threshold crossed. L51's clause should be cut (see 3f above); L87 can survive as the stronger of the two, but both cannot stay.

---

## 4. Secondary Tic Check

- **Polysyndeton runs** (max 1 per chapter): Multiple "and...and...and" runs throughout (L7, L15, L41, L87 are the densest). The chapter runs hot on polysyndeton — there are at least 4 sentences with 8+ "and" conjunctions. This is a voice choice consistent with Daniel's panic-state narration, and in ch02 the technique earns its place as a register of overwhelm. However, max-1-per-chapter rule is exceeded. The L41 run (22 ands — the writing-the-notes paragraph) is the strongest and most justified. The L15 and L87 runs are also strong. The L7 run (shirt-examination scene) could be condensed. Flag: over limit, but contextually defensible for an early chapter establishing Daniel's panic register. Recommend trimming L7 run.
  - Count: 4+ — [X] Flag: over limit. Recommend cutting the L7 polysyndeton run.

- **"Nobody tells you" formula** (max 1 per book): [X] Absent.

- **False-modesty rhythm** ("I was an idiot" then immediate sophistication): [X] Absent. Daniel calls himself "stupidly" at L11 ("I remember thinking, stupidly, with the clean idiot clarity of a person in shock, that I knew a better knot") — but this is followed by confirmation of the stupidity, not a demonstration of sophistication. The self-deprecation lands. Clean.

- **"Which is to say" pivot** (max 1 per 10 chapters): Count 0 — [X] OK.

- **"Looked at me"**: Count 3 (L17: "looked at my boots" — actually "looked at my boots" not at me; L23: "looked at me for a while"; L95: "looked at me with a directness"). Precise count: "looked at me" exactly = 2 (L23 and L95). L17 is "looked at my boots" — not a "looked at me" instance.
  - Count: 2 — [X] Within limit (max 2 per chapter). Exactly at limit.

- **One-sentence paragraphs**: Approximately 14 one-sentence paragraphs (excluding the chapter heading) out of ~51 content paragraphs = ~27%. Over the 15% limit.
  - Count: ~14 of ~51 = 27% — [X] Flag: over limit (max 15%). The strongest justifications: "They tied my hands." (L9), "Then they walked me down." (L13), "I had a clock." (L29), "Now the hard one." (L81). Weaker single-sentence paragraphs that can be absorbed: "Then I opened Notes and I started writing, fast, because the funny thing dying had scared me worse than the spears had." (L39 — absorb into previous or next paragraph); "Then I picked it back up, because there was one more thing." (L47 — absorb); "I took a picture of my own face." (L49 — absorb into the following paragraph).

- **Cycle of defeat**: [X] Not present as a structural tic. The chapter is primarily a survival/orientation chapter.

- **Ledger-as-catharsis**: [X] Absent.

- **Socratic echo**: [X] Absent. No secondary characters in substantive dialogue.

- **"Let it sit / let that hang"**: [X] Absent.

---

## 5. Canon Consistency

- **Daniel's age this chapter**: Expected 17 (98 AD per timeline). Stated: "I was alive and seventeen and scared in a cell outside Rome" (L51) — [X] Consistent.

- **Other character ages**: The optio is unnamed; no age stated — [X] N/A.

- **Dates / era**: Chapter era 98 AD — "ROME 98 AD??" written in notes (L41); "nineteen hundred years" referenced (L35) — [X] Consistent with timeline.

- **Tech state**: Phone at 98% on arrival (L33: "Ninety-eight percent"); drops to 96% after photo and brief use (L79: "battery count read ninety-six"). Canon says ~98% on arrival with ~50-100 hours of use — [X] Consistent. No anachronistic tech.

- **Named objects / relics**: Phone (present, handled correctly), rope binding (correct), clay chamber pot (referenced at L89 via implication: "a clay pot in the corner"), cell dimensions ~8x10 (L27: paced heel-to-toe — consistent), iron-banded plank door (L21: "a door of heavy planks with iron bands") — [X] All consistent with canon.

- **Phone rationing**: Canon requires airplane mode and low brightness to be started this chapter. Both confirmed (L37). Canon requires selfie (2nd photo after Colosseum). Confirmed (L49-51: "Two photos on the phone now") — [X] Consistent.

- **Address/phone number**: Canon log (current version) lists both in "What he COULD write." Prose has Daniel writing both successfully (L43: "My mom's number. Our address, 1147 Clearwater"). [X] Consistent with current canon. Note: V2 change notes flagged this as a conflict against an older canon log state; the canon log has since been updated to match the prose. No action required.

- **Cover story**: Canon specifies cover story spine decided this night; "Thule" word NOT yet introduced. Prose: cover story reached at L87 ("I am from very far away and I am learned"); Thule absent — [X] Consistent.

- **Optio**: Canon specifies unnamed, shoulder mark, cuts rope, trades names. Prose: shoulder mark "leather or braid" (L95), rope cut in two strokes (L99), name exchange at L101 — [X] Consistent. Optio remains unnamed — [X] Correct.

- **Ending beat**: Canon specifies ending on "Daniel eating garum-flavored grain mush with his fingers in the dark." Prose: L103 matches exactly, including garum smell, fingers, dark, licking bowl — [X] Consistent.

**New canon facts introduced this chapter** (log for coordinator):
- Daniel's home address confirmed in prose as "1147 Clearwater" (street + number only; city and zip written in Notes but not stated on the page).
- Battery at 96% after selfie + brief notes session. Canon log records phone "at 11%" at end of ch03 — the drain between ch02 and ch03 is heavy (signal hunting); this is consistent with the ch03 canon note.
- Guard shoulder mark: "something dark, leather or braid" — optio's insignia described without naming rank; canonical unnamed optio correctly preserved.

---

## 6. Voice

- **Daniel's voice**: Dry, self-deprecating, specific — [X] Yes, consistent throughout. Examples: "I cleared it" (L1 — undercut to a bar of not-dying); "The shirt is from a three-pack. It cost about six dollars." (L7 — precise, mundane, dark); "which is a stupid-looking way to measure a cell" (L27 — self-deprecation without apology); "airplane mode in 98 AD" (L37 — gallows humor exactly right). The voice fingerprint is well-established and does not drift toward earnestness or tour-guide.

- **Class-marked secondary voices**: The guards and the optio have no spoken dialogue that survives translation — this is correct (Daniel has no Latin yet). Their actions are rendered in Daniel's register. No smoothing problem. — [X] N/A.

- **No muted mutes**: No named secondary characters with established voices yet (Heras, Pamphilus, Naso not yet introduced). — [X] N/A.

- **Info-delivering monologue check**: No secondary character delivers any monologue. — [X] No flag.

- **Child dialogue**: No child characters. — [X] N/A.

- **Daniel competence**: He panics genuinely. He cannot recall saltpeter. He can't untie his own hands during arrest. He fumbles with the bowl when his wrists are tied. The cover story he reaches is incomplete ("the rest of it...came later and it came hard, with help"). — [X] Appropriate incompetence; no anachronistic competence. Note: one area of sharpness — the cover-story reasoning in L85–87 is very clean for a panicking teenager. It reads as Daniel-in-retrospect rationalizing the decision, which is consistent with the memoir frame. The reasoning is also stated as approximate ("I got as far as:") and the word "Thule" is absent. Acceptable.

---

## 7. Verdict

**REVISE**

### Blocking issues (must fix before next use)

1. **Correctio at L7** — "Not to hurt. To feel it." is a "Not X. Y." construction in violation of the zero-tolerance ban. Fix: rewrite as "He reached out and took a fistful of my T-shirt at the shoulder, slowly, feeling the cotton between his thumb and two fingers."

2. **Meta-disclaimer at L25** — "I'm not going to pretend I didn't." is a direct instance of the banned "I will not pretend" throat-clearing construction. Fix: delete the clause. The sentence "I sat in the half-dark and shook for a while." stands alone and needs no apology attached.

3. **"The way" over limit** — 4 rhetorical simile uses against a maximum of 3. Fix: cut L83 "the way I'd work any problem, badly and in circles" — revise to "I worked the problem badly and in circles, but I worked it."

### Revise items (should fix)

4. **One-sentence paragraphs at ~27%** (limit 15%) — Absorb at least 3-4 of the weaker single-sentence paragraphs: "Then I opened Notes..." (L39), "Then I picked it back up..." (L47), "I took a picture of my own face." (L49), "He looked at it a while longer." (L69). The strongest pivot-work single sentences should be preserved: "They tied my hands." "Then they walked me down." "I had a clock." "Now the hard one."

5. **Wisdom button at L51** — "The proof and the proven." ends the selfie sub-section as a portable aphorism. Cut the clause; end at "The Colosseum and my face." or similar concrete statement.

6. **Gnomic aphorism stacking** — With L51's clause cut (item 5 above), stacking drops to one (L87: "A man from the future is a horror or a god, and both of those die young.") which is within limit. L87 is the stronger of the two and can stay.

7. **Polysyndeton runs** — L7 (13 "and" conjunctions) and L15 (15 "and" conjunctions) are the densest alongside L41 (22 "and"s, the strongest and most justified). L7's run is the weakest contextually (the guard examining the shirt doesn't require exhaustion-register prose). Trim L7 to a shorter, more clipped rhythm to clear the max-1-per-chapter rule.

8. **"Thing" at L17** — "I was the strange thing. I was the thing that was wrong in the picture." Revise to cut the vague placeholder: "I was what was wrong in the picture."

### Notes for coordinator

- **Chapter numbering / outline alignment**: The prose `ch02.md` ("The Cell") contains content the `chapter_list.md` places in ch01 ("Waking Up"). The `chapter_list.md` ch02 brief ("The Map" — Heras, dirt map, numerals) corresponds to content in the canon log's ch03–ch04. The chapter has been split in the prose but not in the chapter_list.md outline. **Coordinator should update `chapter_list.md` to reflect the split:** the "The Cell" chapter (arrest through optio/food) is its own chapter; the chapter_list.md ch02 entry "The Map" (Heras/map/numerals) should become ch03, and subsequent chapter numbers shift accordingly — OR the prose files should be renumbered. This is a structural issue for the coordinator to resolve; it does not affect the quality of the prose itself.

- **Canon log update**: Address confirmed as "1147 Clearwater" — if city and zip are needed for continuity in later chapters, they should be logged when rendered on the page. Currently the prose says Daniel wrote them but does not state them aloud.

- **V2 phone-guard scene**: Present and well-executed. The guard finding the volume buttons and pressing them without result is a strong, specific detail — keep as-is. The shirt-texture setup before the phone is an unscripted addition that works; no need to cut.

- **Address/phone number conflict**: Fully resolved in current canon log. No further action.

- **Future chapters**: The optio who cuts the rope is unnamed and does not reappear until identified. The cover story is incomplete — "Thule" and the full backstory are planted as a deferred event ("that came later and it came hard, with help"). This is correctly handled.
