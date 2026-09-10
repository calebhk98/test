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
