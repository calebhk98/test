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

