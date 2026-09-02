import { calculateAge, isAtLeastMinimumAge, MINIMUM_AGE } from '../age';

describe('calculateAge', () => {
  const today = new Date('2026-09-02T12:00:00Z');

  it('computes age when the birthday already happened this year', () => {
    expect(calculateAge('2000-01-01', today)).toBe(26);
  });

  it('computes age when the birthday has not happened yet this year', () => {
    expect(calculateAge('2000-12-31', today)).toBe(25);
  });

  it('treats a birthday that is today as already happened', () => {
    expect(calculateAge('2008-09-02', today)).toBe(18);
  });

  it('returns null for malformed input', () => {
    expect(calculateAge('not-a-date', today)).toBeNull();
    expect(calculateAge('2020-13-40', today)).toBeNull();
  });

  it('returns null for a birthdate in the future', () => {
    expect(calculateAge('2030-01-01', today)).toBeNull();
  });

  it('rejects a calendar date that does not exist (e.g. day 31 in a 30-day month)', () => {
    expect(calculateAge('2020-04-31', today)).toBeNull();
  });
});

describe('isAtLeastMinimumAge', () => {
  const today = new Date('2026-09-02T12:00:00Z');

  it('accepts someone exactly the minimum age today', () => {
    expect(isAtLeastMinimumAge('2008-09-02', today)).toBe(true);
  });

  it('rejects someone who turns the minimum age tomorrow', () => {
    expect(isAtLeastMinimumAge('2008-09-03', today)).toBe(false);
  });

  it(`rejects someone under ${MINIMUM_AGE}`, () => {
    expect(isAtLeastMinimumAge('2015-01-01', today)).toBe(false);
  });
});
