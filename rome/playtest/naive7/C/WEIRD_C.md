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
