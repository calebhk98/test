# WEIRD_C — playtest notes

Player: contrary/bored/curious. England 1300, fog of war ON, poor scholar purse, founder does NOT age.

## Log

### Setup (1300 AD)
Answered: 4 (England 1300), y (fog), poor_scholar, n (no ageing).
Session file: england_1300.json in cwd. Resume: `python3 rome/sim/simulator.py play --session england_1300.json` (note: that path is relative to repo root, not to my cwd — I'll use the absolute simulator path and it seems to find the session in cwd).

Start line: `[1300 AD | 400 den | you:2000 hr | sch 0 art 0 | rep 5]`

EXPECTATION before touching anything: this is a tech-tree game where I spend my 2000 personal hours/year plus money to "build" things, hire scholars (sch) and artisans (art), and reputation (rep 5, presumably out of 10 or 100) gates access to patrons. I expect `available` to list a handful of cheap starting projects, and I expect the game wants me to bootstrap income first.

MY DELIBERATE PLAN (contrary play): I will be a **hoarder who never runs anything**. Specifically:
1. First I'll survey with help/available/why.
2. Then commit to one refusal: I will never hire anyone and never take a patron, no matter what the game nags about. One person, alone, forever — the title says "One person", so I'll take it literally.
3. I'll also try doing nothing for centuries (spam `step`) and see if the game notices or breaks.

### 1300 — first look
Goal revealed: **build a point-contact transistor before 1800**. 500 years. 105 things startable now, 132 technologies "granted for free".

Immediately interesting: three things cost **0 den, 0 hours, 0 years** —
- `lnd_cursus_publicus` Cursus publicus courier — upkeep **200/yr**
- `sea_pharos_lighthouse` Pharos lighthouse — upkeep 0
- `cap_measure_time_s` Time to the second — upkeep 20/yr

My income is +2.8 den/yr net on 400 den. A free-to-build thing with 200/yr upkeep is a trap with a bow on it.

EXPECTATION: I bet "build" and "run" are separate, and that upkeep only bites once something is *running*. The `available` header calls them "startable", and `state` has a RUNNING: nothing line, so I expect I can accumulate built-but-idle things at no ongoing cost. **That is my whole strategy: become a hoarder of unrun infrastructure.** If upkeep charges on merely-built things, I'll be bankrupt inside two years and I'll say so.

Also weird already: a "Pharos lighthouse" and "Cursus publicus" (Roman imperial post) offered in *England, 1300*. Feels like the scenario is a reskin of a Rome tree.

### Confirmation that hoarding is legal
`help commands` says outright: "open <id>: start actually running something you have worked out how to do; **until you do, it earns nothing and costs nothing**". So build-and-never-open is a supported state. Good — my strategy is sanctioned. I'll push it to absurdity.

Started all three free things at once. All accepted, "the bill you have taken on: 0".

**CONFUSION #1 — two things called RUNNING.** `state` prints "RUNNING (3):" listing my three in-progress *projects*. `ventures` prints "running: nothing". Same word, opposite answers, one command apart. The `state` screen never uses the word "building" or "in progress".

**CONFUSION #2 — who is a scholar.** Status bar: `sch 0 art 0`. `state`: "EMPLOY: 0 people ... nobody". `why`: "you have 1, 0". `ventures`: "scholars: 1". So the founder is a scholar in two screens and not a person in two others.

**SURPRISE #3 — I have a medical practice I never agreed to.** `money` shows Revenue 232.8/yr from `med_cataract_couching` (166.7) and `med_trepanation` (66.7). I never built or opened those. Meanwhile `ventures` insists "running: nothing". So the game is paying me for couching cataracts and drilling skulls in my spare time while telling me I run nothing. Note also that this makes trepanation my second-largest income source, which is a funny thing for a 1300s destitute scholar.

EXPECTATION for next `step`: the three 0-year projects finish instantly; built count goes 0 -> 3; upkeep stays 0 because none are opened. If upkeep of 220/yr lands anyway, the help text is lying.

### 1300 -> 1301: the free-lighthouse reputation exploit
Result of stepping one year:
- All three 0-cost projects completed instantly, as expected. Upkeep stayed **0**. Help text is honest. Hoarding confirmed legal.
- **Reputation went 5 -> 8.2.** For building three things that cost zero denarii, zero hours and zero years. I did nothing. I merely declared that I had done nothing, and England was impressed.
- Revenue rose 232.8 -> 248.4/yr on its own, apparently because reputation rose. So free builds -> rep -> more phantom cataract money.
- **UNEXPECTED: "COMPLETED 1300: Sails on ships"** appeared in the completion list. I never started it. Granted-tech count went 132 -> 133. So a *granted* tech is announced with the same "COMPLETED" verb as my own projects, in the same list, with no marker distinguishing them. If I hadn't been counting I'd think I'd built it.
- New line appeared in `state`: "RUNNING AS CONCERNS: 0 (you know how to run 2 more...)". So the earlier RUNNING/running collision is now a three-way: RUNNING (projects), RUNNING AS CONCERNS (opened), and ventures' "running".

NEW PLAN, following the exploit all the way down: **if free things give reputation, I will hunt down and build every single 0-cost thing in the game and nothing else.** Never spend a denarius on a project. Poverty as a discipline. Let's see how much reputation a man can accumulate by building nothing.

### Dead ends and a contradiction
- `available afford 0` -> "0 startable now". So those three were the only free things in the game; the exploit is capped. Fine.
- `bounty transistor` / `why transistor` -> "REFUSED: unknown node id 'transistor'". The goal is stated to me every single turn as "Aiming at: Point-contact transistor" but I cannot refer to it by that name, and under fog the game will not even tell me its id. So the one thing I am told to do is the one thing I cannot type. (I tried `bounty` on it because `help commands` says bounty means "pay someone else to solve it instead", and paying someone else to invent the transistor for me is *exactly* the sort of thing I would try.)

**CONTRADICTION #4.** `state` warns every turn: "AHEAD: 4 technologies at risk if a hazard lands, hedged by nothing yet". `risk` says, in the same breath: "technologies at risk: 4 ... chance lost if a site is sacked: 80%" and then "no remaining hazard for this civilization sacks a site, so **nothing here is currently at risk of being forgotten**". So the persistent scary line on the main screen is about a danger the risk screen says cannot happen in this scenario.

### Next: save/reload determinism
EXPECTATION: I saved `base1301.json`. I will step 20 years doing nothing, write down the result, reload base1301, step 20 again. If the game is seeded per-save I get identical numbers; if it reseeds on load I get different ones. I expect **identical** — the game encourages stopping and resuming constantly, so it ought to be deterministic from a save.

### Save/reload IS deterministic
Stepped 1301->1321 idle: 686 den, rep 5.1, eminence 0.05. Loaded `base1301.json`, stepped the same 20 years: **686 den, rep 5.1, identical events**. Seeded from the save. Good — no reload-scumming available. (I approve, but a bored player will try it, so worth stating in-game.)

Events I only saw on the second run because the first run's log scrolled: "EVENT 1303: fire in the thatched lanes behind the market" (no stated effect on me at all) and "EVENT 1317: Great Famine: **staff -12%**, and **49 pence** gone with the trade that stopped".

- I employ **zero** people. The famine took 12% of nobody and reported it as a loss.
- "49 **pence**" — every other number in the game is denarii. Unit slips mid-sentence.
- Reputation decayed 8.2 -> 5.1 over 20 idle years, i.e. below where a rep-5 nobody started once you count the +3.2 the free lighthouse bought me. Doing nothing is punished, slowly.

### NOW THE STUPID PART: deliberate bankruptcy
EXPECTATION: `lnd_cursus_publicus` costs 200 den/yr to run and earns **0**. `cap_measure_time_s` costs 20/yr and earns 0. My net is +18/yr. Opening both makes me -202/yr against 686 den and a 1,547 credit limit — roughly 11 years to broke, ~19 to the limit.

What I *think* will happen: the game will let me go into arrears at 12%, and at the credit limit it will either (a) refuse further spending, (b) force-mothball my ventures, or (c) end the game with some kind of ruin. I think (a) is likeliest because `help economy` says "as far as somebody will lend you and no further".

What I *want* to find out: whether a man can operate an imperial courier service that carries nothing, for no one, at a loss, forever, and whether anyone in the simulation ever asks him why.

### Bankruptcy: the game handles it well, and then traps you
Opening the two ventures **charged a full year of upkeep immediately** (685 -> 486 -> 466 den on the two `open` commands, before any `step`). Nothing said it would. Then 20 years:

- 1324 interest on arrears; 1328 "creditors took what they could: 1 concerns closed and sold up: lnd_cursus_publicus"; 1330 same for the clock; 1330 "INSOLVENCY SETTLED: most of the debt is written off and you still owe about 457 pence. Your name is worth less for it (reputation -12)"; 1340 a **second** insolvency.
- Ended 1341 at **-86 den, reputation 0**, net **-0.30 den/yr**.

This is the best-modelled thing I've seen so far — creditors seize the *ventures* specifically, and you keep the knowledge. Genuinely good.

But: **I am now in an unescapable loop.** Net -0.30/yr with no ventures and nothing running. Every few decades I will slide into arrears, get another insolvency, take another -12 reputation off a reputation that is already 0. There is no natural floor and no prompt telling me the way out. My "practice" (the phantom cataract surgery) is the only income and it scales with a reputation I have destroyed.

Also, `ventures` prints raw Python: `needs={'scholars': 0.0, 'craftsmen': 0.0}`. In a game whose help says "Type commands in plain words."

More "pence" for "denarii": every insolvency and interest message says pence, the ledger says den.

### THE BIG ONE: 459 years of nothing
EXPECTATION: I will now `step` all the way to the 1800 horizon and do literally nothing. I expect (a) the Black Death in 1348 to hit a man with no staff, (b) an endless repeating insolvency cycle, (c) some kind of ending screen at 1800 that acknowledges I built three free things and failed. What I most want to know is whether the game *notices* that nothing has happened for four and a half centuries, or whether it just quietly runs the clock.

### RESULT: 459 years of doing nothing (1341 -> 1800)
The single most informative thing I have done. Findings:

1. **The Black Death fired three years running — 1348, 1349, 1350 — each "staff -45%, and 0 pence gone with the trade that stopped".** I have zero staff. It took 45% of nobody, three times, and cost me nothing. The Great Famine, a far smaller event, cost me 49 pence. The worst demographic catastrophe in European history was, for me, free.
2. **A perfectly periodic insolvency loop.** "INSOLVENCY SETTLED ... you still owe about **86 pence** ... reputation **-12**" fired in 1350, 1360, 1370, 1380, 1390, 1400, 1410, 1420, 1430, 1440, 1450, 1461. Twelve times. The *same 86 pence* every time. My reputation was already 0, so -12 twelve times did nothing. It reads like a stuck state machine, not an economy.
3. **Then, after 1461, three hundred and thirty-nine years in which nothing happens.** The only events 1461-1800 are "fire in the thatched lanes behind the market" (x7) and "banditry or a frontier war disrupts supply" (x6), neither of which states any effect on me. No Wars of the Roses, no Reformation, no Armada, no Civil War, no plague recurrence — despite the risk screen promising the Black Death was "**and recurrent thereafter**". It never recurred.
4. **Doing nothing made me rich.** I entered this stretch at **-86 den** and finished at **+1,308 den**, net +8.6/yr, on the strength of the phantom cataract practice alone. The *only* time I lost money in five centuries was the one time I actually used the game's mechanics. Idleness pays; action bankrupts.
5. Reputation crawled back from 0 to 1.5 unaided.

**THE WORLD IS FROZEN.** This is the finding I'd flag hardest. In **1800**, `available` still offers me "Roman masonry arch", "Lodestone knowledge" and "Horizontal loom", and still tells me "this needs chemists and **there are none in this society**". Five hundred years passed. England invented nothing, learned nothing, and produced not one chemist. The intro says "Nothing happens unless you make it," but I don't think it means *this* — a 1300 tech list served unchanged to a man standing in 1800.

**Does the game notice I did nothing?** No. The ending is: "You built 3 things of your own and did not reach point-contact transistor." No acknowledgement that I spent 459 years asleep, and no acknowledgement that the 3 things I "built" cost nothing whatsoever.

**Post-ending state is handled well**, except: `available` still says "102 startable now", still offers "what you can pay for: available afford 1,577", still advises "Teach one: train chemist 2" — and then `start` answers "REFUSED: the run has ended ... nothing more can be started". The shop is open, the till is bricked.

---

## RUN 2: reload to 1301. New obsession: THE HOARDER.
EXPECTATION: I'm going back to `base1301.json`. New rule I will not break: **I will start every single thing I can afford, every year, and I will never `open` a single one.** No employees ever (the title says one person). No patron. If the game wants me to run things to make money, it can want.

I predict: (a) reputation will balloon, because building three free things bought +3.2, (b) I'll be cash-starved almost immediately at 253/yr revenue, (c) hours, not money, will turn out to be the real constraint since I only get 2,000/yr and `identity_cover` alone wants 500.

### Two anachronisms found by poking
- **`buy slaves 5` in England, 1300 is not refused on principle — only on price.** "REFUSED: cannot afford 5 slaves: 2124 pence (425 each...)". Chattel slavery was gone from England well before 1300 (Domesday's slaves had vanished by ~1200; the ordinary condition of production here was villeinage). The help text justifies the mechanic as "the ordinary condition of production in most of these societies" — "most" is doing heavy lifting, and this particular society is one of the ones where it wasn't. If I get the money I'll try again and see if England actually delivers.
- **`mat_obsidian_blade` — "Obsidian blade knapping", 196 den, earns 150/yr — is offered as a live business in medieval Yorkshire.** There is no obsidian in Britain. Likewise `mat_papyrus` (377 den) in England. These look like a shared tech pool served to every scenario without a geography filter, same smell as the Pharos lighthouse and the cursus publicus.
- `help money` and `help economy` print **the same page**, though `help` advertises them as two topics.
- `quote mine coal 500`: 4,950 to sink, 825/yr standing, 3 years to produce. Honest and clear. Good screen.

### The hoard begins
EXPECTATION: I will now try to `start` all 30 of the cheapest things at once. Their costs total far more than my 417 den. I expect the game to refuse the ones I can't pay for. If it *doesn't* — if it lets me take on unlimited liabilities because the money is only drawn down later — then "start everything" is a free option and the interesting constraint is my 2,000 hours, not money.

### The hoard, year one — and an exploit I think I've found
`start` does NOT debit at start; it books a liability. I got 22 projects going on 417 den, and was cut off at exactly the credit ceiling: "REFUSED: you already owe 2,656 pence on work in hand; this would take it to 2,925, and between cash and credit you can raise 2,807." Clear, well-worded refusal. (Still "pence".)

One `step`:
- **18 of the 22 completed in a single year.** Not one of them failed, despite listed risks of 5%, 10%, 15%. Twenty-two rolls, zero failures.
- The **entire 2,656 den bill was charged in year one**, even for projects with a "CALENDAR FLOOR" of 0.1-0.5 years. Money: **-2,492 den**.
- **Reputation 8.2 -> 33.2 in one year.** Also a **scandal of 1.4** appeared with no message explaining it. Nothing told me I had done anything scandalous. (Toothbrushes? Obstetric practice? The obsidian?)
- Note the wording on the four unfinished ones: "60% of your hours spent, 0 still owed - **waiting on your hours**". It is simultaneously telling me nothing is owed and that it is waiting for something.

**THE EXPLOIT I EXPECT TO WORK:** I now owe 2,492 den I cannot possibly repay at +17/yr. From the earlier run I know the game's answer to that is "INSOLVENCY SETTLED: most of the debt is written off ... reputation -12 ... **and you keep your knowledge**". I have no ventures open, so creditors have nothing to seize. So I predict: I wait, the debt evaporates, I pay 12 of my 33 reputation, and I keep all 21 technologies.

If that's right, **insolvency is the cheapest financing in the game**: borrow to the ceiling, build everything, default, repeat. Reputation regenerates on its own (I watched it climb 0 -> 1.5 unaided) and building things *raises* it faster than defaulting lowers it. Let's find out.

## *** BUG: "progress is written after every command" is not true ***
The startup screen promises: "Progress is written to this file after every command, so you can stop any time - **close the terminal, anything** - and come back to exactly where you left off."

It isn't. It writes on clean exit. I lost 12 years of play twice before I noticed, because I was piping output through `head` and the closed pipe killed the process partway through printing. Reproduced deliberately:

```
printf 'step 3\n' | python3 .../simulator.py play --session england_1300.json | head -2
  -> Resumed from england_1300.json: 1301 AD.  ... COMPLETED 1301: Composting
printf 'quit\n'   | python3 .../simulator.py play --session england_1300.json | head -2
  -> Resumed from england_1300.json: 1301 AD.
```
Three years stepped; the file still says 1301. The state at the moment of interruption is exactly the state the promise says will be preserved, and it is the state that is lost. "Close the terminal, anything" is the specific thing that does not work.

(Also of note, from the un-truncated `state`: two projects read "100% of your hours spent, 10.2 still owed - **waiting on money**" while I am sitting on 417 den and the thing costs 10.2. It means "waiting on the year's money allocation", but as printed it is nonsense.)

### Retrying the insolvency-as-financing exploit, this time with the output saved
EXPECTATION unchanged: 22 projects, ~2,656 den of debt I cannot service, nothing open for creditors to seize. I expect the debt to be written off for -12 reputation and for me to keep all 21 technologies. In the run I accidentally threw away, I got to **-7,131 den in 1313 with net +28/yr and no insolvency had fired at all** — the debt just compounded. So my revised guess is that insolvency is gated on something other than being hopelessly insolvent, and I may simply be allowed to owe an unbounded amount forever.

## *** THE EXPLOIT WORKS: default is free if you never open anything ***
1301: borrowed to the ceiling, started 22 projects on 417 den of cash.
1314, 1324, 1334: "INSOLVENCY SETTLED ... reputation -12 ... you keep your knowledge".
1341: **25 technologies built by me. Debt gone. Reputation 0.6.**

I paid for twenty-two technologies with money that did not exist, defaulted three times, and lost nothing but a reputation that regenerates on its own. Creditors "take what they are owed" by seizing *concerns* — and I have never opened a concern in my life, so there is nothing to seize. **`open` is the only thing that exposes you to consequences, and `open` is optional.** The hoarder is invulnerable.

Worse, it's a loop with positive feedback: building things *raises* reputation (8 -> 33 in one year), reputation raises the credit limit, the credit limit is how much you can build. Build -> borrow more -> build -> default -> wait -> repeat. The only cost is time, and the founder does not age.

Two ledger oddities in the aftermath:
- "**paid so far: 18,331**" interest, on a principal that never exceeded ~2,700 and was written off three times. I never paid any of it. The line counts accrued-then-forgiven interest as paid.
- Credit limit is now 293.3 — so the ceiling tracks reputation, confirming the loop above.

`policy` is a genuinely good screen — eleven switches, all off but `auto mothball`, with a closing note distinguishing automation from consequence ("creditors take what they are owed ... follows from having no money, not from a setting"). Best-written thing in the game.

**`help sittings` repeats the false save claim**: "The game is written to that file after every command and read back when you start again". Same lie, second location.

### Input validation: genuinely solid
`step -5`, `step 0`, `step 1.5`, `hire scholar -3`, `work labourer 999999`, `work wizard 100`, `bribe -100`, `open <a lighthouse>`, `mothball <a thing with no upkeep>`, `start <already built>` — every one refused with a specific, correct, plain-English reason, and "Nothing was changed." I could not get it to accept nonsense. Best-defended part of the program.

Two nice ones: `open sea_pharos_lighthouse` -> "that is knowledge, not a going concern: there is nothing to open and nothing it would earn." `work wizard 100` -> lists the seventeen trades I could actually work as.

### *** INCONSISTENCY: my hours are free for building but not for working ***
`work labourer 2000` returned a genuinely excellent line:
> "you earned 110, and **the practice those hours were running was worth 223 a year** - so this cost you 113. Wage work is for when you have no practice to lose."

So the game says my 2,000 founder-hours ARE the phantom cataract practice. But in 1301 I poured all 2,000 hours into twenty-two building projects **and collected the 248 den of practice revenue anyway**. Building is free of that opportunity cost; taking a job is not. Same hours, two different rules.

Follow-on: `work` looks **strictly dominated** for any founder who has a practice — 2,000 hours of labouring pays 110 against a practice worth 223. The game tells you this to your face after you've done it, which is charming, but it means an entire top-level command exists to be a mistake.

### Small stuff
- `hom_toothbrush`: UPKEEP 40/yr, REVENUE 30/yr. A venture that loses money by construction. (`auto open` explicitly refuses to open these, which is a nice touch — but nothing warns you before you build one.)
- Toothbrush flavour text in the England 1300 scenario: "**Romans** use twigs and charcoal powder for dental cleaning." More Rome bleeding through.
- "EMINENCE is dangerous above 26" is printed on the main screen every single turn. After building 25 things my eminence is **0.15**. I have no idea how one would ever approach 26, and nothing in the game has hinted at it. It reads as a permanent warning about a mechanic I cannot reach.

### Next: teach England chemistry while insolvent
EXPECTATION: `chm_continuous_batch` has been sitting in "HEARD OF, CANNOT BEGIN YET" since 1301 saying "this needs chemists and there are none in this society. Teach one: train chemist 2 (about 450 of your own hours each, two years)". I am at **-164 den** with no income beyond the practice. I expect training to cost hours (900 of my 2,000) rather than money, and therefore to be something a bankrupt man can do. If a penniless defaulter can singlehandedly invent the profession of chemist in 1341, that's the same hole as the hoard: hours are unpriced.

### `train` is properly gated (good)
`train chemist 2` -> "REFUSED: you must keep them fed while they learn: 660 pence, and you have -420". So teaching a trade costs money as well as hours. My guess that hours were unpriced was **wrong**, and the game was right to refuse. Credit where due.

But: `available chemistry` filters the *startable* table to chemistry and then prints a "HEARD OF, CANNOT BEGIN YET" list containing `civ_town_planning`, `opt_gravimeter`, `civ_insula`, `med_obstetric_antisepsis`, `sea_fresnel_lens`... The subject filter doesn't reach the second half of the screen.

(And `civ_insula` and `civ_sewer_roman` are waiting on `civ_arch_roman` in 1345 England. Roman tenement blocks and Roman sewers, still pending.)

### start / stop cycling: no exploit, but silent losses
`start fin_trademark` / `stop` / `start` / `stop` / `start`, then a year, then `stop` / `start` again. Each `start` re-books the full 18.7. Stopping at 38% complete threw away the 7.1 den already spent and reset it to 0%. `stop` prints exactly one word of feedback — "stopped: fin_trademark" — and never says what it just burned. (Help does warn, on a different screen, an hour earlier.)

### *** The game HAS a poverty-trap detector, and its advice contradicts itself ***
Once I'd been broke long enough, `state` started printing:

> !! YOU HAVE BEEN IN ARREARS 8 YEARS AND YOU LOSE **0 PENCE A YEAR**, SO NOTHING YOU START WILL EVER BE PAID FOR
>    it is escapable, and none of these need anybody to lend you a pence
>    - **work for wages**: you have 2000 of your own hours left this year...

Three problems:
1. "YOU LOSE 0 PENCE A YEAR, SO NOTHING YOU START WILL EVER BE PAID FOR" is a non-sequitur as printed. The real figure is -0.30, rounded to 0, and the sentence is built as if the number were the reason.
2. It recommends **work for wages** — the exact action the `work` command itself told me was a net loss of 113 den/yr against my practice. The rescue advice and the action's own feedback disagree.
3. It lists only *one* escape, and never mentions the actually correct one: **I am sitting on twenty finished concerns, several of them plainly profitable, and I have opened none of them.** See below.

### *** The thing the game never tells you: your hoard is free money ***
`ventures` (in full) finally shows `to_open_it`:
```
ag2_oil_pressing   earns 140/yr  costs 35/yr  to_open_it 39.9
mat_obsidian_blade earns 150/yr  costs 20/yr  to_open_it 29.5
ag2_hopping        earns  80/yr  costs 15/yr  to_open_it 24.8
ag2_layering       earns  80/yr  costs 20/yr  to_open_it 27.2
hom_safety_pin     earns  15/yr  costs  0.5/yr to_open_it  4.0
```
Roughly 130 den of one-off spending buys ~350 den/yr of profit, on a founder whose entire income is 223/yr. `state` mentions the hoard only as a neutral count — "you know how to run 20 more and have not opened them" — with no hint that most of them pay. The trap detector, firing on the same screen, doesn't look at the list either.

### Last small ones
- **`state full:true` disagrees with plain `state` about danger.** Plain: "AHEAD: 4 technologies at risk **if a hazard lands**, hedged by nothing yet". Full: "AHEAD: 4 technologies at risk, **0 lost per sacking on average**, hedged by nothing yet". The detailed view quietly admits the number is zero; the default view is the one that worries you.
- `ventures` prints twenty lines of raw Python dict literals (`needs={'scholars': 0.0, 'craftsmen': 0.0}`) in a game whose help says "Type commands in plain words."
- `help risk` -> "no such topic: risk. topics: commands, labour, economy, money, automatic, sittings, fog". But `state` ends every turn with "more: knowledge_risk -> **risk**; ... where_the_money_comes_from -> **money**". Those look like help topics and are actually top-level commands — and `help money` prints the *economy* page verbatim, so `money` is both a command and a duplicate help alias.
- `commission smith 400` = 101 pence for 400 hours of a smith. That is remarkably cheap next to the ~450 founder-hours + 660 den it costs to train one chemist, and it's the documented way past "needs 1 trained craftsmen". Suspect it's underpriced.
- `load no_such_file.json` -> "REFUSED: could not load ... [Errno 2] No such file or directory". Correct behaviour, but a raw Python OSError repr in the player-facing text.

---

## SUMMARY OF THE RUN
Two lives, one save file.

**Life 1 (idle):** built the three free things, opened the two loss-making ones on purpose, went bankrupt, then did absolutely nothing from 1341 to 1800. Ended richer than I started. The world did not change in five centuries.

**Life 2 (hoarder):** reloaded to 1301, borrowed to the credit ceiling, started 22 projects in a single command block, defaulted three times, kept all 25 technologies, and never opened a single concern. Ended in a permanent poverty trap holding twenty profitable businesses I refused to run.

The game is much better written than it is balanced. Its refusals, its `policy` screen, its bankruptcy model and its `quote mine` screen are all excellent. What it doesn't expect is a player who **treats `open` as optional** — because `open` is the only thing that attaches consequences to anything.
