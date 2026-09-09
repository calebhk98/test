# Module 70: Medicine, Public Health and Biology

This module is not a side quest. Two events are fixed on your calendar
whether you plan for them or not: the Antonine Plague (165-180 AD) and the
Plague of Cyprian (249-262 AD). Each one will kill a large fraction of the
population of the Empire, disrupt every supply chain your programme depends
on, and, if you have not prepared, kill the trained people your institute
took a generation to build. A furnace can be rebuilt in a season. A dead
school of scholars cannot. Everything else in this document, metallurgy,
chemistry, glass, precision mechanics, is worthless if the people who know
it are dead of dysentery or smallpox before they can teach a second
generation. Read this module first, or at least alongside `school_founded`,
not after.

The entries below are ordered roughly by how soon you need them, not
alphabetically: sanitation before germ theory before variolation before
anything clever.

---

### sanitation_antisepsis - Boiled water, handwashing, wound irrigation, quarantine (*aqua fervens*, *manus lotae*, no single Roman term covers the practice)

**What it is / why you want it.** A short list of habits that cost nothing
but labour and argument, and that will save more lives in this Empire than
every machine described in this document combined. In order of lives saved
per hour of effort spent persuading people to do them: (1) handwashing
before touching a wound, a birth, or food, with plain water or wine, (2)
boiling drinking and wound-irrigation water, (3) isolating the visibly sick
from the well, (4) never reusing a dressing on a second patient or a second
wound, and burning soiled dressings rather than washing and rewearing them,
(5) heating metal instruments in a flame before cutting, (6) general removal
of standing waste from where people sleep and eat. Every one of these is
older than the theory that explains why it works.

**Why you would never guess this.** You would guess it fine in the abstract;
the trap is thinking the existing Roman infrastructure already does it. It
does not, and in one specific case it actively works against you.

**Prerequisites.** `distillation_alcohol` (20_chemistry.md#distillation_fractional)
for a cheap, reliable disinfecting spirit; otherwise no material prerequisite
at all, only argument and authority.

**Roman-available inputs.** Water, already piped by aqueduct into most
cities of any size (Frontinus, *De Aquaeductu*, describes Rome's own supply
in detail). Wine, universal, cheap in its rough forms, and mildly
antiseptic on its own even before distillation. Linen for dressings,
already produced at scale. Bronze or iron surgical tools, already
manufactured to a high standard (see `surgery_practice` below).

**Procedure.** (1) Boil drinking and irrigation water at a rolling boil, not
a simmer, for the time it takes to recite a short prayer twice through,
roughly a few minutes; let it cool in a covered clean vessel, not an open
one that recollects dust. (2) Wash hands in hot water, then in wine or
(once available) diluted distilled spirit, before touching any open wound
or delivering a child, and again after touching a corpse or a dressing
before touching a living patient. (3) Set aside a separate room or tent for
anyone with fever, cough, or rash, away from the healthy, with its own
water vessel and its own attendant if you can spare one. (4) Burn used
dressings in a fire pit rather than washing and reissuing them; if cloth is
too scarce to burn, boil it at a full rolling boil for a long soak, not a
rinse, before reuse, and never reuse a dressing from a suppurating wound on
a clean one. (5) Pass blades and probes through a flame until they glow
faintly, then let them cool in clean air, not in a cloth, before cutting.
(6) Route latrine and kitchen waste away from any well, cistern, or food
storage area, downhill and downstream of both.

**How you know it worked.** Compare two otherwise similar groups of
patients, one treated this way and one treated by ordinary practice, over
a season. Track how many wounds turn foul-smelling and swollen (Galenic
practice reads this as "laudable pus," a good sign; it is not) versus how
many close cleanly. Track how many of the sick-room group's healthy
household members fall ill compared to households without isolation. The
gap will be visible within a single campaign season or birthing season; you
do not need to wait years.

**Failure modes.** Boiling water that is then poured back into the same
dirty vessel it came from undoes the point. "Isolating" the sick in the
same room with a curtain, rather than a separate airspace, does very
little. Reusing a wine-soaked rag as a general-purpose cloth instead of
discarding it after one wound spreads exactly what you were trying to stop.
The single most common failure is treating this as a one-time announcement
rather than a standing order that must be checked, since old habits (see
below) reassert themselves within weeks of inattention.

**Cost & labour.** ESTIMATED (basis: prices.json wage rates,
labourer 0.075 den/hr, scholar 0.4 den/hr). Roughly 300 personal hours to
work out the protocol, write it down, and train the first cohort of
attendants who will enforce it. Ongoing labour is mostly fuel-gathering and
water-boiling, on the order of 900 labourer-hours per year for an
establishment the size of a legion valetudinarium or a large household;
capital is a handful of large clean boiling vessels, on the order of
400 denarii, with annual upkeep (fuel, linen replacement) around
300 denarii. Calendar time: effective the day you start; no maturation
floor. Revenue: not a product in itself, but it is the single highest
return-per-denarii item in this entire document, since it converts
directly into fewer dead skilled workers.

**Danger.** Physically, almost none, beyond ordinary burns from boiling
water and flame-sterilising blades. Socially, the danger is being seen to
imply that established physicians and the "laudable pus" doctrine they were
trained under are simply wrong, which they are; sell this first to an
audience that already measures results rather than argues from authority.
The Roman army is that audience: it already runs valetudinaria (military
hospitals), already has an officer class used to giving and following
standing orders, and already tracks who returns to duty and who does not.
Convince a camp prefect with a controlled comparison inside his own
hospital before you try to convince a senator with a lecture.

**On the existing Roman infrastructure, honestly assessed.** Rome already
has aqueducts, public latrines, and public baths, and it is tempting to
assume "the sanitation is already handled." Some of it genuinely helps;
some of it actively spreads disease, and you need to know which is which
before you praise any of it in public.

*Aqueducts*: genuinely helpful, when the water is used for drinking,
cooking, and flushing waste away rather than for standing storage. Fast-
flowing piped water from a clean upland source is a real public health
asset; it is the single reason Roman cities could sustain the populations
they did.

*Public latrines (foricae)*: mixed. Removing waste from streets and homes
into a sewer (the Cloaca Maxima being the most famous example) is a real
benefit over a city with no sewer at all. But communal multi-seat latrines
were commonly serviced with a single shared sponge on a stick (a
*tersorium*), rinsed in one shared bucket of salted water or vinegar and
passed from user to user. This is a textbook fecal-oral transmission
device, not a hygiene measure, and it should be one of the first things you
replace, with individual disposable material or private facilities, even
though it will look to a Roman like you are removing something civilised.
(A modern parasite-load study of Roman-era latrine sediments found no
improvement over pre-Roman levels despite the infrastructure investment;
attributed, unverified for exact figures, but the qualitative finding is
consistent with the shared-sponge mechanism above and worth citing to a
sceptical physician as evidence the old practice is not working.)

*Public baths (thermae)*: net negative for infectious disease, however
pleasant and however genuinely useful they are for general wellbeing and
social order. Large volumes of standing warm water, changed infrequently
relative to the number of bathers, shared by the well and the sick alike,
with skin lesions, open sores, and respiratory secretions all going into
the same pool, is close to an ideal transmission environment for skin
infections and several other classes of disease. You will not be able to
close the baths, and you should not try; instead push for more frequent
water changes, separate facilities (or at minimum separate hours) for
anyone visibly unwell, and drainage that does not double back into the
same pool.

**Confidence: HIGH.** The germ-theory mechanism behind each practice is
textbook modern medicine; the description of Roman aqueducts, latrines, and
baths is well attested archaeologically and in Frontinus and Vitruvius. The
specific claim about the shared *tersorium*'s effect on measured parasite
loads is flagged MEDIUM, since it rests on a modern archaeological
inference rather than a Roman-era measurement.

---

### germ_theory - Germ theory of disease (no Roman term; the closest existing idea is Varro's *semina morbi*, "seeds of disease")

**What it is / why you want it.** The demonstration, not merely the
assertion, that specific invisible living agents cause specific diseases
and spread by specific routes, replacing the idea that disease is an
imbalance of the four humours (blood, phlegm, yellow bile, black bile). You
need this before anyone will accept sanitation, quarantine, or variolation
as more than superstition, because right now the entire trained medical
profession of the Empire is invested, financially and intellectually, in
the humoral model.

**Why you would never guess this.** The non-obvious part is not the theory,
which you already know, but the fact that a Roman audience already has a
half-built conceptual slot for it. Varro, a full generation before your
arrival, already speculated in writing that marshes breed "certain minute
creatures, invisible to the eye, that float in the air and enter the body
through the mouth and nose and cause serious disease" (*De Re Rustica*
1.12.2, attributed, unverified for exact wording, but the general claim is
a standard citation in histories of epidemiology). Anchor your demonstration
to that existing idea rather than presenting germ theory as a total
foreign novelty; you are completing a Roman thought, not importing an alien
one.

**Prerequisites.** `glass_bead_microscope` (30_glass_optics.md#glass_bead_microscope),
`glass_lab_ware` for sealed and swan-necked flasks, `distillation_alcohol`
is useful but not required for the core demonstration.

**Roman-available inputs.** Clear or near-clear blown glass, already a
mature Roman craft (glass_clear_cristallo). Meat or vegetable broth. Pond
or ditch water for the first microscope samples. A skilled glassblower to
draw the long curved neck of a swan-neck flask, which is well within the
range of existing lamp-working and blowing technique used for other narrow-
necked vessels.

**Procedure.** Run three separate, independent demonstrations, and keep
them independent so a sceptic cannot dismiss all three on one objection.

(1) **The bead microscope.** Draw a single small glass bead on the end of a
rod, polish it, and mount it in a small metal frame so a sample can be held
at its focus a hair's breadth away (full construction in
30_glass_optics.md#glass_bead_microscope). Put a drop of stagnant pond or
ditch water on the mount. At full focus you will see small moving bodies:
blobs that change shape as they move (protozoa, later called animalcules),
and, at the very limit of what a good bead can resolve, faint moving rods
and threads (the largest bacteria and spirochetes). This alone will not
convince a Galenist of anything; it only shows there is a hidden world, not
that it causes disease.

(2) **Boiled versus unboiled broth, sealed versus open.** Divide broth into
four vessels: boiled and sealed, boiled and left open to air, unboiled and
sealed, unboiled and left open. The unboiled vessels turn cloudy and foul
quickly regardless of sealing, since they already carry what will spoil
them. Of the two boiled vessels, the open one turns cloudy within days; the
sealed one stays clear far longer. The strongest version of this test is
the swan-neck flask: blow a flask with a long, thin neck bent down and then
back up in an S-curve, boil broth inside it, and leave the neck open to the
air rather than sealed shut. Air can pass freely in and out, but dust and
the bodies riding on it settle in the low bend of the curve and never reach
the broth; the broth stays clear indefinitely. Break or tilt the neck so
the low bend is bypassed, or wipe the inside of the bend and let the
washings run down into the broth, and it clouds within days. This is the
single most persuasive demonstration you have: it shows that clear air by
itself does not spoil broth, but airborne matter that has had a chance to
settle out of that air does, which flatly contradicts spontaneous
generation of decay from the air itself.

(3) **Treated versus untreated wounds.** Take a cohort of similar wounds
(the army will hand you plenty), assign them by simple alternation, not by
severity, to two protocols: the sanitation_antisepsis regimen above, or
standard Galenic practice (poultices, unboiled dressings, encouragement of
suppuration as "laudable pus"). Record how many in each group develop
fever, how many suppurate badly, how many die, over the following month.

**How you know it worked.** The broth test is self-demonstrating to anyone
who watches both flasks for two weeks side by side; no instrument or
argument is needed beyond patience and a sealed control. The wound
comparison needs a large enough cohort, several dozen wounds per arm at
minimum, that the difference is not plausibly chance; write the counts down
before and after so no one can later dispute what was observed.

**Failure modes.** A poorly sealed "sealed" flask that still lets dust in
through a crack gives a false negative and will be seized on by opponents.
A wound cohort too small or too dissimilar between arms (all the worst
wounds by chance ending up in one group) produces an ambiguous result.
Galenists will reinterpret any result inside humoral vocabulary rather than
abandon it outright; expect this, and do not expect a single demonstration
to convert the profession, only to convert individual sceptics who watch it
themselves.

**Cost & labour.** ESTIMATED, cross-referenced against the tech tree's own
figure for this node: roughly 350 personal hours and 1500 scholar-hours
(0.4 den/hr) over about two years, capital around 250 denarii, annual
upkeep around 150 denarii (see rome/data/tech_tree.json, node
`germ_theory`, marked confidence C in that file). This is cheap. The
expense is in years and in status, not in denarii.

**Danger.** Physical risk is minimal. Social risk is real: you are telling
established, wealthy, well-connected physicians that their entire training
is built on a wrong premise, publicly, with evidence. Expect professional
hostility, and possibly accusations of impiety or sorcery if you frame the
invisible agents as anything other than natural creatures (see "How not to
be executed for this," below). Do this under a patron, and do the broth
demonstration in a controlled setting with witnesses you have already
primed, not as a street spectacle.

**Confidence: HIGH** on the physics and biology (the swan-neck flask
experiment is real, historically Pasteur's, and needs nothing but
glassblowing skill Rome already has). **MEDIUM** on the Varro citation's
exact wording, flagged attributed/unverified above.

---

### variolation - Smallpox inoculation (no Roman term; propose *insitio variolae*, "grafting of the pox," coined for this purpose)

**What it is / why you want it.** Deliberately giving someone a small,
controlled dose of smallpox material through the skin, so they suffer a
mild, localised case and gain lasting immunity, rather than risking the
severe, often fatal case that comes from breathing in the disease
naturally. It is the single most important item in this whole module if
the Antonine Plague turns out to be smallpox, and worthless if it is not
(see below).

**Why you would never guess this.** It looks reckless: deliberately
infecting a healthy person with a lethal disease. The non-obvious part is
that the dose and the route matter enormously, and that societies without
any Western scientific medicine at all had already worked this out
centuries before the Roman period you are in, entirely empirically, by the
simple observation that people who survive a mild dose of the pox never
catch it again.

**Prerequisites.** `germ_theory` (to explain why it works and to defend it
against Galenic objection), `sanitation_antisepsis` (for the inoculation
site and for keeping the deliberately-infected inoculee isolated during
their illness).

**Roman-available inputs.** No special material beyond an active, mild case
of smallpox to take material from, and a clean blade or needle. This is a
technique, not a substance you must import.

**Procedure.** (1) Identify a **mild** case: a patient with a modest number
of pustules, not the confluent, densely packed, haemorrhagic pattern that
marks a severe case. Never take material from a severe case; you inoculate
severity as well as immunity. (2) Take material at the right stage: the
clear or slightly turbid fluid from an unbroken pustule around the eighth
to tenth day of the eruption gives a smaller, better-controlled dose than
thick mature pus. (3) Make a small superficial scratch or series of
scratches, not a deep cut, on the outer upper arm, and work a minimal
amount of the material into it, then cover it lightly. (4) Isolate the
inoculee for the full course of their resulting illness, as you would any
smallpox case, since they are contagious. (5) Keep the chain going by
taking fresh material arm-to-arm from one inoculee's pustule to inoculate
the next, rather than repeatedly returning to severe natural cases, since
serial arm-to-arm passage tends to keep the material's severity consistent.

**How you know it worked.** The inoculee develops a small local pustule at
the scratch site within a week or two, with mild fever and a light,
localised rash, then recovers; afterward, deliberately exposing them to a
active natural case (a real test, historically done) produces no reaction
at all, confirming immunity.

**Dose problem, stated plainly.** This procedure kills a meaningful minority
of the people who receive it, because it is still a live infectious dose
of a genuinely lethal disease, and there is no reliable way in this period
to titrate it precisely. Historical inoculation programmes in the 18th
century (the best documented pre-vaccine data available, not Roman data)
report variolation case-fatality on the order of roughly 1 in 100 to 2 in
100, MEASURED from those programmes but not from any Roman source, against
roughly 20 to 30 in 100 for naturally acquired smallpox in the same
records. Treat the specific ratio as directionally solid and the exact
percentages as ESTIMATED for your Roman context, since outcomes depend
heavily on inoculator skill, patient nutrition and age, and the strain
circulating that season, none of which you can measure precisely here.

**On priority.** This technique long predates Edward Jenner, who only
formalised the safer cowpox version in 1796 (see `vaccination_cowpox`
below). It was practised in parts of Asia, including nasal insufflation of
powdered scabs recorded in China (exact date of origin uncertain, variously
placed anywhere from the 10th to the 16th century in different secondary
accounts, attributed, unverified), and it was practised in parts of West
Africa and brought to public attention in the English-speaking world by an
enslaved West African man's account given to a Boston minister in the
early 18th century (attributed, unverified for exact date). Do not present
this as a modern Western invention to any audience; it has no single
inventor and was independently arrived at by direct observation of who
gets smallpox twice and who does not.

**On the Antonine Plague specifically.** You know it arrives around 165 AD.
You do not know for certain what it is. Ancient descriptions, including
what survives of Galen's own account of an epidemic he witnessed
(attributed, unverified for exact passage and title), describe fever and a
pustular or dark rash, which is consistent with smallpox but is also
broadly consistent with measles, and modern historians genuinely disagree
about which disease it was, or whether it might have been something else
entirely. This is a real, unresolved uncertainty, not a gap in your
knowledge alone. The practical consequence: do not build your entire
survival plan on variolation working, because if the epidemic turns out to
be measles, smallpox material will do nothing for it (there is no
equivalent pre-modern inoculation technique for measles that reliably
works). Build the pathogen-agnostic layer, `quarantine_publichealth` and
`sanitation_antisepsis`, as your primary defence regardless of which
disease it is, and treat variolation as a powerful but conditional bonus,
to be validated in the decades before 165 AD against whatever pox or rash
diseases you can actually observe circulating in the interim, so you know
by direct observation, not guesswork, whether what is coming presents as
smallpox (deep, umbilicated pustules concentrated on the face and limbs)
or measles (a fine, flat rash starting at the hairline, preceded by small
white spots inside the cheeks, a genuine and teachable distinguishing
sign).

**Failure modes.** Taking material from a severe case, or too much of it,
produces a severe inoculated case indistinguishable in danger from natural
infection. A dirty blade transmits an unrelated disease along with the
inoculation. Failing to isolate the inoculee turns your controlled
demonstration into an outbreak.

**Cost & labour.** ESTIMATED. Low material cost, since the "material" is a
technique applied to naturally occurring cases; the real cost is the
years of careful, small-scale, low-stakes trial needed to build a track
record before you inoculate anyone politically important (see "How not to
be executed for this").

**Danger.** Physical: a real, non-trivial chance of killing the person you
inoculate, smaller than the chance of dying from a natural case but not
zero, and this must be stated to anyone whose consent you seek. Social:
enormous, since a single visible death from an inoculation you performed on
a prominent family's child is the single most dangerous event described
anywhere in this module.

**Confidence: MEDIUM.** The mechanism and the general historical mortality
comparison are solid (well documented in the 18th century record).
**LOW** on whether the Antonine Plague is even smallpox at all, which is
flagged explicitly above and must not be papered over.

---

### vaccination_cowpox - Vaccination from cowpox (*variolae vaccinae*, "pox of the cow," a term you may as well keep since it is already descriptive Latin)

**What it is / why you want it.** The safer successor to variolation: using
material from cowpox, a related but much milder disease of cattle (and the
humans who milk them), instead of live smallpox, to confer immunity without
the roughly 1-in-100 death risk of variolation.

**Why you would never guess this.** The connection is not obvious from
first principles; it comes from a specific, repeatable folk observation
that dairy workers who had caught cowpox from their animals' udders never
seemed to catch smallpox afterward. You need that same specific
observation, made by you or reported to you, before the idea has anything
to act on.

**Prerequisites.** `variolation` (to have the arm-scratch technique and the
isolation discipline already working), `germ_theory`, ongoing veterinary
surveillance under `veterinary_and_agriculture_link` below.

**Roman-available inputs.** Cattle, universal across the Empire. Dairying
and milking, already a standard rural occupation Columella writes about at
length. No new material beyond an actual cowpox outbreak to find.

**Procedure.** (1) Establish standing surveillance of dairy herds and their
milkers for pustular lesions on the udder and on milkers' hands, since
cowpox is sporadic and you cannot manufacture an outbreak on demand. (2)
When a genuine case is found, confirmed by the mild course it takes in the
milker (a few local pustules, little to no serious systemic illness, unlike
smallpox), take material from a fresh pustule exactly as in variolation.
(3) Inoculate by the same superficial arm-scratch method. (4) Maintain the
chain by arm-to-arm transfer from each successful inoculee's resulting
pustule to the next person, since natural cowpox outbreaks are too
infrequent to serve as the sole source. (5) Confirm protection, once you
have enough confidence in a maintained line, by later exposing a small
number of consenting, informed volunteers to variolation material and
observing no reaction, exactly as the historical 1796 test did.

**How you know it worked.** The vaccinated inoculee develops a small, mild
local pustule and little else, and subsequently shows no reaction to a
variolation challenge that would otherwise produce a full local pustule.

**What this requires beyond variolation.** Reliable identification of true
cowpox against other, non-protective cattle skin conditions, which takes
practice and a few false starts. A continuously maintained arm-to-arm chain
of living material, since cowpox does not reliably keep as dried scab
material the way smallpox pustule material can. And, eventually, the
willingness to run the ethically uncomfortable but historically real
confirmatory challenge test described above.

**Failure modes.** Confusing an unrelated bovine skin lesion for cowpox
gives a false, unprotective inoculation that is then wrongly trusted.
Losing the maintained chain (no fresh natural case for too long, and no
surviving inoculee line) forces you back to hunting for a new natural
outbreak.

**Cost & labour.** ESTIMATED, similar order to variolation but with an
added, ongoing veterinary surveillance cost: labourer-hours to inspect
herds regularly, on the order of a few hundred per year across a modest
number of estates, plus the same scholar oversight as variolation.

**Danger.** Physical risk to the vaccinated person is much lower than
variolation, close to negligible by comparison, though not literally zero.
Social risk is lower than variolation for the same reason: fewer visible
deaths to explain.

**Confidence: MEDIUM.** The biology is solid and historically proven
(Jenner, 1796, a well documented case). Confidence is capped at MEDIUM
here because the practical bottleneck, finding and confirming a genuine
Roman-era cowpox outbreak on demand, is not something any source can give
you a timeline for; you may wait years for the first usable case.

---

### quarantine_publichealth - Quarantine, clean water, sewage separation and food inspection (*custodia*, *cura aquarum*, no single Roman institutional term covers the whole programme)

**What it is / why you want it.** The pathogen-agnostic layer that protects
you whether the coming plague is smallpox, measles, or something else
entirely: isolation of the sick, cordons around afflicted areas, tracking
who has been in contact with whom, protected water, separated sewage, and
inspected food, all backed by enough political authority to actually be
enforced.

**Why you would never guess this.** The mechanism is intuitive once you
believe in contagion; the hard part is entirely political, not medical.
Rome has no census-taking public health bureaucracy and no statistics in
the modern sense, so "contact tracing" here means something much cruder and
more manual than the phrase suggests, and getting a magistrate to act on
any of it requires fitting your request into categories of authority that
already exist, rather than asking for a new one.

**Prerequisites.** `germ_theory`, `sanitation_antisepsis`, `school_founded`
(this is explicitly gated on having an institution behind you in the tech
tree's own data; see rome/data/tech_tree.json, node `plague_preparedness`,
which lists `germ_theory` and `school_founded` as prerequisites).

**Roman-available inputs.** Existing Roman civic machinery you can extend
rather than invent from nothing: the aediles, who already have a legal
market-inspection and public-order role; the curator aquarum, who already
oversees the aqueduct and water supply; local collegia (guilds), which
already function as membership registries and mutual-aid bodies and can
double as reporting networks; funeral colleges and undertakers, who already
see every death in a district and can serve as an informal mortality
register; midwives, who already see every birth.

**Procedure, isolation and contact tracing.** (1) Set the isolation period
by the disease's own observed course, not by later convention: for
smallpox, roughly ten to fourteen days from exposure to first symptoms,
then another three to four weeks of active infectiousness until all scabs
have fallen away, so a full isolation window of a case is close to a
month and a half from first exposure to safe release; watch known contacts
for the shorter incubation window, ten to fourteen days, before clearing
them. (Do not import the later, unrelated "forty days" convention from
Mediterranean maritime quarantine practice as though it were derived from
this disease's biology; it was not.) (2) In a pre-statistical society, do
contact tracing through the reporting nodes above: task collegium officials
and household heads with naming who a newly sick person lived with, worked
with, and was recently visited by, and physically move those named contacts
into a watched but not yet isolated status until their own window passes.
(3) Use a physical cordon, a guarded boundary around an afflicted
household, ship, or town quarter, when a cluster is identified, with
food and water passed in rather than people passed out, enforced by
whatever armed authority the local magistrate controls.

**Procedure, water and sewage.** (1) Confirm that no latrine, cesspit, or
sewer outflow sits upstream of, or drains toward, any well or aqueduct
intake serving drinking water; relocate whichever is easier to move. (2)
Where night soil (human waste) is used to fertilise market-garden crops, a
real and attested Roman-era practice, insist on a long composting or aging
period before it touches food crops, rather than fresh application. (3)
Keep drinking cisterns covered and cleaned on a fixed schedule rather than
left open to dust and vermin.

**Procedure, food inspection.** Extend the aediles' existing market-
inspection authority explicitly to cover spoiled meat and fish (a known
risk in a garum-producing economy where fermented fish products are a
dietary staple) and contaminated grain stores, with a simple sense-based
standard your inspectors can apply without instruments: no strong off-odour,
no visible mould on grain, no discoloured or slimy fish or meat.

**How you actually get a Roman magistrate to act.** Do not present any of
this as new medicine; present it as an extension of duties the magistrate
already holds and is already judged on. An aedile already loses standing if
the grain supply sickens people; frame food inspection as protecting his
existing mandate, not creating a new one. A curator aquarum already answers
for the water supply's reputation; frame water protection the same way.
Above all, get results first in a setting where outcomes are already
tracked and where the decision-maker is used to acting on evidence rather
than precedent: the legion, again, is your best first client, since a
camp prefect who sees fewer men in the valetudinarium after adopting your
quarantine order will act on that alone, and a legion's endorsement is a
powerful lever to bring to a civilian magistrate afterward. Secure a
patron of real standing (a senator, a provincial governor, eventually
someone close to the emperor) before you approach any magistrate who does
not already know you, since an unknown foreigner asking to cordon off part
of a town will otherwise be treated as a threat to public order rather
than a defender of it.

**How you know it worked.** Fewer new cases appearing outside a cordon than
inside it, over the course of a single outbreak; fewer contacts falling ill
after being identified and watched early than a comparable group not
traced. These comparisons are visible within one outbreak, without needing
long-run population statistics you do not have.

**Failure modes.** A cordon with no enforcement is a suggestion, not a
quarantine, and will be crossed. Contact tracing through collegium
officials fails where a district has no collegium coverage, typically the
poorest quarters, which is exactly where crowding makes disease spread
fastest; do not assume your reporting network's coverage is uniform.
Food inspection by untrained aediles' staff without a clear sense-based
standard degenerates into arbitrary enforcement or bribery.

**Cost & labour.** ESTIMATED, cross-referenced against the tech tree's own
figure for this node: roughly 700 personal hours, 2500 scholar-hours and
6000 labourer-hours over about four years, capital around 6000 denarii,
annual upkeep around 2000 denarii (rome/data/tech_tree.json, node
`plague_preparedness`, confidence C in that file, and explicitly flagged
there as "the highest expected-value defensive investment in the game").

**Danger.** Political, more than physical: cordoning off part of a town, or
publicly declaring a food supply contaminated, threatens vested interests
(landlords, grain merchants, sometimes the magistrate's own family
business) and will generate enemies. Do this with a patron's authority
behind you, in writing, before you act.

**Confidence: MEDIUM.** The public health mechanisms are well attested and
well understood. The specific isolation-period numbers above are DERIVED
from smallpox's own known incubation and infectious course, not from any
Roman record, and are only as reliable as the assumption that the coming
epidemic follows that course (see the honest uncertainty flagged under
`variolation`).

---

### anaesthesia_analgesia - Pain relief and anaesthesia (*sedatio doloris*)

**What it is / why you want it.** The difference between what genuinely
dulls pain or produces sleep with real, known dangers, all already
available to you, and what produces true surgical unconsciousness, which
needs chemistry you have to build.

**What is genuinely available now.** Opium poppy (*papaver*, *Papaver
somniferum*, already cultivated and described by Dioscorides), the dried
latex of the unripe seed pod, taken orally or in a wound dressing, gives
real and reliable pain relief and sedation, but the effective and the fatal
dose are not far apart, and it slows breathing; overdose kills by
suffocation, and repeated use produces dependence. Mandrake (*mandragora*,
*Mandragora officinarum*) and henbane (*hyoscyamus*, *Hyoscyamus niger*),
both known to Dioscorides, contain tropane alkaloids that produce genuine
sedation and delirium, but potency varies wildly by plant, season, and
preparation, and the margin between a sedating dose and a fatal or
permanently damaging one is narrow and unpredictable; historical "soporific
sponges" soaked in mixtures of these plants with opium, held to a patient's
nose before surgery, gave inconsistent and sometimes dangerous results, not
reliable unconsciousness. Wine and other alcohol dull pain mildly at best,
at the cost of impairing the patient's cooperation, provoking vomiting
(dangerous in an unconscious or semi-conscious patient), and thinning the
blood, worsening bleeding during surgery. None of these four, alone or
combined, reliably produces the still, unconscious, cooperative-by-absence
state that real surgical anaesthesia requires.

**What follows, and what it needs.** Diethyl ether and chloroform are true
general anaesthetics, first used surgically in 1846 and 1847 respectively,
historically. Ether needs ethanol (from `distillation_alcohol`) reacted
with concentrated sulfuric acid under controlled, moderate heat (see
20_chemistry.md#organic_reagents_first_tier for the full procedure and the
warning that overheating gives flammable ethylene instead of ether).
Chloroform needs a chlorine source, built from pyrolusite and hydrochloric
acid, absorbed into slaked lime, then reacted with ethanol or acetone in a
haloform reaction (same cross-reference). Both are therefore downstream of
a working acid industry, not available at the same time as the plant-based
options above.

**Why surgery without anaesthesia is limited to about two minutes.** A
conscious patient in severe pain can hold still, cooperate, and avoid going
into unmanageable shock for only a short window, historically on the order
of a couple of minutes for major cutting, which is why the fastest
pre-anaesthesia surgeons trained specifically for speed (a famous
historical case, a 19th century surgeon reported to amputate a leg in
under thirty seconds specifically to stay inside that window, attributed,
unverified for the exact figure but broadly consistent with the surgical
literature of the period). This hard limit is what makes amputation
practicable without anaesthesia, since it can be done fast, and makes any
exploratory or sustained internal surgery essentially impossible without
it, since no patient can hold still and survive the shock of an open
procedure lasting many minutes while fully conscious.

**How you know it worked.** For the plant preparations: the patient becomes
drowsy and reports less pain but remains rousable and breathing evenly; if
breathing slows and becomes shallow or irregular, you have overdosed and
must act immediately (keep the patient upright, stimulate them, do not
give more). For ether or chloroform: the patient loses consciousness
smoothly, their limbs relax, and they no longer respond to a pinch, while
breathing remains steady; this state is reversible within minutes of
removing the vapour.

**Failure modes.** Overdose with opium, mandrake, or henbane causing fatal
respiratory depression is the most common and best-documented danger of
the plant-based route. Ether is extremely flammable and its vapour, heavier
than air, can travel along a floor to a distant open flame or coal, a real
hazard in a candlelit or hearth-lit surgery; chloroform is not flammable in
the same way but has a narrower margin between an anaesthetic dose and a
fatal one, and can cause sudden cardiac arrest even in skilled hands,
historically documented and part of why ether, despite being more
dangerous around fire, remained in wide use alongside it.

**Cost & labour.** ESTIMATED. The plant-based route costs almost nothing,
since the plants are already cultivated or wild-gathered; the risk is
entirely in dosing, which must be learned by careful titration on a small
number of consenting volunteers before wide use. The ether and chloroform
route inherits the full labour and capital cost of `organic_reagents_first_tier`
in 20_chemistry.md, which is not small.

**Danger.** As above: overdose death with the plant route, fire with ether,
sudden cardiac events with chloroform. Socially, giving a patient something
that renders them insensible and unresponsive, indistinguishable to an
onlooker from death or possession, is exactly the kind of thing that
invites accusations of sorcery; perform it only with witnesses already
primed to expect it.

**Confidence: HIGH** on the plant pharmacology and its dangers (well
attested by Dioscorides and by later medieval and early modern surgical
practice). **HIGH** on the ether and chloroform chemistry, which is
textbook. **MEDIUM** on the "two minutes" endurance figure, which is a
rough historical characterisation, not a measured constant.

---

### surgery_practice - Surgical practice (*chirurgia*)

**What it is / why you want it.** Roman surgery, contrary to the modern
stereotype of ancient medicine as pure superstition, is genuinely
competent in several respects, and this entry is mostly about specific,
targeted upgrades rather than starting from nothing.

**What Rome already does well.** Cataract couching (displacing a clouded
lens out of the line of sight with a fine needle inserted at the eye's
edge, restoring rough vision) is a real, described Roman procedure (Celsus,
*De Medicina*, book 7, HIGH confidence this general operation is described
there). Trepanation (cutting a hole in the skull, for injury or to relieve
pressure) is well attested archaeologically by skull specimens showing
healed bone growth around the opening, meaning patients regularly survived
it. Amputation is practised and, combined with the speed discussed under
`anaesthesia_analgesia`, is one of the more survivable major procedures of
the period. The surviving Roman surgical instrument kit is genuinely
impressive: scalpels, various forceps, bone levers, specula, and cautery
irons in bronze and iron, closely resembling instruments in use many
centuries later (the instrument set recovered from the so-called House of
the Surgeon at Pompeii is the best known example).

**Why you would never guess this.** The trap runs the other way: assuming
Roman surgery is primitive and needs wholesale replacement. It does not; it
needs three specific corrections layered onto an already-solid base.

**Prerequisites.** `sanitation_antisepsis`, `germ_theory`,
`anaesthesia_analgesia` for the procedures that benefit from it (mainly
longer or more invasive ones; amputation and couching do not strictly
require it given the two-minute constraint, though it improves the
experience and reduces shock).

**Roman-available inputs.** The existing instrument kit, described above,
needs no redesign. Fine linen or silk (imported, dear) or, more practically,
boiled and dried gut or flax fibre for ligature thread.

**Procedure, the three upgrades.** (1) **Ligature over cautery.** Roman
surgeons already know how to tie off a blood vessel with thread (Celsus
describes vessel ligation), but cautery, burning the vessel closed with a
hot iron, remains the dominant method for stopping bleeding, partly because
an untreated ligature thread left in a wound is itself a source of
infection under existing practice, making cautery's crude sterilising
side-effect seem like the safer choice. Once `sanitation_antisepsis` is in
place, boiled and wine- or spirit-soaked ligature thread removes that
downside, and ligature becomes strictly better: it preserves tissue that
cautery destroys and causes far less post-operative pain and scarring. (2)
**Better haemostasis before tying.** Grip the bleeding vessel with forceps
first, under direct sight, before tying it off, rather than tying blind
into a mass of tissue; this is a technique refinement, not a new tool,
since the forceps already exist in the Roman kit. (3) **Post-operative
care under the antisepsis regime**, not the "laudable pus" doctrine: clean
dressings changed rather than reused, the wound watched for fever as a
warning sign to intervene rather than a sign the humours are correctly
draining, and adequate food and fluids during recovery rather than the
restrictive diets some Galenic practice prescribed for the injured.

**How you know it worked.** Compare post-operative infection and death
rates between ligature-plus-antisepsis and cautery-plus-old-practice on
comparable wounds and amputations, the same controlled-comparison method
as under `germ_theory`.

**Failure modes.** A ligature tied with dirty thread or left in an
otherwise unclean wound reintroduces the exact infection risk the old
cautery practice was accidentally protecting against; the upgrade only
works as a package with sanitation, not on its own. Cautery habits are
deeply trained into existing surgeons and will reassert themselves under
time pressure unless practised deliberately.

**Cost & labour.** ESTIMATED. Low material cost, since it uses the
existing instrument kit; the cost is training time for surgeons already
skilled in cautery to retrain toward ligature, plus the ligature thread
itself (boiled linen or gut, negligible cost per patient).

**Danger.** Physical risk is the ordinary risk of surgery, reduced rather
than increased by these changes. Social risk is professional: you are
telling skilled, respected surgeons that part of their trained technique
should change, which is a smaller and easier claim than the wholesale
challenge to Galenic theory in `germ_theory`, and easier to win on visible
results alone.

**Confidence: HIGH.** Roman surgical competence and the existing instrument
kit are well attested (Celsus, archaeological finds). The specific upgrades
are textbook and their mechanism is well understood.

---

### pharmacology_first_tier - First-tier pharmacology: willow, foxglove, and opium, and why quinine is out of reach

**What it is / why you want it.** Three real medicines you can reach, each
with its own chemistry ladder, plus one important medicine you cannot
reach at all and should stop planning around.

**Willow bark to aspirin.** (1) **Willow bark decoction**: boil the bark of
willow (*salix*, *Salix* species, common across the Empire) in water and
drink the liquid; this alone gives real pain and fever relief and needs no
chemistry at all, only the plant and a pot, and willow's use for pain is
already attributed to earlier Greek medical tradition (attributed,
unverified for an exact Dioscorides citation, but consistent with his
general herbal coverage). (2) **Salicylic acid**: extract salicin from
concentrated willow bark (or meadowsweet, a related and in some
regions more concentrated source) by repeated boiling and evaporation,
then break it down and oxidise it to salicylic acid using the acid and
oxidation methods available once `analytical_chemistry` and
`organic_reagents_first_tier` are working; salicylic acid is a stronger
and more reliable pain and fever remedy than the raw bark decoction, but
it is harsh on the stomach in effective doses. (3) **Aspirin
(acetylsalicylic acid)**: react salicylic acid with a strong acetylating
agent, most practically acetic anhydride, itself a further downstream
product of the acetic acid chemistry in `organic_reagents_first_tier`; the
acetylated product is gentler on the stomach at an equally effective dose,
a genuine chemical improvement, not merely a different name for the same
substance. Flag this last step as the hardest of the three, since a
reliable acetic anhydride supply is itself several processing steps deep.

**Digitalis, and its narrow window.** Foxglove (no Roman name; Greek and
Roman pharmacology never identified it, so this is knowledge you bring, not
something Dioscorides catalogued, though the plant itself grows within
parts of the Empire's territory) contains cardiac glycosides that
genuinely strengthen and regulate a failing heartbeat, historically the
basis of a real and important treatment for dropsy (fluid retention from
heart failure). The danger is that the effective dose and the toxic dose
sit very close together, with only a narrow margin between them, a
well-established modern pharmacological fact; too little does nothing,
slightly too much causes nausea, visual disturbance (a yellow-green tinge
or haloes around lights is a specific, teachable warning sign), and
dangerous heart rhythm disturbance, and it accumulates in the body with
repeated dosing, so a dose that was safe yesterday can become toxic after
several days of the same dose. Use it only with `analytical_chemistry`'s
balance to weigh dried, powdered leaf precisely and consistently, start at
the smallest plausible dose, and watch the pulse for every dose given.

**Opium standardisation.** Raw opium latex varies substantially in potency
by source, harvest, and age, making any dose given by rough measure
unreliable. Fix this by dissolving a carefully weighed quantity of dried
opium into a fixed volume of distilled spirit (from `distillation_alcohol`)
to make a standard tincture, so that a given volume of the tincture always
delivers a known, repeatable dose, a real and important practical
improvement over guessing at a lump of raw resin.

**Why quinine is out of reach.** Quinine, the historical treatment for
malaria, comes from cinchona bark, a tree native only to the Andes of
South America. Per the hard rule on New World materials, cinchona is not
reachable from Rome in this period by any means; there is no substitute
Old World source. Malaria will remain a problem you cannot solve
pharmacologically for the foreseeable span of this programme. The only
lever available is prevention: draining or oiling standing water to
disrupt mosquito breeding and using fine netting where affordable, both
imperfect and neither a cure.

**How you know it worked.** Willow decoction and salicylic acid: fever and
pain measurably ease within an hour or two of a dose, judged by the
patient's own report and by touch (a fever-hot forehead cooling). Aspirin
compared against plain salicylic acid: same relief, less stomach
complaint, on a comparison across a cohort. Digitalis: pulse becomes
stronger and more regular in a patient with the dropsy/heart-failure
presentation (swollen legs, breathlessness lying flat) at a correctly
titrated dose; any of the warning signs above at any dose means stop
immediately and do not resume until the balance and the reasoning are
rechecked.

**Failure modes.** Aspirin synthesis without a properly dried, standardised
acetic anhydride gives a weak, unreliable, or contaminated product.
Digitalis dosing by rough handfuls of leaf rather than weighed, dried
powder is the single most dangerous mistake in this entry and will kill
patients; this is not a medicine to dose by eye. Opium tincture made from
old or damp opium gives a weaker-than-labelled dose, which then leads to a
dangerous overcorrection when a stronger batch is later used at the same
volume.

**Cost & labour.** ESTIMATED. Willow decoction is nearly free. Salicylic
acid and aspirin inherit the cost of the organic chemistry chain in
20_chemistry.md. Digitalis is cheap in material (the plant itself) but
expensive in the analytical-balance infrastructure required to dose it
safely, which is not optional here.

**Danger.** Digitalis is the standout physical danger in this entire
module outside of surgery itself: a small dosing error is fatal, and the
symptoms of early toxicity can be mistaken for the underlying illness
worsening, tempting a well-meaning attendant to increase the dose further,
which is exactly backwards. Treat any digitalis programme as requiring the
same discipline as a poison, because it is one.

**Confidence: HIGH** on willow, salicylic acid, and aspirin chemistry, all
well-established organic chemistry. **HIGH** on digitalis's pharmacology
and its narrow therapeutic window, a well-known modern medical fact.
**HIGH** on quinine's total unavailability, a direct consequence of the
New World materials rule.

---

### nutrition_deficiency - Deficiency diseases and their cheap fixes

**What it is / why you want it.** A short list of diseases caused not by
any germ but by a missing nutrient, several of which have essentially free
fixes once identified, and an honest assessment of which of them actually
threaten a Roman population and which mostly do not.

**Scurvy** (vitamin C deficiency; no vitamin concept available to Romans,
present it as "a wasting sickness of the gums and joints cured by fresh
green food or fresh fruit"). Rome's ordinary civilian diet, with regular
access to fresh vegetables and fruit including citron (*citrus medica*, a
real if somewhat costly Roman-era citrus already known), makes population-
wide scurvy unlikely in settled populations. It becomes a real risk
specifically on long sea voyages or in besieged garrisons cut off from
fresh food for extended periods, a well-attested pattern in later
seafaring history and plausibly applicable to Roman naval and siege
contexts, though I do not have a Roman-specific measured incidence to cite.
Fix: any regular ration of fresh vegetable or fruit; for stored provisions
on a long voyage, fermented cabbage keeps its vitamin content far longer
than fresh produce and travels well.

**Rickets** (vitamin D deficiency, from too little sunlight on skin; present
as "bowed and weakened bones in children kept from the sun"). Plausible in
dense Roman insula housing blocks with narrow streets and little direct
sunlight reaching lower floors, and there is some bioarchaeological
evidence suggestive of rickets in less sunny Roman provinces such as
Britain, but I am not confident of the scale, and flag this as attributed,
unverified for exact rates. Fix: regular sunlight exposure for children,
and fatty fish where available, both cheap.

**Beriberi** (thiamine/B1 deficiency, from a diet of over-refined grain).
This is historically associated with populations relying on heavily
polished rice as a near-total staple, and is unlikely to be a major Roman
problem given that the Roman staple is wheat and barley, generally stone-
milled in a way that retains more of the grain than later industrial
rice-polishing, though I am not fully certain no Roman population ever
over-refined its grain enough to matter. Flag as probably not a significant
Roman-era issue, with real uncertainty.

**Iodine deficiency and goitre** (a visible swelling of the neck from a
starved thyroid gland). This is genuinely and directly attested in
antiquity, particularly in inland and mountainous regions far from
seafood, such as parts of the Alps; ancient physicians describe and treat
visible neck swellings consistent with goitre. Fix: seafood, sea salt, or
seaweed for inland populations who otherwise never eat anything from the
sea, a cheap and reliable correction once the link is understood.

**How you know it worked.** Scurvy: bleeding, swollen gums and joint pain
resolve within days to weeks of fresh food being restored, a fast and
convincing result. Rickets: harder to observe quickly, since bone changes
in children develop and resolve over months; watch for reduced new cases
in a cohort given regular sun exposure rather than expecting fast reversal
in existing cases. Goitre: visible swelling recedes over weeks to months
once iodine-containing food is added regularly.

**Failure modes.** Assuming any general "poor diet" complaint is one of
these specific deficiencies without checking the actual presentation
(gum bleeding for scurvy, bowed legs for rickets, neck swelling for
goitre) leads to the wrong fix being applied. Assuming beriberi is a risk
in a wheat-and-barley economy and reworking milling practice to prevent it
is very likely wasted effort given the current uncertainty stated above.

**Cost & labour.** ESTIMATED, and low across the board: these are
observation-and-diet corrections, not manufactured treatments. The main
cost is in identifying which deficiency, if any, a given complaint
actually is.

**Danger.** Minimal directly. The main risk is misdiagnosis, treating a
germ-caused illness as a deficiency or vice versa, delaying the correct
response.

**Confidence: MEDIUM** on scurvy's general risk pattern and fix (well
understood mechanism, uncertain Roman-specific incidence). **LOW** on
rickets' Roman-era scale specifically, flagged. **LOW**, leaning toward
"probably not applicable," on beriberi in a wheat-and-barley economy.
**HIGH** on iodine deficiency and goitre being real and already observed
in antiquity, and on the fix.

---

### microscopy_biology - Microscopy and the beginnings of biology

**What it is / why you want it.** What the single-bead microscope shows
you the first time you use it, and the research programme it opens up,
independent of the specific germ theory demonstration above.

**Why you would never guess this.** You already know these things exist;
the non-obvious part for a Roman collaborator is that a small glass bead,
an object indistinguishable from jewellery, resolves a genuinely new tier
of the world, and that this was, historically, discovered by one
determined amateur with exactly this equipment and no institutional
backing at all (Antonie van Leeuwenhoek, 17th century, working alone with
hand-ground single-lens instruments; attributed, well documented
historically though centuries after your setting, cited here only as proof
the equipment level is sufficient, not as a Roman event).

**Prerequisites.** `glass_bead_microscope` (30_glass_optics.md#glass_bead_microscope).

**Roman-available inputs.** Pond and ditch water, blood (from any wound or
bloodletting, already a routine Galenic practice you can piggyback on for
samples), semen, thin slices of cork or green plant stem, all freely
available.

**Procedure, what to look at first, in order of ease.** (1) **Cork or
plant stem**, sliced as thin as possible with a sharp blade: shows a
regular honeycomb of small walled compartments, the plant cell wall
structure, the easiest and least ambiguous first observation since the
subject is dead and motionless. (2) **Blood**, a fresh drop thinly smeared
on a flat mount: shows countless small disc-shaped bodies, red blood
cells, filling the field. (3) **Pond or ditch water**, especially water
that has stood for a few days: shows moving bodies of varied shape,
protozoa, some changing shape as they move, at magnifications a well-made
bead comfortably reaches. (4) **Semen**, a fresh sample thinly mounted:
shows large numbers of small bodies with active whip-like tails, motile in
a way nothing else on this list is, a striking and unambiguous
demonstration of motion under the lens. (5) **Bacteria, at the limit**: in
matter left to putrefy, or in dental scrapings, faint moving rods and
threads are visible at the edge of what a single small-radius bead can
resolve; this is the hardest of the five to see clearly and the one most
likely to need the best bead you have and a patient, practised eye.

**How you know it worked.** Each of the five categories above has a
distinct, describable appearance; if you or a trained observer can
reliably find and describe the same structures on repeated independent
looks at fresh samples, the instrument and the technique are both working.

**The research programme that follows.** Once observation is reliable,
move to comparison: healthy versus diseased tissue or fluid samples side
by side, looking for a consistent difference; systematic description and
rough classification of the different moving bodies seen in different
water sources by size, shape, and manner of movement; and, eventually,
transfer experiments, deliberately introducing material from a sick sample
into a healthy subject or culture and watching whether the same
appearance and the same illness follow, which is the direct experimental
bridge to `germ_theory` above. Longer term, this programme is what
motivates building toward `microscope_compound`
(30_glass_optics.md#microscope_compound), a much later, tier 3 item that
resolves finer structure than any single bead ever will.

**Failure modes.** A poorly ground or dirty bead gives a blurred, useless
image that can be mistaken for "there is nothing to see," discouraging
further work; insist on a well-polished bead and a clean, thin sample
before concluding an observation has failed. Overinterpreting shapes seen
at the resolution limit (claiming to see fine internal structure in
bacteria-sized bodies that a simple bead genuinely cannot resolve) produces
false claims that damage credibility; be conservative about what you claim
to have actually seen.

**Cost & labour.** ESTIMATED, low: the microscope itself is built once
under `glass_bead_microscope`'s own costing in 30_glass_optics.md; ongoing
cost here is only observer time.

**Danger.** Minimal. The main risk is social overreach, claiming more
certainty from a hazy image than the instrument can support, which invites
easy mockery from a hostile Galenist audience.

**Confidence: HIGH.** Simple single-lens microscopy at this level is
extremely well documented historically (Leeuwenhoek's real, surviving
letters and specimens), and every observation listed above is a genuine,
repeatable result at the magnifications such an instrument achieves.

---

### antibiotics_note - Antibiotics: why they are not the priority

**What it is / why you want it (or rather, why you mostly do not, yet).**
A blunt statement of where penicillin and the sulfonamides sit on the
difficulty scale, so you do not spend a decade chasing them while cheaper,
earlier wins go unbuilt.

**Penicillin.** Needs, in rough historical order: a mould that happens to
produce a useful yield of the compound (the original discovery strain was
a poor producer), a deliberate strain-hunting programme to find a
substantially higher-yield strain (historically found on a mouldy melon in
a market survey during the Second World War), further yield improvement by
irradiation-induced mutation and selection, large aerated deep-tank
fermentation vessels rather than the shallow surface cultures the first
researchers used, a nutrient-rich growth medium at industrial scale, and a
chromatographic or solvent-extraction purification process to get a usable,
stable, dosable product out of a fermentation broth. Every one of those
steps needs infrastructure, precision, and microbiological understanding
far beyond what this module or the chemistry and glass modules alone
provide by the time the plagues arrive; this is realistically a very late
item in the overall technology programme, well beyond the horizon of
either plague described in this module.

**Sulfonamides.** Come out of the coal-tar synthetic dye industry
(historically, the first, Prontosil, was developed from azo dye research
in the 1930s), which means they need a mature `destructive_distillation`
of coal for tar, isolation of aniline-family compounds from that tar, and
diazotization and azo-coupling chemistry built on top of that. This is a
real, substantial prerequisite chain, later than the willow-bark and
opium chemistry in `pharmacology_first_tier` but considerably earlier than
penicillin's fermentation-and-purification demands.

**The bottom line.** Sanitation, clean water, and isolation (the first
three entries in this module) deliver most of the achievable reduction in
epidemic and wound-infection mortality for a tiny fraction of the effort
either antibiotic class requires; this comparison is a strategic
characterisation, not a measured ratio, and is flagged as such, but the
direction of the comparison is not in doubt. Do not delay
`sanitation_antisepsis` or `quarantine_publichealth` to chase antibiotics.
Treat sulfonamides as a reasonable mid-programme goal once the coal-tar
chemistry chain exists for other reasons, and treat penicillin as a
long-term aspiration, not a plague-preparedness item.

**Cost & labour.** ESTIMATED and, for penicillin specifically, treated here
as out of scope for cost estimation, since the prerequisite chain (deep-tank
fermentation, strain selection, chromatography) is itself not yet specified
anywhere in this document.

**Danger.** None directly from the decision not to prioritise this; the
danger is entirely in the opportunity cost of chasing it too early, at the
expense of the cheap interventions above.

**Confidence: HIGH.** The historical difficulty and sequencing of
penicillin versus sulfonamide development is well documented, and the
comparison to sanitation's cost-effectiveness, while not a precise ratio,
is not a controversial claim in the history of public health.

---

### obstetrics_maternal - Obstetric handwashing and maternal mortality (building on Soranus of Ephesus's existing gynaecological tradition)

**What it is / why you want it.** A single, nearly free habit change,
already implied by `germ_theory` above but important enough to state on
its own: handwashing and clean hands specifically before any internal
examination or delivery, which historically produced a dramatic and
well-documented fall in deaths from childbed fever.

**Why you would never guess this.** The historical discovery (Ignaz
Semmelweis, Vienna, 1847) came from a specific and slightly grim
observation: doctors and students who went directly from performing
autopsies to examining labouring women had far higher maternal death rates
on their ward than midwives who never touched a cadaver. The mechanism,
invisible material carried on unwashed hands, is exactly the mechanism
`germ_theory` above already establishes; this entry exists to make sure
the specific application to childbirth is not missed, since maternal death
from childbed fever was, historically, one of the largest preventable
causes of death for young women.

**Prerequisites.** `germ_theory`, `sanitation_antisepsis`.

**Roman-available inputs.** Water, wine, and eventually distilled spirit,
exactly as in `sanitation_antisepsis`; no new material.

**Procedure.** Anyone about to examine or assist a labouring woman
internally washes their hands thoroughly in hot water, then in wine or
spirit, immediately beforehand, with particular attention if they have
recently handled a wound, a corpse, or another sick patient; instruments
used in delivery are cleaned the same way as surgical instruments under
`sanitation_antisepsis`.

**How you know it worked.** Compare maternal fever and death rates between
attendants who follow this practice and those who do not, across a large
enough number of births to see a real difference, the same controlled-
comparison method used throughout this module.

**On the scale of the benefit, honestly.** The historically documented
effect in Semmelweis's own ward was large: commonly cited accounts describe
his First Clinic's maternal mortality falling from a range around 18 in
100 births down to roughly 1 or 2 in 100 after the handwashing policy was
enforced, MEASURED from that specific 19th century hospital record, but
not a Roman number and not guaranteed to transfer exactly, since his high
starting figure was driven specifically by a teaching hospital's frequent
autopsy-to-delivery traffic, a pattern less exactly replicated in Roman
domestic midwifery, which did not involve systematic student dissection in
the same way. Expect a real and probably large reduction in Roman maternal
mortality from consistent handwashing, since the underlying mechanism
(hand-to-uterus transmission of infectious material) is the same
regardless of setting, but treat the specific percentage as ESTIMATED for
your context, not as a number you can promise a patron in advance.

**Failure modes.** Washing hands once at the start of a long attending
shift, rather than immediately before each new patient, misses the point;
the risk is in the specific transfer event, not a general state of
cleanliness for the day. Midwives who already avoid handling the dead
(a role often separately assigned in Roman households) may see little
benefit from this specific change and need a different comparison
(handwashing between different labouring patients, or after handling
soiled linens) to demonstrate value to them.

**Cost & labour.** ESTIMATED, effectively free: water, wine or spirit, and
the habit itself.

**Danger.** Minimal physically. Socially, implying that an experienced,
respected midwife's existing practice contributed to deaths is delicate;
present it as an addition, not an accusation, and let the comparison data
make the case.

**Confidence: HIGH** on the mechanism and on the qualitative historical
result (the Semmelweis case is extremely well documented). **MEDIUM** on
the exact historical percentages, which vary somewhat between sources and
are in any case a 19th-century Viennese hospital figure, not a Roman one.

---

### veterinary_and_agriculture_link - Animal disease, draught power, and food supply

**What it is / why you want it.** The same germ theory, sanitation, and
isolation principles applied to livestock, because draught power (oxen,
mules, horses) and a large share of the food supply (dairy, meat) both
depend directly on herd health, and an epizootic can cripple your
agriculture and transport just as thoroughly as a human epidemic cripples
your population.

**Why you would never guess this.** It is easy to treat this module as
entirely about humans and treat animal disease as someone else's problem;
in an economy where nearly all cartage, ploughing, and milling power comes
from animals, a herd-wide disease outbreak is a transport and food crisis
of the same character as a human plague, just less visible to a physician
focused only on people.

**Prerequisites.** `germ_theory`, `sanitation_antisepsis`; builds directly
on existing Roman veterinary and husbandry knowledge (Columella,
*De Re Rustica*, already covers animal care and disease at length, a real
and citable Roman agricultural authority).

**Roman-available inputs.** Existing Roman livestock husbandry practice as
described by Columella; the same clean water, isolation, and wound care
principles as the human-focused entries above, simply applied to a stable
or byre instead of a sickroom.

**Procedure.** (1) Do not share water troughs or feed between visibly sick
and healthy animals; isolate a sick animal in a separate space. (2) Clean
wounds on working animals (harness sores, plough injuries) the same way as
human wounds: boiled or spirit-washed, not left to fester as a matter of
course. (3) Maintain standing surveillance of dairy herds for pustular
udder lesions, which serves double duty: protecting the herd and food
supply directly, and functioning as the ongoing search described under
`vaccination_cowpox` for a genuine cowpox source. (4) Keep separate tools
and attendants, where practical, between sick and healthy animal groups, to
avoid carrying infection on hands or equipment the way a human attendant
would.

**How you know it worked.** Fewer working animals lost or lamed to
untreated wound infection over a season; fewer secondary cases in a herd
after isolating a first sick animal, compared to a herd where no isolation
was practised.

**Failure modes.** Treating animal husbandry as entirely separate from the
human-health programme above, so that the same attendants move freely
between sick animals and human patients (or vice versa) without the
handwashing discipline established elsewhere in this module, reintroduces
exactly the transmission risk the rest of the module works to remove.

**Cost & labour.** ESTIMATED, low: mostly labourer time for basic
separation and cleaning, well within the same wage-rate basis used
throughout (labourer 0.075 den/hr).

**Danger.** Minimal directly. The strategic danger of ignoring this entry
is indirect but real: losing draught animals to a preventable epizootic at
the same moment a human epidemic is straining your labour force is a
compounding, not a separate, crisis.

**Confidence: HIGH** on the mechanism (the same germ theory and sanitation
principles apply to any mammal) and on Columella's existence as a citable
source; **MEDIUM** on how readily Roman herdsmen will accept isolation
practices that reduce a sick animal's economic use in the short term
without a demonstrated track record first.

---

## The plague timetable

**165-180 AD, the Antonine Plague.** From your arrival in 100 AD you have
roughly sixty-five years. This module's own dependency chain (per the
tech tree data in rome/data/tech_tree.json) runs `school_founded`
(a stated four-year floor in that file) before `germ_theory` (a further
two years, itself gated on `glass_bead_microscope`) before
`plague_preparedness` (a further four years on top of that). Summed
naively that is a floor of roughly a decade of sequential calendar time,
DERIVED from the tech tree's own stated `yrs` fields, not counting the
time needed to found the school in the first place or to train the people
who will staff any of it. The practical implication is not "you have
sixty-five years, relax," it is "start the whole chain, school founding
included, inside your first decade in-country, or you will be racing an
epidemic with an unfinished programme." Use the remaining decades, once
the core chain is running, for two things: first, field-testing
variolation against whatever pox or measles-like disease cases actually
appear in the Empire in the interim, since you will not know for certain
whether the Antonine Plague is smallpox or measles (see `variolation`
above) until you can observe its actual presentation, ideally by comparison
with earlier, smaller outbreaks; second, and more important given that
uncertainty, building out `quarantine_publichealth` and
`sanitation_antisepsis` as broadly as your influence reaches, since these
work regardless of which disease arrives. Do not wait for certainty about
the pathogen before building the pathogen-agnostic layer.

**249-262 AD, the Plague of Cyprian.** By this point you have had, from
165 AD, roughly eighty years to institutionalise whatever survived the
first plague, and you personally will almost certainly not be alive to
manage it directly if you arrived as an adult in 100 AD; this must be a
transmitted institution by 249 AD, not personal knowledge, which is
precisely why `school_founded` and durable written tradition matter as
much as any single medical technique. The identity of this second plague
is, if anything, even less certain than the first; ancient descriptions
are fragmentary and modern historians offer several candidate diseases
without consensus, and I do not have a confident attribution to offer here
beyond flagging the uncertainty itself. Spend the eighty-year gap widening
the reach of the first plague's institutions rather than inventing new
ones: train more physicians and magistrates in the existing protocol,
embed the practice in already-trusted institutions (the legions, temples
associated with healing such as those of Asclepius/Aesculapius, and
professional collegia) so it survives leadership changes, and account
explicitly for the real bottleneck that Rome has no printing and no paper
in the modern sense, so every copy of your protocols is a scribe's labour
on papyrus or parchment; budget for that copying effort as seriously as
for any material good, since a protocol that exists in one copy in one
city is not actually institutionalised.

---

## How not to be executed for this

Practising medicine in Rome carries real, existing legal and social
advantages: physicians already occupy a recognised, often Greek or
freedman social slot, and later imperial-era law recognises certain
immunities from civic burdens for practising physicians, alongside
teachers and philosophers (a pattern reflected in juristic writing of the
period, attributed, unverified for an exact citation, but broadly
consistent with the standard picture of the profession's legal standing).
That status is an asset. It is also exactly what makes reliably curing
people where established physicians fail dangerous, because unusual
success where others fail is, in Rome, a recognised route to an accusation
of poisoning or sorcery (*veneficium*), not simply professional envy.
Specific tactics:

1. **Operate under a powerful patron before you need one, not after.** A
foreign physician with no patron performing strange, effective treatments
reads as a threat; the same person, introduced as a client physician of a
senator, a governor, or eventually someone closer to the emperor, reads as
a known and vouched-for professional. Secure the patronage relationship
before your first controversial demonstration, not in response to trouble.

2. **Speak in existing vocabulary even while changing the content.**
Describe the invisible agents of `germ_theory` using Varro's own phrase,
"seeds of disease" (*semina morbi*), rather than presenting the idea as a
total break from everything Roman medicine already believes. You are
completing an existing, respectable Roman intellectual thread, not
importing foreign magic.

3. **Never claim, or appear to claim, perfect success.** Let some patients
die visibly and openly, and do not obscure it; a physician who is seen to
lose patients is a physician, a physician who never loses one is,
uncomfortably fast, a suspected poisoner or sorcerer working by
unnatural means, especially if a rival's patient or a political enemy's
family member happens to die under your care while your own patients
thrive. Keep your failure rate visible.

4. **Control the venue for anything that looks uncanny.** A moving speck
under a bead microscope, a patient rendered insensible by ether, a person
deliberately given a mild dose of a lethal disease, all read to an
unprimed crowd as marvels indistinguishable from *maleficium* (harmful
magic). Perform first demonstrations privately, for witnesses you have
already briefed and who already trust you, and only go public once you
have a track record those witnesses can vouch for.

5. **Get licensed through existing structures, and stay inside them.** A
recognised collegium membership gives you an institutional face and a body
that can vouch for you; operating entirely outside any recognised guild or
institutional structure leaves you with no one to appeal to if accused.

6. **De-risk dangerous demonstrations on low-political-consequence
volunteers first.** This is exactly how the historical 18th-century
inoculation programmes actually de-risked variolation, testing first on
condemned prisoners with royal permission before extending it to a royal
family (attributed, historically the actual sequence in the Lady Mary
Wortley Montagu and Caroline of Ansbach-era trials, though this is an
18th-century English precedent, not a Roman one, cited here only as a
sound de-risking strategy). Apply the same logic in Rome: build your track
record on informed, consenting volunteers of modest standing before you
ever inoculate, operate on, or anaesthetise anyone politically important. A
single dramatic public failure involving someone well connected is the
single most dangerous event described anywhere in this module.

---

## Sources and confidence

**High confidence, well attested primary sources you can actually build
on.** Celsus, *De Medicina*, for Roman surgical technique, instruments,
and specific procedures including cataract couching and vessel ligation.
Dioscorides, for the pharmacology of willow, opium poppy, mandrake, and
henbane, all genuine entries in his surviving materia medica. Frontinus,
*De Aquaeductu*, for the Roman water supply described under
`sanitation_antisepsis`. Columella, *De Re Rustica*, for existing Roman
animal husbandry underlying `veterinary_and_agriculture_link`. Soranus of
Ephesus, whose gynaecological writing is a genuine, roughly contemporary
(Trajanic/Hadrianic-era) source you can build `obstetrics_maternal` on
directly, though I have not cited specific passages from him here.
Galen's dominance of the medical profession, and the general shape of
humoral theory as the obstacle `germ_theory` must overcome, is well
attested, though specific claims about what Galen wrote about the
Antonine Plague itself are noted below as less certain.

**Flagged, lower confidence, or explicitly attributed-and-unverified
items.** Varro's exact wording on invisible disease-causing creatures in
marshes (*De Re Rustica* 1.12.2), the general concept is a standard
citation in histories of epidemiology, the precise Latin and its exact
implications are attributed, unverified here. The precise identity of both
the Antonine Plague and the Plague of Cyprian: genuinely disputed among
modern historians, not a gap in this module's research, flagged
explicitly wherever it matters for planning. The specific mortality
percentages given for variolation versus natural smallpox, and for
Semmelweis's ward before and after handwashing: real historical figures
from documented programmes, but from later centuries and different
societies, transposed here as the best available evidence rather than as
Roman-specific measurements, and flagged as such at each use. The exact
legal citation for physicians' civic immunities: the general fact is
well established in the standard picture of the Roman medical profession's
status, the precise juristic passage is attributed, unverified. Roman-era
incidence of rickets and beriberi: flagged LOW and MEDIUM respectively
under `nutrition_deficiency`, genuine uncertainty, not false precision.
Wherever this module gives a cost, labour, or calendar figure not drawn
directly from rome/data/tech_tree.json, it is marked ESTIMATED against the
wage-rate basis in rome/data/prices.json and should be read as a shape,
not a guarantee.
