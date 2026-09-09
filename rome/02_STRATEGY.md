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

400 Monte Carlo runs per strategy, 500-year horizon, all three dated
catastrophes active.

| Strategy | Reaches the transistor | Median year | Elapsed | Dominant failure |
|---|---|---|---|---|
| **RUSH** (beeline at the goal, skip revenue, institutions, defence) | **0%** | never | - | founder dies with no successors, 100% |
| **TOPO** (bare topological order) | 58% | 396 AD | 296 yr | founder dies with no successors, 41% |
| **RECOMMENDED** | **79%** | **384 AD** | **284 yr** | founder dies with no successors, 20% |

The irreducible serial calendar time on the critical path, if money and labour
were infinite, is **144 years**. Everything above that is people, money and
catastrophe.

**The rush strategy scores zero.** It does not fail at the transistor. It fails
at `atomic_theory`, a node that requires two trained natural philosophers,
because it never founded a school. This is not a quirk of the model. It is the
central finding: *the bottleneck is never the machine, it is the number of
people who understand it.*

## 2. The value of each choice, measured

From the ablation study. "Delay" is how many years later the median run reaches
the transistor if that node is never built.

| Node removed | Delay | Verdict |
|---|---|---|
| `corpus_written` | **+90 yr** | CRITICAL |
| `corpus_dispersed` | **+50 yr** | CRITICAL |
| `printing_press` | +38 yr | clearly worth it |
| `rag_paper` | +32 yr | clearly worth it |
| `endowment_land` | +23 yr | clearly worth it |
| `academy_network` | +17 yr | clearly worth it |
| `plague_preparedness` | +8 yr | worth it |
| `telegraph_electric` | +6 yr | worth it |
| `world_map` | +5 yr | worth it |
| `crop_rotation` | +4 yr | marginal |
| `mirror_amalgam` | +1 yr, and success rate *rises* 6 points | the model says this costs more than it returns |

**The four biggest items in the entire tech tree are: write it down, print it,
copy it, and make the paper to copy it onto.** Not the blast furnace. Not the
steam engine. That result held under every calibration I tried, and it is the
single most useful thing this project produced.

The `mirror_amalgam` result is the model criticising my own strategy: once the
economy-growth term is active, luxury revenue is not worth the founder-hours it
costs. I have left it in the recommended order and flagged it rather than
quietly deleting it, because the revenue model is the weakest part of the
simulator and I do not trust that finding enough to act on it. Treat it as a
question, not an answer.

## 3. The phases

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

## 4. Three decisions I made deliberately, and why

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

## 5. What the model is probably wrong about

Stated plainly, because someone is going to check.

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
