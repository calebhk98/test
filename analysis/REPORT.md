# Story Audit — *The Long Way Home* (consolidated findings)

Scope: a ~197,000-word, 53-chapter novel (HS student wakes in 98 AD Rome, sparks a
tech revolution) written by AI subagents, audited here against the author's two
prompt files, the outline, the story bible, and the per-chapter QA reviews.

Method: 20+ focused subagents, deliberately overlapping (e.g. characters and prose
checked in five chapter-ranges each) so a miss by one agent is caught by another.
Detailed evidence lives in the files referenced under each section. **No story files
were edited** — this is analysis only.

Severity legend: [BLOCKER] rule/spec violation in shipped prose · [MAJOR] real craft
or continuity problem · [MINOR] polish.

---

## TL;DR — the headline answers

- **Follows the prompts?** Yes on the *spine and themes* (very faithfully). Mixed on
  the prompt's "name every gadget" wishlist (a deliberately trimmed subset). One real
  prose-rule violation recurs book-wide: the **banned "not X, it's Y" correctio**.
- **Follows the outline?** Yes — closely. No contradicted beats; every chapter hits
  its stated goal. A handful of small partial/missing beats.
- **Does every QA say PASS?** **No.** 23 of 53 QA files say REVISE, yet all 53 are
  marked "ACCEPTED." Fixes were almost all really applied — **except one live
  violation in ch40.**
- **Do the character profiles list all characters?** **No.** Several load-bearing
  characters (notably Daniel's daughter **Ulpia Severa**) are absent from the bible.
- **Do characters follow their profiles?** Yes — strong, no real drift.
- **Repetition / AI tells?** The book is clean on crude tells (no nodded/sighed/
  chuckled) but leans hard on a few signature tics: **gnomic takeaway-restating
  closings**, the **correctio**, and the phrase **"the way" (677×)**.
- **History spread?** Well-calibrated and historically accurate; bends late and
  gated, never breaks on a whim.
- **Trains?** Builds primitive mine **rail-carts** (rejected as "slaves are cheaper");
  engine/steam trains correctly stay named-only dreams. The intended catchphrase
  **"all tracks lead to Rome" is absent.**
- **Ignored easy fixes?** Sanitation is handled well; the glaring miss is **lead
  poisoning** (he adores Rome's lead pipes), then **city-scale fire prevention**.

---

## 1. Does it follow the prompts in the .txt files?
Detail: `analysis/prompt_adherence.md`, `analysis/repetition_and_tells.md`, `analysis/manuscript_integrity.md`

### 1a. `HS student Ancient Rome.txt` (the idea prompt) — mostly YES on substance
WINS (present and well-executed): the from-memory **world map**, the **Thule/Atlantis
cover story**, the **hot-air balloon** + its deadly manned crash, **Hindu-Arabic
numerals**, the **germ framing as "invisible creatures,"** water boiling/filtration,
the **cannon-built-to-burst**, the **niter-bed gunpowder slog**, **crucible/folded
steel as THE chokepoint**, the **telescope and water-clock as honest failures**, **mine
rail-carts that lose to slavery**, the **annual sci-fi writing contest**, the
**true-and-false ocean-redirection map**, and the **English-cipher encyclopedia
"ladder."** The MC is convincingly HS-competent and **wrong in teen-plausible ways**.
The anti-slavery-by-economics attack, literacy push, the phone dying early, and the
loneliness spine are all delivered richly.

MISSES (prompt items the book dropped or under-delivered):
- [MAJOR, by-design tradeoff] The prompt wanted a *maximalist naming* of impossible
  tech. The book chose a tight, deep subset instead. **Entirely absent:** soap,
  **nitroglycerin** (incl. the wanted "refuses to touch it" beat), compound bow,
  Korean-style heated floors, ball bearings, tea/chamomile, wristwatch/quartz clocks,
  Romeo & Juliet / spreading specific fiction, and nearly the whole appliance/vehicle
  bait list (submarines, aircraft carriers, 3D printers, washers/dryers/fridges,
  bidets, AC, vacuums, displays, maglev/1000 mph floating trains, rockets/jets).
- [MAJOR] The **water-wheel mills / looms / spinning wheel** — a core industrial-
  revolution engine the prompt stressed — is the most substantive under-dramatized
  item (appears only as metaphor/contest-dream, never built). See §7/threads.
- [MINOR] **Distilled spirits** is named in the outline but never written into prose.
- [Note, intended] The breezy "**satellites by 300 AD, go big**" ambition is
  deliberately swapped for the sober "I moved the bottom rungs" — a defensible
  thematic choice, not an error.

### 1b. `Bad writing.txt` (the prose-rules prompt) — mostly YES, one recurring breach
- **Em dashes:** chapter prose is clean (**0**). The compiled manuscript has **8**, all
  in auto-generated PART headers from `build_manuscript.py` (one-line fix). [MINOR]
- **"not X, it's Y" correctio / epanorthosis (explicitly banned):** **recurs book-wide
  — ~25 strict / ~37 loose instances**, found independently by the repetition agent
  and all five prose-quality agents. This is the single clearest prose-rule violation.
  Examples: ch28 "I did not have a plan. I had a wound with an idea in it"; ch50 "It
  was not the heart that stopped me. It was the breath." [BLOCKER as a rule, MAJOR in
  practice]
- **Conjunction-led sentences (So,/And,):** used as requested. Good.

---

## 2 & 3. Does the story follow the outline, and does each chapter's prose match its brief?
Detail: `analysis/outline_fidelity/range_ch01-11.md` … `range_ch44-53.md`

Fidelity is **high**. Across all 53 chapters there are **no contradicted beats**, and
every chapter achieves its stated structural/emotional goal. Hard mandates are honored:
the canon "Daniel is a slave until ch17" flip; ch13's death rendered without telegraph
(but see §8/9); ch21 dramatizing *why* he breaks his gunpowder vow; ch23's honest
failures; the ch49 phone-relic disposition; ch50 death rendered not annotated; ch51 a
distinct Roman-document voice; ch53 kept a vague glimpse.

The few genuine shortfalls (all [MINOR] unless noted):
- **ch02 — MISSING:** briefed "guards fascinated by zippers, baffled by the phone"
  never happens (only the shirt's weave; the phone is never seen by guards). [MAJOR]
- **ch40 — MISSING:** "political and economic theory" is named in the encyclopedia-
  ladder brief but never appears and isn't flagged as a deferred gap. [MAJOR]
- **ch06 — deviation:** briefed "paper model rises" becomes a rag toy (no paper yet).
- **ch22 — PARTIAL:** briefed "contubernium then marriage" is rendered as a single
  lawful marriage (defensible: both are free, so contubernium would be wrong term).
- **ch09 — PARTIAL:** Macer's full tria nomen never actually appears on the page.
- **ch11 — PARTIAL:** Celer's interest is observation only; "signaling" never raised.
- **ch32 / ch38 / ch39 — PARTIAL:** macro political beats (Hadrian proclaimed /
  abandons the east / workshop-as-academy) are carried by adjacent chapters rather
  than dramatized in-chapter.

---

## 4. Does each QA review say the story passes?
Detail: `analysis/qa_status.md`, `analysis/manuscript_integrity.md`

**No.** **30 PASS / 23 REVISE** — yet `chapter_list.md` marks **all 53 "ACCEPTED."**
That's an internal contradiction in the bookkeeping.

The chapter-range audits verified the REVISE blockers against the *current* prose: in
almost every case the fix was really applied (e.g. ch01 em-dash title, ch04/ch09/ch16/
ch34/ch52 future-narrator lines, multiple correctio fixes), so the "ACCEPTED" flip is
mostly justified. **One confirmed exception:**
- [BLOCKER] **ch40** still contains the exact banned correctio QA flagged: *"…she said
  so to me one evening over the third copy, **not as a complaint, as a figure**"* (~L71).

---

## 5. Do the character profiles list all characters?
Detail: `analysis/characters.md` + `analysis/characters/range_*.md`

**No — this is the biggest documentation gap.** `02_characters.md` was never updated
past the planning roster. Characters with real page-weight that are **NOT profiled**:
- [MAJOR] **Ulpia Severa** — Daniel's daughter, central to the cipher/encyclopedia
  thread in Parts VI-VII. Profiled nowhere.
- **Lucanus** (Marcus Ulpius Lucanus) — Daniel's son.
- **Pamphilus, Felix, Sabinus, Naso, Geta** — recurring freedmen/assistants.
- The keeper-chain: **Vitalis, Chloe, Zoticus, Eudemus, Theophanes, Vibia.**
- **Procula** — the epilogue climber (a *different* person from Ulpia; see below).
- The **optio** of ch02-04 — Daniel's first sustained human contact, unnamed.

Related items:
- [BLOCKER, in docs not prose] **`03_timeline.md` conflates "Ulpia" and "Procula"** in
  its divergence ledger. The prose keeps them clearly distinct (Ulpia = blood
  daughter; Procula = unrelated craft-keeper a generation later). Fix the ledger.
- [MINOR] The bible's planned **Pliny the Younger cameo** (ch51) was replaced by an
  invented correspondent, **Gaius Norbanus Rufus** — a sensible chronology fix worth
  logging.
- The **canon log (`08_canon_log.md`) is the de-facto complete character record**; the
  prose develops all these figures consistently. The gap is in the profile bible, not
  the story.

---

## 6. Do all characters follow their character profile?
Detail: `analysis/characters.md` + `analysis/characters/range_*.md`

**Yes — adherence is strong and consistent; no real drift found** across Daniel, Heras,
Macer, Tyche, Hermes, Celer, Crispus, Vibenius, Scaeva, Marcia, Trajan, Hadrian,
Apollodorus. Macer stays blunt/mean-funny; Heras stays the dry skeptic who punctures
the germ pitch; **Daniel stays a fallible non-prodigy who never wins without cost**
(flubbed long division, maimings, a death he causes, the clock he can't build); Tyche's
enslavement is not romanticized and the relationship is kept non-romantic. The bible's
"DON'T" notes are honored.

Minor watch-items (all [MINOR], continuity not character):
- Age drift: **Scaeva/Crispus/Vibenius read ~6-7 years too young** for the 98 AD
  baseline by the time of the ~117 AD scenes; Daniel's elapsed-time label jumps
  ("twelve years" → "nineteen/twenty").
- Daniel's late-book **"Latin drift" is rendered as lexical loss** (losing English
  words) rather than the syntactic Latinate cadence the style guide describes — a
  coordinator call, not a breach.
- Marcia marries with no contubernium phase (see §3).

---

## 7 & 11. Repetition (including reusing the same phrase over and over)
Detail: `analysis/repetition_and_tells.md` (with grep counts)

The book is **clean on crude beat-tags** (nodded 0, sighed 0, chuckled 0) and hedging
is *varied*, not uniform (perhaps 5, seemed 2). The repetition problem is in distinctive
phrasing and motif over-use:
- [MAJOR] **"the way" / "X the way Y" — 677×** (~13/chapter, the defining verbal tic;
  the book's final sentence even lands on it).
- [MAJOR] **"looked at me" — 91×** (eye-contact as connective punctuation, the stealth
  replacement for beat-tags).
- [MAJOR] **"the shape of" — 59×**, **"the whole of" — 63×** (+ "that was the whole" 17×),
  **gnomic "a man who…" 38/29×**, **"which is to say" 21×**.
- [MINOR motif over-use] Macer's "turned the gold ring on his thumb" (~11×); the
  "wait for the water to boil" image closing **three war chapters in a row** (ch28-30);
  "old hands flat on a surface" closing gesture (4×); the "Cheap. Mine. Undeniable."
  tricolon refrain; the forearm burn-scar re-explained nearly every early chapter.
- [MINOR] Deliberate motifs are well-controlled (the phone 22×, "the new figures" 39×,
  "the little ones" 17×) — leave those.

---

## 8. How predictable is the story?
Detail: `analysis/prose_quality/range_*.md`

Generally well-paced; most reveals are *rendered* rather than guessable. The genuine
predictability problems:
- [MAJOR] **ch11 Naso fire** is so heavily foreshadowed that only the victim, not the
  outcome, is in doubt.
- [BLOCKER per the brief] **ch13's death is over-telegraphed** — the chapter declares
  catastrophe in its opening lines ("a thing that is going to crush you"), pre-grieves
  the victim, and annotates "I knew with my whole body what was coming" a beat before
  the fall. Rendered well, but drained of suspense, violating the no-telegraph mandate.
- [MINOR] Antagonist arcs (Crispus, Scaeva, Vibenius) **fade out** rather than resolve,
  which is the opposite problem — under-paid-off, not predictable (see §13).
- The epilogue pays off Daniel's two mourned "rungs" (the clock, the westing) almost on
  cue, but the inhabited-shore twist keeps it off a tidy bow.

---

## 9 & 10. AI tells and bad writing
Detail: `analysis/prose_quality/range_*.md`, `analysis/repetition_and_tells.md`
(Note: the bad-writing criteria are already defined in `Bad writing.txt`; agents scored
against every category in it, so no separate "what is bad writing" file was needed.)

**The dominant AI tell, found in every range:** [BLOCKER/MAJOR] **gnomic, aphoristic,
takeaway-restating scene/chapter closings** — nearly every break ends on a portable
wisdom-button that restates the scene's meaning (e.g. ch23 "I can't beat it"; ch34 "It
is the only interesting part"; ch49 "Some things you secure. Some things you only
confess you could not"). The reader is trained to expect the button.

Other recurring tells:
- [MAJOR] **"not X. It was Y." correctio** (the banned construction; see §1b).
- [MAJOR] **Narrator stepping outside time** despite the style-guide ban: ch04 "for a
  long time afterward I got him wrong," ch07 "I have never entirely stopped," ch36/ch37
  future-vantage lines, ch46 a future prediction.
- [MAJOR] **Exposing subtext / announcing emotional weight**: ch05 states the loneliness
  theme aloud; the "two feelings, same size, you couldn't get a knife between them"
  formula is used ~4× (ch46-48); the "I want to be exact/honest about X" metanarrative
  frame opens scenes 12+ times.
- [MAJOR] **Info-delivering dialogue** in a few charged spots (Macer's ch09 monologue;
  Marcia's ch38-39 thesis speeches; the Heras deathbed exchange).
- [MAJOR] **"X. Y. Z." short-sentence tricolons — 19×**; **templated chapter openings
  (~23/53)** ("There is a [sound] a [place] makes when…", "[X] came…", "The first
  thing…").

**Genuine strengths to preserve:** sensory grounding, coherent (non-stacked) imagery,
oblique/human dialogue in most scenes, real architectural dramatic irony (ch51/ch53,
Apollodorus's gourds → Hadrian), and the ch42 (Heras) and ch50 (death) chapters, which
render grief through action/absence and are the technical high points.

---

## 12. Threads the book could have created but didn't
Detail: `analysis/threads/could_have_created.md`

Top high-value uncreated threads (the book is faithful, so these are *consequence*
threads it left on the table):
1. **A rival leaking/stealing gunpowder to an enemy (Parthia / frontier peoples)** —
   the prompt's single biggest stated worry. Powder goes "loose" inside Rome but never
   crosses a border; the danger stays static dread, never a dramatized event.
2. **Christian/Jewish sectarian reaction** to his ideas — set in the Pliny era, yet
   monotheism is essentially absent (Jews appear only as Bar Kokhba victims).
3. **The "uninhabited west" map-lie detonating on Daniel politically *while alive*** —
   the puncture is deferred to the epilogue, costing him nothing personally.
4. **A Daniel-trained protégé going wrong** — the keeper-chain is uniformly loyal; no
   student ever sells, weaponizes, or corrupts the knowledge.
5. **An epidemic or economic shock testing the germ framing / labor-saving tech at
   scale** — kept as slow background rather than a public reckoning.

---

## 13. Threads opened but not closed
Detail: `analysis/threads/opened_not_closed.md`

**Every actually-seeded chapter "Plant:" pays off**, and all load-bearing threads CLOSE
(phone relic buried with him; English cipher; ocean-map lie; Felix as the recurring
contest entrant; Ulpia; Tyche; Celer; Apollodorus; steel).

PARTIALLY closed (fade rather than resolve) — [MAJOR] collectively:
- **Vibenius's debt** (the unreadable IOU from the ch27 trial) is never called; it
  dissolves when he dies offstage.
- **Crispus's fate** — defeated at the trial, reappears in the ch33 terror, then
  vanishes; no on-page downfall.
- **Scaeva's fate** — sheds Daniel to save himself, then disappears; his "point the
  powder for me" debt is never collected.

DANGLING — but note these were **tech-schedule/outline intentions never written as
on-page promises**, so the prose never opens them: **distillation** (named in the
outline's own Part III summary), **soap**, **horse collar**, **spinning wheel**,
**water-power adoption**, and the **"all tracks lead to Rome"** catchphrase.

---

## 14. How far does it spread from history?
Detail: `analysis/history/divergence_ch01-30.md`, `divergence_ch31-53.md`

**Historically accurate and well-calibrated.** Every real anchor is correct (Nerva/
Trajan 98, adventus 99, Dacian Wars and Apollodorus's bridge, Sarmizegetusa 106,
Forum/Column 112-113, Parthian War, Ctesiphon 116, Trajan's death at Selinus Aug 117,
the Four Consulars 118, Hadrian's abandonment/Wall/travels, Bar Kokhba, Hadrian's death
138, Pius's succession). The one "wrong fact" (China had gunpowder by 100 AD) is
deliberately in Daniel's fallible memory and flagged as such.

Divergence pace: **the macro-timeline does not bend at all in 98-117** (texture changes
only — capped numerals, hygiene, crude printing, the dreaming-contest). First *logged*
divergence is the ch36/~121 bounded ocean program; the ch44 signs are all measured and
partial; ch53's ocean crossing is the cumulative top of an on-page ladder (Procula's
escapement → marine chronometer), gated on the unsolved sea-clock/longitude problem,
kept a glimpse, and undercut by the inhabited shore (the "uninhabited west" exposed as
Daniel's lie).

**Verdict: neither too bold nor too timid.** Aggressiveness scales with time and
institutions, not one transplant's cleverness — exactly the right fit for the premise,
and faithful to world-rule 8 ("history bends but does not break on a whim").

Minor flags for the timeline desk: ch51's "consulship of Clarus and Cethegus" implies
~AD 170 (confirm intended); Antinous's 130 drowning is ledger-listed but never on-page.

---

## 15. Does it show him making trains?
Detail: `analysis/threads/trains.md`

**No — and the nuance is executed mostly as intended.**
- **Rail-carts (BUILT, correct):** ch23 — wooden rails, flanged wheels, "Four men and a
  slope did the work of twenty-six men and a whip" — then torn out because, as Marcia
  says, *"You own the men… You do not have to pay your haulers."* The wheels end up "in
  the shed." Exactly the intended slaves-are-cheaper beat.
- **Engine/steam/floating trains (NAMED-ONLY bait, correct):** never built; the
  aeolipile reframe is present (ch19, *"imagine this strong enough to pull a hundred
  carts"*) and recurs as Felix's prize-tale and a clay toy "train in everything but the
  rails" he "never built and never would."
- [MAJOR gap vs intent] **"All tracks lead to Rome" — ABSENT.** The bible explicitly
  called for this reframing of "all roads lead to Rome"; the phrase appears nowhere.

---

## 16. Easy fixes a modern teen would know, but ignored
Detail: `analysis/threads/easy_fixes_ignored.md`

Handled WELL (category A, not misses): **sanitation / waterborne disease** (germ
framing, boiled water, limed latrines, sand-charcoal filters at army scale) and
**handwashing in medicine**.

Genuine misses (the MC would obviously notice, but the story never has him), worst first:
1. [MAJOR] **Lead poisoning.** The text walks Daniel up to Rome's lead water pipes and
   has him love them *"without reservation,"* and he is literally **"the emperor's
   water-man."** The most famous schoolbook fact about Rome (lead pipes / lead-sweetened
   *defrutum*) never crosses his mind. The setup makes the blind spot conspicuous.
2. [MAJOR] **City-scale fire prevention.** He vividly notices Rome is a firetrap ("goes
   up like kindling") and even *causes* a Subura fire, but only ever manages his own
   flames — firebreaks, a fire watch/brigade, or building codes (Great Fire 64 AD /
   London 1666) never occur to him, even once rich and warrant-backed.
3. [MINOR] **Charcoal-brazier carbon monoxide** indoors recurs; ventilation never
   occurs to him (arguably at the edge of teen recall).

Not misses: childbirth/puerperal-fever handwashing (no childbed scene exists), dentistry,
and soap (only in the author's brainstorm notes, never in the manuscript — a dropped
intention, per §13).

---

## Cross-cutting priority fixes (if the author wants a punch list)
1. [BLOCKER] Remove the live ch40 correctio; then do a book-wide **correctio sweep**
   (~25-37 instances) — it's the most-violated explicit prose rule.
2. [MAJOR] **Vary the scene-closing cadence** — the gnomic takeaway-button is the
   book's defining AI tell.
3. [MAJOR] **Reconcile the bible:** add Ulpia Severa / Lucanus / the keeper-chain to
   `02_characters.md`; fix the Ulpia↔Procula conflation in `03_timeline.md`; flip the
   23 REVISE QA verdicts only after confirming fixes (and fix the 8 part-header em
   dashes in `build_manuscript.py`).
4. [MAJOR] Decide whether the dropped tech intentions (distillation, soap, horse collar,
   spinning wheel/water-power, the "all tracks lead to Rome" line) are cut on purpose or
   restored — they're promised in the outline/bible but absent from the prose.
5. [MAJOR] Thin the "the way" (677×) / "looked at me" (91×) verbal tics.
6. [Consider] Dramatize at least one of the high-value uncreated threads (the gunpowder
   leak is the prompt's own priority) and give Crispus/Scaeva/Vibenius real exits.

## File index
- `analysis/qa_status.md` — QA verdict census (Q4)
- `analysis/manuscript_integrity.md` — em dashes, build script, ACCEPTED-vs-REVISE
- `analysis/prompt_adherence.md` — both .txt prompts (Q1)
- `analysis/characters.md` + `analysis/characters/range_*.md` — roster + adherence (Q5,Q6)
- `analysis/outline_fidelity/range_*.md` — prose-vs-brief per chapter (Q2,Q3)
- `analysis/prose_quality/range_*.md` — bad writing / AI tells / predictability (Q8,Q9,Q10)
- `analysis/repetition_and_tells.md` — phrase repetition with counts (Q7,Q11)
- `analysis/threads/opened_not_closed.md` — dangling threads (Q13)
- `analysis/threads/could_have_created.md` — uncreated threads (Q12)
- `analysis/threads/trains.md` — trains (Q15)
- `analysis/threads/easy_fixes_ignored.md` — ignored easy fixes (Q16)
- `analysis/history/divergence_ch01-30.md` + `divergence_ch31-53.md` — history (Q14)
- `analysis/chapters/range_*.md` — first-pass combined per-range audits (redundant cross-check)
