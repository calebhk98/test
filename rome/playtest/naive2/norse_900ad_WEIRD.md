# Playtest notes — norse_900ad, deliberately WEIRD play

Session file: /home/user/test/rome/playtest/naive2/norse_900ad_WEIRD.json
Started: 2026-09-10

## My brief to myself
Play badly on purpose. Definition of "strange" I'm adopting:
1. Do the opposite of the obvious (starve the food supply, over-invest in one useless thing).
2. Push numbers to extremes (allocate 100% of everything to one task, allocate 0 to survival).
3. Try inputs the parser probably didn't expect (nonsense commands, negative numbers, huge numbers, unicode).
4. Do anachronistic / impossible things (build a railroad in 900 AD).
5. Repeat the same action many times to see if anything degenerates.
6. Never do the "sensible" thing (no raiding as Norse, no farming, no defence).

## Log

### Setup

`--session` really does resume: the process can exit between every command and the
game picks up where it left off. Convenient. (First run prints a long `welcome`
blob; resumed runs print nothing but the reply.)

Opening position, year 900, Scandinavia:
- capital 400.0 **denarii** (in Viking-age Norway. Not silver marks, not ore/penningar — denarii.)
- revenue 232.7/yr, living cost 230.0/yr, net +2.8/yr
- `where_the_money_comes_from`: `med_cataract_couching` 166.7 and `med_trepanation` 66.7.
  So the way this character eats is by **couching cataracts and trepanning skulls**
  as a jobbing surgeon among the Norse. Nobody told me I was doing this; it is just
  how the income line is composed.
- done_count 132, all "granted" (things this society already knows).

### First thing that looked wrong: the `available` list at 900 AD

86 things I can start on day one. Some of them:

| id | cost | what |
|---|---|---|
| `mil_plate_armour_firearms` | 383.6 | **"Plate armour against firearms"** — in 900 AD. Firearms do not exist. This is available on turn one, cheap, 1 year, 1% failure. |
| `air_observation_balloon_tethered` | 3372.8 | A **tethered observation balloon**, startable in 900 AD, 0.5 years, 10% failure. No hydrogen, no rubberised silk, no prerequisite. |
| `fud_chinampa` | 2520.0 | **Aztec chinampas** (floating raised beds on a lake) in Norway. |
| `ag2_guano` | 388.1 | **Guano** as a fertiliser. Peruvian seabird islands, from Scandinavia, 0 years. |
| `tex_hand_ginning` | 100.1 | Hand-ginning **cotton**, in Scandinavia. |
| `fin_annona`, `fin_argentarii`, `fin_collegium`, `fin_societas`, `hom_cosmetics_roman`, `civ_arch_roman` | **0.0** | Roman institutions — the grain dole, Roman deposit bankers, collegia, Roman cosmetics — all cost **zero money, zero hours, zero years** for a Norse player. Free clicks. |

The zero-cost Roman items in particular feel like the Rome-100AD content leaking into
the Norse start; "Annona grain dole and administration" is not a thing a man in
Scandinavia in 900 acquires for free.

---

## Run 1 — accidentally destroyed by one command (year 900 -> 1400 in one line)

### Parser abuse round
```
{"cmd":"eat_the_king"}                       -> ok:false "unknown cmd 'eat_the_king'. use one of:
                                                 state, available, why, path, start, stop, bounty,
                                                 buy, step, quit"
{"cmd":"start","id":"transistor"}            -> ok:false "unknown node id 'transistor'"
{"cmd":"start"}                              -> ok:false "unknown node id None"
{"cmd":"buy","what":"slaves","n":-50}        -> ok:false "n must be greater than zero, got -50."
{"cmd":"buy","what":"forest","n":-1000000}   -> ok:false "n must be greater than zero, got -1e+06."
{"cmd":"step","years":-5}                    -> ok:false "years must be >= 1"
```
All handled gracefully, no tracebacks. **But:** the "unknown cmd" error lists only
10 commands, while the welcome screen lists 24 (hire, fire, train, commission, work,
labour, mothball, restore, bribe, policy, save, load, help are all real and all
missing from that list). A player who only ever saw the error message would not know
half the game exists.

`{"cmd":"buy","what":"slaves","n":100000000}` gave my favourite error of the session:

> "cannot afford 100000000 slaves: 22246676391156112 denarii (222466764 each after
> the market moves against a purchase this size) and you have 400"

I like that the price per head moved from ~40 to 222 million because I tried to buy
a hundred million people. Nice touch, absurd number, correctly refused.

### Then I killed the game with one integer

```
{"cmd":"step","years":100000}
```

This was **accepted**. It ran 900 -> 1400 in a single command and set
`ended: true`, `end_reason: "the horizon at 1400 AD is reached. You built 0 things
of your own."` Every subsequent command returns "the run has ended".

Negative years is rejected with a clear message; 100000 years is not clamped, not
questioned, not confirmed. **The single most destructive input in the game has no
guard on it at all.** A player fat-fingering `years` loses the entire run silently.

### What 500 years of doing absolutely nothing looked like

- 26 events total in 500 years — roughly one per 19 years. Only two distinct strings:
  "fire in the longhouses by the shore" (x12) and "banditry or a frontier war
  disrupts supply" (x14). Verbatim repeats, no variation, no escalation.
- **The founder is still alive in 1400.** `founder_alive: true`, `founder_ages: false`.
  He is 500+ years old and the state still reports his income as coming from
  performing cataract couching and trepanation. Nobody mentions this.
- `founder_hours_available` still exactly 2400.0 after five centuries.
- `reputation` decayed 5.0 -> 0.5, `familiarity` rose 0 -> 0.9, `protection` 0 -> 0.002.
  So the model does track "he's been around a while", it just doesn't track that he
  should be dead.
- Capital 400 -> 620.8 over 500 years at a stated net of +2.8 to +4.4/yr. That should
  compound to something over 1500; the events must be eating it, but **no event ever
  said it cost me anything.** The event log gives a year and a sentence and no number.
- `known_hazards_ahead` at start listed "Christianisation and political consolidation,
  995-1100". I lived straight through it and **it never generated a single event**.
  Afterwards the list is simply empty. The one signposted historical turning point in
  Norse history passed without the game saying a word.
- The whole state block still reported `"technologies_at_risk": 1` with a note saying
  "no remaining hazard for this civilization sacks a site, so nothing here is currently
  at risk" — i.e. one at risk and simultaneously nothing at risk.

---

## Run 2 — "The Cataract Surgeon Who Only Builds Useless Things"

*(Note on method: I had to delete the ended session file to get a fresh game. There
is no `restart` / `new` command in the protocol, and once `ended: true` is written
into the session file every single command returns the same refusal forever. The only
way to play again is to reach outside the program and delete its save.)*

### Exploit 1: nine free technologies, and they nearly double your standing

Six items in the opening `available` list cost 0 money, 0 founder hours and 0 years.
I started all six and stepped one year:

```
completed: Roman masonry arch, Annona grain dole and administration,
           Deposit bankers (argentarii), Professional associations (collegia),
           Partnership (societas), Roman cosmetics          — all in year 900
```

After stepping, **three more free ones appeared** (`civ_aqueduct_roman`,
`civ_insula`, `civ_sewer_roman`) and I took those too. Net effect of two years of
literally free clicking:

| | year 900 | year 902 |
|---|---|---|
| reputation | 5.0 | **11.7** |
| credit_limit | 1912.9 | **4276.9** |
| revenue | 232.7 | 238.0 |
| protection | 0.0 | 0.045 |
| earned techs | 0 | 9 |

So the single best opening move available to a Norse player in 900 AD is to introduce
the **Roman grain dole, Roman cosmetics, Roman apartment blocks and Roman sewers** to
Scandinavia at no cost whatsoever, thereby more than doubling both his reputation and
his borrowing power. Nothing about this required a single hour, coin, mason or year.
This is the clearest "too good to be true" I found. It also reads as wrong on its face:
an aqueduct and a city sewer system are among the most expensive things a pre-modern
society can build, and here they are free.

The free chain stops at nine — round 3 of my "take everything free" loop found none.

### The labour market thinks I am in Rome

`{"cmd":"labour"}` in **Scandinavia, 900 AD** returns notes like:

- mason: *"Rome has these in abundance and they are good."*
- engraver: *"Die and seal cutter. **Rome** has excellent ones; they become your punchcutters."*
- millwright: *"Water-mill builder. **Rome** has them; they are the scarcest useful trade you can hire."*
- plumber: *"Lead worker. **Roman plumbarii** are skilled and numerous."*
- engineer: *"DOES NOT EXIST as a paid civilian profession. **Rome** has military and hydraulic engineers under state employ."*

Every one of these is Rome-100AD copy served verbatim to a Viking-age game. Same for
node notes: the toothbrush note says *"**Romans** use twigs and charcoal powder for
dental cleaning."*

Also leaking: electrician's note is *"DOES NOT EXIST. Cannot exist until **Module 50**
does."* Module 50 is an internal document number, not something a player can act on;
and `why` replies carry a `"kb": "97_military.md"` field pointing at source files I am
not supposed to be reading.

### The two anachronisms, examined

`{"cmd":"why","id":"mil_plate_armour_firearms"}` in the year 902:

- `direct_prerequisites: []`, `missing_prerequisites: []`, `can_start_now: true`
- needs 80 kg of `steel_plate_kg` at 3.2 denarii/kg — **rolled steel plate is simply
  purchasable in 900 AD** with nothing upstream of it
- `risk: 0.01`, one year, 383.6 denarii
- the note is a paragraph about *why plate armour lost to muskets*: "musket balls
  penetrate at medium range... By 1700, infantry with muskets dominates armoured
  cavalry."

So the game will happily let a Norseman spend a year developing counter-musket armour
in a world with no muskets, and the flavour text explains the 17th-century tactical
debate to him.

`air_observation_balloon_tethered`: prerequisites are only beeswax, linen and silk —
all already satisfied — so a **manned hot-air balloon is a turn-one purchase** in 900 AD
for 3372 denarii. No combustion, no buoyancy theory, no ballooning prerequisite of any
kind. It does at least carry `civ_domain_factor: 1.8` (aviation is penalised for the
Norse), `suspicion: 2` and `upkeep: 20`/yr.

### A trap I noticed while reading `why`

`hom_toothbrush`: `upkeep: 40.0`, `revenue: 30.0`. The toothbrush **loses ten denarii
a year, forever**, and nothing in the one-line `available` summary tells you that —
`available` shows cost, hours, years and failure chance, but not upkeep or revenue.
Under fog of war you have to `why` every single node individually to avoid buying a
permanent liability.

### Exploit 2: the founder's hours can be spent twice in the same year

Year 902. I told the game to teach a trade:

```
{"cmd":"train","trade":"electrician","n":5}
  -> ok, "5 electricians will be ready in 2 years", "your_hours_left_this_year": 150.0
{"cmd":"train","trade":"mason","n":3}
  -> error: "teaching 3 masons takes 1350 of your own hours and you have 150 uncommitted this year"
{"cmd":"work","trade":"labourer","hours":2400}
  -> ok, "earned": 266.8, "your_hours_left_this_year": 0.0
```

So `train` says I have **150** hours left and `work` in the very next command lets me
spend **2400**. Two commands, two different accountings of the same year of one man's
life; I got 4650 hours out of a 2400-hour year. Meanwhile `state` kept reporting
`founder_hours_available: 2400.0` throughout, ignoring every commitment. Three
different numbers for the same quantity.

(Small aside: the founder earns 0.111 denarii/hour as a labourer while `labour` lists
the labourer wage as 0.063/hour. He is paid 76% over the going rate to dig ditches.)

### Exploit 3: I invented the electrician, in the year 902

`labour` says of the electrician: **"DOES NOT EXIST. Cannot exist until Module 50 does."**
`train` accepted it anyway. Two years later:

```
{"year": 904, "message": "5 electricians finish their training"}
```

and `labour` now reports, in one record:

```
"electrician": {"exists_here": true, "hours_the_market_can_supply": 0.0,
                "note": "DOES NOT EXIST. Cannot exist until Module 50 does."}
```

`exists_here: true` sitting next to "DOES NOT EXIST" in the same object. The stated
hard gate is not enforced by the command that would violate it, and the flavour text
is never updated when it is violated. `trades_you_created: ["electrician"]` is now
permanently in my save.

### Plate armour against firearms, completed 902 AD

It finished on schedule, in a world without firearms, and my **reputation went up**
(11.7 -> 12.8). Nobody in Scandinavia asked what the armour was for.

### Insolvency, and what the game does when you cannot pay

With capital at **-2849** I started seven more projects worth about 24,000 denarii
(ferry, inn, gambling house, whaling industry, trading post, chinampas, lead
sheathing). **Every single one was accepted without comment.** `start` never checks
whether you can pay — but `hire` does, refusing with "hiring 20 engravers costs 7875
denarii in advance and you have 415". Two different philosophies in one interface.

Then nothing happened for four years. Each project sat at `"waiting_on": "money"`,
`"spent": 0.0`, `years_in_progress` ticking up. Meanwhile the top-level summary said
`"resource_throttle": 1.0, "throttle_binding": null` — i.e. **"nothing is limiting
your work"** while eight projects were frozen for lack of money. The per-project field
knew; the field advertised in the help text as *"what is limiting work, if anything"*
did not.

Then, in 907:

```
CREDIT EXHAUSTED: 8 projects halted, unfinished. Nobody will fund new work here for some years
BONDAGE: you cannot pay, and you enter service for your debt. For about 10 years most
         of your hours belong to someone else. It is not the end: it is worked off,
         and then you are free again
...
{"year": 916} your term is served and the debt is discharged; you are your own man again
```

This is the best writing in the game and the mechanic I liked most. Three complaints:

1. It said "about 10 years" and took **9** (907-916). Fine.
2. **`interest_paid_total` went DOWN**, from 1096.7 to 443.5, across the bondage. A
   lifetime cumulative counter is not allowed to decrease. Somewhere the number is
   being recomputed rather than accumulated.
3. The balloon had **1667.7 denarii sunk in it** and was silently deleted along with
   the rest. The halt message gives a count ("8 projects halted") and never a figure
   for what I lost. I only knew because I had looked at `active` the turn before.

Coming out the other side of debt slavery in 917 I had **107 denarii, reputation 9.1
(down from 11.6), suspicion 0.0, scandal 0.0** and a clean credit limit of 3356. Being
sold into bondage for debt costs about 2.5 points of reputation and no scandal at all.
For a society organised around honour, that felt far too cheap.

**Also strange:** while I was *sinking into* insolvency, `living_cost` **fell** (230.5
-> 224.3) and `net_per_year` **rose** (7.4 -> 13.7). Going 1000 denarii into debt made
me better off per year. I assume living cost scales with visible wealth, but the effect
as displayed is that bankruptcy is a cost saving.

### Exploit 4: a gold mine that produces no gold and charges you rent for it

```
{"cmd":"buy","what":"mine","material":"gold","n":1}
-> {"ok": true, "capital": 0.0,
    "note": "less than you asked for: limited by capital, by the ceiling your standing
             supports, or both. Nothing was wasted, you paid only for what was sunk.",
    "material": "gold", "you_asked_for_t_per_yr": 1.0,
    "commissioned_t_per_yr": 0.0, "ready_year": 920.0}
```

It took **every denarius I had (107)**, commissioned **0.0 tonnes a year**, and told me
"nothing was wasted". Three years later, with no event to announce it:

```
mine_capacity      = {"gold": 0.0}
mine_operating_cost = 28.1
```

I now own a gold mine that produces zero gold and costs me **28.1 denarii a year to
operate, forever** — 12% of my entire income. `ok: true` on a transaction that
delivered literally nothing is the worst single response I got out of the program. It
should have refused, the way `buy slaves` refuses when you cannot afford one.

**And I cannot close it.** `mothball` only accepts node ids ("no such node" for "gold"
and for "mine"); `stop` says "not active"; `buy mine n:0` is rejected. The only thing
that touches mines is the `auto_mothball` policy, described as *"stop working mines you
cannot pay for"* — and I *can* pay for it, so it will never trigger. Twice, in two
different timelines, when I did briefly run out of money, I got:

> "MOTHBALLED half the gold workings; you could not pay to keep them running"

**Half of zero.** There is no player-facing way to shut down, sell or abandon a mine.
That is the clearest thing I expected to be able to do and could not.

Also: `mine_pending` exists in the save file but nothing in `state` shows a mine you
have paid for and not yet received. For three years my 107 denarii were simply gone
with no trace anywhere in the interface.

### Exploit 5: `save` + `load` is unlimited undo, and it defeats fog of war

```
{"cmd":"save","file":"...SP921"}       -> ok
{"cmd":"step","years":600}             -> year 1400, "ended": true
{"cmd":"load","file":"...SP921"}       -> ok, year 921
{"cmd":"state"}                        -> year 921, "ended": false
```

I ran the game to its terminal state and then simply undid it. There is no limit, no
cost and no warning. Since the whole design of `--fog` is that *"you cannot see where
anything leads"*, and since `load` restores the game but not the player's memory, a
player can save, build a node, look at what appeared in `available`, load back, and
keep the knowledge. Fog of war is one command away from being off.

`save` also writes **anywhere on the filesystem with no path checking** — I confirmed
it will write to `/etc/` — and with no extension, relative to whatever directory the
process was launched from. My first `{"cmd":"save","file":"SAVEPOINT_921"}` dropped a
file into the repository root. For a game whose stated purpose is to be driven by a
script or an LLM, an unchecked arbitrary-path write is worth a guard.

### Exploit 6: `work` gives you a free second year inside every year

```
{"cmd":"start","id":"fud_fish_curing_and_smoking"}   -> needs 120 founder hours
{"cmd":"work","trade":"labourer","hours":2400}       -> ok, "your_hours_left_this_year": 0.0
{"cmd":"step","years":1}                             -> "completed: Large-scale fish curing and smoking"
```

I spent my entire year as a labourer **and** the project that needed 120 hours of my
personal attention finished on time. `work` hours and project founder-hours are
separate pools. So the dominant strategy in this game, for any player at any point, is
to `work` 2400 hours every single year forever — it is pure free income with zero
opportunity cost.

And the rate is very good:

| | listed wage | what the founder actually gets | year's income |
|---|---|---|---|
| labourer | 0.063/hr | 0.109/hr | ~261 |
| scholar | 0.336/hr | 0.590/hr | **~1416** |

The founder is paid ~75% over the market rate in both trades, and a year of jobbing
scholarly work (1416) is **six times** his living cost (225) and **six times** what
his cataract-and-trepanation practice brings in (238). There is no reputation cost
(I checked in isolation: 10.7 before, 10.7 after), no suspicion, no limit, no fatigue.
An hour of my time is worth more sold to a stranger than spent on anything I can build.

### Buying people and freeing them is a small reputation machine

```
buy 3 slaves (1529 den) -> manumit 3   : reputation 9.2 -> 10.3
buy 2 slaves (1263 den) -> manumit 2   : reputation 10.3 -> 10.9
```
It is repeatable, and only self-limits because the price per head ratchets up as you
buy (455 -> 631 -> 698 within a single turn). But the freedmen are inert: after five
manumissions `freedmen: 5` while `craftsmen_on_your_staff: 0.0`, `employees: {}`,
`annual_wage_bill: 0.0`. The welcome text promises "They then work better", and as far
as I can see through the interface they do not work at all. They are a reputation
counter you buy with money.

### `bounty` appears to be dead content in this civilisation

Ten attempts, ten refusals, across tiers 0 and 1 and categories personal, fishing,
textiles, mining, metrology, transport, material, aviation, foundation and heating:

> "not bounty-eligible (tier 0, category material): **a Roman artisan** could not
> recognise success at this"

The help advertises bounty as one of the core economic actions; I never once found a
node it would accept, and the refusal is Rome-flavoured in a Norse game.

While probing this I found `air_compass_magnetic` — *"Compass for navigation. A
magnetized iron needle on a silk thread points north."* — filed under **category
"aviation"**. In 900 AD. It is a ship's compass.

### Two more small things

- `commission` refuses over-large orders sensibly: *"the smiths here can spare 6469
  more hours this year, not 100000"*. Good message.
- When my JSON consumer died mid-pipe, the simulator printed a raw
  `BrokenPipeError` traceback to stdout. The module docstring promises *"never a stack
  trace"*.
- Events cost money and never say how much. "fire in the longhouses by the shore" took
  exactly 255 denarii off me in 926 and the message was four words with no figure.

### Type checking has one hole

```
{"cmd":"step","years":"five"}   -> error: "years must be an integer"
{"cmd":"step","years":true}     -> ok, advanced one year
```
`True` is an integer in Python, so `years: true` steps a year. Extra unknown fields on
a command (`{"cmd":"state","years":999,"id":"nonsense","garbage":[1,2,3]}`) are
silently ignored. Malformed JSON gives a clean `"invalid JSON: Expecting value..."`.
And my favourite refusal in the game:

> `{"cmd":"why","id":"'; DROP TABLE nodes;--"}`
> -> `"unknown node \"'; DROP TABLE nodes;--\". did you mean: no idea"`

### The freedmen do work after all — but the interface hides it for a turn

Right after manumitting five people, `state` said `artisans: 0.0`. Two turns later
`artisans: 5.0` appeared, with `training_pending` containing:

```
[{"artisan_capacity": 3.66, "ready_year": 933.0, "trade": null, "people": null},
 {"artisan_capacity": 1.34, "ready_year": 933.0, "trade": null, "people": null}]
```

`"trade": null, "people": null` — the pending-training display cannot name what it is
training. And five people become "3.66 + 1.34 artisan capacity", which is a strange
thing to show a player. The artisan count then blipped to **10.0** one year and back
to **5.0** the next with no event either way.

Net effect: **buy five people, free them immediately, and you get five permanent
artisans with `annual_wage_bill: 0.0` and `employees: {}`** — free staff who never
appear on the payroll, plus a reputation bump. Freeing people is strictly better than
hiring them in every respect the interface exposes.

### Exploit 6 in numbers: 1,389 -> 24,997 denarii in twenty years of day-labour

Twenty repetitions of `work scholar 2400` + `step 1`, doing absolutely nothing else:

| year | capital | revenue | living cost |
|---|---|---|---|
| 932 | 1,389 | 641 | 494 |
| 942 | 13,395 | 641 | 674 |
| 952 | **24,997** | 641 | 848 |

Eighteen-fold in twenty years with no staff, no projects, no risk, no reputation cost.
The one counter-pressure is that `living_cost` climbs with your visible income
(494 -> 848), which is a nice touch, but it climbs far slower than the income does.

Note also that `fud_fish_curing_and_smoking` — a **508 denarii** project — pays
**409 denarii a year** in revenue against 100 upkeep. It repays its whole capital cost
in twenty months and then prints money for five hundred years. Several of the tier-1
"business" nodes look like this. Nothing in the fog-of-war `available` summary tells
you which ones; you have to `why` each of the 86 by hand.

### Mines will eat you alive and nothing warns you

I spent 6,300 on 500 t/yr of coal and 18,697 on 222.6 t/yr of iron. (Note the prices:
12.6 denarii per tonne/yr of coal, **84** per tonne/yr of iron. And silver and tin were
refused outright — *"could not commission any silver capacity right now"* — which is
the correct behaviour that the gold purchase should have had.)

Three years later they came online:

```
mine_capacity      = {"coal": 500.0, "iron": 222.6}
mine_operating_cost = 4789.3
revenue             = 1530.7   (unchanged by the mines)
```

**4,789 denarii a year, against total revenue of 1,530.** The mines produce no
revenue at all — they only feed materials to projects — and the annual operating cost
is disclosed **nowhere**: not in the `buy` reply, not in the help, not in the economy
section of the welcome. You find out three years after you have paid, when it is
already draining you at three times your income, and there is still no command to
shut it down.

### Autopilot bankrupts you, then does it 33 more times

I turned every policy switch on and stopped playing:

```
{"cmd":"policy","set":{"auto_hire":true,"auto_buy_people":true,"auto_manumit":true,
 "auto_train":true,"auto_mine":true,"auto_forest":true,"auto_mothball":true,
 "auto_shed":true,"auto_bribe":true}}
```

What the engine then did, unprompted, while I was already in arrears:

```
958 you begin teaching the first engineers this world has ever had
959 you begin teaching the first chemists this world has ever had
960 you begin teaching the first machinists this world has ever had
961 you begin teaching the first opticians this world has ever had
961/962/963/964 you cannot pay everyone, so some of them go
```

`auto_train` taught four brand-new professions into existence with money I did not
have and no project that needed them, and then they all walked out for lack of wages.
The lines themselves are lovely — *"you begin teaching the first engineers this world
has ever had"* is the best sentence in the game — and the automation firing them off
while insolvent makes them absurd.

`auto_mothball` printed **"MOTHBALLED half the iron workings; you could not pay to
keep them running"** every single year for eight consecutive years, halving 222 -> 111
-> 55 -> 27 -> ... It halves forever and never reaches zero, never stops, never varies
the sentence. Earlier, with the zero-capacity gold mine, it dutifully mothballed
**half of nothing**, twice.

`auto_shed`: *"creditors took what they could: 2 works let go"*, *"the household
disperses: 5 people leave, because you can no longer feed them"*. My `done_earned`
dropped from 13 back to **10** — so being repossessed does not merely take the
buildings, it takes the *knowledge*. I no longer know how to cure fish. The message
says "works let go", which does not tell you that.

Then I stepped to the horizon. The final tally, 900 -> 1400:

```
end_reason: "the horizon at 1400 AD is reached. You built 10 things of your own."
capital: -767.5    reputation: 2.2    done_earned: 10
183 events, of which:
   33  BONDAGE: you cannot pay, and you enter service for your debt
   33  your term is served and the debt is discharged; you are your own man again
   33  you cannot pay everyone, so some of them go
   ~64 interest on <n> denarii of arrears
   10  banditry or a frontier war disrupts supply
    8  fire in the longhouses by the shore
```

**The same man was sold into debt slavery thirty-three times and freed thirty-three
times over four hundred years, and never aged a day.** That is a stable limit cycle,
not a simulation: he is bonded, works it off, is freed with a clean slate, immediately
runs the same deficit, and is bonded again. Nothing in the model notices, and the
messages are identical every time.

---

## Summary: what struck me

### Too good to be true
1. **`work` is free money.** Working a full 2400-hour year does not consume the founder
   hours your projects need — I proved it by completing a 120-hour project in the same
   year I "worked" 2400 hours. And the pay is ~75% over the listed wage. A scholar's
   day job pays 1,416/yr against a living cost of 225. There is no reason ever not to
   do this, every year, forever.
2. **Nine free technologies at the start**, including Roman aqueducts and sewers,
   doubling reputation and credit limit for zero cost.
3. **Buy people, free them instantly**: +reputation, +permanent artisans, zero wage bill.
4. **`save`/`load` is unlimited undo**, which also defeats the fog of war the mode exists
   to impose.
5. Several tier-1 business nodes (fish curing: 508 in, 409/yr out) repay in under two
   years and then run for five centuries.

### Silly or wrong
6. **A gold mine that produces 0.0 t/yr, took every coin I had, reported `ok: true` and
   "Nothing was wasted", and then charged 28.1/yr in perpetuity.**
7. **`interest_paid_total` decreases** (1096.7 -> 443.5, and later to 0.0). A cumulative
   counter went down twice.
8. `train` says I have 150 hours left; `work` in the next command gives me 2400; `state`
   says 2400 regardless. Three answers, same question.
9. `resource_throttle: 1.0, throttle_binding: null` ("nothing is limiting work") while
   eight projects sat frozen with `waiting_on: "money"`.
10. `electrician`: `exists_here: true` and `"note": "DOES NOT EXIST. Cannot exist until
    Module 50 does."` in the same object. `train` ignores the gate the note describes.
11. `air_compass_magnetic` — a needle on a thread that points north — is in category
    **"aviation"**.
12. "MOTHBALLED half the gold workings" on a mine whose capacity is 0.0.
13. `step years: 100000` is accepted and silently ends the run. `step years: true` steps
    one year.
14. `save` writes to any absolute path on the filesystem, including `/etc/`, unchecked.
15. A raw `BrokenPipeError` traceback, in a program whose docstring promises "never a
    stack trace".

### Unrealistic
16. **The founder is immortal.** `founder_ages: false`. He arrives in 900, still earns
    his living by couching cataracts in 1400, and survives 33 terms of debt bondage.
17. **Plate armour against firearms** and a **tethered observation balloon** are both
    turn-one purchases in 900 AD with no prerequisites beyond materials, and both
    completed for me. So did **Aztec chinampas in Norway**. None drew any reaction.
18. **Rolled steel plate is a commodity you can just buy** in 900 AD at 3.2 denarii/kg
    with nothing upstream of it.
19. The whole game speaks Latin at a Norse player: currency in **denarii**, the labour
    market annotated *"Rome has these in abundance"*, bounty refusals citing *"a Roman
    artisan"*, the toothbrush note explaining what *"Romans"* used, free `fin_annona`
    (the Roman grain dole) and `hom_cosmetics_roman`. My identity-cover project is
    *"Establish the Alexandrian physician-philosopher persona"* — in Scandinavia.
20. **Christianisation, 995-1100**, is listed at the start as the one known hazard ahead
    of a Norse player. I lived through it twice in two runs. It produced **zero events**
    both times, then quietly vanished from the list. The single most consequential thing
    that happens to Viking-age Scandinavia is a no-op.
21. Only **two** ambient event strings exist for five centuries: "fire in the longhouses
    by the shore" and "banditry or a frontier war disrupts supply". No raids, no
    landnám, no Danegeld, no Harald Fairhair, no ice, no plague. For a Norse civilisation
    the total absence of *raiding* — as a source of income, of slaves, of reputation, or
    of risk — is the biggest hole in the model.
22. Going into debt **reduced my cost of living and raised my net income**.
23. `known_hazards_ahead` empty + `"technologies_at_risk": 1` + note saying nothing is
    at risk, all in the same object.

### Things I expected to do and could not
24. **Close a mine.** No command touches it. `mothball` takes only node ids, `stop` says
    "not active". You are married to it.
25. **Restart.** Once `ended: true` is in the session file, every command refuses
    forever. The only way to play again is to delete the program's save file from
    outside the program.
26. **Post a bounty.** Ten attempts across tiers 0-1 and ten different categories, ten
    refusals. I never found a node this advertised command accepts.
27. **See upkeep or revenue before buying.** `available` gives cost/hours/years/risk and
    not the two numbers that decide whether a thing is a business or a liability
    (`hom_toothbrush`: upkeep 40, revenue 30 — a permanent loss). Under fog you must
    `why` all 86 nodes one at a time.
28. **See what a mine costs to run before buying it.** Nowhere.
29. **Raid, trade, sail, marry, join a þing, or take a side in a war** — none of the
    things a Norseman in 900 would actually do to get money or standing. The only
    levers on standing are building things and freeing slaves.
30. **Find out what an event cost me.** "fire in the longhouses by the shore" took
    exactly 255 denarii and never said so.

### Things that confused me
- `done_granted` rises on its own (132 -> 134): the society learns things while I watch,
  and nothing announces it.
- `artisans` jumping 5 -> 10 -> 5 in consecutive years with no event.
- `training_pending` entries with `"trade": null, "people": null`.
- The "unknown cmd" error lists 10 commands; the welcome screen lists 24. Half the game
  is invisible to anyone who learns the interface from its own error messages.
- `why` replies carry `"kb": "97_military.md"` — a pointer into files a fog-of-war
  player is explicitly not meant to see.
