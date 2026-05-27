# Audit Findings — Chapters 44–53 (Final Act, Coda, Epilogue)

Research-only audit. No story files were edited. Scope: ch44–ch53 prose against the
prompt, Bad-writing list, chapter_list.md briefs, the bible (characters, world rules,
tech schedule, style guide, timeline + DIVERGENCE LEDGER), and each chapter's QA file.

Severity tags: [BLOCKER] (premise/canon breaking or banned-move that survived into
current prose), [MAJOR] (real craft/coverage problem), [MINOR] (watch-item / polish).

**Headline:** This range is in strong shape. The three QA chapters that carried a
REVISE verdict (ch46, ch47, ch49, ch52) all have their blocking fixes applied in the
current prose (verified below). No surviving BLOCKERs found. Findings are mostly MINOR
voice-watch items and a handful of MAJOR coverage notes worth flagging.

---

## Range-level patterns

### QA REVISE chapters — fix-verification (the central QA-vs-prose check)
chapter_list.md marks all of ch44–ch53 "ACCEPTED," but four QA files carry REVISE. I
checked each blocking issue against the *current* prose:

- **ch46 [REVISE → FIXED].** QA blocker: the closer was a lamp + young-person + figures
  tableau (banned "child-with-figures" + second consecutive storeroom-lamp closer).
  Current ch46 line 61 ends on Ulpia setting the leaf face-up, ruled-off-not-totaled,
  weighting the curling corner with "a stone loom-weight out of her mother's basket...
  true to the last headland, a thing not closed, only laid down." Lamp stripped, the
  load-bearing laid-down-column image kept. **Fix applied exactly as QA prescribed.**
- **ch47 [REVISE → FIXED].** QA blocker: reused ch43's signature closing clause "a house
  that was/is mine in a country that was not." Current ch47 line 55 ends "...and lie down
  beside Marcia, and wait to see what the night will be." Borrowed clause gone. **Fixed.**
- **ch49 [REVISE → FIXED].** QA blocker: a cluster of age/elapsed-time errors (Lucanus 26,
  Ulpia 29, Tyche 60, "sixty years" ×5). Current prose: Lucanus "eight-and-thirty" (L57),
  Ulpia "two-and-thirty" (L9), Tyche "five-and-sixty" (L47), and "fifty years"/"half a
  century" throughout (L75, L83, L87, L95). **All age fixes applied.**
- **ch52 [REVISE → FIXED].** QA blocker: banned narrator-stepping-outside-time clause
  "though she did not know that and never would" (L63). Current ch52 line 63 reads "...the
  way the founder had gone down his last stair, and behind her in its cedar case the
  patient step kept the count..." Clause excised; echo left architectural. **Fixed.**

### Banned-style mechanical scans (whole range, ch44–53)
- **Em dashes:** clean. A grep for `—`/`--` returned only markdown `---` section dividers,
  zero in prose.
- **"not X but Y" / correctio:** clean. The only candidate is ch46 L51 "Not all at once and
  not cleanly, but I let it go..." — same subject/verb both sides, a concessive qualifier,
  not the banned negate-to-pivot form (QA agrees; I concur).
- **Anachronistic time units / modern register:** clean. Every "second/minute"-looking hit
  is an ordinal ("second mile," "second morning," "second column," "second working") or
  "half a day" — all period-appropriate. No clock-minutes/seconds, no "okay," no "telephone."

### Intentional recurring motifs (NOT accidental repetition)
These recur across the range by design and are load-bearing; flagging only so the pattern
is on record, not as defects:
- **Macer's joke — "make me say it twice" + "you are paying your pressmen too much."**
  Appears ch48 L23 (Macer, origin), ch49 L95 (Daniel→Tyche), ch50 L45 (Tyche→dying Daniel).
  This is a deliberate three-beat inheritance arc and lands well; do not "dedupe" it.
- **The hooked stroke / "the Thulean is guessing here" / blank rungs.** ch47, ch49, ch52.
  Core thematic device (honest ladder); intentional.
- **"A step and a wait and a step, even and even" (the escapement knock).** ch52 (built),
  ch53 (at sea). Deliberate echo carrying the clock from invention to crossing.
- **"The press going on without me / biting its sheets."** ch44, ch46, ch48, ch50.
  Intentional institution-outlives-founder refrain.
- **Hands flat on a surface taking/refusing warmth.** Milestone (ch44), warm brick (ch47),
  the day-book that "gives nothing back" (ch48), warm cedar clock-case (ch52). A controlled
  recurring gesture; QA explicitly tracked ch48 as an *inversion* of ch47. Working as art,
  but it is now a four-time signature — worth a [MINOR] note that any *future* chapter should
  not reach for "old hands flat on a thing" a fifth time.

### Gnomic-aphorism density (range pattern) [MINOR]
The retrospective-memoir voice leans on one-line maxims. QA rationed these to ~one per
chapter and flagged several chapters at-or-near the ceiling (ch44 L13 + the L71 cadence;
ch48 L9 + L67; ch49 epigraph + L41 + L59; ch53 L5 + L7). None survive as a *closing* maxim,
and each is concrete-anchored, so none is a BLOCKER. But across ten chapters the cumulative
"a man wants… / a finished-looking book has killed… / it is the slow ones that wear you"
cadence is a recognizable authorial tic. Not a defect per chapter; a [MINOR] range texture
note.

### Character-canon note (per task)
- **The daughter (Ulpia Severa / "Procula"):** correctly NOT in `02_characters.md` — she is
  established only in the canon log (ch38: "ULPIA SEVERA," b. ~late 118). She is consistent
  across ch44–50 (clean copyist, grave, ferociously exact, reckons under a borrowed name
  because the law bars her). NOTE: "Procula" in ch52 is a *different* person — a freeborn
  workshop-line keeper ~190 AD, descended through the Chloe/freed-slave line, explicitly NOT
  Daniel's blood (ch52 L5; ledger L180 calls her "Procula" as the survey-continuer). The
  divergence ledger (L180) conflates the two by calling the epilogue line "the ladder Daniel
  laid and Procula began," which reads as if Procula is the survey-starter; the prose keeps
  them distinct. See ch52 note below — this is a [MINOR] ledger-wording ambiguity, not a
  prose error.
- **Tyche as keeper of the ladder:** fully consistent (ch47 dictation-keeper, ch49 holds the
  living master copy, ch50 at the deathbed, ch51 the "very old freedwoman… his clerk fifty
  years" still teaching the cipher). Canon-faithful.

### History-divergence discipline (range)
The single deliberate divergence (the ocean program) is handled with restraint exactly per
the ledger: ch44 shows it MEASURED/partial (third hull, cannot cross), ch46 shows it lapsing
(champion dead), ch53 delivers the crossing as a vague far whisper with no mechanical/
alternate-history over-explaining. No unlogged divergences. Details under each chapter.

---

## ch44 — The World Bends  (QA: PASS)

**Outline fidelity:** Excellent. All four briefed "accumulating divergence" signs are
rendered as distinct textured scenes, not a montage: (a) numerals on the Aurelian milestone
("a two and a circle," L9), (b) the printed library off the Argiletum with codices
outnumbering scrolls and a slave girl reading freely (L19–33), (c) the third open-ocean hull
at the Garonne yard that "could not cross" (L43–49), (d) the carter's boy reciting Felix's
steam-ship contest tale in the dust (L55–61). Hope/unease braided on every sign, and the
hubris-or-duty question is left open, pointing forward into ch45. Matches ledger L145–165
precisely (third hull, two lost, longitude unsolved, prize unwon).

**Bad writing:** Clean. Emotion rendered (the swallowed-stone-in-the-chest at the milestone),
not announced. No outside-time spoiler.

**[MINOR] Style — single permitted maxim-cadence at the close (L71).** The four-beat anaphora
"A figure serves the man who reckons with it… A book serves the page it carries… A faster
ship goes wherever its owner points the bow. A powder throws the stone the gunner aims." is
the one place the chapter edges toward stated thesis. It stays legal because it is rendered
through the four already-seen objects, but it is at the ceiling. Per QA: do not add a second.

**Easy fixes the MC ignores:** None genuinely missed — the chapter's whole point is that he
*can't* fix the deep problems (steel, longitude), and it is honest about that. No flag.

---

## ch45 — What It Serves  (QA: PASS)

**Outline fidelity:** Excellent and on-brief: Bar Kokhba brutality + the hubris-or-duty
question at its sharpest, unresolved. The atrocity is delivered through Daniel's own marks
(the captives column with the falling price, L13) and worn-smooth secondhand reports
(L21–23), never spectacle. Aelia Capitolina, the cave sieges, the Jewish prohibition all
rendered through the porticoes' casual approval. The moral core is left explicitly open
(L57: "Both arguments are good arguments… neither has ever once won").

**Bad writing:** Clean. The single close-retrospect line "I will go to my grave not knowing
which" (L47) is the one earned instance and ties exactly to the unresolved torment. No
preaching; the complicity is dramatized via the tally and the Thulean-name reframe.

**[MINOR] Voice texture — polysyndeton dread-cadence (L5, L9, L13).** The accumulating
"and… and… and" arithmetic-as-dread rhythm is effective and earned here, but it is now a
recognizable signature of this chapter (QA flagged the same). Range-level: future heavy
chapters should not reach for the identical rhythm to carry weight.

**Historical accuracy:** Tracks real Bar Kokhba history; no invented numbers, no new
divergence. Period-grounded moral vocabulary ("a slaughtering empire," "a destroyed people"),
no anachronistic terms (genocide/war-crime absent).

**Easy fixes the MC ignores:** N/A — the chapter is *about* his deliberate refusal to ask
whether his powder sealed the caves ("I would rather not know than be told," L45). That is
characterization, not an oversight, and the prose owns it ("I despise that in a man and found
it in myself"). No flag.

---

## ch46 — Hadrian Dies  (QA: REVISE → fix verified applied)

**Outline fidelity:** Full. Hadrian dies (dropsy at Baiae, thwarted suicides as city gossip,
the animula vagula blandula verses, L15–17); Antoninus Pius succeeds (L37); the ocean program
loses its champion and is foreseen to lapse-not-be-killed (L45–49); Daniel relinquishes the
private "road west / home" hope (L49); the survey is kept "current-but-unworked… laid down,
not closed" (L57–61); the endowed institutions hold (L39). Matches ledger L166–176 exactly,
including "true to the last headland."

**QA status:** The lone blocker (lamp/young-person/figures closer) is **fixed** in current
prose (L61 ends on the loom-weighted laid-down leaf; lamp stripped). Verified.

**Bad writing:** Clean now. Two future-vantage lines — "as far as I would ever know" (L27)
and "no one would ever again, in my lifetime" (L47) — both render present-moment reckoning,
not "little did I know"; "in my lifetime" is load-bearing for the mortality beat. Acceptable.

**[MINOR] Two gnomic maxims (L47 "the answer that ends projects"; L57 "an emperor's death is
a thing that closes columns").** Neither closes; at the watch ceiling but within it.

**Character consistency:** The complex Hadrian feeling (relief and grief "the same size and
the same shape and I could not get a knife between them," L31) is rendered, not named, and
earned. Survivor's-detachment contrast with ch30 (Trajan blindside) is achieved through
action (going back to the pearwood) — good.

---

## ch47 — Old  (QA: REVISE → fix verified applied)

**Outline fidelity:** Full. Body failing with no medicine he can make (the dished-step
cardiac episode, L5–9; eyes, hands, teeth, sleep, L13–21); the encyclopedia's upper rungs
finished by dictation against time (L25–33); a last unbuilt dream let go — the clock/
escapement formally relinquished and the gear-box given to Felix's failure-fund (L37–43).
The Macer-husk beat (L47–49) sets up ch48.

**QA status:** The blocker (reused ch43 signature closing clause) is **fixed** — current L55
ends on "...and wait to see what the night will be." Verified. The warm-brick roof image was
ruled acceptable (tactile/downward, view explicitly refused) and is kept.

**Bad writing:** Clean. One close-retrospect line (L9, "in all the years of picturing my
death") within ration; not at open or close.

**[MINOR] Two candidate aphorisms (L15 "It is the slow ones that wear you"; L43 "A ladder
that hides where its maker fell teaches a man to fall there again").** Spaced, neither the
closer; at the edge of the ration.

**Easy fixes the MC ignores:** N/A — the thematic point is precisely that he built clean
water and germ-practice and *still* cannot touch his own heart/age ("The heart is inside…
There is no boiling them out," L9). Deliberate and earned.

---

## ch48 — The Subtraction  (QA: PASS)

**Outline fidelity:** Full. The last deaths rendered as distinct scenes: Pamphilus (L5),
Eros (L7), then Macer (L13–29) and Marcia (L41–53). Macer = "cage and shield" paid off in the
will beat ("to the Thulean, who will know what it cost," L29). The keepers are confirmed as
the ones who now hold the ladder (L35). Daniel's letting-go rendered, not annotated.

**Bad writing:** Clean. No banned close-retrospect tic (a real strength given ch13 closed on
"as long as I live"). Marcia's absence rendered through behavior (the reach for her breathing,
the patted-empty-table tally habit, L59–61) — excellent, not announced.

**[MINOR] Second gnomic maxim near the close (L67).** "I had thought… the hardest thing here
would be to be the only one who knew. I had not reckoned on this." This is a second sweeping
maxim (first is L9). Saved from blocking only because the actual closer is the L69 day-book
image and it is biographically anchored. QA recommended recasting off the maxim frame; the
prose currently retains it. Worth flagging as the one spot brushing the ration.

**Character consistency:** Macer at 96 supersedes an earlier provisional canon cap of ~90;
the prose flags 96 as "a freakish thing… an obscenity almost" (L15), which handles it. The
gold ring "will not go past the swell of my own ruined knuckles" ties to ch47. Consistent.

---

## ch49 — Securing the Ladder  (QA: REVISE → fixes verified applied)

**Outline fidelity:** Full and precise. The four copies are secured with distinct concrete
dispositions (Tyche's moving working copy; the sealed collegium chest under a three-board
rule; the lead-and-pitch case under the press-room stone; the partial Latin in the Argiletum
as "the open door," L17–27). Honest blanks/hooked strokes enforced (L31–41). The keeper-chain
written into the deed as a binding rule, fanning down the craft line not the blood (L45–51).

**The dead-phone relic's last appearance — RESOLVED (per task requirement):** Decided and
rendered. The phone ("the dead glass") AND the citizenship tablet ("Marcus Ulpius Danihel")
are to be **buried with Daniel** in the oiled wool, box not reopened (L77–79, L89). Macer's
ring goes (as worth) to Felix's patronage fund (L61). The decision is dramatized in a private
Daniel–Tyche scene; Tyche offers to keep it, Daniel refuses ("the carrying ends with the
carrier"). Theme rendered, not thesis-stated. **Resolution confirmed.**

**QA status:** All four age/elapsed-time blockers **fixed** in current prose (Lucanus 38,
Ulpia 32, Tyche 65, "fifty years" throughout). Verified.

**[MINOR] Borderline exposed-subtext (L51).** "the ladder I had built was for whoever was
hungry, and it would not check a man's birth before it let him up. That was the whole quiet
argument of the thing." Edges toward stating the thesis; partly defused by "I never once said
it aloud to him." QA suggested trimming "That was the whole quiet argument of the thing."
Still present; a legitimate [MINOR] watch.

**[MINOR] Aphorism density (L3 epigraph, L41, L59).** L59 "Some things you secure. Some things
you only confess you could not." is a section-closing maxim — the weakest of the three.

---

## ch50 — Going  (QA: PASS)

**Outline fidelity:** Full. Daniel's death, far from home, not tidy — he drowns by inches,
propped, "working at the air the way you work a stiff pump" (L41). No deathbed wisdom-speech;
his last attempted communication is the pressmen-overpay joke he can't get breath to say
(L45). The ch01 bookend (stubble field, dew, new Colosseum, the four spearmen, the warm phone
"that will not call anyone," age seventeen, "no one… who knows where I am," L55) lands as
failing perception and breaks off mid-sentence (L57: "and the next one is"). Render-not-
annotate honored.

**Structural integrity (the load-bearing check):** No posthumous narration. The past→present
collapse is motivated by the L49 hinge ("It is hard to say now where the order of it went").
The clean mid-sentence threshold stop preserves first-person honesty. Aftermath correctly
reserved for ch51–53.

**Bad writing:** Clean. The danger line (L17, "I had moved what I could reach… The rest stood
at the foot of the bed") lands as concrete perception inside the "unbuilt dead" image, not
thesis. ESCALATED voice-watch at ZERO for the dying-narrator chapter (no close-retrospect
tic, no maxim closer). One earned gnomic line (L51, "I have always known the difference
between rising and not falling") grounded in his lived balloon physics; not at the close.

**Predictability:** Avoids a tidy bow — he gives Ulpia the same lie to the end (L27), the
secret goes into the ground untold. Devastating rather than neat.

**[MINOR] Continuity nicety (not an error).** The "electric wire lighting the dark" (L17) is a
new never-attempted unbuilt dream appearing for the first time here. It is explicitly framed
as something he "could not have so much as begun," consistent with the impossible-bait rule.
Logged as first appearance; no defect.

---

## ch51 — A Hand Not His  (QA: PASS)

**Outline fidelity:** Full and on-brief. Pliny-manner letter (Gaius Norbanus Rufus to Sextus
Caecilius Priscus, dated 12 June AD 170, ~15 years post-death). Daniel remembered AND
misremembered: the figures vindicated, the balloon "past dispute," the microscope a fraud, the
germ-practice credited to Asclepius, Crispus's "the barbarian's heaven by ladder" survives as
the famous phrase, the enterprise "dedicated into Minerva's keeping… Heaven… bought rather than
climbed." Dramatic irony built architecturally, never declared.

**The buried-phone payoff:** The black-glass tablet is misread as "a savage's charm… a dark
mirror these northern peoples carry to frighten off the dead" (L21), laughed at, NOT understood,
NOT dug up. The reader supplies the truth. Exactly the planted gap between man and legend.

**Bad writing:** Clean. The watched line (L23, "the thing he made does not need him to be
remembered rightly in order to go on") reads as an in-character cynical aside buried under the
corked-wine close, not a theme-declaration. No anachronism. Voice fully distinct from Daniel's.

**Historical accuracy:** Consulship of Clarus and Cethegus = real ordinary consuls of AD 170.
Correct anchor, not a fake detail.

**Predictability:** The toy close ("a wheeled lie a child loves, going nowhere on a marble
floor, very fast," L25) lands the irony concretely without a bow.

---

## ch52 — A Generation Later  (QA: REVISE → fix verified applied)  ⟵ the one to check carefully

**Outline fidelity:** Full. ~190 AD. The press still runs, the contest is still held on the
Quinquatrus in Minerva's name (priests paid from the endowment, L49). A young keeper (Procula,
freeborn, descended through the freed-slave/Chloe line, NOT Daniel's blood) decodes the English
ladder ("BEGIN WHERE I FAILED," L9) and climbs the exact rung Daniel marked he couldn't reach —
the escapement/isochronism. The bottom rungs held. Warm, earned, forward-facing. Sets up the
sea-clock/longitude next rung (L59) into ch53.

**QA status (REVISE — checked carefully per task):** The lone blocker — the banned
narrator-from-future clause "though she did not know that and never would" (L63) — is **excised
in current prose**. L63 now reads cleanly: "...the way the founder had gone down his last stair,
and behind her in its cedar case the patient step kept the count of the climbing night..." The
ch50/ch47 echo survives; the irony stays architectural. **Verified fixed.**

**[MINOR] Borderline declared-gap opener (L53), QA non-blocking.** "She did not know the man who
had laid the bottom of it." This is a "she did not know" sentence-opener, but the paragraph
immediately earns it architecturally (the sleet-word she "never once thought to wonder" about;
"the truth of him went on lying quiet under the press-room stone and under the dirt of a grave
she had never seen"). Acceptable as written; flagged as the one remaining soft spot. QA's
optional suggestion to recast the opener to an action was not taken — fine, but on record.

**Honesty / no-magic-leap (the chapter's strongest achievement):** Procula builds ALL of
Daniel's failed drawings first (L21), they fail as he said, she logs each per the oath; the
breakthrough is a physical analogy (a child's swing felt "with a piece of cloth in her hand and
not in her head," L25–31), then thirteen logged hangings with a bleeding knuckle (L33), then a
year of fitting still owed. Explicitly "not a clock yet" (L41), still drifts (L59), keeps uneven
seasonal Roman hours (L43). No over-reach into modernity. Exemplary discipline.

**[MINOR] Ledger-wording ambiguity (not a prose defect).** Divergence ledger L180 says the
crossing is "the ladder Daniel laid and Procula began." In the prose, the *African survey* was
begun under Daniel/Ulpia (ch44/46), and *Procula* is the ~190 clock-builder. The ledger phrasing
risks reading as if Procula started the ocean survey. The prose keeps roles distinct; only the
ledger gloss is loose. Worth a one-line ledger clarification by the coordinator.

**Predictability:** The "someone climbs a rung" payoff is the planned thesis beat, but it avoids
a tidy bow — the clock still drifts and is no use at sea yet, and she "would not reach" the next
rung. Forward-open.

---

## ch53 — The Far Whisper  (QA: PASS)

**Outline fidelity:** Full and on-brief. The largest deliberate divergence (the ocean ultimately
crossed) is delivered as a brief, spare, distant log-record glimpse. A single ship stands off an
unknown western coast after 31 days out of sight of land, finding its westing by the gimbaled
sea-clock box (descended from Procula's escapement; longitude implicitly solved) against
sun-height, lead-line soundings, and figures-with-zero (L3–11). Matches ledger L177–189.

**History-divergence discipline (the task's key check):** Stays a vague whisper. NO mechanical
over-explaining (the boy "could not have explained why it was true. He only had to read it,"
L5), NO alternate-history exposition, NO "how the empire changed." The crossing is glimpsed, not
built out.

**The shore is INHABITED (puncturing the "uninhabited" lie):** Rendered plainly and without
authorial comment — a tended fire, drawn-up boats, figures at the waterline (one lifts an arm),
"three more smokes far up the green hills… people who had been living there a long time" (L13–17).
The pilot does NOT land or conquer; she holds off in deep water; "she did not write what it
meant… No one did yet" (L23). A beginning, unresolved — the explicit no-tidy-bow.

**Daniel FORGOTTEN:** His name survives only as "the wear of one… the place where a name had
stood at the bottom of the oldest copy" of the rule-of-the-box, "read by no one as a man… a sound
with no person behind it" (L21). The phone is never mentioned. The forgottenness is a present
observable fact (a worn name on a nav-table), not an outside-time declaration.

**Bad writing:** Clean. Two maxim-leaning phrases land near each other (L5 "the whole of the
secret and the whole of the cost"; L7 "which was the whole point and the work of lifetimes") —
separate paragraphs, neither closes, both tethered to concrete mechanics. [MINOR] watch only.
The load-bearing bookend line (L27, "looked west at the shore, the way you look at a thing you
have only ever drawn") reads literally as the pilot looking at the point she charted; the
ch03-map echo is left entirely to the reader. Correct.

**Predictability:** The final image (unnamed pilot at the rail looking WEST, the box knocking
below decks, "a step and a wait and a step, even and even") is concrete perception + sound, not
a maxim and not a bow. The climb continues past the page. Strong ending.

---

## Summary table

| Ch | QA verdict | Fix status in current prose | Surviving issues |
|----|-----------|------------------------------|------------------|
| 44 | PASS   | n/a                          | MINOR: closing maxim-cadence at ceiling |
| 45 | PASS   | n/a                          | MINOR: polysyndeton dread-cadence is a chapter signature |
| 46 | REVISE | FIXED (loom-weight closer)   | MINOR: two maxims within ration |
| 47 | REVISE | FIXED (closing clause cut)   | MINOR: two candidate aphorisms |
| 48 | PASS   | n/a                          | MINOR: second maxim near close (L67) |
| 49 | REVISE | FIXED (all 4 age errors)     | MINOR: borderline exposed-subtext L51; phone disposition RESOLVED (buried) |
| 50 | PASS   | n/a                          | none (clean dying-narrator chapter) |
| 51 | PASS   | n/a                          | none |
| 52 | REVISE | FIXED (banned clause excised)| MINOR: "she did not know" opener L53; ledger-wording ambiguity |
| 53 | PASS   | n/a                          | MINOR: two adjacent maxim-phrases |

No surviving [BLOCKER]s in the range. All required beats rendered; the dead-phone relic
resolved (buried with Daniel, ch49); ch53 divergence stays a vague whisper with the shore
inhabited and Daniel forgotten, per the ledger.
