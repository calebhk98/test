/**
 * Projects a venue's weekly time-slot template (`dayOfWeek` +
 * start/end minute, the shape `GET /venues/:id/time-slots` returns)
 * forward into concrete, pickable datetimes. The server only ever
 * describes a venue's recurring weekly availability, not a list of
 * open appointments, so turning "Saturdays 14:00-18:00" into "Saturday
 * the 6th, 2:00 PM" for the next couple of weeks is a client-side,
 * pure, and therefore testable, projection.
 */
import type { VenueTimeSlot } from '../api/types';

export interface ConcreteSlot {
  start: Date;
  end: Date;
}

const MINUTES_PER_DAY = 24 * 60;

/** Every concrete occurrence of `slots` within `[from, from + days)`, sorted chronologically, one hour granularity is not assumed, exact start/end minute is preserved. */
export function projectUpcomingSlots(slots: VenueTimeSlot[], from: Date, days = 14): ConcreteSlot[] {
  const results: ConcreteSlot[] = [];
  const start = new Date(from);
  start.setSeconds(0, 0);

  for (let dayOffset = 0; dayOffset < days; dayOffset++) {
    const day = new Date(start);
    day.setDate(day.getDate() + dayOffset);
    const dayOfWeek = day.getDay();

    for (const slot of slots) {
      if (slot.dayOfWeek !== dayOfWeek) continue;
      const slotStart = atMidnightPlusMinutes(day, slot.startMinute);
      const slotEnd = atMidnightPlusMinutes(day, slot.endMinute);
      if (slotStart.getTime() < from.getTime()) continue;
      results.push({ start: slotStart, end: slotEnd });
    }
  }

  return results.sort((a, b) => a.start.getTime() - b.start.getTime());
}

function atMidnightPlusMinutes(day: Date, minutes: number): Date {
  const d = new Date(day);
  d.setHours(0, 0, 0, 0);
  d.setMinutes(minutes % MINUTES_PER_DAY);
  return d;
}
