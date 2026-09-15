# Society and Economy: *The Long Way Home* (book_v5) vs. the Rome simulator

Scope: social, political, and economic mechanisms only. Narrative pacing and technical/engineering
feasibility are covered by other researchers and are out of scope here except where they bear
directly on a social or economic point (e.g., why a technically working invention fails to spread).

Method: read `book_v5`'s planning documents (`CHAPTER_SUMMARIES.md`, `FINANCE_MODEL.md`,
`V2_DANIEL_FINANCES.md`, `bible/05_world_rules.md`) for the intended model, then read primary
chapter text (ch01, ch09, ch17, ch20, ch23, and more below) to verify what's actually on the page,
since planning docs and prose sometimes diverge (the finance docs flag their own internal
reconciliation in `FINANCE_MODEL.md` §7). Compared against `rome/knowledge/03_SOCIAL_POLITICS.md`,
`rome/04_ECONOMICS.md`, `rome/data/civilizations/*.json`, and live runs of
`rome/sim/simulator.py agent --civ rome_100ad`.

Status: **in progress, written incrementally.** Sections below are filled in as research completes.

---

## PART 1 — THE BOOK

### 1. Money: how Daniel gets it, what life costs, what pays first

**Start state (ch01, `book_v5/chapters/ch01.md`):** the protagonist (Danny/Daniel Mercer, 17)
arrives with nothing convertible — "like forty bucks" in a bank account eighteen centuries away,
a phone at 98% that's dead by day three-four (`bible/05_world_rules.md` §2), and the clothes he's
wearing. He is captured within hours and is a prisoner, then a slave, for the next several years —
he does not choose his first "employer"; he is bought (ch03-ch04: an official has him drawing maps
under interrogation; a freed physician, Heras, examines and begins teaching him; by ch04's end he's
moved from a cell to a workshop loft as an owned curiosity, not a free economic actor at all).

**The actual first thing that "pays" is not a technology — it's proof of unique, undismissable
utility to a man who already owns him.** Chapters 5-8 are unmonetized (he is Heras's — and,
unbeknownst to him for a year, Macer's — property; nothing he produces in this period is *his*
money in any legal sense). The hot-air balloon (ch05-ch08) is the first "product," but its payoff
is not a wage or sale — it's a status change: it forces his owner, Titus Flavius Macer, to
introduce himself and renegotiate terms (ch09). That is the book's real "first payday": not a
transaction, but being upgraded from disposable curiosity to a **managed asset with a peculium**.

**The peculium (ch09, `book_v5/chapters/ch09.md`):** Macer's deal is explicit and stated on the
page — cloth by the bolt, two slave assistants, a walled yard, materials "on account" verified by
the steward, and "a fund. A peculium," with Macer's own gloss: *"It is not yours. A clever master
lets a clever slave keep a little jar because a man guarding his own jar guards the master's whole
house and never notices he is doing it."* Daniel has no legal claim to any of it; it exists purely
because it is in Macer's interest to let him think he has money. This is the book's core economic
claim about the era: **for an unfree person, "earning" and "being permitted an allowance by your
owner" are the same act**, and the book is careful never to blur that line rhetorically even as it
lets Daniel use the peculium exactly like working capital.

**What actually turns into real (if still owner-mediated) money:**
- The **military contract** for a man-carrying balloon (ch11): 80,000 HS to Macer, 40,000 direct
  to Daniel, a 10,000 HS holding fee — the first hard number in the book, and Daniel opened low
  (12,000) against an implied 40,000+ ceiling, which the finance docs flag as "the leverage
  lesson." Even this money is not fully his — it flows through Macer.
- A **quietly run gambling/bookmaking operation** on chariot races (mentioned ch08, expanded
  ch19), exploiting Daniel's knowledge of implied probability/odds-setting for a guaranteed
  margin — notably a form of income that requires no technology transfer at all, just statistical
  literacy Rome doesn't have. This is one of the book's few "pure arbitrage on knowledge" income
  sources.
- **Hindu-Arabic numerals** spread virally and for free (ch16: "Arabic numerals have already
  spread through Rome's merchant class without his direct involvement... because they made fraud
  harder to hide") — the book is explicit that Daniel does *not* successfully monetize his most
  consequential invention directly; it leaks out and becomes a public good, and only later
  generates money indirectly (via the printing press selling arithmetic sheets, ch16, and later
  the imperial paper/numerals contracts).
- **The printing press + rag paper + the literary/invention contest** become the visible, famous,
  long-run engine (ch10, ch16, ch19 onward): cheap printed sheets, a prize competition that
  doubles as an unpaid R&D pipeline (people submit invention ideas for a prize; if useful, Daniel
  extracts the technique).
- **Manumission money is the real inflection point.** Emperor Trajan buys Daniel from Macer and
  immediately frees him (ch17) — he does not buy his own freedom; he is bought *and freed in the
  same transaction* by the one buyer with essentially unlimited funds. Only after this (as an
  imperial freedman, *Marcus Ulpius Danihel*) can he hold property, make a will, or own slaves in
  his own name — i.e., only after this point does "his" money legally exist at all.
- Later streams (steel, gunpowder/cannon as secret state monopoly, water filtration, a steam mine
  pump, kerosene, eyeglasses, coal-gas lighting) compound over decades; see `FINANCE_MODEL.md` for
  the full ledger (below).

**Cost of living / scale, per the planning docs (`V2_DANIEL_FINANCES.md` §1, cross-checked against
`FINANCE_MODEL.md`, which explicitly corrects some of `V2_DANIEL_FINANCES.md`'s numbers — see its
§7 "Reconciliations"):**
- Unskilled laborer: 1,000-1,500 HS/yr. Skilled artisan: 2,000-4,000 HS/yr. Comfortable
  merchant/officer: 5,000-15,000 HS/yr. Equestrian census minimum: 400,000 HS net worth. Senator:
  1,000,000 HS net worth.
- Daniel's liquid worth at ~26 (ch20) is stated on the page as **"forty thousand was most of
  everything I had"** — spent almost entirely on buying and freeing Tyche (38,000 HS) plus
  Pamphilus (4,000 HS, ch18). `FINANCE_MODEL.md` explicitly flags and overrides
  `V2_DANIEL_FINANCES.md`'s earlier claim of "150,000-300,000 HS at age 21" as inconsistent with
  this on-page number, and resets the trajectory to match the lower, on-page figure. **This
  matters for the comparison below: the finance planning documents were themselves audited against
  the prose and corrected downward once — the book's economic "ground truth" is the prose, not the
  spreadsheet.**
- One clean anchor late in the book: Marcia states the press cleared "a little over two hundred
  thousand sesterces last year... Clear, after Eros and the paper and the rent and the prize money
  and the priest's portion and the two men I had to pay to forget a cart at the wrong dock" (ch38,
  per `FINANCE_MODEL.md` §5) — note that "bribes/protection" is a *named, budgeted line item in an
  ordinary business's accounts*, not an exceptional event.
- Terminal wealth at death: 50-100M HS (Pliny-the-Younger-plus tier), built on ~4 compounding
  "monopolies" (press, mine drainage, gunpowder/cannon, balloon supply) each protected by secrecy
  or sole know-how rather than by law (Rome has no patent system Daniel can use — see §3 below).

**Verdict on money:** the book's economic arc is not "clever guy invents things and gets rich." It
is "an unfree person's first economic problem is that he owns nothing, including his own output,
and every subsequent stage of wealth is gated by a *legal status change* (peculium → contract money
still routed through an owner → manumission → citizen able to hold property) before it is ever
gated by having a good idea." The ideas are almost the easy part; the legal personhood is the hard
part. The book is also consistent that Daniel personally never tracks his own net worth — Tyche and
later Marcia do — which is itself a social/gender claim (see §2 and §6).

---

### 2. Labour: how Daniel gets people to work, and how he gets skills that don't exist as trades

The book never lets Daniel simply "hire" his way to a workshop. Every worker relationship is one
of a small, named set of Roman labor institutions, and the book is explicit that these are legally
and socially distinct categories, not interchangeable "employees":

- **He is himself unfree labor for the first ~5 years.** He starts as a prisoner (ch02-03), passes
  to Heras's household as a curiosity (ch04), and is legally Macer's slave from before ch07 (we
  learn only in ch07/09 that Heras had been fronting him to Macer all along) until Trajan buys and
  manumits him in ch17. Everything he "builds" in that period is legally his owner's.
- **Slaves assigned to him by his owner** (ch09-10): Macer gives him "two slaves, mine, to fetch
  and stitch and not to run" — Pamphilus (a collared porter) and later others — explicitly *not
  gifts*: Macer states he'll sell the cleverer one if Daniel makes them too valuable. This produces
  the book's central labor-secrecy problem: Daniel must hide Tyche's mathematical talent for five
  years (ch05-ch20) specifically because visible skill in an owned person is a liquidation risk to
  a third-party buyer, not a promotion path.
- **Free hired labor, paid in coin**, appears early and is treated as unremarkable: "free women to
  sew seams" (ch10) is the first wage labor Daniel directs himself, notably *not* slaves — the book
  uses this to show that free wage labor is available in Rome for piecework even to a low-status
  foreigner, it's just not the default for a wealthy man's core workforce.
- **Manumission-into-clientage, not manumission-into-freedom.** Both times Daniel frees someone
  (Pamphilus ch18, Tyche ch20) the book insists the freed person doesn't actually become
  economically independent — they become his *client/freedman*, bound by *obsequium* in the Roman
  sense even if the prose doesn't use the word. Pamphilus's first free act is to ask "You free... 
  You don't have to cut anything... Go where?" and returns to cutting cloth for wages because a
  freedman with no family, capital, or trade literally has nowhere else to go. Tyche is the sharper
  version: she is bought (38,000 HS, nearly all Daniel's liquid wealth) and then dictates her own
  terms on the spot — real wages, no peculium-fiction, her name kept off every contract of his (to
  avoid the "kept woman" reading Rome will otherwise assign to an unmarried freedwoman living in
  her manumittor's household, ch20), a lockable room, a prompt court date for full citizenship —
  a negotiation the book stages as the freed person correcting the terms of her own liberation,
  which the free man had unilaterally decided for her "for her own good."
- **Apprenticeship** appears late and explicitly, once Daniel has capital: a twelve-year-old
  apprentice, Vitalis, learns block-cutting under the aging letterer Eros (ch39) inside a formally
  chartered *collegium* Marcia builds specifically so the press survives Daniel's death — i.e.,
  apprenticeship shows up as **succession planning**, not as a hiring convenience.
- **Skilled free professionals bought as partners, not employees.** Marcia (ch22) is the clearest
  case: a self-made freedwoman running a warehouse, who diagnoses every leak in Daniel's business,
  refuses a wage, and takes an equity-like partnership share instead, "wanting in early before men
  of rank notice its value" — later becoming his wife for openly stated legal/economic reasons
  (joint estate protection, freeborn heirs).
- **How he gets skills that don't exist as trades yet:** the book's answer is consistently *pay a
  master craftsman to co-develop against Daniel's incomplete theory, and expect failure*. Crucible
  steel with the smith Hermes (ch15) fails on the third batch because Daniel can supply the
  *concept* (carbon, sealed clay, full melt) but not the *numbers* (how much carbon, how hot, how
  long) — the craftsman's hands and the foreigner's theory are both necessary and neither is
  sufficient alone. The clock escapement (ch23) is the sharpest statement of this: Daniel has
  *watched* an escapement in a documentary a hundred times and still cannot describe its geometry
  to Hermes ("What does it look like, in your country, the part that quarrels?" — Daniel has
  nothing) — the book is making an explicit claim that knowing a technology exists is not remotely
  the same as being able to specify or transfer it, and that the craftsman without the concept and
  the visionary without the craft are both stuck. The book's late-game institutional answer to "how
  do you manufacture a whole missing science" is the **patronage/prize fund** (ch39): pay craftsmen
  "to fail systematically at hard problems" — i.e., convert his own inability to derive the answer
  into a standing bounty on it, then let the empire's whole population of specialists compete for
  the payoff (this is also his innovation-adoption mechanism, see §5).
- **Skills transfer down through a private "keeper chain," not a market.** Because his most
  dangerous and valuable knowledge (the full English-language science books, ch40) can't be sold,
  taught publicly, or protected by law, it moves person-to-person: Tyche learns to read/write his
  English first (ch20), then three students at once — his daughter Ulpia, apprentice Vitalis, and
  a freed slave-girl Chloe (ch41) — an explicitly matrilineal, informally curated transmission line
  that the epilogue (ch51-52) shows surviving him by generations, teacher to student to student,
  entirely outside any guild, school, or state institution.

**Verdict on labour:** the book treats "labour" as inseparable from *legal status*, exactly as it
treats money. There is no unified labor market Daniel can simply post a job to; there are five or
six distinct, non-interchangeable relationships (owned-slave-assigned-by-master,
free-hired-piecework, freedman-client-on-wages, apprentice, equity partner, private knowledge-heir)
each with different obligations, different risks to the worker, and different visibility
constraints, and the book's driving tension in this domain is that **making a person's labor
visibly valuable while they are still unfree is dangerous for the person**, not a triumph.

---

### 3. Political danger

The book models political danger as a layered, largely non-violent, reputational and legal system,
with four recurring threat-vectors that recombine across the book:

1. **Eminence itself is the danger, independent of wrongdoing.** The balloon's first public flight
   (ch08) immediately makes Daniel "a thing worth stealing or destroying" rather than a curiosity —
   Macer's very first words to him (ch09) are that being noticed by a senator's freedman is *worse*
   for Daniel than the roof fire he caused. Visibility is consistently treated as the primitive
   danger that everything else (accusation, patronage, extortion) is downstream of.
2. **Patronage is protection that is simultaneously a leash and a liability.** Scaeva (ch25)
   explicitly trades a favor (fixing a customs shakedown) for reconnaissance on Daniel's supply
   chain and a future claim on the gunpowder/cannon technology — patronage in the book is never
   free, and the patron's protection evaporates the instant the patron's own risk calculus changes:
   Scaeva silently drops Daniel the moment the political wind shifts against Trajan's men (ch33,
   "the senator is not receiving this morning"), demonstrating that a patron's promise is only as
   durable as the patron's own safety margin.
3. **Formal legal/religious accusation — impiety.** Crispus's charge (seeded ch16, ch26, formal
   hearing ch27) is the book's model of how an autocracy without free speech law actually
   prosecutes an inconvenient public figure: not for the technology (fraud charges don't stick once
   the balloon/filter demonstrably work), but for the *meaning* attached to it — a children's prize
   story about a "ladder to heaven" reachable by human works is reframed as a claim that gods are
   unnecessary. The hearing (ch27) is resolved not by evidence or argument but by which senator
   "leans" in the room (Scaeva's unsolicited intervention tips it), and the "victory" itself costs
   Daniel three things simultaneously: the priestly college gets permanent ritual oversight of his
   press/contest, Scaeva now has a public, undeniable claim on him, and Vibenius (the haruspex) is
   owed an unspecified debt. **The book's clear thesis: winning a political/legal confrontation in
   Rome does not remove the danger, it just re-denominates it as a debt to whoever saved you.**
4. **State succession crises are existential and arrive with no warning and no due process.**
   Trajan's death (ch30) instantly devalues Daniel's entire legal identity, because his citizenship,
   name, and protection all derived from one man's personal favor. Hadrian's accession opens with
   the extrajudicial killing of four ex-consuls on the Guard prefect's own authority, before the new
   emperor has even reached Rome (ch33) — the book is explicit that guilt or a trial were never in
   question; only *proximity* to the wrong faction mattered, and the killings are a pre-emptive
   purge to protect the incoming emperor's household, not a response to any actual plot. Daniel's
   own response — Marcia's "make him small" strategy (removing his name from contracts, running the
   business under her name, ch32-33), an unnamed informant/*delator* probing the press-house who is
   defeated only by boredom and hiding evidence behind a woman sitting on a basket (ch33) — is the
   book's model of the only real defense against a terror with no formal charges: invisibility,
   loyal subordinates who can lie fluently and calmly, and abandoning every earlier gain in
   *visibility* that had been the whole engine of his success.

**What actually protects him, ranked by the book's own demonstrated reliability:**
- Least reliable: **patrons** (Scaeva, Macer) — both explicitly state they will not spend their own
  safety on him (Macer, ch33: "I will not burn for you").
- Middling: **being useful to the state itself** (imperial contracts, the emperor's personal
  interest) — powerful but conditional on the *specific* emperor remaining in power and remaining
  interested (this is why Trajan's death is catastrophic and Hadrian's cold curiosity in ch35-36 has
  to be re-earned from zero).
- Most reliable, per the book: **deliberate invisibility maintained by people other than himself**
  (Marcia's fronting, Tyche's concealment of documents) — i.e., the protection that actually works
  is social/organizational, not political.

**What threatens him:** never brute force or open violence (no assassination attempt ever lands on
Daniel directly) — always reputational/legal/administrative mechanisms: an accusation that can be
escalated to a court, a patron's withdrawal, a purge that catches him by proximity rather than
targeting, and a spy sent to quietly build a paper trail (ch33).

---

### 4. Historical events, and how Daniel handles them

The book explicitly commits (`bible/05_world_rules.md` §8, "History bends") to keeping the real
historical timeline largely on schedule while showing measurable local divergence — Daniel is a
passenger on the big events and only a lever on specific, named details. The major hazards he lives
through:

- **First and Second Dacian Wars (ch11-14, ch18).** He is dragged into the first as *property on
  loan* to a military tribune (Celer) — his objections to flying an untrained volunteer in bad wind
  are overridden precisely because "the no of a slave is a sound and not an event" (ch26) — and the
  volunteer Sabinus dies. Daniel's personal response is a private vow never again to put an
  untrained person into an untested design "because he was told to," which the book then makes him
  *keep in letter but arguably break in spirit* by the second war (ch18): he builds the design past
  the point of failure and flies trained volunteer crews at the siege of Sarmizegetusa, and uses his
  water/sanitation expertise to *locate and deliberately foul* the besieged city's water supply,
  breaking it from within (the same knowledge that saves Roman soldiers from the flux is used, on
  his own explicit recommendation, to kill a city by thirst). He has no illusions about this: "I
  read the slope. I said cut here... I chose to live, and I am not calling that a moral act."
- **Trajan's Parthian campaign (ch28-29).** Presented as imperial overreach the book flags via
  Celer's line "out of world or out of us" — Daniel is co-opted simultaneously as camp
  sanitation/medical expert *and* as an unwitting intelligence asset through Scaeva's pre-arranged
  officer contacts, a leash he cannot refuse. Celer dies of a septic sword wound Daniel's
  antisepsis knowledge cannot cure once infection reaches the blood — the book's explicit statement
  of the ceiling on Daniel's medicine: he can prevent infection, not cure sepsis.
- **Trajan's death (ch30) and Hadrian's accession (ch30-33).** The single biggest political shock
  in the book — see §3. Daniel's coping mechanism is pure damage control: race home, go quiet,
  let Marcia rebuild his legal footprint under her own name.
- **The Bar Kokhba revolt / Judaea (ch45, dated to the 130s).** Handled entirely retrospectively,
  through an accounting audit rather than a battlefield scene — see §6, the book's most direct
  statement of complicity as a historical-event response.
- **Later, off-page but consequential: the Antonine Plague, ~15-20 years after Daniel's death**
  (ch49) — he pre-empts it not by preventing it (he can't; it's after his lifetime) but by handing
  his quarantine protocol to his physician successor Zoticus in advance, the book's clearest
  statement that his only real lever on history is **institution-building that outlives him**, not
  personal intervention.

**Pattern across all of these:** Daniel never *prevents* a historical hazard. He either (a) is
overruled and absorbs the human cost (Sabinus), (b) is deputized as an instrument of the hazard and
made complicit in making it more effective (the Dacian siege, the Judaean bombards), or (c) survives
a hazard by disappearing until it passes (the succession terror). The book never once lets personal
cleverness neutralize a large historical/political event — only small, local, or long-delayed
effects bend at all, exactly as `05_world_rules.md` specifies.

---

### 5. Technology adoption: who has to be convinced, who resists, who loses their living

The book is unusually disciplined about **not** letting "it works" imply "it spreads." Concrete,
contrasting cases:

- **Numerals spread virally, for free, without Daniel's involvement or control** (ch16) — the book
  identifies the actual adoption mechanism explicitly: merchants adopted them because "they made
  fraud harder to hide," i.e., the numerals won not because they were more efficient in the
  abstract but because they solved a *trust/verification* problem for the specific people who
  handled money. Adoption, in this one case, required convincing no one — it was self-propagating
  once visible, and Daniel gets essentially none of the economic upside directly (§1).
- **The rail line is the book's central counter-example, and the single most important adoption
  finding for the comparison below (ch23):** a technically flawless, cheaply built demonstration
  (4 men on rails moving what took 26 men on rollers) is rejected by its target buyer, quarry owner
  Maximus, for a purely economic reason stated on the page by Marcia: *"You own the men, Maximus...
  The rail saves labor. You have labor to burn, bought and fed and going nowhere. What you are
  short of is iron and silver."* The people whose labor the invention would obsolete (the chained
  stone-hauling coffle) are not fired or retrained — the invention simply never gets bought,
  because the "labor cost" it would save is a sunk, already-paid cost to the owner (a slave, once
  purchased, is a near-zero marginal cost vs. a wage laborer). **The book's explicit claim is that
  slavery doesn't just compete with labor-saving technology on cost — it makes a chunk of
  labor-saving technology economically irrational to adopt at all**, regardless of quality. Nobody
  "loses their living" here because the technology never launches; the workers stay enslaved
  instead.
- **The prize contest as an adoption/extraction mechanism** (ch10, ch16, ch19, ch26, ch39): rather
  than selling a finished invention into a market, Daniel posts a *specification* (a clarity
  standard for glass, a bronze cylinder tolerance, a steel-heat color table) as a prize, and lets
  the empire's existing craft specialists compete to solve it on their own dime, paying only the
  winner. Crispus's late, most dangerous accusation (ch26) is not fraud but a structural critique:
  *"You are farming it. The knowledge... you pay only the one who arrives. No one bears the full
  cost. You bear none of the failures... The bronzesmith does not own his knowledge after that. You
  do."* This is the book's most sophisticated statement about adoption: the *guild system itself* is
  the resistance, because guild knowledge is proprietary-by-tradition (a master's knowledge is what
  makes him a master), and Daniel's prize mechanism systematically strips that knowledge out of the
  guild and into his own hands/presses, which is a real and correctly named harm to the guild
  structure even though no individual craftsman is worse off in the moment (they're paid).
- **Steam-rail power for slave-owning industry only becomes economically viable once the mine
  labor changes character** — the finance planning docs (`FINANCE_MODEL.md`) make explicit that the
  steam pump succeeds commercially specifically because it's sold as a *service* draining a mine
  nobody can currently work at all (a flooded gallery, zero competing labor cost), never framed as
  a labor-replacement sale to an owner who already has cheap hands, learning directly from the
  rail failure.
- **Resistance from the literate/priestly class is about status and cosmology, not technology per
  se** (ch16, ch26-27): Crispus's attacks evolve from "your geography is fraudulent" (easily
  disproven) to "your invention contest strips craft guilds of their knowledge" (structurally true,
  unanswerable) to "your children's prize story teaches impiety" (unfalsifiable, and the one that
  nearly kills him) — the book's arc suggests that as a technology's *practical* case becomes
  undeniable, resistance migrates from technical/fraud objections toward cosmological/status
  objections that are immune to demonstration.
- **Who loses their living, on the page:** the book is honest that this is mostly *not shown* —
  the stonecutter's chained coffle keeps hauling by hand because the rail never launches; there's no
  scene of guild scribes or abacus-users displaced by numerals (the abacus-using freedman quietly
  loses status, not income, in ch17's demonstration); Crispus is a rhetorician/man-of-letters whose
  *social standing*, not income, is what's actually threatened by Daniel's press. The book's honest
  gap is that it mostly shows resistance from people with status to lose (priests, rhetoricians,
  guild-pride smiths) rather than showing the ordinary laborer actually thrown out of work by a
  successful adoption — because in the book's own logic (the rail chapter), a slave society mostly
  doesn't *let* labor-saving technology reach the point of displacing anyone; it gets filtered out
  economically before it can.

---

### 6. Social failure, not technical failure

The book is careful to distinguish "the invention didn't work" (clock, spyglass — ch23, technical)
from cases where **the invention worked and Daniel still lost**, which are more interesting for
this research brief:

1. **The rail line (ch23)** — covered fully in §5: correct engineering, correct demonstration,
   total commercial failure because of who owns the alternative labor. This is the book's cleanest
   "social, not technical" failure and is explicitly framed by Daniel himself as heavier than his
   technical failures: *"I built a clean, true, simple machine that took the killing labor off
   men's backs, and it lost, fair and square, in the open court of arithmetic, to the plain fact
   that a man already owned the backs."*
2. **The fire-safety ordinance (ch18)** — Daniel writes a complete, correct municipal fire-code
   proposal (cistern spacing, bucket crews, a night watch) after a fatal tenement fire, and a
   magistrate hears him out "courteously" and does nothing, because the burned block's absentee
   owners are two senators and an equestrian: *"I would be very interested if any of those men were
   interested."* A purely social/political veto on a purely technical/administrative fix, with no
   technology failure anywhere in it — the bottleneck is entirely about who owns the property that
   would bear the cost.
3. **Buying and freeing Tyche (ch20)** is technically flawless (Daniel has the money, the law
   permits it) and socially catastrophic in the execution: the town instantly reads it as a kept-
   mistress arrangement ("Buy her a comb"), Daniel is shown to have spent five years making
   Tyche's competence invisible "for her own good" without her consent, and her own verdict — "You
   decided I'd be slow. For my own good. And now you've decided I'm free. For my own good."
   — reframes his entire protective strategy as a paternalism failure, not a legal one.
4. **The fire-flight vow and its erosion (ch13 → ch18)**: not a reversal exactly, but the book
   stages Daniel's own moral reasoning eroding under sustained institutional/military pressure —
   he keeps the *letter* of "no untrained pilots in untested designs" by making the design good
   enough, while quietly abandoning the deeper spirit of "I decide when people fly," which by the
   second Dacian war is entirely subordinated to military necessity and his own survival calculus
   ("I chose to live, and I am not calling that a moral act").
5. **Judaea (ch45)** is the book's most direct and devastating "social/moral failure" — not a
   scene of Daniel doing anything wrong in the moment, but a slow accounting-desk realization,
   staged entirely through ledger columns, that his numerals, surveying grid, sanitation, and
   bronze siege bombards were all direct instruments of Rome's destruction of a rebellious province,
   down to watching "the price of a human being fall down a column of my own marks" as the slave
   market floods with war captives. He explicitly refuses himself an exculpatory stopping point:
   *"the gap between knowing about walls and not-knowing about individual caves is the gap between
   a man who can be precise and one who has chosen a comfortable stopping point."* No technology
   failed here; his tools worked exactly as designed, for an end he cannot make himself unsee.
6. **Apollodorus's fall (ch37, summarized)** is a pure social/status failure adjacent to Daniel: the
   empire's best engineer is exiled and dies (cause never officially named) not for an engineering
   error but for publicly mocking an emperor's amateur architecture — Daniel's attempted
   intervention fails, and the lesson the book draws (via Daniel's own shame) is that he "bent" and
   Apollodorus didn't, and only one of them survived with his position intact.
7. **Ulpia's ceiling (ch38, ch41, ch43, summarized):** Daniel's daughter is demonstrably the most
   mathematically gifted person in the household by adolescence, and the book is blunt that no
   technology or wealth Daniel possesses can buy her a legal path to use it publicly — Marcia's
   argument that educating her fully is "a cruelty because no path exists for a freedman's daughter
   to hold a charter or run the business openly" is never resolved by invention; it's resolved
   (barely, generations later) by informal transmission chains (Tyche → Ulpia → Procula) entirely
   outside the formal economy.

**Ranked by how much the book leans on it as a thesis statement:** the rail chapter (slavery beats
a working machine on pure arithmetic) and the Judaea chapter (correct tools serving an end the
inventor can't consent to or withdraw from) are the two the book treats as load-bearing — they are
each given a full chapter, a named interlocutor stating the mechanism aloud (Marcia; Ulpia's
silence), and no narrative resolution or redemption. The others are important texture but are
resolved or absorbed into the ongoing plot.

---

## PART 2 — THE SIMULATOR

Read `rome/03_SOCIAL_POLITICS.md` (the model document), `rome/04_ECONOMICS.md`,
`rome/knowledge/03_SOCIAL_POLITICS.md` (the in-game how-to), and `rome/data/civilizations/
rome_100ad.json`; ran `python3 rome/sim/simulator.py civs`, `agent --civ rome_100ad [--fog]`, and
inspected `rome/sim/simulator.py`'s scandal/eminence code directly (read-only, no edits made, per
instructions — two other agents are editing it live).

**Premise, and the first major divergence from the book.** The simulator's player starts as *"a
modern person dropped into a pre-industrial society with the blueprints for everything up to about
1950,"* choosing a starting kit (`destitute` 0 den up to `rich_merchant` 20,000 den; default
`poor_scholar` = 400 den, "a few months' subsistence, a knife, a lens, a codex of notes"), and is
told outright: *"you arrive alone: No employees, no slaves, nobody who owes you anything. Anyone
who works for you is hired, taught, commissioned or bought."* Crucially, the sim's player **chooses
a plausible free identity** ("Recommended cover: a Greek-speaking natural philosopher and physician
of Alexandria... Never claim foreknowledge, divine revelation, or a new religion" —
`knowledge/03_SOCIAL_POLITICS.md` §2) and starts with immediate, monetizable expert knowledge — a
fresh `state` call on `rome_100ad` shows revenue of 233.5 den/yr from `med_cataract_couching` and
`med_trepanation` on turn one, with `done_granted: 137` techs already known. **The book's
protagonist has none of this**: no chosen cover story, no credentialed identity, no starting capital,
no starting technique he can monetize (he is a minor with no medical or scholarly training, and he
is a prisoner/slave for years before he has any economic agency at all). This is the single largest
structural gap between the two: **the simulator's whole model assumes the newcomer arrives as a free
person with a plausible elite-adjacent identity to inhabit; the book's whole first act is about what
happens when that assumption is false.**

**Money.** `{"cmd":"money"}` itemizes revenue by product, upkeep, wages, and `net_per_year`; capital
can go negative up to a `credit_limit` (interactively observed at 1,366.8 den against 400 starting
capital, i.e. roughly 3.4x starting capital, at 10.83% annual interest on arrears) — an explicit,
numeric answer to "what can a newcomer borrow." The book gives no equivalent number for an
enslaved newcomer (he has *no* credit standing at all; his "peculium" is entirely at his owner's
discretion, per §1 above) and only lets Marcia's ledger imply a credit-like structure much later.
Cost-of-living is charged automatically every year regardless of activity (`living_cost` 230
den/yr on the default kit) — matching the book's insistence that Daniel is billed for existing
(rent, food, appearances) whether or not a project is paying off, though the book renders this as
narrative pressure rather than a visible number until Marcia starts keeping books.

**Labour.** `{"cmd":"labour"}` and `{"cmd":"help","topic":"labour"}` state, almost verbatim, the
book's own taxonomy: *"Trades are NOT interchangeable: a smith is not a scribe, and a project
asking for an engineer cannot be built by smiths however many you have."* Four mechanically distinct
acquisition modes are modeled, mapping directly onto §2 of Part 1:
- `hire` — pay a market wage for an existing trade, every year whether or not there's work
  (matches the book's "free women to sew seams," ch10).
- `train` — teach a trade that does not exist in this society, spent out of the founder's own
  scarce `personal_hours` (interactively: training one engineer cost ~450 of the founder's 2,400
  annual hours and 25 denarii, with a 2-year lead time) — this is a precise mechanical analogue of
  the book's clock/steel-recipe problem (ch15, ch23): Daniel has the *concept* but must spend his
  own scarce time transferring it to a craftsman who supplies the *hands*, and neither one alone
  is sufficient.
- `commission` — buy a single finished job's worth of hours rather than a standing employee (the
  sim's version of the book's one-off contracted deals, e.g. Celer's balloon contract, ch11).
- `buy slaves` / `manumit` — explicitly modeled as a real, named mechanism, with the game's own
  voice stating it is included "because it was the ordinary condition of production in most of
  these societies, and a model that hides it lies about the cost of everything," and that
  manumission "is the decent thing" and also makes the freed worker perform and transmit knowledge
  better. `freedman_staff` (a chartered tech node, `rome/data/tech_tree.json`) formalizes this as
  "Buy, train and manumit a technical staff... a freed worker who remains literate and paid
  transmits knowledge onward; a coerced one does not... this is both the ethical and the efficient
  answer," costing 8 skilled slaves (~8,000 den) plus 2,000 den and granting +8 artisans on the
  player's permanent staff. **This is a near-exact restatement of the book's Tyche/Pamphilus arc**
  (buy → manumit → retain on wages as a loyal, literate, higher-output staff), but compressed into
  a single reusable game mechanic with no representation of the *individual* negotiation, coercion,
  or reputational cost the book spends two full chapters on (ch18, ch20) — see Part 3.

**Danger.** The state tracks four separate pools — `suspicion`, `scandal`, `eminence`,
`protection` — and the source code (`rome/sim/simulator.py`) makes an explicit, deliberate
distinction that maps closely onto the book's own layered danger model (Part 1 §3):
- `suspicion`/`scandal`: accrues from "every impressive, inexplicable thing you do" (`03_SOCIAL_
  POLITICS.md` §5: an unexplained demonstration of light/motion/sound = +12, an explosion = +25,
  being publicly right about a future event = +40), decays ~10%/yr, and **can be bribed down**
  (`simulator.py` line ~3363-3367: `auto_bribe` spends capital to reduce `scandal`). This is the
  mechanical form of Crispus's impiety accusation and the anonymous informant in ch33 — a
  legal/reputational threat that money and patronage can blunt.
- `eminence`: a *separate, explicitly unbribable* pool. The code comment is unambiguous: *"Eminence
  is its own hazard, and protection does NOT reduce it... You can buy a magistrate, an accuser and
  a jury. You cannot buy an emperor's judgement that you have grown too large, and the attempt is
  itself evidence against you"* (simulator.py, prominence_hazard/eminence block, ~line 886-909,
  3357-3401). It is driven by reputation² and wealth, and its worst outcome
  (`_catastrophe("too eminent...")`) is described in-code as being *"brought down not for what you
  built but for how large you had become."* Its milder rolls include: a 55% capital confiscation
  with a public withdrawal, or — **the single most precise mechanical echo of the book found in
  this whole research pass** — *"your patron is destroyed in someone else's quarrel and you lose
  [patron_senatorial/patron_imperial]"* (line 3394-3395). This is, almost verbatim, what happens to
  Daniel's patron Scaeva in ch33: Scaeva is not attacked *for* Daniel, but the political purge
  around him ends the patronage relationship anyway, and Daniel's protection evaporates as
  collateral damage of someone else's danger, not his own.
- `protection`: pools from patrons, citizenship, office, and money; explicitly reduces the danger
  multiplier from `scandal`/accusation-type threats, and explicitly does *not* touch `eminence`.
  `rome_100ad.json`'s civ-level weight `w_eminence_danger: 0.85` with the annotation *"An autocracy
  in which prominence is lethal: Sejanus, Seneca, Thrasea Paetus. The higher you rise the fewer
  people are above you, and every one of them is a threat"* is the sim's one-line version of the
  book's entire ch25/ch30-33 arc.
- The civ file's `notes` also independently states *"Manual work is socially degrading"* and
  *"Unlicensed associations are illegal: Trajan refuses Pliny even a fire brigade"* — the latter is
  cited in both `03_SOCIAL_POLITICS.md` and `knowledge/03_SOCIAL_POLITICS.md` as the reason a
  private, cross-provincial academy/collegium is `gov: -2` and cannot be built without senatorial
  patronage — a real-history precedent the book never dramatizes directly (Daniel's press/contest
  are folded into an *existing* license via the Minerva dedication, ch27, rather than being refused
  outright), but which sits squarely inside the same logic: unlicensed private organization is
  itself a suspicious act, independent of what it does.

**Historical hazards.** `{"cmd":"risk"}` surfaces the civ file's dated `hazards` array directly to
the player: the Antonine Plague (165-180, 28% staff loss, mitigated by "clean water, quarantine,
and eventually inoculation"), the Plague of Cyprian (249-262, same), the Third Century Crisis
(235-284, 16%/yr chance of a site being sacked, output factor 0.62, mitigated by "walls, firearms,
powerful friends, and copies of your work kept somewhere else"), and currency debasement (190-275,
mitigated by "metal you dug yourself, land, and a way to prove what a coin contains"). This is
structurally the same category of event the book dramatizes (succession crisis, purge, eventual
plague) but on a much longer, empire-scale clock — the sim is built for a 150-600 year "relay,"
while the book's Antonine-plague-adjacent event (referenced in ch51 as "the plague of Verus's
campaigns," i.e. the same Antonine Plague, ~165 AD) arrives only in the book's epilogue, decades
after Daniel's death, exactly matching the hazard's dated window in the civ file.

**Technology adoption / diffusion.** The sim models the book's contest mechanism directly as a
first-class economic instrument — `rome/04_ECONOMICS.md` §7, "Bounties: buying other people's
hours with money": *"The craft must already exist in the Empire, and the artisan must be able to
recognise success without understanding why it works... a smith can tell whether a plate is flat by
the marking. Neither needs your theory."* This is precisely Daniel's Macer Prize mechanism (ch10,
ch16, ch19, ch26, and Crispus's "farming knowledge" critique, ch26) — post a specification, let
existing craft specialists compete on their own dime, pay only the winner — down to the same
economic logic (price ≈ 2.5x honest cost, but zero supervision hours spent, +2 suspicion for being
conspicuous). The sim also independently reaches the book's central adoption-resistance finding:
`rome_100ad.json`'s `w_labour_saving: -0.6` (annotated "because of the Vespasian precedent and
cheap coerced labour") and `04_ECONOMICS.md` §6's explicit admission — *"Slavery is modelled far
too thinly. Roman labour is cheap partly because much of it is coerced, which suppressed the
business case for every labour-saving device in this document... compete where headcount cannot
substitute, which is precision, chemistry and optics"* — is the sim's own abstracted version of
exactly what happens to Daniel's rail line in ch23 (a technically correct labour-saving machine
that a slave-owner has no economic reason to buy). Notably, **the sim's authors flag this as the
weakest part of their own model** (a rare, honest admission that the mechanism is "thin"), whereas
the book dramatizes the same mechanism as a fully worked, specific, named scene — see Part 3.

**Observed bug (noted, not fixed, per instructions):** `{"cmd":"available"}` throws
`TypeError: Sim.start_reason() got an unexpected keyword argument '_memo'` whenever the agent is run
with `--fog` (fog-of-war mode). The same command works normally without `--fog`. `{"cmd":"why",
"id":...}` also appears gated by fog-of-war discovery state (it refuses to describe an undiscovered
node with "you have never heard of that... use 'available'"), which, combined with the `available`
crash, means a fog-of-war playthrough may currently be unable to see its own tech menu at all. Not
investigated further since two other agents are actively editing this file.

---

## PART 3 — COMPARISON

Ranked by how much each finding matters to the book-vs-simulator question, most important first.

### 1. [MOST IMPORTANT — the book's strongest finding the simulator does not represent at all]
**Slavery does not just compete with labour-saving technology on cost — it can make a technically
perfect invention economically irrational to adopt at all, regardless of quality, and the simulator
concedes it does not really model this.** The book gives this a full chapter (ch23) with a named
mechanism spoken aloud by a character (Marcia: *"You own the men, Maximus... What you are short of
is iron and silver"*) and a specific, irreversible outcome (Daniel tears out his own demonstration
line). The simulator's civ file assigns a single scalar penalty (`w_labour_saving: -0.6`) to the
*node's* government-interest score, and `04_ECONOMICS.md` §6 admits outright: *"Slavery is modelled
far too thinly... suppressed the business case for every labour-saving device in this document."*
There is no mechanic in the sim for "this specific buyer already owns the specific labour force
this specific machine would replace, so the sale fails even though the machine works" — the sim's
labour model is a market (hire/train/commission/buy-and-manumit) with a friction coefficient, not
a world where a large fraction of potential customers are *outside the market entirely* because
they already own free coerced capacity. **The book is more convincing here** — it derives the
failure from a specific character's specific asset position rather than a tunable global weight,
and it is honest that the invention doesn't fail to be *built*, it fails to be *bought*, which is a
sharper and more falsifiable claim than "labour-saving tech is disfavoured."

### 2. [Very close, arguably the best-aligned single mechanism] **Eminence as an unbribable,
patron-independent danger, distinct from accusation/scandal.** This is the strongest point of
*agreement*, not disagreement, between the two works, and it's worth stating plainly because it
could easily have been missed: the simulator's code deliberately separates `eminence` (unbribable,
protection does not reduce it, worst outcome is being "brought down not for what you built but for
how large you had become," and one specific rolled outcome is literally "your patron is destroyed
in someone else's quarrel and you lose him") from `scandal`/`suspicion` (bribable, reduced by
patronage and office). The book dramatizes exactly this distinction across two different threats:
Crispus's impiety charge (a `scandal`-type threat, resolved by Scaeva's patronage "leaning" in the
room, ch27) versus the Hadrian-succession purge (an `eminence`-type threat: four consulars killed
with no trial for being too prominent under the old regime, and Scaeva abandoning Daniel not
because of anything Daniel did but because Scaeva's own proximity to danger made the association
toxic, ch33). **Verdict: the two models genuinely agree, and the simulator's mechanical separation
of these two failure modes is arguably a cleaner articulation of the same idea the book only shows
by example.**

### 3. [Important, moderate divergence] **What a newcomer starts with.** The simulator's player
chooses a free identity and starting capital (0-20,000 den) and is productive from turn one. The
book's protagonist starts enslaved, with zero capital, zero chosen identity, and no economic agency
for roughly five years (ch01-ch09) before his first real negotiation (the peculium). This is not a
flaw in the sim so much as a difference in premise — the sim is explicitly a general-purpose,
cross-civilization "bootstrap a philosophy" toolkit (see `civs` output: it also runs Han China,
Mexica, Norse, and Plantagenet England) built around a player who *chooses* to be a philosopher of
Alexandria, whereas the book is telling one specific, harsher story about a teenager who arrives
with no say in the matter. But it means the simulator has **no representation of the book's central
early thesis: that for an unfree person, "earning" and "being permitted an allowance by an owner"
are legally identical acts**, and that skill visibility while still owned is a liquidation risk
rather than an asset (Tyche's five hidden years, ch05-ch20). The sim's `buy slaves → manumit` flow
starts *after* the purchase decision and skips the part of the book that argues purchase and
manumission are themselves fraught, individually negotiated, status-laden acts (Macer's "Buy her a
comb" scene, ch20) rather than a flat unit cost.

### 4. [Important] **What the book shows working that the simulator has essentially no
representation of: paternalism and consent as a labour-relations problem.** Buying-and-freeing in
the sim is a cost/output transaction (`freedman_staff`: 8,000 den for 8 skilled slaves, +8
artisans, better retention). The book's two manumission scenes (Pamphilus ch18, Tyche ch20) are
about what freedom is *worth to the freed person specifically* and whether the person who freed
them consulted them about the *terms* — Tyche's insistence on real wages, no peculium-fiction, a
lockable room, her name off every contract, and instruction in the one thing Daniel had kept
entirely for himself (his private script) is a negotiation over *dignity and consent*, not
productivity. Nothing in the sim's data model has a variable for this; a manumitted worker is
strictly better than a coerced one on the same axes (retention, transmission rate) with no
representation of the freed person having preferences that might conflict with the founder's plan
for them. The book's Pamphilus ("Go where?") captures a related, equally unmodeled point: legal
freedom without capital, family, or an alternative trade is close to freedom in name only, which is
consistent with the book's economics (§2 above) but is not something `manumit` in the sim can
express — manumission in the sim is a strict upgrade with no "and now what."

### 5. [Important] **Moral complicity of one's own successful tools — the book's Judaea chapter
(ch45) has literally no analogue in the simulator.** The sim tracks `gov_interest`,
`state_interest_trait_score`, and revenue for military nodes (gunpowder, siege engines,
surveying), and correctly flags gunpowder as `[risk 0.3, suspicion 25]` with an explicit
recommendation to withhold the corning step as a "survival card" — a good structural match to the
book's gunpowder-as-monopoly-and-liability arc (ch21, ch25, `FINANCE_MODEL.md`). But there is no
mechanic anywhere for the sim's player to *retroactively discover*, via their own accounting tools,
that their surveying grid, bombards, and administrative numerals were direct instruments of a
specific historical atrocity, and no mechanic for the private moral reckoning the book stages
entirely through a ledger (watching "the price of a human being fall down a column of my own
marks"). This is a one-directional gap: **the book does something the simulator has no
representational language for at all** — technology's use is tracked in the sim only as
revenue/suspicion/gov-interest, never as an ethically legible consequence the player is made to sit
with.

### 6. [Moderate] **Money.** Broadly compatible in structure (a founder who can go into debt up to
a multiple of capital, at a modeled interest rate; living costs charged whether or not you're
building) but not in magnitude or texture. The sim's numbers are denarii-denominated and scoped to
a *hypothetical, free* newcomer's opening balance sheet (400-20,000 den start, ~1,367 den credit
limit on the default kit). The book's numbers are sesterces-denominated and scoped to an *unfree*
person's decades-long climb (0 → "forty thousand was most of everything I had" at 26 → 200,000/yr
net at 46 → 50-100M HS at death), and the book is unusually disciplined about keeping the number
oblique and letting other characters (Tyche, Marcia) hold it, which the sim has no equivalent
for (the sim's `{"cmd":"money"}` hands the player the number directly, always). Worth noting in the
book's favor: `FINANCE_MODEL.md` records that its own internal financial projections were audited
against the prose and *corrected downward* once they contradicted an on-page number (§7 of that
document) — the book's economics were disciplined by narrative fact-checking in a way that gives
its numbers more integrity as a coherent system than a casual reader might assume from how rarely
they're stated outright.

### 7. [Moderate] **What the simulator models that the book never engages with.** Two clear cases:
(a) **empire-scale, multi-century hazards and knowledge-survival mechanics** — the sim's entire
"survival of knowledge" doctrine (`03_SOCIAL_POLITICS.md` §8: write it down in plain language,
print and disperse hundreds of copies across multiple climates, endow institutions in more than one
place, "teach method, not results") is a generalized version of what the book dramatizes for one
family/workshop lineage (the keeper chain, ch40-52) but the sim reasons about it at civilizational
scale (Alexandria-preserves-papyrus vs the West-preserves-nothing; the Third Century Crisis as the
real test of durability) in a way the book, being one person's biography, structurally cannot; and
(b) **direct resource ownership as a hedge (forest/coppice, mines) and the charcoal-vs-ore
ceiling on iron** (`04_ECONOMICS.md` §5) — the book never once has Daniel buy land or forest for
fuel security, relying instead on existing supply chains (Hermes's forge, Maximus's quarry), so the
sim's emphasis on owning your own fuel/mineral inputs against future disruption has no book
analogue at all.

### 8. [Minor but real] **Is Daniel doing something the simulator wouldn't let a player do, or vice
versa?** Two clean examples each way:
- *Daniel does something the sim's rules would flag as reckless or block outright*: flying an
  untrained pilot in an untested balloon design on a commander's direct order (ch13) — in sim
  terms this is deploying a `risk`-bearing, unmothballed project under external command with no
  founder consent, which the sim's model doesn't represent (the founder is always the one deciding
  whether to `start` a project); and publicly demonstrating germ theory / hygiene under a religious
  framing he privately disbelieves (ch27) is exactly the sim's own "recovery frame" advice
  (`03_SOCIAL_POLITICS.md` §2 — dress novelty as recovered ancient knowledge) but the book shows the
  *emotional cost* of sustaining a lie under interrogation by a professional (Vibenius) in a way no
  sim mechanic scores.
- *The simulator explicitly permits things the book's protagonist never even considers*: buying
  land/mineral concessions as a deliberate hedge against future supply disruption, and knowingly
  withholding a militarily decisive technology's *most dangerous refinement* (corned gunpowder) as
  a calculated "survival card" to cash in only if existentially threatened — Daniel in the book
  never manages his gunpowder secret this strategically; he backs into secrecy reactively (ch21)
  rather than banking it as a deliberate reserve move, and the book never has him treat any
  technology as a chip to be spent only at the moment of maximum need.

### Summary judgment

The two models agree far more than they disagree on the **shape** of danger (accusation vs.
eminence, patronage as leash-and-shield, suspicion decaying with normal behavior) and on the
**shape** of labour (hire/train/commission/buy-and-manumit as genuinely distinct, non-fungible
acquisition modes). Where they diverge is scale and texture: the simulator is honest about
modeling slavery's economic chilling effect "too thinly" and about having no representation of
consent, dignity, or retrospective moral complicity as game mechanics — precisely the three places
the book does its most serious work (the rail chapter, the Tyche negotiation, the Judaea ledger).
The book, in turn, has no equivalent of the simulator's civilization-scale, multi-century knowledge-
survival calculus, because it is telling one life, not simulating an institution across 500 years.
**If a reader wanted the simulator's abstractions made emotionally and causally concrete, the book
supplies exactly three scenes to point to: ch23 (labour-saving tech loses to sunk slave capital),
ch33 (a patron destroyed in someone else's quarrel, eminence not scandal), and ch45 (a ledger as the
site of moral reckoning) — and of the three, only the second has a real mechanical counterpart
already built into the simulator.**
