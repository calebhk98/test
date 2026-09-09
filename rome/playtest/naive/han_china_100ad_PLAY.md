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

