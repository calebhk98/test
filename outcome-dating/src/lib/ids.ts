import { randomUUID, randomBytes } from 'node:crypto';

/** Generate a v4 UUID for use as an application-level id (mirrors DB-side gen_random_uuid()). */
export function newId(): string {
  return randomUUID();
}

/**
 * A short, URL-safe, human-typeable code (Crockford-ish base32, no I/L/O/U)
 * for things a person may need to read aloud or type in, e.g. voucher
 * fallback codes (spec §15.3 "scans or enters code").
 */
const CODE_ALPHABET = '0123456789ABCDEFGHJKMNPQRSTVWXYZ';

export function newHumanCode(length = 8): string {
  const bytes = randomBytes(length);
  let out = '';
  for (let i = 0; i < length; i++) {
    out += CODE_ALPHABET[bytes[i]! % CODE_ALPHABET.length];
  }
  return out;
}
