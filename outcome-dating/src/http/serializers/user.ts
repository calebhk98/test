/**
 * src/http/serializers/user.ts — the account-level (`/me`) view. Never
 * includes `passwordHash` — this is the last-line-of-defence guarantee for
 * that invariant: even if a future route handler carelessly spreads a raw
 * `User` domain object into a response, going through this function instead
 * (an explicit field allowlist, not a spread) makes leaking the hash a
 * one-line diff to notice in review rather than a silent regression.
 */
import type { User } from '../../domain/types.js';

export interface MeView {
  id: string;
  email: string;
  status: User['status'];
  trustLevel: User['trustLevel'];
  emailVerifiedAt: string | null;
  createdAt: string;
  lastActiveAt: string;
}

export function serializeMe(user: User): MeView {
  return {
    id: user.id,
    email: user.email,
    status: user.status,
    trustLevel: user.trustLevel,
    emailVerifiedAt: user.emailVerifiedAt ? user.emailVerifiedAt.toISOString() : null,
    createdAt: user.createdAt.toISOString(),
    lastActiveAt: user.lastActiveAt.toISOString(),
  };
}
