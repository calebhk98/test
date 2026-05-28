# V4 Audit Review and Cleanup Report
**Generated:** 2026-05-28  
**Purpose:** (1) Surface recurring/systemic craft issues for the V4 QA pass; (2) recommend stale analysis artifacts for deletion.  
**Scope:** All artifacts under `/home/user/test/book_v4/` except chapters/, bible/, core outline files, build scripts, manuscript/, research/, and writer/QA brief & rules files.

---

## PART 1 — RECURRING CRAFT ISSUES FOR THE V4 QA PASS

The following issues were flagged independently by multiple audit streams (blind critiques, line-prose close-reads, chapter analyses, QA V2 reviews, round summaries, and prose-tic audits). They are listed from most systemic to least. Each has a V4 QA watch note.

---

### ISSUE 1 (MOST SYSTEMIC): Paragraph-Ending and Chapter-Closing Aphorism / Wisdom-Button

**Prevalence:** Every analysis stream flags this independently. The prose_quality_summary counts ~20–25 restated-takeaway chapter endings and ~15+ gnomic aphoristic closings. The blind_lineprose_attribution_summary puts it at 2–4 aphorisms per chapter, spiking to 3–5 in mid-book. ROUND2_SUMMARY calls it "the calcified one" and reports "~55–60% of chapters end on extended interpretive reflection." ROUND3_SUMMARY says it was named separately by all three blind critiques, all three line-prose close-reads, the syntax/cadence audit, the show-vs-tell audit, the scene-architecture audit, and the voice-distinctiveness audit. The QA MASTER_SUMMARY_V2 confirms it survived into the QA-reviewed (V2) draft with worst offenders at ch41 (12 "the way" instances), ch42 (13), ch49 (13), ch50 (14).

**Character of the problem:** The narrator dramatizes a beat well, then adds a sentence or paragraph that restates its meaning in a portable, extractable maxim. "A man kneels, in the end, to whatever is holding the knife." (ch27); "burning a thing is only another way of keeping the smell of it." (ch29). By ch27–29 readers are trained to expect the aphorism; it absorbs the emotional hit instead of delivering it.

**Related sub-problems confirmed across multiple files:**
- The "I want to be exact / honest / plain / clear about X" metanarrative frame (12+ instances in ch12–22 alone, recurring through ch34–43)
- The "there is a [X] a [place] makes when…" templated chapter opening (back-to-back in ch23 and ch24)
- The aphorism + "because"-clause paradox opening (ch34, ch38, ch40, ch41)

**V4 QA watch:** Flag every chapter ending that closes on a present-tense generalization or portable maxim. Target: ≤1 wisdom-button per chapter, ≤1 per 3 chapters on average. Flag every opening that begins with a thesis statement rather than a scene. Check ch23–33 and ch40–50 ranges especially hard.

---

### ISSUE 2: The "Not X, It Was Y" Correctio Construction (Zero-Tolerance Rule Violation)

**Prevalence:** 25–37 documented instances across the book per ROUND2_SUMMARY and bad_prose_catalog.md. prose_quality_summary lists confirmed examples in ch08, ch11, ch18, ch27, ch38, ch47, ch50. The ch40 QA confirmed one survived into the V2 draft as a live blocker ("not as a complaint, as a figure" at L71). The QA MASTER_SUMMARY_V2 confirms additional instances in ch47 and ch48. AGENT_WRITER_BRIEF_V2 lists this as a zero-tolerance hard rule.

**Character of the problem:** The negation-as-definition pattern — "It was not a cheer. A cheer has words in it somewhere. This had no words." — is both stylistically banned (the style guide and PROSE_PATTERNS_TO_AVOID.md both prohibit it explicitly, with named examples) and a quantifiable AI prose marker. Each instance substitutes rhetorical pivot for direct statement.

**Related sub-tics confirmed across audits:**
- The "which is to say" pivot (TIC V12): named example "which is to say I lied a little with the truth" confirmed surviving verbatim in ch25 post-V2 revision
- Correctio-adjacent negation clusters: "Not it will do for me. Not the gods are content." (ch27); stacked negatives in ch24 phone section

**V4 QA watch:** Run a zero-tolerance sweep of every chapter for "it was not," "not X / it was Y," and "which is to say" constructions. The ch40 L71 instance was the most recently confirmed live violator; also verify ch47 and ch48 (QA flagged both). The "Not Spanish. / Not French." list-of-negatives in ch01 was flagged borderline; treat any leading negation before a positive statement as a candidate for revision.

---

### ISSUE 3: "The Way You / The Way a Man / The Way a Child" Sentence-Frame Overuse

**Prevalence:** 677 instances total in V1 (~13 per chapter). V2 imposed a 3-per-chapter cap. QA MASTER_SUMMARY_V2 confirmed the cap was consistently applied only in ch28 and ch33; worst post-V2 offenders measured: ch41 (12), ch42 (13), ch49 (13), ch50 (14), ch27 (6), ch32 (7), ch36 (6). The audit_prose_tics.md confirms the closing "the way you" construction appears in ch01 (at limit: 3), ch10 (2), ch25 (4, over limit), ch40 (2); and the book's final sentence deploys it ("looked west at the shore, the way you look at a thing you have only ever drawn"). PROSE_PATTERNS_TO_AVOID.md names it TIC V10, limit 3 per chapter.

**Character of the problem:** The frame was Daniel's default simile delivery mechanism in V1. At high frequency it becomes the book's audible fingerprint rather than a voice marker. The closing "the way you" in ch53 is flagged by audit_prose_tics.md as an unresolved decision point (intentional callback vs. unconsidered carryover).

**V4 QA watch:** Count "the way" instances per chapter mechanically. Any chapter over 3 is a revise. Focus hard on ch40–53 range where QA confirmed the heaviest accumulation post-V2. Also flag the ch53 final-line instance as requiring an explicit documented decision.

---

### ISSUE 4: One-Sentence Paragraph Overuse (Drama-Beat Exhaustion)

**Prevalence:** V1 measured at 26.1% overall (23.5% excluding dialogue). Literary fiction norm is 5–15%. V2 imposed a 15% cap. QA ch01 review found ch01 at ~30% (13 one-sentence paragraphs of ~43 total) and ruled this a blocker. ROUND3_SUMMARY notes that by ch50's death scene the device "consumes its own climax." The quantitative_metrics.md confirms the 26.9% figure. PROSE_PATTERNS_TO_AVOID.md sets the hard limit at 15% and names it a zero-tolerance cap in the per-chapter checklist.

**Character of the problem:** Fragmented paragraphs were used to create dramatic beats, but at ~26% they become the novel's default texture rather than a dramatic tool. The device loses its impact precisely where the book needs it most (the death scene, the grief moments).

**V4 QA watch:** Count single-sentence paragraphs per chapter as a percentage of total paragraphs. Flag any chapter exceeding 15%. Check ch01 (confirmed at 30%), and any emotionally climactic chapter (ch13, ch29, ch42, ch50) where the device is likely to cluster.

---

### ISSUE 5: Narrator Stepping Outside Time (Future-Vantage Annotation)

**Prevalence:** prose_quality_summary identifies ~7–8 BLOCKER instances in ch01–11 alone, with ch13 the densest single chapter. V2_CHAPTER_CHANGE_NOTES labels specific lines as blockers: "for a long time afterward I got him wrong" (ch04), doubled "I have never entirely stopped" (ch07:107/109), "he told me their names and I have them still" (ch13:47), "I knew with my whole body what was coming" (ch13:63). The outline/audit/audit_prose_tics.md finds the ch25 opening "I have held those two things together ever since" is the banned construction confirmed surviving in V2.

**Character of the problem:** The style guide's hard rule forbids narrator-arriving-from-the-future to telegraph significance. The permitted form is close-retrospect ("I can still see it") vs. the banned form ("I would later understand that this was the moment"). The distinction is violated at the named instances above, and the pattern recurs through ch46 ("would ever again…be paid by the empire" flagged in prose_quality_summary).

**V4 QA watch:** Flag every "I have never entirely stopped," "I have held since," "I would later," "I knew then that," "I would not again" construction. Distinguish from permitted close-retrospect. Check ch04, ch07, ch13, ch25, and ch46 specifically.

---

### ISSUE 6: Tricolon Crutch (Three-Beat Default Delivery)

**Prevalence:** Measured at 4–5 tricolons per chapter in blind_lineprose_attribution_summary, audible as machinery by ch02. Examples across every line-prose review: "The numbers were a trick. The creatures were witch-talk. The map was a curiosity in a drawer." prose_quality_summary calls it a MAJOR structural issue. The V2 refrain "Cheap. Mine. Undeniable." becomes so embedded that it is used as a chapter title (ch06) and re-stated at ch05:73, ch06:13, and ch06:89.

**Character of the problem:** Three-beat structures become the default unit for every inventory, summary, and moment of emphasis. At 4–5 per chapter they establish audible rhythm the reader anticipates, collapsing freshness into formula.

**V4 QA watch:** Flag passages where three consecutive short sentences or phrases deliver the same semantic unit. Target: thin by 50% from V1 baseline. Watch especially for closing tricolons (which compound with Issue 1). The "Cheap. Mine. Undeniable." refrain must not recur — check the global tracker's budget.

---

### ISSUE 7: Voice Sameness — Muted Lower-Class Characters / Universal Eloquence

**Prevalence:** ROUND3_SUMMARY describes this as the "everyone is intelligent/articulate AI failure on the competence/class/honesty axis." The voice_range_audit.md finds: no speaking character is genuinely dull; no class-marked rough/halting grammar for slaves, smiths, or soldiers; near-zero crude oaths despite soldiers and dockers; liars are all clever-strategic. The book "mutes" anyone who'd sound dumb or crude ("a man in the crowd shouted something I did not catch"). CHARACTER_VOICE_GUIDE.md establishes a 7-tier voice spectrum specifically to address this; it was not applied consistently through V2.

**Specific tracked deficits (from CHARACTER_VOICE_GUIDE.md and chapter analyses):**
- Pamphilus must have ≥4 spoken lines; QA flagged him present at the ch22 wedding but silent
- Naso must have ≥1 pre-accident line in cocky/dim register
- Crowd hecklers must be quoted (2–3 lines minimum) in at least one scene, not muted
- Celer must have ≥1 directly quoted crude oath

**V4 QA watch:** For every chapter containing Pamphilus, Naso, Davus, crowd scenes, or soldiers (Celer's unit), verify those characters speak in their correct register — fragmented, class-marked, occasionally crude — and are not muted by summary ("he said something I could not follow"). Check that Macer has exactly one crude oath instance (allowed: one, in genuine anger). Verify the CHARACTER_VOICE_GUIDE.md tier assignments chapter by chapter.

---

### ISSUE 8: Info-Delivering Dialogue (Thesis-Stating Monologues)

**Prevalence:** prose_quality_summary flags ch09:53–87 (Macer's full deal-structure monologue), ch22:95 (Marcia's perfectly-reasoned marriage-proposal speech), ch38:57–61 (Marcia's complete mortality/legacy thesis), ch42:51–75 (Heras's deathbed speech stating the theme aloud). misc_reviews_summary notes the "Daniel line → three-line interior analysis → next line → analysis" rhythm in imperial-audience chapters (ch17, ch35) reads as debating, not conversing. Trajan and Hadrian receive step-by-step tutorials before their first real questions.

**Character of the problem:** Characters deliver their full meaning in a structured monologue when the Hadrian dialogue (ch35–36) proves the book knows how to write evasive, testing, trap-setting speech. The contrast between what works (Hadrian) and what doesn't (Marcia's thesis speech, Macer's deal monologue) is documented in the prose_quality_summary as the standard to impose.

**V4 QA watch:** Flag any speech exceeding 4 consecutive uninterrupted lines for a single character. Check whether the speech deflects, tests, or traps — or states the thesis directly. The Hadrian model (ch35–36) is the benchmark: information forced out in fragments by specific imperial questions. The QA template (QA_CHAPTER_TEMPLATE.md) already flags "info-delivering monologue check" as a standard section; verify it's applied rigorously for ch09, ch22, ch38, ch42.

---

### ISSUE 9: Stacked Repetition / Context Re-Explanation

**Prevalence:** prose_quality_summary documents: forearm burn-scar re-explained 7 times in ch06–ch11 (reader has it by ch08); "Cheap. Mine. Undeniable." refrain stated 4 times across ch05–ch06; Daniel's failing eyes re-stated 6 times in ch38–43; water clock's "lying time" re-established 5 times in ch23–ch31; "the numbers stayed where I set them / had no far side" exact refrain in ch34, ch35, ch36. V2_GLOBAL_TRACKER.md documents Macer's ring-turning gesture at 18 occurrences (cap: 3).

**Character of the problem:** Each re-explanation was originally appropriate context-setting; accumulated across chapters it signals distrust of the reader's memory and drains the motif of its earned weight.

**V4 QA watch:** Check the V2_GLOBAL_TRACKER.md budget for Macer's ring gesture (keep: ch09, ch31, ch47 only — CUT all others). Track the burn-scar: should not appear after ch08 re-establishment. Failing-eyes: should not appear after first ch38 introduction. "Numbers stayed" refrain: must not appear in ch34–36 (flagged as a global prose note in V2_CHAPTER_CHANGE_NOTES). Any repeated motif appearing more than 3 times in a 10-chapter range warrants flagging.

---

### ISSUE 10: Frozen-Epiphany / Protagonist-Stops-and-Stares Pattern

**Prevalence:** Named TIC V13 in PROSE_PATTERNS_TO_AVOID.md. The named example "I stood there in my own yard and looked at a fourteen-year-old slave who had taught herself in a week…" confirmed surviving verbatim in ch10 despite being the exact banned-example sentence in the tics document (audit_prose_tics.md confirmed V2 missed it). The ch01 Colosseum moment is also a frozen epiphany (earned on first use; template-setting). The ch25 opening is additionally a frozen-epiphany candidate.

**Character of the problem:** The protagonist physically stops, faces a revelation, and narrates the understanding arriving complete. Real shock disrupts cognition; this pattern shows understanding arriving too clean and too whole (blind_lineprose_attribution_summary: "the narrator is too consistently self-aware — real shock disrupts cognition, this shock only disrupts it at the seams").

**V4 QA watch:** Flag any "I stood/sat/stopped and [looked/felt/understood]" construction that is followed by a fully-formed analytical realization. Apply PROSE_PATTERNS_TO_AVOID.md TIC V13 check. The ch10 instance ("I stood there in my own yard and looked at a fourteen-year-old slave") was missed by V2; confirm it is resolved in V3.

---

### ISSUE 11: Tech Hand-Waving / "Cycle of Defeat" Template

**Prevalence:** audit_prose_tics.md (TIC V16) shows the Cycle of Defeat (demonstrate → works imperfectly → iterates without resolution → depression → pivot) still running in the steam pump, pendulum clock, and steel arcs despite the fix instruction. ROUND3_SUMMARY and ROUND4_SUMMARY confirm the steel-wall is the book's greatest structural strength but that 4–5 zero-cost wins (rag paper, heliocentrism teaching, Volta pile, water-wheel textile mechanization, glider) were left on the table. QA MASTER_SUMMARY_V2 shows the Volta pile was still absent from ch24–ch31 (8 chapters past its required 110 AD milestone).

**Character of the problem:** The legitimate steel/temperature wall does real work; but the absence of rag paper (existed in Han China 105 AD), heliocentrism as a taught subject (zero materials), and the Volta pile (zinc/copper/brine, no precision metal) reads as over-conservative hedging rather than genuine constraint. The Cycle of Defeat pattern makes all tech arcs structurally identical.

**V4 QA watch:** Confirm whether V3 added: (a) rag paper introduction at the press by Phase B/C; (b) heliocentrism stated aloud in educated company with social consequences; (c) Volta pile demonstrated to Heras by ~110 AD. If any are still absent, they remain the book's most exposed easy-win omissions. For the Cycle of Defeat: verify at least two tech arcs do NOT follow the fail-iterate-despair pattern (gambling/sportsbook and spinning wheel were meant to be the exceptions).

---

### ISSUE 12: Continuity / Age Arithmetic Errors

**Prevalence:** misc_reviews_summary documents four confirmed continuity errors: Tyche called "fourteen" in ch12 when she should be ~16; Lucanus called "five" in ch31 when he should be ~6; Pamphilus's collar described as "five years gone" in ch31 when it should be ~12–13 years; Heras says the balloon "convinced Macer forty years ago" in ch42 when the actual elapsed time is ~33–34 years. QA MASTER_SUMMARY_V2 adds: Lucanus described as "twelve" near birth in ch27, and stated "five" when he should be 7–8 in ch32. chapters_characters_summary flags antagonists' ages off by 6–7 years (Scaeva, Crispus, Vibenius). The ch32 internal self-contradiction ("nineteen years" L49, L65 vs. "twenty years gone" L91) is also noted.

**V4 QA watch:** The fresh per-chapter QA run should check every named age and every elapsed-time statement against bible/03_timeline.md. Priority targets: any chapter mentioning Tyche's age, Lucanus's age (he appears from ch26 onward), Pamphilus's collar, Heras's elapsed-time references to early events, and the antagonist ages in any chapter post-ch25.

---

## PART 2 — CLEANUP RECOMMENDATION

### Framework

The context is: V3 is a full 53-chapter rewrite of the chapters in `book_v4/chapters/`, implementing the fixes documented in V2 reference files. A fresh per-chapter V4 QA is about to be generated. Files are stale if: (a) they analyzed V1 or V2 prose that has since been rewritten, (b) their findings were absorbed into the V2 reference documents (which are the current authoritative brief), or (c) they describe problems the V3 rewrite was designed to address (and the V4 QA will independently verify whether they succeeded).

Files are NOT stale if: they still describe active architectural requirements, live story gaps, or standing prose rules — even if the rewrite was supposed to address them — because the V4 QA will need to check whether the rewrite actually did so.

---

### DELETE LIST

These files describe V1/V2-draft problems absorbed into V2 reference documents, or are superseded by the V3 rewrite + forthcoming V4 QA. They add noise without adding signal.

#### Group A: `chapter_analysis/` — All 53 files

**Reason:** These are V2 compliance checklists run against V1 chapter prose. They document which V1 patterns survived into V2 and list blocker-vs-preserve items for the V2 writing agent. V3 has now rewritten all 53 chapters. The V4 QA will generate fresh per-chapter analysis against the actual V3 text. Keeping these files creates a false paper trail (they say "MUST FIX" for problems that may now be resolved, or may describe entirely absent content that V3 invented from scratch). Their findings were already synthesized into V2_CHAPTER_CHANGE_NOTES.md, PROSE_PATTERNS_TO_AVOID.md, and V2_MASTER_CONTEXT.md — which remain.

**Files (53 total, ~704 KB):**
```
/home/user/test/book_v4/chapter_analysis/ch01_analysis.md
/home/user/test/book_v4/chapter_analysis/ch02_analysis.md
[... ch03 through ch53 — all 53 files]
/home/user/test/book_v4/chapter_analysis/ch53_analysis.md
```

---

#### Group B: `review/` tree — All 49 files

**Reason:** These are the Round 2–4 craft audits and specialist reviews run against V1 prose. Their findings were synthesized into the six `summaries/` files and then further collapsed into V2_MASTER_CONTEXT.md, AGENT_WRITER_BRIEF_V2.md, and PROSE_PATTERNS_TO_AVOID.md. The round summaries (ROUND2_SUMMARY.md, ROUND3_SUMMARY.md, ROUND4_SUMMARY.md) are the distillations that actually matter; the underlying detail files are now two drafts stale. The V3 rewrite was designed to address everything these files document; the V4 QA will verify the results independently.

**Specific files and one-line reasons:**

| File | Reason |
|------|--------|
| `review/ROUND2_SUMMARY.md` | Synthesis of V1 audits; findings absorbed into V2_MASTER_CONTEXT.md and summaries/ |
| `review/ROUND3_SUMMARY.md` | Same — V1 craft audits synthesized and superseded |
| `review/ROUND4_SUMMARY.md` | Same — V1 tech rebuttal findings absorbed into V2_TECH_DEEP_DIVE.md |
| `review/bad_prose_catalog.md` | V1 35-pattern catalog; absorbed into PROSE_PATTERNS_TO_AVOID.md |
| `review/bootstrapping_critique.md` | V1 tech critique; absorbed into V2_TECH_DEEP_DIVE.md |
| `review/cold_reader_ch1-3.md` | V1 cold-reader impressions; findings summarized in misc_reviews_summary.md |
| `review/continuity_naming_audit.md` | V1 continuity errors; fixed list in misc_reviews_summary.md and V2_CHAPTER_CHANGE_NOTES |
| `review/dialogue_blind_test_results.md` | V1 attribution test; findings in blind_lineprose_attribution_summary.md |
| `review/dialogue_distinctiveness.md` | V1 voice analysis; absorbed into CHARACTER_VOICE_GUIDE.md |
| `review/dialogue_mechanics_audit.md` | V1 dialogue mechanics; absorbed into misc_reviews_summary.md |
| `review/gesture_repetition_audit.md` | V1 gesture-count audit; absorbed into V2_GLOBAL_TRACKER.md |
| `review/language_handling.md` | V1 Latin/Greek language audit; findings in ROUND4_SUMMARY.md |
| `review/latent_knowledge_tech.md` | V1 tech-knowledge audit; absorbed into V2_DANIEL_COGNITIVE_EDGE.md |
| `review/market_audit.md` | V1 market positioning; findings in misc_reviews_summary.md |
| `review/obvious_tech_gaps.md` | V1 tech gaps; absorbed into V2_TECH_DEEP_DIVE.md and V2_STORY_GAP_AUDIT.md |
| `review/pacing_map.md` | V1 pacing map; findings in threads_pacing_predict_summary.md |
| `review/preachiness_audit.md` | V1 preachiness check; verdict Clean — absorbed into misc_reviews_summary.md |
| `review/predictability_audit.md` | V1 predictability scoring; absorbed into threads_pacing_predict_summary.md |
| `review/quantitative_metrics.md` | V1 Zipf/paragraph stats; absorbed into misc_reviews_summary.md |
| `review/rome_divergence_diff.md` | V1 divergence analysis; superseded by V2_HISTORICAL_IMPACT.md |
| `review/scene_architecture_audit.md` | V1 scene-ending audit; absorbed into prose_quality_summary.md |
| `review/showing_telling_audit.md` | V1 show-vs-tell audit; findings in ROUND3_SUMMARY.md |
| `review/syntax_cadence_audit.md` | V1 syntax/cadence metrics; absorbed into blind_lineprose_attribution_summary.md |
| `review/tech_plausibility_audit.md` | V1 tech audit; absorbed into history_tech_qa_summary.md |
| `review/tech_plausibility_rebuttal.md` | V1 tech rebuttal; absorbed into history_tech_qa_summary.md and ROUND4_SUMMARY.md |
| `review/teen_knowledge_and_change.md` | V1 teen-knowledge audit; absorbed into misc_reviews_summary.md |
| `review/thread_audit.md` | V1 thread health; absorbed into threads_pacing_predict_summary.md |
| `review/voice_audit.md` | V1 voice consistency; absorbed into blind_lineprose_attribution_summary.md |
| `review/voice_range_audit.md` | V1 voice-range critique; absorbed into CHARACTER_VOICE_GUIDE.md |
| `review/parts/attribution_guesses.md` | V1 attribution quiz responses; absorbed into blind_lineprose_attribution_summary.md |
| `review/parts/attribution_key.md` | V1 quiz answer key; absorbed into blind_lineprose_attribution_summary.md |
| `review/parts/attribution_quiz.md` | V1 quiz questions; absorbed into blind_lineprose_attribution_summary.md |
| `review/parts/blind_critique_ch01-10.md` | V1 blind critique; absorbed into blind_lineprose_attribution_summary.md |
| `review/parts/blind_critique_ch25-34.md` | V1 blind critique; absorbed into blind_lineprose_attribution_summary.md |
| `review/parts/blind_critique_ch44-53.md` | V1 blind critique; absorbed into blind_lineprose_attribution_summary.md |
| `review/parts/lineprose_ch01-06.md` | V1 line-prose close-read; absorbed into prose_quality_summary.md |
| `review/parts/lineprose_ch24-29.md` | V1 line-prose close-read; absorbed into prose_quality_summary.md |
| `review/parts/lineprose_ch47-53.md` | V1 line-prose close-read; absorbed into prose_quality_summary.md |
| `review/parts/predict_ch06.md` | V1 chapter-6 predictability test; absorbed into threads_pacing_predict_summary.md |
| `review/parts/predict_ch13.md` | V1 chapter-13 predictability test; absorbed into threads_pacing_predict_summary.md |
| `review/parts/predict_ch21.md` | V1 chapter-21 predictability test; absorbed into threads_pacing_predict_summary.md |
| `review/parts/predict_ch36.md` | V1 chapter-36 predictability test; absorbed into threads_pacing_predict_summary.md |
| `review/parts/thread_ch01-18.md` | V1 thread audit part 1; absorbed into threads_pacing_predict_summary.md |
| `review/parts/thread_ch19-36.md` | V1 thread audit part 2; absorbed into threads_pacing_predict_summary.md |
| `review/parts/thread_ch37-53.md` | V1 thread audit part 3; absorbed into threads_pacing_predict_summary.md |
| `review/parts/voice_apollodorus.md` | V1 voice study; absorbed into CHARACTER_VOICE_GUIDE.md |
| `review/parts/voice_heras.md` | V1 voice study; absorbed into CHARACTER_VOICE_GUIDE.md |
| `review/parts/voice_macer.md` | V1 voice study; absorbed into CHARACTER_VOICE_GUIDE.md |
| `review/parts/voice_tyche.md` | V1 voice study; absorbed into CHARACTER_VOICE_GUIDE.md |

**Total: 49 files, ~920 KB**

---

#### Group C: `summaries/` — All 6 files

**Reason:** These are synthesis documents that collapsed the Round 2–4 review/ tree into navigable summaries. Their primary purpose was to serve V2 writing agents as a compact alternative to reading 87 review files. That purpose is now fulfilled: V2_MASTER_CONTEXT.md absorbed the essential content from all six summaries (V2_DIFF_REPORT.md explicitly describes this in its summaries/ section). The V4 QA agents are working from V2_MASTER_CONTEXT.md, PROSE_PATTERNS_TO_AVOID.md, AGENT_QA_BRIEF.md, and QA_BIGPICTURE.md — not from these summary files. Keeping them adds a stale middle layer between the review files (stale) and the active reference documents (current).

**Files (6 total, ~76 KB):**
```
/home/user/test/book_v4/summaries/blind_lineprose_attribution_summary.md
/home/user/test/book_v4/summaries/chapters_characters_summary.md
/home/user/test/book_v4/summaries/history_tech_qa_summary.md
/home/user/test/book_v4/summaries/misc_reviews_summary.md
/home/user/test/book_v4/summaries/prose_quality_summary.md
/home/user/test/book_v4/summaries/threads_pacing_predict_summary.md
```

---

#### Group D: `outline/audit/` directory — All 14 files

**Reason:** These were 10 parallel outline-vs-planning-document audits run against the V2 outline prior to the V3 chapter rewrite. Their findings (the MASTER_AUDIT_SUMMARY.md lists all discrepancies as CRITICAL, HIGH, or MEDIUM priority) were the instruction set for the V3 rewriting agents. The V3 chapters have now been written. The V4 QA will verify whether V3 addressed these gaps in the actual prose. The outline audit files now describe discrepancies between the V2 outline and the V2 planning documents — two layers removed from the current V3 chapters. Their CRITICAL items are captured in QA_BIGPICTURE.md and the active V2 reference docs.

**Files (14 total, ~388 KB):**
```
/home/user/test/book_v4/outline/audit/MASTER_AUDIT_SUMMARY.md
/home/user/test/book_v4/outline/audit/audit_atlantic_crossing.md
/home/user/test/book_v4/outline/audit/audit_finances_prize.md
/home/user/test/book_v4/outline/audit/audit_flight_vow.md
/home/user/test/book_v4/outline/audit/audit_food_arc.md
/home/user/test/book_v4/outline/audit/audit_games_gambling.md
/home/user/test/book_v4/outline/audit/audit_historical_divergence.md
/home/user/test/book_v4/outline/audit/audit_new_gaps.md
/home/user/test/book_v4/outline/audit/audit_plague_newworld_timing.md
/home/user/test/book_v4/outline/audit/audit_prose_tics.md
/home/user/test/book_v4/outline/audit/audit_rome_fall_prevention.md
/home/user/test/book_v4/outline/audit/audit_tech_timeline.md
/home/user/test/book_v4/outline/audit/audit_ulpia_education.md
/home/user/test/book_v4/outline/audit/audit_writing_contest.md
```

---

#### Group E: `outline/audit_*.md` (top-level) — 5 files

**Reason:** Earlier generation of outline audit files (predating the `outline/audit/` subdirectory). The `outline/audit/` directory superseded these with more detailed 10-agent versions. These are now two generations stale.

**Files (5 total, ~108 KB):**
```
/home/user/test/book_v4/outline/audit_atlantic_food.md
/home/user/test/book_v4/outline/audit_cards_games.md
/home/user/test/book_v4/outline/audit_characters_arcs.md
/home/user/test/book_v4/outline/audit_contest.md
/home/user/test/book_v4/outline/audit_tech_timeline.md
```

---

#### Group F: `outline/OUTLINE_AUDIT_V1.md`

**Reason:** The first-generation outline audit, predating both the `audit_*.md` top-level files and the `outline/audit/` subdirectory. Entirely superseded by subsequent audit generations and the V2 rewrite.

**File (1 file, ~small):**
```
/home/user/test/book_v4/outline/OUTLINE_AUDIT_V1.md
```

---

#### Group G: `qa/` directory — All 21 files

**Reason:** These 20 per-chapter QA files + 1 master summary reviewed the V2 draft chapters (pre-V3 rewrite). The MASTER_QA_SUMMARY_V2.md explicitly states: "The V2 chapters were edited for prose quality (removing correctio, em dashes, throat-clearing, future-vantage violations). They were NOT updated to reflect the major plot changes mandated by the V2 reference files." The V4 fresh QA run will supersede these entirely — it will run against the actual V3 chapters, not the V2 draft these files reviewed. Keeping qa/ creates a misleading artifact set that documents the state of a draft that no longer exists.

**Caution note:** The MASTER_QA_SUMMARY_V2.md does contain the important COORDINATOR DECISION flag about the Atlantic crossing timeline (V2 reference files vs. V1 chapter model). If this decision has not yet been formally resolved, extract that decision point into the QA_BIGPICTURE.md or another active document before deleting. The Atlantic crossing flag appears in QA_BIGPICTURE.md already if that document was updated. Verify before deleting.

**Files (21 total, ~848 KB):**
```
/home/user/test/book_v4/qa/MASTER_QA_SUMMARY_V2.md
/home/user/test/book_v4/qa/ch01_review_v2.md
/home/user/test/book_v4/qa/ch02_review_v2.md
/home/user/test/book_v4/qa/ch03_review_v2.md
/home/user/test/book_v4/qa/ch04_review_v2.md
/home/user/test/book_v4/qa/ch05_review_v2.md
/home/user/test/book_v4/qa/ch06_ch07_review_v2.md
/home/user/test/book_v4/qa/ch08_ch09_review_v2.md
/home/user/test/book_v4/qa/ch10_ch11_review_v2.md
/home/user/test/book_v4/qa/ch12_ch13_review_v2.md
/home/user/test/book_v4/qa/ch14_ch15_review_v2.md
/home/user/test/book_v4/qa/ch16_ch17_review_v2.md
/home/user/test/book_v4/qa/ch18_ch19_review_v2.md
/home/user/test/book_v4/qa/ch20_ch21_review_v2.md
/home/user/test/book_v4/qa/ch22_ch23_review_v2.md
/home/user/test/book_v4/qa/ch24_ch25_review_v2.md
/home/user/test/book_v4/qa/ch26_ch31_review_v2.md
/home/user/test/book_v4/qa/ch32_ch37_review_v2.md
/home/user/test/book_v4/qa/ch38_ch43_review_v2.md
/home/user/test/book_v4/qa/ch44_ch48_review_v2.md
/home/user/test/book_v4/qa/ch49_ch53_review_v2.md
```

---

#### Group H: Selective `V2_*.md` top-level docs — 3 files

These three are stale for specific documented reasons. The remaining 12 V2_*.md files are KEPT (see below).

| File | Reason for deletion |
|------|---------------------|
| `V2_DIFF_REPORT.md` | Documents what was new/changed in the V2 file set vs. V1. That transition is complete; the V2 files are now the baseline. Readers of the V3/V4 work do not need a V1→V2 diff; they need the current V2 reference docs directly. |
| `V2_CHAPTER_CHANGE_NOTES.md` | Per-chapter V2 revision instructions written for V2 writing agents rewriting V1 chapters. V3 has now rewritten all 53 chapters. The V4 QA does not use these per-chapter directives — it uses QA_CHAPTER_TEMPLATE.md and the V3 chapters themselves. The active standing rules in V2_CHAPTER_CHANGE_NOTES (global prose notes, global tic budgets) have been absorbed into PROSE_PATTERNS_TO_AVOID.md and V2_GLOBAL_TRACKER.md. |
| `V2_STORY_GAP_AUDIT.md` | The per-chapter story-gap checklist for V2 writing agents. At 700+ lines, it mapped every missing story beat in V1 to the chapters responsible for adding it. V3 has now implemented (or attempted to implement) those beats. The V4 QA will assess whether they landed. This document's job is done; QA_BIGPICTURE.md carries the standing story-architecture expectations forward. |

**Files (3 total, ~162 KB):**
```
/home/user/test/book_v4/V2_DIFF_REPORT.md
/home/user/test/book_v4/V2_CHAPTER_CHANGE_NOTES.md
/home/user/test/book_v4/V2_STORY_GAP_AUDIT.md
```

---

### KEEP LIST

The following files should be retained, with reasons.

#### Core Outline and Structure (mandatory keep per task rules)
- `outline/master_outline.md` — Active story architecture
- `outline/V2_REVISED_OUTLINE.md` — V2 chapter-by-chapter brief; the current authoritative chapter guide
- `outline/updated_ch01_18.md`, `updated_ch19_36.md`, `updated_ch37_53.md` — Current chapter briefs for the 53 chapters

#### Active V2 Reference Documents (mandatory working set for V4 QA)
- `V2_MASTER_CONTEXT.md` — The single-document V2 brief; all QA agents need this
- `V2_AGENT_WRITER_BRIEF_V2.md` → (file is `AGENT_WRITER_BRIEF_V2.md`) — V2 writing rules
- `V2_GLOBAL_TRACKER.md` — Macer ring / burn-scar / refrain global budget; V4 QA must check these
- `V2_STORY_PLOT_NOTES.md` — Story architecture requirements (Atlantic crossing decision lives here)
- `V2_HISTORICAL_IMPACT.md` — Divergence timeline and "Rome in 155 AD" reference; needed by V4 QA
- `V2_TECH_DEEP_DIVE.md` — Engineering feasibility reference for tech scenes
- `V2_DANIEL_COGNITIVE_EDGE.md` — Daniel's knowledge limits; prevents V4 QA from incorrectly flagging calibrated ignorance as errors
- `V2_DANIEL_FINANCES.md` — Financial reference for all transactions; V4 QA will check wealth-phase consistency
- `V2_NEW_WORLD_CONTACT.md` — Atlantic/New World epidemiology; needed for ch28–ch36 and ch53 QA
- `V2_CONTEST_STRUCTURE.md` — Contest arc mechanics; needed to verify V3 beats are present
- `V2_FOOD_ARC.md` — Food arc beat assignments; needed to verify V3 food thread
- `V2_PRIZE_INNOVATION.md` — Prize model and institutional innovations; needed to verify V3 coverage
- `V2_ULPIA_EDUCATION.md` — Ulpia/Lucanus education arc; needed for V4 QA of ch38–50

#### Active Prose Rules (mandatory working set)
- `PROSE_PATTERNS_TO_AVOID.md` — The mechanical pre-flight checklist; every QA chapter must run against this
- `AGENT_RULES.md` — Standing agent rules
- `AGENT_QA_BRIEF.md` — QA agent standing brief
- `AGENT_WRITER_BRIEF.md` — V1 writer brief (historical reference; keep in case of rollback need)
- `AGENT_WRITER_BRIEF_V2.md` — V2 writer brief; current active version
- `QA_BIGPICTURE.md` — Big-picture QA expectations
- `QA_CHAPTER_TEMPLATE.md` — Per-chapter QA template; the V4 fresh QA run uses this
- `ABOUT.md`, `README.md` — Project documentation

#### Bible (mandatory keep per task rules)
- All files in `bible/` — canonical world and character reference

#### Research (mandatory keep per task rules)
- All files in `research/`

---

### DELETE SUMMARY TABLE

| Group | Count | Size | Reason |
|-------|-------|------|--------|
| A: chapter_analysis/ (all 53) | 53 files | ~704 KB | V1/V2 compliance checklists, superseded by V3 rewrite + V4 QA |
| B: review/ tree (all 49) | 49 files | ~920 KB | V1 craft audits, absorbed into summaries/ then V2 reference docs |
| C: summaries/ (all 6) | 6 files | ~76 KB | Middle-layer syntheses absorbed into V2_MASTER_CONTEXT.md |
| D: outline/audit/ (all 14) | 14 files | ~388 KB | V2-outline-vs-planning audits; V3 has implemented; V4 QA verifies |
| E: outline/audit_*.md (5 top-level) | 5 files | ~108 KB | Superseded by outline/audit/ subdirectory |
| F: outline/OUTLINE_AUDIT_V1.md | 1 file | ~small | First-generation audit, two generations stale |
| G: qa/ (all 21) | 21 files | ~848 KB | V2-draft QA; superseded by V4 fresh QA run |
| H: V2_DIFF_REPORT.md, V2_CHAPTER_CHANGE_NOTES.md, V2_STORY_GAP_AUDIT.md | 3 files | ~162 KB | Transition docs: job done; V4 QA does not need them |
| **TOTAL** | **152 files** | **~3.2 MB** | |

---

### CONDITIONAL DELETES (Verify Before Acting)

Before deleting the `qa/` group, confirm that the Atlantic crossing coordinator decision (V1 "no crossing in Daniel's lifetime" vs. V2 "crossing by 112–115 AD") has been formally resolved in either QA_BIGPICTURE.md or the active outline files. The MASTER_QA_SUMMARY_V2.md is the only document that explicitly names this as an open COORDINATOR DECISION. If it is still unresolved, extract the decision point into QA_BIGPICTURE.md before deleting.

---

*Report written: 2026-05-28. Do not commit or push. V4 QA agent should read PART 1 before generating per-chapter analyses.*
