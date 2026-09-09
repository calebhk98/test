# Playtest notes — rome_100ad, session B

Rules I'm following: only look at the running game (no source/data/docs in the repo).
Session file: rome_100ad_B.json

## Setup

Started via:
    python3 rome/sim/simulator.py agent --civ rome_100ad --fog --session .../rome_100ad_B.json

The game speaks one JSON object in, one JSON object out, over stdin/stdout. I wired it up
through a FIFO + a `while true; do cat control.fifo; done > game.in` forwarder so the process
stays alive as one long-running conversation across many tool calls, with the state also
persisted to the session file as instructed.

### First impression (welcome text)

- Premise: I'm one person under Trajan in 100 AD, with modern knowledge but none of the
  industrial base. "Knowing how a thing works is free. Building it is not." Good hook.
- Goal: get as far as possible before 600 AD (the horizon). No score, just what you've built.
- Commands: state, available, why <id>, start <id>, stop <id>, step <years>, buy, bounty <id>,
  path <id> (disabled under fog), save/load, help, quit.
- Notable: slavery is modeled explicitly (buy slaves / manumit). The game calls this out itself:
  "This is available because it was the ordinary condition of production in most of these
  societies, and a model that hides it lies about the cost of everything." Strong, deliberate
  design choice — flagging it up front rather than burying it.
- Fog of war is on: I can see what's built, what's startable, and things "heard of" but not
  startable yet. Can't see the tech tree or where anything leads.

## Opening state, year 100

`state` at turn 0: capital 400, revenue 0, living_cost 216/yr, net -216/yr, founder_hours
2400/yr, 1 scholar, 3 artisans, reputation 5. Already a built-in `knowledge_risk` block warning
about future hazards I haven't triggered yet: Antonine plague (165-180), Plague of Cyprian
(249-262), Third century crisis (235-284, can get a site *sacked*), currency debasement
(190-275). I like this a lot — it's playing fair with the "you have modern knowledge" premise:
I *know* the 200s are going to be rough for a Roman enterprise, and the game tells me so upfront
rather than ambushing me. Good design.

`available` returned 299 items on turn 1 (!). 113 of those are cost-0/hours-0 "ROME ALREADY HAS
THIS" flavor entries — i.e. things Rome's baseline economy already provides, listed so you know
not to waste time reinventing them. The other ~186 are real, startable projects.

Surprise/oddity #1: scanning the actionable items, pure theory nodes — Newton's laws, the
photoelectric effect, Heisenberg's uncertainty principle, nuclear fission — are all listed as
startable *on day one in 100 AD*, for a few hundred denarii and a few months, same as "flax
cultivation." A trench (`mil_trench`) is also buildable now, and its own description says it
"becomes primary infantry defense after 1900" against machine guns that don't exist for 1800
more years. There doesn't seem to be any prerequisite gating tying abstract science to the
instruments/observations that would realistically be needed to formulate it (telescopes,
vacuum pumps, precise clocks...). You can apparently publish quantum mechanics to Trajan's Rome
the moment you step off the boat, provided you can afford the parchment. This feels like the
single biggest crack in an otherwise very carefully-thought-through premise. I did NOT test
starting one of these physics nodes to see if something downstream stops me — noting it as a
question rather than a confirmed bug.

Money is tight at the very start: cheapest "generically useful" foundational thing,
`units_standards` ("Define and publish standard length, mass, time and temperature" — the game
itself says "do this before writing any other recipe down"), costs 444 capital against my 400
on hand. Tried `start`-ing it anyway and the game accepted it — cost is evidently drawn down
over the life of the project rather than charged up front as a lump sum, so you can start
something you can't fully afford yet as long as the cash arrives before the bill does. That's a
nice, non-obvious mechanic; wasn't explained anywhere in the welcome text, I had to discover it
by trying.

Also notable: a lot of cheap technologies (e.g. `tx2_flax_fibre`, cost 9) carry a recurring
*upkeep* (40/yr) and a permanent staff draw (1 artisan) even though the up-front cost is trivial
— so "cheap" and "affordable to run" are two different questions. Good realism, but easy to miss
if you only look at the headline cost in `available` (upkeep isn't shown there, only in `why`).

## Turn 1: started units_standards

- `start units_standards` succeeded despite cost > cash on hand (see above).
- `step 1` (year 100->101): 139 baseline "Rome already has this" items all got formally
  recorded as "done" (`done_granted`) in a single lump — so the fog-of-war "ROME ALREADY HAS
  THIS" list isn't just flavor text, it's actually processed into your tech ledger over time.
  Revenue went from 0 to 666.7 essentially as a side effect of that — so it seems your income is
  driven by your recorded technology/civilizational base rather than anything you actively do
  to sell goods. Capital showed as 0.0 after this despite a positive net figure for the step,
  which confused me for a moment (see below) — resolved itself over the next couple of steps and
  I now think it's a display/accounting-timing quirk, not lost money: by year 103 capital read
  700 and matched the running total.
- `step 1` again (101->102): units_standards finished ("completed: Define and publish standard
  length, mass, time and temperature"), reputation ticked 5.0 -> 4.8 -> 5.4 -> 5.3 (small
  fluctuations turn to turn, not sure yet what drives them — I never touched anything that looks
  reputation-related).
- `step 1` again (102->103): a *second*, distinct completion fired with no corresponding
  `events` entry — `cap_measure_len` ("Reproducible length standard") auto-completed as a
  side-effect/derivative of units_standards, silently. `completed` list showed it but `events`
  was empty that turn. Minor inconsistency: two different "this thing finished" signals
  (`completed` array vs `events` array) that don't always agree with each other.
- By year 103: capital 700, revenue steady at 1000/yr, living_cost creeping up (216 -> 250 ->
  270 -> 280.5 across 3 years) even though I haven't grown my household. Between revenue 1000
  and living_cost ~280 I'm now solidly cash-positive (~690-700/yr) with nothing active. The
  early-game cash crunch was real but short (about 2-3 years) and resolved itself once that one
  foundational project landed.

## Turns 2-4: identity_cover, scientific_method, patron_local

Went after the three big "foundation" tier nodes that `why` revealed have enormous
`downstream_count` (identity_cover 2151, scientific_method 1082, patron_local 1984) versus the
leaf items (a random mid-tier item like `civ_truss_triangulated` unlocks just 4 things
downstream). This asymmetry is stark and, once you notice it via `why`, makes the early strategy
pretty obvious: rush the 3-4 huge multiplier nodes before touching any of the ~300 leaf techs.
That's a reasonable "figure out the meta" moment, but it does mean the `available` list's flat
one-line summaries are actively misleading about value without `why` — a newcomer who just reads
`available` has no way to tell `identity_cover` (2151 downstream) from `tx2_button_horn` (0
downstream) except by cost, and cost doesn't track it (button: horn material is *cheaper* than a
lot of the small stuff and looks just as "startable now").

- Confirmed capital genuinely goes **negative** — saw -632 and -401 at different points. No
  bankruptcy trigger, no interest charge that I've noticed, no forced project cancellation. It
  just gets pulled back to positive by revenue over the following year or two. This reads as
  "personal overdraft with your banker" which is plausible for a well-connected persona, but the
  game never says anywhere that debt is possible or safe — I only found out by watching the
  number go negative and nothing bad happening. A one-line explanation of what negative capital
  means (and whether it's ever dangerous) would help.
- `scientific_method` (200 capital, 350 of my hours, 2 years, 20% fail risk) finished
  successfully. Notable events fired: "changes the society: w_magic_fear, w_novelty" (visible
  named internal weights - a bit of the machinery leaking through the fog, deliberately or not)
  and "fire in the insula district" (looked like flavor/ambient noise, no visible stat impact).
  `scandal` appeared and has been climbing since (0 -> 1.56 -> 5.26) — presumably from publicly
  contradicting Aristotle/Galen, which the item's own note warned would provoke "organised
  opposition, not curiosity." Good thematic follow-through. I don't yet know what scandal *does*
  at higher values — no threshold has been reached or explained.
- `patron_local` (halves incoming suspicion, 1200 capital, 1984 downstream) finished, and one
  year later: **"your patron dies; his heir must be courted afresh."** I liked this a lot — you
  can't just buy a benefit permanently and forget about it, the social world underneath keeps
  moving. `protection` went from 0 to 0.106 and seems to have survived the patron's death,
  though I don't know if it will decay or if I actually need to spend again to keep it.
- Tried `why corpus_dispersed` — this id is *named directly by the game itself*
  (`knowledge_risk.better_hedge_available` in `state`, present since turn 0) as the better
  mitigation against losing technologies to a sacked site. But asking `why` about it returns
  `"you have never heard of that."` So the fog-of-war system surfaced a specific, concrete
  recommendation for something it then refuses to tell me anything about or let me pursue. That
  feels like a genuine inconsistency rather than intentional mystery — a hint that points at a
  locked door with no visible handle.

## Turns 5-9: fixing the economy, and a significant finding about slavery (year ~113-134)

Cash flow went properly upside down after `workshop_first` (900/yr upkeep on top of everything
else): capital hit -1, then -1401, then -2801, then -3232 while I hunted for a fix, with
`net_per_year` sitting around -450 to -700. No bankruptcy trigger, no forced liquidation, no
warning message of any kind — it just quietly went further into the hole turn after turn. Found
the fix by brute-force `why`-ing a bunch of `fin_*` items: several of them are absurdly good
value — `fin_seigniorage` (cost 25, +1000/yr revenue, forever, for a 0.2-year project) is the
standout, but `fin_arbitrage` (37.5 -> +300/yr), `fin_tariff` (47.5 -> +200/yr),
`fin_promissory_note` (28 -> +100/yr), `fin_cheque` (35 -> +150/yr), `fin_discounting`
(47.5 -> +250/yr) and `fin_endorsement` (47.5 -> +200/yr) are all in the same league. Total
outlay for that batch: under 300 capital and a few hundred hours. Total revenue gained: over
2000/yr, permanently. That took net income from -700/yr to +1234/yr in a single 2-year step, and
by year 134 revenue was 9374/yr against 1878 living cost. This looks like a real balance hole —
these low/no-downstream "financial instrument" nodes are wildly better return-on-investment than
anything else I've seen in the tree (including the flashy foundational nodes with 1000+
downstream counts), and nothing in the game flags them as unusually good. A player who doesn't
methodically `why` their way through the `fin_` id prefix would likely never find them and could
plausibly get stuck in the same debt spiral I was in for a while, not knowing a fix existed a few
lines away.

`corpus_written` ("write down everything you know" — 6000 of my own hours, 10-year minimum)
completed at year 131. This is clearly meant to be the thematic centerpiece of the whole
premise — you're not just building things, you're transcribing your modern knowledge into a
form Rome can keep. It's genuinely the best moment in the playthrough so far: a real emotional
payoff for the setup. Two things stood out around it:
  - **Wasted hours while calendar-gated.** `corpus_written` needed 6000 founder-hours but has a
    hard 10-year floor. I had nothing else running in parallel for a chunk of that time, so my
    2400 hrs/yr kept pouring into it — `why`/`state` showed `founder_hours_left: -1200` (i.e.
    it had absorbed 1200 more hours than it could ever use) while still not finished, because
    the calendar hadn't caught up. The engine doesn't warn "this project is capped on time, not
    effort — go start something else with your spare hours" — I only noticed because I was
    reading `state` closely. Feels like a real trap for anyone not tracking it.
  - **`knowledge_risk` visibly improved once it landed**: `hedged_by` changed from `null` to
    `"corpus_written"`, `loss_chance_if_a_site_is_sacked` dropped 0.8 -> 0.45, and
    `fraction_lost_when_it_happens` dropped 0.4 -> 0.22. So the mechanic I'd been curious about
    since turn 0 paid off exactly as advertised. Good. `corpus_dispersed` is *still* listed as
    `better_hedge_available` and *still* returns "you have never heard of that" from `why` — so
    that one remains a visible-but-unreachable goal five turns later.

**The slavery finding.** At year 134 I checked full `state` out of habit and found
`"slaves": 20, "freedmen": 7`. I never issued a `buy slaves` command — not once, not even to
test it. Nothing in the `events` log at any point said anything like "you purchase slaves" or
"the workshop is staffed with slaves" — the only events I saw were project completions and two
ambient ones ("fire in the insula district", "banditry or a frontier war disrupts supply").
`artisans` also grew organically from 3.0 to 17.86 over the same stretch without me hiring
anyone through a visible command. My read: as `workshop_first` and the trade-route venture spun
up their `hired_labour` requirements (carpenters, labourers, scribes), the simulation quietly
satisfied part of that demand with slave labour on its own, and later freed some of them into
`freedmen`, with no on-screen decision point and no line in `events` marking it. This sits
awkwardly against the game's own stated design philosophy from the welcome screen: slavery is
presented as something the *player* opts into via an explicit `buy slaves` action, specifically
because "a model that hides it lies about the cost of everything." Having it happen silently as
a side effect of ordinary economic growth, with no notification, is arguably the game doing the
exact thing its own design note says it refuses to do. This is the single thing from the whole
session I'd most want a developer to look at — it undercuts a principle the game states about
itself. (I'm inferring the mechanism from the state diff, since I'm not allowed to read the
source to confirm it — noting that as a real limit on my confidence here, but the observation
itself — unexplained slaves appearing with zero prompt or log entry — is not in doubt.)

Once I noticed, I manumitted all 20 via `{"cmd":"buy","what":"manumit","n":20}` — this part of
the mechanic is well done: it cost zero capital, `reputation` jumped 25.8 -> 29.6, and `artisans`
(my effective workforce) jumped from 17.86 to 26.86, a bigger gain than the raw headcount change
would suggest — matching the welcome text's claim that freed people "work better." `living_cost`
also rose (1878 -> 2148), presumably because freedmen draw wages where slaves didn't. So the
manumission mechanic itself is thoughtful and consistent with the game's stated values — my
complaint upstream is specifically that the slaves arrived silently, not that the freeing
mechanic is bad.

**Update, year 144**: stepped 10 more years with *nothing active* (no projects running at all)
and `slaves` went from 0 back up to 24, again with no event logged. This rules out "it only
happens when a specific project's hired_labour needs filling" — it's happening as a passive,
ongoing background process tied to upkeep of things I've already built, every time regardless of
what I'm doing. Manumitting is not a one-time fix; it seems to be something I'd need to keep
doing every few turns for the rest of the game if I don't want to be a slaveholder between
checks. Freedmen are now at 51 (up from 27) after this second manumission. I'll keep checking
`slaves` periodically and manumitting as I go, and keep noting the cadence.

## Turns 10-14: chasing more `fin_` revenue, then the Antonine plague (years 129-180)

Kept mining the `fin_` prefix for cheap high-ROI items (`fin_lottery` +700 net/yr,
`fin_marine_insurance` +600 net/yr, `fin_gambling_house` +400 net/yr, `world_map` +450 net/yr,
downstream 14) and capital snowballed hard: 10718 (y.134) -> 26812 (y.144) -> 41703 (y.152) ->
72381 (y.162). Net income climbed into the thousands per year. The early cash-crunch problem is
now the opposite problem — I have far more capital than I have good places to put it, since I've
already picked the obvious high-ROI low-cost nodes and the next tier (`fin_hotel`,
`fin_theatre_business`, `fin_plantation`, `fin_department_store`, all 5000-16000 capital) mostly
have *worse* ROI than the cheap stuff, sometimes barely breaking even on upkeep. Fascinating
inversion of normal game-econ expectations: bigger buildings are not better investments here.
`fin_plantation` — the literal slave plantation — actually nets *negative* cash flow (800
revenue vs 1000 upkeep) in this model, which I found sort of grimly funny either way it was
intended.

Also confirmed the slave auto-acquisition pattern a second time on a longer, unattended stretch:
manumitted 6 at y.152, then after 10 untouched years (to y.162) slaves were back at 11; after a
further 14-year stretch with several disasters going on (see below) they were at 33. So it's not
occasional, it's a steady background drip roughly proportional to time elapsed / economic
activity, not to anything I'm actively doing. I've now manumitted four separate times (20, 24,
6, 11, 33 people — 94 total) over the session's ~80 in-game years, and each time it's free,
raises reputation, and improves my effective workforce. There does not seem to be any way to
simply *turn off* future slave acquisition rather than launder it after the fact each time I
remember to check.

**The Antonine plague** hit right on schedule, starting exactly at year 165 as the `state`
forecast said it would from turn zero. It's modeled as a recurring per-year event, not a single
hit: I saw `"Antonine plague: staff -28%"` fire *eight separate times* across 165-176 (165, 166,
168, 169, 171, 172, 175, 176), each one cutting scholars/artisans by 28% again on top of whatever
they'd recovered to since the last hit. `scholars` dropped from 1.0 to 0.72 and bounced around;
`artisans` swung from ~14 down toward 8 and partway back repeatedly. `reputation` drifted down
from ~25 to 14.8 over the plague years. One unrelated event also fired mid-plague: "banditry or a
frontier war disrupts supply" (171) — no visible stat tag on it that I could isolate against the
plague noise.

The one thing that surprised me: **`revenue` never moved during any of this** — it sat dead flat
at 12971.5 for the entire 165-180 stretch despite repeated ~28% staff losses. Whatever drives my
income in this model, it isn't current headcount — it reads much more like "reputation/completed
technologies" than "people currently working for you." That's a soft realism gap: a plague that
guts your workshop staff eight times over fifteen years should, I'd think, cost you *something*
in output, and here it cost nothing directly (my `living_cost` rose and `net_per_year` fell, but
that was because living costs crept up, not because revenue fell).

## Turns 15-18: chasing `corpus_dispersed`, years 180-184

With the plague past and the Third Century Crisis (235-284, the one hazard flagged as able to
*sack a site*) still ahead, I went back to `corpus_dispersed` — the node `state` had been
pointing at as `better_hedge_available` since turn zero. This time `why corpus_dispersed` finally
answered instead of "never heard of that" — worth correcting myself here: earlier I called this
an inconsistency, but it now looks like fog-of-war working as intended: it became visible once
its prerequisite (`corpus_written`) was actually done, it just wasn't visible before that. Fair
enough — I was wrong to call it a bug earlier; it's closer to "the game pointed at a specific
future goal by name before I could reach it," which is a reasonable design choice, if a slightly
disorienting one the first time you hit it.

Once visible, `corpus_dispersed`'s own description calls it "THE highest expected-value node in
the tree, and it is cheap" and says it's specifically "what carries the programme through
235-284 AD" — i.e. it exists to blunt the exact sacking risk I'm about to face. Its direct
prerequisite is `printing_press`, which `why` still refuses to acknowledge
("you have never heard of that") — so `printing_press` itself hasn't surfaced in `available`
yet. I spent several turns guessing at plausible precursors by name and starting the cheap ones
that showed up in `available`: `prn_woodblock_carving`, `tx2_printing_block`, `mt2_type_metal`,
`prn_wire_mould_deckle`, then `prn_relief_printing` and `mfg_mould` once those appeared. All six
completed without issue, but `printing_press` never appeared in `available` and `why
printing_press` still comes back unknown. I'm stopping the hunt here rather than continuing to
guess blindly — this is the one point in the session where the fog-of-war design worked against
me in a way that felt like friction rather than mystery: the game told me by name, unprompted,
that a specific node is the best thing in the entire tree and exactly what I need for an
upcoming crisis, then gave me no way to see how far away it actually is or whether I'm even on
the right branch toward it. A numeric hint (e.g. "2 more technologies away" without naming them)
would have made this a fair puzzle instead of a guessing game with no feedback signal.


