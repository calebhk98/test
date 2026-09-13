# Playtest: norse_900ad, fog of war ON

Agent-mode JSON protocol, session file `norse_900ad_PLAY.json`.
Notes written as I go.

## Setup

Started with:

    python3 rome/sim/simulator.py agent --civ norse_900ad --fog \
        --session /home/user/test/rome/playtest/naive2/norse_900ad_PLAY.json

The welcome banner is genuinely good — it tells me the premise in one
paragraph ("You are one person, dropped into a pre-industrial society,
carrying the knowledge of how modern technology works but none of the
industry that makes it"), lists every command, and is explicit that
"Knowing how a thing works is free. Building it is not". Horizon is 1400,
start 900, so 500 years. "There is no score but the state of what you
have built."

Fog of war: "You can see what you have built, what you could begin today
as a one line summary, and things you have heard of but cannot yet
begin. You cannot see where anything leads, and there is no way to view
the whole tree." `path` is disabled under fog.

## Year 900 — the opening

Start position: capital 400, revenue 232.7 ("where_the_money_comes_from":
`med_cataract_couching` 166.7, `med_trepanation` 66.7 — so I am apparently
an eye surgeon), living_cost 230, net **+2.8/yr**. Founder hours 2400/yr.
132 things "granted", 0 "earned". No employees, no slaves.

`founder_ages: false` — I appear to be immortal over a 500-year horizon.
That is a large, unremarked design decision; I expected an heir/succession
problem and there is none.

`available` returned 86 nodes; `heard_of_but_cannot_begin` was **empty**,
even though fog-of-war explicitly promises "things you have heard of but
cannot yet begin". That stayed empty all through the opening.

### The economics are extremely exploitable

I ran `why` on all 86 available nodes and sorted by (revenue - upkeep)/cost:

    hom_toys_dolls        cost 105.6  upkeep 2    revenue 150   -> +140%/yr
    tex_horizontal_loom   cost 323.4  upkeep 30   revenue 400   -> +114%/yr
    hom_button            cost  44.2  upkeep 1    revenue  50   -> +111%/yr
    tex_field_bleaching   cost 342.7  upkeep 30   revenue 400   -> +108%/yr
    tex_indigo            cost 269.0  upkeep 40   revenue 300   -> +97%/yr
    tex_mordanting        cost 185.3  upkeep 15   revenue 150   -> +73%/yr

A horizontal loom that pays for itself three times over every year is not
an economy, it is a money printer. Nothing anywhere told me these were
one-off *inventions* rather than businesses I own, so I read revenue as
"the engine hands you this every year forever" — and that turned out to be
right. **I think this is the single biggest balance problem in the game.**

Six nodes were free outright — cost 0.0, 0 hours, 0 years:
`civ_arch_roman`, `fin_annona`, `fin_argentarii`, `fin_collegium`,
`fin_societas`, `hom_cosmetics_roman`. I took all six. Confusing: if a
900 AD Norse society already has the Roman masonry arch and the *annona*
grain dole for free, why are they nodes I "start" rather than part of the
132 granted? Probably a bug in how the civ's starting endowment is applied.

### What I did

Started all six free nodes plus `med_bone_setting`, `med_obstetric_practice`,
`hom_button`, `hom_toys_dolls`, `tex_horizontal_loom`, `tex_indigo`,
`tex_mordanting`, `hom_umbrella`. Then `step 1`.

**All fourteen completed inside the same year 900**, including ones whose
`calendar_floor_years` was 0.5. So the "least years" floor is a fraction of
a year, not a floor of one turn — several half-year projects run in parallel
inside a single step. I expected a 0.5-year floor to bite when I started
eight things at once with one pair of hands; it did not.

Result after one step:

    year 901, capital -684.7, revenue 992.5, net_per_year 632.0
    reputation 5 -> 28.1, credit_limit 1912.9 -> 10516.2

I went from +2.8/yr to +632/yr in one turn, financed on credit, at no risk.
Notice also the credit limit quintupled because revenue rose, so the more I
borrow-and-build the more I can borrow. There is no brake here.

Small inconsistency: `why tex_horizontal_loom` promised revenue 400.0, but
`where_the_money_comes_from` afterwards lists it at 272.6. Something scales
the quoted number down and nothing says what. Not a bug necessarily, but the
quoted figure is not the figure you get.

## 901-910 — the runaway

I kept doing the obvious thing: `available`, `why` everything, start every
node whose payback beat the ~10% interest rate, `step 1`. The result:

    year 902  revenue  2234  net 1549   done_earned  29
    year 903  revenue  4076  net 2731   done_earned  39
    year 904  revenue  6548  net 4203   done_earned  54
    year 905  revenue  7600  net 3879   done_earned  94
    year 907  revenue  9685  net 5006   done_earned 142
    year 909  revenue 14037  net 8552   done_earned 157
    year 911  revenue 15687  net 8000   done_earned 165

Revenue went up 67x in eleven years, financed entirely on credit I never
had to justify. The credit limit tracks revenue, so borrowing to build
things that raise revenue raises the borrowing limit, which funds more
building. `debt_interest_rate` actually *fell* as I got deeper into debt
(0.1183 -> 0.065) because reputation went up. That is a positive feedback
loop with no counterweight I could find. I never once had to choose between
two things I wanted.

### Things that surprised me

- **Nothing I did not start completed anyway — except when it did.**
  `civ_vault_barrel` and `civ_amphitheatre` both showed up in `completed`
  in year 901 and I never started either. `manual` is true and the docstring
  promises "Nothing becomes active except what start_project() was explicitly
  told to start". Same later with `cap_measure_len` and `civ_sewer_separate`.
  My guess is these are zero-cost nodes that auto-complete once their
  prerequisites are met, which is defensible, but it directly contradicts
  the documented `--manual` guarantee. I'd call it a documentation bug at
  minimum.

- **An event said "IN ARREARS for 3 years: staff are leaving because you
  cannot pay them" while `employees_total` was 0.** I had no staff to lose.
  Two turns later `scholars` and `artisans` silently dropped from 1.0/3.0 to
  0.0/0.0 — so I did have invisible staff that arrived from somewhere (I
  never hired anyone) and then left. `employees_total: 0` and `artisans: 3.0`
  at the same time is not something the interface ever explains.

- **`hom_toothbrush`: cost 42.4, upkeep 40.0, revenue 30.0.** A toothbrush
  that loses you 10 denarii a year, forever. Fine as a trap, but there is
  nothing anywhere that flags upkeep-exceeds-revenue, and `auto_mothball` is
  on by default so the engine may quietly bin it.

- **`fud_chinampa` — chinampa raised-bed agriculture, in Viking-age
  Scandinavia.** It was in my starting `available` list. Chinampas are
  Mesoamerican lake gardens; there is no lake-bed horticulture to be had in
  Norway in 900 AD, and the model happily let me build it for +780/yr. Same
  smell as `ag2_maize_newworld`, `ag2_potato_newworld`, `ag2_coffee_voyage`
  and `ag2_sugar_voyage` appearing as ordinary purchasable nodes centuries
  before contact with the Americas. If the intent is "you know how, so you
  can go get it", nothing says so.

- **The whole thing is written for Rome and only relabelled for the Norse.**
  Constant: `civ_arch_roman`, `fin_annona` (the Roman grain dole), "Rome has
  these in abundance and they are good" (masons), "Rome never develops the
  chimney", "Buttons exist in Rome but are rare". Even a *refusal* is Roman:
  `bounty tx2_wool_fibre` -> "not bounty-eligible (tier 0, category fibres):
  **a Roman artisan** could not recognise success at this". I am playing
  Scandinavia in 900 and the engine keeps telling me about Rome.

### `workshop_first` does not exist and the game keeps recommending it

Every `state` reply carries:

    "artisans": "... build freedman_staff ...; build workshop_first
                 (you need somewhere for them to work)."

and blocked nodes say `"case_hardening": "missing prerequisites:
workshop_first"`. But:

    {"cmd":"why","id":"workshop_first"}
    {"ok": false, "error": "you have never heard of that. You know what you
     have built and what you could begin now; use 'available'."}

Same for `school_founded`, `freedman_staff`, `scientific_method` (before it
unlocked). The engine names a node as the remedy and then denies knowing it.
Under fog that is arguably consistent — but then it should not be naming it
in the advice text. **This is the single most confusing thing in the game so
far**, and I think it is a real bug: the hint generator does not respect fog.

### The hire cap, and an advice string that eats its own tail

At year 910, with revenue 15,687/yr, I tried to build a staff. I got six
smiths and then:

    {"ok": false, "error": "you can supervise, house and teach 0.0 more
     people, not 4. To get more artisans: {\"cmd\":\"hire\",\"trade\":
     \"smith\",\"n\":3} or any trade in {\"cmd\":\"labour\"}; ..."}

The remedy offered for "you cannot hire anybody else" is "hire somebody
else". The cap itself is good design — money alone should not buy you an
organisation — but nothing tells me what raises it, and the one lever it
names (`workshop_first`) is the node the game says I have never heard of.

## 911-966 — the middle game, and where the model stops pushing back

Milestones: `arithmetic_positional` (912, "changes the society:
literacy_elite, state_capacity"), `scientific_method` (914, "changes the
society: w_magic_fear, w_novelty"), `workshop_first` (the node that had not
existed), then `fin_double_entry` (931), `germ_theory` (961),
`cementation_steel` (966). The society-change events are a lovely touch —
they are the only place the world visibly reacts to what I build.

`workshop_first` finally appeared in `available` only *after*
`scientific_method` completed — i.e. exactly the node the engine had been
telling me to build for ten years while denying it existed.

I turned on `auto_hire`, `auto_train`, `auto_mine`, `auto_forest`,
`auto_bribe`. `auto_train` is the best thing in the game: over the next
forty years I got

    "you begin teaching the first engineers this world has ever had"
    "2 engineers finish their training"
    ... then chemists, machinists, opticians, electricians

`trades_you_created: ["chemist","engineer","machinist","optician"]`, later
electricians. Inventing *professions* rather than gadgets is the most
interesting mechanic here and I wish the game made more of it — it happens
entirely in the background once the switch is on.

### The economy stops being a constraint entirely

    year 950  revenue 140,660   net  64,613
    year 960  revenue 198,440   net 107,456
    year 966  revenue 214,294   net 108,625   capital 696,351

By 960 I had more money than I could spend and no decision left to make.
The only real limit is my own 2,400 founder-hours a year, which never grew:
`founder_hours_available` was 2400.0 in year 900 and is 2400.0 in year 966,
with 43 employees, 23 scholars and five invented professions. Nothing I
built — not the workshop, not the doctorate, not the research group, not
`sc2_institution_research_group` — bought me a single hour of anybody's
time that could substitute for mine. That is the deep design problem: the
game is about founding an industrial civilisation and the founder is still
personally doing every hour of the design work in year 966.

### Two things I am fairly confident are bugs

**1. Projects stall "waiting on money" while I am sitting on 696,000 denarii.**

    active: civ_monumental_stone   still_to_pay 2.3     waiting_on "money"
            sc2_algebra_determinant still_to_pay 84.0   waiting_on "money"
            geometry_analytic       still_to_pay 158.2  waiting_on "money"
    state:  capital 696350.6, project_spend_this_year 14529.7

Two denarii and three hundred pounds. Capital *grew* by 94,000 that year
while those projects sat blocked. Whatever caps annual project spend, it is
not looking at capital, and it is not explained anywhere in `state`,
`policy` or `help`. Either the cap should be reported (a `spend_cap` field
next to `resource_throttle`) or this is simply broken.

**2. `founder_hours_left` goes negative and stays negative.**

    fud_chinampa      founder_hours_left -30.0
    geometry_analytic founder_hours_left -776.8
    collegium_licensed founder_hours_left -541.8

A project cannot need minus seven hundred hours. Cosmetic, but it makes the
`active` display useless for planning, which is the one thing it is for.

**3. A refusal that does not say the price.**

    {"cmd":"buy","what":"forest","n":2000}
    {"ok": false, "error": "cannot afford 2000 ha of coppice woodland
     (you have 602900 denarii)"}

It tells me what I have and not what it costs. By bisection coppice is 350
denarii/ha, so 2000 ha is 700,000. Every other refusal in this game is
excellent at saying what is missing; this one is not.

Mines: `buy mine` for coal and iron took 200 t/yr each with a 3-year sink
time (nice). Copper only gave me 87.89 of the 200 I asked for and tin and
lead refused outright: "could not commission any tin capacity right now
(capital too low, ceiling reached, or standing too low for a concession
that size)" — three possible reasons, and it will not tell me which. That
is the same problem: the refusal knows the answer and withholds it.

Note also `auto_mine: true` and `auto_forest: true` were on for twenty-five
years while `throttle_binding` sat on `"charcoal"` and `mine_capacity` was
`{}`. The automation that is meant to fix exactly this never fired. I had
to buy 1,850 ha of coppice by hand.
## 978-1154 — deep tech, and a bomb in the Viking age

Chain landmarks, all from the engine's own event log:

    1082  "Movable type and the screw press changes the society:
           literacy_elite, literacy_general, w_information, w_novelty"
    1085  "Newspaper as business and subscription changes the society"
    1099  "Tolerances, jigs, fixtures and interchangeable manufacture
           changes the society: w_labour_saving"
    1100  "Found the school (the Museum) changes the society:
           adaptation_rate, literacy_elite, w_novelty"
    1109  "Central bank and monetary authority changes the society"
    1142  "Electric telegraph changes the society: state_capacity,
           w_information"

By year 1154 I had 2,268 earned technologies, 2.34 million denarii a year
of revenue, 62 scholars and 180 artisans, and the goal node reported:

    {"cmd":"why","id":"point_contact_transistor"}
    "start_blocked_reason": "missing prerequisites: single_crystal,
                             vacuum_tube"

Five of the transistor's seven direct prerequisites — `galena_detector`,
`gp_whisker_forming`, `micrometer_gauges`, `prc_lapping_plate`,
`quantum_solidstate_theory` — were already done in the twelfth century.

### `mil_atomic_bomb` is buildable in 978 AD for 342 denarii

This is the clearest bug I found.

    {"cmd":"why","id":"mil_atomic_bomb"}
    "tier": 4, "cost": {... "total": 341.6}, "founder_hours": 200.0,
    "direct_prerequisites": ["cap_tol_100um"],
    "missing_prerequisites": [],
    "can_start_now": true,
    "note": "The atomic bomb as a single node with an honest statement:
     requires the isotope separation and reactor programme it needs ..."

The note says out loud that it requires an isotope separation and reactor
programme. The prerequisite list contains one machining-tolerance node and
nothing else. No uranium, no `mat_uranium`, no reactor, no `cap_pure_*`, no
electricity — I had none of those in 978. 342 denarii is about what
`med_surgical_gloves_mask` costs. I declined to build it; the note calls its
use "a mass atrocity" and it `unlocks: []`, so it buys nothing anyway. But
it should not have been startable, and it stayed startable for the next two
centuries.

### Fog of war leaks through the machine-readable field

    "start_blocked_reason": "missing prerequisites: cap_vac_1e6,
      diffusion_pump, discharge_xray, gp_exhaust_pinchoff, gp_getter,
      something you have not heard of",
    "missing_prerequisites": ["cap_vac_1e6", "diffusion_pump",
      "discharge_xray", "gp_exhaust_pinchoff", "gp_getter",
      "in2_electron_source_cathode"]

The prose carefully says "something you have not heard of"; the field right
underneath it names the thing. One of the two is wrong. (I'd fix the list,
not the prose — the prose is the nicer piece of writing.)

### Costs that look like unit errors

Sitting side by side in the same `available` listing:

    md2_surgical_drape       302.3
    md2_surgical_glove   210,298.9
    md2_tourniquet       210,340.9
    tx2_ballpoint_pen  1,232,234.1
    ag2_milking_machine 7,001,168.3
    fin_central_bank   6,289,575.6

A tourniquet is a stick and a strap. A ballpoint pen costing 1.2 million
denarii next to a `md2_catgut_suture` at 305 is not a judgement call, it
looks like a scaling formula running away on some inputs. `railway` at
2,340,928 I can believe; `md2_tourniquet` at 210,340 I cannot.

### Resource shortages finally bite (and this part is good)

Around 1085-1130 the run genuinely got hard for the first time:

    "SHORT OF COAL: work running at 11% of plan"
    "SHORT OF IRON: work running at 21% of plan"
    "MOTHBALLED half the copper workings; you could not pay to keep them
     running"

and `net_per_year` went to **-120,106**. This is the one stretch of the game
where I had to actually manage something: buy coppice by the thousand
hectares, sink 2,000 t/yr iron mines, wait three years for them to come in.
It was the most interesting twenty turns of the run and it is a shame it
arrives 180 years after the outcome is already decided.

The `auto_mine`/`auto_forest` policies still did essentially nothing here —
`throttle_binding` sat on `coal` for years with the switch on. Either those
policies only fire under conditions I could not observe, or they are broken.
## 1154-1262 — the last stretch, and the ending

The endgame was a waiting game rather than a decision game. By 1194 the
whole of `available` was two nodes (`arrival_orientation`, which the game
itself labels "OPTIONAL, and no longer a prerequisite for anything", and
`corpus_written` at 6,000 founder hours). Everything else was `heard_of`
and blocked behind a handful of long projects already running —
`electrolysis_industrial`, `power_grid`. For twelve turns in a row I
started nothing at all and simply pressed `step`.

Then the vacuum-tube era opened all at once: `el2_magnetron_microwave_
oscillator`, `com_radar_magnetron`, `el2_klystron_microwave_amplifier`,
`com_vacuum_tube_computer`, `radio`. The final block was one node:

    "start_blocked_reason": "missing prerequisites: single_crystal"

and behind that, `zone_refining` <- `ge_reduction` <- `gecl4_purification`
<- (`cap_pure_6N`, `fused_quartz`, `germanium_extraction`,
`glass_borosilicate`).

    Y1262  ENDED  goal reached: point_contact_transistor completed in 1262 AD

Final position:

    year 1263          done_count 2818  (2679 earned, 139 granted)
    capital        90,508,614
    revenue         6,650,260 / yr
    employees             463   (110.9 scholars, 352.2 artisans)
    reputation           98.6   eminence 9.16
    forest              3,351 ha
    mines        coal 49,551 t/yr, iron 16,884 t/yr, copper 740 t/yr
    trades invented: chemist, electrician, engineer, machinist, optician

Point-contact transistor in **1262 AD**, 685 years early, 138 years inside
the horizon.

### The ending is the biggest problem in the game

    {"cmd":"step","years":1}
    {"ok": false, "error": "the run has ended (goal reached:
     point_contact_transistor completed in 1262 AD); time cannot advance."}

I was never told there was a goal. The welcome screen says, in as many
words:

    "what you are trying to do": "Advance as far as you can before the
     horizon at 1400. There is no score but the state of what you have
     built."

and every single `state` reply from year 900 to the end reported

    "goal": null, "goal_reached": false

Then the run terminated 138 years early on a win condition that only
`why point_contact_transistor` ever disclosed ("THE GOAL ... Getting here
from 100 AD is the whole game"), and it did so while four things were still
sitting in `available` — `junction_transistor`, `academy_network`,
`mt2_titanium_alloys` — and `silicon_path` was in `heard_of`. I was asked to
see how advanced I could get and the game stopped me from getting more
advanced, without warning, on a criterion it told me did not exist.

Either `state.goal` should say `"point_contact_transistor"` from turn one,
or reaching it should be an announcement and not a termination. As it
stands the two halves of the program disagree about what the game is.

### Correction to something I wrote earlier

I complained above that founder hours never grow. That was true for the
first ~70 years — `founder_hours_available` was 2400.0 in 900 and still
2400.0 in 966 — but by the end it was **13,007.4**. So the mechanic does
exist; it simply gave me no signal that it existed, no indication which
build raised it, and no entry in `state` explaining the number. Compare
`resource_throttle`, which comes with `throttle_binding` telling you exactly
what is limiting you. Founder hours deserve the same treatment.

## What worked well

- **The refusal messages.** Almost every `{"ok": false}` tells you exactly
  what to do instead, in the JSON you would need to type. "you can
  supervise, house and teach 0.0 more people, not 4" is a good sentence.
  This is far better than most simulation interfaces.
- **`why <id>` is excellent.** Cost broken into labour/materials/capital
  with the multipliers shown separately (`civ_domain_factor`,
  `material_distance_factor`, `opposition_factor`, `price_index`), plus
  `staff_needed_means` and `hired_labour_means` explaining what the numbers
  actually mean. I never had to guess what a field was.
- **Inventing professions.** `trades_that_do_not_exist_here`, `train`, and
  the events "you begin teaching the first engineers this world has ever
  had" / "2 engineers finish their training". That there is no engineer to
  hire in 900 AD because the job does not exist yet is the single best idea
  in the model.
- **The society-change events.** "Movable type and the screw press changes
  the society: literacy_elite, literacy_general, w_information, w_novelty".
  These are the only moments the world answers back.
- **Resource throttling with a named cause.** `"resource_throttle": 0.112,
  "throttle_binding": "coal"` plus "SHORT OF COAL: work running at 11% of
  plan" is exactly right: it tells you you are stuck and what you are stuck
  on, in one line.
- **The honesty about slavery.** "This is available because it was the
  ordinary condition of production in most of these societies, and a model
  that hides it lies about the cost of everything." I chose not to buy
  anyone and the game let that be a choice with a cost rather than a
  cost-free moral freebie. (Though in practice it was cost-free: the hire
  cap, not the labour supply, was what limited me.)

## What I expected and did not find

- **Any reason to make a trade-off.** From about year 905 to the end I never
  once had to choose between two things I wanted. Everything with positive
  net revenue paid for everything else. A tech tree game where the answer is
  always "yes, build it" is a spreadsheet, not a game. The fix is not more
  hazards, it is making revenue nodes *compete* — a market that saturates,
  a labour pool that a loom and a tannery both draw from.
- **Any downside to debt.** I ran 30,000 denarii in arrears for a decade and
  my interest rate went *down*, because reputation went up. `suspicion`
  stayed at 0.0 for the entire 362-year run despite my inventing five
  professions, publishing a world map, and building a central bank in Norse
  Scandinavia. `scandal` peaked around 5 and `auto_bribe` handled it.
- **Anything at all from the one hazard the game announced.** At year 900
  `knowledge_risk.known_hazards_ahead` warned me about "Christianisation and
  political consolidation", years [995, 1100], "changes the value vector
  rather than killing people", `what_you_can_do: {}`. I played straight
  through 995-1100 and nothing observable happened — no event, no changed
  number I could attribute to it. An empty `what_you_can_do` on the one
  named hazard in a 500-year game is a missed opportunity.
- **Succession.** `founder_ages: false`. I personally worked 2,400 hours a
  year from 900 to 1262. Nothing in the fiction accounts for this and
  nothing in the mechanics does either.
- **A way to see how I did.** There is no score, no summary at the end, no
  "you reached the transistor in 1262, X years faster than the median run".
  The run just stops and `state` refuses to advance.

## Summary of things I believe are bugs

1. `mil_atomic_bomb` startable in 978 AD for 341.6 denarii, with
   `direct_prerequisites: ["cap_tol_100um"]` and a note that admits it needs
   "the isotope separation and reactor programme".
2. Projects stalled `"waiting_on": "money"` for `still_to_pay: 2.3` while
   `capital` was 696,350 and rising. Some undisclosed cap on annual project
   spend.
3. `founder_hours_left` reported as large negative numbers (-776.8, -541.8).
4. The engine names `workshop_first` / `freedman_staff` / `school_founded`
   in its own advice strings while `why` on them returns "you have never
   heard of that".
5. The `hire` cap error offers `hire` as the remedy for being unable to
   `hire`.
6. `start_blocked_reason` says "something you have not heard of" while
   `missing_prerequisites` in the same object names it.
7. `auto_mine` / `auto_forest` on, `throttle_binding: "coal"` for years,
   `mine_capacity: {}`. The automation never fired; I had to buy by hand.
8. "IN ARREARS for 3 years: staff are leaving because you cannot pay them"
   while `employees_total` was 0 — and `artisans: 3.0` with
   `employees_total: 0` at the same time.
9. Cost outliers that read as unit errors: `md2_tourniquet` 210,340;
   `md2_surgical_glove` 210,299; `tx2_ballpoint_pen` 1,232,234;
   `ag2_milking_machine` 7,001,168 — sitting next to `md2_surgical_drape`
   at 302.
10. `state.goal` is `null` for the entire run, then the run ends on a goal.

Uncertain whether bug or intent, and why:
- **Zero-cost nodes completing without being started** (`civ_vault_barrel`,
  `civ_amphitheatre`, `cap_measure_len`). Probably intended — free nodes
  cascade — but it contradicts the documented `--manual` guarantee that
  "Nothing becomes active except what start_project() was explicitly told
  to start", so at minimum the doc is wrong.
- **New World crops and chinampas available to Norsemen in 900 AD.**
  Could be a deliberate "you know they exist, go get them" reading — the
  `ag2_*_voyage` naming hints at it — but nothing says so, and `fud_chinampa`
  is not a voyage node.
- **Roman flavour text throughout a Norse civ.** Could be an accepted cost
  of one shared dataset, but "a Roman artisan could not recognise success at
  this" as the refusal text in a Viking game reads as an oversight.
