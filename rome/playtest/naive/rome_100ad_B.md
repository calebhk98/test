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


