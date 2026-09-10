# Round two findings, and who is fixing what

Four testers: three naive agents on Norse 900 (play / break / weird) and a
fourth playing independently and reporting separately. Their notes are the
`.md` files beside this one; that fourth report is quoted inline below where it
is the only source.

Some of what they found was already fixed while they were still playing, and is
marked CLOSED with the reason. Everything else is open work.

---

## Already closed

| Finding | Where it stands |
|---|---|
| `available` returns one huge object; 86 entries at the start, 186 after the first wave, and the tool output truncated | CLOSED. It is a digest by subject now, with `subject`, `find`, `afford`, `limit`/`offset` and `all:true`. 21.5KB to 4KB at the start; 165KB to 7KB at year 250. |
| `simulator.py --help` is a wall | CLOSED. 5.6KB to 1.4KB; the design essay moved to `rome/sim/PROTOCOL.md`. |
| `state` repeats a hazard briefing on every call | CLOSED. Short by default; `full:true`, plus `risk`, `money`, `labour`, `policy`. 4KB to 1.5KB. |
| `work` sells the same year's hours twice | CLOSED. Wage hours are committed hours now, and the tally persists across sittings. |
| Wage arbitrage: work as a scholar for 1,416/yr, hire one for 625 | CLOSED. Both sides read the same wage table. |
| `founder_hours_left` goes negative (-776.8) | CLOSED. Floored at zero. |
| `start` names undiscovered prerequisites; a 20-line crawler mapped 163 nodes | CLOSED. Names only what you have heard of and counts the rest. |
| Advice says "build workshop_first" while `why workshop_first` says you have never heard of it | CLOSED. Advice is filtered by visibility. |
| `NaN`/`Infinity` walk through every guard and poison the save file | CLOSED. Rejected centrally, before anything is touched. |
| `policy` reads the string `"false"` as true | CLOSED. |
| Deficit softlock: sheds profitable works, keeps the loss-maker, ignores `auto_shed:false`, and `mothball` refuses the thing bankrupting you | CLOSED. Sheds only what costs more than it returns, honours the switch, and a deliberate shutdown is allowed where automatic abandonment is not. |
| Same `--seed` gives different answers on alternate runs | CLOSED. Three float accumulators iterated a set; summation order changed the last bits and five centuries amplified it. |
| `mil_atomic_bomb` buildable in 978 for 341 denarii | CLOSED. Now needs fission, uranium extraction and an ultracentrifuge. |
| `mil_plate_armour_firearms` startable in 900 with no prerequisites | CLOSED. Needs the matchlock. |
| Fire "in the insula district" of a Norse settlement | CLOSED. Each civilisation names its own quarter. |

---

## A. The setting is Rome wearing a hat  (data)

The loudest finding, from all four testers. Playing Scandinavia in 900:

- `labour` says "Rome has these in abundance and they are good" (masons),
  "Roman plumbarii are skilled and numerous", "Rome has military and hydraulic
  engineers under state employ".
- `available` offers "Establish the Alexandrian physician-philosopher persona".
- Node notes say "Rome already has this (Barbegal, 16 wheels)", "Rome never
  develops the chimney", "Buttons exist in Rome but are rare".
- A refusal reads "not bounty-eligible: a Roman artisan could not recognise
  success at this".
- Six to nine nodes cost 0.0 and take 0 hours and 0 years for a Norse founder:
  `civ_arch_roman`, `fin_annona` (the Roman grain dole), `fin_argentarii`,
  `fin_collegium`, `fin_societas`, `hom_cosmetics_roman`. One tester took all
  six on turn one and doubled their reputation and credit limit for nothing.
- `fud_chinampa`, Mesoamerican lake-bed horticulture, is startable in Norway.

The fourth tester: "This seems unintended rather than alternate-history flavor
because it directly contradicts the selected Norse setting."

## B. Anachronism is gated by nothing much  (data)

- Mustard gas: 77.1 denarii and 1.5 years, the moment a chemist exists. No
  chlorine chemistry, no protective equipment, no delivery system.
- `mil_trench`, whose own text describes machine guns, completed in 903.
- `mil_general_staff` and `mil_trace_italienne` completed around 903-904.
- A tethered man-lifting observation balloon is visible at the start.
- New World crops and voyage crops are ordinary purchasable nodes.

"If modern knowledge makes concepts free, prerequisite material/process
readiness still feels like it should gate them."

## C. Knowledge is not a building  (simulator)

Creditors seized 21 works and the founder forgot Newton's laws and basic
textile technique. Earned progress fell from 45 to 24.

"It is unclear whether creditors can logically make society forget Newtonian
physics and basic textile knowledge... Ownership/maintenance-dependent
facilities should be distinct from durable published knowledge."

Related: repossessed works reappear in `available` looking like fresh research
rather than something you already knew and must rebuild.

## D. The automatic policies do not do what they say  (simulator)

- `auto_hire` at turn one hired 1.32 artisans and 0.38 scholars, took living
  cost from 230 to 699.9, and put capital from 400 to -688 with net -462/yr.
  Its own description is "grow the staff toward what you can house and pay".
- `auto_train` began "teaching the first engineers this world has ever had"
  with no active project needing an engineer, and later created chemists,
  machinists and opticians with no active projects at all. Its description is
  "teach trades this society does not have **when a project needs them**".
- Auto-shed events say "stopped maintaining 1 works" without naming them, so
  you cannot tell what you lost or why an option reappeared.
- Fractional people: 1.32 artisans, 0.07 engineers, "you employ no chemists"
  two years after hiring one. Either say what a fraction of a person means or
  do not show one.

## E. Starting work nobody can do  (simulator)

Four engineer-dependent projects were accepted with `ok: true` and then, years
later, `HALTED ... there is nobody here who can do this work (engineer). What
you spent is lost`. A preflight warning should say so at `start`.

## F. Founder hours are allocated opaquely  (simulator)

Four projects each showed exactly half their founder hours left after one year,
with 2,400 hours available and only about 200 apparently spent. "That equal
halving is confusing and feels artificial; the UI did not explain why."

## G. Five centuries, two events  (data and simulator)

426 years of "fire in the longhouses by the shore" and "banditry or a frontier
war disrupts supply". Christianisation is advertised as a 995-1100 hazard and
produced no event and no visible consequence. No plague, no succession, no
climate, no trade shift, no diffusion of what you introduced.

## H. Smaller, but real  (simulator)

- No command closes a mine. One tester bought a gold mine that produced 0.0
  t/yr, paid every coin they had, got `ok: true` and "Nothing was wasted", and
  was billed 28.1/yr for ever. Operating cost is disclosed nowhere before purchase.
- `save`/`load` is unlimited undo, which defeats fog; `save` writes to any
  absolute path (confirmed into `/etc/`).
- `train` bypasses the supervision cap that `hire` enforces, and pumps the
  labour-market ceiling without limit (smith supply 6,469 to 36,433).
- `step` accepts `years: 100000`; `years: true` steps one year.
- `bribe` works after the run has ended, and charges to reduce 0.00 scandal.
- `hire` accepts `"5"` as a string where `buy` and `start` type-check.
- `buy forest` refuses without quoting the price.
- Under fog the run ENDS on a hidden goal, having said "there is no score" and
  reported `goal: null` throughout.
- A granted capability (`cap_measure_len`) appears in `completed` mixed in with
  things you paid for.

## I. Raw JSON is hard to read  (new work)

"The JSON-lines interface is precise... However, raw JSON is verbose for play
and makes scanning long output harder than a formatted CLI." A human-readable
rendering, alongside the machine one, was asked for by two testers.
