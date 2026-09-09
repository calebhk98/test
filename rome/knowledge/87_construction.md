# Module 87: Construction Engineering

Say the honest thing first, or a builder who raised the Pantheon's dome will stop listening. Rome already has hydraulic concrete that cures underwater and strengthens for decades. Rome already has the true arch and the groin vault, spanning valleys and bath halls nothing will match for a thousand years. Rome already has the groma, the chorobates, and a corps of military engineers as competent as any modern army's. If your plan is "teach Romans to build," burn it.

What Rome lacks is four things, and all 101 items below serve one of them. First: a cement that behaves the same on the hundredth batch as the first, not one riding on which shore the ash came from and the mason's eye that morning. Second: iron, then steel, doing real work in tension, since Rome has wrought iron for cramps but no cast iron in the West, no crucible steel of its own, and nowhere near a load-bearing frame's tonnage. Third: the theory of the beam, the mathematics of *why* a proportion works, not just that it worked last time, so a span can change without rebuilding a failure to find the new limit. Fourth: machinery of scale, cranes, mixers, pumps, needing continuous mechanical power Rome has only in trickle amounts (`40_power_precision.md`). Fix those roughly in order and the rest is carpentry.

---

### cn_pozzolana_concrete - Pozzolana hydraulic concrete (*opus caementicium*)

**What it is.** Quicklime plus volcanic ash, sets underwater, gains strength for decades. Already Roman; this entry exists to give the tech tree a node.
Also covers: cn_mortar.

**Why you'd never guess this.** Nothing here for a Roman. For a modern visitor: this is not lesser Portland cement, it is chemically different and, for marine work, arguably better. Full account: `85_transport_civil.md#concrete_and_cement`.

**Prerequisites.** Lime burning, pozzolana access, formwork carpentry.

**Roman-available inputs.** *Calx* (quicklime), *pulvis puteolanus* (pozzolana, Bay of Naples), *caementa* (rubble), fresh water. Plain lime mortar is the everyday binder without pozzolana.

**Procedure.** Slake lime, mix with pozzolana and rubble near Vitruvius's ratios (II.6, verify by testing your own ash), pack in formwork, cure weeks to years. Real addition: cast a labelled test cylinder per batch, crush matched cylinders at intervals with known weights, log it. No Roman source does this systematically.

**How you know it worked.** A month-old cylinder resists the load your log predicts; an opened underwater section rings hard, not crumbly.

**Failure modes.** Weak ash never fully hardens. Batch variation is invisible without testing.

**Cost & labour.** DERIVED: one attentive foreman and a wax tablet.

**Danger.** Slaking lime burns skin and eyes, wash immediately. No social danger.

**Confidence: HIGH.**

### cn_quarrying_wedge - Stone quarrying with wedges

**What it is.** Splitting stone along a chosen plane instead of random fracture, already routine in every legionary quarry.
Also covers: cn_stone_saw, cn_stone_polish, cn_gang_saw.

**Why you'd never guess this.** Nothing here for a Roman either.

**Prerequisites.** Iron wedges, a reader of the stone's grain.

**Roman-available inputs.** Iron *cunei*, emery (Naxos) for polish, sand and water for sawing, the abrasive cuts, the blade only guides.

**Procedure.** Mark holes along the bedding plane, drive wedges in sequence, not at once, listen for the pitch change that says the crack runs true. Sawing: drag iron blade with wet sand beneath. Polishing: work down through finer emery by hand. Gang saw is the genuine addition, several parallel blades cutting one block into slabs at once; the hard part is equal blade tension, one that binds ruins the block.

**How you know it worked.** The split face follows your marked line.

**Failure modes.** Out-of-sequence wedges split wrong; unequal gang-saw tension warps the cut.

**Cost & labour.** MEASURED: a building block splits in under a day; an obelisk blank is a season, per Aswan.

**Danger.** Flying chips, crushed fingers, collapsing faces. No social danger.

**Confidence: HIGH.**

### cn_true_arch - True arch in stone (*fornix*)

**What it is.** Compression-only load path around an opening. Already extensive Roman practice.
Also covers: cn_groin_vault, cn_ribbed_vault, cn_flying_buttress.

**Why you'd never guess this.** What's missing is not the arch, it's calculating safe thickness instead of copying a proportion (Colosseum ratios) into a bigger arch where it quietly fails. The thrust line, the true compression path, must stay inside the stone everywhere; nobody in 100 AD can compute that curve, so they build thick and watch what stands.

**Prerequisites.** `cap_tol_1mm`, cn_quarrying_wedge, centring carpentry.

**Roman-available inputs.** Cut voussoirs, or concrete cast over struck centring, brick ribs (as at the Pantheon).

**Procedure.** (1) Groin vault: two barrel vaults crossing at right angles, concentrating load onto four corner points, already Roman, extend deliberately to free wall space. (2) Ribbed vault: build diagonal ribs first as a light skeleton, then thin webs between, lighter, and the load path is visible by eye; use the ribs as formwork for the web. (3) Flying buttress: an arch leaping from a high wall to a free pier, carrying vault thrust away so the wall stays thin and glazed, useful only where thin tall walls are wanted, which Roman basilicas mostly don't.

**How you know it worked.** No sag against a straightedge a year after striking centring.

**Failure modes.** Thrust escaping at the haunches, a hinge-like crack; webs poured before ribs set, collapsing the skeleton; undersized buttress abutment, which just pushes the pier over.

**Cost & labour.** ESTIMATED, scales roughly with span cubed; a modest bay is weeks, cathedral-scale is a generation.

**Danger.** Falling centring and partial vault collapse, the deadliest trade in this module.

**Confidence: HIGH** on baseline, **MEDIUM** on rib/buttress transfer without calculus, historically built this way by trial and injury.

### cn_crane_treadwheel - Treadwheel crane (*polyspastos*)

**What it is.** Man-powered drum crane, already Roman, raising tonnes with a handful of men walking a wheel.
Also covers: cn_block_tackle_hoist.

**Why you'd never guess this.** Vitruvius describes it (*De Architectura* X). Worth stating: advantage equals rope parts under load, minus 10-20% to sheave friction (ESTIMATED, typical wooden-sheave loss).

**Prerequisites.** Hemp rope, timber, bronze sheave bearings.

**Roman-available inputs.** Hemp rope, seasoned timber, bronze pulleys.

**Procedure.** Rig rope through multiple blocks; each part shares the load. A treadwheel turns men's body weight, not arm strength, into pull, which is why few men lift tonnes.

**How you know it worked.** Load rises smoothly; creep or slip means a worn or wet groove.

**Failure modes.** Slip on worn sheaves; overloading one rope part snaps it without warning.

**Cost & labour.** MEASURED, attested at multi-tonne column and obelisk lifts.

**Danger.** Snapped rope, or an operator caught by an overrunning wheel. Socially unremarkable.

**Confidence: HIGH.**

### cn_scaffolding - Timber scaffolding system

**What it is.** Temporary timber platform for working at height, already routine.

**Why you'd never guess this.** Obvious once you want it. Non-obvious point: lashing discipline, not lumber, holds it together, one untied joint can unravel a bay.

**Prerequisites.** Timber poles, rope or withies.

**Roman-available inputs.** Fir or pine poles, hemp rope, green withy.

**Procedure.** Erect standards, tie ledgers at working height, brace diagonally, double every lashing that carries a joint. Inspect for creep daily.

**How you know it worked.** No visible sag under a loaded plank; a shove doesn't rack the frame.

**Failure modes.** One failed lashing propagates as load redistributes onto ties not sized for it.

**Cost & labour.** MEASURED, a normal minor cost line.

**Danger.** Falls are the trade's main hazard.

**Confidence: HIGH.**

### cn_aqueduct - Masonry aqueduct arch bridge (*aqua ducta*)

**What it is.** Level water channel carried across a valley on an arcade, already Roman at huge scale, nine lines feeding Rome per Frontinus.
Also covers: cn_siphon, cn_sewer_system, cn_water_main.

**Why you'd never guess this.** Not non-obvious to Rome. Worth stating: pressure in an open channel is static per section, so one arch's failure among dozens is local, unlike a single point of failure in a pressurised pipe.

**Prerequisites.** cn_true_arch, chorobates levelling (`85_transport_civil.md#surveying_precision`), lead or ceramic pipe.

**Roman-available inputs.** Cut stone/concrete arcading, lead pipe (*fistulae plumbeae*) or safer ceramic (*fistulae fictiles*, Vitruvius's own preference), ceramic sewer pipe.

**Procedure.** Level a gentle continuous fall, arcade across deep valleys, drop into an inverted siphon (sealed pipe down and back up, driven by head of water) where an arcade would be absurd, drain waste through sloped sewer pipe (Cloaca Maxima the proof of scale). A siphon must stay full and sealed, one trapped air pocket stops flow; sediment collects at the low point and needs periodic flushing.

**How you know it worked.** Continuous matched flow at delivery, no hammering in the siphon.

**Failure modes.** One arch failure drops the channel locally; an air lock halts a siphon line; unflushed sediment chokes a main.

**Cost & labour.** MEASURED, Rome's own system is the evidence.

**Danger.** Collapsing arcading during construction; lead is a slow chronic risk, don't boil acidic liquids in it.

**Confidence: HIGH.**

### cn_portland_cement - Portland cement powder

**What it is.** A binder fired hot enough to clinker, not merely calcine, giving strength and consistency pozzolana cannot match batch to batch.
Also covers: cn_rotary_cement_kiln, cn_cement_clinker_grinding, cn_gypsum_plaster, cn_artificial_stone.

**Why you'd never guess this.** "Cement" tricks a visitor into thinking Rome already has this. Lime burning calcines around 900-1000 C; Portland clinker needs roughly 1450 C, hot enough the raw meal partly melts and recombines into calcium silicates pozzolana never forms. Different kiln, different fuel budget, not a stronger old one. Grinding the clinker after matters almost as much as firing it: unground clinker is nearly inert.

**Prerequisites.** `cap_heat_1600` (roughly `10_metallurgy.md#high_temp_furnace`), limestone and clay quarrying, a mechanical mill (`40_power_precision.md#water_power_scaleup`).

**Roman-available inputs.** Limestone, clay, gypsum (Cyprus, Sicily, already traded) added at grinding to control set speed.

**Procedure.** (1) Grind limestone:clay roughly 4:1 by mass (ESTIMATED, standard raw-mix ratio) into slurry. (2) Feed a rotary kiln, a long tilted cylinder turning 1-3 rpm; flame temperature at the firing end must reach roughly 1800 C to hold material at 1450 C; refractory lining must survive it. (3) Output is clinker, dark grey glassy nodules; quench and cool. (4) Grind fine in a ball mill with a little gypsum to slow set to an hour or two; grinding heats the mill, and overheated cement hydrates inside it, ruining the batch, so cool while grinding. Gypsum plaster is separate and easier: calcine gently under 200 C, sets in minutes wetted, fast but ruined by rain outdoors. Artificial stone is just Portland concrete poured into reusable moulds mimicking dressed masonry.

**How you know it worked.** Clinker rings when struck, doesn't slake in water; ground cement sets hard within hours, most strength within a month, tested like pozzolana.

**Failure modes.** Underfired clinker stays chalky; overground overheated cement flash-sets in the mill; wrong gypsum dose ruins placement timing.

**Cost & labour.** ESTIMATED, a major standalone industrial project, generation-scale, not a first attempt.

**Danger.** Kiln burns, refractory collapse, silicosis from long grinding exposure. No social danger.

**Confidence: HIGH** on chemistry and temperatures, **LOW** on near-term Roman timeline.

### cn_post_lintel - Post and lintel, the theory of the beam

**What it is.** The plain beam across two supports, and the mathematics of why it holds or breaks, which nobody in 100 AD has even though everybody builds beams.
Also covers: cn_cantilever.

**Why you'd never guess this.** This is the real kernel of the module. A loaded beam bends: top fibre shortens (compression), bottom fibre stretches (tension), a neutral plane between carries nothing. Stone and plain concrete are strong in compression, weak in tension, so they always fail bottom-up, a crack starting underneath at midspan, invisible until nearly through. A mason knows a thicker beam spans further; he does not know deflection scales with the *cube* of span, so doubling the length gives eight times the sag for the same load, which is why copying a proportion at twice the scale fails badly. A cantilever, fixed one end, free the other, has no support to share load with, so its fixed end carries the full bending moment; a short-looking overhang can already be near its limit, worst exactly where you can't see it.

**Prerequisites.** `cap_tol_1mm`, timber or dressed stone.

**Roman-available inputs.** Seasoned oak or fir, dressed stone lintels, iron cramps.

**Procedure.** Keep material where tension will occur, never rely on tension-weak material past a span already tested to failure. Treat a cantilever's fixed end as the single critical section, never extend past a tested length.

**How you know it worked.** A test beam loaded to visible sag, not failure, springs back near-straight when unloaded; permanent set means you're near the limit.

**Failure modes.** Invisible bottom-fibre cracking; cantilevers extended past a tested length fail suddenly with little warning sag.

**Cost & labour.** ESTIMATED, one destroyed test sample per unproven span, cheap insurance.

**Danger.** Sudden unannounced collapse. No social danger.

**Confidence: HIGH** on physics; **HIGH** on Roman ignorance of it as formal theory, **MEDIUM** on how much survives as craft rule.

### cn_king_post - King post roof truss

**What it is.** A triangular timber frame converting a roof's bending problem into pure tension and compression, spanning further than one beam could.
Also covers: cn_queen_post, cn_timber_truss, cn_trussed_arch.

**Why you'd never guess this.** Wood is strong along the grain in both tension and compression, weak in long unsupported bending. Triangulate it, a central post in pure compression, rafters and tie beam in a closed triangle, and every member works its strong direction, at the cost of needing every joint to actually hold.

**Prerequisites.** cn_post_lintel, joinery, iron strap or bolt at tie joints.

**Roman-available inputs.** Seasoned timber, iron straps and pins, since mortise-and-tenon alone creeps under sustained load.

**Procedure.** King post: one central post, tie beam to apex, narrow spans. Queen post: two posts set inward, shortening the tie beam's unsupported length, wider spans, trickier geometry. General timber truss: more members, still wider roofs. Trussed arch: timber bracing bolted onto a masonry arch specifically to resist its outward spread, letting a thinner arch stand.

**How you know it worked.** No visible ridge sag after a full seasonal load cycle; no daylight gap opening at joints under load.

**Failure modes.** One slipped joint racks the whole triangle; timber failure is progressive, watch for a truss sagging more each year.

**Cost & labour.** MEASURED order of magnitude, days to weeks of carpentry per bay.

**Danger.** Falling roof timbers during erection; a failed truss can drop a whole roof at once.

**Confidence: HIGH** on triangulation; **MEDIUM** on exact Roman-attested geometry.

### cn_cast_iron_beam - Cast iron beam

**What it is.** A beam cast in iron, far stronger in compression than stone or timber. First item here gated on the metal itself, not calculation.
Also covers: cn_iron_column.

**Why you'd never guess this.** The classic killer: cast iron is brittle, weaker in tension than compression by roughly a third to half (ESTIMATED, known grey-iron ratios), giving almost no warning before snapping. A beam's bottom fibre is in tension, so a cast iron beam is weakest exactly where stone-trained instinct says thickness matters least. Columns are the opposite done right: pure compression, cast iron's strength, which is why hollow cast iron columns genuinely work and cast iron beams genuinely don't.

**Prerequisites.** Cast iron supply (`10_metallurgy.md#blast_furnace_cast_iron`, absent in the Roman West, bloomery gives only wrought iron), cn_post_lintel's beam theory.

**Roman-available inputs.** None directly, gated on the blast furnace tree. Once cast iron exists: sand moulds, a foundry, remelted pig iron.

**Procedure.** Columns: cast hollow, load only in pure axial compression, never off-centre. Beams: prefer wrought iron or steel; if cast iron must be used, thicken the tension face, test to failure at smaller scale first, never trust it under shock loading, since fracture starts from a casting flaw and every casting has some.

**How you know it worked.** A column carries rated load with no deformation; there is no reliable visual warning before a beam fails, which is the danger.

**Failure modes.** Sudden brittle fracture, no warning sag, cause of several 19th-century collapses; hidden casting flaws halving real strength.

**Cost & labour.** ESTIMATED, gated entirely on bulk cast iron existing first.

**Danger.** Sudden collapse with no warning, the deadliest failure mode in this module. Socially, a reputation for unexplained collapse kills future commissions.

**Confidence: HIGH** on the tension/compression asymmetry; **MEDIUM** on exact ratios, which vary with casting quality.

### cn_wrought_iron_girder - Wrought iron girder, and later steel

**What it is.** Getting iron to actually hold tension: first wrought iron, ductile and forgiving, then cheap bulk steel once `10_metallurgy.md`'s finery-to-crucible chain runs.
Also covers: cn_rolled_I_beam, cn_plate_girder, cn_box_girder, cn_steel_frame_skeleton.

**Why you'd never guess this.** The obvious move after cast iron fails is "more iron"; the correct move is a different iron. Wrought iron's fibrous grain, from repeated forging and folding, deforms visibly before breaking, unlike cast iron. Riveted wrought iron girders are flexible, not stiff, they bend and spring back, a feature, since that flex is your warning system. Rolling instead of riveting a single I-section is more efficient but needs a mill heating and squeezing the whole cross-section through shaped rollers, hard on the dies. A box girder resists twisting far better than an open I, since an open section has almost no torsional stiffness; welding it shut is expensive but makes long twist-resistant spans possible. A full steel skeleton moves all load into a steel grid, so walls become weathertight skin only, the change that eventually makes tall buildings possible.

**Prerequisites.** `10_metallurgy.md#finery_forge` for wrought iron; `cementation_steel`/`crucible_steel` before bulk steel is worth pursuing; rolling needs `40_power_precision.md#water_power_scaleup` or steam.

**Roman-available inputs.** Bloomery wrought iron bar, routine but small-batch, nowhere near structural tonnage.

**Procedure.** Forge-weld plates into a riveted girder, deep web for stiffness, thick flanges (flanges carry bending, web carries shear). Once rolling exists, roll one I-bar instead. Close a girder into a box by welding both flange edges and a second web shut where twisting matters.

**How you know it worked.** A girder deflects predictably under test load, returns to true unloaded; a box section resists hand-twisting an equivalent open section would not.

**Failure modes.** Rivets sheared by vibration loosen invisibly over years; an open section used where torsion matters twists and buckles; a cold-fed mill tears the billet.

**Cost & labour.** ESTIMATED, gated on bulk wrought iron then steel; one riveted girder is weeks of forge work.

**Danger.** Rivet failure under load, hot-metal burns. No unusual social danger once framing is established.

**Confidence: HIGH** on the tension/ductility argument; **LOW** on near-term timeline, deep in the metallurgy tree.

### cn_pratt_truss - Pratt truss, and the iron-age truss family

**What it is.** Once iron reliably holds tension, diagonals can be thin tension members instead of thick timber struts, cutting truss weight dramatically.
Also covers: cn_warren_truss, cn_lattice_truss, cn_space_frame.

**Why you'd never guess this.** A timber king post truss puts diagonals in compression, since timber joints handle compression better. An iron-age truss inverts this deliberately: Pratt truss diagonals run in tension, verticals in compression, letting diagonals be thin rod, since a tension member never buckles the way a compression member does. Warren truss removes verticals for consistent 45-degree diagonals, most material-efficient if geometry is precise, wasteful if not. Lattice truss crosses many thin diagonals to save weight at full depth, at the cost of many joints, each an unannounced weak point. Space frame triangulates in three dimensions, very light for span, but every joint carries load from several directions at once, making the joint the whole design problem.

**Prerequisites.** cn_wrought_iron_girder or steel, cn_riveted_connection, cn_post_lintel's beam theory.

**Roman-available inputs.** Only ordinary bar stock once bulk iron exists; the principle needs no new material, only the will to put iron in tension deliberately.

**Procedure.** Lay out geometry precisely before fabrication, these forms depend on angle, not oversized members, for efficiency. Size diagonals for the tension load calculated or model-tested; size compression members against buckling, which happens well below crushing strength, a separate failure mode.

**How you know it worked.** A loaded test truss deflects a small predictable amount and returns true; no joint shows slip.

**Failure modes.** One failed joint redistributes load onto neighbours not sized for it, a chain failure; compression members buckling sideways, invisible until already curved.

**Cost & labour.** ESTIMATED, precise geometry costs fabrication time but saves weight.

**Danger.** Progressive chain-failure collapse. No unusual social danger.

**Confidence: HIGH**, well documented from the historical truss-bridge era.

### cn_riveted_connection - Riveted, bolted, gusseted, and welded joints

**What it is.** How iron and steel members are actually joined, since a joint is usually the weak point, not the member.
Also covers: cn_bolted_connection, cn_gusset_plate, cn_welded_connection.

**Why you'd never guess this.** A rivet is heated red hot, dropped through aligned holes, hammered flat both ends hot; cooling contraction, not the pin filling the hole, clamps the plates. A bolt relies on thread accuracy and how hard the nut is turned, weaker per fastener but fast and removable. An arc weld can match parent steel strength cooled slowly, but cooled fast forms brittle martensite right at the joint, so quality is entirely technique, not equipment. A gusset plate spreads force along a stiffer path than the members alone, but too many rivets in it concentrates stress at the hole pattern instead.

**Prerequisites.** cn_wrought_iron_girder or steel, a forge, for welding `10_metallurgy.md` alloy steel plus a reliable arc (`50_electricity.md`).

**Roman-available inputs.** Iron rod stock, forge, tongs, hammers.

**Procedure.** Heat a rivet to bright orange-yellow, hammer the protruding end flat against a backing bar before it cools past dull red. Cut bolt threads accurately (`40_power_precision.md#screw_cutting_lathe`), torque by feel or gauge, expect vibration loosening without a lock nut. Weld with a steady arc rate matched to plate thickness, cool slowly, never quench.

**How you know it worked.** No gap a thin blade slips under a cooled rivet head; a bolted joint survives a hard shake test; a weld bead is smooth when hammer-tapped.

**Failure modes.** A cold-driven rivet never clamps and works loose; an over-torqued bolt snaps its thread; a rushed weld cracks months later.

**Cost & labour.** MEASURED for riveting, minutes per rivet, thousands on a large bridge; DERIVED for bolting, faster but needs precision threading first.

**Danger.** Hot rivet burns; a snapped bolt or failed weld releases stored force violently.

**Confidence: HIGH** on riveting/bolting; **MEDIUM** on welding, gated on electrical capability.

### cn_reinforced_concrete - Reinforced concrete slab and beam

**What it is.** Concrete cast around steel bars so steel carries the tension plain concrete cannot, giving flat slabs and beams plain concrete never could.
Also covers: cn_deformed_rebar, cn_precast_panel.

**Why you'd never guess this.** The second real kernel: reinforced concrete works only because steel and set concrete expand with temperature at nearly the same rate, roughly 10-14 millionths per degree C for both (MEASURED, unverifiable to a Roman without precision thermal measurement). If they didn't match, every seasonal cycle would peel the bond apart, and the whole technology would be a curiosity. Nobody engineered this, it is a coincidence of iron oxide and silicate rock under heat. Second point, equally load-bearing: steel must sit exactly where the tension is, the *bottom* of a simple beam, the *top* over a support where bending reverses. Wrong face and you've built an expensive plain concrete beam.

**Prerequisites.** cn_portland_cement or tested pozzolana (weaker), bulk wrought iron or steel bar, cn_post_lintel's beam theory.

**Roman-available inputs.** None for bar steel; wrought iron bar substitutes at reduced effect. Either concrete works chemically.

**Procedure.** Place bar exactly along the tension face before pouring, never after; keep a few centimetres of cover, since concrete's alkaline pore water protects steel only while uncracked and fully encased. Vibrate around bars so no voids trap air against them. Deformed rebar (rolled ribs) bonds mechanically rather than by friction alone, and that bond transfers load, invisible failure until the beam suddenly deflects. Precast panels apply this in a factory for consistency and speed, at the cost of transport and weak panel-to-panel joints.

**How you know it worked.** A reinforced test beam outlasts an identical unreinforced one; a cut section shows the bar still bonded, no rust bleed.

**Failure modes.** Bar in the compression zone, doing almost nothing; inadequate cover letting the bar rust, and rust's greater volume spalls the concrete off from inside, slow, with no Roman precedent; undetectable bond failure.

**Cost & labour.** ESTIMATED, gated on cement and bulk steel both, a late combination, not a first project.

**Danger.** Sudden failure with no warning cracking. No unusual social danger.

**Confidence: HIGH** on the coincidence and tension-face placement; **LOW** on Roman-era timeline.

### cn_prestressed_concrete - Prestressed concrete element

**What it is.** Stressing steel before the concrete ever takes load, so concrete starts in compression everywhere; service load must cancel that first before creating any tension.
Also covers: cn_post_tensioning.

**Why you'd never guess this.** Ordinary reinforced concrete still cracks near the bar under tension; the crack's load then falls on the steel. Stress the tendon first, stretched before pour and released after cure, or threaded through cured concrete and jacked tight after, and the concrete is squeezed permanently before service load arrives, staying crack-free under loads that would split ordinary reinforced concrete, and allowing longer, thinner spans.

**Prerequisites.** cn_reinforced_concrete, high-strength steel wire (ordinary bar stretches too much), a hydraulic jack for controlled tension.

**Roman-available inputs.** None, needs bulk high-strength wire and hydraulics beyond Roman reach.

**Procedure.** Post-tensioning: cast with hollow ducts placed for the tendons, cure fully, thread cable, jack each to specified tension, lock with a wedge anchor, then grout the duct.

**How you know it worked.** The jack gauge shows target load before lock-off; the element shows no cracking under a proof load that would crack an equivalent unstressed beam.

**Failure modes.** Jack failure under high pressure is violently dangerous; a mis-placed duct causes uneven, hidden internal damage; stress loss over years without margin.

**Cost & labour.** ESTIMATED, gated on wire, jacks, and reinforced concrete all existing first.

**Danger.** A failed jack or snapped tendon releases stored energy violently, one of the more dangerous moments in this module.

**Confidence: MEDIUM-HIGH** on physics; **LOW** on reachability, end of several chains.

### cn_suspension_bridge - Suspension bridge system

**What it is.** A deck hung from cables in pure tension, spanning gaps no beam or arch can reach economically.
Also covers: cn_cable_anchorage, cn_wire_cable_spinning, cn_stiffening_truss.

**Why you'd never guess this.** The cable looks like the hard part and is actually the easy one: many thin wires spun in place strand by strand are stronger and more uniform than any chain link, provided bundle rotation is controlled during spinning or it twists itself apart before ever loaded. The real problem, learned expensively and repeatedly, is aerodynamic stiffness of the deck. A light deck can twist under wind in a way that feeds energy into its own oscillation instead of damping it, a resonance that grows until the deck tears apart, Tacoma Narrows being the filmed example. A stiffening truss adds weight and torsional resistance so the deck can't twist freely; tuned dampers do the same with less weight and far more design difficulty. Towers resist the horizontal component of enormous cable tension, which is why they dwarf the deck they seem to merely hold up.

**Prerequisites.** Bulk steel wire (`10_metallurgy.md#wire_drawing`), cn_post_lintel and cn_pratt_truss's tension logic, an anchorage massive enough for the cable's stress cone.

**Roman-available inputs.** None, a late high-tonnage technology with no partial Roman version.

**Procedure.** Erect towers first. Spin the main cable strand by strand with a travelling wheel, controlling rotation throughout. Anchor each end into a block large enough that the cable's stress cone stays inside its mass, undersized and the wedge pulls free violently. Hang the deck from vertical hangers, stiffen it full-length against twist.

**How you know it worked.** Minimal deck twist under crosswind, tested with streamers before trusting load; uniform cable tension by sag curve.

**Failure modes.** Aerodynamic flutter, capable of destroying an otherwise sound bridge in minutes; anchorage pull-out; uncontrolled spinning rotation losing cable strength invisibly.

**Cost & labour.** ESTIMATED, one of the largest, latest projects in the tree, gated on bulk steel wire.

**Danger.** Catastrophic sudden collapse with almost no warning to people on the deck. A public collapse is a severe reputational blow.

**Confidence: HIGH** on the mechanisms; **LOW** on near-term reachability.

### cn_arch_bridge_steel - Steel arch bridge

**What it is.** The masonry arch's compression path rebuilt in steel, reaching much further than stone voussoirs.

**Why you'd never guess this.** A masonry arch is fixed and heavy of necessity, since stone can only push, and any temperature change or settlement in a rigid arch builds hidden internal stress with nowhere to go, over-determined and unable to flex. A steel arch hinged at its base (sometimes the crown too) can rotate slightly at those points, absorbing thermal change as a small rotation instead of hidden stress a rigid arch won't show until it cracks.

**Prerequisites.** cn_wrought_iron_girder or steel, cn_true_arch's load-path logic, a hinge that carries full thrust while still rotating freely.

**Roman-available inputs.** None, steel-tonnage technology.

**Procedure.** Design the arch curve to match its expected thrust line. Place hinges at the base and, for very long spans, the crown, using a pin bearing that rotates under full compression without seizing from rust or debris.

**How you know it worked.** The hinge rotates a small expected amount across a seasonal swing with no new cracks elsewhere.

**Failure modes.** A seized hinge silently becomes a rigid joint again, reintroducing the stress it was built to avoid; a mismatched thrust curve concentrates stress at one point.

**Cost & labour.** ESTIMATED, gated on bulk steel and precision hinges.

**Danger.** Sudden compression buckling if the thrust line drifts outside the material.

**Confidence: MEDIUM-HIGH** on the hinge logic; **LOW** on reachability.

### cn_bascule_bridge - Bascule, swing, and pontoon bridges

**What it is.** Three ways to open a bridge for river traffic: a counterweighted tilting leaf, a whole span pivoting centrally, and a floating anchored roadway.
Also covers: cn_swing_bridge, cn_pontoon_bridge.

**Why you'd never guess this.** A bascule's counterweight must balance the leaf, but the balance point shifts through its arc, so the mechanism must suit the whole range of motion, not just closed or open, or it jams. A swing bridge's central pivot carries the whole deck on one small bearing, enormous friction, and any binding on the guide rail jams a bridge that otherwise pivots freely. Pontoon is simplest and the only one already within Roman reach (Caesar's Rhine crossings show the competence); it rises and falls with the water, approach ramps must accommodate that, and it's normally removable for winter ice.

**Prerequisites.** Bascule/swing: bulk iron or steel, precise bearings (cn_wrought_iron_girder). Pontoon: Roman carpentry and boat-building only.

**Roman-available inputs.** Pontoon: timber, boats, rope or chain, all Roman. Bascule/swing: gated on iron/steel tonnage.

**Procedure.** Bascule: size the counterweight against the leaf's weight at several arc points, not one. Swing: centre and lubricate the pivot, keep the guide rail clear. Pontoon: anchor floats against current, build ramps with vertical play, plan seasonal removal.

**How you know it worked.** Bascule/swing open and close through full range without stalling; pontoon rises freely without straining its lines.

**Failure modes.** Miscalculated mid-arc load stalling a bascule; a binding swing pivot; pontoon anchor failure in flood, releasing the span downstream.

**Cost & labour.** MEASURED for pontoon, already within reach; ESTIMATED and gated for bascule/swing.

**Danger.** A jammed moving bridge is a serious hazard to river and road traffic at once.

**Confidence: HIGH** on pontoon; **MEDIUM** on bascule and swing mechanics.

### cn_gravity_dam - Gravity dam, arch dam, earth dam, spillway, retaining wall

**What it is.** Holding back water or soil with mass, curvature, or both, and calculating whether it slides, overturns, or is lifted off its foundation by water pressing beneath.
Also covers: cn_arch_dam, cn_earth_dam, cn_spillway, cn_retaining_wall.

**Why you'd never guess this.** A gravity dam holds back water by being too heavy to slide or tip, so the foundation, not the wall, is usually the real limit, soil can't support the load, only rock can, and seepage under the base creates uplift that can lift the dam like a boat if undrained. An arch dam curves the load sideways into its abutments the way a masonry arch transfers load into supports, needing far less mass, but a bad abutment fails catastrophically rather than merely leaking. An earth dam's clay core must be more impermeable than the surrounding fill or seepage concentrates into an internal channel, piping, silent until sudden and total. A spillway exists purely to control overtopping; water over an undesigned crest erodes at very high velocity, and one miscalculated crest elevation dooms the whole structure regardless of dam quality. A retaining wall is the same soil-pressure problem at building scale, needing enough mass and the right base geometry, aided by drainage relieving pressure from behind it.

**Prerequisites.** cn_true_arch for arch-dam curvature, cn_pozzolana_concrete or cn_portland_cement, rock foundation surveying.

**Roman-available inputs.** Cut stone, concrete, clay, all Roman; missing is the calculation of sliding/overturning/uplift, currently done, if at all, by conservative overbuilding.

**Procedure.** Site on sound rock wherever possible. Gravity dam: proportion mass so weight comfortably exceeds water's horizontal push, and drain the foundation to relieve uplift rather than resist it with mass alone. Arch dam: confirm abutment rock can take the thrust first. Earth dam: build the core distinctly less permeable than shoulders, monitor seepage continuously, cloudy or rising seepage is early warning. Spillway: size for the worst flood plus margin, never trim for cost.

**How you know it worked.** No measurable base movement after a full pool cycle; seepage runs clear; the spillway has passed a real flood untopped elsewhere.

**Failure modes.** Uplift lifting the base; sudden total abutment failure; invisible piping erosion until a sinkhole appears; an undersized spillway eroding the dam body itself.

**Cost & labour.** ESTIMATED, steep with height; a modest masonry gravity dam is reachable with Roman materials and caution, larger dams need real calculation this tree lacks.

**Danger.** Downstream failure is mass-casualty scale, among the worst modes in this module.

**Confidence: HIGH** on the mechanisms; **MEDIUM** on Roman-era sizing without formal calculation.

### cn_pile_driving - Pile driving, screw piles, soil compaction

**What it is.** Raising a foundation's bearing capacity in soft ground, either driving a pile to firmer material or densifying the soil itself.
Also covers: cn_screw_pile, cn_soil_compaction.

**Why you'd never guess this.** A drop-hammer pile compresses and packs the soil around it as it goes, which is why driving gets harder with depth, each blow achieving less penetration, and a foreman tracking that diminishing penetration is measuring bearing capacity in real time without any instrument. A screw pile, a shaft with a helical blade, is twisted rather than hammered, but wrong pitch or angle means it spins in place without advancing, and uneven torque along its length loses capacity invisibly. Soil compaction by rolling works the same densification logic, but only within an optimal moisture range, too dry or too wet both resist it, since water fills the pore space compaction is meant to close.

**Prerequisites.** cn_crane_treadwheel or a gin-pole hoist for the drop hammer, iron for the helix, nothing beyond Roman baseline for compaction.

**Roman-available inputs.** Timber piles, iron shoes, iron helix blades once forged, stone or timber rollers.

**Procedure.** Drop-hammer: raise and drop repeatedly, tracking penetration per blow, stop once it falls below a set small amount. Screw pile: match helix pitch to soil by trial, apply even torque throughout. Compaction: test moisture by feel (holds shape squeezed, not wet), roll repeatedly, tracking diminishing benefit per pass.

**How you know it worked.** Penetration per blow has dropped to a small stable figure across several more blows; compacted soil resists a firmly pressed boot heel.

**Failure modes.** A pile in a soft pocket that never reaches bearing, invisible until the structure settles; a screw pile spinning without advancing; over- or under-moist compaction that looks finished but isn't.

**Cost & labour.** MEASURED order of magnitude, standard heavy labour, days per pile.

**Danger.** Dropped hammer weight crushes workers.

**Confidence: HIGH**, easily observed in practice.

### cn_cofferdam - Cofferdam, dewatering, diaphragm wall, sheet piling

**What it is.** Four ways to keep water out of a hole you need to dig, from a temporary dike to a permanent slurry-formed wall.
Also covers: cn_dewatering, cn_diaphragm_wall, cn_sheet_piling.

**Why you'd never guess this.** A cofferdam is a dike, pumped dry, but leakage rises as outside water pressure builds relative to the dry pit, so pump capacity must grow through the job, and one pump with no backup is a single point of failure for the whole excavation. Dewatering lowers the water table more broadly, which also lets nearby ground settle as the water supporting it is removed, meaning a job can crack a neighbour's foundation while perfectly protecting your own. Sheet piling, interlocking plates driven side by side, needs a tight interlock or water seeps between sheets, and, non-obviously, each new sheet is pushed against the friction of every sheet already driven beside it, so the last sheets in a long run are hardest, not easiest. A diaphragm wall excavates a trench filled with clay slurry that holds the walls open without shoring, then concrete poured through a tremie pipe kept submerged displaces the lighter slurry upward rather than mixing with it, a use of clay Rome does not currently make.

**Prerequisites.** Timber and iron, continuous mechanical pumping (`40_power_precision.md#hydraulics_pumps`), bentonite-equivalent slurry knowledge for diaphragm walls.

**Roman-available inputs.** Timber, clay, forged iron sheet; the pump is the real gate, Roman force pumps aren't reliable at the needed continuous capacity.

**Procedure.** Cofferdam: oversize the dike, run two pumps so one failure doesn't flood the site. Dewatering: monitor nearby structures throughout, not just at the end. Sheet piling: drive in sequence, check interlock tightness sheet by sheet. Diaphragm wall: keep slurry level high whenever work pauses, a dropped level is what lets trench walls collapse; place concrete through a submerged tremie.

**How you know it worked.** A cofferdam stays dry with steady pump output; a diaphragm trench holds shape overnight.

**Failure modes.** Single-pump flooding; dewatering-induced settlement cracking neighbours; loose sheet interlocks leaking soil through with the water; a slumped diaphragm trench from a dropped slurry level.

**Cost & labour.** ESTIMATED, cofferdam and sheet piling reachable with Roman materials plus pumping; diaphragm wall has no Roman precedent at all.

**Danger.** Sudden flooding is a drowning/crush hazard; settlement is a legal and social hazard, a cracked neighbour's wall won't care your own site stayed dry.

**Confidence: MEDIUM-HIGH** on cofferdam and sheet piling; **MEDIUM** on diaphragm wall.

### cn_caisson - Caisson, pneumatic caisson, underpinning

**What it is.** Building a foundation below water or below an existing structure, inside a sealed or pressurised chamber, or by replacing an old foundation piece by piece while the building stays standing.
Also covers: cn_pneumatic_caisson, cn_underpinning.

**Why you'd never guess this.** A simple caisson sinks under its own weight as material is dug from inside, sealed at every joint or it floods, and a failed seal with men inside can be sudden. A pneumatic caisson pressurises the chamber to match water pressure at depth, letting men dig the open face directly, but introduces a genuinely new danger: workers ascending from high pressure too fast get caisson disease (the bends), nitrogen bubbling out of the blood as pressure drops, with no warning at the time of exposure and an agonising delayed onset, so slow staged decompression must be followed even when nothing seems wrong. A sand boil, sudden inrush when pressure drops even briefly, can undermine a chamber wall in moments. Underpinning removes and replaces an existing foundation under a building that must not move, even a millimetre of uneven settlement can crack walls above, so work proceeds one small shored section at a time.

**Prerequisites.** cn_cofferdam's sealing logic, compressed air supply and pressure control (beyond Roman force pumps), adjustable shoring for underpinning.

**Roman-available inputs.** Timber, iron seals; pneumatic capability itself is not Roman-reachable without dedicated development.

**Procedure.** Simple caisson: seal every joint, test under load before committing workers. Pneumatic: raise pressure gradually, decompress on a slow staged schedule every shift regardless of how workers feel, since symptoms appear after exposure, not during. Underpinning: shore section by section, replace one small section at a time, monitor a fixed reference mark before moving to the next.

**How you know it worked.** A caisson sinks evenly with no leaks; a crew shows no delayed pain or dizziness after decompression; underpinned sections show no new cracking above.

**Failure modes.** Sudden flooding from a seal failure; rushed decompression causing the bends hours after the crew feels fine; a sand boil undermining a wall in moments; underpinning too large a section at once, cracking the structure above.

**Cost & labour.** ESTIMATED, slow specialised work, small crews on short shifts at depth.

**Danger.** The bends is a genuinely novel danger, a symptom appearing only after the danger seems past. Sand boils and seal failures are acute drowning risks.

**Confidence: HIGH** on the bends' mechanism; **LOW** on Roman-era pneumatic capability.

### cn_drill_blast - Tunnelling by drill and blast

**What it is.** Breaking rock by planned explosive charges in drilled holes, the only way to advance through hard rock at useful speed.
Also covers: cn_tunnel_cut_cover, cn_ventilation_shaft.

**Why you'd never guess this.** More explosive is not faster progress. Charges fired in the wrong sequence, rather than a planned pattern (centre cut first for a free face, rings fired outward toward it), leave large boulders and poor fragmentation, costing as much hand-breaking time as the blast saved; too much charge per hole wastes powder and damages walls the tunnel later relies on. Cut-and-cover, an open trench, structure built in it, covered over, suits only shallow tunnels, since the roof carries everything piled back on it plus traffic, worsening with depth; past a point the shield method is better. A ventilation shaft, usually far shallower than the tunnel, works by natural stack effect, warm air rising draws fresh air in, unless obstructed, in which case foul air and blast fumes pool at the face.

**Prerequisites.** Explosive is a genuine anachronism trap, Rome has none, this technique is gated on chemistry outside this module; rock drilling, cn_quarrying_wedge's grain-reading.

**Roman-available inputs.** None for explosive; drilling and rock-reading, timber shoring, iron bits, all Roman.

**Procedure.** Drill a planned pattern, deepest toward centre, fire centre holes first for a free face, then rings outward in sequence, clear fumes before re-entering. Size a cut-and-cover roof for the worst load it will ever carry before backfilling. Site ventilation shafts to work with the tunnel's natural draft.

**How you know it worked.** Well-fragmented rock, no boulder too large to move by hand; a shaft draws a candle flame toward the entrance.

**Failure modes.** Wrong sequence leaving boulders and wasted charge; overcharged holes damaging walls that later collapse; an undersized cut-and-cover roof crushed by backfill; a blocked shaft pooling fumes, a suffocation risk with no warning smell for some gases.

**Cost & labour.** ESTIMATED, gated on explosive availability; without it, hand-break progress is a few metres per week per crew (ESTIMATED, basis: pre-explosive historical rates).

**Danger.** Misfire, premature detonation, fume poisoning, all acute; explosives carry real social danger, a magistrate treats unauthorised large-scale production as a threat, not a curiosity.

**Confidence: MEDIUM** on blast mechanics; explicitly **LOW** on Roman-era explosive availability.

### cn_tunnel_shield - Tunnel shield method, and tunnel lining

**What it is.** A protective shell pushed forward by jacks through soft ground, letting men excavate safely while permanent lining rings go in immediately behind, the method that makes tunnelling soft, unstable ground survivable.
Also covers: cn_tunnel_lining.

**Why you'd never guess this.** In hard rock the rock briefly holds its own shape, giving time to shore. In soft ground, sand, clay, waterlogged soil, the face can collapse the instant it's exposed, no grace period, which is exactly what the shield solves, holding the face open while men work just behind its leading edge, pushed forward by jacks bearing against the lining already installed behind, so the tunnel builds its own advancing anchor. In waterlogged ground the face may need pressurising or support (an early relative of cn_caisson's logic) or it flows into the shield faster than it can be removed. Lining rings are cast and cured before installation, so installation is fast, but every joint must be tight, water finding a joint slowly rots the lining from inside over years, no dramatic warning until it fails structurally.

**Prerequisites.** cn_wrought_iron_girder or steel for shell and jacks, cn_concrete_mixer-scale production for lining segments, cn_caisson's sealing and pressure logic.

**Roman-available inputs.** None, a late steel-and-concrete-industry combination with no partial Roman precedent.

**Procedure.** Push the shield forward in short jacked increments, excavating only the exposed increment at any time. Install a lining ring immediately behind, providing the next jacking point. Grout the gap behind the lining promptly, an ungrouted void lets the ground above settle unevenly.

**How you know it worked.** Steady advance with no sudden surface settlement above the line; no seepage at lining joints.

**Failure modes.** Face collapse into the shield without pressure support; an ungrouted void causing delayed settlement, sometimes long after the tunnel is forgotten; leaking joints rotting the lining slowly.

**Cost & labour.** ESTIMATED, a late-tree, capital- and steel-intensive technique.

**Danger.** Face collapse is an acute burial hazard; poorly grouted settlement endangers anyone above ground unaware a tunnel runs beneath them.

**Confidence: MEDIUM** on mechanics; explicitly **LOW** on near-term reachability.

### cn_crane_derrick - Derrick and tower cranes, elevator safety brake

**What it is.** Lifting machinery beyond the treadwheel's practical scale, once continuous power and steel exist for taller, stronger masts.
Also covers: cn_crane_tower, cn_elevator_safety_brake.

**Why you'd never guess this.** A derrick's mast is strong in straight-up compression, weak against side load, exactly what unevenly tensioned guy lines introduce; a loose stay that whips in wind is a warning, not a nuisance. A tower crane's jib and load are cantilevered from a fixed mast, so the base must be heavy enough against the overturning moment, worse the further the jib reaches, and wind on the tall exposed structure adds to it, so bracing adequate in calm weather can fail in a storm never tested against. An elevator's safety brake is the clearest lesson here: its jaws are held open by tension in the very cable that might break, so as that tension drops, the drop itself triggers the brake, the failure event arms the safety device, elegant, but only if the wedge angle is exactly right, too shallow and it slips instead of gripping.

**Prerequisites.** cn_wrought_iron_girder or steel, cn_riveted_connection, continuous power (`40_power_precision.md#gearing_and_transmission`, `steam_high_pressure`).

**Roman-available inputs.** Timber builds a modest derrick within Roman means; tower crane and elevator brake are iron/steel-tonnage technologies gated well beyond baseline.

**Procedure.** Derrick: tension all guy lines equally before loading, recheck after any load change. Tower crane: size the base counterweight against maximum load at maximum reach plus expected wind, not calm-weather average. Elevator brake: set the wedge angle by testing against a deliberately cut cable before ever trusting a rider, inspect regularly for corrosion or debris.

**How you know it worked.** A derrick stays plumb under full load in stiff wind; a tower crane shows no base uplift opposite the load at maximum reach; a test-cut cable stops the cage within a short predictable distance.

**Failure modes.** Unequal guy tension bending or toppling a mast; wind-driven overturning of a crane sized only for calm conditions; a wrong wedge angle that slips instead of grips, the single most consequential failure here since it endangers a rider.

**Cost & labour.** ESTIMATED, derricks reachable at modest scale with Roman timber and rope; tower cranes and elevator brakes are late-tree.

**Danger.** A toppling mast or crane crushes anyone nearby; a failed elevator brake is a fall hazard the rider cannot personally prevent once the cable has parted.

**Confidence: HIGH** on the mechanical logic; **LOW** on reachability for the tower crane and elevator brake specifically.

### cn_concrete_mixer - Concrete mixing and placing at scale

**What it is.** Machinery and technique that let concrete be placed fast and evenly at real building scale, not one hand batch at a time.
Also covers: cn_formwork_shuttering, cn_slipform, cn_shotcrete, cn_vibratory_compaction, cn_expansion_joint.

**Why you'd never guess this.** A rotary mixer has a narrow optimum speed: too slow and heavy aggregate settles while paste stays on top, segregating rather than mixing; too fast and centrifugal force pins everything to the drum wall, which looks like mixing but isn't. Formwork must be stiff enough not to deflect under wet concrete's full weight, and any deflection while wet becomes permanently cast into the finished surface, unfixable after the fact. Slipform raises the stakes, the form creeps continuously upward as concrete is poured below, creep rate tuned exactly against setting speed, too fast breaks unsupported wet concrete, too slow cracks set concrete against the moving form's friction. Shotcrete wastes real material to rebound on vertical surfaces and needs slow controlled curing or drying shrinkage cracks the thin layer. Vibration has a narrow window, too little leaves voids, too much un-mixes it, shaking heavy aggregate down and light paste up, the working window is only five to ten seconds per area (ESTIMATED, standard modern practice). Expansion joints exist because concrete moves roughly 10-15 mm per 100 m across a 50-degree swing (ESTIMATED, standard thermal coefficients); without a joint it cracks itself at a point of its own choosing, so joints are normally spaced under 20 m apart.

**Prerequisites.** cn_pozzolana_concrete or cn_portland_cement, mechanical power for mixer and vibrator, timber for formwork.

**Roman-available inputs.** Timber formwork, already Roman; mechanised mixing, slipform, shotcrete, and powered vibration are beyond baseline, gated on continuous power.

**Procedure.** Run the mixer at tested optimum speed. Build formwork stiff enough to show no deflection under a test load equal to the wet concrete, strike only once self-supporting. Match slipform creep rate to on-site tested setting time. Angle the shotcrete nozzle to minimise rebound, cure damp and slow. Vibrate in short bursts, moving steadily, stop once the surface goes smooth and glistening. Place expansion joints regularly with compressible filler that squeezes rather than extrudes.

**How you know it worked.** Uniform mixed batch, no settled aggregate; a struck formwork surface is flat and true; vibrated concrete rings solid when tapped, no hollow spots.

**Failure modes.** Segregated concrete from wrong mixer speed; formwork deflection cast permanently into the surface; slipform mismatch breaking wet concrete or cracking set concrete; shotcrete rebound waste and shrinkage cracking; over- or under-vibrated concrete, weak either way; missing expansion joints cracking the slab uncontrolled.

**Cost & labour.** DERIVED, formwork and hand mixing are within Roman means; mechanised versions need continuous power this tree may not yet have on site.

**Danger.** Formwork collapse under wet concrete can bury or crush workers.

**Confidence: HIGH** on the mechanics; **MEDIUM** on reachability without dedicated site power.

### cn_curtain_wall - Curtain wall, plate glass, sash window, asphalt roofing, corrugated roof

**What it is.** How a building's outer skin works once a frame, not the wall, carries structural load, freeing the wall to be thin and glazed.
Also covers: cn_plate_glass_window, cn_sash_window, cn_asphalt_roofing, cn_roof_truss_corrugated.

**Why you'd never guess this.** A curtain panel is supported only at its top, hanging rather than standing, and every wind load travels through its fasteners into the frame, with essentially no redundancy, one failed seal is one failed panel. This idea only works once cn_steel_frame_skeleton exists to carry real load; without a frame there's nothing to hang from, so the wall must be load-bearing, all Rome has ever needed a wall to be. Plate glass at real size is slow to cast, and slow controlled annealing afterward matters as much as casting, internal stress left by fast cooling can crack a pane months later for no visible reason. A sash window trades a simple opening for smooth operation via cord, pulley, and counterweight, but the weight must exactly balance the pane or it won't stay open or will slam shut, and cord wear is invisible until it snaps. Asphalt roofing is sharply temperature-sensitive at installation, too cold it cracks, too hot it flows away, and laps must overlap downslope or trap water. Corrugated iron is stiff because of its corrugations, not despite them, flat sheet of the same thickness would sag badly, but fastening through the ridges concentrates stress at each hole, and daily thermal cycling against those fasteners is the source of a corrugated roof's characteristic ticking.

**Prerequisites.** cn_steel_frame_skeleton for true curtain wall, Roman glassblowing (`30_glass_optics.md`) scaled up, bitumen (already traded) for roofing, cn_wrought_iron_girder-tonnage rolled sheet for corrugated iron.

**Roman-available inputs.** Roman glassblowing already produces clear panes at modest size; bitumen is a known traded material; sheet rolling and curtain framing are gated on tonnage above.

**Procedure.** Anneal glass slowly with a controlled cooling gradient, generous time if no way to check for residual stress. Balance sash counterweights precisely, inspect cords on a schedule. Install asphalt within its stated temperature range, lap downslope always. Fasten corrugated roofing through ridges where possible, allow slight play for thermal movement.

**How you know it worked.** No water ingress at a curtain panel after a storm; an annealed pane shows no spontaneous cracking after weeks of cycling; a sash rises and holds at any height; roofing sheds a hose test.

**Failure modes.** A single failed curtain seal with no redundancy; unannealed glass cracking with no warning; a worn cord snapping suddenly; out-of-range asphalt cracking or sliding; fatigued corrugated fasteners leaking at every hole.

**Cost & labour.** ESTIMATED for curtain wall, late-tree and steel-gated; the other four are individually reachable earlier at modest cost.

**Danger.** A falling curtain panel is a hazard below; a snapped sash cord can injure or drop suddenly.

**Confidence: MEDIUM-HIGH** on components; **LOW** on curtain wall as a system.

### cn_cavity_wall - Cavity wall, damp proof course, insulation

**What it is.** Keeping moisture and heat where they belong using an air gap, a moisture barrier, and trapped air, none of which a solid Roman masonry wall does deliberately.
Also covers: cn_damp_proof_course, cn_insulation.

**Why you'd never guess this.** A cavity wall's outer leaf is expected to get wet while the inner stays dry across a gap, but the ties holding the leaves together, without which it's two unstable skins, become thermal bridges carrying heat straight across the gap meant to break it, and the cavity must stay clear of mortar droppings or moisture bridges across the debris instead. A damp proof course is a thin impermeable layer built in specifically to break capillary rise, since masonry wicks groundwater up several metres with no pump needed, easy to underestimate until you see how far rot and salt staining reach without one. Insulation works by trapping still air, since the still air is what resists heat flow, not the material holding it, which is why compressing insulation destroys it, and a vapour barrier is needed in cold climates or migrating moisture condenses inside and saturates it from within.

**Prerequisites.** Ordinary masonry, cn_wrought_iron_girder-scale iron for ties, an impermeable sheet for the damp course, any low-density fibrous fill for insulation.

**Roman-available inputs.** Fired brick and mortar, bitumen as a plausible damp course, wool or chaff as plausible crude insulation, though not currently used this way.

**Procedure.** Build two independent leaves with a continuous clear gap, tied to shed water droplets rather than carry them across, keep the cavity clear of mortar debris. Lay a continuous damp course with no gaps, a single gap defeats the whole course. Pack insulation loosely, never compressed, with a vapour-resistant layer on the warm side in cold climates.

**How you know it worked.** No damp staining above a proper damp course after a wet season; the inner leaf stays dry while the outer weathers; an insulated wall feels less cold to the hand.

**Failure modes.** Mortar droppings bridging the cavity gap; a damp course with even one gap; compressed or wet insulation, silently useless though still present.

**Cost & labour.** DERIVED, modest additional material and care, no new heavy industry.

**Danger.** No acute danger, only long-term unseen rot and salt damage.

**Confidence: HIGH**, physics well established, reachable with Roman materials, missing mainly the technique.

### cn_central_heating - Central heating, radiators, forced ventilation

**What it is.** Distributing heat via circulating hot water and moving air mechanically, beyond what a Roman hypocaust does with hot air under the floor.
Also covers: cn_radiator, cn_forced_ventilation.

**Why you'd never guess this.** A hot water system must stay filled and free of trapped air, an air pocket stops circulation exactly the way one stops a siphon (cn_aqueduct); an expansion tank is needed because water expands as it heats, and without somewhere for that to go a sealed system builds dangerous pressure. Radiators lose heat transfer to mineral scale with no outward sign until the room is simply colder for the same fuel. Forced ventilation's fan noise rises sharply with speed, so an undersized duct forces a fan to run faster than comfortable, and a damper closed fully against a running fan can overheat it.

**Prerequisites.** cn_wrought_iron_girder-scale iron for radiators and piping, mechanical power for the fan, the existing hypocaust as the natural starting point.

**Roman-available inputs.** The hypocaust itself, already routine in baths and villas; iron pipe and radiator sections are the missing pieces for a water-based system.

**Procedure.** Fill the system completely before firing, bleed air from every high point. Size an expansion tank generously against total water volume and temperature rise. Keep radiator water as scale-free as practical, flush periodically. Size ducts generously so the fan need not run at maximum for ordinary operation, never fully close a damper against a running fan.

**How you know it worked.** Radiators run hot evenly along their length; ventilation moves audibly but not uncomfortably at normal speed.

**Failure modes.** Trapped air stopping circulation; a missing expansion tank building dangerous pressure; scaled radiators losing capacity invisibly; a stalled overheating fan.

**Cost & labour.** ESTIMATED, gated on real iron tonnage well beyond the hypocaust's brick-and-tile.

**Danger.** An over-pressured system can rupture violently; a stalled fan is a fire risk.

**Confidence: MEDIUM-HIGH** on mechanics; **LOW** on near-term reachability.

### cn_plumbing_stack - Plumbing stack and trapped drains

**What it is.** A vertical waste pipe with water-sealed traps at every fixture, carrying waste away without the smell, and disease vector, of an open drain.
Also covers: cn_trapped_drain.

**Why you'd never guess this.** A soil stack sized too narrow siphons itself, waste flowing down drags the air behind it, and that suction can pull the water seal straight out of every trap on that stack at once, even though the traps themselves are sound. A trap's seal is only a few centimetres of standing water, broken two ways: siphoning, or evaporation from a fixture unused long enough, which is why an occasionally used bathroom can smell of sewage with no plumbing fault, the trap simply dried out. Every fixture needs its own trap, one upstream doesn't protect a fixture connected below it.

**Prerequisites.** Ceramic or lead pipe (prefer ceramic, per cn_aqueduct's caution), correct fall surveyed with the chorobates.

**Roman-available inputs.** Ceramic pipe, lead pipe (avoid for acidic waste), mortar joints.

**Procedure.** Size the main stack generously so falling waste doesn't fill the pipe's cross-section and drag trap seals with it. Fit every fixture with its own trapped bend. Slope every run consistently, no high point trapping air, no low point trapping solids.

**How you know it worked.** No sewer smell at any fixture after normal use; an unused fixture is flushed periodically to keep its trap wet.

**Failure modes.** An undersized stack siphoning many trap seals at once; an unused trap drying out; one untrapped fixture undermining every trap elsewhere.

**Cost & labour.** MEASURED order of magnitude, well within Roman pipe-laying, the gap is technique, not material.

**Danger.** Sewer gas exposure is unpleasant and hazardous in confined poorly ventilated spaces.

**Confidence: HIGH**, straightforward hydraulics within Roman material capability.

### cn_fire_escape - Fire escape and automatic sprinklers

**What it is.** Getting people safely out of a burning multi-storey building, and suppressing fire automatically before it spreads.
Also covers: cn_sprinkler.

**Why you'd never guess this.** A fire escape is only as good as its worst point: stairs that can be obstructed or locked defeat the whole purpose at the one moment it matters, and a pivoting ladder section can itself jam at the hinge, a real historical cause of fire escape deaths unrelated to the fire. A sprinkler's thermal element, historically a soldered joint, must melt reliably at a set temperature, but that solder plug can be damaged in installation and fail to melt later, or fail the other way and trigger falsely; the system is also only as good as its water pressure reaching the most distant nozzle, not just the nearest.

**Prerequisites.** cn_wrought_iron_girder-scale iron for stairs and piping, a reliable fusible alloy for the thermal element, `85_transport_civil.md#water_supply_sanitation`-level pressurised supply.

**Roman-available inputs.** Iron is reachable once bulk supply exists; a tuned fusible alloy is a small metallurgy problem, tin-lead-bismuth alloys are known in principle but untested for this melting point.

**Procedure.** Keep escape stairs permanently unobstructed and unlockable from inside, by policy as much as design, test pivoting sections regularly for a seized hinge. Sample-test thermal elements to destruction to confirm the rated melting temperature, and verify pressure reaches the most distant nozzle.

**How you know it worked.** Escape sections deploy freely under a supervised test; sample sprinkler heads trigger at rated temperature, none trigger falsely at room temperature over long observation.

**Failure modes.** A locked or obstructed escape, useless when it matters most; a seized hinge trapping people mid-escape; a damaged solder plug that never melts; inadequate pressure at distant nozzles, false confidence in a half-working system.

**Cost & labour.** ESTIMATED, moderate for iron stairs once bulk iron exists, a smaller but real development effort for a tested fusible alloy.

**Danger.** Fire is the obvious danger; the equipment's own failure modes are a second layer, since people trust it and stop looking for another way out.

**Confidence: MEDIUM-HIGH** on mechanics; **LOW** on near-term reachability.

### cn_terrazzo - Terrazzo floor finish

**What it is.** A floor of stone chips set in binder, ground flat and glossy, a marble-like finish at a fraction of solid marble's cost and weight.

**Why you'd never guess this.** The binder's set state matters more than the recipe: aggregate size and binder porosity must match so the surface grinds to a stone-wide sheen without pulling chips loose; an under-fired binder stays too soft and yields to the abrasive before the chips do, while an over-fired, over-hard binder tears the chips out instead of grinding evenly with them.

**Prerequisites.** cn_mortar or cn_gypsum_plaster as binder, cn_stone_polish's grinding skill, marble chip waste.

**Roman-available inputs.** Marble chip waste from any workshop, lime or gypsum binder, emery for grinding, all already Roman, this is very nearly reachable already, mostly missing the deliberate combination.

**Procedure.** Set chips into a binder bed over a solid base, let it cure to a firmness matched by test to the chip hardness, then grind flat with progressively finer abrasive until a continuous polish emerges across both.

**How you know it worked.** A smooth continuous polish across chips and binder, no chips pulled loose or standing proud.

**Failure modes.** Binder too soft, uneven gouging around firm chips; binder too hard, chips tear free leaving pits.

**Cost & labour.** ESTIMATED, modest, uses waste Rome already discards.

**Danger.** Grinding dust over long exposure is a lung hazard, the usual stone-trade caution.

**Confidence: MEDIUM-HIGH**, materials and skills already Roman, only the combination is new.

---

## Sources and confidence

Roman baseline claims (arch, vault, pozzolana concrete, aqueduct, crane, surveying) are HIGH confidence, from Vitruvius's *De Architectura*, Frontinus's *De Aquaeductu*, and surviving structures; see `85_transport_civil.md` for the fuller citation trail this module deliberately doesn't repeat. Beam theory, truss mechanics, cast/wrought iron tension behaviour, reinforced and prestressed concrete's thermal-expansion coincidence, and suspension bridge aerodynamics are HIGH confidence on the physics, textbook materials science backed by well documented historical collapses. Portland cement chemistry and clinkering temperature are HIGH confidence, MEASURED figures from modern manufacture. Caisson disease's mechanism is HIGH confidence, well established medically. Anything marked LOW confidence in this module is LOW specifically on Roman-era reachability, not the underlying physics, which is not in doubt; the gating items are almost always bulk iron and steel tonnage (`10_metallurgy.md`) and continuous mechanical power (`40_power_precision.md`), not missing scientific insight. No number here is invented; every figure is tagged MEASURED, DERIVED, or ESTIMATED with its basis stated.

## Where to go next

- `85_transport_civil.md` for what Rome's civil engineering already does well, the freight arithmetic deciding where to build first, and the `structures_iron_steel`, `concrete_and_cement`, `surveying_precision`, and `water_supply_sanitation` entries this module builds on.
- `10_metallurgy.md` for the blast furnace, finery forge, and cementation/crucible steel chain gating nearly every iron and steel item here, from cast iron beams to suspension bridge cable.
- `40_power_precision.md` for the continuous mechanical power gating rotary cement kilns, concrete mixers, powered cranes, and mechanical ventilation.
