# ROME 100 AD -> MODERN TECHNOLOGY

**A guide, a record, a game and a planning tool for someone sent back to the
Roman Empire under Trajan with the job of rebuilding modern technology as fast
as physically possible.**

The transistor is the *marker* the simulator aims at, because it is the deepest
single point in the tree and a great deal is upstream of it. It is not the
subject. The subject is all 2,833 technologies, and the ones that matter most to
the people who would actually live there are chimneys, water traps, soap, lamps
and clean water.

Everything lives in [`rome/`](rome/). Start with
[`rome/00_BRIEFING.md`](rome/00_BRIEFING.md), then
[`rome/knowledge/03_SOCIAL_POLITICS.md`](rome/knowledge/03_SOCIAL_POLITICS.md),
which is the module that decides whether any of the rest happens.

---

## Scale

**2,833 technologies, 4,745 dependency edges**, across forty domains from
spinning wheels to jet engines to public key cryptography. Every node is costed
in the founder's own hours, hired labour by trade, materials, capital, calendar
floor, failure risk, and how a given society reacts to it.

Three layers, because the point is to show WHY things are hard:

- **34 capability rungs**: furnace temperature 700 C to 3000 C, machining
  tolerance 1 mm to 0.1 micron, vacuum 1 torr to 1e-9, purity 99% to one part in
  a billion, power from muscle to grid, and eight kinds of measurement. A
  technology names the rung it needs and the tree proves you can reach it.
- **A material layer with its own prerequisites**, and **nothing in it is
  unobtainable**. That category used to exist and it was wrong. Rubber is not
  unobtainable, it is in West Africa. Saltpetre is not unobtainable, it
  effloresces on the Gangetic plain, on a route Rome already sails every year.
  Materials that are elsewhere depend on an `exp_*` expedition node that says
  what going to get them costs.
- **The technologies themselves**, with `req_any` substitution groups wherever a
  real alternative exists, because a steam engine does not require coal and does
  not require steel. It requires a fuel and a pressure vessel.

**The transistor needs 158 of them.** The other 2,675 are the rest of
technology, and that is deliberate: a tree that only covers the path to a
transistor is dishonest about what technology is for.

## The answer, in eight lines

Figures below are from the current tree. Where a run count is small the noise
band is roughly plus or minus 25 years, and I say so rather than quoting three
significant figures at you.

- The irreducible serial calendar time to a working transistor is **142 years**
  across 33 nodes, even with unlimited money, labour and life. That is the floor
  and nothing buys it down.
- With the founder immortal, which is the default, the median run reaches it
  around **427 AD**, roughly **330 years** after arrival, in 100% of runs.
- Turning mortality on (`--mortal`) costs about 20 years and still succeeds
  almost always. The programme survives its founder once the school exists.
- **Bare topological order to the goal succeeds 0% of the time. The
  institution-first strategy succeeds 100%.** Nothing in physics requires a
  patron, a school or citizenship. The technical dependency graph and the real
  dependency graph are different graphs, and the second one is the one that
  kills you.
- **Starting money barely matters.** Across the whole range from destitute to a
  million denarii the medians sit inside the noise band. Three centuries of
  revenue swamp whatever you arrive with. Money still matters enormously *later*,
  because it sinks mines and buys protection, but the size of your purse on day
  one is close to irrelevant.
- **The founder skips the charcoal era entirely.** Historical Britain needed
  until 1709 to smelt iron with coke. Someone who arrives knowing what coke is
  builds the coking oven before the blast furnace, so the median run buys zero
  hectares of coppice. The charcoal famine is a constraint on people who have to
  discover coke.
- The binding constraint is therefore **coal, and briefly saltpetre**, not
  knowledge and not money.
- Three things that will surprise you: **Roman *nitrum* is sodium carbonate, not
  saltpetre**; **zinc is the hidden gate on the electrical age**, and at
  industrial scale it is 83% of the entire tree's fuel demand; and **a single
  glass bead is a 250x microscope you can build in a week**.

## The same tree, five societies

The tech tree does not change. The society does, and it is loaded from a JSON
file, so adding a sixth is data rather than code. 12 runs each, so treat the
years as approximate.

| Society | Reaches the transistor | Median years | Why |
|---|---|---|---|
| Han China, 100 | 100% | **313** | Cast iron for five centuries already, the blast furnace, and paper in 105 AD. It starts several rungs up in exactly the places Rome is weakest. |
| Rome, 100 | 100% | 339 | Enormous, rich, superb at concrete, and an elite that despises manual work and has cheap coerced labour, so every labour-saving device is politically unwelcome. |
| Norse Scandinavia, 900 | 100% | 356 | The best ships in Europe and no state at all. Nobody will stop you and nobody can fund you: public works cost nearly twice what they cost Rome. |
| England, 1300 | 100% | 415 | Wool, watermills, chartered towns and a legal system, against a much smaller population. |
| The Mexica, 1500 | 92% | 454 | No domesticable large mammal exists in Mesoamerica. Every load moves on a human back, so animal traction costs 3x and field machinery 2.4x. That single fact, which the founder cannot teach away, is the largest handicap in the file. |

The spread is about 140 years, and the causes are legible rather than a fudge
factor: what a society already has, what it can organise, what it is willing to
tolerate, and in the Mexica case a fact about which animals happen to live on
which continent.

Norse and Mexica both used to fail 100% of the time. Neither failure was a
finding. One was a mine ceiling keyed to a Rome-specific node id, one was a
mine-sizing bug that counted ore in the shortage and bar in the response, and a
third was an enterprise that went bankrupt and could not shut a mine down. When
a run fails, read why before believing the reason it reports.

## How this is graded

**Not by the end date.** Each technology is judged on its own:
*could someone holding exactly this node's prerequisites, and nothing else,
actually build it?*

```bash
python3 rome/sim/treetool.py judge --id zinc_metal
```

gives a report card: grade, tier, direct prerequisites, full ancestry depth,
which capability rungs appear in its chain, cost, calendar floor, and every
defect by name. Across all 2,833 nodes the mean is **97.0/100**.

**Discount that number, and here is precisely why.** Three separate times in
this project the score rose because a CHECK was wrong, not because the data
improved:

1. An early repair pass inferred 112 capability prerequisites from keywords and
   took the score from 80.8 to 98.0. An independent reviewer found all eight
   sampled inferred edges wrong, including a 1300 C blast furnace rung on a
   room temperature explosive and a vacuum rung on mercury extraction, which
   reverses the dependency because distilling mercury is how you learn to make a
   vacuum. All 112 were reverted and inference is now behind a flag nobody
   should use.
2. The social check still tested the v1 `gov`/`sus` scalars after schema v2
   replaced them with `traits`, so it flagged 769 fully tagged nodes as
   defective. Three quarters of the largest defect category was the audit
   looking at the wrong field.
3. The capability check exempted a fixed list of category names, and branch
   authors then invented 240 categories, so it began flagging pure mathematics
   for not declaring a furnace temperature.

The lesson is not that the number is fake. It is that a rising score is evidence
about the checker at least as often as about the data, and this file will keep
saying so. The trustworthy check is
[`rome/data/review/INDEPENDENT_AUDIT.md`](rome/data/review/INDEPENDENT_AUDIT.md),
done by a separate reviewer against a random sample.

## What is not done

Stated plainly, because a list of achievements without this is marketing.

- Every node now resolves to a specific how-to entry: 2,742 of 2,833 linked to
  an anchor rather than to a bare domain module, 88 correctly unlinked because
  they are capability rungs or raw materials, and 3 (`com_led` and two household
  appliances) simply not linked yet. That was the single largest outstanding
  complaint and it is closed for all but those three.
- **192 nodes still declare no capability rung anywhere in their ancestry.**
  Some of those are correct, because an idea needs no furnace. Not all of them,
  and I would rather leave them flagged than infer edges from keywords again.
- **122 nodes are SHALLOW**, meaning their prerequisite chain is thinner than
  the technology really is.
- **Substitution reaches about 12% of nodes.** The mechanism is right and the
  coverage is thin.
- **158 is the closure of a JUNCTION transistor**, the 1951 device, which needs
  a grown single crystal and zone-refined germanium, not just a whisker on a
  point contact. The 1947 point-contact transistor is still in the tree, as a
  milestone on the way to the 1951 one, which is now the goal.
- **Civilization differentiation is still thin, though less thin than it was.**
  Five civilizations are modelled, and the Mexica having no draught animals and
  no wheel now IS modelled as a negative capability (`animal_traction: 3.0`,
  `field_machinery: 2.4` in their `cost_multipliers`, and a `needs_first` gate
  that blocks the horse collar outright until animals are imported). What is
  still thin is that the social nodes are named for Roman institutions
  (patron_senatorial, collegium_licensed) across every civilization, which is a
  real limit on how generic the abstraction actually is.
- The cost model is the weak part throughout. See "How much to trust it".

## What is here

| File | What it is |
|---|---|
| [`rome/00_BRIEFING.md`](rome/00_BRIEFING.md) | Your first thousand days. Read first. |
| [`rome/01_WORLD_STATE_100AD.md`](rome/01_WORLD_STATE_100AD.md) | What Rome has, what it lacks, where every material comes from, what everything costs. |
| [`rome/02_STRATEGY.md`](rome/02_STRATEGY.md) | The master plan and the simulator evidence that it beats the alternatives. |
| [`rome/knowledge/03_SOCIAL_POLITICS.md`](rome/knowledge/03_SOCIAL_POLITICS.md) | **The ten nodes without which every run fails.** Patronage, citizenship, the school, the licence, and why money protects you only once it is converted into obligation. |
| [`rome/knowledge/`](rome/knowledge/) | **The how-to library.** 28 modules of real recipes with masses, temperatures and failure modes, plus a generated index linking 2,742 tree nodes to the specific entry that documents them. |
| [`rome/knowledge/00_NONOBVIOUS_TRICKS.md`](rome/knowledge/00_NONOBVIOUS_TRICKS.md) | **Start here in the library.** The specific physical tricks that make everything else buildable. |
| [`rome/knowledge/95_expeditions.md`](rome/knowledge/95_expeditions.md) | Why nothing is unobtainable, and what going to get it actually costs. |
| [`rome/data/tech_tree.json`](rome/data/tech_tree.json) | **2,833 nodes, 4,745 edges**, fully costed in hours, denarii, materials, risk and social consequence. |
| [`rome/data/civilizations/`](rome/data/civilizations/) | Rome, Han China, Norse Scandinavia, the Mexica, and medieval England, as data. Swap one in with `--civ`. |
| [`rome/data/world/geography.json`](rome/data/world/geography.json) | 21 regions, reach levels, and where 33 distant materials actually are. |
| [`rome/data/world/resources.json`](rome/data/world/resources.json) | Annual output ceilings and the physical conversion ratios: charcoal per hectare, charcoal per kg of iron, saltpetre per square metre of nitre bed. |
| [`rome/data/branches/`](rome/data/branches/) | Per-domain source files, plus the CONTRACT and VOCABULARY the branch authors worked to. |
| [`rome/sim/treetool.py`](rome/sim/treetool.py) | Merge, repair, and **JUDGE EACH TECHNOLOGY IN ISOLATION**. |
| [`rome/sim/simulator.py`](rome/sim/simulator.py) | The tool. Validates, plans, Monte-Carlos, ablates, sweeps and plays. |
| [`rome/data/review/INDEPENDENT_AUDIT.md`](rome/data/review/INDEPENDENT_AUDIT.md) | A hostile reviewer's findings, and my resolutions, including the ones where the reviewer was right and I was wrong. |

## Run it

```bash
python3 rome/sim/simulator.py validate                       # DAG, prices, reachability
python3 rome/sim/simulator.py path                            # the critical path, costed
python3 rome/sim/simulator.py why zinc_metal                  # explain any single node
python3 rome/sim/simulator.py costs --top 25                  # where the money goes
python3 rome/sim/simulator.py civs                            # the societies you can play
python3 rome/sim/simulator.py run --civ norse_900ad           # same tree, different people
python3 rome/sim/simulator.py run --kit destitute             # arrive with nothing
python3 rome/sim/simulator.py compare --mc 200                # topological vs institution-first
python3 rome/sim/simulator.py sensitivity --mc 300            # what is each choice worth
python3 rome/sim/simulator.py sweep capital                   # how much gold should you bring
python3 rome/sim/simulator.py run --mortal                    # turn death back on
python3 rome/sim/treetool.py  judge                           # score all 2,833 nodes
python3 rome/sim/treetool.py  judge --id zinc_metal           # one report card
python3 rome/sim/treetool.py  merge                           # branches -> tree
python3 rome/sim/simulator.py play                            # play it year by year
python3 rome/sim/simulator.py play --manual                   # real free choice: nothing starts but what you start
python3 rome/sim/simulator.py agent                            # JSON protocol: let a script or an AI play instead
python3 rome/sim/simulator.py agent --script commands.json     # same protocol, from a file instead of stdin
python3 rome/sim/build_index.py                               # regenerate the library index
```

No dependencies beyond the Python 3 standard library.

## The premise

You speak Latin and Greek. You pass as a Greek physician and natural philosopher
of Alexandria, which is the cover that explains your accent, your apparatus,
your chemistry and your interest in bodies and minerals, and which is not a
magician, a prophet or a priest, those being the three identities that attract
prosecution.

**Research is free. Building is not.** You carry the blueprints, so you do not
have to invent the flyer, the lockstitch or the p-n junction; you can draw them
on the first day. What costs you is teaching, specifying, debugging a first
article, and then physically constructing the thing. A delay that happened
historically because nobody knew the answer is not a cost you pay. A delay that
happened because a furnace takes two years to build still is.

You know when the plagues come. Nobody else does. That is worth more than any
machine in this document.

## How much to trust it

Honestly: **trust the ordering and the failure modes; do not trust the absolute
years to better than a factor of about 1.5.**

The dependency structure is the strong part, and it is checkable. The cost model
is the weak part: bulk Roman commodity prices are reconstructed from the Edict
of Diocletian, which is 301 AD and denominated in a currency that had already
collapsed, so it is used for ratios only. Every such figure is tagged `[C]` in
the data. Mining costs are derived from a hewer's daily output and the attested
miner's wage, and they are labelled DERIVED in the source rather than presented
as measurements.

The simulator is also allowed to criticise its own author, and it has. The
ablation study reports that one of the revenue businesses in my recommended
strategy costs more founder-hours than it returns, and I left the finding in
rather than tuning it away. More sharply: two commits before this file was
rewritten I reported that a successful run buys about 8,000 hectares of coppice
and that charcoal was a binding constraint. Modelling fuel substitution properly
overturned that completely, and the honest reading is that the earlier finding
was an artefact of a substitution mechanism that existed but was never connected
to the material demand it was supposed to change.
