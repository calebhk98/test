# WEIRD_C — playtest notes

Playtester: naive5/C. Instructions: play strangely, don't play to win.

## Ground rules I'm holding myself to
- Only the running program tells me anything. No reading source, data, docs, or other notes.
- Notes appended as I go, including **what I expected before I did it**.

## Planned stance (before I've seen anything)
Setup asked for: Han China, 100 AD, fog of war ON, "poor scholar" purse, founder does NOT age.

Expectation before launch: this is some kind of dynasty/empire management sim. "Founder"
suggests I play a person who starts a thing (a school? a house? a business?). "Poor scholar"
purse suggests deliberately low starting money. Fog of war ON means I won't see the map.

My weird plan, chosen in advance so I can commit to it:
1. **Do nothing for a very long time.** Advance time repeatedly with no actions and see
   whether the world moves without me, whether the game nags, and whether it can handle a
   player who simply never engages.
2. Then, **commit to poverty**: if there's a way to spend or give away money, do it, and
   refuse every profitable option.
3. Build many things and never use them, if building exists.
4. Repeat one single command over and over far past any point of usefulness.

---

## Log

### Setup (100 AD)

Chose: Han China 100 AD / fog ON / poor_scholar (400 den) / founder does not age.

Game revealed itself as "ONE PERSON, AND EVERYTHING THEY KNOW" — a time-traveller-with-modern-
knowledge tech-tree sim. Status line: `[100 AD | 400 den | you:2000 hr | sch 0 art 0 | rep 5]`.

**Expectation before first real command:** "you:2000 hr" is my own labour budget per year
(2000 hours = a working year, which is a nice honest touch). "sch"/"art" are probably scholars
and artisans I employ. "rep" is reputation, 0-10ish. I expect `available` to list buildable
techs with costs, and `step` to burn a year. I expect the game to want me to build a workshop,
earn money, hire people, and climb a tree toward some industrial goal.

**My contrarian plan, decided now, before I know anything:** the game just told me my hours are
the scarce resource and that a poor founder spends the first fifty years "choosing between eating
and building." So I will choose neither. I will do **absolutely nothing for 50 years** and see
whether a world with 58 million people in it can produce any history at all without me.

### The goal, and the first oddity

`help` says: **"Build point-contact transistor, before the horizon at 600."** 500 years, founder
immortal. I start with 133 technologies "granted for free" and 0 built.

`available` says 91 startable. Two of them cost **0 den, 0 hours, 0 years**:
- `lnd_cursus_publicus` (Cursus publicus courier service) — 0/0/0, upkeep 200/yr
- `sea_pharos_lighthouse` (Pharos lighthouse) — 0/0/0, upkeep 0

Both are Roman institutions offered to me in **Han China**, which is the first thing that made me
blink. A Pharos lighthouse in Luoyang, an inland capital 600km from the sea, for free, instantly.

**Expectation:** free/instant things are probably "you already have access to this because the
state provides it" rather than real builds. I'll come back to them.

### Experiment 1: do nothing for fifty years

**What I expect:** money is +3.5 den/yr with nothing running, so I cannot starve. I expect the
world to move on its own — the game told me the Yellow Turbans come in ~180 and warlords after.
I expect it to nag me, and I expect `step 50` to either be refused or to print 50 boring years.
I want to know whether a game about one person doing everything notices when the one person
does nothing.

**What actually happened (100 → 150, zero actions):**
- Money 400 → **839.2**, and net income *rose* from +3.5/yr to **+21.2/yr**. I own nothing, employ
  nobody, and run nothing. **Where is this money coming from?** The game charges me "food, rent and
  appearances" every year and I still get richer, faster over time. That is the single most
  unrealistic thing I have seen so far: an idle penniless scholar compounding capital.
- Reputation **5 → 1.5**. So the game *does* punish idleness in one channel. Good.
- Events fired on their own: fire in the timber wards of the capital in 104, 130, 137, **and 141**
  — the same identical event four times, twice within four years. Plus one "banditry or frontier
  war disrupts supply" in 141.
- **Zero nagging.** No "are you sure", no hint, no prod. `step 50` was accepted without comment.

**Where expectation and reality differ:** I expected doing nothing to be survivable but flat. It
is not flat — it is *profitable and accelerating*. I expected the intro's promised history (Yellow
Turbans at ~180) but 100–150 produced only a repeating capital fire.

### Experiment 1b: keep doing nothing, through the promised catastrophe

The opening screen spent a whole paragraph on: "Eighty years, then the Yellow Turbans, then the
warlords, then three centuries of division." **Prediction: the simulation does not actually model
this.** I predict 150→250 gives me more generic "fire in the timber wards" and no Han collapse,
because the events I've seen so far read as a generic random table, not a scripted history. If I'm
wrong and there's a scripted 184 event, that's a point in the game's favour.

**I was wrong, and the game deserves the credit:** the history IS scripted and specific.
- EVENT 184: Yellow Turban rebellion (values shift, `w_religious_rigidity` rising 0.16→0.30)
- EVENT 187/189/190/203: Yellow Turban rebellion sacks sites
- EVENT 220: Three Kingdoms fragmentation, "trade and output fall to 60% of normal",
  `patronage_weight` 0.70→0.75, `w_commerce` going negative
That's real, dated, scenario-specific history. Nice.

**Then it fell apart.** Doing nothing turned into a *debt spiral*, from a standing start of
"I own nothing and spend nothing":

- 231: interest on 149 den of arrears at 12%/yr
- 232: **BONDAGE** — "For about 12 years most of your hours belong to someone else"
- 235: INSOLVENCY SETTLED, still owe ~58 den, reputation −12
- 235: "your term is served" — **three years after a twelve-year term began**
- 237: BONDAGE again → 240 served (3 yrs)
- 241: BONDAGE again → 245 served (4 yrs)
- 247: BONDAGE again (still running at 250)

**Bugs / inconsistencies found here:**
1. **The bondage term never matches its own text.** It says "about 12 years" every single time and
   then discharges in 3–4. Four times in a row.
2. **Status line contradicts the ledger.** At 250: `Money: -151.4 den` but
   `IN DEBT BONDAGE: 9 years left owing 11 den`. Owing 11 or owing 151?
3. **Reputation floors at 0.10** and then takes another −12 from insolvency, twice, with no visible
   effect. A penalty applied to a value that cannot go lower is a penalty that isn't real.
4. **I was sold into debt bondage for a debt I had no way to incur.** I own nothing, employ nobody,
   run nothing, and started the century with 839 den in hand. My *upkeep* alone bankrupted a man
   with no possessions. And a bondsman apparently still pays rent and "appearances."

**Where expectation and reality differ:** I expected idleness to be boring and safe. Instead the
economy has a one-way ratchet — passive income that scales *up* while you're solvent, and fixed
costs that don't scale *down* when you're destitute — so "do nothing" is not a stable state, it's
a delayed loss. That is arguably realistic, but the game presents `step` as the neutral no-op and
never once warns you that the neutral no-op is fatal.

### A tooling note that turned into a finding

The `step 100` run above **did not save**. Re-opening the session put me back at 150 AD. My own
fault (I piped output through `head`, which killed the process on SIGPIPE), but the help text
claims *"Progress is written to this file after every command, so you can stop any time — close
the terminal, anything."* That is not true: progress appears to be written on a clean exit. A
player who closes the terminal mid-step loses the step. **Worth fixing, because the game
explicitly promises the opposite.**

### Where the money was actually coming from — this is the good one

`money` at 150 AD:
```
Capital: 839.2 den     Revenue: 259.3 den/yr
  from:
    med_cataract_couching        185.1
    med_trepanation               74
Costs: living and appearances    238.1
```

**I never built either of those.** They are among the 133 technologies "granted for free". So the
game has quietly been earning me a living, for fifty years, by having me perform **cataract
couching and trepanation** — drilling holes in Han skulls — on a man who has issued no orders at
all. My entire economy, the one that later collapses and sells me into debt bondage, is an
unchosen skull-drilling practice.

**Expectation vs reality:** I expected "granted for free" to mean *knowledge I possess*, not
*a business I am operating*. Nothing in `state` or `available` told me I had a revenue-generating
medical practice; I only found it by asking `money` for a breakdown. And it is odd that of 133
granted technologies, exactly the two gruesome surgical ones are the ones that pay.

Re-ran identically: **deterministic**, same events, same numbers, same bondage loop. Saved at 250 AD,
−151.4 den, 500 hours, rep 0.10, **0 technologies built**.

### Experiment 1c: run past the end of the world

**What I expect:** I will `step 400`, which overshoots the 600 horizon by 50 years. I expect one of
three things and I want to know which: (a) it clamps at 600 and declares me a failure, (b) it runs
to 650 and the horizon turns out to be decorative, (c) it errors. I'm betting on (b) — the horizon
is described as a scoring deadline, not a wall, and nothing so far has refused an input.

I also expect the debt-bondage loop to repeat roughly every 4–5 years for 350 years, i.e. about
80 more times, on a man who owns nothing.
