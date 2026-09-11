# Open work, as of 2026-09-11

Collated from the two playtest audits (AUDIT_rounds_1_6.md, AUDIT_rounds_7_11.md),
the round-11 notes, and this session's own measurements. Ordered by how much
damage each does to a player, not by how hard it is to fix.

## The measurement problem, which gates everything else

Rome reaches the goal in 0% of automated runs at HEAD and 38% at a06f3fb,
eight runs each at horizon 700. The capability change (1be633d) is NOT the
cause: reverting it at HEAD still gives 0%. A bisect across the four later
commits (rubber e88a822, auto_train/auto_hire ac5cfa5, reporting 8ef53cd,
ledger d25ab26) is in progress. Until this is settled, no balance judgement
made from `run --mc` is trustworthy.

Separately: a hand-played run on this same build reached 122 of the goal's 146
nodes with 617M denarii (naive11/b, fog ON, Rome default). So the automated
strategy runner and a competent player disagree sharply, and the runner is the
instrument development has been steered by all along. That is its own problem.

## Correctness, still open

- `waiting_on` names the wrong constraint: "waiting on your hours" with 2,000
  hours free, "waiting on money, 491.3 still owed" with 490,410 in hand.
  Reported in every single round. An agent is on this.
- The scribe units bug: "this society can field 1321 scribes at most", and
  `hire scribe 2` raises the pool to 5,321. A per-year hours ceiling compared
  against a headcount. Same agent.
- Fog of war can be rewound with save/load: build something, see what appears
  on the frontier, reload before paying for it.
- England is pre-granted blast_furnace and mat_cast_iron, the exact technology
  its own scenario briefing calls "the biggest single technology gap you face".
- Free zero-cost Roman and Ptolemaic institutions (cursus publicus, the Pharos)
  are offered in every civilisation, unfiltered by geography.
- Save progress can be silently lost on a closed output pipe mid-step, against
  the explicit promise that closing the terminal costs nothing.
- Training a specialist trade does not price the founder-hours before you
  commit, and founder-hours are the scarcest resource in the game.

## Design, still open

- People are fractional. 0.8 of a person is not a person. Attrition should be
  probabilistic on whole people; hiring and training should land whole.
- Techniques carry upkeep. A thing you merely know how to do should cost
  nothing to keep; upkeep belongs on the establishment it unlocks.
- A node's labour requirement is a rate per year you must sustain, so you
  cannot take twice as long at half the rate. It should be a cap per year plus
  a maximum total duration.
- `start` may run into arrears; `open` refuses credit entirely. Opening a shop
  is at least as financeable as half-digging a foundation.
- Revenue is exact before you have built the thing, which under fog is the
  strongest signal in the game and the only heuristic testers could find. It
  should be an estimate under fog and exact only once you have run it.
- The auto_* policies read as optimal play and are not. They are a quick
  approximation; several testers turned them on and were ruined. They should
  say so where they are listed.
- Reputation rewards raw completion count, so it is maxable by building
  trinkets you never use.
- The game tells the player which branch matters ("every year of delay costs
  more than any single technology"). Under fog that is the game playing itself.
- Norse flagship starting technologies (clinker hull, deep keel, bog-iron
  bloomery) are dead ends in the dependency graph, contradicting the civ's own
  description.
- `commission` appears to strictly dominate `hire` for project labour.
- The economy tips early: after roughly 150 to 250 AD there is nothing left to
  spend money on and no tradeoffs remain. Reported in nearly every round as the
  single biggest balance problem.
- Mortality mode buries the founder's death among the completions, never states
  the founder's age, and then accepts commands for years afterwards.
- Rubber is bought at a market price. It should be something you produce.

## Discoverability, still open

- `_room_advice` filters by is_visible, so the text naming workshop_first and
  school_founded appears with fog off and vanishes with fog on, which is
  precisely when a player needs it.
- Whether a zero-revenue node's effect requires staying open is now consistent
  in the engine and stated nowhere in the interface.
- No command shows the society's own values, though event text names them.
- No progress-toward-the-goal figure until the run has ended, at which point
  "146 nodes in all; you had 122" is the most useful line in the game.
- No way to bulk-start what is startable, so the late game is pure typing.
- A multi-year `step` ploughs through its own emergency warnings, including
  "while it is still your choice", into insolvency.

## Already fixed this session, for the record

Hysteresis on concern closing; the three staff figures agreeing; free
technologies no longer arriving on turn one; capability requiring a concern to
be open; rubber repricing and gating; auto_train affordability; auto_hire in
arrears; fatal probabilities no longer rounding to 0%; the scandal trend;
`stuck` on turn one; `labour` naming what raises household room; `hire`
reporting its count; the ledger's double-billed hiring advance; a dead founder
starting projects; `close <material>` on a half-sunk shaft; the com_ family
filed under electricity.

## Added 2026-09-11, after the user read the audits

### The two rulebooks, which is the worst thing found so far

`hire scholar 12` is refused with "this society's literacy will not supply
more than 5.9 scholars in total, ever, at any price". In the same state,
`auto_hire` reaches 146.4 scholars in forty years, because it writes
`self.scholars` directly and never goes through `hire()`. The goal and three
other nodes on the road to it want 25 scholars. So a person at a keyboard is
hard-walled at about six against a requirement of twenty-five, while the
automation ignores the wall by a factor of twenty-five. Measured, not inferred.

That single asymmetry is the best explanation anyone has offered for why
testers called the literacy ceiling "the single thing that decided whether
their run could be won", and for why hand play and `run --mc` disagree so
violently that one reaches 122 of 146 nodes while the other reaches none.

Fixing it needs both halves at once, because either alone makes things worse:
auto_hire must respect the ceiling, AND the ceiling must be able to reach what
the tree asks for.

### The ceiling is also mislabelled, and barely moves

The refusal states a fact about Rome. It is not one: the binding quantity is
`hired_hours_cap_base`, 25,000 hours, which is this household's reach into the
labour market. Rome's literacy_elite is already 0.900, and since it cannot
exceed 1.0, the entire printing/paper/school/academy/library mechanism can move
Rome's scholar ceiling from 5.88 to 6.36. An eight per cent gain is not what
the argument for printing rests on.

### Institutions are flags; mines are quantities

open_mine takes a tonnage and forest_ha is an area, so you can sink many mines
and buy more coppice. school_founded is a boolean: one school, ever. You cannot
found five, or five thousand, however rich or literate you become. That
asymmetry is why the literacy ladder dead-ends, and it is the same shape of
problem as the capability change ran into.

Missing alongside it: no land constraint on mines or woodland; no depletion as
the easy seams are worked out; no yield gain from technology. All three were
asked for and none exists.

### The optimizer should plan, not walk, and should learn from its own wins

`run --mc` is a greedy walk over a fixed order from recommended.json. It does
not look ahead and does not know the goal; Monte Carlo only averages over event
randomness. The tree is a DAG with a known goal and a 145-node closure, so
backward chaining with costs and calendar floors is both better and tractable
at this size. And when a run DOES reach the goal its build order is discarded -
caching it as a strategy file is cheap and would have saved most of a day.

These two are worth more than any remaining item above, because every balance
judgement in this project has been measured with an instrument that plays badly.

### The blind prerequisite audit was biased, and should be re-run

Two flaws, both in how it was briefed. It looked up each node's real
prerequisites in the middle of its walk, which fed it tree knowledge that
contaminated every later guess. And it recorded its guesses in conversation
rather than in a file, so it certainly drifted and forgot some. Re-run it by
completing the whole imagined breadth-first walk into a file FIRST, and looking
anything up only at the very end.

### Wire tungsten into the cathode

Real finding, deferred only for cost: in2_electron_source_cathode's own note
says "Tungsten chosen for high melting point and low evaporation" and mat_tungsten
is not among its prerequisites. Check the MARGINAL closure before pricing the
work: much of mat_tungsten's 101-node closure may already be in the goal's 145,
in which case the true addition is far smaller than the raw number suggests.
