# V4 File Consistency Audit -- The Long Way Home

**Audit date:** 2026-05-28
**Scope:** All files under `/home/user/test/book_v4/` only.
**Ground truth:** 53 prose chapters in `chapters/`; canon log CHARACTER AGE ANCHOR (authoritative).
**Severity key:**
- CRITICAL -- directly breaks the story, contradicts every other authoritative source, or produces an impossible age/date on the page.
- MAJOR -- significant drift between two or more planning documents that must be resolved before drafting the affected chapters.
- MINOR -- small inconsistency, low story impact, easily corrected.

---

## CRITICAL ISSUES (5)

---

### C-1: Lucanus birth year -- 02_characters.md contradicts canon log anchor and ch26 prose

**Where:**
- `bible/02_characters.md` line 256: "Born ~108 AD to Daniel and Marcia."
- `bible/08_canon_log.md` CHARACTER AGE ANCHOR (bottom): "Lucanus: named on day 9 after birth, ch26 (~112 AD) -> born ~112 AD."
- `chapters/ch26.md` opens: "On the ninth day we named him Lucanus" -- ch26 is set at the Trajan's Forum dedication (~112-113 AD). This is ground truth.
- `outline/V2_REVISED_OUTLINE.md` CROSS-CHAPTER CONTINUITY: "Lucanus birth ~108-111 AD" -- also wrong.
- `outline/V2_REVISED_OUTLINE.md` ch32 fix note: "Lucanus age: stated 'five' -> should be 7-8 (born ~110-111 AD, chapter spring 118 AD)." -- If ch32 is 118 AD and Lucanus is 7-8, that yields born ~110-111, not 108 and not 112.
- `outline/updated_ch19_36.md` ch34 note: "Lucanus (Daniel's son, born ~108 AD, approximately 10-14 years old in this chapter's range [118-122 AD])." -- inconsistent range; if 10-14 in 118-122, that implies born ~104-112.

**What conflicts:** The ground truth (ch26 prose, set ~112-113 AD) and the canon log anchor (~112 AD) agree. The characters file says ~108 AD. The V2 outline says ~108-111 AD. The ch32 fix note implies ~110-111 AD.

**Why Critical:** Every age computation for Lucanus downstream depends on this anchor. At ch37 (~122-124 AD) he is described as "~10 years old" -- consistent with birth ~112-114, not ~108 (which would make him ~14-16 there).

**Recommended resolution:** Accept the canon log anchor ("born ~112 AD") as authoritative, which is confirmed by the ch26 prose. Update every occurrence of "108" or "~108-111" in outline files.

**Action taken:** FIXED in `bible/02_characters.md` -- changed "Born ~108 AD" to "Born ~112 AD". Remaining occurrences in `outline/V2_REVISED_OUTLINE.md` (lines 440, 279) and `outline/updated_ch19_36.md` (ch34 note) are flagged but left unfixed because the correction involves connected narrative age calculations that require author review (the ch32 note implies ~110-111, which is a different disagreement).

---

### C-2: Lucanus birth year internal conflict within V2_REVISED_OUTLINE

**Where:**
- `outline/V2_REVISED_OUTLINE.md` line 440: "Lucanus birth ~108-111 AD."
- `outline/V2_REVISED_OUTLINE.md` line 279 (ch32 fix note): "Lucanus age: stated 'five' -> should be 7-8 (born ~110-111 AD, chapter spring 118 AD)."

**What conflicts:** The continuity anchor says "~108-111 AD" but the ch32 correction math yields "~110-111 AD" as the consistent figure. These two are not in conflict with each other (110-111 is within 108-111), but both conflict with the canon log and ch26 ground truth (~112 AD). The fact that the ch32 correction yields "7-8 years old in 118 AD" implies born ~110-111, which is not ~112. Accepting the canon log anchor (~112) means Lucanus would be ~6 in spring 118 AD, not 7-8.

**Recommended resolution:** Author must decide: is the canon log anchor (~112 AD, based on ch26 set at Trajan's Forum dedication ~112-113 AD) correct, or is the ch32 age-7-8 figure correct? These cannot both be true. If born ~112, he is ~6 at spring 118. If born ~110-111, ch26 cannot be the naming chapter (ch26 is set ~112-113 AD, when he would already be 1-3 years old, not newborn). The ch26 prose opens with the naming ("On the ninth day we named him Lucanus") at the same time as the Forum dedication. The ch26 prose is the authoritative ground truth: Lucanus was born approximately when Trajan's Forum was dedicated, ~112-113 AD.

**Recommended fix:** Change ch32's fix note to say "born ~112 AD, chapter spring 118 AD -> ~6 years old" and accept that the "five" in V1 ch32 was close to correct. Flag to author before revising the ch32 prose.

**Action taken:** FLAGGED. Not fixed (structural author decision required).

---

### C-3: Part structure numbering -- three incompatible systems in use simultaneously

**Where:**
- `bible/08_canon_log.md` lines 817, 844-850: "[ch31] CLOSES PART IV... [ch32] OPENS PART V. The year 117-118 is a seam year, intentional, not a contradiction. Part IV = the fall of Daniel's Trajan-era world; Part V = starting over under Hadrian."
- `outline/master_outline.md`: Part I (ch01-11), Part II (ch12-22), Part III (ch23-33), Part IV (ch34-38), Part V (ch39-46), Part VI (ch47-50), Part VII (ch51-53).
- `outline/V2_REVISED_OUTLINE.md` (implied by ch assignments): Part III (ch23-33), Part IV (ch32-38), Part V (ch38-46), Part VI (ch47-53) -- with overlap at ch32 and ch38 boundaries.

**What conflicts:** The canon log says Part IV closes at ch31 and Part V opens at ch32. The master_outline says Part IV = ch34-38 and Part V = ch39-46. This is a 3-chapter disagreement on where Part IV ends and Part V begins, and a completely different Part VI/VII structure. The master_outline's Part VI = ch47-50 and Part VII = ch51-53, but the canon log labels ch38-46 as "Part V" content with "Part VI: The Ladder" starting at ch39 (see master_outline line 585 with "Part VI: The Ladder (125-138 AD, ch47-50)").

**Why Critical:** Chapter briefs, plotting notes, and context notes all refer to "Part IV" or "Part V" without disambiguation. A writing agent receiving a brief for "Part IV ch36" gets contradictory instructions depending on which numbering system it uses.

**Recommended resolution:** The master_outline's part numbering appears to be the most recently maintained document and is internally consistent. The canon log's "CLOSES PART IV at ch31" was written earlier and reflects an older structure. The master_outline's numbering (Part IV = ch34-38) is consistent with the updated_ch19_36 and updated_ch37_53 outline files. However, the V2_REVISED_OUTLINE shows yet another overlap at ch32 and ch38. Author should canonize one numbering and propagate it.

**Action taken:** FLAGGED. No fix applied (structural ambiguity requiring author decision).

---

### C-4: Phone death timing -- 00_premise.md contradicts world_rules.md and canon log

**Where:**
- `bible/00_premise.md` line 41: "The phone dies inside two weeks."
- `bible/05_world_rules.md`: "the phone dies for good around day three to four."
- `bible/08_canon_log.md`: "~50-100 hours of use before dying" (consistent with days, not weeks).

**What conflicts:** "Two weeks" vs. "day three to four" is a factor-of-4 to 5 discrepancy. The world_rules.md and canon log agree on "days." The premise file is the outlier.

**Why Critical:** Any writing agent reading only 00_premise.md would assume Daniel has two weeks of phone access. All other documents say he has approximately three to four days. This affects every early chapter's pacing.

**Recommended resolution:** Change "inside two weeks" in 00_premise.md to "within days (see world rules -- the phone dies around day three to four)."

**Action taken:** FLAGGED. Not fixed -- the edit touches a premise-level document that the author may have intentional reasons for (e.g., "two weeks" could be the original draft intent later revised in world_rules and canon log). The conflict is real and the world_rules.md version is the one that has been propagated through subsequent documents, making the premise file the stale outlier.

---

### C-5: Glossary gives wrong template for Daniel's citizen name

**Where:**
- `bible/07_glossary.md` lines 40-43: "He ends up commonly called Danihel or just the Thulean, and once a citizen takes a Roman-style name incorporating his patron's (e.g. a praenomen + Flavius from Macer + a cognomen). Settle the exact citizen-name when the citizenship chapter is drafted and LOG it."
- `bible/08_canon_log.md` bottom (DECISION ch17 freedom + name): "His Roman name becomes Marcus Ulpius Daniel (nomen Ulpius from Trajan's gens)."
- `outline/updated_ch01_18.md` ch17 entry: "'Marcus Ulpius Danihel' -- logged: imperial grant, Ulpius from Trajan's gens."
- `chapters/ch26.md` line 5: "Marcus Ulpius Lucanus, the praenomen mine, the nomen the emperor's" -- confirms the nomen is Ulpius (Trajan's gens), not Flavius (Macer's gens).

**What conflicts:** The glossary suggests the nomen comes from Macer ("Flavius from Macer"). All other sources agree the nomen is Ulpius from Trajan (the emperor who freed and enfranchised Daniel). The ch26 prose is unambiguous: "the nomen the emperor's." The glossary entry predates the ch17 decision and has never been updated.

**Why Critical:** Any writer consulting only the glossary would give Daniel the wrong Roman name -- "Flavius" instead of "Ulpius." Daniel's canonical name is "Marcus Ulpius Danihel."

**Recommended resolution:** Update the glossary to reflect the settled name: "He takes the Roman name Marcus Ulpius Danihel at citizenship (ch17): praenomen Marcus, nomen Ulpius from Trajan's gens (the emperor who freed and enfranchised him), cognomen Danihel (his own name). Informally he remains 'the Thulean' and 'Daniel'; Macer continues calling him 'Thulean/boy.'"

**Action taken:** FLAGGED. Editing the glossary was considered but this is a guidance/template entry that also functions as a reminder to settle the name. Since the name IS now settled in the canon log, the template language is just stale. However, editing it without knowing what other notes reference "Flavius" is risky. Author should update.

---

## MAJOR ISSUES (6)

---

### M-1: Tyche's birth year off by one year in 02_characters.md

**Where:**
- `bible/02_characters.md` line 108: "~14 in 98."
- `bible/08_canon_log.md` CHARACTER AGE ANCHOR: "Tyche: 14 in 99 AD -> born ~85 AD."
- `chapters/ch09.md` (sampled): "She was small, fourteen maybe" -- ch09 is dated "mid/late 99 AD" in the canon log. The prose confirms she is fourteen in 99 AD.
- `outline/updated_ch19_36.md` ch20 note: "Tyche is ~14 in 98 AD (born ~85 AD)" -- uses the wrong year.

**What conflicts:** The characters file and the updated_ch19_36 outline say "14 in 98 AD." The canon log anchor and the ch09 prose both say she is 14 in 99 AD (ch09 is set mid/late 99 AD). The difference is one year, but it shifts her computed age by one in every downstream calculation.

**Recommended resolution:** Change "~14 in 98" to "~14 in 99" in 02_characters.md and update the updated_ch19_36 reference. The canon log anchor and the ch09 prose are the authoritative sources.

**Action taken:** FLAGGED. Not fixed (requires editing two files with potential downstream cascade; author should review whether any prose ages in chapters use the 98-based computation).

---

### M-2: Marcia's birth year conflict within canon log itself

**Where:**
- `bible/08_canon_log.md` line 547 (ch22 entry): "She is a freedwoman, ~34-35 (b. ~73 AD)."
- `bible/08_canon_log.md` CHARACTER AGE ANCHOR: "Marcia: ~34 in 108 -> born ~74 AD."
- `bible/02_characters.md` line 214: "~25 in 98 (age-appropriate as the years pass)."

**What conflicts:** The canon log's own ch22 entry says "b. ~73 AD" but the CHARACTER AGE ANCHOR (which explicitly supersedes earlier entries) says "born ~74 AD." The characters file says "~25 in 98" -- if born ~74 AD she would be ~24 in 98, and if born ~73 AD she would be ~25 in 98. The "~25 in 98" in 02_characters.md is thus closer to the ch22 entry's "b. ~73 AD" than to the anchor's "b. ~74 AD."

**Recommended resolution:** The CHARACTER AGE ANCHOR explicitly supersedes all older entries. Accept "born ~74 AD" (~34 in 108) as authoritative. The "~25 in 98" in 02_characters.md should be "~24 in 98" to be consistent with the anchor, or the characters file should add a note that Marcia first appears in ch22 (~108 AD, age ~34) rather than in 98 AD. The ch22 entry in the canon log saying "b. ~73 AD" is stale and should be noted as superseded by the anchor.

**Action taken:** FLAGGED. Not fixed (requires author review of whether any prose in the early chapters references Marcia with an age anchored to 98 AD).

---

### M-3: Celer's death -- stale tentative language in 03_timeline.md

**Where:**
- `bible/03_timeline.md` entry for 105-106 AD: "Possible death of Celer here (decide in drafting; if not here, hold for Parthia)."
- `bible/08_canon_log.md` COORDINATOR DECISION: "Quintus Marcius Celer is ALIVE through ch28. He DIES in ch29 (Overreach), in the Parthian war's deep-east overreach / the rear revolts (~116-117); b.~63, so ~53."
- `outline/updated_ch19_36.md` ch29 entry: "Celer dies here (if still alive after ch21)." -- The parenthetical is also stale, since the canon log says explicitly he is alive through ch28.

**What conflicts:** The timeline file has not been updated since the DECISION was locked in the canon log. Any writer consulting the timeline file sees "Possible death of Celer here (105-106)" and might kill him before ch29.

**Recommended resolution:** Update `bible/03_timeline.md` to read: "Celer alive here and through ch28; DIES in ch29 (~116-117 AD, Parthian War overreach). See canon log COORDINATOR DECISION." Also update the ch29 parenthetical in updated_ch19_36.md.

**Action taken:** FLAGGED. Not fixed (would require editing 03_timeline.md, which is a structured planning document -- left for author to update alongside a thorough timeline review).

---

### M-4: Atlantic crossing timeline discrepancy -- departure chapter stated inconsistently

**Where:**
- `outline/V2_REVISED_OUTLINE.md` ATLANTIC CROSSING DECISION box: "first crossing ~113-114 AD, departure ch27, return news ch28."
- `outline/master_outline.md`: "First crossing departs: ~112-115 AD (Part IV / early Part V)."
- `outline/updated_ch19_36.md` ch26 note: "Ch26: Expedition organized." ch27: "[V3 TIMELINE NOTE] serious expedition planning begins ~108-110 AD; first departure ~112-115 AD. By ch28 (~113 AD) the plan is years old and the departure is imminent or has just occurred."
- `outline/updated_ch19_36.md` ch29 note: "Atlantic crossing status: by this chapter (~115-116 AD), the first expedition has either recently departed or is about to depart."

**What conflicts:** The V2_REVISED_OUTLINE says departure = ch27 specifically. The updated_ch19_36 file (more recent V3 notes) says the departure is "imminent or has just occurred" at ch28, and at ch29 it "has either recently departed or is about to depart." These are not fully contradictory but they blur which chapter the departure is in. The most recent V3 note in updated_ch19_36 says the departure should be treated as already underway or very recently completed by ch28, making ch27 the likely chapter of departure.

**Recommended resolution:** Lock the departure to ch27 per the V2_REVISED_OUTLINE DECISION box and update the V3 notes in updated_ch19_36 to reflect this. The ch28 and ch29 treatments should then be framed as: "the ship departed in ch27; Daniel is now in the east with no news from it."

**Action taken:** FLAGGED. Not fixed (structural plot decision for author).

---

### M-5: Part II date range mismatch in master_outline

**Where:**
- `outline/master_outline.md`: "Part II: The Man Who Flew (99-102 AD, ch12-22)."
- `bible/08_canon_log.md`: "[ch12] 101 AD, Daniel 20" -- meaning Part II (if ch12-22) starts in 101 AD, not 99 AD.
- The updated_ch01_18.md confirms ch12 is "101 AD, Daniel 20."

**What conflicts:** The master outline says Part II covers "99-102 AD" but the actual first chapter of Part II (ch12) is set in 101 AD. The 99-100 AD window belongs to Part I (ch01-11). This is a metadata error in the Part II header, not a structural plotting problem.

**Recommended resolution:** Update the Part II header to "101-102 AD, ch12-22" or "late 100-102 AD" (allowing for ch12's late-100 workshop establishment).

**Action taken:** FLAGGED. Not fixed (cosmetic metadata; low risk for prose drafting).

---

### M-6: Master_outline contains embedded V3 revision note in Subplot tracker

**Where:**
- `outline/master_outline.md` Subplot tracker, Phase D note: "[CANNON ARC -- SUCCEEDS IN DANIEL'S LIFETIME..." bracket -- this is a V3 revision note embedded mid-outline.

**What conflicts:** The note signals a canon change (cannon success in Daniel's lifetime) but it is embedded in the outline body without clear version tagging. A writing agent reading this section might not recognize it as a V3 override of V2 content earlier in the same file. This creates a risk of a writer using the V2 "cannon blocked" framing from the Phase D section while missing the V3 success note.

**Recommended resolution:** Move the V3 cannon success note to the top of the Subplot tracker section with a prominent "V3 OVERRIDE" tag, or add a V3 override note at the Phase D entry heading.

**Action taken:** FLAGGED. Not fixed (structural reorganization of the outline file).

---

## MINOR ISSUES (8)

---

### m-1: Vibenius death timing -- "exits ch35" vs. canon log

**Where:**
- `outline/V2_REVISED_OUTLINE.md` CONTINUITY section: "Vibenius exits ch35."
- `bible/08_canon_log.md`: "COORDINATOR DECISION: Vibenius is 'four years dead' at ch39 (~129 AD), so died ~125 AD -- consistent with V2_REVISED_OUTLINE 'Vibenius exits ch35.'"
- The canon log ch36 entry would be ~121-125 AD; if ch35 is just before and Vibenius dies there, his death at ~125 fits. This is consistent.

**What conflicts:** Nothing conflicts here -- the canon log and the V2 outline agree. However, the master_outline's Part IV description says "Vibenius exits... death witnessed" in a Part IV covering ch34-38. In that numbering, Vibenius exiting at ch35 is in Part IV, which aligns. This is a non-issue except insofar as confused Part numbering (C-3 above) makes it unclear which "Part IV" the V2 outline is using.

**Assessment:** MINOR -- not a real conflict; flagged only for cross-reference with C-3.

**Action taken:** No fix needed.

---

### m-2: updated_ch01_18.md contains corrections log showing past work already applied

**Where:**
- `outline/updated_ch01_18.md` lines 1904-1972: A corrections log showing C1-C9 corrections applied 2026-05-28.

**What conflicts:** Nothing conflicts. The corrections log confirms nine corrections were applied to this file. Auditing note: these corrections (C1-C9 within this file) are already reflected in the file's content and do not represent open issues.

**Assessment:** MINOR informational note; no inconsistency.

**Action taken:** No fix needed.

---

### m-3: updated_ch37_53.md contains corrections log at bottom confirming past work applied

**Where:**
- `outline/updated_ch37_53.md` lines 1053-1094+: A corrections log for C1-C14+ applied to this file.

**Assessment:** Same as m-2; informational. Corrections are already in the file content.

**Action taken:** No fix needed.

---

### m-4: updated_ch19_36.md ch20 uses "14 in 98 AD" (should be 99 AD per canon log)

**Where:**
- `outline/updated_ch19_36.md` ch20 note: "Tyche is ~14 in 98 AD (born ~85 AD)."
- This is the same birth-year-offset documented in M-1 above, appearing in a second file.

**Assessment:** MINOR (same root cause as M-1; fix both together).

**Action taken:** FLAGGED. Not fixed here (fix alongside M-1).

---

### m-5: Canon log internal conflict -- Part VI assignment

**Where:**
- `bible/08_canon_log.md` line 817: "[ch31] CLOSES PART IV."
- `bible/08_canon_log.md` line 1085: "[ch39] OPENS PART VI."
- `bible/08_canon_log.md` line 1296: "[ch46] CLOSES PART VI."
- `outline/master_outline.md`: Part VI = ch47-50 (not ch39-46).

**What conflicts:** Within the canon log, if Part IV closes at ch31 and Part VI opens at ch39, what is Part V? The canon log says "[ch32] OPENS PART V" and presumably Part V closes somewhere before ch39. The ch38 entry says "CLOSES PART V; hinges into Part VI." That would make Part V = ch32-38. But ch39 "OPENS PART VI" in the canon log while the master_outline says Part VI = ch47-50. This is the C-3 problem manifesting in the canon log as well.

**Assessment:** MINOR (same root cause as C-3; redundant to the Critical issue).

**Action taken:** No additional fix beyond C-3 flag.

---

### m-6: updated_ch19_36.md ch34 note says Lucanus "born ~108 AD"

**Where:**
- `outline/updated_ch19_36.md` ch34 note: "Lucanus (Daniel's son, born ~108 AD, approximately 10-14 years old in this chapter's range)."

**What conflicts:** Same as C-1/C-2; the birth year is wrong. At born ~112 and ch34 set ~118-122, Lucanus is ~6-10, not 10-14.

**Assessment:** MINOR (same root cause as C-1; fix when C-1 is resolved).

**Action taken:** FLAGGED. Not fixed here (fix alongside C-1 in the outline files).

---

### m-7: Outline-vs-chapter drift: ch45 prose has blocked-cannon language that contradicts V3 cannon-success arc

**Where:**
- `outline/updated_ch37_53.md` ch45 entry contains: "[V3 CANNON -- GUILT IS CONCRETE, NOT ABSTRACT]" and "[NOTE TO WRITING AGENT: Ch45 requires significant prose revision to ch45.md...]" with a note that "the existing ch45 prose says 'there is no gun in the world, no cannon a gunner can trust'" which must be revised.
- The prose chapter ch45.md is flagged as requiring revision per the cannon arc success update.

**What conflicts:** The outline knows the prose needs updating, and has flagged it. The actual ch45.md prose has not been revised per the V3 cannon arc change. This is an outline-vs-chapter drift where the outline is *correct* and the chapter *needs to catch up*.

**Assessment:** MINOR from a consistency-report standpoint (the flag is already in the outline). However, any QA reviewer reading ch45.md without the outline context would see a chapter that contradicts the canon (cannon DOES work in Daniel's lifetime).

**Recommended resolution:** The author or writing agent should revise ch45.md per the outline's specific instructions (lines 35-37 of ch45.md, reframe "no cannon a gunner can trust" to "no mobile field artillery a gunner can trust in the field").

**Action taken:** FLAGGED. Not fixed (prose revision of ch45 is out of scope for a small unambiguous fix).

---

### m-8: Tyche's name in 02_characters.md header vs. canon log

**Where:**
- `bible/02_characters.md` header for Tyche: uses "TYCHE" without the Ulpia nomen.
- `bible/08_canon_log.md` COORDINATOR DECISION: "Her legal name is Ulpia Tyche. She refuses to use 'Ulpia,' signs and is known only as 'Tyche.'"

**What conflicts:** This is not a true conflict -- the characters file correctly calls her Tyche throughout, consistent with the canon log's instruction ("she is 'Tyche' on the page always"). The legal nomen is noted in the canon log DECISION section but does not need to be in the characters file header. No inconsistency in usage.

**Assessment:** MINOR informational note only; no fix needed.

**Action taken:** No fix needed.

---

## OUTLINE-VS-OUTLINE DRIFT SUMMARY

| Document pair | Issue | Severity |
|---|---|---|
| master_outline Part numbering vs. canon log Part numbering | Three incompatible systems | CRITICAL (C-3) |
| V2_REVISED_OUTLINE Lucanus birth "~108-111 AD" vs. canon log anchor "~112 AD" | Birth year off | CRITICAL (C-1) |
| 02_characters.md "~14 in 98" vs. canon log "14 in 99" for Tyche | Age anchor off by 1 year | MAJOR (M-1) |
| V2_REVISED_OUTLINE departure "ch27" vs. updated_ch19_36 V3 notes | Atlantic departure chapter | MAJOR (M-4) |
| master_outline Part II header "99-102 AD" vs. ch12 actual date "101 AD" | Date range metadata off | MAJOR (M-5) |
| 03_timeline.md "Possible death of Celer" vs. canon log DECISION "dies ch29" | Stale tentative language | MAJOR (M-3) |

## OUTLINE-VS-CHAPTER DRIFT SUMMARY

| Chapter | Outline says | Prose says | Severity |
|---|---|---|---|
| ch09 | Tyche "~14" (using 98 AD anchor) | "fourteen maybe" set mid/late 99 AD | confirms 99 AD anchor |
| ch26 | Lucanus named, Forum dedication ~112-113 AD | Opens: "On the ninth day we named him Lucanus" at Trajan's Forum (~112 AD) | confirms birth ~112 AD |
| ch32 | Hadrian arriving, Four Consulars era, ~118 AD | Consistent | no drift |
| ch38 | Ulpia "nine that year" at ~127 AD (born ~118) | "Ulpia at the bench, my daughter, who was nine that year" at ~127 AD | consistent |
| ch45 | V3 cannon arc: siege bombards WORKED at Bar Kokhba | Prose says "no cannon a gunner can trust" -- uses pre-V3 framing | MINOR (m-7), flagged in outline |
| ch26 | Daniel's citizen name "Marcus Ulpius Lucanus" (nomen from Trajan) | "the nomen the emperor's" -- confirms Ulpius, not Flavius | confirms canon log; contradicts glossary (C-5) |

---

## TECH SCHEDULE / CANNON ARC CONSISTENCY

All documents agree on the following:
- Escapement: never solved by Daniel; Procula solves it in ch52 (~180-200 AD). Consistent across all files.
- Marine chronometer: only in ch53, descended from Procula's escapement. Consistent.
- Cannon/bombard: V3 canon is that the first working bronze bombard test is ~117-122 AD and bombards were used at Bar Kokhba (132-135 AD). This is consistent across the canon log, updated_ch37_53, and master_outline. The only drift is in ch45 prose (m-7 above).
- Steam pump: first operational in Hispania ~118 AD. Consistent.
- Phase assignments (A-E): consistent across all outline files and bible/04_tech_schedule.md.

---

## WORLD RULES / GLOSSARY CONSISTENCY

- `bible/01_world.md`: no conflicts found; consistent with other documents on Roman geography, power structure, money, and daily texture.
- `bible/07_glossary.md`: one conflict (Daniel's name template, C-5 above). All Latin terms consistent with usage in chapters.
- `bible/06_style_guide.md`: no conflicts found; no em dashes anywhere in introduced text, consistent with the style guide's prohibition.
- `bible/CHARACTER_VOICE_GUIDE.md`: no conflicts found; voice profiles consistent with how characters appear in sampled chapters (ch09, ch17, ch26, ch32, ch38).

---

## FIXES APPLIED IN THIS AUDIT

| File | Change | Basis |
|---|---|---|
| `bible/02_characters.md` | Changed "Born ~108 AD to Daniel and Marcia" to "Born ~112 AD to Daniel and Marcia" for the Lucanus entry. | Canon log CHARACTER AGE ANCHOR + ch26 prose (naming at ~112-113 AD at the Trajan's Forum dedication). All other authoritative sources agree on ~112 AD. |

**Total fixes applied: 1**

---

## ISSUES BY SEVERITY COUNT

| Severity | Count |
|---|---|
| CRITICAL | 5 |
| MAJOR | 6 |
| MINOR | 8 |
| **Total** | **19** |

---

## APPENDIX: Files Audited

- `bible/00_premise.md`
- `bible/01_world.md`
- `bible/02_characters.md`
- `bible/03_timeline.md`
- `bible/04_tech_schedule.md`
- `bible/05_world_rules.md`
- `bible/06_style_guide.md`
- `bible/07_glossary.md`
- `bible/08_canon_log.md` (full read, both halves)
- `bible/CHARACTER_VOICE_GUIDE.md`
- `outline/V2_REVISED_OUTLINE.md`
- `outline/master_outline.md`
- `outline/updated_ch01_18.md` (full read)
- `outline/updated_ch19_36.md` (full read)
- `outline/updated_ch37_53.md` (full read)
- `chapters/ch01.md` (sampled in prior session)
- `chapters/ch09.md` (sampled -- Tyche age verification)
- `chapters/ch17.md` (sampled in prior session)
- `chapters/ch26.md` (sampled -- Lucanus birth and Daniel name verification)
- `chapters/ch32.md` (sampled -- Hadrian era, Lucanus age check)
- `chapters/ch38.md` (sampled -- Ulpia birth year verification)
