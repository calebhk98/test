/**
 * Typed application error hierarchy.
 *
 * Every service-layer failure that should reach an HTTP response MUST be
 * (or wrap into) an `AppError` subclass so the HTTP layer can map it to a
 * status code and a stable machine-readable `code` without string-sniffing
 * messages. `code` values are part of the API contract (spec §24) and MUST
 * NOT change once shipped.
 */

/** Base class for all expected/typed application errors. */
export abstract class AppError extends Error {
  /** HTTP status code the API layer should respond with. */
  abstract readonly status: number;
  /** Stable machine-readable error code, e.g. "not_found". Part of the API contract. */
  abstract readonly code: string;
  /** Extra structured detail safe to serialize to the client (e.g. field errors). */
  readonly details?: unknown;

  constructor(message: string, details?: unknown) {
    super(message);
    this.name = new.target.name;
    this.details = details;
    Error.captureStackTrace?.(this, new.target);
  }

  /** Shape suitable for an API error response body. */
  toJSON(): { code: string; message: string; details?: unknown } {
    return { code: this.code, message: this.message, details: this.details };
  }
}

/** Request failed validation (bad input shape, out-of-range value, etc). */
export class ValidationError extends AppError {
  readonly status = 400;
  readonly code = 'validation_error';
}

/** Caller is not authenticated, or credentials/token are invalid or expired. */
export class UnauthorizedError extends AppError {
  readonly status = 401;
  readonly code = 'unauthorized';
}

/** Caller is authenticated but not allowed to perform this action. */
export class ForbiddenError extends AppError {
  readonly status = 403;
  readonly code = 'forbidden';
}

/** Requested entity does not exist (or is not visible to the caller). */
export class NotFoundError extends AppError {
  readonly status = 404;
  readonly code = 'not_found';
}

/** Request conflicts with current state (e.g. duplicate email, stale status transition). */
export class ConflictError extends AppError {
  readonly status = 409;
  readonly code = 'conflict';
}

/** Caller exceeded a configured rate/capacity limit (spec §11.2, §12.3, etc). */
export class RateLimitError extends AppError {
  readonly status = 429;
  readonly code = 'rate_limited';
}

/** Payment authorization/capture/refund failure (spec §14). */
export class PaymentError extends AppError {
  readonly status = 402;
  readonly code = 'payment_error';
}

/**
 * Marks a stub body in the foundation layer. Parallel agents replace the
 * body that throws this; the signature and JSDoc above it are the contract.
 * Deliberately NOT an AppError subclass — it must never be caught and
 * turned into a graceful API response. It should crash loudly in dev/test
 * so an unimplemented path is never mistaken for a working one.
 */
export class NotImplementedError extends Error {
  constructor(what: string) {
    super(`Not implemented: ${what}`);
    this.name = 'NotImplementedError';
  }
}
