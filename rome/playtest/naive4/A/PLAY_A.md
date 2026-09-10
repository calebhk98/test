# Playtest A — naive4

Player: Claude (naive playtester). Rules: only the program tells me anything.
Target setup: England, 1300, fog of war ON, "poor scholar" purse, founder does NOT age.

## Log

### Before I start
Expectation: an interactive setup wizard asking nation/year/difficulty-ish questions,
then a save file I resume with `play --session <file>`. I expect a historical
management/strategy sim ("rome/sim/simulator.py" suggests a long-run civilisation or
dynasty simulator). "Founder not ageing" + "poor scholar purse" suggests I run a person
or institution across many years.

### Setup (turn 1)
Answers: 4 (England under Edward I, 1300), y (fog of war), poor_scholar, n (no ageing).

Premise revealed: "ONE PERSON, AND EVERYTHING THEY KNOW" — I'm a modern-knowledge person
dropped into 1300 England with 400 denarii. Knowing is free; building costs hours, money,
materials, years.

Prompt line: `[1300 AD | 400 den | you:2400 hr | sch 0 art 0 | rep 5] >`
Guess at fields: year, money, my own labour-hours per year (2400), sch = scholars?,
art = artisans? (employees I can hire), rep = reputation (0-10?).

Suggested first commands: state, available, why <name>, step, help.

Expectation before first look: `available` will show a small list of cheap things a
lone scholar can start — probably teaching/scribing for income, and a few simple
inventions. I expect money to be the binding constraint early, and that I'll need an
income source before any real project. Real history hook: Great Famine in 15 years,
Black Death in 48 — so the game is signalling a deadline.

### Learning the interface (still 1300)
CONFUSION #1: the game says come back with `simulator.py play --session england_1300.json`
but that errors: "this save is from a different civilisation ('england_1300'); this game is
running 'rome_100ad'. Start the agent with --civ england_1300". The printed resume line is
wrong for every civ except Rome. Correct line: `play --civ england_1300 --session ...`.
CONFUSION #2: after the setup wizard, if you exit before typing a command, it prints
"Saved to england_1300.json" but no file is written. Only after a real command does the
file appear.
CONFUSION #3: `help money` prints the same text as `help economy` (the "ledger/buy/debt"
topic). The money *command* is different from the money *topic*.

What the game is: build a tech tree with one person's hours + money, 1300 -> 1800 horizon,
no score but what you built.

STATE at 1300: 400 den, 2400 founder-hours/yr, rep 5, suspicion 0, 134 technologies
"granted for free" (things this society already has / I know), 0 built by me.
LEDGER: revenue 232.8/yr, all from med_cataract_couching (166.7) and med_trepanation (66.7)
— i.e. I make my living as a surgeon. Living+appearances 230/yr. Net +2.8/yr.
Credit limit 1,503 at 12% on arrears. That explains `available afford 1,151`.

EXPECTATION vs REALITY: I expected to have to find an income (teaching/scribing). Actually
the game *starts* me with a surgical practice earning 232.8/yr. I did not choose that and
was not told about it in the intro — I only found it by typing `money`. That is a real
surprise: my "poor scholar" is in fact a practising eye surgeon.

RISK (from `risk`): Great Famine 1315-17 (12% staff loss after mitigation), Black Death
1348-50 and recurrent (45% staff loss), Hundred Years War 1337-1453 (output x0.80).
Mitigations named: clean water, quarantine, inoculation; and for the war, "land and power
of your own, not depending on trade a war can cut". That is a clear, legible steer.

LABOUR: can hire artisan, carpenter, engraver, furnaceman, glassblower, labourer, mason,
master, merchant, millwright, miner, plumber, potter, sailor, scholar, scribe, smith.
MUST BE TAUGHT (don't exist in 1300): chemist, electrician, engineer, machinist, optician.
That is a nice concrete statement of what 1300 lacks.

AVAILABLE: 103 startable now across 19 subjects. Biggest: finance 17, household 15,
roads/bridges/canals 15, farming 14, power and precision 9, textiles 8.

Notable single item: `cap_measure_time_s` "Time to the second (pendulum)" costs 0 den,
0 hours, 0 years — but UPKEEP 20/yr and REVENUE 0. With net income of +2.8/yr that free
thing would put me 17/yr in the red. EXPECTED a free tech to be an obvious yes; the
upkeep makes it a real decision. Good.
Also odd: it says prerequisite clock_pendulum is already met in 1300 — a pendulum clock in
1300 is ~350 years early. I assume that's because it was in my 134 "granted" set. Slightly
unrealistic-feeling.

`arrival_orientation` (561 den, 900 hr, 6 months, 2% risk): explicitly optional, buys
accurate local prices, the law, who's who, and "a large reduction in early blunder risk".
EXPECTATION: this is the tutorial's recommended opening. It costs more than I have (561 vs
400) and 900 of my 2400 hours. I'll decide after I see what income options exist.

### The revenue survey (1300) — the biggest thing I learned
`available` shows COST/HOURS/YEARS/RISK but NOT revenue or upkeep. You only get those from
`why <id>`, one at a time. So to play well you must `why` every single item. With 103
startable that is 103 commands. TEDIOUS — the single worst usability problem so far. I would
want a `revenue` / `upkeep` column, or `available sort roi`.

It matters enormously, because the spread is huge. Household subject, all 15 items:
  toys_dolls        83 den,  60h -> rev 150/yr, upk 2     (payback ~7 months)
  button            37 den,  40h -> rev  50/yr, upk 1
  umbrella         100 den,  80h -> rev  60/yr, upk 3
  safety_pin        27 den,  40h -> rev  15/yr, upk 0.5
  mechanical_clock 1092 den,180h -> rev 1200/yr, upk 20   (!!)
  toothbrush        33 den,  60h -> rev  30/yr, upk 40    <- LOSES 10/yr forever
  cosmetics/punkah/mangle/latrine/washing machine/flush toilet/chimney/sprung mattress
                                 -> rev 0, upkeep 3..20   <- all pure money sinks
EXPECTATION BROKEN: I assumed "cheap + low risk" was the guide, because that is what the
list sorts and shows. Actually cheapness is nearly uncorrelated with worth. The toothbrush
is the clean trap: 33 den to build, then bleeds 10/yr forever. I like that the trap exists;
I dislike that the list hides exactly the number that reveals it.

REALISM NOTE: revenue for a lone person from "toys and dolls" being 150 den/yr while a
mechanical clock for the home yields 1,200 den/yr feels like these are business lines, not
inventions. Fine, but the framing ("technologies you built") doesn't say that.

### Plan for 1300
I will NOT buy arrival_orientation (561 den) — I only have 400 and its stated benefit
(prices, law, blunder risk) is vaguer than 150 den/yr of cash.
START: hom_toys_dolls, hom_button, hom_umbrella, hom_safety_pin.
  = 247.8 den of my 400, 220 hours of my 2400.
EXPECTATION: all four run in parallel; by end of 1301 I should have ~275 den/yr of new
revenue on top of 232.8, i.e. ~500/yr, and can then borrow toward the 1,092 clock, which
should roughly quintuple income again. I expect the constraint to be MONEY, not hours —
I'm using 9% of my hours and 62% of my cash.
RISK I'm accepting: 5%+2%+5%+2% failure chances. I don't yet know what "failure" costs.

### 1300 -> 1301: first step
Started 4, stepped 1 year. ALL FOUR COMPLETED IN 1300 — including two with a 0.50-year
"calendar floor". EXPECTED them to take until mid-1301; the floor appears to be satisfied
within the same step. So "calendar floor 0.5 years" does not mean "half a year of the next
step"; a 1-year step swallows it. Worth knowing: steps are chunky, sub-year detail is lost.

SURPRISE: "COMPLETED 1300: Sails on ships" — something I never started completed itself,
and granted techs went 134 -> 135. Nothing explained it. I still don't know what that was.

REVENUE IS NOT WHAT `why` QUOTES. Quoted vs actual, all scaled by exactly 0.711:
  toys 150 -> 106.7, umbrella 59.8 -> 42.5, button 50 -> 35.6, safety pin 15 -> 10.7.
Meanwhile my pre-existing surgery income ROSE by x1.0666 (166.7 -> 177.8). So there is some
scaling the game does not show me and did not warn about. I would have planned differently
if `why` had said "about 0.7x of this in your civ". CONFUSING.

Reputation 5 -> 13.2 after four builds. Scandal 1.9 appeared from nowhere (no explanation).
Credit limit 1,503 -> 3,876: reputation clearly buys borrowing power. Net/yr now +196.4.

### The full ROI survey (1301)
I dumped `available all`, then ran `why` on all 83 ids I could scrape, and tabulated
cost/hours/revenue/upkeep. Findings:
- Only ~35 of 83 startable things produce ANY revenue. Roughly half are pure upkeep sinks.
- The best returns are wildly better than the rest, and are not the expensive things:
    tex_field_bleaching  181 den,  50h -> +370/yr net
    tex_horizontal_loom  158 den,  80h -> +370/yr net, and "a few things" rest on it
    tex_indigo           129 den,  60h -> +260/yr net
    tex_mordanting        89 den,  40h -> +135/yr net, "a few things" rest on it
  Textiles is simply the money subject in England 1300. That is historically satisfying
  (English wool/cloth) and I like that the game rewards noticing it.
- The worst: fin_annona 3,627 den for 0 revenue and 300/yr upkeep; sea_lead_sheathing
  1,590 for 200/yr upkeep; met_safety_lamps 1,105 for 180/yr. These would ruin an
  unwary player and nothing in the list warns you.
PLAN 1301: borrow into the textile cluster. Start field_bleaching, horizontal_loom, indigo,
mordanting, spinning_wheel, hand_ginning, prn_sizing_surface, fin_mortgage.
  868 den (I have 169.7, so ~700 of debt at 12%) and 530 of 2,400 hours.
EXPECTATION: +~950 den/yr net revenue, debt cleared inside a year, and the loom/mordant
lines open the next rung of the textile tree. Borrowing at 12% against >100%/yr returns is
obviously right; my worry is an unmodelled penalty for arrears (scandal? ruin?). I'll watch
`state` for it.

### 1301 -> 1302
Textile cluster mostly completed in one year. Revenue 232.8 -> 1,337/yr; net +910/yr.
Money -428 den (deliberate debt), credit limit now 7,649, interest fell 12% -> 11%.
Reputation 25.1. Techs built by me: 10.

Two projects stalled and the reasons were clearly stated, which I liked:
  "Field bleaching  100% of your hours spent, 90.5 den still owed - waiting on money"
  "Mortgage         60% of your hours spent, 0 den still owed - waiting on your hours"
So a project can be hour-starved even when I've only used 530 of 2,400 hours — there must
be a per-project annual hour cap I can't see. WANTED AND COULDN'T FIND: any way to ask
"how many of my hours will this get this year" or to prioritise one project over another.

CONFUSION #4: the `state` footer line reads
  "more: knowledge_risk -> risk; how_to_grow_staff -> labour; policy -> policy; ..."
I read those left-hand names as node ids and typed `why knowledge_risk` — REFUSED. They are
topic -> command pairs. The arrow reads like "leads to", not "type this".

### THE BIG FIND (1302): the two nodes that matter are invisible
`available` sorts by cost and shows no revenue, no upkeep and no downstream weight. The
ONLY signal about tree position is the last line of `why`: "HOW MUCH RESTS ON THIS".
I ran `why` on all 100 startable items to build a table. Two of them say:
    units_standards   415 den, 300h, upkeep 30  -> "almost everything"
    identity_cover  1,477 den, 500h, upkeep 200 -> "almost everything"
Both are tier 0, both startable on arrival, both produce ZERO revenue. Everything else in
the game says "nothing else; this is worth having for itself" or "a few things".
So the correct opening was: units_standards + identity_cover. I did not do that. I did toys
and dolls, because the game's own list put toys and dolls near the top and told me nothing
about the other two. EXPECTATION vs REALITY at its sharpest: the interface actively steers a
new player away from the two moves that matter. If I had not brute-forced 100 `why` calls I
would still be building umbrellas in 1400.
(In fairness: the money detour was not wasted — I can now afford both outright. But that
was luck, not the game teaching me.)

`identity_cover` text: buy books, a house, a secretary, a reputation for piety; "reduces all
future suspicion". `units_standards`: "Do this before writing any other recipe down. Every
number in your corpus is meaningless to posterity without it." That second line is the
tutorial for the whole game and it is hidden three commands deep.

PLAN 1302: start units_standards, identity_cover, civ_arch_roman ("a fair amount" rests on
it). 2,258 den (going to ~-2,700 debt against a 7,649 limit), 860 hours.
EXPECTATION: after these land, `available` should grow a lot — I'm predicting the 100
startable items jump substantially, and the "HEARD OF, CANNOT BEGIN YET" list (currently
just mat_dyes_synthetic and tex_water_frame) becomes reachable. If it doesn't, then
"almost everything" was overstated.

### 1302 -> 1303: the foundations paid off exactly as advertised
Built units_standards, identity_cover, civ_arch_roman (all completed in the one step).
"HEARD OF, CANNOT BEGIN YET" went from 2 entries to 19, and a whole new subject appeared:
"mathematics and method" (scientific_method, world_map, arithmetic_positional).
EXPECTATION MET, and strongly. "almost everything rests on this" was accurate.
Revenue 2,026/yr, upkeep 406.5, net +1,288/yr, debt -1,867 against a 10,287 limit.

Also revenue on existing works keeps RISING year over year with no action from me
(horizontal loom 290 -> 435). Nothing tells me why. I assume reputation or diffusion.

`scientific_method`: 242 den, 350h, 2 years, 20% risk, upkeep 100/yr, prereq identity_cover
(just built), "HOW MUCH RESTS ON THIS: a great deal". Its description is the best writing in
the game so far: "The hard part is not stating it, it is displacing Aristotelian authority...
Expect organised opposition, not curiosity."

CONFUSION #5: `STANDING: reputation 31.8 ... dangerous above 26 (settles near 1.2 ...;
0% chance of ruin this year)`. My reputation is 31.8, which is above 26, and the same line
says 0% chance of ruin. So "dangerous above 26" must be about suspicion or scandal, not the
number printed immediately before it. As written it looks like a warning I am already
violating. I still do not know which number is being compared to 26.

PLAN 1303: scientific_method, arithmetic_positional, world_map, civ_surveying_groma,
civ_brick_tile, civ_truss_triangulated. ~2,038 den, ~1,230 hours.
EXPECTATION: scientific_method opens corpus_written and prc_standard_meter; groma opens
civ_sewer_roman; brick opens civ_insula; truss opens civ_bridge_timber_truss. That is four
named unlocks I can verify. I expect the 20% failure risk on scientific_method to be the
real hazard — I do not yet know what "failure" costs, which is itself a gap: nothing tells
me whether a failed project loses the money, the years, or both.

### 1303 -> 1308: labour becomes the wall
Four of six started projects finished at once; scientific_method and arithmetic_positional
then stalled with a message I thought was excellent:
  "81% of your hours spent, 177.4 den still owed - waiting on nobody to do the work: scribe"
That is the game teaching labour, and it taught it well: the reason is named, and `labour
scribe` gives price (275 den/yr) and market depth (1,321 hours available).
Hired 2 scribes (830 den/yr at first, settling to ~500 as attrition trims). Both projects
then moved.

NICE TOUCH: "EVENT 1305: Decimal positional notation ... changes the society:
literacy_elite, state_capacity". So some builds move the whole civilisation, not just me.
Nothing told me in advance which ones do that — I'd have prioritised differently if `why`
had said so.

Staff are fractional FTEs with 3.5%/yr attrition, and the game explains this in-line the
first time it shows a fraction. Good.

By 1308: 20 techs of my own, money +2,823, net +1,601/yr, revenue still compounding on its
own. The gate has moved from money to PEOPLE. New blockers now read:
  "civ_town_planning  needs 1 trained craftsmen on your own staff, you have 0.0."
and it lists three remedies inline (hire / commission / buy slaves then manumit). Two of the
three are plain English and the third is raw JSON:
  {"cmd":"buy","what":"slaves","n":N}
CONFUSION #6: the interface is bilingual for no reason. Everywhere else it accepts and
prints plain words; this one hint drops into the JSON protocol mid-sentence.

Wages/yr: artisan 220, mason 220, carpenter 220, smith 248, millwright 346, master 440,
scribe 275, scholar 550. Market depth varies a lot (millwright only 604 h available in the
whole market, scholar 1,556, masons 7,548) — a real constraint I did not expect and like.

PLAN: hire a broad staff (artisan 3, smith 2, mason 2, carpenter 2, scholar 2, master 1)
~ 2,400 den/yr against +1,601 net. That is more than I earn, so I'll go debt-financed again
and expect revenue growth plus new works to cover it. EXPECTATION: staffing unlocks
civ_town_planning, fin_arabic_numerals, fin_survey_map immediately, and stops the "waiting
on nobody" stalls for good.

### 1308: a hard cap I cannot see or raise
`hire mason 2` -> "REFUSED: you can supervise, house and teach 0.2 more people, not 2."
So staff is capped at ~7 FTE and I have no idea what raises it. The refusal then advises:
"To get more artisans: hire smith 3 or any trade in labour" — i.e. it tells me to do the
exact thing it just refused. That error message is a loop and it is the worst text I have
hit. WANTED AND COULD NOT FIND: any command that says what my supervision capacity is, what
it is a function of, or what would increase it. `state`, `labour`, `policy` and `help
labour` all stay silent on it.

Third "almost everything" node found: `patron_local` "Secure a town patron", 1,122 den,
400h, upkeep 200, prereq identity_cover, "Halves incoming suspicion."
So the spine of this game is three tier-0 social/foundation nodes —
units_standards, identity_cover, patron_local — none of which earn a penny, all of which
are invisible unless you `why` them one at a time. Everything I found by playing the
obvious way (cheapest first, best ROI first) was a side quest.

New subject appeared after arithmetic_positional: "the remaining arts", 21 items, mostly
sc2_* — the institutions of science (peer review, replication, doctorate, citation,
textbook, curriculum) and Newtonian physics. Their striking feature is CALENDAR FLOORS of
5, 8, 10 and even 20 years, at only ~242 den each. That is a clear "start these now and
forget them" signal, and the nicest bit of design I've met: the game is saying institutions
take a generation and money is not the constraint.
EXPECTATION: starting all the long-floor sc2 nodes in 1308 means they mature 1316-1328,
i.e. before the Black Death in 1348. If instead they turn out to need continuous founder
hours each year, this will jam and I'll have wasted the decade.
PLAN: patron_local + sc2_method_negative_result(20y) + sc2_method_replication(10y) +
sc2_institution_doctorate(8y) + sc2_institution_referee(8y) + sc2_method_hypothesis(8y) +
sc2_institution_examination(8y) + sc2_institution_textbook(8y).

### 1309-1312: I overextended
All 8 started fine — founder hours were NOT the constraint (each showed "100% of your hours
spent" in year one). They then all sat "waiting on money" for years. By 1312:
  revenue 3,108/yr but upkeep 873 + wages 1,430 + living 398 = net only +406/yr,
  capital 90 den, and 1,555 still owed on work in hand.
EXPECTATION BROKEN: I assumed the long calendar floors meant these were cheap to *carry*.
They are not — each carries 40/yr upkeep FROM THE MOMENT IT COMPLETES, and I stacked eight
of them on top of a wage bill I had just tripled. The lesson the game is teaching is real
(institutions cost you every year forever) but I only learned it by nearly stalling.

Also: staff is silently DECAYING (6.8 -> 5.9 FTE) because attrition is 3.5%/yr and auto_hire
is off. Nothing warns you; you just get quietly poorer in people. I only noticed by
comparing two `state` prints.

GOOD SURPRISE: revenue from a finished work RISES over time — tex_field_bleaching was quoted
400/yr, delivered 290 in 1303, and pays 452.9 in 1312. And world_map, which I never checked,
turns out to be my single biggest earner at 566/yr. Interest on my debt also fell 12% -> 9%
as reputation rose. None of this is documented anywhere I could find; `why` quotes one
static REVENUE number that is wrong in both directions at different times.

FIX: switch auto_hire on, and buy the two big earners I identified back in 1301 and never
bought — tex_knitting_frame (877 -> ~1,100/yr) and hom_mechanical_clock_home (1,092 ->
~1,200/yr). EXPECTATION: ~4 years to fund them out of cash flow, after which net jumps to
roughly +2,500/yr and the eight institutions finish themselves.

### 1317: the default policy quietly destroyed my tech tree
By 1317 net is +2,264/yr (clock 1,410 + knitting frame 1,293 were exactly the earners I
predicted). Great Famine came and went with no visible damage.

Then I checked the frontier and found this, four times over:
  "civ_arch_roman   you built this once and let it go; you already know how, so restoring it
                    is cheaper than starting over: restore civ_arch_roman for about 110 den"
`auto_shed` is ON BY DEFAULT and is described as "let go of WORKS that cost more than they
return". Every one of my four civil-engineering prerequisites earns 0 den and costs upkeep,
so the engine demolished all four — civ_arch_roman, civ_brick_tile, civ_surveying_groma,
civ_truss_triangulated — and with them the roads/bridges/water branch, which is 14+ nodes.
Nothing announced it. No event line, no warning, nothing in `state`. I found it only because
I read the "cannot begin yet" list and saw prerequisites I KNOW I built listed as missing.
THIS IS THE WORST THING I HAVE FOUND. A default-on automation that deletes tree progress and
does not tell you, in a game whose entire point is the tree. The mitigation (restore is
cheap: 37-110 den) is good; the silence is not.
Fixed: `policy auto_shed off`, restored all four for 263 den total.

Fourth "almost everything" node revealed by patron_local: `workshop_first` — "First workshop
and laboratory. On navigable water. With a walled yard, a separate furnace shed downwind,
and a door onto the street so that witnesses can see you are not conjuring." 5,383 den, 500h,
upkeep 900/yr. That last clause is the best sentence in the game.
So the spine, in order, is:
  identity_cover -> patron_local -> workshop_first, plus units_standards and
  scientific_method alongside. All zero-revenue, all upkeep, all mandatory, none signposted.

EXPECTATION: workshop_first unlocks case_hardening -> precision_three_plate ->
balance_analytical -> opt_standards_laboratory, plus school_founded and prc_apprentice_system,
and I am guessing it is also what lifts the "you can supervise, house and teach 0.2 more
people" cap, since it is literally a building with a yard. That last one is a guess; nothing
says so.

### 1322: the tree explodes
workshop_first + chm_phosphorus_extraction built. Money 7,557, net +3,230/yr, 32 techs.
`available` goes from 106 startable to **365**. Metallurgy 2 -> 28 items (dearest 106,513 —
that will be the blast furnace the intro promised). Textiles 8 -> 69. New subjects appear:
transport, construction, power stations, expeditions.
EXPECTATION MET, spectacularly. The four spine nodes really were the whole game so far.
This is the single most satisfying moment of the playthrough and it took 22 in-game years.

Then the second wall, and it is a much better-written one than the supervision cap:
  "REFUSED: this society's literacy will not supply more than 2.3 scholars in total, ever,
   at any price; you already have 2.6. Raise literacy_general or literacy_elite -- printing,
   schools and libraries do -- to widen this pool."
That is a perfect refusal: it names the limit, says it is societal not personal, and tells
me the three levers. Compare with the supervision-cap refusal which just told me to do the
thing it refused. Same game, same command, two completely different qualities of message.
Also learned: `train chemist 2` costs "about 450 of your own hours each, two years" — that
is 900 of my 2,400 hours to create a trade this society does not have.

NEW PLAN (1322): (a) printing + schools + libraries to raise literacy and widen the scholar
pool; (b) train chemists; (c) drive at metallurgy, because the game's own opening briefing
said England's missing piece is "cheap iron, and the temperature to make it".

### 1322: found the real spine, and the real bottleneck
`why school_founded`: "The pivot of the entire game. Converts your hours into other people's
hours permanently. Every year of delay here costs more than any single technology.
Grants +4 scholars and +2 scholars/yr thereafter... Money cannot buy this down." 12,650 den,
2,000 founder hours, 4-year floor, upkeep 2,500. Blocked by collegium_licensed (which needs
citizenship) and freedman_staff (+8 artisans, i.e. THE fix for the supervision cap).
So the chain nobody told me about is:
  identity_cover -> patron_local -> {workshop_first, citizenship} ->
  {freedman_staff, collegium_licensed} -> school_founded
Five to seven of my in-game decades, and the game calls the last one "the pivot of the
entire game" only when you finally `why` it. EXPECTATION vs REALITY: I said in 1302 that I
had found "the spine". I had found the first two vertebrae of seven.

Started citizenship, freedman_staff, corpus_written (6,000 founder hours over 10 years —
"the largest single call on your personal hours in the entire game, and the one you must
not cut").

Then I re-ran the `why`-everything survey over all 365 startable nodes. New high-leverage
items now visible:
  case_hardening      1,757 den, rev 1,500, "almost everything"
  refractory_fireclay 2,395 den, rev   600, "almost everything"
  lens_grinding       2,080 den, rev 3,200, "a great deal"   <- best thing in the game
  finery_puddling   106,513 den, rev 9,000, "a great deal"   <- the blast furnace, at last
  charcoal_industrial 63,360 / lead_metallurgy 88,582        <- the heavy industry tier
and a long tail of works returning MORE THAN 1 denarius per year per denarius of cost
(tex_treadle_loom 2.18, tex_rope_walk 2.10, tex_sewing_machine 1.82, tr_hopper_wagon 1.67).
Money has stopped being a constraint; founder hours have become one.
PLAN: start ~22 things at once — the >1.0-return works to fund everything, plus every cheap
"a great deal"/"almost everything" node. ~12,400 den, ~3,400 founder hours (so ~2 years of
me). EXPECTATION: revenue roughly quadruples to >12,000/yr, and case_hardening +
refractory_fireclay open the metallurgy branch that leads to finery_puddling.

### 1327-1341: compounding, and the hazards start to bend
Started 22 works in 1322 and 24 metallurgy/power works in 1331. By 1341:
  90 technologies of my own, 105,382 den in hand, revenue 31,817/yr, net +8,658/yr,
  reputation 82.7, staff 20 FTE, founder hours 2,400 -> 2,500 (the school raised them).
corpus_written completed and `risk` now reads "hedged by corpus_written", with the loss
figures dropping from "80% chance, 40% lost" to "45% chance, 22% lost". That is exactly what
the description promised and it is the clearest cause-and-effect the game has shown me.

Better still, `risk` now itemises what my own works have already bought me:
  Black Death staff loss 45% -> 34% "(softened by fields that do not fail together, fodder
  that keeps through a bad winter)"
  Hundred Years War output 80% -> 49% "(softened by you feed yourself, power that does not
  come by ship, your own roads, losses spread rather than borne)"
and then names what to do next: "you could begin now: soap_hard (2,840 den)". This is the
best-designed screen in the game: it turns a scripted disaster into a shopping list, in
plain English, naming the actual mechanism. I would put this in front of the player far
earlier — I only started reading `risk` seriously in 1327.

CONFUSION #7: projects report "waiting on money" while I am sitting on 31,000 denarii. There
seems to be a per-year cap on how much a project can absorb, but nothing says so, and the
phrase "waiting on money" is exactly wrong when I have thirty thousand of it.
CONFUSION #8: `state` says "dangerous above 26" every single year while reputation has gone
5 -> 83 and the chance of ruin has stayed at 0%. Ten thousand words in, I still don't know
what number that sentence is about.

### 1341-1371: THE DISASTER, and it is the most interesting thing in the game
In 1341 I had 105,382 den, 90 technologies, 20 staff and net +8,658/yr, so I bought the
thing the opening briefing had pointed at from the very first screen: `finery_puddling`,
"Finery forge and the puddling furnace", quoted at 106,567 den. I could just afford it.

Except I could not. Two things I did not know:
1. The quoted COST IS NOT FIXED. By the time the project was running it wanted 207,811 den —
   90,060 of that in materials — because prices had roughly doubled between 1331 and 1371.
   `why` shows one number with no indication that it is a snapshot. This is the single most
   expensive misunderstanding available in the game and nothing flags it.
2. Being in arrears is not merely expensive, it is destructive. From 1349 to 1371 I sat at
   -20,000 to -28,000 den. In that time:
     - staff fell 20 -> 3.3 FTE (I could not pay them, so they left — this IS documented,
       under `policy`, as "not policies: ... people you cannot pay leave")
     - technologies fell 99 -> 85. Fourteen finished works were taken.
     - among them: corpus_written (my ONLY hedge against knowledge loss), school_founded
       ("the pivot of the entire game"), collegium_licensed, freedman_staff.
     - finery_puddling itself was abandoned with ~106,000 den sunk into it. It now reads
       STATUS: BLOCKED and wants 207,811 to start again.
     - I paid 42,556 den in interest.
   `risk` went from "hedged by corpus_written" back to "hedged by nothing yet".
   I had turned `auto_shed` OFF precisely to stop this. It happened anyway, because
   insolvency is a consequence and not a policy.

WHAT I OBJECT TO: not the mechanic — the mechanic is excellent and it is the truest thing in
the game, that a lone genius who overreaches loses the institutions first and the knowledge
second. What I object to is that I watched it happen across a 12-year `step` and the only
evidence was two numbers quietly getting smaller in a screen full of numbers. There was no
"1362: your creditors took the school", no warning at 1350 that I was one bad decade from
losing the corpus. A `step 12` should not be able to silently eat the pivot of the entire
game. At minimum the loss of a work should be an EVENT line, the way completions are.

WHAT I SHOULD HAVE DONE: not bought the furnace. Or rather — checked `why finery_puddling`
again immediately before starting it, seen 207,811 instead of 106,567, and waited. There was
no way to know I needed to, but there was a way to find out.

Also tested `work scholar 1000`: 1,000 of my own hours as a jobbing scholar earns 359.9 den,
against 30,000/yr from my works. Correct and quietly brutal: once you own capital, selling
your own labour is pointless. I like that it is in the game and that it is a trap.

### 1374-1395: recovery, and the game becomes a spreadsheet
Restore prices are ~10% of build cost (corpus 1,271, collegium 718, freedman_staff 2,805,
school 3,795), so recovering from the disaster cost 8,589 den and one command each. That is
a merciful design and I was glad of it — but it also means the catastrophe that removed
99 -> 85 technologies was undone for under 9,000 denarii, which slightly undercuts how
frightening it was.
Note: school_founded REFUSED to restore until collegium_licensed and freedman_staff were
back — "you no longer have what it stands on". Correct and well-worded.

By 1395: 221 technologies, 224,097 den, net +30,168/yr, 47.6 staff, reputation 91.
Founder hours (3,350/yr and rising) are now the only real constraint; every big project sits
at "90% of your hours spent, 0 den still owed - waiting on your hours". That is the right
end-state for a game called ONE PERSON, AND EVERYTHING THEY KNOW, and I think it is the
game's best structural idea: money -> people -> your own irreplaceable time.

HONEST OBSERVATION ABOUT MY OWN PLAY: from about 1380 the optimal move stopped being
interesting. The winning loop is mechanical — dump `available all`, run `why` on every id,
score each by (revenue - upkeep)/cost plus a bonus for "almost everything"/"a great deal",
start everything affordable, `step 10`, repeat. I wrote that loop as a script and it plays
better than I did by hand. The reason it works is that the game gives no penalty for
breadth: there is no attention limit, no maintenance-of-focus, nothing that makes starting
84 projects at once worse than starting 8. The only limiter is money and founder hours, and
both scale faster than the costs do once you are past the spine.

### 1431-1437: trained the trades that do not exist
`train chemist 3` / `engineer 3` / `machinist 3` were REFUSED with the same excellent
literacy-ceiling message ("will not supply more than 2.8 chemists in total, ever, at any
price"), but `train optician 2` and `train electrician 2` went through, and switching
`policy auto_train on` then quietly produced 2 of every missing trade by 1435:
  "EVENT 1433: 2 opticians finish their training" ... "EVENT 1435: 2 chemists finish"
By 1437: 323 technologies, 662,276 den, 79.6 staff including 2 each of chemist, electrician,
engineer, machinist, optician — the five trades the 1300 briefing said England did not have.
That closed the loop on the very first thing the game told me about this civilisation, 137
in-game years later. Satisfying.

### 1437: RUN ENDED BY AN ENVIRONMENT FAULT, not by the game
My next command failed with:
  "could not read the save file 'england_1300.json': this save refers to node(s) the current
   tech tree does not have: chemist, electrician, engineer, machinist, optician. The tree has
   changed since this was saved; it cannot be loaded against this version of the game."
The repository is being edited by others while I play (I had already hit a transient
SyntaxError in the engine earlier in the run and worked around it by retrying). This time the
tech-tree data changed underneath a live save and the save became permanently unloadable.
That is not a fair criticism of the game design, but it IS a real robustness finding:
  - a save that references trained trades cannot survive a tree edit,
  - the failure is total (no partial load, no "drop the unknown nodes and continue"),
  - and the message offers no recovery path at all, not even "start a new game".
For a program whose whole selling point is "stop any time and come back", a save format
this brittle is worth hardening: unknown node ids in a save could be dropped with a warning
rather than refusing the file.
FINAL STATE REACHED: 1437 AD, 323 technologies built by me (461 total), 662,276 denarii,
79.6 staff, reputation ~70, corpus written, school founded, Black Death and half the
Hundred Years War survived. 363 years short of the 1800 horizon.

---

## SUMMARY OF EXPECTATIONS vs REALITY

| I expected | What happened | What made me expect it |
|---|---|---|
| I'd have to find an income | I started with a surgical practice earning 232.8/yr | The intro says "about enough money to eat for a few months" and never mentions the practice; only `money` reveals it |
| Cheap + low-risk = good opening | Cheapness is nearly uncorrelated with value; the toothbrush is a permanent loss-maker | `available` sorts by cost and shows COST/HOURS/YEARS/RISK — the four columns that don't decide anything |
| The quoted REVENUE is what I'll get | Got 0.711x of it at first, then more than 100% of it later as it grew year on year | `why` prints one flat number labelled REVENUE |
| The quoted COST is what I'll pay | finery_puddling was quoted 106,567 and billed 207,811 forty years later | Same: `why` prints one flat COST with a visible formula, which makes it look computed and fixed |
| A 0.5-year "calendar floor" delays a project | A 1-year `step` swallows it entirely | The phrase "calendar floor 0.50 years" |
| Turning `auto_shed` off protects my works | Insolvency took 14 works anyway, including the corpus and the school | `policy` describes auto_shed as the thing that lets works go |
| Founder hours would be the early constraint | Money, then people, then hours — in that order, decades apart | The framing "one person, and everything they know" |
| "almost everything rests on this" would be rare | It is rare (5 nodes in ~460) and it is the entire game | Nothing — I had to brute-force 100 `why` calls to find the first two |

## THINGS I WANTED TO DO AND COULD NOT FIND A WAY TO DO
- Sort or filter `available` by revenue, upkeep, net return, or downstream weight. The one
  field that decides everything ("HOW MUCH RESTS ON THIS") exists only inside `why`, one node
  at a time. I ended up scripting 100, then 365, then 461 `why` calls to build the table the
  game should have given me. This is the biggest single usability gap.
- Find out what my supervision/housing capacity is, or what raises it. The refusal quotes a
  number ("you can supervise, house and teach 0.2 more people") that appears nowhere else.
- Prioritise which running project gets my founder hours. With 5 projects each stuck at
  "90% of your hours spent", I could not tell the engine which one I cared about.
- See the cost of a project *now* without a separate `why`, or be warned that a quote had
  gone stale. `quote` exists but `help` only documents `quote mine coal 500`.
- Get any event line when a finished work is lost. Completions produce EVENT lines; losses
  do not.
- Understand `eminence` or `scandal`. Both are printed every turn, both moved a lot, and
  neither is explained by any `help` topic I could find.

## THINGS THAT STRUCK ME AS UNREALISTIC OR ODD
- In 1300 I already "had" clock_pendulum as a granted technology, three and a half centuries
  before Huygens. The granted set seems to be the union of what the tree needs rather than
  what the society had.
- Revenue lines like "Toys and dolls: 169.8 den/yr" and "Umbrella: 67.7" are business
  incomes, but the game calls them technologies and counts them in "technologies built by
  you". Building an umbrella business and building the puddling furnace score the same way.
- 47 to 80 employees, an aqueduct, a school, a licensed collegium, a paved road network and
  a puddling furnace, and my `suspicion` stayed at exactly 0.0 for 137 years while the
  Hundred Years War ran. The social-danger system (suspicion, scandal, "dangerous above 26")
  never once did anything to me. Given how much text the game spends on Aristotelian
  authority, guild litigation and being burned as a conjuror, I expected to be in trouble at
  least once.
- The Black Death killed 45% of my staff and nothing else. Prices, wages and the labour pool
  did not visibly react to half of England dying, which historically is the single biggest
  thing that happened to English labour.

## TEDIOUS OR HARD TO READ
- `why` is the only source of the decisive numbers and is one-node-at-a-time. 461 invocations
  to see the board once.
- `state` prints the same 20 lines whether or not anything changed, and prints them twice if
  you type `step` and `state` in the same batch.
- The footer "more: knowledge_risk -> risk; how_to_grow_staff -> labour; ..." reads like a
  list of node ids. It is a list of topic-to-command mappings.
- "dangerous above 26" on the reputation line, forever, while reputation is 83 and ruin risk
  is 0%.
- The refusal messages paste the same three-remedy block (hire / commission / JSON slaves)
  into every unrelated error, including the one where the remedy is refused.
- `help money` shows the economy topic, not the money command.
- The resume line printed at every exit is wrong for every civilisation except Rome: it omits
  `--civ`, so following the game's own instructions produces an error.

## WHAT THE GAME TEACHES WELL
- The spine is social, not technical: legal standing, a patron, a cover identity, a
  workshop, a licence, a freed staff, a school. Every one is expensive, none earns anything,
  and nothing works without them. That is the right lesson and it is the whole shape of the
  game.
- Institutions take a generation and money cannot buy the years down (5, 8, 10, 20-year
  calendar floors on peer review, replication, the doctorate).
- Selling your own labour is worthless once you own capital (1,000 founder-hours = 360 den
  against 30,000/yr from works).
- `risk` turning scripted catastrophes into a shopping list, and then naming which of your
  own works softened them ("softened by hard soap, in quantity, fields that do not fail
  together, fodder that keeps through a bad winter"), is excellent.
- The literacy ceiling: "this society's literacy will not supply more than 2.8 chemists in
  total, ever, at any price". A limit that is about the society and not about your money.

---

## RUN B (a control experiment, 1300 again)
Run A's save was killed by the tree change, so I started a second England 1300 game in the
same directory (`england_1300_b.json`) to test the conclusion I had drawn from run A:
"the correct opening is units_standards + identity_cover, and my toys-and-dolls detour was a
mistake."

That conclusion is WRONG, and the game proves it in five years.
Starting units_standards (415) and identity_cover (1,477) immediately from the 400-denarius
poor-scholar purse puts you at -988 den with net income of +23.4/yr. Then:
  "Establish a respectable cove  90% of your hours spent, 152.9 den still owed"
  "Define and publish standard    0% of your hours spent, 415.1 den still owed"
and nothing moves, at all, for years — in arrears your founder hours do almost nothing, so
you cannot even work your way out. Five years in I had built zero technologies.
So the real structure is: you MUST run a trinket economy first (buttons, dolls, umbrellas,
then the textile cluster) to reach roughly 1,000 den/yr, and only then can you afford the
foundations that actually open the tree. My "wasted" first two years in run A were in fact
the only possible opening.
That is a good piece of design — and it means my complaint about `available` burying the
spine is only half right. The spine is unaffordable at the start anyway. What the interface
should be telling a new player is not "buy this first" but "these exist, and here is what
they will cost you when you can afford them".
(Also visible in run B and not in run A: the header now reads
"YEAR 1300   (500 years to the horizon at 1800)". Someone improved that line while I was
playing — it is a real improvement, it was the one number I kept having to work out myself.)

### Run B also killed, and now the fault is reproducible
Run B reached 1328 AD (15 technologies) and then died with the same error as run A:
  "could not read the save file 'england_1300_b.json': this save refers to node(s) the
   current tech tree does not have: engineer, machinist."
Run A died naming chemist, electrician, engineer, machinist, optician. Run B named engineer
and machinist. In both cases the trigger was the same: the save had recorded TRAINED TRADES
(run A by explicit `train` plus `policy auto_train on`; run B by `policy auto_train on`
alone). Both saves were fine for many years until a trained trade entered them.
So: trained trades are stored in the save as node ids, and any save containing them cannot
be loaded once those ids move or change in the tree. Everything else in a save survives.
That is a specific, reproducible robustness bug and it costs the player the entire run.
Suggested fix: store trained trades as trade names, not tech-tree node ids; or drop unknown
ids with a warning and load the rest, rather than refusing the file.
(Caveat, stated plainly: the tree was being edited by other people while I played, so this
is not something a normal player would hit every day. But a save format that cannot survive
its own game being patched is worth fixing regardless, in a game explicitly sold on "stop
any time, close the terminal, come back".)

### Run B's own lesson, before it died
Run B confirmed run A's shape twice over. Buying the spine early is not merely suboptimal,
it is fatal:
  - spine first from 400 den -> -1,061 den, net +23/yr, 0 technologies after 5 years, and in
    arrears your founder hours do nothing, so you cannot even work the debt off through the
    projects.
  - the escape hatch is `work`: `work scholar 2400` earns ~673 den/yr, which is enough to
    climb out of a 1,300-denarius hole in two years and nothing else. That is exactly what
    that command is for, and I had dismissed it as useless in run A because by then it was.
  - then, having bootstrapped textiles to +1,086/yr and immediately bought workshop_first
    (5,383 + 900/yr) and citizenship (5,610), run B went straight back to -4,377 and
    -790/yr. In run A I did not buy the workshop until net was +3,200/yr, and that is
    apparently the real threshold.
The game is teaching something quite precise here: each rung of the spine needs an income
roughly equal to its own annual upkeep before you can carry it, and there is no way to see
that in advance except by trying and failing.

### MINIMAL REPRODUCTION OF THE SAVE-KILLING BUG
On a healthy run-C save at 1380 AD (240 technologies, 691,891 den), one single command:
    train optician 1
and the very next invocation fails permanently:
    could not read the save file 'england_1300_c.json': this save refers to node(s) the
    current tech tree does not have: optician.
Nothing else is needed — no auto_train, no step, no further play. Any `train` of a trade
whose node id is not in the currently-installed tree destroys the save on write. I recovered
by keeping a copy of the save file beside it, which is the only reason run C survived.
So the practical advice to anyone playing this build is: **do not use `train`**, and keep a
backup copy of your session file. That is a bad place for a game to be, since `train` is the
only route to chemists, engineers, machinists, opticians and electricians, and those five
trades gate the entire chemistry, precision and electricity half of the tree.

## RUN C — a complete playthrough, 1300 to the 1800 horizon
Knowing the shape from run A, I replayed properly: trinkets -> textiles -> clock and knitting
frame -> spine (units_standards, identity_cover, arithmetic, patron_local, scientific_method,
workshop_first, citizenship) -> then a scripted breadth loop. I never used `train`, because
`train` destroys the save in this build.

Milestones:
  1307  14 techs,      9,214 den, +3,902/yr   (vs run A: 1303, 15 techs, -1,867 den)
  1330  33 techs,     18,903 den
  1356 167 techs,    217,891 den   (Black Death survived)
  1400 246 techs,    801,420 den
  1490 509 techs,  2,150,304 den
  1600 742 techs,  8,196,824 den
  1700 809 techs, 16,362,847 den
  1800 813 techs, 17,756,546 den, 308 staff, 951 technologies in total

### AND THEN THE GAME TOLD ME WHAT IT WAS ABOUT
At 1800 the run ends and `state` prints two things it has never printed once in 500 years:

    *** THE RUN HAS ENDED: ran out of horizon (1800 AD) without reaching the goal ***
    Goal: point_contact_transistor
    EMINENCE is dangerous above 26 (settles near 8.1 ...)

1. THERE IS A GOAL, AND IT IS SECRET UNTIL YOU FAIL. `help` told me "Advance as far as you
   can before the horizon at 1800. There is no score but the state of what you have built."
   That is not true. The goal is the point-contact transistor, and the end screen says so
   flatly: "Getting here from 100 AD is the whole game." I played 500 years optimising
   breadth — technologies built — when I should have been driving one specific chain.
   This is the single biggest thing I would change. Under fog of war I accept not seeing
   the tree. Not being told what I am aiming at is different: it is the difference between
   a hard game and an unfair one. Even "your goal is the transistor; you cannot see the
   route" would have completely changed how I played.
2. "dangerous above 26" is about EMINENCE. The label appears only on the end screen. For 500
   years that sentence sat under the reputation line with no subject, and I noted it twice as
   confusing before finding out by accident at the very end.

And with the run over, the fog lifts on `why`, which now prints what I wanted all game:
    FULL CHAIN BEHIND IT: 145 nodes, 55,420 of your hours, 9,421,124 den,
                          142.2-year serial floor
    DIRECTLY UNLOCKS: junction_transistor
    TOTAL DOWNSTREAM: 5 things depend on this -- INCLUDING THE GOAL
    TRADES NOT YET TAUGHT HERE: chemist, machinist
So the transistor was reachable: 145 nodes, 9.4M denarii (I finished with 17.8M) and a
142-year serial floor against my 500. I had the money and the time. What I did not have was
chemists and machinists — the two trades that require `train`, the one command that destroys
the save in this build. The bug did not just annoy me; it cost me the game.

## FINAL VERDICT AS A PLAYER
The good: the spine is social and expensive and it is the truest thing here. `risk` naming
which of your own works softened a famine is superb. The literacy ceiling, the trades that
must be taught, the fact that selling your own labour becomes worthless, the fact that
institutions take twenty years and money cannot buy the years down — all of that teaches
something real.
The bad: the interface hides the three numbers that decide everything (revenue, upkeep,
downstream weight) behind a one-at-a-time command, so competent play degenerates into
scripting `why` across the whole tree; catastrophic losses happen silently inside a `step`;
quoted costs go stale by 100% over decades with no warning; and the goal is a secret.
The fatal: `train` kills the save.
What I would fix first, in order: (1) show the goal; (2) put revenue/upkeep/downstream in
`available`; (3) make the loss of a finished work an EVENT line; (4) fix `train`.
