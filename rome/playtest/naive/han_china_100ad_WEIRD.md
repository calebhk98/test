# Playtest Notes — han_china_100ad, session WEIRD (naive/perverse playtest)

Goal: play badly ON PURPOSE. Look for exploits, loops, absurd results, broken
rules. Do not read any repo files (source, data, docs, other playtest notes).
Only interact with the running simulator process.

Command used to start:

    cd /home/user/test
    python3 rome/sim/simulator.py agent --civ han_china_100ad --fog --session /home/user/test/rome/playtest/naive/han_china_100ad_WEIRD.json

Session file (state, carries over between runs):
/home/user/test/rome/playtest/naive/han_china_100ad_WEIRD.json

---

## Log

### 1. Startup / welcome

`{"cmd":"state"}` and `{"cmd":"available"}` right after a fresh session (year 100,
turn 0) show:

- `state` at turn 0: `"done_count": 12, "done_granted": 12, "done_earned": 0`,
  `capital: 400.0`, `revenue: 0.0`, `living_cost: 216.0`.
- `available` lists **250** startable items even though nothing has been built
  yet, including things like `civ_arch_roman` ("Roman masonry arch") with
  `"cost": 0.0, "your_hours": 0.0, "least_years": 0.0, "chance_of_failure": 0.0`.

Odd thing #0: a Han-China (100 AD) game offers "Roman masonry arch" as an
available item at the very start, alongside `fin_annona` (Roman grain dole),
`fin_argentarii` (Roman bankers), `hom_cosmetics_roman` (Roman cosmetics). Tech
IDs/content look shared/generic across the whole game rather than civ-specific,
which is a little immersion-breaking for a "Han China" playthrough but not
itself exploitable.

Also noted: the big welcome/help block is *not* printed on every invocation —
only sometimes (first time a session is created, seemingly). Not a big deal,
just noting it so future command batches in this log aren't confused by its
absence.

### 2. THE BIG ONE — free 128-technology dump on the very first `step`, doing nothing

Command sequence (fresh session, nothing started, nothing bought):

    {"cmd":"state"}
    {"cmd":"step","years":1}
    {"cmd":"state"}

Result: `done_count` jumps from **12 to 140** (`done_granted: 140,
done_earned: 0`) after a single `step` of just **one year**, having started
*zero* projects. `capital` also moves from 400.0 to 184.0 (the year's living
cost was deducted) but then **revenue: 518.8** appears out of nowhere and
`net_per_year` becomes **+274.9**, all with `active: {}` (nothing running) and
zero buildings/mines/forest owned.

I verified this is not related to anything I did (like starting the free
`civ_arch_roman` project) by repeating with a brand-new *control* session
(`/tmp/.../control_nostart.json`, outside the repo, not read as a repo file —
just a scratch save) where I issued `state`, `step 1`, `state` and touched
nothing else: same result, `done_count` 12 -> 140 after one bare `step`.

I then advanced this control session much further doing *nothing else at all*
(`step 5`, `step 10`, `step 50`, `step 100`, `step 134`, `step 100` — no
`start`, no `buy`, no `bounty`): `done_count` stayed pinned at **140** forever
after that first jump. So this is not a repeatable "free tech every year"
loop — it is a **one-time backlog of ~128 technologies that the game silently
owes you at game start but only actually grants the instant you call `step`
for the first time**, no matter how small the step. Until you step, `state`
undercounts what you "have" by over 100 items.

Expected: turn-0 `state` should already reflect whatever the Han-China 100AD
starting tech package is (12? 140? something), or the first `step` should not
be the trigger that suddenly hands you ~128 unrelated technologies for having
done literally nothing.

Actual: you can look extremely advanced (140 technologies known, revenue
flowing) after doing precisely nothing except calling `step 1`.

### 3. Passive wealth and passive survival: 500 years of doing absolutely nothing

Continuing the same do-nothing control session (no `start`, no `buy`, ever)
all the way to the year-600 horizon:

    {"cmd":"step","years":50}   -> year 120..166
    {"cmd":"step","years":100}  -> year 166..266
    {"cmd":"step","years":200}  -> year 266..466
    {"cmd":"step","years":134}  -> year 466..600 (ends)

Results along the way:
- capital drifted 400 -> 184 -> 2026.8 (yr106) -> 6619.7 (yr116) -> 13049.6
  (yr166) -> dips to 10027.1 (yr266, after several "banditry/frontier war" and
  5x "Yellow Turban rebellion: a site is sacked" events) -> 25265.0 (yr466) ->
  21765.7 at yr600.
- `founder_alive: true` continuously from year 100 to year 600 — **the single
  founder character survives 500 years** with zero aging/death mechanic ever
  firing, despite the game's own premise being "you are one person". I never
  saw a single event about the founder's health, retirement, or succession in
  500 years of simulated time doing nothing.
- Game auto-ends at year 600 with
  `"end_reason": "ran out of horizon (600 AD) without reaching the goal"`,
  as documented. After it ends, further `step` commands are accepted and just
  echo the same ended state back (no error, no crash) — mildly odd (I'd have
  expected a "game over, no further commands" refusal) but harmless.
- Event flavour text is very Rome-flavoured even in a Han China game — e.g.
  repeated `"fire in the insula district"` ("insula" = Roman apartment
  block) and generic "banditry or a frontier war disrupts supply" messages,
  alongside the correctly Han-specific "Yellow Turban rebellion: a site is
  sacked" (184-205 AD, which is period-correct for Han China). So some event
  flavour is civ-aware and some clearly is not.

Take-away: an AFK strategy of "start nothing, buy nothing, just mash `step`
until year 600" already nets you ~140 technologies and ~21,000 capital and a
founder who never dies, purely from the free initial-tech backlog described
in #2 plus passive tax/background revenue. That is a pretty strong candidate
for "should not work but does."


