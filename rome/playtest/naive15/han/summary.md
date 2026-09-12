# Final summary - Han China playtest (naive15)

## How far I got
Played from year 100 AD to year 144 AD (44 of 500 available years, against the transistor goal's own 142-year theoretical floor) as the Later Han Empire, fog of war on, mortality off, default "poor_scholar" start (300 cash after Han's 0.75x price multiplier), aiming at the default goal (Grown and alloy junction transistors, closure 168, floor 142 years). Ended with:
- 14 technologies built by me personally, 148 known in total (134 were free starting knowledge)
- 21 of the goal's nodes reached
- 239 cash, +17.4 cash/yr recurring, reputation 8.9, scandal 0.16 (safe), eminence 0.10 (safe)
- No staff currently employed (fired everyone to control costs); no active project
- No civilisation-ending event landed; one historical hazard window ("The regency cycle and the Partisan Prohibitions") is live and several more are queued on a real historical timeline

I stopped deliberately at a stable, debt-free point rather than running out the clock or hitting a wall - the game was still fully playable and I could have continued. Given the goal's ~142-year floor and this being turn-by-turn interactive play (not a script), I judged this was enough ground to report on faithfully without turning the session into pure grinding.

## What stopped me
Nothing broke or dead-ended the run. What "stopped" me was practical: the game is enormous (a 168-node prerequisite tree for the default goal, a 500-year default horizon, and a promise in its own menu text that "a real run takes substantially longer than its floor"). Having demonstrated and documented the core loop, the economy/debt mechanics, the staffing/training mechanics, and the historical risk system in depth - including finding real rough edges - continuing for hundreds more turns would mostly repeat the same loop (start something, work idle hours, step, repeat) without teaching me anything new to report.

## What I would tell the people who made it

**The good:**
- The historical risk system ('risk') is genuinely excellent - real, dated, well-researched events specific to this civilisation and era, each explained in terms of both what happened and why it concretely threatens the player's position, with a live "what would help" and "you could begin now" tied to actual buildable techs. This is the single best piece of design I found.
- The core "why/available/start/step" loop is legible once you find it, and 'why' in particular is very complete (cost breakdown, risk, staff needed now vs. to keep it open, what rests on it).
- Failure is handled honestly and non-catastrophically: a failed research attempt costs money/hours and reduces future risk rather than ending the run, and the game tells you this upfront in 'why' before you commit.
- The unprompted "you have been in arrears N years, here is exactly how to dig out" warning block is good, proactive design that should probably fire earlier than 8 years in.
- 'quote', 'score', and the credit-forecast shown by 'start' are all honest, well-written previews of consequences before or after commitment.

**The rough edges, roughly in order of how much they cost me:**
1. Nothing anywhere warns you about your TOTAL cash exposure across everything you have committed to in a turn/session - only per-item forecasts. Stacking several individually-reasonable-looking starts (each flagged "almost everything rests on this") is the single easiest way to blow a 12%-interest debt spiral, and the game lets you do it freely. A simple "you are about to commit to X cash across N things, you have Y on hand and Z in credit" confirmation would have saved me two separate debt spirals.
2. A hired specialist's ongoing necessity is not fully visible: 'why'/'state' show only the SINGLE current bottleneck ("waiting on: money"), not the whole live set of things a project still depends on. I safely fired an engineer whose hour-requirement showed 0% owed, only to have the project immediately declare "cannot go on: no engineer here" again. This reads as a bug or at least a real information gap, not clearly signposted anywhere.
3. Staff can vanish to random annual attrition ("death and to better offers") - a real, deliberate mechanic, confirmed once by a clear log line - but the very first time it happened to me (a scholar, one step after hiring, still 100% idle), there was NO log entry, no message during 'step', nothing. I only found out by checking 'labour' on a hunch. If attrition is meant to be visible, it should always be logged; if it's meant to sometimes be silent, that should be stated somewhere (I looked in 'help labour' and found nothing).
4. A completed project can sit at "100% of hours spent, 0 still owed" while its status line still reads "waiting on: your hours" for several turns running, when it's actually just waiting on its own calendar floor (the correct phrase, used elsewhere, is "waiting on the calendar"). Minor, but it cost me repeated re-checks looking for a hidden requirement that didn't exist.
5. The numbers don't always reconcile in an obvious way turn to turn - several times my cash balance moved by noticeably more or less than the "net X cash/yr" figure printed that same turn, with no breakdown covering the gap (I didn't chase this into the code, per the ground rules, but flagging that a careful player will notice and be unsettled by it).

**What I wanted to do and couldn't work out:** get a second scholar or a craftsman to persist reliably alongside an active research project without either (a) starving myself of cash via their wage, or (b) losing them to random attrition right when a project depended on them. I never found a clean way to grow past "one person doing everything," which given the scale of the tree (needs 2-3 staff of various trades for many nodes) seems like it should be a earlier, more central mechanic than it currently feels - a school (school_founded) is gated behind prerequisites I never got to see under fog.

**Biggest single surprise, good:** the history system.
**Biggest single surprise, bad:** how easy it is to accidentally deep-dive into 12%-interest debt from combining a few individually-reasonable decisions, with no aggregate warning.

## Notes on this write-up
Detailed, timestamped, turn-by-turn notes (including the dead ends, exact commands, and exact numbers) are in `notes.md` in this same directory. This summary is the condensed version.

Two things I was curious about but deliberately did not look at, per the ground rules of this playtest: the exact mechanism behind the mismatched cash deltas (item 5 above), and why the first staff-attrition event was silent while the second was logged. Both are recorded above as open questions rather than resolved.
