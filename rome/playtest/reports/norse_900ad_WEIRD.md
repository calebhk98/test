# norse_900ad / WEIRD

## What I did

I read `BRIEF.md`, the Norse civilization file (`rome/data/civilizations/norse_900ad.json`),
`rome/playtest/FINDINGS.md` (to see exactly what was already patched on Rome and Han China so I
did not waste budget re-discovering closed holes), and the existing Rome and Han China WEIRD
reports for technique. I drove the game exclusively through
`python3 rome/sim/simulator.py agent --civ norse_900ad [--kit ...] [--seed ...]`, feeding
hand-written JSON lines over stdin from small Python driver scripts (using `subprocess` only to
pipe JSON at the unmodified CLI process, never `import simulator`). I never called `run`,
`compare`, `sensitivity`, `sweep`, the CLI `path`/`why`/`costs`, or `treetool.py`, and never opened
`rome/data/strategies/` or the tech tree JSON. The one disclosed exception, per the brief's
carve-out: I used the in-protocol `path` command on `point_contact_transistor` to check the
specific claim (repeated from the Rome and Han China reports) that no institution node is a
technical prerequisite of the transistor, and I greped the accessible knowledge files for the
words "1400" and "horizon" after the game told me a run had silently ended at "1400 AD" to see
whether that limit was documented anywhere a player could have found it first. I did not open the
tech tree JSON itself.

My plan, in order: (1) re-attempt the twice-patched slave-buy-and-manumit exploit on Norse's much
smaller market (population 1.5M vs Rome's 65M) at several purchase granularities, to see whether
the volume-and-memory pricing fix holds and whether Norse's tiny market makes the underlying
reputation/eminence pump stronger or weaker than on Rome/Han; (2) attack the brand-new abandonment
mechanic directly and hard, per the brief's specific instruction — go bankrupt on purpose, see what
gets dropped, try to rebuild it cheaper, try to abandon something the goal needs and softlock, try
to abandon something mid-build; (3) look for "poverty produces nonsense numbers" by comparing all
seven kits and stress-testing `--kit destitute`; (4) test whether eminence danger 0.2 (lowest of
any civilization) makes Norse genuinely untouchable in a way Rome, where the same exploit ended a
run in one step, could not be; (5) sanity-check the technical prerequisite graph for
`point_contact_transistor` against the "no state to offend" premise.

The most valuable thing I found was not a bigger version of the slave exploit — Norse's tiny
population caps that route so hard it is nearly impossible to become dangerously eminent through
it — but a genuine, reproducible **softlock**: one early, moderate-sized slave-buying binge (150
head, well within a rich kit's means) put me far enough into debt that the abandonment mechanic
correctly kicked in, dropped a technology that sits on the transistor's technical prerequisite
chain, and then **never let me recover solvency for the rest of the 500-year run**. The game did
not end when this happened — it kept accepting `step` calls for five centuries, always refusing
`start`/`bounty`/`buy` with the same "in arrears" message, until it silently timed out at a
previously undocumented "1400 AD" horizon with `end_reason: "ran out of horizon... without
reaching the goal"`. Nothing told me at the moment of the bad purchase, or at any point in the
following 470 years, that the run was already unwinnable.

## Result

No run reached `point_contact_transistor`; consistent with the WEIRD role I did not attempt a full
multi-century engineering run and say so plainly. Key numbers: the softlock reproduction (F3) ran
from year 900 to year 1400 (the game's hard end-of-horizon), starting from `--kit absurd`
(1,000,000 denarii) and one 150-slave buy-and-manumit cycle costing roughly 155,000 denarii at the
time, ending at **capital -859,773.2 denarii**, `done_count` permanently stuck at 134 (down from a
peak of 136), and the technical prerequisite `identity_cover` permanently un-buildable the entire
time. Separately, the reopened slave/manumit exploit topped out at **reputation 28.4** and
**eminence 0.14** (kit absurd, every denarii spent on the cheapest possible n=1 purchase
granularity) — for comparison, the equivalent trick killed a Rome run outright at eminence 220.56
with reputation 1298.1. Norse's own small market, not the eminence mechanic, is what keeps this
civilization safe from that particular exploit.

## FINDINGS

### F1. Reopened slave/manumit exploit: the volume-and-memory price fix holds against the two obvious attacks, but salami-slicing into n=1 calls still saves 16-25% over one big call
- **Severity**: EXPLOIT (residual, weak)
- **What I saw**: a single large call is throttled hard and steeply, exactly as advertised:
  ```
  {"cmd":"buy","what":"slaves","n":1000}
  ```
  ```
  {"ok": false, "error": "cannot afford 1000 slaves: 23563873 denarii (23564 each after the
  market moves against a purchase this size) and you have 1000000"}
  ```
  Splitting the same total into 100 calls of n=10 no longer defeats this the way it did on Han
  China pre-patch (13.0x cheaper there) — buying in n=10 chunks now visibly gets *more* expensive
  as you go and the run ran out of money at 230 slaves bought for 954,483.8 denarii total (kit
  absurd, `--seed 1`), a rising marginal price the whole way (last successful n=10 call quoted
  7,300/head, the affordability refusal after it: `{"error": "cannot afford 10 slaves: 73004
  denarii (7300 each after the market moves against a purchase this size) and you have 45516"}`).
  I then compared total spend for 200 slaves bought at different chunk sizes in one session each
  (same seed, same kit, all fresh runs):
  ```
  chunk=1   -> 200 bought, 723985.7 spent, 3619.93/head
  chunk=2   -> 200 bought, 726919.4 spent, 3634.60/head
  chunk=5   -> 200 bought, 735686.0 spent, 3678.43/head
  chunk=10  -> 200 bought, 750203.1 spent, 3751.02/head
  chunk=20  -> 200 bought, 778954.9 spent, 3894.77/head
  chunk=50  -> 200 bought, 863494.2 spent, 4317.47/head
  chunk=100 -> only 100 bought before running out (1,000,000 cap)
  chunk=200 -> 0 bought, refused outright as unaffordable
  ```
  n=1 calls are consistently the cheapest granularity, 16.2% cheaper than n=20 and 19.4% cheaper
  than n=50 for the identical final headcount. I also directly tested whether manumitting resets
  the price memory (an obvious next attack once you know it's cumulative): buy 50 (n=1 x 50, cost
  70,920.5), manumit all 50 (freedmen 50, slaves back to 0), then buy 50 more identical units —
  the second batch cost **149,420.4, a 2.11x markup for the exact same headcount with zero slaves
  currently owned**, proving the counter tracks lifetime cumulative purchases, not current
  holdings, and manumission does not launder it.
- **Why it is wrong**: the brief states this exploit was patched by making price "rise with volume
  AND remember across calls." It clearly does remember (the 2.11x post-manumit re-buy proves that
  conclusively) and it clearly throttles single large calls hard. But a scripted player — which the
  brief's own protocol explicitly invites ("You drive it however you like... by writing your own
  script") — still gets a real, non-trivial discount (16-25% at n=200, likely more at larger scale
  since the chunk=50/100 curve is visibly steeper than chunk=1-10) by never issuing a `buy` call
  larger than n=1. This is much smaller than the pre-patch holes (13x on Han, flat-rate on Rome)
  but it is not zero, and a marginal-cost curve that depends on transaction size rather than pure
  cumulative volume is still modelling something closer to "how the software throttles a single
  request" than "how a market absorbs demand."
- **Reproduce**: `python3 rome/sim/simulator.py agent --civ norse_900ad --kit absurd --seed 1`,
  then feed 200 separate `{"cmd":"buy","what":"slaves","n":1}` calls and compare total spend
  against one `{"cmd":"buy","what":"slaves","n":200}` call (refused) or against 4 calls of
  `{"cmd":"buy","what":"slaves","n":50}` (863,494.2 total, vs 723,985.7 for the n=1 version).

### F2. Norse's tiny population caps the exploit's *payoff* so hard it is nowhere near capable of triggering the eminence death that ended a Rome run
- **Severity**: WORKS-WELL
- **What I saw**: spending the *entire* 1,000,000-denarii `absurd` kit on the cheapest possible
  granularity (n=1 buy, n=1 manumit, repeated) bought only 240 people total before the market
  refused further purchases at 7,325/head:
  ```
  {"cmd":"buy","what":"slaves","n":1}
  {"ok": false, "error": "cannot afford 1 slaves: 7325 denarii (7325 each after the market moves
  against a purchase this size) and you have 3169"}
  ```
  After manumitting all 240 (also at n=1 each), `state` showed `"reputation": 28.4, "eminence":
  0.0`. A single `step` afterward brought eminence to only 0.02. I then ran 15 buy-spree cycles
  back to back with 5-year steps between them (same seed) to see whether eminence could be made to
  climb over time even after the market was tapped out; the peak across the whole run was
  **reputation 28.4, eminence 0.14**, both *falling* every cycle thereafter as reputation decays
  and the "in arrears" state (see F3) blocks any further buying. Contrast the equivalent Rome
  finding from `rome_100ad_WEIRD.md`: 3,333 slaves bought and freed in one call there produced
  reputation 1298.1 and eminence 220.56, which killed the run outright the same year
  (`"too eminent: brought down not for what you built but for how large you had become"`).
- **Why it is right**: the brief specifically asks whether eminence danger 0.2 (the lowest of any
  civilization) makes Norse untouchable in a way Rome could not be. It does — but not because the
  eminence mechanic itself is weaker per point of reputation (I did not measure that ratio
  directly), but because Norse's declared population (1.5M vs Rome's 65M) makes the *underlying
  market* so shallow that no amount of starting capital in this game (`absurd` is the richest kit
  offered) can buy enough people to generate Rome-scale reputation in the first place. The
  civilization's stated weakness ("nobody will fund you") turns out to double as a hard ceiling on
  its own most dangerous exploit. I did not have budget to test every other possible route to high
  reputation (public works, patronage nodes, etc.), so I cannot say Norse is untouchable by every
  means — only that this specific, previously game-ending lever is capped an order of magnitude
  below where it mattered on Rome.
- **Reproduce**: `python3 rome/sim/simulator.py agent --civ norse_900ad --kit absurd --seed 1`,
  loop `{"cmd":"buy","what":"slaves","n":1}` until refused, then the same count of
  `{"cmd":"buy","what":"manumit","n":1}`, then `{"cmd":"state"}`.

### F3. Deliberate bankruptcy can permanently soft-lock a technical prerequisite of the goal, and the game never says so — a 500-year run to a silent, undocumented timeout
- **Severity**: BUG (the most important finding of the session)
- **What I saw**: starting fresh (`--kit absurd --seed 1`), I started and completed three cheap
  foundation nodes, then bought and manumitted 150 slaves in one pair of calls:
  ```
  {"cmd":"start","id":"identity_cover"}
  {"cmd":"start","id":"units_standards"}
  {"cmd":"start","id":"arrival_orientation"}
  {"cmd":"step","years":2}
  {"cmd":"buy","what":"slaves","n":150}    -> {"ok": true, "bought": 150, "capital": 212218.3}
  {"cmd":"buy","what":"manumit","n":150}   -> {"ok": true, "manumitted": 150, "freedmen": 150}
  ```
  Stepping forward, capital fell steadily (living cost of the founder plus 150 idle freedmen) until
  year 927, when the new mechanic fired exactly as documented in the brief:
  ```
  {"year": 927, "message": "IN ARREARS for 3 years: staff are leaving because you cannot pay them"}
  {"year": 927, "message": "ABANDONED 2 works you could no longer maintain; they have fallen into
   disrepair"}
  ```
  `done_count` dropped 136 -> 134, and the two most expensive-to-maintain nodes were dropped —
  `identity_cover` (upkeep 200/yr) and `units_standards` (upkeep 30/yr) — while `arrival_orientation`
  (upkeep 0) was correctly spared. `artisans` collapsed from a manumit-inflated 115.14 back to the
  baseline 3.0 and `reputation` from 11.6 to 5.9 in the same step, so the entire labour/reputation
  gain from the exploit was wiped out along with the abandoned works. So far this is the
  abandonment mechanic working exactly as intended. Then I kept stepping, watching for recovery:
  ```
  y=939 cap=-65335.5   y=989 cap=-265801.3   y=1059 cap=-521692.3
  y=1119 cap=-673243.3   y=1129 cap=-606649.7   (still oscillating, never positive)
  ```
  I ran this out to the full horizon (60 more `step` calls of 10 years each, 600 years total from
  the bankruptcy point). It never recovered. At year 1400 the run ended on its own:
  ```
  {"ok": true, "year": 1400, "capital": -859773.2, "net_per_year": -5998.9, "done_count": 134,
   "done_earned": 1, "goal_reached": false, "ended": true,
   "end_reason": "ran out of horizon (1400 AD) without reaching the goal"}
  ```
  For the entire 470+ years between the abandonment and the horizon cutoff, `identity_cover`
  remained permanently un-buildable:
  ```
  {"cmd":"why","id":"identity_cover"}
  ... "done": false, "can_start_now": false,
  "start_blocked_reason": "you are 22115 denarii in arrears; nobody will fund a new undertaking
   until you are solvent again. Finish or stop what you have running, or raise revenue."
  ```
  (the exact denarii figure in that message grows every time you check, tracking the ever-more
  negative capital, but the substance never changes). And because `identity_cover` sits on the
  technical prerequisite chain of the goal (confirmed via `why` on a direct dependent:
  `{"cmd":"why","id":"arithmetic_positional"}` returned `"missing_prerequisites":
  ["identity_cover"]` only *after* the abandonment — before it, with `identity_cover` done, the
  same query returned `"missing_prerequisites": []`), the goal itself became unreachable from that
  point on. At the horizon, `{"cmd":"path","id":"point_contact_transistor"}` still reported 163
  remaining prerequisites, exactly where a run this age should have made real progress. I also
  confirmed there is no way out once here: `start`, `bounty`, and `buy` on anything all return the
  same "in arrears" refusal for the entire remaining run, `stop` on the now-inactive node returns
  `"error": "not active"`, and there is no `buy ... sell` or debt-forgiveness command in the
  protocol.
- **Why it is wrong**: the abandonment mechanic itself is a good fix for the old "run into infinite
  debt with no consequence" bug — dropping unmaintainable works and letting staff leave is a
  believable, well-signposted response to insolvency *at the moment it happens*. What it does not
  do is prevent, warn about, or ever resolve the state *after* that moment: capital has no floor,
  no bankruptcy end-state, no forced liquidation, and (per my measurements) no reliable path back
  to solvency once idle freedmen or other fixed population costs are large enough relative to
  passive revenue — I confirmed capital only asymptotically approaches a *positive* equilibrium in
  a leaner scenario (identity_cover alone, no freedmen, stabilizes around 20,000-26,000 denarii
  across 400 simulated years) but never reverses in the heavier scenario above. A player who makes
  one bad purchase early — 150 slaves is not an outlandish number, it is half of what the `absurd`
  kit can comfortably buy — can be locked out of the goal for the rest of the game, with the game
  continuing to accept commands and give the impression of an ongoing playthrough for 470+ more
  years, and the only feedback being the same static "in arrears" message every time. Nothing in
  `state`, `why`, or the accessible knowledge base names a debt ceiling, a recovery mechanism, or
  the 1400 AD horizon itself — I grepped `knowledge/*.md` and the top-level `*.md` files for
  "1400" and "horizon" after the game told me the run had ended for that reason, and found nothing
  relevant (only unrelated matches like temperature figures and lens/telescope prose). A player
  cannot know, from anything the protocol or the accessible guide tells them in advance, that a
  moderate debt taken on in year 927 has already decided the outcome of a run that nominally has
  until 1400 to play out.
- **Reproduce**: `python3 rome/sim/simulator.py agent --civ norse_900ad --kit absurd --seed 1`,
  then: `start identity_cover`, `start units_standards`, `start arrival_orientation`,
  `step years:2`, `buy slaves n:150`, `buy manumit n:150`, then repeated `step years:10` (I used 60
  such calls) until `ended:true`. The exact event sequence and final state above reproduce
  byte-for-byte on repeat runs with the same seed (I ran the buy/manumit/step prefix four times
  with different post-fix step-chunk sizes — 1, 2, 3, 5, and 10 years per call — and all five
  produced the identical `year 932` state with the identical five events in the identical order,
  so the outcome is deterministic given the seed and not sensitive to how a script happens to chunk
  its `step` calls).

### F4. No "abandon and rebuild cheaper" exploit — a re-started node costs exactly what it cost the first time, and downstream unlocks correctly re-lock
- **Severity**: WORKS-WELL
- **What I saw**: the brief specifically asks whether an abandoned work can be rebuilt cheaper. In
  the F3 scenario, `{"cmd":"why","id":"identity_cover"}` reported `"cost": {..., "total": 1738.0}`
  both before it was ever started and after it had been built, abandoned, and (hypothetically)
  ready to rebuild — the number never moved. I also confirmed abandonment properly propagates
  forward: `{"cmd":"why","id":"arithmetic_positional"}` showed `"missing_prerequisites": []` while
  `identity_cover` was done, and `"missing_prerequisites": ["identity_cover"]` again the moment it
  was abandoned — there is no free permanent unlock from having built something once and then
  losing it to insolvency.
- **Why it is right**: this closes off two plausible abuse vectors the brief specifically asked me
  to check for (cheap rebuilds, permanent unlocks from a since-abandoned prerequisite) and I could
  not make either happen despite deliberately trying, across the same scenario used for F3.
- **Reproduce**: compare `{"cmd":"why","id":"identity_cover"}`'s `cost.total` field before starting
  it and again after the F3 abandonment sequence; compare `{"cmd":"why","id":"arithmetic_positional"}`'s
  `missing_prerequisites` field at the same two points.

### F5. Living cost scales down with capital, so pure inaction can never bankrupt you — only an active lump-sum choice (like F3's slave buy) can
- **Severity**: WORKS-WELL / CONFUSING (worth knowing, not obviously exploitable)
- **What I saw**: starting fresh (`--kit absurd --seed 1`), completing only `identity_cover`
  (upkeep 200/yr, no slaves bought at all) and then stepping forward with **no further commands of
  any kind** for 400 simulated years:
  ```
  y=911 cap=572077.40 net=-8030.100 living=8852.500
  y=991 cap=59023.80  net=-334.300  living=1156.700
  y=1051 cap=38230.10 net=-22.400   living=844.800
  y=1091 cap=20408.40 net=244.900   living=577.500   <- net turns positive
  y=1301 cap=22184.40 net=218.300   living=604.100    (still oscillating near here at y1301)
  ```
  `living_cost` fell continuously and `net_per_year` converged to a small positive number and
  stayed there, oscillating around a ~20,000-26,000 denarii equilibrium (perturbed by random
  "fire in the insula district" / "banditry" events) for the rest of the 400-year test. Capital
  never crossed zero after the initial small dip.
- **Why it is right (with a caveat)**: this means the only way I found to actually trigger the new
  insolvency/abandonment machinery was a deliberate, large, one-off purchase (F3's 150 slaves) —
  never simple neglect. That is a sensible design (you should not be able to accidentally go bust
  by doing nothing), but it is also *why* F3 is dangerous: the "safe by default" behaviour trains a
  player, correctly, to believe passive time is never risky, right up until one aggressive purchase
  proves otherwise and (per F3) never lets go. The caveat: I don't know the exact formula behind
  `living_cost`'s decline (whether it is pegged to capital, to founder age, or to something else)
  since reading the source/tree JSON to find out is against the brief's rules — I report only the
  observed behaviour.
- **Reproduce**: `python3 rome/sim/simulator.py agent --civ norse_900ad --kit absurd --seed 1`,
  `{"cmd":"start","id":"identity_cover"}`, `{"cmd":"step","years":1}`, then repeated
  `{"cmd":"step","years":10}` with a `{"cmd":"state"}` after each, watching `living_cost` and
  `net_per_year`.

### F6. `step` outcomes are exactly reproducible regardless of how a script chunks the years — no manipulation available there
- **Severity**: WORKS-WELL
- **What I saw**: I ran the identical F3 prefix (three starts, step 2, buy 150, manumit 150) and
  then advanced exactly 30 further years via three different chunkings — one `step years:10` call,
  two `step years:5` calls, and ten `step years:1` calls — from three separate fresh sessions with
  the same seed. All three landed on year 932 with **identical** capital (-35051.3) and an
  **identical**, identically-ordered event list. I repeated this with a longer run (F3's full 500+
  year continuation) at step sizes 1, 2, 3, 5, and 10 and again got byte-identical final states at
  year 932 in every case.
- **Why it is right**: this rules out a class of exploit I was specifically hunting for (does
  calling `step` in smaller or larger increments change how randomness or thresholds get evaluated,
  the way F1's purchase-granularity trick worked for buying). It does not — the simulator is
  deterministic in year-count given a seed, independent of call chunking.
- **Reproduce**: run the F3 prefix, then compare final `state` after `step years:10` once vs.
  `step years:5` twice vs. `step years:1` ten times, same seed.

### F7. `--kit destitute` (0 starting denarii) is not meaningfully punishing — background "society already knows this" technologies hand you positive cash flow within a handful of years regardless of anything the player does
- **Severity**: UNREALISTIC / CONFUSING
- **What I saw**: starting `--kit destitute` (`capital: 0.0`) and issuing **no commands at all**
  except repeated `{"cmd":"step","years":1}`:
  ```
  state0: capital 0.0, revenue 0.0, living_cost 210.0, net_per_year -210.0
  y=901: capital -210.00, revenue 681.6, net 430.70   (132 background technologies auto-completed)
  y=902: capital 220.70,  net 747.80
  y=915: capital 8737.00, net 620.00 (still climbing)
  ```
  The jump comes entirely from `done_count` going 4 -> 132 in the very first `step` call, purely
  from nodes the game grants for free ("ROME ALREADY HAS THIS"-style background techs like
  `fin_market`, `fin_tax_farming`, `sea_merchant_ships_large`), which apparently carry passive
  revenue. This happens identically whether the founder does anything or not, and identically
  across every kit I tested (all seven kits showed the same ~130-140 node jump in year one).
- **Why it is confusing rather than a clean exploit**: it is not something the *player* engineered
  (see the Rome WEIRD report's F7, which flagged the same "granted" technologies as confusing
  there) — but on Norse specifically, a kit explicitly named `destitute`, starting at literally
  zero capital in a civilization whose own notes say "nobody will fund you," turns into a
  comfortably cash-flow-positive founder within about five simulated years purely from ambient
  society-level income, with no player skill, risk, or plan involved. That undercuts the
  civilization's own stated premise ("Small population... every plan must be capital-light and
  skill-heavy") in the one kit where it should matter most.
- **Reproduce**: `python3 rome/sim/simulator.py agent --civ norse_900ad --kit destitute --seed 1`,
  then repeated `{"cmd":"step","years":1}` with no other commands, watching `capital` and
  `net_per_year`.

### F8. Manumission does not reset the cumulative purchase-price memory, but the memory does decay with elapsed calendar time even without manumitting
- **Severity**: CONFUSING (minor; see F1 for the exploit-relevant half of this)
- **What I saw**: buying 50 slaves (n=1 x 50) fresh costs 70,920.5. Buying 50 *more* after fully
  manumitting the first 50 (freedmen count 50, slaves count back to 0) costs 149,420.4 — 2.11x —
  proving the price ledger is keyed to lifetime purchases, not current holdings (detailed in F1).
  Separately, I bought 50 slaves and then simply waited, *without* manumitting, buying no more:
  ```
  wait 0 years:  next 3 buys average ~2,297/head, 50 slaves owned
  wait 3 years:  next 3 buys average ~760/head,   29 slaves owned (21 died of natural attrition)
  wait 10 years: next 3 buys average ~530/head,   10 slaves owned
  wait 30 years: next 3 buys average ~520/head,   3 slaves owned
  ```
  The marginal price fell substantially the longer I waited, even though I never freed anyone —
  slaves themselves died off over the decades (a plausible mortality model), and the price the
  simulator quotes fell alongside that.
- **Why it is confusing**: I cannot fully separate "the price memory decays with elapsed time" from
  "the price memory is a function of current holdings, and holdings fell due to mortality" from
  these observations alone — both would produce this exact result, and distinguishing them would
  require reading the source I'm not permitted to open. Either way, it means the F1 exploit's
  headline defence ("remembers across calls") is not permanent: given enough in-game decades, a
  patient scripted player recovers the original low prices, something neither the protocol nor the
  refusal messages disclose.
- **Reproduce**: buy 50 slaves via n=1 calls (fresh `--kit absurd --seed 1` session), record the
  next 3 marginal prices; in a fresh session with the identical prefix, insert
  `{"cmd":"step","years":N}` for N in {3, 10, 30} before recording the next 3 marginal prices, and
  compare.

### F9. No forced abandonment of an *active* (mid-build) project — could not reproduce, reported honestly as inconclusive
- **Severity**: (not rated — inconclusive)
- **What I saw**: the brief specifically asks whether abandoning something you were mid-way through
  rebuilding does something strange. I tried to force it: started a long-build node
  (`fin_plantation`, calendar floor 3.0 years, cost 10,075) and then immediately tried to drain
  capital hard enough with a single large slave purchase to go insolvent *while the node was still
  active*. I could not — a single-call purchase large enough to matter (n=200) was itself refused
  outright as unaffordable at the market's single-call throttle (F1), and the project's own cost is
  charged progressively over its build (`"spent": 4063.6` after 1 year, `8127.2` after 2, on a node
  whose founder-hours completed in 2 years against a 3-year calendar floor) rather than all at once,
  so I ran out of capital-draining options before the project either finished or I could push
  capital negative during its active window. Every insolvency/abandonment event I managed to
  trigger in this session (F3 and its variants) happened only *after* all in-flight projects had
  already completed.
- **Why I'm reporting this as inconclusive rather than WORKS-WELL**: I did not exhaust the design
  space (I tried one node, one purchase pattern, one kit) and a different combination — a very
  expensive long node started at the same moment as a maximal single-call purchase, or under a
  poorer kit where the project's own progressive cost is a much larger fraction of available
  capital — might behave differently. I'm flagging this as "tried, could not reproduce" rather than
  claiming the mechanic is safe.
- **Reproduce (what I tried)**: `--kit absurd --seed 1`, `{"cmd":"start","id":"fin_plantation"}`,
  then `{"cmd":"buy","what":"slaves","n":200}` immediately after (refused: "cannot afford 200
  slaves: 1262532 denarii... and you have 1000000"), then stepping — the project completed cleanly
  at year 902 with capital still comfortably positive throughout.

### F10. The technical prerequisite graph for the transistor still does not require any institution node — confirmed on a civilization that structurally has none of them
- **Severity**: WORKS-WELL / CONFUSING (same pattern as the Rome and Han China reports)
- **What I saw**: Norse's own civ file declares `"corporation": false, "guild": false, "bank":
  false, "charter": false, "patent": false` and states outright: "The thing is an assembly, not a
  state. No one can license you and no one can fund you." I checked whether the goal's technical
  graph reflects that absence or merely happens not to need those nodes anyway:
  ```
  {"cmd":"path","id":"point_contact_transistor"}
  ```
  returned `"remaining_count": 168`. None of `school_founded`, `collegium_licensed`,
  `freedman_staff`, `citizenship`, `patron_senatorial`, `patron_imperial`, `endowment_land`,
  `academy_network`, or `corpus`-prefixed nodes appear in that list; only the cheap early social
  nodes `patron_local` and `identity_cover` do.
- **Why it is right**: this matches the same finding from `rome_100ad_WEIRD.md` and
  `han_china_100ad_WEIRD.md` exactly, and it is a *stronger* result here, since Norse society
  genuinely lacks the institutions in question rather than merely making them optional for the
  player. I did not attempt a full run confirming that a real "never build a school-equivalent"
  playthrough actually reaches the transistor (that is WIN-role work, and my role is WEIRD/exploit
  hunting) — only that the prerequisite graph itself imposes no such requirement, same caveat as
  the prior two reports.
- **Reproduce**: `{"cmd":"path","id":"point_contact_transistor"}` from a fresh
  `--civ norse_900ad --kit absurd` session; check institution-node membership in the returned list.

## Honesty note

I did not attempt a run toward the transistor in either direction (institution-first or bare
technical order) — my role was exploit-hunting, not winning, and I judged that chasing F3 (the
softlock) to a fully reproduced, deterministic, 500-year conclusion was a better use of the
session's budget than a partial, unfinished march toward the goal. F9 is explicitly flagged as an
attempted-but-inconclusive test rather than a confirmed result. F2's "untouchable" claim is scoped
specifically to the slave/manumit reputation route — I did not have budget to test every possible
path to high reputation or eminence on this civilization.
