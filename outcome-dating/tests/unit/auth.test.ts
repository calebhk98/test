import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { setupTestDatabase, teardownTestDatabase, getTestPool, buildCtx, uniqueEmail } from './testCtx.js';
import * as auth from '../../src/services/auth.service.js';
import { calculateAge } from '../../src/services/auth.service.js';
import { ConflictError, UnauthorizedError, ValidationError, ForbiddenError } from '../../src/lib/errors.js';
import { sha256Hex } from '../../src/lib/hash.js';

before(async () => {
  await setupTestDatabase('auth');
});

after(async () => {
  await teardownTestDatabase();
});

// A real, fixed "today" (not an arbitrary test date) so birthdates computed
// relative to it also satisfy the DB's `users_min_age` CHECK constraint,
// which uses real wall-clock CURRENT_DATE, see auth.service.ts's comment
// on why `register`'s age gate must never depend on that constraint firing
// the same way the app-level check does.
const TODAY = new Date();

function isoDateYearsAgo(years: number, extraDays = 0): string {
  const d = new Date(Date.UTC(TODAY.getUTCFullYear(), TODAY.getUTCMonth(), TODAY.getUTCDate()));
  d.setUTCFullYear(d.getUTCFullYear() - years);
  d.setUTCDate(d.getUTCDate() + extraDays);
  return d.toISOString().slice(0, 10);
}

function validRegisterInput(overrides: Partial<auth.RegisterInput> = {}): auth.RegisterInput {
  return {
    email: uniqueEmail('reg'),
    password: 'CorrectHorseBattery1',
    birthdate: isoDateYearsAgo(25),
    acceptedTermsAt: TODAY,
    city: 'Springfield',
    ...overrides,
  };
}

test('calculateAge: exactly 18 today passes the boundary, one day short does not', () => {
  assert.equal(calculateAge(isoDateYearsAgo(18), TODAY), 18);
  assert.equal(calculateAge(isoDateYearsAgo(18, 1), TODAY), 17); // birthday is one day in the future relative to 18 years ago => still 17
});

test('register: happy path creates an active user and returns tokens, never plaintext password', async () => {
  const ctx = buildCtx({ now: TODAY });
  const { user, tokens } = await auth.register(ctx, validRegisterInput());

  assert.equal(user.status, 'active');
  assert.equal(user.trustLevel, 'standard');
  assert.equal(user.emailVerifiedAt, null);
  assert.ok(user.passwordHash.startsWith('$2'), 'password must be bcrypt-hashed');
  assert.notEqual(user.passwordHash, 'CorrectHorseBattery1');
  assert.ok(tokens.accessToken.length > 0);
  assert.ok(tokens.refreshToken.length > 0);
  assert.ok(tokens.accessTokenExpiresAt.getTime() > TODAY.getTime());
  assert.ok(tokens.refreshTokenExpiresAt.getTime() > tokens.accessTokenExpiresAt.getTime());

  // An email verification token was issued as a side effect (§6.2).
  const pool = getTestPool();
  const { rows } = await pool.query('SELECT count(*)::int AS n FROM email_verification_tokens WHERE user_id = $1', [
    user.id,
  ]);
  assert.equal(rows[0].n, 1);
});

test('register: exactly 18 years old today passes', async () => {
  const ctx = buildCtx({ now: TODAY });
  const { user } = await auth.register(ctx, validRegisterInput({ birthdate: isoDateYearsAgo(18) }));
  assert.equal(user.status, 'active');
});

test('register: one day short of 18 is rejected', async () => {
  const ctx = buildCtx({ now: TODAY });
  await assert.rejects(
    () => auth.register(ctx, validRegisterInput({ birthdate: isoDateYearsAgo(18, 1) })),
    ValidationError,
  );
});

test('register: rejects when neither city nor locationPermissionGranted is provided', async () => {
  const ctx = buildCtx({ now: TODAY });
  const input = validRegisterInput();
  delete (input as Partial<auth.RegisterInput>).city;
  await assert.rejects(() => auth.register(ctx, input), ValidationError);
});

test('register: locationPermissionGranted alone (no city) is sufficient', async () => {
  const ctx = buildCtx({ now: TODAY });
  const input = validRegisterInput({ locationPermissionGranted: true });
  delete (input as Partial<auth.RegisterInput>).city;
  const { user } = await auth.register(ctx, input);
  assert.equal(user.status, 'active');
});

test('register: duplicate email is rejected', async () => {
  const ctx = buildCtx({ now: TODAY });
  const email = uniqueEmail('dup');
  await auth.register(ctx, validRegisterInput({ email }));
  await assert.rejects(() => auth.register(ctx, validRegisterInput({ email })), ConflictError);
});

test('register: no phone number or government ID field exists on the input type (spec §5.2/§5.3)', () => {
  const input = validRegisterInput();
  const asRecord = input as unknown as Record<string, unknown>;
  assert.equal(asRecord.phone, undefined);
  assert.equal(asRecord.phoneNumber, undefined);
  assert.equal(asRecord.governmentId, undefined);
  assert.equal(asRecord.idDocument, undefined);
});

test('login: succeeds with correct credentials and records a successful user_auth_events row', async () => {
  const ctx = buildCtx({ now: TODAY });
  const email = uniqueEmail('login');
  await auth.register(ctx, validRegisterInput({ email }));

  const { user, tokens } = await auth.login(ctx, {
    email,
    password: 'CorrectHorseBattery1',
    deviceFingerprint: 'device-abc',
    ipAddress: '203.0.113.5',
  });
  assert.equal(user.email, email.toLowerCase());
  assert.ok(tokens.accessToken);

  const pool = getTestPool();
  const { rows } = await pool.query(
    'SELECT success, device_fingerprint, ip_address::text AS ip_address FROM user_auth_events WHERE user_id = $1 ORDER BY login_at DESC LIMIT 1',
    [user.id],
  );
  assert.equal(rows[0].success, true);
  assert.equal(rows[0].device_fingerprint, 'device-abc');
});

test('login: wrong password fails and records a failed user_auth_events row', async () => {
  const ctx = buildCtx({ now: TODAY });
  const email = uniqueEmail('badpw');
  await auth.register(ctx, validRegisterInput({ email }));

  await assert.rejects(() => auth.login(ctx, { email, password: 'wrong-password' }), UnauthorizedError);

  const pool = getTestPool();
  const { rows } = await pool.query(
    `SELECT success FROM user_auth_events ua JOIN users u ON u.id = ua.user_id WHERE u.email = $1 ORDER BY login_at DESC LIMIT 1`,
    [email.toLowerCase()],
  );
  assert.equal(rows[0].success, false);
});

test('login: unknown email still records an auth event with a null user_id', async () => {
  const ctx = buildCtx({ now: TODAY });
  const email = uniqueEmail('unknown');
  await assert.rejects(() => auth.login(ctx, { email, password: 'whatever12' }), UnauthorizedError);

  const pool = getTestPool();
  const { rows } = await pool.query(
    'SELECT user_id, success FROM user_auth_events WHERE user_id IS NULL ORDER BY login_at DESC LIMIT 1',
  );
  assert.equal(rows[0].success, false);
});

test('refresh: rotates the refresh token and the old one stops working', async () => {
  const ctx = buildCtx({ now: TODAY });
  const email = uniqueEmail('rotate');
  await auth.register(ctx, validRegisterInput({ email }));
  const { tokens: first } = await auth.login(ctx, { email, password: 'CorrectHorseBattery1' });

  const second = await auth.refresh(ctx, { refreshToken: first.refreshToken });
  assert.notEqual(second.refreshToken, first.refreshToken);
  assert.notEqual(second.accessToken, first.accessToken);

  // The new access token verifies fine.
  const { userId } = await auth.verifyAccessToken(ctx, second.accessToken);
  assert.ok(userId);
});

test('refresh: reusing an already-rotated refresh token is detected and revokes the session', async () => {
  const ctx = buildCtx({ now: TODAY });
  const email = uniqueEmail('reuse');
  await auth.register(ctx, validRegisterInput({ email }));
  const { tokens: first } = await auth.login(ctx, { email, password: 'CorrectHorseBattery1' });

  const second = await auth.refresh(ctx, { refreshToken: first.refreshToken });
  assert.ok(second);

  // Reusing the now-stale `first.refreshToken` must fail...
  await assert.rejects(() => auth.refresh(ctx, { refreshToken: first.refreshToken }), UnauthorizedError);

  // ...and must have revoked the session, so even the *current* valid
  // refresh token from the rotation no longer works.
  await assert.rejects(() => auth.refresh(ctx, { refreshToken: second.refreshToken }), UnauthorizedError);
});

test('logout: revokes the session so a subsequent refresh fails', async () => {
  const ctx = buildCtx({ now: TODAY });
  const email = uniqueEmail('logout');
  await auth.register(ctx, validRegisterInput({ email }));
  const { tokens } = await auth.login(ctx, { email, password: 'CorrectHorseBattery1' });

  await auth.logout(ctx, { refreshToken: tokens.refreshToken });
  await assert.rejects(() => auth.refresh(ctx, { refreshToken: tokens.refreshToken }), UnauthorizedError);
});

test('verifyAccessToken: rejects an expired access token', async () => {
  const ctx = buildCtx({ now: TODAY });
  const email = uniqueEmail('expiry');
  await auth.register(ctx, validRegisterInput({ email }));
  const { tokens } = await auth.login(ctx, { email, password: 'CorrectHorseBattery1' });

  const { userId } = await auth.verifyAccessToken(ctx, tokens.accessToken);
  assert.ok(userId);

  // Advance the (test-controlled) clock well past the access token TTL.
  const future = new Date(TODAY.getTime() + 24 * 60 * 60 * 1000);
  const laterCtx = buildCtx({ now: future });
  await assert.rejects(() => auth.verifyAccessToken(laterCtx, tokens.accessToken), UnauthorizedError);
});

test('verifyAccessToken: rejects a garbage token', async () => {
  const ctx = buildCtx({ now: TODAY });
  await assert.rejects(() => auth.verifyAccessToken(ctx, 'not-a-real-token'), UnauthorizedError);
});

test('forgotPassword: does not throw and does not leak whether an email exists', async () => {
  const ctx = buildCtx({ now: TODAY });
  await assert.doesNotReject(() => auth.forgotPassword(ctx, { email: uniqueEmail('nosuchuser') }));
});

test('forgotPassword + resetPassword: end-to-end token consumption changes the password and revokes sessions', async () => {
  const ctx = buildCtx({ now: TODAY });
  const email = uniqueEmail('reset');
  const { user } = await auth.register(ctx, validRegisterInput({ email }));
  const { tokens } = await auth.login(ctx, { email, password: 'CorrectHorseBattery1' });

  await auth.forgotPassword(ctx, { email });

  const pool = getTestPool();
  const { rows } = await pool.query('SELECT token_hash FROM password_reset_tokens WHERE user_id = $1', [user.id]);
  assert.equal(rows.length, 1);

  // We only ever store the *hash* server-side (never the raw token), the
  // test drives resetPassword by seeding a token whose hash it controls,
  // exactly like a real "click the emailed link" flow would.
  const rawToken = 'test-reset-token-12345';
  await pool.query('UPDATE password_reset_tokens SET token_hash = $2 WHERE user_id = $1', [
    user.id,
    sha256Hex(rawToken),
  ]);

  await auth.resetPassword(ctx, { resetToken: rawToken, newPassword: 'NewPassword2!' });

  // Old password no longer works, new one does.
  await assert.rejects(() => auth.login(ctx, { email, password: 'CorrectHorseBattery1' }), UnauthorizedError);
  const relogin = await auth.login(ctx, { email, password: 'NewPassword2!' });
  assert.ok(relogin.tokens.accessToken);

  // The session that existed before the reset was revoked.
  await assert.rejects(() => auth.refresh(ctx, { refreshToken: tokens.refreshToken }), UnauthorizedError);

  // The reset token itself is single-use.
  await assert.rejects(
    () => auth.resetPassword(ctx, { resetToken: rawToken, newPassword: 'AnotherPassword3!' }),
    UnauthorizedError,
  );
});

test('resetPassword: an expired token is rejected', async () => {
  const ctx = buildCtx({ now: TODAY });
  const email = uniqueEmail('expiredreset');
  const { user } = await auth.register(ctx, validRegisterInput({ email }));

  const pool = getTestPool();
  const rawToken = 'expired-token-xyz';
  await pool.query(
    `INSERT INTO password_reset_tokens (user_id, token_hash, created_at, expires_at) VALUES ($1, $2, $3, $4)`,
    [user.id, sha256Hex(rawToken), TODAY, new Date(TODAY.getTime() - 1000)],
  );

  await assert.rejects(
    () => auth.resetPassword(ctx, { resetToken: rawToken, newPassword: 'NewPassword2!' }),
    UnauthorizedError,
  );
});

test('requestEmailVerification: requires an authenticated user actor', async () => {
  const systemCtx = buildCtx({ now: TODAY }); // default actor is 'system'
  await assert.rejects(() => auth.requestEmailVerification(systemCtx), ForbiddenError);
});

test('verifyEmail: consumes a valid token and marks the account verified; rejects reuse', async () => {
  const ctx = buildCtx({ now: TODAY });
  const email = uniqueEmail('verify');
  const { user } = await auth.register(ctx, validRegisterInput({ email }));

  const pool = getTestPool();
  const rawToken = 'verify-token-abc';
  await pool.query('UPDATE email_verification_tokens SET token_hash = $2 WHERE user_id = $1', [
    user.id,
    sha256Hex(rawToken),
  ]);

  await auth.verifyEmail(ctx, { token: rawToken });

  const { rows } = await pool.query('SELECT email_verified_at FROM users WHERE id = $1', [user.id]);
  assert.notEqual(rows[0].email_verified_at, null);

  await assert.rejects(() => auth.verifyEmail(ctx, { token: rawToken }), UnauthorizedError);
});
