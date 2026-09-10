# PLAY_A — naive playthrough (Rome, 100 AD, fog ON, poor scholar, founder not ageing)

## Setup

Opening screen offers 5 settings. Picking (2) Roman Empire under Trajan, 100.

**Expectation before starting:** This is a "modern knowledge in an ancient world"
sim. I expect to have some kind of tech tree gated by money, time, labour and
materials; the flavour text ("Knowing how a thing works is free. Building it is
not") says the challenge is the *build*, not the *idea*. Rome's blurb warns about
slavery + elite contempt for manual work, so I expect social/status friction to
be a real mechanic, not decoration.

## Year 100 — orientation

Goal revealed by `help`: **build a point-contact transistor before 600 AD**. 500
years, founder immortal. That reframes everything: this is not "survive Rome",
it is "bootstrap a semiconductor industry across five centuries".

State at start: 400 den, 2000 founder-hours/yr, rep 5, scandal 0, eminence 0,
137 technologies "granted for free" (i.e. what Rome already has), 0 built by me.
Net income +3.5 den/yr — basically nothing.

`available` says **207 startable now**, grouped by subject. Textiles is the
biggest bucket (54!) which surprised me — I expected metallurgy/glass to
dominate a road to a transistor. My guess: textiles is a cheap early *income*
ladder, not a tech path.

The game flags "MOST RESTS ON THESE": identity_cover (1580), units_standards
(444), arithmetic_positional (1032), scientific_method (230), horse_collar (709).
Only scientific_method is affordable at 400 den.

**Expectations before I commit:**
- `identity_cover` — "Establish a respectable..." at 1580 den and marked RESTS:ALL.
  I expect this is the social-legitimacy gate: in Rome a nobody who tinkers is
  suspect, so I probably cannot hire/patronise/publish without it. Likely a hard
  prerequisite for most of the tree. Expensive relative to my purse.
- `units_standards` — measurement. The intro said the missing things are
  *instruments*: temperature, tolerance, vacuum, purity. So standards feels like
  the true root.
- `scientific_method` — 230 den, 350 hr, 2 yrs, cheapest of the "big" ones and
  affordable. I expect it multiplies research success / lowers risk on everything
  after.
- `horse_collar` — earns 900/yr for 709 cost. That looks like the money engine,
  and risk says it also blunts the Antonine plague (?!) which I did not expect —
  a horse collar helping against plague reads odd. Guess: it stands in for
  transport/food supply, so staff survive better.
- "the briefing" (600 den, 1 item) — I expect this is a meta/tutorial item that
  explains the win condition. Checking it first.

### The economics I worked out in year 100

`work scholar 100` earned 32 den — so my own time is worth ~0.32 den/hr, or
640 den for a whole year of my 2000 hours. `money` showed I already have
221.9 den/yr revenue from two *granted* medical techs (cataract couching,
trepanation) against 229.8 den/yr of "living and appearances". So doing nothing
is roughly break-even, and my labour is the only free resource I have.

Dumping `available all` and sorting by EARNS/YR is the single most useful thing
I did. Findings:

- The 54 textile `tx2_*` items cost 6-10 den but carry **40 den/yr upkeep and
  zero revenue**. That is a trap for anyone who buys cheap things because they
  are cheap. (Mitigated by `open`: help says a thing "earns nothing and costs
  nothing" until opened, so I think upkeep is opt-in. I have not verified.)
- Best returns available with no staff:
  - tex_horizontal_loom 225.8 den / 80 hr / 0.5 yr / 10% → 400 earn, 30 upkeep
  - tex_indigo 187.8 den / 60 hr / 0.4 yr / 10% → 300 earn, 40 upkeep
- Better still but blocked: tr_hopper_wagon (266 den → 600/yr!) and
  horse_collar (709 → 900/yr) both need **1 artisan on staff**, which I don't
  have. `available` does not show the staff requirement in its table — you only
  find it in `why`. That cost me a plan.

**Expectation:** start loom + indigo this year (413 of my 432 den, 140 of my
1900 hours), step a year or two, and come out with ~650 den/yr net revenue,
which then funds an artisan, then the hopper wagon, then horse_collar. I expect
the "MOST RESTS ON THESE" foundations (units_standards, scientific_method,
identity_cover) to be affordable by ~year 105 rather than now.

### 100-102: the money loop, and two surprises

Both projects finished in one step. Two things I did not expect:

1. **Completing a project does not make it earn.** You get a separate `open`
   step with its own fee (33.9 and 40 den). The game *did* tell me, in the event
   line and in `ventures`, and the phrasing ("Knowing how to do a thing and
   running it are different") is the clearest bit of teaching so far. Good
   mechanic — it makes the 40 den/yr textile upkeep trap harmless unless you
   actually open the thing.
2. **Listed revenue is not delivered revenue.** The loom advertised 400/yr and
   actually contributes 266.7; indigo advertised 300, delivers 200. Both are
   exactly 2/3. Meanwhile my granted med_cataract_couching income *fell* from
   158.3 to 141.7 when I opened new ventures. I read this as a market-saturation
   or share-of-attention effect. Nothing in the UI explains it and `why` doesn't
   mention it. This is my first real "the game is telling me something and I
   can't tell what" moment.

Also: **scandal jumped from 0 to 6.0** the year I built two things, with no
message saying why. Reputation went 5 → 8.8 at the same time. I assume building
visibly draws notice, but I had to infer it.

Discovery that reshapes my whole plan: **unused founder-hours are lost, and
`work scholar` converts them to cash at ~0.33 den/hr.** 2000 hours = ~650 den/yr,
which is more than my entire venture income. So the correct loop is: spend hours
on projects first, dump every leftover hour into `work`. I will do this every
year from now on.

Wages: artisan 250/yr, carpenter 250, smith 281, scribe 312, merchant 394,
master 500, scholar 625.

**Next expectation:** hire 1 artisan (250/yr) to unlock tr_hopper_wagon
(266 den → 600/yr listed, so ~400 real) and later horse_collar. I expect one
artisan to satisfy the "1 artisan" requirement of many projects at once, not to
be consumed per project.

### 103-107: compounding, failures, and staff as a hidden ceiling

Working the loop (start what I can afford → dump leftover hours into
`work scholar` → `step 1`) took me from 400 den to ~2,000 den/turn throughput by
107. Built by 107: horizontal loom, indigo, hopper wagon, units_standards,
horse_collar, scientific_method, arithmetic_positional (7 of my own).

Things that surprised me:

- **Projects fail and auto-retry.** scientific_method failed once (20% risk),
  identity_cover failed once (5% risk, and it ate 632 den). The message is clear
  and the retry is automatic, which is merciful. But a 5% risk costing 632 den
  is a big variance spike for an early player; I lost about a third of a year's
  income to one roll.
- **`open` costs money too**, roughly a year of upkeep, and some things earn
  literally nothing and only cost: units_standards is 0 earn / 30 upkeep,
  scientific_method 0 earn / 100 upkeep. I opened them anyway on the theory that
  a foundation must be *running* to count as a prerequisite. **I do not actually
  know whether that is true** — nothing in the game says whether a prerequisite
  must be built or built-and-open. That is the biggest piece of missing
  information so far.
- **Staff is the real ceiling, and it is invisible until you look.** `ventures`
  has a line "free to put behind something new: 1 scholars, 0.40 craftsmen".
  Running concerns *consume* craftsmen continuously (horse_collar 1, hopper
  wagon 1). With 0.84 artisans and 2 craftsman-slots already committed I am
  oversubscribed and did not notice for two turns. `state` shows headcount but
  not commitment; only `ventures` shows commitment.
- **Staff decays.** 1 artisan hired became 0.96, then 0.93, 0.87, 0.84 — 3.5%/yr
  attrition. The explanation of fractional FTEs is one of the better bits of
  writing in the game, but it means "hire 1" is really "hire 1 and top up
  forever".

### 108-112: the tree opens, and I overspend

Finishing the four foundations (units_standards, scientific_method,
arithmetic_positional, identity_cover) jumped `available` from 205 to 264 to 279.
That is the clearest signal in the game that the "MOST RESTS ON THESE" hint is
real, and it paid off exactly as advertised.

Newly visible gates, and they are good ones:
- **`patron_local`** (1,200 den). A whole family of agricultural and tool items
  was listed as "the state is wary of this (state interest -0.6); get at least a
  local patron first". So political cover is a literal prerequisite class, not
  flavour. I like this a lot — it is the Rome blurb ("an elite that despises
  manual work") turned into a mechanic.
- **`atomic_theory`** — "needs 2 trained scholars, you have 1.0 (you are one of
  them)". The game then *told me how to fix it*: hire scholar 2, or build
  school_founded. That is the single most helpful error message I have seen.

Mistake I made: I hired 2 scholars (625/yr each) at the same time as starting a
1,200 den project, and went from +900/yr to **-710/yr and 886 den in debt** in
one turn. The game let me, warned me nowhere, and charged 11% on arrears. In
fairness `money` shows it plainly; I just did not look before committing.

I dug out with shipbuilding: rope walk, mast stepping, caulking, carvel and
clinker planking — all cheap (200-670 den), all 300-900 den/yr. Revenue went
2,725 → 4,511/yr, net +1,474/yr.

**Expectation vs reality on upkeep:** I now think opening a zero-revenue
foundation is a mistake. `why identity_cover` shows STATUS: DONE, and prereqs
elsewhere are phrased as "missing prerequisites", never "not opened". So DONE is
almost certainly what counts, and the 100/yr I pay to keep scientific_method
"running" is probably wasted. The game never says either way. I am leaving
identity_cover, patron_local, algebra and statistics **unopened** on that theory.

Also noticed: **`auto_open` did not fire while I was in arrears.** Sensible, but
undocumented — the policy text says it opens "concerns that plainly pay for
themselves" with no mention that being broke disables it.

**Annoyance:** every single `available` call reprints the entire "HEARD OF,
CANNOT BEGIN YET" list — 25+ lines, identical each time, even when I asked for
one subject with 2 items in it. It buries the answer to the question I asked.

### 115-120: the two institution gates

Two hard ceilings appeared, both stated as refusals rather than in any list:

1. `hire artisan 6` → "you can supervise, house and teach 1.49 more people, not
   6 ... build workshop_first (you need somewhere for them to work)". So there is
   a **housing/supervision cap on headcount** and `workshop_first` (5,757 den,
   RESTS: ALL, prereq patron_local) lifts it.
2. `open tr_carvel_planking` → "nobody free to keep an eye on it: it needs 0.0
   scholars and 0.8 craftsmen to supervise". **Running concerns permanently tie
   up craftsmen.** With 13 concerns running I now need a standing workforce just
   to keep the lights on, quite separate from building anything.

Both refusals name the exact fix. That is good design — I was never stuck
without knowing why.

`why school_founded` is the most emphatic text in the game: "The pivot of the
entire game... Every year of delay here costs more than any single technology...
Grants +4 scholars and +2 scholars/yr thereafter." And then: **STATUS BLOCKED,
"this needs 2 other things you have not heard of yet"**. Under fog I cannot find
out what they are. So the game shouts "do this first, delay is the worst
mistake" about a thing it will not let me start or plan toward. That is the most
frustrating moment so far, and I think it is a genuine design tension between
the fog and the advice.

Also: **auto_mothball silently closed horse_collar** when craftsmen ran short. I
lost 900/yr for two turns before I noticed in `ventures`. No event line said so.

By 120: 18 techs, 13 concerns, revenue ~11,700/yr, net **+6,572/yr**, 7.6 staff.
The economy is solved. From here the question is purely the tech road.

**Expectation for the technical push:** the intro named four missing
instruments — temperature, tolerance, vacuum, purity. The RESTS:ALL items now
visible are case_hardening, refractory_fireclay (heat), crank_conrod (power),
plus lens_grinding marked "much". I expect refractory_fireclay to be the
temperature gate, the prc_* lathe items (straightedge, mandrel, tailstock) to be
the tolerance gate, and lens_grinding + a pump to lead to vacuum. Starting all
four RESTS-heavy ones now.

### 120-130: the instrument ladder appears, and hours become the bottleneck

Once `workshop_first` + `patron_local` were done the tree opened enormously:
279 → 352 → 414 startable. And the fog started naming the actual road:

    glass_clear        <- cap_heat_1100
    mirror_amalgam     <- glass_clear
    drawplate_wire     <- case_hardening
    crude_cell         <- lead_metallurgy
    opt_focal_length   <- opt_plano_convex_lens

`cap_heat_1100` ("Sustained 1100 C, hand-blown charcoal", RESTS: ALL) cost 300
den and 60 hours. That is the temperature instrument from the opening briefing,
and it is *cheap* — the expensive thing was the 20 years of institution-building
needed before the game would show it to me. I think that is the intended lesson
and it landed.

**The bottleneck flipped.** Money went from binding to irrelevant (47,901 den
banked, +13,818/yr by 130). The constraint is now my own 2,000 founder-hours a
year, and everything that matters is hour-hungry: atomic_theory 1,000 hours,
precision_three_plate 500, glass_clear 400, and each trained trade costs ~450
hours per person. I stopped using `work` entirely around year 122; before that it
was the best thing to do with spare hours, after that it was the worst.

`bounty charcoal_industrial` → "needs about 122,400 denarii" for a 48,960 den
project. So a bounty is ~2.5x the cash price and (I assume) costs no founder
hours. That is exactly the escape valve for an hour-starved late game, and I
expect to lean on it. The game does not say anywhere that this is the trade;
I had to try it and read the refusal.

Trades that must be taught: engineer, machinist, optician (done), chemist,
electrician (outstanding). `policy auto_train on` now handles this and removed a
lot of tedium — I wish I had found it 20 years earlier.

By 130: 30 techs of my own, 19 concerns running, 17 staff across 5 trades,
+13,818 den/yr. Built the four RESTS:ALL items — precision_three_plate,
water_power_scale, glass_clear, cementation_steel.

