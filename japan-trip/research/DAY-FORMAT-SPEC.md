# Day-Block Format Spec (all writing agents MUST follow exactly)

Every day is one markdown block. No deviation in headings, order, or table columns.

---

## Day N — Weekday, Month D, 2026 — <City / Base>

**Base:** <city> | **Weather (typical):** <high>/<low> °C, <rain note>
**Theme:** <one line>

### Schedule

| Time | Duration | Item | Type |
|---|---|---|---|
| 07:30 | 0h45 | Breakfast at apartment | Food |
| 08:30 | 0h25 | Ueno Stn -> Asakusa (Ginza Line) | Transit |
| ... | ... | ... | ... |

- `Type` is one of: Food, Transit, Activity, Lodging, Rest, Admin.
- Every row needs a real duration. Infant nap/rest blocks are mandatory: at least
  one 1h30-2h00 midday rest block back at the lodging or a park on every day.
- Total scheduled hours + rest must be plausible for a party with two under-2s.
  Cap active out-of-lodging time at ~7 hours/day. Do not schedule 12-hour days.

### Lodging

**<Property name>** — <full street address>
Unit: <type, max occupancy> | Nightly: ¥X,XXX (= $XX.XX) | Night <n> of <total>

### Meals

| Meal | What / Where | Address or store | kcal/adult | Cost (¥) |
|---|---|---|---|---|
| Breakfast | ... | ... | 550 | 780 |
| Lunch | ... | ... | 700 | 1,450 |
| Dinner | ... | ... | 750 | 2,100 |
| Infant food | ... | ... | n/a | 900 |

- Adult kcal column MUST sum to 1,950-2,100 per adult per day. Show the sum.
- Costs are for the WHOLE PARTY (3 adults), infants on their own row.
- Name real chains/stores/restaurants. If you are not certain a specific branch
  exists at an address, name the chain and the neighbourhood only.

### Transport

| Leg | Mode | Duration | Adult fare (¥) | Party cost (¥) |
|---|---|---|---|---|

- Infants under 6 ride free on JR and city transit (2 free per fare-paying adult),
  so party cost = adult fare x 3 unless a seat is reserved. State it when it differs.

### Activities

| Activity | Location | Details | Duration | Adult (¥) | Party (¥) |
|---|---|---|---|---|---|

- Under-6 admission is free at most Japanese sites; note the exceptions.
- At least 2 days per week must be built around free activities (parks, shrines,
  neighbourhood walks, riverside) to hold the budget.

### Day N Cost

| Category | ¥ | $ |
|---|---|---|
| Lodging | | |
| Food | | |
| Transport | | |
| Activities | | |
| **Day total** | | |

**Running total after Day N: ¥XXX,XXX ($X,XXX)**

---

## Global rules

1. Planning FX rate: use the rate given in the brief. Show ¥ first, $ in parentheses.
2. Round yen to the nearest ¥10, dollars to the nearest $1 in day totals.
3. Never invent a street address. Verified address, or chain + neighbourhood only.
4. Every price gets a source posture: prices are 2026 planning estimates unless you
   verified them. Do not present estimates as quotes.
5. Two infants are ~12 months and ~20 months in October 2026. The 12-month-old is
   still on formula + purees; the 20-month-old eats mostly table food.
6. Do not exceed your segment's assigned budget envelope by more than 5%.
