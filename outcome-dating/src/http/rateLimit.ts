/**
 * src/http/rateLimit.ts — a tiny in-process sliding-window rate limiter for
 * the HTTP layer.
 *
 * Most of the spec's per-user rate limits (outgoing/daily interest caps
 * §11.2, message throughput + link caps §12.3) are already enforced INSIDE
 * the service layer (`interest.service#sendInterest`,
 * `message.service#sendMessage`) — those are correctly modeled as business
 * rules with DB-backed counts, not HTTP concerns, and this module does not
 * duplicate them.
 *
 * What's missing at the service layer is §19.2 "Device and Network Checks
 * ... rate limiting" for automated/anonymous abuse against endpoints that
 * exist BEFORE a business-rule counter can apply — brute-forcing
 * `/auth/login`, hammering `/auth/register` or `/auth/forgot-password` to
 * enumerate emails or spam resets, or a report-spam flood against
 * `/reports`. This module is that layer: a simple per-key (IP, or IP+route)
 * fixed-window counter, held in memory. No Redis (per INTERFACES.md "no
 * Redis" simplification, mirrored from the jobs scheduler) — each server
 * process has its own counters, which is an acceptable MVP tradeoff for a
 * single-instance deployment and is trivially swappable for a shared store
 * later without changing any call site (see the `RateLimiter` interface).
 */
import { RateLimitError } from '../lib/errors.js';
import type { Clock } from '../lib/time.js';

export interface RateLimitOptions {
  /** Max requests allowed within `windowMs`. */
  max: number;
  windowMs: number;
}

interface Bucket {
  windowStart: number;
  count: number;
}

/** A minimal fixed-window limiter. `check` throws `RateLimitError` once `max` is exceeded within the current window; the window resets on the first call after it elapses. */
export class InMemoryRateLimiter {
  private buckets = new Map<string, Bucket>();

  constructor(private readonly clock: Clock) {}

  check(key: string, opts: RateLimitOptions): void {
    const now = this.clock.now().getTime();
    const existing = this.buckets.get(key);

    if (!existing || now - existing.windowStart >= opts.windowMs) {
      this.buckets.set(key, { windowStart: now, count: 1 });
      return;
    }

    if (existing.count >= opts.max) {
      throw new RateLimitError('Too many requests. Please slow down and try again shortly.', {
        limit: opts.max, windowMs: opts.windowMs,
      });
    }
    existing.count += 1;
  }

  /** Drops all counters — tests use this between scenarios so one test's abuse doesn't bleed into the next. */
  reset(): void {
    this.buckets.clear();
  }
}
