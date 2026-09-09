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
| [`50_electricity.md`](50_electricity.md) | Electricity, magnetism and electrical machines | 15 | 15 |
| [`55_semiconductors.md`](55_semiconductors.md) | Vacuum, high purity and semiconductors | 13 | 17 |
| [`60_mathematics_method.md`](60_mathematics_method.md) | Mathematics, physics and the scientific method | 13 | 11 |
| [`70_medicine_biology.md`](70_medicine_biology.md) | Medicine, public health and biology | 13 | 3 |
| [`75_agriculture_food.md`](75_agriculture_food.md) | Agriculture, food and surplus | 12 | 2 |
| [`80_information_printing.md`](80_information_printing.md) | Paper, printing and the survival of knowledge | 11 | 5 |
| [`85_transport_civil.md`](85_transport_civil.md) | Transport, mining and civil engineering | 12 | 2 |
| [`99_AUDIT.md`](99_AUDIT.md) | Adversarial audit of the technical modules | 4 | 0 |

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
| `case_hardening` | 1 | 300 | [`case_hardening`](10_metallurgy.md#case_hardening---surface-hardening-a-finished-tool-ferrum-indurare) |
| `drawplate_wire` | 1 | 180 | [`wire_drawing`](10_metallurgy.md#wire_drawing---the-drawplate) |
| `lead_metallurgy` | 1 | 200 | [`lead_silver_cupellation`](10_metallurgy.md#lead_silver_cupellation---refining-silver-from-lead-ore-cupellatio) |
| `bellows_water_blown` | 2 | 300 | [`bellows_water_blown`](10_metallurgy.md#bellows_water_blown---water-driven-double-bellows-and-the-trompe) |
| `blast_furnace` | 2 | 900 | [`blast_furnace_cast_iron`](10_metallurgy.md#blast_furnace_cast_iron---the-tall-shaft-furnace-and-cast-iron) |
| `cementation_steel` | 2 | 400 | [`cementation_steel`](10_metallurgy.md#cementation_steel---blister-steel) |
| `charcoal_industrial` | 2 | 250 | [`charcoal_industrial`](10_metallurgy.md#charcoal_industrial---charcoal-at-scale-carbo) |
| `coal_coke` | 2 | 350 | [`coal_and_coke`](10_metallurgy.md#coal_and_coke---sea-coal-and-coking-carbo-fossilis) |
| `copper_fire_refined` | 2 | 200 | [`copper_refining`](10_metallurgy.md#copper_refining---fire-refining-copper-aes) |
| `crucible_steel` | 2 | 600 | [`crucible_steel`](10_metallurgy.md#crucible_steel---melted-homogeneous-steel-huntsman-process) |
| `finery_puddling` | 2 | 500 | [`finery_forge`](10_metallurgy.md#finery_forge---converting-pig-iron-to-wrought-iron-fining) |
| `mercury_supply` | 2 | 150 | [`mercury`](10_metallurgy.md#mercury---retorting-cinnabar-hydrargyrum) |
| `refractory_fireclay` | 2 | 350 | [`refractory_fireclay`](10_metallurgy.md#refractory_fireclay---furnace-lining-and-crucible-clay-argilla-refractaria) |
| `zinc_metal` | 2 | 700 | [`zinc_metal`](10_metallurgy.md#zinc_metal---distilling-metallic-zinc-per-descensum) |
| `high_temp_furnace` | 3 | 800 | [`high_temp_furnace`](10_metallurgy.md#high_temp_furnace---pushing-past-1500-c) |
| `bessemer_openhearth` | 4 | 900 | [`alloy_steels_ferroalloys`](10_metallurgy.md#alloy_steels_ferroalloys---ferromanganese-ferrosilicon-tungsten-and-chrome-steels) |
| `arc_furnace_ferroalloys` | 5 | 600 | [`alloy_steels_ferroalloys`](10_metallurgy.md#alloy_steels_ferroalloys---ferromanganese-ferrosilicon-tungsten-and-chrome-steels) |

### 20_chemistry.md

| Node | Tier | Your hours | Recipe |
|---|---:|---:|---|
| `distillation_alcohol` | 1 | 450 | [`distillation_fractional`](20_chemistry.md#distillation_fractional---fractional-distillation-and-the-worm-still) |
| `potash_soda` | 1 | 200 | [`potash_and_soda`](20_chemistry.md#potash_and_soda---potash-and-soda-ash-soda-overlaps-with-roman) |
| `soap_hard` | 1 | 250 | [`potash_and_soda`](20_chemistry.md#potash_and_soda---potash-and-soda-ash-soda-overlaps-with-roman) |
| `gunpowder` | 2 | 300 | [`gunpowder`](20_chemistry.md#gunpowder---gunpowder-pulvis-pyrius-a-later-coinage-no-roman) |
| `lab_apparatus` | 2 | 600 | [`lab_apparatus`](20_chemistry.md#lab_apparatus---laboratory-apparatus-vasa-chymica) |
| `nitre_beds` | 2 | 350 | [`saltpetre_nitre_beds`](20_chemistry.md#saltpetre_nitre_beds---saltpetre-nitre-beds-no-roman-name-this) |
| `sulfuric_retort` | 2 | 800 | [`sulfuric_acid_retort`](20_chemistry.md#sulfuric_acid_retort---oil-of-vitriol-by-dry-distillation) |
| `analytical_chemistry` | 3 | 900 | [`analytical_chemistry`](20_chemistry.md#analytical_chemistry---analytical-chemistry-and-the-assay-bench) |
| `destructive_distillation` | 3 | 600 | [`destructive_distillation`](20_chemistry.md#destructive_distillation---destructive-distillation-of-wood-and-coal) |
| `hydrochloric_acid` | 3 | 300 | [`hydrochloric_acid`](20_chemistry.md#hydrochloric_acid---spirit-of-salt-muriatic-acid) |
| `industrial_gases` | 3 | 450 | [`industrial_gases`](20_chemistry.md#industrial_gases---industrial-gases-oxygen-and-hydrogen-without) |
| `lead_chamber` | 3 | 900 | [`lead_chamber`](20_chemistry.md#lead_chamber---the-lead-chamber-process) |
| `nitric_acid` | 3 | 400 | [`nitric_acid`](20_chemistry.md#nitric_acid---nitric-acid-aqua-fortis) |
| `soda_leblanc` | 3 | 600 | [`potash_and_soda`](20_chemistry.md#potash_and_soda---potash-and-soda-ash-soda-overlaps-with-roman) |
| `hydrofluoric_acid` | 4 | 400 | [`hydrofluoric_acid`](20_chemistry.md#hydrofluoric_acid---hydrofluoric-acid-no-established-roman-name) |

### 30_glass_optics.md

| Node | Tier | Your hours | Recipe |
|---|---:|---:|---|
| `camera_obscura` | 1 | 120 | [`camera_obscura_photography`](30_glass_optics.md#camera_obscura_photography---camera-obscura-and-silver-halide-photography) |
| `glass_bead_microscope` | 1 | 300 | [`glass_bead_microscope`](30_glass_optics.md#glass_bead_microscope---bead-microscope) |
| `glass_clear` | 1 | 400 | [`glass_clear_cristallo`](30_glass_optics.md#glass_clear_cristallo---clear-glass-vitrum) |
| `lens_grinding` | 1 | 600 | [`lens_grinding`](30_glass_optics.md#lens_grinding---grinding-and-polishing-lenses) |
| `mirror_amalgam` | 1 | 350 | [`mirrors_amalgam`](30_glass_optics.md#mirrors_amalgam---tin-mercury-amalgam-mirror-later-venetian-mirror) |
| `balance_analytical` | 2 | 700 | [`balance_analytical`](30_glass_optics.md#balance_analytical---analytical-balance-milligram-precision) |
| `barometer` | 2 | 200 | [`thermometer`](30_glass_optics.md#thermometer---sealed-liquid-in-glass-thermometer) |
| `glass_labware` | 2 | 500 | [`glass_lab_ware`](30_glass_optics.md#glass_lab_ware---laboratory-glassware) |
| `telescope` | 2 | 350 | [`telescope`](30_glass_optics.md#telescope---refracting-telescope) |
| `thermometer` | 2 | 400 | [`thermometer`](30_glass_optics.md#thermometer---sealed-liquid-in-glass-thermometer) |
| `glass_borosilicate` | 3 | 500 | [`glass_borosilicate`](30_glass_optics.md#glass_borosilicate---boron-glass-no-roman-name-propose-vitrum-larderellianum) |
| `microscope_compound` | 3 | 600 | [`microscope_compound`](30_glass_optics.md#microscope_compound---compound-microscope) |
| `photography` | 3 | 800 | [`camera_obscura_photography`](30_glass_optics.md#camera_obscura_photography---camera-obscura-and-silver-halide-photography) |
| `spectroscope` | 3 | 500 | [`spectroscope`](30_glass_optics.md#spectroscope---prism-spectroscope) |
| `fused_quartz` | 4 | 700 | [`fused_quartz`](30_glass_optics.md#fused_quartz---fused-silica-pure-quartz-glass) |

### 40_power_precision.md

| Node | Tier | Your hours | Recipe |
|---|---:|---:|---|
| `units_standards` | 0 | 300 | [`micrometer_gauge_blocks`](40_power_precision.md#micrometer_gauge_blocks---screw-micrometer-vernier-scale-and-end) |
| `crank_conrod` | 1 | 300 | [`crank_connecting_rod`](40_power_precision.md#crank_connecting_rod---the-crank-and-connecting-rod-no-attested) |
| `water_power_scale` | 1 | 450 | [`water_power_scaleup`](40_power_precision.md#water_power_scaleup---scaling-up-the-water-wheel-rota-aquaria) |
| `clock_pendulum` | 2 | 500 | [`clockwork_escapement`](40_power_precision.md#clockwork_escapement---verge-and-foliot-pendulum-and-balance) |
| `master_screw` | 2 | 700 | [`screw_cutting_lathe`](40_power_precision.md#screw_cutting_lathe---the-lead-screw-slide-rest-and-change-gears) |
| `precision_three_plate` | 2 | 500 | [`precision_three_plate`](40_power_precision.md#precision_three_plate---whitworths-three-plate-method-no-latin) |
| `boring_mill` | 3 | 600 | [`boring_mill`](40_power_precision.md#boring_mill---the-cylinder-boring-machine-no-latin-term) |
| `interchangeable_parts` | 3 | 800 | [`interchangeable_parts`](40_power_precision.md#interchangeable_parts---gono-go-gauges-tolerance-jigs-and) |
| `micrometer_gauges` | 3 | 500 | [`micrometer_gauge_blocks`](40_power_precision.md#micrometer_gauge_blocks---screw-micrometer-vernier-scale-and-end) |
| `screw_lathe` | 3 | 900 | [`screw_cutting_lathe`](40_power_precision.md#screw_cutting_lathe---the-lead-screw-slide-rest-and-change-gears) |
| `steam_atmospheric` | 3 | 900 | [`steam_atmospheric`](40_power_precision.md#steam_atmospheric---the-newcomen-atmospheric-engine-no-latin-term) |
| `steam_high_pressure` | 4 | 700 | [`steam_high_pressure`](40_power_precision.md#steam_high_pressure---high-pressure-non-condensing-steam-no-latin) |
| `steam_watt` | 4 | 800 | [`steam_watt`](40_power_precision.md#steam_watt---watts-separate-condenser-no-latin-term) |

### 50_electricity.md

| Node | Tier | Your hours | Recipe |
|---|---:|---:|---|
| `em_theory` | 0 | 800 | _(module has no anchor)_ |
| `crude_cell` | 1 | 120 | [`crude_cell`](50_electricity.md#crude_cell---iron-and-copper-brine-cell) |
| `electrostatics` | 2 | 350 | [`electrostatics`](50_electricity.md#electrostatics---static-machines-and-the-leyden-jar-electrum-vis-electrica) |
| `copper_refining` | 3 | 400 | [`wire_insulation`](50_electricity.md#wire_insulation---insulated-wire-varnish-and-cable) |
| `daniell_cell` | 3 | 250 | [`daniell_cell`](50_electricity.md#daniell_cell---two-fluid-cell-daniell-no-latin-name) |
| `electromagnet` | 3 | 350 | [`electromagnet`](50_electricity.md#electromagnet---iron-core-electromagnet-and-relay) |
| `electroplating` | 3 | 350 | [`electrolysis_industrial`](50_electricity.md#electrolysis_industrial---electroplating-electro-refining-chlor-alkali-aluminium) |
| `galvanometer` | 3 | 400 | [`galvanometer`](50_electricity.md#galvanometer---tangent-galvanometer-and-the-absolute-measurement-bootstrap) |
| `telegraph_electric` | 3 | 700 | [`telegraph`](50_electricity.md#telegraph---electric-line-telegraph) |
| `voltaic_pile` | 3 | 300 | [`voltaic_pile`](50_electricity.md#voltaic_pile---zinc-and-copper-disc-pile) |
| `arc_light_lamp` | 4 | 500 | [`incandescent_lamp`](50_electricity.md#incandescent_lamp---filament-lamp-carbon-then-tungsten) |
| `dynamo` | 4 | 800 | [`dynamo_motor`](50_electricity.md#dynamo_motor---faraday-disc-ring-and-drum-armatures-self-excitation) |
| `motor_transformer_ac` | 4 | 700 | [`transformer_ac`](50_electricity.md#transformer_ac---ac-generation-transformers-lamination-three-phase) |
| `electrolysis_industrial` | 5 | 700 | [`electrolysis_industrial`](50_electricity.md#electrolysis_industrial---electroplating-electro-refining-chlor-alkali-aluminium) |
| `power_grid` | 5 | 900 | [`transformer_ac`](50_electricity.md#transformer_ac---ac-generation-transformers-lamination-three-phase) |

### 55_semiconductors.md

| Node | Tier | Your hours | Recipe |
|---|---:|---:|---|
| `quantum_solidstate_theory` | 0 | 1,800 | [`semiconductor_theory`](55_semiconductors.md#semiconductor_theory---what-to-write-down-before-you-can-test-any-of-it-doctrina-de-semiconductoribus) |
| `galena_detector` | 2 | 150 | [`galena_detector`](55_semiconductors.md#galena_detector---the-cats-whisker-rectifier-plumbago-fulminans-informal) |
| `vacuum_pumps` | 4 | 500 | [`vacuum_pumps`](55_semiconductors.md#vacuum_pumps---pumps-and-gauges-for-empty-space-antlia-pneumatica) |
| `diffusion_pump` | 5 | 600 | [`vacuum_pumps`](55_semiconductors.md#vacuum_pumps---pumps-and-gauges-for-empty-space-antlia-pneumatica) |
| `discharge_xray` | 5 | 700 | [`crookes_xray_electron`](55_semiconductors.md#crookes_xray_electron---discharge-tubes-x-rays-and-the-electron-tubus-vacuus-electricus) |
| `ge_reduction` | 5 | 600 | [`germanium_sourcing`](55_semiconductors.md#germanium_sourcing---finding-germanium-at-all-plumbum-cinereum-informal) |
| `gecl4_purification` | 5 | 900 | [`germanium_sourcing`](55_semiconductors.md#germanium_sourcing---finding-germanium-at-all-plumbum-cinereum-informal) |
| `germanium_extraction` | 5 | 900 | [`germanium_sourcing`](55_semiconductors.md#germanium_sourcing---finding-germanium-at-all-plumbum-cinereum-informal) |
| `junction_transistor` | 5 | 800 | [`junction_transistor`](55_semiconductors.md#junction_transistor---grown-and-alloy-junctions-iunctio-amplificans-informal) |
| `point_contact_transistor` | 5 | 900 | [`point_contact_transistor`](55_semiconductors.md#point_contact_transistor---the-first-transistor-punctum-amplificans-informal) |
| `radio` | 5 | 700 | [`radio_spark_to_valve`](55_semiconductors.md#radio_spark_to_valve---from-spark-transmitter-to-the-crystal-set-and-the-valve-radio-telegraphia-sine-filo) |
| `semiconductor_metrology` | 5 | 800 | [`semiconductor_metrology`](55_semiconductors.md#semiconductor_metrology---measuring-what-you-have-made-mensura-resistentiae-informal) |
| `silicon_path` | 5 | 1,000 | [`silicon_path`](55_semiconductors.md#silicon_path---the-alternative-substrate-and-why-to-defer-it-silex-amplificans-informal) |
| `single_crystal` | 5 | 1,000 | [`single_crystal_growth`](55_semiconductors.md#single_crystal_growth---pulling-a-single-crystal-from-the-melt-cristallus-tractus-informal) |
| `vacuum_tube` | 5 | 900 | [`vacuum_tube`](55_semiconductors.md#vacuum_tube---the-diode-and-triode-lampas-electrica) |
| `zinc_industry_scale` | 5 | 600 | [`germanium_sourcing`](55_semiconductors.md#germanium_sourcing---finding-germanium-at-all-plumbum-cinereum-informal) |
| `zone_refining` | 5 | 1,200 | [`zone_refining`](55_semiconductors.md#zone_refining---pfanns-travelling-molten-zone-purgatio-per-zonam-informal) |

### 60_mathematics_method.md

| Node | Tier | Your hours | Recipe |
|---|---:|---:|---|
| `algebra_symbolic` | 0 | 500 | _(module has no anchor)_ |
| `arithmetic_positional` | 0 | 450 | _(module has no anchor)_ |
| `atomic_theory` | 0 | 1,000 | _(module has no anchor)_ |
| `calculus` | 0 | 800 | _(module has no anchor)_ |
| `geometry_analytic` | 0 | 350 | _(module has no anchor)_ |
| `logarithms` | 0 | 400 | _(module has no anchor)_ |
| `newtonian_mechanics` | 0 | 600 | _(module has no anchor)_ |
| `scientific_method` | 0 | 350 | _(module has no anchor)_ |
| `statistics_basic` | 0 | 300 | _(module has no anchor)_ |
| `thermodynamics_theory` | 0 | 700 | _(module has no anchor)_ |
| `world_map` | 0 | 250 | _(module has no anchor)_ |

### 70_medicine_biology.md

| Node | Tier | Your hours | Recipe |
|---|---:|---:|---|
| `germ_theory` | 0 | 350 | [`germ_theory`](70_medicine_biology.md#germ_theory---germ-theory-of-disease-no-roman-term-the-closest-existing-idea-is-varros-semina-morbi-seeds-of-disease) |
| `sanitation_antisepsis` | 1 | 300 | [`sanitation_antisepsis`](70_medicine_biology.md#sanitation_antisepsis---boiled-water-handwashing-wound-irrigation-quarantine-aqua-fervens-manus-lotae-no-single-roman-term-covers-the-practice) |
| `plague_preparedness` | 2 | 700 | [`quarantine_publichealth`](70_medicine_biology.md#quarantine_publichealth---quarantine-clean-water-sewage-separation-and-food-inspection-custodia-cura-aquarum-no-single-roman-term-covers-the-whole-programme) |

### 75_agriculture_food.md

| Node | Tier | Your hours | Recipe |
|---|---:|---:|---|
| `crop_rotation` | 1 | 450 | [`crop_rotation`](75_agriculture_food.md#crop_rotation---three-course-rotation-with-a-legume-break) |
| `horse_collar` | 1 | 200 | [`horse_collar_harness`](75_agriculture_food.md#horse_collar_harness---see-module-40-for-construction-agronomic-case-here) |

### 80_information_printing.md

| Node | Tier | Your hours | Recipe |
|---|---:|---:|---|
| `corpus_written` | 1 | 6,000 | _(module has no anchor)_ |
| `printing_press` | 1 | 900 | _(module has no anchor)_ |
| `rag_paper` | 1 | 400 | _(module has no anchor)_ |
| `semaphore_telegraph` | 1 | 700 | _(module has no anchor)_ |
| `corpus_dispersed` | 2 | 800 | _(module has no anchor)_ |

### 85_transport_civil.md

| Node | Tier | Your hours | Recipe |
|---|---:|---:|---|
| `hot_air_balloon` | 2 | 400 | _(module has no anchor)_ |
| `railway` | 4 | 800 | _(module has no anchor)_ |

