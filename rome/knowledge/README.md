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
| [`10_metallurgy.md`](10_metallurgy.md) | Metallurgy, fuel and refractories | 19 | 69 |
| [`20_chemistry.md`](20_chemistry.md) | Chemistry, acids, alkalis and energetics | 16 | 15 |
| [`30_glass_optics.md`](30_glass_optics.md) | Glass, optics and scientific instruments | 17 | 84 |
| [`40_power_precision.md`](40_power_precision.md) | Prime movers, machine tools and precision | 21 | 137 |
| [`50_electricity.md`](50_electricity.md) | Electricity, magnetism and electrical machines | 15 | 90 |
| [`55_semiconductors.md`](55_semiconductors.md) | Vacuum, high purity and semiconductors | 13 | 17 |
| [`60_mathematics_method.md`](60_mathematics_method.md) | Mathematics, physics and the scientific method | 13 | 11 |
| [`70_medicine_biology.md`](70_medicine_biology.md) | Medicine, public health and biology | 13 | 52 |
| [`75_agriculture_food.md`](75_agriculture_food.md) | Agriculture, food and surplus | 12 | 60 |
| [`80_information_printing.md`](80_information_printing.md) | Paper, printing and the survival of knowledge | 11 | 64 |
| [`85_transport_civil.md`](85_transport_civil.md) | Transport, mining and civil engineering | 12 | 227 |
| [`90_textiles.md`](90_textiles.md) |  | 20 | 0 |
| [`92_vehicles_flight.md`](92_vehicles_flight.md) |  | 29 | 0 |
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
| `met_electro_refining` | 0 | 100 | _(module has no anchor)_ |
| `met_electroplating` | 0 | 60 | _(module has no anchor)_ |
| `met_fire_assay` | 0 | 60 | _(module has no anchor)_ |
| `met_investment_casting` | 0 | 100 | _(module has no anchor)_ |
| `met_ore_crushing_sorting` | 0 | 20 | _(module has no anchor)_ |
| `met_trip_hammer` | 0 | 80 | _(module has no anchor)_ |
| `case_hardening` | 1 | 300 | [`case_hardening`](10_metallurgy.md#case_hardening---surface-hardening-a-finished-tool-ferrum-indurare) |
| `drawplate_wire` | 1 | 180 | [`wire_drawing`](10_metallurgy.md#wire_drawing---the-drawplate) |
| `lead_metallurgy` | 1 | 200 | [`lead_silver_cupellation`](10_metallurgy.md#lead_silver_cupellation---refining-silver-from-lead-ore-cupellatio) |
| `met_annealing_recrystallization` | 1 | 100 | _(module has no anchor)_ |
| `met_cupola_furnace` | 1 | 150 | _(module has no anchor)_ |
| `met_drop_hammer` | 1 | 120 | _(module has no anchor)_ |
| `met_green_sand_mold` | 1 | 80 | _(module has no anchor)_ |
| `met_jigging_gravity` | 1 | 80 | _(module has no anchor)_ |
| `met_mine_pumping` | 1 | 180 | _(module has no anchor)_ |
| `met_reverberatory` | 1 | 200 | _(module has no anchor)_ |
| `met_roasting_calcining` | 1 | 60 | _(module has no anchor)_ |
| `met_tempering_color` | 1 | 120 | _(module has no anchor)_ |
| `met_water_ore_stamp` | 1 | 120 | _(module has no anchor)_ |
| `bellows_water_blown` | 2 | 300 | [`bellows_water_blown`](10_metallurgy.md#bellows_water_blown---water-driven-double-bellows-and-the-trompe) |
| `blast_furnace` | 2 | 900 | [`blast_furnace_cast_iron`](10_metallurgy.md#blast_furnace_cast_iron---the-tall-shaft-furnace-and-cast-iron) |
| `cementation_steel` | 2 | 400 | [`cementation_steel`](10_metallurgy.md#cementation_steel---blister-steel) |
| `charcoal_industrial` | 2 | 250 | [`charcoal_industrial`](10_metallurgy.md#charcoal_industrial---charcoal-at-scale-carbo) |
| `coal_coke` | 2 | 350 | [`coal_and_coke`](10_metallurgy.md#coal_and_coke---sea-coal-and-coking-carbo-fossilis) |
| `copper_fire_refined` | 2 | 200 | [`copper_refining`](10_metallurgy.md#copper_refining---fire-refining-copper-aes) |
| `crucible_steel` | 2 | 600 | [`crucible_steel`](10_metallurgy.md#crucible_steel---melted-homogeneous-steel-huntsman-process) |
| `finery_puddling` | 2 | 500 | [`finery_forge`](10_metallurgy.md#finery_forge---converting-pig-iron-to-wrought-iron-fining) |
| `mercury_supply` | 2 | 150 | [`mercury`](10_metallurgy.md#mercury---retorting-cinnabar-hydrargyrum) |
| `met_basic_lining_phosphorus` | 2 | 240 | _(module has no anchor)_ |
| `met_black_powder_blasting` | 2 | 120 | _(module has no anchor)_ |
| `met_chill_casting` | 2 | 100 | _(module has no anchor)_ |
| `met_continuous_casting` | 2 | 140 | _(module has no anchor)_ |
| `met_converter_furnace` | 2 | 180 | _(module has no anchor)_ |
| `met_deep_shaft_sinking` | 2 | 240 | _(module has no anchor)_ |
| `met_drawn_tube` | 2 | 100 | _(module has no anchor)_ |
| `met_dry_sand_mold` | 2 | 120 | _(module has no anchor)_ |
| `met_froth_flotation` | 2 | 300 | _(module has no anchor)_ |
| `met_galvanizing` | 2 | 120 | _(module has no anchor)_ |
| `met_normalizing` | 2 | 100 | _(module has no anchor)_ |
| `met_open_hearth_furnace` | 2 | 220 | _(module has no anchor)_ |
| `met_quenching_media` | 2 | 140 | _(module has no anchor)_ |
| `met_rail_mill` | 2 | 180 | _(module has no anchor)_ |
| `met_safety_lamps_ventilation` | 2 | 140 | _(module has no anchor)_ |
| `met_tin_plate` | 2 | 100 | _(module has no anchor)_ |
| `met_two_high_mill` | 2 | 280 | _(module has no anchor)_ |
| `met_winding_engine` | 2 | 200 | _(module has no anchor)_ |
| `met_wire_rod_rolling` | 2 | 160 | _(module has no anchor)_ |
| `refractory_fireclay` | 2 | 350 | [`refractory_fireclay`](10_metallurgy.md#refractory_fireclay---furnace-lining-and-crucible-clay-argilla-refractaria) |
| `zinc_metal` | 2 | 700 | [`zinc_metal`](10_metallurgy.md#zinc_metal---distilling-metallic-zinc-per-descensum) |
| `high_temp_furnace` | 3 | 800 | [`high_temp_furnace`](10_metallurgy.md#high_temp_furnace---pushing-past-1500-c) |
| `met_acetylene_supply` | 3 | 200 | _(module has no anchor)_ |
| `met_deep_drawing` | 3 | 220 | _(module has no anchor)_ |
| `met_die_casting` | 3 | 180 | _(module has no anchor)_ |
| `met_dynamite_blasting` | 3 | 100 | _(module has no anchor)_ |
| `met_extrusion_press` | 3 | 200 | _(module has no anchor)_ |
| `met_hardenability_alloys` | 3 | 280 | _(module has no anchor)_ |
| `met_hydraulic_press` | 3 | 240 | _(module has no anchor)_ |
| `met_oxyacetylene_welding` | 3 | 160 | _(module has no anchor)_ |
| `met_pneumatic_drill` | 3 | 180 | _(module has no anchor)_ |
| `met_powder_metallurgy` | 3 | 260 | _(module has no anchor)_ |
| `met_resistance_welding` | 3 | 180 | _(module has no anchor)_ |
| `met_reversing_mill` | 3 | 240 | _(module has no anchor)_ |
| `met_section_mill` | 3 | 200 | _(module has no anchor)_ |
| `met_steam_hammer` | 3 | 180 | _(module has no anchor)_ |
| `met_three_high_mill` | 3 | 200 | _(module has no anchor)_ |
| `met_tube_mill_seamless` | 3 | 220 | _(module has no anchor)_ |
| `bessemer_openhearth` | 4 | 900 | [`alloy_steels_ferroalloys`](10_metallurgy.md#alloy_steels_ferroalloys---ferromanganese-ferrosilicon-tungsten-and-chrome-steels) |
| `met_arc_welding` | 4 | 140 | _(module has no anchor)_ |
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
| `opt_burning_glass` | 0 | 0 | _(module has no anchor)_ |
| `opt_dioptra` | 0 | 0 | _(module has no anchor)_ |
| `opt_geared_mechanisms` | 0 | 0 | _(module has no anchor)_ |
| `opt_groma` | 0 | 0 | _(module has no anchor)_ |
| `opt_metal_mirror_polished` | 0 | 0 | _(module has no anchor)_ |
| `opt_steelyards` | 0 | 0 | _(module has no anchor)_ |
| `opt_sundial` | 0 | 0 | _(module has no anchor)_ |
| `opt_water_clock` | 0 | 0 | _(module has no anchor)_ |
| `opt_water_globe_magnifier` | 0 | 0 | _(module has no anchor)_ |
| `camera_obscura` | 1 | 120 | [`camera_obscura_photography`](30_glass_optics.md#camera_obscura_photography---camera-obscura-and-silver-halide-photography) |
| `glass_bead_microscope` | 1 | 300 | [`glass_bead_microscope`](30_glass_optics.md#glass_bead_microscope---bead-microscope) |
| `glass_clear` | 1 | 400 | [`glass_clear_cristallo`](30_glass_optics.md#glass_clear_cristallo---clear-glass-vitrum) |
| `lens_grinding` | 1 | 600 | [`lens_grinding`](30_glass_optics.md#lens_grinding---grinding-and-polishing-lenses) |
| `mirror_amalgam` | 1 | 350 | [`mirrors_amalgam`](30_glass_optics.md#mirrors_amalgam---tin-mercury-amalgam-mirror-later-venetian-mirror) |
| `opt_anemometer` | 1 | 60 | _(module has no anchor)_ |
| `opt_artificial_horizon` | 1 | 60 | _(module has no anchor)_ |
| `opt_focal_length_measurement` | 1 | 50 | _(module has no anchor)_ |
| `opt_hygrometer` | 1 | 70 | _(module has no anchor)_ |
| `opt_level` | 1 | 80 | _(module has no anchor)_ |
| `opt_manometer` | 1 | 60 | _(module has no anchor)_ |
| `opt_plane_table` | 1 | 100 | _(module has no anchor)_ |
| `opt_plano_convex_lens` | 1 | 40 | _(module has no anchor)_ |
| `opt_sextant` | 1 | 120 | _(module has no anchor)_ |
| `opt_spectacles` | 1 | 60 | _(module has no anchor)_ |
| `opt_spherometer` | 1 | 80 | _(module has no anchor)_ |
| `balance_analytical` | 2 | 700 | [`balance_analytical`](30_glass_optics.md#balance_analytical---analytical-balance-milligram-precision) |
| `barometer` | 2 | 200 | [`thermometer`](30_glass_optics.md#thermometer---sealed-liquid-in-glass-thermometer) |
| `glass_labware` | 2 | 500 | [`glass_lab_ware`](30_glass_optics.md#glass_lab_ware---laboratory-glassware) |
| `opt_abbe_condenser` | 2 | 120 | _(module has no anchor)_ |
| `opt_achromatic_doublet` | 2 | 180 | _(module has no anchor)_ |
| `opt_aneroid_barometer` | 2 | 140 | _(module has no anchor)_ |
| `opt_bourdon_gauge` | 2 | 120 | _(module has no anchor)_ |
| `opt_calorimeter` | 2 | 100 | _(module has no anchor)_ |
| `opt_clock_drive` | 2 | 160 | _(module has no anchor)_ |
| `opt_diffraction_grating` | 2 | 120 | _(module has no anchor)_ |
| `opt_electrometer` | 2 | 120 | _(module has no anchor)_ |
| `opt_equatorial_mount` | 2 | 180 | _(module has no anchor)_ |
| `opt_flame_spark_spectra` | 2 | 80 | _(module has no anchor)_ |
| `opt_fraunhofer_lines` | 2 | 200 | _(module has no anchor)_ |
| `opt_magnetometer` | 2 | 140 | _(module has no anchor)_ |
| `opt_newton_rings` | 2 | 80 | _(module has no anchor)_ |
| `opt_nicol_prism` | 2 | 100 | _(module has no anchor)_ |
| `opt_oil_immersion_objective` | 2 | 130 | _(module has no anchor)_ |
| `opt_photometry` | 2 | 100 | _(module has no anchor)_ |
| `opt_pitot_tube` | 2 | 80 | _(module has no anchor)_ |
| `opt_polarimeter` | 2 | 120 | _(module has no anchor)_ |
| `opt_pyrometer_contraction` | 2 | 80 | _(module has no anchor)_ |
| `opt_reflecting_telescope` | 2 | 200 | _(module has no anchor)_ |
| `opt_refractometer` | 2 | 140 | _(module has no anchor)_ |
| `opt_silvered_glass_mirror` | 2 | 150 | _(module has no anchor)_ |
| `opt_spectroscopy_absorption` | 2 | 120 | _(module has no anchor)_ |
| `opt_spectroscopy_emission` | 2 | 100 | _(module has no anchor)_ |
| `opt_speculum_metal` | 2 | 120 | _(module has no anchor)_ |
| `opt_stellar_parallax` | 2 | 150 | _(module has no anchor)_ |
| `opt_theodolite` | 2 | 200 | _(module has no anchor)_ |
| `opt_transit_instrument` | 2 | 200 | _(module has no anchor)_ |
| `telescope` | 2 | 350 | [`telescope`](30_glass_optics.md#telescope---refracting-telescope) |
| `thermometer` | 2 | 400 | [`thermometer`](30_glass_optics.md#thermometer---sealed-liquid-in-glass-thermometer) |
| `glass_borosilicate` | 3 | 500 | [`glass_borosilicate`](30_glass_optics.md#glass_borosilicate---boron-glass-no-roman-name-propose-vitrum-larderellianum) |
| `microscope_compound` | 3 | 600 | [`microscope_compound`](30_glass_optics.md#microscope_compound---compound-microscope) |
| `opt_apochromat` | 3 | 250 | _(module has no anchor)_ |
| `opt_ballistic_galvanometer` | 3 | 160 | _(module has no anchor)_ |
| `opt_bolometer` | 3 | 200 | _(module has no anchor)_ |
| `opt_chronograph` | 3 | 160 | _(module has no anchor)_ |
| `opt_gravimeter` | 3 | 220 | _(module has no anchor)_ |
| `opt_michelson_interferometer` | 3 | 250 | _(module has no anchor)_ |
| `opt_phase_contrast` | 3 | 200 | _(module has no anchor)_ |
| `opt_photocell` | 3 | 180 | _(module has no anchor)_ |
| `opt_potentiometer` | 3 | 180 | _(module has no anchor)_ |
| `opt_pyrometer_optical` | 3 | 120 | _(module has no anchor)_ |
| `opt_pyrometer_radiation` | 3 | 180 | _(module has no anchor)_ |
| `opt_pyrometer_thermoelectric` | 3 | 150 | _(module has no anchor)_ |
| `opt_ruling_engine` | 3 | 400 | _(module has no anchor)_ |
| `opt_seismograph` | 3 | 200 | _(module has no anchor)_ |
| `opt_spectroheliograph` | 3 | 250 | _(module has no anchor)_ |
| `opt_standards_laboratory` | 3 | 500 | _(module has no anchor)_ |
| `opt_stroboscope` | 3 | 140 | _(module has no anchor)_ |
| `opt_ultramicroscope` | 3 | 150 | _(module has no anchor)_ |
| `photography` | 3 | 800 | [`camera_obscura_photography`](30_glass_optics.md#camera_obscura_photography---camera-obscura-and-silver-halide-photography) |
| `spectroscope` | 3 | 500 | [`spectroscope`](30_glass_optics.md#spectroscope---prism-spectroscope) |
| `fused_quartz` | 4 | 700 | [`fused_quartz`](30_glass_optics.md#fused_quartz---fused-silica-pure-quartz-glass) |
| `opt_electron_microscope` | 4 | 400 | _(module has no anchor)_ |
| `opt_high_speed_camera` | 4 | 280 | _(module has no anchor)_ |
| `opt_oscilloscope` | 4 | 300 | _(module has no anchor)_ |

### 40_power_precision.md

| Node | Tier | Your hours | Recipe |
|---|---:|---:|---|
| `pwr_animal_treadmill` | 0 | 0 | _(module has no anchor)_ |
| `pwr_force_pump` | 0 | 0 | _(module has no anchor)_ |
| `pwr_overshot_wheel` | 0 | 0 | _(module has no anchor)_ |
| `pwr_screw_press_power` | 0 | 0 | _(module has no anchor)_ |
| `pwr_ship_sail` | 0 | 0 | _(module has no anchor)_ |
| `pwr_treadwheel_crane` | 0 | 0 | _(module has no anchor)_ |
| `pwr_undershot_wheel` | 0 | 0 | _(module has no anchor)_ |
| `units_standards` | 0 | 300 | [`micrometer_gauge_blocks`](40_power_precision.md#micrometer_gauge_blocks---screw-micrometer-vernier-scale-and-end) |
| `crank_conrod` | 1 | 300 | [`crank_connecting_rod`](40_power_precision.md#crank_connecting_rod---the-crank-and-connecting-rod-no-attested) |
| `prc_arbor_press` | 1 | 40 | _(module has no anchor)_ |
| `prc_back_gear` | 1 | 60 | _(module has no anchor)_ |
| `prc_drill_press` | 1 | 70 | _(module has no anchor)_ |
| `prc_lathe_faceplate` | 1 | 40 | _(module has no anchor)_ |
| `prc_mandrel_chuck` | 1 | 60 | _(module has no anchor)_ |
| `prc_reamer_hand_flute` | 1 | 40 | _(module has no anchor)_ |
| `prc_slide_rest_simple` | 1 | 100 | _(module has no anchor)_ |
| `prc_square_reference` | 1 | 50 | _(module has no anchor)_ |
| `prc_straightedge` | 1 | 30 | _(module has no anchor)_ |
| `prc_tailstock_deadcentre` | 1 | 50 | _(module has no anchor)_ |
| `prc_treadle_lathe_flywheel` | 1 | 80 | _(module has no anchor)_ |
| `prc_twist_drill` | 1 | 50 | _(module has no anchor)_ |
| `pwr_breastshot_wheel` | 1 | 180 | _(module has no anchor)_ |
| `pwr_flywheel_governor` | 1 | 150 | _(module has no anchor)_ |
| `pwr_leat_and_weir` | 1 | 200 | _(module has no anchor)_ |
| `pwr_millpond` | 1 | 150 | _(module has no anchor)_ |
| `pwr_norse_waterwheel` | 1 | 120 | _(module has no anchor)_ |
| `pwr_oil_shale` | 1 | 80 | _(module has no anchor)_ |
| `pwr_peat` | 1 | 100 | _(module has no anchor)_ |
| `pwr_smeaton_efficiency` | 1 | 200 | _(module has no anchor)_ |
| `water_power_scale` | 1 | 450 | [`water_power_scaleup`](40_power_precision.md#water_power_scaleup---scaling-up-the-water-wheel-rota-aquaria) |
| `clock_pendulum` | 2 | 500 | [`clockwork_escapement`](40_power_precision.md#clockwork_escapement---verge-and-foliot-pendulum-and-balance) |
| `master_screw` | 2 | 700 | [`screw_cutting_lathe`](40_power_precision.md#screw_cutting_lathe---the-lead-screw-slide-rest-and-change-gears) |
| `prc_capstan_turret_lathe` | 2 | 150 | _(module has no anchor)_ |
| `prc_change_gears_quadrant` | 2 | 80 | _(module has no anchor)_ |
| `prc_compound_slide_rest` | 2 | 120 | _(module has no anchor)_ |
| `prc_coolant_cutting_fluid` | 2 | 50 | _(module has no anchor)_ |
| `prc_cylindrical_square` | 2 | 60 | _(module has no anchor)_ |
| `prc_depth_gauge` | 2 | 40 | _(module has no anchor)_ |
| `prc_dial_indicator` | 2 | 90 | _(module has no anchor)_ |
| `prc_dividing_head` | 2 | 100 | _(module has no anchor)_ |
| `prc_fly_cutter` | 2 | 50 | _(module has no anchor)_ |
| `prc_go_nogo_gauge` | 2 | 60 | _(module has no anchor)_ |
| `prc_jig_and_fixture` | 2 | 120 | _(module has no anchor)_ |
| `prc_lapping_plate` | 2 | 60 | _(module has no anchor)_ |
| `prc_lead_screw_error_cam` | 2 | 100 | _(module has no anchor)_ |
| `prc_machine_frame_cast_iron` | 2 | 120 | _(module has no anchor)_ |
| `prc_milling_machine` | 2 | 160 | _(module has no anchor)_ |
| `prc_pantograph_copying` | 2 | 80 | _(module has no anchor)_ |
| `prc_planer_machine` | 2 | 140 | _(module has no anchor)_ |
| `prc_scraped_surface_plate` | 2 | 200 | _(module has no anchor)_ |
| `prc_shaper_machine` | 2 | 100 | _(module has no anchor)_ |
| `prc_sine_bar` | 2 | 80 | _(module has no anchor)_ |
| `prc_slotter_machine` | 2 | 70 | _(module has no anchor)_ |
| `prc_tap_die` | 2 | 80 | _(module has no anchor)_ |
| `prc_three_wire_thread_measure` | 2 | 70 | _(module has no anchor)_ |
| `prc_vernier_caliper` | 2 | 60 | _(module has no anchor)_ |
| `precision_three_plate` | 2 | 500 | [`precision_three_plate`](40_power_precision.md#precision_three_plate---whitworths-three-plate-method-no-latin) |
| `pwr_boiler_haystack` | 2 | 180 | _(module has no anchor)_ |
| `pwr_boiler_wagon` | 2 | 200 | _(module has no anchor)_ |
| `pwr_cable_tool_drilling` | 2 | 300 | _(module has no anchor)_ |
| `pwr_coal_gas` | 2 | 300 | _(module has no anchor)_ |
| `pwr_coal_seam` | 2 | 150 | _(module has no anchor)_ |
| `pwr_coking` | 2 | 200 | _(module has no anchor)_ |
| `pwr_condenser` | 2 | 200 | _(module has no anchor)_ |
| `pwr_flywheel_storage` | 2 | 200 | _(module has no anchor)_ |
| `pwr_fuel_oil` | 2 | 150 | _(module has no anchor)_ |
| `pwr_gas_main` | 2 | 250 | _(module has no anchor)_ |
| `pwr_gas_meter` | 2 | 180 | _(module has no anchor)_ |
| `pwr_hydroelectric_generation` | 2 | 400 | _(module has no anchor)_ |
| `pwr_indicator_diagram` | 2 | 200 | _(module has no anchor)_ |
| `pwr_kerosene` | 2 | 100 | _(module has no anchor)_ |
| `pwr_oil_refinery` | 2 | 300 | _(module has no anchor)_ |
| `pwr_pelton_wheel` | 2 | 250 | _(module has no anchor)_ |
| `pwr_petroleum_seeps` | 2 | 100 | _(module has no anchor)_ |
| `pwr_post_mill` | 2 | 250 | _(module has no anchor)_ |
| `pwr_safety_valve` | 2 | 150 | _(module has no anchor)_ |
| `pwr_tide_mill` | 2 | 200 | _(module has no anchor)_ |
| `pwr_tower_mill` | 2 | 300 | _(module has no anchor)_ |
| `pwr_trompe` | 2 | 180 | _(module has no anchor)_ |
| `pwr_water_turbine_fourneyron` | 2 | 300 | _(module has no anchor)_ |
| `pwr_windmill_fantail` | 2 | 200 | _(module has no anchor)_ |
| `boring_mill` | 3 | 600 | [`boring_mill`](40_power_precision.md#boring_mill---the-cylinder-boring-machine-no-latin-term) |
| `interchangeable_parts` | 3 | 800 | [`interchangeable_parts`](40_power_precision.md#interchangeable_parts---gono-go-gauges-tolerance-jigs-and) |
| `micrometer_gauges` | 3 | 500 | [`micrometer_gauge_blocks`](40_power_precision.md#micrometer_gauge_blocks---screw-micrometer-vernier-scale-and-end) |
| `prc_autocollimator` | 3 | 110 | _(module has no anchor)_ |
| `prc_automatic_screw_machine` | 3 | 200 | _(module has no anchor)_ |
| `prc_ball_roller_bearing` | 3 | 140 | _(module has no anchor)_ |
| `prc_ballscrew` | 3 | 130 | _(module has no anchor)_ |
| `prc_broach_machine` | 3 | 110 | _(module has no anchor)_ |
| `prc_comparator_optical` | 3 | 100 | _(module has no anchor)_ |
| `prc_cylindrical_grinder` | 3 | 130 | _(module has no anchor)_ |
| `prc_die_sinker` | 3 | 110 | _(module has no anchor)_ |
| `prc_gauge_blocks_johansson` | 3 | 120 | _(module has no anchor)_ |
| `prc_honing_machine` | 3 | 100 | _(module has no anchor)_ |
| `prc_jig_boring_machine` | 3 | 150 | _(module has no anchor)_ |
| `prc_metrology_room_20c` | 3 | 200 | _(module has no anchor)_ |
| `prc_optical_flat` | 3 | 100 | _(module has no anchor)_ |
| `prc_profile_projector` | 3 | 110 | _(module has no anchor)_ |
| `prc_roundness_measurement` | 3 | 100 | _(module has no anchor)_ |
| `prc_surface_grinder` | 3 | 140 | _(module has no anchor)_ |
| `prc_tool_cutter_grinder` | 3 | 120 | _(module has no anchor)_ |
| `prc_tool_steel_hss_carbide` | 3 | 100 | _(module has no anchor)_ |
| `prc_toolmaker_microscope` | 3 | 130 | _(module has no anchor)_ |
| `prc_tracer_lathe` | 3 | 140 | _(module has no anchor)_ |
| `prc_universal_milling_machine` | 3 | 180 | _(module has no anchor)_ |
| `prc_vibration_and_chatter` | 3 | 100 | _(module has no anchor)_ |
| `pwr_boiler_cornish` | 3 | 250 | _(module has no anchor)_ |
| `pwr_boiler_lancashire` | 3 | 250 | _(module has no anchor)_ |
| `pwr_boiler_water_tube` | 3 | 300 | _(module has no anchor)_ |
| `pwr_feedwater_heating` | 3 | 200 | _(module has no anchor)_ |
| `pwr_gas_engine` | 3 | 350 | _(module has no anchor)_ |
| `pwr_high_voltage_transmission` | 3 | 300 | _(module has no anchor)_ |
| `pwr_lead_acid_battery` | 3 | 250 | _(module has no anchor)_ |
| `pwr_pipeline` | 3 | 250 | _(module has no anchor)_ |
| `pwr_pumped_storage` | 3 | 400 | _(module has no anchor)_ |
| `pwr_rotary_drilling` | 3 | 350 | _(module has no anchor)_ |
| `pwr_selenium_metal` | 3 | 200 | _(module has no anchor)_ |
| `pwr_steam_turbine_parsons` | 3 | 400 | _(module has no anchor)_ |
| `pwr_stirling_engine` | 3 | 300 | _(module has no anchor)_ |
| `pwr_substation` | 3 | 300 | _(module has no anchor)_ |
| `pwr_superheater` | 3 | 200 | _(module has no anchor)_ |
| `pwr_thermoelectric_couple` | 3 | 200 | _(module has no anchor)_ |
| `pwr_thermopile` | 3 | 150 | _(module has no anchor)_ |
| `pwr_three_phase_ac` | 3 | 250 | _(module has no anchor)_ |
| `pwr_transformer` | 3 | 250 | _(module has no anchor)_ |
| `screw_lathe` | 3 | 900 | [`screw_cutting_lathe`](40_power_precision.md#screw_cutting_lathe---the-lead-screw-slide-rest-and-change-gears) |
| `steam_atmospheric` | 3 | 900 | [`steam_atmospheric`](40_power_precision.md#steam_atmospheric---the-newcomen-atmospheric-engine-no-latin-term) |
| `prc_standard_meter_wavelength` | 4 | 150 | _(module has no anchor)_ |
| `pwr_electric_motor_industry` | 4 | 300 | _(module has no anchor)_ |
| `pwr_fuel_cell` | 4 | 300 | _(module has no anchor)_ |
| `pwr_load_factor_economics` | 4 | 200 | _(module has no anchor)_ |
| `pwr_nickel_iron_battery` | 4 | 300 | _(module has no anchor)_ |
| `pwr_selenium_cell` | 4 | 150 | _(module has no anchor)_ |
| `pwr_selenium_photovoltaic` | 4 | 200 | _(module has no anchor)_ |
| `steam_high_pressure` | 4 | 700 | [`steam_high_pressure`](40_power_precision.md#steam_high_pressure---high-pressure-non-condensing-steam-no-latin) |
| `steam_watt` | 4 | 800 | [`steam_watt`](40_power_precision.md#steam_watt---watts-separate-condenser-no-latin-term) |
| `pwr_nuclear_fission` | 5 | 500 | _(module has no anchor)_ |

### 50_electricity.md

| Node | Tier | Your hours | Recipe |
|---|---:|---:|---|
| `em_theory` | 0 | 800 | _(module has no anchor)_ |
| `com_optical_codebook` | 1 | 100 | _(module has no anchor)_ |
| `com_signal_flags` | 1 | 40 | _(module has no anchor)_ |
| `crude_cell` | 1 | 120 | [`crude_cell`](50_electricity.md#crude_cell---iron-and-copper-brine-cell) |
| `com_heliograph` | 2 | 80 | _(module has no anchor)_ |
| `com_jacquard_loom` | 2 | 120 | _(module has no anchor)_ |
| `com_morse_code` | 2 | 60 | _(module has no anchor)_ |
| `com_morse_register` | 2 | 100 | _(module has no anchor)_ |
| `com_morse_sounder` | 2 | 80 | _(module has no anchor)_ |
| `com_napiers_bones` | 2 | 100 | _(module has no anchor)_ |
| `com_optical_tower` | 2 | 120 | _(module has no anchor)_ |
| `com_relay` | 2 | 100 | _(module has no anchor)_ |
| `com_stepped_drum` | 2 | 80 | _(module has no anchor)_ |
| `com_stock_ticker` | 2 | 100 | _(module has no anchor)_ |
| `com_telegraph_battery` | 2 | 60 | _(module has no anchor)_ |
| `electrostatics` | 2 | 350 | [`electrostatics`](50_electricity.md#electrostatics---static-machines-and-the-leyden-jar-electrum-vis-electrica) |
| `com_analytical_engine` | 3 | 250 | _(module has no anchor)_ |
| `com_antenna_ground` | 3 | 60 | _(module has no anchor)_ |
| `com_arithmometer` | 3 | 120 | _(module has no anchor)_ |
| `com_baudot_code` | 3 | 60 | _(module has no anchor)_ |
| `com_coherer` | 3 | 60 | _(module has no anchor)_ |
| `com_comptometer` | 3 | 140 | _(module has no anchor)_ |
| `com_cryptography_substitution` | 3 | 80 | _(module has no anchor)_ |
| `com_difference_engine` | 3 | 200 | _(module has no anchor)_ |
| `com_duplex_telegraph` | 3 | 120 | _(module has no anchor)_ |
| `com_loading_coil` | 3 | 80 | _(module has no anchor)_ |
| `com_mechanical_calculator` | 3 | 150 | _(module has no anchor)_ |
| `com_multiplexing` | 3 | 120 | _(module has no anchor)_ |
| `com_quadruplex_telegraph` | 3 | 140 | _(module has no anchor)_ |
| `com_slide_rule` | 3 | 80 | _(module has no anchor)_ |
| `com_strowger_exchange` | 3 | 180 | _(module has no anchor)_ |
| `com_submarine_cable` | 3 | 200 | _(module has no anchor)_ |
| `com_telephone_carbon_mic` | 3 | 100 | _(module has no anchor)_ |
| `com_telephone_diaphragm` | 3 | 80 | _(module has no anchor)_ |
| `com_telephone_manual_exchange` | 3 | 150 | _(module has no anchor)_ |
| `com_teleprinter` | 3 | 140 | _(module has no anchor)_ |
| `com_trunk_lines` | 3 | 100 | _(module has no anchor)_ |
| `com_tuned_circuit` | 3 | 100 | _(module has no anchor)_ |
| `com_tv_mechanical_scanning` | 3 | 140 | _(module has no anchor)_ |
| `copper_refining` | 3 | 400 | [`wire_insulation`](50_electricity.md#wire_insulation---insulated-wire-varnish-and-cable) |
| `daniell_cell` | 3 | 250 | [`daniell_cell`](50_electricity.md#daniell_cell---two-fluid-cell-daniell-no-latin-name) |
| `electromagnet` | 3 | 350 | [`electromagnet`](50_electricity.md#electromagnet---iron-core-electromagnet-and-relay) |
| `electroplating` | 3 | 350 | [`electrolysis_industrial`](50_electricity.md#electrolysis_industrial---electroplating-electro-refining-chlor-alkali-aluminium) |
| `galvanometer` | 3 | 400 | [`galvanometer`](50_electricity.md#galvanometer---tangent-galvanometer-and-the-absolute-measurement-bootstrap) |
| `telegraph_electric` | 3 | 700 | [`telegraph`](50_electricity.md#telegraph---electric-line-telegraph) |
| `voltaic_pile` | 3 | 300 | [`voltaic_pile`](50_electricity.md#voltaic_pile---zinc-and-copper-disc-pile) |
| `arc_light_lamp` | 4 | 500 | [`incandescent_lamp`](50_electricity.md#incandescent_lamp---filament-lamp-carbon-then-tungsten) |
| `com_accumulator` | 4 | 130 | _(module has no anchor)_ |
| `com_amplitude_modulation` | 4 | 100 | _(module has no anchor)_ |
| `com_binary_arithmetic` | 4 | 100 | _(module has no anchor)_ |
| `com_boolean_algebra` | 4 | 120 | _(module has no anchor)_ |
| `com_broadcasting_institution` | 4 | 200 | _(module has no anchor)_ |
| `com_cathode_ray_tube` | 4 | 120 | _(module has no anchor)_ |
| `com_continuous_wave` | 4 | 120 | _(module has no anchor)_ |
| `com_crystal_set` | 4 | 80 | _(module has no anchor)_ |
| `com_flip_flop` | 4 | 100 | _(module has no anchor)_ |
| `com_frequency_modulation` | 4 | 140 | _(module has no anchor)_ |
| `com_hollerith_tabulation` | 4 | 180 | _(module has no anchor)_ |
| `com_logic_gate` | 4 | 100 | _(module has no anchor)_ |
| `com_magnetic_core_memory` | 4 | 140 | _(module has no anchor)_ |
| `com_magnetic_drum_storage` | 4 | 110 | _(module has no anchor)_ |
| `com_magnetic_tape_storage` | 4 | 120 | _(module has no anchor)_ |
| `com_magnetic_wire_storage` | 4 | 100 | _(module has no anchor)_ |
| `com_one_time_pad` | 4 | 100 | _(module has no anchor)_ |
| `com_radar_magnetron` | 4 | 160 | _(module has no anchor)_ |
| `com_radio_spark_transmitter` | 4 | 120 | _(module has no anchor)_ |
| `com_register_computing` | 4 | 120 | _(module has no anchor)_ |
| `com_relay_computer` | 4 | 300 | _(module has no anchor)_ |
| `com_ring_counter` | 4 | 110 | _(module has no anchor)_ |
| `com_rotor_machine` | 4 | 160 | _(module has no anchor)_ |
| `com_superheterodyne_receiver` | 4 | 160 | _(module has no anchor)_ |
| `com_triode_oscillator` | 4 | 100 | _(module has no anchor)_ |
| `com_tv_electronic_camera` | 4 | 160 | _(module has no anchor)_ |
| `com_tv_raster_sync` | 4 | 120 | _(module has no anchor)_ |
| `com_vacuum_tube_computer` | 4 | 400 | _(module has no anchor)_ |
| `com_vacuum_tube_pentode` | 4 | 110 | _(module has no anchor)_ |
| `com_vacuum_tube_tetrode` | 4 | 100 | _(module has no anchor)_ |
| `com_waveguide` | 4 | 80 | _(module has no anchor)_ |
| `dynamo` | 4 | 800 | [`dynamo_motor`](50_electricity.md#dynamo_motor---faraday-disc-ring-and-drum-armatures-self-excitation) |
| `motor_transformer_ac` | 4 | 700 | [`transformer_ac`](50_electricity.md#transformer_ac---ac-generation-transformers-lamination-three-phase) |
| `com_compiler_and_language` | 5 | 300 | _(module has no anchor)_ |
| `com_error_detecting_code` | 5 | 140 | _(module has no anchor)_ |
| `com_information_theory` | 5 | 160 | _(module has no anchor)_ |
| `com_integrated_circuit` | 5 | 220 | _(module has no anchor)_ |
| `com_photolithography` | 5 | 180 | _(module has no anchor)_ |
| `com_public_key_cryptography` | 5 | 200 | _(module has no anchor)_ |
| `com_semiconductor_diode` | 5 | 100 | _(module has no anchor)_ |
| `com_stored_program_concept` | 5 | 180 | _(module has no anchor)_ |
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
| `med_amputation` | 0 | 0 | _(module has no anchor)_ |
| `med_aqueducts_latrines` | 0 | 0 | _(module has no anchor)_ |
| `med_bone_setting` | 0 | 0 | _(module has no anchor)_ |
| `med_cataract_couching` | 0 | 0 | _(module has no anchor)_ |
| `med_herbal_pharmacy` | 0 | 100 | _(module has no anchor)_ |
| `med_legal_physician` | 0 | 0 | _(module has no anchor)_ |
| `med_obstetric_practice` | 0 | 0 | _(module has no anchor)_ |
| `med_opium_mandrake` | 0 | 0 | _(module has no anchor)_ |
| `med_surgical_kit_good` | 0 | 0 | _(module has no anchor)_ |
| `med_trepanation` | 0 | 0 | _(module has no anchor)_ |
| `med_valetudinaria` | 0 | 200 | _(module has no anchor)_ |
| `med_wound_suturing` | 0 | 0 | _(module has no anchor)_ |
| `med_clinical_thermometer` | 1 | 60 | _(module has no anchor)_ |
| `med_epidemiology_statistics` | 1 | 150 | _(module has no anchor)_ |
| `med_handwashing_semmelweis` | 1 | 80 | _(module has no anchor)_ |
| `med_hospital_institution` | 1 | 200 | _(module has no anchor)_ |
| `med_ligature_haemostasis` | 1 | 60 | _(module has no anchor)_ |
| `med_medical_education` | 1 | 200 | _(module has no anchor)_ |
| `med_nursing_profession` | 1 | 150 | _(module has no anchor)_ |
| `med_nutrition_vitamins` | 1 | 120 | _(module has no anchor)_ |
| `med_obstetric_antisepsis` | 1 | 120 | _(module has no anchor)_ |
| `med_quarantine_sanitation` | 1 | 150 | _(module has no anchor)_ |
| `med_saline_resuscitation` | 1 | 60 | _(module has no anchor)_ |
| `med_spectacles_refraction` | 1 | 60 | _(module has no anchor)_ |
| `med_stethoscope_percussion` | 1 | 60 | _(module has no anchor)_ |
| `med_surgical_gloves_mask` | 1 | 40 | _(module has no anchor)_ |
| `med_vector_control` | 1 | 100 | _(module has no anchor)_ |
| `sanitation_antisepsis` | 1 | 300 | [`sanitation_antisepsis`](70_medicine_biology.md#sanitation_antisepsis---boiled-water-handwashing-wound-irrigation-quarantine-aqua-fervens-manus-lotae-no-single-roman-term-covers-the-practice) |
| `med_antitoxin_serum` | 2 | 120 | _(module has no anchor)_ |
| `med_asepsis_antisepsis` | 2 | 120 | _(module has no anchor)_ |
| `med_aspirin` | 2 | 80 | _(module has no anchor)_ |
| `med_autoclave` | 2 | 150 | _(module has no anchor)_ |
| `med_blood_groups` | 2 | 150 | _(module has no anchor)_ |
| `med_clinical_trials` | 2 | 200 | _(module has no anchor)_ |
| `med_dentistry` | 2 | 120 | _(module has no anchor)_ |
| `med_ether_anaesthesia` | 2 | 120 | _(module has no anchor)_ |
| `med_forensic_medicine` | 2 | 120 | _(module has no anchor)_ |
| `med_gram_stain_culture` | 2 | 100 | _(module has no anchor)_ |
| `med_hypodermic_syringe` | 2 | 100 | _(module has no anchor)_ |
| `med_microscopy_pathology` | 2 | 120 | _(module has no anchor)_ |
| `med_ophthalmoscope` | 2 | 100 | _(module has no anchor)_ |
| `med_sphygmomanometer` | 2 | 100 | _(module has no anchor)_ |
| `med_sterile_technique` | 2 | 100 | _(module has no anchor)_ |
| `med_vaccination_progression` | 2 | 150 | _(module has no anchor)_ |
| `plague_preparedness` | 2 | 700 | [`quarantine_publichealth`](70_medicine_biology.md#quarantine_publichealth---quarantine-clean-water-sewage-separation-and-food-inspection-custodia-cura-aquarum-no-single-roman-term-covers-the-whole-programme) |
| `med_endoscope` | 3 | 200 | _(module has no anchor)_ |
| `med_sulfonamides` | 3 | 150 | _(module has no anchor)_ |
| `med_xray_imaging` | 3 | 200 | _(module has no anchor)_ |
| `med_electrocardiogram` | 4 | 200 | _(module has no anchor)_ |
| `med_insulin` | 4 | 200 | _(module has no anchor)_ |
| `med_penicillin` | 4 | 250 | _(module has no anchor)_ |

### 75_agriculture_food.md

| Node | Tier | Your hours | Recipe |
|---|---:|---:|---|
| `crop_rotation` | 1 | 450 | [`crop_rotation`](75_agriculture_food.md#crop_rotation---three-course-rotation-with-a-legume-break) |
| `fud_alfalfa` | 1 | 100 | _(module has no anchor)_ |
| `fud_bone_meal_fertilizer` | 1 | 100 | _(module has no anchor)_ |
| `fud_bottling_sealed_cork` | 1 | 80 | _(module has no anchor)_ |
| `fud_brewing_with_hops` | 1 | 120 | _(module has no anchor)_ |
| `fud_clover_winter_fodder` | 1 | 80 | _(module has no anchor)_ |
| `fud_coffee_trade_import` | 1 | 60 | _(module has no anchor)_ |
| `fud_controlled_pollination` | 1 | 150 | _(module has no anchor)_ |
| `fud_dairy_butter_production` | 1 | 120 | _(module has no anchor)_ |
| `fud_dairy_cheese_aging` | 1 | 100 | _(module has no anchor)_ |
| `fud_distillation_spirits` | 1 | 150 | _(module has no anchor)_ |
| `fud_enclosure_of_common_land` | 1 | 150 | _(module has no anchor)_ |
| `fud_farm_as_capital_enterprise` | 1 | 200 | _(module has no anchor)_ |
| `fud_fish_curing_and_smoking` | 1 | 120 | _(module has no anchor)_ |
| `fud_guano_import_trade` | 1 | 80 | _(module has no anchor)_ |
| `fud_hay_making_storage` | 1 | 100 | _(module has no anchor)_ |
| `fud_horse_hoe` | 1 | 120 | _(module has no anchor)_ |
| `fud_ice_harvesting_and_cutting` | 1 | 100 | _(module has no anchor)_ |
| `fud_ice_house_construction` | 1 | 150 | _(module has no anchor)_ |
| `fud_liming_acid_soils` | 1 | 100 | _(module has no anchor)_ |
| `fud_livestock_selective_cattle` | 1 | 200 | _(module has no anchor)_ |
| `fud_livestock_selective_sheep` | 1 | 180 | _(module has no anchor)_ |
| `fud_malt_production` | 1 | 120 | _(module has no anchor)_ |
| `fud_nitrogen_fixing_understanding` | 1 | 80 | _(module has no anchor)_ |
| `fud_rice_cultivation` | 1 | 120 | _(module has no anchor)_ |
| `fud_root_cellar_storage` | 1 | 120 | _(module has no anchor)_ |
| `fud_seed_drill` | 1 | 180 | _(module has no anchor)_ |
| `fud_selective_breeding_pedigree` | 1 | 200 | _(module has no anchor)_ |
| `fud_sourdough_starter` | 1 | 100 | _(module has no anchor)_ |
| `fud_sugar_cane_cultivation` | 1 | 100 | _(module has no anchor)_ |
| `fud_tea_trade_import` | 1 | 60 | _(module has no anchor)_ |
| `fud_three_field_rotation` | 1 | 120 | _(module has no anchor)_ |
| `fud_turnips_winter_fodder` | 1 | 100 | _(module has no anchor)_ |
| `fud_vegetable_oil_extraction` | 1 | 100 | _(module has no anchor)_ |
| `fud_vinegar_production` | 1 | 80 | _(module has no anchor)_ |
| `horse_collar` | 1 | 200 | [`horse_collar_harness`](75_agriculture_food.md#horse_collar_harness---see-module-40-for-construction-agronomic-case-here) |
| `fud_beet_sugar_processing` | 2 | 200 | _(module has no anchor)_ |
| `fud_canning_appert_method` | 2 | 200 | _(module has no anchor)_ |
| `fud_drying_evaporated_milk` | 2 | 150 | _(module has no anchor)_ |
| `fud_grain_storage_silos` | 2 | 200 | _(module has no anchor)_ |
| `fud_heavy_mouldboard_plough_coulter` | 2 | 200 | _(module has no anchor)_ |
| `fud_ice_trade_logistics` | 2 | 120 | _(module has no anchor)_ |
| `fud_mechanical_reaper` | 2 | 300 | _(module has no anchor)_ |
| `fud_pasteurisation` | 2 | 180 | _(module has no anchor)_ |
| `fud_roller_mill` | 2 | 250 | _(module has no anchor)_ |
| `fud_roller_milled_white_flour` | 2 | 150 | _(module has no anchor)_ |
| `fud_silage_fermentation` | 2 | 150 | _(module has no anchor)_ |
| `fud_threshing_machine` | 2 | 250 | _(module has no anchor)_ |
| `fud_whaling_industry` | 2 | 300 | _(module has no anchor)_ |
| `fud_winnowing_machine` | 2 | 150 | _(module has no anchor)_ |
| `fud_yeast_pure_culture` | 2 | 200 | _(module has no anchor)_ |
| `fud_can_opener` | 3 | 100 | _(module has no anchor)_ |
| `fud_margarine_synthesis` | 3 | 200 | _(module has no anchor)_ |
| `fud_mechanical_refrigeration` | 3 | 300 | _(module has no anchor)_ |
| `fud_superphosphate_fertilizer` | 3 | 200 | _(module has no anchor)_ |
| `fud_tin_plate_cans` | 3 | 200 | _(module has no anchor)_ |
| `fud_cold_chain_refrigerated_shipping` | 4 | 200 | _(module has no anchor)_ |
| `fud_combine_harvester` | 4 | 400 | _(module has no anchor)_ |
| `fud_freezing_with_mechanical_cold` | 4 | 150 | _(module has no anchor)_ |
| `fud_haber_process_synthetic_nitrogen` | 5 | 600 | _(module has no anchor)_ |

### 80_information_printing.md

| Node | Tier | Your hours | Recipe |
|---|---:|---:|---|
| `prn_carbon_ink` | 0 | 0 | _(module has no anchor)_ |
| `prn_codex_bound` | 0 | 0 | _(module has no anchor)_ |
| `prn_mosaic_fresco` | 0 | 0 | _(module has no anchor)_ |
| `prn_papyrus_sheets` | 0 | 0 | _(module has no anchor)_ |
| `prn_parchment_sheets` | 0 | 0 | _(module has no anchor)_ |
| `prn_scribal_copying` | 0 | 0 | _(module has no anchor)_ |
| `prn_sculpture` | 0 | 0 | _(module has no anchor)_ |
| `prn_seals_stamps` | 0 | 0 | _(module has no anchor)_ |
| `prn_theatre_pantomime` | 0 | 0 | _(module has no anchor)_ |
| `prn_wax_tablets` | 0 | 0 | _(module has no anchor)_ |
| `corpus_written` | 1 | 6,000 | _(module has no anchor)_ |
| `printing_press` | 1 | 900 | _(module has no anchor)_ |
| `prn_hand_papermaking` | 1 | 80 | _(module has no anchor)_ |
| `prn_magic_lantern` | 1 | 120 | _(module has no anchor)_ |
| `prn_pulp_stamper` | 1 | 100 | _(module has no anchor)_ |
| `prn_relief_printing` | 1 | 60 | _(module has no anchor)_ |
| `prn_sizing_surface` | 1 | 50 | _(module has no anchor)_ |
| `prn_wire_mould_deckle` | 1 | 150 | _(module has no anchor)_ |
| `prn_woodblock_carving` | 1 | 120 | _(module has no anchor)_ |
| `rag_paper` | 1 | 400 | _(module has no anchor)_ |
| `semaphore_telegraph` | 1 | 700 | _(module has no anchor)_ |
| `corpus_dispersed` | 2 | 800 | _(module has no anchor)_ |
| `prn_calotype_process` | 2 | 250 | _(module has no anchor)_ |
| `prn_cinema_projection` | 2 | 120 | _(module has no anchor)_ |
| `prn_cinema_shutter` | 2 | 100 | _(module has no anchor)_ |
| `prn_composing_stick` | 2 | 40 | _(module has no anchor)_ |
| `prn_daguerreotype` | 2 | 200 | _(module has no anchor)_ |
| `prn_disc_record` | 2 | 150 | _(module has no anchor)_ |
| `prn_enlarger` | 2 | 150 | _(module has no anchor)_ |
| `prn_etching_technique` | 2 | 200 | _(module has no anchor)_ |
| `prn_film_studio` | 2 | 300 | _(module has no anchor)_ |
| `prn_gelatin_dry_plate` | 2 | 150 | _(module has no anchor)_ |
| `prn_hand_mould_adjustable` | 2 | 80 | _(module has no anchor)_ |
| `prn_intaglio_engraving` | 2 | 300 | _(module has no anchor)_ |
| `prn_intermittent_motion` | 2 | 180 | _(module has no anchor)_ |
| `prn_lithography_stone` | 2 | 200 | _(module has no anchor)_ |
| `prn_loudspeaker` | 2 | 120 | _(module has no anchor)_ |
| `prn_newspaper_institution` | 2 | 400 | _(module has no anchor)_ |
| `prn_nitrate_film_safety` | 2 | 100 | _(module has no anchor)_ |
| `prn_oil_based_ink` | 2 | 100 | _(module has no anchor)_ |
| `prn_phonograph_cylinder` | 2 | 250 | _(module has no anchor)_ |
| `prn_platen_press` | 2 | 200 | _(module has no anchor)_ |
| `prn_silver_halide_chemistry` | 2 | 150 | _(module has no anchor)_ |
| `prn_stereotype_plate` | 2 | 120 | _(module has no anchor)_ |
| `prn_type_matrix` | 2 | 60 | _(module has no anchor)_ |
| `prn_type_metal_alloy` | 2 | 100 | _(module has no anchor)_ |
| `prn_type_punch` | 2 | 200 | _(module has no anchor)_ |
| `prn_wet_collodion_plate` | 2 | 200 | _(module has no anchor)_ |
| `prn_wood_pulp` | 2 | 120 | _(module has no anchor)_ |
| `prn_colour_photography` | 3 | 250 | _(module has no anchor)_ |
| `prn_cylinder_press` | 3 | 250 | _(module has no anchor)_ |
| `prn_electrical_recording` | 3 | 200 | _(module has no anchor)_ |
| `prn_electrotype_plate` | 3 | 150 | _(module has no anchor)_ |
| `prn_four_colour_separation` | 3 | 200 | _(module has no anchor)_ |
| `prn_fourdrinier_machine` | 3 | 400 | _(module has no anchor)_ |
| `prn_halftone_screen` | 3 | 150 | _(module has no anchor)_ |
| `prn_magnetic_tape_recording` | 3 | 250 | _(module has no anchor)_ |
| `prn_offset_lithography` | 3 | 250 | _(module has no anchor)_ |
| `prn_radio_broadcasting` | 3 | 300 | _(module has no anchor)_ |
| `prn_roll_film_celluloid` | 3 | 200 | _(module has no anchor)_ |
| `prn_rotary_press` | 3 | 300 | _(module has no anchor)_ |
| `prn_typewriter` | 3 | 300 | _(module has no anchor)_ |
| `prn_linotype_machine` | 4 | 600 | _(module has no anchor)_ |
| `prn_monotype_machine` | 4 | 500 | _(module has no anchor)_ |

### 85_transport_civil.md

| Node | Tier | Your hours | Recipe |
|---|---:|---:|---|
| `air_balloon_ballast` | 0 | 20 | _(module has no anchor)_ |
| `air_compass_magnetic` | 0 | 30 | _(module has no anchor)_ |
| `air_hot_air_balloon_ref` | 0 | 0 | _(module has no anchor)_ |
| `air_kite_basic` | 0 | 20 | _(module has no anchor)_ |
| `civ_amphitheatre` | 0 | 0 | _(module has no anchor)_ |
| `civ_aqueduct_roman` | 0 | 0 | _(module has no anchor)_ |
| `civ_arch_roman` | 0 | 0 | _(module has no anchor)_ |
| `civ_brick_tile` | 0 | 0 | _(module has no anchor)_ |
| `civ_chorobates` | 0 | 0 | _(module has no anchor)_ |
| `civ_cofferdam` | 0 | 0 | _(module has no anchor)_ |
| `civ_crane_treadwheel` | 0 | 0 | _(module has no anchor)_ |
| `civ_dome_roman` | 0 | 0 | _(module has no anchor)_ |
| `civ_glass_windows` | 0 | 0 | _(module has no anchor)_ |
| `civ_insula` | 0 | 0 | _(module has no anchor)_ |
| `civ_iron_wrought` | 0 | 0 | _(module has no anchor)_ |
| `civ_marble_facing` | 0 | 0 | _(module has no anchor)_ |
| `civ_road_paved` | 0 | 0 | _(module has no anchor)_ |
| `civ_sewer_roman` | 0 | 0 | _(module has no anchor)_ |
| `civ_surveying_groma` | 0 | 0 | _(module has no anchor)_ |
| `civ_vault_barrel` | 0 | 0 | _(module has no anchor)_ |
| `lnd_axle_pivot_front` | 0 | 0 | _(module has no anchor)_ |
| `lnd_bridge` | 0 | 0 | _(module has no anchor)_ |
| `lnd_cursus_publicus` | 0 | 0 | _(module has no anchor)_ |
| `lnd_four_wheel_cart` | 0 | 0 | _(module has no anchor)_ |
| `lnd_harness_throat_girth` | 0 | 0 | _(module has no anchor)_ |
| `lnd_horse_saddle_basic` | 0 | 0 | _(module has no anchor)_ |
| `lnd_litter` | 0 | 0 | _(module has no anchor)_ |
| `lnd_milestone` | 0 | 0 | _(module has no anchor)_ |
| `lnd_mule_transport` | 0 | 0 | _(module has no anchor)_ |
| `lnd_ox_transport` | 0 | 0 | _(module has no anchor)_ |
| `lnd_paved_road_network` | 0 | 0 | _(module has no anchor)_ |
| `lnd_two_wheel_cart` | 0 | 0 | _(module has no anchor)_ |
| `lnd_tyre_iron` | 0 | 0 | _(module has no anchor)_ |
| `lnd_wheel_spoked` | 0 | 0 | _(module has no anchor)_ |
| `sea_anchor` | 0 | 0 | _(module has no anchor)_ |
| `sea_coastal_pilotage` | 0 | 0 | _(module has no anchor)_ |
| `sea_harbours_pozzolana` | 0 | 0 | _(module has no anchor)_ |
| `sea_lead_sheathing` | 0 | 0 | _(module has no anchor)_ |
| `sea_merchant_ships_large` | 0 | 0 | _(module has no anchor)_ |
| `sea_monsoon_route` | 0 | 0 | _(module has no anchor)_ |
| `sea_mortise_tenon` | 0 | 0 | _(module has no anchor)_ |
| `sea_pharos_lighthouse` | 0 | 0 | _(module has no anchor)_ |
| `sea_sounding_lines` | 0 | 0 | _(module has no anchor)_ |
| `sea_spritsail` | 0 | 0 | _(module has no anchor)_ |
| `sea_square_sail` | 0 | 0 | _(module has no anchor)_ |
| `sea_steering_oars` | 0 | 0 | _(module has no anchor)_ |
| `air_balloon_valve` | 1 | 60 | _(module has no anchor)_ |
| `air_elevator_pitch` | 1 | 50 | _(module has no anchor)_ |
| `air_goldbeater_skin` | 1 | 200 | _(module has no anchor)_ |
| `air_observation_balloon_tethered` | 1 | 120 | _(module has no anchor)_ |
| `air_pitot_tube` | 1 | 50 | _(module has no anchor)_ |
| `air_rudder_vertical` | 1 | 60 | _(module has no anchor)_ |
| `air_varnished_silk_envelope` | 1 | 150 | _(module has no anchor)_ |
| `civ_bridge_timber_truss` | 1 | 200 | _(module has no anchor)_ |
| `civ_foundation_piles` | 1 | 100 | _(module has no anchor)_ |
| `civ_foundation_spread` | 1 | 80 | _(module has no anchor)_ |
| `civ_gate_sluice` | 1 | 100 | _(module has no anchor)_ |
| `civ_roof_king_post` | 1 | 80 | _(module has no anchor)_ |
| `civ_roof_queen_post` | 1 | 100 | _(module has no anchor)_ |
| `civ_street_paved` | 1 | 80 | _(module has no anchor)_ |
| `civ_truss_triangulated` | 1 | 120 | _(module has no anchor)_ |
| `civ_water_tower` | 1 | 100 | _(module has no anchor)_ |
| `civ_wire_drawn` | 1 | 100 | _(module has no anchor)_ |
| `lnd_coach` | 1 | 200 | _(module has no anchor)_ |
| `lnd_hobby_horse` | 1 | 40 | _(module has no anchor)_ |
| `lnd_horseshoe_nailed` | 1 | 40 | _(module has no anchor)_ |
| `lnd_spring_leaf` | 1 | 80 | _(module has no anchor)_ |
| `lnd_stirrup` | 1 | 60 | _(module has no anchor)_ |
| `lnd_wheelbarrow` | 1 | 30 | _(module has no anchor)_ |
| `lnd_whippletree` | 1 | 50 | _(module has no anchor)_ |
| `sea_bowsprit` | 1 | 60 | _(module has no anchor)_ |
| `sea_carvel_planking` | 1 | 200 | _(module has no anchor)_ |
| `sea_clinker_planking` | 1 | 100 | _(module has no anchor)_ |
| `sea_dry_compass_card` | 1 | 60 | _(module has no anchor)_ |
| `sea_fore_aft_rig` | 1 | 100 | _(module has no anchor)_ |
| `sea_jib` | 1 | 40 | _(module has no anchor)_ |
| `sea_lateen_sail` | 1 | 80 | _(module has no anchor)_ |
| `sea_lodestone` | 1 | 20 | _(module has no anchor)_ |
| `sea_log_line` | 1 | 30 | _(module has no anchor)_ |
| `sea_multiple_masts` | 1 | 150 | _(module has no anchor)_ |
| `sea_skeleton_first` | 1 | 250 | _(module has no anchor)_ |
| `sea_sternpost_rudder` | 1 | 120 | _(module has no anchor)_ |
| `sea_traverse_board` | 1 | 40 | _(module has no anchor)_ |
| `air_aerial_photography` | 2 | 120 | _(module has no anchor)_ |
| `air_aerial_reconnaissance` | 2 | 100 | _(module has no anchor)_ |
| `air_aerodrome` | 2 | 100 | _(module has no anchor)_ |
| `air_aerofoil_section` | 2 | 200 | _(module has no anchor)_ |
| `air_aileron` | 2 | 140 | _(module has no anchor)_ |
| `air_airspeed_indicator` | 2 | 100 | _(module has no anchor)_ |
| `air_altimeter` | 2 | 120 | _(module has no anchor)_ |
| `air_biplane` | 2 | 140 | _(module has no anchor)_ |
| `air_cayley_forces` | 2 | 250 | _(module has no anchor)_ |
| `air_elongated_envelope` | 2 | 120 | _(module has no anchor)_ |
| `air_glider_simple` | 2 | 160 | _(module has no anchor)_ |
| `air_hydrogen_generation_charcoal` | 2 | 100 | _(module has no anchor)_ |
| `air_parachute` | 2 | 80 | _(module has no anchor)_ |
| `air_propeller_wing` | 2 | 180 | _(module has no anchor)_ |
| `air_three_axis_control` | 2 | 200 | _(module has no anchor)_ |
| `air_wind_tunnel` | 2 | 150 | _(module has no anchor)_ |
| `air_wing_warping` | 2 | 120 | _(module has no anchor)_ |
| `civ_bridge_cast_iron` | 2 | 150 | _(module has no anchor)_ |
| `civ_bridge_wrought_iron_truss` | 2 | 200 | _(module has no anchor)_ |
| `civ_caisson` | 2 | 150 | _(module has no anchor)_ |
| `civ_canal_pound_lock` | 2 | 150 | _(module has no anchor)_ |
| `civ_dam_earth_fill` | 2 | 150 | _(module has no anchor)_ |
| `civ_dam_gravity` | 2 | 200 | _(module has no anchor)_ |
| `civ_dredging` | 2 | 120 | _(module has no anchor)_ |
| `civ_harbour_dock` | 2 | 200 | _(module has no anchor)_ |
| `civ_lightning_conductor` | 2 | 80 | _(module has no anchor)_ |
| `civ_precise_levelling` | 2 | 120 | _(module has no anchor)_ |
| `civ_pumping_station` | 2 | 150 | _(module has no anchor)_ |
| `civ_sewer_separate` | 2 | 120 | _(module has no anchor)_ |
| `civ_spillway` | 2 | 150 | _(module has no anchor)_ |
| `civ_theodolite` | 2 | 150 | _(module has no anchor)_ |
| `civ_town_planning` | 2 | 180 | _(module has no anchor)_ |
| `civ_tunnel_rock_drill` | 2 | 180 | _(module has no anchor)_ |
| `hot_air_balloon` | 2 | 400 | _(module has no anchor)_ |
| `lnd_ball_bearing` | 2 | 80 | _(module has no anchor)_ |
| `lnd_boneshaker` | 2 | 80 | _(module has no anchor)_ |
| `lnd_chain_drive_bicycle` | 2 | 100 | _(module has no anchor)_ |
| `lnd_coal_tar_gas` | 2 | 80 | _(module has no anchor)_ |
| `lnd_fishplate` | 2 | 50 | _(module has no anchor)_ |
| `lnd_flanged_wheel` | 2 | 80 | _(module has no anchor)_ |
| `lnd_gas_engine_atmospheric` | 2 | 250 | _(module has no anchor)_ |
| `lnd_iron_edge_rail` | 2 | 60 | _(module has no anchor)_ |
| `lnd_macadam` | 2 | 80 | _(module has no anchor)_ |
| `lnd_penny_farthing` | 2 | 100 | _(module has no anchor)_ |
| `lnd_point_switch` | 2 | 120 | _(module has no anchor)_ |
| `lnd_signal_railway` | 2 | 80 | _(module has no anchor)_ |
| `lnd_stagecoach` | 2 | 250 | _(module has no anchor)_ |
| `lnd_turnpike` | 2 | 50 | _(module has no anchor)_ |
| `sea_astronomical_tables` | 2 | 400 | _(module has no anchor)_ |
| `sea_backstaff` | 2 | 100 | _(module has no anchor)_ |
| `sea_buoy` | 2 | 60 | _(module has no anchor)_ |
| `sea_charts_navigation` | 2 | 200 | _(module has no anchor)_ |
| `sea_cross_staff` | 2 | 80 | _(module has no anchor)_ |
| `sea_diving_bell` | 2 | 120 | _(module has no anchor)_ |
| `sea_drydock` | 2 | 300 | _(module has no anchor)_ |
| `sea_lead_line_hydro` | 2 | 120 | _(module has no anchor)_ |
| `sea_magnetic_compass` | 2 | 80 | _(module has no anchor)_ |
| `sea_mercator_projection` | 2 | 180 | _(module has no anchor)_ |
| `sea_sextant` | 2 | 150 | _(module has no anchor)_ |
| `air_aerial_bombing` | 3 | 150 | _(module has no anchor)_ |
| `air_autogyro` | 3 | 200 | _(module has no anchor)_ |
| `air_coal_gas_generation` | 3 | 180 | _(module has no anchor)_ |
| `air_dirigible_engine_mount` | 3 | 200 | _(module has no anchor)_ |
| `air_flying_boat` | 3 | 220 | _(module has no anchor)_ |
| `air_hydrogen_danger` | 3 | 100 | _(module has no anchor)_ |
| `air_light_petrol_engine` | 3 | 250 | _(module has no anchor)_ |
| `air_power_to_weight` | 3 | 150 | _(module has no anchor)_ |
| `air_powered_aeroplane` | 3 | 300 | _(module has no anchor)_ |
| `air_radial_engine` | 3 | 200 | _(module has no anchor)_ |
| `air_rotary_engine` | 3 | 220 | _(module has no anchor)_ |
| `civ_bridge_suspension` | 3 | 300 | _(module has no anchor)_ |
| `civ_building_code` | 3 | 200 | _(module has no anchor)_ |
| `civ_caisson_compressed_air` | 3 | 200 | _(module has no anchor)_ |
| `civ_dam_arch` | 3 | 250 | _(module has no anchor)_ |
| `civ_elevator_otis` | 3 | 250 | _(module has no anchor)_ |
| `civ_fireproofing` | 3 | 150 | _(module has no anchor)_ |
| `civ_glass_plate` | 3 | 100 | _(module has no anchor)_ |
| `civ_tunnel_shield` | 3 | 250 | _(module has no anchor)_ |
| `civ_water_treatment` | 3 | 200 | _(module has no anchor)_ |
| `lnd_air_brake` | 3 | 250 | _(module has no anchor)_ |
| `lnd_block_system` | 3 | 150 | _(module has no anchor)_ |
| `lnd_carburettor` | 3 | 120 | _(module has no anchor)_ |
| `lnd_caterpillar_track` | 3 | 200 | _(module has no anchor)_ |
| `lnd_differential` | 3 | 150 | _(module has no anchor)_ |
| `lnd_gearbox_clutch` | 3 | 200 | _(module has no anchor)_ |
| `lnd_magneto` | 3 | 150 | _(module has no anchor)_ |
| `lnd_otto_cycle_four_stroke` | 3 | 350 | _(module has no anchor)_ |
| `lnd_safety_bicycle` | 3 | 120 | _(module has no anchor)_ |
| `lnd_spark_plug` | 3 | 100 | _(module has no anchor)_ |
| `lnd_standard_gauge` | 3 | 200 | _(module has no anchor)_ |
| `lnd_steam_locomotive` | 3 | 400 | _(module has no anchor)_ |
| `lnd_steering_geometry` | 3 | 100 | _(module has no anchor)_ |
| `lnd_superheater` | 3 | 200 | _(module has no anchor)_ |
| `lnd_tarmacadam` | 3 | 100 | _(module has no anchor)_ |
| `lnd_tender` | 3 | 120 | _(module has no anchor)_ |
| `sea_canal_lock` | 3 | 250 | _(module has no anchor)_ |
| `sea_compartmented_hull` | 3 | 150 | _(module has no anchor)_ |
| `sea_copper_sheathing` | 3 | 180 | _(module has no anchor)_ |
| `sea_diving_suit` | 3 | 180 | _(module has no anchor)_ |
| `sea_dredging` | 3 | 200 | _(module has no anchor)_ |
| `sea_iron_hull` | 3 | 250 | _(module has no anchor)_ |
| `sea_lifeboat` | 3 | 100 | _(module has no anchor)_ |
| `sea_lunar_distances` | 3 | 200 | _(module has no anchor)_ |
| `sea_marine_chronometer` | 3 | 250 | _(module has no anchor)_ |
| `sea_paddle_wheel` | 3 | 200 | _(module has no anchor)_ |
| `sea_screw_propeller` | 3 | 220 | _(module has no anchor)_ |
| `air_artificial_horizon` | 4 | 250 | _(module has no anchor)_ |
| `air_helicopter_rotor` | 4 | 280 | _(module has no anchor)_ |
| `air_jet_engine_concept` | 4 | 200 | _(module has no anchor)_ |
| `air_monoplane_structure` | 4 | 200 | _(module has no anchor)_ |
| `air_rigid_airship_frame` | 4 | 300 | _(module has no anchor)_ |
| `air_stressed_skin_fuselage` | 4 | 180 | _(module has no anchor)_ |
| `civ_box_girder` | 4 | 120 | _(module has no anchor)_ |
| `civ_bridge_cantilever` | 4 | 250 | _(module has no anchor)_ |
| `civ_bridge_steel_arch` | 4 | 250 | _(module has no anchor)_ |
| `civ_curtain_wall` | 4 | 150 | _(module has no anchor)_ |
| `civ_prestressed_concrete` | 4 | 180 | _(module has no anchor)_ |
| `civ_reinforced_concrete` | 4 | 200 | _(module has no anchor)_ |
| `civ_sewage_treatment` | 4 | 200 | _(module has no anchor)_ |
| `civ_steel_frame` | 4 | 300 | _(module has no anchor)_ |
| `civ_street_lighting` | 4 | 120 | _(module has no anchor)_ |
| `lnd_assembly_line` | 4 | 600 | _(module has no anchor)_ |
| `lnd_automobile` | 4 | 500 | _(module has no anchor)_ |
| `lnd_diesel_cycle` | 4 | 400 | _(module has no anchor)_ |
| `lnd_diesel_supply` | 4 | 180 | _(module has no anchor)_ |
| `lnd_omnibus` | 4 | 250 | _(module has no anchor)_ |
| `lnd_pneumatic_tyre` | 4 | 120 | _(module has no anchor)_ |
| `lnd_tractor` | 4 | 350 | _(module has no anchor)_ |
| `lnd_truck` | 4 | 300 | _(module has no anchor)_ |
| `railway` | 4 | 800 | _(module has no anchor)_ |
| `sea_boiler_water_tube` | 4 | 200 | _(module has no anchor)_ |
| `sea_compound_expansion` | 4 | 300 | _(module has no anchor)_ |
| `sea_diesel_engine` | 4 | 250 | _(module has no anchor)_ |
| `sea_electromagnetic_wave_theory` | 4 | 200 | _(module has no anchor)_ |
| `sea_fresnel_lens` | 4 | 180 | _(module has no anchor)_ |
| `sea_fuel_oil_burner` | 4 | 140 | _(module has no anchor)_ |
| `sea_steam_turbine` | 4 | 280 | _(module has no anchor)_ |
| `sea_steel_hull` | 4 | 200 | _(module has no anchor)_ |
| `sea_submarine` | 4 | 300 | _(module has no anchor)_ |
| `sea_submarine_cable` | 4 | 200 | _(module has no anchor)_ |
| `sea_torpedo` | 4 | 180 | _(module has no anchor)_ |
| `air_jet_engine_build` | 5 | 350 | _(module has no anchor)_ |
| `lnd_motor_road_network` | 5 | 250 | _(module has no anchor)_ |
| `sea_sonar` | 5 | 250 | _(module has no anchor)_ |

## Broken links

- `cap_gas_o2h2` points at ``, which does not exist
- `cap_heat_0700` points at ``, which does not exist
- `cap_heat_1100` points at ``, which does not exist
- `cap_heat_1300` points at ``, which does not exist
- `cap_heat_1600` points at ``, which does not exist
- `cap_heat_2000` points at ``, which does not exist
- `cap_heat_3000` points at ``, which does not exist
- `cap_measure_elec` points at ``, which does not exist
- `cap_measure_len` points at ``, which does not exist
- `cap_measure_light` points at ``, which does not exist
- `cap_measure_mass_mg` points at ``, which does not exist
- `cap_measure_temp` points at ``, which does not exist
- `cap_measure_temp_hi` points at ``, which does not exist
- `cap_measure_time_ms` points at ``, which does not exist
- `cap_measure_time_s` points at ``, which does not exist
- `cap_power_electric` points at ``, which does not exist
- `cap_power_grid` points at ``, which does not exist
- `cap_power_muscle` points at ``, which does not exist
- `cap_power_steam` points at ``, which does not exist
- `cap_power_water` points at ``, which does not exist
- `cap_pure_2N` points at ``, which does not exist
- `cap_pure_4N` points at ``, which does not exist
- `cap_pure_6N` points at ``, which does not exist
- `cap_pure_9N` points at ``, which does not exist
- `cap_tol_100nm` points at ``, which does not exist
- `cap_tol_100um` points at ``, which does not exist
- `cap_tol_10um` points at ``, which does not exist
- `cap_tol_1mm` points at ``, which does not exist
- `cap_tol_1um` points at ``, which does not exist
- `cap_vac_1e3` points at ``, which does not exist
- `cap_vac_1e6` points at ``, which does not exist
- `cap_vac_1e9` points at ``, which does not exist
- `cap_vac_1torr` points at ``, which does not exist
- `chm_activated_carbon` points at `Activation of charcoal by steam or acid washing to create high surface area adsorbent`, which does not exist
- `chm_alizarin` points at `Oxidation of anthraquinone to alizarin, a red dye replacing madder root`, which does not exist
- `chm_alkali_waste` points at `Recognition that Leblanc produces enormous volumes of CaS and CaSO4 waste requiring regulation`, which does not exist
- `chm_ammonia_recovery` points at `Distillation column to recover NH3 from mother liquor and recycle to ammonia absorber`, which does not exist
- `chm_aniline` points at `Nitration of benzene to nitrobenzene, then reduction with iron and acid`, which does not exist
- `chm_anthracene` points at `Distillation of coal tar above 280 C and crystallisation to yield anthracene`, which does not exist
- `chm_aspirin` points at `Acetylation of salicylic acid with acetic anhydride to give acetylsalicylic acid`, which does not exist
- `chm_azo_dyes` points at `Conversion of aniline to diazonium salts, then coupling with phenols or naphthols`, which does not exist
- `chm_bakelite` points at `Polycondensation of phenol with formaldehyde under heat and pressure in a mould`, which does not exist
- `chm_benzene` points at `Fractional distillation of coal tar to isolate pure benzene`, which does not exist
- `chm_black_powder` points at `Mixture of saltpetre, charcoal and sulfur, corned for stability`, which does not exist
- `chm_blasting_cap` points at `Sealed copper tube containing mercury or lead fulminate to initiate high explosives`, which does not exist
- `chm_bleaching_powder` points at `Absorption of chlorine gas into dry slaked lime to make stable powder`, which does not exist
- `chm_casein` points at `Precipitation of casein from milk, hardening with formaldehyde to yield hard plastic`, which does not exist
- `chm_catalyst_concept` points at `Catalysis speeds reaction by lowering activation energy without being consumed itself`, which does not exist
- `chm_caustic_soda` points at `Concentration of dilute NaOH solution to 50% by evaporation under vacuum`, which does not exist
- `chm_celluloid` points at `Plasticisation of nitrocellulose with camphor to yield flexible thermoplastic sheet`, which does not exist
- `chm_centrifuge` points at `Rotating cylinder to separate solids from liquids by density, with scroll discharge`, which does not exist
- `chm_chlor_alkali_diaphragm` points at `Electrolysis of brine with asbestos cloth diaphragm separating anode and cathode`, which does not exist
- `chm_chlor_alkali_mercury` points at `Electrolysis of brine with liquid mercury cathode to produce Cl2 gas and NaOH solution`, which does not exist
- `chm_chromatography` points at `Separation of mixtures by differential adsorption on a stationary phase`, which does not exist
- `chm_coal_tar_distillation` points at `Separation of coal tar into volatile fractions: benzene, toluene, naphthalene, anthracene`, which does not exist
- `chm_contact_sulfuric` points at `Catalytic oxidation of SO2 to SO3 across heated platinum at high purity`, which does not exist
- `chm_contact_vanadium` points at `V2O5 on silica support as cheaper alternative to platinum`, which does not exist
- `chm_continuous_batch` points at `Design choice between continuous reactors and batch kettles based on production rate and product lifetime`, which does not exist
- `chm_corrosion_glass_lined` points at `Fused glass coating on steel for acid resistance and thermal shock resistance`, which does not exist
- `chm_corrosion_lead` points at `Lined vessels of lead sheet to contain sulfuric acid and chlorine`, which does not exist
- `chm_corrosion_stainless` points at `Chromium-nickel stainless steel resistant to most chemicals and oxidising acids`, which does not exist
- `chm_corrosion_stoneware` points at `High-fired stoneware vessels glazed with acid-resistant glaze for chemical storage`, which does not exist
- `chm_crystallisation` points at `Cooling of saturated solution to grow crystals, which are filtered and dried`, which does not exist
- `chm_cyanamide_fixation` points at `Production of calcium carbide, then reaction with nitrogen gas to make cyanamide`, which does not exist
- `chm_deacon_process` points at `Gas-phase oxidation of HCl with air over hot copper chloride catalyst`, which does not exist
- `chm_detergent_synthetic` points at `Sulfonation of long-chain alkene to yield sulfonic acid, then neutralisation to salt`, which does not exist
- `chm_dynamite` points at `Adsorption of liquid nitroglycerin onto porous diatomaceous earth for safe transport and storage`, which does not exist
- `chm_electric_arc_nitrogen` points at `High-temperature arc oxidises nitrogen in air to nitric oxide, absorbed to yield nitric acid`, which does not exist
- `chm_electroplating` points at `Electrodeposition of metal ions onto a cathode to coat an object`, which does not exist
- `chm_evaporator_surface` points at `Heated tube bundle in liquid to evaporate solvent slowly while concentrating dissolved salts`, which does not exist
- `chm_filter_press` points at `Packed plates with cloth or paper filter medium under mechanical pressure`, which does not exist
- `chm_formaldehyde_synthesis` points at `Catalytic oxidation of methanol vapour over silver or copper catalyst`, which does not exist
- `chm_fractionating_column` points at `Vertical column with bubble-cap trays to separate liquids by boiling point`, which does not exist
- `chm_fulminate` points at `Reaction of mercury with dilute nitric acid and ethanol to yield mercury fulminate`, which does not exist
- `chm_gelignite` points at `Stabilisation of nitroglycerin by absorbing into gelatinised nitrocellulose`, which does not exist
- `chm_glycerol` points at `Recovery of glycerol from saponification of oils and fats`, which does not exist
- `chm_guncotton` points at `Cellulose nitrated with mixed acid to yield highly explosive nitrocellulose`, which does not exist
- `chm_haber_bosch` points at `Synthesis of NH3 from N2 and H2 at 200 atm and 500 C over iron catalyst`, which does not exist
- `chm_indigo_synthesis` points at `Fusion of indole intermediate to yield indigo; fusion with molten NaOH at 180 C`, which does not exist
- `chm_industrial_hygiene` points at `Recognition of specific occupational poisons: phosphorus necrosis, mercury, lead, benzene, chlorine gas`, which does not exist
- `chm_ion_exchange` points at `Synthetic resin beads with exchangeable ions to remove hardness and trace metals`, which does not exist
- `chm_matches` points at `Wooden sticks coated with red phosphorus, antimony sulfide and potassium dichromate`, which does not exist
- `chm_naphthalene` points at `Distillation of coal tar above 250 C to obtain naphthalene; crystallisation and recrystallisation`, which does not exist
- `chm_nitroglycerin` points at `Nitration of glycerol to yield highly sensitive volatile liquid explosive`, which does not exist
- `chm_nylon` points at `Polycondensation of adipic acid with hexamethylenediamine to yield nylon fibre`, which does not exist
- `chm_oleum` points at `Concentration of sulfuric acid by absorption of SO3 into 100% H2SO4`, which does not exist
- `chm_ostwald_ammonia_oxidation` points at `Catalytic oxidation of gaseous ammonia with air over hot platinum gauze`, which does not exist
- `chm_phenol` points at `Distillation of coal tar yields crude phenol; direct synthesis via benzene sulfonation`, which does not exist
- `chm_phosphorus_extraction` points at `Roasting of bone ash with carbon in retort at 1300 C, collecting phosphorus vapour on water`, which does not exist
- `chm_photography` points at `Sensitisation of silver halide emulsions and development chemistry for silver images`, which does not exist
- `chm_picric_acid` points at `Nitration of phenol to yield picric acid (trinitrophenol)`, which does not exist
- `chm_polyethylene` points at `Polymerisation of ethylene at 1000 atm and 150 C with organic peroxide initiator`, which does not exist
- `chm_potash_mining` points at `Extraction of naturally-occurring potassium salt deposits`, which does not exist
- `chm_pressure_gauge` points at `Spring-loaded metal tube to measure and limit pressure safely`, which does not exist
- `chm_pressure_vessel` points at `Containment of reaction at elevated temperature and pressure using riveted iron`, which does not exist
- `chm_pvc_synthesis` points at `Polymerisation of vinyl chloride monomer under free-radical initiation`, which does not exist
- `chm_refrigerant_ammonia` points at `Use of ammonia as working fluid in mechanical refrigeration compression cycles`, which does not exist
- `chm_saccharin` points at `Sulfonation then oxidation of methylbenzene to benzosulfimide`, which does not exist
- `chm_salicylic_acid` points at `Sulfonation and alkali fusion to convert benzenesulfonic acid to phenol`, which does not exist
- `chm_smokeless_powder` points at `Stabilised nitrocellulose grains for ballistic use, stable for decades`, which does not exist
- `chm_soap_hard` points at `Saponification of tallow or vegetable oil with caustic soda and salt precipitation`, which does not exist
- `chm_solvay_process` points at `Absorbing ammonia in brine, then carbonating to precipitate sodium bicarbonate`, which does not exist
- `chm_sulfonamides` points at `Sulfonation of aniline derivatives followed by amidation to yield sulfonamides`, which does not exist
- `chm_superphosphate` points at `Treatment of rock phosphate with sulfuric acid to make soluble phosphate fertiliser`, which does not exist
- `chm_tnt` points at `Nitration of toluene in three stages to yield trinitrotoluene`, which does not exist
- `chm_toluene` points at `Fractional distillation of coal tar to isolate methylbenzene`, which does not exist
- `chm_water_chlorination` points at `Addition of chlorine gas or bleaching powder to water to kill pathogens`, which does not exist
- `chm_water_coagulation` points at `Use of aluminum sulfate or ferric salts to destabilise colloids and settle suspended solids`, which does not exist
- `chm_water_filtration` points at `Passage of coagulated water through layers of sand and gravel to remove particles`, which does not exist
- `chm_weldon_process` points at `Oxidation of MnCl2 with bleach to regenerate MnO2, closing the chlorine cycle`, which does not exist
- `civ_bending_moment` points at ``, which does not exist
- `civ_elasticity_theory` points at ``, which does not exist
- `civ_euler_buckling` points at ``, which does not exist
- `civ_factor_safety` points at ``, which does not exist
- `civ_materials_testing` points at ``, which does not exist
- `civ_method_joints` points at ``, which does not exist
- `civ_neutral_axis` points at ``, which does not exist
- `civ_soil_mechanics` points at ``, which does not exist
- `civ_statics` points at ``, which does not exist
- `fud_agricultural_treatises` points at ``, which does not exist
- `fud_chocolate_tier9` points at ``, which does not exist
- `fud_maize_tier9` points at ``, which does not exist
- `fud_potato_tier9` points at ``, which does not exist
- `fud_soil_composition_analysis` points at ``, which does not exist
- `hom_attar_roses` points at ``, which does not exist
- `hom_bath_piped_hot_water` points at ``, which does not exist
- `hom_board_games` points at ``, which does not exist
- `hom_button` points at ``, which does not exist
- `hom_candle_beeswax` points at ``, which does not exist
- `hom_candle_tallow` points at ``, which does not exist
- `hom_carpet_sweeper` points at ``, which does not exist
- `hom_cosmetics_modern_warning` points at ``, which does not exist
- `hom_cosmetics_roman` points at ``, which does not exist
- `hom_deodorant` points at ``, which does not exist
- `hom_dishwasher` points at ``, which does not exist
- `hom_doll_fashion` points at ``, which does not exist
- `hom_double_glazing` points at ``, which does not exist
- `hom_electric_fan` points at ``, which does not exist
- `hom_electric_lighting` points at ``, which does not exist
- `hom_eraser_breadcrumb` points at ``, which does not exist
- `hom_fireplace_chimney` points at ``, which does not exist
- `hom_flush_latrine_simple` points at ``, which does not exist
- `hom_flush_toilet_trap` points at ``, which does not exist
- `hom_fountain_pen` points at ``, which does not exist
- `hom_furniture_wooden` points at ``, which does not exist
- `hom_gas_lamp` points at ``, which does not exist
- `hom_glass_windows` points at ``, which does not exist
- `hom_heating_hot_water_radiator` points at ``, which does not exist
- `hom_hypocaust` points at ``, which does not exist
- `hom_jigsaw_puzzle` points at ``, which does not exist
- `hom_kitchen_range` points at ``, which does not exist
- `hom_lamp_argand` points at ``, which does not exist
- `hom_lamp_kerosene` points at ``, which does not exist
- `hom_latrine_water_trap` points at ``, which does not exist
- `hom_lead_plumbing` points at ``, which does not exist
- `hom_locks_keys` points at ``, which does not exist
- `hom_mangle_wringer` points at ``, which does not exist
- `hom_matches_friction` points at ``, which does not exist
- `hom_mechanical_clock_home` points at ``, which does not exist
- `hom_metronome` points at ``, which does not exist
- `hom_mirror_bronze_polished` points at ``, which does not exist
- `hom_mirror_silvered_glass` points at ``, which does not exist
- `hom_musical_instruments` points at ``, which does not exist
- `hom_oil_lamp_simple` points at ``, which does not exist
- `hom_pencil` points at ``, which does not exist
- `hom_perfume_distilled` points at ``, which does not exist
- `hom_perfume_enfleurage` points at ``, which does not exist
- `hom_piano` points at ``, which does not exist
- `hom_playing_cards_printed` points at ``, which does not exist
- `hom_pocket_watch` points at ``, which does not exist
- `hom_pressure_cooker` points at ``, which does not exist
- `hom_printed_books` points at ``, which does not exist
- `hom_public_bath` points at ``, which does not exist
- `hom_punkah_ceiling` points at ``, which does not exist
- `hom_refrigeration_mechanical` points at ``, which does not exist
- `hom_refrigerator_home_electric` points at ``, which does not exist
- `hom_safety_pin` points at ``, which does not exist
- `hom_safety_razor` points at ``, which does not exist
- `hom_sewer_stormwater_separation` points at ``, which does not exist
- `hom_sewing_machine_hand` points at ``, which does not exist
- `hom_shampoo_soap_based` points at ``, which does not exist
- `hom_soap_hard` points at ``, which does not exist
- `hom_spectacles` points at ``, which does not exist
- `hom_sprung_mattress` points at ``, which does not exist
- `hom_stove_enclosed` points at ``, which does not exist
- `hom_toothbrush` points at ``, which does not exist
- `hom_toothpaste_commercial` points at ``, which does not exist
- `hom_toys_dolls` points at ``, which does not exist
- `hom_umbrella` points at ``, which does not exist
- `hom_vacuum_cleaner` points at ``, which does not exist
- `hom_vacuum_flask` points at ``, which does not exist
- `hom_washing_machine_electric` points at ``, which does not exist
- `hom_washing_machine_hand` points at ``, which does not exist
- `hom_zip_fastener` points at ``, which does not exist
- `mat_alum` points at ``, which does not exist
- `mat_aluminium` points at ``, which does not exist
- `mat_ammonia` points at ``, which does not exist
- `mat_asbestos` points at ``, which does not exist
- `mat_bakelite` points at ``, which does not exist
- `mat_beeswax` points at ``, which does not exist
- `mat_bitumen` points at ``, which does not exist
- `mat_blister_steel` points at ``, which does not exist
- `mat_brass` points at ``, which does not exist
- `mat_bronze` points at ``, which does not exist
- `mat_bulk_steel` points at ``, which does not exist
- `mat_calamine` points at ``, which does not exist
- `mat_camphor` points at ``, which does not exist
- `mat_carbon_black` points at ``, which does not exist
- `mat_cast_iron` points at ``, which does not exist
- `mat_celluloid` points at ``, which does not exist
- `mat_cement_portland` points at ``, which does not exist
- `mat_charcoal` points at ``, which does not exist
- `mat_chile_nitrate` points at ``, which does not exist
- `mat_chlorine` points at ``, which does not exist
- `mat_chromium` points at ``, which does not exist
- `mat_concrete_reinforced` points at ``, which does not exist
- `mat_copper` points at ``, which does not exist
- `mat_crucible_steel` points at ``, which does not exist
- `mat_cryolite` points at ``, which does not exist
- `mat_dyes_synthetic` points at ``, which does not exist
- `mat_emery` points at ``, which does not exist
- `mat_formaldehyde` points at ``, which does not exist
- `mat_fused_quartz` points at ``, which does not exist
- `mat_galena` points at ``, which does not exist
- `mat_glass_boro` points at ``, which does not exist
- `mat_glass_lead` points at ``, which does not exist
- `mat_glass_soda` points at ``, which does not exist
- `mat_glycerol` points at ``, which does not exist
- `mat_gold` points at ``, which does not exist
- `mat_graphite_pure` points at ``, which does not exist
- `mat_gutta_percha` points at ``, which does not exist
- `mat_gypsum` points at ``, which does not exist
- `mat_ice_artificial` points at ``, which does not exist
- `mat_lead` points at ``, which does not exist
- `mat_leather` points at ``, which does not exist
- `mat_lime` points at ``, which does not exist
- `mat_linen` points at ``, which does not exist
- `mat_magnesium` points at ``, which does not exist
- `mat_manganese` points at ``, which does not exist
- `mat_mercury` points at ``, which does not exist
- `mat_natron` points at ``, which does not exist
- `mat_natural_rubber` points at ``, which does not exist
- `mat_newworld_crops` points at ``, which does not exist
- `mat_nickel` points at ``, which does not exist
- `mat_nitrocellulose` points at ``, which does not exist
- `mat_nitroglycerin` points at ``, which does not exist
- `mat_olive_oil` points at ``, which does not exist
- `mat_paper` points at ``, which does not exist
- `mat_papyrus` points at ``, which does not exist
- `mat_parchment` points at ``, which does not exist
- `mat_petroleum_refined` points at ``, which does not exist
- `mat_platinum_bulk` points at ``, which does not exist
- `mat_porcelain` points at ``, which does not exist
- `mat_pozzolana` points at ``, which does not exist
- `mat_pyrolusite` points at ``, which does not exist
- `mat_quinine` points at ``, which does not exist
- `mat_salt` points at ``, which does not exist
- `mat_shellac` points at ``, which does not exist
- `mat_silk` points at ``, which does not exist
- `mat_silver` points at ``, which does not exist
- `mat_stainless` points at ``, which does not exist
- `mat_sulfur` points at ``, which does not exist
- `mat_synthetic_rubber` points at ``, which does not exist
- `mat_tallow` points at ``, which does not exist
- `mat_tin` points at ``, which does not exist
- `mat_tool_steel_hss` points at ``, which does not exist
- `mat_tungsten` points at ``, which does not exist
- `mat_vitriols` points at ``, which does not exist
- `mat_wool` points at ``, which does not exist
- `mat_wrought_iron` points at ``, which does not exist
- `mat_zinc` points at ``, which does not exist
- `med_cocaine_unobtainable` points at ``, which does not exist
- `met_fatigue_testing` points at ``, which does not exist
- `met_hardness_test` points at ``, which does not exist
- `met_mannesmann_piercing` points at ``, which does not exist
- `met_metallography` points at ``, which does not exist
- `met_phase_diagram_knowledge` points at ``, which does not exist
- `met_spectroscopic_assay` points at ``, which does not exist
- `met_tensile_test` points at ``, which does not exist
- `prc_apprentice_system` points at ``, which does not exist
- `prc_toolroom_institution` points at ``, which does not exist
- `prn_cataloguing_system` points at ``, which does not exist
- `prn_copyright_economics` points at ``, which does not exist
- `prn_index_concordance` points at ``, which does not exist
- `prn_library_archive` points at ``, which does not exist
- `tex_buttons_buttonholes` points at ``, which does not exist
- `tex_calico_printing` points at ``, which does not exist
- `tex_canvas` points at ``, which does not exist
- `tex_carding` points at ``, which does not exist
- `tex_chlorine_bleaching` points at ``, which does not exist
- `tex_chrome_tanning` points at ``, which does not exist
- `tex_combing` points at ``, which does not exist
- `tex_cotton_gin` points at ``, which does not exist
- `tex_cotton_trade` points at ``, which does not exist
- `tex_drop_spindle` points at ``, which does not exist
- `tex_dye_madder` points at ``, which does not exist
- `tex_dye_murex` points at ``, which does not exist
- `tex_dye_woad` points at ``, which does not exist
- `tex_felting` points at ``, which does not exist
- `tex_field_bleaching` points at ``, which does not exist
- `tex_fitted_garment` points at ``, which does not exist
- `tex_flying_shuttle` points at ``, which does not exist
- `tex_fulling` points at ``, which does not exist
- `tex_fulling_water` points at ``, which does not exist
- `tex_hand_ginning` points at ``, which does not exist
- `tex_horizontal_loom` points at ``, which does not exist
- `tex_hosiery` points at ``, which does not exist
- `tex_indigo` points at ``, which does not exist
- `tex_jacquard_loom` points at ``, which does not exist
- `tex_knitting_frame` points at ``, which does not exist
- `tex_linen` points at ``, which does not exist
- `tex_mercerisation` points at ``, which does not exist
- `tex_mordanting` points at ``, which does not exist
- `tex_nylon` points at ``, which does not exist
- `tex_pattern_cutting` points at ``, which does not exist
- `tex_power_loom` points at ``, which does not exist
- `tex_rayon_nitro` points at ``, which does not exist
- `tex_rayon_viscose` points at ``, which does not exist
- `tex_roller_printing` points at ``, which does not exist
- `tex_rope_walk` points at ``, which does not exist
- `tex_sailcloth` points at ``, which does not exist
- `tex_sewing_machine` points at ``, which does not exist
- `tex_shoddy` points at ``, which does not exist
- `tex_silk_trade` points at ``, which does not exist
- `tex_spinning_jenny` points at ``, which does not exist
- `tex_spinning_mule` points at ``, which does not exist
- `tex_spinning_wheel` points at ``, which does not exist
- `tex_synthetic_dyes` points at ``, which does not exist
- `tex_tape_measure` points at ``, which does not exist
- `tex_textile_factory` points at ``, which does not exist
- `tex_treadle_loom` points at ``, which does not exist
- `tex_two_beam_loom` points at ``, which does not exist
- `tex_vegetable_tanning` points at ``, which does not exist
- `tex_warp_weighted_loom` points at ``, which does not exist
- `tex_water_frame` points at ``, which does not exist
- `tex_wool` points at ``, which does not exist
- `tex_wool_combing_machinery` points at ``, which does not exist

