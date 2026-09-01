/**
 * src/domain/units/brand.ts — nominal ("branded") numeric types.
 *
 * Not part of the original spec (no § reference) — added for this build
 * to make "a value in one unit gets used as another" a TYPE ERROR instead
 * of a runtime bug, which is the whole point of this module (see the
 * incident this task exists to fix: distance silently swapping between
 * km and miles with nothing in the type system to catch it).
 *
 * A plain `number` carries no unit information, so `heightCm: number` and
 * `heightInches: number` are mutually assignable — TypeScript cannot tell
 * them apart, and neither can a careless `return a + b`. Branding tags
 * each unit with a distinct string literal at the type level only (zero
 * runtime cost, zero runtime representation — a branded value IS its
 * underlying number at runtime, `JSON.stringify`/`pg` see a plain number)
 * so `Brand<number, 'Kilometres'>` and `Brand<number, 'Miles'>` become
 * mutually non-assignable even though both compile to a `number`.
 *
 * The brand key is a `unique symbol` that is never exported, so the ONLY
 * way to mint a branded value from a raw number is to go through this
 * module's `brand()` helper — and in practice, through each unit file's
 * own named constructor (`kilometres()`, `centimetres()`, `grams()`, ...)
 * that wraps it with the range/integer validation for that measure. There
 * is no `as Kilometres` anywhere outside `distance.ts` for exactly this
 * reason: every place a branded value is created is auditable in one
 * file per unit.
 */

declare const UNIT_BRAND: unique symbol;

/** A `Value` tagged with `Tag` at the type level. `Tag` is a distinct string literal per unit (e.g. 'Kilometres', 'Miles', 'Centimetres') — two different tags make two `Brand<number, Tag>` types mutually non-assignable, which is the entire mechanism this module exists to provide. */
export type Brand<Value, Tag extends string> = Value & { readonly [UNIT_BRAND]: Tag };

/**
 * Casts a raw value into a branded type. Intentionally the ONLY function
 * in this file — every unit module calls this once, inside its own
 * validating constructor, rather than every call site doing its own
 * unchecked `as` cast. Not re-exported from `index.ts`: consumers of the
 * units module mint branded values only through `kilometres()`,
 * `centimetres()`, `grams()`, etc.
 */
export function brand<Value, Tag extends string>(value: Value): Brand<Value, Tag> {
  return value as Brand<Value, Tag>;
}
