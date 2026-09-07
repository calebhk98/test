# Brief: enriching the topic index

The topic index currently gives a name, a day, a ward and a one-clause note. That is
not enough to know what something is or why you would go. Each row becomes:

```
| What | Day | Address | Website | What it is |
```

## Where the material already is

**Most of this is a join, not fresh writing.** Nearly every item already appears in a
day's `### Activities` table in /home/user/test/japan-trip/days/, which carries a full
street address and a two-to-four sentence description. Pull from there first.

Example, from Day 2:

> | Pokemon Centre Skytree Town | 0h25 | 0 | 0 | Tokyo Skytree Town Solamachi, 4F East Yard, 1-1-2 Oshiage, Sumida-ku, Tokyo 131-0045 | The official Pokemon retail store, on the same mall floor the day already visits for the aquarium and Skytree deck - plushes, trading cards, region-exclusive merchandise, and a photo-op Pikachu. Free to walk in, no ticket needed... |

becomes

> | Pokemon Centre Skytree Town | 2 | Tokyo Skytree Town Solamachi, 4F East Yard, 1-1-2 Oshiage, Sumida-ku, Tokyo 131-0045 | https://www.pokemon.co.jp/shop/pokecen/skytree/ | The official Pokemon retail store: plushes, trading cards, region-exclusive merchandise and a photo-op Pikachu. Free to walk in, no ticket needed. Indoor and mall-level with lifts throughout. |

## The four columns

- **What** - keep the existing name unless the day file has a better one.
- **Day** - a bare number, or several separated by commas. **Verify against the day files**; some numbers in the current index are stale.
- **Address** - the verified street address from the day file. Where the day file says "(address unverified)", carry that through. Where an item is a district or a walk with no single address, give the district and nearest station. **Never invent an address.**
- **Website** - the official site, researched. Prefer the venue's own domain over an aggregator. Where a thing has no site of its own (a street, a public park, a monthly market), give the operating temple, city or prefecture tourism page if there is a real one, otherwise a single dash. **Never invent or guess a URL. Only give a URL you have actually seen resolve.**
- **What it is** - two to four sentences. What it actually is, why you would go, and any practical constraint that changes the visit: stairs, carrier rather than stroller, closure days, advance booking, age limits, tide dependence, opening hours where they bind. Condense the day file's description; the day keeps the long version.

## Rules

- **No self-assessment and no reference to how the itinerary was built.** No "covered", "the audit found", "an earlier draft", "this closes a gap", no praise of the plan. Write as though the trip has always been this way.
- Costs belong in the description where they matter, e.g. "¥600 per adult, free under 6".
- Do not use em dashes. Use " - " or a comma.
- Keep the section headings exactly as they are, at `##` level.
- Keep the existing row order within each section.
- If an item in the index does not appear in any day file, check whether it is real before keeping it. Say so in your report if you drop one.

## Output

Write ONLY your assigned sections, in the given order, to your own output file. Do not
touch topic-index.md or any other agent's file. Start the file directly with your first
`##` heading, no preamble.
