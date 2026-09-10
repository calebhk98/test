# TOP PROBLEMS

Ordered by how much they cost me. I played Rome/100 AD, fog on, poor scholar,
no ageing, and lost at the 600 AD horizon with 1,944 technologies built, about
thirty nodes short of the point-contact transistor.

1. **`start` and `restore` deadlock each other on any technology you lose to a
   sacking — this alone probably cost me the game.** A third-century sack
   destroyed `precision_three_plate`. `start` said "restore it instead"; `restore`
   said "you no longer know how to do that; it has to be built again". `open` and
   `mothball` both refused too. Since that node gates master_screw -> screw_lathe
   -> the entire precision branch, `available` printed **"0 startable now /
   nothing"** for 180 game years while I sat on a quarter of a billion denarii.
   The only escape was guessing `bounty <id>`, which nothing suggests. Eight
   other lost technologies were stuck the same way at the final turn.

2. **The critical path is only ever revealed inside refusal messages, and only
   sometimes.** `patron_local -> workshop_first -> freedman_staff -> citizenship
   -> collegium_licensed -> school_founded` is the backbone of the entire game.
   I hit a hard six-person staff ceiling at year 117 and stayed there until year
   149 — thirty years, with 20,000 idle denarii — because the "cannot hire"
   message listed hire/commission/slaves and did not mention `workshop_first`.
   One day the same message silently grew a `build workshop_first` clause. `state`
   points at `how_to_grow_staff -> labour`; `labour` says nothing at all about
   capacity, workshops, patrons or the literacy ceiling. That pointer is a dead
   end and the capacity number appears nowhere until you exceed it.

3. **The opening the game recommends bankrupts you, and the debt trap that
   follows is unescapable and unexplained.** `available` heads its list with
   "MOST RESTS ON THESE: identity_cover 1,580 / arithmetic_positional 1,032 /
   horse_collar 709 / units_standards 444 / scientific_method 230". You start
   with 400 denarii. I started two of them, went into arrears, and discovered
   that arrears freeze *all* project progress ("the hours offered this year did
   almost nothing") while 11% interest compounds. Nothing warned me at `start`,
   even though the engine clearly can — later, at scale, it refuses politely:
   "you already owe 6,045 denarii on work in hand; this would take it to
   74,497... Finish or stop something first." The things that actually work on
   turn one (`hom_toys_dolls` 75 den for 150/yr, `tex_horizontal_loom`) are not
   hinted at anywhere.

4. **`available` offers work that cannot be finished, then destroys the money.**
   `HALTED ...: there is nobody here who can do this work (engineer). What you
   spent is lost` — seven at once, all of which `why` had reported as "STATUS:
   CAN START NOW". Meanwhile the specialist trades are capped at 5.9 "in total,
   ever, at any price" and mine never moved off 2.0 despite paper, printing, a
   university, three academies and 148 scholars — while `train electrician 20`
   in the very same command batch succeeded and gave me 27. That inconsistency
   left half the tree permanently out of reach.

5. **The numbers on the tin are not the numbers you get.** `why` and `ventures`
   both advertise `REVENUE / EARNS/YR: 400`; the ledger the same turn paid
   266.7 — exactly two-thirds, across every single line — and years later paid
   409. Nothing says a multiplier exists. Separately, `work scholar 400` earned
   128 denarii and silently cut my standing revenue by 46.7/yr, because that
   revenue is secretly proportional to unspent founder-hours. And `money`
   attributed all my income to `med_cataract_couching` and `med_trepanation`
   while `ventures` said "RUNNING: nothing / Only what you are RUNNING earns
   anything".

6. **The ending tells you nothing.** "You built 1944 things of your own and did
   not reach point-contact transistor." No distance, no last missing link, no
   sense of which century I fell behind in. I had to start a *second game with
   fog off* and run `path point_contact_transistor` to learn the goal is 142
   nodes and that I had finished all of thermometer, master_screw, screw_lathe,
   interchangeable_parts, steam_watt and electroplating and died at
   `copper_refining <- cap_pure_4N`. That is a thrilling fact and the game hid
   it from me.

7. **Smaller, but constant:** the 17-25 line "HEARD OF, CANNOT BEGIN YET" block
   is reprinted in full after *every* `available` call, including ones that
   match nothing; `policy <x> on` reprints the whole 25-line policy manual for a
   one-line change; `why point_contact_transistor` answers "you have never heard
   of any such thing" on a screen whose next line says "Aiming at: Point-contact
   transistor"; `available subject electricity` returns two optical signalling
   technologies; the failure message "60% of the work is to do again" is
   followed by a progress bar reading "60% of your hours spent", so you cannot
   tell whether you kept 60% or lost it; `hire` silently charges a full year's
   wages up front and `fire` refunds none of it; "no viable option in a required
   substitution group (fuel, vessel, etc.)" is the only blocker message that
   does not tell you what to do, and I never worked it out.

# Playtest notes — naive player, session naive8/a

(Notes written as I go. TOP PROBLEMS section will be added at the top at the end.)

## Session 1 — first contact

Ran `python3 rome/sim/simulator.py`. Title screen:
"ONE PERSON, AND EVERYTHING THEY KNOW" — you're a modern-knowledge person dropped
into a pre-industrial society. Five settings to choose from (Han 100, Rome 100,
Viking 900, England 1300, Mexica 1500).

Good: the framing paragraph is genuinely evocative and told me the core tension
(knowing is free, building is not) in three sentences.

Confusing already: with an empty/EOF input the prompt repeats forever-ish and
printed the hint "-- a number from 1 to 5." twice. Minor.

## Session 1, run A (Rome, fog on, poor_scholar, no ageing) — I bankrupted myself in 3 turns

What I did: `hire artisan 1`, `start horse_collar` (709 den, "earns 900/yr"),
`start scientific_method` (230 den), `step 1`. I had 400 denarii.

The game let me commit 939 denarii of projects with 400 denarii in hand and
never warned me. One `step` later:

    Money: -586.9 den    net -788.1 den/yr
    horse_collar   53% of your hours spent, 332.2 still owed - waiting on your hours
      in arrears: after fixed costs there is nothing left to draw on, so the
      hours offered this year did almost nothing

**This is a death spiral and nothing signposts it.** Once you are in arrears:
* projects stop progressing entirely ("the hours offered this year did almost nothing"),
* interest runs at 11% and compounds,
* so the debt grows and the projects that would have paid it off stay frozen.
The only escape is `work <trade> 2000` for several years, which is buried in
`help commands` as one line ("work <trade> <hours>: do an ordinary job for
ordinary pay") and which I only found by hunting.

What I wanted: when I type `start` on something I cannot afford, a line like
"this will put you 539 den into arrears; arrears stop all project work".
`start` already prints "the bill you have taken on: 709.4" — it knows. It
could just as easily say what that does to me.

### `work` secretly cancels your other income
`work scholar 400` printed `earned: 128`. Then `money` showed revenue had
dropped from 233.5/yr to 186.8/yr — exactly 400/2000 of it. So my standing
income (a medical practice) is proportional to my *unspent founder hours*, and
working for wages cannibalises it. Net effect of that command was about +81
den, not +128. Nothing in `help`, in `work`'s output, or in `money` says the
revenue line depends on my free hours. That is a hidden mechanic that makes
the one escape hatch from bankruptcy worse than it looks.

### `ventures` and `money` disagree
`money` says:
    Revenue: 233.5 den/yr
      from: med_cataract_couching 166.7 / med_trepanation 66.7
`ventures` at the same moment says:
    RUNNING
      nothing
and then insists "Only what you are RUNNING earns anything". Two screens, two
answers. I could not find any way to see or manage the two things that were
actually paying my bills.

### The failure message reads as a bug
    EVENT 106: FAILED at ... horse collar: it did not work. 60% of the work is
    to do again and 334 is gone. Attempt 2.
Next line of `state`:
    horse_collar  60% of your hours spent
So "60% of the work is to do again" and "60% ... spent" are the same number
shown two opposite ways. I genuinely could not tell whether I had lost 60% or
kept 60%. (I think it kept 60%: the progress bar went 53% -> 60%. Which makes
the message wrong.)

### Odd: `available subject electricity` lists two optical/flag signalling techs
    AVAILABLE: 2 startable now  1-2 in 'electricity'
    com_optical_codebook  Codebook for optical s...
    com_signal_flags      Signal flags for marit...
Neither is electricity.

### Pleasant surprises
* The scenario blurbs are excellent, and the "WHAT IS MISSING / Not the ideas.
  The instruments." paragraph made me want to play.
* `risk` is superb: a dated list of everything history is about to do to me
  ("[165-180] Antonine plague ... staff loss after what you have built: 28%"),
  with what would blunt each. Best screen in the game.
* `why <id>` is genuinely informative, historically careful, and shows the
  cost breakdown with multipliers.
* Autosave after every command, and the resume line printed on exit.

## Session 2 (fresh game, same settings) — the actual opening the game wants

Restarted. This time I ignored the "MOST RESTS ON THESE" list the game puts in
front of you on `available` and instead did `available all`, eyeballed the
EARNS/YR column, and started the two cheapest profitable things:
`hom_toys_dolls` (75 den, earns 150) and `tex_horizontal_loom` (226, earns 400).
Both finished in the first year. By 105 AD I was at +893 den/yr; by 121 AD at
+2,112 den/yr with 42 technologies.

**So the game's own front page recommends the wrong opening.** `available` puts
`identity_cover` (1,580 den), `units_standards` (444), `arithmetic_positional`
(1,032), `scientific_method` (230) and `horse_collar` (709) under the banner
"MOST RESTS ON THESE". Every one of them is unaffordable-or-marginal on turn 1
with 400 denarii, and taking any two of them bankrupts you. The things that
actually work are toys, looms and dye — which appear nowhere in any hint.
A pointer like "you will need an income before you need a foundation" would
have saved me a whole ruined playthrough.

### `hire` charges a full year's wages the instant you type it
`hire artisan 3` + `hire scholar 1` took 1,424 den out of 1,670 immediately and
then charged 1,287/yr on top. Nothing in `help labour` ("hire smith 3 - paid
every year") suggests there is an up-front charge at all, let alone a whole
year in advance. That single command put me back into arrears. And `fire` gives
none of it back.

### `open` refused me on a tie
    REFUSED: nobody free to keep an eye on it: it needs 0.0 scholars and
    0.2 craftsmen to supervise, and you have 1.0 and 0.2 not already
    watching something else.
Needs 0.2, I have 0.2, refused. Reads as an off-by-a-rounding-error bug: the
message is literally arguing my case for me.

### The staff cap is invisible until you hit it
    REFUSED: you can supervise, house and teach 3.66 more people, not 4 -
    3 is the most whole people you can take.
    ...later...
    REFUSED: you can supervise, house and teach 0.89 more people, not 2 -
    you have no room for even one.
`state` never shows this number. `labour` never shows it. The `state` screen
even points at `how_to_grow_staff -> labour`, and `labour` says nothing about
capacity or how to raise it. I still do not know what governs it.

### The stated REVENUE is not the revenue
`why tex_horizontal_loom` says `REVENUE: 400 den/yr`. `ventures` says
`EARNS/YR 400`. The ledger, the same turn, says `tex_horizontal_loom 266.7`.
Every line was exactly 2/3 of its advertised figure. (Later, as reputation
rose, they went *above* the advertised figure — 409.) So the headline number
is neither a floor nor a ceiling nor what you get, and nothing says what the
multiplier is or that one exists.

### Failure messages, again
Two projects failed *in the same year they were started* and one failed three
years running at a stated 6-10% risk. It may be honest dice, but "FAILED ...
Attempt 3" three times in five years on 6% odds made me suspect the number on
the tin. There is also no per-project record of attempts anywhere but the
scrolling event log.

### `why` refuses to tell me about my own goal
    > why point_contact_transistor
    REFUSED: you have never heard of any such thing.
    Did you mean: fin_contract_law
The line directly above it on every single `state` screen reads
`Aiming at: Point-contact transistor`. Being told I have never heard of the
thing the game keeps telling me I am aiming at is the single most jarring
moment so far. (I understand the fog rule. Then don't print the target.)

### The "HEARD OF, CANNOT BEGIN YET" block is printed in full every time
It is 17 lines, it is global, and it is appended to *every* `available` call —
including `available find patron`, which found nothing and still printed all 17
lines. Three `available` calls in one batch = 51 lines of identical text.

### Pleasant surprises (2)
* The blocked-tech reasons are excellent and actionable: "needs 2 trained
  scholars, you have 1.0 (you are one of them). To get more scholars: hire
  scholar 2 ... or build school_founded". "this needs engineers and there are
  none in this society. Teach one: train engineer 2 (about 450 of your own
  hours each, two years)". That is exactly the right amount of hand-holding.
* "this needs 1 other thing you have not heard of yet, and you do not yet know
  what it is" is a lovely way to express fog.
* `what the market will not absorb  -30.1` appearing in the ledger as revenue
  grew is a great touch, though nothing explains it.
* The sc2_* institutional technologies (peer review, negative results, the
  equals sign, the doctorate) with 8-20 year calendar floors are a genuinely
  delightful idea and the best content in the game.

## The critical path is hidden inside error messages

This is the thing I would most want fixed. The backbone of the whole game turns
out to be:

    patron_local -> workshop_first -> freedman_staff -> citizenship ->
    collegium_licensed -> school_founded

I found every single one of those by accident, in the text of a *refusal*:

    REFUSED: you can supervise, house and teach 2.27 more people, not 20 ...
      To get more artisans: hire smith 3 ...; or commission smith 400 ...;
      buy slaves N then manumit ...

That was the message at year 136. At year 149 the *same* refusal read:

    ... or commission smith 400 ...; build workshop_first (you need somewhere
    for them to work); buy slaves N ...

The `build workshop_first` clause simply appeared one day. I spent **thirty
in-game years and 20,000 idle denarii** stuck at a hard ceiling of six staff,
repeatedly told I could not hire anyone, with no hint that a building existed
that would fix it — and then the hint appeared unannounced in a message I only
read because I was retrying a command out of frustration. The same happened
again with `freedman_staff` at year 151 and again with the scholar cap
("this society's literacy will not supply more than 5.9 scholars in total,
ever ... Raise literacy_general or literacy_elite").

`patron_local` and `workshop_first` are not obscure: they are literally called
"Secure a town patron" and "First workshop and laboratory", they gate
case_hardening -> precision_three_plate -> balance_analytical -> thermometer,
and `why workshop_first` says "HOW MUCH RESTS ON THIS: almost everything". They
just never once appeared in `available` output where I would look for them,
because `available` sorts by cost and by subject and I never thought to page
through 200 entries looking for a building.

Meanwhile `state` has a hint line that says `how_to_grow_staff -> labour`, and
`labour` says nothing whatsoever about capacity, workshops, patrons, or the
literacy ceiling. That pointer is a dead end.

## Other things from the middle game

* `EVENT 165: Antonine plague: staff -28%, 22,326 gone with the trade that
  stopped` — fired four separate times (165, 170, 172, 174) for a total of
  ~120,000 denarii. The `risk` screen presents it as one dated event; nothing
  says it can recur every year or two for its whole window.
* Failure rates feel much higher than advertised. Of five projects started in
  157 AD at stated risks of 10-25%, four failed. Over the game nearly every
  multi-year project failed at least once. If the risk is rolled per year (which
  would explain it) then "FAILURE RISK: 25%" on a 2-year project is misleading;
  if it is per attempt, something is off.
* `hire scholar 6` -> "this society's literacy will not supply more than 5.9
  scholars in total, ever, at any price". Good message. But `labour` had just
  listed `scholar` under "YOU COULD HIRE", and after I hit the ceiling scholar
  silently vanished from that list with no explanation.
* My auto-hiring filled all my staff slots with smiths and quietly starved the
  artisans down to 1.1, because `hire` never says "this will use N of your M
  remaining places". The cap is only ever quoted at you when you exceed it.
* Nice: at ~180 AD `state` started reading "3,365 founder-hours free this year
  (2,000 of your own, plus 0.76 deputies directing work in your name at 1,800
  hours each)". Deputies arriving from the school is a lovely, well-explained
  payoff.
* Nice: `REFUSED: you already owe 6,045 denarii on work in hand; this would
  take it to 74,497, and between cash and credit you can raise 62,903. Finish
  or stop something first.` This is exactly the warning I wanted at the start
  of the game and never got when I was starting 939 denarii of work with 400 in
  hand. Why does this check exist for big numbers and not small ones?

## Endgame (session 2 continued) — I lost, at 600 AD, with half a billion denarii

Final line:

    *** THE RUN HAS ENDED: the horizon at 600 AD is reached. You built 1944
    things of your own and did not reach point-contact transistor. ***

Final position: 470,504,293 denarii, +5.5M/yr, 504 employees, 2,088
technologies, reputation 98.8, protection 92%.

Afterwards I started a second game with fog OFF purely to find out how badly I
had lost, and ran `path point_contact_transistor`:

    remaining count: 142
    remaining: arithmetic_positional, identity_cover, scientific_method, ...
    ... zone_refining, single_crystal, point_contact_transistor

Then I checked my finished game against that list. I had **thermometer,
master_screw, screw_lathe, interchangeable_parts, steam_watt, electroplating,
cap_vac_1torr — all DONE**. I was blocked at `copper_refining` (missing
`cap_pure_4N`), and behind that the dynamo / vacuum-tube / germanium chain. So
I finished perhaps twenty to forty nodes short of the win after five hundred
years and two thousand technologies.

That makes the two big blockers below not cosmetic. **The ~150 years I lost to
the invisible staff ceiling, and the ~180 years I lost to the
precision_three_plate deadlock, are almost exactly the margin by which I
lost.**

### The hard-lock: `start` and `restore` each tell you to use the other

A sacking during the third-century crisis destroyed `precision_three_plate`.
From then on, for 180 game years:

    > start precision_three_plate
    REFUSED: you built this once and let it go; you already know how, so
    restoring it is cheaper than starting over: restore precision_three_plate
    for about 980 denarii

    > restore precision_three_plate
    REFUSED: you no longer know how to do that; it has to be built again
    rather than reopened

`open` -> "you have not worked out how to do that yet, so there is nothing to
open". `mothball` -> "you have not built that". Four commands, four refusals,
two of them contradicting each other in consecutive lines. `why
precision_three_plate` meanwhile says "HOW MUCH RESTS ON THIS: almost
everything", which is true: it gates master_screw -> screw_lathe -> the entire
precision and instrument half of the tree, i.e. the road to the goal.

For 180 years `available` reported **"AVAILABLE: 0 startable now / nothing"**
while I had a quarter of a billion denarii and 458 employees. I sat there
stepping five years at a time watching the technology count not move. The only
thing that broke it was guessing at `bounty precision_three_plate` (7,335 den),
which posted a public prize and quietly put the project back in RUNNING. Nothing
anywhere suggests bounty is the way out of that state.

The same message appears for eight other lost technologies (`fin_tariff`,
`tl_coil_spring`, `tl_muffler`, `tl_universal_joint`, `tl_velocipede`,
`tl_water_pump`, `fin_trade_union`, `fin_bill_exchange`) and `restore` refuses
every one of them, right up to the last turn of the game.

### The specialist trades are capped at 5.9 forever, inconsistently

    > train machinist 20
    REFUSED: this society's literacy will not supply more than 5.9 machinists
    in total, ever, at any price; you already have 2.0 ...
    Raise literacy_general or literacy_elite -- printing, schools and
    libraries do -- to widen this pool.

By 460 AD I had rag paper, movable type, a university, three academies, a
school, the corpus written and dispersed, 148 scholars and 2,000
technologies. The machinist / chemist / engineer / optician ceiling was still
5.9 and my count of each was still exactly 2.0, all the way to 600 AD. But
`train electrician 20` in the same batch of commands **succeeded**, and I
finished with 27 electricians. Same command, same turn, same literacy, five
trades refused and one allowed. Either the cap is not actually tied to
literacy or electricians are exempt for some reason nothing explains. Half the
tree wants machinists.

### Things that killed projects without warning

    EVENT 195: HALTED mt2_classifier_size_separation: there is nobody here who
    can do this work (engineer). What you spent is lost

Seven projects halted at once and burned their spend. Every one had been
listed by `available` as startable, and `why` had shown "STATUS: CAN START
NOW". `available` will happily offer you work that cannot be finished with the
staff you have and then destroy the money. `start` knows how to refuse for
money ("you already owe 6,045 denarii on work in hand..."); it should refuse,
or at least warn, for people.

### "no viable option in a required substitution group (fuel, vessel, etc.)"

Eleven technologies were blocked by this, including several I needed. It is
the only blocker message in the game that does not tell you what to do about
it, it is not in `help`, "substitution group" is not a phrase used anywhere
else, and "(fuel, vessel, etc.)" is not a list of my options, it is a list of
examples of the kind of thing it might be. I never worked out what to build.

### The ending has nothing in it

After 500 years the game says how many things I built and that I did not win,
and stops. It does not say how close I came, what the last missing links were,
which decade I fell behind in, what a good run looks like, or what I should
try differently. I had to start a *second game with different settings* and
run `path` to find out I had been thirty nodes away. The single most
interesting fact about my run was invisible from inside it.

### Late-game pleasant surprises
* The end-state `risk` screen is the best writing in the game:
  "sack chance: you take 3% of it (softened by angled bastion walls no ram or
  ladder answers, ... a patron with soldiers, the work is in too many places
  to burn, land nobody can carry away)". Seeing a two-century-long list of
  things I built turn a 30% catastrophe into 0% is a genuinely great payoff.
* `academy_network` completing and eminence dropping from 26 (3% chance of
  ruin per year) to 20 in one turn, with the event text
  "Three geographically separated academies changes the society:
  adaptation_rate, literacy_elite, literacy_general, state_capacity, w_novelty"
  — excellent.
* Deputies. "18,686 founder-hours free this year (2,000 of your own, plus 9.3
  deputies directing work in your name at 1,800 hours each)". Watching the
  one-person bottleneck dissolve into an institution is exactly the fantasy the
  intro promises.
* `auto_hire` is transformative and I found it far too late; the `policy`
  screen is buried behind `help automatic`.
