# Playtest notes: mexica_1500, fog of war, naive3

Session file: /home/user/test/rome/playtest/naive3/mexica_1500_PLAY.json
Command: `python3 rome/sim/simulator.py agent --civ mexica_1500 --fog --session .../mexica_1500_PLAY.json`

Format: I write EXPECTATION (what I think a command will do/cost/unlock and why)
before running it, then ACTUAL (what happened), then a note if I was surprised.

## Setup / orientation

Ran `{"cmd":"help"}` with no args first to read the welcome text. Key lines quoted:

- "You are one person, dropped into a pre-industrial society, carrying the knowledge
  of how modern technology works but none of the industry that makes it. You are
  playing The Mexica Triple Alliance, beginning in 1500. Knowing how a thing works is
  free. Building it is not: it takes your own hours, other people's hours, money,
  materials, and years."
- "You begin projects, then advance time. Nothing happens unless you make it. You are
  charged for food, rent and appearances every year whether or not you are building
  anything."
- "Advance as far as you can before the horizon at 2000. There is no score but the
  state of what you have built."
- "No employees, no slaves, nobody who owes you anything. Anyone who works for you is
  hired, taught, commissioned or bought."
- The four core commands: `state`, `available`, `why <id>`, `step <years>`.

Next: reading the other help topics (commands, labour, economy, money, automatic,
sittings, fog) before doing anything that costs money or time.

## Help topics summary

- `commands`: state, available, why, start, stop, step, money, quote, close, risk,
  labour, hire/fire/train/commission, buy, work, bounty, mothball/restore, bribe,
  policy, path (disabled under fog), save/load, help, quit.
- `labour`: trades are NOT interchangeable. hire (annual wage regardless of work),
  fire, train (teach a trade that doesn't exist here, costs your own hours), commission
  (buy a one-off job).
- `economy`/`money`: buy forest (coppice -> charcoal), buy mine (quote first! takes
  years to sink, costs upkeep even unused), buy slaves, manumit (free slaves - "they
  then work better, and it is the decent thing"), debt allowed up to a credit limit,
  interest on arrears.
- `automatic`: policy toggles for auto_hire, auto_buy_people (slaves), auto_manumit,
  auto_train, auto_mine, auto_forest, auto_mothball, auto_shed, auto_bribe. All off by
  default except auto_mothball and auto_shed (True by default).
- `fog`: "You can see what you have built, what you could begin today as a one line
  summary, and things you have heard of but cannot yet begin. You cannot see where
  anything leads, and there is no way to view the whole tree." `path` command disabled.

## Initial state, year 1500

- Money: 400 den, net +2.7 den/yr income currently (before any project spend).
- 2,400 founder-hours free this year (my own labour budget).
- No staff, no buildings running.
- Reputation 5, suspicion 0, scandal 0, eminence 0. "dangerous above 26 (settles near 0
  if nothing changes; 0% chance of ruin this year)".
- 128 technologies granted for free (i.e. known but not built), 0 built by me.
- Revenue 232.6 den/yr comes from med_cataract_couching (166.7) and med_trepanation
  (66.7) -- apparently I start knowing/practicing some medicine that earns money passively?
  Costs: living and appearances 230/yr fixed. Net 2.7/yr. Credit limit 1,093 den,
  interest on arrears 12%.
- 83 things startable now, cheapest 6 range 4-16.8 den.

### Two big scheduled threats (this is the headline finding of the whole playthrough)

1. **[1520-1600] Old World epidemics on contact** -- "Smallpox, measles and typhus in a
   population with no immunity. This is the single most severe hazard of any
   civilization in this directory and it is not a fair fight." Staff loss: I take 100%
   of it currently; "staff loss after what you have built: 80%" (so something I already
   have/get for free cuts it from 100 to 80, or that's just current mitigation = none
   yet, need to check). What would help: "clean water, quarantine, and eventually
   inoculation".
2. **[1519-1521] Spanish invasion** -- "The conquest does not just take the city, it
   replaces the religious order that ran it... " sack chance 100% currently, "after what
   you have built: 90%". What would help: "walls, firearms, powerful friends, and
   copies of your work kept somewhere else".

## Scouting: things related to the two big threats are NOT visible yet

Tried `{"cmd":"available","find":"..."}` for wall, quarantine, water, firearm, gun,
inocul, copy, friend. Only "water" matched anything (chorobates water levelling,
latrine/flush toilet S-bend traps) -- none of the others appear at all under fog. This
confirms the fog-of-war description literally: I cannot see techs I have not "heard of"
yet; the hedges for the two catastrophes are presumably deep in the tree behind
prerequisites I haven't unlocked. I will have to tech toward them blind and re-check
`available` periodically as new things unlock.

## why on a few standalone/meta items (before spending)

- `arrival_orientation` ("Six months of listening before you act"): tier 0, confidence
  C. "OPTIONAL, and no longer a prerequisite for anything. It buys you accurate local
  prices, the actual law of this province, who is who, and a large reduction in early
  blunder risk... The simulator lets you skip it, because a model that forces the
  cautious opening is not a model, it is an opinion." Cost 480 den, 900 of my hours,
  0.5yr floor, 2% risk. "HOW MUCH RESTS ON THIS: nothing else; this is worth having for
  itself." -- i.e. pure quality-of-life, not a gate. Skipped for now: too expensive
  relative to starting 400 den, and nothing downstream needs it.
- `identity_cover` ("Establish a respectable cover identity"): tier 0, confidence C.
  Buy books/house/clothes/secretary/reputation for piety -- "Reduces all future
  suspicion." Cost 1,264 den, 500 of my hours, 0.5yr floor, 5% risk, plus 200 den/yr
  UPKEEP once built. Crucially: **"HOW MUCH RESTS ON THIS: almost everything."** This
  is clearly a load-bearing early unlock (probably gates a lot of the tree, or at least
  suppresses suspicion/scandal that would otherwise choke me). EXPECTATION: this should
  become priority #1 once I can afford 1,264 den + still have buffer, likely well before
  I try anything overtly commercial/illegal-sounding (monopoly, cartel) since those raise
  suspicion/scandal.
- Medical techs `med_cataract_couching` and `med_trepanation` show STATUS: DONE already
  (0 cost) -- these are pre-built/granted, and they explain the starting revenue 232.6
  den/yr. Confirms the founder arrives already a practicing physician-surgeon type in
  this scenario (matches "carrying the knowledge of how modern technology works").
- Finance-subject items (`fin_employment_contract`, `fin_apprenticeship`,
  `fin_trademark`, `fin_seigniorage`, `fin_usury_law`, `fin_arbitrage`, `fin_monopoly`,
  `fin_cartel`, `fin_mortgage`) are all cheap (8-46 den), fast (0.2-1yr floor), low risk
  (5-20%), and every one of them individually says "HOW MUCH RESTS ON THIS: nothing
  else; this is worth having for itself" -- i.e. flat, non-gating, but several carry
  real recurring REVENUE at roughly 80-85% of build cost per year (seigniorage 20 den
  cost -> 16.7 den/yr revenue; arbitrage 30->25; cartel 41->33.3; mortgage 46->38.3).
  That is an extremely good return (paying for itself in ~14 months) with no listed
  upkeep. EXPECTATION: building all the affordable revenue-bearing finance techs early
  should be a strictly good move to bootstrap capital for the expensive
  identity_cover/hedge techs later, as long as it doesn't trigger scandal/suspicion
  problems (cartel and monopoly are described as "often illegal"/"breaks existing
  merchants' ability to compete", so I expect some scandal risk from those specifically).

## Turn 1: 1500 -> 1501

Started (same year, no cost yet -- payment happens as `step` consumes hours):
`fin_employment_contract` (8 den, 60h, 1yr floor) and `med_bone_setting` (7.4 den, 0h,
0.5yr floor). Note: `start` doesn't charge money immediately -- state afterward still
showed "Money: 400 den" with the two projects listed as "still owed - waiting on your
hours"/"waiting on money". So cost is realized during `step`, not at `start`.

`{"cmd":"step","years":1}`: both projects completed within the year (even the 1-year
floor one). Result: Money 401.8 den, net +5.9 den/yr (up from +2.7), reputation 7.9 (up
from 5), eminence 0.01, technologies built-by-me 2. So a batch of 15.4 den across the
two projects still netted me *more* cash than I started with, because bone_setting's
revenue (6.2/yr, prorated) plus base income covered it within the year.

SURPRISE: I expected `step years:1` to possibly leave a 1-year-floor project (the
employment contract) partially done, since it has a 1-year calendar floor and I only
stepped exactly 1 year -- it exactly finished, not partially. Calendar floor appears to
be a minimum, and with hours available up front it completes right at the floor.

## Turn 2: 1501 -> 1502 -- batch of finance techs

EXPECTATION: start all the affordable revenue-bearing finance techs
(`fin_apprenticeship`, `fin_trademark`, `fin_usury_law`, `fin_seigniorage`,
`fin_arbitrage`, `fin_monopoly`, `fin_cartel`, `fin_mortgage`) plus
`med_obstetric_practice` (15 den, 12.5 den/yr revenue) in one go, using 401.8 den of
capital (total cost ~258.7 den for the 9 items) and 720 of my 2,400 hours/yr. Expected
this to be net-positive quickly given the ~83% revenue/cost ratios seen in `why`, and
did not expect scandal to be a real cost yet.

ACTUAL: Started all 9 simultaneously, then `step years:1`. All completed in 1502 except
Mortgage (60% of hours spent, still running -- 120h needed, evidently hours got shared
across many concurrent projects so it didn't finish in 1 year even though its own floor
is 1yr) and Obstetric practice (100% hours spent, "waiting on the calendar" -- floor is
0 years but apparently still needed to roll into the next year tick to register?).
Money dropped to 155 den (243.8 den spent on projects), net income jumped to **+76.8
den/yr** (from +5.9), reputation jumped to 19.7 (from 7.9), and a new stat appeared:
**scandal 1.4** (was 0). Technologies built-by-me: 9.

Ledger breakdown confirms revenue sources: med_cataract_couching 177.8, med_trepanation
71.1, fin_cartel 23.7, fin_arbitrage 17.8, fin_seigniorage 11.9, med_bone_setting 6.6.
Notably fin_monopoly, fin_mortgage (still building), fin_usury_law, fin_trademark,
fin_apprenticeship, fin_employment_contract contribute **no revenue line** -- matches
what `why` showed (only cartel/arbitrage/seigniorage/mortgage had a REVENUE field; the
others are pure reputation/legal-framework techs with no direct income, exactly as
predicted).

CONFIRMED: cartel and/or monopoly (the "often illegal" ones) are the likely source of
the new scandal 1.4 -- consistent with my prediction. Need to check `risk` to see how
dangerous scandal is before doing more ethically-shady finance techs.

## Turn 3: 1502 -> 1503 -- mortgage completes, scandal note

`step years:1` completed Mortgage. Money 260.9 den, net jumped to +166.5 den/yr.
Reputation 21.6, **scandal dropped slightly to 1.2** (from 1.4) on its own with no
action from me -- so scandal decays over time rather than being permanent, good to
know. `risk` command re-checked: still just the same two hazards, no separate scandal
danger explanation shown there (scandal ruin mechanics must live elsewhere, inferred
from the STANDING line "dangerous above 26 ... 0% chance of ruin this year" which I now
think refers to *suspicion*, not scandal, since suspicion is the stat sitting at 0 and
threatening to rise).

Checked `available` again: list shrank from 83 to 74 (the finance techs I already built
disappeared, as expected -- consumed). New items appeared in the cheapest-six list I
hadn't seen before (`fin_brand`, `fin_usury_evasion`) -- so the visible frontier does
shift as you build, even though these specific two weren't gated behind anything I
built (their prereqs were presumably always met, they just weren't shown in the
original CHEAPEST SIX because that view is truncated/sorted, not because they were
locked). Also surfaced a **"HEARD OF, CANNOT BEGIN YET"** section for the first time:
`fin_company_town` needs "1 trained craftsmen on your own staff, you have 0.0" with a
helpful pointer to hire/commission/train/buy-slaves-then-manumit. This is a genuinely
useful fog-of-war feature: the game tells you a thing exists and exactly what's
blocking it, even though you can't see what it unlocks.

## A confusing/possibly-buggy case: `med_obstetric_practice` took far longer than its
own numbers implied

EXPECTATION: `med_obstetric_practice` has CALENDAR FLOOR 0 years and YOUR HOURS 0 (no
founder time required at all), so I expected it to complete within the very next
`step`, same as `hom_eraser_breadcrumb`-style trivial items.

ACTUAL: It was started turn 2 (1501->1502) alongside the finance batch. By the very
next state check it already showed "100% of your hours spent, 0 den still owed -
waiting on the calendar" -- and then it STAYED in that exact state, unchanged, through
FOUR more `step years:1` calls (1502->1503->1504->1505), i.e. roughly 3-4 in-game years,
before finally printing `COMPLETED 1505: Obstetric practice`. `why` on it mid-wait
showed `STATUS: ACTIVE` (not "CAN START NOW" or "DONE"), all prerequisites met, 0 owed.
Also discovered while poking at it: `{"cmd":"step","years":0.1}` is REFUSED with
"years must be >= 1" -- step only accepts whole years >= 1, so I could not single-step
finer to see exactly when in a year it flipped.

This is the single most confusing thing so far. A project advertising "0 years floor,
0 hours needed" that then visibly sits fully-paid-and-fully-staffed for 3-4 real years
before completing contradicts what its own `why` printout told me going in. I cannot
tell from the outside whether this is: (a) intended -- e.g. some hidden per-step
completion-roll/queueing mechanic, possibly related to the 15% FAILURE RISK rolling
each step until it succeeds, or a cap on how many things can resolve per step when many
projects are queued at once; or (b) a bug where a 0-floor project's completion check
divides by/depends on its (zero) duration and never naturally triggers except via some
fallback path. Flagging as **possible bug, unconfirmed** -- a careful player reading
only the `why` output would have no way to predict this multi-year delay.

## Turn 4-6: 1503 -> 1506, letting the queue clear

Nothing new started; just stepped through to let Mortgage and Obstetric finish and
watch income compound. Net income climbed steadily on its own each year (166.5 -> 185.1
-> 182.4 -> 189.1 den/yr) purely from the revenue-generating techs already built, no
further spending needed. By 1506: Money 789.6 den, technologies built-by-me 11,
reputation 21.6, scandal down to 0.89 (still decaying), suspicion still 0.

Now above the 1,264 den needed for `identity_cover`. Given "HOW MUCH RESTS ON THIS:
almost everything" from its `why` text, this is next.

## Turn 7: 1506 -> 1507 -- identity_cover pays off, confirms "almost everything"

EXPECTATION: identity_cover (1,264 den, 500 hrs, 0.5yr floor) should unlock a
meaningfully larger slice of the visible tree given its own "HOW MUCH RESTS ON THIS:
almost everything" line, and add ongoing upkeep (200 den/yr) plus presumably reduce
future suspicion as advertised.

ACTUAL: Completed in 1 step. Money went to -285.3 den (first time in debt -- fine,
credit limit is ~4,800+ den). Immediately new things appeared:
  - New subject "society and politics" (1 item): `patron_local` "Secure a town
    patron", 960 den.
  - New subject "mathematics and method" (2 items): `scientific_method` (160 den,
    "Multiplier on every research node thereafter... HOW MUCH RESTS ON THIS: a great
    deal") and `world_map` (266.8 den, REVENUE 500 den/yr(!), prereq exactly
    identity_cover, "HOW MUCH RESTS ON THIS: a few things").
  - New "HEARD OF, CANNOT BEGIN YET" entries: `arithmetic_positional` ("Highest return
    on personal hours in the entire tree... HOW MUCH RESTS ON THIS: almost
    everything", but STATUS: BLOCKED -- "the state is wary of this (state interest
    -0.5); get at least a local patron first") and `med_obstetric_antisepsis` (needs an
    unknown prereq).
CONFIRMED: identity_cover really was a major gate exactly as its own text warned, and
the "why" self-description was accurate and trustworthy going in -- good sign for the
readability of this system under fog of war.

## Turn 8-9: 1507 -> 1509 -- world_map is an extraordinary investment

Started `world_map` (266.8 den) + `fin_brand` (30 den) + `fin_usury_evasion` (36 den),
all completed by 1508. world_map's revenue is NOT flat -- it started at 412.8 den/yr
(1509) and had grown to 629.7 den/yr by 1510 just from the passage of time / rising
reputation, nearly 2.5x the build cost, every year, indefinitely. This one item alone
came to dominate my income. Also noticed revenue on my older techs (med_cataract_couching,
med_trepanation etc.) creeping up slightly year over year too (202.9 -> 206.4 -> 209.9),
so it looks like ALL revenue-generating techs scale a bit with some rising stat
(reputation? eminence?) rather than staying fixed at their `why`-quoted value -- the
`why` revenue figure is evidently a base/reference number, not a hard constant.

Noticed reputation crossed 26 here (26.3), and the STANDING line changed its
qualifier text from "(settles near 0.70/0.80 if nothing changes...)" to "(settles near
1.1 if nothing changes...)" -- I still cannot tell for certain which stat "dangerous
above 26" and "settles near X" refer to (my best guess now is it's about scandal's
long-run equilibrium level given current behaviour, not reputation itself, since
scandal has been the only stat visibly trending/decaying near those magnitudes; reputation
itself only ever goes up and 26 read as a plain threshold would suggest danger, but nothing
bad happened at 26.3 or later at 25.5-26.3, and "0% chance of ruin this year" stayed 0%
throughout) -- flagging as something the UI could state more plainly; I am inferring,
not certain.

## Turn 10-11: 1509 -> 1511 -- patron_local + scientific_method, and a big tree-opening

EXPECTATION: `scientific_method` (160 den, upkeep 100/yr, revenue 0, "HOW MUCH RESTS ON
THIS: a great deal") should unlock a batch of new visible items given how strongly its
`why` text was worded, more than the modest previous unlocks. `patron_local` (960 den)
should unblock `arithmetic_positional` specifically per its stated requirement.

ACTUAL: Both started together, `scientific_method` completed first (1510) with a
flavour event: `EVENT 1510: Controlled experiment, hypothesis, replication,
publication changes the society: w_magic_fear, w_novelty` -- first time I've seen a
tech announce a change to underlying society "values" directly in the event log,
confirming the `why`/risk text about "values" mentioned back in the Spanish-invasion
hazard description is a real, referenced mechanic (`w_magic_fear` presumably tracks how
much my unexplained-looking tech is read as sorcery -- directly relevant to the
invasion-era "diabolism or sorcery to be extirpated" line).

`available` afterward jumped from a short "HEARD OF" list to a MUCH longer one (18
entries) covering entirely new subject areas I hadn't seen mentioned before:
`ag2_biological_control`, `ag2_nitrogen_cycle`, `ag2_plant_quarantine`,
`ag2_record_keeping_breeding`, `atomic_theory` (needs arithmetic_positional),
`corpus_written` (needs units_standards), `exp_openocean_navigation`, `fin_company_town`,
`fin_survey_map`, `md2_case_record`, `med_clinical_trials`,
`sc2_institution_patent_disclosure`, `sc2_method_controlled_experiment`,
`sc2_method_lab_notebook`, `sc2_method_peer_criticism`, `statistics_basic` (needs
arithmetic_positional). CONFIRMED scientific_method's "a great deal" claim -- this was
a much bigger unlock than identity_cover's was. Also confirms `ag2_plant_quarantine`
exists in the tree -- possibly relevant to the epidemic hazard's "quarantine" hint,
though I have not reached it yet (blocked on 1 unknown prereq).

STRIKING PATTERN: the *majority* of these newly-visible items are blocked the same
way -- "needs N trained craftsmen on your own staff, you have 0.0" -- with the exact
same boilerplate remedy text every time (hire/commission/buy-slaves-then-manumit). I
have gone 11 years without a single employee, living entirely off my own 2,400
hours/yr and one-off commissioned labour bundled into project costs. That clearly
cannot continue -- hiring actual staff (probably a smith, "trade" unspecified which is
needed generically as "craftsmen") looks like the next real bottleneck, not money.
NEXT: check `labour` command for hiring costs and hire artisans before doing anything
else, since so much of the tree is gated on headcount rather than cash.

EXPECTATION: Given the Spanish invasion window starts in just 19 years (1500->1519),
and sack chance is currently 90% even "after what I have built" (meaning baseline
mitigation is already priced in and is small), my main early strategic goal should be
racing to build hedges against these two catastrophes (walls/firearms/allies/copies of
work for the invasion; clean water/quarantine/inoculation for the epidemic) rather than
pure economic growth, since losing 80-100% of staff and having a 90% sack chance sounds
like it could wipe out most progress. I'll try to verify this by reading `why` on
relevant-sounding available techs before committing money in the early game.

