# Playtest notes — "One person, and everything they know" (rome/sim/simulator.py)

Naive player, no source read, no manual. Session: Rome 100 AD, poor_scholar kit, fog of war ON,
mortality OFF (all defaults except the civ choice).

## Running log

### First contact
- Great opening. The five-civilisation menu is genuinely enticing and the flavour text for Rome
  ("Domitian is four years dead and nobody has corrected the milestone") is the best writing I've
  seen in a terminal game in a while. The "WHAT IS MISSING / Not the ideas. The instruments."
  framing immediately told me what the game is about.
- Confusion 1: at the very first prompts, `help` is not accepted. At `Which? [destitute/...]`
  typing `help` gives "I did not understand that. Options: destitute, poor_scholar, ...". Fine,
  but I had no idea what those wealth levels *meant for play* beyond the denarii figure until
  much later.
- Bug/leak: `--civ rome` errors with
  `unknown civilization 'rome'. available: _TECH_EFFECTS, england_1300, han_china_100ad, mexica_1500, norse_900ad, rome_100ad`
  `_TECH_EFFECTS` is clearly an internal table leaking into a user-facing list.
- `help economy` and `help money` print the identical text (the "the ledger:" block). `help economy`
  is listed as its own topic in the `more:` list, so I expected something different.
- Nice: the game says up front it saves after every command and tells you the resume command.

### Learning the loop (years 100-114)
- **The best thing in the game**: `why <id>` is superb. Full cost breakdown, hours, calendar floor,
  failure risk, staff needed, hired labour, materials, upkeep, revenue, prerequisites, plus a
  paragraph of real history ("Roman throat-and-girth harness chokes a horse under heavy draught.
  The size of the improvement is disputed in modern scholarship, so claim a real but modest gain,
  not the old textbook figure of four times."). I trusted the game immediately because of this.
- **Confusion 2 (big)**: `why point_contact_transistor` →
  `REFUSED: you have never heard of any such thing ... Did you mean: fin_contract_law`
  The status line literally says `Aiming at: Point-contact transistor` every single turn. Being
  told what my goal is and then told I've never heard of it is jarring, and the "did you mean"
  suggestion is nonsense. At minimum the goal node should be inspectable.
- **Confusion 3**: `available "power and precision"` (quoted, because the subject has spaces)
  returns `0 startable now`. Unquoted `available power and precision` works. Quoting is the
  natural instinct and it silently fails rather than saying anything.
- **Trap 1 — `work` is a nearly-pointless trap.** `work scribe 500` paid me 80.1 den. But my
  passive revenue (from *granted* techs `med_cataract_couching` / `med_trepanation`) silently
  scales with my *free founder hours*: it fell from 233.5/yr to 175.2/yr the same instant.
  So 500 hours of paid work netted ~22 den. Nothing anywhere says founder-hours drive revenue.
  I only worked it out by diffing the ledger.
- **Trap 2 — `policy auto_train on` nearly ended the run.** Its own description says it
  "teaches trades this society does not have *when a project needs them*". No project of mine
  needed them. Within three years it had started engineers, chemists AND machinists, at
  781 den/yr each, against revenue of 1,005 den/yr. I went from +685/yr to -1,074/yr and
  -1,951 denarii. Turning the policy off does **not** cancel training already in flight —
  four more people I never asked for arrived over the next two years and the wage bill hit
  2,491 den/yr. There is no `cancel training` command that I could find.
- **Inconsistency**: I may go 3,000 denarii into debt by `start`ing projects, but
  `hire artisan 3` is `REFUSED: hiring 3 artisans costs 750 denarii in advance and you have -3059`.
  Credit exists for one kind of spending and not the other, with no explanation.
- **Confusion 4 — the `open` gate.** Finishing a project earns you nothing. You then have to
  `open` it, and opening needs *supervisors*:
  `REFUSED: nobody free to keep an eye on it: it needs 0.0 scholars and 0.6 craftsmen to
  supervise, and you have 1.0 and 0.2 not already watching something else.`
  Nothing in `why horse_collar` mentions supervision, so a 709-denarius project I'd already paid
  for sat idle. The `REVENUE: 900 den/yr` line on `why` reads as a promise; it is actually
  conditional on money-to-open plus free supervisory craftsmen.
- **`policy` reporting is good**: `switched on but cannot act right now: auto open: nothing to
  open with: opening a concern costs stock and premises` is exactly the kind of feedback I want.
- Nice: `risk` with dated hazards (Antonine plague 165-180, debasement 190-275, sack of Rome
  406-460) and a "you could begin now: X (cost, why it helps)" hint per hazard. That is a
  genuinely elegant way to connect the tech tree to history.
- Mild oddity: `com_optical_codebook` and `com_signal_flags` are filed under the subject
  **electricity**. Also `mat_camphor` shows `COST 0` which looks wrong.

### The mid-game (years 114-153): the real game is a staffing puzzle nobody explains
- **The single biggest hidden mechanic: a hard cap on headcount.**
  `REFUSED: you can supervise, house and teach 0.72 more people, not 8 - you have no room for even one.`
  This number appears **nowhere** — not in `state`, not in `state full:true`, not in `labour`,
  not in `ventures`. The only way to see it is to try to hire and be refused. I had
  285,000 denarii in the bank and could not hire a sixth person. Please put
  "staff: 9.7 of 15 places" in `state` and `labour`.
- Relatedly: what *raises* the cap is only revealed by the refusal text, and the refusal text
  **changes over time**. At year 120 it said "hire smith 3 ... or commission ... or buy slaves".
  At year 126 it suddenly added "build workshop_first (you need somewhere for them to work)"
  and at 129 "build freedman_staff". These are the two most important buildings in my whole game
  and the game only names them inside an error message, once they happen to be unlocked.
- **Concerns silently close and you keep paying for the loss.**
  `EVENT 151: nobody left to keep an eye on 4 concerns, so arithmetic_positional, med_bone_setting,
  prn_magic_lantern, pwr_coal_seam closed.` This happened over and over, every year, because staff
  attrition (3.5%/yr) constantly drops supervisory craftsmen below the threshold. It cost me
  hundreds of denarii per year in re-opening fees and I could never get ahead of it. There is no
  "keep this open" priority, and `auto_open` will not reopen them either.
- **The engineer trap.** Engineers cost ~780-1,090 den/yr against an artisan's 250. They count as
  *scholars*, so they cannot supervise a concern. I spent 30 years being poor because
  `auto_train` had bought me engineers. The turn I fired 3 engineers and hired 3 artisans my net
  went from **-155/yr to +4,164/yr**. Nothing in the game hints that trade choice matters that much;
  `labour <trade>` shows the wage but not that scholars can't watch a workshop.
- **HALTED loses everything, with only a start-time warning.**
  `EVENT 150: HALTED en_two_stroke_cycle: there is nobody here who can do this work
  (engineer, machinist). What you spent is lost` — six projects wiped in one year. `start` does warn
  ("warning: no one can do this work YET"), but there is no way to list which of my in-flight
  projects are at risk of halting, and no grace command to cancel and recover.
- Wages inflate with reputation: engineers were 781 den/yr at reputation 16 and 1,094 at
  reputation 25. That is a nice touch but it is never stated, so my budgeting kept being wrong.
- **Pleasant surprise**: the "you could begin now: X (cost, why it helps)" hints inside `risk`, and
  `HEARD OF, CANNOT BEGIN YET` telling me *exactly* why each thing is blocked ("the state is wary
  of this (state interest -0.6); get at least a local patron first" / "missing prerequisites:
  arithmetic_positional" / "this needs 1 other thing you have not heard of yet"). That last one is
  a lovely way to do fog of war.
- **Annoyance**: the whole `HEARD OF, CANNOT BEGIN YET` block (25+ lines) is reprinted after every
  single failed `available find X`. Three searches in a row produced ~80 lines of identical text.
- **Annoyance**: `available society and politics` → `nothing in 'society and politics'` even though
  the subject summary printed one line earlier listed `society and politics  1  1,200  1,200  1`.
  (The one item was already active, but the summary counts it and the filter doesn't.)

### Run 1 ended in defeat: 289 AD, "too eminent", 311 years short of the horizon
Final position: 1,385 technologies built, 73,234,107 denarii, 225 staff, +4.97M den/yr,
`reputation 98.3  protection 92%  scandal 1.8  eminence 32.6`.

- **This is the thing I'd most want changed.** `help eminence` says "Nothing lowers it directly,
  which is the point." Eminence rises automatically with reputation and visible wealth, both of
  which rise automatically with *playing well*. The only two counters named (`academy_network`,
  `corpus_dispersed`) are 8-10 year builds sitting behind long prerequisite chains
  (`academy_network` needs `endowment_land`, costs 56,810 den and has a **10-year calendar floor
  that "money cannot buy down"**). By the time the game first told me eminence existed as a
  threat — `EVENT 210: YOU ARE BECOMING CONSPICUOUS: eminence 25 against a danger line of 26` —
  I had no way to get either counter finished in time. I died 2 years after finally being able to
  *start* `academy_network`.
- Worse, the same hazard has two completely different outcomes and nothing distinguishes them:
  `EVENT 230: PROMINENCE: property confiscated, 6432649 den lost, and you withdraw from public
  life for a while` (survivable, happened twice) versus, at 289, instant permanent run-over. The
  status line said `7% chance of ruin this year` in both cases. I had no way to know one roll was
  a fine and another was death.
- The `EMINENCE is dangerous above 26 (settles near 39.2...)` line tells you the *steady state* is
  far above the danger line. That is effectively an announcement that a successful run is
  scheduled to die, and there is no lever in the UI that reads as "get smaller".
- **The game-over is handled badly.** My input batch kept going, and the game printed
  `REFUSED: the run has ended (too eminent...)` **fifteen times in a row**, once per queued
  command, before finally adding "; time cannot advance. Use state to see the final position."
  There is no summary screen: no "you built 1,385 of N", no "here is how far you got along the
  road to the transistor", no offer to restart. After 190 simulated years that is a flat ending.

### Clear bug: "waiting on money" with 73 million denarii in the chest
  `academy_network   100% of your hours spent, 45,448 still owed - waiting on money`
  while `Money: 73,234,107 den    net +4,973,645 den/yr`. The same wording appeared much earlier
  with `corpus_written   100% of your hours spent, 945.1 still owed - waiting on money` when I had
  403,199 den. If there is a per-year spending rate cap, say *that* ("spending is limited to X/yr
  on this"); "waiting on money" when you are sitting on a hundred times the sum is simply wrong.

### Other things from the late game
- `why <id>` works for anything you have *heard of*, including things not in `available` —
  that is how I finally found `academy_network`'s prerequisite (`endowment_land`) and read the
  whole road to the transistor (`point_contact_transistor` ← `single_crystal` + `vacuum_tube`
  ← `cap_vac_1e6`, `copper_refining`, `diffusion_pump`, `discharge_xray`, `gp_exhaust_pinchoff`,
  `gp_getter` ← ... ← `zinc_industry_scale` ← ...). **But the goal node itself was `REFUSED: you
  have never heard of any such thing` for the first 187 years** even though the status bar named
  it every turn. Make the goal always inspectable.
- `available find X` searches display names only, not ids. `available find cap_` finds
  "Cap frame spinning", not any of the `cap_*` capability nodes, which are the spine of the game.
- `HEARD OF, CANNOT BEGIN YET` is silently capped at ~25 rows. With 1,000+ nodes in play there
  was no way to page through the rest and no note that it was truncated.
- `no viable option in a required substitution group (fuel, vessel, etc.)` is the one blocked-reason
  I never decoded. It names no candidate and no fix.
- Nice: the note on `zinc_industry_scale` ("germanium concentrates in the flue dust of zinc
  smelters, at the parts-per-thousand level in the dust against 1.6 ppm in the crust. Design the
  flues for dust collection from the first furnace or you will rebuild them later") is the single
  best paragraph in the game. Also lovely: `Currency debasement: ... you feel less of it (you can
  assay ore and coin yourself)` — the hazard system actually reads your tech.
- Nice: founder-hours grow. `You: alive, 10,175 founder-hours free this year (2,000 of your own,
  plus 4.5 deputies directing work in your name at 1,800 hours each)`. I only noticed by accident;
  nothing announced that `school_founded`/deputies had changed my hour budget.

### Run 2 (fog OFF): died the same way, faster — 221 AD, "too eminent"
Turning fog off is a completely different, much better game. `path <id>` prints the whole ordered
remaining route (142 nodes to the transistor), and `why <id>` gains three brilliant extra lines:
`FULL CHAIN BEHIND IT: 22 nodes, 16,460 of your hours, 252,154 den, 30-year serial floor`,
`DIRECTLY UNLOCKS: ...` and `TOTAL DOWNSTREAM: 2,008 thing(s) depend on this -- INCLUDING THE GOAL`.
Those are the numbers you need to make any decision at all. Under fog you are guessing.
**My honest reaction: fog-of-war-on is close to unplayable for a first-timer and fog-off is the
real game.** The menu presents fog as the default (`Fog of war? [Y/n]`), which I think is backwards.

- Run 2 died at eminence ~30 in 221 AD, *earlier* than run 1, precisely because I played better and
  got rich faster. The "settles near" figure tracked my income: at 2.2M capital it said
  `settles near 25.9`; two rounds later at 5.5M it said `settles near 38.9`. So the reward for
  building an economy is a guaranteed death sentence, and the counter (`academy_network`) has a
  **30-year serial floor and 22 nodes behind it** and needs 10 scholars in a society that
  `REFUSED: this society's literacy will not supply more than 5.9 scholars in total, ever, at any
  price`. The two clocks are not compatible unless you know from turn one to beeline it, which is
  exactly what a first-time player cannot know.
- Circular hint, verbatim: `why workshop_first` says it is blocked for want of artisans, and the
  advice for getting artisans is "...build workshop_first (you need somewhere for them to work)".
  (Hiring 2 artisans directly does work; the hint just points at itself.)
- `INSOLVENCY SETTLED: most of the debt is written off ... reputation -12` fired twice in six years
  during a botched expansion and took me from reputation 9 to 0, plus
  `CREDIT EXHAUSTED: 4 projects halted, unfinished. Nobody will fund new work here for some years`.
  A recoverable-looking cash dip turned into a 40-year dead run with no warning that I was near
  the edge. `money` shows a credit limit but nothing shows how close to insolvency you are.
- `REFUSED: cannot afford 40000 ha of coppice woodland (you have 5528831 denarii)` — it tells you
  what you have but not what it costs. (`quote` covers mines beautifully; there is no
  `quote forest`.)
- Lovely: `money` eventually explains the thing I had to reverse-engineer in run 1 —
  "YOUR PRACTICE: med_cataract_couching, med_trepanation are your own practice, and they pay about
  a third of what the tree quotes... Selling your hours for wages takes another bite out of it,
  because you cannot be in two places." That text should appear on turn one, not after I've already
  lost 500 hours to `work`.
