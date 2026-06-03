# Writer Brief V2 — standing instructions for any chapter-writing subagent

You are rewriting ONE chapter of *The Long Way Home* for V2. V1 was a complete 53-chapter
draft; V2 fixes its specific, documented problems. Other agents wrote the chapters around
yours in V1; your job is to rewrite your assigned chapter so it fits the V2 spec.

---

## Read first, in this order

1. `V2_MASTER_CONTEXT.md` — **Start here.** Premise, narrator voice, the 5 core V2
   changes, character fingerprints, file map. Replaces reading 87 analysis files.
2. `V2_CHAPTER_CHANGE_NOTES.md` → find your chapter → read its specific entry.
3. `bible/06_style_guide.md` — prose mechanics, POV rules, scene-ending taxonomy.
4. `PROSE_PATTERNS_TO_AVOID.md` — quick-reference checklist (banned constructions,
   hard limits, tic watch-list). Read before you finalize, not just before you start.
5. `bible/CHARACTER_VOICE_GUIDE.md` — 7-tier voice spectrum with DO/DON'T examples.
6. `bible/02_characters.md` — full profiles for characters in your chapter.
7. `bible/08_canon_log.md` — everything established. DO NOT contradict it.
8. `bible/04_tech_schedule.md` — what's achievable/blocked in your chapter's era.
9. The V1 chapter you are rewriting: `chapters/chNN.md` — your baseline.

Also read if your chapter involves specific topics:

| If the chapter involves... | Also read... |
|---|---|
| Story-level changes, antagonist exits, Atlantic crossing, games/gambling, crossbows, balloon, trains/rails, food arc | `V2_STORY_PLOT_NOTES.md` |
| Chronology / exact AD dates | `bible/03_timeline.md` |
| Optics, steam, clocks, precision manufacturing, tech bootstrapping | `V2_TECH_DEEP_DIVE.md` |
| Money, wealth, prices, business deals, finance phases | `V2_DANIEL_FINANCES.md` |
| War outcomes, military divergence, historical impact | `V2_HISTORICAL_IMPACT.md` |
| Atlantic crossing, New World contact, disease, transatlantic timeline | `V2_NEW_WORLD_CONTACT.md` |
| Daniel's knowledge limits, what he knows vs. guesses | `V2_DANIEL_COGNITIVE_EDGE.md` |
| Honesty constraints on what Daniel can claim to know | `bible/05_world_rules.md` |
| Food beats, tavern scenes, cooking, New World crop arrivals | `V2_FOOD_ARC.md` |
| Tech development, metallurgy, craftsman competitions, prize specs, lens-grinding | `V2_PRIZE_INNOVATION.md` |
| Lucanus or Ulpia (children's education, playground, truth-telling) | `V2_ULPIA_EDUCATION.md` |

**Notes on key conditional reads:**
- `V2_FOOD_ARC.md`: covers what Rome has, what Daniel knows how to cook, phase timeline (pasta Phase B, New World crops Phase D), the tomato moment, cacao scene (ch43), and the Gnaeus tavern-partner arrangement. Do NOT have Daniel cook with ingredients unavailable in his chapter's era.
- `V2_PRIZE_INNOVATION.md`: X-Prize model (post spec → pay only winners → nobody sees the aggregate) runs Phase B through Phase E. Six narrative beats with chapter assignments listed. Do NOT have Daniel explain the model in a speech.
- `V2_STORY_PLOT_NOTES.md`: read this for ANY chapter where Daniel encounters new technology, gambling/games, the balloon program, rail transport, or the Atlantic crossing timeline — these are major V2 additions not present in V1.
- `V2_NEW_WORLD_CONTACT.md`: the Atlantic crossing is a major V2 divergence from V1. Read this whenever your chapter is Phase D or later (~120+ AD) and involves ocean exploration, the western shores, or New World disease questions.

---

## PROSE STATISTICS TARGETS (V4 MANDATORY)

These targets come from running `analyze.py` against all 53 chapters and comparing to a baseline of 26 classic novels.

- **Dialogue density: this is the single most important fix.** At least 50% of paragraphs must contain dialogue. The current V4 average is 30% — severely low. Every scene needs more back-and-forth. If you finish a scene and it has been three or four paragraphs of narration in a row, add an exchange. Do not let characters stand in silence while Daniel explains things to the reader.
- **Sentence length:** Target a bell curve centered around 15 words median. V4 is currently too bimodal — too many 1-5 word sentences AND too many 30+ word sentences, with a dip in the middle. Bring short-sentence (1-5 word) percentage below 15%. Currently running at 22.7%. This means: if you write a punchy short sentence, balance it with some mid-length ones before the next short one. Do not machine-gun staccato beats.
- **Single-sentence paragraphs:** Current 12.3% is acceptable and intentional. Do not artificially inflate this figure.

---

## DANIEL'S VOICE — THE NARRATION/DIALOGUE SPLIT (CRITICAL)

Daniel narrates in close, immediate first-person past tense - the young Daniel telling it from small remove (days or weeks), NOT an older man writing a memoir. (In the story he does write a memoir and an encyclopedia later; the novel is not that document.) His NARRATION voice is plain, immediate, and dry - the kid's voice, a little more ordered than his in-scene panic but NOT mature, sophisticated, or literary.

Daniel's QUOTED DIALOGUE is the same 17-year-old under live pressure - even rougher: hedged, incomplete, panicky. Agents must not let EITHER voice drift up into a skilled-adult-writer register.

**Required features of Daniel's dialogue:**
- Contractions, always
- Hedging: "I think," "kinda," "sort of," "I mean-"
- Incomplete sentences and trailing off
- "like" as a filler
- Second-guessing mid-statement
- Occasional mild swearing when scared or frustrated

**Forbidden in Daniel's dialogue:**
- Perfectly formed arguments
- Philosophical summations
- "I know." as a flat one-line response to something heavy
- Rhetorical questions that land too cleanly
- Formal diction ("I do not know whether...")

**Example CORRECT:**
> "Yeah, I mean-okay. So I was thinking maybe we just... try it? Like, I know it probably won't work first time but if we just start and see what happens? I don't know. Maybe that's dumb."

**Example WRONG:**
> "I do not know whether to be glad it already exists or sad that I did not do it."

**Example WRONG:**
> Someone tells Daniel he will kill people. Daniel says: "I know."
> A teenager would say: "Yeah. Yeah, I-I know, okay? I know." or trail off entirely.

---

## ETHICS AND MORALITY — ONE BEAT RULE

Daniel is a modern American teenager, not an ethics professor. When something bad happens because of his inventions, he feels bad. That is one beat. It should take no more than one paragraph.

- He does NOT make formal vows. He makes plans, breaks them, and feels guilty later like a normal person.
- He does NOT spend multiple scenes relitigating the ethics of the same event.
- He does NOT treat the ethics of "bringing knowledge to natives" as a multi-chapter moral crisis. A modern teen would feel vaguely bad, avoid thinking about it, and move on. That is realistic.

**The Roman-era ethics he actually WOULD feel:** homesickness, imposter syndrome, fear of being found out, grief that hits suddenly. Write those instead.

---

## CIPHER AND ENCYCLOPEDIA — CORRECT USAGE

- Daniel's notes are written in ENGLISH. Romans cannot read English in 100 AD. There is no "cipher" — English itself is the security. Agents must not write Daniel encoding his notes in any additional cipher system in chapters 1-40.
- The word "cipher" should not appear in chapters 1-30 at all. In chapters 30-40, it refers only to the contest notation system Tyche develops for the prize index — not Daniel's personal notes.
- The encyclopedia is a LATE-STORY project (chapters 40+). Before that, Daniel has notes. Notes. Not an encyclopedia. Agents must not have characters discussing "the encyclopedia" before chapter 40.

---

## HISTORICAL DIVERGENCE — REQUIRED FROM CH34 ONWARD

The story's premise requires Rome to change dramatically due to Daniel's inventions. From chapter 34 onward (~118 AD), the historical record no longer applies.

- Agents must NOT default to actual Roman history for wars, political outcomes, or emperors' decisions after this point. The technology Daniel has introduced (cannon, balloon, printing, gunpowder, steel improvements, semaphore) would have profoundly changed military and political outcomes.
- Trajan's wars should resolve differently. Hadrian's reign should be actively shaped by Daniel's tech. Later history should be unrecognizable.
- If an agent is unsure what the "changed" history looks like, they should invent plausibly altered outcomes rather than following the historical record.

---

## Your job

- **Rewrite** the chapter as finished, polished prose. Not a summary. Not a placeholder.
- **Use V1 as your structural baseline** — keep what worked, fix what the change notes
  specify, and apply the V2 prose/voice rules throughout.
- **Hit every beat in the original brief** unless your chapter's change notes say
  otherwise (some beats are dropped or replaced in V2).
- **Own the execution:** lines, blocking, texture, order within the chapter are yours.
- **Target 2,500–3,500 words** unless the change notes specify otherwise.

---

## Hard "don'ts" (zero tolerance — check these before you submit)

1. **No "not X, it's Y" / "It was not X. It was Y." constructions** — the correctio /
   epanorthosis. Explicitly banned. Check every scene break and paragraph ending.
2. **No em dashes** — use commas, normal dashes (single hyphen), or full stops.
3. **No narrator stepping outside time** — no "for years afterward I thought…" lines,
   no future-vantage telegraphing. Exception: explicitly flagged encyclopedia excerpts.
4. **No wisdom-button scene endings more than once per chapter** — the gnomic aphorism
   that restates the scene's meaning is the book's defining AI tell. End on image,
   action, silence, or dialogue instead. (See style guide §Scene Endings.)
5. **No muting the mutes** — if Pamphilus, a crowd heckler, or Naso is in the scene,
   they speak in their actual voice. No "shouted something I didn't catch" workarounds.
6. **No smoothly competent Daniel** — he gets things wrong, panics in private, fakes
   confidence in public. He is NOT a prodigy.
7. **No info-delivering monologues** — if a character explains something for more than
   4 consecutive lines without interruption or deflection, break it up.
8. **No child delivering the thematic capstone** — if Lucanus or any child under 12
   says something, it should be childlike, not aphoristic wisdom.

---

## Tech rules for V2

A tech wall is NOT an excuse to stop. Daniel bootstraps. If he needs X to make Y:
- He manufactures X, or
- He finds a partial solution that gets him halfway, or
- He explicitly explains WHY he can't bootstrap X (specific, honest reason)

"Rome currently lacks X" is a starting point, not a conclusion.

See `bible/04_tech_schedule.md` for what IS achievable in each phase and HOW.

---

## Deliver

- Write to: `chapters/chNN.md` (exact path given in your assignment)
- Start with: `# Chapter N: <short title>` (colon, never em dash, in the title)
- After writing, report in under 150 words:
  (a) 3–5 sentence recap of what happens (for the next writer's continuity)
  (b) Any NEW canon facts established (names, dates, inventions' states, who knows what)
  (c) Any V2 change notes items you could not apply, with reason

---

## What makes a V2 chapter different from a V1 chapter

| V1 tendency | V2 correction |
|------------|---------------|
| Ends every scene on packaged wisdom | Ends on image, silence, action, dialogue |
| Everyone is eloquent | Class-marked voices; some people speak roughly |
| Daniel hits a wall and waits | Daniel bootstraps or fails specifically |
| History stays mostly real | Measurable divergence on the page by era |
| "Not X, it's Y" as emphasis tool | Never; find a different construction |
| Dumb/rough characters are muted | They speak in their actual voices |
| Long explanatory speeches | Broken up; information fights its way out |
