# Module 98: Power Plants

This module is a parts bin, not a story. It covers 115 named machines and fuels that sit downstream of the basic prime movers already documented elsewhere (see 93_energy.md), grouped into families because that is how they actually relate: a Cornish boiler and a Lancashire boiler are the same idea taken one step further, not two separate inventions. Read a family once and you have all its members.

The single fact that should organise your thinking: a steam engine does not require coal. Charcoal, peat, wood gas and oil all work, worse in specific, measurable ways, and charcoal is GROWN at roughly 0.75 tonnes per hectare per year of managed coppice (ESTIMATED, basis: standard European coppice yield). Every furnace you light is a claim on land, before it is a claim on labour or capital. Keep that arithmetic in your head through every section below.

By the tier these machines sit at, cast iron, precision boring, and high sustained furnace heat are already assumed available to you through the metallurgy and precision chains (see 10_metallurgy.md, 40_power_precision.md). This module does not re-derive those; it tells you what to build once you have them.

---

### en_undershot_wheel - Undershot water wheel

Also covers: en_treadwheel, en_horse_gin

**What it is / why you want it.** The cheapest way to turn flowing water or muscle into a rotating shaft.

**Why you would never guess this.** An undershot wheel is struck by water's speed alone, and most of that momentum splashes past the flat paddles unused: measured efficiency is only 25-30 percent (MEASURED, Smeaton 1759). Horsepower is not a metaphor - Watt defined it from a horse in a gin, walking a circle and sustaining about 500W for a working day; a man on a treadwheel sustains roughly 75W (MEASURED, standard ergonomic figures), so ten men in a wheel replace two-thirds of one horse.

**Prerequisites.** cap_power_water / cap_power_muscle.

**Roman-available inputs.** Oak or elm wheel and axle (already worked by Roman millwrights); iron bar for gearing (ferrum, Noricum or Spain).

**Procedure.** 1. Site on any stream with flow, no fall needed. 2. Build paddle wheel, gear to horizontal shaft. 3. For gin, harness horse to walking-beam arm geared to vertical shaft.

**How you know it worked.** Shaft turns steadily under load without stalling; grindstone or pump keeps pace with normal use.

**Failure modes.** Flood carries an undershot wheel away; wet ground founders a horse; shock load shears wooden gear teeth.

**Cost & labour.** ESTIMATED: wheel and gearing, 40-60 artisan-days carpentry plus smith work; treadwheel or gin, half that.

**Danger.** Crush injuries from exposed gearing; kicks and bites from draft animals.

**Confidence: HIGH** - textbook hydraulics, Smeaton's figures are real measurements.

---

### en_overshot_wheel - Overshot water wheel

Also covers: en_breastshot_wheel, en_poncelet_wheel

**What it is / why you want it.** The efficient water wheel, when you have height to spare.

**Why you would never guess this.** The overshot wheel is filled with water at the top and uses its WEIGHT, not its speed, falling through nearly the whole wheel diameter - roughly double the undershot wheel's efficiency, 60-80 percent (MEASURED, Smeaton). Breastshot, water entering at axle height, is the compromise where the ground doesn't give you enough drop, at about 70 percent. Poncelet curves the entry vanes so water enters tangentially with no impact shock, recovering another 10 percent over a plain undershot wheel even without added height.

**Prerequisites.** cap_power_water.

**Roman-available inputs.** Timber wheel and buckets; a millrace or leat, which is civil engineering (surveying a level channel) before it is machine building.

**Procedure.** 1. Survey and cut a leat delivering water above the wheel's top. 2. Build bucketed rim. 3. For Poncelet, forge curved entry vanes to precise angle.

**How you know it worked.** Buckets fill and empty cleanly without water shooting past unused; wheel holds speed under load.

**Failure modes.** Ice stops the wheel in winter; buckets rot and leak; breastshot entry silts.

**Cost & labour.** ESTIMATED: leat construction dominates cost, weeks of labour gang time depending on distance; wheel itself comparable to undershot.

**Danger.** Falling into a leat or wheel pit; low compared to steam.

**Confidence: HIGH** - Smeaton's efficiency figures are the historical benchmark for this whole family.

---

### en_penstock - Penstock and flume

Also covers: en_draft_tube, en_tide_mill

**What it is / why you want it.** Delivers water to a wheel or turbine under control, and recovers energy after it leaves.

**Why you would never guess this.** An open flume is a miniature aqueduct and leaks and freezes; a penstock, a pipe under pressure (wood stave with iron hoops, or lead), delivers the same head through far smaller cross-section and lets you site the machine away from the stream itself. A draft tube, a diverging pipe fitted below a turbine, slows the exiting water gradually and recovers kinetic energy that would otherwise be lost, adding several effective meters of head for free and letting the turbine sit above tailwater level, something no wheel can do. A tide mill is an ordinary wheel plus a pond and a one-way sluice: the rising tide fills the pond, the gate shuts, and the wheel runs on the controlled fall as the pond empties against the falling sea, predictable to the minute from tide tables but running only about ten hours in twenty-four.

**Prerequisites.** cap_power_water; draft tube needs en_fourneyron_turbine; tide mill needs en_overshot_wheel.

**Roman-available inputs.** Lead sheet for penstock lining (plumbum, Britain); oak staves and iron hoops; stone for tide pond walls.

**Procedure.** 1. Lay pipe on the surveyed gradient. 2. Fit sluice gate at pond entrance for tide mill. 3. Fit draft tube below turbine outlet, diverging gradually, never abruptly.

**How you know it worked.** No pressure surge or hammer noise when sluice closes; draft tube shows no cavitation pitting after a season's running.

**Failure modes.** Penstock bursts from water hammer if a sluice slams shut; draft tube cavitates (water flashing to vapour from low pressure) and pits the turbine if made too long.

**Cost & labour.** ESTIMATED: pipe and hoop ironwork scales directly with length; tide pond wall is a substantial masonry project, months of labour.

**Danger.** Burst penstock under pressure can knock a person down; tide gate machinery crushes hands.

**Confidence: MEDIUM** - the physics is solid, exact draft tube gains are site-specific.

---

### en_fourneyron_turbine - Fourneyron turbine

Also covers: en_francis_turbine, en_pelton_wheel, en_kaplan_turbine

**What it is / why you want it.** A fully enclosed, guided water machine, far smaller than a wheel for the same power.

**Why you would never guess this.** A turbine differs from a wheel by using fixed guide vanes to accelerate and aim water before it strikes the moving runner, so the entire flow works continuously rather than bucket by bucket - this is why a turbine the size of a barrel can do the work of a wheel the size of a house. Which type you build is dictated by how much head you have, not by preference: Fourneyron (radial outflow, 1827) suits medium head at 80+ percent efficiency (MEASURED); Francis (inward flow, the reverse geometry) suits a wide range of medium heads at 85+ percent (MEASURED) and is the general-purpose choice; Pelton (a needle jet striking split buckets) suits very high head, hundreds of metres, at 90+ percent, pure impulse with no reaction; Kaplan (adjustable-pitch blades, like a ship's propeller) suits very low head and high volume, the only one of the four that adapts its geometry to changing flow.

**Prerequisites.** cap_tol_10um, boring_mill; each later type also requires the one before it in this list.

**Roman-available inputs.** Bronze (aes, tin from Cornwall, copper from Cyprus) for runner and guide vanes; cast iron casing.

**Procedure.** 1. Cast and machine guide vane ring to design angle. 2. Cast and machine runner to matching clearance (tenths of a millimetre). 3. Fit in sealed casing under penstock head.

**How you know it worked.** Shaft speed matches calculated design speed for the given head and flow; no cavitation noise (a rattling, gravel-like sound) at the runner.

**Failure modes.** Cavitation pits the runner where local pressure drops too low; sand or silt in the water sandblasts the vanes.

**Cost & labour.** ESTIMATED: precision casting and machining, hundreds of artisan-hours per unit, well beyond wheel-building.

**Danger.** Enclosed high-speed machinery; a burst runner at speed is a shrapnel event.

**Confidence: MEDIUM** - efficiencies are well documented historical figures; achieving the required tolerances at Roman-adjacent tooling is the open question.

---

### en_water_wheel_governor - Governor for water wheel

Also covers: en_centrifugal_governor

**What it is / why you want it.** Automatic speed regulation with no person watching.

**Why you would never guess this.** An unregulated mill speeds up the instant load drops (grinding stops resisting the stones) and can burst a stone or a gear train. The centrifugal governor is a physical feedback loop that predates any electronics: spinning weights fly outward as speed rises, and the linkage they pull throttles the water gate, or on Watt's identical steam-engine version, the throttle valve, closed. It is a proportional controller only, and it oscillates ("hunts") slightly around its setpoint rather than holding dead steady, because it can only react after speed has already changed.

**Prerequisites.** en_overshot_wheel or equivalent; steam version needs en_separate_condenser, cap_tol_100um.

**Roman-available inputs.** Bronze flyball weights; iron linkage rods.

**Procedure.** 1. Gear a vertical spindle to the wheel or engine shaft. 2. Hang pivoted arms with weights from the spindle top. 3. Link arm angle to gate or valve via a sliding collar.

**How you know it worked.** Shaft speed stays within a narrow band as load is added and removed suddenly.

**Failure modes.** Linkage friction causes violent hunting; a bent arm or broken spring gives a false reading and the mill overspeeds unseen.

**Cost & labour.** ESTIMATED: a skilled smith and fitter, days not weeks, once the mill itself exists.

**Danger.** A failed governor lets machinery run away to destructive speed.

**Confidence: HIGH** - Watt's governor is one of the best-documented mechanisms in the whole steam corpus.

---

### en_post_mill - Post mill

Also covers: en_tower_mill

**What it is / why you want it.** A windmill you can turn to face the wind.

**Why you would never guess this.** In a post mill the entire timber body pivots on one vertical post so a miller can push the whole building around by hand with a tail pole - this caps the size, since the post carries all the weight and every gust's full torque. A tower mill fixes the body (stone or brick) and rotates only the cap on a bearing ring, so the mill can be much taller and larger, catching cleaner wind above ground turbulence, at the cost of a bearing that must carry the whole cap's weight without binding.

**Prerequisites.** cap_power_water (wind treated as a power-capture prerequisite in this tree).

**Roman-available inputs.** Oak frame; canvas sails (Roman sailcloth is already a mature craft); stone for tower.

**Procedure.** 1. Build pivoting timber body on greased post, or fixed tower with rotating cap. 2. Fit four sail arms. 3. Gear windshaft to millstones.

**How you know it worked.** Mill turns freely to face changing wind; stones grind steadily.

**Failure modes.** Post cracks under a broadside gust and the mill can capsize; tower curb ring wears unevenly and the cap seizes.

**Cost & labour.** ESTIMATED: post mill, one carpentry crew, weeks; tower mill, masonry crew plus carpentry, months.

**Danger.** Sail tips move at tens of km/h; a miller struck by a sail ("taken by the sail") is a recorded, common cause of death in windmill trades.

**Confidence: HIGH** - well attested medieval and early modern practice.

---

### en_patent_sail - Patent sail

Also covers: en_spring_sail, en_windmill_fantail

**What it is / why you want it.** Automatic speed and orientation control for a windmill, no one climbing the sails.

**Why you would never guess this.** Plain cloth sails must be reefed by hand out on the arm in rising wind, dangerous and slow, and a sudden squall can wreck the mill first. Spring sail replaces cloth with hinged shutters held shut by a spring; wind pressure beyond the spring's setting forces them open automatically, spilling excess force. Patent sail links every shutter on every arm to one rod through the windshaft, so a single lever, adjustable while the mill is running, sets the whole mill's power at once - the first live remote speed control in this tree. The fantail applies the same idea to orientation: a small perpendicular rotor on the tail catches any crosswind and, through reduction gearing, slowly cranks the whole cap around to square the main sails into the wind, with nobody there at all.

**Prerequisites.** en_post_mill; fantail also needs en_tower_mill, cap_tol_100um.

**Roman-available inputs.** Iron shutter frames; small canvas fantail blades; bronze gearing.

**Procedure.** 1. Replace cloth sail bays with hinged wooden shutters. 2. Fit spring tensioner per shutter. 3. Link all shutters to windshaft rod for patent-sail control. 4. Mount small fantail rotor at right angles on the cap, geared to the slewing ring.

**How you know it worked.** Shutters open automatically in a gust and mill speed stays roughly constant; cap re-aligns to a wind shift within minutes unattended.

**Failure modes.** Fatigued spring lets shutters flap uncontrolled; rusted fantail gearing seizes and the mill runs broadside, self-destructing in a strong gust.

**Cost & labour.** ESTIMATED: precision ironwork for linkage, a skilled smith's specialty, weeks per mill.

**Danger.** Same sail-strike risk as the base mill; a seized fantail during a storm is a mill-destroying failure.

**Confidence: HIGH** - Meikle and Cubitt's mechanisms are well documented eighteenth-century engineering.

---

### en_wind_pump - Wind pump

Also covers: en_wind_electric

**What it is / why you want it.** Wind power applied where there is no stream to turn a wheel.

**Why you would never guess this.** A wind pump is simply a mill re-geared to a reciprocating pump crank instead of millstones, useful specifically on flat land with no fall for a water wheel - and because wind is intermittent, it needs a header tank for storage exactly as a wind-electric plant needs a battery. Wind electric generator couples the same mill through step-up gearing (a mill turns tens of rpm, a dynamo needs hundreds) to a dynamo, but the gearbox now takes gust loads far beyond anything a millstone gear train was designed for, and without lead-acid storage or a standby engine, supply is only as reliable as the wind.

**Prerequisites.** en_post_mill; wind electric additionally needs dynamo.

**Roman-available inputs.** Bronze pump valves and gearing; iron pump rod.

**Procedure.** 1. Replace millstone drive with crank and pump rod. 2. Route to elevated header tank. 3. For electric version, add step-up gear train to a dynamo.

**How you know it worked.** Tank fills steadily in normal wind; pump rod does not bind at either end of stroke.

**Failure modes.** Gearbox teeth shear in a sudden gust; pump rod jams if the well silts up.

**Cost & labour.** ESTIMATED: pump conversion, a smith and carpenter, one to two weeks over an existing mill.

**Danger.** Moving pump rod and gearing crush hazard; low overall.

**Confidence: MEDIUM** - the mechanical principle is simple, gust-load durability is a real, under-documented weak point historically.

---

### en_atmospheric_engine - Atmospheric engine (Newcomen)

Also covers: en_double_acting

**What it is / why you want it.** The first practical engine that turns fuel into continuous mechanical pumping.

**Why you would never guess this.** This engine does not use steam pressure to move the piston - it uses ATMOSPHERIC pressure. Near-atmospheric steam fills the cylinder, a jet of cold water sprayed inside condenses it to near-vacuum, and the ordinary weight of the air above (about ten tonnes per square metre) pushes the piston down. It is slow, four to twelve strokes a minute (MEASURED), because the cylinder itself must reheat from cold every single stroke, which also explains its terrible fuel appetite: it is single-acting only, one power stroke down and a counterweight resets it, with no way to give smooth continuous rotation. Double-acting cylinder is the eventual fix: steam admitted alternately to both ends through valves so every stroke, both directions, is a power stroke, doubling output for the same cylinder and enabling smooth rotary drive, but the piston rod must now pass sealed through one cylinder end, and that packed gland leaks and needs constant repacking.

**Prerequisites.** cap_heat_1100, cap_tol_1mm, boring_mill.

**Roman-available inputs.** Cast iron cylinder (via blast furnace chain, see 10_metallurgy.md); leather or hemp piston packing.

**Procedure.** 1. Bore true cylinder. 2. Fit piston with leather packing. 3. Fit boiler, injection water valve, and beam linkage to pump rod.

**How you know it worked.** Piston completes a full stroke and the pump rod lifts water on each cycle without stalling.

**Failure modes.** Packing leak loses vacuum; injection valve stuck open floods the cylinder with cold water.

**Cost & labour.** ESTIMATED: major casting and boring project, a skilled foundry crew for weeks.

**Danger.** LOW pressure so it does not explode; the beam and pump rod's sheer weight and momentum are the main hazard.

**Confidence: HIGH** - Newcomen's engine and its documented 4-12 strokes/minute cycle are extremely well attested.

---

### en_high_pressure_engine - High pressure steam engine

Also covers: en_compound_engine, en_uniflow_engine

**What it is / why you want it.** A much smaller, lighter engine per unit of power, using pressure instead of vacuum.

**Why you would never guess this.** Pushing with several atmospheres of steam pressure, rather than exploiting the one atmosphere already free above you, makes an engine small enough to move itself, which is what made locomotives and portable engines possible - but now a failed boiler seam is a bomb, not a leak. Compound engine expands the same steam charge across two or three cylinders in series instead of dropping it all at once, so no single cylinder wall swings through the whole temperature range each stroke; this cuts fuel use roughly in half compared to a simple engine (ESTIMATED, basis: widely cited 50 percent compounding gain). Uniflow pushes the same idea to its limit: steam always enters at the cylinder ends and exhausts only through ports uncovered mid-stroke, so flow is always one direction and the hot end stays hot, the cold end cold, permanently rather than swinging every stroke.

**Prerequisites.** cap_heat_1300, cap_tol_10um, boring_mill; compound needs en_high_pressure_engine + en_separate_condenser; uniflow needs en_corliss_valve.

**Roman-available inputs.** Cast iron cylinder blocks; wrought iron bar for staying.

**Procedure.** 1. Bore high-precision cylinder(s). 2. Fit boiler rated well above working pressure with safety valve (see below). 3. For compound, connect cylinders in series with intermediate receiver.

**How you know it worked.** Engine holds steady speed under load at rated pressure without valve chatter or knocking.

**Failure modes.** Boiler seam or joint failure under pressure (see boiler entries); compound engine hammers the crank if cylinder pressures fall out of balance.

**Cost & labour.** ESTIMATED: a substantial foundry and fitting project, a crew of specialists for a season.

**Danger.** HIGH - high-pressure boiler failure is lethal; never operate without a functioning, unweighted safety valve.

**Confidence: HIGH** - the fuel-saving figures for compounding are widely reported historical measurements.

---

### en_steam_turbine_impulse - Impulse steam turbine (de Laval)

Also covers: en_steam_turbine_curtis, en_steam_turbine_reaction

**What it is / why you want it.** Converts steam's heat directly into rotation, no piston.

**Why you would never guess this.** De Laval's insight was to expand the entire pressure drop in one fixed nozzle rather than gradually in moving blades, producing a jet at the true molecular speed of the steam - hundreds of metres per second - so the wheel it strikes must spin up to 30,000 rpm (MEASURED) and needs a reduction gear before it can drive anything. Curtis splits that one big drop across two nozzle-and-bucket stages, trading some efficiency for a slower, more usable speed. Parsons' reaction turbine goes further: ten to fifty small stages, each row of moving blades itself shaped like a little nozzle, so the reaction of steam leaving each row pushes the rotor directly - lower speed (about 3,000 rpm), no gearbox, and the best efficiency of the three, 85+ percent (MEASURED), at the cost of far more stages to machine precisely.

**Prerequisites.** cap_heat_1300, cap_tol_10um, boring_mill; Curtis and reaction both build on en_steam_turbine_impulse.

**Roman-available inputs.** Bronze blading; cast iron casing.

**Procedure.** 1. Machine nozzle(s) to precise throat dimension. 2. Machine and balance bladed rotor. 3. Fit in sealed casing with shaft bearings.

**How you know it worked.** Rotor reaches design speed smoothly with no vibration audible by hand on the casing.

**Failure modes.** Wet steam (water droplets) erodes blades rapidly - superheating (below) answers this; a cracked blade at speed is a shrapnel event.

**Cost & labour.** ESTIMATED: among the most demanding machining projects in this module, specialist crew for months.

**Danger.** HIGH - rotational energy released at failure is catastrophic.

**Confidence: HIGH** - efficiencies and speeds are well-documented historical figures for these named designs.

---

### en_boiler_haystack - Haystack boiler

Also covers: en_boiler_wagon

**What it is / why you want it.** The earliest practical pressure boilers.

**Why you would never guess this.** The haystack boiler, a domed copper vessel with brazed seams, can only hold 2-3 atmospheres (MEASURED) before the seams give way, and copper is expensive - this is exactly why boiler pressure stayed near zero gauge for the first century of steam. Wagon boiler, a horizontal cylinder with one large internal fire tube, is the first step up, but its flat ends are the structural weak point: a flat plate under pressure wants to bulge, unlike a cylinder, and needs heavy iron stay rods or it tears.

**Prerequisites.** cap_heat_1100, cap_tol_1mm.

**Roman-available inputs.** Copper sheet (haystack); cast and wrought iron (wagon), both already Roman-worked metals.

**Procedure.** 1. Braze or rivet copper dome over firebox (haystack). 2. Roll and rivet cylinder shell with stayed flat ends (wagon). 3. Fit safety valve before first firing.

**How you know it worked.** Holds steady pressure with no visible steam leak at any seam for a full day's firing.

**Failure modes.** Seam brazing fails under repeated heating and cooling cycles; flat ends bulge and eventually tear.

**Cost & labour.** ESTIMATED: coppersmith work is costly and slow, weeks for a haystack boiler; wagon boiler somewhat cheaper in ironwork.

**Danger.** HIGH even at low pressure - a sudden seam failure sprays scalding water and steam without warning.

**Confidence: HIGH** - these are the best-documented earliest boiler forms.

---

### en_boiler_cornish - Cornish boiler

Also covers: en_boiler_lancashire, en_boiler_locomotive

**What it is / why you want it.** Puts the fire inside the water instead of underneath it, multiplying heated surface.

**Why you would never guess this.** A Cornish boiler runs one large fire-tube through the middle of the water-filled shell, hugely increasing the surface where heat actually transfers; Lancashire simply doubles that to two fire tubes for still more surface. Locomotive boiler compresses the same idea to its limit: hundreds of small tubes carry hot gas from the firebox through the water to a smokebox, packing enormous surface into a portable shell - but a flat crown sheet sits directly above the fire holding back the water, and if water level ever drops below it, the now-dry iron overheats and fails, releasing the boiler's entire contents into the fire in an instant.

**Prerequisites.** en_boiler_wagon, cap_tol_10um.

**Roman-available inputs.** Wrought iron plate and rivets; cast iron for fittings.

**Procedure.** 1. Fit one (Cornish) or two (Lancashire) internal fire tubes through the shell. 2. For locomotive form, build firebox with flat crown sheet plus bank of small tubes to smokebox. 3. Fit water gauge glass and a fusible lead plug in the crown sheet.

**How you know it worked.** Water gauge shows a stable level with the fire lit and no crown-sheet discolouration after use.

**Failure modes.** Crown sheet failure from low water ("blew its crown") is the single most common historical boiler-explosion cause; scale builds in stagnant flow pockets.

**Cost & labour.** ESTIMATED: locomotive-type tube boiler is the most labour-intensive of the fire-tube family, a specialist boilershop for months.

**Danger.** HIGH - this is the textbook explosion mechanism; the fusible plug is designed to melt and vent steam harmlessly before the iron itself fails catastrophically.

**Confidence: HIGH** - crown sheet failure is one of the best-documented causes of historical boiler deaths.

---

### en_boiler_water_tube - Water tube boiler

Also covers: en_boiler_babcock, en_boiler_stirling

**What it is / why you want it.** Inverts the fire-tube boiler: water inside many small tubes, fire and gas outside.

**Why you would never guess this.** A tube full of pressurised water is in tension, trying to burst outward, and a thin-walled small tube resists tension far better per unit weight than a large shell resists the same pressure, because a shell's required wall thickness grows with its diameter while a small tube's barely does. Water-tube boilers therefore run at much higher pressure on much less metal, and if one tube fails it vents a small amount of water, not the whole vessel at once - a fundamentally safer failure mode than any fire-tube design above. Babcock and Wilcox uses straight tubes between headers, easy to inspect and replace one at a time. Stirling coils the tubes for a very compact, high-surface boiler, at the cost of uneven heating at the coil's centre and thermal shock when cold feedwater first enters.

**Prerequisites.** cap_tol_10um, boring_mill.

**Roman-available inputs.** Bronze and cast iron headers; wrought iron tubes.

**Procedure.** 1. Expand tube ends into headers with a cup-expander tool for a sealed joint. 2. Arrange tubes for full gas contact with minimal dead pockets. 3. Fit safety valve and gauge before firing.

**How you know it worked.** Holds high pressure steadily with only minor weeping at joints, correctable by re-expanding.

**Failure modes.** A single tube fails from scale or corrosion, producing a violent local jet, not a full-vessel explosion.

**Cost & labour.** ESTIMATED: many precisely expanded tube joints, a specialist boilershop crew for a season.

**Danger.** MEDIUM relative to fire-tube boilers - inherently safer failure mode, still dangerous at full pressure.

**Confidence: HIGH** - the tension-versus-shell-stress argument is textbook pressure vessel engineering.

---

### en_separate_condenser - Separate condenser (Watt)

Also covers: en_condenser_jet, en_condenser_surface

**What it is / why you want it.** The single biggest fuel-saving idea in the entire steam corpus.

**Why you would never guess this.** The win is not condensing the steam - the Newcomen engine already did that inside the cylinder. The win is that the cylinder stops being cooled and reheated every stroke. In the atmospheric engine, the cold-water jet that condenses steam also chills the cylinder walls, so fresh steam on the next stroke condenses uselessly re-warming the metal before doing any work at all - Watt measured this waste at roughly three-quarters of the fuel. Moving condensation to a separate vessel, connected by a valve, keeps the cylinder permanently hot and the condenser permanently cold. Jet condenser sprays water directly into the steam, fast and simple, but the mixed water and air must be pumped out together and cannot be recycled to the boiler, being contaminated. Surface condenser condenses steam on the outside of many cold-water tubes so steam and cooling water never mix, letting a ship recycle its own fresh boiler water instead of scaling solid on seawater.

**Prerequisites.** en_atmospheric_engine, cap_tol_10um.

**Roman-available inputs.** Copper or brass tubes (surface type); cast iron condenser vessel.

**Procedure.** 1. Build separate vacuum-tight vessel connected to cylinder by valve. 2. For jet type, add water spray and air pump. 3. For surface type, bundle straight tubes with cooling water flow.

**How you know it worked.** Fuel consumption per stroke drops sharply compared to an equivalent atmospheric engine; vacuum holds between strokes.

**Failure modes.** Air leaking through any gland ruins the vacuum; surface condenser tubes foul with scale and lose cooling.

**Cost & labour.** ESTIMATED: a skilled coppersmith and fitter, weeks per unit.

**Danger.** LOW physically; socially this was Watt's most fiercely contested patent (1769-1800) - expect the same resistance around any single, obviously superior invention.

**Confidence: HIGH** - the three-quarters fuel-waste figure is Watt's own well-documented measurement.

---

### en_expansive_working - Expansive working (cutoff)

Also covers: en_cutoff_valve, en_corliss_valve

**What it is / why you want it.** Lets steam already admitted do further work by expanding on its own, instead of feeding the cylinder at full pressure the whole stroke.

**Why you would never guess this.** Shutting the inlet valve early ("cutoff") and letting the trapped steam expand and cool for the rest of the stroke throttles fuel more steeply than it throttles power, giving roughly a 20 percent efficiency gain (MEASURED). A simple cutoff valve sets one fixed point by hand or governor. The Corliss valve refines this into four independent valves on trip-cams so cutoff can be adjusted smoothly while running, each valve sealing dead-tight at its own stop - but every valve face must be flat to a hair's width or it leaks exactly the pressure the mechanism exists to save.

**Prerequisites.** en_high_pressure_engine; Corliss additionally needs cap_tol_10um.

**Roman-available inputs.** Bronze valve faces (best wear resistance available); cast iron valve chest.

**Procedure.** 1. Fit slide or trip valve with adjustable cutoff point. 2. For Corliss, fit four independent valves with cam-trip release. 3. Lap valve faces flat against a reference plate.

**How you know it worked.** Fuel use per stroke falls with cutoff shortened, until power output starts to suffer noticeably.

**Failure modes.** Valve seat wear reintroduces leakage; wrong cutoff timing makes the engine knock near stroke's end.

**Cost & labour.** ESTIMATED: Corliss gear is a precision fitter's specialty, weeks per engine.

**Danger.** LOW beyond the base engine's own pressure hazard.

**Confidence: HIGH** - the 20 percent expansive-working gain is a standard cited historical figure.

---

### en_economiser - Economiser

Also covers: en_feedwater_heater, en_superheater

**What it is / why you want it.** Three ways to catch heat that is about to be thrown away.

**Why you would never guess this.** An economiser is a bank of tubes in the flue AFTER the boiler, extracting leftover heat from exhaust gas that would otherwise go up the chimney, saving 15-20 percent of fuel (MEASURED) essentially for free. A feedwater heater does the same job earlier: it warms cold water on its way INTO the boiler using waste steam, since raising water from ambient to boiling is itself a large share of total fuel use, saving another 10-15 percent (MEASURED). A superheater raises steam temperature further after it leaves the boiler, without adding pressure or moisture - dry steam does more work as it expands and, critically, does not erode turbine blades the way wet steam does.

**Prerequisites.** en_separate_condenser.

**Roman-available inputs.** Cast iron flue tubes (economiser); copper coil (feedwater heater); iron alloy tubes able to hold red heat (superheater).

**Procedure.** 1. Route tube bank through flue gas path before the chimney. 2. Route feedwater through a separate coil heated by exhaust steam. 3. Route superheater tubes back through the hottest part of the firebox.

**How you know it worked.** Chimney gas feels noticeably cooler by hand-test at a safe distance than before fitting; steam at cylinder inlet shows no wetness (no droplets on a polished plate held briefly in the flow).

**Failure modes.** Superheater tubes run hottest of anything in the boiler and scale or oxidise fastest; economiser corrodes from acidic condensate if flue gas cools below its dew point inside the tubes.

**Cost & labour.** ESTIMATED: moderate, an extension to an existing boiler, days to weeks of boilershop work.

**Danger.** MEDIUM - superheated steam burns are worse than wet steam burns because superheated steam is invisible and carries more energy.

**Confidence: HIGH** - all three efficiency figures are widely cited historical measurements.

---

### en_safety_valve - Safety valve (pop-off)

Also covers: en_pressure_gauge, en_steam_trap

**What it is / why you want it.** The three instruments that tell you what is happening inside a sealed pressure vessel you cannot see into.

**Why you would never guess this.** The safety valve, weighted or spring-loaded to lift at a set pressure and vent to atmosphere, is the single most important safety device in the entire steam age; a boiler without one, or one with the valve deliberately weighted down to squeeze more power out (a common, lethal historical shortcut), is a bomb on a schedule. The pressure gauge (a curved flattened tube that tries to straighten under internal pressure, moving a needle) is the only way to know what pressure a sealed vessel actually holds, since nothing about it looks different at one atmosphere or ten. The steam trap, a small thermostatic or float valve on pipe runs, drains condensed water while holding steam back; without it, condensate pools at low points and an oncoming rush of steam can slam that trapped water violently down the pipe (water hammer), bursting fittings.

**Prerequisites.** en_high_pressure_engine (safety valve); cap_measure_temp, cap_tol_100um (gauge).

**Roman-available inputs.** Bronze valve body and spring; iron weights.

**Procedure.** 1. Fit weighted or spring valve calibrated to lift below the boiler's rated pressure. 2. Fit Bourdon-tube gauge to the same steam space. 3. Fit float or thermostatic traps at every low point in the pipe run.

**How you know it worked.** Valve lifts and vents cleanly at the marked pressure during a deliberate test; gauge needle tracks pressure changes smoothly.

**Failure modes.** A tied-down or corroded-shut safety valve is the classic cause of catastrophic boiler explosion; an unread or absent gauge hides a developing overpressure.

**Cost & labour.** ESTIMATED: a bronze-founder and fitter, days per set.

**Danger.** HIGH for the whole cluster - the historical record of boiler explosions is dominated by exactly this failure: valve tied shut, gauge unread or missing.

**Confidence: HIGH** - the causal link between disabled safety valves and explosions is extremely well documented.

---

### en_parallel_motion - Parallel motion linkage (Watt)

Also covers: en_sun_planet_gear, en_reduction_gear

**What it is / why you want it.** Three separate answers to turning a piston's straight-line motion into useful rotation.

**Why you would never guess this.** A beam engine's piston rod moves in a true straight line, but the far end of the beam it drives swings in an arc - Watt's rhomboid parallel-motion linkage constrains the beam-end's path to be straight enough using only pivoted rods, no sliding guide, and he considered it his best invention. Sun-and-planet gear exists because Watt could not use a simple crank (Pickard had already patented it): a planet gear fixed to the connecting rod walks around a fixed sun gear on the flywheel shaft, converting the same up-down motion to rotation while working around the patent, and as a side effect turning the shaft twice per stroke, smoothing the flywheel. Reduction gear steps down turbine speeds of 5,000-30,000 rpm to the 10-500 rpm that mill machinery or a propeller actually wants, each precisely-cut mesh losing about 2 percent of power to friction (MEASURED).

**Prerequisites.** en_double_acting, cap_tol_100um; reduction gear needs en_steam_turbine_impulse, cap_tol_10um.

**Roman-available inputs.** Iron linkage rods; cast iron gear blanks, cut to true involute profile.

**Procedure.** 1. Fabricate rhomboid linkage from measured beam geometry. 2. Cast and cut sun and planet gears to matched pitch. 3. For reduction gear, cut multi-stage gear train to required ratio.

**How you know it worked.** Piston rod travels in a visibly straight line with no side-load wear on the cylinder walls after running.

**Failure modes.** Worn linkage pins let the rod side-load and wear the cylinder oval; roughly-cut gear teeth whine, wear fast, and shear under shock.

**Cost & labour.** ESTIMATED: precision gear-cutting is a specialist trade, weeks per set.

**Danger.** LOW, standard mechanical hazards of moving linkage and gearing.

**Confidence: HIGH** - all three mechanisms are exceptionally well documented eighteenth and nineteenth century engineering.

---

### en_turbine_blading - Turbine blade design and profile

Also covers: en_turbine_condenser_vacuum

**What it is / why you want it.** The precision engineering that decides whether a turbine is efficient or self-destructive.

**Why you would never guess this.** With dozens to hundreds of identical blades on one rotor, even a 1 percent deviation in profile from blade to blade costs roughly 5 percent of the turbine's overall efficiency (ESTIMATED, basis: standard turbomachinery blade-tolerance sensitivity), and worse, sets up vibration that fatigues the whole disc. A turbine's exhaust benefits enormously from being pulled down to a hard vacuum, 0.05-0.1 atmosphere (MEASURED), because every extra 0.1 atmosphere of vacuum lets steam expand further inside the turbine before leaving, extracting roughly another 5 percent of available work (MEASURED) - but any air leaking in through a shaft gland destroys that vacuum as fast as the pump can remove it.

**Prerequisites.** cap_tol_10um, boring_mill; vacuum system needs en_steam_turbine_reaction, cap_vac_1torr.

**Roman-available inputs.** Bronze blade stock; leather or packed-fibre shaft seals for the vacuum system.

**Procedure.** 1. Machine each blade to a master template, checked by direct comparison, not by eye. 2. Balance the assembled rotor statically and dynamically. 3. Fit shaft-driven vacuum pump with tight gland seals to the condenser.

**How you know it worked.** Rotor runs without audible vibration at full speed; vacuum gauge holds steady under load.

**Failure modes.** A blade fatigue crack gives no warning until sudden failure at speed; vacuum system gland wear lets efficiency creep down with no obvious cause.

**Cost & labour.** ESTIMATED: the most labour-intensive precision task in this module, a dedicated shop for months per turbine set.

**Danger.** HIGH - a burst rotor disc at speed is lethal to anyone nearby.

**Confidence: MEDIUM** - the physics is solid; the 1-percent-to-5-percent sensitivity figure is an engineering rule of thumb, not a single citable measurement.

---

### en_four_stroke_cycle - Four-stroke cycle (Otto)

Also covers: en_two_stroke_cycle, en_gas_engine

**What it is / why you want it.** The internal-combustion cycle that made compact, fuel-efficient engines possible.

**Why you would never guess this.** Firing only once every two revolutions sounds wasteful, but it is what lets you compress the fuel-air mixture significantly before ignition, and a compressed charge burns faster and pushes with far higher peak pressure, 50-100 psi (MEASURED), than any uncompressed steam stroke - so despite firing half as often, it is far more powerful per cylinder volume. Two-stroke fires every revolution by using the piston itself to uncover ports at the bottom of its travel, roughly doubling power for the same size engine, but fresh charge and exhaust briefly mix in the cylinder (poor "scavenging"), so unburnt fuel escapes and efficiency suffers. The coal gas engine is the same four-stroke cycle burning coal gas, ignited by an external heated tube rather than any spark - only 20 percent efficient (MEASURED) but extremely reliable and simple, history's first commercially successful internal combustion engine.

**Prerequisites.** cap_heat_1100, cap_tol_1mm, boring_mill.

**Roman-available inputs.** Cast iron cylinder block; town gas (see fuel entries below) for the gas engine variant.

**Procedure.** 1. Bore cylinder to close tolerance. 2. Fit valves timed to a camshaft geared 2:1 to the crank. 3. For gas engine, fit external hot-tube igniter instead of a spark source.

**How you know it worked.** Engine runs smoothly at governed speed with regular, even firing audible by ear.

**Failure modes.** Valve timing drift fires the charge against a closing exhaust valve, blowing hot gas back through the intake; two-stroke fouls its ignition source with unburnt oil from poor scavenging.

**Cost & labour.** ESTIMATED: a specialist machine shop project, weeks to months per engine.

**Danger.** MEDIUM - an internal explosion in a flawed cylinder is violent, though contained compared to a boiler.

**Confidence: HIGH** - efficiency and pressure figures are well documented for these historical engine types.

---

### en_hot_bulb_engine - Hot bulb engine

Also covers: en_carburetted_engine, en_compression_ignition

**What it is / why you want it.** Three ways to ignite fuel inside a cylinder without an electric spark.

**Why you would never guess this.** Hot bulb ignites fuel simply by dripping it onto a metal bulb kept glowing by the previous cycle's own combustion - crude, forgiving of bad fuel, and 25 percent efficient (MEASURED), the workhorse of early motor boats. Carburetted engine draws fuel into the airstream by suction in a narrowing throat (a Venturi), the same principle as a perfume atomiser, working only because petrol evaporates readily, and needing a precise float-controlled fuel level to keep the mixture consistent as the tank empties. Compression ignition (Diesel) uses no spark and no hot bulb at all: air alone is compressed so hard, 15:1 versus 8:1 for a spark engine (MEASURED), that it reaches 500°C+ and ignites injected fuel on contact, giving the best efficiency of the three, 40 percent (MEASURED), but demanding precision machining and strong materials for the much higher peak pressures.

**Prerequisites.** cap_heat_1100 to 1300 depending on type; cap_tol_1mm (hot bulb, carburettor) or cap_tol_10um, boring_mill (compression ignition).

**Roman-available inputs.** Cast iron cylinder and bulb; refined petroleum fuel (mat_petroleum_refined, see fuel entries below).

**Procedure.** 1. Fit glowing bulb chamber connected to cylinder (hot bulb) or Venturi and float chamber (carburetted). 2. For compression ignition, bore cylinder to the higher tolerance needed for 15:1 compression. 3. Preheat bulb externally before first start.

**How you know it worked.** Engine restarts reliably from a warm bulb or from cold-cranking compression alone (Diesel), without external ignition aid once running.

**Failure modes.** Hot bulb goes cold and won't restart without reheating; carburettor float sticks, flooding or starving the engine; Diesel cylinder or injector failure under high pressure is more damaging than in a spark engine.

**Cost & labour.** ESTIMATED: hot bulb is the simplest and cheapest of the three to build; compression ignition the most demanding.

**Danger.** MEDIUM to HIGH depending on type - Diesel's higher pressures raise the stakes of any component failure.

**Confidence: HIGH** - all three efficiency and pressure figures are well documented.

---

### en_poppet_valve - Poppet valve and camshaft

Also covers: en_sleeve_valve, en_fuel_injection

**What it is / why you want it.** Precise, repeatable control of gas flow in and out of a cylinder.

**Why you would never guess this.** A camshaft geared to the crankshaft opens each poppet valve against a closing spring at exactly the right instant every cycle, locking timing mechanically with no operator input - but the valve head runs red-hot and can stick or burn. Sleeve valve avoids that weakness: a sliding sleeve between piston and cylinder wall has ports that line up with the cylinder's own ports at the right moment, quieter and simpler in timing, but the sleeve-to-cylinder clearance must be tiny or it leaks compression, making it far harder to machine well. Fuel injection replaces a carburettor's suction with a pump forcing fuel at 200+ atmospheres (MEASURED) through a fine nozzle into droplets 10-100 microns across, timed to within one degree of crank rotation - this precision is what makes compression ignition work at all, since there is no spark to fall back on if timing drifts.

**Prerequisites.** en_four_stroke_cycle, cap_tol_100um; sleeve valve and injection need cap_tol_10um; injection needs en_compression_ignition.

**Roman-available inputs.** Bronze valve seats; cast iron camshaft; bronze injector body.

**Procedure.** 1. Cut cam profiles to the required lift and duration. 2. Fit valve springs of matched, tested strength. 3. For injection, fit high-pressure pump timed to crank position.

**How you know it worked.** Valve train runs quietly with no clatter; injected fuel forms a fine mist visible only as a haze, not a stream, when tested into open air.

**Failure modes.** Valve spring fatigue lets a valve float and strike the piston; injector nozzle coking (carbon buildup) ruins the spray pattern.

**Cost & labour.** ESTIMATED: camshaft and valve gear, a machine shop specialty, weeks; injection pump considerably more, among the hardest small components in this module.

**Danger.** MEDIUM, standard moving-machinery and high-pressure fuel hazards.

**Confidence: MEDIUM-HIGH** - mechanisms are well documented; achieving 200-atmosphere injection pressure at Roman-adjacent tooling is the open question.

---

### en_supercharger - Supercharger (mechanically driven)

Also covers: en_turbocharger

**What it is / why you want it.** Forces extra air into a cylinder so more fuel can burn per stroke.

**Why you would never guess this.** Both machines do the identical job, raising power 30-50 percent (MEASURED), but draw the energy to do it from opposite places. A supercharger is driven directly off the crankshaft by belt or gear, always spinning with engine speed and responding instantly, at the direct cost of stealing some of the engine's own output to run itself. A turbocharger instead spins a turbine wheel in the engine's own exhaust stream, using energy that would otherwise be wasted out the tailpipe at no direct cost to the crankshaft - but its bearing must survive continuous temperatures above 800°C (MEASURED), a problem the supercharger never faces, and because it depends on exhaust flow building up, there is a characteristic lag before boost arrives.

**Prerequisites.** en_poppet_valve, cap_tol_10um; turbocharger additionally needs en_compression_ignition.

**Roman-available inputs.** Cast iron rotor housing; iron bar shafting.

**Procedure.** 1. Fit rotor compressor geared to crank (supercharger) or to a small exhaust turbine wheel (turbocharger). 2. Route compressed air to intake manifold. 3. Fit intercooler if boost is significant.

**How you know it worked.** Engine power increases measurably at the same fuel setting, confirmed by load test.

**Failure modes.** Over-boost without an intercooler overheats the charge and causes knock; turbocharger bearing seizes if oil supply is interrupted even briefly at that heat.

**Cost & labour.** ESTIMATED: turbocharger bearing and heat-resistant materials are the harder build; supercharger gearing is comparatively straightforward.

**Danger.** MEDIUM, exhaust-side components run hot enough to burn on contact.

**Confidence: MEDIUM** - the power-gain figure is well attested; turbocharger bearing life at Roman-adjacent metallurgy is genuinely uncertain.

---

### en_stirling_engine - Stirling hot air engine

Also covers: en_compressed_air_engine, en_spring_motor

**What it is / why you want it.** Three prime movers that trade efficiency for one specific practical advantage.

**Why you would never guess this.** In a Stirling engine, a fixed quantity of air is shuttled between a hot end and a cold end by a displacer piston, expanding when heated and contracting when cooled, with a regenerator recapturing heat from the air each pass - the heat source is entirely OUTSIDE the working gas, so it will run on any fuel that burns, or even stored heat, but real efficiency is only about 25 percent (MEASURED) against a theoretical 40 percent, because gas-to-metal heat transfer is inherently slow. Compressed air engine has no combustion in the engine at all: air compressed elsewhere expands in a cylinder exactly like steam, but that expansion is adiabatic (no heat added as it happens), so efficiency is only 40-50 percent, and the heavy storage vessel limits it to portable or mine work where an open flame is dangerous. Spring motor stores pure mechanical energy wound up before use, power and duration trading directly against each other, fine for a clock, useless for sustained industrial work.

**Prerequisites.** cap_heat_1100, cap_tol_100um; compressed air needs cap_power_steam, cap_tol_1mm; spring motor needs only cap_tol_1mm.

**Roman-available inputs.** Cast iron cylinders; copper for Stirling regenerator mesh; iron spring stock.

**Procedure.** 1. Build hot and cold cylinder ends linked by displacer and regenerator (Stirling). 2. Build storage vessel and expansion cylinder (compressed air). 3. Wind spring against a ratchet (spring motor).

**How you know it worked.** Stirling engine runs continuously on steady external heat; compressed air engine runs until storage pressure drops below useful minimum.

**Failure modes.** Stirling regenerator clogs or degrades, killing efficiency silently; compressed air vessel seam fails under repeated pressure cycling.

**Cost & labour.** ESTIMATED: Stirling engine is a demanding fit of matched hot and cold cylinders, weeks; the other two are comparatively simple.

**Danger.** LOW for all three, the safest cluster in this module.

**Confidence: HIGH** - all three are well documented, low-risk, historically real machines.

---

### en_gas_turbine - Gas turbine (Brayton cycle)

Also covers: en_jet_engine, en_rocket_motor, en_liquid_propellant

**What it is / why you want it.** The frontier this technology tree can reach but barely hold.

**Why you would never guess this.** A gas turbine compresses air through ten or more stages (MEASURED), burns fuel continuously in that compressed air rather than in pulses, and lets the hot gas expand through a turbine that drives its own compressor and delivers surplus power - combustor temperature runs above 900°C continuously (MEASURED), demanding nickel alloys that hold strength at that heat far longer than bronze or iron, without which the blades simply creep and fail. A jet engine is the same machine, extracting only enough turbine power to drive its own compressor and letting the rest of the hot gas expand out a nozzle at high velocity for thrust directly - it only makes sense at high speed and altitude, where a propeller has already lost effectiveness, and fuel consumption is enormous by any prior standard. A rocket motor carries its own oxidiser as well as fuel, so it needs no atmosphere at all, burning at 2000-3000°C (MEASURED) through a carefully shaped throat and nozzle. Liquid propellant systems must pump BOTH fuel and oxidiser to an injector head at a precisely matched ratio, and because a practical oxidiser (liquid oxygen or a strong acid) is intensely reactive, every wetted surface must resist corrosion no ordinary iron or bronze survives.

**Prerequisites.** cap_heat_1600, cap_tol_10um, boring_mill; jet engine needs en_gas_turbine; rocket needs cap_heat_2000, cap_tol_10um; liquid propellant needs en_rocket_motor.

**Roman-available inputs.** None of the core alloys (nickel superalloys, oxidiser-resistant linings) are Roman-native; treat this cluster as an end-state goal reached only after every other capability chain in this module is already mature.

**Procedure.** Not given in detail here - this cluster sits beyond the scope of a first working power system and depends entirely on capability nodes (cap_heat_1600 to 2000) documented elsewhere.

**How you know it worked.** Sustained, controlled combustion at rated temperature without blade creep or nozzle burn-through over repeated runs.

**Failure modes.** Blade creep and failure at sustained high temperature; propellant plumbing corrosion failure under reactive oxidisers.

**Cost & labour.** ESTIMATED: beyond ordinary artisan-hour accounting, a dedicated research programme.

**Danger.** HIGH - uncontained turbine or rocket failure at these temperatures and pressures is instantly lethal to anyone nearby.

**Confidence: LOW-MEDIUM** - the physics is textbook, but the materials and tolerances needed sit at or beyond the edge of what this tree's earlier metallurgy nodes can plausibly deliver.

---

### en_alternator - Alternator (AC generator)

Also covers: en_commutator, en_dynamo, en_exciter, en_three_phase_gen

**What it is / why you want it.** Turns rotation into electricity, in several different flavours depending on what you need the output to look like.

**Why you would never guess this.** Every rotating generator does the same basic thing (a coil moving through a magnetic field has voltage induced in it, proportional to speed), so this whole family is about what you do with that voltage afterward. An alternator brings the coil's raw output straight to slip rings unmodified: alternating current, both voltage and frequency scaling directly with rotation speed, which is why holding a generator's speed dead constant matters enormously the moment anything downstream depends on frequency. A commutator, a split metal ring reversing the external connection exactly in step with each half-turn, converts that same internal alternating voltage into pulsating direct current at the terminals - the brushes riding on it wear and arc constantly, worse the faster or harder-loaded the machine runs. A dynamo is simply a self-exciting commutator generator, already established elsewhere in this tree, referenced here only as the alternator's ancestor. An exciter is a small separate generator supplying magnetising current for a big machine's field coils, adjustable by a simple rheostat to trim the big machine's output voltage without touching its main circuit. Three-phase generation places three coils around the rotor, staggered so their peaks arrive in sequence, smoothing mechanical torque ripple and enabling efficient large industrial motors.

**Prerequisites.** cap_tol_10um, cap_power_steam; dynamo needs the existing dynamo tech; others build on en_alternator.

**Roman-available inputs.** Copper wire (already worked for coinage and fittings, drawn fine for windings); iron laminations for the core; lodestone or an existing dynamo for initial field excitation.

**Procedure.** 1. Wind coils on a rotating armature. 2. Fit slip rings (alternator) or a split commutator ring (dynamo). 3. For three-phase, wind three coil sets staggered 120 degrees apart.

**How you know it worked.** A test lamp or resistive load lights steadily as the shaft is turned at working speed.

**Failure modes.** Commutator brush wear and pitting causes sparking then loss of contact; bearing wear lets the rotor rub the stator, ruining the windings in seconds.

**Cost & labour.** ESTIMATED: precision winding is skilled, slow work, weeks per machine.

**Danger.** Electrical burns and fire from shorted windings; the magnetic field alone can pull loose iron tools into the machine violently.

**Confidence: HIGH** - basic generator principles are textbook electromagnetism.

---

### en_battery_lead_acid - Lead acid storage battery

Also covers: en_battery_nickel_iron

**What it is / why you want it.** Stores electricity as chemical energy so it can be released on demand, not only while a generator turns.

**Why you would never guess this.** Lead-acid uses lead and lead oxide plates in sulfuric acid, 2 volts per cell (six cells in series for a familiar 12 volts), 80-90 percent round-trip efficiency (MEASURED) - cheap materials, but the plates are damaged by deep discharge and overcharging boils the acid, releasing hydrogen and oxygen, a real explosion risk near any flame. Nickel-iron is a different chemistry entirely, more expensive, but far more tolerant of abuse: it survives overcharge and rough handling that would ruin lead-acid, lasting 5,000+ cycles (MEASURED) against a few hundred, at the cost of lower voltage per cell (1.2V) and faster self-discharge when idle.

**Prerequisites.** cap_tol_100um; nickel-iron additionally needs mat_nickel.

**Roman-available inputs.** Lead (plumbum, Britain and Spain); sulfuric acid (oil of vitriol, distilled from green vitriol, an established Roman-reachable process, see 20_chemistry.md); nickel is NOT a metal Rome smelted pure - flag this as the weak link.

**Procedure.** 1. Cast lead plates, positive and negative, of differing composition. 2. Assemble in acid-resistant cell case with dilute sulfuric acid electrolyte. 3. Charge slowly on first fill before drawing current.

**How you know it worked.** Cell holds a measurable voltage across terminals for hours after charging stops, tested by a simple electrolytic or spark test.

**Failure modes.** Overcharge gassing is a fire and explosion hazard in an enclosed room; prolonged undercharge sulfates the plates and permanently reduces capacity.

**Cost & labour.** ESTIMATED: lead casting is straightforward; acid handling requires trained, careful labour, days per battery bank.

**Danger.** Sulfuric acid is a severe skin and eye hazard; hydrogen accumulation in a sealed battery room is an explosion waiting for a spark.

**Confidence: HIGH for lead-acid** - basic electrochemistry and Roman-available vitriol are well established. **LOW for nickel-iron** - pure nickel supply is the real constraint.

---

### en_battery_charging - Battery charging system

Also covers: en_rotary_converter

**What it is / why you want it.** Keeps a storage battery correctly charged without cooking it.

**Why you would never guess this.** Charging voltage must sit just above the battery's own voltage plus wiring drop, and the correct value itself shifts with temperature, so a setting that is right in summer overcharges in winter - too high and you gas and ruin the battery, too low and it never fully charges. A rotary converter solves a different, older problem in a system with no separate rectifying device: a synchronous motor and a DC generator built on one shaft, so AC drives the motor half and the generator half delivers DC out the other end - elegant, but a synchronous motor has no starting torque of its own and must be brought to speed some other way first, which is why plain separate motor-generator pairs saw far wider use.

**Prerequisites.** en_battery_lead_acid, en_alternator; rotary converter needs en_alternator, en_three_phase_gen.

**Roman-available inputs.** Bronze rheostat contacts; copper wire.

**Procedure.** 1. Fit adjustable resistance in series with the charging circuit. 2. Set charge voltage by test-lamp brightness matched to a reference cell. 3. Monitor and reduce charge rate as the battery nears full.

**How you know it worked.** Battery reaches full charge without excessive gassing (visible bubbling) or heat by hand-test on the case.

**Failure modes.** Thermal runaway if charge voltage is not adjusted for a hot battery room; rotary converter fails to synchronise on startup and stalls.

**Cost & labour.** ESTIMATED: a fitter's afternoon to set up a charging rheostat correctly.

**Danger.** Same acid and gas hazards as the battery itself.

**Confidence: MEDIUM** - the voltage-temperature relationship is well known; exact set points depend on the specific cell.

---

### en_transmission_line - Transmission line (high voltage power cable)

Also covers: en_insulator, en_transformer

**What it is / why you want it.** Moves electrical power over distance without losing most of it as heat.

**Why you would never guess this.** Power lost in a wire scales with the CURRENT SQUARED times the wire's resistance, so for a fixed power delivered, doubling voltage halves current and cuts transmission losses to a quarter - this is the entire reason long lines run at high voltage, 10-100 kV (MEASURED), even though nothing downstream wants that voltage; it exists purely to shrink the current. The transformer, two coils sharing an iron core related by their turns ratio, is what makes this possible without generating at high voltage directly, stepping voltage up for the line and back down at the far end. An insulator, typically porcelain, holds the conductor away from its support, shaped with ribs and skirts to lengthen the surface path any leakage current would have to cross, since a straight air gap alone is not enough once the line is dirty or wet.

**Prerequisites.** en_alternator, cap_tol_100um; transformer needs motor_transformer_ac.

**Roman-available inputs.** Copper cable, stranded for flexibility; porcelain (needs kaolin clay and a high, controlled fire, see 30_glass_optics.md for comparable ceramic-firing precedent).

**Procedure.** 1. String stranded copper conductor on porcelain insulators atop poles or towers. 2. Fit step-up transformer at the generating end, step-down at delivery. 3. Test insulation resistance before energising.

**How you know it worked.** No audible hissing or visible corona glow at night along the line; voltage at the far end matches the expected drop for the distance.

**Failure modes.** Insulator surface contamination or a hairline crack lets current track across the surface (flashover); transformer winding insulation breaks down from age or overheating, shorting turns internally.

**Cost & labour.** ESTIMATED: copper cost dominates, scaling directly with distance; a specialist crew for stringing and testing.

**Danger.** HIGH - tens of kilovolts kills instantly on contact, and arcs at this voltage can jump many centimetres through open air.

**Confidence: HIGH** - the I-squared-R loss relationship is basic, well established physics.

---

### en_switchgear - Switchgear (high voltage switch)

Also covers: en_circuit_breaker, en_fuse, en_lightning_arrester

**What it is / why you want it.** Opens a high-voltage circuit safely, which is far harder than closing one.

**Why you would never guess this.** The instant contacts start to separate under load, the current tries to keep flowing as an arc across the gap, hot enough to weld the contacts back together or burn them away if not extinguished fast. Switchgear handles routine, deliberate switching, typically immersing contacts in oil to help quench the arc. A circuit breaker does the same job automatically, triggered by a thermal or magnetic sensing element at a set fault current, and unlike a fuse can be reset and reused, but must be rated to interrupt fault currents of thousands of amps far beyond its own normal load. A fuse is the oldest, simplest answer: a deliberately thin, precisely sized wire, silver alloy for corrosion and vibration resistance, that melts and breaks the circuit at a known current after a known delay, sacrificing itself once. A lightning arrester protects against a threat none of the others handle: a spark gap set to break down only above a defined surge voltage, shunting a strike's energy to earth, then critically must stop conducting again once the surge passes or it becomes a permanent short itself.

**Prerequisites.** en_transmission_line, cap_tol_100um; circuit breaker needs en_switchgear.

**Roman-available inputs.** Silver alloy fuse wire (argentum, mined in Spain); bronze switch contacts; oil (olive oil or mineral, for arc quenching) in an insulated vessel.

**Procedure.** 1. Build oil-immersed break contacts sized to the line's fault current. 2. Fit thermal or magnetic trip mechanism for the breaker. 3. Set fuse wire gauge to melt reliably below equipment damage thresholds.

**How you know it worked.** Deliberate test trip interrupts a simulated fault cleanly, with no sustained arc after contacts fully separate.

**Failure modes.** Switchgear oil carbonises from repeated arcing and loses quenching ability; a lightning arrester gap that fails to re-extinguish causes a sustained fault exactly when the line is most needed.

**Cost & labour.** ESTIMATED: a specialist electrical fitter, days per unit once components are cast and machined.

**Danger.** HIGH, same order as the transmission line itself.

**Confidence: MEDIUM-HIGH** - the arc-quenching principle is well established; exact interrupting capacity depends on build quality.

---

### en_substation - Substation (transformer station)

Also covers: en_grid_interconnection, en_frequency_standardisation, en_power_factor_correction, en_load_factor_diversity

**What it is / why you want it.** Where the abstractions of managing an electrical grid become physical machinery.

**Why you would never guess this.** A substation steps transmission voltage (order 50 kV) down to distribution (order 10 kV) and again to what actually reaches a building (roughly 400V), with several substations feeding one town in a mesh rather than a single chain (grid interconnection): if one line or generator fails, power reroutes rather than the whole area going dark, at the cost of needing careful fault analysis so a fault in one place cannot cascade into all of them. Frequency standardisation, settling on one number, 50 or 60 Hz (MEASURED as the two that emerged historically), exists because every generator on a shared grid must spin in exact lockstep, fighting every other generator if it drifts even slightly, so governors must hold speed tightly. Power factor correction addresses a subtler waste: inductive loads (motors) make current lag behind voltage, and that lagging current still heats wires and loads generators while delivering no useful work at the far end, so capacitor banks, which lead rather than lag, cancel it out. Load factor and diversity management is an accounting fact with real consequences: not every customer uses full power at once, so a system sized for the sum of every peak would be grossly oversized, real systems running at only 70-90 percent of that theoretical sum (MEASURED, standard diversity factor).

**Prerequisites.** en_switchgear, en_transformer; the other three all build on en_substation.

**Roman-available inputs.** Steel plate housing; mineral or vegetable oil for transformer cooling.

**Procedure.** 1. House step-down transformers, switchgear, and protection together at each distribution point. 2. Link substations in a mesh with more than one supply path each. 3. Add capacitor banks where inductive load (motors) dominates.

**How you know it worked.** Voltage at the far end of the town stays within a narrow band as load varies through the day.

**Failure modes.** Transformer oil overheats and can rupture catastrophically if cooling fails; generators out of frequency lockstep fight each other and can be torn apart mechanically.

**Cost & labour.** ESTIMATED: the largest single civil and electrical project in the distribution chain, a season's work for a full crew.

**Danger.** HIGH, combining every hazard already listed for transformers and switchgear at scale.

**Confidence: MEDIUM** - the individual mechanisms are well documented; the specific 50/60 Hz standard and diversity-factor range are period-specific historical conventions, not universal physical constants.

---

### en_hydroelectric_station - Hydroelectric power station

Also covers: en_thermal_station

**What it is / why you want it.** The largest possible integration of everything above it in this module.

**Why you would never guess this.** A hydroelectric station couples a turbine directly to an alternator feeding a substation, behind a dam that exists purely to manage water supply predictably rather than at the river's mercy; efficiency is very high, about 90 percent (MEASURED), because there is no combustion step to lose heat in, but the civil works dwarf the machinery in cost and time, and reservoir silting is a slow, unavoidable loss of capacity over decades. A thermal, coal-fired station instead chains boiler to turbine to alternator to substation, and losses compound at every stage - boiler efficiency around 80 percent, turbine around 40 percent, giving an overall efficiency of only about 32 percent (MEASURED) - most of the fuel's energy leaves as low-grade heat in the condenser cooling water, so the station needs enormous volumes of cooling water as much as it needs fuel, and coal handling plus ash disposal become an ongoing logistics operation, not a one-time build cost.

**Prerequisites.** Hydro: en_francis_turbine, en_alternator, en_substation. Thermal: en_steam_turbine_reaction, en_alternator, en_substation.

**Roman-available inputs.** Stone for dam and powerhouse (already a Roman strength, see hydraulic concrete precedent in other modules); coal, where a seam is mined locally (see fuel entries below).

**Procedure.** 1. Build dam and reservoir sized to smooth seasonal flow. 2. Site turbine hall at the base with direct alternator coupling. 3. For thermal, site boiler house adjacent to turbine hall with a large water source for condenser cooling.

**How you know it worked.** Output at the substation matches the calculated capacity within a small margin under steady load.

**Failure modes.** Reservoir silting slowly reduces effective head and capacity; thermal station cooling water shortage in drought forces output curtailment.

**Cost & labour.** ESTIMATED: the largest capital project in this entire module, years of dedicated labour and materials.

**Danger.** Dam failure is a catastrophic, mass-casualty event; a thermal station concentrates every steam and electrical hazard in this module onto one site.

**Confidence: HIGH** - the overall efficiency figures for both station types are well documented historical benchmarks.

---

### en_flywheel_storage - Flywheel energy storage

Also covers: en_pumped_storage

**What it is / why you want it.** Two very different ways to bank surplus power for later use.

**Why you would never guess this.** A flywheel stores energy as pure rotational motion, and the amount stored rises with the SQUARE of both radius and speed - a modest increase in rim speed or diameter buys a large increase in stored energy, which is exactly why a burst flywheel is so dangerous: that stored energy has to go somewhere instantly. It smooths short-term power ripple, seconds at most, evening an engine's individual power strokes into steady output, but cannot store energy for hours. Pumped storage does the opposite: a reversible turbine-pump lifts water into an upper reservoir when power is surplus and lets it fall back through the same machine run backwards when power is needed, round-trip efficiency about 75 percent (MEASURED), needing a real elevation difference, 100 metres is typical (MEASURED), and two reservoirs - but capable of storing a city's worth of energy for hours or days, the only method in this module that scales to that duration.

**Prerequisites.** Flywheel: cap_tol_100um, cap_power_steam. Pumped storage: en_hydroelectric_station.

**Roman-available inputs.** Cast iron flywheel rim, cast in one piece and tested for flaws before mounting; stone for a second reservoir.

**Procedure.** 1. Cast flywheel rim, inspect thoroughly for casting flaws before fitting to shaft. 2. Mount on a shaft with generous bearing margin. 3. For pumped storage, build an upper reservoir connected by penstock to a reversible turbine.

**How you know it worked.** Flywheel smooths visible speed fluctuation between individual engine strokes; pumped storage delivers power on demand by opening the penstock gate.

**Failure modes.** A hidden casting flaw or bearing seizure at speed causes the rim to fly apart, an explosion of solid metal; pumped storage reservoir leakage or a burst penstock is a flood risk to anything below it.

**Cost & labour.** ESTIMATED: flywheel casting and balancing, a specialist foundry task, weeks; pumped storage reservoir, a dam-scale civil project.

**Danger.** Flywheel failure is HIGH danger and famously hard to predict in advance; site pumped-storage reservoirs with the same care as any dam.

**Confidence: HIGH** - the energy-storage relationships for both are basic, well established physics.

---

### en_hydraulic_accumulator - Hydraulic accumulator

Also covers: en_hydraulic_power_main

**What it is / why you want it.** Distributes power around a city or factory as pressurised water, predating and rivalling electrical distribution.

**Why you would never guess this.** A steady pump charges an accumulator, a weighted or air-cushioned piston in a cylinder storing pressurised water, smoothing continuous pump output into pressure available on demand for bursts of heavy work - the precharge air or weight acts exactly like a mechanical spring, releasing stored pressure as flow drops. A hydraulic power main then extends this the way an electrical grid extends a generator: cast iron pipes carrying water at 600-1000 psi (MEASURED, real historical London and Manchester hydraulic power networks ran at this pressure) run through city streets to remote actuators lifting, clamping, or rotating, simpler and quieter than a maze of belts and shafting, though leakage and friction losses in the pipe network are considerably higher than an equivalent electrical circuit's resistive losses.

**Prerequisites.** cap_heat_1100, cap_tol_100um; power main needs en_hydraulic_accumulator.

**Roman-available inputs.** Cast iron pipe (a scaled continuation of Roman lead-pipe aqueduct plumbing, see 85_transport_civil.md); lead for seals and jointing.

**Procedure.** 1. Fit a weighted piston accumulator downstream of a steady pump. 2. Lay cast iron main to distribution points. 3. Fit local actuator cylinders at each point of use.

**How you know it worked.** Pressure at the far end of the main stays within useful range during a burst of demand.

**Failure modes.** A burst main floods streets and cuts off every actuator downstream at once; accumulator piston seal wear lets pressure bleed away when idle.

**Cost & labour.** ESTIMATED: pipe-laying dominates cost, scaling with the length of the network, a season's work for a large crew.

**Danger.** A burst high-pressure main can knock a person down or drive debris like a weapon; bleed accumulator pressure fully before working on it.

**Confidence: HIGH** - the historical London and Manchester hydraulic power companies are well documented working examples of this exact system.

---

### en_charcoal_burning - Charcoal production by burning

Also covers: en_peat_fuel, en_coal_mining_washing

**What it is / why you want it.** The fuel question underneath every machine in this module.

**Why you would never guess this.** A steam engine does not need coal. Charcoal is the default answer, and it is GROWN, not mined: managed coppice woodland yields roughly 0.75 tonnes of wood per hectare per year on a sustainable cutting cycle (ESTIMATED, basis: standard European coppice yield), so any serious ironworks or engine-building programme needs thousands of hectares of managed forest behind it, a land commitment, not a supply contract. Burning wood in a covered earth clamp or kiln with restricted air drives off water and volatile gases, leaving charcoal at about 25 percent of the original wood's weight (MEASURED) - hotter and cleaner burning than raw wood, but its bulk and cost per unit of heat stay worse than coal wherever coal is actually available. Peat is the fallback where neither wood nor coal is convenient: cut and air-dried over a full season, it delivers only about half of coal's energy per unit weight (MEASURED) and burns smoky and ashy, but needs no mining infrastructure at all, just a spade and a bog. Coal mining and washing is the alternative where a seam exists: raw coal carries 5-15 percent ash content even after washing (MEASURED) in a wet washery separating coal from denser rock, and unwashed, gritty coal will abrade and damage boiler tubes and mill machinery.

**Prerequisites.** cap_heat_1100; coal mining needs mining_concession.

**Roman-available inputs.** Managed coppice woodland (already a Roman agricultural practice, see 75_agriculture_food.md); bog peat (northern provinces, Britain, Germania); coal (Britain and a few continental seams were known to Rome, though barely exploited).

**Procedure.** 1. Stack cut wood in an earth-covered clamp, leaving a controlled air vent. 2. Fire and tend for one to several days, watching smoke colour to judge progress. 3. For peat, cut blocks and air-dry a full season before burning; for coal, wash in a flowing water trough to separate rock.

**How you know it worked.** Charcoal rings when struck and breaks with a clean, brittle fracture, not a fibrous one; dried peat crumbles rather than squeezing water.

**Failure modes.** A charcoal clamp catching full fire (rather than smouldering) burns the yield to ash; unwashed coal grit erodes machinery invisibly over months until sudden failure.

**Cost & labour.** ESTIMATED: charcoal burning, a burner and helper tending a clamp for days per batch; the land itself is the real, ongoing cost.

**Danger.** Charcoal burning risks carbon monoxide poisoning for anyone tending a clamp in an enclosed space; coal mining carries roof collapse and firedamp (methane) explosion risk underground.

**Confidence: HIGH** - coppice yield and charcoal conversion figures are standard, widely cited numbers.

---

### en_coke_oven - Coke oven (beehive or by-product)

Also covers: en_town_gas_retort, en_gas_holder, en_gas_producer

**What it is / why you want it.** One continuous chain: heating coal or wood without enough air to burn it releases gas while what remains concentrates into a cleaner solid fuel.

**Why you would never guess this.** A coke oven heats coal in a sealed or part-sealed chamber; a beehive oven just burns or discards the released gas, wasting it, while a by-product oven captures it, recovering tar, ammonia, and combustible gas for sale, leaving coke, nearly pure carbon plus ash, that burns hotter and cleaner than the coal it came from. Town gas retort takes that same driven-off gas as the actual product: it passes through cooling coils where tar condenses and drains, then through water where ammonia dissolves out (later recovered separately with lime), leaving a hydrogen-methane-carbon monoxide mixture piped for lighting and heat - the whole process consumes roughly 1.5 times as much energy in coal as the gas delivers (ESTIMATED, basis: typical historical retort energy accounting), a convenience fuel, not an efficient one. A gas holder stores that gas in a telescoping bell that rises and falls with volume, floating in a water seal that both prevents escape and self-regulates delivery pressure by the bell's own weight and height. A gas producer is the simpler, unrefined cousin fuelling an engine directly on site: fuel gas drawn up through a grate with limited air, a water-cooled scrubber stripping tars, needing no pipeline or gasometer at all.

**Prerequisites.** coal_coke (oven); en_coke_oven (retort); en_town_gas_retort (holder); cap_heat_1100 (producer).

**Roman-available inputs.** Coal or wood feedstock; cast iron oven and pipework; lead for gas holder seals.

**Procedure.** 1. Heat coal in a sealed chamber, collecting driven-off gas through cooling coils if by-product recovery is wanted. 2. Route gas through a water scrubber to strip ammonia and remaining tar. 3. Store finished gas under a floating bell in a water-sealed holder.

**How you know it worked.** Coke rings clean and grey when struck; gas burns with a steady flame at the holder outlet without soot.

**Failure modes.** Gas leaks are an asphyxiation and poisoning risk, carbon monoxide is odourless; a gas holder bell jamming off its guide can rupture the water seal and release a large gas cloud at once.

**Cost & labour.** ESTIMATED: a coke oven battery and gasworks is a substantial industrial installation, months to build, ongoing skilled labour to run.

**Danger.** HIGH - carbon monoxide poisoning and open-flame gas explosion are real, well documented hazards at every stage of this chain.

**Confidence: HIGH** - coking and town gas manufacture are extremely well documented nineteenth-century industrial processes.

---

### en_oil_drilling - Oil drilling and production

Also covers: en_oil_shale_retorting, en_oil_refining_distillation, en_oil_cracking

**What it is / why you want it.** Getting oil out of the ground and turning it into usable fractions, two separate problems with different failure modes.

**Why you would never guess this.** A cable-tool rig, a heavy bit repeatedly dropped and lifted, is simple to build but slow, while a rotary rig with circulating drilling mud, which both cools the bit and holds back whatever pressure the drill is about to hit, is faster for deep wells but far more complex to maintain - either way, well control is genuinely difficult, and an uncontrolled high-pressure pocket can blow the entire drilling apparatus back up the hole. Oil shale retorting is the fallback with no accessible liquid oil: shale heated to 500-600°C (MEASURED) in a sealed retort drives oil vapour out to condense and collect, at only 10-15 percent yield by weight (MEASURED), far more capital- and labour-intensive per unit of oil than drilling where crude already exists. Oil refining separates crude's mix of hydrocarbon chain lengths by boiling point in a column of bubble trays or packing, letting vapour and liquid repeatedly re-equilibrate as they pass, lighter fractions collecting near the top, heavier near the bottom, a clean separation between adjacent cuts being genuinely difficult even with a well-built column. Oil cracking deliberately breaks heavier, less useful long-chain molecules apart under heat into shorter, more valuable ones, increasing gasoline and kerosene yield, but the cracking furnace steadily accumulates carbon deposits (coking) on its own internal surfaces and needs regular shutdown and cleaning.

**Prerequisites.** cap_power_steam, cap_heat_1100 (drilling); en_oil_drilling, destructive_distillation (refining); en_oil_refining_distillation (shale retorting, cracking).

**Roman-available inputs.** Iron bar for drill string and casing; copper for retort and refining condensers; natural oil seeps were known and used by Romans in a few locations, though never systematically drilled.

**Procedure.** 1. Sink well by cable-tool percussion or rotary rig with circulating mud. 2. Route crude to a fractionating column, heated at the base, cooled and collected in trays by boiling range. 3. For shale, crush and heat rock in a sealed retort, condensing driven-off vapour.

**How you know it worked.** Distinct fractions collect at different tray levels, distinguishable by colour and viscosity between samples; retort yields visible oil condensate, not just water.

**Failure modes.** A drilling blowout is sudden and violent; retort or cracking furnace overheating warps or cokes the vessel; fractionating column contamination between cuts if trays are damaged or flooded.

**Cost & labour.** ESTIMATED: drilling a well is a season's dedicated crew and equipment; a refining column is a substantial ironworking and coppersmithing project on top of that.

**Danger.** HIGH for drilling (blowout, fire) and for cracking furnaces (high-temperature hydrocarbon vapour is a serious fire and explosion hazard at any leaking joint).

**Confidence: MEDIUM** - the chemistry and mechanics are textbook; achieving deep rotary drilling at Roman-adjacent tooling is genuinely uncertain.

---

### en_petrol - Petrol (gasoline) production

Also covers: en_kerosene, en_fuel_oil, en_lubricating_oil

**What it is / why you want it.** Four different cuts from the same refining process, each suited to a different job purely by its boiling-point range.

**Why you would never guess this.** Petrol, the lightest, most volatile cut, suits spark-ignited engines specifically because it vaporises quickly and burns cleanly, but that same volatility makes its vapour dangerously easy to ignite even at a distance from a visible flame, and its resistance to knocking (uncontrolled pre-ignition under compression) improves with aromatic hydrocarbon content, which depends on how the crude was refined, not automatic from the crude itself. Kerosene was originally refined purely for lighting, needing careful control of both flash point, so it does not ignite from ordinary handling, and purity, so it burns without smoking up the lamp glass, later repurposed as a heater and engine fuel. Fuel oil, the heavy, dense end of the barrel, is cheap because it is what remains after the valuable light fractions are taken out, but so viscous it must be heated before it will even flow through a pump in cold weather. Lubricating oil is not a fuel at all but essential to every moving machine in this module - viscosity and flash point matched to the duty, light oil for fast-turning machinery, heavy oil for slow, heavily loaded machinery, with paraffinic crudes giving the cheapest lubricants and naphthenic crudes giving oils with different cold-flow properties.

**Prerequisites.** en_oil_refining_distillation for all four.

**Roman-available inputs.** Refined crude oil fractions (see previous entry); no Roman name exists for any of these, they are entirely post-refining products.

**Procedure.** 1. Draw the desired boiling-range cut from the fractionating column. 2. Test flash point by controlled small-scale flame exposure at a safe distance. 3. Store each fraction in sealed, clearly marked vessels away from open flame.

**How you know it worked.** Petrol ignites readily from a small spark at a safe test distance; lubricating oil coats a test surface evenly without immediately draining off.

**Failure modes.** Petrol vapour pooling in a low, unventilated space and igniting from a spark yards away; fuel oil left unheated in cold weather simply will not flow, stalling a dependent engine; wrong-viscosity lubricant either fails to protect (too light) or adds drag and overheats bearings (too heavy).

**Cost & labour.** ESTIMATED: separation and testing labour, days per batch once the refining column itself exists.

**Danger.** Petrol vapour is the most acutely dangerous substance in this entire module, comparable to any explosive material documented elsewhere in the knowledge base.

**Confidence: HIGH** - refining fractions and their properties are extremely well documented.

---

## Sources and confidence

Water wheel and turbine efficiency figures trace to Smeaton's 1759 experiments and to well documented nineteenth-century turbine trials; these are HIGH confidence. Steam engine, boiler, and internal combustion figures (Newcomen's stroke rate, Watt's three-quarters fuel-waste measurement, compression ratios, superheat and economiser gains, turbine speeds and efficiencies) are drawn from standard, widely cited historical engineering figures and are HIGH confidence throughout. Electrical distribution figures (transmission voltage ranges, diversity factor, battery cycle life) are HIGH to MEDIUM, well documented but sometimes period- or design-specific rather than universal constants. The charcoal coppice yield and the town-gas energy-accounting figure are explicitly flagged ESTIMATED with their basis stated, per the hard rule against inventing numbers. The gas turbine, jet engine, and rocket cluster is LOW-MEDIUM confidence as a whole: the physics is textbook, but whether the required nickel alloys and machining tolerances are reachable from this tree's earlier metallurgy nodes is a genuinely open question, and this module does not pretend otherwise. Nowhere in this module is a number given without either a MEASURED, ESTIMATED, or DERIVED basis attached.

## Where to go next

- [93_energy.md](93_energy.md) - the base prime movers and fuels this module extends.
- [10_metallurgy.md](10_metallurgy.md) - cast iron, precision casting, and the alloys several entries above depend on.
- [40_power_precision.md](40_power_precision.md) - the boring mills and tolerance chains referenced throughout as prerequisites.
- [30_glass_optics.md](30_glass_optics.md) - porcelain and precision ceramic firing, relevant to insulators and rocket nozzle linings.
