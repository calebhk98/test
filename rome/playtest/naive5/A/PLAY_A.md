# Playtest A — naive5

Player: Claude (naive playtester). Rules: only the running program tells me anything.
Target setup: Han China, 100 AD, fog of war ON, "poor scholar" purse, founder does NOT age.

## Log

### 0. Before starting
Expectation: an interactive setup wizard asking era/civ/difficulty-ish questions, then a
command prompt. I expect a session file to be printed that I can resume with
`play --session <file>`. I expect commands like `help`, `status`, `look`.

### 1. Setup (done)
Answers: 1 (Later Han, 100 AD) / y (fog of war) / poor_scholar / n (no ageing).
Setup went exactly as I expected: a menu of five worlds, then three toggles.
Nice touch: the world blurb told me GLASS is the missing thing in Han China, and that
civil war arrives in ~80 years. I read that as: (a) optics will be expensive here,
(b) there is a clock ticking on the "easy bureaucracy" advantage.

Session file: han_china_100ad.json. Resume with
`python3 rome/sim/simulator.py play --session han_china_100ad.json`.

Prompt line format: `[100 AD | 400 den | you:2000 hr | sch 0 art 0 | rep 5] >`
Guess: year | money | my own labour-hours per year | scholars? artisans? | reputation.

Suggested first commands: state, available, why <name>, step, help, quit.

Expectation before typing anything: `available` will show a handful of cheap things
(paper? glass? a school?), each with an hour and money cost. With 400 den and 2000 hr
I expect my own hours to be the real currency early, and I expect I'll need income
before I can build anything big. My plan: find a money-making project first, then
buy scholars/artisans, then push a tech line.

### 2. Reading the game (100 AD, no time spent yet)
`help` told me the actual goal: **build a point-contact transistor before the horizon
at 600 AD**. That reframes everything — this is a 500-year tech-tree race, not a
lifetime sim (which is why "founder doesn't age" is the default).

`state full:true` gives: 400 den, net +3.5/yr, 2000 founder-hours, rep 5, scandal 0,
eminence 0, "135 technologies granted for free" (the Han starting stock), and an
AHEAD block naming the Yellow Turbans (184-205) and Three Kingdoms (220-280) with
"5 technologies at risk, 1.6 lost per sacking".

Surprise #1: I did not expect *losing* technologies to be a mechanic. "hedged by
nothing yet" is clearly an invitation to find a hedge. I don't know what hedges it.
I'll go looking later; nothing in `available` obviously says "archive".

Surprise #2: eminence. "dangerous above 26 ... 0% chance of ruin this year". So
success itself is a threat. Two opposed pressures (need reputation to build, but
visibility kills you) is the most interesting thing I've seen so far.

`available` = 89 startable, grouped by subject. Good affordance: the summary tells me
CHEAPEST SIX and "MOST RESTS ON THESE" so I'm not reading 89 rows.

Expectations from the columns COST/HOURS/YEARS/RISK/EARNS/UPKEEP/RESTS:
- EARNS/YR means these projects are businesses, not just tech unlocks. Payback maths:
    prn_sizing_surface   20.7 den -> +100/yr, -20 upkeep = net +80/yr  (payback ~0.3 yr)
    tex_mordanting      114.1 den -> +150/yr, -15        = net +135/yr (payback ~0.85 yr)
    tex_indigo          165.7 den -> +300/yr, -40        = net +260/yr (payback ~0.64 yr)
    tex_horizontal_loom 201.9 den -> +400/yr, -30        = net +370/yr (payback ~0.55 yr)
  If those numbers are real, the opening is trivially solved: buy the money printers
  first, then everything else is affordable. I EXPECT that to be too good to be true
  and for something (market saturation? scandal? eminence?) to punish it.
- identity_cover (1,431 den, 500 hr, upkeep 200/yr) says "HOW MUCH RESTS ON THIS:
  almost everything" and "reduces all future suspicion". I read that as the answer to
  the eminence problem, and probably a hard prerequisite gate. Too expensive now.
- units_standards (402 den, 300 hr) also "almost everything" rests on it. It says
  "Do this before writing any other recipe down" — that reads like the game telling me
  it gates the whole corpus/legacy line.

PLAN for year 100: start the cheap high-yield earners (sizing, mordanting, indigo),
keep ~100 den buffer, step 1 year, and see (a) whether costs are charged up front or
spread, (b) whether revenue is real, (c) what a year's living costs are.

### 3. Year 100 -> 101: the first real surprise
I started sizing/mordanting/indigo and stepped one year. All three completed at once
(my 2000 founder-hours dwarfed the 150 they needed).

EXPECTED: completing them would start the money flowing.
ACTUALLY: "You know how; nothing is earning yet - 'open prn_sizing_surface' to run it."
Knowing != running. There is a separate `ventures` / `open` / `mothball` layer, and
opening costs about one year's upkeep as capital.

This is a good distinction and I like it, BUT: **neither `open` nor `ventures` appears
in `help commands`.** I only found them because the completion event happened to name
them. `help commands` lists mothball/restore but not their counterpart `open`. That is
a real documentation gap for a fog-of-war game where the command list is my map.

After opening all three:
  Revenue 665.9/yr, upkeep 75, living and appearances 250.7, net +340.2/yr.
SURPRISE: the ledger credits revenue to things I never built —
`med_cataract_couching 185.1` and `med_trepanation 74`. Those must be among the 135
"granted" Han technologies. So some of my income is just "the world already had this
and you can practise it". I never asked for it and nothing told me it was happening;
I inferred it from the ledger. Also nominal EARNS/YR is not what you get: indigo says
300/yr and pays 222.1. Something scales it and I cannot see what.

`risk` is excellent and answered the question `state` raised. Hedges are named
explicitly: "walls, firearms, powerful friends, and copies of your work kept somewhere
else" for the rebellion; "land and power of your own, and not depending on trade that
a war can cut" for the Three Kingdoms, and it even points at a startable item
(civ_surveying_groma) that helps. That is the clearest signposting in the game so far.
Oddity: it prints "sack chance: you take 100% of it" and then "sack chance after what
you have built: 20%" with nothing built. I read 20% as the base rate and "100% of it"
as my exposure share, but the two lines look contradictory on first read.

`policy` shows ten automation switches, all off except auto_mothball. Leaving them off
for now — I want to see the manual mechanics before I let the engine drive.

`labour`: hireable here = artisan, carpenter, engraver, furnaceman, glassblower,
labourer, mason, master, merchant, millwright, miner, plumber, potter, sailor,
scholar, scribe, smith. MUST BE TAUGHT = chemist, electrician, engineer, machinist,
optician. That is a clean, legible statement of what this civilisation is missing, and
it tells me the transistor road will require training electricians/chemists out of my
own hours. Noted as the long pole.

PLAN now: chm_phosphorus_extraction is 1,668 den for a nominal 2,000/yr — payback
under a year, 20% failure risk. Credit limit is 2,280 at 12%. I am going to borrow to
build it, plus civ_surveying_groma (cheap, hedges the Three Kingdoms) and
opt_manometer. EXPECT: I end the year deep in arrears but with income around
1,500-2,000/yr, and I expect a 1-in-5 chance the phosphorus burns the money for
nothing.

### 4. Years 101-106: the debt trap, and the economy solved
Started phosphorus + groma + manometer on credit (1,986 den). All three succeeded
(the 20% failure roll on phosphorus did not bite).

**The sharpest lesson of the game so far, and it stung:** you may borrow to BUILD a
thing, but you may NOT borrow to OPEN it.
    REFUSED: opening it costs 250 denarii in stock and premises and you have -1,596
So I financed the money-printer and then could not switch it on. That asymmetry is
never stated anywhere I looked - `help money` says "You may spend past what you have",
and nothing says opening is cash-only. I expected the opposite (opening is trivially
cheap relative to building, so surely it is covered by the same credit). Whether or
not it is intentional, it is the single most punishing undocumented rule I hit.

Escape hatch: `work scholar 2000`. 2,000 founder-hours of ordinary scholar's work pays
~352 den/yr. Four years of day-labouring (102-105) plus the existing 530/yr net dug me
out. Realistic and rather good: the modern genius spends four years teaching for a fee
because he over-borrowed. But note it is a strictly worse use of the founder's time,
so the punishment for the debt trap is four wasted years.

Small thing I only noticed in the numbers: reputation decays (15.3 -> 13.7 over four
idle years) and so does scandal (2.1 -> 1.4). Nothing announces this; I inferred it.
I think it means visible activity is what sustains standing.

106 AD after opening everything: revenue 3,305/yr, upkeep 232, living 416.6,
**net +2,657/yr**. Phosphorus alone pays 2,264. The economy is now solved, in six
years, from a 400-den purse. That feels far too easy for a game whose premise is
"building it is not free" - one tier-2 chemistry venture out-earns everything else
combined by 7x, and its only gate was a heat capability I was granted for free.
If the intent is that money should stay tight, this is a hole.

Also noticed: "living and appearances" rose 250 -> 416 as reputation rose. So standing
has a running cost. That is a nice touch and I only found it by watching the ledger.

NEXT PLAN: money is no longer the constraint, so the constraints must be (a) founder
hours, (b) staff I have to train, (c) eminence/scandal, (d) the 184 AD rebellion.
I will now buy the two "ALL rests on this" foundations (identity_cover 1,431 for
suspicion, units_standards 402), then look for the road to electricity.
EXPECT: identity_cover reduces eminence-risk; units_standards unlocks a large batch of
new items (it says every recipe depends on it).

### 5. 107-109: units_standards is the real gate
Hired 3 smiths + 3 artisans (~875 den/yr), trained 2 chemists (900 of my hours, 394
den, 2 years), built units_standards and identity_cover.

EXPECTED: units_standards would unlock "a large batch". ACTUALLY it went from
**84 startable to 313 startable**. That is the single biggest state change in the game
and my expectation was right for once. It also silently granted me a free follow-on
("COMPLETED 108: Reproducible length standard") which I never started - pleasant, but
it appeared with no explanation of where it came from.

Confusing display: `train chemist 2` reported "your hours left this year: 1,100", but
the prompt and `state` both still said `you:2000 hr` afterwards. I could not tell
whether training had actually eaten this year's hours or next year's. The hour budget
is the scarcest resource in the game and I cannot reliably read it.

Nice writing: `state` explains fractional staff on its own ("5.6 people ... these are
continuous full-time-equivalents ... attrition about 3.5%/yr"). I had been about to
ask why I employed 2.8 smiths.

`labour` now lists chemist as HIREABLE - because I taught it. So training a trade
creates a labour market, it does not just give me two people. That is a big deal and
nothing said it would happen; I noticed it by diffing the list. Remaining MUST BE
TAUGHT: electrician, engineer, machinist, optician.

New "MOST RESTS ON THESE": patron_local (1,087, "Halves incoming suspicion"),
water_power_scale (5,155, earns 2,200), arithmetic_positional (360),
scientific_method (157.5, "Multiplier on every research node thereafter"),
prc_treadle_lathe_flywheel (181.6).
And in HEARD OF: **corpus_written, missing prerequisite scientific_method**. That is
almost certainly the "copies of your work kept somewhere else" hedge that `risk` told
me about. So the chain risk -> hedge -> corpus_written -> scientific_method -> ... ->
identity_cover is discoverable purely from in-game text. Good.

Started all four: scientific_method, patron_local, arithmetic_positional,
prc_treadle_lathe_flywheel (1,786 den, 1,280 of my 2,000 hours).
EXPECT: 2 years (scientific_method has a 2-year calendar floor), 20% and 15% failure
risks respectively, and a further large unlock afterwards. I especially expect
scientific_method to be the thing that opens "mathematics and method" and the corpus.

### 6. 111-117: the corpus, water power, and hours as the real currency
Opened scientific_method, patron_local, arithmetic_positional, treadle lathe.
`scientific_method` printed something new: "EVENT 110: ... changes the society:
w_magic_fear, w_novelty". So projects move society-level values. Nothing tells me what
w_magic_fear or w_novelty are or what direction they moved, and I found no command to
inspect them. That is the one place where the game clearly has a system I can feel but
cannot see at all - and unlike the tech tree, the fog is not supposed to be the point.

Found the hedge: **corpus_written** - "Write the corpus: everything you know, in plain
quantitative Greek and Latin". 1,386 den but **6,000 founder-hours over 10 years**.
That is the honest price of durability and I like it a lot: the thing that saves your
work from the Yellow Turbans costs three full years of your only irreplaceable
resource.

Started corpus + water_power_scale together. Two mechanics I had to learn by watching:
- **Founder hours split across running projects, and I cannot set priorities.** Year
  one, corpus took all 2,000 (33% of 6,000) and water power got 0%. Year two they
  split 1,560/270. There is no `prioritise` command I could find. With one 6,000-hour
  job running, everything else crawls, and I have no lever.
- **Money is charged on the calendar, not on progress.** Water power was billed
  2,578 in a year where it received 0% of my hours. So a 2-year project bills half up
  front regardless. That is what pushed me to -2,557 den.

And the debt trap bit AGAIN, exactly as before: water power completed in 114 but I
could not `open` it (900 den) until 117 because I was in arrears. Three years of a
finished 2,200/yr mill sitting idle. Second time I have been caught by the same
undocumented rule; a one-line warning at `start` time ("you will also need N den in
hand to open this") would fix it entirely.

117 AD: revenue 6,097/yr, upkeep 1,792, net ~+2,500/yr, 12 concerns running.

Where the goal actually is: `dynamo` shows in HEARD-OF as "needs 8 other things you
have not heard of yet". The visible spine is
  workshop_first -> case_hardening -> precision_three_plate -> balance_analytical
  -> opt_standards_laboratory, plus thermometer
i.e. **precision metrology, not electricity**, is the road to a transistor. I think
that is the correct and interesting lesson and the fog delivers it well: I did not
guess it, I was shown it by watching prerequisites resolve.

NEXT: workshop_first (5,214 den, "ALL rests on this", 900/yr upkeep) is clearly the
next gate. I need cash in hand this time - lesson learned, I will bank first.
Also training engineers (450 of my hours each) since ag2_gravity_irrigation and
presumably much else needs them.
EXPECT: workshop_first opens the precision branch and a fresh wave of ~100 items.

### 7. 117-122: workshop, corpus, atoms
Banked cash first this time (lesson learned) and ran workshop_first (5,214),
algebra_symbolic, atomic_theory, cap_power_water. All completed; corpus_written
finished in 120 too (10 calendar years exactly, as advertised).

`state` now reads "6 technologies at risk if a hazard lands, **hedged by
corpus_written**". Confirmed: the risk -> hedge loop closes and the game tells you.
Very satisfying, and the best-designed loop I have found.

`risk` also improved on its own: Three Kingdoms went from "output factor: you take
100% of it" to "**you take 80% of it (softened by power that does not come by ship)**"
purely because I had built water power. Nothing prompted me to do that for that reason
- I built the mill for money - and the game noticed and explained why. That is
excellent. It now also names concrete startable mitigations (mil_artillery_piece,
nitre_beds, charcoal_industrial for the rebellion; civ_road_paved, crop_rotation for
the fragmentation) and even names two locked ones, corpus_dispersed and school_founded,
with their missing prerequisites.

421 startable now. The precision branch opened as expected: case_hardening (838 den,
earns 1,500, "ALL rests on this") and refractory_fireclay (1,143, "ALL").

**The thing I am now most worried about is upkeep creep.** Revenue 6,941/yr but
upkeep 3,542 + wages 1,682 + living 672 leaves net only +1,045. Every foundation I
open (corpus 600/yr, workshop 900/yr, patron 200/yr, identity 200/yr) is a permanent
0-revenue tax. That is a real and interesting squeeze - "the institutions that let you
work cost more than the work" - but it means the mid-game tempo is: build one earner,
spend it all on the upkeep of the last three foundations. I cannot tell yet whether
that is intended pressure or an accounting problem.

Two things I wanted and could not do:
1. **Prioritise founder hours between running projects.** No command for it.
2. **See society `values`.** Events say "changes the society: w_magic_fear, w_novelty,
   literacy_elite" and `risk` twice says "applied gradually below as `values`", which
   reads like an instruction to type `values` - but that is not a command and `help`
   does not list it. That is a dangling reference in the text.

### 8. 122-127: precision, lenses, and a staffing cap
- `values` really is not a command. Confirmed: "no command called 'values'". The text
  refers to it twice.
- Discovery worth flagging: **`why <id>` works on things that are not visible in
  `available` at all.** precision_three_plate and thermometer disappeared from both the
  startable list and the HEARD-OF list, but `why` still gave me their full entry
  including cost, prerequisites and "TRADES NOT YET TAUGHT HERE: machinist". Under fog
  of war that is a large hole - if I remember an id, fog does not apply to it. It is
  also the only way I found to answer "why can't I see this any more?".
- Also learned from `why`: some projects say "BOUNTY: yes, could be posted as a public
  prize". I have not needed `bounty` yet.
- lens_grinding (1,418 -> 3,200/yr) and en_post_mill (519 -> 1,000/yr) are again
  absurdly profitable. Revenue is now 17,358/yr against 9,490 of costs, net +7,868.
  Money has stopped being a constraint for the second time, and faster than before.
- **Revenue scaling changes over time and is never explained.** Indigo pays 300
  nominal; in 101 it paid 222 (x0.74), in 127 it pays 346 (x1.15). Something -
  reputation? society values? - multiplies output, and the only way to see it is to
  diff the ledger against the EARNS/YR column.
- EVENT 126: "your patron dies; his heir must be courted afresh" - scandal jumped
  0.96 -> 5.1. The patron_local concern stayed running, so the event was a scandal
  shock rather than a loss of the institution. I liked it; it made 200/yr of upkeep
  suddenly feel like a real relationship rather than a line item.
- **Headcount cap found the hard way:** "REFUSED: you can supervise, house and teach
  1.97 more people, not 4". The refusal message is genuinely good - it lists every way
  out (hire a different trade, commission a job, build freedman_staff, buy slaves then
  manumit). I had no idea a cap existed until I hit it; nothing in `labour` or `state`
  shows the cap or how close I am to it. That is the one number I most want on the
  status line and cannot get.

Started precision_three_plate (2,342, 500 hr, 2 yr, "almost everything rests on
this"). EXPECT it to open the machine-tool branch: screw lathe, gauges,
interchangeable parts - which `interchangeable_parts` already hinted at
("missing prerequisites: screw_lathe").

### 9. 130-144: the ladders, and the game becoming a treadmill
From 130 the loop settled into a rhythm and I stopped having to think:
  read `available`'s "MOST RESTS ON THESE" -> start all of them -> `step 3` -> repeat.
That five-row hint is doing all the navigation. Under fog of war it is the ONLY
navigation, and because it is always right, the game plays itself once you can afford
the whole list. From 130 to 144 I never once had to choose.

I turned on `policy auto_open on` and `auto_hire on` purely to stop typing `open` after
every completion. Both worked silently and correctly. Honestly `auto_open` should
probably be the default, or `start` should have an "and open it when done" flag; the
open step added nothing but keystrokes once I had money.

Capability ladders revealed themselves: cap_tol_1mm (granted) -> cap_tol_100um,
cap_heat_1100, and named cap_heat_1300 as a prerequisite of the phosphorus I built in
101. So the spine of the tree is tolerance / temperature / purity capability tiers,
with everything else hanging off them. That is a good model and the fog made
discovering it feel like an actual insight.

Milestones passed: glass_clear, cementation_steel, geometry_analytic, glass_labware,
balance_analytical, lab_apparatus, calculus, master_screw, nitre_beds.
144 AD: 105,945 den, +12,044/yr, 32 built, rep 34.9, eminence 2.5.

Things that bother me at this point:
1. **Money stopped mattering around year 127 and never mattered again.** The premise
   is "building it is not free", but by 140 I could start every single thing on the
   MOST-RESTS list in one turn without checking the price. The one genuinely scarce
   resource is founder-hours, and even that only bites when a 6,000-hour job is open.
2. **Failure risk never bit.** I have started ~35 projects at 5-40% failure risk and I
   do not believe a single one has failed. master_screw at 35% and nitre_beds at 25%
   both completed. Either I am lucky or risk is not doing much; either way I have
   stopped reading the RISK column, which is a shame because it is the most
   interesting number on the table.
3. **The patron keeps dying** (126, 132, 143) and each time scandal jumps ~3. It is the
   only recurring event I have seen besides "fire in the timber wards of the capital",
   which has now happened three times and appears to do nothing to me at all. I cannot
   tell whether that fire is flavour or a near-miss I should react to.
