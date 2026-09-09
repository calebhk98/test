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

By contrast, **founder-hours *are* honestly and visibly rationed.** In a
follow-up test I started 8 more projects at once needing 900+500+450+400+
300+300+300+300 = 3450 founder-hours against only 2400 available that year.
Unlike money, `start` still accepted all 8 unconditionally, but the actual
hour allocation after `step 1` showed real contention: `hot_air_balloon`
(400h) and `mfg_punch_press` (300h) got fully funded down to 0 left, two
small projects (`units_standards`, `fud_whaling_industry`, 300h each)
finished outright and dropped off the active list, `identity_cover` and
`water_power_scale` got partially funded (325/500 and 225/450 left), and
`arrival_orientation` — the single biggest ask at 900h — got **zero** hours
that year (900/900 left, no progress at all), and a pre-existing project
(`fin_chain_store`) that had been ticking along also stalled (40/200 left,
unchanged). So the engine clearly *does* implement a real, contested
resource-allocation pass for founder-hours (with some scheduling bias toward
finishing cheap projects first, apparently at the expense of big or
already-running ones) — it just doesn't do the equivalent thing for money.
That inconsistency (hours are honestly scarce, capital is not) is itself
worth flagging: the fix for the debt-spree exploit above is presumably to
give `start`/the yearly project-spend pass the same kind of hard budget
constraint that `founder_hours_available` already visibly enforces.

---

## Summary (end of this sitting)

Session left at **year 139**, capital 0.0, revenue 17,711.2/yr, reputation
24.2 (started at 5.0), scandal 0.95, done_count 157, 7 projects mid-flight,
founder still alive, game not ended. State is fully persisted in
`han_china_100ad_WEIRD.json` and can be resumed at any time with the same
start command.

**Biggest bug/silly-result found:** `start` places zero check on whether the
founder can afford a project, ever — unlike `buy`, which does check.
Capital can and does go negative with no bankruptcy, no forced cancellation,
and no real penalty (just a slow-climbing, apparently inert `scandal`
number), while `founder_hours_available` is a genuinely enforced, contested
resource in the same code path. Net effect: a "debt spree" — start every
expensive thing you can see the instant you see it, regardless of your
treasury — is a strictly dominant strategy over playing it safe, since new
projects' own revenue reliably bails out the deficit they created and being
broke has (as far as I could find) no real downside. See section 7.

**Second biggest:** the game silently owes the Han-China start a backlog of
roughly 128 "ambient" technologies that do not show up in `state.done_count`
at turn 0, and only get dumped in all at once the instant you call `step`
for the very first time — no matter how small that step is, and even if you
start and do nothing else. See section 2. This makes turn-0 `state` actively
misleading about your true position.

**Funniest/most immersion-breaking:** a literal developer QA/audit comment
(complete with "[AUDIT: ... an independent review found that EVERY inferred
rung it sampled was wrong, so all of them were reverted...]") is shown to the
player as if it were in-world flavour text, on the very first non-trivial
item I inspected with `why`. See section 4.

**Most unrealistic (thematically):** the founder is a single named person
who is explicitly the load-bearing resource in this game ("you are one
person") yet survives, unaged and unremarked upon, from 100 AD clear through
to the 600 AD horizon with zero aging, retirement, succession, or death
mechanic ever triggering, even over 500 years of pure inaction. Also, event
flavour text for a Han-China game is inconsistently Rome-flavoured
("fire in the insula district" — insula is a Roman apartment block — and
Roman-named starting techs like `fin_argentarii`/`civ_arch_roman` showing up
in a Han China `available` list), while other events correctly reference
Han-specific history (Yellow Turban rebellion, dated exactly 184-205 AD).

**Tried hard and could NOT break:** `stop` (100% loss of sunk cost, no
partial refund, no bug found); `bounty` (correctly priced at a ~2.5x premium
over DIY, correctly refuses if unaffordable); `buy slaves`/`buy mine`/`buy
forest` (all correctly gated on affordability up front, with a rising
market-impact price that persists between purchases rather than resetting
for free re-grinding).

**What I'd change:** give `start` the same affordability check `buy`
already has (or explicitly design "financed" projects as a real mechanic
with real interest/risk, rather than an accidental free one); make scandal
from running a deficit actually bite (visible cap on suspicion/state
interest, or an actual bankruptcy state); populate turn-0 `state` with the
real starting tech count instead of a number that jumps 12x on the first
`step`; add a founder-mortality/succession mechanic given the game's whole
framing is "you are one person"; and sweep the KB text for other leaked
`[AUDIT: ...]`-style developer notes, since finding one on the first item I
inspected suggests there are more.



