# PLAY_A — naive playtest log

Setup goal: England, 1300, fog of war ON, "poor scholar" purse, founder NOT ageing.

## Expectation before first launch
I expect an interactive setup wizard: pick a country/region, a start year, some
toggles. I expect it to then print a save-session filename I can pass back with
`play --session <file>`. I expect a turn-based strategy/management game of some kind
("rome"/"sim" suggests a historical simulation). Poor scholar purse suggests a
money-constrained start; "founder not ageing" suggests I run a dynasty/institution
and the founder is a persistent avatar.

## Setup (actual)
Game title: "ONE PERSON, AND EVERYTHING THEY KNOW". Premise: I'm a modern-knowledge
person dropped into a pre-industrial society. Knowing is free; building is not.

Answers: 4 (England under Edward I, 1300) / fog of war Y / poor_scholar / age+die N.
Session file: england_1300.json in my own dir.

Opening HUD: `[1300 AD | 400 den | you:2000 hr | sch 0 art 0 | rep 5]`
Guesses at HUD fields: den = denarii (money), you:2000 hr = my own labour-hours per
year, sch = scholars?, art = artisans? (staff counts), rep = reputation 0-10?

Suggested commands: state, available, why <name>, step, help, quit.

### Expectation before `help`/`state`/`available`
I expect a tech-tree game where each "project" costs money + my hours + hired
hours + years. With 400 den and 2000 hr/yr and no staff, I expect the first move
has to be earning money (teaching? a cheap invention to sell?) rather than
starting a big project. Big worry the game flagged: Great Famine in 1315, Black
Death in 1348. So I expect a time pressure to either build something robust before
1348 or deliberately wait.

## 1300 — first look

`help` reveals the objective: **build a point-contact transistor before 1800**. 500 years.
132 technologies "granted for free" (what England already has). Fog: I only see the
next step.

`state full:true`: 400 den, net +2.8 den/yr, 2000 founder-hours. Reputation 5,
scandal 0, eminence 0 ("dangerous above 26"). Risks ahead: Great Famine 1315-17,
Black Death 1348-50, Hundred Years War 1337-1453, "3 technologies at risk,
hedged by nothing yet".

`available`: 105 startable. Two flagged "RESTS: ALL":
  identity_cover   1,477 den / 500 hr / 0.5 yr / upkeep 200 -- can't afford
  units_standards    415 den / 300 hr / 0.5 yr / upkeep 30  -- can't quite afford
Cheapest six include two free things (cursus_publicus, pharos_lighthouse) and
med_bone_setting (10 den, earns 6.2/yr).

### Expectations before asking `why`
- identity_cover: I expect this is the gate on being taken seriously — hiring,
  patronage, maybe protection from scandal. "RESTS ALL" makes it look mandatory.
  200/yr upkeep on a 400 den purse is frightening.
- units_standards: standard weights/measures; I expect it gates all precision
  engineering (which a transistor surely needs).
- The two 0-cost items look like scenery/flavour. cursus_publicus with 200/yr
  upkeep and 0 benefit would be a trap.
- I expect I must first EARN. `work <trade> <hours>` exists, so the intended
  opening is probably: work for pay, or start a cheap earning venture
  (med_bone_setting earns 6.2/yr for 10 den — 60% return, but tiny).

## Reading the board (1300)

`available all` gives 105 items with COST / HOURS / YEARS / RISK / EARNS/YR /
UPKEEP / RESTS. Money-makers are obvious once you can see the table:
  tex_horizontal_loom  158 den -> 400/yr rev, 30 upkeep, 80 hr, 0.5 yr, 10% risk
  tex_indigo           129 den -> 300/yr, 40 upkeep
  hom_toys_dolls        83 den -> 150/yr, 2 upkeep
  hom_button            37 den -> 50/yr, 1 upkeep
`labour`: hireable trades = artisan, carpenter, engraver, furnaceman, glassblower,
labourer, mason, master, merchant, millwright, miner, plumber, potter, sailor,
scholar, scribe, smith. MUST BE TAUGHT: chemist, electrician, engineer, machinist,
optician. That is clearly the spine of the whole game — a transistor needs the
taught trades, and teaching costs my own hours.

`arrival_orientation` is explicitly optional and gates nothing; 561 den + 900 of
my 2000 hours for "reduced early blunder risk". I am skipping it: I cannot afford
it and the game tells me plainly it leads nowhere.

### PLAN / EXPECTATION for turn 1
Start tex_horizontal_loom + hom_toys_dolls + hom_button (278 den, 180 hr).
Expect: money deducted (probably up front), projects run for 0.25-0.5 yr, then
complete; then I must `open` each to actually earn. Expect ~600/yr gross once
open, which pays for identity_cover and units_standards within 3-4 years.
Risk I am accepting: 10%/5%/2% failure, which I assume loses the spend.
Unknown I want to test: whether `start` charges immediately, and whether several
projects can run at once.

## 1300 -> 1301: first surprises

`start` does NOT charge money up front — the bill accrues as your hours go in.
All three finished inside the first year (I had 2000 hours, needed 180).
SURPRISE 1: a fourth tech, "Sails on ships", completed for free alongside them.
Nothing told me why; I assume some techs come free once prerequisites exist.
SURPRISE 2: reputation jumped 5 -> 11.2 and **scandal appeared at 3.7** from
building three ordinary things. Nothing warned me building would create scandal.
SURPRISE 3 (the big one): `open` was REFUSED on all three —
  "nobody free to keep an eye on it: it needs 0.0 scholars and 0.0 craftsmen to
   supervise, and you have 1.0 and 0.0"
It says it needs 0.0 craftsmen and refuses because I have 0.0. That message reads
like a bug; the real requirement must be a small fraction rounded to 0.0.
I expected a completed project to just start paying. Instead knowing / building /
RUNNING are three separate states, and running needs supervisory staff.

SURPRISE 4: `money` shows I already earn 248.4 den/yr from med_cataract_couching
and med_trepanation — free-granted techs that are apparently already running.
I never chose those and cannot see them in `ventures`. Living costs 227/yr.
Credit limit 3,218 den at 12%.

Trade prices: artisan 220 den/yr, scholar 550 den/yr. engineer/chemist/machinist/
electrician/optician do not exist and must be trained out of my own hours.

### Expectation for next step
Hire 1 artisan (220/yr) -> should free enough craftsman-supervision to open all
three. Net should go to roughly +370/yr. Note `labour trade artisan` is wrong
syntax; it is `labour artisan` (help said 'add "trade"', which misled me).

## 1301 — hiring, opening, and the ledger

`hire artisan 1` (230/yr) let me open all three. Note the stated EARNS/YR is a
headline, not what you get: the loom advertised 400/yr and shows 284.5 in the
ledger. Nothing explained the haircut. Net/yr went to +156. I am at -129 den —
the game let me go into debt without asking (credit limit 3,449 @ 12%).

`risk` is the best screen in the game so far. It tells me:
  Great Famine 1315-17: 12% staff loss (after what I've built)
  Black Death 1348-50: 45% staff loss; helped by clean water, quarantine, inoculation
  Hundred Years War 1337-1453: 80% output hit, softened by "power that does not
  come by ship"; suggests fin_marine_insurance / civ_surveying_groma
It even explains WHY the Hundred Years War helps a technology importer (Edward
III's 1331 patent to John Kempe). That is genuinely good teaching.

`policy` lists 11 automations. Turning on auto_open and auto_hire.

### Expectation for the 1301 build-out
I am going to borrow against the 3,449 credit line and start ~15 cheap
high-margin ventures at once (~1,600 den, ~1,100 of my 2,000 hours). Expect:
they all complete in a year or two, auto_hire buys the artisans needed, auto_open
switches them on, and net/yr goes to roughly +700-900. Then buy identity_cover
(scandal control) and units_standards (gates "almost everything").
Risk I expect: scandal rising with each build, and interest ~200/yr on the debt.

## 1301-1303 — the money engine

Started 17 ventures at once; nearly all finished within a year (my 2,000 founder
hours are the real constraint, and most cost 30-120 hours).
- auto_open was ON but opened NOTHING. I had to open all 16 by hand. My guess is
  it refuses while capital is negative, but the policy text ("open concerns that
  plainly pay for themselves") does not say that. This was the most confusing
  moment so far — a switch that is on and silently does nothing.
- auto_hire was ON and also hired nobody; I hired 3 artisans by hand.
- Staff are fractional FTEs with 3.5%/yr attrition. The state screen explains this
  well.
- Revenue per venture drifts UP over time (loom 400 -> 452.9). Never explained.
  Possibly reputation or price index. It makes the EARNS/YR column advisory only.

By 1303: 19 techs built, revenue 2,152/yr, net +662/yr, debt -1,789, credit limit
13,362 (it scales with revenue, so borrowing gets easier as you grow).
Reputation 44.3, scandal 5.0, eminence 0.30.

### Expectation now
Start identity_cover (1,477) + units_standards (415), the two "RESTS: ALL" items.
I expect units_standards to unlock a precision/measurement branch (the road to a
transistor must run through precision), and identity_cover to suppress scandal.
I also expect `available` to have grown a lot after 19 builds.

## 1303-1306 — the spine appears

After building the lathe / silica brick / Bessemer converter, `available` grew from
105 to ~300 items across 22 subjects. The "MOST RESTS ON THESE" block is the only
navigation aid under fog, and it works: it keeps handing me the next four load-
bearing things. That is a good design — but it also means the optimal strategy is
simply "do whatever is in that box", which makes the fog feel less like a fog.

Confusions:
- `available subject electricity` returns 0; the correct form is `available
  electricity`. The help line "add subject, find, afford, limit/offset" reads as
  if `subject` is a keyword. Same trap as `labour trade artisan`.
- Subject "electricity" in 1306 contains only com_optical_codebook and
  com_signal_flags — signalling, not electricity. Mis-shelved.
- Things with no revenue (identity_cover, units_standards, the lathe, the
  converter) ALSO have to be `open`ed and carry upkeep. Nothing says whether
  their benefit applies when merely built or only when open. I opened them to be
  safe: +340 den/yr of upkeep on a guess.
- `open` refuses when a work needs 1.0 craftsmen and I have 0.9 free, so
  supervision headcount, not money, throttles how many concerns you can run.

1306: 28 techs built, revenue 3,319/yr, net +1,447/yr, debt -6,238 at 10%.
Reputation 54, scandal 4.0, eminence 0.95. Debt has grown every turn and the game
has never once warned me about it; the credit limit just keeps rising with
revenue (17,215 now), which feels too permissive for 1300.

### Expectation for 1306
New "RESTS: ALL" items: patron_local (1,122), arithmetic_positional (968),
scientific_method (242, "much"). I expect scientific_method is the gate on the
whole research/chemistry/electricity half of the tree — it is cheap and I expect
it to be the single most important thing I have seen. patron_local I expect to be
political protection (like identity_cover). arithmetic_positional should gate
mathematics.

## 1309 — the first real wall

Two things went wrong at once, and both were interesting.

1. `arithmetic_positional` stalled: "waiting on nobody to do the work: scribe
   (wants 2500 hours a year; this society can field 1321 at most)". It is
   UNCOMPLETABLE in 1300s England at any price. Nothing in the `why` screen
   warned me — `why` lists "HIRED LABOUR" but not whether the market can supply
   it. That is the single worst information gap I have hit: I committed 968 den
   and 450 founder-hours to something the engine already knew was impossible.
2. It also starved `scientific_method` (needs only 250 scribe-hours) because
   arithmetic had the scribes booked. So one impossible project silently blocked
   a possible one. I am stopping arithmetic and eating the loss.

`hire scribe 3` -> "this society's literacy will not supply more than 2.2 scribes
in total, ever, at any price... Raise literacy_general or literacy_elite --
printing, schools and libraries do". Good message, and it names the lever.
`hire artisan 6` -> "you can supervise, house and teach 3.84 more people... build
workshop_first (you need somewhere for them to work)". Also good.

So the real gate is **workshop_first**: 5,383 den, 500 hr, 1 yr, 900/yr upkeep,
"RESTS: almost everything", prereq patron_local (which I built — and then got
"EVENT 1307: your patron dies; his heir must be courted afresh", so patronage
decays and presumably must be re-bought).

The "HEARD OF, CANNOT BEGIN YET" block is the best part of fog: it shows the
shape of the road without the map —
  workshop_first -> case_hardening -> precision_three_plate -> balance_analytical
  -> opt_standards_laboratory; and high_temp_furnace -> mat_bulk_steel.
That is recognisably the real road to a transistor.

### Expectation
Stop arithmetic, start workshop_first. Expect debt to ~-12,000 against a 17,000
limit and 900/yr new upkeep, but expect it to unlock staff capacity (more than
3.84 people) and the precision branch.

## 1311 — debt is a trap door

workshop_first and scientific_method both completed (1309/1310). scientific_method
printed "changes the society: w_magic_fear, w_novelty" — the first hint that my
work moves world values. Nice touch, never explained anywhere.

Then the discovery that reframes the whole game:
  `hire artisan 4` -> "REFUSED: hiring 4 artisans costs 880 pence in advance and
  you have -9206"
**You cannot hire anyone at all while your capital is negative.** That is why
auto_hire and auto_open had been silently doing nothing since 1301. The game let
me borrow up to 17,000 without a word of warning, and the penalty for using the
credit line is that the labour market — the thing everything depends on — closes.
Nothing in `help money` ("You may spend past what you have, as far as somebody
will lend you") hints that arrears freeze hiring and opening.

(Also: the HUD and ledger say "den", this refusal says "pence". Inconsistent.)

New "RESTS: ALL": refractory_fireclay (2,395, upkeep 700 vs 600 revenue — a net
LOSS to run), case_hardening (1,764, earns 1,500/yr — obviously good),
arithmetic_positional (still impossible). And two "much" items priced at 63,606
and 88,925 den, which is 25x my annual revenue. The cost curve is very steep.

### Expectation
Start case_hardening only (pays back in ~1.5 yr), then step 4 years without
spending, to climb back to positive capital before the Great Famine (1315-17).
I expect ~+2,500/yr to clear the 9,200 debt by about 1315, and I expect the
famine to cost me ~12% of staff.

## 1317-1318 — out of debt, and the real bottlenecks named

Cleared the debt by 1317 by simply not spending for four years. Total interest
paid: **5,952 den** — more than my entire starting revenue base. Expensive lesson,
and one the game let me walk into without a single warning line.

Once positive, hiring worked again immediately (7.2 artisans). Opened workshop_first
(900/yr) and re-opened patron_local (200/yr — patronage is a subscription, not a
purchase; the patron dying in 1307 makes that vivid).

Note: "scholar" has silently vanished from the hireable list — I think I exhausted
the society's supply with a 0.10 FTE scholar. That is a nice, harsh detail.

The board now shows 350 startable things and the fog's "HEARD OF" list finally
names my two hard blockers:
  * precision_three_plate / met_drop_hammer: "this needs machinists and there are
    none in this society. Teach one: train machinist 2 (about 450 of your own
    hours each, two years)"
  * atomic_theory / statistics_basic: "missing prerequisites: arithmetic_positional"
    — the project I already know is impossible until literacy rises.
  * crude_cell (the voltaic cell — the electricity road) needs lead_metallurgy,
    which costs **89,189 den**. My whole revenue is 7,600/yr.
Also spotted corpus_written: 4,235 den and **6,000 founder-hours over 10 years** —
three full years of my entire life's labour to write down what I know. That is the
best single design idea I have seen in this game.

### Expectation
train machinist 2 + refractory_fireclay + the paper/printing chain (papermaking,
woodblock) — the last on the theory that printing raises literacy, which is what
the hire-refusal told me widens the scribe pool, which is what unblocks
arithmetic_positional -> atomic_theory. That is a three-step inference from
scattered messages; if it is wrong I will have wasted a decade.

## 1321-1323 — the capability ladder appears

Trained 2 machinists (594 den + 900 founder-hours, ready in 2 years), then built
precision_three_plate (3,615 den, 500 hr, 2 yr). Its `why` text is the best
writing in the game: "Two plates lapped together converge on a matched sphere and
socket. Three plates lapped in rotation can only converge on flat."

Building it revealed what the tree actually is: a ladder of *capabilities* —
  cap_heat_1100 "Sustained 1100 C"  (330 den)  RESTS ALL
  cap_tol_100um "Tolerance 0.1 mm"  (660 den)  RESTS ALL
and downstream, glass_clear and cementation_steel both wait on cap_heat_1100.
So the road to a transistor is: temperature ladder + tolerance ladder + chemistry,
and everything else is scaffolding to pay for it. That clicked only at 1323,
23 years in. Under fog I could not have guessed it earlier.

Disappointment: papermaking + woodblock + wire mould did NOT move scribe supply
(still 1,321 hours, same as 1300). My inference about literacy was wrong, or the
effect needs the venture opened and many years, or it needs actual movable type.
The game gave me a lever ("printing, schools and libraries do") and then no
visible feedback on whether I was pulling it. I have no way to inspect
literacy_general at all — there is no command for world values that I can find.

### Expectation
Start cap_heat_1100, cap_tol_100um, bellows_water_blown (all "RESTS ALL"), hire
back the artisans attrition has eaten. Expect the heat rung to open glass_clear
and cementation_steel, and expect a further heat rung (1300 C? 1500 C?) after it.

## 1325 — learning to read the table

Discovery: `available all` is machine-readable enough that the right move is to
dump it and sort by (EARNS - UPKEEP) / COST. Doing that turns up paybacks under a
year all over the tree (tex_rope_walk 0.5 yr, tex_sewing_machine 0.5 yr,
en_breastshot_wheel 0.6 yr, lens_grinding 0.7 yr, tex_water_frame 0.9 yr) sitting
right next to traps (lead_metallurgy: 89,189 den for 900/yr net — a 99-year
payback, and it is the gate on crude_cell, i.e. on electricity).
This is the point where the game stopped feeling like exploration and started
feeling like spreadsheet optimisation. A player who does not think to sort the
table plays a much worse and much slower game; a player who does can print money.

Decision I made on evidence: glass_clear became *available* the moment
cap_heat_1100 was BUILT, before I opened it. So prerequisites count "built", not
"running". I am therefore NOT opening zero-revenue capability works (saves
1,275 den/yr of upkeep). I would like the game to confirm this; nothing does.

### Expectation
Buy a batch of sub-1-year-payback works (rope walk, breastshot wheel, sewing
machine, drawplate, post mill, knitting frame, mechanical clock: 5,026 den,
1,170 hr) to roughly double revenue, then use that to afford cementation_steel
(16,879) and glass_clear (12,482), the two "RESTS ALL" gates.

## 1327-1335 — compounding, a silent failure, and price inflation

Revenue went 7,600 -> 15,000 -> 25,000 as the sub-year-payback batch came online.
auto_open finally started working now that capital is positive, confirming my
guess that arrears disable it. It still opened only some of them.

Three findings:

1. **A project failed and the game never told me.** glass_clear (20% risk) simply
   was not in RUNNING and not in my tech count two years later. No event line, no
   "failed" message anywhere in the step output. I only found out by running
   `why glass_clear` on a hunch and seeing "STATUS: CAN START NOW". I had already
   spent its money. Completions get an event line; failures apparently do not.
   This is the single worst bug-feeling thing I have hit.

2. **Materials are real and can throttle you.** "EVENT 1329: SHORT OF CHARCOAL:
   work running at 54% of plan" for two years. glass_clear alone wants 187,500 kg
   of charcoal. `buy forest 500` -> "cannot afford" (with 21,661 in hand);
   `buy forest 100` cost **27,500 den**, i.e. 275/ha. Coppice is astonishingly
   expensive, which I assume is the point: charcoal is the real limit on
   pre-industrial heat. I liked this a lot. (`quote` only works for mines, though
   — "only mines can be quoted so far" — so I had to discover the forest price by
   being refused twice.)

3. **Prices inflate fast.** charcoal_industrial 63,794 (1331) -> 71,636 (1335).
   lead_metallurgy 89,189 -> 100,152. About 3%/yr. Saving up to afford something
   is partly self-defeating; the game rewards borrowing-free speed. But borrowing
   freezes hiring. That tension is good design and it is nowhere explained.

### Expectation
Restart glass_clear (now 14,016, up from 12,482) plus potash_soda, nitre_beds
(both chemistry roots) and the two hedges the `risk` screen named
(ag2_silage_silo for plague, civ_surveying_groma + fin_marine_insurance for the
war). ~28,000 den of my 40,800. I expect chemistry to be the road to
semiconductors and I expect glass to be the road to vacuum/optics.

## 1338-1343 — supply of *people* is the real tech tree

Two more hard blocks, both about labour supply, both solvable in ways the game
never told me directly:
- glass_clear stalled: "glassblower (wants 2000 hours a year; this society can
  field 1887 at most)". Fix I guessed and which worked: `hire glassblower 2` —
  **employing a trade adds its hours to the market pool** (supply went 1,887 ->
  5,887). Nothing says this. It is the difference between "this is impossible"
  and "this costs 880 den".
- `commission glassblower 2000` bought 2,000 trade-hours for 1,276 den, good for
  one year only. Also never explained outside one line in `help labour`, and it is
  far and away the cheapest way past a labour wall.
- nitre_beds stalled on labourers "booked by your other work" — my own projects
  compete with each other for the same hired pool, invisibly.

Batched 17 works with sub-1.5-year paybacks in 1340; 16 completed by 1342.
1343: 72 techs built, capital 97,907, net +15,900/yr, reputation 80.

The fog list now says the whole next age is gated on trained trades I don't have:
~20 items each saying "this needs engineers/chemists/opticians and there are none
in this society. Teach one: train X 2 (about 450 of your own hours each, two
years)". So the mid-game currency is **founder-hours**, 2,000 a year, and each
trained trade costs 900 of them. That is a good, legible constraint and it is the
first time the game has felt like it is about me rather than about my balance
sheet.

Also seen: `if_punch_and_matrix` "needs 4 trained scholars... build
collegium_licensed (required before the school is legal)", and collegium_licensed
needs `citizenship`. A legal-status subtree I have not touched at all.

### Expectation
Spend 1,800 of this year's 2,000 hours on train engineer 2 + train chemist 2.
Expect that to open the engine/chemistry half of the tree. Expect opticians next
year. I also expect to have to solve arithmetic_positional with
`commission scribe 2500` — the trick I just learned on glassblowers.

## 1346-1349 — electricity, at a ridiculous price

Bought lead_metallurgy for **132,416 den** because it is the only gate on
crude_cell. Then read crude_cell:
  "A poor cell, and you can have it on arrival... COST: 273.1 d, 120 hours."
So the copper-iron brine cell costs 273 den and its prerequisite costs 132,416.
The flavour text explicitly says you could have it on arrival. That is the
sharpest mismatch between what the game *says* and what it *charges* that I have
met. (I understand the argument — you need worked lead before you have a
controllable electrochemistry industry — but the text undercuts the gate.)

Trained engineers, chemists, opticians (2 each, 900 founder-hours each pair).
Built freedman_staff (9,350 den, +8 artisans; the text is careful and pointed
about manumission being both the ethical and the efficient answer, which is the
best-written thing in the game after the three-plate method).

Housing was the binding constraint before that: "you can supervise, house and
teach 0.00 more people - you have no room for even one."

Black Death hedging worked and was legible: after soap_hard + ag2_silage_silo the
`risk` screen moved "staff loss: you take 100% of it" -> "81% (softened by hard
soap, in quantity, fodder that keeps through a bad winter)" and projected loss
45% -> 36%. That is exactly the right feedback loop, and it is the only place in
the game where I could see a decision change a number before it happened.

Still unsolved after 49 years: **arithmetic_positional**. It has been sitting at
81% since 1309 wanting 2,500 scribe-hours/yr against a national ceiling of 1,321.
`hire scribe` is capped at 2.2 by literacy; `commission scribe 2600` -> "the
scribes here can spare 1321 more hours this year, not 2600". It gates
atomic_theory and statistics_basic. I have no idea how to raise literacy and the
game has told me only "printing, schools and libraries do" — the school
(if_punch_and_matrix / collegium_licensed) needs `citizenship`, which I have never
seen offered. This is my biggest open frustration.

## 1352-1364 — the grind, and the shape of the mid-game

The loop has settled into: read "MOST RESTS ON THESE" -> start those -> dump
`available all`, sort by payback -> start every earner under ~2 years payback ->
`train <trade> 2` whenever the fog says a trade is missing -> `step 3` -> repeat.
By 1364: 119 techs built, 47.6 staff, capital 133,435, net +23,548/yr, rep 94.

Things I noticed in this stretch:
- Founder-hours (2,000/yr) are now the only real constraint. Money accumulates
  faster than I can spend hours designing things. A trained trade costs 900 hours;
  a big node costs 500-800. So a year is about two or three decisions.
- The cost curve of the "material" nodes is brutal and, I think, deliberate:
  mat_copper is **324,519 den**, of which 194,400 is just buying copper.
  `quote mine copper 500` -> sink 132,000, then 30,250/yr forever, 3 years before
  it produces. Owning the mine is the alternative to paying the market. This is
  the most interesting economic decision the game has offered and I only found it
  because `help economy` mentioned `quote mine coal 500` in passing.
- `quote` works for mines only. There is no way to ask the price of anything else
  before committing (forest, commission, bounty).
- Knowledge risk: 44 technologies "at risk" is displayed every turn, but `risk`
  says "no remaining hazard for this civilization sacks a site, so nothing here is
  currently at risk of being forgotten". So the AHEAD line on the main state
  screen is alarming about a thing that cannot happen in England. That is a
  persistent false alarm and it made me consider corpus_written (6,000 hours) for
  no reason.

### Expectation
Buy finery_puddling (159,221 -> 9,000/yr, "RESTS much" and the gate on puddled
iron and rails), plus thermometer and prc_milling_machine. I expect puddling to
open the iron/steel/rail branch and the thermometer to open temperature-controlled
chemistry, which is where semiconductors have to come from.

## 1378-1385 — a bug that cost me my workforce

Chain of reasoning that led here: 57 of my finished works were sitting unopened
because "people free to run something new: craftsmen: 0", and `hire artisan`
refused with "you can supervise, house and teach 0.00 more people". The refusal
text itself suggests "buy slaves N then manumit, though they are untrained for
three years", so I did exactly that — twice (10, then 20; ~12,750 den), and
manumitted both batches immediately (reputation went up 3 points each time, which
is a nice touch).

What actually happened:
  `labour` -> "IN TRAINING: None x15.7, ready 1384.0"
The freed people are training into a trade literally named **None**. When the
training completed they did not appear on the staff list at all — they simply
vanished. And my artisan count collapsed from 34.6 (1381) to 6.1 (1384) to
**3.8** (1385). I appear to have lost roughly thirty artisans and 12,750 den by
following the game's own printed advice.

I cannot tell from inside the program whether the artisans were converted into the
"None" trade and then deleted, or whether something else ate them, but the timing
is exact and nothing else changed. This is the clearest defect I have found.

## 1385-1397 — the capability ladders, and where the real tree is

Once I stopped chasing revenue and searched `available find cap_`, the actual
spine of the game showed itself. It is four ladders:
  cap_heat_*   1100 C -> 1600 C ...
  cap_tol_*    1 mm -> 0.1 mm ...
  cap_vac_*    1 torr -> 1e-3 torr ...
  cap_pure_*   99% ...
plus measurement nodes (cap_measure_temp, _mass_mg, _time_s) that cost **0 den and
0 hours** and which I had been ignoring for 85 years because they sat at the
bottom of the "cheapest six" list looking like junk. Three free techs, one of them
marked "RESTS: much". That is a real discoverability failure: the game's own
summary screen buries its most important cheap nodes under a "cheapest" sort.

By 1397: 156 techs, capital 378,934, net +45,707/yr, voltaic_pile built,
Sprengel pump and 1e-3 torr vacuum built, 1600 C built, copper refined
(324,519 den, the single biggest cheque I have written).

Staff has never recovered from the manumission bug: 20-odd people, capacity
pinned at "0.00 more". I have worked around it entirely with `commission`
(4,000 artisan-hours for 845 den, one year) which is so cheap relative to hiring
that I now think commission is strictly better than employment for project work,
and staff only matter for *supervising open concerns*. If that is intended it is
not signposted; if it is not intended it is an exploit.

## 1430-1438 — the literacy lock finally opens

At 1430 the fog list turned into a wall of "needs 4 / 5 / 6 / 50 trained scholars,
you have 3.2" and `hire scholar` said "this society's literacy will not supply
more than 2.7 scholars in total, ever, at any price". Same wall as the scribes in
1309, 120 years earlier.

The key turned out to be the **printing chain**, which I finally built as a block:
prn_type_punch + mt2_type_metal + if_type_mould + hom_printed_books +
sc2_institution_textbook + sc2_method_lab_notebook (about 880 founder-hours,
~7,400 den total — trivial money).

Result in eight years: scholar supply went from 2.7 people / 1,321 scribe-hours to
**30 employed and 67,464 hours available**, and `available` went from ~350 items
to **897**. That is the single largest state change in the whole run, and it cost
almost nothing. I had the information to do it in 1318 (the hire refusal literally
says "printing, schools and libraries do") and I did not connect it, partly
because papermaking and woodblock alone visibly did nothing, which taught me the
wrong lesson.

Also noticed: my founder-hours have quietly risen from 2,000 to 3,730/yr. Nothing
ever announced this or explained it. I assume reputation or the institutions buy
me assistants, but the HUD just changes number.

Endgame road is now legible:
  newtonian_mechanics -> em_theory -> quantum_solidstate_theory -> (transistor)
plus thermodynamics_theory, electroplating, and the cap_* ladders.
