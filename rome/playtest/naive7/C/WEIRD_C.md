# WEIRD_C — playtest notes

Playtester C. Brief: play strangely. Rome, 100 AD, fog of war ON, poor scholar purse, founder does not age.

Rule I'm following: only the running program tells me anything. No source, no data files, no docs, no other notes.

---

## Session log

### 0. Before I start

Expectation: I have no idea what this game is. The path says `sim/simulator.py` and the
setup asks about "Rome, 100 AD", "fog of war", a "starting purse" and whether a "founder"
ages. So I'm guessing: some kind of historical institution-builder where you found a
thing (a school? a business? a household?) and run it across years, with a person at
the head who normally dies of old age unless you turn that off. "Poor scholar" purse
suggests starting broke. Fog of war suggests I can't see the whole map/options list.

Let's find out.

### 1. Setup

Answered: `2` (Rome under Trajan, 100), `y` (fog of war ON), `poor_scholar` (400 den),
`n` (founder does not age).

Title screen: "ONE PERSON, AND EVERYTHING THEY KNOW". So it's a lone-time-traveller
tech-tree game. Start: 400 den, 2000 hr, sch 0, art 0, rep 5.

Session file: `rome_100ad.json`, resumed with
`python3 rome/sim/simulator.py play --session rome_100ad.json`.

Note already: the resume line it prints is a RELATIVE path (`rome/sim/simulator.py`)
which only works from `/home/user/test`, but the save file is in my cwd
(`.../naive7/C`). So the exact command it tells me to type cannot work from either
directory. Minor, but it's the one instruction it gives you and it's wrong.

**Expectation before playing:** the status bar shows `rep 5` and the game named
reputation first among things it tracks, so I am going to *assume reputation is the
score*. My persona for this run: **The Publicist.** I will chase fame and staff, and
refuse to build technology. I expect the game will keep offering me tech and I will keep
saying no. I want to see whether it notices, or whether it just quietly lets a Roman
celebrity with no inventions run out the clock.

### 2. Orientation (all from `help`, `state`, `available`, `labour`, `money`)

- Real goal: **build a point-contact transistor before 600 AD.** I have 500 years.
- 207 things startable now; 137 technologies "granted for free".
- I already earn 233.5 den/yr from `med_cataract_couching` and `med_trepanation`,
  which I never chose. Apparently the free grant includes running an eye-surgery
  practice. Slightly odd to be told "you arrive alone with nothing" and then find I
  have a medical income on turn one.
- `help eminence`: fame + visible wealth = eminence, and past 26 it rolls yearly for
  your ruin, and *nothing lowers it*. So the game explicitly warns that my chosen
  persona (get famous) is the way to die.
- Debt exists: credit limit 1,367 at 11%.
- Wages: labourer 125 den/yr, master 500, scholar 625. Market can supply 22,500
  labourer-hours.
- `help economy` prints the *identical text* as `help money`. Two topics, one body.
  Small thing, but `commands` lists them as separate topics.

**Plan, committed to for the whole run:** I am "The Publicist". I will
  (a) hire the largest staff the game will let me and never give them work,
  (b) chase reputation/eminence deliberately, straight past the warning,
  (c) build as close to nothing as I can,
  (d) fund it with day labour and debt.
I want to find out if the game has anything to say to a person who does the opposite of
everything it advised in the first five minutes.

**Expectation for the next move (`hire labourer 500`):** I have 400 den and a 1,367
credit limit. 500 labourers = 62,500 den/yr. I expect a refusal along the lines of "you
cannot afford this". If it *lets* me, that's a much more interesting bug: a man with 400
denarii employing five hundred people.

### 3. Probing `work` — and a thing the game does not tell you

`hire labourer 500` -> REFUSED, "costs 62500 denarii **in advance** and you have 400".
So wages are paid up front out of capital, and credit does not count. Good, clear.

Edge cases, all handled cleanly:
- `work engineer 100` -> refused, the trade does not exist here. Nice error.
- `work labourer 999999` -> refused, "you have 2000 of your own hours left, not 999999".
- `work labourer -500` -> refused, "hours must be greater than zero".

`work scholar 2000` -> earned 640.6 den. Note 2000 hr x 0.40 den/hr = 800, so I was paid
**80%** of the listed scholar wage. The `labour scholar` screen says "wage: 0.40 den/hr"
with no hint of a discount. I don't know why I get 0.32. Nothing on screen explains it.

**The thing I did not expect at all:** after working, `money` shows **Revenue: 0**. My
233.5 den/yr of medical income vanished. Working it out: the cataract-couching and
trepanation income must be paid *out of my founder-hours*, and I had spent all 2000. The
game never says this anywhere. `state` lists the practices under nothing, `money` just
lists them under "from:" as if they were passive rents, and then they silently disappear
from the ledger with no line saying "you had no hours for your practice this year".
That's the first place the display lost track of what was going on from my side.

Two more oddities in the same breath:
- "living and appearances" fell 230 -> 225.6 the moment my revenue went to zero. My cost
  of living apparently tracks my income. Plausible modelling, zero explanation.
- **Credit limit fell from 1,367 to 1,250 while my capital went UP from 400 to 1,040.**
  I got richer and the bank liked me less. Presumably credit keys off revenue, but on
  screen it reads as nonsense.

**Next expectation:** I will now do the same thing every year for a long time —
`work scholar 2000`, `step 1`, repeat. I expect: money piles up at ~+410/yr, reputation
stays 5 forever because scholarly day-labour is anonymous, and the game says nothing at
all about the fact that the person who came to build a transistor has spent a decade
copying manuscripts. I predict no nudge, no comment, no event.

### 4. Fifty years of copying manuscripts (100 -> 150 AD)

I ran `work scholar 2000` + `step 1` fifty times. Results:

- Capital 400 -> 9,891 (peak, ~128 AD) -> **9,408 and falling** by 150.
  There is a hidden equilibrium: "living and appearances" scales with wealth, so a
  day-labourer saturates around 9-10k denarii and then slowly *loses* money. I like this
  — it's the one place so far where the sim pushed back on a dumb strategy on its own,
  emergently, without a lecture.
- **Reputation decays if you don't do anything: 5.0 -> 1.5 over fifty years**, about
  -0.1/yr. So the game does track that I'm doing nothing. But it never *says* so. There
  is no line anywhere like "you are forgotten". You have to notice the number.
- **Eminence rose the whole time, 0 -> 0.28, while reputation fell 5 -> 1.5.** So a
  complete unknown who is quietly hoarding gold becomes more "eminent" every year.
  `help eminence` told me eminence "rises with how well known you are and how visibly
  rich" — but here it rose monotonically while how-well-known-I-am *collapsed*. Those
  two numbers moving in opposite directions for fifty straight years reads wrong.
- Free granted technologies went 137 -> 139 on their own. The world invents things
  without me. Nothing announced this; I only caught it by diffing two `state` screens.
- **Fifty years, zero events.** Not one line of flavour text, not one hazard, not one
  interruption. The `step` output is byte-identical every year apart from the numbers.
  This is the emptiest half-century in Roman history.

Expectation vs reality: I predicted "no nudge, no comment, no event" and that is exactly
what happened, which is the correct prediction and the disappointing one.

**Next: the enormous useless staff.** I have ~9,400 den. A labourer is 125/yr. I am going
to hire 70 labourers and give them absolutely nothing to do, then step. Expectation: the
wage bill is 8,750/yr against ~640/yr of income, so I should be destitute within one
year and, per `policy`, "people you cannot pay leave". I want to see whether the game
narrates that or just silently deletes them. I also want to know whether hand-hiring
respects the housing limit that `auto hire` mentions ("toward what you can house").

### 5. The enormous staff, attempt one — and the slave loophole

`hire labourer 70` ->
  "REFUSED: you can supervise, house and teach **6.00 more people**, not 70".
So there IS a cap on staff, tied to me. Good design; kills my "hire 500 idlers" plan
through the front door. (Also note "6.00 more people" — a formatted float for a count of
humans.)

Also, still counterintuitive: **capital 9,408, credit limit 487.** I have gone from 400
denarii and 1,367 of credit to 9,408 denarii and 487 of credit. Getting nine times richer
made lenders trust me a third as much. Whatever formula is behind this, on screen it is
simply backwards.

So I went round the back:

- `buy slaves 70` -> refused, but only on **price** (39,265 den, "561 each after the
  market moves against a purchase this size" — nice touch, bulk buying moves the market).
  Not one word about the supervision cap.
- `buy slaves 6` -> **bought**. `buy slaves 1` -> **bought**. I now hold 7 people.

**Finding: `buy slaves` does not check the supervise/house/teach cap that `hire` checks.**
I was told to my face that I could take 6.00 more people, and then took 7 by a different
verb, with no complaint and no penalty.

It gets stranger. After buying, `labour` shows:

    ON YOUR STAFF:
      nobody
    IN TRAINING:
      None x3.3, ready 153.0
      None x0.55, ready 153.0
    Total employed: 0     annual wage bill: 0 den

and `state` says "EMPLOY: 0 people".

Three separate problems in five lines:
1. The trade of these people prints as the literal string **`None`** — a null leaking
   straight into the display.
2. They are **fractional**: `x3.3` and `x0.55`. 3.3 people and 0.55 of a person.
3. **3.3 + 0.55 = 3.85, but I bought 7.** Over half of the people I paid 2,358 denarii
   for are not on any screen the game will show me. `state` says I employ 0, `labour`
   says nobody, and the only evidence they exist is two lines of `None`.

The game has lost track of who is in my household. This is exactly the kind of thing I
was told to look for.

Expectation going in: I assumed slaves would either be blocked by the same cap or appear
as staff with a purchase price and no wage. Instead they went into a "training" limbo as
`None`. `help economy` says "buy slaves 5" and "manumit ... they are untrained for three
years", which is presumably the three-year training — but nothing said they'd be
invisible or fractional in the meantime.

### 6. Ten bought people, three different headcounts

Stepping to 153 produced:

    EVENT 153: 6 of the people you bought finish learning the work
    EVENT 153: 1 of the people you bought finish learning the work
    EVENT 153: 3 of the people you bought finish learning the work

6 + 1 + 3 = 10, correct. So the engine knows perfectly well I bought ten. But it printed
them as three separate events (one per purchase batch) rather than "10 of the people you
bought", which reads as though three unrelated things happened in one year.

After they finish, the prompt bar reads `art 7`. But:

    labour  ->  ON YOUR STAFF: nobody     Total employed: 0
    state   ->  EMPLOY: 0 people, 0 den/yr in wages / nobody

**Three screens, three answers, same household: 10 bought, `art 7` in the status bar,
0 everywhere else.** If I only ever looked at `labour` or `state` — the two screens whose
whole job is to tell me who works for me — I would believe I own nobody.

`state` did eventually print the explanation, but only once and in the wrong place:

    EMPLOY: 0 people, 0 den/yr in wages
      nobody
      these are continuous full-time-equivalents, not a count of whole people:
      ... 1.32 artisans is the wage and output of one artisan plus a third of another's.

That paragraph is attached to the word "nobody" and cites "1.32 artisans", a number that
appears nowhere on the screen or in my game. So the one explanation of the headcount
model is printed underneath a headcount of zero, using an example figure from somewhere
else.

Also, in 150 AD: `EVENT 150: fire in the insula district, where the tenements stand six
storeys in wood`. My capital moved 5,909 -> 4,522 across that step; upkeep accounts for
maybe 370 of it, so the fire seems to have cost me roughly a thousand denarii. **The
event line never says so.** It's atmosphere with an invisible bill attached. I own no
buildings and employ nobody, so I have no idea what of mine burned.

### 7. Manumission is free reputation

    buy manumit 10
    manumitted: 10   freedmen: 10   slaves: 0

Capital: **unchanged** (3,419 before, 3,419 after). Reputation: **1.4 -> 4.2**, tripled,
instantly, in the same year, for free. Artisan-equivalents `art 7 -> art 12`.

So freeing people costs nothing, triples your standing and nearly doubles your output. The
game frames it morally ("it is the decent thing") and it is also, mechanically, the single
best-value action I have found in 54 years of play. That combination is worth a look:
right now the optimal play is to buy people purely in order to free them.

I was about to test exactly that — buy 5, free 5, buy 5, free 5, and see whether
reputation just keeps going up — when the game broke.

### 8. The program stopped working mid-session

    ImportError: cannot import name 'load_state' from 'engine.protocol'

Every invocation, three times in a row, including a bare `state`. I have not touched
anything in the repository except this notes file and my own save. Someone or something is
editing the engine underneath me while I play. Recording the time and moving on; I'll
retry. My save `rome_100ad.json` is at 154 AD with ~3,419 den, rep 4.2, 10 freedmen.

### 9. The engine came back, and reputation turns out to be farmable

The ImportError cleared on its own after a few minutes; my save resumed at 154 AD exactly
where it was. (So the crash was somebody editing the engine, not my save. Save integrity
across it: fine.)

**Reputation is farmable in a single turn, with no time cost.** In year 154, without ever
calling `step`, I ran `buy slaves 2` / `buy manumit 2` four times:

    rep 4.2 -> 4.8 -> 5.3 -> 5.8 -> 6.2      (freedmen 10 -> 18)

Every cycle is +0.5 reputation for about 660 denarii and zero elapsed time. Nothing caps
it, nothing comments on it, and there is no cooldown — the only limit is cash. My whole
"become famous" persona reduces to a shopping loop I can run as many times as I can
afford in one afternoon of 154 AD. A player trying to be famous will find this in about
four minutes and it is strictly better than anything the game recommends.

Two other things fell out of it:
- `art` stayed frozen at 12 while freedmen went 10 -> 18, because new ones are untrained
  for 3 years. Fine, but the status bar gives no hint that 8 people are pending.
- Buying moves the price against me *within* a year (626 -> 666 -> 703 -> 737 for two
  slaves each time) but resets between years. Nice touch.

### 10. "RUNNING: nothing", while running two things

    ventures  ->  RUNNING: nothing
    state     ->  RUNNING: nothing
    money     ->  Revenue 233.5/yr from med_cataract_couching, med_trepanation

`open med_cataract_couching` -> "REFUSED: you are already doing that". So the game knows
I'm doing it. It just refuses to list it under the heading called RUNNING, on the two
screens whose job is to list what I'm running. The refusal message is good and explains
the distinction (society's skill vs. my concern) — but it only appears if you guess to
type `open` on something you already have.

`why med_cataract_couching` says **REVENUE: 500 den/yr**. The ledger pays me **166.7**.
Exactly one third. Nothing on either screen accounts for the factor of 3. If I were
planning around the `why` numbers — which is what `why` is for — every projection I made
would be 3x too high.

Same screen, same second, two different headcounts:
    ventures -> "free to put behind something new: 1 scholars, **12.5** craftsmen"
    why      -> "STAFF NEEDED: 1 scholars, 0 artisans (you have 1, **11.5**)"
Nothing happened in between.

### 11. Poverty, on purpose

Freeing 18 people has quietly wrecked me. "living and appearances" has gone
365 -> **1,044 den/yr** and net is **-810.8/yr** against **688 denarii** in hand. I did
the decent thing eight times and it is going to bankrupt me within the year.

And the credit line keeps moving the wrong way: 9,408 capital -> 487 credit;
688 capital -> **1,675** credit. Consistently, the poorer I get the more Rome will lend
me. I now have more than twice the credit I started the game with, on a tenth of the
money.

**Expectation for the next move:** I am going to step ten years and do nothing —
no work, no projects. I expect to burn through 688 den, then through 1,675 of credit at
11%, and then per `policy` ("people you cannot pay leave, creditors take what they are
owed") something should take my freedmen away and I should hit some kind of floor. I want
to see whether the game has a bottom, and whether it tells me I've hit it.
