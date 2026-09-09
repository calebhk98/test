# Module 87: Construction Engineering

Say the honest thing first, because a builder who has raised the Pantheon's dome will stop listening the moment you patronise him. Rome already has hydraulic concrete that cures underwater and gets stronger for decades. Rome already has the true arch and the groin vault, and has used them to bridge valleys and roof bath halls wider than anything built again for a thousand years. Rome already has the groma and the chorobates and a corps of military engineers who can lay a camp, a road, and a siege ramp to a standard modern armies would recognise. If your plan for this module is "teach Romans to build," burn it. You have nothing to teach them there.

What Rome does not have is four things, and every one of the 101 items below is one of those four things or a machine built to deliver one of them. First: a cement that behaves the same on the hundredth batch as the first, because Roman pozzolana concrete is excellent but its quality rides on which shore the ash came from and how the mason's eye judged the mix that morning. Second: iron, and later steel, doing useful work in tension, because Rome has plenty of wrought iron for cramps and dowels but no cast iron in the West, no crucible steel of its own, and nothing like the tonnage a load-bearing frame needs. Third: the theory of the beam, meaning the mathematics that tells you *why* a proportion worked, not just that it worked last time, so you can change the span without rebuilding a failure to find the new limit. Fourth: the machinery of scale, cranes and mixers and pumps and shafts that let ten men do what previously needed a thousand, mostly because it needs continuous mechanical power Rome has only in trickle amounts (see `40_power_precision.md`). Everything from cast iron beams to skyscraper frames to sewage traps below is downstream of solving one of those four. Fix them roughly in that order and the rest of this module is carpentry.

---

### cn_pozzolana_concrete - Pozzolana hydraulic concrete (*opus caementicium*)

**What it is / why you want it.** The concrete Rome already makes: quicklime plus volcanic ash sets underwater and keeps gaining strength for decades. This entry exists to give the tech tree a node, not to teach it.
Also covers: cn_mortar.

**Why you would never guess this.** Nothing here is non-obvious to a Roman. What is non-obvious to a modern visitor is that this is not a lesser Portland cement, it is chemically different and, for marine work, arguably better; see `85_transport_civil.md#concrete_and_cement` for the full account.

**Prerequisites.** Lime burning (routine), pozzolana access, formwork carpentry.

**Roman-available inputs.** *Calx* (quicklime, any limestone district), *pulvis puteolanus* (pozzolana, Bay of Naples, and other volcanic ash from Campania), *caementa* (rubble aggregate), fresh water. Plain lime mortar (no pozzolana) is the everyday binder for ordinary walling everywhere lime is burned.

**Procedure.** Slake the quicklime, mix with pozzolana and rubble roughly by Vitruvius's ratios (II.6, attributed, verify by testing your own ash), pack into formwork, cure weeks to years. The one genuine improvement available now, without any new chemistry: cast a labelled test cylinder from every batch, crush a matched cylinder at fixed intervals with known stone weights, and keep a written log. No Roman source shows this being done systematically.

**How you know it worked.** A month-old test cylinder resists a load your log predicts within a small margin; an opened underwater section is uniform and rings hard when struck, not crumbly.

**Failure modes.** Weak or wrong ash gives a soft set that never fully hardens. Batch-to-batch variation, invisible without testing, means one bad wall in ten looks identical to the other nine until it fails decades later.

**Cost & labour.** DERIVED: testing costs one attentive foreman and a wax tablet, nothing else.

**Danger.** Slaking lime burns skin and eyes on contact, wash immediately with water. No social danger.

**Confidence: HIGH** on the chemistry and Roman practice.

### cn_quarrying_wedge - Stone quarrying with wedges

**What it is / why you want it.** Splitting stone along a chosen plane instead of fracturing it at random, which is what makes squared building block possible at all.
Also covers: cn_stone_saw, cn_stone_polish, cn_gang_saw.

**Why you would never guess this.** Also nothing here for a Roman; every legionary quarry and every marble yard at Carrara and Docimium already runs this way.

**Prerequisites.** Iron wedge and mallet, a reader of the stone's grain.

**Roman-available inputs.** Iron wedges (*cunei*), sometimes dry wood wedges swollen with water in a pinch, emery (Naxos) for polishing, sand and water for sawing, since the blade itself never touches the cut, the abrasive does the work and the blade is only a guide.

**Procedure.** Mark a line of holes along the natural bedding or a chosen split plane, drive wedges in sequence not all at once, listen for the pitch change that says the crack is running true. For sawing, drag an iron blade with wet sand under it back and forth; for polishing, work down through progressively finer emery grits by hand. Gang saw is the one genuine addition Rome lacks in practice, several parallel blades in one frame, water or slave-powered, cutting a whole block into slabs at once instead of one saw at a time; the hard part is keeping every blade cutting at the same rate, since one that binds ruins the block.

**How you know it worked.** The split face is flat and follows your marked line, not a random fracture surface.

**Failure modes.** Wedges struck out of sequence split the block wrong. A gang saw with unequal blade tension warps or binds mid-cut, wasting the whole slab.

**Cost & labour.** MEASURED order of magnitude: a skilled quarryman splits a modest building block in under a day; a large obelisk blank is a season's project with dozens of men, as Aswan's evidence shows.

**Danger.** Flying stone chips, crushed fingers, collapsing quarry faces. No social danger, quarrying is a normal state and private industry.

**Confidence: HIGH.**

### cn_true_arch - True arch in stone (*fornix*)

**What it is / why you want it.** Compression-only load path around an opening, letting stone (strong in compression, weak in tension) span without ever bending.
Also covers: cn_groin_vault, cn_ribbed_vault, cn_flying_buttress.

**Why you would never guess this.** Also already Roman, extensively. What is missing is not the arch, it is a way to *calculate* the safe thickness instead of copying a proportion (span-to-thickness ratios that worked at the Colosseum) into a bigger arch where the same ratio quietly fails. The line of thrust, the true path the compression takes through the masonry, must stay inside the stone at every point; nobody in 100 AD can compute that curve, they can only build conservatively thick and watch what stands.

**Prerequisites.** `cap_tol_1mm` stonecutting tolerance, cn_quarrying_wedge, centring carpentry to hold voussoirs until the keystone locks.

**Roman-available inputs.** Cut stone voussoirs, or Roman concrete cast over a wood centring and then the centring struck once cured, brick ribs (as used at the Pantheon).

**Procedure.** Rome already does this at scale. The two genuine additions: (1) the groin vault (two barrel vaults crossing at right angles) concentrates load onto four corner points instead of two continuous walls, already Roman practice, extend it deliberately to free up wall space for windows; (2) the ribbed vault, building the diagonal ribs first as a light stone skeleton, then filling thin webs between them, which is lighter and lets you see the load path by eye, a medieval refinement Rome can reach by simply building the ribs as temporary formwork for the web instead of one solid shell; (3) the flying buttress, an arch that leaps outward from a high wall to a free-standing pier, taking the vault's outward thrust away from the wall entirely so the wall itself can be thin and full of glass, useful only once a building wants tall thin walls, which Roman basilicas mostly do not.

**How you know it worked.** Struck centring, the arch stands with no visible sag; a straightedge across the underside shows no deflection after a year.

**Failure modes.** Thrust escaping the masonry at the haunches, causing a crack pattern like a hinge; ribbed vault webs poured before the ribs have set, collapsing the whole skeleton; flying buttress abutment too small, which simply pushes the pier over.

**Cost & labour.** ESTIMATED, scales with span cubed roughly; a modest ribbed vault bay is weeks of masons, a cathedral-scale nave is a generation's project as European history shows.

**Danger.** Falling centring timber and collapsing partial vaults kill masons; this is the single most dangerous trade in this module.

**Confidence: HIGH** on Roman baseline, **MEDIUM** on ribbed/buttress transfer without any calculus, since it was in fact built that way historically by trial, injury, and accumulated craft rule.

### cn_crane_treadwheel - Treadwheel crane (*polyspastos*)

**What it is / why you want it.** A man-powered drum crane, already Roman, that raises several tonnes with a handful of men walking inside a wheel.
Also covers: cn_block_tackle_hoist.

**Why you would never guess this.** Not non-obvious, Vitruvius describes it (*De Architectura* X). What is worth stating is the arithmetic: mechanical advantage equals the number of rope parts under load, minus 10 to 20 percent lost to friction in the sheaves (ESTIMATED, basis: typical block friction losses in wooden-sheave tackle).

**Prerequisites.** Rope (hemp), timber, bronze or iron sheave bearings.

**Roman-available inputs.** Hemp rope, seasoned timber, bronze pulley wheels.

**Procedure.** Rig a rope through multiple pulley blocks; each additional rope part shares the load, so a five-part tackle needs roughly a fifth the pulling force for the same weight, less the friction tax. A treadwheel converts men walking on the inside of a large wheel into that pulling force, using their body weight rather than arm strength, which is why a handful of men can lift several tonnes.

**How you know it worked.** Load rises smoothly; if the rope creeps or slips on a sheave, the groove is worn smooth or wet, replace or dress it.

**Failure modes.** Rope slip on worn sheaves; overloading a single rope part beyond its breaking strength snaps it without warning, dropping the load.

**Cost & labour.** MEASURED order of magnitude, attested at multiple-tonne column and obelisk lifts across the Empire.

**Danger.** A snapped rope or a wheel operator caught inside a wheel that overruns kills. Socially unremarkable, a normal construction trade.

**Confidence: HIGH.**

### cn_scaffolding - Timber scaffolding system

**What it is / why you want it.** A temporary timber platform that lets masons work at height, already routine Roman practice on any tall building.

**Why you would never guess this.** Obvious once you want it. The one non-obvious point: lashing discipline, not lumber, is what actually holds a scaffold together, one untied joint at the wrong point can unravel a whole bay under load.

**Prerequisites.** Timber poles, rope or withies for lashing.

**Roman-available inputs.** Fir or pine poles, hemp rope or green withy for lashing.

**Procedure.** Erect vertical standards, tie horizontal ledgers at working-height intervals, brace diagonally, and never trust a single lashing to carry a joint alone, double it. Inspect for creep (visible sag under load) daily.

**How you know it worked.** No visible sag under a loaded plank; a hard shove doesn't rack the frame sideways.

**Failure modes.** A single failed lashing propagates, since load redistributes suddenly onto neighbouring ties which were not sized for it.

**Cost & labour.** MEASURED as a normal minor cost line on any Roman building project.

**Danger.** Falls are the main hazard of the whole construction trade; workers visibly fear a scaffold that deflects, and they are right to.

**Confidence: HIGH.**

### cn_aqueduct - Masonry aqueduct arch bridge (*aqua ducta*)

**What it is / why you want it.** Carrying a level water channel across a valley on an arcade, already Roman practice at enormous scale, nine lines feeding Rome by Frontinus's survey.
Also covers: cn_siphon, cn_sewer_system, cn_water_main.

**Why you would never guess this.** Also not non-obvious to Rome. Worth stating precisely: the channel gradient must stay nearly constant, water pressure in an open channel is static per section, not dynamic, so a single arch's failure among dozens is locally catastrophic but the rest of the line survives, unlike a single point of failure in a pressurised pipe.

**Prerequisites.** cn_true_arch, chorobates levelling (see `85_transport_civil.md#surveying_precision`), lead or ceramic pipe for final runs.

**Roman-available inputs.** Cut stone and concrete arcading, lead pipe (*fistulae plumbeae*) or the safer earthenware pipe (*fistulae fictiles*, Vitruvius's own preference) for pressurised siphon crossings, ceramic sewer pipe.

**Procedure.** Level a gentle continuous fall with the chorobates, arcade across valleys too deep to fill, drop into an inverted siphon (a sealed pipe running down into the valley and back up, driven by the head of water behind it) where an arcade would be absurdly tall, and gravity-drain waste through sloped sewer pipe (Cloaca Maxima being the standing proof of scale). A siphon must stay entirely full and sealed, any trapped air pocket stops the flow dead, and sediment collects at the low point and must be periodically flushed.

**How you know it worked.** Continuous flow at the delivery end matching the intake, no air hammering in the siphon pipe.

**Failure modes.** A single arch failure drops the channel locally; an air lock in a siphon halts the whole line until purged; unflushed sediment eventually chokes a main.

**Cost & labour.** MEASURED, Rome's own aqueduct system is the evidence; a full line is a state-scale, multi-year project.

**Danger.** Collapsing arcading during construction; lead pipe risk is a slow chronic exposure, avoid boiling acidic liquids in it (see `85_transport_civil.md#water_supply_sanitation`), not an acute one.

**Confidence: HIGH.**

### cn_portland_cement - Portland cement powder (*no ancient term*)

**What it is / why you want it.** A binder fired hot enough to *clinker*, not merely calcine, giving a strength and consistency pozzolana concrete cannot match batch to batch.
Also covers: cn_rotary_cement_kiln, cn_cement_clinker_grinding, cn_gypsum_plaster, cn_artificial_stone.

**Why you would never guess this.** The word "cement" tricks a modern visitor into thinking this is what Rome already has. It is not. Lime burning calcines limestone around 900-1000 C, driving off carbon dioxide. Portland clinker requires roughly 1450 C, hot enough that the raw meal partially melts and recombines into new mineral compounds (calcium silicates) that pozzolana concrete never forms. This is a different kiln, a different fuel budget, and a different furnace design, not a stronger version of the old one. And the grinding afterward matters almost as much as the firing: unground clinker is nearly inert, only fine grinding exposes enough surface area to hydrate fast.

**Prerequisites.** `cap_heat_1600` furnace capability (roughly matching `10_metallurgy.md#high_temp_furnace`), limestone and clay quarrying, a mechanical grinding mill (water or animal powered, see `40_power_precision.md#water_power_scaleup`).

**Roman-available inputs.** Limestone (everywhere lime is already burned), clay (any brickyard), gypsum (Cyprus, Sicily, widely traded already as *gypsum* for plaster) added at grinding to control set speed.

**Procedure.** (1) Grind limestone and clay roughly 4:1 by mass (ESTIMATED, standard modern raw-mix ratio, not a Roman-attested figure) into a wet slurry. (2) Feed the slurry into a rotary kiln, a long slightly tilted cylinder turning 1-3 rpm so material tumbles slowly toward the hot end; flame temperature at the firing end must reach roughly 1800 C to hold the material at 1450 C, and refractory lining must survive that heat without slumping. (3) The output, clinker, is dark grey, glassy, pea to walnut sized nodules; quench and cool it. (4) Grind the clinker fine in a ball mill with a small amount of gypsum (a few percent) to slow the set to a workable hour or two instead of minutes; grinding heats the mill, and overheated cement begins hydrating inside the mill itself, ruining it, so cooling during grinding is essential. Gypsum plaster is a separate, easier product: calcine gypsum gently (under 200 C, far below clinkering) and it sets in minutes when wetted, useful for fast interior finishing but useless outdoors, it dissolves in rain. Cast artificial stone is simply Portland concrete poured into reusable moulds to mimic dressed masonry, saving quarrying labour at the cost of mould-making and slower curing per piece.

**How you know it worked.** Clinker rings when struck and does not slake or crumble in water the way underburned lime does; ground cement mixed with water sets hard within hours and gains most of its strength within a month, testable the same way as pozzolana, cast cylinders, logged loads.

**Failure modes.** Underfired clinker (too cool, or fed too fast) stays soft and chalky, useless. Overground, overheated cement in the mill "flash sets" before it ever reaches the site. Wrong gypsum dose gives either a set so fast you cannot place it or one so slow the site stalls.

**Cost & labour.** ESTIMATED as a major standalone industrial project: a purpose-built kiln, a fuel supply far beyond ordinary lime burning, and a grinding mill needing continuous mechanical power. Not a near-term craft project; treat as a generation-scale industrial commitment.

**Danger.** Kiln burns, refractory collapse at the hot end, silicosis-type lung damage from clinker dust over years of grinding work without protection. No social danger, cement making reads as an ambitious but legitimate industrial venture.

**Confidence: HIGH** on the chemistry and temperatures, **LOW** on any near-term Roman timeline; this is explicitly the far end of a long branch, not a first project.

### cn_post_lintel - Post and lintel structure, the theory of the beam

**What it is / why you want it.** The plain beam across two supports, and, more valuably, the mathematics of *why* it holds or breaks, which nobody in 100 AD possesses even though everybody in 100 AD builds beams.
Also covers: cn_cantilever.

**Why you would never guess this.** This is the real non-obvious kernel of the whole module. A beam under load bends; the top fibre shortens (compression) and the bottom fibre stretches (tension), with a neutral plane between them carrying no stress at all. Stone and cast material are strong in compression and weak in tension, so a stone or plain-concrete beam always fails from the bottom up, a crack starting on the underside at midspan, invisible until it is most of the way through. A Roman mason knows empirically that a thicker beam spans further and that stone beams should stay short; he does not know that deflection scales with the *cube* of the span, so a beam twice as long sags eight times as much for the same load, which is why doubling a proportion that worked at one scale fails badly at twice the scale. This single relationship, correctly used, is why post-Roman engineers eventually stop copying old ratios and start calculating new ones; incorrectly ignored, it is why every "just make it bigger" bridge and roof in this module's failure list actually failed. A cantilever, a beam fixed at one end and free at the other, makes the problem worse: it has no support to redistribute load to, so its fixed end carries the full bending moment, and a short-looking overhang can already be close to its limit, since the deflection-cubed relationship punishes any added length hardest right where you can least see it.

**Prerequisites.** `cap_tol_1mm`, timber or dressed stone.

**Roman-available inputs.** Seasoned oak or fir beams, dressed stone lintels, iron cramps to tie lintel to post where Rome already does so.

**Procedure.** For any beam, keep material where the calculation (even an empirical, tested-to-failure calculation, not a formal one) says tension will occur, and never rely on a material weak in tension to carry a span longer than proportions already tested to failure. For a cantilever, treat the fixed end as the single critical section and never extend it past a length you have tested a matching sample to destruction on first.

**How you know it worked.** A loaded test beam, taken to visible sag but not failure, springs back close to straight when unloaded; permanent set (a beam that stays bent) means you are near the limit and must not build that span again without more material.

**Failure modes.** Bottom-fibre cracking in stone or plain concrete beams, invisible from above; cantilevers extended past a tested length that fail suddenly with almost no warning sag, since brittle materials give little visible deflection before snapping.

**Cost & labour.** ESTIMATED, testing to failure costs one destroyed sample per span you have not already proven, cheap insurance against a building-scale failure.

**Danger.** Sudden, unannounced collapse, the single most dangerous property of any beam in tension-weak material. No social danger; beam-testing reads as ordinary engineering caution.

**Confidence: HIGH** on the physics, textbook and well attested; **HIGH** on Roman-era ignorance of it as formal theory, MEDIUM on how much was captured as informal craft rule.

### cn_king_post - King post roof truss

**What it is / why you want it.** A triangular timber frame that converts a roof's bending problem into pure tension in some members and pure compression in others, spanning further than a single beam of the same timber ever could.
Also covers: cn_queen_post, cn_timber_truss, cn_trussed_arch.

**Why you would never guess this.** Wood is strong in both tension and compression along the grain, but weak in bending over a long unsupported length, exactly the beam problem above. Triangulate it, put a central post in pure compression and two rafters and a tie beam in a closed triangle, and every member works in the direction wood is strongest, at the cost of needing every joint to actually hold, since a truss is only as good as its worst connection.

**Prerequisites.** cn_post_lintel (the beam problem this solves), joinery skill, iron strap or bolt for tie joints.

**Roman-available inputs.** Seasoned timber, iron straps and pins for critical joints, since a mortise-and-tenon alone can creep under sustained load.

**Procedure.** A king post truss uses one central vertical post from the tie beam to the roof apex, suited to narrow spans; a queen post uses two posts set inward from the ends, shortening the unsupported length of the tie beam and reaching wider spans at the cost of trickier geometry. A general timber truss extends this triangulation with more members for still wider roofs. A trussed arch bolts timber bracing onto a stone or masonry arch specifically to resist the arch's outward spreading force at points the masonry alone would need to be far thicker to resist, letting a thinner arch stand.

**How you know it worked.** No visible sag at the ridge after full seasonal load (snow, wind) has been carried at least once; joints show no daylight gap opening under load.

**Failure modes.** A single joint that slips lets the whole triangle rack out of shape, and because failure is progressive rather than sudden in timber, watch for a truss that visibly sags more each year, it is failing slowly and will eventually go quickly.

**Cost & labour.** MEASURED order of magnitude from surviving Roman and later timber roof spans, days to weeks of carpenter labour per bay depending on span.

**Danger.** Falling roof timbers during erection; a truss that fails in service can bring down the whole roof at once, more dangerous than a beam because more area is at risk from one failure.

**Confidence: HIGH** on the triangulation principle; **MEDIUM** on exact Roman-attested truss geometry, since surviving evidence is indirect.

### cn_cast_iron_beam - Cast iron beam

**What it is / why you want it.** A beam cast in iron instead of cut in stone or timber, far stronger in compression than either, and the first item in this module where the missing input is not calculation but the metal itself.
Also covers: cn_iron_column.

**Why you would never guess this.** This is the classic killer, and you must not build one without knowing it: cast iron is strong in compression but brittle and much weaker in tension, roughly a third to half its compressive strength depending on the casting (ESTIMATED, basis: known historical ratios for grey cast iron), and it gives almost no warning before it snaps, unlike timber which visibly sags first. Recall from cn_post_lintel that a beam's bottom fibre is in tension. A cast iron beam is therefore weakest exactly where a builder's instinct, trained on stone, says thickness should matter least. Iron columns are the opposite case done right: a column is in pure compression, cast iron's strength, which is why hollow cast iron columns genuinely work well and cast iron beams genuinely do not; the same metal is excellent in one orientation and treacherous in the other.

**Prerequisites.** Cast iron supply, meaning `10_metallurgy.md#blast_furnace_cast_iron`, which Rome does not have in the West (bloomery iron only produces wrought iron, never molten cast iron), plus cn_post_lintel's beam theory to know where the danger sits.

**Roman-available inputs.** None directly; this whole entry is gated on the blast furnace tree in `10_metallurgy.md`. Once cast iron exists: sand moulds, a foundry, pig iron remelted in a cupola or reverbatory furnace.

**Procedure.** For a column: cast a hollow cylindrical section, since a hollow section resists buckling nearly as well as solid for far less weight, and load it only in pure axial compression, never off-centre. For a beam: never use plain cast iron where wrought iron or steel can be substituted; if you must, make the section deepest and thickest at the tension (bottom) face specifically, cast to a design already tested to failure at smaller scale, and never trust a cast iron beam under sudden or shock loading, since brittle fracture initiates from any internal casting flaw, and every casting has some.

**How you know it worked.** A column carries its rated load with no visible deformation; there is no reliable visual warning sign for an overstressed cast iron beam before it fails, which is exactly the danger.

**Failure modes.** Sudden brittle fracture with no warning sag, the historical cause of multiple 19th century bridge and mill floor collapses; hidden casting flaws (blowholes, cold shuts) that halve real strength versus the design assumption.

**Cost & labour.** ESTIMATED, gated entirely on bulk cast iron output existing first; treat as a mid-tree project, not a first casting.

**Danger.** Sudden structural collapse with no warning, the single deadliest failure mode in this entire module. Socially, once cast iron beams gain a reputation for unexplained collapse, expect real reluctance from any patron who has heard of one.

**Confidence: HIGH** on the tension/compression asymmetry, textbook and historically proven at great cost; **MEDIUM** on exact strength ratios, which vary with casting quality.

### cn_wrought_iron_girder - Wrought iron plate girder, and later steel

**What it is / why you want it.** Getting iron to actually work in tension, which cast iron cannot reliably do, first with wrought iron (fibrous, ductile, ten times more tolerant of flaws than cast iron) and then with cheap bulk steel once the finery-forge-to-crucible chain in `10_metallurgy.md` is running.
Also covers: cn_rolled_I_beam, cn_plate_girder, cn_box_girder, cn_steel_frame_skeleton.

**Why you would never guess this.** The obvious move after cast iron beams fail is "use more iron." The correct move is "use a different iron": wrought iron's fibrous grain structure, from repeated forging and folding, lets it deform visibly before it breaks, giving warning a cast iron beam never gives. Riveted wrought iron plate girders are flexible, not stiff, they visibly bend under load and spring back, which is a feature, not a flaw, since it is your warning system. Rolling instead of riveting plate together into a single I-shaped section is more efficient, but needs a rolling mill that can heat and squeeze the whole cross-section through shaped rollers in one pass, energy-intensive and hard on the roll dies. A box girder (a closed rectangular or trapezoidal tube) resists twisting far better than an open I-section, since an open section has almost no torsional stiffness at all, only a closed loop does; welding the box shut is expensive but is what makes long, twist-resistant spans possible. A full steel frame skeleton, once steel is cheap and reliable, moves all structural load into a steel grid so walls become weathertight skin only, not load-bearing, the change that eventually makes tall buildings possible.

**Prerequisites.** `10_metallurgy.md#finery_forge` for wrought iron; `10_metallurgy.md#cementation_steel` and `crucible_steel` for the small-batch steel that must exist before bulk steel is worth pursuing; rolling requires `40_power_precision.md#water_power_scaleup` or later steam power to turn heavy rolls continuously.

**Roman-available inputs.** Bloomery wrought iron bar (already routine, but only in small quantities per bloom, nowhere near structural tonnage), charcoal fuel.

**Procedure.** Forge and hammer-weld wrought iron plates into a built-up girder, riveted (see cn_riveted_connection) with the web deep for stiffness and the flanges (top and bottom edges) thickest, since flanges carry the bending, the web mainly carries shear (sideways sliding force). Once rolling capacity exists, roll a single I-shaped bar instead of building one up from plates, faster and stronger per unit weight, but requires heating the whole billet to rolling heat and passing it through progressively shaping rolls without tearing. Close an I or plate girder into a box by welding or riveting a second web and both flange edges shut, if the span must resist twisting (a curved bridge, a deck carrying off-centre traffic). A steel frame skeleton stacks columns and beams into a rigid three-dimensional grid, with walls hung on the outside afterward.

**How you know it worked.** A plate girder deflects visibly and predictably under test load, then returns to true when unloaded; a box section resists twisting by hand that an equivalent open I-section does not.

**Failure modes.** Rivets sheared by vibration loosen a girder over years, invisible until a joint finally slips; an open I-section used where torsion is significant twists and eventually buckles; a rolling mill fed too cold tears the billet instead of shaping it.

**Cost & labour.** ESTIMATED, entirely gated on bulk wrought iron and then steel output; a single riveted girder is weeks of forge work even with iron on hand.

**Danger.** Rivet failure under load, hot metal burns during forging and rolling. No unusual social danger once iron framing is an established trade.

**Confidence: HIGH** on the tension/ductility argument; **LOW** on near-term Roman timelines, gated deep in the metallurgy tree.

### cn_pratt_truss - Pratt truss, and the iron-age truss family

**What it is / why you want it.** Once iron reliably holds tension, truss diagonals can be thin tension members instead of thick timber struts, cutting the weight of a long-span truss dramatically.
Also covers: cn_warren_truss, cn_lattice_truss, cn_space_frame.

**Why you would never guess this.** A timber king post truss (cn_king_post) puts its diagonals in compression because timber joints handle compression better than tension. An iron-age truss deliberately inverts this: in a Pratt truss the diagonals run in tension and the verticals in compression, which lets the diagonals be thin iron rods instead of heavy timber struts, since a tension member never buckles the way a compression member does, so it can be far slimmer for the same strength. A Warren truss removes the verticals entirely and uses consistent 45-degree diagonals alternating tension and compression, the most material-efficient shape if the geometry is laid out precisely, but precision is exactly what the geometry demands, an inconsistent angle wastes the efficiency. A lattice truss crosses many thin diagonals to save weight at midspan while keeping full depth, at the cost of many more joints, each one a possible weak point that will not announce itself before it fails. A space frame extends triangulation into three dimensions at once, extremely light for its span, but every joint must carry load from several directions simultaneously, making the joints themselves the whole design problem.

**Prerequisites.** cn_wrought_iron_girder or steel supply, cn_riveted_connection or cn_bolted_connection for joints, cn_post_lintel's beam theory.

**Roman-available inputs.** None beyond ordinary iron bar stock, once bulk iron exists; the design principle itself needs no new material, only the willingness to put iron in tension deliberately.

**Procedure.** Lay out the truss geometry precisely before fabrication, since these forms depend on angle for their efficiency, not on oversized members compensating for sloppy angles; size diagonals in tension for the load path calculated (or, absent formal calculation, tested at model scale first) and verticals or compression diagonals heavy enough not to buckle, which for a slender iron member happens well below its crushing strength, a separate failure mode from crushing entirely.

**How you know it worked.** A loaded test truss deflects a small, predictable amount at midspan and returns to true; no joint shows visible slip.

**Failure modes.** A single failed joint in a lattice or space frame redistributes load onto neighbours that were not sized for the extra share, a chain failure; compression members buckling sideways rather than crushing, a mode invisible until the member is already curved.

**Cost & labour.** ESTIMATED, precise geometry costs surveying and fabrication time up front but saves material weight overall.

**Danger.** Progressive chain-failure collapse once one joint goes. No unusual social danger.

**Confidence: HIGH** on the tension/compression logic, well documented from the historical truss-bridge era.

### cn_riveted_connection - Riveted joint, bolted, welded, and gusseted

**What it is / why you want it.** How you actually join iron and steel members, since a beam or a truss is worthless if its joints are its weak point, which they usually are.
Also covers: cn_bolted_connection, cn_gusset_plate, cn_welded_connection.

**Why you would never guess this.** A rivet is not just a metal pin, it is heated red hot, dropped through aligned holes in the two plates, and hammered flat on both ends while still hot; as it cools it contracts and clamps the plates together under real tension, which is where the joint's strength actually comes from, not from the pin filling the hole. A bolted connection instead relies on thread accuracy and how hard the nut is turned, weaker per fastener than a good rivet but far faster to assemble and, critically, removable. An electric arc weld, much later technology, can be as strong as the parent steel if cooled slowly, but cooled too fast it forms brittle martensite (a hard, crack-prone crystal structure) right at the joint, meaning weld quality depends entirely on technique, speed, angle, and heat input, not just on having the equipment. A gusset plate is simply a flat steel plate bolted or riveted across a joint to spread force along a stiffer path than the members alone provide, but overloading a gusset with too many rivets concentrates stress at the hole pattern instead of relieving it.

**Prerequisites.** cn_wrought_iron_girder or steel supply, a forge for rivets, for welding: `10_metallurgy.md` alloy steel understanding plus a reliable electric arc, itself gated on `50_electricity.md`.

**Roman-available inputs.** Iron rod stock for rivets and bolts, a forge, tongs, hammers.

**Procedure.** Heat a rivet to a bright orange-yellow, drop through the aligned hole, hammer the protruding end flat against a heavy backing bar (a "dolly") before it cools past a dull red, working fast since the clamping force comes entirely from cooling contraction. For bolts, cut matching threads accurately (a screw-cutting lathe, `40_power_precision.md#screw_cutting_lathe`, is what makes consistent threads possible at all) and torque by feel or a calibrated wrench; expect loosening under vibration unless a lock washer or a second jam nut is used. For welding, keep the arc moving at a steady rate, matched to plate thickness, and let the joint cool slowly, wrapped or shielded, never quenched.

**How you know it worked.** A cooled rivet head is tight against the plate with no gap a thin blade can slip under; a bolted joint does not loosen after a hard shake test; a weld bead is smooth, not pitted or cracked when tapped with a hammer.

**Failure modes.** A rivet driven cold never develops clamping force and works loose under vibration; an over-torqued bolt snaps its thread; a rushed weld cracks along the heat-affected zone months later under repeated load.

**Cost & labour.** MEASURED for riveting, one rivet is minutes of skilled hammer work, a large bridge needs many thousands; DERIVED for bolting, faster per joint but needs precision thread-cutting capacity first.

**Danger.** Hot rivet work burns; a snapped bolt or failed weld under load can release stored force violently. No unusual social danger.

**Confidence: HIGH** on riveting and bolting, well attested; **MEDIUM** on welding, since it is gated on electrical capability this tree may not yet have.

### cn_reinforced_concrete - Reinforced concrete slab and beam

**What it is / why you want it.** Concrete cast around steel bars so the steel carries the tension a plain concrete beam cannot, giving flat slabs and beams plain concrete or plain stone can never achieve.
Also covers: cn_deformed_rebar, cn_precast_panel.

**Why you would never guess this.** This is the second real kernel of the whole module, stated exactly as it should be stated: reinforced concrete works at all only because steel and set concrete happen to expand and contract with temperature at nearly the same rate, roughly 10-14 millionths per degree Celsius for both (MEASURED, a modern materials property, unverifiable to a Roman without precision thermal measurement). If they did not match, every summer-to-winter cycle would peel the bond apart at the interface, and the whole technology would be a curiosity, not a building method. Nobody engineered this match, it is a coincidence of what iron oxide and silicate rock happen to do when heated, and reinforced concrete exists because of it. The second non-obvious point, equally important: the steel must go exactly where the tension is, which for a simple beam resting on two supports is the *bottom*, and for a beam continuous over a support is the *top* at that support, since the bending direction reverses there. Put the steel on the wrong face and you have built an expensive, heavy, plain concrete beam that fails exactly like one, because the steel sitting in the compression zone does almost nothing.

**Prerequisites.** cn_portland_cement or high-quality tested pozzolana (weaker substitute, per the tech tree's own reinforcement/binder trade-off), bulk wrought iron or steel bar, cn_post_lintel's beam theory to know where tension falls.

**Roman-available inputs.** None for bar steel; wrought iron bar can substitute at reduced effectiveness. Concrete side: Roman pozzolana concrete or Portland cement, either works chemically, Portland gives more predictable strength.

**Procedure.** Place steel or iron bar in the formwork exactly along the tension face before pouring, never after; keep enough concrete cover (a few centimetres) over the bar, since concrete's alkaline pore water passively protects steel from rust only as long as it stays fully encased and uncracked. Pour and vibrate concrete around the bars so no voids trap air against the steel. Deformed rebar, bar with ribs rolled into its surface rather than smooth, bonds mechanically to the concrete instead of relying on friction alone, and this bond is what actually transfers load between the two materials; a bond failure is invisible from outside until the beam suddenly deflects or cracks along the bar's length. Precast panels apply the same logic in a factory setting, casting standardised reinforced panels off-site under controlled conditions for better consistency and faster on-site assembly, at the cost of transport expense and the fact that panel-to-panel connections become the weak point instead of the panel itself.

**How you know it worked.** A test beam with steel on the tension face carries a load that snaps an identical unreinforced beam; a cut section shows the bar still fully bonded, with no rust stain bleeding along its length.

**Failure modes.** Rebar placed in the compression zone by mistake, contributing almost nothing; inadequate concrete cover letting the bar rust, and rusting steel expands, which cracks and eventually spalls the concrete off from the inside, a slow failure with no Roman precedent since plain concrete has no embedded metal to corrode; bond failure between deformed bar and concrete, undetectable without destructive testing.

**Cost & labour.** ESTIMATED, gated on cement and bulk steel both existing; DERIVED that this is not a first project, it is a late-tree combination of two other hard-won capabilities.

**Danger.** A wrongly reinforced member can fail suddenly, without the warning cracking that plain masonry usually gives first. No unusual social danger.

**Confidence: HIGH** on the thermal-expansion coincidence and on tension-face placement, both textbook materials science; **LOW** on Roman-era timeline, this is explicitly a late combination technology.

### cn_prestressed_concrete - Prestressed concrete element

**What it is / why you want it.** Stressing the steel before the concrete ever takes load, so the concrete starts in compression everywhere and the bending load only has to cancel that pre-existing compression before it can create any tension at all.
Also covers: cn_post_tensioning.

**Why you would never guess this.** Ordinary reinforced concrete still lets the concrete crack in tension near the bar, the steel then carries the crack's load, which works but limits span and lets water eventually reach the steel through the cracks. Stress the tendon first, either by stretching wire before the pour and releasing it after curing (pre-tensioning) or by threading ducted cable through already-cured concrete and jacking it tight afterward (post-tensioning), and the concrete is squeezed into permanent compression before any service load arrives, letting it stay crack-free under loads that would split ordinary reinforced concrete, and allowing longer, thinner spans for the same material.

**Prerequisites.** cn_reinforced_concrete, high-strength steel wire or cable (ordinary bar stretches too much to hold useful stress), a hydraulic jack able to apply large, controlled tension.

**Roman-available inputs.** None; needs both bulk high-strength steel wire (see cn_wire_cable_spinning) and hydraulic jacking capability well beyond Roman hydraulics.

**Procedure.** For post-tensioning specifically: cast the concrete with hollow ducts already placed where the tendons will run, cure fully, thread steel cable through the ducts, then jack each cable to a specified tension and lock it off with a wedge anchor before releasing the jack, grouting the duct afterward to bond and protect the cable.

**How you know it worked.** The stressed jack shows the target load on its gauge before lock-off; the finished element shows no cracking under a proof load that would crack an equivalent unstressed beam.

**Failure modes.** Hydraulic jack failure under high pressure is violently dangerous to anyone nearby; a duct placed off from its planned line causes uneven stressing, damaging the concrete internally in a way invisible from outside; stress loss over years (the tendon slowly relaxing) if not designed with a safety margin.

**Cost & labour.** ESTIMATED, gated on high-strength wire, jacking equipment, and cn_reinforced_concrete all existing first; a genuinely late-tree technique.

**Danger.** A failed jack or snapped tendon under tension releases stored energy violently, among the more dangerous moments in this entire module. No unusual social danger.

**Confidence: MEDIUM-HIGH** on the physics; **LOW** on Roman-era reachability, this sits at the very end of several other chains.

### cn_suspension_bridge - Suspension bridge system

**What it is / why you want it.** A deck hung from cables in pure tension, spanning gaps no beam, arch, or truss can reach economically.
Also covers: cn_cable_anchorage, cn_wire_cable_spinning, cn_stiffening_truss.

**Why you would never guess this.** The obvious-seeming problem is the cable, and the cable is in fact the easy part, since steel wire is superb in tension and a bundle of many thin wires, spun in place strand by strand across the span, is stronger and more reliably uniform than any single heavy chain link could be, provided the rotation of the bundle is controlled during spinning or it twists itself apart before it is ever loaded. The real problem, discovered expensively and repeatedly through history, is aerodynamic stiffness of the deck. A light deck flexes and, worse, can twist under wind in a way that feeds energy into its own oscillation rather than damping it out, a resonance that grows until the deck tears itself apart, the Tacoma Narrows collapse being the canonical, filmed example centuries after this. A stiffening truss along the deck adds weight and, crucially, torsional resistance, so the deck cannot twist freely, at the cost of extra material; the same problem can be solved with less weight but far more design difficulty using tuned dampers, which is a later refinement, not a first attempt. The towers, meanwhile, must resist the horizontal component of enormous cable tension, which is why they are always massive relative to the deck they appear to be merely holding up.

**Prerequisites.** Bulk steel wire (`10_metallurgy.md#wire_drawing`, at structural tonnage), cn_post_lintel and cn_pratt_truss's tension logic, a cable anchorage massive enough to resist the wedge of stress the cable imparts.

**Roman-available inputs.** None; this is a late-tree, high-steel-tonnage technology with no partial Roman version.

**Procedure.** Erect towers first, able to carry the full vertical load of the cables. Spin the main cable strand by strand across the span using a travelling wheel that carries one wire at a time back and forth, bundling and compacting thousands of individual wires into one cable, with rotation controlled throughout or the bundle twists on itself. Anchor each cable end into a massive block, the cable's tension forms a cone of stress that must stay entirely within the anchorage's own mass, an undersized block lets the wedge pull free, releasing the cable violently. Hang the deck from vertical hangers off the main cable, and stiffen the deck with a truss running its full length to resist twisting in wind.

**How you know it worked.** The deck shows minimal twist under a strong crosswind, tested with flags or streamers at multiple points along its length before trusting it with load; the cable shows uniform tension by hand-test or by consistent sag curve along its length.

**Failure modes.** Deck aerodynamic flutter, a resonance that can destroy an otherwise perfectly engineered bridge in minutes; anchorage pull-out from an undersized block; a cable spun with uncontrolled rotation that develops internal twist and loses strength invisibly.

**Cost & labour.** ESTIMATED, this is one of the largest and latest projects in the whole tree, gated on bulk steel wire production existing first.

**Danger.** Catastrophic, sudden, total collapse if aerodynamic stiffness is wrong, with essentially no warning to people already on the deck. No unusual social danger, but a public collapse would be a severe reputational blow.

**Confidence: HIGH** on the cable tension and aerodynamic-flutter mechanisms, well documented historically; **LOW** on near-term Roman reachability.

### cn_arch_bridge_steel - Steel arch bridge

**What it is / why you want it.** The masonry arch's compression-only load path, rebuilt in steel, letting a single span reach much further than stone voussoirs ever could.

**Why you would never guess this.** A masonry arch (cn_true_arch) is fixed and heavy by necessity, since stone can only push, not pull, and any temperature change or foundation settlement in a rigid fixed arch creates internal stress with nowhere to go, because the structure is over-determined, more connected than the minimum needed to stand, so it cannot simply flex to absorb the change. A steel arch, hinged at its base (and sometimes at its crown too), is instead free to rotate slightly at those hinge points, which lets the whole arch absorb thermal expansion and minor settlement as a small rotation instead of building up hidden internal stress that a rigid arch cannot show you until it cracks.

**Prerequisites.** cn_wrought_iron_girder or steel supply, cn_true_arch's compression-load-path logic, a hinge mechanism strong enough to carry the full arch thrust while still rotating freely.

**Roman-available inputs.** None; steel-tonnage technology.

**Procedure.** Design the arch curve to match the thrust line for its expected loading, as close to Rome's own arch practice as the material allows; place hinges at the base, and at the crown for very long spans, using a pin bearing that can rotate under full compressive load without binding or seizing with rust or debris.

**How you know it worked.** The hinge visibly rotates a small, expected amount across a full seasonal temperature swing without developing new cracks anywhere else in the arch.

**Failure modes.** A hinge that seizes (rust, dirt, poor lubrication) turns a hinged arch back into a rigid one silently, reintroducing the thermal stress problem it was built to avoid; an arch curve that does not match its actual thrust line concentrates stress at one point.

**Cost & labour.** ESTIMATED, gated on bulk steel and precision hinge fabrication.

**Danger.** Sudden compression buckling if the thrust line drifts outside the material. No unusual social danger.

**Confidence: MEDIUM-HIGH** on the hinge logic; **LOW** on near-term reachability.

### cn_bascule_bridge - Bascule, swing, and pontoon bridges

**What it is / why you want it.** Three different ways to open a bridge for river traffic without building it impossibly high: a counterweighted leaf that tilts up (bascule), a whole span that rotates on a central pivot (swing), and a floating roadway anchored across the water (pontoon).
Also covers: cn_swing_bridge, cn_pontoon_bridge.

**Why you would never guess this.** A bascule's counterweight must balance the leaf exactly, but the balance point is not fixed, since the effective load changes as the leaf rotates through its arc, meaning the mechanism must be designed for the whole range of motion, not just the closed or fully open position, or it either will not lift or will not stay open. A swing bridge's central pivot carries the entire deck's weight on one small bearing, so friction there is enormous, and any binding on the rail that guides the free end as it swings will jam a bridge that otherwise pivots freely. A pontoon bridge is the simplest of the three and the only one already within Roman reach in principle (Caesar's Rhine crossings show timber trestle and boat-bridge competence already), it simply rises and falls with the water and its approach ramps must be built to accommodate that motion, and it is normally removable entirely for winter ice or when clear passage is needed.

**Prerequisites.** For bascule and swing: bulk iron or steel for the mechanism and counterweight (cn_wrought_iron_girder), precise bearing fabrication; pontoon needs only Roman-level carpentry and boat-building.

**Roman-available inputs.** Pontoon: timber, boats or floats, rope or chain anchoring, all already Roman. Bascule and swing: gated on iron/steel tonnage.

**Procedure.** Bascule: size the counterweight against the leaf's weight at several points through its arc, not just one, and never let the mechanism jam mid-swing under any load condition. Swing: centre the pivot bearing precisely and keep it lubricated and clear of debris, with a guide rail smooth enough that the free end does not bind on approach. Pontoon: anchor floats securely against current, build ramps with enough vertical play to follow water level, and plan for seasonal removal where ice or flood demands it.

**How you know it worked.** Bascule and swing open and close through their full range without stalling or requiring more force than the design mechanism provides; pontoon rises and falls freely with the water without straining its anchor lines.

**Failure modes.** Bascule counterweight miscalculated for mid-arc load, stalling the leaf partway; swing bridge pivot binding under its own weight; pontoon anchor failure in flood, releasing the whole span downstream.

**Cost & labour.** MEASURED for pontoon, well within Roman capability already; ESTIMATED and gated on iron/steel tonnage for bascule and swing.

**Danger.** A jammed or partially open moving bridge is a serious hazard to river and road traffic simultaneously. No unusual social danger.

**Confidence: HIGH** on pontoon (already demonstrated by Rome); **MEDIUM** on bascule and swing mechanics.

### cn_gravity_dam - Gravity dam, arch dam, earth dam, spillway, retaining wall

**What it is / why you want it.** Holding back water or soil with mass, curvature, or both, and the calculation of whether the structure will slide, overturn, or simply be lifted off its foundation by the water pressing under it.
Also covers: cn_arch_dam, cn_earth_dam, cn_spillway, cn_retaining_wall.

**Why you would never guess this.** A gravity dam holds back water purely by being too heavy for the water's push to slide or tip it, which means the foundation, not the dam wall, is usually the real limit, soil cannot support the load, only rock can, and water seeping under the base creates uplift pressure that can lift the dam like a boat if the foundation is not sealed or drained. An arch dam instead curves horizontally, so it transfers water pressure sideways into its abutments the same way a masonry arch transfers vertical load into its supports, needing far less mass for the same height, but only where the abutments are themselves strong rock, a bad abutment makes an arch dam fail catastrophically rather than merely leak. An earth dam relies on an impermeable clay core surrounded by more permeable zones that drain any seepage safely away from the core; if the core is not more impermeable than the surrounding fill, seepage concentrates and erodes an internal channel through the dam, called piping, a failure mode that is silent until it is sudden and total. A spillway exists purely to control overtopping, since water flowing over a crest not designed for it erodes at very high velocity, and it must never be undersized relative to the worst flood the dam will ever see, one miscalculated crest elevation dooms the whole structure regardless of how well the dam itself was built. A retaining wall is the same soil-pressure problem at building scale, holding back earth rather than water, and needs enough mass and the right base geometry that soil pressure cannot overturn or slide it, helped by drainage that relieves water pressure from behind the wall, the same uplift-and-slide logic as the dam.

**Prerequisites.** cn_true_arch for arch dam curvature logic, cn_pozzolana_concrete or cn_portland_cement for masonry dams, rock foundation surveying.

**Roman-available inputs.** Cut stone, concrete, clay for cores, all already Roman materials; the missing piece is not material but the calculation of sliding, overturning, and uplift forces against a given foundation, currently done, where it is done at all, by conservative overbuilding rather than by number.

**Procedure.** Site any dam on sound rock wherever possible, never on soil alone; for a gravity dam, proportion the mass so its own weight, resisting slide and overturn, comfortably exceeds the water's horizontal push at full pool, and drain the foundation to relieve uplift pressure rather than trying to resist it with mass alone. For an arch dam, confirm the abutment rock itself can take the thrust before committing to the lighter design. For an earth dam, build the clay core distinctly less permeable than the shoulders around it, and monitor seepage continuously, since piping gives visible warning, cloudy or increasing seepage, before it gives catastrophic warning. Size the spillway for the worst flood you can reasonably estimate plus a margin, never trim it for cost.

**How you know it worked.** No measurable base movement after a full pool cycle; seepage, if any, runs clear, not cloudy with eroded core material; the spillway has been tested at a real flood without overtopping elsewhere.

**Failure modes.** Uplift lifting a gravity dam at its base; abutment failure in an arch dam is sudden and total; piping erosion through an earth dam's core, invisible until a sinkhole or cloudy seepage appears, by which point failure may already be near; an undersized spillway that lets the dam overtop anywhere but the spillway, eroding the dam body itself.

**Cost & labour.** ESTIMATED, scales steeply with height; a modest masonry gravity dam is within reach using only Roman materials and empirical caution, larger dams need real load calculation this tree does not yet have.

**Danger.** Dam failure downstream is mass-casualty scale, among the worst failure modes in this entire module for people who never even worked on the structure. No unusual social danger to the builder short of failure.

**Confidence: HIGH** on the sliding/overturning/uplift/piping mechanisms, well documented; **MEDIUM** on Roman-era ability to size these correctly without formal calculation.

### cn_pile_driving - Pile driving, screw piles, soil compaction

**What it is / why you want it.** Getting a foundation's bearing capacity up in soft or loose ground, either by driving a pile down to firmer material or by densifying the soil itself.
Also covers: cn_screw_pile, cn_soil_compaction.

**Why you would never guess this.** A drop-hammer pile does not simply punch a hole, it compresses and packs the soil around it as it goes, which is why driving gets progressively harder the deeper the pile goes, each blow achieves less penetration than the last as the soil densifies, and a foreman who tracks that diminishing penetration per blow is actually measuring the soil's improving bearing capacity in real time without any instrument. A screw pile, a shaft with a helical blade, is driven by twisting instead of hammering, eliminating the drop-hammer entirely, but the helix pitch and angle must be right or the pile simply spins in place without advancing, and a pile driven with uneven torque along its length loses capacity in a way that is not visible from the surface. Soil compaction by rolling works the same densification logic without a pile at all, but only within an optimal moisture range, soil too dry does not compact, soil too wet resists compaction just as badly, since water fills the pore spaces that compaction is trying to close.

**Prerequisites.** cn_crane_treadwheel or a simple gin-pole hoist for the drop hammer, iron for the screw pile's helix, none beyond ordinary Roman capability for compaction itself.

**Roman-available inputs.** Timber piles, iron shoes for pile tips, iron helix blades once forged, rollers of stone or timber for compaction.

**Procedure.** For drop-hammer piling: raise a weight on a guide frame and drop it repeatedly on the pile head, tracking penetration per blow, driving stops once penetration per blow falls below a set small amount, the practical sign the pile has reached adequate bearing. For screw piles: match helix pitch to soil type by trial, and apply steady, even torque throughout the drive. For compaction: test soil moisture by feel (a handful that holds a shape when squeezed but does not run wet is close to optimal) before rolling, and pass the roller repeatedly, tracking that each pass gives less additional benefit than the last.

**How you know it worked.** A driven pile's penetration per blow has dropped to a small, stable figure and stays there for several more blows; compacted soil resists a boot heel pressed firmly into it.

**Failure modes.** A pile driven into a soft pocket that penetrates easily forever, never reaching real bearing capacity, invisible until the structure above it settles; a screw pile spun without advancing wastes effort and gives false confidence; over- or under-moist soil compaction that looks finished but is not.

**Cost & labour.** MEASURED order of magnitude, pile driving is standard heavy construction labour, days per pile depending on depth and soil.

**Danger.** Dropped hammer weight can crush workers; no unusual social danger.

**Confidence: HIGH** on the mechanics, well attested across history and easily observed in practice.

### cn_cofferdam - Cofferdam, dewatering, diaphragm wall, sheet piling

**What it is / why you want it.** Four related ways to keep water out of a hole you need to dig or build in, ranging from a simple temporary dike to a permanent slurry-formed wall.
Also covers: cn_dewatering, cn_diaphragm_wall, cn_sheet_piling.

**Why you would never guess this.** A cofferdam is conceptually simple, a dike around the work area, pumped dry, but leakage increases as the water pressure outside builds relative to the dry pit inside, so the pump capacity needed grows through the job, not just at the start, and a single pump with no backup is a single point of failure for the whole excavation. Dewatering by continuous pumping lowers the water table more broadly, which sounds purely beneficial until you notice it also lets nearby ground settle as the water that was supporting it is removed, meaning a dewatering job can crack a neighbour's foundation even while perfectly protecting your own excavation. Sheet piling, interlocking vertical plates driven side by side into the ground, forms a wall in place without a separate cofferdam basin, but the interlock between sheets must be tight or water seeps between them, and, non-obviously, each new sheet driven is pushed down against the friction of every sheet already driven beside it, so the last sheets in a long run are always the hardest to drive, not the easiest. A diaphragm wall goes further, excavating a trench filled with bentonite clay slurry (a thick, heavy fluid, not yet a Roman-known technique in this application) that holds the trench walls open without any temporary shoring, then pouring concrete into the slurry-filled trench through a pipe that stays submerged in the fresh concrete as it rises, so the heavier concrete displaces the lighter slurry upward and out rather than mixing with it.

**Prerequisites.** Timber and iron for cofferdam and sheet piling, continuous mechanical pumping (`40_power_precision.md#hydraulics_pumps`) for dewatering, bentonite-equivalent clay slurry knowledge for diaphragm walls, a specific gap since Rome has clay but not this particular use of it.

**Roman-available inputs.** Timber, clay, iron sheet stock once forged; the pump technology is the real gate, Roman force pumps exist but not at the continuous, reliable capacity a flooding excavation demands.

**Procedure.** For a cofferdam: build the dike generously oversized against expected water rise, and run two pumps, not one, so a single failure does not flood the site in minutes. For dewatering: monitor nearby structures for settlement throughout the job, not just at the end, since settlement can begin before it is visible in the excavation itself. For sheet piling: drive sheets in a planned sequence, checking interlock tightness sheet by sheet, and expect driving force to increase toward the end of a long run. For a diaphragm wall: keep the slurry level high in the trench at all times work is paused, since a dropped slurry level is what lets trench walls collapse, and place concrete through a tremie pipe kept submerged throughout the pour.

**How you know it worked.** A cofferdam stays dry with steady, manageable pump output, not increasing without explanation; a diaphragm wall trench holds its shape overnight without slumping.

**Failure modes.** Single-pump cofferdam failure flooding the site suddenly; dewatering-induced settlement cracking nearby structures; loose sheet pile interlocks leaking and eventually letting soil wash through with the water; a diaphragm wall trench that collapses because slurry level was allowed to drop.

**Cost & labour.** ESTIMATED, cofferdam and sheet piling are within reach with Roman materials plus continuous pumping capacity; diaphragm wall technique is a genuinely new procedure Rome has no precedent for at all.

**Danger.** Sudden flooding of an occupied excavation is a real drowning and crush hazard; nearby-structure settlement is a legal and social hazard, a neighbour whose wall cracks from your dewatering will not care that your excavation stayed dry.

**Confidence: MEDIUM-HIGH** on cofferdam and sheet piling mechanics; **MEDIUM** on diaphragm wall procedure, a genuinely later technique with no Roman analogue to anchor confidence against.

### cn_caisson - Caisson, pneumatic caisson, underpinning

**What it is / why you want it.** Building a foundation below water or below an existing structure by working inside a sealed or pressurised chamber, or by carefully replacing an old foundation piece by piece while the building above stays standing.
Also covers: cn_pneumatic_caisson, cn_underpinning.

**Why you would never guess this.** A simple caisson is a heavy open-topped box that sinks under its own weight as material is dug out from inside it, sealed at every corner and joint or it floods; if the seal fails while men are inside, the loss of air or buoyancy can be sudden. A pneumatic caisson takes this further by pressurising the working chamber with compressed air to match the water pressure at depth, keeping water out of an open-bottomed chamber entirely, which lets men dig directly at the working face, but it introduces a genuinely new and non-obvious danger: workers who ascend from high pressure back to normal too quickly develop caisson disease (the bends), nitrogen dissolved in the blood under pressure forming bubbles as pressure drops, a killer with no dramatic warning at the time of exposure and a delayed, agonising onset afterward, which means the safety procedure (slow, staged decompression) has to be followed even when nothing seems wrong. A sand boil, sudden inrush of sand and water when pressure drops even briefly, can undermine the whole chamber wall in moments. Underpinning is a different problem entirely, removing and replacing an existing foundation under a building that must not move, even a millimetre of uneven settlement can crack walls above, so the work proceeds in small sections at a time, each one shored, replaced, and allowed to take load again before the next section is touched.

**Prerequisites.** cn_cofferdam's sealing logic, compressed air supply and pressure control (a gap beyond Roman force-pump capability, needing reliable continuous air compression), for underpinning: adjustable shoring and very close monitoring of the structure above.

**Roman-available inputs.** Timber for the caisson box, iron for seals and fittings; pneumatic capability and its pressure control are not Roman-reachable without dedicated development.

**Procedure.** For a simple caisson: seal every joint before sinking begins, and never assume a seal is sound without testing it under load before committing workers inside. For a pneumatic caisson: raise chamber pressure gradually to match working depth, and decompress workers on a slow, staged schedule after every shift regardless of how they feel, since symptoms of the bends appear after exposure, not during it. For underpinning: shore the existing structure section by section, remove and replace only one small section of old foundation at a time, and monitor for any settlement with a fixed reference mark before moving to the next section.

**How you know it worked.** A caisson sinks evenly with no leaks visible at any joint; a pneumatic caisson crew shows no delayed joint pain or dizziness after decompression; underpinned sections show no new cracking in the structure above after each stage.

**Failure modes.** A caisson seal failure floods the working chamber suddenly; skipped or rushed decompression causes the bends, sometimes fatally, hours after the men have left the caisson feeling fine; a sand boil undermines a chamber wall in moments; underpinning a section too large at once lets the building above settle unevenly and crack.

**Cost & labour.** ESTIMATED, pneumatic caisson work is slow and specialised, a small number of trained men working short shifts at depth; underpinning is inherently slow by design, since speed is exactly what causes its failures.

**Danger.** The bends is a genuinely novel danger this module must flag hard, since nothing in Roman experience prepares a worker to fear a symptom that appears only after the danger seems past; sand boils and seal failures are acute drowning risks. No unusual social danger beyond the obvious concern any patron would have about workers dying underground or underwater.

**Confidence: HIGH** on caisson disease's mechanism and the value of staged decompression, well established; **LOW** on Roman-era pneumatic capability, this needs compressed air technology this tree may not yet provide.

### cn_drill_blast - Tunnelling by drill and blast

**What it is / why you want it.** Breaking rock by controlled explosive charges in a planned pattern of drilled holes, rather than by hand tools alone, the only way to advance a tunnel through hard rock at any useful speed.
Also covers: cn_tunnel_cut_cover, cn_ventilation_shaft.

**Why you would never guess this.** The obvious assumption is that more explosive means faster progress; the opposite is closer to true. Blast timing and hole pattern matter more than total charge: charges fired in the wrong sequence (rather than a planned pattern, typically a centre cut fired first to create a free face, followed by rings fired outward toward it) leave large unbroken boulders and poor fragmentation, meaning the crew spends as long breaking up the debris by hand as they saved by blasting; too much charge in any one hole wastes explosive and damages the surrounding rock, weakening the tunnel walls the crew will need to rely on later. Cut-and-cover, digging an open trench, building the tunnel structure inside it, then covering it over, is the right method only for shallow tunnels, since the roof structure must carry the full weight of everything piled back on top of it plus whatever traffic runs above, and that load only gets worse with depth, past a certain depth the shield method (cn_tunnel_shield) becomes the better choice. A ventilation shaft, usually much shallower than the main tunnel it serves, works by natural stack effect, warm air rising out of the shaft draws fresh air in through the tunnel entrance, unless the pressure difference is disrupted by an obstruction, in which case foul air and blast fumes simply pool at the working face.

**Prerequisites.** Gunpowder-equivalent explosive is a serious anachronism trap, Rome has none, this entire technique is gated on an explosive chemistry this tree may treat elsewhere (see `20_chemistry.md` if such an entry exists); rock drilling by hand or animal-powered drill, cn_quarrying_wedge's stone-reading skill.

**Roman-available inputs.** None for the explosive itself; drilling and rock-reading skill, timber for shoring, iron drill bits, all already Roman.

**Procedure.** Drill a planned pattern of holes, deepest and most numerous toward the centre of the face, load and fire the centre holes first to create a free surface, then fire surrounding rings outward toward that free face in sequence, never all at once, clear fumes (natural draft or a temporary shaft) before re-entering the face. For cut-and-cover, size the roof structure for the worst load it will ever carry, everything above it plus traffic, before backfilling. For ventilation shafts, site them to work with the tunnel's natural draft, not against it.

**How you know it worked.** Broken rock at the face is well-fragmented, no boulders too large for a man to move without further breaking; a ventilation shaft draws a candle flame visibly toward the tunnel entrance.

**Failure modes.** Wrong blast sequence leaving unbroken boulders and wasted explosive; overcharged holes damaging tunnel walls that later collapse under their own disturbed stress; an under-sized cut-and-cover roof crushed by backfill and traffic load; a blocked ventilation shaft letting fumes pool at the working face, a suffocation risk with no warning smell for some blast gases.

**Cost & labour.** ESTIMATED, entirely gated on explosive availability; without it, drill-and-hand-break progress in hard rock is measured in a few metres per week per crew (ESTIMATED, basis: pre-explosive tunnelling rates recorded historically).

**Danger.** Explosive misfire, premature detonation, and fume poisoning are all acute, immediate dangers; tunnel roof collapse during cut-and-cover work before the structure is complete. Explosives themselves carry serious social danger, a magistrate will treat unauthorised large-scale explosive production as a direct threat, not an engineering curiosity.

**Confidence: MEDIUM** on the blast-sequence mechanics, well documented from later mining and tunnelling practice; explicitly gated and LOW on Roman-era availability of the explosive itself.

### cn_tunnel_shield - Tunnel shield method, and tunnel lining

**What it is / why you want it.** A protective steel shell pushed forward through soft ground by jacks, letting men excavate the face safely while rings of permanent lining are installed immediately behind, the method that makes tunnelling through soft, unstable ground (rather than solid rock) survivable.
Also covers: cn_tunnel_lining.

**Why you would never guess this.** In hard rock, the rock itself briefly holds its own shape after excavation, giving time to shore it. In soft ground, sand, clay, waterlogged soil, the face can collapse the instant it is exposed, with no such grace period, which is exactly the problem the shield solves: it physically holds the face and the surrounding ground open while men work just behind its leading edge, and is pushed forward by jacks bearing against the lining rings already installed behind it, meaning the tunnel effectively builds its own advancing anchor as it goes. In very soft or waterlogged ground the face itself may need to be pressurised or otherwise supported (an early version of the same principle behind the pneumatic caisson, cn_caisson) or it simply flows into the shield faster than it can be removed. Lining rings are cast and cured before installation, so installation itself is fast, a ring or two a day once the routine is established, but every joint between segments must be tight, since water finding its way through a joint will slowly rot the lining from the inside over years, a slow failure with no dramatic warning until the lining itself starts to fail structurally.

**Prerequisites.** cn_wrought_iron_girder or steel for the shield shell and jacks, cn_concrete_mixer-scale concrete production for lining segments, cn_caisson's sealing and pressure logic for waterlogged ground.

**Roman-available inputs.** None directly; this is a late, iron/steel-tonnage-and-concrete-industry combination technique with no partial Roman precedent, unlike cut-and-cover, which at least resembles a very deep foundation trench Rome could attempt.

**Procedure.** Push the shield forward in short, jacked increments, excavating only the small increment of face exposed at the front at any time, never more. Install a new lining ring immediately behind the shield's advance, providing the next jacking reaction point. Grout the small gap between the lining's outer face and the surrounding ground promptly, since an ungrouted void lets the ground above settle unevenly, a hazard to anything built above the tunnel line.

**How you know it worked.** The shield advances steadily with no sudden ground loss (surface settlement) visible above the tunnel line; lining joints show no water seepage after installation.

**Failure modes.** Face collapse into the shield in waterlogged or very soft ground without pressure support; an ungrouted void behind the lining causing delayed surface settlement, sometimes long after the tunnel is finished and forgotten; leaking lining joints rotting the structure slowly from the inside.

**Cost & labour.** ESTIMATED, a genuinely late-tree, capital- and steel-intensive technique.

**Danger.** Face collapse is an acute burial hazard to the crew working at the shield's leading edge; surface settlement from a poorly grouted tunnel is a hazard to anyone above ground who has no idea a tunnel runs beneath them. No unusual social danger beyond that.

**Confidence: MEDIUM** on the mechanics, well documented historically; explicitly LOW on any near-term Roman reachability.

### cn_crane_derrick - Derrick and tower cranes, elevator safety brake

**What it is / why you want it.** Lifting machinery beyond the Roman treadwheel's practical scale, once continuous mechanical power and steel are available to build taller, stronger masts.
Also covers: cn_crane_tower, cn_elevator_safety_brake.

**Why you would never guess this.** A derrick's mast is strong in the direction it is built for, straight-up compression, but weak against side load, which is exactly what an unevenly tensioned guy line introduces; if the guy cables holding the mast upright are not tensioned equally, the mast bends sideways under a load it was never designed to resist in that direction, and a loose stay that whips in wind is a warning sign, not a minor annoyance. A tower crane takes this further, with the jib and its load cantilevered out from a fixed vertical mast, meaning the base must be heavy enough to resist the overturning moment (the load's tendency to tip the whole tower over, worse the further out the jib reaches) and wind load on the tall exposed structure adds to that overturning tendency, so bracing that seems adequate in calm weather can fail in a storm the crane was never tested against. An elevator's safety brake is the clearest lesson in this whole cluster: the brake's jaws are held open by the tension of the very cable that might break, so as the cable's tension drops (because it is breaking), that drop in tension is what triggers the brake to close, meaning the failure event itself arms the safety device, an elegant design, but only if the wedge angle is exactly right, too shallow and the brake slips instead of gripping.

**Prerequisites.** cn_wrought_iron_girder or steel for the mast and jib, cn_riveted_connection or bolted joints, continuous mechanical power (`40_power_precision.md#gearing_and_transmission`, `steam_high_pressure` for a powered hoist rather than muscle).

**Roman-available inputs.** Timber can build a modest derrick within Roman means; a true tower crane and a mechanical elevator brake are iron/steel-tonnage technologies gated well beyond baseline Rome.

**Procedure.** For a derrick: tension all guy lines equally before loading, and check tension again after any load change, since a mast that was balanced empty may be unbalanced loaded. For a tower crane: size the base counterweight against the worst combination of maximum load at maximum reach plus expected wind, not against calm-weather average conditions. For an elevator brake: set the wedge angle by testing against a deliberately cut cable under controlled conditions before ever trusting it with a rider, and inspect the brake mechanism regularly for corrosion or debris that could stop it engaging cleanly.

**How you know it worked.** A derrick mast stays plumb under full working load in a stiff wind; a tower crane shows no measurable base uplift on the side opposite the load at maximum reach; a test-cut cable on an elevator brake stops the cage within a short, predictable distance.

**Failure modes.** Unequal guy tension bending or toppling a derrick mast; wind-driven overturning of a tower crane whose base counterweight was sized only for calm conditions; an elevator brake with the wrong wedge angle that slips rather than grips, the single most consequential failure in this section since it endangers a rider rather than a construction worker.

**Cost & labour.** ESTIMATED, derricks are within Roman timber-and-rope reach at modest scale; tower cranes and elevator brakes are iron/steel and precision-fabrication technologies, late-tree.

**Danger.** Toppling mast or crane crushes anyone nearby; a failed elevator brake is a fall hazard to an occupant with essentially no personal ability to save themselves once the cable has actually parted. No unusual social danger.

**Confidence: HIGH** on the mechanical logic of all three; **LOW** on Roman-era reachability for the tower crane and elevator brake specifically.

### cn_concrete_mixer - Concrete mixing and placing at scale

**What it is / why you want it.** The machinery and technique that let concrete be placed fast, evenly, and at real building scale, rather than one hand-mixed batch at a time.
Also covers: cn_formwork_shuttering, cn_slipform, cn_shotcrete, cn_vibratory_compaction, cn_expansion_joint.

**Why you would never guess this.** A rotary drum mixer has a real, narrow optimum speed: too slow and the heavier aggregate simply settles to the bottom while the paste stays on top, segregating rather than mixing; too fast and centrifugal force pins everything to the drum wall instead of tumbling it, which looks like mixing but is not. Formwork, the timber or metal mould that holds wet concrete to shape, must be stiff enough that it does not deflect under the wet concrete's full weight, and the non-obvious part is that any deflection that happens while the concrete is still wet becomes permanently cast into the finished surface, a formwork problem you cannot fix after the fact, only before. Slipform construction raises this stakes further, the formwork itself creeps continuously upward as concrete is poured below it, so the creep rate must be tuned exactly against the concrete's setting speed, too fast and the wet concrete below breaks under its own unsupported weight, too slow and the concrete that has already set cracks against the friction of the form still dragging past it. Shotcrete, concrete sprayed on rather than poured, wastes a real fraction of its material to rebound on vertical or overhead surfaces, and needs slow, controlled curing afterward or drying shrinkage cracks the thin sprayed layer. Vibratory compaction is a genuinely narrow-window technique: too little vibration leaves voids and weak zones in the finished concrete, too much actually un-mixes it, shaking the heavy aggregate down and the light paste up, the opposite of what vibration was meant to achieve, and the whole working window per area is only five to ten seconds (ESTIMATED, basis: standard modern vibration practice), easy to overshoot without a trained eye. Expansion joints exist because concrete genuinely moves with temperature, roughly 10-15 millimetres per 100 metres across a 50-degree swing (ESTIMATED, basis: standard concrete thermal expansion coefficients), and without a joint to absorb that movement the slab cracks itself at a point of its own choosing rather than yours; joints are normally spaced under 20 metres apart for exactly this reason.

**Prerequisites.** cn_pozzolana_concrete or cn_portland_cement, mechanical power for a drum mixer and for a vibrator (`40_power_precision.md`), timber for formwork.

**Roman-available inputs.** Timber formwork, already Roman practice for concrete pours; mechanised mixing, slipform, shotcrete, and powered vibration are all beyond Roman baseline, gated on continuous mechanical power.

**Procedure.** Run a drum mixer at its tested optimum speed, neither creeping nor throwing material outward; build formwork stiff enough to show no visible deflection under a test load equal to the wet concrete it will hold, and strike it only once the concrete has enough strength to support itself. For slipform, match the creep rate to the concrete's actual setting time under current temperature and humidity, tested on-site rather than assumed. For shotcrete, angle the nozzle to minimise rebound and cure slowly, keeping the surface damp rather than letting it dry fast. Vibrate concrete in short bursts, moving the vibrator steadily rather than holding it in one place, watching for the surface to go from rough to smooth and glistening, the visual sign it is done, not before and not long after. Place expansion joints at regular intervals, filled with a compressible material that can squeeze rather than extrude out under the joint's own movement.

**How you know it worked.** A mixed batch shows uniform colour and texture with no separated aggregate at the bottom; a struck formwork surface is flat and true to the mould with no visible sag lines; vibrated concrete rings solid when tapped, with no hollow-sounding voids.

**Failure modes.** Segregated concrete from wrong mixer speed, weak and uneven once cured; formwork deflection permanently cast into the finished surface; slipform mismatch either breaking wet concrete below or cracking set concrete against the moving form; shotcrete rebound waste and shrinkage cracking from fast curing; over- or under-vibrated concrete, both weak in different ways; missing or too-widely-spaced expansion joints letting the slab crack itself at an uncontrolled point.

**Cost & labour.** DERIVED, formwork and hand mixing are within Roman means already; mechanised mixing, slipform, shotcrete, and vibration all require continuous mechanical power this tree may not yet have at construction-site scale.

**Danger.** Formwork collapse under wet concrete's full weight can bury or crush workers; shotcrete equipment under pressure can injure if mishandled. No unusual social danger.

**Confidence: HIGH** on the underlying mechanics, well documented modern practice; **MEDIUM** on how much is reachable without dedicated mechanical power at the construction site itself.

### cn_curtain_wall - Curtain wall, plate glass, sash window, asphalt roofing, corrugated roof

**What it is / why you want it.** How a building's outer skin works once a steel or reinforced concrete frame, not the wall itself, carries the structural load, freeing the wall to be thin, glazed, and purely weatherproofing.
Also covers: cn_plate_glass_window, cn_sash_window, cn_asphalt_roofing, cn_roof_truss_corrugated.

**Why you would never guess this.** A curtain wall panel is supported only at its top, hanging rather than standing, and every wind load on it must travel through its fasteners into the frame behind, meaning sealing is critical with essentially no redundancy, one failed seal or fastener is one failed panel, not a shared, forgiving load path the way a thick masonry wall provides. This entire idea only makes sense once cn_steel_frame_skeleton exists to carry the real structural load, without a frame there is nothing for the wall to hang from and it must simply be load-bearing, which is all Rome has ever needed a wall to be. Plate glass at real size is slow and expensive to cast, and the annealing step (controlled slow cooling) afterward matters as much as the casting, since internal stress left in glass cooled too fast can crack the pane months later with no warning, for no visible reason at the time. A sash window trades a simple opening for smooth vertical operation using a cord, pulley, and counterweight, but the weight must exactly balance the pane, or the window either will not stay open on its own or will slam shut, and cord wear is a slow, invisible failure until it snaps. Asphalt (bitumen) roofing is sharply temperature-sensitive at installation, too cold and it cracks rather than bonds, too hot and it simply flows away from where you placed it, and laps must overlap in the direction water actually runs, downslope, or the roofing traps water under itself instead of shedding it. Corrugated iron roofing is stiff specifically because of its corrugations, not despite them, flat iron sheet of the same thickness would sag badly, but fastening through the corrugation ridges concentrates stress at each hole, and daily thermal expansion and contraction against those fasteners is what produces the characteristic ticking and popping noise of a corrugated roof.

**Prerequisites.** cn_steel_frame_skeleton for true curtain wall, glassblowing and casting skill Rome already has (see `30_glass_optics.md`) scaled up for plate glass, bitumen (already known and traded, the Dead Sea and Mesopotamian sources) for asphalt roofing, cn_wrought_iron_girder-tonnage rolled sheet for corrugated iron.

**Roman-available inputs.** Roman glassblowing already produces clear glass panes at modest size; bitumen is a known, traded Roman material; iron sheet rolling and true curtain-wall framing are both gated on the steel tonnage this module discusses above.

**Procedure.** For plate glass: cast, then anneal slowly in a cooling oven with a controlled temperature gradient, checking with polarised light (a much later technique) or, absent that, simply allowing generous cooling time and accepting some loss to invisible internal stress. For a sash window: balance counterweights precisely to the pane's actual weight, and inspect cords for wear on a fixed schedule rather than waiting for a failure. For asphalt roofing: install within the stated temperature range for the bitumen in use, and always lap in the direction water runs. For corrugated roofing: fasten through ridges rather than valleys where possible to reduce standing water at the fastener, and allow slight play at fixings for thermal movement rather than pinning tight.

**How you know it worked.** A curtain wall panel shows no water ingress after a heavy storm; an annealed glass pane shows no spontaneous cracking after some weeks of temperature cycling; a sash window rises and stays at any height without drifting; roofing sheds a hose test with no leaks at the laps.

**Failure modes.** A single failed curtain wall seal or fastener with no redundancy behind it; unannealed glass cracking with no warning weeks after installation; a worn sash cord snapping suddenly; asphalt applied out of temperature range cracking or sliding; corrugated roof fasteners fatiguing from repeated thermal cycling and eventually leaking at every hole.

**Cost & labour.** ESTIMATED, curtain wall is late-tree and steel-gated; plate glass, sash windows, asphalt roofing, and corrugated iron are each individually reachable earlier with Roman-adjacent materials, at real but modest cost.

**Danger.** A falling curtain wall panel is a serious hazard to anyone below; a sash window with a snapped cord can injure fingers or drop suddenly on someone reaching through it. No unusual social danger.

**Confidence: MEDIUM-HIGH** on individual components, well documented; **LOW** on curtain wall specifically as a system, since it is gated deep behind the steel frame.

### cn_cavity_wall - Cavity wall, damp proof course, insulation

**What it is / why you want it.** Keeping moisture and heat where they belong in a wall, using an air gap, a moisture barrier, and trapped air respectively, none of which a solid Roman masonry wall does deliberately.
Also covers: cn_damp_proof_course, cn_insulation.

**Why you would never guess this.** A cavity wall's outer leaf (layer) is expected to weather and get wet, while the inner leaf stays dry across an air gap between them, but the metal ties holding the two leaves together, without which the wall is structurally two thin unstable skins rather than one, become thermal bridges, small paths that carry heat (or cold) straight across the gap the cavity was built to break, and the cavity itself must be kept clear of mortar droppings during construction or moisture bridges across on the debris instead of staying isolated. A damp proof course is a thin, deliberately impermeable layer built into a wall specifically to break capillary rise, since masonry can wick groundwater up several metres through nothing but capillary action in its pores, with no pump or pressure needed, a fact easy to underestimate until you see how far up a wall rot and salt staining can actually reach without one. Insulation works by trapping still air in small cells, since still air itself is what resists heat flow, not the material holding it in place, which is why compressing insulation destroys its performance, squeeze out the trapped air and you have removed the only thing doing the work; a vapour barrier is needed alongside it in cold climates or moisture migrating through the wall condenses inside the insulation and saturates it, again destroying the trapped-air effect from the inside.

**Prerequisites.** Ordinary masonry skill (already Roman) plus cn_wrought_iron_girder-scale iron for wall ties, a genuinely impermeable sheet material (bitumen-soaked felt or similar) for the damp course, any low-density fibrous or cellular material for insulation.

**Roman-available inputs.** Fired brick and mortar (already Roman), bitumen (already traded) as a plausible damp course material, wool or chaff as a plausible crude insulating fill, though Roman builders do not currently use either deliberately for this purpose.

**Procedure.** Build two independent wall leaves with a continuous clear air gap between them, tied at regular intervals with a tie shaped to shed water droplets rather than carry them across, and keep the cavity free of mortar debris as the wall rises, cleaning it out through temporary gaps left for that purpose. Lay a continuous impermeable damp course at the base of any wall, and at any point where groundwater could otherwise wick upward, with no gaps, since a single gap defeats the whole course. Pack insulating material loosely, never compressed, into wall or roof cavities, backed by a vapour-resistant layer on the warm side of the assembly in cold climates.

**How you know it worked.** No damp staining above a properly installed damp course after a wet season; the inner leaf of a cavity wall stays visibly dry while the outer leaf weathers; a hand held against an insulated wall in cold weather feels noticeably less cold than an equivalent solid wall.

**Failure modes.** Mortar droppings bridging a cavity wall's gap, letting damp cross despite the ties; a damp course with even one gap, defeating the whole barrier; compressed or wet insulation, both silently useless despite still being physically present.

**Cost & labour.** DERIVED, modest additional material and care over ordinary Roman wall-building, no new heavy industry required for any of the three.

**Danger.** No acute physical danger; the risk is entirely long-term structural, rot and salt damage accumulating unseen behind a wall that looks fine from outside. No social danger.

**Confidence: HIGH** on the physics of capillary rise, thermal bridging, and trapped-air insulation, all well established and reachable with materials Rome already has, mainly missing the specific technique, not the material.

### cn_central_heating - Central heating, radiators, forced ventilation

**What it is / why you want it.** Distributing heat through a building via circulating hot water and mechanically moving air, beyond what a Roman hypocaust already does with hot air under the floor.
Also covers: cn_radiator, cn_forced_ventilation.

**Why you would never guess this.** A hot water central heating system must stay completely filled with water and free of trapped air, since an air pocket in a pipe stops circulation at that point exactly the way an air lock stops a siphon (cn_aqueduct); an expansion tank is needed specifically because water itself expands as it heats, and without somewhere for that expansion to go, a sealed system builds dangerous pressure. Radiators work by both convection and radiation off a large finned surface area, and mineral scale building up inside them from hard water steadily reduces heat transfer with no outward sign until the room is simply colder than it used to be for the same fuel. Forced ventilation, moving air by fan rather than relying on natural draft, has its own quiet failure mode: fan noise rises sharply with speed, so a duct sized too small forces the fan to run faster than comfortable just to move the required air, and dampers used to adjust flow must never be closed all the way, a fully stalled fan against a closed damper can overheat or damage itself.

**Prerequisites.** cn_wrought_iron_girder-scale iron or cast iron for radiators and piping, mechanical power for a forced ventilation fan, an understanding of the hypocaust Rome already runs as the natural starting point.

**Roman-available inputs.** The hypocaust itself, hot air circulated under floors and through wall flues, already routine in bath complexes and villas; iron pipe and cast iron radiator sections are the missing pieces for a water-based system.

**Procedure.** Fill a hot water system completely before firing the boiler, bleeding air from every high point in the pipe run; size an expansion tank generously against the system's total water volume and expected temperature rise. Keep radiators on a water supply as clean and scale-free as practical, and expect to periodically flush accumulated scale. Size ventilation ducts generously enough that the fan need not run at maximum speed for ordinary operation, and never fully close a damper against a running fan.

**How you know it worked.** Radiators run hot evenly along their whole length, not hot at one end and cool at the other, a sign of a trapped air pocket; ventilation air moves audibly but not uncomfortably loud at normal operating speed.

**Failure modes.** Trapped air stopping circulation to part of a system; an undersized or missing expansion tank building dangerous pressure as water heats; scaled radiators losing capacity invisibly over seasons; a stalled fan against a closed damper overheating.

**Cost & labour.** ESTIMATED, gated on iron piping and radiator casting at real tonnage, well beyond the hypocaust's brick-and-tile construction.

**Danger.** An unvented, over-pressured hot water system can rupture violently; a stalled, overheating fan is a fire risk. No unusual social danger; central heating reads as pure comfort, not suspicious.

**Confidence: MEDIUM-HIGH** on the mechanics; **LOW** on near-term Roman reachability given the iron tonnage required.

### cn_plumbing_stack - Plumbing stack and trapped drains

**What it is / why you want it.** A vertical waste pipe system with water-sealed traps at every fixture, carrying waste away reliably without the smell (and the disease vector) of an open drain.
Also covers: cn_trapped_drain.

**Why you would never guess this.** A soil stack must be sized generously or it siphons itself, waste flowing down a too-narrow pipe drags the air behind it, and that suction can pull the water seal straight out of every trap connected to that stack, defeating them all at once even though nothing about the traps themselves was faulty. A trap's water seal is genuinely small, typically only a few centimetres of standing water in a bent section of pipe, and it can be broken two ways: siphoning, as above, or simple evaporation from a fixture that goes unused for long enough, which is why a bathroom used only occasionally can develop a sewer smell with no plumbing fault at all, the trap simply dried out. Every fixture needs its own trap, since a single trap somewhere upstream does not protect a fixture connected below it, sewer gas will find any untrapped opening.

**Prerequisites.** Ceramic or lead pipe (already Roman, see cn_aqueduct's note on preferring ceramic), correct fall (slope) surveyed with the chorobates or a simple level.

**Roman-available inputs.** Ceramic pipe, lead pipe (avoid for anything carrying acidic waste, the same lead caution as drinking water), mortar joints.

**Procedure.** Size the main soil stack generously relative to the fixtures it serves, so falling waste does not fill the pipe's full cross-section and drag air (and trap seals) down with it. Fit every single fixture, not just some, with its own trapped bend, and slope every supply and waste run consistently so no high point can trap air and no low point can trap solids.

**How you know it worked.** No sewer smell at any fixture after normal use; a fixture left unused for a season still shows a wet trap, or is deliberately flushed periodically to keep it so.

**Failure modes.** An undersized stack siphoning trap seals throughout the building at once, a single design flaw defeating many fixtures simultaneously; an unused fixture's trap drying out by evaporation; an untrapped fixture connected anywhere in the system undermining every trap elsewhere.

**Cost & labour.** MEASURED order of magnitude, well within Roman pipe-laying capability, the missing piece is the trap-and-stack-sizing knowledge, not any new material.

**Danger.** Sewer gas exposure is unpleasant and can be genuinely hazardous in confined, poorly ventilated spaces; no unusual social danger.

**Confidence: HIGH**, this is straightforward hydraulics well within Roman material capability, the gap is purely in the specific technique.

### cn_fire_escape - Fire escape and automatic sprinklers

**What it is / why you want it.** Getting people safely out of a burning multi-storey building, and, separately, suppressing a fire automatically before it spreads, both aimed at a taller, denser style of building than Rome typically builds.
Also covers: cn_sprinkler.

**Why you would never guess this.** A fire escape is only as good as its worst point of failure: stairs or landings that can be obstructed or, worse, locked defeat the entire purpose in the one moment it matters most, and a pivoting ladder section meant to swing down to street level can itself jam at the hinge, historically a real cause of fire escape deaths that had nothing to do with the fire itself, people trapped by the escape mechanism rather than saved by it. An automatic sprinkler's core trick is a thermal element, historically a soldered joint, engineered to melt reliably at a set temperature, releasing water only where and when heat actually triggers it, but that solder plug can be damaged by careless handling during installation and fail to melt reliably later, or fail in the opposite direction and trigger falsely; the whole system is also only as good as its water pressure, adequate pressure must reach every nozzle in the building, not just the ones nearest the supply.

**Prerequisites.** cn_wrought_iron_girder-scale iron for stairs and piping, a reliable, consistent solder or fusible alloy for the sprinkler's thermal element, `85_transport_civil.md#water_supply_sanitation`-level pressurised water supply.

**Roman-available inputs.** Iron for stairs and piping is within reach once bulk iron exists; a genuinely reliable fusible alloy for a sprinkler head is a small-scale metallurgy problem, tin-lead-bismuth alloys are known to Roman metalworkers in principle, but not tuned or tested for this specific melting-point application.

**Procedure.** Keep escape stairs and landings permanently unobstructed and unlockable from the inside, by policy as much as by design, and test any pivoting or folding section regularly under its own weight to confirm the hinge has not seized. For sprinklers, test a sample of each batch of thermal elements to destruction to confirm they melt at the intended temperature, not above it, and verify water pressure reaches the most distant nozzle in the system, not just the nearest.

**How you know it worked.** A fire escape's moving sections deploy freely under a supervised test; a sample sprinkler head triggers at its rated temperature and no other test element triggers falsely at room temperature over a long observation period.

**Failure modes.** A locked or obstructed fire escape, useless in the exact emergency it exists for; a seized pivot hinge trapping people mid-escape; a sprinkler solder plug damaged in handling that never melts; inadequate pressure reaching distant nozzles, giving false confidence in a system that only half-works.

**Cost & labour.** ESTIMATED, iron stairs are a moderate cost once bulk iron exists; sprinkler systems need both piping and a genuinely tested thermal element, a smaller but real development effort.

**Danger.** Fire itself is the obvious danger this equipment addresses; the equipment's own failure modes (locked doors, seized hinges, untested solder) are a second, less obvious danger layered on top, since people trust the escape and stop looking for another way out. Socially, an owner who locks a fire escape door for security reasons is trading one danger for another, and should be told so plainly.

**Confidence: MEDIUM-HIGH** on the mechanics; **LOW** on near-term Roman reachability, gated on both iron tonnage and a tuned fusible alloy.

### cn_terrazzo - Terrazzo floor finish

**What it is / why you want it.** A floor of stone chips set in binder and ground flat and glossy, giving a marble-like finish at a fraction of the cost and weight of solid marble slab.

**Why you would never guess this.** The binder's exact set state matters more than the recipe: aggregate size and the binder's porosity must be matched so the surface can be ground down to a stone-wide sheen without pulling chips loose, and an under-fired lime or gypsum binder stays too soft, yielding to the abrasive stone dust rather than holding the aggregate firmly, while an over-fired, over-hard binder instead tears the chips out of their sockets during grinding rather than grinding down evenly with them.

**Prerequisites.** cn_mortar or cn_gypsum_plaster as binder, cn_stone_polish's grinding and finishing skill, a supply of decorative stone chips (marble offcuts are the obvious Roman source, already generated as quarry and workshop waste).

**Roman-available inputs.** Marble chip waste from any marble workshop, lime or gypsum binder, emery for grinding, all already Roman materials, this is very nearly a Roman-reachable technique already, mostly missing the specific deliberate combination.

**Procedure.** Set stone chips into a bed of binder over a solid base, let the binder cure to a firmness matched to the chip hardness by test (softer than the marble chips but not so soft it yields under the grinding stone before the chips do), then grind the surface flat with progressively finer abrasive until a stone-like polish emerges across both binder and chips together.

**How you know it worked.** The ground surface shows a smooth, continuous polish across both chips and binder with no chips pulled loose or sitting proud of the surface.

**Failure modes.** Binder too soft, grinding gouges the matrix around firmly-set chips unevenly; binder too hard, chips tear free during grinding, leaving pits.

**Cost & labour.** ESTIMATED, modest, using material Rome already discards as waste, a genuinely accessible near-term technique.

**Danger.** Dust exposure during grinding over long periods is a lung hazard, the same caution as any stone-grinding trade. No social danger.

**Confidence: MEDIUM-HIGH**, the materials and skills are all Roman-available, the specific combined technique is the only genuinely new element.

---

## Sources and confidence

Roman baseline claims (arch, vault, pozzolana concrete, aqueduct, crane, surveying) are HIGH confidence, drawn from Vitruvius's *De Architectura*, Frontinus's *De Aquaeductu*, and surviving structures still standing; see `85_transport_civil.md` for the fuller citation trail this module deliberately does not repeat. Beam theory, truss mechanics, cast/wrought iron tension behaviour, reinforced and prestressed concrete's thermal-expansion coincidence, and suspension bridge aerodynamics are all HIGH confidence on the physics, textbook materials science with well documented historical failures (bridge and roof collapses across the 18th to 20th centuries) as evidence. Portland cement chemistry and clinkering temperature are HIGH confidence, MEASURED figures from modern cement manufacture. Caisson disease's mechanism is HIGH confidence, well established medically. Anything marked LOW confidence in this module is LOW specifically on Roman-era reachability, not on the underlying physics, which is not in serious doubt; the gating items are almost always bulk iron and steel tonnage (see `10_metallurgy.md`) and continuous mechanical power (see `40_power_precision.md`), not any missing scientific insight. No number in this module has been invented; every figure is tagged MEASURED, DERIVED, or ESTIMATED with its basis stated inline.

## Where to go next

- `85_transport_civil.md` for the full account of what Rome's civil engineering already does well, the freight arithmetic that should decide where to build first, and the existing `structures_iron_steel`, `concrete_and_cement`, `surveying_precision`, and `water_supply_sanitation` entries this module builds directly on.
- `10_metallurgy.md` for the blast furnace, finery forge, and cementation/crucible steel chain that gates nearly every iron and steel item in this module, from cast iron beams to suspension bridge cable.
- `40_power_precision.md` for the continuous mechanical power (water wheels, steam engines, gearing) that gates rotary cement kilns, concrete mixers, powered cranes, and mechanical ventilation.
