import { z } from 'zod';
import type { Ctx } from '../lib/ctx.js';
import { ConflictError, ForbiddenError, UnauthorizedError, ValidationError } from '../lib/errors.js';
import { hashPassword, verifyPassword, sha256Hex } from '../lib/hash.js';
import { sign, verify, InvalidSignatureError } from '../lib/signing.js';
import { newId, newHumanCode } from '../lib/ids.js';
import { getEnv } from '../config/env.js';
import type { AccessTokenPayload, AuthTokens, RefreshTokenPayload, User, UserStatus } from '../domain/types.js';

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
 *
 * Beyond the frozen export list, this file adds `requestEmailVerification`
 * and `verifyEmail` (§6.2 email-verification trust signal — "issue/consume"
 * per the build brief). Nothing in INTERFACES.md's "may call" graph lists
 * anyone importing `auth.service`, so these additions are safe: they don't
 * change any signature another agent's code depends on. The API agent
 * needs to wire routes for these two (e.g. `POST /auth/verify-email`,
 * `POST /auth/resend-verification`) — flagged in the build report.
 */

// =====================================================================
// Local (non-shared-config) tunables. `src/config/config.service.ts` is
// shared infra outside this agent's ownership; these two TTLs are simple
// enough to keep as file-local constants rather than proposing new global
// config keys for a single-consumer value.
// =====================================================================
const PASSWORD_RESET_TOKEN_TTL_HOURS = 2;
const EMAIL_VERIFICATION_TOKEN_TTL_HOURS = 48;

function authSecret(): string {
  return getEnv().AUTH_TOKEN_SECRET;
}

function normalizeEmail(email: string): string {
  return email.trim().toLowerCase();
}

// =====================================================================
// Zod input schemas
// =====================================================================

const RegisterSchema = z.object({
  email: z.string().trim().email().max(320),
  password: z.string().min(8).max(200),
  // ISO date, YYYY-MM-DD (§5.1).
  birthdate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'birthdate must be an ISO date (YYYY-MM-DD)'),
  acceptedTermsAt: z.date(),
  city: z.string().trim().min(1).max(200).optional(),
  locationPermissionGranted: z.boolean().optional(),
});

const LoginSchema = z.object({
  email: z.string().trim().email().max(320),
  password: z.string().min(1),
  deviceFingerprint: z.string().max(500).optional(),
  ipAddress: z.string().max(64).optional(),
});

const ForgotPasswordSchema = z.object({
  email: z.string().trim().email().max(320),
});

const ResetPasswordSchema = z.object({
  resetToken: z.string().min(1),
  newPassword: z.string().min(8).max(200),
});

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

// =====================================================================
// Row mapping
// =====================================================================

interface UserRow {
  id: string;
  email: string;
  password_hash: string;
  birthdate: string;
  status: UserStatus;
  trust_score: number;
  trust_level: User['trustLevel'];
  shadowbanned: boolean;
  suspended: boolean;
  email_verified_at: Date | null;
  created_at: Date;
  last_active_at: Date;
}

function mapUser(row: UserRow): User {
  return {
    id: row.id,
    email: row.email,
    passwordHash: row.password_hash,
    birthdate: row.birthdate,
    status: row.status,
    trustScore: row.trust_score,
    trustLevel: row.trust_level,
    shadowbanned: row.shadowbanned,
    suspended: row.suspended,
    emailVerifiedAt: row.email_verified_at,
    createdAt: row.created_at,
    lastActiveAt: row.last_active_at,
  };
}

// =====================================================================
// Age (§5.1 "at least 18 years old", computed from birthdate)
// =====================================================================

/** Whole years between `birthdate` (YYYY-MM-DD) and `asOf`, both treated as UTC calendar dates — exact-18-today passes, one day short fails. */
export function calculateAge(birthdate: string, asOf: Date): number {
  const [by, bm, bd] = birthdate.split('-').map(Number) as [number, number, number];
  const ay = asOf.getUTCFullYear();
  const am = asOf.getUTCMonth() + 1;
  const ad = asOf.getUTCDate();

  let age = ay - by;
  if (am < bm || (am === bm && ad < bd)) age -= 1;
  return age;
}

const MIN_AGE_YEARS = 18;

// =====================================================================
// Token issuance
// =====================================================================

function issueTokens(ctx: Ctx, userId: string, sessionId: string): AuthTokens {
  const env = getEnv();
  const nowSec = Math.floor(ctx.clock.now().getTime() / 1000);
  const accessExpSec = nowSec + env.ACCESS_TOKEN_TTL_MINUTES * 60;
  const refreshExpSec = nowSec + env.REFRESH_TOKEN_TTL_DAYS * 24 * 60 * 60;

  // `jti` (a random nonce, not part of the domain `*TokenPayload` shape —
  // added structurally here rather than by editing the shared
  // `domain/types.ts`) guarantees two tokens signed within the same clock
  // second are never byte-identical. Without it, two rotations in the same
  // second (a real possibility — this is exactly what `refresh` does twice
  // in a row) would produce the *same* compact token both times, which
  // would silently defeat reuse detection (the "old" and "new" refresh
  // token would be indistinguishable). `verify<...Payload>` below simply
  // ignores the extra field.
  const access = sign<AccessTokenPayload & { jti: string }>(
    { sub: userId, kind: 'access', iat: nowSec, exp: accessExpSec, jti: newId() },
    authSecret(),
  );
  const refresh = sign<RefreshTokenPayload & { jti: string }>(
    { sub: userId, kind: 'refresh', sessionId, iat: nowSec, exp: refreshExpSec, jti: newId() },
    authSecret(),
  );

  return {
    accessToken: access.compact,
    refreshToken: refresh.compact,
    accessTokenExpiresAt: new Date(accessExpSec * 1000),
    refreshTokenExpiresAt: new Date(refreshExpSec * 1000),
  };
}

async function createRefreshSession(ctx: Ctx, userId: string): Promise<AuthTokens> {
  const sessionId = newId();
  const tokens = issueTokens(ctx, userId, sessionId);
  await ctx.db.query(
    `INSERT INTO refresh_sessions (id, user_id, token_hash, created_at, expires_at)
     VALUES ($1, $2, $3, $4, $5)`,
    [sessionId, userId, sha256Hex(tokens.refreshToken), ctx.clock.now(), tokens.refreshTokenExpiresAt],
  );
  return tokens;
}

// =====================================================================
// register / login / logout / refresh
// =====================================================================

/**
 * Create a new account. Requires §5.1's five fields; enforces the §5.1
 * minimum age of 18. Does NOT create a `profiles` row — profile setup is a
 * separate step (`profile.service.ts`) per the Phase 1 exit criteria
 * ("user can register" is distinct from "user can create profile").
 */
export async function register(ctx: Ctx, input: RegisterInput): Promise<{ user: User; tokens: AuthTokens }> {
  const parsed = RegisterSchema.parse(input);

  // §5.1 rule 5: "Location permission OR manually entered city."
  if (!parsed.city && !parsed.locationPermissionGranted) {
    throw new ValidationError('Either a city or location permission is required.');
  }

  if (Number.isNaN(parsed.acceptedTermsAt.getTime())) {
    throw new ValidationError('acceptedTermsAt must be a valid date.');
  }
  if (parsed.acceptedTermsAt.getTime() > ctx.clock.now().getTime() + 60_000) {
    throw new ValidationError('acceptedTermsAt cannot be in the future.');
  }

  // §5.1 "MUST be at least 18 years old" — app-level gate, checked against
  // ctx.clock (never Date.now()) so tests control "today". This is a hard
  // short-circuit before any DB write; the `users_min_age` CHECK constraint
  // (which uses real wall-clock CURRENT_DATE) is defense in depth only —
  // this check must never rely on that constraint to catch anything.
  const age = calculateAge(parsed.birthdate, ctx.clock.now());
  if (age < MIN_AGE_YEARS) {
    throw new ValidationError(`Must be at least ${MIN_AGE_YEARS} years old to register.`, { minAge: MIN_AGE_YEARS });
  }

  const email = normalizeEmail(parsed.email);

  const { rows: existing } = await ctx.db.query<{ id: string }>('SELECT id FROM users WHERE email = $1', [email]);
  if (existing.length > 0) {
    throw new ConflictError('An account with this email already exists.');
  }

  const passwordHash = await hashPassword(parsed.password);
  const now = ctx.clock.now();

  const { rows } = await ctx.db.query<UserRow>(
    `INSERT INTO users
       (email, password_hash, birthdate, status, trust_score, trust_level, shadowbanned, suspended, email_verified_at, terms_accepted_at, created_at, last_active_at)
     VALUES ($1, $2, $3, 'active', 50, 'standard', false, false, NULL, $4, $5, $5)
     RETURNING id, email, password_hash, birthdate::text, status, trust_score, trust_level, shadowbanned, suspended, email_verified_at, created_at, last_active_at`,
    [email, passwordHash, parsed.birthdate, parsed.acceptedTermsAt, now],
  );
  const user = mapUser(rows[0]!);

  // Issue an email-verification token immediately (§6.2). Delivery (the
  // actual email send) is out of scope for this leaf module; the raw token
  // is intentionally not returned here (see `requestEmailVerification` for
  // the resend path a logged-in user/API layer can call).
  await createEmailVerificationToken(ctx, user.id);

  const tokens = await createRefreshSession(ctx, user.id);
  return { user, tokens };
}

export async function login(ctx: Ctx, input: LoginInput): Promise<{ user: User; tokens: AuthTokens }> {
  const parsed = LoginSchema.parse(input);
  const email = normalizeEmail(parsed.email);

  const { rows } = await ctx.db.query<UserRow>(
    `SELECT id, email, password_hash, birthdate::text, status, trust_score, trust_level, shadowbanned, suspended, email_verified_at, created_at, last_active_at
     FROM users WHERE email = $1`,
    [email],
  );
  const row = rows[0];

  let passwordOk = false;
  if (row) {
    passwordOk = await verifyPassword(parsed.password, row.password_hash);
  }
  const success = Boolean(row) && passwordOk && row!.status === 'active';

  // §23.2 user_auth_events — recorded for both success and failure so the
  // trust/moderation agents can see login attempts, per §6.2/§18.2 device
  // and velocity signals. `user_id` is null for an unknown email.
  await ctx.db.query(
    `INSERT INTO user_auth_events (user_id, device_fingerprint, ip_address, login_at, success)
     VALUES ($1, $2, $3, $4, $5)`,
    [row?.id ?? null, parsed.deviceFingerprint ?? null, parsed.ipAddress ?? null, ctx.clock.now(), success],
  );

  if (!row || !passwordOk) {
    throw new UnauthorizedError('Invalid email or password.');
  }
  if (row.status === 'deleted') {
    // Don't distinguish "deleted" from "wrong password" to the caller.
    throw new UnauthorizedError('Invalid email or password.');
  }
  if (row.status === 'suspended') {
    throw new ForbiddenError('This account is suspended.');
  }

  await ctx.db.query('UPDATE users SET last_active_at = $2 WHERE id = $1', [row.id, ctx.clock.now()]);

  const user = mapUser({ ...row, status: 'active' });
  const tokens = await createRefreshSession(ctx, user.id);
  return { user, tokens };
}

/** Invalidates the given refresh token (and, by extension, its session). */
export async function logout(ctx: Ctx, input: { refreshToken: string }): Promise<void> {
  let payload: RefreshTokenPayload;
  try {
    payload = verify<RefreshTokenPayload>(input.refreshToken, authSecret());
  } catch {
    // Logging out with an already-garbage token is a no-op, not an error —
    // the caller's goal (no valid session) is already achieved.
    return;
  }
  if (payload.kind !== 'refresh') return;

  await ctx.db.query(
    `UPDATE refresh_sessions SET revoked_at = $2 WHERE id = $1 AND revoked_at IS NULL`,
    [payload.sessionId, ctx.clock.now()],
  );
}

/** Rotates a refresh token for a new access+refresh pair. Throws UnauthorizedError if the refresh token is invalid, expired, or already rotated (reuse detection). */
export async function refresh(ctx: Ctx, input: { refreshToken: string }): Promise<AuthTokens> {
  let payload: RefreshTokenPayload;
  try {
    payload = verify<RefreshTokenPayload>(input.refreshToken, authSecret());
  } catch {
    throw new UnauthorizedError('Invalid refresh token.');
  }
  if (payload.kind !== 'refresh') {
    throw new UnauthorizedError('Invalid refresh token.');
  }

  const now = ctx.clock.now();
  if (payload.exp * 1000 < now.getTime()) {
    throw new UnauthorizedError('Refresh token expired.');
  }

  const { rows } = await ctx.db.query<{
    id: string;
    user_id: string;
    token_hash: string;
    expires_at: Date;
    revoked_at: Date | null;
  }>(
    `SELECT id, user_id, token_hash, expires_at, revoked_at FROM refresh_sessions WHERE id = $1`,
    [payload.sessionId],
  );
  const session = rows[0];
  if (!session || session.user_id !== payload.sub) {
    throw new UnauthorizedError('Invalid refresh token.');
  }
  if (session.revoked_at) {
    throw new UnauthorizedError('Refresh session has been revoked.');
  }
  if (session.expires_at.getTime() < now.getTime()) {
    throw new UnauthorizedError('Refresh session expired.');
  }

  const presentedHash = sha256Hex(input.refreshToken);
  if (presentedHash !== session.token_hash) {
    // §28.2: reuse of an already-rotated (stale) refresh token. Treat as a
    // compromise signal and kill the whole session rather than silently
    // rejecting just this call.
    await ctx.db.query('UPDATE refresh_sessions SET revoked_at = $2 WHERE id = $1', [session.id, now]);
    throw new UnauthorizedError('Refresh token reuse detected; session revoked.');
  }

  const newTokens = issueTokens(ctx, session.user_id, session.id);
  await ctx.db.query(
    `UPDATE refresh_sessions SET token_hash = $2, rotated_at = $3, expires_at = $4 WHERE id = $1`,
    [session.id, sha256Hex(newTokens.refreshToken), now, newTokens.refreshTokenExpiresAt],
  );

  return newTokens;
}

// =====================================================================
// Password reset
// =====================================================================

export async function forgotPassword(ctx: Ctx, input: { email: string }): Promise<void> {
  const { email: rawEmail } = ForgotPasswordSchema.parse(input);
  const email = normalizeEmail(rawEmail);

  const { rows } = await ctx.db.query<{ id: string }>(
    `SELECT id FROM users WHERE email = $1 AND status = 'active'`,
    [email],
  );
  if (rows.length === 0) {
    // Do not leak whether an email is registered.
    return;
  }
  const userId = rows[0]!.id;

  const rawToken = newHumanCode(32);
  const tokenHash = sha256Hex(rawToken);
  const expiresAt = new Date(ctx.clock.now().getTime() + PASSWORD_RESET_TOKEN_TTL_HOURS * 60 * 60 * 1000);

  await ctx.db.query(
    `INSERT INTO password_reset_tokens (user_id, token_hash, created_at, expires_at) VALUES ($1, $2, $3, $4)`,
    [userId, tokenHash, ctx.clock.now(), expiresAt],
  );

  // Delivery (emailing `rawToken`) is out of scope for this leaf module —
  // a real deployment wires this through an email sender. Never log the
  // raw token (it's a bearer credential for the account).
  ctx.logger.info('auth.password_reset_requested', { userId });
}

export async function resetPassword(ctx: Ctx, input: { resetToken: string; newPassword: string }): Promise<void> {
  const parsed = ResetPasswordSchema.parse(input);
  const tokenHash = sha256Hex(parsed.resetToken);

  const { rows } = await ctx.db.query<{ id: string; user_id: string; expires_at: Date; consumed_at: Date | null }>(
    `SELECT id, user_id, expires_at, consumed_at FROM password_reset_tokens WHERE token_hash = $1`,
    [tokenHash],
  );
  const row = rows[0];
  if (!row) {
    throw new UnauthorizedError('Invalid or expired reset token.');
  }
  if (row.consumed_at) {
    throw new UnauthorizedError('This reset token has already been used.');
  }
  if (row.expires_at.getTime() < ctx.clock.now().getTime()) {
    throw new UnauthorizedError('This reset token has expired.');
  }

  const passwordHash = await hashPassword(parsed.newPassword);
  const now = ctx.clock.now();

  await ctx.db.query('UPDATE users SET password_hash = $2 WHERE id = $1', [row.user_id, passwordHash]);
  await ctx.db.query('UPDATE password_reset_tokens SET consumed_at = $2 WHERE id = $1', [row.id, now]);
  // A password reset invalidates every existing session (§28.2 defense in depth).
  await ctx.db.query(
    `UPDATE refresh_sessions SET revoked_at = $2 WHERE user_id = $1 AND revoked_at IS NULL`,
    [row.user_id, now],
  );
}

// =====================================================================
// Email verification (§6.2 trust signal)
// =====================================================================

async function createEmailVerificationToken(ctx: Ctx, userId: string): Promise<{ token: string; expiresAt: Date }> {
  const rawToken = newHumanCode(32);
  const tokenHash = sha256Hex(rawToken);
  const expiresAt = new Date(ctx.clock.now().getTime() + EMAIL_VERIFICATION_TOKEN_TTL_HOURS * 60 * 60 * 1000);

  await ctx.db.query(
    `INSERT INTO email_verification_tokens (user_id, token_hash, created_at, expires_at) VALUES ($1, $2, $3, $4)`,
    [userId, tokenHash, ctx.clock.now(), expiresAt],
  );

  return { token: rawToken, expiresAt };
}

/** (Re)issues an email verification token for the logged-in caller. Not part of INTERFACES.md's frozen export list — see module doc. */
export async function requestEmailVerification(ctx: Ctx): Promise<void> {
  if (ctx.actor.type !== 'user') {
    throw new ForbiddenError('Only an authenticated user can request email verification.');
  }
  await createEmailVerificationToken(ctx, ctx.actor.userId);
  ctx.logger.info('auth.email_verification_requested', { userId: ctx.actor.userId });
}

/** Consumes an email verification token, marking the account's email verified. Not part of INTERFACES.md's frozen export list — see module doc. */
export async function verifyEmail(ctx: Ctx, input: { token: string }): Promise<void> {
  const tokenHash = sha256Hex(input.token);

  const { rows } = await ctx.db.query<{ id: string; user_id: string; expires_at: Date; consumed_at: Date | null }>(
    `SELECT id, user_id, expires_at, consumed_at FROM email_verification_tokens WHERE token_hash = $1`,
    [tokenHash],
  );
  const row = rows[0];
  if (!row) {
    throw new UnauthorizedError('Invalid or expired verification token.');
  }
  if (row.consumed_at) {
    throw new UnauthorizedError('This verification token has already been used.');
  }
  if (row.expires_at.getTime() < ctx.clock.now().getTime()) {
    throw new UnauthorizedError('This verification token has expired.');
  }

  const now = ctx.clock.now();
  await ctx.db.query('UPDATE users SET email_verified_at = $2 WHERE id = $1', [row.user_id, now]);
  await ctx.db.query('UPDATE email_verification_tokens SET consumed_at = $2 WHERE id = $1', [row.id, now]);
}

// =====================================================================
// Access token verification
// =====================================================================

/**
 * Verify a compact access token (see `src/lib/signing.ts`) and return the
 * subject. HTTP middleware calls this once per authenticated request to
 * build `ctx.actor`. Throws `UnauthorizedError` (not `InvalidSignatureError`
 * — that's an implementation detail this function should catch and
 * translate) on any invalid/expired token.
 */
export async function verifyAccessToken(ctx: Ctx, accessToken: string): Promise<{ userId: string }> {
  let payload: AccessTokenPayload;
  try {
    payload = verify<AccessTokenPayload>(accessToken, authSecret());
  } catch (err) {
    if (err instanceof InvalidSignatureError) {
      throw new UnauthorizedError('Invalid access token.');
    }
    throw err;
  }
  if (payload.kind !== 'access') {
    throw new UnauthorizedError('Invalid access token.');
  }
  if (payload.exp * 1000 < ctx.clock.now().getTime()) {
    throw new UnauthorizedError('Access token expired.');
  }

  const { rows } = await ctx.db.query<{ status: UserStatus }>('SELECT status FROM users WHERE id = $1', [payload.sub]);
  const row = rows[0];
  if (!row || row.status !== 'active') {
    throw new UnauthorizedError('Account is not active.');
  }

  return { userId: payload.sub };
}
