# Playing it badly on purpose: rome_100ad_WEIRD

Session file: `/home/user/test/rome/playtest/naive/rome_100ad_WEIRD.json`
Started: 2026-09-09

Goal: find silly/broken/exploitable results in the simulator, not to win well.
Rules followed: only interacting with the running process (stdin/stdout JSON),
never reading source or other playtest files. Not changing any repo files
except this note file and the session json the game itself writes.

## Setup

Started the simulator with:
```
cd /home/user/test
python3 rome/sim/simulator.py agent --civ rome_100ad --fog --session /home/user/test/rome/playtest/naive/rome_100ad_WEIRD.json
```
(Actually run via a FIFO + background process from the harness since the tool
here can't hold an interactive stdin open across calls, but this is exactly
equivalent to running the command above and typing lines into it.)

Startup banner confirms: one person with modern knowledge, pre-industrial
Rome 100 AD, must spend hours/money/materials/years to build things. Turn
model: nothing happens until you `step <years>`. Commands: state, available,
why <id>, start <id>, stop <id>, step <years>, buy, bounty <id>, path <id>
(disabled under fog), save/load, help, quit. Fog of war is ON.

Notable from the top: `buy slaves` and `manumit` are explicit game mechanics.
The economy section literally justifies slavery as a mechanic "because it was
the ordinary condition of production ... a model that hides it lies about the
cost of everything." Worth noting as a design choice, not exploiting it yet.

## Log

### 1. Ambient "Rome already has this" background tech (not an exploit, but worth flagging)

The `available` list contains ~113 zero-cost, zero-hour entries whose summary
is literally "ROME ALREADY HAS THIS" (e.g. `cap_heat_0700`, `mat_bronze`,
`lnd_wheel_spoked`). I started one of these (`cap_heat_0700`, the pottery
kiln) with:
```
{"cmd":"start","id":"cap_heat_0700"}
{"cmd":"step","years":1}
```
Result: not just that one item completed — 137 *other* unrelated
already-has technologies auto-completed in the same step (`done_granted:
137`, `done_earned: 1`), and `revenue` jumped from 0.0 to 666.7/year out of
nowhere, `reputation` 5.0->5.4, `familiarity` 0->0.302, with no player
action behind any of it.

I suspected this was caused by starting the kiln, so I opened a second,
throwaway control session (`ctrl_session.json`, kept outside the repo in the
scratch dir, not part of the deliverable) and did `{"cmd":"step","years":1}`
as the *very first command*, no `start` at all. Same result: 139 techs
auto-granted, revenue still 666.7. So this is **not** something I triggered
— it's unconditional background/ambient history that happens every year
regardless of what the player does. Interesting/unrealistic bit: this
"ambient" 666.7/year (later 1000, 1200...) of revenue appears with zero
buildings, zero trade, zero mines, zero staff beyond the starting 1
scholar/3 artisans — there's no visible in-fiction source for it (no line
item explaining where it comes from). Also odd: `capital` in the `state`
reply lags one step behind the displayed `revenue`/`net_per_year` — those
fields describe the *upcoming* year's rate, while `capital` reflects last
year's net already applied. Confirmed by checking capital before/after
successive steps (400 -> 184 after living_cost 216 was deducted but before
that year's 393.9 net was added; next step capital becomes 577.9 =
184+393.9). Not a bug, just worth noting as something a player could easily
misread as "my money vanished".

### 2. FOUND IT: `el2_sonar_acoustic_detection_ranging` — Roman sonar, year ~103

Dumped `available` (300+ ids) and ran `why` on every non-free entry to
compare cost/upkeep/revenue. One item is a wild outlier:

```
{"cmd":"why","id":"el2_sonar_acoustic_detection_ranging"}
->
{"id": "el2_sonar_acoustic_detection_ranging", "name": "Sonar acoustic
 detection and ranging", "tier": 4, "cat": "application",
 "note": "Frequency 20 kHz to MHz for resolution; attenuation in water
 limits range; multibeam arrays scan volume; target motion analysis
 reveals speed.",
 "kb": "50_electricity.md",
 "founder_hours": 180.0, "hired_labour": {"engineer": 450.0}, "materials": {},
 "cost": {"total": 208.2}, "upkeep": 4.0, "revenue": 15000.0,
 "calendar_floor_years": 3.5, "risk": 0.17,
 "staff_needed": {"scholars": 0.0, "artisans": 3.0},
 "direct_prerequisites": [], "missing_prerequisites": [], "chain_size": 0,
 "can_start_now": true, "start_blocked_reason": null}
```

This is a *tier 4* electronics technology (`kb: 50_electricity.md` — sonar,
20 kHz-MHz acoustic ranging, target motion analysis: this is 20th-century
naval technology) sitting with **no prerequisites at all** and directly
startable in year 100-103 AD by one Roman-era polymath. For comparison, every
other revenue-generating item I sampled across the whole available list
tops out around 500-1000 net-revenue/year for similar or higher cost. Sonar
costs 208.2 capital / 180 founder-hours / 3.5 years, 4/year upkeep, and pays
**15,000/year** revenue — roughly 15-20x the next best thing in the entire
sample, for a bottom-of-the-list acquisition cost. This has to be a data
entry error in the tech tree (a misplaced digit, or a template revenue
value that was never scaled down for how anachronistic/uncosted the tech
actually is), not an intentional design choice. There's also an internal
inconsistency in the entry itself: `hired_labour` names an `engineer` role
(450 units) but `staff_needed` asks for `artisans` (3.0), not engineers or
scholars — the two labour fields don't agree on who is actually doing the
work.

Testing what happens when you actually build it below.

**Built it.** Commands and results, exact:

```
{"cmd":"start","id":"el2_sonar_acoustic_detection_ranging"}
-> {"ok": true, "started": "el2_sonar_acoustic_detection_ranging",
    "founder_hours_needed": 180.0, "calendar_floor_years": 3.5}

{"cmd":"step","years":4}
-> year 107, capital 4068.3, project still active (founder hours trickle
   in slowly — only ~27/year of the 180 needed got applied over 4 years,
   so the founder's 2400 hours/year is mostly consumed elsewhere, maybe by
   "living"/overhead, not fully explained anywhere)

{"cmd":"step","years":5}
-> "completed": [{"id": "el2_sonar_acoustic_detection_ranging", ... "year": 110}]
   year now 112 (multi-year step, it finished partway through and kept
   simulating), capital JUMPS from 4068.3 to 16457.0 in that single step,
   revenue field now 16665.4/year, net_after_project_spend 15134.6/year.

{"cmd":"step","years":1}
-> year 113, capital 31591.6 (16457.0 + 15134.6, exactly last year's net).
   revenue steady at 16665.4/year.
```

So: a Roman polymath in the reign of Trajan spends 208 sesterces-equivalent
and about a year's worth of spare hours, and by 110 AD is personally
sonar-mapping the Mediterranean seabed for a **permanent, recurring
15,000+/year windfall** — roughly 20x the entire rest of the starting
economy's income, forever, with 4/year upkeep. Two more steps and capital
goes 4,068 -> 16,457 -> 31,591. This is compounding: with this much idle
capital I can now buy out essentially the entire remaining tech tree (309
items, median cost in the hundreds) with cash left over, constrained only by
founder-hours and calendar years, never again by money. I did not even need
to touch `bounty` (paying someone else to build it) — building it myself was
already free money.

Expected: an anachronistic tier-4 electronics item like this should either
(a) not be reachable this early (locked behind centuries of prerequisites
that don't exist for it — `direct_prerequisites: []` is itself suspicious
for a tier-4 item), or (b) if reachable, have a return in line with
everything else in the tree (tens to low-hundreds per year, matching every
other "application" tier item I sampled). Instead it is a straightforward
economy-breaking outlier, almost certainly a stray extra zero (or a
copy-pasted placeholder revenue value) in the tech database, not an
intended reward for reaching tier 4 electronics. This is the headline
finding of this playtest.

`knowledge_risk.technologies_at_risk` did tick from 0 to 1 once sonar was
done (it's an un-hedged single point of failure, 80% loss chance / 40%
technologies lost if a "site" is sacked) — so the game *does* track that
this windfall is fragile. But nothing stops you from banking a few years of
its income, which then sits safely as capital rather than as
at-risk "knowledge", before any hazard in the timeline (first one listed is
the Antonine plague in 165) can touch it.

### 3. A second, smaller money-for-nothing item: `fin_seigniorage`

Ranked second in my "biggest net revenue minus upkeep" scan, behind only
sonar:

```
{"cmd":"why","id":"fin_seigniorage"}
-> "Seigniorage and debasement" (tier 2, money). note: "Profit from issuing
   new money... Short-term profit destroys long-term monetary trust."
   cost.total 25.0, upkeep 0.0, revenue 1000.0/year, calendar_floor_years 0.2.

{"cmd":"start","id":"fin_seigniorage"}
{"cmd":"step","years":1}
-> completed same year (2026-... i.e. game year 113). revenue jumped
   16665.4 -> 17347.0/year. capital kept climbing at ~15,300/year after.
```

Unlike sonar, this one is thematically justified in-world (debasing coinage
really was a real revenue source for emperors) — but the game's own note
text warns about long-term trust being destroyed, and nothing mechanical
ever charges that price: no reputation hit, no inflation, no trust/loyalty
stat exists to spend down. It is worth pointing out that "Currency
debasement, 190-275" is literally listed among the game's own future
`known_hazards_ahead` — the simulator clearly *knows* debasement has
consequences down the line, it just doesn't apply any of them to a player
who deliberately debases 90 years early for free money. For 25 capital and
zero ongoing upkeep, once built, `fin_seigniorage` is close to a strictly
dominant move for anyone who has unlocked coined money (which, per section
1 above, everyone has by year 100 automatically).

## Things I tried hard to break and could NOT

- **Refund-by-stop.** Started `sc2_notation_decimal_point` (cost 249.6,
  2-year floor), stepped 1 year (134.2 already spent and already deducted
  from capital), then `{"cmd":"stop", ...}`. Capital before and after the
  stop was identical (61408.3 -> 61408.3): the spend from the step you already
  took is not refunded, exactly as the help text warns ("stop: abandon it,
  losing what you have spent"). No free-cancel exploit here. You *can*,
  however, `start` then immediately `stop` an item with **no** step in
  between at zero cost — since spend is only applied during `step`, this
  works as a free zero-risk way to "peek" at `founder_hours_needed` /
  `calendar_floor_years` beyond what `why` already tells you, which is a
  non-issue since `why` already exposes that.
- **Buying at unlimited scale.** `{"cmd":"buy","what":"slaves","n":1000}`
  was refused outright: `"cannot afford 1000 slaves: 2806111 denarii (2806
  each after the market moves against a purchase this size) and you have
  31026"`. There is real price-impact scaling on bulk slave purchases
  (~307 denarii each at n=1, ~2806 each at n=1000, a ~9x markup) and a hard
  affordability check that blocks the purchase outright rather than letting
  capital go negative. Good, sane guard.
- **Negative/zero quantities.** `buy` with `n=-5` or `n=-1` (manumit) is
  rejected cleanly: `"n must be greater than zero, got -5. Nothing was
  changed."` No sign-flip exploit. (Minor rough edge, not an exploit: `n=0.5`
  slaves gets floored to 0 somewhere and produces a confusing error message,
  `"cannot afford 0 slaves: 0 denarii ... and you have 31026"`, instead of
  a clean "fractional slaves not allowed" message.)
- **Re-completing a finished item for repeat rewards.** Tried
  `{"cmd":"start","id":"cap_heat_0700"}` and
  `{"cmd":"start","id":"el2_sonar_acoustic_detection_ranging"}` again after
  both were already done: both cleanly refused with `"already done"`. No
  way to re-trigger the same completion bonus/revenue-add repeatedly.
- **Bounty as a cost-shortcut.** Tried `{"cmd":"bounty","id":"horse_collar"}`,
  a bounty-eligible item that costs 709.4 to build yourself. The bounty
  price was 1773.5 — about 2.5x self-build cost — and it *still* required
  70 of 200 founder-hours afterward (bounty only bought down part of the
  hour requirement, not all of it). So bounty is a real (if pricey)
  convenience, not a way to dodge founder-hours entirely, and not cheaper
  than building yourself when you can afford the capital. Also tried
  bountying `sc2_notation_decimal_point` (tier 1, "notation" category):
  refused with an in-fiction reason, `"not bounty-eligible (tier 1,
  category notation): a Roman artisan could not recognise success at
  this"` — a nice touch, and correctly gated by the `bounty_eligible_by_type`
  flag `why` already exposes.
- **`step years:0`** to try to get a "free" instant-complete tick without
  paying a year's living cost: rejected, `"years must be >= 1"`.

## Overall impressions / things I'd flag to whoever maintains this

1. **`el2_sonar_acoustic_detection_ranging` is a real balance bug**, not
   just a fun anachronism. A tier-4, no-prerequisite electronics item that
   nets 15,000+/year for a 208-capital, ~1-year investment, when every
   other revenue-bearing item I sampled across the whole tech tree (~300
   items) tops out in the hundreds per year, breaks the entire economic
   pacing of the game once you notice it. It should almost certainly either
   require centuries of prerequisites it currently lacks, or have a revenue
   figure with two or three fewer zeroes.
2. **`fin_seigniorage`** is a smaller, thematically-motivated version of the
   same problem: real money for (nearly) nothing, with the in-fiction
   downside (destroyed monetary trust) described in the flavour text but
   never enforced by any stat.
3. The **ambient "Rome already has this" background completions** (~113-140
   items that complete for free regardless of anything the player does,
   each step) are not exploitable by the player, but they are a strange
   design choice worth a second look: they hand the player ever-growing
   baseline `revenue`/`reputation`/`familiarity` (0 -> 666.7/yr by year 101
   just from time passing) with literally nothing built, no economy
   modelled behind it, and no in-fiction explanation offered anywhere in
   `state`, `why`, or the startup banner for where that money is coming
   from. A player who never issues a single `start` still gets richer every
   year. It doesn't feel like an exploit so much as a hole in the game's own
   fiction: "you have built nothing, and Rome pays you anyway."
4. Field naming is a little inconsistent and easy to misread: `state.capital`
   lags one full year behind `state.revenue`/`state.net_per_year` (the
   latter two describe the year about to happen, not the year just
   finished), which had me double-checking arithmetic more than once.
5. `hired_labour` and `staff_needed` don't always agree on who does the
   work (sonar wants an `engineer` in `hired_labour` but `artisans` in
   `staff_needed`) — cosmetic, but a sign the tech entries may be
   templated/generated rather than hand-checked individually, which is
   consistent with a stray-zero bug like the sonar revenue slipping through.

## Final state snapshot (year 117, still running)

capital 90,695.3; revenue 19,013.0/year; net_per_year 16,031.3; reputation
12.5; suspicion 2.0 (first time nonzero — appeared after the `bounty` call,
or possibly from wealth/eminence accumulating; did not chase down which);
eminence 0.79; done_count 143 (138 granted "ambient", 5 actually built:
kiln, amputation, sonar, seigniorage, horse collar); 1 forest ha; 1 t/yr
coal mine commissioned; 0 slaves / 1 freedman (bought 1 slave earlier for
the buy-mechanics test, it shows as a freedman now rather than a slave —
did not chase down whether that's an automatic-manumission mechanic or a
side effect of something else; flagging as unexplained rather than
claiming it as a finding). Session continues to accrete free money every
year from the sonar + seigniorage combo with nothing further required from
the player.



