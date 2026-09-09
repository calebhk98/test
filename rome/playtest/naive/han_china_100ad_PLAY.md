# Playtest notes — Han China 100 AD

Rules I'm following: never read repo files, only interact with the running
simulator. Session file: rome/playtest/naive/han_china_100ad_PLAY.json

## Session log

Started the simulator. Intro text (paraphrased): I'm one person dropped into
a pre-industrial society (Later Han Empire, starting 100 AD) with modern
knowledge but no modern industry. Knowing is free, building costs my hours,
other people's hours, money, materials, years. Nothing happens until I make
it happen — I start projects then step time forward. Goal: advance as far as
possible before a horizon at year 600. No score, just what I've built.

Commands: state, available, why <id>, start <id>, stop <id>, step <years>,
buy (forest/mine/slaves/manumit), bounty <id>, path <id> (disabled under fog),
save/load, help, quit.

Fog of war is ON: I see what I've built, what I can begin (one-liner each),
and things I've heard of but can't start yet. Can't see the tree or where
things lead.

First reaction: the slavery mechanic being explicit and buyable (with a
manumit option that's flagged as "the decent thing") is a striking design
choice — worth watching how it plays out.

### Opening moves (year 100-106)

`state` at year 100: capital 400, revenue 0, living_cost 216/yr — I am
losing money just by existing, before building anything. `available` showed
250 items already, even under fog. That's a startlingly deep tech tree for
turn one.

Noticed several items with cost 0.0 / hours 0.0 sitting in `available`
(civ_arch_roman, fin_annona, fin_argentarii, fin_collegium, fin_societas,
hom_cosmetics_roman). Started all of them since they were free. This turned
out to be a big deal: stepping one year caused a cascade — done_count jumped
from 12 to 146 in a single step. Most of that (140) is "done_granted" versus
only 6 "done_earned" — so there's a large pile of ambient/background
technologies that belong to "being a Han Chinese subject in 100 AD" that get
revealed/granted once you do practically anything, rather than things I
built. That's a sensible modeling choice (you don't have to personally
reinvent the wheel your neighbours already have) but it was confusing at
first: I thought I'd somehow completed 134 research projects for free by
starting six trivial ones. The distinction between "granted" (ambient/starting
knowledge) and "earned" (built by me) is the key thing to watch, not
done_count.

Capital went to 0.0 after year 1, then actually negative (-8.0) after year
3 while several projects were running concurrently (identity_cover,
serpentine powder, three fibre techs, two labour-contract techs all at once).
Nothing broke — no bankruptcy penalty, game kept running, capital recovered
to +312.9 by year 106 once projects finished and revenue caught up. I
expected an overdraft to be some kind of failure state; it isn't (so far).
Worth noting the design doesn't stop you from overcommitting — it just lets
your ledger go red and trusts you to recover, which feels realistic but I
was not warned about it anywhere. A one-line "you are running a deficit"
event would have been nice; I only knew because I happened to check `state`.

Started `identity_cover` (the Alexandrian physician-philosopher cover
identity) early on instinct — it explicitly "reduces all future suspicion"
and its `why` output showed downstream_count 2157, i.e. it (or the "founder
hours" metaphor generally) touches almost the entire tree. Also noticed
`arrival_orientation` (six months of listening before acting) is flagged
explicitly in its own text as OPTIONAL and no longer gating anything, with a
little authorial aside: "a model that forces the cautious opening is not a
model, it is an opinion." I liked that — skipped it, playing fast or fully
informed is a genuine player choice here, not a trap.

Grabbed `mil_serpentine_powder` (granulated gunpowder) mostly because it was
cheap (20.1) and the name jumped out — turns out `mil_gunpowder_base` is
already a prerequisite I apparently have (granted?), so China starts with
proto-gunpowder knowledge already assumed. Neat civ-flavour touch if true.

By year 106: reputation 12.8, eminence 0.08, protection 0.049, familiarity
0.437 — four slow-building social/political meters whose purpose I don't
yet understand (no in-game explanation of what they unlock or threaten, only
that suspicion is the danger one to watch, currently pinned at 0).

`available` count has grown from 250 -> 383 -> 390 as I complete things,
each visible item still shown one-line/fog-of-war style. No way to see the
tree shape, only breadth right now. It genuinely feels like exploring a
research tree blind, which is the stated design.

### Years 106-156: building out an economic/scientific base

Kept a loop going: check `available`, start a batch of affordable things,
`step` several years, repeat. Economy snowballed nicely: capital went from
0 -> ~1000 (yr136) -> ~5500 (yr156), revenue climbed from 778 to 2719/yr,
artisans grew from ~4 to 8.46 automatically (I never explicitly hired
anyone — headcount seems to grow on its own from active projects/reputation).
Scholars stayed pinned at 1.0 the entire time despite building multiple
"institution" techs (curriculum, doctorate, research group, referee, funded
programme) — I expected those to grow my scholar headcount and they didn't,
which was confusing; I never found a `buy scholars` or hire command, only
`buy` for forest/mine/slaves/manumit. If scholar count matters for research
speed I don't know how to increase it deliberately.

Random flavour events fire during `step`: several "fire in the insula
district" messages with no visible consequence in the numbers I could see,
and once "stopped maintaining 1 works that cost more than they returned" —
i.e. the game will auto-abandon an unprofitable holding rather than bleed me
forever, which is a nice bit of automatic housekeeping I wasn't expecting
and wasn't warned about either.

One genuinely delightful event: completing "Controlled experiment,
hypothesis, replication, publication" (the scientific-method bundle) fired
`"changes the society: w_magic_fear, w_novelty"` — i.e. the tech chain
doesn't just unlock more tech, it measurably moves the culture's underlying
belief weights (fear of magic down, openness to novelty up, presumably).
That's the first sign the world model is reacting to what I've taught it,
not just gating a tree.

The `knowledge_risk` block in `state` has been climbing the whole game —
technologies_at_risk 5 -> 18, expected loss per sacking 1.6 -> 5.8 — and
every single state dump repeats the same line: "there is said to be a way
to guard against this; you have not found it yet." I went looking for it
under fog (grepped my own `available` dump for library/archive/backup/
monastery/vault/secret/scatter) and found nothing yet at year 156. This is
good tension design — the risk clock is visibly ticking toward the Yellow
Turban rebellion (184-205) and I still haven't found the mitigation — but
after ~10 checks of the same unresolved hint I did start to find the
repetition a little naggy rather than ominous.

The single most striking thing so far: `why water_power_scale` returned a
note field containing a literal developer audit comment left in the game
content itself: *"[AUDIT: this node does not declare the capability rung it
needs. An automated pass once inferred one, and an independent review found
that EVERY inferred rung it sampled was wrong, so all of them were reverted.
The gap is left visible on purpose: a missing prerequisite you can see beats
a wrong one you cannot.]"* That is remarkably honest — the game is telling
me, in character as a knowledge-note, about a limitation in its own
procedural content generation, and defending the design choice to leave a
visible gap rather than a silently-wrong one. I did not expect a simulation
like this to be self-aware about its own data quality in the player-facing
text. It's the kind of thing I'd have assumed was left in by accident, but
the framing ("left visible on purpose") reads deliberate.

Also notable: the tech tree happily offers wildly anachronistic, era-skipping
jumps very cheaply once a few prerequisites are met — e.g. `mt2_basic_converter`
("Basic Bessemer converter for steel from iron-ore matte", historically 1856)
was sitting in my available list at year ~146 for a mere 200 capital, right
next to buttons and paperclips in the sorted-by-cost list. Mustard gas
(`mil_chemical_mustard`) and general-purpose bombs (`mil_bomb_general_purpose`)
were both available for ~41-46 capital as early as year 106, cheaper than a
lot of textile odds and ends. I chose not to build either — partly roleplay,
partly curiosity about whether the game would react — but their presence,
priced like a commodity, is a pointed reminder of what "carrying modern
knowledge into the past" actually implies once you stop being precious
about it. Worth trying in a future playthrough to see what the game does if
you actually pull that lever.

Started `water_power_scale` (line-shaft power: mill + bellows + stamps +
paper mill + boring mill + lathe all off one shaft) at year 156, cost 5085.8,
revenue 2200/yr, downstream_count 1276 — clearly a load-bearing mid-game
infrastructure piece. Its own note text again has the Rome-comparison
flavour ("Rome already has this... what's missing is applying it to
anything other than grinding grain") that a lot of these entries carry —
the writing consistently frames Han China's opportunity against what Rome
is doing in parallel, which is a nice worldbuilding touch given the chosen
civ.

### Years 156-205: the economy takes off, then the Yellow Turban rebellion hits

Kept queueing batches (financial techs, manufacturing presses, cold
storage, marine insurance, Newton's laws, regression/control-group
statistics, positional decimal notation) and stepping in big jumps. The
snowball got dramatic: capital went 5497 (yr156) -> 15426 (yr166) -> 74787
(yr184), revenue 2719 -> 5760 -> 10949/yr, artisans 8 -> 13 -> 16. It felt
genuinely good, like the game was rewarding sustained investment with
compounding returns, and I got a little complacent about the looming
hazard I'd been warned about since turn one.

At year 184 the Yellow Turban rebellion arrived exactly on schedule
(`in_progress` flipped true). Over the next 21 years, stepping through it:
- Six separate "a site is sacked" events (184, 186, 189, 191, 195, 201,
  203 — more than one per sack_chance_per_year=0.2 would suggest across 21
  years, so the odds bit repeatedly).
- One "banditry or a frontier war disrupts supply" event.
- Capital cratered from 74,787 to a low around 14-21k over the course of
  it — a ~70% wealth loss even though revenue never stopped flowing. I
  never got an explanation of what exactly the "sack" spends capital on;
  I just watched the number fall.
- Two explicit "KNOWLEDGE LOST" events: at year 195, "8 technologies
  forgotten (the corpus was never printed and dispersed)", and at year 201,
  "5 technologies forgotten" for the same reason. done_earned dropped from
  71 to 58 — thirteen techs I had actually built with my own hours, gone,
  permanently (nothing since has restored that count). This is the single
  harshest, most consequential moment of the game so far, and it landed
  as a direct, legible punishment for a warning I'd been shown at every
  single `state` call and had failed to act on.

That loss message ("the corpus was never printed and dispersed") was also
the answer to the running "there is said to be a way to guard against
this" hint: right after the losses, a new item appeared in `available`:
`corpus_written` — "Write the corpus: everything you know, in plain
quantitative Greek and Latin" — prerequisites `scientific_method` +
`units_standards` (both of which I'd already done, apparently coincidentally,
months before I had any idea this was the payoff). Its own text is
unusually direct for this game: *"The largest single call on your personal
hours in the entire game, and the one you must not cut. Write plainly and
with numbers. The alchemists' habit of deliberate obscurity destroyed
centuries of work."* Founder-hours cost: 6000 (versus a 2400/year personal
budget — this alone is two and a half years of nothing but writing), a
961-capital cost that's trivial by comparison, and a 10-year calendar
floor. I started it immediately at year 205, too late to save the 13 techs
already lost, but presumably in time for the next hazard window (Three
Kingdoms fragmentation, 220-280, though that one is flagged
`sacks_a_site: false` so maybe moot for this particular risk).

This is worth calling out as the best-designed moment I've hit so far: the
game telegraphed a real, specific, escapable danger from the very first
`state` call, let me ignore it for a hundred years while I chased visible
economic growth, then cashed in the consequence in a way that was painful
but fair — and the fix was always sitting right there once I had the two
unglamorous prerequisites (a units-of-measure standard and the scientific
method) that I'd built for unrelated reasons. I do think the repeated,
verbatim "you have not found it yet" line across ~15 `state` calls was more
naggy than suspenseful in the moment-to-moment — a version that varied its
wording, or hinted slightly harder as the risk number climbed, would have
sold the tension better without giving away the answer.

One open confusion: I still don't know what exactly a "sack" *costs* beyond
capital and the explicit knowledge-loss lines — whether it kills staff,
destroys a specific building, or is purely an abstraction of "you lost a
site's worth of value." `staff_loss` in the hazard block has stayed `null`
throughout, so either it's not modeled for this hazard or it's a fogged
field. I'd have liked one line in the event log translating "a site is
sacked" into what concretely changed, the way the knowledge-loss line did.

