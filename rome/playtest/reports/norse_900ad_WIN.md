# norse_900ad / WIN

## STATUS: IN PROGRESS (report being written incrementally as I play, per instructions)

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
— this immediately found a crash bug). Findings and gameplay narrative continue below and were
appended incrementally as I played, per the instruction to write-as-I-go rather than save the
write-up for the end.

## Result

(being filled in — not yet reached)

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
