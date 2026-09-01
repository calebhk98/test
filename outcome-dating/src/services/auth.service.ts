import type { Ctx } from '../lib/ctx.js';
import { NotImplementedError } from '../lib/errors.js';
import type { AuthTokens, User } from '../domain/types.js';

/**
 * auth.service — account creation, login, and token lifecycle.
 * Spec: §5 (signup/verification), §24.1 (routes), §28.1-§28.2 (password/token security).
 *
 * Owning agent: A.
 *
 * Invariants this module MUST uphold (see INTERFACES.md):
 *  - No phone number or government ID is ever required (§5.2, §5.3).
 *  - `register` rejects under-18 signups (also enforced by the `users_min_age`
 *    DB check constraint — this is defense in depth, not the only gate).
 *  - Passwords are hashed with `src/lib/hash.ts` (bcrypt) — the plaintext
 *    password never reaches storage or logs.
 *  - `refresh` rotates the refresh token (old one is invalidated) so reuse
 *    of a stolen-then-superseded refresh token is detectable (§28.2).
 *
 * Callers: every other module receives an already-authenticated `Ctx`
 * (HTTP middleware calls `verifyAccessToken` once per request and builds
 * `ctx.actor` from the result) — no other service should import this
 * module.
 */

export interface RegisterInput {
  email: string;
  password: string;
  /** ISO date (YYYY-MM-DD). */
  birthdate: string;
  acceptedTermsAt: Date;
  city?: string;
  locationPermissionGranted?: boolean;
}

export interface LoginInput {
  email: string;
  password: string;
  deviceFingerprint?: string;
  ipAddress?: string;
}

/**
 * Create a new account. Requires §5.1's five fields; enforces the §5.1
 * minimum age of 18. Does NOT create a `profiles` row — profile setup is a
 * separate step (`profile.service.ts`) per the Phase 1 exit criteria
 * ("user can register" is distinct from "user can create profile").
 */
export async function register(ctx: Ctx, input: RegisterInput): Promise<{ user: User; tokens: AuthTokens }> {
  throw new NotImplementedError('auth.register');
}

export async function login(ctx: Ctx, input: LoginInput): Promise<{ user: User; tokens: AuthTokens }> {
  throw new NotImplementedError('auth.login');
}

/** Invalidates the given refresh token (and, by extension, its session). */
export async function logout(ctx: Ctx, input: { refreshToken: string }): Promise<void> {
  throw new NotImplementedError('auth.logout');
}

/** Rotates a refresh token for a new access+refresh pair. Throws UnauthorizedError if the refresh token is invalid, expired, or already rotated (reuse detection). */
export async function refresh(ctx: Ctx, input: { refreshToken: string }): Promise<AuthTokens> {
  throw new NotImplementedError('auth.refresh');
}

export async function forgotPassword(ctx: Ctx, input: { email: string }): Promise<void> {
  throw new NotImplementedError('auth.forgotPassword');
}

export async function resetPassword(ctx: Ctx, input: { resetToken: string; newPassword: string }): Promise<void> {
  throw new NotImplementedError('auth.resetPassword');
}

/**
 * Verify a compact access token (see `src/lib/signing.ts`) and return the
 * subject. HTTP middleware calls this once per authenticated request to
 * build `ctx.actor`. Throws `UnauthorizedError` (not `InvalidSignatureError`
 * — that's an implementation detail this function should catch and
 * translate) on any invalid/expired token.
 */
export async function verifyAccessToken(ctx: Ctx, accessToken: string): Promise<{ userId: string }> {
  throw new NotImplementedError('auth.verifyAccessToken');
}
