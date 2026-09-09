# ROME 100 AD -> MODERN TECHNOLOGY

**A guide, a record, a game and a planning tool for someone sent back to the
Roman Empire under Trajan with the job of rebuilding modern technology as fast
as physically possible.**

The transistor is the *marker* the simulator aims at, because it is the deepest
single point in the tree and everything else is upstream of it. It is not the
subject. The subject is all 1,176 technologies, and the ones that matter most to
the people who would actually live there are chimneys, water traps, soap and
lamps.

Everything lives in [`rome/`](rome/). Start with
[`rome/00_BRIEFING.md`](rome/00_BRIEFING.md).

---

## Scale

**1,176 technologies, 2,156 dependency edges**, across fifteen domains from
spinning wheels to jet engines to public key cryptography. Every node is costed
in the founder's own hours, hired labour by trade, materials, capital, calendar
floor, failure risk, State interest and suspicion.

Three layers, because the point is to show WHY things are hard:

- **33 capability rungs**: furnace temperature 700 C to 3000 C, machining
  tolerance 1 mm to 0.1 micron, vacuum 1 torr to 1e-9, purity 99% to one part in
  a billion, power from muscle to grid, and eight kinds of measurement. A
  technology names the rung it needs and the tree proves you can reach it.
- **70 materials as nodes with their own prerequisites**, including **11 marked
  UNOBTAINABLE** (rubber, gutta percha, quinine, Chile saltpetre, cryolite, bulk
  platinum, potato, maize, chocolate, cocaine) so that the tree states the
  impossibility instead of quietly omitting it.
- **1,073 technologies.**

**The transistor needs 97 of them. The other 1,079 are the rest of technology**,
and that is deliberate: a tree that only covers the path to a transistor is
dishonest about what technology is for. Most human benefit is in module 91,
which is about chimneys, water traps and lamps.

## The answer, in seven lines

- The irreducible serial calendar time to a working transistor is **141 years**
  across 28 nodes, even with unlimited money, labour and life.
- With the founder immortal, which is the default, the median run reaches it in
  **275 AD**, about **175 years** after arrival, in **86%** of 200 runs.
- Turning mortality back on (`--mortal`) barely changes it: 90%, median 276 AD.
  The programme now survives its founder, which it could not in the first
  version. **The dominant failure mode has shifted from succession to politics:
  14% of immortal runs end with the founder denounced as a magician**, because an
  immortal who never stops producing marvels accumulates suspicion faster than
  any patron can absorb it.
- **Reputation is now a resource** distinct from money and protection. It
  shortens diffusion floors, attracts staff you did not pay for, and makes you
  harder to accuse. Median final reputation in a successful run: 74/100.
- Past about 50,000 denarii, **more starting gold makes you less likely to
  succeed**, because money buys speed, speed buys visibility, and visibility in
  Trajanic Italy is dangerous.
- Three things that will surprise you: **Roman *nitrum* is sodium carbonate, not
  saltpetre**; **zinc metal is the hidden gate on the entire electrical age**;
  and **a single glass bead is a 250x microscope you can build in a week**.
- The four highest-value nodes are still **write it down, print it, copy it, and
  make the paper**.

## How this is graded

**Not by the end date.** Each technology is judged on its own:
*could someone holding exactly this node's prerequisites, and nothing else,
actually build it?*

```bash
python3 rome/sim/treetool.py judge --id zinc_metal
```

gives a report card: grade, tier, direct prerequisites, full ancestry depth,
which capability rungs appear in its chain, cost, calendar floor, and every
defect by name. Across all 1,176 nodes the mean is 98/100 after repair, and
**you should discount that number**, because a large part of the rise from 80.8
is my own checker being satisfied by my own repair. Every prerequisite the
repair inferred is stamped into the node so you can find all 112 of them. The
trustworthy check is `rome/data/INDEPENDENT_AUDIT.md`, done by a separate
reviewer against a random sample of 70 nodes.

## What is here

| File | What it is |
|---|---|
| [`rome/00_BRIEFING.md`](rome/00_BRIEFING.md) | Your first thousand days. Read first. |
| [`rome/01_WORLD_STATE_100AD.md`](rome/01_WORLD_STATE_100AD.md) | What Rome has, what it lacks, where every material comes from, what everything costs. |
| [`rome/02_STRATEGY.md`](rome/02_STRATEGY.md) | The master plan, the six phases, and the simulator evidence that it beats the alternatives. |
| [`rome/03_SOCIAL_POLITICS.md`](rome/03_SOCIAL_POLITICS.md) | Patronage, the law, what the State will fund, what gets you executed. |
| [`rome/04_ECONOMICS.md`](rome/04_ECONOMICS.md) | Labour, materials, transport, and where the 15.4 million denarii goes. |
| [`rome/LABOR_LEDGER.md`](rome/LABOR_LEDGER.md) | Your personal hours, and the author's. |
| [`rome/knowledge/`](rome/knowledge/) | **The how-to library.** Eleven modules of actual recipes with masses, temperatures and failure modes, plus a generated index linking all 128 tree nodes to the entry that documents them. |
| [`rome/knowledge/00_NONOBVIOUS_TRICKS.md`](rome/knowledge/00_NONOBVIOUS_TRICKS.md) | **Start here in the library.** The 33 specific physical tricks that make everything else buildable. |
| [`rome/knowledge/99_AUDIT.md`](rome/knowledge/99_AUDIT.md) | An adversarial fact-check of the technical modules. It found real errors and they have been fixed. |
| [`rome/data/tech_tree.json`](rome/data/tech_tree.json) | **1,176 nodes, 2,156 edges**, fully costed in hours, denarii, materials, risk and political consequence. |
| [`rome/data/branches/`](rome/data/branches/) | Per-domain source files, plus the CONTRACT and VOCABULARY the branch authors worked to. |
| [`rome/sim/treetool.py`](rome/sim/treetool.py) | **Merge, repair, and JUDGE EACH TECHNOLOGY IN ISOLATION.** |
| [`rome/data/INDEPENDENT_AUDIT.md`](rome/data/INDEPENDENT_AUDIT.md) | A hostile reviewer's findings against a random sample of 70 nodes. |
| [`rome/data/prices.json`](rome/data/prices.json) | Roman wages and commodity prices, every figure confidence-tagged. |
| [`rome/sim/simulator.py`](rome/sim/simulator.py) | The tool. Validates, plans, Monte-Carlos, ablates, and plays. |
| [`rome/log/playthrough_01.md`](rome/log/playthrough_01.md) | Real simulator traces: the lucky run, the typical run, and a failure. |

## Run it

```bash
python3 rome/sim/simulator.py validate                       # DAG, prices, reachability
python3 rome/sim/simulator.py path point_contact_transistor   # the critical path, costed
python3 rome/sim/simulator.py why zinc_metal                  # explain any single node
python3 rome/sim/simulator.py costs --top 25                  # where the money goes
python3 rome/sim/simulator.py compare --mc 500                # rush vs topological vs recommended
python3 rome/sim/simulator.py sensitivity --mc 300            # what is each choice worth
python3 rome/sim/simulator.py sweep capital                   # how much gold should you bring
python3 rome/sim/simulator.py sweep lifespan                  # how long must you live
python3 rome/sim/simulator.py run --mortal                    # turn death back on
python3 rome/sim/treetool.py  judge                           # score all 1,176 nodes
python3 rome/sim/treetool.py  judge --id zinc_metal           # one report card
python3 rome/sim/treetool.py  merge                           # branches -> tree
python3 rome/sim/simulator.py run --strategy recommended --trace
python3 rome/sim/simulator.py play                            # play it year by year
python3 rome/sim/build_index.py                               # regenerate the library index
```

No dependencies beyond the Python 3 standard library.

## The premise

You speak Latin and Greek. You carry about 3 kg of unminted gold, roughly 10,300
denarii, which is comfortable and well short of the equestrian census of
100,000. You pass as a Greek physician and natural philosopher of Alexandria,
which is the cover that explains your accent, your apparatus, your chemistry and
your interest in bodies and minerals, and which is not a magician, a prophet or
a priest, those being the three identities that attract prosecution.

You know when the plagues come. Nobody else does. That is worth more than any
machine in this document.

## How much to trust it

Honestly: **trust the ordering and the failure modes; do not trust the absolute
years to better than a factor of about 1.5.**

The dependency structure is the strong part, and it is checkable. The cost model
is the weak part: bulk Roman commodity prices are reconstructed from the Edict
of Diocletian, which is 301 AD and denominated in a currency that had already
collapsed, so it is used for ratios only. Every such figure is tagged `[C]` in
the data. The social model is under-powered and I say so in
[`rome/02_STRATEGY.md`](rome/02_STRATEGY.md) section 5, along with four other
things the model gets wrong.

The simulator is also allowed to criticise its own author: the ablation study
reports that one of the revenue businesses in my recommended strategy costs more
founder-hours than it returns. I left the finding in rather than tuning it away.
