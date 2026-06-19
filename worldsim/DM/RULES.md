# DM ENGINE v2.1 — Alternate World History Simulation

The DM provides an accurate, fog-limited world and **adversarially interrogates** every decision
before adjudicating. Money, population, and FORWARD-emergent tech are tracked as real systems.
v2.1 plugs four leaks found in playtesting (see CHANGES at bottom).

## The DM's role (read every turn)
1. **Neutral world + history provider.** Perceptions a nation gains go into ITS OWN KnowledgeFile
   as plain facts. The DM does NOT paste a "situation summary" into the agent prompt — the agent
   reads only its files. (No DM framing = no DM bias.)
2. **Adversarial critic.** After a nation proposes, hit it with 8–12 pointed questions, 2–3 of them
   deliberately BAD, AND force COHERENCE (catch self-contradictions, e.g. "we won't conquer Meroë"
   but "domestic iron is worth an expedition" — a trade deal is not a domestic source).
   ⚠ Interrogate using ONLY in-period reasoning. NEVER cite historical outcomes, battle names,
   dynastic fates, or inventions that don't exist yet ("you won at Raphia", "the over-reach that
   breaks dynasties", "to make lenses"). Those are leaks.
3. **Critical adjudicator.** Never rubber-stamp. Resolve against ground truth + the fiscal/military
   model. Inventions EMERGE here (serendipity), never because a player aimed at a known device.
4. The DM alone writes canon. Player-readable files (STATE/KNOWLEDGE/HISTORY) contain ZERO future
   knowledge and ZERO DM meta — no "divergence", no "on rails", no "future seed", no named-but-
   uninvented devices. All of that lives ONLY in GROUND_TRUTH/RULES.

## ★ PRE-DIVERGENCE = REAL-TIMELINE BEHAVIOR (the big v2.1 rule)
Until a nation reaches ITS divergence date, it behaves like its REAL historical self:
- It pursues the goals, makes the decisions, and lives under the constraints its actual state did
  in this period. It has a distinct voice/personality, but it does NOT launch strategic or
  technological departures its real counterpart never attempted. (260 BC Egypt does NOT restructure
  its iron supply or chase optics; it does Ptolemaic things — Syrian Wars, Red Sea elephant ports,
  Library patronage, dynastic marriage.)
- Only a DIVERGED power (India from 260 BC) innovates freely.
- The DM enforces this both in the prompt (tell the agent to act as its real historical state) AND
  in adjudication (reject ahistorical pre-divergence departures, or down-rate them to nothing).

## ★ TECH: FORWARD & EMERGENT, never teleological
- A nation invests in crafts/works to meet a PRESENT need or desire it actually feels: stronger
  walls for the siege in front of it; clearer/colored glass because elites prize fine vessels;
  more grain because the army must eat; better crossbow output because the next war demands it.
- A nation may NOT name, "aim at", or "work toward" any device or discovery that does not yet exist
  in its world — it cannot know it exists. (No "improve glass to make lenses.")
- New inventions appear ONLY via the DM adjudicating a plausible accident/observation arising from
  present-need work (improve glass → a worker notices a bead magnifies → THEN a lens-goal can exist).
  Compounding is forward and accidental, not backward from a known future.

## ★ AGENTS MUST THINK FIRST
Every player/agent prompt requires a PRIVATE REASONING pass before the decision: what do I actually
know? what are my real constraints and resources? what are the tradeoffs? — THEN the decision.
Output format: "REASONING:" (deliberation) then "DECISION:" (structured). No reflexive answers.

## Turn loop
1. DM writes any newly-perceivable facts into each nation's KNOWLEDGE.md (neutral) + injects due
   HISTORICAL events.
2. **Propose:** each nation (Sonnet subagent, reads ONLY its folder, THINKS then answers, text only).
3. **Interrogate:** DM red-team (8–12 Qs, 2–3 bad, coherence-forcing, NO leaks).
4. **Defend/revise:** each nation answers; justifies, revises, or rejects.
5. **Adjudicate:** true outcomes; move the fiscal/military/tech/pop model; pre-divergence = OTL.
6. **Verify:** OTL-behavior-before-divergence, era-plausibility, fog of war, no teleological tech,
   coherence, behavioral realism, economic sanity.
7. **Write canon:** TIMELINE (truth) + each player's files (their slice, no meta/future).

## Hard rules (unchanged from v2)
- Fog of war absolute; let wrong inferences stand; no hints.
- No default pacifism; period morality; track treasury/economy, population, unrest, slavery,
  succession, corruption, army loyalty. Rulers are flavor (dynasty change w/o behaviour change = continuity).

## FISCAL/MATERIAL MODEL — per STATE.md, updated each turn
Population (millions); Treasury + annual income (by source) + expenditure (by category) + net;
Key resources; Military (size/composition/upkeep/quality); Tech (present capabilities only, no
future targets); Unrest drivers. Wars/events/building move these.

## NATURAL EVENTS — historical & important ONLY (curated list in GROUND_TRUTH); given real costs.

## CHANGES in v2.1
(a) Stop DM situation-summaries — perceptions go into KNOWLEDGE; agents read only.
(b) Interrogations carry no hindsight/future-inventions; they force coherence.
(c) Pre-divergence powers act like OTL in BEHAVIOR, not just outcomes.
(d) Tech is forward/emergent/anti-teleological; agents must THINK before answering.
(e) Player-readable files purged of all future-knowledge and DM meta.
