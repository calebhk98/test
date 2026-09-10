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
