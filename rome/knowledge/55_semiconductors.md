# Module 55: Vacuum, High Purity and Semiconductors

Two things matter more than any single recipe in this module.

First: **a galena cat's whisker rectifier is a working semiconductor device that needs no purification at all.** Mineral lead sulfide straight out of a lead mine, a springy scrap of wire, and the crude copper-iron brine cell from `50_electricity.md` are enough to show a magistrate or patron a current that flows one way and not the other. No furnace, no vacuum, no theory. Build it in your first five years. It is the single piece of evidence that turns "the exile's mad two-century plan" into a funded programme, because it is a real, working, testable thing, not a promise.

Second: **you carry the theory, and that is worth more than any apparatus.** Band structure, doping, majority and minority carriers, the p-n junction, minority carrier injection: working these out from scratch took the modern world from about 1900 to 1947 and several Nobel prizes. You already know the answers. Write them down in `semiconductor_theory` below in your first decade, in as many durable copies as you can manage, whether or not you personally ever see a transistor amplify. You will not live two hundred years and you will not get to teach this twice. The writing costs a scribe's fee. The saving is generations.

Everything else in this module, pumps, tubes, radio, germanium, zone refining, crystal pulling, is the two-century machine that turns those two facts into an amplifying device. Read `50_electricity.md` first; every entry here assumes its batteries, dynamo, meters and insulated wire.

---

### vacuum_pumps - Pumps and gauges for empty space (*antlia pneumatica*)

**What it is / why you want it.** Removing air from a sealed vessel. Needed for discharge tubes, X-ray tubes, vacuum tube filaments, and zone-refining atmospheres.

**Why you would never guess this.** That falling liquid can drag gas out of a closed space with no pistons, seals, or moving parts, is not intuitive. It is also slow: hours per run.

**Prerequisites.** Glassblowing and clear soda-lime glass, mercury (Almadén, Spain), a reliable source of narrow-bore glass tubing.

**Roman-available inputs.** Mercury (*hydrargyrum*, Almadén, imperially operated mine). Glass tubing (Syrian and Alexandrian glassblowers). Leather and tallow for piston seals.

**Procedure.**
1. Piston pump: a brass or bronze cylinder, a leather-and-tallow-sealed piston, one-way leather flap valves at each end, connected by tube to the vessel. Stroke by hand or treadle. Reaches roughly 10 torr with a single barrel, perhaps 1 torr with a well-fitted double barrel and good valves. Leaks past the leather limit it hard.
2. Sprengel mercury drop pump (Sprengel, 1865): a vertical glass tube, closed at bottom by a fine capillary outlet, fed at the top by mercury dripping from a reservoir. Each falling drop seals a slug of the tube's cross-section, trapping a small volume of gas from a side-arm connected to the vessel above; the drop carries that gas plug down and out at the bottom into a mercury trough, drop after drop, thousands per run. No piston, no seal, no machining tolerance: only glass geometry and gravity. Reaches roughly 0.001 torr (1 millitorr) with careful operation, and has been pushed lower with patience.
3. Run the Sprengel for hours; each run removes progressively less gas as pressure drops, so budget a full day for a good vacuum.

**How you know it worked.** McLeod gauge: a bulb of known volume with a graduated capillary, connected to the vacuum line, with its own small mercury reservoir. Trap a sample of the vacuum's gas in the bulb, then compress it by raising mercury into the bulb until it fills a known small volume in the capillary; the compression ratio times the known volumes gives you the original pressure directly, readable from about 10 torr down to roughly 0.0001 torr. This is your only real pressure instrument; build it early.

**Failure modes.** Piston pump: leather dries and cracks, seal fails, pressure stalls. Sprengel: mercury column breaks (air bubble), capillary clogs with dust, reservoir runs dry mid-run. Any hairline crack in the glass ruins the whole system instantly and silently until the McLeod gauge shows it.

**Cost & labour.** Piston pump: ESTIMATED 20 artisan-days (brass turner, leatherworker), 200-400 denarii in materials. Sprengel: ESTIMATED 15 artisan-days of glassblowing plus 5-10 kg mercury in circulation, glass losses expected during development (assume 3-5 rebuilds). MEASURED: Sprengel's historical pump reached vacua adequate for early discharge tube work within his lifetime using exactly this design.

**Danger.** Mercury vapour is a cumulative neurotoxin; work the Sprengel in a ventilated room, never heated, wash hands, do not let apprentices work it daily for years without rotation. Imploding evacuated glass is a real hazard: wire mesh or a leather guard around large vessels.

**Confidence: HIGH** for the physics and the historical Sprengel design; MEDIUM for exact torr figures achievable with Roman-grade glass and mercury purity, which will be worse than 19th-century laboratory glass.

---

### crookes_xray_electron - Discharge tubes, X-rays and the electron (*tubus vacuus electricus*)

**What it is / why you want it.** A sealed, evacuated glass tube with two metal electrodes, driven by a high-voltage source (an induction coil or the dynamo of `50_electricity.md` stepped up), shows cathode rays (a beam from the negative electrode), and at higher voltage, X-rays from wherever that beam strikes glass or metal. Studying the beam's deflection in electric and magnetic fields is how the electron's charge-to-mass ratio was measured.

**Why you would never guess this.** Nothing here is conceptually hard once you know to look. You are not discovering the electron, you are building the two instruments (discharge tube plus deflecting field) that let you demonstrate what you already know exists. This compresses a 30-year 19th-century research programme into an instrument-building exercise.

**Prerequisites.** `vacuum_pumps`, `50_electricity.md` (induction coil or stepped-up dynamo output, on the order of 10-50 kV), glass-metal seals (see `vacuum_tube`).

**Roman-available inputs.** Glass tube (blown, pear-shaped or cylindrical), platinum or iron wire electrodes, mercury-pumped vacuum, copper wire for coils.

**Procedure.**
1. Seal two electrodes into a glass bulb, evacuate with the Sprengel pump to roughly 0.01-0.001 torr (too high a vacuum stops the discharge; too low a vacuum, a poor one, glows differently).
2. Apply high voltage across the electrodes. At moderate vacuum you get a glow discharge; at low pressure (below about 0.01 torr) you get a dark space near the cathode and a beam of cathode rays running straight from it, visible as fluorescence where it strikes the glass.
3. Place a magnet near the tube: the beam bends, proving it is charged particles, not light.
4. Wherever the beam or a metal target inside the tube is struck at higher voltage (tens of kV), X-rays are emitted, detectable by fogging a covered photographic plate or making certain minerals (fluorite) glow faintly nearby.

**How you know it worked.** Visible glow and beam deflection under a magnet; a photographic plate fogs when placed near the tube during operation even through an opaque cover, showing something penetrating passed through.

**Failure modes.** Vacuum too poor: no beam, just a diffuse glow. Vacuum too good: discharge won't strike at all without much higher voltage. Electrode overheats and outgasses, ruining the vacuum mid-run.

**Cost & labour.** ESTIMATED 10 artisan-days per tube, high glass wastage during development (assume half your early tubes crack or leak). Capital: as `vacuum_pumps` plus an induction coil, ESTIMATED 300-600 denarii total workshop cost.

**Danger.** Publish a blunt radiation warning BEFORE your first public demonstration: unshielded X-rays cause burns, sterility and cancer with repeated exposure. Never place a hand or any body part in the direct beam. Keep exposure times to seconds, stand behind a lead sheet (lead is abundant, mined at Cartagena and in Britain) whenever the tube runs above roughly 20 kV, and do not let this become a court entertainment performed daily.

**Confidence: HIGH** on the physics and the instrument design; MEDIUM on exact voltage/pressure thresholds achievable with Roman-grade coils and glass.

---

### vacuum_tube - The diode and triode (*lampas electrica*)

**What it is / why you want it.** A heated filament in vacuum boils off electrons (thermionic emission); a nearby plate at positive voltage collects them, giving one-way current flow, a diode. Add a fine wire mesh (a grid) between filament and plate, and a small voltage on the grid controls a much larger current at the plate: an amplifier. This is the device that turns every weak signal in your empire, a distant radio wave, a faint galvanometer deflection, a whisper down a wire, into something strong enough to read, record or drive a speaker.

**Why you would never guess this.** Obvious once you have the electron (`crookes_xray_electron`) and a decent vacuum. The hard part is entirely mechanical: getting a metal wire through a glass wall without the seal cracking on every heating and cooling cycle.

**Prerequisites.** `vacuum_pumps`, `crookes_xray_electron`, `50_electricity.md` (a stable low-voltage supply for the filament, a higher-voltage supply for the plate), metal-alloying capability for seal wire.

**Roman-available inputs.** Platinum wire for filament and seals (soda-lime and lead glass both expand at rates close enough to platinum's to seal reliably, a real property, not a guess); iron or nickel sheet for the plate; fine copper or iron wire for the grid; phosphorus (see `vacuum_pumps` getters, below) or a strip of barium metal for finishing the vacuum.

**Procedure.**
1. Filament: platinum wire, or a carbonized fiber (a thread or strip of bamboo charred in a closed crucible, in the manner Edison first used, before tungsten is available to you) mounted between two lead-in wires. Heat it with a small current from `50_electricity.md`'s battery bank until it glows dull red to orange, hot enough to emit electrons, not so hot it burns out.
2. Plate: a small metal cylinder or flat sheet surrounding or facing the filament, connected to a lead-in wire and a positive voltage supply.
3. Triode: insert a fine wire grid or spiral between filament and plate, on its own lead-in, positioned close to the filament so small grid voltage swings strongly affect the electron stream reaching the plate.
4. Glass-to-metal seal, the hard problem: glass and metal must have matched thermal expansion or the seal cracks on the first heating cycle. Platinum works but is ruinously expensive at scale. The practical, cheaper long-term answer is what later engineers called Dumet wire: a core of nickel-iron alloy (roughly 42% nickel, the rest iron, an alloy whose expansion nearly matches glass) clad in a thin copper sheath for solderability. Both nickel and iron are Roman-available; the alloy must be weighed and crucible-melted to composition, then drawn to fine wire. Expect years of trial before you match platinum's seal reliability with this cheaper alloy.
5. Evacuate the sealed envelope with the Sprengel pump, then finish with a getter (below) before final seal-off, and seal the exhaust tip closed with a torch while still under vacuum.

**How you know it worked.** Diode: current flows filament-to-plate when plate is positive, not when negative, testable directly with `50_electricity.md`'s galvanometer. Triode: a small voltage change on the grid produces a large, visible swing in plate current on the same galvanometer; that swing-ratio is your gain.

**Failure modes.** Seal cracks on heating (mismatched expansion): tube loses vacuum and glows blue-white briefly, then dies. Filament burns out (too much current). Grid too close to filament: shorts. Getter under-dosed: residual gas ionizes, blue glow, poor performance.

**Cost & labour.** ESTIMATED 15-30 artisan-days per working tube during development, dropping with practice; expect a majority of early tubes to fail the seal. Capital, once developed: platinum for early prototype seals is expensive, ESTIMATED 50-100 denarii per gram; Dumet-equivalent alloy wire, once mastered, drops this to ordinary metal cost.

**Danger.** High voltage plate supplies (hundreds of volts) can injure or kill; treat like any live electrical apparatus per `50_electricity.md`.

**Confidence: MEDIUM.** The physics and general design are HIGH confidence. The Dumet-alloy composition and the platinum-glass expansion match are real, MEASURED facts from later engineering; how many rebuild cycles Roman glassblowers need to master matched seals is ESTIMATED.

**Getters (finishing the vacuum after sealing).** A sealed tube always retains trace gas the pump cannot reach. Phosphorus getter: a small pellet of white phosphorus (produced by Brand's process: evaporate urine to a paste, char the residue with sand and charcoal, distil in a covered retort at red heat, collect the vapour under water) placed inside the tube and ignited electrically just before final seal-off; it burns the last oxygen and nitrogen out of the envelope. White phosphorus is pyrophoric and severely toxic; handle only under water, never bare-handed. Barium getter: barium metal, produced by molten-salt electrolysis of barium chloride using `50_electricity.md`'s dynamo, evaporated onto the glass wall by resistive heating inside the sealed, evacuated tube; the fresh barium film chemically scavenges residual gas for the tube's working life. This is a later-stage refinement, ESTIMATED to require its own multi-year metallurgical side-project; phosphorus getters alone are adequate for early tubes.

---

### radio_spark_to_valve - From spark transmitter to the crystal set and the valve radio (*telegraphia sine filo*)

**What it is / why you want it.** Long-distance signalling without wires: a spark transmitter radiates a burst of radio-frequency energy each time its gap fires; a receiver (coherer, then galvanic crystal, then vacuum tube) detects it at a distance.

**Why you would never guess this.** Not obvious that a spark makes waves that travel and can be tuned; the receiver side is where the galena rectifier (`galena_detector`) earns its keep as more than a curiosity.

**Prerequisites.** `50_electricity.md` (induction coil, dynamo), `galena_detector`, insulated copper wire, later `vacuum_tube`.

**Roman-available inputs.** Copper wire (insulated per `50_electricity.md`), an induction coil for the spark gap, iron filings for a coherer, galena and phosphor bronze for the crystal detector.

**Procedure.**
1. Spark transmitter: an induction coil charges a capacitor (a foil-and-mica or Leyden-jar type) across a spark gap wired to an antenna wire and an earth stake; each spark discharges a burst of damped oscillation up the antenna.
2. Earliest receiver, the coherer: a glass tube loosely packed with iron filings between two electrodes; normally high resistance, it "coheres" (drops to low resistance) when radio energy hits it, and must be tapped or vibrated to reset after each pulse. Crude, slow, but needs no crystal-hunting.
3. Better receiver, the crystal set: an antenna and earth, a tuned coil (copper wire wound on a wood or cardboard former, with a sliding tap or several fixed taps to select frequency) in series with a capacitor, feeding the galena cat's whisker detector (`galena_detector`), feeding a high-impedance earpiece.
4. Earpiece, the hard part: a small horseshoe or bar permanent magnet (a natural lodestone, or an electromagnet energized from `50_electricity.md`'s battery for a fixed unit), soft iron pole pieces wound with roughly 1,000-3,000 turns of very fine insulated copper wire (as fine as your wire-drawing allows, insulated per `50_electricity.md`), positioned 0.2-0.5 mm from a thin iron diaphragm (roughly 0.1-0.2 mm sheet iron) stretched over a cup. The many turns of fine wire give the thousands of ohms of impedance needed to respond to the weak current the crystal detector passes; too few turns and the weak signal produces no audible movement at all.
5. Once `vacuum_tube` exists, replace spark and coherer with a valve oscillator (transmitter) and valve amplifier (receiver): continuous waves instead of damped bursts, far greater range and clarity, and the tube amplifier can drive a proper loud diaphragm instead of a delicate earpiece.

**How you know it worked.** A click or tone in the earpiece, or a coherer's needle deflection, coincident with a spark fired at a known distant point; range testing across a field, then across the city, then across provinces once amplification exists.

**Failure modes.** Detuned coil: no signal even at close range. Poor earth connection: weak or no reception. Earpiece gap wrong: too far, no sound; too close, diaphragm sticks to the pole piece.

**Cost & labour.** ESTIMATED 40-80 artisan-hours per receiving station (coil winder, instrument maker), plus `galena_detector` and `50_electricity.md` costs. Range: MEASURED historically, spark sets reached tens of kilometres; ESTIMATED comparable or less with Roman antenna heights and copper purity.

**Danger.** Social: an instantaneous message across provinces looks like sorcery or divine omen to most Romans; manage the reveal carefully, ideally under direct imperial patronage, to avoid a charge of magic (a real legal risk in this period).

**Confidence: MEDIUM.** Coherers and spark sets are well-attested 19th-century devices; exact Roman-achievable ranges and wire gauges are ESTIMATED.

---

### galena_detector - The cat's whisker rectifier (*plumbago fulminans*, informal)

**What it is / why you want it.** A sharp metal point pressed lightly on a natural crystal of galena (lead sulfide, PbS) conducts current far better in one direction than the other. That asymmetry is rectification, the core action of every semiconductor device in this module, and this is the one entry point that costs you nothing: no smelting, no doping, no vacuum, no theory, no good battery. This is your five-year proof of concept.

**Why you would never guess this.** That an ordinary, unrefined mineral straight from a mine, touched by a bent wire, would show any electrical asymmetry at all is not intuitive; it was found in 1874 (Braun) essentially by accident, decades before anyone understood why.

**Prerequisites.** None beyond mining access and `50_electricity.md`'s crude copper-iron brine cell and simple galvanometer, used only to demonstrate the effect, not to make it work.

**Roman-available inputs.** Galena (lead ore, mined extensively across the Empire, notably Britain, Spain and Sardinia, sold openly as the raw material for lead smelting). Fine springy wire: phosphor bronze is best if you have it, otherwise plain spring bronze, brass, or hard-drawn iron wire. A soft metal cup (lead, tin, or a low-melting lead-tin alloy) to mount the crystal.

**Procedure.**
1. Select a piece of galena with a clean, bright, metallic-lustre cleavage face, not a weathered or oxidized (dull grey, crumbly) surface. Galena cleaves perfectly along cubic planes: tap gently with a knife edge along a natural crack line and it splits into flat, shiny faces.
2. Mount the crystal in a small cup of molten lead or fusible lead-tin alloy, poured around its base and allowed to solidify, giving a solid, low-resistance electrical connection to the bulk of the crystal.
3. Mount a length of fine springy wire on a pivoted arm with a fine adjustment screw, so its tip can be moved across the crystal face and pressed down with light, controllable, and importantly consistent, spring force, just enough for contact, not enough to gouge the crystal.
4. Hunt for a sensitive spot: touch the wire tip to different points on the crystal face one at a time, testing each for rectification (below). Sensitive spots are inclusions, boundaries, or defects in the crystal that happen to give strong asymmetric conduction; there is no way to see them in advance, only to search by touch and test. Expect to try dozens of points before finding a good one.
5. To demonstrate to a sceptical patron: wire the crystal-whisker contact in series with `50_electricity.md`'s crude copper-iron brine cell and its galvanometer. Note the deflection. Reverse the cell's polarity. The deflection should now be much smaller, roughly a tenth or less of the first reading, at a sensitive spot. That asymmetry, with no furnace, no glassblower, and a battery a child could build, is your proof of concept.

**How you know it worked.** The galvanometer deflection with the cell one way is markedly larger, several times to tens of times, than with the cell reversed, at the same contact point. In actual radio service, the detector rectifies the received signal into a current the earpiece can render as sound.

**Failure modes.** Oxidized crystal face: little or no asymmetry, resembles a plain resistor both ways. Whisker pressed too hard: crystal fractures or the contact stops being a fine point. Vibration or a jolted table shifts the whisker off its sensitive spot mid-use, a known nuisance of this exact device throughout its later history.

**Cost & labour.** ESTIMATED 2-4 hours to build a mount and adjustment screw, plus an ESTIMATED half-day of patient spot-hunting per usable detector. Materials: a lump of galena (essentially free at any lead mine), a few grams of spring wire, a few grams of lead or tin for the mounting cup. Total capital under 20 denarii.

**Danger.** Lead exposure from handling galena and molten lead-tin mounting alloy; wash hands, do not melt lead indoors without ventilation, do not let children handle raw galena dust. Socially, this is easy to demonstrate as a curiosity and hard to overclaim, present it honestly as "a stone that lets the lightning-fluid pass one way and not the other," not as magic.

**Confidence: HIGH.** This is real, MEASURED 19th-century technology (Braun 1874, used commercially in crystal radio sets from the 1900s on) requiring no purification, no doping and no vacuum. It is the most certain entry in this entire module.

---

### semiconductor_theory - What you must write down before you can test any of it (*doctrina de semiconductoribus*)

**What it is / why you want it.** The conceptual framework that turns "some stones rectify" into "we can engineer a device on purpose." This costs a scribe and paper (or wax, or papyrus), and nothing else, and it is the largest single time-saving in the whole programme: it took the real world roughly 1900-1947 to work this out.

**Why you would never guess this.** You would not guess it: you already know it. The task is transcription and preservation across centuries of copying, not discovery.

**Prerequisites.** None beyond literacy and a durable medium; ideally multiple redundant copies in different archives, since this is the one entry a fire or a bad papyrus batch must never be allowed to erase.

**Roman-available inputs.** Papyrus, wax tablets, and eventually parchment codices, for redundant copies; trusted scribes sworn to accurate, verbatim copying of technical diagrams.

**Procedure, i.e. what to write.**
1. Band structure: in a solid, electrons occupy a filled valence band and an empty conduction band separated by an energy gap; whether a material conducts, insulates, or does something in between depends on how large that gap is and whether electrons can be pushed across it. Germanium's gap is small (roughly 0.67 electron-volts); silicon's is larger (roughly 1.1 electron-volts). These are numbers you carry, not numbers Rome can measure yet; state them as given facts to be confirmed once instruments exist.
2. Intrinsic versus extrinsic: a perfectly pure crystal (intrinsic) conducts poorly, weakly, and worse as it cools. Deliberately adding tiny, controlled traces of the right impurity (extrinsic, i.e. doping) changes conduction by orders of magnitude and makes it controllable on purpose.
3. Donors and acceptors: atoms with one more outer electron than germanium (phosphorus, arsenic, antimony, from the same column as nitrogen) donate a spare electron into the crystal when substituted in; this makes n-type material, majority carriers are electrons. Atoms with one fewer outer electron (boron, aluminum, gallium, indium) accept an electron, leaving a mobile "hole," a missing electron that behaves like a positive charge carrier; this makes p-type material, majority carriers are holes.
4. Majority and minority carriers: n-type material's overwhelming carrier population is electrons (majority) with a tiny population of holes (minority) always present too, and vice versa for p-type. Both populations matter; devices are built on what happens to the minority population.
5. The p-n junction: where n-type and p-type material meet, majority carriers diffuse across and recombine near the boundary, leaving a thin depletion region with a built-in electric field. That field lets current flow easily in one direction (forward bias) and blocks it in the other (reverse bias), a rectifier by design, the same asymmetry the galena crystal shows by accident.
6. Minority carrier injection: forward-bias a junction hard enough, and it does more than pass current, it injects minority carriers (holes, from the p-side, into the n-side, say) into the neighbouring region in large numbers. Those injected carriers diffuse through the material before recombining.
7. Transistor action: place a second junction close enough (within the diffusion distance of the injected minority carriers, a fraction of a millimetre in germanium) to the first, and it can collect those diffusing carriers before they recombine. A small change in the first junction's forward bias controls a much larger current collected at the second: amplification. Everything from `point_contact_transistor` onward is an engineering answer to "how do we build two junctions that close together, reliably."

**How you know it worked.** You cannot test any of this until `galena_detector`, `semiconductor_metrology` and workable germanium exist, possibly decades after you write it. That is expected and acceptable: the writing is insurance against forgetting, not a claim of proof.

**Failure modes.** The greatest risk is loss: a single copy lost to fire, damp, or a careless copyist. Commission at least three independent copies in different cities from the outset.

**Cost & labour.** ESTIMATED 2-6 months of your personal time to write this clearly with worked diagrams, plus scribal copying costs, ESTIMATED under 100 denarii total. This is by a wide margin the cheapest entry in this module and arguably in the entire programme.

**Danger.** None physical. Socially, written claims about invisible "carriers" and "bands" with no demonstrable proof for decades will read as philosophy or fantasy to contemporaries; frame it explicitly as a sealed technical archive for future workers, not a public claim, to avoid ridicule undermining your credibility on the things you can demonstrate now (`galena_detector`, `vacuum_tube`).

**Confidence: HIGH.** This is settled, textbook 20th-century solid-state physics; the only uncertainty is how faithfully it survives transcription across centuries, which is a social, not a scientific, risk.

---

### germanium_sourcing - Finding germanium at all (*plumbum cinereum*, informal)

**What it is / why you want it.** Germanium is the practical bootstrap semiconductor: lower melting point and simpler chemistry than silicon. The problem is that it essentially never occurs as its own workable ore anywhere you can reach.

**Why you would never guess this.** Germanium is common enough in the crust, roughly ESTIMATED 1.6 parts per million (a Winkler-era, later-confirmed figure), to seem findable, but it is chemically dispersed rather than concentrated, so there is no "germanium mine" to go looking for. You must go through someone else's ore.

**Prerequisites.** Zinc smelting or sulfide-ore roasting operations, or coal-ash access, plus later `zone_refining` and `single_crystal_growth` to turn found germanium into usable device material.

**Roman-available inputs.**
1. Sphalerite (zinc sulfide, ZnS) ore concentrates: germanium substitutes for zinc in the crystal lattice at roughly tens to a few hundred parts per million in some deposits, ESTIMATED, higher in some Spanish and Balkan zinc districts.
2. Flue dust from zinc roasting and smelting, the best realistic source: germanium volatilizes preferentially during roasting and concentrates in the flue dust and condensate, historically reaching roughly 0.1-2% germanium by weight in favourable flue dusts, ESTIMATED, an order of magnitude or more richer than the raw ore. Any Roman zinc- or brass-cementation operation (brass making is Roman-attested) produces flue dust; start collecting and testing it rather than hunting for a mythical germanium ore.
3. Certain coal ashes: some coal seams carry germanium at up to several hundred parts per million to over 1% in the ash after burning, ESTIMATED, a real but unpredictable and location-specific source, worth testing wherever coal is burned in quantity.
4. Argyrodite (silver germanium sulfide, Ag8GeS6), roughly 6-7% germanium by weight, MEASURED, the mineral in which germanium was first identified (Winkler, Freiberg, Saxony, 1886). Freiberg lies in free Germania, outside imperial borders but within trade reach via the amber-road network and Germanic client contacts; expect real diplomatic and logistical friction, not a simple purchase.
5. Germanite (a copper-germanium sulfide ore), roughly 1-8% germanium, MEASURED, found at Tsumeb in modern Namibia. This is effectively unreachable for your programme: no Roman trade route runs remotely near sub-Saharan south-west Africa. Note it, do not plan around it.

**Procedure, separation chemistry.**
1. Roast the zinc flue dust or sulfide concentrate to convert sulfides to oxides and chlorides where present.
2. Treat with concentrated hydrochloric acid (from vitriol plus salt, or from sulfur-chlorine chemistry established in earlier modules); germanium converts to germanium tetrachloride, GeCl4, a liquid that boils at roughly 86°C, remarkably low and remarkably useful.
3. Fractionally distil the crude chloride liquor. GeCl4's low boiling point separates it from far higher-boiling zinc chloride (boils roughly 732°C) and iron chloride, and requires repeated redistillation, ESTIMATED 10-20 passes, to separate it from the one close interferent, arsenic trichloride (boils roughly 130°C). This is the same still-and-column technique used for distilling other liquids in earlier modules, applied to a new liquid.
4. Hydrolyze the purified GeCl4 with water: it reacts readily, precipitating germanium dioxide, GeO2, and releasing hydrochloric acid you can recover and reuse.
5. Reduce the GeO2 with hydrogen gas at roughly 650°C in a tube furnace, yielding grey metallic germanium powder or sponge.

**Why the chloride is the door.** Germanium metal and germanium dioxide are both solids with no easy purification path at this level of chemistry, you cannot fractionate a powder. Germanium tetrachloride is a volatile liquid you can fractionally distil exactly like separating brandy from wash, over and over, until the arsenic and everything else is reduced to a trace. This single property, that the impure intermediate happens to be a low-boiling liquid, is what makes germanium tractable at all.

**How you know it worked.** GeO2 precipitate is white and gelatinous; reduced germanium sponge is dull grey-black, brittle, and should show measurable but modest conductivity when tested with `50_electricity.md`'s galvanometer, well below a true metal's, well above a true insulator's.

**Failure modes.** Incomplete distillation leaves arsenic behind, poisoning later devices. Under-reduction leaves oxide mixed with metal, giving unreliable, high-resistance lumps.

**Cost & labour.** ESTIMATED: mining and roasting labour as for any smelting operation; the distillation itself is ESTIMATED 200-400 artisan-hours per batch to reach adequate purity by repeated passes, plus significant acid and glassware consumption. Yield from flue dust: ESTIMATED single-digit grams of purified germanium per large batch of dust, this is a precious-metal-scale operation, not a bulk one.

**Danger.** Hydrochloric acid and chlorine-bearing fumes are severely corrosive to lungs and eyes; work this in a ventilated shed, never indoors. Arsenic trichloride, the main contaminant, is a lethal poison; treat all distillation residues as hazardous waste, buried away from water sources.

**Confidence: MEDIUM.** The chemistry (GeCl4 route, boiling points, reduction temperature) is HIGH confidence, MEASURED 19th-20th century industrial chemistry. The exact concentrations achievable from Roman-era zinc flue dust and coal ash are ESTIMATED by analogy to later industrial sources; real Roman ore assays will vary.

---

### zone_refining - Pfann's travelling molten zone (*purgatio per zonam*, informal)

**What it is / why you want it. ** A narrow molten band, moved slowly along a solid bar of germanium, sweeps almost all remaining impurities to one end. Repeated passes push the clean end's purity to levels no chemical method can reach. Without this step, germanium sourced and chemically purified per `germanium_sourcing` is still not clean enough to make a working transistor.

**Why you would never guess this.** That melting only a thin slice at a time, and moving that slice slowly down the bar, would concentrate impurities rather than just redistribute them evenly, depends on a subtle fact: most impurities dissolve more readily in molten germanium than in solid germanium, so as a zone freezes behind it, it rejects impurity into the still-molten region ahead. This is not something you would stumble on; Pfann worked it out in 1952, after the transistor already existed.

**Prerequisites.** `germanium_sourcing` (chemically reduced germanium metal), `vacuum_pumps` or an inert/hydrogen atmosphere, high-purity graphite or fused quartz vessels.

**Roman-available inputs.** Reduced germanium sponge or ingot. Fused quartz tubing (silica glass, achievable with sufficiently hot, sufficiently pure glassblowing) or high-purity graphite, from carefully selected, ash-poor charcoal or coke-equivalent carbon, worked into a shallow boat shape. Hydrogen gas (from acid reacting with iron or zinc, a standard 19th-century-style generator) for the furnace atmosphere.

**Procedure.**
1. Melt the germanium (melting point 938°C) and cast it into a bar inside a graphite or fused-quartz boat.
2. Seal the boat inside a quartz tube, either evacuated with `vacuum_pumps` or continuously flushed with dry hydrogen, to keep the molten surface from oxidizing.
3. Heat only a narrow band, roughly a centimetre or two wide, of the bar to melting, using a small, sharply localized furnace or induction coil, while the rest of the bar stays solid.
4. Move that molten zone slowly along the full length of the bar, ESTIMATED 5-20 cm per hour, either by moving the heater or by drawing the boat through it.
5. Most impurities have a segregation coefficient below one in germanium, meaning they prefer to stay in the liquid rather than the freshly freezing solid behind the zone; as the zone travels, it effectively sweeps impurities along with it toward one end of the bar.
6. Repeat the pass, same direction, many times, ESTIMATED 10-30 passes, each pass driving the impurity concentration at the clean end down further. Cut off and discard the impurity-rich end after the final pass.

**How you know it worked.** Resistivity measured along the bar with `semiconductor_metrology`'s four-point probe should rise sharply, indicating fewer free carriers from fewer impurity atoms, toward the clean end after successive passes; a working feedback loop, not a one-shot process.

**Failure modes.** Boat material contaminates the melt if it is not high-purity graphite or quartz, ordinary clay or ceramic crucibles leach silicon, aluminum, or worse into the germanium and defeat the entire purpose. Zone moves too fast: impurities do not have time to segregate properly. Atmosphere leaks air in: molten germanium oxidizes at the surface, ruining that pass.

**Cost & labour.** ESTIMATED significant furnace-operator time per bar, days of continuous, carefully controlled heating per multi-pass run, plus the cost of quartz or graphite vessels that themselves require a mature ceramics or glass programme to produce reliably.

**Why no chemical method suffices, stated plainly.** Chemical purification (`germanium_sourcing`) gets you from an ore trace to a workable metal, roughly to the level chemists can measure by ordinary means. Zone refining, historically, pushed germanium purity to roughly one part impurity in ten billion parts germanium, far beyond anything achievable by distillation, precipitation, or any wet chemistry. This physical segregation trick is not optional polish, it is the step that makes a semiconductor device possible at all; skip it and every transistor attempt downstream will fail from stray, uncontrolled impurities acting as unintended, unwanted dopant.

**Danger.** Molten germanium and high-temperature furnace work carry standard burn and fire risk. Hydrogen atmosphere is explosive if mixed with air; purge the tube thoroughly before and after each run, no open flame near the generator.

**Confidence: HIGH** on the physical principle and the historical purity figures (MEASURED, Pfann's published results); MEDIUM on achievable pass counts and rates with Roman-era furnace control, which will be cruder than 1950s laboratory equipment.

---

### single_crystal_growth - Pulling a single crystal from the melt (*cristallus tractus*, informal)

**What it is / why you want it.** Growing the zone-refined germanium into one continuous, unbroken crystal lattice, rather than letting it freeze as many small randomly oriented crystals (polycrystalline), is what makes a working transistor possible, not merely a pure piece of germanium.

**Why you would never guess this.** That the internal boundaries between tiny crystal grains, invisible without magnification, would completely destroy a device's function even in chemically perfect material, is deeply counterintuitive: the material looks and tests as pure either way by ordinary chemical assay.

**Prerequisites.** `zone_refining` (ultra-pure germanium), `semiconductor_metrology` (to confirm doping and check crystal quality), precise weighing equipment, a stable furnace and a mechanism for slow, controlled vertical pulling and rotation.

**Roman-available inputs.** Zone-refined germanium ingot, a small oriented seed crystal (your first ones from an early zone-refined bar, kept and used to seed later, better pulls), weighed dopant elements (phosphorus, arsenic or antimony for n-type; boron, aluminum, or indium for p-type), a graphite or fused-quartz crucible.

**Procedure, the Czochralski method (Czochralski, 1916, applied to germanium circa 1948-1950).**
1. Melt zone-refined germanium in a graphite or fused-quartz crucible at 938°C, in the same protected atmosphere used for zone refining.
2. Add a precisely weighed trace of your chosen dopant to the melt, targeting parts-per-million concentrations; this requires an analytical-grade balance, itself a serious instrument-making project.
3. Lower a small seed crystal, of known crystal orientation, until it just touches the melt surface.
4. Slowly withdraw the seed upward, ESTIMATED 1-10 mm per minute, while rotating it, ESTIMATED a few to a few tens of revolutions per minute, to average out any temperature asymmetry in the furnace.
5. As it is withdrawn, germanium freezes onto the seed in the same crystal orientation, growing a single continuous cylindrical boule, doped uniformly by whatever concentration was set in the melt.

**How you know it worked.** A good boule looks smooth and has a lustrous, unbroken metallic surface, no visible facet jumps or cracks along its length. Slice it and test resistivity at several points with the four-point probe (`semiconductor_metrology`): a good single crystal gives smoothly varying, predictable resistivity; a polycrystalline or poorly grown boule gives erratic, patchy readings.

**Why grain boundaries are fatal, not just undesirable.** A boundary between two differently oriented crystal grains is dense with broken, unsatisfied chemical bonds. These act as traps that capture and instantly recombine minority carriers, the very carriers `semiconductor_theory` says a transistor depends on surviving long enough to diffuse across a junction. Carrier lifetime near a grain boundary can crash from the microseconds needed for a working device to nanoseconds, useless. This holds however chemically pure the polycrystalline material is; purity and crystallinity are two separate requirements, and polycrystalline germanium, however many zone-refining passes it has had, will never make a working transistor.

**Failure modes.** Pulling too fast: crystal grows with multiple grains or facets, effectively polycrystalline. Temperature unstable: boule necks down or breaks off. Dopant weighed incorrectly: wrong carrier type or concentration, discovered only at the metrology step.

**Cost & labour.** ESTIMATED weeks of furnace-operator and instrument-maker time per successful pull, with a low early success rate; treat the first dozen or more boules as development losses.

**Danger.** As `zone_refining`: burns, furnace hazards, atmosphere control. Dopant handling: arsenic and its compounds are toxic, weigh and handle with the same care as any poison.

**Confidence: MEDIUM.** The Czochralski method and the grain-boundary/carrier-lifetime physics are HIGH confidence, MEASURED science. Pull rates and yields achievable with Roman-built pulling rigs are ESTIMATED, likely worse than 20th-century laboratory results at first.

---

### semiconductor_metrology - Measuring what you have made (*mensura resistentiae*, informal)

**What it is / why you want it.** Two instruments, the four-point probe and the Hall effect apparatus, tell you the resistivity, carrier type, and carrier concentration of a piece of germanium. Without these, purification and doping are blind guesswork; with them, every zone-refining pass and every doped crystal pull becomes a measured, converging process instead of a hopeful one.

**Why you would never guess this.** The four-point probe's trick, that using four separate contacts rather than two eliminates the unknown contact resistance of the probe tips themselves, is a specific, non-obvious circuit design; you would naturally reach for two contacts and get a hopelessly contaminated reading dominated by the contacts, not the material.

**Prerequisites.** `50_electricity.md` (precision galvanometer, stable low-current source), a small permanent or electromagnet for the Hall measurement, fine wire for probe contacts.

**Roman-available inputs.** Four fine, evenly spaced metal probe tips (phosphor bronze or similar spring wire, as in `galena_detector`) on an insulating mount; a small horseshoe magnet (lodestone or electromagnet); `50_electricity.md`'s meters and stable current source.

**Procedure, four-point probe.**
1. Press four collinear, evenly spaced probe tips onto the flat, polished surface of the germanium sample, spacing s between adjacent tips.
2. Force a known small current I through the two outer tips from `50_electricity.md`'s stable source.
3. Measure the voltage V that appears across the two inner tips.
4. For a sample large relative to the probe spacing, resistivity is approximately rho equals 2 times pi times s times V divided by I; smaller or thinner samples need a geometric correction factor, determined by comparing against a sample of known resistivity.

**Procedure, Hall effect.**
1. Pass a steady current through a thin, regularly shaped sample of the germanium.
2. Apply a magnetic field perpendicular to that current, using the horseshoe magnet.
3. Measure the small transverse voltage (the Hall voltage) that appears across the sample, perpendicular to both the current and the field.
4. The sign of that voltage tells you directly whether the majority carriers are electrons or holes, n-type or p-type. Its magnitude, combined with the known current, field strength, and sample thickness, gives the carrier concentration.

**How you know it worked.** Results should be reproducible: the same sample, measured twice, gives the same resistivity and carrier type. A properly zone-refined, then correctly doped, sample should show resistivity and carrier type matching what you targeted when you weighed the dopant into the melt.

**Failure modes.** Poor probe contact (oxidized tips, uneven pressure) gives noisy, inconsistent readings. Sample too small or too thin relative to probe spacing without applying the correction factor gives a systematically wrong resistivity.

**Cost & labour.** ESTIMATED a few days of instrument-maker time to build a usable probe rig and Hall fixture once `50_electricity.md`'s meters exist; this is cheap relative to what it saves.

**Why this closes the loop.** Every earlier entry in this module, distillation passes, zone-refining passes, dopant weighing, is a blind operation without a number coming back at the end. Once resistivity and carrier type can be measured directly on a sample, each additional pass or trial tells you whether you are converging on usable material or wasting mercury, charcoal, and months. This measurement capability is what turns purification from an act of faith into an engineering process.

**Danger.** Minor: standard electrical handling per `50_electricity.md`.

**Confidence: HIGH.** Both techniques are well-established, MEASURED 20th-century instruments with simple physical principles; achievable precision with Roman-grade meters and magnets is MEDIUM confidence.

---

### point_contact_transistor - The first transistor (*punctum amplificans*, informal)

**What it is / why you want it.** Two fine metal points, pressed onto a small slab of n-type germanium a fraction of a millimetre apart, form a device where a small current into one point controls a much larger current at the other: real amplification, real gain, the device that ends this module's programme.

**Why you would never guess this.** Bardeen and Brattain themselves were investigating a different, failed device (a field-effect design Shockley had proposed) when they stumbled onto point-contact amplification while testing surface effects on germanium in 1947; even with the theory in hand, the working geometry is not obvious. This is the one entry where having `semiconductor_theory` in advance saves you the most: you already know to look for exactly this.

**Prerequisites.** `single_crystal_growth` (n-type germanium single crystal, doped, ESTIMATED with arsenic or antimony), `semiconductor_metrology` (to confirm the slab's carrier type and resistivity before use), fine phosphor bronze wire, `50_electricity.md` (small stable current source for the "forming" step and for bias).

**Roman-available inputs.** A single-crystal n-type germanium slab, roughly 1 cm by 1 cm by a few millimetres thick (MEASURED, comparable to the original device). Two phosphor bronze point contacts, mounted on a small insulating wedge (plastic in the original 1947 device; a hard resin, wax-impregnated wood, or fired ceramic wedge should serve), spaced roughly 0.05 mm (50 micrometres) apart, achieved historically by cutting a single gold foil contact with a razor blade to split it into two closely spaced points; the same razor-split technique should work with fine bronze foil or wire.

**Procedure.**
1. Confirm the germanium slab is single-crystal, n-type, with `semiconductor_metrology`.
2. Mount the two point contacts on the wedge, pressed lightly onto the slab's surface, spaced as close as your finest cutting technique allows, ESTIMATED 0.03-0.1 mm.
3. Forming pulse: pass a brief pulse of relatively high current (compared to normal operating current) through one of the point contacts. This locally alters the germanium immediately beneath that contact, historically believed to create a thin p-type region right at that point through local electrochemical action, turning that contact effectively into a small p-n junction against the n-type bulk.
4. Wire the "emitter" contact (the formed one) forward biased, and the nearby "collector" contact reverse biased, both referenced to the bulk n-type slab (the "base").
5. Forward bias on the emitter injects minority carriers, holes, into the n-type base; because the collector is so close, within the diffusion range of those injected holes before they recombine, it collects a large fraction of them.

**How you know it worked.** A small alternating signal applied at the emitter produces a much larger corresponding signal at the collector, measurable on `50_electricity.md`'s galvanometer or, once built, driving `radio_spark_to_valve`'s earpiece audibly louder than the input. MEASURED historical performance: roughly 18 decibels of power gain (a factor of order 20-100 in power), and voltage gain on the order of 100, in the original December 1947 device.

**Failure modes.** Points spaced too far apart: no gain, minority carriers recombine before reaching the collector. Forming pulse too weak: no rectifying region created, device behaves as a plain resistor. Forming pulse too strong: destroys the contact. Mechanical shock: point contacts are extremely position-sensitive and easily jarred out of their sensitive configuration, a direct echo of `galena_detector`'s fragility, and the main reason the industry moved quickly to `junction_transistor`.

**Cost & labour.** ESTIMATED weeks of trial-and-error per working device even with all prerequisite materials in hand, matching the real history: Bardeen and Brattain's team spent roughly a year of dedicated Bell Labs research reaching this point after Shockley's original, different, approach failed. With `semiconductor_theory` already written down, expect this to compress, but not vanish.

**Danger.** None beyond ordinary low-voltage electrical handling.

**Confidence: HIGH** on the physics, geometry, and MEASURED historical performance figures (Bardeen, Brattain, and Shockley, Bell Telephone Laboratories, first demonstrated 16 December 1947). MEDIUM on how long Roman-era hands, without modern micromanipulators, take to achieve the necessary point spacing and forming control.

---

### junction_transistor - Grown and alloy junctions (*iunctio amplificans*, informal)

**What it is / why you want it.** Replacing the fragile, hand-positioned point contacts with junctions built directly into the crystal, first by growing them, then by alloying, gives a rugged, reproducible, manufacturable device instead of a delicate laboratory curiosity.

**Why you would never guess this.** Once you have `point_contact_transistor` working and understand it through `semiconductor_theory`, this is a natural engineering refinement, not a conceptual leap: the theory already tells you a p-n junction with a nearby second junction is what matters, not specifically that it be two sharp metal points.

**Prerequisites.** `point_contact_transistor` (proof that the effect works), `single_crystal_growth`, `semiconductor_metrology`.

**Roman-available inputs.** N-type germanium single crystal or melt (as `single_crystal_growth`), p-type dopant (indium, for alloy junctions), n-type and p-type dopants in sequence (for grown junctions).

**Procedure, grown junction (Teal and Sparks, 1950).**
1. Begin a Czochralski pull (`single_crystal_growth`) with n-type dopant in the melt.
2. Partway through the pull, add a measured dose of p-type dopant, in excess of the existing n-type dopant, switching the freezing crystal's type.
3. Add n-type dopant again in excess later in the pull, switching back.
4. The result is a single boule with two built-in junctions along its length (n-p-n or p-n-p) at known positions, sliced out afterward.

**Procedure, alloy junction (1951).**
1. Take a thin wafer of n-type single-crystal germanium.
2. Place a small pellet of indium (a p-type dopant that also melts at a convenient temperature, well below germanium's melting point) on each face of the wafer.
3. Heat briefly to melt the indium into the germanium surface on each side, recrystallizing a thin p-type region as it cools, giving a p-n-p structure with two junctions defined by where the molten indium penetrated.

**Why this is far more manufacturable.** No point contact has to be positioned by hand to within a fraction of a millimetre and kept there against vibration. Junction depth and spacing are set by pull timing or pellet placement and melt duration, both far more controllable and repeatable than manual point placement. The resulting device tolerates more current, more mechanical handling, and gives more consistent gain from unit to unit, which is why this quickly became the standard commercial form historically.

**How you know it worked.** As `point_contact_transistor`: measurable current and power gain between the outer regions (emitter, collector) controlled by the middle region (base), tested with `50_electricity.md`'s instruments.

**Failure modes.** Grown junction: dopant switch not sharp enough (gradual transition instead of a clean junction), weak or no gain. Alloy junction: indium pellet too large or overheated, penetrates too far, shorts the two junctions together.

**Cost & labour.** ESTIMATED comparable to or somewhat less than `point_contact_transistor` once `single_crystal_growth` and dopant-weighing practice are established, with much higher yield per attempt, since there is no delicate point-spacing step.

**Danger.** As prior entries: furnace burns, dopant toxicity (indium is comparatively mild, but treat with standard metal-handling care).

**Confidence: HIGH.** MEASURED historical devices (Teal and Sparks, Bell Labs, 1950; alloy junction, 1951), well documented, straightforward extensions of the prerequisite techniques.

---

### silicon_path - The alternative substrate, and why to defer it (*silex amplificans*, informal)

**What it is / why you want it.** Silicon eventually replaced germanium in the real world's industry, for good reasons, larger bandgap giving better high-temperature behaviour, and near-total crustal abundance. It is not the right first target for a two-century bootstrap.

**Why you would never guess this.** It looks backwards to choose the rarer material first; the reason is that Roman-era furnace and crucible technology struggles far more with silicon's demands than with germanium's.

**Prerequisites.** Same overall chain as germanium (`vacuum_pumps` through `semiconductor_metrology`), plus better refractory crucible chemistry than germanium needs.

**Roman-available inputs.** Silicon is abundant, roughly 27% of the crust by mass, present in essentially all sand and clay; no exotic sourcing problem exists here, unlike `germanium_sourcing`.

**Honest comparison.**
1. Melting point: germanium 938°C, well within reach of a good bellows-blown charcoal furnace (roughly 1200°C hand-blown, 1500°C water-blown, per the general thermal note in this guide's rules). Silicon melts at 1414°C, near the top of what a water-blown charcoal furnace can sustain reliably for the hours a Czochralski pull requires.
2. Crucible chemistry: molten silicon is aggressively reactive with most refractories at its melting point, attacking ordinary fused quartz far more than germanium does; achieving a crucible that survives repeated silicon melts without contaminating the melt is a harder materials problem than germanium's graphite-or-quartz boat.
3. Purification route: silicon's analogue of `germanium_sourcing`'s volatile chloride door is trichlorosilane, SiHCl3, made by passing hydrogen chloride gas over heated silicon at roughly 300°C, boiling at roughly 32°C, fractionally distilled, then reduced with hydrogen at high temperature to deposit ultra-pure silicon (the historical Siemens process). This is a real, workable route, but adds another gas-handling and high-temperature-reduction step beyond germanium's chain.
4. Payoff: silicon's larger bandgap (roughly 1.1 eV versus germanium's roughly 0.67 eV) gives devices that tolerate higher operating temperatures before failing, a real advantage for a mature industry, but irrelevant to proving the concept works at all.

**Recommendation.** Build the germanium chain first (`germanium_sourcing` through `junction_transistor`). Its lower melting point is a materially easier furnace problem at Roman technological maturity, its purification chemistry is precedented and comparatively simple, and it is the historically proven first path (1947-1951). Treat silicon as a second-generation project, to be attempted only once your furnace, crucible, and vacuum infrastructure from the germanium programme are mature and well understood, likely decades after the first working germanium transistor.

**How you know it worked.** As `point_contact_transistor` and `junction_transistor`, applied to a silicon slab or wafer instead of germanium.

**Failure modes.** Crucible contamination from silicon's aggressive high-temperature chemistry is the dominant, distinctive failure mode beyond what germanium already presents.

**Cost & labour.** ESTIMATED comparable artisan-hours to the germanium chain per step, but with a materially higher furnace and crucible-development cost up front, owing to the higher operating temperature.

**Danger.** Trichlorosilane and hydrogen chloride gas handling: severely corrosive and toxic; identical precautions to `germanium_sourcing`'s chlorine chemistry, ventilate thoroughly, never work indoors.

**Confidence: MEDIUM.** The chemistry and comparison figures are HIGH confidence, MEASURED. Which path is genuinely faster for a Roman-era programme specifically is ESTIMATED reasoning, not a measured historical fact, since history never ran the germanium-first, silicon-second choice under these constraints.

---

## The endgame dependency chain

In order, what must exist before a transistor can exist:

1. `50_electricity.md`: batteries, dynamo, insulated wire, meters (galvanometer). Everything else draws current or measures current from this module.
2. `semiconductor_theory`, written down in your first decade. Costs almost nothing, saves the most.
3. `galena_detector`, built within roughly five years, the proof of concept that funds everything after it.
4. Glassblowing and clear glass (assumed prior module), matured enough to blow sealed, evacuated envelopes.
5. `vacuum_pumps`, piston then Sprengel, plus the McLeod gauge and phosphorus getters.
6. `crookes_xray_electron`: discharge tubes, confirming the electron and X-rays as instruments, not discoveries.
7. `vacuum_tube`: diode, then triode, requiring the Dumet-equivalent alloy seal, the single hardest metallurgical sub-problem in the chain.
8. `radio_spark_to_valve`: a working communications system, both a funding and prestige driver and a proving ground for tuned circuits and amplifiers you will reuse.
9. `germanium_sourcing`: zinc flue dust or argyrodite located and traded for, GeCl4 distillation chemistry mastered.
10. `zone_refining`: quartz or graphite vessel-making, atmosphere control, patience across dozens of passes.
11. `single_crystal_growth`: precision pulling mechanism, weighed dopants, an analytical balance.
12. `semiconductor_metrology`: four-point probe and Hall apparatus, without which steps 9-11 are blind.
13. `point_contact_transistor`, then `junction_transistor`.
14. Optionally, decades later, `silicon_path`.

**How many trained people this needs, ESTIMATED.** Not a handful of workshop hands: this is a standing, multi-generational technical establishment. Reckon on roughly 150-300 skilled specialists sustained at any one time across the full supporting chain: miners and ore-sorters (lead, zinc, coal), glassblowers and lampworkers, ceramicists making fused quartz and refractory crucibles, metallurgists and alloy-smiths (Dumet-equivalent wire, phosphor bronze), acid- and chlorine-chemistry workers, furnace operators, instrument makers (pumps, gauges, probes, meters), precision mechanics (pulling rigs, adjustment screws), and scribes maintaining the theory archive across copies and generations. This is comparable in scale to a legion's engineering corps or an imperial mint, concentrated in two or three dedicated workshops under direct, continuous patronage, not a single inventor's garage. Expect apprenticeship chains of masters training successors across the full roughly two-century span, since no one person lives to see `semiconductor_theory` (year 1-10) through to `junction_transistor` (realistically a century or more later at Roman-era development speed).

---

## Sources and confidence

MEASURED historical figures (Sprengel pump design and performance, McLeod gauge, Crookes/Röntgen/Thomson discharge tube work, Bell Labs point-contact transistor of 16 December 1947 and its gain figures, Teal and Sparks' 1950 grown junction and the 1951 alloy junction, Pfann's 1952 zone refining and its purity results, Czochralski's 1916 pulling method, argyrodite's discovery by Winkler at Freiberg in 1886 and its germanium content, germanium and silicon melting points and bandgaps, boiling points of GeCl4 and SiHCl3) are drawn from standard solid-state physics and electronics references (in the spirit of Sze's semiconductor device texts) and standard histories of the transistor (in the spirit of Riordan and Hoddeson's account of Bell Labs). These are HIGH confidence.

ESTIMATED figures (Roman-era achievable vacuum levels, artisan-hours, exact germanium concentrations in Roman-accessible flue dusts and ores, pass counts and pull rates achievable with hand-built Roman apparatus, the size of the supporting workforce) are reasoned extrapolations from the measured historical base cases, adjusted down for cruder materials and tooling, and are flagged as such throughout. Treat every ESTIMATED number as a planning assumption to be corrected by `semiconductor_metrology`'s actual readings once the apparatus exists, not as a fact to build irreversible decisions on.

Overall module confidence is MEDIUM: the underlying science is HIGH confidence and completely settled, the Roman-era engineering path to realize it is a reasoned but unverified extrapolation.
