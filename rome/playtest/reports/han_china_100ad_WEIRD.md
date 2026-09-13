# han_china_100ad / WEIRD

## What I did

I read `BRIEF.md`, the Han China civilization file
(`rome/data/civilizations/han_china_100ad.json`), `rome/knowledge/00_NONOBVIOUS_TRICKS.md`,
and `rome/knowledge/03_SOCIAL_POLITICS.md` (the model-and-HOWTO module that documents patrons,
protection, bribery, and the "eminence" hazard the previous Rome tester found undocumented). I
also read the two existing reports in `rome/playtest/reports/` (`han_china_100ad_BREAK.md`, empty
placeholder, and `rome_100ad_WEIRD.md`, the report the task brief references) so I would not waste
budget re-discovering the exact pre-patch exploit that report describes, and so I could design
tests that specifically probe whether the four stated fixes ("same person not counted twice",
"price rises steeply with volume", "people are untrained for three years", "manumission reputation
saturates") actually hold under adversarial use, rather than just under normal use.

I drove the game exclusively through `python3 rome/sim/simulator.py agent --civ han_china_100ad
[--kit ...] [--seed ...]`, piping hand-written JSON lines on stdin, exactly per the protocol. I
never called `run`, `compare`, `sensitivity`, `sweep`, the CLI `path`/`why`/`costs`, or
`treetool.py`, never imported `simulator` as a module, and never opened `rome/data/strategies/` or
the tech tree JSON directly. The **one disclosed exception**, per the brief's own carve-out: I used
the in-protocol `why` command on the same node id (`patron_imperial`, `galena_detector`, and a
handful of cost-comparison nodes) under **both** `--civ han_china_100ad` and `--civ rome_100ad` to
check a specific claim I doubted — that Han China's declared `cost_multipliers` actually change
node costs. I did not open `tech_tree.json` itself; I only compared the simulator's own `why`
output between two civilizations, which is exactly the kind of "check a specific claim the game
told you" use the brief permits.

My plan, in order: (1) re-attempt the patched slave-buy-and-manumit trick at several purchase
granularities to see whether the fix is really airtight or just moved the exploit surface; (2)
follow the brief's specific lead on domain cost multipliers and handicap remedies, since Han
China's civ file is explicit about having them (`casting: 0.65`, `commerce: 1.15`, etc.) in a way
Rome's file is not; (3) push the manumission pump to extreme scale to see whether the "too eminent"
death that ended the previous Rome WEIRD run reproduces here, given Han's civ file sets
`w_eminence_danger: 0.8` and calls out "court factions and eunuch politics" as a specific danger
in its own notes; (4) check whether massive negative capital (the natural end state of an
unconstrained buying spree) has any consequence at all; (5) sanity-check forest/mine pricing and
the `bounty` command as cheap comparison points.

The most valuable thing I found was not a reproduction of the old exploit (that fix holds up
better than I expected) but a **different, and arguably bigger, hole in the same buy/manumit
machinery**: the "price rises steeply with volume" fix throttles a single `buy` call by its own
size, but never remembers what you bought a moment ago. Splitting one giant purchase into many
small ones defeats it completely, at any scale, with no cap I could find. Separately, and
unrelated to slaves at all, I found that Han China's headline civilizational feature — cheaper
metallurgy/paper, more expensive commerce/finance — appears to have **zero effect on any cost the
protocol will show or charge you**, which if true means the entire "handicap and its remedy" story
in the civ file is currently flavour text.

## Result

No run reached `point_contact_transistor`; consistent with my WEIRD role, I did not attempt a full
multi-century engineering run and say so plainly rather than rounding a partial result up. The most
important data points are: (a) 1,000 slaves bought via 100 separate `buy` calls of n=10 cost
297,688 den total (297.69/head, flat, never rising) versus 3,868,030 den (3,868/head) if the same
1,000 are requested in a single `buy` call — a **13.0x** price difference for an identical outcome;
(b) pushing this to 2,000-3,350 freed labourers and stepping decades forward never produced an
end-state, unlike the pre-patch Rome run — reputation saturates around 44-50 and eminence stays
under 2.0 even at extreme scale, then decays; (c) capital reached **-4,123,916.4 denarii** after an
80-year span with the game still reporting `"ended": false` and no adverse event of any kind; (d)
Han China's declared `cost_multipliers` (0.5-1.2 across six categories) produced byte-identical
`why` output to `rome_100ad` (which declares none) on every node I tested in four different
categories, in both the cost-cutting and cost-penalizing directions.

## FINDINGS

### F1. The patched "price rises steeply with volume" throttle is per-call, not cumulative — splitting one order into many small ones defeats it completely
- **Severity**: EXPLOIT
- **What I saw**: a single large purchase is throttled hard:
  ```
  {"cmd":"buy","what":"slaves","n":1000}
  ```
  ```
  {"ok": false, "error": "cannot afford 1000 slaves: 3868030 denarii (3868 each after the market
  moves against a purchase this size) and you have 1000000"}
  ```
  But issuing the *same total volume* as 100 separate calls of n=10 never triggers the scaling at
  all — every single call costs exactly 2,976.9 den (297.69/head), the n=10 baseline rate, all the
  way to 1,000 slaves bought:
  ```
  # 100 lines of {"cmd":"buy","what":"slaves","n":10} then {"cmd":"state"}
  {"ok": true, "bought": 10, "slaves": 1000, "capital": 702312.0}
  ```
  `1,000,000 - 702,312.0 = 297,688` total for 1,000 slaves = 297.69/head, flat, versus 3,868/head
  quoted for the same headcount in one call — a 13.0x difference. I also confirmed the price does
  not even creep up across consecutive small calls with no manumit in between:
  ```
  {"cmd":"buy","what":"slaves","n":10} -> {"bought":10,"slaves":10,"capital":997023.1}
  {"cmd":"buy","what":"slaves","n":10} -> {"bought":10,"slaves":20,"capital":994046.2}
  {"cmd":"buy","what":"slaves","n":10} -> {"bought":10,"slaves":30,"capital":991069.4}
  ```
  Cost per call is identical (2,976.9 each) regardless of how many you already hold. Then, combined
  with `manumit` (which is free and instant, see F2), I ran 200 iterations of buy-10/manumit-10 (200
  lines each) and reached 2,000 freed labourers for 595,376 total denarii — still the flat
  297.69/head rate — with reputation only 47.1 and eminence still 0.0 in the same year:
  ```
  {"ok": true, "year": 100, "capital": 404624.0, ..., "artisans": 903.0, "reputation": 47.1,
   "eminence": 0.0, ..., "freedmen": 2000}
  ```
- **Why it is wrong**: the brief explicitly says this exploit was fixed by making "price rise
  steeply with volume." It does — for a single order. A market that charges 3,868 den for the
  1,000th-through-2,000th slave bought in one transaction but only 297.69 den for the exact same
  slave bought one call later in a separate transaction is not modelling market depth at all; it is
  modelling *transaction size*, which a scripted player (which the brief's own protocol invites:
  "You drive it however you like... by writing your own script") trivially works around. This is
  the same shape of bug the fix was written to close, one layer down: instead of "buy 1 slave, free
  1 slave, repeat" being free (the original hole), "buy 10, repeat" is now the free version of "buy
  1,000." Nothing in the protocol or the error messages hints at a cumulative session-level cap; I
  found none up to 2,000-3,350 units tested.
- **Reproduce**: `python3 rome/sim/simulator.py agent --civ han_china_100ad --kit absurd --seed 1`,
  then feed `{"cmd":"buy","what":"slaves","n":1000}` (observe the refusal/price), restart the
  session, and instead feed 100 repetitions of `{"cmd":"buy","what":"slaves","n":10}` followed by
  `{"cmd":"state"}` — compare total capital spent for the same final slave count.

### F2. `manumit` grants roughly 80% of the trained-labour value of a slave instantly, in the same calendar year, bypassing the patched three-year training wait for that cohort
- **Severity**: EXPLOIT / BUG
- **What I saw**: buying slaves alone correctly queues them as untrained, with the promised delay:
  ```
  {"cmd":"buy","what":"slaves","n":50}
  {"cmd":"state"}
  ```
  ```
  {"ok": true, "bought": 50, "slaves": 50, "capital": 974475.6}
  {"ok": true, "year": 100, ..., "training_pending": [{"artisan_capacity": 27.5, "ready_year":
   103.0}], "artisans": 3.0, ...}
  ```
  `artisans` stays at its starting value of 3.0 — correct, they are still training. But manumitting
  the same 50 people **immediately**, with no `step` call and the year still 100, grants a large
  chunk of that capacity right now:
  ```
  {"cmd":"buy","what":"manumit","n":50}
  {"cmd":"state"}
  ```
  ```
  {"ok": true, "manumitted": 50, "freedmen": 50, "slaves": 0}
  {"ok": true, "year": 100, ..., "training_pending": [{"artisan_capacity": 27.5, "ready_year":
   103.0}], "artisans": 25.5, ...}
  ```
  `artisans` jumped 3.0 -> 25.5 (+22.5 for 50 heads = 0.45/head) in the same instant, for zero
  additional capital and zero founder-hours, while the *original* training-queue entry for the same
  50 people (27.5 capacity, i.e. 0.55/head, the value you get by actually waiting the three years)
  is still sitting in `training_pending` unchanged. Repeating buy-10/manumit-10 five times in a row
  (all still year 100) shows the same +4.5 artisans (0.45/head) per batch, consistently:
  ```
  buy 10 / manumit 10 -> freedmen 10,  artisans 3.0  -> 7.5
  buy 10 / manumit 10 -> freedmen 20,  artisans 7.5  -> 12.0
  buy 10 / manumit 10 -> freedmen 30,  artisans 12.0 -> 16.5
  ```
- **Why it is wrong**: the brief states the exploit was fixed in part by "people are untrained for
  three years." That holds for a slave who stays a slave. But the specific act the original Rome
  exploit abused — buy then immediately free — still produces most of a trained worker (0.45 of
  0.55, ~82%) with no wait at all, for the cohort you bought and freed in the same breath. A modern
  person buying and manumitting fifty people in the same afternoon should not thereby have fifty
  people who can already do skilled artisan work; the guide's own `freedman_staff` node (in
  `03_SOCIAL_POLITICS.md`, written for Rome but present in the shared tree, see F5) treats teaching
  the freed cohort a craft as a 900-founder-hour, 2-year undertaking, not something that happens by
  the act of manumission itself.
- **Reproduce**: exact sequence above, `--civ han_china_100ad --kit absurd --seed 1`.

### F3. Reputation saturation and the eminence hazard both hold up, even against F1/F2 pushed to extreme scale — the "too eminent" death from the pre-patch Rome exploit does not reproduce
- **Severity**: WORKS-WELL
- **What I saw**: I ran 1,000 iterations of buy-10/manumit-10 (10,000 requested, capped by
  affordability at 3,350 actually completed once capital ran out) and then stepped 5 years:
  ```
  {"ok": true, "year": 105, "capital": -615574.9, "artisans": 1731.74, "reputation": 44.8,
   "eminence": 1.21, "protection": 0.172, "freedmen": 3350, "ended": false}
  ```
  Reputation tops out in the mid-40s no matter how many people are freed (7.9 after the first 10,
  ~35 after 600, ~47 after 2,000, ~45-47 after 3,350 — visibly logarithmic, matching the brief's
  claim that "manumission reputation saturates"). Eminence, which the civ file sets an unusually
  high `w_eminence_danger: 0.8` for, never rose above 1.95 in any test I ran, including a deliberate
  80-year long-horizon test with 2,000 freedmen sitting on the books the whole time — and it
  actually **decayed** over that horizon along with reputation and artisans:
  ```
  {"ok": true, "year": 180, "capital": -4123916.4, "artisans": 16.11, "reputation": 4.1,
   "eminence": 0.11, "freedmen": 2000, "ended": false}
  ```
  Compare this to the pre-patch Rome result quoted in `rome_100ad_WEIRD.md`: reputation 1298.1,
  eminence 220.56, run ended with `"too eminent"` after a single n=3333 buy-then-manumit and one
  `step`. Nothing close to that happened here at any scale I tried.
- **Why it is right**: this is exactly the "become untouchable, or find the one hazard that
  punishes it" test the brief asks for, and here the game's own countervailing mechanic (reputation
  saturation feeding a bounded eminence) genuinely holds even when I deliberately tried to break it
  with a much larger and cheaper labour pump (F1) than the original exploit had access to. The
  saturation fix is doing real work; it just doesn't close the price-throttle hole (F1) or the
  instant-training hole (F2), which are economic, not reputational.
- **Reproduce**: `--civ han_china_100ad --kit absurd --seed 1`, 1,000x
  `{"cmd":"buy","what":"slaves","n":10}` / `{"cmd":"buy","what":"manumit","n":10}` pairs, then
  `{"cmd":"step","years":5}` and `{"cmd":"step","years":80}` variants, `{"cmd":"state"}`.

### F4. Han China's declared domain cost multipliers appear to have zero effect on any cost the protocol will show you or charge you
- **Severity**: BUG
- **What I saw**: the civ file declares `cost_multipliers` of 0.65 (casting), 0.75 (alloys), 0.6
  (information), 0.5 (paper), 1.15 (commerce), 1.2 (finance), etc., and an explicit note that this
  is Han China's core differentiator ("It arrives at the tree several rungs up in exactly the
  places Rome is weakest... Its handicap is a state that distrusts private commerce"). I compared
  `why` output for the same node id under `--civ han_china_100ad` and `--civ rome_100ad` (Rome's
  file declares no `cost_multipliers` at all) across four different categories, in both directions
  of the multiplier:
  ```
  {"cmd":"why","id":"mt2_white_cast_iron"}   # alloys, Han multiplier 0.75
  han:  {"labour": 38.4, "materials": 450.0, "capital": 200.0, "total": 688.4}
  rome: {"labour": 38.4, "materials": 450.0, "capital": 200.0, "total": 688.4}

  {"cmd":"why","id":"prn_hand_papermaking"}  # paper, Han multiplier 0.5 (should roughly halve it)
  han:  {"labour": 45.0, "materials": 2.0, "capital": 80.0, "total": 127.0}
  rome: {"labour": 45.0, "materials": 2.0, "capital": 80.0, "total": 127.0}

  {"cmd":"why","id":"fin_trading_post"}      # commerce, Han multiplier 1.15 (should raise it)
  han:  {"labour": 37.5, "materials": 125.0, "capital": 1500.0, "total": 1662.5}
  (same node under rome_100ad also 1662.5 — checked in the same session as met_investment_casting)

  {"cmd":"why","id":"met_investment_casting"} # casting, Han multiplier 0.65
  han:  {"labour": 21.0, "materials": 8.8, "capital": 300.0, "total": 329.8}
  rome: {"labour": 21.0, "materials": 8.8, "capital": 300.0, "total": 329.8}
  ```
  Every figure is byte-identical between the two civilizations, in both the "Han should be cheaper"
  and "Han should be pricier" directions. I also actually started and completed
  `prn_hand_papermaking` under `--civ han_china_100ad` to confirm the *charged* cost matches the
  *displayed* one (it does: capital dropped by exactly the displayed 80 den plus two years of
  ordinary upkeep, nothing extra or reduced).
- **Why it is wrong**: this is the brief's own suggested direction ("Can a multiplier go the wrong
  way?") landing on something more basic — the multiplier does not go *any* way. If this holds
  throughout the tree, Han China's entire stated identity (cheaper metallurgy and paper, pricier
  commerce and finance, with `patron_imperial` as the one remedy for the latter) is currently pure
  flavour text with no numeric effect a player can see or feel through the protocol. That in turn
  makes the brief's specific question ("can you get the remedy without paying for what it
  represents?") moot in the most literal sense: there is nothing to remedy, because the penalty was
  never applied in the first place. I could not check every node in the tree by hand within budget
  (that would mean reading the JSON, which is against the rules), so I am reporting this as
  observed on the four categories and eight node/civ pairs I tested, not as a proven tree-wide fact
  — but four different categories in both directions all showing the identical pattern is a strong
  signal.
- **Reproduce**: `{"cmd":"why","id":"mt2_white_cast_iron"}` (or any of the ids above) under both
  `--civ han_china_100ad --seed 1` and `--civ rome_100ad --seed 1`; diff the `cost` objects.

### F5. Node flavour text (and at least one error message) is shared verbatim across civilizations and hardcodes Roman institutions even when playing Han China
- **Severity**: CONFUSING
- **What I saw**: `patron_imperial`'s `why` output under `--civ han_china_100ad` reads, verbatim:
  ```
  "note": "Approach through the a rationibus or the Praetorian Prefect, not the emperor. The
  optical telegraph is the demonstration that buys this: an empire's core problem is that a
  message to the Rhine takes weeks. ..."
  ```
  — the *a rationibus* and Praetorian Prefect are Roman offices, and "the Rhine frontier" is
  Rome's, not Han China's problem (Han's frontier concerns are the steppe and the southern
  provinces, and the civ file's own notes talk about "an examined civil service" and "eunuch
  politics," never mentioned here). Running the identical `why` call under `--civ rome_100ad`
  returns the identical string. Likewise `galena_detector`'s note begins "A working semiconductor
  device **in Rome**, using mineral lead sulfide..." under the Han China civ. And the `bounty`
  command's refusal message hardcodes the civ regardless of who is asking:
  ```
  {"cmd":"bounty","id":"prn_hand_papermaking"}
  {"ok": false, "error": "not bounty-eligible (tier 1, category paper): a Roman artisan could not
  recognise success at this"}
  ```
  under `--civ han_china_100ad`, where a Han artisan, not a Roman one, is standing behind me.
- **Why it is confusing rather than a hard bug**: the tech tree and its flavour text are clearly a
  single shared asset across civilizations (consistent with F4 — the mechanism differentiating
  civs, `cost_multipliers`, does not appear wired up either), and only `starting_techs` and the top-
  level civ values genuinely change per civilization. That's a defensible engineering shortcut for
  a prototype, but it directly undercuts the specific "abuse the civilization model" framing the
  brief invites for this civ (Han's `handicap_remedies` names `patron_imperial` as the Han-specific
  fix for a Han-specific problem, and the node it points to is unmistakably Roman prose). A player
  reading only the in-game text, as the brief's premise assumes, would reasonably conclude they are
  petitioning a Roman finance secretary while playing the Later Han Empire.
- **Reproduce**: `{"cmd":"why","id":"patron_imperial"}` and `{"cmd":"why","id":"galena_detector"}`
  under both civs; `{"cmd":"bounty","id":"prn_hand_papermaking"}` under `--civ han_china_100ad`.

### F6. There is no insolvency/bankruptcy mechanic — capital can run to over four million denarii in debt for eighty years with no consequence of any kind
- **Severity**: UNREALISTIC / BUG
- **What I saw**: continuing the F3 long-horizon test, after 80 years at -4,123,916.4 den the state
  object reports no problem whatsoever:
  ```
  {"ok": true, "year": 180, "capital": -4123916.4, ..., "ended": false, "end_reason": null}
  ```
  `start` is unaffected by the deep negative balance (consistent with the documented "cost realized
  on completion, not on start" behaviour, but here there is no completion-time check either, since
  nothing in the 80-year window triggered one):
  ```
  {"cmd":"start","id":"identity_cover"}
  {"ok": true, "started": "identity_cover", "name": "Establish the Alexandrian physician-
  philosopher persona", "founder_hours_needed": 500.0, "calendar_floor_years": 0.5}
  ```
  Only the raw `buy` command's own affordability check ever refuses anything:
  ```
  {"cmd":"buy","what":"slaves","n":10}
  {"ok": false, "error": "cannot afford 10 slaves: 2977 denarii (298 each after the market moves
  against a purchase this size) and you have -4123916"}
  ```
  There is no debt-driven suspicion increase, no seizure, no forced-sale event, no bankruptcy
  end-state — the eight recorded events over those 80 years were ordinary fires and banditry
  disruptions, unrelated to the ledger.
- **Why it is wrong (or, from the "lose spectacularly" angle, notably right)**: this is close to
  the opposite of what the brief's "lose spectacularly" prompt was fishing for. I went looking for
  the fastest way to get the founder killed by his own success and instead found that you cannot
  be destroyed by failure either — a man 4 million denarii in debt to the wu zhu cash economy of
  Han China, in a state that runs salt-and-iron monopolies and famously enforced its tax and debt
  law, faces literally nothing. This is a real gap in the "money models power, power can also be
  taken away" thesis `03_SOCIAL_POLITICS.md` argues for at length: the model punishes being too
  visible but never punishes being unable to pay your bills.
- **Reproduce**: run the F3 long-horizon sequence (200x buy/manumit-10, `step` 80 years), then
  `{"cmd":"state"}` and any further `{"cmd":"start",...}` call.

### F7. Forest and mine purchases are flat-priced with no per-call throttle at all, in contrast to slaves
- **Severity**: WORKS-WELL (neutral finding, useful contrast to F1)
- **What I saw**: two consecutive `{"cmd":"buy","what":"forest","n":100}` calls both cost exactly
  187.50 den/ha (18,750 den for 100 ha each time); two consecutive
  `{"cmd":"buy","what":"mine","material":"iron","n":10}` calls both cost 45.0 den per t/yr of
  capacity (450 den each), and both come with the documented multi-year `ready_year` delay before
  the capacity is usable. Neither showed any sign of the "market moves against a purchase this
  size" language that guards slave purchases.
- **Why it is right (with a caveat)**: forest and mine capacity are throttled by time (the
  `ready_year` floor) rather than by price, which is a reasonable and different way to prevent an
  instant pump, and I could not find a way to make either one produce more value than it costs
  within budget — they behave exactly as advertised. The caveat is that I did not exhaustively test
  bulk mine/forest purchases at F1-style extreme scale (thousands of hectares/tonnes) the way I did
  for slaves, so I cannot rule out a similar per-call-vs-cumulative gap existing there too; I simply
  did not find one in the tests I ran.
- **Reproduce**: sequence in the "What I did" testing, `--civ han_china_100ad --kit absurd --seed 1`.

### F8. `bounty` correctly refuses low-tier/wrong-category nodes; I could not find any node in the currently-available set that was bounty-eligible, so the bounty money-pump lead went untested
- **Severity**: CONFUSING (process note, not a claim of safety or exploit)
- **What I saw**: every node I tried to bounty in the first-available set (tier 0-2, mostly
  `foundation`/`paper`/`casting`/`alloys`) returned `"not bounty-eligible (tier N, category X): a
  Roman artisan could not recognise success at this"`, and scanning the full 366-entry `available`
  list for `"bounty_eligible_by_type": true` returned nothing.
- **Why this matters**: the brief specifically names bounties as a money-pump lead worth checking,
  and I am reporting honestly that I did not find a way into that mechanic within the early-game
  state this session explored — I do not know whether higher-tier or later-unlocked nodes are
  bounty-eligible, because reaching them would have consumed the budget I spent on F1-F6 instead.
  This is an explicit gap in my testing, not a claim that bounties are safe.
- **Reproduce**: `{"cmd":"available"}` then filter for `bounty_eligible_by_type`; try
  `{"cmd":"bounty","id":<any early node>}`.

## Honesty note

I did not attempt a "win backwards" run to `point_contact_transistor` skipping the social/
institution chain, and I did not attempt a full multi-century engineering run in either direction.
Given this session's WEIRD/exploit-hunting purpose, I judged that fully characterizing F1 (a
clean, large, reproducible economic exploit that survived the stated patch) and F4 (a plausible
tree-wide bug undermining this civ's entire stated identity) was higher value than a long grind
toward the goal node. I did check, in passing, that `scholars` stays pinned at 1.0 and
`founder_hours_available` stays pinned at 2400.0 throughout every F1/F2/F3 test regardless of how
many artisans or how much reputation the slave/manumit pump generates — consistent with the
previous Rome tester's F5 finding that this pump inflates a resource (artisan labour) that does
not gate the deep research chain, which still appears to require the school/scholar path this
report did not test building. I also did not verify F4 against every category or every node in the
tree (that would require reading the tech tree JSON, which the brief forbids outside checking a
specific doubted claim); I checked four categories in both directions and found the same pattern
every time, which I judged sufficient to report as BUG rather than as a fully proven tree-wide
fact.
