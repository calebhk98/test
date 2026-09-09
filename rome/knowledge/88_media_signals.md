# Module 88: Media, Signal and Memory

## Why these hundred have no entry anywhere else

These hundred technologies have costs and prerequisites in the tree but no build guide, because most are not chemistry or metallurgy, they are precision mechanics plus organisation, and the guide's other modules walk past them toward furnaces. A furnace is dramatic. A composing stick is not. But the composing stick lets one man outproduce a scriptorium of forty monks, and the punched card lets one clerk do what a hundred clerks did.

Two kinds appear below. The first is Roman-buildable now: papyrus, iron gall ink, the screw press, the crude telegraph relay. The second needs something Rome flatly lacks, usually a hard vacuum, a fine uniform powder, or a specific tropical latex, and each of those has an explicit note on where the missing piece lives.

Read the danger lines. Nothing else in this guide is as likely to get you killed by people rather than physics. A furnace that fails kills you. A press that runs kills the scribal economy's confidence in you, and a frightened elite is worse than a bad furnace, because it thinks.

---

## Part One: the book before the press

### if_papyrus - Papyrus sheet (*papyrus, biblus*)

**What it is.** Rome's standard writing surface, from *Cyperus papyrus* pith, Nile Delta and Faiyum. You already have it; it is here so the two things built from misunderstanding it make sense.

**Why you would never guess this.** Papyrus never becomes pulp. Strips of pith laid crosswise, wetted, and pressed; the plant's own sap glues the layers as they dry. Beat it like rag pulp and you destroy it.

Also covers: if_parchment, if_rag_paper, if_bookbinding_case.

**Parchment** (*pergamena*) is skin unhaired in a lime bath (2-3 weeks, turned daily), scraped, then dried stretched, never tanned; too much lime dissolves the collagen, too little leaves hair. Takes correction by knife-scrape, which papyrus cannot survive.

**Rag paper** is China's invention (Cai Lun, c.105 AD), not traded west for centuries; reinvent it by fulling linen rag to pulp until fibres **fray** (not merely soften, see `90_textiles.md`), diluting in a vat, lifting a wire-mesh mould through it, couching, pressing, drying.

**Case binding**: sewn signatures through cords laced into boards survive centuries; glue alone fails in years. Raised bands protect the sewing from shear.

**Prerequisites.** `mat_papyrus`; `mat_parchment`; `mat_paper` plus fulling; `cap_tol_1mm`.

**Cost & labour.** ESTIMATED. A scribe copies 2-3 columns/hour; papyrus roughly a denarius per roll in Egypt, several times that shipped to Rome; parchment several times papyrus per equivalent area.

**Danger.** None. Build these first; no enemy is made by a better writing surface.

**Confidence: HIGH** for papyrus/parchment (attested daily use); **MEDIUM** for reinvented rag paper.

---

### if_movable_type - Movable type, cast metal (*typi mobiles*)

**What it is.** Casting thousands of identical metal letters that lock into a page and print thousands of impressions. The highest-leverage node in the tree for outrunning a magistrate's ability to suppress an idea.

**Why you would never guess this.** The hard part is not the letter, it is that every piece of type must be the same height to a fraction of a millimetre or it does not print at all: tall pieces black, short ones blank. Gutenberg's invention was the **adjustable hand mould**: a punch (hardened steel, letter cut mirror-reversed) strikes a matrix (copper or brass) to leave a precise negative, which drops into a spring-adjustable mould casting every letter to one fixed body height regardless of width. One punch, unlimited identical type.

Also covers: if_punch_and_matrix, if_type_mould, if_type_metal_alloy, if_linotype_machine.

**Prerequisites.** `cap_tol_100um`, `mat_brass`, `cap_heat_1100`.

**Roman-available inputs.** Lead (*plumbum*, Britain/Spain), tin (*stannum*, Cornwall), antimony (*stibium*, Anatolia). Lead alone is too soft; tin hardens; antimony **expands** slightly on cooling, filling the mould instead of shrinking from it. DERIVED ratio from later foundry practice: roughly 4 lead : 1 tin : 1 antimony.

**Procedure.** Cut punch square and mirror-reversed; strike vertically into matrix blank; true the matrix; ladle molten alloy (cherry-red to orange, ~240-300 C) into the mould, jerk once, eject; repeat per letter. A straightedge across ten sorts of one letter should show no rock, no light under any.

**Failure modes.** Uneven height prints patchy. Cold metal gives a short cast; overheated metal etches the matrix.

**Linotype**: matrices fall from a magazine by keystroke; each has a unique notch pattern letting a rotating distributor bar sort it home automatically. One operator replaces roughly six hand compositors (MEASURED, standard trade figure); needs interchangeable-parts precision, a tier-4 destination, not a start.

**Cost & labour.** ESTIMATED, DERIVED from Gutenberg-scale shops: a full font (~300 sorts, thousands of pieces) is 2-3 punchcutter-months plus a month's casting; several thousand denarii capital.

**Danger.** Physical: molten splash, lead fume, ventilate. Social, and this is the largest danger in the module: a scriptorium's income and a rhetor's status depend on copying staying scarce, and a press turning a month's work into an afternoon destroys that logic outright. Read `03_SOCIAL_POLITICS.md` first: this is the technology most likely to get its founder denounced, because everyone who matters sees instantly what it does to them. Still worth doing early, since everything downstream in this guide depends on enough literate people to use it. Build under a patron's name and disperse the corpus (`80_information_printing.md#corpus_dispersed`) before anyone official notices.

**Confidence: HIGH** on the metallurgy; the danger read is inference from `03_SOCIAL_POLITICS.md`'s pattern, not one attested case.

---

### if_printing_ink - Printing ink, oil-based

**What it is.** Ink that sticks to metal type and transfers cleanly under press pressure, without which movable type is a curiosity.

**Why you would never guess this.** Every ink a scribe knows, carbon or iron gall, is watery and beads off polished metal type. This is a paint problem, not a writing one: you need a sticky, oil-based varnish that clings to metal and does not spread sideways, and it defeated printers for years after they had working type.

Also covers: if_composing_stick, if_chase_and_forme, if_woodblock_printing.

**Prerequisites.** `cap_heat_1100`, `mat_olive_oil` (or linseed).

**Roman-available inputs.** Linseed/walnut oil, boiled; lampblack (*fuligo*, lamp soot); pine resin (*colophonia, pix*) for tack.

**Procedure.** Boil oil slowly, uncovered, to a thick varnish that strings between two fingers (~260-300 C, "flows like honey"); stir in resin hot; grind in lampblack on a stone until gritless; store sealed, skim any skin before use.

**Failure modes.** Under-boiled: never sets, stays sticky. Over-boiled: skins in the pot. Too little resin: ink squashes sideways, filling letters like "o" solid.

**Composing stick**: a hand-held width-adjustable gauge holding a justified line of type upside-down and mirror-reversed, spring catch holds without crushing. **Chase and forme**: iron frame locking a page with wedges (quoins) so press pressure cannot shift a letter; wood furniture swells with humidity, metal does not. **Woodblock**: China's earlier method, no type, a page carved in relief mirror-reversed from fine plank-cut fruitwood (pear, box); the bottleneck is cutting fine lines without splintering the grain.

**Cost & labour.** ESTIMATED. A run's ink batch (200-300 sheets) is a day's work; under 50 denarii.

**Danger.** Physical: boiling oil is a fire risk. Social: as with the type itself.

**Confidence: HIGH** - textbook oxidative polymerisation, every input Roman-attested.

---

### if_screw_press - Screw press for printing

**What it is.** The machine that squeezes inked type against paper evenly, across a whole page, in one motion.

**Why you would never guess this.** Rome already has this press, the *torcular* for wine and oil. The catch is that a wine press's slow squeeze is wrong for printing; you need one quick, even, whole-page impression, so add a flat platen, a padded tympan, and a frisket masking the margins, hinged to swing over the locked forme.

Also covers: if_iron_hand_press.

**Prerequisites.** `master_screw`, `cap_tol_1mm`, `mat_wrought_iron`.

**Procedure.** Lock forme; ink with a leather dabber; lay paper in the tympan, close the frisket over it, swing onto the forme; run the bed under the platen and pull hard and fast in one motion, release at once.

**Failure modes.** Platen and bed out of parallel print one side dark; too much ink fills letter counters solid.

**Iron hand press**: cast iron (Rome's West has none natively) and a toggle-lever giving almost no advantage through most of the pull, then multiplying force enormously in the last few degrees, peak pressure exactly at contact.

**Cost & labour.** DERIVED from wine-press carpentry: 3-4 carpenter-weeks plus a screw-cutter's day, under 1,000 denarii.

**Danger.** Physical: fingers under a closing platen. Social: same as movable type, this is the visible machine an agent recognises as a press; site it discreetly.

**Confidence: HIGH** for the screw press (direct Roman analogue); **MEDIUM** for the iron version. Han China has blast-furnace cast iron (MEASURED, attested since roughly the 5th century BC), a genuine import; see `10_metallurgy.md` for a cupola-furnace alternative.

---

### if_cylinder_press - Cylinder press

**What it is.** A rotating cylinder rolls paper over the inked forme instead of a flat platen slamming down, sharply speeding printing.

**Why you would never guess this.** A platen applies its whole force to the whole page at once; a cylinder touches only a thin rolling line at any instant, so the same total force covers more ground and feed can be continuous. Even ink coverage on the curve is the trade-off.

Also covers: if_rotary_press.

**Prerequisites.** `if_iron_hand_press`, `cap_power_steam`, `boring_mill`.

**Procedure.** Inked, locked forme on a reciprocating bed; paper feeds around a large iron cylinder rolling over it at steady low pressure; a steam or water-mill drive keeps bed and cylinder in step.

**Failure modes.** A cylinder even slightly out of true prints heavier on one side every revolution.

**Rotary press**: curves the type itself, cast as one stereotype plate around the cylinder, no reciprocating bed at all; register between impressions becomes the critical tolerance.

**Cost & labour.** ESTIMATED, DERIVED from an iron hand press plus steam drive (`93_energy.md`): several thousand denarii, throughput several times a hand press's ~200 sheets/hour.

**Danger.** Physical: power-driven entanglement risk. Social: louder, harder to hide than a hand press.

**Confidence: MEDIUM** - mechanically straightforward once steam power and precision boring exist.

---

### if_stereotype - Stereotype plate

**What it is.** Casting a whole locked page as one solid plate, so several presses can print it at once or it can be stored and reprinted years later without tying up type.

**Why you would never guess this.** Type is finite and every page kept set is type you cannot reuse. Take a mould of the locked forme in wet papier-mache (a "flong"), dry it rigid, then use it as a mould to cast one plate in a single fast pour.

Also covers: if_electrotype.

**Prerequisites.** `if_movable_type`, `mat_lead`, `cap_heat_1100`.

**Procedure.** Beat damp pulp into the forme; dry gently to rigidity; lay the flong in a casting box, pour molten type metal in one continuous pour; trim to type-height.

**Failure modes.** A slow pour leaves air pockets printing as white holes; fast drying cracks the flong.

**Electrotype**: grows a copper shell electrolytically (`50_electricity.md`) onto a wax or lead impression over hours, far crisper edges, but the shell must be backed with lead or it buckles under press pressure.

**Cost & labour.** ESTIMATED. A stereotype plate is roughly a day once the forme exists; electrotype several days, mostly unattended electrolysis.

**Danger.** Low, hot metal and the same social risk as printing generally.

**Confidence: MEDIUM** - stereotype chemistry is simple and attested; electrotype depends on `50_electricity.md`'s current chain, itself gated on zinc.

---

### if_lithography - Lithography

**What it is.** Printing from a flat stone with no carving and no relief at all, pure surface chemistry.

**Why you would never guess this.** Draw with a greasy crayon on porous limestone, dampen the whole stone (water clings to bare stone, is repelled by grease), roll oily ink over it (sticks only to the grease, repelled by the wet stone). No relief does any work; it is entirely chemical.

Also covers: if_chromolithography, if_offset_lithography.

**Prerequisites.** `cap_tol_1mm`, `mat_alum`.

**Roman-available inputs.** The historical stone, fine-grained Solnhofen limestone from Bavaria, lies outside the empire, not a documented Roman quarry good. ESTIMATED: a fine Italian or Anatolian limestone may substitute if it holds an even wetting film; test before a run.

**Procedure.** Polish the slab fine; draw in greasy crayon; etch lightly with dilute nitric acid and gum arabic to fix the grease; before each print, sponge with water then roll with ink; press paper against the stone.

**Failure modes.** A stone drying mid-run picks up ink everywhere ("scumming"); over-etching destroys fine detail.

**Chromolithography**: one stone per colour, registered to a fraction of a millimetre by hand. **Offset**: a rubber blanket carries stone-to-paper, so the image reads correctly (not reversed) and is gentler on the stone, at roughly half the pressure.

**Cost & labour.** ESTIMATED, high for the stone and hand-drawn colour separations, a later shop technology.

**Danger.** Low beyond dilute acid; a stone looks nothing like a scribal tool, less immediate suspicion than a type-filled press.

**Confidence: LOW on the stone source** (unattested in Roman hands); **MEDIUM on the chemistry**.

---

### if_halftone_screen - Halftone screen and dot matrix

**What it is.** The trick letting a press, which lays down only solid ink or none, reproduce a photograph's full range of grey.

**Why you would never guess this.** You cannot print a grey. Ink is there or it is not. Break the image into a fine grid of dots and vary their **size**, not their darkness; large dots read dark, small light, the eye blends them at a distance. The screen is a precisely ruled crossed-line grid, photographed slightly out of focus on purpose, in front of the plate, so blur turns sharp grid lines into graduated dot edges.

Also covers: if_photoengraving.

**Prerequisites.** `cap_tol_10um`, `lens_grinding`.

**Procedure.** Rule two glass plates with fine parallel lines (toward 100-150 lines/inch), fill grooves with pigment, cement the plates with lines crossed at 90 degrees; photograph the original through the screen; develop.

**Failure modes.** Uneven ruling or wrong screen angle between two colour separations gives a visible interference pattern (moire) instead of an image; screen ruling accuracy is the hard physical limit.

**Photoengraving**: coat metal with light-hardening bichromated gelatin, expose through the halftone negative, wash away unhardened gelatin, etch the bare metal so hardened dots stand in relief for the press.

**Cost & labour.** ESTIMATED. Ruling a good screen is weeks for a skilled instrument-maker; reused indefinitely once made.

**Danger.** Low; photoengraving's acid bath is the main hazard.

**Confidence: MEDIUM** - optics are textbook, ruling fine enough needs precision this guide's early tiers lack.

---

### if_mimeograph - Mimeograph

**What it is.** A cheap, press-free way to run a few hundred to a couple of thousand copies from a single master.

**Why you would never guess this.** No ink chemistry and no metal type: a waxed fibrous stencil is written on with a stylus or typewriter, and the letterform's pressure simply displaces the wax, opening the fibre beneath. Ink forced through the open fibre prints onto a fresh sheet; the stencil is a mask, not a mould.

Also covers: if_stencil_duplicator.

**Prerequisites.** `if_typewriter` (or stylus), `mat_nitrocellulose`, `cap_power_muscle`.

**Procedure.** Type or trace onto a waxed stencil backed by a smooth plate; mount it on an ink-fed drum; hand-crank paper through.

**Failure modes.** The stencil degrades after roughly 200 (fine silk-screen) to 2,000 (waxed mimeograph) copies as channels wear larger and print blurs.

**Cost & labour.** ESTIMATED. A stencil is minutes; the duplicator, a drum and crank, is a modest metalworking job, well under any press above.

**Danger.** Social: the module's samizdat technology, no forme, no type, no visible press, run from a back room and dismantled in minutes; use it for anything you cannot afford traced to a fixed shop.

**Confidence: MEDIUM** - simple mechanically, depends on `mat_nitrocellulose` (`20_chemistry.md`) for the stencil coating.

---

## Part Two: the hand and the desk

### if_quill - Quill pen (*penna*)

**What it is.** A flexible pen cut from a flight feather, standard once parchment overtakes papyrus.

**Why you would never guess this.** Obvious once you want it, with one non-obvious fact: Rome's reed pen (*calamus*) suits papyrus but scratches on parchment's tougher grain; a feather's spring glides where a reed digs in. The split holds ink by capillary action and meters flow, but wears and needs re-cutting every few hours.

Also covers: if_iron_gall_ink, if_steel_pen_nib.

**Iron gall ink**: tannic/gallic acid from oak galls binds chemically to iron from green vitriol (*atramentum sutorium*), pale on application, oxidising over hours to a black-blue that bonds into the substrate's fibres rather than sitting on top, unlike carbon ink, which can be sponged off. Cannot be erased once dry: good for a legal record, bad for a correctable account.

**Steel pen nib**: stamped, hardened steel that never needs re-cutting; the kernel is heat treatment, harden fully then temper to spring hardness, not full hardness, or the nib snaps.

**Prerequisites.** Ink: `cap_heat_0700`, `mat_vitriols`. Nib: `mat_blister_steel`, `cap_tol_100um`, interchangeable-parts precision.

**Cost & labour.** ESTIMATED. Quills near-free; ink a day's batch chemistry; nibs need real stamping-die tooling, a later industrial product.

**Danger.** None of weight.

**Confidence: HIGH** for quill and ink (both attested); **MEDIUM** for the nib, gated on stamping precision.

---

### if_fountain_pen - Fountain pen

**What it is.** A pen carrying its own ink reservoir, writing continuously without dipping.

**Why you would never guess this.** The reservoir is trivial; the hard part is the feed, a comb of fine cuts that must let air bubble **in** at the same rate ink flows **out**, purely by capillary action, no valve. Wrong geometry floods the pen or starves it, a self-regulating plumbing problem that lagged the dip pen by centuries.

Also covers: if_pencil_graphite, if_carbon_paper.

**Prerequisites.** `if_steel_pen_nib`, `mat_celluloid`, `cap_tol_100um`.

**Graphite pencil**: pure native graphite is scarce (historically one large English deposit) and too soft alone. The Conte process grinds low-grade graphite with fine clay and fires it; the clay:graphite **ratio**, not graphite purity, sets hardness grade.

**Carbon paper**: an even oily lampblack coating in a thin wax carrier on tissue, transferring by pressure alone; too thick and it clogs and cracks when rolled.

**Failure modes.** Pen: flooding or starving. Pencil: too much clay barely marks, too little snaps. Carbon paper: uneven coating gives patchy copies.

**Cost & labour.** ESTIMATED, small-batch craft goods once materials are in hand.

**Danger.** None of weight.

**Confidence: MEDIUM** across all three, limited by sourcing native graphite or celluloid.

---

### if_typewriter - Typewriter

**What it is.** A machine striking a fixed, legible character per keystroke, faster and more legible than any hand.

**Why you would never guess this.** QWERTY is not for finger speed; it keeps letter pairs common in English typing on opposite sides of the basket so their bars swing in from different angles and do not collide mid-stroke. Optimised for clearance, not speed.

Also covers: if_shift_key_mechanism.

**Prerequisites.** `if_steel_pen_nib`, `cap_tol_100um`, interchangeable-parts precision.

**Procedure.** Each key swings a type bar to strike an inked ribbon at a fixed point; bars must return fast and fully or the next stroke jams against one still retracting.

**Shift key**: the whole basket (or carriage) shifts one notch so the same bar strikes a different face of a two-character slug; the spring return must be precise or the next keystroke prints the wrong case.

**Failure modes.** Weak return springs jam under fast typing; an imprecise shift misprints case intermittently.

**Cost & labour.** ESTIMATED, comparable in skilled hours to a good clock; a mid-tier product, not an early one.

**Danger.** None directly; a typed document's anonymous hand is useful for anything you would rather not trace to a known scribe.

**Confidence: MEDIUM** - mechanism well documented; achievability gated on interchangeable-parts precision.

---

### if_punched_card - Punched card

**What it is.** A standard-format card whose hole pattern encodes information, readable and sortable by machine.

**Why you would never guess this.** The ancestor is the loom, not the office. Jacquard cards, fed through a loom one at a time, lift or block hooks controlling which warp threads rise; a chain of thousands weaves a complex pattern automatically, arguably the birth of the stored program. It took a leap to realise hole positions controlling a mechanism could encode anything.

Also covers: if_jacquard_chain, if_keypunch.

**Prerequisites.** `cap_tol_1mm`, `mat_paper`.

**Procedure.** Fix a card size and hole grid; any later machine depends on every card matching it exactly; punch holes at chosen positions to encode a record.

**Keypunch**: a modified typewriter driving a punch die per keystroke; the card must be held in precise register or the hole lands in the wrong column, silently.

**Failure modes.** Drift in card dimensions between batches makes cards from different runs unreadable together.

**Cost & labour.** ESTIMATED. A Jacquard card chain for one pattern is days of cutting; a punched-card standard is cheap per card but expensive to establish and enforce across an organisation.

**Danger.** Low, mostly organisational: an unenforced standard is the real failure.

**Confidence: HIGH** for Jacquard (well attested, in use); **MEDIUM** for a Roman-era card standard, a social achievement as much as a mechanical one.

---

### if_card_sorter - Card sorter

**What it is.** A machine routing punched cards into trays by which holes they carry, and, developed further, counting and cross-tabulating them.

**Why you would never guess this.** Sensing is bare electrical contact, not sight: fine wire brushes ride the card, and wherever a hole exists a brush touches a metal drum beneath, completing a circuit that trips a solenoid gate diverting the card. Nothing optical, decades before optical sensing existed.

Also covers: if_hollerith_tabulator.

**Prerequisites.** `if_punched_card`, `electromagnet`.

**Procedure.** Feed cards past a brush bank wired to gate solenoids, one per hole position of interest; a completed circuit fires the matching gate.

**Hollerith tabulator**: adds an odometer-style counter advancing on every sensed hole, counting and cross-tabulating categories automatically. MEASURED: the 1880 US census took roughly eight years by hand; the 1890 census, with Hollerith machines, roughly one.

**Failure modes.** A worn brush misses a hole intermittently, undercounting silently; dirty contacts give false triggers.

**Cost & labour.** ESTIMATED. A modest sorter is comparable in complexity to a telegraph relay bank; low thousands of denarii once electromagnets exist.

**Danger.** Low physically; socially notable, a tabulator is a real census and tax accelerator, handing a magistrate a sharper tool for finding and taxing people.

**Confidence: MEDIUM** - straightforward once electromagnets and punched cards exist.

---

### if_index_card_system - Index card and filing system

**What it is.** A uniform card per record, filed in strict order in drawers, letting you insert new information without recopying a ledger.

**Why you would never guess this.** Obvious once you want it, yet nobody assembled it: Rome has alphabetical order and cheap slips already, and never combined uniform size with strict filed order and drawer storage. The invention is procedural discipline, nothing to build, only a convention to enforce.

Also covers: if_dewey_classification.

**Prerequisites.** `mat_paper`, `cap_tol_1mm`.

**Procedure.** Fix a card size; file strictly by one agreed order; never let an unfiled backlog accumulate, since constant insertion cost is the whole value.

**Dewey classification**: hierarchical decimal scheme (philosophy at the 100s, science at the 500s) lets you insert any new subject without renumbering existing cards, unlike sequential shelf order.

**Failure modes.** The system fails the moment filing discipline lapses; one misfiled card is effectively lost until the drawer is re-sorted.

**Cost & labour.** ESTIMATED, negligible material cost; the real cost is a disciplined clerk and, for Dewey, designing the scheme.

**Danger.** Low; the risk is organisational, adopting it without the labour to maintain it.

**Confidence: HIGH** - no unattested material, pure organisation, well demonstrated payoff.

---

### if_adding_machine - Adding machine

**What it is.** A mechanical device adding numbers reliably without a human carrying.

**Why you would never guess this.** The carry is the whole problem: each decade wheel, rolling 9 to 0, must physically kick the next wheel forward by one, and that kick must itself trigger a further carry down the line. A simple gear train cannot cascade this; it defeated skilled 17th-century mechanics for years.

Also covers: if_comptometer, if_cash_register, if_slide_rule.

**Prerequisites.** `cap_tol_1mm`, `crank_conrod`.

**Procedure.** Each digit wheel carries a spring-loaded finger that, only passing 9 to 0, engages and advances the next wheel by one tooth; chain wheels to cover the largest expected sum. A correct carry gives identical results by hand and machine at any cascade length.

**Comptometer**: every keystroke adds instantly, no separate total stroke; faster once mastered, harder to learn. **Cash register**: a social device, not an arithmetic one, forcing a printed receipt and locked drawer per transaction to prevent an employee pocketing cash unrecorded. **Slide rule**: an analog lineage, multiplication as addition of lengths on a logarithmic scale, needing logarithm tables first (`60_mathematics_method.md`; Rome's lack of positional notation makes this real labour). The rule itself is simple carpentry once the scale exists; precision capped near three significant figures by eye.

**Failure modes.** Adding machine: a mistimed finger skips or double-advances a carry. Slide rule: a warped rule throws every reading off consistently.

**Cost & labour.** ESTIMATED, comparable to a mechanical clock; a slide rule a day's ruling once tables exist.

**Danger.** Low; the cash register reduces its owner's risk (catching theft) rather than adding any.

**Confidence: MEDIUM** - carry mechanisms and log scales are textbook once tolerance and tables exist; Rome's numerals are a real obstacle for the slide rule.

---

## Part Three: capturing sound

### if_phonautograph - Phonautograph

**What it is.** The first device to record a sound wave's shape as a visible trace, without playback.

**Why you would never guess this.** Built purely to let scholars *see* sound: a diaphragm and stiff bristle scratch a wavy line into lamp-blacked paper or glass on a rotating drum. Running the mechanism backward to reproduce sound did not occur to its own inventor; the historical traces were only converted to audible sound roughly a century and a half later, by modern optical scanning (ATTRIBUTED, a documented modern episode).

Also covers: if_tin_foil_phonograph, if_wax_cylinder.

**Prerequisites.** `cap_tol_1mm`.

**Tin foil phonograph**: the same mechanism with the stylus **indenting** soft tin foil on a cylinder; running it back vibrates the diaphragm, reproducing a faint, harsh sound. The foil crinkles after roughly 10-20 plays (MEASURED, attested), a novelty.

**Wax cylinder**: cuts, rather than indents, a groove into soft wax, cleaner, durable, and erasable and recuttable, good for 100+ plays, the basis of the first real recording industry.

**Failure modes.** Too stiff a stylus or shallow groove gives faint, distorted playback; wax too soft wears fast, too hard skips.

**Cost & labour.** ESTIMATED, a modest precision project comparable to a decent clock, once a sensitive diaphragm exists.

**Danger.** Low, though a stranger's voice from a spinning cylinder with no visible speaker reads as sorcery to a superstitious observer; stage the first demonstration carefully.

**Confidence: MEDIUM** - all three attested and mechanically simple; the barrier is a sufficiently sensitive, even diaphragm.

---

### if_disc_record - Disc record

**What it is.** Recorded sound on a flat disc mass-produced from a single master, rather than re-recorded one at a time.

**Why you would never guess this.** A cylinder duplicates slowly, one at a time; a disc's master groove can be electroplated into a metal "stamper" that presses thousands of identical copies in hot shellac in seconds each, like a coin die. This is why disc beat cylinder commercially despite the cylinder's arguably better fidelity.

Also covers: if_disc_cutting_lathe, if_gramophone_motor, if_acoustic_horn_recording.

**Prerequisites.** `if_wax_cylinder`, `mat_shellac` (Indian lac resin, a reachable Far-East good).

**Disc-cutting lathe**: the stylus feeds sideways at a constant precise pitch while the disc spins at dead-constant speed, or groove spacing and playback pitch wavers. **Gramophone motor**: a spring or weight drive fitted with a centrifugal governor (as in a steam engine) and a flywheel smoothing short-term ripple. **Acoustic horn**: a purely passive amplifier, gain rising only logarithmically with size, so doubling the horn gives far less than double the loudness; the diaphragm's own stiffness caps how much air it moves, why bass is essentially absent, a physical ceiling, not workmanship.

**Failure modes.** Uneven disc speed distorts pitch; shellac is brittle and shatters on impact.

**Cost & labour.** ESTIMATED, minutes of pressing per copy once master and stamper exist; the lathe and stamper tooling are the real capital cost.

**Danger.** Low; manage reactions to a talking machine as with the phonautograph.

**Confidence: MEDIUM** - shellac is genuinely reachable; the electroplating stamper depends on `50_electricity.md`'s current chain.

---

### if_carbon_microphone - Carbon microphone

**What it is.** A device converting sound pressure directly into varying current, the basis of the telephone and electrical recording.

**Why you would never guess this.** Loosely packed carbon granules (lampblack) between two electrodes change **resistance** as sound pressure compresses or relaxes their packing; a steady current through them is modulated in step with the sound. It needs no chemistry, but it is not passive, without current already flowing it produces nothing.

Also covers: if_moving_coil_loudspeaker.

**Prerequisites.** `crude_cell`, `mat_carbon_black`.

**Failure modes.** Granules pack down and lose sensitivity over weeks, needing tapping or replacement; too loose a pack drops sensitivity.

**Moving coil loudspeaker**: the electrical converse, a coil on a paper cone in a strong magnetic field, varying current makes varying force, pushing and pulling the cone. Cone size and material set bass response directly; a small cheap cone cannot move enough air for low notes, a physical limit.

**Cost & labour.** ESTIMATED, modest once electromagnets and current exist; the loudspeaker's magnet is the harder single component.

**Danger.** Low.

**Confidence: MEDIUM** - textbook, gated on `50_electricity.md`'s electromagnet and current chain.

---

### if_magnetic_tape - Magnetic tape recording

**What it is.** Sound recorded as magnetisation along a moving tape, erasable and re-recordable indefinitely.

**Why you would never guess this.** Fine magnetic oxide particles on the tape pick up magnetisation roughly proportional to recording current, but that curve is sharply nonlinear near zero, so a naive recording distorts badly. The fix, mixing in a strong, inaudible high-frequency "bias" (above 20 kHz) with the audio, is counterintuitive: add a huge signal you will never hear, purely to keep the tape's magnetic domains cycling through their full linear range.

Also covers: if_recording_bias.

**Prerequisites.** `electromagnet`, `mat_paper`.

**Failure modes.** Without bias, distortion is severe; uneven tension stretches tape and warps pitch.

**Cost & labour.** ESTIMATED, high, the oxide coating must be extremely fine and uniform, well beyond reliable Roman-era grinding and settling.

**Danger.** Low physically.

**Confidence: LOW** - bias is textbook, but manufacturing fine, uniform oxide is a genuine late barrier; one of the hardest destinations in the module.

---

## Part Four: wires that carry a signal

### if_electric_telegraph - Electric telegraph

**What it is.** Sending messages instantly over long distances by electrical pulses on a wire.

**Why you would never guess this.** A single circuit's range is capped at a few tens of miles by wire resistance and battery capacity. A telegraph crosses a continent because of the **relay**: at each station, the weak incoming current only moves a small local armature, which closes a separate, fresh-battery local circuit that retransmits full strength onward. Without the relay you have a curiosity; with it, a continental network. Nobody guesses the trick is "use the weak signal only to trigger a strong one."

Also covers: if_morse_key_and_sounder, if_telegraph_relay.

**Prerequisites.** `electromagnet`, `crude_cell`.

**Procedure.** Space relay stations by wire resistance and battery strength (a few tens of miles per hop, ESTIMATED from 19th-century line practice); a key opens and closes the circuit in short and long pulses (Morse); a sounder, an electromagnet clicking an armature, reproduces them at the far end. A trained operator reads the **rhythm** of the clicks as words directly, not by counting.

**Failure modes.** Dirty relay contacts drop the signal; a relay spaced too far from its neighbour receives too weak a trigger.

**Cost & labour.** ESTIMATED, DERIVED from wire resistance and battery output, scaling roughly with route length; comparable per mile to a lighter Roman road.

**Danger.** Social: an instant long-distance network is exactly the cross-provincial capability the Roman state fears in private hands (`03_SOCIAL_POLITICS.md`); expect it to attract imperial oversight past one estate's boundary.

**Confidence: HIGH** - the relay principle is textbook and every material is Roman-available once `50_electricity.md`'s chain is solved.

---

### if_submarine_cable_gutta_percha - Submarine cable with gutta percha

**What it is.** A telegraph cable surviving on the sea floor without shorting through seawater for years.

**Why you would never guess this.** The problem is insulation, not the conductor; bare copper shorts instantly in seawater. Gutta percha, latex of the *Palaquium* tree, native only to Malaya, Sumatra and Borneo, is thermoplastic and chemically inert, and does not rot under seawater pressure the way rubber, tar or wax do. This one tree product from one distant region is why undersea telegraphy became possible, exactly the case `95_expeditions.md` describes: not unobtainable, elsewhere. `50_electricity.md` says flatly Rome will never have gutta percha; true only for passive trade, someone has to sail for it.

Also covers: if_cable_repeater.

**Prerequisites.** `if_electric_telegraph`, `mat_gutta_percha` (`95_expeditions.md#trade_route_extend`).

**Procedure.** Warm gutta percha pliable and wrap layers around the copper conductor, well beyond bench-tested thickness since undersea faults are unrepairable; armour with wound iron wire near shore; pay out under tension at a slow, steady speed.

**Failure modes.** A pinhole shorts the whole line on submersion, detectable only by continuous continuity testing while laying.

**Cable repeater**: a submerged relay boosting a signal too weak after roughly 100-200 km, ESTIMATED from attenuation scaling; unrepairable once laid, so its own reliability, not its electronics, is the design limit.

**Cost & labour.** ESTIMATED, extremely high: an expedition, a purpose-built cable ship, and the cable itself before one message sends, among the largest single capital commitments in the tree.

**Danger.** Both large: `95_expeditions.md`'s expedition risks, plus a laid cable is an obvious sabotage target.

**Confidence: HIGH** on the material science; **LOW** on Roman-era logistics, laying real cable length needs ship-handling this guide's early centuries likely lack.

---

### if_telephone_transmitter - Telephone transmitter

**What it is.** A device converting nearby voice into an electrical signal for wire transmission.

**Why you would never guess this.** The same carbon-granule mechanism as the microphone above, packaged for mouth distance, needing a constant small current at every handset, a real infrastructure burden: a telephone network needs power distributed to every subscriber, not just wire.

Also covers: if_telephone_receiver, if_loading_coil.

**Prerequisites.** `if_carbon_microphone`.

**Failure modes.** Receiver and transmitter too close or too loud causes acoustic feedback squeal.

**Telephone receiver**: a small loudspeaker run in reverse, an electromagnet pulling a thin iron diaphragm. Fidelity is deliberately poor, passing only roughly 300-3400 Hz, why a phone voice sounds thin, all intelligibility needs and all the diaphragm supports.

**Loading coil**: an inductor inserted periodically to cancel the cable's own capacitance, extending range roughly from 20 km unloaded to 50 km loaded; wrong spacing increases crosstalk, and worsens the line for anything but voice-band audio.

**Cost & labour.** ESTIMATED, a handset modest once the microphone exists; a full network is the real capital sink.

**Danger.** Low physically; see the exchange entry below for the sharper risk.

**Confidence: MEDIUM** - textbook once the carbon microphone and low-voltage supply exist.

---

### if_telephone_exchange - Telephone exchange and switchboard

**What it is.** A central point connecting any subscriber's line to any other's on demand.

**Why you would never guess this.** A manual exchange works by an operator physically plugging a cord between jacks, meaning that operator hears, or can choose to listen to, every call passing through. This is the largest single social danger in this cluster: an exchange operator is a standing eavesdropper on every subscriber's business, and a rival, spouse or faction only needs one sympathetic operator to listen to anything routed through the board. Capacity is capped by staffed operators, not wire.

Also covers: if_strowger_exchange.

**Prerequisites.** `if_telegraph_relay`, `if_telephone_transmitter`.

**Strowger exchange**: an electromechanical stepping switch moves a wiper vertically then rotates it horizontally, driven purely by the caller's own dial pulses, removing the operator entirely. A persistent ATTRIBUTED (unverified) anecdote holds its inventor was an undertaker who suspected the town operator was diverting his calls to a rival; true or not, it captures exactly the danger the automation solves. Bearing wear on the switches is rapid, an ongoing maintenance cost.

**Failure modes.** Manual: an overwhelmed board cannot connect calls fast enough at peak. Strowger: worn contacts misroute calls intermittently.

**Cost & labour.** ESTIMATED, a manual exchange scales with operator wages, ongoing; Strowger trades that for a large maintenance-heavy capital asset.

**Danger.** Serious, not minor: assume any sensitive call through a manually-staffed exchange is not private; see `03_SOCIAL_POLITICS.md` on who is watching you.

**Confidence: MEDIUM** for manual (simple, attested); **LOW** for Strowger, precise stepping switches need tolerances this guide's early centuries will struggle to hold.

---

## Part Five: capturing light

### if_camera_obscura_lens - Camera obscura with lens

**What it is.** A darkened box projecting a real, inverted image of the outside world, sharp and bright enough to trace or expose.

**Why you would never guess this.** Obvious once you want it: a pinhole projects an image but is extremely dim, bright sun only. A modest ground lens (Rome already grinds lenses, `30_glass_optics.md`) in place of the pinhole gathers far more light for a brighter image at a smaller aperture, essentially free once lens grinding exists.

Also covers: if_camera_lucida.

**Prerequisites.** `lens_grinding`, `cap_tol_1mm`.

**Camera lucida**: an entirely different trick, no dark box, a prism (or angled mirrors) held above paper at exactly 45 degrees lets the artist see the scene and the paper superimposed, tracing an accurate outline freehand in daylight, no darkroom, no exposure.

**Failure modes.** A poor lens gives a soft image; a prism angle off by a couple degrees breaks the superimposition.

**Cost & labour.** ESTIMATED, low, a modest lens-grinding job (`30_glass_optics.md`).

**Danger.** Low; a "ghostly" projected image may unsettle a superstitious observer, demonstrate it as natural philosophy.

**Confidence: HIGH** - straightforward optics once Roman lens-grinding exists.

---

### if_silver_halide_sensitivity - Silver halide photographic sensitivity

**What it is.** The chemical fact under almost every process here: certain silver salts darken under light in proportion to exposure.

**Why you would never guess this.** Light breaks a small fraction of a halide crystal's ions to metallic silver, a latent image invisible to the eye; development amplifies it to visible. The non-obvious part: this does not stop on its own. Unexposed grains stay light-sensitive and keep darkening until the whole plate goes uniformly black. The craft is stopping it in time, dissolving away every unexposed grain (fixing) before it reacts further, a step almost nobody guesses is necessary until a ruined plate teaches them.

Also covers: if_daguerreotype.

**Prerequisites.** `analytical_chemistry`, `mat_silver` (Cartagena mines).

**Roman-available inputs.** Silver chloride, from silver nitrate plus sea salt, is readily reachable; bromide and iodide, more sensitive, need sources Rome cannot easily reach. ESTIMATED: start with chloride.

**Procedure.** Coat a surface with the halide; expose in a camera obscura; develop to amplify the latent image; fix by dissolving every unexposed grain, historically a hyposulfite bath, the step that makes photography possible at all.

**Failure modes.** Skip fixing and the plate blackens within hours of returning to light.

**Daguerreotype**: develops by exposing the plate to hot mercury vapour, amalgamating onto exposed silver in proportion to light received, building a mirror-bright image directly on silvered copper, unique, no negative, no copies.

**Cost & labour.** ESTIMATED, a skilled chemist's day per plate; silver a real material cost.

**Danger.** Physical: mercury vapour is a serious cumulative poison, ventilate. Social: an exact captured face reads as uncomfortably close to image-magic *devotio* effigies to many Romans; expect suspicion.

**Confidence: HIGH** on the chemistry; **MEDIUM** on sourcing anything beyond chloride.

---

### if_calotype - Calotype paper negative

**What it is.** A negative-positive process letting unlimited copies print from one exposure.

**Why you would never guess this.** A paper negative (silver iodide, waxed translucent after exposure) can be contact-printed any number of times onto fresh paper, the first true photographic reproduction technology, at the cost of the paper's fibre texture showing faintly in every print.

Also covers: if_wet_collodion_plate, if_dry_gelatin_plate.

**Prerequisites.** `if_silver_halide_sensitivity`, `mat_paper`.

**Wet collodion**: glass coated with collodion (nitrocellulose in ether and alcohol, `20_chemistry.md`) carrying silver salts gives a texture-free negative, but must be sensitised, exposed and developed while wet, evaporation ruins sensitivity in 10-15 minutes, forcing field photographers to carry a whole portable darkroom, a large hidden logistics tax.

**Dry gelatin**: gelatin heated permeates evenly with silver salts, and once dried, stays sensitive on the shelf for months, finally separating preparation, exposure and development in time and place, which enables amateur, handheld, spontaneous photography far more than the camera itself does.

**Failure modes.** Calotype: over-waxing blurs detail. Collodion: any delay past 10-15 minutes ruins the image. Gelatin: uneven heating leaves patchy sensitivity.

**Cost & labour.** ESTIMATED, moderate per batch; collodion additionally demands ongoing field logistics.

**Danger.** Low beyond standard darkroom handling; same image-magic suspicion as daguerreotype, somewhat softened since reproducible negatives look less like a captured soul.

**Confidence: MEDIUM** - collodion depends on a working nitrocellulose supply, a real Roman-era chemistry project.

---

### if_celluloid_roll_film - Celluloid roll film

**What it is.** A flexible transparent plastic base manufacturable as a continuous roll, ending single-plate reloading.

**Why you would never guess this.** Celluloid (nitrocellulose plasticised with camphor, a Far-East import) coated with gelatin emulsion can be a long strip with sprocket holes for precise frame spacing, unlocking handheld cameras with dozens of exposures and, with fast repeated pulldown (see below), true motion pictures.

Also covers: if_panchromatic_emulsion, if_autochrome_plate.

**Prerequisites.** `if_dry_gelatin_plate`, `mat_celluloid`, `cap_tol_100um`.

**Panchromatic emulsion**: ordinary emulsion is blind to red, safe under a yellow safelight; special dye sensitisers extend sensitivity across the full spectrum including red, more realistic tone, but now even a dim red safelight fogs the plate.

**Autochrome plate**: millions of transparent starch grains dyed red, green and violet, dusted onto glass as a random colour filter over a single panchromatic emulsion; light reaches the emulsion only through correctly-coloured grains, and viewing the developed plate backlit blends the dots into full colour. Resolution caps around 100 lines/mm; colours read soft and pastel.

**Failure modes.** Uneven camphor plasticising cracks the film; panchromatic plates fog invisibly under an ordinary safelight.

**Cost & labour.** ESTIMATED, high; camphor is a genuine expensive import, dye sensitisers a real synthetic-chemistry reach.

**Danger.** Physical: celluloid and nitrocellulose stock are genuinely flammable, closer to a slow explosive when aged; store away from flame.

**Confidence: MEDIUM** on celluloid; **LOW** on panchromatic and autochrome, both needing synthetic dye chemistry beyond this guide's early modules.

---

### if_flash_powder - Flash powder

**What it is.** A way to produce a very bright, near-daylight burst of light in a fraction of a second, for exposures where lamp or gaslight is far too dim.

**Why you would never guess this.** Burning magnesium metal gives blue-white light near daylight's spectrum in well under a second. The hard part is the magnesium itself: historically isolated only by electrolysis of molten salts, not achieved until the early 1800s; treat true magnesium flash as gated behind `50_electricity.md`'s current chain, a genuinely late capability.

Also covers: if_flashbulb.

**Roman-available inputs.** A real stopgap: dried lycopodium powder (clubmoss spores, MEASURED as a stage-flash material for centuries before magnesium) burns bright but dim and yellow-orange when blown through a flame, dramatic, not a real exposure.

**Procedure.** Grind magnesium fine to maximise burning surface; ignite by spark or flame at exposure, held clear of anything flammable.

**Failure modes.** Coarse powder burns too slowly; damp powder fails to ignite.

**Flashbulb**: thin magnesium foil sealed in a glass bulb filled with pure oxygen, fired electrically, single-use and safer than loose powder; the seal must be perfect, any leak ruins it before firing.

**Cost & labour.** ESTIMATED, high, gated on magnesium; lycopodium is cheap but does not solve the actual exposure problem.

**Danger.** Physical: burning magnesium is a fire and burn hazard, the smoke an eye/lung irritant indoors; ventilate.

**Confidence: LOW** - chemistry is textbook, magnesium metal is a real late-tier barrier.

---

### if_focal_plane_shutter - Focal plane shutter

**What it is.** A precise mechanism controlling exposure duration, essential below a fraction of a second.

**Why you would never guess this.** A fabric curtain with a slit runs across the film plane itself; narrowing the slit's **width**, not the curtain's speed (roughly constant), shortens exposure. Above roughly 1/500 second needs multiple synchronised slits. Shutter speed here is a width, not a speed.

Also covers: if_leaf_shutter, if_intermittent_film_movement.

**Prerequisites.** `cap_tol_100um`.

**Leaf shutter**: overlapping metal blades at the lens, opened and closed together by a small geared spring mechanism; because the whole aperture opens as one unit it flash-synchronises far more cleanly than a focal-plane curtain, whose slit exposes different parts of the frame at different instants.

**Intermittent film movement**: to hold a frame still for exposure then advance it in a fraction of a second needs a Geneva cross or claw-and-cam converting smooth rotation into a stop-start jerk. The cross-slot geometry must be cut precisely or the pin binds, tearing film or skipping a frame.

**Failure modes.** An uneven curtain over-exposes one edge; a weak leaf-shutter spring effectively lengthens exposure.

**Cost & labour.** ESTIMATED, fine clockwork-level precision mechanism work.

**Danger.** Low.

**Confidence: MEDIUM** - well documented, achievability depends on holding the stated tolerance in production.

---

### if_cine_camera - Cine camera

**What it is.** A camera capturing a rapid sequence of stills on moving film, the basis of motion pictures.

**Why you would never guess this.** It is celluloid roll film plus intermittent movement plus one easy-to-miss requirement: the shutter must **blank the lens during pulldown**, or every frame carries a smeared double image. Spring-wound drive is simple but drifts speed over a shot; a motor drive holds a steadier frame rate.

Also covers: if_film_projector.

**Prerequisites.** `if_celluloid_roll_film`.

**Film projector**: the same problem in reverse, holding each frame still while light shines through it, adding a bright, hot light inches from flammable nitrocellulose film. Heat dissipation is a life-safety requirement, not a refinement.

**Failure modes.** Incomplete blanking smears or flickers the picture; inadequate heat dissipation can ignite jammed film in seconds.

**Cost & labour.** ESTIMATED, comparable to two fine clocks' worth of mechanism working in synchrony.

**Danger.** Physical, severe: nitrocellulose fires in enclosed cinemas were a real, repeated historical hazard (MEASURED as a documented class of incident) once projection became common; treat heat management as audience life-safety. Social: moving images of real people amplify the daguerreotype's image-magic anxiety.

**Confidence: MEDIUM** on the mechanism; **HIGH** on the fire risk, nitrocellulose flammability is settled chemistry.

---

## Part Six: the air itself

### if_tuned_circuit - Tuned LC circuit

**What it is.** A coil-and-capacitor pair resonating at one frequency, letting a receiver select one signal from the whole spectrum.

**Why you would never guess this.** A coil and capacitor together oscillate naturally at a set frequency, but how sharply that resonance selects one frequency and rejects others (its "Q") depends on minimising resistance in the loop, a fussy small-scale winding and low-loss-capacitor problem, not an exotic material one.

Also covers: if_antenna_dipole.

**Prerequisites.** `electromagnet`.

**Procedure.** Wind a coil with as few resistive joints as possible in pure annealed copper; pair with a low-loss variable capacitor; tune until the desired frequency peaks.

**Dipole antenna**: an antenna's own radiation resistance is very low, so impedance matching matters more than anything else for efficient transfer, and height above ground matters far more than a good ground connection.

**Failure modes.** A resistive coil or lossy capacitor gives a broad resonance that cannot separate close stations; a mismatched antenna radiates or receives only a fraction of its power.

**Cost & labour.** ESTIMATED, modest once copper and a basic capacitor exist; the cost is precision winding labour.

**Danger.** Low physically; socially, invisible long-distance signal detection reads as augury or sorcery to most Romans, be ready to explain it as natural philosophy.

**Confidence: MEDIUM** - textbook, gated on `50_electricity.md`'s electromagnet chain and winding precision.

---

### if_spark_transmitter - Spark transmitter

**What it is.** The earliest practical way to generate a radio signal strong enough to detect at a distance.

**Why you would never guess this.** A spark across a high-voltage gap produces a broadband, rapidly damped wave, not a clean tone, wasting energy and jamming every nearby transmitter at once, an early instance of the spectrum as a shared commons, a social problem as much as a technical one. Rotating the gap's electrodes so a fresh contact meets every spark reduces pitting but does not fix the broadband waste.

Also covers: if_coherer, if_crystal_detector.

**Prerequisites.** `if_tuned_circuit`.

**Coherer**: a glass tube loosely packed with metal filings briefly "cohere," clumping and sharply dropping resistance, when a radio wave passes, registering a click. The filings do not decohere on their own; a spring-driven tapper must bump the tube after every signal, or it stays stuck.

**Crystal detector**: a fine wire ("cat's whisker") pressed against a galena crystal (lead ore, Spanish/British/Sardinian mines) forms a one-way rectifying junction at lucky spots, converting the wave directly to signal with no battery or moving parts, far more reliable than the coherer but temperamental, needing trial-and-error hunting for a sensitive spot, lost with a bump.

**Failure modes.** An unpitted gap gives an inconsistent tone; an untapped coherer stops responding; a crystal's sensitive spot drifts or is lost.

**Cost & labour.** ESTIMATED, low to moderate, the crystal detector cheapest once galena is on hand.

**Danger.** Low physically; socially, visible sparking makes the sorcery suspicion worse, not better.

**Confidence: HIGH** for spark gap and coherer (first working radio systems, well attested); **MEDIUM** for the crystal detector, reliability depending on finding a sensitive sample.

---

### if_triode_oscillator - Triode oscillator

**What it is.** A stable continuous single-frequency radio wave generator, replacing the spark's crude damped burst.

**Why you would never guess this.** Once you have a hard vacuum tube (`50_electricity.md`, `55_semiconductors.md`), positive feedback from output back to input sustains continuous oscillation indefinitely. The fiddly part: coupling strength must sit in a narrow window, too little and it will not oscillate, too much and it chirps unstably.

Also covers: if_continuous_wave_transmitter, if_amplitude_modulation, if_frequency_modulation.

**Prerequisites.** `vacuum_tube`, `if_tuned_circuit`.

**Continuous wave**: the practical name for what a stable triode gives you, a steady, cleanly keyed tone using far less bandwidth than spark, letting many stations share a band without drowning each other.

**Amplitude modulation**: varies the carrier's strength with a microphone signal, bandwidth roughly twice audio frequency, simple, but atmospheric noise is itself amplitude noise and rides straight through as crackle.

**Frequency modulation**: varies frequency instead, sidestepping that noise almost entirely (a limiter clips amplitude noise before a discriminator recovers the sound), far quieter, at the cost of more bandwidth and a more complex receiver.

**Failure modes.** Loose feedback fails to oscillate; tight feedback chirps or drifts.

**Cost & labour.** ESTIMATED, high, gated on the vacuum tube.

**Danger.** Low physically once the tube exists; socially, continuous deliberate broadcast is far more visible and harder to deny than a one-off spark demonstration.

**Confidence: LOW** across all four, entirely gated on a working vacuum tube, treated as a hard, late-tier destination here.

---

### if_superheterodyne_receiver - Superheterodyne receiver

**What it is.** A receiver design letting a single dial select any station cleanly across a band.

**Why you would never guess this.** Rather than one stage sharp enough to isolate a station at its actual frequency, mix the incoming signal with a local oscillator to shift it to one fixed "intermediate frequency," where a single permanently-tuned sharp stage filters regardless of station. Deliberately converting to the "wrong" frequency to simplify everything downstream is the counterintuitive step.

Also covers: if_radio_direction_finding, if_facsimile_transmission, if_radar.

**Prerequisites.** `if_triode_oscillator`, `if_amplitude_modulation`.

**Radio direction finding**: a rotatable loop antenna has a sharp **null** edge-on to a transmitter, a far more precise bearing than its broad maximum; two stations taking simultaneous bearings triangulate a position. **Facsimile**: a rotating drum and photocell scan an image in a raster; receiving and sending drums must synchronise near-perfectly or the image smears; scan speed trades against resolution. **Radar**: transmit a short timed pulse, measure the echo's round-trip time for range, display on a CRT, a genuine capstone needing a stable oscillator, sub-microsecond timing and a working CRT together, essentially the far end of this guide's reconstruction path.

**Failure modes.** A drifting oscillator loses the intermediate lock; a bent loop gives a false null; drum drift skews a facsimile image.

**Cost & labour.** ESTIMATED, high across the cluster, all gated on the triode chain.

**Danger.** Low physically; RDF and radar are recognisably military-relevant the moment a general understands them.

**Confidence: LOW** across the cluster; radar marks the plausible end of this guide's reconstruction path.

---

### if_cathode_ray_tube - Cathode ray tube

**What it is.** A vacuum tube steering a focused electron beam to draw an image on a glowing phosphor screen.

**Why you would never guess this.** The beam is steered by magnetic coils or electrostatic plates striking a phosphor screen that glows at impact; the coils need genuine symmetry or the picture distorts. Phosphor wears out with use, dimming or "burning in" a ghost image.

Also covers: if_iconoscope, if_video_scanning_standard, if_television_mechanical.

**Prerequisites.** `discharge_xray`, `vacuum_tube`.

**Iconoscope**: a mosaic of tiny light-sensitive cells, each capacitively isolated so it independently accumulates its own charge since last scanned; building this fine, uniform mosaic, not the tube, is the real barrier.

**Video scanning standard**: fixing scan lines and frame rate, often matched to power-line frequency, is a coordination problem, not a technical one, every transmitter and receiver must agree or nothing displays (`03_SOCIAL_POLITICS.md`).

**Mechanical television** (Nipkow disc): a spinning disc punched with a spiral of holes, before a photocell or lamp, scans an image mechanically, no vacuum tube at all, just precision disc-cutting, giving a real, dim, flickering picture; the sensible stepping stone before the electronic route.

**Failure modes.** Asymmetric coils skew the image; a poorly isolated mosaic bleeds and blurs; an off-speed disc rolls the image.

**Cost & labour.** ESTIMATED, very high for CRT/iconoscope; moderate for mechanical, closer to Roman-era precision engineering.

**Danger.** Low physically; socially, transmitted moving images amplify image-magic suspicion.

**Confidence: LOW** for CRT and iconoscope; **MEDIUM** for mechanical television.

---

## Sources and confidence

These mechanisms are drawn from well-documented 19th and early 20th century engineering history: Gutenberg's punch-matrix-mould system, drying-oil ink chemistry, wet and dry photographic emulsions, the telegraph relay, gutta percha submarine insulation, and the spark-to-triode radio lineage are all HIGH-confidence, textbook engineering, independent of whether Rome can build them. Where this module flags LOW confidence, the uncertainty is almost always a Roman-era **material or precision** barrier, not the mechanism: vacuum tubes, fine magnetic oxide powders, synthetic dye sensitisers, and sub-millimetre disc ruling are all late, hard destinations in this tree, not myths. Cost and labour figures are marked ESTIMATED or DERIVED, never invented; real historical figures (census tabulation time, tinfoil phonograph play count, gutta percha's origin) are marked MEASURED with the basis given. Two anecdotes, the phonautograph's delayed playback and the Strowger undertaker story, are flagged ATTRIBUTED and not fully verifiable, included because they illustrate the mechanism honestly, not as settled fact.

## Where to go next

- `80_information_printing.md` - the lower-tier print and corpus-survival technologies this module's press cluster builds on, and the social strategy for surviving what you publish.
- `30_glass_optics.md` - lens grinding and mirror-making that the camera obscura, camera lucida and every glass photographic plate depend on.
- `50_electricity.md` - the electromagnet, crude cell and vacuum tube chain almost everything in Parts Four and Six is gated on; read its zinc and gutta percha notes before the telegraph or cable clusters.
- `03_SOCIAL_POLITICS.md` - read before building a press, an exchange, or a telegraph line. Everything here that moves information faster or more privately than a scribe also moves it faster or more privately than a magistrate.
- `95_expeditions.md` - the gutta percha logic, and more broadly "elsewhere, not unobtainable," that the submarine cable cluster depends on directly.
- `20_chemistry.md` - nitrocellulose, distillation and fixing-bath chemistry underlying collodion, celluloid and photographic fixing generally.
- `10_metallurgy.md` - cast iron sourcing (Han China import, or a cupola furnace) for the iron hand press and cylinder press.
