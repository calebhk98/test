# Playtest notes - Mexica Triple Alliance, 1500 AD start

Playing blind, no source reading. Command: `python3 rome/sim/simulator.py`.
Session file: `/root/.rome-saves/mexica_1500_4.json`.

## Setup (before year 1500)

Menu flow: New game -> pick civ (1-5) -> scenario flavour text -> fog of war
on/off -> starting wealth tier -> mortality on/off -> goal (1-17) -> horizon
(calendar length).

Choices made:
- Civ: 5) The Mexica Triple Alliance, 1500 AD.
- Fog of war: ON (default Y). Reasoning: this is the "normal" way to play,
  and the prompt says you can't turn it off later anyway, so I took the
  intended default experience.
- Starting wealth: default `poor_scholar` (quoted as 400 den in Rome-prices,
  converted to 320 cacao beans here at the 0.8x price multiplier for this
  civ). Interesting that money is denominated in "beans" (cacao) for the
  Mexica rather than "denarii" - good touch, it's reading the civ choice
  through to the UI text.
- Mortality: default N (off). The intro text frames this as "measuring the
  tree, not a lifespan lottery" - i.e. off-by-default is the analytical mode,
  on is the "real" mode. Took the default.
- Goal: default 1) Grown and alloy junction transistors (closure 168, floor
  142 years). This is clearly a multi-century megaproject. Took the default
  since nothing told me to pick otherwise and the intro framed it as "the
  original target."
- Horizon: default 4) Endless (no deadline). Made sense given the goal takes
  142+ years minimum and mortality is off.

First surprise: the opening flavour text is civilisation-specific and well
observed - it calls out chinampas, the dual aqueduct, compulsory schooling,
obsidian edges, and explicitly states there is no wheel-for-work, no draft
animal, no iron in this civilisation, and that this is deliberately "the
hardest start in the game" because of the 19-years-to-smallpox countdown.
That's a striking design choice: the game is telling me up front that doom
is coming on a fixed, known timer (1519, contact/conquest-adjacent), and that
*only I know it*. I don't yet know if that's just colour or an actual game
mechanic (an event at year 19). Noting this as something to watch for rather
than something I looked up.

## Year 1500 (turn 1)

Starting prompt format:
`[1500 AD | 320 beans | you:2000 hr | sch 1 art 1 | rep 5] >`

Worked out fast (under a minute) that the five starter verbs are: `state`,
`available`, `why <name>`, `start <name>`, `step`.

`state` gives a full dashboard: money + recurring net, founder-hours free,
RUNNING projects, EMPLOY (household places, staff), STANDING (reputation,
protection, scandal, eminence), AHEAD (hazards), and progress toward the
goal ("On the road there so far: 7 of its nodes" - so I started with 7 of
168 closure nodes already satisfied, presumably free starting techs/granted
ones, since it also says "114 granted for free" technologies).

`available` dumps a *lot*: 211 startable projects on turn 1, bucketed by
subject (textiles 61(!), finance 26, power and precision 18, roads/bridges
18, farming 14, household 13, etc). This is overwhelming for a first-time
player - there is no guidance at all on which of 211 options matters for the
actual goal, only a "MOST RESTS ON THESE" shortlist sorted by how many other
things depend on it. That shortlist turned out to be the actual useful
signal: `units_standards` and `identity_cover` and `scientific_method` all
say "HOW MUCH RESTS ON THIS: almost everything" when inspected with `why`.

Confusion #1 (resolved in ~2 min): the "textiles" subject has 61 available
items on turn 1 as the Mexica, who historically did not have sheep/wool or a
spinning wheel the way the flavour text implies (the IDs are prefixed
`tx2_...` and look generic - "Bleaching by sunlight", "Retting of flax",
"Shed: warp separation", "Yarn count standardisation" - these read as
European/Old World textile techs, not obviously adapted to Mesoamerican
cotton/agave weaving). I did not dig into this further (didn't want to read
source), but it's a thing that looked like it might not be civ-flavoured
under the hood even though the framing text elsewhere clearly is. Flagging
as "possibly generic content reused across civs without a Mexica-specific
pass," not confirmed.

`why <id>` is rich: tier, category, a flavour paragraph, full cost
breakdown (labour/materials/capital, then multipliers for civ/distance/
scarcity/opposition/prices), hours needed, calendar floor, failure risk (and
what you lose if it fails), staff needed to BUILD vs staff needed to KEEP
OPEN (explicitly flagged as two different numbers, checked at different
times - `start` checks the first, `open` checks the second), hired-labour
breakdown by trade, materials, upkeep/revenue, and "HOW MUCH RESTS ON THIS."

Good explanatory text: projects are NOT charged or earning until you
`open` them - finishing buys the knowledge, running it is a separate
decision. This was stated clearly and I didn't have to guess at it.

Started (in this order): `scientific_method` (160 beans, 350 hrs, 2yr floor,
20% risk, "almost everything" rests on it), then free-and-instant
`sea_pharos_lighthouse` (0 cost/hours/years - pure flavour completion, "this
is worth having for itself," nothing else rests on it), then
`units_standards` (355.2 beans, 300 hrs, 0.5yr floor, 5% risk, also "almost
everything" rests on it).

Surprise: `step` auto-allocates your founder-hours into whatever is
running, up to what the project can absorb that year (some projects are
"rate limited" - e.g. scientific_method could only absorb 80 beans/yr even
though I had the cash and 2000 hours, so it spent 100% of hours but still
owed money for a second year). So there's no manual hour-allocation command
needed for a single project - step does it. Good, low-friction.

Further surprise: when I stepped with 3 things running at once, ALL THREE
completed in the same step (1501->1502), not staggered by their different
calendar floors (2y, 0y, 0.5y). I expected scientific_method (2-year floor)
to still be mid-build. Need to watch this - possibly the floor is a MINIMUM
across the whole build and completion this step was legitimate because
enough hours/money landed in one sitting to cross both the hour AND floor
gates at once; or the "calendar floor" really only binds if hours/money
*aren't* the bottleneck, and my lump of 2000 hours was enough to blow through
all of it in under a year once credit covered the cost. Going to keep an eye
on whether the stated "floor years" number is ever actually enforced as a
wait, or if it's more of a "minimum possible, but you basically never hit it
because money is usually the real constraint" flavour stat.

After that step: went into debt (-166.3 beans) because projects drew a
combined 435.2 beans that step and I didn't have it - the game auto-borrowed
on credit (credit limit 938.7, 17% used, 12% interest on arrears). This was
not surprising since `start units_standards` had pre-warned me with an exact
credit forecast ("you would borrow: 101.2, interest per year on it: 11.8")
before I committed - good, it told me the downside up front rather than
surprising me blind.

`ventures` command: shows concerns (ongoing businesses) you know how to run
but haven't opened. Both `scientific_method` and `units_standards` show
EARNS/YR: 0, COSTS/YR: 80 and 24 respectively, plus an "open" cost (100 and
53.3 beans). Given I'm already in debt, I have NOT opened either yet - not
obvious whether opening them helps unlock further tech (HOW MUCH RESTS ON
THIS talked about the knowledge itself existing, built) or whether
unlocking further prerequisites needs them open-and-running too. This is
genuinely unclear to me right now and I want to test it directly rather than
guess - will try advancing the tree without opening them first and see if
gated items stay gated.

`money`/`ledger`: current income is entirely "YOUR PRACTICE" -
`med_cataract_couching` (141.8/yr) and `med_trepanation` (56.9/yr) - which
the game says I never explicitly started; these must be freebies from the
114 "granted for free" technologies, run automatically as personal practice
income (it explicitly says "you did not open it and you cannot close it").
Interesting passive-income design: the founder does surgery on the side for
cash, at 1/3 the rate an organised concern would get for the same trade,
explicitly because it's "one person in a rented room" vs a real business.

Contradiction / bug candidate #1: `available` listed several "HEARD OF,
CANNOT BEGIN YET" items (e.g. `corpus_written`, `sc2_method_controlled_
experiment`) with the stated blocker "the state is wary of this... get at
least a local patron first: 'start patron_local'" - i.e. the UI is telling
me to type `start patron_local`. But both `why patron_local` and
`start patron_local` respond: "REFUSED: you have never heard of any such
thing." So the hint text references an action/id the engine currently
treats as unknown to me. Either `patron_local` needs its own prerequisite
that I also haven't been told about (and the advice text is jumping ahead
of the fog), or this is a genuine inconsistency between the advice shown in
`available` and what `start`/`why` will accept. I did not look at source to
find out - just noting it as something that confused me and cost a couple
of commands to confirm (maybe 2 minutes).

Next planned actions: figure out how to grow staff (I only have 1
scholar-equivalent and 1 artisan-equivalent, both "me"), since many
interesting "heard of" items are gated on having 2-3 trained craftsmen, and
check `labour`/`hire` to start building a household.

## Years 1502-1506: I ran myself into debt bondage. Here is exactly how.

`labour` command: shows household places (0 of 6 used), which trades exist
here and can be hired (artisan, carpenter, engraver, furnaceman, glassblower,
labourer, mason, master, merchant, millwright, miner, plumber, potter,
sailor, scholar, scribe, smith) vs which "must be taught" because they don't
exist yet (chemist, electrician, engineer, machinist, optician). Checked
`labour smith` and `labour scribe` - a smith costs 112 beans/yr, a scribe 125
beans/yr, and scribes additionally have a hard headcount ceiling (1.8 ever,
at any price, until literacy-raising techs like printing/schools raise it).

Bug/inconsistency #2 (the `patron_local` one, confirmed): opening
`scientific_method` and `units_standards` (paying more money I didn't have,
to "run" them) did NOT change the `available` list at all - the same
"HEARD OF, CANNOT BEGIN YET" items still said "the state is wary of this...
get at least a local patron first: 'start patron_local'" verbatim, and
`start patron_local` / `why patron_local` both still say "you have never
heard of any such thing." Then I looked at `why corpus_written` directly
(one of the blocked items) and its own STATUS block gives a DIFFERENT
rendering of the identical blocker: "get at least a local patron first:
'start something you have not heard of'". So there are two different hint
strings for the same blocking condition, and neither actually lets me act
on it: one names a concrete but nonexistent id (`patron_local`, which reads
like a hardcoded example/placeholder rather than a real tech id), the other
honestly admits the real prerequisite is still hidden under fog. This cost
me real time (several commands across ~10 minutes) chasing a dead end
before I concluded it's not solvable right now and moved on. I did not look
at source to check what patron_local "should" be - just reporting what the
game told me.

Mistake, fully owned: I opened `scientific_method` (100 beans/yr, 0 revenue)
and `units_standards` (30 beans/yr, 0 revenue) for no visible benefit (see
above - it didn't unlock anything I could detect), while ALSO starting
three new medical projects in the same turn (`med_herbal_pharmacy` 464
beans, `med_bone_setting` 7.4, `med_obstetric_practice` 15) and turning on
`auto_open`/`auto_hire`. That's five simultaneous financial commitments on
top of an already-negative balance (-166 beans going in). I did this
partly to test mechanics quickly rather than to play "well," but it is
exactly the kind of move a genuinely new player would make, since nothing
in the UI flagged "you are about to overextend" until it actually happened.

What followed, turn by turn:
- 1502->1503: net -168/yr. A message appeared: "THIS SOCIETY NOW HAS 1502:
  Reproducible length standard" - a nice touch, a historical/world-event
  ticker independent of my actions.
- 1503->1504: interest on arrears alone was 1.7 beans one step, climbing.
- 1504->1505: warning fired: "CLOSE TO THE LIMIT: you owe 867 of the 991
  anyone here will advance you (87%)... 'stop' a project, 'mothball' a
  loss-maker or 'fire' somebody while it is still your choice." This is a
  good, clear warning - it named the exact commands to use to save myself.
  I did react (mothballed both zero-revenue techs, saving 104/yr upkeep)
  but it was already too late: arrears interest (102/yr) alone outweighed
  the saving, and I even tried `work scribe 500` to raise quick cash, which
  the game explicitly told me afterward was a bad idea ("you earned 32, but
  the practice those hours were running was worth 50 - so this cost you
  18... wage work is for when you have no practice to lose"). I did this on
  purpose to see what `work` actually does, and the answer was: it always
  shows you the true opportunity-cost math it used, even when the math says
  you made a mistake. I appreciated that it didn't hide the bad outcome.
- 1505->1506: CREDIT EXHAUSTED. All three in-progress medical projects
  (`med_bone_setting`, `med_herbal_pharmacy`, `med_obstetric_practice`) were
  force-stopped unfinished (partial payment credited if I restart them
  later, it says). Then: "BONDAGE: you cannot pay, and you enter service
  for your debt. For about 8 years most of your hours belong to someone
  else. It is not the end: it is worked off, and then you are free again."

Current state (1506 AD): "IN DEBT BONDAGE: 7 years left owing 909.9 beans."
Founder-hours collapsed from 2,000/yr to 500/yr (the rest presumably goes to
the creditor). `available` now shows 0 startable things at all - not just
fewer, literally zero - and every previously-heard-of blocked item now
carries the same note: "nobody here will fund new work: your creditors were
left unpaid and the word is out. They will deal with you again in 1510,
and until then you may finish what is running, and pay for something out
of money you actually hold." My own leftover 0 beans on hand and +18.8/yr
recurring net (from the surgery practice alone, now that nothing else is
running) means I am slowly climbing out, but cannot start a single new
thing for at least 4 years (to 1510 for new credit) and am personally
bonded for 7 (to ~1513).

This is a genuinely severe, well-telegraphed-in-retrospect failure state,
and I want to flag it clearly for the people who made this:
- It is NOT a game over - the framing ("it is worked off, and then you are
  free again") is humane and historically apt for this civilisation's own
  institutions (debt servitude existed in Mexica society), and I respect
  that the game modelled a real economic consequence instead of just
  ending the run.
- BUT there was exactly one clear warning (the 87%-of-limit message at
  1504->1505) before the cliff, and by the time it appeared, the interest
  snowball was already unrecoverable with the tools I had (mothballing
  saved 104/yr against 102/yr of interest alone, before even touching
  living costs). A new player reading that warning message would
  reasonably think mothballing two loss-making techs was an adequate
  response to a "close to the limit" alert - it was not, and nothing told
  me it would not be enough. I would suggest either an earlier warning
  threshold, or the warning stating the actual shortfall number explicitly
  ("you need to cut at least X/yr, this only cuts Y/yr") rather than just
  naming the available commands.
- Separately: opening `scientific_method`/`units_standards` for no
  discernible benefit was money I should not have spent, and the game gave
  me a mechanically-identical warning at the time I opened them ("!! this
  costs more than it earns... that may be the right call for what it
  unlocks, but check 'why' if it is not what you meant") - so in fairness,
  the game DID warn me about that specific decision, clearly, at the
  moment I made it. I read past it because I was testing mechanics rather
  than playing cautiously. Owning that as my mistake, not the game's.

Next: since nothing is startable, I'll step through the bondage years and
see what happens - whether there's anything to do at all during bondage, or
whether it is purely "wait it out."

## 1506-1513: bondage, recovery, and fixing my mistakes

Bondage turned out to be purely "wait it out": every turn while bonded shows
`RUNNING: nothing`, `available` shows exactly 0 startable things, and
founder-hours are capped at 500/yr (down from 2,000) - presumably the other
1,500 belong to the creditor. The debt itself pays down on a fixed schedule
independent of my cash ledger (855.9 -> 801.9 -> 747.9 -> 693.9 -> 639.9,
about -54/yr) while my cash ledger runs its own small positive trickle
(+17 to +18/yr) from the surgery practice alone, which just accumulates as
savings - it does NOT appear to go toward the bondage debt directly; they
are two separate tracks. After exactly 7 steps (1506->1513) I got: "your
term is served and the debt is discharged; you are your own man again" -
full 2,000 hours restored instantly, zero residual debt. Clean, fair,
exactly as advertised up front. Reputation drifted down slowly the whole
time (11->9ish) for no stated reason during bondage - possibly a standing
decay-to-baseline mechanic, not confirmed.

Recovery strategy once free (1513 AD, 117 beans, +31.9/yr recurring): this
time I was deliberately conservative - started ONE thing at a time, let it
finish and open before starting the next, and avoided reopening the two
zero-revenue foundational techs. `available sort earns reverse` is a good
command for this - it reranks the whole startable list by revenue instead
of by "how much rests on it," which is exactly what I wanted once I was
rebuilding capital rather than chasing tech-tree depth. First pick:
`tex_rope_walk` (336.6 beans, 682-800/yr revenue, 60/yr upkeep, 10% risk) -
an excellent ROI. It worked: by 1517 (4 years later) recurring net had gone
from +31.9/yr to +415/yr, and cash from 117 to 390 (after also hiring one
scholar and one artisan along the way via `auto_hire`).

Bug/contradiction #3, confirmed and resolved: `why tex_rope_walk` required
`iron_bar_kg 10` as a material, and the project's STATUS was "CAN START
NOW" with prerequisites "all met." I started it anyway specifically to
test this, since the game's own opening briefing for this civilisation said
explicitly: "no iron anywhere in the hemisphere... That is not ignorance,
and no amount of teaching will fix it." It started and completed with no
complaint, no missing-material block, nothing. So the "no iron" framing in
the intro text is NOT actually enforced by the simulation underneath - at
least not for this item. This strongly confirms my earlier suspicion from
the "textiles" subject and `med_herbal_pharmacy`'s `olive_oil_kg`/`mat_linen`
prerequisites (olives and flax/linen are not Mesoamerican either): the
content (trade names, material ids, costs) looks like it is largely shared
across civilisations, generic/Old-World by default, while the flavour text
at the top is genuinely civ-specific. That is a real gap between what the
game TELLS you about this civilisation and what it actually SIMULATES, and
I think it is worth the developers' attention - either the Mexica playthrough
should not be able to requisition iron bar stock and olive oil at all, or
the opening text's "no iron, ever" claim should be softened to something
like "no iron INDUSTRY of your own," if importing small quantities via
trade is the intended reading. I did not check source to find out which is
intended - just reporting the observed contradiction from play.

Once `tex_rope_walk` was paying off, I pushed toward the fogged "ALL rests
on this" item from turn 1 (`identity_cover`, 1,264 beans) - started and
finished it in 1517-1518. The moment it finished, `patron_local` (which had
been an unreachable, nonexistent-to-the-engine id since turn 1 - see bug #2
above) appeared for real in the "MOST RESTS ON THESE" shortlist, at 960
beans, confidence C, "HOW MUCH RESTS ON THIS: almost everything." So bug #2
resolves cleanly in retrospect: `patron_local` genuinely exists and is
genuinely gated behind `identity_cover`; the bug was specifically that the
EARLIER hint text (in the `available`/`why` blocked-item listings) printed
the string "start patron_local" as if I could act on it right then, several
turns and in-game years before it actually became reachable. That is a real
UI bug under fog of war: the hint named a real, correct prerequisite id
before the fog should have allowed me to see that id at all. A more honest
message at that earlier point would have been the OTHER phrasing the game
itself used elsewhere for the identical situation ("get at least a local
patron first: 'start something you have not heard of'") - which is exactly
what `why corpus_written` showed me when I asked it directly instead of
reading the summary list. So the bug is really: two code paths render the
same "blocked on a fogged prerequisite" condition differently, and one of
them leaks the id early.

Built and opened `patron_local` in 1518-1519. Reputation up to 12,
protection up to 16% (this is the first time "protection" moved
meaningfully - I now suspect patron_local is what raises it). Immediately
on opening it, the "state is wary of this... get at least a local patron
first" items vanished from the blocked list entirely and were replaced by
more ordinary blockers (needs more craftsmen, needs `workshop_first`,
missing a newly-revealed prerequisite `arithmetic_positional`). So
patron_local really was the gate on the whole "sc2_method_*"/"corpus_written"
cluster, confirming it was worth chasing, eventually.

## 1519 AD: the clock I was told about on turn 1 went off exactly on time

`state`'s hazard line changed to: "HAPPENING NOW: Spanish invasion." This
is EXACTLY 19 years after arrival (1500->1519), matching the opening
briefing's "Nineteen years. Then ships, and then smallpox" to the year. I
want to flag this as a genuinely well-built piece of design: it was not a
vague "eventually" threat, it is a hard-scripted date that the intro text
told me about truthfully and the simulation then delivered on schedule.

`risk` at this point printed something I did not expect at all: a FULL
historical hazard timeline for Mexico running from 1519 all the way to
2024 - Old World epidemics (1520-1600, 80-100% staff loss), the colonial
order/encomienda system (1550-1700), the silver cycle and patio process
(1554-1810, explicitly flagged as "No damage fields: this is the opening"
and "the best environment this civilization offers a technologist between
the conquest and the twentieth century" - genuinely interesting, specific,
well-researched detail, e.g. naming Bartolome de Medina, 1554, Pachuca, and
Andres Manuel del Rio's 1801 vanadium discovery "nine years before anyone
in Europe"), the matlazahuatl epidemic of 1736, the Bourbon reforms, the
wars of independence (1810-1821, 7%/yr sack chance), the unstable republic
(1821-1867), the Porfiriato, the Revolution (1910-1920, 9%/yr), the Cristero
war, the Mexican miracle, the 1985 Mexico City earthquake (12% that single
year), the debt crisis, NAFTA, the 2006-2024 drug war (2%/yr), and the 2017
Puebla earthquake. This is an enormous amount of real, specific historical
research packed into hazard flavour text, and it surprised me - I had not
expected the game to model the ENTIRE subsequent history of the region as a
sequence of hazard windows with dates, percentages and "what would help"
mitigation hints (walls/firearms/powerful friends/copies of your work kept
elsewhere, for the conquest; clean water/quarantine/inoculation for the
epidemics). This is a good surprise and probably the single most impressive
thing I've seen the game do so far.

The Spanish invasion itself: 90%/yr for a 3-year window, "sack chance after
what you have built: 90%" (my one piece of protection, 30% after
patron_local, barely dented it), "you take 100% of it." I could not do
anything meaningful to stop it in the single year I had before it started
resolving - no realistic wall/firearms/ally tech was in reach. I stepped
through it anyway to see what happens:
  - 1519: "a site is sacked - you had nothing it could take" (no loss,
    since my 3 at-risk technologies apparently weren't stored somewhere
    vulnerable, or I got lucky on the 80%-chance-to-actually-lose-something
    roll) - BUT society values permanently shifted: w_magic_fear 0.32,
    w_novelty -0.29, w_religious_rigidity 1.00 (maxed). The flavour text
    had explained why in advance: Franciscan/Dominican friars beginning
    "systematic campaigns against indigenous ritual," a colonial
    administration "far less willing... to read an inexplicable effect as
    divine favour rather than diabolism or sorcery to be extirpated."
  - 1520: sacked again, again "you had nothing it could take."
  - 1521: the epidemic window (1520-1600) is now also HAPPENING NOW
    alongside the invasion. Still alive, staff intact, money recovering
    (net +308.7/yr). Continuing to play through this rather than stopping
    to study it further.

Nothing about this felt unfair given the up-front warning; if anything I
was relieved the sack rolls found "nothing to take" both times - I assume
that is because my actual built technologies are not literally stored at a
"site" that can be physically sacked the way the flavour text implies, or
because the 80% chance is itself a further roll I passed. I did not look
into which.

## 1521-1546: math, `arithmetic_positional`, and the labour-supply ceiling

`why arithmetic_positional` opened with "Highest return on personal hours
in the entire tree" - the strongest hint text I'd seen yet, so I built it
immediately (720 beans). First encounter with a labour-SUPPLY cap, distinct
from money: "this society cannot supply the labour it wants and it will
crawl until you can: scribe (wants 2500 hours a year; this society can
field 673 at most)." So a project can be money-rich and still crawl for
years because the whole city only has ~673 scribe-hours/yr to sell you, no
matter how much I pay. It finished anyway (3 years later than its 1-year
floor) because "% of your hours spent" grinds up slowly against that hard
ceiling. Good, consistent mechanic - just slower than the sticker price
suggested, and worth remembering that "CALENDAR FLOOR" really is a floor,
not an estimate, whenever the demanded trade-hours exceed the town's supply.

During this project, the Spanish invasion resolved with one real loss this
time: "a site is sacked - 1 project back to the beginning" (I did not
manage to work out which project that referred to - `geometry_analytic`
hadn't started yet, `arithmetic_positional` didn't visibly reset). Society
values kept sliding: `w_religious_rigidity` past 1.0 by the second sacking.

Then the epidemic (1520-1600 window) started landing hard, and its REAL
mechanic became clear over several turns: it is not a one-off money hit,
it is a recurring "staff -80%" roll that can fire more than once across the
80-year window, and it visibly nukes whatever craftsmen/scholars I have
just hired back down to a fraction of a person (`EMPLOY` dropping from 1-2
people to 0.2 in a single step, repeatedly). One instance even reported an
explicit cash cost tied to it: "368 gone with the trade that stopped," so
losing a staffed trade mid-production can waste the money already put into
that year's production, not just the labour. This made me understand
something the intro text undersold slightly: the "no immunity" hazard does
not just threaten the FOUNDER (I don't age or catch anything, apparently -
every single "you had nothing it could take" or "-80% staff" message never
touched me personally) - it is a permanent tax on HIRING for the better
part of a century, because every hire I make is a Nahua person who can be
struck down again the next epidemic wave. That's a sharp, unstated design
implication I had to work out by watching it happen several times, not
something the game told me directly - worth flagging as something that
took real observation to piece together (maybe 20-30 minutes of watching
repeated hire/lose cycles) rather than being explained anywhere I found.

Recovered by building `statistics_basic` (failed once, retried, "40% of the
hours are to do again... 42 is gone... next attempt's chance of failing
this way is 8%, down from the 10%" - a clean, fair, well-explained failure
mechanic: partial credit, and the game explicitly reduces future risk based
on what you learned from the failure) and `algebra_symbolic`. Also
discovered a THIRD systemic shock, separate from epidemics and invasion: my
patron (from `patron_local`) can simply die of old age and needs "courting
afresh" for real money (640 beans) plus a temporary protection/scandal hit
- this happened twice across the run (1522, 1557) and both times caught me
by surprise mid-recovery from something else. I don't yet know if this is
avoidable or just a recurring cost of having a patron at all; I did not
look into it further, just paid it both times.

Built `world_map` (`identity_cover` was its prerequisite) as a second,
diversified income stream once I noticed `tex_rope_walk`'s own revenue was
sagging: the game explicitly names a "market saturation" mechanic - "1
concern selling into a market that has moved since it opened: tex_rope_walk
is at 73% of the tree's own figure, because supply of what it makes has
grown since it opened... opening ANOTHER concern in a category you are
already saturating makes this worse, not better, while a concern in a
category you do not yet run keeps the tree's own figure." That's a
genuinely good piece of economic modelling and it directly steered my
choice of `world_map` (a different subject, "information," not "textiles")
over doubling down on more textile concerns. I worked this out from the
ledger text itself, not by guessing.

By 1546 I had 13 of my own technologies (128 total with grants), 15 of 168
nodes toward the transistor goal, and a comfortable positive recurring
income again (~+260 to +680/yr depending on the epidemic's current bite).

## 1546-1564: `workshop_first`, the second bondage, and the sharpest lesson of the run

`workshop_first` ("First workshop and laboratory... a walled yard, a
separate furnace shed downwind, and a door onto the street so that
witnesses can see you are not conjuring" - lovely period detail) was
flagged "HOW MUCH RESTS ON THIS: almost everything" and cost 4,606 beans,
the single largest commitment of the run so far, with a hefty 900/yr
upkeep once opened. I hired 2 artisans and started it the same turn
(learning from the epidemic-attrition problem: hire and commit before the
next wave, not after). It absorbed 3,320 beans in one step and put me
60-90% into my credit limit for the next 13 IN-GAME YEARS (1550-1563) of
slow grinding, repeatedly hitting "in arrears: after fixed costs there is
nothing left to draw on, so the hours offered this year did almost
nothing" even while my recurring net stayed POSITIVE the whole time
(+113 to +227/yr). This taught me something the ledger doesn't say in so
many words: a project's yearly "instalment" appears to be funded out of
that year's actual cash SURPLUS after fixed costs, evaluated from a
still-deeply-negative running balance - being recurring-net-positive is not
enough to make progress if your ABSOLUTE cash position is still very
negative; you need the underlying debt itself to shrink close to zero
before big projects can resume drawing meaningfully. `portfolio` confirmed
this starkly: "500 offered, 0 effective, of 500 hrs total to go... waiting
on: your hours" for TURN AFTER TURN despite having the full 2,000 hours
free and a positive income - the real bottleneck was invisible from the
hours side entirely.

Then, after 14 in-game years of grinding, at 98% of hours spent and only
2.3 beans still owed - essentially finished - `workshop_first` ROLLED ITS
8% FAILURE CHANCE AND FAILED. "40% of the hours are to do again (200 of
your own) and 1,842 is gone." This is the single sharpest lesson of the
whole run: the stated failure-risk percentage is a real, live risk against
the FULL committed cost, checked at (or near) completion, not a risk that
tapers off as progress accumulates. Being at 98% done bought me nothing;
the dice still had teeth. Losing 1,842 beans in one shot, on top of an
already-strained balance, blew straight through the credit limit and
triggered a SECOND debt bondage: "IN DEBT BONDAGE: 7 years left owing 3,585
beans," hours cut from 2,000/yr to 500/yr again.

I want to be very fair to the game here: nothing about this was hidden.
`why workshop_first` told me plainly, before I ever started it, "FAILURE
RISK: 8%" and "IF IT FAILS: 1,842 gone... It can fail more than once." I
read that number, judged 8% as good enough odds given how much rested on
the project, and it simply came up on the wrong side once. That is
legitimate risk, honestly priced and honestly disclosed - I lost a real bet
I chose to take, at good odds, and the consequence (bondage, not game
over) was exactly what the game told me such a consequence would be back
in 1506. I don't think this is a flaw. I think it is the sharpest, most
memorable teaching moment of the run precisely BECAUSE it is fair: a
95%+-complete flagship project that still had a live chance of eating
almost half its cost and setting me back years, is a genuinely different
feeling from a normal "roll at the start" risk model, and I would tell the
developers this is worth keeping exactly as it is - it is a good design,
not a bug, and it is the single moment that most changed how I think about
this game's risk. What I WOULD suggest: somewhere in `why`'s output, make
explicit that the stated failure risk applies to the WHOLE project, checked
once near completion, rather than leaving the player to infer that (I had
assumed, wrongly, that an 8% risk meant something more like "8% chance per
year of a setback," and was still surprised when it detonated as one
lump-sum event at 98% done). A single added sentence would have cost me
nothing to learn and saved the surprise without diluting the sting.

Current state (1564 AD): in bondage again, 500 hours/yr, 7 years to go
(to ~1571), 13 of my own technologies built, 15/168 nodes toward the goal.
Continuing to play through this.

## 1564-1580: a correction to my own earlier note, a real self-inflicted deadlock, and a third bondage

Second bondage discharged cleanly again in 1570 ("your term is served and
the debt is discharged; you are your own man again"), same as the first -
consistent, trustworthy mechanic. By 1571 I had 692 cash and a positive
income base, and restarted `workshop_first`: since 4,606 beans were
already sunk into it before the earlier failure, `why` told me plainly
"'start' would actually charge 0 beans, not the total above" and the
failure risk had dropped from 8% to 6% ("What went wrong last time is not
lost on the people who will try again"). Hired 2 artisans, restarted it,
and it finished in ONE step this time, clean. Good, fair mechanic: a
failed project is not fully wasted, it comes back cheaper and safer on
retry, which softens the sting of the earlier 98%-done failure
considerably in hindsight.

`workshop_first` unlocked a large new tier (300 startable items, up from
290) including three more "ALL rests on this" items:
`refractory_fireclay`, `case_hardening`, `crank_conrod`. It also raised my
household-places ceiling from 6.0 to 12.1 in one shot - a visible, large
structural unlock, not just a gate for one or two techs.

SELF-CORRECTION on an earlier note: I had written above that "no iron" in
the Mexica intro text looked unenforced because `tex_rope_walk` used
`iron_bar_kg` at a flat x1 civ multiplier. `why case_hardening` (a
metallurgy/ironworking tech) showed a civ multiplier of x1.76 - the
highest I've seen anywhere in this run, on a project that is centrally
ABOUT iron ("Smiths already do all of this in any developed ironworking
tradition..."). So the game DOES apply civilisation-specific cost
penalties to iron/metallurgy work for the Mexica - it is just not a hard
block, it is a heavy tax (76% over baseline), which is arguably a MORE
elegant way to represent "no iron industry of your own, so doing this
requires expensive imported materials and improvised technique" than an
outright refusal would be. I want to flag this as me getting it partly
wrong earlier: the "no iron, and no amount of teaching will fix it" claim
from the 1500 AD opening text is, on reflection, consistent with what I've
now seen - the multiplier system IS where that constraint lives, I just
hadn't found a big enough example of it yet when I wrote the first note.
I'm leaving the earlier note as written (mistakes are the point of this
log) but flagging the correction here rather than editing it away.

Started `case_hardening` (2,246 beans, 12% risk, "925-2,000/yr" revenue).
It failed TWICE in a row before finishing (the log showed "Attempt 2" and
then "Attempt 3" across two separate failure events, so it must have
failed once even before the one I caught in my own reading) - a real run
of bad luck against a stated 12%-then-9%-then-7% risk ladder, costing
898.5 + 510 beans (roughly 1,400 beans) in wasted spend on top of the
2,246 already committed, on a project I had budgeted carefully for. This
pushed me deep into debt again (-3,150ish) purely from bad rolls on a
project I managed well going in - a good reminder that the risk system is
not just a beginner's tax, it can bite a careful player too, repeatedly,
even late in a run with 15 technologies already under my belt.

It DID finish on the third attempt (1577), 15 technologies built, 17/168
nodes toward the goal - real progress. But then I ran into the single most
interesting PUZZLE of the whole session, and I want to record it in full
because I never solved it:

`case_hardening` was quoted, once built, as earning "1,500 a year against
400 of upkeep" (later shown in `ventures` as 921.7 net-of-market vs 320
upkeep) - by far my best single concern. `open case_hardening` refused:
"nobody free to keep an eye on it: it needs 0.00 scholars and 1.00
craftsmen to supervise, and you have 0.50 and 0.12 not already watching
something else." I am my own only craftsman (1.0 total), and `ventures`
showed my craftsman-time already split across `tex_rope_walk` (0.53) and
`world_map` (0.33), leaving 0.12 free of the 1.00 that `case_hardening`
needed ALONE. I tried to free capacity by mothballing both `tex_rope_walk`
and `world_map` (sacrificing 663.9 beans/yr of my two best-established
earners) - that got me to 0.99 free craftsmen. Still refused: short by
0.01. I looked for the source of that last 0.01 and found it:
`med_obstetric_practice` holds 0.01 craftsman-worth of supervision
(visible in `ventures`'s "HELD BY" table). I tried `mothball
med_obstetric_practice` to release it - REFUSED: "that costs nothing to
keep; there is nothing to save" (it has 0 upkeep, so the engine apparently
treats "mothballable" as "has a nonzero money upkeep to save," even though
the SAME concern visibly occupies a nonzero, nonzero-consequence STAFF
allocation that `open` elsewhere treats as a real, blocking resource). I
could not find any other way to shed that 0.01: no partial-mothball, no
"release staff without closing" command, nothing in `help commands` that
fit. The only path I can see now would be hiring a genuine second
craftsman, which needs cash I did not have (deep in debt already).

I want to flag this clearly as "something I wanted to do and could not
work out how to do, and I don't think it was my own oversight": a
fully-built, extremely valuable concern was rendered permanently
unopenable by a 0.01 shortfall in a resource (craftsman-supervision-time)
that the game will not let me free from the one place it is trapped,
because the freeing tool (`mothball`) is gated on a DIFFERENT resource
(money upkeep) than the one actually blocking me (staff-time). If this is
intended, I could not find the intended solution to it from inside the
game; if it is not intended, it is a real inconsistency between what
`ventures`/`open` count as "staff committed" and what `mothball` counts as
"worth freeing."

Compounding the mistake: having failed to open `case_hardening`, I then
tried to undo my mothballing of `tex_rope_walk` and `world_map` to at
least get their income back - and discovered `restore` is NOT free either
("restored: tex_rope_walk back in service for 120 in cacao beans" /
"world_map... for 100"), so my attempted recovery cost me 220 more beans
I did not have, on top of already being at 100% of my credit limit by
that point. This pushed me over, and 1579 ended in a THIRD debt bondage:
"7 years left owing 3,620 beans," hours cut to 500/yr again.

I am ending active play here, at 1580 AD, having gone through this exact
boom -> big commitment -> debt -> (sometimes) failure -> bondage -> clean
discharge -> boom cycle three full times across 80 in-game years. I think
that repetition is itself the finding: this is not a beginner's mistake I
made once and then avoided - it is a structural rhythm the economy
produces even when I was actively managing it (checking `money`/`ventures`
every turn, reacting to "CLOSE TO THE LIMIT" warnings, diversifying income
by subject to avoid market saturation, retrying failed projects at reduced
risk). Bondage itself is well-designed and never felt unfair or terminal -
it discharges cleanly and completely every time, exactly as promised at
game setup. What I'd tell the developers: the REPEATABILITY of the
cycle, even for an attentive player, might be intentional ("this is what
building anything ambitious pre-industrially actually costs, and the
founder is not supposed to escape that rhythm early") - if so, it is
working as designed and is a genuinely interesting statement for the game
to make. But if the intent is that a careful player should be able to
graduate out of the boom-bust cycle permanently after a certain point,
something is currently stopping that: my income base by 1579 (before the
final mothball mistake) was 803.5/yr against costs of roughly 950-1150/yr,
i.e. STRUCTURALLY negative even before any new project spending, driven
mostly by the standing upkeep of "capability" unlocks (`identity_cover`
160/yr, `patron_local` 160/yr, `workshop_first` 720/yr - together 1,040/yr
just to keep the tech tree open, regardless of whether I run any
production concern at all) plus interest on whatever debt is already
outstanding. That fixed capability-upkeep total is worth a second look: it
means the "ALL rests on this" unlocks that the game explicitly steers you
toward are also, cumulatively, the single largest fixed drain on the
economy, and I never found a way to reduce it once paid.

FINAL STATE: 1580 AD, in bondage (7 years left, releasing ~1587), 15 of my
own technologies built (130 total with the 115 free grants), 17 of the 168
nodes needed for the Grown and alloy junction transistors goal, reputation
8, protection 29%, several hazard windows still open (epidemics through
1600, the colonial order through 1700, the silver cycle through 1810).
