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
