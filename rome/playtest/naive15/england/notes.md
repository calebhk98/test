# England playtest notes (naive15)

Player: Claude (playing blind, no source reading). Civ: England under Edward I, 1300.

## Setup

- Game is a CLI menu/text simulator. `python3 rome/sim/simulator.py`.
- Main menu: New game / Load / Options / Quit.
- Choosing New Game gives a "WHERE, AND WHEN" choice of 5 civ/era starts:
  Han Empire 100AD, Rome under Trajan 100AD, Viking Scandinavia 900AD,
  England under Edward I 1300AD, Mexica Triple Alliance 1500AD. Each has
  population, "state capacity" (0-1), and a price multiplier relative to Rome.
  I picked England (#4) as instructed.
- Premise (from the title screen): "ONE PERSON, AND EVERYTHING THEY KNOW" —
  you are a single modern person dropped into a pre-industrial society with
  full knowledge of how modern tech works, but none of the infrastructure.
  You start with ~enough money to eat for a few months, no employees, no
  slaves. The framing is explicitly: knowing how something works is free,
  building it costs your own hours, other people's hours, money, materials,
  and time.
- England blurb: 4.5M population, real legal system, chartered towns,
  universities, parliament starting to assert itself on taxation. Tech
  visible: watermills/windmills everywhere, horse collar, crank, spinning
  wheel, blast furnace "arriving", mechanical clock "about to" arrive,
  double-entry bookkeeping in Italian merchant houses, paper, spectacles,
  compass, gunpowder (known but not useful yet). Explicitly the most
  mechanically advanced start in the game. Missing: cheap iron / furnace
  temperatures for steel.
  Also explicitly flagged: the game knows future history the character
  doesn't control — 15 years to Great Famine, 48 years to Black Death
  (kills 1/3-1/2 of population). This is clearly meant to be a real
  planning constraint, a doom clock.

## Fog of war choice

Asked Y/n, defaulting to Y (fog of war ON). Description: with fog on you
see only what you've built / can start now (one-line summaries) / things
heard of but can't start; can't see where anything leads. Off = full tech
tree visible, plan routes. EXPLICITLY IRREVERSIBLE per-save: a fogged save
can never become unfogged, and an unfogged save is already "spoiled" so
can't be refogged. This is a real, permanent choice the game warns you
about clearly, which is a good sign of thoughtful design.

Decision: keeping fog of war ON (default), since that's how someone
encountering this world blind would actually experience it, and it matches
the spirit of "figure it out from the game itself" that I've been asked to
do.

## Remaining setup choices (all defaults)

- Starting wealth: default "poor_scholar" (400 den base -> 440 pence in
  England at 1.1x Rome prices). Currency here is called "pence", scaled
  relative to Rome's "denarii" system for balancing across civs - a nice
  implementation detail, shows the game normalizes prices across very
  different starts.
- Mortality: default N (founder does not age/die). Game explains this is
  because the flagship goal (transistor) takes >142 years and can't fit a
  human lifespan; not aging "measures the tree". Can turn ON later via
  'options' but never back off. Took this at face value and left default.
- Goal: 17 possible goals shown, from "Establish experimental science"
  (closure 1, floor 2y, lifetime-scale) up to "Grown and alloy junction
  transistors" (closure 168, floor 142y, civilisation-scale, THE default
  and flagship goal). Picked the default (transistor) to see the game's
  main intended arc, understanding I likely won't finish it in one
  session - "closure" seems to mean number of prerequisite
  techs/achievements needed first, "floor" = minimum possible years even
  with perfect luck.
- Horizon (deadline): Challenge 400y / Standard 500y (default) / Relaxed
  650y / Endless / exact number. Took default Standard (500 years).
  Difficulty here is explicitly ONLY about how much calendar time you get -
  costs and odds don't change. Good, unusually honest framing of
  "difficulty".

## [1300 AD] Game has started

Status bar format: `[1300 AD | 440 pence | you:2000 hr | sch 1 art 1 | rep 5] >`
- 1300 AD: in-game date (starts at year granularity apparently, or at
  least displayed as year).
- 440 pence: money.
- you:2000 hr: my own labour-hours available (per year? per turn/"step"?
  unclear yet - 2000 hr/year is roughly 40hr/week * 50 weeks, a plausible
  calendar-year labour budget, so I suspect "step" = 1 year and this is
  my personal hour budget for that year).
- sch 1 art 1: unclear yet - maybe "scholarship 1, artisanship 1" skill
  levels, or building counts (1 school, 1 workshop?). Need to check via
  'state'.
- rep 5: reputation, presumably.

The game told me the 5 starting commands: state, available, why <name>,
start <name>, step. Plus: stuck, quit, help (with topics: commands, labour,
economy, money, automatic, sittings, fog, eminence, risk, protection,
stuck, log), options.

Game autosaves after every command to
/root/.rome-saves/england_1300_4.json and can be resumed with
`python3 rome/sim/simulator.py play --session <path>`.

## Technical note on playing this (not about the game itself)

The game is a blocking stdin/stdout REPL, no non-interactive mode. To play
turn-by-turn from this tool environment I had to background the process
with its stdin attached to a FIFO opened in read-write mode (`<>` in bash,
not plain `<`) so the open() call doesn't block; a plain blocking `<` open
raced with a later attempt and I ended up with TWO simulator processes both
reading the same FIFO and both writing (truncating) the same log file,
which produced garbled/duplicated output for a few turns before I noticed
via `ps aux` and killed the strays. Lesson for next time: launch once,
verify with `ps aux | grep simulator` that exactly one process exists,
before trusting the log.

## [1300-1306 AD] First moves: foundations, and a debt spiral

Explored `help commands`, `help labour`, `help money`, `help economy`,
`help automatic`, and `policy` before acting, to understand the systems.
Key mental model I built:
- You have a personal "practice" (mine: medicine - cataract couching,
  trepanation) that earns passive income every year for free, forever,
  whether or not you do anything else. It's explicitly worth about 1/3 of
  what an "organised concern" doing the same trade would earn.
- "Projects" (the tech tree nodes) are bought with a mix of your own
  founder-hours (2000/yr, do not carry over), hired labour-hours (bought
  from the local labour market, which has a supply ceiling per trade!),
  materials, and money. Money for a project is not charged all at once at
  'start' - it draws down over the project's calendar-floor duration, at
  whatever pace your cash and the labour market allow. If you don't have
  the cash, you go into debt automatically (12%ish interest) rather than
  the project just stalling - UNLESS a hard credit ceiling is hit.
- Once "built", a tech is permanently yours (a technology, contributes to
  score/goal) but doesn't cost/earn anything unless it's also an economic
  "concern" that you separately 'open' (which then has its own ongoing
  upkeep/revenue and staffing-to-keep-open requirement).
- Idle founder-hours can be sold via `work <trade> <hours>` for wages, but
  this comes out of your practice time (you "cannot be in two places"), so
  net gain is smaller than gross wage. Still clearly worth doing whenever
  you have hours a project isn't using.
- auto_open policy: opens concerns that plainly pay for themselves. I
  turned it on early; it correctly left scientific_method (earns 0, costs
  110/yr) closed, matching its own description exactly.

MISTAKE / DEAD END: I started three expensive tier-0 "foundation" projects
in quick succession (scientific_method 242p, treadle lathe 275p, then
arithmetic_positional 968p AND units_standards 415p together) because each
one's `why` said "HOW MUCH RESTS ON THIS: almost everything" and I wanted
to unblock the tree fast. This was too aggressive for a starting capital of
440 pence: by 1303 I was at -975 pence with interest on arrears eating
~115 pence/yr, more than my entire practice income, and the log started
reporting the project "in arrears: after fixed costs there is nothing left
to draw on, so the hours offered this year did almost nothing" - i.e. the
debt was actively STALLING the very project it was borrowed for. That's a
real, well-modelled debt trap, not a bug, but it cost me about 4 in-game
years (1303-1307) of just grinding `work scholar 2000` every year to claw
back to solvency, doing nothing new. Takeaway I'd tell a new player: price
out your OPENING SEQUENCE in total before committing, not project-by-project
- "almost everything rests on this" is true of several things at once near
the root of the tree, and the game will happily let you stack them into a
debt spiral even though none of the individual `start` commands looked
reckless on their own. I'd also tell the designers: consider whether the
game could warn more loudly ("this combination will likely put you in
arrears next year") - the per-project credit forecast IS shown at start
time (it's actually quite good: it literally told me "you would borrow: 968
... you would then owe: 1,027" before I committed), so in fairness the
information was there and I just didn't add up two such forecasts together
before acting. This is my own planning failure, clearly flagged by the
game's own UI in retrospect - not a design gap.

By working `scholar` hours for four straight years (net ~+300/yr each time)
while stepping, I got from -960 pence back to +169 pence by 1308, and both
scientific_method and arithmetic_positional and units_standards had already
finished and are permanent technologies (4 total built by me, plus the
starting 130-131 "free" ones granted by the setting). arithmetic_positional's
completion changed two named society-wide values: literacy_elite,
state_capacity - so completions visibly move the simulated society's
characteristics, not just my personal tech list. Also noticed a recurring
flavour/hazard line every couple of years: "fire in the thatched lanes
behind the market: it destroyed nothing, because you were holding none" -
looks like a periodic hazard roll that would matter once I own property/
mines/workshops, currently a no-op because I own no physical assets yet.

## [1308-1320 AD] Recovering, then a repeatable loop

Strategy that worked, and that I kept repeating: get solvent by spending
ALL idle founder-hours on `work scholar 2000` for a year or two (nets
roughly +300/yr even after the opportunity cost to my own practice),
THEN spend the resulting cash buffer on one or two new `start`s, THEN
step and repeat. This alternation avoided ever hitting the hard credit
ceiling again.

Opened my first economic "concern": fin_pawnshop (958p to build, then
earns ~300/yr, costs 50/yr upkeep). Learned auto_open did NOT open it
automatically even though it "plainly pays for itself" once built - I had
to `open fin_pawnshop` by hand. Not sure why auto_open skipped it (maybe
auto_open only fires on the SAME step something finishes, and I noticed it
one step late; or maybe the 0.2-artisan-to-keep-open requirement matters
and auto_open is cautious about staffing it without me confirming). Worth
a design note either way: the policy's own description ("opens concerns
that plainly pay for themselves") did not visibly match what happened here.

After opening it, `state` warned "Pawnshop and secured loan is within 1.3
craftsmen of closure" - reads like an urgent threat, but hiring one smith
(248 pence/yr wage) moved the number the WRONG way at first glance (1.3 ->
2.3, i.e. it went UP after I added staff), which confused me for a minute.
On reflection I think bigger = safer here (more headroom before an
auto-closure threshold), so the wording "within N craftsmen of closure"
means "N more craftsmen would have to leave before this closes", and
hiring one added exactly one unit of headroom (1.3 -> 2.3). If that's
right, the phrase reads a little ambiguously on first encounter - it could
as easily be read as "getting close to closure, 1.3 away" being BAD news
which is what worried me into hiring somebody I may not have needed yet.
I never did see it actually close, so I can't confirm which reading is
correct from observed behaviour alone.

Discovered the local labour market has hard per-trade supply ceilings I
compete against, not just against my own project queue: several projects
(arithmetic_positional, then later geometry_analytic) reported "this
society can field 1321 [scribe hours] at most" and crawled at that pace
regardless of my cash or founder-hours. This is a genuinely interesting
constraint - knowledge doesn't buy you infinite scribes on day one, the
economy has to have the capacity. 'labour scribe' confirmed: "HEADCOUNT
CEILING: 2.3 scholars in total, ever, at any price" for MY hiring pool
specifically (separate concept from the town's raw hour supply), rising
with printing/schools/academies.

By 1320 (20 years in): 8 technologies built (scientific_method, treadle
lathe, units_standards, arithmetic_positional, pawnshop, statistics_basic,
algebra_symbolic, geometry_analytic), 1 concern open and earning, 1 smith
hired, net income stable and positive (+28.7 pence/yr recurring), "on the
road" counter for the transistor goal at 17. Survived the Great Famine
(1315, exactly as the opening text promised - nice touch) with apparently
no visible staff loss logged (I have very little staff to lose yet).
`risk` showed a remarkable full historical event timeline for England
baked into the scenario, all the way out to the World Wars, each with its
own staff-loss/sack-chance percentages and a list of techs that would
mitigate it - genuinely impressive scripted breadth for a text sim.

## [1320-1346 AD] The iron/agriculture push, and a second, worse debt spiral

Built met_bloomery_bog_iron (iron smelting - directly answers the
England intro's "what is missing: cheap iron"). Opened it as a concern:
420/yr. Then en_breastshot_wheel (a water-mill, 800/yr). Both together with
the pawnshop pushed recurring net income from +28/yr up past +300/yr, which
let me afford proper staff for the first time (hired a second smith, then a
scholar).

Ran into a SECOND, bigger debt spiral around 1336-1339: I fast-forwarded
with `step 3` instead of stepping one year at a time (to save my own time,
not the character's), and in that gap: the Hundred Years War started
(scripted, historical, right on schedule for 1337) and cut trade/output to
88%, my newly-trained engineer sat idle costing 688/yr wages with nothing
to do, and interest compounded - by the time I looked again capital was
-1,877 and recurring net was -757.5/yr. LESSON: multi-year `step N` is
efficient but blind - if something like a war or a market shift lands
inside the skipped span, you only find out after the fact and after
several years of unseen compounding damage, rather than being able to
react year 1. I'd tell the designers this is probably fine/intended (real
history doesn't pause for you either), but it's worth flagging that a
player optimizing for their OWN time (as I was, trying to cover more
calendar in fewer commands) is pushed toward exactly the play style
(multi-year blind stepping) that the debt-and-arrears system punishes
hardest. Recovered by firing the idle engineer (cut -688/yr immediately)
and grinding `work scholar 2000` for several years.

Started crop_rotation (Legume rotation / three-field system) once solvent
again - a 6-year-floor, 3,104p project, deliberately chosen for its huge
quoted revenue (2,300-3,900/yr). This put me into a THIRD debt spiral
(pace-limited at 517p/yr, so it dragged the whole 1336-1343 stretch), but
it was worth it: once open, it alone earns 3,000/yr against 800 upkeep.

Then the Black Death landed, 1348-1350, again exactly on the schedule the
game told me on day one (15/48 years - I'm now 48 years in). Effect: "staff
-38%, 898 gone with the trade that stopped. Empire-wide population -45% -
wages stay dear for roughly the next 150 years". All three of my open
concerns immediately flashed "has no spare craftsmen: losing just one more
closes it outright" - a real, sudden crisis that took immediate hiring
(hire smith 3) to avert losing ~2,780 pence/yr of income in one stroke.
Also: for the first time a random "fire in the thatched lanes" hazard
actually cost me money (277 pence) instead of the "destroyed nothing,
because you were holding none" I'd seen a dozen times before - the flavour
text is genuinely load-bearing, not decorative; it only bites once you own
something exposed to it.

Learned that HIRING (unlike starting a research project) needs cash IN
HAND right now, not credit: `hire smith 2` was flatly REFUSED with
"costs 495 pence in advance and you have -1697" while I was in debt, even
though my credit limit had lots of headroom. Projects can run you into
debt automatically; adding staff cannot. Distinct rule, easy to miss, and
it bit me right when I most needed to hire (mid-crisis, no cash) - had to
grind wages first, then hire.

By 1350 the economy had genuinely transformed: revenue 4,411 pence/yr
across crop_rotation (3,078), the water wheel (821), the bloomery (431),
the pawnshop (308) and my own practice (239), against upkeep+wages+living
costs of roughly the same. 15-16 technologies built.

## [1350-1355 AD] Hit a real structural wall: the literacy ceiling

Built identity_cover and patron_local (both "HOW MUCH RESTS ON THIS:
almost everything", both pure standing/political unlocks with 0 revenue)
specifically because newtonian_mechanics turned out to be gated behind
them: trying to `start newtonian_mechanics` was flat REFUSED with "the
state is wary of this (state interest -1.0); get at least a local patron
first" - a political/social prerequisite that fog hadn't shown me until I
had enough scholars to actually attempt the node. That was a genuine
surprise: I assumed prerequisites were purely technical (other techs) but
some are about your STANDING in society, checked separately from the
tech-tree dependency graph.

Got newtonian_mechanics built (1353) by hiring a 3rd scholar (had to fire a
smith first purely to free a household-capacity slot - "household places:
6.0 of 6.0 used" is a hard cap on live-in staff separate from the labour
market's own per-trade ceiling). Checked `why em_theory` (the next node,
clearly on the path toward the goal: em_theory -> quantum_solidstate_theory
-> presumably the transistor eventually) and hit a wall that isn't about
money at all: "needs 4 trained scholars, you have 3.0 ... literacy here
will never let you HIRE more than 2.2" - i.e. I am at, or very near, the
hard ceiling on how many scholars this whole KINGDOM can supply me, at any
price, given current literacy. The only way past it is `school_founded`
(12,650 pence, 4-year floor, "CALENDAR FLOOR is set by diffusion, not by
construction: the economy needs roughly a generation... money cannot buy
this down") or other literacy-raising tech (printing, paper, libraries).

This is where I stopped: 1355 AD (55 years into a 500-year run), 17
technologies built by me (148 total with the free starting set), a
6-concern economy grossing ~4,400+ pence/yr, 3 scholars + 3 smiths on
staff, reputation 11.4, and a clear, concrete, well-explained next
objective (save ~12,650 pence and 4 calendar years for school_founded)
that the game itself pointed me at rather than leaving me guessing.
Session state is autosaved at
/root/.rome-saves/england_1300_4.json and resumable with
`python3 rome/sim/simulator.py play --session /root/.rome-saves/england_1300_4.json`.

======================================================================
# FINAL SUMMARY - how far I got, what stopped me, what I'd change

## How far I got

Played from the main menu through full setup (England/1300 AD, fog of war
ON, poor_scholar start, mortality off, goal = the flagship "Grown and alloy
junction transistors", Standard 500-year horizon) to **1355 AD, i.e. 55
years of a 500-year run**, entirely through the game's own text interface,
no source reading.

End-of-session state:
- 17 technologies built personally (148 total counting the 131 granted
  free at setup)
- 6 open economic "concerns": a pawnshop, a bloomery iron works, a
  breastshot water wheel, a three-field crop-rotation farming system, a
  respectable cover identity, and a local patron - plus my starting
  medical practice
- Recurring revenue around 4,400+ pence/yr, roughly breakeven net at the
  moment I stopped (had just spent down cash hiring a third scholar)
- Staff: 3 scholars (counting myself) and 4 craft hands (myself + 3
  smiths)
- Reputation 11.4, protection 31%, scandal 0.42 (safely under the danger
  threshold of 25), eminence 0.13
- Survived, on schedule, both historical hazards the game told me about on
  day one: the Great Famine (1315) and the Black Death (1348-1350, which
  cost me 38% of staff and forced emergency hiring to save three concerns
  from auto-closing)
- Currently mid-way along what looks like the correct physics spine toward
  the goal: scientific_method -> arithmetic_positional -> geometry_analytic
  -> algebra_symbolic -> calculus -> newtonian_mechanics (built) -> em_theory
  -> quantum_solidstate_theory (both still ahead)

## What stopped me

Two things, one practical and one structural:

1. **Practical**: this was a long, deliberately-paced playtest and I chose
   to stop at a natural checkpoint rather than push further, once I'd
   exercised most of the game's major systems (research, concerns/
   businesses, hiring/firing/training, debt and credit, scandal/eminence/
   protection, the labour-market supply ceiling, household-capacity caps,
   scripted historical hazards, political/standing-gated prerequisites,
   and the scoring rubric) and had solid, representative notes on each.

2. **Structural, and this is the real "stopped here"**: the next node on
   the path to the goal, em_theory, is blocked not by money or by my own
   founder-hours but by a hard **literacy ceiling** - "you have 3.0
   [scholars], literacy here will never let you HIRE more than 2.2" - i.e.
   Edward I's England, at its current state of literacy, cannot supply me
   a 4th scholar at any price. The only way past that is school_founded
   (12,650 pence, a 4-year floor set by "diffusion, not construction" that
   money cannot buy down) or other literacy-raising tech. That's a
   genuine, well-telegraphed economic/demographic wall, not a bug or a
   dead end - the game clearly wants you to go build the big, slow
   institutional project next. I stopped right at the point of taking that
   decision, having banked enough understanding of the economy to know it
   was achievable (my income comfortably covers it within a handful of
   years of saving) but not yet having spent the in-game years to get
   there.

I never hit a hard game-over, was never denounced for scandal, never had
a concern actually close on me (came close twice - "no spare craftsmen,
losing just one more closes it outright" - and both times caught it with
emergency hiring in time), and never ran past the credit ceiling.

## What I'd tell the people who made it

**What works very well:**
- The economic model is genuinely coherent and forces real trade-offs:
  every "start" has a visible calendar floor, hour cost, money cost,
  failure risk and (crucially) a pre-commitment credit forecast that
  literally tells you "you would borrow X, you would then owe Y" before
  you commit. I made debt-spiral mistakes anyway, but every single time
  the information to avoid them had already been shown to me - that's
  good, honest design, and my mistakes are on me, not on missing
  information.
- The historical hazard timeline (`risk`) is remarkable - the Great
  Famine and Black Death landed on their real historical years, with
  believable, sourced-feeling effects (staff loss, wage inflation lasting
  "150 years"), and dozens more scripted events run out to the World Wars.
- The "why <id>" screen is excellent and almost always sufficient to
  decide whether to build something, including flavour text that
  frequently explains WHY something is hard (e.g. scientific_method:
  "the hard part is not stating it, it is displacing Aristotelian
  authority... their defenders hold the chairs, the patronage and the
  medical guild").
- Small mechanical touches that reward attention: the labour market has
  real per-trade supply ceilings independent of your own money/hours; a
  trade you teach into existence has nobody able to do the work until
  someone is actually trained in it; household capacity is a separate
  hard cap from the labour market; opening a concern ramps up over 3
  years rather than snapping to full revenue; staff attrition (~3.5%/yr)
  is modelled as continuous FTE decay, not discrete deaths, and is
  explained as such when you ask.

**What confused me, or cost real time to work out:**
- `auto_open` did not open my first profitable concern (the pawnshop) even
  though its own description says it "opens concerns that plainly pay for
  themselves" - I had to notice and open it by hand. I never found out why
  (didn't dig into source, as instructed), but the discrepancy between the
  policy's stated behaviour and what I actually observed is worth a look.
- The "X is within N craftsmen of closure" warning is ambiguous on first
  read. After hiring more staff the number went UP (1.3 -> 2.3), which
  read at first like the situation getting WORSE before I worked out
  (never fully confirmed) that bigger = safer here. A rephrase like "N
  craftsmen of headroom before closure" would remove the ambiguity
  outright.
- Some prerequisites are political/social (state approval, needing a
  patron) rather than technical, and under fog of war you only discover
  this by trying to `start` the node and getting refused, not from
  anything shown beforehand in `available` or `why` for the blocking
  patron item. That felt like a real "how was I supposed to know that"
  moment, though I recognize under fog SOME things must stay hidden by
  design - maybe `why` on the blocked node itself could hint at a
  political gate the way it already hints at missing technical
  prerequisites.
- Multi-year `step N` is efficient (fewer commands) but genuinely
  dangerous: a scripted event (the Hundred Years War, in my case) landed
  inside a skipped span and I only discovered the resulting debt spiral
  well after the fact, several years of compounding interest later,
  rather than at the moment I could still have reacted. I don't think
  this needs fixing (real history doesn't pause), but it's worth the
  designers knowing that the game currently nudges an efficiency-minded
  player toward the play style its own economy punishes hardest.
- Hiring staff requires cash on hand and is flatly refused during debt,
  even with unused credit headroom, while STARTING a research project
  will happily borrow against that same credit automatically. Two
  different rules for what looks like the same kind of spending; consistent
  once you know it, surprising until you hit it (right when it hurts most
  - mid financial-crisis, unable to hire the staff that would fix the
  crisis).

**What I wanted to do and couldn't (yet):**
- Get a 4th scholar to unblock em_theory - genuinely can't, not a
  UI gap, just where the run currently stands (needs school_founded or
  equivalent literacy tech first).
- I was curious what `path <goal>` and `available fewest_missing` would
  show with fog off, and what the full tech tree looks like, but did not
  turn fog off or peek - stayed inside the constraint as asked.
- I noticed a `bounty <id>` command (pay someone else to solve a problem)
  advertised on at least two "why" screens (met_bloomery_bog_iron,
  case_hardening) but never had a concrete reason to use it in this
  session - would be worth a dedicated playtest of its own.

**Overall**: this is a dense, honest, well-explained simulation. Nothing I
hit felt actually broken; the few things that confused me were either
information that existed and I didn't connect (my debt spirals) or minor
wording ambiguities (the craftsmen-of-closure phrasing) rather than
missing functionality. I would happily keep playing this - the literacy
ceiling I stopped at is a compelling, legible obstacle, exactly the kind
of "now go build the big slow thing" beat a good long-form strategy game
should produce around the 50-year mark of a 500-year run.


