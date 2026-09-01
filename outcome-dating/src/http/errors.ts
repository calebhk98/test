/**
 * src/http/errors.ts — maps the typed `AppError` hierarchy
 * (`src/lib/errors.ts`, frozen/shared infra) plus raw Zod errors onto a
 * single, stable HTTP error envelope:
 *
 *   { "error": { "code": "validation_error", "message": "...", "details"?: ... } }
 *
 * Every route handler in this codebase is expected to let a thrown
 * `AppError` (or `ZodError`) propagate — Fastify's `setErrorHandler` (wired
 * in `server.ts`) is the ONE place that translates it into a response, so
 * every route gets the same envelope/status mapping for free rather than
 * each handler hand-rolling try/catch.
 */
import type { FastifyReply, FastifyRequest } from 'fastify';
import { ZodError } from 'zod';
import { AppError, NotImplementedError } from '../lib/errors.js';

export interface ErrorEnvelope {
  error: {
    code: string;
    message: string;
    details?: unknown;
  };
}

export function envelope(code: string, message: string, details?: unknown): ErrorEnvelope {
  return details === undefined ? { error: { code, message } } : { error: { code, message, details } };
}

/** Flattens a ZodError into the same `{code, message, details}` shape services' own ValidationError carries, so callers can't tell whether a 400 came from route-level or service-level validation. */
function zodToEnvelope(err: ZodError): ErrorEnvelope {
  return envelope('validation_error', 'Request failed validation.', { issues: err.issues });
}

export function fastifyErrorHandler(err: unknown, req: FastifyRequest, reply: FastifyReply): void {
  if (err instanceof AppError) {
    req.log?.debug?.({ code: err.code, err: err.message }, 'app_error');
    reply.status(err.status).send(envelope(err.code, err.message, err.details));
    return;
  }

  if (err instanceof ZodError) {
    reply.status(400).send(zodToEnvelope(err));
    return;
  }

  if (err instanceof NotImplementedError) {
    // A service this build depends on hasn't landed its body yet (payments
    // agent may still be in flight — see task brief). Surface as 503 with a
    // stable code rather than a raw 500/stack trace.
    reply.status(503).send(envelope('not_implemented', err.message));
    return;
  }

  // Fastify's own request-level errors (malformed JSON body, etc.) carry a
  // `statusCode`/`code` — honor them if present rather than collapsing
  // everything to 500.
  const maybeFastifyErr = err as { statusCode?: number; code?: string; message?: string };
  if (typeof maybeFastifyErr.statusCode === 'number' && maybeFastifyErr.statusCode >= 400 && maybeFastifyErr.statusCode < 500) {
    reply
      .status(maybeFastifyErr.statusCode)
      .send(envelope(maybeFastifyErr.code ?? 'bad_request', maybeFastifyErr.message ?? 'Bad request.'));
    return;
  }

  req.log?.error?.({ err }, 'unhandled_error');
  // eslint-disable-next-line no-console
  console.error('unhandled_error', err);
  reply.status(500).send(envelope('internal_error', 'An unexpected error occurred.'));
}
