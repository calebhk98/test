# Playtest notes - naive9/a

(Playing blind: no source, no docs. Notes appended as I go.)

## Session 1 - first contact

Title screen: "ONE PERSON, AND EVERYTHING THEY KNOW". Nice premise, clearly written.
Five settings offered (Han 100, Rome 100, Viking 900, England 1300, Mexica 1500).

Immediate annoyance: when I piped an empty line in, it printed
    Which one? [1-5, or q to leave]    -- a number from 1 to 5.
    Which one? [1-5, or q to leave]
i.e. the error message is appended on the SAME line as the prompt, which reads oddly.

## Session 1 - opening moves (Rome, poor_scholar, fog on, no aging)

Goal revealed by `help`: "Build point-contact transistor, before the horizon at 600."
`why point_contact_transistor` is a great screen - it shows the full bill (33,970 den,
25 scholars, 20 artisans, 900 of my hours) and says "this needs 7 other things you have
not heard of yet". Good hook.

Things that worked well / pleasant surprises:
- `available all` gives a table with COST/HOURS/YEARS/RISK/EARNS/UPKEEP/STAFF, which is
  enough to do real ROI arithmetic. That is the best thing in the game so far.
- `money` ledger itemises revenue per concern and literally says "these add up to the
  revenue above" - very trustworthy.
- `risk` listing historical hazards with dates and "what would help" is excellent.
- The game auto-saves after every command and tells you the resume command. Nice.

Confusions / problems:
1. `state` uses the word RUNNING for two different things: "RUNNING (5)" = projects
   under construction, and "RUNNING AS CONCERNS: 1" = things earning money. I read the
   first as "these are earning" for a while. Suggest "BUILDING" vs "RUNNING".
2. `why <id>` does NOT mention that OPENING a finished thing costs money again.
   `why tex_horizontal_loom` said COST 225.8; after it completed, `ventures` showed a
   "TO OPEN 33.9" column I had never been told about. Small, but it is a hidden cost.
3. After my first `step`, I got:
      COMPLETED 100: Amphitheatre with tiered seating
      COMPLETED 100: Barrel vault
      COMPLETED 100: Rigid padded horse collar...
   I never started an amphitheatre or a barrel vault. I assume these are free
   "granted" techs the civ already has, but the log calls them COMPLETED next to the
   thing I actually built, which is misleading.
4. `quote hire artisan 1` -> "REFUSED: no such material: 'hire'. Mineable: coal, ...".
   `help commands` says "quote <what>: what something would cost before you commit to
   it; so far quote mine coal 500". So `quote` is really `quote mine`. The error
   message talks about materials, which is a confusing thing to be told when you asked
   about hiring.
5. Every fresh run writes a NEW session file into the repo root
   (rome_100ad_2.json ... rome_100ad_21.json). Twenty exploratory launches left twenty
   files lying around. It should reuse one, or put them somewhere.
6. The very first prompt, when fed a blank line, renders as
      Which one? [1-5, or q to leave]    -- a number from 1 to 5.
   the complaint is glued to the end of the prompt line.
7. Scandal appeared out of nowhere: after one `step` STANDING went from
   "scandal 0" to "scandal 4.1" with no event line explaining why. Nothing in the
   step output said I had done anything scandalous.

## Session 1 - I went bankrupt because of an automation switch (years 104-112)

I turned on `policy auto_train on` because `help automatic` said it "teach[es] trades
this society does not have when a project needs them". No project of mine needed them.
It nevertheless taught engineers, chemists, machinists and then opticians, and put them
on my payroll permanently at ~650 den/yr each. My wage bill went 217 -> 4,818 den/yr
against a revenue of 4,561, and eight years later:

    EVENT 110: CLOSE TO THE LIMIT: you owe 7,626 of the 9,801 anyone here will advance you
    EVENT 111: CREDIT EXHAUSTED: 2 projects halted, unfinished.
    EVENT 111: INSOLVENCY SETTLED: ... you still owe about 3,358 denarii ... reputation -12

PROBLEMS:
8. `auto train` trained four trades that NO project of mine needed, which directly
   caused an insolvency. Either the description ("when a project needs them") is wrong
   or the trigger is. This is the single most damaging thing that happened to me and I
   had no way to see it coming - nothing warned me that turning that switch on would
   commit me to ~2,600 den/yr of new wages.
9. I set `policy auto_train off` in 109 and an OPTICIAN still appeared on the payroll by
   112. I assume there was training already in flight, but nothing told me that. There
   is a hint `training_pending -> labour` in state's "more:" line, but `labour` never
   printed anything about pending training.
10. Firing was the fix and it is silently very good: after firing them, chemist,
    engineer, machinist and optician moved from "MUST BE TAUGHT" to "YOU COULD HIRE" -
    i.e. teaching a trade once creates it in the whole labour market forever. That is a
    lovely mechanic and the game never says it anywhere. I only found it by accident.
11. `labour` says "HOUSEHOLD PLACES: 0.65 of 6 used" and then, under "to make room:",
    explains only how to HIRE people. It never says what raises the cap of 6. `state`
    says "'labour' says what raises it." It does not. This matters enormously because
    the win condition needs 25 scholars and 20 artisans on staff and I am capped at 6.
12. Every `available ...` query reprints the same ~26-line "HEARD OF, CANNOT BEGIN YET"
    block, even for a one-line query like `available find estate`. It buries the answer.

## Session 1 - the recovery, and what the game actually rewards (115-143)

After firing everyone I was at +3,005 den/yr and recovered fast. Two more observations:

13. When I was under the post-insolvency credit ban, `start patron_local` refused with:
      "REFUSED: nobody here will fund new work ... until then you may finish what is
       running, and pay for something out of money you actually hold."
    I had 9,603 denarii in hand and the project costs 1,200. It still refused. Either
    the message is wrong or the rule is. That sentence promises something the game
    does not allow, and I retried it twice believing I was doing it wrong.
14. `available electricity` returns "Codebook for optical telegraph" and "Signal flags
    for maritime signalling". Neither is electricity. The subject buckets are odd
    (signal flags in electricity, "sizing systems: body measurement" and 50 other
    textile micro-nodes crowding out everything else).
15. The dominant strategy I found is dull and probably not intended: dump `available
    all`, sort by cost, and start EVERY cheap node at once. I started 47 things in one
    year, went from 16 to 63 technologies, and my reputation tripled. The engine has no
    penalty for breadth, so "buy the whole bottom shelf" beats any thoughtful plan.
    A player who plans carefully is punished relative to one who spams.
16. Failure messages are good but very frequent and identical:
      "FAILED at Green manure: it did not work. 40% of the hours are to do again
       (20 of your own) and 84 is gone. Attempt 2."
    In one 4-year step I got nine of these. "it did not work" never says anything about
    WHY, so nine failures teach me nothing and just tax me.

## Session 2 - I restarted with fog OFF, and it is a different (much better) game

With fog off, `path point_contact_transistor` prints the whole 142-node road in
topological order, and `why <id>` gains three lines that are worth more than everything
else in the interface put together:

    FULL CHAIN BEHIND IT: 145 nodes, 55,420 of your hours, 9,421,124 den, 142.2-year serial floor
    DIRECTLY UNLOCKS: case_hardening, charcoal_industrial, collegium_licensed, ...
    TOTAL DOWNSTREAM: 2,008 thing(s) depend on this -- INCLUDING THE GOAL

17. THE BIG ONE. Fog of war is the DEFAULT ("Fog of war? [Y/n]") and it removes the
    only tools that make the game strategic. Under fog you get 218 startable things,
    a four-value hint column (ALL / much / some / few / ?), and no way to tell which of
    them is on the road. I played 43 in-game years under fog and never learned that
    `workshop_first` exists, let alone that 2,008 things and the goal depend on it -
    because it was BLOCKED, and fog hides blocked nodes' descriptions. The default
    setting is the one where the interesting decisions are invisible.
18. Related and worse: the answer to "how do I ever get 25 scholars and 20 artisans on
    staff when my household cap is 6" is hidden in the prose of three blocked nodes:
      freedman_staff: "Grants +8 artisans."
      school_founded: "Grants +4 scholars and +2 scholars/yr thereafter."
    Under fog I could not read either of those, and `labour` - which `state` explicitly
    points at for this - does not mention them. A fog-on player cannot find the single
    mechanic that makes the goal reachable except by accident.
19. The real opening is patron_local -> workshop_first -> citizenship -> collegium_licensed
    -> freedman_staff -> school_founded, and nothing in the fog-on game says so. Under
    fog, patron_local is the only one of those six that is even visible on turn one.

## Session 1 continued - the economy is not a constraint at all

I let the "start everything cheap that is available, then step 4 years" loop run under
fog of war. Results:

    year 143   capital    106,994 den
    year 160   capital  1,308,609 den
    year 168   capital  2,292,003 den

20. The economy breaks completely. `why point_contact_transistor` says the whole
    remaining chain costs 9,421,124 den; a strategy with no thought in it whatsoever
    generates 2.3 million by year 168 of a 500-year game, i.e. it will pay the entire
    bill several times over with four centuries to spare. The only real limits are my
    2,000 founder-hours a year, the calendar floors and the staff caps. Once I realised
    that, every money-flavoured mechanic in the game (bounties, mines, debt, `work`,
    market saturation, "an idle million bleeds fifteen thousand a year") stopped
    mattering, and those are some of the nicest-written parts of the game.
21. The lever that makes this work is that opening N concerns has no diminishing return
    worth speaking of. "what the market will not absorb -22.5" was the only pushback I
    ever saw, on a revenue of 4,561. If breadth is meant to be self-limiting, it is not.

## Good error handling (a genuine pleasure)

    why transistor
    REFUSED: unknown node 'transistor'. did you mean: junction_transistor,
    point_contact_transistor, tl_radiator, tr_pantograph, tl_tractor

    step abc
    step takes a number of years, e.g. 'step 5', or nothing at all for one. 'abc' is not a number.

    withdraw
    REFUSED: nobody is watching you closely enough for this to buy anything: prominence
    is 0.0 against a danger line of 26. ... Nothing was changed.

Every refusal I hit told me why and what to do instead, and `withdraw` refusing to let
me hurt myself pointlessly is a really nice touch. `work scholar 500` explaining that
the wage cost me 58.4 of my own practice, "so you are up: 101.8", is exactly the kind
of honesty the rest of the game promises.

## More problems found while grinding

22. `start <id>` will happily start a project that literally nobody in the world can
    work on. I started tl_windscreen_wiper (needs a machinist; no machinist exists in
    Rome) and the game took the order without comment. Four years later:
      EVENT 147: HALTED tl_windscreen_wiper: there is nobody here who can do this work
      (machinist). What you spent is lost
    The warning is excellent - but it arrives at `step` time, after the money is
    committed. `available` marks it with a "1a*" star, but `start` itself never
    mentions it, and `why` says "STATUS: CAN START NOW".
23. Related: this line appears with no year and no EVENT prefix, breaking the pattern
    of every other message in the step log:
      "warning: no one can do this work YET: engineer. The trade exists here or is
       being taught, ..."
24. Nice: hazards are properly costed and counterfactual'd -
      "EVENT 170: Antonine plague: staff -7%, 129,835 gone with the trade that stopped
       (would have been -28%: knowing what is actually killing them; variolation and
       then vaccination; hard soap, in quantity; ...)"
    Telling me what the number WOULD have been without my mitigations is the single
    best feedback line in the game.
25. Also nice: "EVENT 150: your patron dies; his heir must be courted afresh. The
    courting cost 800 denarii, your protection falls from 57% to 34%, and you are
    talked about (scandal +4)."

## Session 3 - the automation switches are a run-ending trap (second time)

I started a fresh fog-off run and turned on every policy switch, exactly as `help
automatic` invites you to ("Some things the engine will do for you if you let it ...
Every one is a switch you control"). The run never recovered:

    r00 yr104 cap-2398   * EVENT 103: CLOSE TO THE LIMIT: you owe 2,398 of the 2,421 anyone will advance you (99%)
    r01 yr108 cap-1074   * EVENT 104: INSOLVENCY SETTLED ... reputation -8.9
    r03 ...              * EVENT 114: INSOLVENCY SETTLED
    r07 ...              * EVENT 131: INSOLVENCY SETTLED
    r10 ...              * EVENT 141: INSOLVENCY SETTLED
    r14 ...              * EVENT 157: CREDIT EXHAUSTED: 3 projects halted, unfinished
    r24 ...              * EVENT 197: INSOLVENCY SETTLED
    r36 yr248            * EVENT 244: INSOLVENCY SETTLED ... reputation -12.0
    ... year 292, 132 of 142 goal nodes still remaining, reputation 0.

26. Turning the policies on with a poor purse puts you into a 200-year insolvency loop
    that the game never diagnoses. Every ~12 years it prints "INSOLVENCY SETTLED: most
    of the debt is written off" and carries on. Nothing ever says "your wage bill is
    the problem" or "auto_hire and auto_train are what is spending your money", and
    `money` shows wages as one undifferentiated line. Between the two runs where I used
    them, the automation switches cost me two entire playthroughs.
27. Repeated insolvency has almost no teeth: the debt is written off, I keep the
    knowledge and the practice, and I only lose some reputation. So the "loop" is
    survivable but sterile - 200 years passed and I built nothing. A run that is dead
    but not over is worse than one that ends.
28. During the plague I saw the SAME line three times in one step block:
      EVENT 165: Antonine plague: staff -28%
      HAPPENING NOW: Antonine plague
      HAPPENING NOW: Antonine plague
    and later "EVENT 170 ... staff -28%, 20 gone with the trade that stopped" while I
    employed 0.13 people. Losing 28% of nobody four separate times reads like a bug.

## Session 4 - a run that actually worked, and where it jammed

Doing it by hand (auto_open + auto_shed + auto_bribe ONLY, economy first, then the
institution chain) went completely differently:

    year 116  6,296 den      year 144    181,910 den    year 200  1,429,716 den
    year 128  33,465 den     year 160    595,208 den    year 340  3,479,256 den
    household places 6 -> 18 (freedman_staff) -> 33 (school_founded)

So the game is winnable-shaped and the institution chain is exactly as advertised: it
is the pivot. But then I jammed for 250 in-game years, and here is why:

29. I sat at "100 of 142 goal nodes remaining" from year 172 to year 436 with three and
    a half million denarii in the bank and nothing I could start. The cause was one
    line I only found by typing `why precision_three_plate` on a hunch:
      "this needs machinists and there are none in this society. Teach one:
       train machinist 2 (about 450 of your own hours each, two years)"
    That message is perfect. The problem is that NOTHING SURFACES IT. `state` never
    said "you are blocked on a trade". `available` just quietly stopped listing the
    node. `path` listed precision_three_plate as remaining with no annotation. There is
    no "what is blocking me" command, and with 306 things startable and 1,600 nodes
    downstream of the one that mattered, I had no way to notice.
30. Training is the most expensive thing in the game in the only currency that is
    actually scarce - founder hours. `train machinist 4` ate 1,800 of my 2,000 hours
    for the year, and there are five trades to teach (chemist, electrician, engineer,
    machinist, optician). That is several years of doing nothing else. Nothing warns
    you before you type it; `train machinist 4` just silently consumed the year, and my
    following four `train` commands in the same turn did nothing.
31. And training quietly wrecked my economy: right after it,
      EVENT 436: nobody left to keep an eye on 2 concerns, so crop_rotation,
      med_bone_setting closed.
      EVENT 437: ... 3 concerns ... EVENT 438: ... 4 concerns ...
    Teaching a trade evidently converts staff I already had, so a dozen running
    businesses shut down as a side effect of a `train` command. Nothing said it would.
32. BUG (or very misleading): `why point_contact_transistor` prints the same
      "FULL CHAIN BEHIND IT: 145 nodes, 55,420 of your hours, 9,421,124 den,
       142.2-year serial floor"
    in year 436 after I had built 227 technologies and 42 of the goal's prerequisites
    as it printed in year 100 with nothing built. It never counts down. Since that is
    the number you would use to decide whether you can still make the horizon, a static
    figure labelled "FULL CHAIN BEHIND IT" is actively misleading - at year 439 it told
    me I needed 142 more years of serial floor with 161 years left, which is not true.

## Session 4 - the ending (I lost)

    ended in 600 AD
    you built 299 things; this society already had 141
    91,934 in hand, 0 people, reputation 33.9, 12 concerns running

    THE ROAD TO POINT_CONTACT_TRANSISTOR
      146 nodes in all; you had 52 of them and 94 were still to build
      the next steps would have been: charcoal_industrial, nitre_beds,
      precision_three_plate, bellows_water_blown, galena_detector, ...
    the largest things you built: blast_furnace, mat_copper, lead_metallurgy, ...

The end screen is genuinely good - it tells you the score, the shape of the failure and
what the next moves would have been. Two more things it exposed:

33. My goal count went BACKWARDS during the run: 66 remaining in year 487, 80 in year
    541, 94 at the end. Hazards were destroying technologies I had already built
    ("AHEAD: 68 technologies at risk if a hazard lands, hedged by nothing yet"). That is
    a fine mechanic, but the only notice is that a number in `state` moves. A run can be
    quietly losing ground for a century and the only tell is a counter.
34. My staff decayed from 28 people to ZERO over 150 years purely through the 3.5%/yr
    attrition, because I stopped hiring. Household places also fell from 33 to 16.6
    (institutions destroyed, presumably). Nothing ever raised an alarm: no "you have no
    staff and 12 concerns", no "your school is gone". By the end I had 91,934 denarii
    and literally nobody, and had been in that state for decades.
35. Very good: `step 6` two years from the horizon was refused with
      "REFUSED: there are only 2 years left before the horizon at 600. Ask for 2 or
       fewer, or fewer still if you want to see what happens on the way."
    and after the end, `step` says "the run has ended ...; time cannot advance. Use
    state to see the final position." Both perfect.

## Session 5 - informed attempt (fog off, rich_merchant, everything I had learned)

Opening: institutions first (patron_local -> workshop_first -> citizenship ->
collegium_licensed -> freedman_staff -> school_founded), keep the household full every
single turn, teach one trade a round as soon as I could afford it, hedge with
corpus_written/corpus_dispersed, and only then chase the goal chain.

    year 184   48,317 den   7 people    household cap 20    130 goal nodes left
    year 204  514,755 den  36 people    household cap 87    104 left
    year 224 2,671,306 den  45 people   household cap 111    78 left
    year 264   617,125 den  30 people   household cap 107    80 left   <- going backwards
    year 316 5,446,600 den  49 people   household cap 123    82 left   <- flat for 90 years

36. This is the shape of the whole game once you know what you are doing: a fast,
    satisfying 120 years, and then a wall. From year 224 to 316 I started ~30 projects
    per round, had five and a half million denarii, 49 staff and 123 household places,
    and the goal counter did not move. The binding constraint is my own 2,000 hours a
    year - the chain needs 55,420 of them - and nothing in the interface makes that
    legible. `state` says "2,000 founder-hours free this year" and never says "you have
    committed 40,000 hours of work to projects in hand". There is no queue view, no
    "your hours are the bottleneck", no way to see which of my 30 running projects is
    actually getting my time.
37. There is no way I could find to buy more founder-hours, which is thematically right
    but means that after about year 250 money is completely inert. I ended sessions
    with 3-5 million denarii and nothing whatsoever to spend it on. `bounty <id>` (pay
    someone else to solve it) is the obvious answer and it is one line in `help
    commands` with no worked example anywhere; I never found a case where the game
    offered it to me at the moment I needed it.

## The wall, found at last (year 460, 7.4 million denarii, 82 nodes to go)

For 160 in-game years my goal counter did not move while I started ~30 projects a round.
The whole thing came down to one node, `precision_three_plate` (TOTAL DOWNSTREAM: 1,629
things INCLUDING THE GOAL), and to find out why I had to type `why` at it on a hunch:

    why precision_three_plate  ->  STATUS: CAN START NOW
    available find precision   ->  listed as startable
    start precision_three_plate ->
        "but: started, but this society cannot supply the labour it wants and it will
         crawl until you can: machinist (wants 1500 hours a year; this society can
         field 0 at most)"

38. `why` and `available` both say a node is startable when the game already knows it
    cannot progress at all. The truth is only told by `start`, i.e. after you have
    committed the money. `why` prints "STAFF NEEDED: 0 scholars, 3 artisans (you have
    1, 45.1)" and says nothing at all about the HIRED LABOUR line (machinist 3,000h)
    that is the actual blocker. Please put the labour-supply check into `why`.
39. And the reason there were no machinists is the thing that should be on the front
    page of this game:

        hire machinist 10
        REFUSED: this society's literacy will not supply more than 5.9 machinists in
        total, ever, at any price.

    There is a hard, society-wide ceiling on how many scholars/machinists/chemists/
    engineers can ever exist, it is set by "literacy", and the GOAL REQUIRES 25
    SCHOLARS on staff against a ceiling of 6.4. So the win condition is gated on
    raising literacy - and literacy appears NOWHERE. It is not in `state`, not in
    `state full`, not in `labour`, not in `help`. I found the number by accident, in a
    refusal message, in year 463 of a 500-year game.
40. Meanwhile `labour` was telling me "MUST BE TAUGHT: none" and listing machinist
    under "YOU COULD HIRE", while `labour machinist` said "the town can supply: 0
    hours". Those two screens contradict each other.
41. Lovely undocumented mechanic I only saw at year 460:
      "You: 6,128 founder-hours free this year (2,000 of your own, plus 2.3 deputies
       directing work in your name at 1,800 hours each)"
    Deputies triple the one resource that is genuinely scarce. Nothing in `help`,
    `labour` or `state` ever mentions that deputies exist or how you get them. This is
    the single most important thing in the late game and it is a surprise.
42. Stale contradiction: right after I hired 5 machinists, the same `state` block said
      precision_three_plate  ... waiting on your hours
      !! ABANDONED IN 1 YEAR unless you can find a machinist
    The project was no longer blocked; the warning had not caught up.

## Best result so far, and what unlocked it

Continuing the same save with one change - HIRE EVERY TRADE, EVERY YEAR, UP TO THE
LITERACY CEILING - moved the goal counter from 82 remaining to 41 in 90 years, with
staff going from 45 to 155 people:

    year 467  76 left   88 people
    year 483  56 left  118 people
    year 503  50 left  141 people
    year 551  41 left  142 people
    ended in 600 AD - you had 105 of 146 nodes; 41 still to build

So the "correct play" turns out to be: hire everything you are allowed to hire, every
single year, forever. Nothing in the game suggests that, and the reason it matters is
invisible (attrition eats 3.5%/yr and the literacy ceiling caps you low).

43. Cosmetic but it bit me: the NAME column in `available` is truncated mid-word and
    mid-parenthesis - "Rigid padded horse c", "Purity 99% (careful", "Codebook for
    optical", "Averages, error, sam". With 774 rows in `available all` and no way to
    widen the column, the list is genuinely hard to read.
