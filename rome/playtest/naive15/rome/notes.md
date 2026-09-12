# Playtest notes — naive15 — Roman Empire under Trajan

Playing blind: never read source, never read other playtest notes, never read the repo's design docs. Everything below is worked out from the game's own text.

## Setup (Year 100, before turn 1)

The game opens with a well-written framing screen: "ONE PERSON, AND EVERYTHING THEY KNOW". You're a modern person dropped into a past society with knowledge but no industrial base. Good hook, sets expectations correctly (this is a tech-tree game, not combat/4X).

Choices at setup, in order:
1. Which civilization/era (5 choices). Picked "The Roman Empire under Trajan, 100" per instructions.
2. Fog of war on/off — **irreversible once chosen** (can go off→can't go back on if you start with it off; on stays on). Chose ON, since that's clearly the "real" way to play (off is described as a planning/spoiler mode). This means I cannot see the tech tree, only what's buildable now and rumors of things I've "heard of."
3. Starting wealth tier: destitute / poor_scholar (default, 400 den) / artisan / merchant / rich_merchant / equestrian / absurd. Took the default, poor_scholar — "a knife, a lens, a codex of notes."
4. Mortality: age and die, or not. Default is NOT aging — explicitly said to be the way "to measure the tree rather than a lifespan lottery." Left it off, since the immediate goal (transistor) is stated to take centuries.
5. The GOAL. This is the actual win condition, chosen once at setup, from a list of 17 with wildly different scope: goals range from "closure 1, floor 2y" (Establish experimental science) up to "closure 168, floor 142y" (the transistor — the default and the game's named endpoint). Chose the default: **Grown and alloy junction transistors**. This was a deliberate choice to see the real shape of the game rather than a quick lifetime-sized goal — but in hindsight, given limited session time, a shorter goal might have let me see an actual ending. Noted as a thing to flag: the game front-loads a huge, mostly irreversible commitment (goal + fog + mortality) before you've seen a single turn of actual play. There's no "try a short goal first" onramp.
6. Horizon: how many in-game years before the run force-ends. Options 400/500/650/endless. Picked Standard (500). This one IS changeable later via `options`.

First confusion: right after choosing "1" for the goal (transistor) via **empty-Enter-for-default**, the game process crashed and killed the whole tmux session twice in a row, with no traceback visible in the captured output. The THIRD attempt, this time typing the digit "1" explicitly instead of pressing Enter on the default, worked fine and proceeded normally. I did not chase this further (told not to read source), but it's worth flagging: something about accepting the bare-Enter default at the goal-selection prompt looked fragile in my environment. Might be an artifact of my terminal/tmux setup rather than the game — noting it rather than concluding it's a bug.

## Turn 1, Year 100 AD

Game state is shown as a prompt-bar `[100 AD | 400 den | you:2000 hr | sch 1 art 1 | rep 5] >` plus a fuller `state` dump on request. Core resources, as best I can tell:
- **Money** (denarii). Starts 400.
- **Founder-hours**: 2000/year, does not carry over. This is YOUR personal labor budget for the year.
- **Staff**: counted as "scholars" and "artisans" — starts at 1 and 1 (i.e., just you, counted as both, apparently, since you're a "poor scholar" with "a knife" — a hybrid).
- **Reputation**, **protection%**, **scandal**, **eminence** — a cluster of social/political stats. Scandal >25 apparently ends the run (denunciation). Eminence >26 also dangerous somehow. Both were explained in the `state` output, which is nice — the game surfaces its own danger thresholds without me having to guess.
- Every game starts with **139 technologies "granted for free"** — i.e., baseline tech this civilization already has (roads, concrete, etc. from the intro text). Progress is measured in techs "built by you" on top of that base.

The starting command vocabulary the game itself recommends: `state`, `available`, `why <name>`, `start <name>`, `step`. That's a good minimal onramp — I used exactly these first.

### `available` — my first real look at the tree

209 things startable immediately, bucketed by subject (textiles 54, finance 26, roads/bridges 20, "the remaining arts" 20, power and precision 16, farming 10, household 10, metallurgy 9, transport 9, mathematics 7, medicine 7, etc.) This is a LOT of surface area on turn 1. Slightly overwhelming — the subject-summary table is the right instinct for taming it, and the "cheapest six" / "most staff-rests" call-outs at the bottom were genuinely useful shortcuts. Still, 209 options with only "why" as a way to interrogate them means turn 1 is a lot of reading.

Two commands stood out as load-bearing: `why <id>` gives full cost/risk/prereq/effect detail, and its "HOW MUCH RESTS ON THIS" line (none / a few things / almost everything) is basically the only compass available under fog. I leaned on it heavily to find "foundation" nodes.

### First real decisions: scientific_method and units_standards

Checked `why scientific_method` — flagged "tier 0, foundation... HOW MUCH RESTS ON THIS: almost everything". Cost 230 den, 350 of my hours, 2-year floor, 20% failure risk. Flavor text is good: the risk is explicitly *cultural* ("displacing Aristotelian authority"), not technical — a nice bit of texture that ties the number to the fiction.

`why units_standards` (define length/mass/time/temperature standards) — also "tier 0, foundation... almost everything" rests on it, cost 444 den.

Both looked like unavoidable foundations, so I started both on turn 1 (`start scientific_method`, `start units_standards`), spending my hour budget and taking on debt against my 400 den. This turned out to be **too aggressive for a poor_scholar start** — see the debt spiral below.

### Debt spiral, years 101–107 — the single most important thing I learned this run

Mechanic, pieced together the hard way:
- Starting a project doesn't charge you the money up front; it "owes" the cost, drawn down over time as your founder-hours and available cash let it, subject to a calendar floor.
- If you overcommit and go into **arrears** (negative cash), the interest on arrears (~11%/yr) starts eating your income, and — this is the part that isn't obvious from any single screen — **being in arrears also stalls the founder-HOURS going into your projects**, not just the money. The game does say this explicitly if you read `help economy`'s debt entry, but I only found that after several turns of watching a project sit at "13% of your hours spent... in arrears: the hours offered this year did almost nothing" without understanding why my own free hours weren't moving it forward. That was a real "wait, what?" moment — I initially assumed hours and money progressed independently once a project had "enough" money queued.
- Meanwhile I had `open`ed scientific_method and units_standards, which do NOT earn anything but DO cost upkeep (100/yr and 30/yr respectively) once opened — "open" just means "actually running," separate from "known/built." I opened them reflexively, without realizing opening a pure-knowledge tech with 0 revenue is pure downside unless something else needs it running (see below). That pushed net income to -220/yr on top of the debt-interest problem, and my capital went from +400 to -835 den over about 4 in-game years while a project inched forward at a trickle.

How I dug out:
1. `mothball <id>` on all three open-but-earning-nothing concerns (scientific_method, units_standards, cap_measure_len). The game confirmed explicitly: mothballing stops the upkeep AND stops the (zero) earnings, but "you still know how to do it" — i.e., **the built/finished status is permanent and separate from the open/running status**. I verified this really matters by checking `why corpus_written` afterward, which listed "PREREQUISITES (all met, and finished counts for ever): scientific_method, units_standards" and STATUS: CAN START NOW even with both mothballed. So: opening a "concern" is a pure economic decision about revenue vs upkeep, not a precondition for using it as a tech-tree prerequisite. This was NOT obvious up front and cost me real playtime to work out — the flavor text for scientific_method ("Multiplier on every research node thereafter") reads like it should matter whether it's kept running, but as far as I can tell that's just narrative color describing why the technology itself is important, not a live "must stay open" bonus. I never got a crisp confirmation either way and I'm flagging that ambiguity rather than claiming a bug.
2. Discovered the `work <trade> <hours>` command — explicitly sell your own founder-hours for ordinary wages instead of spending them on your own projects. This was hugely effective: `work scholar 2000` (all my free hours) earned ~650 den in a single year, net ~+400-500 after accounting for what it took away from my existing "practice" income (I earn passive money from practicing medicine on the side — cataract surgery and trepanation, apparently part of the poor_scholar's existing skillset, which the game explicitly said pays "about a third of what the tree quotes" because it's informal, one-person work). Using `work` for 1-2 years while nothing else was running dug me out of debt (-835 → -190 by year 107) and then to a healthy surplus (net +205/yr) once the debt principal was down and a revenue concern (horizontal loom) came online.

**Lesson for the designers, if I could say one thing**: the debt-and-arrears mechanic is well-designed and well-explained *in isolated help text*, but the consequence (hours wasted, not just money) is not shown prominently on the turn-to-turn status screen — it shows up as a terse one-line annotation under the affected project ("in arrears: ... did almost nothing") that reads more like flavor than a mechanical warning. A new player doing exactly what the game's own opening suggests (start two "foundation, almost everything rests on this" techs on turn 1) walks straight into this trap. It might be intentional — early overreach being punished is thematically appropriate for "you arrive with nothing" — but it wasn't at all obvious that opening a completed, zero-revenue technology has ongoing cost with no compensating benefit; I'd have expected either (a) opening to be free for pure-knowledge techs, or (b) the game to warn "this only exists to be later prerequisite-checked; you may prefer not to open it" instead of me discovering that by trial, error, and cross-referencing `why` on a downstream tech.

### Recovery and progress, years 107–109

- Opened `tex_horizontal_loom` (a textile technology, cost 225.8 den, cheap) once it finished — this one DOES earn (300-500 den/yr, ramping up over ~3 years). This was my first actual revenue-producing "concern," and it flipped my net income positive.
- Started and finished `arithmetic_positional` (decimal positional notation, zero, negative numbers) — flavored as "recovered from Indian sources" and "highest return on personal hours in the entire tree," another "almost everything rests on this" foundation. Cost 1032 den, financed on credit (credit limit had grown to 2163 den by this point — apparently it scales with reputation/standing over time, though I haven't confirmed the mechanism). Confirmed it has NO open/close mechanic at all — `ventures` doesn't list it, `why` shows no UPKEEP/REVENUE line. So not every tech is a "concern" — some are pure permanent knowledge with zero ongoing cost. Good, that's the sane default; I wish I'd realized on turn 1 that scientific_method/units_standards were the unusual, upkeep-bearing kind rather than assuming (wrongly) all techs behave like arithmetic_positional.

Currently (year 109) sitting at -245 den, net income positive again, one artisan/scholar short of building `atomic_theory` (needs 2 scholars; I have 1, hiring one costs 625 den/yr in wages — a real recurring commitment I'm about to make).

## Things I wanted to check but deliberately did not (per instructions)
- Did not look at source to understand exactly how the arrears/hours-stall formula works, or whether "open" concerns' effects (like scientific_method's stated "multiplier") apply while mothballed. Both times I wanted to check the code and stopped myself and reasoned from in-game text instead.
- Did not read the other briefing/strategy .md files sitting in the repo root next to the sim (00_BRIEFING.md, 02_STRATEGY.md, etc.) even though they're visible in a directory listing — per instructions, played the game only through its own interface.

## Running impression so far

The writing quality is very high — every `why` entry has real, specific, era-appropriate flavor text, and the framing (you know how modern tech works, but "knowing is free, building is not") is sustained consistently rather than being setup-screen-only. The economic model (founder-hours vs money vs staff, practice income vs concerns, credit and arrears) is legible once you've been burned by it once, and the help system is comprehensive if you go looking (`help commands`, `help money`, `help economy`, `help labour` all had exactly what I needed). The single biggest friction point so far is that the game front-loads you into being able to start big "foundation" projects immediately, with all the framing suggesting you should ("almost everything rests on this"), and the debt/arrears trap that follows from doing so is easy to fall into and non-obvious to climb back out of without reading `help economy` closely — a status-screen line more clearly saying "you are locked out of paying down debt / your own hours are being wasted here" instead of the drier "in arrears" annotation would have saved me a few turns of confusion.
