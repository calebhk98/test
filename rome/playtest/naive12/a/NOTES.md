# Playtest Log - naive12/a
Game: "ONE PERSON, AND EVERYTHING THEY KNOW" (rome/sim/simulator.py)
Player: fresh, no prior knowledge, told not to read source/docs.

Setup chosen: Roman Empire under Trajan, 100 AD; fog of war ON; starting wealth
"merchant" (4000 den); mortality ON (aging/death enabled) — chose this because
the game's own prompt text said "the premise of the whole game is that one is
the honest number", which read like a nudge toward the "real" mode.

Game 2 setup: Rome again, fog of war OFF, rich_merchant (20,000 den),
mortality OFF. Played to year 201 AD, stopped by my own time budget while
clearly winning, not by any game-imposed ending. (Housekeeping note: I
initially ran Game 2's session in playtest/naive12/b/, not realizing that
directory already held a different, unrelated playtest session's files
(git history shows a prior "break tester" run). I restored that directory
to its committed state with `git checkout` and moved Game 2's transcript to
this folder instead, at transcript_game2.txt, alongside this NOTES.md.)

---

## TOP PROBLEMS (ordered by damage to a player like me)

1. **Mortality-on death is a silent, permanent softlock with zero warning,
   despite the game itself nudging new players toward that setting.** In
   Game 1 my founder died of old age at year 138/73. Every technology in the
   tree costs nonzero "founder-hours" (the win condition itself needs 900),
   and once the founder is dead, founder-hours are gone forever — there is
   no heir, successor, or inheritance mechanic (`help commands` confirms no
   such command exists). The escape hatch, `bounty`, explicitly only
   applies to practically-visible crafts, not the theory-heavy chain that
   leads to the goal ("a craftsman... could not recognise success at this
   without understanding the theory"). The game never says "you have lost"
   or "the goal is no longer reachable" — `state`, `available`, `start`, and
   `step` all keep working forever in a fully dead-end game, and running
   concerns keep earning money, so nothing on screen signals that the run
   is over. Meanwhile, the mortality setup prompt's own sales pitch is "The
   premise of the whole game is that one is the honest number," which reads
   as an invitation to enable exactly the mode most likely to quietly end
   the game with no way to know it happened. (It does also correctly call
   mortality-on "a lifespan lottery," so the risk is not hidden entirely —
   see entry 10 in the log for the fuller, fairer treatment. But nothing
   marks the moment the lottery is lost.) This is the single most damaging
   thing I found: it can turn 30+ turns of careful, winning-looking play
   into a run that was dead on arrival at one early yes/no prompt, and nail
   that fact to nobody.

2. **The simulator can hang or crash outright once the economy gets large,
   with no error message and (at least once) the process actually gone.**
   In Game 2 at year 185 AD (153+ staff, 222+ self-built technologies), a
   `step 3` command produced no output for minutes; checking the OS process
   list directly showed the `python3 sim/simulator.py` process no longer
   existed, with no traceback anywhere in the captured output and no new
   autosave written. I could only recover because I happened to know the
   resume command from the game's own opening text. A single-year `step`
   at similar scale later took 2+ minutes to return (successfully), so this
   looks like a real performance/scaling problem that gets worse exactly as
   a player succeeds at the game's stated goal (grow a large, mature,
   multi-generational economy) — the better you are doing, the more likely
   you are to hit this, and a player without shell access has no way to
   tell "still thinking" from "dead," and no in-game hint to resume from
   save rather than give up.

3. **A leaked developer/debug note appears repeatedly in player-facing
   text, including on the win condition itself.** Any zero-upkeep
   "technique" node's description carries the literal string "[AUDIT:
   upkeep removed - a technique costs nothing to keep knowing; it is not an
   establishment with premises, staff or a standing cost. See JOB 1 upkeep
   audit.]" — seen on `algebra_symbolic`, `atomic_theory`, and even
   `point_contact_transistor` itself (the actual stated goal of the game).
   This is clearly an internal changelog comment that was never meant to
   ship; it appears often enough (every zero-upkeep technique, which is a
   large fraction of the tree) that it stops feeling like a one-off glitch
   and starts feeling like a maintenance gap. It undercuts an otherwise
   very well-written, historically careful text throughout the rest of the
   game.

4. **`rush`, the "start everything affordable, highest-leverage first"
   command, can nearly end a fresh run with no warning.** Tried at turn 1
   of Game 2 with 20,000 starting denarii, it started 38 projects
   simultaneously (many with no relevance to the stated goal), which on the
   very next `step` sent scandal from 0 to 16.1 ("crosses the line in about
   1 year") and money from +20,000 to -2,217 (interest-bearing debt).
   Recovering required manually `stop`-ping 9 projects and a costly
   `bribe`. `rush` is genuinely useful later in the game once there's an
   economic base to absorb it (later uses in the same game, from a
   6-figure income, worked fine and accelerated play a great deal — see
   entry 12 for the full comparison) but is a trap exactly when a new
   player is most likely to try it: turn one, before they understand
   scandal or cashflow mechanics at all. Also: `rush limit:5` (colon
   syntax) was silently ignored rather than erroring or limiting anything.

5. **Staff death/attrition is sometimes silent, and its consequences
   (concerns shutting down) are easy to miss.** Hired artisans/scholars
   die or leave "to better offers" repeatedly through the game, sometimes
   with a one-line event ("you lose 1 scholar to death and to better
   offers"), but the effect (several profitable concerns closing because
   nobody is left to watch them) is only reported after the fact, in a
   combined message, on a later turn. A player who isn't diffing the
   staff-count fields in the status header turn over turn can lose real
   income for several turns without knowing why.

6. **Fog of war ON hides `path <id>` and the "TOTAL DOWNSTREAM... INCLUDING
   THE GOAL" / "STILL TO BUILD BEHIND IT" fields entirely, and the setup
   prompt undersells how large that gap is.** Game 1 (fog on) never once
   let me see more than one step ahead; Game 2 (fog off) let me print the
   *entire* 151-node critical path to the goal on day one and re-check
   remaining-count at will, which is what actually made "trying to win"
   tractable rather than a guessing game. The fog-of-war prompt's neutral
   phrasing ("you cannot see where anything leads" vs. "you can see the
   whole tree and plan a route through it") does not convey how large a
   practical difference this makes for anyone who wants to actually reach
   the goal rather than explore blind.

7. **Minor: some hint text points at a command before its real
   precondition is met, without saying what that precondition is.** Several
   early "HEARD OF, CANNOT BEGIN YET" items in Game 1 said "get at least a
   local patron first: 'start patron_local'" many turns before
   `patron_local` was itself startable (it needed `identity_cover`
   finished first, which the hint never mentioned) — running the suggested
   command just returned "you have never heard of any such thing."

8. **Minor: REPUTATION and SCANDAL share the same numeric danger threshold
   (25/26), displayed adjacently in STANDING**, which caused repeated
   double-takes wondering whether a high, healthy reputation was itself
   dangerous. It never is — only scandal crossing 25 matters — but the
   coincidence of the numbers plus proximity in the display made me
   re-verify this more than once.

### What worked well (worth protecting)
- `why <id>` is excellent: full cost/hours/risk/staff/materials/revenue
  breakdown, honest "nobody has run this here yet - a guess, not a fact"
  framing on unproven revenue, prerequisites, and (fog off) "DIRECTLY
  UNLOCKS" / "TOTAL DOWNSTREAM... INCLUDING THE GOAL" / calendar-floor
  chain summaries. The single most useful command in the game.
- Proactive, specific nudges during `step`: missed-income warnings ("X
  would earn 3,200 a year... and is still shut: it needs 0.00 scholars and
  2.13 craftsmen..."), rising-scandal-trend warnings with a year-to-danger
  estimate, and eminence's "withdraw" option and its real cost explained
  every time it becomes relevant. The game consistently tells you what's
  wrong and how to fix it before you have to ask.
- `risk` gives a full, dated timeline of historical hazards (Antonine
  plague, currency debasement, sack risk, etc.) together with concrete
  mitigations and the current hedge level — turns "history happening to
  you" into a plannable problem rather than a jump-scare, and both hazards
  I actually lived through (Antonine plague, currency debasement) behaved
  exactly as advertised.
- Failure handling is fair and transparent: a failed project loses ~40% of
  sunk hours and a real but bounded chunk of money, then gets a numbered
  retry, rather than being all-or-nothing; `stop <id>` refunds sunk money
  to credit-on-reopen rather than deleting it outright.
- Autosave after every command plus a clearly printed resume command at
  the very start of the session is what saved Game 2 after the year-185
  hang, and generally removes save-scum anxiety entirely.
- The "deputies" mechanic (founder-hours scale past the base 2,000/yr from
  some built institution) is a great, under-signposted answer to the
  founder-hours bottleneck that made Game 1 unwinnable — see entry 14.
- Writing quality throughout is very high: specific, well-researched
  historical grounding (Pliny/Trajan on unlicensed associations, Sejanus
  for eminence, Huntsman's crucible steel), and the treatment of slavery
  (`freedman_staff`: buy, train, and manumit skilled workers, framed
  explicitly as "both the ethical and efficient answer") handles a heavy
  real-world topic thoughtfully rather than glossing over or sensationalizing it.

---

## GAME 2 SETUP: Rome again, this time FOG OF WAR OFF and MORTALITY OFF,
## rich_merchant (20,000 den) start. With fog off, `path point_contact_transistor`
## immediately printed the FULL 151-node dependency chain to victory by name -
## something completely unavailable in Game 1 ("path: not available under fog
## of war"). This is a night-and-day difference in how plannable the game
## feels; see entry 12 for detail.

12. GAME 2, `rush` COMMAND IS A TRAP FOR A NEW PLAYER AT TURN 1. `help`
    describes `rush` as: "start everything you could begin today in one go,
    highest-leverage first; add limit:N to cap it." I tried `rush limit:5`
    hoping to start only 5 things; the `limit:5` (colon) syntax was silently
    ignored (no error) and it started ALL 38 affordable projects at once
    instead. Consequences on the very next `step`:
    - SCANDAL rocketed from 0 to 16.1 in one year ("and RISING: up 16.1 last
      year. At that rate you cross the line in about 1 year(s)") — one step
      away from an ended run, from a single command, with zero warning
      beforehand that starting many things at once reads as suspicious.
    - Money cratered from 20,000 to -2,217 den (interest-bearing arrears)
      because dozens of projects were simultaneously drawing down cash with
      no revenue yet to offset it, and many of them (fin_ferry,
      fin_marine_insurance, air_observation_balloon_tethered, etc.) were NOT
      even on the `path point_contact_transistor` critical-path list I had
      just printed — `rush`'s "highest-leverage" heuristic is generic, not
      aware of my specific declared goal, so it burned scarce cash and
      scandal budget on side technologies irrelevant to winning.
    - Recovery required manually `stop`-ping 9 of the 38 projects, one
      `bribe 2000` (which itself cost 2,000 of the little cash I had left),
      and 4 turns of careful, hire-free austerity before the ledger went
      positive again. A brand-new player who trusted `rush` at turn 1
      without understanding scandal/cashflow mechanics yet (i.e., exactly
      the moment `rush` looks most tempting, before you know better) could
      very plausibly end the run in year 1-2 with no recourse.
    - Silver lining: `stop <id>` is NOT punishing — "The X denarii already
      paid stands to your credit and comes off the bill if you begin again;
      the hours are gone." Only the sunk hours are lost, not the money, so
      recovering from an over-eager `rush` is possible if you catch it in
      time. This is a good safety valve design; it just isn't advertised
      anywhere near the `rush` command itself, where a warning would help
      most.
    RECOMMENDATION: `rush` should warn about projected scandal/cashflow
    impact before committing (a confirmation step showing "this will start
    N projects costing X den/yr and raise scandal by ~Y"), respect a
    `limit N` argument robustly (and/or accept `limit:N` since that's the
    natural syntax to try), and ideally take an optional goal filter so it
    only rushes things on the path to the stated objective.

13. GAME 2, YEAR 185 AD: A `step 3` COMMAND APPEARS TO HAVE HUNG/CRASHED THE
    SIMULATOR OUTRIGHT, SILENTLY, WITH A LARGE LATE-GAME ECONOMY. By this
    point the run had grown very large: 222 technologies I had built, 363
    known in total, 153+ staff (113 artisans, 35 scholars, etc.), 1.56
    million denarii, dozens of running concerns. I sent `step 3` and after
    well over a minute of no output, checked the OS process list directly:
    the `python3 sim/simulator.py` process was simply gone — not running,
    no traceback in the captured stdout/stderr log, no new autosave written
    after it. (System had 13GB free RAM, so not an obvious OOM; more likely
    a hang so severe it got reaped, or an unhandled exception that somehow
    produced no output before the process died — I cannot tell which from
    outside, and a real player has no way to tell either.) I was able to
    recover cleanly by relaunching with the game's own resume command
    (`python3 rome/sim/simulator.py play --session
    /root/.rome-saves/rome_100ad_239.json`), which picked back up from the
    last successful autosave (185 AD) with nothing lost except that one
    `step 3` attempt — so the autosave-per-command design paid for itself
    here and prevented a real disaster. But: a first-time player would have
    no idea to try resuming from a save file if they didn't already know
    that command existed (it IS printed at the very start of the session,
    which is good foresight by the game, but easy to have lost track of 85
    years and hundreds of commands later), and would likely just conclude
    "the game is broken" and give up, especially since nothing on screen
    ever explained what happened. This is a serious scalability/robustness
    concern for exactly the endgame phase the whole design is pointing
    players toward (a large, mature, multi-generational economy) — the
    better you play, the more likely you are to hit whatever this is.

    FOLLOW-UP after resuming: a single `step` (1 year, not 3) at this same
    scale (202 staff, 275+ technologies) took well over two minutes of
    real wall-clock time to return - and DID succeed, jumping from 222 to
    275 self-built technologies in that one year. So the underlying issue
    looks like a straightforward performance/scaling problem (each year of
    simulation gets more expensive as the economy grows, non-linearly
    enough that a 3-year step at this scale apparently exceeds whatever
    tolerance caused it to die) rather than a hard logic bug - but from a
    player's chair the symptom is indistinguishable from a crash: the
    program stops responding and, at least once, actually did stop
    existing as a process. A player without a way to inspect the OS process
    list (i.e. everyone, normally) would have no way to tell "still
    thinking" from "dead" and no in-game guidance to wait it out vs. restart
    vs. resume from save.

## GAME 2 ENDING (stopped year 201 AD, not a loss — stopped by playtest time
## budget, not by the game). Founder alive (mortality off), thriving:
## 8,677,109 denarii, net income deep in six figures/yr, 302 technologies
## built personally (445 known total), 136 scholars + 466 artisans on staff,
## 29,391 founder-hours/year (2,000 base + ~27,000 from "deputies", see
## entry 14), reputation 91, scandal 0.6 (safe), eminence 22 current /
## settling toward 30 (above the 26 danger line - a real, growing risk I
## was actively managing but had not resolved, see entry 16), 75 of the
## original 151 nodes still needed to reach point_contact_transistor, and
## 399 in-game years still remaining to the year-600 horizon. Every trend
## line (income, tech count, hours/year, staff) was accelerating, not
## plateauing. This run reads as clearly ON TRACK TO WIN given enough
## further turns - a complete contrast with Game 1, which was arithmetically
## guaranteed to fail from the moment the founder died. I stopped play here
## because per-step wall-clock cost had grown very large (multi-minute
## waits per single year, see entry 13) and continuing to full completion
## would have needed a large further time budget, not because anything in
## the game stopped me.

16. EMINENCE BECAME A REAL, GROWING THREAT BY YEAR 201 that I did not fully
    resolve before stopping. By 201 AD eminence's *current* value (22) was
    still under the 26 danger line, but its *equilibrium* ("settles near")
    had risen from ~15 (year 166) to 30.4 (year 196) as reputation, wealth
    and visible technology count kept climbing - meaning if I had kept
    playing without intervention it would very likely have crossed 26 and
    started rolling its yearly chance of "confiscation and forced
    retirement" (45%), "patron destroyed" (35%), or outright "end of the
    run" (20%) per `help eminence`. I had built `corpus_dispersed` (hedges
    the hazard) and `corpus_written`, and the game clearly flagged the
    `withdraw` option and its real cost ("halves this now and gives up half
    the reputation you hold above what your work alone is worth") every
    single status screen once it became relevant - excellent, proactive
    warning design, exactly like the scandal trend-line warnings in Game 1.
    This is a genuinely well-designed late-game tension: rapid success
    creates its own existential risk, and the game tells you so clearly
    and with real numbers. I'm flagging it here as unresolved business
    rather than a flaw - a longer session would need to either `withdraw`
    periodically or invest harder in academy_network/corpus_dispersed-style
    mitigations to keep pushing this fast.

14. POSITIVE: "DEPUTIES" — a way to grow founder-hours beyond 2,000/yr. By
    year ~166 AD the prompt started showing e.g. "You: alive (you do not
    age), 4,250 founder-hours free this year (2,000 of your own, plus 1.2
    deputies directing work in your name at 1,800 hours each)". Some
    institution I built via `rush` (never explicitly identified which)
    evidently grants delegated-hours capacity, and it kept growing — by
    year 186 AD I had 10,719 hours/year available, more than 5x my
    "natural" 2,000. This is a fantastic mechanic I wish I had understood
    earlier and deliberately pursued: in Game 1, founder-hours were the
    single immovable bottleneck (and the thing that hard-locks the game on
    death, see entry 10) — if "deputies" is buildable at any real founder
    age/time, this is probably the single highest-leverage thing to chase
    early, and the game does not point at it explicitly anywhere I saw
    (no "why deputies", no obvious id - it looks like it's a side effect of
    something else built, e.g. collegium_licensed or school_founded, not a
    tech you can `why` by name). If true, that's a missed opportunity: the
    game is very good at telling you the cost/value of a NAMED node via
    `why`, but this important compounding mechanic surfaced with no
    signposting at all - I only noticed it by reading the status line
    closely.

15. POSITIVE, GAME 2 vs GAME 1 — `path <id>` and `why <id>`'s "DIRECTLY
    UNLOCKS" / "TOTAL DOWNSTREAM: N thing(s) depend on this -- INCLUDING
    THE GOAL" / "STILL TO BUILD BEHIND IT: X of Y nodes, Z of your hours,
    W den, V-year serial floor" fields (all fog-of-war-off only) are
    excellent, high-value planning tools completely absent under fog of
    war. `path point_contact_transistor` alone turned an intractable-
    feeling "figure out the tech tree by trial and error" problem into a
    literal checklist. This is the single biggest quality-of-life gap
    between the two modes I played, and probably the most important
    thing to communicate to a new player: fog-of-war ON is atmospheric and
    matches the framing text well, but fog-of-war OFF is dramatically more
    playable/winnable for anyone actually trying to reach the goal rather
    than soak in discovery. Worth the game saying this more directly at
    the fog-of-war prompt itself, rather than the current neutral
    "you cannot see where anything leads" / "you can see the whole tree and
    plan a route through it" phrasing, which undersells how large the
    difference actually is in practice.

## FAIRNESS CORRECTION to entry 10 below: re-reading the mortality prompt
## carefully, the game's own text is more balanced than I first gave it
## credit for: "By default the founder does not age, which measures the
## tree rather than a lifespan lottery. Turned on, you get one human life...
## The premise of the whole game is that one is the honest number." So it
## DOES call mortality-on a "lifespan lottery" up front - that is a real,
## fair warning that luck (when you die) governs the outcome. What it still
## never does is tell you, in the moment your founder dies, that the run has
## become unwinnable, or roughly how far through the tree a typical lifetime
## gets you. The prompt copy is fair; the silence afterward is the problem.

## GAME 1 ENDING (year 138 AD): founder died of old age at 73; run becomes
## permanently unwinnable but the game does not say so or stop. Full writeup
## at the end of this log (entry 10). Starting a Game 2 with mortality OFF
## afterward to see the other shape of play, per instructions.

## Observations log (progress checkpoint: year 132 AD, 24 techs built, 21/? nodes toward
## transistor, 15,741 den, revenue ~16,100/yr, 9 staff, reputation 26 / scandal 2.0)

1. Intro screen is well-written and atmospheric — scenario choice screen gives
   population, state capacity, and relative prices for 5 civilizations. Good:
   gives real decision-relevant numbers up front, not just flavor.

2. Fog of war toggle explained clearly: with it on you see built things, what
   you could start today, and "things you have heard of but cannot yet start"
   but not the full tech tree; off shows the whole tree. Chose ON for the
   immersive first-timer experience.

3. Starting wealth menu shows 7 tiers from "destitute" (0 den) to "absurd"
   (1,000,000 den) with a nice note that money mostly changes the *opening*
   years, not the whole game ("buys perhaps a tenth off the time, not a
   different game"). Chose "merchant" (4000 den, "a modest trading capital,
   fund one real venture").

4. Mortality toggle: default is [y/N] i.e. OFF by default (immortal founder),
   but the flavor text says turning it on is closer to "the premise of the
   whole game". A bit of a mixed signal — the bracket default suggests most
   players should leave it off, but the prose argues for on. I turned it ON
   to play it "as intended". Worth flagging: new players may not appreciate
   how consequential this choice is (permadeath vs never dying) from a single
   paragraph before they've seen any of the game's pacing.

5. Game start message gives the resume command
   `python3 rome/sim/simulator.py play --session /root/.rome-saves/rome_100ad_232.json`
   and says progress autosaves after every command. Good — removes save-scum
   anxiety and clarifies persistence model immediately.

6a. `help` gave the actual win condition, which fog-of-war had NOT shown me
    at the start screen: "what you are trying to do: Build point-contact
    transistor, before the horizon at 600." I had to explicitly type `help`
    to learn my goal — the initial prompt only listed command names, not the
    objective. That feels like it should be front and center at game start,
    not one line buried inside a `help` dump.

6b. `available` on turn 1 dumped 209 startable items as a by-subject summary
    table (good) plus "cheapest six" and "most rests on these" tables (very
    good triage aid) plus a "HEARD OF, CANNOT BEGIN YET" section explaining
    exactly which prerequisite is missing for teased items. This is one of
    the best-designed screens so far: even with 209 options it gave me a
    clear way to narrow down. Only complaint: with fog of war on, I have no
    idea if "textiles" (54 available things!) is a fruitful subject or a
    time-sink relative to my one true goal (the transistor) - "why" per item
    is the only way to find out, and there are far too many items to `why`
    them all.

6c. `why <id>` is an excellent info screen: cost breakdown (labour/materials/
    capital, then civ/distance/scarcity/opposition/price multipliers),
    hours, calendar-floor years, % failure risk, staff needed, hired labour,
    materials, upkeep, revenue (often "nobody has run this here yet - a
    guess, not a fact" — nice honesty about revenue uncertainty),
    prerequisites, and "HOW MUCH RESTS ON THIS" (a qualitative dependency-
    count hint: none/a fair amount/much/a great deal/almost everything/ALL).
    This is the single most useful command for decision-making so far.
    `why arithmetic_positional` explicitly told me "Highest return on
    personal hours in the entire tree" — a strong, specific, and (per my
    play so far) trustworthy signal. Good: the game is willing to just tell
    you the answer sometimes.

6d. Multiple projects can run concurrently (I ran arithmetic_positional +
    hom_eraser_breadcrumb together turn 1, then scientific_method +
    horse_collar together turn 2), limited by founder-hours (2000/yr) and by
    staff (scholars/craftsmen) each project needs. Good — lets a solo player
    parallelize instead of being railroaded into one thing at a time.

6e. IMPORTANT RULE, stated plainly in `help`: "Finishing something earns you
    nothing. A concern earns when you 'open' it, and costs its upkeep only
    then too." This is a real trap for a first-time player: you could
    finish ("COMPLETE") a dozen technologies and see zero income from any of
    them because you forgot to `open` each one individually. The game does
    warn about it in the completion event text itself though — e.g.
    "COMPLETED: ... You know how; nothing is earning yet - 'open
    arithmetic_positional' to run it" — which is a good just-in-time nudge
    that stopped me from missing it.

6f. Opening `arithmetic_positional` (150-425 projected) actually opened at
    "earns 300 a year and costs 100 a year to run" — a concrete number
    replacing the earlier revenue *range* estimate the moment you commit.
    Nice level of specificity.

6g. BUG — leaked developer/audit note in player-facing text. `why
    algebra_symbolic` includes, inline in the flavor description: "[AUDIT:
    upkeep removed - a technique costs nothing to keep knowing; it is not an
    establishment with premises, staff or a standing cost. See JOB 1 upkeep
    audit.]" This reads exactly like an internal changelog/dev comment that
    was meant to be stripped before shipping, not narrative text. It breaks
    immersion badly and looks unprofessional. Will watch for more of these.

6h-UPDATE2 (Game 2, fog off): now that `why <id>` can show real prerequisite
    chains, `patron_local`'s only prerequisite is `identity_cover` (finished)
    — nothing about reputation at all. So the mystery in Game 1 was probably
    just that I hadn't finished `identity_cover` yet when the OTHER items'
    hint text ("get at least a local patron first: 'start patron_local'")
    started showing — the hint simply didn't mention what patron_local
    itself was waiting on. Filed as a hint-text-completeness issue, not a
    broken id.

6h-UPDATE (year 114): `patron_local` ("Secure a town patron") eventually
    appeared on its own in `available` (as a real startable item, cost
    1,200, "ALL" rests) once my reputation had grown (was 19-21 by then).
    So it wasn't a permanently broken id — it just weirdly told me to
    `start patron_local` many turns (years 100-113) before that command
    could possibly work, with no explanation of what threshold unlocks it.
    Downgrading this from "dead end" to "misleading/premature hint": the
    error text should say what's missing (e.g. "needs reputation >= X") the
    same way prerequisite-item hints do, instead of implying the fix is one
    command away.

6h-ORIGINAL. BUG — dead-end hint text. Several "HEARD OF, CANNOT BEGIN YET" entries
    read e.g. "ag2_coulter: the state is wary of this (state interest -0.6);
    get at least a local patron first: 'start patron_local'" — repeated
    verbatim for ~9 different items. I typed exactly what it told me:
    `start patron_local` and also `why patron_local`. Both were REFUSED with
    "you have never heard of any such thing. You know what you have built
    and what you could begin next; nothing tells you what lies beyond
    that." So the game's own suggested command does not work — either
    `patron_local` is not its real id, or it requires some other prior step
    the hint doesn't mention. This is a real dead end for a first-time
    player: the game explicitly tells you the fix and the fix doesn't work.

7. RANDOM HAZARD EVENTS: two turns in a row (year 101->102 and 102->103) an
   identical-flavor event fired: "fire in the insula district, where the
   tenements stand six storeys in wood: it destroyed 341 denarii" (then 269
   denarii the next year). No warning beforehand, no way (that I've found
   yet) to prevent it, and the flavor text is verbatim identical both times
   apart from the number. Two identical fires back-to-back reads as a bug or
   at least a very repetitive event pool this early in the game — a little
   variety in phrasing would help sell it as a "world happening around you"
   rather than a scripted recurring tax. Will check `risk`/`help risk` to
   see if this is explained/mitigable.

8. SCANDAL climbed from 0 to 1.9 in the turn where I completed
   `scientific_method` ("Contradicting Aristotle and Galen in public is a
   social act... Expect organised opposition"), and the game proactively
   flagged the trend: "and RISING: up 1.9 last year. At that rate you cross
   the line in about 13 year(s)". That's a genuinely useful forward-looking
   warning I didn't have to ask for — good design, prevents a silent death
   spiral.

8b. The "fire in the insula district" event fired 4 turns in a row with
    IDENTICAL wording (only the denarii lost changed: 341, 269, 213, 251),
    then did NOT fire turn 5 or several turns after. So it's probabilistic
    background flavor/cost, not guaranteed each year as I first suspected —
    correcting my earlier note. Still, 4 in a row with copy-paste-identical
    phrasing felt like a bug the first time I saw it; a bit of text variance
    would sell it better even though the underlying frequency is fine.

8c. `why point_contact_transistor` (the stated win condition) IS answerable
    even under fog of war, and is genuinely useful: tier 5, cost 33,970 den,
    900 personal hours, 4-year calendar floor, 45% failure risk, needs 25
    scholars + 20 artisans on staff (society literacy caps hired scholars at
    6 total!), needs materials germanium_g/gold_g/phosphor_bronze_g, and
    says plainly "this needs 7 other things you have not heard of yet".
    Good design: the player can always sanity-check the shape of the final
    goal even without seeing the path. Also repeats the same "[AUDIT: upkeep
    removed...]" leaked dev-note text (see 6g) — so that string is a
    systemic template artifact stamped onto every zero-upkeep "technique"
    entry, not a one-off. Raising this bug's severity accordingly: it will
    appear constantly through a full playthrough.

8d. STAFF CAP is a real, well-telegraphed structural bottleneck: "this
    society's literacy will never let you HIRE more than 6.0 of [scholar-
    type trades] in total, however rich you are." The transistor itself
    wants 25 scholars. The fix path is visible (schools/academies/printing/
    paper raise the cap) but expensive (school_founded: 11,500 den, all
    2,000 of a year's founder-hours, 4-year floor set by "diffusion" that
    "money cannot buy down", 2,500 den/yr upkeep). This is clearly the
    central mid-game economic wall the whole strategy has to be built around
    — good, legible long-term design, not a gotcha.

8e. FIRST FAILURE observed: `identity_cover` (5% stated risk) failed on its
    first attempt: "FAILED at Establish a respectable cover identity: it did
    not work. 40% of the hours are to do again (200 of your own) and 632 is
    gone. Attempt 2." So failure does not erase all progress — it claws back
    a chunk of hours/money and forces a retry, rather than being an
    all-or-nothing coin flip. That is a fair, well-communicated way to
    handle risk; losing 632 sunk den still stung on a thin cash balance
    (dropped me from 1,620 to 845 den in one turn) but didn't end the run.

9a. GREAT FEATURE, worth protecting: the game proactively surfaces missed
    income during `step` without being asked: "EVENT 131: lens_grinding
    would earn 3,200 a year against 400 of upkeep and is still shut: nobody
    free to keep an eye on it: it needs 0.00 scholars and 2.13 craftsmen to
    supervise, and you have 1.50 and 0.78 not already watching something
    else. Hire, teach, or close something." This told me exactly what was
    wrong and exactly how to fix it (hire more craftsmen) without me having
    to dig through `ventures`/`labour`. This is the single best piece of
    UX in the game so far — it turns a silent opportunity cost into an
    actionable nudge.

9b. STAFF ATTRITION IS A RECURRING, SOMETIMES-SILENT DRAIN. Across the game
    so far, hired staff (artisans, scholars) have died/left several times
    (turn counts dropping, e.g. "art 3"->"art 2", "sch 2"->"sch 1") without
    always being called out individually — only the downstream CONSEQUENCE
    gets a message ("nobody left to keep an eye on 3 concerns, so X, Y, Z
    closed"), not the death itself. A player who isn't checking `state`'s
    headcount every single turn could easily miss *why* three revenue
    streams silently went to zero between one glance and the next. This
    happened to me at least twice (~year 111 and ~year 118). Recommend the
    game announce staff losses themselves, not just their downstream
    effects, or at least make "art 3" -> "art 2" visually obvious in the
    step output (it currently only shows in the one-line prompt/state
    header, which is easy to not compare turn to turn).

9c. REPUTATION (danger line 25) and SCANDAL (danger line 25, worded
    "dangerous above 25") share the same threshold value and appear
    adjacent in the STANDING block, which made me double-take more than
    once wondering if my reputation of 25-26 was itself dangerous. It is
    not — only scandal crossing 25 matters. Coincidental shared numbers
    between two meters with opposite "goodness" (high reputation is good,
    high scandal is bad) is a minor but real source of confusion; a
    different threshold value or clearer separation in the display would
    help.

9d. FAILURES ARE FREQUENT ENOUGH TO PLAN AROUND, not rare edge cases. By
    year 132 I have hit failure on: identity_cover (once), workshop_first
    (once), lens_grinding (once), precision_three_plate (once) — roughly 4
    failures across ~15-20 started projects, consistent with the stated
    risk percentages (5-20%). Each failure costs ~40% rework (hours) plus a
    chunk of the money already sunk (not the full total, but not trivial —
    632, 2303, 756, 1174 den lost on the four failures I've seen). Good
    that this is transparent and bounded rather than catastrophic, but a
    first-time player who doesn't internalize "failure risk is real and
    recurring" could be caught flat-footed on a project they assumed was a
    sure thing.

10. **GAME 1 ENDING — THE FOUNDER DIED, AND THE GAME QUIETLY BECAME
    UNWINNABLE.** At the transition from year 137 to 138 AD (turn ~38 of my
    played life), a multi-year `step 3` stopped itself early with a genuinely
    great piece of UX: "stopped after 2 of the 3 years you asked for:
    something happened that you warned yourself about and should see before
    more time passes." The event itself: "*** THE FOUNDER HAS DIED, aged
    about 73, in 138 ***" / "the founder dies, aged about 73". I had turned
    mortality ON at setup.

    What happened next is the single biggest problem I found in this
    playtest. The game does NOT end, show a game-over screen, or offer any
    successor/heir mechanic. `state` keeps working; it just now reads "You:
    DEAD (aged about 73 at death, in 138) and ageing, 0 founder-hours free
    this year" forever, every future year, with `you:0 hr` permanently in
    the prompt. Every project in the tech tree I checked lists a nonzero
    "YOUR HOURS: N" requirement (the point-contact transistor itself needs
    900) — and `start` on a founder-hours project still nominally succeeds
    ("started: potash_soda") but then sits at "0% of your hours spent, 0
    still owed - waiting on your hours" forever, because there is no way to
    ever generate another founder-hour. I confirmed there is no rescue path:
    - `help commands` lists no heir/successor/inheritance command at all.
    - `bounty <id>` looks like an escape hatch (pay money instead of
      founder-hours) but is explicitly gated: "REFUSED: not bounty-eligible
      (tier 1, category chemistry): a craftsman in The Roman Empire under
      Trajan could not recognise success at this without understanding the
      theory, so there is nothing to award the prize for. A bounty works
      where the craft already exists here and success is visible." Only
      simple, already-locally-legible crafts are bounty-eligible (several
      early items I built did show "BOUNTY: yes, could be posted as a
      public prize" — horse_collar, lens_grinding, precision_three_plate,
      lead_metallurgy). The win condition itself, `point_contact_transistor`
      (tier 5, "confidence A", needs quantum_solidstate_theory among its
      unmet prerequisites), shows no BOUNTY line at all — it is pure
      founder-hours-gated theory, permanently unreachable once the founder
      is dead.
    - Existing opened concerns keep earning money forever (the economy
      survives you), so the game happily lets you go on hiring staff,
      watching `money` grow, and typing `available`/`why`/`start` into a
      tree that can now never advance past whatever bounty-eligible crumbs
      remain. Nothing in the UI ever says "you cannot win anymore."

    Why this matters so much: the setup screen's own sales pitch for turning
    mortality on was "The premise of the whole game is that one is the
    honest number" — a strong nudge toward playing exactly the mode that
    quietly self-destructs. The goal (transistor) needs a chain that by
    year 138 I had only gotten 25 nodes into (of an unknown, clearly much
    longer, total), during which time I was already spending nearly all
    2,000 yearly founder-hours on research every single year with a strong
    economy behind me. At that rate a single ~35-75 year working lifespan
    (my founder started at ~35 and died at 73, i.e. roughly 38 working
    years) does not look close to enough to reach a tier-5 "confidence A"
    endgame technology that still needs 7+ unseen prerequisites on top of
    the visible ones — meaning mortality-on may not merely be "harder," it
    may be effectively unwinnable by design, or nearly so, with no in-game
    indication of that fact before or after the fact. A first-time player
    who takes the game's own framing at face value (turn mortality on for
    "the honest" experience) can sink 30+ turns of careful, successful play
    into a run that was very likely dead on arrival the moment they answered
    that one early yes/no prompt, and the game will never tell them.

    RECOMMENDATION: either (a) add a successor/heir mechanic so a dynasty
    can carry founder-hours forward, (b) have the game explicitly declare
    the run over/lost on founder death when no path to the goal remains
    reachable, or at minimum print something like "with the founder dead
    and no heir, N technologies (including the goal) can never be
    completed" so the player isn't left issuing commands into a stalled
    world without knowing it, or (c) make the mortality-on setup prompt
    honestly convey the odds ("most players will not finish the tree
    within one lifetime; this tests how far you get, not whether you
    finish") rather than framing it as simply the more "honest" choice.

11. Whether to `open` a completed research node isn't always obvious:
   `scientific_method` shows EARNS/YR 0, COSTS/YR 100 if opened — i.e.
   opening it would be pure upkeep cost for no revenue. Its value ("a
   multiplier on every research node thereafter") is presumably inherent to
   having *built* it, not to running/opening it as a business concern. But
   the game does not say this outright anywhere I've seen — I inferred it.
   A first-time player could easily either (a) open it out of habit
   ("finishing earns nothing, so I should open everything") and eat
   needless upkeep forever, or (b) never realize the multiplier is already
   active. Left it un-opened.

6. Opening status/command line:
   `[100 AD | 4000 den | you:2000 hr | sch 1 art 1 | rep 5] >`
   Told the 5 starter commands: state, available, why <name>, start <name>,
   step, plus stuck/help/quit. "sch 1 art 1" and "rep 5" are NOT explained
   yet at this point — I don't know what "sch" and "art" mean (scholarship?
   artisanship? some skill/attribute pair) or what "rep" (reputation?) does
   or its scale. Will check with 'state' next.
