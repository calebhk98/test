# Civilization schema

The tech tree says **X requires Y**. It never says "tech level 4", and it never
says "Rome". Everything specific to a place and a century lives here, in one
file per civilization, so that swapping Rome for Han China, Viking Norway,
Mexica Tenochtitlan, Plantagenet England or somewhere invented is a matter of
pointing the simulator at a different file.

That is also why the tree has no linear tech levels. **A civilization can have
aeroplanes and no gunpowder, or electricity and no steam, or steam and no
electricity, or cities built on rafts because the land will not farm.** The only
thing that constrains it is the prerequisite graph.

```
python3 rome/sim/simulator.py run --civ rome_100ad
python3 rome/sim/simulator.py run --civ han_china_100ad
python3 rome/sim/simulator.py civs            # list what is available
```

## Fields

| field | meaning |
|---|---|
| `id`, `name`, `year`, `blurb` | identity |
| `population`, `urban_fraction`, `literacy_elite`, `literacy_general` | demography |
| `currency`, `price_index`, `wage_index` | economy scaling. 1.0 is Rome 100 AD, which is the calibration baseline for `prices.json`. |
| `state_capacity` | 0 to 1. Can the state fund and compel a large project? Rome 0.85, Norse 0.15. |
| `starting_techs` | node ids the civilization ALREADY HAS. This replaces the hardcoded "tier 0 means Rome has it". A different civ has a different free list. |
| `home_regions` | which geography regions it controls or trades in cheaply |
| `base_reach` | how far its ships and caravans already go, on the geography reach scale |
| `institutions` | which legal vehicles exist: partnership, corporation, guild, testament, charter, bank, patent |
| `values` | the REACTION MODEL. See below. |
| `hazards` | dated shocks: plagues, invasions, dynastic collapse, with year ranges. A `staff_loss` hazard now also costs the whole society population (`Sim.pop_deficit`, core.py), which raises `wage_index` until it recovers - see `_demographic_recovery` in core.py. Keep each civilization's list spread across its whole playable span (roughly every 50-90 years, start to start+700): a list that goes quiet for centuries reads as the game having stopped, not as a peaceful age. |
| `cost_multipliers` | what this society finds harder or easier than Rome, by node category and trait. Above 1 is dearer here. |
| `handicap_remedies` | per `cost_multipliers` key: `{"node": ..., "residual": ...}`. Building that node drops the multiplier to `residual`. |
| `needs_first` | HARD gates, as against the soft ones above: `{"<label>": {"node": ..., "because": ..., "ids": [...]}}`. Those ids cannot be STARTED at all until `node` is done, and the refusal quotes `because`. For what is not dear here but impossible - the Mexica had no draught animal of any kind, so a horse collar is not a 1.3x agriculture cost, it is nothing you can build. Always liftable by the node it names. |
| `notes` | what a newcomer must know |

## The values vector, and why it replaces `gov` and `sus`

The old model gave each technology a single number for "the State likes it" and
a single number for "this looks like sorcery". Both are properties of the
SOCIETY, not of the technology. A printing press is subversive in a society that
controls information through a scribal elite and unremarkable in one that does
not. Gunpowder is a gift to a centralised empire and a threat to a fragmented
one.

So a technology now carries **traits**, and a civilization carries **weights**,
and the reaction is the dot product.

| trait on a technology | meaning |
|---|---|
| `military` | improves war-making |
| `labour_saving` | displaces workers |
| `information` | moves, copies or stores knowledge |
| `spectacle` | visibly astonishing |
| `inexplicable` | produces an effect with no visible cause |
| `medical` | heals |
| `food` | feeds |
| `infrastructure` | roads, water, harbours, power |
| `luxury` | status goods for the rich |
| `commerce` | trade, finance, records |
| `religious_adjacent` | touches burial, the body, the heavens, or omens |
| `weapon_democratising` | arms individuals rather than states |
| `status_threatening` | undermines an existing elite's monopoly |

| weight on a civilization | meaning |
|---|---|
| `w_military` | how much the state rewards military value |
| `w_labour_saving` | NEGATIVE where cheap coerced labour makes machines unwelcome |
| `w_information` | negative where an elite controls literacy |
| `w_novelty` | tolerance for the new as such |
| `w_magic_fear` | how dangerous it is to produce an inexplicable effect |
| `w_religious_rigidity` | how much doctrine constrains inquiry |
| `w_commerce` | how much merchants are respected and protected |
| `bribability` | how far money buys a legal outcome. THIS IS A PROTECTION, and the old model had nothing like it. |
| `patronage_weight` | how much a powerful protector matters |
| `adaptation_rate` | how fast the astonishing becomes ordinary. People habituate. The iPhone was astounding in 2007 and boring by 2012. |
