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

