/**
 * src/http/validation.ts, small shared Zod schemas/helpers for route
 * params and query strings. Request BODIES are validated by the service
 * functions themselves (every `src/services/*.service.ts` function already
 * parses its input with Zod and throws the shared `ValidationError`, see
 * INTERFACES.md), so this file only covers the two things services never
 * see directly: URL path params and query strings, both delivered by
 * Fastify as loosely-typed string maps.
 */
import { z, ZodError } from 'zod';
import { ValidationError } from '../lib/errors.js';

/**
 * Extracts and validates a single uuid path param by name. Deliberately
 * NOT `z.object({ [name]: z.string().uuid() })`, a computed property key
 * makes Zod (and TS) type the result as an index signature
 * (`{ [x: string]: string }`), which under this project's
 * `noUncheckedIndexedAccess` compiler option infers every access as
 * `string | undefined` even though the schema guarantees it's present.
 * Validating the single field directly sidesteps that entirely and returns
 * a plain, always-defined `string`.
 */
export function requireUuidParam(params: unknown, name: string): string {
  const value = (params as Record<string, unknown> | null | undefined)?.[name];
  return parseOrThrow(z.string().uuid(), value);
}

export const paginationQuerySchema = z.object({
  cursor: z.string().optional(),
  limit: z.coerce.number().int().min(1).max(200).optional(),
});

/** Parses `input` with `schema`, translating a ZodError into the shared `ValidationError` so route-level and service-level validation failures produce byte-identical error envelopes. */
export function parseOrThrow<T>(schema: z.ZodType<T, z.ZodTypeDef, unknown>, input: unknown): T {
  try {
    return schema.parse(input);
  } catch (err) {
    if (err instanceof ZodError) {
      throw new ValidationError('Request failed validation.', { issues: err.issues });
    }
    throw err;
  }
}

/** Coerces a Fastify body value to a `Date`, throwing `ValidationError` for anything unparseable. Route bodies carry ISO date strings over JSON; several service schemas (e.g. `dateProposal.proposeDate`) expect a real `Date`. */
export function coerceDate(value: unknown, field: string): Date {
  if (value instanceof Date) return value;
  if (typeof value === 'string' || typeof value === 'number') {
    const d = new Date(value);
    if (!Number.isNaN(d.getTime())) return d;
  }
  throw new ValidationError(`"${field}" must be a valid date.`, { field });
}
