# Round two findings, and who is fixing what

Four testers: three naive agents on Norse 900 (play / break / weird) and a
fourth playing independently and reporting separately. Their notes are the
`.md` files beside this one; that fourth report is quoted inline below where it
is the only source.

Some of what they found was already fixed while they were still playing, and is
marked CLOSED with the reason. Everything else is open work.

---

## Already closed

| Finding | Where it stands |
|---|---|
| `available` returns one huge object; 86 entries at the start, 186 after the first wave, and the tool output truncated | CLOSED. It is a digest by subject now, with `subject`, `find`, `afford`, `limit`/`offset` and `all:true`. 21.5KB to 4KB at the start; 165KB to 7KB at year 250. |
| `simulator.py --help` is a wall | CLOSED. 5.6KB to 1.4KB; the design essay moved to `rome/sim/PROTOCOL.md`. |
| `state` repeats a hazard briefing on every call | CLOSED. Short by default; `full:true`, plus `risk`, `money`, `labour`, `policy`. 4KB to 1.5KB. |
| `work` sells the same year's hours twice | CLOSED. Wage hours are committed hours now, and the tally persists across sittings. |
| Wage arbitrage: work as a scholar for 1,416/yr, hire one for 625 | CLOSED. Both sides read the same wage table. |
| `founder_hours_left` goes negative (-776.8) | CLOSED. Floored at zero. |
| `start` names undiscovered prerequisites; a 20-line crawler mapped 163 nodes | CLOSED. Names only what you have heard of and counts the rest. |
| Advice says "build workshop_first" while `why workshop_first` says you have never heard of it | CLOSED. Advice is filtered by visibility. |
| `NaN`/`Infinity` walk through every guard and poison the save file | CLOSED. Rejected centrally, before anything is touched. |
| `policy` reads the string `"false"` as true | CLOSED. |
| Deficit softlock: sheds profitable works, keeps the loss-maker, ignores `auto_shed:false`, and `mothball` refuses the thing bankrupting you | CLOSED. Sheds only what costs more than it returns, honours the switch, and a deliberate shutdown is allowed where automatic abandonment is not. |
| Same `--seed` gives different answers on alternate runs | CLOSED. Three float accumulators iterated a set; summation order changed the last bits and five centuries amplified it. |
| `mil_atomic_bomb` buildable in 978 for 341 denarii | CLOSED. Now needs fission, uranium extraction and an ultracentrifuge. |
| `mil_plate_armour_firearms` startable in 900 with no prerequisites | CLOSED. Needs the matchlock. |
| Fire "in the insula district" of a Norse settlement | CLOSED. Each civilisation names its own quarter. |

---

## A. The setting is Rome wearing a hat  (data)

The loudest finding, from all four testers. Playing Scandinavia in 900:

- `labour` says "Rome has these in abundance and they are good" (masons),
  "Roman plumbarii are skilled and numerous", "Rome has military and hydraulic
  engineers under state employ".
- `available` offers "Establish the Alexandrian physician-philosopher persona".
- Node notes say "Rome already has this (Barbegal, 16 wheels)", "Rome never
  develops the chimney", "Buttons exist in Rome but are rare".
- A refusal reads "not bounty-eligible: a Roman artisan could not recognise
  success at this".
- Six to nine nodes cost 0.0 and take 0 hours and 0 years for a Norse founder:
  `civ_arch_roman`, `fin_annona` (the Roman grain dole), `fin_argentarii`,
  `fin_collegium`, `fin_societas`, `hom_cosmetics_roman`. One tester took all
  six on turn one and doubled their reputation and credit limit for nothing.
- `fud_chinampa`, Mesoamerican lake-bed horticulture, is startable in Norway.

The fourth tester: "This seems unintended rather than alternate-history flavor
because it directly contradicts the selected Norse setting."

## B. Anachronism is gated by nothing much  (data)

- Mustard gas: 77.1 denarii and 1.5 years, the moment a chemist exists. No
  chlorine chemistry, no protective equipment, no delivery system.
- `mil_trench`, whose own text describes machine guns, completed in 903.
- `mil_general_staff` and `mil_trace_italienne` completed around 903-904.
- A tethered man-lifting observation balloon is visible at the start.
- New World crops and voyage crops are ordinary purchasable nodes.

"If modern knowledge makes concepts free, prerequisite material/process
readiness still feels like it should gate them."

## C. Knowledge is not a building  (simulator)

Creditors seized 21 works and the founder forgot Newton's laws and basic
textile technique. Earned progress fell from 45 to 24.

"It is unclear whether creditors can logically make society forget Newtonian
physics and basic textile knowledge... Ownership/maintenance-dependent
facilities should be distinct from durable published knowledge."

Related: repossessed works reappear in `available` looking like fresh research
rather than something you already knew and must rebuild.

## D. The automatic policies do not do what they say  (simulator)

- `auto_hire` at turn one hired 1.32 artisans and 0.38 scholars, took living
  cost from 230 to 699.9, and put capital from 400 to -688 with net -462/yr.
  Its own description is "grow the staff toward what you can house and pay".
- `auto_train` began "teaching the first engineers this world has ever had"
  with no active project needing an engineer, and later created chemists,
  machinists and opticians with no active projects at all. Its description is
  "teach trades this society does not have **when a project needs them**".
- Auto-shed events say "stopped maintaining 1 works" without naming them, so
  you cannot tell what you lost or why an option reappeared.
- Fractional people: 1.32 artisans, 0.07 engineers, "you employ no chemists"
  two years after hiring one. Either say what a fraction of a person means or
  do not show one.

## E. Starting work nobody can do  (simulator)

Four engineer-dependent projects were accepted with `ok: true` and then, years
later, `HALTED ... there is nobody here who can do this work (engineer). What
you spent is lost`. A preflight warning should say so at `start`.

## F. Founder hours are allocated opaquely  (simulator)

Four projects each showed exactly half their founder hours left after one year,
with 2,400 hours available and only about 200 apparently spent. "That equal
halving is confusing and feels artificial; the UI did not explain why."

## G. Five centuries, two events  (data and simulator)

426 years of "fire in the longhouses by the shore" and "banditry or a frontier
war disrupts supply". Christianisation is advertised as a 995-1100 hazard and
produced no event and no visible consequence. No plague, no succession, no
climate, no trade shift, no diffusion of what you introduced.

## H. Smaller, but real  (simulator)

- No command closes a mine. One tester bought a gold mine that produced 0.0
  t/yr, paid every coin they had, got `ok: true` and "Nothing was wasted", and
  was billed 28.1/yr for ever. Operating cost is disclosed nowhere before purchase.
- `save`/`load` is unlimited undo, which defeats fog; `save` writes to any
  absolute path (confirmed into `/etc/`).
- `train` bypasses the supervision cap that `hire` enforces, and pumps the
  labour-market ceiling without limit (smith supply 6,469 to 36,433).
- `step` accepts `years: 100000`; `years: true` steps one year.
- `bribe` works after the run has ended, and charges to reduce 0.00 scandal.
- `hire` accepts `"5"` as a string where `buy` and `start` type-check.
- `buy forest` refuses without quoting the price.
- Under fog the run ENDS on a hidden goal, having said "there is no score" and
  reported `goal: null` throughout.
- A granted capability (`cap_measure_len`) appears in `completed` mixed in with
  things you paid for.

## I. Raw JSON is hard to read  (new work)

"The JSON-lines interface is precise... However, raw JSON is verbose for play
and makes scanning long output harder than a formatted CLI." A human-readable
rendering, alongside the machine one, was asked for by two testers.

---

# Wave two: found while wave one was running, with diagnoses

## J. `why`'s cost breakdown shows a decoy factor  (simulator, confirmed)

A tester checked the itemised cost against its own total across seven nodes and
found the total was 1.4000x the product of the parts every time, and called it
"an undisclosed constant 1.4 overhead multiplier".

It is not undisclosed, it is mislabelled. Diagnosed:

    base_total                                      444.0
    civ_cost_factor                                 1.1
    material_distance_factor                        1.0
    opposition_factor                               1.0
    price_index   <- the field `why` prints         1.0    (this is money_real)
    price_index   <- the number actually multiplied 1.4    (this is price_index)

`_node_explain` fills the field named `price_index` with `s.money_real`, while
`project_cost` multiplies by `s.cost_money_factor()`, which returns
`s.price_index`. Norse prices are 1.4x Roman, so for Norse the breakdown hides
its largest factor and prints a 1.0 in its place. The fix is one line, and the
lesson is that a breakdown offered as an explanation has to reconcile.

## K. `bounty` refuses the one thing this civilisation is best at  (simulator)

Of 86 startable nodes, 80 refuse a bounty. The refusal reads "not
bounty-eligible (tier 1, category personal): a Roman artisan could not
recognise success at this" — in a Norse game. It refuses `sea_skeleton_first`,
shipbuilding, for a civilisation whose own profile says `ships x0.60`, the
thing it is best at in the world.

Two bugs: the eligibility test is tier AND an allow-list of categories while
the help says "tier <=2 crafts", and the refusal text names a Roman artisan
whatever society you are in. Bounty pricing itself is sound (2.5x build cost,
removes 65% of founder hours, verified across six nodes) — leave that alone.

## L. `buy mine` spends everything you have, with no price and no way to ask

    (capital 38,151.6)
    {"cmd":"buy","what":"mine","material":"gold","n":1}
    -> ok: true, commissioned 0.17 t/yr, capital 0.0,
       "Nothing was wasted, you paid only for what was sunk."

One tonne a year is the same order as the example in the help text. There is no
quote, no dry run, and no per-tonne sinking cost anywhere in `why` or `state`.
Five years later the workings were mothballed for non-payment and the founder
was in debt bondage. Separately, a small gold mine reports `"gold": 0.0`
capacity while charging 588/yr of operating cost.

Needs: a price before it commits, an operating cost disclosed before purchase,
and a command to close a mine (there is `mothball_mines` internally and no way
for a player to ask for it).

## M. The robustness batch  (simulator)

- `save` writes to any absolute path, confirmed into `/etc/`; a relative path
  drops files into the repository root. `load` validates nothing.
- `save`/`load` is unlimited undo, which defeats fog of war entirely.
- `step` accepts `years: 100000`; `years: true` steps one year.
- `bribe` works after the run has ended and charges to reduce 0.00 scandal.
- `hire` accepts `"5"` as a string where `buy` and `start` type-check.
- `buy forest` refuses without quoting the price.
- `train` bypasses the supervision cap `hire` enforces, and pumps the labour
  market ceiling without limit (smith supply 6,469 -> 36,433).
- You can be paid to work as, and can train, engineers, chemists, electricians,
  machinists and opticians in the year 900 — the trades the game itself says do
  not exist yet.
- The founder is immortal in every civilisation and `--mortal` is the only way
  off; a 500-year run has no succession.
- Under fog the run ENDS on a hidden goal after saying "there is no score" and
  reporting `goal: null` throughout.
- A granted capability appears in `completed` mixed in with things you paid for.

## N. A human-readable rendering  (new work)

Two testers asked for it. The JSON is precise and unreadable; a formatted view
for a person, alongside the machine protocol, not replacing it.

## P. A hazard can only be four numbers  (engine)

Found by the agent fixing the civilisation data, and it is right to have
refused to fake it.

`_shocks` reads exactly four fields off a hazard: `staff_loss`, `sack_chance`,
`output_factor` and `real_erosion`. Norse Christianisation's real effect is
none of those. It is a shift in the society's `values` vector — more religious
rigidity, more fear of the inexplicable — which is precisely the thing that
decides whether your work gets you patronised or denounced, and the schema
cannot carry it. The agent used `output_factor` as the closest honest stand-in
and wrote ENGINE TODO in the hazard's own note rather than inventing a field
nothing reads.

The fix is to let a hazard carry a `values` delta and have `_shocks` apply it,
the same way `apply_tech_effects` already applies a technology's effect on the
society. The machinery exists; the hazards just cannot reach it.

Worth noting what this makes possible: a civilisation whose values move against
you mid-run is the sharpest version of the danger this game models, and at
present every hazard can only kill people, burn a site, or make you poorer.

---

# Round three: what the model does not represent

Not bugs. Things the simulator has no opinion about, found by being asked
directly whether it did.

## Q. Literacy is tracked, changed by technology, and read by nothing

Every civilisation file carries `literacy_general` and `literacy_elite`, and
`apply_tech_effects` raises both when the printing press is built. Nothing
else in the engine ever reads either number.

So hiring a scribe in a society where two per cent of people can read costs
exactly what it costs anywhere else, and is exactly as easy. The pool of
people who can be taught a trade that needs reading is unbounded. Raising
literacy is currently a stat that goes up.

What it should do: bound the hiring pool for literate trades to some fraction
of the population that can actually read, so that in a low-literacy society
money genuinely cannot buy you scribes, engineers or chemists — and so that
printing, schools and libraries pay off by widening the pool rather than by
incrementing a number nobody reads. This is also the mechanism by which
teaching changes politics and religion, which the values vector already
models and the literacy fields currently do not feed.

## R. The market only responds to demand for slaves

`market_pressure` exists and works: buying people in bulk bids their price up,
it remembers between purchases, and it decays. Nothing else in the economy has
an equivalent.

- Materials have `MARKET_SHARE`, which is a supply CEILING — how much of the
  empire's output you may buy — with no price response at all. Buying the
  ceiling costs the same per tonne as buying a kilogram.
- Wages are a fixed table. Hiring half the smiths in a town does not move
  smith wages, and `market_supply` is likewise a ceiling rather than a price.
- Supply works in one direction only. Nothing you build makes anything
  cheaper. Opening a mine does not lower the price of iron for you or anyone
  else; teaching fifty machinists does not reduce what a machinist costs.

Both halves matter, and the second may matter more: a large part of what an
industrial revolution IS, is the price of iron and labour falling because
supply rose. The model currently cannot express that.

## S. Small gaps in the machine list

Present and correctly wired: 72 mining nodes (pumps, drainage, blasting,
flotation, leaching, amalgamation), steamship components, submarine hull,
ironclad, helicopter rotor, jet engine, powered aeroplane, tank, ballistic
rocket, automobile, locomotive, railway, 36 radio and telegraph nodes, arc and
incandescent lighting, street lighting, washing machine by hand and electric,
home refrigerator, kitchen range, electric fan, central heating.

Absent: the light-emitting diode, the clothes dryer, and the domestic freezer
as distinct from the refrigerator.
