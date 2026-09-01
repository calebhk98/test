import bcrypt from 'bcryptjs';
import { createHash } from 'node:crypto';

/**
 * Password hashing (spec §28.1: "Use Argon2id or bcrypt"). We use bcrypt via
 * `bcryptjs` (pure JS, no native build step) rather than Argon2id to keep
 * the foundation layer install-free in this environment; swapping to a
 * native argon2 binding later is a one-file change confined to this module.
 */
const BCRYPT_COST = 12;

export async function hashPassword(plain: string): Promise<string> {
  return bcrypt.hash(plain, BCRYPT_COST);
}

export async function verifyPassword(plain: string, hash: string): Promise<boolean> {
  return bcrypt.compare(plain, hash);
}

/**
 * SHA-256 hex digest. Used for non-secret content addressing, e.g. refresh
 * token lookup keys (store the hash, not the raw token) and perceptual/
 * duplicate-image hash inputs (spec §7.2, §18.2) upstream of the real
 * perceptual-hash algorithm the media moderation adapter plugs in.
 */
export function sha256Hex(input: string | Buffer): string {
  return createHash('sha256').update(input).digest('hex');
}
