# Playtest notes — rome_100ad, session C

Playing blind: agent CLI only, fog of war on. Not reading any source/data files, only
what the running process tells me.

## Setup notes (infra, not gameplay)
- The game speaks line-delimited JSON on stdin/stdout and explicitly documents that
  you don't need to keep a process open — pass `--session FILE` and it reloads/saves
  state around every single command. So instead of holding a long-lived process I'm
  just invoking `python3 rome/sim/simulator.py agent --civ rome_100ad --fog --session ...`
  fresh for each command (or small batch of commands), piping in JSON lines.
- First attempt: I tried to build a fifo+background-driver setup to hold one process
  open, then killed the background process mid-flight. This left the session JSON
  in a state where `state` and `available` both threw internal TypeErrors
  ("'>=' not supported between NoneType and int", "NoneType doesn't define __round__")
  on every subsequent call — i.e. the crash looked like it was persisting into the
  save file itself, each call failing slightly differently. I deleted the session
  file and started clean rather than trying to inspect/repair it (would have meant
  reading a file, which is against the rules, and also felt like save-scumming).
  Once restarted cleanly, `available` as literally the first command worked fine
  (299 entries), so I believe this was me breaking my own plumbing, not a game bug.
  Flagging it anyway: if a real player's terminal/ssh session dies mid-command,
  it's worth knowing whether the save can end up in a half-written, crash-looping
  state. Worth the game verifying/atomic-writing the session file if it doesn't
  already.

## BUG (major): save/reload breaks the game — confirmed, reproducible

The welcome text specifically advertises: "Pass --session FILE... The game is written
to that file after every command and read back when you start again, so you do not
need to hold a process open or write a script." I tested exactly that documented
workflow and it is broken:

- Fresh session, single process, sending `state`, `available`, `why <id>`, `state` as
  four lines to ONE process invocation: all four succeed fine.
- Same session file, but starting a brand NEW process afterward (i.e. actually doing
  the "stop and start again later" thing the game tells you is safe) and sending just
  `{"cmd":"state"}`: crashes every time with
  `TypeError: type NoneType doesn't define __round__ method`.
- Reproduced this from scratch twice (deleted the session file and redid it both times,
  once with `available` as the second-ever command, once with `why` as the second-ever
  command) — in both cases the *first* command against a brand new session works, and
  the *first command of the second process invocation* (i.e. right after one save/load
  round trip) throws either `'>=' not supported between instances of 'NoneType' and
  'int'` or (on the call after that) the `__round__` one. Once it starts happening it
  happens on every subsequent call, including plain `state` — the save file seems to
  stay bad forever after.
- So: something written to the session JSON on first save doesn't round-trip cleanly —
  some numeric field is being saved as `null`/omitted where the code assumes it's
  always an int/float, and nothing guards the None case. Given the very first save
  (from the game's own initial setup) is already enough to trigger it on reload, this
  looks like it would hit essentially any player who actually stops and restarts,
  which the game explicitly invites you to do.
- Workaround I'm using: keep a single long-lived process open for the whole session
  (via a fifo) instead of relying on --session reload between commands, so I never
  actually exercise the reload path again after this point. That means my playthrough
  from here on is NOT testing the "stop and start whenever" promise — just flagging
  that the promise looks broken as documented.

## Actually playing now (persistent process via fifo, no more restarts)

- `why units_standards`: downstream_count 1683(!), on_goal_path true, cost 444 total
  (labour 104 + materials 90 + capital 250), 300 founder-hours, 0.5yr floor, 5% risk.
  Also has a `goal`/`on_goal_path` concept even though `state.goal` is null — not sure
  yet what the actual goal is or how it's set; fog of war may be hiding it, or maybe
  there just isn't one yet (sandbox mode?).
- `why arrival_orientation`: explicitly says "no longer a prerequisite for anything...
  Skip it if you want to move fast... The simulator lets you skip it, because a model
  that forces the cautious opening is not a model, it is an opinion." Charming bit of
  authorial voice. downstream_count 0, on_goal_path false — so it's genuinely optional
  fluff/insurance, not gating anything. Decided to skip it.
- `why identity_cover`: cost 1580 total, upkeep 200/yr, suspicion -6 (reduces
  suspicion, good), downstream_count 2151. Can't afford right now (only have 400
  capital) even though `can_start_now: true` — apparently you're allowed to start
  things you can't fully afford; presumably cost is drawn down over the project's
  life rather than charged instantly. Untested consequence if you run out of capital
  mid-project — will watch for that.
- Went with `start units_standards` first: cheap-ish, explicitly foundational
  ("do this before writing any other recipe down"), huge downstream count.

### `available` is enormous and very noisy
- 298 entries on turn 1, but 185 of those have cost 0 / hours 0 / years 0 / 0% failure
  and names like "ROME ALREADY HAS THIS" in the summary — i.e. they're not really
  choices, they're background facts about what the setting already includes (spoked
  wheel, coined money, standing bureaucracy, Roman concrete-adjacent stuff...). They're
  mixed in the same flat list as genuine choices with real costs, so at a glance the
  list looks 3x bigger than the actual decision space. I'd want these filtered out of
  `available` by default (maybe a flag to show them) rather than have to filter cost>0
  myself.
- Among genuine (cost>0) options even tier-0/turn-1, the tech tree ranges wildly:
  everything from breadcrumb erasers (cost 5) and flax retting up to trace italienne
  fortification (cost 51, 4 years), substitution ciphers, tin cans, corsets, friction
  matches, spectacle frames — all "available" immediately in 100 AD because you (the
  player) already know how they work, you just have to actually build the knowledge
  base/tooling for Roman craftsmen to produce them. That's a nice, thematically
  consistent way to make the tree feel unbounded rather than a straight tech-era ladder.

### Stepping time: `step years:1` dumped something confusing
- After starting units_standards and stepping 1 year, the response's `completed` list
  had 139 entries, ALL dated "year": 100 (even though we're now told we're in year
  101), and `done_granted: 139, done_earned: 0` in the state block. These look like
  a one-time bulk grant of "things Rome already had at game start" rather than
  anything I did — i.e. the 185 zero-cost "ROME ALREADY HAS THIS" items from
  `available` getting formally marked done, dumped all at once as a giant list mixed
  into the same `completed` array that (presumably) will later report real projects
  finishing. Visually/functionally this is the same shape as "you just discovered
  139 technologies in one year," which reads as a very confusing turn 1 if you didn't
  already know these were freebies. I'd want free starting knowledge to be granted
  silently before turn 1 (or reported separately from earned completions), not mixed
  into the same completion feed as things I actually spent hours and money on.
- Money: started with capital 400.0. After the step: `capital: 0.0`, `revenue: 666.7`,
  `living_cost: 250.0`, `project_spend_last_year: 444.0`, `net_after_project_spend:
  -27.3`, `net_per_year: 416.7`. The arithmetic doesn't obviously reconcile for me:
  400 (start) + 666.7 (revenue) - 250 (living) - 444 (project spend) = -27.3, matching
  net_after_project_spend, so capital "should" be about 372.7, not 0.0. Instead it
  landed exactly at 0.0 — suspicious round number, looks like it's clamped at a floor
  of zero rather than truly reflecting the ledger, which would mean the -27.3 either
  got silently absorbed or is about to bite me as debt I can't see. Also unclear where
  the 666.7 revenue came from — I have no buildings/production/trade set up, no
  `revenue` field was nonzero on turn 1's `state`. Possibly a one-off starting grant,
  or the 139 free "already known" completions each contributed a bit of revenue when
  granted, but the game never says which. Watching capital closely from here.
- Also noticed `artisans` crept from 3.0 to 3.12 and `reputation` dipped from 5.0 to
  4.8 with no explanation attached in the step response — background drift I can't
  yet attribute to any specific cause.
- UPDATE a few turns later: `capital` isn't stuck/bugged after all — it stayed
  exactly 0.0 for ~10 years straight while I kept starting new projects back-to-back
  (it's being fully absorbed by project spend every year), then the moment I let a
  few years pass with nothing active, it jumped to 5686.8 in one `step`. So capital
  really does accumulate, it's just that "0.0" is indistinguishable from "genuinely
  broke" vs "fully committed, spending everything I've got as fast as it comes in."
  I'd still call this a rough edge: there's no way to see, while a project is active,
  how much slack you actually have, or whether you're one bad random event away from
  a cash crunch. A running total that can dip below the "committed" line, or a
  distinct "uncommitted cash" vs "total wealth" figure, would remove a lot of the
  guessing I did here.

## Turn 1 (year 100)
- `state`: capital 400.0, revenue 0, living_cost 216/yr, net -216/yr, founder_hours 2400,
  1 scholar, 3 artisans, reputation 5, everything else (suspicion/scandal/eminence/
  protection/familiarity) at 0. No forest/mines/slaves. Knowledge-risk block already
  lists future hazards by year: Antonine plague (165-180), Plague of Cyprian (249-262),
  Third century crisis (235-284, can sack a site), currency debasement (190-275). That's
  a nice bit of foreshadowing — the game tells you up front what's coming, fog of war or not.
- `available` returns 299(!) options. Huge. Many are flavour/no-ops for things Rome
  already has ("ROME ALREADY HAS THIS") — e.g. cap_heat_0700 (pottery kiln, 700C),
  cap_power_muscle, cap_tol_1mm — cost 0, hours 0, years 0, 0% failure. Not sure yet
  why these show up as "available" to start rather than just being background facts;
  maybe they matter as prerequisites shown for context. First few real options:
  - arrival_orientation: "Six months of listening before you act" — optional, cost 600,
    900 of your hours, 0.5 yr, 2% failure.
  - identity_cover: Alexandrian physician-philosopher persona — cost 1580, 500 hrs,
    0.5yr, 5% failure.
  - units_standards: define standard length/mass/time/temperature, "do this before
    writing any other recipe down" — cost 444, 300 hrs, 0.5yr, 5% failure.
  - hot_air_balloon: for siege observation/signalling — cost 4361.5, 400 hrs, 2yr, 40% failure.
