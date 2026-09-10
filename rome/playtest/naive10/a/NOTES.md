# Playtest notes — naive player, session A

(TOP PROBLEMS section will be added at the top at the end.)

## Log

### Session A, Rome 100 AD, fog on, poor_scholar, no mortality

- Opening menus are excellent: the five civilisations, the starting-wealth menu and the
  mortality toggle are all clearly explained and the prose is genuinely good. Pleasant surprise.
- Goal is only revealed by typing `help`: "Build point-contact transistor, before the horizon
  at 600." The opening text never says it. `state` shows "Aiming at: Point-contact transistor"
  but doesn't say by when. I only learned the 600 deadline from `help` and later from the
  `YEAR 100 (500 years to the horizon at 600)` banner. It should be in the intro.
- CRASH: one invocation died before the banner with
      File "/home/user/test/rome/sim/engine/core.py", line 1236
        self._resync_pools()
    IndentationError: unexpected indent
  Re-running the identical command worked. (Possibly someone editing the tree under me, but
  from a player's seat it looked like the game randomly refused to start.)
- Session files are dumped into the *repository root* as rome_100ad_NN.json (mine was #81 —
  there were already 80). Very messy: a game should put saves somewhere of its own.
- `state` header says `sch 0 art 0` but `why identity_cover` says "STAFF NEEDED: 0 scholars,
  0 artisans (you have 1, 0)". Two different counts of the same thing on adjacent screens;
  turns out the founder counts as a scholar in one place and not the other. Confusing.
- Stepping year 1 printed "COMPLETED 100: Amphitheatre with tiered seating" and "COMPLETED 100:
  Barrel vault" — things I never started. I assume these are free grants, but they are listed
  identically to my own completions, so for a moment I thought the game had started projects
  for me.
- BIG TRAP: finishing a project earns you nothing. You must also `open` it. The game does warn
  ("You know how; nothing is earning yet - 'open X' to run it"), but nothing in the intro or in
  `help` (the "four to start with") mentions `open`, and I ran three years at a loss and
  1,600 den into debt before I noticed. `policy auto_open` exists and is OFF by default; that
  default seems designed to punish a first-time player.
- Possible bug: I issued a batch of seven `open` commands after two `policy` commands. The
  first four (`tr_hopper_wagon`, `tex_horizontal_loom`, `fud_fish_curing_and_smoking`,
  `tex_indigo`) silently did nothing — no error line at all — while the last three worked.
  Re-issuing the same four commands afterwards worked fine. I never saw any explanation.
- Nice: `money` itemises revenue per concern and the rows really do add up. `ventures` telling
  me "those shut concerns would clear 1,713 den/yr between them" is a great nudge.
- Nice: "HEARD OF, CANNOT BEGIN YET" under fog, with the specific reason per item
  ("needs 2 trained scholars, you have 1.0 (you are one of them)"), is the best part of the UI.

### 125-165 AD: the economy works, but the automation is a trap

- `policy auto_hire on` was a disaster. It filled my 22 household places with SCHOLARS at
  625 den/yr each and let my ARTISANS fall to 0.03. Artisans are what supervise concerns, so
  22 of my concerns shut themselves down and my net income went from +8,010/yr to -3,027/yr
  over six years. The policy help says only "grow the staff toward what you can house and
  pay" — it never says it will preferentially hire the trade you least need, or that it will
  starve the supervision your existing income depends on. I would expect auto_hire to at
  minimum keep the staff that keeps the lights on.
- `train engineer 2` issued in the same breath as three `start` commands did nothing at all,
  silently — no error, no message. Issued on its own a few minutes later it worked. Same
  class of silent no-op as the `open` problem above. Any command that cannot be carried out
  should say so.
- The supervision rule ("Most concerns want CRAFTSMEN to keep an eye on them") is the single
  most important mechanic in the game and it is only mentioned in a note at the top of
  `ventures`. Nothing in `help`, `help labour` or `help economy` mentions it.
- I still do not understand what `open` does for a 0-revenue "work". `ventures` lists
  patron_local, workshop_first, identity_cover, school_founded etc. under "YOU KNOW HOW, AND
  HAVE NOT OPENED" with EARNS/YR 0 and COSTS/YR 200-2,500. When they closed for lack of
  supervisors, my protection stayed at 92% and my household places stayed at 48.8. So as far
  as I can tell, opening them costs money and does nothing. If that is wrong the game never
  told me; if it is right, they should not be listed as concerns at all.
- Pleasant: the failure messages are specific and fair — "FAILED at Zinc metal by downward
  distillation: 40% of the hours are to do again (280 of your own) and 25,678 is gone.
  Attempt 2." I never felt cheated by a failure.
- Pleasant: "waiting on the pace it can absorb money: at most 470 a year goes into this...
  Money in hand cannot buy it down faster" is a lovely, legible constraint.
- Annoying: `available <anything>` always appends the same 25-line "HEARD OF, CANNOT BEGIN
  YET" block, even for `available electricity` where the list is mostly farm machinery, and
  even when the search matched nothing. Every query costs a screenful of noise.
