# LABOUR LEDGER

Two ledgers, because two different people did work on this project.

---

# PART 1 - The founder's personal hours (in the game)

Your own hours are the binding constraint of the whole enterprise. Money is
recoverable; a year of your attention is not. This ledger is computed from 300
simulated lifetimes under the recommended strategy.

**Budget:** about 2,400 useful hours a year. Roman elite males who reached 35
could expect roughly another 25 to 30 years, so call it 30 years and 72,000
hours, total, forever.

| | |
|---|---|
| Median years the founder survives after arrival | **29** |
| 10th / 90th percentile | 18 / 39 years |
| Median founder-hours actually delivered in a lifetime | **39,132** |
| Founder-hours the full tree demands | 215,600 |
| Those hours as a share of the tree's total founder-hour demand | **18%** |

### What the founder personally lives to see finished

Share of 300 runs in which this node was complete before the founder died.

| Node | Completed before death | Tier |
|---|---:|---:|
| `workshop_first` | 100% | 1 |
| `patron_local` | 100% | 0 |
| `world_map` | 100% | 0 |
| `arithmetic_positional` | 100% | 0 |
| `units_standards` | 100% | 0 |
| `identity_cover` | 100% | 0 |
| `horse_collar` | 100% | 1 |
| `arrival_orientation` | 100% | 0 |
| `citizenship` | 100% | 0 |
| `scientific_method` | 99% | 0 |
| `nitre_beds` | 99% | 2 |
| `lens_grinding` | 97% | 1 |
| `glass_bead_microscope` | 97% | 1 |
| `case_hardening` | 97% | 1 |
| `soap_hard` | 97% | 1 |
| `drawplate_wire` | 97% | 1 |
| `crank_conrod` | 96% | 1 |
| `potash_soda` | 96% | 1 |
| `refractory_fireclay` | 95% | 2 |
| `camera_obscura` | 95% | 1 |
| `glass_clear` | 92% | 1 |
| `freedman_staff` | 92% | 1 |
| `collegium_licensed` | 88% | 1 |
| `glass_labware` | 88% | 2 |
| `water_power_scale` | 87% | 1 |
| `mirror_amalgam` | 84% | 1 |
| `distillation_alcohol` | 83% | 1 |
| `lead_metallurgy` | 71% | 1 |
| `school_founded` | 71% | 1 |
| `algebra_symbolic` | 69% | 0 |
| `crude_cell` | 67% | 1 |
| `charcoal_industrial` | 57% | 2 |
| `corpus_written` | 54% | 1 |
| `germ_theory` | 53% | 0 |

Nodes reached in fewer than half of runs before the founder dies, and therefore
things you should assume you will NOT live to see:

`cementation_steel`, `precision_three_plate`, `telescope`, `bellows_water_blown`, `blast_furnace`, `statistics_basic`, `geometry_analytic`, `lab_apparatus`, `sulfuric_retort`, `mercury_supply`, `nitric_acid`, `hydrochloric_acid`, `barometer`, `thermometer`, `master_screw`, `balance_analytical`, `atomic_theory`, `calculus`, `finery_puddling`, `coal_coke`, `crucible_steel`, `copper_fire_refined`, `zinc_metal`, `newtonian_mechanics`, `em_theory`, `screw_lathe`, `micrometer_gauges`, `lead_chamber`, `voltaic_pile`, `copper_refining` ...

## The single most important number in this project

**18%.** Your entire working life delivers under a fifth of the founder-hours
the tree demands. And that is the flattering way to put it, because those hours are
spread across retries and abandoned attempts, not neatly banked against finished
nodes. You are not the builder of a transistor. You are the first link in a
relay of many generations of directors, and the only things you
can hand forward are trained people and written words.

Which is why the corpus is 6,000 hours, about 17% of everything you will ever
deliver, and why the ablation study says cutting it costs 90 years.

## The allocation rule, restated as arithmetic

For any task, ask: **can a hired Roman do it if I specify it?**

| | Founder-hours | Hired-hours | Do it yourself? |
|---|---|---|---|
| Grinding a lens | 1 | 1 | No. Specify it once, hire it forever. |
| Running a furnace campaign | 1 | 1 | No. |
| Teaching a student calculus | 1 | 0 | **Yes. Nobody else can.** |
| Writing the corpus | 1 | 0.5 (a scribe copies) | **Yes.** |
| Deciding what to build next | 1 | 0 | **Yes.** |
| Debugging a process that has never worked | 1 | 0.3 | Yes, at first, then hand it over. |

Every simulated run that fails is a founder who got this wrong.

---

# PART 2 - The author's hours (building this guide)

Recorded because the exercise asked for it and because a tool should say how it
was made.

## Division of labour

| Work | Done by | Notes |
|---|---|---|
| Branch setup, repository structure | author | |
| `01_WORLD_STATE_100AD.md` | author | The gap list and the material sourcing table are the load-bearing content. |
| `03_SOCIAL_POLITICS.md` | author | |
| `knowledge/00_NONOBVIOUS_TRICKS.md` | author | The flagship file. |
| `knowledge/_TEMPLATE.md` | author | Including the anachronism trap list given to every agent. |
| `data/tech_tree.json` core spine (128 nodes) | author | Written by hand. |
| `data/branches/` 15 domain files (1,048 nodes) | 15 Haiku subagents in parallel | Written to a strict CONTRACT and a fixed VOCABULARY of allowed prerequisite ids, then merged, validated and repaired by the author's tooling. |
| `data/branches/00_capabilities.json`, `01_materials.json` | author | The capability rungs and material layer, which are the load-bearing correction to the first version. |
| `sim/treetool.py` (merge, repair, judge) | author | The per-technology audit. |
| `data/prices.json` | author | |
| `sim/simulator.py` | author | |
| `sim/strategies/*.json` | author | |
| `00_BRIEFING.md`, `02_STRATEGY.md`, `04_ECONOMICS.md` | author | Numbers computed from the data files, not asserted. |
| `log/playthrough_01.md` | generated | Real simulator output, not a story. |
| `knowledge/10` through `knowledge/85` | 10 Sonnet subagents, 5 at a time | Each given the template, an explicit list of TECH_IDs matching the tree, and the anachronism trap list. |

## Why the split fell that way

The subagents got the *breadth* work: ten deep technical modules, each 4,000 to
10,000 words, which is simply a lot of typing. The author kept everything where
a single wrong number propagates: the tech tree, the price model, the simulator,
and the strategy conclusions drawn from them. A hallucinated detail inside a
metallurgy recipe is a bug in one paragraph. A wrong prerequisite edge in
`tech_tree.json` silently corrupts every result the simulator produces.

That is the same allocation rule as Part 1, applied to this document: delegate
what can be specified, keep what cannot.

## Verification actually performed

- `simulator.py validate` on every edit: DAG acyclicity, no dangling
  prerequisites, every material priced, every trade waged.
- Deliberate traps planted in the agent brief (Roman *nitrum* is not saltpetre;
  no cast iron in the Roman West; no rubber; no New World crops) and then
  grepped for in the returned files. All four held. One agent independently
  caught and corrected two anachronisms it had introduced itself, in a draft the
  author had not seen.
- Every headline number in `02_STRATEGY.md` and `04_ECONOMICS.md` recomputed
  from the data files rather than quoted from memory.

## Known unverified

- The Larderello boric acid claim is geologically sound and its Roman-era
  exploitation is unattested. Marked [C] and flagged in three places.
- Bulk metal prices are anchored to a 301 AD document. Marked [C] throughout.
- The subagent modules were checked for the planted traps and for internal
  format compliance. They were **not** line-by-line fact-checked. Treat any
  single number inside a knowledge module as [C] unless it carries its own
  MEASURED tag.
