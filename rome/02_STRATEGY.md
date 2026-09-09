# 02 - Master Strategy

The plan, why it is shaped this way, and the evidence from the simulator that it
is better than the obvious alternatives.

Run the evidence yourself:

```
python3 rome/sim/simulator.py compare      --mc 500
python3 rome/sim/simulator.py sensitivity  --mc 300
python3 rome/sim/simulator.py path point_contact_transistor
```

---

## 1. The result, up front

600 Monte Carlo runs per strategy, 500-year horizon, all three dated
catastrophes active.

| Strategy | Reaches the transistor | Median year | Elapsed | Dominant failure |
|---|---|---|---|---|
| **RUSH** (beeline at the goal, skip revenue, institutions, defence) | **0 of 600** | never | - | founder dies with no successors, 93% |
| **TOPO** (bare topological order of the technical prerequisites) | **5 of 600** | 417 AD | 317 yr | founder dies with no successors, 94% |
| **RECOMMENDED** | **471 of 600 (78%)** | **385 AD** | **285 yr** | founder dies with no successors, 16% |

With all random events switched off, so pure engineering with no plague, no
civil war and no denunciation, the recommended strategy reaches the goal in 84%
of runs with a median of **367 AD**. The catastrophes cost about **19 years and
7 percentage points**. The strategy choice costs everything.

The irreducible serial calendar time on the critical path, if money and labour
were infinite, is **133 years across 23 nodes**. Everything above that is
people, money and catastrophe.

## 2. Why the two obvious strategies score zero

**RUSH does not fail at the transistor. It fails long before it**, in every one
of 600 runs, because that node needs two trained natural philosophers and the rush
strategy never founded a school. It gets a blast furnace, crucible steel, a
screw-cutting lathe and mineral acids, and then stops, because there is nobody
to hand them to.

**TOPO fails for a subtler and more interesting reason, and finding it was the
most useful thing this project did.** Halfway through building the tree I
removed one prerequisite edge that was wrong: I had made mercury supply depend
on an imperial mining concession, when in fact cinnabar was traded across the
Empire as the pigment *minium* and you can simply buy it. Removing that single
edge dropped **citizenship, the licensed collegium, the freedman staff, the
school, both patrons and the optical telegraph out of the technical closure of
the goal entirely.** Nothing in physics requires any of them.

The topological strategy, which follows the technical graph, promptly collapsed
from a 58% success rate to under 1%.

That is the finding: **the technical dependency graph is not the real dependency
graph.** Nothing in the chain from calamine to a germanium crystal requires you
to be a citizen, or to have a patron, or to have taught anybody. And you cannot
do a single step of it without all three.

## 3. The value of each choice, measured

Ablation study, 300 runs per variant. "Delay" is how many years later the median
run reaches the transistor if that node is never built.

| Node removed | Success rate | Delay | Verdict |
|---|---|---|---|
| `freedman_staff` | **0%** | never | CRITICAL |
| `collegium_licensed` | **0%** | never | CRITICAL |
| `citizenship` | **0%** | never | CRITICAL |
| `school_founded` | **0%** | +173 yr | CRITICAL |
| `corpus_written` | 73% | **+83 yr** | CRITICAL |
| `corpus_dispersed` | 76% | **+47 yr** | CRITICAL |
| `rag_paper` | 77% | +42 yr | clearly worth it |
| `printing_press` | 76% | +40 yr | clearly worth it |
| `patron_senatorial` | **37%** | +6 yr | CRITICAL |
| `world_map` | **49%** | +3 yr | CRITICAL (as early revenue and early favour) |
| `endowment_land` | 76% | +27 yr | clearly worth it |
| `academy_network` | 75% | +21 yr | clearly worth it |
| `patron_imperial` | 70% | +16 yr | clearly worth it |
| `semaphore_telegraph` | 68% | +7 yr | clearly worth it |
| `telegraph_electric` | 74% | +4 yr | worth it |
| `plague_preparedness` | 77% | +7 yr | marginal in this model, and I distrust that |
| `crop_rotation` | 77% | +2 yr | marginal |
| `sanitation_antisepsis` | 75% | +1 yr | marginal |
| `mirror_amalgam` | **80%** | 0 yr | the model says this costs more than it returns |

Two things to take from that table.

**The four biggest technical items in the entire tree are: write it down, print
it, copy it, and make the paper to copy it onto.** Not the blast furnace, not
the steam engine, not the dynamo. That result survived every recalibration I
tried.

**Everything with a 0% row is a social or legal node, not a technical one.**

Two results I have left in rather than tuning away. `mirror_amalgam`, one of my
own recommended revenue businesses, apparently costs more founder-hours than it
returns; I think that is an artefact of the weak revenue model rather than a
real finding, and I say so rather than deleting the line. And
`plague_preparedness` scores as marginal, which I do not believe: the model lets
staff regrow too easily after a plague, so it understates the value of not
losing them.


## 3a. The one number that reframes the whole problem

`python3 rome/sim/simulator.py path` reports that the minimum technical closure
of the goal is **84 nodes, 49,550 founder-hours and 3.54 million denarii**,
against the roughly **72,000 hours** you will ever have.

So on hours alone, one person could in principle direct the entire technical
path to a transistor. It is the other two constraints that make that a fantasy:

1. **The calendar floor is 133 years** and you have about 30. Nitre beds take
   two years whatever you spend. A generation of economic diffusion takes a
   generation. Money buys neither.
2. **The 84 technical nodes do not include a single one of the 44 nodes that
   provide the money and the people.** No patron, no citizenship, no school, no
   revenue, no printing, no defence against plague. Ablate any of the first
   three and the success rate is zero.

The technical problem is one lifetime of work. The actual problem is three
centuries of institution-building, and that is the problem this project is
really about.


## 3b. Two sweeps that changed how I would play this

`python3 rome/sim/simulator.py sweep capital` and `sweep lifespan`, 200-250 runs
per point. **Read the failure column, not the success column.** When the way you
die changes, the binding constraint has changed and so should your strategy.

### More starting money is not simply better

| Starting capital | Success | Median | Dominant failure |
|---|---|---|---|
| 2,000 den | 69% | 388 AD | died without successors |
| 5,000 den | 71% | 388 AD | died without successors |
| **10,320 den** (the default kit, 3 kg of gold) | 76% | 380 AD | died without successors |
| 25,000 den | 79% | 385 AD | died without successors |
| **50,000 den** | **80%** | 374 AD | denounced as a magician |
| 200,000 den | 74% | 373 AD | **denounced as a magician** |
| 1,000,000 den | 71% | 375 AD | **denounced as a magician** |
| 10,000,000 den | 71% | 375 AD | **denounced as a magician** |

The optimum is somewhere around **25,000 to 50,000 denarii**, comfortably below
the equestrian census of 100,000, and past that **more money makes you less
likely to succeed**. The mechanism is not arbitrary: money buys speed, speed
produces a stream of inexplicable marvels, and a stream of inexplicable marvels
in Trajanic Italy gets you prosecuted before your patron can absorb it.

Practical consequence: **bring enough gold to buy a workshop and a staff, and
not enough to look like a magnate.** If you find yourself rich, spend it on
people and on public benefaction, which lowers suspicion, rather than on
building three more things at once, which raises it.

### The founder's lifespan matters enormously, then abruptly stops mattering

| Years the founder survives | Success | Median | Dominant failure |
|---|---|---|---|
| 10 | **0%** | never | died without successors |
| 15 | **0%** | never | died without successors |
| 20 | 48% | 383 AD | died without successors |
| **28** (the median draw) | **86%** | 379 AD | denounced |
| 35 | 90% | 378 AD | denounced |
| 45 | 88% | 383 AD | denounced |
| 60 | 88% | 372 AD | denounced |

There is a cliff between 15 and 28 years and a plateau after it. Living to 95
buys you almost nothing that living to 63 did not.

**That is the clearest statement of the job.** Your entire task is to get the
school founded and the corpus started before roughly year 20. Everything you
personally build after that is a bonus, and everything you fail to transmit
before then is lost whatever else you achieve. It also means the most valuable
possible use of your medical knowledge is on yourself and your first students,
early: the difference between dying at 15 years in and 28 years in is the
difference between certain failure and 86%.

## 4. The phases

### Phase A - Years 0 to 5. Survive, and start the slow things.
Do nothing impressive for six months. Then, in parallel:
- **nitre beds** (24 months of biology you cannot buy down)
- **lens grinding** (revenue, and the gift that buys your first patron)
- **units and standards** (before you write any recipe down)
- **a patron**, then **citizenship**, then a **licensed collegium**

Cheap wins that cost days and buy goodwill: the horse collar and whippletree,
the crank and connecting rod, the drawplate, hard soap, the world map, the
camera obscura, the single-bead microscope.

### Phase B - Years 5 to 20. Convert money into people.
**Found the school.** This is the pivot of the entire game and every year of
delay costs more than any single technology. Buy skilled slaves, teach them,
free them, pay them, keep them: a manumitted literate artisan transmits
knowledge and a coerced labourer does not, and Roman society is entirely
comfortable with the arrangement.

Start the corpus. 6,000 of your hours over ten years. Do not cut it.

### Phase C - Years 10 to 30. Make knowledge indestructible.
Paper, then oil-based ink, then punchcut type, then the press (Rome already has
the screw press, so you are building half a machine). Then **hundreds of copies
of the corpus, dispersed from Britain to India, in three climates and two
languages.** The lesson of Alexandria is not that books burn. It is that single
copies burn.

### Phase D - Years 15 to 60. The three industrial keys, in order.
1. **Iron.** Water-blown bellows, then the tall shaft furnace and cast iron,
   then the finery and puddling, then cementation and crucible steel. This is
   also the financial engine of the middle game.
2. **Acid.** Green vitriol in a retort, then the lead chamber process. Then
   nitric and hydrochloric from it. Nothing in chemistry happens first.
3. **Precision.** Three plates rubbed in rotation give a true plane from
   nothing. From the plane comes the straightedge, the square, the master
   screw, the lead screw, the micrometer, the bored cylinder, and every
   machine after.

### Phase E - Years 50 to 150. Zinc, then electricity.
**Zinc metal is the hidden gate and almost nobody sees it.** Zinc boils at
907 C, below the temperature at which its ore is reduced, so it leaves as vapour
and reburns, which is exactly why Rome makes brass without ever seeing the
metal. Seal the retort, condense downward. Without zinc there is no voltaic
pile, and without a pile there is no electrochemistry, no electromagnetism, and
no electrical age at all.

Then: pile, Daniell cell, drawn insulated copper wire (silk, oiled linen and
shellac, because you have no rubber and never will), tangent galvanometer,
electromagnet, telegraph, dynamo with self-excitation, transformers, grid.

### Phase F - Years 120 to 280. Vacuum, purity, semiconductors.
Sprengel mercury pump (high vacuum with no machining at all), discharge tubes,
the vacuum tube, then the germanium chain: zinc smelter flue dust, germanium
tetrachloride distilled like brandy at 86 C, hydrogen reduction, zone refining,
Czochralski pulling, and finally two phosphor bronze points a fraction of a
millimetre apart on an n-type slab.

## 5. Three decisions I made deliberately, and why

**Gunpowder is scheduled last, on purpose.** It is cheap, it is easy once the
nitre beds run, and it would buy imperial favour instantly. It would also arm
every provincial usurper for the next two centuries, during exactly the fifty
years when the Empire must not fragment. Develop the nitric acid chemistry,
withhold the corning step, and keep it as a card to play if the programme's
survival requires it.

**Steam is scheduled late.** Italy and Gaul have rivers. Water power gets the
same shaft horsepower for a fraction of the prerequisite tree, and steam is
gated behind cylinder boring anyway. Steam matters when you need power where
there is no river, which is a problem you do not have for a century.

**Public health is a technology node, not a moral aside.** You know the Antonine
Plague arrives in 165 AD. Quarantine, clean water, handwashing and variolation
are nearly free and they are what decides whether your school still exists in
181 AD. It is also, separately, the right thing to do, and the two facts are not
in tension.

## 6. What the model is probably wrong about

Stated plainly, because someone is going to check.

- **The calibration was tuned by me until the output looked defensible, and you
  should discount it accordingly.** The first version of this simulator returned
  a median of 253 AD, which I judged far too fast for a programme that has to
  build a power grid and a railway, so I raised the workforce requirements on the
  heavy nodes and added generational diffusion floors. Those changes were
  reasoned, and they were also chosen because the answer they produced looked
  more plausible to me. That is not an independent measurement. The parts of this
  project that are NOT tuned in that way, and are therefore worth more, are the
  dependency structure, the ablation ORDERING, and the two sweeps in section 3b,
  where the shape of the result (an optimum in starting wealth, a cliff in
  lifespan) was not something I designed for and did not expect.

- **The absolute years.** Trust them to a factor of about 1.5, not better. The
  ordering and the failure modes are far more robust than the dates.
- **The revenue side is the weakest part.** Roman bulk commodity prices marked
  [C] in `data/prices.json` are my estimates anchored to silver through ratios
  implied by the Edict of Diocletian, which is 301 AD and denominated in a
  collapsed currency. The `mirror_amalgam` ablation result above is probably an
  artefact of this weakness.
- **The social model is under-powered.** Denunciation ends only about 2% of
  runs. I believe the true risk to an unprotected foreign chemist in Trajanic
  Italy is materially higher than that, and I could not find a defensible way to
  calibrate it. Treat `03_SOCIAL_POLITICS.md` as better than the number.
- **Slavery is modelled as a labour market with a manumission option.** That is
  a thin treatment of the central economic institution of the society, and it
  understates how much cheap coerced labour suppressed the business case for
  every labour-saving device in this document.
- **There is no competitor, no state seizure of your industry, and no war that
  targets you specifically.** All three are real risks the model ignores.
