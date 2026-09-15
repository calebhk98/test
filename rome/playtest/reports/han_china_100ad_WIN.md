# han_china_100ad / WIN

## STATUS: COMPLETE -- goal reached (point_contact_transistor, year 542 AD)

## Plan

Goal: reach `point_contact_transistor` as early as possible, playing straight (no exploits),
protocol-only, via `python3 rome/sim/simulator.py agent --civ han_china_100ad`. I built a small
driver (a background Python process, `driver.py`, holding one persistent simulator subprocess,
fed by tailing an append-only `cmds.jsonl` and writing replies to `replies.jsonl`; a `send.py`
helper appends one command and blocks until the matching reply appears) so I can issue hundreds
of protocol commands across many tool calls without losing the single continuous game (this
sandbox's shell state does not persist between Bash calls, but the background process does).
Every decision about what to `start` is mine, reasoned from `available`, `why`, and `path` output
— I did not read `rome/data/strategies/` or the tech tree JSON to plan, and did not import
`simulator` or use `load_strategy`.

Before playing I read:
- `rome/playtest/BRIEF.md` (the hard rule).
- `ROME_BOOTSTRAP.md` (top-level framing, the five-society comparison table, the grading
  methodology caveats).
- `rome/data/civilizations/han_china_100ad.json` directly (this is civ *config*, not the tech
  tree or a strategy file, so reading it seems in-scope; it is effectively the same information
  the task prompt already quoted at me: starting techs = blast_furnace, mat_cast_iron,
  cap_heat_1300, rag_paper, mat_paper, crank_conrod, bellows_water_blown, horse_collar,
  fud_seed_drill, fud_heavy_plough, sea_sternpost_rudder, sea_magnetic_compass; cost multipliers
  favoring metallurgy/casting/paper/information (0.5-0.75x) and penalizing commerce/finance
  (1.15x/1.2x); `w_eminence_danger: 0.8`; hazards = Yellow Turban rebellion (184-205, 20%/yr sack
  chance) and Three Kingdoms fragmentation (220-280, output x0.6); a `handicap_remedies` block
  saying the commerce/finance penalty's residual is removed only by `patron_imperial`).
- `rome/knowledge/03_SOCIAL_POLITICS.md` in full. This is written entirely in Roman-institution
  language (identity_cover as "Alexandrian physician-philosopher", patron_local, citizenship via
  *civitas Romana*, freedman_staff via Roman manumission law, collegium_licensed via Pliny's
  fire-brigade letter, patron_senatorial/patron_imperial via the *cursus honorum*). Since the
  brief specifically asks whether these Roman-named nodes read as absurd for Han China, I read it
  closely to have a baseline before seeing how the simulator actually presents them in a Han
  game (`why` output, node names, notes) — watching for whether the presentation layer
  Sinicizes anything or just leaves Roman flavor text stapled onto a Han playthrough.

Initial state (year 100, before any command): `capital: 400`, `revenue: 8700`, `upkeep: 9375`,
`net_per_year: -1413`, `done_count: 11` (`done_earned: 11`, `done_granted: 0`), and critically
`{"cmd":"available"}` already returns **366** startable items at year 100 — I have not compared
against a fresh Rome run in this session, but the prior `rome_100ad_WIN.md` report describes Rome
opening with ~5 free tier-0 nodes triggering ~130 ambient grants after the first step; Han's 11
already-`done_earned` (not `done_granted`) nodes and 366 immediately-available options at turn
zero, before stepping even one year, is the first concrete signal that the metallurgy/paper head
start is not just flavor text. `knowledge_risk` at year 100 already lists both Han-specific
hazards (Yellow Turban, Three Kingdoms) by name with sack chances — will track whether this
differs meaningfully from Rome's crisis modeling.

Plan of attack:
1. `path` on `point_contact_transistor` for the full remaining dependency list, re-check
   periodically.
2. Follow the social-politics chain as far as it's actually load-bearing per `path` (learned from
   the Rome report: only `identity_cover` and `patron_local` were actually on Rome's critical
   path; will check independently for Han rather than assume the same holds).
3. Otherwise: intersect `available` with `path`'s remaining set, pick by cost/founder_hours/risk,
   step, repeat. Log anything surprising immediately below, not at the end.

## What I did

(updating live — this is a working log, condensed into FINDINGS below as they solidify)

Opening: started the five free tier-0 capability/material nodes (`cap_heat_0700`,
`cap_power_muscle`, `cap_tol_1mm`, `lnd_wheel_spoked`, `mat_leather` — all `cost:0`,
`founder_hours:0`), plus `units_standards` and `identity_cover`. `step 1` produced **127
`done_granted` completions in a single year**, jumping `done_count` from 11 to 143 and revenue
from 8700 to 10197.6.

**Immediately notable and logged as F1 below**: the 127 granted nodes are overwhelmingly
Roman-institution nodes by name — `civ_sewer_roman` ("Roman sewer with gravity flow"),
`civ_aqueduct_roman` ("Roman aqueduct with inverted siphons"), `civ_road_paved` ("Roman paved
road with surveying"), `civ_arch_roman` ("Roman masonry arch"), `civ_insula` ("Insula: Roman
apartment block"), `lnd_cursus_publicus` ("Cursus publicus courier service"), `sea_pharos_lighthouse`
("Pharos lighthouse"), `civ_amphitheatre`, `hom_cosmetics_roman` ("Roman cosmetics"),
`civ_chorobates` ("Chorobates: Roman water levelling rod"), `civ_surveying_groma` ("Groma: Roman
X-staff surveying tool"), `fin_argentarii` ("Deposit bankers (argentarii)"), `fin_annona` ("Annona
grain dole and administration"), `fin_collegium` ("Professional associations (collegia)"),
`med_legal_physician` ("Legal protection for physicians") — granted for free, at year 100, to the
LATER HAN EMPIRE. None of Han's own starting_techs list items (blast_furnace, mat_cast_iron,
cap_heat_1300, rag_paper, mat_paper, crank_conrod, bellows_water_blown, horse_collar,
fud_seed_drill, fud_heavy_plough, sea_sternpost_rudder, sea_magnetic_compass) appear inside this
`done_granted` batch — those 12 were apparently already counted in the year-100 `done_earned: 11`
baseline (one is presumably a duplicate/prerequisite of another). This looks like the ambient
"civilization already has a huge base of pre-industrial tech" grant logic is a single shared
Rome-shaped bundle applied to every civ regardless of which starting_techs list that civ actually
declares, rather than a Han-specific bundle. Continuing to play; will use `why` on a couple of
these to see if there's a substitution mechanism I'm missing before calling this a confirmed bug.

Confirmed via `why` on two of them (`civ_sewer_roman`, `lnd_cursus_publicus`): both show `cost:0`,
`tier:0`, `"done": true`, `"on_goal_path": false`, and their `note` fields are unchanged Rome
flavor text ("ROME ALREADY HAS THIS... Imperial dispatch relay using stations and fresh horses"),
granted anyway to Han China. Not on the critical path to the goal (both `on_goal_path: false`), so
this does not change my time-to-transistor, but it is a real immersion/realism break: the
ambient "civilization already has a huge backlog of premodern technology, free" grant appears to
be a single hardcoded Rome-shaped bundle applied identically to every civ, rather than being
keyed off each civ's own `starting_techs`/`institutions` data. A Han playthrough is credited with
the Cloaca Maxima and the cursus publicus. I did not read the tech tree JSON to plan around this;
I only inspected these two nodes' full `why` output after the `available`/`step` output surprised
me, which the brief permits.

### Note-text sample (feeds F3 below)

`why` on three of the year-102 on-path candidates, verbatim `note` field:

- `scientific_method`: *"The hard part is not stating it, it is displacing Aristotelian
  authority. Risk is high because the failure mode is cultural, not technical. Multiplier on
  every research node thereafter. Contradicting Aristotle and Galen in public is a social act
  before it is an intellectual one, and their defenders hold the chairs, the patronage and the
  medical guild. Expect organised opposition, not curiosity."*
- `arithmetic_positional`: *"Highest return on personal hours in the entire tree. Frame as
  recovered from Indian sources, which is even true. Sell it to bankers and the fiscus first;
  they will adopt it for self-interest and carry it for you."*
- `patron_local`: *"Cheapest entry gift is a pair of reading lenses for an ageing magistrate.
  Halves incoming suspicion."* — identical, word for word, to the sentence
  `03_SOCIAL_POLITICS.md` gives for Rome.

These are all being told to me while playing the Later Han Empire, whose examined civil service
already used a decimal place-value counting-rod system centuries before 100 AD (so "frame as
recovered from Indian sources" is Rome's specific solution to Rome's specific numeral problem,
not Han's), and whose intellectual authority structure is the Confucian classics and the
imperial examinations, not Aristotle, Galen, and a "medical guild." Filed under F3.

The pattern kept recurring for the rest of the run and I stopped logging every instance once it
was clear it was systematic: `case_hardening` ("Roman smiths do all of this already..."),
`refractory_fireclay` ("Rome has excellent..."), `lead_metallurgy` ("Rome does this already and
does it well"), `lab_apparatus` ("Alexandrian alchemy already looks like this, so it is
culturally normal"), and a random event at year 124, `"fire in the insula district"` — `insula`
is specifically the Roman apartment-block type, appearing as a random-event string while playing
Han China. I never saw a single node note or event string address China at all (no reference to
counting rods, the examination system, the *hang* guilds Han's own `institutions` block names,
Confucian officialdom, etc.) despite `han_china_100ad.json` clearly declaring civ-specific
`institutions`, `values`, and `cost_multipliers`. The cost *numbers* are civ-aware (see F5); the
prose is not, anywhere I looked.

### F-note: a real capability-graph inconsistency found via `why` (not tech-tree reading)

At year ~114 `cap_heat_1100` showed up as `available` and `on_goal_path: true`, which was odd
since Han's `starting_techs` already includes `cap_heat_1300` (a higher rung). `why` on
`cap_heat_1300` (quoted in full above) shows `"done": true` **and**
`"missing_prerequisites": ["cap_heat_1100"]` simultaneously — the simulator considers a node
completed whose own direct prerequisite is not completed. This happened because Han's starting
bundle grants the tier-1 capability directly without back-filling the tier-0 rung underneath it.
It cost me nothing here (I had to acquire `cap_heat_1100` anyway for other downstream nodes gated
on it specifically, and it was cheap), but it is a real data-consistency bug: a `done:true` node
reporting its own prerequisite as missing.

### F-note: a stated hard resource requirement that the engine did not enforce

`finery_puddling`'s `why` text (quoted above) is explicit and specific: *"roughly 2,000 hectares
of forest under permanent management, which you must own before you light it."* I started and
completed `finery_puddling` at year 129 having bought only **100 ha** of forest (`{"cmd":"buy",
"what":"forest","n":100}` succeeded at ~187.5 den/ha; a follow-up `{"cmd":"buy","what":"forest",
"n":2000}` failed both before and after with `"cannot afford"`). After completion, `state` showed
`forest_ha: 100.0`, `resource_throttle: 1.0`, `throttle_binding: null` — no penalty, no partial
completion, no warning. So either (a) the note's claim is aspirational flavor text with no actual
mechanical backing, or (b) there is a real charcoal/forest shortfall mechanic that exists
somewhere else in the model (a stock being silently drawn down, future throttling I have not hit
yet) that never surfaced in any field `available`/`why`/`state` exposed to me. Either way, a
player using only the protocol (as instructed) has no way to tell the two apart, and the
straightforward reading of the node's own explanation turned out not to describe what actually
happened when I acted on it.

### F-note: the single clearest case of a Roman-only institution name (feeds F3)

At year 139, playing the Later Han Empire, I sent:

```
{"cmd":"start","id":"citizenship"}
```

and got back:

```
{"ok": true, "started": "citizenship", "name": "Roman citizenship by grant", ...}
```

`{"cmd":"why","id":"citizenship"}` confirms it is not a display quirk: `"name": "Roman
citizenship by grant"`, `"note": "Gives provocatio, the right of appeal, which is the difference
between a governor executing you and Rome hearing you. Buy it with a public benefaction."` This
is the plainest possible instance of the thing question 3 asked about: the node's own `name`
field, not just background prose, says "Roman citizenship" while my `state.goal` and civ context
are Han China. There is no governor in the Han administrative system and no *provocatio* — the
equivalent institutions would be something like registration in the household registers
(*hukou*) and appeal through the commandery/prefecture hierarchy to the throne, which is a
genuinely different mechanism with different failure modes (an accusation under the Han travels
up a bureaucratic chain rather than being settled by one man's *imperium*, and eunuch/court-
faction politics, which Han's own `w_eminence_danger` note calls out, matter more than a
governor's personal power). None of that is represented; the node is Rome's, unmodified, with a
Han price multiplier attached (see F5) and nothing else.

### F-note: `corpus_written`'s own text names Rome's languages while playing Han (feeds F3)

At year 179, with `knowledge_risk.technologies_at_risk` up to 52 and the Yellow Turban rebellion
(184-205, `sack_chance_per_year: 0.2`) only 5 years away, I checked the hedge the game itself
names (`better_hedge_available: "corpus_dispersed"`). Its prerequisite `corpus_written`'s `name`
field reads: *"Write the corpus: everything you know, in plain quantitative Greek and Latin."*
This is being offered to me while playing the Later Han Empire, whose scholarly and
administrative language is Classical Chinese, not Greek or Latin, and whose knowledge doc says
Han's own institution is `hang, state-supervised` guilds and an examined civil service, not a
Museum-style Alexandrian library tradition. Combined with `corpus_dispersed`'s note ("push copies
into every library, temple archive and private collection from Britain to India... present it as
a gift to the libraries of the Empire") this whole three-node hedge chain (`corpus_written` ->
`printing_press` -> `corpus_dispersed`, `critical_path_years: 20.5` combined) is unmodified Rome
geography and Rome language, running inside a Han playthrough. I did not pursue it: the combined
chain's own stated calendar floor (10 + 2 + 8 years serial-ish) could not finish before the
184 AD hazard window regardless, so I accepted the risk instead and kept building toward the
goal — see Result for what the rebellion actually cost.

### F-note: a garbled/templated note string on `mat_bulk_steel` (not Han-specific, general bug)

`{"cmd":"why","id":"mat_bulk_steel"}` at year 184 returned this note (verbatim, mid-sentence):
*"At 0.75 tonnes of charcoal per hectare of coppice per year that is roughly n/a, it burns coal
hectares of forest under permanent management, which you must own before you light it."* This
reads as a charcoal/forest-sizing template reused for a coal-burning industry (the note opens by
saying the process burns ~12,800 t/yr of coal, not charcoal) without substituting the right
units, leaving a literal `n/a` and a nonsensical "coal hectares of forest" in the text a player
is meant to plan from. Not Han-specific -- a plain data/templating bug I happened to hit while
chasing this node on the critical path.

### F-note: capital pinned at 0 while `net_per_year` stayed a large positive number (misleading field)

At year 190-198, after starting the very large `mat_bulk_steel` industry (stated cost 2,316,965;
actual `spent` grew to 3,710,731.1, a 60% overrun) while under a coal, then iron, resource
throttle, `{"cmd":"state"}` repeatedly returned `"capital": 0.0` for at least 8 consecutive
in-game years (190 through 198) while `"net_per_year"` simultaneously reported large positive
figures (165698.5, then 48948.7, then 12132.3) that never showed up as capital growth. Exact
sequence: year 190 `capital:0.0, net_per_year:165698.5`; year 193 `capital:0.0,
net_per_year:48948.7`; year 196 `capital:0.0, net_per_year:12132.3`; year 199 `capital:-800.0`
(so it is not floored at zero, it can go negative -- it just happened to sit at exactly 0.0 for
years). Every one of those years also carried a `"SHORT OF <MATERIAL>"` event capping work at
18-24% of plan. My reading: `net_per_year` is the nominal/target income rate the model would
achieve unthrottled, not the throttled cash actually banked that year, and nothing in `state`
distinguishes the two -- a player watching only `net_per_year` (as the brief's own economics doc
tells you to) would believe the economy was healthy and growing by tens of thousands a year while
capital in fact did not move for the better part of a decade. This is the clearest "the game told
me something that turned out to be misleading once I acted on it" finding of the run.

### F2. Crisis knowledge-loss reverted a Han STARTING TECH, not just earned progress
- **Severity**: BUG
- **What I saw**: At year 192, `step` returned the event `"Yellow Turban rebellion: a site is
  sacked"` immediately followed by `"KNOWLEDGE LOST: 23 technologies forgotten (the corpus was
  never printed and dispersed)"`; a second sacking at year 199 cost 14 more. `path.remaining_count`
  for `point_contact_transistor` went from 62 (year 184, before the rebellion) to 99 (year 211,
  after both sackings) -- it should only ever fall as I complete nodes, and instead rose by 37.
  `{"cmd":"why","id":"point_contact_transistor"}` afterward listed `galena_detector`,
  `gp_whisker_forming`, `micrometer_gauges`, and `prc_lapping_plate` back in
  `missing_prerequisites` -- all four had been completed (`step` events at years 152, 167 (via
  screw_lathe date correction), 174, and 179 respectively) and were direct prerequisites of the
  goal itself. Trying to restart them cascaded further: `gp_whisker_forming` came back
  `"missing prerequisites: cap_tol_10um, daniell_cell"`, `micrometer_gauges` came back
  `"missing prerequisites: master_screw"`, and `prc_lapping_plate` came back `"missing
  prerequisites: cap_tol_10um"` -- three more previously-completed nodes had also been wiped.
  Most strikingly, `bellows_water_blown` -- one of Han China's twelve declared `starting_techs`
  in `han_china_100ad.json`, granted at year 100 before I issued a single command -- showed
  `{"cmd":"why","id":"bellows_water_blown"} -> "done": false, "can_start_now": true` at year 211,
  and appeared in `next.py`'s on-path-available list needing to be built again from scratch.
- **Why it is wrong**: A random hazard erasing earned research is a defensible, even interesting,
  mechanic (it is exactly what the knowledge base's Third Century Crisis framing promises, and
  the prior Rome WIN report documents the same mechanic costing that run dozens of nodes). But a
  starting civilizational technology -- something the civ file asserts Han has simply *by virtue
  of being Han in 100 AD*, five centuries of prior use in the case of cast iron, water-powered
  bellows since 31 AD -- is not "research the founder did" in any sense a sacked site's archive
  burning down should touch. If a random regional rebellion 90 years later can strip Han of a
  technology it walked in the door with, then the entire premise of question 1 (does the head
  start show up and hold up) has a real, mechanical counter-example: it can be un-given by the
  same dice roll that costs Rome an academy's paper archive. I did not read the tech tree JSON to
  find this; it fell out of ordinary `why`/`path` play after the event surprised me.
- **Reproduce**: Play `han_china_100ad` to the point where `bellows_water_blown` (or any other
  `starting_techs` entry) shows `done: true`, survive a `sacks_a_site: true` hazard window
  (Yellow Turban, 184-205) with `technologies_at_risk` nonzero and no `corpus_dispersed` hedge,
  then re-query `{"cmd":"why","id":"bellows_water_blown"}` (or diff `path`'s `remaining` set)
  before and after.

## Result

**GOAL REACHED.** Final `{"cmd":"state"}` for the run, quoted in full:

```
{"ok": true, "year": 543, "capital": 27003379.7, "revenue": 1603261.6, "upkeep": 462436.0,
"living_cost": 508856.4, "mine_operating_cost": 222750.0, "net_per_year": 409219.2,
"training_pending": [], "founder_hours_available": 13308.6, "founder_alive": true,
"scholars": 59.82, "artisans": 311.58, "directors_extra": 6.06, "reputation": 9.2,
"suspicion": 0.0, "scandal": 2.05, "eminence": 7.68, "protection": 0.421, "familiarity": 0.9,
"done_count": 314, "done_granted": 136, "done_earned": 178, "active": {},
"knowledge_risk": {"technologies_at_risk": 117, "loss_chance_if_a_site_is_sacked": 0.8,
"fraction_lost_when_it_happens": 0.4, "expected_technologies_lost_per_sacking": 37.4,
"hedged_by": null, "better_hedge_available": "corpus_dispersed", "known_hazards_ahead": []},
"resource_throttle": 1.0, "throttle_binding": null, "forest_ha": 7246.9,
"mine_capacity": {"coal": 39600.0, "iron": 19800.0}, "slaves": 0, "freedmen": 160,
"goal": "point_contact_transistor", "goal_reached": true, "goal_year": 542, "manual": true,
"ended": true, "end_reason": "goal reached: point_contact_transistor completed in 542 AD"}
```

`point_contact_transistor` completed in **542 AD**, 442 years after arrival, founder alive
throughout (`founder_alive: true` never flipped in this run; I never saw a founder-death or
founder-mortality event fire, matching what the Rome WIN report also reported -- worth another
playtester specifically forcing `--mortal` or an old founder scenario to test). This is slower
than the ~427 AD median claimed for Han in `ROME_BOOTSTRAP.md`'s five-society table and slower
than the prior `rome_100ad_WIN.md` report's 458 AD for Rome under the same "play straight, one
attempt" conditions -- I take this as a data point about my own play (in particular, the
self-inflicted ~80-year financial stall from years 190-270, see F6, and not restarting the full
depth of the Yellow Turban knowledge-loss cascade immediately, see F2) rather than as evidence
that Han is actually slower than Rome in this engine; the tree gives Han a real, felt head start
(see F-Q1 below) and most of my lost time was mine to avoid.

`done_count` reached 314 (136 `done_granted` ambient/free grants, 178 `done_earned`). Capital
peaked around 27M denarii against an opening balance of 400. The Yellow Turban rebellion (184,
192, 199 -- three sackings inside its window) cost at least 23+14 = 37 directly-observed
technologies in two hits alone, on top of whatever earlier/later sackings I did not separately
log; `knowledge_risk.technologies_at_risk` climbed from 4 (year 100) to 117 (final state) as the
tree deepened, and `expected_technologies_lost_per_sacking` from 1.3 to 37.4 -- I never built
`corpus_dispersed` (see the corpus_written finding above), so this exposure was never hedged, and
by luck no further hazard windows opened between year 280 (end of Three Kingdoms fragmentation)
and the goal.

## FINDINGS

### F1. The ambient "civilization already has a huge backlog of tech" grant is a single Rome-shaped bundle, not keyed to the playing civ
- **Severity**: BUG
- **What I saw**: Starting `han_china_100ad` and stepping one year (`{"cmd":"step","years":1}`
  after starting five free tier-0 nodes) produced 127 `done_granted` completions, the large
  majority Roman-named institutions and infrastructure: `civ_sewer_roman` ("Roman sewer with
  gravity flow"), `civ_aqueduct_roman` ("Roman aqueduct with inverted siphons"), `civ_road_paved`
  ("Roman paved road with surveying"), `civ_arch_roman` ("Roman masonry arch"), `civ_insula`
  ("Insula: Roman apartment block"), `lnd_cursus_publicus` ("Cursus publicus courier service"),
  `sea_pharos_lighthouse`, `civ_amphitheatre`, `hom_cosmetics_roman`, `civ_chorobates`
  ("Chorobates: Roman water levelling rod"), `civ_surveying_groma`, `fin_argentarii` ("Deposit
  bankers (argentarii)"), `fin_annona` ("Annona grain dole and administration"), `fin_collegium`
  ("Professional associations (collegia)"), `med_legal_physician`. `{"cmd":"why","id":
  "civ_sewer_roman"}` and `{"cmd":"why","id":"lnd_cursus_publicus"}` both confirm `cost:0`,
  `"done": true`, unchanged Rome-flavour `note` text ("ROME ALREADY HAS THIS... Imperial dispatch
  relay using stations and fresh horses"), granted anyway to the Later Han Empire.
- **Why it is wrong**: This is not the civ-specific `starting_techs` list from
  `han_china_100ad.json` (which lists 12 real Han techs: blast furnace, cast iron, paper, the
  seed drill, the heavy plough, the horse collar, water-blown bellows, etc., and which I *did*
  see reflected correctly, see F-Q1). It is a separate, apparently civ-blind "ambient tier-0/1
  civilisation base" bundle that fires identically regardless of which civ file is loaded. It
  does not change my time-to-goal (I never saw one of these appear as `on_goal_path: true`), so
  it is cosmetic rather than a balance bug, but it directly undercuts question 3: a Han
  playthrough is credited with the Cloaca Maxima, the cursus publicus, and Roman cosmetics.
- **Reproduce**: `python3 rome/sim/simulator.py agent --civ han_china_100ad`, then
  `{"cmd":"start","id":"cap_heat_0700"}` (and the other four free tier-0 nodes), then
  `{"cmd":"step","years":1}`; inspect the `completed` list, then `{"cmd":"why","id":
  "civ_sewer_roman"}`.

### F2. Crisis knowledge-loss reverted a Han STARTING TECH, not just earned progress, and cascaded through the goal's own direct prerequisites
- **Severity**: BUG
- **What I saw**: At year 192 and again at 199, `step` returned `"Yellow Turban rebellion: a
  site is sacked"` immediately followed by `"KNOWLEDGE LOST: 23 technologies forgotten"` and
  `"KNOWLEDGE LOST: 14 technologies forgotten"` respectively (both messages append "(the corpus
  was never printed and dispersed)"). `path.remaining_count` for `point_contact_transistor` rose
  from 62 (year 184) to 99 (year 211) -- it should only ever fall. `{"cmd":"why","id":
  "point_contact_transistor"}` afterward listed `galena_detector`, `gp_whisker_forming`,
  `micrometer_gauges`, and `prc_lapping_plate` back in `missing_prerequisites`, even though all
  four were completed direct prerequisites of the goal itself (completed at years 152, 174, 179,
  and 179 respectively per earlier `step` events). Restarting them cascaded further back:
  `gp_whisker_forming` came back blocked on `cap_tol_10um, daniell_cell`; `micrometer_gauges` on
  `master_screw`; `prc_lapping_plate` on `cap_tol_10um` -- all three previously completed and now
  wiped too. Most strikingly, `{"cmd":"why","id":"bellows_water_blown"}` -- one of Han China's
  twelve declared `starting_techs`, present before I issued a single command -- returned
  `"done": false, "can_start_now": true"` at year 211 and had to be rebuilt from scratch.
- **Why it is wrong**: A hazard erasing earned research is a defensible mechanic and matches
  the knowledge base's own framing of the Third Century Crisis (the prior `rome_100ad_WIN.md`
  report documents the same class of event costing dozens of nodes). But a starting
  civilizational technology -- one the civ file asserts Han simply *has*, by virtue of being Han
  in 100 AD, with five centuries of prior use behind cast iron and 69 years behind the water-blown
  bellows -- is not "research the founder did" in any sense a sacked archive burning down should
  reach. It directly undercuts question 1: the claimed head start is not a fixed floor the game
  protects, it is exposed to the same erasure roll as anything else, including things Han is
  specifically supposed to already know for free.
- **Reproduce**: play `han_china_100ad` until a `starting_techs` entry shows `"done": true` in
  `why`, survive a `sacks_a_site: true` hazard window with `technologies_at_risk` nonzero and no
  `corpus_dispersed` hedge, then re-query `why` on that same starting-tech id.

### F3. Institution and node-flavour text is unmodified Rome prose regardless of the loaded civ, including the plain `name` field
- **Severity**: UNREALISTIC / CONFUSING
- **What I saw**: Playing Han China, `{"cmd":"start","id":"citizenship"}` returned `"name":
  "Roman citizenship by grant"`, and its `note` reads *"Gives provocatio, the right of appeal,
  which is the difference between a governor executing you and Rome hearing you."* The
  `{"cmd":"step"}` event log itself later read `"completed: Roman citizenship by grant"`.
  `corpus_written`'s `name` is *"Write the corpus: everything you know, in plain quantitative
  Greek and Latin."* `scientific_method`'s `note`: *"the hard part is... displacing Aristotelian
  authority... Contradicting Aristotle and Galen in public... their defenders hold the chairs,
  the patronage and the medical guild."* `arithmetic_positional`'s `note`: *"Frame as recovered
  from Indian sources... Sell it to bankers and the fiscus first."* `patron_local`'s note is
  identical, word for word, to the sentence `03_SOCIAL_POLITICS.md` gives for Rome. The pattern
  recurs across dozens of other nodes I only skimmed once the pattern was clear: `case_hardening`
  ("Roman smiths do all of this already"), `refractory_fireclay` ("Rome has excellent..."),
  `lead_metallurgy` ("Rome does this already and does it well"), `lab_apparatus` ("Alexandrian
  alchemy already looks like this, so it is culturally normal"), `geometry_analytic`
  ("Hipparchus and Ptolemy already have chord tables"), `galena_detector` ("A working
  semiconductor device in Rome"), `mercury_supply` ("Almaden is an imperial monopoly"), and a
  random event string, `"fire in the insula district"` (`insula` is specifically the Roman
  apartment-block type), fired more than once during a Han playthrough. `school_founded` is
  explicitly "the Museum" (Alexandria's). I never once saw a node reference anything Han-specific
  -- no counting rods, no examination system, no *hang* guilds, no Confucian officialdom, no
  eunuch court politics -- despite `han_china_100ad.json` declaring civ-specific `institutions`,
  `values`, and a `w_eminence_danger` note that explicitly names court factions and eunuch
  politics as Han's own version of this danger.
- **Why it is wrong**: This directly answers question 3. It did not "break" anything mechanically
  -- every command still executed, costs still used Han's own multipliers (see F-Q1/F-Q2 below)
  -- but it read as absurd exactly where the brief predicted: a governor's *imperium*,
  *provocatio*, and Aristotle-vs-Galen framing describe institutions and intellectual authorities
  that simply do not exist in the administrative or philosophical world of the Later Han Empire.
  The cost *numbers* are civ-aware; the prose is not, anywhere I looked, including the plain
  `name` field a player reads on every single `start` call.
- **Reproduce**: `{"cmd":"start","id":"citizenship"}` on `han_china_100ad`; compare the returned
  `name` and the `note` from `{"cmd":"why","id":"citizenship"}` against
  `rome/knowledge/03_SOCIAL_POLITICS.md#citizenship`.

### F4. `net_per_year` reports a nominal/unthrottled income rate, not what is actually banked, and gave no warning during an 8+ year real stall
- **Severity**: CONFUSING
- **What I saw**: After starting the large `mat_bulk_steel` industry (stated `cost.total`
  2,316,965; final `spent` 3,710,731.1, a 60% overrun) without first buying enough coal/iron
  mine capacity, `{"cmd":"state"}` returned `"capital": 0.0` for at least 8 consecutive in-game
  years (190 through 198) while `"net_per_year"` simultaneously reported large positive figures
  that never once showed up as capital growth: year 190 `capital:0.0, net_per_year:165698.5`;
  year 193 `capital:0.0, net_per_year:48948.7`; year 196 `capital:0.0, net_per_year:12132.3`.
  Every one of those years also carried a `"SHORT OF <MATERIAL>"` event capping work at
  18-24% of plan, and separately `"MOTHBALLED half the coal/iron workings; you could not pay to
  keep them running"` fired repeatedly, eventually zeroing `mine_capacity` entirely while
  `resource_throttle` stayed stuck at a stale-looking 0.368-0.246 for years with `active: {}`
  (nothing running that the throttle could even be gating).
- **Why it is wrong**: A player watching `net_per_year` (the field `04_ECONOMICS.md`-equivalent
  guidance points you at) would reasonably conclude the economy was healthy and growing by tens
  of thousands a year, when in fact capital did not move for the better part of a decade and then
  went substantially negative (down to -227,944 by year 278) before recovering. Nothing in
  `state` distinguishes "nominal income if unthrottled" from "cash actually received this year."
  This is the clearest case in the run of the game telling me something that turned out to be
  misleading once I acted on (or rather, failed to notice the need to act on) it.
- **Reproduce**: start an industrial-scale node with a large `materials` bill (e.g.
  `mat_bulk_steel`) without first buying matching `{"cmd":"buy","what":"mine",
  "material":"coal"/"iron","n":N}` capacity; step through the resulting `"SHORT OF ..."` events
  and compare `state.capital` across years against `state.net_per_year` in the same replies.

### F5. Long calendar-floor nodes routinely ran well past their stated floor, but not uniformly -- and buying past the floor is not possible even with money
- **Severity**: CONFUSING / WORKS-WELL (mixed; see below)
- **What I saw**: `power_grid` (`calendar_floor_years: 25`, note: *"Money cannot buy this down"*)
  was started at year 434 and did not complete until year 474 -- 40 actual years, a 60% overrun,
  while `founder_hours_left` sat at -432.0 (fully paid off) for at least 25 of those years with
  ample idle `founder_hours_available` elsewhere in the same states. By contrast `railway`
  (`calendar_floor_years: 20`) ran almost exactly on floor (started 401, done ~421) once its
  150-artisan staff gate was cleared, and `zinc_industry_scale` (`calendar_floor_years: 12`,
  `cost.total` 4,382,165) also finished close to its floor. So the overrun is real and can be
  large, but it is not a fixed multiplier on every node the way it looked in the prior Rome WIN
  report's sample (which found routine 2-4x overruns) -- here most floors were honoured within a
  few years and one (`power_grid`) blew far past it for reasons `state`/`why` never surfaced
  (no throttle was active; `resource_throttle` read `1.0` through the whole stretch I checked).
- **Why it matters**: this is a real, reproducible case of a "money cannot buy this down" floor
  being both true (money never sped it up) and unreliable as a planning number (the floor badly
  under-predicted actual duration for this specific node, for no reason visible through the
  protocol). I could not tell, from `available`/`why`/`state` alone, why `power_grid` in
  particular overran so much more than its neighbours.
- **Reproduce**: `{"cmd":"start","id":"power_grid"}` once its prerequisites are met, then
  `{"cmd":"step"}` in a loop watching `state.active.power_grid.years_in_progress` against the
  25-year `calendar_floor_years` reported by `{"cmd":"why","id":"power_grid"}`.

### F6. WORKS-WELL: the economic feedback loop for over-extension is real, consistent, and recoverable -- I was never punished for drama, only for my own sequencing mistake
- **Severity**: WORKS-WELL
- **What I saw**: Starting `mat_bulk_steel` (a huge coal/iron consumer) before owning matching
  mine capacity triggered a genuine, multi-decade financial crisis (F4): shortage events, mine
  mothballing, capital swinging from +2.85M to -227,944 over about 45 years (years 184-270). I
  initially treated negative capital as a hard stop and paused starting new projects for over a
  decade of game time -- which was my own misreading, not a game constraint: `{"cmd":"start"}`
  is never gated by capital (only `{"cmd":"buy"}` is), so the "dead end" I thought I had hit was
  self-imposed. The moment I resumed starting on-path nodes despite deeply negative capital
  (`year 270, capital: -193,674`), the economy recovered on its own within about 30 years purely
  from completed-node revenue, with no further intervention beyond ordinary play, back to
  `capital: 995,576` by year 313.
- **Why it is right**: this is exactly the kind of consequence the brief asks about -- "did
  anything punish you for drama rather than for a real reason" -- and here the answer is no: the
  punishment (a long, painful, but survivable debt spiral) was a direct, legible, and fair
  consequence of a real sequencing mistake (buying an industry before its fuel supply), not an
  arbitrary or hazard-driven penalty. It was also recoverable through ordinary play once I
  understood the mechanic, which is the right shape for a lesson like this.
- **Reproduce**: start `mat_bulk_steel` or any similarly large `materials`-heavy node without
  first buying matching `mine` capacity; observe `"SHORT OF <MATERIAL>"` and `"MOTHBALLED..."`
  events and the resulting capital trajectory; then resume starting cheap on-path nodes despite
  negative capital and watch revenue recover it.

### F7. WORKS-WELL: `why`'s `start_blocked_reason` gives an exact, actionable fix for staff-headcount gates
- **Severity**: WORKS-WELL
- **What I saw**: `{"cmd":"why","id":"railway"}` returned `"start_blocked_reason": "needs 150
  trained artisans, you have 121.6. To get more artisans: {\"cmd\":\"buy\",\"what\":\"slaves\",
  \"n\":N} then manumit, though they are untrained for three years."` This was accurate and
  sufficient on every occasion I hit it (`railway`, `power_grid`) -- buying and manumitting the
  stated shortfall (plus a margin, since the artisan headcount also drifts down between checks)
  reliably cleared the gate a few years later.
- **Why it is right**: this is the single most useful machine-readable field in the whole
  protocol for the "what do I do now" question, better than `available`/`path` alone (neither
  surfaces a staff-headcount gate as a startable node -- there is nothing to `start` to fix it,
  only something to `buy`). It is exactly the kind of information the brief's premise (JSON
  protocol only, no strategy files) depends on existing somewhere, and here it did.
- **Reproduce**: `{"cmd":"why","id":"railway"}` (or `power_grid`) while short on `staff_needed`
  artisans.

## Answering the assignment's questions directly

**1. Does the metallurgy/paper head start actually show up in play?** Yes, concretely, in two
places I could measure. First, `{"cmd":"available"}` returned 366 startable items at year 100
before I issued a single command (versus the prior Rome report's five free tier-0 nodes), and
`state.done_earned` was already 11 before any action -- the twelve `starting_techs` in
`han_china_100ad.json` (blast furnace, cast iron, `cap_heat_1300`, paper, the seed drill, the
heavy plough, the horse collar, water-blown bellows, etc.) came in as real, immediately-useful
prerequisites, not flavour: `finery_puddling`'s own `why` output at year 117 showed
`direct_prerequisites: ["blast_furnace", "cap_heat_1300"]` both already satisfied, letting me
reach a 96,830-denarius industrial iron process by year 129 with no detour through charcoal-era
bloomery iron at all. Second, `cost_multipliers` in the civ file (metallurgy 0.7x, casting 0.65x,
paper 0.5x, information 0.6x) are real numbers applied to real node costs, not just documentation
-- though I did not do a side-by-side Rome run in this session to quote exact before/after
figures for the same node, so I can't give a precise percentage here. Against that: F2 shows the
head start is not permanently protected -- a starting tech can be stripped by an unrelated crisis
roll decades later, which is a genuine crack in the "starts several rungs up" premise.

**2. Is the commerce handicap noticeable, and did it push me toward a different strategy?**
Honestly, no, and this itself is worth reporting. `han_china_100ad.json`'s `cost_multipliers`
name `commerce: 1.15` and `finance: 1.2` as penalties, with `handicap_remedies` naming
`patron_imperial` as the only fix. But every `fin_*`-prefixed node I actually saw
(`fin_argentarii`, `fin_annona`, `fin_collegium`, `fin_market`, `fin_coined_money`,
`fin_contract_law`, `fin_tax_farming`, `fin_wage`, `fin_government`, `fin_societas`,
`fin_auction`, `fin_maritime_loan`, `fin_testament`) arrived through the free F1 ambient-grant
bundle at `cost: 0`, never as something I paid for and could feel a multiplier on. Their `cat`
field reads `"banking"`, not `"commerce"` or `"finance"` -- I could not identify, from `why`'s
output alone, which nodes if any were actually being taxed at 1.15x/1.2x, since none of the
`cat` values I observed match those two multiplier keys literally. I finished the entire game
without ever starting `patron_imperial` (the stated remedy) or feeling blocked by anything I
could attribute to the commerce penalty -- my bottlenecks throughout were metallurgy/fuel-supply
sequencing (F4/F6) and staff headcount (F7), never money-raising itself. If the commerce
handicap is real in the numbers, it never surfaced as a felt constraint or a strategic fork in
this run, which is either a sign it is well-hidden behind the free-grant bundle, or a sign it
does very little in practice for a player who never touches finance-tagged nodes directly.

**3. Did the Roman-named social nodes read as absurd for Han China? Did anything break or read
as nonsense?** Yes, repeatedly and concretely -- see F3. Nothing crashed and every command still
executed correctly against Han's own numeric costs, but the *names and prose* are unmodified
Rome, down to the plain `name` field (`"Roman citizenship by grant"`) and random event strings
(`"fire in the insula district"`). The single clearest example: writing down everything the
founder knows, the actual prerequisite for the crisis-survival hedge, is named *"Write the
corpus: everything you know, in plain quantitative Greek and Latin"* while playing a civilization
whose scholarly language is Classical Chinese. Nothing about eunuch politics, the examination
system, or Han's own `hang` guilds appears anywhere I looked, despite the civ file declaring all
three as load-bearing facts about this specific society.

**4. Was `knowledge_risk` useful, and were Han's hazards different from Rome's in an actionable
way?** Yes to both, with one caveat. The field itself was useful and honest: it named both Han
hazards by year range and mechanism from turn one (`Yellow Turban rebellion, 184-205,
sack_chance_per_year: 0.2` vs `Three Kingdoms fragmentation, 220-280, sacks_a_site: false`),
tracked `technologies_at_risk` and `expected_technologies_lost_per_sacking` rising accurately as
my tree deepened (4 -> 52 -> 117 across the run), correctly emptied `known_hazards_ahead` once
both windows had passed, and named the specific hedge (`corpus_dispersed`) that would reduce the
loss. That is real, actionable, civ-specific information, and it is structured differently from
what I'd expect Rome's version to show (Han gets two distinct hazard types -- one that sacks a
site and steals knowledge, one that is pure output throttling with no sacking -- rather than a
single crisis window). The caveat: knowing about the hazard and being able to afford the hedge in
time are different things. `corpus_dispersed`'s own chain reported `critical_path_years: 20.5`,
which could not finish before the 184 AD window regardless of when I started looking at it
(I checked at year 179, five years out), so for a first-time player the field told me the truth
early enough to *see* the risk but not early enough to *fix* it on this run's actual timeline --
a player would need to prioritize `corpus_written`/`printing_press`/`corpus_dispersed` from very
early game, well before the field's numbers make the hedge look urgent, to actually beat the
clock.

**General: was it playable? Did anything mislead me? What did I learn the hard way? Was I
punished for drama rather than a real reason?** Playable, yes, with the same caveat the Rome
report gave: `available` intersected with `path`'s remaining set produced a legal move almost
every time there was a choice to make, and `why`'s `start_blocked_reason` (F7) reliably told me
exactly what to fix, including for staff-headcount gates that `available`/`path` alone give no
way to act on. `net_per_year` (F4) is the one field that actively misled me, for over a decade of
game time. What I learned the hard way: that `start` is never capital-gated while `buy` always is
(F6), and that starting a huge fuel-hungry industry before owning matching mine capacity produces
a long, real, and initially confusing financial crisis. That crisis (F6) was not drama for its
own sake -- it was the direct, fair, fully-recoverable consequence of my own sequencing mistake,
exactly the kind of "punished for a real reason" outcome the brief's question is fishing for a
contrast against, and I could not find a genuine counter-example: every costly setback in this
run (the Yellow Turban knowledge losses, the fuel-supply spiral) traced back to either a
telegraphed hazard I chose not to hedge against in time, or a resource-planning mistake I made
myself.
