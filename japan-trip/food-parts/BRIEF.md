# Brief: enriching the food index

The food index currently gives a dish, a day, a neighbourhood and a short note. A reader
who does not already know Japanese food learns nothing from "Katsudon". Each row becomes:

```
| What | Day | Where | Website | Typical price | kcal | What it is |
```

## Where the material already is

Every row corresponds to a real meal in a day's `### Meals` table in
/home/user/test/japan-trip/days/, which carries the dish, the venue or store, the
kcal/adult for that meal and the party cost. Start there, then research the venue.

## The seven columns

- **What** - the dish. Keep the existing name.
- **Day** - bare number, or several separated by commas. **Verify against the day files.**
- **Where** - the venue with a real street address where the day file names a specific
  restaurant. Where the day file names only a chain and a neighbourhood, or a market
  stall, give the chain and district and say so. **Never invent an address.**
- **Website** - the restaurant's or chain's official site, researched and actually loaded.
  Chains like Ichiran, Ippudo, Marugame Seimen, Sukiya, Matsuya, Yoshinoya, Saizeriya,
  Sushiro, Kura Sushi, CoCo Ichibanya, Torikizoku and Yayoiken all have one. A market
  stall, a supermarket deli or a meal cooked in the accommodation kitchen has none: put a
  single dash. **Never invent or guess a URL.**
- **Typical price** - per serving, per adult, in yen. Take the day file's figure where it
  is per-dish; otherwise give the normal menu price for that dish and mark it approximate.
  Self-catered meals get the ingredient cost.
- **kcal** - an approximate figure for one adult portion. The day files give kcal per meal
  rather than per dish, so where a meal combines items, estimate the dish itself and label
  it approximate. Do not present an estimate as exact.
- **What it is** - two to four sentences, **written for someone who has never eaten
  Japanese food.** This is the point of the whole pass. Say what is physically in the
  dish, how it is served and eaten, and what it tastes like. "Katsudon" should tell a
  reader it is a breaded deep-fried pork cutlet simmered with onion and egg and served
  over rice in a bowl. Include a practical note where one matters: whether it is eaten hot
  or cold, whether it contains raw fish, whether it is safe or adaptable for a toddler,
  whether it is ordered from a vending machine at the door.

## Rules

- **No self-assessment and no reference to how the itinerary was built.** Write as though
  the trip has always been this way.
- Do not use em dashes. Use " - " or a comma.
- Keep the section headings exactly as they are, at `###` level.
- Keep the existing row order within each section.
- Note allergens or raw-fish content where a reader would want to know.

## Output

Write ONLY your assigned sections, in the given order, to your own output file. Do not
touch food-index.md or any other agent's file. Start directly with your first `###`
heading, no preamble.
