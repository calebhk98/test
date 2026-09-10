# BREAK_B — playtest notes

Target: `/home/user/test/rome/sim/simulator.py`
Scenario requested: Rome, 100 AD; fog of war ON; poor scholar purse; founder does NOT age.
Rule I am following: I only learn things from the running program. No source reading.

## Log

### Step 0 — before I start
Expectation: an interactive setup wizard asks era/place, fog, purse, ageing; then hands me a
session file and a `play --session <file>` invocation. I expect piping lines to work.

### Setup
Answers piped: `2` (Rome), `y` (fog), `poor_scholar`, `n` (no ageing).
Session file: `rome_100ad.json` written into cwd. Resume works exactly as advertised.

Baseline at 100 AD: 400 den, 2000 founder-hr, rep 5, scandal 0, eminence 0,
137 technologies "granted for free", 0 built. Target: point-contact transistor by 600.

**Observation 1 (candidate inconsistency).** `help commands` says:
  "open <id>: start actually running something you have worked out how to do;
   until you do, it earns nothing and costs nothing"
But `money` on turn 0, with nothing started and nothing opened, already shows
  Revenue: 233.5 den/yr  from: med_cataract_couching 166.7, med_trepanation 66.7
Expectation was 0 revenue. Need to check `ventures` to see whether these count as "open".

**Observation 2.** `available` suggests `available afford 1,083` as "what you can pay for"
while capital is 400 and credit limit 1,367. 1083 is neither. To check.

### FINDING 1 (confirmed contradiction) — revenue from ventures that do not exist
Expected: `ventures` and `money` agree about what is earning.
Actual, same session, no commands in between:
```
> ventures
RUNNING
  nothing
YOU KNOW HOW, AND HAVE NOT OPENED
  nothing
Knowing how to do a thing and running it are different. Only what you are
RUNNING earns anything or costs anything.
> money
Capital: 400 den     Revenue: 233.5 den/yr
  from:
    med_cataract_couching        166.7
    med_trepanation              66.7
```
`ventures` says nothing is running and nothing earns; `money` says 233.5 den/yr is coming in
from two named concerns. The screen's own sentence ("Only what you are RUNNING earns
anything") is falsified by the other screen. Confidence this is wrong: HIGH — the two
statements cannot both be true.

### FINDING 2 (candidate) — risk mitigation advice does not match the stated remedy
```
> risk
[165-180] Antonine plague
  probably smallpox or measles
  staff loss: you take 100% of it
    what would help: clean water, quarantine, and eventually inoculation
    you could begin now: horse_collar (709.4 den)
```
The prose remedy is sanitation/quarantine/inoculation; the concrete suggestion is a
**horse collar**. A padded horse collar does nothing about smallpox. Looks like the
"you could begin now" line is picking from a generic list rather than from the hazard's
actual mitigators. Confidence: MEDIUM-HIGH that this is a bug.

Also in the same block: "staff loss: you take 100% of it" immediately followed by
"staff loss after what you have built: 28%" — with nothing built. Two numbers for the
same quantity in adjacent lines.

### FINDING 3 (confirmed contradiction) — how many people do I have?
Four screens, same turn, four different answers:
- prompt line:            `sch 0 art 0`
- `labour`:               "ON YOUR STAFF: nobody ... Total employed: 0"
- `ventures`:             "free to put behind something new: 1 scholars, 1 craftsmen"
- `why horse_collar`:     "STAFF NEEDED: 0 scholars, 1 artisans   (you have 1, 0)"
So ventures claims a spare craftsman that `why` says I do not have, and `why`/`ventures`
claim a scholar that the prompt and `labour` say I do not have. Confidence: HIGH that at
least two of these are inconsistent (the founder is plausibly the "1 scholar", but that
cannot also explain the "1 craftsmen").

### FINDING 4 (confirmed contradiction) — per-venture revenue disagrees with the ledger
`why med_trepanation` -> "REVENUE: 200 den/yr" and "STATUS: DONE / THIS SOCIETY ALREADY
HAS THIS. You did not build it and do not maintain it."
`money` -> "med_trepanation 66.7".
200 vs 66.7 for the same line item, and it is money from something the game explicitly
says I did not build and do not maintain. Confidence: HIGH on the mismatch.

### work
`work scholar 500` -> earned 160.2 (0.3204 den/hr), capital 400 -> 560.2, hours 2000 -> 1500.

### FINDING 5 (mechanic never disclosed) — "revenue" is really the founder's own unspent hours
Revenue tracks remaining founder-hours exactly:
  2000 hr free -> Revenue 233.5   (cataract 166.7 + trepanation 66.7)
  1500 hr free -> Revenue 175.2   (125 + 50)          = 233.5 x 0.75
     0 hr free -> Revenue 0
So the 233.5 den/yr is the founder personally doing surgery, prorated by idle hours.
Nothing in `why`, `ventures`, `money` or `help` says this. `why med_trepanation` states a
flat "REVENUE: 200 den/yr" that is never the number you actually get, and `ventures`
insists nothing is running. Confidence the display is misleading: HIGH.
Also `work scholar 2000` would pay 640.8 den vs 233.5 passive, so the "free" revenue is
strictly the worst use of the same hours - a trap for a player reading `money`.

### FINDING 6 (candidate) — credit limit ignores capital, and falls as you get richer
  capital  400 den, revenue 233.5 -> credit limit 1,367
  capital  560 den, revenue 175.2 -> credit limit 1,338
  capital 1041 den, revenue   0   -> credit limit 1,250
Fit: credit = 1250 + 0.5 x revenue. Capital contributes nothing. Tripling my cash
LOWERED my credit limit. A Roman lender who cares about your surgical income but not at
all about the money in your strongbox is odd. Confidence: MEDIUM (could be deliberate
"lending against income", but the direction of travel is clearly wrong to a player).
Living-and-appearances also *fell* (230 -> 228.9 -> 225.6) as capital rose, which is
backwards for a cost described as "appearances".
