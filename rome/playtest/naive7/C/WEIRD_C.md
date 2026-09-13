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

### 12. Bankruptcy, and the dead who finish their apprenticeships

`step 10` from 154. The events, in order:

    EVENT 155: interest on 1036 denarii of arrears at 10.8% a year
    EVENT 156: the household disperses: 18 people leave, because you can no longer feed them
    EVENT 156: INSOLVENCY SETTLED: most of the debt is written off and you still owe about
               557 denarii. Your name is worth less for it (reputation -12), and you keep
               your knowledge and your practice
    EVENT 157: 6.2 of the people you bought finish learning the work
    EVENT 157: 3.4 of the people you bought finish learning the work
    EVENT 157: 2.7 of the people you bought finish learning the work
    EVENT 157: 2.3 of the people you bought finish learning the work
    EVENT 159: banditry or a frontier war disrupts supply

**The eighteen people left in 156 and then completed their training in 157.** The game
announced their apprenticeships finishing a year after it announced they had all walked
out because I could not feed them. Nobody was there to finish anything.

And the numbers are wrong even on their own terms. I bought in batches of 10, 2, 2, 2, 2 —
five purchases. The completion events are four, and they read 6.2, 3.4, 2.7, 2.3, which
sum to 14.6, not 18 and not any of my batch sizes. Earlier, the same events for the first
ten read "6 ... 1 ... 3", which were whole numbers and did sum correctly. So the same event
prints whole people sometimes and fractions of people other times.

The insolvency itself is good writing and works: debt written off, reputation -12
(6.2 -> floored at 0.10), knowledge and practice kept. No complaints there.

Also, in 165: **"EVENT 165: Antonine plague: you had nothing it could take."** That is the
first time in 65 years the game has acknowledged that I have achieved nothing, and it is a
genuinely great line. More of that, please.

### 13. A real bug: the ledger's Net/yr ignores debt interest

Three consecutive years, doing nothing at all:

    Capital -1,052   Net/yr: 9.5   (interest paid so far 874.6)
    Capital -1,157   Net/yr: 9.5   (interest paid so far 989.3)
    Capital -1,274   Net/yr: 9.5   (interest paid so far 1,115)

`money` reports **Net/yr +9.5** while my capital falls by **105, then 117**, and the
amount is *accelerating*. The Costs block lists upkeep, living, wages and mines — and no
line at all for interest — so the totals it prints simply omit the largest thing happening
to my money. The rate is even printed two lines lower ("interest on arrears: 11%"), so the
screen contains everything needed to be right and still says +9.5.

A player reading `money` sees "I'm slowly recovering". They are in fact compounding at 11%.
This is the one thing I found that I'd call an outright bug rather than a rough edge.

Related: **Capital -1,052 with "Credit limit: 224".** I am five times past my own credit
limit and the game let me get there and does nothing about it. The credit limit appears to
be decorative once you are already underwater.

**Expectation next:** I will now do the thing I most wanted to try — **nothing, for a
hundred years.** `step 100`, no commands. I predict the debt compounds to something absurd
(11% for a century is ~14,000x), and I want to know whether insolvency fires a second time
or whether the first one is a one-off and I just accumulate an impossible number. I also
expect to see the Plague of Cyprian, the third-century crisis and the debasement go past.

### 14. A hundred years of doing absolutely nothing (166 -> 266)

One command: `step 100`. Highlights:

    EVENT 166 / 240 / 250 / 260 : INSOLVENCY SETTLED ... you still owe about 77 denarii.
                                  Your name is worth less for it (reputation -12)

**Insolvency is a repeatable free debt-wipe.** It fired five times. Each time it settles
me at *the same* ~77 denarii owed, and each time it announces "reputation -12" against a
reputation that has been floored at 0.10 since the first one. So after the first
bankruptcy there is no penalty at all: I sit in a stable ten-year orbit — accrue interest,
get wiped, repeat, forever. A player who wants to never think about money again can simply
stop paying and the game will keep resetting them.

    EVENT 240/243/246/252/265: Third century crisis: a site is sacked

I own no sites. It said this five times. Compare the plague, which correctly says
**"Antonine plague: you had nothing it could take"** and **"Plague of Cyprian: you had
nothing it could take"**. So one hazard family checks whether I have anything and the other
doesn't. The sacking line reads like something is happening to me when nothing is.

Good things: the nag banner does eventually appear and it is well written and specific —
"!! YOU HAVE BEEN IN ARREARS 29 YEARS AND YOU LOSE 66 DENARII A YEAR, SO NOTHING YOU START
WILL EVER BE PAID FOR ... it is escapable ... work for wages". That is the game noticing me,
110 years late but correctly.

### 15. The coin loses 99% of its value and wages don't move

    EVENT 190: Currency debasement: the coin is worth 6% less
    EVENT 205: ... 62% less
    EVENT 220: ... 85% less
    EVENT 235: ... 94% less
    EVENT 250: ... 97% less
    EVENT 265: ... 99% less

My practice income did erode: 233.5 -> 153.7 den/yr. But:

    labour labourer  ->  a year of one: 125 den   wage: 0.07 den/hr   (year 100: identical)
    labour scholar   ->  a year of one: 625 den   wage: 0.40 den/hr   (year 100: identical)

**The labour market has not moved by a single denarius in 166 years, through a 99%
debasement.** So after the currency collapses, day labour pays exactly what it did under
Trajan while my professional practice has lost a third of its real value. In real terms
`work scholar` is now the best-paid activity in the game *because* the empire's money
failed. That cannot be intended, and it's the kind of thing a contrary player finds
immediately: the response to hyperinflation is to go get a day job.

### 16. Save-scumming: deterministic in the numbers, not in what it tells you

`save snap1.json`, `step 5`, `load snap1.json`, `step 5`, `load`, `step 5`. All three
runs: identical money (-76.7), identical reputation, identical insolvency event in 270.
Good — the RNG is properly seeded off the state, so reloading does not reroll the dice.
I checked this three times because save-scumming is the first thing I try in any game.

But one event went missing. Run 1 printed:

    EVENT 266: Third century crisis: trade and output fall to 65% of normal

Runs 2 and 3, from the identical save, did not print it — while producing identical
numbers. Tighter test at 271, same result: `save s2.json` / `step 1` prints
"EVENT 271: Third century crisis: trade and output fall to 65% of normal";
`load s2.json` / `step 1` prints nothing and lands on the same -157.9 den.

Then I loaded the very same file in a **fresh process** — and the event printed again.

    same file, in-process `load` + step  ->  event silently suppressed
    same file, fresh process   + step    ->  event announced

So `load` does not clear whatever set remembers which hazard announcements have already
been made; it survives the load. The simulation is right and the narration is wrong. The
practical effect is that a player who save-scums in-process is quietly shown a *less
eventful* world than one who quits and comes back, and will conclude the crisis stopped.

### 17. Debt makes the entire tech tree disappear

While at -157 den, `available all` printed:

    AVAILABLE: 0 startable now
    1-0
    ID   NAME   COST   HOURS   YEARS   RISK   EARNS/YR   UPKEEP   RESTS
    (nothing)

209 things became 0 because I was 157 denarii overdrawn, including the 5-denarius eraser.
The pagination line renders as **"1-0"**. If a new player wandered into debt early — very
easy, living costs run ahead of a poor scholar — the game would show them an empty world
with no explanation on that screen at all. (The `state` nag does explain it, elsewhere.)

### 18. "A site is sacked" takes 60% of your money and doesn't say so

Working my way out of debt, year 283:

    EVENT 283: Third century crisis: a site is sacked
    money before step: 4,490      money after step: 1,685

That is roughly **2,700 denarii, about 62% of everything I had**, removed by an event
whose entire text is "a site is sacked", at a moment when `risk` was telling me
"technologies at risk: **0**" and "hedge: nothing yet", and when `state` said I own
nothing and employ nobody. I have no sites. The same event line had already fired five
times during my idle century and cost me nothing, because I had nothing.

So: the biggest single financial hit of my whole game arrived with no number attached, no
mention on any screen, and a name that refers to property I do not own. Contrast, again,
the plague's "you had nothing it could take", which is exactly the right treatment.

### 19. 192 years pass and the tech tree has not moved a denarius

Year 292 vs year 100, `available`:

    year 100: 207 startable. cheapest: hom_eraser_breadcrumb 5 den. identity_cover 1,580.
    year 292: 209 startable. cheapest: hom_eraser_breadcrumb 5 den. identity_cover 1,580.

Between those two screens the currency lost **99%** of its value, the third century crisis
cut trade and output to 65%, and Diocletian is about to fix wages and prices on pain of
death. Wages: unchanged. Project costs: unchanged. Prices: unchanged. The only price in
the game that responds to the debasement is my own revenue. The rest of the economy is a
fixed price list wearing a century of monetary collapse as flavour text.

**Expectation for the next move:** I have 4,578 den and I am going to try to
**`start` all 209 things at once** — run everything, finish nothing. I expect the first
few dozen cheap ones to be accepted and then a refusal on money or on staff ("STAFF
NEEDED" appears on the `why` screens and I employ nobody). What I actually want to know is
whether there is any cap on concurrent projects, because there is no mention of one
anywhere in `help`.

### 20. Twenty projects at once: 4,577 denarii buys the entire third century

`start` on all 209 ids: **20 accepted, 189 refused**, all with the same refusal, and it is
a genuinely excellent one:

    REFUSED: you already owe 4,314 denarii on work in hand; this would take it to 4,914,
    and between cash and credit you can raise 4,866. Finish or stop something first.

Concrete, numeric, tells me the fix. Best message in the game so far. And there is no
concurrency cap at all beyond money — 20 simultaneous projects, no complaint.

Then `step 5`, and **all twenty finished in the first year.** 2,000 founder-hours cleared
30h, 40h, 450h (`arithmetic_positional`, listed as CALENDAR FLOOR **1 year**) and a
tethered observation balloon, in the same twelve months. Three of them failed and retried
and *still* finished by 293.

The scoreboard consequence: **reputation 0.20 -> 30.6 in five years.** Compare my earlier
manumission grind, which cost me my entire fortune to move reputation from 1.4 to 6.2.
Completing twenty of the cheapest possible items is worth five times as much fame as
freeing eighteen people. So the actual fame engine in this game is "finish lots of small
things at once", and it is available to anyone with ~4,500 denarii and one turn.

A `scandal` of 1.4 appeared at the same time, from nowhere. Nothing said why. There is a
`bribe` command for scandal but no screen that explains what caused it.

Reporting problems in that one step:
- Every completion is announced **twice**, in two different formats:
  `COMPLETED 292: Composting` and `EVENT 292: completed: Composting. You know how...`.
  Forty lines for twenty events, in two interleaved orderings.
- `state` now has **two headings that both say RUNNING**:
  `RUNNING: nothing` and, two lines later, `RUNNING AS CONCERNS: 0`.

### 21. `start` is blocked by debt; `open` is not

At -1,167 denarii, `available` showed me **0 startable things** — the debt gate is
absolute.

Then I opened **fourteen** concerns in the same breath, paying to open each one, and drove
myself from -1,167 to **-1,649**. Not one word of objection. So being overdrawn stops me
from beginning a five-denarius eraser but does not stop me from taking on fourteen new
businesses on credit I do not have.

While doing it I hit the one real constraint, and hit it in the stupidest possible order:

    REFUSED: nobody free to keep an eye on it: it needs 0.0 scholars and 0.2 craftsmen to
    supervise, and you have 1.0 and 0.1 not already watching something else.

I had opened the ventures **alphabetically**. By the time I reached `arithmetic_positional`
— the one worth 300 den/yr, the most valuable thing I own — my last fraction of a craftsman
was already committed to a **tethered observation balloon that earns 0 and costs 20 a
year**. The game let me spend my entire supervisory capacity on three things that earn
nothing at all (balloon, lightning conductor, truss) and then told me I was too busy to run
the profitable one. `ventures` lists EARNS/YR right there in the table and never once
suggests that opening order matters or that supervision is scarce.

Also the same number renders differently on adjacent screens: the refusal says the venture
"needs 0.0 scholars and 0.2 craftsmen"; the RUNNING table for those same ventures prints
"0 sch 0 cr", and one of them "0 sch 1 cr". Rounded to death in one place, not the other.

**Expectation next:** revenue is now 837.6/yr against 250.5 upkeep, and I'm 1,649 in debt.
I expect the concerns to dig me out. But I also expect another INSOLVENCY, and this time I
actually own things — so I want to see whether bankruptcy takes my ventures away, or
whether it still just wipes the debt and says "reputation -12" at a reputation of 31.

### 22. Parser robustness (mostly excellent, one hole)

Good: `why nonexistent_thing` -> "you have never heard of any such thing ... Did you mean:
met_investment_casting, sea_lead_sheathing". `why`/`start`/`stop`/`bounty`/`hire` with no
argument all give a tailored usage line. `fire labourer 5` -> "you employ no labourers".
`foo bar baz` -> "no command called 'foo'". A pasted `{"cmd":"state"}` works, as documented.
`path` under fog gives a lovely in-fiction refusal ("nobody can lay out a road to somewhere
they have not been").

The hole: **`step 0` and `step -5` are correctly refused ("years must be >= 1"), but
`step abc` silently advances one year** with no message at all. Garbage is treated more
permissively than a wrong number, and it costs you a year of game time you didn't ask for.

### 23. `bribe` sells a hidden stat that no screen will show you

`bribe 100` with **scandal already at 0**:

    bribed: scandal 0.00 -> 0.00 for 100 denarii; advocacy and piety bought as well:
    protection 0.16 -> 0.23

I ran it repeatedly. 700 denarii took protection from 0.07 to 0.37, at which point:
"you have no scandal to answer and you are already as protected as money can make you
here, so this would buy nothing."

So `bribe` is really two things: scandal removal, and a cheap purchase of a permanent
defensive stat. `help commands` describes it only as "spend money to reduce a scandal", and
`policy` as "pay your way out of a scandal before it kills you". **`protection` appears on
no screen anywhere** — not `state`, not `state full:true`, not `risk`, not `money`. The
only way to discover it exists, or to read its current value, is to bribe and watch the
message. For 700 denarii — a seventh of my net worth at the time, and pocket change later —
this is the cheapest thing in the game and it is completely undiscoverable.

### 24. The one refusal that doesn't tell you the price

Everything in this game refuses with numbers. `quote mine coal 500` is a model of it:
"to sink it 4,500; every year it stands 750; years before it produces 3; you have 4,760;
you can afford about 528.9". `quote mine gold 5000` cheerfully quotes 800,000,000 denarii
to sink and 210,000,000 a year, and tells me I can afford 0.03 tonnes. Great.

But:

    buy forest 100      -> REFUSED: cannot afford 100 ha of coppice woodland (you have 4760 denarii)
    buy forest 100000   -> REFUSED: cannot afford 100000 ha of coppice woodland (you have 4760 denarii)

Identical message for a thousandfold difference in order. **No price is ever named, and
there is no `quote forest`** — `help money` says "ASK THE PRICE FIRST with quote mine coal
500" for mines and says nothing of the sort for forest. So coppice is the one purchase in
the game whose price you cannot discover except by binary-searching refusals.

**Expectation for the endgame:** back to being The Publicist. Completing 20 cheap things
took reputation from 0.2 to 30.6, so I'm going to repeat that as hard as my money allows —
start everything I can afford, step, repeat — and drive reputation as high as it will go.
The game has warned me from the first help screen that eminence past **26** rolls every
year for my ruin, and that *nothing lowers it*. I intend to walk straight into that. I
expect either (a) to be ruined, which would be the game working exactly as advertised, or
(b) to find that eminence, which after 218 years of play is still **0.89**, is on a scale
that a normal game never reaches, in which case the loudest warning in the game is
decoration.

### 25. Chasing fame: 8 rounds of "start everything, step 6 years" (318 -> 366)

Expectation was (a) ruin by eminence or (b) eminence turns out to be unreachable. It was
firmly (b).

    year 324:  rep 61.4   eminence 2.9    money  -2,153
    year 330:  rep 62.9   eminence 4.9    money -12,040
    year 336:  rep 53.1   eminence 5.3    money -12,736
    year 366:  rep 43.6   eminence 3.1    money  -7,215

**Peak reputation 63, peak eminence 5.3, danger line 26.** I built 79 technologies, held
14 businesses and was the most famous man in the empire, and I got to a fifth of the line
that `help eminence` calls "the one hazard no patron, no bribe and no reputation protects
you from". Every `state` screen for 500 years carried the words "0% chance of ruin this
year". The most dramatic warning in the game — with its own help topic and its own Sejanus
anecdote — never once became relevant to a player actively trying to trigger it. Either
the thresholds want re-scaling, or the help topic is advertising a mechanic that only
exists for a strategy nobody plays.

Meanwhile the actual failure state is money, and I hit it properly:

    EVENT 339: CREDIT EXHAUSTED: 12 projects halted, unfinished. Nobody will fund new work
               here for some years
    EVENT 339: creditors took what they could: 4 concerns closed and sold up:
               air_observation_balloon_tethered, civ_truss_triangulated,
               civ_lightning_conductor, hom_eraser_breadcrumb. You keep the knowledge;
               reopening means paying for the premises again

The creditors seized **exactly the four concerns that earned nothing** and left the twelve
profitable ones alone. That is the single best-judged thing that happened in the whole run:
it's correct, it's specific, it names them, it explains what I keep. More of that.

But note the debt ceiling is not a ceiling. Earlier I was force-settled at 1,036 denarii of
arrears. This time I reached **-12,736** with no insolvency at all, against a stated credit
limit that was never above ~4,900. The gate appears to be "is your net income negative",
not "have you exceeded your credit", so a player with income can borrow several times their
limit indefinitely while a player without income is wiped at a fifth of it.

### 26. Knowledge is lost properly — but the year is wrong

Running out the clock, 366 -> 600:

    EVENT 386: Adrianople and the Gothic settlement: a site is sacked
    EVENT 386: KNOWLEDGE LOST: 9 technologies forgotten (the corpus was never printed and dispersed)
    LOST 387: Town planning and street layout
    LOST 387: Census and population enumeration
    LOST 387: Marine insurance
    ... (9 of them)

This is excellent — it names every technology, it tells you *why* ("the corpus was never
printed and dispersed"), and one of them helpfully adds "(restore brings it back for a
fraction of the cost)". I completed Marine insurance in 367 and lost it in 387; it is the
only thing I built in the last two centuries and the Goths took it.

But **the two halves of the same event disagree about the year**: the sack and the
KNOWLEDGE LOST summary are stamped 386, the itemised LOST lines are stamped 387. Same for
398/399, and 408/409. Consistently off by one.

This is also where my headline number silently changed. `state` said **79 built** at 366
and the end screen said **59 built**. Twenty of my technologies were forgotten across those
centuries. That is the game working exactly as designed and it is the most interesting
thing that happened all run — the whole point of the `risk` screen's "hedged by nothing
yet" nag, which I ignored for five hundred years, paid off precisely as advertised.

Also: `EVENT 579: Recurrent plague: 308 gone with the trade that stopped`. 308 what?
Denarii, presumably, but the line never says, and "gone with the trade that stopped" is the
only place in the game where a quantity is printed with no unit.

### 27. The ending

    *** THE RUN HAS ENDED: the horizon at 600 AD is reached. You built 59 things of your
    own and did not reach point-contact transistor. ***

Clean, correct, and the lockout afterwards is well done: `step`, `start` and `work` all
refuse with a specific reason and the closing line invites you to keep looking around.

One blemish: after the end, `available` still reports **"AVAILABLE: 175 startable now"**
and lists them with an AFFORD column, while `start` refuses everything. "Startable now"
should not survive the end of time.

---

## Summary of what I found

Things that only work if you behave as expected:

1. **The ledger's `Net/yr` omits interest on arrears.** It read "+9.5" while capital fell
   105, then 117, then more, per year. The rate is printed on the same screen.
2. **`buy slaves` ignores the supervise/house/teach cap that `hire` enforces.** Told I
   could take 6 more people, I took 7 by typing a different verb.
3. **Bought people vanish from the two screens that list your people.** 10 bought; status
   bar `art 7`; `labour` "nobody"; `state` "EMPLOY: 0 people".
4. **People who leave still finish their apprenticeships the next year** — 18 dispersed in
   156, four events in 157 announced them completing training, in fractions (6.2, 3.4, 2.7,
   2.3) that sum to 14.6 rather than 18.
5. **The `IN TRAINING` list prints the trade as the literal string `None`.**
6. **Insolvency is a repeatable free debt-wipe** that settles you at the same ~77 denarii
   every time and announces "reputation -12" against a reputation already floored at 0.10.
   Five times, no escalation.
7. **The debt ceiling only binds if your income is negative** — I reached -12,736 against a
   ~4,900 limit while earning, and was force-settled at -1,036 while not.
8. **"A site is sacked" took 62% of my money without printing a number**, while `risk` said
   "technologies at risk: 0" and I owned no sites. The plague family handles this correctly
   ("you had nothing it could take"); the sacking family does not.
9. **`bribe` sells a hidden stat, `protection`, with no scandal present and no UI anywhere.**
   700 denarii took it 0.07 -> 0.37. It is on no screen, in no help topic.
10. **`load` inside a running process suppresses hazard announcements** that the same save
    file produces in a fresh process. Numbers identical, narration silently thinner.
11. **`step abc` advances a year silently** while `step 0` and `step -5` are properly refused.
12. **Knowledge-loss events are stamped one year later than the sack that caused them.**
13. **Currency debasement of 99% moves nothing but my own revenue.** Wages and every
    project cost are byte-identical in 292 to what they were in 100.
14. **Eminence, the game's loudest warning, is unreachable.** Peak 5.3 against a stated
    danger line of 26, while playing to maximise it.
15. Smaller: `help economy` duplicates `help money`; two headings both called RUNNING on
    `state`; completions announced twice in two formats; "1-0" pagination when the list is
    empty; `buy forest` is the only purchase whose price cannot be discovered; `available`
    reports 0 startable when overdrawn but `open` will happily deepen the overdraft;
    `available` still says "175 startable now" after the run has ended; the resume command
    the game prints uses a relative path that doesn't work from the directory it saves into.

Things that are genuinely good and that I want to say so about:
- The refusal messages. "you already owe 4,314 denarii on work in hand; this would take it
  to 4,914, and between cash and credit you can raise 4,866. Finish or stop something
  first." Almost every refusal in this game tells you the number and the fix.
- "Antonine plague: you had nothing it could take."
- Creditors seizing precisely the four loss-making concerns and naming them.
- The `risk` screen's historical writing, which is better than it needs to be.
- The wealth-scaled cost of living, which quietly killed my day-labour strategy without a
  lecture.
- Save/reload is deterministic in every number I could measure. I checked three times.

The strategy the game most rewarded, which I found by accident and which is nothing like
what it advises: **start twenty of the cheapest possible technologies at once, finish them
all in a single year with your 2,000 founder-hours, and go from reputation 0.2 to 30.6.**
Founder-hours are not scarce, calendar floors do not appear to bind, and there is no cap on
concurrent projects other than money.
