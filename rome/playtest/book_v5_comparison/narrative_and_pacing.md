# Narrative and Pacing: *The Long Way Home* (book_v5) vs. the Rome simulator

Scope: the story's shape — what the protagonist does, in what order, over what elapsed time;
what goes wrong; the turning points; where the arc ends up — compared against the simulator's
order of discovery, timescale, and what each model treats as a hard wall. Technical feasibility
research and the social/economic model are other researchers' territory and are touched only
where pacing depends on them.

Method: read the top-level planning docs (`README.md`, `V2_MASTER_CONTEXT.md`,
`bible/03_timeline.md`, `Rome_98AD_Intervention_Timeline.md`, `bible/04_tech_schedule.md`,
`V2_STORY_PLOT_NOTES.md`) to get the intended shape, then `CHAPTER_SUMMARIES.md` end to end (all
53 chapters — this is the closest thing to a scene-by-scene record of what's actually on the
page), then spot-checked primary prose (`chapters/ch21.md` in full) against both the summary and
the plan, then cross-checked the book's own QA audits (`TECH_GAP_AUDIT.md`,
`TIMELINE_TEXTURE_AUDIT.md`) which independently flag where the *outline* and the *actual
chapters* disagree — a second, book-internal source of "plan vs. execution" drift that turns out
to matter a lot for this comparison. On the simulator side: `simulator.py civs/validate/path`,
`00_BRIEFING.md`, `03_SOCIAL_POLITICS.md`, and the extensive playtest reports already on disk in
`rome/playtest/` (`FINDINGS.md`, `reports/rome_100ad_WIN.md`, `naive2/FINDINGS_ROUND2.md`) — these
already contain far more play-hours than I could add in this pass, so I read them closely rather
than re-running long sessions myself (one live `agent --fog` session confirmed the `state`/`path`
shapes cited below; I did not edit anything).

---

## Ranked findings

**1. The book's central structural claim — one mortal lifetime, knowledge dies unless
institutionalized — is also the simulator's designed thesis, but the shipped tool doesn't enforce
it by default, and that gap matters more than any single technology dispute.**
`00_BRIEFING.md` opens by telling the player they have "about thirty years" and that the
recommended-strategy sweep shows survival is a *cliff* (0% success surviving 15 years, 86% at 28,
"everything hinges on whether the school exists and the corpus is started by roughly year 20" —
`00_BRIEFING.md` lines 81-99). That is, almost verbatim, the book's own thesis: Daniel spends
Part V-VII (ch38 on) explicitly pivoting off personal invention because he has realized "everything
will die with him" (ch38 summary) and the payoff — Procula solving the clock escapement a
generation later (ch52), the Atlantic finally crossed with solved longitude generations after that
(ch53) — only happens *because* the corpus, the press, and the endowed prize fund outlived him.
But the actual playable `agent` JSON protocol defaults to `founder_ages: false` — an **immortal
founder** — and `--mortal` is a flag nobody exercised in any playtest report I found (confirmed by
grep across `FINDINGS.md` and every `naive*`/`reports/*` file: every hit is a note that the
default is immortal, none is a mortal-mode play session). The interactive tool, as shipped, lets
you skip the exact bottleneck the design doc and the book agree is the whole point. This is the
single most important place where "does the simulator model the book's premise" and "does the
simulator's current default *exercise* that model" come apart.

**2. Both works, independently, put the identical two moves first: a cover story and a patron —
and neither work needs numerals or a wonder-invention to come before them.**
The book's opening moves in order (ch01-ch09) are: survive the first hours, then a wordless
demonstration (the world map, ch03) that buys him status as "a curiosity worth keeping alive"
rather than a body to be disposed of, then a cover identity ("a cold place beyond Britain," ch04),
then slow language acquisition and small trust-building (ch05), and only *then* the balloon
spectacle that forces a real patron (Macer) to formalize terms (ch09). The simulator's own
`path point_contact_transistor` critical-path list puts `identity_cover` at position 4 and
`patron_local` at position 11, both in the first dozen of 168 required nodes, well before any
"impressive" technology — matching `00_BRIEFING.md`'s explicit advice ("Days 1 to 180: do nothing
impressive... Find out who is ill and rich. This is your entry to patronage"). This is a real,
specific convergence between a work of fiction and an independently-built optimizer, and it is
good evidence that both got something true about the premise.

**3. On the single technology both works dramatize as the defining bottleneck — steel — they
reach opposite verdicts about whether one lifetime is enough, and the disagreement is legible and
worth taking seriously on both sides.**
The book is explicit and insistent: production-grade, *reproducible* crucible steel is listed
under "CORRECTLY BLOCKED — do not re-open these" in `bible/04_tech_schedule.md` (line ~665):
temperature measurement is solved (the thermocouple chain, Phase D, ~10-20 years) but
carbon/atmosphere control in the melt is "genuinely hard, requires instruments Daniel cannot yet
build," and Daniel dies with steel still "occasionally right, never reliably repeatable" (ch21,
ch42 — Heras's deathbed line even names clean water, not steel, as the real achievement). The
simulator's `path` output puts `crucible_steel` at position 98 of 168, reachable via a serial
floor of about 22 years (summing the stated `calendar_floor_years` down its own listed critical
chain: identity_cover through crucible_steel), and the actual `agent` WIN playtest run (see
finding 5 below) completed it well inside a 57-year span. The tree's own chain shows the
identical causal shape the book invented independently — precision flatness → measured
temperature → controlled heat → steel — but the sim's `crucible_steel` node appears to be gated
on a `cap_heat_1600` capability tier plus the precision/measurement chain, and I did not find a
separate node gating specifically on *carbon-atmosphere* control (the book's stated residual
wall). I did not open simulator internals to confirm this (out of scope; the technical-
prerequisites researcher owns that ground), so I flag it as an observation from `path`'s node
list, not a settled claim. My own judgment: the book did more specific metallurgical homework
here (`V2_TECH_DEEP_DIVE.md` and `bible/04_tech_schedule.md` both name the O2/CO ratio problem
explicitly and argue why measuring temperature doesn't solve it) than the tree's node names
suggest the simulator did, and a story that makes its hero fail at something specific and
well-argued is more persuasive than a tree that reduces "steel" to a heat-capability threshold.
But the sim's broader point — that once you rigorously chase the *measurement* chain the serial-
time floor is shorter than intuition says — is also a real correction to the book's more diffuse
"the fire is the master" framing (ch21), which never quite explains why 57 years and a wealthy
workshop can't close a gap the book's own bible says needs "instruments Daniel cannot yet build"
without specifying what would be enough.

**4. The two works are not actually answering the same question, and the "same story" framing in
the brief needs a caveat.**
The book's endpoint (Daniel's death, ~155 AD, 57 elapsed years) is deliberately modest: a
Newcomen-class atmospheric pump, a Volta pile, spark-gap radio with a Morse relay network, a
printing/paper/numerals complex, ocean hulls that float but cannot yet cross — explicitly "the
bottom rungs moved," not a transistor (`bible/03_timeline.md`'s own coda line). The simulator's
chosen goal for this playtest campaign, `point_contact_transistor`, is a 1947-equivalent target
168 required nodes and (per `00_BRIEFING.md`'s designed sweep) a **285-year median** out, later
revised in play to roughly 310-360 years across several sessions (`00_BRIEFING.md`: 385 AD
median; `naive2/FINDINGS_ROUND2.md`: Rome 312-325; `reports/rome_100ad_WIN.md`: a single
interactive run finished 458 AD / 358 elapsed years). None of these numbers is what the book is
measuring. The book's arc, converted to the simulator's own units, would end at something like
node ~15-25 of the 2,828-node tree (numerals, paper, printing, water filtration, a steam pump,
a battery, a radio) — a stopping point the tree passes through in its first 20-40 years on every
run I found reported. Where the two works really can be checked against each other is the
**rate** of the first few decades, not the total distance to a transistor — and there, per finding
2 above, they agree closely.

**5. The book's own audits show a wide gap between what was *planned* as achievable and what
actually reached the page — a "plan vs. execution" drift that has a real analogue on the
simulator side (`available`/`why`/`path` vs. the prose knowledge base), and both are worth
naming plainly rather than treating either artifact as the ground truth.**
`TECH_GAP_AUDIT.md` (book's own QA, dated 2026-05-30) lists as **completely absent from the
written chapters**, despite being called "required" in the outline: the generator/dynamo,
generator-powered arc lighting, reading glasses (the presbyopia payoff explicitly built up in
ch38), the mechanical calculator/marble-adder, ball bearings, the typewriter, all three hydrogen
applications (torch, tethered balloon, grenade test), the flying shuttle and water-powered loom,
war rockets, coal-gas lighting, photography, absorption refrigeration, the centrifugal pump, and
bulkheaded hulls. Several of these (generator, arc lighting, reading glasses) are called out by
the audit as chapter-specific payoffs whose setup is on the page but whose delivery scene simply
never got written. This matters for pacing because it means the book's own planning documents
(which this report leans on heavily for the "what's achievable when" picture) are systematically
*more* optimistic about Daniel's technological reach than the actual 53 chapters are — the prose
is more conservative than its own bible. On the simulator side, the playtest `FINDINGS.md`
records the mirror problem (N1, F4, F5 in `reports/rome_100ad_WIN.md`): the machine-readable
protocol (`available`/`why`/`path`) systematically under-signals hazards and gates that the prose
knowledge base (`03_SOCIAL_POLITICS.md`) states plainly — the Third Century Crisis knowledge-loss
mechanic cost one WIN playtester ~25 technologies at a stroke with zero warning from `path`, and
the scholar-headcount wall around year 174-180 was undiscoverable from the protocol alone. Both
works, in other words, have a documented "plan" that is more generous/complete than what a reader
or player actually experiences — worth remembering before treating either the book's bible or the
simulator's `path` output as a full account of what each system really does.

**6. What the book has that the simulator has no way to represent: named, singular human cost,
and unresolved moral guilt that the story refuses to discharge.**
Geta loses a hand, three fingers, and an eye grinding niter (ch21) and the book spends a full
paragraph on his face afterward, his one-eyed nod, Daniel paying his wages "every month I've had a
month to pay it in." Sabinus falls to his death in the first manned balloon (ch13); Naso is
maimed in the trial before that. The "uninhabited" lie Daniel draws into the first world map
(ch03) is revealed, privately, to have caused 30-50% mortality in a New World village from
disease he sent a ship toward (ch28), and the book never lets him off that hook — it resurfaces in
ch48's private confession and is corrected, bitterly, only in the coda (ch53) when the shore turns
out to be inhabited after all. Ch45 has him doing routine grain arithmetic with his numerals on
Judaean slave-price columns after Bar Kokhba, and the chapter ends on him and Marcia saying
nothing about it "until the lamp burns out." The simulator has a `risk` field, a `scandal`
field, hazard categories (plague, war, sacking, debasement) — all *statistical* and *reversible*
(mothballing, rebuilding, the automatic safety valve documented as F7 in the WIN report). Nothing
in the protocol could represent a single named worker's ruined hands as a standing weight the
player carries for the rest of the game, or a founder lying to himself and to his emperor about
what a shoreline contains. This is not a fixable gap — it is the difference between a story and a
resource model, and it's worth stating plainly rather than as a complaint: it is exactly the
kind of thing "other researchers are covering the economic model" cannot capture either.

**7. What the simulator models that the book never has to deal with: multi-civilization
comparison, and a fully quantified, adversarial economy running underneath every decision.**
The book only ever explores Rome, and Daniel's economic life, while detailed in sesterces
(`V2_DANIEL_FINANCES.md`), is measured in a handful of headline numbers per era, not a live
ledger of mine-operating costs, credit limits, debt interest rates, and resource throttling the
way `state` reports them. The simulator runs five civilizations side by side (`civs`: Rome, Han
China, Norse, Mexica, England) with different starting tech counts, population, state capacity,
and cultural coefficients ("fears heterodoxy," "resents machines," "eminence is dangerous") — a
comparative apparatus the book has no equivalent for and isn't trying to have one; Rome is Rome
in the book because the premise needs one fixed, richly-researched setting for character and
plot, not a controlled variable. This is a genuine difference in what each artifact is *for*,
not a flaw in either.

---

## PART 1 — The book: what Daniel does, in order, over what elapsed time

All years AD; Daniel arrives spring 98 AD at age 17 and the story runs to his death, ~155 AD
(age ~70-74), 57 elapsed years, per `bible/03_timeline.md` and `V2_MASTER_CONTEXT.md`'s own
framing ("He spends 57 years using a normal modern education to bend history"). Citations are to
`CHAPTER_SUMMARIES.md` chapter numbers unless noted; `[HIST]`/`[STORY]` tags follow
`bible/03_timeline.md`'s own convention.

| Year (age) | What he does | Depended on | Elapsed | Outcome |
|---|---|---|---|---|
| 98 (17) | Arrives, captured, phone note-taking (~2 wks before dead battery), draws a world map from memory under interrogation — accidentally reveals two western continents | Nothing (pure knowledge transfer) | days-weeks | Succeeds; earns "curiosity worth keeping" status (ch01-ch04) |
| 98-99 (17-18) | Latin acquisition via immersion; numerals demonstrated to Heras (flubs long division, recovers); germ theory reframed as "tiny invisible creatures" after Heras rejects it outright; crude soap; lead-pipe avoidance (household only); horse-collar sketch | Nothing but time and a captor willing to listen | ~1 year | Mixed: numerals land, germ theory only lands once reframed, soap/collar stay niche (ch05) |
| 99-100 (18-19) | Hot-air balloon: paper fails, linen burns him (the scar), third attempt holds ~10 breaths | Cloth, grease, fire — no patron yet | ~months | Partial proof of concept, not yet public (ch06-ch07) |
| 100 (19) | Public untethered balloon launch in the Subura; crashes into rooftops, near-riot defused by a haruspex's ambiguous omen | The balloon | 1 launch | Public spectacle succeeds; forces Macer to reveal himself as owner (ch08) |
| 100-101 (19-20) | Macer formalizes a walled yard, cloth, two assistants, a peculium; Tyche assigned; block printing begun; crop rotation/horse collar spread starts on Macer's estates; humiliated in public by Crispus at a salon | The balloon spectacle | ~1 year | Real patronage and capital secured; first public enemy acquired (ch09-ch10) |
| 101 (20) | Celer contracts a man-carrying balloon (80,000 HS); stirrup/crossbow sketches; heliocentrism taught to Heras; first manned tethered trial — Naso maimed | Workshop + patron capital | ~months | Technical partial success, human catastrophe (ch11) |
| 101-102 (20-21) | Sent to the Danube frontier; meets Apollodorus; unmanned tethered balloon works for reconnaissance but only in calm wind | Celer's contract, army logistics | ~1 year | Works narrowly; pressure mounts for manned free flight (ch12) |
| 102 (21) | Ordered to fly Sabinus untethered over hostile ground on a fixed deadline; wind catches the bag; Sabinus dies | Military schedule overriding his objections (he is still a slave) | 1 event | Catastrophic failure; permanent vow against manned fire-flight (ch13) |
| 102-103 (21-22) | Packs away the balloon; sorts future work into "clean tech" vs. gunpowder (refuses gunpowder — for now); returns to Rome; begins water filtration | The vow | ~1 year | Establishes the moral sorting that structures the rest of the book (ch14) |
| 103 (22) | Water filtration continues; realizes bronze-vs-iron tradeoff means steel is the real bottleneck; first crucible steel batches — one perfect blade, next batch (identical process) shatters; builds a Baghdad-type battery, calipers, mercury thermometer | Hermes (smith), workshop | ~1 year | Confirms the chokepoint; instrumentation begins (ch15) |
| ~103-104 (22-23) | Numerals now spreading on merchants' slates *without his involvement*; printing press running (block); prize-contest idea conceived (Tyche: "who prints the sea"); defends himself publicly against Crispus's impiety framing by drinking his own filtered water | Numerals already seeded 5 years earlier | ongoing | First evidence his earlier moves are now self-propagating (ch16) |
| ~104-105 (23-24) | Summoned by Trajan; demonstrates balloon, filter, Eratosthenes proof; Tyche out-calculates the imperial accountant; Trajan buys and manumits him on the spot — legal name Marcus Ulpius Danihel | Reputation reaching the top | 1 audience | Structural turning point: slave → imperial freedman, can own property/marry/free others (ch17) |
| 105 (24) | Buys and frees Pamphilus; deploys balloons/sanitation on the Second Dacian campaign; fouls Sarmizegetusa's water supply to break the siege; Decebalus's suicide | Citizenship, prior sanitation knowledge | ~1 year | Military success achieved through the same knowledge that saves lives elsewhere — moral inversion he names on the page (ch18) |
| ~105-107 (24-26) | Launches the annual writing/invention contest (funded by a quiet sportsbook); Trajan asks what the balloon can do as a weapon; buys and frees Tyche after a 5-year standoff over her agency; begins teaching her English | Contest needs the press; Tyche's price needs capital | ~2 years | Institution #1 (the contest) launched; first crack in "protecting people by deciding for them" theme (ch19-ch20) |
| ~106-108 (25-27) | Breaks his own gunpowder vow (niter beds, ~2 years); Geta maimed in a grinding explosion; deliberately bursts a flawed cannon to argue for precision boring — which is also what a steam-pump cylinder needs | Hermes's forge, 2 yrs of niter-bed slog | ~2 years | Gunpowder "works" but at direct human cost; argument for precision funding lands (ch21) |
| ~108-110 (27-29) | Meets and marries Marcia (business partner, not romance-first); first working steam pump (leaky, ~1% efficient, but pumps water); private notes on New World crops begin | Hermes/Tyche's bookkeeping gaps exposed the need for Marcia | ~2 years | First real institutional partner outside the original trio (ch22) |
| ~109-111 (28-30) | Clock/escapement attempted and fails (falls back to water clocks); telescope stays a blurry ~2x toy; rail tramway technically works (4 men do 26 men's labor) but is torn out — economically defeated by sunk slave capital; Volta pile + electromagnet built | Precision/steel chokepoint (clock, telescope); Maximus already owns his labor (rail) | ~2 years | Three separate, clearly-argued failures in one chapter — the book's "humbling beats" cluster (ch23) |
| ~110-112 (29-31) | A child independently reaches Daniel's own "ladder of knowing" metaphor at the contest; a farrier's 50-year heat-color table beats his own records; Volta pile demonstrated to Heras; son Lucanus born | Contest as a knowledge-gathering mechanism | ~2 years | First sign his institutions are outperforming him personally (ch24) |
| ~112 (31) | Senator Scaeva, rival Crispus, and haruspex Vibenius converge — patronage-as-trap, impiety threat, religious ultimatum, all within one chapter | Peak visibility | weeks | Peak-danger turning point set up (ch25) |
| ~112-113 (31-32) | Trajan's Forum dedicated; Crispus reframes his contest-prize network as "farming knowledge" out of the guilds — the sharpest and most accurate attack in the book | Years of scattered prize competitions now visible as a pattern | ~1 year | Antagonist's best argument; sets up the impiety trial (ch26) |
| 113 (32) | Formal impiety hearing; survives via a "my knowledge belongs to the gods" defense plus Scaeva's practical-benefits intervention; forced public sacrifice/dedication of all his works to Minerva under priestly oversight | The trial | 1 hearing | Survives, but at a real institutional cost (a leash on the contest) (ch27) |
| 113-117 (32-36) | Ordered to the Parthian War as camp physician/sanitation officer; learns via letter that his secretly-funded Atlantic ship (the *Corva*) reached the Americas and a sick crewman caused 30-50% village mortality; petroleum seeps noted in Syria; Celer dies of sepsis from a wound Daniel's antiseptic knowledge cannot reach in time; Trajan dies (8 Aug 117) — the blindside | Imperial orders (no choice); years-earlier private ship funding | ~4 years | Farthest territorial reach of the empire, and the book's largest personal grief + largest unresolved guilt, arriving in the same stretch (ch28-ch30) |
| 117-118 (36) | Returns to a Rome frightened by the Four Consulars purge; patron web (Macer, Scaeva) unreliable or actively hostile; son doesn't recognize him | Trajan's death | ~1 year | Total reset of political capital — the book's midpoint structural shock (ch31-ch33) |
| 118-121 (37-40) | Rebuilds via audits for the treasury (Eudemus), two private audiences with Hadrian; realizes Hadrian is the architect-Apollodorus once humiliated; deploys the false "uninhabited" world map, pitching an ocean program | Nearly a decade rebuilding from zero visibility | ~3-4 years | Hadrian grants a *bounded* program (survey, shipyard school, sea-clock prize) — "FIRST DIVERGENCE" from real history per the canon ledger (ch34-ch36) |
| ~121-122 (40-41) | Apollodorus mocks Hadrian's temple design; Daniel's backchannel intervention fails; Apollodorus exiled, dies | Political capital he's unwilling to fully spend | ~1 year | Fails to save a peer; accepts the bend-not-break lesson (ch37) |
| ~122-129 (41-48) | Presbyopia forces institution-building over personal invention: press chartered as a *collegium*, prize contest sheltered inside a religious endowment, patronage fund for systematic craftsman failure; first wireless spark-gap transmission (SOS/FELIX, 20 paces); writes the English-language encyclopedia with an explicit "hooked stroke" for uncertain claims; Heras dies; Bar Kokhba complicity confronted and left unresolved | Decades of prior infrastructure (press, Tyche/Ulpia as literate successors) | ~7-8 years | The book's stated turning point: personal invention chase → institutions built to survive him (ch38-ch45) |
| 130-138 (49-57) | Ocean survey reaches a third experimental hull (still cannot cross — no solved longitude); numerals reach official milestone stone; a library off the Argiletum stocks more printed codices than hand copies; Hadrian dies (138), succeeded by the stay-at-home Antoninus Pius — the ocean program loses its imperial champion but the *endowed* parts (press, contest, patronage) survive because they were built not to need one | Institution-building already done | ~8 years | Confirms the ch38 thesis worked: political patronage is fragile, endowed institutions aren't (ch44-ch46) |
| 138-155 (57-70s) | Cardiac decline; dictates rather than writes; formally closes the clock project as an unsolved standing prize; quarantine doctrine handed to a physician line against a plague ~10-15 years off; Macer, Pamphilus, Eros die; Marcia dies of cancer; the knowledge ladder is triple-copied and sealed (including a lead-buried copy); Daniel dies with Tyche reciting figures to him | Everything built since ch38 | ~17 years | Ends: bottom rungs moved, most dreams unbuilt, institutions intact (ch47-ch50) |
| Coda | A generation later, Procula (never met Daniel) solves the clock escapement he couldn't, from his honestly-marked failure notes (ch52). Centuries later (left deliberately vague — "long after," ~190 AD by one internal note, "generations" by another), a ship finally crosses the Atlantic using a descendant of that clock to solve longitude — and finds the shore inhabited, contradicting Daniel's founding lie (ch53) | The corpus, the press, the keeper-chain | generations | The payoff the book was built to deliver, and it happens entirely off-page and after his name is forgotten |

**Totals:** 57 years from arrival to death is the book's own stated frame. The technological
endpoint at death is explicitly modest by design (see Finding 4). The full payoff — solved
longitude, an actual ocean crossing — lands an unspecified but clearly multi-generational span
later, which the book leaves deliberately vague rather than dated (`bible/03_timeline.md`'s own
divergence ledger calls the ch53 date "left vague," floating anywhere from ~35 to 150+ years post-
Daniel).

---

## PART 2 — What goes wrong, and why

Ranked roughly by how central each failure is to the book's argument:

- **Manned flight kills people.** Naso maimed (ch11), Sabinus dead (ch13) — both under command
  pressure that a slave cannot refuse. This produces the book's central operating rule for the
  rest of the story (a vow, narrowly scoped, revisited explicitly rather than silently dropped —
  the V2 rewrite's own note flags that V1 had wrongly let this vow metastasize into a 40-year ban
  on *all* aerial work, and V2 explicitly fixes it: unmanned kite/glider work resumes within 5-7
  years, `bible/04_tech_schedule.md`).
- **Steel never becomes reproducible.** Confirmed chokepoint from ch15 onward; explicitly listed
  as permanently unsolved in `bible/04_tech_schedule.md`'s "CORRECTLY BLOCKED" section. This is
  the book's single most load-bearing technical failure — it gates the clock, precision
  instruments, and (implicitly) everything downstream that needed tight tolerances.
- **The mechanical clock/escapement is never solved in Daniel's lifetime.** He substitutes water
  clocks; the failure is named explicitly as one of the book's designed "humbling beats"
  (`bible/04_tech_schedule.md`'s "HUMBLING BEATS" list, item 2) and its resolution is deliberately
  deferred to a successor a generation later (ch52) — the clearest single dramatization of the
  book's institution-over-individual thesis.
- **The niter/gunpowder program costs a named worker his hands and an eye** (Geta, ch21) after
  ~2 years of foul, failure-prone slog (wrong nitrate salt scraped from cellar walls first; the
  right process is a manure-bed fermentation taking months per batch).
- **The rail tramway works and still fails** — a rare case where the *technology* succeeds
  (4 men outperform 26) and the *economics* kill it anyway, because the labor it would replace is
  already a sunk, slave-owned cost with no marginal price (ch23). This is presented as a hard
  structural wall, not a technical one.
- **The telescope stays a blurry toy** — striated, bubbly Roman glass is explicitly "CORRECTLY
  BLOCKED," and Daniel's claim of an "atom-seeing microscope" elsewhere is written as a deliberate
  lie he tells to bluff impact, not a technology he actually has.
- **He fails to save Apollodorus** from Hadrian's political enmity (ch37) despite trying a
  backchannel — a rare case where the book shows him spending political capital and simply losing.
- **He fails to prevent an epidemiological catastrophe he set in motion.** The "uninhabited"
  Americas lie (planted ch03, weaponized ch36) causes real deaths (ch28) that the book never lets
  him undo, and corrects only in the epilogue, after he's dead and forgotten.
- **He cannot resolve his own complicity in Bar Kokhba** (ch45) — the book's most morally
  unresolved chapter; it ends on silence rather than catharsis, deliberately.
- **Institutional overreach costs him a leash, not his life** — the impiety trial (ch27) is
  survived, but the "victory" is a forced public dedication of his own contest under priestly
  oversight, i.e. even his wins carry a tax.
- **Several *planned* technologies never make it onto the page at all** (see Finding 5): the
  generator, arc lighting, reading glasses, the mechanical calculator, ball bearings, the
  typewriter, hydrogen applications, the flying shuttle/water loom, war rockets, coal-gas
  lighting, photography, absorption refrigeration, the centrifugal pump, bulkheaded hulls. This
  isn't a diegetic failure (nothing "goes wrong" for Daniel) — it's a *production* failure, the
  book's own execution falling short of its own plan, and it quietly narrows the book's actual
  demonstrated tech-order below what its bible claims is achievable.

---

## PART 3 — Turning points

The handful of moves the rest of the book's causal chain runs through:

1. **The world map (ch03, week 1).** Zero materials, zero language — pure knowledge transfer that
   converts him from disposable captive to "curiosity worth keeping alive." Nothing after this
   point is possible without it.
2. **The public balloon launch (ch08) → Macer's patronage (ch09).** Converts subsistence-slave
   into a funded workshop with a peculium, staff, and material credit. This is the book's
   Finding-2-relevant "spectacle earns a patron" move, matching the simulator's own
   `identity_cover`/`patron_local` sequencing.
3. **Manned-flight catastrophe → the vow (ch11-ch13).** Not a technology unlock but a permanent
   constraint that reshapes every subsequent risk decision and gives the book's failures moral
   weight rather than just cost.
4. **Citizenship (ch17, ~104-105 AD).** The single cleanest structural turning point: converts
   Daniel from property to legal person, unlocking marriage, ownership, manumitting others, and
   independent enterprise — everything from ch18 onward depends on this.
5. **Marcia (ch22).** Solves the scaling/legal-complexity problem no amount of personal cleverness
   could — the book's first dramatization of "you need a partner whose skills aren't yours."
6. **Trajan's death (ch30, 117 AD).** The single largest external shock in the book: destroys a
   decade of accumulated patronage in one event, and is the hinge that forces the shift from
   "build things Trajan wants" to "build things that don't need an emperor at all."
7. **The Hadrian ocean-map gambit (ch36, ~121 AD).** Converts a twenty-year-old private hobby
   (secretly-funded voyages since ch27, roughly a decade *before* this "official" divergence
   point) into an imperially-sanctioned, survivable-past-Hadrian institution. Worth noting: the
   book's own canon log dates "FIRST DIVERGENCE" to ch36/121 AD, but the *Corva* actually sailed
   and reached the Americas back in ch27, under Trajan, a decade earlier — the private
   infrastructure precedes the public legitimization, which is itself a small but real
   inconsistency in how the book dates its own turning point.
8. **The institution-building pivot (ch38, presbyopia as the trigger).** The clearest thematic
   turning point: Daniel explicitly stops chasing steel/the clock/the ocean personally and starts
   building things that don't need him — and the payoff (Procula, ch52; the crossing, ch53) is the
   book's entire argument for why this was the correct move.

---

## PART 4 — Comparison to the simulator

### Order of discovery

Where the book and the tree can be checked against each other, they largely agree on *sequence
logic* even though neither is tracking the other:

- **Cover story and patron before anything impressive** — book ch01-ch09; sim `path` positions 4
  and 11 of 168, and `00_BRIEFING.md`'s explicit "days 1-180: do nothing impressive" advice.
  Strong match (Finding 2).
- **Measurement before precision metalwork** — the book's Phase C→D chain (precision length
  bootstrapping → thermocouple pyrometry → narrower-but-real steel, `bible/04_tech_schedule.md`)
  matches the sim's own `path` chain almost node-for-node in *shape*: `precision_three_plate` →
  `cap_tol_100um` → `thermometer` → `cap_measure_temp` → `cap_measure_temp_hi` →
  `cap_heat_1600` → `crucible_steel`. This is a genuine and striking convergence — both a novelist
  working from research and a tech-tree designer working from a dependency model independently
  concluded that temperature measurement, not raw heat, is the actual gate on steel quality.
  Where they diverge is the *verdict* at the end of that chain (Finding 3).
- **Numerals/standardization first, in the book; standardization gated by a "units_standards"
  node before numerals, in the sim.** The book has Daniel demonstrate positional numerals in week
  one with no upstream requirement (ch04) — it's framed as a pure, free, immediate win. The sim's
  `path` lists `units_standards` (position 9) essentially alongside `arithmetic_positional`
  (position 10), and `00_BRIEFING.md` insists standards come *before* any recipe is worth writing
  down ("Define your units and make the master artefacts before you write a single recipe down.
  Every number you record without them is worthless to whoever reads it in 250 AD"). The book
  never dramatizes this concern — Daniel's numerals just work, and the "who prints the sea"/
  contest thread never surfaces a units-standardization crisis. This is a place where the
  simulator is arguably more rigorous than the book: a "7" is legible without a standard unit
  system behind it, but the deeper claim (that quantitative science needs agreed units before it's
  transmissible) is exactly the kind of infrastructure problem the book's tech-optimist premise
  tends to wave through.
- **Balloon/germ-theory/hygiene as reputation-only, not technology-gating, moves.** Neither
  `hot_air_balloon` nor anything resembling "germ theory" appears anywhere in the 168-node
  `path point_contact_transistor` listing — they're not technical prerequisites for anything
  downstream in the tree. This matches the book's own arc surprisingly well: the balloon buys
  Daniel patronage and never leads anywhere technologically (it's explicitly walled off by the
  vow after ch13), and the germ/hygiene thread is framed throughout as a credibility- and
  life-saving move, not an engineering one. Both works agree these are *social capital* moves,
  not links in a technology chain — though the book treats that as poignant (Heras's ch42
  deathbed insistence that clean water, not the balloon or gunpowder, was the real achievement)
  where the sim treats it as structurally invisible (reputation/protection stats, off the `path`
  graph entirely).

### Timescale

The headline comparison the brief asks for — "the book covers a specific span; the simulator's
optimiser reaches a transistor in roughly 310-330 years" — needs the caveat from Finding 4: these
are not measuring the same distance. But taking the comparison on its own terms:

- The book's full arc (arrival to death) is **57 years**, ending at a technology level the sim's
  own tree would place somewhere in its first few dozen nodes (paper, printing, numerals, a
  battery, a leaky atmospheric pump, spark-gap radio, a bronze siege bombard) — nowhere near
  `point_contact_transistor`, and the book never claims otherwise; its own outline documents cap
  ambition explicitly ("NEVER BUILT IN DANIEL'S LIFETIME": combustion engines, trains, aircraft,
  submarines, computers — `bible/04_tech_schedule.md`).
  - Cross-checked against the sim's own critical-path floor (`path`'s listed serial chain), a
    Newcomen-class atmospheric steam pump sits at roughly a 29-year floor from a standing start
    (summing the stated `calendar_floor_years` down to and including `steam_atmospheric`), and
    crucible steel at roughly 22 years — both comfortably inside the book's 57-year window, which
    is one more point of agreement: neither work thinks these specific technologies need more
    than a single working lifetime, even though the book insists the *reliability* of steel stays
    unsolved regardless of elapsed time (Finding 3).
- The simulator's full run to a transistor (285-year designed median per `00_BRIEFING.md`;
  312-325 in the corrected fixed-economy default per `naive2/FINDINGS_ROUND2.md`; 358 in one
  interactive `agent`-mode WIN playthrough) is **5-6x the book's entire lifespan**, and the book
  never depicts a story anywhere near that endpoint — its own epilogue, centuries out, still only
  reaches "an Atlantic crossing with a working mechanical sea-clock," a fraction of the distance
  to solid-state electronics.
- Where the two really can be read side by side is the *first several decades*, and there — per
  the "order of discovery" section above — the pacing logic (patron first, measurement before
  metalwork, spectacle as reputation not technology) matches closely. The disagreement shows up
  past that point, on whether specific hard technologies (steel, high-pressure steam) resolve
  within one lifetime at all, not on how fast the opening moves should go.

### What the book treats as a hard bottleneck that the simulator waves through, and vice versa

**Book insists, sim doesn't obviously model:**
- Reproducible/production-grade crucible steel *staying unsolved* regardless of elapsed time or
  capital, because the residual wall is carbon/atmosphere control specifically, not a heat
  threshold (Finding 3).
- High-pressure steam (Watt-class) as **permanently** blocked absent reproducible steel
  (`bible/04_tech_schedule.md`'s "CORRECTLY BLOCKED" list) — yet the sim's own critical-path floor
  reaches `steam_watt` and even `steam_high_pressure` well inside 57 years (roughly a 50-year
  floor by the same node-summing method above), suggesting the tree, at least along its bare
  critical path, doesn't carry forward the book's atmosphere-control caveat as a separate,
  binding constraint on those later steam nodes either.
- The specific, singular human cost of a failure (Geta's hands, Sabinus's death, Naso's ankle) as
  a permanent narrative weight rather than a recoverable statistic.
- The book's insistence that political patronage is *categorically* fragile in a way money can't
  buy back (Trajan's death wiping out a decade of standing in one event) — the sim's equivalent
  hazards (crisis knowledge-loss, plague, "denounced as a magician") are all modeled as
  probabilistic and recoverable-with-effort (F4, F7 in the WIN report), never as a single
  irreversible narrative hinge the way Trajan's death functions in the book.

**Sim insists, book waves through:**
- Standardized units/measurement infrastructure as a prerequisite for *any* number being useful
  to a future reader (`00_BRIEFING.md`) — the book never dramatizes this risk even though its own
  entire second-half thesis is about knowledge transmission across time.
- A quantified, recurring, empire-wide knowledge-loss hazard (the Third Century Crisis, 235-284
  AD) that punishes *not* building redundant institutions early — the book's institution-building
  urgency is motivated by Daniel's own mortality and the fragility of imperial patronage, never by
  a named future sacking/dark-age risk on this scale (the book's story ends around 155 AD/coda
  ~190+ AD, before 235 AD; it simply never reaches the era the sim treats as the central
  stress-test of "did you hedge enough").
- Staff/headcount as a hard, separate resource distinct from money or founder-hours (the
  `school_founded` scholar-count wall, F5) — the book gestures at needing apprentices and
  successors (Tyche, Vitalis, Chloe, Ulpia) but never frames it as a quantified bottleneck the way
  the sim's `staff_needed: {scholars:25, artisans:20}` does.

### What happens in the book that the simulator has no way to represent at all

Covered in depth in Finding 6: named individual injury and death as permanent narrative weight;
unresolved moral guilt (the Americas lie, Bar Kokhba complicity) that the story deliberately never
discharges; the protagonist's own status as enslaved property for the first six years of the
story (the sim's founder is never owned — he starts with 10,300 denarii of gold and legal
personhood the book's Daniel doesn't get until ch17); grief and family relationships across a full
adult lifetime (Heras's death, Marcia's cancer, a daughter who can never legally hold what she's
capable of running); the specific texture of language loss and loneliness (English narration
picking up Latin cadence over decades, `V2_MASTER_CONTEXT.md` §2). None of this is a gap the
simulator could plausibly close — it's the difference in kind between a resource-optimization
model and a novel, not a missing feature.

### What the simulator models that the book never has to deal with

Covered in Finding 7: five civilizations compared side by side under different cultural/
institutional coefficients; a fully itemized, adversarial economy (mine operating costs, credit
limits, debt interest, resource throttling) running continuously under every decision, which the
book only ever samples at dramatic moments (a specific sesterce figure for a specific transaction,
`V2_DANIEL_FINANCES.md`); a quantified, dated, empire-scale knowledge-loss hazard centuries past
the book's own story window; and a target technology (the transistor) an order of magnitude
beyond anything the book's premise ever aims for.

---

## A note on confidence

The book side of this report leans heavily on `CHAPTER_SUMMARIES.md` (a rolling AI-generated
summary chain, explicitly flagged by its own header as subject to "detail loss/drift" between
source text and summary) cross-checked against one full chapter read (`ch21.md`) and the book's
own internal audits (`TECH_GAP_AUDIT.md`, `TIMELINE_TEXTURE_AUDIT.md`), which independently
confirm the summary chain's broad shape while adding the plan-vs-execution gap noted in Finding 5.
I did not read all 53 chapters of primary prose; where a claim rests only on the summary chain and
matters to a ranked finding, I've said so. The simulator side leans on `path`/`civs`/`validate`
output I ran directly, plus the substantial playtest record already in `rome/playtest/` (which
represents many more play-hours than this pass could add) rather than a fresh long session, per
the brief's instruction to avoid duplicating or disturbing concurrent editing work.
