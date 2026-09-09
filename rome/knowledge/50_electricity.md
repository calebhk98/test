# Module 50: Electricity, Magnetism and Electrical Machines

Three things decide the shape of this whole module. Read them before anything else.

**Zinc is the gate.** Zinc boils at 907 C, below the ~1000-1200 C needed to reduce its ore (calamine) with charcoal. In an open furnace the metal leaves as vapour, burns to white oxide smoke, and reburns into hot copper as brass rather than condensing as ingots. This is why Rome has brass by cementation without anyone ever holding a bar of zinc. See `10_metallurgy.md#zinc_metal` for the sealed-retort fix (condense vapour under a liquid seal, the historical Zawar/European process). Without it: no good pile, no cheap steady DC, no electroplating, no serious electromagnets. Everything past `voltaic_pile` waits on that trick.

**No rubber, no gutta percha, ever.** Both are New World/Southeast Asian latex, outside Rome's reach (gutta percha not traded west in quantity until the 19th century; rubber is American). Insulated wire is a real bottleneck. Working answers: silk wrapping (excellent, ruinous price), oiled linen tape (cheap, adequate), shellac varnish (Rome as you find it has no distilled spirits to dissolve it in, so apply it hot; once you have built the worm condenser in `20_chemistry.md#distillation_fractional`, which is a tier 1 node you should have long before any winding, use alcohol as the solvent and the work becomes far easier), bitumen for buried/submerged cable. See `wire_insulation`.

**You do not have to wait for zinc.** A copper plate and an iron plate in brine give roughly 0.4-0.7 V immediately, high internal resistance, fast polarisation. No electroplating, but it swings a compass needle and biases a crystal contact. Static electricity (friction machines, Leyden jars) needs no electrochemistry and no electromagnetic theory, Franklin and Volta had none. Build the electrostatics bench and the brine cell in month one; let the zinc chain mature in parallel.

---

### electrostatics - static machines and the Leyden jar (*electrum, vis electrica*)

**What it is / why you want it.** A rubbed-glass friction machine and a Leyden jar (charge-storing glass jar) give sparks, shocks, and a working model of "electric fluid" with zero chemistry and zero magnetism. Demonstrates the phenomenon before you owe an explanation.

**Why you would never guess this.** High voltage at negligible current can shock, spark, jump a gap, charge a jar; it cannot light a lamp or run a motor. Current is the missing ingredient the rest of the module supplies. No electromagnetic theory is needed.

**Prerequisites.** Glassblowing (`30_glass_optics.md#glassblowing`), tin or silver foil, dry silk or catskin, sulfur or resin.

**Roman-available inputs.** Blown glass globe or cylinder; tin foil (Cornwall/Iberia); dry wool, catskin or silk rubbing pad; amber (*electrum*, Baltic Amber Road, known since Thales to attract chaff); pitch or bitumen for an electrophorus cake.

**Procedure.**
1. Blow a glass globe/cylinder on a crank axle; rub with a dry wool or silk pad while spinning, in a low-humidity room (charge leaks fast in damp air).
2. Leyden jar: glass jar, tin foil glued inside and outside to a hand's width of the rim (bare rim prevents arc-over), a chain/wire from an interior rod to the inner foil, through a dry cork stopper.
3. Charge by touching the rod to the spinning globe for 1-2 minutes.
4. Electrophorus: cast a pitch/bitumen resin disc, rub with fur to charge it, lay a metal plate on top, touch the plate to earth, lift by an insulating handle, charged, repeatable without re-rubbing.
5. Gold leaf electroscope: two gold leaf strips (Rome already beats gold leaf for gilding) hung from a brass rod through a cork in a jar; a charged object touched to the rod splays the leaves, divergence angle is a rough charge gauge.

**How you know it worked.** Jar gives a visible spark and shock across two fingers on rod and foil; electroscope leaves splay; a charged rod lifts papyrus scraps.

**Failure modes.** Damp air or dirty glass bleeds charge in seconds, work near a brazier. Foil too near the rim arcs over. Grounding one hand while charging increases the shock.

**Cost & labour.** ESTIMATED. 1 glassblower-day for jar and globe; 1 goldsmith-day for foil/leaf; under 50 denarii in materials.

**Danger.** Physical: a large jar bank shocks painfully, not usually lethal but risky for a frail heart. Social: unexplained sparks read as *magia*; stage it as *physica* for the Emperor and philosophers, not a wonder-show, or risk prosecution for harmful magic.

**Confidence: HIGH** - textbook 18th-century electrostatics, all materials and skills attested in Rome.

---

### crude_cell - iron and copper brine cell

**What it is / why you want it.** Two dissimilar metal plates in salt water make a battery on day one, before any zinc exists. Weak but real: deflects a needle, biases a point contact.

**Why you would never guess this.** Obvious once galvanic couples are known; not obvious beforehand, nothing about rubbing glass suggests two wet metals push current.

**Prerequisites.** Sheet copper, wrought iron plate, salt or vinegar, a non-conducting vessel.

**Roman-available inputs.** Copper sheet (common); wrought iron plate (bloomery, common); *sal* (salt) in water, or wine vinegar; glazed ceramic or glass vessel.

**Procedure.**
1. Cut a copper plate and an iron plate, ~10x10 cm, keep them apart.
2. Brine: roughly 1 part salt to 5 parts water by weight; or use undiluted wine vinegar.
3. Stand both plates in the vessel a few cm apart, submerged 8-10 cm, wire lead on each.
4. Read voltage only by effects (no meter yet).

**How you know it worked.** Touch the leads to a compass needle's wire loop (`galvanometer`): needle twitches and settles off north. Touch leads to your tongue: faint metallic tingle.

**Failure modes.** Output drops within seconds to minutes as hydrogen bubbles coat the copper (polarisation); brush off or refresh brine to restore briefly. Rusted iron plate gives erratic, lower output.

**Cost & labour.** ESTIMATED. Under 1 denarius in scrap metal, half an hour to build.

**Danger.** Negligible physically (under 1 V, milliamps). Socially trivial.

**Confidence: HIGH** - standard galvanic couple, ~0.4-0.7 V is a well attested real-world range for a dirty iron/copper brine couple (theoretical Fe/Cu couple is about 0.78 V from standard potentials, polarisation and impure metal knock it down).

---

### voltaic_pile - zinc and copper disc pile

**What it is / why you want it.** Zinc and copper discs separated by brine-soaked card give a steady, scalable DC source, the first strong enough for real electrochemistry and magnetism.

**Why you would never guess this.** Stacking, found by Volta in 1800 by trial, is not obvious: single cells are weak, but series cells add their voltages while sharing the stack's structure.

**Prerequisites.** `10_metallurgy.md#zinc_metal` (metallic zinc, sealed-retort produced), copper sheet, brine, card or felt.

**Roman-available inputs.** Zinc discs (once produced per the metallurgy module); copper discs; linen card or wool felt discs, same diameter; brine.

**Procedure.**
1. Cut zinc and copper discs, ~4 cm diameter, and matching brine-soaked card discs.
2. Stack in repeating order: zinc, card, copper, zinc, card, copper..., top to bottom.
3. Compress lightly between two boards, three insulating rods hold alignment.
4. Leads off the top and bottom discs.

**How you know it worked.** A 10-20 cell stack sparks visibly when leads touch and shocks two fingers on top and bottom.

**Failure modes.** Card drying kills output within an hour or two, re-wet periodically. Cells short if brine bridges discs down the outside.

**Cost & labour.** ESTIMATED. ~0.76 V per cell (standard Zn/Cu potential); a 20-cell pile gives ~10-15 V open circuit, internal resistance rises as cells dry. 1 artisan-day for 20 cells; zinc cost dominates until domestic production runs.

**Danger.** Low voltage/current, minor shock only. Zinc dust and fumes from cutting/casting, ventilate.

**Confidence: HIGH** - this is exactly Volta's 1800 design, well documented, all non-zinc materials Roman-attested.

---

### daniell_cell - two-fluid cell (*Daniell, no Latin name*)

**What it is / why you want it.** Separating zinc and copper into different solutions stops the pile's fast polarisation, giving a steady ~1.1 V that holds for days under light load. This, not the pile, is what makes telegraphy and electroplating industries rather than demonstrations.

**Why you would never guess this.** The pile's failure (hydrogen coats the copper) looks like a purity problem. The fix is topological, not chemical: keep the two electrodes' solutions apart with a porous barrier so copper, not hydrogen, deposits at the cathode.

**Prerequisites.** `voltaic_pile` (zinc supply, cell-building skill), copper sulfate (*blue vitriol*, native, Cyprus/Spain), unglazed earthenware.

**Roman-available inputs.** Copper sulfate crystals (blue vitriol, Cyprus/Rio Tinto); zinc plate; dilute acid brine or plain brine for the zinc side (zinc sulfate better if available, `20_chemistry.md#vitriols`); unglazed clay pot as porous membrane, or bladder/parchment diaphragm.

**Procedure.**
1. Outer vessel: copper plate rolled into a cylinder, standing in saturated copper sulfate solution.
2. Inner unglazed clay pot inside the cylinder, filled with dilute brine (or zinc sulfate), zinc rod suspended in it, not touching the pot.
3. Top up copper sulfate crystals as solution depletes, standard maintenance.
4. Leads from zinc rod (negative) and copper cylinder (positive).

**How you know it worked.** Voltage barely sags over hours under light load, unlike the pile; compass-needle test (`galvanometer`) shows steady deflection instead of one fading within a minute.

**Failure modes.** Clay pot too dense chokes current; too porous, solutions mix and the cell fouls within a day. Copper sulfate exhausted: voltage falls, renew crystals.

**Cost & labour.** ESTIMATED. ~1.1 V per cell (attested CuSO4/ZnSO4 figure). 1 potter-day per 50 porous pots; copper sulfate cheap and native.

**Danger.** Copper sulfate toxic in quantity, mild skin irritant. Otherwise as safe as the pile.

**Confidence: HIGH** - textbook 1836 design, every material Roman-available except the choice between zinc sulfate and brine, brine substitution is a documented (if slightly weaker and shorter-lived) workaround.

---

### lead_acid - lead-acid accumulator

**What it is / why you want it.** The first genuinely rechargeable store: charge from a battery bank or dynamo, then carry the charge to where it's needed (a relay hut, a lamp away from a generator).

**Why you would never guess this.** That a lead plate "charges" into two different active materials (spongy lead and lead dioxide) by simply running current through it in acid, rather than being built already-charged, is not intuitive.

**Prerequisites.** `daniell_cell` (or `dynamo_motor`) as charging source, sulfuric acid (`20_chemistry.md#sulfuric_acid`), lead, litharge.

**Roman-available inputs.** Lead sheet and litharge (cupellation byproduct, already produced from silver refining); dilute sulfuric acid (roasted/distilled green vitriol, laborious but attested); glass or wax-lined wood cell.

**Procedure.**
1. Cast lead grids, paste both with litharge worked into a stiff paste with dilute sulfuric acid.
2. Stand grids in dilute sulfuric acid (~1 part strong acid to 4 parts water, acid into water, never reverse, it spatters otherwise).
3. "Form" the plates: current from a Daniell bank for several hours, one plate converts to brown lead dioxide (positive), the other to grey spongy lead (negative). Reverse and repeat a few cycles.
4. Charge fully before first use: constant current until both plates gas freely.

**How you know it worked.** Charged cell reads ~2.0-2.1 V by the deflection test, holds deflection for hours of light discharge, drops sharply near exhaustion.

**Failure modes.** Overcharging boils off water, warps plates. Undercharging leaves soft, low-capacity plates. Discharged for weeks, plates sulfate (hard white crystal), permanent capacity loss.

**Cost & labour.** ESTIMATED. ~2.05 V per cell (attested). 1 lead-worker day per cell for casting/pasting, several days of bank time to form properly.

**Danger.** Sulfuric acid, severe burns, acid into water always. Charging vents hydrogen, explosive indoors, ventilate, no flames. Lead is cumulative poison, wash hands.

**Confidence: MEDIUM** - the electrochemistry is textbook (1859 design), but Roman-era sulfuric acid production is laborious and not independently attested at scale for this period; treat the acid supply chain as the real schedule risk.

---

### wire_insulation - insulated wire, varnish, and cable

**What it is / why you want it.** Every entry below needs wire that does not short against itself, its neighbours, or the earth. This is the New World materials gap worked around with silk, oil, resin and bitumen.

**Why you would never guess this.** Obvious once needed; the twist is shellac, normally solvent-cast in alcohol, must be applied hot-melt in Rome because there is no distilled spirit to dissolve it in.

**Prerequisites.** Drawn copper wire (`10_metallurgy.md#copper_metal`), silk or flax thread, linseed oil, lac resin (Indian Ocean trade), bitumen (Judaea/Mesopotamia).

**Roman-available inputs.** Copper wire, iron drawplate; raw silk (costly import) or flax/linen thread (cheap, local); linseed oil (pressed flax, common); shellac/lac resin (India, Red Sea/Indian Ocean route, the Periplus trade); bitumen (Dead Sea or Hit, Mesopotamia).

**Procedure.**
1. Draw copper rod through successively smaller drawplate holes; anneal (dull red, ~600-700 C, air cool) every 3-4 passes, copper work-hardens and cracks otherwise.
2. Fine/critical wire (galvanometer coils): spiral-wrap a single strand of raw silk under light constant tension, overlap ~half thread width, hand or treadle winder.
3. Bulk wire (telegraph, power windings): wrap linen tape pre-soaked in boiled linseed oil (simmered hours until thick, standard Roman painters'-oil technique), cure 2-3 days.
4. Extra protection: melt shellac in a shallow pan (~80-120 C), draw the wrapped wire through, wipe excess, cool, this hot-dip replaces the solvent-varnish Rome cannot build.
5. Buried/underwater cable: bundle coated wires, wrap in tarred linen, pour molten bitumen over the run in a trough mould, let set.
6. Coil winding: even layers on a wooden former, oiled linen tape between layers, constant tension so turns cannot migrate and touch.

**How you know it worked.** Continuity: Daniell cell plus compass-needle loop (`galvanometer`) in series with the winding's two ends, steady deflection means unbroken conductor. Short test: with the winding otherwise disconnected, touch the cell leads between the winding and whatever it must stay isolated from (core, adjacent layer, earth): any deflection means a short; none confirms isolation.

**Failure modes.** Loose silk wrap migrates, bares copper under vibration. Oil too thick never cures, stays tacky, picks up dust that bridges turns. Shellac dip too hot scorches and embrittles the silk beneath.

**Cost & labour.** ESTIMATED. Silk priced near parity with silver by weight (Pliny on the coin drain to Eastern silk), reserve for fine coils only. Linen/oil insulation costs labour more than material, ~1 weaver-day per 200 m.

**Danger.** Hot shellac and bitumen burn badly on skin, use long tools. Bitumen fumes unpleasant, not acutely poisonous outdoors.

**Confidence: MEDIUM** - the individual materials and processes are all well attested for Rome; their specific use as electrical insulation is a reasoned substitution for materials Rome will never have, not a historically attested electrical practice.

---

### electromagnet - iron-core electromagnet and relay

**What it is / why you want it.** A coil of insulated wire on a soft iron core turns a weak current into a strong, instantly on/off pull, far beyond the bare coil or a lodestone. Also the single most alarming demonstration in Rome.

**Why you would never guess this.** An ordinary iron bar becoming many times more magnetic than the coil alone, then losing it all the instant current stops, is not predictable from static magnetism (lodestones do not turn off).

**Prerequisites.** `wire_insulation`, `crude_cell` or better, soft wrought iron bar.

**Roman-available inputs.** Wrought iron bar, low-carbon, unhardened (hardened steel keeps its magnetism, works badly here); insulated copper wire.

**Procedure.**
1. Wind 100-300 turns of insulated wire tightly around a straight soft iron bar, both ends free.
2. Connect to a cell bank; the bar is strongly magnetic only while current flows, pull scales with turns times current (ampere-turns), squared for horseshoe pull-in designs.
3. Relay: a small electromagnet's spring-loaded armature snaps shut when even a weak, far-travelled current arrives, its contact closing a second, local, strong circuit, so a signal too weak after kilometres of resistive wire still triggers full-strength local action.

**How you know it worked.** The energized bar lifts an iron chain or nail-stack several times its own weight instantly on connection, drops it instantly on disconnection.

**Failure modes.** Hardened/high-carbon iron stays magnetized after current stops (bad for a relay, which must reset). Too few turns or too weak a bank gives barely-detectable pull.

**Cost & labour.** ESTIMATED. Half a blacksmith-day for the bar, one winder-day for 200 turns of insulated wire.

**Danger.** Physically minor at these currents. Socially, an inert bar that seizes and drops metal silently on command reads unmistakably as sorcery. Stage it as *ars*, mechanism explained first, demonstration second.

**Confidence: HIGH** - textbook electromagnetism, all materials Roman-attested once `wire_insulation` and any working cell exist.

---

### galvanometer - tangent galvanometer and the absolute-measurement bootstrap

**What it is / why you want it.** A ring of known radius and turns, with a compass needle at its centre, converts deflection angle into an absolute measurement of current, in real physical units, from geometry, the Earth's own field, and no prior calibrated instrument. This is how Rome bootstraps electrical measurement from nothing.

**Why you would never guess this.** It looks circular: you seem to need a calibrated ammeter to build a calibrated ammeter. The way out is that the Earth's field, though initially unknown, can itself be measured absolutely by a separate, self-contained experiment (Gauss's method, 1832); once that field strength is known, plain coil-and-needle geometry gives current for free.

**Prerequisites.** `wire_insulation`, a compass needle, a plain magnetized needle for calibration.

**Roman-available inputs.** Lodestone (magnetizing needles by stroking), fine steel/iron needle, wood or brass coil former, insulated wire, a protractor (geometry is well within Roman mathematics).

**Procedure, part 1: build the instrument.**
1. Wind N turns of insulated wire in a flat vertical ring of measured radius R (e.g. N=10, R=0.10 m, recorded exactly).
2. Orient the coil's plane along the local magnetic north-south line (align with a resting compass).
3. Pivot a small compass needle at the coil's centre, free to swing horizontally, with a scale to read deflection angle theta from north.
4. Current through the coil deflects the needle to theta; theta=0 with no current confirms alignment.

**Procedure, part 2: find the Earth's field absolutely (Gauss's method), done once, reused forever.**
1. Suspend a small magnetized needle of known mass and simple shape (a uniform rod computes easiest), swinging freely under the Earth's field alone.
2. Time its oscillation period T over many swings. Moment of inertia K comes from measured mass and dimensions (rod: K = mass x length^2/12). This gives (magnetic moment m) x (Earth's field H), since T = 2*pi*sqrt(K/(m*H)).
3. Separately, place the same needle at a measured distance d on the east-west line level with a second free compass needle, read its deflection phi. tan(phi) equals the ratio of the test needle's field there to Earth's field, giving m/H via the standard dipole formula.
4. Multiply the two results, take the square root, for m; divide and take the square root, for H. Both come out in absolute units from mass, length, time, distance and angle alone, no prior electrical or magnetic standard anywhere in the chain.

**Procedure, part 3: use it.** With H known, current follows directly from I = (2*R*H*tan(theta)) / N, so any coil of known R and N reads current straight off a needle's angle from then on, only geometry needed.

**How you know it worked.** Double the current (add an identical cell in series) and confirm deflection follows the tangent law, not a straight line: fast near small angles, most sensitive near 45 degrees, barely moving near 90, that curve is the signature the geometry is correct.

**Failure modes.** Coil misaligned to magnetic north gives a fixed offset error, realign each session. Nearby iron or another energized coil distorts the local field, clear the bench. Pivot friction flattens small deflections, use the lightest suspension possible.

**Cost & labour.** ESTIMATED. 2-3 days bench work for one experimenter to complete the Gauss determination once; the galvanometer itself is a day's winding and mounting.

**Danger.** None physically. Pure metrology, the only risk is sloppy geometry propagating into every current figure downstream, take the measurements seriously and repeat them.

**Confidence: HIGH** - Gauss's absolute method is a real, historically executed (1832) technique requiring nothing beyond mechanics and geometry Rome already has; the tangent galvanometer itself is elementary and well attested.

---

### ammeter_voltmeter - moving-coil meters, standard resistances, Wheatstone bridge

**What it is / why you want it.** Once you have an absolute current standard (`galvanometer`) you can build faster, more convenient meters, and measure unknown resistances precisely by nulling a bridge instead of reading a dial.

**Why you would never guess this.** The Wheatstone bridge's trick: you need no accurate meter at all if you only need to detect zero current, so a crude, nonlinear galvanometer is a perfectly adequate null detector even though it would make a poor absolute meter.

**Prerequisites.** `galvanometer`, `electromagnet` (for magnetizing steel bars), `wire_insulation`.

**Roman-available inputs.** Hardened steel bar for the permanent magnet, magnetized by prolonged insertion in a strong electromagnet's coil (itself pile-powered, a self-bootstrapping step since no strong permanent magnets exist beforehand); drawn wire of known, consistent gauge for standard resistance coils.

**Procedure.**
1. Moving coil meter: a small coil suspended between poles of a hardened, pre-magnetized steel bar magnet, a spring restoring force, current produces torque proportional to itself, deflection reads on a scale calibrated against the tangent galvanometer.
2. Standard resistance coils: draw wire to a precise, repeatable gauge, cut a measured length, R = resistivity x length / cross-section; verify against a coil of double the length (should read double) as a consistency check.
3. Wheatstone bridge: four resistances (two known, one adjustable known, one unknown) in a diamond, galvanometer bridging the two midpoints, battery across the ends. Adjust the known variable resistance until the galvanometer reads zero; unknown = (known adjustable) x (ratio of the other two arms), no current-magnitude accuracy required from the galvanometer at all.

**How you know it worked.** The bridge balances at the same setting regardless of how many cells power it (proof only the ratio matters), and swapped known arms give the same unknown value.

**Failure modes.** Loose or corroded contacts add unaccounted resistance and shift the balance, clean all junctions first. Inconsistent wire gauge along a "standard" coil invalidates the calculation, trust only coils drawn in one continuous pass.

**Cost & labour.** ESTIMATED. 1 instrument-maker week for a working bridge and matched standard coils.

**Danger.** None beyond ordinary battery handling.

**Confidence: HIGH** - Wheatstone bridge (1843, though the null-balance principle is older, Christie 1833) is elementary and robust; every material is available once the earlier entries in this module exist.

---

### electrolysis_industrial - electroplating, electro-refining, chlor-alkali, aluminium

**What it is / why you want it.** Four industrial processes ride on the same trick, current through a solution moving metal or splitting molecules, and the first (electroplating) is immediately, enormously profitable in a status-obsessed Roman market.

**Why you would never guess this.** That the same weak battery current which barely warms a wire can, given time, physically transfer measurable metal from one electrode to another, atom by atom, is not intuitive from mechanics.

**Prerequisites.** `daniell_cell` or `dynamo_motor` for current, `wire_insulation`.

**Roman-available inputs.** Copper sulfate (native, plating/refining baths); brine (chlor-alkali); silver or gold scrap as plating anode; for aluminium, bauxite-type clay (Gallic deposits, workable even if true bauxite is unconfirmed locally) and fluorspar (synthetic cryolite, below).

**Procedure.**
1. Electroplating: object to be plated as cathode, a bar of the plating metal as anode, both in that metal's salt solution (copper sulfate for copper), steady low current for hours to days depending on thickness. Cheap bronze/iron statuary plated silver or gold is visually near-identical to solid precious metal at a fraction of the cost.
2. Electro-refining copper: impure "blister" copper anode, thin pure-copper starter cathode, dilute copper sulfate/sulfuric bath, current dissolves the impure anode and redeposits 99.9%+ pure copper on the cathode; silver/gold impurities collect as recoverable "anode slime". This purity is what low-resistance wire needs.
3. Chlor-alkali: electrolyse strong brine between inert electrodes (carbon anode, iron cathode); chlorine at the anode, hydrogen at the cathode, sodium hydroxide accumulates in solution. First cheap ancient source of caustic soda and chlorine.
4. Aluminium, Hall-Heroult: dissolve alumina (roasted, purified bauxite-clay) in molten cryolite or synthetic fluoride flux (fluorspar plus sulfuric acid gives hydrofluoric acid, reacted with soda and alumina), electrolyse at ~950-980 C with carbon electrodes and heavy current, molten aluminium collects at the cathode. Needs `dynamo_motor`-scale current, a battery bank cannot supply it economically.

**How you know it worked.** Plating: visible, adherent, evenly coloured layer that does not flake under a fingernail. Refining: cathode grows measurably heavier and more lustrous over days. Chlor-alkali: sharp chlorine smell confirms gas evolution. Aluminium: a silvery pool distinctly lighter than any prior metal for the same volume.

**Failure modes.** Plating: too high a current gives a rough "burnt" deposit, keep current density low. Aluminium bath: wrong flux ratio raises the melting point past what the furnace holds, or fails to dissolve the alumina.

**Cost & labour.** ESTIMATED. Plating is cheap, fast to profit. Aluminium is a late, capital-heavy, dynamo-dependent capstone project, not an early win.

**Danger.** Chlorine gas is acutely toxic, strong ventilation only, never enclosed. Hydrofluoric acid is severely corrosive, absorbs through skin causing delayed poisoning, handle only in lead/wax-lined vessels with full protection. Electroplating precious metal onto base objects that imitate coinage risks prosecution for counterfeiting (*crimen falsi*), keep plated goods clearly distinct from coin.

**Confidence: HIGH for electroplating and refining, MEDIUM for chlor-alkali (materials fine, gas handling is the risk), LOW for aluminium** - the Hall-Heroult chemistry is textbook, but a Roman-sourced fluoride flux chain and dynamo-scale current are both multi-decade downstream dependencies within this same tech tree.

---

### dynamo_motor - Faraday disc, ring and drum armatures, self-excitation

**What it is / why you want it.** A rotating machine that turns mechanical motion (water wheel, animal capstan) into large, sustained electric current, or runs backwards as a motor turning current back into mechanical work. This is what finally makes electricity a bulk industrial power source rather than a battery-limited curiosity.

**Why you would never guess this.** Self-excitation is the trap: you need a magnetic field to generate current, and the obvious way to get a strong field is an electromagnet, but an electromagnet needs current you do not yet have. Nobody guesses that the iron core's own faint residual magnetism (left over from any prior exposure to a magnetic field, however weak) is enough to start a tiny trickle of current, which strengthens the field coil, which strengthens the current, in a self-reinforcing climb up to full output within seconds of starting rotation. Years get wasted building ever-bigger permanent-magnet machines because this is not obvious.

**Prerequisites.** `electromagnet`, `wire_insulation`, `galvanometer` (for setup verification), a water wheel or capstan for mechanical drive.

**Roman-available inputs.** Soft iron for cores, insulated copper wire, wooden or bronze axle and bearings, existing Roman water-mill or animal-capstan infrastructure for the drive.

**Procedure.**
1. Faraday disc (simplest, weakest): a copper disc spun rapidly between the poles of a fixed magnet, brushes contacting the rim and the axle draw off a low-voltage, high-current DC output. Useful as a proof of principle, poor for real power.
2. Ring armature (Pacinotti-type): an iron ring wound with many coil sections around its circumference, rotating inside fixed field-coil poles; a commutator, a segmented copper ring the coil sections connect to in sequence, with fixed brushes riding on it, converts the internally-alternating current to steady DC at the output leads.
3. Drum armature (Gramme-type): the practical successor, coils wound lengthwise around an iron drum rather than a ring, mechanically stronger and more efficient, otherwise the same commutator principle.
4. Self-excitation: wind the field-coil poles with the same wire the armature will eventually feed, connect them in the circuit (shunt, across the output, is simplest to build first) rather than powering them from a separate battery. Spin the armature; the iron core's small residual magnetism (present in any iron that has ever been near another magnet, including the Earth) induces a tiny starting current, which flows into the field coil, strengthening the field, which increases the induced current, climbing rapidly to full rated output within seconds. No permanent magnet and no external battery are needed once the machine has run once.
5. Run as motor: apply external current to the same machine's field and armature windings, the same electromagnetic force that generated current in reverse now produces torque, turning the shaft.

**How you know it worked.** Spin the armature by hand or light drive: output leads produce a small but rapidly climbing deflection on the galvanometer over the first several seconds, a spark appears at the brushes as current builds, and a slack field-coil connection (breaking self-excitation) makes output collapse back to near zero, confirming the field really is self-sustaining, not from a hidden battery.

**Failure modes.** Field coil wound backwards relative to the armature's rotation direction actively cancels the residual field instead of reinforcing it, output stays near zero indefinitely, reverse either the winding direction or the rotation and try again. Commutator segments not properly insulated from each other short the armature windings together.

**Cost & labour.** ESTIMATED. A working drum-armature dynamo is a multi-week project for a small instrument-making team, several skilled artisan-weeks in winding alone; the mechanical drive (water wheel, gearing) is standard Roman engineering, no new skill needed there.

**Danger.** A running dynamo's brushes and commutator can spark and burn fingers; larger machines can deliver a dangerous shock and enough current to cause real burns at points of poor contact. Spinning parts are a mechanical hazard, guard the drive belt and axle.

**Confidence: HIGH** - self-excitation is a well documented, historically real discovery (Wilde, Siemens, Wheatstone, all 1866-67, converging independently once dynamos existed), the physics is textbook and every material is Roman-available once the earlier module entries exist.

---

### transformer_ac - AC generation, transformers, lamination, three phase

**What it is / why you want it.** Alternating current lets you step voltage up for long-distance transmission (lower current for the same power, so much lower resistive loss in the wire) and step it back down for safe local use, something a DC-only system cannot do simply.

**Why you would never guess this.** That a transformer moves power between two entirely unconnected wire coils, with no direct electrical contact at all, purely through a changing magnetic field in a shared iron core, looks impossible until you have already accepted electromagnetic induction from `dynamo_motor`.

**Prerequisites.** `dynamo_motor`, `wire_insulation`.

**Roman-available inputs.** Thin iron sheet (rolled and cut for lamination), insulated wire, varnish or paper for inter-sheet insulation.

**Procedure.**
1. Build an alternator: same as the `dynamo_motor` drum armature, but with slip rings (continuous copper rings, not a segmented commutator) at the brushes, this passes the coil's naturally alternating current straight out rather than rectifying it.
2. Transformer: wind a primary coil and a separate secondary coil on a shared closed iron core (a rectangular or ring-shaped loop of thin iron). The ratio of turns sets the voltage ratio directly (turns_primary / turns_secondary = volts_primary / volts_secondary), power in equals power out minus small losses, so a step-up in voltage gives a matching step-down in current, and vice versa.
3. Laminated core: build the core from thin iron sheets, roughly 0.3-0.5 mm, each coated with a thin varnish or separated by paper, stacked rather than cast solid. A solid iron core lets large circulating "eddy" currents flow inside the metal itself, wasting power as heat; thin insulated sheets each carry only a small local eddy current, cutting this loss drastically. This is not optional at any serious power level, a solid-core transformer can grow uncomfortably hot doing nothing useful.
4. Three-phase: build three separate windings on the alternator, spaced 120 degrees apart around the rotor, giving three overlapping AC outputs. This smooths total power delivery (the three phases never all dip to zero together), uses the conductor material more efficiently for a given power, and, later, lets an AC motor start itself from the rotating field the three phases naturally produce, without extra starting machinery.
5. Distribution logic: generate at moderate voltage, step up with a transformer for the transmission run, step back down with a second transformer near the point of use. Resistive loss in the line scales with current squared, so halving the transmission current (by doubling voltage) cuts line loss to a quarter for the same delivered power, this is the entire economic argument for AC over DC at any distance beyond a single building.

**How you know it worked.** The transformer's secondary produces a voltage on the galvanometer/meter test in the ratio predicted by the turns count, and a laminated-core transformer stays noticeably cooler to the touch after an hour of running than a solid-core one of the same size and load.

**Failure modes.** Inter-sheet insulation damaged or omitted turns lamination back into a solid core electrically, losses return and the core overheats. Mismatched phase spacing on a three-phase winding produces uneven, juddering output.

**Cost & labour.** ESTIMATED. A small transformer is a few artisan-days; sheet-iron rolling and coating for lamination is the slow step, expect it to be the bottleneck material for a while.

**Danger.** AC at transmission voltages is at least as dangerous as DC of the same voltage, and the stepped-up transmission voltage itself (potentially hundreds of volts) is lethal, insulate and fence transmission runs, never work on a live line.

**Confidence: HIGH** - all textbook 19th-century electrical engineering, no material or skill gap beyond what earlier entries in this module already require.

---

### telegraph - electric line telegraph

**What it is / why you want it.** A wire line with relay stations turns a message that takes a courier a month into one that arrives within the hour. This is the single strongest funding argument in this entire module: it is a strategic weapon, not a toy.

**Why you would never guess this.** The individual pieces (wire, cell, electromagnet, relay) are each already covered above; the non-obvious part is operational, that a chain of short relay hops, each one re-amplifying a weakening signal with its own local battery, can carry a message indefinitely far without the line resistance ever mattering end to end.

**Prerequisites.** `wire_insulation`, `daniell_cell`, `electromagnet` (as relay and as sounder), `galvanometer` for line testing.

**Roman-available inputs.** Iron or copper line wire; wooden poles (set along the existing Roman road network, reusing its surveyed, maintained right-of-way and milestones); glass or fired-ceramic insulator knobs mounted on crossarms to hold the wire clear of the pole and shed rain; Daniell cell banks at every station.

**Procedure.**
1. String wire on poles at a height clear of traffic and livestock, along the road network for ease of maintenance and right-of-way.
2. Mount each wire on a glass or glazed-ceramic insulator knob at every pole, this is what actually stops the signal leaking to earth through a wet wooden pole, bare wire against wet wood loses current fast.
3. Every 30-50 km (shorter in wet climates or with lower-grade insulation, longer in dry ones, ESTIMATED basis: 19th-century relay spacing on comparably-insulated lines), build a relay station: incoming weak current works a relay's electromagnet (see `electromagnet`), whose contact closes a fresh local circuit, powered by that station's own Daniell bank, driving the next leg of wire at full strength again.
4. At each station, an operator reads the incoming clicks (electromagnet sounder) and keys the outgoing line by hand, relaying the message onward.
5. Terminal stations: a keying switch to open/close the circuit in a code (simple on/off patterns suffice, a Morse-style dot/dash scheme is easy to teach and requires no new technology).

**How you know it worked.** A message sent from one terminal is read back correctly at the other after transiting every relay, and total transit time is dominated by operator speed at each station (seconds per station), not by the wire itself, current in a copper wire moves at a large fraction of light speed for these purposes, effectively instantaneous over any Roman distance.

**Failure modes.** A single broken wire or failed relay stops the whole line past that point, test each segment daily with the galvanometer continuity test from `wire_insulation`. Storms and lightning strikes damage exposed lines, a lightning gap or fuse device (a weak sacrificial link that arcs and breaks before finer equipment is damaged) at each station protects the relay coils.

**Cost & labour.** ESTIMATED (basis: 19th-century telegraph construction rates, adjusted for Roman road reuse). Pole-setting and wiring at perhaps 1 labourer-day per km with an established road to follow; a relay station is a small permanent posting, 1-2 operators, comparable to an existing *cursus publicus* mutatio.

**Danger.** Lightning strikes on exposed line are a real fire and injury risk at stations, ground/fuse protection is not optional. Strategically, a working telegraph line is a target, treat frontier relay stations as fortified posts, not open sheds.

**Cost argument for the Emperor.** The *cursus publicus* moves an urgent dispatch at perhaps 50-80 km/day under favourable conditions; Rome to the Rhine frontier, roughly 1,500 km, takes on the order of 20-30 days by courier. A telegraph line covering the same route, with roughly 30-50 relay stations each adding a few minutes of operator time, delivers the same message in under an hour. That collapse, a month of warning time for a frontier incursion down to under an hour, is what buys this module its funding.

**Confidence: HIGH** - every component is separately well attested above; the only genuinely new claim is operational (relay chaining), which is exactly how real 19th-century telegraph networks worked.

---

### arc_light - carbon arc lamp

**What it is / why you want it.** Two carbon rods with a high-current, low-voltage supply between them strike a blinding, sustained electric arc, the first electric light bright enough to matter for a public square or a lighthouse.

**Why you would never guess this.** That pulling two touching conductors slightly apart under load creates a stable, self-sustaining glowing gas bridge (ionised air/carbon vapour) rather than simply extinguishing the circuit, is not predictable from the batteries-and-wires picture built so far.

**Prerequisites.** `dynamo_motor` (batteries alone are too weak/short-lived for sustained arc use), pure carbon rod stock.

**Roman-available inputs.** Charred hardwood or lampblack pressed and baked into rod form for carbon electrodes; dynamo-supplied current.

**Procedure.**
1. Prepare carbon rods: char dense hardwood in a low-air kiln, or press lampblack with a starch binder into rod moulds and bake hard, roughly 1 cm diameter, 20-30 cm long.
2. Mount two rods point to point in a lamp housing, connected to a dynamo supply of roughly 40-60 V and several tens of amps for a bright arc.
3. Touch the rods together to strike the arc, then draw them apart a few mm, the arc bridges the gap and glows intensely.
4. Fit a simple clockwork or weighted feed mechanism to advance the rods slowly as their tips burn away, maintaining the gap automatically.

**How you know it worked.** A stable, steady, very bright blue-white light with a faint hiss, rods visibly shorten over the course of an hour.

**Failure modes.** Gap too wide extinguishes the arc, too narrow just short-circuits with no arc at all. Rods of inconsistent density burn unevenly and the arc wanders or dies.

**Cost & labour.** ESTIMATED. Rod-making is cheap; the dynamo supply is the real capital cost, shared with other module entries.

**Danger.** Arc light is dangerously bright to view directly (eye damage with prolonged close viewing) and the electrodes run very hot, fire risk if housed carelessly. High current supply is a serious shock and burn hazard at the terminals.

**Confidence: HIGH** - simple, well attested 19th-century technology, no material gap once a dynamo exists.

---

### incandescent_lamp - filament lamp, carbon then tungsten

**What it is / why you want it.** A thin filament heated to incandescence inside an evacuated glass bulb gives soft, steady, room-scale light, safe and practical in a way an open arc is not, and in a city whose insulae burn down routinely, "light without flame" is a serious public-safety selling point.

**Why you would never guess this.** The vacuum requirement is the trap: a filament heated to glowing in open air burns to ash in seconds, and it is not obvious beforehand that removing the air entirely, rather than somehow protecting the filament, is the actual fix.

**Prerequisites.** `30_glass_optics.md#glassblowing`, `dynamo_motor` or a large battery bank, a vacuum-pumping method.

**Roman-available inputs.** Carbonised bamboo fibre or cotton thread for the first-generation filament (charred in a sealed crucible, no air, until it is pure brittle carbon); blown glass bulbs; mercury (Almadén, Spain, imperially operated mines) for a mercury-column vacuum pump built on the same siphon/piston principles as existing Roman force pumps.

**Procedure.**
1. Carbonise a thin thread or bamboo splint: seal it in a covered crucible packed with charcoal dust (excludes air), heat to a dull-to-cherry red for an hour or more, cool before opening, the thread comes out as fragile pure carbon, shape it into a thin loop or filament before or during carbonising.
2. Mount the carbon filament on two lead-in wires sealed through the glass bulb's neck (a glassblowing skill, sealing metal through glass without cracking it).
3. Evacuate the bulb: connect to a mercury or piston vacuum pump before sealing the neck shut, draw as hard a vacuum as the pump achieves, residual air still oxidises the filament slowly, so "as good a vacuum as achievable" is the standing goal, not a fixed number.
4. Seal the neck closed under vacuum (glassblower's torch, working fast).
5. Connect to a dynamo or large battery bank at low voltage, high current, the filament glows orange-yellow when correctly matched to the supply.

**How you know it worked.** Steady, sustained glow for extended use (target hours, not seconds); a bulb with a poor vacuum blackens inside and the filament burns out within minutes, a good one lasts far longer.

**Failure modes.** Any air leak at the glass-metal seal shortens filament life drastically, test seals carefully before committing a finished filament. Filament too thick draws too much current for available supply and never gets hot enough to glow; too thin burns out almost immediately.

**Cost & labour.** ESTIMATED. A skilled glassblower-day per bulb early on, dropping fast with practice; the vacuum pump is a one-time capital build, reused for every bulb after.

**Tungsten upgrade, later stage.** Tungsten filaments run hotter and last far longer than carbon, but tungsten ore is scarce, its extraction and the powder-metallurgy techniques needed to draw it into fine wire (melting point 3422 C, far beyond any Roman furnace, so it must be sintered from powder, not cast) are a substantial separate technology project. Treat carbon filaments as the workable centuries-long solution and tungsten as a distant stretch goal, not a near-term requirement.

**Danger.** Vacuum-sealed glass bulbs can implode if struck or over-stressed, throwing glass fragments. Mercury (for the vacuum pump) is a cumulative poison, handle spills immediately and never heat mercury in an open room.

**Political value.** Rome's insulae burn constantly (the fire of 64 AD under Nero is the famous case, but tenement fires from oil lamps and cooking fires are a routine hazard throughout the city). A sealed glass bulb that gives light with no open flame, no oil to spill, and no wick to tip over is a direct, visible answer to the city's single most dangerous everyday risk, and is worth making explicitly in any pitch for imperial or civic funding.

**Confidence: MEDIUM for carbon filament** (textbook 1870s-80s technology, every material Roman-reachable, but the vacuum pump and glass-metal seal both need real practiced skill); **LOW for tungsten** (metallurgically far beyond near-term Roman capability, flagged as a later-centuries upgrade only).

---

## Sources and confidence

The physics and chemistry throughout are standard 18th-20th century textbook material (Volta 1800, Daniell 1836, Gauss's absolute magnetic measurements 1832, Wheatstone bridge popularised 1843 after Christie 1833, Pacinotti/Gramme/self-excitation dynamos 1860s, Edison/Swan incandescent lamps 1879-80, Hall-Heroult aluminium 1886); none of it is in doubt. What is genuinely uncertain is Roman-era feasibility of specific material substitutions: shellac's hot-melt application in place of a solvent varnish, sulfuric acid production by vitriol distillation at useful scale, and a Roman-sourced synthetic cryolite chain for aluminium, all marked MEDIUM or LOW above and flagged as schedule risks rather than physics risks. Roman antiquity already had a documented, if unexplained, brush with bioelectricity: Scribonius Largus (1st century AD, *Compositiones*) recommended standing on a live torpedo/electric ray to treat headache and gout, attested, unverified beyond the secondary literature, worth mentioning to a Roman audience as evidence the phenomenon was never truly unknown to them, only unexplained. Cross-references: `10_metallurgy.md#zinc_metal` for the zinc bottleneck, `10_metallurgy.md#copper_metal` for wire stock, `20_chemistry.md#sulfuric_acid` and `#vitriols` for acid and vitriol chemistry, `30_glass_optics.md#glassblowing` for jars, bulbs, and sealed vacuum vessels.
