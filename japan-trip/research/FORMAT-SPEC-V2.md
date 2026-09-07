# Format spec v2 - supersedes DAY-FORMAT-SPEC.md for Activities and Meals

The header, Schedule and Lodging blocks have ALREADY been reformatted by script.
**Do not touch them.** Only the Activities and Meals sections change in this pass.

---

## Activities - NEW column order and NEW content requirement

```
### Activities

| Activity | Duration | Adult (¥) | Party (¥) | Location | Details |
|---|---|---|---|---|---|
```

`Location` must be a real street address wherever one is verifiable, in Japanese
postal order (e.g. "1-1 Marunouchi, Chiyoda-ku, Tokyo 100-0005"). If you cannot verify
a street address, give the district plus nearest station and write "(address
unverified)". **Never invent one.**

`Details` is the part that matters most in this pass. Today the tables assume the
reader already knows what everything is. They do not. Write 2 to 4 sentences that
answer, in this order:

1. **What it actually is.** A reader who has never heard the name should finish the
   first sentence knowing what kind of thing this is. "Shibuya Sky" means nothing;
   "an open-air rooftop deck 229 m above the Shibuya Scramble crossing" means
   something.
2. **Why you would go.** What is the actual experience or payoff. Be concrete and
   honest, including when the honest answer is "it is famous and it is fine".
3. **What to know practically.** Opening hours or last entry if they constrain the
   day, whether it needs advance booking, and the infant/stroller reality: stairs,
   gravel, crowds, carrier-only stretches, lifts, changing facilities.

Do not pad. Four good sentences beat eight vague ones. Where a thing is free, say
so plainly rather than leaving the cost column to carry it alone.

Infants are free at essentially every site on this trip. Party cost = adult x 3
unless stated otherwise; note the exceptions explicitly.

---

## Meals - same columns, much better content

```
### Meals

| Meal | What / Where | Address or store | kcal/adult | Cost (¥) |
|---|---|---|---|---|
```

The problem being fixed: rows currently read "Breakfast | Self-catered | Hotel
kitchenette | 500 | 750". That tells the reader nothing about what is being eaten.

**Every row must name actual food.** Rewrite so a reader knows what is on the plate:

- Bad:  `Breakfast | Self-catered | Hotel kitchenette | 500 | 750`
- Good: `Breakfast | Rice, miso soup, grilled salmon fillet, natto, banana | Cooked in room; ingredients from OK Store Ueno | 520 | 760`

- Bad:  `Dinner | Self-catered | Hotel kitchenette | 800 | 1,650`
- Good: `Dinner | Chicken thigh and cabbage stir-fry over rice, tofu and miso soup, half-price karaage from the evening deli counter | Cooked in room; Life Supermarket, Taito-ku | 790 | 1,640`

Rules:
- Where a meal is bought out, name the dish AND the restaurant or chain, not just the
  chain. "Marugame Seimen - kake udon plus a chicken tempura and a rice ball" beats
  "udon".
- Where breakfast is the Toyoko Inn buffet, keep cost ¥0 but still say what is on it
  (rice, miso soup, natto, pickles, bread, coffee, ~500 kcal).
- **Infant food rows must be specific too.** "Purees/formula" is not enough. Say what:
  formula feeds per day, which pouches (Wakodo, Pigeon or Morinaga - NOT Kewpie, which
  discontinues its baby food line in August 2026), and what the 20-month-old eats off
  the family table.
- Adult kcal must still sum to 1,950-2,100 per adult per day. Show the sum under the
  table. If you change a meal, re-check the arithmetic.
- Keep the party costs consistent with the day's cost table. If a meal cost changes,
  update the `### Day N Cost` table and the segment totals to match.

---

## Rules that still apply from v1

- Planning FX ¥155 = $1. Yen to the nearest ¥10, dollars to the nearest $1.
- Prices are 2026 planning estimates, not quotes. Never invent an address.
- Do NOT edit the `**Running total after Day N**` lines. A script recomputes those.
- Do not use em dashes. Use " - " or a comma.
- Two infants, ~12 months and ~20 months. Pacing rules unchanged: a mandatory
  1h30-2h00 midday rest block, ~7 hours active out-of-lodging time maximum.
