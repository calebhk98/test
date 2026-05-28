# Round 2 Audit — consolidated summary

Follow-up pass covering: sentence-level/structural prose quality, an independent
AI-bad-prose catalog, blind adversarial critiques, thread/predictability/voice/pacing
audits, preachiness, the "teen-knowledge seeding" theme, and a real-Rome-vs-book-Rome
diff. Detail files are under `book/review/` (and `book/review/parts/`). No story files
were edited.

---

## THE BIG TENSION (author-intent vs execution)
Two independent agents converge on one finding worth your attention first:

**You want (a) a vivid sense of how fast a modern teen can bend history and (b) a
"huge difference" between real Rome and book-Rome. The book as written delivers
neither *within Daniel's lifetime* — on purpose — and only pays both off in the
epilogue.**
- `teen_knowledge_and_change.md`: the "Daniel points an expert at a target and they
  return with the answer in his lifetime" scene is **nearly absent**. Pointing happens
  through *institutions* (contest, patronage, the encyclopedia), not expert-to-expert
  breakthroughs. Steel never solved, clock never solved, telescope fails. The chapter-
  by-chapter *felt experience is grinding failure, not transformation.* Verdict: theme
  **MIXED**.
- `rome_divergence_diff.md`: within Daniel's life the divergence is **conservative/
  incremental** (7 Major, 3 Moderate, 5 failed; "Rome is recognizably Rome"); it only
  becomes **genuinely huge in the epilogue**, and even then as a quiet whisper.
- The cold reader (`cold_reader_ch1-3.md`) liked the voice but this is the same shape.

This is faithful to the bible's honesty rules (deep tech withheld, dies-with-it-in-his-
head). But it is in real tension with your stated wish for awe at teen knowledge and a
big visible delta. **If you want the "huge difference" felt earlier, the cheapest fix is
to add 2-3 in-lifetime "pointing pays off" scenes** (see the Eratosthenes miss below).

### The single best missed "pointing" scene
The **Eratosthenes chain**: two sticks, two shadows, two cities -> Earth's circumference
-> (with the right nudge) Earth's mass and the Sun's distance. Needs no materials
breakthrough, lands inside Daniel's lifetime, and is exactly your "he knows enough to
point, Romans finish it" ideal. The book never uses it. Other candidates: a geared
aeolipile -> paddle demonstration; pendulum timing; variolation.

---

## PROSE AT THE SENTENCE LEVEL (your new ask)
Reference catalog written independently: `bad_prose_catalog.md` (35 patterns across 7
levels). Deep close-reads: `parts/lineprose_ch01-06.md`, `_ch24-29.md`, `_ch47-53.md`.

**The dominant, book-wide, sentence-level weaknesses (all three close-reads agree):**
1. **Paragraph/scene-ending aphorism** (the calcified one) — scenes are sealed with a
   portable maxim that restates what the scene already showed. Fires 2-3×/chapter and
   *worsens* across the book. The canon log's own "VOICE WATCH" already flagged this
   after ch33 and it was never fully reined in. Examples: *"a man kneels, in the end, to
   whatever is holding the knife"* (ch27); *"burning a thing is only another way of
   keeping the smell of it"* (ch29 close); ch49's *"A finished-looking book... has killed
   more climbers than any honest gap."*
2. **Tricolon "X. Y. Z."** as the default unit of emphasis — ~4-5×/chapter early,
   audible machinery by ch2. *"The numbers were a trick. The creatures were witch-talk.
   The map was a curiosity in a drawer."*
3. **Correctio "it wasn't X, it was Y"** — the explicitly banned construction, still
   reflexive (~25-37 instances book-wide; one still live in ch40).
4. **The "two long, one short punchy fragment" cadence** and **filtering verbs**
   ("I felt / I knew the way I knew most things") at high-tension moments.

The ch50 death scene and the ch3 map scene are the genuine sentence-level high points.
The **ch53 final line steps outside POV to announce the meaning** — the ending leans on
devices exactly where it should trust the reader.

## BLIND ADVERSARIAL CRITIQUES (I told the agents it was human work)
`parts/blind_critique_ch01-10.md`, `_ch25-34.md`, `_ch44-53.md`. All three independently:
- **Level: seasoned professional.** **AI usage: "almost certainly human," HIGH/medium
  confidence.** (Notable, given it's AI-written — the prose passes as professional human
  work; the human-signals they cite are the documented failures, controlled imperfection,
  and refusal of emotional closure.)
- But all three name the **same calcified weakness**: the "dramatized scene -> analysis
  -> extended metaphor" close has become a *mechanical formula* by ch31; "cut ~30% of the
  section-closing interpretive passages and the prose gets harder and better."
- ch1-10 adds: **Daniel is too consistently self-aware** — unbroken strategic
  metacognition that reads like retrospective analysis, never disrupted by the terror the
  prose claims he's in.

---

## THE OTHER ROUND-2 AUDITS (quick results)
- **Threads** (`thread_audit.md`): every *seeded* thread closes; genuine never-closed
  loose ends are **Naso** (ruined at ch11, vanishes after ch29), **Scaeva's sulfur
  secret** (hook never springs), and the **ch44 ocean hull's** fate. "Design-open" rungs
  (steel/steam/planets) are intentional.
- **Predictability** (`predictability_audit.md`): **not over-telegraphed** by the 2-of-4
  rule (scores: PARTIAL, PARTIAL, WRONG, WRONG). Nuance: the two misses happened because
  *multiple* threads were telegraphed at once — the middle/late book is **over-loaded
  with parallel set-ups**, which dilutes tension. Sharpest single over-telegraph: the
  ch11->ch13 manned-flight death, rehearsed step-by-step across three chapters.
- **Voice** (`voice_audit.md`): Macer/Tyche/Apollodorus/Heras all **consistent**. Two
  small fixes: Macer ch33 (his suppressed fondness narrated too explicitly), and Tyche's
  bible-mandated "Ulpia" friction is described but never *dramatized* in a scene.
- **Pacing** (`pacing_map.md`): one real **valley at ch38-41** (legacy-building, avg ~4),
  widening to a soft ch38-44 zone; **no exhausting back-to-back peaks**; lone peak ch13.
- **Preachiness** (`preachiness_audit.md`): **Clean.** Anti-slavery stays in events and
  economics; no authorial lectures, no modern political vocabulary. Closest edges: ch20
  (Tyche's *named-but-suppressed* speech) and ch43 (Ulpia's wasted mind) — neither tips
  over. **This meets your "fun story, not an agenda" bar.**

---

## ANSWERS TO YOUR DIRECT QUESTIONS THIS ROUND
- *"Sections where sentence-to-sentence prose is bad/predictable/repetitive?"* -> Yes;
  see the three `lineprose_*` files. The repeating offenders are the closing-aphorism,
  the tricolon, and the correctio, intensifying mid-book.
- *"Did any agent define AI bad prose first?"* -> Now yes: `bad_prose_catalog.md` (35
  patterns), built independently of your `Bad writing.txt`, then graded against.
- *"Lie to agents to make them more critical?"* -> Done: three blind critiques judged the
  text as human and still surfaced the calcified-aphorism formula and the over-aware
  narrator.
- *"Is there a file showing the actual difference vs history?"* -> The in-universe one is
  the **DIVERGENCE LEDGER** at the bottom of `book/bible/03_timeline.md`; the analytic
  ones are `analysis/history/divergence_*.md`; and the new concrete diff is
  `book/review/rome_divergence_diff.md`.
- *"Show how much a teen knows / how fast they change history / huge difference?"* -> See
  THE BIG TENSION above: currently deferred to the epilogue; under-delivered in-lifetime.
- *"Thinly veiled political pushiness?"* -> None of concern; verdict Clean.

## File index (round 2)
`book/review/`: bad_prose_catalog.md · thread_audit.md · predictability_audit.md ·
voice_audit.md · pacing_map.md · preachiness_audit.md · teen_knowledge_and_change.md ·
rome_divergence_diff.md · cold_reader_ch1-3.md · ROUND2_SUMMARY.md (this file)
`book/review/parts/`: thread_ch*, predict_ch*, voice_*, lineprose_ch*, blind_critique_ch*
