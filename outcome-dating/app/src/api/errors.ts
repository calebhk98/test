/**
 * Error code -> human sentence.
 *
 * The server's error envelope (`AppError#toJSON` in the backend's
 * src/lib/errors.ts) carries a stable machine `code` plus a `message`
 * that is sometimes a genuinely safe sentence and sometimes an internal
 * diagnostic string (spec-section citations, raw state-machine names,
 * see docs/ux-api-review.md "Error messages still leak internal
 * vocabulary to the wire"). This module is the one place that decides
 * what a person actually sees: known codes get a written, reviewed
 * sentence; anything unrecognised falls back to one calm generic line
 * rather than the raw `message` field.
 */
import type { ApiErrorBody } from './types';

export class ApiError extends Error {
  readonly code: string;
  readonly status: number;
  readonly details?: unknown;

  constructor(status: number, body: ApiErrorBody) {
    super(body.message);
    this.name = 'ApiError';
    this.status = status;
    this.code = body.code;
    this.details = body.details;
  }
}

/** Raised by the client itself, never the server: no connection, or a response that could not be parsed at all. */
export class NetworkError extends Error {
  constructor(message = 'offline') {
    super(message);
    this.name = 'NetworkError';
  }
}

const GENERIC_FALLBACK = "Something didn't go through. Please try again.";

const CODE_MESSAGES: Record<string, string> = {
  validation_error: "That doesn't look right. Please check what you entered and try again.",
  unauthorized: 'Please sign in again to continue.',
  forbidden: "You don't have access to do that.",
  not_found: "We couldn't find that. It may have been removed.",
  conflict: 'Someone may have already acted on this, or it changed while you were looking. Refresh and try again.',
  rate_limited: "You've reached today's limit for this. Please try again later.",
  payment_error: "We couldn't reach your card. Nothing was charged. Please try again or use a different card.",
};

/** Specific, friendlier overrides keyed by `${code}:${details.kind}`, for the handful of moments the product review calls out by name. */
const DETAIL_MESSAGES: Record<string, string> = {
  'rate_limited:daily_outgoing': "You've sent as many interests as you can for today. It resets tomorrow.",
};

export function messageForError(error: unknown): string {
  if (error instanceof ApiError) {
    const details = error.details as { kind?: string } | undefined;
    if (details?.kind) {
      const detailed = DETAIL_MESSAGES[`${error.code}:${details.kind}`];
      if (detailed) return detailed;
    }
    return CODE_MESSAGES[error.code] ?? GENERIC_FALLBACK;
  }
  if (error instanceof NetworkError) {
    return "You're offline. Check your connection and try again.";
  }
  return GENERIC_FALLBACK;
}

export function isOffline(error: unknown): boolean {
  return error instanceof NetworkError;
}
