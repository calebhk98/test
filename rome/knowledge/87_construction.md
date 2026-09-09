# Module 87: Construction Engineering

Say the honest thing first, or a builder who raised the Pantheon's dome will stop listening. Rome already has hydraulic concrete that cures underwater and strengthens for decades, the true arch and the groin vault, aqueducts crossing valleys, and a corps of military engineers as competent as any modern army's. If your plan is "teach Romans to build," burn it.

What Rome lacks is four things, and all 101 items below serve one of them. First: a cement consistent on the hundredth batch, not riding on which shore the ash came from and the mason's eye that morning. Second: iron, then steel, doing real work in tension, since Rome has wrought iron for cramps but no cast iron in the West, no crucible steel of its own, nowhere near a load-bearing frame's tonnage. Third: the theory of the beam, the mathematics of *why* a proportion works, not just that it worked last time, so a span can change without rebuilding a failure to find the new limit. Fourth: machinery of scale, cranes, mixers, pumps, needing continuous mechanical power Rome has only in trickle amounts (`40_power_precision.md`). Fix those roughly in order and the rest is carpentry.

---

### cn_pozzolana_concrete - Pozzolana hydraulic concrete (*opus caementicium*)

**What it is.** Quicklime plus volcanic ash, sets underwater, gains strength for decades. Already Roman; noted here only to give the tech tree a node.
Also covers: cn_mortar.

**Why never guess.** Nothing here for a Roman. For a modern reader: not lesser Portland cement, chemically different, arguably better for marine work. Full account: `85_transport_civil.md#concrete_and_cement`.

**Prerequisites.** Lime burning, pozzolana access, formwork.

**Roman inputs.** *Calx* (quicklime), *pulvis puteolanus* (pozzolana, Bay of Naples), *caementa* (rubble). Plain lime mortar without pozzolana is the everyday binder.

**Procedure.** Slake lime, mix with pozzolana and rubble near Vitruvius's ratio (II.6, verify locally), pack in formwork, cure. Real addition: cast a labelled test cylinder per batch, crush at intervals, log it, something no Roman source does.

**How you know.** A month-old cylinder resists the logged load; an opened underwater section rings hard, not crumbly.

**Failure modes.** Weak ash never fully hardens; batch variation is invisible without testing.

**Cost.** DERIVED: one foreman, a wax tablet.

**Danger.** Slaking lime burns skin/eyes, wash immediately. No social danger.

**Confidence: HIGH.**

### cn_quarrying_wedge - Stone quarrying with wedges

**What it is.** Splitting stone along a chosen plane, already routine in every legionary quarry.
Also covers: cn_stone_saw, cn_stone_polish, cn_gang_saw.

**Why never guess.** Nothing here for a Roman either.

**Prerequisites.** Iron wedges, a reader of the grain.

**Roman inputs.** Iron *cunei*, Naxos emery for polish, sand and water for sawing, the abrasive cuts, the blade only guides.

**Procedure.** Mark holes along bedding, drive wedges in sequence, listen for the pitch change of a true crack. Saw with wet sand under the blade; polish through finer emery by hand. Gang saw is the real addition, parallel blades cutting one block into slabs at once, the hard part is equal blade tension, one that binds ruins the block.

**How you know.** Split face follows the marked line.

**Failure modes.** Out-of-sequence wedges split wrong; unequal gang-saw tension warps the cut.

**Cost.** MEASURED: a block splits in a day; an obelisk blank is a season (Aswan).

**Danger.** Flying chips, crushed fingers, collapsing faces.

**Confidence: HIGH.**

### cn_true_arch - True arch in stone (*fornix*)

**What it is.** Compression-only load path around an opening. Already extensive Roman practice.
Also covers: cn_groin_vault, cn_ribbed_vault, cn_flying_buttress.

**Why never guess.** Missing is not the arch but calculating safe thickness instead of copying a proportion into a bigger arch where it quietly fails. The thrust line, the true compression path, must stay inside the stone everywhere; nobody in 100 AD can compute that curve, so they build thick and watch.

**Prerequisites.** `cap_tol_1mm`, cn_quarrying_wedge, centring carpentry.

**Roman inputs.** Cut voussoirs, or concrete over struck centring, brick ribs (Pantheon).

**Procedure.** Groin vault: two barrels crossing at right angles, load onto four corner points, extend deliberately for wall space. Ribbed vault: build ribs first as a light skeleton, thin webs after, load path visible by eye. Flying buttress: an arch leaping from a high wall to a free pier, carrying thrust away so the wall stays thin, useful only where thin tall walls matter.

**How you know.** No sag against a straightedge a year after striking centring.

**Failure modes.** Thrust escaping at the haunches (hinge-crack); webs poured before ribs set, collapsing the skeleton; undersized buttress abutment pushed over.

**Cost.** ESTIMATED, scales roughly with span cubed; a bay is weeks, cathedral scale a generation.

**Danger.** Falling centring, the deadliest trade here.

**Confidence: HIGH** baseline, **MEDIUM** rib/buttress transfer without calculus.

### cn_crane_treadwheel - Treadwheel crane (*polyspastos*)

**What it is.** Man-powered drum crane, already Roman, raising tonnes with a handful of men.
Also covers: cn_block_tackle_hoist.

**Why never guess.** Vitruvius describes it (*De Arch.* X). Worth stating: advantage equals rope parts under load, minus 10-20% to sheave friction (ESTIMATED, typical wooden-sheave loss).

**Prerequisites.** Hemp rope, timber, bronze bearings.

**Roman inputs.** Hemp rope, seasoned timber, bronze pulleys.

**Procedure.** Rig rope through multiple blocks, each part shares load. A treadwheel converts body weight, not arm strength, into pull.

**How you know.** Load rises smoothly; creep means a worn or wet sheave groove.

**Failure modes.** Sheave slip; overloading one rope part snaps it without warning.

**Cost.** MEASURED, attested at multi-tonne lifts empire-wide.

**Danger.** Snapped rope, or an operator caught by an overrunning wheel.

**Confidence: HIGH.**

### cn_scaffolding - Timber scaffolding system

**What it is.** Temporary timber platform for working at height, already routine.

**Why never guess.** Obvious once wanted. Non-obvious point: lashing discipline, not lumber, holds it together, one untied joint can unravel a bay.

**Prerequisites.** Timber poles, rope or withies.

**Roman inputs.** Fir/pine poles, hemp rope, green withy.

**Procedure.** Erect standards, tie ledgers at working height, brace diagonally, double every load-bearing lashing, inspect for creep daily.

**How you know.** No sag under a loaded plank; a shove doesn't rack the frame.

**Failure modes.** One failed lashing propagates as load redistributes onto ties not sized for it.

**Cost.** MEASURED, a normal minor cost line.

**Danger.** Falls, the trade's main hazard.

**Confidence: HIGH.**

### cn_aqueduct - Masonry aqueduct arch bridge (*aqua ducta*)

**What it is.** Level water channel across a valley on an arcade, already Roman at huge scale, nine lines feeding Rome per Frontinus.
Also covers: cn_siphon, cn_sewer_system, cn_water_main.

**Why never guess.** Pressure in an open channel is static per section, so one arch's failure among dozens is local, unlike a single point of failure in a pressurised pipe.

**Prerequisites.** cn_true_arch, chorobates levelling (`85_transport_civil.md#surveying_precision`).

**Roman inputs.** Cut stone/concrete arcading, lead pipe (*fistulae plumbeae*) or safer ceramic (*fistulae fictiles*, Vitruvius's preference), ceramic sewer pipe.

**Procedure.** Level a gentle continuous fall, arcade across deep valleys, drop into an inverted siphon (sealed pipe down and back up, driven by head) where an arcade would be absurd, drain waste through sloped sewer pipe. A siphon must stay full and sealed, one trapped air pocket stops flow; sediment collects at the low point.

**How you know.** Continuous matched flow at delivery, no hammering in the siphon.

**Failure modes.** One arch failure drops the channel locally; an air lock halts a siphon; unflushed sediment chokes a main.

**Cost.** MEASURED, Rome's own system is the evidence.

**Danger.** Collapsing arcading in construction; lead is a slow chronic risk.

**Confidence: HIGH.**

### cn_portland_cement - Portland cement powder

**What it is.** A binder fired hot enough to clinker, not merely calcine, giving strength and consistency pozzolana cannot match batch to batch.
Also covers: cn_rotary_cement_kiln, cn_cement_clinker_grinding, cn_gypsum_plaster, cn_artificial_stone.

**Why never guess.** "Cement" tricks a visitor into thinking Rome has this. Lime burning calcines around 900-1000 C; Portland clinker needs roughly 1450 C, hot enough the raw meal partly melts and recombines into calcium silicates pozzolana never forms, a different kiln, not a stronger old one. Grinding the clinker after matters almost as much as firing: unground clinker is nearly inert.

**Prerequisites.** `cap_heat_1600` (~`10_metallurgy.md#high_temp_furnace`), limestone/clay quarrying, a mechanical mill (`40_power_precision.md#water_power_scaleup`).

**Roman inputs.** Limestone, clay, gypsum (Cyprus, Sicily, already traded).

**Procedure.** Grind limestone:clay roughly 4:1 (ESTIMATED) into slurry. Feed a rotary kiln, tilted, turning 1-3 rpm; flame at the hot end must reach roughly 1800 C to hold material at 1450 C. Output is clinker, dark glassy nodules; quench, cool, grind fine with a little gypsum to slow the set; grinding heats the mill, and overheated cement hydrates inside it, ruining the batch, cool while grinding. Gypsum plaster separately: calcine under 200 C, sets in minutes, ruined by rain outdoors.

**How you know.** Clinker rings, doesn't slake in water; ground cement sets hard within hours.

**Failure modes.** Underfired clinker stays chalky; overheated cement flash-sets in the mill.

**Cost.** ESTIMATED, a generation-scale industrial project, not a first attempt.

**Danger.** Kiln burns, refractory collapse, silicosis from grinding dust.

**Confidence: HIGH** chemistry/temperatures, **LOW** near-term Roman timeline.

### cn_post_lintel - Post and lintel, the theory of the beam

**What it is.** The plain beam across two supports, and the mathematics of why it holds or breaks, which nobody in 100 AD has though everybody builds beams.
Also covers: cn_cantilever.

**Why never guess.** The real kernel of this module. A loaded beam bends: top fibre shortens (compression), bottom stretches (tension), a neutral plane between carries nothing. Stone and plain concrete are weak in tension, so they fail bottom-up, invisible until nearly through. Deflection scales with the *cube* of span, so doubling length gives eight times the sag for the same load, why copying a proportion at twice scale fails badly. A cantilever's fixed end carries the full moment alone, worst exactly where it can't be seen.

**Prerequisites.** `cap_tol_1mm`, timber or dressed stone.

**Roman inputs.** Seasoned oak or fir, dressed stone, iron cramps.

**Procedure.** Keep material where tension occurs, never exceed a span already tested to failure. Treat a cantilever's fixed end as the critical section.

**How you know.** A test beam loaded to sag, not failure, springs back near-straight; permanent set means you're near the limit.

**Failure modes.** Invisible bottom-fibre cracking; cantilevers extended past a tested length fail with little warning.

**Cost.** ESTIMATED, one destroyed test sample per unproven span.

**Danger.** Sudden unannounced collapse.

**Confidence: HIGH** physics and Roman ignorance of formal theory, **MEDIUM** how much survives as craft rule.

### cn_king_post - King post roof truss

**What it is.** A triangular timber frame converting bending into pure tension and compression, spanning further than one beam.
Also covers: cn_queen_post, cn_timber_truss, cn_trussed_arch.

**Why never guess.** Wood is strong along the grain, weak in long unsupported bending. Triangulate it, a central post in pure compression, rafters and tie beam closing a triangle, and every member works its strong direction, at the cost of needing every joint to actually hold.

**Prerequisites.** cn_post_lintel, joinery, iron strap at tie joints.

**Roman inputs.** Seasoned timber, iron straps and pins, since mortise-and-tenon alone creeps under sustained load.

**Procedure.** King post: one central post, narrow spans. Queen post: two posts set inward, shorter unsupported tie beam, wider spans. Timber truss: more members, still wider roofs. Trussed arch: timber bracing bolted onto a masonry arch to resist its outward spread, letting a thinner arch stand.

**How you know.** No visible ridge sag after a full seasonal load; no daylight gap at joints.

**Failure modes.** One slipped joint racks the whole triangle; timber failure is progressive, sag grows year on year.

**Cost.** MEASURED order of magnitude, days to weeks per bay.

**Danger.** Falling timbers during erection; a failed truss drops a whole roof at once.

**Confidence: HIGH** triangulation, **MEDIUM** exact Roman-attested geometry.

### cn_cast_iron_beam - Cast iron beam

**What it is.** A beam cast in iron, far stronger in compression than stone or timber. First item gated on the metal itself, not calculation.
Also covers: cn_iron_column.

**Why never guess.** The classic killer: cast iron is brittle, weaker in tension than compression by roughly a third to half (ESTIMATED, known grey-iron ratios), almost no warning before snapping. A beam's bottom fibre is in tension, exactly where stone-trained instinct says thickness matters least. Columns are the opposite done right: pure compression, cast iron's strength, so hollow cast iron columns genuinely work and cast iron beams genuinely don't.

**Prerequisites.** Cast iron supply (`10_metallurgy.md#blast_furnace_cast_iron`, absent in the Roman West, bloomery gives only wrought iron), cn_post_lintel.

**Roman inputs.** None directly. Once cast iron exists: sand moulds, a foundry, remelted pig iron.

**Procedure.** Columns: cast hollow, load only in pure axial compression. Beams: prefer wrought iron or steel; if used, thicken the tension face, test to failure at small scale first, never trust shock loading, fracture starts from a casting flaw and every casting has some.

**How you know.** A column carries rated load with no deformation; there's no reliable visual warning before a beam fails.

**Failure modes.** Sudden brittle fracture, cause of several 19th-century collapses; hidden casting flaws halving real strength.

**Cost.** ESTIMATED, gated entirely on bulk cast iron existing first.

**Danger.** Sudden collapse with no warning, the deadliest failure mode here.

**Confidence: HIGH** tension/compression asymmetry, **MEDIUM** exact ratios.

### cn_wrought_iron_girder - Wrought iron girder, and later steel

**What it is.** Getting iron to actually hold tension: wrought iron first, ductile and forgiving, then cheap bulk steel once `10_metallurgy.md`'s finery-to-crucible chain runs.
Also covers: cn_rolled_I_beam, cn_plate_girder, cn_box_girder, cn_steel_frame_skeleton.

**Why never guess.** The obvious move after cast iron fails is "more iron"; the correct move is a different iron. Wrought iron's fibrous grain deforms visibly before breaking, unlike cast iron. Riveted girders flex and spring back, that flex is the warning system. Rolling one I-section needs a mill squeezing the whole cross-section through shaped rollers. A box girder resists twisting far better than an open I, which has almost no torsional stiffness. A steel skeleton moves all load into a grid, walls become weathertight skin only, the change that makes tall buildings possible.

**Prerequisites.** `10_metallurgy.md#finery_forge`, `cementation_steel`/`crucible_steel`, rolling needs `40_power_precision.md#water_power_scaleup` or steam.

**Roman inputs.** Bloomery wrought iron bar, routine but small-batch, nowhere near structural tonnage.

**Procedure.** Forge-weld plates into a riveted girder, deep web for stiffness, thick flanges (flanges carry bending, web carries shear). Once rolling exists, roll one I-bar instead. Close a girder into a box by welding both flange edges shut where twisting matters.

**How you know.** A girder deflects predictably, returns to true; a box resists hand-twisting an open section would not.

**Failure modes.** Rivets sheared by vibration loosen invisibly; an open section under torsion twists and buckles.

**Cost.** ESTIMATED, gated on bulk wrought iron then steel.

**Danger.** Rivet failure under load, hot-metal burns.

**Confidence: HIGH** tension/ductility, **LOW** near-term timeline.

### cn_pratt_truss - Pratt truss, and the iron-age truss family

**What it is.** Once iron reliably holds tension, diagonals can be thin tension rod instead of thick timber struts, cutting truss weight dramatically.
Also covers: cn_warren_truss, cn_lattice_truss, cn_space_frame.

**Why never guess.** A timber king post puts diagonals in compression, joints handle it better. Iron trusses invert this: Pratt diagonals run in tension, verticals in compression, since a tension member never buckles the way compression does. Warren truss uses consistent 45-degree diagonals, most efficient if the geometry is precise. Lattice truss crosses many thin diagonals to save weight at full depth, at the cost of many joints, each an unannounced weak point. Space frame triangulates in three dimensions, very light, but every joint carries load from several directions at once, the joint is the whole design problem.

**Prerequisites.** cn_wrought_iron_girder or steel, cn_riveted_connection, cn_post_lintel.

**Roman inputs.** Ordinary bar stock once bulk iron exists; the principle needs no new material.

**Procedure.** Lay out geometry precisely, these forms depend on angle, not oversized members, for efficiency. Size diagonals for calculated or model-tested tension; size compression members against buckling, which happens well below crushing strength.

**How you know.** A loaded test truss deflects a small predictable amount and returns true.

**Failure modes.** One failed joint redistributes load onto neighbours, a chain failure; compression members buckling sideways, invisible until curved.

**Cost.** ESTIMATED, precise geometry costs fabrication time but saves weight.

**Danger.** Progressive chain-failure collapse.

**Confidence: HIGH**, well documented from the historical truss-bridge era.

### cn_riveted_connection - Riveted, bolted, gusseted, and welded joints

**What it is.** How iron and steel members are actually joined, since a joint is usually the weak point.
Also covers: cn_bolted_connection, cn_gusset_plate, cn_welded_connection.

**Why never guess.** A rivet is heated red hot, dropped through aligned holes, hammered flat both ends hot; cooling contraction, not the pin filling the hole, clamps the plates. A bolt relies on thread accuracy and torque, weaker per fastener but fast and removable. An arc weld can match parent steel cooled slowly, but cooled fast forms brittle martensite at the joint, quality is technique, not equipment. A gusset spreads force along a stiffer path, but too many rivets in it concentrates stress at the hole pattern instead.

**Prerequisites.** cn_wrought_iron_girder or steel, a forge; welding needs a reliable arc (`50_electricity.md`).

**Roman inputs.** Iron rod stock, forge, tongs, hammers.

**Procedure.** Heat a rivet bright orange-yellow, hammer flat against a backing bar before it cools past dull red. Cut threads accurately (`40_power_precision.md#screw_cutting_lathe`), torque by feel, expect loosening without a lock nut. Weld with a steady arc, cool slowly, never quench.

**How you know.** No gap under a cooled rivet head; a bolted joint survives a hard shake; a weld bead is smooth when tapped.

**Failure modes.** A cold-driven rivet never clamps; an over-torqued bolt snaps; a rushed weld cracks months later.

**Cost.** MEASURED riveting, minutes per rivet; DERIVED bolting, faster but needs precision threading.

**Danger.** Hot rivet burns; a snapped bolt releases force violently.

**Confidence: HIGH** riveting/bolting, **MEDIUM** welding.

### cn_reinforced_concrete - Reinforced concrete slab and beam

**What it is.** Concrete cast around steel bars so steel carries tension plain concrete cannot, giving flat slabs and beams plain concrete never could.
Also covers: cn_deformed_rebar, cn_precast_panel.

**Why never guess.** The second real kernel: reinforced concrete works only because steel and set concrete expand with temperature at nearly the same rate, roughly 10-14 millionths per degree C for both (MEASURED, unverifiable to a Roman without precision thermal measurement). Mismatched, every seasonal cycle would peel the bond apart. Nobody engineered this, a coincidence of iron oxide and silicate rock under heat. Second point: steel must sit exactly where tension is, the *bottom* of a simple beam, the *top* over a support where bending reverses. Wrong face and you've built an expensive plain concrete beam.

**Prerequisites.** cn_portland_cement or tested pozzolana (weaker), bulk iron or steel bar, cn_post_lintel.

**Roman inputs.** None for bar steel; wrought iron bar substitutes at reduced effect.

**Procedure.** Place bar exactly along the tension face before pouring; keep a few centimetres of cover, since pore water protects steel only while uncracked and encased. Vibrate around bars so no voids trap air. Deformed rebar (rolled ribs) bonds mechanically. Precast panels do this in a factory for consistency, at the cost of weak panel joints.

**How you know.** A reinforced test beam outlasts an identical unreinforced one; a cut section shows the bar still bonded.

**Failure modes.** Bar in the compression zone doing almost nothing; inadequate cover letting the bar rust, rust's greater volume spalls the concrete off from inside.

**Cost.** ESTIMATED, gated on cement and bulk steel both, a late combination.

**Danger.** Sudden failure with no warning cracking.

**Confidence: HIGH** the coincidence and placement, **LOW** Roman-era timeline.

### cn_prestressed_concrete - Prestressed concrete element

**What it is.** Stressing steel before the concrete takes load, so it starts in compression everywhere; service load must cancel that first before creating any tension.
Also covers: cn_post_tensioning.

**Why never guess.** Ordinary reinforced concrete still cracks near the bar under tension. Stress the tendon first, stretched before pour or jacked through cured concrete after, and the concrete is squeezed permanently before service load arrives, staying crack-free under loads that would split ordinary reinforced concrete.

**Prerequisites.** cn_reinforced_concrete, high-strength steel wire, a hydraulic jack.

**Roman inputs.** None, needs bulk high-strength wire and hydraulics beyond Roman reach.

**Procedure.** Post-tensioning: cast with hollow ducts placed for tendons, cure, thread cable, jack to specified tension, lock with a wedge anchor, grout the duct.

**How you know.** The jack gauge shows target load before lock-off; no cracking under a proof load that would crack an unstressed beam.

**Failure modes.** Jack failure under high pressure is violently dangerous; a mis-placed duct causes hidden internal damage.

**Cost.** ESTIMATED, gated on wire, jacks, and reinforced concrete all first.

**Danger.** A failed jack or snapped tendon releases stored energy violently.

**Confidence: MEDIUM-HIGH** physics, **LOW** reachability.

### cn_suspension_bridge - Suspension bridge system

**What it is.** A deck hung from cables in pure tension, spanning gaps no beam or arch reaches economically.
Also covers: cn_cable_anchorage, cn_wire_cable_spinning, cn_stiffening_truss.

**Why never guess.** The cable looks hard and is easy: many thin wires spun strand by strand are stronger and more uniform than any chain link, provided bundle rotation is controlled during spinning or it twists apart. The real problem, learned expensively and repeatedly, is aerodynamic stiffness of the deck. A light deck can twist under wind, feeding energy into its own oscillation instead of damping it, a resonance that grows until the deck tears apart, Tacoma Narrows the filmed example. A stiffening truss adds weight and torsional resistance so the deck can't twist freely. Towers resist the horizontal component of enormous cable tension, dwarfing the deck they seem to hold up.

**Prerequisites.** Bulk steel wire (`10_metallurgy.md#wire_drawing`), cn_post_lintel and cn_pratt_truss tension logic, a massive anchorage.

**Roman inputs.** None, a late high-tonnage technology.

**Procedure.** Erect towers first. Spin the main cable strand by strand, controlling rotation. Anchor each end into a block large enough the stress cone stays inside its mass, undersized and the wedge pulls free violently. Hang the deck from vertical hangers, stiffen it full-length against twist.

**How you know.** Minimal deck twist under crosswind, tested with streamers first.

**Failure modes.** Aerodynamic flutter, capable of destroying a sound bridge in minutes; anchorage pull-out; uncontrolled spinning rotation losing cable strength invisibly.

**Cost.** ESTIMATED, one of the largest, latest projects here, gated on bulk steel wire.

**Danger.** Catastrophic sudden collapse with almost no warning to people on the deck.

**Confidence: HIGH** mechanisms, **LOW** reachability.

### cn_arch_bridge_steel - Steel arch bridge

**What it is.** The masonry arch's compression path rebuilt in steel, reaching much further than stone voussoirs.

**Why never guess.** A masonry arch is fixed and heavy of necessity, stone only pushes, and any temperature change or settlement in a rigid arch builds hidden internal stress with nowhere to go. A steel arch hinged at its base (sometimes the crown too) can rotate slightly, absorbing thermal change as a small rotation instead of hidden stress a rigid arch won't show until it cracks.

**Prerequisites.** cn_wrought_iron_girder or steel, cn_true_arch, a hinge carrying full thrust while rotating freely.

**Roman inputs.** None, steel-tonnage technology.

**Procedure.** Design the arch curve to match its expected thrust line. Place hinges at the base and, for long spans, the crown, using a pin bearing that rotates without seizing from rust or debris.

**How you know.** The hinge rotates a small expected amount across a seasonal swing with no new cracks.

**Failure modes.** A seized hinge silently becomes rigid again, reintroducing the stress it avoided; a mismatched thrust curve concentrates stress at one point.

**Cost.** ESTIMATED, gated on bulk steel and precision hinges.

**Danger.** Sudden compression buckling if the thrust line drifts outside the material.

**Confidence: MEDIUM-HIGH** hinge logic, **LOW** reachability.

### cn_bascule_bridge - Bascule, swing, and pontoon bridges

**What it is.** Three ways to open a bridge for river traffic: a counterweighted tilting leaf, a whole span pivoting centrally, and a floating anchored roadway.
Also covers: cn_swing_bridge, cn_pontoon_bridge.

**Why never guess.** A bascule's counterweight balance point shifts through its arc, the mechanism must suit the whole range of motion or it jams. A swing bridge's central pivot carries the whole deck on one bearing, enormous friction, any binding on the guide rail jams it. Pontoon is simplest and already within Roman reach (Caesar's Rhine crossings); it rises and falls with the water, ramps must accommodate that, and it's normally removable for winter ice.

**Prerequisites.** Bascule/swing: bulk iron or steel, precise bearings. Pontoon: Roman carpentry and boat-building only.

**Roman inputs.** Pontoon: timber, boats, rope, all Roman. Bascule/swing: gated on iron/steel tonnage.

**Procedure.** Bascule: size the counterweight against the leaf at several arc points. Swing: centre and lubricate the pivot. Pontoon: anchor floats against current, ramps with vertical play, plan seasonal removal.

**How you know.** Full range operation without stalling; pontoon rises freely without straining lines.

**Failure modes.** Miscalculated mid-arc load stalling a bascule; a binding pivot; pontoon anchor failure in flood.

**Cost.** MEASURED pontoon, already reachable; ESTIMATED and gated for bascule/swing.

**Danger.** A jammed moving bridge is a hazard to river and road traffic at once.

**Confidence: HIGH** pontoon, **MEDIUM** bascule and swing.

### cn_gravity_dam - Gravity dam, arch dam, earth dam, spillway, retaining wall

**What it is.** Holding back water or soil with mass, curvature, or both, calculating whether it slides, overturns, or is lifted off its foundation.
Also covers: cn_arch_dam, cn_earth_dam, cn_spillway, cn_retaining_wall.

**Why never guess.** A gravity dam holds by being too heavy to slide or tip, so the foundation is the real limit, only rock bears the load, and seepage under the base creates uplift that can lift the dam like a boat if undrained. An arch dam curves load sideways into abutments as a masonry arch transfers load into supports, needing far less mass, but a bad abutment fails catastrophically. An earth dam's clay core must be more impermeable than the surrounding fill or seepage concentrates into an internal channel, piping, silent until sudden and total. A spillway controls overtopping; one miscalculated crest elevation dooms the structure.

**Prerequisites.** cn_true_arch for arch-dam curvature, cn_pozzolana_concrete or cn_portland_cement, rock surveying.

**Roman inputs.** Cut stone, concrete, clay, all Roman; missing is the sliding/overturning/uplift calculation, done by overbuilding.

**Procedure.** Site on sound rock. Gravity dam: mass comfortably exceeding the water's push, drain the foundation against uplift. Arch dam: confirm abutment rock first. Earth dam: core less permeable than shoulders, monitor seepage. Spillway: size for the worst flood plus margin.

**How you know.** No base movement after a full pool cycle; seepage runs clear.

**Failure modes.** Uplift lifting the base; sudden abutment failure; invisible piping until a sinkhole appears; an undersized spillway eroding the dam body.

**Cost.** ESTIMATED, steep with height; larger dams need calculation this tree lacks.

**Danger.** Downstream failure is mass-casualty scale, among the worst modes here.

**Confidence: HIGH** mechanisms, **MEDIUM** Roman-era sizing without calculation.

### cn_pile_driving - Pile driving, screw piles, soil compaction

**What it is.** Raising a foundation's bearing capacity in soft ground, driving a pile or densifying the soil itself.
Also covers: cn_screw_pile, cn_soil_compaction.

**Why never guess.** A drop-hammer pile compresses the soil around it as it goes, so driving gets harder with depth, and a foreman tracking diminishing penetration per blow is measuring bearing capacity in real time without any instrument. A screw pile, a shaft with a helical blade, is twisted rather than hammered, but wrong pitch means it spins in place without advancing. Soil compaction by rolling works the same logic, but only within an optimal moisture range, too dry or too wet both resist it.

**Prerequisites.** cn_crane_treadwheel or a gin-pole hoist, iron for the helix.

**Roman inputs.** Timber piles, iron shoes, iron helix once forged, stone or timber rollers.

**Procedure.** Drop-hammer: track penetration per blow, stop once it falls below a set small amount. Screw pile: match helix pitch to soil by trial. Compaction: test moisture by feel, roll repeatedly, tracking diminishing benefit per pass.

**How you know.** Penetration per blow has dropped to a small stable figure; compacted soil resists a firmly pressed boot heel.

**Failure modes.** A pile in a soft pocket never reaching bearing, invisible until settlement; a screw pile spinning without advancing.

**Cost.** MEASURED order of magnitude, days per pile.

**Danger.** Dropped hammer weight crushes workers.

**Confidence: HIGH**, easily observed in practice.

### cn_cofferdam - Cofferdam, dewatering, diaphragm wall, sheet piling

**What it is.** Four ways to keep water out of a hole you need to dig, from a temporary dike to a permanent slurry-formed wall.
Also covers: cn_dewatering, cn_diaphragm_wall, cn_sheet_piling.

**Why never guess.** A cofferdam's leakage rises as outside pressure builds, so pump capacity must grow through the job, one pump with no backup is a single point of failure. Dewatering also lets nearby ground settle as the water supporting it is removed, cracking a neighbour's foundation while protecting its own site. Sheet piling's interlock needs tightness or water seeps between sheets, and each new sheet is pushed against the friction of every sheet already driven, so the last are hardest. A diaphragm wall excavates a trench filled with clay slurry holding the walls open without shoring; concrete poured through a submerged tremie pipe displaces the lighter slurry upward, a use of clay Rome does not currently make.

**Prerequisites.** Timber, iron, continuous pumping (`40_power_precision.md#hydraulics_pumps`), bentonite-equivalent slurry knowledge.

**Roman inputs.** Timber, clay, forged iron sheet; the pump is the real gate.

**Procedure.** Cofferdam: oversize the dike, run two pumps. Dewatering: monitor nearby structures throughout. Sheet piling: check interlock tightness sheet by sheet. Diaphragm wall: keep slurry level high whenever paused, pour through a submerged tremie.

**How you know.** A cofferdam stays dry with steady pump output; a diaphragm trench holds shape overnight.

**Failure modes.** Single-pump flooding; dewatering settlement cracking neighbours; leaking interlocks; a slumped trench from a dropped slurry level.

**Cost.** ESTIMATED, cofferdam and sheet piling reachable with Roman materials and pumping; diaphragm wall has no Roman precedent.

**Danger.** Sudden flooding is drowning/crush hazard; settlement is a legal and social hazard.

**Confidence: MEDIUM-HIGH** cofferdam and sheet piling, **MEDIUM** diaphragm wall.

### cn_caisson - Caisson, pneumatic caisson, underpinning

**What it is.** Building a foundation below water or below an existing structure, in a sealed or pressurised chamber, or by replacing an old foundation piece by piece.
Also covers: cn_pneumatic_caisson, cn_underpinning.

**Why never guess.** A simple caisson sinks under its own weight as material is dug from inside, sealed at every joint or it floods. A pneumatic caisson pressurises the chamber to match water pressure, letting men dig directly, but introduces caisson disease (the bends): workers ascending too fast get nitrogen bubbling out of the blood, no warning at exposure, an agonising delayed onset, so slow staged decompression must follow even when nothing seems wrong. A sand boil, sudden inrush when pressure drops briefly, can undermine a wall in moments. Underpinning replaces a foundation under a building that must not move, so work proceeds one small shored section at a time.

**Prerequisites.** cn_cofferdam's sealing logic, compressed air supply beyond Roman force pumps.

**Roman inputs.** Timber, iron seals; pneumatic capability is not Roman-reachable without development.

**Procedure.** Simple caisson: seal every joint, test under load first. Pneumatic: raise pressure gradually, decompress on a slow staged schedule regardless of how workers feel. Underpinning: replace one small section at a time, monitor a fixed reference mark.

**How you know.** A caisson sinks evenly with no leaks; a crew shows no delayed pain after decompression.

**Failure modes.** Sudden flooding from a seal failure; rushed decompression causing the bends hours later; a sand boil undermining a wall.

**Cost.** ESTIMATED, slow specialised work, small crews on short shifts at depth.

**Danger.** The bends is a genuinely novel danger, symptom appearing only after the danger seems past.

**Confidence: HIGH** the bends' mechanism, **LOW** Roman-era pneumatic capability.

### cn_drill_blast - Tunnelling by drill and blast

**What it is.** Breaking rock by planned explosive charges in drilled holes, the only way to advance through hard rock at useful speed.
Also covers: cn_tunnel_cut_cover, cn_ventilation_shaft.

**Why never guess.** More explosive is not faster progress. Charges fired in the wrong sequence, rather than a planned pattern (centre cut first for a free face, rings fired outward), leave large boulders, costing as much hand-breaking time as the blast saved. Cut-and-cover suits only shallow tunnels, the roof carries everything piled back plus traffic; past a point the shield method is better. A ventilation shaft works by natural stack effect unless obstructed, in which case fumes pool at the face.

**Prerequisites.** Explosive is a genuine anachronism trap, Rome has none; rock drilling, cn_quarrying_wedge's grain-reading.

**Roman inputs.** None for explosive; drilling, timber shoring, iron bits, all Roman.

**Procedure.** Drill a planned pattern, fire centre holes first, then rings outward in sequence, clear fumes before re-entering. Size a cut-and-cover roof for the worst load before backfilling. Site shafts with the tunnel's natural draft.

**How you know.** Well-fragmented rock, no boulder too large to move by hand.

**Failure modes.** Wrong sequence leaving boulders; overcharged holes damaging walls; an undersized roof crushed by backfill; a blocked shaft pooling fumes, a suffocation risk with no warning smell for some gases.

**Cost.** ESTIMATED, gated on explosive availability; without it, hand-break progress is a few metres per week per crew (ESTIMATED, basis: pre-explosive historical rates).

**Danger.** Misfire, fume poisoning; explosives carry real social danger, a magistrate treats unauthorised production as a threat.

**Confidence: MEDIUM** blast mechanics, **LOW** Roman-era explosive availability.

### cn_tunnel_shield - Tunnel shield method, and tunnel lining

**What it is.** A protective shell pushed by jacks through soft ground, letting men excavate safely while lining rings go in immediately behind.
Also covers: cn_tunnel_lining.

**Why never guess.** In hard rock the rock briefly holds its own shape. In soft ground the face can collapse instantly, no grace period, which the shield solves, holding the face open, pushed forward by jacks bearing against lining already installed behind, so the tunnel builds its own advancing anchor. In waterlogged ground the face may need pressurising (cn_caisson's logic) or it flows into the shield faster than it can be removed. Lining rings are cast and cured before installation, so installation is fast, but every joint must be tight, water finding a joint slowly rots the lining from inside over years.

**Prerequisites.** cn_wrought_iron_girder or steel, cn_concrete_mixer-scale production, cn_caisson's sealing logic.

**Roman inputs.** None, a late steel-and-concrete combination with no Roman precedent.

**Procedure.** Push the shield forward in short jacked increments. Install a lining ring immediately behind. Grout the gap behind the lining promptly, an ungrouted void lets the ground above settle unevenly.

**How you know.** Steady advance with no sudden surface settlement; no seepage at joints.

**Failure modes.** Face collapse without pressure support; an ungrouted void causing delayed settlement; leaking joints rotting the lining.

**Cost.** ESTIMATED, a late-tree, capital- and steel-intensive technique.

**Danger.** Face collapse is an acute burial hazard.

**Confidence: MEDIUM** mechanics, **LOW** near-term reachability.

### cn_crane_derrick - Derrick and tower cranes, elevator safety brake

**What it is.** Lifting machinery beyond the treadwheel's scale, once continuous power and steel exist for taller masts.
Also covers: cn_crane_tower, cn_elevator_safety_brake.

**Why never guess.** A derrick's mast is strong in straight-up compression, weak against side load, exactly what unevenly tensioned guy lines introduce. A tower crane's jib is cantilevered, the base must resist the overturning moment, worse the further the jib reaches, and wind adds to it, so bracing adequate in calm weather can fail in a storm never tested against. An elevator's safety brake is the clearest lesson: its jaws are held open by tension in the cable that might break, so the drop in tension itself triggers the brake, the failure arms its own safety device, but only if the wedge angle is exactly right.

**Prerequisites.** cn_wrought_iron_girder or steel, cn_riveted_connection, continuous power (`40_power_precision.md#gearing_and_transmission`, `steam_high_pressure`).

**Roman inputs.** Timber builds a modest derrick within Roman means; tower crane and elevator brake are gated beyond baseline.

**Procedure.** Derrick: tension guy lines equally, recheck after load changes. Tower crane: size the base counterweight against maximum load at maximum reach plus wind. Elevator brake: set wedge angle by testing against a deliberately cut cable first.

**How you know.** A derrick stays plumb under full load in stiff wind; a test-cut cable stops the cage within a short distance.

**Failure modes.** Unequal guy tension toppling a mast; wind-driven overturning; a wrong wedge angle that slips instead of grips, the most consequential failure here.

**Cost.** ESTIMATED, derricks reachable at modest scale, tower cranes and elevator brakes late-tree.

**Danger.** A toppling mast crushes anyone nearby; a failed brake is a fall hazard.

**Confidence: HIGH** mechanical logic, **LOW** reachability for tower crane and brake.

### cn_concrete_mixer - Concrete mixing and placing at scale

**What it is.** Machinery and technique letting concrete be placed fast and evenly at real building scale.
Also covers: cn_formwork_shuttering, cn_slipform, cn_shotcrete, cn_vibratory_compaction, cn_expansion_joint.

**Why never guess.** A rotary mixer has a narrow optimum speed: too slow and aggregate settles, too fast and centrifugal force pins it to the wall, which looks like mixing but isn't. Formwork must not deflect under wet concrete's weight, since any deflection while wet is cast permanently into the surface, unfixable after. Slipform creeps continuously upward, tuned exactly against setting speed, too fast breaks unsupported concrete, too slow cracks set concrete against the form's friction. Vibration's window is only five to ten seconds per area (ESTIMATED, standard practice), too little leaves voids, too much un-mixes it. Expansion joints exist because concrete moves roughly 10-15 mm per 100 m across a 50-degree swing (ESTIMATED, standard thermal coefficients); without one it cracks itself uncontrolled.

**Prerequisites.** cn_pozzolana_concrete or cn_portland_cement, mechanical power for mixer and vibrator.

**Roman inputs.** Timber formwork, already Roman; mechanised versions gated on continuous power.

**Procedure.** Run the mixer at tested optimum speed. Build formwork stiff enough to show no deflection under test load. Match slipform creep rate to tested setting time. Vibrate in short bursts, stop once the surface goes smooth. Place expansion joints regularly with compressible filler.

**How you know.** Uniform mixed batch; a struck formwork surface is flat and true; vibrated concrete rings solid.

**Failure modes.** Segregated concrete; formwork deflection cast permanently in; over- or under-vibrated concrete; missing joints cracking the slab uncontrolled.

**Cost.** DERIVED, formwork and hand mixing within Roman means; mechanised versions need continuous power.

**Danger.** Formwork collapse under wet concrete can bury workers.

**Confidence: HIGH** mechanics, **MEDIUM** reachability without site power.

### cn_curtain_wall - Curtain wall, plate glass, sash window, asphalt roofing, corrugated roof

**What it is.** How a building's outer skin works once a frame, not the wall, carries structural load, freeing the wall to be thin and glazed.
Also covers: cn_plate_glass_window, cn_sash_window, cn_asphalt_roofing, cn_roof_truss_corrugated.

**Why never guess.** A curtain panel hangs from its top only, wind load travels through fasteners into the frame with no redundancy, one failed seal is one failed panel. Only works once cn_steel_frame_skeleton carries real load; without a frame the wall must be load-bearing, all Rome has ever needed. Plate glass needs slow controlled annealing after casting, or internal stress from fast cooling cracks a pane months later. A sash counterweight must exactly balance the pane or it won't stay open; cord wear is invisible until it snaps. Asphalt is temperature-sensitive, too cold cracks, too hot flows away. Corrugated iron is stiff from its corrugations, but fastening through the ridges concentrates stress at each hole.

**Prerequisites.** cn_steel_frame_skeleton, Roman glassblowing (`30_glass_optics.md`) scaled up, bitumen, rolled sheet.

**Roman inputs.** Glassblowing already makes clear panes; bitumen already traded.

**Procedure.** Anneal glass slowly with a controlled gradient. Balance sash counterweights precisely. Install asphalt within its temperature range, lap downslope. Fasten corrugated roofing through ridges, allow play for thermal movement.

**How you know.** No water ingress after a storm; an annealed pane shows no spontaneous cracking; a sash holds at any height.

**Failure modes.** A failed curtain seal with no redundancy; unannealed glass cracking with no warning; a snapped cord.

**Cost.** ESTIMATED, curtain wall late-tree, the rest reachable earlier.

**Danger.** A falling curtain panel is a hazard below.

**Confidence: MEDIUM-HIGH** components, **LOW** curtain wall as a system.

### cn_cavity_wall - Cavity wall, damp proof course, insulation

**What it is.** Keeping moisture and heat where they belong using an air gap, a moisture barrier, and trapped air, none of which a solid Roman wall does deliberately.
Also covers: cn_damp_proof_course, cn_insulation.

**Why never guess.** A cavity wall's ties, without which it's two unstable skins, become thermal bridges carrying heat straight across the gap meant to break it, and the cavity must stay clear of mortar droppings or moisture bridges across the debris. A damp proof course breaks capillary rise, masonry wicks groundwater up several metres with no pump needed. Insulation works by trapping still air, not the material itself, so compressing it destroys it; a vapour barrier is needed in cold climates or condensation saturates it from within.

**Prerequisites.** Ordinary masonry, iron for ties, an impermeable sheet for the damp course, low-density fibrous fill.

**Roman inputs.** Fired brick and mortar, bitumen as a plausible damp course, wool or chaff as plausible insulation, not currently used this way.

**Procedure.** Build two leaves with a clear gap, ties that shed water rather than carry it across, keep the cavity clear of debris. Lay a continuous damp course, one gap defeats the whole course. Pack insulation loosely, never compressed.

**How you know.** No damp staining above a proper damp course after a wet season; an insulated wall feels less cold.

**Failure modes.** Mortar droppings bridging the gap; a damp course with even one gap; compressed or wet insulation, silently useless.

**Cost.** DERIVED, modest additional material and care.

**Danger.** No acute danger, only long-term unseen rot.

**Confidence: HIGH**, physics well established, reachable with Roman materials.

### cn_central_heating - Central heating, radiators, forced ventilation

**What it is.** Distributing heat via circulating hot water and moving air mechanically, beyond a Roman hypocaust.
Also covers: cn_radiator, cn_forced_ventilation.

**Why never guess.** A hot water system must stay filled and air-free, an air pocket stops circulation exactly like an air lock stops a siphon (cn_aqueduct); an expansion tank is needed because water expands as it heats, without one a sealed system builds dangerous pressure. Radiators lose heat transfer to mineral scale with no outward sign until the room is simply colder. Forced ventilation's fan noise rises sharply with speed, so an undersized duct forces the fan to run faster than comfortable.

**Prerequisites.** Iron for radiators and piping, mechanical power for the fan, the existing hypocaust as a starting point.

**Roman inputs.** The hypocaust, already routine in baths and villas; iron pipe and radiators are the missing pieces.

**Procedure.** Fill the system completely, bleed air from every high point. Size an expansion tank generously. Keep radiator water scale-free, flush periodically. Size ducts so the fan need not run at maximum for ordinary operation.

**How you know.** Radiators run hot evenly along their length; ventilation moves audibly but not uncomfortably.

**Failure modes.** Trapped air stopping circulation; a missing expansion tank building dangerous pressure; scaled radiators losing capacity invisibly.

**Cost.** ESTIMATED, gated on real iron tonnage.

**Danger.** An over-pressured system can rupture violently.

**Confidence: MEDIUM-HIGH** mechanics, **LOW** near-term reachability.

### cn_plumbing_stack - Plumbing stack and trapped drains

**What it is.** A vertical waste pipe with water-sealed traps at every fixture, avoiding the smell and disease vector of an open drain.
Also covers: cn_trapped_drain.

**Why never guess.** A soil stack sized too narrow siphons itself, waste dragging the air behind it, and that suction can pull the water seal out of every trap on that stack at once, even sound ones. A trap's seal is only a few centimetres of standing water, broken by siphoning or by evaporation from a fixture unused long enough, which is why an occasional bathroom can smell of sewage with no fault, the trap simply dried out.

**Prerequisites.** Ceramic or lead pipe (prefer ceramic), correct fall surveyed with the chorobates.

**Roman inputs.** Ceramic pipe, lead pipe (avoid for acidic waste), mortar joints.

**Procedure.** Size the main stack generously so falling waste doesn't drag trap seals with it. Fit every fixture with its own trapped bend. Slope every run consistently.

**How you know.** No sewer smell at any fixture after normal use.

**Failure modes.** An undersized stack siphoning many traps at once; an unused trap drying out; one untrapped fixture undermining every trap elsewhere.

**Cost.** MEASURED order of magnitude, well within Roman pipe-laying, the gap is technique.

**Danger.** Sewer gas exposure is hazardous in confined poorly ventilated spaces.

**Confidence: HIGH**, straightforward hydraulics within Roman capability.

### cn_fire_escape - Fire escape and automatic sprinklers

**What it is.** Getting people safely out of a burning multi-storey building, and suppressing fire automatically.
Also covers: cn_sprinkler.

**Why never guess.** A fire escape is only as good as its worst point: stairs that can be locked defeat the whole purpose at the one moment it matters, and a pivoting ladder can itself jam at the hinge, a real historical cause of fire escape deaths unrelated to the fire. A sprinkler's thermal element, historically a soldered joint, must melt reliably at a set temperature, but that solder plug can be damaged in installation and fail to melt, or trigger falsely; the system is only as good as its pressure reaching the most distant nozzle.

**Prerequisites.** Iron for stairs and piping, a reliable fusible alloy, `85_transport_civil.md#water_supply_sanitation`-level pressurised supply.

**Roman inputs.** Iron reachable once bulk supply exists; tin-lead-bismuth alloys known in principle but untested for this melting point.

**Procedure.** Keep escape stairs permanently unobstructed, test pivoting sections regularly. Sample-test thermal elements to destruction, verify pressure reaches the most distant nozzle.

**How you know.** Escape sections deploy freely under a supervised test.

**Failure modes.** A locked or obstructed escape; a seized hinge trapping people mid-escape; a damaged solder plug that never melts.

**Cost.** ESTIMATED, moderate for iron stairs once bulk iron exists.

**Danger.** The equipment's own failure modes are a second layer since people trust it and stop looking for another way out.

**Confidence: MEDIUM-HIGH** mechanics, **LOW** near-term reachability.

### cn_terrazzo - Terrazzo floor finish

**What it is.** A floor of stone chips set in binder, ground flat and glossy, a marble-like finish at a fraction of solid marble's cost and weight.

**Why never guess.** The binder's set state matters more than the recipe: aggregate size and binder porosity must match so the surface grinds to a stone-wide sheen without pulling chips loose; an under-fired binder yields to the abrasive before the chips do, an over-fired binder tears the chips out instead of grinding evenly with them.

**Prerequisites.** cn_mortar or cn_gypsum_plaster, cn_stone_polish's grinding skill, marble chip waste.

**Roman inputs.** Marble chip waste, lime or gypsum binder, emery for grinding, all already Roman, nearly reachable already, only the deliberate combination is new.

**Procedure.** Set chips into a binder bed, cure to a firmness matched by test to the chip hardness, grind flat with progressively finer abrasive until a continuous polish emerges.

**How you know.** A smooth continuous polish across chips and binder, no chips proud of the surface.

**Failure modes.** Binder too soft, uneven gouging; binder too hard, chips tear free leaving pits.

**Cost.** ESTIMATED, modest, uses waste Rome already discards.

**Danger.** Grinding dust over long exposure is a lung hazard.

**Confidence: MEDIUM-HIGH**, materials and skills already Roman.

---

## Sources and confidence

Roman baseline claims (arch, vault, pozzolana concrete, aqueduct, crane, surveying) are HIGH confidence, from Vitruvius's *De Architectura*, Frontinus's *De Aquaeductu*, and surviving structures; see `85_transport_civil.md` for the fuller citation trail this module deliberately doesn't repeat. Beam theory, truss mechanics, cast/wrought iron tension behaviour, reinforced and prestressed concrete's thermal-expansion coincidence, and suspension bridge aerodynamics are HIGH confidence, textbook materials science backed by well documented historical collapses. Portland cement chemistry and clinkering temperature are HIGH confidence, MEASURED figures from modern manufacture. Caisson disease's mechanism is HIGH confidence, well established medically. Anything marked LOW confidence here is LOW specifically on Roman-era reachability, not the underlying physics, which is not in doubt; the gating items are almost always bulk iron and steel tonnage (`10_metallurgy.md`) and continuous mechanical power (`40_power_precision.md`), not missing scientific insight. No number here is invented; every figure is tagged MEASURED, DERIVED, or ESTIMATED with its basis stated.

## Where to go next

- `85_transport_civil.md` for what Rome's civil engineering already does well, the freight arithmetic deciding where to build first, and the `structures_iron_steel`, `concrete_and_cement`, `surveying_precision`, and `water_supply_sanitation` entries this module builds on.
- `10_metallurgy.md` for the blast furnace, finery forge, and cementation/crucible steel chain gating nearly every iron and steel item here, from cast iron beams to suspension bridge cable.
- `40_power_precision.md` for the continuous mechanical power gating rotary cement kilns, concrete mixers, powered cranes, and mechanical ventilation.
