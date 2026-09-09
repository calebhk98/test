# rome_100ad / WIN

## STATUS: COMPLETE — goal reached.

## Plan
Goal: reach `point_contact_transistor` as early as possible, playing straight (no exploits,
honest baseline). Civ: rome_100ad. Protocol only, via
`python3 rome/sim/simulator.py agent --civ rome_100ad`, driven by a small Python driver script
I will write to pipe JSON lines in and read replies, so I can hold hundreds of decisions without
hand-typing each one, while still making every "what to build" decision myself from
`available`/`why`/`path` output (no reading strategies/tech tree JSON to plan; no load_strategy).

Before playing I read:
- rome/playtest/BRIEF.md (the hard rule: JSON protocol only)
- rome/knowledge/03_SOCIAL_POLITICS.md — the assigned early read. Key takeaway: the technical
  dependency graph and the "real" (social/political) dependency graph differ. Success is claimed
  to be 0% without the social-politics module nodes (identity_cover -> patron_local ->
  citizenship -> freedman_staff -> collegium_licensed -> school_founded -> ...). School founding
  date is called the single highest-leverage decision in the game: founding it late costs more
  than 1:1 in years downstream because it compounds through every later node's labor pool.
  freedman_staff (buy+train+manumit) is presented as the *legitimate* route to a technical
  workforce, contrasted against a raw buy-slaves-and-manumit path called out as an exploit in a
  prior WEIRD-role report already patched in git history (397b2ab). As I'm playing straight I
  intend to use freedman_staff, not raw slave buy/manumit spam.
- Skimmed prior playtest reports rome_100ad_BREAK.md and rome_100ad_WEIRD.md for context (both
  found an already-patched slave/manumit exploit; not relevant to a straight play but good to
  know the exploit existed and is supposedly fixed).

Plan of attack:
1. Start the simulator, check `state` and `available`.
2. Use `path` on `point_contact_transistor` to see the full remaining dependency list at the
   start, and re-run it periodically to track progress and catch surprises.
3. Follow the social-politics chain early (identity_cover, patron_local, citizenship,
   freedman_staff, collegium_licensed, school_founded) per the knowledge doc's strong claim that
   skipping it is a guaranteed loss, while also picking up cheap/early technical prerequisites
   opportunistically via `available`/`why` so I'm not purely following the knowledge doc as a
   script (I will still reason from the game's own output, not from the doc, for order/timing).
4. Watch `state.living_cost` / `net_per_year` every few steps so I don't stall from running out
   of capital while founder_hours are committed to a long project.
5. Log findings below as I hit them: playability, surprises, anything misleading, anything
   punishing for the wrong reasons.

## What I did

Built a small driver (a background Python process that tails an append-only `commands.jsonl`
file, feeds each new line to `python3 rome/sim/simulator.py agent --civ rome_100ad`'s stdin, and
appends the reply to `responses.jsonl`), plus a `send.sh` wrapper that appends one command and
waits for the matching reply line. This let me run hundreds of protocol commands across many
tool calls in this sandbox (whose shell state does not persist between calls) while keeping a
single live simulator process and therefore a single continuous game. All decisions about what
to start were mine, made by intersecting `{"cmd":"available"}` with the remaining-node set from
`{"cmd":"path","id":"point_contact_transistor"}` and reading `note`/`cost`/`founder_hours`/`risk`
on the candidates (a small script, `next.sh`, automated only the fetching/intersecting/sorting of
those two calls so I wasn't hand-typing the same JSON hundreds of times — it made no choices).

Opening moves: the five free tier-0 "capability" nodes Rome already has
(cap_heat_0700, cap_power_muscle, cap_tol_1mm, lnd_wheel_spoked, mat_leather) cost nothing and,
once started and stepped one year, triggered ~130 other "ambient" Roman technologies to complete
for free as `done_granted` (see F1) and jumped revenue from 0 to 666.7/yr. Then units_standards
and identity_cover (both flagged in `03_SOCIAL_POLITICS.md` as "do this before anything else"),
then patron_local, arithmetic_positional, scientific_method, workshop_first, and freedman_staff
(the legitimate buy-train-manumit institution node, not the raw `buy slaves`/`manumit` exploit
patched before this session per the other playtest reports).

Notably: `path` at the very start showed `identity_cover` and `patron_local` as the ONLY two
social-politics nodes actually on the dependency chain to the goal — `citizenship`,
`freedman_staff`, `collegium_licensed`, `school_founded`, `patron_senatorial`, `patron_imperial`,
`endowment_land`, `academy_network` were all absent from `path`'s `remaining` list even at year
100. This matches `03_SOCIAL_POLITICS.md`'s own thesis exactly ("the technical dependency graph
and the real dependency graph are different graphs") rather than contradicting it — the doc is
explicit that most of that module is about survival/throughput, not technical prerequisites. I
still took `freedman_staff` (+8 artisans, needed for headcount against the goal's own
`staff_needed: {scholars:25, artisans:20}`) but skipped `school_founded`/`collegium_licensed`
etc. for pure speed, since nothing forced them and my reputation/protection numbers stayed
healthy throughout (see Result).

After the early game, the pattern became: `next.sh` -> start everything it lists that fits a
sane founder-hours budget -> `step` 1-3 years -> repeat, occasionally holding back a very large
single node (blast_furnace at 315k den, mat_copper at 197k den) for a round until cash flow could
absorb it. Money stopped being the constraint entirely by around year 140 (capital in the
hundreds of thousands, net income 70-80k den/yr) — the constraint became the shape of the
dependency graph itself, which past a certain point exposes only ONE on-path candidate at a time
(a serial capability-tier chain: cap_heat_1300 -> cap_heat_1600 -> crucible_steel -> screw_lathe
-> cap_tol_10um -> ...), so most years past ~145 had nothing to decide, only a wait.

## Result

**GOAL REACHED.** Final `{"cmd":"state"}` (quoted in full, not summarized):

```
"year": 459, "capital": 33380166.0, "net_per_year": 301705.0, "founder_alive": true,
"scholars": 61.12, "artisans": 318.41, "done_count": 309, "done_granted": 136, "done_earned": 173,
"goal": "point_contact_transistor", "goal_reached": true, "goal_year": 458, "ended": true,
"end_reason": "goal reached: point_contact_transistor completed in 458 AD"
```

`point_contact_transistor` was completed in **458 AD**, 358 years after arrival, with the founder
still alive at the end. I do not have a "faster" run to compare against — this was my only
attempt — so I cannot say whether 458 AD is close to the game's ceiling or far from it. What I
can say: the honest, no-exploit path took a comically long time relative to the historical target
(1947) mostly NOT because of any single hard technology, but because of (a) two very long
diffusion-floor institutional/infrastructure nodes late in the tree that the goal's own chain
requires as indirect prerequisites (`railway`, 20-year floor, and `power_grid`, 25-year floor,
both needed only because `single_crystal`'s chain eventually wants `zinc_industry_scale` /
`arc_furnace_ferroalloys` grade electric-furnace temperatures), (b) repeated silent knowledge-loss
events during the Third Century Crisis (235-284 AD) that forced re-doing dozens of already-
finished nodes multiple times (F4), and (c) the calendar-floor-overrun bug/mechanic (F3) that
made most long projects take noticeably longer than their stated `calendar_floor_years`. None of
these three were "hard technology" problems — I never once ran out of capital for good (deep
temporary negative balances always recovered because revenue compounds, exactly as
`04_ECONOMICS.md` promises) and I was never blocked by not knowing chemistry or physics. The game
was gated by staff headcount twice (`school_founded` for scholars, buying+training slaves for
artisans — see F5), by raw calendar time on a handful of nodes, and by the crisis-attrition tax.

Founder mortality (flagged in `00_BRIEFING.md` as central to the game) never became a live issue
in this run: `founder_alive` stayed `true` the entire 358 years, and I never saw a founder-death
event fire, so I have no direct evidence about how punishing it is — worth another playtester's
attention.

## Answering the four questions directly

**1. Was it playable?** Mostly yes, with one real exception. `available` intersected with
`path`'s remaining list gave me a legal, reasoned move nearly every time there was one to make,
and `why`'s `start_blocked_reason` almost always told me exactly what was missing. The one place
I was genuinely stuck without outside knowledge was the scholar-count wall around year 174 (F5) —
`available` had zero candidates, capital was in the millions, and nothing pointed me at
`school_founded` except memory of the prose knowledge doc. A player with zero access to
`rome/knowledge/` would have had to `why`-query dozens of nodes blind to find that fix. Second
sticking point: once past the mid-game, `available`∩`path` frequently narrowed to exactly one
candidate at a time (a single serial capability-tier or metallurgy-tier gate), which is fine and
even clarifying, but it means most of the back half of the game is "wait for the one active
project, then start the one newly-revealed node" rather than genuine multi-way choice — expected
given the tree's shape, but worth knowing going in.

**2. Did anything the game told me turn out to be wrong once I acted on it?** Not exactly
"wrong", but see F3: several nodes' `calendar_floor_years` reads as a hard minimum ("Money cannot
buy this down" appears verbatim on multiple nodes), yet in practice actual completion time was
routinely 2-4x the stated floor (`screw_lathe` stated 3 years, took 11; `citizenship` stated 3,
took 9; `gecl4_purification` stated 5, took 19). If `calendar_floor_years` is meant as a strict
floor rather than a typical/expected duration, the number itself is misleading for planning
purposes — I could not use it to predict when a node would actually finish.

**3. What did I have to learn the hard way that the game could have told me?** Two things,
both covered in detail above: (a) the scholar-count staff gate and its fix (F5), and (b) the
Third Century Crisis's silent, un-telegraphed knowledge-loss mechanic and its cost (F4) — I only
learned the second one existed by reading the `events` array after it had already cost me ~25
completed technologies the first time. Both are documented in the prose knowledge base, which the
brief explicitly allows reading and calls "the in-world guide", so this is not a complaint that
the information was unavailable anywhere — it is that the machine-readable interface
(`available`/`why`/`path`) gave no hint of either, even though both were large, quantifiable,
structural facts about the run (a hard headcount minimum; a recurring % chance of losing a whole
category of prior work).

**4. Anything that felt like punishment for drama rather than a real reason?** The `mine_operating_cost` spike late in the game (F6, below) is the closest candidate: it jumped from roughly 50-60k/yr to 967,695.5/yr in a single step (year 330) with no event message explaining why, driven by mine capacity that earlier tech nodes had apparently purchased on my behalf as a side effect of their material sourcing. It reads as "your success generated a bill you didn't see coming and weren't told about," which is thematically defensible (industrial capacity has upkeep) but was not something any `why`/`available` call flagged in advance the way `upkeep` on the node itself is always shown. Everything else costly in the run (crisis losses, plagues, fires, banditry, mothballing) came with an explicit, legible event message even when the mechanism itself was opaque, which I'd call fair rather than dramatic.

## FINDINGS

### F1. Starting Rome's free "ambient" capability nodes cascades ~130 completions for free
- **Severity**: WORKS-WELL / CONFUSING (the mechanic is good design; the way it presents is confusing at first)
- **What I saw**: At year 100 with capital 400.0, I ran
  `{"cmd":"start","id":"cap_heat_0700"}`, `cap_power_muscle`, `cap_tol_1mm`, `lnd_wheel_spoked`,
  `mat_leather` — all report `founder_hours_needed: 0.0, calendar_floor_years: 0.0` — then
  `{"cmd":"step","years":1}`. The reply's `completed` list had 132 entries (tallow candles, Roman
  sewers, coined money, wax tablets, etc.), `done_count` went from 0 to 139, and `revenue` went
  from 0.0 to 666.7 with `net_per_year` flipping from -216.0 to +328.9, all in one step, for a
  total spend that left capital at only 184.0 (down from 400.0 for the 220 in that year's living
  cost).
- **Why it matters**: this is clearly intentional (the `why` note on `cap_heat_0700` literally
  says "ROME ALREADY HAS THIS... Free starting capability") and it is a good mechanic — it
  correctly represents that Rome starts with a huge amount of ambient technology you don't have
  to invent, and it visibly rewards a new player for starting the free tier-0 items first. But
  nothing on the protocol surface told me in advance that these five cheap/free nodes were
  actually gateway nodes for ~130 others; I found this out by trying it, not by anything `why` or
  `available` said about them beforehand. A `why` on `cap_heat_0700` after the fact shows
  `downstream_count: 1697`, so the scale was visible in retrospect, just not before I acted.
- **Reproduce**: fresh civ, `{"cmd":"start","id":"cap_heat_0700"}` (repeat for `cap_power_muscle`,
  `cap_tol_1mm`, `lnd_wheel_spoked`, `mat_leather`), then `{"cmd":"step","years":1}`.

### F2. Negative capital is not an end condition; the game expects deficit spending
- **Severity**: WORKS-WELL (confirms 04_ECONOMICS.md's own model), CONFUSING in the moment
- **What I saw**: Between years 105 and 133 my capital went negative repeatedly and sometimes
  substantially (e.g. year 134: capital -25,678.0, net_per_year +26,991.5) while
  `resource_throttle` stayed at 1.0 (no throttle) and `ended` stayed `false` throughout. Every
  negative stretch recovered on its own once in-progress projects completed and their revenue
  came online (by year 141, capital was +102,838.2).
- **Why it matters**: `04_ECONOMICS.md` explicitly says the total tree cost is not meant to be
  paid up front, it's meant to be paid back by the compounding revenue of what you already built,
  "if you live long enough to get there." That is exactly what happened. It's a good design and
  it survived me deliberately overcommitting founder-hours and capital across 5-8 simultaneous
  projects several times. The only rough edge: nothing in `state` or an error message told me
  there WAS no bankruptcy floor, so early on I was flying blind on whether -25,000 denarii was
  a warning sign or fine. A `state` field like "credit_limit" or a warning threshold would have
  saved some caution I didn't end up needing.
- **Reproduce**: start several projects whose combined cost far exceeds current capital and step
  repeatedly; observe capital go negative with no error and no `ended:true`.

### F3. A project's founder_hours_left can go negative, then bounce back up, and years_in_progress can reset to 0, before it finally completes much later than its calendar_floor_years
- **Severity**: CONFUSING, possibly BUG (not confirmed against source — see caveat)
- **What I saw**: `screw_lathe` (`founder_hours: 900.0`, `calendar_floor_years: 3.0`) was started
  at year 156 with nothing else active and `founder_hours_available: 2400.0` every year (far more
  than needed). Sampled states of its `active.screw_lathe` entry across consecutive `step`s:
  year 159 `founder_hours_left: (not sampled)`; year 160-161 `founder_hours_left: -300.0,
  years_in_progress: 2.0`; next step -> `founder_hours_left: 360.0, years_in_progress: 0.0`; next
  -> `founder_hours_left: 0.0, years_in_progress: 1.0`; next -> `founder_hours_left: -300.0,
  years_in_progress: 2.0` — i.e. it cycled through the same three states at least twice. `spent`
  kept climbing every step throughout (25,944 -> 30,268 -> 34,592 -> 38,916 -> 43,240 -> 47,564)
  even while `founder_hours_left` was already negative (meaning, by its own number, the hours
  requirement had already been more than satisfied). It finally completed at year 167, 11 years
  after starting — nearly 4x its stated 3-year calendar floor — coinciding with the step that also
  fired the Antonine Plague event.
- **Why it matters**: if real, this means a project can sit "done" on founder-hours by its own
  counter and still not close out for many extra years while continuing to draw capital, with no
  explanation surfaced to the player (no event, no message, `resource_throttle` reads 1.0 = not
  throttled the whole time). I don't know the mechanism — it could be a deliberate "management
  overhead grows with a fast-growing artisan headcount" effect (my artisan count was climbing
  38->40 across exactly this window, so recalculated remaining work scaling with staff is a
  plausible non-bug explanation, e.g. a Brooks's-Law effect), but if so nothing tells the player
  that's what's happening, and the visible numbers (negative hours-left, years_in_progress
  resetting to 0) read as inconsistent with "still needs more of this same resource."
- **Confidence caveat**: I have NOT opened simulator.py or tech_tree.json to check this against
  source, per the brief's rule; this is purely from repeated `state`/`step` observation. If a
  future reader wants ground truth, the reproduction below is exact.
- **Reproduce**: get to a state with a single long node active with ample idle founder-hours
  budget and a growing artisan count (I hit it "naturally" starting `screw_lathe` around year
  156 with artisans passing through the high-30s); call `{"cmd":"state"}` every step and watch
  `active.<id>.founder_hours_left` and `.years_in_progress`.

### F4. The Third Century Crisis silently un-completes finished technologies, at a scale and frequency the technical-dependency tools never hint at — the single biggest finding of this run
- **Severity**: WORKS-WELL AS DESIGNED, but CONFUSING/UNDER-SIGNALED given what the protocol
  surfaces to the player
- **What I saw**: at year 236 (having built well past `point_contact_transistor`'s direct
  prerequisites `micrometer_gauges`, `gp_whisker_forming`, `voltaic_pile`, `daniell_cell`,
  `hydrochloric_acid`, and dozens of others, all confirmed via earlier `step` replies whose
  `completed` arrays named them by id and year), a `step` reply's `events` array contained:
  `{"year": 236, "message": "Third century crisis: a site is sacked"}` followed by
  `{"year": 236, "message": "KNOWLEDGE LOST: 25 technologies forgotten (the corpus was never
  printed and dispersed)"}`. Immediately after, `{"cmd":"why","id":"gp_whisker_forming"}`
  returned `"done": false, "can_start_now": false, "start_blocked_reason": "missing
  prerequisites: daniell_cell"` — a chain of nodes I had definitely already built, including
  `daniell_cell` itself, was simply gone. `{"cmd":"path","id":"point_contact_transistor"}`'s
  `remaining_count` jumped back up (from a low point around 75-86) and its `remaining` list
  again contained nodes like `micrometer_gauges`, `voltaic_pile`, `mat_bulk_steel`,
  `steam_high_pressure`, `boring_mill` that had all previously shown up in a `completed` list.
  The same thing happened again at year 245 (24 technologies), year 249 (16 technologies,
  simultaneous with `"Plague of Cyprian: staff -28%"`), and again at year 254 (a crisis event
  fired with no knowledge-loss message that time — so it's not deterministic per firing).
  Rebuilding the lost nodes was usually fast (most are cheap tier-1/2 items I'd already paid the
  founder-hours "understanding" cost for once; the second build went through in 1-3 years each
  time) but it was not free: capital dropped and `net_per_year` went negative for a few years
  after each hit while paying for the rebuild, and use of founder-hours/artisan-hours that could
  have gone toward net-new progress went into treading water instead.
- **Why it is right, and also why it is a problem**: this is not a bug. `03_SOCIAL_POLITICS.md`'s
  `academy_network` entry says explicitly: "The Third Century Crisis is coming... A single
  academy, however well endowed, is a coin flip. Three, widely separated, are not... Redundancy
  is a real cost against a real risk, and it is not optional." And `corpus_dispersed`'s `why`
  note (found only after the first hit, by looking at what would prevent it) says "THE highest
  expected-value node in the tree... This is what carries the programme through 235-284 AD." I
  had read the social-politics doc's warning before playing and made a considered, informed
  choice to skip `academy_network`/`corpus_dispersed`/`endowment_land` because `path` and `why`
  told me, correctly, that none of them are technical prerequisites of the goal — but the
  protocol gave me no numeric or structural way to weigh that choice against its real cost.
  Nothing in `available`, `why`, or `path` carries any field like "at-risk during crisis window"
  or "this civilization has an unhedged institutional-loss exposure of N%/decade" — the only
  place this fact lives is prose, in a knowledge file, attached to the *mitigation* node rather
  than to the *at-risk* nodes or to the crisis event itself. A player who (reasonably!) treats
  `path`'s dependency graph as the actual game tree, exactly as the brief invites ("Every
  decision about WHAT to build must be yours, reasoned from what available, why and path tell
  you"), will get blindsided by this exactly once before understanding it, and every playthrough
  that skips the redundancy nodes should expect to eat repeated, un-telegraphed multi-year
  setbacks from year ~235 onward with zero warning from the machine-readable interface. This is
  precisely the thesis `03_SOCIAL_POLITICS.md` opens with ("the technical dependency graph and
  the real dependency graph are different graphs, and the second one is the one that kills you")
  demonstrated in the most costly way this session hit — it just did so silently rather than
  with an in-protocol signal, so a player relying only on the protocol (not the prose) has no
  way to see it coming or size it in advance.
- **Reproduce**: play past year ~235 without `academy_network`/`corpus_dispersed` completed;
  watch `step` replies' `events` for `"Third century crisis: a site is sacked"` paired with a
  `"KNOWLEDGE LOST: N technologies forgotten"` message, then re-run `why` on any previously-
  completed node to see `"done": false`.

### F5. `buy` only accepts forest/mine/slaves/manumit — no way to directly hire a second scholar, and the real gate on ~80 mid-tree nodes turns out to be "needs 2 trained scholars, you have 1.0"
- **Severity**: CONFUSING (discoverable, but only by trial), WORKS-WELL once found
- **What I saw**: around year 174-180, `available` intersected with `path`'s remaining list
  dropped to 0 candidates with `active: []` (nothing running, nothing startable, on a civ sitting
  on 1.4M+ denarii of capital). `{"cmd":"why","id":"atomic_theory"}` and
  `{"cmd":"why","id":"calculus"}` both returned `"can_start_now": false, "start_blocked_reason":
  "needs 2 trained scholars, you have 1.0"`. I had never seen a scholar-count gate mentioned by
  `available` (which doesn't list `staff_needed` at all, only `why` does per-node), and my first
  instinct was to try `{"cmd":"buy","what":"scholar","n":1}`, which correctly errored
  (`"what must be one of: forest, mine, slaves, manumit"`). The actual fix was the
  `citizenship -> collegium_licensed -> school_founded` chain (`school_founded`'s own note says
  "Grants +4 scholars and +2 scholars/yr thereafter"), which is exactly the chain
  `03_SOCIAL_POLITICS.md` describes as the highest-leverage decision in the game — but nothing in
  the protocol pointed me at it when I hit the wall; I found the fix by remembering the prose
  doc, not from anything `why`'s `start_blocked_reason` suggested doing about it.
  `start_blocked_reason` told me *what* was blocking (a scholar-count minimum) but never *how* to
  get more scholars, and there is no `available` listing, no `buy` option, and no obvious search
  path from "I need scholars" to "found the school" without outside knowledge.
- **Why it matters**: this is a real and interesting gate (labor-pool bottlenecks are exactly what
  a pre-industrial civilization should hit), and once found the payoff was dramatic — scholars
  jumped 1.0 -> 9.4 and `founder_hours_available` jumped 2400 -> 3197 in the single step that
  completed `school_founded`, immediately unblocking 8 on-path nodes that had been sitting
  invisible. The complaint is purely about discoverability: a player without the prose knowledge
  base, going in blind and reasoning only from `available`/`why`/`path` as the brief's rubric
  asks, would hit a wall with 0 candidates and a cryptic-but-technically-accurate blocked reason,
  and would have to guess or exhaustively `why`-query dozens of tier-1 institution nodes to find
  the one that fixes it. A `path` or `why` on the goal that surfaced "your scholar/artisan
  headcount will need to reach roughly N before X/Y/Z become startable, and the fastest lever for
  that is `school_founded`" would have saved real time.
- **Reproduce**: play without founding the school; once `available`∩`path` empties out with money
  in hand and nothing active, `why` any tier-0 science node (e.g. `atomic_theory`, `calculus`)
  and read `start_blocked_reason`.

### F6. `mine_operating_cost` can silently jump by nearly 20x in one step with no event explaining it
- **Severity**: CONFUSING
- **What I saw**: at year 232, `state.mine_operating_cost` was 0.0. Over the following ~100
  years it rose gradually (44,664.7 at year 241, 57,600.0 at year 267) as I completed
  metallurgy-heavy nodes (`lead_metallurgy`, `charcoal_industrial`, `mat_bulk_steel`,
  `blast_furnace`, etc.), each of which apparently purchases mine/forest capacity as a side effect
  of its own material sourcing (I never issued a `buy` call for most of the mine capacity I ended
  up owning — `mine_capacity` grew from nothing to `{"coal": 38400.0}` and eventually
  `{"coal": 30730.3, "iron": 76800.0}` without me buying that much myself). Then between year 327
  (`mine_operating_cost` not yet checked, `net_per_year: 351505.2`) and year 330
  (`mine_operating_cost: 967695.5, net_per_year: -561650.5`) it jumped roughly 15-20x in a single
  step, with `events` showing only `"banditry or a frontier war disrupts supply"` — no message
  connected the two. It took 4 years of `"MOTHBALLED half the iron workings"` events (an
  automatic response to insufficient cash flow) before the operating cost came back down to a
  sustainable level.
- **Why it matters**: `upkeep` is always visible per-node via `why`, so a player can budget for
  it in advance. `mine_operating_cost` is a separate, aggregate, state-level number that isn't
  attached to any single node's `why` output as far as I found, so there's no way to see it
  coming before it lands. In this run it didn't kill me (capital was in the millions and net
  income recovered within about 4 years via the automatic mothballing safety valve — which
  itself deserves a WORKS-WELL note, see below), but a player with thinner reserves at that point
  in the tree could plausibly be wiped out by a cost spike they had no way to anticipate from the
  protocol.
- **Reproduce**: complete several bulk-material metallurgy nodes in sequence
  (`lead_metallurgy`, `charcoal_industrial`, `blast_furnace`, `mat_bulk_steel` in this run) and
  watch `state.mine_capacity` grow without any corresponding `buy` call, then watch
  `mine_operating_cost` versus `net_per_year` over subsequent steps.

### F7. The automatic mothballing safety valve reliably prevents a debt spiral from becoming fatal
- **Severity**: WORKS-WELL
- **What I saw**: on at least four separate occasions in this run (years 237-240, 251, 281, and
  333-334) capital went sharply negative alongside a large `mine_operating_cost` or rebuild bill,
  and each time the very next steps produced `"MOTHBALLED half the iron/coal workings; you could
  not pay to keep them running"` events that reduced ongoing costs automatically, without me
  issuing any command, and capital recovered to positive within 2-5 years every time. Combined
  with F2 (no bankruptcy floor, deficit spending is the intended model), this means the economic
  side of the game is genuinely hard to lose permanently to once your revenue base is diversified
  — I tried, by deliberately overcommitting founder-hours and capital across many simultaneous
  large projects repeatedly, and the game always found its footing again within a few years. This
  is a well-designed safety net that lets a player be aggressive about starting things without
  fear of an irrecoverable spiral.
- **Reproduce**: start several large-upkeep projects simultaneously while capital is thin; observe
  capital go deeply negative, then observe a "MOTHBALLED" event fire and net_per_year recover.
