# Playtest notes — rome_100ad_A

Playing "Rome 100ad" simulator, fog of war on. Rules I'm following: only look at
what the running game tells me, never read the repo source/docs. Session file:
rome/playtest/naive/rome_100ad_A.json

## What actually happened, in order

- Year 100: started with 400 capital, -216/yr living cost — less than 2
  years of runway doing *nothing*. Started `units_standards` (444 cost, 0.5
  yr floor) even though I was 44 short, and the game let me — money is
  clearly not checked strictly against the full project cost up front.
- Year 101 (after `step years:1`): the step auto-granted 139 technologies at
  once — all the free "ROME ALREADY HAS THIS" items from `available`
  (coined money, contract law, the arch, aqueducts, bronze, wool, dozens
  more) — as `done_granted` rather than `done_earned`. Revenue jumped from
  0 to 666.7 purely from this baseline package. I hadn't done anything to
  cause this beyond stepping time once; it seems to be a one-time "Rome's
  starting economy switches on" event.
- Year 102-103: `units_standards` completed. Revenue climbed to 1000, then
  capital (which had read exactly 0.0 for two straight yearly snapshots
  despite different, once-positive `net_after_project_spend` values) jumped
  to 700. See the "confusing numbers" note below.
- Year 104-106: banked capital, then built `fin_pawnshop` (1025 cost, 0.3 yr
  floor, revenue 300/upkeep 50). Reputation jumped 5.0 -> 6.9 on completion.
- Year 108-111: built `identity_cover` (1580, the Alexandrian
  physician-philosopher cover) and `scientific_method` (200, 2 yr, 20%
  fail risk, needed identity_cover as a prerequisite) — scientific_method
  succeeded despite the risk. `why` on these showed staggering
  `downstream_count`: identity_cover 2151, scientific_method 1082,
  patron_local (done next) 1984. These three "foundation/social" moves
  gate a huge fraction of the whole tree.
- Year 111-115: built `patron_local` (secure a town patron, 1200, halves
  incoming suspicion) and `fin_trading_post` (1662.5, revenue 300/upkeep
  100). Reputation climbed steadily to 9.1.
- Year 115: experimented with the economy commands. `buy forest` at n=50
  and n=10 both failed ("cannot afford", even though 10ha should have cost
  2500 and I had 1587 — consistent, not a bug); n=1 succeeded and cost 250
  denarii for that one hectare (first time the currency is named —
  everywhere else it's just "capital"). Bought 2 slaves for 625.5 denarii
  total; `scandal` immediately went from 0 to 1.06 — the only stat that
  moved from the purchase. Manumitted both immediately: reputation ticked
  up 9.1 -> 9.9, `freedmen` went 0 -> 2, but **scandal stayed at 1.06** —
  freeing them did not erase the moral cost of having bought them, which
  feels like a genuinely well-considered piece of modeling rather than an
  oversight. Headcount-wise, freedmen contributed the same to the
  `artisans` labour total as slaves had (3.45 either way); the help text's
  claim that freed people "work better" isn't visible in that raw number,
  so either it's a hidden multiplier elsewhere or it doesn't actually show
  up in aggregate labour count.

## The rest of the run, compressed

- Year 121-165: kept building small profitable ventures (ferry, inn) and
  banked a big cash pile (peaked around 12,500 capital at year 165) while
  reputation quietly eroded in the background even though I wasn't doing
  anything wrong that I could see (10.5 at year 121 down to 4.1 by year
  165, with no explaining event in between) — "appearances" upkeep
  apparently isn't fully captured by the `living_cost` number, or
  reputation just decays on its own over time unless actively maintained;
  never explained anywhere.
- Year 165-180: **the Antonine plague hit for real** — five separate
  "Antonine plague: staff -28%" events between 168 and 179, each
  compounding. Artisans fell from 3.45 to 1.96, scholars from 1.0 to 0.72,
  reputation kept sliding, and capital fell (14,061 -> 8,602) even though
  I hadn't started anything and revenue was flat — this was the disaster
  the game told me about on turn one, arriving exactly on schedule and
  doing exactly what it said it would.
- Year 189: built `corpus_written` ("Write the corpus: everything you
  know, in plain quantitative Greek and Latin") — flagged in its own
  description as "the largest single call on your personal hours in the
  entire game, and the one you must not cut." It completed and fired a
  distinct event: "changes the society: literacy_elite, w_magic_fear" —
  the one time the game showed a project reshaping the *society* around
  me rather than just my own balance sheet. It also visibly improved my
  knowledge-loss odds in `knowledge_risk` (loss chance on a sacking 0.8 ->
  0.45, fraction lost 0.4 -> 0.22).
- I went looking for the *better* hedge it pointed to,
  `corpus_dispersed` ("Print and disperse hundreds of copies across three
  continents... THE highest expected-value node in the tree"). Its own
  `why` output named `printing_press` as a missing prerequisite — but
  calling `why printing_press` directly got "you have never heard of
  that." So a locked node's full name and description leaked to me
  through a downstream node's prerequisite list, even though fog of war
  is supposed to hide anything I haven't reached myself yet. Minor, but a
  real leak.
- Year 190 on: currency debasement (190-275) under way in the background.
  I stopped investing new capital and just let time run while reputation
  and revenue quietly drifted down (revenue flat at 2198.2 for decades,
  reputation 2.7 -> 1.7 -> 0.7 -> 0.2 by year 278) — this was my own
  passivity, not a forced outcome, but the game never warned me the
  neglect was compounding until it was already bad.
- Year 235-284: **the third century crisis** — repeated "a site is
  sacked" events (237, 240, 243, 248, 253, 261, 263, 271, 275), overlapping
  with the Plague of Cyprian (staff -28% twice more) and the tail of the
  currency debasement. This is where it stopped being background flavor:
  - Year 253: "KNOWLEDGE LOST: 1 technologies forgotten (the corpus was
    never printed and dispersed)" — direct, specific payoff for not
    finishing the corpus_dispersed hedge. `done_count` dropped from 150 to
    145 across this stretch.
  - Year 259: "ABANDONED 4 works you could no longer maintain; they have
    fallen into disrepair."
  - Year 260: "IN ARREARS for 25 years: staff are leaving because you
    cannot pay them."
  - Capital went **negative** (-2075.8 at year 250, -2854.8 by year 277)
    and stayed negative for decades. The game did not end, block further
    commands, or flag any special "bankrupt" state — `ended` stayed
    `false` and `end_reason` stayed `null` throughout. You can apparently
    run an empire of one at a permanent, unrepaired loss indefinitely.
- Year 277-278, an odd final discovery: with capital deeply negative and
  reputation near zero, `available` started listing the same enterprise
  projects I'd built decades earlier at **pennies on the denarius** —
  `fin_pawnshop` for 5.0 (was 1025 originally), `fin_inn` for 17.3 (was
  3537.5), `fin_ferry` for 9.4 (was 1915.5). I started a second pawnshop
  for 5 denarii to test it, and it was accepted immediately. If this is
  meant to represent currency debasement, it's backwards — debasement
  should make nominal prices go *up*, not collapse by two orders of
  magnitude. It reads much more like a bug (some multiplier tracking
  reputation/familiarity/capital collapsing toward zero and getting
  multiplied into cost instead of divided, or similar) than a deliberate
  "things are cheap when your currency is worthless" mechanic, because it
  makes recovering from collapse trivially easy rather than harder.

## Where I stopped
Year 278 AD (178 years played of the 500-year horizon to 600). 145
technologies completed (peaked at 150 before the third-century losses),
revenue 620/year, capital -1480.8 (in debt), reputation 0.2 (near zero),
founder still alive. I stopped here because I'd seen a full arc — bootstrap,
growth, a real historical disaster survived, a second real historical
disaster that caused permanent knowledge loss, and a slow-motion financial
collapse that the game just lets you sit in — and because at this point
further play was mostly "step and watch the same numbers drift," which
wasn't teaching me anything new about the simulator.

## Overall impressions

What I liked:
- The premise is genuinely good and the writing backs it up. Notes on
  individual items are specific and often wry ("Rubber erasers require
  natural rubber, which is UNOBTAINABLE"; "the ordinary condition of
  production in most of these societies"; "Expect organised opposition,
  not curiosity" on the scientific method; "the lesson of Alexandria is
  not that books burn, it is that single copies burn"). It never feels
  like generic flavor text.
- The historical hazards (Antonine plague, Plague of Cyprian, third
  century crisis, currency debasement) are told to you up front, in full,
  including years and mechanical effect, and then they actually happen on
  schedule and do what they said. Foreknowledge without being able to see
  the tech tree is a nice asymmetry, and the fact that I could have
  hedged against the sacking-related knowledge loss (with
  corpus_dispersed) and didn't finish doing so, and then specifically lost
  a technology to exactly that failure mode, is the kind of consequence
  that makes we want to play it again more carefully.
- Slavery is modelled with real teeth rather than being a checkbox: it
  costs money, it adds a `scandal` stat that decays slowly rather than
  vanishing the instant you manumit, and manumission is free and raises
  reputation. It doesn't feel like it's lecturing so much as pricing the
  thing honestly.
- The sheer scale is impressive — 299 items visible turn one, growing past
  370 by mid-game, spanning textile buttons to nuclear fission, all with
  real cost/hours/years/risk numbers and (when `why` works) full
  prerequisite chains and downstream counts in the thousands.

What confused, bothered, or seemed missing:
- The session-reload bug (see above) is the single biggest problem: it
  breaks the one persistence feature the game's own help text advertises
  as its reason for existing, and it breaks completely and immediately —
  not a rare edge case. Anyone playing this the way the instructions say
  to play it (stop, come back later) will hit an unrecoverable "TypeError"
  wall on their very next command.
- Numbers that are shown to you frequently didn't add up against each
  other: `capital` sat frozen at exactly 0.0 across two different turns
  with two different (including positive) `net_after_project_spend`
  values, then jumped by amounts that didn't match any displayed net
  figure; `net_per_year` and `net_after_project_spend` disagreed with each
  other more than once (-27.3 vs +416.7 on the same turn early on); late
  game, `revenue - living_cost` routinely didn't match `net_per_year`
  (620 - 337.2 should be +283, the game said -847.2). I never found a
  reliable way to predict what capital would do next turn from the
  numbers state gives you, which undercuts the "everything about your
  position right now" promise of the `state` command.
- Reputation decayed steadily for decades with no event ever explaining
  why (10.5 -> 0.2 over about 150 years without a single logged cause),
  which made it feel less like a lever I could manage and more like a
  clock running out in the background.
- The apparent cost-collapse once capital went deeply negative and
  reputation hit near-zero (pawnshop at 5 denarii instead of 1025) reads
  as a bug, and if so it's a forgiving one — it makes recovering from
  total collapse almost too easy, which undercuts the third-century-crisis
  moment right after it hit hardest.
- `step` refuses fractional years below 1 ("years must be >= 1") even
  though plenty of projects have a `least_years`/`calendar_floor_years`
  well under 1 (0.0, 0.1, 0.3...). You can never actually watch one of
  those complete on its own timeline; everything gets rounded up to
  whole-year ticks regardless of the project's own stated duration.
- No difficulty ever pushed back on me for going 25 years into arrears
  besides losing works and staff — no debtor's prison, no forced sale, no
  hard game-over. `ended`/`end_reason` never triggered despite a
  five-decade, ever-deepening negative balance. It's plausible that's
  intentional ("no score but the state of what you have built," per the
  welcome text) but it does mean there's no real floor to how badly you
  can be doing while still nominally "playing."
- Minor fog-of-war leak: a locked prerequisite's full id, name, and
  description surfaced through another node's `why` output
  (`corpus_dispersed` names and describes `printing_press` in full) even
  though `why printing_press` itself is refused as something I've "never
  heard of."
- I never did find out what `on_goal_path` was actually measured against
  — `state.goal` was `null` for the entire game.

If I were changing this game, in priority order: fix the session
persistence bug first, since it makes the advertised way of playing
unusable; then reconcile the capital/net/revenue arithmetic so the numbers
you're given actually explain the numbers you're given next turn; then
either explain reputation decay or tie it visibly to something I can act
on.

## Session log

### Start
Launched the simulator. It printed a welcome block explaining the premise:
I'm one person in 100 AD Rome with modern knowledge but no modern industry.
Building things costs my hours, other people's hours, money, materials, years.
Goal: advance as far as possible before the horizon at 600 AD. No score, just
what you've built.

Commands: state, available, why <id>, start <id>, stop <id>, step <years>, buy,
bounty <id>, path <id> (disabled under fog), save/load, help, quit.

Economy: buy forest (hectares of coppice -> charcoal), buy mine (tonnes/year,
takes years to sink), buy slaves, manumit (free slaves - "the decent thing").

First reaction: interesting that slavery is modeled explicitly and manumission
is editorialized in the help text itself ("it is the decent thing"). Notable
design choice to put a moral valence in the tool description rather than
leaving it neutral.

### Initial state (year 100)
capital 400, revenue 0, living_cost 216/yr, net -216/yr, founder_hours 2400,
scholars 1, artisans 3, reputation 5. So I start basically broke: less than
two years of runway before I'm out of money, even doing nothing.

State also shows "known_hazards_ahead" right from turn one under fog of war:
Antonine plague (165-180, 28% staff loss), Plague of Cyprian (249-262, 28%
staff loss), Third century crisis (235-284, 16%/yr chance of a site being
sacked), currency debasement (190-275). That's a neat piece of design —
foreknowledge of history-shaped disasters baked into "what you know" even
though fog of war hides the tech tree.

### `available` at turn 1: 299(!) items
Huge surprise: right at the start, under fog of war, there are 299 things
listed as "available to begin now" — everything from tiny textile techniques
(buttons, needles, retting flax) up to Newton's laws, the neutron, nuclear
fission, and quantum mechanics. 113 of them are zero-cost/zero-hour/zero-year
items tagged "ROME ALREADY HAS THIS" (i.e. baseline stuff like coined money,
contract law, muscle power, bronze). The other 186 have a real cost in money
and founder-hours.

This is surprising/confusing: it implies there's effectively no prerequisite
gating at the surface level — a 100 AD Roman persona can in principle start
"Heisenberg uncertainty principle" turn one for 292.8 currency and 120 of my
hours, having never done algebra or written a paper. I expected fog-of-war to
reveal a much smaller frontier that widens as I complete things. Instead it
seems the frontier IS almost the whole tree already, just cost/hours act as
the real gate (and I only have 400 capital, so 99% of these are unaffordable
right now regardless).

### CRITICAL BUG: the --session file breaks the game on reload
I tried `state`, `available`, `why`, `start` from separate process invocations
(exactly the "playing across several sittings" workflow the game's own help
text advertises: "Pass --session FILE ... so you do not need to hold a
process open or write a script"). Reproduced cleanly with throwaway test
sessions outside my notes:
  1. Run one command (even just `state`) against a brand-new --session file.
     Works fine, writes the file.
  2. Start a **second process** pointed at that same session file (i.e. what
     "playing across several sittings" means) and send `state` again.
  3. Every single command now fails:
     `{"ok": false, "error": "internal error handling that command:
     TypeError: type NoneType doesn't define __round__ method. The game is
     intact; try something else."}`
     and other commands (`why`, `start`) fail the same way with a sibling
     error: `TypeError: '>=' not supported between instances of 'NoneType'
     and 'int'`.
This is not a one-off — I reproduced it three separate times, including with
nothing but two bare `state` calls. The save/load round trip the game
explicitly advertises as its headline feature is completely broken: the
moment a session is written to disk and read back by a new process, the game
becomes permanently unusable through the ordinary interface, even for the
read-only `state` command that's supposed to be always safe. The claim "The
game is intact; try something else" in the error message is not true in any
useful sense — nothing else works either once this happens.

Workaround I used to actually play: instead of invoking a fresh process per
command (which is what --session is *for*, and what stopping/restarting
tool calls naturally does), I kept a single simulator process alive for the
whole session, feeding it commands through a growing file piped in with
`tail -F`, so the process never restarts and never reloads its own session
file from disk. This is not something a normal player could be expected to
do — the documented, intended workflow (stop, come back later, `--session`
picks up where you left off) is the one that's broken.

### `why <id>` — only works before the first reload
Correction to my earlier note: `why` isn't broken in general, it's a
casualty of the session-reload bug above. Inside one continuous process it
works, and it's genuinely great: for `identity_cover` and `units_standards`
it showed `downstream_count` (2151 and 1683 respectively!), `on_goal_path`,
full cost breakdown (labour/materials/capital, with civ/distance/price
multipliers), upkeep, revenue, risk of failure, staff needed, suspicion
delta, and prerequisites. Once I switched to the single-long-lived-process
workaround, `why` worked every time. So this is really one bug (the reload
corruption above), not two.

One thing `why` revealed that seems like a real inconsistency: `state.goal`
is `null` and `state.goal_reached` is `false` the entire game (fog of war
apparently means no explicit goal is ever set for me), yet individual items
report `"on_goal_path": true/false` as if there's a concrete goal being
measured against. `identity_cover` and `units_standards` both say
on_goal_path: true; most of the small textile/free items say false. If
there's no goal, what path is this? Never explained.
