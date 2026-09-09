# knowledge/ - the how-to library

**This file is generated. Do not edit it.** Run `python3 rome/sim/build_index.py`.

A tech tree that says *microscope requires glass* is useless to someone who does
not already know that one melted bead of glass gives 250x. The tree in
`../data/tech_tree.json` says WHAT and IN WHAT ORDER. These modules say HOW, at a
level of detail a competent non-specialist can act on: masses, ratios,
temperatures with Roman-observable proxies, vessel materials, how to tell it
worked, how it fails, what it costs, and what it will do to you.

## Start here

**[`00_NONOBVIOUS_TRICKS.md`](00_NONOBVIOUS_TRICKS.md)** is the index of specific
physical tricks: the glass-bead microscope, the three-plate method, downward zinc
distillation, the Sprengel pump, zone refining, and the rest. If you read one file
in this directory, read that one.

## Modules

| Module | Subject | Entries | Tree nodes it documents |
|---|---|---:|---:|
| [`00_NONOBVIOUS_TRICKS.md`](00_NONOBVIOUS_TRICKS.md) | The tricks that make everything else buildable. READ FIRST. | 0 | 0 |
| [`10_metallurgy.md`](10_metallurgy.md) | Metallurgy, fuel and refractories | 19 | 17 |
| [`20_chemistry.md`](20_chemistry.md) | Chemistry, acids, alkalis and energetics | 16 | 15 |
| [`30_glass_optics.md`](30_glass_optics.md) | Glass, optics and scientific instruments | 17 | 15 |
| [`40_power_precision.md`](40_power_precision.md) | Prime movers, machine tools and precision | 21 | 13 |
| [`70_medicine_biology.md`](70_medicine_biology.md) | Medicine, public health and biology | 13 | 3 |
| [`75_agriculture_food.md`](75_agriculture_food.md) | Agriculture, food and surplus | 12 | 2 |

### Nodes documented in the top-level prose files

These are institutional, political and economic nodes. Their 'how to' is a
strategy, not a procedure, so it lives outside the recipe library.

| Node | Tier | Your hours | Documented in |
|---|---:|---:|---|
| `arrival_orientation` | 0 | 1,200 | [`00_BRIEFING.md`](../00_BRIEFING.md) |
| `citizenship` | 0 | 250 | [`03_SOCIAL_POLITICS.md`](../03_SOCIAL_POLITICS.md) |
| `identity_cover` | 0 | 500 | [`03_SOCIAL_POLITICS.md`](../03_SOCIAL_POLITICS.md) |
| `patron_local` | 0 | 400 | [`03_SOCIAL_POLITICS.md`](../03_SOCIAL_POLITICS.md) |
| `collegium_licensed` | 1 | 350 | [`03_SOCIAL_POLITICS.md`](../03_SOCIAL_POLITICS.md) |
| `freedman_staff` | 1 | 900 | [`03_SOCIAL_POLITICS.md`](../03_SOCIAL_POLITICS.md) |
| `patron_senatorial` | 1 | 600 | [`03_SOCIAL_POLITICS.md`](../03_SOCIAL_POLITICS.md) |
| `school_founded` | 1 | 2,000 | [`03_SOCIAL_POLITICS.md`](../03_SOCIAL_POLITICS.md) |
| `workshop_first` | 1 | 500 | [`00_BRIEFING.md`](../00_BRIEFING.md) |
| `endowment_land` | 2 | 500 | [`03_SOCIAL_POLITICS.md`](../03_SOCIAL_POLITICS.md) |
| `mining_concession` | 2 | 400 | [`01_WORLD_STATE_100AD.md`](../01_WORLD_STATE_100AD.md) |
| `patron_imperial` | 2 | 900 | [`03_SOCIAL_POLITICS.md`](../03_SOCIAL_POLITICS.md) |
| `academy_network` | 3 | 2,500 | [`03_SOCIAL_POLITICS.md`](../03_SOCIAL_POLITICS.md) |

## Every tech-tree node, and where its recipe lives

Sorted by module, then by tier. `tier 0` is knowledge you carry in your head;
`tier 5` is the semiconductor endgame.

### 10_metallurgy.md

| Node | Tier | Your hours | Recipe |
|---|---:|---:|---|
| `case_hardening` | 1 | 300 | [`case_hardening`](10_metallurgy.md#case-hardening) |
| `drawplate_wire` | 1 | 180 | [`wire_drawing`](10_metallurgy.md#wire-drawing) |
| `lead_metallurgy` | 1 | 200 | [`lead_silver_cupellation`](10_metallurgy.md#lead-silver-cupellation) |
| `bellows_water_blown` | 2 | 300 | [`bellows_water_blown`](10_metallurgy.md#bellows-water-blown) |
| `blast_furnace` | 2 | 900 | [`blast_furnace_cast_iron`](10_metallurgy.md#blast-furnace-cast-iron) |
| `cementation_steel` | 2 | 400 | [`cementation_steel`](10_metallurgy.md#cementation-steel) |
| `charcoal_industrial` | 2 | 250 | [`charcoal_industrial`](10_metallurgy.md#charcoal-industrial) |
| `coal_coke` | 2 | 350 | [`coal_and_coke`](10_metallurgy.md#coal-and-coke) |
| `copper_fire_refined` | 2 | 200 | [`copper_refining`](10_metallurgy.md#copper-refining) |
| `crucible_steel` | 2 | 600 | [`crucible_steel`](10_metallurgy.md#crucible-steel) |
| `finery_puddling` | 2 | 500 | [`finery_forge`](10_metallurgy.md#finery-forge) |
| `mercury_supply` | 2 | 150 | [`mercury`](10_metallurgy.md#mercury) |
| `refractory_fireclay` | 2 | 350 | [`refractory_fireclay`](10_metallurgy.md#refractory-fireclay) |
| `zinc_metal` | 2 | 700 | [`zinc_metal`](10_metallurgy.md#zinc-metal) |
| `high_temp_furnace` | 3 | 800 | [`high_temp_furnace`](10_metallurgy.md#high-temp-furnace) |
| `bessemer_openhearth` | 4 | 900 | [`alloy_steels_ferroalloys`](10_metallurgy.md#alloy-steels-ferroalloys) |
| `arc_furnace_ferroalloys` | 5 | 600 | [`alloy_steels_ferroalloys`](10_metallurgy.md#alloy-steels-ferroalloys) |

### 20_chemistry.md

| Node | Tier | Your hours | Recipe |
|---|---:|---:|---|
| `distillation_alcohol` | 1 | 450 | [`distillation_fractional`](20_chemistry.md#distillation-fractional) |
| `potash_soda` | 1 | 200 | [`potash_and_soda`](20_chemistry.md#potash-and-soda) |
| `soap_hard` | 1 | 250 | [`potash_and_soda`](20_chemistry.md#potash-and-soda) |
| `gunpowder` | 2 | 300 | [`gunpowder`](20_chemistry.md#gunpowder) |
| `lab_apparatus` | 2 | 600 | [`lab_apparatus`](20_chemistry.md#lab-apparatus) |
| `nitre_beds` | 2 | 350 | [`saltpetre_nitre_beds`](20_chemistry.md#saltpetre-nitre-beds) |
| `sulfuric_retort` | 2 | 800 | [`sulfuric_acid_retort`](20_chemistry.md#sulfuric-acid-retort) |
| `analytical_chemistry` | 3 | 900 | [`analytical_chemistry`](20_chemistry.md#analytical-chemistry) |
| `destructive_distillation` | 3 | 600 | [`destructive_distillation`](20_chemistry.md#destructive-distillation) |
| `hydrochloric_acid` | 3 | 300 | [`hydrochloric_acid`](20_chemistry.md#hydrochloric-acid) |
| `industrial_gases` | 3 | 450 | [`industrial_gases`](20_chemistry.md#industrial-gases) |
| `lead_chamber` | 3 | 900 | [`lead_chamber`](20_chemistry.md#lead-chamber) |
| `nitric_acid` | 3 | 400 | [`nitric_acid`](20_chemistry.md#nitric-acid) |
| `soda_leblanc` | 3 | 600 | [`potash_and_soda`](20_chemistry.md#potash-and-soda) |
| `hydrofluoric_acid` | 4 | 400 | [`hydrofluoric_acid`](20_chemistry.md#hydrofluoric-acid) |

### 30_glass_optics.md

| Node | Tier | Your hours | Recipe |
|---|---:|---:|---|
| `camera_obscura` | 1 | 120 | [`camera_obscura_photography`](30_glass_optics.md#camera-obscura-photography) |
| `glass_bead_microscope` | 1 | 300 | [`glass_bead_microscope`](30_glass_optics.md#glass-bead-microscope) |
| `glass_clear` | 1 | 400 | [`glass_clear_cristallo`](30_glass_optics.md#glass-clear-cristallo) |
| `lens_grinding` | 1 | 600 | [`lens_grinding`](30_glass_optics.md#lens-grinding) |
| `mirror_amalgam` | 1 | 350 | [`mirrors_amalgam`](30_glass_optics.md#mirrors-amalgam) |
| `balance_analytical` | 2 | 700 | [`balance_analytical`](30_glass_optics.md#balance-analytical) |
| `barometer` | 2 | 200 | [`thermometer`](30_glass_optics.md#thermometer) |
| `glass_labware` | 2 | 500 | [`glass_lab_ware`](30_glass_optics.md#glass-lab-ware) |
| `telescope` | 2 | 350 | [`telescope`](30_glass_optics.md#telescope) |
| `thermometer` | 2 | 400 | [`thermometer`](30_glass_optics.md#thermometer) |
| `glass_borosilicate` | 3 | 500 | [`glass_borosilicate`](30_glass_optics.md#glass-borosilicate) |
| `microscope_compound` | 3 | 600 | [`microscope_compound`](30_glass_optics.md#microscope-compound) |
| `photography` | 3 | 800 | [`camera_obscura_photography`](30_glass_optics.md#camera-obscura-photography) |
| `spectroscope` | 3 | 500 | [`spectroscope`](30_glass_optics.md#spectroscope) |
| `fused_quartz` | 4 | 700 | [`fused_quartz`](30_glass_optics.md#fused-quartz) |

### 40_power_precision.md

| Node | Tier | Your hours | Recipe |
|---|---:|---:|---|
| `units_standards` | 0 | 300 | [`micrometer_gauge_blocks`](40_power_precision.md#micrometer-gauge-blocks) |
| `crank_conrod` | 1 | 300 | [`crank_connecting_rod`](40_power_precision.md#crank-connecting-rod) |
| `water_power_scale` | 1 | 450 | [`water_power_scaleup`](40_power_precision.md#water-power-scaleup) |
| `clock_pendulum` | 2 | 500 | [`clockwork_escapement`](40_power_precision.md#clockwork-escapement) |
| `master_screw` | 2 | 700 | [`screw_cutting_lathe`](40_power_precision.md#screw-cutting-lathe) |
| `precision_three_plate` | 2 | 500 | [`precision_three_plate`](40_power_precision.md#precision-three-plate) |
| `boring_mill` | 3 | 600 | [`boring_mill`](40_power_precision.md#boring-mill) |
| `interchangeable_parts` | 3 | 800 | [`interchangeable_parts`](40_power_precision.md#interchangeable-parts) |
| `micrometer_gauges` | 3 | 500 | [`micrometer_gauge_blocks`](40_power_precision.md#micrometer-gauge-blocks) |
| `screw_lathe` | 3 | 900 | [`screw_cutting_lathe`](40_power_precision.md#screw-cutting-lathe) |
| `steam_atmospheric` | 3 | 900 | [`steam_atmospheric`](40_power_precision.md#steam-atmospheric) |
| `steam_high_pressure` | 4 | 700 | [`steam_high_pressure`](40_power_precision.md#steam-high-pressure) |
| `steam_watt` | 4 | 800 | [`steam_watt`](40_power_precision.md#steam-watt) |

### 70_medicine_biology.md

| Node | Tier | Your hours | Recipe |
|---|---:|---:|---|
| `germ_theory` | 0 | 350 | [`germ_theory`](70_medicine_biology.md#germ-theory) |
| `sanitation_antisepsis` | 1 | 300 | [`sanitation_antisepsis`](70_medicine_biology.md#sanitation-antisepsis) |
| `plague_preparedness` | 2 | 700 | [`quarantine_publichealth`](70_medicine_biology.md#quarantine-publichealth) |

### 75_agriculture_food.md

| Node | Tier | Your hours | Recipe |
|---|---:|---:|---|
| `crop_rotation` | 1 | 450 | [`crop_rotation`](75_agriculture_food.md#crop-rotation) |
| `horse_collar` | 1 | 200 | [`horse_collar_harness`](75_agriculture_food.md#horse-collar-harness) |

## Broken links

- `world_map` points at `60_mathematics_method.md`, which does not exist
- `arithmetic_positional` points at `60_mathematics_method.md`, which does not exist
- `algebra_symbolic` points at `60_mathematics_method.md`, which does not exist
- `geometry_analytic` points at `60_mathematics_method.md`, which does not exist
- `logarithms` points at `60_mathematics_method.md`, which does not exist
- `calculus` points at `60_mathematics_method.md`, which does not exist
- `scientific_method` points at `60_mathematics_method.md`, which does not exist
- `statistics_basic` points at `60_mathematics_method.md`, which does not exist
- `newtonian_mechanics` points at `60_mathematics_method.md`, which does not exist
- `thermodynamics_theory` points at `60_mathematics_method.md`, which does not exist
- `atomic_theory` points at `60_mathematics_method.md`, which does not exist
- `em_theory` points at `50_electricity_semiconductors.md`, which does not exist
- `quantum_solidstate_theory` points at `50_electricity_semiconductors.md#semiconductor_theory`, which does not exist
- `rag_paper` points at `80_information_printing.md`, which does not exist
- `printing_press` points at `80_information_printing.md`, which does not exist
- `corpus_written` points at `80_information_printing.md`, which does not exist
- `corpus_dispersed` points at `80_information_printing.md`, which does not exist
- `semaphore_telegraph` points at `80_information_printing.md`, which does not exist
- `hot_air_balloon` points at `85_transport_civil.md`, which does not exist
- `railway` points at `85_transport_civil.md`, which does not exist
- `electrostatics` points at `50_electricity_semiconductors.md#electrostatics`, which does not exist
- `voltaic_pile` points at `50_electricity_semiconductors.md#voltaic_pile`, which does not exist
- `daniell_cell` points at `50_electricity_semiconductors.md#daniell_cell`, which does not exist
- `copper_refining` points at `50_electricity_semiconductors.md#wire_insulation`, which does not exist
- `galvanometer` points at `50_electricity_semiconductors.md#galvanometer`, which does not exist
- `electromagnet` points at `50_electricity_semiconductors.md#electromagnet`, which does not exist
- `telegraph_electric` points at `50_electricity_semiconductors.md#telegraph`, which does not exist
- `electroplating` points at `50_electricity_semiconductors.md#electrolysis_industrial`, which does not exist
- `dynamo` points at `50_electricity_semiconductors.md#dynamo_motor`, which does not exist
- `motor_transformer_ac` points at `50_electricity_semiconductors.md#transformer_ac`, which does not exist
- `power_grid` points at `50_electricity_semiconductors.md#transformer_ac`, which does not exist
- `arc_light_lamp` points at `50_electricity_semiconductors.md#incandescent_lamp`, which does not exist
- `electrolysis_industrial` points at `50_electricity_semiconductors.md#electrolysis_industrial`, which does not exist
- `vacuum_pumps` points at `50_electricity_semiconductors.md#vacuum_pumps`, which does not exist
- `diffusion_pump` points at `50_electricity_semiconductors.md#vacuum_pumps`, which does not exist
- `discharge_xray` points at `50_electricity_semiconductors.md#crookes_xray_electron`, which does not exist
- `vacuum_tube` points at `50_electricity_semiconductors.md#vacuum_tube`, which does not exist
- `radio` points at `50_electricity_semiconductors.md#radio_spark_to_valve`, which does not exist
- `galena_detector` points at `50_electricity_semiconductors.md#galena_detector`, which does not exist
- `semiconductor_metrology` points at `50_electricity_semiconductors.md#semiconductor_theory`, which does not exist
- `zinc_industry_scale` points at `50_electricity_semiconductors.md#germanium_sourcing`, which does not exist
- `germanium_extraction` points at `50_electricity_semiconductors.md#germanium_sourcing`, which does not exist
- `gecl4_purification` points at `50_electricity_semiconductors.md#germanium_sourcing`, which does not exist
- `ge_reduction` points at `50_electricity_semiconductors.md#germanium_sourcing`, which does not exist
- `zone_refining` points at `50_electricity_semiconductors.md#zone_refining`, which does not exist
- `single_crystal` points at `50_electricity_semiconductors.md#single_crystal_growth`, which does not exist
- `point_contact_transistor` points at `50_electricity_semiconductors.md#point_contact_transistor`, which does not exist
- `junction_transistor` points at `50_electricity_semiconductors.md#junction_transistor`, which does not exist
- `silicon_path` points at `50_electricity_semiconductors.md#silicon_path`, which does not exist

