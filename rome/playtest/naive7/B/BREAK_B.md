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

### Note: the program became unrunnable mid-session (not caused by me)
At 103 AD, after `available all`, every invocation began dying at import time:
```
Traceback (most recent call last):
  File "/home/user/test/rome/sim/simulator.py", line 46, in <module>
    from engine.protocol import (_agent_available, _agent_dispatch,  # noqa: F401
ImportError: cannot import name 'load_state' from 'engine.protocol'
```
I have modified nothing in the repository; this appeared between two consecutive runs of
the same command line, so the tree is being edited underneath me. Waiting and retrying.

### FINDING 7 (confirmed) — "waiting on your hours" when my hours are not the constraint
`start tr_hopper_wagon` (needs 50 founder hours, calendar floor 1 year), then `step 1`:
```
RUNNING (1):
  tr_hopper_wagon   60% of your hours spent, 0 still owed - waiting on your hours
You: alive (you do not age), 2,000 founder-hours free this year
```
It claims to be waiting on my hours while 2,000 of my hours sit unspent and it needs 20
more. It was actually waiting on the one-year calendar floor - it finished the next step.
A status line whose stated reason is not the real reason. Confidence: HIGH.

### FINDING 8 (confirmed) — staff requirements are advertised and then not enforced
`why tr_hopper_wagon` -> "STAFF NEEDED: 0 scholars, 1 artisans   (you have 1, 0)" and in
the same breath "STATUS: CAN START NOW". `labour` says "Total employed: 0 ... nobody".
I started and completed it with zero artisans on the staff. `help labour` insists
"Trades are NOT interchangeable: a project asking for an engineer cannot be built by
smiths however many you have" - but a project asking for an artisan can apparently be
built by nobody at all. Confidence: HIGH that STAFF NEEDED is cosmetic here.

### FINDING 9 (candidate) — the founder's hour has two prices, 24x apart
`work scholar` pays the founder 0.3204 den/hr (80% of the 0.40 den/hr market scholar wage).
`bounty tr_hopper_wagon` costs "about 649" against a build cost of 266.1 - i.e. 383 den to
avoid spending 50 founder hours, or 7.66 den/founder-hour. The same hour is worth 0.32 den
when you sell it and 7.66 den when you buy your way out of it. Confidence: MEDIUM
(defensible as scarcity pricing, but nothing in the game says so).

### Guarded successfully (could NOT break)
- `work scholar -1000` / `hire scholar -3` / `buy slaves -5` / `bribe -1000` /
  `commission smith -400` / `step -5` / `step 0`: all REFUSED with a clear reason.
- `work scholar 99999` refused ("you have 1500 of your own hours left this year").
- `work chemist 100` refused because the trade does not exist here - correct and consistent
  with `labour`.
- `work nonexistent 100` refused with the list of real trades.
- Fog of war held: `path point_contact_transistor`, `why point_contact_transistor` and
  `available find transistor` all reveal nothing ("you have never heard of any such thing").
- `fire scholar 5` with 1 employed succeeded silently rather than refusing (cosmetic).

### FINDING 10 (confirmed, serious) — `load` validates the filename and nothing else
`save backup1.json`, then edit that file by hand (`capital` -> 1e12, `_fog` -> false),
then in the running game:
```
> load cheat.json
loaded: cheat.json
year: 107
[107 AD | 1000000000000 den | ...] > help fog
  fog of war: OFF. You can see the whole tree.
> path arithmetic_positional
id: arithmetic_positional ...
```
The `state` header even flips from "Fog of war is on: you see the next step, never the
road." to "Goal: point_contact_transistor", and `path` - which had been refusing with
"not available under fog of war" - starts answering.
Notable because the path checks ARE careful: `load /nonexistent/x.json` is refused with
"a save file must be a relative path", `load BREAK_B.md` with "a save file should end in
.json or .save". So the filename is validated and the contents are not at all.
Confidence: HIGH that this is unintended for the fog switch specifically - fog is chosen
once at setup and `help fog` says "there is no way to view the whole tree".
(I restored `backup1.json` afterwards and kept playing with fog ON. The 1e12 experiment
also revealed that living-and-appearances is ~1.5% of capital plus a base:
capital 1e12 -> "living and appearances 15,000,000,270".)
