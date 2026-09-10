# Playtest notes — naive10/c

(Adversarial playtest of `python3 rome/sim/simulator.py`. Notes appended as I go.
TOP PROBLEMS section will be added at the top at the end.)

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

## Obs 9 — `start` may borrow; `open` may not — so you can permanently strand a finished project

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
