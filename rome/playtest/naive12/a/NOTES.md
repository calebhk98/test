# Playtest Log - naive12/a
Game: "ONE PERSON, AND EVERYTHING THEY KNOW" (rome/sim/simulator.py)
Player: fresh, no prior knowledge, told not to read source/docs.

Setup chosen: Roman Empire under Trajan, 100 AD; fog of war ON; starting wealth
"merchant" (4000 den); mortality ON (aging/death enabled) — chose this because
the game's own prompt text said "the premise of the whole game is that one is
the honest number", which read like a nudge toward the "real" mode.

(TOP PROBLEMS section to be filled in at the end once I have enough evidence.)

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
