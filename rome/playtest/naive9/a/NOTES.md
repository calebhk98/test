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
