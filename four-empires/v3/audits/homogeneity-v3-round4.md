I have everything. Report follows.

---

# Homogeneity check — v3, turn 525–550

Four test documents against four human-written controls (500–525). Independent reading first; comparison with the prior audit at the end.

## Verdict: **88% probability of one author**

Against the prior check's 85%. That 3-point difference is inside my own noise and should not be read as a finding. **The finding is that four rounds of audit and correction moved every homogeneity metric by zero, and moved two specific things backwards.**

---

## 1. Mechanical signals

| Metric | Control (4 humans) | Test (4 agents) |
|---|---|---|
| Length | 3,535–4,512 words — **24.0% spread** | 13,128–14,345 — **8.8% spread** |
| Mean sentence length | 21.9 / 35.1 / 28.9 / 33.5 — **1.60× spread** | 22.6 / 26.9 / 26.5 / 24.0 — **1.19×** |
| Sentence-length SD | 12.1 / 22.7 / 17.4 / 20.3 | 13.8 / 17.5 / 15.7 / 15.4 |
| Numbers per 1k words | 17.3 / 0.5 / 8.0 / 1.6 — **34.6× spread** | 34.4 / 40.6 / 19.8 / 30.8 — **2.05×** |
| Affect per 1k words | 3.96 / 1.26 / 3.27 / 4.21 | 0.63 / 0.15 / 0.86 / 0.78 |
| **Syntactic-construction CV** (15 constructions) | **1.149** | **0.355** |

Two things the prior audit did not measure:

**The register convergence is directional.** Egypt's sentence length is unchanged from its human control (21.9 → 22.6). Rome fell 8.2 words, Maurya 9.5, China 2.4. The other three collapsed *toward the Egyptian clipped-declarative register*, not toward a neutral midpoint.

**There is a shared syntactic fingerprint below the lexicon.** Five constructions appear in none or one of the four human documents and in **all four** agent documents at comparable rates (per 10k words):

| Construction | Control (E/R/C/M) | Test (E/R/C/M) |
|---|---|---|
| `, which is` appositive | 0 / 0 / 6.9 / 0 | 17.5 / 21.2 / 18.9 / 11.0 |
| `stands at` (stative report) | 0 / 0 / 0 / 0 | 5.4 / 3.7 / 4.2 / 2.8 |
| `against <number>` comparative | 0 / 0 / 0 / 0 | 4.7 / 4.4 / 3.5 / 3.5 |
| `what X does/did/changed` cleft | 0 / 0 / 0 / 0 | 2.7 / 2.9 / 2.8 / 2.1 |
| `entered / recorded / logged` | 2.8 / 2.5 / 6.9 / 2.2 | 19.5 / 10.2 / 14.7 / 18.6 |

The em-dash purge worked on one layer of tell. This is the layer underneath it, and `register-check.sh` does not test for any of it.

Rome is the largest single drift from its own control: **0.5 → 40.6 numbers per thousand words, an 80× increase.** Human Rome was a court that argued and did not count. Test Rome counts obsessively. That is not Rome becoming more itself.

---

## 2. Affect — does any court feel anything?

**No. Not one, not once.** I extracted every affect-vocabulary hit in context. In the test set, **100% are false positives**:

- **Rome** (2 hits): "spent in anger" (idiom for firing a gun), "relief" (troop rotation). Rome stormed nineteen cities, killed 46,000 people, seized 240,000, and watched two million die. Temperature: zero.
- **China** (11 hits): "relief valve", "relief columns", "famine relief", "bitter seed" (cacao), "aggrieved" (political-analytic, of the great families).
- **Maurya** (11 hits): "flush" (hull plating), "temper" (of a lock spring), "famine relief", "grievance" (strategic term of art).
- **Egypt** (7 hits): five are "grievance" as a term of art; two are the inherited doctrinal phrases "the standing fear" / "the founding fear".

The control differs **in kind**, exactly as specified:

- **Maurya (hot, wounded):** *"a court that was miffed to the point of grief and moving at the speed of injured pride"*; *"grown heartily sick of it"*; *"the flat and hated answer"*.
- **Egypt (elegiac):** *"The mood in the chamber is grief over the squandered century-long head start, not embarrassment over the leak."*
- **China (self-auditing pride):** *"The court feels real vindication... tempered rather than triumphant... A court that has just declared its own monopoly gone is not drunk on its own success."*
- **Rome (cold, with propaganda):** *"Rome trumpets this loudly and largely truthfully"*; *"the mortality... soft-pedalled in the telling"*.

Four temperaments versus four instances of none. And the collapse is worst where the control was hottest: Maurya went from 17 affect hits (all genuine, all psychological) to 11 (all machinery). **This is the single strongest tell in the set, and it is worse than a level difference — it is the absence of a dimension.**

---

## 3. Convergent invention

All four courts built the same apparatus in the same twenty-five years, with no shared tradition:

| Institutional invention | Egypt | Rome | China | Maurya |
|---|---|---|---|---|
| Standing sighting order: record exactly, do not close, do not conclude in the field | ✔ Item 6/10 | ✔ Canaries/Madeira watch | ✔ standing order 543 | ✔ First Degree |
| Printed standard return justified because a nil return is informative | ✔ register office | ✔ "the null goes on the file" | ✔ "whether or not there is anything to enter" | ✔ printed register form |
| Written contact ladder drafted *before* any contact | ✔ | — | ✔ | ✔ Five Degrees |
| Enumerated withholding list published beside a disclosure | ✔ | ✔ | ✔ | ✔ |
| Deliberate deception run, true position recorded, cost priced in own file | ✔ two falsehoods | announces the refusal | ✔ "the bluff of this period" | ✔ "an overstatement the court made knowingly" |
| Contact-disease / mortality discipline adopted this turn | ✔ quarantine of contact parties | ✔ distance rule 544 | ✔ quarantine extended 534 | ✔ mortality registers 528 |
| Interchangeable parts / master gauges / one pattern | ✔ | ✔ | ✔ | ✔ |
| Names the losing faction and records that its office keeps standing | ✔ | ✔ | ✔ | ✔ |
| Own inference explicitly flagged as inference | ✔ | ✔ | ✔ | ✔ |
| Refuses to project a falling figure forward flat | — | ✔ | ✔ | ✔ |

Eight of eleven distinctive epistemic moves are 4/4. In the control, none of them appears in more than one document. Three courts writing a standing escalation ladder for an unvisited coast in the same generation is not a coincidence; four courts independently building the *shown-versus-found* epistemology and stating it explicitly rather than practising it silently is a shared mind.

---

## 4. Fallibility

The test asked for propaganda, an unexamined assumption, a self-serving account, a suppressed number, or a confident claim never qualified. The set contains **almost none of it**, and every candidate is pre-hedged at the point of statement:

- Maurya asserts Egypt sabotaged its research — then triple-hedges: *"this court's reading and may be wrong"*, *"this court's inference about a foreign court's purpose"*.
- Maurya's most doubtful number (22M revenue over 900,000 people, 24.4 paṇas/head against the empire's 24.9) is not suppressed but **volunteered, computed, disbelieved, and flagged provisional** with a re-count ordered.
- Rome's largest failure — the west running 110M short with gold thinning and tribute halving — is stated more baldly than any Roman would state it.
- China's bluff on the far coast is fully self-diagnosed, including *"what would break it"*.

Three genuine blind spots do exist, and they are the best material in the set:

1. **Egypt believes its plant-path misdirection worked.** It calls it *"the same instrument"* as the coffee deception and says *"the council is content to lose some of them."* Egypt does not know Maurya closed the programme in 527, named it as sabotage, and reported it to Rome in 530. Real dramatic irony across documents.
2. **Maurya exports a hedged inference as a diplomatic instrument** — the sabotage warning goes to Rome as a warning despite being marked "may be wrong". That is a court acting on a belief it has told itself is uncertain, which is exactly how real archives work.
3. **Rome carries forward an unexamined inherited premise** — *"the crossing and the island fevers were assessed in the previous turn as not severe and nothing since has changed that"* — in a document that re-examines everything else.

But no document contains a **suppressed number**, **propaganda in its own voice**, or **a confident claim it fails to qualify at the point of stating it**. Four states, four continents, four archives, and none of them fools itself once. That is the deepest homogeneity in the set, deeper than the prose.

---

## 5. Coverage and length

Length spread **8.8%** against the control's **24.0%** — the test set is 2.7× more uniform.

Coverage is *not* fully symmetric, and this is real credit: Egypt writes nothing on literacy/schooling and nothing on religion or caste; Rome writes nothing on electricity; China nothing on religion. But 11 of 16 domains are covered by all four, and every document carries a full fiscal accounting, a research programme table with headcounts, a territory section split held / surveyed-not-held, spy taskings with cover and network age, and quoted outbound letters. The human control has none of that symmetry — human Rome gives no revenue, no population and no territory at all.

**Note on the scaffold:** the five-block scaffold (INCOMING / Documents received / Intelligence returns / Technical assessments / MESSAGES OUT / SPY TASKINGS / RESEARCH / TERRITORY) is **externally mandated** by the coordinator notes, so it should be discounted as authorship evidence. It should *not* be discounted as a homogenising force — see §7.

---

## 6. Residual tics — genuine apparatus or one apparatus relabelled?

**The labels are genuine. The apparatus is one.**

Both tics are inherited from the human controls, which is decisive on the narrow question: `Accepted cost:` appears once in **human** Egypt (line 110); `Read cold` appears twice in **human** China. Neither appears in any other document in either set. So these are legitimate per-court inheritance, not invented uniformity, and the prior audit's recommendation to *delete* `Cold reading:` outright would be correcting in the wrong direction.

But they do only two jobs between them, and **all four documents do both jobs**:

**Job A — discount your own observation:**
- Egypt: *"The council enters a caution against its own figures... A number a man is shown is not a number he has found... The counts stand as floors and are not to be treated as measurements."*
- China: *"Cold reading: a counted position is a displayed position, so the count is a floor and not a total."*
- Rome: *"It stands in the file as the programme's explanation and not as a finding"*; *"a guess made from empty buildings"*; *"the null goes on the file."*
- Maurya: *"The establishment's interpretation, entered as interpretation"*; *"The treasury does not believe that and cannot correct it."*

**Job B — take the decision, then price it:**
- Egypt: *"Accepted cost:"* (×4) and *"the cost is entered rather than argued away."*
- China: *"The risk accepted is plain"*; *"That is the price paid and the court paid it knowingly."*
- Maurya: *"The cost of the overstatement is recorded with it"*; *"It records the cost."*
- Rome: *"the fiscal conservatives moved in 536 to cap the charge and were beaten. The office that gained standing across both defeats is..."*

**Assessment: four labels on one apparatus.** The visible tic is the least of the problem; killing the labels would hide the convergence rather than fix it. The frequency is the fixable part — Egypt uses `Accepted cost:` four times in one document, which is what makes it read as a stamp rather than a habit.

---

## 7. Has the loop helped? — **Sideways, and backwards on the two things it touched**

The prior audit was written at commit `e45443f` (04:16), measuring the state at `25de951`. Since then the documents have been through a letters audit, three tech re-verify passes, and three INCOMING passes, adding **6,817 words across the four**.

| | At audit (25de951) | Now (HEAD) |
|---|---|---|
| Words E/R/C/M | 12,613 / 12,437 / 12,191 / 13,258 | 14,889 / 13,668 / 14,269 / 14,490 |
| Length spread | **8.5%** | **8.5%** |
| Affect /1k E/R/C/M | 0.50 / 0.08 / 0.08 / 0.31 | 0.42 / 0.08 / 0.29 / 0.28 |

**Zero movement.** Nearly seven thousand words of correction changed nothing measurable.

Worse, two changes ran the wrong way:

1. **The audit's own strongest counter-evidence was destroyed thirty minutes after it was written.** The audit's stated reason for 85 rather than 95 was that *"the Maurya find a cairn with a squared timber... and Egypt — which describes its survey squadron exhaustively — never mentions planting it."* At `115b195` (04:46) the **letters audit** added Egypt's 534 landing, the eleven days, the refuse, the cairn, and the squared timber — plus a letter to India volunteering it and offering to take it down. The asymmetry is now perfectly reconciled. A consistency pass, working correctly and blind to the homogeneity finding, deleted the evidence for independence.

2. **A fifth identical block was added to all four.** The audit's recommendation #6 was to *vary* the four-part scaffold because it *"is buying a large share of the homogeneity for free."* The loop then added an identical `INCOMING / Documents received / Intelligence returns / Technical assessments` block to all four documents (`235ab69`, `1daf6a3`, `c0fcd5a`) — mandated for good operational reasons, but it made the scaffold *more* uniform, not less.

**The structural lesson: this loop has no homogeneity brake.** Each corrective pass optimises a local property (letters consistent, technology verified, distribution has a landing zone) and each one tightens the set. Nobody measured the spread before and after.

---

## 8. Strongest counter-evidence for genuine independence

A fair report has to give this, and it is stronger than the prior audit allowed:

1. **A hard, unresolved factual contradiction between two documents.** Rome: *"Twenty-five years passed. Nothing was received. No reply came."* Maurya: *"The account was written in 528, struck and sealed in 529, and carried west in 530."* Rome then argues four readings of the silence and lands on *"twenty-five years of silence is a decision"* — which is flatly false, and Rome cannot know it. Maurya reads Rome's non-answer as patience. Neither resolves it, and each acts on its own wrong reading. A single author usually cannot resist fixing this.

2. **Genuinely partial and complementary observation.** Egypt sees Indian hulls with *"a row of shuttered ports cut low along each side whose purpose the officers could not name."* Maurya sees Egyptian hulls with *"no port, no opening, no lid, no shutter... from stem to stern"* — and orders its officers not to report them unarmed anyway. Each side is wrong in its own direction, and the errors are not symmetric.

3. **Numeric disagreement on shared events.** Egypt logs the beach display on **eleven** occasions; Maurya records **five** Second Degree events. Egypt counts *"not fewer than thirty-one works"*; Maurya holds fifty-seven majors plus 420 lesser stations. Egypt's floor discipline is vindicated by a number it does not have.

4. **Real format and unit divergence, consistently sustained.** Numbered council Items with a confidence-class preamble (Egypt); continuous narrative with Latin offices — *curatores*, *magister classis*, *legatus*, *praefectus* — and two fiscal tables (Rome); topical memoranda with bold sub-labels and percent-of-revenue accounting (China); past-tense reign chronicle with blockquoted "The reasoning" boxes, Sanskrit toponyms and an Appendix A row (Maurya). Talents / HS / tonnes of silver-equivalent / paṇas, each with its own arithmetic idiom.

5. **Rome has no confidence apparatus at all.** No firm/reported/rumor tagging, no floors, no cold readings — it argues instead. It is the least generic document in the set and the closest to a real archive.

6. **Genuine coverage gaps.** Egypt is silent on literacy and on religion/caste; Rome on electricity; China on religion.

This is why the number is 88 and not 95.

---

## 9. Recommendations for the next generation, by yield

### Cross-cutting

1. **Mandate affect by *kind*, not by level, and make it causal.** Assign each court a named temperament and require it to *distort a decision* — a court that reaches a defensible conclusion for an indefensible reason. The human Maurya is the model: *"The realm would afterward call the decision a logical one, and in its bones it was, but it was reached by a court that was miffed to the point of grief."* Acceptance test: strip proper nouns from a paragraph and see whether a reader can name the court from temperature alone. Today they cannot.
2. **Install a homogeneity brake in the loop itself.** Measure length spread, affect, mean sentence length and syntactic CV before and after *every* mechanical pass, and reject any pass that tightens them. This is the highest-leverage change available, because it is the loop and not the agents that produced the last four rounds of nothing.
3. **Break the syntactic idiolect, not just the lexicon.** Forbid each court a construction the others may use and mandate one only it may use — e.g. deny Egypt the `, which is` appositive, deny Rome `stands at` / `runs at` / `against <number>`, deny China sentence-final `rather than`, deny Maurya `X and not Y`. Add all five constructions from §1 to `register-check.sh`, which currently tests eleven tells and catches none of the ones that now matter.
4. **Mandate one *load-bearing* unflagged error per document.** Not a wrong opinion — a wrong number the court uses to take a decision, with the qualification absent from the entire file. Rome's inherited "fevers not severe" is the right shape; it just needs to be wrong and consequential.
5. **Do not add a uniform block to all four again.** If distribution needs a landing zone, give it a different shape per country: Rome folds it into narrative, China returns it as a censorate report, Maurya as an appendix row, Egypt as numbered Items.
6. **Force asymmetric length by event weight** — roughly 7k / 11k / 14k / 18k — and forbid later passes from equalising it.
7. **Ban the universal self-audit close.** At most two of four may end on open questions. Currently all four do.
8. **Ban the priced-cost move in two of four.** Let two courts take a decision and simply not say what it cost.

### Per country

**Egypt** — *Keep* `Accepted cost:`; it is inherited from the human control and is real. Cut it from four uses to one. Retire the confidence-class system as a *global* rule and let Egypt mark only the figures it happens to care about, leaving the rest as assertions nobody checked. Give it the self-flattery it entirely lacks: Egypt believes the coffee deception has worked for five centuries and has never audited it — make that belief false, and let a spy return break it. Give it one decision made in the treasury's interest and presented as neutral.

**Rome** — Strongest of the four; protect what makes it strong (no confidence apparatus, argument over enumeration). But **Rome has drifted furthest from its own control**: 0.5 → 40.6 numbers per thousand words. Halve its numeric density and let it argue instead. Let it be openly triumphant about the 210-million strip. Let the Senate flatter itself once. Let one fiscal figure be a fiction the *curatores* stopped questioning a generation ago.

**China** — Do **not** delete `Cold reading:` as the prior audit recommended; it derives from the human control's `Read cold` and deleting it corrects toward uniformity. Cut it from three uses to one. China's real deficit is that it is the only court with no institutional failure it has not already diagnosed. Give it a pathology it cannot see: a suppressed censorate report, a shaded memorial, a faction that wins an argument it should have lost.

**Maurya** — The largest regression in the set. Its control document is the only one that analyses its own court's motives (*"its temper turned before its reason did"*), and its test document is now made of hull plating and lock springs. Restore the chronicle's psychological register as the priority. Then halve the self-audit: it confesses four faults in its own Coast Order in a single section, an overstatement in its notice to Egypt, and a twenty-nine-year failure to Rome. Let it defend the overstatement instead of pricing it, and push the Sixth Degree reasoning — the only genuine moral position in the set — toward self-righteousness.

---

**No files were edited.** Working scripts are in the scratchpad at `/tmp/claude-0/-home-user-test/b674fc0c-e12d-56b6-88e3-f69d58523b41/scratchpad/` (`metrics.py`, `tics.py`, `moves.py`, `affect.py`, `cover.py`, `syntax.py`) if you want the measurements re-run against the next generation.