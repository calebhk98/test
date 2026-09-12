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


