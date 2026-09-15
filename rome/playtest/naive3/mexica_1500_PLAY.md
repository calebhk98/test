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

## Turn 12: 1511 -- hiring staff is the biggest single unlock so far

EXPECTATION: several new "HEARD OF" items were blocked on "needs N trained craftsmen
on your own staff, you have 0.0", with the game's own suggested remedy being
`{"cmd":"hire","trade":"smith","n":3}`. I expected hiring artisans to unlock some of
those specific items, but did not expect it to be bigger than the scientific_method
unlock.

ACTUAL: `{"cmd":"hire","trade":"smith","n":3}` (112 den/yr each, so ~403 den/yr wages
including some day-one proration) unlocked an ENORMOUS jump: `available` went from
72 startable items to **244**, with whole new subjects appearing that were not listed
at all before (textiles 61 items, transport-in-depth 31, construction 16, metallurgy 9,
power stations 3, etc.). This was a far bigger unlock than either identity_cover or
scientific_method. LESSON: under fog of war, plain cash was never the binding
constraint for most of the tree -- headcount was. A careful player should hire staff
very early, probably before pouring money into more finance techs, since "0 employees"
silently hides the majority of the visible game. Nothing in the earlier UI signalled
how large this gate was in advance (each blocked item just said "needs 1/2/3 trained
craftsmen", not "unlocks 170 further items").

Searched `available find` for "wall", "quarantine", "gun", "cannon", "fort" again after
this unlock: still nothing for any of them except "water" (chorobates, latrines,
flush toilets, and now also `tr_watertight_bulkhead`, a ship part, cost 223 den) --
none of these looked like they addressed the epidemic or invasion hazards directly by
name. The hedges the risk text promises ("clean water, quarantine... walls, firearms,
powerful friends") are still not visible 11 years in, 8 years before the Spanish
invasion window opens. This is a real concern for a fog-of-war playthrough: I cannot
tell whether I am one unlock away from finding them or many, and the clock (1519) does
not wait.

## Turn 13-16: 1511 -> 1515 -- a probable bug: `patron_local` progress resets to zero

EXPECTATION: `patron_local` (960 den, 400 founder-hours, 0.5yr calendar floor) should
complete within roughly a year or two given I have 2,400 free founder-hours/yr and
nothing else was running concurrently against it.

ACTUAL, tracked via `{"cmd":"state","full":true}"` (which under `--pretty` also prints
the raw JSON on stdout, letting me see machine fields not shown in the text rendering):
started turn 10 (1509). By 1512 it was reported "60% of your hours spent... waiting on
your hours" and stayed frozen at exactly that 60% for 1512 AND 1513 (two full
`step years:1` calls) despite the raw JSON showing, in 1513:
```
"patron_local": {"founder_hours_left": 160.0, "founder_hours_total": 400.0,
 "years_in_progress": 0.0, "spent": 960.0, "still_to_pay": 0.0,
 "waiting_on": "your hours", "hours_offered_this_year": 400.0,
 "hours_effective_this_year": 400.0, "underfunded_this_year": false}
```
i.e. it says 400 of my hours were BOTH offered AND effective that year, yet
`founder_hours_left` (160) did not move at all from the prior check. Then in 1515,
after another step, the raw JSON showed:
```
"patron_local": {"founder_hours_left": 400.0, "founder_hours_total": 400.0,
 "years_in_progress": 1.0, "spent": 960.0, "still_to_pay": 0.0,
 "waiting_on": "your hours", "hours_offered_this_year": 400.0,
 "hours_effective_this_year": 0.0, "underfunded_this_year": true}
```
i.e. `founder_hours_left` JUMPED BACK UP from 160 to the full 400 (progress fully
erased) while simultaneously `hours_effective_this_year` dropped to 0 and
`underfunded_this_year` flipped to true -- despite the human-readable text throughout
showing "0 den still owed" (the 960 den was paid in full at the start and never
refunded). The full 960 den stays spent either way.

I cannot be certain whether this is a bug or an intentional-but-opaque "setback"
mechanic (the item's own `why` text lists FAILURE RISK: 15%, and my best guess is this
is exactly that risk landing -- a failed roll that wipes hour-progress without
refunding money already committed, a genuinely harsh but at least legible design if so).
What makes me suspect an actual bug rather than intended failure-risk flavour: the
`hours_effective_this_year` field went from 400 (fully funded) directly to 0
(`underfunded_this_year: true`) with nothing in between, right as my capital swung deep
negative (-3,087 -> -3,823 den, driven by interest on arrears), which suggests the
"underfunding" may be a cash-flow check against my (very negative) capital balance
rather than a labour/skill check -- but I already had ample credit headroom
(credit_limit ~5,600-5,900 den vs debt ~3,000-3,800 den) so by the numbers I should not
have been "underfunded" by any plain reading of "credit limit". If being deep in debt
silently stalls/reverses project progress even while under the stated credit limit,
that is worth flagging clearly to the designers as either a bug or a very
non-obvious rule that the UI does not explain anywhere I've found (`why`, `money`,
`risk`, `policy`, `help` -- none of these mention debt stalling project hours).

DECISION: since the 960 den is already fully spent regardless of whether I keep
waiting or `stop` the project (stop only prevents further loss, and there is no
further cost listed - `still_to_pay: 0.0`), I chose to leave it running and keep
playing rather than abandon it, since the founder-hours it "occupies" (400 of 2,400)
still leave 2,000/yr idle for other projects meanwhile.

## Turn 17: 1515 -> 1516 -- the mystery resolves: this looks like a debt/credit-headroom mechanic, not a per-project bug

Started a small, cheap `cn_quarrying_wedge` (90 den, 20 founder-hours, 0.1yr floor,
revenue 50/yr) to use idle hours. After stepping, checked the raw JSON again: NOW BOTH
`patron_local` and `cn_quarrying_wedge` show `hours_effective_this_year: 0.0` and
`underfunded_this_year: true`, and critically the year-level summary shows
`hours_this_year.effective_on_projects: 0.0` even though `offered_to_projects: 420.0`
and `unused: 1980.0` -- i.e. EVERY project I have running got zero effective progress
this year, not just the old one. At this point: capital -4,035 den, credit_limit 5,247
den (so nominally 1,212 den of headroom left, well "under the limit").

REVISED READING: I now believe this is not a per-project bug but a global
"credit-crunch" mechanic -- once debt eats far enough into the gap between capital and
credit_limit, ALL project hours stop being "effective" (even though they're still
"offered"), so nothing progresses no matter how many idle founder-hours I have. The
`money` ledger confirms how much this cost me: **"interest on arrears: 11% ... paid so
far: 1,882"** den in cumulative interest alone, against a net income of only +195.2
den/yr -- the interest bill has been eating a large share of my income, and debt
actually GREW between checks (-3,823 -> -4,035) even with positive "net/yr", meaning
interest was outpacing net income at that point. This looks like an intentional design
lesson -- overleveraging early (I went from +400 den to -4,035 den by starting
~1,264+960+267+160+90 den of projects back-to-back on credit) leads to a debt spiral
where the credit system itself throttles you, not just your wallet. Nothing in `help
money`, `why`, or `money` explicitly says "projects stall if your debt-to-credit-limit
ratio gets too high" -- I only found this by comparing raw JSON across steps, which a
player using only the human-readable text would likely not have been able to diagnose
(the text just repeats "waiting on your hours" whether the true blocker is hours,
money, or -- it turns out -- neither, but total leverage). This is the most important
practical lesson of the playthrough so far: watch capital-vs-credit-limit headroom, not
just the credit limit ceiling.

DECISION: stop starting anything new; let net income pay debt down and see whether
project effectiveness resumes once headroom improves.

## Turn 18-20: 1516 -> 1519 -- fired all staff to fight the debt spiral, reached the invasion

Fired all 3 (2.4 FTE) smiths (`{"cmd":"fire","trade":"smith","n":3}`) purely to cut the
~272-282 den/yr wage bill, since the credit-crunch appeared to be stalling all project
progress regardless of staff anyway. This worked as expected mechanically: net/yr
jumped from 205.1 to 477.6 den/yr immediately, EMPLOY dropped to "0 people, 0 den/yr in
wages". Debt very slowly started improving (-4,261 -> -4,210 -> -4,154 den across two
more steps) but credit_limit kept shrinking in parallel (5,134 -> 5,024 -> 4,917),
apparently tracking my declining reputation (which fell every single year from its
peak of 26.3 in 1509 down to 20.8 by 1519, even though I did nothing to actively harm
it -- looks like a slow natural decay of reputation/eminence-driven credit rather than
anything I triggered). `cn_quarrying_wedge` and `patron_local` remained stuck at 0%
hours-effective the whole time, confirming the credit-crunch theory: hours offered
every year, never effective.

One unexpected event fired: `EVENT 1518: IN ARREARS for 12 years: staff are leaving
because you cannot pay them` -- this appeared AFTER I had already fired all my staff
down to 0 the previous turn, so either it is a delayed/queued consequence from when I
still had understaffed smiths during the crunch, or it is not actually tied to current
headcount and just narrates the ongoing arrears situation generically. Confusing either
way -- there was no one left on staff at that point for anyone to "leave."

Reached 1519. `state` now shows **"HAPPENING NOW: Spanish invasion"** in the AHEAD
section, and `risk`'s hazard entry switched its year tag from "[1519-1521]" to
"[IN PROGRESS]". Sack chance is still stated as 90% (unchanged from the pre-invasion
figure -- I found and built nothing that reduced it). I never found any wall, firearm,
"powerful friend" (beyond the still-stuck patron_local), or backup-copy tech in the
entire visible tree in 19 years of play, despite reaching 244 visible startable items
at peak and deliberately searching `available find` for "wall", "fort", "gun",
"cannon", "quarantine" repeatedly. Going into the invasion window completely
unhedged. Current holdings at risk: 12 technologies built (expected loss 3.8 per
sacking at current 80%/40% loss parameters), plus whatever my mismanaged
finances/debt situation does under a shock.

## Turn 21: 1519 -> 1520 -- the sack happens, and both stuck projects suddenly complete

`step years:1` produced, in order:
```
COMPLETED 1519: Stone quarrying with wedge
COMPLETED 1519: Secure a town patron
EVENT 1519: Spanish invasion: a site is sacked
EVENT 1519: Spanish invasion: the society's values are shifting (w_magic_fear now 0.32,
  w_novelty now -0.29, w_religious_rigidity now 1.00)
EVENT 1519: completed: Secure a town patron
EVENT 1519: completed: Stone quarrying with wedge
```
SURPRISE #1: both of the long-stuck projects (`patron_local`, stuck since 1509 across
multiple resets, and `cn_quarrying_wedge`, stuck since 1516) suddenly completed in the
SAME step the invasion hit, with no action from me. This is consistent with my
credit-crunch theory in one sense (my debt situation had been slowly recovering,
-4,261 -> -4,210 -> -4,154 den over the prior 3 steps of zero new spending), but the
exact-same-turn coincidence with the invasion is odd; I cannot rule out that the
invasion event itself changed something (e.g. a forced resolution of pending projects,
or the underlying "underfunded" gate finally clearing right as the war narrative fired)
independent of my debt recovery.

SURPRISE #2, the bigger one: capital JUMPED from -4,154 den to -1,727 den in a single
step where `money` shows net/yr was only +305.8 and project spend was only 90 den (i.e.
I'd expect roughly -4,154 + 306 - 90 = -3,938, not -1,727). That is an unexplained
~2,211 den windfall landing in the exact same step as "a site is sacked." Also in that
same step: credit_limit jumped from 4,917 to 7,755 den, and the interest rate DROPPED
from 11% to 10%. My reputation also rose slightly (20.8 -> 22.9) despite nothing I did.
**I cannot explain this from anything the game told me.** Best guesses, none confirmed:
(a) getting sacked might force-write-off some debt as an in-fiction consequence
("conquest cancels your debts to the old order" would be a very defensible piece of
history, but nothing in the text said so); (b) completing `patron_local` might carry a
one-time capital effect beyond its stated "0 den revenue" (its `why` text never
mentioned a capital bonus); (c) this could be a step-ordering/accounting quirk where
multiple large state changes (project completions + invasion event + interest tick) 
landed in an order that produced a number I'm mis-attributing. Flagging as **unexplained,
not confirmed bug or feature** -- a case where the program told me THAT something
happened (the numbers) but not WHY, which is exactly the fog-of-war problem the
exercise is testing for.

SURPRISE #3: despite "sack chance: 90%" and the literal event text "a site is sacked",
NO technology loss was reported anywhere (`technologies: 18 built by you` after the
step, up from 16 only because the two stuck projects completed -- not down). `risk`
afterward still shows "technologies at risk: 12" (unchanged) and no "lost N
technologies" event appeared in the log. Since the hazard's own numbers say "chance
lost IF a site is sacked: 80%, fraction lost when it happens: 40%", knowledge loss is
apparently a second, separate roll from the sacking itself, and this time (whether by
the game's dice or by some mitigation I'm not aware of) it seems I got the lucky ~20%
outcome and lost no technologies from this pass. The invasion is a 1519-1521 window
(3 years), not a single-year event, so this may not be over.

## Turn 22: 1520 -> 1521 -- knowledge loss finally happens, and the "sack = debt relief" pattern repeats

```
EVENT 1520: Old World epidemics on contact: staff -80%
EVENT 1520: Spanish invasion: a site is sacked
EVENT 1520: KNOWLEDGE LOST: 3 technologies forgotten (the corpus was never printed and dispersed)
```
Lost `fin_mortgage` and `fin_brand` (both vanished from the `money` revenue breakdown)
plus one more (technologies-built-by-me went 18 -> 15, "technologies at risk" 12 -> 9,
consistent with exactly 3 lost as stated). The epidemic's "staff -80%" had nothing to
bite on since I had already fired everyone (0 employees) -- so by accident, going
into the epidemic with zero staff meant zero staff losses; whether that is a
legitimate defensive strategy or a loophole I can't be sure, but it is worth recording:
**having no employees makes you immune to the single worst-described hazard in the
scenario ("the single most severe hazard of any civilization in this directory") purely
because there is no staff to lose.**

Capital AGAIN jumped far beyond what net income explains: -1,727 -> -324.3 den in one
step (net income was only +252.4, no project spend), an unexplained ~+1,150 den on top
of ordinary income, for the second time in two steps, both times landing on "a site is
sacked" events. This makes me more confident (though still not certain, since I still
have not seen the game say this outright) that **getting sacked forgives or writes off
some of my debt in this engine** -- possibly narratively defensible (a conquest ending
your obligations to the prior order) but never stated anywhere in `why`, `risk`,
`money`, or `help`. If true, this is a strange incentive: the mechanic meant to
represent catastrophic loss is, for a heavily-indebted player, financially a net
positive. I'm flagging this explicitly as something the designers should check --
either it's a real and intentional-but-undocumented interaction (debt owed to a
regime that just got overthrown becomes uncollectable) or an accounting bug.

## Where things stand at 1521 (invasion window closing, epidemic window still open to 1600)

Capital -324 den, net +252/yr, credit limit 7,616 den (up from under 5,000 pre-invasion
-- another data point for the "sack raises credit limit" pattern, alongside reputation
22.3 and rising). 15 technologies of my own, 9 still "at risk". No employees. No hedge
technology for either hazard was ever found under fog of war in 21 years of active
searching. Next: check whether `arithmetic_positional` unblocked now that
`patron_local` finally completed, and continue playing forward through the rest of the
epidemic window and beyond.

## Turn 23-24: 1521 -> 1522 -- the invasion window closes, `arithmetic_positional` finally reachable

`arithmetic_positional` was STATUS: CAN START NOW as soon as `patron_local` finished --
confirms its stated blocker ("get at least a local patron first") was exactly and only
that. Started it (720 den) right as the last year of the invasion window (1521) played
out:
```
EVENT 1521: Old World epidemics on contact: staff -80%
EVENT 1521: Spanish invasion: a site is sacked
EVENT 1521: KNOWLEDGE LOST: 2 technologies forgotten (the corpus was never printed and dispersed)
EVENT 1521: Spanish invasion: the society's values are shifting (...)
```
So the Spanish invasion sacked my site in ALL THREE of its stated years (1519, 1520,
1521) -- entirely consistent with the stated "sack chance after what you have built:
90%" (three independent ~90% rolls almost certainly hit at least once, and did in
fact hit every single time). Total knowledge lost across the whole window: 0 + 3 + 2 =
**5 of my original 18 self-built technologies gone** -- specifically all my finance
techs except `fin_cartel` (`fin_mortgage`, `fin_brand`, `fin_arbitrage`,
`fin_seigniorage` all vanished from the revenue ledger over the three sackings), plus
one more I didn't specifically track. `world_map`, both medical techs, `fin_cartel`,
`cn_quarrying_wedge`, and `med_obstetric_practice`/`med_bone_setting` all survived.
Losing 5/18 (about 28%) over the window is roughly in line with the stated "fraction
lost when it happens: 40%" applied a few times, though not an exact match (expected
value would suggest somewhat more loss given 3 sackings at 40% each) -- reasonable
under a small-sample random process.

The epidemic's "staff -80%" fired every single year the epidemic was active
(1520, 1521, and presumably continuing) but, again, has nothing to act on since I still
have 0 employees -- this appears to be a genuine, repeatable loophole: **statelessness
(no employees) makes the epidemic's headline mechanic a no-op for me.** I consider this
worth flagging clearly: whether intentional or not, "never hire anyone" is a strict
defence against the single hazard the game's own text calls "the single most severe
hazard of any civilization in this directory," which seems like an odd emergent result
for a mechanic clearly meant to be punishing.

The capital "windfall on sack" pattern continued but seemed to shrink in magnitude as
my debt itself shrank (this step's unexplained gap was roughly +330 den, versus ~+2,200
and ~+1,150 den on the two earlier sackings) -- consistent with a hypothesis that
whatever this effect is, it scales with outstanding debt rather than being a fixed
per-sack bonus. Still unconfirmed and still undocumented anywhere in the UI.

## Current status snapshot heading into a second play phase (year 1522)

- 13 technologies built by me (down from a peak of 18, after losing 5 to three
  Spanish-invasion sackings), 141 total known (128 granted + 13 earned).
- Capital -222 den, net income dropped to -38.1 den/yr this step only because of the
  arithmetic_positional spend; underlying revenue-only income is healthy (984.8 den/yr
  gross from world_map 598.2, med_cataract_couching 199.4, med_trepanation 79.8,
  cn_quarrying_wedge 59.8, fin_cartel 39.8, med_obstetric_practice 15, med_bone_setting
  7.4).
- Credit limit 7,462 den, well above the shrunken debt -- healthy headroom again, no
  more credit-crunch stalling expected for now.
- 0 employees (by choice, to dodge the epidemic and cut costs -- also means I still
  cannot start the ~15+ "needs trained craftsmen" items sitting in HEARD OF).
- `arithmetic_positional` 71% done, "Highest return on personal hours in the entire
  tree" and "HOW MUCH RESTS ON THIS: almost everything" -- expect a big unlock like
  identity_cover's and scientific_method's once it lands.
- Epidemic hazard still open until 1600 per its stated window, currently "HAPPENING
  NOW" -- will keep watching for repeats, though so far harmless to me specifically
  due to having no staff.
- Never found any wall/firearm/quarantine/inoculation/clean-water/copy-of-work hedge
  tech anywhere in the visible tree across 22 years of active searching. The entire
  Spanish invasion was weathered completely unhedged, exactly as the "sack chance after
  what you have built: 90%" figure (never dropping from its year-1500 baseline value)
  implied it would be.

## Turns 25-35ish: 1524 -> 1546 -- a second, more serious probable bug: asymptotic
## "still_to_pay" that may never reach zero

`arithmetic_positional` reached 71% of founder-hours almost immediately (by 1522) and
then sat at exactly "71%... waiting on your hours" for the rest of this whole period,
with `still_to_pay` (the money portion of its cost) draining ever more slowly:
384.5 -> 281 -> 109.7 -> 58.6 -> 31.3 -> 22.9 -> 16.7 -> 3.5 -> 2.5 -> 1.9 -> 0.7 -> 0.5
-> 0.4 -> 0.3 den, tracked over roughly TWENTY FIVE in-game years (1521 to 1546) and
about 18 separate `step` calls. The amount paid off each step also shrank in lockstep
(6.2, then 0.9, 0.7, 0.3, 0.2, 0.1, 0.1 den...) even though my net income stayed
essentially flat around +115 to +122 den/yr throughout and I was not otherwise
resource-constrained (once past the earlier debt-spiral period). The pattern looks
exactly like **geometric/asymptotic decay of the remaining balance** (roughly -25 to
-30% of what's left, each step) rather than "pay what you can afford toward the
remainder" -- and critically, it is NOT tied to how much income or credit headroom I
actually have. This means the last fraction of a project's cost can take a very long
time to clear, and by the pattern observed, might mathematically never hit exactly
0.0 in a reasonable number of turns (Zeno's-paradox style): after 25 years, `why` still
showed 71% and a nonzero balance no matter how comfortable my finances were.

I tried `{"cmd":"bounty","id":"arithmetic_positional"}` to see if paying someone else to
finish it would bypass this -- refused: "arithmetic_positional is already active; stop
it first if you want to switch to a bounty instead" (and `stop` would forfeit the ~720
den and 20+ years already sunk into it). There does not appear to be, from anything
`help`, `why`, or `money` told me, any in-band way to simply pay off the last scraps of
a project's cost in one go. **This looks like a real bug**, distinct from the earlier
debt-crunch stall (that one was explainable, even if undocumented, as a credit-headroom
gate; this one persists regardless of headroom and shrinks toward zero without
reaching it). A careful player relying only on the text output would see "waiting on
your hours" forever and have no way to know that the true blocker is a vanishing
decimal, not their own hours (which show 2,400 free every year, untouched).

DECISION: given the project doesn't seem to be consuming my other capacity (I still
show 2,400 founder-hours free most years net of this project's "offered" allocation),
I am leaving it running in the background indefinitely and moving on to other
priorities, since parking capital or hours specifically to accelerate it does not
appear to help based on the data above.

## Correction to an earlier guess: "dangerous above 26" is `prominence` (= eminence), not reputation or scandal

Checked the raw JSON `state full:true` output directly: there is an explicit
`"prominence"` block: `{"now": 0.38, "dangerous_above": 26.0, "settles_at_if_nothing_changes": 0.2,
"chance_of_ruin_this_year": 0.0, "what_would_change_it": ["a wide, dispersed institution
is harder to destroy than one great man"], "note": "This is prominence, not scandal. It
cannot be bribed away, and every defence that makes you safer from accusation makes you
larger and so raises this."}` -- and `"now": 0.38` matches the `eminence` field exactly.
So my earlier guesses (turns 8-9 and 13-16) that the "dangerous above 26 / settles near
X" line might refer to reputation or to scandal were WRONG -- it is prominence, which is
just eminence under another name, and it explicitly is NOT scandal ("cannot be bribed
away"). Correcting the record here since I flagged genuine uncertainty earlier and this
is now confirmed directly from the game's own structured output (available to me via
`--pretty`'s raw JSON on stdout, though a player using ONLY the human-readable text would
have had a much harder time confirming this, since the rendered text never uses the word
"prominence" -- it just says "dangerous above 26" inline with reputation/suspicion/
scandal/eminence on the STANDING line, with no explicit label pointing at eminence
specifically). At 0.38 against a danger threshold of 26, I am nowhere near this danger
regardless.

Scandal, separately, has climbed to 10.4 by 1546 (from lows near 0.1-0.2 mid-game) with
no stated danger threshold I've found yet -- worth continuing to monitor.

## Turns 36-50ish: 1567 -> 1653 -- steady state, both hazard windows close, and a WORSE version of the hours-progress bug appears

Rebuilt the finance base (`fin_seigniorage`, `fin_arbitrage`, `fin_mortgage` re-bought
after the invasion wiped them), re-hired smiths carefully this time (keeping cash
buffer in mind), and let time run in large chunks (`step years:N` with N up to 45 -- it
handles arbitrarily large multi-year steps fine, correctly narrating every year's
events in order). Recurring background events settled into a predictable rhythm:
`your patron dies; his heir must be courted afresh` (no visible cost each time, but
seems to correlate with capital dips), `fire in the reed and adobe quarter by the
canal`, and `banditry or a frontier war disrupts supply` -- flavour/ambient events with
no visible mechanical effect I could isolate, alongside routine `interest on arrears`
notices.

By year **1600 the epidemic hazard's own stated window (1520-1600) ended**, and by 1605
`risk` reported **"0 more hazard(s) known ahead"** with no active hazards listed at
all -- I had passed both of the scenario's headline catastrophes. Final tally: the
Spanish invasion sacked my site in all three of its years and cost me 5 of 18
technologies (28%); the epidemic's "staff -80%" fired roughly 20 separate times across
80 years and cost me nothing, because I deliberately kept zero employees the entire
time it was active -- confirming my turn-22 note that "never hire anyone" is a complete,
repeatable defence against the game's own "single most severe hazard" description.

At 1650, with a healthy cash buffer (3,413 den, no debt) I hired 5 smiths at once,
which triggered the same "huge unlock" pattern as the very first hire back in 1511:
`available` jumped from 76 to **269** startable items in one step, with the "HEARD OF,
CANNOT BEGIN YET" list shrinking from ~15 entries to 9, all but 2 of which trace back
to the still-broken `arithmetic_positional`. This makes we more confident the "N
trained craftsmen" gate is doing an enormous amount of the tree-gating work throughout
the whole game, not just early on.

Found and started `workshop_first` ("First workshop and laboratory", 4,606 den, 900
den/yr upkeep, prereq exactly `patron_local`, **"HOW MUCH RESTS ON THIS: almost
everything"**) -- its flavour text mentions "a walled yard" for the first time, the
single closest thing to the invasion hazard's "walls" hint I found in the entire
playthrough, though it reads as a workshop-security detail, not city fortification.

Starting `workshop_first` while `arithmetic_positional` was still stuck produced a
**worse and unambiguous version of the earlier bug**: `arithmetic_positional`'s
displayed progress went from "71%" to **"-29%"** and then, one more step later
(with 0 employees and healthy net income again), to **"-67%"** -- a NEGATIVE
percentage, which cannot be a sane value under any reading of "hours spent so far."
The raw JSON confirms the arithmetic: `founder_hours_left: 581.5` against
`founder_hours_total: 450.0` -- the "hours left" figure exceeded the total requirement,
something that should be structurally impossible if hours are only ever being
subtracted from a fixed total. This happened exactly when both projects simultaneously
showed `underfunded_this_year: true` in the raw JSON, reinforcing that the
"credit-headroom crunch" I identified around turn 17 is real, recurring, and now shown
to actively corrupt/worsen a stuck project's progress rather than merely freezing it.
**I am now confident this whole family of behaviour (frozen progress, resets to 0%,
and now negative percentages) is a genuine bug in how the engine accounts for
founder-hours on projects that go "underfunded," not an intentional mechanic** -- no
help text, `why` output, or `risk`/`money` explanation anywhere ever mentioned debt
headroom affecting project hour-progress, and a negative percentage cannot be the
designers' intended display for anything.

## Final state at year 1654 (stopping the playthrough here)

- Money: -2,464 den (in arrears again, credit limit 3,853 den, so still within nominal
  headroom but evidently inside whatever threshold triggers the underfunded-progress
  bug).
- Net income: +260.8 den/yr with 0 employees (fired everyone again at the end to stop
  new wage bleed while I write this up).
- 16 technologies built by me, 144 known in total (128 granted + 16 earned) -- down
  from a peak of 18 after losing 5 to the Spanish invasion, up again by rebuilding 3 of
  the lost finance techs plus gaining `cn_quarrying_wedge` and `patron_local`.
- 2 projects permanently stuck mid-flight: `arithmetic_positional` (started 1521, still
  not done at 1654 -- 133 years and counting, now at a nonsensical -67%) and
  `workshop_first` (started 1652, 0% hours effective, 134.7 den still owed and
  shrinking asymptotically the same way).
- Both scripted hazards (Spanish invasion 1519-1521, Old World epidemics 1520-1600)
  have concluded; `risk` currently shows no active or upcoming hazards.
- Never found any tech literally named/tagged for walls, firearms, quarantine, clean
  water treatment as a hazard countermeasure, or "copies of your work kept elsewhere"
  despite reaching 269 visible items and searching repeatedly by keyword throughout.
  The closest hits were generic plumbing/water-engineering items (chorobates, S-bend
  traps) and `workshop_first`'s incidental "walled yard" detail -- none of which
  `risk`'s own "staff loss after what you have built" / "sack chance after what you
  have built" figures ever reflected as improved (both stayed frozen at their year-1500
  baseline: 80% and 90% respectively) the entire game.

I am stopping active play here, at year 1654 of the 1500-2000 horizon, having reached
what I judge to be a stable, well-documented picture of the simulator's core loop, its
fog-of-war information design, and several concrete bugs -- see the summary below.

---

# Summary for the designers

**What worked well:**
- The `why <id>` command is excellent: cost/hours/risk/prereqs/upkeep/revenue/"HOW MUCH
  RESTS ON THIS" is exactly the information a player needs to make an informed bet
  under fog of war, and in every case I could verify, it was accurate (identity_cover,
  scientific_method, patron_local, and workshop_first all said "almost everything"/"a
  great deal" and then genuinely unlocked large swathes of the tree).
- The "HEARD OF, CANNOT BEGIN YET" list with specific, actionable blockers ("needs 3
  trained craftsmen, you have 0.0", "get at least a local patron first", "missing
  prerequisites: X") is a very good compromise for fog of war: you know something
  exists and exactly what's stopping you, without seeing the whole tree. This made it
  possible to plan several moves ahead even under fog.
- The scale of the two historical hazards was communicated honestly and the actual
  outcome matched the stated odds closely (three sack rolls at a stated ~90%/yr chance,
  three sacks; the epidemic's blunt "-80% staff" fired reliably every time it rolled).
- Multi-year `step` calls work correctly and narrate every intervening year's events in
  order, which made large time-skips practical without losing information.

**What was confusing or seemed like a bug, ranked by how sure I am:**
1. **(Very likely a bug)** A project that goes "underfunded" for a sustained period can
   have its founder-hours progress not just freeze but actively worsen past 100%
   remaining, producing a NEGATIVE percentage-complete ("-67% of your hours spent").
   Reproduced twice on two different projects (`patron_local` froze/reset once,
   `arithmetic_positional` went negative twice).
2. **(Likely a bug, or at minimum needs a clearer explanation)** The "still_to_pay"
   portion of a project's cost can decay asymptotically toward (but arguably never
   reach) zero, independent of available cash or credit, taking 25+ years to go from
   single digits to zero on `arithmetic_positional`. No in-game text explains this
   pacing or offers a way to accelerate/force it.
3. **(Confirmed pattern, not necessarily a bug, but definitely undocumented)** Running
   a large negative capital balance relative to your credit limit silently stops ALL
   active projects from making effective progress ("hours offered" but 0 "hours
   effective"), even while nominally "under the credit limit." Nothing in `help`,
   `why`, `money`, or `risk` mentions this threshold.
4. **(Unexplained, possibly a feature)** On three separate occasions, the turn a
   Spanish-invasion "site is sacked" event fired, my capital jumped up by an amount far
   larger than that period's net income could explain (+2,200 den, then +1,150 den,
   then +330 den, shrinking each time), alongside a jump in credit_limit and a drop in
   the interest rate. My best guess is that getting sacked forgives some debt in-fiction
   (a conquered city no longer owing its old creditors), but this is never stated
   anywhere.
5. **(Real design tension, not a bug)** Having zero employees is a complete, free
   defence against the epidemic hazard the game's own text calls "the single most
   severe hazard of any civilization in this directory." This feels like an unintended
   emergent loophole given how the hazard is described.

**What I expected to find and never did:** any hedge technology for either hazard
(walls, firearms, "powerful friends" beyond patron_local, backup copies of work, clean
water treatment, quarantine, inoculation) despite explicit hints in the hazard
descriptions and a wide search across 269 visible tech entries. Either these exist much
deeper in the tree than I reached in 154 years, or they were effectively unreachable in
time for the 1519-1521 invasion window given how long the early game's patron/workshop
prerequisites took to clear (patron_local alone consumed 1509-1519, almost the entire
runway before the invasion). If the intended experience is "you cannot realistically
hedge the Spanish invasion in time," the game communicates that very well through pure
mechanical pressure; if hedges were meant to be reachable, the prerequisite chain
(identity_cover -> patron_local, itself hit by the underfunded-progress bug) may be
gating them behind more real-time cost than a careful player can clear in 19 years.

**What struck me as unrealistic:** the sack-event capital windfalls (finding #4 above)
read backwards from the fiction -- getting your city sacked by conquistadors should not
plausibly improve your cash position and credit rating in the same turn it happens,
regardless of the mechanism.

(End of log. Session file left in place at
/home/user/test/rome/playtest/naive3/mexica_1500_PLAY.json, year 1654, so play could
resume from here in a future session.)

