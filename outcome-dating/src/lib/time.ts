/**
 * Clock abstraction so jobs, expiry logic, and tests never call `Date.now()`
 * or `new Date()` directly. Pass a `Clock` through `Ctx` (see src/lib/ctx.ts)
 * and services read time from it. Tests use `FixedClock`/`ManualClock` to
 * control expiry (interest expiry, date-proposal expiry, chat decay,
 * voucher expiry — spec §25) deterministically.
 */
export interface Clock {
  /** Current time. */
  now(): Date;
}

/** Real wall-clock time. Used in production/dev. */
export class SystemClock implements Clock {
  now(): Date {
    return new Date();
  }
}

/**
 * A controllable clock for tests. Starts at `initial` (or the current time)
 * and only moves when `advance`/`set` is called explicitly.
 */
export class ManualClock implements Clock {
  private current: Date;

  constructor(initial: Date = new Date()) {
    this.current = initial;
  }

  now(): Date {
    return this.current;
  }

  set(date: Date): void {
    this.current = date;
  }

  advanceMs(ms: number): void {
    this.current = new Date(this.current.getTime() + ms);
  }

  advanceHours(hours: number): void {
    this.advanceMs(hours * 60 * 60 * 1000);
  }

  advanceDays(days: number): void {
    this.advanceMs(days * 24 * 60 * 60 * 1000);
  }
}

export function addHours(date: Date, hours: number): Date {
  return new Date(date.getTime() + hours * 60 * 60 * 1000);
}

export function addDays(date: Date, days: number): Date {
  return new Date(date.getTime() + days * 24 * 60 * 60 * 1000);
}

export function hoursBetween(a: Date, b: Date): number {
  return (b.getTime() - a.getTime()) / (60 * 60 * 1000);
}
