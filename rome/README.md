# rome/ — how this project is put together

Three artefacts that share one dataset.

```
rome/
├── 00_BRIEFING.md            your first thousand days
├── 01_WORLD_STATE_100AD.md   what Rome has and lacks, materials, prices, mindset
├── 02_STRATEGY.md            the plan, the phases, and the evidence for them
├── 03_SOCIAL_POLITICS.md     patronage, law, what the State funds, what kills you
├── 04_ECONOMICS.md           labour, materials, transport, where the money goes
├── LABOR_LEDGER.md           the founder's hours, and the author's
├── knowledge/                THE HOW-TO LIBRARY (start at 00_NONOBVIOUS_TRICKS.md)
├── data/
│   ├── tech_tree.json        127 nodes, 251 edges, fully costed
│   └── prices.json           wages and commodity prices, confidence-tagged
├── sim/
│   ├── simulator.py          validate / path / costs / run / compare / sensitivity / play
│   └── strategies/*.json     rush, and the recommended order, with reasoning
└── log/playthrough_01.md     real traces: lucky, typical, and failed
```

## The one rule that keeps it coherent

**Every claim about cost, time or dependency lives in `data/`. Every claim about
how to physically do something lives in `knowledge/`. Prose files quote the data,
they never assert it.** Every number in `02_STRATEGY.md` and `04_ECONOMICS.md`
was computed by the simulator from the data files, so if you edit the tree, run
the commands again and the documents are wrong until you do.

## The link between the tree and the library

Every node in `tech_tree.json` carries a `kb` field pointing at a file and an
anchor, for example:

```json
"id": "zinc_metal",
"kb": "10_metallurgy.md#zinc_metal",
```

and `rome/knowledge/10_metallurgy.md` contains a `### zinc_metal` entry with the
actual procedure: ore, ratios, temperatures, vessel, condenser design, what
success looks like, how it fails, what it costs, and what it will do to your
lungs. **That link is the point of the whole project.** A tech tree that says
"microscope requires glass" is useless to someone who does not already know that
a single melted bead of glass gives 250x. The tree tells you *what* and *in what
order*; the library tells you *how*, at a level of detail a competent
non-specialist can actually act on.

## Node schema

Documented in full in `data/tech_tree.json` under `meta.schema`. The fields that
matter most:

| Field | Meaning |
|---|---|
| `ph` | **Your own hours.** The scarce resource. You have about 72,000, ever. |
| `lab` | Hired hours by trade, priced from `prices.json` |
| `yrs` | **Calendar floor.** Curing, growing, maturing, or a generation of economic diffusion. Money cannot buy this down, and this is what sets the 144-year critical path. |
| `risk` | Probability an attempt fails outright and must be retried at 40% of cost |
| `sus` | Suspicion delta. Rome executes magicians and your chemistry looks like magic. |
| `gov` | State interest, -3 (will suppress) to +3 (will fund and demand) |
| `sch` / `art` | Trained people required. This is what the greedy strategy runs out of. |
| `conf` | A well attested, B probable, C the author's estimate |

## Confidence, stated plainly

- **Dependency structure: strong.** It is checkable against the history of
  technology, and `validate` proves it is an acyclic, fully priced, reachable graph.
- **Calendar floors: reasonable.** Grounded in real historical durations.
- **Costs in denarii: weak.** Bulk Roman commodity prices are reconstructed from
  the Edict of Diocletian, which is 301 AD and denominated in a collapsed
  currency, so it is used for *ratios* anchored to silver. Every such figure is
  tagged `[C]`.
- **Revenue: weakest.** These are guesses at the profit of enterprises that did
  not exist, in a market reconstructed from secondary scholarship.
- **The social model: under-powered, and I know it.** See `02_STRATEGY.md` §5.

## Editing it

```bash
python3 sim/simulator.py validate    # run this after EVERY edit to data/
```

`validate` checks acyclicity, dangling prerequisites, unpriced materials,
unknown trades, out-of-range risks, and reachability of the goal. It has caught
every mistake I made while building this, which was several.
