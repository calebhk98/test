# Norse playtest notes (naive15)

Playing as: Norse, Scandinavia 900 AD, fog of war ON, mortality OFF, goal = default
(Grown and alloy junction transistors, closure 168, floor 142y), horizon = Endless.
Starting kit: poor_scholar (560 hacksilver locally, quoted as 400 den in Rome prices x1.4).

## [900 AD, turn 0] Setup impressions

- Main menu -> New game -> civ/era choice. Picked "Scandinavia in the Viking age, 900":
  small pop (1.5M), state capacity 0.15, prices 1.4x Rome. Flavour text frames it as the
  opposite problem to Rome: no state to stop you, but also no state to fund you.
- Fog of war toggle: framed clearly - with it off you see the whole tech tree and can plan
  a route; with it on you only see what's buildable now or rumoured. It's a one-way,
  un-resettable choice (can't turn off later, same as mortality). Went with fog ON (default)
  since that's how someone would play blind the first time.
- Mortality toggle: off by default, framed explicitly as "measures the tree, not a lifespan
  lottery" - can be turned on later but not off again. Left off.
- Goal selection: big menu of 17 possible end goals, each with "closure" (# of
  prerequisite techs) and "floor" (minimum possible years even with luck). Default is the
  full transistor chain (closure 168, floor 142y). Interesting design: you could instead
  aim for something much smaller like "establish experimental science" (closure 1, floor 2y)
  as a real, separate win condition. Kept the default transistor goal since mortality is off
  and I have unlimited time to explore.
- Horizon (deadline): chose Endless (no deadline) - default given mortality off. The game
  explicitly says difficulty ONLY changes the calendar, not costs/odds.
- Game auto-saves after every command to a session JSON file, and tells you the exact
  resume command up front. Good: means I never need to manually save.
- Starting status line format:
  [900 AD | 560 hacksilver | you:2000 hr | sch 1 art 1 | rep 5] >
  Guesses: currency=hacksilver (matches "no coinage anybody trusts" flavour, i.e. silver by
  weight, not coin). "you:2000 hr" = my own labour-hours available (per year?). "sch 1 art 1"
  unclear yet - maybe scholarship/artisan skill level 1 each? "rep 5" = reputation, probably
  out of some max. Will check with 'state' and 'help'.

## [900-919 AD] Core loop, and a self-inflicted debt spiral

Commands confirmed by playing: 'state' (full status), 'available' (everything startable now,
233 things at turn 0!), 'why <id>' (full card on one project: cost, hours, calendar floor,
risk, staff, prerequisites, "how much rests on this"), 'start <id>' (commit to it), 'step'
(advance a year, or 'step N' for N years), 'stuck' (advice when nothing is happening),
'money' (ledger), 'ventures' (things completed but not yet 'open'ed), 'labour'/'hire'/'work'
(the labour market), 'risk' (hazard timeline), 'help <topic>' (essential, the game expects you
to read it).

"sch 1 art 1" = my own labour counted as 1.0 scholars + 1.0 craftsmen (artisans), which is
what 'why'/'start' test a project's staff requirement against. Confirmed by 'state': "counting
yourself and hours you have bought". "rep 5" = reputation (starts 5, a soft currency of trust
that also rises/falls with completions and scandal).

First moves: picked scientific_method (280 hacksilver, "almost everything" rests on it) and
units_standards (683.8, also "almost everything") as the two cheapest tier-0 foundation nodes,
started both turn 0-1. Both COMPLETED within ~1 calendar year (even though scientific_method's
own card said "CALENDAR FLOOR: 2 years" - it finished in 1; not sure if that's the minimum with
luck, i.e. the floor really is a floor and it can go faster, or if I'm misreading the calendar).
Completing something does NOT make it earn or cost anything - you have to 'open' it separately,
and 'ventures' showed both would cost upkeep (140/yr and 42/yr) for 0 revenue if opened, so I
left them unopened. Confusion #1, resolved in a few minutes: starting a project shows a COST
in hacksilver and a separate YOUR HOURS figure; the cost is not paid all at once, it is drawn
down year by year as your hours (and any hired trade's hours) are spent on it - 'state' shows
"X% of your hours spent, Y still owed" while it's running.

MISTAKE / DEBT SPIRAL (this is the important one): I started a third project,
arithmetic_positional (1,120 hacksilver, "ALL" rests on it, 450 of my hours, 1yr floor),
immediately after the first two, while already short on cash, using the game's offer of
credit without thinking about the interest. The game is explicit that credit is a forecast,
not automatic doom ("nothing is borrowed yet... this is what happens if cash runs short"),
but I did not appreciate how punishing 12% annual interest on arrears is when your baseline
income barely covers living costs. Within about 4 years (900->906) I went from +560 to -1,519
hacksilver, net recurring income went from +3.4/yr to -160/yr, because interest on a ~1,300
debt (~150-180/yr) dwarfed my entire practice income (332/yr) minus living costs (314/yr) -
i.e. there was essentially NO slack to pay debt down, so the debt fed on itself. It also
stalled the project itself: a note appeared ("in arrears: after fixed costs there is nothing
left to draw on, so the hours offered this year did almost nothing") meaning being in debt
doesn't just cost money, it also stops your own projects progressing, because the hired-labour
share of the cost can't be paid for.

THE WAY OUT, and a genuinely good piece of design: at year 914, 8 years into arrears, the game
itself printed an unmissable warning:
  "!! YOU HAVE BEEN IN ARREARS 8 YEARS AND YOU LOSE 65 IN HACKSILVER A YEAR, SO NOTHING YOU
  START WILL EVER BE PAID FOR"
and then gave the exact fix: "work as a scholar: 2000 of your own hours ... would bring in
about 541 ... so you are up 307. Nobody has to lend you anything for that." I had in fact
already discovered 'work <trade> <hours>' a few turns earlier by reading the command list, and
was using it - so this confirms that "sell your own hours for ordinary wages instead of research"
is the intended, in-game-taught answer to a cash crunch, not something I had to guess. Mechanic:
'work scholar <hours>' earns a wage but displaces your own medical "practice" income hour-for-
hour at a worse rate (practice pays more per hour but can't be sold for wages at the same time);
working ALL 2000 hours in a year nets roughly +200 hacksilver versus doing nothing, because the
wage (~540) beats the foregone practice income (~330). Doing this for about 8-9 years running
(900->919 in my game) dug me back from -1,519 to +407 hacksilver and back to a positive net
income, ending roughly where I'd have been if I had simply not touched credit at all, but with
9-10 extra years spent digging out and four technologies banked (scientific_method,
units_standards, cap_measure_len, arithmetic_positional).

LESSON I would give myself replaying this: do not start more than one or two hacksilver-costed
projects back to back before your income stabilises; 'money' shows a forecasted borrow/interest
figure right when you 'start' something on credit - READ IT, it is not a formality. Also: if
you are ever going to spend hours on 'work' to cover a shortfall, do it BEFORE you are in heavy
arrears, not after - the interest compounds daily^H^H^H yearly and the earlier you catch it the
less of your income goes to interest instead of principal.

ONE THING I WANTED BUT COULD NOT GET: a way to pay down debt directly/early rather than just
waiting for net income to erode it over several turns. I looked for something like "repay
<amount>" and did not find it in 'help commands' - it seems the debt only falls via the
residual of (revenue - costs - interest) each step, which is why the hole took 9+ years to
climb out of even once I started working full hours every year.

## [919-945 AD] Playing more carefully: single projects, then a real income concern

After recovering solvency, I changed approach: start ONE thing at a time, work whatever hours
are left over as a scholar for wages (careful to leave enough of my own hours unspent for the
project's own YOUR HOURS requirement - more on that confusion below), and only start the next
thing once the current one is either finished or its money is fully paid off. This kept me
solvent through statistics_basic (182), algebra_symbolic (504), and geometry_analytic (980) -
7 techs built by turn 922, on the road to the goal. Money stayed positive throughout.

CONFUSION #2 (took a few turns to notice): 'work <trade> <hours>' happily lets you sell every
single one of your 2000 founder-hours for wages, INCLUDING the hours your own active project
still needs. If you do that, the project's "still owed" money can hit 0 while its "% of your
hours spent" stays stuck (I saw it parked at 66%, then 80%, then 92%, for several turns running)
with the log saying "waiting on your hours" - because I kept working all 2000 and leaving
nothing for the project itself. The fix, once I noticed the pattern, was simple: work
(2000 - hours_the_project_still_needs) instead of a flat 2000, so the leftover goes to the
project automatically at 'step'. This is not explained anywhere I found; you have to notice
the stuck percentage and reason backward. I would ask the designers to have 'work' either warn
you if you are about to starve your own active project of its last hours, or show remaining-
hours-needed somewhere more prominent than 'why <id>'.

HIRING STAFF, a second expensive mistake: several multi-scholar techs (atomic_theory,
logarithms, calculus) need "2 trained scholars... on your own staff", not just hired labour-
hours. I hired one scholar to reach 2. The quoted price when checking 'labour scholar' beforehand
was "a year of one: 525 hacksilver", but the actual 'hire scholar 1' command charged an
IMMEDIATE 525 advance AND set an ongoing wage bill of 826.6/yr (which settled to 633.6/yr the
following year once the advance washed out) - about 20% more than the quoted number, presumably
a scarcity premium: the game had already told me (in 'labour scholar') that the literacy
ceiling here is "1.8 scholars in total, ever, at any price," and hiring a second pushed me right
up against that ceiling. My recurring net income swung from +12/yr to -620/yr in one hire. I
fired the scholar the same turn once I saw 'money'. LESSON: always run 'money' immediately after
any 'hire', not just after 'start' - the forecast shown at hire-time (just "a year of one: 525")
significantly understated the real cost of a marginal hire against a scarce trade.

THE THING THAT ACTUALLY FIXED MY ECONOMY: horse_collar (2,103 hacksilver, 1 artisan staff,
10% risk). I built it the same way as everything else (one project, work leftover hours, ride
out a debt dip while it drew down its cost - this one paid almost all of itself in a single
step since it wasn't scribe-bottlenecked, driving me to -1,155 hacksilver in one go, which was
alarming but recovered in about 5 turns). The difference from every "foundation" tech I had
built before: 'ventures' showed it would EARN 1,288/yr against 210/yr upkeep once opened -
foundation techs like scientific_method or units_standards earn exactly 0 no matter what.
I 'open'ed it (315.5 more to open) and watched net recurring income go from roughly break-even
to +1,043/yr within two turns as the business "found its custom" (the game telegraphs this:
"it earns 900 a year... It reaches that over the first 3 years, expect less at first"). This
was the single biggest lesson of the whole session: FOUNDATION/KNOWLEDGE techs (tier 0,
"almost everything rests on this") are necessary to unlock the tree but generate no income
even when finished and opened; you have to deliberately go find and build something with a
nonzero EARNS/YR in the 'available' table (I had been ignoring that column) if you want the
economy to ever stop being a treadmill. With that fixed, I could comfortably hire a permanent
artisan (210/yr, plentiful trade, 6,469 hours available town-wide, no scarcity premium - a
useful contrast with scholars) as backup labour for the horse_collar concern (which had warned
"no spare craftsmen: losing just one more closes it outright"), and a second scholar (this
time affordable, ~1,049/yr combined wage bill against +1,583/yr revenue) to finally start
atomic_theory, which completed in a single year.

STATE AT AT TURN ~945 (45 years played, session still open): 9 technologies built by me (of a
goal-tree that needs 168 for the transistor), 14 nodes down the fogged road to the goal,
193 hacksilver in hand, +300/yr recurring net income, one open income concern (horse_collar),
2 hired staff (1 artisan, 1 scholar) plus myself (now sch 2 art 2 total), reputation 7.4,
scandal a harmless 0.30 (decaying), eminence 0.02. 'risk'/'state full' show the upcoming
historical hazard timeline explicitly even under fog of war: Christianisation 995-1100 (will
cut output ~10% unless I have land/military of my own), a Norwegian civil-war era 1130-1240,
the Black Death 1349-1351 (55% staff loss threatened), the Little Ice Age from 1300, and the
Reformation 1536-1560. Interesting asymmetry in the fog design: it hides the TECH tree (what
you could research and where it leads) but does NOT hide the HISTORY tree (what is coming and
roughly when) - you're blind about your own progress but not about the world's calendar. I
have not yet reached any of these historical hazards in play.

## Design observations / things I'd tell the makers, so far

- The core loop (why -> start -> work leftover hours -> step -> open) is legible and the
  game's own in-line help is unusually good: 'help <topic>' answers most "how do I..."
  questions directly, and the arrears warning at turn 914 (see above) is a genuinely well-
  designed piece of teaching, delivered exactly when needed rather than as a wall of text
  up front.
- The credit/interest system is realistic but punishing in a way that is easy to trigger by
  accident in the opening turns, when income is thin (starting net income was +3.4/yr against
  a "poor_scholar" 560-hacksilver purse) and the temptation is to start 2-3 cheap-looking
  foundation techs at once because 'available' shows 200+ affordable things immediately. A
  first-time player has no prior signal that "cost you can pay" and "cost you can safely
  service the resulting debt on" are different numbers, and the game does not warn about this
  until you are already in arrears with a whole page of accusatory red-flag text. A one-line
  nudge the FIRST time a project draws on credit ("this puts you into recurring interest that
  your current income might not cover - see money") would have saved me several real turns of
  confused debugging.
- The EARNS/YR column in 'available' is exactly the information that would have prevented my
  early debt spiral (start income-producing things before, or alongside, purely-enabling
  foundation research) but nothing in the early tutorial text foregrounds it - the five
  starter commands (state/available/why/start/step) are taught, but "look at what actually
  pays for itself" is something I had to learn by going broke, not something I was told.
- 'work <trade> <hours>' silently competing with an active project's own hour requirement
  (see CONFUSION #2 above) is the sharpest small usability gap I found - it would be very easy
  to add a one-line note to 'work's output when doing so leaves an active project's hours
  unfinished for the step ahead.
- The hazard/history timeline is a genuinely lovely piece of design: real Norse history
  (Iceland/Althing, Christianisation, the Black Death, the Kalmar Union, the Reformation) is
  dramatized as a sequence of economic and knowledge risks with concrete, checkable mechanical
  effects (output multipliers, staff-loss percentages) rather than flavour text, and it is
  visible under fog of war while the tech tree is not, which is a nice piece of asymmetric
  information design that I did not expect and liked a lot once I noticed it.

## [945-954 AD] Trying 'rush', and a second, smaller debt dip

With the horse_collar income established, I tried 'rush limit:3' out of curiosity (it is
documented in 'help commands' as "start everything you could begin today in one go, highest-
leverage first"). It picked identity_cover (2,433), calculus (546) and sea_sternpost_rudder
(501.1) - three foundation/math techs, not an income-producer among them, and its own output is
admirably honest about this: "it begins things in order of how much rests on them, with no idea
what you are building toward... on an early turn it can do real damage. A careful player beats
it." That warning turned out to be accurate: committing to 3,480 hacksilver of work against a
credit limit of 3,701 pushed me to -2,062 hacksilver two turns later (worse than my very first
debt spiral in absolute terms), even with a working income concern going. The difference from
the early-game spiral was recovery speed: because horse_collar was now paying ~1,288/yr, 3-4
turns of 'work scholar 2000' plus 'step' brought me back to +310 hacksilver and a healthy
+304/yr recurring by year 954, versus the 9+ years the FIRST spiral took to fix. CONCLUSION:
'rush' is a real, working feature, exactly as labelled ("a rough rule of thumb... it exists to
save typing in a late game"), but it is honest about being reckless if used early, and the
game's own help text told me so before I even ran it - I ran it anyway on purpose, as an
experiment, and it did what it said it would.

## STATE AT END OF THIS SESSION (year 954, 54 years played)

- 12 technologies built by me, 125 granted free at start (137 total known); 16 nodes down the
  fogged road toward the goal (transistors, closure 168 - so genuinely early, maybe 10% of the
  way there by node count, though nodes are surely not uniform in difficulty).
- Capital 310 hacksilver, net recurring income +304/yr (healthy, no debt).
- One open income concern: horse_collar (earns ~1,288/yr, costs 210/yr upkeep).
- Staff: myself + 1 hired artisan (210/yr, cheap, no scarcity) + 1 hired scholar (735/yr
  combined with the artisan's wage in the ledger; scholars are scarce and expensive here).
- Reputation 8.8, scandal 0.12 (harmless and decaying), eminence 0.03 (harmless), protection 3%.
- Two debt spirals survived (900-919 AD, self-inflicted by parallel foundation-tech starts
  with no income; 945-953 AD, self-inflicted on purpose via 'rush' as an experiment), both
  recovered using the same lever: 'work <trade> <hours>' to sell founder-hours for wages.
- Went 3-for-3 on multi-turn techs that stalled on "society cannot supply the labour" (scribes
  capped around 419 hours/yr town-wide) - a recurring, expected friction rather than a bug: the
  game explicitly frames Scandinavia as having "no bureaucracy," so a thin scribe pool feels
  earned rather than arbitrary.
- Never saw a project actually FAIL its risk roll (several had 10-20% failure chances and all
  succeeded) or a scandal/eminence event trigger a run-ending denunciation - I did not play
  long enough, or run reckless enough on standing, to see those systems bite.
- Never got as far as founding a school (school_founded, 16,100 hacksilver, +4 scholars/yr,
  4-year floor) or unlocking engineer/machinist trades (needed by a visible cluster of
  "heard of, cannot begin yet" manufacturing techs) - these are clearly the next big
  infrastructure rungs, both blocked mainly by capital and by the scholar/craftsman ceiling.

======================================================================
# FINAL SUMMARY

## How far I got

Played as the Norse (Scandinavia, Viking age, arriving 900 AD), fog of war on, mortality off,
default goal (grown and alloy junction transistors), horizon set to Endless. Reached year 954
(54 in-game years), with:

- 12 technologies built by me, out of 168 needed for the full transistor goal (roughly 16 of
  the goal's own "road" nodes reached, by the game's own count - so meaningfully started, not
  close to finished; this looks like a game meant to be played over hundreds of in-game years).
- A stable, self-sustaining economy: 310 hacksilver in hand, net +304 hacksilver/year
  recurring, with one open income-producing "concern" (the horse collar, earning ~1,288/yr
  against 210/yr upkeep), a hired artisan and a hired scholar on staff alongside myself.
- Reputation 8.8, scandal and eminence both negligible and decaying, no denunciation or run-
  ending event encountered.
- Survived two self-inflicted debt spirals (see the timestamped log above) and recovered fully
  from both.

I stopped there because I judged I had seen the core loop, the failure modes, the recovery
mechanisms, and a representative slice of the tech tree and world-event system clearly enough
to write an honest report - not because the game itself stopped me. The session's progress is
saved in the game's own session file (it told me the path on first launch); nothing was lost by
stopping.

## What stopped me

Nothing in the game stopped me - I chose to stop once further play looked like "more of the
same shape of decision" (pick an affordable or credit-worthy tech, work spare hours for wages,
step, repeat) rather than new territory. The genuinely large next steps I could see waiting -
founding a school (16,100 hacksilver, a 4-year build) to break the scholar-scarcity ceiling, or
teaching an engineer to unlock a visible cluster of manufacturing techs - are legitimate,
telegraphed mid-game goals, not something I was blocked from attempting; I simply did not have
the runway in this session to grind out the capital and turns they would need.

## What I would change, if I were advising the makers

1. **Foreground the EARNS/YR column earlier.** The five starter commands you teach
   (state/available/why/start/step) never mention that most early "foundation" techs
   (scientific_method, units_standards, arithmetic_positional, etc - anything that says
   "almost everything rests on this") earn exactly nothing even once built AND opened, while a
   few things (horse_collar and presumably others) genuinely pay for themselves. I found this
   out only by going broke first. A single sentence in the opening tutorial text - "some things
   you build only unlock other things; look at EARNS/YR in 'available' for what actually pays
   for itself" - would have saved a real debt spiral.

2. **Warn earlier and more specifically about credit.** The game does eventually warn you
   (the "YOU HAVE BEEN IN ARREARS N YEARS" message, which is genuinely excellent once it
   fires), but by the time it fires you may already be years deep. A warning the FIRST time a
   'start' command's forecast shows you drawing on credit at all - not just once you are
   already delinquent - would catch the mistake earlier.

3. **'work <trade> <hours>' can silently starve your own active project of the last hours it
   needs to finish**, even while showing its money fully paid off. I watched a project sit at
   "80% of your hours spent... waiting on your hours" for several turns because I kept selling
   all 2,000 hours to wage work. This is discoverable (the log says exactly what it's waiting
   on) but non-obvious, and cost me real time before I noticed the pattern.

4. **Hiring a scarce trade (scholar) costs meaningfully more than the price quoted by 'labour
   <trade>' just beforehand** - the quoted "a year of one: 525" became an 826.6 first-year
   bill and a 633.6/yr ongoing one once I actually hired, apparently a scarcity premium tied to
   the literacy ceiling. I would either fold that premium into the quote shown by 'labour', or
   say explicitly in that quote that hiring near the ceiling costs more than the average.

## What I liked

- The command surface is genuinely well-designed for a text game: 'why <id>' gives you
  everything you need to make an informed choice (cost, hours, calendar floor, risk, staff,
  prerequisites, and critically "how much rests on this" as a plain-language leverage signal),
  and 'help <topic>' reliably answers "how do I do X" the moment you think to ask it.
- The historical hazard timeline (Iceland/Althing, Christianisation, the Black Death, the
  Kalmar Union, the Little Ice Age, the Reformation) is dramatized with real mechanical stakes
  (output multipliers, staff-loss percentages) rather than as flavour text, and - a detail I
  did not expect and liked a lot - it stays visible under fog of war even though the tech tree
  itself does not. You are blind about your own progress but not about the world's calendar.
- The 'rush' command is honestly documented as reckless in the early game and behaves exactly
  as warned when I deliberately tried it - a rare case of a game's own help text being fully
  trustworthy about a shortcut's downside.
- The economic model (labour scarcity by trade, a household/"lettered trades" ceiling on how
  many literate staff you can ever field until you build the institutions that raise it,
  interest on arrears, a concern needing time to "find its custom" after opening) all hang
  together as one coherent, learnable system, even though parts of it are unforgiving to a
  first-time player who has not yet learned its shape.

## Notes on process

Per instructions I did not open or read the game's source code, or any other files in the
repository (including any other playtester's notes), at any point. Where I was curious about
mechanics I could not observe directly from play (e.g. exactly how the calendar-floor vs.
actual-completion-time relationship is computed, or the precise formula behind the scholar
scarcity premium), I noted the curiosity in the timestamped log above and moved on without
looking, playing purely through the game's own interface as instructed.
