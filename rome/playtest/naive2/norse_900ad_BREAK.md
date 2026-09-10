# Playtest: norse_900ad — attempting to break the simulator

Session file: /home/user/test/rome/playtest/naive2/norse_900ad_BREAK.json
Started: (see log below)

Rules I'm following: only interact with the running program. No reading source, data, docs, or other notes.

## Log

### Setup

Main session command (as given):

    cd /home/user/test
    python3 rome/sim/simulator.py agent --civ norse_900ad --fog --session /home/user/test/rome/playtest/naive2/norse_900ad_BREAK.json

The `--session` file means I can drive it one command per invocation:

    echo '{"cmd":"state"}' | python3 rome/sim/simulator.py agent --civ norse_900ad --fog --session .../norse_900ad_BREAK.json

Opening position (year 900): capital 400.0, revenue 232.7, living_cost 230.0,
net_per_year 2.8, founder_hours 2400, 132 techs "granted", 0 earned,
0 employees, credit_limit 1912.9 at 11.83% interest.

**Observation 1 (flavour/realism, low confidence it's a bug):** all revenue for a
Viking-age Scandinavian comes from `med_cataract_couching` (166.7) and
`med_trepanation` (66.7). The 900 AD Norse starting kit apparently makes you an
itinerant eye surgeon. Also `state` says `"founder_ages": false` — the founder
never gets old across a 500-year horizon (900 -> 1400). Flagged for later; see
"Immortal founder" below.

**Observation 2 (realism):** the 86-item `available` list includes other
civilisations' technologies with no apparent gating: `civ_arch_roman` (Roman
masonry arch), `fin_annona` (the Roman grain dole), `hom_cosmetics_roman`,
`fud_chinampa` (Mexica floating gardens, in Scandinavia), `mat_obsidian_blade`,
and `mil_plate_armour_firearms` ("plate armour proof against firearms") in the
year 900, five centuries before firearms exist. The last one is the one I'd
call a real content bug.

**Observation 3 (candidate exploit):** six nodes are listed at cost 0.0,
your_hours 0.0, least_years 0.0, chance_of_failure 0.0 —
`civ_arch_roman`, `fin_annona`, `fin_argentarii`, `fin_collegium`,
`fin_societas`, `hom_cosmetics_roman`. Free instant technologies. Testing next.

