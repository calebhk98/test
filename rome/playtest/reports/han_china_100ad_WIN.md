# han_china_100ad / WIN

## STATUS: IN PROGRESS

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
