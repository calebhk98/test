# Playtest findings, and what was done about them

One row per finding that changed the code or the documents. Countries are played
one at a time, three testers each: one trying to win, one hunting bugs, one
being deliberately strange.

The rule for this file: a finding is only closed when the fix is verified by
reproducing the tester's exact commands. "Probably fixed" is not closed.

---

## Rome, 100 AD

### Fixed

| # | Finding | Severity | What was wrong | Fix |
|---|---|---|---|---|
| W1 | Buy people, free them instantly, get labour and reputation from money | EXPLOIT | `buy_slaves` added 0.55 artisans per person and `manumit` added another 0.55 for the SAME person. One human yielded 1.1 workers. | Manumission raises the same person 0.55 to 1.0, so it adds 0.45. |
| W2 | Flat price at any volume | EXPLOIT | 300 den each whether you bought 1 person or 3,333. | Price rises against local market depth. That purchase now quotes 43.9M and is refused. |
| W3 | Purchased people were productive instantly | EXPLOIT | Ten bought and freed became eleven trained artisans in the same tick, with no founder hours. It strictly dominated `freedman_staff`, which models the same thing at 900 founder hours and two years. | Three year training lag before they count. |
| W4 | Manumission reputation had no ceiling | EXPLOIT | Out-earned taking a patron. 240 people minted 96 reputation. | Saturates; the same 240 now yield 25. |
| B1 | **Money from nothing** | BUG, severe | `buy forest n:-5` returned `ok:false` and moved capital 400 to 1,650. Negative quantity made a negative cost, which passed the affordability test, credited the money, and only then reported failure. | One guard at the top of the dispatcher, before anything is touched. |
| B2 | **A malformed command killed the session** | BUG, severe | `{"cmd":"why","id":{"a":1}}` died on an unhashable-type TypeError and took the process with it, losing the whole game. Five id lookups had the same hole. | One central guard. A bad command costs you the command, never the game. |
| B3 | Money vanished with no explanation | CONFUSING | Capital fell 400 to 184 on the first step with nothing active and revenue and upkeep both reported zero. It was living cost, always charged, never shown. | `state` reports `living_cost`, `mine_operating_cost`, `net_per_year`, `training_pending`. |
| B4 | `step` silently no-opped after game over | CONFUSING | Indistinguishable from a working game that had stopped progressing. | Says so, and points at `state`. |
| W5 | The eminence mechanic was undocumented | CONFUSING | A tester was killed by "too eminent", went looking, and `grep -rn "eminen"` returned nothing across the whole knowledge base. The module listed exactly three ways to die and the game had four. | Fourth threat written up in `03_SOCIAL_POLITICS.md`, including that every other defence in that module is a shield and this hazard is caused by the shields working. |
| W6 | `done_count` credited players with work they had not done | CONFUSING | 139 "the society already has this" nodes complete in year one and were counted identically to earned ones. | Split into `done_granted` and `done_earned`. |
| N1 | **The protocol showed one graph while the guide insisted another governs you** | CONFUSING, the best finding of the batch | The WIN tester read the warning about the Third Century Crisis, then reasonably skipped the academies because `path` said, correctly, that no academy is a technical prerequisite of a transistor. They lost 25 technologies in one year, 24 nine years later, 16 after that. The risk existed only as prose, attached to the mitigation rather than to anything visible while deciding. | `state` carries `knowledge_risk`: technologies exposed, chance per sacking, fraction lost, expected number, current hedge, better hedge, and dated hazards ahead. |
| N2 | A staff wall halted everything and the refusal named the shortfall, not the remedy | CONFUSING | Staff is not a technical prerequisite so it never appears in `path`. The player had no way to discover the answer. | Refusals now name the nodes that produce scholars and artisans, and the buy-and-manumit route with its training lag. |

### Not fixed, with reasons

| Finding | Why not |
|---|---|
| `start` does not check affordability | Correct behaviour. Projects are paid progressively as they build, so starting something you cannot yet fund is legitimate and you stall if the money runs out. The complaint underneath was really B3, that you could not see it coming, and `net_per_year` answers that. |
| Negative capital has no bankruptcy floor | By design. Mines mothball automatically when you cannot pay, which is the safety valve, and the WIN tester marked that WORKS-WELL. |
| The founder never dies | The default is an immortal founder; `--mortal` turns it on. The briefing oversells survival as central, which is a documentation problem rather than a model one. |
| Calendar floors overrun by 2 to 4x | Reported as unconfirmed by the tester. Under investigation. Floors are minimums, and throttling by money, staff or materials legitimately extends them, but the size of the overrun deserves checking. |

### Results

| Role | Outcome |
|---|---|
| WIN | Reached the transistor in **458 AD**, 358 years, playing straight through the protocol. The optimizer's median is 348 to 363, so a player choosing their own path does about as well as the planner. That was the single most reassuring result of the batch. |
| BREAK | Two severe bugs, two transparency bugs, and four things it attacked hard and could not break. |
| WEIRD | One compound exploit worth four fixes, plus the undocumented death. |

### A note on process

The first WIN attempt was killed by a rate limit and produced no report at all,
while its parting message claimed it had reached the transistor in year 226.
That claim was discarded rather than reported: no file existed, and 126 years
would have been three times faster than anything recorded. Every tester since is
told to write the report file FIRST and append as it goes.
