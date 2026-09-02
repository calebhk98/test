import { projectUpcomingSlots } from '../venueSlots';
import type { VenueTimeSlot } from '../../api/types';

describe('projectUpcomingSlots', () => {
  // 2026-09-02 is a Wednesday.
  const from = new Date('2026-09-02T10:00:00');

  it('projects a weekly slot onto every matching upcoming day', () => {
    const slots: VenueTimeSlot[] = [{ dayOfWeek: 3, startMinute: 18 * 60, endMinute: 20 * 60 }]; // Wednesdays 6-8pm
    const result = projectUpcomingSlots(slots, from, 15);
    expect(result.length).toBeGreaterThanOrEqual(2);
    for (const slot of result) {
      expect(slot.start.getDay()).toBe(3);
      expect(slot.start.getHours()).toBe(18);
      expect(slot.end.getHours()).toBe(20);
    }
  });

  it('excludes a slot on the current day that has already passed', () => {
    const slots: VenueTimeSlot[] = [{ dayOfWeek: 3, startMinute: 9 * 60, endMinute: 10 * 60 }]; // Wed 9-10am, already past at 10am `from`
    const result = projectUpcomingSlots(slots, from, 1);
    expect(result).toHaveLength(0);
  });

  it('includes a slot later today', () => {
    const slots: VenueTimeSlot[] = [{ dayOfWeek: 3, startMinute: 14 * 60, endMinute: 15 * 60 }]; // Wed 2-3pm, still ahead
    const result = projectUpcomingSlots(slots, from, 1);
    expect(result).toHaveLength(1);
  });

  it('returns results sorted chronologically', () => {
    const slots: VenueTimeSlot[] = [
      { dayOfWeek: 5, startMinute: 10 * 60, endMinute: 11 * 60 },
      { dayOfWeek: 3, startMinute: 14 * 60, endMinute: 15 * 60 },
    ];
    const result = projectUpcomingSlots(slots, from, 10);
    const times = result.map((s) => s.start.getTime());
    expect(times).toEqual([...times].sort((a, b) => a - b));
  });
});
