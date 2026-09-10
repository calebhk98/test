# Playtest notes — naive player, session A

(Filling in as I go. TOP PROBLEMS section will be added at the top at the end.)

## Session 1 — first contact

Ran `python3 rome/sim/simulator.py`. Title screen:

```
                      ONE PERSON, AND EVERYTHING THEY KNOW
   You are one person, dropped into a pre-industrial society, carrying the
   knowledge of how modern technology works and none of the industry that makes
   it.
```

Then a menu of 5 settings (Han 100, Rome 100, Viking 900, England 1300, Mexica 1500).
Pleasant surprise: the setting blurbs are genuinely informative and give a hint of the
strategic problem each one poses ("nobody will stop you, and nobody can fund you either").

## Session 1 — Rome, poor_scholar, fog ON, no mortality

Opening is clear and the tutorial line ("the five to start with are 'state', 'available',
'why <name>', 'start <name>', 'step'") is genuinely helpful. `help` is good.

### Confusions / annoyances so far

1. **`stuck` lied to me on turn 1.** With zero projects running it said:
   `nothing: you have work in hand, money to pay for it and people to do it`
   I had no work in hand at all. It should have said "you have started nothing".

2. **`available` is drowned in filler.** 207 startable things, of which 54 are `tx2_*`
   textile nodes all costing 6-30 den, all with `EARNS/YR 0` and `UPKEEP 40`, e.g.
   `tx2_shed  Shed: warp separatio  6  30  0  15%  0  40  1a`. Opening one is a pure
   -40/yr loss. They exist as a wall between me and the ~30 things that actually matter.
   The summary-by-subject view helps, but there is no way to sort by "what earns".
   I had to scrape the output myself with awk to find that `tr_hopper_wagon` returns
   560 den/yr net on a 266 den outlay. A naive player will never find that.

3. **Column headers are ambiguous.** `EARNS/YR` and `UPKEEP` sit next to `RISK` and
   `STAFF`, and `STAFF` prints as `1a`/`1s1a`/`-` with the legend a full screen below.
   Fine once learned; opaque at first.

4. **Things completed that I never started.**
   ```
   COMPLETED 100: Guano
   COMPLETED 100: Amphitheatre with tiered seating
   COMPLETED 100: Barrel vault
   ```
   I started Guano and the Horizontal loom. Amphitheatre and Barrel vault appeared from
   nowhere with no explanation. Nice if it's a freebie, but tell me why.

5. **Pleasant surprise:** the "you know how, but nothing earns until you `open` it"
   rule is called out in `help` *and* in the completion event *and* in `ventures`.
   That is exactly the kind of thing that usually eats an hour of a new player's life.

6. **Pleasant surprise:** `why <id>` is excellent. It gives the historical reasoning
   ("The size of the improvement is disputed in modern scholarship, so claim a real but
   modest gain, not the old textbook figure of four times"), the cost breakdown with
   every multiplier, prerequisites and what rests on it.

7. **Opening a concern silently charges money.** `open ag2_guano` dropped me 58.8 -> 40.9
   and `open tex_horizontal_loom` dropped 40.9 -> 7.1. The printed line only said
   "it earns 100 a year and costs 0 a year to run" — it never mentioned a setup fee.
   I only noticed because my cash nearly hit zero.
