# WEIRD_C playtest notes

Started. England 1300, fog ON, poor scholar purse, founder not ageing.

## Setup

Chose 4 (England 1300). Fog Y (default), poor_scholar (default), aging N (default).
All four answers were the defaults, so a bare `printf '4\n\n\n\n\n'` got exactly the
requested configuration. Save file: `england_1300.json` in cwd.

Header line reads: `[1300 AD | 400 den | you:2400 hr | sch 0 art 0 | rep 5]`

EXPECTATION (before anything): "you:2400 hr" is my personal hours per year (a working
year). "sch"/"art" are probably scholars and artisans I employ. "rep" is reputation,
starting at 5 of presumably 10. I expect `available` to list a handful of cheap
starting techs and `why <name>` to explain one.

## The plan I am committing to

Persona: **a person who thinks the game is a waiting simulator.** I will do NOTHING
but `step` for as long as the game will let me. The intro told me the Black Death is
48 years out and that "whatever you build must survive that or it must be built after
it." I am taking that literally and absurdly: I will build nothing, wait out the
plague, and see whether the world moves without me. Only after ~250 years of pure
idling will I start acting, and then on a deliberate misunderstanding.

I expect: the sim will narrate famine (1315) and plague (1348), my money will drain
to 0 since I have no income, and probably something will complain that I am doing
nothing. I do not expect the world tech to advance on its own -- the pitch is "one
person and everything they know", so I suspect the world is static scenery.

## BUG 1 (found before I even played a turn): the resume command the game prints is wrong

The game ends every session by printing, verbatim:

    Saved to england_1300.json. Come back with:
       python3 rome/sim/simulator.py play --session england_1300.json

That command does not resume my game. Two different failure modes, both bad:

* In one directory it printed
  `could not read the save file 'england_1300.json': this save is from a different
  civilisation ('england_1300'); this game is running 'rome_100ad'. Start the agent
  with --civ england_1300 to load it.`
  -- so the loader knows the right answer and the save banner still tells you the
  wrong command.
* In another directory (repro: run setup, answer the four questions, send nothing but
  a blank line, EOF) the same command **silently started a brand new Rome 100 AD game**
  -- `YEAR 100`, `137 granted` instead of `134`, `net +3.5` instead of `+2.8`, fog off,
  `Goal: point_contact_transistor` visible -- and then, on exit, cheerfully wrote that
  Rome game over the top of my England save file (8571 bytes -> 8783 bytes). If I had
  been forty years in, my whole game would have been gone with no warning.

EXPECTED: pasting the command the program itself just printed puts me back where I was.
GOT: a different century, a different continent, and my save overwritten.
The fix the game already knows about is `play --civ england_1300 --session ...`.
I am using that from here on.

Also worth noting: setting up and immediately hitting EOF wrote a save; setting up and
running one `state` first wrote a *different* save (one that errors on load rather than
silently resetting). So whether you get "loud wrong" or "silent wrong" depends on
whether you typed a command before you quit.

## Non-bug note about my environment
Twice mid-session the simulator died with `SyntaxError: invalid syntax` in
`rome/sim/engine/core.py` line 782 -- somebody is editing the repo while I play. It
healed itself after a minute. I wrapped my launcher in a retry loop and moved on.

## First look at the world

`state` in 1300: 400 den, +2.8 den/yr, 2400 founder-hours, rep 5, suspicion 0,
"dangerous above 26", 134 technologies granted free, 0 built by me.
`available`: 75 startable now (that was the Rome number; England's will differ).

EXPECTATION about "134 granted for free": I read this as "things this society already
has, so you get them without paying". Under fog, England 1300 gets 134 and Rome 100
got 137, which surprised me -- the intro says England is "the most mechanically
advanced society in this game at its start", so I expected England to be granted MORE
free technology than Rome, not three fewer.

## Phase 1: fifty years of doing absolutely nothing (1300 -> 1350)

EXPECTED: money drains, reputation drains, the Great Famine of 1315 arrives because
the intro promised it ("Fifteen years to the Great Famine"), the Black Death arrives
in 1348 and hurts, and somewhere the game nudges me for being idle.

GOT (`step 50`), in order of how surprising it was:

1. **`COMPLETED 1300: Sails on ships`** -- on the very first year, with `RUNNING:
   nothing` and 0 den spent. I had not started anything. The granted-technology count
   also went 134 -> 135 over the fifty years. I have no idea whose project this was.
   Under fog I cannot tell if the world advances on its own or if the engine
   auto-started something for me; either way, a completion message for a project I
   never began is the game losing track of who is doing what.
2. **The Great Famine never happened.** The scenario blurb sells 1315 as one of the
   two dated things you are supposed to plan around. Between 1300 and 1350 the only
   events were: four identical thatch fires, one bandit, the Hundred Years War, and
   the Black Death. No famine, in the fifty years it was promised for.
3. **The Black Death did nothing to me.** `EVENT 1348: Black Death: staff -45%` and
   the same again in 1349. I employ nobody, so -45% of nothing is nothing. Money,
   reputation, prices and my 2,400 hours were all untouched. The worst demographic
   catastrophe in European history is, for a player with no employees, two lines of
   text. Nothing modelled food prices, wages, my rent, or the fact that half the
   people who might sell me anything are dead. A pure idler is completely immune to
   the scenario's headline hazard.
4. The Hundred Years War prints **the identical line every single year** from 1337 to
   1349 ("trade and output fall to 88% of normal"). Thirteen copies. It reads like a
   per-year recalculation leaking into the event log.
5. "fire in the thatched lanes behind the market" fired in 1304, 1329, 1336 and 1340.
   I own no building, no stock and no thatch. Nothing was reported as burning.
   The same sentence four times, verbatim, is also a lot of thatch.
6. Reputation fell 5 -> 1.5 just from existing. Money 400 -> 172.5, now -7.2/yr.
   So the game does model "idleness costs you", which I like -- it is the only thing
   in fifty years that responded to my choice.

Next EXPECTATION: at -7.2 den/yr I hit zero money around 1374. I want to know what
zero means when you have no income and no assets to sell. I predict either (a) money
goes negative forever with no comment, or (b) some ruin/starvation ending. The intro
said "about enough money to eat for a few months", so I half expect starving to be
modelled. Founder does not age, so I should not be able to die.
## Phase 2: idling into insolvency (1350 -> 1390)

EXPECTED: hit 0 den around 1374, then either silent negative money or some ruin ending.

GOT:
* 1368: `interest on 8 denarii of arrears at 12.0% a year`. Good -- the game does model
  debt, and 12% is a plausible medieval rate. I liked this.
* 1387: `INSOLVENCY SETTLED: the debt is written off, you keep your name and your
  knowledge, and you begin again poor`.
* **BUG 2: the debt was not written off.** Three years later `state` shows
  `Money: -162.4 den` at a drain of only -4.6 den/yr. If the balance had been zeroed in
  1387 I should be at about -14, not -162. The message and the ledger disagree; either
  the write-off never touches the balance or it fires without doing anything. Nothing
  else changed either -- no assets seized, no reputation hit for going bankrupt
  (reputation was already 0), no new status.
* Reputation is now exactly 0 and has stuck there. Being bankrupt and having a
  reputation of zero has, so far, no gameplay consequence whatsoever. I set out to be
  as poor and as disliked as possible and the game has not once reacted to it.
* `EVENT 1350: Black Death: staff -45%` fired a third year running. Still 0 staff.
* The Hundred Years War line has now printed **forty times**, identically. Between 1337
  and 1389 it is roughly 80% of everything the game has said to me.

The "society's values are shifting" line drifts by 0.01 every ten years
(patronage_weight 0.70 -> 0.72, w_novelty -0.30 -> -0.26). Under fog I have no idea
what either number does to me, and `state` never shows them, so it is fifty years of
telemetry for a value I cannot see, act on, or find in any menu.
## Phase 3: three hundred years of nothing (1390 -> 1600). The big one.

EXPECTED: continued slow decay; possibly a game-over for being permanently broke.

GOT, and this is the headline finding:

**Doing absolutely nothing for 300 years is profitable.** In 1600 the unemployed,
bankrupt-eight-times, reputation-zero hermit has **1,030 den and +8 den/yr** -- two and
a half times what he started with, earned by never once leaving the house. Money went
400 -> 172 -> -162 -> +1,030 with no input from me at all. Whatever the passive income
model is, it out-earns its own drain over long horizons, so patience alone beats
poverty. My entire attempt to be as poor as possible was defeated by the economy.

**BUG 3: `INSOLVENCY SETTLED` fired eight times** -- 1387, 1397, 1407, 1417, 1427,
1438, 1448, 1458 -- almost exactly every ten years, each time announcing the debt is
written off and that I "begin again poor". Being ceremonially declared bankrupt eight
times had no visible consequence of any kind: no seizure, no reputation loss, no
creditor, no change to what I could start. It reads like a cooldown timer firing on an
effect that does nothing.

**BUG 4: `available` grew from ~75 things to 103 while I did nothing.** The help text
says, in as many words, "**Nothing happens unless you make it.**" But over 300 idle
years the world grew me 28 new startable technologies and whole new subjects appeared
that were not there in 1300 -- `military`, `chemistry`. Combined with the phantom
`COMPLETED 1300: Sails on ships`, either the world advances on its own (and the help
text lies), or something is auto-starting things for me. Under fog I cannot tell which,
and that is exactly the sort of thing a player needs to be told.

**BUG 5 / worst design surprise: there is a hidden deadline at 1800.** I asked for
`step 400` and got
`REFUSED: there are only 200 years left before the horizon at 1800.`
That is the first time in three hundred years the game mentioned a horizon. It is not
in `state`, not in the intro, not in `help`. Under fog of war the player is told
"you cannot see where anything leads" -- fair -- but they are never told **how long they
have**, which is a fact a real founder would obviously know. I have now spent 300 of my
500 years and only learned there was a clock by tripping over it.

Also: **the game never once noticed I was doing nothing.** No prompt, no nudge, no
"you have built nothing in three centuries", no failure state. Three hundred turns of
deliberate refusal produced zero acknowledgement.

Small oddity spotted in 1600's list:
  `cap_measure_time_s  Time to the second (pendulum)   COST 0   HOURS 0   YEARS 0   RISK 0%`
A technology that is free in money, free in hours, takes no time and cannot fail.

EXPECTATION for next: I will start `cap_measure_time_s` because it costs nothing, and I
expect it to complete instantly and give me my first "built by you" technology for
free. If a 0/0/0/0% entry exists, either it is a placeholder that leaked into the
player-visible list, or it is a genuinely free win, and either is worth knowing.
## Phase 4: the free technology, and where my money was secretly coming from

`why cap_measure_time_s` -> "Time to the second (pendulum)", tier 2, COST 0 den,
YOUR HOURS 0, CALENDAR FLOOR 0 years, FAILURE RISK 0%... and **UPKEEP: 20 den/yr**.

EXPECTED: a free win. GOT: a free win with a permanent 20 den/yr bill that the
`available` table does not show a column for. My net income went from +8/yr to -12.1/yr
the moment it completed. That is a good trap in principle, but the only place upkeep is
visible is inside `why`, and the shopping list sorts by COST, which is 0.

Three display faults on that one screen:
* `STAFF NEEDED: 0 scholars, 0 artisans   (you have 1, 0)` -- **I have 1 scholar?**
  The status bar says `sch 0 art 0` and `EMPLOY` says `0 people ... nobody`. Something
  counts the founder as a scholar and something else does not.
* `RUNNING (1): Time to the second (pendulum 100% of your hours spent, 0 den still owed
  - waiting on the calendar`. A project needing 0 of my hours reports **100% of my hours
  spent**; 0/0 is being rendered as 100%. The name also loses its closing bracket to
  truncation, so the line reads as one broken sentence.
* Money 1,038 -> body says `1,026` while the same screen's status bar says `1,025`.

Repeat-build probes, all sensibly refused, no complaints here:
  `start cap_measure_time_s` again -> `REFUSED: already done`
  `start hom_eraser_breadcrumb` twice -> `REFUSED: already active`
  `step 0` and `step -3` -> `REFUSED: years must be >= 1`

### BUG 6 (my favourite finding): I have been an eye surgeon this whole time

`money` shows the ledger:

    Capital: 1,026 den     Revenue: 253.5 den/yr
      from:
        med_cataract_couching        181.5
        med_trepanation               72.6

I never started those. They are two of the 135 technologies "granted for free". So the
reason three hundred years of deliberate idleness turned a profit is that the engine has
been quietly running **a cataract-couching and trepanation practice** on my behalf since
1300, with no staff, no premises, no consent, no hours deducted from my 2,400, and no
effect on reputation or suspicion. Drilling holes in medieval skulls for 300 years cost
me nothing in standing.

This is the single thing that most breaks the game's own pitch. "You arrive alone... what
you have is everything you know", and "Nothing happens unless you make it" -- but in fact
you arrive with an unasked-for medical income stream that pays your rent forever. It also
explains why my attempt to be as poor as possible was impossible: I could not switch the
revenue off, and nothing in `state` ever hinted it existed. I only found it by typing
`money` after 302 years.

(`mothball <id>` exists and might turn it off. I intend to try -- I want to see whether
the game lets a player refuse an income he never asked for.)

Also in the ledger: `interest on arrears: 12%  paid so far: 1,956`. I have paid nearly
2,000 den in interest -- twice my current capital and five times my starting purse --
while being declared insolvent and "written off" eight separate times.

### Anachronism: England 1300 still sells slaves
`policy` lists `auto buy people: buy slaves when the workshop is short-handed`, and
`help commands` lists `buy: forest, mine, slaves, or manumit`. This is the England of
Edward I, where chattel slavery had been gone for two centuries and the institution was
villeinage. The Rome scenario's slave market appears to be present in every civilisation.
I am going to try to buy a slave in medieval England and see if anyone objects.
## Phase 5: buying a slave in Edward I's England

EXPECTED: a refusal, or at minimum a legal/reputational consequence. Villeinage yes,
chattel slave market no. I also expected the game to at least *say* something about it.

GOT: `buy slaves 1` -> `bought: 1 / slaves: 1 / capital: 671.4`. It cost **354 den**,
a third of everything I had. No objection, no law, no scandal, no suspicion, no
reputation change (rep stayed 2.4, suspicion 0). In 1602 England.

**BUG 7: the slave I paid 354 den for does not exist.** Immediately afterwards:
* `labour` -> `ON YOUR STAFF: nobody`, `Total employed: 0`
* `state`  -> `EMPLOY: 0 people, 0 den/yr in wages / nobody`
* status bar -> `sch 0 art 0`
* but `labour` also grew a new section: `IN TRAINING:  None x0.55, ready 1605.0`

So the purchase turned into **0.55 of a person, of trade "None"**, arriving in three
years, and is counted in no roster anywhere. The only lasting effect I can find is that
"living and appearances" jumped 240.6 -> 266.8 den/yr, i.e. I am paying upkeep on a
fractional person who is on nobody's books.

## BUG 8: I cannot refuse the income I never asked for

    why med_trepanation
      tier 0, surgery, confidence A
      "Drilling into the skull to relieve pressure or expel evil spirits."
      FAILURE RISK: 20%     REVENUE: 200 den/yr
      STATUS: DONE

    mothball med_trepanation
      REFUSED: that is something the society has, not something you maintain;
               there is no upkeep of yours to stop

The same object is `STATUS: DONE` (mine, finished, paying me) and "something the society
has, not something you maintain" (not mine) in two commands typed one line apart. There
is no way to stop earning from it. A player who wants to be poor, or who does not want
to be a trepanner, has no move.

Its numbers do not agree either: `why` says `REVENUE: 200 den/yr`, the `money` ledger
says `med_trepanation 72.6`. And `FAILURE RISK: 20%` on a surgery that is already DONE
and has been running for 300 years -- 20% of what, and it has evidently never been rolled,
because nothing has ever gone wrong in the operating theatre.

Minor: `state full:true` (offered in `help commands` as "add full:true for every field")
printed exactly the same screen as plain `state`.
