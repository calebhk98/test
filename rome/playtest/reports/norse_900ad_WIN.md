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

(being filled in as I play)

## Result

(being filled in — not yet reached)

## FINDINGS

(being filled in as I go)
