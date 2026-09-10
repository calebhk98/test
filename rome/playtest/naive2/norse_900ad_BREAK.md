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

---

## FINDING 1 — `NaN` / `Infinity` in a numeric argument corrupts the game permanently (HIGH confidence, real bug)

Python's `json.loads` accepts the non-standard literals `NaN`, `Infinity` and
`-Infinity`. The engine's guards are all of the form "must be greater than
zero", which `NaN` silently passes (every comparison with `NaN` is false), so
`NaN` flows straight into `capital`.

Reproduce from a completely fresh session:

    $ printf '%s\n' '{"cmd":"hire","trade":"labourer","n":NaN}' \
                    '{"cmd":"buy","what":"forest","n":999999}' \
                    '{"cmd":"state"}' \
      | python3 rome/sim/simulator.py agent --civ norse_900ad --fog --session /tmp/fresh.json

Actual replies:

    {"ok": true, "hired": "labourer", "n": NaN, "you_now_employ": NaN, "annual_wage_bill": NaN, "capital": NaN}
    {"ok": true, "bought_ha": 999999.0, "forest_ha": 999999.0, "capital": NaN}
    {"ok": true, "year": 900, "capital": NaN, ... "living_cost": NaN, "net_per_year": NaN ...}

Consequences:
* `capital` is `NaN` forever; every affordability check is `cost > capital`,
  which is false against `NaN`, so **everything is free**. I bought 999,999 ha
  of coppice with 400 denarii, and in another run hired 50 scholars and 50
  millwrights at once (the market only supplies 575 millwright-hours a year).
* The save file is written containing the bare token `NaN`, which is not legal
  JSON. Any non-Python consumer of the session file will fail to parse it.

Related, same root cause:

    {"cmd":"bribe","amount":Infinity}
      -> {"ok": true, "bribed": "scandal 0.00 -> 0.00 for inf denarii", "capital": NaN}
    {"cmd":"work","trade":"scholar","hours":NaN}
      -> {"ok": true, "trade": "scholar", "hours": NaN, "earned": NaN, "capital": NaN,
          "your_hours_left_this_year": 0.0}
    {"cmd":"step","years":Infinity}
      -> {"ok": false, "error": "internal error handling that command: OverflowError:
          cannot convert float infinity to integer. The game is intact; try something else."}

The last one is caught politely, but it shows the `years >= 1` check also lets
`Infinity` through; it only fails later at `int()`.

**Missing type check in `hire` specifically.** `buy` validates the type of `n`
("n must be a number") and `start` validates the type of `id` ("id must be a
string, got int"), but `hire` does not:

    {"cmd":"hire","trade":"labourer","n":"5"}
      -> {"ok": true, "hired": "labourer", "n": "5", "you_now_employ": NaN,
          "annual_wage_bill": NaN, "capital": NaN}

A string "5" is accepted and multiplied into the wage bill, producing `NaN`.

Confidence this is a bug rather than intended: very high.

## FINDING 2 — the `why` cost breakdown does not add up (HIGH confidence)

`why` presents an itemised cost with a `total`, but the total is always exactly
1.4x the product of the parts. The factor is never named anywhere.

    $ printf '{"cmd":"why","id":"units_standards"}\n' | <agent>
      "cost": {"labour": 300.0-ish..., "base_total": 444.00, "civ_domain_factor": 1.1,
               "material_distance_factor": 1.0, "opposition_factor": 1.0,
               "price_index": 1.0, "total": 683.80}

    444.00 x 1.1 x 1.0 x 1.0 x 1.0 = 488.40, but total = 683.80 = 488.40 x 1.4001

Checked across seven nodes with different base costs and civ factors
(`units_standards`, `identity_cover`, `arrival_orientation`, `ag2_hopping`,
`sea_lead_sheathing`, `fud_chinampa`, `fin_inn`): the ratio is 1.4000-1.4001
every time. So there is an undisclosed constant 1.4 overhead multiplier that
the "here is why it costs this" display omits. Either the breakdown is
incomplete or a factor is being applied twice. Confidence it is wrong as
presented: high (the breakdown is explicitly offered as the explanation of the
total).

## FINDING 3 — free-technology cascade (MEDIUM-HIGH confidence it is unintended)

Six nodes are offered at cost 0.0 / your_hours 0.0 / least_years 0.0 /
chance_of_failure 0.0 on turn one. Start all six, `step 1`, and all six
complete in the same year for nothing:

    {"cmd":"start","id":"civ_arch_roman"}   ... also fin_annona, fin_argentarii,
                                                fin_collegium, fin_societas,
                                                hom_cosmetics_roman
    {"cmd":"step","years":1}
    -> {"ok": true, "completed": [6 entries, all "year": 900], ...
        "reputation": 10.2,  (was 5.0)
        "credit_limit": 3750.7,  (was 1912.9)
        "done_earned": 6}

Completing them unlocks three more free instant nodes (`civ_aqueduct_roman`,
`civ_insula`, `civ_sewer_roman`), which also complete for nothing. Net effect
of two turns and zero denarii: reputation 5.0 -> 11.7, credit limit
1912.9 -> 4276.9 (2.2x), 9 technologies earned.

The engine agrees the cost should not be zero — `why civ_arch_roman` reports
`"civ_domain_factor": 3.06` — but the base cost is 0.0 so the multiplier has
nothing to bite on. Doubling your borrowing power on turn one for free is the
part I would call broken.

## Things I attacked and could NOT break (arithmetic/argument guards)

All of these were rejected cleanly, with a useful message and no state change:

    {"cmd":"step","years":0}            -> "years must be >= 1"
    {"cmd":"step","years":-3}           -> "years must be >= 1"
    {"cmd":"step","years":0.25}         -> "years must be >= 1"
    {"cmd":"work","trade":"scholar","hours":-1000}      -> "hours must be greater than zero"
    {"cmd":"work","trade":"scholar","hours":1000000000} -> "you have 2400 of your own hours left this year, not 1000000000"
    {"cmd":"hire","trade":"labourer","n":-5}   -> "n must be greater than zero. Nothing was changed."
    {"cmd":"fire","trade":"labourer","n":5}    -> "you employ no labourers"
    {"cmd":"buy","what":"slaves","n":-10}      -> "n must be greater than zero, got -10."
    {"cmd":"buy","what":"manumit","n":10}      -> "you have no slaves to free"
    {"cmd":"buy","what":"forest","n":-100}     -> "n must be greater than zero, got -100."
    {"cmd":"bribe","amount":-1000}             -> "amount must be greater than zero."
    {"cmd":"commission","trade":"smith","hours":-500} -> "hours must be greater than zero."
    {"cmd":"train","trade":"engineer","n":-3}  -> "n must be greater than zero."
    {"cmd":"buy","what":"mine","material":"unobtainium","n":-500} -> "n must be greater than zero, got -500."
    {"cmd":"start","id":"nonexistent_thing"}   -> "unknown node id ..."
    {"cmd":"nosuchcmd"}                        -> "unknown cmd ..."
    not json at all                            -> "invalid JSON: Expecting value: line 1 column 1 (char 0)"
    {"cmd":"buy","what":"forest","n":[1,2]}    -> "n must be a number"
    {"cmd":"start","id":123}                   -> "id must be a string, got int."

No stack traces escaped; the one internal error (`step years:Infinity`) was
caught and reported as JSON, as the docstring promises.

Minor: the "unknown cmd" error lists only `state, available, why, path, start,
stop, bounty, buy, step, quit` — it omits `work, labour, hire, fire, train,
commission, mothball, restore, bribe, policy, save, load, help`, all of which
`help` documents and all of which work.

## Confusing / unrealistic things noticed

* `labour` for a **Norse** civilisation returns Rome-specific flavour: mason
  "Rome has these in abundance and they are good", plumber "Roman plumbarii are
  skilled and numerous", millwright "Water-mill builder. Rome has them",
  engineer "Rome has military and hydraulic engineers under state employ".
  Rome is 400 years gone by 900 AD and this is Scandinavia.
* `electrician` note reads "Cannot exist until Module 50 does" — internal
  authoring jargon leaking into player-facing text.
* `mil_plate_armour_firearms` ("Plate armour against firearms") is startable in
  the year 900, with a note about muskets and the year 1700. `direct_prerequisites`
  is `[]`.
* `fud_chinampa` (Mexica floating-garden agriculture) is startable in Scandinavia.
* `done_granted` rose from 132 to 134 between year 900 and 902, although the
  help text says the society's existing knowledge is credited "in the first year".

---

## FINDING 4 — fog of war is completely defeated by `start` error messages (HIGH confidence)

The rules of fog are stated by the program itself: *"You cannot see where
anything leads, and there is no way to view the whole tree."* `why` and `path`
enforce it:

    {"cmd":"why","id":"point_contact_transistor"}
      -> {"ok": false, "error": "you have never heard of that. ..."}
    {"cmd":"path","id":"point_contact_transistor"}
      -> {"ok": false, "error": "you cannot plan a route to something you have not discovered. ..."}

`start` does not:

    {"cmd":"start","id":"point_contact_transistor"}
      -> {"ok": false, "error": "missing prerequisites: galena_detector, gp_whisker_forming,
          micrometer_gauges, prc_lapping_plate, quantum_solidstate_theory, single_crystal,
          vacuum_tube"}
    {"cmd":"start","id":"zinc_metal"}
      -> {"ok": false, "error": "missing prerequisites: cementation_steel, refractory_fireclay"}

That is a free prerequisite oracle for any id, discovered or not, and it
recurses. I wrote a 20-line breadth-first crawler that does nothing but issue
`start` on unknown ids and parse the error text. From the single seed
`point_contact_transistor` it mapped **163 nodes — the entire ancestor closure
of the goal — in 8 rounds**, on a fresh fogged Norse session, without ever
building anything:

    round 1 new 7   total known 8
    round 2 new 24  total known 32
    round 3 new 37  total known 69
    round 4 new 38  total known 107
    round 5 new 25  total known 132
    round 6 new 23  total known 155
    round 7 new 8   total known 163
    round 8 new 0   total known 163

Fog of war is therefore cosmetic against any scripted player. Confidence this
is unintended: very high — `why` and `path` are explicitly gated and `start`
was simply missed.

Smaller version of the same leak: `state.how_to_grow_staff` names
`school_founded`, `academy_network`, `freedman_staff` and `workshop_first` and
tells you to build them, but

    {"cmd":"why","id":"school_founded"}
      -> {"ok": false, "error": "you have never heard of that. ..."}

while

    {"cmd":"start","id":"school_founded"}
      -> {"ok": false, "error": "missing prerequisites: arithmetic_positional,
          collegium_licensed, freedman_staff"}
    {"cmd":"start","id":"workshop_first"}
      -> {"ok": false, "error": "missing prerequisites: patron_local"}

The game advises you to build four things and then denies you have ever heard
of them.

## FINDING 5 — the founder is immortal; mortality is switched off for every civilisation (HIGH confidence it is at least a disabled mechanic)

`state` reports `"founder_ages": false` and `"founder_alive": true`. I ran a
fresh Norse session that issued nothing but `step`:

    {"cmd":"step","years":100} x4, then {"cmd":"step","years":99}, then {"cmd":"step","years":1}

    year=1000 ... alive=True
    year=1100 ... alive=True
    year=1200 ... alive=True
    year=1300 ... alive=True
    year=1399 ... alive=True
    year=1400 ended=True reason="the horizon at 1400 AD is reached. You built 0
      things of your own. ..." alive=True

The same person practises cataract surgery from 900 to 1400. `founder_ages` is
`false` for **every** civilisation (checked `rome_100ad`, `han_china_100ad`,
`england_1300`, `mexica_1500`, `norse_900ad`), so this is not a Norse setting.
A save the program wrote for me shows the underlying field:

    life_left = 999999940.0   (after 60 simulated years; i.e. it starts at 1e9)

So the mortality machinery exists — `founder_alive`, `dead_reason`, `life_left`,
and an end_reason for dying are all present — and is being fed a sentinel that
disables it. For a game whose entire premise is "you are ONE person carrying
modern knowledge", a 500-year lifespan removes the single largest constraint.

Note in passing: doing absolutely nothing for 500 years is survivable and
mildly profitable. Capital 400 -> 620.8, never in danger.

## FINDING 6 — you can be paid to work as an engineer, chemist, electrician, machinist or optician in the year 900 (HIGH confidence)

`labour` is unambiguous that these trades do not exist:

    "engineer":    {"exists_here": false, "hours_the_market_can_supply": 0.0,
                    "note": "DOES NOT EXIST as a paid civilian profession..."}
    "electrician": {"exists_here": false, "note": "DOES NOT EXIST. Cannot exist until Module 50 does."}

and the engine enforces that for hiring and commissioning:

    {"cmd":"hire","trade":"engineer","n":5}
      -> {"ok": false, "error": "there are no engineers to hire in this society at any
          price: DOES NOT EXIST as a paid civilian profession... Teach one: train"}
    {"cmd":"commission","trade":"millwright","hours":100000}
      -> {"ok": false, "error": "the millwrights here can spare 575 more hours this year, not 100000"}
    {"cmd":"hire","trade":"millwright","n":100}
      -> {"ok": false, "error": "you can supervise, house and teach 6.0 more people, not 100."}

But `work` does not check `exists_here` at all, and lists these trades as jobs
you may take. From a fresh year-900 Norse session:

    {"cmd":"work","trade":"engineer","hours":100}    -> {"ok": true, "earned": 71.8}
    {"cmd":"work","trade":"electrician","hours":100} -> {"ok": true, "earned": 57.4}
    {"cmd":"work","trade":"machinist","hours":100}   -> {"ok": true, "earned": 64.6}
    {"cmd":"work","trade":"chemist","hours":100}     -> {"ok": true, "earned": 57.4}
    {"cmd":"work","trade":"optician","hours":100}    -> {"ok": true, "earned": 50.2}
    {"cmd":"work","trade":"notatrade","hours":100}   -> {"ok": false, "error": "no such trade.
        you could work as: artisan, carpenter, chemist, electrician, engineer, engraver, ..."}

`engineer` is the **best-paid job in the game** (0.718 denarii/hour against the
scholar's 0.574 and the labourer's 0.108), so the money-optimal opening for a
Viking is to take up a profession that will not exist for eight hundred years.
Working full time as an engineer:

    {"cmd":"work","trade":"engineer","hours":2400} -> {"ok": true, "earned": 1720.9}

against a living cost of ~250/yr at the start.

The founder is paid a uniform 1.71x the listed market wage for every trade
(0.718/0.42, 0.574/0.336, 0.108/0.063 all = 1.71). That is not explained
anywhere, but it is at least consistent.

## FINDING 7 — `bribe` is not blocked after the run has ended, and takes money for nothing when there is no scandal (MEDIUM-HIGH confidence)

After the horizon at 1400, every other mutating command is refused:

    {"cmd":"step","years":5}   -> {"ok": false, "error": "the run has ended (...); time cannot advance."}
    {"cmd":"start","id":...}   -> {"ok": false, "error": "... nothing more can be started"}
    {"cmd":"buy",...}          -> {"ok": false, "error": "... nothing more can be bought"}
    {"cmd":"hire",...}         -> {"ok": false, "error": "the run has ended (...)"}
    {"cmd":"work",...}         -> {"ok": false, "error": "the run has ended (...)"}
    {"cmd":"commission",...}   -> {"ok": false, "error": "the run has ended (...)"}
    {"cmd":"train",...}        -> {"ok": false, "error": "the run has ended (...)"}
    {"cmd":"bounty",...}       -> {"ok": false, "error": "... nothing more can be bought"}

but:

    {"cmd":"bribe","amount":10}
      -> {"ok": true, "bribed": "scandal 0.00 -> 0.00 for 10 denarii", "capital": 610.8}

Capital went 620.8 -> 610.8 in a finished game. Two things wrong at once: the
end-of-run guard is missing on `bribe`, and `bribe` cheerfully charges you for
reducing a scandal of 0.00 to 0.00 rather than telling you there is nothing to
bribe away.

## More things I attacked and could NOT break

* Market-supply and supervision caps on `hire` and `commission` (above) are
  enforced and give good errors.
* `work` correctly refuses to spend founder hours you do not have:
  `{"cmd":"work","trade":"scholar","hours":1}` after spending all 2400 ->
  `"you have 0 of your own hours left this year, not 1"`.
* `save` to a bad path: `{"cmd":"save","file":"/nonexistent_dir_xyz/foo.json"}`
  -> `"could not save ...: [Errno 2] No such file or directory"`. No crash.
* `load` of a non-save file: `{"cmd":"load","file":"/etc/hostname"}` ->
  `"could not load '/etc/hostname': Expecting value: line 1 column 1 (char 0)"`.
* The horizon/end-of-run state is otherwise consistent; `state` still answers.
* The `work` money printer is NOT unbounded: working 2400 engineer-hours every
  year from 900, capital rises to ~40,000 by year 930 and then plateaus, because
  `living_cost` scales with wealth (230 -> ~800) and random fires/banditry take
  chunks out. That looked like a runaway and is not one. Good.
* Revenue does not compound: it rises 232.7 -> 238.0 in the first year and then
  stays at 238.0 for five centuries. No exponential-growth exploit there.

---

## FINDING 8 — founder hours are double-spent: you can sell all 2400 hours for wages AND put the same hours into your projects (HIGH confidence)

Fresh Norse session, three commands:

    {"cmd":"start","id":"fin_inn"}
      -> {"ok": true, "started": "fin_inn", "founder_hours_needed": 100.0, ...}
    {"cmd":"work","trade":"engineer","hours":2400}
      -> {"ok": true, "earned": 1722.0, "capital": 2122.0, "your_hours_left_this_year": 0.0}
    {"cmd":"state"}
      -> active: {"fin_inn": {"founder_hours_left": 100.0, "founder_hours_total": 100.0,
                              "years_in_progress": 0.0, "waiting_on": "your hours"}}
    {"cmd":"step","years":1}
    {"cmd":"state"}
      -> active: {"fin_inn": {"founder_hours_left": 50.0, ..., "years_in_progress": 1.0,
                              "spent": 3235.9, "waiting_on": "your hours"}}

I had **zero** hours left for the year — `work` said so itself — and the project
still consumed 50 of them. Repeat the pair and it takes another 33.3. The
founder's year is worth 2400 hours of wages *plus* 2400 hours of research.

Related reporting inconsistency: `state.founder_hours_available` reads 2400.0
even immediately after `work` has reported `"your_hours_left_this_year": 0.0`.
The two commands disagree about the same number.

## FINDING 9 — a project's remaining founder hours go negative (HIGH confidence)

Fresh Norse session, two commands:

    {"cmd":"start","id":"fin_ferry"}
      -> {"ok": true, "started": "fin_ferry", "founder_hours_needed": 100.0,
          "calendar_floor_years": 1.0}
    {"cmd":"step","years":3}
    {"cmd":"state"}
      -> active: {"fin_ferry": {"founder_hours_left": -50.0, "founder_hours_total": 100.0,
                                "years_in_progress": 3.0, "spent": 1557.6,
                                "still_to_pay": 4689.1, "waiting_on": "money"}}

150 hours put into a 100-hour job, and the counter keeps going. In my main
playthrough the same thing on `workshop_first` reached

    {"workshop_first": {"founder_hours_left": -1250.0, "founder_hours_total": 500.0,
                        "years_in_progress": 7.0, "spent": 7008.9,
                        "still_to_pay": 1856.8, "waiting_on": "money"}}

i.e. 1750 hours burned on a 500-hour task while the project was stalled waiting
for cash. Whatever the intended model, "hours left" should not pass zero.

## FINDING 10 — staff disappeared during a multi-year `step` with an empty `events` list (MEDIUM-LOW confidence)

In the main run, at year 909 with capital 1152.6:

    {"cmd":"hire","trade":"smith","n":2}      -> {"ok": true, "you_now_employ": 2.0, "annual_wage_bill": 472.5}
    {"cmd":"hire","trade":"carpenter","n":2}  -> {"ok": true, "you_now_employ": 2.0, "annual_wage_bill": 892.5}
    {"cmd":"start","id":"workshop_first"}
    {"cmd":"work","trade":"engineer","hours":1800}
    {"cmd":"step","years":2}
      -> {"ok": true, "completed": [], "events": [], "year": 911, "capital": -5845.3, ...}
    {"cmd":"state"}
      -> "employees": {}, "annual_wage_bill": 0.0

All four employees were gone and 892 denarii of wages were spent, with `events`
empty. The engine clearly knew: two steps later it announced *"IN ARREARS for 3
years: staff are leaving because you cannot pay them"*, which dates the arrears
to year 910, inside that silent step.

I could not reproduce it in isolation — the equivalent situation in a fresh
session did report `"you cannot pay everyone, so some of them go"`. So either
there is a path that sheds staff without an event, or events raised inside a
multi-year step can be dropped. Flagging it as observed-but-unreduced.

Wording nit: the message is *"some of them go"* but every employee went.

## FINDING 11 — you can start a project that costs 8,866 denarii holding 1,612, with no warning, and `start` never tells you the price

    {"cmd":"start","id":"workshop_first"}
      -> {"ok": true, "started": "workshop_first", "name": "First workshop and laboratory",
          "founder_hours_needed": 500.0, "calendar_floor_years": 1.0}

That is the whole reply. `why workshop_first` says `"total": 8865.8` and
`"upkeep": 900.0` a year. I had 1,612. Two years later capital was -5,845 and
the project was stalled at `"still_to_pay": 3233.2`, having burned 5,632
denarii I never had. The engine is willing to lend past the point of ruin
without asking, and `start` reports hours and years but never money. Whether
this is intended ruin-you-if-you-are-careless design or a missing check I
cannot tell from outside — but the asymmetry (it names hours and years, and
hides the cost) reads like an oversight.

## Debt spiral: attacked, did NOT break

I drove a copy of the main save into permanent insolvency and ran it 200 years.
It is stable, not runaway: at credit exhaustion projects halt, then

    'BONDAGE: you cannot pay, and you enter service for your debt. For about 10
     years most of your hours belong to ...'
    'your term is served and the debt is discharged; you are your own man again'

and the cycle repeats roughly every 10-12 years indefinitely. Capital oscillates
between about -4,000 and -6,500 from year 918 to year 1128 and the run never
ends. So there is no numeric explosion — but also no terminal consequence:
you can be a debt-bonded serf for five centuries, still own an inn, and still
be alive at the horizon.

---

## FINDING 12 — `train` bypasses the supervision cap that `hire` enforces (HIGH confidence)

`hire` is capped by how many people you can look after:

    {"cmd":"hire","trade":"smith","n":1}
      -> {"ok": false, "error": "you can supervise, house and teach 0.0 more people, not 1. ..."}

Issued in the same breath, on the same save:

    {"cmd":"train","trade":"smith","n":5}
      -> {"ok": true, "training": "5 smiths will be ready in 2 years", "capital": 11191.0,
          "your_hours_left_this_year": 150.0}
    {"cmd":"step","years":3}
      -> events: ["5 smiths finish their training"]
    {"cmd":"labour"}
      -> you_employ_in_total 17.16   (was 13.53)

`train` is limited only by founder hours (450 per trainee: *"teaching 50 smiths
takes 22500 of your own hours and you have 2400 uncommitted this year"*). It
never consults the supervision/housing ceiling, so the ceiling is advisory —
5 people a year, forever, for free.

## FINDING 13 — `train` inflates the whole society's labour market, permanently and without limit (HIGH confidence)

`commission` is capped by *"the millwrights here can spare 575 more hours this
year"*. That ceiling can be pumped by training people. Watch the smith supply:

    baseline                      hours_the_market_can_supply = 6469
    train 2 smiths,  step 3       -> 10469
    train 5 smiths,  step 3       -> 20063
    train 5 smiths,  step 3       -> 28685
    train 5 smiths,  step 3       -> 36433

Each trainee adds roughly 2,000-4,000 hours a year to what *the market* can
supply — not to what that person can work (a full-time craftsman is 1,667
hours). Since `train` costs only founder hours and ignores the supervision cap
(Finding 12), the market ceiling on hired labour can be raised without bound.
That ceiling is the main brake on building fast, so this is the most
load-bearing exploit I found.

## FINDING 14 — you can train electricians, opticians, chemists and machinists in the Viking age (HIGH confidence, same family as Finding 6)

    {"cmd":"train","trade":"electrician","n":2}
      -> {"ok": true, "training": "2 electricians will be ready in 2 years",
          "capital": 37584.6, "your_hours_left_this_year": 1500.0}
    {"cmd":"step","years":3}
      -> events: ["2 electricians finish their training", ...]
    {"cmd":"labour"}
      -> "electrician": {"you_employ": 2.0, "exists_here": true,
                         "hours_the_market_can_supply": 6000.0}
    {"cmd":"state"}
      -> "trades_you_created": ["electrician", "optician", "smith"]

`labour` says of that trade: *"DOES NOT EXIST. Cannot exist until Module 50
does."* Nothing in `train` checks that precondition. Two electricians are
walking around Scandinavia in 963 and the market can now supply 6,000
electrician-hours a year.

`train` also accepts trades that already exist here (`train smith` when
`"exists_here": true`), although its own help says it is for teaching "a trade
that does not exist here into existence". That is how Finding 13 works.

Cosmetic: `"1 optician finish their training"` — should be "finishes".

## FINDING 15 — `bounty` is advertised for "tier <=2 crafts" but 80 of the 86 startable nodes refuse it

I posted a bounty on every one of the 86 nodes in `available` on the same save.
Six were eligible (`pwr_oil_shale`, `pwr_peat`, `pwr_petroleum_seeps`,
`pwr_coal_seam`, `fud_hay_making_storage`, `fud_chinampa`). The other 80 all
came back with variants of

    {"cmd":"bounty","id":"hom_safety_pin"}
      -> {"ok": false, "error": "not bounty-eligible (tier 1, category personal):
          a Roman artisan could not recognise success at this"}
    {"cmd":"bounty","id":"sea_skeleton_first"}
      -> {"ok": false, "error": "not bounty-eligible (tier 1, category ships):
          a Roman artisan could not recognise success at this"}

Two problems. First, the refusal reason is about *tier and category*, not tier
alone, so "tier <=2 crafts only" in the docstring is wrong — a tier-1 craft
like a safety pin is refused. Second, the refusal talks about **a Roman
artisan** in a game about Norse Scandinavia, and refuses `sea_skeleton_first`
— shipbuilding, the one thing this civilisation is explicitly best at
(`ships x0.60`) — on the grounds that nobody local could tell whether it
worked.

Bounty pricing itself is consistent: the posted price is exactly 2.5x the build
cost in all six cases (119.7->299.2, 170.1->425.2, 329.0->822.5, 2520->6300,
302.4->756.0, 808.9->2022.3), and a bounty removes 65% of the founder hours,
not all of them, so `"waiting_on": "your hours"` still applies. That is
reasonable; it is just not what "pay someone else to solve it instead of
building it" suggests.

## FINDING 16 — `buy mine` will spend 100% of your capital on one command, with no price shown first and no way to ask

    (save with capital 38,151.6)
    {"cmd":"buy","what":"mine","material":"gold","n":1}
      -> {"ok": true, "material": "gold", "you_asked_for_t_per_yr": 1.0,
          "commissioned_t_per_yr": 0.17, "ready_year": 963.0,
          "years_until_producing": 3.0, "capital": 0.0,
          "note": "less than you asked for: limited by capital, by the ceiling your
                   standing supports, or both. Nothing was wasted, you paid only for
                   what was sunk."}

One tonne of gold a year is the example unit the help text itself uses
(`{"cmd":"buy","what":"mine","material":"coal","n":500}`), so asking for 1 is
not an obviously reckless number. Capital went 38,151.6 -> 0.0 in one command
and five years later the workings had been mothballed for non-payment and I was
in debt bondage. There is no dry-run, no price in the reply before it commits,
and nothing in `why`/`state` that quotes a per-tonne sinking cost.

Smaller: a small gold mine reports zero capacity while still charging upkeep —

    {"cmd":"buy","what":"mine","material":"gold","n":0.01}   (cost 2,240)
    {"cmd":"step","years":4}
    {"cmd":"state"}
      -> "mine_capacity": {"gold": 0.0}, "mine_operating_cost": 588.0

— which looks like display rounding, but reads as "you are paying 588 a year
for a mine that produces nothing".

## Also could NOT break

* `mothball` refuses to shut down anything structural:
  `{"cmd":"mothball","id":"identity_cover"}` -> *"that is load-bearing for what
  you are trying to reach, or it is who you are here; shutting it down would
  softlock the run"*. `{"cmd":"restore","id":"patron_local"}` on something not
  mothballed -> *"you have not shut that down"*. No mothball/restore arbitrage.
* `{"cmd":"mothball","id":"med_cataract_couching"}` (a society-granted tech) ->
  *"that is something the society has, not something you maintain"*. Good.
* `{"cmd":"buy","what":"mine","material":"cheese","n":10}` -> *"material must be
  one of: coal, iron, copper, lead, tin, silver, gold"*.
* `{"cmd":"train","trade":"notatrade","n":1}` -> *"no such trade: notatrade"*.
* Buying with no money is refused with the numbers spelled out:
  *"cannot afford 5 slaves: 2792 denarii (558 each after the market moves against
  a purchase this size) and you have 0"*.

## Oddity: `years_in_progress` stops counting

`pwr_oil_shale` (bountied, calendar floor 0.5 years) sat at
`"years_in_progress": 0.0` for five consecutive calendar years (960 -> 965)
while its `founder_hours_left` fell from 80 to 32, and then completed. Either
the counter only advances on years where the project gets a full share of
attention, or it is simply not being incremented. Confusing to read either way.

---

## FINDING 8b — the double-spend at full strength

Same save, one year, both things at once:

    12 x {"cmd":"start","id": ...}          (2,200 founder hours of work queued)
    {"cmd":"work","trade":"engineer","hours":2400}
      -> {"ok": true, "earned": 1690.3, "your_hours_left_this_year": 0.0}
    {"cmd":"step","years":1}
      -> completed 8 projects: sea_sternpost_rudder, hom_fireplace_chimney,
         fud_hay_making_storage, arrival_orientation, pwr_peat,
         hom_sprung_mattress, hom_mangle_wringer, pwr_coal_seam

2,044 founder hours went into projects in a year where all 2,400 had already
been sold for wages. (Projects do share the pool correctly *with each other* —
12 concurrent projects consumed 2,044 of 2,400, not 2,200 each. It is only
`work` that is outside the accounting.)

## FINDING 17 — `auto_shed` destroys your most profitable works and keeps the ones that only cost money (MEDIUM-HIGH confidence)

In the main run, at year 916 (capital -5,525, upkeep 1,460 from `workshop_first`
900 + `identity_cover` 200 + others, revenue 541):

    {"cmd":"start","id":"hom_toys_dolls"}      ... and hom_button, tex_mordanting,
      tex_indigo, tex_horizontal_loom, tex_field_bleaching, ag2_hopping,
      hom_safety_pin, tex_hand_ginning, med_bone_setting, med_obstetric_practice,
      hom_umbrella
    {"cmd":"work","trade":"engineer","hours":2400}
    {"cmd":"step","years":2}
      -> completed 13 works, then:
         "ABANDONED 9 works you could no longer maintain; they have fallen into ..."

The nine destroyed were `hom_safety_pin`, `hom_toys_dolls`, `tex_hand_ginning`,
`ag2_hopping`, `tex_mordanting`, `hom_umbrella`, `tex_horizontal_loom`,
`tex_indigo`, `hom_button`. From `why`, their listed figures:

    combined revenue  1,248.1 / yr
    combined upkeep     111.5 / yr

They were destroyed in the same year they were finished, before earning a
denarius, and I had just paid ~1,780 to build them. What survived was
`workshop_first` (upkeep 900/yr, revenue 0) and `identity_cover` (upkeep
200/yr, revenue 0) — the two things with the worst ratio in my whole estate.

The policy's own description is `auto_shed: "let go of works that cost more
than they return"`. It did the opposite. My guess at the mechanism is that the
pure-cost works are flagged load-bearing and therefore exempt (a manual
`{"cmd":"mothball","id":"identity_cover"}` is refused with *"that is
load-bearing ... shutting it down would softlock the run"*), so the shedder
takes whatever it is allowed to take — which is exactly the profitable estate.

Second problem: this is not a mothball. Afterwards

    {"cmd":"state"}    -> "mothballed": []
    {"cmd":"why","id":"tex_indigo"}  -> "done": false, "active": false, "can_start_now": true
    {"cmd":"restore","id":"tex_indigo"} -> {"ok": false, "error": "you have not shut that down"}

The works are gone from `done` and must be paid for again in full. Nothing
warned me this could happen, and `auto_shed` is on by default.

Confidence: high that the behaviour is as described; medium that it is
unintended rather than harsh-by-design. What tips me toward "bug" is that the
policy text says the opposite of what happened.

## Could NOT break: the revenue economy

The obvious dominant strategy — spam the cheap revenue nodes — works, but is
bounded, which surprised me in a good way. From a fresh session:

    {"cmd":"start","id":"hom_toys_dolls"}   (cost 105.6, listed revenue 150/yr, upkeep 2)
    {"cmd":"start","id":"hom_button"}       (cost  44.2, listed revenue  50/yr, upkeep 1)
    {"cmd":"start","id":"tex_horizontal_loom"} (cost 323.4, revenue 400/yr, upkeep 30)
    {"cmd":"start","id":"tex_indigo"}       (cost 269.0, revenue 300/yr, upkeep 40)
    {"cmd":"step","years":1}   -> all four complete, revenue 232.7 -> 841.2

742 denarii bought 600/yr of net income: a payback under 15 months. Per-work
revenue then ramps for about three years (loom 272.6 -> 417.9) and **stops** at
about 1.045x the listed figure. Stepping to year 1074 leaves revenue frozen at
1,163.3 while `living_cost` keeps climbing with wealth (499 -> 805). So there
is no compounding runaway; capital grows linearly, roughly 35,000 over 170
years. I expected an exponential and did not find one.

---

## FINDING 18 — THE BIG ONE: a deficit is an unrecoverable softlock, and the policy switches that are supposed to govern it do nothing

This is the one I would fix first. Once annual net income is negative, **every
work you complete is destroyed at the end of the following year**, regardless of
how profitable it is, and there is no legal way to reduce the upkeep that caused
the deficit.

State of my main run at year 923: capital -8,840.5, revenue 674.5, upkeep
1,430.0, net -1,006.0, credit limit 29,762.9 (so ~21,000 of headroom),
reputation 70.1.

First, I turned off the two switches that are documented to govern this:

    {"cmd":"policy","set":{"auto_shed":false,"auto_mothball":false}}
      -> {"ok": true, "changed": {"auto_shed": false, "auto_mothball": false},
          "policy": {... "auto_mothball": false, "auto_shed": false ...}}

Then built eighteen revenue works and worked a full year:

    18 x {"cmd":"start","id": ...}
      (four largest refused: "you have been in arrears 13 years and are 8840
       denarii down; nobody will fund a new undertaking of this size")
    {"cmd":"work","trade":"engineer","hours":2400}
    {"cmd":"step","years":1}
      -> completed 11: tex_mordanting, ag2_potash, ag2_hopping, tex_hand_ginning,
         opt_anemometer, mat_obsidian_blade, hom_button, ag2_oil_pressing,
         tex_indigo, tex_horizontal_loom, hom_toys_dolls
      -> revenue 674.5 -> 1803.2, upkeep 1633.0, net -148.0
    {"cmd":"step","years":1}
      -> events: ["ABANDONED 11 works you could no longer maintain; they have
                  fallen into disrepair", "fire in the longhouses by the shore"]
      -> revenue back to 1316.2, net -537.8, active 0

The eleven works destroyed are exactly the eleven built the year before. The
deficit at the moment of destruction was **-148 denarii a year** — 8% of one
year's revenue — and it cost me everything I had built. Repeat the cycle and
the same thing happens again; I ran it three times (years 916, 921, 925) with
identical results, 9 then 12 then 11 works burned.

Three separate things are wrong here:

1. **The policy switches are ignored.** `help` says of the automatic
   behaviours: *"Every one of them is a switch you control, and every one can be
   done by hand instead."* `auto_shed` (*"let go of works that cost more than
   they return"*) and `auto_mothball` were both `false` and the abandonment
   happened anyway.

2. **It destroys the profitable works and keeps the unprofitable ones.** The
   eleven destroyed had a combined listed revenue of ~2,700/yr against ~330/yr
   of upkeep. What survived every purge was `workshop_first` (upkeep 900/yr,
   revenue 0) and `identity_cover` (upkeep 200/yr, revenue 0) — the actual cause
   of the deficit.

3. **There is no way out.** The two upkeep sinks cannot be shut down:

       {"cmd":"mothball","id":"workshop_first"}
         -> {"ok": false, "error": "that is load-bearing for what you are trying to
             reach, or it is who you are here; shutting it down would softlock the run"}
       {"cmd":"mothball","id":"identity_cover"}   -> same
       {"cmd":"mothball","id":"units_standards"}  -> same

   and destroyed works are not mothballed, so they cannot be brought back
   cheaply:

       {"cmd":"state"}   -> "mothballed": []
       {"cmd":"restore","id":"tex_indigo"} -> {"ok": false, "error": "you have not shut that down"}
       {"cmd":"why","id":"tex_indigo"}     -> "done": false, "can_start_now": true

   You may rebuild them, at full price, to have them destroyed again next year.
   Meanwhile the largest revenue works — the only ones big enough to close the
   gap in one jump — are refused because you are in arrears. The run is dead
   but never ends: `founder_alive` stays true and the horizon is 475 years away.

The message on the refusal is the punchline: shutting down the thing bleeding
me dry *"would softlock the run"*. Refusing it is what softlocked the run.

Confidence: very high on the behaviour (reproduced three times, plus the policy
switches verified off in the same session). Very high that at least point 1 is a
bug. Point 2 contradicts the policy's own description.

## FINDING 19 — `policy` treats any non-empty string as `true`, including "false" and "off"

    {"cmd":"policy","set":{"auto_hire":"false"}}
      -> {"ok": true, "changed": {"auto_hire": true}}
    {"cmd":"policy","set":{"auto_bribe":"off"}}
      -> {"ok": true, "changed": {"auto_bribe": true}}
    {"cmd":"policy","set":{"auto_hire":"yes please"}}
      -> {"ok": true, "changed": {"auto_hire": true}}
    {"cmd":"policy","set":{"auto_bribe":7}}
      -> {"ok": true, "changed": {"auto_bribe": true}}

Unknown keys are rejected properly (`"no such policy: nonexistent_switch. They
are: ..."`), so the validation is half-present. Asking to turn a switch *off*
and being told `"changed": {"auto_hire": true}` is a nasty little trap.

## FINDING 20 — `start` said "already done" about works that were producing nothing and that `why` later called not-done (MEDIUM-LOW confidence, not fully reduced)

At year 918, immediately after the first "ABANDONED 9 works" event:

    {"cmd":"start","id":"hom_toys_dolls"}     -> {"ok": false, "error": "already done"}
    {"cmd":"start","id":"hom_button"}         -> {"ok": false, "error": "already done"}
    {"cmd":"start","id":"tex_horizontal_loom"} -> {"ok": false, "error": "already done"}

but `state.where_the_money_comes_from` at that moment listed only
`arithmetic_positional`, `tex_field_bleaching`, `med_cataract_couching`,
`med_trepanation`, `med_obstetric_practice`, `med_bone_setting`, and those six
summed to the reported `revenue` — so the three "already done" works were
contributing exactly zero. Three years later `why hom_toys_dolls` reported
`"done": false, "can_start_now": true`.

So there appears to be an intermediate state — done enough to refuse a restart,
ruined enough to earn nothing — which nothing in `state` exposes. I could not
build a minimal repro for this one; it needs the deficit conditions of Finding
18 to arise.

---

## FINDING 21 — buy slaves, free them immediately, and you have permanent labour with a zero wage bill and a reputation bonus (MEDIUM confidence it is unbalanced rather than intended)

    (save with capital 11,647)
    {"cmd":"buy","what":"slaves","n":5}
      -> {"ok": true, "bought": 5, "slaves": 5, "capital": 8854.6}      (2,792 for five)
    {"cmd":"buy","what":"manumit","n":10}
      -> {"ok": true, "manumitted": 5, "freedmen": 5, "slaves": 0}      (clamps to what you hold)
    {"cmd":"step","years":1}
    {"cmd":"state"}
      -> "slaves": 0, "freedmen": 5, "artisans": 5.0,
         "employees": {}, "annual_wage_bill": 0.0, reputation 1.0 -> 2.6

Five permanent craftsmen for a one-off 2,792, with **no annual wage at all**,
against 210/yr each for hiring the same people (payback under three years, then
free forever) — and manumission also pays a reputation dividend. Freeing people
is the strictly dominant labour strategy in every dimension, which is a strange
place for the model to land given the docstring's care about not lying about the
cost of production. Freedmen do at least count against the supervision ceiling
(after 15 of them, `hire` reports *"you can supervise, house and teach 0.0 more
people"*), so it is bounded — just free.

## FINDING 22 — `load` validates nothing

    (hand-edited a save the program itself wrote: capital -> 1e12, year -> 500)
    {"cmd":"load","file":".../doctored.json"}
      -> {"ok": true, "loaded": ".../doctored.json", "year": 500}
    {"cmd":"state"}
      -> {"ok": true, "year": 500, "capital": 1000000000000.0,
          "living_cost": 15000000224.3, "net_per_year": -14999999986.3}
    {"cmd":"step","years":1}   -> {"ok": true, ... "year": 501 ...}

The Norse game begins in 900; it happily ran in the year 500. With
`capital: "lots"` the load also succeeds and the failure surfaces later, though
politely:

    {"cmd":"state"} -> {"ok": false, "error": "internal error handling that command:
      TypeError: type str doesn't define __round__ method. The game is intact; try something else."}

A save file is the player's own, so this is cheating-your-own-game rather than a
security hole. Worth a schema check anyway, if only so a corrupted session file
fails at load with a sentence instead of somewhere later with a TypeError.

Side observation from this: `living_cost` is about **1.5% of capital** per year
(1e12 -> 1.5e10). That is the mechanism that caps the `work` money printer.

## Final round of robustness attacks — could NOT break

    {"cmd":"start","id":"AAAA...(200,000 chars)"}  -> "unknown node id 'AAAA...'"   (no crash;
        it does echo the whole 200 KB id back, so a big input yields a big output line)
    {"cmd":"why","id":"../../etc/passwd"}          -> "unknown node '../../etc/passwd'. did you mean: no idea"
    {"cmd":"work","trade":"scholar","hours":1e308} -> "you have 2400 of your own hours left this year, not 1000...336"
    {"cmd":"buy","what":"forest","n":1e308}        -> "cannot afford 1000...0 ha of coppice woodland"
    {"cmd":"step","years":1e18}                    -> runs to the horizon and stops cleanly
    {"cmd":"hire","trade":"labourer","n":1e308}    -> refused (run had ended)
    {"cmd":"state","extra":[[[[... 500 deep ...]]]]} -> answered normally
    {"cmd":["state"]}                              -> "unknown cmd ['state']. use one of: ..."

Nothing wrote to stderr, nothing threw a stack trace out of the process, and the
session file survived every one of these.

`stop` is honest and there is no progress-farming exploit:

    {"cmd":"start","id":"sea_skeleton_first"}  {"cmd":"step","years":1}
      -> active: {"founder_hours_left": 100.0 of 250.0, "spent": 1893.6, "still_to_pay": 0.0}
    {"cmd":"stop","id":"sea_skeleton_first"}   -> {"ok": true, "stopped": ...}
    {"cmd":"start","id":"sea_skeleton_first"}
      -> active: {"founder_hours_left": 250.0, "spent": 0.0, "still_to_pay": 1893.6}
    {"cmd":"stop",...} twice                   -> second one: {"ok": false, "error": "not active"}

The 1,893.6 already spent is gone and the hours reset. Exactly as advertised.

I also never managed to raise `suspicion` or `scandal` above 0.00 in ~45 years
of Norse play across all my saves, so the whole scandal/bribe/protection
subsystem went untested. That may just be correct for a civilisation whose
profile reads *"fears heterodoxy 0.10, eminence is dangerous 0.20"* —
"nobody will stop you" is the stated premise — but it does mean `bribe` and
`auto_bribe` are dead controls in this scenario, and `bribe` is the one command
that will silently take your money for nothing (Finding 7).

## Where the main session ended up

    year 945, capital -15,488.8, revenue 660.1, upkeep 1,430.0, net -1,019.5/yr,
    done_count 152 (135 granted, 17 earned), reputation 53.4, ended: false

Locked in the Finding 18 spiral: everything I build is destroyed the following
year, the 1,430/yr of upkeep cannot be shut off, and the run has 455 years left
to go with no possible outcome. Peak was 13 completed works in a single year.

---

# Summary

## Ranked by how much I think they matter

1. **Finding 18** — negative net income is an unrecoverable softlock; new works
   are destroyed the following year; `auto_shed`/`auto_mothball` set to `false`
   do not stop it; the upkeep causing it cannot be mothballed.
2. **Finding 1** — `NaN`/`Infinity` in any numeric argument permanently poisons
   `capital`, makes everything free, and writes invalid JSON to the save.
   `hire` also accepts a string for `n`.
3. **Finding 8 / 8b** — founder hours are double-spent: `work` and projects draw
   on the same 2,400 hours without either knowing about the other.
4. **Finding 4** — `start` leaks prerequisites for undiscovered nodes, which
   defeats fog of war entirely (163 nodes crawled from one seed).
5. **Finding 13 + 12** — `train` raises the society's labour-market ceiling
   without limit and ignores the supervision cap that `hire` enforces.
6. **Finding 5** — the founder never ages or dies, in any civilisation.
7. **Finding 6 / 14** — you can work as, and train, engineers / electricians /
   opticians / chemists / machinists in the year 900.
8. **Finding 2** — the `why` cost breakdown is short by a constant factor of 1.4.
9. **Finding 9** — a project's remaining founder hours go negative.
10. Findings 7, 16, 19, 21, 22 — bribe after the horizon and bribe-for-nothing;
    `buy mine` spending 100% of capital in one command; `policy` reading
    `"false"` as true; free labour via manumission; `load` validating nothing.

## What held up under attack

Argument validation (negative, zero, wrong-type, absurd magnitudes), the
unknown-id and unknown-command paths, malformed and deeply nested JSON, 200 KB
inputs, market-supply and supervision caps on `hire`/`commission`, `mothball`
refusing to softlock, `stop` losing sunk cost honestly, save/load I/O error
handling, end-of-run guards on every mutator except `bribe`, the debt/bondage
cycle (bounded, not runaway), and the revenue economy (ramps to ~1.045x listed
and stops; no exponential). No command ever threw a stack trace out of the
process and the session file was never corrupted except by my own `NaN`.

## Things that struck me as unrealistic or confusing

* Rome bleeds through everywhere in a Norse game: `labour` notes about Roman
  plumbarii and masons; the bounty refusal *"a Roman artisan could not recognise
  success at this"*; `identity_cover` = *"Establish the Alexandrian
  physician-philosopher persona"*; `patron_local` = *"Secure a town patron.
  Cheapest entry gift is a pair of reading lenses for an ageing magistrate"*
  (reading lenses are ~1286, and a Viking-age town does not have magistrates).
* Your entire starting income is `med_cataract_couching` and `med_trepanation`.
  The 900 AD Norse start you as an itinerant eye surgeon and skull-driller.
* `mil_plate_armour_firearms` — "Plate armour against firearms", note explains
  what happens by 1700 — is startable in year 900 with no prerequisites at all.
* `fud_chinampa` (Mexica floating-garden agriculture) is startable in
  Scandinavia, and is one of only six bounty-eligible nodes.
* Six Roman civil/financial technologies (`civ_arch_roman`, `fin_annona`,
  `fin_argentarii`, `fin_collegium`, `fin_societas`, `hom_cosmetics_roman`,
  then `civ_aqueduct_roman`, `civ_insula`, `civ_sewer_roman`) cost literally
  nothing and complete instantly, doubling your credit limit on turn one
  (Finding 3).
* `electrician` note: *"Cannot exist until Module 50 does"* — internal authoring
  jargon in player-facing text.
* `state.how_to_grow_staff` tells you to build four nodes that `why` says you
  have never heard of.
* The "unknown cmd" error lists 10 commands; `help` documents 24.
* `mothball` refuses on the grounds that shutting a thing down "would softlock
  the run" while there is no goal set at all (`"goal": null`).
* `years_in_progress` sometimes stops counting: `pwr_oil_shale` sat at 0.0 for
  five calendar years while its hours drained, and `sea_skeleton_first` read 0.0
  after a full year of progress, while `fin_inn` counted 1.0 and 2.0 normally.
* `"1 optician finish their training"`; `"some of them go"` when all of them go;
  `"ABANDONED 1 works"`.
* `done_granted` grows during play (132 -> 135 by year 923) although `help` says
  the society's existing knowledge is credited "in the first year".
* Being permanently insolvent has no terminal consequence: you cycle through
  debt bondage every ten years for five centuries and are still alive at the end.
