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


