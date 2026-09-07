# Fix brief: transit rows and hangaku timing

Two corrections to apply across every day. Both are accuracy problems, not additions.

---

## FIX 1: Missing transit between activities

Schedules currently jump between locations with no travel time, which implies the
places are adjacent when they are not. Example, from Day 3:

```
| 08:30 | 1h15 | Activity | Ueno Zoo (stroller-friendly paths) |
| 09:45 | 0h45 | Activity | Tokyo National Museum - permanent collection |
```

Those are about a 15-minute walk apart inside Ueno Park. The walk must appear.

**Go through every day you own, row by row.** Wherever two consecutive rows are at
different locations and there is no Transit row between them, insert one:

```
| 09:45 | 0h15 | Transit | Walk, Ueno Zoo -> Tokyo National Museum (through Ueno Park) |
```

Then **re-time every row after the insertion** so the day stays arithmetically
consistent. The clock must add up: each row's start time equals the previous row's
start plus its duration.

Rules:
- Name both ends of the movement, e.g. "Walk, X -> Y", not just "Walk".
- Give realistic durations. Verify with a map where you are unsure. Do not guess
  wildly; a 15-minute walk written as 5 minutes is the same class of error as
  omitting it.
- **Add a realistic buffer for this party.** Three adults, a stroller, and two
  infants move slower than a solo traveller: lifts instead of stairs, nappy changes,
  a toddler who wants to walk. Where a map says 10 minutes on foot, 15 is honest.
- Short in-complex moves still count. If the aquarium and the observation deck are
  in the same building, a 5-minute Transit row is still better than none.
- Do NOT add transit where there genuinely is none, e.g. two activities in the same
  room, or a meal at the venue just visited.
- If inserting transit pushes a day past its stated active-time figure, update that
  figure honestly. Do not quietly leave the old number.

Recompute each `### Day N Cost` table only if a fare actually changes. Most of these
insertions are walks and cost nothing.

---

## FIX 2: Hangaku markdown timing is currently unrealistic

The itinerary refers to hangaku (半額, 50% off) evening markdowns as a budget lever
but never states when they actually happen, and some days imply a discount run at a
time when no discounts exist yet. Real timings:

| Venue type | Closing | First markdowns (10-30%) | True hangaku (50%) |
|---|---|---|---|
| Depachika, department store food halls | 20:00-20:30 | 18:30-19:00 | **19:15-19:45** |
| Standard supermarkets (Aeon, Life, Ito-Yokado) | 21:00-22:00 | ~19:30 | **20:00-20:45** |
| 24-hour supermarkets | n/a | tied to expiry batches | **21:00-23:00** for bento and sashimi |

**The problem this creates, and it must be faced rather than glossed over:** this
itinerary puts the infants down at roughly 19:00-19:30. A true supermarket hangaku
run at 20:00-20:45 is therefore **after bedtime**, and cannot be a family outing.

So wherever a day claims a hangaku saving, rewrite it as one of these three, and say
which:

1. **A depachika run at 19:15-19:45**, which is the only window that overlaps an
   evening the whole party could still be out. Tight, and only works on days where
   dinner is late or the infants are already out.
2. **One adult going out alone after the infants are down**, roughly 20:00-20:45, to
   a named supermarket near the accommodation. This is the realistic default. Say
   plainly that it costs one adult 45 minutes of their evening.
3. **Buying the next day's lunch rather than tonight's dinner**, which is what the
   timing actually supports on most days.

Add a Transit or Admin row to the schedule for the run where it is a real trip out,
so the time is accounted for rather than assumed free. Name the actual store and its
closing time where you can verify it.

Where a day currently implies hangaku prices but the timing does not work at all,
**raise that meal's cost to the undiscounted price** and update the day and segment
totals. An unachievable discount is a budget error.

---

## Rules that still apply

- Do not edit any `**Running total after Day N**` line; a script recomputes those.
- Keep table formats exactly as they are. The header and lodging blocks now end
  lines with two trailing spaces to force markdown line breaks: **preserve those
  trailing spaces.**
- Planning FX ¥155 = $1. Adult calories stay in the 1,950-2,100 band per day.
- Do not use em dashes. Use " - " or a comma.
- Never invent an address, a fare, or a store's opening hours.
