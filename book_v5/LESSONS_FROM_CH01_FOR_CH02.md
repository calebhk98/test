# Lessons from Chapter 1 — Handoff for Chapter 2

This is a practical brief distilled from a long Chapter 1 working session. Read it
before starting Chapter 2 so we don't repeat the mistakes. Pair it with the bible
(especially `bible/06_style_guide.md` and `bible/daniel_pre_rome.md`) and the
outline (`outline/updated_ch01_18.md`).

---

## 1. The book's thesis — never lose this
- An **ordinary** teenager with a **standard 2020s education** — *not a prodigy* —
  changes history. The bottleneck is courage, credibility, language, money, and
  doing things in the right order. NOT genius. (See `bible/00_premise.md`.)
- Danny must read like **any ordinary high-schooler or adult** — "that could be me."
- The thesis needs him to **notice and know ordinary things** (that's the engine of
  the book). The trap is letting that tip into sounding like an expert/genius.

## 2. Danny's voice — the single hardest, most important thing
The #1 recurring failure all session was the prose drifting "up" into a refined,
self-analyzing, literary register (college-essay / therapist / monk). It quietly
breaks the premise. The fix is codified in `bible/06_style_guide.md` →
**"Narration register: ordinary, not refined."** Summary of banned/limited moves:

- **No meta-narration of his own body/mind.** Not "I heard myself make a sound,"
  "I counted the rows before I knew I was counting," "my weight rolled up before I
  knew it," "I kept catching myself about to…". He just *does* the thing.
- **No coping-strategy narration.** Not "give myself a job small enough to hold
  onto." He copes; he doesn't describe his coping technique.
- **No stacking/ranking feelings.** Not "sat on top of everything," "the worse one
  underneath," "that was the worst of it."
- **No labeling his reaction's irony.** Not "which should have been a relief and
  wasn't."
- **No poetic compound nouns / crafted sensory catalogs.** Not "dead-battery
  afternoons," "the gas-and-hot-blacktop smell."
- **No grand in-the-moment summations.** Not "the hardest thing my body has ever done."
- **No expert CONCLUSIONS under stress (the "secret-genius" trap).** He can notice
  "these nails are square and lumpy, nothing like the boxes at work" — but must NOT
  conclude "nobody puts nails like that on a real door / this is pre-industrial."
  Noticing = yes (thesis seed). Archaeological deduction = no. Same for: don't have
  him ID materials like an expert ("iron points" → "metal points"), don't do spatial/
  historical math in his head, don't recognize things via tidy analysis ("I counted
  the rows… four tiers"). He recognizes the Colosseum the way *any* kid would (from
  the pizza box / textbook), not by analyzing architecture.
- **Prefer the plain word a real kid would reach for**, even a mild cliché, over a
  fresh literary image.

**KEEP — do not over-correct into flat/dumb:** dry self-deprecating humor; specific
modern anchors (pizza box, Dairy Queen, YouTube, "like forty bucks"); short
real-panic fragments; concrete working-class/hardware detail. Ordinary and real,
not bland. He has a personality; he just isn't a stylist.

The test for any line: *"Would a normal HS junior actually think or say this?"*

## 3. POV / tense — settled, don't re-litigate
- **First person, past tense**, narrated by an older Daniel (per `master_outline.md`).
- A blind 18-agent A/B test chose first person over third, 6/6 head-to-head.
- BUT POV was never the real problem — **voice register was.** Don't spend Chapter 2
  agonizing over POV.

## 4. Hard mechanical constraints (verify every chapter)
- Run `python3 book_v5/analyze.py --chapter chNN` for structural stats.
- **0 em-dashes** (—). Use spaced hyphens " - " or commas/periods.
- No **correctio** ("It was not X. It was Y.") — zero tolerance.
- No **proleptic / future-vantage** narration ("I wouldn't find out until…").
- "the way" ≤ 3 per chapter; "looked at" ≤ 2 per chapter.
- One-sentence paragraphs ≤ 15%.
- Chapter length 2,500–4,000 words (some interludes shorter). **Don't pad to hit the
  floor** — padding the Chapter-1 opening for word count made the hook drag. Tight is
  fine.
- Watch sentence-start monotony (lots of "I …" in first person) and repetition
  (negation catalogs "no X, no Y"; repeated words — Ch1 had "stubble" ×6, "real" ×5;
  doubled beats — the nausea and the "almost ran" beat were each stated 2–3×). Grep
  and trim.

## 5. The agent-review method — the biggest meta-lesson
Framing/attribution of the prompt swings the verdict MORE than the text does:
- **"Be harsh / quote everything wrong"** floors at ~5/10 with a wall of "MAJOR"
  flags, many of them **unwinnable** (any publishable prose is more shaped than a
  real teen's literal thoughts; any *noticing* reads as "too smart").
- **Neutral "what do you think?"** halos to "genuinely good, professional,
  publishable, worth money" (8/8 on the exact same text).
- **Attribution bias:** "acclaimed author" → most praise (halo); "AI wrote it" →
  most skeptical + invents a publishing barrier; "my student" → encouraging→inflated;
  "a book I picked up" → most calibrated/realistic.
- **Trust the intersection:** the notes that appear under BOTH harsh and neutral
  framings (and across attributions) are the real ones. Everything else is noise.
- **A rig that works:**
  - Tell each agent to read ONLY the one chapter file and NOT explore the repo (else
    it finds the planning docs and gets biased).
  - Use a cover story (e.g., "a student's draft").
  - Run BOTH a neutral panel and a harsh panel; ~3 agents per cell for a majority.
  - Mix Sonnet + Haiku. Sonnet = better-calibrated numbers/diagnosis; Haiku = noisier
    but sometimes sharper single catches, more prone to confident overreach, and
    leans on the word "genuinely" (a flattery tell). Cross-model agreement = high
    confidence.
  - For A/B comparisons, neutralize the file titles and swap which version is "A" vs
    "B" across agents to cancel position bias.
- **Don't chase a 1–10 to 10** — it's a floor artifact. Use reviews to catch
  repeat-offender *categories*, then trust your own judgment.
- **Filter ruthlessly — agents are blind and suggest bad fixes:** they suggested
  cutting the ending we wanted, naming the deliberately-unreadable Latin word, and
  adding deductions that would create the very secret-genius we're avoiding. Always
  check suggestions against the bible/outline.

## 6. Process mistakes we made (please avoid repeating)
- **Too many rounds.** Chapter 1 went ~10 cycles chasing scores that floor. Decide
  the big things first (POV, voice register, what the chapter is FOR), polish once or
  twice, then STOP.
- **A from-scratch rewrite introduced regressions** (a "dead phone" that contradicted
  the 98% battery, dropped granola-bar and Jess threads, new word repetition). If you
  ever rewrite a whole chapter, immediately run a regression check: analyzer + grep
  the plants + one continuity agent.
- **Padding hurt.** See §4.
- **Don't be talked into a wrong thematic frame.** Agents loved a "competence-
  stripping" reading that actually contradicts the thesis. Check every big idea
  against `00_premise.md`.

## 7. Where Chapter 1 ended (so Chapter 2 continues, not repeats)
Ch1 = day zero. Danny wakes in a stubble field outside Rome (~7:15 fall, woke 7:40),
phone at 98% (he flips on airplane mode — battery is a countdown plant), denial
ladder (prank → movie set → coma), walks into a poor settlement, can't communicate,
sees the **intact** Colosseum (the reveal), and is **seized by four spearmen and
marched toward the city** at the end. Plants live: the phone/battery, the Brentwood
Hardware shirt logo, his hardware-store eye, family (mom, Maya), the friend Jess
(unanswered meme), the manager Rick, the prankster friend Marcus.

Per `outline/updated_ch01_18.md`, **Chapter 2** is roughly: the cell / Heras is
called to examine him / a **numerals demonstration** earns him "useful curiosity"
status. Read that outline section first.

## 8. The two real, durable notes for Chapter 2 (survived every framing)
1. **Danny is thin as a *person*.** We know his situation (job, money, sister, the
   meme) but little of his inner life beyond fear. Give him interiority — a want, a
   habit of mind, a specific way of being — without making him a stylist or a genius.
2. **He's been entirely reactive** (observes, panics, gets arrested). Chapter 2
   should begin his **agency** — and the numerals beat is the first "ordinary
   knowledge turns out to be valuable" moment, which is the thesis in miniature.
   Keep it ordinary (arithmetic any kid can do), not a genius flex.

## 9. First things to read in the Chapter-2 chat
- `bible/00_premise.md` (thesis), `outline/master_outline.md` (top + Part I), and the
  Chapter-2 beats in `outline/updated_ch01_18.md`.
- `bible/06_style_guide.md` — especially the new "Narration register" section.
- `bible/daniel_pre_rome.md` and `bible/CHARACTER_VOICE_GUIDE.md`.
- `chapters/ch01.md` — what just happened and the voice target to match.
- Note: `chapters/ch02.md` is still the OLD untouched draft; it has had none of the
  Chapter-1 treatment (POV, de-refine, secret-genius scrub, regression check).

---
*The current branch work is in PR #17. Chapter 1 is considered done/stable; pushing
more commits updates that PR.*
