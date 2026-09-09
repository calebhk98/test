# 04 - Economics: labour, materials and what it all costs

All figures computed from `data/tech_tree.json` and `data/prices.json` by
`sim/simulator.py costs`. Regenerate them after any edit; do not trust a number
copied into prose over the number in the data file.

**Wage basis.** A 10-hour day and about 250 working days a year, so 2,500
worker-hours per person-year. Unskilled 2-4 sestertii a day, skilled artisan
4-8, master 8-16. One denarius = 4 sestertii.

**Confidence.** Wages are [B]. Bulk commodity prices are [C]: my estimates,
anchored to silver through ratios implied by the Edict of Diocletian, which is
301 AD and denominated in a collapsed currency, so I use it for ratios only.
**Replace every [C] price with an observed one in your first month.**

---

## 1. The whole programme, by category

| Category | Nodes | Your hours | Total cost (den) | Revenue at maturity (den/yr) |
|---|---:|---:|---:|---:|
| transport | 1 | 800 | 1,393,410 | 60,000 |
| electrical | 15 | 7,720 | 988,108 | 237,700 |
| metallurgy | 18 | 8,280 | 566,696 | 199,000 |
| chemistry | 16 | 8,900 | 484,925 | 97,900 |
| semiconductor | 10 | 8,250 | 443,949 | 70,000 |
| institution | 6 | 6,750 | 235,797 | 5,300 |
| power | 5 | 3,150 | 205,877 | 44,800 |
| social | 5 | 2,550 | 59,200 | 20,000 |
| glass_optics | 10 | 4,420 | 52,784 | 22,000 |
| precision | 7 | 4,500 | 51,790 | 18,000 |
| information | 6 | 9,050 | 50,207 | 7,400 |
| instruments | 7 | 3,700 | 44,406 | 7,000 |
| physics | 5 | 4,600 | 20,610 | 3,000 |
| mathematics | 6 | 2,800 | 11,780 | 900 |
| military | 2 | 700 | 10,724 | 6,000 |
| medicine | 3 | 1,350 | 9,060 | 4,000 |
| agriculture | 2 | 650 | 4,146 | 3,900 |
| foundation | 4 | 2,350 | 2,824 | 0 |
| **TOTAL** | **128** | **80,520** | **4,636,293** | **806,900** |

### The twelve most expensive nodes

| Node | Labour | Materials | Capital | TOTAL |
|---|---:|---:|---:|---:|
| `railway` | 13,410 | 1,290,000 | 90,000 | **1,393,410** |
| `power_grid` | 18,000 | 544,000 | 150,000 | **712,000** |
| `electrolysis_industrial` | 5,400 | 245,200 | 70,000 | **320,600** |
| `zinc_industry_scale` | 4,165 | 143,000 | 50,000 | **197,165** |
| `endowment_land` | 80 | 150,000 | 8,000 | **158,080** |
| `steam_high_pressure` | 5,670 | 89,000 | 26,000 | **120,670** |
| `silicon_path` | 10,050 | 31,045 | 60,000 | **101,095** |
| `telegraph_electric` | 3,795 | 52,000 | 35,000 | **90,795** |
| `bessemer_openhearth` | 4,165 | 42,800 | 40,000 | **86,965** |
| `arc_furnace_ferroalloys` | 2,680 | 15,300 | 60,000 | **77,980** |
| `zone_refining` | 7,500 | 28,500 | 35,000 | **71,000** |
| `charcoal_industrial` | 900 | 53,200 | 3,500 | **57,600** |

### Best return on capital: revenue per denarius of setup cost

| Node | Revenue/yr | Setup cost | Payback |
|---|---:|---:|---:|
| `glass_bead_microscope` | 700 | 306 | 0.4 yr |
| `sanitation_antisepsis` | 1,400 | 760 | 0.5 yr |
| `telescope` | 2,000 | 1,094 | 0.5 yr |
| `world_map` | 500 | 290 | 0.6 yr |
| `lens_grinding` | 3,200 | 1,891 | 0.6 yr |
| `camera_obscura` | 600 | 376 | 0.6 yr |
| `drawplate_wire` | 800 | 638 | 0.8 yr |
| `distillation_alcohol` | 4,200 | 3,458 | 0.8 yr |
| `radio` | 25,000 | 21,152 | 0.8 yr |
| `horse_collar` | 900 | 826 | 0.9 yr |
| `crucible_steel` | 11,000 | 11,388 | 1.0 yr |
| `finery_puddling` | 9,000 | 9,530 | 1.1 yr |

### Where your own hours go

| Node | Your hours | %% of a 72,000-hour life |
|---|---:|---:|
| `corpus_written` | 6,000 | 8.3% |
| `academy_network` | 2,500 | 3.5% |
| `school_founded` | 2,000 | 2.8% |
| `quantum_solidstate_theory` | 1,800 | 2.5% |
| `arrival_orientation` | 1,200 | 1.7% |
| `zone_refining` | 1,200 | 1.7% |
| `atomic_theory` | 1,000 | 1.4% |
| `single_crystal` | 1,000 | 1.4% |
| `silicon_path` | 1,000 | 1.4% |
| `freedman_staff` | 900 | 1.2% |
| `patron_imperial` | 900 | 1.2% |
| `printing_press` | 900 | 1.2% |

---

## 2. What these tables actually say

**Read the first table again.** `information` is the single largest consumer of
*your own hours* in the entire programme, 9,050 of them, and one of the smallest
consumers of *money*, about 50,207 denarii for the whole branch. Meanwhile
`transport` (the railway) costs 1,393,410 denarii and 800 of your hours.

That asymmetry is the whole strategic geometry of this problem:

- **Money buys things. It does not buy understanding.** The expensive branches
  are expensive in denarii and cheap in founder-hours, because once specified
  they can be handed to a competent freedman and a large workforce.
- **The cheap branches are the ones only you can do.** Writing the corpus,
  teaching mathematics, establishing the method. Nobody in the Empire can do
  those for you, at any price, until you have made someone who can.
- Therefore: **spend money freely and hours miserably.** The failure mode of
  every simulated run that dies is a founder who spent his hours on apparatus.

## 3. The total is unaffordable, and that is the point

The full tree costs about **4.6 million denarii**, which is roughly 19 senatorial
fortunes, and **80,520 of your hours** against the roughly 72,000 you will ever have.

Neither number is meant to be paid by you. They are paid by:

1. **Compounding revenue.** The programme's own products fund it. Note the
   revenue column totals about 806,900 denarii a year at full maturity, which
   pays back the entire capital cost in about 6 years, if you live long
   enough to get there, which you do not.
2. **The State.** Once the optical telegraph exists, imperial funding is worth
   more than every product you sell.
3. **Economic growth.** This is the term most bootstrap plans forget.
   Industrialisation pays for itself: each diffused technology raises output
   across the whole Empire, and a share comes back to you as demand, taxes and
   patronage. In the simulator, removing this term makes the industrial
   revolution mathematically unaffordable, which is false, and the reason it is
   false is that the revolution funds itself.

## 4. Transport dominates everything, so build on water

The single most important economic fact in the Empire, and the one most likely
to wreck a plan drawn on a map: **sea freight costs roughly one-fortieth to
one-sixtieth of land freight per tonne-kilometre.** Moving grain 500 km overland
roughly doubles its price.

Consequences, all of them binding:
- A blast furnace consumes about 180 tonnes of charcoal per campaign in this
  model. Charcoal is bulky and worth about 0.03 denarii a kilogramme. Hauling it
  40 km overland can cost more than the fuel.
- **Every facility goes on navigable water.** Ostia, Puteoli, the Rhône, the
  Rhine, the Guadalquivir, the Nile. A workshop sited for convenience rather
  than for water is a workshop that will strangle on its own supply chain.
- Ore, flux, fuel and finished metal should ideally never touch a road.

## 5. Charcoal is the real ceiling on iron, not ore

Pre-coke ironmaking is limited by forest, not by mines, and it deforests
regions. The charcoal node in the tree carries 200 *iugera* of dedicated
coppice land for exactly this reason. Coppice rotation is 15 to 20 years, so the
land must be acquired long before the furnace is lit. Coking coal breaks the
ceiling permanently and is the reason `coal_coke` sits where it does in the
recommended order.

## 6. Two honest warnings about these numbers

**The revenue figures are the weakest thing in this project.** They are
estimates of net profit from enterprises that do not exist in a market I have
reconstructed from secondary scholarship. The ablation study found that removing
the amalgam mirror business *improves* the outcome, which I think is an artefact
of exactly this weakness rather than a real result.

**Slavery is modelled far too thinly.** Roman labour is cheap partly because
much of it is coerced, which suppressed the business case for every
labour-saving device in this document. The model treats labour as a market with
a manumission option. That understates the problem, and the honest version of
the answer is in `03_SOCIAL_POLITICS.md` section 7: compete where headcount
cannot substitute, which is precision, chemistry and optics.

## 7. Bounties: buying other people's hours with money

The third way to get something built, alongside doing it yourself and hiring
labour by the hour, is to **post a public prize**.

> *Decem milia sestertium ei vitrario qui primus mihi attulerit sphaerulam
> vitream puram, milii grano parem.*
> Ten thousand sesterces to the first glassworker who brings me a clear sphere of
> glass the size of a millet grain.

This is a genuinely different economic instrument and it is the one that best
fits your actual constraint. Hiring labour by the hour still costs you the hours
of **specifying and supervising** the work. A prize costs you only the hours of
**writing the notice**. You are converting denarii, which you can regenerate,
into somebody else's attention, which you cannot.

**Terms modelled in the simulator** (`bounties` in a strategy file):

| | |
|---|---|
| Price | about **2.5x** the honest cost of the work |
| Your hours saved | **65%** |
| Supervision slots consumed | **none**, which is the real advantage |
| Side effect | +2 suspicion. A public prize makes you conspicuous. |

**Where a bounty works, and where it cannot.** The craft must already exist in
the Empire, and the artisan must be able to **recognise success without
understanding why it works**. A glassworker can tell a clear bead from a cloudy
one. A smith can tell whether a plate is flat by the marking. Neither needs your
theory. That is why the eligible set in the model is limited to tier 0 to 2
nodes in glass, metallurgy, precision, power, agriculture, instruments and
information.

You cannot post a bounty for zone refining. Nobody in the Empire would know what
to aim at, or how to tell if they had hit it. Past about tier 3, the only people
who can recognise success are people you trained, and at that point you are back
to paying wages.

**Measured effect**, 400 runs each: bounties move the median from 391 AD to
**385 AD** and lift the success rate from 78% to 80%. Real but modest. They help
most in the first thirty years, when your hours are the binding constraint and
the cash premium is affordable relative to what an unmade lens is costing you in
delay.
