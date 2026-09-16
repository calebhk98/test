# Master QA Summary — V4 pass (reviews of the V3 chapter rewrites)

**Scope:** Fresh per-chapter QA of all 53 chapters in `book_v4/chapters/`, one
reviewer agent per chapter. Individual reports: `book_v4/qa/chNN_review_v3.md`.

## Verdict tally
- **PASS: 4** — ch01, ch40, ch47, ch50 (ch47/ch50 carry minor SHOULD FIX only).
- **REVISE: 49** — everything else.

Every REVISE chapter is fixable with local edits; no chapter needs a structural
rewrite. The book's bones are sound — the misses are line-level tics, a layer of
date/age arithmetic slips, and a handful of missing outline beats.

## Most widespread issues (priority order)
1. **One-sentence-paragraph density over the 15% cap** — the single most common
   failure; present in a large majority of chapters, several at 25–47% (worst:
   ch38 ~47%, ch53 ~38%, ch24 ~37%, ch42/ch43 ~37%, ch17 ~34%, ch20 ~36%).
2. **Correctio ("not X, it's Y" / "It was not X. It was Y.")** — survived the V3
   rewrite in ~25+ chapters; zero-tolerance. Usually 1–4 instances each; worst
   ch27 (4) and ch41 (2 in one paragraph).
3. **Wisdom-button / aphoristic scene closings over the 1-per-chapter cap** —
   very common; stacked 2–4x in ch5, ch24, ch36, ch37, ch39, ch43, ch46, ch48,
   ch50, ch51.
4. **Future-vantage narration** — ch8, ch10, ch15, ch17, ch25, ch34, ch37, ch52.
5. **Meta-disclaimers / honesty-scaffolding** — ch3, ch10, ch18 (3 in one scene),
   ch37, ch42, ch44.
6. **"the way you/a man/a child" over the 3-cap** — ch10, ch17 (9), ch27 (8),
   ch32 (7), ch35 (8), ch37 (5).
7. **Muted lower-class voices** — Pamphilus repeatedly appears with no line
   (ch11, ch19); occasional clean-heckler problem (ch8).

## Date / age arithmetic slips (recurring, low-effort fixes)
- ch6: Heras "forty-five years explaining the world" at age ~46.
- ch14: Tyche "sixteen" should be ~17 (102 AD); plus a near-verbatim duplicated
  gunpowder-vow passage (copy-paste artifact).
- ch20: "nine years" should be ~eleven.
- ch35: "twenty years" should be twenty-three.
- ch38: Daniel "five-and-forty" should be "six-and-forty" (127 AD).
- ch39: Marcia called "the widow" while still alive (she dies ch48) — should be
  "wife."
- ch41: "fifty years here" should be ~33–36.
- ch44: "eleven years" (tomatoes) and "thirty-five years" (Hermes/steel) both off.
- ch47: clock "forty years" should be ~thirty-odd.
- ch48: marriage "thirty-five years" should be ~38; AND Pamphilus's freedom
  attributed to "Macer's sesterces" — canon says Daniel's own money (load-bearing
  to the scene's emotional point).
- ch50: "forty years" (x2) should be ~45–48.

## Canon / continuity issues beyond arithmetic
- ch7: a glass-disc prize block (Sextus Pedanius optics breakthrough) contradicts
  later canon — no peculium yet in 99 AD, prize model not until ch16–19, and it
  undercuts ch23's "honest failure." Recommend cutting the block.
- ch24: Volta-pile demonstration to Heras deferred ("tomorrow") though the V2
  milestone wants it on-page by 110 AD.
- ch43: POV slip — "Daniel" appears in first-person narration (should be "me").
- ch46 vs ch48/ch49: the Atlantic/Garonne ocean program is shown lapsing in ch46
  but ch48's dock scene and ch49's legacy need it still operating (privately
  funded through Phase E). Reconcile direction across the three chapters.

## Missing required outline beats (per-chapter reviews have specifics)
- ch10: water-powered bellows plant. ch19: rag-paper R&D seed. ch21: steam-pump
  attempt + valve-casting prize. ch30: on-page institutional autonomy during the
  Trajan-death chaos. ch32: Heras's personal (not political) diagnostic line on
  Hadrian. ch34: Lucanus English-exchange before his ch38 departure. ch47/ch48:
  railway/steam argument to Antoninus Pius. ch49: the endowed Prize-for-
  Demonstrated-Truth in the will scene; Atlantic-ship uncertainty beat.

## AUTHOR DECISIONS REQUIRED (not auto-fixable)
1. **ch52 pendulum line** — "The length of the rope, not the force of the push"
   is simultaneously a zero-tolerance correctio AND an explicit outline
   preservation mandate. Pick which wins (suggest rephrasing to keep the insight
   without the negation pivot).
2. **Part-numbering systems** (from `V4_FILE_CONSISTENCY_AUDIT.md`, C-3): canon
   log, master_outline, and V2_REVISED_OUTLINE use three different Part-boundary
   schemes. Choose one.
3. **Atlantic/ocean-program direction** (ch46 vs ch48/ch49 above).

## Note
These reviews assess the V3 rewrite; they were generated independently of the
older (now-deleted) analysis artifacts. A future "V5" fix pass could apply the
MUST FIX items chapter-by-chapter the same way V3 was produced.
