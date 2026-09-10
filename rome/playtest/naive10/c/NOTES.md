# Playtest notes — naive10/c

Adversarial playtest of `python3 rome/sim/simulator.py` (menu path).
Full repro transcript: `transcript.txt`. Command files and session saves: `games/`.
Menu answers written as `2 / <blank> / <blank> / <blank>` mean:
civilisation 2 (Rome, 100 AD), fog on, `poor_scholar` (400 den), no ageing.

**Caveat:** the repository was being edited during this session (`rome/sim/engine`
mtime 20:01, `test_regressions.py` mtime 20:20). Every problem below was re-verified
against the build as of ~20:30 unless marked otherwise.

---

# TOP PROBLEMS

### 1. Paying your debt off in full makes you bankrupt, and it takes all your reputation  (Obs 8)
Working harder is punished with the game's worst outcome, silently and with no
warning. From the game's own recommended opening:

```
2 / <blank> / <blank> / <blank>
start arithmetic_positional
step 1                 -> Money: -628.5 den, project complete, reputation 6.6
work scholar 2000      -> earned 645.7, "so you are up: 412.2"
state                  -> Money: 17.2 den   reputation 6.6   (no arrears at all)
step 1
```
```
EVENT 101: INSOLVENCY SETTLED: most of the debt is written off and you still owe
about 74 denarii. Your name is worth less for it (reputation -6.6) ...
Money: -73.5 den        STANDING: reputation 0   protection 0%
```
A player holding **+17.2 den and owing nothing** is declared insolvent; a debt that
does not exist is "written off"; 74 den of new debt is *created* out of a positive
balance; and all 6.6 reputation is destroyed (not to the 0.10 floor - to 0).

It is monotone the wrong way. Same opening, varying only the hours sold:

| `work scholar N` | capital at end of 101 | what the next `step` does |
|---|---|---|
| 0 | **-628.5** | nothing, reputation 6.5 |
| 1000 | -305.6 | nothing |
| 1500 | -144.2 | nothing |
| 1800 | **-47.0** | `CLOSE TO THE LIMIT: you owe 261 of the 328...` (state said -47) |
| 2000 | **+17.2** | **INSOLVENCY**, reputation -> 0 |

Owing 628 is safe, owing 47 is a warning, owing nothing is ruin. The early-warning
event fires only in the case that survives, and the debt it quotes (261) is five
times the debt `state` printed one line earlier (-47).

### 2. The default start cannot play the game, and the setup screen's own number about this is wrong by 100x  (Obs 27)
The kit screen: *"a million denarii buys perhaps a tenth off the time, not a different
game."* Identical 250-year script (all auto policies on; every year attempt `start`
on all 142 ids from `path point_contact_transistor`, then `step 1`):

| kit | technologies built by 350 AD | capital |
|---|---|---|
| `absurd` (1,000,000 den) | **102** | 871,718 |
| `poor_scholar` (400 den, the DEFAULT) | **1** | **-93.8** |

A gentler poor-scholar script (one `start` attempt a year, all 500 years) finishes
**2 technologies** and logs **34 INSOLVENCY SETTLED events**, ending at -1,227 den
with "Credit limit: 219.2 (559% used)". The cheapest node on the road to the goal
costs 1,032 den; the default purse is 400 den with +3.5 den/yr; the game lets you
commit anyway and one legal action starts an unrecoverable loop.

### 3. Following the game's own headline advice destroys a default start by year 106, and "halted" means "deleted"  (Obs 13, Obs 14)
`available` lists `units_standards`, `arithmetic_positional` and `scientific_method`
under **"MOST RESTS ON THESE"**; `why arithmetic_positional` calls it "Highest return
on personal hours in the entire tree". Start all three:
```
start arithmetic_positional / start scientific_method / start units_standards
step 5 -> scientific_method: 100% of your hours spent, 115 still owed
step 2 -> EVENT 106: CREDIT EXHAUSTED: 2 projects halted, unfinished...
          RUNNING: nothing
```
"Halted, unfinished" reads as suspended; the projects are **deleted**. ~795 den paid
and ~800 founder-hours spent are gone, `scientific_method` dying 115 denarii short of
done with every one of its hours already burnt. The earlier warning's suggested
remedy (`stop` a project) loses exactly the same thing, so no branch saves the sunk
cost. For the next twelve years `available` reports "0 startable now" and `stuck`
gives a false reason for it ("everything in front of you is either built, already
running, or waiting on something" - in fact 214 things are startable the moment the
credit freeze lifts), while the header still advertises "what you can pay for:
available afford 224" to a player 970 in arrears.

### 4. `commission` is a documented command that takes your money and does nothing  (Obs 22)
`why units_standards` lists `HIRED LABOUR: carpenter 200h, smith 400h`. Buy exactly
that first: the bill is 444 and the year spends 444 — identical to the control run
without the commissions. It does not unblock a labour-starved project either: in
Scandinavia, `arithmetic_positional` stuck at "wants 2500 [scribe] hours a year; this
society can field 419 at most" reaches *byte-identical* progress (81%, 368.7 owed at
year 904) whether or not you commission the maximum 419 hours every year. It does not
supervise a concern either. `labour` actively recommends it: "or commission smith 400
to buy one job instead of employing anybody".

### 5. The staff system: the `*` marker is false, and five screens give five headcounts  (Obs 12)
`available`'s legend says a `*` means "you do not have them yet - 'hire' or 'train'
first, **or the work waits**". Nothing waits: `tx2_retting`, `met_investment_casting`
and `fin_census` (all starred) all complete at full speed with `EMPLOY: 0 people`.
Staff only matter at `open`, as fractional *supervision*, which is not what any
screen says. With an empty payroll, at one instant: `state` "sch 0 art 0";
`labour` "nobody"; `why` "(you have 1, 0)"; `available` `1a*`; `ventures`
"1 scholars, 1 craftsmen (one of each of those is you)". Only the last matches the
engine. `ventures`' NEEDS column ("0 sch 1 cr") is not the number used either — the
real cost is 0.5 craftsmen — and the refusal message reads
"it needs 0.2 craftsmen ... and you have ... 0.2 not already watching something else"
and then refuses. Hired staff also decay ~3.5%/yr to zero with no replacement and no
warning in `help labour`.

### 6. `ventures` understates what a concern earns by a factor of 2.24  (Obs 18)
At year 350 of the long run, for every single open concern: `ventures` says
crucible_steel earns 11,000/yr, the `money` ledger says 24,571; lead_chamber 9,000 vs
20,104; interchangeable_parts 8,000 vs 17,870 — a uniform 2.234x. The whole
`ventures` RUNNING column sums to 100,200; the ledger's concern rows sum to 224,343.
`open <id>`'s confirmation and `state`'s "those shut concerns would clear 20,000
den/yr between them" quote the same understated figure. The screen a player uses to
choose what to open is wrong by 124%.

### 7. `restore` costs double what `open` cost; the engine elsewhere says a tenth  (Obs 23)
`open fin_lottery` 312 → `mothball` → `restore` **624**, immediately and after five
years (horse_collar: 150 then 300). But an engine event says "The premises and the
stock stand for a few years yet, so reopening soon costs **a tenth** of what opening
did". A factor of twenty apart, and the price is never shown before you commit —
while `auto_shed`, `help commands` and the CLOSE TO THE LIMIT advice all push you to
mothball.

### 8. A dead founder keeps playing  (Obs 16)
With mortality on: `EVENT 138: the founder dies, aged about 73`. At year 140,
`You: DEAD and ageing, 0 founder-hours free this year`, and `start units_standards`
(a 300-founder-hour project) is accepted, `hire artisan 2` is accepted, and the
practice keeps paying (+3.4 den/yr from `med_cataract_couching` and `med_trepanation`
— a dead surgeon still operating). Only `work` checks the hours. The run does not end
for up to eleven more years, all of them playable. Bonus:
`EVENT 145: you cannot pay everyone: 0.0 of your staff leave for work that pays`.

### 9. The credit "limit" is not a limit, and insolvency is a free, repeating debt write-off  (Obs 6)
Do nothing at all for 400 years and you reach `Money: -1,034 den` against
`Credit limit: 220.5 (**469% used**)`, after both help topics promised "as far as
somebody will lend you and no further". From year 240, `INSOLVENCY SETTLED ... about
77 denarii` fires **every ten years, forever**, costing -0.1 reputation against a
floor of 0.10 — i.e. nothing. There is no game over and no recovery; you just cycle.

### 10. A fire in somebody else's tenement burns a flat ~18% of your cash  (Obs 7, Obs 20)
`fire in the insula district` destroyed 75/413.8, 79/434.3, 70/382.5, 60/330.9 —
18.1%, 18.2%, 18.3%, 18.1% — of a founder who owns no building, and 166,021 denarii
of a millionaire. It destroys exactly nothing if you hold no coin ("it destroyed
nothing, because you were holding none"), so the optimal play against the game's
biggest recurring hazard is to run at zero or negative cash.

### 11. The two hazards `state` puts on screen every turn never fire  (Obs 24)
`state` prints "SCANDAL is dangerous above 25" and "EMINENCE is dangerous above 26"
every single turn. Over two full 500-year runs (ending 5,000,000 den, reputation 97,
131 technologies) the maxima reached were **scandal 7.8** and **eminence 13.1**. An
entire help topic, the undocumented `withdraw` command, `bribe`'s stated purpose and
the `auto_bribe` policy hang off machinery I could not get to trigger once.

### 12. 76 denarii buys the whole purchasable protection, at any wealth  (Obs 4)
`bribe 100` as a pauper and `bribe 1000000` as a millionaire both take exactly
**76 denarii** and both give **32%** protection — which `help protection` calls "the
only thing money can buy here directly" and documents as a cap of **30**, not 32.
`bribe 1000000` is refused if you do not *hold* the million, though it would only
have taken 76.

### 13. Everything else
Headcount arithmetic that turns 5 bought people into "6.6 ... learning the work" and
then 4 artisans in the prompt (Obs 17); a `net/yr` forecast that is wrong by ~260 den
in the year you hire (Obs 15); `help money`'s living-cost formula omitting the ~6% of
revenue that is actually in the line, so the cost *falls* as you get richer (Obs 2);
the Mexica scenario quoting you an iron mine after its own blurb says "no iron", and
all five civilisations sharing one hiring list and one starting medical practice
(Obs 25); `bounty` as an irreversible 1,774-denarius purchase with no way to see the
price or the effect first (Obs 26); an end-of-run summary that says "you built 0
things" and "you had 4 of them" two lines apart (Obs 28); a mine whose quoted 750/yr
standing cost is invisible for three years and whose `close` says "You stop paying 0 a
year" (Obs 19); and the assorted small ones in Obs 29.

**What is solid:** determinism (two identical menu runs are byte-identical; read-only
commands do not perturb the RNG; `step 50` twice equals `step 100`), the cost
breakdowns in `why` (labour + materials + capital times the listed multipliers always
reconciles to the total), and the `money` ledger's internal arithmetic (its rows sum
exactly to the printed revenue, and the compounding debt spiral matches a hand
calculation to within a denarius).

---

# DETAILED OBSERVATIONS

## Setup / how I drove it

All runs: `cd /home/user/test/rome/playtest/naive10/c/games && printf '<lines>' | python3 /home/user/test/rome/sim/simulator.py`
Menu answers used throughout unless stated: `2` (Rome 100 AD), blank (fog on), blank (poor_scholar 400 den), blank (no ageing).

---

## Obs 1 — "Come back with" resume command is wrong unless you are in the repo root

Repro: run the game from any directory other than `/home/user/test`. It saves
`rome_100ad.json` into the *current* directory but prints

```
Saved to rome_100ad.json. Come back with:
   python3 rome/sim/simulator.py play --session rome_100ad.json
```

The `rome/sim/simulator.py` part is relative to the repo root, the session file is
relative to cwd. Only one of those two can be right at a time. Cosmetic but the
game is explicitly telling you to run a command that will not work.

---

## Obs 2 — `help money` describes living costs as capital-based; they are also revenue-based, and they FALL when you get richer

`help money` says: "Living and appearances is about a sixtieth of your capital a
year, on top of a subsistence floor and your household, plus a fixed sum for each
rank you hold." Nothing about income.

Repro (`money`, `work smith 1000`, `money`, `work smith 1000`, `money`):

| | capital | revenue | living and appearances | of which "because you are rich" |
|---|---|---|---|---|
| start | 400 | 233.5 | 230 | 6 |
| after 1000 hr sold | 544.1 | 116.8 | 225.2 | 8.2 |
| after 2000 hr sold | 688.3 | 0 | 220.3 | 10.3 |

Capital went UP by 72%, the "because you are rich" line went up with it, and yet
the total living cost went DOWN. Backing it out, ~6% of revenue is inside the
"living and appearances" line, which is nowhere in the help text. A player
budgeting from the documented rule ("a sixtieth of capital + a floor") gets the
wrong answer.

---

## Obs 3 — `work scholar` pays more than `work master`, and much more than `work smith`

Repro: `work master 100` -> earned 25.6. `work scholar 100` -> earned 32.
`work smith 1000` -> earned 144.1 (14.4 per 100 hr). `work labourer 100` -> 6.4.

So the highest-paid job available to the founder is "scholar", above "master"
(the top artisan rank). Not obviously wrong, but it means the optimal money
command is always `work scholar`.

---

## Obs 4 — `bribe` : 76 denarii buys 32% protection, at ANY wealth, and the help text says 30

`help protection` says money is worth "only 30 points" of protection "however much
you spend", and tells a story about a break tester offering a million and stopping
"at the same 32%".

Repro (poor_scholar, 400 den):
```
bribe 10   -> for 10 denarii ... protection 0.00 -> 0.06
bribe 50   -> for 50 denarii ... protection 0.00 -> 0.22
bribe 100  -> for 76 denarii; 24 denarii of what you offered was not taken ... protection 0.00 -> 0.32
bribe 400  -> for 76 denarii; 324 ... not taken ... protection 0.00 -> 0.32
```
and with `absurd` (1,000,000 den): `bribe 1000000` -> "for 76 denarii; 999,924 ...
not taken ... protection 0.00 -> 0.32".

Two problems:
1. The documented cap is **30**, the delivered cap is **32**. Small, but the help
   text quotes the exact number.
2. The saturation price is a flat 76 den *independent of capital*. A destitute
   founder and a millionaire pay the same 76 for the same 32 points. Given that
   `state` calls protection "the only thing money can buy here directly", 76
   denarii (a third of one year's living costs) for the whole purchasable ceiling
   makes the first move of every game trivially `bribe 100`. It decays (32% -> 1%
   over 50 idle years) so it must be topped up, but at 76 den a pop that is noise.

Also: `bribe` **refuses** if you do not *hold* the amount you offer ("REFUSED: you
have 400 denarii" for `bribe 1000000`) even though it then only takes 76. So the
offer amount is validated against a number that is never spent.

---

## Obs 5 — `why <id>` says "you have 1" scholar; `state` and `labour` both say you have none

Repro: `why units_standards`
```
STAFF NEEDED: 0 scholars, 0 artisans   (you have 1, 0)
```
while at the same moment the prompt reads `sch 0 art 0`, `state` says
"EMPLOY: 0 people ... nobody", and `labour` says "ON YOUR STAFF: nobody".
Three views of the same quantity, two of which say 0 and one says 1.

---

## Obs 6 — the debt death-spiral: "no further" credit that lends you 469% of the limit, and an insolvency that repeats forever

Repro: `2 / <blank> / <blank> / <blank>` then `step 20`, `step 80`, `step 100`,
`state`, `money`, and keep stepping. Do nothing at all for 400 years.

`help money` and `help economy` both say: "You may spend past what you have, as far
as somebody will lend you and no further."

What actually happens (year 300, having issued no command but `step`):
```
Money: -1,034 den    net -159.5 den/yr
Credit limit: 220.5 (469% used)     interest on arrears: 11%     paid so far: 4,039
```
Nobody agreed to lend 1,034 against a 220 limit. The debt is involuntary — it is
just living costs minus practice income minus compounding interest — but the game
told me there was a hard stop and there is not.

Then, from year 240 onward, this repeats **every ten years, forever**:
```
EVENT 240: INSOLVENCY SETTLED: most of the debt is written off and you still owe about 77 denarii...
EVENT 250: INSOLVENCY SETTLED: ... about 77 denarii ...
EVENT 260: ... 270: ... 280: ... 290: ... 300: ... 310: ...
```
(reputation -0.1 each time, but reputation is already floored at 0.10, so the
"cost" of insolvency is zero after the first one.)

Two consequences:
* **Unlosable / unescapable stuck state.** Doing literally nothing for 500 years
  never ends the run; you just cycle bankrupt -> forgiven -> bankrupt. There is no
  game-over and no way the situation improves.
* **Free money.** Debt above ~77 den is written off on a ten-year clock at zero
  real cost once reputation is at the floor. Borrow, spend the borrowed money on
  projects (which are permanent), wait for the write-off, repeat. See Obs 12 for
  the exploited version.

The arithmetic of the spiral itself does check out: with revenue ~175, living ~224
and 11% on arrears, d(n+1)=1.11d+49 from 77 gives 1,040 after ten years, and the
game printed 1,034.

---

## Obs 7 — "fire in the insula district ... destroyed 75 denarii" is a flat ~18% of whatever coin you are holding

Repro: idle run, single steps:
```
EVENT 104: fire ... destroyed 75 denarii   (capital was 413.8 -> 18.1%)
EVENT 130: fire ... destroyed 79 denarii   (capital was 434.3 -> 18.2%)
EVENT 137: fire ... destroyed 70 denarii   (capital was 382.5 -> 18.3%)
EVENT 141: fire ... destroyed 60 denarii   (capital was 330.9 -> 18.1%)
```
You own no building - you are explicitly "one person in a rented room" - yet a fire
in someone else's tenement burns a fixed fraction of your *cash*. The player-facing
consequence is that holding coin is taxed at ~18% per fire and holding none is free,
so the optimal play is to run at zero or negative cash. Combined with Obs 6 that is
a strategy, not a hazard.

---

## Obs 8 — **Paying off your debt in full makes you bankrupt.** Positive cash is confiscated, reputation is wiped, and the message is a lie

This is the worst thing I found. Exact repro, from a fresh menu game:

```
2
<blank>            (fog on)
<blank>            (poor_scholar, 400 den)
<blank>            (no ageing)
start arithmetic_positional
step 1
work scholar 2000
state
step 1
state
```

`start arithmetic_positional` is the game's own signposted best opening — `why`
calls it "Highest return on personal hours in the entire tree" and `available`
lists it under "MOST RESTS ON THESE".

After `step 1` you are at **-628.5 den**, project complete, reputation 6.6.
`work scholar 2000` earns 645.7 and clears the debt: `state` now says

```
Money: 17.2 den
STANDING: reputation 6.6   protection 2%   scandal 0   eminence 0.01
```

You owe nothing. You have money in hand. Then `step 1`:

```
EVENT 101: INSOLVENCY SETTLED: most of the debt is written off and you still owe
about 74 denarii. Your name is worth less for it (reputation -6.6), and you keep
your knowledge and your practice

Money: -73.5 den
STANDING: reputation 0   protection 0%   scandal 0   eminence 0
```

So the engine:
* declared insolvency on a player holding **+17.2 den and no arrears**;
* "wrote off" a debt that did not exist, and in doing so **created** 74 den of debt
  out of a positive balance (a swing of about -91 den);
* took **all** of the reputation (6.6 -> 0, not to the usual 0.10 floor), which also
  zeroed protection (2% -> 0%);
* gave **no** "CLOSE TO THE LIMIT" warning first.

### It is monotone in the wrong direction

Same opening, varying only how many hours you sell in year 101:

| `work scholar N` | capital at end of 101 | what the next `step 1` does |
|---|---|---|
| 0 (don't work) | **-628.5** | nothing. rep 6.5. fine. |
| 500 | -467.0 | nothing. rep 6.5. |
| 1000 | -305.6 | nothing. rep 6.5. |
| 1500 | -144.2 | nothing. rep 6.5. |
| 1800 | **-47.0** | `CLOSE TO THE LIMIT: you owe 261 of the 328...` |
| 2000 | **+17.2** | **INSOLVENCY**, rep -> 0, capital -> -73.5 |

Owing 628 is safe. Owing 47 is a credit warning. Owing nothing is bankruptcy. The
harder you work to pay your creditors, the worse the game treats you.

The visible cause is that the credit limit is computed from revenue, and `work`
consumes the founder-hours that produce the practice revenue, so selling all your
hours drives your credit line to ~0 for that year. Nothing in `help money`,
`help economy` or the `work` command's own explanation ("Hours sold for wages come
out of the practice ... so you are up: 412.2") warns that this can bankrupt you.
`work` even reports the trade as *profitable* in the same breath.

### Sub-bug: the CLOSE TO THE LIMIT warning quotes a debt you do not have

In the 1800-hour row, `state` printed `Money: -47 den` and the very next event said
`you owe 261 of the 328 anyone here will advance you (79%)`. Two different figures
for the same debt in the same year, one of them off by a factor of 5.

### Sub-bug: the warning fires only in the case that is safe

The 1800-hour run got the warning and survived. The 2000-hour run got no warning at
all and went bankrupt. The early-warning system is anti-correlated with the danger.

---

## Obs 9 — [FIXED DURING THE SESSION] `start` may borrow; `open` may not — so you could permanently strand a finished project

`help money` / `help economy`: "You may spend past what you have, as far as somebody
will lend you and no further."

`start arithmetic_positional` with 400 den in hand happily runs you to -628.5 den
(45% of a 1,392 credit limit). But once it is finished, the only way it earns
anything is `open`, and:

```
REFUSED: opening it costs 155 denarii in stock and premises and you have -628
```

So `start` is allowed to use credit and `open` is not. The net effect on the naive
opening is: you spend everything on the single project the game most recommends,
finish it, and then cannot switch it on. `state` twists the knife every turn with
"those shut concerns would clear 200 den/yr between them, and earn nothing while
they are shut" - a 200 den/yr income you are locked out of for want of 155 den you
are allowed to borrow for anything else.

---

## Obs 10 — `ventures` and `why`/`available` disagree about whether the founder is a craftsman

`ventures`: "free to put behind something new: **1 scholars, 1 craftsmen** (one of
each of those is you)" - i.e. the founder counts as one of each simultaneously.

`why tx2_retting` at the same moment: "STAFF NEEDED: 0 scholars, 1 artisans
**(you have 1, 0)**", and `available` tags the same project `1a*` where
"A * means you do not have them yet".

So the founder is a craftsman according to `ventures` and not a craftsman according
to `why` and `available`. `state` and `labour` say the founder is neither
("sch 0 art 0", "ON YOUR STAFF: nobody").

---

## Obs 11 — determinism: confirmed good

Two identical menu runs (`2`, blank, blank, blank, `step 100`) produce byte-identical
event streams. Interleaving read-only commands (`state`, `available`, `money`,
`risk`, `labour`, `ventures`) does not perturb the stream, and `step 50` twice equals
`step 100`. That part is solid.

One consequence worth flagging as a design smell: the **menu path never asks for a
seed and always uses the same one**, so every player's Rome game gets the identical
fire in 104, 130, 137, 141 and so on. `play --seed N` exists on the command line but
the menu the game tells you to use does not expose it.

---

## Obs 12 — the `*` staff marker is a lie for building, and every screen disagrees about how many people you have

`available` legend: "STAFF is the standing people it needs: 2s = two scholars,
1a = one craftsman. **A * means you do not have them yet - 'hire' or 'train' first,
or the work waits.**"

### (a) The work never waits. Nothing needs staff to be BUILT.

```
2 / <blank> / absurd / <blank>
start tx2_retting            (listed 1a*)
start met_investment_casting (listed 1a*)
start fin_census             (listed 1s1a*)
step 1
state
```
```
EMPLOY: 0 people, 0 den/yr in wages
COMPLETED 100: Investment casting and lost wax
COMPLETED 100: Retting of flax and hemp fibres
```
All of them finish at the fastest possible rate with zero employees. `state`'s
RUNNING lines only ever say "waiting on your hours" or "waiting on the pace it can
absorb money" - never waiting on staff. Same for `horse_collar` (`1a*`): built and
opened with no employees at all, earning its full 900/yr. Hiring the artisan first
(250 down + 251/yr) buys you nothing and the interface pushes you to do it.

Staff only matter at `open` time, as *supervision*, and that is not what the legend
says.

### (b) Four screens, four different answers to "how many craftsmen have I got?"

With an empty payroll, at the same instant:

| screen | says |
|---|---|
| prompt / `state` | `sch 0 art 0`, "EMPLOY: 0 people ... nobody" |
| `labour` | "ON YOUR STAFF: nobody" |
| `why tx2_retting` | "STAFF NEEDED: 0 scholars, 1 artisans **(you have 1, 0)**" |
| `available` | `1a*` - "you do not have them yet" |
| `ventures` | "free to put behind something new: **1 scholars, 1 craftsmen** (one of each of those is you)" |

`ventures` is the one that matches the engine: the founder silently counts as a whole
scholar **and** a whole craftsman. Everything else tells you that you have nobody,
so a player hires people they do not need.

### (c) `ventures`' NEEDS column is not the number the engine uses

```
2 / <blank> / absurd / <blank>
start horse_collar / start arithmetic_positional / start med_herbal_pharmacy / start fin_lottery
step 2
open horse_collar          -> opened
open med_herbal_pharmacy   -> opened
open fin_lottery           -> REFUSED: needs 0.2 scholars and 0.5 craftsmen ...
open arithmetic_positional -> REFUSED: needs 0.0 scholars and 0.2 craftsmen ...
```
`ventures` lists `horse_collar ... 0 sch 1 cr` and `med_herbal_pharmacy ... 1 sch 1 cr`,
i.e. two whole craftsmen and one whole scholar, and both opened on one founder. The
real requirements are fractional (0.5 cr, 0.2 sch, ...). A player reading the NEEDS
column cannot predict what will open.

### (d) The refusal message contradicts itself

```
open arithmetic_positional
REFUSED: nobody free to keep an eye on it: it needs 0.0 scholars and 0.2 craftsmen
to supervise, and you have 0.8 and 0.2 not already watching something else.
```
It needs 0.2 craftsmen. You have 0.2 craftsmen. It is refused. (The underlying
figures are 0.2 vs 0.15, but both are printed to one decimal as 0.2, so the reason
given is arithmetically impossible as printed.)

### (e) Hired staff evaporate and are never replaced, and nothing says so

`hire artisan 1` then `labour` over time, same game:

| year | Total employed | wage bill | horse_collar revenue |
|---|---|---|---|
| 105 | 0.96 | 241.8 | ramping |
| 115 | 0.68 | 168.9 | 900 |
| 135 | 0.33 | 82.8 | 900 |
| 205 | **0** | **0 den** | **900** |

`state` mentions "attrition (about 3.5%/yr)" only once you have enough staff for the
long EMPLOY block to print; `help labour` ("hire smith 3 - paid every year") never
mentions it, and `auto_hire` is off by default, so a player who hires once quietly
loses the whole payroll over a century.

## Obs 13 — the CREDIT EXHAUSTED axe destroys partly-paid projects, after telling you they are only "halted"

Repro:
```
2 / <blank> / <blank> / <blank>
start arithmetic_positional
start scientific_method
start units_standards
step 5
state
step 2
state
```
At year 105:
```
RUNNING (2):
  arithmetic_positional     66% of your hours spent, 352.4 still owed - waiting on your hours
  scientific_method        100% of your hours spent, 115 still owed - waiting on money: ...
```
At 106:
```
EVENT 106: CREDIT EXHAUSTED: 2 projects halted, unfinished. Nobody will fund new work here for some years
...
RUNNING: nothing
```
"Halted, unfinished" reads as suspended. They are **deleted**: ~795 den already paid
and ~800 founder-hours already spent are gone, and the tech is startable again later
at the full original price. `scientific_method` was destroyed 115 denarii short of
completion after every one of its 350 founder-hours had been spent.

The earlier warning (`CLOSE TO THE LIMIT ... 'stop' a project`) offers a remedy that
costs exactly the same thing - `help commands` says "stop <id>: abandon it, losing
what you have spent" - so both branches lose everything. There is no action that
saves the sunk cost.

The three projects I started are precisely the three the game itself flags:
`available` lists `units_standards`, `arithmetic_positional` and `scientific_method`
under "MOST RESTS ON THESE", and `why arithmetic_positional` calls it "Highest return
on personal hours in the entire tree". Following that advice with the default
400-denarii purse wipes you out by year 106 and locks you out of the game until 118.

---

## Obs 14 — during a credit freeze, `available` says nothing is startable and gives a false reason

At year 115 of the run above:
```
AVAILABLE: 0 startable now
a summary by subject, because the full list is 0 things
...
  what you can pay for: available afford 224
```
and `stuck` says
```
NOTHING YOU COULD BEGIN:
  everything in front of you is either built, already running, or waiting on
  something. 'available' says which.
ARREARS:
  you owe 970 of the 224 anyone will advance you...
A CREDIT FREEZE:
  nobody will fund new work until 118
```
The reason given under "NOTHING YOU COULD BEGIN" ("built, already running, or waiting
on something") is false - 214 things are startable the moment the freeze lifts.
`available` also advertises `available afford 224` to a player who is 970 in arrears
and can afford nothing at all.

---

## Obs 15 — the ledger's "net/yr" is wrong for the year after a hire

```
2 / <blank> / <blank> / <blank>
money            -> Net/yr 3.5, capital 400
hire artisan 1   -> capital 150
money            -> wages 251.5,  Net/yr before the work in hand: -244.2
step 1
money            -> capital 164.6
```
The ledger predicted -244.2 for the year and the year delivered **+14.6**. The 250
taken at `hire` is evidently the first year's wages paid in advance, but the ledger
double-counts it in the forecast. The forecast is the number `state` prints as the
headline "net", so the one number a player plans with is wrong by ~260 den in the
year it matters most.

(`fire artisan 1` immediately after `hire artisan 1` returns nothing: capital stays
at 150. No warning that the hiring fee is non-refundable.)

---

## Obs 16 — a DEAD founder can still start projects, hire staff and earn a living

Repro (mortality ON - answer `y` to the third question):
```
2 / <blank> / <blank> / y
step 40
state
start units_standards
hire artisan 2
step 9
state
```
```
EVENT 138: the founder dies, aged about 73
...
YEAR 140
You: DEAD and ageing, 0 founder-hours free this year
[140 AD | 409 den | you:0 hr ...] > started: units_standards
[140 AD | 409 den ...] > hired: artisan
[140 AD | -90 den | you:0 hr | sch 0 art 2 | rep 2] >
```
The corpse committed 444 denarii to a 300-founder-hour project, hired two artisans,
and then went bankrupt. `work scholar 500` is correctly refused ("you have 0 of your
own hours left"), so the hours check exists - `start`, `hire`, `buy` and `bribe`
simply do not consult it.

Meanwhile the dead founder's *practice* keeps paying: money rose from 402.2 (year
138, alive) to 409.1 (year 140, dead) at +3.4/yr, itemised in `money` as
med_cataract_couching + med_trepanation - i.e. a dead surgeon is still operating.

The run does not end at death; it ends up to eleven years later
(`EVENT 149: RUN ENDS: the founder died without training successors`), and the whole
gap is playable.

Bonus: `EVENT 145: you cannot pay everyone: 0.0 of your staff leave for work that pays`
- an event announcing that zero people did something.

---

## Obs 17 — buying and freeing people produces counts that do not agree with each other

Repro:
```
2 / <blank> / absurd / <blank>
buy slaves 5
labour
buy manumit 2
labour
step 3
labour
```
```
bought: 5 / slaves: 5
LABOUR ... people you own 5 ... HOUSEHOLD PLACES: 5 of 6 used
IN TRAINING: people you bought, learning the work x5, ready 103.0

manumitted: 2 / freedmen: 2 / slaves: 3
LABOUR ... people you own 3, freedmen 2 ... HOUSEHOLD PLACES: 5 of 6 used
IN TRAINING: people you bought, learning the work x6.6, ready 103.0
```
Freeing 2 of 5 people turned "5 learning the work" into "6.6 learning the work"
while the household still holds exactly 5 bodies. Then:
```
EVENT 103: 6.6 of the people you bought finish learning the work
[104 AD | 939109 den | you:2000 hr | sch 0 art 4 | rep 5] > LABOUR
  people you own          3
  freedmen                2
  HOUSEHOLD PLACES: 5 of 6 used
  Total employed: 0     annual wage bill: 0 den
```
Five people bought; 6.6 of them graduate; the prompt then reports 4 artisans;
`labour` reports 0 employed; `state` reports "0 people ... (and 5 in your
household)". Four different numbers for one group of five.

`buy slaves 5` also raised reputation from 5 to 6.7 the moment they were freed, for
1,638 denarii, with no time cost - a cheap one-off reputation purchase for anyone
starting at `artisan` or above.

---

## Obs 18 — `ventures` understates what a concern actually earns by a factor of ~2.24

From a long scripted `absurd` run at year 350 (session saved as
`games/big350.json`), `ventures` and `money` describe the same concerns:

| concern | `ventures` EARNS/YR | `money` ledger row | ratio |
|---|---|---|---|
| crucible_steel | 11,000 | 24,571 | 2.234 |
| lead_chamber | 9,000 | 20,104 | 2.234 |
| finery_puddling | 9,000 | 20,104 | 2.234 |
| interchangeable_parts | 8,000 | 17,870 | 2.234 |
| high_temp_furnace | 7,000 | 15,636 | 2.234 |
| cementation_steel | 6,000 | 13,403 | 2.234 |
| electroplating | 5,500 | 12,286 | 2.234 |
| mirror_amalgam | 5,000 | 11,169 | 2.234 |
| ... | ... | ... | 2.234 |

Adding up the whole `ventures` RUNNING column gives 100,200 den/yr for the 40 open
concerns; the ledger's concern rows add to 224,343. `open <id>` quotes the same
understated base ("it earns 900 a year"), and so does the `state` line "those shut
concerns would clear 20,000 den/yr between them" - the real figure is over twice
that. So the screen a player uses to decide what to open is wrong by 124%.

(The ledger itself is internally consistent: its rows sum exactly to the printed
revenue, including a `what the market will not absorb  -78,913` row that is not
described in `help money`, which lists only practice + opened concerns + workshop.)

---

## Obs 19 — `quote mine coal 500` promises a yearly cost that is not charged for three years, and `close` reports it as zero

```
2 / <blank> / absurd / <blank>
quote mine coal 500     -> "every year it stands: 750" ... "years before it produces: 3"
buy mine coal 500       -> capital 1,000,000 -> 995,500
step 3
money                   -> "mines standing        0"
close coal              -> "closed: ... You stop paying 0 a year."
```
The "every year it stands: 750" only begins in the fourth year. `close` telling you
"You stop paying 0 a year" while the quote said 750 is the kind of thing that makes
a player think the mine was free.

---

## Obs 20 — an event that destroys a fifth of a million-denarius fortune, described as someone else's tenement fire

```
2 / <blank> / absurd / <blank>
buy mine coal 500
step 1 (x4)
```
`EVENT 104: fire in the insula district, where the tenements stand six storeys in
wood: it destroyed 166,021 denarii` - 17.7% of the 937,138 held at the time. See
Obs 7: it is a flat ~18% of liquid capital every time, and it is exactly zero if you
hold no coin ("it destroyed nothing, because you were holding none").

---

## Obs 21 — `withdraw` is a real command that `help commands` does not list

`help eminence` tells you "One command does [lower eminence], and its price is real:
**withdraw** halves your prominence now...". `help commands` - the canonical list -
does not mention `withdraw` anywhere. Typing it works:
```
> withdraw
REFUSED: nobody is watching you closely enough for this to buy anything: prominence
is 0.0 against a danger line of 26...
```
It also calls the statistic "prominence" where `state` calls it "eminence".

---

## Obs 22 — **`commission` takes your money and does nothing at all**

`help commands`: "commission <what>: buy a job rather than a person".
`help labour`: "commission: commission smith 400 - buy a job rather than a person".
`labour`'s own advice: "To get more artisans: hire smith 3 ...; or **commission smith
400 to buy one job instead of employing anybody**".

### It does not reduce a project's bill
`why units_standards` lists `HIRED LABOUR: carpenter 200h, smith 400h`. So buy
exactly that before starting it:
```
2 / <blank> / absurd / <blank>
commission carpenter 200   -> bought for 51 denarii
commission smith 400       -> bought for 115 denarii
start units_standards      -> the bill you have taken on: 444
step 1
money                      -> spent on projects last step: 444
```
Control run without the commissions: `the bill you have taken on: 444`,
`spent on projects last step: 444`. Identical. The 166 denarii bought nothing.

### It does not unblock a labour-starved project either
In Scandinavia 900 (`3`), `arithmetic_positional` wants 2,500 scribe-hours a year and
`labour scribe` says "the town can supply: 419 hours", so it sits at
`waiting on nobody to do the work: scribe (wants 2500 hours a year; this society can
field 419 at most)`. A/B over four years, commissioning the maximum every year:

```
A: start arithmetic_positional / step 1 x4
   -> year 904: 81% of your hours spent, 368.7 still owed
B: start arithmetic_positional / commission scribe 419 / step 1  (x4)
   -> year 904: 81% of your hours spent, 368.7 still owed
```
Byte-identical progress after paying ~900 hacksilver in commissions. (`commission
scribe 2500` is refused: "the scribes here can spare 419 more hours this year", so
commission cannot even in principle exceed the supply that is already blocking you.)

### It does not supervise a concern
```
open fin_lottery -> REFUSED: nobody free to keep an eye on it: it needs 0.2 scholars
                    and 0.5 craftsmen ...
commission artisan 2000 -> bought for 480 denarii
commission scholar 2000 -> bought for 1280 denarii
open fin_lottery -> REFUSED: (identical message)
```

I could not find any state of the game in which `commission` changes any number
except your capital going down.

---

## Obs 23 — `restore` costs **twice** what `open` cost, and the game elsewhere says it costs a tenth

```
2 / <blank> / absurd / <blank>
start fin_lottery / step 3
ventures            -> fin_lottery ... TO OPEN 312
open fin_lottery    -> capital 953,671 -> 953,359   (312)
mothball fin_lottery-> "you stop paying 100 a year ... 'restore fin_lottery' opens it again"
restore fin_lottery -> "back in service for 624 denarii"   (2x)
mothball fin_lottery / step 5 / restore fin_lottery -> "for 624 denarii"  (still 2x)
```
Same with horse_collar: open 150, restore 300.

Meanwhile the engine's own auto-close event says the opposite:
```
EVENT 417: nobody left to keep an eye on 7 concerns, so ... closed. You still know
how; reopen with 'open' once you have the people. The premises and the stock stand
for a few years yet, so reopening soon costs a tenth of what opening did
```
A tenth versus double is a factor of twenty. The `mothball` message quotes no price
at all, and `ventures` shows no restore price for a mothballed concern, so the player
finds out only after paying. Note that `policy auto_shed`, the `CLOSE TO THE LIMIT`
advice ("'mothball' a loss-maker") and `help commands` all encourage mothballing.

---

## Obs 24 — the two hazards `state` puts on screen every single turn never fire

`state` prints, every turn:
```
SCANDAL is dangerous above 25 ...
EMINENCE is dangerous above 26 ...
```
Across two full 500-year runs (one starting with a million denarii, ending with
5,000,000 den, reputation 97 and 131 technologies built), the maxima reached were:

| | maximum reached | danger line |
|---|---|---|
| scandal | 7.8 | 25 |
| eminence | 13.1 | 26 |

Neither got within a factor of two of its threshold. The only thing that ever
generated scandal at all was "your patron dies; ... you are talked about". So an
entire help topic (`help eminence`), the `withdraw` command, `bribe`'s stated primary
purpose ("spend money to reduce a scandal") and the `auto_bribe` policy are all
attached to machinery that, as far as I could drive it, is unreachable.

---

## Obs 25 — the Mexica scenario's own blurb says "no iron", and you can sink an iron mine there

Menu text for option 5: "chinampa agriculture that outyields anything in Europe, and
**no draught animals, no iron, no wheel in practical use**."
```
5 / <blank> / <blank> / <blank>
quote mine iron 500
->  material: iron / tonnes per year: 500 / to sink it: 24,000 / every year it stands: 4,800
```
Relatedly, all five civilisations offer the identical hiring list -
`artisan, carpenter, engraver, furnaceman, glassblower, labourer, mason, master,
merchant, millwright, miner, plumber, potter, sailor, scholar, scribe, smith` -
so Viking-age Scandinavia (population 1,500,000, "no state to speak of") has a
professional scholar market, and the Mexica have plumbers and millwrights. All five
also start with the identical practice, `med_cataract_couching` + `med_trepanation`.

---

## Obs 26 — `bounty` is an irreversible spend with no way to find out the price first

```
2 / <blank> / absurd / <blank>
bounty horse_collar
->  posted: horse_collar
    price: 1,774
    capital: 998,226
```
`why horse_collar` says only "BOUNTY: yes, could be posted as a public prize" - no
price, no description of what you get. What you actually get is the money bill paid
(709.4) and 65% of your founder-hours covered, for 1,774. `quote` explicitly handles
only mines. So the command's entire cost/benefit is invisible until after you have
paid 2.5x the build cost.

---

## Obs 27 — **"a million denarii buys perhaps a tenth off the time, not a different game" is wrong by two orders of magnitude**

The kit-selection screen says of `absurd`:

> "It used to make things worse and no longer does ... What it does NOT do is make you
> a magician: **a million denarii buys perhaps a tenth off the time, not a different
> game.**"

I ran the *identical* 250-year script under both kits. The script: turn on every auto
policy, then every year attempt `start <id>` for all 142 ids returned by
`path point_contact_transistor`, then `step 1`.
(command files `games/cmds_big.txt` and `games/cmds_poor.txt`.)

| kit | technologies built by 350 AD | capital at 350 AD | concerns running | reputation |
|---|---|---|---|---|
| `absurd` (1,000,000 den) | **102** | 871,718 | 40 | 45 |
| `poor_scholar` (400 den, the DEFAULT) | **1** | **-93.8** | 0 | 0.40 |

Not a tenth off the time. A hundred times the output.

I then gave the poor start a *gentler* script - one `start` attempt per year, all auto
policies on, the whole 500 years (`games/cmds_poor2.txt`). Result at the horizon:

```
Ended 600 AD. ran out of horizon (600 AD) without reaching the goal
Capital: -1,227 den   Revenue: 153.7   interest on arrears: 134.9
Credit limit: 219.2 (559% used)     interest on arrears: 11%   paid so far: 20,298
```
**2 technologies in 500 years, and 34 separate INSOLVENCY SETTLED events.**

The mechanism is simple and worth naming: the cheapest item on the road to the goal
is `arithmetic_positional` at **1,032 den**. A `poor_scholar` has **400 den** and
+3.5 den/yr. The game lets you commit to it, and one allowed action puts you in a
bankruptcy loop that the auto policies cannot get you out of.

### The one escape route is the one that is booby-trapped

From the -628.5 den position, `work scholar 1500` every year climbs back to positive
in two years and all is well:
```
start arithmetic_positional / step 1        -> -628.5
work scholar 1500 / step 1  (x15)           -> -331.6, -5.6, +315.6, +631.7, ...
```
`work scholar 2000` - working *harder* - triggers the false insolvency of Obs 8 and
destroys the run. There is nothing on any screen that distinguishes 1500 from 2000.

---

## Obs 28 — the end-of-run summary contradicts itself about what you built

```
2 / <blank> / <blank> / <blank>
step 500
```
```
  the horizon at 600 AD is reached. You built 0 things of your own and did not
  reach point-contact transistor.
  ended in 600 AD
  you built 0 things; this society already had 139
  -1,227 in hand, 0 people, reputation 0.10, 0 concerns running

  THE ROAD TO POINT_CONTACT_TRANSISTOR
    146 nodes in all; you had 4 of them and 142 were still to build
```
"you built 0 things" and "you had 4 of them" in adjacent lines. (4+142=146 is
internally consistent, so the intended meaning is presumably "4 of the road's nodes
came free with the society" - but the summary never says so and the two figures read
as a straight contradiction.)

---

## Obs 29 — smaller things

* **`available afford N` mislabels its own count.** Plain `available` says
  "AVAILABLE: 207 startable now"; `available afford 1766` in the same turn says
  "AVAILABLE: **193** startable now". Both use the words "startable now" for two
  different quantities.
* **`available limit -5` is accepted** and prints "AVAILABLE: 207 startable now /
  **1-202**" - a negative limit silently drops five entries off the end.
* **The credit line is not a limit.** `help money`/`help economy`: "as far as somebody
  will lend you and no further." Observed: `Credit limit: 220.5 (**469% used**)`,
  and in the 500-year poor run `Credit limit: 219.2 (**559% used**)`.
* **`bribe` validates against a number it never spends**: `bribe 1000000` with 400 den
  is "REFUSED: you have 400 denarii", but `bribe 400` only ever takes 76.
* **`destitute` (0 den) has a *better* net income than `poor_scholar` (400 den)** -
  +9.5/yr vs +3.5/yr - because living costs are a sixtieth of capital. The kit blurb
  says "You must earn your first meal"; in fact you are 6 den/yr better off than the
  default kit from the first turn.
* **`save`/`load` drifts slightly.** A game saved and reloaded reported
  `annual wage bill: 675.3` before and `674` after, and the trajectory diverged by
  1 den over the next 20 years. Harmless in size, but the save is not exact.
* **The resume line is wrong outside the repo root.** The game writes
  `rome_100ad.json` into the *current* directory and then prints
  `python3 rome/sim/simulator.py play --session rome_100ad.json`, a path pair that
  can only both be right if cwd is the repo root.

---

## Note on a moving target

The repository was being edited while I tested (`rome/sim/engine` mtime 20:01 and
`rome/sim/test_regressions.py` mtime 20:20, during this session). I re-ran every
top finding against the build as of ~20:30 and they all still reproduce, **except**:

* **Obs 9** (`open` refusing to use credit while `start` may) no longer reproduces.
  At ~19:50 `open arithmetic_positional` at -628 den gave
  "REFUSED: opening it costs 155 denarii ... and you have -628"; at ~20:30 the same
  sequence opens it and charges the 155 to credit (capital -628.5 -> -783.3). Treat
  Obs 9 as fixed, and the rest as live.

---

## Files in `games/`

* `cmds_big.txt` / `big1.txt.gz` — 250-year `absurd` script and its output (102 techs by 350 AD)
* `cmds_big2.txt` / `big2.txt.gz` — its continuation to the 600 AD horizon (131 techs)
* `cmds_poor.txt` / `poor1.txt.gz` — the identical script on `poor_scholar` (1 tech by 350 AD)
* `cmds_poor2.txt` / `poor2.txt.gz` — gentle one-start-a-year `poor_scholar`, all 500 years (2 techs, 34 insolvencies)
* `path.txt` — the 142 ids from `path point_contact_transistor`
* `c1.txt` … `c15.txt` — the small repro command files used in `transcript.txt`
* `d1/d2.txt`, `e1/e2.txt` — determinism comparisons
* `*.json` — session saves produced along the way
