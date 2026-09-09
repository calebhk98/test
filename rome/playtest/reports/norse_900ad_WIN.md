# norse_900ad / WIN

## STATUS: COMPLETE — goal reached (point_contact_transistor, 1226 AD, 326 years after arrival)

## Plan

Goal: reach `point_contact_transistor` as early as possible playing straight (no exploits),
protocol-only, via `python3 rome/sim/simulator.py agent --civ norse_900ad`. I built a small
driver (`driver.py` in my scratchpad, a background persistent process holding the one simulator
subprocess; it tails an append-only `commands.jsonl` and appends replies to `responses.jsonl`;
`send.py` appends one command and blocks for the matching reply) so I can issue many protocol
commands across tool calls in this sandbox (whose shell state does not persist between Bash
calls) while keeping a single continuous game. Every decision about what to `start` is mine,
reasoned from `available`/`why`/`path` output. I did not read `rome/data/strategies/` or the
tech tree JSON to plan, and did not use `load_strategy` or import `simulator`.

Before playing I read:
- `rome/playtest/BRIEF.md` (the hard rule: protocol only).
- `rome/data/civilizations/norse_900ad.json` directly — this is civ config (population 1.5M vs
  Rome's 65M, urban_fraction 0.03, literacy_elite 0.15/general 0.02, price_index 1.4, wage_index
  0.6, state_capacity 0.15, starting techs sea_clinker_hull/sea_keel_deep/met_bloomery_bog_iron/
  exp_openocean_navigation, base_reach 4, no corporation/guild/charter/bank/patent institutions,
  cost_multipliers cheap for ships/marine/navigation/hull/metallurgy (0.6-0.9x) and expensive for
  infrastructure/structures/buildings/civil/binders/commerce (1.1-2.2x), a `handicap_remedies`
  block saying most of those public-works multipliers get a residual (down to ~1.0-1.2x) once
  `collegium_licensed` is built, except `binders` which needs `cn_portland_cement`;
  `w_eminence_danger: 0.2`, lowest of any civ seen so far, "no state, no court, nobody to
  denounce you to. The danger here is a feud, not a treason charge"; hazard: Christianisation/
  political consolidation 995-1100 AD, "changes the value vector rather than killing people".
  This is civ config, not the tech tree or a strategy file, so reading it is in scope the same
  way the task prompt already quoted much of it at me directly.
- `rome/knowledge/00_NONOBVIOUS_TRICKS.md` (the general "doors not destinations" tricks index).
- `rome/knowledge/03_SOCIAL_POLITICS.md` (Rome-specific social-politics chain; explicitly notes
  the Norse file "inverts the sign on labour-saving technology... the whole of the Vespasian
  problem simply disappears" — so I expect this module's Rome-specific chain (identity_cover,
  patron_local, citizenship, collegium_licensed, school_founded, academy_network...) to matter
  differently or not at all for Norse, and I will check via `path`/`why` rather than assume).
- Skimmed `rome/knowledge/96_finance.md` for institution-node context (bank, partnership, etc.)
  given Norse starts with only `felag` (a genuine joint venture) and nothing else.
- Read the prior `rome_100ad_WIN.md` and skimmed `han_china_100ad_WIN.md` for report format and
  to know what mechanics/findings are already known (F1-F7 in the Rome report: free ambient-tech
  cascade, no bankruptcy floor / deficit spending is intended, calendar-floor overruns, Third
  Century Crisis silent knowledge loss, scholar-count staff wall discoverability, mine operating
  cost spikes, automatic mothballing safety valve). I will check whether these still hold for
  Norse and whether Norse's specific handicaps (public-works multiplier, low state_capacity, no
  institutions) create genuinely different dynamics, per the assignment's questions.

I was specifically asked to watch money closely given a recently-fixed bug where Norse insolvency
was unrecoverable and failed most runs, and to report exactly what happens if I go into arrears.

## What I did

Started the driver, confirmed `{"cmd":"state"}` at year 900: `capital: 400.0, revenue: 0.0,
living_cost: 216.0, net_per_year: -216.0, scholars: 1.0, artisans: 3.0, done_count: 4,
done_granted: 4, done_earned: 0`. The four `done_granted` are the civ file's four starting techs.

Before making any decisions I checked `available` (319 candidates) and `why` on a few nodes to
calibrate, including the four Norse starting techs, to see what they actually give (see F1 below
— this immediately found a crash bug).

**Opening (year 900-940).** Started the five free tier-0 "ambient" nodes
(`cap_heat_0700`/`cap_power_muscle`/`cap_tol_1mm`/`lnd_wheel_spoked`/`mat_leather`) exactly as
the prior Rome WIN report describes, then stepped: the same free cascade fired for Norse (121
completions in one step, revenue 0 -> 681.6), confirming this mechanic is civ-agnostic (see F8).
Followed `path`'s intersection with `available` through `units_standards`, `identity_cover`,
`patron_local`, `scientific_method`, `arithmetic_positional`, `workshop_first` — all of which
`path` marked as genuinely on the technical route to the goal for Norse too (the same result
the Rome report found: only two of the social-politics module's nodes are hard technical
prerequisites, the rest is about survival, not the tech graph). Hit an early charcoal shortage
(`resource_throttle` down to 0.3) because I hadn't bought forest yet; it self-corrected partly on
its own (the simulator has an automatic buy-forest response when under-throttled and flush) and
partly once I understood the mechanic.

**The handicap test (year 930-940).** Deliberately detoured off the shortest technical path to
build `patron_local` -> `citizenship` -> `collegium_licensed`, specifically to test the civ
file's own claim that this lifts the public-works cost handicap (none of these three are on
`path`'s technical `remaining` list for the goal). Compared `blast_furnace`'s quoted
`civ_domain_factor` before and after completing `collegium_licensed`: unchanged, 1.53 both times.
This is F3 below, and it is the single most important test I ran for the brief's Q2.

**The iron trap (year 1009-1058).** `steam_high_pressure` triggered a persistent iron shortage.
I bought mine capacity three times over ten years, all reporting success, and watched
`resource_throttle` sit frozen at exactly 0.393 for 28 straight years — 15 years past the last
quoted `ready_year` — while capital comfortably exceeded 100,000 denarii almost the whole time.
It only resolved the year after `steam_high_pressure` itself finally completed. This is F4 below,
and it was the single largest unexplained stall in the run (measured in real years lost, larger
than the handicap-multiplier cost in F3).

**The arrears episode (year 933-941).** Right after `collegium_licensed` and `zinc_metal`
completed in the same window, capital fell to **-126,180.0** at year 938 (state quoted in full
in F6 below) — the deepest deficit of the run. It climbed back to positive within three years
purely from revenue, with no staff loss, no event, and no manual intervention from me. I never
personally drove the run deep or long enough to trigger the deeper "IN ARREARS"/"ABANDONED"
staff-bleed mechanism the codebase's own comments describe (that needs three *consecutive* years
below `-max(4000, revenue*2)`, and my revenue by then was already large enough that the floor was
far more negative than I ever reached) — see F6 for the honest scope of what I did and didn't
verify first-hand on this question.

**Midgame to endgame (year 940-1226).** Once `school_founded` was up (built via `freedman_staff`
after hitting the same scholar-count wall Rome's report calls F5 — the refusal message correctly
named the fix this time, see F9), the run had abundant capital (multiple millions of denarii by
year 1000) and the `available`∩`path` set narrowed to a handful of items per round almost every
round, exactly matching the Rome report's description of the midgame as "mostly waiting for the
one active project." I bought slaves and manumitted them twice more to clear artisan-count walls
ahead of `railway` (needed 150 trained artisans) and `power_grid` (200). Both diffusion-floor
institutions (`railway`, quoted 20-year floor; `power_grid`, quoted 25-year floor) completed
faster than their stated floors this time (`railway` in 11 years, `power_grid` in 19), unlike the
Rome report's experience of routine 2-4x overruns — I do not have an explanation for the
difference beyond noting the formula that shrinks the floor with reputation
(`floor = yrs / (1 + reputation/90)`) and my reputation was generally healthy through this
stretch. The endgame semiconductor chain (`zinc_industry_scale` -> `germanium_extraction` ->
`gecl4_purification` -> `ge_reduction` -> `zone_refining` -> `single_crystal` ->
`point_contact_transistor`) ran with no further surprises once iron was flowing, though
`zinc_industry_scale` displayed the same `founder_hours_left`-goes-negative / `years_in_progress`
resets-and-cycles behaviour the Rome report already documented as F3 there (I did not re-derive
it; I just confirmed it recurs for a different civilization).

Across the whole run I never saw a single eminence-driven adverse event, despite `eminence`
spending well over half the game above 1.0 and peaking at 3.76 — see F5. I never saw the
Rome-style "Third Century Crisis" knowledge-loss mechanic fire even once — Norse's own hazard
list (`Christianisation and political consolidation, 995-1100`) has `sacks_a_site: false` and
`sack_chance_per_year: null`, and the run passed straight through that window (995-1100 AD)
with no unusual events, confirmed by grepping every event message the whole 326-year run
produced (see F5).

## Result

**GOAL REACHED.** `point_contact_transistor` completed in **1226 AD**, 326 years after arrival
(year 900), founder alive throughout. Full final `{"cmd":"state"}`, quoted exactly, not
summarized:

```json
{
    "ok": true,
    "year": 1227,
    "capital": 27022557.4,
    "revenue": 1781763.7,
    "upkeep": 470906.0,
    "living_cost": 524039.2,
    "mine_operating_cost": 272160.0,
    "project_spend_last_year": 8492.5,
    "net_after_project_spend": 506166.0,
    "net_per_year": 514658.5,
    "training_pending": [],
    "founder_hours_available": 10461.4,
    "founder_alive": true,
    "scholars": 42.81,
    "artisans": 210.29,
    "directors_extra": 4.48,
    "reputation": 9.3,
    "suspicion": 0.0,
    "scandal": 1.14,
    "eminence": 1.92,
    "protection": 0.43,
    "familiarity": 0.9,
    "done_count": 304,
    "done_granted": 129,
    "done_earned": 175,
    "active": {},
    "knowledge_risk": {
        "technologies_at_risk": 120,
        "loss_chance_if_a_site_is_sacked": 0.8,
        "fraction_lost_when_it_happens": 0.4,
        "expected_technologies_lost_per_sacking": 38.4,
        "hedged_by": null,
        "better_hedge_available": "corpus_dispersed",
        "known_hazards_ahead": []
    },
    "resource_throttle": 1.0,
    "throttle_binding": null,
    "forest_ha": 4109.8,
    "mine_capacity": { "coal": 43200.0, "iron": 10800.0 },
    "slaves": 0,
    "freedmen": 253,
    "goal": "point_contact_transistor",
    "goal_reached": true,
    "goal_year": 1226,
    "manual": true,
    "ended": true,
    "end_reason": "goal reached: point_contact_transistor completed in 1226 AD"
}
```

For scale: the prior `rome_100ad_WIN` playtest reached the same goal in 458 AD, 358 years after
Rome's 100 AD arrival. This Norse run reached it in 326 years — **32 years faster than the
Rome run**, despite starting 1.5 million people against 65 million, a 1.4 price index, and a
public-works multiplier that, per F3, turned out never to actually lift. I want to flag plainly
that this is not a controlled comparison — different tester, unfixed random seed (I did not pass
`--seed`), and a different set of moment-to-moment decisions — so I would not treat "Norse beat
Rome by 32 years" as a reliable measurement of the civilizations' relative difficulty. What I can
say with more confidence, because I watched it happen directly in the event log, is *why* the
Norse run had less drag than Rome's: it never once paid the Third-Century-Crisis-style
knowledge-loss tax that cost the Rome run dozens of already-finished technologies multiple times
over (see F5) — Norse's own hazard list has no sacking mechanic at all — and it never lost a
single founder-hour to eminence-driven confiscation or patron destruction despite `eminence`
sitting above 1.0 for most of the game's second half. Both of those are real, structural
differences between the two civilizations' hazard models, not an artefact of my play.

## Answering the assignment's questions directly

**1. Does poverty change HOW you have to play, or just make everything slower? Is there a
genuinely different strategy here, or is it Rome with worse numbers?** Mostly the latter, and I
want to be honest that this surprised me, because I expected the opposite going in. For roughly
the first 50 years (900-950 AD), poverty is a real, felt constraint: capital repeatedly landed at
exactly zero or went negative (see F6), I had to consciously buy forest/mine capacity rather than
assume abundance, and every choice of what to start next was genuinely load-bearing. Past about
year 950, revenue outgrew every cost so completely (net_per_year crossed 100,000 den/yr by 962
and never looked back) that the rest of the 276-year run played exactly like the Rome report
describes its own midgame: a narrow `available`∩`path` set, wait for the one active project,
occasionally clear a headcount wall with `buy slaves`+`manumit`. The one part of the brief's
premise that WOULD have made this a genuinely different strategy — the public-works multiplier
that is supposed to lift once you charter `collegium_licensed` — turned out not to function at
all (F3), so the "capital-light, skill-heavy" plan the civ file's own notes recommend never
actually had to be a *different* plan from Rome's; it only had to be a *patient* one for the
first two generations. The one place poverty produced a real, qualitatively different decision
was the eminence question (F5): because Norse eminence is nearly costless, I never had to hold
back on visible wealth or reputation the way a Rome player is warned to, which is a real
strategic freedom Rome does not have, not merely a smaller number in the same equation.

**2. Did you feel the public-works handicap, and did building the remedy visibly help?** I felt
the handicap clearly: `blast_furnace` quoted a `civ_domain_factor` of 1.53 (base_total 315,450 ->
total 482,638.5), and `citizenship` quoted 1.98, both driven by the `infrastructure` trait
multiplier (1.8x) stacking with the node's own category multiplier — exactly the mechanism the
civ file describes. Building the remedy (`collegium_licensed`) did **not** visibly help — I
checked the exact same `blast_furnace` node's `civ_domain_factor` before and after, and it was
unchanged to three significant figures, and confirmed by reading the one function that computes
it (`civ_cost_factor`) that the civ file's `handicap_remedies` block is never read anywhere in
the simulator. See F3. This is the most concrete, falsifiable finding in this report, and I am
confident in it because I checked it two independent ways.

**3. Watch your money closely. If you go into arrears, can you actually climb out? Report
exactly what happened.** Yes. My deepest arrears were `capital: -126,180.0` at year 938 (full
context and the exact recovery trajectory in F6); it climbed back to positive within three years
with no staff loss, no lost technology, and no event message of any kind — just patience while
`net_per_year` (which stayed positive throughout, ~32,000-33,000 den/yr at the time) paid it down.
I never personally drove a run into the deeper three-consecutive-year staff-bleed/abandonment
branch the fix commit describes, so I cannot report first-hand what THAT looks like in play — see
F6's honest caveat. What I can say with full confidence is that the specific bug the task asked
me to watch for (insolvency that is simply unrecoverable) did not recur in this run: every deficit
I incurred, including the deepest one, resolved itself.

**4. Norse start with four technologies including clinker hulls, a deep keel and bog iron. Did
those matter, or were they decoration?** Decoration, for three of the four, and I did not expect
this answer when I started. `sea_clinker_hull`, `sea_keel_deep` and `met_bloomery_bog_iron` are
each granted `done` at turn zero but (a) crash the `why` command outright (F1), (b) unlock
nothing anywhere in the 2,828-node tech tree (confirmed by grep), and (c) contribute zero revenue
and zero upkeep because the auto-grant revenue rule only pays out for practisable personal skills
(medicine categories), not for owning a fleet or a bloomery as a starting condition (F2). The
fourth, `exp_openocean_navigation`, is real: it answers `why` correctly, shows `done: true`, and
represents a genuine 24-node, 12.5-critical-path-year chain that Rome would have had to build
from scratch and Norse gets for free. So of the civ's headline "best shipwrights in Europe"
flavor, only the navigation piece is mechanically real; the ships and the iron are, in this
build, pure narrative color with a live crash bug attached.

**Was it playable? Did anything the game told you turn out misleading? What did you learn the
hard way? Did anything punish you for drama rather than a real reason?** Mostly playable, with
two real exceptions (F1's crash and F4's silent multi-decade stall) and one thing that told me
something specifically wrong (F3's dead-letter handicap remedy, which is the most misleading
single number in the whole run — it is quoted to me, with a specific mechanism and a specific
node to build, and the mechanism simply is not there). What I learned the hard way, with no
warning from the protocol: that a resource shortage can outlive its own fix by decades (F4), and
that the promised handicap remedy does nothing (F3) — I only found the second one because the
brief specifically told me to probe it; a player who read the civ file, built `collegium_licensed`
for the reasons it gives, and moved on without re-checking a node's quoted cost would never learn
this at all, and would credit their own hard-won capital for a discount they never actually
received. Nothing punished me for drama rather than a real, mechanically-grounded reason: every
cost I paid traced to a real mechanic once I understood it (F4's trap has a real, findable cause;
F6's arrears had a real, findable cause; the mine-mothballing and eminence-silence findings, F5
and F7, are both cases of the game correctly NOT punishing me for something that looked
alarming). The closest thing to an unexplained cost was `mine_operating_cost` climbing
without a dedicated `why`-visible line item, but that is the same finding the Rome report
already made (its F6) and I did not find a new wrinkle in it worth re-reporting at length here.

## FINDINGS

### F1. `why` on 3 of Norse's 4 starting techs crashes and kills the whole simulator process
- **Severity**: BUG, severe
- **What I saw**: fresh process, single command:
  `printf '{"cmd":"why","id":"sea_clinker_hull"}\n' | python3 rome/sim/simulator.py agent --civ norse_900ad`
  produces an uncaught `KeyError: 'sus'` at `simulator.py:2384` in `_node_explain`
  (`"suspicion": n["sus"], "state_interest_trait_score": n["gov"]`) and the process exits,
  taking the whole game with it — this is the same class of bug as Rome's playtest finding B2
  ("A malformed command killed the session"), except this time the command is not malformed at
  all, it is exactly what a player is told to do ("`why` ... ARE protocol commands and you should
  use them freely"), and it fires on a node the civ itself starts with. The same crash reproduces
  identically for `sea_keel_deep` and `met_bloomery_bog_iron`. The fourth starting tech,
  `exp_openocean_navigation`, answers `why` fine (`"done": true`, full explanation). My first live
  driver session hit this by accident mid-exploration and the underlying simulator subprocess
  died silently (no error surfaced through my driver except the traceback landing in the reply
  stream) — I had to notice `ps aux` showed no simulator process left and restart from year 900
  with a fresh process, losing nothing only because it was still turn zero.
  - Per the brief's rule ("You may read [the tech tree] ONLY to check a specific claim after the
    game has told you something you doubt, and if you do, say so in your report"), I opened
    `rome/data/tech_tree.json` after this to confirm the mechanism, since I had real, specific
    doubt about a crash and wanted to know if it was reproducible in a principled way rather than
    an artifact of my driver. Confirmed: `sea_clinker_hull`, `sea_keel_deep` and
    `met_bloomery_bog_iron` are the three ids added in git commit `ee83c79` ("Han playtest: eight
    silently dropped starting techs...") to fix the previously-reported bug where these ids were
    silently dropped from Norse's starting techs. Every other node in the tree I sampled carries
    `sus` (suspicion) and `gov` (state-interest) fields; these three do not — they were added
    without them. `exp_openocean_navigation`, which does answer `why` correctly, does carry both.
- **Why it is wrong**: a player following the brief's explicit invitation to use `why` freely, on
  a node the civ starts with, loses the entire run with no recovery, exactly the severity class
  the brief calls out (B2 in the Rome report) as already fixed once for other malformed-input
  cases. Here the input is perfectly well-formed; the bug is in the node data, not the command
  parsing, so the earlier fix's guard (catching bad *commands*) does not catch this.
- **Reproduce**: `printf '{"cmd":"why","id":"sea_clinker_hull"}\n' | python3 rome/sim/simulator.py agent --civ norse_900ad`
  (repeat with `sea_keel_deep` or `met_bloomery_bog_iron`) — uncaught `KeyError: 'sus'`, process
  exits nonzero, no JSON error object returned.

### F2. Norse's own advertised starting techs (clinker hull, deep keel, bog iron) are pure decoration in the running model: zero downstream unlocks, zero revenue, zero upkeep
- **Severity**: UNREALISTIC / CONFUSING (answers the brief's Q4 directly)
- **What I saw**: because F1 makes `why` unusable on these three nodes, I could not get
  `downstream_count`/`unlocks` from the protocol for them. Having already opened
  `tech_tree.json` to diagnose F1, I checked, as a direct extension of the same doubt, whether
  anything in the 2,828-node tree lists any of the three as a prerequisite
  (`[n['id'] for n in nodes if set(n.get('pre',[])) & {'sea_clinker_hull','sea_keel_deep','met_bloomery_bog_iron'}]`)
  and got an **empty result** — nothing in the entire tree requires any of them. They each carry a
  nonzero `rev` field in the data (700, 300, 420 den/yr respectively) that looks like it should
  matter, but `Sim.revenue()` (simulator.py:923-933) explicitly excludes granted (civ-gifted, not
  player-built) nodes from revenue **unless** their category is in `PRACTISABLE_CATS =
  {"surgery","obstetrics","pharmacology","medicine","diagnosis","dentistry"}` — a design choice
  the code comments explain in detail (a practised medical skill earns you a fee directly; owning
  a fleet or a bloomery as a starting condition does not entitle you to its freight/output as
  personal income). `sea_clinker_hull`/`sea_keel_deep` are category `ships` and
  `met_bloomery_bog_iron` is category `metallurgy`, neither in the practisable set, so none of the
  1,420 den/yr of nominal revenue ever reaches `state.revenue` — confirmed directly: `state` at
  turn zero shows `revenue: 0.0` with `done_count: 4` already granted. The same exclusion means
  they also cost zero upkeep (`upkeep()` at simulator.py:952-956 uses the identical granted/
  practisable test), so they are entirely inert in the simulation: present in `done`, invisible
  everywhere else, and un-inspectable via `why` because of F1.
- **Why it matters**: the civ file's own blurb calls the Norse "the best shipwrights and among the
  best smiths in Europe" and lists these four as the mechanical expression of that; a player
  reading the civ file (as I did, since it's in-scope config) would reasonably expect these to be
  doing *something* — either seeding early revenue the way Rome's tier-0 "ambient" cascade did
  (see the Rome WIN report's F1, which found ~130 free completions and a revenue jump from 0 to
  666.7 for Rome), or at minimum unblocking something downstream. They do neither. The actual
  mechanical expression of "best shipwrights and smiths" lives entirely in `cost_multipliers`
  (ships 0.6x, hull 0.6x, metallurgy 0.85x — applied to nodes I build later in the `sea_*`/`met_*`
  categories), which is legitimate and does matter (see later findings once I actually build
  something in those categories), but the four *starting_techs* themselves, despite being the
  civ's headline flavor, are functionally decoration in the current build — one step short of
  Rome's own tier-0 nodes, which at least need to be manually `start`ed and non-Rome civs don't
  get free (see `FOREIGN_MARKERS` in the same commit). This directly answers the brief's Q4
  ("Norse start with four technologies including clinker hulls, a deep keel and bog iron. Did
  those matter, or were they decoration?"): three of the four are decoration by the numbers, and
  the fourth (`exp_openocean_navigation`) is a real, inspectable, already-completed prerequisite
  with a genuine chain behind it (`chain_size: 24`, `critical_path_years: 12.5` when queried from
  scratch) that the Norse get for free and Rome would have to build.
- **Confidence caveat**: as with F1, this required opening `tech_tree.json`, which I would not
  normally do to plan, but did here specifically to check a claim I doubted after the crash — the
  civ file's own prose claim that these techs matter, versus what the running `state` showed
  (revenue unmoved by their grant). Flagging per the brief's rule.
- **Reproduce**: fresh civ, `{"cmd":"state"}` immediately shows `revenue: 0.0` with `done_count: 4`
  already granted; `grep`ing the tech tree for `pre` lists containing any of the three ids returns
  nothing.

### F3. The civ file's promised handicap remedy (`collegium_licensed` lifting the public-works cost multiplier) does not exist anywhere in the simulator — the multiplier is unchanged before and after building it
- **Severity**: BUG, severe (directly answers the brief's Q2, and the answer is "no, it does not help at all")
- **What I saw**: the civ file's own `handicap_remedies` block is explicit and specific: build
  `collegium_licensed` and the `infrastructure`/`structures`/`buildings`/`civil`/`foundations`/
  `commerce` multipliers drop from 1.6-2.2x to a residual of 1.0-1.2x (binders needs
  `cn_portland_cement` instead). I set out to test this directly. `{"cmd":"why","id":"blast_furnace"}`
  **before** `collegium_licensed` was built showed `"civ_domain_factor": 1.53` inside `cost`
  (base_total 315,450 -> total 482,638.5). I built `citizenship` (prerequisite) then
  `collegium_licensed` — confirmed completed via a `step` reply's `events`:
  `{"year": 938, "message": "completed: Licensed collegium of physicians and teachers"}` — and
  immediately re-ran `{"cmd":"why","id":"blast_furnace"}` (blast_furnace was still mid-build, so
  its remaining cost is exactly what the multiplier still governs): **`"civ_domain_factor": 1.53`,
  unchanged to three significant figures**, same `total: 482638.5`. I also checked a `commerce`-
  trait node (`fin_societas`) before and after: `civ_domain_factor: 1.1` both times, no change,
  against a promised residual of `1.0`.
  - Having gotten an empirical result I doubted the civ file's own claim about, I opened
    `rome/sim/simulator.py` (not the tech tree, and not a strategy file — I want to flag this
    exception too, in the same spirit as the brief's rule about the tech tree, even though the
    brief's text technically only restricts tech-tree/strategy reading) and searched for
    `handicap_remedies` and `residual`, the two key names from the civ file's own schema:
    **zero matches in the entire file.** `civ_cost_factor(k)` (simulator.py:872-896), the only
    function that computes this multiplier, reads exclusively from `civ["cost_multipliers"]`
    keyed by the node's `cat` and `traits`, multiplying every matching entry together (this is
    also how I confirmed the 1.53 figure directly: `blast_furnace` has `cat: metallurgy` (0.85)
    and `traits: ["infrastructure"]` (1.8), and 0.85 x 1.8 = 1.53 exactly; `citizenship` has
    `traits: ["commerce","infrastructure"]`, and 1.1 x 1.8 = 1.98, which is exactly what `why`
    quoted for it). Nothing in that function, or anywhere else I could find, ever reads
    `handicap_remedies` or checks whether its named node is in `self.done`. The block sits in the
    civ JSON as a promise the code never looks at.
- **Why it is wrong**: this is the single most consequential number the brief asked me to probe
  ("The public-works handicap is supposed to lift once you charter a body able to organise one
  ... did building the remedy visibly help?"), and the honest answer, checked two independent
  ways (direct before/after `why` comparison in a live game, and reading the one function that
  computes the number), is that it does not lift at all. A player who reads the civ file (which
  the brief and the task both treat as legitimate, in-scope information — the task prompt itself
  quotes the remedy mechanism at me) and therefore spends real founder-hours and roughly 14,700
  effective denarii on `patron_local` -> `citizenship` -> `collegium_licensed` specifically to
  unlock cheaper infrastructure gets nothing for it on that front. It is not merely "the effect is
  small" — it is exactly zero, to the precision `why` reports. Everything else `collegium_licensed`
  does (unlock `school_founded`, presumably reduce suspicion/eminence via its own `suspicion: -10`
  field, standing as a legitimate institution) is real and I do not regret building it for the
  social-politics reasons Rome's module documents, but the specific, numbered claim in Norse's own
  civ file — the one that gives the civilization's central economic handicap a stated way out — is
  fiction the model never enacts.
- **Reproduce**: fresh Norse game, `{"cmd":"why","id":"blast_furnace"}` (or any `infrastructure`-
  trait node), note `cost.civ_domain_factor`; build `patron_local` -> `citizenship` ->
  `collegium_licensed` to completion (confirm via `step` events); re-run the same `why` call on the
  same still-incomplete node and observe `civ_domain_factor` is identical.

### F4. A resource shortage can trap itself: buying mine capacity for the bottleneck resource can push its own delivery date out forever while the project that needs it stays active
- **Severity**: BUG, severe
- **What I saw**: hit an iron shortage at year 1009 (`"SHORT OF IRON: work running at 20% of
  plan"`) with `steam_high_pressure` active. I bought iron mine capacity myself three times —
  `{"cmd":"buy","what":"mine","material":"iron","n":100}` at year 1029 (`"ready_year": 1032.0`),
  `n:200` immediately after (`"ready_year": 1032.0`), `n:400` at year 1039 (`"ready_year":
  1042.0`), 700 t/yr committed in total, all reporting success and debiting capital. `state`
  from year 1029 through **year 1057** — 28 years, 15 past the last quoted `ready_year` —
  continuously showed `mine_capacity: {"coal": 43200.0}` with **no iron entry at all**, and
  `resource_throttle` frozen at exactly `0.393` every single year (`{"cmd":"state"}` sampled at
  years 1040, 1043, 1046, 1049, 1052, 1055, 1057 — same value to three decimals every time, with
  capital comfortably above 100,000 den for most of that span, so it was never a money-side
  cap). It only resolved at year 1058, right after `steam_high_pressure` itself finally
  completed (`{"year": 1056, "message": "completed: High pressure steam and adequate boilers"}`)
  — `mine_capacity` then showed `iron: 43200.0` and `resource_throttle: 1.0` in the same step.
  - Reading `rome/sim/simulator.py` (not the tech tree) to understand this, since I had strong,
    specific doubt after watching a paid-for resource sit undelivered for 28 years: `open_mine()`
    (line 1104) sets `self.mine_ready[mat] = max(self.mine_ready.get(mat, 0.0), self.year +
    self.MINE_LEAD_YEARS)` on every call — so a NEW purchase always pushes the ready date to at
    least 3 years from whenever it is made, never earlier, and the automatic under-throttle
    response (line 1723, `if thr < 0.9 and self.capital > 3000: ... self.open_mine(self.binding,
    min(want, ...))`) fires every single year the shortage persists, computing `want = short -
    self.mine_capacity.get(self.binding, 0.0)` (line 1744) — note this subtracts only already-
    commissioned `mine_capacity`, never `mine_pending`, so as long as the shortage's own cause
    (an active project's ongoing annual material draw) keeps `short` above zero, `want` stays
    positive and the code calls `open_mine` again on the very next step, **re-maxing
    `mine_ready` to `this_year + 3` before the previous order ever reaches maturity.** The result
    is a genuine trap: a long-running active project that itself needs the scarce resource every
    year it remains in progress keeps `thr < 0.9`, which keeps re-ordering (and re-delaying) the
    fix for as long as the project stays active — and the project stays active in part *because*
    it is under-throttled. My run only escaped because `steam_high_pressure` happened to cross its
    founder-hours completion threshold on its own after 26 years despite running at ~39% of plan,
    removing the demand that was re-triggering the reset; a run with a slower-completing
    iron-hungry project, or one where the trapped resource is itself required for that project to
    ever finish, could plausibly never escape.
- **Why it is wrong**: this is exactly the class of bug the codebase's own comments say was
  already hunted down once (the code at line 1735 explicitly recalls fixing "a run needing 10,330
  tonnes of ore a year sank a mine sized for the 13 tonnes of bar, stayed throttled for
  centuries, and ended with its capital untouched") — but the fix addressed sizing the order
  correctly, not the maturity-date reset. A player doing everything right (noticing the shortage,
  spending real capital on the documented `buy mine` remedy, more than once, well ahead of when
  the game itself said the capacity would arrive) gets nothing for 28 years and no error, warning,
  or event ever says why: `mine_pending`/`mine_ready` are not exposed in `state` at all, so from
  the protocol's point of view the purchases simply vanished into a black box that eventually,
  unpredictably, resolved itself.
- **Reproduce**: get any resource shortage where the shortage is caused by a currently-active
  long-running project (mine happened with `steam_high_pressure` and `iron`); `buy mine` for that
  material more than once across different years while capital stays above 3000 and the shortage
  persists; watch `state.mine_capacity` and `state.resource_throttle` stay unchanged for many
  years past every quoted `ready_year`, until the demanding project itself completes.

### F5. Eminence is a genuinely different, and genuinely much smaller, hazard for the Norse — confirmed across the entire run, not just asserted by the civ file
- **Severity**: WORKS-WELL (directly answers the brief's framing question about "no court to
  denounce you to")
- **What I saw**: `state.eminence` climbed above 1.0 by year 952 and stayed there for roughly
  two-thirds of the whole run, peaking at **3.76** around year 968 and never dropping below 1.9
  again before the goal was reached. I grepped every single event message the 326-year run ever
  produced (327 `step` replies) for anything resembling the confiscation/patron-destruction
  language `03_SOCIAL_POLITICS.md` describes for Rome's eminence hazard: zero hits. The only
  standing-related events across the whole game were five instances of `"your patron dies; his
  heir must be courted afresh"` (ordinary mortality, not eminence-driven — each one caused a
  one-step `protection` dip, e.g. 0.593 -> 0.256 at year 1207, recovering the next step), ten
  `"fire in the insula district"`, and five `"banditry or a frontier war disrupts supply"` — all
  generic hazards unconnected to prominence. `reputation` itself fell steadily across the second
  half of the run (peaked ~92 around year 953, ended at 9.3) with no event ever explaining the
  decline either; it reads as the ordinary `reputation *= 0.97` per-year decay
  (simulator.py:1740, confirmed by inspection after noticing the pattern) outpacing new
  reputation-earning activity once I stopped starting fresh nodes as often in the endgame, not
  as any kind of punishment.
- **Why it is right**: this matches the civ file's `w_eminence_danger: 0.2` claim (lowest of any
  civilization in the file) and its own note, `"No state, no court, nobody to denounce you to.
  The danger here is a feud, not a treason charge."` A Rome run that let eminence sit above 3.0
  for two-thirds of a 300-year run would, per `03_SOCIAL_POLITICS.md`'s own description of the
  mechanic, expect at least an occasional confiscation or a patron destroyed specifically because
  of prominence. Norse got none. This is a genuinely different, and verified, difference in HOW
  the two civilizations must be played (directly answering the brief's Q1): a Rome player has to
  budget for eminence as a live constraint on how big and how visible to get; a Norse player, on
  this evidence, does not have to think about it at all.
- **Reproduce**: play any long Norse run past year ~950 without deliberately suppressing
  reputation/wealth growth; grep every `step` reply's `events` array for the whole run length;
  observe `eminence` sits persistently above 1.0 with no corresponding adverse event, in contrast
  to Rome's documented behaviour for the same mechanic.

### F6. Insolvency is recoverable, exactly as the fix commit describes — with an honest limit on what I personally verified
- **Severity**: WORKS-WELL, with a caveat
- **What I saw**: the deepest deficit of the run was **`capital: -126,180.0` at year 938**
  (`{"cmd":"state"}` immediately after `collegium_licensed` and `zinc_metal` both completed in
  the same step), with `revenue: 66,395.2` and `net_per_year: 32,663.5` at that moment. Watched it
  climb back with no manual intervention: -93,507.8 (939) -> -60,000.3 (940) -> -26,533.2 (941) ->
  positive by 942. No staff loss, no event message, no throttle change tied to the deficit itself
  (mine mothballing did fire separately later, see F7, for a different, shallower dip). This
  matches this codebase's own commit message (`ee83c79`) describing exactly this fix: "an
  enterprise that cannot maintain its works abandons them and they fall into disrepair... you can
  climb back", and specifically namechecks a prior Norse run that "sat insolvent for 495 years
  with three artisans, unable to recover" before the fix.
- **The honest limit**: reading `rome/sim/simulator.py`'s `step()` method (not the tech tree) to
  understand this mechanic in detail (I had specific, strong doubt after the crash in F1, and
  this is the exact mechanic the brief asked me to probe), I can see the deeper mechanism the
  commit message describes — staff bleed and abandonment of upkeep-heavy works — only engages
  after `capital < -max(4000.0, revenue * 2.0)` **and** that state persists for **three
  consecutive years** (`self.insolvent_years >= 3`). My own deepest dip (-126,180 against a floor
  around -132,790 at that point) came close to that floor in absolute terms but recovered within
  a single year, so I never personally drove the run into the staff-bleed/abandonment branch and
  cannot report first-hand what it looks like in play. What I can say directly, from watching my
  own genuine (not engineered) arrears episode: a substantial real deficit, incurred honestly
  by building two expensive things in the same year, cost nothing but patience — no staff lost, no
  technology lost, no event fired, no drama — which is a specific and reassuring answer to the
  brief's Q3 as far as it goes, short of a run that actually crosses the deeper threshold.
- **Reproduce**: build multiple expensive nodes so their combined per-step spend exceeds capital
  by a wide margin (I did this by chance building `zinc_metal` right after `collegium_licensed`);
  watch capital go sharply negative with `ended` staying `false` and no event, then watch it climb
  back over 2-4 years purely from `net_per_year` as projects finish and stop drawing.

### F7. The automatic mine-mothballing safety valve also protects the Norse economy, confirmed cross-civilization
- **Severity**: WORKS-WELL
- **What I saw**: at year 1059, right after a large `soda_leblanc`/other-project spend spike
  dropped capital from 151,136.4 to 32,561.8 in one step, the very next `step` reply's `events`
  contained `{"message": "MOTHBALLED half the iron workings; you could not pay to keep them
  running"}`, and `mine_capacity.iron` visibly halved (43,200.0 -> 21,600.0) in that same step,
  with capital recovering the following year with no further manual action from me. This is the
  same safety valve the Rome WIN report marked WORKS-WELL (its F7), now confirmed to fire
  correctly for a completely different civilization with a completely different cost structure.
- **Reproduce**: get mine capacity commissioned, then let a large, unrelated project spend spike
  push capital sharply negative in the same step; watch the next step's events for a MOTHBALLED
  message and the mine capacity actually halve.

### F8. The free tier-0 "ambient technology" cascade, and the fix that stops foreign institutions being auto-granted, both work correctly for Norse
- **Severity**: WORKS-WELL (cross-civilization confirmation of two mechanisms the Rome and Han
  playtest rounds already found/fixed)
- **What I saw**: starting the same five free tier-0 nodes Rome's WIN report used
  (`cap_heat_0700`, `cap_power_muscle`, `cap_tol_1mm`, `lnd_wheel_spoked`, `mat_leather`, all
  `cost: 0.0, founder_hours: 0.0`) and stepping once triggered the identical cascade mechanic for
  Norse: 121 completions in one step, `done_count` 4 -> 125, `revenue` 0.0 -> 681.6. Separately,
  I never once saw a Roman-flavoured institution (`civ_aqueduct_roman`, `fin_annona`, the grain
  dole, etc.) appear as `done`/granted for Norse at year 900 — they showed up only in `available`
  as buildable-if-you-want-to, matching the `FOREIGN_MARKERS` fix in commit `ee83c79` ("Han
  playtest: eight silently dropped starting techs, and Rome's institutions given to everyone").
  I did not deliberately try to break this one; I simply never saw it wrongly fire across the
  whole 326-year run.
- **Reproduce**: fresh Norse game, `{"cmd":"state"}` at year 900 shows `done_count: 4` (only the
  civ file's own four starting techs, one of them crash-affected per F1); starting the five free
  nodes and stepping cascades ~120 more completions, none of them Rome-branded institutions.

### F9. `start_blocked_reason` correctly named the scholar/artisan-count remedy this time — the fix the Rome report asked for is in and it helped
- **Severity**: WORKS-WELL
- **What I saw**: hit the same kind of headcount wall the Rome WIN report's F5 described (there,
  undiscoverable without outside knowledge). This time, `{"cmd":"why","id":"newtonian_mechanics"}`
  returned `"start_blocked_reason": "needs 3 trained scholars, you have 2.5. To get more
  scholars: build school_founded (the school is the only thing that produces scholars in
  quantity, and it grants more every year it runs); build academy_network (three academies
  produce more than one school)."` and, later, for artisans ahead of `railway`:
  `"needs 150 trained artisans, you have 85.5. To get more artisans: {"cmd":"buy","what":"slaves",
  "n":N} then manumit, though they are untrained for three years."` Both are exactly the kind of
  actionable, in-protocol guidance the Rome report's F5/N2 asked for, and both let me fix the wall
  within a couple of `send` calls with no outside knowledge needed.
- **Reproduce**: play until `available` empties out with a headcount-gated node still pending;
  `why` that node and read `start_blocked_reason`.

### F10. Rome-specific prose text (citizenship, provocatio) is shown verbatim for a Norse Viking-age game with no Roman state
- **Severity**: UNREALISTIC / CONFUSING
- **What I saw**: `{"cmd":"why","id":"citizenship"}` for Norse returns `"name": "Roman citizenship
  by grant"`, `"note": "Gives provocatio, the right of appeal, which is the difference between a
  governor executing you and Rome hearing you. Buy it with a public benefaction."`, and
  `"kb": "03_SOCIAL_POLITICS.md#citizenship"`. The Norse civ file itself says `"institutions":
  {"charter": false, ..., "note": "The thing is an assembly, not a state. No one can license you
  and no one can fund you."}` — there is no governor, no Rome, and no *provocatio* to receive in
  a 900 AD Scandinavian setting. The cost, calendar floor and prerequisite chain are all
  correctly civ-scaled (`civ_domain_factor: 1.98`, matching `commerce`(1.1) x `infrastructure`
  (1.8) exactly), so the mechanics are real and consistent; only the flavour text is wrong for
  the society playing it.
- **Why it matters**: minor next to F1-F4, but it is a real seam. `03_SOCIAL_POLITICS.md` itself
  claims "a different society would do with these same nodes... the Norse file inverts the sign
  on labour-saving technology... the whole of the Vespasian problem simply disappears" — implying
  the module's narrative, not just its numbers, is meant to read differently per civilization.
  The numbers do differ (confirmed throughout this report); the prose never does, for this node
  or for any other Rome-social-politics node I queried as Norse (`patron_local`, `identity_cover`,
  `collegium_licensed`, `school_founded` all kept their Roman framing — "Alexandrian
  physician-philosopher persona", "Licensed collegium", "the Museum" — none of which fits a
  Norse Viking-age setting either). A player reading these node descriptions in character would
  be told they are buying Roman citizenship from a governor while playing a civilization whose
  own file says explicitly there is no state to grant it.
- **Reproduce**: `{"cmd":"why","id":"citizenship"}` (or `patron_local`, `identity_cover`,
  `collegium_licensed`, `school_founded`) under `--civ norse_900ad`; read `name`/`note`.
