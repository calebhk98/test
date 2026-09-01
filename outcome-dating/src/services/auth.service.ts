import { randomInt } from 'node:crypto';
import { z } from 'zod';
import type { Ctx } from '../lib/ctx.js';
import { requireUserActor } from '../lib/ctx.js';
import { ConflictError, ForbiddenError, RateLimitError, UnauthorizedError, ValidationError } from '../lib/errors.js';
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
 *  - No phone number or government ID is ever required (§5.2, §5.3) — a
 *    corrected reading of that rule, worth spelling out precisely: it does
 *    NOT mean no phone number anywhere, it means a phone number must never
 *    be MANDATORY for any flow (not registration, not sending an interest,
 *    not proposing a date, not appearing in discovery — nothing but the
 *    SMS channel itself). An OPTIONAL, user-added, verified-by-one-time-code
 *    phone number is fully supported below (`requestPhoneVerification` /
 *    `verifyPhone` / `removePhone` / `getMyPhoneStatus`) — not requiring
 *    one is what keeps the product usable for the growing share of real
 *    users who don't carry a conventional phone number; not OFFERING one
 *    would just mean nobody who wants SMS notifications can have them.
 *    `tests/unit/phone.test.ts`'s "phone-less core loop" test is the
 *    executable proof of the MANDATORY half of this invariant.
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
 *
 * Also beyond the frozen export list (this build): the optional-phone
 * lifecycle — `requestPhoneVerification`, `verifyPhone`, `removePhone`,
 * `getMyPhoneStatus` (self-service, masked) — plus `getVerifiedPhoneForUser`,
 * an internal (system-or-self) read the `notifications/**` SMS channel
 * calls to resolve a send target and to gate SMS eligibility, exactly the
 * trust boundary `devices.ts#listActiveDeviceTokensForUser` and
 * `preferences.ts#getContentPreviewForUser` already use for their own
 * cross-module internal reads. Wired to HTTP as `POST /auth/phone`,
 * `POST /auth/phone/verify`, `DELETE /auth/phone`, `GET /auth/phone` in
 * `src/http/routes/auth.routes.ts` (this same build — additive routes,
 * see `routeTable.ts`).
 *
 * Phone verification delivery follows the exact same "issue token/code,
 * never actually send it — that's out of scope for this leaf module"
 * pattern `requestEmailVerification`/`forgotPassword` already establish
 * below: the raw one-time code is hashed before it ever touches the
 * database (same discipline as `email_verification_tokens.token_hash` /
 * `password_reset_tokens.token_hash`) and is never logged or returned to
 * the caller. A production deployment wires the actual SMS send (through
 * `notifications/**`'s `SmsSender` port, or a dedicated transactional path
 * — a one-time code is time-critical in a way that argues against routing
 * it through the coalescing/preference/quiet-hours pipeline built for
 * ordinary event notifications) the same way real email delivery for
 * `requestEmailVerification`/`forgotPassword` still needs wiring — flagged
 * in this build's report, not a gap unique to phone.
 */

// =====================================================================
// Local (non-shared-config) tunables. `src/config/config.service.ts` is
// shared infra outside this agent's ownership; these two TTLs are simple
// enough to keep as file-local constants rather than proposing new global
// config keys for a single-consumer value.
// =====================================================================
const PASSWORD_RESET_TOKEN_TTL_HOURS = 2;
const EMAIL_VERIFICATION_TOKEN_TTL_HOURS = 48;

// ---- Phone verification (optional phone number — see module doc) ----
/** A one-time code is short-lived: long enough to receive and type an SMS, short enough that a leaked/intercepted old code is worthless quickly. */
const PHONE_VERIFICATION_CODE_TTL_MINUTES = 10;
/** Wrong-code attempts allowed against one issued code before it's dead and a fresh one (via `requestPhoneVerification`) is required — caps brute-forcing a 6-digit code (1e6 space) to a vanishingly small success probability. */
const PHONE_VERIFICATION_MAX_ATTEMPTS = 5;
/** Max `requestPhoneVerification` calls (i.e. codes issued/SMS notionally sent) per user within the window below — the "rate-limited" half of the build brief's "verification by one-time code, rate-limited, with expiry and a cap on attempts". */
const PHONE_VERIFICATION_MAX_REQUESTS_PER_WINDOW = 5;
const PHONE_VERIFICATION_REQUEST_WINDOW_MINUTES = 60;

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

// =====================================================================
// Optional phone number (build correction — see module doc)
//
// Lives with the account (this file), not the profile: `user_phones`
// (015_phone.sql) is a separate table auth.service.ts owns outright, the
// same way `email_verification_tokens`/`password_reset_tokens` already
// are. Never required for anything; the whole point of this section is
// that it's addable, changeable, and removable independently of every
// other flow in the product.
// =====================================================================

function normalizePhoneE164(raw: string): string {
  // Strip the punctuation people commonly type/paste — spaces, hyphens,
  // dots, parens — but do NOT attempt to infer a country calling code from
  // a national-format number (that needs a phone-number-parsing library
  // this foundation layer deliberately doesn't depend on). The client is
  // expected to send an already-E.164-shaped number; `country` is supplied
  // alongside it explicitly rather than derived.
  return raw.trim().replace(/[\s\-().]/g, '');
}

const E164_REGEX = /^\+[1-9]\d{6,14}$/;
const COUNTRY_CODE_REGEX = /^[A-Z]{2}$/;

const RequestPhoneVerificationSchema = z.object({
  phoneNumber: z.string().trim().min(3).max(20),
  /** ISO 3166-1 alpha-2, e.g. "US" — stored alongside the E.164 number (build brief: "store it normalised (E.164) with the country"). */
  country: z
    .string()
    .trim()
    .toUpperCase()
    .refine((c) => COUNTRY_CODE_REGEX.test(c), 'country must be a 2-letter ISO 3166-1 country code'),
});

const VerifyPhoneSchema = z.object({
  code: z.string().trim().min(4).max(10),
});

export interface RequestPhoneVerificationInput {
  phoneNumber: string;
  country: string;
}

/**
 * Masked, self-service view of the calling user's own phone state — never
 * the full number (see module doc / build report: "never expose it to
 * another user" is enforced here even more strictly, by never returning
 * the full number through ANY route, including the owner's own — the
 * owner already knows the number they typed, so a `last2` confirmation
 * plus verification status is enough UI feedback without ever putting the
 * full E.164 value on the wire).
 */
export interface PhoneStatusView {
  hasPhone: boolean;
  verified: boolean;
  countryCode: string | null;
  /** Last 2 digits of the E.164 number only — e.g. "34" for "+14155551234". Never the full number. */
  last2: string | null;
  addedAt: Date | null;
  verifiedAt: Date | null;
}

interface UserPhoneRow {
  user_id: string;
  phone_e164: string;
  country_code: string;
  verified_at: Date | null;
  created_at: Date;
  updated_at: Date;
}

function generatePhoneVerificationCode(): string {
  // 6 numeric digits, zero-padded — the conventional SMS OTP shape. Not
  // `newHumanCode` (lib/ids.ts): that alphabet is base32 letters+digits,
  // meant to be read off a screen and typed by hand (voucher codes); an
  // SMS code should be the digits-only shape every phone keypad/autofill
  // expects.
  return String(randomInt(0, 1_000_000)).padStart(6, '0');
}

/**
 * (Re)issues a one-time verification code for `input.phoneNumber` (rate-
 * limited, see `PHONE_VERIFICATION_MAX_REQUESTS_PER_WINDOW`). Always resets
 * `user_phones.verified_at` to NULL for the calling user — adding a number
 * for the first time and changing an already-verified number are the same
 * operation, and both require a fresh code, never carrying over a prior
 * verification. Delivery of the actual SMS is out of scope for this leaf
 * module (see module doc) — the raw code is never returned or logged.
 */
export async function requestPhoneVerification(ctx: Ctx, input: RequestPhoneVerificationInput): Promise<void> {
  const { userId } = requireUserActor(ctx);
  const parsed = RequestPhoneVerificationSchema.parse(input);
  const e164 = normalizePhoneE164(parsed.phoneNumber);
  if (!E164_REGEX.test(e164)) {
    throw new ValidationError('phoneNumber must be a valid E.164 number, e.g. "+14155551234".', { field: 'phoneNumber' });
  }

  const now = ctx.clock.now();

  // ---- rate limit: requests (i.e. codes issued) per rolling window ----
  const windowStart = new Date(now.getTime() - PHONE_VERIFICATION_REQUEST_WINDOW_MINUTES * 60 * 1000);
  const { rows: recentRows } = await ctx.db.query<{ count: string }>(
    `SELECT count(*)::text AS count FROM phone_verification_codes WHERE user_id = $1 AND created_at >= $2`,
    [userId, windowStart],
  );
  if (Number(recentRows[0]?.count ?? '0') >= PHONE_VERIFICATION_MAX_REQUESTS_PER_WINDOW) {
    throw new RateLimitError('Too many verification codes requested. Please wait before requesting another.', {
      limit: PHONE_VERIFICATION_MAX_REQUESTS_PER_WINDOW,
      windowMinutes: PHONE_VERIFICATION_REQUEST_WINDOW_MINUTES,
    });
  }

  // A VERIFIED number already claimed by a different account can't be
  // re-claimed here — matches the DB-level partial unique index
  // (015_phone.sql) but checked first for a clean, typed error rather than
  // surfacing a raw constraint violation.
  const { rows: claimedRows } = await ctx.db.query<{ user_id: string }>(
    `SELECT user_id FROM user_phones WHERE phone_e164 = $1 AND verified_at IS NOT NULL AND user_id <> $2`,
    [e164, userId],
  );
  if (claimedRows.length > 0) {
    throw new ConflictError('This phone number is already verified on another account.');
  }

  // Any code still pending for this user (for whatever number it was
  // issued against) is now stale — a fresh request always supersedes it,
  // so it can never later be used to "verify" a number the user has since
  // changed away from.
  await ctx.db.query(
    `UPDATE phone_verification_codes SET consumed_at = $2 WHERE user_id = $1 AND consumed_at IS NULL`,
    [userId, now],
  );

  await ctx.db.query(
    `INSERT INTO user_phones (user_id, phone_e164, country_code, verified_at, created_at, updated_at)
     VALUES ($1, $2, $3, NULL, $4, $4)
     ON CONFLICT (user_id) DO UPDATE SET
       phone_e164 = EXCLUDED.phone_e164, country_code = EXCLUDED.country_code,
       verified_at = NULL, updated_at = EXCLUDED.updated_at`,
    [userId, e164, parsed.country, now],
  );

  const code = generatePhoneVerificationCode();
  const codeHash = sha256Hex(code);
  const expiresAt = new Date(now.getTime() + PHONE_VERIFICATION_CODE_TTL_MINUTES * 60 * 1000);
  await ctx.db.query(
    `INSERT INTO phone_verification_codes (user_id, phone_e164, code_hash, attempt_count, created_at, expires_at)
     VALUES ($1, $2, $3, 0, $4, $5)`,
    [userId, e164, codeHash, now, expiresAt],
  );

  // Never log `code` itself — it's a bearer credential for this step, same
  // rule as the password-reset/email-verification raw tokens above.
  ctx.logger.info('auth.phone_verification_requested', { userId });
}

/** Consumes the calling user's current pending phone verification code. Throws `UnauthorizedError` for no/expired/wrong code, `RateLimitError` once the attempt cap on the current code is exhausted (request a new one via `requestPhoneVerification` to reset it). */
export async function verifyPhone(ctx: Ctx, input: { code: string }): Promise<void> {
  const { userId } = requireUserActor(ctx);
  const parsed = VerifyPhoneSchema.parse(input);
  const now = ctx.clock.now();

  const { rows } = await ctx.db.query<{
    id: string;
    phone_e164: string;
    code_hash: string;
    attempt_count: number;
    expires_at: Date;
    consumed_at: Date | null;
  }>(
    `SELECT id, phone_e164, code_hash, attempt_count, expires_at, consumed_at
       FROM phone_verification_codes
      WHERE user_id = $1 AND consumed_at IS NULL
      ORDER BY created_at DESC
      LIMIT 1`,
    [userId],
  );
  const row = rows[0];
  if (!row) {
    throw new UnauthorizedError('No pending phone verification code. Request a new one.');
  }
  if (row.expires_at.getTime() < now.getTime()) {
    throw new UnauthorizedError('This verification code has expired. Request a new one.');
  }
  if (row.attempt_count >= PHONE_VERIFICATION_MAX_ATTEMPTS) {
    throw new RateLimitError('Too many incorrect attempts. Request a new verification code.', {
      limit: PHONE_VERIFICATION_MAX_ATTEMPTS,
    });
  }

  if (sha256Hex(parsed.code) !== row.code_hash) {
    await ctx.db.query('UPDATE phone_verification_codes SET attempt_count = attempt_count + 1 WHERE id = $1', [row.id]);
    throw new UnauthorizedError('Incorrect verification code.');
  }

  await ctx.db.query('UPDATE phone_verification_codes SET consumed_at = $2 WHERE id = $1', [row.id, now]);
  await ctx.db.query(
    `UPDATE user_phones SET verified_at = $2, updated_at = $2 WHERE user_id = $1 AND phone_e164 = $3`,
    [userId, now, row.phone_e164],
  );

  ctx.logger.info('auth.phone_verified', { userId });

  // Deliberately NOT wired here: bumping trust score for a verified phone.
  // `trust.service.ts` is outside this build's file-ownership boundary and
  // its own "may call" graph does not list auth.service among the modules
  // wired to push `trust_events` — see this build's report for the
  // suggested weight and why it's a report, not a direct edit.
}

/**
 * Removes the calling user's phone number — as easy as adding one (a
 * single call, no confirmation flow beyond auth), and the entire
 * "immediately disable SMS" story: `notifications/delivery.ts` re-checks
 * `getVerifiedPhoneForUser` live on every SMS send, so deleting this row
 * takes effect on the very next delivery attempt, not just future
 * enqueues. A no-op (never throws) if the user has no phone on file.
 */
export async function removePhone(ctx: Ctx): Promise<void> {
  const { userId } = requireUserActor(ctx);
  const now = ctx.clock.now();
  await ctx.db.query('DELETE FROM user_phones WHERE user_id = $1', [userId]);
  await ctx.db.query(
    `UPDATE phone_verification_codes SET consumed_at = $2 WHERE user_id = $1 AND consumed_at IS NULL`,
    [userId, now],
  );
  ctx.logger.info('auth.phone_removed', { userId });
}

function mapPhoneStatus(row: UserPhoneRow | undefined): PhoneStatusView {
  if (!row) {
    return { hasPhone: false, verified: false, countryCode: null, last2: null, addedAt: null, verifiedAt: null };
  }
  return {
    hasPhone: true,
    verified: row.verified_at !== null,
    countryCode: row.country_code,
    last2: row.phone_e164.slice(-2),
    addedAt: row.created_at,
    verifiedAt: row.verified_at,
  };
}

/** Self-service, masked phone status for the calling user (never the full number — see `PhoneStatusView` doc). */
export async function getMyPhoneStatus(ctx: Ctx): Promise<PhoneStatusView> {
  const { userId } = requireUserActor(ctx);
  const { rows } = await ctx.db.query<UserPhoneRow>('SELECT * FROM user_phones WHERE user_id = $1', [userId]);
  return mapPhoneStatus(rows[0]);
}

/**
 * Internal (system, or the user themselves) read of a user's currently
 * VERIFIED phone, full E.164 value included — the one place the full
 * number is ever returned by this module, and only to a caller who is
 * either `system` or that same user, never another user. This is what
 * `notifications/**` calls to (a) decide SMS eligibility for an event
 * (`outbox.ts`) and (b) resolve the actual send target (`delivery.ts`) —
 * same trust boundary as `devices.ts#listActiveDeviceTokensForUser` /
 * `preferences.ts#getContentPreviewForUser`. Returns `null` for no phone,
 * an unverified phone, or a phone that's since been removed — callers
 * never need to check `verified_at` themselves.
 */
export async function getVerifiedPhoneForUser(
  ctx: Ctx,
  userId: string,
): Promise<{ e164: string; countryCode: string } | null> {
  if (ctx.actor.type === 'user' && ctx.actor.userId !== userId) {
    throw new ForbiddenError("Cannot read another user's phone number.");
  }
  const { rows } = await ctx.db.query<{ phone_e164: string; country_code: string }>(
    `SELECT phone_e164, country_code FROM user_phones WHERE user_id = $1 AND verified_at IS NOT NULL`,
    [userId],
  );
  const row = rows[0];
  return row ? { e164: row.phone_e164, countryCode: row.country_code } : null;
}
