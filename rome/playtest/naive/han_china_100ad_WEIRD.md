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

(Switched back to the real WEIRD session for everything below. The
`civ_arch_roman` free item from section 1 was actually completed in this
session, which is why `done_earned` starts at 1 rather than 0 below.)

### 4. Dev/QA note leaking straight into player-facing text

    {"cmd":"why","id":"water_power_scale"}

Reply `note` field, verbatim:

> "Rome already has this (Barbegal, 16 wheels). What is missing is applying
> it to anything other than grinding grain. Put the bellows, the stamps, the
> paper mill, the boring mill and the lathe on the same shaft. **[AUDIT: this
> node does not declare the capability rung it needs. An automated pass once
> inferred one, and an independent review found that EVERY inferred rung it
> sampled was wrong, so all of them were reverted. The gap is left visible on
> purpose: a missing prerequisite you can see beats a wrong one you cannot.]**"

That bracketed `[AUDIT: ...]` sentence is obviously an internal
data-QA/developer annotation about the content pipeline itself (an "automated
pass" that inferred something wrong, "an independent review", reverted
values) — not in-world flavour text. It's shown to the player through the
ordinary `why` command with no special flag. This is the single most
"unrealistic" thing I found in the sense of breaking the fourth wall: found
on the very first non-trivial item I inspected with `why`, so it is likely
not an isolated case — there are probably more `[AUDIT: ...]` notes lurking
on other nodes with the same authoring gap.

### 5. Slave-buy-then-manumit as a reputation-laundering loop (partial exploit — costed, not free)

    {"cmd":"buy","what":"slaves","n":5}   -> {"ok": true, "bought": 5, "capital": 7434.6}   (cost 1234, capital 8668.6->7434.6)
    {"cmd":"buy","what":"manumit","n":5}  -> {"ok": true, "manumitted": 5, "freedmen": 5, "slaves": 0}
    {"cmd":"state"}                       -> reputation 3.1 -> 4.8, capital UNCHANGED at 7434.6

Manumitting is completely free (no capital cost at all) and gives an
immediate, guaranteed reputation bump (+1.7 the first time, +1.4 the second
time on a repeat of the same buy/free cycle — so it does taper, but it never
costs anything beyond the purchase price of the slaves). So "reputation" is
directly purchasable with capital via a buy-then-immediately-free loop, no
risk, no time delay, no `chance_of_failure` roll at all (unlike almost every
tech). Freed people also make your labour force permanently better
(`artisan_capacity` training target rose from 2.75 to 5.0 the moment the same
5 people flipped from slave to freedmen), at the cost of higher ongoing
`living_cost` upkeep for them from then on. Not "free money", but it is a
completely deterministic, zero-risk way to convert capital directly into
reputation and workforce quality, with no other mechanic (suspicion, scandal,
review) reacting to a founder who is very transparently buying and freeing
slaves back to back purely to farm reputation.

### 6. Things that worked as advertised (tried to break them, could not)

- **`stop` really does forfeit 100% of spend.** Started `water_power_scale`
  (total cost 5085.8), stepped 1 year, `spent` reached 2542.9, then
  `{"cmd":"stop","id":"water_power_scale"}`. Capital before and after the stop
  was identical (3464.0 -> 3464.0) — no partial refund, no residual credit
  toward anything else, no side-channel to recover the sunk cost. Correctly
  brutal, as documented ("losing what you have spent").
- **`bounty` is a real premium, not a shortcut.** `{"cmd":"bounty","id":"water_power_scale"}`
  quoted "needs about 12714 denarii" versus a build cost of 5085.8 for the
  same tech — bounty is ~2.5x the DIY price here, so there's no "pay someone
  else, it's cheaper" trick available; it correctly refuses if you can't
  afford it rather than letting you go into debt for it.
- **`buy slaves`/`buy mine`/`buy forest` are gated up front.** Tried
  `{"cmd":"buy","what":"slaves","n":5}` with insufficient capital and got a
  clean refusal (`"cannot afford 5 slaves: 1234 denarii ... and you have
  184"`) rather than silently letting me go negative. Price also rises with
  purchase size ("the market moves against a purchase this size") and
  persists somewhat between purchases rather than instantly resetting, so you
  can't cheaply grind slave-buying either.

### 7. THE BIG ECONOMIC EXPLOIT — `start` never checks whether you can afford the project, at all

This is the most exploitable thing I found, and unlike #2 it *is* a
repeatable, at-will lever the player can pull any time.

While sitting at **capital 3483.6**, I issued three `start`s back to back for
projects whose *listed* costs alone total roughly 12,573 denarii
(`fin_postal_service` 4609.6, `civ_monumental_stone` 4455.0, `fin_inn`
3508.8) — nearly 4x my cash on hand:

    {"cmd":"start","id":"fin_postal_service"}     -> {"ok": true, "started": "fin_postal_service", ...}
    {"cmd":"start","id":"civ_monumental_stone"}   -> {"ok": true, "started": "civ_monumental_stone", ...}
    {"cmd":"start","id":"fin_inn"}                -> {"ok": true, "started": "fin_inn", ...}

Every single one is accepted unconditionally — no "can you afford this"
check exists for `start` the way it demonstrably does exist for `buy`. I
pushed this much further a bit later: at **capital 6414.8** I started seven
more big-ticket items at once —

    fin_chain_store 34854.5, tl_windscreen_wiper 15575.5, tx2_watch_case 13060.9,
    fin_plantation 9993.1, fin_theatre_business 7631.4, mil_artillery_piece 6797.7,
    fin_hotel 5776.7

— a combined listed cost of **93,689.8 denarii against 6,414.8 in the
treasury** (about 14.6x over budget), all seven `start`s returned `"ok":
true` with no warning.

What actually happened when I stepped time forward:

    {"cmd":"step","years":1}
    -> year 134, capital: 0.0, project_spend_last_year: 51195.4, scandal: 0.65 (up from 0)

    {"cmd":"step","years":4}
    -> year 138, capital: -2910.4, revenue: 16720.5, scandal: 1.05
       completed: tl_windscreen_wiper, tx2_watch_case, fin_theatre_business,
                  mil_artillery_piece, fin_hotel, fin_plantation  (6 of 7 done)

So the engine spent **51,195.4 in a single year** against a treasury that
never held more than a few thousand, capital was allowed to swing to a
genuinely negative **-2910.4**, and yet:

- No bankruptcy, no forced project cancellation, no game-over, no error of
  any kind.
- Every project still completed on its own schedule as if fully funded.
- The *only* visible consequence was a slowly-climbing `scandal` stat
  (0.0 -> 0.65 -> 1.05) — a number I never saw explained or connected to any
  penalty in anything I tried. Reputation, meanwhile, kept climbing anyway
  (13.5 -> 22.1) because each completed business adds its own reputation
  bonus, so being reckless with money was net *good* for my reputation in
  this run.
- Capital self-repaired within a handful of years purely because the newly
  completed businesses immediately started generating heavy `revenue`
  (778.2/yr at the start of this experiment -> 16,720.5/yr four years later).

Net effect: the game's own stated premise — "Building it is not [free]: it
takes your own hours, other people's hours, money, materials" — is not
actually enforced for money. You can start an unlimited pile of expensive
projects you have no way to pay for today, run a large operating deficit
(capital below zero) with only a mild cosmetic `scandal` tick as
consequence, and let tomorrow's revenue from those very projects bail you
out. This is a "debt spree" strategy: front-load as many `start`s as your
`founder_hours_available` (2400/yr) can service in parallel, ignore capital
entirely, and let completions snowball your revenue to cover the deficit
after the fact. It never once produced a refusal, an error, or any
consequence worse than a slowly rising number I couldn't find a use for.



