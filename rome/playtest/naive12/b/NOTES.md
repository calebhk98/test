# Playtest notes — naive12/b

Adversarial playtest of `python3 rome/sim/simulator.py play --session ...`, Roman Empire
100 AD, poor_scholar kit, fog OFF, immortal founder. Transcript in `transcript.txt` in
this directory. Findings are numbered as discovered; final reply orders them by severity.

---

## Finding 1: hired staff vanish from the payroll with zero explanation, ever — no `EVENT` line, no `log` entry, nothing

**Repro** (fresh session, `absurd` kit so money is never the constraint):

```
cd rome
rm -f /tmp/staff.json
python3 sim/simulator.py play --session /tmp/staff.json --civ rome_100ad --kit absurd
hire scholar 5
step 1
step 1
step 1
step 1
step 1
state
log
```

Watch `EMPLOY:` in `state` each year: it goes **5 people (100 AD) -> 4 (101) -> 3 (102) -> 3
(103) -> 3 (104) -> 2 (105)**. Money never runs remotely short (capital stays above
900,000 den throughout; wages are ~1,250-3,925 den/yr against 15,000+ den/yr of other
outflow that is itself easily paid), no policy that could shed staff is enabled (`policy`
shows `auto_shed off`, `auto_hire off`, everything off except `auto_mothball ON`, which is
documented as "stop working mines you cannot pay for" and has nothing to do with people),
and `RUNNING AS CONCERNS: 0` the whole time, so nothing is being mothballed for lack of
staff either. Not one `EVENT ...` line prints during any of the `step`s that lose a
scholar, and `log` (checked both immediately, in the same process, and after a reload)
shows only the original `100 AD 5 scholars taken on for 3,125 denarii` line — the four
departures are entirely unrecorded, live or in history.

**Isolated retest, smaller numbers, two more independent sessions** (`hire scholar 2` and
`hire smith 2`, both `absurd`/`rome_100ad`, both starting 100 AD): both lose their first
hire at **exactly year 105**, again silently. A control with `hire scholar 1` (one hire,
otherwise identical) stays at 1 for at least 5 years straight with no loss — so the effect
scales with headcount (5 hires start shedding immediately; 2 hires take until year 105;
1 hire is stable), which rules out a fixed-probability "an employee quietly retires" roll
and points to some sustainability/market-size check silently trimming the roster back — but
the game never says so anywhere a player can read it, in the turn it happens or afterward.

**What should happen vs what happens:** `help log` promises the log records "staff hired or
let go" and `help stuck` positions `log`/`state` as the tools that explain why you are not
getting on. A player who hires 5 scholars, checks back later, and finds 2 has no way to
learn what happened to the other 3 — not this turn, not by scrolling `log`, not ever. Since
`state`'s STAFF NEEDED check against `sch`/`art` gates whether a project can even `start`,
this silently invalidates a plan built around a headcount the game itself reported as
correct a few turns earlier.

**Severity:** this is worse than Finding 1 below because it is not merely losing a
convenience record — it is the game changing load-bearing simulation state (payroll, and
therefore what you can staff and start) with no observable cause, in a way indistinguishable
from a silent bug versus a deliberate mechanic, because nothing anywhere documents which it
is.

---

## Finding 2: fog of war leaks exact hidden node IDs through the "did you mean" typo-correction

**Repro** (fresh fog-ON session):

```
cd rome
rm -f /tmp/fog.json
python3 sim/simulator.py play --session /tmp/fog.json --civ rome_100ad --kit poor_scholar --fog
why bronze_castin
```

Output:
```
REFUSED: you have never heard of any such thing. ... Did you mean: med_bone_setting,
hom_mirror_bronze_polished, mat_bronze
```

None of `med_bone_setting`, `hom_mirror_bronze_polished`, or `mat_bronze` have been built,
started, or mentioned anywhere in this fog-on session — `why mat_bronze` on its own gets the
correct fog refusal with no suggestions, confirming the game agrees it is not something this
save has "heard of" yet. The same leak fires through `start` as well as `why`
(`start bronze_castin` -> `Did you mean: med_bone_setting, hom_mirror_bronze_polished,
mat_bronze`), and through a nonsense near-miss too: `why zone_refin` (a real, deep-tree
semiconductor node correctly hidden on its own) returns `Did you mean: tr_reefing` — a
transport-domain id with no relation to zone refining, again never heard of. `available find`
is the one command that gets this right: `available find bronze_castin` correctly answers
"nothing matching" with no id-shaped hint.

**What should happen vs what happens:** the game's own fog design is deliberate and, in
every other command tested (`start`, `path`, plain `why` misses with no near neighbour,
`available`), scrupulously refuses to name anything not yet revealed — `help fog` and the
in-game refusal text both say so explicitly ("nothing tells you what lies beyond that").
The typo-correction path is wired to the full 3,001-node id list regardless of fog state, so
a player can map out real node ids (and, from the id's domain prefix, their category —
`met_`, `mat_`, `hom_`, `mil_`, etc.) simply by guessing plausible technology names and
making small typos, with no need to ever actually reach them in the tree. This is exactly
the sort of shape-of-the-tree information fog is supposed to withhold (see `naive11`'s
notes on the same design goal), leaking it through an error-message code path nobody
threat-modelled as a disclosure channel.

**Severity:** does not corrupt money, staff, or tech state, but it is a clean, repeatable
breach of the one thing fog of war exists to guarantee, reachable from the very first turn
with nothing but a keyboard.

---

## Finding 3: `log`/history is never saved — it silently vanishes on every reload

**Repro** (two separate process invocations against the same `--session` file):

```
cd rome
python3 sim/simulator.py play --session /home/user/test/rome/playtest/naive12/b/save.json --civ rome_100ad --kit poor_scholar
# in-session:
start hom_eraser_breadcrumb
step 1
log
```
This prints `HISTORY: 4` with four entries (`started`, `interest on arrears`, `completed`,
`fire in the insula district`). The process then exits and prints:
```
Saved to .../save.json. Come back with:
   python3 rome/sim/simulator.py play --session .../save.json
```
Now resume in a **new** process and immediately run `log`:
```
python3 sim/simulator.py play --session /home/user/test/rome/playtest/naive12/b/save.json
log
```
Output: `HISTORY: 0 / nothing / nothing has happened yet` — even though the resumed game
correctly shows the money, reputation, and tech-count changes from those same four events
(`-184 den`, `rep 6`, `2 built by you`). Confirmed by inspecting the save JSON directly:
`python3 -c "import json; d=json.load(open('save.json')); print(list(d.keys()))"` lists
every piece of state the engine tracks (money, reputation, scandal, mine_pending, wages_paid,
etc.) but **no log/history field of any kind exists in the file.**

**What should happen vs what happens:** The game's own farewell message ("Saved to X. Come
back with...") and the help text for `log` ("your own history — what you did and what
followed") both promise continuity. Every other piece of state round-trips through the save
file correctly. The event log is the one exception: it lives only in the current process's
memory and is unconditionally discarded the moment the session is resumed, 100% of the time,
for every kind of event (player actions, completions, interest charges, random events,
society-wide unlocks). A player who quits and comes back — which the game explicitly
advertises as safe — permanently loses the "what did I just do and why" record `log` and
`stuck` implicitly rely on, with no warning that this will happen.

**Severity:** does not corrupt the simulated economy/tech state itself, but it is a clean,
always-reproducible break of an explicit promise ("written to this file after every command,
so you can stop any time... and come back to exactly where you left off") — "exactly where
you left off" is false for one whole subsystem.

---

## Finding 4 (minor): `quote mine <material> <n>` silently treats a negative n as 0 instead of refusing

**Repro:**
```
quote mine coal 500     # -> tonnes per year: 500, to sink it: 4,500, every year it stands: 750
quote mine coal -1      # -> tonnes per year: 0,   to sink it: 0,     every year it stands: 0
quote mine coal -999999 # -> identical all-zero quote, no error
```
Every other quantity-taking command checked (`hire`, `buy slaves`, `buy mine`, `step`)
refuses a negative or zero argument outright with an explicit `REFUSED: n must be greater
than zero...` message. `quote mine` is the one path that instead silently clamps the
negative input to 0 and prints a valid-looking (if useless) report, rather than refusing it
like its siblings. No money or state changes as a result (quote never commits to anything),
so this is purely an input-validation inconsistency, not an exploit.

---

## Finding 5 (cosmetic): the prompt's money figure and the printed `Money:`/`Capital:` line disagree by up to 1 denarius on the same turn

**Repro:** any turn with a non-integer cash balance, e.g. from the `richtest` bribe test:
```
bribe 1000000
# reply:  ... protection 0.00 -> 0.32  capital: 999,924
state
# [100 AD | 999923 den | ...] prompt   vs   "Money: 999,924 den" in the body, same instant
```
The bracketed prompt truncates the balance toward zero while the body text rounds it to the
nearest denarius, so the two on-screen figures for the identical quantity, printed a line
apart, differ by 1. Purely cosmetic — the underlying ledger reconciles exactly (verified
separately: `Capital` before a plain step, minus that step's printed `net`, equals `Capital`
after, to the fraction, across several turns with no projects running) — but it is exactly
the kind of "two printings of the same number disagree" surface the game should not have.
