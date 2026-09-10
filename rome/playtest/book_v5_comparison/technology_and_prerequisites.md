# Book v5 vs. the tech tree: technical content and prerequisites

Scope: technical facts, bottlenecks, and prerequisite chains only. Narrative
pacing and the social/economic model are covered by other researchers and are
mentioned here only where they materially change a technical claim.

Primary book sources: `book_v5/TECH_GAP_AUDIT.md`, `book_v5/V2_TECH_DEEP_DIVE.md`,
`book_v5/research/tech_feasibility.md`, `book_v5/bible/04_tech_schedule.md`,
`book_v5/V2_MASTER_CONTEXT.md`. These are planning/research documents, not the
manuscript prose itself; `TECH_GAP_AUDIT.md` shows several of the technologies
below (generator, arc lighting, reading lenses, flying shuttle, ball bearings,
typewriter, mechanical calculator, centrifugal pump, oxy-hydrogen, coal gas,
photography) were **planned but confirmed absent from the actual chapter text**
as of that audit. I treat the planning docs as the book's authoritative
technical position (that is what they are for), but flag where a claim never
made it onto the page.

Tree sources: `rome/sim/simulator.py` (`path`, `why`, `costs`, `validate`),
`rome/data/tech_tree.json` (2,828 nodes), `rome/data/branches/CONTRACT_V2.md`,
`rome/knowledge/*.md`.

---

## 1. What the book treats as load-bearing

Ranked by how many other things the book's own planning documents say wait on
them (not by drama):

1. **Precision length measurement, bootstrapped from geometry alone.**
   `V2_TECH_DEEP_DIVE.md` and `04_tech_schedule.md` both single this out by
   name as the correction to a wrong prior model: "V1 treated precision as one
   monolithic unavailable thing. WRONG." The three-plate method (two plates
   converge on a sphere, three plates can only converge on flat), vernier
   calipers, go/no-go gauges, and a boring bar on a fixed guide are all
   explicitly said to need "nothing any Iron-Age workshop does not already
   have." Everything downstream — gears, cylinders, screw threads,
   interchangeable parts, clock trains — is gated on this chain.
2. **Furnace temperature measurement**, via the "Precision Bootstrapping
   Loop" the book names explicitly (see §5): Volta pile → galvanometer →
   iron/copper or platinum/iron thermocouple → ±30–50°C furnace reading →
   better steel → better boring bar → better steam engine → better machine
   tools → better gear cutting → better clocks → better scientific
   measurement → better thermocouple calibration (loop closes).
3. **Better steel**, gated on the above two. Named directly as "the
   chokepoint" in `tech_feasibility.md` ("Steel is the **chokepoint** —
   Daniel should understand that almost every Tier-3 dream (cannon, springs,
   clocks, engines) dies here").
4. **The printing press / movable type**, called the book's single
   highest-value early move and explicitly framed as an *infrastructure*
   technology rather than a product: "The printing press, ironically, solves
   [the bandwidth-of-craftsmen problem]: once Daniel can print instruction
   manuals, calibration standards, and experimental records, the knowledge
   propagation problem shrinks dramatically and the pace of all other
   development accelerates" (`V2_TECH_DEEP_DIVE.md` §4). This is a *diffusion
   multiplier* claim, not a materials prerequisite claim — see §9 for how the
   tree handles (or fails to handle) this.
5. **Water power, repurposed.** Not invented, just redirected: bellows,
   trip-hammers, stamp mills, fulling, later the spinning wheel. Explicitly
   named as the prerequisite that unblocks the steel-temperature problem
   ("Water-powered bellows addresses temperature control for steel," Phase B).
6. **The Volta pile → zinc/copper/brine chain**, load-bearing for four
   separate downstream programs the book lists: galvanometer, compass,
   thermocouple pyrometry, electrolysis (hydrogen for oxy-hydrogen torch and
   lift balloons), and eventually the generator.
7. **Hindu-Arabic positional numerals.** Zero materials cost, called
   "Daniel's single most realistic high-impact win" and the opening move of
   the whole schedule (Phase A, week one).

---

## 2. What the book identifies as the real bottlenecks (with numbers)

- **Roman glass, optically:** iron contamination (Fe₂O₃ green-brown tint),
  bubbles from insufficient working time, striations from uneven furnace
  temperature, and consequent refractive-index variation the book puts at
  **n = 1.48–1.55 within a single piece**, against a target of **n variation
  < 0.002 within a single lens blank** for decent optics (`V2_TECH_DEEP_DIVE.md`
  §1, §5 appendix). Fix is manganese dioxide decolorant (already known
  antiquity practice, Daniel just has to demand and pay for it), low-iron
  river-mouth sand, and longer hot/stirred working time.
- **Telescope optics specifically:** objective ~4–6 cm diameter / 50–80 cm
  focal length is "the easier lens"; the **eyepiece** (2–3 cm, 8–12 cm focal
  length) is harder because more curvature is more sensitive to refractive-index
  variation. Binoculars are flagged as a separate, harder problem (matched
  pairs + prisms needing striation-free glass) and explicitly deprioritized.
- **Steel:** carbon content (0.6–1.0% for spring steel) as the uncontrolled
  variable; Roman iron is low-carbon and inconsistent; the missing piece is
  not chemistry knowledge but **temperature measurement and atmosphere
  control** (O₂/CO ratio in the crucible affecting carbon uptake), which the
  book explicitly says the thermocouple chain narrows but does **not** solve.
- **Gunpowder:** ratio given as **75% KNO₃ / 15% charcoal / 10% sulfur**.
  Sulfur and charcoal are trivial; saltpeter is the bottleneck, requiring
  niter beds (composting manure/urine + ash + lime) over **12–24 months**
  minimum, explicitly called "the longest lead-time item" in the schedule,
  plus corning (wetting, pressing, granulating) for usable propellant vs.
  weak "serpentine" powder.
- **Steam pump:** thermal efficiency **~0.5–1%**, cycle **12–16 strokes/min**,
  boiler at **near-atmospheric pressure (0–2 psi gauge)** vs. a genuinely
  dangerous **40+ psi** for Trevithick-class high pressure, which the book
  says is flatly not achievable in the period ("Needs wrought iron/steel. NOT
  achievable in Roman period"). A single pump example: 70 cm bore, 1.5 m
  stroke, 15 strokes/min lifts **~450 L/min from 30 m depth**.
- **Thermocouple drift:** iron oxidizes above **~800°C**, so a base-metal
  thermocouple drifts within weeks to months; platinum is needed for forge
  temperatures (1200–1400°C), sourced as a "waste" byproduct of Spanish gold
  placer mining (heavy, non-malleable grey inclusions already discarded).
  Seebeck output at forge temperature given as **~12–14 mV** (~10 μV/°C),
  detectable only via a compass-needle galvanometer, and read to only
  **±30–50°C**.
- **Pendulum physics:** T = 2π√(L/g); L = 0.994 m gives T = 2.000 s exactly;
  a 1 m pendulum gains/loses 1 second per ~2 mm length change; iron's thermal
  coefficient (12 ppm/°C) shifts a 1 m rod by 0.012 mm/°C, which the book
  flags as a real, non-hand-wavy error source requiring a bimetallic
  compensation Daniel "knows the concept of" but must still build.
- **Type-metal alloy:** lead/tin/antimony is named as the historical answer,
  and antimony is flagged explicitly as uncertain ("Romans have lead and tin;
  controlled antimony alloying is not a known practice, no source checked").

---

## 3. What the book says is harder than a naive reading suggests

- **The mechanical clock escapement.** Explicitly the book's favorite "honest
  failure": Daniel is a 17-year-old, not a horologist, and "most modern teens
  couldn't draw" a verge escapement. The gear-cutting and materials are fine
  (Antikythera proves Hellenistic gear-cutting skill); the **specific
  mechanism memory** is the gap, and it is treated as a genuine, permanent
  in-story failure resolved a generation later by his successor.
- **Manned flight.** Treated as the single riskiest "easy win" in the whole
  premise: envelope weight vs. lift scaling with volume, permeability
  bleeding hot air, sustained heat without burning treated linen, hand-sewn
  seams. The book insists the first manned attempt should **cost a death**
  (Sabinus) rather than succeed cleanly, and frames the unmanned demonstration
  as the actually-easy version people conflate with the much harder manned one.
- **Any high-power optics.** "A crude 2–3x telescope... is the realistic
  ceiling for a long time"; grinding a true spherical curve repeatably by eye
  with no test plate is called "the killer." The microscope-that-sees-atoms
  claim is flagged as a **deliberate lie**, physically impossible at any
  technology level (optical resolution limit, not a period limit).
- **Marine chronometer.** Needs consistent spring behavior over 0–40°C
  shipboard swings; the book puts this a full human generation past Daniel's
  own working lifetime, gated entirely on spring steel.
- **Antimony/type-metal, movable type generally** — flagged as a real
  precision problem (uniform type-body height, casting matrix) even though
  the press mechanism itself is trivial.
- **Reliable field artillery** (as opposed to a fixed siege bombard) — the
  book is explicit that bore tolerance, powder consistency and crew-speed
  for rapid field fire are never solved in the protagonist's lifetime, while
  a slow, heavy, fixed-position bombard is achievable by ~118–122 AD.

What the book says is **easier** than a naive reading suggests:
- **Positional numerals / decimal notation** — zero materials, zero
  precision, spreads in week one.
- **The printing press mechanism itself** — the screw press already exists
  (olive/wine presses); block printing is "very feasible" immediately; the
  press is not the hard part, the type-metal and ink are.
- **Precision flatness/length** (three-plate method) — needs nothing an
  Iron-Age workshop lacks; this is the book's explicit correction of an
  earlier, wrongly pessimistic draft.
- **Heliocentrism** — "costs only words," Aristarchus gives Greco-Roman
  intellectual precedent, zero materials or precision cost.
- **Soap, rag paper, water-cooled distillation condenser** — all graded
  "the gap is one clever part, not a whole science" (paper: the screen mold
  and sizing; distillation: apparatus already exists in 1st-c. Alexandria,
  only the water-cooled coil condenser is missing).
- **The dynamo/generator, once you have the Volta-pile chain** — the book's
  strongest and most debatable "easier than you think" claim (see §12): it
  argues Faraday's 31-year gap (1800→1831) collapses to years because the
  *theoretical insight* (moving a magnet near a wire produces current), not
  materials, was the historical bottleneck, and Daniel starts already knowing
  it.
- **Water-mill repurposing** (bellows, trip-hammers, stamp mills) — Romans
  already run 16-wheel industrial mill complexes (Barbegal); the only missing
  step is pointing the wheel at a new job.

---

## 4. Genuinely unobtainable in period, and the workaround

| Thing | Book's verdict | Workaround used |
|---|---|---|
| True positional/zero numerals | Not in Rome (it's Indian, 9th–12th c. transmission) | Daniel just teaches it from memory; no material substitute needed |
| Pure metallic zinc (for brass *and* for the Volta pile) | Not treated as a separate obstacle at all — book assumes "zinc is in Roman brass" | **Not worked around — the book does not notice this is a problem.** See §12; the tree treats this as a genuine, non-obvious chokepoint the book missed. |
| Antimony for type-metal alloy | Flagged uncertain/unconfirmed for Roman antimony use | Book's fallback: stay on block printing rather than movable type until/unless antimony is confirmed |
| Spring steel (0.6–1.0% C, quenched/tempered) | Genuinely hard; gates chronometer and leaf springs | Bronze leaf springs (already exist, work-hardened by cold hammering) as an explicitly *worse but real* substitute; springless pendulum clock chosen as the first target specifically to avoid the steel dependency |
| High-pressure steam (Trevithick-class, 40+ psi) | "NOT achievable in Roman period" | Substitute the *entire design philosophy*: near-atmospheric Newcomen-class engine that tolerates leaks, not a sealed high-pressure one |
| Nitroglycerin | "Near-impossible and lethal... a 17-year-old attempting this dies, full stop" | Named and refused outright; recorded in the encyclopedia as a warning, never attempted |
| Verge escapement (as a *remembered mechanism*, not a material) | A knowledge gap, not a materials gap | Water clocks and geared astronomical displays instead; the true mechanical clock deferred to the next generation via a cipher note |
| Balloon silk / rubberized fabric | Romans have linen and imported Chinese silk, not airtight treated fabric | Oil/wax-treated linen, accepted as heavier and leakier, accepted crash/death risk rather than solved |
| Concrete | **Not a gap at all** — "Rome is ahead of what Daniel could improvise" | None needed; explicit instruction to the writer to have Daniel learn from Romans, not "introduce" concrete |
| Germ theory (the actual causal science) | "Absolutely unknown, and genuinely centuries premature" | Practices without theory: boiling, handwashing, soap, "tiny invisible creatures the gods send" as a religiously-camouflaged folk framing |
| Photographic fixer chemistry | Explicitly named as the one wall Daniel cannot cross in Phase E | Silver nitrate darkening and camera obscura both work; the failure ("the image arrives and then eats itself") is recorded honestly for a successor |

---

## 5. Explicit prerequisite chains the book states

Quoted or paraphrased directly from the planning documents, since the task
specifically asks these be written down:

1. **The Precision Bootstrapping Loop** (`V2_TECH_DEEP_DIVE.md` §3, stated as
   an explicit numbered loop):
   `Volta pile + galvanometer → thermocouple → furnace temperature reading
   → better steel heat treatment → harder cutting tools → more precise boring
   bar → tighter cylinder → better steam efficiency → more power → better
   machine tools → better gear cutting → better clocks → better scientific
   measurement → better thermocouple calibration → (repeat)`.
2. **Glass clarity chain:** iron-free river-mouth sand + weighed manganese
   dioxide dose + extended hot/stirred working time → clear flat glass →
   (with existing lapidary curved-grinding skill transferred to glass) → lens
   grinding → spyglass (long-focal-length objective first, easier; short
   eyepiece harder) → astronomical telescope (later) → **separately**,
   reading lenses/eyeglasses for presbyopia (Phase E payoff of the *same*
   chain).
3. **Volta pile chain:** zinc (assumed available) + copper + vinegar/brine →
   wet-cell pile → compass-needle galvanometer (wire coil + lodestone
   needle) → magnetic compass (same needle, relabeled) AND → electrolysis of
   water → hydrogen → oxy-hydrogen torch / hydrogen-lift tethered balloon
   (non-manned, so it doesn't breach the post-Sabinus vow) AND → thermocouple
   (feeds loop above) AND → (later) dynamo/generator, once fine wire-drawing
   and stronger magnets exist.
4. **Steam chain:** aeolipile demo → sealed bronze boiler + valve iteration →
   small-bore atmospheric pump (leaky, low-cycle) → boring bar (from the
   precision chain) improves the cylinder → full-scale mine-drainage pump →
   (much later, gated on better castings/valves) Watt-type separate condenser.
5. **Printing chain:** existing screw press (olive/wine) + skilled die-cutters
   (proven by coin dies) + oil-based ink (new chemistry) → block printing
   (immediate) → [antimony/lead/tin type-metal alloy + casting matrix for
   uniform body height] → movable type (multi-year craft program).
6. **Gunpowder/cannon chain:** sulfur (volcanic Italy) + charcoal (trivial) +
   niter beds (12–24 month minimum maturation) → lixiviation/leaching →
   corning (wet/press/granulate) → usable propellant → **separately**, bronze
   casting quality (gated on nothing new) → a cannon that is *deliberately*
   thin-walled and bursts as a proof-of-concept for why better metallurgy is
   needed → (gated on the precision-bootstrapping loop's steel output,
   ~118–122 AD) reliable fixed-position bronze siege bombard → (never, in
   Daniel's lifetime) rapid-fire field artillery.
7. **Radio chain:** Volta pile / dynamo → Wimshurst static generator or
   induction coil + Leyden jar/capacitor → spark-gap transmitter with
   antenna → galena (byproduct of lead smelting) + cat's-whisker wire →
   crystal receiver → electromagnetic earphone (needs the same fine
   wire-drawing as the dynamo) → the *same* Morse codebook already built for
   the optical semaphore network (chain reuse, explicitly noted) → relay
   network. Explicitly **not** gated on vacuum tubes; voice/vacuum-tube radio
   is a separate, later, successor-only branch.
8. **Wire-drawing chain:** calibrated-hole draw plates (already used for
   jewelry/decorative weaving) → fine, even, low-resistance copper wire
   (measured in years of engineering, not blocked) → feeds *both* the dynamo
   (field coils) and the radio receiver earphone (many-hundred-turn coil).

---

## 6. Where the book is technically wrong (worth reporting as fiction being wrong in an interesting way)

- **China and gunpowder by 98 AD.** The book's own research doc flags this
  directly: the premise's assumption that "China had gunpowder by 100 AD" is
  wrong (Chinese gunpowder/incendiary knowledge is 9th century+); `tech_feasibility.md`
  calls this "a good place for Daniel to be confidently mistaken" — i.e. the
  book is aware it is wrong and uses the error as *characterization* rather
  than asserting it as fact. Worth noting as deliberate, not sloppy.
- **Zinc availability for the Volta pile is asserted, not examined** (see §12
  below) — this one the book does *not* flag as uncertain; it states "Zinc is
  in Roman brass (zinc ore was traded)" as if that settles sourcing
  *metallic* zinc, which it does not. This looks like an unexamined error
  rather than a deliberate one.
- **Stirrups "underwhelm."** The book's research explicitly corrects the
  common wish-fulfillment assumption that stirrups are a big unlock: Roman
  four-horned saddles already work well, so the fictional payoff of
  introducing stirrups is smaller than genre convention suggests. Good,
  research-grounded correction.
- **Roman concrete is already better than anything Daniel can add** — again
  a deliberate correction of trope (the "advanced person brings concrete"
  cliché), and factually solid: Roman pozzolanic concrete does outperform
  plain Portland cement in some respects (seawater curing), which the tree
  agrees with (§10).

---

## 6A. A finding not asked for directly, but load-bearing for everything above: the book's own planning documents disagree with each other about what Daniel personally knows

`book_v5/bible/daniel_pre_rome.md` is a character-competency inventory —
what the real-world 17-year-old actually remembers, as opposed to what the
story needs him to accomplish — and it is noticeably more conservative than
`V2_TECH_DEEP_DIVE.md` and `04_tech_schedule.md`, which read as *plot*
planning documents where Daniel already reliably knows the right answer.
Three direct contradictions:

- **Glass clarity.** `daniel_pre_rome.md`, "What Would Take Him Years": making
  crude glass, "doesn't know the flux materials, temperatures, or annealing
  process — would figure out through catastrophic failure." `V2_TECH_DEEP_DIVE.md`
  §1 has him confidently specifying "add black powder from the mine at
  [Sinai/specific source — manganese dioxide deposits were mined]" as
  something "Daniel knows enough to specify... in 98 AD terms." These cannot
  both be true of the same character. The tree's own `glass_clear` node
  happens to agree with the confident version (manganese dioxide is named
  directly), so the tree and the *optimistic* half of the book agree, but the
  book's own character bible disagrees with the book's own technology plan.
- **The generator/dynamo.** `daniel_pre_rome.md`: "Describe how to build a
  crude generator (coil + magnet moving relative to each other = current) —
  cannot name historical generators specifically; might know 'dynamo' as a
  word," filed under years-long trial and error to reach *functional*, not
  merely conceptual. `04_tech_schedule.md` Phase D/E: "Daniel has that
  insight on day one," reducing Faraday's 31-year historical gap to
  "engineering... in years rather than decades" essentially on confidence
  alone. The character bible's version is the more defensible one, and it
  undercuts the schedule's central argument for why the generator should be
  "ACHIEVABLE IN DANIEL'S LIFETIME" rather than a slower, more failure-prone
  program — which matters directly for whether the book actually supports
  reaching `dynamo`-tier tech as confidently as its own schedule claims.
- **Reading lenses / prescription optics.** `daniel_pre_rome.md`: "knows the
  optics; cannot grind a lens to a specific prescription," filed under
  "Can Only Direct, Not Execute." This one is actually consistent with the
  rest of the book's optics chain (grinding is craftsman work Daniel directs,
  not performs), and matches the tree's `lens_grinding`/`telescope` framing —
  flagged here as the one item on this list where the two book documents
  *don't* conflict, for contrast.

This matters for anyone treating `V2_TECH_DEEP_DIVE.md`'s feasibility claims
as ground truth: at least two of its "MAXIMUM priority, achievable in N
years" calls (glass clarity's specific manganese-source knowledge, and the
generator's one-day insight) rest on a level of protagonist knowledge the
book's own character bible says he does not have. The tree, which assumes an
omniscient founder who "carries the blueprints" and treats research as free
(`CONTRACT_V2.md` §2), is consistent with the *optimistic* half of the book
and inconsistent with the *conservative* half — worth knowing when using
`V2_TECH_DEEP_DIVE.md` as a citation for what's "easy," since it is itself
the less-conservative of the book's two internal sources on the question.

---

## 7. Do the tree's bottleneck nodes match the book's bottlenecks?

Yes, closely, for the ones the tree has built out — the semiconductor,
metallurgy, and precision-length branches in particular read as having done
real independent homework rather than tracking the book. Specific matches:

| Book bottleneck | Tree node(s) | Match quality |
|---|---|---|
| Glass iron/striae/bubbles, manganese decolorant | `glass_clear` — "Near-colourless soda-lime glass, and the trick that pyrolusite is glassmaker's soap, are already known... What is missing is control: iron-free sand chosen deliberately, a weighed manganese dose, and a proper annealing lehr." | Near-verbatim agreement, independently arrived at |
| Precision length via three-plate method | `precision_three_plate` — "Two plates lapped together converge on a matched sphere and socket. Three plates lapped in rotation can only converge on flat." | Exact match to the book's Whitworth-method description, including the "needs nothing an Iron-Age workshop doesn't have" framing |
| Steam efficiency ~0.5–1% | `steam_atmospheric` — "Appallingly inefficient, around 0.5 to 1 percent" | Exact numeric match |
| High-pressure steam blocked | `steam_high_pressure` sits three tiers above `steam_atmospheric`/`steam_watt` and is gated on `mat_bulk_steel` | Agrees: atmospheric first, high-pressure much later and steel-gated |
| Niter beds, multi-year slog | `nitre_beds` — "START THIS IN MONTH ONE. It is the longest lead-time item in the tree: the beds take 12-24 months to mature no matter what you spend." | Exact match, same 12–24 month figure |
| Antimony uncertain for type-metal | `printing_press` `req_any` type-metal group: `antimony_kg 1.0, lead_kg 0.6, mat_bronze 0.5` | Tree **resolves** the book's flagged uncertainty by making antimony a quality bonus, not a hard requirement — see §11 |
| Escapement as the hard part of a clock | `clock_pendulum` — "what is missing is the escapement and the pendulum's isochronism" | Matches, though the tree (correctly, for a game about *capability*, not a specific character's memory) treats it as buildable given time/hours rather than permanently blocked by one person's recall — see §13 |
| Spring steel numbers | `mt2_spring_steel` — "0.5-1.0% C steel, hardened and tempered" | Matches book's 0.6–1.0% almost exactly |

---

## 8. Does the book agree the tree's critical path to the transistor is the hard road?

Partially, and this is the most important finding in the report.

The tree's own `path point_contact_transistor` reports a **142.2-year serial
floor, 168 required nodes, ~58,800 founder-hours, ~10.86M denarii**. Its
`knowledge/55_semiconductors.md` "endgame dependency chain" independently
describes a workshop-scale bootstrap — Volta pile → galena detector →
glassblowing/vacuum pumps → discharge tubes → vacuum tube (diode/triode) →
spark radio → germanium sourcing (zinc flue dust or coal ash) → zone refining
→ Czochralski single-crystal growth → four-point-probe metrology →
point-contact transistor — and estimates **"roughly 150-300 skilled
specialists sustained at any time... concentrated in two or three workshops
under continuous patronage," comparable in scale to a legion's engineering
corps or an imperial mint.**

The book's own planning documents get remarkably far along the *first half*
of exactly this chain and independently agree with almost every step:
Volta pile, galvanometer, galena/crystal-radio detector (`radio_spark_to_valve`
matches the book's spark-gap + crystal-set + galena + earpiece description
almost line for line, including reusing the semaphore Morse codebook), and
the dynamo/generator. **But the book's technology schedule stops one entire
epoch short of the tree's actual goal.** `04_tech_schedule.md` explicitly
and repeatedly calls voice/vacuum-tube radio "CORRECTLY BLOCKED" ("vacuum
tubes require a reliable near-perfect vacuum that Roman glass-work cannot
produce"), and the words "transistor," "semiconductor," and "germanium"
**do not appear anywhere in `book_v5`** (checked across the whole tree,
chapters, outline, and bible). The book's ceiling — spark-gap Morse radio, a
Faraday-style dynamo, arc lighting, an unamplified crystal receiver — is
exactly the tree's tier-3/4 midpoint, roughly node `radio_spark_to_valve` /
`dynamo` in the tree's own chain, not tier 5.

This is confirmed directly, not just by absence: `bible/daniel_pre_rome.md`'s
"What He Cannot Do" list states outright, "Build a computer from transistors
or logic gates up," alongside "Build an electron microscope (knows it uses
electrons instead of light; that's it)" — i.e. the book's own competency
model for its protagonist places the entire vacuum-tube/electron-optics/
semiconductor cluster the tree's endgame runs through beyond what Daniel
personally knows, independent of what Roman industry could in principle
build for him.

So: **the book agrees the tree's path is hard and gets every early rung of
it right, but never considers, let alone endorses, the specific claim that a
working transistor is achievable in Daniel's lifetime (or his successor's).**
That is not a contradiction so much as a different stopping point — the
book's Daniel is a "well-funded, systematic, rewards-driven artisan program,"
explicitly *not* a multi-generational, 150–300-specialist state-scale
research institute of the kind the tree's own semiconductor module says the
job needs. If the book's technical judgment on this ceiling is trusted, the
tree's premise (an individual founder reaching a transistor at all) is
several institutional scales beyond what "The Long Way Home" thinks one
funded Roman workshop network can do — worth flagging to the tree's
designers as a genuine question of scope, not a bug: is the simulator
modeling one founder's workshop, or (as `germanium_extraction`'s own note
about a "legion's engineering corps" suggests) an entire empire's industrial
policy? The node costs (capital in the tens of millions of denarii,
tens of thousands of hired-labour hours per late node) already read as the
latter, which is internally consistent with the semiconductor module's own
framing — just far outside anything the book's Daniel ever attempts.

---

## 9. Missing prerequisite edges — ranked, actionable

These are places the book insists on a real technical dependency the tree
either doesn't encode at all, or encodes more weakly than the book's own
research supports. Ranked by how much they matter to the tree's fidelity.
(I did not edit anything; another agent is working the tree data live, so
verify these are still true before acting on them.)

### 9.1 HIGH — Zinc metal isolation is a real, separate, non-obvious prerequisite of the Volta pile, and the tree already models this correctly; **the book does not**, and should. (Not a tree bug — flagging for whichever side of this project writes the book's technical bible next, since it's the single largest "the book got this wrong" finding.)
The tree's `zinc_metal` node ("CRITICAL PATH, and nobody guesses it... Zinc
boils at 907 C, below the temperature at which calamine is reduced, so the
metal leaves as vapour and reburns at the furnace mouth... Without this
there is no good voltaic pile") is historically correct: pre-modern brass was
made by cementation for centuries without anyone in the Mediterranean world
ever isolating metallic zinc; the technique (downward distillation) is a
distinct medieval Indian (Zawar) achievement. The book's `04_tech_schedule.md`
Phase C treats the Volta pile as achievable in "5-10 years once he has the
materials," asserting "Zinc is in Roman brass (zinc ore was traded)" as if
that settles sourcing. It does not: brass proves zinc *ore* is tradeable, not
that anyone can hand Daniel a bar of zinc *metal*. **This is worth surfacing
back to the book side of this project as a correction**, and worth the tree
keeping exactly as strict as it currently is.

### 9.2 HIGH — the tree should double check `arc_furnace_ferroalloys` and the germanium chain's dependency on `power_grid` (civilizational-scale, gated on `railway`) rather than `cap_power_electric` (workshop-scale dynamo)
`arc_furnace_ferroalloys` requires `power_grid` directly, and `power_grid`
itself lists `railway` as a direct prerequisite. `germanium_extraction`
requires `zinc_industry_scale`, which also requires `power_grid`. This means
the tree's critical path to the transistor runs through building a national
railway network and a "Central generation and distribution" grid explicitly
described as "a civilisational-scale project, not a workshop one" — yet the
tree's own `55_semiconductors.md` describes the transistor programme as **"two
or three workshops under continuous patronage,"** never mentioning a grid or
railway, and separately describes `cap_power_electric` (the *workshop-scale*
dynamo) as "enough for arc lights, electroplating, a laboratory." Real
electric-arc ferroalloy furnaces do need megawatt-class continuous power
(so gating on *some* electrical capability above `cap_power_electric` is
plausible), but a railway as a direct prerequisite of a power grid is not
obviously justified by anything in the knowledge base and reads as a
candidate miscalibration — worth the tree-editing agent checking whether
`power_grid`'s `pre: [..., "railway", ...]` is intentional (e.g., steel-plate
and copper-wire supply chain logic) or an accidental over-broad edge.

### 9.3 MEDIUM — `cap_measure_temp_hi` (needed for `crucible_steel`, `cap_heat_1600`, and everything downstream) does **not** require the electrical/thermocouple chain at all — it only needs `cap_heat_1300` + `cap_measure_temp` (a mercury thermometer). This *contradicts* the book's central "Precision Bootstrapping Loop" claim that furnace-temperature measurement is gated on the Volta pile.
The tree is arguably more correct here (Wedgwood-style clay-contraction
pyrometry historically predates the thermocouple by about a century and needs
no electricity), but this is worth flagging explicitly because it means **the
book's own signature mechanism — the loop it names and diagrams as the
engine of the entire middle game — is not the only route the tree allows to
the same capability, and may not even be the fastest one.** If the tree's
designers want the thermocouple path to matter (it exists as
`opt_pyrometer_thermoelectric` / `in2_thermocouple`, gated on `galvanometer` +
`cap_measure_elec`), consider whether it should be *required* for anything,
since currently a clay-cone/color-pyrometer route bypasses it for the steel
chain entirely. Either the tree should make clear the thermocouple route buys
something the clay-cone route doesn't (e.g., the ±30–50°C precision figure
the book gives, versus a cruder color-judgment error band), or the book's
loop should be corrected to note the cheaper alternative.

### 9.4 LOW/INFORMATIONAL — the printing press's "technology multiplier" effect that the book treats as its single highest-priority move is not implemented in the simulator, and the simulator's own code says so.
`sim/simulator.py`, `apply_tech_effects()`, carries this comment verbatim:
*"`_TECH_EFFECTS.json` was written, committed with a description of what it
would do, and never referenced by any code. Printing raised nobody's
literacy; the scientific method reduced nobody's fear of the inexplicable.
The whole argument for teaching and printing early is that they change
people, and the model quietly did not implement it."* Consistent with this,
`printing_press` has only 21 downstream dependent nodes in the whole
2,828-node tree (versus 1,626 for `precision_three_plate` and 1,219 for
`arithmetic_positional`). The book's `V2_TECH_DEEP_DIVE.md` explicitly frames
the press as *the* technology multiplier — the thing that shrinks the
"knowledge propagation problem" for every other program. This is not a
missing DAG edge so much as a missing *mechanic* (a diffusion-speed modifier),
already flagged as dead code by the tree's own maintainers. I'm surfacing it
because it's the clearest case where the book's stated technical priority and
the tree's modeled priority for the same technology diverge sharply, and the
cause is visible and named in the source.

### 9.5 LOW — the book's `04_tech_schedule.md` explicitly proposes **importing saltpeter is not considered** as an alternative to niter beds; the tree already offers this (`nitre_beds` `req_any` includes `exp_trade_route_extend` alongside `manure_kg`), consistent with `CONTRACT_V2.md`'s "nothing is unobtainable, if it's a distant material depend on an `exp_*` node" rule. Not a tree gap — noting because it's a case where the tree's substitution model is strictly richer than the book's, and the book's writers might want to know an import route exists (it would shave real time off the "longest lead-time item in the tree").

---

## 10. Where the tree demands something the book shows being skipped or substituted

- **Movable type / antimony.** Book: stays on block printing rather than
  committing to movable type until antimony is confirmed workable ("no source
  checked on Roman antimony use... correct call"). Tree: `printing_press`
  already encodes exactly this substitution logic via `req_any` (antimony
  1.0 quality, lead 0.6, bronze 0.5) — the tree's node *is* the generalized
  version of the book's specific hedge, and both agree the press mechanism
  itself needs nothing new (screw press already exists in both).
- **Steel type.** Book: repeatedly has Daniel substitute bronze for steel
  where steel isn't ready (bronze cannon barrel, bronze crossbow springs,
  bronze thermocouple wire before platinum). Tree: encodes this generally via
  `req_any` "pressure_vessel" groups on `steam_atmospheric` and similar nodes
  (`mat_bulk_steel 1.0, mat_wrought_iron 0.6, mat_bronze 0.45, mat_copper
  0.35`), matching the book's practice of "worse metal still works" rather
  than a hard steel requirement.
- **Fuel.** Book: coal sourced from Britain specifically because charcoal
  alone caps furnace temperature and deforests. Tree: `steam_atmospheric`'s
  `req_any` fuel group (`coal_coke 1.0, charcoal_industrial 0.7, firewood_kg
  0.45, mat_charcoal 0.7`) matches this substitution logic, and
  `charcoal_industrial`'s own note ("Charcoal supply, not ore, is the real
  ceiling on pre-coke iron output, and it deforests regions") independently
  reaches the book's conclusion.

No case found where the tree *hard-requires* something the book shows Daniel
routing around with a worse substitute and treats as a wall — the tree's
`req_any` substitution mechanic (CONTRACT_V2 §3) generally already covers
the book's improvisation instinct. This is a point of strong alignment
between the two works' underlying engineering philosophy.

---

## 11. Technologies the book describes that the tree has no node for

Checked against the full 2,828-node id/name list.

- **Wedgwood-style clay-contraction pyrometer as a *named, dramatized*
  beat** — the tree has the node (`cap_measure_temp_hi`) but the book never
  considers this path at all (see §9.3); this is really the reverse case
  (tree has it, book doesn't know about it), included here because it's the
  same gap viewed from the other side.
- **A dedicated "self-excitation" dynamo bootstrapping trick.** The tree's
  `dynamo` node calls out a specific, genuinely non-obvious engineering fact —
  residual magnetism in the iron core is enough to start the current buildup,
  so you don't need a pre-existing field magnet ("Nobody guesses this and
  everybody wastes years on permanent magnets"). The book's dynamo section
  treats the generator as basically solved once you have the *theoretical*
  insight (magnet + wire + motion = current) plus fine wire and strong
  magnets; it never identifies the self-excitation chicken-and-egg problem or
  its solution. This is a case of the tree containing a real engineering
  subtlety absent from the book's account, not a missing tree node — noting
  it because it's a place the book's dynamo section reads as easier than it
  actually would be, contradicting its own claimed rigor.
- **Photographic fixer chemistry as a named dead end.** The book explicitly
  writes this as a wall Daniel cannot cross ("the image arrives and then eats
  itself"). No `photography`/`silver_nitrate_fixing`-type node with this
  specific framing was found by name search; if the tree models photography
  at all under another id, it's worth checking whether it encodes fixing
  chemistry as a distinct, separately-gated capability the way the book
  does, since this is one of the book's few explicit "correctly permanently
  blocked, here is exactly why" technical claims. (Not confirmed as a true
  gap without a name search across the full JSON, which the ranking above
  reflects — flagged MEDIUM confidence.)
- **Nitroglycerin as a named, deliberately-refused technology.** The book
  is unusually specific about *why* Daniel refuses it (lethal margin between
  synthesis and detonation, missing precise ratios/temperatures/stabilization
  procedure) as a character choice distinct from a hard technical block. If
  the tree has a `nitroglycerin`/`dynamite`-family node (search turned up
  `chm_dynamite` in the `costs --top 40` output), it's worth checking whether
  its note captures the same "the danger is procedural precision, not
  ingredient sourcing" framing, since the book's version is a genuinely sharp
  technical point (concentrated nitric+sulfuric acid at controlled low
  temperature) that a generic "dynamite" node might understate.

Overall the tree's coverage is broad enough that almost everything the book
names has a corresponding node; the interesting gaps run the *other*
direction far more often (§9, §12): the tree contains real prerequisites and
subtleties the book's planning documents either assert away or never notice.

---

## 12. Summary of the single biggest asymmetry

The book is a story about **one funded, motivated individual with 57 years
and modern conceptual knowledge**, bootstrapping a workshop-scale artisan
program. Its own thesis statement, stated directly in `V2_MASTER_CONTEXT.md`:
*"The bottleneck is not genius. It is courage, credibility, language."* Its
technology ceiling — reached deliberately, and defended in detail — is
spark-gap Morse radio, a self-excited dynamo, battery-bank and later
generator-scale arc lighting, an atmospheric (not high-pressure) steam
engine, and a pendulum clock without a working spring escapement. Every one
of these matches a real rung of the tree's own critical path to the
transistor, and the book's technical research is, rung for rung, careful and
well-sourced (see §7's near-verbatim matches).

The tree's goal is a **point-contact transistor**, which its own knowledge
base says requires "150-300 skilled specialists sustained at any time...
comparable in scale to a legion's engineering corps," a 142-year serial
floor, and (per the current tree data) a national railway and power grid
along the way. The book never claims this is reachable, and its own
technology schedule explicitly and repeatedly blocks the *next* rung up
(voice radio, vacuum tubes) as beyond what one founder's lifetime can do.

Neither claim is wrong: they are answers to different questions. But it means
the two works cannot be fully reconciled by fixing prerequisite edges — the
book's technical vision, read honestly, is an argument that the tree's stated
goal is out of scope for a "Daniel"-style protagonist and belongs, if
anywhere, several generations and an imperial-scale industrial policy later.
That is worth stating plainly to whoever is using this comparison to steer
either project: the tree is not wrong to go further than the book: it is
answering "what could Rome achieve with total commitment," while the book is
answering "what could one smart teenager with 57 years achieve." The
prerequisite-edge fixes in §9 matter regardless of that framing question, but
the framing question is the bigger of the two findings.
