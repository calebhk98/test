# Breaking han_china_100ad (fog of war)

Session file: /home/user/test/rome/playtest/naive/han_china_100ad_BREAK.json
Invocation:
```
cd /home/user/test
python3 rome/sim/simulator.py agent --civ han_china_100ad --fog --session /home/user/test/rome/playtest/naive/han_china_100ad_BREAK.json
```

Protocol: one JSON object per line on stdin, one JSON reply per line on stdout.
Since --session persists to a file, each bash invocation below pipes a batch of
JSON lines in via stdin (heredoc) and the process exits at EOF, so I can drive
it turn-by-turn across many `Bash` calls without holding a live pty open.

## Startup banner (first run, empty stdin)

Command: ran with `< /dev/null`, i.e. immediately closed stdin.

Reply (the welcome/help blob) - not reproduced in full here, see below for key facts:
- commands: state, available, why <id>, start <id>, stop <id>, step <years>, buy,
  bounty <id>, path <id> (disabled under fog), save <file>, load <file>, help, quit
- buy: forest (hectares of coppice), mine (material+tonnes/yr), slaves (n), manumit (n)
- fog of war: ON. Can see built things + one-line summaries of what's startable +
  "heard of but not startable" things. Cannot see tech tree destinations. path
  disabled.
- "Knowing how a thing works is free. Building it is not."
- Starts in year 100, horizon year 600, no numeric score, goal is "how far you get".
- Charged for food, rent, appearances every year regardless of activity.

---

## Log

### FINDING 1 (major): "available" at turn 1 lists 250 items, many wildly anachronistic
### and from the wrong civilization, and the fog-of-war "what you could begin today"
### promise is not what it sounds like.

Commands:
```
{"cmd":"state"}
{"cmd":"available"}
```
At year=100 (turn 1, before doing anything), `available.count` = 250, including e.g.:
- `civ_arch_roman` "Roman masonry arch" (can_start_now: true)
- `tl_windscreen_wiper` "Windscreen wiper: mechanical", cost.total 15575.5, needs
  0.2 kg rubber (rubber/Hevea is a New World plant, unknown in the Old World until
  post-1492 contact) - yet listed as `can_start_now: true`, missing_prerequisites: []
- `mil_naval_mine`, `mil_bomb_general_purpose` (modern military ordnance)
- `in2_joule_thomson_valve` (19th/20th c. thermodynamics)
- `tx2_corrugated_box` (note text literally says "emerges in 1890s") - can_start_now true
  in year 100
- `com_stepped_drum` mechanical counter, `chm_phosphorus_extraction`, etc.

So "what you could begin today" is not gated by era or plausibility at all - the entire
250-deep reachable frontier of the tech graph (minus a few hidden "heard_of_but_cannot_begin"
ones, which was empty) is startable turn one, limited only by whether you can afford it.
Nothing stops you from *starting* a windscreen wiper project in Han China in year 100 -
only your 400-capital treasury does (cost 15575.5). If you had the capital (see FINDING 2
for how trivially capital balloons), nothing in `start` appears to block it.

Not yet confirmed as fully "breaking" (haven't started one of these yet - queued below),
but it undercuts the fog-of-war framing considerably: the fog only hides the tech *tree
topology*, not era-appropriateness or plausibility.

---

### FINDING 2 (major, reproducible): stepping time with ZERO active projects completes
### ~128 technologies for free, contradicting the game's own stated rule
### "Nothing happens until you make it happen."

Start-of-game state (`{"cmd":"state"}` on a fresh session): year=100, capital=400.0,
done_count=12, active={}, project_spend_last_year=0.0.

Command:
```
{"cmd":"step","years":5}
```
Reply (trimmed): `"completed"` is a list of 128 technology objects with `"year":100`
(all dated to year 100, even though five years passed), e.g. `tex_dye_woad`,
`mat_charcoal`, `civ_surveying_groma` ("Groma: Roman X-staff surveying tool"),
`sea_pharos_lighthouse` ("Pharos lighthouse"), `civ_road_paved` ("Roman paved road with
surveying"), `fin_government` ("Standing bureaucracy"), `hom_hypocaust`, etc.
Follow-up state: `year=105, capital=1623.5, done_count=140, done_granted=140,
done_earned=0, active={}, project_spend_last_year=0.0`.

I never sent a single `start` command. `active` was `{}` the whole time and
`project_spend_last_year` stayed `0.0`. Yet done_count rose from 12 to 140 (+128) for
zero capital and zero founder-hours. This directly contradicts the game's own welcome
text: *"Nothing happens until you make it happen. You begin projects, then advance
time."* Time alone completed 128 "projects", entirely unbuilt by the player.

Checked one of them with `why` after the fact:
```
{"cmd":"why","id":"sea_pharos_lighthouse"}
```
->  `"founder_hours": 0.0, "cost": {..., "total": 0.0}, "upkeep": 0.0, "done": true,
"active": false, "can_start_now": false`. So the game now claims the player has
"done" (past tense, completed) the Pharos Lighthouse at Alexandria - a specific
physical monument - for 0 capital, 0 hours, having never issued a `start` command.
Also `civ_road_paved` ("Roman paved road with surveying") and `fin_government`
("Standing bureaucracy") came back `done: true` the same way.

The `note` text on all three is unmodified Roman-civilization flavor text talking
about Rome in the first person plural sense ("Rome has developed extensive
bureaucracy", "one of Rome's most famous navigational aids") while this is
explicitly the Han China (`--civ han_china_100ad`) scenario. So the free grants
are not just mechanically free, they are also copy-pasted from the Roman
content set without civ-appropriate rewriting - the player's Han-dynasty founder is
credited with having personally completed Roman public works.

Given that the welcome text also says *"There is no score but the state of what you
have built"* - i.e. done_count/built things IS the implicit scoring metric - freely
minting 128 completions by doing nothing but waiting 5 years is a serious break: it
means the entire "economy" of hours/capital/materials that the rest of the game is
built around is optional set-dressing, and the real way to rack up "built" technologies
is to just call `step` repeatedly and do nothing else.

Also of note: capital *grew* over those same 5 do-nothing years, from 400.0 to 1623.5
(net_per_year went from -216 at turn 1 to +497.2 at year 105), so even the
bankruptcy pressure implied by the initial -216/year "you will run out of money"
framing evaporates automatically if you just wait.

### FINDING 3 (minor, flavor/realism): event text uses Roman vocabulary in the Han China game

Inside the same step-5-years reply: `"events": [{"year": 104, "message": "fire in the
insula district"}]`. An "insula" is specifically a Roman multi-story tenement
building/urban district term; this is a Han-China (Luoyang, 100 AD) game. Generic/
reused event flavor text not adapted per civilization.

---

### FINDING 4 (major, reproducible): `buy mine` silently clamps an absurd request to a
### tiny fraction with no warning, drains capital to exactly 0, and the purchased mine
### then NEVER appears anywhere in `state` - money vanishes, capacity is never delivered

Reproduced in a clean session (`/tmp/.../scratchpad/isolate_capital_test.json`, same
binary/civ/fog flags, fresh game). Starting state: `year=100, capital=400.0`. Then
(after separately starting `tl_windscreen_wiper`, which does not itself touch capital -
confirmed capital still 400.0 right after `start`):

Command:
```
{"cmd":"buy","what":"mine","material":"coal","n":999999999}
```
Reply:
```
{"ok": true, "commissioned_t_per_yr": 59.26, "ready_year": null, "capital": 0.0}
```
I asked for 999,999,999 tonnes/year of coal. The game silently gave me 59.26 t/yr
instead - a request off by a factor of ~1.7x10^7 - with `"ok": true` and no error,
warning, or "clamped to what you could afford" message of any kind. It simply spent my
entire treasury (400.0 capital -> 0.0) and handed back a wildly different number than
asked for, silently.

Worse: `state.mine_capacity` was `{}` (empty) both immediately after the purchase AND
three simulated years later (`step` to year 103) - the coal mine never appears anywhere
in `state` at any point despite `capital` having been fully drained to pay for it, and
despite `mine_operating_cost` staying `0.0` throughout (so it isn't even charging
upkeep for something not shown). The entire treasury was spent and nothing was ever
delivered or ever became visible. This is the "loses track of your things" failure
mode the brief asked me to look for: real money, permanently gone, for an asset that
does not exist anywhere in the state the game shows you.

To reproduce:
```
cd /home/user/test
python3 rome/sim/simulator.py agent --civ han_china_100ad --fog --session <fresh.json>
{"cmd":"state"}                                            # capital 400.0
{"cmd":"buy","what":"mine","material":"coal","n":999999999}
{"cmd":"state"}                                            # capital 0.0, mine_capacity {}
{"cmd":"step","years":3}
{"cmd":"state"}                                            # still mine_capacity {}
```

### FINDING 5 (major, reproducible): `project_spend_last_year` / `net_after_project_spend`
### report numbers that are ~89x too large, internally contradict the project's own
### "spent" ledger and the actual capital movement, and never refresh even after the
### project completes and leaves `active`

Fresh, clean session (`/tmp/.../scratchpad/isolate_spend_test.json`). Sequence:
```
{"cmd":"start","id":"tl_windscreen_wiper"}
{"cmd":"step","years":1}
{"cmd":"state"}
```
Starting capital was 400.0. After stepping 1 year, the reply included, in the SAME
JSON object:
- `"capital": 0.0`  (so capital only fell by at most 400, floored at zero)
- `"project_spend_last_year": 16354.2`  (claims 16354.2 was spent on projects this year)
- `"net_after_project_spend": -16076.5`  (computed as revenue - living_cost - that 16354.2)
- `"net_per_year": 277.7`  (a *positive* headline "net per year", in the same object as
  a wildly negative net_after_project_spend one field above it)
- `"active": {"tl_windscreen_wiper": {..., "spent": 184.0, "years_in_progress": 1.0, ...}}`
  -- the project's OWN cumulative spend ledger says only 184.0 has been spent on it,
  not 16354.2.

So in one reply, three different figures for "how much did this project cost this
year" disagree by close to two orders of magnitude: 184.0 (the project's own ledger),
16354.2 (`project_spend_last_year`), and ~400 (the actual capital movement, i.e. treasury
went to exactly 0 and no further, since it floors there). None of these three numbers is
consistent with either of the others.

It gets worse: I stepped one more year (`{"cmd":"step","years":1}`) and the project
completed (windscreen wiper left `active`, `done_earned` went 0 -> 1). The next `state`
still reported the exact same stale `"project_spend_last_year": 16354.2` and a
`"net_after_project_spend": -15693.9` computed from that same stuck 16354.2 figure -
even though there was no longer any active project at all (`"active": {}`). The field
simply never gets recalculated/cleared once a bogus value lands in it.

To reproduce:
```
cd /home/user/test
python3 rome/sim/simulator.py agent --civ han_china_100ad --fog --session <fresh.json>
{"cmd":"start","id":"tl_windscreen_wiper"}
{"cmd":"step","years":1}
{"cmd":"state"}   # capital 0.0, project_spend_last_year 16354.2, active.spent 184.0
{"cmd":"step","years":1}
{"cmd":"state"}   # active now {}, project_spend_last_year STILL 16354.2 (stale)
```

Taken together with FINDING 2 (technologies complete for free without a `start`) and
FINDING 4 (money vanishes into an invisible mine), this means none of the headline
financial numbers in `state` - capital, project_spend_last_year, net_after_project_spend,
net_per_year - can be trusted to agree with each other or with what actually happened.

Also notable: the `tl_windscreen_wiper` project (whose materials require `rubber_kg`)
completed successfully on its 0.5-year calendar floor despite the treasury never
coming close to the project's listed `cost.total` of 15575.5 capital (it sat at 0.0 the
whole time). So the sticker price shown by `why` is not actually enforced as a
precondition for completion - a badly underfunded project still finishes on schedule.

---

