# ROME 100 AD → THE TRANSISTOR

**A guide, a record, a game and a planning tool for someone sent back to the
Roman Empire under Trajan with the job of getting to solid-state electronics as
fast as physically possible.**

Everything lives in [`rome/`](rome/). Start with
[`rome/00_BRIEFING.md`](rome/00_BRIEFING.md).

---

## The answer, in seven lines

- The irreducible serial calendar time to a working transistor is **133 years**,
  across 23 nodes, even with unlimited money and labour.
- Across 600 simulated runs of the best strategy I could write, the median is
  **386 AD**, about **286 years** after arrival, with **77%** of runs succeeding
  within five centuries.
- **You will not see it.** You will die around 128 AD having personally directed
  about **44%** of the tree.
- The naive strategy, beelining at the goal, **succeeds in 0 of 600 runs.** It
  does not fail at the transistor. It fails at basic atomic chemistry, because
  it never trained a second person who understood anything.
- **The technical dependency graph is not the real dependency graph.** Nothing
  in the chain from zinc ore to a germanium crystal requires you to be a Roman
  citizen, to have a patron, or to have taught anybody. Remove those and the
  success rate goes to zero.
- The four highest-value *technical* nodes in the tree are **write it down,
  print it, copy it, and make the paper**. Removing them costs 83, 47, 40 and 42
  years. No furnace or engine comes close.
- Three things that will surprise you: **Roman *nitrum* is sodium carbonate, not
  saltpetre**; **zinc metal is the hidden gate on the entire electrical age**;
  and **a single glass bead is a 250x microscope you can build in a week**.

## What is here

| File | What it is |
|---|---|
| [`rome/00_BRIEFING.md`](rome/00_BRIEFING.md) | Your first thousand days. Read first. |
| [`rome/01_WORLD_STATE_100AD.md`](rome/01_WORLD_STATE_100AD.md) | What Rome has, what it lacks, where every material comes from, what everything costs. |
| [`rome/02_STRATEGY.md`](rome/02_STRATEGY.md) | The master plan, the six phases, and the simulator evidence that it beats the alternatives. |
| [`rome/03_SOCIAL_POLITICS.md`](rome/03_SOCIAL_POLITICS.md) | Patronage, the law, what the State will fund, what gets you executed. |
| [`rome/04_ECONOMICS.md`](rome/04_ECONOMICS.md) | Labour, materials, transport, and where the 5.1 million denarii goes. |
| [`rome/LABOR_LEDGER.md`](rome/LABOR_LEDGER.md) | Your personal hours, and the author's. |
| [`rome/knowledge/`](rome/knowledge/) | **The how-to library.** Eleven modules of actual recipes with masses, temperatures and failure modes. |
| [`rome/knowledge/00_NONOBVIOUS_TRICKS.md`](rome/knowledge/00_NONOBVIOUS_TRICKS.md) | **Start here in the library.** The 33 specific physical tricks that make everything else buildable. |
| [`rome/knowledge/99_AUDIT.md`](rome/knowledge/99_AUDIT.md) | An adversarial fact-check of the technical modules. It found real errors and they have been fixed. |
| [`rome/data/tech_tree.json`](rome/data/tech_tree.json) | 128 nodes, 254 dependency edges, fully costed in hours, denarii, materials, risk and political consequence. |
| [`rome/data/prices.json`](rome/data/prices.json) | Roman wages and commodity prices, every figure confidence-tagged. |
| [`rome/sim/simulator.py`](rome/sim/simulator.py) | The tool. Validates, plans, Monte-Carlos, ablates, and plays. |
| [`rome/log/playthrough_01.md`](rome/log/playthrough_01.md) | Real simulator traces: the lucky run, the typical run, and a failure. |

## Run it

```bash
python3 rome/sim/simulator.py validate                      # DAG, prices, reachability
python3 rome/sim/simulator.py path point_contact_transistor  # the critical path, costed
python3 rome/sim/simulator.py costs --top 25                 # where the money goes
python3 rome/sim/simulator.py compare --mc 500               # rush vs topological vs recommended
python3 rome/sim/simulator.py sensitivity --mc 300           # what is each choice actually worth
python3 rome/sim/simulator.py why zinc_metal                  # explain any one node
python3 rome/sim/simulator.py run --strategy recommended --trace
python3 rome/sim/simulator.py play                           # play it year by year
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
