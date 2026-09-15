# Playtest notes — first-time player, session A

Result: **won.** Rome under Trajan, 100 AD, fog of war ON, poor_scholar start (400 den),
mortality off. Point-contact transistor completed **583 AD**, 17 years inside the 600 horizon.
284 technologies built, 146-node road, ~41M denarii, 666 people at the end.

---

## TOP PROBLEMS

**1. You can borrow 1,600 denarii to *build* a thing but not 40 denarii to *switch it on*.**
This nearly ended my run in the first five years and it is the single most punishing
inconsistency in the game. `start` happily runs you into arrears against your credit limit.
`open` will not touch credit at all:

> `REFUSED: opening it costs 40 denarii in stock and premises and you have -1,608`

At that moment my credit limit was 3,684 with only 44% used, and I had seven finished
concerns sitting idle that `ventures` itself told me "would clear 1,713 den/yr between them".
So the game let me borrow my way into a hole by building, then refused me the last 40 denarii
that would have dug me out. Either `open` should be allowed on credit like `start`, or `start`
should refuse for the same reason `open` does.

**2. Finishing a project earns you nothing, and the tutorial never says so.**
`help` names "the four to start with" — state, available, why, step. `open` is not among them
and is not mentioned in the intro at all. I built three concerns, watched the year tick over,
and could not work out why my income had not moved. The completion line does say
*"You know how; nothing is earning yet - 'open X' to run it"*, but it scrolls past in a block
of other events. And `policy auto_open` — which fixes the whole problem — ships **off**.
Combined with problem 1, the default configuration walks a new player straight into a debt
spiral. `auto_open` on by default, or `open` in the "four to start with", would fix it.

**3. `policy auto_hire on` quietly destroyed my economy.**
Its whole description is "grow the staff toward what you can house and pay". What it actually
did was fill all 22 of my household places with **scholars** at 625 den/yr while my
**artisans** fell from 6.0 to 0.03. Artisans are what supervise concerns, so 22 concerns shut
themselves down and my net went from **+8,010/yr to −3,027/yr** in six years. The automation
optimised for nothing I could see and starved the exact resource my income depended on. It
should at least defend the staff that keeps running concerns running, and its description
should say what mix it will hire.

**4. The supervision rule is the most important mechanic in the game and is documented in one
sentence, in the wrong place.**
"Most concerns want CRAFTSMEN to keep an eye on them" appears only as a note at the top of
`ventures`. It is not in `help`, `help labour`, or `help economy`. Yet running out of free
craftsmen is what closes your concerns, and it happened to me over and over:

> `EVENT 179: nobody left to keep an eye on 15 concerns, so cn_gypsum_plaster, cn_stone_polish,
> collegium_licensed, freedman_staff and others closed.`

Related and worse: because staff attrit at 3.5%/yr and plagues take 12% at a stroke, keeping
concerns open means re-typing `hire artisan 40` every few turns for four hundred years. That
is not a decision, it is a chore.

**5. Contradictory scholar-cap messages.** With 210 scholars on staff, `why
point_contact_transistor` told me:

> `STAFF NEEDED: 25 scholars, 20 artisans   (you have 210, 518.8)`
> `!! 25.0 wanted, and literacy here will never supply more than 6.4.`

and `hire scholar 5` said:

> `this society's literacy will not supply more than 6.4 scholars in total, ever, at any price,
> and you have 61.0 ... There is no room for even one more.`

"Never more than 6.4, and you have 61" is nonsense on its face. Either the ceiling is stale
(it should have risen with printing_press, rag_paper, school_founded, academy_network) or the
figure printed is a different quantity from the one it is being compared against. Twice this
made me think I was blocked from the goal when I was not.

**6. I never worked out what `open` does for a work that earns nothing.**
`ventures` lists patron_local, identity_cover, workshop_first, school_founded, collegium_licensed,
freedman_staff and a dozen others under "YOU KNOW HOW, AND HAVE NOT OPENED" with
`EARNS/YR 0` and `COSTS/YR 200–2,500`. When they closed for lack of supervisors, my protection
stayed at 92% and my household places stayed at 48.8. So paying to open them looked like pure
loss, and I ignored them for two centuries with no visible penalty. If opening them matters,
say what it buys; if it doesn't, don't list them as concerns.

**7. `available <anything>` always dumps the same 25-line "HEARD OF, CANNOT BEGIN YET" block.**
Even `available electricity` (whose blocked list was mostly farm machinery), even a search
that matched nothing at all. Every single query cost a screenful of the same irrelevant text.
It should be filtered to the subject or the search term, or hidden behind its own command.

**8. Saves are dumped in the project root.** Starting a game wrote `rome_100ad_81.json` into
the top-level directory — alongside eighty other people's `rome_100ad_*.json`. A saves folder,
please.

**9. One start crashed outright** before printing anything:
```
File ".../rome/sim/engine/core.py", line 1236
    self._resync_pools()
IndentationError: unexpected indent
```
Re-running the identical command worked. From the player's chair the game just randomly
refused to launch.

**10. Small stuff.** After "THE RUN IS OVER", *every* subsequent command reprints the entire
victory block — `why patron_local` gave me four lines of tech and then thirteen lines of
end-of-run summary. Also: `state`'s header says `sch 0 art 0` while `why <id>` on the same turn
says "you have 1, 0" (the founder counts as a scholar in one and not the other). And year one
printed `COMPLETED 100: Amphitheatre with tiered seating` / `Barrel vault` for things I never
started, formatted identically to my own completions.

---

## What was genuinely good

- **The writing.** The five civilisation blurbs, the arrival text, the hazard essays (the one
  on Diocletian's Price Edict and hereditary collegia is better than most textbook paragraphs)
  and the little historical asides inside `why` are excellent. "Sejanus was the most protected
  man in Rome until the morning he was not" is a better explanation of the eminence mechanic
  than a formula would be.
- **The economics are legible.** `money` itemises every concern's revenue and the rows really
  do sum. `stuck` answers "why am I not getting on" in four lines and was right every time.
- **Refusals explain themselves properly.** I twice accused the game of failing silently and
  was twice wrong — it had printed a precise reason and I had scrolled past it:
  "you can feed, house and oversee 1.78 more people, and teaching 2 would make 2. Teach 1
  instead." That is a model error message.
- **Constraints that aren't money are the interesting ones.** "waiting on the pace it can
  absorb money: at most 470 a year goes into this. Money in hand cannot buy it down faster."
  "started, but this society cannot supply the labour it wants and it will crawl until you
  can: chemist (wants 1500 hours a year; this society can field 1139 at most)." Excellent.
- **Hedging hazards feels great.** Building germ_theory + sanitation before 165 AD turned the
  Antonine plague from −28% staff into −12%, and the event line *told me the counterfactual*:
  "(would have been -28%: boiled water, handwashing, clean wounds...)". Later,
  `corpus_dispersed` visibly stopped the 3rd-century sackings from eating my tech tree, after
  I had already lost 25 technologies to them. Learning that lesson the hard way was the best
  moment in the run.
- **Fog of war works.** "HEARD OF, CANNOT BEGIN YET" with a per-item reason — "needs 2 trained
  scholars, you have 1.0 (you are one of them)", "this needs a catalyst and you have none of
  the things that would serve: any of mat_nickel would do" — gave me exactly one step of
  visibility and made the whole 500 years feel like exploration rather than a checklist.
- **The endgame chain is beautifully specific.** zinc → flue dust → germanium concentrate →
  GeCl4 → reduction under hydrogen → zone refining → Czochralski → transistor. Finding that
  the last thing standing between me and the goal was *one* missing node called `single_crystal`
  was a real moment.

---

## Log (chronological)

### Opening
- Menus (civilisation / starting wealth / mortality / fog) are clear and well written.
- The goal is only revealed by typing `help`: "Build point-contact transistor, before the
  horizon at 600." The intro text never states it. `state` says "Aiming at: Point-contact
  transistor" but not the deadline. Put both in the arrival screen.
- 400 den, +3.5 den/yr net. The opening is genuinely tight and that is good.

### 100–110: bootstrapping
- Started cheap high-ROI concerns (toys and dolls, guano, umbrella; then horizontal loom,
  indigo, fish curing, hopper wagon). Went 1,600 into arrears because I did not know about
  `open`. See TOP PROBLEMS 1 and 2.
- Once opened: +2,025 den/yr. The turnaround is very satisfying.

### 110–140: institutions
- identity_cover → patron_local → citizenship → collegium_licensed → freedman_staff →
  school_founded, plus workshop_first for household places. The "HOW MUCH RESTS ON THIS:
  almost everything" line in `why` is what guided me; it is a good signal.
- `available`'s "MOST RESTS ON THESE" table was the single most useful screen in the game and
  is basically how I navigated 500 years under fog.
- auto_hire catastrophe here (TOP PROBLEM 3).

### 140–190: instruments
- cap_heat_1100/1300/1600, cap_tol_100um/10um, cap_vac_1torr/1e-3, cap_pure_2N/4N,
  balance_analytical, thermometer, barometer, micrometer_gauges, master_screw, screw_lathe.
- The "four things nobody can do" framing from the arrival text (measure temperature, hold a
  tolerance, sustain a vacuum, purify anything) pays off exactly here. Very satisfying.
- Antonine plague survived at −12% instead of −28% thanks to germ_theory/sanitation.

### 190–290: the third century nearly broke me
- Four separate sackings. 25 technologies forgotten. ~3M denarii taken. I had `corpus_written`
  but not `corpus_dispersed`, and the game told me so in the event text:
  "(the corpus was never printed and dispersed)". Fair, and it stung.
- Currency debasement took 73k/yr until `endowment_land` blunted it.

### 290–460: industry
- printing_press → literacy → more scholars; dynamo → motor_transformer_ac → transformer →
  substation → power_grid → electrolysis_industrial → aluminium.
- Deputies ("you now have 11 deputies directing work in your name: your year is 21,964 hours
  instead of 2,000") are a lovely, well-signposted escalation.
- Long chains have to be started one link at a time with a `step` between, because a start is
  refused if its prerequisite is merely *in progress*. I lost about 20 years to guessing wrong
  about how long a link would take. A queued `start` (or `start X --when-ready`) would help.

### 460–583: semiconductors
- quantum_solidstate_theory, cap_pure_6N, vacuum_tube, then the germanium chain.
- Won in 583.
