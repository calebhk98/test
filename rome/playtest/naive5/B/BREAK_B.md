# BREAK_B — playtest notes

Started. Goal: Han China, 100 AD, fog of war ON, poor scholar purse, founder NOT ageing.

## Setup
Answers piped: `1` (Han China 100), `y` (fog of war ON), `poor_scholar`, `n` (founder does not age).
Save file created: `/home/user/test/rome/playtest/naive5/B/han_china_100ad.json`.
Opening prompt line: `[100 AD | 400 den | you:2000 hr | sch 0 art 0 | rep 5] >`

EXPECTATION going in: a tech-tree sim where hours + money + reputation gate projects.
Suspicion targets, in order: (1) save-file trust / resume semantics, (2) fog of war leaking
info via `why`/error messages, (3) money and hour accounting (negative values, overspend),
(4) time: `step` with weird args, (5) people/hiring economics.

## First look (year 100)
- 135 technologies "granted for free"; 0 built by me. Already earning 233.5 den/yr from
  `med_cataract_couching` (166.7) and `med_trepanation` (66.7) — a penniless newcomer who has
  never introduced anything is already running a surgical practice. EXPECTED: 0 income at start
  for a "poor scholar ... must earn". ACTUAL: +233.5/yr revenue, net +3.5/yr. Suspicious, noted.
- `available` shows `med_obstetric_practice`: cost 14.1, hours 0, years 0, earns 12.5/yr.
  EXPECTATION: a project costing 0 hours and 0 years that pays 12.5/yr forever is a money pump.
  If several exist, the "poor founder choosing between eating and building" framing is broken.
  Going to test.
- Attack surface list from `help commands`: save/load arbitrary file, JSON command paste,
  work <trade> <hours>, bounty, bribe, quote, step <years>, hire/fire/train/commission, buy.

## Guards that HELD (could not break)
- `step -5` / `step 0` -> "REFUSED: years must be >= 1". `step 0.001` -> "REFUSED: years must be a
  whole number of years; 0.001 is not. Nothing was changed."
- `work smith -1000` -> REFUSED hours>0. `work smith 1000000` -> "REFUSED: you have 2000 of your own
  hours left this year, not 1000000".
- `bribe -5000`, `hire smith -3`, `buy slaves -5`, `commission smith -400` all REFUSED with
  "Nothing was changed."  Negative-number injection is properly guarded everywhere I tried.

## FINDING 1 (confirmed, mechanic): free-granted revenue is a linear function of unspent founder hours
Repro, from a fresh 100 AD save:
  `money`                -> Revenue 233.5/yr (med_cataract_couching 166.7, med_trepanation 66.7)
  `work smith 1`         -> earned 0.10; `money` -> Revenue 233.4 (166.6 + 66.6)
  `work smith 1999`      -> earned 151.3; `money` -> Revenue 0, no "from:" block at all
EXPECTED: taking a side job would not delete a standing medical practice's whole annual income;
at worst it should prorate. ACTUAL: it does prorate, exactly linearly with founder-hours left, and
at 0 hours the income silently disappears from the ledger with no message. Defensible as a model
(you can't operate if you're at the forge) but there is NO warning: nothing tells you that spending
hours costs you revenue, and `work` is advertised as "do an ordinary job for ordinary pay".

## FINDING 2 (numbers contradict the game's own claims)
- Setup screen: "poor_scholar 400 den — A few months' subsistence". Ledger says living and
  appearances = 230 den/yr. 400 den is therefore ~1.7 YEARS of subsistence, not "a few months".
- `work smith 2000` (an entire working year of skilled smithing) earns 151.3 den, i.e. 0.076 den/hr,
  while merely existing costs 230 den/yr. An ordinary tradesman in this world cannot feed himself
  by working. Confidence this is wrong: high that it is internally inconsistent, medium that it
  is unintended.
- Side effect: after `work smith 2000`, "living and appearances" DROPPED 230 -> 218.3 and the credit
  limit dropped 1,025 -> 937.5, purely because revenue went to 0. Expenses that shrink when your
  income shrinks were not explained anywhere.

## FINDING 3 (undocumented commands)
`help commands` lists 20-odd commands and does NOT include `open` or `ventures`, yet NOTHING you
build earns anything until you `open` it. You only learn this from the completion event text.
