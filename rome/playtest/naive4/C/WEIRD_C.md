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
## Phase 6: the day-job run -- refuse to use your knowledge, dig ditches for two centuries

Commitment: from 1603 I do nothing but `work labourer 2400` (the worst-paid trade) and
`step 1`, every year, forever. No projects. The founder who has the whole of modern
technology in his head and chooses to be a farmhand.

First the wage check:
    work labourer 2400  -> earned 133.6 den
    work scholar  2400  -> earned 667.8 den
A full year of the founder's own labour as a labourer earns **133 den**, against living
costs of 266-295 den/yr and a passive medical income of 253 den/yr. **Working full time
for a year cannot pay half your rent**, while doing nothing at all pays it in full. As a
statement about medieval unskilled labour that is arguably right; as a game affordance it
means `work` is a trap for anyone who does not first check the numbers, and it is the
only thing in the game you can do with your hours that has no risk attached.

Results of 1603-1652, fifty consecutive years of ditch-digging:
* Capital 704 -> 2,588. So it does work, slowly.
* **BUG 9: the ledger's `Net/yr` is wrong for anyone who uses `work`.** Every single year
  `state` insisted `net -43 den/yr` ... `net -62.6 den/yr` while my capital rose by about
  85 den a year. The `money` screen agrees with the wrong number: `Net/yr: -62.6`. Wage
  income from `work` is not in the ledger at all. A player watching the net number would
  conclude he was bleeding out while actually getting richer.
* `net` got steadily *worse* the richer I got (-43 -> -63) because "living and
  appearances" scales with capital (240 -> 295). Meanwhile `Credit limit` **fell** from
  797 to 558 as my capital more than tripled. Getting richer lowered my credit.
* Reputation drifted 2.4 -> 1.5 over fifty years of honest work. Eminence crept 0.02 ->
  0.06. Suspicion and scandal never moved off 0 through anything I have done, including
  buying a human being.
* 1607: `fire in the thatched lanes behind the market` and my capital dropped 1,689 ->
  1,345, about 344 den. The identical event in 1304/1329/1336/1340/1356/1358/1361/1373
  cost me nothing at all. Same sentence, sometimes free, sometimes a third of my money,
  never a word about what burned.

**BUG 7 continued: the ghost slave.** Fifty years on, the status bar says `art 1`, but:
`EMPLOY: 0 people ... nobody`, `LABOUR / ON YOUR STAFF: nobody`, `Total employed: 0`,
`wages 0 den`. He does no work, appears on no roster, and earns nothing. 354 denarii for a
person who exists only in the status bar.

Also, `state` prints this whether or not you employ anyone:
  "1.32 artisans is the wage and output of one artisan plus a third of another's."
A worked example about a number I do not have, printed under the word "nobody".

NEXT EXPECTATION: grind to the 1800 horizon. I expect the game to end with a summary that
notes I built two things in five hundred years (an eraser and a pendulum clock) and got
nowhere near a transistor. I would like to see whether it says anything at all about that,
because so far nothing in five hundred years has commented on my behaviour.
## Phase 7: the horizon, 1800

Grinding to 1800 with nothing but `work labourer`. Events 1652-1800 were: seven more
identical thatch fires and five identical "banditry or a frontier war disrupts supply".
That is the entire content of the last 148 years. Two sentences, twelve times.

Final capital 4,929 den. Reputation 1.3. Suspicion 0. Scandal 0. Built: 2.

The ending, in full:

    *** THE RUN HAS ENDED: the horizon at 1800 AD is reached. You built 2 things of
    your own. There was no target to hit; how far you got is the whole of the result. ***

**BUG 10: the ending contradicts the tutorial.** `help` says, in its own words,
"what you are trying to do: **Reach point_contact_transistor**, and see the rest of what
you can build on the way", and with fog off `state` prints `Goal: point_contact_transistor`
on every screen. The ending then tells me "**There was no target to hit**". One of those
two is wrong, and a player who spent 500 years chasing a transistor is being told at the
buzzer that it never counted.

The ending also does not name the two things I built, does not show the ledger, does not
say how close (or in my case how catastrophically far) I got, and does not remark in any
way on the fact that a man with the whole of modern technology in his head spent five
centuries digging ditches and drilling skulls. **In 500 turns the game never once reacted
to what I was doing.**

**BUG 11: you get exactly one command after the run ends.** Post-1800 the process
executes the first line you send and then exits, discarding the rest of the input. I sent
`state / money / available / help / work` and got `state` only, then "Ended". Any command
that changes things is `REFUSED: the run has ended`, which is correct, but read-only
post-mortem commands are also cut off after the first, so you cannot actually review your
own run. And the final screen *still* prints the resume command that does not work.

Also on the final screen: `net -97.7 den/yr` at 4,930 den. The living-costs-scale-with-
capital rule means the endgame punishes you for the money the passive medical income
forced on you.
## Phase 8: second and third games, run as controls

I started two more England 1300 games (`gameB/`, `gameC/`) purely to check whether the
things that ignored me in game A ignore everybody.

### The Great Famine of 1315 does not exist
Three separate 1300->1350 runs. Zero famine events in any of them, idle or staffed. The
scenario text sells it as one of the two dated catastrophes you are meant to plan around
("Fifteen years to the Great Famine"). It is not in the game.

### `COMPLETED 1300: Sails on ships` is reproducible
Fresh game, first `step`, `RUNNING: nothing`, and the log announces a completion. It
happened in game A and in game B identically. Whatever it is, it is labelled with the
same word the game uses for *my* finished projects, which is the confusing part.

### BUG 13: the Black Death silently eats ~28% of your capital
`EVENT 1348: Black Death: staff -45%` is the whole message. In game C I went into 1348
with 12,676 den and came out of it with 9,111 (-28%), and 1350 took 8,970 -> 6,447
(-28% again), against a stated net of only -195 and -101 den/yr. So the plague *does*
have teeth -- it takes more than a quarter of your money per year -- and the event text
mentions only staff, which is the one thing it did not touch, because I had none.
A player reading the log has no way to know where a quarter of his money went.
(The staff-loss half does work: with staff I could not pay, I got
`you cannot pay everyone: 2.7 of your staff leave for work that pays`, which is a good
line.)

### BUG 12: the last hiring slot is unreachable (off-by-one)
    hire artisan 7
    REFUSED: you can supervise, house and teach 7.0 more people, not 7.
    hire artisan 1   (with 1.0 free)
    REFUSED: you can supervise, house and teach 1.0 more people, not 1.
It refuses n when the cap is exactly n. `hire artisan 6` against a cap of 7.0 works. The
comparison is strict where it should be inclusive, so you can never fill your last place.

The same refusal has two more problems:
* It leaks the machine protocol into prose: *"...or commission smith 400 to buy one job
  instead of employing anybody; **{"cmd":"buy","what":"slaves","n":N}** then manumit,
  though they are untrained for three years."* Raw JSON, mid-sentence, in a game that
  tells you to "type commands in plain words".
* It answers the wrong question. `hire labourer 1` is refused with "To get more
  **artisans**: hire smith 3". I did not ask for artisans or smiths.

### BUG 14 (the big one): the whole mining subsystem is unreachable
`help commands` says: `quote <what>: ... so far quote mine coal 500`.
`help economy` says: `buy mine: buy mine coal 500 ... ASK THE PRICE FIRST with
quote mine coal 500, and close it with close coal.`
Both of those documented commands fail:

    quote mine coal 500  -> REFUSED: no such material: None. Mineable: coal, copper, ...
    buy mine coal 500    -> REFUSED: material must be one of: coal, iron, copper, ...
    buy mine iron 100    -> REFUSED: material must be one of: coal, iron, copper, ...

The error lists the material I just typed as a valid material. Every three-word form
(`buy mine <material> <n>`, `quote mine <material> <n>`) drops the material argument;
two-word forms (`buy forest 100`, `buy slaves 1`) parse fine. And the errors point at
each other in a circle: `quote coal 500` is refused with *"only mines can be quoted so
far: quote mine coal 500"* -- the form that doesn't work -- while bare `quote` suggests
a third syntax, `quote iron 500`, which the first message says is impossible.

Net effect: **you cannot sink a mine or buy ore in plain-word mode.** For a scenario
whose stated bottleneck is "Cheap iron, and the temperature to make it. Everything
downstream of steel waits on a furnace nobody has yet built", losing the iron supply
chain to an argument-parsing bug is the most consequential thing I found.

### Other small things from the controls
* Hiring 5 artisans for 1,100 den with 400 den in hand was allowed (straight to -700 via
  credit); the very next hire was refused for having -700. Fine on reflection -- credit
  limit -- but the two messages read as a contradiction in the moment.
* `help economy` and `help money` print the identical page.
* `save mysave.json` / `load mysave.json` both work correctly in-process. It is only the
  *printed resume line* (Bug 1) that is wrong.
* `bounty hom_eraser_breadcrumb` gave the best-written refusal in the game:
  "a craftsman in England under Edward I could not recognise success at this without
  understanding the theory, so there is nothing to award the prize for." That is the
  standard the rest of the messages should be held to.
* Unknown commands, negative quantities, zero quantities, stop-and-restart, freeing
  slaves you do not own, closing mines you do not have -- all refused cleanly and
  correctly. The input handling is solid; it is the documented commands that break.

## What I actually did, in one paragraph

Played England 1300 as a man who refused to do anything. Idled 1300-1600 (300 turns,
zero actions) and got richer. Discovered in 1602 that the engine had been running a
cataract and trepanation practice in my name the whole time. Bought one free technology,
one breadcrumb eraser and one slave, in that order. Spent 1603-1800 digging ditches for
133 den a year while a 20 den/yr pendulum clock and an invisible artisan sat on my books.
Reached the horizon in 1800 having built two things, with a reputation of 1.3, a
suspicion of 0, a scandal of 0, and 4,929 denarii I did not want.

## The thing that struck me hardest

**In 500 turns the game never once responded to me.** Not when I did nothing for three
centuries. Not when I went bankrupt eight times. Not when I bought a human being in
Christian England. Not when a man carrying the whole of modern physics chose to be a
farmhand for two hundred years. Suspicion and scandal never moved off zero through any
of it. The systems that exist -- reputation decay, arrears interest, staff walking out --
all work, and they are the good part. But they are all *thermostats*, not reactions.
Nothing in the world has an opinion about the player. The game reads as though it was
built and tested by people who were trying to reach the transistor, and it is completely
undefended against someone who isn't.
