# Coordinator notes

Read this before running a turn. Written after v1 and v2 of turn 525–550 both failed.

---

## 1. The main problem

Agents write for drama. They produce documents that read like published history — ironic reversals, memorable closing lines, courts that diagnose their own pathologies. That is not what a turn is. A turn is a government's working record.

An agent asked to play a country will instead write *about* a country. The difference shows up as:

- Self-aware framing no court would put in its own file
- Every tension resolved the same way: a correct memo existed, a named subordinate wrote it, nobody read it
- Volunteering unflattering facts to rivals
- Courts that confess, retract, apologise, and refuse advantages on principle

Tell agents directly: you are running a state, not writing about one. Nobody will read this except the men who wrote it. It does not need to be interesting.

## 2. Prose register

Test: does it read like a professor writing for a newspaper, or like a Wikipedia article for eighth graders? Aim for the second.

Specific things to ban:

- The em-dash pivot. v2 had 569 across four documents. The human-written turns had zero.
- "X is not Y; it is Z." 31 instances in v2, zero in the human turns.
- Aphorisms closing a section.
- Bolded or italicised minutes attributed to named officials for effect.
- Paradox offered where a mechanism belongs.
- Irony as explanation. Two facts juxtaposed is not a cause.

Flat prose is a feature. If a passage would be improved by being made duller, make it duller.

Two tells found by counting, both sharper than the em-dash. Run `v3/register-check.sh` on a turn directory before any review agent reads it.

**First person.** v2 used "we", "our" or "us" 337 to 561 times per document, 1,658 across the four. The four human turns used them once in total, in 16,300 words. A state paper does not say "we propose." This is the single strongest mechanical signal and it is trivially checkable.

**Length.** The human turns run 3,500 to 4,500 words per country per 25 years. v2 ran 18,500 to 25,800, about five times as much. Do not fix this with a word limit; that produced fifteen rewrites per agent and made the trimming, not the omission, into the work. Fix it by telling each agent what its own court does not bother writing down, and that whole subjects being absent is the correct outcome. Length is a symptom of the real defect, which is that agent turns omit nothing.

## 3. What the coordinator must not do

Every item below happened. Most were mine.

**Do not inject knowledge from our own timeline.** Verified instances: telling Rome that Europe lacks natural saltpetre; telling Rome it was the lightest-taxing power in the world; telling China to use a copper obturating ring (de Bange, 1873); telling China qinghao must be cold-infused (artemisinin, 1972); telling China the wall was optical-quality flint glass (Dollond, 1758). Three of those were in a single message.

**Do not praise.** Saying a passage is excellent stops you reading it critically. Several things called outstanding in v2 were surrendering the empire's core interests in well-built sentences.

**Do not tell a country what it did not discover.** Naming the thing discloses that the thing exists.

**Do not tell a country its intelligence was wrong.** That destroys the point of having separate agents with separate information.

**Do not give exact figures, or fake ranges centred on the true value.** 150 reported as "125 to 175" is the true number with extra steps.

**Do not hand over unrequested findings.** In eight human turns this happened about three times. In v2 it happened constantly.

**Check claims against each other, not just against plausibility.** Egypt's two nitrogen figures differed by two orders of magnitude and both were approved, in separate turns.

**When you strip a bad justification, check what was standing on it.** Removing Rome's saltpetre claim left it firing artillery with no oxidiser.

**A correction that makes the world more ordinary is suspect.** Revising Han frontier settlement down from 50–80,000 to 15–25,000 made a divergent world look more like Siberia. It was delivered as a fix.

**Verify before pushing back, and verify that a push was carried out.** Four times this session I nearly corrected something from memory that was not in the source. Once I reported Egypt's firearms as removed without opening the file. They were still there.

## 3b. Failure modes found in v3

**Never tell a country what it observes.** Asking Egypt to write what it found in Australia and the Maurya to write what it saw offshore produced two incompatible records: the Maurya logged parties landing, Egypt logged withdrawal without contact. Both were written to order, so neither is evidence. Ask only two things: what does this country **do**, and what are its **standing orders** for that situation. Then adjudicate the encounter yourself from the two sets of orders. Orders are checkable against a file; observations are not.

**Praise blinds the reader who gives it.** This recurs every generation of this project and it recurred badly in v3. Once a passage has been called excellent it stops being read. Say what a passage does and move on.

**Colonial death rates compound and agents model them as a single cause.** Contact disease, war, enslavement, and forced labour in mines and works each carry their own mortality and they stack. A subject population falling 0.6 per cent a year is not a catastrophe, it is a mild decline. Where a militarised power is conquering, enslaving and working a population that has never met the diseases, the honest figures are far steeper, and the coordinator must not accept a gentle curve as grimness.

**A bluff is a display placed where it can be tested.** Operational secrecy and counter-intelligence are not bluffs. This world's China bluffs by holding a frontier with a few dozen men and months of lead time at the end of its supply line, and by threatening what it cannot deliver. When an agent claims its court deceives, check whether the deception is a posture a rival could call, or merely a thing withheld.

**Agents cap compounding mechanisms and model them as linear.** Literacy and industrialisation are the two that matter here. A cheap-print examination society feeds back on itself: failed candidates become teachers, teachers lower the price of schooling, cheaper schooling produces more candidates, more candidates force the examination harder, a harder examination makes teachers more valuable. Ask explicitly for the loop and for what the loop does over a century. A figure that stops where the first generation stopped is the tell.

**Industrialisation is driven by profit on volume and consistency, not by the price of labour.** Merchants mechanise because a uniform product made faster takes the market, and they then carry the method into the next trade. This happens whether labour is scarce or abundant. Where an agent explains a factory by wage levels, it has the causation backwards, and the real sequence is usually: method observed abroad, applied to one trade, profit, carried into others, then transport becomes the binding constraint and the state is lobbied for it under another name.

**A court must not adopt its own lie, and the coordinator must not correct the lie out of existence either.** Egypt told Rome its African coast was newly taken. The internal file then began treating long-held ground as new. The fix is to keep the lie in the letter, stated flatly and without detail, and to keep the internal record accurate — not to soften the letter into something true.

**Check that a promised deliverable is actually produced in the turn it is owed.** Rome spent this turn reasoning about India's silence while India was never asked to produce the account or the letter. An obligation one court is waiting on has to be a live item in the other court's turn, or the exchange cannot resolve in either direction.

## 4. Hard rules for agents

1. **You may never state what another power did, decided, intends, believes, possesses, or offered.** You may report what your people observed and what your court concluded. Conclusions may be wrong.
2. **You may not write another power's letter.** Do not quote articles, clauses or figures from a message unless the actual text was given to you. v2 had two empires accepting articles that were never written.
3. **You do not have to send a message.** Egypt historically sends one letter to one power, and often none. Silence is a normal turn.
4. **You do not have to spy.** One operation per turn is the norm, not five.
5. **You never write your own spy results.** A tasking is a declaration of intent. Results come from the coordinator.
6. **Something does not have to go wrong.** Do not manufacture a disaster. Bad things get added by the coordinator after checking what would actually have happened — circulating diseases, weather, the real odds of a revolt.
7. **Missing data in your file is absence, not concealment.** If nobody wrote it down, it is not hidden.
8. **Author-voice passages are not knowledge.** Text addressing a reader, comparing to "our world," or explaining why the world was built a certain way is not your court's knowledge. Nothing downstream of it stands.
9. **Name the instrument, not the outcome.** Which levy, on whom, why not the alternatives. Which official, which office, which year.
10. **"First in N centuries" is not forbidden — it is expensive.** If a court really is reversing five centuries of practice, name who opposed it, what it cost, and who lost standing.

## 5. Canonical facts that were gotten wrong

**The Rome–Maurya steam-for-firearm trade, state at 525:**

- The Maurya asked Rome for marine steam, offering knowledge of the Chinese firearm.
- Rome agreed, but only for a maker's-standard account, which the Maurya did not have.
- The Maurya stole a physical weapon from a Han arsenal by bribery.
- **At 525 the Maurya had NOT replied to Rome. The gun was NOT yet reverse-engineered. Rome had sent NO engineers.**
- Maurya engineers were working on both the weapon and steam independently.
- Rome did not believe the Maurya would deliver, and said it would verify anything sent before providing assistance.

Both v1 and v2 had Roman engineers resident in Indian yards from 528, and v2 invented a completed account sealed in 524. Neither is true.

**Egyptian disposition.** Egypt distrusts everyone. On a ten-point scale: China 4–5, the Maurya 2, Rome 1. It does not confess, apologise, or hand over knowledge that cost it something.

## 6. Order of operations

1. Roll succession where the country's file makes ruler quality a mechanism. Use a real die. Mediocre means unremarkable — programmes continue at their funding, colonisation continues, research continues. It does not mean decline.
2. Each agent reads only its own files. Answers the country-understanding questions. Coordinator pushes back.
3. Agent plays the turn. No word limit. Declarations separate from narrative: message intent, spy taskings, research, territory split into held versus surveyed.
4. Coordinator pushes back. Always. There is always something.
5. Tech verification — one agent per country, given the country's own claimed aims so it can judge targeted research, blind to what the country wants to be true.
6. Spy adjudication — one agent per target, given only the target's files, the tasking, the cover and the network age. State explicitly that full and correct information is a normal outcome. A well-placed observer under good cover asking answerable questions usually succeeds.
7. Distribute: adjudicated returns, technical verdicts, and the actual text of letters received. Replies open.
8. Hostile review before anything is treated as canon.

## 7. What the review passes must check

Character continuity against the previous two documents. Modern-institution tells. Foreign control. Regression toward our own timeline. Unrequested gifts. Prose register. And a homogeneity check across all four turns in the same generation.

The homogeneity check is the one that matters most and the one most likely to be skipped. Four agents, four separate documents, no communication, and v2 still came out as one author at ~97% confidence. The voice was already present in the pre-turn assessments, so it is not introduced by coordination. It has to be attacked at generation time, per country, with different instructions about register, tense, structure and what that court does not bother to write down.

Human turns differ from each other because each omits what its court does not care about. Agent turns omit nothing. That asymmetry is the strongest single tell.

**v3 result: 85 per cent, down from 97.** The prose fixes worked and the convergence moved rather than disappearing. Formats now genuinely diverge; the *mind* behind them does not. Full report at `v3/audits/homogeneity-v3.md`. The three tells that replaced the em-dash:

**Affect went to zero in all four, and the variance collapsed.** Humans run 0.5 to 2.5 emotional words per thousand and differ in *kind* — hot, elegiac, self-auditing, cold. The four agent turns run 0.1 to 0.2 and every hit is a false positive. Across fifty thousand words and four empires, no court feels anything, and nobody boasts — including one that just stormed nineteen cities. Four real chanceries do not share a nervous system. **Mandate mood: at least two courts in a stated temper, and let it distort the document.**

**Four courts independently built the same epistemic apparatus in the same generation.** All four articulate that a displayed quantity is a lower bound, in four different labels. In the human control only two mark confidence at all, they mark it differently, and one *fails* to mark it in a place the turn then dramatises. No agent document ever fails to mark anything. **Mandate one unflagged error per document — a claim the court believes, is wrong about, and states with full confidence.**

**Nobody is stupid, corrupt, defensive or self-flattering.** Every document admits an error without excuse, names an internal loser, prices a downside it accepted anyway, and creates a standing order to fix a fault found by use. None contains propaganda, an unexamined assumption, a self-serving account, or a suppressed number. Real archives are mostly made of those things. **Give each court one pathology: a suppressed report, a shaded figure, a faction that wins an argument it should have lost.**

Also: force asymmetric length (agents came within 8 per cent of each other; humans varied 26), forbid each country two or three domains so coverage stops being symmetric, and vary the four-block scaffold by country — it appears in all four agent turns and none of the four human ones, and buys a large share of the homogeneity for free.
