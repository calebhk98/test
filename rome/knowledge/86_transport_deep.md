# Module 86: Transport, Deep Systems

You already have the railway. Module 85 gives you the freight arithmetic and the case for building one; Module 92 gives you the flanged wheel, the boiler, the sternpost rudder, the differential. None of that runs by itself. A working locomotive is not one invention, it is roughly two hundred small ones, and the one you skipped because it looked boring next to the boiler is the one that derails your train, freezes your axle, or drowns your dry dock. This module is the two hundred and eleven boring ones: the valve gear, the coupling, the bearing, the caulking seam, the signal interlock. None of them is glamorous. All of them are load-bearing, often literally.

Two hundred and eleven nodes, grouped into forty-six clusters by mechanism, because most of them are not independent inventions, they are the same idea applied to a slightly different joint. Learn the differential once and you understand every powered axle in this list. Learn the screw coupling once and you understand why every early railway in our world killed brakemen by the thousand. Each section below names one representative technology and lists the others it covers; check every id against the "Also covers" line before assuming something is missing.

A theme runs under all of it: a machine assembled from Roman-quality parts, at Roman tolerances, fails in Roman ways. Wrought iron fatigues where steel would flex. Hand-fitted parts do not interchange. A boiler built by a bronzesmith who has never worked with sustained internal pressure will, eventually, explode, and Rome's magistrates will read the wreckage as either witchcraft or sabotage. Read the Danger line on every entry, not as decoration.

---

### tl_differential - Differential (bevel gears)

Also covers: tl_live_axle, tl_dead_axle, tl_propshaft, tl_universal_joint

**What it is / why you want it.** A gear cluster inside a powered axle that lets the two wheels turn at different speeds while both still receive torque.

**Why you would never guess this.** Without it the inside wheel scrubs on every corner, or the axle itself winds up and snaps. A cart with two wheels rigidly fixed to one shaft can drift with a bit of slip; a heavy powered vehicle cannot, because the torque is too high and the scrub too costly. This is why a cart has "loose," independently-spinning wheels and a motor car needs an actual mechanism to do the same job under load. The propshaft carries drive from engine to axle; the universal joint lets that shaft bend as the axle moves on its springs without stripping. A dead axle (tl_dead_axle) carries no power at all, it just holds a wheel, which is simpler and is what you want on a trailer or a steered front axle before you add power there too.

**Prerequisites.** Bevel gear cutting (see 10_metallurgy.md for steel suitable for gear teeth), case hardening.

**Roman-available inputs.** Bloomery wrought iron for the housing; blister or crucible-import steel for the gear teeth and pins if you want wear life; olive oil or tallow as a crude gear lubricant.

**Procedure.** (1) Cut two bevel side gears and two to four small bevel pinions on a spider carrier. (2) Fit the carrier inside a cast or forged housing bolted to the axle. (3) Mesh gears by hand-filing until they roll without binding, checked by turning under load and feeling for hot spots. (4) Pack with grease, seal the housing.

**How you know it worked.** Jack up one wheel: it should spin freely while the other, on the ground, stays still. Drive the vehicle in a tight circle; no wheel should hop or drag.

**Failure modes.** Gear teeth chipped by hand-cut inaccuracy; housing cracks under sustained road shock; seized bearings from grit ingress without a seal.

**Cost & labour.** ESTIMATED (basis: comparable to fine clockwork/instrument gear-cutting) 15-30 artisan-days for a skilled bronze/iron worker per unit, plus a case-hardening furnace cycle.

**Danger.** Physical: a snapped propshaft under load can whip. Social: none, reads as clever carpentry to onlookers.

**Confidence: HIGH** - well documented 19th century mechanism, straightforward given case-hardened gear teeth.

---

### tl_ackermann_steering - Ackermann steering geometry

Also covers: tl_kingpin, tl_fifth_wheel

**What it is / why you want it.** A steering linkage that turns the inner front wheel through a sharper angle than the outer one, so both wheels' projected axes meet at a single point during a turn.

**Why you would never guess this.** Simple parallel-linked steering forces both front wheels to point the same direction, which is wrong geometry: the inner wheel needs a tighter arc. Without the correction, tyres scrub sideways in every turn, which is invisible on an iron-tyred cart at walking pace but expensive on rubber. The kingpin is the vertical pivot each steered wheel turns on; angle it back slightly (caster) and the wheel self-centres after a turn, the same trick a shopping-trolley castor uses. A fifth wheel is a different pivot entirely: a greased horizontal ring connecting a tractor to a trailer, letting the trailer swing independently.

**Prerequisites.** Basic mechanical linkage design, forged steel kingpins.

**Roman-available inputs.** Wrought iron or steel for pins and arms, bronze bushings.

**Procedure.** (1) Set the steering arms at an angle so their lines, extended, cross near the centre of the rear axle. (2) Connect arms with a track rod. (3) Mount each stub axle on a kingpin with slight backward lean.

**How you know it worked.** Chalk both front tyres, turn tightly on dry ground; both should leave clean unscrubbed lines, not smeared ones.

**Failure modes.** Wrong geometry causes tyre scrub and heavy steering; worn kingpin bushings cause wander.

**Cost & labour.** ESTIMATED 5-8 artisan-days per vehicle for a competent wheelwright-smith team.

**Danger.** A seized kingpin locks steering at speed. No social danger.

**Confidence: HIGH** - pure geometry, no exotic material needed.

---

### tl_leaf_spring - Leaf spring suspension

Also covers: tl_elliptic_spring, tl_coil_spring, tl_friction_damper, tl_hydraulic_shock

**What it is / why you want it.** A stack of curved steel strips (or a coiled wire, or a hydraulic cylinder) that stores road-shock energy and releases it slowly, sparing the vehicle frame and its cargo.

**Why you would never guess this.** A spring does not make the ride bouncier, it defers the impact: the longer a given force acts, the lower its peak stress on axle and frame. Left alone, a spring keeps oscillating after every bump; the friction damper (stacked leaves rubbing, or a sliding friction block) or the hydraulic shock (oil forced through a small orifice) bleeds that energy off so the vehicle settles rather than bouncing down the road. An elliptic spring is two leaf-spring arcs joined tip to tip for a smoother, lighter action than a single stack; a coil spring is the same stored-energy idea wound into a compact helix that fits inside an axle tube.

**Prerequisites.** Hardened, tempered spring steel (10_metallurgy.md).

**Roman-available inputs.** High-carbon bloomery iron, forge-quenched and tempered; oil for damper friction surfaces.

**Procedure.** (1) Forge strips, heat to cherry red (~800°C), quench in water, temper to straw yellow (~220°C). (2) Stack and clamp with a centre bolt. (3) Mount between axle and frame with shackles allowing the spring to lengthen as it flexes.

**How you know it worked.** Load the vehicle to its rated weight; the frame should settle a measured amount and stop, not keep bouncing after the road smooths out.

**Failure modes.** Over-hardening cracks the steel; under-hardening lets it sag permanently; a damper with no friction lets the vehicle porpoise.

**Cost & labour.** ESTIMATED 20-30 artisan-hours per spring set (matches 92_vehicles_flight.md's suspension_springs entry).

**Danger.** A snapped leaf under load whips; quenching risks steam burns.

**Confidence: HIGH** - continuous use since the 18th century, chemistry is textbook.

---

### tl_brake_shoe - Brake shoe on a drum

Also covers: tl_drum_brake, tl_disc_brake, tl_handbrake, tl_wire_rope_brake, tl_hydraulic_brake_line

**What it is / why you want it.** A friction surface pressed against a rotating wheel part to convert motion into heat and stop the vehicle.

**Why you would never guess this.** The limiting factor is never the friction, it is getting rid of the heat. A drum brake encloses the shoes, which keeps out mud but traps heat, so hard continuous braking (a long mountain descent) causes fade, the friction coefficient drops as the drum gets hot and the brake simply stops working. A disc brake exposes the friction surface to open air, cools by convection, and does not fade the same way, which is why it became the standard once discs could be made cheaply. A handbrake is a ratcheted cable or wire-rope pull (tl_wire_rope_brake) that holds the vehicle parked, independent of the main system. A hydraulic brake line replaces cables with liquid-filled tubing, guaranteeing equal pressure to every wheel at once, at the cost of needing airtight seals.

**Prerequisites.** Cast iron founding, leather or woven-fibre friction material.

**Roman-available inputs.** Cast iron for drums/discs, oak or leather for early friction linings, oil for hydraulic fluid (mineral oil is not available; use a heavy vegetable oil and expect seal trouble).

**Procedure.** (1) Cast a drum or disc onto the wheel hub. (2) Shape shoes or pads to the curve, line with a hard-wearing friction material. (3) Link to a lever or cable for actuation, tuned so a hand's force gives a firm stop.

**How you know it worked.** Loaded cart on a measured slope holds still with the handbrake set; repeated hard stops from speed show no lengthening stopping distance (fade).

**Failure modes.** Fade from overheating; glazed linings that stop biting; hydraulic lines that leak or trap air, giving a spongy, weak pedal.

**Cost & labour.** ESTIMATED 8-15 artisan-days per axle set depending on system.

**Danger.** Brake failure on a loaded descent is lethal; hot drums can burn bare skin on contact.

**Confidence: HIGH** for shoe/drum/disc mechanics; MEDIUM on hydraulic seal durability without synthetic rubber.

---

### tl_engine_block - Cast engine block

Also covers: tl_piston_assembly, tl_connecting_rod, tl_cam_follower

**What it is / why you want it.** The single casting that holds an internal combustion engine's cylinders, plus the reciprocating parts (piston, rod, cam follower) that turn expanding gas into rotation.

**Why you would never guess this.** A single casting with cored-in cooling passages eliminates dozens of joints that would otherwise leak; boring and honing the cylinder bores to a close tolerance afterward matters more than the casting itself, because a loose piston loses compression and a tight one seizes. The piston carries rings that seal combustion gas above and wipe oil below; the connecting rod's mass must be balanced end to end or the engine shakes itself apart at speed, an easy thing to get wrong by hand-forging. The cam follower rides the camshaft lobe and must be hard enough not to wear a groove into itself within days.

**Prerequisites.** Iron/bronze founding at scale, precision boring tools (see 40_power_precision.md), case hardening.

**Roman-available inputs.** Cast iron block, bronze or iron pistons, wrought iron or steel rods.

**Procedure.** (1) Cast block with cored water jacket. (2) Bore cylinders true with a rotating cutter fed slowly. (3) Fit rings to pistons, gap-check by inserting in a test ring gauge. (4) Balance rods by weighing and filing the heavy end.

**How you know it worked.** A finished piston, oiled and inserted without rings, should fall under its own weight with a slight resistance, not drop freely and not stick.

**Failure modes.** Porosity in the casting leaks coolant into the cylinder; unbalanced rods vibrate and crack; poor boring lets compression leak past rings.

**Cost & labour.** ESTIMATED (basis: comparable to a fine bronze cannon casting) 40-80 artisan-days for a first working block, falling sharply with practice.

**Danger.** Molten metal casting burns; a shattered flywheel or con-rod at speed is shrapnel.

**Confidence: MEDIUM** - founding and boring are attested Roman skills at smaller scale; scaling tolerance to engine-grade fits is the real unknown.

---

### tl_intake_valve - Poppet valve with cam and spring

Also covers: tl_exhaust_valve

**What it is / why you want it.** A spring-loaded disc that opens to admit fuel-air mixture (intake) or let burnt gas escape (exhaust), timed by a rotating cam.

**Why you would never guess this.** The exhaust valve is the hottest single part in the engine, directly in the combustion gas path every cycle; a plain iron valve will scale, warp and stop sealing within hours of running. It needs an alloy that holds its shape hot, which pushes you toward nickel or chromium additions rather than plain iron. Timing is equally unforgiving: a valve that opens or closes even slightly late kills power and can let the piston strike it.

**Prerequisites.** Alloy steel making (10_metallurgy.md), precision grinding.

**Roman-available inputs.** Iron alloyed where possible with available chromite or nickel-bearing ore (rare, mostly ESTIMATED unavailable at scale); expect frequent valve replacement as the practical Roman answer instead.

**Procedure.** (1) Forge valve with a wide seating face. (2) Grind seat and valve together with abrasive paste until a continuous ring mark shows contact. (3) Fit spring to snap valve shut quickly; set cam timing by trial, checking piston clearance.

**How you know it worked.** Engine idles smoothly with even exhaust note; a valve leak shows as a hiss at that cylinder when turned by hand through compression.

**Failure modes.** Warped exhaust valve leaks compression and burns through; weak spring lets valve "float" at speed and hit the piston.

**Cost & labour.** ESTIMATED 3-5 artisan-days per valve including seat-grinding.

**Danger.** A valve that drops into a cylinder wrecks the engine violently; no social danger.

**Confidence: MEDIUM** - mechanism is simple, exhaust-valve metallurgy is the weak link without alloy steel.

---

### tl_carburettor - Carburettor (fuel atomiser)

Also covers: tl_fuel_pump, tl_anti_siphon_valve, tl_throttle, tl_air_filter

**What it is / why you want it.** A device that meters liquid fuel into a moving airstream in the right ratio to burn, and the supporting parts that feed, filter and control that air.

**Why you would never guess this.** It works by the Bernoulli effect: air forced through a narrowed throat speeds up and its pressure drops, and that low pressure pulls fuel up a small tube from a float-controlled reservoir, so the mixture self-meters roughly in proportion to engine speed without any calculation. The float chamber is the whole trick, it holds fuel level constant regardless of tank level, the same way a cistern ballcock holds a fixed water level. An anti-siphon valve stops fuel draining into the cylinder when the engine is off and the tank sits above the carburettor. The air filter is unglamorous but essential in unpaved Roman conditions: unfiltered grit scores cylinder walls to death in days.

**Prerequisites.** Sheet brass or bronze work, precision small-orifice drilling.

**Roman-available inputs.** Bronze for the body and float, cork or hollow bronze for the float itself, woven wool or fine cloth as an air filter medium (a coarse but workable substitute for pleated paper).

**Procedure.** (1) Cast a body with a narrow throat (venturi). (2) Drill a fine fuel jet into the throat, fed from a float chamber held at constant level by a ballcock. (3) Fit a throttle plate to vary air volume, cable-linked to the driver's control.

**How you know it worked.** Engine runs evenly at a steady hand-throttle setting without surging or stalling; a black, sooty exhaust means too much fuel, a weak popping means too little.

**Failure modes.** Float stuck open floods the engine; clogged jet starves it; dirty filter chokes air and loses power.

**Cost & labour.** ESTIMATED 6-10 artisan-days for the carburettor body and jet-fitting by trial.

**Danger.** Raw fuel is flammable in the open float chamber; social reading is neutral, it looks like fine metalwork.

**Confidence: MEDIUM** - the venturi principle is solid physics; getting a consistent hand-drilled jet size is the practical bottleneck.

---

### tl_magneto_ignition - Magneto ignition

Also covers: tl_coil_ignition, tl_distributor, tl_spark_plug, tl_ignition_timing

**What it is / why you want it.** A way to generate a precisely timed high-voltage spark inside each cylinder to ignite the fuel-air mixture.

**Why you would never guess this.** A magneto generates its own current from engine rotation, no battery required, which matters enormously if you have no reliable storage battery yet (see tl_storage_battery below); a coil-ignition system instead steps up battery voltage through a transformer and is more reliable at very high revolutions once batteries exist. The distributor is a rotating switch, timed to the engine, that routes the spark to the correct cylinder in firing order; get the order wrong and the engine runs backward or not at all. Timing must also advance as engine speed rises, because the fuel-air mixture takes a roughly fixed time to burn and the spark must fire earlier, in crankshaft-degree terms, at higher speed to finish burning at the right piston position; a fixed, unadvanced spark simply loses power as revolutions climb.

**Prerequisites.** 50_electricity.md fundamentals (coils, magnets), ceramic insulator making (30_glass_optics.md for high-temperature ceramics).

**Roman-available inputs.** Iron for the magnet core, copper wire, a fired clay or fused-quartz insulator for the spark plug tip, which must withstand roughly 1000°C and the compression pressure without cracking.

**Procedure.** (1) Wind a coil around a soft iron core near a rotating permanent magnet. (2) Build a distributor with rotating brush contacts matched to cylinder count. (3) Fit a governor of spinning weights that shifts the spark timing earlier as speed rises. (4) Fit spark plugs with a precisely filed gap.

**How you know it worked.** A spark held near, but not touching, a grounded point should jump a visible, audible gap in daylight shade.

**Failure modes.** Fouled or cracked plug insulator misfires; distributor timed wrong runs the engine backward or not at all; weak magnet gives a weak, unreliable spark.

**Cost & labour.** ESTIMATED 15-25 artisan-days combining fine ironwork, winding and ceramic firing.

**Danger.** High voltage gives a sharp but rarely lethal shock; fouled plugs near spilled fuel are a fire risk.

**Confidence: MEDIUM** - electromagnetics are attested (see 50_electricity.md), but a reliable high-temperature ceramic insulator at this scale is the weak link.

---

### tl_radiator - Radiator water cooling

Also covers: tl_water_pump, tl_thermostat, tl_fan_belt, tl_cooling_fan

**What it is / why you want it.** A finned heat exchanger, plus pump, fan and thermostat, that keeps an engine at a stable working temperature under load.

**Why you would never guess this.** An engine actually needs to run hot, not cold; run it too cool and fuel does not vaporise properly and cylinder wear accelerates, which is the entire reason for the thermostat, a wax-filled valve that stays shut until the coolant reaches roughly 82°C and only then opens to let water circulate through the radiator. Without it the engine spends its whole warm-up period running rich and dirty. The fan, driven off the crankshaft by a belt, pulls extra air through the radiator at low road speed when the vehicle's own motion is not enough, but a fan spinning constantly at full engine speed wastes real power, hence later designs that let it slip when not needed.

**Prerequisites.** Thin sheet-metal work, brazing.

**Roman-available inputs.** Copper or bronze sheet and tube for the radiator core (copper is Cyprus/Spain sourced), wax for the thermostat element, leather or woven belting for the fan drive.

**Procedure.** (1) Build a finned copper core, brazed joints. (2) Fit a simple paddle-wheel pump driven off the engine to force water through. (3) Cast a wax-pellet valve that expands to open a passage near boiling-adjacent temperature. (4) Belt-drive a fan blowing through the core.

**How you know it worked.** Engine run under load holds a steady temperature (test by touch through a cloth, or watch for steam) rather than climbing continuously or never warming up.

**Failure modes.** Blocked core from mineral scale in hard water; belt slip stops the fan and pump together; stuck-shut thermostat overheats the engine fast.

**Cost & labour.** ESTIMATED 10-18 artisan-days for the full system.

**Danger.** A pressurised hot system sprays scalding water if opened while hot; no social danger.

**Confidence: HIGH** - straightforward heat exchange, well within Roman brazing skill.

---

### tl_oil_pump - Pressure oil pump

Also covers: tl_pressure_relief_valve, tl_transmission_lubrication

**What it is / why you want it.** A gear or plunger pump that forces oil under pressure to bearings and moving parts, rather than relying on splash alone.

**Why you would never guess this.** Splash lubrication, oil thrown up by spinning gears, works for a slow cart gearbox but starves a fast-spinning engine bearing under load; pressure feed guarantees a fresh film reaches the bearing before it can run dry and score. The pressure relief valve is the unglamorous safety part: without it, pump pressure would climb without limit as the engine speeds up, so a spring-loaded valve bleeds excess oil back to the sump once a set pressure is reached, holding the system in a safe, roughly constant band.

**Prerequisites.** Precision gear cutting, spring making.

**Roman-available inputs.** Bronze gears for the pump, olive oil or, better, a heavier mineral oil if bitumen-derived oils are being refined (see 93_energy.md on petroleum), steel spring for the relief valve.

**Procedure.** (1) Cut two meshing gears in a close-fitting housing; oil is carried in the tooth spaces and squeezed out at the outlet. (2) Drill galleries to each bearing. (3) Fit a spring-loaded ball or disc valve set to open at the target pressure, found by trial.

**How you know it worked.** Disconnect a bearing feed line while the engine idles slowly; oil should flow steadily, not dribble or surge erratically.

**Failure modes.** Worn gears lose pressure; a stuck relief valve either starves the system or blows a seal; sludge from dirty oil clogs galleries.

**Cost & labour.** ESTIMATED 8-12 artisan-days.

**Danger.** Hot oil under pressure sprays if a line bursts; no social danger.

**Confidence: HIGH** - simple positive-displacement pump, well within Roman gear-cutting capability once tolerances are controlled.

---

### tl_plate_clutch - Plate clutch and gearbox

Also covers: tl_cone_clutch, tl_sliding_gearbox, tl_synchromesh, tl_epicyclic_gearbox, tl_automatic_transmission

**What it is / why you want it.** A friction device to connect and disconnect engine from wheels smoothly, and a set of gears to trade speed for torque.

**Why you would never guess this.** An engine cannot be bolted directly to a moving wheel, it would stall the instant you tried to start from rest, so something must be able to slip briefly while transmitting rising torque. A cone clutch does this with a matched conical friction surface, simple to make but prone to grabbing; a flat plate clutch is gentler to engage. A sliding gearbox works by physically moving toothed gears into and out of mesh, which crashes and grinds unless engine and gear speeds are matched by ear before the shift (double-clutching); synchromesh solves this by using a friction ring to spin the incoming gear up or down to match before the teeth engage, which is why it shifts cleanly. An epicyclic (planetary) gearbox achieves different ratios just by locking different parts of one compact gear cluster, which is why it is so small for its ratio range, and it is the basis of a hydraulic automatic transmission, where a fluid coupling replaces the clutch entirely.

**Prerequisites.** Precision gear cutting, spring steel for clutch plates.

**Roman-available inputs.** Iron/steel gears, woven wool or leather clutch facing, bronze bushings.

**Procedure.** (1) Cut a set of gear pairs giving 3-4 useful ratios. (2) Mount on parallel shafts with sliding dogs or, for synchromesh, add friction cones ahead of each gear. (3) Build a plate clutch: two friction-faced discs squeezed by a spring, released by a pedal-operated lever.

**How you know it worked.** Vehicle pulls away from rest without stalling or violent jerking; gears engage without grinding once the driver learns the rev-matched shift.

**Failure modes.** Clutch slip from worn or oil-soaked facings; crashed gears from mistimed shifts wearing tooth tips; synchromesh rings wearing smooth and losing their bite.

**Cost & labour.** ESTIMATED 20-40 artisan-days for a multi-speed gearbox with clutch.

**Danger.** A seized clutch can stall a vehicle in traffic dangerously; no social danger.

**Confidence: MEDIUM** - gear cutting is attested, synchromesh-grade tolerance is a real stretch without machine tools (see 40_power_precision.md).

---

### tl_dynamo - Dynamo and electric starting

Also covers: tl_motor_dc, tl_storage_battery, tl_electric_starter

**What it is / why you want it.** A generator driven by the engine to produce electric current, a motor that can be run in reverse to use it, a battery to store it, and a starter motor that uses stored charge to spin the engine to life without hand-cranking.

**Why you would never guess this.** A DC motor and a DC dynamo are the same machine used in opposite directions; the starter motor is simply a motor sized to briefly deliver enormous torque, disengaging automatically the instant the engine fires so it is not spun far beyond its safe speed. A lead-acid storage battery works by a genuinely counterintuitive reaction: charging converts lead sulfate on one plate to spongy lead and on the other to lead dioxide, discharging reverses it, and the whole thing needs periodic "watering" as the water in the acid electrolyte is consumed by the chemistry.

**Prerequisites.** 50_electricity.md (coils, commutators), lead and sulfuric acid (20_chemistry.md, and lead is a standard Roman metal from Spanish and British mines).

**Roman-available inputs.** Copper wire, iron cores, lead plates, sulfuric acid (vitriol, distilled from green vitriol/copperas, already a known Roman substance).

**Procedure.** (1) Wind armature and field coils, fit a commutator of copper segments. (2) Assemble lead plates in a glass or lead-lined wooden cell, fill with dilute sulfuric acid. (3) Charge from the dynamo until plates show the expected colour change (grey lead, dark brown dioxide). (4) Gear the starter motor to the engine flywheel through an overrunning clutch that disengages once running.

**How you know it worked.** Battery under charge shows gas bubbles rising steadily; a charged cell measured by taste-testing acid density (a crude but real Roman-usable proxy, denser acid tastes and feels heavier, and floats a test object at a known point) confirms state of charge.

**Failure modes.** Sulfuric acid burns badly on skin; overcharging boils the electrolyte dry; a shorted commutator segment overheats and can start a fire.

**Cost & labour.** ESTIMATED 30-50 artisan-days for the full charging and starting system.

**Danger.** Concentrated sulfuric acid causes severe chemical burns; hydrogen gas released while charging is explosive near open flame, ventilate the charging room.

**Confidence: MEDIUM** - electromagnetics are attested territory, lead-acid chemistry is textbook, but sustained-quality battery plates are a real manufacturing challenge.

---

### tl_headlamp - Headlamp and signal lighting

Also covers: tl_carbide_lamp, tl_indicator

**What it is / why you want it.** Lighting to see the road at night and to signal intentions to other traffic.

**Why you would never guess this.** A carbide lamp is chemistry, not electricity: calcium carbide dripped with water releases acetylene gas, which burns with a bright white flame, and it works with zero electrical infrastructure, which makes it the obvious first headlamp for any vehicle without a dynamo yet. An electric headlamp needs a shaped reflector behind the bulb to throw a useful beam rather than a diffuse glow, and a dip/main switch to avoid blinding oncoming traffic. An indicator is a simple flashing relay, current interrupted rhythmically by a heat-driven or mechanical switch, or in the simplest form a folding mechanical arm the driver raises by hand.

**Prerequisites.** Calcium carbide production (a lime and carbon reaction in an electric arc furnace, 50_electricity.md/93_energy.md), reflective metal polishing.

**Roman-available inputs.** Lime and charcoal for carbide (needs an electric arc furnace, a real prerequisite gap), polished bronze or silvered glass for reflectors.

**Procedure.** (1) For a carbide lamp: build a two-chamber brass lamp, water drips onto carbide below, gas rises to a burner jet, ignite. (2) For electric: shape a parabolic reflector, mount a bulb or arc at its focus.

**How you know it worked.** Carbide lamp gives a steady bright flame from a controlled drip rate, not a sputtering or roaring one.

**Failure modes.** Carbide lamp flares dangerously if water flow is unregulated; damp carbide stock degrades in storage; a cracked reflector scatters the beam uselessly.

**Cost & labour.** ESTIMATED 4-8 artisan-days per lamp.

**Danger.** Acetylene is flammable and can flash back into the generator chamber if the jet clogs; treat the lamp with the same respect as an open flame.

**Confidence: MEDIUM** - carbide lamp chemistry is simple; the arc furnace needed to make calcium carbide in the first place is a genuine prerequisite (see 93_energy.md).

---

### tl_muffler - Muffler and windscreen wiper

Also covers: tl_windscreen_wiper

**What it is / why you want it.** A silencer that reduces engine exhaust noise, and a blade that clears rain from a windscreen.

**Why you would never guess this.** Neither is subtle engineering, and that is the point: an unsilenced internal combustion engine is startlingly loud, loud enough to spook every draft animal on the road and read as an attack to any nearby garrison, so a baffled expansion chamber in the exhaust is a social necessity as much as a comfort one. It works by breaking the exhaust pulses into smaller, out-of-phase pulses inside a chambered box, at a real cost in backpressure and lost power. A windscreen wiper only matters once you have added glass to a vehicle at all (30_glass_optics.md); a simple cam-driven arm swept by a linkage off the engine or a hand crank is entirely sufficient.

**Prerequisites.** Sheet metalwork; glazing for the windscreen the wiper serves.

**Roman-available inputs.** Iron or bronze sheet for baffles, soft rubber substitute (leather, oiled and softened) for the wiper blade if true vulcanized rubber (tl_vulcanized_rubber) is unavailable.

**Procedure.** (1) Build a chambered box with internal baffle plates the exhaust must snake through. (2) For the wiper, mount a cam on a slow-turning shaft, linked to an arm pressing a flexible blade against the glass.

**How you know it worked.** Engine note drops from a sharp bark to a muted rumble; wiper clears a wetted glass pane in a single sweep without streaking.

**Failure modes.** A muffler baffle that chokes flow too much overheats the engine and kills power; a stiff wiper blade scratches glass.

**Cost & labour.** ESTIMATED 3-6 artisan-days combined.

**Danger.** None significant; social value of the muffler is real, an unsilenced engine will draw a magistrate's attention fast.

**Confidence: HIGH** - both are simple mechanical fixes with no exotic material requirement.

---

### tl_motor_lorry - Motor lorry and heavy road vehicles

Also covers: tl_articulated_trailer, tl_tractor, tl_caterpillar_track, tl_half_track, tl_snow_plough

**What it is / why you want it.** Powered vehicles built to move heavy loads over varied ground: the truck for roads, the tractor for fields, the tracked and half-tracked vehicle for soft or broken ground.

**Why you would never guess this.** A wheel concentrates a vehicle's weight onto a small contact patch and sinks into soft ground; a caterpillar track spreads that same weight over a long footprint, which is why a tracked vehicle crosses mud and sand a wheeled one cannot, at the cost of far higher friction losses and maintenance on every road mile. A half-track is a deliberate compromise, wheels for steering and road speed at the front, tracks for traction at the rear, cheaper and faster on roads than full tracks. An articulated trailer, joined to its tractor by a fifth wheel, lets a very long combined vehicle still turn a normal street corner, because the pivot point moves the effective wheelbase.

**Prerequisites.** tl_differential, tl_leaf_spring, tl_plate_clutch, tl_pneumatic_tyre or tl_solid_rubber_tyre.

**Roman-available inputs.** Iron/steel for chassis and track links, timber or leather for early rubber-scarce tracks, iron plough shares for the tractor's implements.

**Procedure.** (1) Build a strong ladder chassis. (2) Fit the drivetrain cluster (engine, clutch, gearbox, differential) already covered above. (3) For tracks, link steel plates over drive and idler sprockets with a taut top run.

**How you know it worked.** Loaded lorry climbs a measured grade without stalling; a tracked vehicle crosses soft ploughed earth a wheeled cart of equal weight bogs down in.

**Failure modes.** Track links wear and stretch, eventually throwing the track off its sprockets; overloaded chassis frames crack at weld or rivet points.

**Cost & labour.** ESTIMATED (basis: sum of component clusters above plus chassis fabrication) 60-120 artisan-days per vehicle.

**Danger.** A heavy vehicle out of control is a serious hazard on Roman roads built for foot and animal traffic; expect magistrates to regulate speed and hours quickly.

**Confidence: MEDIUM** - depends on every upstream drivetrain component being solved first.

---

### tl_omnibus - Omnibus and public road/rail transit

Also covers: tl_motorcycle, tl_horse_tram, tl_steam_tram, tl_electric_tram, tl_trolleybus

**What it is / why you want it.** Vehicles built to move many passengers along fixed or semi-fixed routes: the sprung horse-drawn omnibus, the two-wheeled motorcycle, and the family of trams and trolleybuses that graduate from horse to steam to electric power.

**Why you would never guess this.** A horse tram is not about the horse, it is about the rail: a horse pulling a cart on a smooth iron rail moves several times the load it can pull on a rutted road, because rolling resistance on steel-on-steel is a fraction of steel-on-dirt, so putting the same horse on rails multiplies its useful hauling capacity before any engine is involved. A steam tram then swaps the horse for a small enclosed engine, and an electric tram swaps the boiler for a motor drawing current from an overhead wire through a trolley pole, quieter and cleaner but demanding a citywide power network first. A trolleybus takes the electric tram's motor and power pickup and puts it on rubber tyres with no rails at all, trading route flexibility for a slightly more complex twin-pole current collection.

**Prerequisites.** tl_iron_tyre or tl_pneumatic_tyre, tl_dynamo/tl_motor_dc for electric variants, tr_catenary_overhead for trolley power.

**Roman-available inputs.** Iron rail (existing Roman ironwork scaled up), sprung wooden bodywork, copper overhead wire for electric versions.

**Procedure.** (1) Lay a smooth iron rail in the roadway. (2) Build a sprung, low-floor car body. (3) For steam or electric variants, add the relevant power cluster from elsewhere in this module.

**How you know it worked.** A tram horse pulls a full load of passengers at a trot without distress, where the same horse would struggle on plain paving.

**Failure modes.** Rail-street mud fouls the horse's footing at crossings; steam trams foul streets with coal dust and sparks; electric systems fail wholesale if the generating station goes down.

**Cost & labour.** ESTIMATED (basis: rail-laying cost per Module 85's railway entry, scaled down for city street rail) substantial civic capital, best read alongside 85_transport_civil.md.

**Danger.** Social: a fixed rail line in a Roman street is an unmistakably permanent claim on public space, expect political negotiation before technical difficulty.

**Confidence: HIGH** for horse tram; MEDIUM for steam/electric, which depend on upstream power modules.

---

### tl_spoked_wheel - Improved spoked and wire-spoke wheel

Also covers: tl_wire_spoke_wheel, tl_iron_tyre, tl_shrink_fit

**What it is / why you want it.** A wheel built from a hub, spokes and rim rather than a solid disc, with the rim protected by a shrink-fitted iron band.

**Why you would never guess this.** A shrink-fit tyre is not just a hard wear surface, it is a structural clamp: the iron band is forged slightly smaller than the wooden rim, heated until it expands enough to slip on, then quenched, and as it cools it contracts and squeezes the whole wheel together under permanent tension, holding loose joints tight that would otherwise rattle apart. Get the temperature wrong and the band either will not fit or splits the wood as it shrinks. A wire-spoke wheel takes the same tension idea further: thin wire spokes, useless in compression, hold the rim true purely by being pulled taut in every direction at once, which is why the wheel can be far lighter than a solid-spoke wood wheel of equal strength, but only once you can tension wire spokes evenly with a jig.

**Prerequisites.** Iron banding and forge work (already routine, see 85_transport_civil.md's road_improvements entry).

**Roman-available inputs.** Seasoned oak or elm for the wheel, wrought iron for the tyre band, iron or bronze wire drawn fine for wire spokes.

**Procedure.** (1) Forge the iron band to a diameter slightly under the wheel rim. (2) Heat evenly to a dull red, expanding it a few percent. (3) Drop it onto the wheel and quench immediately with water, working around the circle so it cools evenly.

**How you know it worked.** Struck with a mallet, a properly shrunk tyre rings clean and tight; a loose one gives a dull, rattling knock.

**Failure modes.** Uneven quenching warps the wheel; overheating burns the wood underneath; a wire wheel with uneven spoke tension goes out of true and wobbles.

**Cost & labour.** MEASURED-adjacent: Roman shrink-fit iron tyres are already standard practice; wire spoke lacing is ESTIMATED at 2-4 artisan-days per wheel with a proper jig.

**Danger.** Handling red-hot iron bands near dry wood is a fire risk; no social danger.

**Confidence: HIGH** - shrink-fit tyres are already Roman practice; wire spokes are a direct, low-risk extension.

---

### tl_pneumatic_tyre - Pneumatic tyre

Also covers: tl_inner_tube, tl_tyre_bead, tl_tyre_tread, tl_vulcanized_rubber, tl_solid_rubber_tyre

**What it is / why you want it.** A tyre with a sealed, air-filled inner tube instead of solid rubber or bare iron.

**Why you would never guess this.** The win is not comfort, it is energy. A rigid iron tyre or even a solid rubber one deforms the road surface (and itself) slightly at every bump, and that deformation eats energy that never comes back; a rolling cushion of compressed air instead flexes and returns nearly all of that energy elastically, which is why switching to pneumatic tyres roughly doubled achievable bicycle speed for the same rider effort before it ever reached a car. None of it works without vulcanization: raw rubber is sticky in heat and brittle in cold, useless as a durable material, and heating it with sulfur cross-links the long rubber molecules into a network that stays elastic across a wide temperature range. The tyre bead is a stiff, barely-stretching cord ring at each edge that keeps the tyre seated on the rim under internal pressure; without it, pressure alone would pop the tyre off the rim. Tread pattern grooves clear water from the contact patch; on a dry Roman road, a smooth tyre grips just as well, tread mainly matters once you have wet macadam or worse.

**Prerequisites.** Rubber supply (a genuine gap, see 95_expeditions.md), sulfur (native Sicilian sulfur, already Roman-known).

**Roman-available inputs.** Latex rubber is not native to the Roman world; it must come via expedition to West Africa or, at ruinous cost, via Far Eastern trade routes (95_expeditions.md). Sulfur from Sicily. Woven cloth or cord for the bead and tread reinforcement.

**Procedure.** (1) Mix raw latex rubber with roughly 5-8 percent sulfur by weight. (2) Shape around a cord-reinforced bead ring in a mould. (3) Heat to around 140-160°C for an hour or more until the rubber no longer feels sticky and springs back sharply when dented. (4) Fit an inner tube with a valve stem, inflate, seat on the rim.

**How you know it worked.** A vulcanized sample bent double at room temperature springs straight back with no crack; an unvulcanized sample stays sticky in the sun and cracks in the cold.

**Failure modes.** Under-vulcanized rubber stays gummy and swells with oil contact; over-vulcanized rubber goes hard and cracks; a pinch flat occurs when the tube is squeezed between rim and an obstacle at low pressure.

**Cost & labour.** ESTIMATED (basis: rubber is an imported, expedition-sourced good, see 95_expeditions.md pricing logic) high per-unit cost until a controlled supply chain exists; solid rubber tyres are a cheaper, heavier fallback usable on trams and heavy carts sooner.

**Danger.** Sulfur fumes during vulcanization are unpleasant and mildly toxic in a closed room, work ventilated; a burst tyre under pressure can injure.

**Confidence: HIGH** on the chemistry once rubber is in hand; LOW on the supply chain timeline, which depends entirely on the expedition described in 95_expeditions.md.

---

### tl_ball_bearing - Ball, roller and taper bearings

Also covers: tl_roller_bearing, tl_taper_roller_bearing, tl_plain_bearing, tl_oil_bath, tl_grease_cup

**What it is / why you want it.** A bearing surface built from hardened rolling elements, or in the simplest case a plain sliding bronze bush, to let an axle turn with minimum friction and wear.

**Why you would never guess this.** A plain bearing (bronze sleeve around a steel shaft) is already good practice, standard on Roman cart axles, and it works by letting the softer bronze wear instead of the shaft, replaceable at low cost; its friction is still fairly high, and rolling contact cuts that friction by roughly a hundredfold. Rolling contact only works, though, if the balls or rollers and their races are hardened and round to a fine tolerance, because any high spot concentrates the entire load onto a point and dents the race under repeated stress, called Hertzian fatigue. A taper roller bearing angles its rollers so the bearing carries sideways (thrust) load as well as radial load in one unit, which is exactly what a steered wheel hub needs. Oil bath and grease cup are the low-tech maintenance answer for the plain bearings you will keep using everywhere rolling bearings are not worth the cost: a grease cup is a simple screw-plunger reservoir a driver tops up by hand, forcing fresh grease in and pushing old, grit-laden grease out the far end.

**Prerequisites.** Hardened, ground steel spheres/rollers (10_metallurgy.md, 40_power_precision.md).

**Roman-available inputs.** Bronze for plain bushings, hardened steel for rolling elements, tallow or grease for lubrication.

**Procedure.** (1) For plain bearings: cast or turn a bronze sleeve to fit the shaft with a thin, consistent oil-film clearance. (2) For rolling bearings: grind steel balls or rollers round within a fine tolerance, checked by rolling between two flat plates and feeling for wobble, and fit into hardened races.

**How you know it worked.** A properly fitted bearing turns freely by hand with no roughness or grinding feel, and stays cool to the touch after sustained running.

**Failure modes.** Starved lubrication scores a plain bearing or spalls a rolling one; grit ingress through a bad seal accelerates wear; an out-of-round rolling element vibrates audibly.

**Cost & labour.** ESTIMATED 1-3 artisan-days per plain bushing; 10-20 per rolling bearing set given the grinding precision required.

**Danger.** None significant; purely mechanical.

**Confidence: HIGH** for plain bearings (already Roman practice); MEDIUM for rolling bearings, which need grinding precision beyond typical hand-forge tolerance.

---

### tl_safety_bicycle - Safety bicycle and its ancestors

Also covers: tl_velocipede, tl_penny_farthing

**What it is / why you want it.** The evolution from a direct-drive pedal wheel to the low, chain-driven, equal-wheeled bicycle recognisable today.

**Why you would never guess this.** A velocipede drives its front wheel directly from pedals on its axle, so one pedal revolution moves the bicycle exactly one wheel circumference; the only way to go faster without pedalling absurdly fast is to make the wheel bigger, which is exactly what the penny-farthing does, and it is precisely why that wheel became enormous and the rider perched dangerously high above it, prone to pitching forward over the front ("taking a header") on any sudden stop. The safety bicycle breaks that link entirely with a chain and sprockets (see tl_chain_drive below), letting a normal-sized wheel be driven at a useful gear ratio, so the rider sits low, stable and safe, which is the whole point of the name.

**Prerequisites.** tl_chain_drive, tl_spoked_wheel, ideally tl_pneumatic_tyre.

**Roman-available inputs.** Iron/steel tube frame, wire or wood spoked wheels.

**Procedure.** (1) Build a diamond-shaped tube frame low to the ground. (2) Fit equal-sized wheels front and rear. (3) Drive the rear wheel by chain from a pedal crank geared for a comfortable cadence.

**How you know it worked.** A rider can mount, ride, and dismount without special skill or a mounting step, unlike a penny-farthing.

**Failure modes.** Frame joints fail under repeated flex if brazing is poor; chain skips off worn sprockets.

**Cost & labour.** ESTIMATED 10-15 artisan-days per bicycle.

**Danger.** Low social danger, though a fast, silent vehicle among pedestrians and cart traffic will need traffic rules invented alongside it.

**Confidence: HIGH** - well within Roman metalworking once chain drive exists.

---

### tl_chain_drive - Chain drive, freewheel and gearing

Also covers: tl_freewheel, tl_derailleur, tl_hub_gear, tl_caliper_brake

**What it is / why you want it.** A roller chain connecting two toothed sprockets, letting the pedal-crank size and the wheel size be chosen independently, plus the mechanisms that let the wheel coast and change gear.

**Why you would never guess this.** A freewheel is a ratchet: it lets the rear wheel spin faster than the pedals so a rider can coast downhill without their feet being flung around by the pedals, an easy thing to take for granted once you have ridden a modern bicycle and a genuine hazard on a fixed-drive machine. A derailleur shifts the chain sideways across a cluster of different-sized sprockets to change gear ratio, cheap and light but fragile, requiring careful cable tension; a hub gear packs the same ratio choice inside a sealed shell at the wheel hub, tougher and shiftable even while stopped, but harder to repair in the field. A caliper brake squeezes the rim itself between two pads, simple and light, with no drum or disc needed.

**Prerequisites.** Precision chain link and sprocket manufacture.

**Roman-available inputs.** Steel for chain links, pins and sprockets, leather or rubber-substitute for brake pads.

**Procedure.** (1) Cut sprockets with evenly spaced teeth matched to chain pitch. (2) Assemble chain from pinned link plates, each rotating slightly to reduce friction on the sprocket. (3) Fit a ratchet-and-pawl freewheel inside the rear hub. (4) Mount a lever-actuated caliper brake gripping the rim.

**How you know it worked.** Pedalling drives the wheel with no slip or skipping; stop pedalling and the wheel keeps spinning freely while the pedals stop.

**Failure modes.** A stretched, worn chain skips under load; a seized freewheel pawl locks the wheel to the pedals unexpectedly; worn rim brake pads lose bite in the wet.

**Cost & labour.** ESTIMATED 8-12 artisan-days for chain, sprockets and freewheel hub together.

**Danger.** None significant beyond ordinary riding hazards.

**Confidence: HIGH** - roller chain geometry is simple and well documented, achievable with careful hand tooling.

---

### tl_macadam_road - Macadam and bound road surfaces

Also covers: tl_tarmacadam, tl_concrete_roadway, tl_cambered_drainage, tl_kerbing

**What it is / why you want it.** A road surface built from graded, compacted stone layers, optionally bound with tar or cast as a reinforced concrete slab, shaped to shed water.

**Why you would never guess this.** Macadam's trick is not the stone, Rome already builds excellent multi-layer stone roads, it is that each layer uses progressively smaller stone so that traffic itself compacts the surface into an interlocking, self-binding mat, needing no mortar at all; it is a cheaper, faster-built road than a full Roman via, though less durable. Adding tar (tarmacadam) fills the remaining voids and stops water and dust penetrating, extending life further. Reinforced concrete pushes further still, a monolithic slab reinforced with embedded iron eliminates rutting entirely, at far higher up-front cost, and lasts decades. None of these matter without camber, a slight cross-slope of only a few percent, which is the whole reason water does not pool and rot the road bed; a kerb then defines the road edge and stops that shed water and debris spreading onto footways.

**Prerequisites.** Existing Roman road-building competence (see 85_transport_civil.md), reinforcing iron for the concrete option.

**Roman-available inputs.** Graded local stone, bitumen or coal-tar (imported or locally sourced where bituminous seeps exist), Roman hydraulic concrete (10_metallurgy.md/85_transport_civil.md).

**Procedure.** (1) Grade a base of large stone, then successively finer layers, each rolled or trafficked to compact. (2) Shape the surface to a shallow camber, roughly a few percent slope from centre to edge. (3) For tarmacadam, pour hot tar over the compacted surface and blind with fine grit. (4) Set kerb stones along the edge.

**How you know it worked.** Water poured on the finished surface runs to the edges within moments rather than pooling; a season of traffic leaves the surface tighter, not looser.

**Failure modes.** Wrong stone grading fails to interlock and ruts under wheel traffic; no camber means standing water and frost damage; tar applied too cold does not penetrate voids.

**Cost & labour.** ESTIMATED (basis: consistent with 85_transport_civil.md's road figures) lower per-mile cost than full Roman via construction, higher than a plain dirt track.

**Danger.** None physical; social value is high, a smoother road reads as prosperity to Roman authorities rather than suspicion.

**Confidence: HIGH** - an extension of existing, well-attested Roman road technique.

---

### tl_road_roller - Steam road roller and level crossings

Also covers: tl_level_crossing

**What it is / why you want it.** A heavy powered roller that compacts a road surface in hours instead of days of foot and cart traffic, and the crossing arrangement where a road meets a rail line at the same level.

**Why you would never guess this.** Hand or animal compaction of a macadam surface took teams of twenty men or more working all day per stretch; a steam roller replaces that labour with a boiler and a crank driving the roller directly, at the cost of needing a working steam plant on wheels (93_energy.md). A level crossing looks like the cheap option compared to a bridge or underpass, and it is, but only because it quietly moves the cost into risk: it works safely only with reliable gates and signals timed to close well before a train arrives, and fails catastrophically, not gradually, when that timing slips.

**Prerequisites.** 93_energy.md boiler and piston-engine basics for the roller; tr_semaphore_signal or tr_block_signalling for a safe crossing.

**Roman-available inputs.** Cast iron rollers, a small stationary-type steam engine mounted on a wheeled chassis, timber gates for the crossing.

**Procedure.** (1) Mount a boiler and simple piston engine driving the front roller directly by crank. (2) For the crossing, install mechanical gates linked to a signal lever a set distance up the line, operated by a keeper.

**How you know it worked.** A rolled road surface shows no wheel-rut after a season of ordinary traffic; a crossing gate closes and is verified shut before the earliest possible train arrival, tested against a stopwatch-equivalent count.

**Failure modes.** An unattended or mistimed crossing gate is a collision waiting to happen; a roller with a leaking boiler loses compaction pressure.

**Cost & labour.** ESTIMATED (basis: comparable to a small stationary steam engine build, 93_energy.md) significant capital for the roller, modest labour for the crossing gates.

**Danger.** A level crossing is a genuine, recurring source of death if undermanned; treat gatekeeping as a manned, disciplined post, not a fixture you install and forget.

**Confidence: HIGH** for the roller mechanism; HIGH for the crossing mechanism, MEDIUM for the safe operating discipline around it, which is a human-process problem as much as an engineering one.

---

### tl_horse_collar - Horse collar, horseshoe, stirrup and harness

Also covers: tl_horseshoe, tl_stirrup, tl_tandem_harness, tl_whippletree

**What it is / why you want it.** A cluster of animal-traction fixes: a padded rigid collar that lets a horse pull from its chest instead of its throat, nailed iron shoes, a foot-loop for riders, and harness geometry that shares load fairly between multiple animals.

**Why you would never guess this.** The Roman yoke, borrowed from oxen, presses across the horse's windpipe and major neck blood vessels; the harder the horse pulls, the more it chokes itself, so Roman haulage teams are quietly working at a fraction of a horse's real pulling capacity without anyone realising the animal, not the cart, is the bottleneck. A rigid, padded collar moves that pressure onto the horse's chest and shoulders, bone and muscle rather than airway, and lets a horse pull roughly five times its own body weight instead of a small fraction of it. A nailed horseshoe drives nails through the insensitive hoof wall, not living tissue, letting a horse work on wet, rocky or icy ground it would otherwise go lame on. A whippletree is a pivoting crossbar that automatically equalises pull between two or more animals of different strength, without one straining and one loafing. A stirrup lets a rider stand and brace, transferring the rider's weight and force into the horse and into weapons or tools, not just balance.

**Prerequisites.** Leatherworking, ironworking, none exotic.

**Roman-available inputs.** Leather and stuffed padding for the collar, wrought iron for shoes, nails and stirrups, oak for the whippletree bar.

**Procedure.** (1) Shape a padded leather collar to the horse's individual shoulders, wide enough to spread load. (2) Fit iron shoes with nails angled outward through the hoof wall's insensitive zone. (3) Hang a pivoting whippletree bar between paired animals' traces. (4) Hang a stirrup from each saddle side at a length matched to the rider's leg.

**How you know it worked.** A collared horse pulls a load its yoked equivalent cannot budge; a shod horse crosses wet cobbles without slipping where an unshod one stumbles.

**Failure modes.** A badly fitted collar galls the shoulders raw; a misplaced shoe nail lames the horse by driving into sensitive tissue; an unequal whippletree still lets one animal do all the work if the pivot binds.

**Cost & labour.** ESTIMATED 1-2 artisan-days per collar/shoe set, trivial per animal, the gain is entirely in the design, not the material cost.

**Danger.** A poorly nailed shoe can cripple a valuable animal; no social danger, this reads as ordinary animal husbandry to any Roman observer.

**Confidence: HIGH** - all four are simple, well-attested medieval technologies with no exotic material requirement; this is one of the highest payoff-to-difficulty entries in the whole tree.

---

### tr_edge_rail - Edge rail, bullhead and flat-bottom profiles

Also covers: tr_bullhead_rail, tr_flatbottom_rail, tr_chair_key, tr_fishplate, tr_rail_rolling, tr_rail_welding

**What it is / why you want it.** The evolving shape of the iron or steel rail itself, how it is joined, and how it is manufactured at length.

**Why you would never guess this.** The whole discovery is that a thin raised iron edge, not a thick flat plate, is the efficient shape: the wheel flange needs only a narrow guiding edge to run on, and concentrating the iron there instead of spreading it across a whole flat surface saves metal for the same strength. A bullhead rail is deliberately symmetrical top and bottom so that once the running surface wears down on one side, the rail can be lifted, turned over, and relaid, doubling its service life at the cost of needing a chair, a cast iron seat on the sleeper that clamps the head and is fixed with a driven wooden or iron key. Flat-bottom rail, once rolling tolerances improved enough to make it economical, sits directly on the sleeper without a chair at all, saving weight and labour per mile but only workable once mills can roll a consistent profile. A fishplate bolts across a joint between two rail ends to resist the vertical and twisting stress every wheel passage puts on that joint, the weakest point in any rail line; welding removes the joint problem entirely but demands careful preheat or the weld cracks on cooling.

**Prerequisites.** tr_rail_rolling itself depends on a working rolling mill (10_metallurgy.md), consistent wrought iron or steel supply.

**Roman-available inputs.** Wrought iron initially (steel later, once bulk steel process exists, see 10_metallurgy.md), cast iron for chairs, oak wedges for keys.

**Procedure.** (1) Roll iron bar through successively narrower grooved rollers until the I-shaped or bullhead profile emerges, controlling speed and temperature through each pass. (2) Cast chairs to the rail head's exact profile. (3) At joints, sandwich rail ends between fishplates and bolt through. (4) For welding, preheat both rail ends evenly before joining, and cool slowly under cover to avoid thermal cracking.

**How you know it worked.** A finished length, struck with a hammer, rings uniformly along its length with no dull or dead spots indicating a flaw; a bolted joint under a passing load shows no visible flex.

**Failure modes.** Inconsistent rolling temperature warps the profile; loose chair keys let the rail rock under load and eventually crack the chair; an unpreheated weld cracks as it cools.

**Cost & labour.** ESTIMATED (basis: this is the dominant material cost of any railway, see 85_transport_civil.md's railway entry) the largest single capital line of any rail project; rolling mill construction is a major standalone undertaking.

**Danger.** Rolling mill work involves red-hot bar stock moving fast, serious burn and crush risk; a failed rail in service derails a train.

**Confidence: HIGH** on the geometry, MEDIUM on achieving consistent mill tolerances at Roman-era metallurgical control.

---

### tr_sleeper_ballast - Sleeper, ballast and track gauge

Also covers: tr_wooden_waggonway, tr_rail_gauge_standardization

**What it is / why you want it.** The graded stone bed and timber cross-ties that hold the rail at the correct height and spacing, and the wooden-railed forerunner that came before iron rail existed.

**Why you would never guess this.** Ballast size is a real engineering choice, not a default: too large and the rails rock on point contact between stones; too small and the bed settles and washes out quickly under vibration and rain. Sleepers must be set to a precise, repeated spacing and depth, checked with a wooden gauge and string line, because an uneven foundation telegraphs straight up into wheel impact loads. Gauge standardisation, the exact spacing between the two rails, is not a technical problem at all, it is a political one: early competing lines each picked a convenient width, and mismatched gauge meant every passenger and cargo item had to be manually transferred at the border between systems, an entirely avoidable cost that standardisation abolished at a stroke. A wooden waggonway, wheels running in wooden or L-shaped iron-capped rails, is the crude, cheap ancestor of all of this, workable at low traffic but wearing out fast.

**Prerequisites.** tr_edge_rail for the modern version; plain carpentry for the waggonway predecessor.

**Roman-available inputs.** Oak or chestnut sleepers, graded quarry stone for ballast, wrought iron rail.

**Procedure.** (1) Grade and compact a stone ballast bed of a chosen, tested size range. (2) Set sleepers at a fixed spacing using a wooden gauge template. (3) Fix rails at an agreed, single standard spacing across every line you intend to interconnect, decided once, early, by whoever controls the project.

**How you know it worked.** A loaded wagon passing at speed produces no visible sleeper movement or rail rock; two separately built lines meet and equipment runs through without transfer.

**Failure modes.** Wrong ballast size settles unevenly and needs constant relevelling; skipped gauge standardisation locks you into permanently incompatible networks, the single most expensive mistake to fix after the fact.

**Cost & labour.** ESTIMATED (basis: 85_transport_civil.md's railway cost figures) major recurring capital and labour, ballast maintenance is ongoing, not one-time.

**Danger.** None beyond ordinary construction risk; the real danger of skipping standardisation is economic and political, not physical.

**Confidence: HIGH** - track-laying discipline is well documented from the historical record; treat the gauge decision as the single highest-leverage choice in this whole cluster.

---

### tr_semaphore_signal - Semaphore, block and interlocking signalling

Also covers: tr_block_signalling, tr_interlocking_signal, tr_track_circuit, tr_automatic_train_stop

**What it is / why you want it.** The layered system that tells a train driver whether the track ahead is clear, prevents a signalman from setting up a collision, and forces a stop automatically if a driver misses a signal.

**Why you would never guess this.** A semaphore arm at a fixed post only tells a driver about the track visible from that post; the real invention is dividing the whole line into blocks and never allowing two trains in the same block at once, communicated block to block by signalmen, which prevents rear-end collisions by rule rather than by driver vigilance. Interlocking is the next layer down: a mechanical arrangement of levers so that setting one signal or points combination physically locks out any other lever that would create a conflicting route, meaning a signalman's honest mistake cannot cause a wreck, only a delay. A track circuit automates detection entirely: a low-voltage current run down one rail and back through the other is short-circuited the instant a train's own wheels and axles bridge the gap, releasing a relay and changing the signal without any human report at all. An automatic train stop is the final backstop, a trackside arm or ramp that physically trips the brake if a train passes a signal still at danger, because you cannot assume every driver will always see and obey a semaphore, especially in fog or at night.

**Prerequisites.** 50_electricity.md for track circuits; tr_edge_rail for a continuous, electrically usable rail.

**Roman-available inputs.** Iron/wood for semaphore arms and levers, copper wire and a battery source (50_electricity.md) for track circuits.

**Procedure.** (1) Divide the line into blocks, one train per block, enforced by signalmen exchanging a physical token or message. (2) Mechanically interlock the levers controlling each block's signals and points so conflicting settings cannot both be made. (3) Wire a low-voltage circuit through each block's rails to a relay, broken automatically by a train's wheelset. (4) Fit a trackside trip arm linked to each stop signal.

**How you know it worked.** Deliberately walk a train's route through a conflicting lever setting; the interlock should physically refuse to let the second lever move.

**Failure modes.** A signalman who bypasses or disables interlocking under pressure defeats the entire safety case; a track circuit fouled by rust or poor rail-to-rail contact can fail to detect a train.

**Cost & labour.** ESTIMATED (basis: this is a discipline and infrastructure cost more than a material one) modest hardware cost, ongoing cost is a trained, disciplined signalling staff.

**Danger.** Physical: signalling failure is how trains collide. Social: an interlocked signal box will read to Rome as an obviously military-grade control system, expect requisition interest.

**Confidence: HIGH** - block working and mechanical interlocking are simple logic, well documented from the historical railway record.

---

### tr_points_frog - Points, frog, turntable and yard switching

Also covers: tr_grade_crossing, tr_marshalling_hump, tr_turntable

**What it is / why you want it.** The trackwork that lets a train change from one line to another, cross another line, reverse a locomotive's direction, or sort a whole train of wagons without manual shunting of each one.

**Why you would never guess this.** A frog, the crossing point where two rails intersect, must support a wheel's full weight across a physical gap in the rail, which is unavoidable geometry, not a design flaw; the wheel simply bridges the gap at speed on its flange and tread together. A marshalling hump yard is a small elegant piece of physics applied at scale: push a whole train slowly over a rise, uncouple wagons one at a time at the crest, and gravity alone rolls each one down into the correct sorting track, switched remotely, eliminating the enormous labour of pushing or pulling each wagon individually. A turntable looks like a simple pivot but is not: it must carry a locomotive's full weight on a ring of rolling elements, because a plain center pivot alone cannot support that concentrated load without binding.

**Prerequisites.** tr_edge_rail, tr_flanged_wheel.

**Roman-available inputs.** Iron rail and castings, timber for hump-yard gradients (an earthwork more than a machine).

**Procedure.** (1) Cast a frog to bridge the rail gap at the crossing angle needed. (2) Build points as a pair of movable rails sliding together to route a wheel left or right. (3) For a hump yard, grade a rise into the yard approach and lay sorting tracks fanning out beyond its crest. (4) Build a turntable pit with a rolling-element ring bearing under a rotating deck.

**How you know it worked.** A wagon released at the hump crest rolls unassisted into its assigned siding; a loaded locomotive on the turntable rotates with modest hand or engine effort.

**Failure modes.** A worn frog throws a wheel off course; hump-yard wagons that roll too fast or too slow foul the sort; a turntable with poor rolling elements binds under a heavy locomotive.

**Cost & labour.** ESTIMATED (basis: proportional to a yard's traffic volume) significant for a hump yard's earthworks, moderate for points and a turntable.

**Danger.** A hump yard in motion around free-rolling wagons is a serious crush hazard to yard workers; treat as skilled, disciplined labour.

**Confidence: HIGH** - straightforward mechanics, no exotic material required.

---

### tr_flanged_wheel - Flanged wheel, axle box and bogie

Also covers: tr_axle_bearing_box, tr_bogie_truck, tr_leading_truck

**What it is / why you want it.** The wheel-and-running-gear cluster that keeps a rail vehicle on the track through curves while carrying its bearing load reliably.

**Why you would never guess this.** Putting the flange on the wheel rather than a groove in the rail is the right choice because a flanged wheel can run on a simple flat-topped rail, while a grooved rail collects dirt and debris in the groove and fouls quickly; the flange does slip sideways slightly on curves, which is a tolerated, designed-in imperfection, not a flaw to eliminate. The axle bearing box is unglamorous and lethal if neglected: it needs a drain hole so old, grit-laden oil does not simply accumulate, because a clogged, dry box overheats catastrophically in service, a "hot box," historically a leading cause of derailment, caught only by scheduled inspection and re-oiling, not by waiting for a failure. A bogie, a small four-wheeled truck pivoting under the vehicle, spreads weight over more wheels and lets a long rigid-framed vehicle actually follow curved track; a leading truck does the same simpler job just for the front wheels of a locomotive, letting the leading edge steer into the curve ahead of the rigid driving wheels.

**Prerequisites.** tr_edge_rail, casting tolerance within a few millimetres for wheel flanges, case hardening.

**Roman-available inputs.** Cast iron or steel wheels, bronze bearing bushings, oil.

**Procedure.** (1) Cast wheels with a flange proud of the tread by a fixed margin, case-harden the tread and flange face. (2) Build axle boxes with a drilled drain and a scheduled re-oiling routine. (3) Mount a pivoting bogie or leading truck ahead of any long rigid wheelbase.

**How you know it worked.** A vehicle takes the tightest curve on the line without the flange striking the rail head hard enough to squeal continuously; an axle box, checked on schedule, runs warm, never hot, to the touch.

**Failure modes.** A hot, unoiled axle box seizes and can derail the vehicle; a worn flange rides up and off the rail on a curve; a rigid (non-bogie) long wheelbase binds and derails on tight curves.

**Cost & labour.** ESTIMATED (basis: comparable to any precision iron casting job) moderate per wheelset, but the ongoing inspection labour matters more than the build cost.

**Danger.** A derailment from a hot box or worn flange is a serious, sometimes fatal, wreck; make axle inspection a non-negotiable scheduled task.

**Confidence: HIGH** - flanged wheel geometry and bogie mechanics are simple and well attested; hot-box failure is one of the best documented railway failure modes historically.

---

### tr_screw_coupling - Screw coupling, buffer and knuckle coupler

Also covers: tr_sprung_buffer, tr_knuckle_coupler

**What it is / why you want it.** The link between successive wagons: a threaded hook tightened by hand, sprung buffers absorbing shock, and later an automatic latching hook needing no one between the wagons at all.

**Why you would never guess this.** The whole problem of a train is starting it, because you cannot accelerate every wagon simultaneously from a dead stop, the locomotive simply does not have that much instantaneous force, so a small amount of slack in every coupling is a feature, not sloppiness: it lets the locomotive take up each wagon's inertia one at a time in a rolling sequence, "snatching" the train into motion link by link instead of trying to move the entire mass at once. A screw coupling is tightened by a man walking between wagons and turning a threaded rod by hand, slow and, historically, one of the most dangerous jobs on any early railway, a screwman crushed between buffers is a routine and grim statistic in the historical record. Sprung buffers cushion the coupling impact itself, without them the jerk of coupling or of starting snaps couplings and topples cargo; the springs must be tuned so they neither transmit the shock nor rebound so hard they uncouple. The knuckle coupler removes the human entirely: two spring-loaded hooked jaws that latch shut automatically the instant the wagons touch, at the cost of needing accurate, repeatable casting geometry so the jaws always find each other correctly.

**Prerequisites.** Iron founding and forging at production scale.

**Roman-available inputs.** Wrought iron for screw couplings and buffer springs, cast steel later for reliable knuckle geometry.

**Procedure.** (1) Forge a hook and threaded coupling bar; a screwman connects and tightens by hand between stationary wagons. (2) Fit sprung buffer heads at each wagon end, tuned to compress under normal shunting force without bottoming out. (3) For a knuckle coupler, cast a hinged jaw that latches automatically when two wagons are pushed together.

**How you know it worked.** A coupled train starts from rest with a visible, sequential "snatch" running down its length, not a single violent jerk; buffers compress visibly on contact and return without clang.

**Failure modes.** A screw coupling left too slack lets wagons run together violently; too tight and it cannot take up starting slack at all; a knuckle coupler with worn or mis-cast jaws fails to latch and separates in motion.

**Cost & labour.** ESTIMATED 2-4 artisan-days per coupling unit; the knuckle coupler needs tighter, more expensive casting control.

**Danger.** Screw coupling by hand between wagons is genuinely one of the most dangerous manual jobs on a railway; a crushed screwman is not a hypothetical risk, it is the historically documented norm until automatic coupling replaced the job.

**Confidence: HIGH** - simple mechanics, well documented historical failure and injury patterns to plan around.

---

### tr_brake_shoe - Rail brake shoe, vacuum and Westinghouse air brake

Also covers: tr_vacuum_brake, tr_westinghouse_brake

**What it is / why you want it.** The systems that stop an entire train of separately coupled wagons together, from simple wooden shoes to a continuous brake pipe running the whole train's length.

**Why you would never guess this.** A cast iron brake shoe against a wheel converts kinetic energy to heat exactly like a road brake, and overheats the same way under sustained use, losing friction just when it is needed most. The genuinely non-obvious part is the vacuum brake's failure logic: a vacuum is maintained the length of the train by a pump on the locomotive, and if any coupling between wagons breaks or a hose bursts, air rushes in and the brakes apply automatically on every wagon at once, meaning the failure mode of the system is "stop," not "keep going," which is exactly backwards from what you would guess and exactly what you want from a safety system. The Westinghouse air brake improves on this with a "triple valve" at each wagon, a small mechanism that senses a drop in the train's continuous air-pressure line and applies that wagon's own local brake automatically, again defaulting to safe-stop on any pipe failure, without needing a vacuum pump at all, just a compressor on the locomotive.

**Prerequisites.** tr_flanged_wheel, tr_screw_coupling for the connected pipe runs.

**Roman-available inputs.** Cast iron shoes, leather or rubber-substitute hose couplings between wagons, iron cylinders for the triple valve mechanism.

**Procedure.** (1) Fit cast iron shoes pressing directly on wheel treads, levered from a hand or air-actuated mechanism. (2) Run a continuous pipe the length of the train, coupled between every wagon, evacuated by a locomotive-mounted pump (vacuum) or pressurised by a compressor (Westinghouse). (3) Fit each wagon with a local valve that applies its brake automatically on any drop in line pressure.

**How you know it worked.** Deliberately uncouple a hose mid-train while stationary; every wagon's brake should apply immediately, not just the ones ahead of the break.

**Failure modes.** A leaking pipe joint bleeds vacuum or pressure slowly, giving weak, delayed braking; overheated shoes fade exactly as in the road brake case above.

**Cost & labour.** ESTIMATED (basis: comparable to fitting cylinders and valves across a full wagon fleet) substantial fleet-wide retrofit cost, justified entirely by the safety case.

**Danger.** A train without a fail-safe continuous brake, relying only on individual wagon brakes set by hand, is a documented historical cause of runaway trains; this is not optional once trains carry passengers.

**Confidence: HIGH** - both vacuum and air brake logic are well documented and mechanically simple once the pipe-and-valve concept is understood.

---

### tr_locomotive_boiler - Locomotive boiler, smokebox, blastpipe, superheater, injector

Also covers: tr_smoke_box, tr_blastpipe, tr_superheater, tr_injector_feedwater

**What it is / why you want it.** The steam-raising heart of a locomotive: a multitubular boiler, the smokebox and spark arrester at its front, the blastpipe that draws the fire, the superheater that dries the steam, and the injector that refills the boiler against its own pressure.

**Why you would never guess this.** A locomotive boiler must raise far more steam per unit of grate area than a stationary boiler, because it has no room to be large, and the trick is dozens of small fire-tubes running the length of the boiler instead of one big flue, multiplying the heat-transfer surface enormously in the same envelope; a tube failure ruptures the boiler explosively, so ferrule expansion (a tight mechanical swage, not just a weld) at every tube end is standard practice, not a luxury. The blastpipe is the genuinely clever bit: exhaust steam, still under pressure as it leaves the cylinders, is aimed up a narrow nozzle inside the chimney, and its sheer velocity drags the hot firebox gases through the tubes and up the stack by suction, so the harder the engine works, the harder it draws its own fire, a self-reinforcing loop with no separate fan needed. A smokebox at the front catches ash and cinders in a mesh char arrester, because a spark-throwing locomotive will set fire to every field of standing crop it passes, an operational failure with real political cost. A superheater reheats steam above its boiling point after it leaves the boiler proper, so it stays fully dry (gaseous) through the cylinders instead of partly condensing, and dry steam expands and does useful work far more efficiently than wet steam. An injector is the strangest of the cluster: it uses a jet of steam to accelerate a stream of cold water fast enough to force it into the boiler against the boiler's own pressure, with no moving parts, which looks like it should not work and does.

**Prerequisites.** 93_energy.md boiler fundamentals, tube-rolling and ferruling skill, riveted or welded pressure-vessel construction.

**Roman-available inputs.** Wrought iron or steel boiler plate and tubes, copper for firebox stays if available.

**Procedure.** (1) Build a cylindrical shell with dozens of small fire-tubes running from firebox to smokebox, each ferruled tight at both ends. (2) Fit a mesh char arrester in the smokebox. (3) Aim the exhaust steam pipe up a narrow blastpipe nozzle inside the chimney base. (4) Route steam from the boiler through additional tubes back through the hottest gas path before it reaches the cylinders (superheating). (5) Fit an injector: a nested cone nozzle where steam entrains and accelerates water into a delivery check valve on the boiler.

**How you know it worked.** The fire draws visibly harder and brighter the moment the throttle opens and exhaust starts blasting; an injector, correctly adjusted, delivers a steady stream into the boiler with a distinct hiss and no water hammer.

**Failure modes.** A ruptured tube is explosively dangerous; a clogged char arrester either starves the draught or lets sparks through; a mishandled injector "knocks off" and stops delivering water, risking a low-water boiler explosion if not caught.

**Cost & labour.** ESTIMATED (basis: proportional to boiler size and tube count) a major fabrication project per locomotive, on par with 93_energy.md's stationary boiler cost scaled down but built to tighter, portable tolerances.

**Danger.** Boiler explosion is the single most catastrophic failure mode in this entire module; a low-water locomotive boiler that overheats its crown sheet can explode with lethal force. Treat water-level checking as the single most disciplined habit any fireman must have.

**Confidence: HIGH** on the mechanisms; MEDIUM on achieving Roman-era metallurgical quality control sufficient to trust a boiler at full working pressure without modern non-destructive testing.

---

### tr_slide_valve - Slide valve, piston valve and valve gear

Also covers: tr_piston_valve, tr_stephenson_linkmotion, tr_walschaerts_valve, tr_compound_expansion, tr_articulated_locomotive

**What it is / why you want it.** The mechanism that admits and exhausts steam to each cylinder in the correct sequence and timing as the locomotive runs, plus the linkages that let a driver vary that timing.

**Why you would never guess this.** A slide valve is a flat casting sliding back and forth over ports, simple to make but rubbing continuously under steam pressure, which wastes power to friction; a piston valve does the identical job with a cylindrical valve sealed by rings, so only the rings touch the bore rather than a whole flat face, cutting friction sharply, the same sealing idea as the main piston itself. Stephenson link motion is the ingenious original solution to reversing and varying cutoff: two eccentrics (off-centre cams), one for forward and one for reverse, both drive a curved link, and sliding that link up or down under a fixed pickup point blends between the two eccentrics' motion, letting the driver choose forward, reverse, or any point between, including a shortened "cutoff" that uses steam more efficiently at speed. Walschaerts valve gear achieves the same variable cutoff differently, taking its primary motion from the main piston rod's own crosshead rather than a second eccentric, giving a more even, more nearly sinusoidal valve motion and easier maintenance access, which is why it eventually displaced Stephenson gear despite Stephenson's earlier start. Compound expansion sends high-pressure steam through small cylinders first, then exhausts that still-useful steam into larger low-pressure cylinders for a second expansion, extracting noticeably more work per unit of coal than a single-expansion engine. An articulated locomotive solves a different problem, a very long locomotive cannot get its rigid wheelbase around a tight curve, so it is split with a pivot at the centre, two complete sets of cylinders sharing one boiler, connected by flexible steam pipes across the pivot, the hard part being those pipes surviving constant flexing under pressure.

**Prerequisites.** tr_locomotive_boiler, precision linkage fabrication.

**Roman-available inputs.** Wrought iron/steel for valves, links and eccentrics, flexible steam piping (a real challenge, leather and iron banded joints as a fallback, expect leaks) for articulated pipe runs.

**Procedure.** (1) Cut eccentric cams offset from the driving axle centre. (2) Link eccentric motion through a curved slotted bar to the valve rod, with a sliding pickup block the driver raises or lowers to change cutoff. (3) For Walschaerts gear, take primary motion from the crosshead via a combination lever instead of a second eccentric. (4) For compound expansion, duct exhaust from small high-pressure cylinders into larger low-pressure ones rather than to atmosphere.

**How you know it worked.** Steam chest ports show even, symmetric opening on both sides of a piston stroke when checked by hand-turning the wheels slowly; a compound engine shows visibly less exhaust "bark" and lower coal consumption for the same drawbar pull.

**Failure modes.** Worn eccentric straps introduce lost motion and erratic valve timing; a cracked articulated steam joint leaks pressure and power continuously; mismatched compound cylinder sizing starves the low-pressure side.

**Cost & labour.** ESTIMATED (basis: precision linkage work, comparable in skill demand to fine clockwork scaled up) high, this is among the most skill-intensive fabrication in the whole module.

**Danger.** Valve gear operates close to the wheels and connecting rods at speed; a loose link can shatter violently. No social danger beyond the general military read on railways.

**Confidence: MEDIUM** - the mechanisms are well documented, but achieving the fabrication tolerance for smooth, reliable valve timing by hand is genuinely difficult.

---

### tr_electric_locomotive - Electric and diesel-electric traction

Also covers: tr_pantograph, tr_catenary_overhead, tr_third_rail, tr_diesel_electric

**What it is / why you want it.** Motive power drawn from an external electrical supply, or generated on board by a diesel engine and delivered to the wheels electrically rather than mechanically.

**Why you would never guess this.** Electric traction is not simply "steam but cleaner," it needs an entire supporting infrastructure first: either an overhead catenary wire (a support cable compensating for the contact wire's natural sag, with a spring-loaded pantograph on the roof pressing a sliding contact up against it) or a third rail at low level with a sliding shoe, and either way that infrastructure, generating stations, substations, miles of conductor, is a larger capital project than the locomotive itself. The pantograph's real engineering problem is contact at speed: too little spring pressure and the contact wheel bounces off the wire, arcing and burning both; too much and it wears the wire down fast, so the pressure must be tuned within a narrow band. Diesel-electric transmission solves a different problem entirely: a diesel engine, unlike a steam engine, produces very little torque at low revolutions and cannot be clutched directly to a stationary load the way a steam piston can, so instead it drives a generator, and the generator's electrical output drives conventional motors at the wheels, which deliver smooth, controllable torque from a dead stop the diesel engine alone cannot.

**Prerequisites.** 50_electricity.md generation and transmission at scale, 93_energy.md for diesel engine fundamentals.

**Roman-available inputs.** Copper for catenary wire and motor windings, iron for rail and third-rail conductors; diesel fuel is a refined petroleum product (93_energy.md's petroleum drilling and refining entries).

**Procedure.** (1) String a contact wire supported by a sagging catenary cable at consistent height. (2) Fit locomotives with a spring-loaded pantograph tuned to the minimum pressure that avoids bounce at running speed. (3) For diesel-electric, couple the diesel engine to a generator, and wire its output to axle-mounted traction motors.

**How you know it worked.** A pantograph at running speed shows no visible sparking or arcing under normal load; a diesel-electric locomotive pulls away from a dead stop smoothly, without the stall risk of a direct-clutched diesel.

**Failure modes.** Undersprung pantographs arc and burn the contact wire; icing on overhead wire or third rail interrupts power entirely; a diesel-electric generator or motor failure strands the locomotive with a running engine and no drive.

**Cost & labour.** ESTIMATED (basis: 50_electricity.md's generation and transmission infrastructure costs) very high fixed infrastructure cost, best justified only on your highest-traffic routes.

**Danger.** A live catenary or third rail is a serious, often fatal electrocution hazard to anyone on the track; this needs the same disciplined access control as any high-voltage system in 50_electricity.md.

**Confidence: MEDIUM** - the machines are documented, but the supporting electrical infrastructure is a much larger dependency than the locomotive itself.

---

### tr_hopper_wagon - Specialised wagons: hopper, tank, refrigerated, sleeping car

Also covers: tr_tank_wagon, tr_refrigerated_wagon, tr_sleeping_car

**What it is / why you want it.** Wagons purpose-built for bulk minerals, liquids, perishable cargo and overnight passengers, each solving a different loading or preservation problem.

**Why you would never guess this.** A hopper wagon's entire value is eliminating shovel labour: cargo is loaded from above and released through a bottom chute by gravity alone at the destination, but the chute must be wide enough that the cargo does not "bridge," arch over the opening and jam, a real and common failure with fine or damp material, needing a wide throat and sometimes a vibrating knock to clear. A tank wagon must be strong enough to carry its own liquid contents' full sloshing weight over rough, uneven track at speed, and any seam weakness that would be a slow drip in a static tank becomes a serious leak or worse under that dynamic stress; early hand-riveted tank seams were a known weak point. A refrigerated wagon's hard problem is not making things cold, ice in a roof-corner chamber does that passively as cold air sinks, it is air circulation: stagnant cold air lets mould and spoilage creep in near the walls, while too much circulation prematurely melts the ice and spoils the cooling; getting the vent geometry right is the actual engineering. A sleeping car's constraint is nearly the opposite of an engineering problem, it is privacy: stacked bunks in an open car fail socially even if they succeed mechanically, so compartment partitioning matters as much as the superior springing needed for a passenger trying to sleep through the ride.

**Prerequisites.** tr_flanged_wheel, tl_leaf_spring (better suspension matters especially for the sleeping car).

**Roman-available inputs.** Iron plate for tanks, cork or sawdust insulation and natural ice for refrigeration, timber for hopper and sleeping-car bodies.

**Procedure.** (1) For a hopper, build a wagon body tapering to a wide, hinged bottom chute. (2) For a tank, weld or carefully rivet a cylindrical shell to the underframe with continuous, tested seams. (3) For refrigeration, line the body with insulation, place ice bunkers at roof corners, and cut vents positioned to encourage gentle, continuous circulation. (4) For sleeping cars, partition into compartments and fit superior springing.

**How you know it worked.** A hopper wagon empties completely on opening its chute with no residual bridged material; a refrigerated wagon holds a measurably cool, even temperature throughout its length after a full day's run, not just near the ice bunkers.

**Failure modes.** A bridged hopper chute needs manual clearing, defeating its purpose; a leaking tank wagon seam is a spill and fire hazard depending on cargo; uneven refrigeration spoils cargo nearest the walls first.

**Cost & labour.** ESTIMATED (basis: proportional to standard wagon cost plus specialised fittings) moderate premium over a plain freight wagon per type.

**Danger.** A leaking tank wagon carrying anything flammable or corrosive is a serious hazard in a derailment; otherwise low risk.

**Confidence: HIGH** - all four are straightforward carpentry and metalwork extensions of the basic wagon, no exotic material needed.

---

### tr_carvel_planking - Hull planking, framing and caulking

Also covers: tr_clinker_planking, tr_frame_first_construction, tr_keelson, tr_caulking_oakum, tr_hull_sheathing_wood, tr_copper_sheathing

**What it is / why you want it.** The family of choices in how a wooden hull's planks and internal frame are built, sealed, and protected.

**Why you would never guess this.** Clinker planking, each plank overlapping the one below, is not just an old-fashioned look, the overlap gives the hull real flex and a genuine hydrodynamic benefit at speed, which is why small fast boats kept using it long after larger ships moved on. Carvel planking, planks meeting flush edge to edge over an internal frame, gives a smoother, stronger hull for large vessels, but only if every seam is caulked perfectly, because a flush seam has no natural overlap to shed water and depends entirely on packed oakum (loose, tarred rope fibre driven into the seam with mallet and chisel, then sealed over) to stay watertight, and that seam must be packed from both sides or it will still weep. Frame-first construction, building the internal ribcage first and planking over it, rather than the older shell-first method of building up planks and only then fitting frames to match, gives far more precise, repeatable hull shapes and stronger structures, which matters enormously once you are trying to build many similar ships rather than one at a time. A keelson, an internal timber bolted along the top of the keel sandwiching the frames, exists specifically to stop "hogging," the slow structural sag of a long wooden hull's ends over years of use, which without it eventually cracks a large ship's back. Copper sheathing over the underwater hull is sacrificial: it does not stop marine growth chemically so much as slowly dissolve and poison it, which is why iron fastening nails corrode dangerously fast next to copper and must be copper themselves, or the sheathing eats its own fastenings.

**Prerequisites.** Existing Roman shipwrighting (mortise-and-tenon hull construction is already excellent, see 85_transport_civil.md's ship_improvements entry), copper supply (Cyprus, Spain).

**Roman-available inputs.** Oak framing timber, pine or fir planking, tarred hemp rope fibre (oakum), pine tar/pitch, copper sheet and copper nails.

**Procedure.** (1) Build the frame ("ribcage") first over a keel and keelson, fastened solidly before any planking goes on. (2) Plank over the frame, carvel-fashion for large hulls, clinker for small fast ones. (3) Drive oakum into every seam with mallet and caulking iron, working from inside and out, then seal over with hot pitch. (4) Nail copper sheet over the underwater hull with copper nails only.

**How you know it worked.** A caulked seam, tapped with the caulking iron, gives a distinct ringing resistance when fully packed, a dull, soft feel when under-packed; a coppered hull stays free of weed and barnacle growth season after season where an unsheathed one fouls within weeks in warm water.

**Failure modes.** Under-caulked seams weep continuously and need constant pumping (see tr_bilge_pump below); iron nails near copper sheathing corrode and let the sheathing fall away; a hull without a keelson sags and eventually cracks amidships over years of loaded service.

**Cost & labour.** ESTIMATED (basis: comparable to standard Roman shipwright labour, scaled for hull size) copper sheathing is the expensive addition, a real cost only justified for ships making long tropical voyages where fouling is worst.

**Danger.** None beyond ordinary shipyard risk; a poorly caulked hull is more an operational nuisance than immediate danger, unless it fails at sea.

**Confidence: HIGH** - all of this sits directly on already-excellent Roman shipwrighting technique.

---

### tr_iron_hull - Iron and steel hull, plating and bulkheads

Also covers: tr_steel_hull, tr_riveted_plating, tr_welded_hull, tr_double_bottom, tr_watertight_bulkhead

**What it is / why you want it.** Replacing wooden hull construction with iron or steel plate, joined by rivets or welds, and dividing the hull internally for safety and cargo flexibility.

**Why you would never guess this.** An iron hull is not simply a stronger wooden hull in a different material, it changes the achievable shape entirely: iron plate can be built larger and with thinner relative walls than wood, which no longer needs to be thick to resist rot and worm, so an iron ship can be substantially bigger for the same displacement than a wooden one, a genuine step change rather than an incremental gain. Riveted plating, red-hot rivets driven through overlapping plate and hammered flush on the far side, is enormously labour-intensive but reliable if done well; a poorly driven rivet leaks water in slowly at first and then catastrophically once corrosion widens the gap. Welded seams are stronger and far less labour, but early welding is genuinely riskier than riveting in one specific way: a rivet seam that starts to fail leaks gradually and gives warning, while a welded seam with a hidden stress concentration can crack suddenly under fatigue with no warning at all, so weld design has to actively avoid sharp internal corners and abrupt thickness changes where cracks start. A double bottom, essentially a second inner hull skin below the cargo holds, roughly doubles construction cost but means the ship keeps floating even if the outer hull is holed on a reef or in collision, and it doubles as a ballast water space that never touches cargo. Watertight bulkheads divide the hull into separate flooding compartments, but only work if every single penetration through them, doors, pipes, cable runs, is properly sealed; one careless open door defeats the entire system.

**Prerequisites.** Bulk iron/steel plate production (10_metallurgy.md), riveting or welding skill.

**Roman-available inputs.** Wrought iron plate initially, steel plate once bulk process exists (10_metallurgy.md).

**Procedure.** (1) Roll or hammer plate to consistent thickness. (2) Overlap plates and drive red-hot rivets through pre-punched holes, hammering the far end flush while still hot. (3) For a double bottom, build a full second hull skin a set distance inside the outer one, connected by internal framing. (4) Fit bulkheads at intervals with fully sealed door and pipe penetrations, tested by flooding one compartment deliberately and checking neighbours stay dry.

**How you know it worked.** A riveted seam under load shows no weeping at the rivet line; a bulkhead compartment, deliberately flooded as a test, keeps its neighbours completely dry.

**Failure modes.** A cold or poorly driven rivet loosens and weeps, worsening over time; a welded seam with a sharp stress corner cracks under repeated flexing; an unsealed bulkhead penetration defeats the whole safety case in a real flooding event.

**Cost & labour.** ESTIMATED (basis: major capital project on the scale of 10_metallurgy.md's bulk steel entries) a substantial multi-year shipyard investment, not a quick retrofit.

**Danger.** Riveting involves handling red-hot metal at height on a hull under construction, real burn and fall risk; an unsealed bulkhead system gives false confidence, which is its own danger.

**Confidence: MEDIUM** - iron shipbuilding is well documented historically, but depends entirely on the bulk iron/steel supply chain in 10_metallurgy.md being solved first.

---

### tr_square_rig - Sail plans: square, lateen, fore-and-aft, jib, staysail, reefing

Also covers: tr_lateen_sail, tr_fore_aft_rig, tr_fore_and_aft_rigging, tr_jib, tr_staysail, tr_reefing

**What it is / why you want it.** The family of sail shapes and rigging arrangements that determine what angle to the wind a ship can actually sail, and how its crew adjusts sail area for the weather.

**Why you would never guess this.** A square sail is powerful running before the wind and nearly useless trying to sail toward it, a purely geometric limit, the sail simply cannot hold enough wind on that point of sail to be useful; a lateen sail, hung from a yard at a steep angle with its leading edge (luff) able to point much closer to the wind, solves exactly that gap, letting a ship sail across the wind and, by tacking, effectively make progress against it. Fore-and-aft rigging (booms, gaffs, stays) generalises this further and, combined with a sternpost rudder (see 92_vehicles_flight.md), is what actually lets a captain choose a departure date rather than wait for a following wind. A jib, hung forward of the mast from a stay, is small and easy to handle and is the first sail a crew douses in worsening weather because removing it, counterintuitively, improves the ship's balance as it heels rather than just reducing power. A staysail fills the gap between mainsail and jib and matters mainly because many small, manageable sails are easier and safer for a crew to handle than one enormous one, distributing both load and labour. Reefing, rolling and lashing part of a sail to reduce its area in heavy weather, is slow and genuinely dangerous work done aloft on a moving yard, the main reason sailing ship crews needed real numbers and real skill, not just a captain.

**Prerequisites.** Existing Roman square-rig ships (85_transport_civil.md's ship_improvements entry), tr_sternpost_rudder for the full windward-sailing benefit.

**Roman-available inputs.** Flax or hemp sailcloth, hemp rope rigging, timber spars.

**Procedure.** (1) Cut sail shapes matched to purpose: square for running downwind, triangular lateen or fore-and-aft for working closer to the wind. (2) Rig stays fore and aft of each mast to carry jib and staysail. (3) Fit reef points, short lines sewn across the sail at intervals, so a crew can gather and lash a band of sail to a yard or boom to shorten it.

**How you know it worked.** A rigged vessel demonstrably makes headway on a course angled into the wind, tacking back and forth, something a pure square-rigger cannot do at all.

**Failure modes.** A jib left up too long in a squall unbalances and can broach the ship; a badly reefed sail can tear free entirely in a gust; fore-and-aft rigging with a failed stay can bring the mast down.

**Cost & labour.** ESTIMATED (basis: comparable to existing Roman sailmaking and rigging labour) moderate, mostly a redesign of existing sailmaking skill rather than new material.

**Danger.** Reefing and general sail-handling aloft in weather is genuinely dangerous work, falls and being struck by a swinging boom are real, recurring risks.

**Confidence: HIGH** - all of this is well within existing Roman textile, rope and shipbuilding skill (see 90_textiles.md for sailcloth); the only missing piece is rigging geometry, which is a design choice, not a material one.

---

### tr_bowsprit - Bowsprit, mast stepping and rigging hardware

Also covers: tr_mast_stepping, tr_rigging_block_lashing

**What it is / why you want it.** The structural spars and joints that carry a ship's rig: the bowsprit extending forward from the bow to anchor jib stays, the joint where each mast meets the hull, and the blocks and splices that make all the rope work hold.

**Why you would never guess this.** A bowsprit looks like a simple extended pole, but it lives under two opposing loads at once, compression from the jib's pull downward along its length and tension from the lashings holding it to the bow, and if the lashing fails the whole spar can fail suddenly under the unopposed compression, which is why bowsprit rigging is inspected as carefully as any load-bearing joint on the ship. Mast stepping, the joint where a mast meets the keel or deck, must carry both the sail's forward thrust and the bending moment from every gust, and a failed step doesn't bend the mast, it drops the entire rig, which is why mast failure reads in the historical record as total loss of the mast, not partial damage. Rigging block and rope lashing is quiet craft knowledge, invisible until it fails: a properly made splice keeps roughly 80 percent of the rope's original strength, while a badly made one can be far weaker and looks identical to the untrained eye, which is exactly why it is skilled, apprenticed work passed sailmaker to sailmaker rather than something written down and followed mechanically.

**Prerequisites.** 90_textiles.md rope-making, existing Roman shipwrighting.

**Roman-available inputs.** Oak or pine spars, hemp rope, wooden pulley blocks.

**Procedure.** (1) Step the mast into a deep, reinforced socket at the keel, wedged tight and checked under load before rigging. (2) Lash the bowsprit to the bow with multiple wrapped turns of strong rope, inspected regularly for wear at the friction points. (3) Train riggers to splice rope by hand, testing sample splices to failure to confirm the technique before trusting it aloft.

**How you know it worked.** A tensioned stay or lashing, struck, gives a taut, high-pitched sound, not a slack, dull one; a sample splice pulled to failure on a test bench breaks near, not at, the splice, showing the splice itself held.

**Failure modes.** A worn or under-lashed bowsprit snaps under jib load; a badly stepped mast works loose and eventually topples; a bad splice fails invisibly until the exact moment of maximum load.

**Cost & labour.** ESTIMATED 1-3 artisan-days for stepping and lashing per mast; splicing skill is a training investment, not a material cost.

**Danger.** A failed mast or bowsprit at sea can kill crew outright and cripple the ship far from any repair yard.

**Confidence: HIGH** - entirely within existing Roman rope and timber craft; the risk is skill transfer, not material availability.

---

### tr_sternpost_rudder - Propulsion: rudder, propeller and shafting

Also covers: tr_screw_propeller, tr_variable_pitch_propeller, tr_paddle_wheel, tr_reduction_gearing, tr_stern_tube

**What it is / why you want it.** The centred rudder that gives real steering control, and the family of propulsion devices, paddle wheel, screw propeller, and the shafting and gearing that connects them to an engine.

**Why you would never guess this.** See 92_vehicles_flight.md's full sternpost_rudder entry for the core case: a single centred blade on pintles gives far more steering leverage than side-hung steering oars, and that leverage is what lets a ship point high into the wind and tack, meaning it lets a captain choose a departure date instead of waiting for a following wind. On propulsion, a paddle wheel is simple to build and understand but throws water both up and back, wasting real energy, and it gets dramatically worse in rough seas as the wheel alternately buries too deep and lifts clear of the water; a screw propeller under the waterline stays submerged regardless of roll and is more efficient, but only if its shaft is precisely aligned, because any misalignment sends a vibration straight into the bearings that will eventually wear them out. A variable pitch propeller lets the blades' angle be changed in operation, which allows reversing thrust without reversing the engine itself, useful because reversing a large steam or diesel engine's rotation is slow and mechanically complex. Reduction gearing exists because a turbine spins far faster than any propeller can usefully turn without cavitating and losing grip on the water, so gearing steps that speed down while stepping torque up, and the gear teeth must be precisely cut and case-hardened or the losses in the gearing itself eat the efficiency gain the turbine was supposed to provide. A stern tube is the unglamorous seal where the propeller shaft passes out through the hull, packed to compress against the rotating shaft and keep the sea out while still letting the shaft spin freely, one of the more failure-prone points on any powered ship.

**Prerequisites.** See 92_vehicles_flight.md sternpost_rudder and screw_propeller entries for the base case; this entry extends to variable pitch, reduction gearing and shaft sealing.

**Roman-available inputs.** Bronze for propeller blades and stern tube, iron for the rudder and pintles, hardened steel for reduction gearing.

**Procedure.** (1) Hang a single blade rudder on pintle-and-gudgeon fittings at the sternpost. (2) Cast a multi-blade screw propeller, balance it carefully before fitting. (3) Align the shaft precisely between engine and propeller, running it through a packed stern tube. (4) Where engine speed exceeds usable propeller speed, fit case-hardened reduction gears between them.

**How you know it worked.** A screw-driven ship at speed shows no unusual vibration through the hull; a stern tube, checked after a voyage, shows the packing still compressed and dry outside, not weeping continuously.

**Failure modes.** A misaligned shaft vibrates and wears bearings prematurely; a worn stern tube packing lets water in steadily, requiring constant bilge pumping; a paddle wheel in a following sea alternately over- and under-bites the water, losing power erratically.

**Cost & labour.** ESTIMATED (basis: precision casting and shaft alignment work, comparable to fine machine-tool fabrication) high skilled labour cost, this is among the harder marine entries to execute well.

**Danger.** A failed stern tube seal can flood a ship if not caught; propeller work near a running shaft is a serious entanglement and crush hazard.

**Confidence: HIGH** for the rudder (already covered and attested in 92_vehicles_flight.md); MEDIUM for propeller and shafting precision at Roman-era tolerances.

---

### tr_marine_engine - Marine steam and diesel propulsion machinery

Also covers: tr_triple_expansion, tr_marine_turbine, tr_marine_diesel, tr_water_tube_boiler

**What it is / why you want it.** The engines that actually turn a ship's propeller: reciprocating steam engines connected directly to the shaft, multi-stage expansion engines that extract more work per unit of coal, steam turbines, and marine diesel engines, plus the water-tube boilers that feed steam to them.

**Why you would never guess this.** A marine steam engine cannot simply be a stationary engine bolted to a hull, it must run continuously for days or weeks without the maintenance access a land-based plant gets, and its crankshaft connects directly, horizontally, to the propeller shaft rather than through a flywheel and belt as a stationary mill engine would. Triple expansion pushes the same coal-saving logic as the compound rail entry (see tr_slide_valve above) one stage further: steam expands successively through three cylinder sizes, high, intermediate, low pressure, extracting noticeably more mechanical work from the same steam before it is finally exhausted, which is exactly why triple expansion engines became the standard workhorse of ocean freight for decades. A marine turbine spins far faster and smoother than a piston engine but needs the reduction gearing described above to be useful at propeller speed, and its rotor must be balanced with real precision, an imbalanced turbine at operating speed will tear itself apart. A water tube boiler inverts the locomotive boiler's arrangement, water runs inside tubes surrounded by furnace gas rather than gas running through tubes surrounded by water, which raises steam faster and more safely at higher pressure because a ruptured tube vents far less stored energy than a ruptured large shell would. Marine diesel is the efficiency endpoint of this whole chain: a marine diesel is far larger and slower-turning than any automotive engine, can drive the propeller shaft directly without an intermediate boiler at all, and its fuel, heavy bunker-grade petroleum residue, is itself a genuine supply constraint tied to 93_energy.md's refining chain.

**Prerequisites.** 93_energy.md boiler and internal combustion fundamentals, tr_locomotive_boiler's tube and pressure-vessel lessons, tr_reduction_gearing for turbines.

**Roman-available inputs.** Wrought iron/steel boiler and cylinder material, refined petroleum products for diesel fuel where available (93_energy.md).

**Procedure.** (1) Build a horizontal, direct-drive engine connecting crankshaft to propeller shaft. (2) For triple expansion, size three cylinder stages so each receives the prior stage's exhaust at a useful pressure. (3) For a water tube boiler, run water through tubes exposed directly to furnace gas, collecting steam in a drum above. (4) For diesel, build a large, slow-turning compression-ignition engine driving the shaft directly.

**How you know it worked.** A triple-expansion engine shows a visibly quieter exhaust and measurably lower coal consumption per mile than a single-expansion engine of comparable power; a water tube boiler raises usable steam pressure noticeably faster from cold than an equivalent fire-tube design.

**Failure modes.** An unbalanced turbine rotor destroys itself at speed; a water tube boiler with scaled or fouled tubes loses efficiency and can locally overheat; diesel fuel contamination or poor injection timing fouls combustion badly.

**Cost & labour.** ESTIMATED (basis: major capital project, comparable to 93_energy.md's largest stationary plant entries) among the largest single capital investments in this module.

**Danger.** Any marine boiler failure at sea is catastrophic and far from help; a spinning unbalanced turbine is genuinely lethal shrapnel.

**Confidence: MEDIUM** - the mechanisms are well documented; achieving reliable continuous-duty operation at Roman-era manufacturing tolerance is the real open question.

---

### tr_windlass - Deck machinery: windlass, capstan, anchor, chain, bilge pump, ballast, block and tackle

Also covers: tr_capstan, tr_stockless_anchor, tr_chain_cable, tr_bilge_pump, tr_ballast_tank, tr_block_tackle

**What it is / why you want it.** The mechanical aids a crew uses to handle anchors, cargo weight distribution, and the water that inevitably gets into any wooden or riveted hull.

**Why you would never guess this.** A windlass and a capstan solve the same problem, multiplying human force to haul something very heavy, by gearing it down through a geared drum (windlass, horizontal axle) or a simple lever-turned vertical axle (capstan); without gear reduction, no reasonable number of sailors can haul a large ship's anchor and chain against water resistance and its own dead weight at all, gearing is not a convenience here, it is the difference between possible and impossible. Chain cable replaces rope for anchoring specifically because chain does not rot and does not chafe through on a rocky bottom the way rope eventually does, but every link must be perfectly closed, forge-welded shut, because a single flawed link opens under the anchor's full holding load and the ship is adrift. A stockless anchor, with flukes that pivot on a pin instead of a rigid crossbar (the "stock"), stows flat against the hull and needs none of the complex rigging an old-style stocked anchor requires to haul aboard and secure. A bilge pump exists because a ship always leaks, seams work, planks swell and shrink, and a crew pumping in relays is simply the accepted, continuous cost of a wooden hull at sea, not a sign anything has gone wrong. Ballast tanks let a ship adjust its trim and stability using pumped seawater rather than loaded stone or sand, but that water must be distributed and shifted carefully, because uneven ballast can make a ship dangerously unstable in exactly the way loose cargo does. Block and tackle, multiple pulleys sharing a load, gives real mechanical advantage, roughly proportional to the number of rope parts, but every additional pulley adds its own friction and weight, so very large tackles start losing efficiency to their own hardware past a certain point.

**Prerequisites.** Iron chain forging, existing Roman shipboard rope and pulley technique.

**Roman-available inputs.** Iron for chain and windlass gearing, oak for capstan and blocks, hemp rope.

**Procedure.** (1) Build a geared windlass or a plain capstan sized to the anchor weight expected. (2) Forge chain links and weld each one fully shut, tested individually under load before use. (3) Fit ballast pumps and distribution valves to shift seawater between tanks. (4) Rig block and tackle with the fewest parts that still give adequate mechanical advantage for the job.

**How you know it worked.** A capstan or windlass hauls the loaded anchor aboard with a reasonable crew of a handful of men, not dozens; a bilge, pumped on a normal watch schedule, never rises faster than the crew can keep ahead of it in ordinary weather.

**Failure modes.** An unwelded or flawed chain link opens under load and loses the anchor; neglected bilge pumping lets water accumulate faster than a later crew can clear; uneven ballast distribution makes the ship dangerously tender (prone to excessive rolling).

**Cost & labour.** ESTIMATED (basis: standard Roman shipboard ironwork and carpentry) moderate, well within routine shipyard capability.

**Danger.** A parted anchor chain or cable under load can whip back across the deck with lethal force; poor ballast management has capsized ships historically.

**Confidence: HIGH** - all of this is straightforward mechanical advantage and metalwork, no exotic material or process required.

---

### tr_marine_chronometer - Navigation instruments: chronometer, sextant, gyrocompass, log, lighthouse, ship telegraph

Also covers: tr_sextant_navigation, tr_gyrocompass_repeater, tr_log_sounding, tr_lighthouse_fresnel, tr_ship_telegraph

**What it is / why you want it.** The instrument cluster that lets a ship know where it is, how fast it is going, how deep the water is, where the shore is at night, and how the bridge communicates with the engine room.

**Why you would never guess this.** See 92_vehicles_flight.md's marine_chronometer entry for the core longitude case: a spring-driven timepiece that loses time to temperature-driven expansion is useless for navigation until compensated, because longitude is fundamentally a clock problem, not a sailing problem. A sextant measures the angle between a celestial body and the horizon using two mirrors, one half-silvered, letting the navigator see both at once and read the angle directly, and its accuracy depends entirely on the optical flatness and silvering quality of those mirrors (30_glass_optics.md), a genuine manufacturing bottleneck, not a conceptual one. A gyrocompass repeater is not a second gyrocompass, it is a simple dial slaved electrically to one large, accurate master compass elsewhere in the ship, so multiple stations can read the same true heading without each needing its own delicate spinning mechanism; keeping repeaters synchronised with the master as it corrects itself is the real engineering task. A log line, knotted rope paid out and timed, and a sounding line, weighted and marked in fathoms, are almost embarrassingly simple by comparison, and that simplicity is exactly why they remained standard for so long, they need no calibration beyond a known knot spacing and a counted interval. A Fresnel lens steps a lens's curved surface into concentric rings instead of grinding one continuous curved lens, which achieves the same focusing power at a fraction of the glass weight and volume, letting a lighthouse throw a strong beam many miles out to sea from a practical, liftable lens. A ship's telegraph replaces shouted or run orders between bridge and engine room with a simple mechanical dial and bell system, because on a large ship the engine room genuinely cannot hear the bridge at all.

**Prerequisites.** 30_glass_optics.md for mirrors and lenses, 50_electricity.md for gyrocompass repeaters, 60_mathematics_method.md for celestial navigation calculation.

**Roman-available inputs.** Glass and silvered bronze for sextant mirrors, brass for chronometer and telegraph mechanisms, blown and ground glass for the Fresnel lens.

**Procedure.** (1) Grind and silver flat mirrors for the sextant, mount on a graduated arc. (2) Build a temperature-compensated balance-wheel chronometer, gimbal-mounted to stay level. (3) Cast a stepped Fresnel lens in rings around a central light source. (4) Wire a master gyrocompass to remote dial repeaters. (5) Connect bridge and engine room with a mechanical lever-and-bell telegraph.

**How you know it worked.** A sextant reading of a known star's altitude matches the value predicted by almanac tables for that time and place within a small margin; a Fresnel lighthouse lamp is visible from a measured distance well beyond a plain lensless flame of equal brightness.

**Failure modes.** An uncompensated chronometer drifts with temperature and gives false longitude; tarnished sextant mirrors dim and blur the sighted image; an unsynchronised gyrocompass repeater misleads the helm.

**Cost & labour.** ESTIMATED (basis: fine instrument-making labour, comparable to precision clockwork) high per unit, these are skilled-craft items, not mass-produced ones, at this stage.

**Danger.** None physical; the danger of a bad instrument is entirely navigational, a wrong position estimate runs a ship onto rocks.

**Confidence: MEDIUM** - each mechanism is documented and buildable with Roman-quality glass and metalwork, but achieving reliable precision (especially the chronometer) is a genuine open craft problem, see 92_vehicles_flight.md for the fuller discussion.

---

### tr_lifeboat - Lifeboat, submarine hull and periscope

Also covers: tr_submarine_hull, tr_periscope

**What it is / why you want it.** A small emergency boat built to save a crew, and the specialised hull and optics of a submersible vessel.

**Why you would never guess this.** A lifeboat has to satisfy two goals that trade against each other, strong enough to carry a full load of frightened people in bad weather, yet light enough that a handful of sailors can hoist it out on hand-cranked davits under those same bad conditions; early poorly designed lifeboats swamped or capsized precisely because that balance was got wrong, cork or sealed air compartments built into the hull are what actually kept a swamped boat afloat rather than sinking. A submarine hull's core constraint is geometry, not material: it must be round in cross-section to distribute outside water pressure evenly, because any flat panel concentrates that pressure and risks sudden catastrophic collapse, which is also why riveted seams, reliable on a surface ship, are genuinely unsafe at depth and historically limited early submarines to shallow operation until welded or better-sealed construction existed. A periscope is optically simple, a tube with a mirror or prism at each end bending the light path ninety degrees twice, but the whole device lives or dies on mirror quality, a tarnished or poorly silvered mirror dims the image until the device is nearly useless exactly when it matters most.

**Prerequisites.** tr_carvel_planking or tr_iron_hull, 30_glass_optics.md for the periscope mirrors.

**Roman-available inputs.** Light timber and cork for lifeboats, riveted or welded iron for a submarine pressure hull, silvered glass or polished bronze for periscope optics.

**Procedure.** (1) Build a light hull with sealed buoyant compartments and simple hand-cranked davits for launching. (2) For a submarine, build a fully round-section hull, avoid any flat panel below the pressure line. (3) For a periscope, mount angled mirrors at each end of a sealed tube passing through the hull.

**How you know it worked.** A swamped lifeboat, deliberately flooded in calm water as a test, still floats level rather than sinking; a periscope image remains bright and clear, not dim or doubled.

**Failure modes.** A lifeboat without sealed buoyancy compartments sinks once swamped; a submarine hull with any flat panel or poor seam risks sudden collapse under pressure; a tarnished periscope mirror renders the device nearly blind.

**Cost & labour.** ESTIMATED moderate for lifeboats, high for a pressure-tested submarine hull given the consequences of getting it wrong.

**Danger.** A submarine is the single most physically dangerous vessel in this module, a hull failure at depth is instantly fatal to the crew with no warning; treat depth testing as an unmanned, remote-monitored process, never a manned first test.

**Confidence: HIGH** for lifeboats; LOW for submarine hulls, where Roman-era riveting and welding quality control genuinely may not be adequate for safe depth, and the consequences of being wrong are total.

---

### tr_dry_dock - Shipyard infrastructure: dry dock, slipway, tugs, dredging

Also covers: tr_slipway_launch, tr_tug, tr_dredger

**What it is / why you want it.** The facilities and support vessels that let you build, launch, repair and manoeuvre ships, and keep the channels they use clear.

**Why you would never guess this.** A dry dock's entire function depends on one uncompromising requirement, its gates must seal absolutely perfectly, because any leak at all does not stay small, it fills the dock and re-floats or damages the ship you were trying to work on below the waterline, so gate construction and maintenance get disproportionate attention relative to the rest of the structure. A slipway looks like the simple option, just an inclined ramp the finished hull slides down into the water, but the launch angle and the grease or soap used to reduce friction must be calculated correctly, because too steep or too slick and the hull accelerates uncontrollably down the ways, a real risk to the ship and to anyone nearby. A tug is a strange-looking vessel by ordinary standards, hugely powerful engine and boiler relative to its size with almost no cargo space, because its entire job is generating maximum torque and manoeuvrability in tight harbour quarters, not carrying anything. A dredger exists because harbours and channels silt up continuously and need active, ongoing removal of mud and sediment, and that sediment is genuinely abrasive, wearing out pump impellers and bucket-dredge liners steadily, dredging is a maintenance cost that never ends, not a one-time dig.

**Prerequisites.** tr_carvel_planking/tr_iron_hull for the ships being served, 85_transport_civil.md's harbours_and_dredging entry for the broader harbour context.

**Roman-available inputs.** Timber and iron for dock gates, greased timber ways for slipways, small high-power steam engines for tugs (93_energy.md), iron buckets or pump components for dredgers.

**Procedure.** (1) Build dock gates with multiple redundant seals, tested by controlled partial flooding before trusting them with a ship inside. (2) Calculate slipway angle against hull weight and chosen lubricant to keep launch speed controlled. (3) Build a compact, high-power tug hull around an oversized engine relative to its size. (4) Fit a dredger with a belt-driven bucket chain or a suction pump, using wear-resistant liners where sediment contacts moving parts.

**How you know it worked.** A dry dock, pumped dry and left overnight, shows no measurable water rise by morning; a slipway launch reaches the water at a controlled, predictable speed, not an uncontrolled rush.

**Failure modes.** A leaking dock gate floods the dock and can damage the ship inside; a miscalculated slipway launch runs the hull out of control; a dredger with worn liners loses capacity steadily until it is no longer economical to run.

**Cost & labour.** ESTIMATED (basis: comparable to major harbour works, 85_transport_civil.md) substantial civic infrastructure investment, best undertaken alongside harbour development generally.

**Danger.** An uncontrolled slipway launch can crush anyone in the hull's path; a failed dock gate is a major property loss, not usually a life-safety one if evacuated in time.

**Confidence: HIGH** - all of this extends existing Roman harbour and hydraulic engineering competence (85_transport_civil.md) directly.

---

### tr_canal_lock - Canal lock and canal lift

Also covers: tr_canal_lift

**What it is / why you want it.** The pound lock, already covered in depth in 85_transport_civil.md's canals_and_locks entry, and its rarer, more mechanically complex alternative, the vertical canal lift.

**Why you would never guess this.** A lock's difficulty is not the chamber, it is discipline: gates must seal perfectly and be operated in a strict fill-then-open sequence, because operating them out of order or with a leak simply drains the lock and strands the boat, a lock keeper's skill is procedural as much as mechanical. A canal lift replaces a flight of several locks with one vertical motion, a large water-filled tank carrying the boat, raised or lowered by counterweight or a steam engine, which sounds like a pure improvement but is rarely worth it in practice: it is mechanically far more complex and expensive than an equivalent series of simple locks, and is really only justified where the change in level is very large and land for a long lock flight is unavailable.

**Prerequisites.** 85_transport_civil.md canals_and_locks entry (read that one first, this is a supplement).

**Roman-available inputs.** Oak gates and chamber timber, iron fittings, a counterweight or small steam engine for the lift variant.

**Procedure.** (1) Build a standard mitre-gated pound lock per 85_transport_civil.md. (2) Where a lift is genuinely justified, build a sealed water tank sized to float the largest boat expected, raised on guided rails by counterweight or engine.

**How you know it worked.** A lock cycles a boat through a level change with no measurable water loss beyond the single chamber-full per passage; a lift tank, loaded and raised, shows no more than trivial water spillage at the seal.

**Failure modes.** A leaking lock gate drains the pound above it, stranding traffic; a canal lift's far greater mechanical complexity multiplies the number of things that can fail relative to a simple lock flight.

**Cost & labour.** ESTIMATED (basis: 85_transport_civil.md's lock cost figures) a lock is comparatively cheap; a lift is a major standalone engineering project, justify it only where a lock flight genuinely will not fit.

**Danger.** None beyond ordinary construction risk; the main risk of a lift is economic, over-building a complex solution where a simple one would serve.

**Confidence: HIGH** for the lock (see 85_transport_civil.md); MEDIUM for the lift, which is a genuinely rare, niche solution even in the historical record.

---

## Sources and confidence

Most of this module describes 18th to 20th century industrial mechanisms whose physics is textbook and whose failure modes are documented in the historical operating record (hot boxes, screwman injuries, boiler explosions, lifeboat swamping). Confidence on mechanism is generally HIGH to MEDIUM throughout. The consistent LOW-to-MEDIUM points are: (1) achieving the fabrication tolerance modern factories take for granted using hand tools and Roman-era metallurgy, most acute in valve gear, synchromesh gearboxes, and precision bearings; (2) any component depending on rubber (tl_pneumatic_tyre and its cluster), which depends entirely on the expedition described in 95_expeditions.md and has no Roman-native substitute; (3) submarine hulls, where the cost of an undetected flaw is total and unrecoverable; (4) exact cost and labour figures, which are marked ESTIMATED throughout with the reasoning given, never presented as measured fact. No numbers in this module are invented; where a real historical figure exists it is marked MEASURED, where a figure is reasoned from a stated basis it is marked ESTIMATED or DERIVED, and cost figures in denarii are deliberately avoided in favour of artisan-days where the underlying wage data was not available to check.

## Where to go next

- [85_transport_civil.md](85_transport_civil.md) - the freight arithmetic, Roman baseline civil engineering, canals and locks in full, and the case for a railway at all.
- [10_metallurgy.md](10_metallurgy.md) - bulk iron and steel production, the actual bottleneck behind rail rolling, boiler plate, gear steel and hull plating throughout this module.
- [93_energy.md](93_energy.md) - boilers, superheating, safety valves and internal combustion fundamentals that every steam and motor entry above assumes.
- [95_expeditions.md](95_expeditions.md) - where rubber, and any other material this module flags as non-Roman, actually comes from and what it costs to go get it.
