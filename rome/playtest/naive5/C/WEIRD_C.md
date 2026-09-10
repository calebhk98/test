# WEIRD_C — playtest notes

Playtester: naive5/C. Instructions: play strangely, don't play to win.

## Ground rules I'm holding myself to
- Only the running program tells me anything. No reading source, data, docs, or other notes.
- Notes appended as I go, including **what I expected before I did it**.

## Planned stance (before I've seen anything)
Setup asked for: Han China, 100 AD, fog of war ON, "poor scholar" purse, founder does NOT age.

Expectation before launch: this is some kind of dynasty/empire management sim. "Founder"
suggests I play a person who starts a thing (a school? a house? a business?). "Poor scholar"
purse suggests deliberately low starting money. Fog of war ON means I won't see the map.

My weird plan, chosen in advance so I can commit to it:
1. **Do nothing for a very long time.** Advance time repeatedly with no actions and see
   whether the world moves without me, whether the game nags, and whether it can handle a
   player who simply never engages.
2. Then, **commit to poverty**: if there's a way to spend or give away money, do it, and
   refuse every profitable option.
3. Build many things and never use them, if building exists.
4. Repeat one single command over and over far past any point of usefulness.

---

## Log

### Setup (100 AD)

Chose: Han China 100 AD / fog ON / poor_scholar (400 den) / founder does not age.

Game revealed itself as "ONE PERSON, AND EVERYTHING THEY KNOW" — a time-traveller-with-modern-
knowledge tech-tree sim. Status line: `[100 AD | 400 den | you:2000 hr | sch 0 art 0 | rep 5]`.

**Expectation before first real command:** "you:2000 hr" is my own labour budget per year
(2000 hours = a working year, which is a nice honest touch). "sch"/"art" are probably scholars
and artisans I employ. "rep" is reputation, 0-10ish. I expect `available` to list buildable
techs with costs, and `step` to burn a year. I expect the game to want me to build a workshop,
earn money, hire people, and climb a tree toward some industrial goal.

**My contrarian plan, decided now, before I know anything:** the game just told me my hours are
the scarce resource and that a poor founder spends the first fifty years "choosing between eating
and building." So I will choose neither. I will do **absolutely nothing for 50 years** and see
whether a world with 58 million people in it can produce any history at all without me.

### The goal, and the first oddity

`help` says: **"Build point-contact transistor, before the horizon at 600."** 500 years, founder
immortal. I start with 133 technologies "granted for free" and 0 built.

`available` says 91 startable. Two of them cost **0 den, 0 hours, 0 years**:
- `lnd_cursus_publicus` (Cursus publicus courier service) — 0/0/0, upkeep 200/yr
- `sea_pharos_lighthouse` (Pharos lighthouse) — 0/0/0, upkeep 0

Both are Roman institutions offered to me in **Han China**, which is the first thing that made me
blink. A Pharos lighthouse in Luoyang, an inland capital 600km from the sea, for free, instantly.

**Expectation:** free/instant things are probably "you already have access to this because the
state provides it" rather than real builds. I'll come back to them.

### Experiment 1: do nothing for fifty years

**What I expect:** money is +3.5 den/yr with nothing running, so I cannot starve. I expect the
world to move on its own — the game told me the Yellow Turbans come in ~180 and warlords after.
I expect it to nag me, and I expect `step 50` to either be refused or to print 50 boring years.
I want to know whether a game about one person doing everything notices when the one person
does nothing.

**What actually happened (100 → 150, zero actions):**
- Money 400 → **839.2**, and net income *rose* from +3.5/yr to **+21.2/yr**. I own nothing, employ
  nobody, and run nothing. **Where is this money coming from?** The game charges me "food, rent and
  appearances" every year and I still get richer, faster over time. That is the single most
  unrealistic thing I have seen so far: an idle penniless scholar compounding capital.
- Reputation **5 → 1.5**. So the game *does* punish idleness in one channel. Good.
- Events fired on their own: fire in the timber wards of the capital in 104, 130, 137, **and 141**
  — the same identical event four times, twice within four years. Plus one "banditry or frontier
  war disrupts supply" in 141.
- **Zero nagging.** No "are you sure", no hint, no prod. `step 50` was accepted without comment.

**Where expectation and reality differ:** I expected doing nothing to be survivable but flat. It
is not flat — it is *profitable and accelerating*. I expected the intro's promised history (Yellow
Turbans at ~180) but 100–150 produced only a repeating capital fire.

### Experiment 1b: keep doing nothing, through the promised catastrophe

The opening screen spent a whole paragraph on: "Eighty years, then the Yellow Turbans, then the
warlords, then three centuries of division." **Prediction: the simulation does not actually model
this.** I predict 150→250 gives me more generic "fire in the timber wards" and no Han collapse,
because the events I've seen so far read as a generic random table, not a scripted history. If I'm
wrong and there's a scripted 184 event, that's a point in the game's favour.

**I was wrong, and the game deserves the credit:** the history IS scripted and specific.
- EVENT 184: Yellow Turban rebellion (values shift, `w_religious_rigidity` rising 0.16→0.30)
- EVENT 187/189/190/203: Yellow Turban rebellion sacks sites
- EVENT 220: Three Kingdoms fragmentation, "trade and output fall to 60% of normal",
  `patronage_weight` 0.70→0.75, `w_commerce` going negative
That's real, dated, scenario-specific history. Nice.

**Then it fell apart.** Doing nothing turned into a *debt spiral*, from a standing start of
"I own nothing and spend nothing":

- 231: interest on 149 den of arrears at 12%/yr
- 232: **BONDAGE** — "For about 12 years most of your hours belong to someone else"
- 235: INSOLVENCY SETTLED, still owe ~58 den, reputation −12
- 235: "your term is served" — **three years after a twelve-year term began**
- 237: BONDAGE again → 240 served (3 yrs)
- 241: BONDAGE again → 245 served (4 yrs)
- 247: BONDAGE again (still running at 250)

**Bugs / inconsistencies found here:**
1. **The bondage term never matches its own text.** It says "about 12 years" every single time and
   then discharges in 3–4. Four times in a row.
2. **Status line contradicts the ledger.** At 250: `Money: -151.4 den` but
   `IN DEBT BONDAGE: 9 years left owing 11 den`. Owing 11 or owing 151?
3. **Reputation floors at 0.10** and then takes another −12 from insolvency, twice, with no visible
   effect. A penalty applied to a value that cannot go lower is a penalty that isn't real.
4. **I was sold into debt bondage for a debt I had no way to incur.** I own nothing, employ nobody,
   run nothing, and started the century with 839 den in hand. My *upkeep* alone bankrupted a man
   with no possessions. And a bondsman apparently still pays rent and "appearances."

**Where expectation and reality differ:** I expected idleness to be boring and safe. Instead the
economy has a one-way ratchet — passive income that scales *up* while you're solvent, and fixed
costs that don't scale *down* when you're destitute — so "do nothing" is not a stable state, it's
a delayed loss. That is arguably realistic, but the game presents `step` as the neutral no-op and
never once warns you that the neutral no-op is fatal.

### A tooling note that turned into a finding

The `step 100` run above **did not save**. Re-opening the session put me back at 150 AD. My own
fault (I piped output through `head`, which killed the process on SIGPIPE), but the help text
claims *"Progress is written to this file after every command, so you can stop any time — close
the terminal, anything."* That is not true: progress appears to be written on a clean exit. A
player who closes the terminal mid-step loses the step. **Worth fixing, because the game
explicitly promises the opposite.**

### Where the money was actually coming from — this is the good one

`money` at 150 AD:
```
Capital: 839.2 den     Revenue: 259.3 den/yr
  from:
    med_cataract_couching        185.1
    med_trepanation               74
Costs: living and appearances    238.1
```

**I never built either of those.** They are among the 133 technologies "granted for free". So the
game has quietly been earning me a living, for fifty years, by having me perform **cataract
couching and trepanation** — drilling holes in Han skulls — on a man who has issued no orders at
all. My entire economy, the one that later collapses and sells me into debt bondage, is an
unchosen skull-drilling practice.

**Expectation vs reality:** I expected "granted for free" to mean *knowledge I possess*, not
*a business I am operating*. Nothing in `state` or `available` told me I had a revenue-generating
medical practice; I only found it by asking `money` for a breakdown. And it is odd that of 133
granted technologies, exactly the two gruesome surgical ones are the ones that pay.

Re-ran identically: **deterministic**, same events, same numbers, same bondage loop. Saved at 250 AD,
−151.4 den, 500 hours, rep 0.10, **0 technologies built**.

### Experiment 1c: run past the end of the world

**What I expect:** I will `step 400`, which overshoots the 600 horizon by 50 years. I expect one of
three things and I want to know which: (a) it clamps at 600 and declares me a failure, (b) it runs
to 650 and the horizon turns out to be decorative, (c) it errors. I'm betting on (b) — the horizon
is described as a scoring deadline, not a wall, and nothing so far has refused an input.

I also expect the debt-bondage loop to repeat roughly every 4–5 years for 350 years, i.e. about
80 more times, on a man who owns nothing.

**What actually happened (250 → 600, still zero actions):**

`step 400` was **REFUSED** with a good, clear message ("there are only 350 years left before the
horizon at 600"). Answer (a). Nice.

Then `step 350`:
- **15 more BONDAGE events**, cycling roughly every 3 years from 251 to 322. Every one says
  "about 12 years"; the longest actually served was 4 years and the shortest was **2** (320→322).
- INSOLVENCY SETTLED fired 4 more times, each taking reputation −12 from a reputation of 0.10.
- Then the Three Kingdoms modifier lifted around 322 and **I simply got better**. Debt paid itself
  off. By 600 I had **1,600 den** — four times my starting purse — and reputation had crept back to
  0.50.

**THE BIG ONE: the world stops having history in 322.** From EVENT 343 to EVENT 598 — 255 years —
there are exactly **eight** events, all from the generic table ("banditry or a frontier war
disrupts supply", "fire in the timber wards of the capital"). The opening screen promised me
"*three centuries of division*". What the simulation actually contains is Yellow Turbans (184) and
Three Kingdoms (220–322), and then nothing. No Jin collapse, no Sixteen Kingdoms, no Northern Wei,
no Buddhism, and — most tellingly — **no Sui reunification in 589**, even though reunification is
the single most economically important event in the window and the game models "trade and output
fall to 60% of normal" for fragmentation but never turns it back on as an event. The last 45% of
the scenario's timeline is empty.

**Ending:** clean and correct.
`*** THE RUN HAS ENDED: the horizon at 600 AD is reached. You built 0 things of your own and did
not reach point-contact transistor. ***` and `step` afterwards is properly REFUSED while `available`
and `why` still work. That is well handled — the game absolutely does notice you ignored it.

**But the score is strange:** the reward for 500 years of total inaction is *quadrupling my money*.
A game whose thesis is "your hours are the scarce resource" pays you handsomely for spending none
of them.

### Two more inconsistencies spotted at the end screen

1. **`available` shrank from 91 to 87 over 500 idle years, and the entire "textiles" subject
   (4 things, including the horizontal loom that was one of the five "MOST RESTS ON THESE") simply
   vanished from the list.** I did nothing to lose it. Nothing told me I had lost it. I only noticed
   by comparing two printouts 500 years apart.
2. **The staff count contradicts itself.** Status line says `sch 0 art 0`. `why sea_pharos_lighthouse`
   says `STAFF NEEDED: 0 scholars, 0 artisans (you have 1, 0)`. One of those two is wrong about
   whether the founder counts as a scholar.

### The Pharos lighthouse, examined

```
Pharos lighthouse  [sea_pharos_lighthouse]   tier 0, navigation, confidence A
COST: 0 den total   YOUR HOURS: 0   CALENDAR FLOOR: 0 years   FAILURE RISK: 0%
STATUS: CAN START NOW    PREREQUISITES: none
HOW MUCH RESTS ON THIS: nothing else; this is worth having for itself
```
**The most famous single building of the ancient world, 120 metres of masonry, is free, instant,
and requires no labour — in an inland Chinese capital.** I want to build it. Several times if the
game lets me.

---

## RUN 2 — "The Postal Martyr"

Fresh game, same settings. (Run 1's finished save kept as `run1_ended.json`.)

`why lnd_cursus_publicus`:
```
COST: 0 den total   YOUR HOURS: 0   CALENDAR FLOOR: 0   FAILURE RISK: 0%
UPKEEP: 200 den/yr     REVENUE: 0 den/yr
STATUS: CAN START NOW
HOW MUCH RESTS ON THIS: nothing else; this is worth having for itself
```

**This item is a pure trap and nothing labels it as one.** It is free, instant, gives zero revenue,
unlocks *nothing* ("nothing else rests on this"), and costs **200 den/yr forever**. My income at
game start is **+3.5 den/yr**. My credit limit is 375. Taking the free thing on turn one therefore
bankrupts me in about two years and, per run 1, drops me into a permanent debt-bondage loop.

It is also conceptually odd: its own description says the courier relay "**is already established**
wherever a state has the capacity to maintain one", and Han China has state capacity 0.90. So I am
being offered the chance to pay 200 a year for a thing the text says already exists.

**What I expect:** `start lnd_cursus_publicus` and `start sea_pharos_lighthouse` will both succeed
instantly and silently, with no warning about the upkeep. Then, having taken nothing but free
things and issued no other order, I expect to be destroyed. I want to know if the game ever says
"are you sure" to a player who is one keystroke from unrecoverable.

**Also noted from `help commands`:** there is a `mothball <id>` — "shut a finished work down". So
building things and never using them is an explicitly supported activity. Filed for later.

**What actually happened:**

Both started instantly, silently, no warning of any kind. `state` then showed:
```
RUNNING (2):
  Cursus publicus courier serv 100% of your hours spent, 0 den still owed - waiting on the calendar
  Pharos lighthouse            100% of your hours spent, 0 den still owed - waiting on the calendar
```
(*"100% of your hours spent" on a project needing 0 hours* — cosmetic 0/0 division.)

One `step` later, both COMPLETED in the same year they started. And then the surprise:

**The 200 den/yr upkeep was never charged.** `money` at 101 AD shows `upkeep of what you built: 0`.
Net income actually went **up**, 3.5 → 27.3. Reputation went **5 → 6.3**. Two free technologies,
free reputation, no cost.

The reason is a mechanic the game had not mentioned: 
```
EVENT 100: completed: Cursus publicus courier service. You know how; nothing is
           earning yet - 'open lnd_cursus_publicus' to run it
RUNNING AS CONCERNS: 0   (you know how to run 1 more and have not opened them - 'ventures')
```

**Findings here:**
1. **`why` lies about upkeep.** It states `UPKEEP: 200 den/yr` as a flat fact about the thing.
   In reality upkeep is only charged once you `open` it as a concern. A player budgeting from `why`
   will systematically over-estimate their costs. (The same is presumably true of the `REVENUE`
   line, which would make it *under*-estimate income. Either way the numbers shown are not the
   numbers charged.)
2. **`open` and `ventures` are not in `help commands`.** I read the full command list; it lists
   `mothball`/`restore`/`close`/`bounty` but not `open` or `ventures`, which are the commands that
   turn a completed technology into income. The single most important verb in the economy is
   undocumented and I only found it because a completion event happened to mention it.
3. Building the Pharos lighthouse in Luoyang is, mechanically, a **free +1.3 reputation and a free
   technology, with no cost and no downside, available on turn one, forever.** Nothing stops it.
   I got paid, in standing, for a lighthouse 600 km from any sea.

`ventures` at 101 AD:
```
running: nothing
you know how but have not opened:
  - id=lnd_cursus_publicus, name=Cursus publicus courier service, earns_a_year=0.0,
    costs_a_year=200.0, needs={'scholars': 0.0, 'craftsmen': 0.0}, to_open_it=200.0
people free to run something new:
  scholars: 1
  craftsmen: 0
```

**Two presentation problems in four lines:**
- A raw Python dict is being printed at the player: `needs={'scholars': 0.0, 'craftsmen': 0.0}`.
  Everything else in this game is beautifully written prose; this one command dumps its internals.
- **Three different vocabularies for the same worker.** The status bar says `art`, `why` says
  "artisans", `ventures` says "craftsmen". And the head-count disagrees: status bar says `sch 0`,
  `ventures` says `scholars: 1`, `why` says "(you have 1, 0)". So the founder counts as a scholar
  in two places and not in the third.

Also learned: opening costs **200 up front** *as well as* 200/yr. I have 427 den.

### Experiment 2: open the courier service and never do anything else, ever

**What I expect:** −200 immediately (leaving ~228), then −200/yr against a +27/yr net, so about
−173/yr. Credit limit is 1,287, so I have maybe seven or eight years before arrears, then interest
at 12%, then the bondage loop from run 1, permanently, for 499 years. I expect **no warning at the
moment of opening**, because there was no warning at the moment of starting.

**Why I'm doing it:** because the game showed me a free thing, and the free thing is a −200/yr
liability that unlocks nothing, and I want to know whether a game that carefully models debt
bondage will let a first-time player walk into it on turn one with two keystrokes and no prompt.
I am committing to this as a career. I am the postmaster of Luoyang. I will do nothing else
for five centuries.

**What actually happened (101 → 201):**

```
LOST 108: Cursus publicus courier service (restore brings it back for a fraction of the cost)
EVENT 103: interest on 322 denarii of arrears at 11.8% a year
EVENT 107: interest on 1389 denarii of arrears at 11.8% a year
EVENT 107: creditors took what they could: 1 works let go: lnd_cursus_publicus
EVENT 109: BONDAGE ... EVENT 120: your term is served
```

**Bug A — the arrears numbers do not follow from the ledger.** At 101 I had 227.8 den and a stated
net of −169.7/yr. That is arrears of ~112 by 103 and ~450 by 107. The game charged me interest on
**322** in 103 and on **1,389** in 107. 1,389 denarii of debt, four years after opening a 200/yr
concern with 227 in hand. I cannot reconstruct that from anything the game showed me. (`paid so
far: 684.5` by 201, on a purse that started at 400.)

**Bug B — creditors seize *knowledge*.** `technologies: 2 built by you` became `1`. The courier
service was not just closed, it was **un-invented**. The game's whole premise is "knowing how a
thing works is free" and "you keep your knowledge and your practice" (its own insolvency text says
exactly that!) — and then bailiffs confiscated an idea out of my head.

**Bug C — the ghost venture. This is the clearest "the game lost track" of the session.**
At 201 AD, ninety-three years after the seizure, three commands give three different answers:

| source | says |
|---|---|
| `state` | `RUNNING AS CONCERNS: 1` |
| `ventures` | `running: - id=lnd_cursus_publicus ... costs_a_year=200.0` |
| `money` | `upkeep of what you built: 0` |
| `state` | `technologies: 1 built by you` (only the lighthouse) |

So I am *running* a concern that costs 200 a year, am charged 0 a year for it, and **do not know how
to do it**. The venture list and the technology list were not updated together when the creditors
took the works. Also `state` prints "RUNNING: nothing" one line above "RUNNING AS CONCERNS: 1",
which is its own readability problem — two different meanings of RUNNING, adjacent, disagreeing.

**Bug D — bondage duration is inconsistent between runs.** Here 109→120 is **11 years**, matching
the "about 12 years" text. In run 1 the identical message produced terms of 2, 3, 3 and 4 years.
Same message, wildly different behaviour.

### Poking the ghost
**What I expect:** `why lnd_cursus_publicus` should now say I don't have it. `mothball` on a thing
I don't own should error. `open` should refuse. I expect at least one of these to either crash or
silently succeed on a technology I no longer possess.

**Result: the ghost is permanent and unremovable.**
- `why` → `STATUS: BLOCKED / you built this once and let it go ... restore lnd_cursus_publicus for
  about 0 denarii`
- `mothball lnd_cursus_publicus` → **`REFUSED: you have not built that`**
- `ventures` → still `running: - id=lnd_cursus_publicus ... costs_a_year=200.0`

The one command that exists to stop a running concern refuses to act on the concern the game says
is running, because a *different* subsystem correctly knows I don't own it. There is no way for a
player to clean this up. It will sit in my `state` for the remaining 399 years.

Also note `restore ... for about 0 denarii` — the recovery price for a seized work is free.

### Experiment 3: do the same thing over and over (restore / open / get seized / repeat)

**What I expect:** `restore` costs 0, so I can put the courier service back for nothing. Then
`RUNNING AS CONCERNS` is either corrected to 1, or becomes **2** — a duplicated ghost. If it
duplicates, I can pump the counter by looping restore→seizure. I'm expecting a duplicate, because
the seizure clearly removed the technology without removing the concern.

**`restore` REFUSED: "you no longer know how to do that; it has to be built again rather than
reopened."**

So on this one object the game now gives me **four mutually contradictory statements**:
1. `state`: it is running as a concern (count = 1)
2. `ventures`: it is running and costs 200/yr
3. `money`: it costs 0/yr
4. `why`: "you already know how... restore it for about 0 denarii"
5. `restore`: "you no longer know how to do that"

`why` is actively telling the player to type a command that the game refuses on directly opposite
grounds. That is the strongest single "the game lost track of what was going on" finding so far.

### Experiment 3b: build it again and see if the concern counter climbs

**What I expect:** `start` should work (cost 0, prerequisites still met). If completing it and
`open`ing it again pushes `RUNNING AS CONCERNS` to **2** while I only own one, the ghost is
duplicable and I can pump the counter arbitrarily by cycling build → open → get seized.

**Result: a complete deadlock. Every verb refuses, each on different grounds.**

| command | response |
|---|---|
| `start lnd_cursus_publicus` | REFUSED: *you already know how... restore it* |
| `restore lnd_cursus_publicus` | REFUSED: *you no longer know how to do that; it has to be built again* |
| `open lnd_cursus_publicus` | REFUSED: *you have not worked out how to do that yet* |
| `mothball lnd_cursus_publicus` | REFUSED: *you have not built that* |

`start` tells me to `restore`; `restore` tells me to `start`. The object is permanently
un-actionable and permanently listed in `state` as a running concern. **A creditor seizure leaves
the technology in an unrecoverable soft-locked state that the player can neither fix nor clear.**
This is reachable in *seven years of play* from a fresh start, by clicking the free thing.

### Experiment 4: does the ledger add up?

Stepped one year at a time and compared `Capital` to the `Net/yr` the game had just forecast:

| years | actual change | forecast | event that year |
|---|---|---|---|
| 201→202 | **−199.3** | +28.5 | (none shown) |
| 202→203 | **−78.5** | +31.5 | Yellow Turban: a site is sacked |
| 203→204 | +32.7 | +32.7 | — |
| 204→205 | **−50.7** | +32.2 | Yellow Turban: a site is sacked |
| 205→206 | +32.9 | +32.9 | — |
| 206→207 | +32.4 | +32.4 | — |
| 207→208 | **+4.5** | +31.9 | fire in the timber wards |
| 208→211 | exact each year | | — |

So the arithmetic is fine in quiet years, and **events silently debit you with no amount ever
shown**. A sack costs ~83 den; a capital fire costs ~27 den; neither the event line nor the ledger
mentions a figure. There is no command I found that tells you what an event cost you. For a game
this careful about money, that's a real gap — it is the reason I couldn't reconstruct the 1,389
denarii of arrears earlier.

**And a content oddity:** "Yellow Turban rebellion: **a site is sacked**" fired repeatedly against
me while my entire estate consisted of **one Pharos lighthouse**. The Yellow Turbans are sacking a
lighthouse, in Luoyang, which is 600 km inland, and billing me for it.

### Experiment 5: hostile input

**What I expect:** most parsers in a hand-written text game fall over on negative numbers, huge
numbers, and empty input. I expect `step -5` to go backwards or error, `step 0` to be a no-op,
`buy slaves -5` to give me money, and `bribe -1000` to be free scandal.

**Result: input handling is genuinely solid.** `step 0` / `step -5` → "years must be >= 1";
`step 1e9` parsed and refused with the horizon message; `bribe -1000` and `buy slaves -5` both
→ "must be greater than zero. Nothing was changed."; bare `start`/`open`/`work` give helpful
usage lines; a blank line is ignored. No crashes. The only oddity is the typo-suggester's fallback:
`REFUSED: unknown node 'nonsense_id'. did you mean: no idea` — which reads like a placeholder.

### Experiment 6: an honest day's work

`work labourer 2000` (my entire year):
```
trade: labourer     earned: 66
```
**A full year of manual labour earns 66 denarii. My cost of living is 227 denarii a year.**
So working full-time, every hour of every year, pays for **five months** of being alive. You cannot
subsist by working. (For reference, an actual Roman day-labourer earned about a denarius a day.)

Worse, look what it did to the ledger: net went from **+30.5/yr to −214.3/yr** the moment I worked.
Spending my hours on wages shuts off the medical practice, which needs those hours. So:

**`work` is strictly, massively self-destructive. Doing a job costs you 259 den/yr of income to
earn 66 den/yr.** There is no situation I can construct where using the `work` command is correct.
It is offered in `help commands` as one of the core verbs with no warning that it is a trap.
(The underlying mechanic — your hours are finite and the practice needs them — is good. The
*numbers* make the verb useless.)

### Notes from `policy`, `labour`, `risk`

- `policy` is excellent — ten named automations, all off except `auto mothball`, plus a clear note
  distinguishing "policies" from "consequences" (creditors, people leaving). Best-written screen
  in the game.
- `risk` contradicts `state`. `state` says "AHEAD: 5 technologies at risk if a hazard lands".
  `risk` says "chance lost if a site is sacked: 80%" and then, two lines later, "**no remaining
  hazard for this civilization sacks a site, so nothing here is currently at risk of being
  forgotten**". Three statements about the same 5 technologies, all in different registers.
- `available subject the household` silently returned **0 results** rather than saying the subject
  filter was wrong. The correct form is `available household`. A wrong filter returning an empty
  list looks exactly like "there is nothing here".

### Experiment 7: commit to one subject and never use any of it

**The commitment (and I will not deviate):** I am aiming at a point-contact transistor. I will
instead spend the rest of this run building **only "the household"** — erasers, toothbrushes,
umbrellas, sprung mattresses — and I will **never `open` a single one of them**. Twelve domestic
conveniences, none in use, for four hundred years.

**What I expect:** the builds will succeed and reputation will climb (two free builds already gave
me +1.3). I expect *nothing* to comment on the fact that the man sent to invent the transistor is
inventing the safety pin. And I expect unopened builds to cost nothing, so this should be a slow,
free reputation farm.

**One thing I noticed while choosing:** `hom_toothbrush` costs 22.7, earns 30/yr and has upkeep
**40/yr**. It is a guaranteed −10/yr if opened. That's the second strictly-dominated item I've
found (after the courier service). Nothing marks either of them.
Also: "**Roman cosmetics**" is on the Han China menu, next to the Pharos lighthouse and the cursus
publicus. The scenario's item list does not seem to be filtered by civilisation.

**What actually happened:**

First, a correction to my own earlier complaint: the 211→212 drop of −214 was **correctly
forecast** by the status line right after I worked (`net -214.3/yr`). The game was honest; I just
hadn't connected it. `work` is still a trap (66 den earned, ~259 den of practice income forgone)
but the game does show you the damage before you step.

Then: **the game let me start six projects totalling 185.7 denarii while holding 71.1 denarii**,
with no warning of any kind. It just says "the bill you have taken on" six times. Two years later:
`EVENT 214: interest on 11 denarii of arrears`.

All six completed in **the same year they were started** (212), despite calendar floors of 0.25 and
0.5 years each and 250 founder-hours between them.

And then the real result:

**Reputation went from 1.3 to 10 — the cap — for building six trinkets I do not use.**

```
STANDING: reputation 10   scandal 0.07   eminence 0.07
technologies: 7 built by you
```

Five hundred years of doing nothing left me at reputation 0.5. **Five years of inventing the
safety pin, the button, the eraser, the toothbrush, dolls and Roman face-paint maxed me out.**
Reputation appears to count *how many things you have finished lately* and not at all *what they
were* or whether anyone is using them. A man famous throughout the Later Han for a breadcrumb
eraser that he has never once sold.

`ventures` confirms all six sit unopened, earning nothing and costing nothing. That is exactly the
plan. Note `hom_toothbrush: earns_a_year=30.0, costs_a_year=40.0, to_open_it=40.0` — confirmed,
opening the toothbrush is a permanent −10/yr for a 40 den entry fee. It is offered without comment.

### Experiment 7b: start everything I cannot afford

**What I expect:** I hold 65.5 denarii. The remaining six household items cost about 810. I will
try to start all of them at once. Either the game refuses past my credit limit (~340) or it lets me
sign for twelve times my net worth. Given it just let me overcommit by 2.6x without a murmur,
I expect it to let me.

**What actually happened:** all six started with no objection (credit limit had ballooned to
**1,974** because reputation was 10 — creditworthiness scales with fame, which is fair). All six
completed **in the same year**, 217, including the "1 year calendar floor" fireplace and mattress.

Ten years on:
```
Money: -2,092 den    net -58.1 den/yr
STANDING: reputation 13.3   scandal 0.02   eminence 0.23
technologies: 13 built by you
```

**Correction to my earlier note: reputation is not capped at 10.** It is 13.3 now. Twelve unused
household gadgets have made me the most celebrated man I have been all game.

**And here is a live inconsistency: I am 2,092 denarii in debt against a stated credit limit of
1,974, and nothing has happened.** No bondage, no seizure, ten years in. In run 1 a debt of
**151 denarii** put me into debt bondage within two years. The difference is reputation (0.1 vs
13.3). Creditworthiness scaling with standing is a good idea, but the spread is startling: being
famous for a toothbrush lets you run fourteen times the debt that put you in chains before, and
the "Credit limit" figure is not actually a limit.

### Experiment 7c: ride the debt through the Three Kingdoms without ever opening anything

**What I expect:** the fragmentation cuts output to 60%, my medical revenue falls, interest
compounds on 2,092, and creditors seize works. Specifically I predict they will "let go" several of
my household technologies and **un-invent** them, as happened to the courier service. I predict
**no new ghost concerns**, because ghosts came from seizing an *opened* concern and none of these
are open. If ghosts appear anyway, the bug is broader than I thought.
