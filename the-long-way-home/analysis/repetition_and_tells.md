# Repetition & AI-Tells Audit — *The Long Way Home*

Manuscript: `/home/user/test/book/manuscript/The_Long_Way_Home.md`
Length: ~197,455 words, 53 chapters (concatenated in one file).
Method: `grep -o | wc -l` true-occurrence counts (NOT line counts), n-gram extraction via
`tr/sort/uniq` pipelines on the lowercased text, plus targeted reads of chapter openings/closings.
All counts below are whole-book unless noted.

**Headline:** This manuscript is unusually CLEAN on the obvious beat-tag clichés (nodded/sighed/
chuckled ~ 0). The dialogue-tic problem has been replaced by a deeper, harder-to-spot problem: a
small set of **distinctive sentence-shapes and abstract-noun constructions reused hundreds of times**
across all 53 chapters. The voice is consistent to the point of being formulaic.

---

## SECTION 1 — PHRASE / MOTIF REPETITION

### 1a. The dominant verbal tics (unintentional, book-wide)

| Phrase / shape | Count | Notes |
|---|---|---|
| `the way` (all uses) | **677** | ~13 per chapter, evenly spread. Of these ~563 are the "X the way Y" shape. |
| `looked at me` | **91** | Eye-contact beat used as connective tissue. Appears in **34 of 53** chapters. This is the book's de-facto replacement for nodded/sighed. `he looked at me` = 55. |
| `the shape of` | **59** | Abstract-noun tic. In **36 of 53** chapters. Completions: shape of it (19), shape of the world (9), shape of what I (4), shape of the thing (4), shape of a thing (4). |
| `the whole of` | **63** | Summary tic: the whole of it (22), the whole of the (11), the whole of what (8). Pairs with `that was the whole` (17) as a scene-summarizing close. |
| `of a man who` | **38** / `a man who has` (29) | Gnomic third-person generalization ("a man who sells the army…", "a man who has never once…"). |
| `which is to say` | **21** | Explanatory self-correction tic ("…badly, which is to say in circles"). |
| `the way you look at a [X]` | **17** | A reusable sentence template. Completions: a thing (4), a dog (2), a tool, a sum, a parrot, a man, a machine, a horse, a hand, a door, a child. |
| `looked at me the way` | **14** | The two tics above fused. |
| `for the first time` | **16** | |

**Verdict:** "the way…", "looked at me", "the shape of", and "the whole of" are genuine
unintentional tics, not motifs. They recur at a near-constant per-chapter rate, which is the
tell-tale signature of a uniform generative habit rather than authorial emphasis. The book even
**ends** (Ch 53, final sentence) on the single most-repeated template: "…looked west at the shore,
**the way you look at a thing** you have only ever drawn."

### 1b. Intentional motifs (these are FINE — deliberate, tracked across the arc)

| Motif | Count | Judgment |
|---|---|---|
| `the new figures` | 39 | Deliberate plot motif (the numerals). Concentrated, not uniform. Keep. |
| `the little ones` | 17 | Deliberate (the enslaved children / students). Keep. |
| `the man who flew` | 4 | Deliberate (his public identity; a Part title). Keep. |
| `the phone` | 22 | The relic motif. Deliberate; bookended ritual ("I put the phone in my pocket"). Keep. |
| the strap / wax tablet relic | tablet 21 | Recurring object-rituals at chapter closes (the dead man's strap, the tablet). Deliberate, mostly effective. |

These are controlled and earn their repetition. Do not flatten them while fixing 1a.

### 1c. Beat-tag clichés (book-wide) — LOW, the bright spot

True counts: nodded **0**, sighed **0**, chuckled **0**, shrugged **2** (+ shrug 1),
grimaced **0**, smirked **0**, frowned **0**, furrowed **0**, winced **1**, swallowed **4**.
`let out a breath` = 2. `something in his face` = 1; `something in her/his eyes` = 0.
`not because … but because` = 0.

This is excellent and well within the style guide. The classic AI dialogue-punctuation problem is
essentially absent. The repetition problem has migrated into the gnomic/abstract register instead
(Section 1a) — that is where the effort should go.

### 1d. Uniform-hedging words (book-wide)

| Word | Count | Judgment |
|---|---|---|
| almost | **59** | Highest hedge. Worth spot-thinning. |
| `a little` | **61** | Mostly quantity ("a little water"), some hedging. Mixed. |
| maybe | **42** | In-voice for a modern teen; acceptable but watch density. |
| of course | **23** | |
| in a way | **16** | |
| probably | 11 | |
| perhaps | **5** | Notably LOW — good; avoids the classic AI "perhaps." |
| seemed / seem | 2 / 2 | Very low — good. |
| somehow | 5 | |
| `in some ways` | **0** | |

**Hedging verdict: NOT the flat-uniform AI pattern.** "perhaps" (5) and "seemed" (2) — the two
canonical AI hedges — are near-absent. Hedging here is concentrated in voice-appropriate words
(maybe, almost, a little) and varies by scene. This is a deliberate, controlled voice, not uniform
caution. Only "almost" (59) is high enough to thin.

---

## SECTION 2 — AI TELLS (book-wide)

### 2a. "wasn't X. It was Y." negation/correction construction (epanorthosis)

The style guide and `Bad writing.txt` BAN this ("It's not X, it's Y"). It is present:

- Strict pattern `(wasn't|was not|isn't…) … . (It/That/This) was/were/is` = **25**.
- Looser `… . It was` after a negation = **37**.

Examples: "It wasn't conversation. It was two men passing a stylus back…"; "It wasn't cloth. It was
reasoning my way to why…"; "It wasn't a thank you. It was an order."; "It was not a system. It was
four women and a wharf…" These are exactly the banned correctio device. **25–37 instances is the
single clearest rule-violation in the book.**

### 2b. Tricolon-of-short-sentences (faux-profundity cadence)

`X. Y. Z.` runs of ≤3-word sentences = **19**. Examples: "No ringing. No operator. Nothing.";
"Spy. Lunatic. Runaway slave."; "Long. Short. Same thing."; "Get the steel. Get the clock. Cross
the sea."; "And it passed. The fist opened. The air came." Also appears as a closing cadence
(Ch 13 "The same orange. The same lick of it…"; Ch 43 "The lamps. The brazier banked. The…").
Used as a rhythm device 19 times — recognizable, dilutes when overused.

### 2c. Scene-closing aphorisms that restate the takeaway

Largely AVOIDED. Read of all 53 chapter closings shows most end on a concrete object/action
("I put the phone in my pocket"; "He took the lamp with him. The bar dropped."; "The coals settled
and dimmed…"). This is exactly what the style guide wants. A handful append meaning
("which from Marcia was a benediction", Ch 26) but these are light and in-voice. Not a systemic
problem. The `the whole of it` / `that was the whole of it` summary tic (Section 1a) is the closest
thing to appended-takeaway and is the one to watch.

### 2d. Narrator stepping outside time — WELL CONTROLLED

The style guide forbids "little did I know." Counts confirm compliance: `I would learn` = 1,
`years later` = 0, `I didn't know it then` = 1, `I would later` = 0, `I know now` = 1,
`looking back` = 1, `the last time` = 2. Retrospective foreshadowing is essentially absent. Good.

### 2e. Sentences that announce emotional weight

`something in his/her face/eyes` = ~1 total. Not a pattern. The book shows behavior rather than
naming feeling — consistent with the guide.

### 2f. Chapter OPENING templates — REPETITIVE across the 53

This is a real structural tell. At least ~23 of 53 chapters open on one of a few templates:

- **"[Subject] came…"** (~11): "They came for me…" (Ch 3, 4), "The yard came with a smell…",
  "The soldier came on a dry blue morning…", "The summons came…", "The order came in two halves…",
  "The word came up the road…", "The temple came to the wharf…", "The accounts came to me out of
  Judaea…", "The news came to me at my own bench…", "The gears came in a cedar box…".
- **"There is a [silence/sound/thing/step]…"** (4): Ch 23, 24, 43, 47 — a gnomic present-tense
  generalization opener.
- **"The first… / The thing…"** (8): "The first thing I got wrong…", "The thing about a good idea…",
  "The thing nobody tells you about…", "The thing I remember…", "The first I heard…".

The "[X] came…" and "There is a thing that…" openers in particular read as a generative habit.
Recommend varying ~half of these.

---

## WORST OFFENDERS — shortlist (fix priority)

1. **`the way` / "X the way Y" shape — 677 uses (~13/chapter).** The defining tic. Includes the
   reusable template `the way you look at a [thing/dog/tool…]` (17) and `looked at me the way` (14).
   The whole book even ends on it.
2. **`looked at me` — 91 (in 34/53 chapters).** Eye-contact used as connective punctuation; the
   stealth replacement for beat-tags.
3. **`the shape of` — 59 (in 36/53 chapters).** Abstract-noun tic ("the shape of it/the world/the
   thing").
4. **`the whole of` — 63 + `that was the whole` — 17.** Summary tic, doubles as appended-takeaway.
5. **"wasn't X. It was Y." correctio — 25 strict / 37 loose.** Explicitly banned by the style doc.
6. **`of a man who` / `a man who has` — 38 / 29.** Gnomic generalization habit.
7. **Chapter-opening templates — ~23/53** follow "[X] came…", "There is a [thing]…", or
   "The first/thing…".
8. **`which is to say` — 21** explanatory tic; **tricolon ≤3-word runs — 19** faux-profundity.

**Do NOT touch** the deliberate motifs (the new figures 39, the little ones 17, the phone 22,
the man who flew 4) or worry about classic hedges/beat-tags — those are already clean
(perhaps 5, seemed 2, nodded 0, chuckled 0).
