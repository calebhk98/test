# Playtest notes — rome_100ad_A

Playing "Rome 100ad" simulator, fog of war on. Rules I'm following: only look at
what the running game tells me, never read the repo source/docs. Session file:
rome/playtest/naive/rome_100ad_A.json

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
