/**
 * src/domain/units/bodyType.ts, body type.
 *
 * Not a unit conversion (there is no "canonical" body type to convert
 * to/from), grouped into this module because the product owner's ask
 * ("height, weight, and body type") treats the three as one physical-
 * attributes feature, and because it shares this module's categorical-
 * preference shape: a self-described VALUE, matched against a preference
 * that is a SET of acceptable values (never a numeric midpoint, see
 * `filter.service.ts`'s `body_type` filter, which uses the existing `in`
 * operator against this list, not a range comparison).
 */

export const BODY_TYPES = [
  'slim',
  'athletic',
  'average',
  'curvy',
  'muscular',
  'plus_size',
  'other',
] as const;

export type BodyType = (typeof BODY_TYPES)[number];

export function isBodyType(value: unknown): value is BodyType {
  return typeof value === 'string' && (BODY_TYPES as readonly string[]).includes(value);
}
